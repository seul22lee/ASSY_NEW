# Pipeline implementation proposal — Stages 01–07

**Status.** Final architecture proposal, **revision 2**. The sixteen corrections
from `PIPELINE_HIGH_RISK_ARCHITECTURE_CHECK.md` (verdict B) are incorporated into
the architecture below, not appended as notes. Implementation may begin after the
readiness report (`PIPELINE_IMPLEMENTATION_READINESS.md`).

No stage logic is implemented here.

**Basis.** All accumulated evidence: the Ver2 retirement matrix, the architecture
invariants, the Stage 01 redesign, the eight Oracle packs, the three executable
CAD references and their validators, the simulation work, the negative controls,
the human CAD review decisions, and the two prior reviews
(`PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md`,
`PIPELINE_CRITICAL_DESIGN_REVIEW.md`).

**Relationship to the prior documents.** This proposal *supersedes* their
recommendations where they conflict, and it settles seven of the eight questions
the critical review left open. It does not restart from first principles: the
patch model, the ownership discipline, the status vocabulary and the invariants
are kept because Ver2 paid for them. What changes is what the stages are
*responsible for*, not how the machinery works.

---

## 1. Design philosophy

Seven principles. Each is a conclusion from a specific failure, not a preference.

**1. A stage owns a *question*, not a *representation.**
Ver2's stages were named after artifacts and produced whatever the next stage
could be made to accept. Every stage below is named after the engineering
question it answers, and its output is defined as the minimum that lets the next
question be answered.

**2. Commitment follows evidence, and maturity is per value.**
A value becomes authoritative when the evidence that discriminates it exists —
not when its owning stage finishes. Within one patch, some values are
authoritative and others are provisional. This is the single most important
representational change in this proposal.

**3. Checks run at the cheapest maturity at which they mean something.**
Thirteen of the fourteen late discoveries across the three benchmarks were
knowable before CAD. The defect was never that geometry started late; it was that
checks ran several levels above where their information already existed.

**4. Completeness is enforced by totality, not by declaration.**
A declared set can omit. A total function over an enumerable domain cannot. Every
place where the benchmarks failed by omission — three human-review rejections on
BM-001, `R2` on BM-003 — is a set that was declared but not total.

**5. Every constraint carries the means of its own refutation.**
A relation that cannot be defeated cannot be tested. The defeat specification is
authored with the relation, by the stage that owns it, not reconstructed from
geometry two stages later.

**6. The pipeline is feed-forward with two declared, bounded loops.**
Pretending it is a DAG is what produced `CHG-01`. There is a parameter loop
(S05↔S06) and a geometric settlement loop (S04·B→S05→S06→re-validate). Both are
bounded, both are recorded, and nothing else iterates.

**7. What cannot be evidenced must be declared unevaluable early, not discovered
unevaluable late.**
Force, tolerance, material behaviour and manufacturability have no route in this
toolchain. Saying so at S02 costs nothing. Discovering it at S11 wastes the whole
pipeline and, worse, silently steers mechanism selection.

---

## 2. Final proposed Stage 01–07 pipeline

Seven numbered stages. **S04 has two passes** at different fidelities.
**S05 and S06 form one bounded convergence block.** The numbering is preserved
deliberately: the Oracle packs are frozen and their `stage_expectations`
reference `s01`–`s12` by name, and renumbering would invalidate frozen artifacts
for cosmetic gain.

```
S01  requirement capture                       what was asked, and what is open
      │
S02  obligation, load and candidate formation  what must be true; what loads exist;
      │                                        what families could do it; what we
      │                                        can actually evidence
S03  topology, mobility and assembly strategy  what things there are, what may move,
      │                                        what must not, what reacts what,
      │                                        in what order it goes together
      │                                        ── geometry begins, symbolically ──
S04·A envelope and reach feasibility           can any of these candidates fit and
      │                                        reach?  (cheap, all candidates)
      │                                        ── SELECTION GATE ──
S04·B placement, motion and spatial proof      where is everything, what path
      │  ◄──────────┐                          connects the states, is it clear?
S05  feature and realization                   what geometry makes each relation
      │  ◄───┐      │                          real, and what does it demand?
S06  parameter resolution                      what are the numbers?
      │──────┘      │
      │─────────────┘   geometric settlement loop (bounded)
S07  geometry compilation                      does it build, and is it valid?
```

### 2.1 What changes from the current architecture

| change | fixes |
|---|---|
| **5 new entity families**: `RigidGroup`, `LoadCase`, `LoadPath`, `FunctionalRegion`, `AssemblyStep` | inexpressible compliance; blind support assignment; violated access regions; implicit assembly order |
| **`maturity` field on every geometric value** | provisional and solved values indistinguishable |
| **`MobilityExpectation.forbidden_dof` becomes total** | omission-class failures |
| **`Joint` splits: direction at S03, located frame at S04·B (provisional) → S06 (authoritative)** | circular axis ownership |
| **defeat specification on every constraining relation** | controls that cannot fire |
| **invalidation cone moves from `FailureProvenance` to `StagePatch`** | silent loss of a property when an upstream value changes |
| **S04 splits into two passes; the gate sits between them** | infeasible selection gate |
| **S05/S06 becomes a bounded loop; S05 may not set a value except by citing a solver artifact** | feature envelopes discovered after dimensions were frozen |
| **`EvidenceRoute` becomes a capability registry consulted at S02** | evidence capability silently selecting the mechanism |
| **scout geometry admitted as `Witness` with fidelity `SCOUT`, may only raise** | expensive discoveries deferred to CAD |
| **one rigid group + one compliant joint per compliant *member*; co-actuation by a `Transition`** | a "region" of independent cantilevers asserted a coupling that does not exist |
| **`required_travel` and `allowable_travel` are separate fields** | a 20 mm demand on a 20 mm beam was indistinguishable from a 2 mm one |
| **per-element load components are derived, never stored** | SF-5.3 at the data level; "shaft → bearing" |
| **`driver` on every constraining relation** | a conversion-required constraint had no justification available |
| **loop terminates on round budget + repeated state, not monotone reduction** | the proposed rule would have falsely terminated BM-003 R1→R4 |
| **loop scope: placements, dimensions, feature alternatives only** | without it, "bounded" was aspirational |
| **a `Constraint` for every declared clearance** | the loop had nothing to converge on (BM-003 R5) |

No family is removed. The count goes 32 → 37.

---

## 3. Responsibilities of every Stage

---

### Stage 01 — requirement capture

**Engineering question.** What did the user actually say, and what did they leave
open?

**Engineering responsibility.** Convert prose into typed statements without
sharpening, and make silence explicit.

**Must actively discover.** Which requirements carry a magnitude, a band, a
comparative or nothing; which scenarios are operation and which are service;
which actors exist and what they must reach; the observable behind each
requirement.

**Receives.** Raw source text — exclusively (INV-002).

**Outputs.** `Requirement`, `SourceClause`, `Freedom`, `Ambiguity`, `Scenario`
(with `kind ∈ {OPERATION, SERVICE, ASSEMBLY, TRANSPORT}`), `Actor`,
`SystemBoundary`, observables; and a **quantity inventory** — per requirement,
the source's quantitative content, explicitly including *none*.

