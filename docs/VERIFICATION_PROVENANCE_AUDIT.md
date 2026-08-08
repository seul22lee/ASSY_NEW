# Verification Provenance Audit

Scope: determine whether the dashboard's verification state faithfully
represents the underlying evidence. **No code, prompt, contract, validator or
dashboard was modified.** The Window 2 regression running in the background at
audit time wrote no artifact into the dashboard under audit.

---

## The two chains, traced

### Benchmark — badge `PASS` at S01/S02

| step | artifact / code |
|---|---|
| provider | `OfflineReplayProvider` — `ver3/tools/run_window.py:42` |
| stage output | `ver3/assy_v3/fixtures/responses/BM-001/s01.json` (a **recorded fixture**) |
| validator execution | `run_window.py` runs the fourteen Window 1 checks |
| validator result | `findings: []` |
| **stored artifact** | **`ver3/tools/window_report.json` → `{"case":"BM-001","s01_status":"SUCCESS","s02_status":"SUCCESS","findings":[]}`** |
| dashboard discovery | `load_window_reports()` globs `window_report*.json` — `build_pipeline_dashboard.py:406` |
| dashboard rendering | `wstat = window["s01_status"]` (`:772`) → status `OK` → `verdict_pill` → **PASS** |

### Probe — badge `NOT VERIFIED` at S01/S02

| step | artifact / code |
|---|---|
| provider | `AgentAuthoredProvider` (recordings) **and** `DeepSeekProvider` (live) |
| stage output | `ver3/assy_v3/probes/PRB-01/s01.json`, and `ver3/live_runs/deepseek/*/responses/PRB-01/t*/s01.json` |
| validator execution | (a) `ver3/tests/window/test_s01_s02_window.py` — **writes no file**; (b) `ver3/tools/run_live_window.py` — **writes a file** |
| validator result | e.g. `live_runs/deepseek/q6_fix/trials.json`: **9 probe rows, all `s01_status: SUCCESS`, `s02_status: SUCCESS`, 15 CHECK_FINDINGs** |
| **stored artifact** | **six `trials.json` files on disk carry probe rows** (`phase1_s01`, `phase1_s02`, `q6_fix`, `regression`, `regression_final`, `stabilized`) |
| dashboard discovery | `discover_live_trials()` **does read `trials.json`** — `:304` |
| dashboard rendering | the badge logic consults **only `window`** (`window_report*.json`); `window_reports.get("PRB-01")` → `{}` → `wstat is None` → **NOT VERIFIED** (`:797`) |

---

## Answers

**1. Why are benchmark cards `PASS`? Which artifact authorises it?**
`ver3/tools/window_report.json`, fields `s01_status`/`s02_status` = `"SUCCESS"`
with `findings: []`. Written by `run_window.py`, which uses
`OfflineReplayProvider` — so the badge is authorised by a **fixture replay**, the
weakest evidence category in this repository's own taxonomy.

**2. Why are probe cards `NOT VERIFIED`? Which artifact authorises it?**
**No artifact authorises it. An absence does.** `run_window.py:126` enumerates
`os.listdir(FIXTURES)`, and `ver3/assy_v3/fixtures/responses/` contains only
`BM-001`, `BM-002`, `BM-003`. Probes live in `ver3/assy_v3/probes/`, so they can
never appear in `window_report.json`. The badge is a statement about which
directory a case lives in, rendered as a statement about verification.

**3. Are probes actually being validated?**
**Yes.** `q6_fix/trials.json` records 9 probe rows at `SUCCESS`/`SUCCESS` with 15
check findings; `stabilized/trials.json` records 13. Probes are validated by the
same fourteen checks, additionally against a **live independent provider**, which
the benchmarks in `window_report.json` are not.

They are displayed differently because the badge reads one file family and the
probe validation lives in another.

**Previous reports did not overstate.** They cited `live_runs/*/trials.json`,
which exists and contains what they described. Window 1's freeze review also
recorded this exact gap as a finding: *"has recorded stage output but appears in
no harness report… nothing on disk records it."*

**4. What causes the discrepancy?**
**Dashboard logic**, specifically the badge's choice of evidence source.
Artifact generation is fine (the artifacts exist). Validator policy is fine (the
validators ran on probes). Reporting wording is fine (the reports cited real
files). There is no genuine absence of evidence.

---

## The finding that settles it

The `NOT VERIFIED` badge does not merely under-claim. It makes a **factual
assertion that is false**, and the same panel disproves it.

`PRB-01 / S01` renders, in this order:

1. the badge text *"Structured output exists, but **no harness report on disk
   records a verdict for this case**"*, and then
2. a table headed *"Validator findings recorded by the harness"* containing
   **4 rows sourced from `deepseek/phase1_s01`**.

The panel states that nothing on disk checked the output, then displays what
checked it. Both were rendered from the same `render_stage_panel` call.

The inversion is the practical harm: **the fixture-replayed benchmark gets
`PASS`; the live-provider-validated probe gets `NOT VERIFIED`.** A reader ranking
the two by badge would rank them opposite to their actual evidential strength —
which is precisely the failure this dashboard was built to prevent.

---

## Conclusion

> ## B. Dashboard is incorrect.

Not merely misleading: it asserts on the page that no verdict exists on disk when
six files record one, and contradicts that assertion within the same panel.

**One layer should change: the dashboard's badge-derivation logic** —
`render_stage_panel`'s status derivation in
`ver3/tools/build_pipeline_dashboard.py` (~:770-800).

That layer owns the problem because every other layer discharged its
responsibility: the validators ran on probes, the harness stored the results, and
the reports cited them accurately. Only the rendering layer selected a single
evidence source (`window_report*.json`) whose producer structurally cannot
contain probes, and then described that absence as a verification state.

The fix belongs there and nowhere else. In particular, `run_window.py` should
**not** be changed to enumerate probes: that would make the badge true by
generating a fixture-replay verdict for cases whose stronger, live verdict
already exists — curing the symptom by manufacturing weaker evidence.
