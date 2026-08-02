#!/usr/bin/env python3
"""Turn curated evidence seeds into verified EvidenceSpan records.

An analyst records, in ``data/evidence_seeds.yaml``, only three things per
span: which document, which PDF page index, and a short anchor phrase they
read on that page.  This script does everything else -- and, crucially, it
*fails* if the anchor is not actually present on the stated page.

That inversion is the anti-fabrication mechanism of the whole project.  A page
number is never typed next to a quotation by hand; it is proven by reopening
the PDF.  If a citation drifts, the build breaks rather than lying.

For each seed the script resolves and records:

* the printed page label and the PDF page index, as separate fields;
* the text block containing the anchor, and that block's bounding box;
* the chapter and section that contain the page, from the PDF outline;
* the fraction of characters in a mathematics font, and a resulting
  text-integrity verdict -- because in the Shigley PDF the math glyphs decode
  to unrelated ASCII and such text must never be quoted;
* a short excerpt, capped so that the store never becomes a copy of the book.

Output: ``data/evidence_spans.jsonl`` (deterministic, sorted by span id).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyMuPDF is required: pip install pymupdf") from exc

import yaml

LOG = logging.getLogger("build_evidence_spans")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

#: Excerpts are capped. The evidence store proves a citation; it is not a copy
#: of the source. 480 characters comfortably covers a claim-bearing sentence.
MAX_EXCERPT_CHARS = 480


class SeedVerificationError(RuntimeError):
    """Raised when a seed's anchor cannot be found where the seed says it is."""


@dataclass
class EvidenceSpanRecord:
    """A located, verified region of a source document."""

    span_id: str
    doc_id: str
    source_file_name: str
    book_title: str
    authors: List[str]
    edition: str
    # --- location, with the two page numbers kept apart ---
    pdf_page_index: int
    pdf_page_number: int
    page_label: Optional[str]
    printed_page: Optional[str]
    page_label_style: str
    chapter_number: Optional[str]
    chapter_title: Optional[str]
    section_number: Optional[str]
    section_title: Optional[str]
    block_id: str
    block_no: int
    bbox: List[float]
    # --- content ---
    anchor: str
    match_mode: str
    extracted_text: str
    excerpt_truncated: bool
    # --- quality ---
    math_font_char_ratio: float
    text_integrity: str
    extraction_method: str
    extraction_confidence: float
    # --- curation ---
    topic: str
    artifact_refs: List[Dict[str, str]] = field(default_factory=list)
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

_SOFT_HYPHEN_BREAK = re.compile(r"[­-]\s*\n\s*")
_WS = re.compile(r"\s+")


