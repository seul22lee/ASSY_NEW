# BM-001 executable reference report

Two Oracle-aware executable reference CAD models for BM-001, built and validated
under phase CAD-1.

**State: both references revised and validated.**
Not `CAD_CORPUS_COMPLETE`, not `PACK_LOCK_READY`, not `PHYSICALLY_PROVEN`, not
`PRODUCTION_READY`, and not human-approved.

Two Oracle-aware BM-001 designs were built as valid B-rep solids and found
geometrically and kinematically admissible under the active BM-001 Oracle at the
evaluated fidelity. Both have since been reworked to satisfy the human CAD review
decisions, and both have been rebuilt and revalidated after that rework.

Failure CAD is not part of the current positive-reference plan. Local
counterfactual validation probes may be used without creating a curated
failure-CAD corpus.

| | |
|---|---|
| Oracle commit these were built against | `83fc12d46ad8c5fad36afcfe5b6e916822a41118` |
| Active Oracle scope commit | `0af83c90bbda611182d0544cc736f09ae89fc718` |
| Oracle files modified | none |
| Toolchain | CadQuery 2.4.0 / cadquery-ocp 7.7.0 / OCCT, CPython 3.8.10 |
| Recreate with | `ver3/cad_validation/tools/create_env.sh <path> python3.8` |

## What these are, and are not

They are **references**: their author read the invariants, the fixtures and the
expected predicates before modelling. They establish that designs satisfying the
BM-001 rank-1 source can be built as valid B-rep solids and moved through their
required states without undeclared volumetric overlap.

They establish **nothing** about whether the source alone leads a competent
author anywhere acceptable. Only a source-only Demonstration can test that, and
`demonstrations/` is deliberately empty pending a fresh session.

Two admissible designs passing is also consistent with an over-permissive Oracle.
That is not a defect in this pilot; it is the reason inadmissible and mutation
CAD exist as later phases.

## The two references

| | EXE-BM001-01 | EXE-BM001-02 |
|---|---|---|
| Closure motion | revolute, 110° | prismatic, 84 mm |
| Guidance | five interleaved knuckles on a separate pin | two captive C-section rails, integral |
| Retention | rigid sliding bolt, lift to release | the rails themselves: four integral cover tabs under two retaining lips |
| Snap features | headed pin with two integral cantilever snap arms | four retention tabs and one latch finger, all part of the cover |
| Bodies | 4 | **2** |
| Semantic fixture | ADM-BM-001-E (close) | **none** |
| Terminal bounds | one (open), constructed stop face | two (open and closed), stop faces |
| Geometry signature | `f2bc9599cdd6832d…` (was `5586b96cc2e92e11…`) | `1eba7a573b5787ba…` (was `870af742b622b856…`) |

They differ in joint type, body count, retention principle and assembly process.
Neither is a variation of the other.

EXE-BM001-02 has been through four topologies. The three that are gone are
recorded in `EXE-BM001-02/DESIGN_AND_OPERATION_RATIONALE.md`; their artifacts
have been deleted rather than left in the tree, and git history holds them.

EXE-BM001-02 deliberately matches no listed fixture. The seven admissible
fixtures are the machine-checked sample, not the permitted set, and an Oracle
that only ever sees designs drawn from its own fixture list is being tested
against itself.

## Human review, and what it changed

A person reviewed the first pilot and recorded seven decisions
(`reviews/HUMAN_CAD_REVIEW_DECISIONS.yaml`). Two references were affected very
differently.

**EXE-BM001-01.** The rear stop-arm projection was APPROVED and is unchanged. The
one-direction hinge-pin retention was REJECTED: the head blocked removal one way
and the far end could walk out. The pin was replaced with a headed pin carrying
two integral cantilever snap arms, giving bilateral axial retention — the head
shoulder blocks travel toward the barb, the recovered lug shoulders block travel
toward the head. The revision has been built and validated; **independent human
review of the result is PENDING.**

