# Dossier guided-slider — FROZEN (micro-oracle)

**Tier:** micro_oracle. Constrains **one reusable mechanical capability**, never a
product and never a mechanism. Legacy fixtures below are cited as evidence and as
sources of negative cases; they are **not** acceptance targets.

## S1. Capability
Guided translation of one body relative to another along a defined line, with
the non-translational freedoms removed.

## S2. Legacy fixtures (rank 4-5 evidence, not targets)
| Fixture | Path | What its source says |
|---|---|---|
| Latched drawer | `/home/ftk3187/github/ASSY_Ver1.0/tasks/latched_drawer.json` | command: "A drawer that slides in, clicks shut, and pulls open by hand." functions: guide drawer (slide in/out); retain drawer (click shut, hand-releasable). B1 translation, `axis_hint horizontal`, `range_value 50.0 mm`, `bound min`, realized_by E1, verified_by `P-SLIDE-VA-E1`. B3 assembly translation imposed_by E1 (`imposed_by_card slide_rail`). |
| Slide fixture | `/home/ftk3187/github/ASSY_Ver1.0/tasks/slide_fixture.json` | minimal slide task |
| Slide milestone | `/home/ftk3187/github/ASSY_Ver1.0/m10_slide_rail/` | card + verification |
| Composition | `/home/ftk3187/github/ASSY_Ver1.0/m22_composition/`, `/home/ftk3187/github/ASSY_Ver1.0/m25_contact_layer/` | latched_drawer composed and contact-layered |

## S3. Explicit observables in the sources
- `P-SLIDE-VA`: `reaches_stroke` (mm), `tracks_straight (<=3 deg)`, `converged`.
  Source: `/home/ftk3187/github/ASSY_Ver1.0/m13_hard_anchor/out/t2_hard_verdict.json`.
- latched_drawer B1: `range_value 50.0 mm`, `bound min`.

## S4. Missing criteria
No general stroke, load, friction, duty, alignment tolerance or life is defined
by any capability-level source. All numbers above belong to specific fixtures.

## S5. Evidence fidelity and limitations
- `P-SLIDE-VA` is **V-A declared pairs**. `tracks_straight` measured **0.0 deg
  exactly** — a **structural artifact** of a declared prismatic joint, not
  evidence of guidance quality.
- `/home/ftk3187/github/ASSY_Ver1.0/m25_contact_layer/out/t2_contact_latched_drawer_verdict.json` exists as a
  contact-layer artifact for the drawer.

## S6. Decisions made only by legacy realizations
Two rails at a fixed gap; a carriage per rail; `slide_rail.carve` REPLACES its
mover piece so a rail cannot also be the drawer (`build_goldens.py:1142`
composition note). Rail width 8.0, height 8.0, clearance 0.35.

## S7. Legacy behaviour that must not define correctness
Anti-rotation was realized in the fixtures by *using two rails*, i.e. by the
chosen mechanism. Whether anti-rotation is required at all is a capability
question, not a rail question.