**Owns.** All of the above.

**Never decides.** A requirement the source does not state; a sharpened
qualifier; a resolved ambiguity; any mechanism, material, part or dimension.

**May remain unresolved.** Every ambiguity and every freedom — recording them is
the deliverable, not a shortfall.

**Deterministic checks.** Every requirement resolves to a clause locator; no
numeral appears in a requirement that is absent from its clause; every scenario
has a kind; byte-identical on re-run.

**Geometry maturity.** None.

**Next stage requires.** Requirements, observables, scenarios by kind, actors,
the quantity inventory, ambiguities with their block scopes.

---

### Stage 02 — obligation, load and candidate formation

**Engineering question.** What must physically be true, what loads exist, what
families of mechanism could satisfy both — and which of those can we actually
evidence?

**Engineering responsibility.** Derive physical necessity from stated intent;
enumerate the loads the scenarios imply; generate genuinely different candidate
families; and classify, before any geometry, what each candidate would need to be
proven.

**Must actively discover.**
- Obligations that follow physically but are not stated — the ones a design
  cannot omit even though the user never mentioned them.
- **Load cases**: for each scenario, what is applied, to which body **role**, in
  which direction class, of which `kind ∈ {GRAVITY, PAYLOAD, ACTOR_APPLIED,
  REACTION}`, with a magnitude or `UNSUPPORTED`. A `LoadCase` is
  **candidate-independent**: it says what the world does to the product, never
  what any mechanism carries. `ACTOR_APPLIED` is what distinguishes "the user
  turns the handle" from "a load is applied to the handle"; without the
  distinction the two are indistinguishable.
- The obligations each candidate *creates* as well as those it addresses. A
  candidate that needs a bearing has created a bearing obligation, and this is
  what stops incompleteness winning (R-16).
- Whether the transmission family is self-locking — back-drive is a property of
  the family, knowable here, and a legitimate discriminator.
- **The evidence route** each candidate's primary function would require, and
  whether the toolchain has it.

**Receives.** S01 output only.

**Outputs.** `Obligation`, `Candidate`, `AcceptanceContract`, `LoadCase`,
provisional body hypotheses and interaction hypotheses, and per candidate an
`evidence_route_verdict` referencing the capability registry.

**Owns.** Obligations; load cases; candidates as persisting branches; the
declaration that a claim class is unevaluable.

**Never decides.** A winner (INV-007). A score (R-16). Rejection for absence from
a library — that is `UNSUPPORTED` (INV-011). Any position or dimension.

**May remain unresolved.** Candidate ranking — mandatory. Every magnitude the
source does not give. Which of several admissible principles is used.

**Deterministic checks.** Every obligation traces to a requirement or to a named
derivation premise; no candidate carries a score; every candidate has an evidence
route verdict; every load case names a scenario, a body role and a direction
class; every scenario of kind `OPERATION` has at least one load case or an
explicit statement that it is unloaded.

**Geometry maturity.** Body/shape class only. No positions.

**LLM role.** Highest of any stage. Candidate generation is genuinely open-ended
— two materially different topologies satisfied one Oracle on BM-001.

**Knowledge-base role.** The micro-oracle capability packs are the KB. Per
capability it supplies: the obligations it creates, whether it is self-locking,
which retention-termination options it permits, and its evidence route.

**Next stage requires.** Body hypotheses with roles, interaction hypotheses,
obligations addressed *and created*, load cases with direction classes, evidence
route verdicts.

---

### Stage 03 — topology, mobility and assembly strategy

*The stage that carries the most new responsibility, and the one where the design
becomes a mechanism.*

**Engineering question.** What things are there, how are they connected, what may
move, what must not, what reacts what, and in what order does it go together?

**Engineering responsibility.** Turn a candidate family into a specific
mechanism topology, and account for **every** degree of freedom in it.

**Must actively discover.**
- The bodies, and — where a body is not rigid — its **rigid groups** and the
  compliant joints between them. **One rigid group and one compliant joint per
  compliant member**: four independent tabs are four groups and four joints, not
  one region. A "region" is not an entity; it is a *set of compliant joints
  co-actuated by one `Transition`*, which is the same machinery that moves
  several legs together. Grouping independent members into one rigid group would
  assert a coupling that does not physically exist.
- Every joint: type, participants, DOF, and axis **direction**.
- Every region where two bodies meet, and its interaction kind.
- **The disposition of every degree of freedom, in every configuration.** This is
  the mechanical FMEA and it is obtained free from the joint graph.
- For each `BLOCKED_BY` disposition: which body blocks it, in which direction,
  and how that blocking is to be defeated for testing.
- For each load case: the ordered path from the load to a reaction site.
- The assembly partial order, the access side per step, and the
  **retention-termination strategy** for every retained body.
- The functional regions the design promises: access, support, keep-out,
  aperture.

**Receives.** S02 output only.

**Outputs.**

| output | note |
|---|---|
| `Body` with role and instance identity | |
| `RigidGroup` | omitted for a body with exactly one; then the body *is* its group |
| `Joint` — type, participants, DOF, axis **direction** | endpoints are rigid groups |
| compliant `Joint` — mode, direction, `required_travel`, `allowable_travel`, `actuation`, `compliant_element`, `root_interface`, **activation window** | one per compliant member; see the travel rule below |
| `Interface` — every meeting region, classified | |
| `MobilityExpectation` — **total** DOF disposition per configuration | the central new obligation |
| `blocked_by` relations — retained group, direction, blocker, promised features, **defeat specification**, `driver`, optional `depends_on_compliant_recovery` | RELATE, per GAP-01 |
| `LoadPath` — ordered hops, each naming its interface | **per candidate**; maturity `HYPOTHESIS` → `SPATIALLY_INSTANTIATED` → `AUTHORITATIVE` |
| `AssemblyStep` — order, access side, relations activated, termination strategy, `path_kind ∈ {RIGID, DEFORMATION_RESOLVED}` | subsumes GAP-02's `precedes`. A `DEFORMATION_RESOLVED` step forces `NOT_VERIFIED`, never `PASS` (ASM-BM-003-002) |
| `FunctionalRegion` — role only, no volume | |
| `Configuration` — named arrangements including partial assemblies | |

**The compliant-joint travel rule.** A compliant joint carries **two distinct
travel fields and they must never be one number**:

- `required_travel` — how far the member must move for the operation to be
  possible. Kinematic, authoritative, owned by S05 once features exist.
- `allowable_travel` — how far the material could actually move. Status
  `UNSUPPORTED`, naming the route that would establish it.

Conflating them is how a design that demands 20 mm of deflection from a 20 mm
beam produces exactly the same structure as one demanding 2 mm. Their
non-comparison becomes a machine-readable gap, and the `ExcludedClaim` for strain
is generated from it rather than authored.

**The compliant joint is prescribed, not caused.** It carries
`actuation: PRESCRIBED_KINEMATIC`. In the real mechanism a ramp contact drives
the deflection; in this model the joint coordinate is imposed. The kinematics are
right and the physics is absent, and the field says so, so no reader can take the
structure as evidence that the mechanism self-deflects.

