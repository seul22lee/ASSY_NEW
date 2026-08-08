# P4B — FINAL EVIDENCE-CHAIN SYNTHESIS

Axis A: **GENERATED EVIDENCE**. Axis B: **REVIEW RECORD**.

This package searches for nothing new. It connects evidence already established in
P1–P3, P4A, the capability-gap synthesis, P5 (with its §20 topology→spatial addendum)
and P6 into one chain per engineering capability, and states what that chain establishes
about the current S01–S04 pipeline.

**No fix, prompt change, contract change, validator or architecture revision is proposed
anywhere in this document.** §18 states capability *requirements* only.

---

## §0 SCOPE AND EVIDENCE BASIS

| Package | Establishes | Coverage |
|---|---|---|
| **P1** | architecture of record; 18 invariants; 32 retirement rows | 22 files, 9,713 lines |
| **P2** | 41-family contract system; ownership; producer-consumer graph | 17 contracts, 4,610 lines |
| **P3** | mechanism-independent engineering reference bar | 12 files + 99/99 images |
| **P4A** | raw pipeline behaviour | 24 stage artifacts + 35/35 Window-1 responses + 60/60 prose bodies + 13 fixtures |
| **P4A synthesis** | CAP-01…CAP-14; failure types A–F | — |
| **P5** | implementation root cause; §20 topology→spatial chain | 26 files, 5,184 lines |
| **P6** | evaluator adequacy | 26 files, ~6,000 lines |

**Two settled conflicts between packages**, both resolved from raw anchors rather than by
authority:

1. P4A §2 held that live S02's bare-string `principle` was a deficiency. The s02 prompt's
   PERMITTED VALUES says `principle — one of the PRINCIPLE FAMILIES` (singular). **The
   model conforms; the fixtures do not.** Resolved in P4A §H.3.
2. P5's first pass held that `region_occupancy_check` and `swept_clearance_check` were
   dead and that `derive_mobility` had no caller. `_absorb` (`run_window2.py:346-375`)
   and `run_window2.py:257` disprove all three. Resolved in P5 §14.

---

## §1 EXECUTIVE SCIENTIFIC FINDINGS

1. **The intended architecture is progressive enrichment, and the code is faithful to its
   additive half.** All 30 `Op(...)` constructions in the corpus are `CREATE`; the `EXTEND`
   branch is never exercised. **No TYPE-B persistence failure was observed in the audited
   execution corpus.** This is an observation about the corpus, not a proof of
   impossibility: the normative architecture prohibits overwrite and loss, and two
   implementation-level mutation paths remain conceptually capable of it — the unguarded
   `EXTEND` branch (`design_state.py:135-136`) and `_absorb`'s direct assignment
   (`run_window2.py:346-375`). *(STRONG as an observation; the impossibility claim is not
   made.)*
2. **The additive persistence mechanism works in the audited corpus; the dominant
   recurrent continuity failures occur at consumer boundaries** — the S03→S04 boundary is
   governed by one whitelist, `S03_OWNED`, omitting `Requirement`, `LoadCase` and
   `Envelope` — **alongside distinct capture, representation, reasoning,
   deterministic-authorship, gating and assurance failures**, which are not
   continuity failures and are not explained by any boundary. *(STRONG)*
3. **S04B is instructed to place joints "in the same coordinates as the arrangement you
   were given", and the arrangement is in 0 of 6 prompts.** *(STRONG)*
4. **Deterministic code crosses from bookkeeping into engineering authorship at two exact
   points**: `s03.py:333-337` (`MAINTAINED_BY_CLASS` from absence of evidence) and
   `s04.py:306-308` (`sampling_declaration` from the constant `SAMPLES = 9`). *(STRONG)*
5. **Both of those manufactured values are then validated by checks that test the property
   the same code guarantees.** *(STRONG)*
6. **The model does fail under sufficient support, and the cases are identifiable** —
   principally where a configuration coordinate must change and does not, and where a
   named function has no structural realisation. *(STRONG)*
7. **The model's own unresolved layer is the strongest engineering output in the corpus,
   and nothing reads it back.** No `UnresolvedDecision` is consumed by any check, gate or
   stage. *(STRONG)*
8. **No engineering property of a mechanism is established by an evaluator independent of
   its producer.** Every Layer-B check is co-located with the stage and invoked by the
   same tool. *(STRONG)*
9. **`SAFE_REJECTION` and `FALSE_ACCEPTANCE` — the architecture's two poles — have no
   emitter anywhere in the corpus.** *(STRONG)*
10. **Window 2 is not end-to-end evidence**, and the reason is structural, not
    stylistic. *(STRONG — see §16)*

---

## §2 VERIFIED PROGRESSIVE-ENRICHMENT MODEL

Confirmed in the capability-gap synthesis §A from contract text and in P5 §2 from code.

| Question | Contract | Code |
|---|---|---|
| What persists? | everything; SUPERSEDE keeps both (`STAGE_PATCH_CONTRACT:106`) | all 30 ops are CREATE; nothing deleted |
| May a stage replace prior state? | **no** (`:89`, `:92-95`) | EXTEND branch exists (`design_state.py:135-136`) and **is never used** |
| What does invalidation remove? | nothing — marks STALE (`:48-62`) | `invalidation_cone` declared (`patch.py:46`), **read nowhere** |
| Persistent state vs consumer view | different by design; INV-002 (`DESIGN_STATE_CONTRACT:401`) | `projection.py` strips **one** family |

**Consequence that governs this whole synthesis.** Because nothing is deleted, every
"information loss" observation must resolve to **capture (A)**, **projection (C)**,
**representation (D)**, **reasoning (E)**, **gating (F)** or **assurance (G)** — never to
persistence (B). *(STRONG)*

**One unguarded write exists and must be recorded precisely.** `_absorb`
(`run_window2.py:346-375`) mutates `state.entities` by direct assignment — no `Op`, no
validation, no ownership check, no provenance — writing `volume`, `insertion_direction`
and `frame_origin`. In observed runs each field is written once, so **no loss occurred**;
the mechanism is unguarded, the outcome is not a realised TYPE-B. *(STRONG)*

---

## §3 CAPABILITY EVIDENCE MATRIX

