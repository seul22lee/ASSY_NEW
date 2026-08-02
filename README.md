# mdkg — a mechanical-design ontology with verifiable provenance

**Version 0.1.0**

A general, extensible ontology for mechanical design, and an evidence-grounded
knowledge graph built from two textbooks:

- Robert L. Mott et al., *Machine Elements in Mechanical Design*, 6th ed.
- Richard G. Budynas & J. Keith Nisbett, *Shigley's Mechanical Engineering
  Design*, 10th ed.

The ontology answers questions of the form *what can perform this function*,
*can this replace that*, *under what conditions*, *what could go wrong*, *what
must be checked*, and — for every answer — *which page says so*.

---

## What makes this different from a document index

**A citation cannot be fabricated here, because the build verifies it.**

An analyst writes only three things per piece of evidence: which document, which
PDF page index, and a short phrase read on that page. Everything citable —
printed page number, chapter, section, bounding box — is then *resolved from the
PDF and verified against it*. `scripts/build_evidence_spans.py` **fails** if the
phrase is not on the stated page. `scripts/validate_ontology.py` reopens both
PDFs on every run and re-checks all 91 spans. The claim seed file has no fields
for page or chapter, so they cannot be typed by hand. Citation strings are
assembled from stored fields at read time and are never stored.

A drifted citation breaks the build rather than lying.

### The other three disciplines

- **Substitution is context-dependent and directional.** `SA-001` (spline
  replaces key) concludes *preferred*; `SA-006` — same pair, same context,
  opposite direction — concludes *not an alternative*. Symmetric and transitive
  inference are prohibited and actively checked.
