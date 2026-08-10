# IMPL S-5 — CANONICAL MOBILITY MIGRATION AND DOF DISPOSITION

Baseline of the root-cause pass: `dc84dff`. S-4 is frozen at `6e8bd59` and this
document does not revise its evidence. Sections 0–11 record the correction pass
that ran on `6ccbe7d`; section 12 the pass on `9b22b0a`; section 13 the
root-cause pass, which carries the one CURRENT STATUS.

---

## 0. STATUS OF THE EARLIER CLAIMS

> **SUPERSEDED — `6ccbe7d` "S-5 COMPLETE — CANONICAL MOBILITY MIGRATION AND DOF
> DISPOSITION CLOSED": migration closed before all live producer, premise and
> contract paths were verified.**

> **SUPERSEDED — `9b22b0a` "S-5 VERIFIED CLOSED — SINGLE CANONICAL MOBILITY
> PRODUCER AND PREMISE-BACKED DISPOSITION": branch-scoped production and typed
> citations were complete, but branch-safe totality bookkeeping and
> dependency-premise propagation were not yet fully integrated.**
>
> What `9b22b0a` got right stands and is not re-argued: one producer, ownership
> inside the invocation, typed per-kind premises checked at the write boundary,
> `MAINTAINED_BY_CLASS` retired, declared-configuration applicability, contract
> and metadata aligned.

> **SUPERSEDED — `dc84dff` "S-5 VERIFIED CLOSED — BRANCH-SAFE BOOKKEEPING AND
> PREMISE DEPENDENCY INTEGRATED": each pass repaired one path to "current
> mobility" while the pipeline still reconstructed it through four that did not
> agree.**
>
> `dc84dff` made the domain branch-safe and made cited premises dependencies.
> Both stand. What it did not do was make the lifecycle one thing — section 13.

Kept, not erased. What that pass got right stands: the `MAINTAINED_BY_CLASS`-from-
absence branch is deleted, `UNDISPOSITIONED` exists and behaves, domain and
disposition are separate, the totality report is labelled BOOKKEEPING, and
`blocking_relations` left the prompt and the derivation.

What it did not do was verify the paths that were not in the function it rewrote:

| # | live at `6ccbe7d` | why it contradicted the claim |
|---|---|---|
| 1 | `S03TopologyAndMobility.to_operations` parsed `mobility` and `dof_dispositions` into `MobilityExpectation` | a second live producer, undocumented by any prompt; a recording in the old shape replayed through s03a still created `MAINTAINED_BY_CLASS` cells |
| 2 | `derived_operations` was called only by `tools/run_window2.py`, after `invoke` returned | a second canonical caller of `invoke` got a DesignState with no mobility and no sign any was missing |
| 3 | the disposition premise was a bare string inside `dispositions[]` | no boundary could see it; `premise_required: true` was a sentence, not a property |
| 4 | `MAINTAINED_BY_CLASS` remained in the live vocabulary | a legal disposition whose only evidence was a class STRING, which names no entity |
| 5 | a `ConstraintRelation` naming no configurations was expanded over ALL of them | absence read as the widest possible claim, in a branch nobody had looked at |
| 6 | `blocking_relation_check` read `blocker_body` | the derivation stopped emitting it at S-5, so the check reported every correct cell as incomplete |
| 7 | s03a's prompt still listed `disposition` and `driver`; its `purpose` claimed "a total DOF disposition"; its PERMITTED VALUES block was duplicated verbatim | the responsibility surface described the producer it had stopped being |
| 8 | `S03_CONTRACT` described `blocking_relations` as compatibility input the DOF expansion "still consumes" | production had migrated; the stage contract had not |
| 9 | `disposition_completeness()` was defined and called by nothing | a reported quantity that is not reported is not reported |

Rewriting the defective function is not the same act as removing every path that
reaches its output.

---

## 1. AUTHORITATIVE S-5 TARGET, RECONSTRUCTED FROM THE FROZEN FILES

Read in full before any edit: `S01_S04_ARCHITECTURE_FREEZE.md`,
`S01_S04_ARCHITECTURE_REVISION_PROPOSAL.md` §10, §11.1–11.3, §20.2,
`S01_S04_INTEGRATED_IMPLEMENTATION_PLAN.md` M-6, §11, §18, §19/U-6, §21 (S-5 row),
`S04_IMPLEMENTATION_EVIDENCE.md`, and the S-5 evidence at `6ccbe7d`.

| concept | frozen meaning | owner | authorship class | required premise | must not be inferred | downstream consumer |
|---|---|---|---|---|---|---|
| **DOF domain** | every rigid group × configuration × rigid-body DOF (§11.2) | s03b derivation | **B — deterministic**, reported **BOOKKEEPING** (freeze §8) | none; it is a product of the topology | that a cell's existence says anything about the design | `dof_totality_check`, disposition completeness |
| **MobilityExpectation** | two facts kept apart: which cells exist, and what is known about each | s03b | domain B; disposition A-or-strictly-derived | per disposition, below | that domain totality implies disposition completeness | s04b |
| **INTENDED** | "a joint of a known class leaves it free" (§11.2) | derivation | deterministic consequence | the authored **Joint** | freedom from the absence of a constraint | s04b motion |
| **BLOCKED_BY** (`CONSTRAINED` in the proposal) | "a `ConstraintRelation` covers it, **and the cell references it**" (§11.2) | derivation | deterministic consequence | the authored **ConstraintRelation**, by id | coverage of a configuration the relation does not name (§11.3) | s04b clearance |
| **IRRELEVANT_BECAUSE** | "unloaded and unactuated in a named scenario" — **authored**, then cross-checked against LoadCases | model authors; derivation places | authored | the named **Scenario** | irrelevance from the absence of a load | U-9 cross-premise check |
| **UNDISPOSITIONED** | "a DOF with none of the above … naming the cell and what is missing" (§11.2) | derivation | B | none — it is the statement that there is none | anything positive | reviewer; completeness quantity |
| **MAINTAINED_BY_CLASS** | **absent from every frozen enumeration.** §11.2 lists four outcomes; §20.2 option C is "dispositions derived from authored relations, remainder UNDISPOSITIONED"; plan §11.3 deletes the from-absence branch and plan §21 lists it under **REJECT** | — | — | none exists | that a class string is evidence | — |
| **ConstraintRelation** | addressable, one per *(retained group, direction or DOF set, configuration set)*, with a resolvable provider (§10) | s03b | A | — | a provider or a configuration set it does not declare | mobility, s04b |
| **Joint** | type, groups, DOF, axis direction (§ S03·A) | s03a | A | — | a configuration scope it does not have | mobility |
| **Scenario / LoadCase relevance** | irrelevance is checkable *because* the scenario is named and the load cases are independently authored | s01 / s02 | A | — | per-DOF load resolution — that is U-9 | U-9 |
| **disposition completeness** | "a separate, measurable engineering property: what fraction of the domain is dispositioned by evidence, and which cells are not" (§11.2) | derivation | reported quantity | — | that it is satisfied by totality | reviewer |
| **totality** | "trivially true … bookkeeping and is reported as such" (§11.2); freeze §8 BOOKKEEPING is "**never counted as assurance**" | derivation | BOOKKEEPING | — | that passing it establishes anything | dashboard |

**U-6 success criteria (plan §19), verbatim:** *"An absent mobility premise yields
`UNDISPOSITIONED`, never a class default. Every disposition cites a resolvable
premise. Disposition completeness is reported as a quantity, and the totality
report is labelled BOOKKEEPING."*

**Bound stated explicitly.** Plan §11 item 6 assigns *"cross-premise consistency
against load cases and actuation — a DOF marked irrelevant that a load case loads"*
to **U-9**, at PREMISE independence, and the assurance table names it *"where
mobility assurance actually lives"*. S-5 therefore owes: the scenario is named, it
resolves, the claim reaches exactly its own cell, and the bounded scenario-level
contradiction is reported. It does not owe a relevance theorem engine, and none was
built.

