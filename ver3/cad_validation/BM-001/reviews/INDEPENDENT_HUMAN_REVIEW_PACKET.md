# BM-001 independent human review packet

**Status: `HUMAN_REVIEW_PENDING`.** Nothing below is approved. Every reviewer
decision in this file is `PENDING` and must be filled in by a person.

This packet contains **drawings**, **motion videos** and **measurements**. The
measurements are the evidence; the drawings and videos exist so that a person can
see what was measured. No geometric claim in this pilot rests on an image or a
frame, and nothing in any video establishes a force, a strain or a life.

The author of this geometry also wrote this packet. Treat the middle column of
any table here as a claim to be checked, not as a finding.

---

## EXE-BM001-01 — revised twice, awaiting review

**Round 1 (HCR-BM001-002).** The previous hinge pin blocked axial removal in one
direction only and the far end could walk out. It was replaced with a headed pin
carrying two integral cantilever snap arms.

**Round 2 (HCR-BM001-008, -009, -010).** The separate lift-bolt that held the lid
shut was rejected as functionally excessive: a whole extra body plus a knob, a
shaft, a closure guide boss, an enclosure socket, an extra assembly step and a
manual re-engagement, all to let the user open a lid. It could also be mistaken
for a key, which it never was — no keying, no authorization, no security.

`BODY-BOLT` is gone, with its knob, shaft, guide boss and socket. The product is
now **three bodies**: the closure carries an **integral exterior snap latch** and
the enclosure carries the **keeper**. The hinge pin is untouched — its
sub-signature is identical before and after.

Pull the pad 2.4 mm outward, the tooth clears the keeper, the lid opens. Push the
lid shut and the tooth's lead-in ramp deflects the beam by itself; past the
keeper the beam recovers and the tooth drops back under it. Nothing is put back
by hand, and nothing can be dropped or lost.

### Review evidence — these five images only

| View | File |
|---|---|
| Overview: three bodies, latch operation, and where the cuts are taken | [review_overview_latch_operation_and_sections.png](../executable_references/EXE-BM001-01/screenshots/review_overview_latch_operation_and_sections.png) |
| Knuckle set in side context | [review_section_knuckle_side_context.png](../executable_references/EXE-BM001-01/screenshots/review_section_knuckle_side_context.png) |
| Closure knuckle and pin | [review_section_closure_knuckle_pin.png](../executable_references/EXE-BM001-01/screenshots/review_section_closure_knuckle_pin.png) |
| Enclosure knuckle and pin | [review_section_enclosure_knuckle_pin.png](../executable_references/EXE-BM001-01/screenshots/review_section_enclosure_knuckle_pin.png) |
| Longitudinal: head, knuckles, recovered barb | [review_section_pin_head_and_snap_barb.png](../executable_references/EXE-BM001-01/screenshots/review_section_pin_head_and_snap_barb.png) |

**The latch**

| View | File |
|---|---|
| E-E — latch ENGAGED, tooth under the keeper | [review_section_latch_engaged.png](../executable_references/EXE-BM001-01/screenshots/review_section_latch_engaged.png) |
| E-E — latch RELEASED, same plane and scale | [review_section_latch_released.png](../executable_references/EXE-BM001-01/screenshots/review_section_latch_released.png) |

**Operation sequence**

| View | File |
|---|---|
| 1 — closed and latched | [review_operation_01_closed_latched.png](../executable_references/EXE-BM001-01/screenshots/review_operation_01_closed_latched.png) |
| 2 — release pad pulled out | [review_operation_02_release_pressed.png](../executable_references/EXE-BM001-01/screenshots/review_operation_02_release_pressed.png) |
| 3 — opening started | [review_operation_03_opening_started.png](../executable_references/EXE-BM001-01/screenshots/review_operation_03_opening_started.png) |
| 4 — open, 110° | [review_operation_04_open.png](../executable_references/EXE-BM001-01/screenshots/review_operation_04_open.png) |
| 5 — reclosed, snap re-engaged | [review_operation_05_reclosed_latched.png](../executable_references/EXE-BM001-01/screenshots/review_operation_05_reclosed_latched.png) |

All are orthographic, viewed normal to the cutting plane, showing the cut face
only, with cut faces hatched. No perspective, no isometric inset, no general
product view. The engaged and released latch sections use the same plane and the
same scale, so the 2.4 mm release is a comparison and not a claim.

The general product views under the same directory (`s_closed_retained_*`,
`section_knuckle_*`, and so on) are produced by the machine artifact contract.
**They are not review evidence and are deliberately not linked here.**

