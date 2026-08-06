# BM-003 — source human review checklist

For a human reviewing [`source/request.txt`](source/request.txt).

**Current state: FROZEN at revision R3.** This checklist records the review that
led to the freeze, plus the C5 re-check required by amendment R3.

**What this review is for.** BM-001 and BM-002 have sources that were *extracted*,
so their faithfulness is checkable by comparing bytes to a witness. BM-003's
source was *authored*. There is no witness to compare against, so whether it
states the intent faithfully and contains no answer is a judgement — and the
author of a request is the worst-placed party to make it.

**Reviewer independence.** Ideally not the author of the request. Necessarily not
the same person who later authors the BM-003 Oracle, since an Oracle author who
has already shaped the request has partly answered it.

> **REVIEW COMPLETE — 2026-08-05. Outcome: ACCEPTED_WITH_EDITS.**
>
> All of A, B, D, E and F were accepted. C1–C6 were approved **subject to** two
> wording corrections, applied as revision R2 and recorded in section 4a of the
> authoring record:
>
> - *"rattle"* → *"shift out of place"*
> - *"without anything loosening, coming apart, or needing to be put back on"* →
>   *"with all normal parts remaining attached and without anything needing to be
>   removed and put back on"*
>
> Both removed words describe a **contact-level** condition that this benchmark's
> scope cannot verify; each would have produced UNSUPPORTED. The replacements
> state the same requirements at rigid-body fidelity, preserving gross mobility
> and assembly persistence without importing tolerance, wear, fatigue, fastener
> loosening or lifetime.
>
> Source at the time of that review: 300 words, `sha256 0c3c68b2ac9be8cfaffff0814722577d89386e386f0a0828ba4b1e7fb16da23c`.
>
> **Superseded by amendment R3** — see the R3 box below. The current source is
> **299 words**, `sha256 ffb7f5f9feb8e38d6ee56dbce91529f817aebbd2f7180d7dedce65da0c94929d`, `authority_status: FROZEN`.
>
> The blank checklist below is retained as the record of what was examined.

---

## A. Intent coverage

Does the request carry the fixed product intent? Section 2 of the authoring
record maps each area to its sentence; confirm each against the request itself
rather than against the table.

| | Check | ✅ / ❌ / note |
|---|---|---|
| A1 | Legs fold close to the body; compact stored form | |
| A2 | Everything stays attached when folded | |
| A3 | No loose removable parts needed to fold or unfold | |
| A4 | Unfolds by hand, in a sequence a user can follow | |
| A5 | Three legs end up spread in different directions, usable footprint | |
| A6 | Nothing comes apart during unfolding | |
| A7 | No tools, motor or external fixture | |
| A8 | Stays open without the user holding it | |
| A9 | Legs cannot fold back, twist aside, or **come off** (as amended by R3) | |
| A9b | No leg turns on its own, shifts out of place, or moves in another unexpected direction | |
| A10 | A deliberate action is required before folding | |
| A11 | Folds back to the same compact form | |
| A12 | Open-and-fold cycle repeatable | |
| A13 | Joints and retention stay intact through the cycle | |
| A14 | Can be built and assembled in a sensible order | |
| A15 | Stays together in ordinary opening and folding | |
| A16 | Intended to hold a small desktop object | |

---

## B. No solution content

The request must not answer its own question.

| | Check | ✅ / ❌ / note |
|---|---|---|
| B1 | No mechanism or linkage named or implied | |
| B2 | No locking realization — no latch, collar, toggle, pin, spring, magnet, screw, detent, or any substitute for one | |
| B3 | No joint type named or implied | |
| B4 | No body or component count (three **legs** is behaviour, not a body count) | |
| B5 | No hub design, assembly direction or retention feature | |
| B6 | No dimension, angle, mass, force or other number | |
| B7 | No geometric threshold, including soft ones ("fits in a drawer", "no taller than…") | |

> **The question behind B1–B3:** could at least three genuinely different
> mechanisms satisfy this request? If only one obvious answer exists, something in
> the wording has narrowed it, and the benchmark can no longer detect premature
> convergence to a single candidate.

---

## C. Judgement calls the author flagged

These are the places the author was least certain. Each is argued in the
authoring record; the reviewer decides.

