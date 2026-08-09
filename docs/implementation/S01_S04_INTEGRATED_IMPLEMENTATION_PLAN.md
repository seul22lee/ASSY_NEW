# S01–S04 INTEGRATED IMPLEMENTATION PLAN

**Status: PLAN. Nothing in this document is implemented.**

One coherent migration from the current S01–S04 system to the frozen architecture. Not a
patch sequence, not a defect list, not a benchmark-repair programme.

---

## 0. SCOPE AND NON-GOALS

**In scope.** `ver3/assy_v3/`, `ver3/contracts/`, `ver3/tools/`, `ver3/live_providers/`,
`ver3/tests/`, and the fixture corpus, insofar as each must move to the frozen architecture.

**Non-goals.**
- Not S05+.
- Not tuned to any benchmark, probe, product noun, mechanism family or provider.
- Not a validator catalogue; assurance is planned by claim class, not by check.
- Not final field names, APIs or prompt text — the freeze explicitly leaves these open.
- **No code, contract, prompt, validator or fixture is modified by this document.**

**Governing constraint (freeze §11):** benchmarks evaluate architecture capability; they do
not define it. No step in this plan is justified by a benchmark outcome, and no step's
success criterion is a benchmark score.

---

## 1. FROZEN ARCHITECTURE INPUTS

`S01_S04_ARCHITECTURE_FREEZE.md` governs. The load-bearing inputs:

- **FA-2/FA-3** authority classes A/B/C/D; class-A changes only via `CREATE`/`EXTEND`/
  `SUPERSEDE`/`INVALIDATE` with provenance, from any code whatsoever.
- **FA-5** premise change → dependent commitment loses unqualified authority.
- **FA-6/FA-7** two-source consumer sufficiency, derived from contracts upstream of the
  consuming stage; a stage may widen, never narrow.
- **FA-4/FA-8** derived only from sufficient typed premises; absence never becomes assertion.
- **FA-10** `ENGINEERING_ESTABLISHED` only from an ENGINEERING-CONSEQUENCE check.
- **FA-11** no positional truncation; budget failure is a recorded condition.

---

## 2. CURRENT → TARGET DELTA

Mechanism IDs follow the proposal's migration units (§24), extended where the freeze added
mechanisms.

### M-1 — Accumulated DesignState / authority semantics

| | |
|---|---|
| **Current** | `state/design_state.py` holds one flat `entities` dict plus `by_family`. `apply()` handles `CREATE` and `EXTEND` only; `EXTEND` is an unguarded `dict.update` (`:135-136`) with no owner check. `patch.py` declares `invalidation_cone` (`:46`) and nothing reads it. No authority class exists; a spatial commitment and a cache line are the same kind of thing. |
| **Target** | Every value carries an authority class. Class-A mutation passes one boundary implementing four operations with provenance and premise references. Class B carries a premise set and is recomputable. `invalidation_cone` becomes operative. |
| **Why** | FA-2, FA-3, FA-4, FA-5. Without authority classes there is no definition of "illegal write" to enforce. |
| **Affected** | `state/design_state.py`, `state/patch.py`, `contracts/DESIGN_STATE_CONTRACT.yaml`, `contracts/STAGE_PATCH_CONTRACT.yaml`, `contracts/PROVENANCE_CONTRACT.yaml` |
| **Depends on** | nothing — this is the foundation |
| **Risk** | **high** — every other unit sits on it; a wrong class boundary propagates everywhere |
| **Completion established by** | property tests: a class-A write outside the boundary raises; `SUPERSEDE` retains both values; a class-B value with an incomplete premise set is not produced |

### M-2 — Canonical representation closure

| | |
|---|---|
| **Current** | 41 families across 17 contracts. Known contradictions: `principle` in three shapes; `blocked_by` non-addressable; `BodyHypothesis`/`PhysicalInteractionHypothesis` required by a stage contract, defined by none, owned by none, produced by no code; `required_by_actors`/`reach_targets` defined only in prompt text; `addresses_obligations` divergent; `MobilityExpectation` authorship ambiguous; 14 dangling references. |
| **Target** | One semantic type, one owner, one authoring responsibility and one consumer interpretation per concept. Every referenceable entity has a resolvable id. Every field declares mutability and, where applicable, its semantic referent. |
| **Why** | FA-12, R-10, R-14 |
| **Affected** | all of `contracts/`, principally `DESIGN_STATE_CONTRACT.yaml`, `ENTITY_FAMILY_AUDIT.yaml`, `STAGE_OWNERSHIP_MATRIX.yaml`, `contracts/stages/S01..S04_CONTRACT.yaml` |
| **Depends on** | M-1 for the authority-class vocabulary |
| **Risk** | **medium-high** — contract sprawl (see R-1 in §22) |
| **Completion established by** | every family resolves to exactly one owner; no dangling reference; no field carries two shapes; a structural check proves every spatial field declares a frame and every reference declares a target family |

### M-3 — Two-source Consumer Sufficiency

| | |
|---|---|
| **Current** | `state/projection.py` is 21 lines. It strips exactly one family (`SourceClause`) for non-S01 stages and passes everything else. The real boundary is `tools/run_window2.py:78-79`, a hand-written tuple `S03_OWNED` that excludes `Requirement`, `LoadCase` and `Envelope`. There is no declaration of need anywhere, and no way to detect that a class is missing. |
| **Target** | A required minimum derived from two contracts, a view built to satisfy it, an independent sufficiency assessment, and a recorded `ConsumerView` distinguishing UPSTREAM INSUFFICIENCY from PROJECTION FAILURE. |
| **Why** | FA-6, FA-7 — the dominant recurrent continuity failure |
| **Affected** | `state/projection.py` (replaced), a new view-construction module, every stage contract, `tools/run_window2.py`, `tools/run_window.py` |
| **Depends on** | M-2 (the declarations are the input) |
| **Risk** | **high** — the premise mapping could become another manual whitelist (R-2 in §22) |
| **Completion established by** | removing a required class from state produces UPSTREAM INSUFFICIENCY; removing it from the view alone produces PROJECTION FAILURE; a stage declaring less than the derived minimum fails contract validation |

### M-4 — Controlled authoritative mutation and dependency binding