**The joint names the geometry a beam model would consume.** `compliant_element`
(which feature is the beam) and `root_interface` (where it is built in). These
cost nothing now and are the difference between a reduced-order route being
*addable later* and the model needing to be *re-authored later*.

**The load ownership rule.** `LoadCase` is candidate-independent and owned by
S02. `LoadPath` is **candidate-specific** and owned here, because — in the
Oracle's own words, closing finding SF-5.3 — *"which components a given element
carries depends on the conversion family selected, not on the requirement."*
A cable drum carries no axial load; a rotating nut on a fixed screw reacts
axially through the screw. Consequently:

- **Per-element load components are DERIVED from the load path and are never
  stored.** A stored "this shaft carries a transverse load" field is a
  candidate-independent-looking assertion about a candidate-dependent fact, and a
  later stage cannot tell whether it was traced or assumed. The stored objects
  are the applied load and the path; what each element carries is a projection.
- **No element acquires a reaction obligation from its type.** "Shaft → bearing"
  is unreachable by construction, because an element carries a component only by
  appearing in a path traced from a declared applied load through *this*
  mechanism.
- A `LoadPath` is a **hypothesis** here. It becomes `SPATIALLY_INSTANTIATED` at
  S04·B when its reaction region is proven unoccupied across every state, and
  `AUTHORITATIVE` at S06. BM-002's rear-panel journal was a topologically sound
  path that swept occupancy refuted.

**Every constraining relation records its driver.**
`driver ∈ {LOAD, KINEMATIC_NECESSITY, DECLARED_SCENARIO}`. A constraint may be
required because a load must be reacted, **or** because the selected conversion
needs it to function at all — NRM-BM-002-007's exclusion (b): rotation must be
restrained where *"the selected conversion needs rotational restraint of the
driven body in order to produce translation."* A lead-screw nut is anti-rotated
for the second reason and no load case will ever justify it. One field prevents
both over- and under-justification.

**Retention that depends on recovery says so.** A blocking relation whose
validity requires a compliant joint to have returned to zero names that joint in
`depends_on_compliant_recovery`. HCR-BM001-002 directs that *"the recovered
snap-barb shoulder blocks removal in the other direction"* — that retention is
conditional on recovery, and a creep failure removes it. Without the field the
model shows it as unconditional.

**Owns.** Everything above. This stage owns the *mechanism*.

**Never decides.** Any qualitative region used as a position (R-02/03/04). Any
metric magnitude. Any axis **placement**. Any feature shape. Any dimension. A
selected candidate. An unclassified meeting region. A generic block as an
embodiment (R-09).

**May remain unresolved.** Every magnitude. Axis placements. Assembly
*directions* — S03 fixes the access side and the order; the direction's
feasibility is S04's (see §11, D-4). Which of several admissible retention
strategies is used, if more than one survives.

**Deterministic checks.**
1. **DOF totality** — every rigid group, in every configuration, has every DOF
   dispositioned exactly once.
2. Every `BLOCKED_BY` resolves to a relation carrying a direction, a named
   blocker and a defeat specification.
3. Every `IRRELEVANT_BECAUSE` names a scenario in which that DOF is both
   unloaded and unactuated — cross-checked against the load cases. *This converts
   the one unverifiable disposition into a checkable one.*
4. Assembly order is acyclic.
5. Every load case has a path terminating at a declared reaction site.
6. Every interface is classified.
7. Every obligation is owned by some body pair or compliant joint.
8. Every retained body has a termination strategy from the trichotomy.
9. Every compliant joint declares mode, direction, bounded travel and activation
   window.
10. The joint graph is **simulation-complete**: it can be projected into a
    multibody model without re-derivation.

**Geometry maturity.** Topology, symbolic spatial relations, frames and axis
directions. **Geometry first appears here, and it is symbolic.**

**LLM role.** High for topology and strategy proposal. **None for DOF totality**
— the domain is enumerated mechanically; the LLM only dispositions each entry.

**Knowledge-base role.** Per capability: the standard DOF disposition template,
the standard blocking relations, and the retention trichotomy — *a rigid part
installed by one straight translation always leaves the reverse direction open,
so retention needs a later body, a rotation, or elasticity.*

**Next stage requires.** The joint graph, configurations, the total DOF
disposition, blocking relations, provisional load paths, assembly steps and
functional-region roles.

---

### Stage 04·A — envelope and reach feasibility

**Engineering question.** Can any of these candidates fit, reach and be
approached at all?

**Engineering responsibility.** Kill candidates cheaply, each for a stated
geometric reason.

**Must actively discover.** A provisional extent for every body; whether the
declared functional regions can coexist; whether every actor can reach what it
must operate; whether each assembly step's access side is geometrically
available.

**Receives.** S03 output.

**Outputs.** Provisional `Envelope` per body per configuration; metric
`FunctionalRegion` volumes; reach results per actor; per-candidate feasibility
with an elimination reason where applicable.

**Owns.** Provisional extents. Functional-region volumes. The elimination of a
candidate on geometric grounds.

**Never decides.** Any authoritative dimension. Any feature. Which surviving
candidate wins.

**Absolute scale rule.** Where the source states no size — the common case — the
overall scale is a **declared free parameter with a representative value**,
recorded as `BOUNDED` with the freedom it derives from. It is never a silent
choice, and it never becomes authoritative here.

**May remain unresolved.** Every internal dimension; all feature detail.

**Deterministic checks.** Every body has an extent with maturity `PROVISIONAL`;
every functional region has a volume; every actor has a reach result; **AABB
interference per configuration** — conservative, so *no overlap is a proof and
overlap is not*; every eliminated candidate carries a geometric reason.

**Geometry maturity.** Envelopes and endpoint poses, all `PROVISIONAL`.

**SELECTION GATE.** A `SelectionDecision` may be emitted only after every
retained candidate carries S03 completeness and S04·A feasibility at equal
obligation coverage. If more than one candidate survives with no discriminating
evidence, that is an `UnresolvedDecision` naming what would discriminate — never
an arbitrary pick (R-17).

**Next stage requires.** The selected candidate, its envelopes, its
functional-region volumes.

---

### Stage 04·B — placement, motion and spatial proof

**Engineering question.** Where is everything in each state, what path connects
the states, and is that path — and every assembly path — actually clear?

**Engineering responsibility.** Prove spatial feasibility over *paths*, not over
endpoints.

**Must actively discover.** The metric placement of every joint frame; the pose
of every rigid group in every state; the path between states with declared
sampling; the swept volume of every moving group; whether each provisional load
path's reaction region is actually unoccupied throughout the motion; whether each
assembly step has a clear insertion path **in the configuration produced by the
preceding steps**.

**Receives.** S03 output + S04·A envelopes for the selected candidate.

**Outputs.** Located `Joint` frames (`PROVISIONAL`); `State` with joint
coordinates and rigid-group poses; `Transition` with path and declared sampling;
swept volumes with declared fidelity; assembly insertion sweeps; occupancy
results per functional region per state and per path; confirmation or refutation
of every provisional load path; `Witness` declarations.

**Owns.** Metric placement. Motion paths. Sampling policy. The verdict on whether
a declared spatial promise holds.

**Never decides.** Feature shape. Final dimensions. A functionally-named state —
it may create *waypoint* states for a path, but not a new named configuration.

