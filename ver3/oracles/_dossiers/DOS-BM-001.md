# Dossier BM-001 — FROZEN

## S1. Direct source requirements (rank 1)
Locator: `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001_requirementspec.json`, key `requirements[<id>]`.
Product doc: `/home/ftk3187/github/ASSY_Ver2.0/BM-001_LATCHING_STORAGE_BOX.md`.
`product_intent`: "A compact desktop storage box with a reusable latch mechanism that enables repeated opening and closing operations while maintaining security during transport and normal handling."

| ID | kind | statement (verbatim) | verification.kind | observable (verbatim) |
|---|---|---|---|---|
| REQ-001 | functional | The product must provide a mechanism for repeatedly opening and closing the storage box. | demonstration | box opening and closing operations |
| REQ-002 | performance | The product must remain securely closed during normal handling and transport without accidental opening. | demonstration | box remaining closed under handling/transport |
| REQ-003 | usability | The product must have a latch that is easy for a user to operate. | demonstration | ease of operation by user |
| REQ-004 | safety | The product must maintain secure closure during transport. | demonstration | box remaining closed during transport |
| REQ-005 | manufacturing | The product must be suitable for low-cost manufacturing. | inspection | manufacturing cost |
| REQ-006 | usability | The product must be practical for desktop use. | demonstration | practical desktop use |
| REQ-007 | manufacturing | The product must be mechanically plausible and easy to assemble. | inspection | mechanical plausibility and ease of assembly |
| REQ-008 | performance | The product must have a reusable latch mechanism. | demonstration | reusable latch mechanism |

Clause: `clauses[C-006]` source=clarification — "Approximate product size: desktop-sized (roughly hand-held)."

## S2. Missing criteria and quantities (source silence)
- No load magnitude, direction, duration or acceleration for "normal handling", "transport".
- No effort ceiling, force or torque for "easy to operate".
- No dimension, envelope or mass anywhere.
- No material; no manufacturing process; no cost model or cost target.
- No cycle count for "reusable".
- No opening angle, stroke, or open-state pose.
- No statement of which face opens, which side connects, or handedness.
- No statement that the closure remains attached when open.
- No statement that motion is bounded at the open extreme.
- No statement of rigidity or compliance.
- No statement of the side from which the user operates the latch.

## S3. Freedoms visible in the source
The source names a *function* ("latch", "mechanism for opening and closing")
and never a mechanism, geometry, arrangement, count, material or process.
`product_intent` says "storage box", implying a cavity to store into; it does
not say the cavity's shape.

## S4. Source conflicts / ambiguities
None internal to BM-001.

## S5. Evidence available, with fidelity
| Evidence | Path | Fidelity | What it is |
|---|---|---|---|
| Hinged closure with travel limit | `/home/ftk3187/github/ASSY_Ver1.0/m0/out/stop/t2_verdict_V-B_ring.json` | **V-B contact**, ring collision, friction_mu 0.3 | verdict=True, seeds_passed 5/5, theta_max 115.37 deg (thr >=90) |
| Same without limit (control) | `/home/ftk3187/github/ASSY_Ver1.0/m0/out/nostop/t2_verdict_V-B_ring.json` | **V-B contact**, identical preset | verdict=False, seeds_passed **1/5**, theta_max 219.65 deg |
| Snap retention task | `/home/ftk3187/github/ASSY_Ver1.0/tasks/snap_panel.json` | task definition, not measurement | B2 static snap_event `event_force_window_N = [15.0, 60.0]`; B1 assembly `[0.0, 80.0]` |
| Snap physics milestone | `/home/ftk3187/github/ASSY_Ver1.0/m23_latch_physics/` | tier-1 analytic + contact | — |

### E1. Evidence limitation recorded during Pass 1
In the m0 pair **every seed-0 criterion passes in BOTH stop and nostop**
(pin retention, theta_max>=90, travel interference, settles closed). The nostop
verdict is False only through seed aggregation (1/5). Therefore the pair
demonstrates *seed-level instability without a limit*; it does **not** exhibit a
seed-0 criterion that distinguishes them. Any claim built on this pair inherits
that weakness.

### E2. Evidence limitation recorded during Pass 1
The snap force window in `snap_panel.json` is an **input parameter of the task**,
not a measured product property. Citing it as an achieved value is circular.

## S6. Decisions made only by legacy reference realizations
`/home/ftk3187/github/ASSY_Ver1.0/m0/hinge_box.py` and the m0 fixtures fix: rectangular prismatic box; pin
hinge with ring-meshed knuckles; bore 2.150 / pin 2.000 mm; lid panel; a
discrete stop; theta target 90 deg. **None of these appears in any BM-001
requirement.**

## S7. Legacy implementation behaviour that must not define correctness
- `/home/ftk3187/github/ASSY_Ver2.0/assy/stages/s02_mechanical.py:408` — `selected_id=best.id`, ranked partly on `element count`; ties = "an arbitrary stable pick".
- `/home/ftk3187/github/ASSY_Ver2.0/assy/stages/s06_solver.py:51` — `unit=c.unit or "mm"`.
- `/home/ftk3187/github/ASSY_Ver2.0/assy/domain/upstream.py` — `SpatialZone`(:1547), `AxisStation`(:1522), `RadialPosition`(:859), `BodyPlacement.span: list[int]`, `ConceptVisualization`(:1724).
- `/home/ftk3187/github/ASSY_Ver2.0/assy/stages/s04_concept.py:308` — `_zone_of(pl) -> SpatialZone`.
- Rank-5 historical: `/home/ftk3187/github/ASSY_Ver2.0/BM-001_GOLDEN_STAGE_OUTPUTS.md`, `/home/ftk3187/github/ASSY_Ver2.0/out/BM-001/run-*` (78 runs).
