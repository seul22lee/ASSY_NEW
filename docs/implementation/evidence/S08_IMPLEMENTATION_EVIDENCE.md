# S-8 / U-9 — INDEPENDENT ASSURANCE AND STATUS SEMANTICS

Baseline `237b1ba`. This is migration unit **U-9 / M-9**, not pipeline stage
`s08`. Nothing here plans verification, executes evidence, or touches S05+.

The defect being removed is one sentence long: **the pipeline currently grades
itself with the code that produced the answer, and reports the result on one
axis that mixes four different questions.** Every check lives in the module of
the stage it judges; two of them test properties that module guarantees by
construction; the dashboard turns any finding into a downgraded execution badge;
and a single unweighted `maturity_index` averages contract completeness,
evidence maturity and engineering care into one number.

---

## A. THE THREE OPEN CHOICES, RESOLVED BEFORE IMPLEMENTATION

### A1 — machine-readable assurance metadata

Frozen runtime identifiers. SCREAMING_SNAKE strings, the repository's
serialization convention for every other status vocabulary, so a value is the
same token in code, in a report and in a contract.

**Independence degree** — how far the checker stands from the writer:

| identifier | meaning | why it is not enough on its own |
|---|---|---|
| `STRUCTURAL` | the checker reads the same declaration the writer wrote to | writer and checker share the rule, so agreement is partly guaranteed |
| `PREMISE` | the checker compares two premises authored by DIFFERENT producing stages | neither author could have made the other agree |
| `EXTERNAL` | the precondition is recomputed from committed state by a reader that is not the actor being judged | the gate does not get to report that it fired correctly |

**Claim class** — what a passing result is entitled to assert:

| identifier | asserts | may establish? |
|---|---|---|
| `BOOKKEEPING` | a count, a coverage, an enumeration completed | never |
| `FIDELITY` | a value survived transport between stages unchanged | never |
| `PROVENANCE_INTEGRITY` | every claim traces to a resolvable premise | never |
| `ENGINEERING_CONSEQUENCE` | two independently authored premises agree about a physical property of the design | **only this one** |

Both vocabularies are closed sets in `assy_v3/assurance/model.py`, and a check
declaring a value outside either is a registry error rather than a default.

Outcome and establishment vocabularies are NOT invented here. Outcomes reuse
`STATUS_SEMANTICS.evaluation_outcomes` (`PASS`, `FAIL`, `NOT_VERIFIED`,
`NOT_EVALUABLE`, `UNSUPPORTED`, `INDETERMINATE`); establishment reuses
`STATUS_SEMANTICS.status_constructs.ENGINEERING_ESTABLISHMENT`
(`ENGINEERING_ESTABLISHED`, `NOT_ESTABLISHED`, `NOT_VERIFIED`,
`EVIDENCE_INCOMPLETE`). `FALSE_ACCEPTANCE` is carried as a finding code on the
commitment-validity capability, which is the emitter M-9 records as missing.

### A2 — assurance result persistence and currentness

**Resolved: an immutable external snapshot bound to the exact DesignState
revision it evaluated. Assurance writes nothing into DesignState.**

`AuthorityClass.ASSURANCE` (class D) exists in the authority model and no family
declares it. It stays unused, deliberately:

* writing check results into DesignState would change `state_hash()`, so the act
  of assessing the design would change the design being assessed — and a second
  assurance run would see a different state than the first. S8-I17 forbids
  exactly that recursion, and every S7-F property of the form "reconciling an
  unchanged design writes nothing" would become false;
* `GENERATED_ASSURANCE_PACKAGE_CONTRACT.projection_rule` already requires that
  "re-projecting an unchanged DesignState yields a byte-identical package" and
  that the package "has no authoring channel of its own". A snapshot computed by
  a total function of committed state satisfies that exactly; a stored finding
  family would be the second design world the same contract's `is_not` section
  forbids.

The snapshot therefore carries:

```
state_hash        the exact DesignState revision evaluated
premise_digest    per check, over the entity revisions it actually read
```

