# AUDIT_SCOPE — frozen corpus for the S01–S04 pipeline audit

**Revision 2 — final.** Supersedes revision 1 of this file in this session.
Reading begins immediately under this scope.

**The central subject of this audit is the S01–S04 pipeline and what it actually
produces.** Oracle and CAD material are supporting engineering references. They
establish the quality bar; they are not systems to re-certify, and they must not
dominate the analytical space.

This corpus was reconstructed from the repository in this session. It inherits
nothing from `docs/audit/S01_S04_AUDIT_READ_INVENTORY.md` or
`docs/audit/P1_RUNNING_EVIDENCE_LOG.md`; both are prior claims, not evidence, and
their `COMPLETE` markings are void.

---

## 0. What the audit must determine

1. What engineering reasoning S01–S04 were intended to perform.
2. What reasoning the pipeline actually performs.
3. What DeepSeek actually authors at each stage.
4. What deterministic code derives, transforms, repairs, removes or invents.
5. Whether stage outputs are mechanically coherent and mature.
6. Whether each producer supplies sufficient structured engineering information
   to its consumer.
7. Whether validators distinguish engineering correctness from schema
   completeness.
8. Where implementation drifted from intended architecture.
9. Whether the pipeline genuinely helps a relatively inexpensive LLM reason more
   like a competent mechanical designer.

Not optimised for: benchmark answer similarity, one mechanism, DeepSeek-specific
prompt tricks, or benchmark-specific engineering rules.

---

## 1. Two-axis classification (mandatory)

Every corpus item carries **both**. "This code runs" is not "this defines what
the architecture means."

**Axis A — normative / governance status**
`NORMATIVE AUTHORITY` · `GOVERNING POLICY` · `SUPERSEDED NORMATIVE` ·
`HISTORICAL CLAIM` · `GENERATED EVIDENCE` · `UNKNOWN`

**Axis B — operational role**
`PIPELINE IMPLEMENTATION` · `EVALUATION IMPLEMENTATION` · `CI / ENFORCEMENT` ·
`GENERATED OUTPUT` · `REFERENCE ARTIFACT` · `POLICY / CONTRACT` ·
`REVIEW RECORD` · `NONE`

Where implementation, contract, CI and historical documents disagree, the
disagreement is preserved until the authority chain is established. It is not
resolved by preferring whichever artifact currently executes.

**Read tiers.** `FULL` — complete read, no grep-first. `SKIM` — read for the
specific engineering facts named in the row; not a licence to summarise a file
whose content later carries a finding. `INSPECT` — images, viewed directly.
`STRUCTURAL` — machine-emitted numeric records: every status/verdict/finding
field read, per-sample arrays queried. `EXCLUDED` — with reason, escalatable.

---

## 2. Reading order

```
P1   Intended S01–S04 architecture
P2   Contracts / representation / ownership
P3   Minimal engineering reference (Oracle results + CAD reference, quality bar only)
P4A  BLIND stage-by-stage engineering review of actual outputs   ← before P5
P5   Implementation / prompts / deterministic derivation / git drift
P6   Evaluator and validator adequacy
P4B  Output ↔ reference ↔ evaluator cross-check
     Final synthesis
```

**P4A precedes P5 deliberately.** Implementation intent must not be available to
explain away an engineering defect visible in the output. In P4A the actual
outputs are read as a mechanical designer would read a design description —
reconstructing the mechanism — with no access to why the code produced them.

**P4B is the only place** where a pipeline output is compared to an Oracle or CAD
reference, and only after the output has been independently understood.

---

## 3. Effort allocation

| priority | corpus |
|---|---|
| **VERY HIGH** | actual S01/S02/S03/S03B/S04A/S04B outputs · DeepSeek live responses · contracts · DesignState representation · S01–S04 implementation · prompts · parsers · deterministic derivations · producer/consumer boundaries · BM vs PRB |
| **HIGH** | intended S01–S04 architecture · architecture-critical git history · validator adequacy |
| **REFERENCE ONLY** | Oracle internals, governance and correction history · CAD validator infrastructure · simulation implementation |

Revision 1 of this document allocated ~35,600 lines to Oracle/CAD material. That
package is cut to ~9,900 lines of result-bearing reference here. The deleted
material is listed in §11 and remains escalatable.

---

## Package 1 — Intended S01–S04 architecture

**22 files · 9,697 lines · all FULL**

| path | axis A | axis B | why it belongs | Q |
|---|---|---|---|---|
| [ver3/REBUILD_POLICY.md](../../ver3/REBUILD_POLICY.md) (261) | GOVERNING POLICY | POLICY / CONTRACT | The governing statement for the rebuild; its rule numbers are cited by name inside meta-tests | 1, 8 |
| [ver3/REPOSITORY_LAYOUT.md](../../ver3/REPOSITORY_LAYOUT.md) (182) | GOVERNING POLICY | POLICY / CONTRACT | Declares who may read what — the read-permission model S01–S04 must obey | 1, 6, 8 |
| [ver3/RETIREMENT_MATRIX.yaml](../../ver3/RETIREMENT_MATRIX.yaml) (644) | NORMATIVE AUTHORITY | POLICY / CONTRACT | R-nn rows cited in stage docstrings (`FP-02`, `R-10`, `R-13`, `R-14`); defines the failure modes the design exists to prevent | 1, 8, 9 |
| [ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml](../../ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml) (195) | NORMATIVE AUTHORITY | POLICY / CONTRACT | Data behind the boundary test; declares Oracle and CAD evaluation-only | 1, 7 |
| [ver3/phase0/ARCHITECTURE_INVARIANTS.yaml](../../ver3/phase0/ARCHITECTURE_INVARIANTS.yaml) (628) | NORMATIVE AUTHORITY | POLICY / CONTRACT | INV-001..018; INV-002 and INV-007 are cited in stage and harness code | 1, 5, 8 |
| [ver3/phase0/VER2_RETIREMENT_MATRIX.md](../../ver3/phase0/VER2_RETIREMENT_MATRIX.md) (138) | NORMATIVE AUTHORITY | POLICY / CONTRACT | R-01..32, U-01..05 | 1, 8 |
| [ver3/phase0/ARCHITECTURE_CHANGE_PROPOSALS.yaml](../../ver3/phase0/ARCHITECTURE_CHANGE_PROPOSALS.yaml) (134) | NORMATIVE AUTHORITY | POLICY / CONTRACT | The only authorised way a phase0 authority changes — the test for whether a drift was authorised (§9) | 8 |
| [ver3/phase0/ARCHITECTURE_COMPREHENSION_CHECK.md](../../ver3/phase0/ARCHITECTURE_COMPREHENSION_CHECK.md) (397) | HISTORICAL CLAIM | REVIEW RECORD | Comprehension record | 1 |
| [ver3/phase0/PHASE0_EVIDENCE_REPORT.md](../../ver3/phase0/PHASE0_EVIDENCE_REPORT.md) (1 line / 69 B) | UNKNOWN | NONE | Title-only stub; named as a phase0 file (OBS-2) | 1 |
| [docs/PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md](../PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md) (1055) | UNKNOWN | POLICY / CONTRACT | What each stage must decide and output so the next can proceed — the direct answer to objective 1 and to consumer sufficiency (objective 6) | 1, 6 |
| [docs/PIPELINE_CRITICAL_DESIGN_REVIEW.md](../PIPELINE_CRITICAL_DESIGN_REVIEW.md) (1259) | UNKNOWN | POLICY / CONTRACT | Per-stage "decisions owned" tables; the largest statement of intended stage ownership and the origin of the `BodyHypothesis` / `PhysicalInteractionHypothesis` question (§9) | 1, 6, 8 |
| [docs/PIPELINE_HIGH_RISK_ARCHITECTURE_CHECK.md](../PIPELINE_HIGH_RISK_ARCHITECTURE_CHECK.md) (551) | HISTORICAL CLAIM | REVIEW RECORD | Three falsification probes; source of the "sixteen corrections" | 1, 8 |
| [docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md](../PIPELINE_IMPLEMENTATION_PROPOSAL.md) (1129) | UNKNOWN — self-declares "final architecture proposal, revision 2" | POLICY / CONTRACT | Strongest candidate for the architecture of record | 1, 8 |
| [docs/PIPELINE_IMPLEMENTATION_READINESS.md](../PIPELINE_IMPLEMENTATION_READINESS.md) (225) | HISTORICAL CLAIM | REVIEW RECORD | Records contract alignment and the final interface-sufficiency check | 1, 6, 8 |
| [docs/PIPELINE_STAGE_MATURITY_AUDIT.md](../PIPELINE_STAGE_MATURITY_AUDIT.md) (436) | HISTORICAL CLAIM | REVIEW RECORD | Prior L0–L5 maturity claim; must be reproduced independently, never inherited | 5, 8 |
| [docs/WINDOW_S01_S02_IMPLEMENTATION_REPORT.md](../WINDOW_S01_S02_IMPLEMENTATION_REPORT.md) (221) | HISTORICAL CLAIM | REVIEW RECORD | Claim about what S01+S02 became | 2, 8 |
| [docs/WINDOW_S01_S02_FREEZE_REVIEW.md](../WINDOW_S01_S02_FREEZE_REVIEW.md) (747) | HISTORICAL CLAIM | REVIEW RECORD | Claims READY TO FREEZE; should name which live run backs the freeze — resolves the Window-1 run question (§6) | 2, 3, 8 |
| [docs/WINDOW_S03_S04_IMPLEMENTATION_REPORT.md](../WINDOW_S03_S04_IMPLEMENTATION_REPORT.md) (726) | HISTORICAL CLAIM | REVIEW RECORD | States "S04 is not implemented" (PC-02); gained +71 lines in HEAD | 2, 8 |
| [docs/S02_S04_REASONING_GAP_ANALYSIS.md](../S02_S04_REASONING_GAP_ANALYSIS.md) (293) | HISTORICAL CLAIM | REVIEW RECORD | Prior diagnosis of the S02→S03→S04 gap — the same question as objective 6; gained +36 lines in HEAD | 4, 6, 8 |
| [docs/VERIFICATION_PROVENANCE_AUDIT.md](../VERIFICATION_PROVENANCE_AUDIT.md) (117) | HISTORICAL CLAIM | REVIEW RECORD | Prior claim about whether the dashboard represents the evidence faithfully | 7 |
| [.github/workflows/ver3-boundaries.yml](../../.github/workflows/ver3-boundaries.yml) (47) | GOVERNING POLICY | CI / ENFORCEMENT | The only automated gate; asserts a condition the tree now violates (PC-01) | 7, 8 |
| [README.md](../../README.md) (311) | HISTORICAL CLAIM | NONE | Describes mdkg, not ASSY. Retained so the §11.1 exclusion is visible rather than silent | 1 |