---

## 2. FILES READ

`docs/architecture/S01_S04_ARCHITECTURE_FREEZE.md` ·
`docs/architecture/S01_S04_ARCHITECTURE_REVISION_PROPOSAL.md` ·
`docs/implementation/S01_S04_INTEGRATED_IMPLEMENTATION_PLAN.md` ·
`docs/implementation/evidence/S04_IMPLEMENTATION_EVIDENCE.md` ·
this file at `6ccbe7d` ·
`ver3/assy_v3/stages/s03_topology_and_mobility.py` (all 1322 lines) ·
`ver3/assy_v3/stages/base.py` ·
`ver3/assy_v3/state/design_state.py` ·
`ver3/assy_v3/view/consumer_view.py` ·
`ver3/assy_v3/view/boundary.py` ·
`ver3/assy_v3/stages/s04_envelope_and_motion.py` (mobility consumer) ·
`ver3/tools/run_window2.py` ·
`ver3/contracts/DESIGN_STATE_CONTRACT.yaml` ·
`ver3/contracts/stages/S03_CONTRACT.yaml` (all 371 lines) ·
`ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml` (s03a, s03b) ·
`ver3/tests/meta/test_s5_mobility.py` · `test_s02_s03b_integration.py` · `_fixtures.py`

---

## 3. LIVE PRODUCER / CONSUMER GRAPH AT `6ccbe7d`

```
                      ┌─ s03a response  "mobility"[]         ─┐
                      │  s03a response  "dof_dispositions"[]  ├─► to_operations ─► MobilityExpectation   ◄── PRODUCER 2 (hidden)
                      │                                       │      (premise unexamined)
provider JSON ────────┤
                      │  s03b response  "constraint_relations"[] ─┐
                      └─ s03b response  "irrelevance"[]           ├─► derive_mobility ─► MobilityExpectation  ◄── PRODUCER 1
                                                                  │      called ONLY from run_window2:257,
                         state: RigidGroup / Configuration / Joint┘      in a patch of the runner's own

CONSUMERS   s04b completeness (defeat_specification)   ·  dof_totality_check
            blocking_relation_check (reads blocker_body — no longer emitted)
            irrelevance_check (scenario vs LoadCase)   ·  retention_check
COMPAT      relations_of / canonicalise_blocking / BLOCKING_ALIASES  (run_window2 counter)
```

**After the correction:**

```
provider JSON ── s03b ── to_operations ──────────► ConstraintRelation, PhysicalInteraction, …
                   │                                    (provenance s03b:relations)
                   └─ derived_operations ───────────► MobilityExpectation
                        premises: constraint_relations, irrelevance (response)
                                  RigidGroup/Configuration/Joint (THIS invocation's view)
                                    (provenance s03:derivation)
                   └──────────────► ONE patch, ONE write boundary, every caller

s03a ── to_operations ──► Body, RigidGroup, Joint, Interface, Configuration,
                          FunctionalRegion, LoadPath, AssemblyStep, UnresolvedDecision
                          — and no MobilityExpectation by any route
```

---

## 4. PRE-FLIGHT GAP TABLE

Verdict recorded before any production edit.

| # | issue | live behaviour at `6ccbe7d` | authoritative requirement | root cause | S-5 owned | general | correction | why minimal | surfaces | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | s03a hidden `mobility` | parses a compact per-DOF form into `MobilityExpectation` | FA-12 one owning stage; §20.2 option C | outlived its prompt; never revisited | **yes** | general | delete the branch | the family loses a producer; nothing else changes | s03a parser, s03a prompt, S03_CONTRACT | **GO** |
| 2 | s03a hidden `dof_dispositions` | same, long form | as above | as above | **yes** | general | delete the branch | as above | as above | **GO** |
| 3 | s03a prompt / responsibility residue | `disposition` and `driver` in PERMITTED VALUES; `purpose` claims a total DOF disposition; the whole block duplicated verbatim | freeze §6 — the model is not asked to disposition | prompt migrated piecemeal | **yes** | general | remove the vocabulary, the claim and the duplicate | prompt text is not frozen (freeze §1) | s03a PROMPT, `purpose`, module docstring | **GO** |
| 4 | canonical derivation | correct in substance | §11.2 | — | — | — | keep | — | — | **GO** |
| 5 | ownership | runner calls `derived_operations` after `invoke` | FA-3, FA-4; no frozen source defines a post-stage orchestration step | convenience at S-4 | **yes** | general | `Stage.derived_operations` hook, emitted into the stage's own patch | one hook, default empty; no stage but s03b changes | `base.Stage`, s03b, run_window2 | **GO** |
| 6 | INTENDED premise | `by_joint` is an unchecked string | §11.2 premise is the authored joint | premise never typed | **yes** | general | declare it a typed reference to `Joint` | one declaration, existing machinery | contract, write boundary | **GO** |
| 7 | BLOCKED_BY premise | `constraint_relation` is an unchecked string | §11.2 "the cell *references* it" | nested premise invisible to both boundaries | **yes** | general | `premise_record_list` with per-kind target families | one new field-semantic kind, reusing `reference` verbatim | contract, `design_state`, `consumer_view` | **GO** |
| 8 | IRRELEVANT_BECAUSE premise | `scenario` is an unchecked string, and no Source-A requirement declared that a Scenario had to be reachable | §11.2 authored, naming a scenario | same | **yes** | general | typed reference, `DESIGN_WIDE`; Source A derives the requirement | same declaration as 6 and 7 | contract, `consumer_view` | **GO** |
| 9 | MAINTAINED_BY_CLASS | legal, backed by a class string | absent from §11.2, §20.2, plan §11; plan §21 REJECT | enum kept because historical code used it | **yes** | general | **retire** from the live vocabulary, record why | deleting a value is smaller than inventing a premise type for it | contract, module, checks | **GO** |
| 10 | S03_CONTRACT | describes the pre-migration producer | current contract must describe current production | not updated with the code | **yes** | general | rewrite the mobility sections; reclassify | classification is structural, read by a test | S03_CONTRACT | **GO** |
| 11 | migration metadata | `legacy_producers.rows: []` while three live paths contradicted the closure | a row means the producer does not conform | closure declared too early | **yes** | general | record the correction as its own superseded row | history preserved, not rewritten | DESIGN_STATE_CONTRACT | **GO** |
| 12 | disposition completeness | function exists, no caller | §11.2 a reported quantity | never wired | **yes** | general | report it in the run record | one call | run_window2 | **GO** |
| 13 | S-4 / S-5 separation | `_s4_physical_problems == []`; overall `CONTRACT_INCOMPLETE` | S-4 closed at `6e8bd59` | — | no | — | leave untouched; assert it | — | — | **GO** |
| 14 | configuration applicability | `configs or configurations` — empty means everywhere | §11.3 "over the DOFs and configurations **it declares**" | found while tracing, not reported before | **yes** | general | expand over declared configurations only | one expression; the report already exists | derivation, s03b completeness, s03b prompt | **GO** |
| 15 | `blocking_relation_check` | reads `blocker_body`, which S-5 stopped emitting | a check must describe the live producer | check not migrated with the derivation | **yes** | general | read canonical fields; rename | same check, canonical fields | s03 checks, run_window2 | **GO** |

> **GO — the remaining S-5 defects are bounded and architecture-consistent.**

Two defects below were found **during** step 2's trace, not before it, and are
recorded as such rather than back-dated into the table above:

| # | defect | how it surfaced |
|---|---|---|
| 16 | `MEX-%04d` numbered from 1 per invocation | with the derivation inside `invoke`, the second candidate collided on `MEX-0001`. The id was the symptom; see 17 |
| 17 | the derivation read groups/configurations from **state** | so candidate B's domain contained candidate A's topology. A branch-scope error the runner-owned version could not expose, because the runner only ever derived what it was pointed at |

---

## 5. LOAD-BEARING CLAIMS

Each: authoritative rule · current implementation · negative falsifier · positive
proof · generality argument · status.

### 5.1 One live producer

**RULE.** FA-12: every entity family has exactly one owning stage. §20.2 selects
option C, in which dispositions come from authored relations.

**IMPLEMENTATION.** `S03TopologyAndMobility.to_operations` emits no
`MobilityExpectation` by any route; the two parses are deleted, not disabled.
`S03BMobilityAndAssembly.derived_operations` is the only producer, and
`STAGE_RESPONSIBILITY_CONTRACT.s03b.permitted_output_semantics` now declares it —
previously **no** responsibility did, so the family with two producers was declared
to have none.

**NEGATIVE.** `GEN-PROD-01/02/02b`: a legacy `mobility` payload and a legacy
`dof_dispositions` payload are fed to the real s03a parser; no
`MobilityExpectation` operation is produced and no `MAINTAINED_BY_CLASS` appears
anywhere in the operations. Behavioural, not a source scan.
**Mutation check:** restoring either branch fails 3 tests.

**POSITIVE.** `GEN-PROD-03` — the canonical path still produces the family.
`GEN-PROD-04` — exactly one responsibility declares it.

**GENERALITY.** Stated over the family and the parser, with no id, mechanism or
fixture. A future response key would have to be added to a parser to reintroduce
the defect, and `GEN-PROD-04` would not notice it — which is why the write boundary
(5.3) is the general guard, not this test.

**STATUS: IMPLEMENTED AND FALSIFIED.**

### 5.2 Ownership — the invocation derives, not the runner

**RULE.** FA-3/FA-4: class-B state is recomputable from its premises and enters
through the controlled mutation path. No frozen source defines a deterministic
post-stage orchestration step; the freeze's non-goals (§11) explicitly do not
design one. Plan M-6 records "called from `tools/run_window2.py:257`" as *current*
behaviour under migration, not as target.

**DECISION: option A — S03B's own invocation owns both the authored realization and
the derived grid.** `Stage.derived_operations(parsed, inputs, state)` is a general
hook, default empty, called by `Stage.run` so the derived operations land in the
same patch as the authored ones and pass the same write boundary. Authorship stays
distinguishable per operation: `s03b:relations` vs `s03:derivation`.

**NEGATIVE.** Deleting the hook call from `Stage.run` fails 7 tests
(`GEN-OWN-01`, `GEN-OWN-02`, `PROBE-01…07`).

**POSITIVE.** `test_S5_CHAIN_the_invocation_itself_produces_the_mobility` — `invoke`
alone yields the family, with the two provenance refs distinct.
`GEN-OWN-02` runs the chain twice and compares the resulting dispositions: **two
valid canonical callers cannot observe different DesignState.** That assertion could
not have been written at `6ccbe7d`.

**GENERALITY.** The hook names no stage. `run_window2` is now a caller like any
other and holds no piece of the derivation.

**STATUS: IMPLEMENTED AND FALSIFIED.**

### 5.3 The premise is typed, and checked where state changes

**RULE.** §11.2 — the cell *references* its relation. U-6 — every disposition cites
a **resolvable** premise. R-20 — a free-string subject is a SCHEMA ERROR.

**REPRESENTATION DECISION.** A single `premise_target: ConstraintRelation` cannot
represent the three dispositions honestly: a Joint, a ConstraintRelation and a
Scenario are three kinds of evidence for three different claims. Nor can a free-text
reason or an opaque blob, which fail criteria 1–4 outright. Chosen: **one premise
field per disposition kind, declared in the same vocabulary a top-level reference
uses**, under a new field-semantic kind:

```yaml
dispositions:
  kind: premise_record_list
  discriminator: disposition
  premise_field: {INTENDED: by_joint, BLOCKED_BY: constraint_relation,
                  IRRELEVANT_BECAUSE: scenario, UNDISPOSITIONED: null}
  record_field_semantics:
    by_joint:            {kind: reference, target: Joint,             cardinality: one, resolvable: false}
    constraint_relation: {kind: reference, target: ConstraintRelation, cardinality: one, resolvable: false}
    scenario:            {kind: reference, target: Scenario,           cardinality: one, resolvable: false,
                          referent_population: DESIGN_WIDE}
```

Against §9's eight criteria: **(1)** target family declared per field · **(2)**
existence enforced at the write boundary by the ordinary `resolvable` rule ·
**(3)** the discriminator constrains which premise field is permitted and forbids
another kind's · **(4)** a consumer reads two declared fields, never prose ·
**(5)** no benchmark semantics · **(6)** one authority — `_one_reference` is shared
verbatim by the flat and nested walks, so "does a reference resolve" has one answer
· **(7)** it reuses `field_semantics`, `reference_spec` and `_reference_problems`
· **(8)** no spatial concept appears.

**Tradeoff, stated.** A canonical reference *union* on one field would be smaller
still, but the contract machinery has no union and inventing one would let a
disposition cite any of the three kinds — which is exactly the type distinction
being introduced. Per-kind fields buy that distinction for one new declaration kind.
The cost is that the discriminator lives in the contract rather than in a type
system, so a new disposition value needs a `premise_field` entry; the write boundary
rejects any value that has none, so the failure mode is a refused patch, not a
silent gap.

**NEGATIVE**, all through `state.apply`, none through s03b:

| falsifier | what is refused |
|---|---|
| `GEN-PREM-02` | `constraint_relation: "CRL-GHOST"` → `DANGLING_REF` |
| `GEN-PREM-03` | `scenario: "the drawer is closed and nothing pushes it"` → `REFERENCE_NOT_AN_ID` (R-20) |
| `GEN-PREM-04` | `constraint_relation: "JNT-1"` → `REFERENCE_FAMILY` — a Joint is not evidence of a constraint |
| `GEN-PREM-05` | any positive disposition with no premise field → `PREMISE_MISSING` |
| `GEN-PREM-06` | `BLOCKED_BY` carrying `by_joint` as well → `PREMISE_WRONG_KIND` |
| `GEN-PREM-08` | `MAINTAINED_BY_CLASS` → `PREMISE_KIND_UNKNOWN` |

**Mutation check:** removing the nested walk from `_reference_problems` fails 6.

**POSITIVE.** `GEN-PREM-01` — a well-formed record of each of the four kinds is
accepted. `GEN-PREM-07` — `UNDISPOSITIONED` is the only legal way to hold no premise.
`PROBE-03` — in the canonical probe, every positive cell's premise resolves to its
own declared family, and **all three kinds occur**.

**GENERALITY.** `GEN-PREM-09` asserts the falsifiers do not go through s03b: the rule
binds the boundary, so it binds a producer written after this file.

**SOURCE A, measured rather than assumed.** The consumer boundary now flattens the
nested declarations, so `derive_source_a("s03b", …)` yields
`MobilityExpectation.dispositions.by_joint -> Joint` and `… .scenario -> Scenario`
where it previously yielded neither. What that changes is the DECLARATION: a state
holding no Scenario is now UPSTREAM INSUFFICIENCY rather than a claim s03b is asked
to author with nothing to name it from. It is **not** a fix to an observed omission —
checked directly, both scenarios already reached s03b's view by another route before
this change, so the canonical probe's view is unchanged by it. Stated this way
because the untested version of the claim ("the view may hold no Scenario") was a
hypothesis, and it turned out to be false.

**STATUS: IMPLEMENTED AND FALSIFIED.**

### 5.4 A premise disposes the cells it declares

