# EXE-BM001-02 — PNG review audit

**Status: `AUTHOR_SELF_REVIEW` — `HUMAN_REVIEW_PENDING`.**

Every PNG in `screenshots/` was opened and looked at, not inferred from its
filename or from what the code was supposed to draw. This file records what was
seen and what was done about it.

## Dispositions

`REVIEW_EVIDENCE` — a drawing a reviewer may rely on.
`MACHINE_ONLY` — produced by the artifact contract; not review evidence.
`DELETE_AND_REGENERATE` — found defective; fixed, or the file removed.

### Review drawings

| File | Purpose | Visible | Connected? | Explains? | Cut located? | Cut faces marked? | Artifacts? | Disposition |
|---|---|---|---|---|---|---|---|---|
| `review_overview_operation_and_sections.png` | whole footprint, both bodies, operation arrows, where A-A/C-C/D-D are taken | enclosure walls and rails, cover plate, four tab slots, latch finger through the end wall | yes — cover is one hatched region with its tabs and finger | yes: slide direction and press direction are heavy arrows, not words | n/a (it *is* the locator) | yes, `///` enclosure, `\\\` cover | none | REVIEW_EVIDENCE |
| `review_assembly_01_aligned.png` | cover held above the rails, tabs already deflected | both lips, both ledges, cover with ears held in | yes | yes — press direction and the two tab-deflection arrows | A-A plane, marked on the overview | yes | none | REVIEW_EVIDENCE |
| `review_assembly_02_tabs_compressed.png` | the moment of passage, against the real limiting gap | lip inner edges and the compressed cover between them | yes | yes — the 59.2 vs 59.6 mm numbers are on the drawing | A-A plane | yes | none | REVIEW_EVIDENCE |
| `review_assembly_03_tabs_recovered.png` | ears recovered under the lips | ear under lip on both sides, plate on both ledges | yes | yes — recovery arrows and the 2.0 mm engagement | A-A plane | yes | none | REVIEW_EVIDENCE |
| `review_operation_01_closed_latched.png` | closed and latched | tooth, keeper strip, 0.6 mm gap, finger through the slot | yes — pad, finger and tooth are one hatched region | yes — BLOCKED arrow along the opening direction | plan, same cut as the overview | yes | none | REVIEW_EVIDENCE |
| `review_operation_02_release_pressed.png` | released | tooth moved inboard, keeper strip standing clear | yes | yes — PUSH (+Y) arrow and NOW FREE arrow | plan | yes | none | REVIEW_EVIDENCE |
| `review_operation_03_slide_open.png` | mid travel | whole product, cover displaced, all four tab slots | yes | yes — SLIDE OPEN (−X) arrow | plan | yes | none | REVIEW_EVIDENCE |
| `review_operation_04_full_open_captive.png` | full open, 84 mm clear, still captive | cover at the open bound, aperture clear from 103 to 187, B-B located | yes | yes — the 84 mm span is drawn across the opening that exists | plan, B-B marked | yes | none | REVIEW_EVIDENCE |
| `review_operation_05_reclosed_and_latched.png` | reclosed | tooth back behind the keeper | yes | yes — SLIDE CLOSED (+X) arrow, ramp identified | plan | yes | none | REVIEW_EVIDENCE |
| `review_section_AA_captive_rail_closed.png` | all three rail functions in one cut | ledge, guide wall, lip, ear under lip, plate between lips — both rails | yes | yes — the three functions are numbered on the drawing | A-A, on the overview | yes | none | REVIEW_EVIDENCE |
| `review_section_BB_captive_rail_full_open.png` | the same capture at full open | identical relationship at the 84 mm bound | yes | yes — removal-direction arrow and the measured interference | B-B, on operation 04 | yes | none | REVIEW_EVIDENCE |
| `review_section_CC_assembly_snap.png` | compressed tab against the limiting gap | compressed ear, lip inner edge, deflection slot | yes | yes — compressed and recovered figures both given | C-C, on the overview | yes | none | REVIEW_EVIDENCE |
| `review_section_DD_latch_engaged.png` | the latch engagement, both halves in one plane | pad, finger, ramp, tooth, keeper strip, slot edge, free play | yes — one continuous hatched region from pad to tooth | yes — BLOCKED arrow | D-D, on the overview | yes | none | REVIEW_EVIDENCE |
| `review_section_DD_latch_released.png` | the same plane and scale, released | tooth inboard of the slot edge, keeper untouched | yes | yes — PUSH and NOW FREE TO SLIDE arrows | D-D | yes | none | REVIEW_EVIDENCE |

### Machine artifact contract

| Files | Purpose | Disposition |
|---|---|---|
| `closed_latch_engaged_*.png`, `closed_latch_released_*.png`, `opening_started_*.png`, `open_intermediate_*.png`, `open_84_*.png`, `closing_latch_leadin_*.png`, `closed_reengaged_*.png` (4 views each, 28 files) | per-state general views produced by step 9 of the validation chain | MACHINE_ONLY |

These are transparent wireframe renders with visible tessellation diagonals. They
are a record that the states build and render, nothing more. **They are not review
evidence, they are not linked in the human-review packet, and no claim rests on
them.**

## What the inspection actually caught

Two defects were found by looking, not by the checker, and both were fixed rather
than annotated around:

1. **The full-open view was cut where the aperture is not.** It was a longitudinal
   section through the near rail — which shows the lip and the ears, but contains
   no aperture at all, because the aperture is inboard of the rails. The "84 mm
   usable opening" arrow was floating over solid material. Looking at it also
   exposed a **real geometry defect**: the latch finger, then on the centreline,
   retracted *into* the declared 84 mm opening at full open. The latch was moved
   out over the near rail and the view was rebuilt as a plan, where the 84 mm
   exists to be drawn. Both the opening and the drawing are now honest.

2. **Several label boxes overlapped each other and one leader pointed at the wrong
   feature** — the ledge callout in A-A landed in the rail slot, and two leaders in
   D-D crossed. Repositioned.

Earlier iterations also produced a D-D plane that showed the finger but not the
tooth, because the tooth projects sideways. That plane was abandoned: the latch is
now drawn in the plane it actually works in.

## The question this file exists to answer

> **Can a reviewer understand assembly and operation from the PNG set without
> reading the source code?**

**YES.**

- *How is it assembled?* — `review_assembly_01_aligned.png` →
  `review_assembly_02_tabs_compressed.png` → `review_assembly_03_tabs_recovered.png`,
  with `review_section_CC_assembly_snap.png` giving the compressed-versus-recovered
  numbers against the actual limiting gap.
- *What retains it, and why can it not lift out at full open?* —
  `review_section_AA_captive_rail_closed.png` and
  `review_section_BB_captive_rail_full_open.png`, which are the same relationship at
  the two ends of the travel, plus `review_operation_04_full_open_captive.png`.
- *Where are the snap features?* — `review_overview_operation_and_sections.png`
  labels all five (four tabs, one latch finger); A-A and D-D show them cut.
- *What keeps it closed, where does the user press, and in which direction?* —
  `review_operation_01_closed_latched.png` and
  `review_section_DD_latch_engaged.png` for the engagement;
  `review_operation_02_release_pressed.png` and
  `review_section_DD_latch_released.png` for the release, with the direction drawn
  as a heavy **PUSH (+Y, inboard)** arrow.
- *Which way does the cover slide?* — heavy **COVER SLIDES OPEN (−X)** arrows on
  the overview and on `review_operation_03_slide_open.png`.
- *How does the latch re-engage?* — `review_operation_05_reclosed_and_latched.png`,
  which names the ramp and the corner it rides.

## What this audit is not

It is the author's own reading of the author's own drawings, which is the weakest
kind of review there is. It records that the images are legible and that they
depict the geometry that was actually measured. It does not establish that the
design is good, and no person has yet looked at any of these images.
