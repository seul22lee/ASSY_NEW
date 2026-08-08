# EXE-BM003-01 — design and operation rationale

What this mechanism is, how it works, and every decision that had to be revised
because the exact B-rep disagreed with the intention behind it.

This is an **Oracle-aware executable evaluator fixture**. It is not a golden
design, not a recommended mechanism, and not a production result. See
`GOVERNANCE.yaml`.

---

## 1. The mechanism

A central hub carries three leg stations 120° apart. Each station is a clevis
pair — two parallel plates — and a leg blade sits between them on a hinge pin.

Each leg carries a **heel**: a stub that is rigidly part of the leg and leans
inward from the hinge. Because it is body-fixed, swinging the leg **out** swings
the heel **down and inward**; swinging the leg **back** raises it.

A captive annular **ring** runs on the hub column and has three arms. With the
ring down, each arm sits a small gap above one heel. Folding a leg back drives
its heel up into the arm and stops. That is the entire state-maintenance
principle — declared class **SMC-KINEMATIC_BLOCK**, realised as hard geometric
interference between two named bodies with named features.

Three **ribs** on the column sit inside three **keyways** in the ring's bore.
While the ring is down it cannot be turned. So the release takes two motions:

1. **lift** the ring until its bore clears the rib tops;
2. **turn** it so the arms move off the heels and come to rest over the rib tops.

Only then can the legs fold. Both halves are measured, not asserted:
`validation/state_maintenance.json` records the angle at which fold-back is
stopped with the ring down, the angle at which the fold is stopped if the ring is
lifted but *not* turned, and the fact that the fold is clear once it is both
lifted and turned.

Nothing can leave the product:

| body | escape direction | blocked by |
|---|---|---|
| ring | up | the ring captor |
| ring | down | the hub pedestal top |
| ring captor | up | the hub's lower bayonet lugs |
| ring captor | down | the column step |
| top support | up | the hub's upper bayonet lugs |
| top support | down | the lower bayonet lugs |
| hinge pin | in | its own head on the clevis's outer face |
| hinge pin | out | its turned bayonet end bar |
| leg | along its hinge axis, either way | the clevis pair |
| leg | off its pin, in or out | the pin |

Every one of those rows is a measurement in `validation/retention.json`: the body
is pushed 2 mm along the named direction and the boolean common with the named
blocker is computed.

Ten bodies: `BODY-HUB`, `BODY-LEG-A/B/C`, `BODY-PIN-A/B/C`, `BODY-RING`,
`BODY-RING-CAPTOR`, `BODY-TOP-SUPPORT`.

## 2. Operation

    STORED --M1--> DEPLOYED_RELEASED --M2--> LIFTED_ALIGNED --M3--> DEPLOYED_LOCKED
    DEPLOYED_LOCKED --M4--> LIFTED_ALIGNED --M5--> DEPLOYED_RELEASED --M6--> STORED

M4 is M3 reversed, M5 is M2 reversed, M6 is M1 reversed. No step is one-way, and
the transforms at the end of M6 are bit-identical to the STORED transforms.

## 3. Why this class and not another

The Oracle offers four state-maintenance classes and prefers none of them
(NRM-BM-003-009, corrected at semantic review F-01). This fixture declares
**SMC-KINEMATIC_BLOCK** for one reason and it is a reason about the *evidence*,
not about the *design*: it is the only class whose predicate exact rigid geometry
can decide, because the claim is that a path is **absent**. The other three need
stability, potential-energy or contact-resolving routes this toolset does not
have, and the Oracle says so itself — `establishable_now: false` on all three.

Choosing the class this pipeline can establish is not a statement that an
over-centre, gravity-seated or compliant design would be worse. It would be
equally admissible and its persistence claim would honestly read NOT_VERIFIED.
This fixture establishes **one** positive executable reference. It says nothing
about whether any other admitted family is executable.

## 4. Revisions forced by the exact B-rep

Every one of these was found by building the solids and measuring them. The
first exact build was not expected to be right and was not.

### R1 — the hub built as seven disconnected solids

`clevis_x0 = 28.0` put each clevis plate's inner end exactly on the base flange's
radius. But the plates sit at |y| ∈ [6, 12], and at y = 12 the flange's own
boundary is at x = √(28² − 12²) = 25.3, not 28. The plates therefore missed the
flange entirely and `BODY-HUB` came out of `build()` as 1 + 6 solids.

- **Owning decision:** a dimension.
- **Fix:** `clevis_x0` 28.0 → 24.0.
- **Consequence:** the plates' inner corners moved to r = 24.74, inside the ring
  arms' 26 mm reach and inside their angular span. `ring_arm_r` 26.0 → 23.0. The
  arms still cover the heel's blocking corner, which never exceeds r = 20.6
  anywhere on the fold-back path.