**Critically: the pose law is not authored.** With located joint frames and joint
coordinates, every pose is *derivable*. Nothing downstream needs a hand-written
pose function, which is what hid inside `build.py` in all three references.

**May remain unresolved.** All feature detail; all dimensions; the final
placement of any frame whose position depends on a feature envelope — these stay
`PROVISIONAL` and are settled by the geometric settlement loop.

**Deterministic checks.** Sampling is declared and non-adaptive; **interior
samples exist — endpoints alone are refused**; every functional region has an
occupancy result in every state and along every path; every assembly step has a
swept-path result computed against the preceding configuration; every provisional
load path is confirmed or refuted; every declared blocking relation is shown to
hold in every configuration where it is claimed; and **every compliant joint
coordinate is zero in every state outside its activation set** — the compliant
analogue of the cycle-return check, without which `activation_window` is an
unchecked list of names.

**Geometry maturity.** Poses, motion paths, swept occupancy — authoritative
*except* for placements marked `PROVISIONAL` pending feature envelopes.

**LLM role.** Low. This is computation; the LLM proposes candidate placements for
a solver to check.

**Knowledge-base role.** Sampling policies per motion class; standard probe sets —
escape probes, rotation probes, captivity probes.

**Next stage requires.** Poses, located frames, paths with sampling, swept
volumes, engagement sites, functional-region volumes, confirmed load paths.

---

### Stage 05 — feature and realization *(with S06 as an inner service)*

**Engineering question.** What actual geometry on which rigid group makes each
declared relation real, and what does that geometry demand of the layout?

**Engineering responsibility.** Realize every declared relation as named
geometry, and surface the constraints that geometry imposes back onto the layout.

**Must actively discover.** The feature that realizes each side of each
interaction; the feature pair that produces each declared limit; the geometry of
each compliant joint; the region of interest in which each interaction is to be
measured; and — the item that caused three of the worst late discoveries — the
**envelope constraints** features impose on layout parameters.

**Receives.** S03 + S04·B output.

**Outputs.** `Feature` on named rigid groups; `Realization` citing the
obligations it discharges with a verification predicate; feature pairs for every
blocking relation and every limit; compliant joint geometry; ROI definitions;
`Constraint` including `EnvelopeConstraint`; `Parameter` declarations with units;
a **total** `ConstructionProgram`; feature-level defeat specifications.

**Owns.** Features, realizations, constraints, the construction program, ROI
definitions.

**Never decides.** A `Body`, `RigidGroup` or `Joint` — it extends S03's (INV-001,
R-19). An obligation discharged by a label (INV-008). A null unit (INV-004).
**A parameter value, except by citing a solver artifact.**

**May remain unresolved.** Embodiment alternatives; underdetermined parameter
directions, recorded rather than resolved.

**Deterministic checks.** Every interface has a feature on **each** participant,
or a declared compliant joint; every blocking relation has a feature pair; every
limit has a producing feature pair; every obligation is cited by some realization
carrying a verification predicate; program totality — every referenced symbol
declared; no null unit; no parameter dependency cycle; **no feature intrudes into
a functional region** — a re-run of S04·B's occupancy against the new geometry;
and **every declared clearance and every declared interference-free pair has a
corresponding `Constraint`**.

**Why every clearance must become a constraint.** The convergence block can only
converge on constraints it has been given. In BM-003 the arm-to-clevis clearance
was never declared, so shortening the clevis produced a *build failure* that was
patched by hand rather than an *infeasibility* that triggered a re-solve — and
the lift-only regression rode along undetected for three revisions. Thirty-four
interactions become thirty-four constraints, which is trivial; the alternative is
silent manual patching.

**Geometry maturity.** Feature-level embodiment and parameterized construction
intent; dimensions unsolved.

**LLM role.** High for feature proposal and program shape; **none for
completeness**, which is enumeration over S03's relation set.

**Knowledge-base role.** Highest of any stage. Feature patterns per capability,
each carrying its envelope constraints and assembly implications.

---

### Stage 06 — parameter resolution

**Engineering question.** Do values exist that satisfy every constraint, and if
not, exactly which constraints conflict?

**Engineering responsibility.** Solve, or report precisely why not. Never
approximate a report of success.

**Receives.** S05's constraint system only.

**Outputs.** Per parameter a value or an explicit non-value status; residuals;
active set; margins; a solver status from the five-value vocabulary
(`feasible` / `infeasible` / `underdetermined` / `unsupported_formulation` /
`solver_failure`).

**Owns.** Nothing new; extends `Parameter` and `Constraint`.

**Never decides.** A defaulted unit (R-21). `feasible` for an underdetermined
system. One member of a solution family, silently. A deferred symbolic expression
(R-22). Copied values called solved (R-23).

**May remain unresolved.** Free directions in an underdetermined system —
recorded as `UnresolvedDecision`, never collapsed.

**Convergence contract.**

*Termination.* The block terminates on **a round budget** *N*, or on a
**repeated state**, where a state is the pair (unsatisfied-constraint set,
changed-parameter set). A repeated state is a genuine cycle and is reported as
one. **Termination is NOT by monotone reduction of the unsatisfied set.** That
rule was proposed and is wrong: replay BM-003 R1→R4 and round 1 fixes the
arm-to-clevis clearance while round 2 breaks the lift-only property — set size
unchanged at one, so a monotone rule terminates a problem that has a solution and
that we actually solved (shrink the arm *and* reduce the rib height). Real
constraint systems are not monotone.

*Scope.* The loop **may change** placements, dimensions and feature alternatives.
It **may not change** bodies, rigid groups, joints, interaction kinds, the DOF
disposition, load paths or assembly order. Any of those is an **escalation to
S03**, recorded as a `FailureProvenance` naming the owning decision. This is the
line that stops the loop meaning "redo the whole design", and applied to the
record it reproduces the manual severity judgements exactly: BM-002 `CHG-01` and
`CHG-03` are iterations, `CHG-02` is an escalation (it required an overhung
crank), BM-003 R1 and R4 are iterations, R2 is an escalation (a stop pad realizes
a previously undispositioned DOF).

*Budgets.* Two nested: at most **K feature alternatives per unsatisfied
constraint**, inside at most **N solver rounds**. Exhausting K escalates one
level — feature alternative → placement → dimension → S03. Every exhausted
alternative is retained as a `RejectedAlternative` with its reason.

*Non-convergence.* The block terminates with the solver's own vocabulary —
`infeasible` with a named conflicting set, or `underdetermined` with the free
directions — plus a `FailureProvenance` routing to the S03 decision that owns the
conflict. It never terminates by silently accepting the last state, and it never
produces a design.

Every round is a `StagePatch` with `stage_attempt` incremented; earlier attempts
are retained.

**On convergence.** Every placement marked `PROVISIONAL` at S04·B becomes
`AUTHORITATIVE`, and the invalidation cone marks every S04·B check whose inputs
moved as `STALE`. Those checks are re-run. This is the **geometric settlement
loop**, and it is the only feedback path outside S05↔S06.

**LLM role.** **None.** An LLM here re-introduces R-23.

---

### Stage 07 — geometry compilation

**Engineering question.** Does the declared program, with the solved values,
produce valid solids?

