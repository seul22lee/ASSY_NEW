# EXE-BM001-01 — review checklist

**Review status: `AUTHOR_SELF_REVIEW` — `HUMAN_REVIEW_PENDING`.**

No person has looked at these images. What follows is the author's own reading of
their own model, which is the weakest kind of review there is, and it is recorded
as such so that nobody mistakes it for independent approval.

Images are review aids. No geometric claim in this pilot rests on one; every claim
is backed by a kernel measurement in `validation/`.

## Author self-review

| # | Question | Author's reading | Image |
|---|---|---|---|
| 1 | Does the closed state look closed — plate seated, cavity covered? | Yes. The plate spans the full width and seats on the rim; the cavity is covered to `plate_rear_y` = 79, and the cavity ends at 77. | `s_closed_retained_*.png` |
| 2 | Is the rotation axis where the model says it is? | Yes. The knuckle set sits behind the rear face, tangent to it, at z = 50. | `section_knuckle_closed_*.png` |
| 3 | Do the knuckle segments interleave, five of them, alternating? | Yes — three on the enclosure including both outermost, two on the closure. | `s_closed_retained_top.png` |
| 4 | In the open state, is the aperture actually clear? | Yes. All closure material is behind y = 80 at 110°; measured clearance to the declared access region is 3.0 mm. | `s_open_side.png` |
| 5 | Is the terminal condition visible as a face landing on a face, not a corner? | Yes — the stop block's face lies flat on the rear wall over a 6 mm band. | `s_open_side.png` |
| 6 | Does the retention bolt visibly pass from the closure into the enclosure? | Yes, 8 mm below the rim. | `section_retention_closed_*.png` |
| 7 | Does the released bolt visibly clear the enclosure? | Yes; the shaft end sits 2 mm above the rim and still spans 12 mm of the guide. | `section_retention_released_*.png` |
| 8 | Is anything visibly floating, unsupported or disconnected? | No. Each body is one connected solid (step 2 checked this, four for four). | all |
| 9 | Does anything look like it would obviously foul in use? | The stop arm protrudes about 18 mm behind the enclosure at the closed state. That is intended and is the price of a 110° stop on this geometry, but it is the feature a reviewer is most likely to object to. | `s_closed_retained_side.png` |

## What the author could not review

- Whether the design is *good*. It is admissible; that is a much weaker claim.
- Anything about forces, materials, wear or manufacture.
- Whether a reviewer would consider the rear protrusion acceptable for a desktop
  product. The source states no envelope (UNR-BM-001-003), so nothing in the
  Oracle rejects it — which is exactly the sort of thing worth a human opinion.

## For the human reviewer

Please look at questions 1–9 yourself rather than reading the middle column, and
in particular:

1. **Question 9** — is the rear protrusion acceptable, or is this design being
   admitted by an Oracle that is silent where it should not be? If the latter,
   that is a finding about the Oracle, not about the CAD, and belongs in
   `PRE_CAD_BACKLOG.yaml`.
2. **`manifest.yaml` LIM-01** — the pin is retained axially in one direction
   only. Judged a permitted design freedom. Confirm or reject.
3. Whether any interaction visible in the sections is missing from
   `interactions.yaml`. The per-state pair scan found no undeclared contact, but
   it works from the same declaration, so a human eye is the independent check.

Record the outcome here and change the status line at the top. Until then this
reference is `HUMAN_REVIEW_PENDING`, and no downstream artifact may describe it
as reviewed.