**RULE.** §11.3 permits deterministic *"expansion of an authored relation over the
DOFs and configurations **it declares**"*. §11.1: absence of evidence is never a
premise.

**IMPLEMENTATION.** `for cfg in configs` — the relation's own list. A relation
declaring none covers no cell and `_s5_mobility_problems` reports it. A Joint is
treated differently and the difference is in the contract, not the code: a Joint has
no configuration field, so it is unconditioned by construction. Silence about a field
that exists is not the same fact as a field that does not.

**NEGATIVE.** `GEN-BLK-01/02/03` — a relation reaches only its own group, only its
own configurations, only its own DOFs. `GEN-BLK-04` — a fully well-formed relation
with every reference resolvable supports nothing at the wrong cell. `GEN-INT-03` — a
joint on another group supports nothing here. `GEN-UND-02` — unrelated premises
change nothing.
**Mutation check:** restoring `configs or configurations` fails
`S5-DISP-06`/`GEN-BLK-02`.

**POSITIVE.** `GEN-BLK-01`…`06`, `GEN-INT-01` (six joint classes, each freeing
exactly its own DOFs), `GEN-INT-04` (the cited joint is the one that frees that DOF),
`GEN-IRR-01/01b`.

**GENERALITY.** `GEN-INT-01` iterates the contract's joint classes rather than one;
`GEN-DOM-01` iterates 1×1, 2×3 and 4×2 topologies. No joint type, DOF or axis is
special-cased outside `free_dof`, which is ordinary kinematics.

**STATUS: IMPLEMENTED AND FALSIFIED.**

### 5.5 IRRELEVANT_BECAUSE, to the bound the architecture sets

**RULE.** §11.2 — authored, naming a scenario in which the DOF is unloaded and
unactuated, *"then cross-checked against LoadCases"*. Plan §11.6 and the assurance
table put the cross-premise check at **U-9**, PREMISE independence.

**IMPLEMENTATION.** Three separable things, and the evidence keeps them separate:
the claim reaches exactly its own `(group, configuration, DOF)` cell (derivation);
the scenario is a typed reference that must resolve (write boundary); a scenario
carrying a load case is contradicted (`irrelevance_check`, S03-C3, PROVENANCE
INTEGRITY).

**NEGATIVE.** `GEN-IRR-02` — two states differing **only** in which scenario the
claim rests on: the idle one passes, the loaded one yields
`IRRELEVANCE_CONTRADICTED`. `GEN-IRR-04` — a claim naming no scenario, group,
configuration or DOF is reported as reaching no cell. `GEN-PREM-03` — prose in the
scenario field is refused at the boundary.

**POSITIVE.** `GEN-IRR-01` — the authored claim disposes its own cell and carries the
scenario id. `PROBE-02` — it occurs in the canonical probe.

**WHAT IS NOT CLAIMED.** `GEN-IRR-03` records it plainly: a resolvable Scenario
carrying no load case **is** sufficient under the frozen bounded rule, and saying
otherwise would be inventing a rule the frozen sources do not state. Per-DOF load and
actuation resolution is U-9's ENGINEERING CONSEQUENCE check. No theorem engine was
built and none is implied.

**STATUS: IMPLEMENTED TO THE FROZEN BOUND; the cross-premise assurance is U-9's,
by citation.**

### 5.6 MAINTAINED_BY_CLASS is retired

**RULE.** Its evidence was `holding_class`, a **string**. U-6 requires a resolvable
premise; a string names no entity, so no premise type can exist for it. No frozen
source supplies one: §11.2 enumerates four outcomes and this is not among them,
§20.2's selected option ends "remainder UNDISPOSITIONED", plan §11.3 deletes the
branch, and plan §21 lists `MAINTAINED_BY_CLASS`-from-absence under **REJECT**.

**IMPLEMENTATION.** Removed from `disposition_values`; recorded under
`retired_disposition_values` with what it was, why it went, and where historical data
still holds it. `DISPOSITIONS` is now **read from the contract** rather than restated
in the module, so the two cannot drift again.

**NEGATIVE.** `GEN-PREM-08` — it cannot enter state. `GEN-UND-03` — exhaustive over
the shapes that used to trigger the else branch (no joints, a joint, a FIXED joint
with axis NONE): none produces it, and every value produced is in the live vocabulary.
`PROBE-04` — it appears nowhere in the probe's cells, nor does `holding_class` or
`blocker_body`.

**POSITIVE.** `test_MAINTAINED_BY_CLASS_is_retired_from_the_live_vocabulary`
asserts the retirement **and** that the record of why survives. A value deleted with
no record of why would be a different defect.

**STATUS: RETIRED.**

### 5.7 Domain is bookkeeping; completeness is the quantity

**RULE.** §11.2 and freeze §8 — BOOKKEEPING is "reported, **never counted as
assurance**".

**IMPLEMENTATION.** `dof_totality_check` says so in its own docstring; S03-C1 now
carries `claim_class: BOOKKEEPING` and a `never_assurance` note.
`disposition_completeness()` is **called** — `run_window2` records it per s03b run.
At `6ccbe7d` it had no caller at all.

**NEGATIVE.** `GEN-DOM-02` — adding a premise changes dispositions and not domain
size; the converse (removing evidence shrinking the domain) is
`test_S5_CHAIN_a_dof_without_disposition_stays_visible`.

**POSITIVE.** `GEN-DOM-01` — N×M×6, no duplicates, for three different topologies.
`GEN-UND-04` — completeness counts exactly the evidenced cells and names the rest.
`PROBE-07` — the probe's fraction is **below 1.0** and its uncovered cells are listed.

**STATUS: IMPLEMENTED AND FALSIFIED.**

### 5.8 S-4 is unchanged

**RULE.** S-4 closed at `6e8bd59`. `_s4_physical_problems(...) == []` is its physical
closure criterion.

**IMPLEMENTATION.** The method's logic is byte-for-byte unchanged; one stale sentence
in its docstring (pointing at "the legacy `blocking_relations` checks below", which no
longer exist) was corrected. `S5-S4-05` scans the method's **code** with
`_code_only()` — docstrings stripped — for U5-1/2/3 and for the absence of any
disposition reasoning.

**POSITIVE.** `S5-S4-01…04` and `PROBE-05`: `_s4_physical_problems == []` on both
chains, and the S-4 reference closure (`PEO-0001`, `RSR-0001`, `LC-0001.reacted_at_site`)
still holds.

**STATUS: FROZEN AND VERIFIED.**

---

## 6. CANONICAL INTEGRATION PROBE

`ver3/tests/meta/test_s5_generality.py::TestCanonicalProbe`. Benchmark-independent,
no product noun, nothing seeded that a producer should make — `MobilityExpectation`
in particular is never written by the test. It runs s02 → s03a → s03b through
`Stage.invoke`.

**Shape:** 2 rigid groups · 2 configurations · 1 REVOLUTE +Z joint (RGP-P → RGP-Q) ·
1 ConstraintRelation (RGP-Q, TZ, **CFG-1 only**) · 1 irrelevance claim (RGP-P /
CFG-2 / TX, in a scenario carrying no load case) · and cells nothing covers.

| assertion | result |
|---|---|
| domain deterministic and total | **24 cells** = 2 × 2 × 6, no duplicates |
| INTENDED where the joint applies | `RGP-QA/CFG-1A/RZ` cites `JNT-A` |
| BLOCKED_BY where the relation applies | `RGP-QA/CFG-1A/TZ` cites `CRL-A` |
| …and not where it does not | `RGP-QA/CFG-2A/TZ` is **UNDISPOSITIONED** |
| IRRELEVANT_BECAUSE where relevance logic permits | `RGP-PA/CFG-2A/TX` cites `SCN-IDLE` |
| UNDISPOSITIONED represents uncovered cells | 20 of 24 |
| every positive premise resolves to its own family | all three kinds occur; each `stored_family` matches |
| no legacy shape, no retired value | `MAINTAINED_BY_CLASS`, `holding_class`, `blocker_body`, `blocking_relation` all absent |
| `_s4_physical_problems` | **`[]`** |
| `_s5_mobility_problems` | **`[]`** |
| `constraint_disposition_check` / `irrelevance_check` / `dof_totality_check` | **`[]`** |
| `execution_status` | **`SUCCESS`** |
| `declared_incompleteness` | **`[]`** |
| disposition completeness | **4 / 24 ≈ 0.167**, 20 cells named |

