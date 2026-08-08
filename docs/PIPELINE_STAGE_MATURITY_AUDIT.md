# Pipeline stage maturity audit — S01 to S12

**Task.** Determine the current engineering maturity of every stage. No
implementation, no contract modification, no redesign.

**Method.** Every stage assessed independently against thirteen questions, then
placed on the L0–L5 scale. Evidence is what exists in the repository, not what
was intended.

---

## 0. A finding that must come first

**The contract layer is currently RED.** `python3 -m unittest discover -s
ver3/tests/meta -t .` reports **7 failures out of 309 tests**. Five were caused
by the contract edits made in the previous task; two pre-date it.

| failure | cause | mine? |
|---|---|---|
| `test_audit_covers_every_family_and_nothing_else` | `ENTITY_FAMILY_AUDIT.yaml` still lists 32 families; `DESIGN_STATE_CONTRACT` now has 38 keys | **yes** |
| `test_audit_count_matches_reality` | same | **yes** |
| `test_summary_totals_to_the_family_count` | same (`38 != 32`) | **yes** |
| `test_every_family_has_an_owner` | `CompliantJoint` is a key in `entity_families` but is absent from any stage's `owns` list | **yes** |
| `test_family_owned_by_matches_ownership_matrix` | same root cause | **yes** |
| `test_bm003_still_has_no_positive_executable_reference` | the BM-003 executable reference now exists; the test encodes the world before it | no — pre-existing |
| `test_no_positive_reference_exists_for_bm003` | same | no — pre-existing |

**This corrects the basis of the previous task's verdict.** I issued "READY WITH
SMALL DEFERRED DEBTS" without running the meta suite. The verdict's *substance*
survives — every failure is a synchronisation defect, not an architectural one —
but it was issued on an unverified basis and that is a process miss worth
stating plainly.

**The `CompliantJoint` failure is the informative one.** I documented it under its
own key in `entity_families` while calling it "a `joint_type` of `Joint`, not a
separate family". The test correctly refuses that: a thing with its own key is a
family and needs an owner. Either it becomes a real family (38, owned by s03) or
it moves inside `Joint` as a constrained variant (37, no new key). **That is a
contract decision, not a test fix**, and it is unresolved. It does not block
implementation but it must be settled before the family audit is re-synchronised.

The two pre-existing failures are a different class: the meta suite asserts
BM-003 has no positive executable reference, and it now has one. Whoever owns the
freeze gate must decide whether that assertion retires.

---

## 1. Per-stage assessment

Thirteen questions per stage. `Y` yes, `P` partial, `N` no.

| | S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 | S09 | S10 | S11 | S12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| responsibility clear | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | P |
| engineering question well defined | Y | Y | Y | Y | Y | Y | Y | P | P | N | P | P |
| inputs sufficient | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | P |
| outputs sufficient for consumer | Y | Y | Y | Y | Y | Y | Y | P | P | N | P | P |
| ownership boundaries clear | Y | Y | Y | Y | Y | Y | Y | N | N | P | Y | Y |
| prohibited decisions explicit | Y | Y | Y | Y | Y | Y | Y | P | P | P | P | P |
| **reasoning procedure specified** | Y | **N** | P | Y | P | **N** | Y | N | P | N | P | N |
| representation sufficient | Y | Y | Y | Y | Y | P | Y | P | P | N | Y | P |
| deterministic validation criteria | Y | Y | Y | Y | Y | Y | Y | N | N | N | N | N |
| benchmark-tested | P | P | P | P | P | N | **Y** | P | P | N | P | N |
| architecture-reviewed | Y | Y | Y | Y | Y | Y | Y | N | N | N | N | N |
| implementation-reviewed | N | N | N | N | N | N | N | N | N | N | N | N |
| implementation-ready reviewed | Y | Y | Y | Y | Y | Y | Y | N | N | N | N | N |

"benchmark-tested = P" means tested by *retrospective replay* against BM-001/002/
003 — a consumer-sufficiency thought experiment — never by execution. Only S07 is
`Y`, and only because three working compilers exist.

---

### S01 — requirement capture

**Maturity: L3.**

- **Evidence.** Full contract (`stages/S01_CONTRACT.yaml`) with all ten sections;
  five deterministic checks including the sharpening check S01-C2; consumer
  boundary replayed against all three benchmarks; the `quantity_class` and
  `Scenario.kind` additions came from concrete BM-001/BM-002 gaps.
- **Missing before implementation.** The S01→S02 sufficiency probe. Nothing else.
- **Risk: LOW.** Extraction and classification with a mechanically checkable
  failure mode.
