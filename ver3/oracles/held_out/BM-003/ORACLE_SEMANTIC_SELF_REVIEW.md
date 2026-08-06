# BM-003 Oracle — semantic self-review

Reviewing the held-out Oracle as a **mechanical acceptance specification**: would
it accept the designs it claims to accept, and reject the ones it claims to
reject?

Baseline commit `d2fd24952f5e79618cd63cef1de242538023ccd8`. Source hash
`ffb7f5f9feb8e38d6ee56dbce91529f817aebbd2f7180d7dedce65da0c94929d` verified
before review.

**The headline result is bad, and it is bad in an instructive way.** The auditor
reported PASS on 16 checks and the pack is internally self-consistent by every
structural measure. It is also, on its own terms, unable to accept three of the
five realization families it declares admissible. The structural checks could not
see this because the admissibility fixture is circular: a family "satisfies" an
invariant when its author typed the invariant's tag into the family's tag list.
Nothing checked whether the physics agreed.

---

## Part 1 — Independent findings

### F-01 · BLOCKING · deployed persistence equated with kinematic DOF absence

| | |
|---|---|
| Files | `normative.yaml` NRM-BM-003-009, NRM-BM-003-010; `assembly_and_mobility_expectations.yaml` MOB-BM-003-002 |
| Source clause | SRC-BM003-008 *"Once it is open, it needs to stay open on its own."* |
| Current reading | *"the folding motion is unavailable while the product is in the deployed state"*, predicated as *"the folding degree of freedom of each leg is shown blocked"* |

**Counterexample.** An over-centre leg linkage deployed just past its singularity
has a perfectly good folding kinematic path — the leg *can* rotate back, and the
mechanism's own geometry opposes it energetically. The DOF exists. A gravity-
seated strut has a folding path the moment you lift the strut out of its pocket.
A friction interface has a folding path at any applied torque above breakaway. A
compliant engagement has a folding path once the compliant member deflects.

**Effect: FALSE REJECTION of three declared-admissible families** —
ADM-BM-003-001 (over-centre), ADM-BM-003-003 (compliant), ADM-BM-003-004
(gravity-seated). Only ADM-BM-003-002 (captive collar) and ADM-BM-003-005
(rotating sleeve) are hard kinematic blocks.

The source does not say the folding motion cannot exist. It says the stand
**stays open on its own** — a statement about what happens under ordinary
operation, not about the configuration space.

**Correction.** Replace the DOF-absence predicate with a realization-neutral
persistence requirement plus a declared state-maintenance class. Persistence
means: does not enter folding under ordinary declared operation before deliberate
release. Whether a kinematic path exists is a property of the class, not a
requirement.

**Auditor should have caught it?** Yes — and this is the interesting part. It
could not, because the only permissiveness check compares self-assigned tags.
See F-11.

---

### F-02 · BLOCKING · a persistent RELEASED configuration is forced

| | |
|---|---|
| Files | `normative.yaml` NRM-BM-003-011; `configurations.yaml` CFG-BM-003-RELEASED, TRN-BM-003-RELEASE |
| Source clause | SRC-BM003-011 *"Before it can be folded again I want to have to do something deliberate"* |
| Current reading | *"A **distinct RELEASED configuration** exists, reachable from DEPLOYED only by a declared user action"* |

**Counterexample.** A squeeze-and-fold grip: the user squeezes two tabs and, in
the same continuous motion, folds the leg. There is no stable pose in which the
product sits released-but-deployed. The release is a **transition guard**, not a
configuration. Equally: a lift-and-swing strut where lifting past a threshold and
swinging are one action.

**Effect: FALSE REJECTION** of every realization whose release is transient or
combined with folding initiation.

The source requires a deliberate *action*. It says nothing about a stable
intermediate *state*.

**Correction.** Admit persistent configuration, transient configuration,
transition event, transition guard, and combined release-and-fold as equivalent
representations. Require only that folding not begin without the deliberate
action.

---

### F-03 · BLOCKING · "exactly one changed relationship"

| | |
|---|---|
| File | `configurations.yaml` CFG-BM-003-RELEASED |
| Current text | *"RELEASED must differ from DEPLOYED in **exactly one respect**"*; *"The state-maintaining relationship is disengaged - and **ONLY that one**"* |

**Counterexample.** Three independent legs, each with its own retaining
relationship, released by a deliberate two-handed action that disengages all
three. Three relationships change. The design is coherent and the source permits
it — FRE-BM-003-004 explicitly frees central-versus-distributed coordination.

**Effect: FALSE REJECTION**, and it directly contradicts a declared freedom.

**Correction.** Delete the exactness rule. Require that the deliberate action
changes the system so folding can proceed, and that retention remains coherent.

---

### F-04 · BLOCKING · bilateral interface rule excludes monolithic compliant realization