**Engineering responsibility.** Compile faithfully, report validity, export, and
fail loudly rather than repair.

**Receives.** The construction program and the resolved parameters. Nothing else.

**Outputs.** Compiled solids; per-body validity, positive volume and **single
connected solid**; a `GeometrySignature` taken from the kernel's own mass
properties on the **native** shapes before any export; native BREP then STEP
exports with independent re-import and comparison; an independent rebuild
determinism result.

**Owns.** `GeometrySignature`; compiled geometry as an extension of `Body` and
`Feature`.

**Never decides.** Anything. Specifically: it never consults the source,
requirements or candidates; never repairs an uncompilable statement — it fails
citing the statement and its dependency cone (INV-006, R-24); never uses an OCCT
face index as identity; never chooses a form, placement, axis or missing
dimension; never reads a `SCOUT` witness.

**Is it a pure compiler?** **Yes, plus a validity reporter.** All three
references' `build.py` files are exactly such compilers. But BM-003's hub built as
seven disconnected solids, and that is discoverable nowhere earlier. Compiler +
validity reporter + exporter, with no repair.

**Geometry maturity.** Authoritative solids. **This is where CadQuery becomes
authoritative and nowhere earlier.**

**Next stage requires.** Solids, signature, feature identities, and the declared
predicates **with their defeat specifications from S03 and S05**.

---

## 4. Stage inputs and outputs

| stage | receives | emits | becomes authoritative here |
|---|---|---|---|
| S01 | raw source text (exclusively) | requirements, clauses, freedoms, ambiguities, scenarios by kind, actors, quantity inventory | what the source says |
| S02 | S01 | obligations, load cases, candidates with created-obligations and evidence routes | what must be true; what loads exist; what is unevaluable |
| S03 | S02 | bodies, rigid groups, joints (direction), compliant joints, interfaces, **total DOF disposition**, blocking relations with defeat specs, provisional load paths, assembly steps, functional-region roles, configurations | the mechanism |
| S04·A | S03 | provisional envelopes, functional-region volumes, reach results, candidate elimination | which candidates are spatially possible |
| S04·B | S03 + S04·A | located frames (provisional), states, transitions with sampling, swept volumes, assembly sweeps, occupancy results, confirmed load paths | poses, paths, spatial feasibility |
| S05 | S03 + S04·B | features, realizations, compliant-joint geometry, ROIs, constraints incl. envelope constraints, parameters, construction program | the embodiment |
| S06 | S05 | values, residuals, active set, solver status | the dimensions; and placements promoted from provisional |
| S07 | program + values | solids, validity, signature, exports, determinism | the solids |

---

## 5. Geometry maturity progression

Twelve levels. **Earliest useful** and **latest safe** are different columns, and
the gap between them is exactly where scout geometry is legitimate.

| level | earliest useful | latest safe | authority when created | checks it enables |
|---|---|---|---|---|
| L0 no geometry | S01 | S02 | — | requirement and obligation coverage |
| L1 body / shape class | S02 | S02 | none | obligation ownership; candidate comparability |
| L2 topology | S02 sketch | **S03** | authoritative at S03 | DOF totality; acyclicity; interface classification |
| L3 symbolic spatial relations | S03 | S03 | authoritative | escape direction = −blocking direction; load-path connectivity |
| L4 frames and axis **directions** | S03 | S03 | authoritative | axis parallelism; DOF consistency with joint type |
| L5 envelopes | **S03 (scout)** | S04·A | provisional | packaging; reach; conservative AABB interference |
| L6 poses per state | S04·B | S04·B | authoritative | static interference; region occupancy; reach |
| L7 motion paths and swept occupancy | S04·B | S04·B | authoritative | path interference; swept occupancy of a reaction region; captivity across travel; assembly insertion |
| L8 feature-level embodiment | S05 | S05 | shape authoritative, size unsolved | feature-pair completeness; limit producers; ROI definition |
| L9 parameterized construction intent | S05 | S05 | authoritative | program totality; units; envelope constraints; dependency cycles |
| L10 solved geometry | S06 | S06 | authoritative | residuals; active set; feasibility status |
| L11 CAD solids | S07 | S07 | authoritative and frozen | validity; single connected solid; round-trip; determinism |
| L12 verified geometry | S09 | S09 | evidence | every declared predicate measured on its named feature |

### 5.1 CadQuery: scout and authority

**Authoritative at S07 only.**

**Useful as a scout from S03 onward.** The evidence is decisive: BM-002's three
`CHG` records, BM-003's `R1`, `R3` and `R5`, and BM-001's latch-finger/aperture
conflict would all have been visible in a throwaway solid one or two stages
before they were found.

A scout is a `Witness` with `fidelity: SCOUT`, under five rules:

1. **It may only *raise*, never *set*.** It may raise an `UnresolvedDecision`,
   propose a `Constraint`, or report a measured conflict. It may never supply a
   value, a pose, a form or a placement.
2. It may not CREATE or EXTEND any other entity.
3. It records the `parent_state_hash` it was built from and must be re-derivable
   from it.
4. **S07 must never read it.**
5. Every scout finding must be discharged — by a change the owning stage makes
   for its own reasons, or by a recorded decision not to. An undischarged finding
   blocks the stage gate.

**The mechanical defence against laundering.** A `Parameter` value's provenance
must cite a `Constraint`; a `Constraint`'s provenance must cite a requirement, an
obligation, a feature envelope or a load case — **never a witness**. A
scout-discovered number must therefore be justified independently before it can
be used, which is the strongest barrier available short of forbidding scouts.

---

## 6. Progressive commitment strategy

For each stage: what becomes authoritative, what must stay provisional, and what
must never be invented later.

| stage | becomes authoritative | deliberately provisional | must never be invented later |
|---|---|---|---|
| **S01** | what the source says; what it leaves open | nothing | a requirement; a magnitude the source never gave |
| **S02** | what must physically be true; the load cases; what is unevaluable | which candidate; every magnitude | an obligation discovered at CAD time; a load that appears only when a support is needed |
| **S03** | the mechanism: bodies, groups, joints, interfaces, DOF disposition, blocking relations, assembly order, termination strategy | every magnitude; axis placements; assembly direction feasibility | **a degree of freedom**; a blocking relation; a compliant joint; an interaction kind; a functional region |
| **S04·A** | which candidates are spatially possible; functional-region volumes | all extents (representative, `BOUNDED`); the winner until the gate | a functional region; an actor's reach requirement |
| **S04·B** | poses, paths, swept occupancy, sampling policy | placements dependent on feature envelopes | a state; a path; a sampling policy; an assembly path |
| **S05** | the embodiment: features, realizations, ROIs, the program | every dimension | a feature that realizes a relation; an envelope constraint; a limit producer |
| **S06** | the dimensions; promoted placements | free directions in an underdetermined system | a value without a solver artifact; a unit |
| **S07** | the solids | nothing | anything at all |

### 6.1 Design-space preservation rules

1. **A decision may be taken only when its discriminating evidence exists, and it
   names that evidence.** A decision citing none is `OPEN`.
2. **Three legal states only:** `RESOLVED` (with evidence), `BOUNDED` (a range or
   set, with why it cannot narrow), `OPEN` (alternatives, and what would settle
   it). Silence is not a state.