Order within P1: governing policy → phase0 invariants → geometry/information plan
→ critical design review → high-risk check → proposal → readiness → maturity audit
→ window reports → gap analysis → provenance audit → CI → README.

---

## Package 2 — Contracts, representation, ownership

**17 files · 4,593 lines · all FULL · all axis B = `POLICY / CONTRACT`**

Machine-consumed: `assy_v3/state/design_state.py` loads this directory at import,
and five meta-tests parse it.

| path | axis A | why it belongs | Q |
|---|---|---|---|
| [DESIGN_STATE_CONTRACT.yaml](../../ver3/contracts/DESIGN_STATE_CONTRACT.yaml) (611) | NORMATIVE AUTHORITY | The representation. Whether a stage *can express* an engineering fact is decided here — the first place to look when reasoning is missing from an output | 1, 4, 5, 6 |
| [STAGE_OWNERSHIP_MATRIX.yaml](../../ver3/contracts/STAGE_OWNERSHIP_MATRIX.yaml) (345) | NORMATIVE AUTHORITY | Which stage owns which family; the producer/consumer boundary in machine form | 1, 6, 8 |
| [ENTITY_FAMILY_AUDIT.yaml](../../ver3/contracts/ENTITY_FAMILY_AUDIT.yaml) (871) | NORMATIVE AUTHORITY | Per-family "who consumes this?" — the consumer-sufficiency question already asked once, in writing | 6 |
| [STAGE_PATCH_CONTRACT.yaml](../../ver3/contracts/STAGE_PATCH_CONTRACT.yaml) (175) | NORMATIVE AUTHORITY | The only legal write into DesignState; bounds what deterministic code may do (objective 4) | 4, 5 |
| [STATUS_SEMANTICS.yaml](../../ver3/contracts/STATUS_SEMANTICS.yaml) (340) | NORMATIVE AUTHORITY | The twelve statuses. A SUCCESS on an incoherent mechanism is judged against this | 7 |
| [PROVENANCE_CONTRACT.yaml](../../ver3/contracts/PROVENANCE_CONTRACT.yaml) (171) | NORMATIVE AUTHORITY | What must be recorded about where a fact came from — the contract behind the DEEPSEEK_AUTHORED / DERIVED / INVENTED classification (§7) | 3, 4 |
| [MODEL_RUN_RECORD_CONTRACT.yaml](../../ver3/contracts/MODEL_RUN_RECORD_CONTRACT.yaml) (220) | NORMATIVE AUTHORITY | PR-01..11; shapes every `model_run_records.json` read in P4A | 3 |
| [BENCHMARK_RESULT_CONTRACT.yaml](../../ver3/contracts/BENCHMARK_RESULT_CONTRACT.yaml) (184) | NORMATIVE AUTHORITY | When a benchmark result is valid at all | 7 |
| [GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml](../../ver3/contracts/GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml) (475) | NORMATIVE AUTHORITY | What the pipeline must generate to be trusted; forbids "Oracle" as a production identifier | 7 |
| [STAGE_PROGRESSION_CONTRACT.yaml](../../ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml) (250) | NORMATIVE AUTHORITY | The gate a stage passes before implementation or freeze — the authorisation test for §9 drift | 8 |
| [stages/S01_CONTRACT.yaml](../../ver3/contracts/stages/S01_CONTRACT.yaml) (91) | NORMATIVE AUTHORITY | Intended S01 responsibility | 1, 5, 6 |
| [stages/S02_CONTRACT.yaml](../../ver3/contracts/stages/S02_CONTRACT.yaml) (104) | NORMATIVE AUTHORITY | Intended S02 responsibility | 1, 5, 6 |
| [stages/S03_CONTRACT.yaml](../../ver3/contracts/stages/S03_CONTRACT.yaml) (197) | NORMATIVE AUTHORITY | Intended S03 responsibility. **Never modified since creation** — see §9 finding G-3 | 1, 5, 6, 8 |
| [stages/S04_CONTRACT.yaml](../../ver3/contracts/stages/S04_CONTRACT.yaml) (169) | NORMATIVE AUTHORITY | Intended S04 responsibility | 1, 5, 6 |
| [stages/S05_CONTRACT.yaml](../../ver3/contracts/stages/S05_CONTRACT.yaml) (138) | NORMATIVE AUTHORITY | Read **only** to judge the S04 handoff and to classify deferral as legitimate | 6 |
| [stages/S06_CONTRACT.yaml](../../ver3/contracts/stages/S06_CONTRACT.yaml) (141) | NORMATIVE AUTHORITY | same | 6 |
| [stages/S07_CONTRACT.yaml](../../ver3/contracts/stages/S07_CONTRACT.yaml) (111) | NORMATIVE AUTHORITY | same | 6 |

