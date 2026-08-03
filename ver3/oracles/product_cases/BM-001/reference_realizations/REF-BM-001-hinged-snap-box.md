# REF-BM-001-hinged-snap-box — one worked example, not a target

**Status:** reference realization (rank 4). Satisfies *part* of BM-001.
**It is not normative.** Nothing here may be asserted by a test.

## What it is

A prismatic two-part box: a base and a lid connected by a pin hinge along one
top edge, with a cantilever snap hook on the opposite edge engaging a lip on the
base. The lid swings up and back; a moulded abutment on the base limits the open
angle.

## Legacy sources

| Element | Path | Note |
|---|---|---|
| Hinge + stop kinematics | `V1/m0/out/stop/` | V-A and V-B ring, matched against `nostop/` |
| Hinge without stop (control) | `V1/m0/out/nostop/` | The negative half of the pair |
| Snap engagement | `V1/m23_latch_physics/`, `V1/tasks/snap_panel.json` | Force window is an *input*, not a measurement |

## Which invariants it demonstrates

`NRM-001` (two states, continuous motion) · `NRM-002` (pin realizes the joint on
both sides) · `NRM-003` (lid clears the aperture) · `NRM-004` (rigid) ·
`NRM-005` (abutment realizes the open limit) · `NRM-006`, `NRM-007` (snap holds
and releases, reusable) · `NRM-008` (hook reachable from outside).

## What it decided that the Oracle does NOT require

Written out explicitly, so a reader can see what was chosen *for* this example
rather than *by* the requirements:

- prismatic rectangular enclosure — free (`FRE-006`)
- pin hinge — free (`FRE-001`)
- cantilever snap — free (`FRE-002`)
- top-opening, hinge at the rear — free (`FRE-003`)
- rotation rather than translation — free (`FRE-004`)
- two-part decomposition — free (`FRE-005`)
- every dimension, material and process — free (`FRE-007`, `FRE-008`)

## What it does not demonstrate

Retention under any *quantified* handling or transport load (none exists —
`UNR-001`); release effort against any ceiling (`UNR-002`); manufacturability or
cost (`NV-003`); durability over cycles.

## Why it is not a target

A design that differs in every bullet of the "decided" list above — a curved
enclosure with a sliding cover and a magnetic catch — satisfies BM-001 equally.
Grading against this example would measure resemblance to a Ver1 card
combination, not synthesis.
