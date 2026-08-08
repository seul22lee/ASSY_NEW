# S01–S04 audit — read inventory

> # ⚠ SUPERSEDED HISTORICAL AUDIT RECORD
>
> **DO NOT USE THIS FILE AS CURRENT AUDIT COVERAGE OR CURRENT CONCLUSIONS.**
>
> This is a working record kept *during* the audit and frozen where it stood. Its
> coverage counts, `NOT READ` markers, open questions and provisional findings
> reflect a moment in the reading, **not the final state**. This inventory was built during scope construction and still carries 225 `NOT READ` rows against a file list that the frozen scope later superseded; it is not a record of what went unread.
>
> **Current authorities:**
> - scope, corpus and coverage definitions → `AUDIT_SCOPE.md`
> - per-package findings and final coverage → `P1_COMPLETE.md` … `P6_COMPLETE.md`
> - final conclusions and requirement traceability → `P4B_FINAL_SYNTHESIS.md` (frozen, §21)
>
> Where this file and a `*_COMPLETE.md` report disagree, **the COMPLETE report
> governs**. Several findings recorded here were later withdrawn or narrowed on
> fuller evidence; those reversals are documented in `P5_COMPLETE.md` §14 and
> `P4A_COMPLETE.md` §H.
>
> Retained unedited for chronology. Nothing below has been rewritten to look current.

---

The audit is valid only when every file below is COMPLETE. This file is the
persistent record that makes a faithful read possible across context boundaries:
it is updated as ranges are read, never retroactively assumed.

**Rules this file enforces**
- A package may not be declared complete while any file assigned to it is PARTIAL.
- `grep` may be used for navigation *after* a complete read, never instead of one.
- Memory of having written a file is not a read.
- A prior report is a claim to verify, never evidence.

**Status vocabulary**
`NOT READ` · `PARTIAL (ranges)` · `COMPLETE`


| package | files | lines |
|---|---|---|
| Package 1 — intended design | 35 | 13113 |
| Package 2 — BM/PRB/Oracle | 136 | 25151 |
| Package 3 — actual outputs | 32 | 9299 |
| Package 4 — implementation | 28 | 7710 |
| **total** | **231** | **55273** |

## Progress

| package | complete | partial | not read |
|---|---|---|---|
| P1 | 8 | 0 | 27 |
| P2 | 0 | 0 | 136 |
| P3 | 0 | 0 | 32 |
| P4 | 0 | 0 | 28 |


## Package 1 — intended design — 35 files, 13113 lines