| ID | Capability | P3 bar | P4A observation | First boundary | P5 root cause | P6 response | Recurrence | Conf. | Status |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | Requirement atomization | distinct obligations must separate | "slip or rotate" merged 3/3 PRB-02; "every time" merged 3/3 PRB-03 | **S01** | contract defines no atomization property; `completeness` checks non-emptiness only | not in jurisdiction | cross-case + cross-trial | STRONG | **NOT ESTABLISHED** |
| C-02 | Ambiguity preservation | a silently answered ambiguity is an unrecorded commitment | wall-fixings, signal-scope, knock-magnitude absent 3/3 each; PRB-01 refill typed OPERATION/SERVICE/SERVICE across trials | **S01** | no coverage property; `block_scopes` has no stated vocabulary | not in jurisdiction | cross-case + cross-trial | STRONG | **NOT ESTABLISHED** |
| C-03 | Quantity extraction | a stated quantity must survive with its qualifier | correct in **every** trial where the source states one | — | — | `magnitude_fidelity_check` real | cross-case | STRONG | **DEMONSTRATED** |
| C-04 | Source/provenance semantics | source text must not be re-read downstream | `SourceClause` in 0/18 s02 prompts | — | INV-002, enforced twice | `test_s02_never_sees_source_text` | 18/18 | STRONG | **DEMONSTRATED** |
| C-05 | Quantitative continuity to the consumer | scale-dependent reasoning needs the scale | 80–100 mm and 18–40 mm absent from s04; `scale.absolute: null` 6/6 | **S03→S04A** | `S03_OWNED` excludes `Requirement` | false negative — `interface_gaps` has no quantity term | 2/2 quantity cases | STRONG | **DISCONNECTED** |
| C-06 | Candidate/principle representation stability | one canonical structure both sides | 3 shapes: string ×15, array ×2, dict ×13 | **S02 contract/prompt** | prompt Rule 3 vs PERMITTED VALUES contradict; checks branch on all three | not in jurisdiction | contract-level + within-case | STRONG | **REPRESENTATION-INCOMPLETE** |
| C-07 | Physical-effect / interaction grounding | a transmitting relation must be structural | interlock, screw→jaw, spring→pedal, input→motion all in prose or CONTACT only | **S03** | `Interface` has no transmission field; no `BodyHypothesis` family exists | not in jurisdiction | 4/6 cases | STRONG | **REPRESENTATION-INCOMPLETE** |
| C-08 | Load / reaction closure | a load must terminate outside the product | 0/6 cases close; six degenerate ground encodings | **S03B** | no external-site type; `reaction`/`support` derivations unimplemented | partially detected — hop-resolution yes, externality no | 6/6 | STRONG | **NOT ESTABLISHED** |
| C-09 | Retention / blocking grounding | directional, localized, defeat-specified | `"NONE"` direction 4/7, 4/4, 4/10, 4/5, 4/4; self-blocking; `blocker_body:"NONE"` | **S03B** | prompt offers `NONE`; `"NONE"` is truthy in every presence test | false negative (self-blocking); prompt-permitted (direction) | 6/6 | STRONG | **REPRESENTATION-INCOMPLETE** |
| C-10 | Typed-relation addressability | a relation must be referenceable | `blocking_relation` ids exist in no entity | **contract/code** | `Op` has no `relation_type/subject/object`; relations never stored | false negative — nested refs not traversed | contract-level | STRONG | **REPRESENTATION-INCOMPLETE** |
| C-11 | Mobility / DOF authorship | every DOF disposition needs evidence | ~120/126 cells from the `else` branch in BM-003 | **S03 / deterministic** | `s03.py:333-337` | self-fulfilling | 6/6 | STRONG | **UNSUPPORTED DETERMINISTIC COMPLETION** |
| C-12 | Topology→spatial realization | topology must survive into space | 19/25 joints coincident; s04a symmetry lost | **S03→S04A/B** | `Envelope` in 0/6 s04b prompts; 4/6 truncated | not in jurisdiction | 5/6 | STRONG | **DISCONNECTED** |
| C-13 | Joint/body incidence | a joint lies where its bodies meet | BM-001 `JNT-0002` at `[0,0,0]`, body at `x∈[1.5,2.5]` | **S03→S04B** | arrangement not projected | false negative — check compares bodies, not the joint | 2/6 verified | STRONG | **UNEVALUATED** |
| C-14 | Mechanically required joint distinctness | distinct kinematic roles need distinct locations | BM-002 3 at `[0,0,2.5]`; BM-003 3+3; PRB-03 3 at origin | **S04B** | no predicate; arrangement absent | not in jurisdiction | 5/6 | STRONG | **UNEVALUATED** |
| C-15 | Rigid-link non-degeneracy | a link between two joints has length | BM-002 crank throw = 0 | **S04B** | length is derived from two origins, never computed | not in jurisdiction | 1 case | MODERATE | **NOT ESTABLISHED** |
| C-16 | Repeated-member consistency | N members are N instances | BM-003 s04a 120° → s04b one point | **S03** | correspondence has no typed home | **not establishable** | 1 multi-instance case | CASE-LIMITED | **REPRESENTATION-INCOMPLETE** |
| C-17 | State/configuration physical realization | a named state is a distinct realisation | BM-002 crank fixed; BM-003 legs fixed; PRB-02 two identical states | **S04B** | nothing compares two `State`s; `expected_mobility` defaulted `[]` | not in jurisdiction | 3/6 | STRONG | **MODEL-LIMITED UNDER SUFFICIENT SUPPORT** |
| C-18 | Transition / path realization | a transition needs sampled motion | 0/6 carry a path | **schema** | s04b schema has no path field; declaration fabricated | self-fulfilling | 6/6 | STRONG | **UNSUPPORTED DETERMINISTIC COMPLETION** |
| C-19 | Spatial commitment preservation | a later stage may not silently contradict an earlier one | BM-003 s04a→s04b | **S04A→S04B** | no preservation mechanism; `invalidation_cone` unread | not in jurisdiction | 1 case + contract | MODERATE | **NOT ESTABLISHED** |
| C-20 | Unresolved → commitment gating | recognised uncertainty must bound commitment | 6/6 cases commit over their own diagnoses | **every boundary** | `UnresolvedDecision` never read back | gating failure | 6/6 | STRONG | **UNGATED** |
| C-21 | Independent engineering assurance | assurance must not be producer-local | every check co-located with its stage | **architecture** | planned `validation/` substrate never built | — | architecture | STRONG | **NOT ESTABLISHED** |
| C-22 | Metric / status construct validity | a metric must measure what it names | maturity has no S03/S04 term; predicates metric rewards fabrication | **evaluation layer** | `quality_profile` 32/32 keys s01/s02 | structural-as-engineering | 6/6 | STRONG | **UNEVALUATED** |

---

## §4 REQUIREMENT / CAPTURE CAPABILITIES

**C-01, C-02 — TYPE A, capture.** The facts never entered authoritative state, so no
downstream mechanism could have carried them.

- *"must not slip **or rotate**"* is one requirement in **all three** PRB-02 trials; the
  fixture splits it because translation and rotation are different freedoms, which is why
  its OBL-0003/OBL-0004 are separate.
- *"every time"* is merged into the return requirement in **all three** PRB-03 trials; the
  fixture's separate requirement is what becomes an obligation with
  `route_available: false`.
- Three fixture ambiguities have **no live counterpart in any trial**: the wall type and
  permitted fixings (PRB-01 — the reaction site for every load in that product), the
  signal-scope question (PRB-03), and the knock-disturbance magnitude (BM-003 — the reason
  its retention obligation is unverifiable).
- PRB-01's refill activity is typed `OPERATION` / `SERVICE` / `SERVICE` across three
  trials. The fixture raises exactly this as an ambiguity. **The model answers it
  differently each time and never records that it answered anything.**

**Root cause is architectural, not model.** `S01.completeness` (`s01.py:164-176`) requires
only that requirements and scenarios be non-empty and that two vocabularies be respected.
**No atomization or ambiguity-coverage property is defined in any contract**, so there is
nothing for a check to test. *(STRONG)*

**C-03 is the counterweight and it is real.** Where the source states a quantity, every
trial of every relevant case records `quantity_kinds` and `quantity_class` correctly, and
`"approximately 1 kg"` survives S02 with its qualifier intact. Scope caveat: BM-002's
80–100 mm appears as the s01 prompt's own worked example, so PRB-01 (*twenty* / *exactly
one*) and PRB-02 (18–40 mm) carry the weight of this claim. *(STRONG, scope-stated)*

---