| | |
|---|---|
| File | `normative.yaml` NRM-BM-003-016 |
| Current text | *"realized by identifiable geometry on **each participating body**"*; predicate *"**both participating bodies** expose the feature"* |
| Freedom contradicted | FRE-BM-003-002 admits *compliant flexure* as a joint type |

**Counterexample.** A leg joined to the body by a living hinge, moulded as one
piece. There is one body. "Both participating bodies" has no referent, so the
verification minimum cannot be satisfied by a design the freedoms explicitly
admit.

**Effect: FALSE REJECTION.**

**Correction.** Generalize to *participating bodies **or functional regions***,
with the realization class declared. A compliant realization identifies its
compliant region, the adjacent functional regions, and the intended deformation
mode.

---

### F-05 · MAJOR · assembly endpoint freedom absent from the graph

| | |
|---|---|
| Files | `configurations.yaml` TRN-BM-003-ASSEMBLE; `freedoms.yaml` FRE-BM-003-013 |
| Current state | Edge fixed `UNASSEMBLED → STORED`, with a prose note that DEPLOYED is equally acceptable |

A checker walks the graph, not the note. **Effect: FALSE REJECTION** of a product
assembled in its deployed state.

**Correction.** Type the edge as `to_any_of: [STORED, DEPLOYED]`, conditional on
the completed product traversing the operational cycle.

---

### F-06 · MAJOR · compact storage has no normative predicate

| | |
|---|---|
| Files | `normative.yaml` (absent); `negative_cases.yaml` NEG-BM-003-016; `stage_expectations.yaml` s07 |
| Source clauses | SRC-BM003-001, SRC-BM003-002 |

NEG-BM-003-016 rejects "stored compactness asserted, not shown" and points at
NRM-BM-003-001 — which says only that each leg *has a stored position close to
the body*. Nothing anywhere requires STORED to be **more compact than DEPLOYED**.

Confirmed mechanically: SRC-BM003-001 is cited by **no invariant at all** (see
F-07). The source's first sentence has no normative consequence.

**Effect: FALSE ACCEPTANCE.** A design whose folded envelope equals or exceeds its
deployed envelope passes every invariant.

**Correction.** Add a relational invariant: at least one storage-relevant extent
is smaller in STORED than in DEPLOYED. No ratio, no absolute size, no requirement
that every dimension shrink.

---

### F-07 · MAJOR · clause↔invariant mapping is not reciprocal

Computed over the pack: **5 of 15 clauses disagree** with the invariants citing
them.

| Clause | Claims to support | Actually cited by | Direction of error |
|---|---|---|---|
| SRC-BM003-001 | NRM-001 | *nothing* | claim is aspirational — F-06 |
| SRC-BM003-002 | NRM-001, -002, -003 | NRM-001 | over-claimed |
| SRC-BM003-005 | NRM-004, -005 | NRM-004, **-017** | both directions wrong |
| SRC-BM003-007 | NRM-005, -008, -014 | NRM-005, -008, **-017** | both directions wrong |
| SRC-BM003-012 | NRM-012 | NRM-012, **-017** | under-claimed |

**Effect: OVERCLAIM of traceability.** The ledger asserts coverage the invariants
do not provide, and the auditor's `CLAUSE_NEVER_USED` check passes because it
scans free text for `SRC-` tokens anywhere — including inside the ledger's own
`supports_invariants` lists. A clause could cite itself into apparent coverage.

**Correction.** Enforce exact set equality both ways, and fix each direction on
its merits rather than by deleting whichever side is inconvenient.

---

### F-08 · MAJOR · `authored_independently: true` overstates the facts

`descriptor.yaml` sets `oracle.authored_independently: true`.
`GOVERNANCE.yaml` `prior_context_disclosure` states the same agent authored the
BM-003 source and this Oracle in the same working session.

Both cannot be true. **Effect: OVERCLAIM**, and it is the claim most likely to be
relied on by someone deciding whether a benchmark result is trustworthy.

**Correction.** Replace the boolean with typed fields distinguishing four
different things that "independent" currently conflates: isolation from
production generation, temporal separation of tasks, author independence, and
human review status.

---

### F-09 · MAJOR · unresolved items vanish mid-pipeline

`stage_expectations.yaml` `must_leave_unresolved` per stage:
s01 all ten · s02 two · s03 two · s04 two · s05 two · s06 two · **s07 empty** ·
s08 two · s09 one · s10 one · s11 four · s12 all ten.

DesignState is cumulative and does not delete. An item unresolved at s01 and
absent at s07 reads as resolved at s07 — and its reappearance at s12 is then
unexplained.

**Effect: FALSE ACCEPTANCE** of silent resolution between s05 and s07.

**Correction.** Split into `must_preserve_unresolved` (cumulative, all items) and
`stage_relevant_unresolved` (the subset this stage actively touches).