---

## Package 3 — Minimal engineering reference (quality bar only)

**~60 files · ~9,900 lines + 170 PNGs inspected**

Scope rule: the Oracle answers *"what engineering facts matter?"* — never *"what
exact mechanism must the pipeline produce?"* A mechanically valid alternative
remains valid. Nothing here is re-audited; nothing here is a target answer.

### 3A. Orientation — read first, 2 files

| path | axis A | axis B | tier | why |
|---|---|---|---|---|
| [ver3/oracles/ORACLE_INDEX.md](../../ver3/oracles/ORACLE_INDEX.md) (153) | NORMATIVE AUTHORITY | REFERENCE ARTIFACT | FULL | Declares the 3-layer model (source / semantics / conclusions) and state `PRE_CAD_BASELINE_READY`. Without it no oracle file is interpretable |
| [ver3/oracles/ORACLE_METHOD.md](../../ver3/oracles/ORACLE_METHOD.md) (623) | NORMATIVE AUTHORITY | REFERENCE ARTIFACT | SKIM | Only for what an Oracle statement *may assert*, so a pipeline output is not judged against something the Oracle never claimed |

### 3B. Benchmark case definitions — the pipeline's actual input

FULL. Axis A `NORMATIVE AUTHORITY`, axis B `POLICY / CONTRACT`. These are what
S01 reads; they are pipeline input, not reference.

`benchmarks/BM-001/{descriptor.yaml (49), source/request.txt (1), source/source_manifest.yaml (241), source/README.md (25)}` ·
`BM-002/{49, 1, 266, 25}` ·
`BM-003/{descriptor.yaml (136), request.txt (30), source_manifest.yaml (439), README.md (24), BM-003_SELECTION_CRITERIA.md (238), BM003_SOURCE_AUTHORING_RECORD.md (272), BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md (185)}` ·
`benchmarks/README.md (37)` · `benchmarks/SOURCE_FREEZE_REVIEW.md (312)` — **17 files, 2,330 lines**

`probes/PRB-01/request.txt` · `PRB-02/request.txt` · `PRB-03/request.txt` —
**3 files, 12 lines.** A probe has no descriptor, manifest or envelope (OBS-5);
what a probe *means* is reconstructed in P5/P6 from `compare_maturity.py` and
`quality_profile.py`, not from this directory.

### 3C. Result-bearing Oracle material — the engineering bar

Extracted for: required functions · physical behaviours · state behaviour ·
freedoms · critical negative cases · support/guidance/retention expectations ·
mobility expectations · S01–S04 engineering invariants.

| pack | files read | lines | tier | note |
|---|---|---|---|---|
| `oracles/product_cases/BM-001/` — `README.md` (92), `normative.yaml` (538), `freedoms.yaml` (77), `realizations.yaml` (260), `negative_cases.yaml` (303), `stage_expectations.yaml` (180), `reference_realizations/REF-BM-001-hinged-snap-box.md` (52) | 7 | 1,502 | FULL | `stage_expectations.yaml` is the direct per-stage bar |
| `oracles/product_cases/BM-002/` — same six (78/502/64/204/180/206) | 6 | 1,234 | FULL | |
| `oracles/held_out/BM-003/` — `README.md` (71), `normative.yaml` (525), `freedoms.yaml` (163), `realizations.yaml` (388), `negative_cases.yaml` (327), `stage_expectations.yaml` (406), `configurations.yaml` (284), `assembly_and_mobility_expectations.yaml` (251), `ambiguities.yaml` (161) | 9 | 2,576 | FULL | The held-out pack; the only one frozen before any run. `assembly_and_mobility_expectations.yaml` maps directly onto the S03 mobility question |
| `oracles/product_cases/BM-001-2/` — `README.md` (80), `normative.yaml` (125), `freedoms.yaml` (30), `stage_expectations.yaml` (64) | 4 | 299 | SKIM | Variant pack for the second BM-001 reference |
| `oracles/micro_oracles/{bounded-two-state-closure, guided-slider, latch-retention, rotary-to-linear-engagement}/` — `README.md` + `normative.yaml` + `freedoms.yaml` + `stage_expectations.yaml` each | 16 | 2,283 | SKIM | **Principle-level, product-independent bars.** Directly relevant to objective 9: does the pipeline reason about *guidance*, *retention*, *bounded two-state closure*, *rotary→linear*, or only about a box and a lift? |

All axis A `NORMATIVE AUTHORITY`, axis B `REFERENCE ARTIFACT`.

Deliberately **not** read (§11.2): every pack's `evidence_cases.yaml`,
`evidence_scope.yaml`, `source_map.md`; the whole `C4-drawer` pack (no benchmark,
no probe); `held_out/BM-003/{evidence_scope, source_clause_ledger, GOVERNANCE,
ORACLE_HASHES, ORACLE_SEMANTIC_SELF_REVIEW}`.

### 3D. CAD reference — the intended physical result

Read enough rationale and metadata to understand the mechanism. The validation
framework is **not** re-certified.

| path | tier | why |
|---|---|---|
| `EXE-BM001-01/{README-equivalent via BM001 report, assembly.yaml (72), interactions.yaml (197), poses.yaml (129), expected_evaluation.yaml (181), actual_evaluation.json (82)}` | FULL | What the reference claims and what it concluded |
| `EXE-BM001-01/parameters.yaml` (337) | SKIM | Dimensions, for spatial plausibility only |
| `EXE-BM001-02/{DESIGN_AND_OPERATION_RATIONALE.md (179), assembly.yaml (70), interactions.yaml (199), poses.yaml (112), expected_evaluation.yaml (188), actual_evaluation.json (81)}` | FULL | |
| `EXE-BM001-02/parameters.yaml` (277) | SKIM | |
| `EXE-BM002-01/{DESIGN_AND_OPERATION_RATIONALE.md (590), assembly.yaml (158), interactions.yaml (211), poses.yaml (142), expected_evaluation.yaml (250), actual_evaluation.json (191)}` | FULL | |
| `EXE-BM002-01/parameters.yaml` (337) | SKIM | |
| `EXE-BM003-01/{README.md (116), DESIGN_AND_OPERATION_RATIONALE.md (284), assembly.yaml (234), interactions.yaml (236), poses.yaml (159), expected_evaluation.yaml (125), actual_evaluation.json (310), VALIDATION_STATUS.yaml (176), SELF_AUDIT.md (179)}` | FULL | `VALIDATION_STATUS.yaml` self-declares authority over any SUMMARY and records the certification as DEFERRED |
| `EXE-BM003-01/parameters.yaml` (514) | SKIM | |
| `BM-001/BM001_EXECUTABLE_REFERENCE_REPORT.md` (419), `BM-002/BM002_EXECUTABLE_REFERENCE_REPORT.md` (312) | FULL | The written statement of each reference's mechanism |
| `EXE-BM003-01/validation_interrupted_…T160153/WHY_THIS_EXISTS.md` (18) | FULL | Establishes which BM-003 artifact set is authoritative |
| `SUMMARY.json` ×4 | STRUCTURAL | Aggregate verdicts only |

Axis A `NORMATIVE AUTHORITY` for the declaration files (`assembly`,
`interactions`, `poses`, `expected_evaluation`); `GENERATED EVIDENCE` for
`actual_evaluation.json` and `SUMMARY.json`. Axis B `REFERENCE ARTIFACT`
throughout.

### 3E. PNG evidence — inspected directly, not via review documents

**Terminology, fixed here and used identically in every count below.**