## §5 PRODUCER-CONSUMER CONTINUITY

**The projection layer is not the filter.** `projection.py` is 21 lines and strips exactly
one family. Everything else in accumulated state is projected to every stage. **A fact
missing from a prompt is therefore never a persistence failure and almost never a
projection-layer failure** — it is a prompt-builder or whitelist decision.

| Boundary | View built by | Sufficient for its consumer? |
|---|---|---|
| S01→S02 | `project_for("s02")`, rendered whole | **yes**, and INV-002 correctly enforced |
| S02→S03 | full projection + candidate | **yes** |
| S03→S03B | `S03_OWNED` + `demands{LoadCase, Obligation}` | **yes** — `reacted_at_role` is available here |
| **S03→S04A** | `S03_OWNED` | **no** — `Requirement` excluded (C-05) |
| **S03→S04B** | `S03_OWNED`, re-projected | **no** — `Envelope` excluded (C-12), and 4/6 truncated |

**C-06, representation closure.** The `principle` field carries `CRANK_SLIDER`,
`SEPARATE_RETAINING_MEMBER`, `HARD_STOP` from S02 into S03 and exists in three
incompatible shapes. The s02 prompt contradicts itself — Rule 3 asks for a mapping *"for
each"* function class, PERMITTED VALUES says *"one of"*. The contract specifies no shape.
`candidate_distinctness_check` and `known_principle_check` **branch on dict, list and
string** — the implementation accommodates the ambiguity rather than resolving it.
*(STRONG)*

**A second, quieter continuity loss.** `principle_library` records for each family what it
*creates* — `CRANK_SLIDER → ["slider guidance", "two revolute joints"]`,
`HARD_STOP → ["a producing feature pair"]` — and its `depends_on_claims`, whose keys are
exactly the `capability_registry._CLAIM_ROUTE` keys. **`_render_families` emits only the
family name** (`s02.py:198-203`), and `route_for_claim` is imported twice and called zero
times. The knowledge layer's engineering content and its designed composition with the
route registry are both projected away at prompt-render time. *(STRONG)*

---

## §6 PHYSICAL / MECHANICAL REASONING

**C-07 — the mechanism's defining function lives in prose in four of six cases.**

| Case | Function | How it is represented |
|---|---|---|
| PRB-01 | the two gates are never open together | `BOD-0004.role` string; **no joint** to either gate |
| PRB-02 | the screw drives the traveling jaw | `IFC-0003` CONTACT; **no joint** |
| PRB-03 | the spring returns the pedal | `IFC-0003` COMPLIANT_INTERACTION; **no joint**; `JNT-0002` is FIXED |
| BM-002 | the crank drives the platform | joints exist, but input axis ∥ output axis and the input never moves |

**Split cause.** The **representation** component is real: `Interface` carries
`interaction_kind` and `nominal_status` and **no field expressing force or motion
transmission**, and no `BodyHypothesis` / `PhysicalInteractionHypothesis` family exists in
any contract, prompt or artifact — so a transmitting relation that is not a `Joint` has
nowhere typed to live. The **reasoning** component is also real: nothing prevented a
`Joint` from being emitted, and PRB-01's own `S3U-1003` correctly names the gap
(*"the exact kinematic pairing … is not specified"*). *(STRONG, multi-cause)*

**C-08 — load closure fails in every case, and the rule exists at every layer except the
one that could enforce it.** The s02 prompt states *"a load reacted against the product
itself has not been reacted."* `DESIGN_STATE_CONTRACT` derives *reaction* from the
terminal hop and *support* from a contact interface in a path. **Neither derivation is
implemented, and `reacted_at_role` participates in no check anywhere.** `load_case_check`
tests role *shape* (≥3 words, no underscore, not all-caps), so *"the clamp body"* and
*"the user's hands"* both pass. Downstream, `load_path_check` **would** flag `"NONE"`,
`"desk edge"` and `"arm"` as unknown hops — a genuine detection — but tests neither
externality nor cycles, and `["BOD-0001","BOD-0001"]` clears the two-hop minimum. *(STRONG)*

---

## §7 MOBILITY / RETENTION / BLOCKING

This chain is the clearest instance of the deterministic-authorship boundary.

**P3 bar.** Retention must be directional, physically localized, specific to a
disturbance, and release must change the maintaining interaction.

**P4A raw.** `blocked_direction: "NONE"` on 4/7 (BM-001), 4/4 (BM-002), 4/10 (PRB-01),
4/5 (PRB-02), 4/4 (PRB-03). `blocker_body` equal to the retained group's own body in
BM-001 BLK-0001 and **all four** BM-002 relations. `blocker_body: "NONE"` in PRB-01.
`defeat_specification: "None"` on 4 of 5 PRB-02 relations. And the DOF that most needs
blocking is unblocked in three cases — BM-001's lid `RZ`, BM-003's legs' `RZ`, PRB-03's
pedal `RZ`.

**P5 causal chain.**
1. `S03BMobilityAndAssembly.to_operations` (`s03.py:933-954`) creates only `LoadPath`,
   `AssemblyStep`, `UnresolvedDecision`. **Blocking relations are never stored as
   entities.** `relations_of` builds them in memory for the derivation alone.
2. `Op` cannot carry a RELATE payload (`patch.py:19-24`), and `blocked_by` is absent from
   `Contracts.families`, so an op naming it would be rejected `UNKNOWN_FAMILY`.
3. `derive_mobility` (`s03.py:267-339`) enumerates the domain from topology — **legitimate
   bookkeeping** — then dispositions. **Domain enumeration ends and disposition authorship
   begins at `s03.py:317`.**
4. The `else` branch at `:333-337` assigns `MAINTAINED_BY_CLASS` with
   `holding_class = "joint class of %s"` from the group's first joint, or the literal
   **`"joint class of no joint"`** when it has none. For BM-003 that is ~120 of 126 cells.
5. The derived dispositions carry `blocking_relation: <id>` — **a reference to an id that
   exists in no entity.**
6. **No later code corrects, rejects or overwrites a `MAINTAINED_BY_CLASS` entry.**
   `holding_class` and `derived_by` are written and read by nothing.

**P6 assurance.** `dof_totality_check` asks whether every domain triple appears exactly
once; `derive_mobility` emits exactly one entry per triple. **The check cannot fail on
derived output.** `blocking_relation_check` skips any disposition that is not
`BLOCKED_BY`, so a `MAINTAINED_BY_CLASS` entry is never examined. `_reference_problems`
does not traverse `dispositions`, so the dangling id passes validation.

**What the pipeline can claim about mobility:** that a total grid exists.
**What it cannot claim:** that any cell's disposition is supported by evidence, that a
BLOCKED_BY cell resolves to a real relation, or that the retention it describes is
testable. *(STRONG)*

**One reclassification carried forward.** `blocked_direction: "NONE"` is **prompt-permitted**
— `AXIS_DIRECTIONS` includes `NONE` and the s03b prompt offers that enumeration for the
field. The contract says direction and blocker are required together and that a blocking
fact without a direction cannot be tested. **This is a prompt-contract contradiction, not
a model error.** Self-blocking, by contrast, is invisible to every check: `blocker_body`
is only tested to *be* a Body. *(STRONG)*

---

## §8 TOPOLOGY → SPATIAL REALIZATION

The most important cross-package chain.

### 8.1 What each stage holds, receives and authors