**EXE-BM001-02.** The 84 mm of 90 mm usable opening was APPROVED. The full-open
lift-out, the separate quarter-turn cam, and the cam's missing orientation
retention were all REJECTED, and a guided captive sliding cover with an
integrated assembly snap and an integrated releasable latch was directed. That
redesign has been done, and then done again.

The first attempt at it kept the cam design's lipped rails and bolted a snap onto
them. A lipped channel closed at both ends cannot be entered by any translation,
so it needed a relief cut in the lips and a loading position beyond the open
bound just to get the cover in — a workaround wearing the shape of a feature, and
an assembly path that was implausible rather than merely awkward.

The attempt after that removed the lips and put the retention on a **separate
snap rivet** pressed through cover and enclosure, with a keeper bridge across the
top of the product for the latch. It measured clean, but it was the wrong answer
to the question: a fastener compensating for rails that had no overhang. A third
body was doing the rail's job, and "snap-fit" had come to mean "a snap-fit part"
rather than an integral compliant feature.

**The current design is two bodies and nothing else.** The rails are complete —
ledge, guide wall and overhanging retaining lip on both sides — and they carry
all three retention functions between them: support, lateral guidance and
anti-lift. The cover has four integral snap tabs that deflect 2.2 mm inboard,
pass between the lip inner edges, and recover underneath them. Assembly is one
straight downward press at the closed position. The closed state is held by a
second integral snap: a finger at the cover's exposed end reaching out through
the end wall, with a tooth standing behind the strip of wall beside the slot.
Push the pad sideways, the tooth clears, slide the cover open.

Both references have been built and validated; **independent human review of the
result is PENDING for both.**

### What the two revisions cost

The original reference selection deliberately avoided compliant features so the
model would not depend on material behaviour. Bilateral retention without a
second part cannot be had that way, so the pin is now
`GENERIC_COMPLIANT_POLYMER` and its assembly needs a real 1.05 mm deflection per
arm. Only `REG-P-SNAP-COMPLIANT` is treated as deformable, and only during
insertion; everywhere else the pin is a rigid guide. Every force, strain and life
question the change introduces is NOT_VERIFIED.

EXE-BM001-02 paid it across five features. Its cover is
`GENERIC_COMPLIANT_POLYMER` with three declared compliant regions:
`REG-COVER-RETAIN-LEFT-COMPLIANT` and `REG-COVER-RETAIN-RIGHT-COMPLIANT` (two
tabs each, 2.2 mm inboard, assembly only) and `REG-COVER-LATCH-COMPLIANT` (the
latch finger, 2.6 mm inboard, release and lead-in only). All are modelled as
rigid translations of a declared region, so volume is conserved to 0.000 mm³ —
which makes them a `DECLARED_KINEMATIC_APPROXIMATION` of a snap, testing
geometric passage and engagement and predicting nothing about strain. Service
removal survives, unlike the rivet version, but it now needs all four tabs
deflected at once through the rail channels: a deliberate action, recorded as
`LIM-01`, not an ordinary pull.

### Four errors the checks caught before they reached the report

1. A full-diameter cone split by one slot measured **5.09 × 5.58 mm** compressed
   against a 4.2 mm bore — unassemblable. Splitting a cone compresses it only
   across the slot.
2. The compressed envelope was first measured as a **bounding box**. A bore is
   round, so the constraint is the greatest distance from the axis; the flat span
   fitted while the diagonal did not. The measurement is now the circumscribed
   diameter.
3. The arms were first deflected by **rotating** them about their roots, which
   swung the far end across the axis so the envelope grew with deflection, and
   which did not conserve volume. A rigid inward translation does both correctly
   and conserves volume exactly.
4. Rectangular arm sections put the beam corners at radius **2.33** against a 2.1
   bore radius. The beam is now clipped to the shaft radius; only the lug reaches
   the retaining radius.

None of these would have shown as a failure — each would have produced a clean
report about geometry that cannot be built.

## Results

Both references, full sampling, on the locked interpreter:

| Step | EXE-BM001-01 | EXE-BM001-02 |
|---|---|---|
| 1 build | 4 bodies | 2 bodies |
| 2 solid validity | PASS | PASS |
| 3 STEP + BREP re-import | PASS | PASS |
| 4 signature and rebuild determinism | PASS | PASS |
| 5 motion sampling | PASS (180 samples, 2 segments) | PASS (2 segments) |
| 6 interactions | PASS (16 declared) | PASS (15 declared) |
| 7 assembly | PASS | PASS |
| 8 Oracle predicates | PASS | PASS |
| 9 render | 20 images | 28 images |
| checker self-test | PASS 12/12 | PASS 16/16 |
| **overall** | **PASS**, 0 findings | **PASS**, 0 findings |

Maximum boolean common volume over every body pair, every state and every
sampled point of every motion segment: **0.0 mm³** in both references, against a
1e-6 mm³ threshold.

### Oracle predicate totals

Identical for both references:

| Status | Count |
|---|---|
| PASS | 12 |
| NOT_EVALUABLE | 1 |
| FAIL | 0 |

`NRM-BM-001-006` is `NOT_EVALUABLE / REPRESENTATION_INCOMPLETE`, blocked on
`UNR-BM-001-001`, in both. Its first clause asks what the design holds against;
neither design declares a disturbance magnitude, because inventing one would
manufacture a requirement the source does not state. **That is a missing
declaration, not missing evidence, and NOT_EVALUABLE is not FAIL.**

Two references with entirely different retention mechanisms reaching the same
NOT_EVALUABLE for the same reason is worth noting: it points at
`UNR-BM-001-001` rather than at either design.

Clause-level results additionally carry `NOT_VERIFIED` for durability
(NRM-BM-001-007) and load-path adequacy (NRM-BM-001-011) in both.

## Claim fidelity

What may be read as established: valid non-zero B-rep solids; absence of
undeclared volumetric overlap across the sampled motion; traversability of the
required motion; declared interactions behaving as declared under a stated
evaluation tolerance; terminal conditions produced by realized geometry;
existence of an unobstructed assembly ordering; existence of a load path.

What remains `NOT_VERIFIED` **by construction**, for both references:

| Rank-1 requirement | Why |
|---|---|
| REQ-002 / REQ-004 secure closure under handling and transport | needs a disturbance magnitude and a retention capacity; no forces are computed |
| REQ-003 latch easy to operate | needs an effort ceiling and a measured effort |
| REQ-005 low-cost manufacturing | needs a process and a cost model |
| REQ-007 easy to assemble | the *existence* of an ordering is geometric and passes; *ease* is an effort claim |
| REQ-001 / REQ-008 reusable | geometric repeatability passes; durability over an unstated cycle count does not |
| REQ-006 practical for desktop use | the source states no envelope |

Also unmodelled: snap-in force, pull-out capacity, latch release effort, friction,
wear, flexure, creep, impact resistance, manufacturing tolerance capability.

**No sentence in this pilot may combine a computed geometric result with an
unverified physical requirement.** These references are reported as
*geometrically and kinematically admissible*, never as verified, proven, or
satisfying the source.

## What the validation found, rather than confirmed

A clean report is worth little unless the checks can fail. Four things were
caught by the chain rather than by review:

1. **EXE-BM001-01 could not be assembled as first parameterized.** With the
   rotation axis 4 mm behind the rear face, the knuckle envelope reached 1 mm in
   front of the closure plate's rear edge, and the plate's concentric relief only
   cleared it in the seated position — so no straight-line insertion existed.
   Step 7 rejected it. Moving the axis to `knuckle_r` behind that face removed
   the need for the relief entirely. The fix made the model harder to satisfy,
   not easier.

2. **Two measurement regions were reading the wrong feature.** INT-08's region
   reached down to the rim and reported the seat contact instead of the axial
   knuckle gap; INT-15's reached the guide bore and reported INT-10's clearance
   under INT-15's name. Both were tightened. Additionally
   `NOT_INTENDED_TO_INTERACT` never compared against its declared nominal, so a
   wrong declaration passed — now it does.

