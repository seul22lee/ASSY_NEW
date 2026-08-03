# Oracle Pack index — Ver3 Phase 1

**Workflow status: READY_FOR_HUMAN_REVIEW.** No `LOCK.json` exists. No production
pipeline code exists.

Nine packs. Each is a *semantic acceptance specification* — normative invariants,
declared freedoms, decisions that must stay open, machine-checked realization
fixtures, negative cases, evidence limits, and per-stage representation
obligations. None is a golden output, and none contains an expected design.

## Product cases

| Pack | Invariants | Unresolved | Freedoms | Admissible / Inadmissible | Negative cases | Status |
|---|---|---|---|---|---|---|
| [BM-001](product_cases/BM-001/) — latching storage box | 11 | 5 | 11 | 3 / 6 | 12 | SEMANTICALLY_AUDITED |
| [BM-001-2](product_cases/BM-001-2/) — delta of BM-001 | 2 | 3 | 3 | 3 / 4 | 4 | **BLOCKED_BY_SOURCE_AMBIGUITY** |
| [BM-001-3](product_cases/BM-001-3/) — delta of BM-001 | 3 | 2 | 3 | 3 / 3 | 4 | SEMANTICALLY_AUDITED |
| [BM-002](product_cases/BM-002/) — enclosed hand-cranked platform lift | 11 | 6 | 9 | 3 / 8 | 14 | SEMANTICALLY_AUDITED |
| [C4-drawer](product_cases/C4-drawer/) — knob-driven cabinet drawer | 11 | 7 | 10 | 3 / 9 | 17 | SEMANTICALLY_AUDITED |

## Micro-oracles — reusable capabilities, never products, never mechanisms

| Pack | Capability | Inv | Unres | Free | Adm / Inadm | Neg | Status |
|---|---|---|---|---|---|---|---|
| [guided-slider](micro_oracles/guided-slider/) | guided translation along a defined line, non-translational freedoms removed | 7 | 3 | 7 | 4 / 7 | 12 | SEMANTICALLY_AUDITED |
| [rotary-to-linear-engagement](micro_oracles/rotary-to-linear-engagement/) | rotary → linear conversion through a localized engagement, with load reaction | 7 | 3 | 8 | 4 / 7 | 13 | SEMANTICALLY_AUDITED |
| [latch-retention](micro_oracles/latch-retention/) | holding two bodies in a state against a disturbance, releasing deliberately, repeatably | 8 | 4 | 7 | 4 / 8 | 14 | SEMANTICALLY_AUDITED |
| [bounded-two-state-closure](micro_oracles/bounded-two-state-closure/) | a closure reaching two states by a bounded motion, each bound physically produced | 7 | 4 | 7 | 4 / 7 | 14 | SEMANTICALLY_AUDITED |

**Totals:** 67 invariants, 37 required-unresolved decisions, 65 declared freedoms,
31 admissible + 59 inadmissible realization fixtures, 104 negative cases.

## Two renames, both for the same reason

| Was | Is | Why |
|---|---|---|
| `rack-pinion-conversion` | `rotary-to-linear-engagement` | A mechanism name standing for a capability |
| `hinge-and-stop` | `bounded-two-state-closure` | Same defect, caught by the auditor as F-3C-001 |

A capability named for one of its realizations biases every reader and every
stage toward that realization. That is the mechanism by which the Ver1 catalogue
came to stand in for the design space.

## Files in every pack

| File | Contains |
|---|---|
| `normative.yaml` | invariants (`basis_type`, `source_locators`, `derivation_premises`, `conclusion_scope`, `exclusions`, `verification_predicate`, `requires_tags`) + `required_unresolved` |
| `freedoms.yaml` | decisions no test may assert, each with why it is free |
| `realizations.yaml` | admissible fixtures (all must be admitted) and inadmissible fixtures (each must be rejected), as tag sets |
| `negative_cases.yaml` | designs and pipeline behaviours that must be rejected, each naming its rejecting invariant |
| `evidence_scope.yaml` | what the legacy evidence can and cannot support, with fidelity; what is NOT_VERIFIED and why |
| `stage_expectations.yaml` | per-stage `must_exist` / `must_not_be_decided` / `may_remain_unresolved` / conditional `outcome_rules` |
| `source_map.md` | every statement traced to a rank; every legacy value ranked and disposed of |
| `README.md` | what the pack is for and which failure it exists to prevent |

## The anti-self-confirmation mechanism

Packs cannot be validated by their author's opinion of them. Each declares
materially different designs that **must all be admitted** and designs that
**must each be rejected**, as tag sets. `oracle_tools/audit_oracles.py` evaluates
every invariant against every fixture by pure tag algebra. An invariant that has
absorbed a realization rejects an admissible fixture; an invariant too weak to
carry its obligation admits an inadmissible one. Both are mechanical findings.

The auditor is read-only and never runs as part of any pipeline.

## Oracle access boundary

Production synthesis stages S01–S12 **must not read these files**. Independent
test runners, Oracle evaluators, lock verifiers and audit tools may. Oracle
content must never influence design generation or candidate selection.

## Supporting material

| Path | Role |
|---|---|
| [ORACLE_METHOD.md](ORACLE_METHOD.md) | How packs are authored and what each check means |
| [ORACLE_AUTHORING_POLICY.md](ORACLE_AUTHORING_POLICY.md) | The global policy the batch was authored under |
| [ORACLE_VALIDATION_REPORT.md](ORACLE_VALIDATION_REPORT.md) | Audit history, arbitration record, mutation test |
| [ORACLE_WORKFLOW_STATE.yaml](ORACLE_WORKFLOW_STATE.yaml) | Workflow state only — never Oracle evidence |
| [_dossiers/](_dossiers/) | Nine frozen source dossiers; the only sources packs may cite |
| [_ambiguities/](_ambiguities/) | Recorded source ambiguities, none resolved |
| [_audit/](_audit/) | Machine-readable audit reports, including the pre-correction ones |