| | |
|---|---|
| **Current** | Three direct writes into `state.entities` in `tools/run_window2.py:361-375` — `volume`, `insertion_direction`, `frame_origin` — with no `Op`, no validation, no ownership check and no provenance. Three side-channel attributes on the state object (`s04a_reach`, `s04a_elimination`, `s04a_scale`, `:368-370`), of which reach results and elimination are engineering conclusions with no entity, no id and no provenance. |
| **Target** | All of the above become class-A facts written through the controlled boundary, with provenance and premise references. |
| **Why** | FA-3. These are spatial commitments and engineering conclusions, not bookkeeping. |
| **Affected** | `tools/run_window2.py`, `tools/run_window.py`, `state/design_state.py` |
| **Depends on** | M-1, and M-2 for the families that `elimination` and `reach` must become |
| **Risk** | **medium** — the reason the direct write exists may be that the patch layer could not express the update (P4B Q4, unresolved). If so, `EXTEND`'s expressiveness must be fixed, not bypassed |
| **Completion established by** | a static check finds no assignment into class-A storage outside the boundary; every previously-absorbed field carries provenance |

### M-5 — Commitment and reopening semantics

| | |
|---|---|
| **Current** | No commitment class. No supersession. `invalidation_cone` declared and unread. The selection gate is nominal: no `SelectionDecision` is emitted anywhere, and `SAFE_REJECTION` / `FALSE_ACCEPTANCE` have no emitter in the corpus. |
| **Target** | Commitment classes; supersede-with-reason; premise-change propagation; a gate with externally computed preconditions; both poles reachable. |
| **Why** | FA-5, freeze §7 |
| **Affected** | `state/patch.py`, `state/design_state.py`, `tools/run_window2.py`, `contracts/STAGE_PROGRESSION_CONTRACT.yaml`, `contracts/STATUS_SEMANTICS.yaml` |
| **Depends on** | M-1, M-4; the gate additionally on M-8 |
| **Risk** | **medium** — propagation complexity (R-5 in §22) |
| **Completion established by** | superseding a `COMPARABLE` value marks a dependent selection non-authoritative; a gate cannot fire on a self-authored precondition verdict |

### M-6 — Mobility domain / disposition separation

| | |
|---|---|
| **Current** | `stages/s03_topology_and_mobility.py:267-339`. Domain enumeration and disposition assignment are one function; the `else` branch at `:333-337` writes `MAINTAINED_BY_CLASS` with `holding_class` composed from the joint type of the first joint whose child is the group, or the literal string `"joint class of no joint"` when there is none. Called from `tools/run_window2.py:257`, applied as a patch with `provenance={"provider": "deterministic"}`. A check then tests the totality that this code guarantees. |
| **Target** | Domain enumeration is class B, reported as BOOKKEEPING. Dispositions derive only from authored premises and reference them. Cells with no premise become `UNDISPOSITIONED`, naming what is missing. **Disposition completeness** becomes a reported engineering quantity. |
| **Why** | FA-4, FA-8; the clearest instance of absence becoming assertion |
| **Affected** | `stages/s03_topology_and_mobility.py`, `contracts/stages/S03_CONTRACT.yaml`, `DESIGN_STATE_CONTRACT.yaml` |
| **Depends on** | M-1, M-2, M-7 (constraint relations are the premises) |
| **Risk** | **low-medium** — disposition coverage will fall sharply and visibly; that is the correct result and must not be read as regression |
| **Completion established by** | a DOF cell with no covering relation and no authored irrelevance yields `UNDISPOSITIONED`; no disposition exists whose premise does not resolve |

### M-7 — Physical-effect obligations, interactions, constraint relations, reaction sites

| | |
|---|---|
| **Current** | No typed home for transmission — it appears in prose in four of six cases. `blocked_by` is a nested non-addressable structure. Reaction sites do not exist as a type, so a load path cannot terminate outside the product. `BodyHypothesis`/`PhysicalInteractionHypothesis` are required by the S03 contract and produced by nothing. |
| **Target** | `PhysicalEffectObligation` (S02, role level) → `PhysicalInteraction` (S03·B) with reference-checkable discharge; addressable `ConstraintRelation`; typed `ReactionSiteRequirement` marked external/internal from the scenario boundary. |
| **Why** | R-10, R-11, R-12 |
| **Affected** | `stages/s02_obligation_and_candidates.py`, `stages/s03_topology_and_mobility.py`, `contracts/stages/S02_CONTRACT.yaml`, `S03_CONTRACT.yaml`, `DESIGN_STATE_CONTRACT.yaml`, `ENTITY_FAMILY_AUDIT.yaml` |
| **Depends on** | M-2 |
| **Risk** | **medium** — S02's output grows; must not become a mechanism specification |
| **Completion established by** | every effect obligation is discharged by a named interaction or is explicitly open; every constraint relation is addressable and its provider resolves; every load path terminates at an external site or is recorded open |

### M-8 — Topology→spatial continuity and S04·A→S04·B refinement

| | |
|---|---|
| **Current** | `S03_OWNED` excludes `Envelope`; `Envelope` appears in **0 of 6** S04·B prompts while the prompt instructs the model to place joints "in the same coordinates as the arrangement you were given". `stages/s04_envelope_and_motion.py:377-381` renders with `json.dumps(...)[:26000]` — a silent positional slice that drops `RigidGroup` (which sorts last) in four of six prompts. `:293-309` writes a `sampling_declaration` from the constant `SAMPLES = 9` (`:347`), then a check validates the sampling property that constant guarantees. |
| **Target** | S04·B receives the selected candidate's arrangement and *extends* it. Required-distinctness declarations from S03. Motion evidence level recorded from the computation performed, never from a constant. No positional slicing. |
| **Why** | FA-6, FA-11, FA-8, R-2, R-3 |
| **Affected** | `stages/s04_envelope_and_motion.py`, `stages/s03_topology_and_mobility.py`, `tools/run_window2.py`, `S03_CONTRACT.yaml`, `S04_CONTRACT.yaml` |
| **Depends on** | M-3 (the arrangement must be a derived required premise), M-1, M-5 |
| **Risk** | **medium-high** — views may exceed context (R-3 in §22) |
| **Completion established by** | the arrangement is present in the S04·B view in every run or the run records an insufficiency; no serialization path truncates positionally; the evidence level is a function of the computation, provably not of a constant |

### M-9 — Independent assurance and status semantics