---

### F-10 · MAJOR · S05 forbidden from embodying the selected candidate

`stage_expectations.yaml` s05 `must_not_decide`: *"Which mechanism family is
correct."*

Candidate selection happens after s03/s04 produce comparable evidence. S05's job
is to embody the selected candidate. As written, the stage that must realize the
mechanism is forbidden from committing to one.

**Effect: FALSE REJECTION** of correct pipeline behaviour.

**Correction.** S05 must embody the *selected* candidate and must not substitute
an Oracle-preferred family. The prohibition belongs on substitution, not on
embodiment.

---

### F-11 · BLOCKING · admissibility is established by self-assigned tags

This is the defect underneath F-01, and independently the most serious.

`realizations.yaml` declares `satisfies_tags` per family; `normative.yaml`
declares `requires_tags` per invariant; the auditor checks set inclusion. Both
lists were written by the same author in the same sitting. A family "satisfies"
an invariant precisely when its author typed the tag.

So `deployed_state_maintained` appears on all five families, including three
whose folding DOF demonstrably exists — and the auditor reports permissiveness
verified.

**Effect: the permissiveness guarantee is vacuous.** It proves the author was
self-consistent, not that any family is admissible.

**Correction.** Require each family to declare a **state-maintenance class** and
an **evidence route**, and check that the route can actually establish that
class. A friction-dependent family whose only route is a zero-friction ideal-
joint model must not be accepted.

---

### F-12 · MAJOR · no evidence class can establish three of the five families

`evidence_scope.yaml` offers topology, CAD geometry, assembly path, mobility
analysis, kinematic simulation, human review — plus contact and structural, both
`NOT_AVAILABLE_IN_THIS_BENCHMARK`.

Mobility analysis establishes hard kinematic blocking. **Nothing** establishes:
an energy barrier (needs potential-energy or rigid-body stability evidence);
gravity seating (needs the same); friction retention (needs a friction model);
compliant engagement (needs contact or a reduced-order compliance model).

The Oracle therefore admits families it cannot verify, without saying so.

**Effect: OVERCLAIM.** Either those families are inadmissible — which would be
overfitting — or they are admissible with claims that must remain unverified.

**Correction.** The second. Add the missing evidence classes with honest
availability, and require the outcome to be NOT_VERIFIED where the route is
unavailable. Admissibility must not depend on the current toolset; **claims**
must.

---

### F-13 · MINOR · interference invariant has no deformation exception

NRM-BM-003-017 forbids interpenetration on every declared path. A compliant
snap-together assembly interpenetrates in the rigid sense while deflecting.

**Effect: FALSE REJECTION** of compliant assembly.

**Correction.** Permit a declared deformation-resolved path, and forbid such a
path from passing on rigid geometry alone.

---

### F-14 · NOT_A_DEFECT · "no friction coefficient required"

`assembly_and_mobility_expectations.yaml` `explicitly_not_required` lists *"Any
friction coefficient."* This looked like a contradiction with friction-dependent
retention.

It is not. The entry says no *acceptance threshold* on friction is required —
correct, since the source states none. It does not say friction-dependent
retention may be accepted without friction evidence. **Retained, with the
distinction made explicit** so a future reader does not resolve it the wrong way.

---

## Part 2 — The five families, examined rather than asserted

| Family | State-maintenance principle | Folding DOF in DEPLOYED | Barrier | Minimum verifier | Establishable | Must remain unresolved | Current result | Corrected result |
|---|---|---|---|---|---|---|---|---|
| ADM-001 over-centre | configuration past a singularity | **EXISTS** | energy barrier through the singularity | rigid-body stability / potential-energy analysis | that the deployed pose is a stable equilibrium under declared assumptions | margin, disturbance tolerance | **falsely rejected** by NRM-009 | ADMISSIBLE, persistence NOT_VERIFIED until a stability route exists |
| ADM-002 captive collar | geometric obstruction by a translating body | absent | hard kinematic block | mobility analysis + CAD | folding unavailable in DEPLOYED | wear, tolerance | accepted | ADMISSIBLE, persistence establishable now |
| ADM-003 compliant engagement | elastic deflection of a member | **EXISTS** (once deflected) | strain-energy barrier | contact or reduced-order compliance model | engagement geometry only | return reliability, force, fatigue | accepted **and** falsely rejected by NRM-016 if monolithic | ADMISSIBLE, persistence NOT_VERIFIED |
| ADM-004 gravity-seated strut | seating maintained by pocket geometry and weight | **EXISTS** (lift to unseat) | gravitational potential well | rigid-body stability under declared gravity | that seating is a stable equilibrium | disturbance magnitude, friction contribution | **falsely rejected** by NRM-009 | ADMISSIBLE, persistence NOT_VERIFIED |
| ADM-005 rotating sleeve | geometric obstruction by a rotating body | absent | hard kinematic block | mobility analysis + CAD | folding unavailable in DEPLOYED | wear, tolerance | accepted | ADMISSIBLE, persistence establishable now |

