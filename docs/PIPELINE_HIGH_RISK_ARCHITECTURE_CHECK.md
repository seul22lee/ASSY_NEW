# High-risk architecture check — three falsification probes

**Purpose.** Falsify, or fail to falsify, the three highest-risk decisions in
`PIPELINE_IMPLEMENTATION_PROPOSAL.md` before implementation begins.

**Scope discipline.** Only these three decisions. Scope is not expanded, and no
redesign is proposed, because none of the three provably fails.

**Nothing implemented.** No code, no contract, no stage. The corrections at the
end are *specified*, not applied.

**Verdict: B — safe with small contract changes.** All three decisions survive.
Each needs bounded corrections: six fields for compliance, five ownership rules
for load, five loop rules for settlement. One proposed rule — the S05/S06
termination criterion — is **wrong as written and would have falsely terminated
BM-003**; it is replaced.

---

## Topic 1 — Compliance as a Joint between RigidGroups

### 1.1 Hypothesis under test

> Compliance needs no `CompliantRegion` family. It is adequately represented as a
> `Joint` of compliant type between `RigidGroup`s of one body, carrying mode,
> direction, bounded travel and an activation window.

### 1.2 Evidence inspected

- `EXE-BM001-02/parameters.yaml` — the three `compliant_regions` entries in full,
  and the `modelling_statement`.
- `EXE-BM001-02/DESIGN_AND_OPERATION_RATIONALE.md` — the installation sequence,
  the latch release and re-engagement cycle, the terminal bounds.
- `HUMAN_CAD_REVIEW_DECISIONS.yaml` HCR-BM001-002, -009, -010 — the directed
  snap-barb pin and the directed integral latch architecture.
- `ver3/oracles/held_out/BM-003/` ASM-BM-003-002 (`DEFORMATION_RESOLVED` path
  kind), NRM-BM-003-017 (deformation exception).
- BM-001 pack `evaluability_prerequisites.compliant_region_recorded`.

**The decisive line**, from `parameters.yaml`:

> *"Every compliant configuration is a **rigid translation of a declared
> region**. That is a DECLARED_KINEMATIC_APPROXIMATION: it conserves volume
> exactly and tests geometric passage and engagement. It does not model continuum
> deformation and predicts nothing about strain."*

The accepted reference already models compliance as a rigid sub-body at a pose.
The proposal is not introducing an approximation; it is *typing the one already
in use*.

### 1.3 Concrete dry-run — BM-001-02 cover

Nine capabilities, tested one at a time.

| # | capability | expressible? | how |
|---|---|---|---|
| 1 | multiple compliant members in one behaviour | **partly — see F-1** | four tabs, currently one "region" |
| 2 | deformation direction and bounded travel | **partly — see F-2** | joint axis + travel bound |
| 3 | activation only during specific transitions | **yes, but unchecked — F-3** | joint coordinate non-zero only in named transitions |
| 4 | force/deflection or reduced-order beam relations | **no — correctly, but hooks missing (F-4)** | no route exists |
| 5 | stress/strain or allowable-deflection evidence | **no — correctly (F-2)** | must become an `ExcludedClaim` |
| 6 | contact engagement while deformed | **yes, but causality is inverted — F-5** | interface measured in a deformed state |
| 7 | return to nominal rigid configuration | **yes** | joint coordinate returns to 0; the existing cycle-return check compares transforms exactly |
| 8 | assembly path feasible only under deformation | **yes, but unlabelled — F-6** | `AssemblyStep` swept with the joint at required travel |
| 9 | provenance requirement → behaviour → features → evidence | **yes** | Requirement → Obligation → Candidate(route verdict) → compliant Joint → Features → Realization → ExcludedClaim |

### 1.4 Failure modes found

**F-1 — a "region" is not one rigid group, and calling it one asserts a rigidity
that does not exist.**
`REG-COVER-RETAIN-LEFT-COMPLIANT` lists four features: two beams and two ears,
i.e. **two physically independent cantilevers**. Modelling them as one rigid
group forces them to move together. That is true of the *operation* (all four are
deflected simultaneously during ASM-02) and false of the *structure*.

