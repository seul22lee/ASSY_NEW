# Package 2 — COMPLETE

All 17 contracts read start-to-end in this session, 4,610 lines. Raw contract
text is the only evidence used. No tests were run, no implementation was read, no
PASS/FAIL status or prior report was treated as evidence.

**Nothing was modified. No redesign is proposed.**

---

## 1. Files read

| # | file | lines | read |
|---|---|---|---|
| 1 | `ver3/contracts/DESIGN_STATE_CONTRACT.yaml` | 612 | COMPLETE |
| 2 | `ver3/contracts/STAGE_OWNERSHIP_MATRIX.yaml` | 346 | COMPLETE |
| 3 | `ver3/contracts/PROVENANCE_CONTRACT.yaml` | 172 | COMPLETE |
| 4 | `ver3/contracts/STAGE_PATCH_CONTRACT.yaml` | 176 | COMPLETE |
| 5 | `ver3/contracts/STATUS_SEMANTICS.yaml` | 341 | COMPLETE |
| 6 | `ver3/contracts/MODEL_RUN_RECORD_CONTRACT.yaml` | 221 | COMPLETE |
| 7 | `ver3/contracts/BENCHMARK_RESULT_CONTRACT.yaml` | 185 | COMPLETE |
| 8 | `ver3/contracts/GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml` | 476 | COMPLETE |
| 9 | `ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml` | 251 | COMPLETE |
| 10 | `ver3/contracts/ENTITY_FAMILY_AUDIT.yaml` | 872 | COMPLETE |
| 11 | `ver3/contracts/stages/S01_CONTRACT.yaml` | 92 | COMPLETE |
| 12 | `ver3/contracts/stages/S02_CONTRACT.yaml` | 105 | COMPLETE |
| 13 | `ver3/contracts/stages/S03_CONTRACT.yaml` | 198 | COMPLETE |
| 14 | `ver3/contracts/stages/S04_CONTRACT.yaml` | 170 | COMPLETE |
| 15 | `ver3/contracts/stages/S05_CONTRACT.yaml` | 139 | COMPLETE |
| 16 | `ver3/contracts/stages/S06_CONTRACT.yaml` | 142 | COMPLETE |
| 17 | `ver3/contracts/stages/S07_CONTRACT.yaml` | 112 | COMPLETE |

All seventeen carry `status: draft`. No contract is frozen.

---

## 2. Reconstructed entity-family and ownership model

### 2.1 The count is 41, and it reconciles across three independent routes

`DESIGN_STATE_CONTRACT.yaml` defines **41** family keys: 21 under
`entity_families` (:49-308) and 20 under `assurance_families` (:440-611).
`STAGE_OWNERSHIP_MATRIX.yaml` assigns **41** distinct families (38 in the twelve
`owns` lists, of which Witness and NegativeControl each appear twice, plus 3
`universally_ownable` at :192-204). `ENTITY_FAMILY_AUDIT.yaml:9` declares
`families_audited: 41`, and its `summary` (:25-29) sums CORE 32 + PROVISIONAL 6 +
MERGE_CANDIDATE 3 + UNSUPPORTED 0 = **41**.

The audit's own narrative accounts for only 40: `re_run_note` (:10-16) records
32 → 37 by the proposal's five (RigidGroup, LoadCase, LoadPath, FunctionalRegion,
AssemblyStep), and `note_on_window2_growth` (:36-40) records three more
(Envelope, SweptVolume, SelectionDecision). The forty-first is **Actor**, and the
audit records why at :549-552:

> `evidence: 'Found by the first execution of s01: S01_CONTRACT creates Actor and
> DESIGN_STATE_CONTRACT had no such family, so the patch was rejected as
> UNKNOWN_FAMILY.'`

Actor was added because a patch was rejected, not by any design document. The
narrative does not mention it.

**This settles P1's DIS-9.** The correct figure is 41. The Window 2 report's
"41 → 44" is wrong; its "41 families" in the same section is right.

### 2.2 Ownership, complete

| stage | owns (`STAGE_OWNERSHIP_MATRIX` :30-188) | extends |
|---|---|---|
| s01 | Requirement, SourceClause, Freedom, Ambiguity, Scenario, Actor | — |
| s02 | Obligation, Candidate, AcceptanceContract, LoadCase | Requirement |
| s03 | Body, RigidGroup, Joint, Interface, Configuration, MobilityExpectation, LoadPath, FunctionalRegion, AssemblyStep | Candidate, Obligation |
| s04 | State, Transition, Witness, Envelope, SweptVolume, SelectionDecision | Joint, Body, Configuration |
| s05 | Feature, Realization, Parameter, Constraint, ConstructionStatement | Body, Joint, Interface, Obligation |
| s06 | *(none)* | Parameter, Constraint |
| s07 | GeometrySignature | Body, Feature |
| s08 | VerificationPlanItem, NegativeControl | Requirement, Obligation |
| s09 | EvidenceItem, Witness, NegativeControl | VerificationPlanItem |
| s10 | *(none)* | EvidenceItem, NegativeControl, VerificationPlanItem |
| s11 | RequirementEvaluation, ExcludedClaim | Requirement |
| s12 | FailureProvenance, HumanReviewQuestion | RequirementEvaluation, UnresolvedDecision |
| any | UnresolvedDecision, Assumption, RejectedAlternative | — |

Typed relations, `DESIGN_STATE_CONTRACT` §3b (:370-395), all `created_by: s03`
and all declared to imply **no new family**: `blocked_by`, `retained_by`,
`co_actuated_by`.

### 2.3 Family status, from `ENTITY_FAMILY_AUDIT`

**MERGE_CANDIDATE (3):** Ambiguity (:113, → UnresolvedDecision subtype), Witness
(:300, → s04-only, s09 emits EvidenceItem), AssemblyStep (:646, vs Configuration
— recommendation is *keep both*).