**SUCCESS was not forced.** This probe authors an assembly step, which is why it does
not carry `'no assembly order'`; the earlier S-5 probe omitted them and correctly
reported it. `PROBE-07` asserts the completeness fraction is **strictly below 1.0** —
a probe of this size that reported full coverage would mean the migration had failed,
and the assertion is written so that outcome fails the test.

**Two candidates.** `GEN-BRANCH-01` — each candidate's dispositions contain no entity
id belonging to the other. `GEN-BRANCH-02` — one `PhysicalEffectObligation` and one
`ReactionSiteRequirement` serve both, four MobilityExpectations exist (`CFG-1A`,
`CFG-2A`, `CFG-1B`, `CFG-2B`), and each candidate has its full 24 cells. At `6ccbe7d`
the second candidate's mobility could not exist at all: the ids collided, and the
domain would have been built from both candidates' topology.

---

## 7. MIGRATION METADATA

`legacy_producers.rows` is `[]`, and the empty list is itself a claim: no producer is
known to be nonconforming. **Active S-5-owned rows: 0.**

`superseded_legacy_producers` gains a `why_it_took_two_passes` note on the mobility
row — recording that three live paths contradicted the first closure and that none was
in the function that was rewritten — and a new row, *MobilityExpectation premise typing
and producer singularity*, `closed_by: "S-5 correction"`, `residual: none`. The
ConstraintRelation row's residual no longer claims the DOF expansion consumes
`blocking_relations`, which stopped being true at `6ccbe7d`.

`S03_CONTRACT.authority_status`: `current_producer` and `blocking_relation_rule`
reclassified `LEGACY_PRODUCER` → **`RETIRED`**; `dof_disposition_rule`
`LEGACY_PRODUCER` → **`OPERATIONAL`**, because it now describes the live derivation
rather than a producer awaiting migration.

---

## 8. STATIC REVIEW OF THE FINAL TREE

| token | live production occurrences | classification |
|---|---|---|
| `mobility` | module name and prose; `derive_mobility`; `expected_mobility` (a Configuration field, s03a's) | PRODUCER / naming |
| `dof_dispositions` | one key in `legacy_shapes_in_recording` | S-9 CORPUS |
| `MobilityExpectation` | s03b derivation; four state-reading checks; s04b consumer; contract reads | PRODUCER / CONSUMER |
| `blocking_relations` | one key in `legacy_shapes_in_recording` | S-9 CORPUS |
| `relations_of`, `canonicalise_blocking`, `BLOCKING_ALIASES`, `BLOCKING_REQUIRED/OPTIONAL` | **none — deleted** | — |
| `MAINTAINED_BY_CLASS` | derivation docstring (what was removed); contract `retired_disposition_values`; retirement tests | HISTORICAL / TEST |
| `UNDISPOSITIONED` | derivation; completeness; contract | PRODUCER |
| `by_joint`, `constraint_relation`, `scenario` | derivation; contract declaration; `constraint_disposition_check`; `irrelevance_check` | PRODUCER / VALIDATOR |
| `blocker_body` | **none — deleted** (`provider_body` is canonical) | — |
| `blocking_relation_check` | **none — renamed `constraint_disposition_check`** | — |

Also verified across the changed files: no benchmark id, no candidate-name special
case, no model or vendor logic, no hard-coded joint or DOF case outside `free_dof`,
no prose→id repair, no synthetic premise invented to satisfy completeness, no S-6
spatial semantics, no S-4 reopening.

Two survivors are named rather than hidden. `legacy_shapes_in_recording` counts what a
recording holds of three retired shapes; it feeds no derivation, no check and no
state, and every caller writes into a run record. Counting is not a path. And
`_DISPOSITION_CODE`, the compact wire-code map, is gone with the parser that used it.

---

## 9. CLOSURE CRITERIA

| # | criterion | status | evidence |
|---|---|---|---|
| 1 | one canonical live producer path | ✅ | 5.1, `GEN-PROD-01…04` |
| 2 | s03a cannot author mobility through hidden fields | ✅ | `GEN-PROD-01/02/02b` (behavioural) |
| 3 | s03a prompt/responsibility drops the legacy claim | ✅ | §4 row 3 |
| 4 | DOF domain is deterministic bookkeeping | ✅ | 5.7, S03-C1 `claim_class` |
| 5 | domain independent of disposition coverage | ✅ | `GEN-DOM-02`, chain variant |
| 6 | no absence path creates positive meaning | ✅ | `GEN-UND-01/02/03` |
| 7 | uncovered cells are explicit UNDISPOSITIONED | ✅ | `GEN-UND-01`, `PROBE-02` |
| 8 | every positive disposition has a machine-checkable sufficient premise | ✅ | 5.3, write boundary |
| 9 | premise type matches disposition kind | ✅ | `GEN-PREM-04/06/08` |
| 10 | premise applies to the exact cell | ✅ | 5.4, `GEN-BLK-01…04`, `GEN-INT-03` |
| 11 | BLOCKED_BY uses canonical ConstraintRelation only | ✅ | `GEN-PREM-04`, `GEN-BLK-05` |
| 12 | IRRELEVANT_BECAUSE satisfies the bounded frozen rule | ✅ | 5.5; the bound stated, U-9 cited |
| 13 | MAINTAINED_BY_CLASS retired or premise-backed | ✅ | **retired**, 5.6 |
| 14 | disposition completeness separately reported | ✅ | `run_window2` records it; `GEN-UND-04` |
| 15 | totality is BOOKKEEPING | ✅ | docstring, S03-C1, freeze §8 |
| 16 | S03_CONTRACT describes current production | ✅ | §7 |
| 17 | active migration metadata describes current truth | ✅ | §7 |
| 18 | zero active S-5-owned migration rows | ✅ | `S5-META-01` |
| 19 | S-4 physical semantics unchanged | ✅ | 5.8 |
| 20 | no S-6 spatial semantics introduced | ✅ | §8 |
| 21 | generality falsifiers pass for changed relationships | ✅ | `test_s5_generality.py`, 36 cases |
| 22 | canonical ownership guarantees every caller the same truth | ✅ | 5.2, `GEN-OWN-02` |

---

## 10. WHAT IS NOT S-5's, WITH ITS OWNER

| residual | owner | authority |
|---|---|---|
| per-DOF load / actuation cross-premise consistency for IRRELEVANT_BECAUSE, at PREMISE independence | **U-9** | plan §11.6; assurance table "where mobility assurance actually lives" |
| two authored premises reaching one cell (a relation and a joint) — resolved by declared precedence, not adjudicated | **U-9** | cross-premise consistency is U-9's; the precedence rule is stated in `derive_mobility` rather than left silent |
| relocating S03 checks out of the stage module | **U-9 / M-9** | plan M-9 "no check is reachable from a stage module" |
| `Envelope`, frames, axes, `ReferenceScale`, S04A→S04B continuity | **S-6 / U-7** | plan M-8 |
| selection, commitment, both gate poles | **S-7 / U-8** | plan M-5B |
| 21 stale recordings in retired shapes; full-chain live validation | **S-9** | plan §18 F |

No S-5-owned residual was moved to a later step.

---

## 11. REGRESSION — SECONDARY EVIDENCE ONLY

Reported after the semantic verification above, never as a substitute for it.

```
RUN 794   PASS 794   FAIL 0   ERROR 0   SKIP 22
```

Mutation checks, which are the ones that matter: five deliberate reversions of this
pass's production changes were each caught — restoring the s03a legacy parse (3
failures), deriving from state instead of the branch-scoped view (2 errors), removing
the premise-record walk from the write boundary (6 failures), removing the
`derived_operations` hook from `Stage.run` (7), and restoring
`configs or configurations` (1).

