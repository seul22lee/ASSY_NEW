# EXE-BM003-01 — Phase A report

Metric assembly and kinematic proxy for the BM-003 positive executable reference.
**Phase A is complete and frozen. No B-rep geometry existed when these numbers
were produced.**

## Why Phase A exists

The expensive way to discover that a mechanism does not work is to model it in
solid geometry first. Every body here is a set of capsules and Z-aligned
cylinders, every clearance is an analytic distance, and the whole
assembly-plus-cycle runs in seconds — so a mistake costs a rerun rather than a
rebuild.

The proxy is deliberately conservative where it is approximate: a capsule bulges
where a real prism does not. Phase A can therefore reject a design that Phase B
would have accepted, and cannot accept one Phase B would reject.

**One correction was needed during Phase A**, and it is worth recording because
the failure was silent-looking. Capsules are swept *spheres*, so two coaxial
discs 18.5 mm apart on the same axis — each of radius 15 — reported an 11.5 mm
*overlap*. Every configuration failed identically, which is what gave it away: a
real interference varies with the motion. Z-aligned cylinders now get exact
finite-cylinder distance, and rod-like parts keep capsule treatment.

## Fixture principle

Commissioned, not chosen here: three hinged legs on a central hub, held deployed
by a **captive annular ring** whose three arms geometrically block the leg heels
from rising. Release is a deliberate **lift-and-rotate**.

Declared state-maintenance class: **KINEMATIC_BLOCK**.

## Result

| | |
|---|---|
| Acceptance checks | **16 / 16 PASS** |
| Negative controls | **15 / 15 detected** |
| Bodies | 15 |
| Assembly steps | 15, dependency graph acyclic |
| Trajectory samples | 559 across 5 transitions, interior sampled throughout |

### Signatures

```
phase_a_geometry_signature_sha256  0c05f1a354ec53f1...
topology_signature_sha256          38fe3f2ef8787ad8...
evidence_signature_sha256          d5fcce85ee15d678...
```

Verified identical on a clean rerun.

## Key measurements

| Measurement | Value |
|---|---|
| Deployed footprint area (three feet) | 9832.42 mm² — non-degenerate |
| Fold-back arrest when locked, all three legs | θ = 27.92° (2.08° free travel from 30°) |
| Heel-to-arm clearance after release, all three legs | 18.41 mm — fully clear |
| Ring axial travel, locked → released | 9.5 mm |
| Minimum insertion-path clearance | 0.110 mm |
| Minimum clearance over the full cycle | 0.110 mm |
| Stored radial envelope | 92.36 mm |
| Deployed radial envelope | 162.69 mm |
| Radial reduction on folding | **70.33 mm** |

Designed contacts are excluded from the clearance figure and named explicitly:
the ring seating on its lower shoulder, the ring meeting its upper travel stop at
a nominal 0.0 mm, the hinge pin in its clevis, and the leg root inside the boss.
Counting a designed seat as a collision would bury the leg-to-leg case that
matters.

## What blocks the fold, geometrically

Each leg carries a **heel** above its hinge, leaning outward by 40°. Folding back
from the deployed angle *raises* the heel tip. The ring's three arms sit directly
above the heels in the locked position, so the heel cannot rise and the leg
cannot fold — arrested after 2.08°.

Release lifts the ring 9.5 mm to its captor stop, rotates it 60° so the arms sit
in the gaps between stations, and lowers it again. The heels are then free
through the whole fold, with 18.41 mm to spare.

**Nothing here depends on friction, preload or a spring.** The block is geometry
in contact, which is why the declared class is KINEMATIC_BLOCK and why Phase A
can establish it at all.

## Negative controls

All fifteen fail their intended check, and each records what else failed so a
control cannot pass by breaking something unrelated.

| Control | Target check |
|---|---|
| NC-A01 remove a hinge retainer | hinge retention |
| NC-A02 omit a leg | three legs |
| NC-A03 heel too short to reach the arm | locked blocking |
| NC-A04 blocker engages only two legs | locked blocking |
| NC-A05 ring not captive | ring captivity |
| NC-A06 final retainer bore too small | final retainer installable |
| NC-A07 hinge-pin access closed early | insertion paths |
| NC-A08 assembly dependency cycle | acyclicity |
| NC-A09 endpoints kept, trajectory deleted | trajectories |
| NC-A10 intermediate leg-leg collision | forbidden overlap |
| NC-A11 intermediate leg-hub collision | forbidden overlap |
| NC-A12 blocker still engaged after release | release clears |
| NC-A13 reverse folding possible when locked | locked blocking |
| NC-A14 stored envelope not reduced | compactness |
| NC-A15 transform jumps between samples | teleportation |

**NC-A06 initially failed to detect**, and the reason is instructive: it shrank
the plate's *outer* radius, which the proxy models, while the defect it meant to
express was a *bore* too small to pass the spigot — which the proxy did not model
at all. A body that cannot reach the scene never collides with anything, so no
swept-collision check could ever have seen it. A bore-feasibility precondition
was added.

## Not established by Phase A

Load capacity, stress, stiffness, buckling · fatigue, wear, lifetime ·
tolerance-induced looseness — every clearance here is **nominal** · contact
pressure, friction behaviour · impact resistance · manufacturing-process
feasibility.
