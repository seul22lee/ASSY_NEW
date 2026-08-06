# SOURCE_FREEZE_REVIEW

Consolidated record of all three benchmark sources and the human decisions that
froze them.

**All nine decisions are RESOLVED. All three sources are FROZEN.**
Decided by a human on 2026-08-05. Nothing here was approved or frozen
autonomously — the freeze is a human act, and this document is where that act is
written down.

**Why freezing matters.** `STAGE_PROGRESSION_CONTRACT` step 4 requires
source-only runs, and a source-only run is only meaningful against a settled
source. Running against a source that is still being edited measures the pipeline
against a moving target, and freezing a stage on that evidence bakes the moving
target in.

---

## Gate state — the source precondition is now satisfied

| Benchmark | `human_review_complete` | `frozen` | `authority_status` | Blocks? |
|---|---|---|---|---|
| BM-001 | `true` | `true` | `FROZEN` | no |
| BM-002 | `true` | `true` | `FROZEN` | no |
| BM-003 | `true` | `true` | `FROZEN` | no |

The gate opens **only** because all three conditions are satisfied on all three
benchmarks. Each blocks independently, and that independence is proven by test
rather than asserted: `test_freeze_gate.py` takes a fully settled envelope,
breaks exactly one field, and confirms the gate still closes — for each field in
turn, and for a missing field, which must never read as satisfied.

**This is the SOURCE precondition only.** It is not permission to freeze a stage
contract. Steps 3–7 of the progression have not run — no stage is implemented —
and BM-003 still has no Oracle. What has been removed is one prerequisite, not
the gate.

## Canonical layout

```
ver3/benchmarks/<benchmark_id>/source/request.txt
ver3/benchmarks/<benchmark_id>/source/source_manifest.yaml
```

## Authoritative source witness, per benchmark

| Benchmark | Source class | Authoritative witness |
|---|---|---|
| BM-001 | `EXTRACTED_VERBATIM` | **ORIGINAL BENCHMARK FIXTURE** — `ASSY_Ver2.0/tests/fixtures/BM-001_requirementspec.json`, field `source_text` |
| BM-002 | `EXTRACTED_VERBATIM` | **ORIGINAL BENCHMARK FIXTURE** — `ASSY_Ver2.0/tests/fixtures/BM-002_requirementspec.json`, field `source_text` |
| BM-003 | `NEWLY_AUTHORED` | **none — no independent verbatim witness exists.** Newly authored and human-approved. |

---

# BM-001 — latching storage box

**Source class:** `EXTRACTED_VERBATIM`
**Authoritative witness:** ORIGINAL BENCHMARK FIXTURE (`source_text`)
**SHA-256:** `a37a822a1f759dece5d1966c431be44281a68071628248fa69f76547141578d4`
**Word count:** 63
**Status:** `FROZEN`

### Exact request text

```
Design a compact desktop storage box with a reusable latch. The box should open and close repeatedly without accidental opening during normal handling. The latch should be easy for a user to operate while remaining secure during transport. The product should be suitable for low-cost manufacturing and should be practical for desktop use. The design should be mechanically plausible and easy to assemble.
```

### Recorded discrepancy — retained, not normalized

Two witnesses exist and are **not byte-identical**. The wording is identical word
for word; the fixture is one paragraph (0 newlines) and the specification
document is hard-wrapped (8 newlines).

The specification document delimits the source explicitly — *"The system receives
only the following requirement."* — which is what makes the boundary objective
rather than inferred. It **remains a corroborating witness**. It was not
normalized and was not modified.

### Decision — RESOLVED

- **D-001-1** — Which witness rendering is canonical?
  **→ ORIGINAL BENCHMARK FIXTURE.** `request.txt` is a byte-exact copy of
  `source_text` plus one trailing newline.

---

# BM-002 — enclosed hand-cranked platform lift

**Source class:** `EXTRACTED_VERBATIM`
**Authoritative witness:** ORIGINAL BENCHMARK FIXTURE (`source_text`)
**SHA-256:** `4b25163b95adf59428131da783ee2fe292e099937e196ce1e3a59cc7befb061f`
**Word count:** 73
**Status:** `FROZEN`

### Exact request text

```
Design a compact desktop platform-lifting device enclosed within a housing. The user should rotate an external hand crank to raise and lower an internal platform. The platform should move approximately 80-100 mm and support a payload of approximately 1 kg. The mechanism should remain enclosed within the housing during normal operation. The product should be safe to use, mechanically plausible, easy to assemble, and practical to manufacture. Avoid obvious jamming or unstable operation.
```

### Recorded discrepancy — retained, not normalized

| | Fixture (authoritative) | Specification document (corroborating) |
|---|---|---|
| Travel quantity | `approximately 80-100 mm` | `approximately 80--100 mm` |
| Newlines | 0 | 15 |
| Everything else | identical, word for word | identical, word for word |