---

## 12. THE FINAL PASS — BRANCH-SAFE BOOKKEEPING AND PREMISE DEPENDENCY

Baseline `9b22b0a`. Two integration gaps, both reproduced behaviourally on the
real path before a line of production changed. Neither is new mobility meaning;
both are already-frozen S-5 semantics that stopped at the edge of a neighbouring
substrate.

### 12.1 What the two gaps have in common

`9b22b0a` made **production** branch-scoped and made the disposition premise a
**typed citation**. Each stopped one step short of the thing it was for:

| | `9b22b0a` had | it did not have |
|---|---|---|
| **A** | a branch-scoped PRODUCER — s03b derives from its own view | a branch-scoped BOOKKEEPING CHECKER — `dof_totality_check` still took the design-wide Cartesian product |
| **B** | a typed CITATION — right family, referent resolves, checked at the write boundary | a DEPENDENCY — nothing reached `Op.premise_refs`, so `_propagate` never saw it |

A citation says *where this claim came from*. A dependency says *this claim falls
if that one does*. They are related and they are not the same fact, which is
exactly how one could be finished while the other was not.

### 12.2 Issue A — reproduced before repair

Two candidates, deliberately **unequal** — A: 2 groups × 2 configurations;
B: 1 group × 3 configurations — built through s02 → s03a → s03b with real
`invoke` calls:

```
branch A owns                        24 cells
branch B owns                        18 cells
expected branch-union cell count     42
actual existing cell count           42        <- production is correct
checker-implied Cartesian count      3 groups x 5 configs x 6 = 90
dof_totality_check findings          13   (48 missing cells, capped at 12 + a tail)
representative FALSE missing cells:
    DOF_NOT_DISPOSITIONED: RGP-G0A in CFG-C0B: TX
    DOF_NOT_DISPOSITIONED: RGP-G0A in CFG-C0B: TY
    ...
    DOF_NOT_DISPOSITIONED: and 36 more
```

`RGP-G0A in CFG-C0B` is candidate A's group in candidate B's configuration — a
pair no mechanism contains and no producer could ever disposition. **Nothing was
wrong with the design; the checker was measuring a domain production never had.**

### 12.3 Issue A — the correction, and why it is general

`accumulated_dof_domain(state)`: a cell exists when its group and its
configuration **belong to a common branch**, or when neither belongs to any.
The second clause is the unbranched design, where behaviour is exactly what it
was — which is why `A-TOTAL-01` passes unchanged rather than by special case.

Branch membership comes from `consumer_view.branch_membership`, which is
`_reachable(entity, depends-on graph, standing candidates)` — **the same
computation `scope_of` uses to decide ACTIVE_BRANCH**, now factored into
`branches_built_on` and called from both. There is no second branch ontology, no
candidate-id parsing, no naming convention and no count: the rule is stated over
the depends-on graph the S-3 lineage substrate already builds from declared
references and recorded premises.

`A-TOTAL-10` pins that equivalence: for each of three entities,
`branch_membership` and `scope_of` agree on which branch it belongs to and which
it does not.

### 12.4 Issue A — falsifiers

| case | what it falsifies |
|---|---|
| `A-TOTAL-01` | one candidate: domain 24, no findings — the correction is not a multi-candidate special case |
| `A-TOTAL-02` | two equal branches: no findings, domain 48 |
| `A-TOTAL-03` | **unequal** 2×2 and 1×3: domain 42, and explicitly ≠ 90, the design-wide product |
| `A-TOTAL-04` | adding candidate B leaves candidate A's domain and cells identical |
| `A-TOTAL-05` | three branches (2×2, 1×3, 3×1): domain 60 = the union of three |
| `A-TOTAL-06` | **a real omission is still caught.** One cell removed from candidate A by a real `SUPERSEDE`; the checker returns exactly one finding naming that group, configuration and DOF |
| `A-TOTAL-07` | no cross-branch pair is in the domain, and none is demanded |
| `A-TOTAL-08` | the dual: a cross-branch cell that EXISTS is now `DOF_DISPOSITION_OUT_OF_DOMAIN` — the old flat membership test could not see it |
| `A-TOTAL-09` | it is still BOOKKEEPING: the docstring says so and S03-C1 carries `claim_class: BOOKKEEPING` |
| `A-TOTAL-10` | branch membership is the ConsumerView's relation, not a second one |

`A-TOTAL-06` is the one that matters, and a mutation proves it is doing work:
replacing the domain with "whatever was produced" — the self-fulfilling checker —
makes `A-TOTAL-06` and `A-TOTAL-08` fail. Branch-safe did not become blind.

### 12.5 Issue B — reproduced before repair

Smallest real case, one candidate, through `invoke`:

```
MEX id                    MEX-CFG-C0A
premises CITED in cells   ['CRL-A', 'JNT-A', 'SCN-IDLE']
stored _premises          ['CND-A']            <- only the invocation premise
   CRL-A     in _premises?  False
   JNT-A     in _premises?  False
   SCN-IDLE  in _premises?  False

after INVALIDATE CRL-A (a USED premise, through the real controlled operation):
   CRL-A _validity         INVALIDATED
   MEX   _validity         STANDING            <- FA-5 did not fire
   MEX still cites CRL-A   True
```

The design went on asserting that a DOF was held by a relation it had withdrawn.

### 12.6 Issue B — the correction, and why it is general

`cited_premises(rows)` collects the premises from the **rows that were actually
produced**, through the contract's own `disposition → premise-field` map, and
`derived_operations` passes them as `Op.premise_refs`. Nothing else changed:
`_create` stores them, `_propagate` reads them, `SUPERSEDE`/`INVALIDATE` fire.
**No second provenance system** — `B-PREM-12` asserts the derivation still uses
`premise_refs` and `carry_invocation_premises`.

Three properties follow mechanically from reading the produced rows, and none is
coded as a case:

- **used, not visible.** The premise enters because a cell cites it. An entity
  the consumer view held and no cell used is not a dependency — availability is
  not a claim.
- **UNDISPOSITIONED contributes nothing.** It maps to no premise field. An honest
  statement that nothing is known cannot depend on anything.
- **the set is a set.** A premise cited by many cells appears once; FA-5 asks
  whether this value rests on that one, not how often.

`B-PREM-11` holds the generality: `cited_premises` reads `PREMISE_FIELD` and
names no disposition value and no field, so a new disposition kind needs no edit
here.

### 12.7 Issue B — falsifiers

| case | result |
|---|---|
| `B-PREM-01` | `CRL-0A` is cited **and** in `_premises` |
| `B-PREM-02` | INVALIDATE a used relation → dependent MobilityExpectation **STALE** |
| `B-PREM-03` | INVALIDATE another branch's relation → this one **STANDING**, that one STALE |
| `B-PREM-04` | `JNT-A` enters the dependency set |
| `B-PREM-05` | **SUPERSEDE** the joint (not only INVALIDATE) → STALE. Both are premise changes under FA-5 |
| `B-PREM-06` | an unrelated joint → no effect |
| `B-PREM-07` | one joint + three relations + one scenario: the set is exactly the five used, plus the invocation premise `CND-A` |
| `B-PREM-08` | UNDISPOSITIONED cells yield `[]` — no fabricated premise |
| `B-PREM-09` | the same premise in three cells appears once |
| `B-PREM-10` | `SCN-IDLE` is **visible in the view** and unused: it is not in `_premises` |
| `B-PREM-11` | the collector reads the contract map, naming no kind and no field |
| `B-PREM-12` | the existing substrate is used, not duplicated |

