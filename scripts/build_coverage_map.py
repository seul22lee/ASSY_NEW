#!/usr/bin/env python3
"""Build the cross-source topic coverage matrix from the two books' outlines.

Phase 3 of the work plan.  The point of this stage is to decide which *domain
modules* the ontology needs, and to see where the books overlap, complement one
another, or stand alone.  It is emphatically NOT an attempt to turn a table of
contents into an ontology: chapter groupings reflect a book's pedagogical
order, not the structure of the domain.  Mott's Chapter 11 covers keys,
couplings and seals together, which tells us about Mott, not about machine
elements.

Inputs
------
``build/<doc>.toc.json``
    The PDF outline, already resolved to page ranges by
    ``scripts/extract_pdf_structure.py``.
``TOPIC_MAP`` below
    An analyst mapping from chapter number to domain topic.  This is
    ontology-engineering judgement, not source-derived content, and is labelled
    as such in the generated document.

Outputs
-------
``data/coverage_matrix.csv``   one row per topic, one column group per source
``docs/source_coverage_map.md``  the same, as a readable comparison
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

LOG = logging.getLogger("build_coverage_map")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"


@dataclass(frozen=True)
class Topic:
    """A domain module the ontology may need to cover."""

    key: str
    label: str
    group: str


#: Domain topics.  Ordered roughly from general principles to specific elements,
#: mirroring the ontology's own Level 1 -> Level 4 progression.
TOPICS: List[Topic] = [
    Topic("design-process",      "Design process, requirements and evaluation criteria", "Principles"),
    Topic("uncertainty-safety",  "Design factor, safety, reliability and uncertainty",   "Principles"),
    Topic("standards-economics", "Standards, codes, economics and professional practice","Principles"),
    Topic("materials",           "Engineering materials and properties",                 "Principles"),
    Topic("stress-analysis",     "Load and stress analysis",                             "Principles"),
    Topic("combined-stress",     "Combined stress and stress transformation",            "Principles"),
    Topic("deflection",          "Deflection and stiffness",                             "Principles"),
    Topic("static-failure",      "Failure from static loading",                          "Failure"),
    Topic("fatigue",             "Fatigue and variable loading",                         "Failure"),
    Topic("columns",             "Columns and buckling",                                 "Failure"),
    Topic("shafts",              "Shaft design",                                         "Elements"),
    Topic("shaft-hub",           "Shaft/hub connections: keys, splines, pins, setscrews", "Elements"),
    Topic("couplings",           "Couplings and universal joints",                       "Elements"),
    Topic("seals",               "Seals",                                                "Elements"),
    Topic("rolling-bearings",    "Rolling-contact bearings",                             "Elements"),
    Topic("plain-bearings",      "Plain bearings, journal bearings and lubrication",     "Elements"),
    Topic("gear-kinematics",     "Gear kinematics and general gearing",                  "Elements"),
    Topic("spur-gears",          "Spur gear design",                                     "Elements"),
    Topic("other-gears",         "Helical, bevel and worm gearing",                      "Elements"),
    Topic("flexible-drives",     "Belt, chain and wire-rope drives",                     "Elements"),
    Topic("springs",             "Springs",                                              "Elements"),
    Topic("threaded-fasteners",  "Screws, fasteners and bolted joints",                  "Elements"),
    Topic("permanent-joints",    "Welded, bonded and riveted joints",                    "Elements"),
    Topic("clutches-brakes",     "Clutches, brakes and flywheels",                       "Elements"),
    Topic("tolerances-fits",     "Tolerances, fits and interference fits",               "Elements"),
    Topic("linear-motion",       "Linear motion elements",                               "Elements"),
    Topic("frames",              "Machine frames and structural members",                "Elements"),
    Topic("motors-controls",     "Electric motors and controls",                         "System"),
    Topic("power-transmission",  "Integrated power transmission design",                 "System"),
    Topic("fea",                 "Finite-element analysis",                              "Methods"),
    Topic("gdt",                 "Geometric dimensioning and tolerancing",               "Methods"),
    Topic("design-projects",     "Design projects and case studies",                     "Methods"),
]

TOPIC_BY_KEY: Dict[str, Topic] = {t.key: t for t in TOPICS}

#: ANALYST MAPPING from chapter number to topic keys.
#: A chapter may map to several topics; a topic may be covered by several
#: chapters.  Derived by reading the chapter and section titles extracted from
#: each PDF's own outline.
TOPIC_MAP: Dict[str, Dict[str, List[str]]] = {
    "mott6": {
        "1":  ["design-process", "standards-economics"],
        "2":  ["materials"],
        # Mott has no separate deflection chapter, but covers it in sections
        # 3-5, 3-9, 3-18 and 3-19, and again as shaft rigidity in 12-10.
        "3":  ["stress-analysis", "deflection"],
        "4":  ["combined-stress"],
        "5":  ["fatigue", "static-failure", "uncertainty-safety"],
        "6":  ["columns"],
        "7":  ["flexible-drives"],
        "8":  ["gear-kinematics"],
        "9":  ["spur-gears"],
        "10": ["other-gears"],
        "11": ["shaft-hub", "couplings", "seals"],
        "12": ["shafts", "deflection"],
        "13": ["tolerances-fits"],
        "14": ["rolling-bearings"],
        "15": ["power-transmission"],
        "16": ["plain-bearings"],
        "17": ["linear-motion"],
        "18": ["springs"],
        "19": ["threaded-fasteners"],
        "20": ["frames", "threaded-fasteners", "permanent-joints"],
        "21": ["motors-controls"],
        "22": ["clutches-brakes"],
        "23": ["design-projects"],
    },
    "shigley10": {
        "1":  ["design-process", "uncertainty-safety", "standards-economics", "tolerances-fits"],
        "2":  ["materials"],
        "3":  ["stress-analysis", "combined-stress"],
        "4":  ["deflection", "columns"],
        "5":  ["static-failure"],
        "6":  ["fatigue"],
        "7":  ["shafts", "shaft-hub", "tolerances-fits"],
        "8":  ["threaded-fasteners"],
        "9":  ["permanent-joints"],
        "10": ["springs"],
        "11": ["rolling-bearings"],
        "12": ["plain-bearings"],
        "13": ["gear-kinematics"],
        "14": ["spur-gears"],
        "15": ["other-gears"],
        "16": ["clutches-brakes", "couplings"],
        "17": ["flexible-drives"],
        "18": ["power-transmission", "design-projects"],
        "19": ["fea"],
        "20": ["gdt"],
    },
}


@dataclass
class ChapterInfo:
    """A numbered chapter, with the page range taken from the PDF outline."""

    number: str
    title: str
    start_index: int
    end_index: int
    start_printed: Optional[str]
    section_count: int = 0


def load_chapters(build_dir: Path, doc_id: str) -> Dict[str, ChapterInfo]:
    """Read numbered chapters and their section counts from the resolved outline."""
    nodes = json.loads((build_dir / f"{doc_id}.toc.json").read_text(encoding="utf-8"))
    chapters: Dict[str, ChapterInfo] = {}
    for node in nodes:
        if node["kind"] != "chapter" or not node["number"] or "-" in node["number"]:
            continue
        # Keep the first (outermost) occurrence: index letters at the back of the
        # book also parse as single tokens and must not overwrite real chapters.
        if node["number"] in chapters:
            continue
        chapters[node["number"]] = ChapterInfo(
            number=node["number"],
            title=node["title"],
            start_index=node["start_pdf_page_index"],
            end_index=node["end_pdf_page_index"] or node["start_pdf_page_index"],
            start_printed=node["start_page_label"],
        )
    for node in nodes:
        if node["kind"] != "section" or not node["number"]:
            continue
        chapter_no = node["number"].split("-")[0]
        if chapter_no in chapters:
            chapters[chapter_no].section_count += 1
    return chapters


def build_matrix(build_dir: Path, doc_ids: Sequence[str]) -> List[Dict[str, Any]]:
    """Assemble one row per topic with each source's coverage."""
    chapters = {d: load_chapters(build_dir, d) for d in doc_ids}
    rows: List[Dict[str, Any]] = []

    for topic in TOPICS:
        row: Dict[str, Any] = {"topic_key": topic.key, "topic": topic.label, "group": topic.group}
        covering: Dict[str, List[ChapterInfo]] = {}
        for doc_id in doc_ids:
            hits = [
                chapters[doc_id][num]
                for num, keys in TOPIC_MAP[doc_id].items()
                if topic.key in keys and num in chapters[doc_id]
            ]
            hits.sort(key=lambda c: int(c.number))
            covering[doc_id] = hits
            row[f"{doc_id}_chapters"] = ";".join(c.number for c in hits)
            row[f"{doc_id}_chapter_titles"] = " | ".join(c.title for c in hits)
            row[f"{doc_id}_printed_pages"] = ";".join(str(c.start_printed) for c in hits)
            row[f"{doc_id}_pdf_page_range"] = ";".join(
                f"{c.start_index}-{c.end_index}" for c in hits
            )
            row[f"{doc_id}_pages"] = sum(c.end_index - c.start_index + 1 for c in hits)
            row[f"{doc_id}_sections"] = sum(c.section_count for c in hits)
            row[f"{doc_id}_covered"] = "yes" if hits else "no"

        a, b = doc_ids[0], doc_ids[1]
        if covering[a] and covering[b]:
            row["coverage"] = "both"
        elif covering[a]:
            row["coverage"] = f"{a} only"
        elif covering[b]:
            row["coverage"] = f"{b} only"
        else:
            row["coverage"] = "neither"

        # Depth ratio flags a topic one book treats far more fully than the other.
        pa, pb = row[f"{a}_pages"], row[f"{b}_pages"]
        if pa and pb:
            ratio = max(pa, pb) / min(pa, pb)
            row["depth_note"] = (
                f"comparable depth ({pa} vs {pb} pages)" if ratio < 1.6
                else f"{'mott6' if pa > pb else 'shigley10'} substantially deeper "
                     f"({pa} vs {pb} pages)"
            )
        else:
            row["depth_note"] = "single-source topic" if (pa or pb) else "not covered"
        rows.append(row)
    return rows


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    LOG.info("wrote %d topic rows -> %s", len(rows), path)