| | |
|---|---|
| **Current** | Every Layer-B check is co-located with its stage and invoked by the same tool. Two checks test properties the producing code guarantees. `tools/build_pipeline_dashboard.py:862-905` maps execution status to a badge and downgrades OK→WARN on any finding, merging execution and engineering into one axis. `tools/quality_profile.py:399-419` defines 32 maturity metrics, **all of them S01/S02** — the construct has no term for the stages where the physical defects occur. `SAFE_REJECTION` and `FALSE_ACCEPTANCE` have no emitter. |
| **Target** | A separate assurance layer reading committed state, never invoked by a producing stage; every check declares independence degree and claim class; four status constructs reported separately; only ENGINEERING CONSEQUENCE contributes to `ENGINEERING_ESTABLISHED`. |
| **Why** | FA-10, R-7, R-9, R-15 |
| **Affected** | new assurance module; checks removed from `stages/*.py`; `tools/build_pipeline_dashboard.py`, `tools/quality_profile.py`, `tools/compare_maturity.py`, `contracts/STATUS_SEMANTICS.yaml`, `GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml` |
| **Depends on** | M-1…M-8 **substantially stable** — assurance must not be finalized against moving state semantics |
| **Risk** | **medium** — assurance stays producer-coupled by habit (R-6 in §22) |
| **Completion established by** | no check is reachable from a stage module; every check declares both attributes; no aggregate mixes execution with engineering |

---

## 3. MIGRATION PRINCIPLES

1. **Semantics before syntax.** Contracts and state semantics land before prompts. A prompt is
   a rendering of a contract, never its definition.
2. **One authority model at a time.** Old and new authority semantics must never both be live
   (§5).
3. **Coherent units, not defect-shaped patches.** No implementation unit exists because of one
   observed failure.
4. **Visible regression is acceptable.** Disposition coverage and establishment counts will
   fall when absence stops being asserted. That is the migration working.
5. **Regenerate rather than bridge**, wherever a legacy shape encodes a semantics the freeze
   rejects (§21).
6. **Broad regression, never micro-iteration** (§20).

---

## 4. IMPLEMENTATION UNITS

Nine units. Each is coherent on its own terms and independently reviewable.

| Unit | Name | Mechanisms | Primary subsystems |
|---|---|---|---|
| **U-1** | **Foundation — state and authority** | M-1 | `assy_v3/state/` |
| **U-2** | **Canonical contract model** | M-2 | `contracts/` |
| **U-3** | **Consumer view system** | M-3 | new view module; `state/projection.py` retired |
| **U-4** | **Controlled mutation and dependency binding** | M-4, part of M-5 | `state/`, `tools/run_window*.py` |
| **U-5** | **Physical reasoning representation** | M-7 | `stages/s02*`, `stages/s03*`, contracts |
| **U-6** | **Mobility** | M-6 | `stages/s03*` |
| **U-7** | **Spatial commitment and refinement** | M-8 | `stages/s04*`, runners |
| **U-8** | **Commitment and gating** | rest of M-5 | `state/`, runners, progression contract |
| **U-9** | **Assurance and status** | M-9 | new assurance layer; dashboard and profile tools |

**Cross-cutting, not separate units** — each lands *inside* the unit that makes it possible:

- **prompt migration** (§15) lands with U-5/U-6/U-7 per stage, never before U-2 and U-3;
- **runner/provider migration** (§16) lands with U-4;
- **fixture migration** (§17) lands after U-2 and U-3, before the U-9 evidence claims;
- **test architecture** (§18) is built incrementally with every unit.

---

## 5. DEPENDENCY DAG

```
        U-1 Foundation ──────┬──────────────► U-4 Controlled mutation
             │               │                       │
             ▼               │                       ▼
        U-2 Contracts ───────┼──────────────► U-8 Commitment / gating
             │               │                       ▲
             ├──► U-3 Views ─┴───────────────────────┤
             │        │                              │
             ├──► U-5 Physical reasoning             │
             │        │                              │
             │        ▼                              │
             └──► U-6 Mobility                       │
                      │                              │
        U-3 ─────────►U-7 Spatial / refinement ──────┘
                      │
                      ▼
                 U-9 Assurance / status   ◄── requires U-1…U-8 substantially stable
```

**MUST LAND BEFORE**

| This | Before this | Why |
|---|---|---|
| U-1 | everything | the authority-class vocabulary is the substrate |
| U-2 | U-3 | the required minimum is derived from contract declarations |
| U-2, U-3 | any prompt rewrite | a prompt renders a contract; rewriting first re-creates prompt-only fields |
| U-5 | U-6 | constraint relations are the premises dispositions derive from |
| U-3 | U-7 | S04·B cannot extend an arrangement it does not receive |
| U-7 | U-8 | the gate operates on comparable spatial evidence |
| U-1…U-8 | U-9 | assurance must not be finalized against changing state semantics |

**CAN LAND TOGETHER**

- U-1 + U-2 — they co-define the authority classes and their declarations.
- U-5 + U-6 — one S03 semantic change; splitting them leaves dispositions citing premises
  that do not yet exist.
- U-7 + the S04 prompt migration — the prompt is meaningless without the arrangement.

**MUST NOT LAND IN A TEMPORARILY INCONSISTENT STATE**

> **U-1 and U-4 must land as one change.** The moment the controlled boundary exists,
> `_absorb`'s three direct writes must already be gone. A window in which both the controlled
> path and an uncontrolled path can write class-A facts is precisely the condition the
> architecture exists to eliminate, and it would be undetectable from the outside — the state
> would look correct.

> **U-2 and U-3 must not straddle a release** in which some stages derive their minimum and
> others use `S03_OWNED`. Two consumer-sufficiency definitions live at once is the drift the
> falsification pass just removed from the documents; it must not be reintroduced in code.

---

## 6. SHARED DESIGNSTATE MIGRATION *(U-1)*

- **Authority class on every value.** Class is a property of the *field*, declared in the
  entity contract, not inferred at runtime.
- **One mutation boundary** implementing `CREATE` · `EXTEND` · `SUPERSEDE` · `INVALIDATE`.
  `EXTEND` gains what it currently lacks: an owner check, a "field not already present"
  check, and provenance. Its current form (`design_state.py:135-136`) is an unguarded
  `dict.update` and must not survive.
- **Premise references become first-class.** A derived value stores the ids of the values it
  was computed from. This is what makes FA-5 computable at all.
- **`invalidation_cone` becomes operative** — currently declared at `patch.py:46` and read
  nowhere.
