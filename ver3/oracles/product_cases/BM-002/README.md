# Oracle pack — BM-002 (enclosed hand-cranked platform lift)

**Status:** STRUCTURALLY_COMPLETE — not yet audited, not locked.
**Tier:** product case. **Parent:** none.
**Frozen dossier:** `../../_dossiers/DOS-BM-002.md`.

This pack is a semantic acceptance specification, not a golden output. It states
what any correct design and any correct pipeline run must satisfy, what they are
free to choose, and what must remain undecided.

## Files

| File | Role |
|---|---|
| `normative.yaml` | 11 invariants + 6 required unresolved decisions |
| `freedoms.yaml` | 9 decisions no test may assert |
| `realizations.yaml` | 3 admissible + 8 inadmissible fixtures, machine-checked by tag algebra |
| `negative_cases.yaml` | 8 design + 6 process cases that must be rejected |
| `evidence_scope.yaml` | What the legacy evidence can and cannot support; 6 not-verified requirements |
| `stage_expectations.yaml` | Per-stage representation obligations; conditional s11 outcome rules |
| `source_map.md` | Every statement traced to its rank |

## What makes this case distinctive

BM-002 is the only mandatory product case whose source states quantities
(travel, payload). That makes it the case where **unit and qualifier discipline**
is tested: "approximately 80-100 mm" must survive the pipeline as a qualified
range, not become a crisp bound (AMB-002-02, `NEG-BM-002-012`), and no value may
acquire a unit by default (s06 `unit_note`).

It is also the case where the Ver1 failure mode is sharpest. The legacy run
returned INFEASIBLE for a hand-cranked lift without a gear, because the library
held exactly one conversion card. A hand-cranked lift without gearing is
realizable. `FRE-BM-002-002` and `NEG-BM-002-009` exist to make that verdict
impossible: an absent realizer yields UNSUPPORTED with the capability named.

## Two ambiguities are carried, not resolved

REQ-004 requires the mechanism enclosed; REQ-001 requires the input external.
The source does not say whether the crossing element is part of "the mechanism"
(AMB-002-01). And "approximately 80-100 mm" has no stated compliance edge
(AMB-002-02). Neither is decided here. Both are carried as required unresolved
decisions and both make their requirement INDETERMINATE until resolved.

Unlike BM-001-2, neither ambiguity blocks the pack: they bound the evaluation of
two requirements without preventing fair evaluation of the rest.

## Evidence limits

All available lift kinematic evidence is **V-A declared-pair**. Under declared
coupling the transmission relationship is exact by construction, so it observes
nothing about the engagement. REQ-007 (jamming) is a contact-level question and
is therefore NOT_VERIFIED — which is not INFEASIBLE.
