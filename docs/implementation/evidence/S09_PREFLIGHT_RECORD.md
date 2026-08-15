# S-9 PRE-FLIGHT RECORD — reconstructed from HEAD, not from the plan

```
baseline commit   = 5fb94fb
S-8               = HARD-FROZEN
provider policy   = DEEPSEEK ONLY
scope             = S-9 (fixture regeneration + full chain), not pipeline Stage 09, not a new U-10
```

Written before any production change, per S-9 §0. Every statement below was verified
against current HEAD by reading the code or executing it. Where the implementation plan
and HEAD disagree, HEAD is recorded as the fact.

---

## 1. Every current S01→S04 execution path

There are **three** runners. **None of them executes S01→S04.** No end-to-end path exists
at HEAD, live or replayed.

| # | Runner | Stages | S01 source | S02 source | S03/S04 source |
|---|---|---|---|---|---|
| 1 | [run_window.py](../../../ver3/tools/run_window.py) | S01→S02 | REPLAY | REPLAY | — |
| 2 | [run_live_window.py](../../../ver3/tools/run_live_window.py) | S01→S02 | LIVE (or seeded) | LIVE | — |
| 3 | [run_window2.py](../../../ver3/tools/run_window2.py) | S03→S04 + feasibility/selection/advisory/assurance/S7 | REPLAY | REPLAY | LIVE |

The longest live chain reachable today is **S01→S02** (runner 2) or **S03→S04 on replayed
upstream** (runner 3). The union is not a chain: runner 2 stops before S03, and runner 3
starts from fixtures.

**Consequence for S9-I8 / F-level:** a genuine full-live S01→S04 run is not merely
unexecuted, it is **unreachable at HEAD**. Producing one is new orchestration work, not a
configuration change.

## 2. Where each stage response comes from, per path

| Path | S01 | S02 | S03·A/B | S04·A/B |
|---|---|---|---|---|
| `run_window` | `OfflineReplayProvider(FIXTURES)` | same | — | — |
| `run_live_window` | `DeepSeekProvider` — or `OfflineReplayProvider` under `--seed-s01` | `DeepSeekProvider` | — | — |
| `run_window2` | `OfflineReplayProvider(FIXTURES\|PROBES)` | same | `DeepSeekProvider` | `DeepSeekProvider` |

Deterministic (non-LLM) throughout: feasibility, selection/gating, lifecycle reconcile and
the S-8 assurance pass — all in runner 3 only.

`--seed-s01` is labelled in the trial record (`s01_provider = "offline-replay (SEEDED, not
live)"`), so that substitution is currently visible. Runner 3's replay is labelled only in
the module docstring, **not** in a machine-checkable per-run field.

## 3. Where S01/S02 state is seeded or replayed

