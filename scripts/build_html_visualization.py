#!/usr/bin/env python3
"""Build the offline HTML visualization application in ``outputs/visualizations/``.

One command rebuilds everything::

    python3 scripts/build_html_visualization.py

Options::

    --clean      remove outputs/visualizations/ first (vendor/ is untouched)
    --validate   additionally run SHACL validation and the unit-test suite,
                 writing the diagnostic outputs/visualizations/data/status.json
    --open       print (and, where possible, launch) the local server URL
    --check-reproducible
                 build twice into temporary directories and confirm the
                 generated files are byte-identical

The build is idempotent. No timestamp is written into any generated file, so
two runs over unchanged inputs produce byte-identical output. ``status.json``
is the single diagnostic artefact and is excluded from that comparison because
it depends on whether ``--validate`` was passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_visualization_data as bvd  # noqa: E402

LOG = logging.getLogger("build_html_visualization")
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

TEMPLATE_DIR = REPO_ROOT / "scripts" / "viz_templates"
VENDOR_DIR = REPO_ROOT / "vendor"
OUT_DIR = REPO_ROOT / "outputs" / "visualizations"

#: Copied verbatim from the template directory into the generated app.
TEMPLATES = {
    "index.html": "index.html",
    "app.css": "assets/app.css",
    "app.js": "assets/app.js",
}

#: Vendored runtime dependencies, copied so the app never touches a CDN.
VENDOR_FILES = {
    "cytoscape/cytoscape.min.js": "assets/vendor/cytoscape.min.js",
    "cytoscape/LICENSE": "assets/vendor/cytoscape-LICENSE.txt",
    "cytoscape/vendor.json": "assets/vendor/vendor.json",
}

#: Diagnostic only; excluded from the reproducibility comparison.
DIAGNOSTIC_FILES = {"data/status.json"}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    dest.write_bytes(data)
    return len(data)


# ---------------------------------------------------------------------------
# README for the generated app
# ---------------------------------------------------------------------------

README = """# mdkg v0.1 — visualization application

Interactive, **fully offline** explorer for the mdkg v0.1 mechanical-design
knowledge graph.

## Launch

`fetch()` is blocked on `file://`, so the app must be served over HTTP. From the
**repository root**:

```bash
python3 -m http.server 8000
```

then open:

```
http://localhost:8000/outputs/visualizations/
```

Stop the server with Ctrl-C. No internet connection is required at any point —
Cytoscape.js is vendored locally under `assets/vendor/`, and there is no CDN
link, web font, tracker or external API anywhere in the application.

## Rebuild

```bash
python3 scripts/build_html_visualization.py              # regenerate everything
python3 scripts/build_html_visualization.py --clean      # wipe outputs first
python3 scripts/build_html_visualization.py --validate   # also run SHACL + unit tests
python3 scripts/build_html_visualization.py --check-reproducible
```

The build is idempotent: unchanged inputs produce byte-identical files. The one
exception is `data/status.json`, a diagnostic artefact written only by
`--validate`, which is excluded from the reproducibility comparison.

## Views

| View | What it answers |
|---|---|
| Overview | Counts, validation status, source documents, review states |
| Core ontology | Level-1 general design concepts, classes and properties |
| Mechanical design | Level-2 extension with the Function–Behavior–Structure wiring |
| Machine elements | Family taxonomy; element classes versus design alternatives |
| Function → alternative | "What can perform this function?", with evidence per alternative |
| Substitution | Directional, context-bound verdicts; side-by-side comparison |
| Claims | Filterable claim table with full provenance per claim |
| Evidence | Verified spans, assembled citations, text-integrity warnings |
| Cross-book | Mott/Shigley alignments, including the featured disagreements |
| Rules | Selection, substitution and verification rules with attribution |
| Coverage | Topic-by-book coverage matrix and pilot status |
| Evidence pipeline | How a page becomes a citable claim, and what stops fabrication |

## Reading the interface

**Epistemic badges appear throughout and are never decorative:**

| Badge | Meaning |
|---|---|
| ▣ Source-derived | The cited book states this |
| ≈ Normalized interpretation | Analyst mapped the book's wording onto a controlled scale |
| ✎ Engineering inference | Analyst reasoning beyond what any source states — *not quotable as textbook content* |
| ◈ Ontology engineering | Structure authored for the ontology, not derived from a book |
| ⌛ NeedsReview | Not signed off by a human engineer |
| ? Insufficient evidence | The sources do not settle the question |
| ⚖ …required | An external standard, manufacturer datum, protocol or review is needed |
| ⚠ Glyph-mismapped | The PDF text layer is wrong here; the excerpt must not be quoted |

