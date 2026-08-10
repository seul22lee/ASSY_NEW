# IMPL S-5 — CANONICAL MOBILITY MIGRATION AND DOF DISPOSITION

Baseline of the correction pass: `6ccbe7d`. S-4 is frozen at `6e8bd59` and this
document does not revise its evidence.

---

## 0. STATUS OF THE EARLIER CLAIM

> **SUPERSEDED — `6ccbe7d` "S-5 COMPLETE — CANONICAL MOBILITY MIGRATION AND DOF
> DISPOSITION CLOSED": migration closed before all live producer, premise and
> contract paths were verified.**

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

## CURRENT STATUS

> **S-5 VERIFIED CLOSED — SINGLE CANONICAL MOBILITY PRODUCER AND PREMISE-BACKED
> DISPOSITION.**
>
> One live producer, declared by one responsibility, deriving inside its own
> invocation so every canonical caller sees the same state. Every positive
> disposition names a typed premise of the right family for its kind, resolved at
> the write boundary, applying to exactly the cell it declares.
> `MAINTAINED_BY_CLASS` is retired. Domain totality is BOOKKEEPING and disposition
> completeness is reported. `S03_CONTRACT` describes the live producer and no
> active S-5-owned migration row remains.
>
> S-4 is unchanged and verified so. **Impl S-6 has NOT begun.**
