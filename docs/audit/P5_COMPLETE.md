# P5 — IMPLEMENTATION / ROOT-CAUSE AUDIT

Axis A: **GENERATED EVIDENCE**. Axis B: **REVIEW RECORD**.

Complete read of the frozen P5 implementation corpus. Nothing was modified, rerun or
patched. No fix, prompt change, validator or architecture change is proposed anywhere in
this document. P5 stops at ROOT CAUSE.

Companions: `P1_COMPLETE.md`, `P2_COMPLETE.md`, `P3_COMPLETE.md`, `P4A_COMPLETE.md`,
`P4A_CAPABILITY_GAP_SYNTHESIS.md`. Those are unmodified.

---

## §1 FILES READ COMPLETELY — 26 / 26, 5,184 lines

| File | Lines | File | Lines |
|---|---|---|---|
| `assy_v3/state/projection.py` | 21 | `assy_v3/knowledge/principle_library.py` | 180 |
| `assy_v3/state/design_state.py` | 144 | `assy_v3/knowledge/capability_registry.py` | 88 |
| `assy_v3/state/patch.py` | 53 | `assy_v3/knowledge/__init__.py` | 11 |
| `assy_v3/state/__init__.py` | 8 | `assy_v3/providers/interfaces.py` | 217 |
| `assy_v3/stages/base.py` | 123 | `assy_v3/providers/status.py` | 91 |
| `assy_v3/stages/s01_requirement_capture.py` | 225 | `assy_v3/providers/agent_authored.py` | 88 |
| `assy_v3/stages/s02_obligation_and_candidates.py` | 528 | `assy_v3/providers/offline.py` | 52 |
| `assy_v3/stages/s03_topology_and_mobility.py` | 979 | `assy_v3/providers/__init__.py` | 41 |
| `assy_v3/stages/s04_envelope_and_motion.py` | 687 | `live_providers/deepseek.py` | 318 |
| `assy_v3/stages/__init__.py` | 2 | `live_providers/env.py` | 78 |
| `assy_v3/__init__.py` | 52 | `live_providers/__init__.py` | 20 |
| `ver3/__init__.py` | 11 | `tools/run_window2.py` | 469 |
| `tools/run_live_window.py` | 370 | `tools/run_window.py` | 146 |
| `tools/repair_prompt_pairing.py` | 182 | | |

Every provisional finding from the first stretch was re-checked against the complete
files. Six were **withdrawn or narrowed** (§14).

---

## §2 IMPLEMENTED DesignState / StagePatch SEMANTICS

### 2.1 Operation kinds: contract six, code five, used one

`state/patch.py:15` — `OP_KINDS = (CREATE, EXTEND, RELATE, RECORD_UNRESOLVED, RECORD_REJECTED)`.
**`SUPERSEDE` is absent from the code entirely** (zero occurrences in the corpus), so the
contract's revision mechanism (`STAGE_PATCH_CONTRACT:164-175`) has no implementation.

`state/design_state.py:126-137` — `apply()` has branches for **CREATE and EXTEND only**.
`RELATE`, `RECORD_UNRESOLVED` and `RECORD_REJECTED` ops are accepted by the dataclass and
**silently produce no state**.

**Corpus-wide, all 30 `Op(...)` constructions are `CREATE`.** No `EXTEND`, `RELATE`,
`RECORD_UNRESOLVED` or `RECORD_REJECTED` op is ever built by any stage or tool.

### 2.2 `Op` cannot carry a RELATE payload

`patch.py:19-24` — `Op(kind, entity_type, entity_id, fields, provenance_ref)`. The
contract's RELATE requires `relation_type, subject, object` (`STAGE_PATCH_CONTRACT:99`).
**Those fields do not exist on `Op`.** `Contracts.families` (`design_state.py:29-30`) is
`entity_families + assurance_families`; `blocked_by`, `retained_by` and `co_actuated_by`
live under `typed_relations` and are in **neither**, so an op naming one would be rejected
`UNKNOWN_FAMILY`. **This is P2's structural incompatibility, confirmed at both ends.**

### 2.3 The three mutation paths, and what is actually possible

| Path | Location | Validated? | Used? |
|---|---|---|---|
| CREATE | `design_state.py:127-134` | yes — ownership, duplicate id, required fields, references | **all 30 ops** |
| EXTEND | `design_state.py:135-136` — `self.entities[eid].update(op.fields)` | **no owner-field protection, no append-only enforcement** | **never** |
| direct write | `run_window2.py:346-375` `_absorb()` — `e["volume"] = …`, `e["insertion_direction"] = …`, `e["frame_origin"] = …` | **none at all** | **yes, every s04 run** |

**§4 answered.** The EXTEND branch violates `STAGE_PATCH_CONTRACT:89-90` but is **dead
code** — nothing emits an EXTEND. The pipeline is **purely additive via CREATE**, so no
field is ever overwritten by the patch layer. The one real mutation of existing entities is
`_absorb()`, which **bypasses StagePatch entirely**: no `Op`, no validation, no ownership
check, no provenance, no `applied_patches` entry. `STAGE_PATCH_CONTRACT:3-6` forbids exactly
this (*"A stage that could write directly to the state would make ownership advisory"*), and
`run_window2.py:351` shows the choice was conscious — *"giving each its own family would be
inventing representation to avoid an EXTEND."*

**A practical TYPE-B overwrite is possible through `_absorb` and through EXTEND if it were
ever used. In the observed runs each target field is written once, so no data loss actually
occurred.** Both statements hold.

### 2.4 Invalidation and the two poles are vocabulary only

`invalidation_cone` is declared at `patch.py:46` and **read nowhere**. STALE is never set.
`SAFE_REJECTION` and `FALSE_ACCEPTANCE` exist in `status.py:50-51` and `SEVERITY_ORDER`
and **have no emitter anywhere in the corpus** — the two statuses the module docstring
calls *"the architecture's whole point"* are never produced by any code path.

### 2.5 The reference validator is opt-in by field name

`design_state.py:105-119` checks only keys ending `_id`/`_ids`/`_refs` plus five hard-coded
names, and only for strings matching `ref[:4].isupper() and "-" in ref`.
**Not checked:** `blocker_body`, `retained_group`, `bodies`, `parent_group`, `child_group`,
`owning_bodies`, `ordered_hops`, `configurations`, `body`, `joint`, `functional_region`,
`assembly_step`, `activates`, `depends_on`, `kept_open_by`, `applied_to_role`,
`reacted_at_role`. A free string such as `"desk edge"` is not even recognised as a
reference. `STAGE_PATCH_CONTRACT:102` and `DESIGN_STATE_CONTRACT:416` declare a free-string
subject a SCHEMA_FAILURE (R-20); **that rule has no implementation.**

`design_state.py:90-95` treats an **empty list as present** for required fields (explicit
comment), so `dispositions: []`, `promised_features: []`, `frame_ids: []` all validate.

---

## §3 CONSUMER PROJECTION MAP, S01 → S04

`state/projection.py` is 21 lines and strips exactly one family:

