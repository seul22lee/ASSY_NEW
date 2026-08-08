# Pipeline implementation readiness

**Task.** Apply the sixteen corrections, align the Stage 01–07 contracts and the
representation contract, run one final interface sufficiency check, and leave the
repository implementation-ready.

**No stage logic was implemented.** No CAD, Oracle, simulation, benchmark or
validation code was touched.

**Verdict: B — READY WITH SMALL DEFERRED DEBTS.**

---

## 1. Corrections applied

All sixteen from `PIPELINE_HIGH_RISK_ARCHITECTURE_CHECK.md`, incorporated into
the architecture rather than appended as notes.

| id | correction | where it now lives |
|---|---|---|
| C-1 | one `RigidGroup` + one compliant `Joint` **per compliant member**; a "region" is a set of joints co-actuated by a `Transition` | proposal §3 S03; `DESIGN_STATE_CONTRACT` `RigidGroup`, `co_actuated_by`; `S03_CONTRACT.compliance_rule` |
| C-2 | `required_travel` and `allowable_travel` are **separate fields** | proposal §3 S03 travel rule; `CompliantJoint`; `S03_CONTRACT` |
| C-3 | `actuation: PRESCRIBED_KINEMATIC` | same |
| C-4 | `compliant_element` + `root_interface` named | same |
| C-5 | compliant coordinate is zero outside its activation set | `S04_CONTRACT` check S04B-C7; proposal §3 S04·B |
| C-6 | `AssemblyStep.path_kind`; `DEFORMATION_RESOLVED` ⇒ `NOT_VERIFIED`, never `PASS` | `AssemblyStep`; `S03_CONTRACT.assembly_step_rule` |
| C-7 | `depends_on_compliant_recovery` on blocking relations | `blocked_by` relation; `S03_CONTRACT` |
| C-8 | `LoadCase` candidate-independent, with `kind` | proposal §3 S02; `LoadCase`; `S02_CONTRACT.load_case_ownership` |
| C-9 | `LoadPath` per candidate, maturity `HYPOTHESIS → SPATIALLY_INSTANTIATED → AUTHORITATIVE` | `LoadPath`; `S03_CONTRACT.load_path_rule` |
| C-10 | per-element load components **derived, never stored** | `derived_not_stored`; ownership matrix `s03.may_not`; proposal §8 |
| C-11 | rule 6 rescoped to **reaction interfaces in a load path**; kinematic blocks need no load case | proposal §6 rule 6 |
| C-12 | `driver ∈ {LOAD, KINEMATIC_NECESSITY, DECLARED_SCENARIO}` | `blocked_by`; `S03_CONTRACT.blocking_relation_rule` |
| C-13 | termination by **round budget + repeated state**, not monotone reduction | `S06_CONTRACT.convergence_block.termination`; proposal §3 S06 |
| C-14 | loop scope: placements, dimensions, feature alternatives only; else escalate to S03 | `S06_CONTRACT.convergence_block.scope` |
| C-15 | a `Constraint` for **every declared clearance** | `S05_CONTRACT.clearance_constraint_rule`, check S05-C9 |
| C-16 | nested budgets K/N, escalation ladder, structured non-convergence | `S06_CONTRACT.convergence_block.budgets`, `.non_convergence` |

**Additionally aligned:** `MobilityExpectation` made total; `Joint` split into
s03 direction / s04·B located frame / s06 promotion; `Witness` gained
`SCOUT` fidelity with the raise-only rule and the laundering barrier;
`Candidate` gained `obligations_created` and `evidence_route_verdict`; `Scenario`
gained `kind`; `Requirement` gained `quantity_class`; the invalidation cone moved
onto `StagePatch`.

**Files changed.** `docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md` (revision 2);
`ver3/contracts/DESIGN_STATE_CONTRACT.yaml`;
`ver3/contracts/STAGE_PATCH_CONTRACT.yaml`;
`ver3/contracts/STAGE_OWNERSHIP_MATRIX.yaml`; **new**
`ver3/contracts/stages/S01–S07_CONTRACT.yaml` (seven files, each carrying the ten
required sections). All parse.

**Family count: 37**, plus `CompliantJoint` documented under its own key as a
constrained `Joint` variant — 38 keys, 37 families. No family was removed.

---

## 2. Remaining deferred debts

Nothing here blocks the start of implementation. Each is named with what would
discharge it.

