# S01–S04 ARCHITECTURE — FALSIFICATION REVIEW

Axis A: **GENERATED EVIDENCE**. Axis B: **REVIEW RECORD**.

A falsification pass over `S01_S04_ARCHITECTURE_REVISION_PROPOSAL.md` and the pushed audit
set, at commit `dc65de9`. **This is not a reset.** Four high-risk decisions were attacked;
the proposal was amended only where the frozen audit evidence required it.

No pipeline code, contract, prompt, validator, runner, fixture, benchmark input, Oracle or
CAD reference was modified. No experiment was run.

---

## §1 ISSUES TESTED

| # | Issue | Kind |
|---|---|---|
| I-1 | BM fixture provenance overstated in the evaluation-philosophy document | factual |
| I-2 | Three different PNG counts used with one word | factual |
| I-3 | Working records readable as current coverage authority | documentation |
| I-4 | **Consumer sufficiency: who establishes that the declaration is complete?** | architecture, load-bearing |
| I-5 | Non-degeneracy rejected too broadly, contradicting R-3 | architecture |
| I-6 | R-9 read as "every property independently validated" | architecture |
| I-7 | R-5 substrate presented as frozen | architecture |
| I-8 | Does the new architecture recreate self-fulfilling assurance? | architecture |
| I-9 | Did any withdrawn audit claim survive into the proposal? | consistency |

---

## §2 EVIDENCE

| # | Anchors |
|---|---|
| I-1 | `P4A_COMPLETE.md:76-77`, `:654-672`, `:952`; `P5_COMPLETE.md:274-277`, `:475-476` (the `pairing_history` sentence written verbatim by `tools/repair_prompt_pairing.py:165-175`) |
| I-2 | `AUDIT_SCOPE.md` §3E (170-image universe; ~97 planned); `P3_COMPLETE.md:19,22,1041` (99 assigned, 99 inspected) |
| I-3 | `P1_RUNNING_EVIDENCE_LOG.md:6` ("2 of 35"); `S01_S04_AUDIT_READ_INVENTORY.md` (225 `NOT READ` rows); `AUDIT_EVIDENCE_LOG.md` closing line ("Package 1 continues") |
| I-4 | `P4B` C-05, C-12, R-1; the `S03_OWNED` whitelist chain in `P5_COMPLETE.md` §20 |
| I-5 | `P4B` C-14 (5/6), C-15, R-3; proposal §12, §17.2, §22, §23 |
| I-6 | `P4B` R-9 as written ("at least one engineering property per stage"); C-21 |
| I-7 | `P4B_FINAL_SYNTHESIS.md` §21 (R-5 = PROVISIONAL; unresolved question 4) |
| I-8 | `P6_COMPLETE.md` §7 (self-fulfilling checks); `P4B` C-11, C-18 |
| I-9 | `P4B` §1 items 1–2, §8.2, §11; `P5` §14; `P4A` §H |

---

## §3 SURVIVED UNCHANGED

Attacked and not weakened:

- accumulated persistent DesignState as the substrate
- semantic consumer sufficiency in place of family whitelists *(the mechanism survived; §7.2 was added beneath it — see §4)*
- no silent positional slicing; overflow as a recorded status
- semantic compression applied only after sufficiency is established
- mobility **domain vs disposition** split
- `UNDISPOSITIONED` as a first-class value for missing engineering evidence
- `PhysicalEffectObligation` → `PhysicalInteraction` progression, and the rejection of reviving body-level hypotheses at S02
- addressable `ConstraintRelation` with provider, site and defeat condition
- typed reaction-site semantics with external/internal from the scenario boundary
- S04·A → S04·B refinement rather than fresh re-synthesis
- deterministic derivation only from sufficient typed premises
- unresolved evidence connected to commitment
- assurance independent of the producer
- execution / contract-completeness / evidence-maturity / engineering-establishment kept distinct
- benchmark-independence and model-independence throughout

---

## §4 REVISED

### 4.1 Documentation

| File | Correction |
|---|---|
| `BENCHMARK_PROBE_EVALUATION_PHILOSOPHY.md` | BM upstream re-labelled **"replayed repository fixtures; authorship/provenance UNKNOWN from available metadata"**; PRB re-labelled **"repository-authored, explicit `authored_by: agent-in-repository`"**. "BM and PRB are structurally identical" narrowed to *"their Window-2 execution topology is structurally analogous"*, with provenance explicitly excluded. A provenance note records that the shared `pairing_history` sentence is tool-written and establishes nothing about authorship |
| `AUDIT_SCOPE.md` | Four terms separated — candidate universe **170**, planned estimate **≈97**, final assigned **99**, inspected **99/99**. Planned estimates retained as PLANNED ESTIMATE, never rewritten. All corpus totals moved to the same definition |
| `P1_RUNNING_EVIDENCE_LOG.md`, `S01_S04_AUDIT_READ_INVENTORY.md`, `AUDIT_EVIDENCE_LOG.md` | **SUPERSEDED HISTORICAL AUDIT RECORD** banner. Content unedited; chronology preserved |

