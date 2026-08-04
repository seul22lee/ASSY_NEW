# BM-001 executable reference report

Two Oracle-aware executable reference CAD models for BM-001, built and validated
under phase CAD-1.

**State: EXE-BM001-01 revised and validated; EXE-BM001-02 pending redesign.**
Not `CAD_CORPUS_COMPLETE`, not `PACK_LOCK_READY`, not `PHYSICALLY_PROVEN`, not
`PRODUCTION_READY`, and not human-approved.

Two Oracle-aware BM-001 designs were built as valid B-rep solids and found
geometrically and kinematically admissible under the active BM-001 Oracle at the
evaluated fidelity. EXE-BM001-02's result predates the human decisions that
rejected its retention concept, and stands only as the record of the design that
was rejected.

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
| Guidance | five interleaved knuckles on a separate pin | two lipped rails, integral |
| Retention | rigid sliding bolt, lift to release | rigid quarter-turn cam (REJECTED, awaiting redesign) |
| Hinge pin | headed, with two integral cantilever snap arms | n/a |
| Bodies | 4 | 3 |
| Semantic fixture | ADM-BM-001-E (close) | **none** |
| Terminal bounds | one (open), constructed stop face | two (open and closed), end walls |
| Geometry signature | `f2bc9599cdd6832d…` (was `5586b96cc2e92e11…`) | `11bcc694d0261737…` |

They differ in joint type, body count, retention principle and assembly process.
Neither is a variation of the other.

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
integrated assembly snap and an integrated releasable latch was directed.
**That redesign has not been done.** The reference in the tree is still the
rejected cam design.

### What the pin revision cost

The original reference selection deliberately avoided compliant features so the
model would not depend on material behaviour. Bilateral retention without a
second part cannot be had that way, so the pin is now
`GENERIC_COMPLIANT_POLYMER` and its assembly needs a real 1.05 mm deflection per
arm. Only `REG-P-SNAP-COMPLIANT` is treated as deformable, and only during
insertion; everywhere else the pin is a rigid guide. Every force, strain and life
question the change introduces is NOT_VERIFIED.

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
| 1 build | 4 bodies | 3 bodies |
| 2 solid validity | PASS | PASS |
| 3 STEP + BREP re-import | PASS | PASS |
| 4 signature and rebuild determinism | PASS | PASS |
| 5 motion sampling | PASS (180 samples, 2 segments) | PASS (231 samples, 3 segments) |
| 6 interactions | PASS (16 declared) | PASS (13 declared) |
| 7 assembly | PASS | PASS |
| 8 Oracle predicates | PASS | PASS |
| 9 render | 20 images | 20 images |
| checker self-test | PASS 12/12 | PASS 8/8 |
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

Also unmodelled: cam holding torque, friction, wear, flexure, magnetic force,
manufacturing tolerance capability.

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
pass only if the check reports it: 7 for EXE-BM001-01, 8 for EXE-BM001-02, all
detected. `tools/test_primitives.py` adds 29 closed-form checks on the shared
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
it measures that the declared region is covered by 21367 mm³ of closure in the
closed state, so it is a region the closure genuinely controls rather than one
drawn where the closure never reaches.

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