`B-PREM-10` is the generality case: visibility is not dependency, proved by
asserting the entity is in the view payload and absent from the premise set.

### 12.8 IRRELEVANT_BECAUSE — the bound is unchanged

The Scenario the S-5 derivation actually uses is attached as a dependency, so
withdrawing it costs the mobility its standing. That is reference-and-dependency
correctness. It proves nothing about broader engineering irrelevance, and the
per-DOF load/actuation check remains **U-9's** exactly as before. No relevance
engine was built and none was extended.

### 12.9 Closure probe

Three branches of three shapes — 2×2, 1×3, 3×1 — two constraint relations each,
through the real `invoke`, nothing seeded:

| assertion | result |
|---|---|
| branch-local domains | 24 / 18 / 18 cells, each complete |
| accumulated domain | **60** = (4 + 3 + 3) × 6, the branch union |
| `dof_totality_check` | **`[]`** — no cross-branch false cells |
| all four disposition kinds occur | INTENDED, BLOCKED_BY, IRRELEVANT_BECAUSE, UNDISPOSITIONED |
| every positive premise resolves to its declared family | ✅ |
| every MEX's `_premises` ⊇ its cited premises | ✅ |
| INVALIDATE `CRL-0A` | `MEX-CFG-C0A` **STALE**; `MEX-CFG-C0B`, `MEX-CFG-C0C` **STANDING** |
| `_s4_physical_problems` per branch | **`[]`** |
| `_s5_mobility_problems` per branch | **`[]`** |
| `execution_status` per branch | **`SUCCESS`**, `declared_incompleteness []` |
| producer singularity | every MEX op is `s03:derivation`; a legacy s03a payload still produces none |

### 12.10 Contract corrections

Only what production would otherwise contradict. `MobilityExpectation.authorship_split.domain.meaning`
now says the domain is one branch's and the accumulated domain is the union;
`.disposition` gains a `dependency` line saying the cited premises are also the
operation's premise refs — **derived from the citations, not a second canonical
field**. `S03_CONTRACT.dof_disposition_rule.domain` and S03-C1's text say
"of its own branch"; `.disposition` says the premise is also a dependency and why.
No new family, no new field, no vocabulary change.

### 12.11 Static review

| surface | relationship after this pass |
|---|---|
| `dof_domain(groups, configs)` | ONE branch's domain. Used by `accumulated_dof_domain` |
| `accumulated_dof_domain(state)` | the union of the branches' domains. The only domain a state-wide reader uses |
| `dof_totality_check` | BOOKKEEPING over `accumulated_dof_domain` |
| `branch_membership` / `branches_built_on` | the one branch relation, shared with `scope_of` |
| `cited_premises` | rows → the premises they used, via `PREMISE_FIELD` |
| `premise_refs` → `_premises` | the existing substrate, populated; `_propagate` unchanged |
| `by_joint` / `constraint_relation` / `scenario` | typed citations at the write boundary AND dependency inputs |
| `UNDISPOSITIONED` | no premise field, therefore no dependency |
| `MobilityExpectation` | one producer, `s03:derivation`, inside s03b's invocation |

Verified absent from the diff: candidate-name special cases, branch-suffix logic,
benchmark or mechanism ids, a second branch or premise authority, a new provenance
subsystem, fabricated premises for UNDISPOSITIONED, view material admitted as
premise without use, S-4 semantic change, S-6 spatial work, U-9 assurance.

### 12.12 Regression — SECONDARY EVIDENCE ONLY

```
RUN 821   PASS 821   FAIL 0   ERROR 0   SKIP 22
```

The evidence that carries weight is the four mutations, each caught: restoring the
design-wide Cartesian domain (7 failures), replacing the domain with what was
produced (2 — `A-TOTAL-06`/`08`, proving the checker still sees a real omission),
dropping `premise_refs` from the derived operations (8), and collecting every
premise-shaped field instead of the used one (1 — `B-PREM-10`).

---

## 13. THE ROOT-CAUSE PASS — ONE MOBILITY LIFECYCLE

Baseline `dc84dff`.

### 13.1 Root cause, reproduced before editing

Four passes each repaired one surface and the next one surfaced, because the
architecture's A/B split had never been made operational as **one lifecycle**.
Four disagreeing reconstructions of "current mobility" coexisted:

**A — what the contract declares.** `authorship_split.domain.authority_class:
DERIVED`, `.disposition.authority_class: AUTHORITATIVE`.

**B — what runtime enforces.**

```
Contracts().authority_class('MobilityExpectation')  ->  AUTHORITATIVE
family-level `authority_class` declared?            ->  False   (defaulted)
authority.class_overrides                           ->  {}
field_semantics carrying authority_class            ->  []
```

Authority is **family-level**. The field-level split existed only as prose. The
contract's own note said so: *"Empty at S-1. Populating it — in particular
splitting MobilityExpectation into a derived domain and an authored disposition —
is U-6/M-6"*. U-6 is this step; it had not been done.

**C — a domain-defining premise withdrawn.** Two branches, 2×2 and 1×3, then
`INVALIDATE RigidGroup RGP-G1A`:

```
RGP-G1A _validity                INVALIDATED
still in accumulated domain?     True          <- history defined the domain
domain cell count                42            (unchanged)
dof_totality_check               []            (silent)
MEX-CFG-C0A  _validity=STANDING  holds RGP-G1A  _premises=[CND-A, CRL-0A, JNT-A, SCN-IDLE]
MEX-CFG-C1A  _validity=STANDING  holds RGP-G1A  _premises=[CND-A, JNT-A]
```

The grids went on describing the mobility of a group the design had dropped, and
nothing said so — **the topology a grid addresses was not among its premises**.

**D — two currentness rules in one pipeline.**

```
ConsumerView RigidGroup            ['RGP-G0A']            standing only
accumulated_dof_domain groups      ['RGP-G0A','RGP-G1A']  all history

accumulated_dof_domain          family()=2  standing()=0
dof_totality_check              family()=3  standing()=0
constraint_disposition_check    family()=3  standing()=0
irrelevance_check               family()=3  standing()=0
branch_membership               family()=0  standing()=1
```

The producer had always been standing-only. Everything downstream of it was not.

### 13.2 Representation decision

The frozen sources permit §3's preferred interpretation, so it is what was
implemented:

> **MobilityExpectation is the authoritative disposition container. The DOF
> domain is not a second stored truth — it is a Class-B computation over standing
> branch topology.**

Authority: proposal §11.2 makes domain enumeration deterministic and disposition
the authored act; freeze §5 says class B is *"recomputable from premises"*; FA-2
requires every value to belong to **exactly one** class, which a stored domain
inside an AUTHORITATIVE family violates.

So the mismatch was removed by **removing the false claim**, not by inventing
per-field authority metadata runtime ignores — which §3 explicitly forbids:

- `MobilityExpectation.authority_class: AUTHORITATIVE`, **declared** on the
  family rather than defaulted, because what it stores is dispositions;
- `authorship_split.domain` gains `stored: false`, `computed_by:
  current_dof_domain`, `recomputed_from: [standing RigidGroup, standing
  Configuration, branch membership]`, and a `currentness` clause;
- `dispositions` declares `cell_address: [rigid_group, configuration, dof]` — the
  **address** of the derived cell a claim is about, asserting nothing about its
  existence;
- `class_overrides_note` records the resolution: no override is needed, because
  the table maps a family to a class and the derived half is not stored.

`AUDIT-10` asserts all of it, including that **no field declares an
`authority_class` runtime does not read**. `AUDIT-10b` proves the class-B claim
behaviourally: topology changes, the stored grids are byte-identical, and the
domain follows — so it is recomputed, not read back.