### Motion video

| Clip | File |
|---|---|
| Lid: LATCHED → RELEASE → OPENING → HOLD → CLOSING → RE-ENGAGED, 349 frames, 11.63 s, 30 fps, 1280×720, H.264 | [lid_operation.mp4](../executable_references/EXE-BM001-01/validation/simulation/lid_operation.mp4) |
| The same clip as a GIF, for quick viewing | [lid_operation.gif](../executable_references/EXE-BM001-01/validation/simulation/lid_operation.gif) |
| Record: engine, signature, camera, timeline, hashes, claims | [lid_operation_video.json](../executable_references/EXE-BM001-01/validation/simulation/lid_operation_video.json) |

The visible lid is the CAD closure solid, not the point mass MuJoCo integrates.
Every frame carries the simulation time, the lid angle, the instantaneous hinge
torque, the static gravity torque, the OPENING / HOLD / CLOSING phase, and the
statement that **density is assumed and friction is zero**. The video frames and
the three plots are drawn from the *same* solver rows — one frame per 100 solver
steps, no resampling — so a number read off a frame is a number on the curve.

The torques are a **lower bound** on real effort under those assumptions. They
are not a measurement, and the source states no effort ceiling for them to be
compared against. See [VIDEO_REVIEW_AUDIT.md](VIDEO_REVIEW_AUDIT.md).

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
| 8 | Is the integral latch clearly a **latch** — not a key, a lock or an access control? | PENDING |
| 9 | Is pulling a pad outward the right release action, or would a user expect to press? | PENDING |
| 10 | Is 0.257° of free play before the latch bites acceptable, or is the lid loose? | PENDING |
| 11 | Is 2.4 mm of deflection on this beam credible for a moulded polymer? | PENDING |
| 12 | Is an 8.4 mm front lip acceptable, or does the latch cost too much overhang? | PENDING |
| 7 | Watching `lid_operation.mp4`, does the lid motion and the reported effort look credible for this geometry? | PENDING |

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

## EXE-BM001-02 — redesigned as two bodies, awaiting review

Human decisions **HCR-BM001-004**, **-005**, **-006** and **-007** rejected the
full-open lift-out, the separate quarter-turn cam, and the cam's missing
orientation retention, and directed a guided captive sliding cover with an
integrated assembly snap and an integrated releasable latch.

The reference has been rebuilt from the concept up. **It is now two product
bodies and nothing else:**

> `BODY-ENCLOSURE` — cavity, top panel, and two captive C-section rails
> `BODY-COVER` — plate, four integral retention tabs, one integral latch finger

Each rail carries all three retention functions: a **ledge** that supports, a
**guide wall** that locates, and an **overhanging retaining lip** that blocks
lift. The cover's plate passes *between* the two lips; its four tabs deflect
2.2 mm inboard to pass with it, then recover underneath. That is the assembly and
the retention in one feature set. Nothing is fastened, riveted, pinned or
clipped, and no third body exists at any point.

`DESIGN_AND_OPERATION_RATIONALE.md` in the reference directory explains the
mechanism in plain terms and is worth reading before the drawings.

### Review evidence — these fourteen images only

**Overview**

| View | File |
|---|---|
| Plan: both bodies, operation arrows, where A-A / C-C / D-D are taken | [review_overview_operation_and_sections.png](../executable_references/EXE-BM001-02/screenshots/review_overview_operation_and_sections.png) |

**Assembly sequence**

| View | File |
|---|---|
| 1 — cover aligned, tabs already deflected | [review_assembly_01_aligned.png](../executable_references/EXE-BM001-02/screenshots/review_assembly_01_aligned.png) |
| 2 — tabs passing the lips, the actual limiting opening | [review_assembly_02_tabs_compressed.png](../executable_references/EXE-BM001-02/screenshots/review_assembly_02_tabs_compressed.png) |
| 3 — tabs recovered under the lips, cover captive | [review_assembly_03_tabs_recovered.png](../executable_references/EXE-BM001-02/screenshots/review_assembly_03_tabs_recovered.png) |

**Operating sequence**

