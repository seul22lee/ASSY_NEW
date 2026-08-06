# SOURCE_FREEZE_REVIEW

Consolidated review of all three benchmark sources, for the human who will decide
whether to freeze them.

**Every decision below is `PENDING`.** Nothing here has been approved or frozen,
and nothing was approved or frozen autonomously. Freezing is a human act; this
document exists so that act has everything it needs in one place.

**Why freezing matters.** `STAGE_PROGRESSION_CONTRACT` step 4 requires source-only
runs, and a source-only run is only meaningful against a settled source. Running
against a source that is still being edited measures the pipeline against a moving
target, and freezing a stage on that evidence bakes the moving target in.

---

## Current gate state

All three sources block the Stage freeze gate, on all three fields:

| Benchmark | `human_review_complete` | `frozen` | `authority_status` | Blocks? |
|---|---|---|---|---|
| BM-001 | `false` | `false` | `PROPOSED` | **yes, x3** |
| BM-002 | `false` | `false` | `PROPOSED` | **yes, x3** |
| BM-003 | `false` | `false` | `PROPOSED` | **yes, x3** |

Each field blocks independently, proven in `ver3/tests/meta/test_freeze_gate.py`.
They are not redundant: a source can be reviewed but not yet frozen, marked frozen
without ever being reviewed, or be a `SUPERSEDED` revision that is nonetheless
reviewed and frozen. A missing field also blocks — a gate that fails open is not
a gate.

## Canonical layout

```
ver3/benchmarks/<benchmark_id>/source/request.txt
ver3/benchmarks/<benchmark_id>/source/source_manifest.yaml
```

One location. No duplicates, no compatibility copies, no redirects, no symlinks,
and no path-specific fallback logic — `_paths.source_manifest_path()` is a single
expression with no second path to try, because a fallback would make both layouts
permanently valid.

## Two source classes

| | `EXTRACTED_VERBATIM` | `NEWLY_AUTHORED` |
|---|---|---|
| Benchmarks | BM-001, BM-002 | BM-003 |
| Origin | copied from a pre-existing fixture | written from a fixed product intent |
| Independent witness | **yes** | **no — none exists** |
| Faithfulness checkable by | comparing bytes to the witness | human judgement only |
| Main review burden | choosing which witness is canonical | is it faithful, and answer-free? |

This distinction is the reason the review differs per benchmark. For BM-001 and
BM-002 the question is *which rendering is authoritative*; for BM-003 there is
nothing to compare against at all.

---

# BM-001 — latching storage box

**Source class:** `EXTRACTED_VERBATIM`
**Proposed authoritative source:** `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001_requirementspec.json`, field `source_text`
**SHA-256:** `a37a822a1f759dece5d1966c431be44281a68071628248fa69f76547141578d4`
**Word count:** 63

### Exact request text

```
Design a compact desktop storage box with a reusable latch. The box should open and close repeatedly without accidental opening during normal handling. The latch should be easy for a user to operate while remaining secure during transport. The product should be suitable for low-cost manufacturing and should be practical for desktop use. The design should be mechanically plausible and easy to assemble.
```

### Known discrepancies

Two witnesses exist and are **not byte-identical**. Neither was normalized.

| | Primary (fixture `source_text`) | Corroborating (`BM-001_LATCHING_STORAGE_BOX.md`, section 2) |
|---|---|---|
| Wording | identical, word for word | identical, word for word |
| Newlines | 0 — one paragraph | 8 — hard-wrapped for reading |

The specification document delimits the source explicitly: *"The system receives
only the following requirement."* That sentence is what makes the source boundary
objective rather than inferred, and both witnesses agree on where the request
starts and stops.

### Unresolved judgement calls

- **D-001-1** — Is the single-paragraph fixture the canonical rendering, or the
  hard-wrapped specification document? Affects source-clause locators only; no
  word, number or unit differs between them.

### Human decision

```yaml
BM-001:
  witness_choice: PENDING          # FIXTURE | SPECIFICATION_DOCUMENT
  human_review_complete: PENDING
  authority_status: PENDING        # FROZEN to open the gate
  frozen: PENDING
  reviewer: PENDING
  review_date: PENDING
```

