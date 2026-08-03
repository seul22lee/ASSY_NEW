# Oracle Pack index — Ver3 Phase 1

**Workflow status: READY_FOR_SECOND_HUMAN_REVIEW.** No `LOCK.json`. No production
pipeline code. No CAD fixtures. **Physical validation is pending for every
fixture** — see `FIXTURE_PLAUSIBILITY_REVIEW.yaml`.

Nine packs. Each is a *semantic acceptance specification* — normative invariants,
declared freedoms, decisions that must stay open, machine-checked physical and
evidence fixtures, negative cases, evidence limits, and per-stage representation
obligations. None is a golden output and none contains an expected design.

Corrected against 45 independent semantic review findings; see
[INDEPENDENT_SEMANTIC_REVIEW_REPORT.md](INDEPENDENT_SEMANTIC_REVIEW_REPORT.md).

## Product cases

| Pack | Inv (VM) | Unres | Free | Phys adm/inadm | Evid adm/inadm | Neg | Status |
|---|---|---|---|---|---|---|---|
| [BM-001](product_cases/BM-001/) — latching storage box | 13 (2) | 8 | 13 | 4 / 7 | 2 / 2 | 15 | SEMANTICALLY_AUDITED |
| [BM-001-2](product_cases/BM-001-2/) — delta, flush mount | 2 (0) | 4 | 3 | 4 / 4 | 0 / 0 | 4 | **BLOCKED_BY_SOURCE_AMBIGUITY** |
| [BM-001-3](product_cases/BM-001-3/) — delta, curved back | 3 (0) | 2 | 3 | 3 / 4 | 0 / 0 | 6 | SEMANTICALLY_AUDITED |
| [BM-002](product_cases/BM-002/) — enclosed crank platform lift | 14 (1) | 7 | 11 | 5 / 11 | 2 / 2 | 22 | SEMANTICALLY_AUDITED |
| [C4-drawer](product_cases/C4-drawer/) — knob-driven cabinet drawer | 13 (2) | 6 | 12 | 4 / 10 | 2 / 2 | 22 | SEMANTICALLY_AUDITED |

## Micro-oracles — reusable capabilities, never products, never mechanisms

| Pack | Capability | Inv (VM) | Unres | Free | Phys | Evid | Neg | Status |
|---|---|---|---|---|---|---|---|---|
| [guided-slider](micro_oracles/guided-slider/) | guided translation along a declared line or path, with the freedoms constrained that the instantiating requirement depends on | 7 (1) | 4 | 8 | 5 / 6 | 2 / 1 | 13 | SEMANTICALLY_AUDITED |
| [rotary-to-linear-engagement](micro_oracles/rotary-to-linear-engagement/) | rotary → linear conversion through an uninterrupted chain of localized interactions, with load reaction | 6 (1) | 3 | 8 | 6 / 5 | 2 / 2 | 16 | SEMANTICALLY_AUDITED |
| [latch-retention](micro_oracles/latch-retention/) | holding two bodies in a state against a disturbance, releasing deliberately, repeatably | 8 (2) | 4 | 7 | 4 / 6 | 2 / 2 | 16 | SEMANTICALLY_AUDITED |
| [bounded-two-state-closure](micro_oracles/bounded-two-state-closure/) | a closure reaching two states by a bounded motion, each bound physically produced | 7 (1) | 4 | 7 | 6 / 6 | 2 / 1 | 17 | SEMANTICALLY_AUDITED |

**Totals:** 73 invariants (10 VERIFICATION_MINIMUM), 42 required-unresolved
decisions, 72 declared freedoms, 41 admissible + 59 inadmissible physical
fixtures, 14 admissible + 12 inadmissible evidence cases, 131 negative cases.

## Files in every pack

| File | Contains |
|---|---|
| `normative.yaml` | invariants (`basis_type`, `source_locators`, `derivation_premises`, `conclusion_scope`, `exclusions`, `applies_when`, `verification_predicate`, `requires_tags` or `requires_evidence_tags`, `enables_claim`) + `required_unresolved` with `kind` and `block_scopes` |
| `freedoms.yaml` | decisions no test may assert, each with why it is free |
| `realizations.yaml` | **physical** fixtures and `physical_tag_vocabulary` |
| `evidence_cases.yaml` | **evidence** fixtures and `evidence_tag_vocabulary` |
| `negative_cases.yaml` | design, evidence and process failures that must be rejected |
| `evidence_scope.yaml` | what the legacy evidence can and cannot support, with fidelity |
| `stage_expectations.yaml` | per-stage obligations; conditional `outcome_rules` |
| `source_map.md` | every statement traced to a rank; every legacy value disposed of |
| `README.md` | what the pack is for and which failure it exists to prevent |

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
`SOURCE_ENTAILMENT_REVIEW.yaml` (73 statements, each with the counterexample
tried) and `FIXTURE_PLAUSIBILITY_REVIEW.yaml` (41 fixtures, each with its
physical operation and assumptions). Neither is Oracle evidence and no pack may
cite either.

## Tooling

| Path | Role |
|---|---|
| `../oracle_tools/audit_oracles.py` | read-only auditor, passes 3A–3E; states its own scope |
| `../oracle_tools/mutation_tests.py` | 45 reproducible cases — 38 injected defects, 7 controls |

The auditor never runs as part of any pipeline. Production synthesis stages
S01–S12 **must not read these files**; test runners, evaluators and audit tools
may, and Oracle content must never influence design generation or selection.

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
| [_dossiers/](_dossiers/) | nine frozen source dossiers — the only citable sources |
| [_ambiguities/](_ambiguities/) | recorded source ambiguities, none resolved |
| [_audit/](_audit/) | every audit report, pre- and post-correction |