- **Class-B storage is separated** from class-A storage so that "recompute" is meaningful and
  so that a derived value cannot be mistaken for an authored one on inspection.
- **Reference integrity replaces the heuristic.** `design_state.py:105-119` currently
  identifies references by key suffix plus five hard-coded names, and validates with
  `ref[:4].isupper() and "-" in ref`. Targets come from the contract instead.

---

## 7. CANONICAL CONTRACT MIGRATION *(U-2)*

Per entity family, one declaration of each: **canonical identity** · **owner** · **authority
class per field** · **extendability** (which stage, which field, once) · **supersession
rules** · **provenance obligations** · **maturity vocabulary** · **unresolved-status
semantics** · **semantic dependencies per field** · **relation addressability** · **reference
targets**.

Per stage, one declaration of: **responsibility** · **engineering questions** · **required
reasoning premise classes** · **permitted outputs** · **prohibited decisions**.

**Contradictions resolved, not carried:**

| Contradiction | Resolution |
|---|---|
| `principle` in three shapes (bare string / parallel arrays / mapping) | one type: a mapping from function class to principle family. A single-principle candidate is a one-entry mapping. **The fixtures, not the live model, violate the current prompt's stated vocabulary** — so the fixtures are regenerated, not the rule relaxed |
| `blocked_by` non-addressable | becomes `ConstraintRelation` with an id |
| `BodyHypothesis` / `PhysicalInteractionHypothesis` — required by S03's contract, defined by no contract, owned by no stage, produced by no code | **both names retired.** Replaced by `PhysicalEffectObligation` (S02) and `PhysicalInteraction` (S03·B) |
| `required_by_actors`, `reach_targets` defined only in prompt text | promoted into the functional-region contract |
| `addresses_obligations` divergent between contract and prompt | one field, one meaning, required wherever a stage creates an entity to discharge an obligation |
| `MobilityExpectation` authorship ambiguous | split by authority class: domain is B, disposition is A-or-B with a premise reference |
| stale status vocabularies across `STATUS_SEMANTICS.yaml` and the dashboard | one vocabulary, four constructs, no aggregation across constructs |
| 14 dangling references | resolved or removed; a structural check prevents recurrence |

**No compatibility shim is written for any of these.** Each is a semantics the freeze
rejects; preserving it to avoid edits would carry the defect forward under a new name.

---

## 8. TWO-SOURCE CONSUMER SUFFICIENCY *(U-3)*

**Build order inside the unit:**

1. **Required-minimum derivation** — two independent derivations (representational from
   entity semantics, reasoning-premise from stage responsibility), unioned. Neither reads the
   consuming stage's own declaration.
2. **Contributory declaration** — stage-authored, widening only. A declaration that would
   narrow the minimum fails contract validation rather than being silently clamped.
3. **View construction** — build to the union, preserving provenance and maturity on every
   projected value.
4. **Sufficiency assessment** — independent; reads the contracts and the view; emits
   UPSTREAM INSUFFICIENCY or PROJECTION FAILURE, never a single "incomplete".
5. **Recorded `ConsumerView`** — content, the minimum it was built against, what was
   compressed and by which rule.

**Explicitly prevented, and each needs a test that would catch its return:**

| Failure to prevent | Test shape |
|---|---|
| static family whitelist recurrence | no code path selects families from a literal collection |
| positional character slicing | no serialization path applies a length slice; the current `[:26000]` is the specimen |
| silent tail loss | reduction is recorded with the rule applied |
| a stage narrowing its minimum | a narrowing declaration fails validation |
| the view defining its own completeness | the assessment's inputs include both contracts |

**Budget overflow behaviour, in order:**

1. reference-by-id with expansion on demand;
2. role-level summarisation of homogeneous collections (a derived grid summarises to counts
   plus the non-default cells);
3. omission of **contributory** classes, recorded;
4. where the architecture permits, split the reasoning call along a boundary that does not
   divide a required premise set;
5. otherwise emit `CONTEXT_INSUFFICIENT` / `BUDGET_INSUFFICIENT` and do not call.

**Required semantics are never silently omitted at any step.** No threshold is derived from
benchmark observation; the budget is a provider property and the ordering above is
architectural.

---

## 9. CONTROLLED AUTHORITATIVE MUTATION *(U-4)*

**Current write-path inventory** — from direct inspection of the working tree, to be
re-verified against HEAD before implementation:

| Path | Writes | Classification | Action |
|---|---|---|---|
| `state/design_state.py:127-134` | `CREATE` — entity record, `by_family` index | **LEGITIMATE CONTROLLED MUTATION** | keep; add authority class and premise refs |
| `state/design_state.py:135-136` | `EXTEND` — unguarded `dict.update`, no owner check, no provenance | **LEGITIMATE, INSUFFICIENTLY CONTROLLED** | keep the operation, guard it. Never exercised in the audited corpus, so there is no behaviour to preserve |
| `tools/run_window2.py:361-363` | `e["volume"]` on a functional region | **DIRECT WRITE TO ELIMINATE** — a class-A spatial commitment | route through `EXTEND` with provenance |
| `tools/run_window2.py:365-367` | `e["insertion_direction"]` on an assembly step | **DIRECT WRITE TO ELIMINATE** — class A | route through `EXTEND` |
| `tools/run_window2.py:372-375` | `e["frame_origin"]` on a joint | **DIRECT WRITE TO ELIMINATE** — class A, and the single most consequential spatial commitment in the pipeline | route through `EXTEND`; add the axis, which is currently absent |
| `tools/run_window2.py:368-370` | `state.s04a_reach`, `state.s04a_elimination`, `state.s04a_scale` as bare attributes | **DIRECT WRITE TO ELIMINATE** — reach results and elimination are *engineering conclusions* with no entity, no id and no provenance | promote to class-A families (M-2), then write through the boundary |
| `state/projection.py:20` | `dict(state.entities[i])` — a copy into a view | **EPHEMERAL WRITE** (class C) | fine; the module is replaced by U-3 for other reasons |
| `stages/s03_topology_and_mobility.py:267-339` | mobility cells via a patch | **DERIVED RECOMPUTATION**, except the `:333-337` branch which authors class A from absence | split by U-6 |
| `stages/s04_envelope_and_motion.py:293-309` | `sampling_declaration` from a constant | **class A asserted from no premise** | replaced by a recorded evidence level (U-7) |
| Layer-B checks in `stages/*.py` | findings | **ASSURANCE ARTIFACT** (class D) | relocated by U-9 |

