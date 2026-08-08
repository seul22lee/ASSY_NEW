# Benchmark and Probe: what they mean, what they were meant to mean

Design review. No code, dashboard or validator was modified. Every claim below
cites a repository artifact.

---

## 1. What BM and PRB actually mean today

### BM — as implemented

| question | answer |
|---|---|
| data | `ver3/benchmarks/BM-00N/source/request.txt`, frozen, `read_by: s01` per the descriptor |
| upstream S01/S02 | **replayed** from `ver3/assy_v3/fixtures/responses/BM-00N/s0N.json` — human/agent-authored recordings |
| S03/S04 | **live**, from an independent provider |
| who produced the badge | `ver3/tools/run_window.py` (fixture replay) or `run_window2.py` (live) |
| what is validated | that the *machinery* completed: the response parsed, the patch validated against `DESIGN_STATE_CONTRACT`, and the fourteen/thirteen checks reported nothing |
| PASS means | "the harness ran this case and its checks returned no findings" |
| WARNING/FAIL mean | findings present / the stage returned a non-SUCCESS execution status |
| engineering claim supported | **almost none.** The badge is a statement about execution and schema conformance, not about whether the design is mechanically sound |

### PRB — as implemented

| question | answer |
|---|---|
| data | `ver3/assy_v3/probes/PRB-0N/request.txt` |
| upstream S01/S02 | **also hand-authored recordings** — `probes/PRB-01/` contains `s01.json`, `s02.json`, `s02.pre_revision.json` |
| S03/S04 | live, identically to BM |
| what is validated | *the same fourteen/thirteen checks*, nothing else |
| PASS means | exactly what it means for BM |
| engineering claim supported | the same one: the machinery completed |

**So today BM and PRB are structurally identical.** Same replayed upstream, same
live downstream, same checks, same badge semantics. The only difference is which
directory the request lives in. A probe is currently *"a fourth, fifth and sixth
case with hand-authored S01/S02"* — not a generalization test.

### The decisive omission

`ver3/oracles/` contains, for benchmarks, an independently authored statement of
what must be true: `normative.yaml` (13–14 invariants per case with
`basis_type`, `support_type`, `source_locators`) and `stage_expectations.yaml`
(per-stage `must_exist`, `must_not_be_decided`, `may_remain_unresolved`,
`provenance_required`, for all twelve stages).

**Nothing in the pipeline or the validators reads any of it.** The only consumer
is `ver3/tools/build_pipeline_dashboard.py`, and only for display.

This is correct as far as `assy_v3` goes — `FORBIDDEN_LEGACY_DEPENDENCIES.yaml`
lists `ver3/oracles/` as BLOCKING with the reason *"An Oracle states what must be
true of a run. A stage reading it is reading its own answer key."* But the
prohibition applies to the *pipeline*, not to the *evaluator*, and no evaluator
consumes it. The Oracle layer is presently evaluation content with no evaluator.

---

## 2. What the intended roles appear to have been

The repository is unusually explicit, and it does not support either option as
stated in the question.

**Evidence that a benchmark is an INPUT plus an independent ORACLE, never an
output:**

- `BM-003/descriptor.yaml` declares three separate things: `source` (frozen,
  `read_by: s01`), `oracle` (`location: ver3/oracles/held_out/BM-003/`,
  `oracle_name: HELD_OUT_BENCHMARK_ORACLE`, authored in a separate pass), and
  `positive_executable_reference` carrying an explicit `never_a_precondition`
  field. Nowhere does a benchmark declare an expected *output*.
- `ORACLE_AUTHORING_POLICY.md`: *"Never a normative target."* /
  *"Expressed as `outcome_rules`, never fixed results."* /
  **"Never freeze today's inability into a permanent expected result."**
- The Oracle is *held out* for BM-003 — a term borrowed from evaluation
  methodology, meaning it was authored without seeing a system output.

**Evidence about what a probe was for:** the frozen Window 1 review describes the
probes as *"three micro-probes, each chosen to stress something the benchmarks do
not"*, and records that they found two validator defects and one knowledge gap
that *"survived three full benchmark runs and died on the first unseen input"*.
So a probe was intended as an **unseen input that tests generalization of the
reasoning implementation**.

