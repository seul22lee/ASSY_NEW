# EXE-BM002-01 — design and operation rationale

**Phase A: actual CAD and core geometric / kinematic validation.**
Maximum claim: **GEOMETRICALLY AND KINEMATICALLY ADMISSIBLE AT THE EVALUATED CAD
FIDELITY.** Nothing here is a claim about strength, effort, jamming, safety,
holding, manufacturability or life.

All dimensions in millimetres. Every number quoted below was measured from the
built B-rep solids by `validate.py`; none is asserted.

---

## 1. What the machine is

An enclosed hand-cranked platform lift built as an **in-line slider-crank**. The
user turns an exterior crank; the crank arm inside the housing drives a
fixed-length connecting rod; the rod drives a platform that is constrained to a
vertical line by two guide channels. A crank of radius `R` driving a slider on a
line through its own axis moves that slider by exactly `2R` between the two dead
centres, so `R = 45.000` gives `90.000` of travel — inside the source's
*approximately 80–100 mm* band, and 10 mm clear of both edges.

Seven product bodies, one scenario object:

| body | what it does |
|---|---|
| `BODY-HOUSING` | base, walls, cavity, open top, **both** crank-shaft journal lands, both guide channels, support-surface reaction |
| `BODY-REAR-PANEL` | closes the +X side after internal assembly; carries the integral lands that retain both joint pins |
| `BODY-PLATFORM` | support plate, two guide followers, clevis |
| `BODY-CRANK-SHAFT` | exterior handle, boundary-crossing hub, thrust collar, crank arm |
| `BODY-CONNECTING-ROD` | fixed 85.000 link |
| `BODY-CRANK-JOINT-PIN` | crank arm ↔ rod revolute joint |
| `BODY-PLATFORM-JOINT-PIN` | rod ↔ platform clevis revolute joint |
| `SCENARIO-PAYLOAD-1KG` | **not a product body**; a 36 × 60 × 40 envelope declared at 1 kg |

Produced envelope: **125 × 140 × 224** (x −46 → 79, y 0 → 140, z 0 → 224).
Geometry signature: `6824e5102424e3db883f16b684ab54f02c14eed19bead0116c704092156bc2ee`.

---

## 2. How the drive reaches the mechanism

### 2.1 External crank → crank shaft

The handle grip is a Ø12 pin standing **26.000 off the shaft axis**, spanning
x −46 → −18, entirely outside the housing. It is not a separate part: it is
material of the same single connected solid as the hub. Measured, at θ = 0 the
grip centre is at (y 70.000, z 34.000); at θ = 90 it is at (y 96.000, z 60.000).
It orbits, so it is a crank and not a knob.

### 2.2 Crossing the housing boundary

The hub is Ø70.000 and runs in a Ø70.400 bore through the −X wall, x 0 → 8.
Measured crank-shaft material: **72 438.8 mm³ outside** the housing,
**30 787.6 mm³ inside the wall band**, **100 579.2 mm³ inside** the housing — one
solid passing through one aperture.

The unusual choice here is that the **hub diameter is the journal diameter**. That
is what makes the product assemblable at all. The crank shaft has to be inserted
from the open +X side, because the only other direction would require the crank
arm (radius 54.000) to pass a 35.200-radius bore. Inserting from +X means the
handle end must pass through the whole bore, so the handle envelope has to fit
inside the journal. A Ø70 hub with a grip at radius 26 (envelope radius 32.0)
does; a small shaft with a big crank does not. See §7.

### 2.3 Radial support: two journal lands, not one bore

| land | x | measured clearance | nominal |
|---|---|---|---|
| `FEATURE-HOUSING-JOURNAL-1` (also the crossing) | 0 → 8 | **0.2000** | 0.2 |
| relief between them | 8 → 14 | **3.2000** | 3.2 |
| `FEATURE-HOUSING-JOURNAL-2` | 14 → 26 | **0.2000** | 0.2 |

