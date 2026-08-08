# Pipeline critical design review — Stages 01–07

**Purpose.** Adversarial audit of the Stage 01–07 pipeline *before* it is built.
The question throughout is: *if we had actually run this pipeline while designing
BM-001, BM-002 and BM-003, would each Stage have discovered what it needed, when
it needed it, without forcing premature decisions or leaving downstream stages to
invent engineering content?*

**Method.** The benchmarks are used only as engineering thought experiments. The
evidence is the manual record: `CHG-01/02/03`, `DEF-01/02/03`, `R1–R8`,
`HUMAN_CAD_REVIEW_DECISIONS.yaml`, the Oracle packs and the three executable
references.

**Companion document.** `docs/PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md` is the
retrospective and the information plan. This document does not repeat it; it
attacks it, and it overturns two of its conclusions (§A5.3, §A7.2).

**Nothing is implemented here.** No code and no contract was modified.

**Verdict up front.** The pipeline is *structurally* sound — the patch model, the
ownership matrix and the status vocabulary are right, and they are right for
reasons Ver2 paid for. But it has **two fatal representational gaps that make it
unable to express designs we have already accepted**, one circular stage
ownership, and one economically infeasible gate. None of these is fixable
downstream. All four must be settled before S03 is implemented.

---

# Part A — the audit

## A1. Audit of the overall Stage sequence

### A1.1 The sequence is right; three of its six boundaries are not

S01 → S02 → S03 → S04 → S05 → S06 → S07 is the correct *order* of engineering
concerns: what was asked → what must be true → what things there are → where they
go and how they move → what geometry makes it real → what the numbers are → build
it. I found no argument for reordering.

Three boundaries fail the consumer test as currently drawn:

| boundary | verdict | why |
|---|---|---|
| S01→S02 | **correct** | S02 needs requirements, observables, scenarios, ambiguities. All are owned by S01 and none requires raw text. |
| S02→S03 | **incomplete** | S03 must assign supports and reaction paths. Nothing upstream says what load exists. See S-2. |
| S03→S04 | **internally inconsistent** | S03 owns `Joint.axis`, `parent_frame`, `child_frame`. It cannot know where the axis is. See S-3. |
| S04→S05 | **over-constrained and under-specified** | The selection gate at S04 demands full swept feasibility per candidate (infeasible, S-7); S04 does not emit an executable pose law (S-9). |
| S05→S06 | **wrong kind of boundary** | It is drawn as a sequential barrier. The information flows both ways. See S-11. |
| S06→S07 | **correct in spirit, too narrow in letter** | INV-006 is the right instinct. Its literal input list omits something S07's consumers need. See S-9. |

### A1.2 Information produced too early

**`Joint.axis` at S03** (S-3). BM-002's crank axis sits at y = 70, z = 60. The
z came from `4.0 + 2.0 + 45.0 + 9.0` — floor top, clearance, crank radius, and a
**pin boss radius that is a Stage 05 feature dimension**. `CHG-01` records the
first value, 55.0, producing 278.77 mm³ of arm inside the floor. So a metric
value owned by S03 was determined by S05 information and corrected only at CAD.
S03 is being asked to commit to a number it cannot derive.

**Nothing else is produced too early.** The prohibitions in the ownership matrix
are, if anything, too weak rather than too strong.

### A1.3 Information missing that later became necessary

Four classes, in severity order. Each is developed in §A2.

1. **Compliance** (S-1) — fatal. The pipeline cannot represent BM-001's accepted
   design.
2. **Load** (S-2) — fatal. S03 is required to assign supports with no
   representation of what they react.
3. **Functional regions** (S-10) — access, support, keep-out volumes.
4. **Evidence-route capability** (S-8) — known only at S08, needed at S02.

### A1.4 Is any stage forced to re-read the request?

No. INV-002 holds and the projections are adequate. This is the part of the
architecture that is most clearly correct, and the Ver2 row it retires (R-13) was
real.

But there is a **near-miss worth naming**: S08 must design negative controls, and
a control is only meaningful against the *intent* of a relation. If S08 authors
controls from the compiled geometry — which is what it will do, because that is
what is in front of it — it writes controls that defeat what the geometry
suggests rather than what the design claims. That is `DEF-01`, `DEF-02` and
`NC-17`, three times across three benchmarks. It is not a re-read of the request,
but it is the same defect one level down: **re-deriving intent from an artifact
instead of consuming it from a declaration.**

### A1.5 Contradictions between stage responsibilities

- **C-1.** S03 owns `Joint.axis` (metric, unit-bearing, in a named frame); S04
  owns `State.body_poses` (metric). A frame with no placement is a direction; a
  frame with a placement is a pose. Exactly one of these stages owns the
  placement and the contract does not say which.
- **C-2.** INV-006 gives S07 only the construction program and the resolved
  parameters. But every consumer of S07's output needs the **pose law** to put
  bodies in states. In all three references it lives inside `build.py` alongside
  the construction. Either S05 owns motion (contradicting S04's ownership of
  `State` and `Transition`) or S04 must emit an executable pose law and S07 must
  never see it. The contract currently implies the first and the artifacts do the
  first, while the ownership matrix says the second.
- **C-3.** `Witness` is owned by `[s04, s09]` and `NegativeControl` by
  `[s08, s09]`. Dual ownership of an entity family contradicts INV-001's single
  ownership principle; `ENTITY_FAMILY_AUDIT` flags both and defers them. They
  cannot be deferred past S04 and S08 respectively.
- **C-4.** `MobilityExpectation` requires `forbidden_dof` to be *declared*. The
  rule reads "Unintended-DOF checking requires the forbidden set to be declared,
  not inferred at check time." Correct, and insufficient: a declared set that
  omits a DOF cannot fail. See S-4.

### A1.6 Expensive representations created too early

Only one, and it is severe: **S04 at full swept fidelity, for every surviving
candidate, before selection** (S-7). See §A5.2.

Conversely, one representation is created **too late**: the negative control
(§A1.4).

---

## A2. Per-stage completeness audit

For each stage: its single engineering question, and then the categories of
mechanical-design information it must discover. The category list from the brief
is used as a probe, not as a checklist — several categories turn out to belong to
no stage at all, and saying so is the point.

### A2.1 Where each information class belongs

| class | owning stage | condition | status today |
|---|---|---|---|
| motion and DOF | S03 declares, S04 proves | always | **present but not total** (S-4) |
| support | S03 assigns | when a load case exists | **blocked** — no load case (S-2) |
| load path | S02 derives, S03 assigns, S04 proves geometrically | when any body carries a load | **missing family** (S-2) |
| reaction | S03 | with support | **missing** (S-2) |
| retention | S03 declares direction + blocker, S05 realizes | always | present via `MobilityExpectation` + `Interface`; **direction and blocker not required together** (GAP-01) |
| contact | S03 classifies, S05 gives features, S09 measures | always | correct |
| compliance | **S03** must decide *whether*, S05 realizes | when any obligation is discharged by deflection | **missing family — fatal** (S-1) |
| force / torque | nowhere | needs a material property route | **no route; must be declared UNSUPPORTED at S02** |
| travel limits | S03 declares, S05 gives the producing feature, S09 measures onset | always | present in the Oracles, absent from DesignState as a required pairing (S-13) |
| access | S03 declares region, S04 proves clear, S05 must not intrude | when an actor or a payload must reach something | **missing family** (S-10) |
| assembly | S03 owns order + strategy, S04 proves paths | always | ordering is **GAP-02, open** |
| service | S01/S02 as a distinct scenario | when disassembly is intended | **absent** — and it changes retention requirements |
| packaging | S03 topology + S04 envelope | when an enclosure is required | expressible; no explicit obligation |
| manufacturing | nowhere | — | **no route.** Declare at S02. |
| tolerance | nowhere | — | **no representation at all.** See S-12. |
| material behaviour | `material_class` only, as an Assumption | — | correct as far as it goes; may never be evidence |
| user interaction | S01 `Actor`, S03 access path, S04 reachability | when a human operates it | **not required to be geometrically realized** |
| failure states | S03, as the complement of the DOF disposition | always | **this is the right home and nothing occupies it** (S-4) |
| validation observables | S01 declares, S08 plans | always | correct |

Three rows deserve emphasis.

**Failure states = the complement of the DOF disposition.** BM-001's human review
found three failure modes by inspection: the pin walks out axially, the cover
lifts off at full open, the cam rotates out of its locked orientation. All three
are *a rigid-body DOF that nobody dispositioned*. A total DOF disposition at S03
is a mechanical FMEA, obtained for free from the joint graph. This is the single
highest-value change in this review.