**And the artifact that shows what a probe's bar was meant to be:**
`ver3/oracles/micro_oracles/` — `latch-retention`, `guided-slider`,
`rotary-to-linear-engagement`, `bounded-two-state-closure`. These are named by
**function**, not by product, exactly as `principle_library.py` is. The policy
even distinguishes them formally: *"A micro-oracle must never use
`DIRECT_USER_REQUIREMENT`… A product case must symmetrically never use
`PROJECT_DEFINED_CAPABILITY`: it has a user."*

### Conclusion

Neither Option A nor Option B. The intended design was:

> **BM = a frozen input + a product-specific, independently authored Oracle of
> what must be true.
> PRB = a frozen unseen input + a function-indexed micro-oracle of what must be
> true.
> Both are judged by the pipeline's output being tested against an oracle it
> cannot see. Neither is ever a target output.**

Option A is wrong because it makes the benchmark a *reference reasoning output*
that probes should approach — which is precisely what `ORACLE_AUTHORING_POLICY`
forbids and what development rule 4 forbids. Option B is wrong because it makes
BM merely "replay", stripping it of the Oracle that is its whole point.

---

## 3. Conceptual mismatches

### M-1 — The badge measures execution, the philosophy asks about engineering

*Implementation communicates:* PASS = the harness completed and the checks were
quiet. *Philosophy intends:* a verdict about whether the run satisfies invariants
authored independently of it. *Why it matters:* a run can be schema-perfect and
mechanically absurd, and today it shows green. *Steering risk:* **high.** Every
cycle in this project has optimised the thing the badge measures. Four cycles
were spent on parse failures, id collisions, field names and completion
semantics — all real, none of them engineering quality.

### M-2 — The Oracle is authored and unread

*Implementation communicates:* by omission, that the Oracle is documentation.
*Philosophy intends:* the Oracle is the bar. *Why it matters:* the only artifact
encoding engineering correctness independently of the pipeline is not consulted
when judging the pipeline. *Steering risk:* **high** — it makes the validators the
de facto definition of quality, and a validator is a proxy written by the same
hand as the thing it checks.

### M-3 — Probes have hand-authored upstream, which contradicts their purpose

*Implementation communicates:* a probe is another case. *Philosophy intends:* a
probe is an unseen input. *Why it matters:* `probes/PRB-01/s01.json` is authored,
so the probe's S01/S02 are not generalization evidence at all; only S03/S04 are.
*Steering risk:* **medium** — it inflates apparent probe maturity, and it is how
this project reached "comparable benchmark/probe maturity" while comparing two
replays.

### M-4 — Probes have no oracle, so "probe quality" is unfalsifiable

*Implementation communicates:* probe quality = validator silence.
*Philosophy intends:* micro-oracles judge probes by function-level invariants.
*Why it matters:* without an independent bar, a probe cannot fail for being
mechanically wrong — only for being malformed. *Steering risk:* **high.**

### M-5 — BM and PRB are rendered identically

The dashboard treats them as two labels of one kind, erasing the one real
asymmetry: BM has a product oracle, PRB should have a function oracle. *Steering
risk:* medium — it invites "make the probe numbers look like the benchmark
numbers", which rule 4 forbids.

---

## 4. What an ideal evaluation philosophy would be

Setting implementation aside.

**BM should represent** a frozen product input paired with a product-specific
Oracle: invariants with a basis type and source locators, plus per-stage
expectations, plus explicitly `required_unresolved` items. Its role is to ask
*"on a problem whose correct properties we have written down independently, does
the pipeline establish them?"*

**PRB should represent** a frozen unseen input paired with a **function-indexed
micro-oracle**. Its role is *"on a problem we never fitted anything to, does the
pipeline establish the invariants that any mechanism performing this function must
satisfy?"* Probes must be run end-to-end live — a probe with authored upstream is
not a probe.

**Should BM ever receive PASS/FAIL?** BM is an input; inputs have no verdict.
**A RUN on BM receives a verdict**, and the distinction is not pedantic: it is
what stops a benchmark from acquiring an expected output. Each *invariant* gets
SATISFIED / VIOLATED / NOT_ESTABLISHED, and the run's status is their aggregate
plus the honest count of what could not be evaluated.