| View | File |
|---|---|
| 1 — closed and latched | [review_operation_01_closed_latched.png](../executable_references/EXE-BM001-02/screenshots/review_operation_01_closed_latched.png) |
| 2 — release pressed | [review_operation_02_release_pressed.png](../executable_references/EXE-BM001-02/screenshots/review_operation_02_release_pressed.png) |
| 3 — sliding open | [review_operation_03_slide_open.png](../executable_references/EXE-BM001-02/screenshots/review_operation_03_slide_open.png) |
| 4 — full open, 84 mm clear, still captive | [review_operation_04_full_open_captive.png](../executable_references/EXE-BM001-02/screenshots/review_operation_04_full_open_captive.png) |
| 5 — reclosed and latched | [review_operation_05_reclosed_and_latched.png](../executable_references/EXE-BM001-02/screenshots/review_operation_05_reclosed_and_latched.png) |

**Sections**

| View | File |
|---|---|
| A-A — the captive rail, closed: all three rail functions | [review_section_AA_captive_rail_closed.png](../executable_references/EXE-BM001-02/screenshots/review_section_AA_captive_rail_closed.png) |
| B-B — the same capture at full open | [review_section_BB_captive_rail_full_open.png](../executable_references/EXE-BM001-02/screenshots/review_section_BB_captive_rail_full_open.png) |
| C-C — the assembly snap against the limiting gap | [review_section_CC_assembly_snap.png](../executable_references/EXE-BM001-02/screenshots/review_section_CC_assembly_snap.png) |
| D-D — latch engaged | [review_section_DD_latch_engaged.png](../executable_references/EXE-BM001-02/screenshots/review_section_DD_latch_engaged.png) |
| D-D — latch released, same plane and scale | [review_section_DD_latch_released.png](../executable_references/EXE-BM001-02/screenshots/review_section_DD_latch_released.png) |

Same standard as EXE-BM001-01: orthographic, normal to the cut, cut faces
hatched, nothing behind the plane drawn, every detail cut located on an overview.
Direction of motion and direction of press are drawn as heavy arrows rather than
described in words. The per-state general views under the same directory
(`closed_latch_engaged_*`, `open_84_*`, and so on) are produced by the machine
artifact contract. **They are not review evidence and are deliberately not linked
here.** Their disposition is recorded in
[validation/PNG_REVIEW_AUDIT.md](../executable_references/EXE-BM001-02/validation/PNG_REVIEW_AUDIT.md).

### Motion videos

| Clip | File |
|---|---|
| Operation: closed → press → slide open → full open (captive) → slide closed → snap re-engaged. 301 frames, 10.03 s | [cover_operation.mp4](../executable_references/EXE-BM001-02/validation/simulation/cover_operation.mp4) |
| Snap-in assembly: aligned → tabs compressed → past the lips → ears recovered → captive. 271 frames, 9.03 s | [cover_snap_assembly.mp4](../executable_references/EXE-BM001-02/validation/simulation/cover_snap_assembly.mp4) |
| Records for both: engine, signature, cameras, timelines, hashes, claims | [cover_videos.json](../executable_references/EXE-BM001-02/validation/simulation/cover_videos.json) |

Both are rendered from the final two-body CAD, 30 fps, 1280×720, H.264. There is
no rivet, pin, cam or floating keeper in any frame, because none exists in the
model. The operating clip carries a second **fixed** camera as an inset on the
latch, because a 2.6 mm release on a 190 mm product is invisible at product
scale; in that inset the tooth is plainly behind the keeper when closed and clear
of it when the pad is pushed.

The assembly clip is a **prescribed geometric-state animation**, labelled
`GEOMETRIC COMPLIANT-STATE REPRESENTATION / FORCE / STRAIN NOT VERIFIED` on every
frame. It is sectioned at X = 118 mm, stated on every frame, because a rail lip
is exactly what hides the thing it retains. See
[VIDEO_REVIEW_AUDIT.md](VIDEO_REVIEW_AUDIT.md).

### Supporting reports

- [DESIGN_AND_OPERATION_RATIONALE.md](../executable_references/EXE-BM001-02/DESIGN_AND_OPERATION_RATIONALE.md) — the mechanism in plain terms
- [validation/predicate_report.json](../executable_references/EXE-BM001-02/validation/predicate_report.json) — `supporting_measurements.rails`, `.assembly_snap`, `.captivity`, `.latch`, `.release`, `.keeper`, `.opening`
- [validation/assembly_report.json](../executable_references/EXE-BM001-02/validation/assembly_report.json) — one insertion, swept in the declared compressed configuration
- [validation/checker_selftest.json](../executable_references/EXE-BM001-02/validation/checker_selftest.json) — 16 negative controls, all detected
- [validation/PNG_REVIEW_AUDIT.md](../executable_references/EXE-BM001-02/validation/PNG_REVIEW_AUDIT.md) — what was seen when every image was opened