* [run_window2.py:212](../../../ver3/tools/run_window2.py#L212) `seed_window1()` — the only
  seeding site. Replays S01 then S02 through `.invoke()` and commits both patches.
* [run_live_window.py:143](../../../ver3/tools/run_live_window.py#L143) — `--seed-s01`
  diagnostic replaces the S01 provider only.
* Fixture root resolution is order-dependent: `recording_root()` tries `FIXTURES` then
  `PROBES` and returns the first with an `s01.json`.

## 4. Do replay and live share one state/view/progression path?

**No. Three divergences at HEAD.**

**(a) Different stage entry points.** `invoke()` is the canonical boundary: it builds the
`ConsumerView`, refuses to call the provider when the view is not `VIEW_READY`, and records
the view ([base.py:230-259](../../../ver3/assy_v3/stages/base.py#L230-L259)). `run()` is the
inner driver and does none of that.

[run_live_window.py:146](../../../ver3/tools/run_live_window.py#L146) calls
`S01RequirementCapture().run(...)` **directly**, bypassing the view construction, the
insufficiency gate and the `consumer_view` record. Every other call site in the repository
uses `.invoke()`. The live S01 path is therefore the one path with no recorded ConsumerView
and no view-readiness gate — a direct S9-I6 violation candidate.

**(b) Different inputs.** `seed_window1` passes `{"request_text", "design_profile"}`;
both S01→S02 runners pass `{"request_text"}` only. **Latent, not active** — no
`design_profile.json`/`.yaml` exists anywhere in the tree, so `design_profile()` returns
`None` today. It becomes an active divergence the moment a profile is added.

**(c) Different replay providers with different integrity guarantees.**

| Provider | Pairing hash enforced? | Used by |
|---|---|---|
| `OfflineReplayProvider` | **No** — returns whatever is on disk | all three runners; BM fixtures in tests |
| `AgentAuthoredProvider` | **Yes** — refuses a stale `answers_prompt_sha256` | probe cases in `tests/window/` only |

So the only provenance a fixture carries is enforced on probes and **not** on the BM
fixtures, and by **no runner at all**.

Duplication beyond providers: each runner re-implements stage ordering, patch application
and its own check list. `run_live_window` and `run_window` each hard-code the 3 S01 and 11
S02 checks inline; `run_window2` hard-codes its own S03/S04 tables.

## 5. Every fixture and stored response artifact relevant to S01–S04

### 5a. Replay corpus (13 files) — what the runners consume

| Artifact | Files | `authored_by` | Live-derived? |
|---|---|---|---|
| `fixtures/responses/BM-00{1,2,3}/s0{1,2}.json` | 6 | *(absent)* | **No** |
| `probes/PRB-0{1,2,3}/s0{1,2}.json` | 6 | `agent-in-repository` | **No** |
| `probes/PRB-01/s02.pre_revision.json` | 1 | `agent-in-repository` | **No** — superseded historical artifact |

**No S03 or S04 fixture exists.** Window 2 has always run those stages live.

**Every replayed response in the corpus is agent-authored.** The PRB files say so; the BM
files carry no authorship field at all, which is weaker rather than better. This is debt
**D-2**, named in `run_live_window.py`'s own docstring: *"The window has only ever been
exercised by responses this repository's own agent authored."*

Against **S9-I2**, the entire current replay corpus fails: nothing in it originates from a
live producing-stage execution. This is the substance of S-9, and it is the expected
starting condition rather than a surprise.

### 5b. Fixture provenance actually present vs. S9-I5 required

Each fixture carries exactly `_meta.answers_prompt_sha256` (a **truncated** sha256 — 16 hex
chars, `prompt_hash()` slices `[:16]`) plus a free-text `pairing_history`. Measured against
S9-I5:

| S9-I5 requires | Present in fixtures |
|---|---|
| source/problem identity | implicit in the directory path only |
| stage | implicit in the filename only |
| provider · model requested · model served | **absent** |
| parameters requested · effectively sent | **absent** |
| raw response hash/text | **absent** (the file *is* the response; no hash of it) |
| parser/contract outcome | **absent** |
| run/attempt identity | **absent** |
| code revision | **absent** |

### 5c. Stored live-run artifacts — 314 files under `ver3/live_runs/`

Not previously inventoried as fixtures, and **in scope for S9-I13**.

```
live_runs/deepseek/{phase1_s01,phase1_s02,q6_fix,regression,regression_final,stabilized}
live_runs/window2/{collect1,q3smoke,r1r4smoke,regress1,r_final,s4smoke,smoke,
                   w2final,w2final_prb03,w2freeze,w2freeze_prb01,w2full}
```

Stage responses held: **s01 ×102, s02 ×70, s03 ×37, s03b ×19, s04a ×25, s04b ×25**, plus
`trials.json` and `model_run_records.json` per run.

These are **genuinely live DeepSeek responses** — the one live-derived material that exists.
Whether any can be promoted to fixtures under S9-I2 depends on whether they still pair with
the current prompts and still pass the current parser and contracts; both prompts and
contracts have moved through S-4…S-8 since these were captured (7–8 Aug).

## 6. DeepSeek parameter authority and provenance behaviour

**Verified by live call during pre-flight** (trivial prompt, no repository content):

```
status       = SUCCESS
model req    = deepseek-chat
model served = deepseek-v4-flash      <-- substitution is REAL and IS recorded
finish       = stop
usage        = in 39 / out 5 / cached 0
```

Model substitution works as PR-04 requires. Credentials load from `ver3/.env`
(`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`) and never reach a record.

**The authority model is inconsistent across parameters.** What the stage asks for is
hard-coded in [base.py:289-292](../../../ver3/assy_v3/stages/base.py#L289-L292):
`max_output_tokens=32000, deadline_s=120.0, temperature=0.0, seed=7`.

| Parameter | Requested by stage | What is sent | Authority | Divergence visible? |
|---|---|---|---|---|
| `max_output_tokens` | 32000 | `min(request, 8192)` | **request**, adapter clamps | **Yes** — `max_output_tokens_clamped_from` |
| `temperature` | 0.0 | `self.temperature` | **adapter** | **Yes** — `temperature_requested_by_stage` vs `_actually_sent` |
| `deadline_s` | 120.0 | `self.timeout_s or request.deadline_s or 120.0` | **adapter first** | **No** — only the effective value is recorded |
| `top_p` | `None` | `self.top_p` | **adapter** | **No** — `request.top_p` never consulted |
| `seed` | 7 | *not sent* | **adapter** | **No** — record hard-codes `"seed": None` |
| `response_format` | `response_schema` | `self.json_object_mode` | **adapter** | **No** — `request.response_schema` never consulted |

So `temperature` — the parameter the S-9 brief calls out — is the **only** one whose
divergence is visible. Four others diverge silently, and `max_output_tokens` follows the
opposite authority rule from the rest. Three parameters on the request dataclass
(`top_p`, `seed`, `response_schema`) are accepted and then ignored without trace.

**On the temperature question specifically** — the brief warns against blindly substituting
`request.temperature`, and the warning is correct. Evidence at HEAD says the divergence is
**intentional**: `base.run()` hard-codes 0.0 for determinism, while `run_live_window.py`
exists precisely to run *"many times, at a non-zero temperature"* and passes `--temperature`
(default 1.0) into the provider constructor. Flipping the payload to `request.temperature`
would silently pin every repeated-trial run to 0.0 and destroy that protocol. The intended
model is therefore **experiment/provider override wins over the stage default, and both are
recorded** — which is what the code does for temperature and fails to do for the rest. S9-B
is to state that rule once and apply it uniformly, not to change which value wins.

### 6a. Provider records do not meet their own contract

`MODEL_RUN_RECORD_CONTRACT.yaml` requires 15 fields. The DeepSeek record emits 14, and the
sets differ:

```
missing: model_run_id · run_id · stage_attempt · model_id · model_version_string
extra  : model_id_requested · model_id_served · model_substitution · error_detail
```

Confirmed against a stored artifact (`live_runs/deepseek/stabilized/model_run_records.json`,
36 records). `model_id_requested`/`model_id_served` is a genuine improvement on the
contract's single `model_id`, but **`run_id`, `model_run_id` and `stage_attempt` are simply
absent**, so a record cannot be tied back to the run or stage attempt that produced it. That
blocks S9-I5's "run/attempt identity" for any fixture promoted from these records.

**No test enforces the record shape against the contract.** `test_contract_references.py`
checks that contracts are *referenced*, not that records *conform*.

## 7. Remaining migration bridges and rejected legacy paths

| Bridge | Status at HEAD |
|---|---|
| `_meta.pairing_history` | Present on **12 of 13** corpus files (absent only on `s02.pre_revision.json`). Identical boilerplate string on all 12. |
| `answers_prompt_sha256` | Enforced by `AgentAuthoredProvider` only → probe tests only. **No runner enforces it.** |
| [repair_prompt_pairing.py](../../../ver3/tools/repair_prompt_pairing.py) | Live utility. Re-stamps the pairing hash only for recordings that still pass the real parser/contract/completeness path; never edits content. Honest in design; maintains a field almost nothing reads. |
| Dual runners | Three, not two — see §1. |
| `s02.pre_revision.json` | Superseded PRB-01 answer, retained as historical evidence. Carries no `pairing_history`, so it cannot masquerade as current under the strict provider. |
| `_RETIRED_S03_OWNED` | Retired to a string constant; consumer context now derived by `assy_v3.view`. Clean. |
| `_commit_s04` | Retired at S-6/U-7; writes moved into the stage patches. Clean. |

## 8. Discrepancies between HEAD and the repository-defined S-9 target

The plan (§24, row S-9) requires *"Fixtures regenerated from conforming live upstream; the
two runners converged"* with *"a live S01→S04 chain as the evidence basis"* and E+F evidence.
§25.9 repeats it as an implementation-complete criterion.

| # | Target | HEAD | Gap |
|---|---|---|---|
| D1 | Fixtures from conforming live upstream | 13/13 agent-authored | **Whole corpus** must be regenerated (S9-I2) |
| D2 | "The two runners converged" | **Three** runners, three orchestrations | Plan understates the work |
| D3 | Live S01→S04 chain | No runner spans S01→S04 | New orchestration required (S9-I8) |
| D4 | One state/view/progression substrate | `.run()` bypass, input asymmetry, two replay providers | S9-I6 unmet (§4) |
| D5 | Complete fixture provenance | truncated prompt hash + free text | S9-I5 unmet (§5b) |
| D6 | Parameter authority explicit | 1 of 6 visible, 5 inconsistent | S9-I7 unmet (§6) |
| D7 | Record conforms to its contract | 5 required fields absent | blocks run/attempt identity (§6a) |
| D8 | Stored artifacts inventoried | 314 files never dispositioned | S9-I13 unstarted (§5c) |
| D9 | E-level unseen probe | PRB-01/02/03 all used in development | a **new** probe is required (S9-I10) |

**The plan's line numbers and its "two runners" phrasing do not describe HEAD.** Recorded
here as required by §0.

---

## 9. Frozen S-9 invariants

Recorded before any production change. Status is the honest state at S9-A: most are
**OPEN** because S-9 has not run yet, and recording them as anything else would be the
defect this repository keeps removing.

| # | Invariant | Status at S9-A | Where it will be witnessed |
|---|---|---|---|
| S9-I1 | Frozen source immutability — sources, Oracle, CAD/reference artifacts unchanged | **HOLDS** | no S-9 change touches `benchmarks/*/source`, `oracles/`, `cad_validation/` |
| S9-I2 | Live-derived fixture basis | **FAILS at HEAD** — 13/13 agent-authored (§5a) | S9-E |
| S9-I3 | No response repair | **HOLDS** — provider docstring and code perform no salvage; `repair_prompt_pairing.py` writes one metadata field and never content | S9-E |
| S9-I4 | Fixture honesty — no richer-than-live fixture | **UNTESTED** | S9-E |
| S9-I5 | Complete fixture provenance | **FAILS at HEAD** (§5b, §6a) | S9-B (record), S9-E (fixture) |
| S9-I6 | Replay/live semantic convergence | **FAILS at HEAD** — three divergences (§4) | S9-C |
| S9-I7 | DeepSeek provider fidelity | **FAILS at HEAD** — 5 of 6 parameters silent or inconsistent (§6) | S9-B |
| S9-I8 | Genuine full-live qualification | **UNREACHABLE at HEAD** (§1) | S9-C (reachable), S9-F (executed) |
| S9-I9 | Replay is regression evidence, not capability evidence | **HOLDS in doctrine** — `run_window2` docstring says so; not yet machine-checkable | S9-C |
| S9-I10 | Unseen evidence genuinely unseen | **OPEN** — PRB-01/02/03 all development-used (§10) | S9-G |
| S9-I11 | Failure preservation and attribution | **PARTIALLY HOLDS** — runners classify into PROVIDER/RESPONSE/PARSER/CONTRACT/CHECK/INTERFACE kinds | S9-C |
| S9-I12 | No benchmark-specific tuning | **HOLDS** — no case-ID branch inside `assy_v3` (FP-02 is enforced) | throughout |
| S9-I13 | Stored response artifacts migrate too | **OPEN** — 314 files never dispositioned (§5c, §10) | S9-A decision below |
| S9-I14 | Temporary bridges do not become target architecture | **AT RISK** — pairing enforcement is partial and inconsistent (§7) | S9-C |
| S9-I15 | Final implementation-complete audit | **OPEN** | S9-G |

## 10. Project decisions recorded at S9-A

These are project-owner decisions, recorded here so later steps inherit them rather than
re-deciding them.

**D-A. The ~314 historical live artifacts are NOT promoted as current conforming fixtures.**
They predate material S-4…S-8 prompt and contract changes and lack required current
provenance (`run_id`, `model_run_id`, `stage_attempt` — §6a). They are classified as
**HISTORICAL LIVE EVIDENCE** unless later inspection establishes a more precise disposition
for a specific artifact. Missing historical provenance is **not** to be fabricated, and the
314 are **not** to be regenerated. They may remain for audit and history without becoming
current fixture truth.

**D-B. S9-E regeneration targets the current authoritative replay corpus that remains
necessary** — not every response ever stored. Concretely that is the 13-file active corpus
(§5a), reduced by whatever S9-C/S9-E shows to be unnecessary, and not the 314 historical
files.

**D-C. PRB-01, PRB-02 and PRB-03 are development-used and cannot serve as unseen evidence.**
S9-G requires a **new** probe, created and evaluated only after the S-9 production revision
is frozen. Should an unseen probe later force a production semantic change, it becomes
development evidence and a further new probe is required (S9-I10).

---

## Blockers and decisions required before production changes

**No stop-and-report condition from §"Stop-and-report" is triggered.** Specifically: live
execution works (§6), no fixture has yet been shown to carry information a live stage cannot
emit, and no benchmark-specific exception has been found to be necessary. The gaps above are
S-9's scope of work, not architectural contradictions.

The two questions S9-A raised — whether the 314 historical artifacts may be promoted, and
what regeneration must cover — are **answered by decisions D-A and D-B in §10**. Neither is
open any longer.

**Cost note carried forward to S9-E, not a blocker.** A full S01→S04 chain is 6 model calls
per candidate per case (`s01, s02, s03, s03b, s04a, s04b`), multiplied by candidates and
cases. Regenerating the active corpus plus one full-live chain plus an unseen probe is a
real quota and wall-clock commitment against a paid API, and D-B bounds it to the corpus
that remains necessary.

**Next steps are S9-B (provider fidelity) and S9-C (runner convergence).** Both are pure
code work, provable with fake transports and replay providers, and require no API quota.

---

# S9-C AND S9-D — what was built, and the two defects found while building it

## 11. Defects discovered during S9-C, recorded rather than hidden

Both were found by validation rather than by review, and both were defects in the
S-9 work itself. They are kept here because the closure tests are only worth
something if they can be shown to falsify real failure modes — and these are the
real failure modes they now falsify.

### 11a. The public surface accepted its own private module

`s03_passes` and `s04_passes` were never exported from `assy_v3.pipeline`, so all
three runners failed to import — seven errors across the relevant suite. The
targeted suite passed anyway, because the surface test asked whether each symbol
existed on the package **or** on the private module. The `or` accepted the private
module and hid the missing exports.

**Correction:** the test now requires the name on the public package **and** in
`__all__`, with a direct import of all three runners beside it.

### 11b. An owner was used where a producing responsibility belongs

`StageExecution` recorded `stage.stage_id`. But `stage_id` says WHO OWNS THE WRITE,
and two passes share an owner:

| class | `stage_id` | `responsibility_id()` |
|---|---|---|
| S03TopologyAndMobility | `s03` | `s03a` |
| S03BMobilityAndAssembly | **`s03`** | `s03b` |
| S04AEnvelopeAndReach | `s04` | `s04a` |
| S04BPlacementAndMotion | **`s04`** | `s04b` |

Six producing responsibilities, **four** owners. Every pass-level lookup asked for
`s03b`, `s04a` or `s04b` and found nothing, so `full_live_qualification` — the
predicate built to certify end-to-end evidence — **could never return True for any
run whatsoever**. `PRODUCING_STAGES` was wrong twice over: it omitted the B-passes
and named `s03`, an owner, where the A-pass responsibility belongs.

**The architectural guard already existed.** `Stage.responsibility_id()` has
declared this separately all along, and `base.py`'s own comment names the mistake:
*"s03 — a string that is an owner and not a responsibility — reached a consumer
lookup at all."* The defect was discarding half of a distinction the architecture
had already drawn.

**Why the first tests missed it:** they hand-built `StageExecution` records with
the ids they expected, so they agreed with an implementation that never produced
those ids. The test asserted the author's assumption, not the system's behaviour.

**Correction:** `StageExecution` carries `stage_id` and `responsibility_id`
separately, both taken from the stage object. The qualification set is
`PRODUCING_RESPONSIBILITIES = (s01, s02, s03a, s03b, s04a, s04b)`, named for what
it holds. `by_stage` became `by_responsibility`; `owned_by` answers the ownership
question and returns **both** passes.

**Negative controls now in place:**

* mutating `responsibility_id` back to `stage.stage_id` fails S9C_24;
* removing `s03b`, `s04a` or `s04b` one at a time each fails qualification by name;
* the responsibility set is checked three ways — `STAGE_RESPONSIBILITY_CONTRACT`,
  the real Stage classes, and the pipeline constant — by exact set equality. The
  contract is authored independently of the other two and **has said `s03a` all
  along**; had this oracle existed, the defect would have failed on its first run.

No ownership semantics changed: `patch.stage_id`, `may_create`, `_authority_of`,
`GenerationRequest.stage_id` and `patch_id` are untouched.

## 12. S9-D — artifact inventory, mechanically derived

Computed by `ver3/tools/artifact_inventory.py`, by resolution rather than by
listing, so an artifact that becomes replay-consumable without a disposition shows
up as a test failure instead of a silence.

| disposition | count |
|---|---|
| `CURRENT_REGENERATION_TARGET` | **12** |
| `HISTORICAL_LIVE_EVIDENCE` | 314 |
| `HISTORICAL_MIGRATION_EVIDENCE` | 1 |
| `REPLAY_REGRESSION_ONLY` | 0 |
| `RETIRE` | 0 |
| `FROZEN_SOURCE_OR_REFERENCE` | 9 |

Active replay corpus is 13 files; **12** are regeneration targets. The thirteenth,
`probes/PRB-01/s02.pre_revision.json`, resolves for no producing responsibility, so
no replay can serve it — it is migration evidence and is retained rather than
deleted.

`live_runs` is 314 = 278 stage responses + 18 `trials.json` + 18
`model_run_records.json`; s01 102, s02 70, s03 37, s03b 19, s04a 25, s04b 25. **69**
of those (s03b + s04a + s04b) were unreachable under owner-keyed replay, which is
why no S03/S04 fixture has ever existed.

**The S9-E paid target set is therefore 12, not 13.**

## 13. The S9-D rules

**Source identity — one rule, both corpora.** `sha256(request bytes)`. Benchmarks
additionally publish it as `source_manifest.request_sha256` and all three match
exactly; probes publish nothing and are checked with the same function. No
probe-specific scheme, and no fabricated probe manifest.

**Replay addressing — by producing responsibility.** `<case>/<responsibility>.json`.
`s03a` and `s03b` now address different artifacts, as do `s04a` and `s04b`. `s01`
and `s02` are unaffected: their owner and responsibility are the same string.

**Request identity.** `GenerationRequest` carries `stage_id` (owner, unchanged) and
a new `responsibility_id`, sourced from `Stage.responsibility_id()` and nowhere
else. `producing_identity` falls back to the owner when no pass is stated.

**Fixture integrity — four bindings**, each present because a specific substitution
went undetected without it:

```
source_sha256        which source it answers
responsibility_id    which producing pass produced it
raw_response_sha256  which raw response it is
model_run_id         which run and attempt promoted it
```

plus the existing prompt pairing. **Every current fixture is missing all four** —
asserted, not merely described. They cannot be re-stamped into validity, because
the identities they lack are facts about a live execution that never happened.

**`pairing_history` remains a migration bridge.** `pairing_status` deliberately
does not consult it, so a re-stamping note cannot make a stale fixture valid;
`integrity_report` keeps it visible so S-9 can count what it retires.

**Promotion.** Provider success is not promotion. The ladder —
`PROVIDER_FAILED → RESPONSE_UNUSABLE → PARSER_FAILED → CONTRACT_FAILED →
NOT_ACCEPTED → ACCEPTED` — is kept whole, and only `ACCEPTED` may be promoted. A
hand-edited response can never be promoted whatever else is true of it. Fidelity is
proved by comparing parsed content with `_meta` removed, because JSON
re-serialization is not byte-stable; enrichment, deletion and alteration are all
caught.

**Retry selection is frozen before S9-E:** `FIRST_CONFORMING` — the first eligible
attempt is promoted, later attempts are retained and not consulted. Every attempt
keeps its own `model_run_id`, so a retry cannot overwrite its predecessor.

**Dry run.** The whole loop runs on synthetic responses with no paid call: promote
→ integrity → write → replay through the ordinary `window1` pipeline. The replayed
pass records `consumer_view_recorded`, `response_source = REPLAY`, and pairing
`PAIRED`, and the run is correctly refused full-live qualification.