`premise_digest` reuses S7-F's `entity_revision_digest`, so currentness is
answered per check rather than by whole-state equality: a snapshot is current
for a check when the entities that check read are the revisions it read. A
snapshot whose `state_hash` differs from the current one is HISTORICAL and says
so; nothing may present it as current.

### A3 — the Rule A property map

Rule A: at least one meaningful engineering property per producing stage,
independently established. One row per stage, with the two independent authors
named, because a property whose two premises came from one author establishes
nothing.

| stage | engineering property | premise A (author) | premise B (author) | check | why ENGINEERING_CONSEQUENCE |
|---|---|---|---|---|---|
| **S01** | every stated reach demand is answered by a realization that reaches it | `Actor.must_reach` — the demand the source states (**s01**) | `ReachResult` — whether the arrangement reaches it (**s04a**) | `reach_demand_realization` | An unreached demand is a mechanism that does not do what the request required. s01 stated a demand it could not satisfy on its own; s04 placed bodies without being able to change the demand. Neither author could have made the other agree. |
| **S02** | every required physical effect is discharged by a realized interaction, or explicitly open | `PhysicalEffectObligation` — the effect the design must produce (**s02**) | `PhysicalInteraction` — the interaction that produces it (**s03b**) | `physical_relation_closure` | An undischarged required effect is a design that does not do its job. The demand and the realization are authored by different stages from different questions. |
| **S03** | no degree of freedom is disposed IRRELEVANT under a load or actuation that acts on it | `LoadCase` / actuation premises (**s02**) | `MobilityExpectation` dispositions (**s03b**) | `mobility_cross_premise_consistency` | Calling a loaded DOF irrelevant is a physical contradiction, not a bookkeeping gap. s02 authored the loads before any disposition existed. |
| **S04** | the realized arrangement is incident where the topology says the bodies are connected | `Joint` / `Interface` incidence (**s03a**) | `Envelope` placement (**s04a/b**) | `topology_to_spatial_fidelity` | A placement that separates bodies the topology connects is a mechanism that cannot be assembled. Bounded on purpose: it establishes fidelity to the declared topology, never that the topology was right. |

Two further ENGINEERING_CONSEQUENCE capabilities are registered and are NOT the
Rule A floor for any stage: `state_configuration_realization` (S03 bases vs S04
coordinates) and `required_distinctness_non_degeneracy` (declared distinctness
only). `commitment_validity` is EXTERNAL and judges the gate rather than a
producing stage.

**Nothing was relabelled to reach this floor.** `quantitative_continuity` stays
STRUCTURAL/FIDELITY, `mobility_disposition_completeness` stays
PROVENANCE_INTEGRITY, `consumer_sufficiency` and DOF totality stay BOOKKEEPING —
and none of them establishes anything.

---

## B. THE FROZEN S8 INVARIANT SET

S8-I1 baseline `237b1ba`; S01–S07 semantics frozen; U-9 only.
S8-I2 assurance is a separate deterministic layer over committed state; it
authors no class-A state and reaches no provider.
S8-I3 the dependency direction is producer → committed state → assurance, and no
`stages/*.py` module may import, invoke or reach an assurance check.
S8-I4 every current S01–S04 check is inventoried exactly once as A producer
validation · B bookkeeping · C independent assurance · D shared pure
computation. The inventory is data and the classification is a set equality
(`test_s8_closure_hygiene.py`), reconstructed from the `237b1ba` baseline.
S8-I5 every registered check declares check_id, independence_degree,
claim_class, property_scope and its authoritative inputs.
S8-I6 STRUCTURAL / PREMISE / EXTERNAL keep their architectural meaning; no
benchmark-, case- or mechanism-specific category.
S8-I7 the four claim classes keep their meaning; none is promoted to raise
coverage.
S8-I8 only a valid ENGINEERING_CONSEQUENCE result may raise its scoped property
to ENGINEERING_ESTABLISHED.
S8-I9 establishment is property-local and is never inherited from a sibling, a
stage, a patch, a design badge, execution success, contract completeness or
evidence maturity.
S8-I10 EXECUTION, CONTRACT_COMPLETENESS, EVIDENCE_MATURITY and
ENGINEERING_ESTABLISHMENT are maintained separately, with no term in two
constructs and no aggregate across them.
S8-I11 reporting shows the four constructs separately; an engineering finding
never downgrades EXECUTION SUCCESS, and an execution failure never becomes an
engineering claim.
S8-I12 the cross-construct `maturity_index` headline is retired, not renamed.
S8-I13 DOF totality is BOOKKEEPING and establishes nothing.
S8-I14 the retired sampling declaration stays retired and is no assurance
capability.
S8-I15 the §14 capability matrix semantics are preserved in substance.
S8-I16 Rule A is satisfied by the A3 map, frozen before implementation.
S8-I17 assurance output is bound to the exact state it evaluated; same state,
same output; a superseded snapshot is historical.
S8-I18 U-9 only: no fixture campaign, no generalization claim, no pipeline
s08/s09, no provider in assurance, `.gitignoreJoey…` untouched.

