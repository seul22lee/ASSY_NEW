# mdkg v0.1 — visualization application

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