| | Call | Reviewer decision |
|---|---|---|
| C1 | *"do something deliberate"* expresses the release without naming a lock. Is it clear enough to be answerable, and open enough not to prescribe? | |
| C2 | *"stay open on its own"* is used instead of "lock". Does it read as persistence, or does it still imply a locking device? | |
| C3 | *"It is meant to hold a small object on my desk"* gives purpose with no number. Does it stay clear of a structural-capacity requirement? | |
| C4 | "fold", "open", "spread apart" — do any read as a **prescribed motion or joint type**? ("swing" was rejected in drafting for implying rotation about a fixed axis.) | |
| C5 | **CLOSED. Re-checked at R3.** The general unintended-motion case reads, in the CURRENT source: *"Nothing should turn on its own, shift out of place, or move in some other direction I was not expecting."* Confirm it reads as a user's sentence, states only what must not happen, and prescribes nothing. *(The R1 wording quoted "rattle"; R2 removed it. Do not evaluate the R1 text.)* | |
| C6 | **Added at R3.** The named unintended motions now end *"or come off"* rather than *"or work themselves loose"*. Confirm the retention meaning survives and that no contact-degradation, tolerance, wear or lifetime property has been introduced. | |

---

## D. Register and answerability

| | Check | ✅ / ❌ / note |
|---|---|---|
| D1 | Reads as something a real person would write, not as a specification | |
| D2 | 150–300 words (current, R3: 299) | |
| D3 | No stage names, DesignState or Oracle vocabulary | |
| D4 | No requirement identifiers | |
| D5 | No predicates, acceptance criteria or evaluation instructions | |
| D6 | A competent designer could attempt this without further questions | |
| D7 | Ambiguities that remain are ones a *real* request would have — not accidents of drafting | |

> **D7 is not asking for the ambiguities to be removed.** A source that has been
> polished until nothing is open is no longer a realistic request, and the
> pipeline's ability to *record* an ambiguity rather than silently resolve it is
> part of what the benchmark measures. The question is whether each remaining
> ambiguity is one a user would plausibly have left.

---

## E. Scope boundaries

| | Check | ✅ / ❌ / note |
|---|---|---|
| E1 | No numeric load-capacity requirement | |
| E2 | No claim or requirement of material strength, stress or buckling | |
| E3 | No fatigue, wear or friction-performance requirement | |
| E4 | No manufacturing-process feasibility requirement | |
| E5 | Nothing that would require FEM, CFD or elastic snap-fit analysis to answer | |
| E6 | The in-scope behaviour — assembly, configuration-dependent mobility, deployment, locking, release, folding, retention — is all present | |

> **Why E1–E5 matter as much as the coverage checks.** A requirement this
> benchmark cannot verify does not make it harder; it makes it *emptier*. The
> honest result would be UNSUPPORTED, which is a correct answer that measures
> nothing.

---

## F. Independence

| | Check | ✅ / ❌ / note |
|---|---|---|
| F1 | No Oracle content — and no BM-003 Oracle exists yet | |
| F2 | No positive executable reference content; no geometry from any source | |
| F3 | No Ver1 or Ver2 material | |
| F4 | Does not substantially re-run a frozen dossier (nearest: `C4-drawer`, `guided-slider`, `latch-retention`, `rotary-to-linear-engagement`) | |
| F5 | Nothing in the request is keyed to this being a benchmark rather than a product request | |

---

## G. Outcome

```yaml
reviewer:            # name
review_date:         # YYYY-MM-DD
outcome:             # ACCEPTED | ACCEPTED_WITH_EDITS | REJECTED
c1_c6_decisions:     # one line each, C1 through C6
required_edits:      # empty if ACCEPTED
source_frozen:       # true only if ACCEPTED and no edits pending
```

**On ACCEPTED — done 2026-08-05:** `source/source_manifest.yaml` carries
`authority_status: FROZEN`, `human_review_complete: true`, `frozen: true`, the
decision record, and the re-hashed request.

**Amendment R3 — approved, applied, source re-frozen.** `work themselves loose`
→ `come off`. The source did not revert to unfrozen: a frozen artifact changes
only through a recorded approval, and one frozen state was replaced by another.
Current: 299 words, `sha256 ffb7f5f9feb8e38d6ee56dbce91529f817aebbd2f7180d7dedce65da0c94929d`.

**Then, and only then**, the BM-003 Oracle may be authored — independently, and
frozen **before** the first source-only run. `BENCHMARK_RESULT_CONTRACT`
invalidates a result outright when `oracle_frozen_before_run` is false: an Oracle
written after a run is not a weaker Oracle, it is no Oracle at all.

The source is frozen. BM-003 nonetheless stays a **placeholder** until its Oracle
exists — and no Oracle was authored in this session.