3. **Symbolic before metric.** Never write a number where a relation will do.
4. **A support assignment is `PROVISIONAL` until swept occupancy confirms its
   region is free in every state.**
5. **No dimension is frozen before the assembly path that constrains it.**
6. **No reaction interface in a load path is assigned before a load case
   exists**, even a purely directional one. The rule is scoped to *load-bearing*
   reactions: a **kinematic blocking relation needs no load case**, because its
   claim is that a path is geometrically unavailable and no force establishes it.
   BM-003 has roughly twenty-four blocked directions, all kinematic; requiring a
   load case for each would produce twenty-four magnitude-free load cases and
   bury the two that matter. The Oracles draw the same line — NRM-BM-003-010 is
   about mobility, NRM-BM-002-006 is about load.
7. **Material class may be declared; it may never be evidence** until a property
   route exists.
8. **Absolute scale, when the source gives none, is a declared free parameter
   with a representative value** — never a silent choice.
9. **Candidates die by stated geometric reason, never by score.**
10. **Choosing a mechanism partly because it can be evidenced is legitimate and
    must be recorded as such**, with the coverage gap it creates.

---

## 7. Stage-to-stage information flow

| boundary | consumer's question | minimum sufficient hand-over |
|---|---|---|
| S01→S02 | what must physically be true? | requirements; observables; scenarios **by kind**; actors; quantity inventory; ambiguities with block scopes |
| S02→S03 | what mechanism? | body hypotheses with roles; interaction hypotheses; obligations addressed **and created**; **load cases with direction classes**; evidence-route verdicts |
| S03→S04·A | can it fit and reach? | joint graph; configurations; body roles; **functional-region roles**; packaging obligations; actor reach requirements |
| S04·A→S04·B | which survivor, and at what scale? | the selection decision; provisional envelopes; functional-region volumes |
| S03→S04·B | does intended motion exist and forbidden motion not? | **total DOF disposition**; blocking relations with direction and blocker; assembly steps with order and access side; provisional load paths |
| S04·B→S05 | what geometry makes this real? | **located joint frames**; states with joint coordinates; paths with declared sampling; swept volumes; engagement sites; **metric functional regions**; confirmed load paths |
| S05→S06 | what are the values? | a closed constraint system; every symbol declared and united; envelope constraints from features |
| S06→S05 | did it converge? | values or an explicit status; residuals; active set; the conflicting set if not |
| S06→S04·B | what must be re-validated? | the invalidation cone of every promoted placement |
| S06→S07 | does it compile? | the construction program plus a value for every symbol it references |
| S07→S08 | how is each requirement checked? | solids; signature; feature identities; declared predicates **with defeat specifications** |

---

## 8. Required engineering objects

Every object that has emerged during development, classified. **Not everything is
a family.** The count goes from 32 to 37.

### Essential — new families (5)

| object | owner | why it must exist | evidence |
|---|---|---|---|
| **`RigidGroup`** | S03 | Makes DOF totality well-defined for a non-rigid part, and makes a deflected assembly configuration a *pose*. BM-001's compliant assembly is described in its own rationale as "a rigid inboard translation of the tab region… conserves volume exactly (0.000 mm³)" — that is a rigid sub-body at a pose. | BM-001-02 |
| **`LoadCase`** | S02 | NRM-BM-002-006 quantifies over "every element that carries a transverse or radial load in the declared operating scenario". Without it the domain of that statement is uncomputable and S03 assigns supports by pattern-matching on joint type (R-10). | BM-002 §2.4 |
| **`LoadPath`** | S03 provisional, S04·B confirmed | An ordered body chain from load to reaction, each hop naming its interface. BM-002 wrote exactly this graph by hand. | BM-002 §8 |
| **`FunctionalRegion`** | S03 role, S04·A volume | BM-001's 84 mm declared access was violated by a Stage-05 feature. Oracle `stage_expectations` s04 already requires `declared_usable_access_region`. | BM-001-02 |
| **`AssemblyStep`** | S03 order, S04·B path | Order, access side, relations activated, termination strategy. Subsumes `ENTITY_FAMILY_AUDIT` GAP-02. | BM-002 assembly; BM-003 R4/R7 |

### Essential — existing families, changed

| object | change |
|---|---|
| `Joint` | endpoints become rigid groups; **direction at S03, located frame at S04·B (provisional) → S06 (authoritative)**; gains a compliant joint type with mode, direction, bounded travel and activation window |
| `MobilityExpectation` | `forbidden_dof` ∪ `intended_dof` must be **total** over the DOF set |
| `Body` | may decompose into rigid groups; single-group bodies omit it |
| `Witness` | gains `fidelity: SCOUT` with the raise-only rule |
| `Configuration` | explicitly covers partial assemblies as well as operating arrangements |
| `Candidate` | gains created-obligations and an evidence-route verdict |
| `StagePatch` | gains the **invalidation cone** (moved from `FailureProvenance`) |

### Essential — cross-cutting fields, not families

| object | form |
|---|---|
| **Maturity** | `SYMBOLIC \| PROVISIONAL \| AUTHORITATIVE \| FROZEN` on every geometric value. Without it a scout-informed placeholder and a solved value are indistinguishable. |
| **Provenance** | four origins: source clause, derived-from-constraint, assumption, witness. A witness-origin value is inadmissible as authoritative. |
| **Frame**, **Pose** | value types on `Joint` and `State`. Never families. |
| **Defeat specification** | field on every constraining relation. |
| **Envelope** | field on `Body` per configuration, created at S04·A. |

### Essential — typed relations, not families

| object | form | note |
|---|---|---|
| **Retention / blocking** | `blocked_by(group, direction, blocker, features, configurations, defeat_spec)` | RELATE, per GAP-01's own recommendation |
| **Joint capture** | `retained_by(group, [group], configuration)` | GAP-01: neither retainer alone suffices |
| **Assembly precedence** | carried by `AssemblyStep` | GAP-02 resolved |

### Derived — must not become families

| object | what it actually is |
|---|---|
| **Support** | an `Interface` of contact kind that appears in a `LoadPath`. Adding a Support family would let a support exist with nothing to react. |
| **Contact** | an `Interface` with `interaction_kind: DECLARED_CONTACT`. |
| **Reaction** | the terminal hop of a `LoadPath`. |
| **Element load components** | **derived from the `LoadPath`, never stored.** Storing "this shaft carries a transverse load" reintroduces SF-5.3 at the data level: a candidate-independent-looking field about a candidate-dependent fact, which a later stage cannot tell was traced rather than assumed. |
| **Pose law** | derivable from located joint frames + joint coordinates. **Not authored.** This is what hid inside `build.py` in all three references, and deriving it removes the S07 input contradiction entirely. |
| **Motion path** | `Transition`. |
| **Assembly path** | `AssemblyStep` extended with its proven sweep. |

### Unnecessary