**S03 stores** bodies, groups, joints (`parent_group`/`child_group`, `dof`,
`axis_direction`, `frame_ids: []`), interfaces, configurations (`expected_mobility: []`),
regions, load paths, assembly steps. **Joint incidence exists only as group→body; there is
no spatial content at s03, by design.** Repeated-member identity is free text.

**S04A receives** `S03_OWNED` plus a computed must-touch list. **The constraint is stated
at body-pair level, never at joint level.** S04A authors envelopes, region volumes, reach
results, assembly directions, elimination — and **no joint spatial fact; its schema has no
joint field.** Only `Envelope` is patched; regions and directions arrive via `_absorb`;
reach, elimination and scale become Python attributes and never enter state.

**S04B receives** `mechanism_projection` again — and **`S03_OWNED` does not contain
`Envelope`.** Verified directly: `Envelope` appears in **0 of 6** s04b prompts, and every
`Body` object carries only `{addresses_obligations, created_by_stage, entity_id,
instance_identity, role}` — no extent, no centre. The only `half_extent`/`centre` in those
prompts belongs to `FunctionalRegion.volume`.

Yet the prompt reads: *"Where each JOINT sits — its frame origin, **as a position in the
same coordinates as the arrangement you were given**"*, under the heading **"THE MECHANISM
AND ITS ARRANGEMENT"**.

### 8.2 The second mechanism — silent mid-JSON truncation

`_render` is `json.dumps(...)[:26000]`, a hard character slice with no marker.

| Case | block | `RigidGroup` | ends |
|---|---|---|---|
| BM-001 | 25,995 | **absent** | `…constraint is defeated.",` |
| BM-002 | 6,360 | present | complete |
| BM-003 | **26,000** | **absent** | `…"configuration": "CFG-0002", "derived_by":` |
| PRB-01 | 25,996 | **absent** | `…"blocker_body": "BOD-0001",` |
| PRB-02 | 25,995 | **absent** | `…{ "configuration": "CFG-0002",` |
| PRB-03 | 5,224 | present | complete |

**Four of six s04b prompts are syntactically invalid JSON, cut mid-value.** `RigidGroup`
sorts last under `sort_keys=True` and is the first family lost — while
`transitions[].moving_groups` is specified as *"rigid group ids from the input"*.

**The derived DOF grid consumes a substantial portion of the fixed prompt budget** —
BM-003's `MobilityExpectation` is 7 × 3 × 6 = 126 entries, each carrying a disposition,
`derived_by`, and either a `holding_class` or the blocking fields copied verbatim —
**and under the observed serialization order (`sort_keys=True`, so `RigidGroup` sorts
last) `RigidGroup` falls beyond the 26,000-character slice in four of six S04B prompts.**

**The stronger causal claim is not supported and is withdrawn.** Grid size alone does not
determine truncation: BM-001 has 4 groups × 2 configurations = **48** cells and truncates,
while BM-002 (48 cells, 6,360 chars) and PRB-03 (48 cells, 5,224 chars) do not. Other
content — notably the verbatim `defeat_specification` strings expanded across every
blocked DOF and configuration — contributes materially. Establishing the decomposition
would require a counterfactual measurement, which this audit does not perform.
*(MODERATE for the contribution; the sole-cause claim is not made.)*

### 8.3 Per-observation chains

| Observation | First causal break | Model component? |
|---|---|---|
| BM-001 joint outside its body | **consumer projection** — BOD-0003's envelope was not in the s04b input, and the block was truncated | **no.** The model could not place it inside a body it was never shown |
| BM-002 three joints at `[0,0,2.5]` | **consumer projection + missing invariant** | **partial** — see §8.4 |
| BM-002 zero-length crank | **missing physical invariant** — throw is implied by two origins and derived nowhere | consequence of the above |
| BM-003 s04a 120° → s04b one point | **consumer projection**, compounded by **deterministic derivation** (truncation) and **no commitment preservation** | **no.** The arrangement was withheld |
| BM-002 crank fixed while platform rises | **missing physical invariant + representation** | **yes** — §8.4 |
| BM-003 legs fixed across three configurations | **missing physical invariant + representation** | **yes** — §8.4 |

### 8.4 The model-reasoning question, resolved carefully

Applying the five criteria of §6 of the P4B brief:

**BM-002's collocated pivots — MODERATE, not a clean exemplar.** Criteria 1, 2 and 4 are
not cleanly met: the body extents existed in state but were **not projected**, and the
prompt's instruction to work "in the same coordinates as the arrangement you were given"
is materially contradicted by the arrangement's absence. What survives is narrower and
still real: **the *relative* distinctness of two joints in a serial chain is expressible
without any envelope**, since BM-002's block was untruncated and carried both joints with
distinct group pairs. The absent arrangement explains why the origins are wrong in
absolute terms; it does not explain why two links of a chain share a point.

**Three clean exemplars that need no envelope at all — STRONG:**

1. **BM-002's input coordinate does not move.** `JNT-0001` holds `0.0` in both
   `CFG-0001 (LOWERED)` and `CFG-0002 (RAISED)` while `JNT-0004` goes to `2.0`. The
   configurations, the joint ids and the schema field were all present; nothing in the
   prompt contradicts changing a number. **The rotary input the mechanism exists to serve
   is stationary across the only transition.**
2. **BM-003's leg joints hold `0 / 120 / 240` in all three configurations**, named
   *deployed*, *folded*, *released*. **The folding stand never folds.** No spatial input
   is required to notice that a fold must change a fold coordinate.
3. **BM-002's S03 topology places the input axis parallel to the output axis** —
   `JNT-0001` `RZ` about `+Z`, `JNT-0004` `TZ` along `+Z` — authored at S03, where the
   projection was complete and untruncated.

**Where the model is being blamed for the pipeline:** the absent arrangement (C-12, C-13),
the absent quantities (C-05), the missing swept-path field (C-18), the `NONE` direction
(C-09), `irrelevance: []`, `ELASTICITY` on rigid members, the vocabulary spread, and the
bare-string `principle`. *(STRONG)*

### 8.5 General conclusion

> **The spatial realization stage is not given the spatial arrangement its own prompt
> instructs it to work in; no enforced mechanism-independent invariant requires
> topologically distinct joints to remain geometrically distinct where their kinematic
> role demands it, or requires a joint origin to lie within the bodies it connects; a
> spatial commitment made at S04A does not bind S04B and contradicting one raises nothing;
> and context is bounded by a silent character slice rather than by content priority, so
> large derived content competes with the producer's own topology for a fixed budget and
> the topology is what is lost.** *(STRONG for the slicing mechanism and its observed
> effect; the attribution of the loss to any single content class is MODERATE — see
> §8.2.)*

---

## §9 STATE / TRANSITION REALIZATION

**C-17.** A `State` is `"STA-%s" % configuration` with a free `{joint: number}` map.
Nothing compares two `State` entities, and nothing ties a `Configuration` to the DOF that
realises it — `expected_mobility` is contract-required, requested by no prompt, and
defaulted `[]` (`s03.py:407`). PRB-02's `CFG-0002 "tightening"` and `CFG-0003 "holding"`
are byte-identical with an empty transition between them; BM-003's `CFG-0001` and
`CFG-0003` are coordinate-identical.

