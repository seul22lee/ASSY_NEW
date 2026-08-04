# EXE-BM001-02 redesign status

**The redesign is geometrically complete and NOT yet validated clean.**
`validation/SUMMARY.json` reports `overall: FAIL`. Nothing here may be described
as a validated reference until that is resolved.

## What the redesign does

The quarter-turn cam is gone. `BODY-CAM` does not exist; the bodies are
`BODY-ENCLOSURE`, `BODY-COVER` and `BODY-PIN`. No part is handled separately by
the user in service.

| Human decision | How it is met |
|---|---|
| HCR-BM001-003 90/84 mm approved | travel 84 mm of a 90 mm aperture, unchanged |
| HCR-BM001-004 not removable at full open | pin lugs under the ledge block a 3 mm lift at 0/10/40/70/84 mm |
| HCR-BM001-005 no separate cam | cam removed; the pin is fitted once and snap-retained |
| HCR-BM001-006 no orientation-free cam | no cam; the latch has a defined engaged and released state |
| pin retention structure required | `BODY-PIN` running in `FEA-E-SLOT` |
| snap-fit solution | integral latch beam plus the pin's cantilever snap arms |
| pin axial retention via snap barb | two cantilever lugs recovering in the cover counterbore |

## Verified by measurement

- three bodies, all valid solids
- **zero** common volume in all three states and across all three motion segments
- terminal bounds are the slot ends, discriminating either side of 0 and 84 mm
- captivity: lift blocked at 0, 10, 40, 70 and 84 mm
- latch: blocks opening when engaged, frees it when released, re-engages on closing
- barb: relaxed lug span 7.600 into a 5.400 slot; compressed 5.233 fits; arms 2.8 apart against 2.6 of deflection; volume conserved exactly
- 8/8 negative controls detected, including one that catches a lug narrower than its slot

## What is NOT resolved

1. **`ASM-02` sweep fails** — 307 mm³ where the cover is lowered at the loading
   position. The loading concept is sound (the ear passes through the only lip
   relief, outside the operating range) but the swept path still meets material.
2. **Four measurement regions are wrong** — INT-04, INT-05, INT-11 select no
   geometry and INT-07 measures 3.9 mm against a declared 0.3. These are region
   definitions in `validate.py`, not defects in the geometry: the pin was
   inverted to a bottom-up snap rivet late in the session and the regions still
   describe the top-down arrangement.

Both are measurement-and-path work, not redesign work. The geometry itself
reports zero interference everywhere it has been swept.

## Why the pin is fitted from below

A top-down pin cannot work here. Its head would have to pass through the lips
the cover is already under, and the assembly sweep caught exactly that. Fitting
it upward through the cavity keeps every part of the pin out of the lip zone.

## Not claimed

Snap force, strain, release effort, retention capacity, fatigue, creep, wear,
cost, tolerance robustness and durability are all NOT_VERIFIED. Human review of
this redesign has not happened.