### R2 — nothing stopped a leg swinging *past* deployed

The first exact model bounded the fold-back side and left the other side open. A
leg could keep swinging outward indefinitely; the stand would splay flat under
any downward load. The source does not name this among "fold back, twist aside,
or come off", but it does say "move in some other direction I was not expecting",
and NRM-BM-003-010 requires each leg's forbidden mobility to be *declared and
addressed* rather than merely unmentioned.

- **Owning decision:** topology — a body was missing a feature.
- **Fix:** three **outward stop pads** on the hub base flange, in the clevis gap,
  that the heel's underside comes down on. Their top face is *derived*: the
  heel's underside height at the pad's outer edge at the deployed angle, minus a
  declared `outward_stop_clearance`. The residual outward travel that leaves is
  measured in `validation/outward_stop.json`, not assumed.

### R3 — the stop pad was put inside the leg's hinge eye

`stop_pad_x1` was first set to 33.0, chosen against the leg *shaft*'s inner edge,
which sits at r = 34.8 at the deployed angle and only moves outward from there.
That ignored the leg's hinge **eye**, a cylinder of radius 10 about the hinge
axis at r = 40, whose inner extent is r = 30. The pad sat inside it.

The give-away was the shape of the failure, not its size: `BODY-HUB` ∧
`BODY-LEG-x` reported **86.81988311 mm³ at every leg angle**, identical to nine
decimals. An overlap that is invariant under rotation about the hinge axis has to
be with something that is itself invariant about that axis — which in this design
is the eye and nothing else.

- **Owning decision:** a dimension, and a wrong choice of which feature bounds it.
- **Fix:** `stop_pad_x1` 33.0 → 29.0. The eye, not the shaft, is the binding
  constraint. The deployed clearance then measures 0.1427 mm against a 0.15 mm
  declared nominal — the difference is geometric, because the clearance is
  applied vertically and `min_distance` returns the perpendicular to a heel
  underside tilted about 18° from horizontal.

### R4 — how the hinge pin is captured, and why it took three attempts

A rigid part pushed into a pocket along one straight line always leaves the
reverse direction open. Retention therefore needs either a later body covering
it, a turn, or elasticity. This design has no elastic parts, so:

- A separate clip in a blind pocket was tried first. Its own escape direction
  then needed a captor, which needed a captor. The chain does not terminate.
- Capturing the pin between a blind bore one side and a head the other cannot be
  assembled: the head has to pass through the bore it is meant to bear on.
- **Adopted:** a **bayonet pin**. A bar across the pin's far end passes through a
  relief cut through both clevis plates and the leg eye, and is then given a
  quarter turn so it no longer lines up with that relief. The head blocks travel
  one way, the turned bar the other. The chain terminates on `BODY-HUB` itself.

The relief has to be cut **after** the leg is rotated into its as-built pose, so
that it is horizontal in the configuration assembly happens in. Cutting it in the
leg's stored frame would have left it at 30° and the pin could not have been
inserted.

A first sizing of the relief — a bar long enough to need `pin_slot_half_x` well
past 6 mm — would have cut the leg eye in two, leaving the upper lobe hanging off
a sliver of heel. Shrinking the bar to a 5 mm half-length keeps a 4.7 mm wall of
eye either side of the relief and the eye stays a connected ring.

The same bayonet closes the ring captor and the top support. Step 7 sweeps
straight lines only, so each of the five quarter turns is swept separately in
`validate.py` and reported in `validation/bayonet_turns.json`; the corresponding
assembly steps are `kind: operation` and cite it.

### R5 — the turn quietly stopped being necessary

`P_LIFT_ONLY` — the check that lifting the ring *without* turning it does not free
the legs — failed after R1. The cause was R1 itself. Shortening the arms from
r = 26 to r = 23 to clear the moved clevis plates was correct for the locked
configuration, where the heel's blocking corner is at r ≈ 20.3. But the heel
moves **outward as it rises**: at the lifted ring height it reaches r = 23.79,
just past the shortened arm's outer edge. Lifting alone therefore freed the legs
completely, and the turn became decorative.

- **Owning decision:** a dimension, in a place two revisions away from the
  symptom.
- **Fix:** `rib_h` 4.0 → 2.0. A shorter rib means a shorter lift, and the heel is
  still under the arm when it gets there. Lifting alone now stops the fold at
  θ ≈ 21.5°, measured; the full path to stored needs the turn.
- **Consequence:** every derived height above the ring moved down with it, and
  `INT-RING-CAPTOR-GAP` — which *is* the ring's lift travel — went from 4.4 to
  2.4 mm.