```python
SOURCE_TEXT_FAMILIES = ("SourceClause",)
if stage_id != "s01" and family in SOURCE_TEXT_FAMILIES: continue
```

**Everything else in the accumulated state is projected to every stage.** So a fact missing
from a downstream prompt is never a projection failure at this layer.

| Boundary | Built by | Included | Excluded | Classification of the P4A gaps |
|---|---|---|---|---|
| **S01→S02** | `project_for("s02")`, rendered whole by `s02.py:212-217` | all families minus `SourceClause` | `SourceClause` only | **INTENDED BOUNDARY** — INV-002, enforced twice (projection, and `s02.py:226-228` raises `AssertionError` if it leaks) |
| **S02→S03** | `project_for("s03")` + the selected `candidate` dict (`run_window2.py:183-188`) | everything | nothing | **PROJECTED AND USED** |
| **S03→S03B** | `mech` = `S03_OWNED` whitelist + `demands` = `{LoadCase, Obligation, candidate}` (`run_window2.py:221-224`) | LoadCase **is** included here | Requirement, Candidate, Actor, Scenario, Ambiguity, Freedom | `reacted_at_role` **is** available to s03b |
| **S03→S04A/B** | `mechanism_projection()` = `S03_OWNED` whitelist (`run_window2.py:78-100`) | Body, RigidGroup, Joint, Interface, Configuration, MobilityExpectation, LoadPath, AssemblyStep, FunctionalRegion | **Requirement, Obligation, LoadCase, Candidate, Actor, Scenario, Ambiguity, Freedom, UnresolvedDecision, AcceptanceContract, Assumption** | **PRESENT IN STATE BUT NOT PROJECTED** |

**§5 traced, item by item:**

| Fact | Classification |
|---|---|
| Requirement quantities at S04A | **PRESENT IN STATE BUT NOT PROJECTED** — `S03_OWNED` excludes `Requirement`. Deliberate whitelist, documented at `run_window2.py:75-79` |
| `SourceClause` boundary | **INTENDED** — INV-002, enforced by code |
| `BodyHypothesis` / `PhysicalInteractionHypothesis` | **NOT PRESENT UPSTREAM** — no such family in `DESIGN_STATE_CONTRACT`, no such key in any prompt, no such Op anywhere |
| `FunctionalRegion.required_by_actors` / `reach_targets` | **PROJECTED AND USED** — stored by `s03.py:443-444`, consumed by `interface_gaps()` (`run_window2.py:113-122`). The fields exist to close that gap check, not to satisfy a contract |
| `addresses_obligations` | **PROJECTED AND USED** — `s03.py:384,402`, read by `obligation_ownership_check` (`s03.py:717-721`) |
| `LoadCase.reacted_at_role` | **PROJECTED AND USED at s03b** (`demands`); **NOT PROJECTED at s04** |
| `blocked_by` | **NOT PRESENT UPSTREAM** — never stored as an entity (§5) |
| `MobilityExpectation` | in `S03_OWNED`; created only by the **tool**, not by a stage (§6) |

---

## §4 CONTRACT ↔ PROMPT ↔ RESPONSE-SCHEMA MISMATCHES

| # | Concept | Contract | Prompt / schema | Implementation |
|---|---|---|---|---|
| M-1 | `Candidate.principle` | `required_fields` names it, shape unspecified | s02 Rule 3 says a mapping *"for each"*; PERMITTED VALUES says *"**one of** the PRINCIPLE FAMILIES"* — **self-contradictory in one prompt** | `s02.py:256` passes it through verbatim; `s02.py:394` and `:407-409` **branch on dict / list / str — the code tolerates all three shapes** |
| M-2 | `blocked_direction` | *"Direction and blocker are required TOGETHER… a blocking fact without a direction cannot be tested"* | s03b prompt offers `{axis_directions}`, and `AXIS_DIRECTIONS` **includes `"NONE"`** (`s03.py:127`) | `"NONE"` is truthy, so `s03.py:536` and `s03.py:964` never flag it |
| M-3 | `promised_features` | **required** on `blocked_by` | s03b schema marks it **`(optional)`** | never stored — no blocking entity exists |
| M-4 | `Configuration.expected_mobility` | **required** | **no prompt asks for it** | `s03.py:407` defaults to `[]`, which passes validation |
| M-5 | `Joint.frame_ids` | **required** | **no prompt asks for it** | `s03.py:393` defaults to `[]` |
| M-6 | `Configuration.kind` | **not a contract field** | prompt asks for it, **no enumeration** | `s03.py:405` defaults to `"OPERATIONAL"` |
| M-7 | `interaction_kind` | `DECLARED_*` prefixed (P2) | prompt lists unprefixed | `INTERACTION_KINDS` (`s03.py:41`) unprefixed — code agrees with prompt, not contract |
| M-8 | `nominal_status` | contract name | prompt asks `nominal_status` | `s03.py:401` **renames to `nominal`** and defaults to `"NOMINAL"` |
| M-9 | `LoadPath.maturity` | vocabulary `SYMBOLIC\|PROVISIONAL\|AUTHORITATIVE\|FROZEN` | not asked | `s03.py:433`, `s03.py:940` hard-set **`"HYPOTHESIS"`** — outside the vocabulary |
| M-10 | `unresolved[].kept_open_by` | Ambiguity/Freedom ids | s01, s02 and s03 prompts **state the constraint**; **s03b prompt has no REFERENCES block at all** | `openness_citation_check` exists for **s02 only**; no s03b equivalent |
| M-11 | joint axis at s04b | `Joint.fields_owned_by_s04b: [located_frame]` | prompt asks for the axis in prose; **schema has only `origin [x,y,z]`** | `frame_origin` written by `_absorb`, never a frame |
| M-12 | path / sampling | swept proof required | **s04b schema has no path or sampling field** | `s04.py:306-308` **fabricates** the sampling declaration |
| M-13 | `MobilityExpectation` | `owned_by: s03`, TOTALITY | **no s03 or s03b prompt has a key for it**; `s03.py:411,424` read `mobility`/`dof_dispositions`, which no prompt requests | created only by `run_window2.py:263-279` |
| M-14 | `RETENTION_TERMINATION` | — | library says `LATER_BODY_COVER, ROTATION_LOCK, ELASTIC_CAPTURE`; s03b prompt says `LATER_BODY_COVER, ROTATION, ELASTICITY, NONE` | `TERMINATION_STRATEGIES` (`s03.py:48`) follows the prompt |

**The s03 prompt duplicates a ~1,500-character block** — visible in the source literal at
`s03.py:195-256` — and its rules run **1,2,3,4,5,6,9**.

---

## §5 RETENTION / BLOCKING RELATIONS — END TO END

```
s03b prompt asks for blocking_relations[]
  → model emits them (raw response, stored verbatim as the artifact)
  → relations_of()            s03.py:880-911   builds them IN MEMORY
      · canonicalise_blocking() s03.py:75-95   applies 9 documented ALIASES
        (blocked_by→blocker_body, direction→blocked_direction, test/defeat_test
         →defeat_specification, reason/why→driver, group/rigid_group→retained_group)
        and coerces a 1-element list blocker to a string; renames are RECORDED
  → used by  S03B.completeness()   s03.py:956-979    (a status only)
  → used by  derive_mobility()     via run_window2.py:250-257
  → *** NEVER WRITTEN TO DesignState — S03B.to_operations (s03.py:933-954)
        creates only LoadPath, AssemblyStep, UnresolvedDecision ***
```