**PROVISIONAL (6):** AcceptanceContract (:174), GeometrySignature (:383),
NegativeControl (:423), Envelope (:669), SweptVolume (:690), SelectionDecision
(:712).

**Not projected into the assurance package (9)** — `required_for_assurance_package: false`:
Actor (:546), RigidGroup (:563), LoadCase (:583), LoadPath (:604),
FunctionalRegion (:625), AssemblyStep (:645), Envelope (:667), SweptVolume
(:688), SelectionDecision (:710). Independently confirmed by walking
`GENERATED_ASSURANCE_PACKAGE_CONTRACT` PKG-01..PKG-34: none of those nine appears
in any `projects:` list. Five carry an identical `package_debt` string; three
carry the Window-2 variant; Actor's reads *"a reviewer needs actor reach to read
an access claim"*.

**Nine of forty-one families have no content section in the assurance package.**
Among them are every family the S03→S04 handoff is built on.

### 2.4 Per-value maturity and provenance

`DESIGN_STATE_CONTRACT.maturity_rule` (:326-342): vocabulary
`[SYMBOLIC, PROVISIONAL, AUTHORITATIVE, FROZEN]`, `required_on: "every
authoritative_geometry field, and every Parameter value"`, with a
`check_precondition` making a below-minimum-maturity check a `SCHEMA_FAILURE`.

Families carrying `authoritative_geometry_fields`: Body (pose, extent,
swept_volume, :116), State (body_poses, swept_volumes, :186), Transition (path,
swept_volume, :194), FunctionalRegion (volume, :292). Four families.

`PROVENANCE_CONTRACT` §1 (:22-27): *"Every entity, every field value, and every
relationship in DesignState. … No value enters DesignState without a provenance
record."* Ten methods (:62-118): `SOURCE_VERBATIM` and `SOURCE_DERIVED` (s01
only), `ASSUMPTION`, `MODEL_GENERATION`, `MODEL_ASSISTED`, `TOOL_COMPUTATION`,
`SOLVER`, `ENGINEERING_KNOWLEDGE`, `PROPAGATION`, `HUMAN`. Terminal methods
(:127): `SOURCE_VERBATIM, ASSUMPTION, ENGINEERING_KNOWLEDGE, MODEL_GENERATION,
HUMAN`.

**This is the contract-level instrument for the audit's provenance question.**
`MODEL_GENERATION` vs `MODEL_ASSISTED` vs `TOOL_COMPUTATION` vs `PROPAGATION`
distinguishes model-authored from deterministically-derived, and
`ENGINEERING_KNOWLEDGE` (:99-108) requires `[knowledge_ref, knowledge_version]`
with the constraint *"A fact the model simply knows is MODEL_GENERATION, not
this"* and `prohibited_sources` naming Ver1 cards, the Oracles and the CAD
references.

---

## 3. Reconstructed producer–consumer graph, from the contracts

Read as: consumer's declared `required_inputs` ← producer's declared outputs.

```
s01  ──[Requirement, SourceClause, Freedom, Ambiguity, Scenario, Actor,
        quantity_inventory]──────────────────────────────────────────────► s02
     S01_CONTRACT:84 needs = [requirements, observables, scenarios_by_kind,
                              actors, quantity_inventory,
                              ambiguities_with_block_scopes]
                                     ▲ observables: NO PRODUCER (§6.1)
                                     ▲ block_scopes: NO DEFINITION (§6.2)

s02  ──[Obligation, Candidate, AcceptanceContract, LoadCase]──────────────► s03
     S02_CONTRACT:95 needs = [body_hypotheses_with_roles, interaction_hypotheses,
                              obligations_addressed_and_created,
                              load_cases_with_direction_classes,
                              evidence_route_verdicts]
                                     ▲ first two: NO FAMILY, NO PRODUCER (§4.1)
     S03_CONTRACT:26 from_s02 = [Obligation, Candidate, LoadCase,
                                 AcceptanceContract, UnresolvedDecision]
                                     ◄ corrected; the two lists disagree (§4.1)

s03  ──[Body, RigidGroup, Joint, Interface, Configuration,
        MobilityExpectation, LoadPath, FunctionalRegion, AssemblyStep,
        blocked_by, retained_by]───────────────────────────────────────► s04a
     S04_CONTRACT:31 from_s03 = [Body, RigidGroup, Joint, Configuration,
                                 FunctionalRegion, AssemblyStep,
                                 actor_reach_requirements]
                                     ▲ actor_reach_requirements: NO PRODUCER (§6.3)

s04a ──[Envelope, FunctionalRegion volumes, SelectionDecision]──────────► s04b
     S04_CONTRACT:96-97 from_s03 = [Joint, MobilityExpectation,
                                    blocking_relations, AssemblyStep, LoadPath]
                       from_s04a = [Envelope, FunctionalRegion volumes,
                                    SelectionDecision]

s04b ──[located Joint frames, State, Transition, SweptVolume, Witness,
        Interface.engagement_site, LoadPath maturity]──────────────────► s05
     S05_CONTRACT:19-20 from_s03 = [Interface, blocking_relations,
                                    compliant Joints, AssemblyStep,
                                    MobilityExpectation]
                        from_s04b = [located Joint frames, State, Transition,
                                     SweptVolume, FunctionalRegion volumes,
                                     confirmed LoadPath]

s05  ──[Feature, Realization, Constraint, Parameter, ConstructionStatement,
        ROI]───────────────────────────────────────────────────────────► s06
                                     ▲ ROI: NO FAMILY, NO OWNER (§6.4)
s06  ──[Parameter values, Constraint status]───────────────────────────► s07
s07  ──[GeometrySignature, compiled solids]────────────────────────────► s08
```