For geometric passage it changes nothing. For anything else — an asymmetric load,
one tab that fails to recover, a future beam model — it is a false coupling.

*Correction:* one `RigidGroup` and one compliant `Joint` **per compliant member**
(four tabs → four groups, four joints). The "region" is not an entity; it is a
**set of compliant joints co-actuated by one transition** — exactly how BM-003's
`M1_UNFOLD` moves three legs. This is more truthful and costs nothing, because
the co-actuation already has a home.

**F-2 — required travel and allowable travel are conflated in one number, and
only one of them exists.**
`deflection_mm: 2.2` is the deflection *required for passage*. It is a kinematic
fact. What a material could *allow* is absent. As written, a design that required
20 mm of tab deflection would produce exactly the same structure and nothing
would notice.

*Correction:* two distinct fields. `required_travel` (authoritative, kinematic,
owned by S05) and `allowable_travel` (status `UNSUPPORTED`, naming the route that
would establish it). Their absence of comparison then becomes a machine-readable
gap rather than prose, and the `ExcludedClaim` for strain is generated from it
rather than authored.

**F-3 — `active_only_during` has no checker.**
It is a list of names. Nothing verifies that the joint coordinate is zero
everywhere else.

*Correction:* a deterministic check — in every state not in the activation set,
every compliant joint coordinate is 0. This is the compliant analogue of the
cycle-return check that already exists.

**F-4 — the hooks a reduced-order model would need are not identified.**
The features exist (`FEA-C-TAB-L1-BEAM`) but nothing says *this feature is the
beam* or *its root is here*. If a beam route ever becomes available (open question
O-4), the geometry it consumes cannot be located.

*Correction:* the compliant joint names its `compliant_element` feature and its
`root_interface`. Two reference fields. They cost nothing now and they are the
difference between "a beam model can be added later" and "the model must be
re-authored later".

**F-5 — the causality is inverted, and the model does not say so.**
On closing, the ramp meets the keeper corner and *that contact drives the
deflection*. In the model the joint coordinate is **prescribed**; nothing causes
it. The kinematics are right, the physics is absent, and a reader could take the
structure as evidence that the mechanism self-deflects.

*Correction:* an explicit `actuation: PRESCRIBED_KINEMATIC` field stating that no
force in this model produces the deflection. This is the same discipline the
videos already apply ("PRESCRIBED CAD KINEMATIC ANIMATION").

**F-6 — a deformation-resolved assembly path is indistinguishable from a rigid
one.**
ASM-BM-003-002 is explicit: *"A DEFORMATION_RESOLVED path MUST NOT be reported
PASS from rigid geometry alone… Required outcome without a compliance route:
NOT_VERIFIED."* Without a label on the step, a swept path computed with the tabs
held deflected reports PASS exactly like a rigid one.

*Correction:* `AssemblyStep.path_kind ∈ {RIGID, DEFORMATION_RESOLVED}`, and
`DEFORMATION_RESOLVED` forces the outcome to `NOT_VERIFIED`, never `PASS`.

**F-7 — retention that depends on recovery does not say so.**
HCR-BM001-002 directs: *"the recovered snap-barb shoulder blocks removal in the
other direction"*. The blocking relation exists **only if the barb recovers**. A
creep failure removes retention, and the model shows retention as unconditional.

*Correction:* a blocking relation whose validity depends on a compliant joint
returning to zero names that joint. One reference field, and it makes the
material dependency visible to S11 instead of invisible.

### 1.5 Does the proposal survive?

**Yes.** Every one of the nine capabilities is expressible, or is correctly
inexpressible for want of an evidence route. No failure mode requires a new
abstraction: all seven corrections are fields or a change of granularity on
entities the proposal already has. Notably, F-1 makes the model *simpler* — four
joints instead of one region plus a membership list.

The strongest evidence for survival is that the accepted reference already uses
this representation and says so. The proposal types an existing practice; it does
not impose a new one.

