# EXE-BM001-02 — review checklist

**Review status: `AUTHOR_SELF_REVIEW` — `HUMAN_REVIEW_PENDING`.**

No person has looked at these images. What follows is the author's own reading of
their own model, which is the weakest kind of review there is, and it is labelled
so that nobody mistakes it for independent approval.

Images are review aids. No geometric claim rests on one; every claim is backed by
a kernel measurement in `validation/`.

The enclosure is drawn at 30% opacity in every view, because the closure runs
*inside* its rails and an opaque enclosure hides it completely. That is a
rendering choice only.

## Author self-review

| # | Question | Author's reading | Image |
|---|---|---|---|
| 1 | Does the closed state actually cover the aperture? | Yes — the closure spans x 87–177 and the aperture is x 87–177. | `s_closed_retained_top.png` |
| 2 | Is the guidance real geometry, not an assumed constraint? | Yes — two ledges to run on, two depth faces, two overhanging lips, all measured at their declared 0.2 mm. | `section_rail_closed_*.png` |
| 3 | Are both terminal bounds visible as face pairs? | Yes — the two raised end walls. Neither is a number imposed on the model. | `section_cam_locked_front.png` |
| 4 | In the open state, is the aperture genuinely usable? | **Partly — and this is the design's weak point.** 84 of 90 mm is uncovered; the closure still covers 6 mm at the near end. | `s_open_top.png` |
| 5 | Does the cam visibly pass through both bodies? | Yes — knob above the closure, shaft through both bores, blade below the keeper. | `section_cam_locked_front.png` |
| 6 | Does the quarter turn visibly capture anything? | The blade is 12 mm across a 10.4 mm opening, so it lands on keeper material either side. Measured: a locked cam lifted 0.5 mm interferes by 4.03 mm³; an aligned cam lifts freely. | `section_cam_locked_iso.png` |
| 7 | Is anything floating or disconnected? | No. Each body is one connected solid; step 2 checked all three. | all |
| 8 | Anything that would obviously foul in use? | The withdrawn cam is a loose part with nowhere to live. Recorded as LIM-02. | `s_closed_released_iso.png` |

## What the author could not review

- Whether the design is *good*. It is admissible, which is much weaker.
- Cam holding torque, friction, wear, effort, cost, strength, disturbance
  capacity, durability — none of these is modelled.
- Whether 84 mm of a 90 mm aperture is acceptable usable access for a storage box.

## For the human reviewer

Please answer 1–8 yourself rather than reading the middle column, and in
particular:

1. **Question 4 is the one that matters.** The Oracle asks whether the closure
   obstructs *the access the design declares*, and this design declares the part
   it leaves open. That passed. Ask yourself whether it should have. If you think
   a design should not be able to pass by narrowing its own declaration, that is
   a finding about **NRM-BM-001-003**, not about this CAD, and belongs in
   `PRE_CAD_BACKLOG.yaml`. The evaluator already blocks the crudest version of
   that move by measuring that the declared region is one the closure actually
   covers when closed — but a reviewer may reasonably want a stronger rule.
2. **LIM-01** — the closure can be lifted out at full open. Judged admissible
   under NRM-BM-001-002's exclusion. Confirm or reject.
3. **LIM-03** — nothing holds the cam in the locked orientation. A detent would
   need friction or compliance, both excluded by the frozen selection. Confirm
   that recording it as NOT_VERIFIED is the right call rather than adding a
   feature this toolchain cannot evaluate.
4. Whether any interaction visible in the sections is missing from
   `interactions.yaml`. The per-state scan found no undeclared contact, but it
   works from the same declaration, so a human eye is the independent check.

Record the outcome here and change the status line at the top. Until then this
reference is `HUMAN_REVIEW_PENDING`, and no downstream artifact may describe it
as reviewed.