| object | why |
|---|---|
| **Function** | `Obligation` already carries it. A separate Function family invites role→geometry mapping, which is R-10 — the single most damaging Ver2 pattern. |
| **Compliance as its own family** | expressed as a compliant `Joint` between `RigidGroup`s. Reuses existing machinery and makes deformation-resolved assembly a pose. |
| **`EvidenceRoute` as design state** | it is a *pipeline capability*, not a property of the design. It belongs in a capability registry that S02 consults and S08 re-checks. |
| **`ScoutFinding` as its own family** | a `Witness` with `fidelity: SCOUT`. |

### Too early / too late as currently placed

| object | currently | should be |
|---|---|---|
| `NegativeControl` authorship | S08 | **declared at S03/S05** with the relation; scheduled and executed at S08/S09 |
| Joint axis placement | S03 | **S04·B provisional → S06 authoritative** |
| Evidence route classification | S08 | **S02** |
| Invalidation cone | S12 (`FailureProvenance`) | **every `StagePatch`** |

---

## 9. Consumer sufficiency analysis

The test: *rebuilding BM-001, BM-002 and BM-003 using only the previous stage's
output, would I ever need to reopen the benchmark, inspect CAD, invent
information, reinterpret requirements, or manually add engineering knowledge?*

Three iterations were required. The first two found real gaps; the third is
clean.

### Iteration 1 — gaps found and closed

| boundary | what I would have had to invent | fix now in the proposal |
|---|---|---|
| S02→S03 | what load the crank shaft carries, in order to decide whether it needs a thrust face | `LoadCase` with direction classes |
| S03→S04·B | that BM-001's cover must stay captive **at full open**, not only when closed | DOF disposition is total **per configuration** |
| S04·B→S05 | BM-001's 84 mm access volume, in order to know the latch finger must not intrude | `FunctionalRegion` with a metric volume at S04·A |
| S04·B→S05 | how BM-001's cover behaves when its tabs are deflected | `RigidGroup` + compliant `Joint`; the deflected state is a pose |
| S07→S08 | which feature to remove to defeat BM-003's outward stop | defeat specification declared at S03 |

### Iteration 2 — the residual circularity

Attacking again, one boundary still failed. **S04·B cannot place BM-002's crank
axis**: its height came from `4.0 + 2.0 + 45.0 + 9.0`, and the 9 is a pin-boss
radius that does not exist until S05.

Rejected fixes: moving axis placement to S05 (S04·B then cannot compute swept
volumes); requiring S03 to guess (that is `CHG-01` again).

**Accepted fix — the geometric settlement loop.** S04·B places the axis
provisionally from envelope-level information; S05 emits the envelope constraint;
S06 solves; the placement is promoted to authoritative and the invalidation cone
marks the S04·B checks whose inputs moved as stale; they re-run. Bounded like the
inner loop.

This means **the pipeline is not a DAG**, and the proposal says so plainly rather
than discovering it during implementation.

### Iteration 3 — final walk

| boundary | BM-001 | BM-002 | BM-003 | verdict |
|---|---|---|---|---|
| S01→S02 | ✓ | ✓ travel band and payload carried as stated | ✓ quantity inventory records "none" | **sufficient** |
| S02→S03 | ✓ retention obligation; compliance route flagged unavailable | ✓ payload and gravity load cases | ✓ state-maintenance principle as a candidate property | **sufficient** |
| S03→S04·A | ✓ | ✓ enclosure obligation | ✓ | **sufficient** |
| S04·A→S04·B | ✓ scale declared free, representative value | ✓ scale partly fixed by travel | ✓ scale declared free | **sufficient** |
| S03→S04·B | ✓ all three human-review findings appear as undispositioned DOF | ✓ platform rotational DOF force the guides | ✓ over-swing appears as an undispositioned DOF | **sufficient** |
| S04·B→S05 | ✓ access volume; deflected poses | ✓ swept occupancy refutes the rear-panel journal | ✓ heel sweep known before the pad is placed | **sufficient** |
| S05→S06 | ✓ | ✓ arm envelope constrains axis height | ✓ ring seat derived from the heel | **sufficient** |
| S06→S04·B re-validate | — | ✓ axis moved; BDC clearance re-checked | ✓ arm radius moved; lift-only property re-checked | **sufficient** |
| S06→S07 | ✓ | ✓ | ✓ | **sufficient** |
| S07→S08 | ✓ defeat specs present | ✓ | ✓ | **sufficient** |

**One residual, accepted and named.** BM-001's HCR-BM001-008 — that implementing
a latch as a separate body plus knob, shaft, boss and socket is *disproportionate
to its function* — is not caught by any check and should not be. It is
engineering judgement. The pipeline's obligation is to **surface the input**: a
part count and feature count per discharged obligation, **reported, never scored**
(R-16). Seeing it is achievable; deciding it is human.

---

## 10. Remaining open questions

Seven of the critical review's eight questions are settled in §11. These remain
genuinely open.

**O-1 — Can an LLM produce a reliable total DOF disposition?**
The domain is enumerated mechanically and three of the four dispositions are
checkable. `IRRELEVANT_BECAUSE` is cross-checked against load cases, which
narrows it but does not close it. The failure mode is a plausible reason for an
omission — exactly what happened three times to a careful human on BM-001.
*Mitigation to measure during implementation: the rate at which a disposition is
overturned by S04·B.*

**O-2 — How many candidates survive S04·A?**
The two-pass split makes the gate affordable in principle. Nobody has measured
the elimination rate. If S04·A eliminates few, the cost problem returns at S04·B.

**O-3 — Is the scout boundary enforceable in practice?**
The provenance rule (a parameter cites a constraint; a constraint may not cite a
witness) is a real barrier, not a complete one. A determined author can
manufacture a constraint to justify a scouted number.

**O-4 — Does an affordable compliance route exist?**
A reduced-order beam model for a cantilever snap is not FEA and might be
tractable. If one exists, four rejected BM-001 Oracle fixtures become buildable
and the Oracle's permissiveness becomes testable for the first time. If none
does, mechanism selection stays biased toward what can be evidenced.

**O-5 — Is nominal-only geometry a permanent boundary?**
Every clearance in all three references is nominal. Without tolerance, "practical
to manufacture" is permanently unevaluable and every fit is a nominal fit.
Accepting this permanently is a real decision about what the pipeline is for.

**O-6 — Do the frozen Oracle `stage_expectations` survive the S05/S06 loop?**
§11 D-6 argues yes, because those expectations are about *what must exist*, not
about ordering, and both lists exist at convergence. This needs an explicit
ruling from whoever owns the Oracle freeze; it is not mine to make.

**O-7 — How is the geometric settlement loop bounded in practice?**
"Each round strictly reduces the unsatisfied set" is a heuristic. BM-002 needed
three rounds and BM-003 needed eight. Neither is evidence that a bound exists in
general.

---

## 11. Rationale for every major architectural decision

**D-1 — Seven stages, numbering preserved.**
The Oracle packs are frozen and their `stage_expectations` reference `s01`–`s12`
by name. Renumbering invalidates frozen artifacts for cosmetic gain. S04's two
passes and the S05/S06 loop are *within-stage structure*, not new stages.