**Consequences, all established from code:**

- `blocked_by`, `retained_by`, `co_actuated_by` are **never persisted and never addressable**.
- The derived dispositions carry `blocking_relation: r.get("id")` (`s03.py:323`) — **a
  reference to an id that exists in no entity**. `design_state._reference_problems` does not
  inspect `dispositions` (not a `_id`-suffixed key; values nested in a list of dicts), so the
  **dangling reference passes validation**.
- `blocking_relation_check` **does** catch `blocker_body: "NONE"` via `BLOCKER_NOT_A_BODY`
  (`s03.py:542-544`), but **no check compares `blocker_body` to the retained group's own
  body**, so self-blocking is invisible.
- Presence checks use `not str(x or "").strip()`, so the literal `"NONE"` / `"None"`
  satisfies them (`s03.py:536`, `s03.py:964`).

**Classification: representation AND implementation.** The contract models a first-class
relation; `Op` cannot express it; `Contracts.families` does not contain it; and the stage
does not attempt to store it.

---

## §6 MOBILITY / DOF RESPONSIBILITY — RESOLVED FROM CODE

**Domain enumeration ends and disposition begins at `s03.py:317`.**

`dof_domain()` (`s03.py:342-349`) and the `for group … for cfg … for dof` loops
(`s03.py:308-317`) are pure enumeration over `RigidGroup × Configuration × DOF_NAMES`,
taken from the topology and **never from the response**. Everything from `s03.py:320` is
disposition.

| Disposition | Evidence source | Classification |
|---|---|---|
| domain itself | topology | **LEGITIMATE BOOKKEEPING** |
| `BLOCKED_BY` (`:320-327`) | an authored blocking relation; copies its direction, blocker, defeat spec and driver **verbatim, including `"NONE"`** | **LEGITIMATE LOGICAL CONSEQUENCE** |
| `INTENDED` (`:328-329`) | `free_dof(joint_type, axis_direction)` | **LEGITIMATE LOGICAL CONSEQUENCE**, with two caveats below |
| `IRRELEVANT_BECAUSE` (`:330-332`) | an authored irrelevance entry | **LEGITIMATE LOGICAL CONSEQUENCE** |
| **`MAINTAINED_BY_CLASS` (`:333-337`)** | **nothing** — the `else` branch. `holding_class = "joint class of %s"` from the group's **first** joint, or the literal **`"joint class of no joint"`** when it has none | **UNSUPPORTED DEFAULT** |

**No later code corrects, rejects or overwrites a `MAINTAINED_BY_CLASS` entry.** The
derived patch is validated (`run_window2.py:275`) and applied; `dof_totality_check`,
`blocking_relation_check`, `irrelevance_check` and `retention_check` all skip non-matching
dispositions; nothing reads `holding_class`.

**Two further deterministic behaviours in the same function:**
- `s03.py:298` — `for cfg in (configs or configurations)`: a relation whose `configurations`
  list is empty or non-string is **silently applied to every configuration**.
- `free_dof` (`s03.py:101-118`) — an absent or unrecognised axis **silently becomes Z**;
  `FIXED` and any unknown joint type return the empty set; and **the joint's authored `dof`
  list is never read** — freedom is computed from `joint_type + axis_direction` alone.

**Circularity:** `derive_mobility` emits exactly one entry per `(group, cfg, dof)`, which is
precisely what `dof_totality_check` (`s03.py:483-513`) tests. **The check cannot fail on
derived output.** Totality is satisfied by construction, and — where nothing was authored —
by the unsupported default.

---

## §7 DETERMINISTIC DERIVATION INVENTORY

| # | What | Where | Evidence it derives from | Classification |
|---|---|---|---|---|
| D-1 | DOF domain | `s03.py:342-349` | topology | **LEGITIMATE BOOKKEEPING** |
| D-2 | `BLOCKED_BY` / `INTENDED` / `IRRELEVANT_BECAUSE` | `s03.py:320-332` | authored relations, joint class, authored irrelevance | **LEGITIMATE LOGICAL CONSEQUENCE** |
| D-3 | **`MAINTAINED_BY_CLASS`** | `s03.py:333-337` | **absence of evidence** | **UNSUPPORTED DEFAULT** |
| D-4 | blocking-field aliases | `s03.py:67-95` | the model's own words; renames recorded; *"A field that is absent stays absent"* | **LEGITIMATE BOOKKEEPING** |
| D-5 | **`sampling_declaration`** | `s04.py:306-308` | **a module constant `SAMPLES = 9`** | **INVENTED ENGINEERING EVIDENCE** (§10) |
| D-6 | `frame_ids: []`, `expected_mobility: []` | `s03.py:393,407` | nothing — contract-required, prompt-unasked | **UNSUPPORTED DEFAULT** |
| D-7 | `nominal` ← `nominal_status`, default `"NOMINAL"` | `s03.py:401` | nothing when absent | **UNSUPPORTED DEFAULT** |
| D-8 | `Configuration.kind` default `"OPERATIONAL"` | `s03.py:405` | nothing when absent | **UNSUPPORTED DEFAULT** |
| D-9 | `LoadPath.maturity = "HYPOTHESIS"` | `s03.py:433,940` | nothing; outside the contract vocabulary | **UNSUPPORTED DEFAULT** |
| D-10 | `free_dof` axis default Z | `s03.py:102-103` | nothing when absent/unknown | **UNSUPPORTED DEFAULT** |
| D-11 | AABB overlap, sweep hull, assembly hull | `s04.py:48-99, 437-649` | the model's own numbers; conservative by construction (`s04.py:16-21`) | **LEGITIMATE LOGICAL CONSEQUENCE** |
| D-12 | `required_contacts` must-touch list | `s04.py:350-367` | s03's joint graph + CONTACT-class interfaces | **LEGITIMATE BOOKKEEPING** — but see §9 |
| D-13 | `_absorb` field attachment | `run_window2.py:346-375` | the model's own response | **LEGITIMATE BOOKKEEPING in content, but written outside the patch layer** |

---

## §8 WINDOW-2 FIXTURE EXECUTION PATH

`run_window2.py:151-168` `seed_window1()`:
`OfflineReplayProvider(root, case_id)` → real `S01RequirementCapture().run()` →
`state.apply()` → `project_for("s02")` → real `S02ObligationAndCandidates().run()` →
`state.apply()`. Root is `fixtures/responses/` or `probes/`, chosen by presence of `s01.json`.

**So the fixtures do pass through the real parser, `to_operations` and
`state.validate()`.** A fixture that no longer satisfied S01/S02 would surface as
SCHEMA_FAILURE.