**Two of five are verifiable today. Three are admissible and conditionally
unverified.** That is the honest position, and it is a better one than the pack
currently claims: pretending all five are proven admissible hides that the
benchmark's evidence toolset covers only hard kinematic blocking.

---

## Part 3 — The thirteen required inspections

| # | Inspection | Result |
|---|---|---|
| 1 | "stay open on its own" equated with DOF absence? | **YES — F-01, BLOCKING** |
| 2 | Are differing state-maintenance principles permitted? | Listed but not genuinely permitted — F-01, F-11, F-12 |
| 3 | Is a separate persistent RELEASED forced? | **YES — F-02, F-03, BLOCKING** |
| 4 | Monolithic compliant contradicted? | **YES — F-04, BLOCKING** |
| 5 | Assembly endpoint freedom in the graph? | **NO — F-05** |
| 6 | Compact storage has a normative predicate? | **NO — F-06** |
| 7 | Clause↔invariant reciprocal? | **NO — F-07, 5 of 15** |
| 8 | Author independence accurate? | **NO — F-08** |
| 9 | Unresolved items cumulative? | **NO — F-09** |
| 10 | S05 prevented from embodying? | **YES — F-10** |
| 11 | Tags establish real admissibility? | **NO — F-11, BLOCKING** |
| 12 | Evidence scopes support each principle? | **NO — F-12** |
| 13 | Further contradictions? | F-13 interference/deformation; F-14 examined and dismissed |

---

## Part 4 — External findings, assessed

| Ext | Verdict | Basis |
|---|---|---|
| **A** over-narrow persistence | **CONFIRMED** | NRM-BM-003-009 predicate; falsely rejects ADM-001/003/004. Matches F-01. |
| **B** RELEASED + "exactly one" | **CONFIRMED** | NRM-BM-003-011 requires *"a distinct RELEASED configuration"*; CFG-BM-003-RELEASED requires *"exactly one respect"*. Two separate defects — F-02, F-03. |
| **C** bilateral interfaces vs compliant | **CONFIRMED** | NRM-BM-003-016 *"both participating bodies"* vs FRE-BM-003-002 admitting flexure. Matches F-04. |
| **D** assembly graph STORED-only | **CONFIRMED** | TRN-BM-003-ASSEMBLE `to: CFG-BM-003-STORED` vs FRE-BM-003-013. Matches F-05. |
| **E** compactness lacks a normative anchor | **CONFIRMED** | NEG-BM-003-016 anchors to NRM-BM-003-001, which contains no relational predicate; SRC-BM003-001 cited by nothing. Matches F-06. |
| **F** reciprocity unchecked | **CONFIRMED** | 5 of 15 mismatched, computed. Matches F-07. Stronger than stated: the existing check can be satisfied by a clause citing itself. |
| **G** independence overstated | **CONFIRMED** | `descriptor.authored_independently: true` vs `GOVERNANCE.prior_context_disclosure`. Matches F-08. |
| **H** unresolved items disappear | **CONFIRMED** | s07 `must_leave_unresolved: []`, s12 restores all ten. Matches F-09. |
| **I** S05 prohibited from deciding | **PARTIALLY_CONFIRMED** | The prohibition is real and wrong (F-10). But the fix is narrower than "S05 may decide": S05 must **embody the already-selected** candidate and must still not **substitute** one. Unqualified permission would license S05 to re-open a decision s02–s04 own. |
| **J** auditor structural/lexical only | **CONFIRMED, and superseded in part by F-11** | True as stated. F-11 identifies the specific mechanism — circular tag-based admissibility — which is what makes the structural pass misleading rather than merely incomplete. |

**Nothing rejected.** All ten external findings correspond to real defects. Two
are refined: I is narrowed, J is subsumed by a more precise account.

### Independent findings absent from the external review

- **F-11** circular tag-based admissibility — the root cause behind A and J.
- **F-12** no evidence route exists for three of five families.
- **F-13** interference invariant has no deformation exception.
- **F-14** examined and dismissed, recorded so it is not "found" again later.

---

## Part 5 — What this review does not establish

- That any invariant is physically true.
- That the five families are buildable. They are conceptual witnesses.
- That no further semantic defect remains. This review was conducted by the
  agent that authored the pack, which is exactly the limitation
  `GOVERNANCE.yaml` records. **Independent human semantic approval remains
  PENDING**, and nothing below changes that.

---
---

# Part 6 — Second review, after correction

## 6.1 Disposition of the initial findings

