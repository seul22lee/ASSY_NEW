# EXE-BM001-02 — how it works, in plain mechanical terms

Two bodies and nothing else:

| | |
|---|---|
| `BODY-ENCLOSURE` | `GENERIC_RIGID_POLYMER` — cavity, top panel, two captive rails, latch keeper |
| `BODY-COVER` | `GENERIC_COMPLIANT_POLYMER` — plate, four retention tabs, one latch finger |

There is no third part. Nothing is fastened, riveted, pinned, clipped or cammed.

---

## The rail is the whole retention story

Each side of the enclosure carries a C-section rail. Read it from the outside in:

```
   z
   |    +-------+        retaining lip: solid, z 45.4 – 48.4, reaching
   |    |///////|        2.2 mm inboard from the guide wall
   |    |///+---+ - - -   lip inner edge, y = 5.2
   |    |///|
   |    |///|             guide wall: inner face at y = 3.0
   |    |///|
   |    +---+-----------+ ledge top, z = 40.0 — the cover sits here
   |        |///////////|
   +--------+-----------+---- y
        0   3    5.2   13
```

Three jobs, one rail:

1. **support** — the ledge top face carries the cover (`INT-01`, `INT-02`)
2. **guidance** — the guide wall locates it sideways, 0.2 mm on the tab tips (`INT-03`, `INT-04`)
3. **anti-lift** — the lip overhangs the tabs, so the cover cannot rise (`INT-05`, `INT-06`)

Nothing else in the design performs any of these. Delete the lip and the cover
lifts straight off — which is exactly what control `CTL-01` injects and the
checker reports.

## Why the cover cannot lift out

The cover plate is 59.0 mm wide and sits **between** the two lip inner edges,
which are 59.6 mm apart. Four integral tabs project outward from its edges, past
the lip inner edges, into the rail channels. Each tab ear reaches from y = 3.2
(0.2 mm off the guide wall) to y = 5.5, so **2.0 mm of each ear lies directly
under a lip**.

Lift the cover and the four ear top faces meet the four lip undersides. Measured:
0.4 mm of free vertical play, then 124.8 mm³ of solid interference at a 3 mm lift
— at 0, 10, 40, 70 and 84 mm of travel alike, because the lips run the entire rail
length and have no break anywhere.

Two tabs a side, 52 mm apart, so the cover cannot be rocked out either: a 1.5°
pitch or roll with a 1.5 mm lift is blocked at every sampled position.

**What this does not say:** nothing here is a force. Whether the tabs *withstand*
a pull is `NOT_VERIFIED`.

## How the cover is installed

One straight press, at the closed position, using only the two bodies.

1. Hold the cover square above the closed position.
2. **Deflect all four retention tabs 2.2 mm inboard.** Each tab is a 20 mm
   cantilever beam cut free from the plate by a 2.4 mm slot, rooted at its +X
   end. The slot is wider than the deflection, so the beam has somewhere to go.
3. The cover now spans 59.2 mm across the 59.6 mm gap between the lip inner
   edges — 0.2 mm clear each side. **Lower it straight down.** The plate, the
   tabs and the latch finger all pass without touching anything; the swept common
   volume is 0.000 mm³.
4. The plate seats on the two ledges.
5. **Let the tabs go.** Each ear springs outward under its lip.
6. The cover is captive — here, and at every other position of its travel.

The deflected state is a *declared compliant configuration*: a rigid inboard
translation of the tab region. It conserves volume exactly (0.000 mm³ difference)
and tests geometric passage. It is not a deformation simulation and predicts
nothing about strain.

**What is not required:** threading the cover along a channel closed at both
ends; a loading position outside the 0–84 mm travel; a relief cut in either lip;
rigid penetration; a separate fastener; destructive assembly.

**Service removal** is declared and non-destructive: deflect the four tabs
inboard again and lift the cover out at the closed position. That needs
simultaneous access to all four tabs through the rail channels — a deliberate
service action, not an ordinary upward pull. The captivity checks measure the
ordinary pull.