**But the staleness guard is bypassed by the provider choice.** `AgentAuthoredProvider`
(`agent_authored.py:72-80`) verifies `_meta.answers_prompt_sha256` against
`prompt_hash(request.prompt_text)` and refuses a stale recording.
**`OfflineReplayProvider` (`offline.py:36-52`) has no such check** — it reads the file and
returns it verbatim. `run_window2.py:157` uses `OfflineReplayProvider`.
**The field the fixtures carry specifically so pairing can be verified is ignored by the
provider Window 2 replays them through.**

`repair_prompt_pairing.py:165-175` writes that field, and appends the literal note
*"re-paired after the response-schema section was added to the prompt; content unchanged
and re-verified against the parser, contract validation and completeness check"* — the
**exact sentence present in all eleven fixture `pairing_history` arrays**. It re-stamps only
recordings that still satisfy the stage (`:116`, `:150-154`), and it runs over
`(FIXTURES, PROBES)` (`:135`).

**What Window 2 demonstrates:** S03/S04 behaviour given fixture upstream that satisfies the
current S01/S02 parser and contract validation.
**What it does not demonstrate:** that the live pipeline produces the same upstream
representation, and that the fixture answers the prompt built during that run.
`--candidates` defaults to **1** (`:382-383`), so `t1_CND-0001` in 6/6 cases is the CLI
default — the first candidate — not a selection decision.

---

## §9 TOPOLOGY → SPATIAL REALISATION

**Does the input carry enough?** Yes, for the failures observed.
- s04a receives the full `S03_OWNED` mechanism plus a **computed must-touch list**
  (`s04.py:350-374`), so joint incidence is stated explicitly in the prompt.
- s04b receives the same mechanism **including the Envelope entities s04a created**
  (`run_window2.py:312` re-projects after `state.apply`), so the arrangement is present.

**Could the schema express what was needed?** Only partly.
- s04b's schema holds `origin [x,y,z]` and **no axis field**, while the prompt asks for the
  axis in prose (M-11).
- s04b's schema holds **no path and no sampling field** (M-12).

**Was s04b required to preserve s04a's commitments?** **No.** `S04BPlacementAndMotion.
completeness()` (`s04.py:311-342`) checks only that every joint has *a* placement, every
configuration has coordinates, and >1 configuration implies a transition. **There is no
check that joint origins are distinct, that a joint origin lies within the bodies it
connects, or that configurations are physically distinct.**

**Was any deterministic closure check performed?** Yes, but not on joints.
- `joint_geometry_check` (`s04.py:415-434`) tests **body-pair separation** via
  `required_contacts`, not joint-origin incidence.
- `S04A.completeness()` (`s04.py:225-235`) does the same body-pair test at stage level.
- `swept_clearance_check` (`s04.py:523-603`) **does** use `frame_origin` — supplied by
  `_absorb` — and computes real sweeps.

**The `"desk edge"` propagation is fully traced.** `s03.py:399` stores `i.get("bodies", [])`
verbatim → `required_contacts` (`s04.py:362-366`) reads `i.get("bodies")` and takes free
strings straight through → `_contact_pairs_text` renders `BOD-0001 and desk edge must touch`
→ s04a Rule 1 says *"Every body gets an extent"* → `ENV-0006.body: "desk edge"`.
`envelope_coverage_check` (`s04.py:410-411`) **does** flag it as
`ENVELOPE_FOR_UNKNOWN_BODY`. **It is detected at s04 and not prevented at s03**, because
`_reference_problems` never inspects `bodies` (§2.5).

---

## §10 STATE / TRANSITION REALISATION — §6 of the brief

`S04BPlacementAndMotion.to_operations` (`s04.py:293-309`):

```python
for t in parsed.get("transitions", []):
    ops.append(Op("CREATE", "Transition", t["id"], {
        "from_state": ..., "to_state": ...,
        "path": {"moving_groups": t.get("moving_groups", [])},
        "sampling_declaration": {"kind": "UNIFORM", "samples": SAMPLES,
                                 "adaptive": False,
                                 "interior_samples": SAMPLES - 2}}, prov))
```

- **Created:** in the s04b patch, `s04.py:306-308`.
- **Derived from:** `SAMPLES = 9`, a module constant (`s04.py:347`). **No model input, no
  geometry, no evidence of any kind.**
- **Enters authoritative state:** via `state.apply(out.patch)` at `run_window2.py:331`,
  with the stage's own provenance.
- **Validated by:** `sampling_declaration_check` (`s04.py:503-520`), which tests only that
  the declaration is present, non-adaptive and has ≥1 interior sample — **exactly the
  properties the code just wrote.** It passes by construction.

**Classification: INVENTED ENGINEERING EVIDENCE, not bookkeeping.** A `sampling_declaration`
is an assertion about how a motion was verified. The constant is honest in intent
(`s04.py:345-346`: *"Not a tuning knob: a sampling density chosen per case is a density
chosen after seeing the answer"*), but the artifact asserts a declared 9-sample sweep with 7
interior points **regardless of whether any sweep was computed**.

**Distinctness is never enforced.** A `State` is `"STA-%s" % configuration` with whatever
coordinates were given (`s04.py:298-300`). **Nothing compares two States' coordinates**, and
nothing ties a state label to a change in contact or blocking. A label can change while
every coordinate stays fixed.

---

## §11 LOAD / SUPPORT / REACTION CLOSURE

```
LoadCase (s02)  applied_to_role, reacted_at_role, direction_class, kind, magnitude
  → load_case_check (s02.py:356-385): direction/kind vocabulary, scenario resolves,
      _reads_as_a_role() shape test, PART_NOUNS scan
  → s03b `demands` carries LoadCase (run_window2.py:222)
  → LoadPath (s03b)  ordered_hops, maturity "HYPOTHESIS"
  → load_path_check (s03.py:607-631): every LoadCase has a path; ≥2 hops;
      every hop resolves to a Body/Joint/RigidGroup/Interface
  → LoadPath is in S03_OWNED, LoadCase is NOT → s04 sees paths without their cases
  → load_path_reaction_check (s04.py:652-671): consecutive BODY hops must touch
```

**Where closure is lost.** The s02 prompt states the rule — *"Every load terminates
somewhere OUTSIDE the product… a load reacted against the product itself has not been
reacted"* (`s02.py:97-99`). **No check implements it.** `_reads_as_a_role` (`s02.py:309-320`)
is a shape test — ≥3 alphabetic words, no underscore, not all-caps — so *"the clamp body"*
and *"the user's hands"* both pass.

Downstream, `load_path_check` **would** flag `"NONE"`, `"desk edge"` and `"arm"` as
`LOADPATH_HOP_UNKNOWN`, but:
- there is **no check that the terminal hop is external**,
- there is **no cycle detection**, and
- `["BOD-0001","BOD-0001"]` has two hops, so it passes the length test and yields a
  non-positive gap in `load_path_reaction_check`.

`DESIGN_STATE_CONTRACT` derives *reaction* from *"the terminal hop of a LoadPath"* and
*support* from *"an Interface of contact kind appearing in a LoadPath"*. **Neither
derivation is implemented anywhere in the corpus**, and both become underivable when the
terminus is a literal or a free string.

---

## §12 UNRESOLVED / MATURITY / COMMITMENT GATING

**`UnresolvedDecision` is created** by s02 (`s02.py:265-271`), s03 (`s03.py:445-451`) and
s03b (`s03.py:947-953`) — always as a plain CREATE with `decision, why_open, alternatives,
alternatives_kind, kept_open_by, blocks`. **Nothing anywhere reads it back.** No check, no
stage input, no gate consumes `UnresolvedDecision`. `blocks` is in the five hard-coded
reference-check names, so its targets must resolve — that is its only effect.

**Maturity.** `Envelope.maturity` is the model's value or `"PROVISIONAL"` (`s04.py:194`);
`LoadPath.maturity` is hard-set to `"HYPOTHESIS"`, outside the contract vocabulary. **No
check anywhere reads a maturity field, and no check declares a minimum input maturity**,
though `DESIGN_STATE_CONTRACT` requires *"A check declares the minimum maturity of its inputs.
Running below it is a SCHEMA_FAILURE."*

**The gate.** Across **all three runners**, identically:

```python
if out.declared_incompleteness:
    fail("CONTRACT_CONDITION", …, "declared incomplete", out.declared_incompleteness)