| term | meaning | number |
|---|---|---|
| **candidate image universe** | every PNG under the four reference packs (49 + 54 + 42 + 25) | **170** |
| **assigned direct-inspection set — PLANNED ESTIMATE** | the mandatory sets plus representatives of the redundant groups, as estimated in this scope document *before* the images were opened | **≈ 97** |
| **assigned direct-inspection set — FINAL ACTUAL** | the same set after the per-pack enumeration was made exact during P3 | **99** |
| **inspected** | opened and viewed directly | **99 / 99** |

**`P3_COMPLETE.md` is the file-level authority for the final count**
(`P3_COMPLETE.md:19` per-pack table, `:22` the reconciliation, `:1041` the close).
The planned estimate below is preserved as written; it was low by two because
EXE-BM001-01 has ten pose-state isos where this scope estimated nine.

**The 170-image universe is enumerated in the table below; 99 of it are inspected
directly.** Prior PNG review documents are read *after* my own inspection, and any
disagreement is recorded (§3F).

| reference | total | mandatory visual evidence set | redundant group | engineering claim the group supports |
|---|---|---|---|---|
| **EXE-BM001-01** hinged snap-box | 49 | `review_overview_latch_operation_and_sections`, `review_overview_section_lines`, `review_operation_01..05` (5), `review_section_{closure_knuckle_pin, enclosure_knuckle_pin, knuckle_side_context, latch_engaged, latch_released, pin_head_and_snap_barb}` (6) = **13** | 9 pose-states × 4 ortho = 36 (`closed_latch_engaged`, `closed_latch_released`, `closed_reengaged`, `closing_latch_leadin`, `open`, `opening_started`, `pin_assembly_compressed`, `pin_assembly_recovered`, `section_knuckle_closed/open`) — inspect **1 iso per state**, 9 images | mechanism architecture · knuckle-pin joint location · latch engage/release geometry · snap-barb retention · closed/open states · assembly by pin compression |
| **EXE-BM001-02** integrated snap rails | 54 | `review_overview_operation_and_sections`, `review_assembly_01..03` (3), `review_operation_01..05` (5), `review_section_{AA_captive_rail_closed, BB_captive_rail_full_open, CC_assembly_snap, DD_latch_engaged, DD_latch_released}` (5) = **14** | 10 pose-states × 4 ortho = 40 — inspect **1 iso per state**, 10 images | prismatic guidance by captive rail · rail retention at full open · integral-tab assembly · latch engage/release · motion extremum at 84 mm |
| **EXE-BM002-01** crank-link lift | 42 | `review_body_identification`, `review_kinematic_chain_annotated`, `review_internal_mechanism_cutaway_iso`, `review_internal_mechanism_rear_panel_removed`, `review_external_crank_user_interface`, `review_overview_operation_and_sections`, `review_assembly_01..09` (9), `review_operation_01..09` (9), `review_section_{AA_shaft_and_dual_journals, BB_crank_link_platform ×3, CC_platform_guides ×3, DD_crank_joint_retention, EE_platform_joint_retention, FF_payload_access ×2}` (11) = **35** | `review_overall_{front,front_iso,left,rear,rear_iso,right,top}` = 7 — inspect **1**, plus 1 confirming view | four-body kinematic chain · distinct crank and platform pivots · dual journals supporting the revolute axis · prismatic platform guides · joint retention at both pins · assembly order · full rise/lower cycle · payload access at both extrema |
| **EXE-BM003-01** three-leg deployable stand | 25 | `exploded`, `assembly_steps`, `compare_stored_deployed`, `hub_locked`, `blocker_engaged`, `blocker_released`, `state_stored`, `state_deployed_locked`, `state_deployed_released`, `deployed_locked_section_iso`, `stored_section_iso` = **11** | `stored_[4]`, `deployed_locked_[4]`, `deployed_released_[4]`, `deployed_locked_section_[4]`, `stored_section_[4]` = 20 — the 2 section isos are already mandatory; inspect **3 remaining isos** | hub + 3 legs + 3 pins + ring architecture · repeated-member placement at 120° · bayonet/ring blocking geometry · stored vs deployed states · lock and release · support region and footprint |

**Inspection budget — PLANNED ESTIMATE: ~73 mandatory + ~24 representative from
redundant groups ≈ 97 images.** The remaining ~73 are strict orthographic
duplicates of an inspected iso and are recorded as covered by their group.

**FINAL ACTUAL COVERAGE: 99 assigned, 99 inspected — 73/73 mandatory and 25/25
representative, plus one image the estimate above missed.** The planned figure is
retained above as the historical estimate; it is not the coverage authority.
See `P3_COMPLETE.md:19,22,1041`.

**No image was dropped from the assigned set on the ground of presumed
redundancy after inspection began.** A conflicting reference image found during
P3 is the reason: filename-level inference about redundancy is not safe. Every group's engineering claim
is written down before the images are opened, so an image cannot retroactively
become "what I was looking for".

### 3F. Written reviews — read *after* my own PNG inspection

| path | axis A | axis B | tier |
|---|---|---|---|
| `EXE-BM001-01/validation/PNG_REVIEW_AUDIT.md` (74), `human_review_checklist.md` (51) | HISTORICAL CLAIM | REVIEW RECORD | SKIM, after §3E |
| `EXE-BM001-02/validation/PNG_REVIEW_AUDIT.md` (100) | HISTORICAL CLAIM | REVIEW RECORD | SKIM, after §3E |
| `EXE-BM002-01/validation/PNG_REVIEW_AUDIT.md` (322), `VIDEO_REVIEW_AUDIT.md` (395) | HISTORICAL CLAIM | REVIEW RECORD | SKIM, after §3E |
| `BM-001/reviews/{HUMAN_CAD_REVIEW_DECISIONS.yaml (162), HUMAN_REVIEW_STATUS.yaml (176), REFERENCE_SELECTION.yaml (122), VIDEO_REVIEW_AUDIT.md (121)}` | HISTORICAL CLAIM | REVIEW RECORD | SKIM |
| `BM-002/reviews/{HUMAN_REVIEW_STATUS.yaml (330), REFERENCE_SELECTION.yaml (208)}` | HISTORICAL CLAIM | REVIEW RECORD | SKIM |

Disagreement between what an image shows and what a review says is a finding, and
is recorded rather than reconciled in favour of the document.

---

## Package 4A — BLIND stage-by-stage engineering review of actual outputs

**75 files · ~24,000 lines · all FULL · the highest-priority package**

Axis A `GENERATED EVIDENCE` throughout. Axis B `GENERATED OUTPUT`.

No Oracle, no CAD reference, no validator verdict and no implementation file is
consulted while P4A is read. Each output is read as a design description and the
mechanism it describes is reconstructed. Entity counts and PASS/FAIL are not the
review.

### 4A.1 The chain that actually exists

Established from `run_window2.py`: Window 2 **replays S01 and S02 from the
recorded fixtures and probes** — not from the DeepSeek live runs — and runs
S03/S03B/S04A/S04B live. So a complete S01→S04 chain for one case is:

```
fixtures|probes s01.json + s02.json   →   r_final s03 + s03b + s04a + s04b
```

and the `deepseek/*` runs are a **separate** line of evidence about what a live
model authors at S01/S02. Both are read; they answer different questions.

### 4A.2 The six complete chains — upstream half

| case | files | lines |
|---|---|---|
| BM-001 | `assy_v3/fixtures/responses/BM-001/{s01.json (290), s02.json (545)}` | 835 |
| BM-002 | `…/BM-002/{s01 (316), s02 (566)}` | 882 |
| BM-003 | `…/BM-003/{s01 (524), s02 (668)}` | 1,192 |
| PRB-01 | `assy_v3/probes/PRB-01/{s01 (276), s02 (456)}` | 732 |
| PRB-02 | `…/PRB-02/{s01 (242), s02 (413)}` | 655 |
| PRB-03 | `…/PRB-03/{s01 (229), s02 (439)}` | 668 |
| — | `assy_v3/probes/PRB-01/s02.pre_revision.json` (41) — axis A `SUPERSEDED NORMATIVE`; read to see what one revision changed | 41 |