| path | lines | ranges read | status | evidence anchors |
|---|---|---|---|---|
| `docs/BENCHMARK_PROBE_EVALUATION_PHILOSOPHY.md` | 268 | — | NOT READ | |
| `docs/PIPELINE_CRITICAL_DESIGN_REVIEW.md` | 1259 | 1–958, 959–1260 | **COMPLETE** | §B1 S02 owns BodyHypothesis + PhysicalInteractionHypothesis, no [NEW] marker (L816-817); §B2 S02→S03 fails only for LoadCase + route class (L1056); §B1 S03 output 5 = blocking relation, six fields (L876-879); §B1 L899-901 LLM dispositions each entry; §A7.4 Configuration vs State redundant (L734-736); §A5.3 monotone-reduction termination (L611) — overturned by proposal D-6; §A5.2 gate after S04b (L580) — differs from proposal; S-9 PoseLaw emitted (L322-328) — differs from proposal §8; §B7 correct-and-untouchable list (L1153-1158); §B8 nine sufficiency probes + hand-authored S03/S04b refs required BEFORE any stage (L1166-1199); Q-2 DOF disposition undefined for compliant bodies (L1212-1215) |
| `docs/PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md` | 1055 | — | NOT READ | |
| `docs/PIPELINE_HIGH_RISK_ARCHITECTURE_CHECK.md` | 551 | — | NOT READ | |
| `docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md` | 1129 | — | NOT READ | |
| `docs/PIPELINE_IMPLEMENTATION_READINESS.md` | 225 | — | NOT READ | |
| `docs/PIPELINE_STAGE_MATURITY_AUDIT.md` | 436 | — | NOT READ | |
| `docs/S02_S04_REASONING_GAP_ANALYSIS.md` | 293 | — | NOT READ | |
| `docs/VERIFICATION_PROVENANCE_AUDIT.md` | 117 | — | NOT READ | |
| `docs/WINDOW_S01_S02_FREEZE_REVIEW.md` | 747 | — | NOT READ | |
| `docs/WINDOW_S01_S02_IMPLEMENTATION_REPORT.md` | 221 | — | NOT READ | |
| `docs/WINDOW_S03_S04_IMPLEMENTATION_REPORT.md` | 726 | — | NOT READ | |
| `ver3/contracts/stages/S01_CONTRACT.yaml` | 91 | 1–91 | **COMPLETE** | creates incl. SystemBoundary L32; quantity_inventory L53-58; S01-C1..C5 L69-80 |
| `ver3/contracts/stages/S02_CONTRACT.yaml` | 104 | 1–104 | **COMPLETE** | **creates: [... BodyHypothesis, PhysicalInteractionHypothesis] L30**; next_stage needs body_hypotheses_with_roles + interaction_hypotheses L95; structured_outputs OMITS both L62-66 (internal contradiction); LoadCase required_fields L38 lacks reacted_at_role; S02-C1..C7 L77-91 |
| `ver3/contracts/stages/S03_CONTRACT.yaml` | 197 | — | NOT READ | |
| `ver3/contracts/stages/S04_CONTRACT.yaml` | 169 | — | NOT READ | |
| `ver3/contracts/stages/S05_CONTRACT.yaml` | 138 | — | NOT READ | |
| `ver3/contracts/stages/S06_CONTRACT.yaml` | 141 | — | NOT READ | |
| `ver3/contracts/stages/S07_CONTRACT.yaml` | 111 | — | NOT READ | |
| `ver3/contracts/BENCHMARK_RESULT_CONTRACT.yaml` | 184 | — | NOT READ | |
| `ver3/contracts/DESIGN_STATE_CONTRACT.yaml` | 611 | 1–611 | **COMPLETE** | typed_relations.blocked_by L372-382 = RELATE with 7 required fields incl. retained_group, promised_features, driver; retained_by L384-388; co_actuated_by L390-395; MobilityExpectation TOTALITY L508-524; maturity_rule L326-342 (per VALUE not stage); derived_not_stored L344-364 (pose law, support, reaction); Joint.compliant_variant L136-149; LoadCase requires reacted_at_role L262; NO BodyHypothesis or PhysicalInteractionHypothesis family defined anywhere; Envelope/SweptVolume/SelectionDecision added Window 2 L586-611 |
| `ver3/contracts/ENTITY_FAMILY_AUDIT.yaml` | 871 | — | NOT READ | |
| `ver3/contracts/GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml` | 475 | — | NOT READ | |
| `ver3/contracts/MODEL_RUN_RECORD_CONTRACT.yaml` | 220 | — | NOT READ | |
| `ver3/contracts/PROVENANCE_CONTRACT.yaml` | 171 | — | NOT READ | |
| `ver3/contracts/STAGE_OWNERSHIP_MATRIX.yaml` | 345 | 1–345 | **COMPLETE** | s02 owns [Obligation, Candidate, AcceptanceContract, LoadCase] L55 — NO BodyHypothesis; s03 owns 9 families L67; s03 may_not fix axis PLACEMENT L73; s04 owns State/Transition/Witness/Envelope/SweptVolume/SelectionDecision L89; universally_ownable L192-204; extension_rule forbids overwrite L217-225; cumulativeness L332-345 |
| `ver3/contracts/STAGE_PATCH_CONTRACT.yaml` | 175 | — | NOT READ | |
| `ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml` | 250 | 1–250 | **COMPLETE** | 8 progression steps L27-105; step 6 downstream-sufficiency PROBE is 'the real gate' L71-87; freeze_rule FSF-01..07 L149-197 with current_conclusion 'NO stage contract may freeze' L195-197; downstream_sufficiency definition + insufficiency_signals L215-232; implementation_order.before_s01 L242-250 |
| `ver3/contracts/STATUS_SEMANTICS.yaml` | 340 | — | NOT READ | |
| `ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml` | 195 | — | NOT READ | |
| `ver3/phase0/ARCHITECTURE_CHANGE_PROPOSALS.yaml` | 134 | — | NOT READ | |
| `ver3/phase0/ARCHITECTURE_COMPREHENSION_CHECK.md` | 397 | — | NOT READ | |
| `ver3/phase0/ARCHITECTURE_INVARIANTS.yaml` | 628 | 1–628 | **COMPLETE** | INV-001 single ownership + lineage_duplicate_check L40-56; INV-002 source-text exclusivity L73-96; INV-003 label-as-authority ban L101-165; INV-004 no silent default L170-197; INV-007 selection gate + 'no selected-candidate field at all' L277-280; INV-008 obligation closure, two_extremes_distinct L320-333; INV-011 UNSUPPORTED vs INFEASIBLE L398-426; INV-014 no overfit assertions L476-502; INV-015 no benchmark branching L504-524; INV-017 Oracle immutable, ORACLE_CHANGE_PROPOSAL L552-570; INV-018 determinism L572-591 |
| `ver3/phase0/PHASE0_EVIDENCE_REPORT.md` | 1 | — | NOT READ | |
| `ver3/phase0/VER2_RETIREMENT_MATRIX.md` | 138 | — | NOT READ | |

