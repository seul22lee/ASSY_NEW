# Oracle Pack index — Ver3 Phase 1

**Status: `PRE_CAD_BASELINE_READY`.** No `LOCK.json`. No production pipeline code.
No CAD fixtures. **Physical validation is pending for every fixture.**

| Layer | Path | What it fixes | CAD may change it |
|---|---|---|---|
| **A. immutable source** | [SOURCE_FREEZE.yaml](SOURCE_FREEZE.yaml) | what the source SAYS | no |
| **B. challengeable semantic authority** | [SEMANTIC_AUTHORITY.yaml](SEMANTIC_AUTHORITY.yaml) | what it currently MEANS | **yes** |
| **C. current conclusions** | [PRE_CAD_BASELINE.yaml](PRE_CAD_BASELINE.yaml) | what follows from it | **yes** |

Each carries its own manifest hash; the hashes are not duplicated here, because a
hash cannot live inside a file it covers.

The three layers were separated at PCF-002. Previously `HUMAN_SEMANTIC_DECISIONS.yaml`
sat inside the immutable freeze while declaring every decision challengeable by
CAD — which made the documented revision procedure impossible to execute
(PCF-009).

The freeze covers **sources only** — it is not a semantic lock, and the source is
not challengeable by CAD. The baseline covers the **conclusions**, and every one
of them is challengeable. Next authorized phase: **positive CAD validation** —
two kinds of model, A. source-only Demonstration CAD and B. admissible Executable
Reference CAD. Failure CAD is not part of the current plan. Not production
implementation and not a final Oracle lock.

Eight packs. Each is a *semantic acceptance specification* — normative invariants,
declared freedoms, decisions that must stay open, machine-checked physical and
evidence fixtures, negative cases, evidence limits, and per-stage representation
obligations. None is a golden output and none contains an expected design.

Corrected against 45 independent semantic review findings; see
[INDEPENDENT_SEMANTIC_REVIEW_REPORT.md](INDEPENDENT_SEMANTIC_REVIEW_REPORT.md).

## Product cases

| Pack | Inv (VM) | Unres | Free | Phys adm/inadm | Evid adm/inadm | Neg | Status |
|---|---|---|---|---|---|---|---|
| [BM-001](product_cases/BM-001/) | 13 (2) | 9 | 13 | 7 / 12 | 3 / 2 | 22 | PRE_CAD_SEMANTIC_REVIEWED |
| [BM-001-2](product_cases/BM-001-2/) | 2 (0) | 4 | 3 | 4 / 4 | 0 / 0 | 4 | BLOCKED_BY_SOURCE_AMBIGUITY |
| [BM-002](product_cases/BM-002/) | 14 (1) | 8 | 11 | 5 / 11 | 2 / 2 | 22 | PRE_CAD_SEMANTIC_REVIEWED |
| [C4-drawer](product_cases/C4-drawer/) | 13 (2) | 7 | 12 | 4 / 10 | 2 / 2 | 23 | PRE_CAD_SEMANTIC_REVIEWED |

## Micro-oracles — reusable capabilities, never products, never mechanisms

| Pack | Capability | Inv (VM) | Unres | Free | Phys | Evid | Neg | Status |
|---|---|---|---|---|---|---|---|---|
| [guided-slider](micro_oracles/guided-slider/) | 7 (1) | 4 | 8 | 5 / 6 | 3 / 1 | 13 | PRE_CAD_SEMANTIC_REVIEWED |
| [rotary-to-linear-engagement](micro_oracles/rotary-to-linear-engagement/) | 6 (1) | 3 | 8 | 6 / 5 | 2 / 2 | 16 | PRE_CAD_SEMANTIC_REVIEWED |
| [latch-retention](micro_oracles/latch-retention/) | 8 (2) | 4 | 7 | 4 / 6 | 2 / 2 | 16 | PRE_CAD_SEMANTIC_REVIEWED |
| [bounded-two-state-closure](micro_oracles/bounded-two-state-closure/) | 7 (1) | 4 | 7 | 6 / 6 | 3 / 1 | 17 | PRE_CAD_SEMANTIC_REVIEWED |

**Totals** (computed from this snapshot, never carried forward): 70 invariants (10 VERIFICATION_MINIMUM), 43 required-unresolved decisions, 69 declared freedoms, 41 admissible + 60 inadmissible physical fixtures, 17 admissible + 12 inadmissible evidence cases, 133 negative cases.

## Files in every pack

| File | Contains |
|---|---|
| `normative.yaml` | invariants (`basis_type`, `source_locators`, `derivation_premises`, `conclusion_scope`, `exclusions`, `applies_when`, `verification_predicate`, `requires_tags` or `requires_evidence_tags`, `enables_claim`) + `required_unresolved` with `kind` and `block_scopes` |
| `freedoms.yaml` | decisions no test may assert, each with why it is free |
| `realizations.yaml` | **physical** fixtures and `physical_tag_vocabulary`; every fixture carries a `physical_review` pointer |
| `evidence_cases.yaml` | **evidence** fixtures and `evidence_tag_vocabulary` |
| `negative_cases.yaml` | design, evidence and process failures that must be rejected |
| `evidence_scope.yaml` | what the legacy evidence can and cannot support, with fidelity |
| `stage_expectations.yaml` | per-stage obligations; `evaluability_prerequisites` (representation domain); conditional `outcome_rules` |
| `source_map.md` | every statement traced to a rank; every legacy value disposed of |
| `README.md` | what the pack is for and which failure it exists to prevent |

## Three domains, not two

**Physical** (could it exist and work?) · **Representation** (does the DesignState
say enough to evaluate it?) · **Evidence** (does anything support the claim?).