**Graphs** encode category by *shape and glyph* as well as colour, so nothing
depends on colour alone. Individuals carry a double border; element classes a
single one; bridge nodes a dashed one. Every graph view has a legend, a node
limit with an explicit warning when it narrows the view, focus/neighbourhood
controls, PNG export and JSON export of exactly what is on screen.

**Keyboard:** `/` focuses the search box, `Esc` closes the search list and the
detail panel, `Tab` reaches every control.

## Data integrity

The application is a *projection* of the repository's existing data. It:

- adds no relationship that is not a triple or an explicit curated field;
- never mirrors a substitution edge and never composes a transitive one;
- never invents a threshold, a test procedure or an acceptance criterion;
- builds citations with the project's own `assemble_citation` logic rather than
  composing strings;
- shows "Not stated by the source", "Insufficient evidence", "Requires external
  authority" or "Requires human review" instead of an empty value.

## Files

```
index.html                 application shell
assets/app.css             styling
assets/app.js              application logic
assets/vendor/             Cytoscape.js 3.30.2 (MIT), pinned by SHA-256
data/*.json                generated datasets (see build_manifest.json)
```

All of `outputs/visualizations/` is generated. Edit the sources instead:
`scripts/viz_templates/` for the interface, `scripts/build_visualization_data.py`
for the datasets.
"""


# ---------------------------------------------------------------------------
# Build steps
# ---------------------------------------------------------------------------


def build_app(config: Dict[str, Any], out_dir: Path) -> Dict[str, Any]:
    """Generate datasets and copy the static assets. Returns a manifest."""
    data_dir = out_dir / "data"
    LOG.info("generating datasets")
    datasets = bvd.build_all(config)
    written = bvd.write_datasets(datasets, data_dir)

    LOG.info("copying templates")
    assets: Dict[str, int] = {}
    for name, rel in TEMPLATES.items():
        src = TEMPLATE_DIR / name
        if not src.exists():
            raise SystemExit(f"missing template: {src}")
        assets[rel] = copy_file(src, out_dir / rel)

    LOG.info("copying vendored libraries")
    for rel_src, rel_dest in VENDOR_FILES.items():
        src = VENDOR_DIR / rel_src
        if not src.exists():
            raise SystemExit(
                f"missing vendored file: {src}\n"
                "See vendor/README.md for the re-vendoring snippet."
            )
        assets[rel_dest] = copy_file(src, out_dir / rel_dest)

    (out_dir / "README.md").write_text(README, encoding="utf-8")
    assets["README.md"] = len(README.encode("utf-8"))

    # status.json always exists so the app never issues a request that 404s.
    # --validate overwrites it with real results; it is the one diagnostic file
    # and is excluded from the reproducibility comparison.
    status_path = out_dir / "data" / "status.json"
    if not status_path.exists():
        status_path.write_text(
            json.dumps({
                "validation": None,
                "unit_tests": None,
                "note": "Run scripts/build_html_visualization.py --validate to populate this file.",
            }, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    # Deterministic manifest: input digests, output digests, dataset shapes.
    inputs = {}
    for rel in ("build/mdkg-full.ttl", "data/claims.jsonl", "data/evidence_spans.jsonl",
                "data/substitutions.yaml", "data/alignments_seed.yaml",
                "data/terminology_alignment.csv", "data/coverage_matrix.csv",
                "outputs/ontology_summary.json", "rules/selection_rules.yaml",
                "rules/substitution_rules.yaml", "rules/verification_rules.yaml"):
        path = REPO_ROOT / rel
        if path.exists():
            inputs[rel] = sha256_of(path)

    graphs = {
        name: {
            "nodes": datasets[name]["meta"]["node_count"],
            "edges": datasets[name]["meta"]["edge_count"],
            "isolated_nodes": datasets[name]["meta"]["isolated_node_count"],
            "dropped_dangling_edges": datasets[name]["meta"]["dropped_dangling_edges"],
        }
        for name in bvd.DATASET_FILES if isinstance(datasets[name], dict) and "meta" in datasets[name]
    }

    manifest = {
        "application": "mdkg v0.1 visualization",
        "ontology_version": config["project"]["version"],
        "datasets": written,
        "assets": assets,
        "graphs": graphs,
        "search_entities": datasets["search_index"]["count"],
        "counts": {
            "claims": len(datasets["claims_graph"]["claims"]),
            "evidence_spans": len(datasets["evidence_graph"]["spans"]),
            "substitution_assessments": len(datasets["substitutions_graph"]["assessments"]),
            "claim_alignments": len(datasets["alignments_graph"]["alignments"]),
            "terminology_alignments": len(datasets["alignments_graph"]["terminology"]),
            "rules": len(datasets["rules"]["rules"]),
            "coverage_topics": len(datasets["coverage"]["rows"]),
            "functions": len(datasets["function_behavior_graph"]["functions"]),
        },
        "input_digests": inputs,
        "vendored": json.loads((VENDOR_DIR / "cytoscape" / "vendor.json").read_text(encoding="utf-8")),
        "runtime_dependencies": "local only — no CDN, no external API",
    }
    (out_dir / "data" / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def run_validation(out_dir: Path) -> Dict[str, Any]:
    """Run SHACL validation and the unit-test suite; write the diagnostic status."""
    status: Dict[str, Any] = {}

    LOG.info("running scripts/validate_ontology.py")
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_ontology.py")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    report_path = REPO_ROOT / "outputs" / "validation_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        status["validation"] = report["summary"]
    status["validation_exit_code"] = proc.returncode

    LOG.info("running the unit-test suite")
    test = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    tail = (test.stderr or "").strip().splitlines()
    ran, failures, errors, skipped = 0, 0, 0, 0
    for line in tail:
        if line.startswith("Ran "):
            try: ran = int(line.split()[1])
            except (IndexError, ValueError): pass
        if line.startswith("FAILED"):
            body = line[line.find("(") + 1: line.rfind(")")] if "(" in line else ""
            for part in body.split(","):
                part = part.strip()
                if part.startswith("failures="): failures = int(part.split("=")[1])
                if part.startswith("errors="): errors = int(part.split("=")[1])
                if part.startswith("skipped="): skipped = int(part.split("=")[1])
    status["unit_tests"] = {
        "run": ran, "failures": failures, "errors": errors, "skipped": skipped,
        "exit_code": test.returncode,
    }
    (out_dir / "data" / "status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return status


def digest_tree(root: Path, exclude: Sequence[str] = ()) -> Dict[str, str]:
    """SHA-256 of every file under *root*, keyed by relative path."""
    out: Dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel in exclude:
            continue
        out[rel] = sha256_of(path)
    return out


def check_reproducible(config: Dict[str, Any]) -> bool:
    """Build twice into scratch directories and compare every generated file."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp) / "a", Path(tmp) / "b"
        LOG.info("reproducibility: first build")
        build_app(config, a)
        LOG.info("reproducibility: second build")
        build_app(config, b)
        da, db = digest_tree(a, DIAGNOSTIC_FILES), digest_tree(b, DIAGNOSTIC_FILES)
        if da == db:
            LOG.info("reproducibility: %d files byte-identical across both builds", len(da))
            return True
        only_a = sorted(set(da) - set(db))
        only_b = sorted(set(db) - set(da))
        differing = sorted(k for k in set(da) & set(db) if da[k] != db[k])
        LOG.error("reproducibility FAILED")
        for k in differing: LOG.error("  differs: %s", k)
        for k in only_a: LOG.error("  only in build A: %s", k)
        for k in only_b: LOG.error("  only in build B: %s", k)
        return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--clean", action="store_true",
                        help="remove the output directory before building")
    parser.add_argument("--validate", action="store_true",
                        help="also run SHACL validation and the unit tests")
    parser.add_argument("--open", dest="open_browser", action="store_true",
                        help="print and try to launch the local URL")
    parser.add_argument("--check-reproducible", action="store_true",
                        help="build twice and confirm byte-identical output")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    with args.config.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    if args.clean and args.out.exists():
        LOG.info("cleaning %s", args.out)
        shutil.rmtree(args.out)

    manifest = build_app(config, args.out)

    if args.validate:
        status = run_validation(args.out)
        manifest["status"] = status

    reproducible = None
    if args.check_reproducible:
        reproducible = check_reproducible(config)
        manifest["reproducible"] = reproducible

    url = "http://localhost:8000/outputs/visualizations/"
    print(json.dumps({
        "output_dir": str(args.out.relative_to(REPO_ROOT)),
        "datasets": manifest["datasets"],
        "assets": manifest["assets"],
        "graphs": manifest["graphs"],
        "counts": manifest["counts"],
        "search_entities": manifest["search_entities"],
        "reproducible": reproducible,
        "status": manifest.get("status"),
        "launch": ["python3 -m http.server 8000", url],
    }, indent=2, sort_keys=True))

    print(f"\nServe from the repository root:\n  python3 -m http.server 8000\nThen open:\n  {url}\n")
    if args.open_browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as exc:  # pragma: no cover - headless environments
            LOG.info("could not launch a browser (%s); open the URL manually", exc)

    if args.check_reproducible and not reproducible:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