## What prevents opening while closed

The cover carries a second integral snap: a **latch finger** at its +X end,
reaching out through an open-topped slot in the far end wall to the outside.

It sits **over the near rail**, at y = 6–12, not on the centreline. That is not
cosmetic. A finger on the centreline retracts *into the aperture* at full open
and stands in the way of the 84 mm the design promises. Out over the rail it
retracts over the ledge instead, and the declared opening stays genuinely clear —
measured as 0.000 mm³ of cover in the usable region, both in the aperture band and
in the prism above it.

The finger carries a **tooth**: a lug projecting 2.6 mm *outboard*, standing
behind the strip of end wall left beside the slot. 0.4 mm of that projection is
slot clearance, so **2.2 mm of tooth stands behind solid wall**.

- **Closed:** the tooth's blocking face is 0.6 mm behind the wall's outer face.
  Push the cover open and it moves 0.6 mm, then meets the wall. Measured onset:
  0.62 mm. That free play is reported, not rounded away.
- **Blocking direction:** −X, the rail travel direction, which is the opening
  direction.

## Where the user presses, and what happens

- **Press on:** `FEA-C-RELEASE-PAD` — 11 mm of the finger standing outside the
  product's end face, clear of everything.
- **Direction:** **+Y, inboard** (push it sideways, toward the middle of the box).
- **Distance:** 2.6 mm — more than the 2.2 mm engagement, so the tooth fully
  clears the keeper strip.
- **Then:** the tooth is inboard of the slot edge and passes straight through the
  slot with the rest of the finger. **Slide the cover −X.**

Read as a sequence:

> **PUSH THE PAD SIDEWAYS → THE TOOTH CLEARS THE KEEPER → SLIDE THE COVER OPEN**

The finger must be held deflected for the first 8.0 mm of travel, until the tooth
is past the end wall. After that it springs back on its own and the cover runs
free to the 84 mm bound.

## How the latch re-engages on closing

Nothing to do. Push the cover shut:

1. The tooth's sloped face — `FEA-C-LATCH-RAMP` — meets the corner of the keeper
   strip.
2. Continuing to push drives the ramp against that corner, which deflects the
   finger inboard. The user supplies no separate action.
3. The tooth passes through the slot.
4. Past the keeper the finger springs back and the tooth drops behind the wall.
5. Opening is blocked again.

Measured: the closing sweep ends seated (0.000 mm³) and blocking again (a 1.5 mm
opening attempt from that configuration meets 9.88 mm³ of solid). No orientation
has to be found and no detent has to be felt.

## Terminal bounds

- **Closed** — the cover's +X face lands flat on the far wall's inner face
  (`FEA-E-STOP-CLOSED`).
- **Open** — the cover's −X face lands flat on the solid rail fill at x = 13
  (`FEA-E-STOP-OPEN`). This is a **stop**, not a relief: there is no gap in
  either lip anywhere along the rails, so there is no position at which the cover
  could be lifted through.

Free everywhere inside 0–84 mm; interference 1 mm outside each end.

---

## Historical note (the only one in this directory)

Two earlier topologies for this reference were rejected: a quarter-turn cam
retainer (rejected by HCR-BM001-005 and -006), and, after that, a separate snap
rivet pressed through cover and enclosure with a keeper bridge across the top of
the product. The rivet was a fastener compensating for rails that had no
overhang — a third body doing the rail's job. Both are gone from the geometry and
from every product file; git history holds them. Nothing in the current design
descends from either.

## What none of this establishes

Snap insertion force, retention strength, release effort, material strain, root
stress, creep, fatigue, repeated-cycle life, wear, tolerance capability, moulding
feasibility and cost are all **`NOT_VERIFIED`**. No force is computed anywhere in
this reference, and none should be inferred from any number in it.

The maximum claim is: **geometrically and kinematically admissible at the
evaluated fidelity.**
