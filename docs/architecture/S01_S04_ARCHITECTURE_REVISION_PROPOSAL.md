# S01–S04 ARCHITECTURE REVISION PROPOSAL

Status: **PROPOSAL FOR REVIEW.** Nothing here is implemented.

No code, contract, prompt, validator or fixture is modified by this document. No benchmark
is rerun. Every decision below is stated so that it makes sense for an unseen mechanical
design problem and for any competent language model; benchmark identifiers appear only in
the evidence column that explains *why* a requirement exists.

---

## §0 EVIDENCE BASIS AND NON-GOALS

**Basis.** `P4B_FINAL_SYNTHESIS.md` §3 (capabilities C-01…C-22), §18 (requirements
R-1…R-15) and §21 (traceability, frozen). Supporting chains in P1–P3, P4A, P5 (incl. §20)
and P6.

**Non-goals.**
- Not a patch plan for `s03.py`, `s04.py`, `projection.py` or `run_window2.py`.
- Not tuned for any benchmark, mechanism family, or provider.
- Not a design for S05+.
- Not a set of new validators.

**The design question.** *What is the smallest coherent architecture in which an
inexpensive language model can reason like a competent mechanical designer through
S01–S04, while deterministic code performs only bookkeeping and strict logical
consequence?*

---

## §1 WHAT THE AUDIT ESTABLISHED

Six results shape everything below.

1. **Progressive enrichment is the right model and the additive half works.** In the
   audited corpus nothing was deleted or overwritten. The problem is not memory.
2. **The dominant recurrent continuity failure is consumer sufficiency.** A stage can hold
   a fact in state and not give it to the reader that needs it. The most consequential
   instance: the stage that places joints in space is not given the spatial arrangement its
   own prompt tells it to work in.
3. **Deterministic code crossed from bookkeeping into engineering authorship at two exact
   points**, and in both cases the manufactured value was then validated by a check testing
   the property the manufacturing code guarantees.
4. **The model's recognition capability is real and unused.** Where it names the defect the
   same artifact commits, the failure is gating, not reasoning.
5. **Several concepts the architecture treats as first-class are not addressable**: a
   blocking relation cannot be referenced, a transmitting interaction has no typed home, an
   external reaction site cannot be named.
6. **No engineering property is established by an evaluator independent of its producer**,
   and the maturity construct covers only the two stages where no physical defect occurs.

---

## §2 DESIGN PRINCIPLES DERIVED FROM EVIDENCE

**P-1 — Sufficiency before economy.** A consumer view is first sized to the reasoning it
must perform, and only then compressed. *(R-1)*

**P-2 — Absence is never an assertion.** No deterministic path may convert "no evidence"
into a positive engineering claim. A domain may be total while the function over it is
explicitly partial. *(R-6)*

**P-3 — Anything the architecture calls a relation must have an identity.** If an entity
can be referred to, it must be resolvable. *(R-10)*

**P-4 — One semantic type per concept, agreed by producer, contract and consumer.** *(R-14)*

**P-5 — A commitment is a claim about the design, and claims bind.** A later stage may
refine or supersede with a stated reason; it may not silently contradict.
*(R-5 — **the capability need is evidence-supported; the mechanism proposed to meet it is a
preferred candidate, not frozen.** See §13.0 and §26.1.)*

**P-6 — Assurance must not test the property its producer guarantees.** *(R-7)*

**P-7 — Recognised uncertainty must be able to have a consequence.** Not every open item
blocks; the conditions under which one does must be defined. *(R-8)*

**P-8 — Context is bounded semantically, never by a silent slice.** Overflow is a recorded
condition, not a truncation. *(R-1, R-15)*

**P-9 — The model is asked for engineering judgement; the machine is asked for
consequence.** Enumeration, expansion, unit-consistency, graph closure and geometry are
machine work. What must be true, why, and what remains open is model work.

---

## §3 PRESERVED STRENGTHS, AND WHY EACH SURVIVES

| Preserved | Why it survives the audit |
|---|---|
| **Accumulated persistent DesignState** | The audit found no persistence failure; the model is correct and is the substrate every other requirement needs *(P4B §2)* |
| **Additive StagePatch semantics** | CREATE-only behaviour produced no loss; the revision keeps additive default and makes revision explicit rather than removing it |
| **Absence-is-not-success conservatism** | Five distinct absence statuses; the one construct the evaluation layer got right *(P6 §11)* |
| **Explicit unresolved reasoning** | The strongest engineering output in the corpus; the revision changes what happens to it, not that it exists *(C-20)* |
| **Quantity extraction with qualifier preservation** | Correct in every trial where the source states a quantity *(C-03)* |
| **Candidate-independent `LoadCase` / candidate-specific `LoadPath`** | The split is sound: the world's demand does not depend on the mechanism chosen. Retained unchanged in ownership |
| **Compliance as a `Joint` type between rigid groups of one body** | Avoids a separate ownerless family; the audit found no defect in the *concept*, only in its field completeness |
| **Graph connectivity as a mechanical property** | A real, cheap, mechanism-independent check that fired correctly *(P6 §11)* |
| **Genuine swept-hull computation with interior sampling** | Correct geometry, correctly conservative; the defect was the fabricated *declaration*, not the computation |
| **Deterministic exhaustive enumeration of a domain** | Legitimate and valuable — it is what makes an omission detectable *(P4B §12)* |
| **Explicit provider/run provenance** | Model substitution, requested-vs-sent parameters, clamping and truncation all recorded per call |
| **Worst-status-wins within an evidence tier** | Prevents a passing pass masking an incomplete sibling |
| **Honest NOT_VERIFIED semantics** | No-overlap proves clearance, overlap proves nothing; no manufactured failures anywhere |
| **No response repair** | 59/59 stored artifacts byte-identical to raw text; repair would measure the repair |

---

## §4 CAPABILITY REQUIREMENTS (inputs, restated)

R-1 consumer sufficiency · R-2 spatial state to the spatial stage · R-3 required
distinctness · R-4 state distinguishability · R-5 binding commitment *(PROVISIONAL)* ·
R-6 deterministic/authorship separation · R-7 non-self-fulfilling assurance ·
R-8 uncertainty bounds commitment · R-9 independent assurance · R-10 relation
addressability · R-11 typed home for transmission · R-12 external reaction closure ·
R-13 visible capture failure · R-14 canonical shapes · R-15 valid maturity construct.

---

## §5 REVISED ACCUMULATED DESIGNSTATE SEMANTICS

### 5.1 The distinction the model must make impossible to blur

> **Present in DesignState ≠ available to the next reasoning stage.**

The revision enforces this by making the *view* an artifact in its own right. Every stage
invocation records the **ConsumerView** it was given — its content, the sufficiency
declaration it was built against, and whether that declaration was met. A downstream reader
can then distinguish "the pipeline never knew" from "the pipeline knew and did not say".
*(R-1; addresses P4B question 2 structurally rather than by convention.)*

### 5.2 Per-family semantics

Every family declares, in one place:

| Facet | Meaning |
|---|---|
| **semantic identity** | what the entity *is*, independent of any field name |
| **owning stage** | the only stage that may CREATE it |
| **persistence** | instances persist; nothing is deleted |
| **field mutability** | each field is `IMMUTABLE` (owner-set, final), `EXTENDABLE` (a named later stage may add it, once), `SUPERSEDABLE` (replaceable only via an explicit revision record) or `DERIVED` (never stored; computed on demand) |
| **provenance** | required method and evidence reference; a derived value names its premises |
| **maturity** | the evidence class of the value, not of the entity |
| **dependencies** | which values this one was computed from |
| **invalidation** | when a dependency changes, dependents become `STALE`; STALE is a readable state, and a consumer view must disclose it |
| **referenceability** | whether other entities may point at it, and by what id |
| **consumers** | the stages that declare a need for it |

### 5.3 Four mutation modes, and only four

`CREATE` (owner, once) · `EXTEND` (named stage, named field, once, never over an existing
value) · `SUPERSEDE` (both retained, reason required, dependents marked STALE) ·
`RECORD` (unresolved / rejected / evidence — additive, never overwriting).

**Direct mutation of stored entities outside these modes is not part of the architecture.**
Every value that reaches authoritative state does so through a validated patch with
provenance. *(R-5; addresses the unguarded path P4B §2 recorded.)*

### 5.4 Derived-not-stored, restated

A value that is a projection of other state is computed on demand and carries its premise
set. This preserves the existing principle and extends it: **a derived value with an
incomplete premise set is not computed at all** — it is reported as underivable, naming the
missing premise. *(R-6, P-2.)*

---

## §6 REVISED STAGE RESPONSIBILITIES