`AUDIT_EVIDENCE_LOG.md` was added to the banner set on inspection: it stops inside Package 1
and its closing line reads *"Package 1 continues"*.

### 4.2 I-4 — consumer sufficiency declaration completeness *(the load-bearing amendment)*

**The attack was sound.** As drafted, a stage could under-declare its needs and a checker
could then prove the view "complete" against that understatement — the whitelist omission
one level up.

**Amendment (proposal §7.2–§7.2.4).** The required set is **derived, not declared**:

1. Responsibility is owned by the **stage responsibility contract**, not by the stage.
2. Every output field declares its **semantic dependencies** — what it is expressed relative
   to, what it must be consistent with, what it references. The **derived minimum input set**
   is the union of those dependencies over the outputs the stage may create. A field whose
   contract says it is expressed in the arrangement's frame thereby *makes the arrangement a
   required input*; nobody has to remember to ask.
3. A stage may add **contributory** needs. It may never declare fewer than the derived
   minimum, and it may not self-validate its own sufficiency.
4. **An assurance check reading only the declaration and the view is structurally incapable
   of detecting an omitted need.** It must read the output contract. Stated as a prohibition.
5. Omitted need vs unnecessary fact is decided by derivation (the guarantee), with two
   detectors: contradiction against accumulated state, and the producer's own unresolved
   layer used as a sufficiency sensor.
6. Six design prohibitions record what would make sufficiency self-fulfilling.

**Why the regress terminates (§7.2.3).** A consumer need list is global and has *no*
completeness test — a missing entry is indistinguishable from a fact that was not needed. A
per-field dependency is local and has a **mechanical** one: every spatial value declares its
frame, every reference declares its target family, and a field that declares nothing has no
defined meaning, which is itself a finding. The residual risk is not eliminated; it is moved
somewhere it can be tested. That is the entire claim.

**Operative definition adopted:** consumer-view completeness ≠ *"all facts listed in the
declaration happened to be present"*.

### 4.3 I-5 — conditional non-degeneracy *(proposal §25.1)*

§25 rejected "a validator for zero-length links" without qualification, contradicting §12,
§17.2, §22 R-3 and §23. Three cases now separated:

| | Standing |
|---|---|
| a check for one named joint pair from one case | **rejected** — encodes one mechanism |
| *"all joint pairs must have nonzero separation"* | **rejected** — false as a mechanical statement |
| *"where upstream topology establishes that two kinematic sites must be distinct for a mechanical relationship to exist, spatial realization must establish that the required distinctness is preserved"* | **retained and required** — mechanism-independent, fires only on a declared premise, and is already R-3 |

No implementation algorithm is prescribed.

### 4.4 I-6 — R-9 split into two rules *(proposal §17.0)*

- **Rule A — maturity minimum:** at least one meaningful engineering property per stage must
  be independently established before the stage may be described as having demonstrated
  engineering assurance. This is R-9 as the audit states it, and the audit found zero.
- **Rule B — claim semantics:** any property asserted `ENGINEERING_ESTABLISHED` must carry
  assurance appropriate to that assertion.

**Rule B does not require every stored property to be validated.** `NOT_ESTABLISHED`,
`NOT_VERIFIED`, `PROVISIONAL` and `EVIDENCE_INCOMPLETE` are legitimate, permanently
occupiable states. What is prohibited is **inheritance** — acquiring establishment from a
checked sibling, from stage completion, from patch validation, or from an aggregate badge.
The §22 R-9 row and §18 rules were corrected to match; the four status constructs remain
distinct and non-substitutable.

### 4.5 I-7 — R-5 represented as provisional *(proposal §13.0, §26.1)*

Separated:

- **capability need** — *later-stage reasoning must not silently invalidate the premises on
  which an authoritative commitment depends* → **evidence-supported**;
- **mechanism** — commitment classes + supersede-with-reason + invalidation cone + STALE
  selection → **PREFERRED CANDIDATE PENDING R-5 CLOSURE**.

M-4 is labelled PROVISIONAL in the migration table and in §22. Three open alternatives are
recorded in §26.1 (declarative classes / structurally enforced patch-only mutation /
append-only state with derived commitments). **What must close it:** P4B question 4 — why an
unguarded direct write exists alongside a defined, validated, never-exercised `EXTEND`. Not
resolved by assumption.