### 4A.3 The six complete chains — downstream half

`ver3/live_runs/window2/r_final/` — **LATEST COMPLETE EVIDENCE RUN / CANONICAL
CANDIDATE.** Not called canonical: recency, completeness and commit association
establish that it is the newest complete evidence, not that any document grants
it governing authority.

24 response files: `responses/{BM-001,BM-002,BM-003,PRB-01,PRB-02,PRB-03}/t1_CND-0001/{s03,s03b,s04a,s04b}.json`
(171/168/86/43 · 179/165/88/49 · 292/219/125/78 · 251/263/132/74 · 219/160/103/79 · 147/121/58/39)
plus `trials.json` (1,831) and `model_run_records.json` (1,250). **26 files,
~5,600 lines.**

### 4A.4 Live S01/S02 authorship

`ver3/live_runs/deepseek/q6_fix/` — **LATEST COMPLETE EVIDENCE RUN / CANONICAL
CANDIDATE for Window 1**, pending confirmation from `WINDOW_S01_S02_FREEZE_REVIEW.md`
in P1. 35 response files (6 cases × up to 3 trials × s01/s02) + `trials.json` +
`model_run_records.json`. **37 files, ~11,000 lines.** FULL — objective 3 asks
what DeepSeek actually authors at S01/S02, and this is the only place it is
visible.

### 4A.5 Per-stage review questions

Applied to every case. These are engineering judgements made before any validator
verdict is seen.

**S01** — engineering intent · actors · states · behaviours · requirements ·
constraints · freedoms · quantities · assumptions · ambiguities · verification
intent. *Does it capture the problem without prematurely choosing the mechanism?*

**S02** — obligations · LoadCases · physical-effect reasoning · candidate
principles · interactions · required transformations · support/retention/guidance
obligations · verification obligations · unresolved alternatives · discriminating
evidence. *Is the reasoning physical enough for S03 to synthesise a topology?*

**S03** — bodies · rigid groups · joints · interfaces · physical interactions ·
load paths · support responsibilities · retention responsibilities · blocking
relations · functional regions · assembly dependencies · mobility expectations.
*Does the topology actually realise the selected physical principle?*

**S04** — placement · envelopes · joint origins · joint axes · configurations ·
transitions · motion paths · accessibility · swept occupancy · clearance ·
engagement localisation. Explicitly: connected bodies actually contain/support
their joint · distinct pivots stay distinct · rigid links non-degenerate ·
repeated members placed consistently · revolute axes physically supportable ·
prismatic axes match intended guidance · spatial realisation closes the S03
topology · state transitions geometrically realisable.

### 4A.6 Provenance classification (mandatory, per important engineering fact)

Traced: raw response → parsing → normalized structure → deterministic derivation
→ StagePatch → DesignState → consumer projection → validator findings → reported
status.

`DEEPSEEK_AUTHORED` · `DETERMINISTICALLY_DERIVED` · `PARSER_NORMALIZED` ·
`SILENTLY_REPAIRED` · `DROPPED` · `RENAMED` · `DEFAULTED` ·
`INVENTED_WITHOUT_ENGINEERING_EVIDENCE`

The classification is *proposed* in P4A from the output alone and *confirmed or
overturned* in P5. The governing question: **did DeepSeek produce good
engineering reasoning that the representation or parser lost, or did DeepSeek
fail to reason and deterministic code hide the gap?**

`r_final/trials.json` carries `field_renames_bound`, `rename_examples` and
`dof_entries_derived` — fields that name renaming and derivation directly. They
are read as primary evidence for this section.

### 4A.7 BM vs PRB

Compared at the level of reasoning quality, never answer similarity. Does the
same stage structure work on unseen focused problems? Are BM outputs stronger
because of fixture or history artifacts? Does one representation support both?
Are failures tied to mechanism or product nouns? Are validators equally
meaningful on both?

### 4A.8 Historical runs — STRUCTURAL, used only to explain a revision

16 run directories, ~250 files. Axis A `SUPERSEDED NORMATIVE` or
`HISTORICAL CLAIM`; axis B `GENERATED OUTPUT`.

**All 18 `trials.json` and all 18 `model_run_records.json` are read completely**
regardless of tier — they are short and carry the status and failure fields.
Response payloads in the 16 non-current runs are queried, not read line by line.

Window 1 chronology: `phase1_s01` (08-07 20:02, s01 only) → `phase1_s02` (20:07,
2 trials) → `regression` (20:17, s02 for 5 of 18 trials) → `regression_final`
(20:24) → `stabilized` (21:21) → **`q6_fix` (21:55)**.
Window 2: `smoke` (22:09) → `collect1` (22:13) → `regress1` (22:16) → `s4smoke`
(22:32) → `w2full` (22:35) → `q3smoke` (22:43) → `w2final` (22:47) +
`w2final_prb03` (22:49) → `w2freeze` (23:03) + `w2freeze_prb01` (23:06) →
`r1r4smoke` (08-08 07:06) → **`r_final` (07:10)**.

`trials.json` schema is **not stable** across runs (7 keys in the earliest, 14+
in the newest) — cross-run comparison is not a plain diff (OBS-10).

### 4A.9 Window reports

`ver3/assy_v3/window_report.json` (137, findings) and
`ver3/tools/window_report.json` (109, entity counts) — byte-different, same
basename, neither declared to govern, one inside the production package (PC-05).
Both FULL. Axis A `UNKNOWN`, axis B `GENERATED OUTPUT`.

---

## Package 5 — Implementation, prompts, deterministic derivation, git drift

**26 files · 4,700 lines · all FULL** · axis B `PIPELINE IMPLEMENTATION` unless
noted. Read **after** P4A.

Method: each defect found blind in P4A is traced backward —
output defect → upstream state → consumer projection → representation → prompt →
parser → deterministic derivation → validator. Asking: was the reasoning never
requested? Could the schema not express it? Was intended information removed? Did
the consumer fail to receive it? Did deterministic code do bookkeeping, or make
an engineering judgement? Did normalization destroy meaning? Did prompt/schema
drift cause false negatives?