## Package 2 — BM/PRB/Oracle — 136 files, 25151 lines

| path | lines | ranges read | status | evidence anchors |
|---|---|---|---|---|
| `ver3/oracles/CROSS_PACK_OWNERSHIP_REVIEW.yaml` | 118 | — | NOT READ | |
| `ver3/oracles/FINAL_PRE_CAD_CORRECTION_REPORT.md` | 1 | — | NOT READ | |
| `ver3/oracles/FINAL_PRE_CAD_CORRECTION_STATE.yaml` | 145 | — | NOT READ | |
| `ver3/oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml` | 553 | — | NOT READ | |
| `ver3/oracles/HUMAN_SEMANTIC_DECISIONS.yaml` | 231 | — | NOT READ | |
| `ver3/oracles/INDEPENDENT_SEMANTIC_REVIEW_REPORT.md` | 1 | — | NOT READ | |
| `ver3/oracles/ORACLE_AUTHORING_POLICY.md` | 337 | — | NOT READ | |
| `ver3/oracles/ORACLE_INDEX.md` | 153 | — | NOT READ | |
| `ver3/oracles/ORACLE_METHOD.md` | 623 | — | NOT READ | |
| `ver3/oracles/ORACLE_VALIDATION_REPORT.md` | 1 | — | NOT READ | |
| `ver3/oracles/ORACLE_WORKFLOW_STATE.yaml` | 134 | — | NOT READ | |
| `ver3/oracles/PHYSICAL_FIXTURE_REVIEW.yaml` | 1894 | — | NOT READ | |
| `ver3/oracles/POST_HUMAN_REVIEW_CORRECTION_REPORT.md` | 1 | — | NOT READ | |
| `ver3/oracles/PRE_CAD_BACKLOG.yaml` | 85 | — | NOT READ | |
| `ver3/oracles/PRE_CAD_BASELINE.yaml` | 284 | — | NOT READ | |
| `ver3/oracles/PRE_CAD_CORRECTION_STATE.yaml` | 269 | — | NOT READ | |
| `ver3/oracles/PRE_CAD_V2_CORRECTION_REPORT.md` | 1 | — | NOT READ | |
| `ver3/oracles/SEMANTIC_AUTHORITY.yaml` | 261 | — | NOT READ | |
| `ver3/oracles/SEMANTIC_CORRECTION_STATE.yaml` | 1030 | — | NOT READ | |
| `ver3/oracles/SOURCE_ENTAILMENT_REVIEW.yaml` | 861 | — | NOT READ | |
| `ver3/oracles/SOURCE_FREEZE.yaml` | 214 | — | NOT READ | |
| `ver3/oracles/STATEMENT_PREDICATE_ALIGNMENT_REVIEW.yaml` | 1251 | — | NOT READ | |
| `ver3/oracles/_dossier_amendments/AMENDMENTS.yaml` | 182 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/GOVERNANCE.yaml` | 235 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/ORACLE_HASHES.yaml` | 48 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/ORACLE_SEMANTIC_SELF_REVIEW.md` | 719 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/README.md` | 71 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/ambiguities.yaml` | 161 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/assembly_and_mobility_expectations.yaml` | 251 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/configurations.yaml` | 284 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/evidence_scope.yaml` | 276 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/freedoms.yaml` | 163 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/negative_cases.yaml` | 327 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/normative.yaml` | 525 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/realizations.yaml` | 388 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/source_clause_ledger.yaml` | 287 | — | NOT READ | |
| `ver3/oracles/held_out/BM-003/stage_expectations.yaml` | 406 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/README.md` | 79 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/evidence_cases.yaml` | 35 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/evidence_scope.yaml` | 65 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/freedoms.yaml` | 64 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/negative_cases.yaml` | 180 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/normative.yaml` | 502 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/realizations.yaml` | 204 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/source_map.md` | 92 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-002/stage_expectations.yaml` | 206 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/README.md` | 87 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/evidence_cases.yaml` | 34 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/evidence_scope.yaml` | 82 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/freedoms.yaml` | 74 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/negative_cases.yaml` | 196 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/normative.yaml` | 554 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/realizations.yaml` | 176 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/source_map.md` | 146 | — | NOT READ | |
| `ver3/oracles/product_cases/C4-drawer/stage_expectations.yaml` | 238 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/README.md` | 80 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/evidence_cases.yaml` | 18 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/evidence_scope.yaml` | 10 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/freedoms.yaml` | 30 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/negative_cases.yaml` | 61 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/normative.yaml` | 125 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/realizations.yaml` | 81 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/source_map.md` | 49 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001-2/stage_expectations.yaml` | 64 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/README.md` | 93 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/evidence_cases.yaml` | 59 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/evidence_scope.yaml` | 58 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/freedoms.yaml` | 77 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/negative_cases.yaml` | 303 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/normative.yaml` | 538 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/realizations.yaml` | 260 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/source_map.md` | 125 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/stage_expectations.yaml` | 180 | — | NOT READ | |
| `ver3/oracles/product_cases/BM-001/reference_realizations/REF-BM-001-hinged-snap-box.md` | 52 | — | NOT READ | |
| `ver3/oracles/_ambiguities/AMB-001-2-01.md` | 45 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-BM-001-2.md` | 60 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-BM-001.md` | 74 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-BM-002.md` | 78 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-C4-drawer.md` | 93 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-bounded-two-state-closure.md` | 60 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-guided-slider.md` | 43 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-latch-retention.md` | 41 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOS-rotary-to-linear-engagement.md` | 47 | — | NOT READ | |
| `ver3/oracles/_dossiers/DOSSIER_README.md` | 12 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/README.md` | 112 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/evidence_cases.yaml` | 34 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/evidence_scope.yaml` | 63 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/freedoms.yaml` | 43 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/negative_cases.yaml` | 154 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/normative.yaml` | 253 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/realizations.yaml` | 127 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/source_map.md` | 87 | — | NOT READ | |
| `ver3/oracles/micro_oracles/rotary-to-linear-engagement/stage_expectations.yaml` | 175 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/README.md` | 91 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/evidence_cases.yaml` | 35 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/evidence_scope.yaml` | 64 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/freedoms.yaml` | 40 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/negative_cases.yaml` | 125 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/normative.yaml` | 270 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/realizations.yaml` | 104 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/source_map.md` | 78 | — | NOT READ | |
| `ver3/oracles/micro_oracles/latch-retention/stage_expectations.yaml` | 142 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/README.md` | 89 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/evidence_cases.yaml` | 50 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/evidence_scope.yaml` | 89 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/freedoms.yaml` | 47 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/negative_cases.yaml` | 163 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/normative.yaml` | 344 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/realizations.yaml` | 122 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/source_map.md` | 100 | — | NOT READ | |
| `ver3/oracles/micro_oracles/bounded-two-state-closure/stage_expectations.yaml` | 194 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/README.md` | 82 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/evidence_cases.yaml` | 44 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/evidence_scope.yaml` | 50 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/freedoms.yaml` | 47 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/negative_cases.yaml` | 102 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/normative.yaml` | 308 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/realizations.yaml` | 120 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/source_map.md` | 94 | — | NOT READ | |
| `ver3/oracles/micro_oracles/guided-slider/stage_expectations.yaml` | 134 | — | NOT READ | |
| `ver3/benchmarks/BM-001/descriptor.yaml` | 49 | — | NOT READ | |
| `ver3/benchmarks/BM-001/source/request.txt` | 1 | — | NOT READ | |
| `ver3/benchmarks/BM-002/descriptor.yaml` | 49 | — | NOT READ | |
| `ver3/benchmarks/BM-002/source/request.txt` | 1 | — | NOT READ | |
| `ver3/benchmarks/BM-003/descriptor.yaml` | 136 | — | NOT READ | |
| `ver3/benchmarks/BM-003/source/request.txt` | 30 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-01/request.txt` | 4 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-01/s01.json` | 276 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-01/s02.json` | 456 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-01/s02.pre_revision.json` | 41 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-02/request.txt` | 4 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-02/s01.json` | 242 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-02/s02.json` | 413 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-03/request.txt` | 4 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-03/s01.json` | 229 | — | NOT READ | |
| `ver3/assy_v3/probes/PRB-03/s02.json` | 439 | — | NOT READ | |

## Package 3 — actual outputs — 32 files, 9299 lines

| path | lines | ranges read | status | evidence anchors |
|---|---|---|---|---|
| `ver3/assy_v3/fixtures/responses/BM-002/s01.json` | 316 | — | NOT READ | |
| `ver3/assy_v3/fixtures/responses/BM-002/s02.json` | 566 | — | NOT READ | |
| `ver3/assy_v3/fixtures/responses/BM-001/s01.json` | 290 | — | NOT READ | |
| `ver3/assy_v3/fixtures/responses/BM-001/s02.json` | 545 | — | NOT READ | |
| `ver3/assy_v3/fixtures/responses/BM-003/s01.json` | 524 | — | NOT READ | |
| `ver3/assy_v3/fixtures/responses/BM-003/s02.json` | 668 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-01/t1_CND-0001/s03.json` | 251 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-01/t1_CND-0001/s03b.json` | 263 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-01/t1_CND-0001/s04a.json` | 132 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-01/t1_CND-0001/s04b.json` | 74 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-02/t1_CND-0001/s03.json` | 219 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-02/t1_CND-0001/s03b.json` | 160 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-02/t1_CND-0001/s04a.json` | 103 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-02/t1_CND-0001/s04b.json` | 79 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-002/t1_CND-0001/s03.json` | 179 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-002/t1_CND-0001/s03b.json` | 165 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-002/t1_CND-0001/s04a.json` | 88 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-002/t1_CND-0001/s04b.json` | 49 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-001/t1_CND-0001/s03.json` | 171 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-001/t1_CND-0001/s03b.json` | 168 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-001/t1_CND-0001/s04a.json` | 86 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-001/t1_CND-0001/s04b.json` | 43 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-003/t1_CND-0001/s03.json` | 292 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-003/t1_CND-0001/s03b.json` | 219 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-003/t1_CND-0001/s04a.json` | 125 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/BM-003/t1_CND-0001/s04b.json` | 78 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-03/t1_CND-0001/s03.json` | 147 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-03/t1_CND-0001/s03b.json` | 121 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-03/t1_CND-0001/s04a.json` | 58 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/responses/PRB-03/t1_CND-0001/s04b.json` | 39 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/trials.json` | 1831 | — | NOT READ | |
| `ver3/live_runs/window2/r_final/model_run_records.json` | 1250 | — | NOT READ | |