- **Depends on earlier:** nothing. **Later stages depend on it:** all.
- **Note.** No prior "Stage 01 redesign" artifact exists in the repository. If one
  was produced in an earlier session it was not committed; the contract written
  in the previous task is the only S01 specification that exists.
- **Begin now? YES** — after the probes.

### S02 — obligation, load and candidate formation

**Maturity: L2.**

- **Evidence.** Full contract; `LoadCase` ownership settled with SF-5.3 as the
  authority; `obligations_created` closes R-16; evidence-route verdict closes the
  P-6 pattern seen three times.
- **Why not L3.** Two things:
  1. **The reasoning procedure is not specified.** "Generate genuinely different
     candidate families" is a responsibility, not a method. This is the least
     specified reasoning step in S01–S07, and it is the stage with the highest
     LLM dependence.
  2. **`LoadCase` has never been produced, even by hand.** No benchmark, no
     Oracle and no CAD reference contains one. Every other S02 output has a
     manual precedent; this one has none.
  Also, the **evidence-route capability registry does not exist** — the contract
  references it as an input.
- **Missing before implementation.** A candidate-generation method; the
  capability registry; one worked `LoadCase` set per benchmark.
- **Risk: MEDIUM–HIGH.** Not because the contract is wrong, but because an
  unspecified generative procedure will produce whatever the model finds easy.
- **Depends on earlier:** S01. **Later:** S03 depends on it heavily.
- **Begin now? YES for obligations and load cases. NOT YET for candidate
  generation** — specify the method first.

### S03 — topology, mobility and assembly strategy

**Maturity: L3.**

- **Evidence.** The most heavily reviewed stage in the repository. DOF totality,
  blocking relations with direction/blocker/defeat/driver, the compliance
  representation, candidate-specific load paths, assembly steps with the
  retention trichotomy — every one traced to a specific recorded failure
  (HCR-BM001-002/-004/-006, BM-003 R2/R4/R7, BM-002 CHG-02, SF-5.3). Twelve
  deterministic exit checks. Consumer boundary replayed three times.
- **Missing before implementation.** The S02→S03 and S03→S04 probes; the DOF
  enumeration utility (mechanical, not LLM).
- **Risk: HIGH — the highest of any stage.** It carries the most new machinery
  and none of it has ever been produced, even by hand. A total DOF disposition
  has never existed for any benchmark. Open question D-3 (can an LLM disposition
  reliably?) lands entirely here.
- **Depends on earlier:** S02, including load cases. **Later:** S04, S05 and S08
  all consume it; S08's defeat specifications originate here.
- **Begin now? YES — and it should be the first hard stage.** Its risk is
  concentrated and discoverable early.

### S04 — placement, motion and spatial feasibility (two passes)

**Maturity: L3.**

- **Evidence.** Full contract with both passes and the gate between them; nine
  exit checks; the two-pass split is a direct response to a counted infeasibility
  (7 and 5 admissible fixtures against a manual process that carried 2, 1 and 1).
  **`valcore.py` is a working reference implementation of most S04·B checks** —
  swept sampling with declared refinement, interference, assembly sweeps against
  the preceding configuration.
- **Missing before implementation.** The S03→S04 and S04·B→S05 probes; a decision
  on the S04·A elimination-rate budget (D-4).
- **Risk: MEDIUM.** The expensive half has a working precedent. The novel half is
  S04·A, which is cheap and conservative by construction.
- **Depends on earlier:** S03. **Later:** S05 consumes located frames, engagement
  sites and region volumes.
- **Begin now? YES.**

### S05 — feature and realization

**Maturity: L3.**

- **Evidence.** Full contract; envelope constraints and the every-clearance rule
  both traced to recorded failures (CHG-01/CHG-03, BM-003 R3/R5/R6); ten exit
  checks; three references' `interactions.yaml` and `build.py` are worked
  precedents for the feature graph and ROI machinery.
- **Why still L3 and not higher.** The reasoning procedure is **partially**
  specified: feature *completeness* is enumeration over S03's relation set and is
  fully specified, but feature *proposal* depends on a knowledge base whose packs
  are all `PRE_CAD_SEMANTIC_REVIEWED` with every fixture
  `NEEDS_GEOMETRY_VALIDATION`. Using them imports whatever is wrong in them.
- **Missing before implementation.** The S04·B→S05 probe; a decision on whether
  the micro-oracle packs are usable as a KB in their current state.