The relief exists for one reason: without it the two lands would be one 26 mm
bore, and "two journals" would be a description rather than a fact. Measuring
3.2000 in the middle and 0.2000 at each end is what makes them two. Axial
separation 6.000.

`NRM-BM-002-002` does not require the housing to be the support (SF-5.2), and
`FRE-BM-002-011` leaves the location free. Here the housing happens to be the
support, and the crossing happens to be one of the lands. That is a choice, not
an obligation discharged.

### 2.4 Axial location of the shaft

Measured free travel of the crank shaft along its own axis: **1.031 in −X**,
stopped by `BODY-HOUSING` (the thrust collar meeting the journal-boss end face),
and **2.031 in +X**, stopped by `BODY-CONNECTING-ROD` (the crank arm meeting the
rod, which is itself stopped by the pin head against the rear-panel land).

This is recorded as a **handling design choice, not as a discharge of
NRM-BM-002-006.** The whole mechanism lies in the YZ plane and every joint axis is
parallel to X, so no axial force is produced in the declared scenario. Demanding a
thrust feature where no axial load exists is exactly the error corrected at SF-5.3
and rejected by `NEG-BM-002-019`. The collar is there so that pulling the handle
does not pull the crank out, which is a use case, not a load case.

---

## 3. How the crank arm drives the rod

The crank arm spans x 30 → 40 and runs from radius 14.000 at the shaft axis to a
9.000-radius boss centred 45.000 from it — outer radius 54.000.

`BODY-CRANK-JOINT-PIN` is a Ø10.000 shank through the arm bore (Ø10.200) and the
rod's crank bore (Ø10.200), with a Ø17.000 head. Measured at **all nine states**:

* pin in the crank arm bore — min distance **0.100000** every state, common volume 0;
* pin in the rod's crank bore — min distance **0.100000** every state, common volume 0.

Both regions of interest **follow the joint axis**, recomputed from the pin
solid's own bounding box at each state, so the measurement is of the joint
wherever the joint happens to be — not of a fixed box that the joint has orbited
out of.

### Axial retention of the crank pin

Measured free travel: **0.000 in −X**, blocked by `BODY-CONNECTING-ROD`, and
**2.031 in +X**, blocked by `BODY-REAR-PANEL`. The head seats on the rod's +X face
one way; the panel's annular land — inner radius 36.000, outer radius 54.000 about
the crank axis — faces the head the other way. The pin head orbits at radius 45.000
and the land is an annulus, so the stop is present **at every crank angle**, not
just at one.

The retention criterion is deliberately two-part: the travel must be small
*and* the body that stops it must be the declared retention body. A pin that is
eventually stopped by some unrelated boss it happens to run into is not retained.
Negative control NC-07 removes the head; the pin is then still stopped, at 4 mm,
by the housing journal boss — and the control is detected precisely because the
blocker is wrong.

---

## 4. How the rod drives the platform, and why the platform goes straight up

### 4.1 The link

`BODY-CONNECTING-ROD` is a stadium with two Ø10.200 bores. Two independent
measurements of its centre distance:

* the rod solid's own extent minus its two eye radii: **85.000000**;
* the distance between the two pin bodies' axes, in every one of the nine states:
  **85.000000**, maximum deviation **0.000000000**.

The second measurement is the one that matters: it is taken from the pins, not
from the rod, so a rod that changed length would show up as the pins no longer
being 85 apart *and* as a clearance that is no longer 0.1. Negative control NC-09
lengthens the rod by 2.0 and both detections fire.

### 4.2 Why the platform does not follow the rod sideways

The rod is not vertical except at the dead centres. Its maximum angle from
vertical is **31.9657°** at the quarter positions, where the crank pin is
45.000 off the centre line. So the rod pushes the platform sideways as well as up.

That lateral component goes into the **guide channels**, and nowhere else. The
platform carries two followers, 26.000 wide × 5.600 deep × 16.000 tall, one on
each Y face, running in channels cut into bosses on the front and back inner
walls:

| clearance | value |
|---|---|
| follower side face to channel side wall | **0.200** each side |
| follower tip to channel floor | **0.400** |
| plate edge to guide-boss inner face | **0.400** |

Measured over **37 samples through the full cycle**: follower material inside each
channel **2329.600 mm³ at every sample**, both sides; platform material past
either channel floor **0.000000 mm³ at every sample**; follower z-extent inside
the channel's z range at every sample. The channel walls carry 14 508.0 mm³ of
housing material each, so there is something there to push against.

The follower z-extent is measured from the **follower**, clipped to the channel
footprint — not from the platform's bounding box, which reaches 29 mm lower
because the clevis hangs there. Using the whole-body box was a real defect in the
first version of this validator (§9, DEF-03).

### 4.3 Why the platform stays square

`NRM-BM-002-007` requires orientation to be constrained **where the scenario
requires it**, and `FRE-BM-002-003` leaves anti-rotation free otherwise. Here the
scenario does require it: a flat plate has to stay flat to accept a payload
through a top aperture. `ADM-BM-002-E`'s rotationally symmetric platform is still
admissible in the pack; this design simply is not that design.

Geometric capture is probed by rigidly rotating the platform solid about its own
centroid and measuring the boolean common with the housing, at BOTTOM,
MID-STROKE and TOP:

| probe | angle | overlap with housing |
|---|---|---|
| pitch about X | ±4.0° | **154.372 mm³** |
| roll about Y | +4.0° / −4.0° | **99.705 / 130.335 mm³** |
| yaw about Z | ±0.5° | **55.660 mm³** |

Every probe is obstructed. **This establishes geometric capture and nothing
else.** It says nothing about stiffness, friction, wear, life or behaviour under
load: finding material in the way does not say how hard it is to push past it.

---

## 5. The platform joint

`BODY-PLATFORM-JOINT-PIN`, Ø10.000, passes through clevis lug A (x 35 → 41), the
rod's platform bore (x 42 → 54) and clevis lug B (x 55 → 61). Measured at all nine
states, min distance **0.100000** in each of the three bores, common volume 0.

Two lugs straddling the rod, rather than one lug beside it, is what stops this
joint being a cantilever — the rod force is reacted on both sides of its own line
of action.

Axial retention: **0.000 in −X** blocked by `BODY-PLATFORM` (head on lug B's +X
face), **2.031 in +X** blocked by `BODY-REAR-PANEL` (the vertical land, y 61 → 79,
z 94 → 200, which spans the pin's entire travel so the stop exists at every
platform height).

---

## 6. The rear panel

Three real jobs, all of which have to be done by something:

1. **It closes the +X side.** Everything is assembled through that opening; without
   it there is no fourth wall. Measured seated contact with the housing's +X end
   faces: min distance 0.000.
2. **It retains the crank joint pin.** Annular land, r 36 → 54, standing to x = 67.
3. **It retains the platform joint pin.** Vertical land, y 61 → 79, z 94 → 200,
   standing to x = 67.

Both lands come into position **in the same −X motion that seats the panel**. Before
that motion both pins can be pushed out; after it neither can. That is why the
panel is the last body installed and why the pins are installed before it.

What the rear panel does **not** do is carry a crank-shaft journal. It was
supposed to. See CHG-02.

---

## 7. Assembly

| step | body | direction | why |
|---|---|---|---|
| AS-01 | housing | — | base |
| AS-02 | crank shaft | −X | hub passes through both lands; handle emerges outside |
| AS-03 | connecting rod | −Z | dropped into the 2 mm gap beside the crank arm |
| AS-04 | crank joint pin | −X | through the rod bore into the arm bore |
| AS-05 | platform | −Z | followers enter the channels; lugs come down either side of the rod |
| AS-06 | platform joint pin | −X | through lug B, the rod, lug A |
| AS-07 | crank shaft | operation | cycle with the +X side open |
| AS-08 | rear panel | −X | closes the side and places both retention lands |
| AS-09 | crank shaft | operation | cycle closed |