This one is worth naming plainly: a dimension was changed because a check failed.
That is only legitimate because the check was testing a property the mechanism
was supposed to have and had silently lost, so the failure was a true report of a
real regression. Deleting the predicate instead would have been the illegitimate
move. See `SELF_AUDIT.md` question 10.

### R6 — the ring seat is derived, not chosen

Setting the blocking gap by picking a seat height independently of the heel gives
a gap that silently changes whenever any heel dimension moves. `seat_z` is
therefore computed in `build.geom()` from where the heel's topmost corner
actually is at the deployed angle, plus a declared `blocker_clearance`. Every
height above it — rib top, ring release height, captor seat, captor lugs, sleeve
seat — is derived from that in turn, so the whole column stack moves together and
no two of those numbers can drift apart. R5 is the demonstration that this
matters: one parameter changed and eight heights followed correctly.

### R7 — assembly has to end DEPLOYED

The ring's arms come down over the heels. Fold the legs and the heels rise into
the arms' path, and the ring cannot be seated at all. So the assembly sequence
ends in `DEPLOYED_LOCKED` and `build()` returns that configuration, because step
7 sweeps the as-built solids.

FRE-BM-003-013 leaves the arrival configuration free and AMB-BM-003-010 records
that stored-state holding is not required. Neither is read back as a requirement:
this is a consequence of the mechanism, and a design that arrives stored would be
equally admissible.

### R8 — two corrections to the *checker*, not to the design

Both were found the same way: a check disagreed with the mechanism, and the
mechanism was right.

**Connectivity treated a limit stop as a running pair.** The first version
required every declared pair to stay within `connection_tol`. `BODY-RING` and
`BODY-RING-CAPTOR` touch only at the top of the ring's travel, so the check
reported the ring as detaching every time it was lowered. The distinction it was
missing is that a limit stop's separation *is* the stroke. Running pairs and
limit stops are now separate lists; the stroke is reported, and the ring's
captivity is established by an escape probe — by geometry, not by proximity.

**The outward stop check did not discriminate.** Negative control NC-17 removes
the three stop pads and expects `P_OUTWARD` to fail. It did not: with the pads
gone the heel still eventually reaches the base flange, about 8.5° past deployed,
so "something stops it" stayed true. The predicate was measuring the wrong thing.
NRM-BM-003-010 asks the *design* to declare its intended and forbidden mobility,
so the reference now declares `outward_travel_max_deg = 3.0` and measures the
residual travel against it — 1.0° with the pads, 8.5° without. That number is a
fixture design declaration of this mechanism's own intent. It is **not** an
Oracle threshold and must not be read back as one; the Oracle introduces no
number anywhere (FRE-BM-003-011).

## 5. What the numbers are, and what they are not

BM-003's frozen source contains no digit. Every dimension in `parameters.yaml` is
a fixture design choice, free under FRE-BM-003-011, and **none of them may be
read back into the Oracle as a requirement, a preferred size or a threshold**.
They exist because an exact B-rep needs numbers.

The measured quantities the evidence rests on are *relations*, and they are all
in `validation/`:

- fold-back is obstructed short of stored, for each of the three legs;
- the fold is clear after the lift and the turn;
- lifting alone leaves the fold obstructed;
- the ring cannot be turned at the locked height and turns freely once lifted;
- swinging past deployed is stopped;
- every retention blocks its named direction;
- three ground contacts bound a non-zero area on a common plane;
- at least one storage-relevant extent is smaller stored than deployed;
- every declared connection stays engaged at every sample of the whole cycle.

What is **not** established, and cannot be from this evidence: load capacity, the
disturbance the locked state survives, material, wear, lifetime, manufacturing
process, user effort, whether the footprint is big enough for anything, whether
the residual play between the two leg stops is acceptable, and whether a bayonet
could be turned back by vibration. These are recorded in
`actual_evaluation.json` under `unsupported_and_not_verified`, each against the
ambiguity that keeps it open.

## 6. Dynamics

None was run. The reference records
`DYNAMICS_NOT_REQUIRED_FOR_THIS_REFERENCE`.

Every question this reference answers is a question about whether a rigid-body
configuration exists or does not: is there a path, is there an overlap, is there
a blocked direction, is the envelope smaller. None of them needs gravity,
inertia, a dynamic release, a stability result or a force. The one class of
question that *would* need a dynamic route — how much disturbance the locked
state survives — is blocked at AMB-BM-003-005 anyway, which carries no magnitude,
so a simulation would be measuring an invented number.

Adding a simulation here would produce evidence for a claim nobody is entitled to
make. It was not added.