| id | debt | discharged by |
|---|---|---|
| D-1 | The **sufficiency probes do not exist.** `STAGE_PROGRESSION_CONTRACT` step 6 mandates them. | Implementation order step 1 below |
| D-2 | **Oracle freeze ruling** on whether frozen `s05`/`s06` `stage_expectations` survive the convergence block. Both `must_exist` lists are satisfied at convergence, but the ruling is not mine. | A decision from whoever owns the Oracle freeze |
| D-3 | **LLM reliability for total DOF disposition** is unmeasured. The domain is enumerated mechanically and three of four dispositions are checkable; `IRRELEVANT_BECAUSE` is cross-checked against load cases. | Measure the overturn rate during S03 implementation |
| D-4 | **S04·A elimination rate** is unmeasured. If it eliminates few candidates, the S04·B cost problem returns. | Measure on the first three probe runs |
| D-5 | **No compliance route exists.** `allowable_travel` is permanently `UNSUPPORTED` until one does. | Out of scope; the hooks are in place |
| D-6 | **Nominal-only geometry.** No tolerance representation; "practical to manufacture" is permanently unevaluable. Declared at S02 rather than discovered at S11. | A separate decision about what the pipeline is for |
| D-7 | **BM-003's reference validation is uncompleted** and its working tree uncommitted; the remote diverged at the rejected proxy commit. Unrelated to this architecture, still open. | A user decision on commit and push |

---

## 3. Interface sufficiency results

Method: walk each boundary with BM-001, BM-002 and BM-003 as probes, asking
whether the consumer can do its job from the producer's structured output alone.
**All failures were collected before any correction was made**, then corrected in
one pass.

### Failures found

Three, all of one class: **a named consumer input with no declaring producer
field.**

| id | boundary | failure | correction applied |
|---|---|---|---|
| **B-1** | S02→S03 | `S03-C5` requires every `LoadCase` to have a path "terminating at a declared reaction site" — and **nothing declared the reaction site**. BM-002's path ends at "the support surface at z = 0"; nothing in the contracts said such a thing exists. | `LoadCase.reacted_at_role` — a role, so it stays candidate-independent |
| **B-2** | S04·B→S05 | S05's consumer list named **engagement sites** and no producer emitted them. An `Interface` at S03 is a symbolic meeting region; S05 needs its metric localisation to place features and anchor the ROI. | `Interface.engagement_site`, owned by S04·B; check S04B-C9 |
| **B-3** | S06→S07 | The **construction program's frame convention was unstated**. If world placement were in the program, S07 would need `State` — reopening the input contradiction the derived pose law closed. | `S05_CONTRACT.construction_frame_rule`: statements are in the body's own frame; world placement never appears in the program |

### Boundary results after correction

| boundary | BM-001 | BM-002 | BM-003 | verdict |
|---|---|---|---|---|
| S01→S02 | ✓ `quantity_class: NONE` on every requirement; TRANSPORT scenario now typed | ✓ BAND and MAGNITUDE carried without sharpening | ✓ all NONE, recorded as fact | **sufficient** |
| S02→S03 | ✓ retention obligation; compliance route flagged unavailable at S02, not S08 | ✓ payload + actor-applied load cases with `reacted_at_role` | ✓ magnitude-free disturbance load case | **sufficient** |
| S03→S04·A | ✓ scale declared free with a representative value | ✓ enclosure obligation; scale partly fixed by travel | ✓ scale declared free | **sufficient** |
| S04·A→S04·B | ✓ | ✓ | ✓ | **sufficient** |
| S03→S04·B | ✓ all three human-review findings surface as undispositioned DOF | ✓ platform rotational DOF force the guides | ✓ over-swing surfaces as an undispositioned DOF | **sufficient** |
| S04·B→S05 | ✓ access volume + deflected poses + engagement sites | ✓ swept occupancy refutes the rear-panel journal before features exist | ✓ heel sweep known before the stop pad is placed | **sufficient** |
| S05↔S06 | ✓ | ✓ arm envelope constrains axis height | ✓ ring seat derived, not chosen | **sufficient** |
| S06→S07 | ✓ | ✓ | ✓ | **sufficient** |
| S07→S08 | ✓ defeat specs from S03/S05 | ✓ | ✓ | **sufficient** |

**Previously weak boundaries, re-tested specifically.** S02→S03 now carries load
cases and evidence routes and fails only on B-1, now fixed. S04·B→S05 now carries
located frames, functional-region volumes and engagement sites. S07→downstream
carries defeat specifications, so S08 no longer invents controls from geometry.

---

## 4. Convergence-loop sanity result

Dry-reviewed against `S06_CONTRACT.convergence_block`.

| property | result |
|---|---|
| iteration is dependency-driven | **yes** — the cone is computed from each check's declared input set (S04B-C8) |
| escalation criteria explicit | **yes** — the scope list is closed: anything touching bodies, groups, joints, interaction kinds, DOF disposition, load paths or assembly order escalates to S03 |
| unchanged decisions preserved | **yes** — checks outside the cone are preserved, not recomputed. BM-002's three recorded *"travel 90.000000, unchanged"* results are the demonstration |
| stale checks identified by declared inputs | **yes** |
| repeated-state cycle detection possible | **yes** — state = (unsatisfied-constraint set, changed-parameter set) |
| round budget | **yes** — N rounds, K feature alternatives per unsatisfied constraint |
| non-convergence is structured | **yes** — `infeasible` with a conflicting set, or `underdetermined` with free directions, plus a `FailureProvenance`. Never a design |
| not a scheduler | **yes** — no agent-control architecture was introduced |