---

# BM-002 — enclosed hand-cranked platform lift

**Source class:** `EXTRACTED_VERBATIM`
**Proposed authoritative source:** `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-002_requirementspec.json`, field `source_text`
**SHA-256:** `4b25163b95adf59428131da783ee2fe292e099937e196ce1e3a59cc7befb061f`
**Word count:** 73

### Exact request text

```
Design a compact desktop platform-lifting device enclosed within a housing. The user should rotate an external hand crank to raise and lower an internal platform. The platform should move approximately 80-100 mm and support a payload of approximately 1 kg. The mechanism should remain enclosed within the housing during normal operation. The product should be safe to use, mechanically plausible, easy to assemble, and practical to manufacture. Avoid obvious jamming or unstable operation.
```

### Known discrepancies

Two witnesses, **not byte-identical**, and here the difference falls inside a
quantity. Neither was normalized.

| | Primary (fixture `source_text`) | Corroborating (`BM-002_ENCLOSED_HAND_CRANKED_PLATFORM_LIFT.md`, section 2) |
|---|---|---|
| Travel quantity | `approximately 80-100 mm` | `approximately 80--100 mm` |
| Newlines | 0 — one paragraph | 15 — hard-wrapped for reading |
| Everything else | identical, word for word | identical, word for word |

The specification document delimits the source explicitly: *"The system receives
only the following request."*

**On the extra hyphen.** It is almost certainly a document-converter artifact —
the same doubling appears in that document's horizontal rules, which is how
pandoc renders an en dash. It was recorded rather than silently normalized
because it falls inside a **quantity**, and a source quantity is exactly what
Stage 01 must carry verbatim, qualifier and all. `80-100` and `80--100` parse to
the same interval but are different strings, and deciding they are the same is an
interpretation — which is the one thing extraction may not do.

### Unresolved judgement calls

- **D-002-1** — Is `80-100 mm` or `80--100 mm` the canonical text of the travel
  quantity? *(severity: medium — it is a quantity)*
- **D-002-2** — Is the single-paragraph fixture the canonical rendering, or the
  hard-wrapped specification document? *(severity: low — locators only)*

### Human decision

```yaml
BM-002:
  witness_choice: PENDING          # FIXTURE | SPECIFICATION_DOCUMENT
  travel_quantity_text: PENDING    # "80-100 mm" | "80--100 mm"
  human_review_complete: PENDING
  authority_status: PENDING
  frozen: PENDING
  reviewer: PENDING
  review_date: PENDING
```

---

# BM-003 — compact folding three-leg desktop stand

**Source class:** `NEWLY_AUTHORED`
**Proposed authoritative source:** none — **this request has no independent verbatim witness**
**SHA-256:** `80619fb12625c8a1e958af726227f380590d0d9da4505814af5a208866fd29c5`
**Word count:** 299 (target 150–300)

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
work themselves loose. Nothing should rattle, turn on its own, or move in some
other direction I was not expecting. Before it can be folded again I want to
have to do something deliberate, so it does not collapse just because I knocked
it.

After that deliberate release, it should fold back down to the same compact shape
it started in. I want to be able to open it and fold it away again and again,
without anything loosening, coming apart, or needing to be put back on.

It is meant to hold a small object on my desk while I am working.