## Package 4 — implementation — 28 files, 7710 lines

| path | lines | ranges read | status | evidence anchors |
|---|---|---|---|---|
| `ver3/assy_v3/stages/__init__.py` | 2 | — | NOT READ | |
| `ver3/assy_v3/stages/base.py` | 123 | — | NOT READ | |
| `ver3/assy_v3/stages/s01_requirement_capture.py` | 225 | — | NOT READ | |
| `ver3/assy_v3/stages/s02_obligation_and_candidates.py` | 528 | — | NOT READ | |
| `ver3/assy_v3/stages/s03_topology_and_mobility.py` | 979 | — | NOT READ | |
| `ver3/assy_v3/stages/s04_envelope_and_motion.py` | 687 | — | NOT READ | |
| `ver3/assy_v3/state/__init__.py` | 8 | — | NOT READ | |
| `ver3/assy_v3/state/design_state.py` | 144 | — | NOT READ | |
| `ver3/assy_v3/state/patch.py` | 53 | — | NOT READ | |
| `ver3/assy_v3/state/projection.py` | 21 | — | NOT READ | |
| `ver3/assy_v3/knowledge/__init__.py` | 11 | — | NOT READ | |
| `ver3/assy_v3/knowledge/capability_registry.py` | 88 | — | NOT READ | |
| `ver3/assy_v3/knowledge/principle_library.py` | 180 | — | NOT READ | |
| `ver3/assy_v3/providers/__init__.py` | 41 | — | NOT READ | |
| `ver3/assy_v3/providers/agent_authored.py` | 88 | — | NOT READ | |
| `ver3/assy_v3/providers/interfaces.py` | 217 | — | NOT READ | |
| `ver3/assy_v3/providers/offline.py` | 52 | — | NOT READ | |
| `ver3/assy_v3/providers/status.py` | 91 | — | NOT READ | |
| `ver3/live_providers/__init__.py` | 20 | — | NOT READ | |
| `ver3/live_providers/deepseek.py` | 318 | — | NOT READ | |
| `ver3/live_providers/env.py` | 78 | — | NOT READ | |
| `ver3/tools/build_pipeline_dashboard.py` | 1958 | — | NOT READ | |
| `ver3/tools/run_window2.py` | 469 | — | NOT READ | |
| `ver3/tools/run_window.py` | 146 | — | NOT READ | |
| `ver3/tools/run_live_window.py` | 370 | — | NOT READ | |
| `ver3/tools/quality_profile.py` | 432 | — | NOT READ | |
| `ver3/tools/compare_maturity.py` | 199 | — | NOT READ | |
| `ver3/tools/repair_prompt_pairing.py` | 182 | — | NOT READ | |