**Service is a scenario, not an afterthought.** BM-001-02 declares service
disassembly explicitly — deflect four tabs, lift the cover out at the closed
position — and NRM-BM-003-003 scopes its no-removal requirement to *ordinary
operation* for the same reason. If service is not a declared scenario, then
either the design forbids service (over-constrained) or retention silently means
two different things in two contexts.

**Tolerance is absent and this is not neutral.** Every clearance in all three
references is nominal: 0.2, 0.4, 0.1, 0.15. `contact_tol` is an *evaluation*
tolerance and the BM-003 self-audit is explicit that it is "never a manufacturing
allowance". A 0.2 mm running clearance with no tolerance is not a manufacturable
statement, and "practical to manufacture" cannot be evaluated. This is a
permanent boundary of the current toolchain and must be declared as one at S02,
not rediscovered at S11.

### A2.2 The two fatal gaps

#### S-1 — Compliance has no representation, and BM-001's accepted design needs it

The human-directed final architecture for EXE-BM001-01 (HCR-BM001-010) is:
closure carries an exterior release pad, a compliant cantilever beam, a lead-in
ramp, a latch tooth and a retaining shoulder; enclosure carries a structurally
connected keeper face. EXE-BM001-02 is a cover with **four compliant retention
tabs** and **one compliant latch finger**, and it is installed by deflecting all
four tabs 2.2 mm inboard.

`parameters.yaml` carries what the design actually needs:

```
compliant_regions:
  - id: REG-COVER-RETAIN-LEFT-COMPLIANT
    body: BODY-COVER
    members: [FEA-C-TAB-L1-BEAM, FEA-C-TAB-L1-EAR, ...]
    deflection_mm: 2.2
    direction: inboard, +Y
    active_only_during: [ASM-02, declared service disassembly]
```

Nothing in `DESIGN_STATE_CONTRACT.yaml` can hold this. A `Feature` is a single
named geometric feature on a body. A compliant region is *a set of features, plus
a deformation mode, plus a magnitude and direction, plus an activation window
naming the operations during which the body is not rigid.*

The Oracles require it independently and in three places:
`evaluability_prerequisites.compliant_region_recorded`; the
`DECLARED_COMPLIANT_INTERACTION` interaction kind; and NRM-BM-003-017's
deformation exception with ASM-BM-003-002's `DEFORMATION_RESOLVED` path kind,
which requires "the region and the intended deformation mode".

`ENTITY_FAMILY_AUDIT.yaml` did not find this because it declared its own scope
away: *"NO FAMILY WAS ADDED OR DELETED BY THIS AUDIT."* It asked whether each of
the 32 existing families has a consumer. It never asked whether there is
engineering content with no family. That is a real methodological hole and it
hid a fatal gap.

**Consequence if unfixed.** Run the pipeline on BM-001 and S05 must emit a
compliant tab. It can emit the tab's geometry as a `Feature`. It cannot say that
the tab deflects, by how much, in which direction, or during which operation. S07
compiles a rigid tab. S09 sweeps a rigid assembly and reports interference on the
one insertion path the design has. The pipeline concludes the accepted design is
unassemblable.

**Where the decision belongs.** *Whether this design uses compliance* is an S03
decision, not an S05 one, because it determines the assembly strategy (the
retention trichotomy in §A3.4) and the evidence route (S-8). S05 owns the
region's geometry; S03 owns its existence.

#### S-2 — There is no representation of load, and S03 cannot assign supports without one

There is no `LoadCase`, no `LoadPath`, no reaction entity. `Scenario` (S01) has
`system_boundary`, `actors`, `environment` — a usage scenario, not a load case.

The Oracles quantify over loads directly:

- NRM-BM-002-006: "**Every element that carries a transverse or radial load in
  the declared operating scenario** has a realized radial support." You cannot
  evaluate a universally quantified statement whose domain you cannot compute.
- NRM-BM-002-011, NRM-BM-001-011: a load path to a reaction site must exist.
- Oracle `stage_expectations` s03 `must_exist` includes `load_path_ownership`,
  and s05 includes `load_path_records`.

And the manual work reasoned about loads constantly, in prose the pipeline cannot
hold. BM-002 §2.4, on the crank shaft's axial location:

> This is recorded as a **handling design choice, not as a discharge of
> NRM-BM-002-006.** The whole mechanism lies in the YZ plane and every joint axis
> is parallel to X, so no axial force is produced in the declared scenario.
> Demanding a thrust feature where no axial load exists is exactly the error
> corrected at SF-5.3.

That paragraph distinguishes a *use case* from a *load case* and refuses to
discharge an obligation with a feature that reacts nothing. It is correct
engineering and the pipeline has nowhere to put it.

**Consequence if unfixed.** S03 assigns supports by pattern-matching on joint
type ("a revolute needs a bearing"), which is R-10 — role→geometry — in a new
costume. It will demand a thrust face on BM-002's crank and it will not be able
to say why BM-002's guides carry a *lateral* load but not a vertical one.

**Minimum viable form.** Not FEA. A `LoadCase` needs: the scenario, the applied
load's body and direction class (transverse / axial / moment / gravity), and
whether a magnitude is known or `UNSUPPORTED`. A `LoadPath` is an ordered body
chain from the load to a reaction site, each hop naming the `Interface` that
carries it. Both are **symbolic and directional**; neither needs a number. BM-002's
load-path graph in §8 of its rationale is exactly this shape and was written by
hand.

### A2.3 The severe defects

**S-3 — Joint axis ownership is circular.** Split it: S03 owns the joint's
*existence, type, participating bodies, DOF and axis direction class*; S04 owns
the axis's *metric placement*. `Joint.axis` becomes a direction at S03 and gains a
located frame at S04. This is not bureaucracy — it is the difference between "the
crank turns about an axis parallel to X" (knowable at S03) and "that axis is at
z = 60" (not knowable until the arm's envelope exists).

**S-4 — The forbidden set must be total, not merely declared.** Today
`MobilityExpectation` requires `intended_dof` and `forbidden_dof`. Nothing
requires their union to cover every rigid-body DOF of every body in the
configuration. Both BM-001's cam and BM-003's over-swing were **omissions from a
declared set**. Change the requirement to a total function: for every body, in
every configuration, every DOF maps to exactly one of
`INTENDED | BLOCKED_BY(relation) | MAINTAINED_BY_CLASS(class) | IRRELEVANT_BECAUSE(reason)`.
Totality is mechanically checkable; declaration is not. No new family is needed —
this is a field-level change to an existing one, which respects the audit's own
discipline.

**S-5 — The invalidation cone is attached to the wrong entity.**
`invalidation_cone` exists, on `FailureProvenance`, owned by **s12**. So
invalidation happens only after a failure has been attributed at the end of the
pipeline. BM-003 `R5` is the counter-example: shortening `ring_arm_r` in revision
R1 silently destroyed the lift-only property, and nothing was marked stale
because nothing had failed *yet*. The cone must be on `StagePatch`, computed when
the change is made, not when its consequence surfaces.

**S-6 — Negative controls are authored two stages too late.** `NegativeControl` is
owned by `[s08, s09]`. Move authorship to the stage that owns the relation: every
`BlockingRelation`, retention and limit carries a **defeat specification** —
"remove feature F from body X, and nothing else" — emitted with the declaration.
S08 schedules and parameterizes; it does not invent. This is the direct fix for
`DEF-01`, `DEF-02` and `NC-17`, and it also fixes the second half of `NC-17`: a
control must assert that any *surviving* stop names a **different blocker**, which
is only expressible if the blocker was named in the first place.

**S-7 — The selection gate is at the right place and the wrong fidelity.** See
§A5.2.

**S-8 — No stage owns the evidence route.** BM-001's `REFERENCE_SELECTION.yaml`
rejects four admissible Oracle fixtures — B, D, F, G — because their *primary*
geometry depends on flexure strain, friction margin or hoop strain, "both
material questions this toolchain cannot answer. Building it would make the pilot
rest on assumptions rather than geometry." BM-002 chose a design with no press,
snap or interference fit anywhere. BM-003 declared `SMC-KINEMATIC_BLOCK` because
it is the only one of four classes with an available route.

Three benchmarks, three times the mechanism was chosen partly for what could be
evidenced. Each was recorded; none had an owner. Verification planning is S08 —
*after* the geometry is compiled. Move the classification to S02, as a field on
`Candidate`, and re-check it at S03 when a realization class or state-maintenance
class is declared.

**S-9 — S07's input restriction omits the pose law.** See C-2. Resolution: S04
must emit a typed, executable `PoseLaw` per moving body — a transform expression
parameterized by joint coordinates and by S06 parameters. S07 compiles bodies in
their as-built pose and nothing else. The evidence engine composes poses from
S04's pose law. This makes S07 *more* purely a compiler, and it extracts the one
piece of design information that was hiding inside `build.py` in all three
references.