**Classification test against the record.** The scope rule reproduces the manual
severity judgements with no judgement required: BM-002 `CHG-01` iteration,
`CHG-03` iteration, `CHG-02` **escalation** (it required an overhung crank);
BM-003 R1 iteration, R4 iteration, R2 **escalation** (a stop pad realizes a
previously undispositioned DOF).

**The rejected rule stays rejected.** Monotone reduction of the unsatisfied set
would terminate BM-003 R1→R4 as `underdetermined` on a problem with a solution.

---

## 5. Progressive-commitment sanity result

| value / relation | PROPOSED | BOUNDED | PROVISIONAL | AUTHORITATIVE | SOLVED | VERIFIED |
|---|---|---|---|---|---|---|
| requirement | — | — | — | S01 | — | — |
| load case (applied) | S02 | S02 if magnitude-free | — | S02 | — | S09 |
| candidate | S02 | — | — | never — dies or is selected | — | — |
| topology (bodies, joints, interfaces) | S02 hypothesis | — | — | **S03** | — | S09 |
| DOF disposition | — | — | — | **S03** | — | S04·B |
| axis direction | — | — | — | **S03** | — | — |
| axis **placement** | — | — | **S04·B** | **S06** | S06 | S07 |
| load path | S03 hypothesis | — | S04·B instantiated | S06 | — | S09 |
| envelope / scale | — | **S04·A** | S04·A | S06 | S06 | S07 |
| poses, paths, swept volumes | — | — | — | **S04·B** | — | S09 |
| feature shape | S05 alternatives | — | — | S05 | — | S07 |
| feature dimension | — | — | S05 | — | **S06** | S07 |
| solids | — | — | — | — | — | **S07 / S09** |

Explicit checks the task required:

- **Mechanism alternatives survive until discriminating evidence exists.** ✓
  Candidates persist as branches; the gate sits after S04·A; a tie with no
  discriminating evidence is an `UnresolvedDecision`, never an arbitrary pick.
- **S03 does not invent metric axis placement.** ✓ `s03.may_not` now forbids it
  explicitly, citing `CHG-01`.
- **S04 may carry provisional placements.** ✓ Created `PROVISIONAL` at S04·B,
  promoted at S06.
- **S05 may propose embodiment alternatives.** ✓ Listed under
  `allowed_unresolved`, bounded by K.
- **S06 owns solved parameter values.** ✓ And S05 may not set a value except by
  citing a solver artifact.
- **S07 makes no engineering decision.** ✓ `owned_decisions.note`: it owns only
  facts about what compiled.

---

## 6. Exact implementation order

1. **Write the nine sufficiency probes** — one per row of §3's boundary table.
   Minimal consumers that attempt to construct the next stage's required inputs
   and report exactly what is missing. `STAGE_PROGRESSION_CONTRACT` step 6
   mandates them and they do not exist. *No stage implementation.*
2. **Hand-author S03 and S04·B outputs for the three existing CAD references and
   run the probes against them.** The references are the only ground truth in the
   repository; the CAD record says exactly what was needed. A probe that passes
   on an input missing something the CAD needed is a probe defect. *Highest value
   per unit of effort; still no stage implementation.*
3. **Resolve D-2** — the Oracle freeze ruling on `s05`/`s06`.
4. **Implement S01**, then **S02**. Cheap, low-risk, and needed as input to
   everything.
5. **Implement S03.** The stage carrying all the risk. Measure D-3 here.
6. **Implement S04·A**, measure D-4, then **S04·B**.
7. **Implement S06 as a solver service**, then **S05** against it, then close the
   convergence block.
8. **Implement S07.**

Steps 1–3 involve no stage code. If the architecture is wrong, step 2 finds it
before anything is built.

---

## 7. Final readiness verdict

**B — READY WITH SMALL DEFERRED DEBTS.**

Not A, because two debts are real and neither is merely documentary: the
sufficiency probes do not exist (D-1), and the Oracle freeze ruling (D-2) is a
governance dependency outside my authority. Two more (D-3, D-4) are unmeasured
quantities that implementation itself will settle.

Not C, because no architectural blocker remains. The three boundary failures
found in this pass were all one class — a consumer input with no declaring
producer field — and all three are corrected. The two fatal representational gaps
from the critical review (compliance, load) are closed and expressed in the
contracts. The convergence loop has a termination rule that survives replay
against the recorded history, which the previous one did not.

The bar was: *implementation can begin without immediately rediscovering a basic
boundary or representation contradiction.* Against the three benchmarks, replayed
boundary by boundary, that bar is met.

---

*Changed in this task: `docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md`;
`ver3/contracts/{DESIGN_STATE_CONTRACT,STAGE_PATCH_CONTRACT,STAGE_OWNERSHIP_MATRIX}.yaml`;
new `ver3/contracts/stages/S01–S07_CONTRACT.yaml`. No stage logic, and no CAD,
Oracle, simulation, benchmark or validation code.*