The extra hyphen is almost certainly a pandoc en-dash artifact — the same
doubling appears in that document's horizontal rules. It was recorded rather than
silently normalized because it falls inside a **quantity**, and a source quantity
is exactly what Stage 01 must carry verbatim, qualifier and all.

**The discrepancy stays on the record even though the decision is made.** A
resolved decision is not the same as a difference that never existed: a later
reader comparing the two witnesses must find the divergence already accounted
for, rather than discover it fresh and wonder which one drifted.

### Decisions — RESOLVED

- **D-002-1** — `80-100 mm` or `80--100 mm`?
  **→ `80-100 mm`**, the exact fixture text, preserved. Stage 01 will carry
  *"approximately 80-100 mm"* verbatim.
- **D-002-2** — Which witness rendering is canonical?
  **→ ORIGINAL BENCHMARK FIXTURE.**

The specification witness containing `80--100 mm` **remains a corroborating
witness and a recorded discrepancy.** It was not normalized and not modified.

---

# BM-003 — compact folding three-leg desktop stand

**Source class:** `NEWLY_AUTHORED`
**Authoritative witness:** none — **no independent verbatim source witness exists**
**SHA-256:** `ffb7f5f9feb8e38d6ee56dbce91529f817aebbd2f7180d7dedce65da0c94929d`  *(revision R3)*
**Word count:** 299 (target 150–300)
**Status:** `FROZEN` — human-approved, amended at R3

### Exact request text

```
I need a compact folding stand for my desk.

It should have three legs that fold in close to the body, so the whole thing
becomes narrow and compact when I put it away. Everything should stay attached
while it is folded. I do not want to take anything off to fold it, or loose
pieces to look after.

When I want to use it, I should be able to open it by hand, following a sequence
that makes sense as I go. The three legs should end up spread apart in different
directions so they give the stand a usable footprint on the desk. Nothing should
come apart or fall off while I am opening it, and I should not need tools, a
motor, or any other equipment to do it.

Once it is open, it needs to stay open on its own. I should not have to hold the
legs while I use it, and they should not be able to fold back, twist aside, or
come off. Nothing should turn on its own, shift out of place, or move in some
other direction I was not expecting. Before it can be folded again I want to
have to do something deliberate, so it does not collapse just because I knocked
it.

After that deliberate release, it should fold back down to the same compact shape
it started in. The opening and folding sequence should be repeatable, with all
normal parts remaining attached and without anything needing to be removed and
put back on.

It is meant to hold a small object on my desk while I am working.

It should also be something that can genuinely be built as a product and put
together in a sensible order, and stay together through normal opening and
folding.
```

### No witness — and that is the substantive point

There is no fixture, no prior source and no second rendering. BM-003 was authored
from a fixed product intent supplied by instruction; the subject was fixed by
that instruction and chosen neither by the author nor by any analysis. Its
faithfulness could not be established by comparison, only by a human reading it
against the intent — which is what the acceptance below is.

### Revisions

- **R1** — the general unintended-motion sentence added at the C5 gap.
- **R1a** — *"keep track of"* → *"look after"* (`track` is a guide synonym).
- **R1b** — two phrases trimmed to hold the word target.
- **R2** — the two human-required wording corrections, below.
- **R3** — the pre-Oracle scope correction, below. **Current revision.**

### R2 — the corrections required at acceptance

| | Before | After |
|---|---|---|
| R2-a | *"Nothing should **rattle**, turn on its own, or move in some other direction I was not expecting."* | *"Nothing should turn on its own, **shift out of place**, or move in some other direction I was not expecting."* |
| R2-b | *"...open it and fold it away again and again, without anything **loosening, coming apart**, or needing to be put back on."* | *"The opening and folding sequence should be **repeatable, with all normal parts remaining attached** and without anything needing to be removed and put back on."* |

**What they fixed.** Both removed words describe a **contact-level** condition.
"Rattle" is free play between surfaces; "loosening" is a fastener or interference
losing grip over time. Verifying either needs tolerances, surface behaviour and a
load history — none of which this benchmark's scope covers — so each would have
produced UNSUPPORTED: a correct answer that measures nothing, quietly hollowing
out two of the requirements the benchmark exists for.

The replacements say the same thing at the fidelity actually available. *"Shift
out of place"* is a rigid-body displacement, decidable by a pose comparison.
*"All normal parts remaining attached"* is a retention relationship, decidable by
whether the connection still holds. Gross mobility and assembly persistence
survive intact; contact noise, tolerance, wear, fatigue, fastener loosening and
lifetime are all out.

### Post-edit audits

| Audit | Result |
|---|---|
| Overprescription (13 categories) | **CLEAN** |
| Underdefinition (24 intent elements) | **COMPLETE** |
| Contact-noise & lifetime | **CLEAN** |

The contact-noise category was added specifically to check these edits achieved
their purpose. It matches `rattle`, `loosen*`, `backlash`, `play`, `slop`,
`wobble`, `vibrat*`, `lifetime`, `durab*` and cycle counts.