**C-18.** No transition in any case carries a path or sampling — **and the s04b schema has
no field for either.** The state nevertheless receives
`{"kind":"UNIFORM","samples":9,"adaptive":False,"interior_samples":7}`, fabricated at
`s04.py:306-308` from the module constant `SAMPLES = 9`, then validated by
`sampling_declaration_check`, which tests presence, non-adaptivity and
`interior_samples ≥ 1` — **the exact properties the code just wrote.**

**A sampling policy is not sampled-motion evidence.** The declaration asserts that a
9-sample sweep with 7 interior points was declared; it establishes nothing about whether
any motion was swept. *(STRONG)*

---

## §10 QUANTITATIVE CONTINUITY

**This is a consumer-sufficiency problem, not forgetting.** Stated precisely:

1. **Capture succeeded.** BM-002 records `quantity_class: BAND` for *"approximately
   80-100 mm"* and *"approximately 1 kg"* in all three trials; PRB-02 records BAND for
   18–40 mm in all three.
2. **Persistence succeeded.** The `Requirement` entities are present in the s02 typed
   input, read directly from the raw prompts.
3. **Projection excluded them.** `S03_OWNED` (`run_window2.py:78-79`) does not contain
   `Requirement`, and the s04a prompt states *"You receive ONLY the mechanism … You do not
   receive the original request."*
4. **The model reported truthfully.** `scale.note: "No absolute dimensions given"` is
   **true of s04a's own input.** This is not a model failure.
5. **The design anticipated the class of problem and does not detect this instance.**
   `run_window2.py:75-79` says such a gap *"is an interface failure to record"*, and
   `interface_gaps` records exactly three conditions — bodies exist, configurations exist,
   an ACCESS/APERTURE region names an actor. **It has no quantitative term.**
6. **No evaluator compares consumer responsibility against accumulated state.**
   `quality_profile` cannot help: all 32 maturity keys are S01/S02.

**Consequence.** PRB-02's discriminating obligation is spanning 18–40 mm, and its s04b
jaw joint moves `0 → 0.1` in relative units. The obligation is unevaluable at the only
stage that assigns extents. *(STRONG)*

---

## §11 UNRESOLVED / MATURITY / COMMITMENT

**The distinction the brief asks for is decisive here, and the evidence is one-sided.**

**The model recognises the problem.** In the same file that commits the defect:

- PRB-02 `s03b` emits `BLK-0001`/`BLK-0004` asserting mutual grounding **and** `S3U-1001`:
  *"the anchor nut is not fixed to anything. Thus, the assembly is not grounded."*
- BM-002 `s03b` emits `BLK-0001` with `promised_features: ["fixed to world"]` **and**
  `S3U-1001`: *"no explicit fixity to ground is modeled for the housing (BOD-0001)"* —
  and `blocks` all four of its own relations.
- BM-003 `s03b` `S3U-1001`: *"The load paths reference the ground but no ground body is
  modeled."*
- PRB-01 `S3U-1003` names the missing kinematic pairing that is C-07's exact defect.
- PRB-03 `S3U-1001` correctly names the unblocked `+Z`, `RX`, `RY`.

**The pipeline does not use the recognition.** `UnresolvedDecision` is created by s02, s03
and s03b as a plain CREATE and **read back by nothing** — no check, no stage input, no
gate. It has no severity field. Maturity is written (`Envelope` PROVISIONAL, `LoadPath`
hard-set to `"HYPOTHESIS"`, outside the contract vocabulary) and **no check reads any
maturity field**, contrary to `DESIGN_STATE_CONTRACT`'s *"A check declares the minimum
maturity of its inputs."*

**Progression is unaffected at every layer.** All three runners share the pattern:
`declared_incompleteness` is recorded as a failure row and `state.apply()` runs anyway;
`run_window2.py:431` proceeds to s04 on `("SUCCESS", "CONTRACT_INCOMPLETE")` with a
documented rationale. Two of six cases ran S03/S04 on a candidate whose own
`evidence_route_verdict.available` is `false`. `selection_gate_check` iterates
`SelectionDecision`, which no code creates. `elimination` is never stored.
**`SAFE_REJECTION` and `FALSE_ACCEPTANCE` have no emitter.**

**Classification, stated conditionally.** *In cases where the model explicitly identifies
the same engineering defect that the design simultaneously commits, the failure is
commitment/gating rather than failure to recognise the issue.* Five such cases are
enumerated above. **This is not a claim that the model always recognises its own errors** —
§8.4 records three defects the model committed with no accompanying diagnosis, and C-01,
C-02 and C-07 are failures of recognition, not of gating. What is established is that a
recognition capability exists, is sometimes exercised precisely, and has no consequence
anywhere in the pipeline. *(STRONG for the conditional claim; the general claim is not
made.)*

---

## §12 DETERMINISTIC AUTHORSHIP BOUNDARY

The boundary carried forward exactly from P5 §6 and §7.

| Derivation | Anchor | Evidence it derives from | Class |
|---|---|---|---|
| DOF domain enumeration | `s03.py:342-349` | topology | **LEGITIMATE BOOKKEEPING** |
| `BLOCKED_BY` / `INTENDED` / `IRRELEVANT_BECAUSE` | `s03.py:320-332` | authored relations, joint class, authored irrelevance | **LEGITIMATE LOGICAL CONSEQUENCE** |
| **`MAINTAINED_BY_CLASS`** | **`s03.py:333-337`** | **absence of evidence** | **UNSUPPORTED AUTHORSHIP** |
| blocking-field aliases | `s03.py:67-95` | the model's own words; recorded; *"a field that is absent stays absent"* | **LEGITIMATE BOOKKEEPING** |
| **`sampling_declaration`** | **`s04.py:306-308`** | **the constant `SAMPLES = 9`** | **UNSUPPORTED AUTHORSHIP** |
| `frame_ids: []`, `expected_mobility: []`, `nominal: "NOMINAL"`, `kind: "OPERATIONAL"`, `maturity: "HYPOTHESIS"`, `free_dof` axis→Z | `s03.py:393,401,405,407,433,102` | nothing | **UNSUPPORTED DEFAULTS** |
| AABB overlap, swept hulls, assembly hulls | `s04.py:48-99, 437-649` | the model's own numbers, conservatively | **LEGITIMATE LOGICAL CONSEQUENCE** |

**The general statement.** Deterministically enumerating a complete domain is legitimate
and valuable — it is what makes an omission detectable. Deterministically assigning an
engineering *disposition* to a cell for which no evidence exists is authorship, and it
converts "nothing is known" into "a joint class holds this". The same distinction
separates a sampling *policy* from sampled-motion *evidence*. **In both cases the
manufactured value is subsequently validated by a check that tests the property the
manufacturing code guarantees, so the pipeline confirms its own completion.** *(STRONG)*

---

## §13 EVALUATOR CONSTRUCT VALIDITY

**What current evaluation validly establishes** *(and this is not nothing)*:

- that a response parsed, satisfied its stage's structural contract, and resolved its
  entity-level references;
- that no metric magnitude appears at S03; that every interface is classified; that the
  joint graph is **connected**; that the assembly precedence relation is **acyclic**;
- that declared body pairs are not placed apart; that swept hulls do not enter keep-outs;
  that an insertion path is clear **in the configuration produced by the preceding steps**;
- that a claimed clearance is `NOT_VERIFIED` rather than `FAIL` when boxes overlap —
  conservatism correctly implemented;
- that source text never reaches S02; that no candidate carries a rank or score;
- that contracts parse, cross-reference and do not drift from the status enum.