**Note on the fifth row.** `_absorb`'s docstring argues these are "properties OF existing
entities, not new families; giving each its own family would be inventing representation to
avoid an EXTEND." **The reasoning is sound and the conclusion is right** — they *are*
properties of existing entities. The defect is the bypass, not the modelling. The fix is to
use `EXTEND`, which is precisely the operation the docstring names.

**Provenance and dependency attachment.** Every controlled write carries: the operation, the
authoring stage or derivation, the premise ids, the evidence reference, and the maturity of
the value. Premise ids are what make §10's propagation computable.

**Supersession effect on dependents:** implemented per FA-5. **How** propagation is computed —
eager on write, lazy on read, or closure recompute — is an implementation decision (freeze §9)
and should be chosen after U-1's premise representation is concrete, not before.

---

## 10. PHYSICAL REASONING REPRESENTATIONS *(U-5)*

- **`PhysicalEffectObligation`** at S02: effect · between which **roles** (never bodies —
  they do not exist yet) · under which load case or scenario · which obligation it discharges
  · persistence/intermittence/releasability.
- **`PhysicalInteraction`** at S03·B: the two rigid groups · the effect transmitted · the
  interface or feature where transmission occurs · active configurations · the effect
  obligation discharged. **Distinct from `Joint`** — a joint constrains, an interaction
  transmits.
- **`ConstraintRelation`** at S03·B: addressable; retained group · dofs and direction ·
  **provider** (body or external reaction site) · site · configurations · maintaining
  interaction · defeat condition · driver · provenance. No sentinel values: a provider is a
  resolvable reference or the relation is incomplete.
- **`ReactionSiteRequirement`** at S01/S02: typed external or internal **from the scenario's
  declared system boundary**. A load path is closed when its terminal hop resolves to an
  external site for the scenario in which the load acts; otherwise it is explicitly open.

**Guard against scope creep.** S02 must state *what physical effect must occur between which
roles*, not how. If a review finds S02 naming bodies, joints or mechanisms, the unit has
failed its own prohibition regardless of what the tests say.

---

## 11. MOBILITY MIGRATION *(U-6)*

1. **Split the function.** Domain enumeration becomes class B and is reported as BOOKKEEPING.
   Disposition assignment becomes a separate concern.
2. **Derive dispositions only from premises.** `INTENDED` from an authored joint;
   `CONSTRAINED` from a `ConstraintRelation`, **referencing it**; `IRRELEVANT` authored and
   cross-checked against load cases.
3. **Introduce `UNDISPOSITIONED`** for every remaining cell, naming what is missing. The
   `MAINTAINED_BY_CLASS`-from-absence branch and the string `"joint class of no joint"` are
   deleted, not reworded.
4. **Report disposition completeness** as an engineering quantity: what fraction of the
   domain is dispositioned by evidence, and which cells are not.
5. **Retire the totality check as assurance.** It tests what the enumerator guarantees. It
   remains as a BOOKKEEPING report.
6. **Add the real mobility assurance** in U-9: cross-premise consistency against load cases
   and actuation — a DOF marked irrelevant that a load case loads is a genuine contradiction,
   and the two premises have different authors.

**Expected and correct outcome:** dispositioned coverage falls sharply. Success criteria
(§19) are written so this reads as the migration working, not as regression.

---

## 12. S04 SPATIAL / REFINEMENT MIGRATION *(U-7)*

- **The arrangement becomes a derived required premise** of S04·B (U-3 makes this automatic
  once `joint_frame.origin` declares its frame; no whitelist is edited).
- **Commitment classes** on every S04·A spatial value; S04·B extends, or supersedes with a
  geometric reason and an invalidation cone.
- **Joint frames gain an axis.** `frame_origin` alone cannot support any incidence or
  distinctness claim.
- **Required-distinctness declarations** flow from S03 and are checked at PREMISE
  independence against a placer that did not author them.
- **Configurations carry a distinguishing basis**; transitions declare the coordinates that
  change; realization must change them.
- **Motion evidence level** (`ENDPOINTS_ONLY` / `SAMPLED` / `SWEPT` / `CONTINUOUS`) is
  recorded from the computation performed. The constant-derived `sampling_declaration` is
  deleted. **The swept-hull computation itself is correct and is preserved** — only the
  fabricated declaration goes.
- **`_render`'s positional slice is removed** and replaced by U-3's budget behaviour.

---

## 13. COMMITMENT / GATING MIGRATION *(U-8)*

- Commitment classes and supersession from U-1/U-4 become operative across stages.
- **Blocking is mechanical:** an unresolved item blocks when it names a fact class the next
  consumer's or the gate's required minimum marks required. This finally gives the
  `UnresolvedDecision` family a consumer — currently nothing reads it.
- **The gate**: equal obligation coverage at equal maturity across retained candidates, no
  blocking unresolved item, every evidence-route verdict recorded. A tie emits an
  `UnresolvedDecision`.
- **The gate does not author its own precondition verdict.** Preconditions are computed from
  committed state by a reader that is not the gate.
- **Both poles gain emitters.** `SAFE_REJECTION` when a stage declines a claim it cannot
  support; `FALSE_ACCEPTANCE` when a commitment is made over a blocking item or on a check
  whose inputs were below its minimum maturity.

---

## 14. ASSURANCE / STATUS MIGRATION *(U-9)*

Checks move out of `stages/*.py` into a layer that reads committed state and is not invoked
by any producing stage. Every check declares an **independence degree** and a **claim class**.

