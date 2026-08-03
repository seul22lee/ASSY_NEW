# Dossier latch-retention — FROZEN (micro-oracle)

**Tier:** micro_oracle. Constrains **one reusable mechanical capability**, never a
product and never a mechanism. Legacy fixtures below are cited as evidence and as
sources of negative cases; they are **not** acceptance targets.

## S1. Capability
Holding two bodies in a defined relative state against a disturbance, and
releasing them by a deliberate action, repeatably.

## S2. Legacy fixtures (rank 4-5 evidence, not targets)
| Fixture | Path | What its source says |
|---|---|---|
| Snap panel | `/home/ftk3187/github/ASSY_Ver1.0/tasks/snap_panel.json` | command: "A clip that retains a flat board and can be removed by hand." functions: secure board (retain a flat part); allow_access board (removable by hand). |
| Latch physics | `/home/ftk3187/github/ASSY_Ver1.0/m23_latch_physics/` | tier-1 analytic + contact |
| Latched drawer retention | `/home/ftk3187/github/ASSY_Ver1.0/tasks/latched_drawer.json` | B2 static snap_event, realized_by E2, verified_by PR-LATCH |
| Snap starter | `/home/ftk3187/github/ASSY_Ver1.0/tasks/snap_starter.json`, `/home/ftk3187/github/ASSY_Ver1.0/SNAPFIT_STARTER_v0.md` | — |

## S3. Explicit observables
- `snap_panel.json` B1 assembly `snap_event`, `event_force_window_N = [0.0, 80.0]`, verified_by `PR-T1-MATE`.
- `snap_panel.json` B2 static `snap_event`, `event_force_window_N = [15.0, 60.0]`, verified_by `PR-T1-SEP`.
- `latched_drawer.json` B2 static `snap_event`, `event_force_window_N = [15.0, 60.0]`, verified_by `PR-LATCH`.

## S4. Missing criteria
No capability-level retention load, release effort ceiling, cycle count,
creep/temperature condition or degradation limit exists in any source.

## S5. Evidence fidelity and limitations
**The force windows above are INPUT PARAMETERS of the task definitions, not
measured product properties.** Citing `[15.0, 60.0] N` as an achieved retention
result is circular. `m23_latch_physics` supplies tier-1 analytic and contact
work for one snap geometry family only.

## S6. Decisions made only by legacy realizations
Cantilever snap hook geometry (`/home/ftk3187/github/ASSY_Ver1.0/knowledge/cards/snap_hook.py`,
`snap_hook_geometry.py`); beam length/thickness bounds; a lip on the mating part.

## S7. Legacy behaviour that must not define correctness
The corpus realizes retention exclusively by snap features. Magnetic,
over-centre, detent, friction and threaded retention are absent from the library
but not from engineering.