- **Unquantified terms stay unquantified.** Five threshold definitions exist
  ("low torque", "high speed", "heavy load", "low-cycle fatigue", "high
  torque"); **all five** are marked non-universal, because in every case the
  source used the term without fixing a boundary.
- **Text-layer quality is measured, not assumed.** The Shigley PDF mis-maps
  mathematics glyphs onto ASCII — `a = 10/3` extracts as `a 5 10y3`. Affected
  spans are flagged `glyph-mismapped` and never quoted; every equation in the
  graph was transcribed from a rendered page image and records that fact.

---

## Current contents

| | |
|---|---|
| TBox classes | 286 (115 core, 79 mechanical, 92 machine-element) |
| Object / datatype properties | 129 / 101 |
| SKOS concept schemes | 12 |
| Verified evidence spans | 91 (46 Mott, 45 Shigley) |
| Normalized claims | 82 (40 Mott, 42 Shigley) |
| Cited pages / chapters / sections | 25 / 6 / 16 |
| Cited equations, tables, figures, examples | 21 / 8 / 5 / 1 |
| Design alternatives | 22 |
| Substitution assessments | 6 (+3 recorded evidence gaps) |
| Cross-book claim / terminology alignments | 15 / 12 |
| Selection / substitution / verification rules | 8 / 9 / 7 |
| Total triples | 7,745 |
| Claims marked `HumanVerified` | **0** — by design; nothing has been signed off |

Validation: SHACL conforms; 13/13 custom checks pass; 57/57 tests pass.

---

## Architecture

```
Level 1  ontology/core/              general engineering design
                                     (nothing here mentions a shaft or a key)
Level 2  ontology/mechanical-design/ mechanical specialisation
Level 3  ontology/machine-elements/  element families, organised by function
Level 4  ontology/*-claims.ttl       claims, rules and evidence
         rules/, data/
```

Five separated layers:

| Layer | Holds | Formalism |
|---|---|---|
| **TBox** | Classes, properties, formal definitions | OWL |
| **Vocabularies** | Satisfaction levels, substitution states, review states, alignment types | SKOS |
| **ABox** | Book-derived claims and evidence | RDF instances |
| **Rules** | Selection, substitution, verification logic | YAML + Python |
| **Validation** | Structural constraints | SHACL |

A claim is **never** an axiom. `ontology/mott6-claims.ttl` holds
`ev:NormalizedClaim` individuals, not subclass assertions, so a claim can be
conditioned, contradicted, revised or rejected without touching the schema.

Full rationale: [`docs/ontology_design.md`](docs/ontology_design.md).

---

## Setup and execution

Python 3.8+.

```bash
python3 -m pip install --user pymupdf rdflib pyshacl pint pyyaml networkx pydantic
```

Place both PDFs in the repository root (paths are configured in
`config/config.yaml`), then run the pipeline in order:

```bash
python3 scripts/extract_pdf_structure.py    # PDFs → build/  (~45 s)
python3 scripts/build_evidence_spans.py     # seeds → data/evidence_spans.jsonl  [VERIFIES against PDFs]
python3 scripts/build_claims.py             # seeds + spans → data/claims.jsonl
python3 scripts/build_coverage_map.py       # outlines → coverage matrix + docs
python3 scripts/build_ontology.py           # everything → ontology/*.ttl, build/mdkg-full.ttl
python3 scripts/validate_ontology.py        # SHACL + 13 custom checks
python3 scripts/generate_maps.py            # → outputs/*.mmd
python3 -m unittest discover -s tests -v    # 57 tests
```

Every stage is idempotent. Then explore:

```bash
python3 scripts/query_examples.py                  # all ten competency queries
python3 scripts/query_examples.py --query 7        # evidence for a recommendation
python3 scripts/query_examples.py --query 6        # every substitution verdict
python3 scripts/query_examples.py --query 9        # where the books differ
python3 scripts/query_examples.py --query 1 --show-sparql
python3 scripts/query_examples.py --format json    # machine-readable
```

Sample output of query 7 — every field assembled from stored provenance:

```
CITATION: Machine Elements in Mechanical Design — 6th ed. — ch. 11 (Keys,
          Couplings, and Seals) — sec. 11-5 (Splines) — printed p. 480 —
          PDF page index 496 — Eq. 11-9; Eq. 11-10
          text integrity: reliable; bbox: 50.98,234.68,293.9,390.73
```

---

## Repository layout

```
config/config.yaml            PDF paths, namespaces, extraction/OCR settings, thresholds
ontology/
  core/                       [hand-authored] Level 1 TBox, 11 modules
  mechanical-design/          [hand-authored] Level 2, 7 modules
  machine-elements/           [hand-authored] Level 3-4, 4 modules
  core.ttl  evidence.ttl  mechanical-design.ttl  machine-elements.ttl   [generated bundles]
  mott6-claims.ttl  shigley10-claims.ttl  alignments.ttl                [generated from data/]
shapes/
  modules/                    [hand-authored] SHACL, 3 modules
  ontology-shapes.ttl         [generated bundle]
rules/                        [hand-authored] selection, substitution, verification YAML
data/
  evidence_seeds.yaml         [hand-authored] doc + page index + anchor phrase only
  claims_seed.yaml            [hand-authored] claim content; NO page fields by design
  alignments_seed.yaml  substitutions.yaml    [hand-authored]
  evidence_spans.jsonl  claims.jsonl          [generated, provenance resolved]
  terminology_alignment.csv  coverage_matrix.csv  [generated]
scripts/                      the 8-stage pipeline
tests/test_mdkg.py            57 tests incl. a SHACL negative control
build/                        [generated] intermediates, never hand-edited
outputs/                      [generated] Mermaid maps, summary and validation JSON
docs/                         design, extraction, coverage, cross-book, substitution, CQs
```

Every generated file carries a `GENERATED FILE — DO NOT EDIT BY HAND` banner
naming its inputs.

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/competency_questions.md`](docs/competency_questions.md) | 40 questions with honest status; 4 not yet answerable, with reasons |
| [`docs/ontology_design.md`](docs/ontology_design.md) | Layering, class census, TBox/ABox split, substitution semantics, formalism choices, known limitations |
| [`docs/source_coverage_map.md`](docs/source_coverage_map.md) | 32 topics × 2 books; 26 shared, 4 Mott-only, 2 Shigley-only |
| [`docs/extraction_report.md`](docs/extraction_report.md) | SHA-256s, OCR decision, page-label handling, the glyph mis-mapping finding |
| [`docs/cross_book_analysis.md`](docs/cross_book_analysis.md) | Agreements, complements, differences, and one hidden assumption that matters |
| [`docs/substitution_examples.md`](docs/substitution_examples.md) | Six worked assessments with full evidence |

Diagrams in `outputs/*.mmd` (Mermaid; paste into any Mermaid renderer):
core ontology, mechanical extension, machine-element families, evidence
pipeline, substitution model. All are generated from the built RDF, so they
cannot drift out of step with it.

---

## Interactive explorer

An offline HTML application over the same data, with twelve linked views —
ontology graphs, function→alternative search, directional substitution
comparison, a filterable claims table with full provenance, cross-book
alignments, rules, coverage and the evidence pipeline.

```bash
python3 scripts/build_html_visualization.py     # build
python3 -m http.server 8000                     # serve, from the repository root
# open http://localhost:8000/outputs/visualizations/
```

No internet connection is needed to view it: Cytoscape.js is vendored under
`vendor/` and pinned by SHA-256, and the page makes no external request. The
application is a *projection* of the data in this repository — it adds no
relationship, mirrors no substitution edge and composes no citation string.
See [`outputs/visualizations/README.md`](outputs/visualizations/README.md).

---

## Limitations

Stated plainly:

1. **No claim is human-verified.** All 82 sit at `NeedsReview`. Nothing here
   should yet be treated as a validated design fact.
2. **This is a pilot.** 91 spans over ~1,978 pages, concentrated on five topics.
   Coverage was traded for citation integrity.
3. **The rule layer is declarative, not executed.** `rules/*.yaml` is validated
   and machine-readable, but no engine evaluates it against a design problem
   yet. `SEL-005` is marked `executable: false` because it depends on a
   threshold no source supplies.
4. **Table contents and equations are not machine-parsed.** Tables are cited by
   number, not reproduced. Equation expressions are analyst transcriptions from
   rendered page images.
5. **One function dominates.** 16 of 22 alternatives serve
   `TransmitTorqueShaftToHub`. Gears, springs, seals and flexible drives are
   taxonomy only.
6. **Claims attach to element *types*, substitution to *alternatives*.** Query
   10 therefore over-reports four alternatives as unsupported. A bridging
   property is v0.2 work.
7. **No design decisions.** `DesignDecision` is modelled but unused.

---

## Adding another textbook

No schema change is required.

1. **Register it** in `config/config.yaml` under `sources:` — file name, title,
   authors, edition, namespace prefix, and the `math_fonts` list used for the
   text-integrity metric. Set `math_text_reliability` after inspecting a
   mathematics-heavy page.
2. **Add its namespace** to `namespaces:` in the config and to `SOURCE_NS` in
   `scripts/build_ontology.py`.
3. **Extract:** `python3 scripts/extract_pdf_structure.py --only <doc_id>`.
   Check the resulting `build/<doc_id>.meta.json` for page-label availability
   and the math-heavy page percentage.
4. **Seed evidence** in `data/evidence_seeds.yaml`: document, PDF page index,
   anchor phrase, topic. Run `build_evidence_spans.py`; it will reject any
   anchor that is not on the stated page.
5. **Seed claims** in `data/claims_seed.yaml`, citing those span ids. Do not
   supply page or chapter fields — they are resolved.
6. **Extend the coverage map:** add a `TOPIC_MAP` entry in
   `scripts/build_coverage_map.py`.
7. **Align:** add `concept_alignments` and `claim_alignments` in
   `data/alignments_seed.yaml`. Use `Complements` and `DiffersInScope` freely;
   reserve `Contradicts` for genuine factual conflict.
8. **Rebuild and validate.**

Rule of thumb: if a third source's content requires a *new class*, it is
probably a new domain module (step 2 below), not a new source.

## Adding a machine-element module

1. **Create** `ontology/machine-elements/<family>.ttl`. A family gets its own
   file once it has alternatives with evaluations, or more than ~20 classes;
   below that, extend `other-families.ttl`.
2. **Add the functions** it delivers to
   `ontology/mechanical-design/mechanical-function.ttl` as `mdcore:Function`
   individuals in `mech:MechanicalFunctionScheme`. Name them as solution-neutral
   verb phrases — if a function can only be stated by naming one solution, it is
   a requirement or an alternative in disguise.
3. **Add the behaviors** that realise those functions, with
   `mdcore:reliesOnEffect` and any `mdcore:behaviorRequiresCondition`. This is
   the step that pays off later: alternatives sharing a behavior share a failure
   family.
4. **Add element types** as `owl:Class , owl:NamedIndividual` (punned), under a
   family in `families.ttl`.
5. **Add design alternatives** as `mdcore:DesignAlternative` individuals with
   `melem:usesElementType`, `mdcore:performsFunction` and
   `mdcore:enablesBehavior`. **Assert structure only** — capacities, advantages
   and limits are claims, not TBox.
6. **Add failure modes and verification methods** in
   `ontology/mechanical-design/mechanical-failure.ttl`.
7. **Add claims** with evidence, then rules, then substitution assessments.
8. **Rebuild, validate, run the tests.** The maps regenerate themselves.

---

## Provenance and safety statement

- No page number, quotation, equation number, table number, figure number,
  standard, threshold or test procedure in this repository was written from
  memory. Each is either verified against the source PDF at build time, or
  explicitly marked as absent.
- Where a source recommends a test without defining one, the graph records
  `testRecommended: true` with `testProcedureSpecified: false` and
  `acceptanceCriterionSpecified: false`, and names the external authority
  required to close the gap.
- General mechanical-engineering knowledge was used to *propose ontology
  structure*. It is labelled as ontology engineering throughout and never
  presented as source-derived. Analyst reasoning that goes beyond the cited
  sources carries `mdcore:valueProvenance = EngineeringInference`.
- Quotations are short. The evidence store exists to make citations verifiable,
  not to reproduce the books.
