# S01–S04 ARCHITECTURE FREEZE

**Status: FROZEN FOR IMPLEMENTATION PLANNING.**

This is the short normative entry point. `S01_S04_ARCHITECTURE_REVISION_PROPOSAL.md` is the
rationale; `S01_S04_ARCHITECTURE_FALSIFICATION_REVIEW.md` is the challenge record. **Where
this record and the proposal disagree on a normative rule, this record governs.**

---

## 1. Freeze scope

**Frozen:** the architecture *concepts* for S01–S04 — what persists, what is authoritative,
how authoritative facts change, what each stage must receive and how that is determined, the
LLM/deterministic boundary, commitment and gating semantics, and what assurance may claim.

**Not frozen, and deliberately so:** field names, APIs, validator designs, prompt text, the
final status vocabulary, and the mechanism of dependency propagation. These are
implementation decisions.

**Not answered:** the scientific questions the audit left open (§10). Freezing the
architecture does not close them.

---

## 2. Evidence basis

`P4B_FINAL_SYNTHESIS.md` — **COMPLETE AND FROZEN**, capabilities C-01…C-22, requirements
R-1…R-15, traceability §21 (14 FINAL, **R-5 PROVISIONAL**). Supporting chains in P1–P3, P4A,
P5 (incl. §20) and P6.

**Two statuses are kept distinct throughout, and neither overwrites the other:**

> **AUDIT EVIDENCE STATUS ≠ ARCHITECTURE DESIGN CHOICE.**
>
> An architecture may rationally commit where evidence is incomplete. It may not relabel the
> evidence. Where this record adopts a rule that the evidence does not by itself establish,
> it says so.

---

## 3. Final architecture invariants

| # | Invariant |
|---|---|
| **FA-1** | State is accumulated and additive. Nothing is deleted. Supersession retains both values. |
| **FA-2** | Every value belongs to exactly one authority class: **A** authoritative engineering state · **B** deterministic derived state · **C** ephemeral/view/cache · **D** assurance artifact. |
| **FA-3** | Class-A state changes **only** through `CREATE` · `EXTEND` · `SUPERSEDE` · `INVALIDATE`, each carrying provenance. No stage, runner, projection helper, absorber, provider adapter or validator may mutate class-A facts outside this path. |
| **FA-4** | A class-B value carries its premise set and is recomputable. With insufficient premises it is **not computed** — the gap is reported. A derived value never masquerades as an authored engineering fact. |
| **FA-5** | If a class-A premise is superseded or invalidated, every dependent commitment **loses unqualified authority**. The consequence is represented, not implied. |
| **FA-6** | A consumer view is sufficient only if it satisfies **both** sources (§4). Neither implies the other. |
| **FA-7** | The required minimum is **derived from contracts upstream of the consuming stage**. A stage may widen it with contributory context; it may never narrow it. |
| **FA-8** | Absence of evidence never becomes a positive engineering assertion. An undetermined cell, field or disposition is explicitly undetermined. |
| **FA-9** | Recognised uncertainty can bind: an unresolved item blocks exactly when it names a fact class the next consumer's or gate's required minimum marks required. |
| **FA-10** | A property carries `ENGINEERING_ESTABLISHED` only from an ENGINEERING-CONSEQUENCE check of declared independence with inputs at or above its declared minimum maturity. Establishment is never inherited. |
| **FA-11** | Context is bounded semantically. Positional truncation is prohibited; an unsatisfiable budget is a recorded condition. |
| **FA-12** | Only S01 reads raw source. Every entity family has exactly one owning stage. Every referenceable entity has a resolvable id. |

---

## 4. Final Consumer Sufficiency rule

> **Required Consumer View =
> Representational Dependencies ∪ Engineering Reasoning Premises ∪ justified contributory
> context.**

**Two sources, two questions, neither implying the other:**

| | **A — REPRESENTATIONAL** | **B — REASONING** |
|---|---|---|
| Question | *Can the consumer's outputs be represented with complete and traceable meaning?* | *Has the consumer received the engineering premises the decisions it is responsible for require?* |
| Derived from | the **output / entity semantic contract** | the **stage responsibility contract** |
| Chain | output field → declared referent | responsibility → engineering question → required premise class |

**Derivation chain (normative):**

```
Stage Responsibility Contract ── derives Engineering Questions
                                        └── derives Required Reasoning Premise Classes ──┐
Output / Entity Semantic Contract                                                        │
        └── derives Required Representational Dependencies ───────────────────────────────┤
                                                                                          ▼
                                                     Required Minimum Consumer Semantics
                                              (+ stage-authored CONTRIBUTORY, widening only)
                                                                                          ▼
                                                        Consumer View Construction
                                                                                          ▼
                                                     Independent Sufficiency Assessment
```