### What was measured

| | |
|---|---|
| Rails: ledge, guide wall, overhanging lip | present on both sides, lips continuous over x 13–187 |
| Limiting opening (gap between lip inner edges) | 59.600 mm |
| Cover span, tabs relaxed | 63.600 mm — larger than the opening, which is why it stays in |
| Cover span, tabs deflected 2.2 mm | 59.200 mm — 0.400 mm clearance, so it goes in |
| Assembly sweep, one straight press | 0.000 mm³ common volume |
| Ear engagement under a lip | 2.0 mm each, 31.2 mm³ per tab at a 3 mm lift, four for four |
| Free vertical play before the lips bite | 0.450 mm |
| Captivity at 0 / 10 / 40 / 70 / 84 mm | 124.8 / 133.6 / 133.6 / 133.6 / 133.6 mm³ — blocked at every one |
| Pitch and roll probes (±1.5° with a 1.5 mm lift) | 12 of 12 blocked |
| Latch engagement behind the keeper | 2.200 mm |
| Closed free play before the latch bites | 0.600 mm declared, 0.620 mm measured |
| Release shift, and what it does | 2.6 mm inboard; tooth behind the keeper goes 23.23 → 0.000 mm³ |
| Re-engagement after a full closing sweep | seated 0.000 mm³, blocking again 9.88 mm³ |
| Terminal bounds | free inside 0–84 mm, interference 1 mm outside each end |
| Usable opening | 84.0 mm of a 90.0 mm aperture; 0.000 mm³ of intrusion |
| Release pad outside the product envelope | 357.55 mm³, x 194.5–201.0 |

### Reviewer decisions — all PENDING

| # | Question | Decision |
|---|---|---|
| 1 | Does this read as one integrated snap-fit mechanism, or as a rail with something added to it? | PENDING |
| 2 | Is the rail cross-section a real captive rail — ledge, guide wall **and** overhanging lip? | PENDING |
| 3 | At full open, can you see what physically stops the cover lifting? | PENDING |
| 4 | Is the assembly plausible as a real process: deflect four tabs, press once, let go? | PENDING |
| 5 | Is 2.2 mm of deflection on a 20 mm tab credible for a moulded polymer, and are four tabs enough? | PENDING |
| 6 | Is the release intuitive — push a pad sideways, then slide? Or would a user look for a lift? | PENDING |
| 7 | Is 0.62 mm of free play before the latch bites a latch, or a rattle? | PENDING |
| 8 | Is an 11 mm pad protruding from the end face acceptable? | PENDING |
| 9 | Is service removal (four tabs deflected at once through the rail channels) acceptable, or is `LIM-01` a defect dressed as captivity? | PENDING |
| 10 | Is any intended cover / enclosure interaction missing from the declaration? | PENDING |
| 11 | Are the unknown snap force, release effort, strain and fatigue correctly left NOT_VERIFIED? | PENDING |
| 12 | Watching `cover_operation.mp4`, is the mechanism understandable without the drawings or the code? | PENDING |
| 13 | Watching `cover_snap_assembly.mp4`, is the snap-in process plausible as a real assembly step? | PENDING |

### What the author could not check

Snap insertion force, pull-out capacity, release effort, material strain, root
stress, creep, fatigue, repeated-cycle life, wear, impact resistance, tolerance
robustness, moulding feasibility and cost are all **NOT_VERIFIED**. Geometric
blockage is not holding strength, and nothing in this pilot computes a force.

Questions 5, 6, 7, 8 and 9 are the ones the author most wants answered and is
least able to answer. Each is a judgement about whether a measured, honestly
reported number is *good enough*, and none of them is the author's to make.

One defect in this redesign was caught by looking at a drawing rather than by the
checker: an earlier arrangement put the latch finger on the centreline, where it
retracted **into** the declared 84 mm opening at full open. The access probe
missed it because the probe sampled only the space above the cover, and the
finger sits level with it. The latch was moved out over the near rail. A reviewer
should assume other checks may be blind in ways nobody has noticed yet.

---

## How to record a decision

Replace `PENDING` with `ACCEPT`, `REJECT_CURRENT_GEOMETRY` or
`NEEDS_CHANGE` plus a reason, then set
`independent_human_review_complete: true` in `HUMAN_REVIEW_STATUS.yaml` only when
every row is decided. Until then no downstream artifact may describe either
reference as human-approved.