- **Risk: MEDIUM–HIGH**, concentrated in the KB dependency.
- **Depends on earlier:** S03, S04·B. **Later:** S06 and S07.
- **Begin now? YES for the enumeration half. The KB question is separable.**

### S06 — parameter resolution

**Maturity: L2.**

- **Evidence.** Full contract; the convergence block is the most carefully
  falsified element in the architecture — its termination rule was replaced after
  replay against BM-003 R1→R4 showed the proposed rule would falsely terminate a
  solvable problem. Scope, budgets, cone and non-convergence all specified.
- **Why not L3.** Two gaps, and the second is the serious one:
  1. **No benchmark ever solved a constraint system.** All parameters in all
     three references were hand-derived arithmetic — `4.0 + 2.0 + 45.0 + 9.0`.
     There is zero empirical grounding for the solving capability.
  2. **The constraint expression language does not exist.** `Constraint` has an
     `expression` field and nothing defines its grammar, its type system or what
     the solver must be able to parse. Implementing S06 today means inventing
     that language at implementation time — which is precisely R-22, *"symbolic
     expression deferred to CAD time"*, one stage earlier.
- **Missing before implementation.** The constraint expression grammar and its
  solvability classes. This is genuine contract work.
- **Risk: HIGH.** The one stage where beginning now would create a retirement-row
  defect.
- **Depends on earlier:** S05. **Later:** S07 cannot run without it.
- **Begin now? NO.** Specify the expression language first.

### S07 — geometry compilation

**Maturity: L3 — the best-evidenced stage in the pipeline.**

- **Evidence.** **Three working compilers exist.** `EXE-BM001-02/build.py`,
  `EXE-BM002-01/build.py` and `EXE-BM003-01/build.py` are exactly what S07 must
  be: parameters plus a construction program in, valid B-rep solids out. Plus
  `valcore` steps 1–3 for validity, signature and round-trip. Six exit checks.
  The contract is short because the stage is pure: it owns no engineering
  decision.
- **Missing before implementation.** Only the construction-program schema from
  S05. Given a hand-authored program, **S07 is testable in isolation today.**
- **Risk: LOW.** Lowest of any stage.
- **Depends on earlier:** S05 program, S06 values. **Later:** S08, S09.
- **Begin now? YES — and out of order.** See the roadmap.

### S08 — verification planning

**Maturity: L1.**

- **Evidence.** Ownership matrix entry with three `may_not` rules; Oracle
  `stage_expectations` `must_exist` lists in every pack; `VerificationPlanItem`
  and `NegativeControl` families defined; **37 worked negative controls across
  BM-002 (20) and BM-003 (17)**, including three that failed to fire and were
  fixed — the richest empirical material of any unbuilt stage.
- **What is missing.** No per-stage contract. No reasoning procedure — "plan how
  each requirement will be checked" is a responsibility. No deterministic exit
  checks. Its responsibility just *changed*: defeat specifications now originate
  at S03/S05, so S08 schedules and parameterizes rather than invents, and no
  contract records that.
- **Risk: MEDIUM** once a contract exists; the material to write one is unusually
  good.
- **Depends on earlier:** S03 and S05 (defeat specs), S07 (solids). **Later:** S09.
- **Begin now? NO — write the contract first.**

### S09 — evidence execution

**Maturity: L1.**

- **Evidence.** Ownership entry; Oracle expectations; `EvidenceItem` with
  mandatory fidelity and contact resolution; **`valcore.py` is substantially a
  working S09 for the CAD evidence route**, and the three `validate.py` files plus
  two MuJoCo simulations are worked multi-route precedents.
- **What is missing.** No contract. The multi-route case is only half-explored:
  the CAD route is mature, the dynamics route was exercised twice with heavy
  declared assumptions, and the compliance route does not exist at all.
- **Risk: LOW–MEDIUM.** The strongest implementation head-start of the five late
  stages.
- **Depends on earlier:** S08. **Later:** S10, S11.
- **Begin now? NO — contract first, but it will be the easiest of S08–S12 to write.**

### S10 — evidence consolidation

**Maturity: L1, and it is the least developed stage in the pipeline.**

- **Evidence.** Ownership entry with `owns: []` — it only extends. Two `may_not`
  rules. One Oracle expectation: *"exactly one outcome per planned observable"*.
- **What is missing.** Almost everything. Its engineering question — *how do you
  reconcile two pieces of evidence at different fidelities that disagree?* — has
  **no worked example anywhere in the repository**. No manual analogue was ever
  produced, because the manual process never had contradictory evidence to
  reconcile: it had one route per claim.