### 1.6 Downstream impact if this is wrong

If `Joint` + `RigidGroup` were insufficient, S03 could not decide *whether* a
design uses compliance, so S05 would be inventing a body's non-rigidity while
placing features — reintroducing the invention the whole architecture exists to
prevent. It would also make BM-001's accepted design inexpressible, which is the
fatal finding S-1 from the critical review. The blast radius is S03, S05, S07 and
every assembly claim.

---

## Topic 2 — LoadCase / LoadPath ownership

### 2.1 Hypothesis under test

> `LoadCase` is owned by S02 and exists before geometry. `LoadPath` is owned by
> S03 as a hypothesis and is confirmed spatially at S04·B. Together they prevent
> the pipeline falling back on "shaft → bearing".

### 2.2 Evidence inspected

- NRM-BM-002-006, -007, -011 in full, with derivation premises and exclusions.
- BM-002 `DESIGN_AND_OPERATION_RATIONALE.md` §2.3, §2.4, §5, §8.
- BM-001 NRM-BM-001-011; BM-003 NRM-BM-003-010 and AMB-BM-003-002/-005.

**Two lines decide this topic.** From NRM-BM-002-006's derivation premises:

> *"**Which components a given element carries depends on the conversion family
> selected, not on the requirement.**"*

And from its exclusions, recorded as closing finding **SF-5.3**:

> *"A cable drum carries no axial load; a rotating nut on a fixed screw reacts
> axially through the screw, not through a separate thrust feature.
> **Universalizing either reaction across all conversion families would encode
> one family.**"*

The Oracle was itself corrected for precisely the anti-pattern this topic is
meant to prevent. That is independent confirmation that the risk is real, and it
dictates the ownership split.

### 2.3 Concrete dry-run — five test cases

**Case A — radial support without axial load (BM-002 crank shaft).**
S02 emits: payload load case (gravity, on the platform role) and an actor-applied
torque (on the input role). Neither is axial to the crank axis. S03, for the
slider-crank candidate, traces the path: platform → platform pin → rod → crank pin
→ crank shaft → **housing journals** → ground. Each hop names its interface. The
crank shaft's *carried components* are then **derived** from the path geometry:
transverse, not axial. So no axial reaction is owed.

That is exactly BM-002's own conclusion — *"no axial force is produced in the
declared scenario… the collar is there so that pulling the handle does not pull
the crank out, which is a use case, not a load case"* — and the pipeline reaches
it without a magnitude. **Works.**

**Case B — payload and gravity (BM-002 platform).** Trivially expressible; the
magnitude 1 kg comes from S01's quantity inventory. **Works.**

**Case C — crank input and transmission reactions.** The actor-applied torque is a
`LoadCase` of kind `ACTOR_APPLIED`. Its path runs the chain in reverse to the same
reaction site. **Works** — provided `LoadCase.kind` distinguishes applied loads
from actuation, otherwise "the user turns the handle" is indistinguishable from
"a load is applied to the handle".

**Case D — contact-generated reactions (BM-003 leg blocking).** A user pushes a
deployed leg. The load has **no magnitude** (AMB-BM-003-005 carries none). The
path is leg → heel → ring arm → ring → pedestal → hub → ground.

Here the model nearly breaks — see F-8.

**Case E — load paths differing between candidates.** BM-002's rack-and-pinion
alternative would put the reaction in a completely different place. Because
`LoadPath` is owned by S03 *per candidate*, this is expressible directly, and the
paths become a legitimate discriminator at the S04·A gate. **Works, and is a
benefit the proposal did not claim.**

### 2.4 Failure modes found

**F-8 — the rule "no support is assigned before a load case exists" over-reaches
and would flood BM-003 with empty load cases.**
BM-003 has roughly twenty-four blocked directions. Every one is a *kinematic*
block: the claim is that a path is geometrically unavailable, which needs no
force at all. Requiring a `LoadCase` per blocking relation produces twenty-four
magnitude-free load cases that establish nothing and bury the two that matter.