Measured maximum common volume with already-placed material over every swept
insertion: **0.000000 mm³**.

Two directions are forced rather than chosen. The **crank shaft** must go in from
+X (§2.2). The **connecting rod** and the **platform** must come down from above,
because an axial approach would have to drive the rod's crank eye through the
crank arm's pin boss, which occupies exactly the same place — the rod's x band,
42 → 54, is chosen to sit clear of the arm's, 30 → 40, so that a vertical descent
touches nothing.

There is **no loose retainer anywhere in this product**: no circlip, no washer, no
screw, no separate cover. Both pins are retained by geometry that already had
another job. Nothing was added to make assembly or validation easier.

Insertion force, tooling and ease of assembly are **NOT_VERIFIED** (UNR-BM-002-008).
This design has no press fit, snap fit or interference fit at all, so it does not
even imply a process parameter.

---

## 8. Payload access and the load path

The housing top is fully open at the rim, z = 224.000. The declared
`SCENARIO-PAYLOAD-1KG` envelope, 36 × 60 × 40, is swept down the aperture onto the
support surface at both extremes:

| state | support surface | clear height to rim | overlap during descent | seated distance to platform |
|---|---|---|---|---|
| TOP | **216.000** | 8.000 | **0.000000 mm³** | **0.000000** |
| BOTTOM | **126.000** | 98.000 | **0.000000 mm³** | **0.000000** |

The path **terminates on `FEATURE-PLATFORM-SUPPORT-SURFACE`, not on the housing
rim.** Accepting the rim as the endpoint is `NEG-BM-002-007` / `INA-BM-002-G`, and
is negative control NC-14: the rim stands 8.000 above the support surface at TOP
and 98.000 above it at BOTTOM, so the two are never the same measurement.

The support surface is measured by clipping the platform to the payload footprint,
because the platform's bounding-box top is a guide follower standing 4 mm proud of
the plate. Reporting 130.000 instead of 126.000 would have been a 4 mm error in
the height, though not in the travel.

Qualitative load path, every edge tied to a measured interaction:

```
SCENARIO-PAYLOAD-1KG → BODY-PLATFORM → BODY-PLATFORM-JOINT-PIN
                                      ↘ BODY-HOUSING (guides: lateral and moment only)
   → BODY-CONNECTING-ROD → BODY-CRANK-JOINT-PIN → BODY-CRANK-SHAFT
   → BODY-HOUSING (journals 1 and 2) → support surface at z = 0
```

Existence of this path is structural and is established. **Its adequacy is
NOT_VERIFIED.** `DOS-BM-002` S5 records no strength evidence at any fidelity, so
REQ-003 resolves to **UNSUPPORTED** under `stage_expectations` s11 — an evidence
state, not a product verdict.

---

## 9. Changes to the frozen starting concept

Three changes. Each is recorded with the contradiction that forced it, the
minimum change made, and the resulting measured travel.

### CHG-01 — crank axis height 55.0 → 60.0

* **Contradiction discovered.** The crank arm must carry material around the crank
  pin bore. With a Ø10 pin, a 4 mm wall gives a boss radius of 9.000, so the arm's
  outer radius is 45 + 9 = **54.000**. At `crank_axis_z = 55.0` the arm's lowest
  point at bottom dead centre is z = **1.000**, and the housing floor top is
  z = **4.000**. Measured crank-shaft / housing common volume at BDC:
  **278.7734 mm³** — the arm is 3.000 inside the floor slab.
* **Affected.** `BODY-CRANK-SHAFT` (arm), `BODY-HOUSING` (floor), and every derived
  height: crank pin, platform pin, plate, guide channel, rim.
* **Minimum change.** One parameter. The least axis height that clears the floor by
  2.0 is `4.0 + 2.0 + 45.0 + 9.0 = 60.000`. Set `crank_axis_z = 60.0`.