- **Risk: HIGH**, from pure absence of precedent rather than from difficulty.
- **Depends on earlier:** S09. **Later:** S11.
- **Begin now? NO.** This is where architecture effort should go after S03.

### S11 — requirement evaluation

**Maturity: L1.**

- **Evidence.** Ownership entry; `RequirementEvaluation` with the mandatory
  six-field scope block (INV-009); `ExcludedClaim` with "silence is not
  exclusion"; **`actual_evaluation.json` in all three references is a manual S11
  output**, including honest `UNSUPPORTED` and `NOT_VERIFIED` verdicts against
  named ambiguities.
- **What is missing.** No contract. The matching rule (INV-012: match on
  requirement/criterion/scenario/observable, never on unit) is stated in the
  DesignState contract but has no procedure.
- **Risk: MEDIUM.** Good material, well-understood failure modes (R-25, R-26).
- **Depends on earlier:** S10. **Later:** S12.
- **Begin now? NO.**

### S12 — failure attribution and revision

**Maturity: L1.**

- **Evidence.** Ownership entry; `FailureProvenance` and `HumanReviewQuestion`
  families; the ten `HCR-BM001-*` decisions are a manual analogue of human review
  questions carried out of the pipeline.
- **What is missing.** No contract. Its responsibility just **shrank**: the
  invalidation cone moved to `StagePatch`, so S12 no longer computes it — it
  consumes it. No contract records that. Failure *routing* — attributing a
  failure to the decision and stage that own it — has never been exercised.
- **Risk: MEDIUM–HIGH.** The `may_not` rule "do not attribute a failure to the
  last stage that touched the artifact by default" describes a failure mode with
  no defined alternative procedure.
- **Depends on earlier:** S11, and on the cone from every patch. **Later:** none.
- **Begin now? NO.**

---

## 2. Roadmap answers

### 1. Which stage should be implemented next?

**None yet — two non-stage items come first**, then **S01**.

1. **Re-synchronise the contract layer** (7 meta failures), including the
   `CompliantJoint` family-or-variant decision.
2. **Write the nine sufficiency probes** and run them against hand-authored
   S03/S04·B fixtures derived from the three CAD references.
3. Then **S01**, which is L3 and LOW risk.

### 2. Which later stages are mature enough to skip another architecture review?

**S01, S03, S04, S05, S07.** All L3: architecture validated by benchmark/Oracle/
CAD retrospective, representation and consumer boundaries reviewed across three
benchmarks, deterministic exit checks defined. They need probes, not reviews.

### 3. Which stages still require substantial contract or architecture work?

- **S02** — candidate-generation method; the evidence-route capability registry.
- **S06** — the constraint expression language. Non-negotiable.
- **S08, S09, S11** — per-stage contracts, with good material to write them from.
- **S10, S12** — contracts *and* architecture. S10 has no precedent at all; S12's
  responsibility changed and its core procedure is undefined.

### 4. Is any stage after S02 dangerous to implement now?

**Yes — S06, and it is the clearest case in the audit.** Its `Constraint`
carries an `expression` field with no defined grammar. Implementing S06 today
means inventing the expression language inside the implementation, which is
R-22 — *"symbolic expression deferred… the solver reports success for something
unsolved"* — reproduced one stage earlier than Ver2 did it.

**Also dangerous, for a different reason: S08 implemented before S03 and S05.**
Its defeat specifications now originate upstream. Building S08 first would force
it to author controls from geometry, which is `DEF-01`, `DEF-02` and `NC-17` —
three recorded instances of controls that could not fire.

S03, S04, S05 and S07 are safe.

### 5. Recommended implementation order from today

| # | work | why here |
|---|---|---|
| 0 | Re-sync contracts; settle `CompliantJoint`; rule on the two BM-003 freeze-gate tests | the layer is RED; everything downstream inherits it |
| 1 | Nine sufficiency probes | mandated by `STAGE_PROGRESSION_CONTRACT` step 6; they do not exist |
| 2 | Hand-author S03/S04·B fixtures from the three CAD references; run the probes | highest value per unit of effort; finds architecture defects with zero stage code |
| 3 | **S01** | L3, LOW risk, unblocks everything |
| 4 | **S02** obligations + load cases | L2 but the load half is contract-complete |
| 4b | Specify candidate generation; build the capability registry | in parallel; blocks nothing else |
| 5 | **S03** | L3, HIGH risk, concentrated — surface it early |
| 6 | **S07**, out of order | testable *today* in isolation against three existing compilers; retires the lowest-risk stage while S02/S03 risk is being burned down |
| 7 | **S04·A**, measure the elimination rate (D-4), then **S04·B** | L3; `valcore` is a working precedent |
| 8 | Specify the constraint expression language | the S06 blocker |
| 9 | **S06** as a solver service, then **S05** against it, then close the convergence block | S05 may not set a value without a solver artifact, so S06 must exist first |
| 10 | Write **S08**, **S09**, **S11** contracts | good material exists |
| 11 | Architecture work on **S10**, then **S12** | least precedent; needs design, not just a contract |