| Finding | Severity | Disposition |
|---|---|---|
| F-01 persistence = DOF absence | BLOCKING | **CONFIRMED, CORRECTED.** Four state-maintenance classes introduced. |
| F-02 persistent RELEASED forced | BLOCKING | **CONFIRMED, CORRECTED.** Six admissible representations. |
| F-03 "exactly one changed relationship" | BLOCKING | **CONFIRMED, REMOVED.** |
| F-04 bilateral interface rule | BLOCKING | **CONFIRMED, GENERALIZED** to bodies *or functional regions*. |
| F-05 assembly endpoint not in graph | MAJOR | **CONFIRMED, CORRECTED** to `to_any_of`. |
| F-06 compactness unanchored | MAJOR | **CONFIRMED, CORRECTED.** NRM-BM-003-018 added. |
| F-07 non-reciprocal mapping | MAJOR | **CONFIRMED, CORRECTED.** 5 mismatches → 0, exact both ways. |
| F-08 independence overstated | MAJOR | **CONFIRMED, CORRECTED.** Four typed fields replace one boolean. |
| F-09 unresolved items vanish | MAJOR | **CONFIRMED, CORRECTED.** Cumulative + stage-relevant lists. |
| F-10 S05 cannot embody | MAJOR | **CONFIRMED, CORRECTED.** Prohibition moved to substitution. |
| F-11 tag-based admissibility | BLOCKING | **CONFIRMED, CORRECTED.** Class + evidence route per family. |
| F-12 no route for 3 of 5 families | MAJOR | **CONFIRMED, CORRECTED.** Two evidence classes added, honestly unavailable. |
| F-13 no deformation exception | MINOR | **CONFIRMED, CORRECTED.** |
| F-14 friction coefficient | NOT_A_DEFECT | **REJECTED as a defect, retained with the distinction made explicit.** The entry says no acceptance *threshold* on friction is required. It never said friction-dependent retention may pass without friction evidence, and that reading is now written down so nobody resolves it the wrong way later. |

**Nothing was rejected except F-14, and that one was never a defect.**

## 6.2 External findings

All ten CONFIRMED. **I** narrowed (S05 must embody, not decide freely — unqualified
permission would license S05 to re-open a decision s02–s04 own). **J** confirmed but
superseded in precision by F-11, which names the mechanism: circular tag-based
admissibility is *why* a structural pass was misleading rather than merely
incomplete.

## 6.3 Defects found during correction

Three, all in my own new checks — worth recording because each would have made
the auditor look stronger than it was.

- **The compatibility rule was never inserted.** A string replacement targeted an
  indentation that did not exist and silently no-opped. Caught only because the
  mutation test for it failed. A `.replace()` that matches nothing is the quietest
  possible failure, and the reason the mutation test earns its place.
- **`check_release_representation_freedom` crashed** when the invariant it
  inspects was deleted, masking the finding that should have fired. A check that
  raises on the mutation it exists to catch reports `CHECK_ERROR` instead of the
  defect.
- **A-11 searched the whole file** for "deliberate" and found it in the new class
  definitions — reporting success while no invariant required anything. Now
  scoped to invariant statements and predicates.

## 6.4 Conceptual witnesses

Not CAD, not proven buildable — reasoning witnesses used to falsify the corrected
Oracle.

| Witness | Expected | Required evidence | Unresolved | Corrected Oracle gives |
|---|---|---|---|---|
| **A** hard-blocking rotating ring | ACCEPT, persistence establishable | mobility analysis + CAD | wear, tolerance | ✅ as expected — SMC-KINEMATIC_BLOCK, route available |
| **B** over-centre, folding path exists, deployed stable | ACCEPT, persistence NOT_VERIFIED | stability / potential-energy | margin, disturbance | ✅ as expected — previously **falsely rejected** |
| **C** gravity-seated strut | ACCEPT, persistence NOT_VERIFIED | stability under declared gravity | disturbance, friction share | ✅ as expected — previously **falsely rejected** |
| **D** monolithic compliant engagement | ACCEPT, persistence NOT_VERIFIED | reduced-order compliance | force, return reliability, fatigue | ✅ as expected — previously **falsely rejected twice**, by NRM-009 and NRM-016 |
| **E** distributed three-leg release, several relations change | ACCEPT | mobility before/after the action | effort | ✅ as expected — previously rejected by "exactly one respect" |
| **F** endpoint-only animation, no continuous path | **REJECT** | — | — | ✅ rejected by NRM-005 / NRM-012 / MOB-006, and NEG-BM-003-006 |

**Six of six give the expected result.** Four were wrong before the correction.

## 6.5 Permissiveness after correction

Five families, **three distinct state-maintenance classes**, none preferred:

- SMC-KINEMATIC_BLOCK — captive collar, rotating sleeve
- SMC-STABLE_EQUILIBRIUM_OR_ENERGY_BARRIER — over-centre, gravity-seated strut
- SMC-CONTACT_OR_COMPLIANT_RETENTION — compliant engagement
- SMC-OTHER_DECLARED_PHYSICAL_PRINCIPLE — open extension path

At least four materially distinct realization principles remain admissible.

## 6.6 Families needing evidence the toolset lacks

**Three of five.** Over-centre, gravity-seated and compliant engagement each need
a route that does not exist here: stability/potential-energy, or
contact/compliance analysis.

**They remain ADMISSIBLE with persistence NOT_VERIFIED.** This is the deliberate
position. Admissibility is a property of the design; verifiability is a property
of the toolset. Collapsing the two would make the Oracle reject correct answers
for a reason that has nothing to do with the design — the definition of
overfitting, here overfitting to tooling rather than to a mechanism.

## 6.7 Is the corrected Oracle too permissive anywhere?

Three places worth a human's attention.

- **`SMC-OTHER_DECLARED_PHYSICAL_PRINCIPLE` is deliberately open.** It could be
  used to declare a principle that is not really a principle. Mitigated by a
  heavier declaration burden — predicate, route, and what remains unsupported —
  but a determined run could still declare its way through. This is the price of
  not predicting the solution space, and I judge it worth paying.
- **The class is DECLARED, not verified.** Nothing checks that a design calling
  itself SMC-KINEMATIC_BLOCK really blocks kinematically. The auditor checks the
  *consequences* of the declaration; the declaration's truth is a human item.
- **NRM-BM-003-018 requires only ONE extent to shrink.** A design shrinking one
  dimension while growing two would pass. Requiring more would need a
  compactness measure the source does not supply, so the weak form is the honest
  one — but it is genuinely weak, and it is listed for review.

## 6.8 Too restrictive anywhere?

None found in this pass. The four false rejections are corrected and the six
witnesses behave. The residual risk is asymmetric: the corrections all moved the
Oracle toward permissiveness, so a *new* false rejection is unlikely and a new
false acceptance is the thing to watch.

## 6.9 What the auditor still cannot establish

Declared in `UNCHECKABLE_REQUIRING_HUMAN_REVIEW` and reported with every run:

1. Whether any invariant is physically true.
2. Whether a declared state-maintenance class is the principle the design uses.
3. Whether the admissible families are buildable.
4. Whether the Oracle is overfitted in a way nobody encoded as a check.
5. Whether a deployment sequence is comprehensible to a human.

The auditor is a **structural and declared-semantic consistency auditor**. It
proves the pack agrees with itself. It cannot prove the pack agrees with physics.

## 6.10 Status

- Oracle files **frozen**, hash manifest regenerated and verified.
- Semantic self-review **complete** and acted on.
- Production visibility **false**, unchanged.
- BM-003 **structurally scorable**.
- **Independent human semantic approval: PENDING.**

The same agent authored the source, the Oracle, this review and the corrections.
That is recorded in `GOVERNANCE.yaml` `author_independence` as
`SAME_AGENT_SEPARATE_TASK`, with `independent_author: false`. Thoroughness is not
independence, and the descriptor status says so rather than rounding up:
`ORACLE_SEMANTIC_REVIEW_COMPLETE_HUMAN_APPROVAL_PENDING`.

**The single most valuable thing a human reviewer can do** is check whether the
five families really are all admitted — because that was wrong before this
review, the auditor reported PASS throughout, and the same blind spot that
produced it could have produced another.

---
---

# Final propagation review before CAD validation

Baseline `08de920084f67da40b5dbc41bf03e341246d1166`. Source hash verified
unchanged. Auditor PASS 29/29, 58 Oracle tests green — and the pack still
contains statements from the *pre-correction* model.

**Why a passing auditor missed them.** The previous correction fixed each defect
where the auditor looked. `check_compliant_realization_not_excluded` inspects
`NRM-BM-003-016.verification_predicate`; the predicate was corrected and the
**statement of the same invariant** was not. The check passed on a file that
still says the old thing one line above where it looked. That is the shape of
every finding below: a semantic model changed, and its consequences were
propagated to the places under test rather than to every place they hold.

## Independent findings

### P-01 · MAJOR · NRM-BM-003-012 hard-codes the literal RELEASED sequence

`normative.yaml` — predicate: *"A continuous, sampled path exists from DEPLOYED
**through RELEASED and FOLDING** to STORED"*.

Intended: after the deliberate release condition — however represented — a
continuous path to STORED exists. **False rejection** of a squeeze-and-fold grip
or any distributed release with no separately stable pose, i.e. of designs
`CFG-BM-003-RELEASED.admissible_representations` explicitly admits. The pack
contradicts itself in two files.

*Correction:* realization-neutral wording. *Mutation:* reintroduce a mandatory
persistent RELEASED configuration.

