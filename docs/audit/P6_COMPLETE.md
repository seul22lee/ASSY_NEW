# P6 — EVALUATOR / VALIDATOR ADEQUACY AUDIT

Axis A: **GENERATED EVIDENCE**. Axis B: **REVIEW RECORD**.

Complete read of the frozen P6 corpus. Nothing was rerun, modified or repaired. No
check, threshold, validator or prompt rule is proposed anywhere in this document.
P6 determines evaluator adequacy only.

The question: **do the current evaluators detect the engineering failures P4A already
established from raw artifacts?** The raw defect is ground truth; PASS/FAIL is not the
starting point.

Companions: `P1`–`P5_COMPLETE.md`, `P4A_CAPABILITY_GAP_SYNTHESIS.md`. All unmodified.

---

## §1 FILES READ COMPLETELY — 26 / 26

| File | Lines | File | Lines |
|---|---|---|---|
| `tools/quality_profile.py` | 432 | `tests/meta/test_package_path.py` | 179 |
| `tools/compare_maturity.py` | 199 | `tests/meta/test_benchmark_skeleton.py` | 292 |
| `tools/build_pipeline_dashboard.py` | 1,958 | `tests/meta/test_descriptor_manifest_consistency.py` | 168 |
| `tests/window/test_s01_s02_window.py` | 147 | `tests/meta/test_source_envelope.py` | 289 |
| `tests/meta/_paths.py` | 188 | `tests/meta/test_source_provenance.py` | 223 |
| `tests/meta/test_no_legacy_imports.py` | 131 | `tests/meta/source_audit.py` | 272 |
| `tests/meta/test_no_stage_implementation.py` | 124 | `tests/meta/test_source_audit.py` | 193 |
| `tests/meta/test_contracts_parse.py` | 64 | `tests/meta/freeze_gate.py` | 124 |
| `tests/meta/test_contract_references.py` | 239 | `tests/meta/test_freeze_gate.py` | 211 |
| `tests/meta/test_status_semantics.py` | 114 | `tests/meta/test_manifest_ordering.py` | 246 |
| `tests/meta/test_entity_family_audit.py` | 197 | `tests/meta/__init__.py`, `tests/__init__.py`, `tests/window/__init__.py` | 6 |
| `.github/workflows/ver3-boundaries.yml` | 47 | | |

The **stage-local and runner-level checks** (`s01`–`s04` check functions,
`run_window2.py`, `run_live_window.py`, `run_window.py`) were read completely in P5 and
are the engineering evaluators; they are treated here as P6 subjects, not re-read.

---

## §2 EVALUATOR JURISDICTION MAP

### 2.1 The four evaluator layers

| Layer | Where | Reads | Class |
|---|---|---|---|
| **A. Stage-local `completeness()`** | inside each stage | that stage's parsed response + its inputs | structural / schema completeness |
| **B. Module-level check functions** | `s01`–`s04`, called by the runners | the accumulated `DesignState` | mixed: referential, deterministic-geometric, a few mechanical |
| **C. Report layer** | `build_pipeline_dashboard.py`, `quality_profile.py`, `compare_maturity.py` | artifacts on disk | reporting / maturity metrics — **computes no verdict of its own** |
| **D. CI meta-tests** | `tests/meta/`, `ver3-boundaries.yml` | repository structure, contracts, **source** artifacts | structural / contract consistency |

### 2.2 Layer B — the only layer with engineering jurisdiction

| Check | Anchor | Actually tests | Class | Effect on status |
|---|---|---|---|---|
| `dof_totality_check` | `s03.py:483` | every (group, cfg, dof) appears exactly once | deterministic consistency | CHECK_FINDING |
| `blocking_relation_check` | `s03.py:516` | BLOCKED_BY entries carry non-empty direction/blocker/defeat/driver; blocker is a Body | referential + presence | CHECK_FINDING |
| `irrelevance_check` | `s03.py:548` | IRRELEVANT cites a scenario, and that scenario carries no LoadCase | **mechanical** | CHECK_FINDING |
| `assembly_acyclic_check` | `s03.py:575` | precedence is acyclic and order-consistent | deterministic consistency | CHECK_FINDING |
| `load_path_check` | `s03.py:607` | every LoadCase has a path; ≥2 hops; every hop is a known id | referential | CHECK_FINDING |
| `interface_classification_check` | `s03.py:634` | every interface classified; every joined body pair has an interface | referential | CHECK_FINDING |
| `retention_check` | `s03.py:656` | retained bodies declare a termination strategy | referential | CHECK_FINDING |
| `no_magnitude_check` | `s03.py:687` | no metric magnitude at s03 | structural | CHECK_FINDING |
| `obligation_ownership_check` | `s03.py:705` | s03-satisfiable obligations are claimed | referential | CHECK_FINDING |
| `functional_region_check` | `s03.py:732` | region has a role and a real owning body | referential | CHECK_FINDING |
| `compliance_check` | `s03.py:748` | eight compliance fields present; actuation is PRESCRIBED_KINEMATIC | structural | CHECK_FINDING |
| `simulation_completeness_check` | `s03.py:775` | endpoints resolve, axis in vocabulary, **graph connected** | **mechanical** | CHECK_FINDING |
| `envelope_coverage_check` | `s04.py:401` | every body has an extent; every extent a real body | referential | CHECK_FINDING |
| `joint_geometry_check` | `s04.py:415` | **body pairs** the topology joins are not placed apart | **geometric** | CHECK_FINDING |
| `configuration_interference_check` | `s04.py:437` | AABB overlap vs declared interface, conservatively | **geometric** | CHECK_FINDING |
| `region_occupancy_check` | `s04.py:475` | an ACCESS/APERTURE/KEEP_OUT region is not inside its owner | **geometric** | CHECK_FINDING |
| `sampling_declaration_check` | `s04.py:503` | declaration present, non-adaptive, ≥1 interior sample | structural | CHECK_FINDING |
| `swept_clearance_check` | `s04.py:523` | real swept hulls vs keep-outs and undeclared bodies | **geometric** | CHECK_FINDING |
| `assembly_path_check` | `s04.py:606` | insertion path vs already-placed bodies | **geometric** | CHECK_FINDING |
| `load_path_reaction_check` | `s04.py:652` | consecutive **body** hops touch | **geometric** | CHECK_FINDING |
| `selection_gate_check` | `s04.py:674` | SelectionDecision carries equal-coverage evidence | gating | **vacuous — no SelectionDecision is ever created** |