state.apply(out.patch)          # runs regardless
```

`run_window2.py:213-216`, `:239-242`, `:329-331`; `run_live_window.py:179-183`, `:237-241`.
And `run_window2.py:431` proceeds to s04 on `("SUCCESS", "CONTRACT_INCOMPLETE")`, with the
explicit comment at `:426-429`: *"CONTRACT_INCOMPLETE still yields an applied patch and a
real mechanism; refusing to consume it would hide whether s04 can work from a
declared-incomplete producer, which is exactly the producer-consumer question this window is
asking."*

**So the ladder is: SCHEMA_FAILURE halts; CONTRACT_INCOMPLETE does not, deliberately.**
Every `S03_CHECKS` / `S04_CHECKS` result becomes a `CHECK_FINDING` row and **nothing
consumes it**. `selection_gate_check` iterates `SelectionDecision`, which **no code ever
creates**. `elimination` from s04a is attached to a Python attribute
(`state.s04a_elimination`, `run_window2.py:369`) and **never enters the state**.

**No freeze exists in code** — consistent with the contract's *"NO stage contract may
freeze"*. **There is no progressive-commitment gate: the architecture records unresolved
information and never acts on it.**

---

## §13 CAPABILITY GAP → FIRST CAUSAL BREAK → ROOT CAUSE

| Gap | First causal break | Root-cause class | Anchors |
|---|---|---|---|
| **CAP-01** distinct pivots | s04b schema has no axis field and no distinctness check; `completeness` requires only *a* placement | **MULTI-CAUSE**: RESPONSE SCHEMA + missing DETERMINISTIC DERIVATION. Information was available (envelopes re-projected), so a **MODEL REASONING** component remains for the coincidence itself | `s04.py:268-272`, `:311-322`; `run_window2.py:312` |
| **CAP-02** configuration distinctness | nothing compares two `State` coordinate sets | **ARCHITECTURE/CONTRACT** — no invariant, no check exists | `s04.py:297-300`, `:311-342` |
| **CAP-03** functional connection in structure | `Interface` has no transmission field; a non-joint transmitting relation has no typed home | **REPRESENTATION** | `DESIGN_STATE_CONTRACT` Interface; `s03.py:397-402` |
| **CAP-04** load-reaction closure | s02 prompt states the external-termination rule; **no check implements it**; `reaction`/`support` derivations unimplemented | **MULTI-CAUSE**: REPRESENTATION (no external-site type) + missing DETERMINISTIC DERIVATION | `s02.py:97-99, 356-385`; `s03.py:607-631`; `s04.py:652-671` |
| **CAP-05** retention testability | `AXIS_DIRECTIONS` includes `"NONE"` and the prompt offers it; presence checks treat `"NONE"` as present | **MULTI-CAUSE**: PROMPT (offers NONE) + RESPONSE SCHEMA + REPRESENTATION (relation never stored) | `s03.py:127`, `:536`, `:964`, `:933-954` |
| **CAP-06** DOF totality | `MobilityExpectation` is owned by s03 and requested by no prompt; the grid is built by a **tool** and completed by an unsupported default | **MULTI-CAUSE**: ARCHITECTURE/CONTRACT (ownership vs prompt) + DETERMINISTIC DERIVATION (D-3) | `s03.py:333-337`, `:411,424`; `run_window2.py:246-279` |
| **CAP-07** principle shape | the s02 prompt contradicts itself; the contract does not specify a shape; the code tolerates all three | **MULTI-CAUSE**: PROMPT + ARCHITECTURE/CONTRACT | `s02.py:103-105` vs `:191-192`; `s02.py:394, 407-409` |
| **CAP-08** selected principle realised | `principle_library`'s `basis`, `creates` and `depends_on_claims` are **never rendered** — `_render_families` emits only family names | **CONSUMER PROJECTION** (of the knowledge layer into the prompt) | `s02.py:198-203`; `principle_library.py:34-163` |
| **CAP-09** quantitative continuity | `S03_OWNED` excludes `Requirement`; `interface_gaps` has no quantity check | **CONSUMER PROJECTION**, deliberate | `run_window2.py:78-79, 103-123` |
| **CAP-10** typed-relation integrity | `_reference_problems` never inspects `bodies`; the free-string rule is unimplemented | **DETERMINISTIC DERIVATION / validator scope** | `design_state.py:105-119`; `s04.py:362-366` |
| **CAP-11** swept evidence | schema has no path/sampling field; the declaration is fabricated and self-validated | **MULTI-CAUSE**: RESPONSE SCHEMA + DETERMINISTIC DERIVATION (D-5) | `s04.py:268-272, 306-308, 503-520` |
| **CAP-12** gating | `declared_incompleteness` never stops execution; `UnresolvedDecision` is never read; `SAFE_REJECTION`/`FALSE_ACCEPTANCE` have no emitter | **GATING/PROGRESSION**, deliberate and documented | `run_window2.py:213-216, 426-431`; `status.py:50-51` |
| **CAP-13** capture / atomisation | `S01.completeness` checks only non-emptiness and two vocabularies | **ARCHITECTURE/CONTRACT** — no atomisation or ambiguity-coverage property is defined | `s01.py:164-176` |
| **CAP-14** repeated members | one `region_volume` per FunctionalRegion by schema; `instance_identity` is free text | **REPRESENTATION** | `s04.py:157`; `s03.py:382` |

**Fixture/evaluation-substrate cause, spanning several gaps:** the DOF grid and every
absorbed geometry field are authored by `run_window2.py`, an evaluation tool, not by a
stage. Window-2 evidence is therefore partly evidence about the harness.

---

## §14 PROVISIONAL FINDINGS WITHDRAWN OR NARROWED AFTER COMPLETE READING

1. **WITHDRAWN** — *"`region_occupancy_check` is dead because volumes are never stored."*
   `_absorb` (`run_window2.py:360-363`) writes `e["volume"]`. The check has data.
2. **WITHDRAWN** — *"`swept_clearance_check` never runs because `frame_origin` is never
   written."* `_absorb` (`:372-375`) writes it. The sweep is computed.
3. **WITHDRAWN** — *"`derive_mobility` has no caller."* `run_window2.py:257` calls it and
   applies a `MobilityExpectation` patch. **The MAINTAINED_BY_CLASS default is reached**, so
   that finding *strengthens*.
4. **WITHDRAWN** — *"the s03/s04 checks are vacuous."* They are wired at tool level in all
   three runners and operate on populated families.
5. **NARROWED** — *"EXTEND permits silent overwrite, so TYPE-B is possible."* True of the
   code path, but **no EXTEND op is ever constructed**; the real unguarded write is `_absorb`.
6. **NARROWED** — *"the shared `pairing_history` sentence indicates common authorship."*
   It is **written verbatim by `repair_prompt_pairing.py:167-169`**. It indicates the tool
   ran, not who authored the content. **BM fixtures remain UNKNOWN provenance.**
7. **RECLASSIFIED** — `blocked_direction: "NONE"` is **prompt-permitted**
   (`AXIS_DIRECTIONS` includes it), so it is a prompt/contract mismatch, not model error.

---

## §15 ARCHITECTURE-OF-RECORD vs IMPLEMENTATION DRIFT

| # | Architecture says | Code does |
|---|---|---|
| DR-1 | `assy_v3/__init__.py:3` *"THIS PACKAGE IS INTENTIONALLY EMPTY OF PIPELINE LOGIC"*; `:41` `stages/ … (absent by design)`; `:43` *"`stages/` does not exist"* | `assy_v3/stages/` contains **2,421 lines** of s01–s04 |
| DR-2 | `STAGE_PROGRESSION_CONTRACT:242-250` — the assurance projection is built **before s01**, *"If it is built last it becomes a report generator"* | **no `assurance/` package exists**; all four stages do |
| DR-3 | six operation kinds, SUPERSEDE keeps both | five kinds in code, **SUPERSEDE absent**, only CREATE ever used |
| DR-4 | invalidation cone marks dependents STALE | field declared, **never read** |
| DR-5 | *"A stage does not mutate DesignState"* | `_absorb` writes three geometry fields directly |
| DR-6 | free-string subject is a SCHEMA_FAILURE (R-20) | **no implementation**; `"desk edge"` crosses three stages |
| DR-7 | typed relations are first-class | **never stored; not in `Contracts.families`; `Op` cannot carry them** |
| DR-8 | `MobilityExpectation` owned by s03 | authored by an **evaluation tool** |
| DR-9 | *"A check declares the minimum maturity of its inputs"* | **no check reads any maturity field** |
| DR-10 | SAFE_REJECTION / FALSE_ACCEPTANCE are the poles | **no emitter** |
| DR-11 | INV-002 — source text never reaches s02 | **implemented and enforced twice.** No drift |
| DR-12 | providers never repair responses | **implemented.** `json.loads` only; no salvage. No drift |

---

## §16 PARSER / RAW-RESPONSE HANDLING — where transformation does and does not happen

**No transformation:**
- `deepseek.py:225` `raw_text = message.get("content") or ""`; `:285` retained verbatim;
  `:26-29` *"no fence stripping, no brace balancing, no 'extract the first JSON object'
  salvage."*
- `base.py:84` `parsed = json.loads(raw_text)` — no repair, no key coercion.
- `run_window2.py:417-418, 443-444` and `run_live_window.py:344-345` write
  `out.raw_response` **directly to disk**. This is why all 59 stored artifacts are
  byte-identical to `response.raw_text`.
- `deepseek.py:230` truncation from the provider's `finish_reason`, never guessed; a
  truncated response is never parsed (`base.py:79-82`).

**Transformation does happen — in `to_operations` and in the tool, not in the stored file:**
- `canonicalise_blocking` — nine documented renames plus a list→string coercion
  (`s03.py:67-95`), **recorded** and counted (`run_window2.py:251-253`).
- `nominal_status` → `nominal`, defaulting to `"NOMINAL"` (`s03.py:401`).
- Defaults D-6 … D-10 in §7.
- `_absorb` field attachment (`run_window2.py:346-375`).

**Extra keys:** `parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}` in
every stage; unknown top-level keys are simply not read. A malformed-but-useful structure
survives only where `.get(…, default)` tolerates it; a missing **required** key raises and
becomes SCHEMA_FAILURE (`base.py:94-101`).

---

## §17 PROVIDER / MODEL INVOCATION — §15 of the brief

**Temperature — the two facts, kept separate:**

- `base.py:71-74` builds `GenerationRequest(..., temperature=0.0, seed=7)`.
- `deepseek.py:161-167` builds the payload with `"temperature": self.temperature`.
  **`request.temperature` is read nowhere in `_attempt`.** The declared request field
  (`interfaces.py:74`) is **dead**.
- `self.temperature` comes from the constructor, defaulting to **1.0** (`deepseek.py:100`),
  and both runners pass their own CLI default of **1.0**
  (`run_window2.py:384,396`; `run_live_window.py:297,323`).

**Classification: BOTH of the following, and neither alone is sufficient.**
1. **Intended provider-level configuration** — the harness deliberately sets 1.0, and
   `run_live_window.py:9-13` states the purpose: *"runs the SAME prompts… many times, at a
   non-zero temperature"*. Repeated-trial evidence requires it.
2. **Request-contract violation** — `GenerationRequest.temperature` is part of the provider
   interface and is silently ignored. `base.py` sets 0.0 for every stage and no stage can
   influence sampling. It is **not** generic adapter behaviour and **not** model-specific.

**It is disclosed, not hidden:** `deepseek.py:304-305` records both
`temperature_requested_by_stage` and `temperature_actually_sent`, and the class docstring
(`:84-88`) names the divergence explicitly.

**Token clamp — treated separately, and it is not the same kind of thing.**
`MAX_OUTPUT_TOKENS_CEILING = 8192` (`deepseek.py:56`) is DeepSeek's documented ceiling;
`:157-159` clamps and records `max_output_tokens_clamped_from`. `capabilities()` declares it
(`:122`). **Legitimate provider limitation, correctly declared and recorded.** Its one
observed consequence — the `BM-003/t3/s02` truncation — is reported as `RESPONSE_TRUNCATED`
and never parsed.

`supports_seed=False` (`:126`), so `base.py`'s `seed=7` is discarded and `seed_honoured` is
recorded `"UNKNOWN"`. Model substitution is recorded through `served_model_id` and
`model_substitution` (`:238-240`). Retries are bounded and only on RATE_LIMIT / UNAVAILABLE
/ TIMEOUT (`:144-147`) — *"Never a retry on a response we simply did not like."*

---

## §18 GENUINELY UNRESOLVED — for P6 / P4B

1. Why is `MobilityExpectation` owned by s03 in the contract while only an evaluation tool
   creates it? Was a stage-level derivation intended and never wired?
2. Was `derive_mobility`'s `else` branch intended as a default, or as a placeholder? The
   docstring calls it *"the contract's own division of labour… finally implemented"* and
   does not mention the fallback.
3. Is `S03_OWNED` intended to exclude `Requirement` permanently, or is the missing
   quantity-gap check in `interface_gaps` the omission?
4. Why does `_absorb` exist outside the patch layer when `EXTEND` is defined and validated?
5. What was `frame_ids` (contract-required, prompt-unasked) meant to hold?
6. Is `LoadPath.maturity = "HYPOTHESIS"` an intended vocabulary extension or an error?
7. Nothing emits `SAFE_REJECTION` or `FALSE_ACCEPTANCE`. Was an emitter planned at s12?
8. The `principle_library` `depends_on_claims` keys are exactly the `_CLAIM_ROUTE` keys and
   `route_for_claim` is imported but never called. Was automatic evidence-route derivation
   intended?
9. Which contract governs `required_by_actors` / `reach_targets`, given they were added to
   satisfy `interface_gaps` and appear in no contract?
10. Does the assurance projection's absence (DR-2) block the progression contract's own
    ordering, and what was built in its place?

---

## §19 CODE ANCHORS FOR EVERY MAJOR CONCLUSION

`state/projection.py:12,18` · `state/patch.py:15,19-24,46` ·
`state/design_state.py:29-30,90-95,105-119,122-137` · `stages/base.py:71-74,84,113-123` ·
`stages/s01_requirement_capture.py:164-176,180-225` ·
`stages/s02_obligation_and_candidates.py:97-99,198-203,212-217,226-228,253-260,309-320,356-385,394,407-409,430-434,486-500` ·
`stages/s03_topology_and_mobility.py:41,48,67-95,101-118,127,195-256,267-339,342-349,376-452,483-513,534-544,607-631,672-684,748-772,775-809,825-876,880-911,933-979` ·
`stages/s04_envelope_and_motion.py:16-21,48-99,153,184-196,225-235,268-272,293-309,311-342,345-347,350-374,401-434,437-472,475-500,503-520,523-603,606-649,652-671,674-687` ·
`knowledge/principle_library.py:34-163,174` · `knowledge/capability_registry.py:15-55,58-74,77-84` ·
`providers/status.py:50-51,57-70` · `providers/interfaces.py:74` ·
`providers/offline.py:36-52` · `providers/agent_authored.py:72-80` ·
`live_providers/deepseek.py:56,84-88,100,122,126,144-147,157-159,161-167,225,230,238-240,285,304-305` ·
`tools/run_window2.py:75-79,94-100,103-123,151-168,175,183-188,213-216,221-224,246-279,281-286,293-343,346-375,382-384,396,426-431,443-444` ·
`tools/run_live_window.py:9-13,116-119,133-134,179-183,184-191,237-241,242-258,275-290,296-297,323` ·
`tools/run_window.py:42-101` · `tools/repair_prompt_pairing.py:20,116,122-123,135,150-154,165-175` ·
`assy_v3/__init__.py:3,6,41,43-45,50-52`

**P5 is COMPLETE. P6 is not started. No fix is proposed.**

---
---

# §20 ADDENDUM — THE TOPOLOGY → SPATIAL CAUSAL CHAIN, CLOSED

Narrow addendum. Uses only the already-read P5 corpus and the raw P4A artifacts.
**It corrects one statement in §9 and adds one previously unrecorded mechanism.**

## §20.1 What each stage stores, receives and authors

**S03 stores** (`s03.py:376-452`): `Body{instance_identity, role, created_by_stage,
addresses_obligations}`, `RigidGroup{body, members, is_default}`,
`Joint{joint_type, parent_group, child_group, dof, axis_direction, frame_ids=[], compliance}`,
`Interface{bodies, interaction_kind, nominal, addresses_obligations}`,
`Configuration{name, kind, bodies_present, expected_mobility=[]}`, `LoadPath`,
`AssemblyStep`, `FunctionalRegion{role, owning_bodies, required_by_actors, reach_targets}`,
`UnresolvedDecision`.

- **Joint incidence is expressed only as `parent_group`/`child_group` → `RigidGroup.body`.**
  There is no spatial content of any kind at s03 — by design (`s03.py:143-146`).
- **Repeated-member identity has no structural representation.** BM-003's three legs are
  three unrelated `Body` entities; the only marker is the free-text
  `instance_identity: "each of three identical"` (`s03.py:382`). **No relation links them,
  and nothing downstream can recover the correspondence.**
- `MobilityExpectation` is not created at s03 (§6).

**S04A receives** `mechanism_projection(state)` = the `S03_OWNED` whitelist, plus a computed
`_contact_pairs_text` (`s04.py:370-374`) rendering `required_contacts` (`s04.py:350-367`).
**The must-touch constraint is expressed at BODY-PAIR level, never at joint level.** Two
distinct joints connecting the same body pair produce one constraint line; nothing states
that two joints are distinct entities requiring distinct locations.

**S04A authors** `scale, envelopes, region_volumes, reach_results, assembly_directions,
elimination` (`s04.py:148-171`). **It authors no joint spatial fact — the s04a schema has no
joint field at all.** Only `Envelope` is patched (`s04.py:184-196`); `region_volumes` and
`assembly_directions` arrive by `_absorb`; `reach_results`, `elimination` and `scale` become
Python attributes and never enter the state.

## §20.2 THE CORRECTION — S04B never receives the arrangement

§9 stated that s04b receives the mechanism *"including the Envelope entities s04a created"*.
**That is wrong.** `run_window2.py:312` re-projects with `mechanism_projection`, and
`S03_OWNED` (`run_window2.py:78-79`) **does not contain `Envelope`**.

Verified directly against all six raw s04b prompts in
`window2/r_final/model_run_records.json`:

- **`Envelope` appears in 0 of 6.**
- Every `Body` object in the s04b input carries only
  `{addresses_obligations, created_by_stage, entity_id, instance_identity, role}` —
  **no extent, no centre, no pose.**
- The only `half_extent`/`centre` present belongs to `FunctionalRegion.volume`.

Yet the s04b prompt instructs: *"Where each JOINT sits — its frame origin, **as a position
in the same coordinates as the arrangement you were given**"*, under a heading reading
**"THE MECHANISM AND ITS ARRANGEMENT"**.

**The stage is told to place joints in a coordinate system it is not shown.**

## §20.3 A SECOND, PREVIOUSLY UNRECORDED MECHANISM — silent mid-JSON truncation

`_render` (`s04.py:377-381`) is `json.dumps(obj, indent=1, sort_keys=True)[:26000]` — a hard
character slice with no marker.

| Case | s04b mechanism block | `RigidGroup` present | how the block ends |
|---|---|---|---|
| BM-001 | 25,995 | **no** | `…constraint is defeated.",` |
| BM-002 | 6,360 | yes | `…"members": ["slider_platform"] } ] }` |
| BM-003 | **26,000** | **no** | `…"configuration": "CFG-0002", "derived_by":` |
| PRB-01 | 25,996 | **no** | `…"blocker_body": "BOD-0001",` |
| PRB-02 | 25,995 | **no** | `…{ "configuration": "CFG-0002",` |
| PRB-03 | 5,224 | yes | `…"members": ["BOD-0004"] } ] }` |