**Prohibitions:** the generated view may not define its own completeness criterion; the
consuming stage may not author any part of the minimum; a sufficiency assessment whose only
inputs are a declaration and a view is prohibited, because it is structurally incapable of
detecting an omitted requirement.

**Two findings, never conflated:** **UPSTREAM INSUFFICIENCY** (no instance exists in
accumulated state) vs **PROJECTION FAILURE** (instances exist and the view omits them).

**Residual limitation, stated plainly.** This architecture does **not** prove that the
responsibility and semantic contracts contain all mechanical knowledge competent reasoning
requires. They are human-authored. **No claim of mathematical completeness of engineering
reasoning is made.** The objective is narrower and achievable: *a missing dependency becomes
an explicit contract defect — locally attributable — rather than silent context loss.*

---

## 5. Final authority / mutation rule

**The HYBRID AUTHORITY MODEL.**

| Class | Examples of the class | Rule |
|---|---|---|
| **A — authoritative engineering state** | requirements · physical obligations · load cases · reaction-site requirements · topology · physical interactions · constraint relations · mobility dispositions · spatial commitments · configurations and transitions · selection decisions · unresolved items that gate commitment | **controlled mutation only**, provenance required |
| **B — deterministic derived state** | enumerated DOF domain · graph indexes · derived adjacency · normalized lookups | recomputable from premises; never authored-looking |
| **C — ephemeral / view / cache** | prompt serializations · consumer views · rendering caches · transient bounding computations · provider payloads | freely regenerated |
| **D — assurance artifacts** | check results · findings · establishment claims | append-only; consumers of class A, never producers of it |

**Rejected outright:** *arbitrary direct authoritative writes plus auditing after the fact.*
It is not an open alternative. The audited system had exactly one such path; it wrote spatial
commitments with no provenance, ownership check or validation, and nothing in the system
could have detected it.

**Premise-change invariant:** changed premise → the affected dependent commitment loses
unqualified authority. Sufficient concepts at this level: `STALE` · `REOPEN_REQUIRED` ·
`INVALIDATED`. The final vocabulary and the propagation mechanism are implementation
decisions.

**Audit-status note.** R-5's audit classification is **PROVISIONAL** and is unchanged. The
rule above is a **post-audit design decision** motivated by that evidence, not an
experimentally proven result. Adopting it does not make R-5 evidentially stronger.

---

## 6. Final LLM vs deterministic boundary

| **LLM engineering authorship** | **Deterministic bookkeeping** |
|---|---|
| interpret requirements; preserve or resolve ambiguity explicitly | enumerate domains exhaustively |
| identify physical obligations and required effects | maintain identities and reference integrity |
| propose principle and mechanism alternatives | expand an authored relation over the DOFs and configurations it declares |
| author physical interactions, constraints and load paths | compute graph properties, unit and frame consistency |
| assign engineering dispositions | compute geometry from authored numbers |
| make spatial design decisions | propagate dependency status |
| state what remains open | record provenance and maturity |

**Derived only with sufficient premises.** A semantic engineering conclusion may be produced
deterministically **only if** its complete typed premises exist and the inference is strict.

**Absence of evidence** remains unknown / `UNDISPOSITIONED`. It never becomes a positive
engineering assertion, and no constant may stand in for a missing required value.

---

## 7. Final commitment / gating invariant

- A commitment carries a **class**: `PROVISIONAL` · `COMPARABLE` · `AUTHORITATIVE` ·
  `OVERTURNABLE WITH REASON`.
- A later stage may **refine** within declared constraints, or **supersede with an explicit
  reason**; it may never silently contradict.
- An unresolved item **blocks** exactly when it names a fact class the next consumer's or the
  gate's required minimum marks required. Not every open item blocks.
- The selection gate fires only on equal obligation coverage at equal maturity across all
  retained candidates, with no blocking unresolved item. A tie is an `UnresolvedDecision`,
  never a pick.
- **The gate does not author the verdict on its own preconditions.** All conditions are
  computable from committed state by a reader that is not the gate. A gate firing without an
  externally computed precondition verdict is itself a `FALSE_ACCEPTANCE`.
- `SAFE_REJECTION` and `FALSE_ACCEPTANCE` are reachable outcomes, not decorative statuses.

---

## 8. Final assurance principle

