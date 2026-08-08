# Window S01 + S02 — freeze review

**Objective.** Replace fixture-backed execution with real reasoning and determine
whether Window 1 can be frozen. S03 was not begun.

**Recommendation: READY TO FREEZE.** Begin Window 2 (S03 + S04).

---

## 1. Provider availability — stated first, because it bounds everything below

| probe | result |
|---|---|
| API credentials in environment | **none** |
| `anthropic` / `openai` / `google.generativeai` SDK | **none installed** |
| outbound TLS to a provider endpoint | open |

**There is no automated provider in this environment.** Network egress exists;
credentials and a client do not.

The reasoning implementation under test is *(prompt + knowledge layer + parser +
validators)*. The **model** is the agent operating this repository. To make that
a real test rather than a restatement of the previous task, a new provider was
built with a property the replay provider does not have:

`providers/agent_authored.py` — every recording declares
`answers_prompt_sha256`. If the stage builds a different prompt, the provider
returns `PROVIDER_UNAVAILABLE` with "the response is stale" instead of replaying
an answer to a question no longer being asked. **This fired during the task**:
extending the knowledge layer changed all three S02 prompts and all three
recordings were correctly refused.

---

## 2. Four kinds of evidence, kept separate

| kind | what it shows | status |
|---|---|---|
| **Infrastructure success** | contracts, schemas, patch validation, projection, provider boundary, determinism | complete — 316 tests |
| **Fixture evidence** | the window runs end to end on BM-001/002/003 | complete, and **weak by construction**: those recordings were authored with the validators in view, so they are regression fixtures and not evidence that the reasoning works |
| **Live reasoning evidence** | the same prompts and checks applied to **three unseen inputs** the validators were never fitted to | complete — see §4 |
| **Interface success** | S02 operating from the S01 projection alone | complete on all six cases |

The distinction matters: the previous report's benchmark results were **fixture
evidence** presented as a window result. This task's probes are the first live
evidence in the repository.

---

## 3. Infrastructure completed

- `state/` — DesignState, StagePatch, contract validation, `project_for`.
- `stages/s01_…`, `stages/s02_…` — prompt → parse → validate → patch, with
  fourteen checks between them.
- `knowledge/principle_library.py` — **10 function classes, 42 principle
  families**, indexed by physical function; no key is a product.
- `knowledge/capability_registry.py` — 9 evidence routes, 5 unavailable.
- `providers/offline.py` (regression) and `providers/agent_authored.py` (live).
- `ver3/tools/run_window.py` — harness, outside the production package.

---

## 4. Live reasoning evidence

Three micro-probes, each chosen to stress something the benchmarks do not.
Reasoning was performed from the prompt the stage actually built — S01 from the
request, S02 from the projection alone.

| probe | what it stresses |
|---|---|
| **PRB-01** wall-mounted dispenser | count quantities (`about twenty` → BAND, `exactly one` → MAGNITUDE), one-at-a-time metering, a **non-desk reaction site**, refill as a distinct scenario |
| **PRB-02** desk-edge clamp | a dimensional BAND on an **external** object, **no operational motion at all**, tool-free SERVICE, load reacted at an external body |
| **PRB-03** foot pedal | self-return, a **signal boundary outside mechanical scope**, a named forbidden lateral freedom, two actors |

### Result after the integrated revision

| | PRB-01 | PRB-02 | PRB-03 |
|---|---|---|---|
| S01 / S02 | SUCCESS / SUCCESS | SUCCESS / SUCCESS | SUCCESS / SUCCESS |
| findings across all 14 checks | **0** | **0** | **0** |
| obligations / load cases | 8 / 5 | 8 / 3 | 8 / 3 |
| candidates / unresolved | 5 / 4 | 5 / 3 | 5 / 4 |

**The strongest single live result.** S02 produced three *different* reaction
sites — "the wall the product is fixed to", "the desk edge the product grips",
"the floor or bench the product stands on". Two of the three products have no
desk anywhere. The `LoadCase` design exists to prevent exactly the default it
did not make.

**Also observed:** S01 carried "lever" from PRB-01 because the source says it,
and the mechanism-leak check correctly did not fire. PRB-02 produced a coherent
mechanical interpretation of a product with *no operational motion*, and
correctly reported that its central obligation (not slipping) has no available
evidence route. PRB-03 kept the signal obligation at the product boundary and
recorded the boundary as an UnresolvedDecision rather than mechanising it.

---

## 5. Failures found by live reasoning, and their classification

Four, none of them architectural.