**Four of six s04b prompts are truncated mid-value; the typed input is syntactically invalid
JSON.** `RigidGroup` sorts last under `sort_keys=True`, so it is the first family lost —
**and `transitions[].moving_groups` is specified as "rigid group ids from the input"**, which
in those four cases the model could not see.

**What fills the budget is the derived DOF grid.** `MobilityExpectation` is the largest
family (BM-003: 7 groups × 3 configurations × 6 DOF = 126 entries, each carrying
`disposition`, `derived_by`, and a `holding_class` or blocking fields). The unsupported
default D-3 does not merely assert unearned facts — **its volume evicts the topology from
the consumer view.**

## §20.4 What the s04b schema can express, and what code adds

Schema (`s04.py:268-272`): `joint_placements[]{joint, origin[x,y,z]}`,
`state_coordinates[]{configuration, coordinates{joint: number}}`,
`transitions[]{id, from_configuration, to_configuration, moving_groups[]}`, `notes`.
**No axis field** (though the prompt asks for the axis in prose), **no path**, **no sampling**,
**no engagement localisation**, **no repeated-member correspondence**.

Deterministic additions: `sampling_declaration` fabricated from `SAMPLES = 9`
(`s04.py:306-308`); `frame_origin` attached by `_absorb` (`run_window2.py:372-375`).
`joint_placements` is **never a patch operation** — `S04B.to_operations` creates only `State`
and `Transition` (`s04.py:293-309`).

