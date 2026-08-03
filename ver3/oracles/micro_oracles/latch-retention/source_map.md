# latch-retention — source map (micro-oracle)

**Capability (rank 1 for this pack):** holding two bodies in a defined relative
state against a disturbance, and releasing them by a deliberate action,
repeatably. Source: `ver3/oracles/_dossiers/DOS-latch-retention.md` S1.

A micro-oracle has no user request. Its rank-1 source is the declared capability
statement; product cases and legacy fixtures rank below it and never define it.

## Statements

| Statement | basis_type | Grounded in |
|---|---|---|
| NRM-LR-001 | DIRECT_USER_REQUIREMENT | S1, "a defined relative state" |
| NRM-LR-002 | DIRECT_USER_REQUIREMENT | S1, "holding … against a disturbance" |
| NRM-LR-003 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (holding means carrying the load) |
| NRM-LR-004 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (holds against X, releases by Y ⇒ X ≠ Y) |
| NRM-LR-005 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived |
| NRM-LR-006 | DIRECT_USER_REQUIREMENT | S1, "repeatably" |
| NRM-LR-007 | VERIFICATION_MINIMUM | S1 + S4 (no capability-level disturbance) |
| NRM-LR-008 | VERIFICATION_MINIMUM | S3 + S5 (force windows are inputs) |

NRM-LR-004 is the load-bearing statement of this pack. It follows from the
capability statement alone: a retention that holds against a disturbance and
releases by a deliberate action must be able to tell them apart, or it does not
hold. It names no mechanism, and it admits any discriminant.

## Boundaries with neighbouring capabilities

| Question | Owner |
|---|---|
| How do the bodies reach the vicinity of the retained state? | guided-slider |
| Where does the motion stop? | bounded-two-state-closure |
| What drives the motion? | rotary-to-linear-engagement, among others |

## Legacy material and its rank

| Item | Rank | Disposition |
|---|---|---|
| `snap_panel.json` command "removable by hand" (S2) | 4 | One fixture's requirement. FRE-LR-005, UNR-LR-003, NEG-LR-011. |
| `event_force_window_N = [0.0, 80.0]` and `[15.0, 60.0]` (S3) | 4 | **Input parameters**, not measurements. EV-LR-001/002/003, NRM-LR-008. |
| Cantilever snap-hook geometry, beam bounds, mating lip (S6) | 4 | FRE-LR-002, FRE-LR-006, NEG-LR-009. |
| `m23_latch_physics` tier-1 analytic and contact (S2, S5) | 4 | EV-LR-004, bounded to one snap geometry family. NEG-LR-013. |
| Retention realized exclusively by snaps (S7) | 6 | A library state. The catalogue-as-design-space failure if treated otherwise. |

## The circularity finding

DOS S5 states it plainly: the force windows are inputs of the task definitions,
not measured product properties. The same window `[15.0, 60.0]` appears in two
different tasks, which is a fact about how the tasks were authored and about
nothing else. `NRM-LR-008` forbids reporting such a value as a result;
`stage_expectations.s08.provenance_of_values_note` and `s10.circularity_rule`
place the obligation on specific stages so the check is mechanical rather than
editorial.
