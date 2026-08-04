# EXE-BM001-02 — review checklist

**Review status: `AUTHOR_SELF_REVIEW` — `HUMAN_REVIEW_PENDING`.**

No person has looked at these images. What follows is the author's own reading of
their own model, which is the weakest kind of review there is, and it is recorded
as such so that nobody mistakes it for independent approval.

Images are review aids. No geometric claim in this pilot rests on one; every claim
is backed by a kernel measurement in `validation/`.

This is the third topology for this reference. The first two are recorded in
`expected_evaluation.yaml#version_history` and their artifacts have been deleted
rather than left lying about, so nothing in this directory describes a design that
no longer exists.

## Concept in one line

A cover that slides on two ledges between guide walls, held down for its whole
life by a single snap rivet running in a slot, and held shut by a compliant latch
cut from the cover itself. There is no cam, no separate part to handle, and no
position at which the cover comes off.

## Author self-review

| # | Question | Author's reading | Image |
|---|---|---|---|
| 1 | Is the cover carried and located by something, or is it floating? | Carried on two ledges at z = 40, located by two guide walls with 0.2 mm running clearance each side. Nothing overhangs it. | `review_section_cover_support_and_guides.png` |
| 2 | At full open, what actually stops the cover being lifted off? | The rivet's recovered lugs, standing under the ledge underside at z = 34. A 3 mm lift is blocked by 14.222 mm³ of interference at 0, 10, 40, 70 and 84 mm — every position, not just the convenient ones. | `review_section_captive_at_full_open.png` |
| 3 | Can the rivet itself be pulled back out? | Not geometrically. Its recovered lugs span 7.6 mm across the 5.4 mm slot they came through, a 1.1 mm shoulder each side. Whether they *withstand* a pull is NOT_VERIFIED. | `review_section_rivet_and_slot.png` |
| 4 | Are the travel bounds a realized condition or a declared number? | Realized. The slot is exactly travel + slot width long, so its ends are the two bounds; pushing 1 mm past either end produces 0.61 mm³ of interference and 0.0 inside. | `review_section_rivet_and_slot.png`, `validation/motion_report.json` |
| 5 | Does the latch actually hold the cover shut? | It blocks opening from 1.05 mm onward. The first millimetre is free play: the hook stands 1.0 mm clear of the keeper by declared running clearance, so the cover shifts before it bites. Sampled at 0.05 mm around that gap rather than on a coarse ladder, because a coarse ladder reports its first blocking sample as the onset and overstates it. Reported as measured, not rounded to zero. | `review_section_latch_engaged.png` |
| 6 | Does releasing it genuinely free the cover? | Yes — with the beam deflected 2.6 mm the hook passes under the keeper and common volume is 0.000 mm³ over the whole 6 mm test sweep. | `review_section_latch_released.png` |
| 7 | Is the release feature reachable without handling a separate part? | Yes. It is the latch beam's own top face, lying under the open aperture at the closed position. This is what HCR-BM001-005 asked for. | `review_overview_section_lines.png` |
| 8 | Can the thing actually be built? | Two straight downward presses, both at the closed position, both sweeping 0.000 mm³. Nothing is threaded past anything. | `assembly.yaml`, `validation/assembly_report.json` |
| 9 | Is anything visibly floating, unsupported or disconnected? | No. Each body is one connected solid (step 2 checked this, three for three). The keeper bridge appears free in section C-C because it spans the guide walls out of that plane; the section is annotated to say so. | all |
| 10 | Does anything look like it would obviously foul in use? | The keeper bridge stands 2.5 mm above the cover across the full width at x = 93–96. It is deliberate — it is what the latch catches — but it is a permanent obstruction over the closed cover and is the feature a reviewer is most likely to object to. | `review_section_latch_engaged.png` |

## What the author could not review

- Whether the design is *good*. It is admissible; that is a much weaker claim.
- Anything about snap-in force, pull-out capacity, release effort, strain, creep,
  fatigue or cycle life. All NOT_VERIFIED.
- Whether 84 of the 90 mm aperture is enough usable access for a storage box.
  HCR-BM001-003 approved it, but that decision is reversible.
- Whether the rivet being permanent — the cover cannot be removed without
  destroying it — is acceptable, or a defect dressed as captivity.

## For the human reviewer

Please look at questions 1–10 yourself rather than reading the middle column, and
in particular:

1. **Question 10** — is the keeper bridge acceptable, or does it defeat the point
   of a flush sliding cover? If it does, this is a finding about this design.
2. **Question 5** — 2.0 mm of free play before the latch bites. Is that a latch or
   a rattle? The number is honest; the judgement is not the author's to make.
3. **The permanence of the rivet.** `assembly.yaml#disassembly` states plainly
   that the cover cannot be removed without destroying the rivet. That is the
   price of captivity at full open. Confirm or reject.
4. Whether any interaction visible in the sections is missing from
   `interactions.yaml`. The per-state pair scan found no undeclared contact, but
   it works from the same declaration, so a human eye is the independent check.

Record the outcome here and change the status line at the top. Until then this
reference is `HUMAN_REVIEW_PENDING`, and no downstream artifact may describe it
as reviewed.
