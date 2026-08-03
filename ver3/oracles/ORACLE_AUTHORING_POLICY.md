# ORACLE_AUTHORING_POLICY

Operational rules for authoring every pack. Derived from the BM-001-family
classification report, which established the defects are systematic.

---

## 1. Product normative content — admissible bases only

`basis_type` must be exactly one of:

| basis_type | Means | Requires |
|---|---|---|
| `DIRECT_USER_REQUIREMENT` | Restates a rank-1 source requirement | `support_type: direct`; a rank-1 source locator; the statement must not exceed the source |
| `NECESSARY_PHYSICAL_CONSEQUENCE` | Physically unavoidable given a rank-1 requirement | `support_type: derived`; `derivation_premises`; must survive counterexample search |
| `VERIFICATION_MINIMUM` | The least condition that makes a claimed verification meaningful | must name the claim it enables in `enables_claim` |

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

## 9. Realization fixtures — mandatory, machine-checked

Every product pack declares:

- `admissible_realizations`: **>= 2 materially different** designs that satisfy
  the source. Every normative invariant must admit **all** of them.
- `inadmissible_realizations`: designs drawn from the negative cases. Each must
  be rejected by **at least one** invariant.

These are the inputs to the necessity and overfitting audits. A pack that
rejects an admissible realization is overfitted; one that admits an inadmissible
realization is too weak. Both are BLOCKING.