A buildable design whose record is incomplete is `NOT_EVALUABLE` with reason
`REPRESENTATION_INCOMPLETE` — never physically inadmissible. `interaction_regions_declared`
was carried as a *physical* tag until PCF-004 and now lives in
`stage_expectations.evaluability_prerequisites`.

## The three separations this model rests on

**Physical design vs. verification process.** A realization is never inadmissible
because no test has been authored for it. Enforced as `DESIGN_EVIDENCE_TAG_MIXED`.

**User authority vs. project authority.** Product cases have a user and use
`DIRECT_USER_REQUIREMENT`. Micro-oracles do not: their capability statements were
project-authored and frozen, and carry `PROJECT_DEFINED_CAPABILITY`, whose
authority a reviewer may reject. Enforced in both directions.

**Cannot report PASS vs. cannot derive.** A quantitative unknown may withhold
PASS or make an acceptance INDETERMINATE. It may never make a structural
predicate underivable. Enforced as `UNRESOLVED_BLOCK_SCOPE_INVALID`.

## Two renames, both for the same reason

| Was | Is | Why |
|---|---|---|
| `rack-pinion-conversion` | `rotary-to-linear-engagement` | a mechanism name standing for a capability |
| `hinge-and-stop` | `bounded-two-state-closure` | same defect; `historical_aliases` preserves traceability |

## Anti-self-confirmation

Packs cannot be validated by their author's opinion of them. Each declares
materially different designs that **must all be admitted** and designs that
**must each be rejected**, as tag sets, and the auditor evaluates every invariant
against every fixture mechanically.

But tags are written by the same hand as the invariants, so tag algebra is not
independent evidence. Two further records carry the weight:
`SOURCE_ENTAILMENT_REVIEW.yaml` (70 statements, each with the counterexample
tried) and `FIXTURE_PLAUSIBILITY_REVIEW.yaml` (41 fixtures, each with its
physical operation and assumptions). Neither is Oracle evidence and no pack may
cite either.

## Tooling

| Path | Role |
|---|---|
| `../oracle_tools/audit_oracles.py` | read-only auditor, passes 3A–3J; states its own scope |
| `../oracle_tools/mutation_tests.py` | 112 reproducible cases — 87 injected defects, 25 controls |

The auditor never runs as part of any pipeline. Production synthesis stages
S01–S12 **must not read these files**; test runners, evaluators and audit tools
may, and Oracle content must never influence design generation or selection.

## Decision and attestation records

| Path | Role |
|---|---|
| [SEMANTIC_AUTHORITY.yaml](SEMANTIC_AUTHORITY.yaml) | layer B manifest: decisions, amendments, supersession relations |
| [HUMAN_SEMANTIC_DECISIONS.yaml](HUMAN_SEMANTIC_DECISIONS.yaml) | six approved decisions (HSD-001…006), each challengeable by CAD |
| [PHYSICAL_FIXTURE_REVIEW.yaml](PHYSICAL_FIXTURE_REVIEW.yaml) | every fixture reviewed individually; a tag is a review conclusion, not evidence |
| [STATEMENT_PREDICATE_ALIGNMENT_REVIEW.yaml](STATEMENT_PREDICATE_ALIGNMENT_REVIEW.yaml) | all 70 invariants: statement vs predicate vs tag vs stage |
| [PRE_CAD_CORRECTION_STATE.yaml](PRE_CAD_CORRECTION_STATE.yaml) | PCF-001…011 dispositions |
| [FINAL_PRE_CAD_CORRECTION_STATE.yaml](FINAL_PRE_CAD_CORRECTION_STATE.yaml) | FPC-001…007 dispositions |
| [PRE_CAD_BACKLOG.yaml](PRE_CAD_BACKLOG.yaml) | deferred items; none blocks CAD entry |
| [_dossier_amendments/AMENDMENTS.yaml](_dossier_amendments/AMENDMENTS.yaml) | five additive amendments; frozen dossiers are never overwritten |
| [SOURCE_FREEZE.yaml](SOURCE_FREEZE.yaml) | `freeze_scope: SOURCE_ONLY`, `semantic_lock: false` |
| [PRE_CAD_BASELINE.yaml](PRE_CAD_BASELINE.yaml) | `CHALLENGEABLE_SEMANTIC_BASELINE`, with PU-01…PU-10 and the revision procedure |

## Supporting material

| Path | Role |
|---|---|
| [INDEPENDENT_SEMANTIC_REVIEW_REPORT.md](INDEPENDENT_SEMANTIC_REVIEW_REPORT.md) | 45 findings, finding by finding |
| [SEMANTIC_CORRECTION_STATE.yaml](SEMANTIC_CORRECTION_STATE.yaml) | machine-readable correction state |
| [SOURCE_ENTAILMENT_REVIEW.yaml](SOURCE_ENTAILMENT_REVIEW.yaml) | per-statement entailment review |
| [FIXTURE_PLAUSIBILITY_REVIEW.yaml](FIXTURE_PLAUSIBILITY_REVIEW.yaml) | per-fixture physical review |
| [CROSS_PACK_OWNERSHIP_REVIEW.yaml](CROSS_PACK_OWNERSHIP_REVIEW.yaml) | Pass E ownership boundaries |
| [ORACLE_METHOD.md](ORACLE_METHOD.md) / [ORACLE_AUTHORING_POLICY.md](ORACLE_AUTHORING_POLICY.md) | method and policy |
| [ORACLE_VALIDATION_REPORT.md](ORACLE_VALIDATION_REPORT.md) | audit history |
| [_dossiers/](_dossiers/) | eight frozen source dossiers — the only citable sources |
| [_ambiguities/](_ambiguities/) | recorded source ambiguities, none resolved |
| [_audit/](_audit/) | every audit report, pre- and post-correction. Current: `PRECAD_V2_RESTART-*.json` |
