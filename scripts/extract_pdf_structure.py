#!/usr/bin/env python3
"""Extract document structure and provenance anchors from the source textbooks.

This is the first stage of the evidence pipeline described in
``docs/ontology_design.md``::

    PDF content -> EvidenceSpan -> ExtractedClaim -> NormalizedClaim
                -> CandidateDesignRule -> HumanValidatedRule -> axiom / rule

The script never interprets engineering content.  It only records *where*
things are, and *how trustworthy the text layer is*, so that every later stage
can cite a verifiable location instead of a remembered one.

For each configured source document it writes, into ``build/``:

``<doc>.meta.json``
    Document-level metadata, SHA-256, page count and text-integrity summary.
``<doc>.pages.jsonl``
    One record per page: PDF page index (0-based), PDF page number (1-based),
    the *printed* page label, character counts, math-font ratio and flags.
``<doc>.toc.json``
    The PDF outline, resolved into a part/chapter/section hierarchy with
    start and end page indices.
``<doc>.blocks.jsonl``
    Text blocks with bounding boxes, suitable for anchoring EvidenceSpans.
``<doc>.artifacts.jsonl``
    Detected in-text references to numbered equations, tables, figures and
    example problems, each with a page and a bounding box.

Design notes
------------
* PDF page index and printed page label are kept as *separate* fields and are
  never conflated.  Both books have >20 pages of front matter with roman
  numerals, so the offset is neither constant nor inferable.
* Text reliability is measured, not assumed.  The fraction of characters set
  in a recognised mathematics font is recorded per page, because in the
  Shigley PDF those glyphs are mis-mapped onto ASCII characters and the
  extracted text is therefore wrong in a way that looks plausible.
* The script is idempotent: re-running it reproduces byte-identical outputs
  for an unchanged input PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyMuPDF is required: pip install pymupdf") from exc

import yaml

LOG = logging.getLogger("extract_pdf_structure")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"


# ---------------------------------------------------------------------------
# Data records
# ---------------------------------------------------------------------------


@dataclass
class PageRecord:
    """Per-page provenance and text-quality record.

    Attributes
    ----------
    pdf_page_index:
        Zero-based index as used by PyMuPDF.  This is the canonical
        machine-facing locator.
    pdf_page_number:
        One-based page number, i.e. what a PDF viewer shows in its page box.
    page_label:
        The *printed* page number as declared by the PDF's page-label tree
        (``'xvii'``, ``'184'``, ``'Cover'``).  May be ``None``.
    printed_page:
        ``page_label`` when it looks like an arabic printed page number,
        otherwise ``None``.  Kept separate so that downstream citation code
        never has to guess.
    """

    doc_id: str
    pdf_page_index: int
    pdf_page_number: int
    page_label: Optional[str]
    printed_page: Optional[str]
    label_style: str  # 'arabic' | 'roman' | 'named' | 'none'
    char_count: int
    block_count: int
    image_count: int
    math_font_chars: int
    math_font_char_ratio: float
    dominant_fonts: List[str]
    needs_review: bool
    ocr_candidate: bool
    width: float
    height: float


@dataclass
class TocNode:
    """A node of the resolved table of contents."""

    doc_id: str
    node_id: str
    level: int
    kind: str  # 'part' | 'chapter' | 'section' | 'frontmatter' | 'backmatter'
    title: str
    number: Optional[str]  # '1', '7-7', 'A' ... when parseable
    parent_id: Optional[str]
    start_pdf_page_index: int
    end_pdf_page_index: Optional[int]
    start_page_label: Optional[str]
    children: List[str] = field(default_factory=list)


@dataclass
class BlockRecord:
    """A text block with a bounding box, usable as an EvidenceSpan anchor."""

    doc_id: str
    pdf_page_index: int
    block_id: str
    block_no: int
    bbox: Tuple[float, float, float, float]
    text: str
    char_count: int
    math_font_char_ratio: float
    fonts: List[str]


@dataclass
class ArtifactRecord:
    """A detected reference to a numbered equation, table, figure or example."""

    doc_id: str
    pdf_page_index: int
    page_label: Optional[str]
    artifact_kind: str  # 'equation' | 'table' | 'figure' | 'example'
    artifact_number: str  # e.g. '7-7'
    matched_text: str
    bbox: Optional[Tuple[float, float, float, float]]
    block_id: Optional[str]
    is_caption_like: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ROMAN_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)
_ARABIC_RE = re.compile(r"^\d+$")
# Chapter/section numbers such as '1-1', '7–7', '11–2'.  Both books use an
# en-dash in print; the text layer sometimes yields a hyphen.
_SECTION_NUM_RE = re.compile(r"^\s*(?:(\d{1,2})\s*[–\-—]\s*(\d{1,3})|(\d{1,2}))\s+")
_PART_RE = re.compile(r"^\s*part\s+(\w+)\b", re.IGNORECASE)
_APPENDIX_RE = re.compile(r"^\s*appendix\b", re.IGNORECASE)

_FRONTMATTER_TITLES = {
    "cover", "title", "title page", "copyright", "copyright page", "contents",
    "preface", "acknowledgments", "acknowledgements", "dedication",
    "about the authors", "list of symbols",
}
_BACKMATTER_TITLES = {"index", "answers", "bibliography", "references", "glossary"}


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    """Return the SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def classify_label(label: Optional[str]) -> str:
    """Classify a PDF page label as ``arabic``, ``roman``, ``named`` or ``none``."""
    if not label:
        return "none"
    stripped = label.strip()
    if _ARABIC_RE.match(stripped):
        return "arabic"
    if _ROMAN_RE.match(stripped):
        return "roman"
    return "named"


