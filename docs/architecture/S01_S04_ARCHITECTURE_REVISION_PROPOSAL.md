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

**P-1 — Sufficiency before economy.** A consumer view is first sized to *both* sources of
sufficiency — the representational dependencies of its outputs and the reasoning premises of
its decisions — and only then compressed. *(R-1, §7)*

**P-2 — Absence is never an assertion.** No deterministic path may convert "no evidence"
into a positive engineering claim. A domain may be total while the function over it is
explicitly partial. *(R-6)*

**P-3 — Anything the architecture calls a relation must have an identity.** If an entity
can be referred to, it must be resolvable. *(R-10)*

**P-4 — One semantic type per concept, agreed by producer, contract and consumer.** *(R-14)*

**P-5 — A commitment is a claim about the design, and claims bind.** A later stage may
refine or supersede with a stated reason; it may not silently contradict.
*(R-5 — the capability need is evidence-supported; the mechanism is **frozen by post-audit
design decision**, not by evidence. See §5.4, §5.6, §13.0.)*

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

### 5.3 Authority classes — what the mutation rules apply to

**FROZEN — DESIGN DECISION B.** Strict mutation semantics apply to authoritative engineering
state and **not** to every internal value. Four classes, and every value in the system
belongs to exactly one:

| Class | What it is | Mutation rule | Provenance |
|---|---|---|---|
| **A — AUTHORITATIVE ENGINEERING STATE** | facts the design *asserts*: requirements, physical obligations, load cases, reaction-site requirements, topology, physical interactions, constraint relations, mobility dispositions, spatial commitments, configurations and transitions, selection decisions, and unresolved items that gate commitment | **controlled mutation only** (§5.4) | **required** — method, premises, evidence reference |
| **B — DETERMINISTIC DERIVED STATE** | strict logical consequences of class-A premises: the enumerated DOF domain, graph indexes, derived adjacency, normalized lookups | **freely recomputable** from its premises | premise set required; **must not masquerade as independently authored engineering fact** |
| **C — EPHEMERAL / VIEW / CACHE STATE** | prompt serializations, consumer views, rendering caches, transient bounding computations, provider payload structures | **freely regenerated** | the view records what it was built from, for attribution |
| **D — ASSURANCE ARTIFACTS** | check results, findings, establishment claims *about* committed state | append-only | inputs and their maturity required |

**Two boundaries are load-bearing and must be visible enough for implementation review to
detect a violation:**

- **A vs B.** A derived value that is *stored as if authored* is the audited defect. A class-B
  value carries its premise set; if the premises are insufficient the value is not computed
  and the gap is reported (§5.5).
- **A vs D.** An assurance artifact must never become an input that makes the property it
  asserts true. Class D is a consumer of class A and never a producer of it.

### 5.4 Controlled mutation of authoritative state — normative invariant

> **Authoritative engineering state may change only through explicit, provenance-carrying
> mutation operations.**

The semantic operations, at minimum:

| Operation | Semantics |
|---|---|
| **CREATE** | the owning stage introduces an entity, once |
| **EXTEND** | a named stage adds a named field, once, never over an existing value |
| **SUPERSEDE** | a replacement value is recorded with a reason; **both values are retained**; dependents are affected per §5.6 |
| **INVALIDATE** | a value is marked no longer standing, with a reason; nothing is deleted; dependents are affected per §5.6 |

`RECORD` of unresolved items, rejections and evidence is a `CREATE` in the families that hold
them — additive, never overwriting.

**Exact implementation APIs may differ.** What is frozen is that the set is explicit,
closed, and provenance-carrying.

> **No stage, runner, projection helper, absorber, provider adapter or validator may directly
> mutate authoritative engineering facts outside this controlled path.**

This is a normative architectural invariant, not a style preference. It applies to helper
code and tooling exactly as it applies to stages — the audited direct write was in a runner,
not in a stage.