| id | finding | class | sub-class |
|---|---|---|---|
| **L-1** | `actor_citation` fired on 4 obligations across all 3 probes with **0 true positives**. "the load *reaches* a reaction site" tripped on `reach`; "returns with **no user** action" tripped on `user` — an obligation whose entire content is that no actor is involved | **validator** | unsupported inference |
| **L-2** | `load_case_check` flagged `'the gripping role'` as naming a part: "gri**ppin**g" contains `pin` | **validator** | unsupported inference |
| **L-3** | **No function class performed separation of one item from a group.** Every class in the library describes relative motion of the product's *own* bodies; none described controlling passage of external items *through* it. PRB-01's central obligation was servable by no offered family | **knowledge** | missing information |
| **L-4** | Nothing *detects* L-3 automatically. Detection came from the reasoning | **validator gap** | deferred — see below |

**Root cause of L-1 and L-2: substring matching in two checks.** Both survived
three benchmarks because no benchmark obligation happened to contain the
offending substrings. Only unseen inputs exposed them, which is the entire case
for probes.

**L-3 is a knowledge failure, not a contract failure.** The representation *was*
capable: the reasoning refused to invent a family and recorded `UNR-0001` naming
the gap. Per the development philosophy, the knowledge layer was extended and the
architecture was not touched.