| Capability | Authoritative inputs | Independence | Property established | Self-fulfilling risk | Failure semantics |
|---|---|---|---|---|---|
| **consumer sufficiency** | both contracts + the recorded view | STRUCTURAL | the view carries the derived minimum | **high if** it reads only declaration+view | UPSTREAM INSUFFICIENCY vs PROJECTION FAILURE — never merged |
| **reference integrity** | typed state + contract reference targets | STRUCTURAL | every reference resolves | moderate — writer and checker share the rule | an unresolvable reference refuses the patch |
| **physical relation closure** | effect obligations (S02) + interactions (S03·B) | PREMISE | every required effect is discharged or open | low — different producers | undischarged and unrecorded is a finding |
| **mobility disposition completeness** | dispositions + cited relations | STRUCTURAL | every disposition traces to a resolvable premise | moderate | PROVENANCE INTEGRITY only — **may not contribute to establishment** |
| **mobility cross-premise consistency** | load cases/actuation (S02) + dispositions (S03) | PREMISE | no DOF is irrelevant under a load that loads it | low | **ENGINEERING CONSEQUENCE** |
| **topology→spatial fidelity** | topology (S03) + placement (S04·B) | PREMISE | realization matches declared incidence | low — the placer authored neither | ENGINEERING CONSEQUENCE, bounded: a wrong topology faithfully realized still passes |
| **required distinctness / non-degeneracy** | distinctness declarations (S03) + placement (S04·B) | PREMISE | declared distinctness survives realization | low | ENGINEERING CONSEQUENCE. **Conditional on a declared premise — never "all joint pairs must differ"** |
| **state/configuration realization** | distinguishing bases (S03) + coordinates and transitions (S04·B) | PREMISE | configurations differ on their basis; declared coordinates change | low | ENGINEERING CONSEQUENCE |
| **quantitative continuity** | quantities (S01/S02) + consumer class declarations | STRUCTURAL | no stage declares a class unknown while an authoritative constraint exists | low | FIDELITY |
| **commitment validity** | gate preconditions computed from committed state | EXTERNAL preferred | the gate fired on met preconditions | **high if the gate self-reports** | `FALSE_ACCEPTANCE` |

**Not a rename of the existing validators.** Several current checks are good and are preserved
in substance — graph connectivity, magnitude fidelity, the honest `NOT_VERIFIED` semantics of
the clearance check, the absence-is-not-success statuses. What changes is where they run, what
they may claim, and that two of them (dof totality, sampling declaration) stop being counted
as assurance at all.

**Status reporting** separates the four constructs. `build_pipeline_dashboard.py`'s single
badge is replaced; `quality_profile.py`'s 32 S01/S02-only metrics either gain terms for S03/S04
or stop describing themselves as pipeline maturity.

---

## 15. PROMPT MIGRATION

**No prompt text is written in this plan**, and no prompt is rewritten before U-2 and U-3 for
its stage. Prompts currently live inside the stage modules — `s03_topology_and_mobility.py` is
979 lines including its prompts — and several fields exist *only* in prompt text. That
inversion is what U-2 fixes.

**Prompts should become shorter, not longer.** Every prohibition currently carried in prose
that a contract or the view can carry structurally moves there.

Per stage, the migration states only: **engineering responsibility** · **the consumer view
supplied** (from U-3, not hand-listed) · **decisions expected of the model** · **facts
deterministic code supplies** · **what must remain unresolved if evidence is insufficient** ·
**prohibited premature commitments**.

**Prohibited in every prompt:** product-noun → mechanism advice; benchmark-derived examples;
provider-specific formatting tricks; and prose that compensates for a missing representation.
If a prompt needs a paragraph to explain a concept, the concept belongs in a contract.

---

## 16. RUNNER / PROVIDER MIGRATION

- **One controlled write path.** `run_window2.py`'s `_absorb` is eliminated (§9).
- **`S03_OWNED` is deleted**, not extended. Consumer views come from U-3.
- **The two runners converge.** `run_window.py` (fixture replay) and `run_window2.py` (live)
  currently differ in how state is assembled; both must use the same state and view
  substrate, differing only in where responses come from.
- **Provider parameter fidelity.** `live_providers/deepseek.py:100,165` sends the adapter's
  own `temperature` and never reads `request.temperature`. Requested-vs-sent is already
  recorded (`:304-305`) — the recording is good and stays; the divergence goes.
- **Provenance stays complete.** Model substitution, clamping, truncation and seed status are
  already recorded per call. This is a preserved strength; do not simplify it away.
- **No response repair.** 59/59 stored artifacts are currently byte-identical to raw text.
  Repair would measure the repair. `repair_prompt_pairing.py` is a fixture tool, not a
  response tool, and must stay that way.

---

## 17. FIXTURE MIGRATION

| Compatibility need | Classification |
|---|---|
| the frozen benchmark/probe **source inputs** | **REQUIRED** — inputs are the one thing that must not change |
| the Oracle and reference artifacts | **REQUIRED** unchanged — they are independent bars |
| Window-2 upstream **S01/S02 fixtures** | **REJECT / REGENERATE** after U-2 lands |
| current stage response artifacts | **REJECT / REGENERATE** — they encode retired shapes |
| the `pairing_history` stamping tool | **TEMPORARY MIGRATION BRIDGE** — useful during regeneration, not part of the target |
| current dashboard/profile output shapes | **REJECT** — they merge constructs the freeze separates |

**Fixtures are regenerated, not hand-edited**, and regenerated *from conforming live upstream
runs* once the new contracts exist.

> **The final evaluation must not rely on fixtures richer than conforming live upstream
> output.** The current fixtures violate the live prompt's own stated vocabulary in at least
> the `principle` and `obligations_created` fields — the *live model* conforms and the
> *fixtures* do not. Replaying them makes downstream stages look better supported than a live
> chain would leave them, which is exactly the inflation §18-F exists to prevent.

**Provenance note carried forward:** PRB fixtures declare `authored_by: agent-in-repository`;
BM fixtures declare no authorship and their provenance is **UNKNOWN from available metadata**.
Regeneration should make provenance explicit for every fixture, closing that gap.

---

## 18. TEST ARCHITECTURE

Six levels. Every unit lands with A and B; C onward run as broad regression (§20).

**A — Unit tests.** Contract parsing and joins; mutation operations; view construction;
dependency propagation; reference resolution. Extends the existing `tests/meta/` corpus, which
is genuinely good and should be preserved in kind.

**B — Property / invariant tests.** Architecture semantics, mechanism-independent, expressed
against synthetic state:

- a class-A write outside the boundary raises;
- `SUPERSEDE` retains both values and marks dependents;
- a required class removed from state → UPSTREAM INSUFFICIENCY; removed from the view only →
  PROJECTION FAILURE;
- a narrowing sufficiency declaration fails validation;
- a DOF cell with no covering premise yields `UNDISPOSITIONED`;
- no serialization path applies a positional slice;
- a derived value with an incomplete premise set is not produced;
- a check declaring a claim class other than ENGINEERING CONSEQUENCE cannot raise a property
  to `ENGINEERING_ESTABLISHED`.