Boundaries are re-derived, not assumed. §21 tests whether they should change; the outcome
is that **the S01/S02/S03/S04A/S04B split survives, with one responsibility moved and one
gate made real**.

### S01 — Problem interpretation

**Purpose.** Convert a request into typed statements about what is required, what is
undetermined, and what the world around the product is.

**Must answer.** What does the text require? What does it leave free? What is genuinely
ambiguous? Who or what acts on the product, and what must they reach? What lies outside the
product in each scenario, and can therefore react a load?

**May create.** Source clauses; requirements; scenarios with an explicit **system
boundary**; actors; freedoms; ambiguities; assumptions; **candidate external sites** derived
from each scenario boundary.

**Must not decide.** Any mechanism, material, dimension or resolution of an ambiguity.

**Guaranteed output semantics.** Each requirement is **atomic**: it carries exactly one
verifiable obligation-bearing proposition. Where the source binds two propositions in one
sentence, S01 emits two requirements sharing a source locator. **Non-atomicity is a
declarable condition, not a silent merge** — if S01 cannot separate them it says so, and
that statement is a first-class output. *(R-13, C-01)*

**Unresolved it may leave.** Any ambiguity, with what would resolve it and what it blocks.

**Maturity transition.** Requirements are `SOURCE_VERBATIM` or `SOURCE_DERIVED`; nothing is
`AUTHORITATIVE`.

**Before consumption.** Every source proposition maps to at least one requirement or to a
recorded reason why it does not.

### S02 — Physical obligation, demand and principle

**Purpose.** Establish what must physically be true, what the world does to the product, and
which families of mechanism could satisfy both.

**Must answer.** What must be true regardless of mechanism? What physical effects must occur
between which roles? What loads act, and where may each be reacted? Which principle families
could serve, and which of their claims can this toolchain evidence?

**May create.** Obligations (with derivation premises, scope, earliest satisfiable stage,
evidence route); **candidate-independent LoadCases**; **PhysicalEffectObligations** (§9);
**ReactionSiteRequirements** (§9); candidates with a principle assignment; acceptance
predicates; unresolved decisions.

**Must not decide.** Any body, joint, interface, count, dimension or position. **No
selection.**

**Responsibility moved here.** S02 must now state, at role level and mechanism-independently,
*what physical effect must be transmitted between what* — the gap C-07 identifies. Without
it, S03 synthesises a mechanism from a one-sentence summary. *(R-11)*

**Maturity transition.** Obligations are `SOURCE_DERIVED` or `ENGINEERING_KNOWLEDGE`; every
candidate carries an evidence-route verdict.

**Before consumption.** Every requirement is cited by an obligation; every load case names a
reaction site *requirement* that the scenario boundary places outside the product; every
candidate's principle assignment is complete for the function classes its obligations imply.

### S03 — Mechanism topology, interaction and constraint

Two passes, retained: one response could not carry both, and the audit found the split
itself sound.

**S03·A — topology.** Bodies, rigid groups, joints (type, groups, DOF, axis), interfaces,
configurations, functional regions. **Must not** state any magnitude, position or axis
placement.

**S03·B — interaction and constraint.** `PhysicalInteraction` instances (§9),
`ConstraintRelation` instances (§10), load paths, assembly order.

**Must answer.** What things exist and what does each do? What connects what, and how? What
physically transmits each required effect? What holds each body where it is put, against
what, in which configurations, and how would a test defeat it? How does each load reach an
external site? In what order does it go together, and what retains each part?

**Must not decide.** Position, dimension, axis placement, or which candidate wins.

**Guaranteed output semantics.** Every `PhysicalEffectObligation` from S02 is discharged by a
named `PhysicalInteraction` **or** carried forward as unresolved. Every `ConstraintRelation`
is addressable. Every load path terminates at a declared external reaction site or is
recorded as unclosed.

**Maturity transition.** Topology is `AUTHORITATIVE` for identity and connectivity;
`SYMBOLIC` for direction; nothing spatial exists.

**Before consumption.** The joint graph is connected; every joined body pair has an
interface; every required effect is discharged or open.

### S04·A — Coarse spatial realization and comparability

**Purpose.** Give each retained candidate a provisional arrangement sufficient to decide
whether it can fit, reach and be assembled at all — and to make candidates *comparable*.

**May create.** Body extents and centres in one relative frame; region volumes; reach
results; assembly directions; **an elimination record with a geometric reason**.

**Must not decide.** Which candidate wins. Any authoritative dimension.

**Maturity.** All spatial values `PROVISIONAL`, and — this is new — **`COMPARABLE`**: the
arrangement is fit for comparison across candidates, not for embodiment.

### The selection gate — a real gate

Between S04·A and S04·B. It is not a stage; it is a **commitment event with preconditions**
(§16). It produces either a `SelectionDecision` with equal-coverage evidence, or an
`UnresolvedDecision` recording that the candidates remain indistinguishable and why.

### S04·B — Committed spatial and kinematic realization

**Purpose.** Place the selected mechanism and describe its motion so that clearance,
incidence and distinctness can be computed.

**Must receive.** The S04·A arrangement of the selected candidate. *(R-2 — this is the
single most consequential change.)*

**May create.** Joint frames (origin **and** axis); configuration coordinates; transitions
with the coordinates that change and a motion path at a declared evidence level.

**May extend.** S04·A extents, within declared refinement semantics (§13).

**Must not decide.** Anything that contradicts an S04·A commitment without an explicit
supersede record.

**Maturity.** Joint frames `PROVISIONAL` at S04·B, promotable later; motion evidence carries
its own level (§14).

---

## §7 PRODUCER-CONSUMER SUFFICIENCY ARCHITECTURE

### 7.1 The contract

Each stage declares a **Consumer Sufficiency Contract**: the *semantic facts* it requires,
not the families it wants. Each declared need names:

- the **fact class** (e.g. "the spatial arrangement of every body in the selected
  candidate", "every quantity of class *length* constraining a body extent");
- its **kind** — authoritative upstream fact · derived projection · provenance/reference ·
  unresolved fact · spatial commitment · quantitative constraint · topology relation;
- whether it is **required** or **contributory**;
- the **reasoning step** that consumes it.

### 7.2 Who establishes that the declaration itself is complete

**This is the load-bearing question, and §7.1 alone does not answer it.** A stage that
declares too little can be proved "sufficient" against its own understatement. That would
reproduce the whitelist omission at a higher level of abstraction, and it must be closed
before anything else in this proposal is worth implementing.

**The closure: the required set is derived, not declared.**

**(1) Responsibility is not owned by the stage.** The authoritative source of a stage's
engineering responsibility is its **stage responsibility contract** — the normative
statement of which engineering question the stage answers and which entity families and
fields it may create. It is not the prompt, not the implementation, and not the stage's own
sufficiency declaration.

**(2) Required fact classes are derived from the stage's declared *outputs*.** Every output
field a stage may create declares its **semantic dependencies** in the entity-family
contract: what the value is expressed relative to, what it must be consistent with, and what
it references. The **derived minimum input set** of a stage is the union of the semantic
dependencies of every output field it may create.

> A field whose contract says it is *expressed in the frame of the arrangement* thereby
> makes the arrangement a required input. No one has to remember to ask for it.

**(3) The declaration is bounded below and may only be widened.** A stage may add
**contributory** needs — facts that improve its reasoning. It **may not declare fewer than
the derived minimum**. A declaration narrower than the derivation is a contract violation,
not a preference.

**(4) A stage may not self-validate its own sufficiency.** It may propose contributory
needs. It may not author the required set, and the check that the *declaration* is adequate
is a different check, with different inputs, from the check that the *view* satisfies the
declaration.

### 7.2.1 Four-way independence

| Artifact | Authored by | Read by the sufficiency check? |
|---|---|---|
| **stage responsibility** | normative contract | **yes — this is the essential one** |
| **derived required needs** | deterministic derivation over output-field dependencies | yes |
| **declared contributory needs** | the stage | yes, but they can never reduce the required set |
| **generated view** | the substrate | yes |
| **sufficiency assurance** | the assurance layer, never the stage | — |

> **An assurance check that reads only the declaration and the view is structurally
> incapable of detecting an omitted need.** It must read the output contract from which the
> requirement derives. This is stated as a prohibition because it is exactly the shape of
> the failure the audit found.

### 7.2.2 Distinguishing an omitted need from an unnecessary fact

Three signals, none of them benchmark-specific:

1. **Derivation** — a fact class is necessary iff some output field the stage may create
   declares a semantic dependency on it. A class nothing depends on is not needed, and its
   absence is not a finding. This is the primary test and it is mechanical.
2. **Contradiction against accumulated state** — a stage produces a value that contradicts an
   authoritative value present in accumulated state and absent from its view. The
   contradiction is detectable *because* the accumulated state has the value, and it is
   positive evidence that the class was needed. This converts an omission into an
   observable event rather than a silent one.
3. **The producer's own unresolved layer as a sufficiency sensor** — a stage that records an
   unresolved item naming a fact class which *exists in accumulated state* is reporting an
   omitted need in its own words. The audit established that this recognition capability is
   real and precise, and that nothing consumed it; here it is given a consumer.

Signals 2 and 3 are **detectors, not the guarantee.** The guarantee is signal 1. The
detectors exist because a derivation is only as complete as the dependency declarations it
reads.

### 7.2.3 Why the recursion terminates

The obvious objection is regress: if a need list can be incomplete, so can a dependency
declaration. The regress terminates for a structural reason, and the difference is not
cosmetic.

| | consumer need list *(rejected as the primitive)* | output-field semantic dependency *(the primitive)* |
|---|---|---|
| scope | global — "everything this stage's reasoning requires" | local — "what this one field's value means" |
| completeness test | **none exists**; a missing entry looks exactly like a fact that was not needed | **mechanical** — every field of a given kind must declare its referent, e.g. every spatial value declares its frame, every reference declares its target family |
| who can check it | nobody, without redoing the engineering | a structural check over the contract |
| failure signature | silent | the field has no defined meaning, which is itself a finding |

So the residual risk is not eliminated; it is **moved to a place where it has a completeness
test.** That is the whole claim, and it is the reason this design is proposed rather than a
longer whitelist.

### 7.2.4 What would make consumer sufficiency self-fulfilling

Design prohibitions, stated so that a later reviewer can test for them:

- deriving the declaration from the view that was sent, or from what the stage happened to use;
- letting the consuming stage author its own required set;
- an assurance check whose only inputs are the declaration and the view;
- defining "sufficient" as *"every declared class was present"* with no term referring to
  responsibility;
- silently demoting an unmet required class to contributory to make a call proceed;
- treating a stage's successful execution as evidence that its view was sufficient.

**The operative definition, therefore:**

> **Consumer-view completeness ≠ "all facts listed in the declaration happened to be
> present."** It is: *every fact class on which the stage's permitted outputs semantically
> depend is present in the view, at sufficient maturity, and any that is not is recorded as
> an attributable insufficiency.*

### 7.3 Three consequences

**(a) The view is built from the declaration**, not from a hand-maintained family list. A
family list cannot express "the arrangement of the *selected* candidate" and cannot notice
that a needed fact class is absent — which is exactly how the arrangement and the quantities
were lost.

**(b) Sufficiency is evaluated before the call.** If a required fact class has no instance in
accumulated state, that is an **upstream insufficiency** — attributable to the producer. If
it has instances that the view does not carry, that is a **projection failure** —
attributable to the boundary. **These are different findings and must not be conflated**;
the audit spent significant effort separating them after the fact.

**(c) Budget overflow is a status, never a slice.** When a semantically sufficient view
exceeds the budget, the architecture must reduce it by *semantic* means — reference-by-id
with expansion on demand, role-level summarisation of homogeneous collections, omission of
contributory (never required) classes — and **record what was reduced and by which rule**. A
view that cannot be made sufficient within budget is a recorded condition, not a silently
truncated prompt. *(R-1, P-8)*

---

## §8 CANONICAL REPRESENTATION MODEL

For every concept crossing a producer-consumer boundary, exactly one of each:

| | Rule |
|---|---|
| **Semantic type** | one, declared independently of field names |
| **Ownership** | one creating stage |
| **Authoring responsibility** | model-authored, deterministically derived, or hybrid — declared, never ambiguous |
| **Reference model** | if referenceable, it has an id; a reference resolves or the patch is refused |
| **Consumer interpretation** | one, stated in the sufficiency contract |

Applied to the six audited failures:

| Failure | Resolution |
|---|---|
| `principle` in three shapes | **one type**: a mapping from function class to principle family, since a candidate performs several function classes. Prompt, contract and consumer state the same shape; a single-principle candidate is a one-entry mapping |
| `BodyHypothesis` / `PhysicalInteractionHypothesis` ownerless | **neither name survives.** Replaced by `PhysicalEffectObligation` at S02 (role-level, mechanism-independent) and `PhysicalInteraction` at S03 (the realisation). §9 |
| `blocked_by` non-addressable | becomes `ConstraintRelation`, a first-class entity with an id. §10 |
| `required_by_actors` / `reach_targets` prompt-only | the *need* is real — reach cannot be evaluated without it. It becomes part of the functional-region type, declared in the contract, not invented in a prompt |
| `addresses_obligations` divergence | one field, one meaning: the obligation ids this entity exists because of. Required on every entity a stage creates to discharge an obligation |
| `MobilityExpectation` authorship ambiguous | split into **domain** (deterministic) and **disposition** (authored or strictly derived). §11 |

---

## §9 PHYSICAL-EFFECT, LOAD AND SUPPORT REASONING

### 9.1 What S02 must supply before topology synthesis is legitimate

The audit's C-07 shows S03 receiving a principle name and a one-sentence summary, then
inventing bodies. The missing layer is **what must physically happen**, stated without
naming a mechanism.

**`PhysicalEffectObligation`** (S02, role level):

- the **effect** required — transmit force, transmit motion, convert motion, permit motion,
  prevent motion, locate, contain, meter;
- **between which roles** (never bodies — they do not exist yet);
- **under which LoadCase or Scenario**;
- the **obligation** it discharges;
- whether the effect must persist, be intermittent, or be releasable.

This is mechanism-independent: it says a force must pass from the actuation role to the
closing role, not that a linkage does it.

### 9.2 What S03 must do with it

**`PhysicalInteraction`** (S03·B): the realisation. It names the two rigid groups, the effect
it transmits, the interface or feature at which transmission occurs, the configurations in
which it is active, and the `PhysicalEffectObligation` it discharges.

**Crucially, it is not a `Joint`.** A joint *constrains*; an interaction *transmits*. The
audit's four cases — an interlock, a screw driving a jaw, a spring returning a pedal, an
input driving an output — all had the transmission stated in prose because there was no type
for it. Now the discharge is checkable: **every `PhysicalEffectObligation` is discharged by a
named interaction or is open.** *(R-11)*

### 9.3 Load and reaction closure

Four distinct things, separately owned:

| Concept | Stage | Meaning |
|---|---|---|
| requirement load | S01 | a quantity the source states |
| **LoadCase** | S02 | candidate-independent: what the world does, on which role, reacted at which **ReactionSiteRequirement** |
| **ReactionSiteRequirement** | S02 | a typed, addressable site derived from a scenario's system boundary, marked **external** or **internal** |
| **LoadPath** | S03·B | candidate-specific: the ordered hops from application to the reaction site |
| element consequence | derived | never stored |

**The closure rule, stated generally.** A load path is *closed* when its terminal hop
resolves to a `ReactionSiteRequirement` marked external for the scenario in which the load
acts. A path terminating inside the product, or at an actor, is **open** — a legitimate,
recordable state, not an error to be hidden. Whether an actor may be a reaction site is a
property of the scenario boundary S01 recorded, not a rule about hands. *(R-12)*

This makes the "grounded to the world" problem representable for the first time: the world
is not a body, and it never was — it is an external reaction site, and now it has a type.

---

## §10 RETENTION / BLOCKING / RELEASE

**`ConstraintRelation`** — first-class, addressable, one per *(retained group, constrained
direction or DOF set, configuration set)*:

| Field | Meaning |
|---|---|
| id | referenceable *(R-10)* |
| retained group | what is constrained |
| dofs, direction | what is removed, and in which sense |
| provider | the body **or** the external reaction site that provides the constraint |
| site | the interface or feature at which it acts |
| configurations | where it holds |
| maintaining interaction | reference to the `PhysicalInteraction` that maintains it, where one does |
| defeat condition | what a test would do to defeat it |
| driver | why it must exist |
| provenance / evidence | authored or derived, with premises |

**Two questions become separately answerable**, which is the whole point:
*"is this DOF constrained?"* → the relation exists;
*"what physically constrains it?"* → `provider` + `site` + `maintaining interaction`.

**Release is a state change, not a note.** A releasable constraint names the transition that
defeats it; the architecture can then ask whether that transition actually changes the
maintaining interaction (§14). No latch, catch or detent semantics appear anywhere — this is
a general constraint model.

**No sentinel values.** A provider is a resolvable reference or the relation is incomplete.
"No direction" is expressible only where the constraint genuinely removes all directions, and
that is a distinct, declared case — not a string.

---

## §11 DETERMINISTIC vs ENGINEERING-AUTHORSHIP BOUNDARY

### 11.1 The rule

> **Deterministic code may derive a semantic value only when its premises are present,
> typed, referenceable and sufficient. Absence of evidence is never a premise.**

### 11.2 Applied to mobility

| Act | Owner |
|---|---|
| enumerate the complete domain: every rigid group × configuration × rigid-body DOF | **deterministic** — legitimate, valuable, makes omission detectable |
| mark a DOF `INTENDED` because a joint of a known class leaves it free | **deterministic consequence** — premise is the authored joint |
| mark a DOF `CONSTRAINED` because a `ConstraintRelation` covers it | **deterministic consequence** — premise is the authored relation, and the cell *references* it |
| mark a DOF `IRRELEVANT` because it is unloaded and unactuated in a named scenario | **authored**, then cross-checked against LoadCases |
| a DOF with none of the above | **`UNDISPOSITIONED`** — a first-class value naming the cell and what is missing |

**`UNDISPOSITIONED` is the architectural correction.** The audited pipeline had no way to say
"nothing is known here", so it said "a joint class holds it". Now:

- **Domain totality** is a deterministic property and is trivially true. It is bookkeeping and
  is reported as such.
- **Disposition completeness** is a separate, measurable engineering property: *what fraction
  of the domain is dispositioned by evidence, and which cells are not.*

The second is what a reviewer needs and what the audited system could not express. No value
equivalent to *"joint class of no joint"* can exist, because the branch that produced it is
replaced by an explicit statement of ignorance. *(R-6, P-2)*

### 11.3 Applied elsewhere

Legitimate deterministic work: domain enumeration; expansion of an authored relation over the
DOFs and configurations it declares; graph connectivity; unit and frame consistency; AABB and
swept-hull geometry from authored numbers; alias binding **with the rename recorded**.

Not deterministic work: any default for an absent required field. A missing required value is
a recorded incompleteness, never a substituted constant.

---

## §12 S03 → S04 TOPOLOGY-SPATIAL CLOSURE

**The failure to prevent:** a spatial stage that receives a topology and treats it as a fresh
problem.

**Continuity requirements.** The S04 sufficiency contract declares, and the architecture must
be able to supply and preserve:

| Fact class | Why |
|---|---|
| body and rigid-group identity | placements attach to identities, not to positions in a list |
| joint incidence — which groups, hence which bodies | a joint origin means nothing without the bodies it joins |
| **mechanically required distinctness** | where two joints serve distinct kinematic roles, the topology must be able to *say so*, so realization can be checked against it |
| axes and their frames | direction is S03's; placement is S04's; both must be present at S04·B |
| link relationships | which body carries which pair of joints — the premise for non-degeneracy |
| repeated-member correspondence | *(provisional, C-16)* if N elements are instances of one member, that must be typed, not inferred from prose |
| configuration membership | which bodies are present in which configuration |
| engagement sites | where an interaction acts, so a placement can be checked against it |
| support and guidance relations | which interactions carry load or constrain a path |
| prior spatial commitments | §13 |

**Required distinctness, stated generally.** S03 can declare that two joints must occupy
distinct locations *because their kinematic roles require it* — for example, two joints of one
rigid link, or two joints whose relative offset is the mechanism's transmission. This is a
topological statement with no dimension in it, and it makes the spatial question checkable
without any geometry knowledge downstream. **This is the mechanism-independent replacement for
"the crank must have a radius".** *(R-3)*

---

## §13 S04·A → S04·B REFINEMENT SEMANTICS

### 13.0 Status of this section — SELECTED PROVISIONAL ARCHITECTURE

**R-5 is the one requirement the frozen audit marks PROVISIONAL** (`P4B_FINAL_SYNTHESIS.md`
§21). Everything in this section, in §5.3's `SUPERSEDE` mode, in §16's invalidation
semantics and in migration unit **M-4** rests on it, and must not be presented as frozen
alongside the fourteen FINAL requirements.

**Two things are separated and carry different weight:**

| | Statement | Standing |
|---|---|---|
| **capability need** | *Later-stage reasoning must not silently invalidate the premises on which an authoritative commitment depends.* | **evidence-supported**; a spatial refinement that contradicts an earlier arrangement, and a selection whose premises change beneath it, are both observed shapes |
| **architectural mechanism** | commitment classes + supersede-with-reason + invalidation cone + STALE selection | **PREFERRED CANDIDATE PENDING R-5 CLOSURE** — coherent and self-consistent, but not the only design that meets the need |

**What must be closed before this mechanism is frozen** — this is P4B unresolved question 4:
*why does an unguarded direct write into stored entities exist alongside a defined,
validated `EXTEND` operation that is never exercised?* The answer determines whether
declaring commitment classes is sufficient, or whether the substrate must also make
out-of-band writes structurally impossible. Those are different architectures with different
costs, and the evidence does not currently choose between them.

**Not resolved by assumption here.** The mechanism below is written out in full because a
candidate must be specific enough to be criticised — not because the question is settled.
Alternatives that remain open are recorded in §26.1.

Every S04·A spatial value carries a commitment class:

| Class | Meaning | S04·B may |
|---|---|---|
| **PROVISIONAL** | a placeholder consistent with topology | refine freely within declared constraints |
| **COMPARABLE** | fit for cross-candidate comparison; the basis on which the gate ran | refine, but a change that would alter the comparison must supersede with a reason |
| **AUTHORITATIVE** | established by evidence | not applicable at S04·A |
| **OVERTURNABLE WITH REASON** | provisional, and a downstream stage has standing to contradict it | supersede with an explicit geometric reason, marking dependents STALE |

**S04·B receives the S04·A arrangement and extends it.** It may not author a fresh coordinate
system. A value it changes is a `SUPERSEDE` with a reason and an invalidation cone — both
retained. *(R-5, R-2)*

**Selection interacts with this.** If the gate ran on `COMPARABLE` arrangements and S04·B
supersedes one materially, the gate's premise has changed and the selection is marked STALE.
That is the concrete meaning of "a commitment binds".

---

## §14 STATE, TRANSITION AND PATH SEMANTICS

**A configuration is not a label.** Each `Configuration` carries a **distinguishing basis**:
the set of *(rigid group, DOF)* pairs whose values distinguish it from its named siblings.
S03 authors it — it is a mobility statement, not a geometry statement — and S04·B must
realise it.

**Then three properties become checkable without any mechanism knowledge:**

1. **Physical distinctness.** Two configurations sharing a distinguishing basis must differ in
   at least one of its coordinates. *(R-4)*
2. **Intended motion actually changes.** A transition declares which coordinates change; the
   realisation must change them. A transition whose declared coordinates are unchanged is a
   recorded contradiction. *(C-17)*
3. **Release changes the maintaining interaction.** A transition that defeats a
   `ConstraintRelation` must alter the interaction that maintains it — the two are linked by
   reference, so this is a graph question, not a geometry question. *(§10)*

**Motion evidence by level, not everywhere.** A path claim carries an explicit evidence level:

| Level | Meaning | Appropriate at |
|---|---|---|
| `ENDPOINTS_ONLY` | two states, no interior | never sufficient for a clearance claim |
| `SAMPLED` | interior samples actually evaluated, with the sample set recorded | S04·B for coarse clearance |
| `SWEPT` | swept occupancy computed over the path | S04·B where a clearance claim is made |
| `CONTINUOUS` | analytic or simulated | later stages only |

**A declaration of sampling policy is not evidence.** The level is a property of the
*computation performed*, recorded with its result — never a constant asserting that sampling
was intended. *(R-6, C-18)*

---

## §15 QUANTITATIVE CONTINUITY

**Not "pass every quantity everywhere".** A consumer declares the **quantity classes** its
reasoning depends on; the sufficiency mechanism supplies every authoritative constraint of
those classes from accumulated state.

A `Quantity` is one type: value-or-status, unit, qualifier preserved verbatim, class,
provenance, maturity. `UNSUPPORTED` is a legitimate value distinguishable from absence.

**The invariant:**

> A stage may not declare a quantity class unknown when an authoritative constraint of that
> class exists in accumulated state. It may declare it *unconstrained* — but that is a
> statement about the accumulated state, not about the stage's view.

Classes are derived from consumer responsibilities, not fixed in advance; the audit's evidence
supports at least dimensional extent, travel, clearance, force and load, angular range, and
tolerance, but the list is a consequence of what stages declare, not a constant. *(R-1, C-05)*

---

## §16 PROGRESSIVE COMMITMENT AND GATING

### 16.1 Operational semantics

| Concept | Definition |
|---|---|
| **UnresolvedItem** | a recorded openness: the decision, why it is open, alternatives typed, what keeps it open, **and what it blocks** |
| **blocking** | an unresolved item is blocking *for a stage* when it names a fact class that stage's sufficiency contract marks required |
| **maturity** | the evidence class of a value; a check declares the minimum maturity of its inputs and refuses below it |
| **provisional commitment** | a value asserted to enable downstream reasoning, marked as such, revisable |
| **comparable candidate** | a candidate whose evidence covers the same obligation set, at the same maturity, as every other retained candidate |
| **selected candidate** | exists only after comparability holds across all retained candidates |
| **authoritative commitment** | a value whose premises are all present, typed and at sufficient maturity |
| **invalidation / reopening** | a superseded premise marks dependents STALE; a STALE input to a check makes the check's prior result void, not false |

### 16.2 What blocks, and what does not

**Not every open item blocks.** An item blocks when — and only when — it names a fact class
required by the sufficiency contract of the stage about to run, or by the gate about to fire.
An item about a later stage's concern is carried, not blocking. This is a mechanical test on
declared needs, not a severity judgement. *(R-8, P-7)*

### 16.3 The gate operates on engineering evidence

The selection gate fires only if: every retained candidate has evidence at equal obligation
coverage and equal maturity; no unresolved item blocks selection; and every candidate's
evidence-route verdict is recorded. A tie is an `UnresolvedDecision`, never a pick.

**The gate does not author the verdict on its own preconditions** (§27.2). All three
conditions are computable from committed state by a reader that is not the gate; the gate
consumes that verdict. A gate that fires without an externally computed precondition verdict
is itself a `FALSE_ACCEPTANCE`.

**The two poles become reachable.** A stage that declines a claim it cannot support emits
`SAFE_REJECTION` — a success of restraint. A commitment made over a blocking unresolved item,
or over a check whose inputs were below its declared minimum maturity, is `FALSE_ACCEPTANCE`.
The audit found both defined and unemittable; here they are the natural outputs of the gate.

---

## §17 ASSURANCE ARCHITECTURE

### 17.0 Two rules, deliberately separated

R-9 is easy to inflate into "everything must be independently validated", which is neither
what the evidence supports nor achievable. Two distinct rules are intended, and merging
them would make the architecture incoherent.

**Rule A — maturity minimum (a claim about a stage).**

> **At least one meaningful engineering property per stage must be independently
> established before that stage may be described as having demonstrated engineering
> assurance.**

This is R-9 as the audit states it. It is a floor on development maturity, and it exists
because the audit found *zero* such properties across all stages — every Layer-B check was
co-located with its producer and invoked by the same tool.

**Rule B — claim semantics (a claim about a value).**

> **Any individual property asserted as `ENGINEERING_ESTABLISHED` must carry assurance
> appropriate to that assertion — including sufficient independence and inputs at or above
> the check's declared minimum maturity.**

**Rule B does not require every stored property to be validated.** A property may
legitimately and permanently remain:

| status | meaning |
|---|---|
| `NOT_ESTABLISHED` | no check of sufficient independence has evaluated it |
| `NOT_VERIFIED` | a check ran and its result is honestly inconclusive |
| `PROVISIONAL` | asserted to enable downstream reasoning, revisable |
| `EVIDENCE_INCOMPLETE` | a check exists but its inputs are below its declared minimum maturity |

**What is prohibited is inheritance.** An unassured property must never acquire
`ENGINEERING_ESTABLISHED` by proximity — not from a sibling that was checked, not from its
stage completing, not from its patch validating, not from an aggregate badge. Establishment
attaches to a property and to nothing else.

**Consequence for reporting.** A stage may correctly be described as *executed*,
*contract-complete*, and *carrying values at high evidence maturity*, while most of its
properties are `NOT_ESTABLISHED`. That is an honest and expected state, not a defect, and it
is the state the audit found the pipeline actually to be in.

### 17.1 The independence rule

> **An assurance check may not test a property that the producer of its input guarantees by
> construction.** For every check, the architecture records what would make it self-fulfilling
> and what independence it has.

Independence has three degrees, and each check declares which it has:

| Degree | Definition |
|---|---|
| **STRUCTURAL** | reads committed state only; never invoked by the producing stage; cannot see the producer's intermediate values |
| **PREMISE** | recomputes the property from premises the producer did *not* choose — e.g. checking a placement against a topology the placer did not author |
| **EXTERNAL** | evaluates against an artifact authored independently of the implementation |

### 17.2 Categories

| Category | Information required to evaluate | Who may produce it | Self-fulfilling if… | Required independence |
|---|---|---|---|---|
| schema / reference integrity | typed state + reference model | deterministic | the writer and the checker share the reference rule | STRUCTURAL |
| **consumer sufficiency** | the sufficiency declaration **and** the view actually sent | view builder records both | the declaration is derived from the view | STRUCTURAL |
| deterministic consistency | premises + derived values | derivation records premises | the check tests the derivation's own guarantee | PREMISE |
| mechanical topology consistency | bodies, groups, joints, interactions, constraints | S03 | — | PREMISE |
| **spatial / topology closure** | topology **and** placements | S03 + S04 | the placer also defines incidence | PREMISE |
| state / transition realization | distinguishing bases + coordinates + motion evidence | S03 + S04·B | evidence level is a constant | PREMISE |
| quantitative consistency | quantities + consumer class declarations | S01/S02 + consumer | — | STRUCTURAL |
| evidence / provenance integrity | provenance + maturity on every value | all | provenance is defaulted | STRUCTURAL |
| progression / commitment validity | gate preconditions + unresolved items | gate | the gate records its own precondition as met | EXTERNAL preferred |

### 17.3 Where assurance runs

**Not inside the stage, and not invoked by the tool that ran the stage.** Assurance reads
committed state after a patch is applied. This is the minimum structural independence that
makes the co-location finding go away; it is not a claim that co-located checks are worthless
— several audited ones are good — but they cannot be the *only* layer. *(R-9, R-7)*

---

## §18 STATUS AND MATURITY SEMANTICS

Four constructs, never merged, never collapsed into one badge:

| Construct | Asserts | Does not assert |
|---|---|---|
| **EXECUTION** | the model returned, the response parsed, the schema validated | anything about the design |
| **CONTRACT COMPLETENESS** | every required output is present and typed | that any value is correct |
| **EVIDENCE MATURITY** | *per value*: the class of evidence behind it | that the value is right |
| **ENGINEERING ESTABLISHMENT** | *per property*: an independent check with sufficient-maturity inputs found it to hold | that the design is good |

**Rules.** A stage is never "mature" because it executed and filled a schema. A property with
no check of sufficient independence is `NOT_ESTABLISHED` — **distinct from failing, and a
legitimate permanent state** (§17.0 Rule B). The four constructs never substitute for one
another: execution does not imply contract completeness, contract completeness does not
imply evidence maturity, and evidence maturity — which is a property of a *value's
provenance* — never implies engineering establishment, which requires an independent check. A metric may
not reward specificity the input cannot support: a fabricated numeric predicate must not score
above an honest declaration that no quantity is available, because that inverts
`SAFE_REJECTION`. **No numeric weighting is proposed here**; the constructs come first.
*(R-15, C-22)*

---

## §19 TOKEN AND MODEL ECONOMY

| Work | Assignment |
|---|---|
| **LLM-authored** | what must be true and why; what things exist and what each does; what physically transmits what; what constrains what and how a test would defeat it; what remains open |
| **Deterministically enumerated** | domains — DOF cells, body pairs, configuration pairs, obligation coverage |
| **Deterministically derived** | strict consequences with present premises; geometry from authored numbers; graph properties |
| **Retrieved from reusable knowledge** | principle families **with what each creates and what claims it depends on** — the audited system had this and rendered only the names |
| **Projected to the consumer** | exactly the declared sufficiency, expanded on demand |
| **Retained only in state** | everything else, addressable by id |
| **Independently evaluated** | §17 |

**Three economy rules.**
1. Sufficiency is established first; compression is applied second and recorded.
2. Compression is semantic — reference-by-id, role-level summarisation of homogeneous
   collections, dropping contributory classes — never positional.
3. **A view that cannot be made sufficient within budget is a recorded condition.** Silent
   truncation is not a compression strategy; it is undetected information loss.

**The load-reducing move is not a bigger prompt.** It is making intermediate engineering state
explicit: a model asked "what constrains this group, and where" answers better than one asked
to invent a mechanism and its justification in one pass. That is why the physical-effect layer
(§9) is added rather than a larger S03 context.

---

## §20 ARCHITECTURAL ALTERNATIVES CONSIDERED

### 20.1 Consumer views

| | **A: family whitelist** *(audited)* | **B: whole state** | **C: declared-need views** *(selected)* |
|---|---|---|---|
| requirement coverage | fails R-1, R-2 | satisfies R-1 | satisfies R-1, R-2 |
| semantic clarity | list says nothing about why | none | need names the reasoning step |
| token cost | low | very high, grows with state | bounded by declaration |
| LLM burden | may lack a fact | must filter noise | targeted |
| observability | cannot detect a missing class | cannot attribute a miss | sufficiency is checkable |
| complexity | trivial | trivial | moderate — declarations must be maintained |
| premature-commitment risk | high (silent absence) | moderate | low |

**Selected: C.** B is explicitly rejected: it makes every stage's cognitive load grow with
accumulated state and still cannot distinguish "absent upstream" from "not projected".

### 20.2 Mobility dispositions

| | **A: LLM authors every cell** | **B: deterministic fill with fallback** *(audited)* | **C: domain enumerated, dispositions derived from authored relations, remainder UNDISPOSITIONED** *(selected)* |
|---|---|---|---|
| token cost | very high — hundreds of cells | none | low |
| deterministic legitimacy | full | **violated** — absence becomes assertion | full |
| observability | complete | totality self-fulfilling | disposition completeness measurable |
| provenance | per cell | fabricated | each cell references its premise or names its absence |

**Selected: C.**

### 20.3 S04·A → S04·B

| | **A: independent problems** *(audited)* | **B: shared state, S04·B extends** | **C: shared state + explicit refinement/supersede semantics** *(selected)* |
|---|---|---|---|
| continuity | none | good | good, and contradiction is visible |
| invalidation | none | implicit | explicit cone, selection can be marked STALE |
| complexity | lowest | low | moderate |

**Selected: C.** B alone cannot express a *legitimate* contradiction, which the design must
permit — S04·B may discover that an S04·A arrangement is infeasible.

### 20.4 Assurance placement

| | **A: inline with stages** *(audited)* | **B: separate layer over committed state** *(selected)* | **C: adversarial re-derivation** |
|---|---|---|---|
| independence | none | structural + premise | highest |
| cost | lowest | moderate | high |
| self-fulfilling risk | high | low | lowest |

**Selected: B**, with C available for the small number of properties where premise
independence is insufficient. C everywhere is rejected on cost with no evidence it is needed.

### 20.5 Physical-effect layer

| | **A: none** *(audited)* | **B: revive BodyHypothesis / PhysicalInteractionHypothesis** | **C: role-level PhysicalEffectObligation at S02 + PhysicalInteraction at S03** *(selected)* |
|---|---|---|---|
| mechanism independence | n/a | **poor** — "body" pre-empts topology at a stage that must not decide it | good — roles, not bodies |
| discharge checkable | no | partially | yes, by reference |
| new families | 0 | 2 | 2, with clear ownership |

**Selected: C.** B is rejected on the substantive ground that naming bodies at S02 violates
the stage's own prohibition, not because the names are old.

---

## §21 SELECTED ARCHITECTURE, AND WHETHER THE BOUNDARIES SURVIVE

Each boundary tested against: coherent responsibility · sufficient inputs · meaningful output
maturity · bounded cognitive load · explicit producer-consumer semantics.

| Boundary | Verdict | Reason |
|---|---|---|
| **S01 / S02** | **unchanged** | Coherent; INV-002 clean; the audit found no continuity defect here. S01 gains an atomicity obligation, which is a responsibility clarification, not a boundary move |
| **S02 / S03** | **unchanged, responsibility added** | The gap is not the boundary but S02's under-delivery. Adding a physical-effect layer *inside* S02 is the minimal change; a new stage would add a hand-off without adding a distinct engineering question |
| **S03·A / S03·B** | **unchanged** | Evidence-supported: one response could not carry topology and relations together, and the questions differ |
| **S04·A / gate / S04·B** | **unchanged in position, changed in kind** | The split is right — comparability then commitment. What was missing is that the gate was vacuous and the boundary lost the arrangement. Both are fixed without moving the boundary |

**No stage is merged or split.** Where equally capable designs existed, minimal structural
change was preferred, per the brief. The changes are to *what crosses* the boundaries and to
*what binds* across them.

---

## §22 REQUIREMENT → ARCHITECTURE TRACEABILITY

| Req | Evidence | Mechanism | Owner | Producer | Consumer | Det. vs LLM | Assurance observability | Gating effect | Later testable by |
|---|---|---|---|---|---|---|---|---|---|
| R-1 | C-05, C-12 | Consumer Sufficiency Contract + recorded ConsumerView (§7) | shared substrate | view builder | every stage | deterministic | sufficiency category, STRUCTURAL | unmet required class blocks the call | a declared class present in state and absent from the view is a finding |
| R-2 | C-12, C-13 | arrangement is a required class in S04·B's contract (§7, §12) | S04·B | S04·A | S04·B | deterministic | spatial closure, PREMISE | S04·B cannot run without it | placements checked against the arrangement they extend |
| R-3 | C-14, C-15 | required-distinctness declaration on topology (§12) | S03 | S03·A | S04·B, assurance | LLM declares, det. checks | spatial closure, PREMISE | violation is a finding, not a silent pass | two joints declared distinct sharing a location |
| R-4 | C-17 | Configuration distinguishing basis (§14) | S03 | S03·A | S04·B, assurance | LLM authors, det. compares | state realization, PREMISE | contradiction recorded | two configurations equal on their basis |
| R-5 **PROVISIONAL** *(need supported; mechanism is a preferred candidate — §13.0)* | C-19 | commitment classes + supersede-with-reason + invalidation cone (§13, §5.3) | shared substrate | any stage | assurance, gate | deterministic | progression validity | superseding a gate premise marks selection STALE | a changed COMPARABLE value with no supersede record |
| R-6 | C-11, C-18 | domain/disposition split; `UNDISPOSITIONED`; premise rule (§11) | S03 + substrate | det. enumerates, LLM authors | assurance | both, separated | deterministic consistency, PREMISE | disposition completeness is a reported quantity | a disposition with no resolvable premise |
| R-7 | C-11, C-18 | independence degrees; self-fulfilling disclosure (§17) | assurance layer | assurance | reviewer | deterministic | meta | — | a check whose property its input's producer guarantees |
| R-8 | C-20 | blocking defined by the consumer's required classes (§16.2) | substrate | any stage | gate, stages | deterministic | progression validity | a blocking item stops the call or the gate | commitment with a blocking item open |
| R-9 | C-21 | assurance over committed state, not stage-invoked (§17.3); **Rule A** floor + **Rule B** claim semantics (§17.0) | assurance layer | assurance | reviewer | deterministic | meta | — | **Rule A:** at least one engineering property per stage established by a check of declared independence. **Rule B:** no property carries `ENGINEERING_ESTABLISHED` without assurance appropriate to that claim. Unassured properties remain `NOT_ESTABLISHED`, which is not a failure |
| R-10 | C-10 | `ConstraintRelation` and `PhysicalInteraction` as addressable entities (§9, §10) | S03·B | S03·B | mobility, assurance | LLM authors, det. expands | reference integrity, STRUCTURAL | unresolvable reference refuses the patch | a nested reference resolving to nothing |
| R-11 | C-07 | `PhysicalEffectObligation` → `PhysicalInteraction` discharge (§9) | S02 → S03·B | S02, S03·B | S03, assurance | LLM both ends | topology consistency, PREMISE | undischarged effect blocks or is open | an effect obligation with no interaction and no open item |
| R-12 | C-08 | `ReactionSiteRequirement` typed external/internal from the scenario boundary (§9.3) | S01/S02 | S01, S02 | S03·B, assurance | LLM authors, det. checks closure | quantitative + topology | an open path is recorded, not hidden | a terminal hop that is not an external site |
| R-13 | C-01, C-02 | atomicity obligation + non-atomicity as a declarable condition (§6 S01) | S01 | S01 | S02, assurance | LLM authors | schema + evidence integrity | a declared non-atomic requirement is an open item | a source proposition with no requirement and no reason |
| R-14 | C-06, C-09 | one semantic type per boundary concept (§8) | contract | contract | all | n/a | schema integrity, STRUCTURAL | shape violation refuses the patch | a field carrying two shapes across runs |
| R-15 | C-22 | four separated status constructs (§18) | assurance + reporting | assurance | reviewer | deterministic | meta | — | a maturity claim covering a stage it has no term for |

**Infrastructure rows** — mechanisms present only to support the above, labelled as such:
recorded `ConsumerView` (supports R-1, R-9); commitment classes (support R-5, R-2); evidence
levels on motion (support R-4, R-6).

**No requirement is without a mechanism. No mechanism is without a requirement.**

---

## §23 S04 → S05 READINESS CONTRACT

S05 may consume the design only when S04 guarantees:

1. **Selection is legitimate** — a `SelectionDecision` exists with equal-coverage,
   equal-maturity evidence, or S04 terminates with a recorded tie.
2. **Topology is closed in space** — every body placed; every joint's origin and axis present
   and consistent with the bodies it joins; every declared required-distinctness satisfied;
   every declared repeated-member correspondence realised *(provisional)*.
3. **Every configuration is physically distinct on its declared basis**, and every transition
   changes the coordinates it declares.
4. **Every clearance or interference claim carries its evidence level**, and no claim rests on
   `ENDPOINTS_ONLY`.
5. **Every load path is closed at an external reaction site, or is explicitly open** with the
   openness recorded as blocking or non-blocking for S05.
6. **The DOF domain is total and its disposition completeness is reported**, with every
   `UNDISPOSITIONED` cell named.
7. **Every value carries provenance and maturity**, and nothing S05 requires is below the
   minimum maturity S05 declares.
8. **No blocking unresolved item is open** for any fact class S05's sufficiency contract marks
   required.
9. **No `FALSE_ACCEPTANCE` is outstanding.**

Anything not on this list is not a precondition, and S05 design is out of scope here.

---

## §24 MIGRATION IMPLICATIONS

Coherent units, not a patch sequence. **No file is edited by this document.**

| Unit | Nature | Classes of artifact affected |
|---|---|---|
| **M-1 Representation closure** | contract-first | entity-family definitions; the typed-relation model; ownership matrix; the concepts in §8–§10 |
| **M-2 Sufficiency substrate** | new shared capability | per-stage sufficiency declarations; view construction; the recorded `ConsumerView`; budget policy |
| **M-3 Authorship boundary** | replaces two derivations | the mobility derivation; the motion-evidence representation; the defaulting sites §11.3 names |
| **M-4 Commitment substrate** *(**PROVISIONAL** — pending R-5 closure, §13.0)* | extends the patch layer | commitment classes; supersede-with-reason; invalidation cone made operative; treatment of out-of-band writes. **The capability need is established; this mechanism is the preferred candidate and must not be implemented ahead of P4B question 4** |
| **M-5 Gate** | makes an existing concept real | selection preconditions; the two poles' emission points |
| **M-6 Assurance layer** | new layer | checks relocated to read committed state; independence declarations; self-fulfilling disclosure |
| **M-7 Status constructs** | reporting and metrics | the four constructs; maturity coverage over S03/S04; metric construct validity |
| **M-8 Stage prompts and schemas** | derived from M-1/M-2 | every stage's asked-for content follows the semantic model, not the reverse |
| **M-9 Evidence substrate** | evaluation | fixtures; the replay path's pairing guarantee; what a window run is permitted to claim |

**Ordering constraint, not a schedule.** M-1 precedes M-8, because prompts must follow the
semantic model rather than define it — the audit found several fields whose only definition
was a prompt. M-2 precedes any claim about a stage's competence, because until sufficiency is
established, a stage's failure cannot be attributed.

---

## §25 EXPLICITLY REJECTED PATCH-STYLE APPROACHES

| Rejected | Why |
|---|---|
| a check comparing the origins of one specific named joint pair | treats one symptom; the arrangement is still absent and the next distinctness case is unprotected. **This rejects the case-specific check, not the general invariant — see the note below** |
| add `Envelope` to the S04 family whitelist | fixes one class silently; the whitelist remains unable to notice the next missing class |
| pass the whole DesignState to every stage | destroys token economy, grows cognitive load with state, and still cannot attribute a miss |
| raise the render limit | moves the cliff; silent slicing remains the failure mode |
| ban the string `"NONE"` | the concept needs a type, not a banned token |
| require a defeat specification field to be non-empty | non-emptiness is what the audited system already tested; it is why `"None"` passed |
| a check asserting that *all* joint pairs have nonzero separation | not a mechanical truth — coincident axes are legitimate in many mechanisms; the invariant must be conditioned on a declared premise, not applied universally |
| use a stronger model | the audited failures are dominated by information the model never received |
| add mechanism knowledge to prompts | product-noun → mechanism mapping is the retirement row the architecture exists to avoid |
| tune sampling density | the defect is that a constant was recorded as evidence, not that the constant was wrong |

### 25.1 What is *not* rejected: conditional non-degeneracy

The rows above are easy to over-read, so the boundary is drawn explicitly.

**Rejected — a benchmark-shaped patch:**

> *"A particular case produced a zero-length crank, therefore add a zero-length-crank
> check."*

Rejected because it encodes one mechanism, fires on one geometry, and leaves every other
degeneracy unprotected.

**Also rejected — an over-general invariant:**

> *"All joint pairs must have nonzero separation."*

Rejected because it is false as a mechanical statement.

**Retained, and required — a conditional general invariant:**

> **Where upstream topology establishes that two kinematic sites must be distinct for a
> mechanical relationship to exist, spatial realization must establish that the required
> distinctness is preserved.**

This is mechanism-independent. It fires **only** where the engineering premises require
distinctness, and the premise is authored upstream by the stage that owns topology — not
inferred downstream from geometry, and not written into a validator as product knowledge.
A degenerate realization is then a *contradiction of a declared topological premise*, which
is exactly the kind of thing assurance is for.

**It is already load-bearing elsewhere in this proposal**, and the four statements must be
read as one mechanism:

| Location | Statement |
|---|---|
| §12 | topology may declare *mechanically required distinctness* — a topological statement containing no dimension |
| §17.2 | the spatial/topology-closure category, at **PREMISE** independence — the placer did not author the premise |
| §22 R-3 | the requirement, its owner, and its failure signature |
| §23 item 2 | S04→S05 readiness requires every declared required-distinctness to be satisfied |

**No implementation algorithm is prescribed.** Whether distinctness is expressed as a
minimum separation, a non-coincidence predicate on axes, or a rank condition on the
realized topology is an implementation question; the architecture requires only that the
premise be declarable upstream and checkable downstream against a producer that did not
author it.
| make every unresolved item blocking | would halt on openness that is legitimately deferred; the condition must be defined, not maximised |

---

## §26 REMAINING ARCHITECTURE DECISIONS

### 26.1 The R-5 substrate — open alternatives

Recorded so that the choice is made on evidence rather than inherited from this document:

| Candidate | What it assumes | What would select it |
|---|---|---|
| **(a) declarative commitment classes** *(written out in §13, preferred)* | that recording a commitment's class and requiring a reason to supersede it is enough, because writers are cooperative | P4B Q4 resolves to *"the out-of-band write was an expedient, not a needed capability"* |
| **(b) structurally enforced patch-only mutation** | that no path may write stored state outside a validated patch, at the cost of every convenience path | P4B Q4 resolves to *"the direct write exists because the patch layer could not express the update"* — which would also indict `EXTEND`'s expressiveness |
| **(c) append-only state with commitments as derived views** | that no value is ever mutated at all; supersession is a new record and current-value is computed | if invalidation proves too costly to maintain incrementally |

**No option is chosen here.** (a) is written out because it is the least disruptive of the
three and because a candidate must be concrete to be attacked; that is not an argument that
it is correct.

1. **R-5 is PROVISIONAL, and so is migration unit M-4.** See §13.0 for the full statement of
   what is supported and what is a candidate. The open alternatives are recorded in §26.1.
2. **Repeated-member correspondence** rests on one case (C-16). The typed model in §12 is
   proposed as provisional; a second multi-instance case would settle whether it needs a
   dedicated relation or is a property of body identity.
3. **Where the independent assurance layer's external artifacts come from** — the audit found
   an independently authored artifact that is displayed and never evaluated against. Whether
   it becomes the external evaluator is P4B question 5.
4. **Whether evidence-route verdicts should be derived** from a principle family's declared
   claim dependencies rather than authored, given that the knowledge layer already contains
   the mapping and never uses it *(P4B question 8)*.
5. **How `PhysicalEffectObligation` interacts with candidate discrimination** — whether
   different principle families create materially different effect obligations, or whether the
   effects are candidate-independent and only their realisation differs.
6. **The granularity of the distinguishing basis** — per configuration pair, or per named
   state family. A design decision, not an evidence question.
7. **Whether `UNDISPOSITIONED` cells should block the gate**, or only be reported. §16.2's
   rule implies they block only if a consumer declares the disposition required; whether S04
   or S05 does is open.

---

## §27 SELF-FULFILLING-ASSURANCE AUDIT OF THIS PROPOSAL

The P6 failure shape — *producer creates X → evaluator confirms X has the exact shape the
producer always creates → "engineering validity"* — is applied to this architecture's own
assurance categories.

**The headline result, stated before the table because it changes how §18 must be read:**

> **Most checks this architecture introduces establish *fidelity* or *provenance
> integrity*, not engineering correctness.** A view can be sufficient and the reasoning
> still wrong. A disposition can have a resolvable premise and the premise still be
> mechanically false. A placement can be faithful to a topology that is itself wrong.

This is not a defect, but leaving it implicit **is** how the audited system reached
"engineering validity" from structural conformance. Therefore:

**New architectural rule — every check declares its claim class.**

| Claim class | What passing establishes |
|---|---|
| **BOOKKEEPING** | a property the producer guarantees by construction. Reported, never counted as assurance |
| **FIDELITY** | the artifact faithfully realizes a premise authored elsewhere. Says nothing about whether the premise is right |
| **PROVENANCE INTEGRITY** | every claim is traceable to a resolvable premise. Says nothing about whether the premise is true |
| **ENGINEERING CONSEQUENCE** | two independently authored premises are checked against each other, and a mechanically wrong design can fail. **Only this class may contribute to `ENGINEERING_ESTABLISHED`** |

### 27.1 Category-by-category

| Category | Producer creates | Assurance consumes | Guaranteed by producer? | Claim class | Could a wrong engineering claim still pass? |
|---|---|---|---|---|---|
| **Consumer sufficiency** | the view; contributory needs | the **output contract's dependency derivation** + the view | **No** — the required set derives from a contract the stage does not own (§7.2) | FIDELITY | **Yes.** A sufficient view does not make the reasoning right. Its value is *attributive*: it makes a later failure chargeable to the model rather than the boundary |
| **Mobility — domain totality** | deterministic enumeration | the same enumeration | **Yes, by construction** | **BOOKKEEPING** | n/a — must never be reported as assurance. This is the exact defect the audit found |
| **Mobility — disposition completeness** | authored relations; derived dispositions | dispositions + the relations they cite | **No** — completeness varies with what was authored | PROVENANCE INTEGRITY | **Yes.** A resolvable premise may still be mechanically false |
| **Mobility — cross-premise consistency** | S02 load cases / actuation; S03 dispositions | **both, from different producers** | **No** | **ENGINEERING CONSEQUENCE** | A DOF marked `IRRELEVANT` that a load case loads is a real contradiction. **This is where mobility assurance actually lives** |
| **ConstraintRelation integrity** | S03·B relations | relations + the bodies (S03·A) and external sites (S02) they reference | **No** — referents come from other stages | PROVENANCE INTEGRITY | **Yes.** A well-formed relation naming real entities can be wrong |
| **Constraint ↔ release consistency** | S03·B relations; S04·B transitions | **both** | **No** | **ENGINEERING CONSEQUENCE** | A transition that defeats a constraint without altering its maintaining interaction is a genuine contradiction |
| **Topology → spatial closure** | S03 topology; S04·B placement | **both** | **No** — the placer authored neither incidence nor required distinctness | **ENGINEERING CONSEQUENCE** (bounded) | **Yes, in one direction:** a *wrong topology*, faithfully realized, passes. The check establishes fidelity of realization, not correctness of topology |
| **Commitment / gating** | the gate | gate preconditions | **Yes, if the gate records its own verdict** | **would be BOOKKEEPING** | **Yes — and this is the live risk.** See 27.2 |
| **Status / establishment claims** | the assurance layer itself | its own outputs | **Yes, internally** | — | **Yes.** No structural means answers "does this metric measure engineering quality"; see 27.3 |

### 27.2 The gate is the one place this proposal was about to repeat the mistake

As drafted, §16.3 lets the selection gate check its own preconditions and record that they
were met. That is *producer creates X → evaluator confirms X* exactly.

**Correction, adopted:**

> **The gate may not author the verdict on its own preconditions.** Equal obligation
> coverage, equal maturity, and the absence of blocking unresolved items are all computable
> from committed state by a reader that is not the gate. The gate consumes that verdict; it
> does not produce it. A gate that fires without an externally computed precondition verdict
> is itself a `FALSE_ACCEPTANCE`.

### 27.3 The residual that cannot be closed structurally

Construct validity — *does an establishment claim measure engineering quality?* — is not
answerable from inside the system. R-15 makes a weaker, checkable claim: a maturity
construct must have a term for every stage it purports to cover. The stronger claim needs
**EXTERNAL** independence: an artifact authored without seeing any system output. The
repository contains such artifacts and does not evaluate against them; whether they become
the external evaluator is recorded as open in §26 item 3. **Until then, no aggregate in this
architecture should be described as measuring design quality.**

---

## §28 WITHDRAWN-CLAIM CHECK

Every claim the frozen audit withdrew or narrowed, checked against this document.

| Withdrawn claim | Present? | Where this document stands |
|---|---|---|
| TYPE-B persistence failure is architecturally impossible | **No** | §1 and §3 say the additive mechanism *worked in the audited corpus*; §5.3 constrains mutation prospectively without claiming the old design made loss impossible |
| All continuity failures are consumer-boundary failures | **No** | §1 item 2 says the *dominant recurrent* continuity failure is sufficiency; §1 items 3–6 and §6 carry capture, representation, reasoning, authorship, gating and assurance failures separately |
| DOF-grid size alone caused prompt truncation | **No** | §19 attributes the loss to the silent positional slice and to large derived content *competing* for a fixed budget; no single content class is named as the cause |
| BM fixtures are known human- or agent-authored | **No** | fixtures appear only in migration unit M-9, with no provenance claim. The corrected provenance is in `BENCHMARK_PROBE_EVALUATION_PHILOSOPHY.md` |
| The model always recognises the defect it commits | **No** | §1 item 4 is conditional — *"Where it names the defect the same artifact commits…"*. §7.2.2 signal 3 uses the recognition layer as a detector, explicitly not as a guarantee |
| Every spatial miss is a pure model failure | **No** | §1 item 2 and §7.2 hold that a stage's failure is not attributable until sufficiency is established; §24's ordering constraint states this as a migration precondition |
| State lacks the coordinates needed to detect collocated joints | **No** | §12 and §22 R-3 treat detection as available once the premise is declared and the arrangement is projected; the deficit is the premise and the projection, not the coordinates |
| Zero-length geometry can only be checked with mechanism-specific logic | **Corrected in this pass** | §25 previously rejected "a validator for zero-length links" without qualification, which contradicted §12, §17.2, §22 R-3 and §23. §25.1 now separates the case-specific patch and the over-general invariant (both rejected) from the conditional general invariant (retained and required) |

**One withdrawn claim had survived into the proposal.** It is corrected above.

---

## §29 ARCHITECTURE READINESS

**Verdict: (B) READY EXCEPT FOR THE EXPLICITLY PROVISIONAL R-5 SUBSTRATE.**

**Why not (C).** The load-bearing question was consumer-sufficiency declaration
completeness: if a stage can under-declare and then be proved sufficient against its own
understatement, the whitelist failure returns in a new form and nothing else matters. §7.2
closes it structurally rather than by convention — the required set is **derived** from the
semantic dependencies of the outputs the stage is permitted to create, the stage may widen
but never narrow it, and the sufficiency check must read the output contract rather than the
declaration alone. The regress terminates for a stated reason (§7.2.3): a per-field
dependency has a mechanical completeness test and a consumer need list has none. The
residual risk is real and is named — it is now located where it can be tested.

**Why not (A).** R-5 is PROVISIONAL in the frozen audit, and §13.0, §5.3, §16 and migration
unit M-4 all rest on it. The capability need is evidence-supported; the mechanism is a
preferred candidate among three (§26.1), and P4B question 4 selects between them. Building
M-4 before that question is answered would freeze a choice the evidence has not made.

**What this verdict does and does not license.**

| | |
|---|---|
| **Ready for implementation planning** | M-1 representation closure · M-2 sufficiency substrate · M-3 authorship boundary · M-6 assurance layer · M-7 status constructs · M-8 prompts and schemas *(after M-1)* · M-9 evidence substrate |
| **Not ready — hold for R-5 closure** | M-4 commitment substrate · M-5 gate, insofar as it depends on invalidation semantics |
| **Carried as provisional, not blocking** | repeated-member correspondence (§26 item 2, one-case evidence) |

**Three things must be true before an implementation plan is written**, and none is a code
task: P4B question 4 is answered (selects M-4); the claim-class rule of §27 is adopted, so
no structural check is counted as engineering assurance; and §27.2's correction holds — the
gate does not author the verdict on its own preconditions.

---

**END OF PROPOSAL.** Nothing here is implemented. No contract, prompt, validator, fixture or
runner is modified. The implementation plan is a separate document, to be written after
architecture review.