**Audit-status note.** `P4B_FINAL_SYNTHESIS.md` §21 classifies R-5 as **PROVISIONAL**, and
that classification stands unchanged: it describes what the *evidence* established. The rule
above is a **post-audit design decision**, motivated by that evidence and not presented as an
experimentally proven result. The distinction is preserved deliberately — see §13.0.

### 5.5 Derived-not-stored, restated

A value that is a projection of other state is computed on demand and carries its premise
set. This preserves the existing principle and extends it: **a derived value with an
incomplete premise set is not computed at all** — it is reported as underivable, naming the
missing premise. *(R-6, P-2.)*

### 5.6 Premise change must affect dependent commitment — normative invariant

> **If an authoritative premise used by a downstream commitment is superseded or invalidated,
> that dependent commitment may not silently remain authoritative.**

The architecture must *represent* the consequence. Concepts sufficient at this level:
`STALE` · `REOPEN_REQUIRED` · `INVALIDATED`. **The final status vocabulary is an
implementation decision and is deliberately not over-designed here.** The invariant is:

> **changed premise → the affected dependent commitment loses unqualified authority.**

Applies to every dependency of this class, stated as classes:

| Dependent commitment | Premise whose change affects it |
|---|---|
| a candidate selection | the feasibility evidence it was decided on |
| an S04·B refinement | the S04·A spatial commitment it extends |
| a mobility conclusion | the constraint relation it cites |
| a support or load-closure conclusion | the reaction-site premise it terminates at |
| any derived value | any class-A premise in its premise set |

**What the architecture does not fix here:** how propagation is computed — eagerly on write,
lazily on read, or by recomputing a dependency closure. That is an implementation choice.
What is fixed is that a dependent commitment cannot remain unqualifiedly authoritative after
its premise changes.

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

**FROZEN — DESIGN DECISION A.** This section supersedes every earlier formulation in this
document. Where any other section still reads as though a stage declares its own needs, this
section governs.

### 7.1 Consumer sufficiency has two independent sources

A consumer view is sufficient only if it satisfies **two separate questions that do not
imply one another**. Collapsing them into a single checklist is the error this design exists
to prevent.

| | **A — REPRESENTATIONAL SUFFICIENCY** | **B — REASONING SUFFICIENCY** |
|---|---|---|
| **Question** | *Can the consumer's outputs be represented with complete and traceable meaning?* | *Has the consumer received the engineering premises required by the decisions it is responsible for making?* |
| **Derived from** | the **output / entity semantic contract** | the **stage responsibility contract** |
| **Chain** | output field → its declared referent | responsibility → engineering question → required premise class |
| **Nature of a violation** | an output whose meaning is undefined or untraceable | an output whose meaning is perfectly defined and whose engineering basis is absent |
| **Example of the class** | a spatial value without its reference frame; a relation without addressable subject and object; a load-path segment without defined endpoints; a mobility statement without a defined DOF domain; a constraint statement without the entity and interaction it constrains | topology synthesis without the relevant load cases; support reasoning without reaction-site requirements; retention topology without disturbance/retention obligations; spatial realization without the relevant quantities and mobility expectations; refinement without the prior spatial commitments |

**Why both are required.** A stage can produce output that is fully well-formed and fully
traceable, and still be reasoning without the premises its assigned decision needs. That
output passes every representational test. **Source B is the one that catches it**, and it
cannot be derived from output field referents, because the premise is not something the
output points at — it is something the decision depended on.

### 7.2 The final sufficiency rule

> **Required Consumer View = Representational Dependencies ∪ Engineering Reasoning Premises
> ∪ explicitly justified contributory context.**

**A stage may request additional contributory information. A stage may never narrow the
required minimum.** A declaration below the architecture-derived minimum is a contract
violation, not a preference. A stage does not decide, silently or otherwise, that a required
premise is unnecessary.

### 7.3 The derivation chain, and where independence lies

