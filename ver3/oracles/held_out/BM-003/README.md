# BM-003 — HELD_OUT_BENCHMARK_ORACLE

The independently authored acceptance specification for BM-003, *compact folding
three-leg desktop stand*.

**This is not a production input.** It is read by the benchmark evaluator and by
human reviewers, and by nothing else. `ver3/oracles/` is a BLOCKING forbidden
path root for `assy_v3`; a stage that read this would be reading its own answer
key.

- **Source authority:** [`ver3/benchmarks/BM-003/source/request.txt`](../../../benchmarks/BM-003/source/request.txt)
- **Source SHA-256:** `ffb7f5f9feb8e38d6ee56dbce91529f817aebbd2f7180d7dedce65da0c94929d` (revision R3, FROZEN)
- **Authority status:** FROZEN · **Production visibility:** false
- **Auditor:** `ver3/oracle_tools/audit_bm003_oracle.py` — 16 checks, 0 blocking
- **Mutation tests:** `ver3/tests/meta/test_bm003_oracle.py`

## What this Oracle is for

To accept **materially different** designs that solve the stated problem, and to
reject designs that look plausible and cannot work.

The second half is the harder one. The failures this pack targets are not designs
that obviously violate a requirement — those are easy. They are designs where a
*label*, a *field*, a *relationship* or a *simulation artefact* is present while
the physical realization is absent: a joint declared with no interface on either
body, a lock named but positioned where it obstructs nothing, two valid endpoint
poses with no motion between them, a rigid-body reaction force read as a
structural capacity.

## Contents

| File | Answers |
|---|---|
| `source_clause_ledger.yaml` | What does the source actually say, verbatim, and where does Oracle interpretation begin? |
| `normative.yaml` | What must every acceptable design satisfy? |
| `configurations.yaml` | What states exist, what may move in each, and how do they connect? |
| `assembly_and_mobility_expectations.yaml` | What evidence must a design produce? |
| `freedoms.yaml` | What may differ between two valid designs? |
| `ambiguities.yaml` | What must stay open? |
| `evidence_scope.yaml` | What can each evidence class establish, and what can it not? |
| `realizations.yaml` | Which materially different designs must all be admitted? |
| `negative_cases.yaml` | What must be rejected, and by which predicate? |
| `stage_expectations.yaml` | After each stage, what must exist and what must not yet be decided? |
| `GOVERNANCE.yaml` | Who authored this, from what, under what isolation? |
| `ORACLE_HASHES.yaml` | The freeze. |

## The overfitting definition for this pack

This Oracle is overfitted if it rejects a design that satisfies the source. Five
state-maintenance principles are declared admissible — configuration geometry, a
translating captive member, elastic deflection, a seated load-path member, and
rotation — and **every physical invariant must admit all five**. The auditor
checks that mechanically, because "solution-neutral" is otherwise a claim nobody
tests.

## What it deliberately does not do

- It names no mechanism, joint type, body count or dimension.
- It introduces no number. The source contains no digit, and neither does any
  requirement here.
- It does not convert *"knocked it"* into an impact threshold, or *"a small
  object"* into a load. Both would create requirements the benchmark cannot
  evaluate, whose only honest outcome is UNSUPPORTED.
- It does not resolve any of the ten recorded ambiguities.

## Reading order

`source_clause_ledger.yaml` first — everything else is derived from it and cites
it. Then `normative.yaml`, then `freedoms.yaml` alongside it: the two are meant
to be read together, because what the Oracle refuses to constrain is as much a
part of the specification as what it requires.
