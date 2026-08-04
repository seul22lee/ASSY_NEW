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

### Review evidence — these five images only

| View | File |
|---|---|
| Overview, with the detail cuts located | [review_overview_section_lines.png](../executable_references/EXE-BM001-01/screenshots/review_overview_section_lines.png) |
| Knuckle set in side context | [review_section_knuckle_side_context.png](../executable_references/EXE-BM001-01/screenshots/review_section_knuckle_side_context.png) |
| Closure knuckle and pin | [review_section_closure_knuckle_pin.png](../executable_references/EXE-BM001-01/screenshots/review_section_closure_knuckle_pin.png) |
| Enclosure knuckle and pin | [review_section_enclosure_knuckle_pin.png](../executable_references/EXE-BM001-01/screenshots/review_section_enclosure_knuckle_pin.png) |
| Longitudinal: head, knuckles, recovered barb | [review_section_pin_head_and_snap_barb.png](../executable_references/EXE-BM001-01/screenshots/review_section_pin_head_and_snap_barb.png) |

All five are orthographic, viewed normal to the cutting plane, showing the cut
face only, with cut faces hatched. No perspective, no isometric inset, no general
product view.

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

## EXE-BM001-02 — reworked, awaiting review

Human decisions **HCR-BM001-004**, **-005**, **-006** and **-007** rejected the
full-open lift-out, the separate quarter-turn cam, and the cam's missing
orientation retention, and directed a guided captive sliding cover with an
integrated assembly snap and an integrated releasable latch.

The reference has been reworked twice. The first attempt kept the cam design's
lipped rails and added a snap to them; it needed a relief in the lips and a
loading position beyond the open bound to be assemblable at all, which is a
workaround, not a design. **The reference in the tree now is v0.3**, derived from
the retention question rather than from the old geometry:

> A cover that slides on two ledges between guide walls, held down for its whole
> life by a single snap rivet running in a slot, and held shut by a compliant
> latch cut from the cover itself.

There are no lips, no relief, no loading position outside the operating range and
no cam. The superseded artifacts have been deleted; the version history is in
[expected_evaluation.yaml](../executable_references/EXE-BM001-02/expected_evaluation.yaml).

### Review evidence — these six images only

| View | File |
|---|---|
| Overview (plan), with the detail cuts located | [review_overview_section_lines.png](../executable_references/EXE-BM001-02/screenshots/review_overview_section_lines.png) |
| A-A cover support and lateral guidance | [review_section_cover_support_and_guides.png](../executable_references/EXE-BM001-02/screenshots/review_section_cover_support_and_guides.png) |
| B-B what prevents removal at full open | [review_section_captive_at_full_open.png](../executable_references/EXE-BM001-02/screenshots/review_section_captive_at_full_open.png) |
| C-C snap rivet in its slot: bounds and anti-withdrawal | [review_section_rivet_and_slot.png](../executable_references/EXE-BM001-02/screenshots/review_section_rivet_and_slot.png) |
| D-D latch engaged | [review_section_latch_engaged.png](../executable_references/EXE-BM001-02/screenshots/review_section_latch_engaged.png) |
| D-D latch released | [review_section_latch_released.png](../executable_references/EXE-BM001-02/screenshots/review_section_latch_released.png) |

Same standard as EXE-BM001-01: orthographic, normal to the cut, cut faces
hatched, nothing behind the plane drawn, every detail cut located on the
overview. The general product views under the same directory (`s_closed_*`,
`s_open_*`) are produced by the machine artifact contract. **They are not review
evidence and are deliberately not linked here.**

### Supporting reports