**What it does not establish:**

- that a joint lies where its bodies meet, or that two joints differ;
- that a load reaches anything outside the product;
- that a named state is physically distinct from another;
- that any DOF disposition is supported by evidence;
- that a declared transition was ever swept;
- that a spatial commitment survived to the next stage;
- **any engineering property of S03 or S04 output as *maturity*** — all 32
  `quality_profile` keys are S01/S02, and `compare_maturity` structurally cannot load
  Window 2 because it requires `s01.json`/`s02.json`.

**Status semantics, stated precisely.** In the audited aggregation path
(`build_pipeline_dashboard.py:862-905`) `status` is assigned solely from the recorded
**execution status**; `FAIL` is assigned only for `RESPONSE_TRUNCATED`, `SCHEMA_FAILURE`,
`RESPONSE_PARSE_FAILURE` and `RAISED`; `CHECK_FINDING` enters only as an integer count,
read once, and can move `PASS → WARNING` and nothing further. `SUCCESS` means the provider
returned, the text parsed, `to_operations` did not raise, `state.validate` was clean and
`completeness()` was empty. **It carries no engineering claim.**

**One metric inverts the architecture's own principle.**
`acceptance_contracts_with_predicates` scores BM-001 t1's fabricated *"1000 cycles / 5N /
between 2N and 10N / ABS via injection molding / 30 seconds"* at **1.0**, and BM-001 t2's
honest `[]` at **0.0** — from an input whose every requirement carries
`quantity_class: NONE`. `SAFE_REJECTION` is defined as *"correct behaviour, never
penalised. Penalising it teaches overclaiming."* *(STRONG)*

**Two structural gating facts.** `ver3-boundaries.yml:33` discovers `ver3/tests/meta` only,
so the single behavioural test — which covers S01→S02 and no stage where any physical
defect occurs — **never runs in CI**. And the workflow's final step fails if
`ver3/assy_v3/stages` exists, which it does, while the meta-test governing the same rule
was rewritten to permit contracted stages. *(STRONG)*

---

## §14 DEMONSTRATED STRENGTHS, WITH SCOPE

| Strength | Demonstrated scope |
|---|---|
| **Absence is never success** | dashboard: five distinct absence statuses plus a self-declared-incompleteness class, with a legend |
| **Conservatism in spatial verdicts** | S04: no-overlap proves clearance, overlap proves nothing; every spatial check reports NOT_VERIFIED, never FAIL. **No manufactured failures anywhere** |
| **Real geometric computation** | swept hulls with interior sampling; assembly paths against the *partially built* configuration — the harder and correct question |
| **Graph connectivity as a mechanical property** | `simulation_completeness_check`, all cases |
| **Cross-validated irrelevance** | the one disposition not checkable from the joint graph is checked against LoadCases |
| **Quantity extraction and qualifier preservation** | S01, every trial where the source states a quantity; strongest on PRB-01 and PRB-02, which are not in the prompt |
| **Explicit unresolved reasoning** | 6/6 cases; several correctly name the defect the same file commits |
| **Deterministic exhaustive bookkeeping** | DOF *domain* enumeration; blocking-field alias binding with recorded renames and *"a field that is absent stays absent"* |
| **Worst-status-wins within an evidence tier** | `build_pipeline_dashboard.py:362-366`, explicitly to stop a pass masking an incomplete sibling |
| **Provider and run provenance** | model substitution, temperature requested vs sent, clamp, truncation and reasoning-content presence all recorded per call |
| **No response repair anywhere** | 59/59 stored artifacts byte-identical to `response.raw_text`; no fence stripping, no salvage |
| **Documented willingness to narrow a claim** | a check that produced *"48 findings, 0 true positives"* was rewritten; an actor rule with *"four findings and no true positives"* was narrowed; `source_audit` keeps a reviewed-and-fixed register |
| **Rigorous meta-test suite** | within its jurisdiction: bidirectional enum↔contract drift, entity-family consumer justification, single package path incl. symlinks, source hashes, an independently-blocking freeze gate |

---

## §15 CASE-LIMITED ANOMALIES — NOT ARCHITECTURE EVIDENCE

- **BM-001 t1's fabricated numeric predicates** (1000 cycles, 5N, ABS). Its siblings emit
  `[]` (t2) and `X/Y/Z` placeholders (t3). The general statement is *instability of the
  acceptance-predicate strategy*, not "the model fabricates numbers".
- **PRB-02's `"desk edge"` free string.** One case. Generalises only to C-10 — that an
  external participant has no typed home. Its propagation into the s04a must-touch list is
  a real shared-code path and *is* general.
- **BM-003 t3's truncation.** One record; obligation-set inflation meeting the 8192 cap.
- **BM-003's repeated-member collapse.** BM-003 is the only multi-instance case in the
  corpus. C-16 is marked CASE-LIMITED for that reason.
- **BM-002's parallel input/output axes and zero-length crank.** One case each; the general
  statements are C-07 and C-14/C-15.
- **Vocabulary spread** (`configuration.kind` 9 values, `access_side` 3 systems,
  `approach_side` 6 forms, `locator` 9 conventions, `instance_identity` 6). These are
  **unconstrained fields** — the s01 prompt gives no `locator` format and no `block_scopes`
  vocabulary; `Configuration.kind` is not a contract field at all. Reclassified as
  representation divergence, not model inconsistency.
- **Optional-field absences** (`promised_features`, `self_locking`, `derivation_premises`,
  `involves_actors`, `block_scopes`) — compliance, withdrawn as defects.

---

## §16 WINDOW-2 EVIDENTIARY SCOPE

**What Window 2 validly tests:** the behaviour of S03, S03B, S04A and S04B given upstream
that satisfies the *current* S01/S02 parser, `to_operations` and `state.validate`. Its 24
artifacts are genuine live model output — byte-identical to `response.raw_text` — and its
S03/S04 findings about topology, blocking, load paths and placement are real evidence
about those stages under that substrate.

**What it does not establish:**

1. **Not a live end-to-end chain.** `seed_window1` replays `s01.json`/`s02.json` through
   `OfflineReplayProvider`.
2. **The substrate differs structurally from conforming live S02 output.** S03 received a
   six-key role→principle dict and prose `obligations_created`; a prompt-conforming live
   S02 emits **one** principle and **ids**. The channel carrying `CRANK_SLIDER` and
   `SEPARATE_RETAINING_MEMBER` into S03 does not exist in that form in live output.
3. **The staleness guard was bypassed by provider choice.** The fixtures carry
   `_meta.answers_prompt_sha256` precisely so pairing can be verified;
   `AgentAuthoredProvider` verifies it, `OfflineReplayProvider` does not, and Window 2 uses
   the latter. *(The audit separately confirmed by SHA that the six s01 fixtures do match
   the live s01 prompts — an external check, not a pipeline guarantee.)*
4. **One candidate per case.** `--candidates` defaults to 1, so `t1_CND-0001` is the CLI
   default, not a selection; two of six ran on a candidate whose evidence route is
   unavailable.
5. **Part of the state is harness-authored.** The DOF grid and all three absorbed geometry
   fields are written by `run_window2.py`, not by a stage.

*(STRONG)*

---

## §17 SYSTEM-LEVEL CONCLUSIONS — the fifteen questions