### P-02 · MAJOR · RELEASED treated as a required node in six further places

| File | Object | Stale text |
|---|---|---|
| `assembly_and_mobility_expectations.yaml` | MOB-BM-003-001 | *"In RELEASED, each leg's folding motion is available"* |
| " | MOB-BM-003-003 | *"The difference between DEPLOYED and RELEASED must be demonstrated"* |
| `configurations.yaml` | CFG-BM-003-FOLDING | *"between RELEASED and STORED"* |
| " | TRN-BM-003-FOLD | `from: CFG-BM-003-RELEASED` |
| " | TRN-BM-003-FOLD_REVERSE | `from: CFG-BM-003-RELEASED` |
| `evidence_scope.yaml` | EVC-BM-003-MOBILITY | *"DEPLOYED and RELEASED differ in available folding mobility"* |
| `realizations.yaml` | INADM-BM-003-001 | *"Nothing distinguishes DEPLOYED from RELEASED"* |

Same risk as P-01. The transition edges are the worst of these: a graph walker
finds folding reachable **only** from a node the Oracle says is optional.

### P-03 · MAJOR · hard-DOF-lock language survives in four places

| File | Object | Stale text |
|---|---|---|
| `configurations.yaml` | TRN-BM-003-DEPLOY | *"Arrival at a state where **folding is blocked**"* |
| `assembly_and_mobility_expectations.yaml` | MOB-BM-003-004 | *"the analysis shows each is **unavailable**"* |
| `freedoms.yaml` | FRE-BM-003-001 | *"That **folding is unavailable in DEPLOYED**"* |
| `ambiguities.yaml` | AMB-BM-003-005 | *"That **folding is unavailable** before a deliberate action"* |

**False rejection** of over-centre, gravity-seated and compliant families — the
exact defect F-01 corrected, still asserted in the file that *frees* the locking
principle. FRE-BM-003-001 is the sharpest: the freedom permitting any
state-maintenance principle constrains the design to one.

*Correction:* behavioural semantics — *does not enter* unintended folding under
the declared ordinary-operation scenario — with evidence remaining class-dependent.

### P-04 · MAJOR · monolithic-compliant propagation incomplete

| File | Object | Stale text |
|---|---|---|
| `normative.yaml` | NRM-BM-003-016 **statement** | *"realized by identifiable geometry on **each participating body**"* |
| `assembly_and_mobility_expectations.yaml` | ASM-BM-003-004 | *"realized by geometry on **both participating bodies**"* |
| `freedoms.yaml` | FRE-BM-003-002 | *"realized by geometry on **both bodies**"* |
| `evidence_scope.yaml` | EVC-BM-003-CAD | *"a declared interface exists as geometry on **both bodies**"* |

**False rejection** of a living hinge, which has one body. The auditor check
inspects one field of one invariant, so it verified the fix at the single point
it was applied.

*Correction:* the general rule everywhere, and an auditor check that scans every
occurrence rather than one predicate.

### P-05 · MAJOR · `satisfies_tags` still reads as physical evidence

`realizations.yaml` / `check_fixture_permissiveness` / finding code
`ADMISSIBLE_FAMILY_REJECTED`.

A family "satisfies" an invariant when its author typed the tag. The name says
*satisfies*, the finding says *rejected* — both assert a physical relation the
data cannot support. F-11 diagnosed this and corrected the *consequence* (classes
and routes) while leaving the *vocabulary* claiming what it always claimed.

*Correction:* rename to `declared_coverage_tags`,
`check_declared_family_coverage_consistency`, finding
`DECLARED_COVERAGE_INCOMPLETE`, with an explicit statement that this establishes
author-declared coverage only. *Mutation:* adding tags must not make a family
physically accepted.

### P-06 · MAJOR · contact-evidence self-contradiction

`evidence_scope.yaml` EVC-BM-003-CONTACT: *"**No invariant in this Oracle depends
on one**, which is deliberate."*

False since the classes were introduced. A design declaring
`SMC-CONTACT_OR_COMPLIANT_RETENTION` **requires** a contact or compliance route
for its persistence claim. **Overclaim** — it tells a reader the missing route
costs nothing.

*Correction:* no invariant *universally* requires contact analysis; a design
relying on that class does, and without it persistence is NOT_VERIFIED.

### P-07 · MINOR · duplicate `UNCHECKABLE_REQUIRING_HUMAN_REVIEW`

`audit_bm003_oracle.py` lines 62 and 73 — a botched splice during the previous
task. Harmless today; two lists that can diverge is a defect waiting.

### P-08 · MAJOR · direct execution of the test file is broken

`python ver3/tests/meta/test_bm003_oracle.py` raises
`ImportError: attempted relative import with no known parent package`. It never
ran, so the `__main__` block was never exercised.