## §20.5 What is enforced — and what is not

| Property | Enforced? | Where |
|---|---|---|
| body-pair contact for joined bodies | **yes** | `S04A.completeness` `s04.py:225-235`; `joint_geometry_check` `s04.py:415-434` |
| every joint has *a* placement | **yes** | `S04B.completeness` `s04.py:314-316` |
| every configuration has coordinates | **yes** | `s04.py:317-320` |
| swept occupancy, keep-out entry | **yes** | `swept_clearance_check` `s04.py:523-603` |
| **joint/body incidence (origin inside a connected body)** | **no** | — |
| **distinct joints at distinct origins** | **no** | — |
| **non-zero rigid-link length between two joints on one body** | **no** | — |
| **repeated-member spatial consistency** | **no** | no correspondence exists to check |
| **prismatic guidance consistency (input axis vs output axis)** | **no** | — |
| **configuration-specific coordinate change** | **no** | nothing compares two `State`s |
| **S04A→S04B commitment preservation** | **no** | s04b never receives the commitment |

## §20.6 The six chains

**Format:** upstream available → projected → representable → model commitment → deterministic
post-processing → check → **first causal break**.

**1. BM-002 — three linkage joints at `[0,0,2.5]`.**
JNT-0001/2/3 exist as distinct entities with distinct group pairs → projected (block 6,360,
untruncated, `RigidGroup` present) → **body extents NOT projected** → model places three
origins at one point → `_absorb` writes all three `frame_origin` → no check compares origins.
**FIRST BREAK: CONSUMER PROJECTION** (no arrangement) **+ MISSING PHYSICAL INVARIANT.**
A residual **MODEL REASONING** component stands: the joint ids and group pairs were visible
and distinct, so nothing compelled coincidence.