**S-10 — Functional regions have no family.** BM-001's 84 mm usable access is a
declared volume that a Stage-05 feature violated: a latch finger on the centreline
"retracts *into the aperture* at full open and stands in the way of the 84 mm the
design promises." Oracle `stage_expectations` s04 already requires
`declared_usable_access_region`. The region must be an entity, declared at S03
with a role, given a metric volume at S04, and re-checked whenever S05 places a
feature.

**S-11 — S05/S06 is drawn as a barrier and must be a bounded loop.** See §A5.3,
where I overturn a conclusion of the companion document.

**S-12 — Tolerance, manufacturing process and material properties have no route.**
Not a defect to fix; a boundary to declare. See §A2.1.

**S-13 — A declared limit is not required to name its producing feature.**
NRM-BM-001-005, NRM-BM-001-012 and NRM-BM-002-009 all exist because an asserted
terminal pose is the classic failure. All three references had to invent a
producing feature — a flange, a boss, a ring arm, a stop pad. Make the pairing a
required field, not an Oracle-side check.

---

## A3. Adversarial replay on the three benchmarks

Running the *proposed* pipeline mentally, and asking where each fact would first
appear.

### A3.1 BM-001 — the eight things opening and closing requires

| requirement | first knowable at | pipeline as drawn | with the fixes |
|---|---|---|---|
| a supported DOF | S03 | ✓ `Joint` | ✓ |
| a physical motion carrier | S03 | ✓ `Body` with role | ✓ |
| retention | S03 obligation → S05 realization | ✓ but **direction not required with blocker** | ✓ `BlockingRelation` |
| release | S03 | ✓ as a transition | ✓ + actor access path |
| **compliant-force reasoning** | S02 (route), S03 (existence), S05 (region) | ✗ **cannot be represented** | ✓ `CompliantRegion`, force still `UNSUPPORTED` |
| contact geometry | S03 kind → S05 features | ✓ | ✓ |
| a physical stop | S03 declares → S05 produces | ✗ pairing not required (S-13) | ✓ |
| assembly feasibility | S03 strategy → S04 path | partial — GAP-02 open | ✓ |

**Where the pipeline breaks.** The compliant row. Everything else survives.

**The three human-review findings, replayed.** With a **total** DOF disposition
at S03, all three are caught before any geometry exists:

- The hinge pin has an axial DOF. Dispositioned, someone must write
  `BLOCKED_BY(?)` for **each direction** — and there is no relation for the
  second direction. HCR-BM001-002, caught at S03.
- The cover at full open has a vertical DOF. `BLOCKED_BY(rail lip)` must hold *in
  every configuration*, and the configuration set includes full open.
  HCR-BM001-004, caught at S03.
- The cam has a rotational DOF about its own axis with nothing blocking it.
  HCR-BM001-006, caught at S03.

**The one it would still miss.** HCR-BM001-008 — that implementing the latch as a
separate body plus knob, shaft, boss and socket is *disproportionate to its
function*. No check catches this. It is an engineering-judgement rejection and it
belongs to human review. The pipeline should surface the input for it: a
part-count and feature-count per discharged obligation, reported, not scored
(R-16 forbids scoring). **Being able to see it is achievable; deciding it is not.**

### A3.2 BM-002 — eleven questions, and the two that would be fixed too early