**What should be validated?** Three separable things, never merged:
1. **Machinery** — did it parse, conform, complete? A precondition, not a result.
2. **Contract discipline** — no sharpening, no premature selection, provenance
   intact, totality total. Properties of *process*, product-independent.
3. **Engineering correctness** — the Oracle's invariants. The only one that is
   about the design.

Today only (1) and (2) exist, and they are reported as though they were (3).

**What should the dashboard compare?** Per-invariant outcome, per case, with
NOT_ESTABLISHED as a first-class result. It should show benchmark and probe
oracle-satisfaction side by side *without a shared axis of comparison between
their contents* — never "probe looks like benchmark", always "probe satisfies its
oracle to the same degree that benchmark satisfies its own".

**What should success mean?** That the proportion of independently authored
invariants the pipeline *establishes* rises, on probes, without their oracles
having been touched. Everything else is a precondition.

**What should freeze decisions be based on?** Oracle satisfaction on probes, plus
a declaration that no invariant became unevaluable. Not validator silence.

---

## 5. Recommended evaluation model

**Judge runs against oracles the pipeline cannot read; report machinery,
discipline and engineering correctness as three separate axes; never let a
benchmark own an expected output.**

Four properties make this hard to game:

1. **The oracle is authored before, and independently of, any run** — already the
   project's stated policy, and enforceable by `ORACLE_HASHES.yaml`, which exists.
2. **`assy_v3` cannot read `ver3/oracles/`** — already enforced as BLOCKING. So
   the pipeline provably cannot fit to the bar.
3. **Probe oracles are indexed by function, not product** — so satisfying one
   cannot encode a product. This is why `micro_oracles/` is the right shape and
   why it must not be replaced by per-probe product oracles.
4. **Invariants are `outcome_rules`, not fixed results** — so a bar cannot freeze
   today's inability into tomorrow's expectation.

Why it satisfies the stated requirements: *benchmark-independent* because a probe
is judged by function invariants no benchmark supplies; *model-independent*
because the oracle mentions no model and a cheaper model is judged by the same
invariants; *architecture-independent* because invariants are about the design,
not the stages; *future-proof* because adding a stage does not change what must be
true of a mechanism; *publishable* because "held-out, independently authored
invariants, satisfaction reported per invariant with an explicit
not-established class" is a recognisable evaluation protocol.

**Why accidental benchmark-replay optimisation becomes impossible:** there is no
benchmark output to approach. The only way to raise the number is to establish
more independently authored invariants, and on probes the invariants are
function-level, so the only generalising way to establish more of them is better
engineering reasoning.

**What this model costs, stated honestly:** it will make current numbers look
worse. Most invariants will read NOT_ESTABLISHED for a long time, because the
pipeline currently stops at S04 and most invariants need geometry. That is the
correct reading, and it is more useful than a green badge for a completed parse.

---

## Closing answers

**What should BM mean?**
A frozen product input plus a product-specific, independently authored Oracle. A
quality *reference* in the sense of *"here is what must be true, written without
looking at any output"* — never a reference output, never a target answer, and
never something that itself passes or fails.

**What should PRB mean?**
A frozen unseen input plus a **function-indexed micro-oracle**, run end-to-end
live. The primary generalization evidence, and currently the weakest part of the
setup, because probes have authored upstream and no oracle at all.

**What should the dashboard communicate?**
Three separate axes — machinery, contract discipline, engineering correctness —
never collapsed into one badge; per-invariant outcomes with NOT_ESTABLISHED
first-class; provenance for every claim; and no comparison between benchmark and
probe *content*, only between each one's satisfaction of its own oracle.

**What is the actual optimization target of the ASSY pipeline?**
> The fraction of independently authored, function-level invariants that the
> pipeline can *establish with evidence* on inputs it has never seen — maximised
> without ever reading, editing or fitting to the oracles that state them.

Not validator silence. Not stage completion. Not resemblance to BM-001, BM-002 or
BM-003. Those three cases are how we learned what must be true; they are not what
the system is trying to reproduce.
