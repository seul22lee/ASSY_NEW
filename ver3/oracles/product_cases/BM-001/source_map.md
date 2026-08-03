# BM-001 — source map

> **Pack status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; not lock-ready, not
> CAD-validated. Every admissible fixture is `NEEDS_GEOMETRY_VALIDATION`.


Every normative, unresolved, negative and evidence statement traces to an exact
path. Ranks follow `ORACLE_METHOD.md` §3.

Legacy roots: `V1 = /home/ftk3187/github/ASSY_Ver1.0`,
`V2 = /home/ftk3187/github/ASSY_Ver2.0`.

## Rank 1 — explicit product intent and benchmark requirements

| Source id | Path | Key | Used by |
|---|---|---|---|
| SRC-BM-001-SPEC | `V2/BM-001_LATCHING_STORAGE_BOX.md` | whole document | pack intent |
| SRC-BM-001-REQ-001 | `V2/tests/fixtures/BM-001_requirementspec.json` | `requirements[REQ-001]` — "mechanism for repeatedly opening and closing" | NRM-BM-001-001, 002, 003, 004, 005, 009 |
| SRC-BM-001-REQ-002 | same | `REQ-002` — "remain securely closed during normal handling and transport" | NRM-BM-001-006, 011; UNR-BM-001-001 |
| SRC-BM-001-REQ-003 | same | `REQ-003` — "latch that is easy for a user to operate" | NRM-BM-001-008; UNR-BM-001-002 |
| SRC-BM-001-REQ-004 | same | `REQ-004` — "maintain secure closure during transport" | NRM-BM-001-006; UNR-BM-001-001 |
| SRC-BM-001-REQ-005 | same | `REQ-005` — "suitable for low-cost manufacturing" | UNR-BM-001-004; NV-BM-001-003 |
| SRC-BM-001-REQ-006 | same | `REQ-006` — "practical for desktop use" | NRM-BM-001-009; NV-BM-001-004 |
| SRC-BM-001-REQ-007 | same | `REQ-007` — "mechanically plausible and easy to assemble" | NRM-BM-001-010, 011 |
| SRC-BM-001-REQ-008 | same | `REQ-008` — "reusable latch mechanism" | NRM-BM-001-006, 007 |
| SRC-BM-001-C-006 | same | `clauses[C-006]` — "desktop-sized (roughly hand-held)" | UNR-BM-001-003 |

## Rank 2 — explicit engineering review findings

| Source id | Path | Finding | Used by |
|---|---|---|---|
| SRC-V2-RL-0005 | `V2/research_log/RL-0005.md` | Stage 04 visualization and visual review | NEG-BM-001-011 |
| SRC-V2-RL-0006 | `V2/research_log/RL-0006.md` | Spatial contract repair | NEG-BM-001-005 |
| SRC-V2-RL-0009 | `V2/research_log/RL-0009.md` | Spatial-first, semantics-on-top | NEG-BM-001-004 |
| SRC-V2-RL-0010 | `V2/research_log/RL-0010.md` | Topological anchors — what a feature is attached to | NEG-BM-001-006 |
| SRC-V2-RL-0011 | `V2/research_log/RL-0011.md` | Derived placement — why a feature is where it is | NEG-BM-001-007, NEG-BM-001-008 |
| SRC-V2-RL-0012 | `V2/research_log/RL-0012.md` | Observability of motion is a property of the model, not the drawing | NRM-BM-001-002; NEG-BM-001-002, NEG-BM-001-011 |
| SRC-V2-RL-0013 | `V2/research_log/RL-0013.md` | Ranking measured how well a family was described | NEG-BM-001-009 |
| SRC-V2-ERRTAX | `V2/docs/ERROR_TAXONOMY.md` | Error taxonomy | NEG-BM-001-010 |
| SRC-V2-S06-DEFAULT-UNIT | `V2/assy/stages/s06_solver.py:51` — `unit=c.unit or "mm"` | Silent default unit | `stage_expectations.yaml` s06 `must_not_be_decided: [default_units]` |
| SRC-V1-KG-NOREALIZER | `V1/tasks/benchmark/benchmark.py:145-150` — `KG_NO_PERMITTED_REALIZER` | Missing knowledge reported as INFEASIBLE | NEG-BM-001-012 |

## Rank 3-4 — verified evidence and reference realizations

| Source id | Path | Fidelity | Used by |
|---|---|---|---|
| SRC-V1-M0-HINGE | `V1/m0/out/stop/` | V-A / V-B ring | EV-BM-001-001; NEG-BM-001-003 |
| SRC-V1-M0-NOSTOP | `V1/m0/out/nostop/` | V-A / V-B ring | EV-BM-001-001; NEG-BM-001-001 |
| SRC-V1-SNAP | `V1/m23_latch_physics/`, `V1/tasks/snap_panel.json` | V-B contact + tier-1 analytic | EV-BM-001-002 |