### R3 — pre-Oracle scope correction (current)

`BM003-SOURCE-AMENDMENT-R3`, class `PRE_ORACLE_SCOPE_CORRECTION`, status
`HUMAN_APPROVED`. Recorded under `amendment_history` in
[`BM-003/source/source_manifest.yaml`](BM-003/source/source_manifest.yaml).

| | |
|---|---|
| Previous | *"they should not be able to fold back, twist aside, or **work themselves loose**."* |
| Revised | *"they should not be able to fold back, twist aside, or **come off**."* |

*"Work themselves loose"* reads as clearance growth over a load history —
contact degradation, verifiable only with tolerances and surface behaviour, both
outside this benchmark's scope. It would have produced UNSUPPORTED and quietly
hollowed out a retention requirement. *"Come off"* states the same failure as a
retention fact, decidable by whether the connection still holds.

| | R2 (historical) | R3 (current) |
|---|---|---|
| SHA-256 | `0c3c68b2ac9be8cfaffff0814722577d89386e386f0a0828ba4b1e7fb16da23c` | `ffb7f5f9feb8e38d6ee56dbce91529f817aebbd2f7180d7dedce65da0c94929d` |
| Bytes | 1556 | 1543 |
| Words | 300 | 299 |

The source was **already frozen**, so this was a formal amendment rather than an
edit: approval recorded, superseded hash retained, and the source re-frozen
rather than reverted to unfrozen.

**Timing:** before any Oracle authoring and before any positive realization
existed — `oracle_authored_at_time_of_change: false`,
`positive_reference_authored_at_time_of_change: false`.

Re-audited after R3: overprescription **CLEAN**, underdefinition **COMPLETE**,
contact degradation **CLEAN**.

### Decisions — RESOLVED, and still approved after R3

All approved, subject to R2-a and R2-b, both applied. **D-003-1 through D-003-6
remain APPROVED after amendment R3**, which narrows one phrase inside the scope
those decisions already accepted and reopens none of them.

- **D-003-1** — release expressed clearly and openly enough → **APPROVED**
- **D-003-2** — *"stay open on its own"* avoids implying a lock → **APPROVED**
- **D-003-3** — purpose sentence avoids a capacity requirement → **APPROVED**
- **D-003-4** — motion verbs do not prescribe a joint type → **APPROVED**
- **D-003-5** — general unintended-motion sentence prescribes nothing → **APPROVED**
- **D-003-6** — at least three genuinely different mechanisms admissible → **APPROVED**

---

## The nine decisions

| ID | Benchmark | Decision | Outcome |
|---|---|---|---|
| D-001-1 | BM-001 | Canonical witness | **ORIGINAL BENCHMARK FIXTURE** — RESOLVED |
| D-002-1 | BM-002 | Travel quantity spelling | **`80-100 mm`** (exact fixture text) — RESOLVED |
| D-002-2 | BM-002 | Canonical witness | **ORIGINAL BENCHMARK FIXTURE** — RESOLVED |
| D-003-1 | BM-003 | Release clear and open enough | **APPROVED** — RESOLVED |
| D-003-2 | BM-003 | "Stay open on its own" avoids a lock | **APPROVED** — RESOLVED |
| D-003-3 | BM-003 | Purpose avoids capacity requirement | **APPROVED** — RESOLVED |
| D-003-4 | BM-003 | Motion verbs prescribe no joint type | **APPROVED** — RESOLVED |
| D-003-5 | BM-003 | General motion sentence prescribes nothing | **APPROVED** — RESOLVED |
| D-003-6 | BM-003 | Three different mechanisms admissible | **APPROVED** — RESOLVED |

## Production visibility — unchanged

| | BM-001 | BM-002 | BM-003 |
|---|---|---|---|
| `production_readable` (request.txt) | `true` | `true` | `true` |
| `oracle_visible_to_production` | **`false`** | **`false`** | **`false`** |
| `positive_reference_visible_to_production` | **`false`** | **`false`** | **`false`** |

Freezing a source changes what the pipeline may **rely on**. It changes nothing
about what the pipeline may **see**. `ver3/oracles/` and `ver3/cad_validation/`
remain BLOCKING forbidden path roots.

## What is still outstanding

Freezing the sources removed one prerequisite. It did not make any benchmark
ready.

- **No Oracle exists for BM-003**, and none was authored in this session. It must
  be authored independently and frozen **before** the first source-only run:
  `BENCHMARK_RESULT_CONTRACT` invalidates a result outright when
  `oracle_frozen_before_run` is false. An Oracle written after a run is not a
  weaker Oracle, it is no Oracle at all.
- **BM-003 remains a `PLACEHOLDER`** in its descriptor, for that reason.
- **No stage is implemented**, so progression steps 3–7 have not run for any
  stage, and no stage contract may freeze.