1. **Does S01–S04 behave as progressive enrichment?** In its additive half, yes —
   purely CREATE, nothing deleted or overwritten. In its *consumer* half, no: the value of
   accumulation is realised only if consumers see what accumulated, and two boundaries are
   governed by a whitelist that omits what the consumer needs. *(STRONG)*
2. **Genuinely lost vs not exposed?** **Genuinely never captured:** requirement
   atomization, three ambiguity classes, any `BodyHypothesis`-like content. **Captured,
   retained, not exposed:** stated quantities at S04, the body arrangement at S04B, the
   principle library's `creates`/`depends_on_claims`. **Deliberately withheld and
   correct:** `SourceClause` at S02. *(STRONG)*
3. **Insufficient boundaries?** **S03→S04A** (no `Requirement`), **S03→S04B** (no
   `Envelope`; 4/6 truncated), and the **knowledge-layer→S02 prompt** boundary. *(STRONG)*
4. **Represented but operationally unused?** `UnresolvedDecision`, every maturity field,
   `holding_class`, `derived_by`, `reacted_at_role`, `expected_mobility`, `frame_ids`,
   `Joint.dof` (the derivation reads only `joint_type` + `axis_direction`), s04a
   `elimination` and `scale.absolute`, `invalidation_cone`, `SelectionDecision`,
   `SAFE_REJECTION`, `FALSE_ACCEPTANCE`. *(STRONG)*
5. **Legitimate deterministic derivations?** DOF domain enumeration; BLOCKED_BY / INTENDED
   / IRRELEVANT from authored facts; alias binding with recorded renames; all AABB, swept
   and assembly-path geometry. *(STRONG)*
6. **Unsupported deterministic claims?** `MAINTAINED_BY_CLASS` (`s03.py:333-337`) and
   `sampling_declaration` (`s04.py:306-308`), plus six unsupported field defaults. *(STRONG)*
7. **Where does the model genuinely fail with sufficient support?** BM-002's stationary
   input coordinate; BM-003's unchanged leg coordinates; BM-002's parallel input/output
   axes at S03; the four cases where a defining function has no structural realisation.
   *(STRONG)* BM-002's collocated pivots retain a narrower model component. *(MODERATE)*
8. **Where is the model blamed for the pipeline?** The absent arrangement, the absent
   quantities, the missing path/sampling field, the prompt-permitted `NONE`,
   `irrelevance: []`, `ELASTICITY` on rigid members, the unconstrained vocabularies, and
   the bare-string `principle`. *(STRONG)*
9. **Which uncertainties fail to control commitment?** All of them. *(STRONG)*
10. **Observable in state but unevaluated?** Joint origins vs body extents; two joint
    origins against each other; s04a envelopes vs s04b origins; two `State` coordinate
    maps; load-path terminus externality; load-path cycles; `blocker_body` vs the retained
    group's own body. **All are already read by some existing check, so the information is
    demonstrably reachable.** *(STRONG)*
11. **Impossible to evaluate for lack of representation?** Repeated-member correspondence
    (free-text `instance_identity` only), and *which* coordinate ought to change for a
    given configuration (`expected_mobility` defaulted `[]`). *(STRONG)*
12. **What does the evaluator establish?** §13, first list — structural conformance,
    referential integrity at entity level, and a genuine set of conservative geometric
    facts. *(STRONG)*
13. **What does SUCCESS / WARNING / maturity not establish?** Any engineering property of
    S03 or S04 output. `SUCCESS` is a machinery statement; `WARNING` is the ceiling an
    engineering finding can reach; maturity has no S03/S04 term. *(STRONG)*
14. **What generalises across BM and PRB?** C-01, C-02, C-06, C-07, C-08, C-09, C-10,
    C-11, C-12, C-17, C-18, C-20, C-21, C-22 all recur across unrelated cases or rest on
    contract-level impossibility. C-15, C-16 and C-19 do not yet. *(STRONG)*
15. **Minimum capability requirements before S05+** — §18.

---

## §18 MINIMUM CAPABILITY REQUIREMENTS BEFORE S05+

Capability requirements only. **No implementation, field, check, prompt or threshold is
specified**, and each is stated so that more than one design could satisfy it.

**R-1 — Consumer sufficiency must be established, not assumed.** For each stage boundary,
the pipeline must be able to demonstrate that the consumer's declared question is
answerable from what the consumer actually receives. *(C-05, C-12; questions 2, 3)*

**R-2 — Spatial realization must receive the spatial state it is asked to extend.**
A stage instructed to work in an established coordinate system must be given that system.
*(C-12, C-13, §8)*

**R-3 — Mechanically required distinctness must be expressible and establishable.**
Where a kinematic role requires two elements to occupy different locations, or a link to
have non-zero length, the pipeline must be able to state and settle that. *(C-14, C-15)*

**R-4 — A named state must be distinguishable from another by something other than its
name.** A configuration must be relatable to the freedom whose change realises it.
*(C-17, question 11)*

**R-5 — A spatial or engineering commitment must bind, or its contradiction must be
visible.** A later stage may revise an earlier commitment; it must not silently contradict
one. *(C-19; the unread `invalidation_cone`)*

**R-6 — Deterministic completion must be distinguishable from engineering authorship.**
Enumerating a domain and dispositioning a cell are different acts and must be separable in
the record. *(C-11, C-18, §12)*

**R-7 — A property that a deterministic derivation guarantees must not be the property its
assurance tests.** *(§7, §12, P6 §7)*

**R-8 — Recognised uncertainty must be able to bound commitment.** The pipeline already
produces high-quality recognition; it must be able to act on it. *(C-20, §11)*

**R-9 — At least one engineering property per stage must be established independently of
its producer.** *(C-21)*

**R-10 — Every relation the architecture treats as first-class must be addressable.** A
reference must resolve to something. *(C-10)*

**R-11 — A transmitting physical interaction must have a typed home.** *(C-07)*

**R-12 — A load must be able to terminate at something outside the product, and that must
be checkable.** *(C-08)*

**R-13 — Capture must be able to fail visibly.** Merging two obligations or silently
answering an ambiguity must be distinguishable from a correct minimal extraction.
*(C-01, C-02)*

**R-14 — One canonical shape per typed field, agreed by contract, prompt and consumer.**
*(C-06, C-09)*

**R-15 — A maturity or status claim must measure the thing it names, over the stages it
claims to cover.** *(C-22, §13)*

---

## §19 REMAINING UNRESOLVED QUESTIONS

1. Was `dof_totality_check` written against **model-authored** dispositions, so that the
   deterministic derivation removed its subject? *(UNRESOLVED)*
2. Is `S03_OWNED` intended to exclude `Requirement` and `Envelope` permanently, or is
   `interface_gaps`' missing quantity term the omission? *(UNRESOLVED)*
3. Was `MAINTAINED_BY_CLASS` intended as a default or a placeholder? The docstring calls
   the derivation *"the contract's own division of labour … finally implemented"* and does
   not mention the fallback. *(UNRESOLVED)*
4. Why does `_absorb` exist outside the patch layer when `EXTEND` is defined and validated?
   *(UNRESOLVED)*
5. Is the Oracle intended to remain display-only, or is it the missing independent
   evaluator? *(UNRESOLVED)*
6. Is `tests/window/` deliberately outside CI discovery, and why does the CI shell step
   still forbid a stages package the meta-test now permits? *(UNRESOLVED)*
7. Nothing emits `SAFE_REJECTION` or `FALSE_ACCEPTANCE`. Was an emitter planned at S12 —
   and if so, can the poles function when the stages that would raise them are S01–S04?
   *(UNRESOLVED)*