```
Stage Responsibility Contract
        │
        ├── derives Engineering Questions
        │              │
        │              └── derives Required Reasoning Premise Classes ──┐
        │                                                              │
Output / Entity Semantic Contract                                      │
        │                                                              │
        └── derives Required Representational Dependencies ────────────┤
                                                                       ▼
                                            Required Minimum Consumer Semantics
                                                                       │
                                          (+ stage-authored CONTRIBUTORY context,
                                             which may only widen)
                                                                       ▼
                                              Consumer View Construction
                                                                       ▼
                                            Independent Sufficiency Assessment
```

**Three properties of this chain are normative:**

1. **The generated view does not define its own completeness criterion.** The criterion comes
   from two contracts upstream of the view and upstream of the stage.
2. **The consuming stage authors neither branch of the minimum.** It may author contributory
   needs only, and those can only widen.
3. **The sufficiency assessment reads the contracts, not merely the view.** An assessment
   whose only inputs are a declaration and a view is structurally incapable of detecting an
   omitted requirement, and is prohibited.

**What this forecloses:** *stage says it needs X → view contains X → checker declares
SUFFICIENT.* At no point does a stage's own statement of need enter the minimum.

### 7.4 The residual limitation, stated plainly

**This architecture does not prove that the stage responsibility contracts and entity
semantic contracts contain all mechanical knowledge that competent reasoning requires.**
They are human-authored, and a premise class nobody thought of will not appear in either.

**No claim of mathematical completeness of engineering reasoning is made here, and none
should be read into this document.**

The architectural objective is narrower and achievable:

> **A missing dependency becomes an explicit contract defect — locally attributable, at a
> named contract, in a named field or premise class — rather than silent context loss at a
> projection boundary.**

That is the whole of the improvement, and it is enough: the audited failure was not that
someone chose the wrong families, but that nothing anywhere was obliged to state the
relationship at all.

Two detectors supplement the derivation, and are detectors only, never the guarantee:

- **contradiction against accumulated state** — a stage produces a value contradicting an
  authoritative value that exists in state and was absent from its view;
- **the producer's own unresolved layer as a sufficiency sensor** — a stage recording an
  unresolved item that names a fact class already present in accumulated state is reporting
  an omitted premise in its own words.

### 7.5 Two failures, never conflated

| Finding | Meaning | Attributable to |
|---|---|---|
| **UPSTREAM INSUFFICIENCY** | a required fact class has no instance in accumulated state | the producing stage, or a genuine gap in the problem |
| **PROJECTION FAILURE** | instances exist in accumulated state and the view does not carry them | the view construction / the boundary |

These are different defects with different owners. The audit spent substantial effort
separating them after the fact; the architecture separates them at the point of failure.

### 7.6 Budget overflow is a status, never a slice

A semantically sufficient view that exceeds the budget is reduced by **semantic** means —
reference-by-id with expansion on demand, role-level summarisation of homogeneous
collections, omission of contributory (never required) classes — and **what was reduced, and
by which rule, is recorded**. Positional truncation is not a compression strategy; it is
undetected information loss.

A view that cannot be made sufficient within budget is a recorded condition
(`CONTEXT_INSUFFICIENT` / `BUDGET_INSUFFICIENT`), not a silently truncated prompt.

### 7.7 What would make consumer sufficiency self-fulfilling

Prohibitions, stated so a reviewer can test for them:

- deriving the minimum from the view that was sent, or from what the stage happened to use;
- letting the consuming stage author any part of the required minimum;
- an assessment whose only inputs are the declaration and the view;
- defining "sufficient" as *"every declared class was present"*, with no term referring to
  responsibility or to output semantics;
- silently demoting an unmet required class to contributory so a call can proceed;
- treating a stage's successful execution as evidence that its view was sufficient.

**Operative definition:**

> **Consumer-view completeness ≠ "all facts listed in the declaration happened to be
> present."** It is: *every representational dependency of the outputs the stage may create,
> and every reasoning premise class its assigned decisions require, is present in the view at
> sufficient maturity — and any that is not is recorded as an attributable insufficiency.*