**D-2 — Compliance is a `Joint` between `RigidGroup`s, one per compliant member,
not a new region family.**
BM-001's own rationale describes the deflected assembly configuration as "a rigid
inboard translation of the tab region… conserves volume exactly". That is a rigid
sub-body at a pose. Modelling it this way: makes DOF totality well-defined for
non-rigid parts (settling critical-review Q-2); makes a deformation-resolved
assembly path an ordinary `Transition`; reuses existing machinery; and leaves the
door open for a reduced-order compliance route later, because mode, bounded
travel, the compliant element and its root — exactly a beam model's inputs — are
already declared.

The falsification pass sharpened the granularity: **one rigid group and one
compliant joint per compliant member**, because
`REG-COVER-RETAIN-LEFT-COMPLIANT` lists two beams and two ears — two physically
independent cantilevers whose joint modelling as one rigid group would assert a
coupling that does not exist. The behaviour that binds them is co-actuation by a
`Transition`, which already exists. It also separated `required_travel` from
`allowable_travel`, because one number cannot be both a kinematic fact and a
material limit, and only the first is knowable here.

**D-3 — Load is represented symbolically and directionally, never numerically
unless the source gives a number; and element load components are derived, never
stored.**
NRM-BM-002-006 quantifies over load-carrying elements, so the domain must be
computable. But BM-002's honest reasoning — "no axial force is produced in the
declared scenario, so demanding a thrust feature is the error corrected at
SF-5.3" — needs only a direction class. Requiring magnitudes would force
invention; requiring nothing leaves S03 assigning bearings by joint type, which
is R-10.

The falsification pass made the ownership split sharper than "S02 owns loads,
S03 owns paths". NRM-BM-002-006's own derivation premise settles it: *"which
components a given element carries depends on the conversion family selected, not
on the requirement"*, and its exclusion — closing finding **SF-5.3** — warns that
universalising a reaction across conversion families "would encode one family".
Therefore `LoadCase` is candidate-independent, `LoadPath` is candidate-specific,
and **what each element carries is a projection of the path, never a stored
field**. Storing it reproduces SF-5.3 in the data model, where it is
undetectable.

It also added the second driver. A constraint may exist because a load must be
reacted **or** because the conversion cannot function without it —
NRM-BM-002-007 exclusion (b). A lead-screw nut is anti-rotated for the second
reason and no load case will ever justify it.

**D-4 — S03 owns assembly *order and access side*; S04 owns direction
feasibility.**
Settles critical-review Q-1. BM-002's forced +X insertion was derived from a
metric comparison — the arm's radius against the bore's — but the comparison is
at *envelope* level, not feature level. So S03 fixes what may be decided
symbolically (order, which face, the termination strategy) and S04·A/B proves the
rest. Assigning both to S03, as the information plan did, was too strong.

**D-5 — The selection gate sits between S04·A and S04·B.**
INV-007's principle is right and hard-won: Ver2 selected before the evidence and
scored by part count, so incompleteness won. But demanding full swept feasibility
per candidate is unaffordable — the Oracles list seven and five admissible
fixtures, and the manual process carried two, one and one. Splitting the fidelity
keeps the principle and pays for it.

**D-6 — S05 and S06 keep both numbers and both contracts, but the boundary is a
loop.**
Two stages that must iterate are one stage with an inner loop; calling them two
invites a sequential implementation with a re-entry path bolted on. But merging
and renumbering breaks frozen artifacts. The guard against R-23 does not need a
sequential barrier: it needs the rule that **S05 may not set a value except by
citing a solver artifact**.

The falsification pass replaced the termination rule. "Each round strictly
reduces the unsatisfied set" is wrong and would have terminated BM-003 R1→R4 as
`underdetermined` on a problem that has a solution: fixing the arm-to-clevis
clearance broke the lift-only property, leaving the set the same size, and the
real fix changed two parameters. Termination is now a round budget plus
repeated-state cycle detection. The pass also made the loop's scope a rule —
placements, dimensions and feature alternatives only — which reproduces the
manual severity judgements without judgement, and it required a `Constraint` for
every declared clearance, without which the loop has nothing to converge on. The frozen `must_exist` lists for s05
(`construction_program`, `solver_problem`) and s06 (`solved_values`,
`constraint_residuals`, `active_constraints`) are all present at convergence.

**D-7 — The pose law is derived, never authored.**
With located joint frames and joint coordinates, poses are computable. This
removes the contradiction between INV-006's input restriction and what S07's
consumers need, and it extracts the one piece of design information that was
hiding inside `build.py` in all three references. It also means S03's joint graph
must be **simulation-complete** — which makes CAD/simulation parity structural
rather than checked, since the multibody model becomes a projection instead of a
re-derivation.

**D-8 — Maturity is a field, not a stage property.**
Within one S04·B patch, envelopes are authoritative while placements dependent on
feature envelopes are provisional. Without per-value maturity there is no way for
a check to refuse immature input, which is how a proxy result gets cited as a CAD
result. This is what makes the geometric settlement loop expressible at all.

**D-9 — The invalidation cone moves to every patch.**
It exists today only on `FailureProvenance` at s12, so invalidation fires only
after a failure is attributed at the end. BM-003's `R5` is the counter-example: a
dimension change silently destroyed a functional property and nothing was marked
stale because nothing had failed *yet*.

**D-10 — Negative controls are declared where the relation is declared.**
Three benchmarks produced controls that could not fire — two on BM-002, one on
BM-003 — every time because the control defeated a proxy for the mechanism rather
than the mechanism. A control authored from geometry writes what the geometry
suggests; a control authored from the declaration tests what the design claims.
The second half matters equally: a control must assert that any *surviving* stop
names a **different blocker**, which is only expressible if the blocker was named.

**D-11 — Totality replaces declaration wherever the domain is enumerable.**
`MobilityExpectation` today requires the forbidden set to be *declared*, which is
correct and insufficient: a declared set that omits a DOF cannot fail. All three
BM-001 human-review rejections and BM-003's `R2` were omissions from declared
sets. No new family is needed — this is a field-level change, which respects
`ENTITY_FAMILY_AUDIT`'s discipline of not inflating the family count.

**D-12 — Evidence-route capability is consulted at S02 and lives outside
DesignState.**
BM-001 rejected four admissible Oracle fixtures because their primary geometry
needs strain, friction or hoop-stress answers the toolchain cannot give; BM-002
chose a design with no press, snap or interference fit anywhere; BM-003 declared
the one state-maintenance class with an available route. Each was recorded, none
had an owner, and the aggregate effect is that the Oracle's permissiveness has
never been tested. But the route is a property of the *pipeline*, not of the
design, so it belongs in a capability registry rather than in design state.

**D-13 — Five new families, and no more.**
Every candidate object was tested against the question `ENTITY_FAMILY_AUDIT`
should have asked: *is there engineering content with no home?* Support, contact,
reaction, pose law, motion path and assembly path are all derived. Function is
unnecessary and actively dangerous — it invites role→geometry, which is R-10.
Compliance, scout findings and evidence routes are expressible without new
families. What remains genuinely homeless is exactly five things.

---

*Sources: `ver3/contracts/`, `ver3/phase0/`, `ver3/oracles/` (eight packs),
`ver3/cad_validation/` (three executable references with their rationales,
validators, human review decisions and defect records),
`docs/PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md`,
`docs/PIPELINE_CRITICAL_DESIGN_REVIEW.md`. Nothing was implemented or modified.*