* **Old → new.** crank axis 55.0 → **60.0**; crank pin 10.0/100.0 → **15.0/105.0**;
  platform pin 95.0/185.0 → **100.0/190.0**; housing rim 215 → **224**.
* **Resulting measured travel: 90.000000 mm, unchanged.** Travel is `2R` and `R`
  was not touched.
* **Result after the change:** arm lowest point z = **6.000**, clearance to the
  floor **2.000**, crank-shaft / housing common volume at BDC **0.000000 mm³**.
* **Why the validator was not weakened instead.** The alternative was to raise
  `overlap_tol_mm3` above 278.77, or to thin the pin boss to a 1 mm wall so it
  squeezed above the floor. The first would have blinded the check that found this
  (and every other) interference; the second would have moved a real problem into
  a region the toolchain cannot assess. The overlap tolerance is unchanged at
  `1.0e-6 mm³`.

### CHG-02 — the second crank-shaft journal moved from the rear panel into the housing

The provisional layout said *"the rear panel carries the second crank-shaft
journal"*. It cannot.

* **Contradiction discovered.** For the rear panel to journal the shaft, the shaft
  must reach the panel — that is, it must extend along its axis past the connecting
  rod. But the rod **occupies the crank axis**. Measured at bottom dead centre:
  **64.0000 mm³ of rod material** inside a 4 × 4 × 4 probe centred on the crank
  axis, and a minimum distance from the rod to the axis line of **0.0000**. Any
  shaft material there is struck by the rod.
* **The alternative that also fails.** A two-web crankshaft, with the rod between
  two webs and a separate crank pin through both, would put a journal on each side.
  It cannot be built: the two webs would have to be joined, and in the crank's own
  rotating frame the rod swings a full turn about the crank pin, so it sweeps
  through the axis. `BODY-CRANK-SHAFT` would be two disconnected solids, which
  fails the single-connected-solid check in step 2.
* **Consequence.** The crank must be **overhung** — one arm, both journals on the
  −X side of the rod.
* **Minimum change.** Keep the rear panel and all its other roles; add a second
  journal land inside the housing, separated from the first by a relief so the two
  are physically distinct. No body was added, removed or repurposed. Body count
  stays at seven.
* **Resulting measured travel: 90.000000 mm, unchanged.**
* **Why the validator was not weakened instead.** The alternative was to keep the
  provisional layout and declare the shaft "supported at the rear panel" without
  geometry to back it — which is precisely the class of defect `NRM-BM-002-014` and
  `NEG-BM-002-001` exist to catch. The two-journal check was kept and made
  stricter: it now measures the relief between the lands as well as the lands.

### CHG-03 — platform plate and rim heights

* **Contradiction discovered.** The proposed plate at z 197–207 with a rim at 215
  cannot be reached. The clevis must hang below the plate far enough to clear the
  rod's platform eye (radius 9.500) plus the lug body (radius 11.000). With the
  plate underside 18.000 above the pin centre, the rod's eye top at BOTTOM is
  z = 109.5 and the plate underside is z = 118.0.
* **Minimum change.** `clevis_offset = 18.0`; everything else follows from CHG-01.
* **Old → new.** plate at TOP 197–207 → **208–216**; rim 215 → **224**;
  proposed top clearance 8 → **8.000, unchanged and measured.**
* **Resulting measured travel: 90.000000 mm, unchanged.**

### Frozen values that survived unchanged

crank radius **45.000**; rod centre distance **85.000**; crank axis parallel to X;
nominal travel **90.000**, measured **90.000000**; housing floor top **4.000**;
maximum rod angle **31.9657°** against a predicted ≈31.97°; top clearance
**8.000**; rear panel on the +X side; guides in the front and back inner walls;
platform engaged with its guides before the panel is installed; housing top open
for payload access at TOP.

---

## 10. Errors found and fixed during validation