### 7.8 Per-stage semantic responsibility matrix

Architecture-level. **This is not a prompt specification**, and the premise classes are
stated as classes, never as instances.

---

**S01 — problem interpretation**

| | |
|---|---|
| **Responsibility** | convert a request into typed statements of what is required, what is free, what is ambiguous, and what lies outside the product |
| **Engineering questions** | what does the source oblige? what does it leave open? what is genuinely undetermined? who acts, and what must be reached? where is the system boundary in each scenario? |
| **Representational dependencies** | the source itself, with locators; a scenario identity for every boundary-bearing statement |
| **Reasoning premises** | none upstream — S01 is the only stage that reads raw source |
| **Contributory** | prior recorded ambiguity vocabulary |
| **Output semantics** | atomic requirements; ambiguities with what would resolve them; scenarios carrying an explicit system boundary; candidate external sites |
| **Upstream insufficiency** | source unavailable or unlocatable |
| **Projection failure** | a source proposition present in the input and absent from the view |

---

**S02 — physical obligation, demand and principle**

| | |
|---|---|
| **Responsibility** | establish what must physically be true, what the world does, and which principle families could serve |
| **Engineering questions** | what must hold regardless of mechanism? what physical effects must occur between which roles? what loads act and where may each be reacted? which principle families could serve, and which of their claims can be evidenced? |
| **Representational dependencies** | requirement identities; scenario identities; role identities; the quantity types obligations will cite |
| **Reasoning premises** | **the full requirement set** (an obligation set derived from part of it is unsound); **ambiguities** (an obligation resting on a silently resolved ambiguity is an unrecorded commitment); **scenario boundaries** (a reaction-site requirement cannot be typed external without one); **actors and reach intent** |
| **Contributory** | principle-family knowledge with declared claim dependencies |
| **Output semantics** | obligations with premises and evidence route; candidate-independent load cases; physical-effect obligations; reaction-site requirements; candidates with principle assignment |
| **Upstream insufficiency** | requirements not atomized; no scenario carries a boundary |
| **Projection failure** | requirements or ambiguities exist and the view omits them |

---

**S03·A — mechanism topology**

| | |
|---|---|
| **Responsibility** | state what things exist, what each does, and how they connect — with no magnitude, position or axis placement |
| **Engineering questions** | what bodies and rigid groups exist? what joins what, of what type, leaving which DOF? what configurations exist and what distinguishes them? which sites must be distinct for a mechanical relationship to exist? |
| **Representational dependencies** | obligation identities (for `addresses_obligations`); candidate identity; role identities that bodies realize; the DOF domain definition |
| **Reasoning premises** | **physical-effect obligations** (a topology synthesised without knowing what must be transmitted is invented, not derived); **load cases** (they determine which connections must carry force); **reaction-site requirements**; **the candidate's principle assignment with its claim dependencies**; **quantity classes that constrain topology** (counts, ranges, travel) |
| **Contributory** | prior rejected topologies with reasons |
| **Output semantics** | bodies, rigid groups, joints, interfaces, configurations with distinguishing bases, functional regions, required-distinctness declarations |
| **Upstream insufficiency** | no physical-effect obligation exists for a required function |
| **Projection failure** | load cases or effect obligations exist and the view omits them |

---

**S03·B — interaction and constraint**