---

## C. THE CHECK INVENTORY (S8-I4)

Every S01–S04 check at baseline, classified exactly once.

The baseline is **41 module-level checks** in `stages/*.py` at `237b1ba`,
reconstructed from that commit rather than remembered, and every one of them has
exactly one disposition. The counts below are asserted as SET EQUALITIES by
`tests/meta/test_s8_closure_hygiene.py`; the totals in the first version of this
document did not reconcile with its own tables, which is precisely the kind of
claim a closure record may not make.

**A — producer / write-boundary validation (32).** They refuse malformed writes
and they stay where they are. Deterministic is not independent: the module that
wrote the value is the module deciding the value is well formed, which is the
right place for that question and the wrong place for any other.

| stage | checks |
|---|---|
| s01 | `sharpening`, `locator`, `mechanism_leakage` |
| s02 | `no_selection`, `load_case`, `candidate_distinctness`, `known_principle`, `evidence_route`, `created_obligations`, `requirement_coverage`, `obligation_scope`, `candidate_coverage`, `openness_citation`, `actor_citation` |
| s03 | `assembly_acyclic`, `load_path`, `interface_classification`, `retention`, `no_magnitude`, `obligation_ownership`, `functional_region`, `compliance`, `simulation_completeness`, `no_selection_s03` |
| s04 | `envelope_coverage`, `configuration_interference`, `region_occupancy`, `spatial_commitment`, `joint_frame`, `swept_clearance`, `assembly_path`, `load_path_reaction` |

**B — bookkeeping / report-only (2).** `dof_totality` (a count the producing code
guarantees) and `motion_evidence` (records the computation performed, never its
sufficiency). Neither is registered as assurance; both are named in
`NOT_ASSURANCE` so their absence is visible rather than merely true.

**C — independent assurance (11 capabilities, seven of them carrying relocated
code).** SEVEN baseline checks were relocated, onto seven capabilities — two of
them split, because one of the questions each was asking compares two producers
and the other does not:

| baseline check | pre-S8 owner | became |
|---|---|---|
| `magnitude_fidelity_check` | s02 | `quantitative_continuity` |
| `constraint_disposition_check` | s03 | `mobility_disposition_completeness` |
| `irrelevance_check` | s03 | `mobility_disposition_completeness` (names a scenario) **and** `mobility_cross_premise_consistency` (contradicted by a load) |
| `joint_geometry_check` | s04 | `topology_to_spatial_fidelity` |
| `configuration_realization_check` | s04 | `required_distinctness_non_degeneracy` **and** `state_configuration_realization` |
| `transition_realization_check` | s04 | `state_configuration_realization` |
| `selection_gate_check` | s04 | `commitment_validity` |

**FOUR capabilities are new work with no baseline predecessor** and are counted
separately, never as relocations: `consumer_sufficiency`, `reference_integrity`,
`physical_relation_closure`, `reach_demand_realization`. Seven plus four is the
whole registry, asserted as a set equality rather than as a sum.