def write_markdown(
    rows: List[Dict[str, Any]], build_dir: Path, doc_ids: Sequence[str],
    config: Dict[str, Any], path: Path,
) -> None:
    """Render the coverage comparison as documentation."""
    a, b = doc_ids
    metas = {d: json.loads((build_dir / f"{d}.meta.json").read_text(encoding="utf-8")) for d in doc_ids}
    both = [r for r in rows if r["coverage"] == "both"]
    only_a = [r for r in rows if r["coverage"] == f"{a} only"]
    only_b = [r for r in rows if r["coverage"] == f"{b} only"]
    neither = [r for r in rows if r["coverage"] == "neither"]

    lines: List[str] = []
    lines.append("# Source coverage map\n")
    lines.append(
        "Generated by `scripts/build_coverage_map.py`. Chapter numbers, titles and page\n"
        "ranges come from each PDF's own outline; the mapping of chapters onto domain\n"
        "topics is **analyst judgement**, recorded in `TOPIC_MAP` in that script, and is\n"
        "not a claim about either book.\n"
    )
    lines.append("## The two sources\n")
    lines.append("| | " + " | ".join(metas[d]["bibliographic"]["title"] for d in doc_ids) + " |")
    lines.append("|---|" + "---|" * len(doc_ids))
    for label, getter in [
        ("Authors", lambda m: ", ".join(m["bibliographic"]["authors"])),
        ("Edition", lambda m: m["bibliographic"]["edition"]),
        ("Publisher / year", lambda m: f"{m['bibliographic']['publisher']}, {m['bibliographic']['year']}"),
        ("PDF pages", lambda m: str(m["page_count"])),
        ("Outline entries", lambda m: str(m["toc_entry_count"])),
        ("Numbered chapters", lambda m: str(len(TOPIC_MAP[m["doc_id"]]))),
        ("Text-layer verdict", lambda m: m["text_layer"]["math_text_reliability"]),
        ("Math-heavy pages", lambda m: f"{m['text_layer']['pages_flagged_math_heavy']} "
                                       f"({m['text_layer']['pages_flagged_math_heavy_pct']}%)"),
    ]:
        lines.append(f"| {label} | " + " | ".join(getter(metas[d]) for d in doc_ids) + " |")

    lines.append(f"\n## Coverage summary\n")
    lines.append(f"- Topics covered by **both** sources: **{len(both)}** of {len(rows)}")
    lines.append(f"- Covered by **{a} only**: **{len(only_a)}**")
    lines.append(f"- Covered by **{b} only**: **{len(only_b)}**")
    lines.append(f"- Covered by neither (topic reserved for future extension): **{len(neither)}**\n")

    lines.append("## Coverage matrix\n")
    lines.append(f"| Topic | Group | {a} ch. | pages | {b} ch. | pages | Coverage | Depth |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r['topic']} | {r['group']} "
            f"| {r[f'{a}_chapters'] or '—'} | {r[f'{a}_pages'] or '—'} "
            f"| {r[f'{b}_chapters'] or '—'} | {r[f'{b}_pages'] or '—'} "
            f"| {r['coverage']} | {r['depth_note']} |"
        )

    lines.append("\n## Overlapping topics — where cross-book alignment is possible\n")
    for r in sorted(both, key=lambda r: -(r[f"{a}_pages"] + r[f"{b}_pages"])):
        lines.append(
            f"- **{r['topic']}** — {a} ch. {r[f'{a}_chapters']} "
            f"({r[f'{a}_pages']} pp.), {b} ch. {r[f'{b}_chapters']} "
            f"({r[f'{b}_pages']} pp.). {r['depth_note']}."
        )

    lines.append("\n## Single-source topics — no cross-book comparison is possible\n")
    for r in only_a:
        lines.append(f"- **{r['topic']}** — {a} only (ch. {r[f'{a}_chapters']}, {r[f'{a}_pages']} pp.).")
    for r in only_b:
        lines.append(f"- **{r['topic']}** — {b} only (ch. {r[f'{b}_chapters']}, {r[f'{b}_pages']} pp.).")

    lines.append("\n## How this shaped the ontology\n")
    lines.append(
        "1. **Modules follow function, not chapters.** Mott gathers keys, couplings and\n"
        "   seals into one chapter; Shigley splits shaft components across Chapter 7 and\n"
        "   distributes clutches, brakes, couplings and flywheels into Chapter 16. Neither\n"
        "   grouping is a fact about machine elements, so `ontology/machine-elements/`\n"
        "   is organised by the function a family delivers.\n"
        "2. **Pilot topics were chosen from the overlap.** Every pilot topic in v0.1 is\n"
        "   covered by both books, which is what makes cross-source alignment possible at\n"
        "   all.\n"
        "3. **Single-source topics are marked, not hidden.** Where only one book covers a\n"
        "   topic, the ontology can hold claims but no `ev:ClaimAlignment`, and queries\n"
        "   asking whether the books agree correctly return nothing rather than a\n"
        "   fabricated consensus.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LOG.info("wrote %s", path)


def run(config: Dict[str, Any]) -> Dict[str, Any]:
    build_dir = REPO_ROOT / config["paths"]["build_dir"]
    data_dir = REPO_ROOT / config["paths"]["data_dir"]
    docs_dir = REPO_ROOT / config["paths"]["docs_dir"]
    doc_ids = list(config["sources"].keys())

    rows = build_matrix(build_dir, doc_ids)
    write_csv(rows, data_dir / "coverage_matrix.csv")
    write_markdown(rows, build_dir, doc_ids, config, docs_dir / "source_coverage_map.md")

    counts = {"both": 0, "neither": 0}
    for r in rows:
        counts[r["coverage"]] = counts.get(r["coverage"], 0) + 1
    return {"topics": len(rows), "coverage_counts": counts}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    with args.config.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    print(json.dumps(run(config), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