*Correction:* scope the rule. It applies to **reaction interfaces appearing in a
`LoadPath`**, not to blocking relations. A kinematic block is justified by the DOF
disposition; a load-bearing support is justified by a load path. The Oracles draw
the same line: NRM-BM-003-010 is about *mobility*, NRM-BM-002-006 is about *load*.

**F-9 — a constraint can be required by the conversion rather than by a load, and
the proposal has only one driver.**
NRM-BM-002-007's exclusion is explicit: rotation must be restrained where *"(b)
the selected conversion needs rotational restraint of the driven body in order to
produce translation."* That is a kinematic necessity, not a load. If every
`BLOCKED_BY` must cite a load case, a lead-screw design cannot say why its nut is
anti-rotated.

*Correction:* every constraining relation records its
`driver ∈ {LOAD, KINEMATIC_NECESSITY, DECLARED_SCENARIO}`. Three values, one
field, and it prevents both over- and under-justification.

**F-10 — per-element load components must not be stored.**
If S03 writes "the crank shaft carries a transverse load" as a field, that field
is a candidate-independent-looking assertion about a candidate-dependent fact —
which is SF-5.3 reintroduced at the data level. A later stage reading the field
cannot tell whether it was derived from the path or asserted from the element's
type.

*Correction:* element load components are **derived from the `LoadPath`, never
stored**. The stored objects are the applied load and the path; what each element
carries is a projection. This is the single most important structural rule in
this topic.

**F-11 — a `LoadPath` at S03 is a hypothesis and the proposal does not type it as
one.**
BM-002's `CHG-02` is a load path that was topologically fine and geometrically
impossible: the rod occupies the crank axis, so the rear panel cannot journal the
shaft. A path with no maturity marker is indistinguishable from a confirmed one.

*Correction:* explicit maturity — `HYPOTHESIS` at S03 → `SPATIALLY_INSTANTIATED`
at S04·B (the reaction region is proven unoccupied across every state) →
`AUTHORITATIVE` at S06 (after placements settle). The proposal already says
"provisional until S04·B"; this makes it a typed three-step, matching the three
distinct things that must be true.

### 2.5 Does the proposal survive?

**Yes, with the ownership split made sharper than the proposal states it.** The
corrected division is:

| object | owner | content | candidate-dependent? |
|---|---|---|---|
| `LoadCase` | **S02** | scenario, applied-to role, direction class, kind, magnitude or `UNSUPPORTED` | **no** |
| `LoadPath` | **S03** | ordered hops, each naming its interface | **yes** |
| element load components | **derived** | never stored | yes, by construction |
| reaction interface | S03 assigns, S04·B confirms | an `Interface` appearing as a path terminus | yes |

The anti-pattern is blocked by construction: nothing can conclude "shaft →
bearing", because no element carries a load component except by appearing in a
path traced from a declared applied load through *this* mechanism.

### 2.6 Downstream impact if this is wrong

If the split is wrong in the direction of storing element loads, the pipeline
reproduces SF-5.3 — the exact defect the Oracle was corrected for — and every
support decision becomes unfalsifiable. If it is wrong in the direction of
requiring load cases for kinematic blocks, BM-003-class designs drown in empty
load cases and the real ones lose salience. Blast radius: S02, S03, and every
NRM-*-006/011-class invariant in every pack.

---

## Topic 3 — The S04·B → S05 → S06 → S04·B settlement loop

### 3.1 Hypothesis under test

> A bounded, dependency-driven settlement loop lets feature envelopes move joint
> placements without meaning "redo the whole design".

### 3.2 Evidence inspected

- BM-002 `CHG-01`, `CHG-02`, `CHG-03` with their affected-value lists and their
  *unchanged* results.
- BM-003 revisions R1, R2, R2a, R4 as recorded in `parameters.yaml`, and the R5
  regression.
- BM-003 `validation/` check inventory — which checks consume which values.