Recorded because a validator that never caught anything is not evidence that the
design is right.

* **DEF-01 — the boundary-crossing control was a no-op in one direction.** The
  first version of NC-02 truncated the hub but left the handle grip in place
  outside the housing, so 3166.7 mm³ still sat outside and the control did not
  register. The mutation now pulls the whole shaft inboard, which is what
  `INA-BM-002-H` actually describes.
* **DEF-02 — the pitch/roll control was defeated by a feature it did not remove.**
  Removing the followers left the plate edges 0.400 from the guide bosses, so a 4°
  rotation still fouled them (13.7431 mm³) and "escape" was not achieved. The
  mutation now also pulls the plate edges 6 mm clear, so the platform genuinely has
  no guide engagement left, and the probe overlap falls to 0.
* **DEF-03 — guide engagement was measured from the wrong bounding box.** The check
  compared the *platform's* z-extent against the channel's, but the platform's box
  reaches down to z = 89 because of the clevis, 5 mm below the channel's lower end
  at z = 94. The check reported the followers as leaving the channel at every
  sample when they never do. It now clips the platform to the channel footprint
  first and measures the *follower's* extent: 114.0 → 130.0 at BOTTOM, inside the
  channel's 94.0 → 224.0.

None of these was a change to the CAD. All three were validator defects; two were
controls that were too weak, and one was a check that was measuring the wrong
thing.

---

## 11. What is claimed, and what is not

### Established at this fidelity

Seven valid single-solid B-rep bodies and no others; a complete physical chain from
the exterior handle to the platform; a realized boundary crossing with two distinct
journal lands; two realized revolute joints with measured clearances and bilateral
axial retention; two realized guide channels engaged throughout; a complete 0–360°
cycle with zero undeclared overlap; measured travel of 90.000000 at both the
support surface and the platform pin, each extreme measured independently;
payload access terminating at the platform; a load path that reaches a reaction
site; an acyclic assembly sequence with no passage through undeclared rigid
material; STEP and BREP export with independent re-import; deterministic rebuild.

### Explicitly NOT claimed

* **verified strength for 1 kg** — no strength evidence exists at any fidelity;
  REQ-003 is UNSUPPORTED (UNR-BM-002-007)
* **verified safety** — no safety criterion is stated (UNR-BM-002-005)
* **verified jamming avoidance** — jamming is contact-level; all corpus evidence is
  V-A declared-pair and none of it is cited here (NRM-BM-002-014); REQ-007 is
  NOT_VERIFIED
* **verified manufacturing practicality** — no process evidence exists
* **verified user effort** — no torque or effort figure is stated (UNR-BM-002-003)
* **position holding after the crank is released** — this design declares no
  holding feature and claims none. Imposing one because a legacy realization used a
  pawl is `NEG-BM-002-014` (UNR-BM-002-004, FRE-BM-002-008)
* **self-locking** — not claimed; a slider-crank driven at 45 mm radius is not
  self-locking and nothing here says otherwise
* **stiffness, wear, fatigue, life, tolerance capability, cost, assembly force,
  pinch hazards, stability under disturbance**

### Oracle matters that remain unresolved

| id | what stays open | effect here |
|---|---|---|
| UNR-BM-002-001 | whether the boundary-crossing hub counts as part of the enclosed mechanism | REQ-004 is **INDETERMINATE**. The arm, rod, both pins and the platform are inside at every sampled state and the +X side is closed; the hub itself is the disputed element and this reference does not decide it (AMB-002-01). |
| UNR-BM-002-002 | the compliance edge of "approximately" | REQ-002 numeric acceptance is bounded by it. 90.000000 is mid-band, so the structural predicate is decidable without deciding the qualifier. Fixing the edge here would be `NEG-BM-002-012`. |
| UNR-BM-002-003 | crank effort, torque, mechanical advantage | no effort claim is made |
| UNR-BM-002-004 | whether the mechanism must hold position when released | no holding feature, no claim |
| UNR-BM-002-005 | definitions of "safe to use" and "obvious jamming" | REQ-005 INDETERMINATE, REQ-007 NOT_VERIFIED |
| UNR-BM-002-006 | the numeric envelope implied by "desktop-sized" | REQ-008 INDETERMINATE; produced envelope 125 × 140 × 224 has nothing to be compared against |
| UNR-BM-002-007 | load margin, factor of safety, duty | REQ-003 UNSUPPORTED |
| UNR-BM-002-008 | insertion force and process parameters | REQ-006 process adequacy NOT_VERIFIED; this design has no press or snap region at all |