**D — shared pure computation (9 references, derived from the AST).** Seven
callables and two constants, imported from the producing modules by the assurance
layer: `_s04._boxes`, `_s04._thaw`, `_s04.box_gap`, `_s04.required_contacts`,
`_s04._driving_joint`, `_s04.coordinate_change_disagreement`,
`_s03.current_mobility_cells`, and the constants `_s03.CONSTRAINT_DRIVERS` and
`_s03.QUALIFIER_WORDS`. Box arithmetic has no opinion about whether a design is
good, and a second implementation would be a second answer to "do these boxes
touch". The direction that matters is untouched: no stage reaches assurance.

*Bounded debt, recorded not fixed:* this makes the assurance layer import two
producing modules. It is class-D sharing by the S8-I4 rule and it is not a
producer reaching assurance, but a future pass may prefer to lift the geometry
helpers into a module neither side owns. That is a move, not a semantic change,
and it is out of scope for a hygiene patch.

### The one check that had stopped describing its subject

`selection_gate_check` read `equal_coverage_confirmed` and `evidence` — fields no
SelectionDecision has carried since S7-E. It would have reported every current
commitment as evidence-less, and it lived in the s04 module, so the answer was
wrong in the one place §14 calls the highest self-fulfilling risk. Its
replacement is `commitment_validity`: EXTERNAL, recomputing the contract's own
precondition (feasible for selection, every blocking requirement satisfied, and a
human SELECT behind it) from committed records, and emitting `FALSE_ACCEPTANCE` —
a status that had no emitter in this repository until now.

---

## D. RESULTS

### D.1 The closure suite

**29 tests** in `test_s8_assurance_status.py`, over real committed states and
with no model call. Independence S8_01–S8_05b · establishment S8_06–S8_09 ·
status constructs S8_10–S8_14 · capabilities S8_15–S8_21 · snapshot binding
S8_22–S8_23b · Rule A one test per producing stage plus the "nothing was
relabelled" pin.

### D.2 Mutations, each named to a frozen invariant

| mutation | invariant | caught by |
|---|---|---|
| a stage module imports assurance | S8-I3 | S8_01 |
| a FIDELITY check is relabelled ENGINEERING_CONSEQUENCE | S8-I7 | S8_06, S8_07, RULE_A_nothing_relabelled |
| any passing check establishes | S8-I8 | S8_07 |
| establishment leaks across properties | S8-I9 | S8_09 |
| the dashboard downgrade returns | S8-I11 | S8_10 |
| the maturity index returns | S8-I12 | S8_14 |
| DOF totality is registered as assurance | S8-I13 | S8_15/S8_16 |
| the snapshot is not bound to its state | S8-I17 | S8_22, S8_23 |
| assurance imports a provider | S8-I2 | S8_04 |
| the registry stops validating declarations | S8-I5 | S8_05 |
| one author may claim a consequence | S8-I5/I6 | S8_05b |
| undeclared distinctness is penalised | S8-I15 | S8_17 |

Twelve mutants, twelve caught, every one named to a frozen invariant rather than
invented to raise a count.

### D.3 In-scope defects found and fixed during the pass

* **The gate was reporting on itself against fields that no longer exist**
  (above). Found while relocating it, fixed at the cause rather than by deleting
  the check.
* **`topology_to_spatial_fidelity` named the bodies it compared and not the
  extents it measured**, so a snapshot stayed "current for that check" after the
  placement it read was revised. The premise digest now covers the envelopes.
* **`consumer_sufficiency` would have merged the two absences.** It reports
  `PROJECTION_FAILURE` as a FAIL and `UPSTREAM_INSUFFICIENCY` as NOT_VERIFIED,
  because one of them is a defect in this repository and the other is a fact
  about the design's upstream.

### D.4 Bounded S8-I1…S8-I18 audit

**S8-I2 / S8-I3 direction.** No module under `stages/` imports, names or calls
anything in the assurance package — asserted over the AST of every stage module,
so the audit measures the code rather than a docstring that mentions the word.
The reverse direction exists and is declared: assurance imports the s04 geometry
helpers as class-D shared pure computation.

