# BM-003 — source authoring record

What was written, what was deliberately left out, and where the judgement calls
were. This record exists so a reviewer can check the request against the intent
it came from without having to reconstruct the intent from the request.

**This session authored a source request and nothing else.** No Oracle, no Stage
output, no mechanism selection, no topology, no CAD, no simulation, no positive
reference, no evaluation.

- Subject: **BM-003 — Compact folding three-leg desktop stand**, fixed by the
  authoring instruction and not chosen here.
- Artifact: [`source/request.txt`](source/request.txt) — 289 words, target 150–300
- Status: **HUMAN_REVIEW_REQUIRED**, unfrozen
- `sha256` `1098f2caf1527996466f898966478989f61f511869c9db1ea6a52971d88d92c7`

---

## 1. The authoring problem

A source request has to be answerable and must not contain its own answer. Those
pull against each other, and every judgement below sits on that line.

The specific difficulty for this product: the behaviour that makes BM-003 worth
having as a benchmark — that the stand *stays open on its own* and needs *a
deliberate action* before it folds — is exactly the behaviour a mechanism
normally supplies. Describing it without naming a latch, a detent or an
over-centre link takes care, because those words are how the behaviour is usually
discussed.

The approach taken throughout: **say what the user observes, never what the
product contains.** "It needs to stay open on its own" is an observation. "It
needs a latch" is a solution. The first is answerable in several ways; the second
has already answered it.

---

## 2. Intent → request

Each area of the fixed product intent, and the sentence that carries it. No
requirement identifiers appear in the request itself; this table is the record,
not the source.

| Fixed intent | Carried by |
|---|---|
| Legs fold close to the body; narrow compact form | *"three legs that fold in close to the body, so the whole thing becomes narrow and compact when I put it away"* |
| Components remain attached and captive | *"Everything should stay attached while it is folded"* |
| No loose removable parts to fold or unfold | *"I do not want to take anything off to fold it, and I do not want loose pieces to keep track of"* |
| Unfolds manually through a comprehensible sequence | *"I should be able to open it by hand, following a sequence that makes sense as I go"* |
| Three legs spread in different directions, usable footprint | *"spread apart in different directions so they give the stand a usable footprint on the desk"* |
| Parts stay connected through the deployment path | *"Nothing should come apart or fall off while I am opening it"* |
| No tools, motor, or external fixture | *"I should not need tools, a motor, or any other equipment to do it"* |
| Stays deployed without the user holding it | *"it needs to stay open on its own. I should not have to hold the legs while I use it"* |
| No free folding, twisting, detaching, or other unintended motion | *"they should not be able to fold back, twist aside, or work themselves loose"* |
| Deliberate release required before folding | *"Before it can be folded again I want to have to do something deliberate, so it does not collapse just because I knocked it"* |
| Returns to the compact stored configuration | *"it should fold back down to the same compact shape it started in"* |
| Cycle is repeatable | *"open it and fold it away again and again"* |
| Joint and retention relationships stay intact through the cycle | *"without anything loosening, coming apart, or needing to be put back on"* |
| Assemblable through a comprehensible sequence | *"something that can genuinely be built as a product and put together in a sensible order"* |
| Assembly retains joints and locking components in ordinary use | *"it should stay together through normal opening and folding"* |
| Intended to hold a small desktop object | *"It is meant to hold a small object on my desk while I am working"* |

Every area is carried. Nothing in the request carries anything that is not in the
table.

---

## 3. Judgement calls

### 3.1 The release, without naming a lock

The instruction forbids prescribing a latch, collar, toggle, pin, spring, magnet,
screw *or any other particular locking realization*, while still requiring that a
deliberate release precede folding.

Written as: *"Before it can be folded again I want to have to do something
deliberate, so it does not collapse just because I knocked it."*

**"Something deliberate"** names an action, not a device. The clause that follows
gives the reason a user would actually give — accidental collapse — which is what
makes the requirement comprehensible without hinting at how it is met. A detent, an
over-centre geometry, a friction interface, a captive sliding element and a
separate released member all satisfy it, which is the point: the solution space
must stay open, or the benchmark cannot detect premature convergence.