**C — Synthetic micro-probes.** Minimal constructed cases, each isolating **one** capability —
one that requires a premise from two stages, one with a genuinely underdetermined DOF, one
where a superseded premise must reopen a commitment, one where two candidates are honestly
indistinguishable and the correct output is a recorded tie. **These are not benchmarks and
carry no product nouns**; they exist to make an architectural property fail on demand.

**D — BM/PRB regression.** Non-regression evidence and evidence of improved general
capability. **Never a tuning target.** Failures are classified by architecture cause (§20),
never repaired case-by-case.

**E — Unseen probes.** Required before any generalization claim. A probe whose upstream is
replayed is not generalization evidence for that upstream.

**F — End-to-end live chain.** S01→S04 live throughout. **This does not exist today** — Window
2 replays S01/S02 from fixtures, which is why it is not end-to-end evidence. No claim about
pipeline capability is made from a run with replayed upstream.

---

## 19. SUCCESS CRITERIA

Per unit, defined before code changes. **Tests passing, schemas validating and a green
dashboard are preconditions, never criteria.** Every criterion below is mechanism-independent.

| Unit | Engineering-semantic success criteria |
|---|---|
| **U-1** | An authoritative direct write is *detectable* and *prohibited*. A superseded value remains readable alongside its replacement. A derived value without sufficient premises does not exist. |
| **U-2** | Every family resolves to one owner, one shape and one consumer interpretation. No field's only definition is a prompt. Every spatial field declares a frame; every reference declares a target. |
| **U-3** | **A required consumer premise cannot silently disappear.** Upstream insufficiency and projection failure are always distinguishable. A stage cannot narrow its minimum. No output is produced from a view known to be insufficient. |
| **U-4** | Every previously-absorbed value carries provenance and premise references. No class-A field is writable outside the boundary. |
| **U-5** | Every physical-effect obligation is discharged by a named interaction or is explicitly open. Every constraint relation names a resolvable provider. Every load path terminates externally or is recorded open. |
| **U-6** | **An absent mobility premise yields `UNDISPOSITIONED`**, never a class default. Every disposition cites a resolvable premise. Disposition completeness is reported as a quantity, and the totality report is labelled BOOKKEEPING. |
| **U-7** | **An S04·B refinement cannot silently contradict a binding S04·A commitment.** A declared required distinctness that realization violates is a finding. A motion evidence level is a function of the computation performed. |
| **U-8** | **Changing a premise affects dependent commitment status.** No selection occurs on unequal coverage. Both poles are emitted by real conditions. |
| **U-9** | **Assurance cannot claim engineering establishment from producer-guaranteed shape alone.** No check is reachable from a stage module. No aggregate mixes execution with engineering. Establishment is never inherited. |

---

## 20. BROAD REGRESSION STRATEGY

The prescribed loop:

1. implement one coherent migration unit;
2. run the **full** evaluation — unit, property, synthetic micro-probe, BM, PRB;
3. collect **varied** failures without repairing any;
4. classify each failure by **architecture cause** — capture · representation · sufficiency ·
   authorship · reasoning · commitment · assurance;
5. revise coherently at the level of the cause;
6. rerun the full regression.

**Explicitly prohibited:** *run one benchmark → patch for that benchmark → rerun → patch
another.* That loop produced four cycles of parse-failure, id-collision and field-name work in
this project's history, none of it engineering quality.

**A failure that appears in one case only is not repaired in that case.** It is classified,
and repaired at its architectural cause or recorded as CASE-LIMITED and left.

---

## 21. COMPATIBILITY AND DEPRECATION

| Item | Classification |
|---|---|
| frozen source inputs; Oracle; CAD references | **REQUIRED** — unchanged |
| provider provenance recording | **REQUIRED** — a preserved strength |
| `tests/meta/` structural checks | **REQUIRED** in kind; extended, not replaced |
| the `EXTEND` operation | **REQUIRED** — kept and guarded, not removed |
| swept-hull computation and its conservative semantics | **REQUIRED** — correct today |
| `pairing_history` stamping | **TEMPORARY BRIDGE** |
| dual runners during convergence | **TEMPORARY BRIDGE**, bounded to one unit |
| `S03_OWNED`; `_absorb`; `[:26000]`; `MAINTAINED_BY_CLASS`-from-absence; `sampling_declaration` constant | **REJECT** |
| current Window-2 fixtures; current stage artifacts; current dashboard/profile shapes; retired family names | **REJECT / REGENERATE** |

**Rule:** no broken legacy semantics is preserved because fixtures use it. Fixtures are
derived artifacts.

---

## 22. RISK REGISTER

| ID | Risk | Mitigation | What would falsify the approach |
|---|---|---|---|
| **R-1** | The contract model becomes too large to maintain | declarations are **per field, local** (referent, class, mutability), not per stage-pair; the completeness test is structural | if authoring a new family routinely requires editing more than its own contract, the model is wrong |
| **R-2** | Reasoning-premise mapping becomes another manual whitelist | premises are declared as **classes** against the stage's **engineering questions**, not as family lists; a premise class with no engineering question is a defect | if premise declarations start naming families directly, or drift toward instances, the derivation has degenerated |
| **R-3** | Sufficient views exceed model context | §8's ordered budget behaviour; derived grids summarise; `CONTEXT_INSUFFICIENT` rather than silent loss | if a stage routinely cannot fit its **required** minimum, the stage boundary is wrong — split the reasoning, do not slice the view |
| **R-4** | Controlled mutation becomes bureaucratic | strict semantics apply to class A **only**; B and C stay cheap | if routine derived work needs patches, the A/B boundary is drawn wrongly |
| **R-5** | Dependency propagation becomes complex | premise refs are recorded at write; the *computation* strategy is deferred until the representation is concrete | if propagation needs a bespoke rule per family, the dependency model is not general |
| **R-6** | Assurance stays producer-coupled | checks are unreachable from stage modules; every check declares independence and claim class | if most checks land at STRUCTURAL with claim class FIDELITY, Rule A's floor is still unmet and the layer has not delivered |
| **R-7** | **A cheap model still reasons poorly once information flow is fixed** | this is the open question, not a risk to mitigate away; U-3 makes the attribution possible for the first time | if failures persist *with* verified-sufficient views, the limitation is the model or the stage decomposition — and that is a real, publishable result, not a migration failure |
| **R-8** | Legacy fixtures encode obsolete semantics | regenerate after U-2; never hand-edit | if regenerated fixtures cannot be produced by a conforming live run, the contract is unsatisfiable |
| **R-9** | Migration temporarily mixes authority models | U-1+U-4 land together; U-2+U-3 do not straddle a release (§5) | if any release permits both a controlled and an uncontrolled class-A write, stop and revert |
| **R-10** | Visible metric regression is read as failure | success criteria (§19) are engineering-semantic and were written first | if a unit is judged by dashboard colour, the evaluation philosophy has not been adopted |