8. `principle_library.depends_on_claims` keys are exactly `capability_registry._CLAIM_ROUTE`
   keys, and `route_for_claim` is never called. Was automatic evidence-route derivation
   intended? *(UNRESOLVED)*
9. The assurance projection that `STAGE_PROGRESSION_CONTRACT:242-250` requires **before**
   S01 does not exist while all four stages do. What was built in its place? *(UNRESOLVED)*
10. `ver3/live_runs/deepseek/phase1_s01/` is classified HISTORICAL PRECURSOR from metadata
    only. Escalate if P-next needs the earlier prompt revision. *(UNRESOLVED)*

---

## §20 EVIDENCE INDEX

**Reports.** `P1_COMPLETE.md` · `P2_COMPLETE.md` · `P3_COMPLETE.md` ·
`P4A_COMPLETE.md` (§A–§H) · `P4A_CAPABILITY_GAP_SYNTHESIS.md` ·
`P5_COMPLETE.md` (§1–§19 + §20 addendum) · `P6_COMPLETE.md` (§1–§15).

**Contracts.** `STAGE_PATCH_CONTRACT.yaml:3-6,48-62,72,85-95,98-107,164-175` ·
`STAGE_PROGRESSION_CONTRACT.yaml:215-226,242-250` ·
`DESIGN_STATE_CONTRACT.yaml:99,135,330-342,344-364,372-382,400-421,434-447,496,510-525` ·
`docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md:1098-1113`.

**Raw artifacts.** `ver3/live_runs/window2/r_final/responses/<case>/t1_CND-0001/{s03,s03b,s04a,s04b}.json`
(24, all byte-identical to `model_run_records.json` `response.raw_text`) ·
`ver3/live_runs/deepseek/q6_fix/responses/<case>/t{1,2,3}/{s01,s02}.json` (35) ·
both `trials.json` · both `model_run_records.json` ·
`ver3/assy_v3/fixtures/responses/BM-00{1,2,3}/{s01,s02}.json` ·
`ver3/assy_v3/probes/PRB-0{1,2,3}/{s01,s02}.json` + `PRB-01/s02.pre_revision.json`.

**Implementation.** `state/projection.py:12,18` · `state/patch.py:15,19-24,46` ·
`state/design_state.py:90-95,105-119,122-137` · `stages/base.py:71-74,84,113-123` ·
`stages/s01_requirement_capture.py:164-176` ·
`stages/s02_obligation_and_candidates.py:97-99,198-203,309-320,356-385,394,407-409` ·
`stages/s03_topology_and_mobility.py:67-95,101-118,127,267-339,342-349,376-452,483-513,534-544,607-631,825-876,933-979` ·
`stages/s04_envelope_and_motion.py:16-21,184-196,225-235,268-272,293-309,311-342,345-347,350-374,377-381,401-434,503-520,523-603,652-671,674-687` ·
`knowledge/principle_library.py:34-163,174` · `knowledge/capability_registry.py:15-74` ·
`providers/status.py:50-51` · `providers/offline.py:36-52` ·
`providers/agent_authored.py:72-80` ·
`live_providers/deepseek.py:56,100,157-167,304-305` ·
`tools/run_window2.py:78-79,94-123,151-168,213-216,221-224,246-279,312,329-331,346-375,382-384,396,426-431`.

**Evaluators.** `tools/build_pipeline_dashboard.py:306-308,315-368,862-905,1195-1218,1470-1476,1620-1700,1720-1736` ·
`tools/quality_profile.py:395-432` · `tools/compare_maturity.py:64-104` ·
`tests/window/test_s01_s02_window.py:140-147` · `.github/workflows/ver3-boundaries.yml:33,41-47`.

---

---

## §21 AUDIT CLOSURE — CAPABILITY-REQUIREMENT TRACEABILITY

Narrow closure pass. **No new investigation.** After this section the audit is frozen.

| Req | Supporting capabilities | Confidence | Support class | Unresolved-question exposure | Standing |
|---|---|---|---|---|---|
| **R-1** consumer sufficiency established | C-05, C-12 | STRONG | shared code (`S03_OWNED`) + cross-case (2/2 quantity cases; 6/6 arrangement) | Q2 affects the *remedy*, not the requirement | **FINAL** |
| **R-2** spatial stage receives spatial state | C-12, C-13 | STRONG | shared code (0/6 `Envelope`) + cross-case | — | **FINAL** |
| **R-3** required distinctness expressible | C-14 (STRONG, 5/6); C-15 (MODERATE, 1 case) | STRONG | cross-case via C-14 | — | **FINAL** *(C-15 alone would not carry it)* |
| **R-4** a state distinguishable other than by name | C-17 | STRONG | cross-case (3/6) + contract (`expected_mobility` unused) | — | **FINAL** |
| **R-5** commitment binds or its contradiction is visible | C-19 | MODERATE | contract-level (`invalidation_cone` declared, unread) + 1 case | Q4 (`_absorb` outside the patch layer) bears directly | **PROVISIONAL** |
| **R-6** deterministic completion separable from authorship | C-11, C-18 | STRONG | shared code + 6/6 | Q3 affects intent, not the requirement | **FINAL** |
| **R-7** assurance must not test what the producer guarantees | C-11, C-18 | STRONG | shared code (two confirmed instances) | Q1 affects intent, not the requirement | **FINAL** |
| **R-8** recognised uncertainty can bound commitment | C-20 | STRONG | 6/6 + contract-level | — | **FINAL** |
| **R-9** ≥1 property per stage established independently | C-21 | STRONG | architecture-level | Q5 (Oracle's intended role) bears on the *mechanism* | **FINAL** *(mechanism open)* |
| **R-10** first-class relations addressable | C-10 | STRONG | contract-level impossibility | — | **FINAL** |
| **R-11** transmitting interaction has a typed home | C-07 | STRONG | cross-case (4/6) + contract | — | **FINAL** |
| **R-12** load terminates externally and checkably | C-08 | STRONG | 6/6 + contract | — | **FINAL** |
| **R-13** capture failure visible | C-01, C-02 | STRONG | cross-case **and** cross-trial | — | **FINAL** |
| **R-14** one canonical shape per typed field | C-06, C-09 | STRONG | contract-level + within-case trial flips | — | **FINAL** |
| **R-15** a maturity claim measures what it names | C-22 | STRONG | shared code (32/32 keys s01/s02) + 6/6 | — | **FINAL** |

**No requirement rests solely on a CASE-LIMITED capability.** C-16 (repeated-member
consistency) is CASE-LIMITED — BM-003 is the corpus's only multi-instance case — and is
therefore **deliberately not elevated to a standalone requirement**. It is carried as a
provisional sub-case of R-14, on the ground that repeated-member identity is currently
free text and any canonical-typing decision will have to address it.

**One requirement is PROVISIONAL: R-5.** Its non-case-limited support is the contract's
declared-but-unread `invalidation_cone`, and Q4 asks why an unguarded direct write exists
alongside a defined-and-validated `EXTEND`. The answer changes what "binding" can mean.

**Audit frozen at this point.** P1–P6 are reopened only if a specific architecture
decision requires one exact evidence anchor.

---

**P4B is COMPLETE AND FROZEN. No fix, prompt change, contract change, validator or
architecture revision is proposed in this document.**