---

## 3. Maturity table

| stage | name | maturity | risk | begin now? | blocking gap |
|---|---|---|---|---|---|
| **S01** | requirement capture | **L3** | LOW | **yes** | probe only |
| **S02** | obligation, load, candidate | **L2** | MED–HIGH | partly | candidate-generation method; capability registry |
| **S03** | topology, mobility, assembly | **L3** | **HIGH** | **yes** | none — risk is inherent, not architectural |
| **S04** | placement, motion, spatial proof | **L3** | MED | **yes** | elimination-rate budget |
| **S05** | feature and realization | **L3** | MED–HIGH | partly | knowledge-base validity |
| **S06** | parameter resolution | **L2** | **HIGH** | **no** | **constraint expression language** |
| **S07** | geometry compilation | **L3** | **LOW** | **yes** | construction-program schema |
| **S08** | verification planning | **L1** | MED | no | no contract |
| **S09** | evidence execution | **L1** | LOW–MED | no | no contract |
| **S10** | evidence consolidation | **L1** | **HIGH** | no | **no precedent anywhere** |
| **S11** | requirement evaluation | **L1** | MED | no | no contract |
| **S12** | failure attribution | **L1** | MED–HIGH | no | no contract; responsibility changed |

Nothing is L4 or L5: no stage is implemented, and no integrated pipeline exists.

---

## 4. Highest remaining architectural risks

1. **S10 has no precedent of any kind.** Reconciling contradictory evidence
   across fidelities was never done manually, because the manual process had one
   route per claim. It is the only stage whose *engineering question* is
   undefined rather than merely unspecified.
2. **The S06 constraint expression language does not exist**, and its absence is
   the one place where beginning implementation would manufacture a
   retirement-row defect.
3. **Total DOF disposition has never been produced by anyone.** S03's central
   mechanism is unexercised, and open question D-3 — whether an LLM can produce a
   *total* disposition without plausible-sounding omissions — is exactly the
   failure that caught a careful human three times on BM-001.
4. **The knowledge base is unvalidated.** All micro-oracle packs are
   `PRE_CAD_SEMANTIC_REVIEWED` with every fixture `NEEDS_GEOMETRY_VALIDATION`.
   S02 and S05 both depend on it.
5. **The contract layer is not self-consistent**, and the previous task's
   readiness verdict was issued without running the suite that says so.

---

## 5. Where engineering effort should go next

**First, and cheaply: close the RED.** Re-synchronise `ENTITY_FAMILY_AUDIT`,
settle `CompliantJoint`, and rule on the two BM-003 freeze-gate assertions. Hours,
not days, and everything downstream inherits the inconsistency otherwise.

**Then the highest-leverage item in the whole plan: the probes and the
hand-authored fixtures (roadmap steps 1–2).** They need no stage code, they use
the only ground truth the repository has, and a probe that passes on an input
missing something the CAD demonstrably needed is a probe defect found for free.
Every architectural claim made across four review documents is testable there.

**Then split effort three ways:**

- **Build** S01 → S03 → S07 → S04, in that order, accepting that S03 carries the
  risk and surfacing it early.
- **Specify** the constraint expression language and the candidate-generation
  method, in parallel — neither blocks the build track.
- **Design** S10, which needs architecture rather than a contract, and which is
  the only stage in the pipeline whose question is still open.

The pattern across this audit is consistent: **the front of the pipeline is
mature and the back is not.** S01–S07 have contracts, exit checks and three-way
benchmark replay. S08–S12 have role statements and, in two cases, excellent raw
material that nobody has yet turned into a contract. That is the correct place to
be before implementation — provided the back half is not mistaken for being as
ready as the front.

---

*Assessed from: `ver3/contracts/` including the seven new `stages/` contracts;
`ver3/phase0/`; `ver3/oracles/` stage expectations in all packs;
`ver3/cad_validation/` three references, `valcore`, `cadval`, simulations and
negative controls; `ver3/tests/meta/` (executed, 309 tests, 7 failures); and the
four prior review documents. Nothing was implemented or modified.*