3. **An overclaim about retention.** The report asserted the opening rotation was
   blocked while retained, without measuring it. Measured, the block begins at
   **0.75°**, not zero: near the closed pose the closure's motion at the bolt is
   almost entirely *along* the bolt axis, so the bore slides on the shaft before
   it bears on it. The declared 0.1 mm running clearances imply exactly that free
   play. The claim now states the measured onset.

4. **A shared-primitive property nobody had noticed.** `cadval.bbox_of` returns a
   box inflated ~1e-7 mm per face by OCCT's `Bnd_Box` gap. Harmless — it is
   deterministic and well inside the signature tolerance — but it is now
   documented and pinned rather than latent.

Each reference also carries negative controls that inject a defect in memory and
pass only if the check reports it: 12 for EXE-BM001-01, 16 for EXE-BM001-02, all
detected. EXE-BM001-02's set includes a missing retaining lip, a lip that stops
short of the open bound, a missing tab, a tab that never reaches under a lip, a
tab that cannot pass at assembly, lift-out and tilt-out at full open, a
reintroduced third body, a detached release tab, a release that does not clear
the keeper, a floating keeper, a missing tooth, a latch that never re-engages, a
narrowed opening, obsolete metadata, and a review-image set missing its assembly
and operation evidence. `tools/test_primitives.py` adds 29 closed-form checks on the shared
primitives, including an explicit assertion that the naive three-argument
`cq.Location` does **not** fix an arbitrary axis — pinning the rotation bug that
was found and fixed earlier in this phase, and which would have silently
invalidated every motion result in both references.

## The honest weak point

EXE-BM001-02 declares **84 of its 90 mm aperture** as usable access. A captive
sliding closure cannot uncover the whole of its own aperture — it has to go
somewhere, and the only place is over the rest of the enclosure.

`NRM-BM-001-003` asks whether the closure obstructs the access *the design
declares*, so this passes. The evaluator blocks the crudest way of gaming that —
it measures that the declared region is covered by 18480 mm³ of cover in the
closed state, so it is a region the cover genuinely controls rather than one drawn
where the cover never reaches.

That second measurement was itself wrong until an earlier revision, and the way
it was wrong is worth recording: it was taken in the clear prism *above* the
aperture, where the cover never goes. It read 0 mm³ and the clause passed anyway —
a check that could only ever pass. It is now taken in the aperture band between
the ledge tops and the cover top, the clause is load-bearing, and `CTL-09` in the
previous topology injected an out-of-footprint region to prove it could fail.

The redesign then found a defect the *drawings* caught rather than the checker.
An earlier arrangement put the latch finger on the cover's centreline; at full
open it retracted **into** the declared 84 mm opening at cover level. The access
probe missed it because the probe measured only the prism above the cover, and
the finger sits level with it. It was visible the moment the full-open view was
cut in a plane where the aperture actually exists. The latch was moved out over
the near rail, where it retracts over the ledge instead — intrusion is now
0.000 mm³ in the aperture band and in the prism above it alike. The lesson is
about the probe, not the CAD: a region-based access check that samples only one
band can be satisfied by geometry that obstructs another.

A reviewer may still judge that a design should not be able to pass by narrowing
its own declaration. **That would be a finding about NRM-BM-001-003, not about
this CAD**, and belongs in `PRE_CAD_BACKLOG.yaml`. It is flagged here rather than
left for someone to discover.

## Review status

Both references are **`AUTHOR_SELF_REVIEW`** and **`HUMAN_REVIEW_PENDING`**. No
person has inspected the images. Checklists are at
`EXE-BM001-0{1,2}/validation/human_review_checklist.md`; each ends with the
questions the author could not answer about their own work.

## Not created in this phase

Source-only Demonstration CAD; inadmissible CAD; failure CAD; mutation CAD;
`LOCK.json`; production pipeline code; Ver3 stages. `demonstrations/` contains
only a README explaining that a fresh source-only session owns it.