**Producer-local vs external.** Every Layer-B check lives in the same module as the
stage that produced the data, and is invoked by the same tool that ran the stage. **No
external evaluator exists.** The only artifact authored independently of the
implementation — the Oracle pack — is *displayed* by the dashboard and never evaluated
against (`build_pipeline_dashboard.py:1143-1147`: *"Shown for comparison; no verdict is
computed here"*).

### 2.3 Layer D has no jurisdiction over pipeline output

All 18 `tests/meta` files were read. **Not one reads a pipeline output artifact** — no
`s03`/`s04` JSON, no `trials.json`, no `model_run_records.json`, no
`fixtures/responses`. A corpus-wide search confirms the only apparent matches are the
word *envelope* meaning *source-manifest envelope* (`_paths.py:39`,
`test_source_envelope.py:96`) and *joint* as a source-text overprescription pattern
(`source_audit.py:44-46`).

They test: contracts parse and cross-reference; the status enum matches
`STATUS_SEMANTICS`; every entity family has an audited consumer; no legacy or network
import reaches `assy_v3`; one package path; benchmark source layout, hashes, envelopes
and provenance; the source-language overprescription/underdefinition audit; the freeze
gate over source manifests; manifest hash ordering.

**`source_audit.py` is the only check in the repository that inspects engineering
language — and it inspects the *input request*, never the output.**

---

## §3 FINDING → STATUS AGGREGATION, TRACED

```
check function returns a list of strings
  → run_window2.py:281-286 / :336-341   fail("CHECK_FINDING", name, p)
  → trials.json  failures[] row {kind, stage, what, detail}
  → dashboard discover_live_trials()      build_pipeline_dashboard.py:370-388
  → stage_evidence()                      :315-368
        status  := t["<sid>_status"]      ← EXECUTION STATUS ONLY
        findings := count of failures for that stage
  → render_stage_panel()                  :862-905
        SUCCESS              → PASS
        CONTRACT_INCOMPLETE  → CONTRACT INCOMPLETE
        TRUNCATED/SCHEMA/PARSE/RAISED → FAIL
        anything else        → WARNING
        if status == PASS and findings:  status = WARNING      ← :874-875
```

**Correction to a provisional P6 note.** I recorded that findings never affect the
verdict. They do: `:874-875` downgrades **PASS → WARNING** when any finding exists.
Corrected statement:

- SUCCESS + 0 findings → **PASS**
- SUCCESS + ≥1 finding → **WARNING**
- CONTRACT_INCOMPLETE + any number of findings → **CONTRACT INCOMPLETE** (the
  `if status == OK` guard means findings never touch it)
- **Scope-limited FAIL statement.** In the audited aggregation path —
  `build_pipeline_dashboard.py:862-905`, which is the only code in the P6 corpus that
  converts a recorded status into a displayed verdict — the `status` variable is
  assigned solely from `ev["status"]`, the recorded **execution status**. `FAIL` is
  assigned only at `:869-871`, for `RESPONSE_TRUNCATED`, `SCHEMA_FAILURE`,
  `RESPONSE_PARSE_FAILURE` and `RAISED`. `ev["findings"]` (`:874-875`) is read once and
  can only move `PASS → WARNING`. **Therefore, on this path, no CHECK_FINDING count or
  content escalates a verdict to FAIL.** This is a statement about the audited
  aggregation path only; it is not a claim about any path outside the P6 corpus.

**Upstream of the dashboard, the finding has no effect at all.** `run_window2.py:213-216`,
`:239-242`, `:329-331` record `declared_incompleteness` as a failure row and then call
`state.apply()` regardless; `:431` proceeds to s04 on `("SUCCESS", "CONTRACT_INCOMPLETE")`
with the documented rationale at `:426-429`. **Nothing consumes a CHECK_FINDING to stop,
reject or re-enter anything.**

**Summary-view aggregation.** The summary table (`:1695-1700`) has columns for case,
stage completion, **S01 harness status**, provenance, requirement/obligation/candidate
counts, unresolved, CAD, simulation. **There is no S03 or S04 status column.** `stage
completion` is `done/12` counting stages *with output* — presence, not correctness
(`:1621`, `:1653`).

---

## §4 KNOWN P4A DEFECT → EVALUATOR OUTCOME

**Population: 10 top-level P4A defects, rows A–J. Each row carries exactly one
classification; the categories are mutually exclusive at this level. Distribution:
NOT IN EVALUATOR JURISDICTION 3 · FALSE NEGATIVE 3 · SELF-FULFILLING CHECK 2 ·
GATING FAILURE 1 · PARTIALLY DETECTED 1 = 10.** This is a different and coarser
population from the detailed instance inventory in §5 — see §15.

| # | Raw defect | Evaluator with jurisdiction | Outcome |
|---|---|---|---|
| **A** | `MAINTAINED_BY_CLASS` synthesised without evidence, incl. `"joint class of no joint"` | `dof_totality_check` | **SELF-FULFILLING CHECK** |
| **B** | `MobilityExpectation.dispositions[].blocking_relation` references ids that exist in no entity | `design_state._reference_problems`, `blocking_relation_check` | **FALSE NEGATIVE** |
| **C** | BM-002 three joints at one origin; zero-length crank | none | **NOT IN EVALUATOR JURISDICTION** |
| **D** | BM-001 compliant joint outside its body | `joint_geometry_check` | **FALSE NEGATIVE — measures the wrong entity** |
| **E** | BM-003 s04a 120° symmetry collapsed by s04b | none | **NOT IN EVALUATOR JURISDICTION** |
| **F** | BM-002 crank fixed while platform rises; BM-003 legs fixed across configurations | none | **NOT IN EVALUATOR JURISDICTION** |
| **G** | Requirement quantities absent from the s04 view | `interface_gaps` | **FALSE NEGATIVE** |
| **H** | `sampling_declaration` fabricated from a constant | `sampling_declaration_check` | **SELF-FULFILLING CHECK** |
| **I** | Unresolved layer diagnoses the defect the same artifact commits | none | **GATING FAILURE** |
| **J** | Reactions terminating at the user's hand / the product body | `load_case_check`, `load_path_check`, `load_path_reaction_check` | **PARTIALLY DETECTED** |

### A — mobility fallback

`derive_mobility` (`s03.py:308-338`) emits exactly one entry per `(group, cfg, dof)`.
`dof_totality_check` (`s03.py:503-512`) asks whether every such triple appears exactly
once. **The producer guarantees the property the checker tests.** Neither the missing-cell
branch nor the duplicate branch can fire on derived output.

No evaluator inspects **evidence provenance**: `derived_by` and `holding_class` are
written (`s03.py:319`, `:334-337`) and **read by nothing**. `blocking_relation_check`
skips any disposition that is not `BLOCKED_BY` (`:528`), so a `MAINTAINED_BY_CLASS` entry
is never examined at all. **Totality is checked; correctness of disposition is not.**

### B — dangling relation references

`_reference_problems` (`design_state.py:105-119`) inspects only keys ending
`_id`/`_ids`/`_refs` plus five hard-coded names. `dispositions` is none of these, and its
values are dicts nested in a list, so the traversal never reaches `blocking_relation`.
`blocking_relation_check` reads `d.get("blocking_relation")` **never** — it checks
direction, blocker, defeat spec and driver only. **The reference resolves to nothing and
no check looks.** Entity-level references are validated; nested relation references are
not.

### C — collocated pivots, zero-length link

No evaluator compares two joint origins. `joint_geometry_check` compares **body-pair box
separation** derived from `required_contacts` (`s04.py:426-433`). `swept_clearance_check`
uses one origin at a time. No code derives a rigid-link length. And the overlap logic
inverts the concern: `configuration_interference_check` treats overlap as *possible
contact*, so **two joints at the same point produce no signal in a framework whose only
spatial predicate is "do these boxes overlap".**

### D — joint outside its body

`joint_geometry_check`'s docstring claims *"Bodies a joint connects must actually meet"* —
and that is what it tests: `boxes[pb]` vs `boxes[cb]`, body against body. **It never tests
the joint origin against either body.** BM-001's `JNT-0002` at `[0,0,0]` and `BOD-0003` at
`centre [2,1,0] half [0.5,0.5,0.5]` are never compared. Current spatial validity
establishes *bodies touch*, *boxes overlap or do not*, *sweeps stay clear of keep-outs* —
**it establishes nothing about where a joint is.**

### E — repeated-member collapse

Nothing tracks repeated-member correspondence (P5 §20.1: three legs are three unrelated
`Body` entities; the only marker is free-text `instance_identity`). **No evaluator compares
s04a placements against s04b placements** — s04b does not receive them (P5 §20.2), and
`Envelope` and `frame_origin` live on different entities with no relation between them. A
later stage may contradict an earlier spatial commitment with no invalidation:
`invalidation_cone` is never read (P5 §2.4). **There is no spatial-commitment-preservation
evaluator.**

### F — state labels without state change

No evaluator requires a transition to change the coordinate that realises the declared
behaviour. `S04B.completeness` (`s04.py:311-322`) checks that each configuration *has*
coordinates and that >1 configuration implies a transition. **Nothing compares two
`State` entities' `joint_coordinates`**, and nothing relates a `Configuration` to the DOF
that realises it — `expected_mobility` is defaulted `[]` (`s03.py:407`). Two named
configurations with identical coordinates are accepted.

### G — quantity lost before S04

`interface_gaps` (`run_window2.py:103-123`) is the interface-sufficiency evaluator. It
checks three things: bodies exist, configurations exist, and an ACCESS/APERTURE region
names an actor. **It inspects no quantitative requirement.** No evaluator compares the
consumer's responsibility against the accumulated DesignState, so `scale.absolute: null`
is never contrasted with a `Requirement` carrying `quantity_class: BAND`. `quality_profile`
cannot help: its 32 `MATURITY_KEYS` are all s01/s02 (`quality_profile.py:399-419`).

### H — invented sampling declaration

`sampling_declaration_check` (`s04.py:503-520`) verifies the declaration is a dict, is
not adaptive, and has `interior_samples ≥ 1`. **It does not check that a path was sampled**
— no path exists. `S04B.to_operations` (`s04.py:306-308`) writes
`{"kind":"UNIFORM","samples":9,"adaptive":False,"interior_samples":7}` from the module
constant `SAMPLES`. **Producer and evaluator are the same code path validating a value
that code just wrote.**

### I — unresolved vs commitment

No `UnresolvedDecision` severity exists — the family has no severity field, and nothing
reads the family back (P5 §12). `SUCCESS` means: the provider returned, the text parsed,
`to_operations` did not raise, `state.validate` found no problem, and `completeness()`
returned empty. **It carries no engineering claim.** A BLOCKING unresolved item cannot
prevent commitment because no unresolved item is classified, read or gated on. Maturity is
recorded and never read: no check declares a minimum input maturity, contrary to
`DESIGN_STATE_CONTRACT`. **No freeze exists in code**, consistent with the contract.

### J — load / reaction closure

Three checks touch it and none tests externality.
`load_case_check` (`s02.py:372-379`) fires `LOADCASE_ROLE_READS_AS_A_PART` when
`_reads_as_a_role` is false — a shape test (≥3 alphabetic words, no underscore, not
all-caps). *"the clamp body"* and *"the user's hands"* both pass.
`load_path_check` (`s03.py:628-630`) **would** flag `"NONE"`, `"desk edge"` and `"arm"` as
`LOADPATH_HOP_UNKNOWN` — a real detection — but tests neither externality nor cycles, and
`["BOD-0001","BOD-0001"]` passes the 2-hop minimum.
`load_path_reaction_check` (`s04.py:662-670`) filters to bodies with envelopes and tests
adjacency; the self-loop yields a non-positive gap.
**`reacted_at_role` participates in no check anywhere.** It is required by the S02 contract
and emitted by S02, and no downstream check consults it — so the s02 prompt's rule
(*"a load reacted against the product itself has not been reacted"*) has no implementation
at any layer.

---

## §5 DETAILED EVALUATOR-MISS INSTANCES

**Population: 12 instance-level misses, FN-1…FN-12 — a finer granularity than §4.**
One §4 row may expand into several instances (row C → FN-3 + FN-4; row J → FN-8 +
FN-10), and two instances (FN-9, FN-11) have no §4 row of their own. The `FN-`
prefix is retained for stable referencing; **it does not assert that every row is a
false negative** — the taxonomy split is given below the table and reconciled in §15.

| # | Defect | Why it passes | Anchor |
|---|---|---|---|
| FN-1 | nested `blocking_relation` dangling | traversal is opt-in by field-name suffix | `design_state.py:111-113` |
| FN-2 | joint origin outside its bodies | the check compares bodies, not the joint | `s04.py:426-433` |
| FN-3 | coincident joint origins | no predicate compares two origins | — |
| FN-4 | zero-length link between two joints | no derived link length | — |
| FN-5 | s04a→s04b spatial contradiction | no preservation check; s04b lacks the input | P5 §20.2 |
| FN-6 | identical coordinates in distinct configurations | nothing compares two `State`s | `s04.py:311-322` |
| FN-7 | stated quantity absent from the consumer view | `interface_gaps` has no quantity term | `run_window2.py:103-123` |
| FN-8 | reaction at a non-external site | no externality predicate | `s02.py:309-320` |
| FN-9 | `blocker_body` equal to the retained group's own body | blocker is only checked to *be* a Body | `s03.py:542-544` |
| FN-10 | cyclic load path | only length and hop-resolution are tested | `s03.py:623-630` |
| FN-11 | `blocked_direction: "NONE"` | `"NONE"` is truthy, and the prompt permits it | `s03.py:536`; `s03.py:127` |
| FN-12 | repeated members collapsed | no correspondence exists to check | — |

### §5.1 Taxonomy split — corrected

The first draft of this section labelled FN-3, FN-4, FN-5, FN-6 and FN-12 as
NOT ESTABLISHABLE FROM CURRENT REPRESENTATION. **Re-checked against the P5 code
already read, four of those five are in fact establishable from the stored state**,
and the label is corrected here. The evidence is that the relevant fields are not
merely present but are *already read by existing checks*:

- `Joint.frame_origin` is written into `state.entities` by `_absorb`
  (`run_window2.py:372-375`) **and is read** by `swept_clearance_check`
  (`s04.py:535-538`). Two origins are therefore comparable → **FN-3 and FN-4 are
  establishable.**
- `Envelope` entities are created by `S04A.to_operations` (`s04.py:190-195`) **and are
  read** by `_boxes(state)` (`s04.py:387-394`). An evaluator running after s04b can
  compare an s04a envelope with an s04b origin → **FN-5 is establishable.** What s04b
  lacked was the arrangement *as prompt input* (P5 §20.2); that is a producer-input gap,
  not an evaluator-representation gap, and the two must not be conflated.
- `State.joint_coordinates` is stored by `S04B.to_operations` (`s04.py:298-300`) **and is
  read** by `swept_clearance_check` (`s04.py:557-558`) → **FN-6 is establishable** in its
  plain form (are two `State`s coordinate-identical).

| Classification | Instances | Count |
|---|---|---|
| **FALSE NEGATIVE** — information present in state, no predicate examines it | FN-1, FN-2, FN-3, FN-4, FN-5, FN-6, FN-7, FN-8, FN-9, FN-10, FN-11 | **11** |
| **NOT ESTABLISHABLE FROM CURRENT REPRESENTATION** | FN-12 | **1** |
| | | **12** |

**FN-12 is the only genuine representation gap at instance level.** Repeated-member
correspondence has no typed home: BM-003's three legs are three unrelated `Body`
entities and the only marker is the free-text `instance_identity` (P5 §20.1). No
evaluator can establish "these three are instances of one member" because the state does
not say so.

**One partial case, recorded rather than forced.** FN-6 has two readings. *Are two
`State`s coordinate-identical?* — establishable, hence FALSE NEGATIVE above. *Did the
coordinate that realises the declared behaviour change?* — **not establishable**, because
`Configuration.expected_mobility` is defaulted `[]` (`s03.py:407`) and nothing links a
configuration to the DOF that realises it. The weaker question is a false negative; the
stronger one is a representation gap.

**This correction does not alter §4.** No §4 row was classified using the
not-establishable label, and rows C, E and F remain **NOT IN EVALUATOR JURISDICTION** —
that category is about whether any evaluator claims the property, which is orthogonal to
whether the state would support one. For C, E and F the state *would* support an
evaluator and none exists; that is precisely why "not in jurisdiction" rather than "not
establishable" is the correct label for them.

---

## §6 FALSE-POSITIVE INVENTORY

Genuinely few. Two structural claims overstate what the machinery provides:

| # | Claim | Reality |
|---|---|---|
| FP-1 | The dashboard renders, for any recording carrying `prompt_sha`: *"The provider refuses this recording if the stage builds a different prompt, so a stale answer cannot be replayed"* (`:1207-1209`) | True of `AgentAuthoredProvider`; **`run_window2.py:157` uses `OfflineReplayProvider`, which performs no such check** (P5 §8). The guarantee is asserted for an execution path that does not provide it |
| FP-2 | The Summary banner states *"S03–S12 are NOT IMPLEMENTED or NOT RUN and are shown as such"* (`:1722-1726`) | A hard-coded string. S03 and S04 **have run**; the page's own `discover_live_stage_outputs` finds their 24 artifacts and renders them. The banner contradicts the page's content |

The repository's documented false-positive history is otherwise good: `s03.py:709-714`
records a check that produced *"48 findings, 0 true positives"* and was rewritten;
`s02.py:503-511` records an actor rule that produced *"four findings and no true
positives"* and was narrowed; `source_audit.py` keeps a reviewed-and-fixed register.

---

## §7 SELF-FULFILLING CHECKS

Confirmed from code, not from rhetoric.

| Check | Producer | Why self-fulfilling |
|---|---|---|
| `dof_totality_check` | `derive_mobility` (`s03.py:308-338`) | the derivation emits exactly one entry per domain triple; the check asks whether exactly one entry exists per domain triple. **Cannot fail on derived output** |
| `sampling_declaration_check` | `S04B.to_operations` (`s04.py:306-308`) | the code writes `adaptive: False` and `interior_samples: 7`; the check asserts `not adaptive` and `interior_samples ≥ 1`. **Cannot fail** |
| `test_s01_s02_window.py` | the fixtures it replays | the recordings were authored with the validators in view — the dashboard says so itself (`:1200-1204`): *"It is NOT evidence that the reasoning works"* |

`selection_gate_check` (`s04.py:674-687`) is a fourth case of a different kind: not
self-fulfilling but **vacuous** — it iterates `SelectionDecision`, which no code creates.

---

## §8 STRUCTURAL COMPLETENESS PRESENTED AS ENGINEERING VALIDITY

| # | Artifact | Claim | What it tests |
|---|---|---|---|
| SC-1 | `test_reaction_sites_are_not_defaulted` | docstring: *"No probe stands on a desk; none may claim a desk reacts its load"* | `assertTrue(sites)` and `any(s.strip() …)` — **non-emptiness** (`:140-147`) |
| SC-2 | `quality_profile.load_cases_declaring_a_reaction_site` | a maturity term about reaction sites | presence of *a* site. *"the user's hands"* scores 1.0 |
| SC-3 | `quality_profile.acceptance_contracts_with_predicates` | acceptance-contract maturity | non-empty list. BM-001 t1's fabricated *"1000 cycles / 5N / ABS"* scores **1.0**; the honest `[]` scores **0.0** |
| SC-4 | dashboard `stage completion` bar | apparent progress | count of stages with output present (`:1621`, `:1653`) |
| SC-5 | `compliance_check` | *"never collapses required_travel and allowable_travel into one number"* | `str(x).strip()` non-emptiness — `"UNKNOWN"` and `"UNSUPPORTED"` pass (`s03.py:766-768`) |
| SC-6 | `blocking_relation_check` presence test | a testable blocking claim | non-empty string; `"NONE"` passes (`s03.py:534-536`) |

**SC-3 is the sharpest:** the repository's operational definition of engineering maturity
rewards a fabricated numeric predicate and penalises the honest refusal to supply one —
inverting `SAFE_REJECTION`, which the status vocabulary calls correct behaviour that must
never be penalised (`status.py:24-25`).

---

## §9 PROGRESSION / GATING FAILURES

| # | Gate | Status |
|---|---|---|
| G-1 | CHECK_FINDING → progression | **no effect.** Recorded only; nothing consumes it |
| G-2 | CONTRACT_INCOMPLETE → progression | **no effect**, deliberately and documented (`run_window2.py:426-431`) |
| G-3 | UnresolvedDecision → commitment | **no effect.** No severity, never read back |
| G-4 | Maturity → check precondition | **no effect.** No check reads a maturity field |
| G-5 | Selection gate | **vacuous.** No `SelectionDecision` is ever created; `--candidates` defaults to 1 |
| G-6 | `elimination` | **never stored.** Attached to a Python attribute (`run_window2.py:369`) |
| G-7 | `SAFE_REJECTION` / `FALSE_ACCEPTANCE` | **no emitter anywhere** (P5 §2.4), though `test_status_semantics.py` asserts their ordering |
| G-8 | CI → behavioural test | **`ver3-boundaries.yml:33` discovers `ver3/tests/meta` only. `ver3/tests/window/` is not in the discovery root, so the only behavioural test never runs in CI** |
| G-9 | CI → stage existence | `ver3-boundaries.yml:41-47` fails if `ver3/assy_v3/stages` exists. **It exists.** Meanwhile `test_no_stage_implementation.py` was rewritten to permit contracted stages (*"This guard was 'no stage may exist' while none did"*). **The Python test and the shell step now disagree**; the workflow cannot pass on this tree |

---

## §10 PLANNED INVARIANT → IMPLEMENTED SEMANTIC EQUIVALENT

Judged on semantics, not filenames.

| Intended invariant | Implemented check | Actual semantics | P4A defect | Verdict |
|---|---|---|---|---|
| **INV-002** source text never reaches s02 | `projection.py:18`, `s02.py:226-228`, `test_contract_references.test_only_s01_reads_source_text`, `test_s01_s02_window.test_s02_never_sees_source_text` | exactly as intended, enforced structurally and twice | — | **IMPLEMENTED** |
| **INV-001** free-string subject is SCHEMA_FAILURE (R-20) | none | `_reference_problems` cannot see `bodies`; `"desk edge"` crosses three stages | `"desk edge"`, `"arm"` | **MISSED** |
| **INV-003/004** geometry proven by geometry; no defaulted unit/axis/placement | `no_magnitude_check` (s03 only) | prevents magnitudes appearing early; **nothing prevents a placement being asserted without derivation** | fabricated `sampling_declaration`; `frame_origin` unvalidated | **PARTIAL** |
| **label is not realization** | none | `Configuration.kind`, `State.name` are free strings; no check ties a label to a realised DOF | BM-002, BM-003 configurations | **MISSED** |
| **two extrema are physically distinct** | none | nothing compares two `State`s | BM-002, BM-003, PRB-02 | **MISSED** |
| **DOF totality** (`MobilityExpectation`) | `dof_totality_check` | totality holds by construction; disposition correctness untested | `MAINTAINED_BY_CLASS` fallback | **SELF-FULFILLING** |
| **stage/consumer sufficiency** (`STAGE_PROGRESSION` step 6) | `interface_gaps` | three structural conditions; **the contract's sufficiency probe does not exist** | quantity loss | **PARTIAL** |
| **referential integrity** | `_reference_problems` + per-stage checks | entity-level references validated; **nested relation references not traversed** | dangling `blocking_relation` | **PARTIAL** |
| **INV-007** no selection before comparable completeness | `no_selection_check`, `no_selection_check_s03`, `selection_gate_check` | the first two genuinely detect ranking fields; the third is vacuous | one candidate embodied per case | **PARTIAL** |
| **ownership / provenance** | `design_state.may_create`, `test_entity_family_audit` | CREATE ownership enforced; **`_absorb` bypasses it entirely** | `frame_origin`, `volume`, `insertion_direction` | **PARTIAL** |
| **INV-018** determinism | `test_status_semantics`, canonical serialisation | vocabulary and serialisation checked; `test_stage_determinism.py` referenced by the contract **does not exist** in this corpus | — | **PARTIAL** |

---

## §11 EVALUATOR CAPABILITIES THAT ARE GENUINELY STRONG

Stated because an adequacy audit that reports only gaps is not evidence-based.

1. **Conservatism is correctly implemented.** `s04.py:16-21` states that AABB no-overlap
   proves clearance and overlap proves nothing, and every spatial check honours it:
   `CLEARANCE_NOT_VERIFIED`, `UNDECLARED_PAIR_OVERLAPS` and `SWEEP_MEETS_UNDECLARED_BODY`
   all report NOT_VERIFIED, never FAIL. **No manufactured failures.**
2. **Real geometric computation exists and runs.** `swept_clearance_check` builds genuine
   swept hulls with interior sampling (`s04.py:577-587`); `assembly_path_check` sweeps an
   insertion path against already-placed bodies **in the configuration produced by the
   preceding steps**, which is the harder and correct question.
3. **`simulation_completeness_check` tests graph connectivity** — a real mechanical
   property, not a schema property.
4. **`irrelevance_check` cross-validates a disposition against LoadCases** — the one
   disposition not checkable from the joint graph is checked against independent evidence.
5. **Absence is never success.** The dashboard has four distinct absence statuses and a
   fifth for self-declared incompleteness, with an explicit legend (`:1729-1734`).
6. **Evidence ranking is honest.** Within one evidence tier the **worst** status wins
   (`:362-366`), explicitly to stop a passing pass masking an incomplete sibling.
7. **Provenance is not flattened.** Fixture replay is labelled *"NOT evidence that the
   reasoning works"* (`:1200-1204`); reference artifacts carry a banner stating no stage
   produced them (`:1470-1473`); interrupted validation directories are quarantined and
   named rather than silently dropped (`:1414-1418`).
8. **The cross-artifact inconsistency scan is real work**: duplicate harness reports,
   conflicting rows, missing manifests, `fast_mode` summaries, unparseable YAML
   (`:1495-1558`).
9. **`quality_profile` refuses similarity scoring.** *"any metric that rewards similarity
   to a benchmark answer is measuring the wrong thing"* — and `None` for a zero
   denominator is distinguished from zero.
10. **The meta-test suite is rigorous within its jurisdiction**: bidirectional enum↔contract
    drift, entity-family consumer justification with owner/consumer ordering, single
    package path including symlink detection, source hashes, and a freeze gate whose three
    fields are proven to block independently.
11. **`source_audit.py` is phrase-aware and keeps a false-positive register**, with the
    deliberate refusal to ban the bare adjective *loose*.

---

## §12 RECURRENT EVALUATOR GAPS

Meeting the §9 scientific threshold: shared evaluator code, cross-case occurrence,
architecture invariant, or representation-level impossibility.

| Gap | Support |
|---|---|
| **EG-1 No mechanism-independent invariant establishes topology-to-spatial joint distinctness or non-degeneracy** | shared code path (`s04.py`); 5 of 6 cases; no predicate exists |
| **EG-2 Spatial validity is established at body granularity only; joint incidence is never tested** | `joint_geometry_check` compares bodies; cross-case |
| **EG-3 No evaluator establishes that a named state is physically distinct from another** | 3 of 6 cases; contract-level (label-is-not-realisation) |
| **EG-4 No evaluator establishes that a load terminates outside the product** | 6 of 6 cases; the prompt rule has no implementation at any layer |
| **EG-5 The engineering evaluator layer is producer-local; the only independent artifact is displayed, never evaluated** | architecture: no `validation/` substrate; Oracle shown with *"no verdict is computed here"* |
| **EG-6 A deterministically derived value is validated by a check testing the property the derivation guarantees** | two confirmed instances (DOF totality, sampling declaration) |
| **EG-7 Engineering findings cannot produce a failing verdict, and cannot stop progression at any layer** | 3 runners share the pattern; dashboard caps findings at WARNING |
| **EG-8 Maturity has no S03/S04 term** | `quality_profile` 32/32 keys are s01/s02; `compare_maturity` structurally cannot load Window 2 |
| **EG-9 No behavioural test covers any stage where the physical defects occur, and the one that exists is outside the CI discovery root** | `tests/window/` vs `ver3-boundaries.yml:33` |

---

## §13 QUESTIONS REMAINING FOR P4B

1. What is `SUCCESS` intended to assert? It currently means the machinery ran; the
   dashboard renders it green; and the architecture's engineering poles have no emitter.
2. Was `dof_totality_check` intended to run against **model-authored** dispositions —
   in which case the deterministic derivation removed its subject?
3. Should `interface_gaps` be the sufficiency probe `STAGE_PROGRESSION` step 6 requires,
   or is that probe still unwritten?
4. Is the Oracle intended to remain display-only, or is it the missing external evaluator?
5. Why does the CI shell step still forbid `ver3/assy_v3/stages` when the meta-test that
   governs the same rule was rewritten to permit it?
6. Is `tests/window/` deliberately outside CI discovery?
7. Should `acceptance_contracts_with_predicates` reward a predicate the input cannot
   support, given `SAFE_REJECTION` must never be penalised?
8. Two report-layer claims (FP-1 prompt pairing, FP-2 the S03–S12 banner) are stale.
   Is either load-bearing for how the evidence has been read?

---

## §14 ANCHORS

`tools/build_pipeline_dashboard.py`: 63-73, 296-308, 315-368, 370-388, 473-512, 515-532,
538-556, 606-711, 718-747, 831-908, 1056-1062, 1065-1087, 1112-1155, 1195-1218, 1470-1476,
1495-1558, 1584-1588, 1620-1664, 1668-1700, 1702-1736.
`tools/quality_profile.py`: 1-27, 62-64, 395-419, 421-432.
`tools/compare_maturity.py`: 1-16, 64-104, 118-142.
`tests/window/test_s01_s02_window.py`: 35-53, 61-83, 85-90, 92-98, 107-114, 116-121,
123-138, 140-147.
`tests/meta/`: `_paths.py:39,55-75`; `test_contracts_parse.py:23-63`;
`test_status_semantics.py:33-52,79-96,111-120`; `test_entity_family_audit.py:28-96,141-176`;
`test_no_stage_implementation.py:32-60,66-80,84-93`; `test_no_legacy_imports.py:28-70`;
`test_package_path.py:75-140`; `source_audit.py:34-140,196-243`;
`test_source_audit.py:20-75,81-117,121-159`; `freeze_gate.py:26-118`;
`test_freeze_gate.py:21-106,110-153`; `test_benchmark_skeleton.py` (22 tests);
`test_descriptor_manifest_consistency.py` (14); `test_source_envelope.py` (29);
`test_source_provenance.py` (13); `test_manifest_ordering.py` (15).
`.github/workflows/ver3-boundaries.yml`: 32-33, 41-47.
Stage checks (read in P5): `s02.py:309-320,356-385`; `s03.py:127,483-513,516-545,548-572,
575-604,607-631,634-653,656-684,687-702,705-729,732-745,748-772,775-809`;
`s04.py:16-21,306-308,311-342,401-412,415-434,437-472,475-500,503-520,523-603,606-649,
652-671,674-687`; `run_window2.py:103-123,213-216,281-286,329-331,336-341,346-375,426-431`.

---

## §15 FINAL COUNT AND TAXONOMY RECONCILIATION

Added as a narrow consistency pass over this document. **No substantive finding changed**
except the instance-level taxonomy split in §5.1, which is a bookkeeping correction
supported by code already read in P5.

### §15.1 Two populations, explicitly defined

| | **TOP-LEVEL DEFECT CLASSIFICATION** (§4) | **DETAILED EVALUATOR-MISS INSTANCES** (§5) |
|---|---|---|
| Unit | one row per P4A defect as stated in `P4A_CAPABILITY_GAP_SYNTHESIS` | one row per distinct evaluator miss |
| Size | **10** (A–J) | **12** (FN-1…FN-12) |
| Exclusive? | **yes** — one classification per row | **yes** — one classification per row |
| Assignments | **10** | **12** |
| Denominator for any "of the …" statement | **/10** | **/12** |

They are not nested one-to-one. Row C expands into FN-3 and FN-4; row J into FN-8 and
FN-10; rows A, H and I have no FN row (they are not misses — they are a self-fulfilling
check, a self-fulfilling check, and a gating failure). FN-9 and FN-11 have no §4 row.

### §15.2 Corrected category counts

**§4 — 10 unique defects, 10 assignments:**

| Category | Rows | Count |
|---|---|---|
| NOT IN EVALUATOR JURISDICTION | C, E, F | **3** |
| FALSE NEGATIVE | B, D, G | **3** |
| SELF-FULFILLING CHECK | A, H | **2** |
| GATING FAILURE | I | **1** |
| PARTIALLY DETECTED | J | **1** |
| **Total** | | **10** |

**§5 — 12 unique instances, 12 assignments:**

| Category | Instances | Count |
|---|---|---|
| FALSE NEGATIVE | FN-1…FN-11 | **11** |
| NOT ESTABLISHABLE FROM CURRENT REPRESENTATION | FN-12 | **1** |
| **Total** | | **12** |

### §15.3 What the inconsistency was

The §4 matrix has always summed to 10. The error was in the **spoken summary** that
accompanied this document, which reported FALSE NEGATIVE as 4 rather than 3 and therefore
implied a population of 11. **The matrix itself was correct; the narration was not.** The
document previously stated no denominator, which is what allowed the mismatch to pass
unnoticed; §4 and §5 now state theirs.

The second apparent conflict — "3 false negatives" (§4) against "12 false negatives"
(§5) — was two populations sharing one word. They are now named
**TOP-LEVEL DEFECT CLASSIFICATION** and **DETAILED EVALUATOR-MISS INSTANCES**, and §5 is
retitled accordingly.

### §15.4 Taxonomy definitions in force

| Label | Means |
|---|---|
| **FALSE NEGATIVE** | the evaluator had sufficient representation and jurisdiction and did not detect the established defect |
| **NOT IN EVALUATOR JURISDICTION** | no current evaluator claims or tests that engineering property, whether or not the state would support one |
| **NOT ESTABLISHABLE FROM CURRENT REPRESENTATION** | the state does not expose enough information for any evaluator to establish the property |
| **SELF-FULFILLING CHECK** | the producer or derivation guarantees the structural property the check later verifies |
| **PARTIALLY DETECTED** | some aspect is found; the engineering defect itself is not established |
| **GATING FAILURE** | a relevant finding exists and does not appropriately control progression or status |

*Not in jurisdiction* and *not establishable* are orthogonal, not ordered: a property may
be perfectly establishable from state and still have no evaluator (§4 rows C, E, F), and
that is the more serious of the two because nothing is missing except the check.

### §15.5 Corrected CHECK_FINDING scope statement

**In the audited aggregation path only** — `build_pipeline_dashboard.py:862-905`, the
sole code in the P6 corpus converting a recorded status into a displayed verdict:

- `status` is assigned exclusively from `ev["status"]`, the recorded execution status.
- `FAIL` is assigned only at `:869-871`, for `RESPONSE_TRUNCATED`, `SCHEMA_FAILURE`,
  `RESPONSE_PARSE_FAILURE`, `RAISED`.
- `CHECK_FINDING` reaches this path only as the integer `ev["findings"]`
  (`stage_evidence`, `:337-340` and `:356-359`), read once at `:874-875`, where it can
  only move `PASS → WARNING`.
- `CONTRACT_INCOMPLETE` maps at `:867-868` and, because of the `if status == OK` guard at
  `:874`, is never modified by findings.

**Established:** on this path, CHECK_FINDING count and content do not escalate a verdict
to FAIL. **Not established and not claimed:** anything about paths outside the P6 corpus.
The separate upstream observation stands on its own anchors — `run_window2.py:213-216`,
`:239-242`, `:329-331`, `:426-431` — where a finding or declared incompleteness does not
stop `state.apply()` or the progression to s04.

---

**P6 is COMPLETE. P4B is not started. No fix is proposed.**