---

## 23. ROLLBACK AND RECOVERY

- **Unit granularity is the rollback granularity.** Each unit is revertible without leaving a
  partial authority model behind — which is why U-1+U-4 are one step.
- **State artifacts are regenerable**, so recovery never depends on migrating stored state.
  Inputs, Oracle and reference artifacts are untouched throughout and are the recovery anchor.
- **The irreversible-in-practice step is U-2**, since retired shapes are not reproduced. It is
  gated on the structural completeness checks in §19 before anything depends on it.
- **A unit that fails its engineering-semantic criteria is reverted, not patched forward.**
  Patching forward across an authority-model boundary is how old and new semantics come to
  coexist.

---

## 24. FINAL IMPLEMENTATION SEQUENCE

| Step | Unit | Files / subsystems expected to change | Preconditions | Authoritative after this step | Tests required before the next step | Must **not** yet be enabled |
|---|---|---|---|---|---|---|
| **S-1** | U-1 + U-4 *(one step)* | `state/design_state.py`, `state/patch.py`, `tools/run_window2.py`, `tools/run_window.py`, `DESIGN_STATE_CONTRACT`, `STAGE_PATCH_CONTRACT`, `PROVENANCE_CONTRACT` | none | authority classes; the four operations; premise refs; **the single class-A write boundary** | A + B: illegal write raises; SUPERSEDE retains both; every former `_absorb` field carries provenance | premise-change *propagation*; commitment classes; any prompt change |
| **S-2** | U-2 | all of `contracts/`; retirement of prompt-only fields | S-1 | canonical families, owners, field authority, semantic dependencies, stage responsibilities and premise classes | A + B: one owner per family; no dangling reference; every spatial field declares a frame; every reference declares a target | consumer-view derivation; any stage output change |
| **S-3** | U-3 | new view module; `state/projection.py` retired; `S03_OWNED` deleted; both runners | S-2 | the derived required minimum; the recorded `ConsumerView`; the insufficiency/projection distinction | A + B + C: removal from state vs from view yields distinct findings; narrowing declaration fails; no positional slice remains | stage semantic changes; assurance relocation |
| **S-4** | U-5 *(+ S02/S03 prompt migration)* | `stages/s02*`, `stages/s03*`, S02/S03 contracts | S-2, S-3 | effect obligations; physical interactions; constraint relations; reaction-site requirements | A–D: discharge closure; provider resolution; load-path closure or explicit openness | mobility disposition changes |
| **S-5** | U-6 | `stages/s03*`, S03 contract | S-4 | dispositions with premises; `UNDISPOSITIONED`; disposition completeness as a reported quantity | A–D: absent premise ⇒ `UNDISPOSITIONED`; no unresolvable disposition premise; totality labelled BOOKKEEPING | counting mobility as engineering-established |
| **S-6** | U-7 *(+ S04 prompt migration)* | `stages/s04*`, runners, S03/S04 contracts | S-3, S-5 | commitment classes on spatial values; arrangement continuity; joint axes; distinguishing bases; recorded motion evidence level | A–D: S04·B receives the arrangement or records insufficiency; refinement cannot silently contradict; evidence level tracks the computation | the selection gate; premise propagation across selection |
| **S-7** | U-8 | `state/`, runners, `STAGE_PROGRESSION_CONTRACT`, `STATUS_SEMANTICS` | S-1, S-6 | premise-change propagation; blocking semantics; the gate; both poles | A–D: superseding a gate premise removes unqualified authority; no selection on unequal coverage; gate cannot self-authorise | engineering-establishment claims |
| **S-8** | U-9 | new assurance layer; checks removed from `stages/*.py`; `build_pipeline_dashboard.py`, `quality_profile.py`, `compare_maturity.py`, `STATUS_SEMANTICS`, `GENERATED_ASSURANCE_PACKAGE_CONTRACT` | S-1…S-7 substantially stable | independence degrees; claim classes; the four separated status constructs; `ENGINEERING_ESTABLISHED` | A–D: no check reachable from a stage; establishment never inherited; no construct-mixing aggregate | generalization claims |
| **S-9** | fixture regeneration + full chain | fixtures regenerated from conforming live upstream; both runners converged | S-2…S-8 | a **live S01→S04 chain** as the evidence basis | **E + F**: unseen probes; end-to-end live | any capability claim made from replayed upstream |

**No step contains a benchmark-specific patch.** Steps S-4 through S-8 each change a
*semantics*; benchmark and probe runs are regression evidence at every step and a target at
none.

---

## 25. DEFINITION OF IMPLEMENTATION-COMPLETE

All of the following, and none of them alone:

1. Every class-A mutation passes one controlled, provenance-carrying boundary, and a
   violation is statically detectable.
2. Every stage's required minimum is derived from two contracts it does not own; no stage can
   narrow it; upstream insufficiency and projection failure are always distinguishable.
3. No deterministic path converts absence of evidence into a positive engineering assertion.
4. A changed premise leaves no dependent commitment silently authoritative.
5. No serialization path truncates positionally; budget failure is recorded.
6. Every check declares an independence degree and a claim class, and only ENGINEERING
   CONSEQUENCE contributes to establishment.
7. **Rule A is met** — at least one meaningful engineering property per stage is
   independently established.
8. The four status constructs are reported separately, with no aggregate across them.
9. Fixtures are regenerable from conforming live upstream output, and at least one **end-to-end
   live S01→S04 chain** exists as the evidence basis.
10. Every retired shape in §7 is gone, with no compatibility path preserving it.

**Not part of the definition:** a green dashboard, a benchmark score, or a maturity
percentage. **And not answered by completion:** whether an inexpensive model reasons like a
competent mechanical designer once information flow is correct. Implementation-complete means
that question is finally *askable* — the architecture exists so that a failure can be
attributed to reasoning rather than to a boundary. Answering it is the work that follows.