| | |
|---|---|
| **Responsibility** | state what physically transmits each required effect, what constrains what, and how load reaches the world |
| **Engineering questions** | what realizes each required effect? what holds each body where it is put, against what, in which configurations, and how would a test defeat it? how does each load reach an external site? in what order does it assemble, and what retains each part? |
| **Representational dependencies** | body and rigid-group identities; interface and feature identities; configuration identities; reaction-site identities; effect-obligation identities |
| **Reasoning premises** | **the full S03·A topology**; **load cases and their reaction-site requirements**; **physical-effect obligations** (to discharge); **disturbance / retention obligations**; **configuration distinguishing bases** (a constraint's configuration set is meaningless without them) |
| **Contributory** | assembly-order constraints from obligations |
| **Output semantics** | physical interactions with discharge references; addressable constraint relations; load paths; assembly steps |
| **Upstream insufficiency** | a load case names no reaction-site requirement |
| **Projection failure** | retention obligations exist and the view omits them |

---

**S04·A — coarse spatial realization and comparability**

| | |
|---|---|
| **Responsibility** | give each retained candidate a provisional arrangement sufficient to decide fit, reach and assemblability, and to make candidates comparable |
| **Engineering questions** | can this candidate fit at all? can each actor reach what it must? can it be assembled? on what geometric ground would it be eliminated? |
| **Representational dependencies** | body and rigid-group identities; **one declared reference frame**; region identities; assembly-step identities |
| **Reasoning premises** | **the full topology and interactions**; **quantities of the classes that bound extent, travel and clearance**; **reach targets and actor requirements**; **envelope and region constraints**; **assembly-order constraints** |
| **Contributory** | comparable arrangements of sibling candidates |
| **Output semantics** | extents and centres in one frame, at commitment class `PROVISIONAL` / `COMPARABLE`; reach results; elimination records with geometric reasons |
| **Upstream insufficiency** | no quantity of a class the extent depends on exists anywhere in state |
| **Projection failure** | such a quantity exists and the view omits it — **the audited failure** |

---

**Selection gate**

| | |
|---|---|
| **Responsibility** | commit to one candidate, or record that the candidates remain indistinguishable |
| **Engineering questions** | do all retained candidates carry evidence at equal obligation coverage and equal maturity? does any unresolved item block selection? on what recorded ground does one win? |
| **Representational dependencies** | candidate identities; obligation coverage per candidate; maturity per value |
| **Reasoning premises** | **every candidate's S04·A evidence**; **every candidate's evidence-route verdict**; **all unresolved items and their blocking scope** |
| **Contributory** | — |
| **Output semantics** | a selection decision with recorded ground, or an unresolved decision; never a tie broken silently |
| **Upstream insufficiency** | candidates carry unequal coverage — this **is** the finding, not an error |
| **Projection failure** | an unresolved item that blocks selection exists and the gate's inputs omit it |

---

**S04·B — committed spatial and kinematic realization**

| | |
|---|---|
| **Responsibility** | place the selected mechanism and describe its motion so that clearance, incidence and distinctness can be computed |
| **Engineering questions** | where is each joint, in which frame, and on which axis? what coordinate values realize each configuration? which coordinates change in each transition, and along what path? |
| **Representational dependencies** | joint and body identities; joint incidence; **the reference frame of the arrangement being extended**; configuration and transition identities |
| **Reasoning premises** | **the selected candidate's S04·A arrangement and its commitment classes** — *the single most consequential premise, and the one the audited system omitted*; **the full topology including axes and link relationships**; **required-distinctness declarations**; **configuration distinguishing bases**; **constraint relations and the interactions maintaining them**; **quantities bounding travel and clearance**; **the selection decision itself** |
| **Contributory** | superseded S04·A alternatives with reasons |
| **Output semantics** | joint frames (origin **and** axis); configuration coordinates; transitions with changing coordinates and a declared motion evidence level; refinements or explicit supersessions of S04·A values |
| **Upstream insufficiency** | no arrangement exists for the selected candidate |
| **Projection failure** | the arrangement exists in state and the view omits it — **the audited failure, in six of six cases** |

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

### 13.0 Status of this section — FROZEN BY DESIGN DECISION B

**Two statuses, deliberately kept distinct, and neither is allowed to overwrite the other:**

| | Statement |
|---|---|
| **AUDIT EVIDENCE STATUS** | `P4B_FINAL_SYNTHESIS.md` §21 classifies **R-5 as PROVISIONAL**. That classification is historically accurate, stands unchanged, and is **not** revised by anything in this document. It records that the evidence for the binding-commitment requirement was contract-level plus a single case, and that P4B question 4 remained open. |
| **ARCHITECTURE DESIGN CHOICE** | After audit review, the architecture **adopts controlled authoritative mutation (§5.4) and dependent-commitment invalidation (§5.6) as normative principles.** This is a design decision motivated by the audit. It is **not** presented as an experimentally proven result, and adopting it does not make R-5 evidentially stronger than it was. |

> **AUDIT EVIDENCE STATUS ≠ ARCHITECTURE DESIGN CHOICE.** A design may rationally commit
> where evidence is incomplete. What it may not do is relabel the evidence.

**What follows from the decision.** The commitment/refinement mechanism below is **frozen as
architecture**, not held open pending P4B question 4. The question remains scientifically
interesting — it is retained in §26 as an unresolved *evidence* question — but it no longer
gates the architecture, because the decision has been made on design grounds: the
alternative, allowing arbitrary direct authoritative writes with auditing after the fact,
is **rejected** (§20.6).

**What remains genuinely open is implementation-level, not architectural:** how dependency
propagation is computed, what the final status vocabulary is, and whether commitment classes
are stored per value or derived from a dependency graph. Those are implementation decisions
and are recorded as such in the implementation plan, not as architecture uncertainty.

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
| **representational sufficiency** | the **output/entity semantic contract** + the view actually sent | contract; view builder records the view | the required set is taken from the view or from the stage | STRUCTURAL |
| **reasoning sufficiency** | the **stage responsibility contract** → engineering questions → required premise classes, + the view actually sent | contract; view builder | the premise classes are authored by the consuming stage | STRUCTURAL |
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

| | **A: family whitelist** *(audited)* | **B: whole state** | **C: stage-declared needs** | **D: architecture-derived two-source minimum** *(SELECTED, §7)* |
|---|---|---|---|---|
| who sets the minimum | a hand-maintained list | nobody | **the consuming stage** | **two contracts upstream of the stage** |
| requirement coverage | fails R-1, R-2 | satisfies R-1 | satisfies R-1 only if the stage declares correctly | satisfies R-1, R-2 |
| can a consumer under-ask? | n/a | n/a | **yes — silently** | **no** — it may widen only |
| catches a missing *reasoning premise*? | no | incidentally | only if declared | **yes — derived from responsibility** |
| token cost | low | very high, grows with state | bounded | bounded by the derived minimum |
| observability | cannot detect a missing class | cannot attribute a miss | cannot detect an under-declaration | omission surfaces as a **contract defect** |
| complexity | trivial | trivial | moderate | moderate — two contracts must be authored |

**Selected: D.** **C is rejected** — it is the whitelist failure one level up, and was an
earlier formulation in this document. **B is rejected** — cognitive load grows with
accumulated state, and it still cannot distinguish *absent upstream* from *not projected*.

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

### 20.6 Authority and mutation — the HYBRID AUTHORITY MODEL

| | **A: uniform strict mutation for all state** | **B: arbitrary direct writes + audit after the fact** *(effectively the audited system)* | **C: HYBRID AUTHORITY MODEL** *(SELECTED, §5.3–§5.6)* |
|---|---|---|---|
| authoritative engineering state | controlled | uncontrolled | **controlled mutation only** |
| deterministic derived state | controlled — over-heavy, and forces derived values to look authored | uncontrolled | **freely recomputable from its premises** |
| ephemeral / view / cache | controlled — pure ceremony | uncontrolled | **freely regenerated** |
| assurance artifacts | mixed with the state they judge | mixed | **separate consumers of committed state** |
| detectability of an illegal write | high, at high cost | **none** | high, and only where it matters |
| premise-change propagation | possible | not representable | **required (§5.6)** |

**Selected: C.**

**B is rejected and is no longer an open alternative.** "Allow arbitrary direct authoritative
writes and audit later" is not an equally viable architecture: the audited system had exactly
one such path, it wrote spatial commitments — class-A facts — with no provenance, no
ownership check and no validation, and nothing in the system could have detected it. Auditing
after the fact is what this review *was*; it is not a control.

**A is rejected** because applying strict semantics to caches and prompt payloads buys
nothing and, worse, blurs the A/B boundary that §5.3 exists to keep sharp.

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
| R-5 *(audit status **PROVISIONAL**; mechanism **frozen by design decision** — §13.0)* | C-19 | commitment classes + supersede-with-reason + invalidation cone (§13, §5.3) | shared substrate | any stage | assurance, gate | deterministic | progression validity | superseding a gate premise marks selection STALE | a changed COMPARABLE value with no supersede record |
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
| **M-4 Commitment substrate** *(**FROZEN** by Decision B — §13.0)* | extends the patch layer | authority classes; the four controlled operations; premise-change propagation; elimination of out-of-band authoritative writes |
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

### 26.1 The R-5 substrate — CLOSED BY DESIGN DECISION B

Previously recorded here as three open alternatives. **The choice has been made on design
grounds** (§5.4, §5.6, §13.0):

| Candidate | Disposition |
|---|---|
| declarative commitment classes with controlled mutation | **SELECTED** — the hybrid authority model of §20.6 |
| structurally enforced patch-only mutation for *all* state | **rejected** — over-applies strict semantics to derived and ephemeral values, which §5.3 separates for good reason |
| append-only state with commitments as derived views | **not selected**, and not foreclosed as an *implementation* of the frozen semantics — it satisfies §5.4 and §5.6 and remains an implementation option |
| arbitrary direct authoritative writes plus auditing after the fact | **rejected outright** — no longer a viable architecture alternative (§20.6) |

**P4B question 4 is retained below as an unresolved evidence question.** It no longer gates
the architecture.

1. **P4B question 4 remains scientifically unresolved** — why an unguarded direct write
   existed alongside a defined, validated, never-exercised `EXTEND`. R-5's audit status
   remains PROVISIONAL. **Neither gates the architecture**, which has committed by design
   decision (§13.0). The answer would inform implementation, not architecture.
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
| **Representational sufficiency** | the view | the **output/entity semantic contract** + the view | **No** — the required set derives from a contract the stage does not own (§7.3) | FIDELITY | **Yes.** A well-formed view does not make the reasoning right |
| **Reasoning sufficiency** | the view; contributory needs | the **stage responsibility contract** → premise classes, + the view | **No** — premise classes derive from responsibility, which the stage does not author | FIDELITY | **Yes.** A sufficient view does not make the reasoning right. Its value is *attributive*: it makes a later failure chargeable to the model rather than the boundary |
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
| The model always recognises the defect it commits | **No** | §1 item 4 is conditional — *"Where it names the defect the same artifact commits…"*. §7.4 uses the recognition layer as a *detector*, explicitly not as a guarantee |
| Every spatial miss is a pure model failure | **No** | §1 item 2 and §7.5 hold that a stage's failure is not attributable until sufficiency is established; §24's ordering constraint states this as a migration precondition |
| State lacks the coordinates needed to detect collocated joints | **No** | §12 and §22 R-3 treat detection as available once the premise is declared and the arrangement is projected; the deficit is the premise and the projection, not the coordinates |
| Zero-length geometry can only be checked with mechanism-specific logic | **Corrected in this pass** | §25 previously rejected "a validator for zero-length links" without qualification, which contradicted §12, §17.2, §22 R-3 and §23. §25.1 now separates the case-specific patch and the over-general invariant (both rejected) from the conditional general invariant (retained and required) |

**One withdrawn claim had survived into the proposal.** It is corrected above.

---

## §29 FINAL ARCHITECTURE CONSISTENCY CHECK AND FREEZE

After Decisions A (§7) and B (§5.3–§5.6, §20.6), the architecture is checked for **one
coherent answer** to each of fifteen questions.

| # | Question | Single answer | Where |
|---|---|---|---|
| 1 | What persists? | everything; nothing is deleted; supersession retains both values | §5.2, §5.4 |
| 2 | What is authoritative? | class A only — the facts the design asserts | §5.3 |
| 3 | What may be derived? | class B — strict consequences of class-A premises, recomputable, never stored as authored | §5.3, §5.5 |
| 4 | What is ephemeral? | class C — views, serializations, caches, provider payloads | §5.3 |
| 5 | What can a stage change? | only what its ownership and field-mutability declaration permit; never another family's authoritative facts | §5.2, §6 |
| 6 | How may authoritative facts be changed? | CREATE · EXTEND · SUPERSEDE · INVALIDATE, with provenance; **no other path**, including runners and helpers | §5.4 |
| 7 | What happens when a premise changes? | the dependent commitment loses unqualified authority; the consequence is represented | §5.6 |
| 8 | What does each stage need to know? | representational dependencies ∪ reasoning premises ∪ justified contributory context | §7.2, §7.8 |
| 9 | How are those inputs determined? | derived from the output/entity semantic contract and the stage responsibility contract — never by the consuming stage | §7.3 |
| 10 | Projection failure vs upstream insufficiency? | instances exist in state and the view omits them, vs no instance exists in state — different findings, different owners | §7.5 |
| 11 | What is LLM engineering authorship? | what must be true and why; what exists and what each thing does; what transmits what; what constrains what; what remains open | §11, §19 |
| 12 | What is deterministic bookkeeping? | domain enumeration, id maintenance, reference integrity, strict consequence from sufficient typed premises, dependency propagation | §11, §19 |
| 13 | What does unresolved evidence do? | it blocks exactly when it names a fact class the next consumer's or gate's minimum marks required; otherwise it is carried | §16.2 |
| 14 | What does assurance establish? | one of four declared claim classes; most checks establish fidelity or provenance integrity, not correctness | §27 |
| 15 | What does `ENGINEERING_ESTABLISHED` mean? | an ENGINEERING-CONSEQUENCE check, of declared independence, with inputs at or above its minimum maturity, found the property to hold. Never inherited | §17.0, §18, §27 |

**No question has two answers, and no two sections give incompatible definitions of consumer
sufficiency or of authority.**

### 29.1 Freeze

> **The S01–S04 architecture is FROZEN FOR IMPLEMENTATION PLANNING.**

**This freeze means:** the architecture concepts are fixed enough that an implementation can
be planned without rediscovering them.

**This freeze does not mean:** that field names are final, that any API is final, that any
validator is designed, or that any prompt is written. It also does not mean that any
scientific question the audit left open has been answered.

The short normative statement of the frozen architecture is
`S01_S04_ARCHITECTURE_FREEZE.md`. **This document remains the rationale**, and where the two
disagree on a normative rule, the freeze record governs.

### 29.2 What is frozen, and on what grounds

| | Grounds |
|---|---|
| two-source consumer sufficiency (§7) | audit evidence (C-05, C-12, R-1, R-2) **plus** design decision A on the two-source structure |
| authority classes and controlled mutation (§5.3–§5.4) | **design decision B**, motivated by audit evidence; R-5's audit status is unchanged and remains PROVISIONAL |
| premise-change propagation (§5.6) | design decision B |
| mobility domain/disposition split, `UNDISPOSITIONED` (§11) | audit evidence (C-11, C-18, R-6) |
| physical-effect → interaction progression, constraint relations, reaction sites (§9, §10) | audit evidence (C-07, C-08, C-10, R-10–R-12) |
| topology→spatial continuity and S04·A→S04·B refinement (§12, §13) | audit evidence (C-12–C-15, R-2, R-3) |
| assurance independence, claim classes, four status constructs (§17, §18, §27) | audit evidence (C-21, C-22, R-7, R-9, R-15) |

---

**END OF PROPOSAL.** Nothing here is implemented. No contract, prompt, validator, fixture or
runner is modified. The implementation plan is a separate document, to be written after
architecture review.