It should also be something that can genuinely be built as a product and put
together in a sensible order, and stay together through normal opening and
folding.
```

### Known discrepancies

**None of the BM-001/BM-002 kind, and that is the problem rather than a relief.**

There is no second witness, no fixture and no prior source. BM-003 was authored
from a fixed product intent supplied by instruction; the subject was fixed by
that instruction and was not chosen by the author or by any analysis. Its
faithfulness therefore cannot be established by comparison — only by a human
reading it against the intent.

The intent-to-sentence mapping is in
[`BM-003/BM003_SOURCE_AUTHORING_RECORD.md`](BM-003/BM003_SOURCE_AUTHORING_RECORD.md).

### Revisions so far

- **R1** — one sentence added at the reviewer-flagged C5 gap, expressing the
  general unintended-motion case the first draft left untranslated: *"Nothing
  should rattle, turn on its own, or move in some other direction I was not
  expecting."* No "degree of freedom", no joint, latch, guide, bearing, linkage
  or locking mechanism, no number, and it states only what must **not** happen —
  never what prevents it.
- **R1a** — *"keep track of"* replaced with *"look after"*. An idiom, not a
  mechanical track, but `track` is a guide synonym and naming a guide is
  forbidden. The phrase tripped the audit twice (first as the substring `rack`,
  then as the whole word `track`), so it was removed rather than annotated twice.
- **R1b** — two phrases trimmed to hold the 150–300 word target after R1 pushed
  it to 306. The added sentence was not shortened; it is the point of the
  revision.

### Unresolved judgement calls

- **D-003-1** — *"do something deliberate"* expresses the release without naming
  a lock. Clear enough to be answerable, and open enough not to prescribe?
- **D-003-2** — *"stay open on its own"* is used instead of "lock". Does it read
  as persistence, or does it still imply a locking device?
- **D-003-3** — *"It is meant to hold a small object on my desk"* gives purpose
  with no number. Does it stay clear of a structural-capacity requirement?
- **D-003-4** — do "fold", "open", "spread apart" read as a prescribed motion or
  joint type? *("swing" was rejected in drafting for implying rotation about a
  fixed axis.)*
- **D-003-5** — **closed by R1**, but confirm the new sentence reads as a user's
  words and prescribes nothing.
- **D-003-6** — could at least three genuinely different mechanisms satisfy this
  request? If only one obvious answer exists, the wording has narrowed it and the
  benchmark can no longer detect premature convergence.

Full checklist:
[`BM-003/BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md`](BM-003/BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md).

### Human decision

```yaml
BM-003:
  faithful_to_fixed_intent: PENDING
  free_of_solution_content: PENDING
  d_003_1_to_6: PENDING            # one line each
  human_review_complete: PENDING
  authority_status: PENDING
  frozen: PENDING
  reviewer: PENDING
  review_date: PENDING
```

---

## All remaining human decisions

| ID | Benchmark | Decision | Severity |
|---|---|---|---|
| D-001-1 | BM-001 | Which witness rendering is canonical | low |
| D-002-1 | BM-002 | `80-100 mm` or `80--100 mm` | **medium** |
| D-002-2 | BM-002 | Which witness rendering is canonical | low |
| D-003-1 | BM-003 | Is the release expressed clearly and openly enough | medium |
| D-003-2 | BM-003 | Does "stay open on its own" avoid implying a lock | medium |
| D-003-3 | BM-003 | Does the purpose sentence avoid a capacity requirement | medium |
| D-003-4 | BM-003 | Do the motion verbs prescribe a joint type | medium |
| D-003-5 | BM-003 | Confirm the R1 sentence prescribes nothing | low |
| D-003-6 | BM-003 | Are three genuinely different mechanisms admissible | **high** |

**D-003-6 is the one to spend time on.** The others affect a locator, a
character, or a phrasing. That one decides whether BM-003 can do the job it
exists for: if the request admits only one obvious mechanism, it cannot detect a
pipeline that converges prematurely, and the third benchmark stops being an
independent witness.

## Freezing

On acceptance, for each benchmark, set in `source/source_manifest.yaml`:

```yaml
human_review_complete: true
frozen: true
authority_status: FROZEN
```

and record the reviewer and date. Re-hash `request.txt` and update
`request_sha256` and `source_word_count` if any edit was made.

**Then, and only then**, the Oracles may be authored — independently, and frozen
**before** the first source-only run of their benchmark.
`BENCHMARK_RESULT_CONTRACT` invalidates a result outright when
`oracle_frozen_before_run` is false: an Oracle written after a run is not a weaker
Oracle, it is no Oracle at all.

No Oracle exists for BM-003, and none was authored.
