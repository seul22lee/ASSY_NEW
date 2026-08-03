# ORACLE_AUTHORING_POLICY

Operational rules for authoring every pack. Derived from the BM-001-family
classification report, which established the defects are systematic.

---

## 1. Normative content — admissible bases only

The admissible set depends on the tier, because **a micro-oracle has no user**.

### Product cases

| basis_type | Means | Requires |
|---|---|---|
| `DIRECT_USER_REQUIREMENT` | Restates a rank-1 source requirement | `support_type: direct`; a rank-1 source locator; the statement must not exceed the source |
| `NECESSARY_PHYSICAL_CONSEQUENCE` | Physically unavoidable given a rank-1 requirement | `support_type: derived`; `derivation_premises`; must survive counterexample search |
| `VERIFICATION_MINIMUM` | The least condition that makes a claimed verification meaningful | `enables_claim` **and** `requires_evidence_tags` |

### Micro-oracles

| basis_type | Means | Requires |
|---|---|---|
| `PROJECT_DEFINED_CAPABILITY` | Restates a fragment of the project-authored, then frozen, capability statement | `support_type: direct`; a locator resolving to **S1** of the capability's dossier |
| `NECESSARY_PHYSICAL_CONSEQUENCE` | as above | as above |
| `VERIFICATION_MINIMUM` | as above | as above |

**A micro-oracle must never use `DIRECT_USER_REQUIREMENT`** (finding SF-1.3). Its
capability statement was written by this project and then frozen; appearing in
dossier S1 does not make it user language and does not make it rank 1. It may
ground normative statements, but its authority is explicitly human-reviewable and
it must never be presented as a user requirement. A product case must
symmetrically never use `PROJECT_DEFINED_CAPABILITY`: it has a user. Both
directions are BLOCKING.

### Every VERIFICATION_MINIMUM must name what it enables

`enables_claim` states exactly which claim becomes admissible once the minimum is
satisfied. Placeholder text does not satisfy it. A verification minimum without
`enables_claim` or without `requires_evidence_tags` is `POLICY_FIELD_MISSING`,
BLOCKING.

## 2. Product normative content must NOT contain

- pipeline representation requirements ("expressed as", "declared … path", "recorded as a graph") — these belong in `stage_expectations`;
- architecture invariants already owned by `ARCHITECTURE_INVARIANTS.yaml` (units, provenance, duplicate entities, renderer/CAD authority);
- current tooling limitations;
- reference-realization details — mechanism names, part counts, dimensions, coordinates, bounds;
- unsupported interpretations — anything whose only support is rank 5–6;
- fixed expected outcomes caused by a capability gap.

## 3. Stage expectations

May state what the pipeline must **represent, preserve, defer or report**. May
not add a product requirement. If a statement would still be true of a product
built by hand with no pipeline, it is a product requirement and belongs in
`normative.yaml` — otherwise it belongs here.

## 4. Evidence scope

Records what current evidence **can** and **cannot** prove: `fidelity`,
`reused_from`, `in_scope`, `out_of_scope`, `structural_artifacts`. A value that
is exact by construction of the model is a structural artifact and is never
evidence.

## 5. Source ambiguities

Preserved explicitly in `_ambiguities/`. Never silently reconciled. They do not
stop authoring of other packs. They become lock blockers **only** when they
prevent a fair acceptance predicate for that specific pack.

## 6. Reference realizations

Never a normative target. Cited only in `reference_realizations/`, always with
their bundled decisions written out so a reader sees what was chosen *for* the
example rather than *by* the requirements.

## 7. Stage-11 outcomes are conditional

Expressed as `outcome_rules`, never fixed results:

```yaml
REQ-00X:
  pass_requires: "<the scoped evidence that would earn PASS>"
  fail_when: "<contradictory evidence>"
  if_capability_absent: UNSUPPORTED
  otherwise: NOT_VERIFIED
```

Never freeze today's inability into a permanent expected result.

## 8. Parent / delta packs

- inherit the parent unchanged (`inherits:`);
- add or narrow only what a rank-1 delta source supports;
- **never** compare a generated child design to a generated parent design;
- evaluate the delta requirement **directly** on the child design alone.

## 9. Fixtures — mandatory, machine-checked, and DOMAIN-SEPARATED

Physical design and verification process are separate domains and never share a
tag set (finding SF-1.1). A physical realization must not become inadmissible
merely because no test has yet been authored for it.

| File | Domain | Declares |
|---|---|---|
| `realizations.yaml` | physical design | `physical_tag_vocabulary`, `admissible_realizations`, `inadmissible_realizations` |
| `evidence_cases.yaml` | evidence and verification | `evidence_tag_vocabulary`, `admissible_evidence_cases`, `inadmissible_evidence_cases` |
| `negative_cases.yaml` | pipeline and process | design, evidence and process cases that must be rejected |

Rules:

- a non-`VERIFICATION_MINIMUM` invariant uses `requires_tags`, drawn only from
  the physical vocabulary;
- a `VERIFICATION_MINIMUM` uses `requires_evidence_tags`, drawn only from the
  evidence vocabulary;
- crossing the two is `DESIGN_EVIDENCE_TAG_MIXED`, BLOCKING;
- `admissible_realizations`: **>= 2 materially different** designs. Every
  physical invariant must admit **all** of them;
- `inadmissible_realizations`: each must be rejected by at least one physical
  invariant;
- the same two rules apply to evidence cases against the verification minima.

A pack that rejects an admissible realization is overfitted; one that admits an
inadmissible realization is too weak. Both are BLOCKING.

## 10. Unresolved decisions carry explicit block scopes

The coarse `blocks:` relation is retired (finding SF-1.4). Every unresolved
decision declares a `kind` and a set of `block_scopes`:

| kind | quantitative \| qualitative \| interpretive \| structural_choice |
|---|---|
| `blocks_structural_predicate` | the predicate's DOMAIN is undefined, not merely a threshold missing |
| `blocks_quantitative_acceptance` | a numeric acceptance cannot be evaluated |
| `blocks_PASS` | PASS may not be reported |
| `blocks_evidence_interpretation` | evidence cannot be interpreted against the requirement |

**A `quantitative` unknown may never carry `blocks_structural_predicate`.** A
missing effort ceiling does not block geometric actuator reachability; a missing
disturbance magnitude does not block the existence of a load path; a missing
stability criterion does not block derivation of a resting configuration. Any
use of `blocks_structural_predicate` requires a
`structural_block_justification` explaining why the domain, not the threshold,
is undefined.

## 11. Two review records, neither of which is Oracle evidence

- `SOURCE_ENTAILMENT_REVIEW.yaml` — for every normative statement: the
  source-derived proposition, the entailment class, the counterexample tried and
  its outcome. Locator resolution is not semantic entailment, and no statement
  may be called audited because its locator resolves (finding SF-1.5).
- `FIXTURE_PLAUSIBILITY_REVIEW.yaml` — for every admissible fixture: how it
  physically operates, what it assumes, what would break it, and a status
  (finding SF-1.6). Tags are authored by the same hand as the invariants and are
  not independent evidence, so the review may never be represented by copying
  them.

## 12. Open search, not fixed plurality

No pack may require a fixed number of candidates to survive a stage (finding
SF-8.3). One candidate may legitimately remain after source- and physics-based
elimination. What must hold instead:

- the solution space was not closed merely by current library availability;
- each rejected candidate carries a source, physical or feasibility reason;
- synthesis beyond the provider catalogue remained possible;
- an absent implemented realizer yields **UNSUPPORTED**, never INFEASIBLE.