## Rank 5 — historical examples only, never assertion targets

| Path | Note |
|---|---|
| `V2/BM-001_GOLDEN_STAGE_OUTPUTS.md` | Ver2 golden stage outputs. Read for shape only; no `must_exist` entry derives from it (ORACLE_METHOD §3.3). |
| `V2/out/BM-001/run-*/` | 78 recorded runs. Historical. |

## Freedoms and their grounding

Every freedom is grounded in DOS-BM-001 S3 — a decision the source does not make —
or in S6, a decision made only by a legacy reference realization, which is a
freedom in Ver3 precisely because no requirement makes it.

| Freedom | Grounded in | Legacy value it refuses to inherit |
|---|---|---|
| FRE-BM-001-001 closure-connection family | S3 | pin hinge with ring-meshed knuckles (S6) |
| FRE-BM-001-002 retention family | S3, S7 | cantilever snap hook (S6); the corpus realizes retention only by snaps |
| FRE-BM-001-003 aperture region and connection location | S3 | prismatic box with a lid on one face (S6) |
| FRE-BM-001-004 motion type of the closure | S3 | rotary about a pin axis (S6) |
| FRE-BM-001-005 part count and decomposition | S3 | the legacy body count |
| FRE-BM-001-006 boundary form and cross-section | S3 | prismatic box (S6) |
| FRE-BM-001-007 dimensions, tolerances, clearances | S3 | bore 2.150 / pin 2.000, min wall 2.192 mm (S6) |
| FRE-BM-001-008 material and process | S3 | — |
| FRE-BM-001-009 what determines the open pose | S3, S7 | discrete stop flange; 90 deg target (S6) |
| FRE-BM-001-010 retention engagement sites | S3 | — |
| FRE-BM-001-011 whether the closure stays connected when open | S3 | every legacy realization kept it connected; no requirement does |

## Requirement coverage

| Requirement | Where it lands |
|---|---|
| REQ-001 | NRM-BM-001-001, NRM-BM-001-002, NRM-BM-001-003, NRM-BM-001-004, NRM-BM-001-005, NRM-BM-001-009 |
| REQ-002 | NRM-BM-001-006, NRM-BM-001-011; UNR-BM-001-001 |
| REQ-003 | NRM-BM-001-008; UNR-BM-001-002 |
| REQ-004 | NRM-BM-001-006; UNR-BM-001-001 |
| REQ-005 | UNR-BM-001-004; not_verified |
| REQ-006 | NRM-BM-001-009; UNR-BM-001-003; not_verified |
| REQ-007 | NRM-BM-001-010, NRM-BM-001-011; UNR-BM-001-005 |
| REQ-008 | NRM-BM-001-006, NRM-BM-001-007 |

UNR-BM-001-005 (whether the closure connection and the retention share a body or
an axis) is grounded in DOS-BM-001 S2: no source relates them. It is held open
rather than answered, because every legacy realization answered it the same way
and none of them was required to.

Every requirement is carried by an invariant, carried as an unresolved decision,
or recorded as not verified with the reason. None is dropped.

## Deliberately excluded

`BM-101` and Geneva material: excluded by instruction; located during Phase 0
and not read for design content.

## Legacy conflicts recorded, not reconciled

None identified for BM-001 itself. See `C4-drawer/source_map.md` for the one
conflict found in the family.

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-2.1 | `NRM-BM-001-003` no longer requires the closure to vacate the aperture prism. It requires the DECLARED usable access region to be unobstructed. Adequacy of that region is held at the new `UNR-BM-001-006`. |
| SF-2.2 | `NRM-BM-001-005` is conditional: a discrete terminal open pose must be physically produced, but a design may instead declare an open configuration region. DOS-BM-001 S2 records that no source bounds the motion at the open extreme. New freedom `FRE-BM-001-012`. |
| SF-2.3 | `UNR-BM-001-001` and `UNR-BM-001-002` are quantitative and no longer block `NRM-BM-001-011` and `NRM-BM-001-008`. `NRM-BM-001-011` is load-conditional. |
| SF-2.4 | `NRM-BM-001-007` requires a realizable engage/release/engage cycle rather than a declaration of repeatability. Cycle count is held at the new `UNR-BM-001-007`. |
| SF-1.1 | Two VERIFICATION_MINIMUM statements added — `NRM-BM-001-012` (the m0 pair does not discriminate) and `NRM-BM-001-013` (the snap force window is an input). Both were prose in `evidence_scope.yaml`; both are now falsifiable and carry `enables_claim`. Their fixtures live in `evidence_cases.yaml`. |
| SF-1.4 | New unresolved `UNR-BM-001-006` (access region), `UNR-BM-001-007` (cycle count), `UNR-BM-001-008` (a discriminating criterion). All carry explicit block scopes. |