_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def _fold_typography(text: str) -> str:
    """Fold quote, dash and space variants that differ between typed and printed text."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    return text.replace(" ", " ")


def squash(text: str) -> str:
    """Reduce text to lower-case alphanumerics only, for a hyphen-blind match.

    De-hyphenation at a line end is ambiguous: the PDF gives no way to tell a
    soft break inside ``organiza-tions`` from a genuine hyphen in
    ``standards-setting`` that happens to fall at a line end.  Rather than
    guess, the builder tries the de-hyphenated form first and falls back to
    this form, which is invariant to that choice.  Long anchors make a false
    positive vanishingly unlikely, and the matcher that succeeded is recorded
    on the span as ``match_mode``.
    """
    return _NON_ALNUM.sub("", _fold_typography(text).lower())


def normalize_for_match(text: str) -> str:
    """Collapse PDF line-breaking artefacts so an anchor can be matched.

    Two-column technical text hyphenates across line ends and wraps mid
    sentence, so a phrase a human reads as continuous is not contiguous in the
    extracted string.  This joins hyphenated line breaks, collapses remaining
    whitespace, and folds the typographic quotes and dashes that differ between
    what an analyst types and what the PDF stores.
    """
    text = unicodedata.normalize("NFKC", text)
    text = _SOFT_HYPHEN_BREAK.sub("", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = text.replace(" ", " ")
    return _WS.sub(" ", text).strip()


def tidy_excerpt(text: str) -> Tuple[str, bool]:
    """Return a whitespace-tidied, length-capped excerpt and a truncation flag."""
    cleaned = _SOFT_HYPHEN_BREAK.sub("", text)
    cleaned = _WS.sub(" ", cleaned).strip()
    if len(cleaned) <= MAX_EXCERPT_CHARS:
        return cleaned, False
    cut = cleaned[:MAX_EXCERPT_CHARS]
    if " " in cut:
        cut = cut[: cut.rindex(" ")]
    return cut + " …", True


def classify_integrity(math_ratio: float, declared_reliability: str) -> str:
    """Judge whether a span's characters can be trusted as printed.

    ``glyph-mismapped`` is reserved for text from a document whose mathematics
    fonts decode to unrelated ASCII.  Such text may be *stored* for traceability
    but must never be quoted or parsed as an equation.
    """
    if math_ratio <= 0.005:
        return "reliable"
    if declared_reliability == "corrupted":
        return "glyph-mismapped"
    if declared_reliability == "partial":
        return "partial-glyph-loss"
    return "unverified"


# ---------------------------------------------------------------------------
# Outline lookup
# ---------------------------------------------------------------------------


class OutlineIndex:
    """Resolve a PDF page index to its containing chapter and section."""

    def __init__(self, toc_nodes: Sequence[Dict[str, Any]]) -> None:
        self._chapters = [n for n in toc_nodes if n["kind"] == "chapter"]
        self._sections = [n for n in toc_nodes if n["kind"] == "section"]

    @staticmethod
    def _innermost(nodes: Sequence[Dict[str, Any]], page_index: int) -> Optional[Dict[str, Any]]:
        """Return the tightest-spanning node containing *page_index*."""
        containing = [
            n for n in nodes
            if n["start_pdf_page_index"] <= page_index
            and (n["end_pdf_page_index"] is None or page_index <= n["end_pdf_page_index"])
        ]
        if not containing:
            return None
        return min(
            containing,
            key=lambda n: (n["end_pdf_page_index"] or 10**9) - n["start_pdf_page_index"],
        )

    def chapter_for(self, page_index: int) -> Optional[Dict[str, Any]]:
        return self._innermost(self._chapters, page_index)

    def section_for(self, page_index: int) -> Optional[Dict[str, Any]]:
        return self._innermost(self._sections, page_index)


def clean_title(title: Optional[str]) -> Optional[str]:
    """Strip a leading number from a TOC title, leaving the human-readable part."""
    if not title:
        return None
    return re.sub(r"^\s*\d{1,2}\s*(?:[–\-—]\s*\d{1,3})?\s*", "", title).strip() or title


# ---------------------------------------------------------------------------
# Seed resolution
# ---------------------------------------------------------------------------


class SpanBuilder:
    """Resolve seeds against one source document."""

    def __init__(self, doc_id: str, source_cfg: Dict[str, Any], build_dir: Path) -> None:
        self.doc_id = doc_id
        self.source_cfg = source_cfg
        self.pdf_path = REPO_ROOT / source_cfg["file"]
        self.doc = fitz.open(self.pdf_path)
        self.reliability = source_cfg.get("math_text_reliability", "unverified")

        with (build_dir / f"{doc_id}.toc.json").open(encoding="utf-8") as fh:
            self.outline = OutlineIndex(json.load(fh))

        self._pages: Dict[int, Dict[str, Any]] = {}
        with (build_dir / f"{doc_id}.pages.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                self._pages[rec["pdf_page_index"]] = rec

        self._blocks_by_page: Dict[int, List[Dict[str, Any]]] = {}
        with (build_dir / f"{doc_id}.blocks.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                self._blocks_by_page.setdefault(rec["pdf_page_index"], []).append(rec)

    def close(self) -> None:
        self.doc.close()

    def build(self, seed: Dict[str, Any]) -> EvidenceSpanRecord:
        """Resolve one seed into a verified span, or raise."""
        page_index = int(seed["pdf_page_index"])
        anchor = str(seed["anchor"])
        norm_anchor = normalize_for_match(anchor)
        if not norm_anchor:
            raise SeedVerificationError(f"{seed['id']}: empty anchor")

        if not 0 <= page_index < self.doc.page_count:
            raise SeedVerificationError(
                f"{seed['id']}: page index {page_index} outside {self.doc_id} (0..{self.doc.page_count - 1})"
            )

        # 1. Verify the anchor really is on that page, straight from the PDF.
        raw_page_text = self.doc[page_index].get_text("text")
        if norm_anchor in normalize_for_match(raw_page_text):
            match_mode = "dehyphenated"
        elif squash(anchor) in squash(raw_page_text):
            match_mode = "squashed"
        else:
            raise SeedVerificationError(
                f"{seed['id']}: anchor not found on {self.doc_id} pdf page index {page_index}\n"
                f"    anchor: {norm_anchor[:120]!r}"
            )

        # 2. Locate the block that carries it, for a bounding box.
        block = self._find_block(page_index, norm_anchor, anchor, match_mode)
        if block is None:
            raise SeedVerificationError(
                f"{seed['id']}: anchor spans no single text block on page index {page_index}; "
                "shorten the anchor so it lies within one paragraph"
            )

        page_rec = self._pages[page_index]
        chapter = self.outline.chapter_for(page_index)
        section = self.outline.section_for(page_index)
        excerpt, truncated = tidy_excerpt(block["text"])
        math_ratio = float(block["math_font_char_ratio"])
        integrity = classify_integrity(math_ratio, self.reliability)

        return EvidenceSpanRecord(
            span_id=seed["id"],
            doc_id=self.doc_id,
            source_file_name=self.pdf_path.name,
            book_title=self.source_cfg["title"],
            authors=list(self.source_cfg.get("authors", [])),
            edition=self.source_cfg.get("edition", ""),
            pdf_page_index=page_index,
            pdf_page_number=page_index + 1,
            page_label=page_rec["page_label"],
            printed_page=page_rec["printed_page"],
            page_label_style=page_rec["label_style"],
            chapter_number=(chapter or {}).get("number"),
            chapter_title=clean_title((chapter or {}).get("title")),
            section_number=(section or {}).get("number"),
            section_title=clean_title((section or {}).get("title")),
            block_id=block["block_id"],
            block_no=int(block["block_no"]),
            bbox=[float(v) for v in block["bbox"]],
            anchor=norm_anchor,
            match_mode=match_mode,
            extracted_text=excerpt,
            excerpt_truncated=truncated,
            math_font_char_ratio=math_ratio,
            text_integrity=integrity,
            extraction_method="pymupdf-textdict+anchor-verified",
            extraction_confidence=float(seed.get("extraction_confidence", 0.95)),
            topic=str(seed["topic"]),
            artifact_refs=list(seed.get("artifact_refs", []) or []),
            note=seed.get("note"),
        )

    def _find_block(
        self, page_index: int, norm_anchor: str, raw_anchor: str, match_mode: str
    ) -> Optional[Dict[str, Any]]:
        """Return the block whose text contains the anchor, using the same matcher."""
        blocks = self._blocks_by_page.get(page_index, [])
        for block in blocks:
            if norm_anchor in normalize_for_match(block["text"]):
                return block
        if match_mode == "squashed":
            squashed_anchor = squash(raw_anchor)
            for block in blocks:
                if squashed_anchor in squash(block["text"]):
                    return block
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(config: Dict[str, Any], seeds_path: Path, out_path: Path, strict: bool) -> Dict[str, Any]:
    """Build all evidence spans. Returns a summary dict."""
    with seeds_path.open(encoding="utf-8") as fh:
        seeds_doc = yaml.safe_load(fh)
    seeds: List[Dict[str, Any]] = seeds_doc["evidence_seeds"]

    build_dir = REPO_ROOT / config["paths"]["build_dir"]
    builders: Dict[str, SpanBuilder] = {}
    records: List[EvidenceSpanRecord] = []
    failures: List[str] = []

    seen_ids = set()
    try:
        for seed in seeds:
            doc_id = seed["doc"]
            if seed["id"] in seen_ids:
                failures.append(f"{seed['id']}: duplicate span id")
                continue
            seen_ids.add(seed["id"])
            if doc_id not in builders:
                if doc_id not in config["sources"]:
                    failures.append(f"{seed['id']}: unknown doc '{doc_id}'")
                    continue
                builders[doc_id] = SpanBuilder(doc_id, config["sources"][doc_id], build_dir)
            try:
                records.append(builders[doc_id].build(seed))
            except SeedVerificationError as exc:
                failures.append(str(exc))
    finally:
        for builder in builders.values():
            builder.close()

    for failure in failures:
        LOG.error("VERIFICATION FAILED: %s", failure)

    if failures and strict:
        raise SystemExit(
            f"\n{len(failures)} evidence seed(s) could not be verified against the PDFs. "
            "No spans were written. Fix the seeds; do not relax the check."
        )

    records.sort(key=lambda r: r.span_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(asdict(rec), ensure_ascii=False, sort_keys=True) + "\n")

    by_doc: Dict[str, int] = {}
    by_integrity: Dict[str, int] = {}
    for rec in records:
        by_doc[rec.doc_id] = by_doc.get(rec.doc_id, 0) + 1
        by_integrity[rec.text_integrity] = by_integrity.get(rec.text_integrity, 0) + 1

    summary = {
        "seeds": len(seeds),
        "verified_spans": len(records),
        "failures": len(failures),
        "failure_messages": failures,
        "by_document": by_doc,
        "by_text_integrity": by_integrity,
        "output": str(out_path.relative_to(REPO_ROOT)),
    }
    LOG.info("verified %d/%d seeds -> %s", len(records), len(seeds), out_path)
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seeds", type=Path, default=REPO_ROOT / "data" / "evidence_seeds.yaml")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "evidence_spans.jsonl")
    parser.add_argument(
        "--no-strict", action="store_true",
        help="write the spans that did verify instead of failing the build (diagnostic use only)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    with args.config.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    summary = run(config, args.seeds, args.out, strict=not args.no_strict)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