**The decisive observation.** All three BM-002 changes record:
*"**Resulting measured travel: 90.000000 mm, unchanged.** Travel is `2R` and `R`
was not touched."* A dependency cone is therefore not merely desirable — it is
**demonstrably discriminating** on real changes. Moving the crank axis invalidates
the bottom-dead-centre clearance check and provably not the travel check, because
the travel check's inputs do not include the axis height.

### 3.3 Concrete dry-run — the four required tests

**Test 1 — a feature dimension moves a joint-axis placement.**
BM-002 `CHG-01`. S04·B places `crank_axis_z` at 55.0, `PROVISIONAL`. S05 embodies
the crank pin: Ø10 shank, 4 mm wall → boss radius 9.000 → arm outer radius 54.000,
and emits an `EnvelopeConstraint`: *arm envelope must clear the floor by
`floor_clearance`*. S06 solves: least axis height satisfying it is
`4.0 + 2.0 + 45.0 + 9.0 = 60.000`. Placement promoted to `AUTHORITATIVE`.
**One loop iteration. No topology touched.** ✔

**Test 2 — a changed placement invalidates swept-volume checks.**
Same change. The cone marks stale: BDC arm/floor clearance, crank-pin height,
platform-pin height, plate height, guide-channel extent, rim height — and every
swept check consuming them. It does **not** mark: travel (inputs `R` only), rod
centre distance, journal clearances, guide-follower engagement widths. Re-run cost
is a fraction of S04·B. ✔

**Test 3 — a load-driven support change invalidates embodiment but not unrelated
topology.**
Suppose a load case revealed an axial component on BM-002's crank. Adding a thrust
face is a **new `Feature` on an existing `Interface`** → an S05 change, one loop
iteration, invalidating only checks touching that interface. But if the reaction
required a *new body or a new interface*, that is a `LoadPath` change → **S03
topology** → escalation, not iteration. ✔ *provided the boundary is stated —
see F-13.*

**Test 4 — a failed embodiment alternative causes local fallback, not global
restart.**
BM-003 R4: the hinge capture took three topologies — a clip in a blind pocket
(the retention chain does not terminate), a blind-bore-plus-head pin (cannot be
assembled), then a bayonet. Under the loop, each failure is a `RejectedAlternative`
at the *feature* level for one interface, with its reason. The joint, the bodies,
the DOF disposition and the assembly order are untouched. ✔

**Test 5 — the one that breaks the proposal.** BM-003 R1 → R4.
R1 changed `clevis_x0` 28 → 24 to fix hub connectivity. That put the clevis inner
corners at r = 24.74, inside the ring arms' 26 mm reach, so `ring_arm_r` was cut
to 23. Three revisions later the *lift-only* property — the fact that lifting the
ring without turning it does not free the legs — was found destroyed, because the
heel moves outward as it rises and now cleared the shortened arm.

Run this through the proposed loop and **it terminates prematurely**. See F-12.

### 3.4 Failure modes found

**F-12 — the proposed termination rule is wrong and would have falsely terminated
BM-003.**
The proposal says: *"each round must strictly reduce the unsatisfied constraint
set; a non-reducing round terminates the block."*

Replay R1 → R4. Round 1: arm/clevis clearance unsatisfied. Shrink the arm.
Round 2: arm/clevis satisfied, **lift-only now unsatisfied**. Set size unchanged
at one. Under the proposed rule the block terminates as `underdetermined` — yet a
solution exists and was found: shrink the arm **and** reduce `rib_h` 4.0 → 2.0,
which is what R4 actually did. The rule rejects a convergent problem.

*Correction:* terminate on **(a) a round budget**, and **(b) a repeated state**,
where a state is the pair (unsatisfied-constraint set, changed-parameter set). A
repeated state is a genuine cycle and is reported as one, with the cycle recorded.
Monotone reduction is not a property real constraint systems have.

**F-13 — the loop's scope boundary is stated in prose and must be a rule.**
Without it, "bounded" is aspirational. The line that makes the loop safe is
exactly the line the manual work drew between `CHG-01`/`CHG-03` and `CHG-02`:

*Correction:* the loop **may change** placements, dimensions and feature
alternatives. It **may not change** bodies, rigid groups, joints, interaction
kinds, the DOF disposition, load paths or assembly order. Any of those is an
**escalation to S03**, recorded as a `FailureProvenance` naming the owning
decision.

Applied to the record, this classifies correctly and without judgement:
`CHG-01` iteration, `CHG-03` iteration, `CHG-02` escalation (it required an
overhung crank — a different arrangement), BM-003 R1 iteration, R2 escalation
(a stop pad is new geometry realizing a previously undispositioned DOF), R4
iteration.

**F-14 — the loop cannot converge on an undeclared constraint, and R5 is that
failure.**
The arm/clevis clearance in BM-003 was never a declared `Constraint`. It surfaced
as a build failure and was patched by hand. Nothing reported infeasibility,
so nothing triggered a re-solve, so the lift-only regression rode along
undetected for three revisions.

*Correction:* S05 must emit a `Constraint` for **every declared clearance and
every declared interference-free pair**, not only for envelope constraints. For
BM-003 that is 34 constraints — trivial. Without it the loop has nothing to
converge *on*, and silent manual patching returns.

**F-15 — nothing bounds embodiment search separately from parameter search.**
A feature alternative is a much larger step than a parameter change, and a
pathological search could try alternatives indefinitely within the round budget.

*Correction:* two nested budgets — at most *K* feature alternatives per
unsatisfied constraint, inside at most *N* solver rounds. Exhausting *K*
escalates one level (feature → placement → dimension → S03), and every exhausted
alternative is retained as a `RejectedAlternative` with its reason.

**F-16 — "no candidate converges" has no defined outcome.**
*Correction:* the block terminates with the solver's own vocabulary —
`infeasible` with a named conflicting set, or `underdetermined` with the free
directions — plus a `FailureProvenance` routing to the S03 decision that owns the
conflict. It never terminates by silently accepting the last state, and it never
produces a design.

### 3.5 Does the proposal survive?

**Yes, but only after F-12 is corrected.** As written, the termination rule would
have rejected a problem we actually solved. That is a genuine falsification of one
clause — not of the loop.

The cone itself is confirmed rather than merely plausible: BM-002 records three
changes each with an explicit *unchanged* result, which is exactly the
discrimination a cone computed from declared check inputs would produce. The
scope boundary (F-13) reproduces the manual severity judgements with no
judgement required.

### 3.6 Downstream impact if this is wrong

If the loop is unbounded, S04·B–S06 becomes an agentic search with no
termination and the pipeline has no cost model. If it is bounded too tightly
(F-12 as written), convergent problems are reported `underdetermined` and the
pipeline fails on designs it could complete. If the scope boundary is absent,
every parameter change risks a topology rewrite and the loop does mean "redo the
whole design". Blast radius: S04·B, S05, S06, and the entire runtime cost profile.

---

## Final verdict

**B — safe with small contract changes.**

| topic | verdict | corrections |
|---|---|---|
| 1. Compliance as Joint + RigidGroup | **survives** | 7 field/granularity changes; no new abstraction |
| 2. LoadCase / LoadPath ownership | **survives** | 4 ownership rules + 1 derived-not-stored rule |
| 3. Settlement loop | **survives after correction** | 1 clause replaced, 4 rules added |

No architecture-level revision is required. Nothing in the three decisions was
falsified at the level of the decision itself; one *clause* of decision 3 was
falsified and is replaced.

---

## Exact changes required to `PIPELINE_IMPLEMENTATION_PROPOSAL.md`

Sixteen changes. To be applied in a later task, not now.

### Topic 1 — compliance (§3 S03/S05, §8, §11 D-2)

1. **C-1.** One `RigidGroup` and one compliant `Joint` **per compliant member**,
   not per region. A "region" is a *set of compliant joints co-actuated by one
   transition* and is not an entity.
2. **C-2.** Compliant joint carries **two** travel fields: `required_travel`
   (authoritative, kinematic, S05) and `allowable_travel` (status `UNSUPPORTED`,
   naming the route that would establish it).