| question | first knowable at | fixed too early? |
|---|---|---|
| user input modality | S01 — "rotate an external hand crank" is stated | no |
| lifting behaviour | S01 — stated with a band | no |
| candidate transformations | S02 | no, if candidates persist |
| reaction / load path | **S02 load case → S03 assignment** | ✗ **no representation** |
| guidance | S03 (from the DOF disposition: the platform's lateral DOF must be blocked) | no |
| anti-rotation | S03 (the platform's three rotational DOF) | no |
| back-drive | S02 as a *question*; S09 as evidence | no — but see below |
| assembly direction | **S03 order, S04 feasibility** | ⚠ see below |
| access | S03 region, S04 occupancy | ✗ no family |
| packaging | S03 topology, S04 envelope | no |
| support placement | **S03 — and this is the trap** | ✗ **yes, fatally** |

**Support placement is fixed too early, and CHG-02 is the proof.** The
provisional layout said the rear panel carries the second crank-shaft journal.
S03 would assign exactly that: two bodies, an interface, a plausible reaction
path. It is geometrically impossible — the connecting rod **occupies the crank
axis**, measured 64.0 mm³ of rod inside a 4×4×4 probe on the axis, minimum
distance 0.0000. Nothing at S03's maturity can see this. It needs swept occupancy
of the axis over a full crank revolution, which is S04/G4.

**Therefore: a support assignment made at S03 is PROVISIONAL until S04 proves the
region is unoccupied over every state.** That is a design-space rule (§A5.4), not
a stage move.

**Assembly direction is the genuinely hard case.** BM-002's shaft must enter from
+X "because the only other direction would require the crank arm (radius 54.000)
to pass a 35.200-radius bore." That reasoning is metric. Can S03 own direction?
Honest answer: **S03 can own the assembly *strategy* and the *partial order*;
direction feasibility belongs to S04.** The companion document assigned both to
S03 and that was too strong. Recorded as open question **Q-1**.

**Back-drive deserves a note.** It is a *question* at S02 — "is this transmission
self-locking?" is a property of the mechanism family, answerable from the
capability library before any geometry. A worm drive answers yes; a slider-crank
answers no. BM-002's simulation measured it, but the *expectation* was knowable
at S02 and would have been a useful discriminator between candidates.

### A3.3 BM-003 — which findings were painfully late, and why

| finding | earliest stage that could catch it | why it was late |
|---|---|---|
| R2 no outward stop | **S03** | forbidden set was declared, not total (S-4) |
| R6 ring seat must be derived | **S05→S06 loop** | derivation had no home; a number was chosen where a relation belonged |
| R3 pad inside the hinge eye | **S05→S06 loop** | feature envelope constraint had no representation |
| R7 assembly must end deployed | **S03/S04** | assembly treated as a check, not a driver |
| R4 hinge capture, three attempts | **S03** | the retention trichotomy was not a planning input |
| R5 lift-only property lost | **invalidation cone at patch time** | cone exists only at s12 (S-5) |
| R1 hub built as 7 solids | **S07** | genuinely not earlier — B-rep connectivity |
| R8 accidental blocker | **S03 declaration + S08 scheduling** | control authored from geometry (S-6) |

**Seven of eight were knowable before CAD.** Only R1 is a true Stage-07
discovery. That ratio — and the identical ratio in the companion document's
fourteen-item table — is the strongest single argument in this review: *the
pipeline's problem is not that geometry starts too late, it is that checks run
several maturity levels above where their information already exists.*

**Oracle predicates and negative controls.** BM-003's Oracle was authored
*independently and frozen before* the CAD, which is correct and must not change.
But note what the CAD had to do: declare a state-maintenance class, declare a
forbidden set, and — for NC-17 — declare a numeric bound
(`outward_travel_max_deg = 3.0`) that exists *only* because a predicate could not
otherwise discriminate. That bound is a fixture invention forced by a control
failure. Under S-6 it would have been declared at S03 as part of the blocking
relation ("outward travel beyond X is forbidden"), which is where a design states
its own intended mobility, and NRM-BM-003-010 explicitly asks the design to do
exactly that.

### A3.4 Successes that should move earlier

Three representations made the manual work dramatically easier. All three should
be pipeline outputs, not CAD conveniences.

1. **The declared-interaction table with a `kind` per body pair.** All three
   references converged on `interactions.yaml` independently. It is what makes a
   clearance measurable rather than a whole-body distance. **Belongs at S03**
   (kind) **and S05** (feature pair and nominal).
2. **Region-of-interest measurement.** Measuring inside a declared region is what
   stops a clearance being masked by a contact elsewhere on the same pair. BM-002
   went further and made ROIs *follow the joint axis*, "recomputed from the pin
   solid's own bounding box at each state, so the measurement is of the joint
   wherever the joint happens to be." **Belongs at S05**, as part of the feature
   declaration.
3. **The retention trichotomy.** Derived on BM-003 R4 and confirmed on the other
   two: a rigid part installed by one straight translation always leaves the
   reverse direction open, so retention needs a later body (BM-002's rear panel),
   a rotation (BM-003's five bayonets), or elasticity (BM-001's snap barb).
   **Belongs at S03**, as a required field on the assembly plan, and it is a
   knowledge-base rule.

---

## A4. Geometry maturity — earliest useful, latest safe, authority

Eleven levels. The two columns that matter are **earliest useful** and **latest
safe**; the gap between them is exactly where exploratory geometry is legitimate.

| # | level | earliest useful | latest safe | authority when first created | what can still change | checks that become possible |
|---|---|---|---|---|---|---|
| **L0** | no geometry | S01 | S02 | — | everything | requirement/obligation coverage |
| **L1** | body & shape class | S02 | S02 | NONE | count, split, roles | obligation ownership; candidate comparability |
| **L2** | topology — bodies, joints, interfaces, DOF | S02 (sketch) | **S03** | PROVISIONAL → AUTHORITATIVE at S03 | any metric | **DOF totality**; graph acyclicity; interface classification; retention direction algebra |
| **L3** | symbolic spatial relations — adjacency, sidedness, direction classes | S03 | S03 | AUTHORITATIVE | all magnitudes | escape direction = −blocking direction; load-path connectivity; access-region role |
| **L4** | frames and axes (direction only) | S03 | S03 | AUTHORITATIVE | axis *placement* | axis parallelism/perpendicularity; DOF consistency with joint type |
| **L5** | envelopes | **S03 (scout)** | S04 | PROVISIONAL at S03, AUTHORITATIVE at S04 | internal features | gross packaging; enclosure fit; **cheap interference by AABB** |
| **L6** | poses per state | S04 | S04 | AUTHORITATIVE | feature detail | static interference; region occupancy per state; reach |
| **L7** | motion paths & swept occupancy | S04 | S04 | AUTHORITATIVE | features, dimensions | **path interference (not endpoints)**; swept occupancy of a support region; captivity across travel; assembly insertion feasibility; anti-rotation probes |
| **L8** | feature-level embodiment | S05 | S05 | AUTHORITATIVE (shape), UNSOLVED (size) | every dimension | feature-pair completeness per interaction; limit producers; ROI definition |
| **L9** | parameterized construction intent | S05 | S05 | AUTHORITATIVE | parameter values | program totality; unit presence; **envelope constraints from features**; parameter dependency cycles |
| **L10** | solved geometry | S06 | S06 | AUTHORITATIVE | nothing, absent a revision | residuals; active set; feasible/infeasible/underdetermined |
| **L11** | CAD solids | S07 | S07 | AUTHORITATIVE & FROZEN | nothing | validity; **single connected solid**; volume; round-trip; determinism |
| **L12** | verified geometry | S09 | S09 | EVIDENCE | — | every declared predicate measured on its named feature |

### A4.1 Where CadQuery is a scout and where it is authoritative

**Authoritative: S07 only.** Unambiguous.

**Scout: from S03 onward, under a hard contract.** The evidence that this is
needed is overwhelming — BM-002 `CHG-01`, `CHG-02`, `CHG-03`, BM-003 `R1`, `R3`,
`R5`, and BM-001's latch-finger/aperture conflict would *all* have been visible in
a throwaway solid built one or two stages before they were actually found.
Forbidding exploratory solids is precisely what pushes these discoveries to L11.

The rule that prevents a scout value from becoming a design decision is not
process discipline — it is a **type restriction**:

> A `ScoutFinding` may only **raise**, never **set**.
> It may raise an `UnresolvedDecision`, propose a `Constraint`, or report a
> measured conflict. It may never supply a value, a pose, a form or a placement.

Plus four supporting rules: it may not CREATE or EXTEND any DesignState entity;
it records the `parent_state_hash` it was built from and must be re-derivable
from it; S07 must never read it; and **every scout finding must be discharged** —
by an entity change the owning stage makes for its own reasons, or by a recorded
decision not to. An undischarged finding blocks the stage gate.

Under those rules the scout is exactly what the three `CHG` records already were:
a measurement that forced a decision, made by the stage that owns the decision.

**The residual risk is real and unfixable by contract** (Q-5): nothing
mechanically stops a number discovered in a scout from being typed into a
parameter with a plausible rationale. The only defence is that a parameter's
provenance must cite a `Constraint`, and the constraint must be derivable from
the state without the scout.

---

## A5. Design-space preservation

### A5.1 What is being decided before the evidence exists

| decision | currently taken at | evidence needed | verdict |
|---|---|---|---|
| mechanism family | S02, as persisting branches | — | **correct.** INV-007 and R-15/R-16 are right and hard-won |
| support type and location | S03 | load case (S-2) + swept occupancy (L7) | **premature** — CHG-02 |
| joint axis placement | S03 | feature envelopes (L8) | **premature** — CHG-01 (S-3) |
| dimensions | S06 | assembly path (L7) | **premature unless the loop exists** — BM-002 hub Ø |
| layout | S03/S04 | swept volume (L7) | correct if S04 precedes S05 |
| material | never fixed; declared as a class | — | **correct** |
| contact geometry | S05 | the required interaction (S03) | correct |
| compliance | nowhere | — | **cannot be taken at all** (S-1) |
| evidence route | S08 | — | **far too late** (S-8) |

### A5.2 The selection gate is economically infeasible as drawn

INV-007 forbids a `SelectionDecision` before S03/S04 feasibility evidence exists
for every retained candidate at equal obligation coverage. The principle is
correct — Ver2's R-15/R-16 (selection before evidence, scored by part count, so
*incompleteness wins*) is one of the worst defects in the retirement matrix.

But count the cost. The BM-001 Oracle lists **7 admissible physical fixtures**;
BM-002 lists 5. S04 at full fidelity means poses, paths, swept volumes and
assembly sweeps for every one. **The manual process never did this and could not
have afforded to.** It carried two candidates for BM-001 and one each for BM-002
and BM-003, and it discriminated informally using evidence-route reasoning.

So the architecture demands something we have never done and have no evidence is
affordable. Two ways out, and only one is acceptable:

- ✗ Weaken INV-007 and let a cheap heuristic select. This is R-15 again.
- ✓ **Split S04 into two fidelities.**
  - **S04a — envelope and reach feasibility (L5/L6).** Cheap: AABB envelopes,
    endpoint poses, gross packaging, access reach. Run on **every** retained
    candidate. Eliminates candidates that cannot fit or cannot reach.
  - **S04b — swept occupancy and path feasibility (L7).** Expensive. Run on the
    survivors of S04a.
  - The `SelectionDecision` gate sits **after S04b**, unchanged. What changes is
    that most candidates die at S04a for a stated geometric reason, at a
    fraction of the cost.

This is not a new stage — it is a declared two-pass structure inside S04 with two
distinct fidelity levels, which the `Witness.fidelity` field already supports.

### A5.3 Overturning a conclusion of the companion document: S05/S06

The companion document recommended "bounded iteration between S05 and S06". That
is right about the information flow and **wrong about the mechanism**. Two stages
that must iterate are not two stages; they are one stage with an internal loop,
and calling them two invites a sequential implementation that then needs a
re-entry path bolted on.

But merging them and renumbering is worse: the Oracle packs are **frozen** and
their `stage_expectations` reference `s05` and `s06` by name, with distinct
`must_exist` lists (`construction_program`, `solver_problem` at s05;
`solved_values_or_explicit_status`, `constraint_residuals`, `active_constraints`
at s06). Renumbering invalidates frozen artifacts for a cosmetic gain.

**Recommendation.** Keep the numbering and both contracts. Change the *boundary
semantics* from a barrier to a **bounded convergence block**:

- S06 is a **deterministic solver service**, not a sequential pass. It may be
  invoked by S05 repeatedly within one stage attempt.
- S05 may not set a `Parameter` value except by citing a solver artifact. This is
  what stops R-23 ("copying existing values and calling them solved") without
  needing a sequential barrier to enforce it.
- The loop is bounded: a declared maximum round count; **each round must strictly
  reduce the set of unsatisfied constraints**; a round that does not terminates
  the block with `underdetermined` or `infeasible` and a named conflicting set.
- Every round is a `StagePatch` with `stage_attempt` incremented, and both
  attempts are retained.

### A5.4 Design-space preservation rules

1. **A decision may be taken only when its discriminating evidence exists, and
   the decision names that evidence.** A decision citing no evidence is `OPEN`.
2. **Exactly three legal states for any decision:** `RESOLVED` (with evidence),
   `BOUNDED` (a range or set, with the reason it cannot narrow), `OPEN` (with
   alternatives and what would settle it). There is no fourth, and silence is not
   a state.
3. **Symbolic before metric.** Never write a number where a relation will do.
   BM-003's ring seat is derived from the heel's actual position rather than
   chosen; that is why the blocking gap survived eight revisions.
4. **A support assignment is PROVISIONAL until swept occupancy confirms the
   region is free in every state.** (CHG-02.)
5. **No dimension is frozen before the assembly path that constrains it.**
   (BM-002 hub Ø = journal Ø.)
6. **No support is assigned before a load case exists**, even a purely directional
   one. (BM-002 §2.4.)
7. **Material class may be declared; it may never be evidence** until a property
   route exists.
8. **Evidence-route capability is a decision input.** Choosing a mechanism partly
   because it can be evidenced is legitimate and must be recorded as such — with
   the coverage gap it creates.
9. **Candidate branches die by stated geometric reason, not by score.** Element
   count is never an input (R-16).

---

## A6. Back-propagation: the earliest maturity at which each check is meaningful

For each check: the minimum information, the cheapest maturity at which it means
something, where it should run, and what cheaper approximation can run earlier.

| check | minimum information | cheapest meaningful level | run at | cheaper proxy earlier |
|---|---|---|---|---|
| DOF completeness | joint graph | **L2** | S03 | none needed — it is enumeration over a known set |
| retention direction | blocking relation with a named blocker | **L3** | S03 | direction algebra: an escape direction must be the negation of a declared blocking direction |
| support completeness | load case + joint graph | **L3** | S03 | every load-carrying body has ≥1 path to a reaction site |
| interference, static | envelopes + poses | **L5** | S04a (AABB) → S04b (exact) | AABB is conservative: no-overlap is a proof, overlap is not |
| swept occupancy | poses + path | **L7** | S04b | AABB sweep of the path |
| assembly insertion | path + already-placed set | **L7** | S04b | straight-line AABB sweep in the preceding configuration |
| anti-rotation | DOF disposition + geometry | **L7** | S04b | rotate the envelope by a declared angle and re-test |
| travel limits | producing feature pair | **L8** declared, L12 measured | S05 / S09 | at S04b: does *any* body pair meet at the limit pose? |
| contact engagement | feature pair + ROI | **L8** declared, L12 measured | S05 / S09 | at S04b: an engagement site exists and the two bodies are co-located there |
| force threshold | material properties + load magnitude | **no level available** | — | none. Declare `UNSUPPORTED` at S02 |
| back-drive | dynamics, or a self-locking geometry class | L12 for evidence | S09 | **at S02**: the capability library knows whether the transmission family is self-locking |
| CAD/simulation parity | solids + simulation model | **L11** | S09 | **structural, at S04**: if the sim topology is a *projection* of the joint graph rather than a re-derivation, parity is guaranteed by construction |
| negative controls | the declared relation | **L2/L3** | authored S03/S05, executed S09 | — |

Two rows carry most of the value.

**CAD/simulation parity becomes structural rather than checked.** BM-002's
simulation re-derived the multibody topology from the CAD — which bodies are
welded, how the closed loop is closed, that "3 joint DOF minus 2 independent
constraint rows in the plane = 1 net DOF". If S03's joint graph is rich enough to
*project* into a MuJoCo model, there is nothing to check: the two cannot
disagree. That is a reason to make S03's joint output simulation-complete, and it
costs nothing extra.

**Negative controls are authored at L2/L3 and executed at L12.** This is the
largest single move in the table: from S08 back to S03/S05.

---

## A7. Representation audit

### A7.1 The three options, judged on the failures

- **Separate stage outputs — rejected.** BM-002 `CHG-01` changed one parameter and
  eight derived heights followed; `CHG-03` then changed one of those again.
  Manual propagation is what BM-003 `R5` records the failure of. Separate files
  with no shared identity also produced the BM-003 mixed artifact directory and
  the BM-002 manifest incident that `manifest_util` was written after.
- **One shared mutable state — rejected.** Ver2's Stage 05 kept its own truth
  store (R-19) and created a second design world. Direct mutation makes ownership
  advisory, and ownership is the mechanism INV-001 depends on.
- **DesignPatch onto one shared DesignState — accepted**, which is what the
  contracts already specify. `parent_state_hash` rejects a patch computed against
  one world and applied to another; `execution_status` and
  `declared_incompleteness` let a degraded run report itself as degraded;
  retaining attempt *n* makes the S05/S06 loop auditable.

### A7.2 Overturning a second conclusion: maturity must be a field, not a stage

The companion document treated geometry maturity as a property of *stages*.
That is not sufficient. Within a single S04 patch there will be envelopes that
are AUTHORITATIVE and axis placements that are still PROVISIONAL pending S05
feature envelopes (S-3). Within a single S05 patch there will be feature shapes
that are AUTHORITATIVE and feature dimensions that are UNSOLVED.

**Maturity must be a first-class field on every geometric value**, with a small
vocabulary: `SYMBOLIC | PROVISIONAL | AUTHORITATIVE | FROZEN`. Without it there is
no way to distinguish a scout-informed placeholder from a solved value, and no
way for a check to refuse to run on immature input — which is how a proxy result
gets cited as a CAD result.

### A7.3 The representation principles the pipeline cannot work without

Not a schema. Eight principles, each traceable to a specific failure.

1. **One entity per real thing, with a stable opaque ID.** (INV-001; R-19, R-20.)
2. **Patches carry the parent state hash.** (Mixed-run artifacts.)
3. **Maturity on every geometric value.** (§A7.2.)
4. **An invalidation cone on every patch, not only on failure.** (BM-003 R5;
   S-5.)
5. **Provenance distinguishes four origins:** `SourceClause`, derived-from-
   constraint, `Assumption`, `ScoutFinding`. A value whose provenance is a scout
   is inadmissible as authoritative. (`Assumption` exists; `ScoutFinding` does
   not.)
6. **Three-state decisions** — `RESOLVED` / `BOUNDED` / `OPEN`. (§A5.4 rule 2.)
7. **Every constraining relation carries its defeat specification.** (S-6;
   `DEF-01`, `DEF-02`, `NC-17`.)
8. **Run identity on every artifact outside the DesignState**, and a manifest
   over a mixed set is refused rather than written. (`manifest_util`'s own
   history; BM-003's quarantine directories.)

### A7.4 What is redundant

- **`Configuration` (s03) vs `State` (s04).** `Configuration` is
  `[bodies_present, expected_mobility]`; `State` is `[joint_coordinates,
  body_poses]`. These are the same concept — a named arrangement — at two
  maturities, one for assembly and one for operation. Recommend one family with a
  `kind` and a maturity field, rather than two families that will need a mapping.
- **`MobilityExpectation` vs the proposed DOF disposition.** No new family:
  make `forbidden_dof` total. This respects `ENTITY_FAMILY_AUDIT`'s discipline of
  not inflating the family count.
- **`Witness` dual-owned by `[s04, s09]`** and **`NegativeControl` dual-owned by
  `[s08, s09]`.** Both contradict single ownership. Resolve as: the *declaration*
  is owned by the earlier stage, the *result* is an `EvidenceItem` owned by s09.

---

## A8. Consumer test at every boundary

The criterion: **can Stage N+1 perform its engineering task using only Stage N's
structured output** — without re-reading the request, inspecting benchmark
documentation, inferring hidden intent, inspecting final CAD, or inventing design
content?

| boundary | consumer's task | verdict today | missing |
|---|---|---|---|
| S01→S02 | derive obligations; form candidates | **PASS** | — (add the quantity inventory as a convenience, not a fix) |
| S02→S03 | establish bodies, joints, interfaces, supports | **FAIL** | `LoadCase`; evidence-route classification on `Candidate`; obligations *created* by each candidate |
| S03→S04a | place envelopes; test reach and packaging | **PASS** | — |
| S04a→S04b | prove paths and swept occupancy | **PASS** | — |
| S04b→S05 | attach features that make each relation real | **FAIL** | functional regions as metric volumes; located joint frames (S-3); an executable `PoseLaw` (S-9) |
| S05→S06 | solve | **PASS** | — (given the loop of §A5.3) |
| S06→S07 | compile | **PASS** | — (given that the pose law is *not* routed through S07) |
| S07→S08 | plan verification | **CONDITIONAL** | passes only if the defeat specifications came from S03/S05; otherwise S08 must invent controls from geometry (S-6) |

**Three boundaries fail.** All three failures are the missing families, not the
sequence.

---

# Part B — deliverables

## B1. Recommended Stage 01–07 pipeline

Changes from the current architecture are marked **[NEW]**, **[CHANGED]** or
**[MOVED]**.

---

### Stage 01 — requirement capture

- **Engineering question.** What did the user actually say, and what did they
  leave open?
- **Reasoning responsibilities.** Extract and classify without sharpening;
  separate what is stated from what is silent.
- **Decisions owned.** `Requirement`, `SourceClause`, `Freedom`, `Ambiguity`,
  `Scenario`, `Actor`, `SystemBoundary`, observables.
- **Prohibited.** Inventing a requirement; sharpening a qualifier; resolving an
  ambiguity; naming any mechanism, material, part or dimension.
- **Required inputs.** Raw source text, exclusively (INV-002).
- **Structured outputs.** The above, plus **[NEW]** a *quantity inventory* —
  per requirement, whether the source gives a magnitude, a band, a comparative or
  nothing; and **[NEW]** *scenario kinds*, distinguishing operation from service.
- **Geometry maturity.** L0.
- **Unresolved allowed.** Every ambiguity; every freedom. Recording them is the
  deliverable.
- **Deterministic checks.** Every requirement resolves to a clause locator; no
  numeral appears in a requirement that is absent from its clause; byte-identical
  on re-run.
- **LLM role.** High — extraction and classification. Failure mode (sharpening)
  is mechanically checkable.
- **Knowledge base.** None. A KB here imports assumptions.
- **Next-stage requirement.** S02 needs requirements, observables, scenarios by
  kind, the quantity inventory and the ambiguities with their block scopes.

**Assessment: correct.** No change beyond two additive outputs.

---

### Stage 02 — obligation, load and candidate formation **[CHANGED]**

- **Engineering question.** What must physically be true, what loads exist, and
  what families of mechanism could satisfy both?
- **Reasoning responsibilities.** Derive obligations; derive the load cases the
  scenarios imply; generate candidate families; classify each candidate's
  evidence route.
- **Decisions owned.** `Obligation`, `Candidate`, `AcceptanceContract`,
  `BodyHypothesis`, `PhysicalInteractionHypothesis`, **[NEW]** `LoadCase`,
  **[NEW]** `EvidenceRouteDecision`.
- **Prohibited.** Selecting a winner (INV-007); scoring by element count (R-16);
  rejecting for absence from a library — that is `UNSUPPORTED` (INV-011); any
  position or dimension.
- **Required inputs.** S01 output only.
- **Structured outputs.** Obligations traced to requirements; **load cases** —
  scenario, loaded body, direction class (transverse / axial / moment / gravity),
  magnitude or `UNSUPPORTED`; candidates as persisting branches, each declaring
  the *principle* it relies on, the obligations it *addresses*, the obligations it
  *creates*, and its **evidence route** with an availability verdict.
- **Geometry maturity.** L1.
- **Unresolved allowed.** Candidate ranking — mandatory. Every magnitude the
  source does not give.
- **Deterministic checks.** Every obligation traces to a requirement; no candidate
  carries a score; every candidate has an evidence-route verdict; every load case
  names a scenario and a direction class.
- **LLM role.** Highest of any stage. Candidate generation is genuinely
  open-ended — BM-001 proves two materially different topologies satisfy one
  Oracle.
- **Knowledge base.** The micro-oracles are the KB. All three benchmarks
  decompose into `guided-slider`, `rotary-to-linear-engagement` and
  `latch-retention`. Per capability the KB supplies: the obligations it creates,
  whether it is self-locking, and the retention-termination options it permits.
- **Next-stage requirement.** S03 needs body hypotheses with roles, interaction
  hypotheses, obligations, **load cases**, and the evidence-route verdicts.

**Assessment: incomplete today.** `LoadCase` and `EvidenceRouteDecision` are the
fixes for S-2 and S-8.

---

### Stage 03 — embodiment topology, mobility and assembly strategy **[CHANGED]**

*The stage that must change most, and the stage where the pipeline currently
breaks.*

- **Engineering question.** What are the bodies, how are they connected, what can
  move, what must not, what reacts what, and in what order does it go together?
- **Reasoning responsibilities.** Enumerate bodies and joints; classify every
  meeting region; **disposition every degree of freedom**; assign reaction paths
  to load cases; decide whether the design uses compliance; choose the
  retention-termination strategy; order the assembly.
- **Decisions owned.** `Body`, `Joint` *(type, bodies, DOF, axis **direction**)*,
  `Interface`, `Configuration`, `MobilityExpectation`, **[NEW]**
  `CompliantRegion` *(existence and role)*, **[NEW]** `FunctionalRegion`
  *(role)*, **[NEW]** `LoadPath`, **[NEW]** `AssemblyPlan`, **[MOVED from s08]**
  the defeat specification on every constraining relation.
- **Prohibited.** Any qualitative region used as a position (R-02/03/04); an
  unclassified meeting region; a generic block (R-09); any feature shape; any
  dimension; **[CHANGED]** any axis *placement* (S-3); selecting a candidate.
- **Required inputs.** S02 output only.
- **Structured outputs.**
  1. Bodies with roles and instance identity.
  2. Joints with type, participating bodies, DOF and **axis direction** — rich
     enough to *project* into a multibody model without re-derivation (§A6).
  3. Interfaces, every meeting region classified into one of the five kinds.
  4. **A total DOF disposition.** For every body, in every configuration, every
     rigid-body DOF maps to exactly one of `INTENDED` / `BLOCKED_BY(relation)` /
     `MAINTAINED_BY_CLASS(class)` / `IRRELEVANT_BECAUSE(reason)`.
  5. **Blocking relations** for every `BLOCKED_BY`: retained body, blocked
     direction, blocker body, the promise of a feature on each, the
     configurations in which it holds, and its **defeat specification**.
  6. **Load paths**: for each load case, an ordered body chain to a reaction
     site, each hop naming the interface that carries it — marked
     `PROVISIONAL` until S04b confirms occupancy.
  7. **Compliance decision**: whether any obligation is discharged by deflection,
     and on which bodies. Existence only; geometry is S05.
  8. **Assembly plan**: partial order, the relationships each step activates, the
     dependency graph, and the **retention-termination strategy** per retained
     body — later-body cover / rotation / elasticity.
  9. **Functional regions** by role: access, support, keep-out, aperture.
- **Geometry maturity.** L2, L3, L4. **Geometry first appears here, and it is
  symbolic.**
- **Unresolved allowed.** Every magnitude; axis placements; assembly *directions*
  (Q-1); which of several admissible retention strategies is used, if more than
  one survives.
- **Deterministic checks.** DOF totality; every `BLOCKED_BY` resolves to a
  blocking relation with a direction and a named blocker; every blocking relation
  has a defeat specification; assembly graph acyclicity; every load case has a
  path terminating at a reaction site; every interface classified; every
  obligation owned by some body pair; every retained body has a termination
  strategy.
- **LLM role.** High for topology and strategy proposal. **None for DOF
  totality** — the DOF set is enumerated mechanically from the joint graph, and
  the LLM only dispositions each entry.
- **Knowledge base.** Per capability: the standard DOF disposition template, the
  standard blocking relations, and the retention trichotomy. This is the
  checklist BM-001's human reviewer supplied by hand three times.
- **Next-stage requirement.** S04 needs the joint graph, configurations, the DOF
  disposition, blocking relations, load paths, the assembly plan and the
  functional regions.

**Assessment: incomplete and internally inconsistent today.** Four new families,
one ownership split, one totality requirement, one moved responsibility.

---

### Stage 04 — placement, motion and spatial feasibility **[CHANGED: two passes]**

- **Engineering question.** Where is everything in each state, what path connects
  the states, and is that path — and every assembly path — actually clear?

**S04a — envelope and reach feasibility.** Run on **every** retained candidate.

- Owns: `Envelope`, endpoint `State` poses at PROVISIONAL maturity.
- Checks: gross packaging; enclosure fit; access reach; **AABB interference**
  (conservative — no-overlap is a proof, overlap is not).
- Purpose: kill candidates cheaply, each with a stated geometric reason.

**S04b — swept occupancy and path feasibility.** Run on survivors only.

- Owns: `State` (AUTHORITATIVE), `Transition`, `SweptVolume`, `Witness`
  (declaration), **[NEW]** located `JointFrame` (S-3), **[NEW]** `PoseLaw` (S-9),
  metric `FunctionalRegion` volumes.
- **Prohibited.** A render as authoritative (R-01); a constant offset as a motion
  model (R-07); undeclared adaptive sampling; feature detail; final dimensions.
- **Structured outputs.** Metric poses per body per state; motion paths with
  **declared** sampling and refinement windows; swept volumes with declared
  fidelity; **assembly insertion sweeps in the configuration produced by the
  preceding steps**; occupancy results for every functional region across every
  state and path; confirmation or refutation of each `PROVISIONAL` load path; the
  per-candidate feasibility record; and the `SelectionDecision` gate.
- **Geometry maturity.** L5–L7. **Authoritative metric geometry first appears
  here.**
- **Unresolved allowed.** All feature detail; all dimensions.
- **Deterministic checks.** Sampling declared and non-adaptive; **interior
  samples present, not endpoints only**; every functional region has an occupancy
  result in every state; every assembly step has a swept-path result; every
  provisional load path is confirmed or refuted; the selection gate refuses to
  fire before all survivors carry equal evidence.
- **LLM role.** Low. This is computation; the LLM proposes candidate poses and
  paths for a solver to check.
- **Knowledge base.** Sampling policies per motion class; standard probe sets —
  the pitch/roll/yaw escape probes BM-002 used, the lift-and-turn probes BM-003
  used.
- **Next-stage requirement.** S05 needs poses, the pose law, paths, engagement
  sites, interfaces with kinds, blocking relations, and functional-region volumes.

**Assessment: correct in intent; over-constraining as a single pass; missing two
outputs.**

---

### Stage 05 — feature and realization *(with S06 as an inner service)* **[CHANGED]**

- **Engineering question.** What actual geometry on which body makes each declared
  relation physically real, and what does that geometry demand of the layout?
- **Reasoning responsibilities.** Realize every declared relation with named
  features; emit the envelope constraints those features impose; converge the
  parameter system through bounded solver rounds.
- **Decisions owned.** `Feature`, `Realization`, `Parameter` *(declaration)*,
  `Constraint`, `ConstructionStatement`, **[NEW]** `EnvelopeConstraint`,
  `CompliantRegion` *(geometry, mode, magnitude, activation window)*, ROI
  definitions, **[MOVED from s08]** defeat specifications at feature level.
- **Prohibited.** Creating a `Body` or `Joint` — it extends S03's (INV-001,
  R-19); discharging an obligation with a label (INV-008); a null unit (INV-004);
  **[CHANGED]** setting a `Parameter` value except by citing a solver artifact.
- **Required inputs.** S03 + S04 output.
- **Structured outputs.** A feature graph in which every interface is realized by
  a feature on **each** participant, or by a declared compliant region with its
  mode; every blocking relation given its feature pair; every declared limit given
  its **producing feature pair** (S-13); compliant regions with direction,
  magnitude and activation window; load-path records; ROI definitions per
  interaction; a **total** construction program; parameters with units;
  constraints including envelope constraints.
- **Geometry maturity.** L8, L9 → L10 on convergence.
- **Unresolved allowed.** Embodiment alternatives; underdetermined parameter
  directions, recorded as `UnresolvedDecision`.
- **Deterministic checks.** Every interface has features on all participants;
  every blocking relation has a feature pair; every limit has a producer; every
  obligation cited by some realization with a verification predicate; program
  totality; no null unit; no parameter dependency cycle; **no feature intrudes
  into a functional region** (re-check of S04's occupancy).
- **LLM role.** High for feature proposal and program shape; **none** for
  completeness, which is enumeration over S03's relation set.
- **Knowledge base.** Highest of any stage. Feature patterns per capability —
  clevis + pin + head + captor; rail + lip + tab; heel + arm — and with each
  pattern its envelope constraints and assembly implications.
- **Next-stage requirement.** S06 needs a closed constraint system with every
  symbol declared and united.

---

### Stage 06 — parameter resolution **[CHANGED: service, not barrier]**

- **Engineering question.** Do values exist that satisfy every constraint, and if
  not, exactly which constraints conflict?
- **Decisions owned.** None. Extends `Parameter` and `Constraint`.
- **Prohibited.** Defaulting a unit (R-21); `feasible` for an underdetermined
  system; silently choosing one member of a solution family; deferring an
  expression to CAD (R-22); copying values and calling them solved (R-23).
- **Structured outputs.** Per parameter a value or an explicit non-value status;
  residuals; active set; margins; solver status from the five-value vocabulary.
- **Convergence contract.** Bounded rounds; each round strictly reduces the
  unsatisfied set; a non-reducing round terminates with `underdetermined` or
  `infeasible` and a named conflicting set.
- **Geometry maturity.** L10.
- **LLM role.** **None.** An LLM here re-introduces R-23.
- **Knowledge base.** Constraint idioms and their solvability class.
- **Next-stage requirement.** S07 needs the program plus a value for every symbol
  it references.

---

### Stage 07 — geometry compilation

- **Engineering question.** Does the declared program, with the solved values,
  produce valid solids?
- **Decisions owned.** `GeometrySignature`; extends `Body` and `Feature` with
  compiled geometry.
- **Prohibited.** Consulting the source, requirements or candidates; **repairing**
  an uncompilable statement — it fails citing the statement (INV-006, R-24); an
  OCCT face index as identity; choosing a form, placement, axis or missing
  dimension; **[NEW]** reading any `ScoutFinding`.
- **Required inputs.** Construction program + resolved parameters. **Not the pose
  law** (S-9).
- **Structured outputs.** Compiled solids; per-body validity, volume positivity
  and **single-connected-solid**; the geometry signature from the kernel's own
  mass properties, taken from the **native** shapes before any export; native
  BREP then STEP exports with independent re-import and comparison; an independent
  rebuild determinism result.
- **Geometry maturity.** L11. **CadQuery becomes authoritative here and nowhere
  earlier.**
- **LLM role.** None whatsoever.
- **Knowledge base.** None. A KB here would be a repair mechanism.
- **Can it be a pure compiler?** **Yes — plus a validity reporter.** All three
  references' `build.py` files are exactly such compilers. But BM-003 `R1` shows
  S07 must also report B-rep connectivity, which is discoverable nowhere earlier.
  Compiler + validity reporter + exporter, with **no repair**.
- **Next-stage requirement.** S08 needs solids, signature, feature identities and
  the declared predicates *with their defeat specifications from S03/S05*.

---

## B2. Stage-to-stage information sufficiency matrix

| producer → consumer | consumer's engineering question | minimum sufficient hand-over | fails today because |
|---|---|---|---|
| S01 → S02 | what must physically be true? | requirements; observables; scenarios **by kind**; quantity inventory; ambiguities with block scopes | — (passes) |
| S02 → S03 | what bodies, joints and supports? | body hypotheses with roles; interaction hypotheses; obligations addressed *and created*; **load cases with direction classes**; evidence-route verdicts | no `LoadCase`; no route classification |
| S03 → S04a | can any of these candidates fit and reach? | joint graph; configurations; body roles; functional-region roles; packaging obligations | — (passes) |
| S04a → S04b | which survivors need full path proof? | surviving candidates with their envelope evidence; endpoint poses | — (passes) |
| S03 → S04b | does the intended motion exist and the forbidden motion not? | total DOF disposition; blocking relations with directions and blockers; assembly plan with order and termination strategy; provisional load paths | DOF set not total; blocker not required with direction |
| S04b → S05 | what features make this real? | metric poses; **executable pose law**; paths with declared sampling; swept volumes; engagement sites; **located joint frames**; **metric functional regions**; confirmed load paths | no pose law; axis placement owned by the wrong stage; no functional-region family |
| S05 → S06 | what are the values? | closed constraint system; every symbol united; envelope constraints from features | — (passes, given the loop) |
| S06 → S07 | does it compile? | construction program + a value for every referenced symbol | — (passes) |
| S07 → S08 | how will each requirement be checked? | valid solids; signature; feature identities; declared predicates **with defeat specifications** | defeat specifications do not exist; S08 must invent controls from geometry |

**Three failing boundaries: S02→S03, S04b→S05, S07→S08.** All three are missing
information, not misplaced sequence.

## B3. Geometry / CadQuery maturity plan

- **Levels and their owners:** the L0–L12 table in §A4.
- **Geometry first appears:** S03, symbolically (L2–L4).
- **Authoritative metric geometry first appears:** S04b (L6–L7). S04a's envelopes
  are PROVISIONAL and conservative.
- **CadQuery authoritative:** S07 (L11), and nowhere else.
- **CadQuery as scout:** permitted from S03 onward under the five rules of §A4.1,
  the load-bearing one being *a scout finding may only raise, never set*.
- **Maturity is a field, not a stage** (§A7.2): `SYMBOLIC | PROVISIONAL |
  AUTHORITATIVE | FROZEN` on every geometric value.
- **A check may not run on input below its declared minimum maturity.** This is
  what stops a proxy result being cited as a CAD result, and it is mechanically
  enforceable.

## B4. Design-space preservation rules

The nine rules of §A5.4. The two that would have changed the most history:

- **Rule 4** — a support assignment is PROVISIONAL until swept occupancy confirms
  the region is free in every state (BM-002 `CHG-02`).
- **Rule 5** — no dimension is frozen before the assembly path that constrains it
  (BM-002 hub Ø = journal Ø).

## B5. Earliest-useful validation map

The table in §A6. Its three structural consequences:

1. **Negative controls move from S08 to S03/S05** (authorship), remaining at S09
   for execution.
2. **CAD/simulation parity becomes structural** rather than checked, if S03's
   joint graph is simulation-complete.
3. **Force, back-drive magnitude, tolerance and manufacturability have no route
   at any maturity** and must be declared `UNSUPPORTED` at S02 rather than
   discovered at S11.

## B6. Representation principles

The eight principles of §A7.3. Restated as the minimum the pipeline cannot work
without: stable IDs; patches against a hashed parent state; **maturity per
value**; **an invalidation cone per patch**; four-way provenance including
`ScoutFinding`; three-state decisions; **defeat specifications on constraining
relations**; run identity on every external artifact.

## B7. Specific weaknesses in the current pipeline

**Fatal — cannot be worked around downstream**

| id | weakness | evidence |
|---|---|---|
| S-1 | no compliance representation; **BM-001's accepted design is inexpressible** | HCR-BM001-010; `compliant_regions` in `parameters.yaml`; `DECLARED_COMPLIANT_INTERACTION`; NRM-BM-003-017 |
| S-2 | no load representation; S03 assigns supports blind | NRM-BM-002-006 quantifies over load-carrying elements; BM-002 §2.4 |

**Severe**

| id | weakness | evidence |
|---|---|---|
| S-3 | `Joint.axis` placement owned by a stage that cannot derive it | BM-002 `CHG-01` |
| S-4 | forbidden DOF set declared but not total | HCR-BM001-002/-004/-006; BM-003 `R2` |
| S-5 | invalidation cone exists only on `FailureProvenance` at s12 | BM-003 `R5` |
| S-6 | negative controls authored at s08 from geometry | `DEF-01`, `DEF-02`, `NC-17` |
| S-7 | S04 selection gate economically infeasible at full fidelity | 7 and 5 admissible fixtures; the manual process carried 2, 1, 1 |
| S-8 | no owner for evidence-route capability | `REFERENCE_SELECTION.yaml` rejects four fixtures on route grounds |
| S-9 | INV-006 omits the pose law; it hides in `build.py` | all three references |
| S-10 | no functional-region family | BM-001's 84 mm access, violated by a feature |
| S-11 | S05/S06 drawn as a barrier | BM-002 `CHG-01`/`CHG-03`; BM-003 `R3`/`R6` |

**Boundary declarations, not defects**

| id | item |
|---|---|
| S-12 | tolerance, manufacturing process and material properties have no representation and no route. Declare at S02. |
| S-13 | a declared limit is not required to name its producing feature |

**Redundant**

`Configuration` vs `State`; dual ownership of `Witness` and `NegativeControl`; a
proposed DOF-disposition family that should instead be a totality requirement on
`MobilityExpectation`.

**Over-constraining**

INV-006 in its literal input list (S-9); INV-007's gate at a single expensive
fidelity (S-7).

**Correct and should not be touched**

INV-002 (source-text exclusivity); INV-001 (single ownership); INV-007's
*principle* of no selection before evidence; the patch model with
`parent_state_hash`; the status vocabulary and its forbidden collapses; the
`RejectedAlternative` retention rule; S07's no-repair rule.

**Methodological finding.** `ENTITY_FAMILY_AUDIT.yaml` states *"NO FAMILY WAS
ADDED OR DELETED BY THIS AUDIT"* and asks only whether each existing family has a
consumer. It could not, by construction, find engineering content with no family
— which is exactly what S-1, S-2 and S-10 are. Any future audit must ask both
questions.

## B8. Minimal implementation order

Contract work first; no stage implementation until step 5.

1. **Add the missing families** to `DESIGN_STATE_CONTRACT.yaml`: `CompliantRegion`,
   `LoadCase`, `LoadPath`, `FunctionalRegion`. Assign ownership. *(Fixes S-1,
   S-2, S-10.)*
2. **Field-level contract changes**, no new families: make
   `MobilityExpectation.forbidden_dof` total; split `Joint.axis` into direction
   (S03) and located frame (S04b); add a defeat specification to every
   constraining relation; add a maturity field to every geometric value; add
   `PoseLaw` to S04b; require a producing feature on every declared limit.
   *(Fixes S-3, S-4, S-6, S-9, S-13, and §A7.2.)*
3. **Patch contract changes**: move the invalidation cone to `StagePatch`; add
   run identity to external artifacts; add `ScoutFinding` provenance. *(Fixes
   S-5.)*
4. **Resolve the two open `ENTITY_FAMILY_AUDIT` gaps** — GAP-01 joint capture and
   GAP-02 assembly ordering — both already scoped as RELATE operations needing no
   new family. Both are marked `decision_required_before: s03 implementation`.
5. **Write the sufficiency probes before any stage.**
   `STAGE_PROGRESSION_CONTRACT` step 6 mandates them and they do not exist. Nine
   probes, one per row of B2.
6. **Hand-author S03 and S04b outputs for the three existing references and run
   the probes against them.** The references are the only ground truth in the
   repository. A probe that passes on a hand-authored input missing something the
   CAD needed is a probe defect, and the CAD record says exactly what was needed.
   **Highest value per unit of effort in this list; needs no stage
   implementation.**
7. **Author the Scout contract** before any exploratory CadQuery exists, so the
   boundary precedes the temptation.
8. **Then implement**, in this order: S01 and S02 first because they are cheap and
   are needed as input; then **S03**, which carries all the risk. Author the S03
   and S04 *contracts* before implementing S01, so the hard unknowns are settled
   while the cheap stages are being built.

**Explicitly not in this plan:** implementing any stage before step 8; changing
any Oracle; changing `cadval` / `valcore`; re-running any benchmark validation.

## B9. Open questions that genuinely remain unresolved

**Q-1 — Can S03 own assembly *direction*, or only order and strategy?**
BM-002's forced +X insertion was derived from metric geometry (the arm cannot pass
the bore). This review assigns order and strategy to S03 and direction feasibility
to S04b, but a direction that is *only* discoverable at S04b may make S03's
assembly plan under-determined in a way that blocks the S03 gate.

**Q-2 — What is a DOF disposition for a compliant body?** A rigid body has six.
A compliant region does not have a finite DOF set in the same sense. BM-001's four
tabs and one latch finger are the test case, and the totality requirement — the
single highest-value change in this review — has no defined meaning for them yet.

**Q-3 — How many candidates can realistically reach the S04b gate?** The two-pass
split makes the gate affordable in principle. Nobody has measured what fraction
S04a eliminates, and if it eliminates few, S-7 returns.

**Q-4 — Can an LLM produce a total DOF disposition reliably?** The enumeration is
mechanical, but dispositioning each entry is judgement, and a wrong
`IRRELEVANT_BECAUSE` is indistinguishable from a right one without geometry. The
failure mode is a plausible reason for an omission — which is precisely what
happened three times to a careful human.

**Q-5 — Is the scout boundary enforceable at all?** Rules 1–5 are contract
statements. Nothing mechanically prevents a number discovered in a scout from
being typed into a parameter with a plausible-sounding rationale. Requiring a
parameter's provenance to cite a state-derivable constraint is the only real
defence and it may not be sufficient.

**Q-6 — Does any affordable compliance route exist?** A reduced-order beam model
for a cantilever snap is not FEA and might be tractable. If one exists, P-6
weakens materially and BM-001's four rejected Oracle fixtures become buildable.
If none exists, the pipeline will keep selecting mechanisms it can evidence and
the Oracle's permissiveness will never be tested.

**Q-7 — Is nominal-only geometry a permanent boundary?** Every clearance in all
three references is nominal. Without tolerance, "practical to manufacture" is
permanently unevaluable and every fit is a nominal fit. Accepting this
permanently is a real decision about what the pipeline is for.

**Q-8 — Do the frozen Oracle `stage_expectations` survive these changes?** The
s05/s06 boundary becomes a bounded loop rather than a barrier (§A5.3). The
numbering and both `must_exist` lists are preserved deliberately for this reason,
but whether a frozen expectation authored against a sequential barrier remains
satisfied by a converged loop needs an explicit ruling from whoever owns the
Oracle freeze.

---

*Sources: `ver3/contracts/` (`DESIGN_STATE_CONTRACT`, `STAGE_OWNERSHIP_MATRIX`,
`STAGE_PATCH_CONTRACT`, `STAGE_PROGRESSION_CONTRACT`, `ENTITY_FAMILY_AUDIT`,
`STATUS_SEMANTICS`); `ver3/phase0/` (`ARCHITECTURE_INVARIANTS`,
`VER2_RETIREMENT_MATRIX`); `ver3/oracles/` (product cases BM-001, BM-002;
held-out BM-003; micro-oracles); `ver3/cad_validation/` (all three executable
references, their rationales, validators and review records). Nothing was
modified.*