**Worse than the reported placement issue.** The block sits at line 352 of 561 —
even with imports fixed it would run only the classes defined above it, silently
skipping every semantic mutation. A developer running the file directly would see
a green result covering less than half the suite.

*Correction:* package-aware import fallback **and** move the block to the end.
Both, and verify both execution modes.

### P-09 · MAJOR · descriptor overstates BM-003's readiness

`descriptor.yaml` `oracle_status_notice.blocks`: *"**Nothing further from
BM-003's side.**"*

Independent human semantic approval is PENDING and positive-executable
permissiveness validation has not happened. **Overclaim.**

## Reported issue list, assessed

| Reported | Verdict | Evidence |
|---|---|---|
| mandatory persistent RELEASED | **CONFIRMED** | P-01, P-02 — 7 sites incl. two transition edges |
| hard kinematic blocking as the only persistence | **CONFIRMED** | P-03 — 4 sites, incl. the freedom that frees it |
| bilateral two-rigid-body interfaces | **CONFIRMED** | P-04 — 4 sites, incl. NRM-016's own statement |
| self-assigned tags as physical proof | **CONFIRMED** | P-05 — naming still asserts it |
| contradictory contact-evidence description | **CONFIRMED** | P-06 |
| overstated human/author independence | **PARTIALLY_CONFIRMED** | Governance and descriptor independence fields are correct after F-08. The residue is a *readiness* overclaim, not an *independence* one — P-09 |
| direct-execution test gaps | **CONFIRMED, and worse than reported** | P-08: import failure, not just block placement |

**Nothing rejected.** Two findings are independent of the report: P-07, and the
import-failure half of P-08.

## Conceptual challenge after propagation

Reasoning witnesses, not CAD, and none is claimed physically proven.

| | Witness | Expected | Evidence required | Unresolved | Actual | Auditor limitation |
|---|---|---|---|---|---|---|
| **A** | hard geometric blocking ring | ACCEPT, persistence establishable | mobility analysis + CAD | wear, tolerance, effort | ✅ SMC-KINEMATIC_BLOCK, route available | cannot confirm the ring really obstructs — the class is declared |
| **B** | over-centre, folding path exists, deployed stable | ACCEPT, persistence NOT_VERIFIED | stability / potential-energy | margin, disturbance | ✅ path existence is the premise, not a defect | cannot evaluate stability at all |
| **C** | gravity-seated support | ACCEPT, persistence NOT_VERIFIED | stability under declared gravity | disturbance, friction share | ✅ | same |
| **D** | monolithic compliant engagement | ACCEPT, persistence NOT_VERIFIED | reduced-order compliance | force, return reliability, fatigue | ✅ — realizable in ONE body after P-04 | cannot evaluate deflection |
| **E** | distributed multi-leg release, no stable released pose | ACCEPT | mobility before/after the deliberate action | effort | ✅ — `TRN-BM-003-FOLD` now reachable from DEPLOYED directly | cannot confirm the action is "deliberate" to a user |
| **F** | endpoint-only animation, no continuous path | **REJECT** | — | — | ✅ NRM-005 / NRM-012 / MOB-006 | — |
| **G** | contact-dependent detent, rigid geometry only | **persistence NOT_VERIFIED, never PASS** | contact or reduced-order compliance | engagement force, wear | ✅ route incompatible with the declared class | cannot tell a real detent from a declared one |

**Seven of seven as expected.** D and E would have been rejected before this
propagation pass: D by the bilateral wording in `NRM-BM-003-016`'s statement and
in `ASM-BM-003-004`, E by `TRN-BM-003-FOLD`'s single `from: RELEASED` edge.

**G is the case worth watching.** It is accepted as a *design* and its persistence
claim is NOT_VERIFIED. That is correct — but it means a contact-dependent detent
and a hard geometric block are, today, distinguishable only by what their authors
declared. The auditor checks the consequences of the declaration, never its truth.

## Residual limitations

- The state-maintenance class is **declared**, never verified. Every acceptance
  above is conditional on the declaration being honest.
- Three of five families still have **no executable evidence route** in this
  benchmark. Admissible, persistence NOT_VERIFIED — deliberately, since
  admissibility is a property of the design and verifiability a property of the
  toolset.
- **Positive-executable permissiveness validation has not happened.** The five
  families are reasoned witnesses; nothing has been built and run against the
  Oracle. This is the largest remaining gap and it is recorded as
  `PENDING_BEFORE_S03_S04_FREEZE`.
- **Independent human semantic approval remains PENDING.** Two rounds of
  self-review by the authoring agent found nineteen findings between them, five
  of them BLOCKING, in a pack whose auditor reported PASS throughout. That is
  evidence the method finds things — and equally evidence that a third round by
  the same agent is not what is needed next.