**2. BM-002 — zero-length crank.**
A crank throw is the distance between the two joints on the crank link. It is not a stored
quantity anywhere — it is implied by two origins. Both origins are the model's, both are
`[0,0,2.5]`, and `DESIGN_STATE_CONTRACT` derives no link length.
**FIRST BREAK: MISSING PHYSICAL INVARIANT** (consequence of chain 1).

**3. BM-001 — compliant joint outside its body.**
JNT-0002 is internal to BOD-0003 (`RGP-0003`↔`RGP-0004`, both of BOD-0003) → projected →
**BOD-0003's envelope `centre [2,1,0] half [0.5,0.5,0.5]` was NOT in the s04b input**, and
BM-001's block was truncated at 25,995 → model emits `[0,0,0]` → `_absorb` stores it →
`joint_geometry_check` tests body-pair separation, **not** origin-in-body.
**FIRST BREAK: CONSUMER PROJECTION + MISSING PHYSICAL INVARIANT.** The model could not have
placed it inside the body: it was never shown where the body is.

**4. BM-003 — S04A's 120° symmetry collapsed by S04B.**
S04A authored `[0,1,0]`, `[1.732,−1,0]`, `[−1.732,−1,0]` → **stored as `Envelope`, which
`S03_OWNED` excludes** → s04b's block truncated at exactly 26,000 with `RigidGroup` gone →
model places all three pivots at `[0,1,0]` → no check compares s04a to s04b.
**FIRST BREAK: CONSUMER PROJECTION**, compounded by **DETERMINISTIC DERIVATION** (the DOF
grid's volume caused the truncation) **and S04A→S04B COMMITMENT NOT PRESERVED** — there is no
mechanism by which an s04a spatial commitment binds s04b, and no invalidation if it is
contradicted. **Not a model reasoning failure: the arrangement was withheld.**

**5. BM-002 — platform rises while the crank coordinate stays `0.0`.**
`state_coordinates` is a free `{joint: number}` map; the prompt asks for "the COORDINATE of
every joint in that configuration" and never requires any coordinate to change; `completeness`
checks only that each configuration is present (`s04.py:317-320`); no check relates a
configuration's declared function to which coordinate moves.
**FIRST BREAK: MISSING PHYSICAL INVARIANT** (label-vs-realisation), with
**REPRESENTATION INSUFFICIENT** — nothing ties a `Configuration` to the DOF that realises it,
because `expected_mobility` is defaulted `[]` (`s03.py:407`) and never populated.

**6. BM-003 — stored and deployed exist while leg coordinates never change.**
Same schema, same absent invariant. `CFG-0001` and `CFG-0003` are coordinate-identical and
`State` ids are `"STA-%s" % configuration` (`s04.py:298`), so two distinct `State` entities
exist with identical `joint_coordinates` and nothing compares them.
**FIRST BREAK: MISSING PHYSICAL INVARIANT + REPRESENTATION INSUFFICIENT.**

## §20.7 The general statements this supports

1. **The spatial realisation stage is not given the spatial arrangement its own prompt tells
   it to work in.** `S03_OWNED` governs both s04a and s04b, and `Envelope` — the only family
   carrying arrangement — is in neither view.
2. **No enforced mechanism-independent invariant requires topologically distinct joints to
   remain geometrically distinct where their kinematic role demands distinct locations**, and
   none requires a joint origin to lie within the bodies it connects.
3. **A spatial commitment made at s04a does not bind s04b**, and contradicting one raises
   nothing — there is no preservation check and no invalidation path (`invalidation_cone` is
   never read, §2.4).
4. **Repeated-member correspondence has no representation at any stage**, so its loss is not
   detectable rather than undetected.
5. **A configuration is a label with a free coordinate map.** No invariant requires two named
   configurations to differ in any generalised coordinate, or requires the coordinate that
   changes to be the one that realises the declared behaviour.
6. **A deterministic derivation that fills every cell of a large domain can evict the
   producer's own topology from the next consumer's view**, because rendering is bounded by a
   silent character slice rather than by content priority.