def is_math_font(font_name: str, math_font_markers: Sequence[str]) -> bool:
    """Return ``True`` when *font_name* looks like a mathematics font.

    Subset-embedded fonts carry a six-letter prefix (``LFHVJP+PearsonMATHPRO08``)
    so matching is done on substrings, case-insensitively.
    """
    lowered = font_name.lower()
    return any(marker.lower() in lowered for marker in math_font_markers)


def parse_section_number(title: str) -> Optional[str]:
    """Extract a leading chapter or section number from a TOC title.

    ``'7–7 Keys and Pins'`` -> ``'7-7'``; ``'11 Rolling-Contact Bearings'`` ->
    ``'11'``.  Returns ``None`` when the title does not start with a number.
    """
    match = _SECTION_NUM_RE.match(title)
    if not match:
        return None
    if match.group(1) is not None:
        return f"{match.group(1)}-{match.group(2)}"
    return match.group(3)


def classify_toc_kind(level: int, title: str) -> str:
    """Classify a TOC entry into part / chapter / section / front / back matter."""
    normalized = title.strip().lower()
    if normalized in _FRONTMATTER_TITLES:
        return "frontmatter"
    if normalized in _BACKMATTER_TITLES:
        return "backmatter"
    if _PART_RE.match(title):
        return "part"
    if _APPENDIX_RE.match(title):
        return "backmatter"
    number = parse_section_number(title)
    if number and "-" in number:
        return "section"
    if number and level <= 2:
        return "chapter"
    return "section" if level >= 3 else "chapter"


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------