### 4.6 I-8 — the gate was about to repeat the P6 mistake *(proposal §16.3, §27.2)*

As drafted, the selection gate checked its own preconditions and recorded that they were
met — *producer creates X → evaluator confirms X* exactly. **Corrected:** the gate may not
author the verdict on its own preconditions; all three are computable from committed state
by a reader that is not the gate. A gate firing without an externally computed precondition
verdict is itself a `FALSE_ACCEPTANCE`.

**And a general amendment (§27):** most checks this architecture introduces establish
*fidelity* or *provenance integrity*, not engineering correctness. Every check must now
declare its **claim class** — BOOKKEEPING / FIDELITY / PROVENANCE INTEGRITY / ENGINEERING
CONSEQUENCE — and **only ENGINEERING CONSEQUENCE may contribute to
`ENGINEERING_ESTABLISHED`**. Mobility *domain totality* is explicitly reclassified as
BOOKKEEPING; the real mobility assurance is cross-premise consistency against load cases and
actuation, which two different producers authored.

### 4.7 I-9 — one withdrawn claim had survived

Seven of eight were absent. The eighth — *zero-length geometry can only be checked with
mechanism-specific logic* — survived in §25 and is corrected by §4.3 above. Recorded in
proposal §28.

---

## §5 STILL PROVISIONAL

| Item | Why | What would close it |
|---|---|---|
| **R-5 and migration unit M-4** | the audit marks R-5 PROVISIONAL; three mechanisms remain viable | P4B unresolved question 4 |
| **M-5 selection gate**, insofar as it depends on invalidation | inherits from M-4 | as above |
| **Repeated-member correspondence** | CASE-LIMITED (C-16) — one multi-instance case in the corpus | a second multi-instance case; carried as a sub-case of R-14, never a standalone requirement |
| **Source of external assurance artifacts** | independently authored artifacts exist and are not evaluated against | P4B question 5 |
| **Evidence-route verdicts derived vs authored** | the knowledge layer already contains the mapping and does not use it | P4B question 8 |
| **Dependency-declaration completeness** | the residual of §7.2.3 — real, but relocated to where a mechanical test exists | adopting the per-field declaration rule and its structural completeness check |

---

## §6 REJECTED INTERPRETATIONS

| Interpretation | Why rejected |
|---|---|
| "pass the whole DesignState" as the sufficiency answer | cognitive load grows with accumulated state, and it still cannot distinguish *absent upstream* from *not projected* |
| "the stage knows what it needs, let it declare it" | this is the failure under review, restated |
| "consumer sufficiency proves the reasoning was adequate" | it is a **precondition**; its value is attributive, not evaluative (§27.1) |
| "reject all non-degeneracy checking as mechanism-specific" | conflates a case-specific patch with a conditional general invariant, and contradicts R-3 |
| "every property must be independently validated" | overstates R-9 and would make `NOT_ESTABLISHED` look like failure |
| "R-5's mechanism is settled because it is written out in detail" | specificity is what makes a candidate criticisable, not what makes it correct |
| "domain totality demonstrates mobility assurance" | totality is guaranteed by the enumerating code — BOOKKEEPING, and the audited defect verbatim |
| "the shared `pairing_history` sentence indicates common fixture authorship" | written verbatim by `repair_prompt_pairing.py`; indicates a tool ran |
| "~97 and 99 are the same number loosely stated" | different constructs — planned estimate vs final assigned set; conflating them is how coverage claims drift |

---

## §7 ARCHITECTURE READINESS STATUS

**(B) READY EXCEPT FOR THE EXPLICITLY PROVISIONAL R-5 SUBSTRATE.**

Not **(C)**, because the load-bearing question — consumer-sufficiency declaration
completeness — is closed structurally rather than by convention: the required set is derived
from the semantic dependencies of the outputs a stage may create, a stage may widen but never
narrow it, sufficiency assurance must read the output contract rather than the declaration
alone, and the regress terminates at a primitive that has a mechanical completeness test.

Not **(A)**, because R-5 is PROVISIONAL in the frozen audit and §13.0, §5.3, §16 and M-4 all
rest on it. The capability need is supported; the mechanism is one of three candidates, and
P4B question 4 selects between them.

**Ready for implementation planning:** M-1, M-2, M-3, M-6, M-7, M-8 *(after M-1)*, M-9.
**Hold:** M-4, and M-5 where it depends on invalidation.

**Three preconditions before an implementation plan is written**, none of them code work:
P4B question 4 is answered; the §27 claim-class rule is adopted so no structural check is
counted as engineering assurance; and §27.2 holds — the gate does not author the verdict on
its own preconditions.

**Implementation planning is not begun by this document.**
