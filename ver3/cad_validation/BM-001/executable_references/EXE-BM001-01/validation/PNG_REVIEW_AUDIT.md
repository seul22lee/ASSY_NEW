# EXE-BM001-01 - PNG review audit

**Status: `AUTHOR_SELF_REVIEW` - `HUMAN_REVIEW_PENDING`.**

Every PNG in `screenshots/` was opened and looked at, not inferred from its
filename or from what the code was supposed to draw.

This reference has been revised twice. The second revision removed `BODY-BOLT`,
its knob and shaft, the closure guide boss and the enclosure socket, and replaced
them with an integral snap latch on the closure against a keeper on the
enclosure. **Every image that depicted the bolt has been deleted**, not left as
"legacy": `section_retention_closed_*`, `section_retention_released_*`, and the
whole `s_closed_retained_*` / `s_closed_released_*` / `s_open_*` machine set,
which was keyed to state names that no longer exist.

## Dispositions

| File | Purpose | Connected? | Explains? | Cut located? | Cut faces marked? | Artifacts? | Disposition |
|---|---|---|---|---|---|---|---|
| `review_overview_latch_operation_and_sections.png` | whole footprint, three bodies, latch operation, where A-A/B-B/C-C/E-E are taken | yes | yes - pull direction and hinge axis are heavy arrows | n/a (it *is* the locator) | yes | none | REVIEW_EVIDENCE |
| `review_section_latch_engaged.png` | the engaged latch, both halves in one plane | yes - pad, beam and tooth are one hatched region | yes - engagement and free play are on the drawing | E-E, on the overview | yes | none | REVIEW_EVIDENCE |
| `review_section_latch_released.png` | the same plane and scale, released | yes | yes - PULL and NOW FREE TO OPEN arrows | E-E | yes | none | REVIEW_EVIDENCE |
| `review_operation_01_closed_latched.png` | closed and latched | yes | yes - OPENING BLOCKED arrow | E-E plane | yes | none | REVIEW_EVIDENCE |
| `review_operation_02_release_pressed.png` | released | yes | yes - PULL THE PAD (-Y) arrow | E-E plane | yes | none | REVIEW_EVIDENCE |
| `review_operation_03_opening_started.png` | opening begun; tooth above the keeper, beam already recovered | yes | yes - LID ROTATES OPEN arrow | E-E plane | yes | none | REVIEW_EVIDENCE |
| `review_operation_04_open.png` | terminal open pose, stop block on the rear wall | yes | yes | E-E plane | yes | none | REVIEW_EVIDENCE |
| `review_operation_05_reclosed_latched.png` | reclosed, latch engaged again | yes | yes - PUSH SHUT arrow | E-E plane | yes | none | REVIEW_EVIDENCE |
| `review_section_closure_knuckle_pin.png` | closure knuckle on the pin | yes | yes | A-A | yes | none | REVIEW_EVIDENCE (unchanged by this revision) |
| `review_section_enclosure_knuckle_pin.png` | enclosure knuckle on the pin | yes | yes | B-B | yes | none | REVIEW_EVIDENCE (unchanged) |
| `review_section_knuckle_side_context.png` | the knuckle set in side context | yes | yes | C-C | yes | none | REVIEW_EVIDENCE (unchanged) |
| `review_section_pin_head_and_snap_barb.png` | head, knuckles and recovered barb | yes | yes | D-D | yes | none | REVIEW_EVIDENCE (unchanged) |
| per-state general views, 4 each for the eight declared states (36 files) | step 9 of the validation chain | - | - | - | - | transparent wireframe with tessellation diagonals | MACHINE_ONLY |

The machine set is a record that the states build and render, nothing more. **It
is not review evidence, it is not linked in the human-review packet, and no claim
rests on it.**

## The question this file exists to answer

> **Can a reviewer understand how the latch is engaged, released and re-engaged
> without reading source code?**

**YES.**

- *How is it engaged?* -
  [`review_section_latch_engaged.png`](../screenshots/review_section_latch_engaged.png)
  shows the tooth under the keeper with the 0.4 mm shoulder gap and the 2.2 mm
  engagement written on the drawing;
  [`review_operation_01_closed_latched.png`](../screenshots/review_operation_01_closed_latched.png)
  shows the same relation in the whole product with the blocked direction arrowed.
- *How is it released?* -
  [`review_section_latch_released.png`](../screenshots/review_section_latch_released.png)
  is the same plane at the same scale with the beam pulled 2.4 mm out and the
  tooth clear of the keeper, so the pair is a direct comparison;
  [`review_operation_02_release_pressed.png`](../screenshots/review_operation_02_release_pressed.png)
  carries the PULL (-Y) arrow on the product.
- *How does it re-engage?* -
  [`review_operation_05_reclosed_latched.png`](../screenshots/review_operation_05_reclosed_latched.png)
  with its PUSH SHUT - THE LATCH SNAPS BACK arrow. The lead-in ramp itself is
  visible as the tooth\'s sloped underside in the engaged section.
- *Where is the release, and which way does the lid open?* -
  [`review_overview_latch_operation_and_sections.png`](../screenshots/review_overview_latch_operation_and_sections.png)
  labels the latch, the keeper and the hinge axis and carries both direction
  arrows.
- *Is there still a bolt?* - no image contains one, because no geometry does.

## What this audit is not

It is the author\'s own reading of the author\'s own drawings, which is the weakest
kind of review there is. It records that the images are legible and that they
depict the geometry that was actually measured. It does not establish that the
latch is a good latch, and no person has yet looked at any of these images. Latch
force, strain, holding capacity, fatigue and material adequacy are `NOT_VERIFIED`
and no drawing here bears on them.