class DocumentExtractor:
    """Extract structure, provenance anchors and text-quality metrics."""

    def __init__(
        self,
        doc_id: str,
        pdf_path: Path,
        source_cfg: Dict[str, Any],
        extraction_cfg: Dict[str, Any],
    ) -> None:
        self.doc_id = doc_id
        self.pdf_path = pdf_path
        self.source_cfg = source_cfg
        self.extraction_cfg = extraction_cfg
        self.math_font_markers: List[str] = list(source_cfg.get("math_fonts") or [])
        self.math_ratio_threshold: float = float(
            extraction_cfg.get("math_font_char_ratio_threshold", 0.06)
        )
        self.min_chars: int = int(extraction_cfg.get("min_chars_per_text_page", 40))
        patterns = extraction_cfg.get("patterns", {})
        self._equation_re = re.compile(patterns["equation_number"])
        self._table_re = re.compile(patterns["table_caption"])
        self._figure_re = re.compile(patterns["figure_caption"])
        self._example_re = re.compile(patterns["example_marker"])
        self.errors: List[Dict[str, Any]] = []
        self._doc: Optional["fitz.Document"] = None

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> "DocumentExtractor":
        LOG.info("[%s] opening %s", self.doc_id, self.pdf_path.name)
        self._doc = fitz.open(self.pdf_path)
        if self._doc.needs_pass:
            raise RuntimeError(f"{self.pdf_path.name} is password protected")
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    @property
    def doc(self) -> "fitz.Document":
        if self._doc is None:
            raise RuntimeError("DocumentExtractor used outside its context manager")
        return self._doc

    # -- page labels -------------------------------------------------------

    def page_label(self, index: int) -> Optional[str]:
        """Return the printed page label for *index*, or ``None``."""
        try:
            label = self.doc[index].get_label()
        except Exception as exc:  # pragma: no cover - defensive
            self._record_error("page_label", index, str(exc))
            return None
        return label or None

    def _record_error(self, stage: str, page_index: Optional[int], message: str) -> None:
        LOG.warning("[%s] %s error on page %s: %s", self.doc_id, stage, page_index, message)
        self.errors.append(
            {
                "doc_id": self.doc_id,
                "stage": stage,
                "pdf_page_index": page_index,
                "message": message,
            }
        )

    # -- pages -------------------------------------------------------------

    def iter_pages(self) -> Iterator[Tuple[PageRecord, List[BlockRecord], List[ArtifactRecord]]]:
        """Yield ``(page, blocks, artifacts)`` for every page in the document."""
        for index in range(self.doc.page_count):
            try:
                yield self._process_page(index)
            except Exception as exc:  # pragma: no cover - defensive
                self._record_error("page", index, repr(exc))
                label = self.page_label(index)
                empty = PageRecord(
                    doc_id=self.doc_id,
                    pdf_page_index=index,
                    pdf_page_number=index + 1,
                    page_label=label,
                    printed_page=label if classify_label(label) == "arabic" else None,
                    label_style=classify_label(label),
                    char_count=0,
                    block_count=0,
                    image_count=0,
                    math_font_chars=0,
                    math_font_char_ratio=0.0,
                    dominant_fonts=[],
                    needs_review=True,
                    ocr_candidate=True,
                    width=0.0,
                    height=0.0,
                )
                yield empty, [], []

    def _process_page(
        self, index: int
    ) -> Tuple[PageRecord, List[BlockRecord], List[ArtifactRecord]]:
        page = self.doc[index]
        label = self.page_label(index)
        label_style = classify_label(label)
        raw = page.get_text("dict")

        blocks: List[BlockRecord] = []
        total_chars = 0
        math_chars = 0
        font_counter: Dict[str, int] = {}

        for block in raw.get("blocks", []):
            if block.get("type") != 0:  # 0 == text block
                continue
            block_no = int(block.get("number", len(blocks)))
            lines_text: List[str] = []
            block_chars = 0
            block_math = 0
            block_fonts: Dict[str, int] = {}
            for line in block.get("lines", []):
                span_texts: List[str] = []
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    font = span.get("font", "")
                    n = len(text)
                    block_chars += n
                    block_fonts[font] = block_fonts.get(font, 0) + n
                    font_counter[font] = font_counter.get(font, 0) + n
                    if is_math_font(font, self.math_font_markers):
                        block_math += n
                    span_texts.append(text)
                lines_text.append("".join(span_texts))
            text = "\n".join(lines_text).strip()
            if not text:
                continue
            total_chars += block_chars
            math_chars += block_math
            bbox = tuple(round(float(v), 2) for v in block.get("bbox", (0, 0, 0, 0)))
            blocks.append(
                BlockRecord(
                    doc_id=self.doc_id,
                    pdf_page_index=index,
                    block_id=f"{self.doc_id}/p{index}/b{block_no}",
                    block_no=block_no,
                    bbox=bbox,  # type: ignore[arg-type]
                    text=text,
                    char_count=block_chars,
                    math_font_char_ratio=round(block_math / block_chars, 4) if block_chars else 0.0,
                    fonts=sorted(block_fonts, key=block_fonts.get, reverse=True)[:4],  # type: ignore[arg-type]
                )
            )

        ratio = round(math_chars / total_chars, 4) if total_chars else 0.0
        try:
            image_count = len(page.get_images(full=True))
        except Exception:  # pragma: no cover - defensive
            image_count = 0

        record = PageRecord(
            doc_id=self.doc_id,
            pdf_page_index=index,
            pdf_page_number=index + 1,
            page_label=label,
            printed_page=label if label_style == "arabic" else None,
            label_style=label_style,
            char_count=total_chars,
            block_count=len(blocks),
            image_count=image_count,
            math_font_chars=math_chars,
            math_font_char_ratio=ratio,
            dominant_fonts=sorted(font_counter, key=font_counter.get, reverse=True)[:5],  # type: ignore[arg-type]
            needs_review=ratio > self.math_ratio_threshold,
            ocr_candidate=total_chars < self.min_chars,
            width=round(float(page.rect.width), 2),
            height=round(float(page.rect.height), 2),
        )
        artifacts = self._detect_artifacts(index, label, blocks)
        return record, blocks, artifacts

    # -- artifacts ---------------------------------------------------------

    def _detect_artifacts(
        self,
        index: int,
        label: Optional[str],
        blocks: Sequence[BlockRecord],
    ) -> List[ArtifactRecord]:
        """Find numbered equations, tables, figures and examples on one page.

        The detector is deliberately recall-oriented and *not* authoritative:
        it produces candidate anchors for human curation, never final claims.
        A match is marked ``is_caption_like`` when it starts its block, which
        is the usual shape of a real caption as opposed to a cross-reference.
        """
        found: List[ArtifactRecord] = []
        specs = (
            ("equation", self._equation_re),
            ("table", self._table_re),
            ("figure", self._figure_re),
            ("example", self._example_re),
        )
        for block in blocks:
            for kind, regex in specs:
                for match in regex.finditer(block.text):
                    groups = [g for g in match.groups() if g is not None]
                    if len(groups) < 2:
                        continue
                    number = f"{groups[-2]}-{groups[-1]}"
                    found.append(
                        ArtifactRecord(
                            doc_id=self.doc_id,
                            pdf_page_index=index,
                            page_label=label,
                            artifact_kind=kind,
                            artifact_number=number,
                            matched_text=match.group(0).strip(),
                            bbox=block.bbox,
                            block_id=block.block_id,
                            is_caption_like=match.start() <= 2,
                        )
                    )
        return found

    # -- table of contents -------------------------------------------------

    def build_toc(self) -> List[TocNode]:
        """Resolve the PDF outline into a hierarchy with page ranges."""
        raw_toc = self.doc.get_toc(simple=True)
        if not raw_toc:
            self._record_error("toc", None, "document has no outline")
            return []

        nodes: List[TocNode] = []
        stack: List[Tuple[int, str]] = []  # (level, node_id)
        for i, entry in enumerate(raw_toc):
            level, title, one_based_page = entry[0], entry[1], entry[2]
            start_index = max(0, int(one_based_page) - 1)
            node_id = f"{self.doc_id}/toc/{i:04d}"
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent_id = stack[-1][1] if stack else None
            node = TocNode(
                doc_id=self.doc_id,
                node_id=node_id,
                level=level,
                kind=classify_toc_kind(level, title),
                title=title.strip(),
                number=parse_section_number(title),
                parent_id=parent_id,
                start_pdf_page_index=start_index,
                end_pdf_page_index=None,
                start_page_label=self.page_label(start_index),
            )
            nodes.append(node)
            stack.append((level, node_id))

        by_id = {n.node_id: n for n in nodes}
        for node in nodes:
            if node.parent_id and node.parent_id in by_id:
                by_id[node.parent_id].children.append(node.node_id)

        # End page = (start of the next entry at the same or shallower level) - 1
        for i, node in enumerate(nodes):
            end: Optional[int] = None
            for later in nodes[i + 1 :]:
                if later.level <= node.level:
                    end = max(node.start_pdf_page_index, later.start_pdf_page_index - 1)
                    break
            node.end_pdf_page_index = end if end is not None else self.doc.page_count - 1
        return nodes

    # -- document metadata -------------------------------------------------

    def build_meta(self, pages: Sequence[PageRecord], toc: Sequence[TocNode]) -> Dict[str, Any]:
        """Assemble the document-level metadata and integrity summary."""
        arabic = [p for p in pages if p.label_style == "arabic"]
        roman = [p for p in pages if p.label_style == "roman"]
        offsets = {
            p.pdf_page_index - int(p.printed_page)
            for p in arabic
            if p.printed_page and p.printed_page.isdigit()
        }
        flagged = [p for p in pages if p.needs_review]
        ocr_pages = [p for p in pages if p.ocr_candidate]
        return {
            "doc_id": self.doc_id,
            "file_name": self.pdf_path.name,
            "sha256": sha256_of(self.pdf_path),
            "byte_size": self.pdf_path.stat().st_size,
            "pdf_metadata": dict(self.doc.metadata or {}),
            "bibliographic": {
                "title": self.source_cfg.get("title"),
                "authors": self.source_cfg.get("authors", []),
                "edition": self.source_cfg.get("edition"),
                "edition_ordinal": self.source_cfg.get("edition_ordinal"),
                "publisher": self.source_cfg.get("publisher"),
                "year": self.source_cfg.get("year"),
            },
            "page_count": self.doc.page_count,
            "toc_entry_count": len(toc),
            "page_labels": {
                "available": any(p.page_label for p in pages),
                "arabic_labelled_pages": len(arabic),
                "roman_labelled_pages": len(roman),
                # A single value here means one constant front-matter offset;
                # several values mean the offset changes and must never be
                # computed on the fly.
                "distinct_index_minus_printed_offsets": sorted(offsets),
                "first_arabic_pdf_page_index": arabic[0].pdf_page_index if arabic else None,
            },
            "text_layer": {
                "declared": self.source_cfg.get("text_layer"),
                "math_text_reliability": self.source_cfg.get("math_text_reliability"),
                "total_chars": sum(p.char_count for p in pages),
                "pages_flagged_math_heavy": len(flagged),
                "pages_flagged_math_heavy_pct": round(100 * len(flagged) / max(1, len(pages)), 2),
                "ocr_candidate_pages": len(ocr_pages),
                "ocr_candidate_page_indices": [p.pdf_page_index for p in ocr_pages][:200],
                "math_font_markers": self.math_font_markers,
            },
            "extraction_errors": self.errors,
        }


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def write_jsonl(path: Path, records: Iterable[Any]) -> int:
    """Write dataclass or dict *records* to *path* as JSON Lines. Returns count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            payload = asdict(record) if hasattr(record, "__dataclass_fields__") else record
            fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_json(path: Path, payload: Any) -> None:
    """Write *payload* to *path* as pretty, deterministically ordered JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_config(path: Path) -> Dict[str, Any]:
    """Load the YAML configuration file."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(config: Dict[str, Any], only: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Run extraction for every configured source (or only the named ones)."""
    build_dir = REPO_ROOT / config["paths"]["build_dir"]
    build_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {"documents": {}, "config_version": config["project"]["version"]}

    for doc_id, source_cfg in config["sources"].items():
        if only and doc_id not in only:
            continue
        pdf_path = REPO_ROOT / source_cfg["file"]
        if not pdf_path.exists():
            LOG.error("[%s] missing PDF: %s", doc_id, pdf_path)
            summary["documents"][doc_id] = {"status": "missing", "path": str(pdf_path)}
            continue

        with DocumentExtractor(doc_id, pdf_path, source_cfg, config["extraction"]) as ex:
            pages: List[PageRecord] = []
            blocks: List[BlockRecord] = []
            artifacts: List[ArtifactRecord] = []
            for page, page_blocks, page_artifacts in ex.iter_pages():
                pages.append(page)
                blocks.extend(page_blocks)
                artifacts.extend(page_artifacts)
                if page.pdf_page_index and page.pdf_page_index % 200 == 0:
                    LOG.info("[%s] processed %d pages", doc_id, page.pdf_page_index)
            toc = ex.build_toc()
            meta = ex.build_meta(pages, toc)

            n_pages = write_jsonl(build_dir / f"{doc_id}.pages.jsonl", pages)
            n_blocks = write_jsonl(build_dir / f"{doc_id}.blocks.jsonl", blocks)
            n_art = write_jsonl(build_dir / f"{doc_id}.artifacts.jsonl", artifacts)
            write_json(build_dir / f"{doc_id}.toc.json", [asdict(n) for n in toc])
            write_json(build_dir / f"{doc_id}.meta.json", meta)

        LOG.info(
            "[%s] pages=%d blocks=%d artifacts=%d toc=%d errors=%d",
            doc_id, n_pages, n_blocks, n_art, len(toc), len(ex.errors),
        )
        summary["documents"][doc_id] = {
            "status": "ok",
            "pages": n_pages,
            "blocks": n_blocks,
            "artifacts": n_art,
            "toc_entries": len(toc),
            "errors": len(ex.errors),
            "sha256": meta["sha256"],
            "math_heavy_page_pct": meta["text_layer"]["pages_flagged_math_heavy_pct"],
            "ocr_candidate_pages": meta["text_layer"]["ocr_candidate_pages"],
        }

    write_json(build_dir / "extraction_summary.json", summary)
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--only", nargs="*", help="restrict to these doc_ids")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    config = load_config(args.config)
    summary = run(config, args.only)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