3. **C-3.** Compliant joint carries `actuation: PRESCRIBED_KINEMATIC`.
4. **C-4.** Compliant joint names its `compliant_element` feature and its
   `root_interface`.
5. **C-5.** New deterministic check at S04·B: in every state outside the
   activation set, every compliant joint coordinate is 0.
6. **C-6.** `AssemblyStep` gains `path_kind ∈ {RIGID, DEFORMATION_RESOLVED}`;
   `DEFORMATION_RESOLVED` forces `NOT_VERIFIED`, never `PASS`
   (ASM-BM-003-002).
7. **C-7.** A blocking relation whose validity depends on compliant recovery
   names the joint it depends on.

### Topic 2 — load (§3 S02/S03, §6 rule 6, §8, §11 D-3)

8. **C-8.** `LoadCase` (S02) is **candidate-independent**: scenario, applied-to
   role, direction class, `kind ∈ {GRAVITY, PAYLOAD, ACTOR_APPLIED, REACTION}`,
   magnitude or `UNSUPPORTED`.
9. **C-9.** `LoadPath` (S03) is **per candidate**, and carries maturity
   `HYPOTHESIS` → `SPATIALLY_INSTANTIATED` (S04·B) → `AUTHORITATIVE` (S06).
10. **C-10.** Per-element load components are **derived from the path and never
    stored**. Cite SF-5.3 as the reason.
11. **C-11.** Rewrite design-space rule 6: *no **reaction interface in a load
    path** is assigned before a load case exists.* Kinematic blocking relations
    require no load case.
12. **C-12.** Every constraining relation records
    `driver ∈ {LOAD, KINEMATIC_NECESSITY, DECLARED_SCENARIO}`
    (NRM-BM-002-007 exclusion (b)).

### Topic 3 — settlement loop (§3 S06, §11 D-6)

13. **C-13.** **Replace** the termination rule. Not "strictly reduces the
    unsatisfied set" — that falsely terminates BM-003 R1→R4. Terminate on a
    **round budget** or a **repeated (unsatisfied-set, changed-parameter-set)
    state**, reporting the cycle.
14. **C-14.** State the loop's scope as a rule: it may change placements,
    dimensions and feature alternatives; it may **not** change bodies, rigid
    groups, joints, interaction kinds, the DOF disposition, load paths or
    assembly order. Those escalate to S03 with a `FailureProvenance`.
15. **C-15.** S05 must emit a `Constraint` for **every declared clearance and
    every declared interference-free pair**, not only envelope constraints.
    Without this the loop has nothing to converge on (BM-003 R5).
16. **C-16.** Two nested budgets: at most *K* feature alternatives per
    unsatisfied constraint inside at most *N* solver rounds; exhaustion escalates
    one level; every exhausted alternative is retained as a
    `RejectedAlternative`. Non-convergence terminates with the solver vocabulary
    plus a `FailureProvenance` — never with a design.

### Not changed

The three decisions themselves stand. No new entity family is required by this
check; the family count remains 37. The proposal's §9 consumer sufficiency
analysis is unaffected — none of these corrections changes what a stage hands
over, only what the handed-over objects contain.

---

*Evidence: `ver3/oracles/product_cases/BM-002/normative.yaml` (NRM-BM-002-006,
-007, -011 and finding SF-5.3); `ver3/oracles/held_out/BM-003/`
(ASM-BM-003-002, NRM-BM-003-017); `ver3/cad_validation/BM-001/executable_references/EXE-BM001-02/`
(`parameters.yaml` compliant regions and modelling statement, rationale);
`ver3/cad_validation/BM-001/reviews/HUMAN_CAD_REVIEW_DECISIONS.yaml`;
`ver3/cad_validation/BM-002/executable_references/EXE-BM002-01/DESIGN_AND_OPERATION_RATIONALE.md`
(CHG-01/02/03); `ver3/cad_validation/BM-003/executable_references/EXE-BM003-01/parameters.yaml`
(revisions R1, R2, R2a, R4). Nothing was implemented or modified.*