### Deferred to a later phase, by instruction

MuJoCo models and runs; plots; operation and assembly videos; the final review PNG
set; VLM review; the human-review packet; the comprehensive report; demonstration
CAD; the failure-CAD corpus; mutation-product CAD; LOCK.json; production pipeline
code; FEA. **None of these was run, and no result from any of them is implied
anywhere in this reference.** Human review status: **HUMAN_REVIEW_PENDING**.

---

## 12. Phase B — MuJoCo rigid-body dynamics

Added **after** Phase A was complete and committed. Nothing in §1–§11 depends on
it, the accepted CAD was not changed to obtain it, and the geometry signature is
identical before and after: `6824e510…6bc2ee`.

Three kinds of evidence now exist for this reference and they are not
interchangeable:

| | what it is | what it computes |
|---|---|---|
| §1–§11 above | **CAD geometry and kinematics** | exact solid measurement. No force. |
| `validation/review/lift_cad_*.mp4` | **prescribed CAD animation** | a pose law. No force. |
| `validation/simulation/` | **MuJoCo rigid-body dynamics** | forces, at an **ideal-joint** fidelity. No contact. |

### 12.1 What the model is

The actual joint topology, not a ratio: a revolute crank on the CAD crank axis, a
revolute crank joint, the fixed-length rod, the platform joint closed as an
equality constraint at the CAD platform-pin axis, and the platform on one
translational degree of freedom. Three joint DOF minus two in-plane constraint
rows leaves one net DOF — the crank angle. **There is no
crank-angle-to-platform-height equation anywhere in the model;** the platform's
height is whatever the solver produces.

Mass and inertia come from the accepted B-rep solids. Densities are **DECLARED
SIMULATION ASSUMPTIONS — NOT SOURCE REQUIREMENTS, NOT VERIFIED MATERIAL
SELECTIONS**: 1200 kg/m³ for the housing, rear panel and platform, 7850 kg/m³ for
the shaft, rod and both pins. Total product mass **2.76052 kg**, of which
**1.88964 kg** moves.

Both joint pins are welded into their CAD parents. Each is a body of revolution
about a joint axis parallel to X and each pin's centre is rigidly fixed to that
parent, so the weld is exact for position and for inertia about the joint axis.
Their full CAD mass and inertia are retained. **This makes no claim about pin
contact, bending or bearing stress.**

### 12.2 What it found

* The assembled mechanism completes a full 0–360° crank cycle with **zero solver
  warnings** and a loop-closure residual of **9–14 nanometres**, against the
  0.1 mm running clearances the CAD declares.
* Measured travel **90.0000 mm** in both scenarios — the dynamics reproduce the
  geometric result rather than being told it.
* Empty actuator torque **±0.15580 N·m** (RMS 0.10649), peaks at 105.2° and 254.8°.
* With the 1 kg scenario payload **±0.65691 N·m** (RMS 0.43031), peaks at 111.6°
  and 248.4°.
* **Incremental payload torque ±0.50263 N·m** (RMS 0.32453), peaks at 113.2° and
  246.8°. This is the density-independent result: the only difference between the
  two runs is the payload.
* An **independently implemented** analytic quasi-static torque `τ = m g dz/dθ`
  agrees with the incremental result to **0.0000703 N·m** — 0.7 % of the declared
  2 % tolerance. The analytic functions are re-derived inside `simulate_lift.py`
  from R, L and the axis height; they do not call this file's pose law, so the two
  sides of the comparison are not the same function.