- [validation/predicate_report.json](../executable_references/EXE-BM001-02/validation/predicate_report.json) — `supporting_measurements.captivity`, `.barb`, `.latch`, `.open_access`
- [validation/assembly_report.json](../executable_references/EXE-BM001-02/validation/assembly_report.json) — two straight insertions, ASM-03 swept in the declared compressed configuration
- [validation/motion_report.json](../executable_references/EXE-BM001-02/validation/motion_report.json) — 283 samples over three segments, plus the terminal-bound causal probe
- [validation/checker_selftest.json](../executable_references/EXE-BM001-02/validation/checker_selftest.json) — 9 negative controls, all detected
- [validation/human_review_checklist.md](../executable_references/EXE-BM001-02/validation/human_review_checklist.md) — the author's own reading, to be checked rather than trusted

### What was measured

| | |
|---|---|
| Slot width vs shaft | 5.400 mm vs 5.000 mm |
| Compressed lug envelope across the slot | 5.000 mm — fits, 0.400 mm clearance |
| Relaxed lug envelope | 7.600 mm across a 5.400 mm slot |
| Lug projection beyond the slot | 1.100 mm each side |
| Arm gap vs required deflection | 2.80 mm vs 2×1.30 mm — arms cannot bottom out |
| Deformation volume difference | 0.000 mm³ |
| Captivity: 3 mm lift at 0 / 10 / 40 / 70 / 84 mm | blocked at all five, 14.222 mm³ of lug interference at each |
| Terminal bounds | 0.0 mm³ inside 0–84 mm; 0.61 mm³ 1 mm outside each end |
| Latch: block onset when engaged | 1.05 mm (the hook stands 1.0 mm clear by running clearance) |
| Latch: released, over a 6 mm sweep | 0.000 mm³ — genuinely frees the cover |
| Assembly: swept common volume, both presses | 0.000 mm³ |
| Declared usable access covered when closed | 18160 mm³ in the aperture band |

### Reviewer decisions — all PENDING

| # | Question | Decision |
|---|---|---|
| 1 | Does this read as one integrated snap-fit closure, or as an old mechanism with a snap feature bolted on? | PENDING |
| 2 | At full open, can you see what physically stops the cover lifting? | PENDING |
| 3 | Is the rivet's anti-withdrawal barb real geometry with a credible recovery space, not a symbol? | PENDING |
| 4 | Is the assembly path plausible as a real process — two straight presses, nothing threaded past anything? | PENDING |
| 5 | Is the keeper bridge standing 2.5 mm above the closed cover acceptable, or does it defeat a flush sliding cover? | PENDING |
| 6 | Is 1.05 mm of free play before the latch bites a latch, or a rattle? | PENDING |
| 7 | Is a permanent, non-removable rivet acceptable, or is `LIM-01` a defect dressed as captivity? | PENDING |
| 8 | Is 1.30 mm of deflection per arm, and 2.6 mm on the latch beam, credible for a moulded polymer? | PENDING |
| 9 | Is any intended cover / enclosure / rivet interaction missing from the declaration? | PENDING |
| 10 | Are the unknown snap force, release effort, strain and fatigue correctly left NOT_VERIFIED? | PENDING |

### What the author could not check

Snap-in force, pull-out capacity, release effort, strain, creep, fatigue,
repeated-use life and tolerance robustness are all **NOT_VERIFIED**. Geometric
blockage is not holding strength, and nothing in this pilot computes a force.

Questions 5, 6 and 7 are the ones the author most wants answered and is least
able to answer. Each is a judgement about whether a measured, honestly reported
number is *good enough* — and none of them is the author's to make.

One check in this reference was found to be vacuous during the rework and has
been strengthened: `NRM-BM-001-003`'s "is this a region the cover controls"
clause was being measured in the clear space above the aperture, where the cover
never goes, so it read 0 mm³ and passed regardless. It is now measured in the
aperture band, and `CTL-09` confirms it can fail. A reviewer should assume other
checks may be vacuous in ways nobody has noticed yet.

---

## How to record a decision

Replace `PENDING` with `ACCEPT`, `REJECT_CURRENT_GEOMETRY` or
`NEEDS_CHANGE` plus a reason, then set
`independent_human_review_complete: true` in `HUMAN_REVIEW_STATUS.yaml` only when
every row is decided. Until then no downstream artifact may describe either
reference as human-approved.
