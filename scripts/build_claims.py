#!/usr/bin/env python3
"""Resolve curated claim seeds into fully provenanced claim records.

Stage three of the evidence pipeline.  Takes the analyst-authored claim content
in ``data/claims_seed.yaml``, joins it to the verified spans in
``data/evidence_spans.jsonl``, and writes ``data/claims.jsonl``.

The join is where citation integrity is enforced:

* Chapter, section, printed page and PDF page index are **copied from the
  spans**, never taken from the seed.  The seed file has no fields for them.
  A claim therefore cannot cite a page that was not proven to exist.
* A claim with no evidence is rejected outright.
* A claim citing an unknown span is rejected.
* Units are checked with Pint.  A quantity whose unit does not parse, or which
  has no unit at all, is rejected -- ``dimensionless`` is a unit and must be
  written explicitly.
* Review status is clamped: this pipeline is automated, so it may never emit
  ``HumanVerified``.  Attempting to seed one is an error.

Every rejection is reported with the claim id; the run fails rather than
emitting a partially trustworthy dataset.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import yaml

try:
    import pint
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pint is required: pip install pint") from exc

LOG = logging.getLogger("build_claims")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

#: A review state an automated pipeline may never assign.
FORBIDDEN_AUTOMATED_STATES = {"HumanVerified"}

#: Unit tokens accepted as "explicitly dimensionless".
DIMENSIONLESS_TOKENS = {"dimensionless", "1", "ratio", "-"}

_UREG = pint.UnitRegistry()


class ClaimBuildError(RuntimeError):
    """Raised when a claim seed cannot be turned into a trustworthy record."""


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


def check_unit(unit: Optional[str], claim_id: str, role: str) -> str:
    """Validate a unit token, returning its canonical form.

    A missing unit is always an error.  Dimensionless quantities must say so,
    because 'no unit recorded' and 'this quantity is a pure number' are
    different facts and conflating them silently loses the distinction that
    makes a design factor different from a length.
    """
    if unit is None or str(unit).strip() == "":
        raise ClaimBuildError(
            f"{claim_id}: quantity '{role}' has no unit. "
            "Write 'dimensionless' explicitly for pure numbers."
        )
    token = str(unit).strip()
    if token.lower() in DIMENSIONLESS_TOKENS:
        return "dimensionless"
    try:
        _UREG.Unit(token)
    except Exception as exc:  # pint raises several types
        raise ClaimBuildError(
            f"{claim_id}: quantity '{role}' has unit {token!r}, which Pint cannot parse ({exc})"
        ) from exc
    return token


def build_quantity(raw: Dict[str, Any], claim_id: str) -> Dict[str, Any]:
    """Normalise one quantity entry, preserving what the source printed."""
    role = str(raw.get("role", "unnamed"))
    unit = check_unit(raw.get("unit"), claim_id, role)
    is_range = bool(raw.get("is_range", False))

    if is_range:
        if raw.get("range_min") is None or raw.get("range_max") is None:
            raise ClaimBuildError(f"{claim_id}: quantity '{role}' is a range but lacks bounds")
        value: Optional[float] = None
    else:
        if raw.get("value") is None:
            raise ClaimBuildError(f"{claim_id}: quantity '{role}' has no value")
        value = float(raw["value"])

    return {
        "role": role,
        "value": value,
        "unit": unit,
        "is_range": is_range,
        "range_min": float(raw["range_min"]) if raw.get("range_min") is not None else None,
        "range_max": float(raw["range_max"]) if raw.get("range_max") is not None else None,
        # What the page actually printed, kept verbatim alongside the parsed form.
        "original_value": str(raw.get("original_value", raw.get("value", ""))),
        "original_unit": str(raw.get("original_unit", unit)),
        # Only present when a conversion or evaluation was performed.
        "conversion_method": raw.get("conversion_method"),
        "value_provenance": raw.get("value_provenance", "SourceDerivedValue"),
    }


# ---------------------------------------------------------------------------
# Span index
# ---------------------------------------------------------------------------


def load_spans(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load verified evidence spans, keyed by span id."""
    spans: Dict[str, Dict[str, Any]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            spans[rec["span_id"]] = rec
    return spans


def resolve_provenance(
    span_ids: Sequence[str], spans: Dict[str, Dict[str, Any]], claim_id: str
) -> Dict[str, Any]:
    """Derive the claim's citable location purely from its evidence spans."""
    if not span_ids:
        raise ClaimBuildError(f"{claim_id}: source-derived claim has no evidence span")

    missing = [s for s in span_ids if s not in spans]
    if missing:
        raise ClaimBuildError(f"{claim_id}: cites unknown evidence span(s) {missing}")

    cited = [spans[s] for s in span_ids]
    docs = {c["doc_id"] for c in cited}
    if len(docs) > 1:
        raise ClaimBuildError(
            f"{claim_id}: cites spans from more than one document {sorted(docs)}. "
            "A claim is attributed to exactly one source; use a ClaimAlignment to relate sources."
        )

    first = cited[0]
    # Locations are collected, not collapsed: a claim may legitimately rest on
    # two adjacent pages, and flattening that would misstate the citation.
    locations = [
        {
            "span_id": c["span_id"],
            "pdf_page_index": c["pdf_page_index"],
            "pdf_page_number": c["pdf_page_number"],
            "printed_page": c["printed_page"],
            "page_label": c["page_label"],
            "chapter_number": c["chapter_number"],
            "chapter_title": c["chapter_title"],
            "section_number": c["section_number"],
            "section_title": c["section_title"],
            "block_id": c["block_id"],
            "bbox": c["bbox"],
            "text_integrity": c["text_integrity"],
        }
        for c in cited
    ]
    integrities = {c["text_integrity"] for c in cited}
    return {
        "doc_id": first["doc_id"],
        "source_file_name": first["source_file_name"],
        "book_title": first["book_title"],
        "authors": first["authors"],
        "edition": first["edition"],
        "locations": locations,
        # Worst integrity across the cited spans governs how the claim may be used.
        "text_integrity": (
            "glyph-mismapped" if "glyph-mismapped" in integrities
            else "partial-glyph-loss" if "partial-glyph-loss" in integrities
            else "reliable"
        ),
        "printed_pages": sorted({c["printed_page"] for c in cited if c["printed_page"]}),
        "pdf_page_indices": sorted({c["pdf_page_index"] for c in cited}),
    }


# ---------------------------------------------------------------------------
# Claim assembly
# ---------------------------------------------------------------------------


def build_claim(
    seed: Dict[str, Any], defaults: Dict[str, Any], spans: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Turn one seed into a fully provenanced claim record."""
    claim_id = str(seed["id"])

    review_status = str(seed.get("review_status", defaults.get("review_status", "NeedsReview")))
    if review_status in FORBIDDEN_AUTOMATED_STATES:
        raise ClaimBuildError(
            f"{claim_id}: review_status '{review_status}' cannot be assigned by an automated "
            "pipeline. Human sign-off must be recorded separately, with a reviewer and a date."
        )

    provenance = resolve_provenance(list(seed.get("evidence", [])), spans, claim_id)

    if provenance["doc_id"] != seed.get("doc"):
        raise ClaimBuildError(
            f"{claim_id}: seed says doc '{seed.get('doc')}' but its evidence spans are from "
            f"'{provenance['doc_id']}'"
        )

    quantities = [build_quantity(q, claim_id) for q in (seed.get("quantities") or [])]

    verification = seed.get("verification")
    if verification:
        for key in ("test_recommended", "test_procedure_specified", "acceptance_criterion_specified"):
            if key not in verification:
                raise ClaimBuildError(
                    f"{claim_id}: verification block must state '{key}' explicitly; "
                    "an unstated procedure is a recorded gap, not a default"
                )

    threshold = seed.get("threshold")
    if threshold and "is_universal" not in threshold:
        raise ClaimBuildError(
            f"{claim_id}: threshold block must state 'is_universal' explicitly"
        )

    return {
        "claim_id": claim_id,
        "claim_type": "NormalizedClaim",
        "topic": seed.get("topic"),
        # --- content ---
        "normalized_statement": " ".join(str(seed["normalized_statement"]).split()),
        "subject": seed.get("subject"),
        "predicate": seed.get("predicate"),
        "object": seed.get("object"),
        "conditions": list(seed.get("conditions") or []),
        "exceptions": list(seed.get("exceptions") or []),
        "assumptions": list(seed.get("assumptions") or []),
        "quantities": quantities,
        "threshold": threshold,
        "verification": verification,
        "external_authority": list(seed.get("external_authority") or []),
        "about": list(seed.get("about") or []),
        "analyst_note": (
            " ".join(str(seed["analyst_note"]).split()) if seed.get("analyst_note") else None
        ),
        # --- numbered artifacts cited ---
        "equations": list(seed.get("equations") or []),
        "tables": list(seed.get("tables") or []),
        "figures": list(seed.get("figures") or []),
        "examples": list(seed.get("examples") or []),
        "procedures": list(seed.get("procedures") or []),
        "standards": list(seed.get("standards") or []),
        "equation_transcription": seed.get("equation_transcription"),
        # --- provenance, resolved from verified spans ---
        "evidence_span_ids": list(seed.get("evidence", [])),
        **provenance,
        # --- pipeline metadata ---
        "extraction_method": str(seed.get("extraction_method", defaults.get("extraction_method"))),
        "extraction_confidence": float(
            seed.get("extraction_confidence", defaults.get("extraction_confidence", 0.9))
        ),
        "review_status": review_status,
        "reviewed_by": None,
        "review_date": None,
    }


def run(seeds_path: Path, spans_path: Path, out_path: Path, strict: bool) -> Dict[str, Any]:
    """Build all claims. Returns a summary dict."""
    with seeds_path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    defaults: Dict[str, Any] = doc.get("defaults", {})
    seeds: List[Dict[str, Any]] = doc["claims"]

    spans = load_spans(spans_path)
    LOG.info("loaded %d verified evidence spans", len(spans))

    claims: List[Dict[str, Any]] = []
    errors: List[str] = []
    seen: Set[str] = set()

    for seed in seeds:
        cid = str(seed.get("id", "<no id>"))
        if cid in seen:
            errors.append(f"{cid}: duplicate claim id")
            continue
        seen.add(cid)
        try:
            claims.append(build_claim(seed, defaults, spans))
        except ClaimBuildError as exc:
            errors.append(str(exc))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{cid}: malformed seed ({exc})")

    for err in errors:
        LOG.error("CLAIM REJECTED: %s", err)

    if errors and strict:
        raise SystemExit(
            f"\n{len(errors)} claim seed(s) rejected. No claims were written. "
            "Fix the seeds; do not relax the checks."
        )

    claims.sort(key=lambda c: c["claim_id"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for claim in claims:
            fh.write(json.dumps(claim, ensure_ascii=False, sort_keys=True) + "\n")

    by_doc: Dict[str, int] = defaultdict(int)
    by_topic: Dict[str, int] = defaultdict(int)
    by_status: Dict[str, int] = defaultdict(int)
    used_spans: Set[str] = set()
    for claim in claims:
        by_doc[claim["doc_id"]] += 1
        by_topic[claim["topic"]] += 1
        by_status[claim["review_status"]] += 1
        used_spans.update(claim["evidence_span_ids"])

    summary = {
        "seeds": len(seeds),
        "claims_written": len(claims),
        "rejected": len(errors),
        "rejection_messages": errors,
        "by_document": dict(by_doc),
        "by_topic": dict(sorted(by_topic.items())),
        "by_review_status": dict(by_status),
        "evidence_spans_available": len(spans),
        "evidence_spans_cited": len(used_spans),
        "evidence_spans_uncited": sorted(set(spans) - used_spans),
        "quantities_recorded": sum(len(c["quantities"]) for c in claims),
        "output": str(out_path.relative_to(REPO_ROOT)),
    }
    LOG.info("wrote %d claims -> %s", len(claims), out_path)
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seeds", type=Path, default=REPO_ROOT / "data" / "claims_seed.yaml")
    parser.add_argument("--spans", type=Path, default=REPO_ROOT / "data" / "evidence_spans.jsonl")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "claims.jsonl")
    parser.add_argument("--no-strict", action="store_true", help="diagnostic use only")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    summary = run(args.seeds, args.spans, args.out, strict=not args.no_strict)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["rejected"] else 0


if __name__ == "__main__":
    sys.exit(main())
