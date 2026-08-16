# S9-E — coherent post-repair S01→S02 canary

One paid DeepSeek chain, run after the blocker repair and after `ver3 boundaries`
went green. **The canary FAILED, and it failed in a different place than before.**

Nothing was promoted. Both attempts are retained under
`ver3/live_runs/s9e/postrepair-canary/BM-001/`.

## Gates that had to hold before any paid call

| gate | result |
| --- | --- |
| local Python 3.11 meta (`unittest discover -s ver3/tests/meta -t .`) | 1511 tests, exit 0 |
| GitHub Actions `ver3 boundaries` for `8e00fa0` | run #73, **success**, every step |
| frozen regeneration targets | 12 |
| CURRENT promoted fixtures | 0 |
| BM-001 `source_sha256` vs published manifest | match |
| frozen sources modified | none |

`a3f8c8b` was run #72, **failure** — the same suite, the commit before the repair.

## The chain

```
ver3/benchmarks/BM-001/source/request.txt      source_sha256 a37a822a1f759dec…
  ↓  LIVE S01                                   deepseek, temperature 1.0
  ↓  parser OK · contract OK · patch APPLIED
committed DesignState                           Assumption: ASM-0001, ASM-0002
  ↓  consumer_view_for("s02", state)
ConsumerView.namespace_occupancy                {Assumption: [ASM-0001, ASM-0002]}
  ↓  S02.build_prompt
rendered prompt, 18 957 chars                   "IDS ALREADY IN USE
                                                   Assumption: ASM-0001, ASM-0002"
  ↓  PRE-CALL GATE — PASS, so the paid call was allowed
  ↓  LIVE S02                                   deepseek, temperature 1.0
raw response, 18 030 chars, finish_reason stop
  ↓  parser OK
  ↓  contract REJECTED                          DUPLICATE_ID: ASM-0001
                                                DUPLICATE_ID: ASM-0002
patch NOT applied · nothing repaired · nothing promoted
```

## The pre-call gate, which is the point of this canary

The gate is checked **before** the S02 call is spent, so a boundary defect costs
nothing. It requires committed occupied ids ⊆ ConsumerView occupancy ⊆ rendered
prompt, and no Assumption semantic content in the prompt.

| gate check | result |
| --- | --- |
| view status | `VIEW_READY` |
| committed ids absent from ConsumerView | none |
| committed ids absent from rendered occupancy block | none |
| Assumption `statement`/`why`/`would_be_invalidated_by` leaked into prompt | none |
| semantic families in view | Actor, Ambiguity, Freedom, Requirement, Scenario |
| prompt actually sent == prompt proven by the gate | pairing hash identical |

Least privilege held: S02 was told **which ids are taken** and never **what was
assumed**.

## What the model did with it

The prompt it received contained, verbatim:

```
IDS ALREADY IN USE
…
  Assumption: ASM-0001, ASM-0002
```

It emitted `ASM-0001` and `ASM-0002`.

```
ASM-0001  "The stored contents are relatively light (e.g., paper clips, pens)…"
ASM-0002  "The box will be placed on a flat, stable desk surface."
```

## Attribution, which is what changed

Before the repair the defect was in the consumer boundary: the prompt rendered
zero committed Assumption entities, so S02 could not have known. That was ours and
it is fixed — proved here on the live chain, not only in unit tests.

This failure is **MODEL NON-CONFORMANCE**. The information was present, in the
prompt, in the position the schema example warns about, and the model reused the
ids anyway. The pipeline behaved exactly as designed at every step: the response
parsed, the contract caught both collisions, the write boundary refused the patch,
and nothing was repaired.

Both statements are worth keeping apart:

- the boundary defect is closed — occupancy reached the model;
- the corpus is not regenerable at BM-001 on this attempt — the model did not
  respect it.

## What was NOT done, deliberately

- no retry — one attempt per responsibility, declared before the calls
- no promotion — S01 conformed, and promoting it beside a failed S02 would create
  exactly the half-migrated CURRENT pair the campaign forbids
- no response edited, no duplicate id renamed, no `DUPLICATE_ID` rule weakened
- no temperature change after seeing the outcome — 1.0 throughout, declared first
- no production code changed by this canary, so `8e00fa0` remains the validated
  and CI-green production state

## Provenance

| | S01 | S02 |
| --- | --- | --- |
| model_run_id | `s9e-canary-BM-001\|s01\|sa1\|a1` | `s9e-canary-BM-001\|s02\|sa1\|a1` |
| requested model | `deepseek-chat` | `deepseek-chat` |
| served model | `deepseek-v4-flash` | `deepseek-v4-flash` |
| temperature sent | 1.0 (stage requested 0.0, overridden and recorded) | 1.0 |
| finish reason | `stop` | `stop` |
| response source | LIVE | LIVE |
| raw sha256 | `7d3aac3c7450f454…` | `b44cb53ab5f9a2a1…` |
| prompt pairing | `c73e5fe9f416eda8` | `ed0155e9155eee21` |
| rung | ACCEPTED | CONTRACT_FAILED |

Requested and served model names are recorded separately and are **not** equal;
the substitution is stated in each record rather than assumed equivalent.

## Artifacts

```
ver3/live_runs/s9e/postrepair-canary/BM-001/
  s01.a1.raw.json          the accepted S01 response
  s01.prompt.txt           the prompt it answered
  s02.precall.prompt.txt   the prompt proved by the gate BEFORE paying
  s02.prompt.txt           the prompt actually sent (identical)
  s02.a1.raw.json          the rejected S02 response, unmodified
  canary_report.json       every field above, machine-readable
```

## Open question this leaves

Whether S02 can respect an occupied namespace at all under the current prompt is
now an open question about the MODEL, and it is the next thing S9-E has to settle
before the 12-target migration can proceed. One attempt is one data point; it is
not yet evidence that the case is unregenerable, and it must not be treated as a
licence to retry until an answer is liked. What the next step may not be is a
change to `DUPLICATE_ID` enforcement or a post-hoc repair of a response.