**Convergence block** (`S06_CONTRACT` :50-112): members `[s04b, s05, s06]`.
`may_change: [placements, dimensions, feature alternatives]`;
`may_not_change: [Body, RigidGroup, Joint, interaction_kind, MobilityExpectation,
LoadPath, AssemblyStep]` → escalate to s03.

**Selection gate** (`S04_CONTRACT` :75-83): sits between s04a and s04b;
precondition is equal obligation coverage; a tie is an `UnresolvedDecision`.
**No `deterministic_exit_check` in either pass enforces it** — S04A-C1..C6 and
S04B-C1..C9 contain no gate check.

---

## 4. P1 architecture-critical concepts, traced through raw contract text

### 4.1 `BodyHypothesis` / `PhysicalInteractionHypothesis`

| question | answer | anchor |
|---|---|---|
| DEFINED? | **No.** Neither appears in `DESIGN_STATE_CONTRACT.yaml` — not in `entity_families`, not in `assurance_families` | complete read of all 41 keys |
| OWNED BY? | **Nobody.** `STAGE_OWNERSHIP_MATRIX` s02.owns = `[Obligation, Candidate, AcceptanceContract, LoadCase]` | `STAGE_OWNERSHIP_MATRIX.yaml:55` |
| PRODUCED BY? | **Declared** as created by s02 | `S02_CONTRACT.yaml:30` — `creates: [Obligation, Candidate, AcceptanceContract, LoadCase, BodyHypothesis, PhysicalInteractionHypothesis]` |
| REQUIRED BY? | **Declared** as the s02→s03 handover | `S02_CONTRACT.yaml:95` — `needs: [body_hypotheses_with_roles, interaction_hypotheses, …]` |
| REFERENCED BY? | s03's input list **explicitly removed them** | `S03_CONTRACT.yaml:21-25` |
| FIELDS? | none anywhere | — |
| CONSUMER? | none | — |

**CONFLICTING EVIDENCE.** `S03_CONTRACT.yaml:21-25` states the correction in its
own comment:

> `# Corrected in Window 2 by the producer/consumer audit. The previous list`
> `# named BodyHypothesis and PhysicalInteractionHypothesis, which no stage`
> `# produces and DESIGN_STATE_CONTRACT does not define. s03 OWNS Body and`
> `# Interface creation, so it cannot also consume them: the bodies are derived`
> `# here from the selected candidate's principle families.`

**WHY IT IS STRANGE.** The consumer side was corrected; the producer side was
not. `S02_CONTRACT` still declares s02 *creates* two families that do not exist
and that its own `structured_outputs` block (:62-66) does not list, and still
declares them the required handover to s03. Under
`STAGE_PATCH_CONTRACT.yaml:78` — *"stage_id must own entity_type in
STAGE_OWNERSHIP_MATRIX"* — a CREATE of either is a `SCHEMA_FAILURE`.

**STATUS: UNRESOLVED.** NEEDS LATER CROSS-READ (P4A: what S02's raw output
actually hands S03 in place of them).

### 4.2 Physical-interaction / physical-effect representation

**DEFINED?** Partly. `Interface` (`DESIGN_STATE_CONTRACT:151-166`) carries
`interaction_kind ∈ [DECLARED_CONTACT, DECLARED_CLEARANCE,
DECLARED_INTERFERENCE_FIT, DECLARED_COMPLIANT_INTERACTION,
NOT_INTENDED_TO_INTERACT]`, owned by s03. There is **no family and no field for a
physical-effect chain** between a candidate principle and a topology. `Candidate`
carries `principle` and `family` as fields (:96) with no structure beneath them.

**P1 INTENDED EVIDENCE** → `S02_S04_REASONING_GAP_ANALYSIS` §5 M-2: *"no
physical-effect chain between S02 and S03. S02 yields a principle family; S03
must produce bodies, joints and interfaces. Nothing in between states what
physically acts on what, in what order."*
**P2 CONTRACT EVIDENCE** → confirmed: no such family, field or relation exists in
any of the seventeen contracts.
**STATUS: MISSING.**

### 4.3 `blocked_by`

| question | answer | anchor |
|---|---|---|
| DEFINED? | Yes, as a **typed relation, not a family** | `DESIGN_STATE_CONTRACT:372-382` |
| OWNED BY? | `created_by: s03`; `subject: RigidGroup` | :373-374 |
| FIELDS? | required `[retained_group, blocked_direction, blocker_body, promised_features, configurations, defeat_specification, driver]`; optional `[depends_on_compliant_recovery]`; `driver ∈ [LOAD, KINEMATIC_NECESSITY, DECLARED_SCENARIO]` | :375-377 |
| REFERENCED BY? | `MobilityExpectation` disposition `BLOCKED_BY` *"must resolve to a blocked_by relation"* | :519 |
| **HAS AN ID?** | **No.** The field list contains no `entity_id` and no identifier of any kind | :375 |

**CONFLICTING EVIDENCE.** `DESIGN_STATE_CONTRACT:218` requires
`UnresolvedDecision.blocks` as a field. `blocks` is given no declared type and no
declared reference target anywhere in the seventeen contracts. Meanwhile
`STAGE_PATCH_CONTRACT:99` defines RELATE as
`required: [relation_type, subject, object, provenance_ref]` and validates
*"Both endpoints must exist"*.

