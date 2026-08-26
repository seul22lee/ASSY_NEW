# Reading the DeepSeek response as a mechanical design

Written **before** any translation, from `parsed_design_plan.json` with the
model's own dimension values resolved. Nothing in the design was changed.

## Does it describe recognizable manufactured bodies?

**Yes.** Both parts read as things a machinist would recognise.

- **BOD-0012 (housing)** — a 110 x 80 x 200 mm block with a 100 x 70 channel cut
  through it, two side slots, an opening at each end, and two stop lugs standing
  proud of the bore at x = -85 and x = +85. This is a housing, not a filled
  envelope: 5 of its 10 elements are subtractions.
- **BOD-0013 (drawer)** — a 98 x 68 x 160 body with a 96 x 66 x 140 storage
  hollow taken out of it, a front pull face, a rear panel, a bottom panel, two
  side panels and two guide ribs.

This is a real change from the previous production S05 output, which gave the
housing a single STOCK solid the size of its envelope.

## Does it contain a real opening / free volume where required?

**Partly.** `front_aperture` is an explicit 10 x 70 x 100 subtraction and is the
only element that names what it opens (`clears: FRG-0018`). `rear_opening`,
`channel_cut` and `storage_hollow` are further real voids. But the design names
only ONE of the branch's six FunctionalRegions; the other five are not
addressed, and `FRG-0013` (the ACCESS region the actor needs, at x = -2 units)
is not cleared by anything that says so.

## Does the moving body have a plausible path?

**Stated, but geometrically inconsistent.** The travel is right in magnitude:
the summary says "pulled out 100 mm (2 units)", which matches S04's
`JNT-0013: 0.0 -> 2.0` at the model's own 50 mm/unit.

The direction does not hold together. The joint is PRISMATIC along **+X**. The
summary says the channel runs along X, but the geometry does not: `channel_cut`
is 100 (X) x 70 (Y) x **200 (Z)** — its long axis is **Z**. The guide ribs, by
contrast, are 160 long in **X**. So the housing's bore is long in one direction
and the drawer's guides are long in another.

## Are corresponding mating / guide / restraint geometries actually present?

**Present and paired, and this is the strongest part of the design.** All four
declared interfaces are given a geometry pair:

| Interface | on BOD-0013 | on BOD-0012 | clearance |
|---|---|---|---|
| IFC-0016 | `upper_guide_rib` | `upper_slot` | `guide_clearance` |
| IFC-0017 | `lower_guide_rib` | `lower_slot` | `guide_clearance` |
| IFC-0018 | `rear_panel` | `rear_stop_lug` | 0 |
| IFC-0019 | `front_pull_face` | `front_stop_lug` | 0 |

**The two travel limits are different geometry in different places** —
`front_stop_lug` at x in [-90,-80] and `rear_stop_lug` at x in [80,90]. That is
precisely the defect the previous CND-0004 embodiment had, where the closed and
open limits sat at the same zero-offset datum.

Two real errors sit inside this otherwise sound scheme:

1. **Rib/slot mismatch.** `slot_width = rib_width + guide_clearance = 5.2 mm`,
   but the rib's extent *in the direction of the fit* is `rib_height = 8 mm`
   (rib y in [34,42], slot y in [35,40]). The rib is larger than the slot it
   must slide in. The two dimension names were crossed.
2. **No geometry is related to the joint or to the restraints.** Only the four
   Interfaces are covered; `JNT-0013` and `CRL-0108/0109/0110/0111` appear in no
   relationship.

## Is it one coherent assembly rather than unrelated duty-features?

**Yes as a scheme, no in the numbers.** Every element belongs to a single story -
a drawer running in a channel, guided by ribs in slots, stopped at each end,
reached through an aperture. Nothing looks like a feature emitted to satisfy a
checklist.

But the parts do not currently occupy compatible space, and both exceed their
S04 envelopes in Z: the housing spans z 0..200 against a bound of +/-100, and
the drawer spans z 20..180 against +/-75.

## Summary before translation

A markedly more designerly answer than the previous mode produced - real walls
and voids, paired mating geometry, and distinct stops at distinct positions -
carrying three concrete mechanical errors: an axis inconsistency between the
channel and the guides, a rib larger than its slot, and envelope overruns.