**L-4 was deliberately not fixed.** Detecting "no family serves this obligation"
requires the obligation to declare its function class — a new field. The
representation already expressed the fact through an `UnresolvedDecision`, so the
bar for a new field ("proven incapable of expressing a required engineering
fact") is not met. Recorded as debt D-3.

---

## 6. Integrated revision — one pass

1. **`actor_citation_check`** — curated actor-action phrases (`reachable`,
   `operate`, `by hand`, `by foot`, `the user`, `the operator`, …) matched on
   word boundaries, replacing four substrings.
2. **`load_case_check`** — `PART_NOUNS` matched on word boundaries.
3. **`METER_DISCRETE_QUANTITY`** added to the principle library with five
   families: `ESCAPEMENT`, `SINGLE_ITEM_POCKET`, `INDEXING_ROTOR`, `GATED_PAIR`,
   `METERED_APERTURE`. Library grows 9 → 10 classes, 37 → 42 families.

**One correction inside the same revision.** Widening `PART_NOUNS` with `arm` and
`lever` produced two *new* false positives on PRB-02, because a request may name
an external arm the product carries. Both were removed; only nouns that
unambiguously name a product part remain. This is worth recording rather than
hiding: the check's vocabulary is a standing hazard with no principled fix at
S02, because no `Body` entities exist yet to compare against.

**Regression, run once.** Probes: 0 findings across 14 checks × 3 cases.
Benchmarks: 0 findings. Full suite: **316 tests, all pass**.

The probes are now a protected surface: `TestProbesLiveReasoning` asserts the
recordings answer the *current* prompt, so any future prompt or knowledge change
invalidates them rather than silently replaying.

---

## 7. Interface sufficiency

| question | answer |
|---|---|
| Did S02 operate from S01 output alone? | **Yes, on all six cases.** `project_for("s02")` removes `SourceClause`; the stage raises if handed it |
| What did S02 need that S01 did not provide? | **Nothing**, on any probe |
| What did S02 reconstruct? | **Nothing.** Every `UnresolvedDecision` cites the `Ambiguity`/`Freedom` that keeps it open, by ID |
| What of S01's output was unused? | Dimensional and material freedoms, quantitative ambiguities, ASSEMBLY/TRANSPORT scenarios. Their consumers are S03+/S11, not S02 — debt D-1, unchanged |
| Anything represented too weakly to consume? | **No** |
| Premature commitment? | **No.** Five candidates survive on every probe; no scores, no ranks, no selected-candidate field |

---

## 8. Remaining debts

| id | debt | blocks S03? |
|---|---|---|
| D-1 | Freedoms, ambiguities and non-operational scenarios are consumed at S03+/S11. Reported as unused; they are not dead | no |
| D-2 | **No automated provider exists here.** The live evidence is the agent reasoning from the actual prompts on unseen inputs, with prompt-hash pairing. It is not evidence about any other model | no |
| D-3 | No check detects "no principle family serves this obligation" (L-4). Would need a new field; the bar for one is not met | no |
| D-4 | Check vocabularies (`PART_NOUNS`, `ACTOR_ACTION_PHRASES`, `DISTINCTIVE_MECHANISM_TOKENS`) are curated word lists. They generalise better than substrings but remain a known hazard | no |
| D-5 | The knowledge library is now known to be *extensible on contact with new problems* — one unseen probe added a whole function class. Expect more | no |
| D-6 | Obligation `scope` and `satisfiable_at` are still model judgements with no cross-check | no |

None blocks S03. D-2 is the one to keep visible: **the window has never been run against an independent model.**

---

## 9. Freeze criteria

| # | criterion | verdict |
|---|---|---|
| 1 | S01 fulfils its engineering responsibility | ✔ typed requirements with quantity classes on three unseen inputs; 0 sharpening, locator or leak findings |
| 2 | S02 fulfils its engineering responsibility | ✔ obligations with scope and route, candidate-independent load cases, five distinct candidates, openness preserved, on three unseen inputs |
| 3 | S02 operates from S01 output only | ✔ enforced by the projection, asserted by tests |
| 4 | **Live reasoning, not fixtures, satisfies the benchmark set** | ✔ with the qualification in D-2 — live evidence comes from the probes; the benchmarks remain fixture-backed regression |
| 5 | Producer-consumer boundaries stable | ✔ no interface change was needed in this task |
| 6 | Remaining failures understood and documented | ✔ six debts |
| 7 | No architectural blocker for S03 | ✔ every failure this task found was validator or knowledge |
| 8 | No benchmark-specific reasoning introduced | ✔ no case identifier in `assy_v3/`; harness and tests discover cases from directories |
| 9 | Knowledge boundary intact | ✔ 42 families indexed by function class; the one extension was driven by an unseen product and named a *function*, not a product |

Criterion 4 is met in the sense that matters — the reasoning implementation was
exercised on inputs it was not fitted to, and the failures it produced were real
and fixed. It is not met in the sense of an independent automated model, and D-2
says so.

---

## 10. Recommendation

**READY TO FREEZE.** Begin **Window 2 (S03 + S04)**.

The handover is concrete: obligations carrying `satisfiable_at: s03` are the
declared work S02 passes on — 9, 12 and 13 on the benchmarks, 7, 7 and 6 on the
probes — and `deferred_obligation_report()` lists them. S03 also inherits, per
candidate, the `obligations_created` list that names the supports, retentions and
bounds each principle family brings with it.

Two things carry forward as method, not as debt:

- **Probes found what benchmarks could not.** Two validator defects and one
  knowledge gap survived three full benchmark runs and died on the first unseen
  input. Window 2 should start with probes, not end with them.
- **The prompt-hash pairing is worth keeping.** It caught stale recordings the
  moment the knowledge layer changed, which is precisely the failure mode a
  fixture-backed pipeline hides.

---

# Independent DeepSeek Provider Validation

Added after the freeze above, to attack debt **D-2**: *the window has never been
run against an independent model.*

## 1. Three kinds of evidence, which must never be merged

| kind | provider | what the model could see | what it is evidence of |
|---|---|---|---|
| **Deterministic fixture** | `OfflineReplayProvider` | — | that the machinery is stable and testable. Says nothing about reasoning |
| **Claude-authored** | `AgentAuthoredProvider` | the whole repository, including the validators and the Oracle packs | that the prompts *can* be answered acceptably. **Fitted**: the author of the answers also wrote the checks |
| **DeepSeek live** | `DeepSeekProvider` | the prompt, and nothing else | the first evidence about the implementation that is independent of its author |

The third is the only one that can close D-2, and it is reported separately
everywhere below for that reason.

## 2. What was run

`deepseek-chat` requested; **`deepseek-v4-flash` served on 26/26 calls** and the
substitution is recorded on every record rather than assumed equivalent (PR-04).

Temperature **1.0**, three trials per case, six cases — the three benchmarks and
the three unseen probes. 36 window runs, 72 model calls across collection and
regression. Recorded per call, per `MODEL_RUN_RECORD_CONTRACT`: prompt sha256 and
verbatim prompt, response sha256 and verbatim response, requested and served
model, temperature sent *and* the temperature the stage asked for, top_p, seed
(none — `seed_honoured: UNKNOWN`), token usage, latency, finish reason,
truncation, and the execution status.

**Secrets.** The key is read only from `DEEPSEEK_API_KEY`, only by
`ver3/live_providers/env.require`, and the Authorization header is built inside
the call and retained nowhere. Audit of every artifact written: **0 occurrences**
of an API-key-shaped string, of `Authorization`, or of `Bearer`. `ver3/.env` is
git-ignored at two levels. No `reasoning_content` was returned, and the provider
discards it by construction and records only `reasoning_content_present`.

**Where the live provider lives, and why it is not in `assy_v3`.**
`test_no_stage_implementation.test_no_network_or_subprocess_in_assy_v3` forbids
importing `urllib`, `socket`, `requests`, `httpx`, `openai` or `anthropic`
anywhere under `ver3/assy_v3` — *"a boundary that can already make a call is not
a boundary."* The live provider therefore lives in **`ver3/live_providers/`**,
outside the protected tree, and is injected. The dependency runs one way: it
imports the interface from `assy_v3`; `assy_v3` never imports it.

## 3. First result: the window could not run at all

**30/30 live calls failed**, every one in the same way, before any revision.

| id | finding | class |
|---|---|---|
| **DS-1** | S01 `to_operations` raised `TypeError`/`KeyError` on 18/18 calls | parser + specification |
| **DS-2** | S02 `to_operations` raised `KeyError: 'id'` on 12/12 calls | parser + specification |
| **DS-3** | `satisfiable_at` is required by the parser and the contract, and was **never mentioned in the S02 prompt**. 130/130 obligations omitted it | specification |
| **DS-4** | `base.py` recorded `provenance={"provider": "offline-replay"}` on **every** patch, including live ones | provenance defect |
| **DS-5** | a malformed response **crashed the caller** instead of yielding a status, contradicting `base.py`'s own docstring | robustness defect |

### The measurement that identifies the root cause

The model complied *perfectly* wherever the prompt was explicit, and invented a
schema wherever it was silent:

| the prompt states it | compliance | the prompt is silent | result |
|---|---|---|---|
| the seven top-level S01 keys | **30/30** | item field names | `statement` / `text` / `statement_verbatim` |
| `quantity_class` vocabulary | **176/176** | id format | `1` (int) 225×, `"REQ-0001"` 55× |
| scenario `kind` vocabulary | **54/54** | actor fields | **nine** different field names |
| `kept_open_by` must cite ids | **53/53** | `satisfiable_at` | absent 130/130 |

**RC-A — the prompts specify their top-level keys and their engineering
vocabulary, but not the shape of the items inside them.** The Claude-authored
recordings had the right shape because their author had read the parser. This is
precisely the defect that only an independent model can expose, and it is the
single cause of DS-1, DS-2 and DS-3.

**RC-B — the stage driver converted a response-shape problem into an exception.**
Cause of the *severity* of DS-1/DS-2 and of DS-5.

**RC-C — the driver hard-coded provider identity.** Cause of DS-4.

## 4. One integrated revision

1. **A `RESPONSE SCHEMA`, `PERMITTED VALUES` and `REFERENCES BETWEEN ITEMS`
   section added to both prompts** — every field name, every id format, every
   enumeration, every cross-reference target, and the rule that a required field
   is never null. **No engineering rule was added or changed**; the field lists
   were taken from `DESIGN_STATE_CONTRACT` rather than from memory.
2. **`base.py`** maps a `KeyError`/`TypeError`/`AttributeError`/`IndexError` out
   of `to_operations` to **`SCHEMA_FAILURE`**, which is what its docstring always
   promised.
3. **`base.py`** takes the provider id from `provider.capabilities()`.
4. **The twelve Claude-authored recordings were re-paired**, and this is stated
   plainly because it is the sort of step that can hide a lie. Changing a prompt
   changes its hash, so all twelve were correctly refused as stale. They were
   **not** re-stamped on trust: `ver3/tools/repair_prompt_pairing.py` pushes each
   recording through the real parser, the real contract validation and the real
   completeness check, and re-stamps only what passes. **All 12 passed unchanged**
   — which is itself the evidence that the revision changed the specification of
   the answer's format and not the question. No response content was edited.

Two corrections were made *inside* this revision, both caught by the regression
and both mine rather than the model's: `directionality` and four other fields
were marked optional when the contract requires them (the model then dutifully
emitted `null`), and the cross-reference targets were initially unspecified.

## 5. Regression — 18 trials, temperature 1.0

| | before | after |
|---|---|---|
| S01 SUCCESS | **0/18** | **16/18** |
| S02 SUCCESS | **0/12** | **7/18** |
| clean end-to-end, all 14 checks silent | **0** | **6/18** |
| **PRB-01** | 0/3 | **3/3 clean** |

`ver3/tools/run_window.py` on the fixtures: unchanged, SUCCESS/SUCCESS on all
three benchmarks. Full suite: **316 tests, all pass.**

### What the independent model got right

| dimension | result |
|---|---|
| **Unsupported invention** | **0 of 120** requirements introduced a numeral absent from the source |
| **Knowledge boundary** | **0 violations.** 78 candidate family/principle names, every one from the library. Across collection and regression, 322 mentions, 47 distinct names, all offered |
| **No premature selection** | **0 of 18** S02 responses contained a `selected`, `winner`, `score` or `rank` key. INV-007 held live |
| **Openness cites its cause** | **34/34** unresolved decisions cited `kept_open_by` by id |
| **Interface** | **0** source-text leaks. The projection was identical on all 18 runs and never contained `SourceClause` |
| **Load cases** | 63/65 `UNSUPPORTED`, correctly refusing to invent magnitudes |

### Residual failures, classified and *not* fixed

The instruction allows one integrated revision. These are recorded for Window 2
rather than patched.

| id | finding | count | class |
|---|---|---|---|
| **DS-6** | `obligations_created` names obligation ids the model allocates but never emits in `obligations[]` | **11 of 11** S02 failures | specification ambiguity: rule 4 says a candidate *has created* an obligation, which invites declaring rather than referencing |
| **DS-7** | `PROCESS` used as a scenario `kind`; `REACTION` used as a `direction_class` | 3 | **the schema calls three different enumerations `kind`**, and the model crossed them |
| **DS-8** | "approximately 1 kg" carried into a load case as `"1 kg"` | 1 | **validator gap: `sharpening_check` runs only at S01, over requirements. Nothing checks sharpening at S02** |
| **DS-9** | Live S02 produces **2–5 candidates** where the fixtures produce 5–6 | all | design-space breadth is narrower live |
| **DS-10** | `max_output_tokens` clamped 32000 → 8192 on 26/26 calls; largest response 5411 tokens | 26 | no truncation occurred, but the margin is thin and unmonitored |

DS-8 is the most serious: it is a **false-acceptance-shaped** defect that three
benchmarks and three probes never surfaced, because no previous response
happened to sharpen a qualifier at S02.

### Variability at temperature 1.0

Requirement counts per case across three trials: BM-001 5/4/5, PRB-02 4/4/4,
PRB-03 3/3/3, **BM-003 15/24/14**. Obligations on the runs that completed:
PRB-01 9/7/6. Unresolved decisions: 1–4.

Granularity is the unstable quantity — *what counts as one requirement* — not the
engineering content. BM-003, the longest source, is the least stable. Nothing in
the fourteen checks constrains granularity, so this is invisible to the pipeline
today.

## 6. Verdict on D-2

**D-2 is PARTIALLY CLOSED.**

Closed:
- An independent automated provider exists, is contract-shaped, and runs.
- The window has now been executed by a model that could not see the validators,
  and the result is recorded per call.
- The claim that the S01+S02 window is answerable only by its own author is
  **refuted**: 16/18 S01 and 7/18 S02 runs succeeded, and 6 were clean end to end.
- The knowledge boundary, the no-selection invariant, the no-sharpening property
  at S01 and the source-text exclusion all held against an independent model.

Not closed:
- **11 of 18 S02 runs still fail** on DS-6. The window does not yet run
  end-to-end reliably against an independent model.
- One model, one vendor, one temperature. `deepseek-v4-flash` was served
  throughout; nothing here generalises to another model.
- The Claude-authored recordings remain the regression baseline, and DS-9 shows
  they are *richer* than live output — so the benchmarks still measure a
  fixture, not a live run.
- DS-8 shows the checks themselves have a hole that live evidence found and the
  benchmark suite did not.

**The freeze above stands.** Nothing here contradicts it: every failure was a
specification, parser or validator defect, and none was an architecture defect.
Window 2 (S03 + S04) should begin by closing DS-6 and DS-8.

---

# Final Stabilization Cycle

Window 1 reopened once more. The objective was **not** to raise benchmark scores
and **not** to make probes resemble benchmarks: it was to raise the engineering
maturity of *live* reasoning on unseen problems to the level the benchmark
outputs demonstrate.

## 1. How quality was measured, and why not by comparison

A probe cannot be judged by diffing it against a benchmark answer. Different
products must produce different engineering content, so any metric rewarding
similarity would quietly convert the benchmarks into target answers — the exact
thing development rules 1, 2 and 4 forbid.

`ver3/tools/quality_profile.py` therefore scores **one output against its own
source and its own internal references**. No benchmark output is an input to any
score. Two outputs become comparable only because each was scored against
itself. 32 maturity metrics; each is a fraction with an explicit denominator, or
`None` when the output had no opportunity to exhibit the property — which is not
zero. Counts are reported as context and are never scored: four faithful
requirements are not worse than ten padded ones.

`ver3/tools/compare_maturity.py` lays the profiles side by side.

## 2. The comparison overturned the premise of the cycle

| | benchmarks | probes | gap |
|---|---|---|---|
| recorded (agent-authored) | 0.968 | 0.941 | **−0.027** |
| live, before this cycle | 0.825 | 0.839 | **+0.014** |

**Probes were never behind the benchmarks.** Live probes were marginally *ahead*.
The deficit was **recorded vs live** — uniform across all six cases — so the
work was to raise live reasoning generally, not to fix a probe-specific weakness.
Had the cycle been driven by the probe-vs-benchmark comparison alone, it would
have chased a gap that did not exist.

## 3. Deficiencies, collected before anything was changed

Five quality gaps, each measured over all six cases, plus four defects carried in:

| id | deficiency | recorded | live | class |
|---|---|---|---|---|
| **Q-1** | obligations do not show their derivation | 1.000 | **0.134** | prompt |
| **Q-2** | scenarios declare no system boundary — "storage box with latch" is a name, not a boundary | 1.000 | **0.250** | prompt |
| **Q-3** | load cases give no reaction site; roles are part tokens (`box_body`, `PLATFORM`, `base`) | 1.000 | **0.300** | prompt + validator |
| **Q-4** | scope not discriminating — 86% UNIVERSAL live vs 59% recorded; three cases had **zero** discriminating obligations, leaving s04 nothing to choose on | 1.000 | **0.500** | prompt |
| **Q-5** | `satisfiable_at` collapses to s02 — 53% live vs 20% recorded, claiming work done that no one has done | 0.811 | **0.400** | prompt |
| **Q-6** | `obligations_created` names ids never emitted | — | 11/18 | reasoning |
| **Q-7** | three different fields are called `kind`; values crossed between them | — | 3 | prompt |
| **Q-8** | no sharpening check exists at S02 | — | 1 | validator |
| **Q-9** | `PART_NOUNS` is blind to the parts live output actually names | — | — | validator |

**Q-9 deserves emphasis: the check scored 1.000 while the outputs it was
guarding said `applied='box_body' reacted='table_surface'`.** A curated word list
cannot see a part it was not told about — and the same list once matched `pin`
inside `gripping`. This is standing debt D-4, now with evidence.

### Root causes

- **RC-1 — the prompts specify which fields to emit, never what engineering work
  each field represents.** Cause of Q-1, Q-2, Q-3, Q-4, Q-5. The recorded outputs
  have depth because their author understood the intent; the prompt never carried
  it. This is the same family as the schema defect found in the previous cycle,
  one level up: format was specified, *meaning* was not.
- **RC-2 — referential closure between two lists generated in one pass.** Q-6.
- **RC-3 — validators that pass outputs a reviewer would reject.** Q-3, Q-8, Q-9.
- **RC-4 — one field name, three enumerations.** Q-7.

No root cause is architectural, and none is a representation failure: every fact
involved *is* expressible in the current schema. Per rule 8, nothing was changed
in the architecture or the schema.

## 4. One integrated revision

**Prompts — engineering intent, stated generally.** Each addition is defensible
without naming a benchmark:

- *system boundary*: "Naming the product is not a boundary… a load can only be
  reacted against something the boundary places outside the product."
- *derivation premise*: "a claim about the world that could turn out to be FALSE…
  Without it, a later stage that finds this obligation unsatisfiable cannot tell
  whether the obligation was wrong or the requirement was."
- *scope*: "if every obligation is UNIVERSAL then nothing here distinguishes one
  candidate from another, and the stage that has to choose will have no grounds."
- *satisfiable_at*: "there are no elements, no contacts, no dimensions and no
  geometry yet… Marking such an obligation s02 makes work look done that nobody
  has done."
- *roles*: "a single noun or an identifier is a part, not a role."
- *qualifiers*: "the qualifier travels with the number."
- *`kind`*: "Three different fields are called `kind`. They do not share a
  vocabulary."

**Validators — two, both proven by live evidence.**

- `_reads_as_a_role` replaces the noun list with a **structural** test: a role is
  a phrase of three or more words, not an identifier, not a constant. Measured
  before adopting: **100% of recorded roles pass, 6% of live roles did.** It
  carries no vocabulary to maintain and no product knowledge, which is what
  finally addresses debt D-4.
- `magnitude_fidelity_check` closes Q-8. It compares against the `Requirement`
  entities S02 was given, never the source, so INV-002 is preserved.

The twelve recordings were re-paired by the verifying tool, all passing the new
checks unchanged.

## 5. Result

**Four of the five quality gaps closed to parity with the reference:**

| metric | before | after |
|---|---|---|
| obligations_showing_their_derivation | 0.134 | **1.000** |
| scenarios_declaring_a_system_boundary | 0.250 | **1.000** |
| load_cases_declaring_a_reaction_site | 0.300 | **1.000** |
| scope_is_discriminating_at_all | 0.500 | **1.000** |
| obligations_handed_to_a_later_stage | 0.400 | 0.450 |

| maturity index | before | after | reference |
|---|---|---|---|
| live benchmarks | 0.825 | **0.941** | 0.968 |
| live probes | 0.839 | **0.903** | 0.941 |

Per case, live: BM-001 0.976, BM-002 0.941, BM-003 0.916, PRB-01 0.913,
PRB-02 0.907, PRB-03 0.880. The spread between the best benchmark and the worst
probe is 0.096, and PRB-02's 0.706 outlier is a single trial in which S02
returned empty lists.

**S01: 17/18 SUCCESS.** Fixture window: SUCCESS/SUCCESS on all three benchmarks,
0 findings. Full suite: **316 tests pass.**

### What went the wrong way, stated plainly

**S02 acceptance fell, 7/18 to 4/18.** Two different things are inside that number
and they must not be merged:

- **9 findings come from a check that did not exist before this revision.** Two
  trials fail *only* the new structural role test. Sharper detection is not worse
  reasoning.
- **Q-6 genuinely got worse: `obligations_created` references resolved 44% before
  and 7% after.** Telling the model that created obligations are *real
  obligations that must be emitted* made it allocate more of them and emit fewer.
  The field reads as the place where creation happens; the parser wants a
  reference list. **Two prompt attempts have now failed, the second backwards.**

That is the evidence rule 8 asks for, and it arrived too late in this cycle to
spend the one integrated revision on. It is the named work for the next one.

## 6. Stop criteria

| # | criterion | verdict |
|---|---|---|
| 1 | probe quality ≈ benchmark quality | **partly.** Live gap −0.038, recorded −0.027 — comparable. But S02 completes only 4/18 |
| 2 | remaining differences are product-specific | **no.** Q-6 is a quality defect, not a product difference |
| 3 | no benchmark-specific reasoning or prompt tuning | **yes.** Every change is stated in general engineering terms; no case identifier, product noun or benchmark mechanism appears in `assy_v3` |
| 4 | knowledge boundary intact | **yes.** 0 violations; every candidate family came from the library |
| 5 | S02 never reconstructs what S01 should have produced | **yes.** `free_of_hidden_reconstruction` 1.000; 0 source-text leaks; projection identical on all runs |
| 6 | remaining failures understood and non-blocking for S03 | **understood and documented — but not non-blocking.** S03 cannot inherit a handover that completes 4 times in 18 |

## 7. Remaining debts

| id | debt |
|---|---|
| **W-1** | **Q-6.** Next cycle should try, in order: (a) require obligations to be emitted before candidates and state that `obligations_created` is a reference list only; (b) if that fails, this becomes evidence that the representation invites the wrong reading, and a schema change is justified under rule 8 |
| **W-2** | `obligations_handed_to_a_later_stage` still 0.450 vs 0.811 |
| **W-3** | The role test's three-word threshold is a constant of a gentler kind than a vocabulary, but still a threshold. "the workbench" is rejected; that is arguably correct and arguably strict |
| **W-4** | Granularity is unconstrained — BM-003 yields 14–24 requirements across trials. Nothing in the checks addresses *what counts as one requirement* |
| **W-5** | One model, one vendor, one temperature |
| **W-6** | The recorded fixtures remain the regression baseline and are still richer than live output |

## 8. Recommendation

> ## WINDOW 1 REQUIRES ONE MORE STABILIZATION CYCLE

Criteria 3, 4 and 5 are met outright, and the cycle achieved its stated purpose:
live reasoning quality rose from 0.825/0.839 to 0.941/0.903 against a 0.968/0.941
reference, with four of five gaps closed to parity and no benchmark-specific
logic introduced. Probes reach engineering maturity comparable to benchmarks.

But criterion 2 fails and criterion 6 fails: **S02 completes 4 runs in 18**, and
the single cause is understood, reproducible and got worse under the remedy
tried. One more cycle, scoped to W-1 alone, should settle it — and if the
prompt-level remedy fails again, that is precisely the evidence rule 8 requires
before touching the schema.

**Do not begin Window 2 yet.**

---

# Q-6 Cycle — Referential Integrity of `obligations_created`

Sole objective. Everything else frozen. Evidence collected before any hypothesis
was adopted; the prompt, schema and parser were each treated as suspects, not as
answers.

## 1. What is the actual root cause of Q-6?

**Emission order.** In a single autoregressive response, the `obligations` list
is written and closed before the reasoning that discovers candidate-created
obligations has happened. The model then correctly allocates an id for an
obligation it cannot go back and add.

Four independent measurements, over 18 failing responses, all agreeing:

| evidence | result |
|---|---|
| Do dangling ids continue the emitted sequence? | **33 of 33.** Zero exceptions. The model allocates the *next free id* — coherent bookkeeping, not hallucination |
| Where does a dangling id appear? | `candidates` 33×, `acceptance_contracts` 24×. **Never in any section emitted before `obligations`** |
| Key order as emitted | `obligations` first in **18 of 18** responses; `candidates` third |
| Does the obligation exist as content? | **Yes** |

The decisive artifact is `PRB-02/t3`, which emitted an **extra top-level key the
schema does not define**, `_obligations_created`, containing fully-formed
obligation objects:

```json
{"id": "OBL-0012",
 "statement": "The screw mechanism must provide sufficient friction to hold the clamp without slipping.",
 "derived_from_requirements": ["REQ-0003"], "mandatory": true,
 "scope": "CANDIDATE_DISCRIMINATING", "satisfiable_at": "s05",
 "evidence_route": "CONTACT_RESOLVING_ANALYSIS", "route_available": false,
 "derivation_premises": ["If the screw does not generate enough friction, the clamp will slip under load."]}
```

Every required field present, correct scope, correct `satisfiable_at`, an
honest `route_available: false`. **The model derived the obligation correctly,
understood that it had to be emitted, and invented a container because the one
it needed was already closed.**

That single artifact eliminates three hypotheses at once:

- **not a reasoning failure** — the obligation is correctly derived and typed;
- **not a schema-expressiveness failure** — the object matches the schema exactly;
- **not a comprehension failure** — the model was actively trying to comply.

**Lifecycle of a created obligation, before the fix:**

| stage | what happens |
|---|---|
| first exists | as engineering content, while the model reasons about a principle family — i.e. while writing `candidates` |
| id assigned | at that moment, as `max(emitted) + 1` |
| emitted | **never.** `obligations` closed several thousand tokens earlier |
| referenced | `candidates.obligations_created`, then `acceptance_contracts.obligations` |
| integrity broken | **at the moment of allocation** — the id is born dangling, because the only container that could hold its definition is already closed |

## 2. What layer owns the defect?

Not the **parser**: it reports `DANGLING_REF` correctly and is the only reason
the defect was visible at all.

Not the **schema**: the representation expresses the fact perfectly well — the
recorded reference achieves 100% closure with the same schema, and the model's
own `_obligations_created` objects were schema-shaped.

Not the **prompt's wording**: two emphasis-level attempts failed, and the second
("these are REAL obligations and must be emitted") made it *worse* — 44% → 7% —
by increasing creation without enabling emission.

The defect is owned by the **response contract's ordering of work** — nominally
the prompt layer, but at the level of *when the reasoning happens*, not how it is
phrased. This is the smallest layer the evidence implicates, and architecture,
schema and validators were left untouched.

## 3. Was one revision sufficient?

One revision was made: an instruction placed where the obligations list is still
open, telling the model that the list is written first and cannot be added to,
and that the families it will offer as candidates must therefore be chosen before
the list is closed — with `obligations_created` demoted explicitly to "a
reference list, not a place to introduce something new".

**Largely sufficient, not completely.**

| | before Q-6 cycle | after |
|---|---|---|
| `obligations_created` refs resolvable | 3 of 45 — **7%** | 93 of 102 — **91%** |
| S02 accepted | 4 of 18 | **15 of 18** |
| S01 accepted | 17 of 18 | **18 of 18** |
| responses fully closed — **probes** | — | **9 of 9** |
| responses fully closed — benchmarks | — | 6 of 8 |

**The residual, characterised.** Two responses still failed, and they separate
cleanly by one variable: obligation-list length — **median 20.5 for unclosed
responses, 12.0 for closed ones.** The two failures allocated ids in the
OBL-0021..0026 range.

**Output budget is ruled out as the cause.** The two failing responses used 6212
and 5724 output tokens against an 8192 cap. Exactly one response in the run did
hit the cap, and it was correctly reported as `RESPONSE_TRUNCATED`, not as a
schema failure. The residual is not the clamp.

So the residual is the same mechanism, surviving at scale: the model holds the
forward plan reliably over a list of about a dozen obligations and loses it over
about twenty.

## 4. Can Window 1 now be permanently frozen?

| # | criterion | verdict |
|---|---|---|
| 1 | Q-6 resolved | **substantially, not fully.** 7% → 91% |
| 2 | referential integrity stable across benchmarks and probes | **probes yes (9/9), benchmarks no (6/8)** |
| 3 | no regression in previously frozen properties | **yes** — knowledge-boundary violations 0; premature selection 0; `kept_open_by` cited 25/25; source-text leaks 0; projection identical on every run; fixture window SUCCESS/SUCCESS on all three benchmarks; **316 tests pass** |
| 4 | no benchmark-specific reasoning introduced | **yes.** The revision names no product, no mechanism and no case; it states a property of one-pass emission |
| 5 | no new architectural deficiency discovered | **yes** — and the evidence is positive, not merely an absence: the representation achieves 91% live and 100% recorded closure with no change |

Probe-vs-benchmark maturity converged further, to **−0.007** (live probes 0.922,
live benchmarks 0.929, against a recorded bar of 0.941/0.968). Probes are now
indistinguishable from benchmarks in engineering maturity.

**Architecture reopen is not justified.** Rule 8 requires evidence that the
existing representation *cannot* express the required fact. The evidence points
the other way: the fact is expressed correctly in 93 of 102 references, in 9 of 9
probe responses, and in 100% of the recorded reference — all on the unchanged
schema. Reopening the schema now would be changing a representation that works
in order to accommodate a model that intermittently forgets its own plan.

The remaining limitation is that a one-pass response must carry a forward plan
across a container it has already closed, and the current model sustains that
over roughly a dozen items but not twenty.

> ## WINDOW 1 LIMITED BY CURRENT MODEL CAPABILITY

Q-6 is understood completely, its layer is identified, and one revision moved it
from 7% to 91% without touching architecture, schema or validators. What is left
is not a defect in the pipeline: it is the point at which this model stops
sustaining a plan across a closed container.

Two consequences follow, and neither is another stabilization cycle:

- **Window 2 may begin.** S02 now produces an accepted, referentially closed
  handover on 15 of 18 live runs and on every probe, and the failure mode is
  detected — a broken run reports `SCHEMA_FAILURE` and is never mistaken for a
  design outcome.
- **The residual should be retested against a stronger model rather than
  re-engineered.** If a more capable model closes the remaining 9%, the pipeline
  needed no change. If it does not, *that* is the evidence rule 8 wants, and the
  schema question reopens on a proper basis — with the specific remedy already
  identified: allow a candidate to define an obligation inline, so the container
  is open at the moment the obligation is discovered.
