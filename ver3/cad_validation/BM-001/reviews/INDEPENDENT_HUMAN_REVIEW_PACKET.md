# BM-001 independent human review packet

**Status: `HUMAN_REVIEW_PENDING`.** Nothing below is approved. Every reviewer
decision in this file is `PENDING` and must be filled in by a person.

The author of this geometry also wrote this packet. Treat the middle column of
any table here as a claim to be checked, not as a finding.

---

## EXE-BM001-01 — revised, awaiting review

Human decision **HCR-BM001-002** rejected the previous hinge pin: its head
blocked axial removal in one direction only, and the far end could walk out. The
pin has been replaced with a headed pin carrying two integral cantilever snap
arms.

### Review evidence — these three images only

| View | File |
|---|---|
| Closure knuckle and pin | [review_section_closure_knuckle_pin.png](../executable_references/EXE-BM001-01/screenshots/review_section_closure_knuckle_pin.png) |
| Enclosure knuckle and pin | [review_section_enclosure_knuckle_pin.png](../executable_references/EXE-BM001-01/screenshots/review_section_enclosure_knuckle_pin.png) |
| Longitudinal: head, knuckles, recovered barb | [review_section_pin_head_and_snap_barb.png](../executable_references/EXE-BM001-01/screenshots/review_section_pin_head_and_snap_barb.png) |

All three are orthographic, viewed normal to the cutting plane, showing the cut
face only. No perspective, no isometric inset, no general product view.

The general product views under the same directory (`s_closed_retained_*`,
`section_knuckle_*`, and so on) are produced by the machine artifact contract.
**They are not review evidence and are deliberately not linked here.**

### Supporting reports

- [validation/predicate_report.json](../executable_references/EXE-BM001-01/validation/predicate_report.json) — `supporting_measurements.pin_axial_retention` holds the barb geometry, the bidirectional axial block and the lug recovery
- [validation/assembly_report.json](../executable_references/EXE-BM001-01/validation/assembly_report.json) — ASM-03 swept in the declared compressed configuration
- [validation/interaction_report.json](../executable_references/EXE-BM001-01/validation/interaction_report.json) — INT-16 retaining shoulder, INT-17 declared compliant passage
- [validation/checker_selftest.json](../executable_references/EXE-BM001-01/validation/checker_selftest.json) — 12 negative controls, all detected

### What was measured

| | |
|---|---|
| Bore diameter | 4.2 mm |
| Compressed envelope (circumscribed) | 4.161 mm — fits, 0.020 mm radial clearance |
| Relaxed lug envelope | 6.000 mm |
| Shoulder projection beyond bore | 0.900 mm |
| Arm gap vs required deflection | 2.40 mm vs 2.10 mm — arms cannot bottom out |
| Block toward the barb end | FEA-P-SHOULDER on FEA-E-CBORE, onset 0.05 mm |
| Block toward the head end | FEA-P-LUG-SHOULDER on FEA-E-FARFACE, onset 0.60 mm |
| Deformation volume difference | 0.000 mm³ (0.000%) |

### Reviewer decisions — all PENDING

| # | Question | Decision |
|---|---|---|
| 1 | Is the snap barb clearly represented as real geometry, not a symbol? | PENDING |
| 2 | Is the pin blocked in **both** axial directions, and can you see which face does each? | PENDING |
| 3 | Does the declared snap insertion look geometrically coherent — arms, lead-in, recovery space? | PENDING |
| 4 | Is any intended pin / closure / enclosure interaction missing from the declaration? | PENDING |
| 5 | Is a 1.05 mm deflection on a 6 mm arm credible for a moulded polymer, or is this asking too much of the material? | PENDING |
| 6 | Are the unknown snap force, strain and fatigue correctly left NOT_VERIFIED? | PENDING |

### What the author could not check

Whether the arms survive the deflection. Insertion force, recovery force,
pull-out force, strain, stress, fatigue, creep, repeated-use life and
manufacturing tolerance robustness are all **NOT_VERIFIED**. Geometric blockage
is not holding strength, and nothing in this pilot computes a force.

Question 5 is the one the author most wants answered and least able to answer.
The correction traded away the original avoidance of compliant features: the pin
is now compliant polymer and its assembly needs a real deflection. That trade is
recorded in `manifest.yaml` LIM-01 rather than hidden.

---

## EXE-BM001-02 — not revised, do not review yet

Human decisions **HCR-BM001-004**, **-005**, **-006** and **-007** rejected the
full-open lift-out, the separate quarter-turn cam, and the cam's missing
orientation retention, and directed a guided captive sliding cover with an
integrated assembly snap and an integrated releasable latch.

**None of that redesign has been done.** The reference still contains `BODY-CAM`
and still declares the cover liftable at full open. Its existing artifacts
describe the rejected design and should not be reviewed as though they were the
answer.

Status: `PENDING_REDESIGN`.

---

## How to record a decision

Replace `PENDING` with `ACCEPT`, `REJECT_CURRENT_GEOMETRY` or
`NEEDS_CHANGE` plus a reason, then set
`independent_human_review_complete: true` in `HUMAN_REVIEW_STATUS.yaml` only when
every row is decided. Until then no downstream artifact may describe either
reference as human-approved.