| path | lines | axis A | why | Q |
|---|---|---|---|---|
| `assy_v3/state/projection.py` | 21 | NORMATIVE AUTHORITY (enforces INV-002) | 21 lines that physically remove `SourceClause` from every projection at and after s02. Read first: it decides what each consumer can see | 4, 6 |
| `assy_v3/state/design_state.py` | 144 | — | Loads `ver3/contracts/` at import; where contract validation actually bites | 4, 6 |
| `assy_v3/state/patch.py` | 53 | — | The only write path; bounds what deterministic code may do | 4 |
| `assy_v3/state/__init__.py` | 8 | — | | |
| `assy_v3/stages/base.py` | 123 | — | The invariant order and the three distinct failure statuses | 4, 7 |
| `assy_v3/stages/s01_requirement_capture.py` | 225 | — | **Contains the S01 prompt.** Only stage that may read raw source | 1, 3, 4 |
| `assy_v3/stages/s02_obligation_and_candidates.py` | 528 | — | **Contains the S02 prompt** | 1, 3, 4 |
| `assy_v3/stages/s03_topology_and_mobility.py` | 979 | — | **Contains the S03 prompts.** Largest stage; `MobilityExpectation` as a total function; the only file changed after the big commit (§9) | 1, 3, 4, 8 |
| `assy_v3/stages/s04_envelope_and_motion.py` | 687 | — | **Contains the S04a/S04b prompts.** Interference computed deterministically, never asked of the model — the sharpest instance of objective 4 | 1, 3, 4 |
| `assy_v3/stages/__init__.py` | 2 | — | | |
| `assy_v3/knowledge/principle_library.py` | 180 | — | Function-class → principle families. The mechanism by which the pipeline is meant to be product-independent (objective 9) | 9 |
| `assy_v3/knowledge/capability_registry.py` | 88 | — | Evidence routes; consulted by S02 | 2, 9 |
| `assy_v3/knowledge/__init__.py` | 11 | — | | |
| `assy_v3/providers/interfaces.py` | 217 | — | The provider contract | 3 |
| `assy_v3/providers/status.py` | 91 | — | The twelve statuses in code | 7 |
| `assy_v3/providers/agent_authored.py` | 88 | — | Refuses a recording whose prompt hash does not match the prompt now built | 3 |
| `assy_v3/providers/offline.py` | 52 | — | Replay; the provider behind every S01/S02 in Window 2 | 3 |
| `assy_v3/providers/__init__.py` | 41 | — | | |
| `ver3/live_providers/deepseek.py` | 318 | — | The model behind every live response in P4A | 3 |
| `ver3/live_providers/env.py` | 78 | — | Returns names, never values | — |
| `ver3/live_providers/__init__.py` | 20 | — | | |
| `ver3/assy_v3/__init__.py` | 52 | — | | |
| `ver3/__init__.py` | 11 | — | | |
| `ver3/tools/run_window2.py` | 469 | — (axis B `EVALUATION IMPLEMENTATION`) | Produced every Window-2 output; decides that S01/S02 are replayed and that S03 runs once per candidate | 3, 4 |
| `ver3/tools/run_live_window.py` | 370 | — (axis B `EVALUATION IMPLEMENTATION`) | Produced every `deepseek/*` run | 3 |
| `ver3/tools/run_window.py` | 146 | — (axis B `EVALUATION IMPLEMENTATION`) | | 3 |
| `ver3/tools/repair_prompt_pairing.py` | 182 | — (axis B `EVALUATION IMPLEMENTATION`) | A tool that can make a stale recording look fresh; read against `agent_authored.py` | 4 |

---

## Package 5G — Architecture-critical git history

Part of P5, executed with it. `git log --follow`, `git show`, `git diff` over the
files named in the instruction.

**Finding established while building this corpus — it changes what git can
answer:**

| id | fact |
|---|---|
| **G-1** | The **entire** S01–S04 architecture, all seven stage contracts, all four stage implementations, all eleven pipeline design documents, the fixtures, the probes and 16 of the 18 live runs arrived in **one commit, `b8da4dd`** — 494 files, 454,882 insertions. There is no committed intra-window history. Git cannot show when `BodyHypothesis` was removed from S02, when `blocked_by` appeared, or when `MobilityExpectation` became a total function, because every one of those transitions happened inside an uncommitted working tree. |
| **G-2** | Exactly **three** usable architecture diffs exist. (a) `8e295b8 → b8da4dd` over `ver3/contracts/`: `DESIGN_STATE_CONTRACT.yaml` +299, `STAGE_OWNERSHIP_MATRIX.yaml` +22/−18, `STAGE_PATCH_CONTRACT.yaml` +16, `STAGE_PROGRESSION_CONTRACT.yaml` +87, `ENTITY_FAMILY_AUDIT.yaml` created (871), all seven stage contracts created. (b) `b8da4dd → ef437cd` over `s03_topology_and_mobility.py` (370 lines changed) and `run_window2.py` (40). (c) the earlier `8e295b8` foundation commit itself. |
| **G-3** | HEAD `ef437cd` is titled *"make the contract authoritative and derive the DOF grid"*, yet **`S03_CONTRACT.yaml` is not among its changed files**. The commit changed the stage code, the harness, two review documents, two live runs and the dashboard — the contract itself was untouched. Whatever "authoritative" meant, it was achieved by changing the implementation to match a contract that already existed, not by amending the contract. This is the single most informative drift signal available, and it points at the S03 code diff, not at a contract history. |

Consequence for the audit: §12's "INTENDED STATE → CHANGE → COMMIT →
AUTHORIZATION → IMPLEMENTED STATE → OBSERVED CONSEQUENCE" chain can be completed
**only** for the contracts diff (a) and the S03 diff (b). For every other named
transition — `BodyHypothesis`, `PhysicalInteractionHypothesis`, physical-effect
chain representation, `blocked_by`, `LoadCase`/`LoadPath` ownership,
`FunctionalRegion`, topology → spatial realization, S03 → S04 sufficiency — the
evidence is **document-vs-contract-vs-code disagreement inside one commit**, not
a diff. Those are traced by comparing P1 documents against P2 contracts against
P5 code, and the absence of a commit boundary is itself recorded: an
unauthorised change and an authorised one are indistinguishable in git here, so
`ARCHITECTURE_CHANGE_PROPOSALS.yaml` is the only authorisation evidence that
exists.

Reads: `git show 8e295b8 b8da4dd ef437cd`, `git diff 8e295b8 b8da4dd -- ver3/contracts/`,
`git diff b8da4dd ef437cd -- ver3/assy_v3/stages/s03_topology_and_mobility.py ver3/tools/run_window2.py`,
and `git log --follow` on each of the 14 named files (already run; results above).

---

## Package 6 — Evaluator and validator adequacy

**26 files · ~7,200 lines · all FULL** · axis B `EVALUATION IMPLEMENTATION` or
`CI / ENFORCEMENT`. Read **after** P4A has independently identified defects.

For every P4A finding: did the evaluator detect it? Classified
`CORRECTLY DETECTED` · `FALSE NEGATIVE` · `FALSE POSITIVE` ·
`NOT ESTABLISHABLE BY CURRENT EVALUATOR` · `MEASURING THE WRONG THING`.
Special attention where a stage reports SUCCESS over an incoherent mechanical
realization. **Schema-complete is not engineering-complete.**

| path | lines | axis A | why |
|---|---|---|---|
| `tools/quality_profile.py` | 432 | NORMATIVE AUTHORITY for "maturity" | Defines engineering maturity operationally. Covers **S01/S02 only** — nothing measures S03/S04 maturity (OBS-12) |
| `tools/compare_maturity.py` | 199 | — | Benchmarks beside probes as profiles, never answer diffs — the BM-vs-PRB method under audit |
| `tools/build_pipeline_dashboard.py` | 1,958 | NORMATIVE AUTHORITY for every dashboard verdict | The authority for everything the dashboard shows; read completely so the HTML need not be |
| `tests/window/test_s01_s02_window.py` | 147 | — | The **only** behavioural test in the repository. None exists for S03 or S04 (OBS-11) |
| `tests/meta/` — `_paths.py` (188), `test_no_legacy_imports.py` (131), `test_no_stage_implementation.py` (124), `test_contracts_parse.py` (64), `test_contract_references.py` (239), `test_status_semantics.py` (114), `test_entity_family_audit.py` (197), `test_package_path.py` (179), `test_benchmark_skeleton.py` (292), `test_descriptor_manifest_consistency.py` (168), `test_source_envelope.py` (289), `test_source_provenance.py` (223), `source_audit.py` (272), `test_source_audit.py` (193), `freeze_gate.py` (124), `test_freeze_gate.py` (211), `test_manifest_ordering.py` (246), `__init__.py` (5) | 3,259 | — | The complete set of checks the CI gate runs. `test_contract_references.py` checks the contract joins; `source_audit.py` is the only check that looks at engineering *language* rather than structure |
| `tests/__init__.py`, `tests/window/__init__.py` | 1 | — | |
| `.github/workflows/ver3-boundaries.yml` | 47 | GOVERNING POLICY / CI | Also in P1; judged here as an evaluator. Contains a step that fails if `ver3/assy_v3/stages` exists — it does (PC-01) |