### 3.2 "Stay open on its own", not "lock"

*"Once it is open, it needs to stay open on its own"* states persistence as an
observation. The word "lock" was avoided throughout, including as a verb, because
it carries a mechanism family with it in ordinary usage.

### 3.3 The unintended-motion list

The instruction requires that the legs *"must not freely fold, twist away,
detach, or acquire another obvious unintended rigid-body motion."*

Written as: *"they should not be able to fold back, twist aside, or work
themselves loose."*

"Rigid-body motion" is analysis vocabulary and does not belong in a user's
request, so the three named failures are given in the words a user would use.
The general clause was not translated — a user would not say "or any other
unintended rigid-body motion", and inventing a phrase for it would have added a
completeness claim the user never made. **A reviewer should decide whether that
omission is acceptable**; it is checklist item C5.

### 3.4 The desktop object, kept out of structural scope

*"It is meant to hold a small object on my desk while I am working."*

Permitted by the instruction, which also forbids turning it into a
structural-capacity benchmark. The sentence gives purpose and no number. No mass,
no force, no "must support", no "load". Adding any of those would create a
capacity requirement the benchmark's declared scope cannot verify, and the honest
outcome would be UNSUPPORTED — a correct answer that measures nothing.

### 3.5 Motion verbs

"fold", "open", "spread apart" are used. They describe what a user sees, and
avoiding them entirely would make the request unintelligible. They were checked
against a prescribed joint type: "swing" was rejected in an earlier draft as
implying rotation about a fixed axis, and replaced with "spread apart", which
constrains only the outcome. **Reviewer confirmation is item C4.**

### 3.6 Three things removed in drafting

- *"narrow enough to slip into a drawer or a bag"* — removed. A soft size
  threshold not present in the fixed intent, and the instruction forbids hidden
  geometric thresholds. "Narrow and compact" carries the intent without it.
- *"stable footprint"* — replaced with *"usable footprint"*, matching the
  instruction's own word. "Stable" reads as a stability criterion, which is not
  in scope and would have been a quiet acceptance threshold.
- *"anything to clamp it to"* — replaced with *"any other equipment to do it"*.
  It rendered the instruction's "external fixture" and appeared only in the
  negative, so it prescribed nothing; but "clamp" is a mechanism noun sitting a
  few lines from the release requirement, and a reviewer should not have to
  work out that it refers to something outside the product.

---

## 4. Deliberately absent

Not omissions — decisions.

| Absent | Why |
|---|---|
| Any mechanism or linkage | The mechanism is what the benchmark asks for |
| Any locking realization | Explicitly forbidden; also the widest part of the solution space |
| Any joint type | Explicitly forbidden |
| Body or component count | Explicitly forbidden; "three legs" is behaviour, not a body count |
| Hub design, assembly direction, retention feature | Explicitly forbidden |
| Every number | No dimension, angle, mass, force or count beyond the three legs |
| Acceptance criteria, predicates, evaluation instructions | Those belong to an Oracle, which does not exist and was not written |
| Requirement identifiers | A source request has none; identifiers are assigned downstream |
| Stage, DesignState or Oracle vocabulary | Would leak the pipeline's own structure into its input |

---

## 5. What must happen next

1. **Human review** of this source against
   [`BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md`](BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md).
2. **Freeze** the source once review passes, recording who reviewed it and when.
3. **Author the Oracle independently**, in `ver3/oracles/`, and freeze it
   **before** the first source-only run. Not in this session, and ideally not by
   whoever wrote this request.
4. Optionally build a positive executable reference, to validate the evaluator —
   never as a scoring target.
5. Update `descriptor.yaml` from `PLACEHOLDER`, which un-blocks the freeze gate.

Until steps 1–3 are complete, BM-003 remains a placeholder and **no stage
contract may freeze**, enforced by `test_benchmark_skeleton.py`.
