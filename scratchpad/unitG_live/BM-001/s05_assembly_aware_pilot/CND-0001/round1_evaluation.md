# Round-1 evaluation — CND-0001 assembly-aware pilot

`CompileResult.ok` was **False**, and that is not the point. Every answer below
is measured from the actual S07-compiled B-reps (`round1_assembly_evidence.json`)
or computed from the design's own declared dimensions. Nothing here comes from
looking at a picture.

## Measured facts

| body | solids | volume |
|---|---|---|
| BOD-0001 base | **3** | 58 553.5 mm³ |
| BOD-0002 lid | **2** | 36 550.2 mm³ |
| BOD-0003 pin | 1 | 766.5 mm³ |

| state | pair | interpenetration | closest distance |
|---|---|---|---|
| CLOSED | base ↔ lid | 0 mm³ | **13.0 mm** |
| CLOSED | base ↔ pin | 61.65 mm³ | 0.0 mm |
| CLOSED | lid ↔ pin | 0 mm³ | **15.0 mm** |
| OPEN | base ↔ lid | 0 mm³ | **15.0 mm** |
| OPEN | base ↔ pin | 61.65 mm³ | 0.0 mm |
| OPEN | lid ↔ pin | 0 mm³ | **17.0 mm** |

Solver `feasible`; S07 produced **0** findings.

## The single dominant cause: an internal datum inconsistency

The design places `base_outer` at `[0, 0, 0]`, and in this language `at` is the
**centre**. So the base occupies z ∈ [−20, +20] and its top face is at
`base_height/2` = 20.

The design then places every base-side feature in that convention —
`hinge_bore_base` at `base_height/2` = 20, `latch_recess` at
`base_height/2 − latch_recess_depth/2` = 18.5 — but places every lid-side
feature as if the base spanned 0…40:

- `lid_plate` at z = `base_height` = 40
- `hinge_bore_lid` at z = `base_height + lid_plate_size[2]/2` = 43
- `snap_hook` at z = `base_height + lid_plate_size[2]` = 46

The whole lid is therefore exactly `base_height/2` = 20 mm too high. Everything
below follows from that one error.

## The 13 questions

| # | question | answer | evidence |
|---|---|---|---|
| 1 | Are all bodies individually connected? | **No** | base = 3 solids, lid = 2 solids |
| 2 | Do base/lid hinge features share one actual hinge axis? | **No** | base bore axis z = 20.00, lid bore axis z = 43.00 — **23 mm apart**; x and axis direction (+Y) do agree |
| 3 | Does the pin pass through the required knuckles? | **No** | pin ∩ lid = 0 mm³ in both states; pin sits at z = 20, the lid bore at z = 43 |
| 4 | Can the pin actually be inserted? | **Not as a hinge** | it enters the base bore only; base ∩ pin = 61.65 mm³ is *interference*, not the declared clearance fit |
| 5 | Is there an axial-retention concept? | **Declared, not realized** | the sequence says "the lid holds it"; the lid never touches the pin (15/17 mm away). Pin length 62 mm vs base depth 60 mm leaves 1 mm proud per side, with no feature engaging it |
| 6 | Can lid and base be assembled in the stated sequence? | **No** | step 3 requires the lid knuckle to slide onto the pin; they are 15 mm apart |
| 7 | Is the lid still attached to the base in OPEN? | **No** | every lid↔anything overlap is 0 mm³; the lid is a free body in both states |
| 8 | Does CLOSED seat the lid on the base? | **No** | 13 mm gap, no contact anywhere |
| 9 | Is there an actual hook/catch pair? | **Geometry exists, never meets** | hook centre (x 51.5, z 46), recess centre (x 48.5, z 18.5) — 27.5 mm apart vertically |
| 10 | Is the compliant member connected to its parent body? | **No** | the lid compiles as 2 solids; the beam/hook group is separate from the plate |
| 11 | Is there visible deflection/release space? | **Not meaningfully** | the hook is in open air 27.5 mm above its recess, so nothing constrains or deflects it |
| 12 | Does latch geometry correspond to CLOSED engagement and OPEN release? | **No** | hook ∩ recess = 0 in both states; CLOSED and OPEN are latch-identical |
| 13 | Are required free/access regions actually free? | **Vacuously yes** | nothing occupies the openings because nothing reaches them; S07 reported 0 findings |

**Score: 0 of 13.** Round 1 is three mutually disconnected part-groups that
share a coordinate frame, not a mechanism.

## What round 1 did get right

The declarations themselves were coherent: two `mating_sets` naming real
participants and binding them to the upstream `IFC-*`/`JNT-*`/`PHI-*` ids, a
3-step `assembly_sequence` with insertion directions and access, and
`state_expectations` for both states. The failure is that none of it was
realized in geometry — which is exactly the gap the assembly-aware language was
added to expose.