**Excluded from P6 and escalatable only:** `oracle_tools/audit_oracles.py`
(1,500), `audit_bm003_oracle.py` (1,040), `mutation_tests.py` (1,133),
`tests/meta/test_bm003_oracle.py` (784), and the entire CAD validation engine
(`cadval.py`, `valcore.py`, `cadvideo.py`, `manifest_util.py`,
`test_primitives.py`, four `validate.py`, four `build.py`, `simulate_lift.py`,
`simulate_lid.py`, `review_views.py` ×4, `make_videos.py` ×3, `export_artifacts.py`,
`make_manifest.py`) — **~22,000 lines**. These evaluate the Oracle and the CAD
references, not the pipeline. Re-certifying them was revision 1's largest
misallocation.

---

## Package 4B — Output ↔ reference ↔ evaluator cross-check

No new files. Runs after P4A, P5 and P6 on material already read.

Per case, per stage: were the important obligations discovered? Were important
physical interactions represented? Is the mechanism a valid alternative? Is
critical support / guidance / retention reasoning present? Is mobility correctly
represented? Are important negative and failure cases represented? Is the spatial
realization physically plausible? What reference-level reasoning is absent — and
is it something S01–S04 should already establish, or legitimately deferred to
S05+ (judged against the S05–S07 contracts in P2)?

Each difference classified: `SUPPORTED` · `VALID ALTERNATIVE` ·
`MISSING ENGINEERING REASONING` · `PHYSICALLY INCONSISTENT` ·
`PREMATURE COMMITMENT` · `UNJUSTIFIED ASSUMPTION` · `LEGITIMATELY DEFERRED` ·
`NOT YET ESTABLISHABLE`.

---

## 4. Corpus totals

| package | files | lines | tiers |
|---|---|---|---|
| P1 intended architecture | 22 | 9,697 | all FULL |
| P2 contracts | 17 | 4,593 | all FULL |
| P3 minimal reference | ~60 + **99 images inspected** (170-image universe; 97 was the planned estimate) | ~9,900 | FULL / SKIM / INSPECT |
| P4A actual outputs (primary) | 75 | ~24,000 | all FULL |
| P4A historical runs | ~250 | — | STRUCTURAL; 36 records FULL |
| P5 implementation | 26 | 4,700 | all FULL |
| P5G git history | 3 diffs, 14 log traces | — | FULL |
| P6 evaluation | 26 | 7,200 | all FULL |
| **corpus** | **~476 files + 99 inspected images** (of a 170-image universe) | **~60,100 lines** | |
| **to be read FULL** | **~226 files** | **~50,200 lines** | |

Revision 1: ~666 files, ~165,000 lines corpus, ~93,000 FULL. The reduction is
entirely Oracle-internals, Oracle-history and CAD-validation-framework material,
plus a shift of ~65,000 lines of superseded model output to STRUCTURAL.

---

## 5. Live-run status vocabulary

Recency does **not** confer governance authority.

| run | status | basis | tier |
|---|---|---|---|
| `window2/r_final` | **LATEST COMPLETE EVIDENCE RUN / CANONICAL CANDIDATE** | newest; only Window-2 run complete across 6 cases × 4 stage calls; landed in HEAD `ef437cd` | FULL |
| `deepseek/q6_fix` | **LATEST COMPLETE EVIDENCE RUN / CANONICAL CANDIDATE** | newest Window-1 run; 18 trials; only run carrying `unused_s01_families` | FULL, pending P1 confirmation from `WINDOW_S01_S02_FREEZE_REVIEW.md` |
| `w2final`, `w2final_prb03`, `w2freeze`, `w2freeze_prb01` | SUPERSEDED NORMATIVE | each left one case incomplete and was patched by the next | STRUCTURAL |
| 12 others | HISTORICAL CLAIM | smoke, partial or single-stage runs | STRUCTURAL |
| `EXE-BM003-01/validation/` | **AUTHORITATIVE BY EXPLICIT DECLARATION** | `WHY_THIS_EXISTS.md` names it authoritative over the two interrupted copies | as §3D |
| `EXE-BM003-01/validation_interrupted_*` ×2 | HISTORICAL CLAIM | same declaration | EXCLUDED (§11.4) |

Where repository governance explicitly declares an artifact authoritative, that
declaration is respected. Where only chronology is available, it is labelled as
chronology.

---

## 6. Canonical / historical map

| family | current evidence | superseded or historical | basis |
|---|---|---|---|
| Window-1 live run | `deepseek/q6_fix` (candidate) | 5 earlier runs | chronology + completeness; confirm in P1 |
| Window-2 live run | `window2/r_final` (candidate) | 11 others | chronology + completeness + HEAD |
| S01/S02 feeding Window 2 | `assy_v3/fixtures/responses/`, `assy_v3/probes/` | — | `run_window2.py` replays these, not the live runs |
| PRB-01 S02 | `s02.json` | `s02.pre_revision.json` | filename |
| BM-003 CAD validation | `validation/` | two `validation_interrupted_*` | `WHY_THIS_EXISTS.md` |
| BM-003 completion claim | `VALIDATION_STATUS.yaml` | any `SUMMARY.json` | self-declared |
| Oracle authority | `SOURCE_FREEZE` → `SEMANTIC_AUTHORITY` → `PRE_CAD_BASELINE` | correction-history files | `ORACLE_INDEX.md` — recorded, not audited |
| Window report | undetermined | — | PC-05 |
| Prior audit inventory | this document | `S01_S04_AUDIT_READ_INVENTORY.md`, `P1_RUNNING_EVIDENCE_LOG.md` | superseded by instruction |

---

## 7. Preserved scope decisions

Carried forward unchanged: prior audit inventory is not trusted · prior COMPLETE
markings are not inherited · latest relevant runs are FULL-read · historical runs
may remain STRUCTURAL · all 18 `trials.json` and all 18 `model_run_records.json`
are read completely · the dashboard HTML is not read literally while its 1,958-line
generator is read completely · `ver3/.env` is never read · the mdkg corpus stays
excluded unless specifically required · interrupted CAD runs stay historical ·
S05–S07 contracts are read only to judge the S04 handoff.

---

## 8. Recorded before reading — Observations and Potential contradictions

Visible from structure, headers and git while building this corpus. **Not
conclusions.** Written now so they cannot later be presented as discoveries or
quietly dropped.