### 13.3 Canonical current-domain definition

```
dof_domain(groups, configurations)      THE enumerator. One branch.
current_dof_domain(state)               THE current answer:
    standing RigidGroup
  × standing Configuration
  restricted to a COMMON BRANCH (branch_membership — the ConsumerView's relation)
  ∪ over branches
  → dof_domain applied per branch
```

The producer applies `dof_domain` to its invocation's view; every current reader
applies it through `current_dof_domain`. `AUDIT-1` asserts the enumeration
expression exists **once** in the module; `AUDIT-9` asserts producer and checker
agree cell for cell, per branch.

`current_mobility_cells(state)` is the coverage side: rows from **standing**
grids only.

### 13.4 Dependency definition

```
premise_refs(MEX) =
      {candidate}                                   invocation premise
    ∪ {configuration} ∪ {rigid groups its rows address}      DOMAIN-DEFINING
    ∪ {premises its rows actually cite}                      DISPOSITION
```

Two halves with different consequences, and that is the point of separating them:
withdraw a **domain** premise and the cells stop being in the current domain, so
the grid loses standing with them; withdraw a **disposition** premise and the
cells remain while the claim about them loses authority. `AUDIT-7/8` asserts each
half produces its own consequence and not the other's.

Both are read mechanically off the produced rows. `AUDIT-5/6` asserts the stored
set is exactly domain ∪ cited ∪ the invocation premise — **nothing else** — and
that every premise resolves. `AUDIT-6b`: an UNDISPOSITIONED cell contributes no
engineering premise and still carries its domain premises, because *existence*
and *evidence* are different claims.

### 13.5 Lifecycle falsifiers

| | case | result |
|---|---|---|
| **L1** | clean current branch | current domain (24) **==** produced mobility domain, `dof_totality_check []` |
| **L2** | three unequal branches 2×2, 1×3, 3×1 | domain 60 = union; equals what was produced |
| **L3** | INVALIDATE `RigidGroup` | leaves the domain (42→30); **both** grids of that branch STALE; other branch unchanged in domain and validity |
| **L3b** | — | the withdrawn group is no longer demanded; the branch's *surviving* group is reported as uncovered, which is a real gap, not a false one |
| **L4** | SUPERSEDE `Configuration` | stays in the domain — FA-1 retains both values and the entity keeps standing — and the dependent grid goes **STALE** |
| **L4b** | INVALIDATE `Configuration` | leaves the domain; dependent grid STALE; other branch untouched |
| **L5** | INVALIDATE used `Joint` | domain **unchanged**; affected grid STALE |
| **L6** | INVALIDATE used `ConstraintRelation` | domain unchanged; affected grid STALE |
| **L6b** | INVALIDATE the bounded `Scenario` premise | domain unchanged; affected grid STALE |
| **L7** | INVALIDATE another branch's relation and joint | this branch's domain and validity untouched |
| **L8** | a stale grid exists | it is **not** current coverage, and the coverage it used to provide is reported as missing |
| **L9** | a genuine current cell removed | exactly one finding, naming that group, configuration and DOF |
| **L10** | an artificial cross-branch cell | `DOF_DISPOSITION_OUT_OF_DOMAIN` |
| **L11** | INVALIDATE the `Candidate` | that branch's topology and mobility stop contributing — via the invocation premise every s03 record already carried — and the other branch is untouched, domain and checks quiet |

**L4 is reported as the substrate defines it, not as the brief phrased it.**
`SUPERSEDE` replaces a value and retains both (FA-1); it does not withdraw the
entity, so a superseded configuration is still part of the mechanism. What it is
is a *premise change*, so the dependent grid stales. `INVALIDATE` is the
operation that removes it, and `L4b` covers that. Forcing "superseded
configuration leaves the domain" would have meant deleting an entity the
architecture says is retained.

### 13.6 Generality

No case names a candidate, parses an id, or depends on a count: branch shapes are
parameters (2×2, 1×3, 3×1), branch membership is `_reachable` over the depends-on
graph, and the premise halves are read off produced rows through the contract's
own map. Nothing in production reads an id suffix. The key property — *changing
any premise of candidate A's current mobility affects exactly A* — is L3, L7 and
L11 from both directions.

### 13.7 Files changed

`ver3/assy_v3/stages/s03_topology_and_mobility.py` ·
`ver3/tools/run_window2.py` ·
`ver3/contracts/DESIGN_STATE_CONTRACT.yaml` ·
`ver3/contracts/stages/S03_CONTRACT.yaml` ·
`ver3/tests/meta/test_s5_lifecycle.py` (new, 25 cases) ·
`ver3/tests/meta/test_s5_branch_and_premise.py` ·
this file.

### 13.8 The ten audit questions

| | question | answer |
|---|---|---|
| 1 | exactly one executable definition of the current DOF domain? | **YES** — `AUDIT-1`, one enumeration expression in the module |
| 2 | standing branch topology only? | **YES** — `AUDIT-2` |
| 3 | can historical topology enlarge the current domain? | **NO** — `AUDIT-3`, history retained and excluded |
| 4 | can a stale grid satisfy current totality? | **NO** — `AUDIT-4`, `L8` |
| 5 | every grid carries all domain-defining dependencies? | **YES** — `AUDIT-5/6` |
| 6 | only actually-used disposition premises? | **YES** — `AUDIT-5/6`, `AUDIT-6b`, `B-PREM-10` |
| 7 | a domain premise change moves exactly the affected mobility? | **YES** — `L3`, `L4b`, `L11`, `AUDIT-7/8` |
| 8 | a disposition premise change stales without moving the domain? | **YES** — `L5`, `L6`, `L6b`, `AUDIT-7/8` |
| 9 | producer and checker over the same current domain? | **YES** — `AUDIT-9`, per branch, cell for cell |
| 10 | executable authority matches the contract's A/B distinction? | **YES** — `AUDIT-10`, `AUDIT-10b` |

### 13.9 Preserved

`_s4_physical_problems` and U5-1/2/3 unchanged and verified empty; one S03B
producer; `UNDISPOSITIONED` semantics; `MAINTAINED_BY_CLASS` retired; typed
disposition premises; the canonical branch relation. No S-6 work, no U-9
assurance, no recording regeneration.

### 13.10 Remaining S-5-owned blockers

**None.** Deferred with owners, unchanged: per-DOF load/actuation cross-premise
consistency and assurance relocation → **U-9**; spatial → **S-6**; selection →
**S-7**; corpus refresh → **S-9**.

### 13.11 Regression — SECONDARY EVIDENCE ONLY

```
RUN 846   PASS 846   FAIL 0   ERROR 0   SKIP 22
```

The evidence that carries weight is the four mutations, each caught: computing
the domain over all history (7 failures), counting stale grids as current
coverage (4), dropping the domain half of the dependency (5), and reducing the
domain premises to the configuration alone (3).

---

## CURRENT STATUS

> **S-5 VERIFIED CLOSED — MOBILITY AUTHORITY, DOMAIN, DEPENDENCY AND VALIDITY
> LIFECYCLE CONSISTENT.**
>
> One executable definition of which mobility cells currently exist, computed
> from standing branch topology and stored nowhere, shared by the producer and
> every current reader. MobilityExpectation is the authoritative disposition
> container and says so in a declaration runtime enforces; its cell coordinates
> address derived cells and assert nothing about their existence. Every grid
> depends on both the topology whose cells it addresses and the premises its
> dispositions cite, so a domain premise moves the cells and a disposition
> premise moves only the claim. Withdrawn topology neither enlarges the domain
> nor satisfies it, and history stays readable throughout.
>
> S-4 is unchanged and verified so. **Impl S-6 has NOT begun.**
