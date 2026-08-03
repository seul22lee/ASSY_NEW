# BM-001 — source map

Every normative, unresolved, negative and evidence statement traces to an exact
path. Ranks follow `ORACLE_METHOD.md` §3.

Legacy roots: `V1 = /home/ftk3187/github/ASSY_Ver1.0`,
`V2 = /home/ftk3187/github/ASSY_Ver2.0`.

## Rank 1 — explicit product intent and benchmark requirements

| Source id | Path | Key | Used by |
|---|---|---|---|
| SRC-BM-001-SPEC | `V2/BM-001_LATCHING_STORAGE_BOX.md` | whole document | pack intent |
| SRC-BM-001-REQ-001 | `V2/tests/fixtures/BM-001_requirementspec.json` | `requirements[REQ-001]` — "mechanism for repeatedly opening and closing" | NRM-001, 002, 003, 004, 005, 009 |
| SRC-BM-001-REQ-002 | same | `REQ-002` — "remain securely closed during normal handling and transport" | NRM-006, 011; UNR-001 |
| SRC-BM-001-REQ-003 | same | `REQ-003` — "latch that is easy for a user to operate" | NRM-008; UNR-002 |
| SRC-BM-001-REQ-004 | same | `REQ-004` — "maintain secure closure during transport" | NRM-006; UNR-001 |
| SRC-BM-001-REQ-005 | same | `REQ-005` — "suitable for low-cost manufacturing" | UNR-004; NV-003 |
| SRC-BM-001-REQ-006 | same | `REQ-006` — "practical for desktop use" | NRM-009; NV-004 |
| SRC-BM-001-REQ-007 | same | `REQ-007` — "mechanically plausible and easy to assemble" | NRM-010, 011 |
| SRC-BM-001-REQ-008 | same | `REQ-008` — "reusable latch mechanism" | NRM-006, 007 |
| SRC-BM-001-C-006 | same | `clauses[C-006]` — "desktop-sized (roughly hand-held)" | UNR-003 |

## Rank 2 — explicit engineering review findings

| Source id | Path | Finding | Used by |
|---|---|---|---|
| SRC-V2-RL-0005 | `V2/research_log/RL-0005.md` | Stage 04 visualization and visual review | NEG-011 |
| SRC-V2-RL-0006 | `V2/research_log/RL-0006.md` | Spatial contract repair | NEG-005 |
| SRC-V2-RL-0009 | `V2/research_log/RL-0009.md` | Spatial-first, semantics-on-top | NEG-004 |
| SRC-V2-RL-0010 | `V2/research_log/RL-0010.md` | Topological anchors — what a feature is attached to | NEG-006 |
| SRC-V2-RL-0011 | `V2/research_log/RL-0011.md` | Derived placement — why a feature is where it is | NEG-007, NEG-008 |
| SRC-V2-RL-0012 | `V2/research_log/RL-0012.md` | Observability of motion is a property of the model, not the drawing | NRM-002; NEG-002, NEG-011 |
| SRC-V2-RL-0013 | `V2/research_log/RL-0013.md` | Ranking measured how well a family was described | NEG-009 |
| SRC-V2-ERRTAX | `V2/docs/ERROR_TAXONOMY.md` | Error taxonomy | NEG-010 |
| SRC-V2-S06-DEFAULT-UNIT | `V2/assy/stages/s06_solver.py:51` — `unit=c.unit or "mm"` | Silent default unit | NRM-012 |
| SRC-V1-KG-NOREALIZER | `V1/tasks/benchmark/benchmark.py:145-150` — `KG_NO_PERMITTED_REALIZER` | Missing knowledge reported as INFEASIBLE | NEG-012 |

## Rank 3-4 — verified evidence and reference realizations

| Source id | Path | Fidelity | Used by |
|---|---|---|---|
| SRC-V1-M0-HINGE | `V1/m0/out/stop/` | V-A / V-B ring | EV-001; NEG-003 |
| SRC-V1-M0-NOSTOP | `V1/m0/out/nostop/` | V-A / V-B ring | EV-001; NEG-001 |
| SRC-V1-SNAP | `V1/m23_latch_physics/`, `V1/tasks/snap_panel.json` | V-B contact + tier-1 analytic | EV-002 |

## Rank 5 — historical examples only, never assertion targets

| Path | Note |
|---|---|
| `V2/BM-001_GOLDEN_STAGE_OUTPUTS.md` | Ver2 golden stage outputs. Read for shape only; no `must_exist` entry derives from it (ORACLE_METHOD §3.3). |
| `V2/out/BM-001/run-*/` | 78 recorded runs. Historical. |

## Deliberately excluded

`BM-101` and Geneva material: excluded by instruction; located during Phase 0
and not read for design content.

## Legacy conflicts recorded, not reconciled

None identified for BM-001 itself. See `C4-drawer/source_map.md` for the one
conflict found in the family.