| id | statement | resolve in |
|---|---|---|
| **PC-01** | CI `ver3-boundaries.yml` fails the build if `ver3/assy_v3/stages` exists. It exists, with six modules. | P1 + P6 |
| **PC-02** | `WINDOW_S03_S04_IMPLEMENTATION_REPORT.md` states "S04 is not implemented"; `s04_envelope_and_motion.py` (687) exists and `s04a`/`s04b` outputs exist in eight runs. The report gained +71 lines in HEAD. | P1 + P4A |
| **PC-03** | `REPOSITORY_LAYOUT.md` calls `SOURCE_FREEZE_REVIEW.md` "all decisions PENDING"; all three descriptors record `authority_status: FROZEN`, `human_review: HUMAN_REVIEW_COMPLETE`. | P1 + P3 |
| **PC-04** | `ORACLE_WORKFLOW_STATE.yaml` records `production_pipeline_code_exists: false`; `assy_v3/` holds 4,700 lines of pipeline code. | P3 (noted only) |
| **PC-05** | Two byte-different `window_report.json` files, same basename, one inside the production package, neither declared to govern. | P4A |
| **PC-06** | `REPOSITORY_LAYOUT.md` describes `assy_v3/` as "THE PIPELINE. Empty of stage logic" listing only `providers/`; it now holds `stages/`, `state/`, `knowledge/`, `fixtures/`, `probes/` and a report JSON. | P1 + P5 |
| **PC-07** | HEAD's subject claims it made the S03 contract authoritative, but `S03_CONTRACT.yaml` is not in the commit (G-3). | P5G |
| **OBS-1** | Two untracked stray files `.gitignoreJoey.riley-sabaj@northwestern.edu` containing `!.env.example`. | — |
| **OBS-2** | Six report documents are title-only stubs totalling 390 B — five in `ver3/oracles/`, one in `ver3/phase0/` — each named elsewhere as though it had content. | P1 (phase0 one) |
| **OBS-3** | `oracles/product_cases/C4-drawer/` is a complete 9-file Oracle pack with no benchmark and no probe. | excluded; noted |
| **OBS-4** | All six `benchmarks/*/runs/` and `*/evaluations/` hold only `.gitkeep`. No benchmark run or evaluation has ever been written to the location `benchmarks/README.md` defines. | P4A |
| **OBS-5** | A probe is a 4-line `request.txt` and nothing else; a benchmark carries descriptor, manifest, envelope and README. | P3 + P6 |
| **OBS-6** | `EXE-BM003-01` has no `manifest.yaml`; the other three references do. | P3 |
| **OBS-7** | BM-002 `reviews/` lacks the `HUMAN_CAD_REVIEW_DECISIONS.yaml` that BM-001 has. | P3 |
| **OBS-8** | `cad_validation/BM-001/demonstrations/` holds only a README — no source-only Demonstration CAD exists. | P3 |
| **OBS-9** | No `s03`/`s04` fixture recording exists for any case; offline regression covers S01–S02 only. | P4A + P6 |
| **OBS-10** | `trials.json` schema is not stable across the 18 runs (7 keys → 14+). | P4A |
| **OBS-11** | `test_s01_s02_window.py` is the only behavioural test; none exists for S03 or S04. | P6 |
| **OBS-12** | `quality_profile.py` measures S01/S02 only; nothing measures S03/S04 maturity. | P6 |
| **OBS-13** | `ver3/cad_validation/schemas/` is an empty directory. | — |
| **G-1..G-3** | Single-commit architecture; three usable diffs; HEAD did not touch the contract it claims to have made authoritative. | P5G |

---

## 9. Exclusions

**11.1 — the mdkg project sharing this repository root.** `ontology/` (29),
`shapes/` (4), `rules/` (3), `scripts/` (13), `tests/` (2), `build/` (12),
`data/` (8), `outputs/` (28), `vendor/` (4), `config/` (1),
`docs/{competency_questions, cross_book_analysis, extraction_report,
ontology_design, source_coverage_map, substitution_examples}.md`, both root PDFs
(61 MB) — ~110 files. A different system (an ontology built from two textbooks);
six of these trees are already named forbidden roots for `assy_v3`. Cannot
influence S01–S04 by construction. `README.md` is kept in P1 so the exclusion is
visible.

**11.2 — Oracle internals, governance and correction history.** ~85 files,
~19,000 lines: `SOURCE_FREEZE.yaml`, `SEMANTIC_AUTHORITY.yaml`,
`PRE_CAD_BASELINE.yaml`, `HUMAN_SEMANTIC_DECISIONS.yaml`,
`ORACLE_WORKFLOW_STATE.yaml`, `PRE_CAD_BACKLOG.yaml`, all four correction-state
files, `SOURCE_ENTAILMENT_REVIEW.yaml` (861),
`STATEMENT_PREDICATE_ALIGNMENT_REVIEW.yaml` (1,251),
`PHYSICAL_FIXTURE_REVIEW.yaml` (1,894), `FIXTURE_PLAUSIBILITY_REVIEW.yaml` (553),
`CROSS_PACK_OWNERSHIP_REVIEW.yaml`, `ORACLE_AUTHORING_POLICY.md`, all
`_dossiers/`, `_dossier_amendments/`, `_ambiguities/`, all `_audit/` attestations,
the whole `C4-drawer` pack, every pack's `evidence_cases`/`evidence_scope`/
`source_map`, and the five title-only oracle reports.
**Reason:** the Oracle establishes the engineering bar, and §3C reads exactly the
material that carries it. Its provenance, freeze procedure and correction history
are a separate audit that was already performed and is not this audit's subject.
Escalation: if a P4B comparison turns on whether an Oracle statement is itself
sound, the specific statement's entailment record is read then.

**11.3 — CAD validation framework and numeric reports.** ~22,000 lines of
validator/simulation/build code (§P6 exclusion list) plus ~75 per-predicate
report JSONs, `geometry_signature.json` ×6, three logs, and the MuJoCo `.xml`
models. **Reason:** the audit needs the intended physical reference, not a
re-certification of how it was measured. `SUMMARY.json` ×4 and
`actual_evaluation.json` ×4 carry the verdicts and are read.

**11.4 — superseded generated output.** Both BM-003 `validation_interrupted_*`
directories (50 files) — excluded on the repository's own written instruction
that they exist for diagnosis and are not authoritative.

**11.5 — binary artifacts other than the inspected PNGs.** 26 `.step`,
26 `.brep`, 10 `.mp4`, 2 `.gif`, 2 `.xml`, and the 71 orthographic PNG duplicates
remaining from the 170-image universe after the 99 assigned images
covered by their inspected group (§3E). Videos and solids become escalation
evidence only when a FULL file or an inspected image raises a question only they
can settle.

**11.6 — not evidence.** `ver3/.env` (credentials, never read), `.env.example`,
four `.gitignore` files, two stray `.gitignoreJoey…` files, 25 `.pyc`,
six 0-byte `.gitkeep` (their *absence of siblings* is the evidence — OBS-4),
`ver3/cad_validation/schemas/` (empty).

**11.7 — the prior audit.** `docs/audit/S01_S04_AUDIT_READ_INVENTORY.md` (284)
and `docs/audit/P1_RUNNING_EVIDENCE_LOG.md` (166). `SUPERSEDED NORMATIVE` /
`REVIEW RECORD`. Not opened during any package. Their counts (231 files) are not
reconciled with this corpus and nothing is inherited from them. If a comparison
against the prior claim is wanted, it happens after the relevant package is
complete and is labelled a comparison, never a source.

---

## 10. Rules binding for the rest of the audit

1. Every FULL file is read completely, in the §2 order, before any conclusion is
   stated about its package. No grep before a file's complete read; grep is for
   navigation afterwards.
2. `COMPLETE` is recorded only for a file read start-to-end **in this session**.
3. **P4A is read blind.** No Oracle statement, CAD reference, validator verdict
   or implementation file is opened while an output is being judged
   mechanically. Reference comparison happens in P4B and nowhere else.
4. During P1, findings are recorded only as **Observation**, **Potential
   contradiction** or **Needs verification**. Resolution waits for package
   completion.
5. Adding or removing a corpus file mid-audit is permitted and is recorded here
   with the reason. Escalating an excluded artifact is permitted and is logged.
6. **Nothing in the repository is modified by this audit** — not the pipeline
   implementation, contracts, prompts, validators, dashboard logic, benchmark
   inputs, Oracle or CAD references. The only writes are this document and the
   audit's own outputs under `docs/audit/`.
7. Analytical space in the final report is allocated per §15 of the instruction:
   what S01–S04 were meant to reason about, what DeepSeek reasoned about, what
   deterministic code contributed, what disappeared between stages, what was
   silently invented, which outputs are mechanically mature versus structurally
   complete but immature, which stage boundaries are insufficient, which
   validators miss real engineering failures, which decisions caused them,
   whether the pipeline generally improves a low-cost LLM's engineering
   capability, and what should change structurally before S05+.
   Oracle and CAD material supports these conclusions and must not dominate them.

**Scope frozen. Package 1 reading begins now.**