* Torque changes by **0.2 % across a 5× speed range**, so the result is
  essentially quasi-static and the inertial term is small.
* **The mechanism back-drives.** 12 of 16 release cases move under gravity when
  the actuator is released. The four that do not are the 0° and 180° **kinematic
  dead centres**, where `dz/dθ = 0` and gravity exerts no crank torque. Those are
  reversals, not stops — nothing in the product arrests the platform there.
  Released at 135° the platform falls **70.66 mm**, at 90° **32.11 mm**, at 45°
  **7.00 mm** — in every case exactly the height from the release position down
  to the bottom of travel, which is the energy check an undamped model must pass.
  The model has no damping, so the mechanism then swings back like a pendulum;
  the reported figures are maximum excursions, not end states.

### 12.3 What it did NOT change

**Nothing in the Oracle position moved, and nothing could have.**

* **REQ-003 payload capacity stays UNSUPPORTED.** The peak ideal joint reactions
  under the 1 kg payload are 29.2 N at the crank bearing, 14.3 N at the crank
  joint, 12.9 N at the platform joint and 7.2 N at the guide. **A constraint
  reaction is a resultant, not a stress.** No area, no pressure, no deflection and
  no stress is computed anywhere in this model (UNR-BM-002-007).
* **REQ-007 jamming stays NOT_VERIFIED.** The guide here is a **single ideal
  prismatic constraint**; the real CAD guide is two channels with 0.2 mm side and
  0.4 mm tip clearances. No contact is resolved, so jamming, binding, wear, local
  pressure and tolerance behaviour are all outside this model
  (NRM-BM-002-014, NEG-BM-002-011).
* **Back-driving creates no requirement.** The source states no holding,
  self-locking or back-drive requirement (UNR-BM-002-004, FRE-BM-002-008), so the
  result is a behaviour a reviewer should weigh, not a failure. Imposing a holding
  requirement because a legacy realization used a pawl is NEG-BM-002-014.
* Safety, manufacturability, effort and life are untouched.

### 12.4 Errors found and fixed during Phase B

Recorded for the same reason as §10: a simulation that never caught anything is
not evidence.

* **SIM-01 — the inertia tensors were wrong, and MuJoCo refused the model.**
  `GProp_GProps.MatrixOfInertia()` is already referred to the **centre of mass**,
  not the frame origin. The first derivation applied a parallel-axis shift anyway,
  subtracting a term that was not there and producing tensors with negative
  eigenvalues. MuJoCo rejected them at load time with *"inertia must have positive
  eigenvalues"*. Verified against a 100 mm cube, which returns 1.666667e9 mm⁵
  about its own centre rather than the 6.666667e9 it has about the origin.
* **SIM-02 — the servo gains were unstable for this mechanism.** The first attempt
  used kp = 4000, kv = 200. The crank's inertia about its axis is ≈1e-3 kg·m², so
  `kv·dt/I = 77` — far beyond the explicit stability limit of 2 — and the
  integrator diverged on the first step. Gains are now sized against that inertia:
  kp = 1500, kv = 3.0, giving 0.4 and 8e-3.
* **SIM-03 — the rod's initial angle had a sign error**, which left the loop
  unclosed at every settle. `q_rod = asin(R sin θ / L) − θ`, not `−asin(…) − θ`.
* **SIM-04 — divergence could hide.** `mj_step` calls `mj_checkPos`, which resets
  the whole `MjData` — warning counters included — when the state goes bad.
  Comparing warning counts before and after a run therefore reports **zero** for a
  run that blew up. Negative control NC-S17 caught exactly this, and every run now
  carries an in-run `Divergence` watch reported as `divergence_watch`.

None of these was a CAD defect. All four were defects in the simulation code, and
two of them were surfaced by the checks that exist to surface them.