**WHY IT IS STRANGE.** Three separate mismatches meet here.
(a) A relation with no identifier cannot be the target of a reference, so
`MobilityExpectation`'s *"must resolve to a blocked_by relation"* has no
mechanism, and `UnresolvedDecision.blocks` has nothing to point at.
(b) None of the three typed relations fits RELATE's `subject`/`object` shape:
`blocked_by` has seven fields and no `object`; `retained_by` (:387) has
`retainer_groups`, a **list**, where RELATE expects one `object`;
`co_actuated_by` (:395) has `[joints, transition]` and no subject at all.
(c) `S03_CONTRACT:42` lists `relates: [blocked_by, retained_by]` and omits
`co_actuated_by`, which `DESIGN_STATE_CONTRACT:391` says s03 creates.

**POSSIBLE IMPLICATION** (not a conclusion): this is the contract-level shape of
the P1 finding that `UnresolvedDecision.blocks → BLK-0001` dangles.
**STATUS: UNRESOLVED.** NEEDS LATER CROSS-READ (P4A raw `s03b` output).

### 4.4 `MobilityExpectation` and DOF-disposition ownership

| question | answer | anchor |
|---|---|---|
| DEFINED? | Yes | `DESIGN_STATE_CONTRACT:508-524` |
| OWNED BY? | s03 | :509, `STAGE_OWNERSHIP_MATRIX:67` |
| FIELDS? | `[entity_id, configuration, dispositions]`; values `[INTENDED, BLOCKED_BY, MAINTAINED_BY_CLASS, IRRELEVANT_BECAUSE]` | :511-512 |
| TOTALITY | *"dispositions is a TOTAL function: for every rigid group in the configuration, every rigid-body DOF maps to exactly one value"* | :514-518 |
| DERIVED? | **Not listed** in `derived_not_stored` (:344-364), whose four instances are per-element load components, the pose law, support and reaction | :344-364 |

**CONFLICTING EVIDENCE.** `S03_CONTRACT:190-193`:

> `llm_role: > High for topology and strategy proposal. NONE for DOF totality:`
> `the domain is enumerated mechanically from the joint graph, and the LLM only`
> `dispositions each entry.`

**WHY IT IS STRANGE.** The contract splits the work precisely: the **domain** is
mechanical, each **disposition** is authored by the model. Nothing in any
contract authorises deriving the disposition *values*, and
`derived_not_stored` — the mechanism the representation uses to mark a value as a
projection — does not list them.

**P1 INTENDED EVIDENCE** → `S02_S04_REASONING_GAP_ANALYSIS` appendix records
`derive_mobility()` computing the whole grid, "grid cells authored by LLM 0",
"420 entries derived".
**P2 CONTRACT EVIDENCE** → the contract assigns disposition authorship to the LLM
and derivation status to nothing.
**STATUS: DIFFERS.** NEEDS LATER CROSS-READ (P5: what `derive_mobility()`
actually computes, and what provenance method it records).

### 4.5 `LoadCase`

| question | answer | anchor |
|---|---|---|
| DEFINED? | Yes | `DESIGN_STATE_CONTRACT:259-273` |
| OWNED BY? | s02 | :260 |
| FIELDS (representation) | `[entity_id, scenario, applied_to_role, reacted_at_role, direction_class, kind, magnitude_or_status]`, `kinds: [GRAVITY, PAYLOAD, ACTOR_APPLIED, REACTION]` | :262-263 |
| FIELDS (stage contract) | `[entity_id, scenario, applied_to_role, direction_class, kind, magnitude_or_status]` — **`reacted_at_role` absent** | `S02_CONTRACT:38` and again :65 |
| CONSUMER | s03, via `LoadPath`; `S03-C5` requires a path *"terminating at a declared reaction site"* | `S03_CONTRACT:168` |

**CONFLICTING EVIDENCE.** `DESIGN_STATE_CONTRACT:268-273` explains why the field
exists: *"reacted_at_role names WHERE the load leaves the product… Without it a
LoadPath has no declared terminus and 'terminates at a reaction site' is
uncheckable."* `S02_CONTRACT` omits it from both places it lists LoadCase's
fields.

**WHY IT IS STRANGE.** P1 recorded this field as the fix for readiness finding
B-1. The fix reached the representation contract and neither of the producing
stage contract's two field lists. S03-C5 therefore checks for a terminus the
producer's own contract does not require the producer to emit.
**STATUS: DIFFERS (contract vs contract).**

### 4.6 `LoadPath`

DEFINED `DESIGN_STATE_CONTRACT:275-286`. OWNED BY s03, `extendable_by: [s04, s06]`.
FIELDS `[entity_id, load_case, candidate, ordered_hops, maturity]` with
`maturity_progression: [HYPOTHESIS, SPATIALLY_INSTANTIATED, AUTHORITATIVE]`.
Maturity owners are given in `S03_CONTRACT:96`:
`{HYPOTHESIS: s03, SPATIALLY_INSTANTIATED: s04b, AUTHORITATIVE: s06}`.
Rules: each hop names the Interface that carries it; **candidate-specific**;
per-element load components derived and never stored (`S03-C11`).

**Its maturity vocabulary is a third, distinct one** — see §5.4.
**CONSUMER**: s04b (`S04B-C5` confirms or refutes every provisional path), s05
(`confirmed LoadPath`), s06 (promotion).

### 4.7 `FunctionalRegion`

DEFINED `DESIGN_STATE_CONTRACT:287-295`. OWNED BY s03, `extendable_by: [s04]`.
FIELDS `[entity_id, role, owning_bodies]`, `authoritative_geometry_fields:
[volume]`. Rule: *"s03 declares the role. s04a gives it a metric volume. s04b
proves occupancy across every state and path."* `S03_CONTRACT:129` gives the same
three fields. `S03-C12` requires a role and at least one owning body.

**No `required_by_actors` and no `reach_targets` field exists in any contract.**

### 4.8 The S03 → S04 handoff

`S03_CONTRACT:184-188` declares two consumers:

```
consumer:   s04a
needs:      [joint_graph, configurations, body_roles, functional_region_roles,
             packaging_obligations, actor_reach_requirements]
consumer_b: s04b
needs_b:    [total_dof_disposition, blocking_relations,
             assembly_steps_with_order_and_access_side, load_paths_as_hypotheses]
```

`S04_CONTRACT:31` mirrors it: `from_s03: [Body, RigidGroup, Joint, Configuration,
FunctionalRegion, AssemblyStep, actor_reach_requirements]`.

Both ends name **`actor_reach_requirements`**. s03 owns nine families and no
field in any of them carries an actor's reach. `Actor.must_reach` exists
(`DESIGN_STATE_CONTRACT:471`) and `Actor` is **s01-owned**;
`STAGE_OWNERSHIP_MATRIX:90` does not permit s04 to extend Actor. `S04A-C3`
nevertheless requires *"every Actor has a reach result"*, and no `ReachResult`
family exists.

**STATUS: MISSING at both ends of the boundary, and unchecked-for by any
producer-side exit check.** `packaging_obligations` is likewise a consumer need
with no typed home; `Obligation` has no `kind` or `packaging` field.

### 4.9 The S04 → S05 handoff

`S04_CONTRACT:160-162` needs `[located_joint_frames, states_with_joint_coordinates,
paths_with_declared_sampling, swept_volumes, engagement_sites,
metric_functional_regions, confirmed_load_paths]`. Each has a producer:
`Joint.fields_owned_by_s04b: [located_frame]` (:126), `State`, `Transition`,
`SweptVolume`, `Interface.fields_owned_by_s04b: [engagement_site]` (:154),
`FunctionalRegion.volume`, `LoadPath.maturity`. `S04B-C9` requires every
Interface to have a metric engagement_site.

**This boundary is complete in the contracts** — the only one of the four S01–S05
boundaries that is.

### 4.10 Deterministic derivation versus authored fact

The contract's instruments are: `PROVENANCE_CONTRACT.methods` (ten values),
`DESIGN_STATE_CONTRACT.derived_not_stored` (four instances), and
`MODEL_RUN_RECORD_CONTRACT.tool_run_record` (:175-190), which a
`TOOL_COMPUTATION` or `SOLVER` provenance must reference.