**Independence degrees:** `STRUCTURAL` (reads committed state; never invoked by the producer)
· `PREMISE` (recomputes from premises the producer did not choose) · `EXTERNAL` (evaluates
against an artifact authored independently of the implementation).

**Every check declares a claim class:**

| Claim class | Passing establishes |
|---|---|
| **BOOKKEEPING** | a property the producer guarantees by construction — reported, **never counted as assurance** |
| **FIDELITY** | the artifact faithfully realizes a premise authored elsewhere |
| **PROVENANCE INTEGRITY** | every claim traces to a resolvable premise |
| **ENGINEERING CONSEQUENCE** | two independently authored premises are checked against each other; a mechanically wrong design can fail |

> **Only ENGINEERING CONSEQUENCE may contribute to `ENGINEERING_ESTABLISHED`.**

**Four status constructs, never merged:** EXECUTION · CONTRACT COMPLETENESS · EVIDENCE
MATURITY (per value) · ENGINEERING ESTABLISHMENT (per property).

**Two rules from R-9, kept separate:** *Rule A* — at least one meaningful engineering property
per stage must be independently established before the stage may be described as having
demonstrated engineering assurance. *Rule B* — any property asserted `ENGINEERING_ESTABLISHED`
must carry assurance appropriate to that assertion. **Rule B does not require every property
to be validated**; `NOT_ESTABLISHED`, `NOT_VERIFIED`, `PROVISIONAL` and `EVIDENCE_INCOMPLETE`
are legitimate permanent states.

---

## 9. What remains implementation-level

Not architecture uncertainty. Recorded in the implementation plan:

- field and operation names; the patch API surface
- how dependency propagation is computed (eager on write · lazy on read · closure recompute)
- the final status vocabulary for premise-change consequences
- whether commitment classes are stored per value or derived from the dependency graph
- semantic compression tactics and their ordering under budget pressure
- the storage form of derived state and whether any of it is memoised
- validator implementations, thresholds and predicates
- prompt wording

---

## 10. What remains scientifically unresolved

Freezing the architecture does not answer these, and none of them gates it:

| | Question | Effect |
|---|---|---|
| 1 | **P4B Q4** — why an unguarded direct write existed alongside a defined, validated, never-exercised `EXTEND` | R-5 stays PROVISIONAL; would inform implementation, not architecture |
| 2 | **P4B Q1** — whether the dof-totality check was written against model-authored dispositions | affects interpretation, not the rule |
| 3 | **P4B Q5** — whether the independently authored reference artifacts become the external evaluator | the only route to EXTERNAL independence |
| 4 | **P4B Q8** — whether evidence-route verdicts should be derived from declared claim dependencies rather than authored | affects S02 |
| 5 | **Repeated-member correspondence** — CASE-LIMITED (C-16), one multi-instance case | carried as a provisional sub-case of R-14, never a standalone requirement |
| 6 | **Contract-authoring completeness** — the residual of §4 | mitigated, not eliminated; relocated to where a mechanical test exists |
| 7 | **Whether a cheap model reasons competently once information flow is correct** | the question the whole architecture exists to make answerable; **not yet answered** |

---

## 11. Explicit non-goals

- Not tuned to any benchmark, probe, mechanism family, product noun, or provider.
- Not a claim that the architecture makes correct engineering *likely* — only that failures
  become attributable and that absent evidence stops masquerading as fact.
- Not a design for S05 or later stages.
- Not a validator suite, a prompt set, or an API specification.
- Not a claim that any status in the current system is wrong-but-fixable; several audited
  behaviours are preserved unchanged (proposal §3).
- Does not revise any historical audit conclusion, coverage claim, or evidence grade.

---

## 12. Freeze record

| | |
|---|---|
| **Frozen** | 2026-08-08 |
| **Source proposal** | `S01_S04_ARCHITECTURE_REVISION_PROPOSAL.md`, §§0–29 as of this commit |
| **Falsification record** | `S01_S04_ARCHITECTURE_FALSIFICATION_REVIEW.md` |
| **Audit basis** | `docs/audit/P4B_FINAL_SYNTHESIS.md` — COMPLETE AND FROZEN, unmodified by this freeze |
| **Design decisions post-audit** | **A** two-source consumer sufficiency (§4) · **B** hybrid authority model with controlled mutation and premise-change propagation (§5) |
| **Freeze means** | architecture concepts are fixed enough to plan implementation |
| **Freeze does not mean** | field names, APIs, validators or prompts are final; nor that any open scientific question is closed |