**S8-I2 no provider.** The assurance package contains no provider import, no
`requests`, no socket and no `generate(`. A check that had to ask a model would
be an opinion about an opinion.

**S8-I4 inventory.** All 41 baseline checks classified exactly once: 32 producer
validations that stay, 2 bookkeeping, 7 relocated onto assurance capabilities.
The registry is those 7 relocation targets plus 4 new capabilities, and the
assurance layer shares 9 pure computations with the producing modules. Every one
of those numbers is a set equality in `test_s8_closure_hygiene.py`, reconstructed
from the baseline commit; the producer set and the registry are disjoint by
name.

**S8-I5 / S8-I6 / S8-I7 declarations.** Every registered check declares all five
fields; four malformed declarations are refused by `Check.validate`, and an
ENGINEERING_CONSEQUENCE claim from a single author is refused unless the degree
is EXTERNAL.

**S8-I8 / S8-I9 establishment.** Only ENGINEERING_CONSEQUENCE establishes, and
only the property its own finding names. The leak probe breaks one incidence and
asserts the sibling pairs stay established while the broken one does not; the
serialized snapshot contains no `overall`, no `score`, no `index`, no
`stage_established` and no `design_established`.

**S8-I10 / S8-I11 constructs.** The four are reported side by side; no term
appears in two; the dashboard's OK→WARN downgrade is gone from the source, and a
report built with two SUCCESS attempts and a failing engineering finding still
reports two SUCCESS attempts.

**S8-I12 scalar.** `maturity_index` does not exist, and no successor named
quality, readiness or confidence exists either. Aggregation survives only within
a construct.

**S8-I13 / S8-I14.** `dof_totality` and the sampling declaration are absent from
the registry, named in `NOT_ASSURANCE`, and absent from the capability module.

**S8-I15 capabilities.** The §14 rows are implemented in substance: the two
absences are never merged; distinctness is conditional on a declared premise; the
gate does not report on itself; and `FALSE_ACCEPTANCE` has an emitter for the
first time.

**S8-I17 snapshot.** Same state, byte-identical snapshot and identical digest;
running the whole registry twice leaves `state_hash` unchanged; a snapshot whose
bound hash is not current reports itself historical; a check's premise digest
moves when what that check read is revised and not when something else is.

**S8-I18 scope.** No fixture campaign, no generalization claim, no pipeline
s08/s09, no S05+ work, and no provider anywhere in the layer.

Zero unresolved S8-owned blockers.

### D.5 Scope

U-9 only. No fixture campaign, no generalization claim, no pipeline s08/s09, no
S05+ work, and no provider anywhere in the assurance layer. S01–S07 semantics are
untouched except where a relocated check's consumers had to follow it, which is
the move M-9 prescribes. `.gitignoreJoey…` untouched.

Regression, **secondary**: RUN 1423 · PASS 1423 · FAIL 0 · SKIP 22.

---

## CURRENT STATUS

> **S-8 / U-9 VERIFIED CLOSED — ASSURANCE IS INDEPENDENT, ENGINEERING
> ESTABLISHMENT IS CLAIM-BOUNDED, AND STATUS CONSTRUCTS DO NOT COLLAPSE.**
>
> The checks no longer live in the modules they judge, and no producing module
> can reach one. Every registered capability declares how far it stands from the
> writer and what a pass entitles it to say, before it runs. Only two
> independently authored premises agreeing about a physical property may
> establish one — and they establish exactly that property, of exactly that
> entity, with no stage, design or badge for it to leak into. Rule A is met by
> four such properties, one per producing stage, none of them relabelled to get
> there. The four status constructs are reported side by side: an engineering
> finding no longer downgrades an execution badge, an execution failure
> manufactures no engineering claim, and the maturity index that averaged
> completeness with care is retired rather than renamed. Results are an immutable
> snapshot bound to the state revision they read, so assessing the design cannot
> change it and yesterday's assurance cannot present itself as today's.