Facts the contracts declare **derived, never stored**: per-element load
components, the pose law, support, reaction (`DESIGN_STATE_CONTRACT:344-364`).
Facts the contracts declare **model-authored**: candidate generation (S02
*"Highest of any stage"*), topology and strategy proposal (S03 *"High"*),
placements (S04 *"Low… the LLM proposes candidate placements for a solver to
check"*), each DOF disposition entry (S03 *"the LLM only dispositions each
entry"*).
Facts the contracts declare **LLM-free**: DOF domain enumeration (S03),
completeness enumeration (S05), all of s06 and s07 (`llm_role: NONE`).

**No contract defines a provenance method for a value the pipeline derives from
other DesignState values by its own rule other than `PROPAGATION`** (:110-112),
which requires `[rule, source_entity_ids]`. Whether the implementation's
deterministic derivations record `PROPAGATION` with a stated rule, or
`TOOL_COMPUTATION` with a ToolRunRecord, or neither, is **P5**.

---

## 5. Contract-internal contradictions

Each verified by complete read of both sides.

### CI-1 — `extendable_by` and `extends` disagree in ten places, in both directions

`DESIGN_STATE_CONTRACT` gives each family an `extendable_by` list.
`STAGE_OWNERSHIP_MATRIX` gives each stage an `extends` list.
`STAGE_PATCH_CONTRACT:87` validates EXTEND with *"stage_id must appear in the
family's `extends`, or own the family"* — without saying which file supplies it.

| family | `extendable_by` (DSC) | stages listing it in `extends` (SOM) | disagreement |
|---|---|---|---|
| Body | s05, s06, s07 (:112) | s04, s05, s07 | s04 permitted by SOM only; s06 by DSC only |
| Joint | s04, s05, s06 (:123) | s04, s05 | s06 by DSC only |
| Interface | s04, s05 (:153) | s05 | **s04 by DSC only — yet `S04_CONTRACT:109` has s04b extend `Interface engagement_site`** |
| LoadPath | s04, s06 (:277) | *(neither)* | permitted by DSC only |
| FunctionalRegion | s04 (:289) | *(none)* | permitted by DSC only |
| AssemblyStep | s04 (:299) | *(none)* | permitted by DSC only |
| Configuration | *(none)* | s04 | permitted by SOM only |
| Requirement | *(none)* | s02, s08, s11 | permitted by SOM only |
| Obligation | *(none)* | s03, s05, s08 | permitted by SOM only |
| Candidate, Feature, EvidenceItem, NegativeControl, VerificationPlanItem, RequirementEvaluation, UnresolvedDecision | *(none)* | various | permitted by SOM only |

**STATUS: UNRESOLVED.** Which list `STAGE_PATCH_CONTRACT:87` means is undecided,
and the two answers differ for at least ten families.

### CI-2 — `instance_identity` is required on five families and declared on one

`DESIGN_STATE_CONTRACT:38`: `required_on: [Body, Joint, Interface, Feature, Realization]`.
Of those five `required_fields` lists, only `Body` (:114) contains
`instance_identity`. Joint (:125), Interface (:162), Feature (:170) and
Realization (:177) do not.

### CI-3 — `REPRESENTATION_INCOMPLETE` is used as a status and defined in no vocabulary

`STATUS_SEMANTICS.collapse_enforcement` (:334-341) declares its own check:
*"Every forbidden collapse names a correct alternative that exists in a
vocabulary here."* `C-12` (:329-332) names
`correct: "REPRESENTATION_INCOMPLETE, and FALSE_ACCEPTANCE if it reached a PASS"`.
`REPRESENTATION_INCOMPLETE` appears in none of the four vocabularies —
`execution_statuses`, `evaluation_outcomes`, `solver_statuses`,
`observable_statuses`. It is also used as a verdict in
`DESIGN_STATE_CONTRACT:165` (*"An unclassified region is
REPRESENTATION_INCOMPLETE"*).

**The file states a rule that the same file violates.**

### CI-4 — `INFEASIBLE` has no evaluation-outcome home

`evaluation_outcomes` (:200-240) defines six: PASS, FAIL, NOT_VERIFIED,
NOT_EVALUABLE, UNSUPPORTED, INDETERMINATE. `C-01` (:272-276) names the collapse
*"missing capability → infeasible"*, and `INV-011` reserves INFEASIBLE for a
physical impossibility supported by an argument. The only `infeasible` defined in
this file is a **solver status** (:247). So the outcome INV-011 protects is not in
the outcome vocabulary.

### CI-5 — RELATE's operation shape does not fit any of the three typed relations

`STAGE_PATCH_CONTRACT:97-103` — `required: [relation_type, subject, object,
provenance_ref]`. `blocked_by` has seven fields and no `object`; `retained_by`
has a **list** where `object` is singular; `co_actuated_by` has no subject.
See §4.3.

### CI-6 — RECORD_UNRESOLVED omits two fields its family requires

`STAGE_PATCH_CONTRACT:116` — `required: [decision, why_open, alternatives, blocks,
provenance_ref]`. `DESIGN_STATE_CONTRACT:218` requires
`[entity_id, decision, why_open, alternatives, alternatives_kind, blocks,
kept_open_by]`. **`alternatives_kind` and `kept_open_by` are absent from the
operation** — and `kept_open_by` is the field whose absence
`DESIGN_STATE_CONTRACT:222-228` describes as the consumer-reconstruction defect
found by the first s01+s02 evaluation.

### CI-7 — `SystemBoundary` is created by a stage, defined by nothing, owned by nobody

`S01_CONTRACT:32` — `creates: [Requirement, SourceClause, Freedom, Ambiguity,
Scenario, Actor, SystemBoundary]`. `SystemBoundary` is not a family in
`DESIGN_STATE_CONTRACT` and not in `STAGE_OWNERSHIP_MATRIX:43`. `Scenario` has a
`system_boundary` **field** (:481).

This is the identical defect `ENTITY_FAMILY_AUDIT:549-552` records having already
been hit once and fixed for `Actor` — *"the patch was rejected as
UNKNOWN_FAMILY"*. Unfixed here.

### CI-8 — Field-name and field-list mismatches between stage contracts and the representation

| item | `DESIGN_STATE_CONTRACT` | stage contract |
|---|---|---|
| Interface | `nominal` (:162) | `nominal_status` (`S03_CONTRACT:125`) |
| Configuration | `[entity_id, name, bodies_present, expected_mobility]` (:506) | adds `kind` (`S03_CONTRACT:130`) |
| Feature | `body` (:170) | `rigid_group`, plus `maturity` (`S05_CONTRACT:83`) |
| Parameter | `[entity_id, symbol, unit, status]` (:203) | adds `maturity` (`S05_CONTRACT:86`) |
| Constraint | `[entity_id, expression, parameters, kind]` (:211) | adds `provenance` (`S05_CONTRACT:85`) |
| Obligation | requires `scope, satisfiable_at, evidence_route, route_available` (:63) | `S02_CONTRACT:63` lists none of the four |
| Ambiguity | `[entity_id, statement, conflicting_clauses, resolvable_when]` (:466) | adds `block_scopes` (`S01_CONTRACT:52`) |
| LoadCase | includes `reacted_at_role` (:262) | omits it (`S02_CONTRACT:38, :65`) |

### CI-9 — `ROI` is created by s05 and defined nowhere

`S05_CONTRACT:51` — `creates: […, ROI definitions]`; `:88` gives
`ROI: [entity_id, interaction, region, follows_frame]`. No `ROI` family exists in
`DESIGN_STATE_CONTRACT` and no stage owns it in `STAGE_OWNERSHIP_MATRIX`.

### CI-10 — `GAP-01` and `GAP-02` are declared OPEN and resolved in the same contract set

`ENTITY_FAMILY_AUDIT:829` — `GAP-01 … status: OPEN`,
`decision_required_before: s03 implementation`. `:850` — same for `GAP-02`.
`DESIGN_STATE_CONTRACT:384-388` defines `retained_by` with
`resolves: "ENTITY_FAMILY_AUDIT GAP-01"`, and `:308` records `AssemblyStep`
*"Subsumes the precedes(Configuration, Configuration) relation recorded as
ENTITY_FAMILY_AUDIT GAP-02."* The audit still carries both as OPEN.

The two resolutions also differ in type from the audit's proposals: GAP-01
proposes `retained_by(Body, [Body], Configuration)` (:825); the implemented
relation is `[retained_group, retainer_groups, configuration]` — RigidGroup-level.

### CI-11 — Two audit decision deadlines have been passed

`ENTITY_FAMILY_AUDIT.findings_by_stage` (:852-866):

| deadline | finding | state |
|---|---|---|
| `before_s01` | Ambiguity merge decision (:120) | s01 implemented; `closing_note:` *"Every finding above is recorded rather than applied"* |
| `before_s03` | GAP-01, GAP-02, Joint/Interface link, Interface/Feature link | resolved in DSC for the first two only; the two links remain `obligation: … Recorded, not applied` (:205, :222) |
| `before_s04` | Witness ownership and merge decision (:308) | s04 implemented; `OV-04` action reads *"Both recorded, neither applied"* (:781) |

`OV-04` (:771-784) states the cost: *"Dual ownership weakens INV-001's ownership
check: with two legitimate creators, a duplicate created by the second is
indistinguishable from a legitimate creation."* `STAGE_OWNERSHIP_MATRIX` still
lists Witness under both s04 and s09, NegativeControl under both s08 and s09.

### CI-12 — Three different maturity vocabularies

| vocabulary | values | anchor |
|---|---|---|
| global | SYMBOLIC, PROVISIONAL, AUTHORITATIVE, FROZEN | `DESIGN_STATE_CONTRACT:330` |
| Envelope | PROVISIONAL, AUTHORITATIVE | :594 |
| LoadPath | HYPOTHESIS, SPATIALLY_INSTANTIATED, AUTHORITATIVE | :280 |

The global rule says `required_on: "every authoritative_geometry field, and every
Parameter value"`. `Parameter.required_fields` (:203) does not list `maturity`;
`S05_CONTRACT:86` and `S06_CONTRACT:45` both add it.

### CI-13 — Two contracts scope the invalidation cone differently

`STAGE_PATCH_CONTRACT:31` makes `invalidation_cone` a required field of **every**
patch envelope. `PROVENANCE_CONTRACT:157` states it is
`required: "Computed and recorded on every SUPERSEDE"`.

### CI-14 — A check's rationale belongs to the check above it

`S04_CONTRACT:156-158` — `S04B-C9 check: "every Interface has a metric
engagement_site"`, `rationale: "the invalidation cone is computed from these
declarations"`. The cone is computed from **input value sets**, which is
`S04B-C8` (:154). The rationale describes C8.

### CI-15 — Three contracts name enforcers that do not exist

`STAGE_PATCH_CONTRACT:155` — `enforced_by: ver3/tests/meta/test_stage_determinism.py`.
`ARCHITECTURE_INVARIANTS` (P1) names the same file plus four others. Verified in
P1: none exists. `STATUS_SEMANTICS:335` names
`test_status_semantics.py` and `GENERATED_ASSURANCE_PACKAGE_CONTRACT:427` names
`test_no_legacy_imports.py` — both of which do exist.

---

## 6. Undefined, dangling and unproduced references

| item | required by | defined by | status |
|---|---|---|---|
| `Observable` | `S02_CONTRACT:18` (`from_s01: […, Observable, …]`); `S01_CONTRACT:29, :84`; `VerificationPlanItem.observable_id` (:233); `RequirementEvaluation` matching (:246); PASS six-field scope (`STATUS_SEMANTICS:205`) | **nothing** — not a family, not owned, not created. `Requirement.observable_verbatim` is a string field (:54) | **DANGLING** |
| `criterion` / `criterion_id` | `VerificationPlanItem` (:233); INV-012 matching (:246); PASS scope (`STATUS_SEMANTICS:205`); PKG-20 | **nothing** | **DANGLING** |
| `BodyHypothesis`, `PhysicalInteractionHypothesis` | `S02_CONTRACT:30, :95` | **nothing** | **DANGLING** (§4.1) |
| `SystemBoundary` | `S01_CONTRACT:32` | **nothing** | **DANGLING** (CI-7) |
| `ROI` | `S05_CONTRACT:51, :88` | **nothing** | **DANGLING** (CI-9) |
| `actor_reach_requirements` | `S03_CONTRACT:186`, `S04_CONTRACT:31`, `S04A-C3` | **no producer**; no `ReachResult` family | **NO PRODUCER** (§4.8) |
| `packaging_obligations` | `S03_CONTRACT:186` | no `Obligation` field distinguishes them | **NO PRODUCER** |
| `block_scopes` | `S01_CONTRACT:52, :84` | absent from `Ambiguity.required_fields` (:466) | **UNDEFINED FIELD** |
| `UnresolvedDecision.blocks` target | `DESIGN_STATE_CONTRACT:218`; `STAGE_PATCH_CONTRACT:116` | no declared type or target; relations have no ids | **UNTYPED REFERENCE** |
| `Constraint.expression` grammar | `DESIGN_STATE_CONTRACT:211`; solved by s06 | no grammar, no type system, no solvability class anywhere | **UNDEFINED** |
| `ConstructionProgram` | `S07_CONTRACT:18` | only `ConstructionStatement` is a family | **UNDEFINED AGGREGATE** |
| `declared predicates` | `S07_CONTRACT:101` | `verification_predicate` is a field on `Realization` | **UNDEFINED AGGREGATE** |
| `AcceptanceContract.predicates` | `DESIGN_STATE_CONTRACT:501` | untyped; no Predicate family | **UNTYPED** |
| `evidence_route_capabilities` registry | `S02_CONTRACT:19` (`from_registry`) | declared to live outside DesignState; no contract defines its shape | **EXTERNAL, UNSPECIFIED** |

---

## 7. P1 ↔ P2 status

| P1 intended evidence | P2 contract evidence | status |
|---|---|---|
| Five new families: RigidGroup, LoadCase, LoadPath, FunctionalRegion, AssemblyStep (`PROPOSAL` §8) | All five defined and owned exactly as proposed | **AGREES** |
| Count 32 → 37 | 41, reconciled across three routes; the extra six are the three Window-2 families plus Actor plus the audit's own arithmetic gap | **DIFFERS** (settles DIS-9) |
| Compliance as a `Joint` variant between `RigidGroup`s, one per member (D-2, C-1..C-4) | `DESIGN_STATE_CONTRACT:136-149` `compliant_variant` with all eight fields, `actuation: PRESCRIBED_KINEMATIC`, the two-travel rule, `compliant_element`, `root_interface`, `activation_window`; `S03_CONTRACT:77-91` repeats it | **AGREES** |
| `LoadCase` candidate-independent with `kind` (C-8) | Defined so, and `S02-C6` forbids naming an element | **AGREES** |
| `reacted_at_role` added (readiness B-1) | In `DESIGN_STATE_CONTRACT` only; absent from both `S02_CONTRACT` field lists | **DIFFERS** (§4.5) |
| `LoadPath` per candidate, three-step maturity (C-9) | Defined with owners per step in `S03_CONTRACT:96` | **AGREES** |
| Element load components derived, never stored (C-10) | `derived_not_stored` (:349); `s03.may_not` (:74); `S03-C11` | **AGREES** |
| `driver` on every constraining relation (C-12) | `blocked_by.driver` with three values | **AGREES** |
| `AssemblyStep.path_kind`, DEFORMATION_RESOLVED ⇒ NOT_VERIFIED (C-6) | :303, :306; `S03_CONTRACT:132-137` | **AGREES** |
| `MobilityExpectation.forbidden_dof` becomes total (D-11) | Totality stated at :514-518 and `S03-C1` | **AGREES** |
| Joint splits: direction s03 / located frame s04b / authoritative s06 | :125-135, `fields_owned_by_s04b: [located_frame]` | **AGREES** |
| Invalidation cone moves to `StagePatch` (C-13/D-9) | `STAGE_PATCH_CONTRACT:31, :48-62` | **AGREES**, but `PROVENANCE_CONTRACT:157` scopes it to SUPERSEDE (CI-13) |
| Termination by round budget + repeated state, not monotone reduction (C-13) | `S06_CONTRACT:53-65`, with the BM-003 replay argument | **AGREES** |
| Loop scope: placements, dimensions, feature alternatives only (C-14) | `S06_CONTRACT:67-78` | **AGREES** |
| A `Constraint` for every declared clearance (C-15) | `S05_CONTRACT:38-48`, `S05-C9` | **AGREES** |
| Nested budgets K/N, escalation ladder (C-16) | `S06_CONTRACT:80-84` | **AGREES** |
| Maturity as a per-value field (D-8) | Defined, but three vocabularies and `Parameter` omits it from its own required list | **AMBIGUOUS** (CI-12) |
| Defeat specification authored with the relation (D-10) | `blocked_by.defeat_specification`; `S03_CONTRACT:68-71` | **AGREES**; `NegativeControl` still dual-owned `[s08, s09]` (CI-11) |
| `BodyHypothesis` / `PhysicalInteractionHypothesis` removed as families | Removed from the representation and from s03's inputs; **still declared created by s02** | **AMBIGUOUS** (§4.1) |
| Physical-effect chain between S02 and S03 (`REASONING_GAP` M-2) | No family, field or relation | **MISSING** |
| `Interface.engagement_site` (readiness B-2) | :154 + `S04B-C9` | **AGREES** |
| Construction-frame rule (readiness B-3) | `S05_CONTRACT:71-80` | **AGREES** |
| `actor_reach_requirements` resolved in Window 2 Cycle 3 by adding `required_by_actors` and `reach_targets` to `FunctionalRegion` | Neither field exists in any contract; both consumer contracts still require it | **MISSING** |
| `addresses_obligations` added to bodies and interfaces (Window 2 Cycle 2) | Absent from both contracts; `S03-C7` still requires obligation ownership | **MISSING** |
| Scout as a `Witness` of fidelity SCOUT, raise-only, laundering barrier | `DESIGN_STATE_CONTRACT:526-546`, all five rules plus the barrier; `S07_CONTRACT:31` forbids reading one | **AGREES** |
| Assurance package built before S01, PKG-01..34 | Contract complete; nine families project into no section | **AGREES as a contract**, with the gap recorded |
| Stage-contract freeze gate | `STAGE_PROGRESSION_CONTRACT:195-197`: *"NO stage contract may freeze. FSF-01 is satisfied and FSF-02 through FSF-07 are not."* All seventeen contracts are `status: draft` | **AGREES** — and no window-freeze vocabulary exists in any contract |

---

## 8. Unresolved questions for later packages

**For P4A (raw outputs).** What does S02 actually hand S03 in place of the two
undefined hypothesis families? Does any `LoadCase` in the raw output carry
`reacted_at_role`? What do `UnresolvedDecision.blocks` values point at, given
that relations have no ids? Do `Obligation` records carry the four fields
`S02_CONTRACT` omits? Is `SystemBoundary` ever emitted?

**For P5 (implementation).** What provenance method does the implementation
record for `derive_mobility()`'s 420 entries — `PROPAGATION`, `TOOL_COMPUTATION`,
or none — and is a `ToolRunRecord` written? Which of the two conflicting
`extends` lists does patch validation enforce (CI-1)? How are the three typed
relations expressed, given that RELATE's shape does not fit them (CI-5)? Is
`instance_identity` emitted for Joint, Interface, Feature, Realization (CI-2)?

**For P6 (evaluators).** Does any check enforce the selection gate, which has a
contract and no exit check? Does any check enforce `PROVENANCE_CONTRACT`'s
"no value enters DesignState without a provenance record"? Is
`REPRESENTATION_INCOMPLETE` emitted anywhere, given it is in no vocabulary
(CI-3)? Does the run output ever produce the `runs/<run_id>/` layout
`BENCHMARK_RESULT_CONTRACT:152-177` specifies — in particular
`execution/file_access.jsonl`, which that contract calls the evidence a leak
claim requires?

**Structural, carried forward.** Nine of forty-one families — including every
family the S03→S04 handoff rests on — are projected into no assurance-package
section. `BENCHMARK_RESULT_CONTRACT` requires the evaluator, not the pipeline, to
write the result; neither the run layout nor the evaluation layout it defines
exists on disk.

---

*Package 2 complete. Every finding above is drawn from raw contract text with a
file and line anchor. Nothing is interpreted beyond what the text states, and no
repository file was modified.*
