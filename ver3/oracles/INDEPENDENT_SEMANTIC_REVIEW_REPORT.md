# Independent semantic review — corrections, finding by finding

**Branch:** `ver3-oracle-phase1-review`
**Reviewed commit:** `3b64aee601985ba509d2420462af624ed5616cc2`
**Status on completion:** READY_FOR_SECOND_HUMAN_REVIEW — not lock-ready.

The first clean audit proved internal structural consistency and nothing more.
Human review found that several statements were stronger than their sources, that
physical design and verification process shared one all-or-nothing tag set, and
that the auditor contained a dead check. **45 findings** were raised; 44 were
corrected and one was confirmed correct as it stood.

Machine-readable record: `SEMANTIC_CORRECTION_STATE.yaml`.

---

## 0. What this pass changed at the level of the model

Four things were wrong about the Oracle model itself, and every pack inherited
them.

### 0.1 A physical design could be rejected for want of a test (SF-1.1)

Tags like `guidance_observable_can_fail` and `force_window_not_cited_as_result`
sat in the same set as `retention_realized` and `travel_axis_horizontal`. A
realization fixture had to carry all of them or it was inadmissible — so a
perfectly buildable latch was rejected because nobody had yet written a test that
names its disturbance.

Physical and evidence domains are now separate files with separate vocabularies:

| File | Domain |
|---|---|
| `realizations.yaml` | physical designs, `physical_tag_vocabulary` |
| `evidence_cases.yaml` | evidence and verification, `evidence_tag_vocabulary` |
| `negative_cases.yaml` | pipeline and process failures |

A non-`VERIFICATION_MINIMUM` invariant may only require physical tags; a
`VERIFICATION_MINIMUM` may only require evidence tags. Crossing them is
`DESIGN_EVIDENCE_TAG_MIXED`, BLOCKING, with three mutation cases.

### 0.2 Micro-oracles were claiming user authority (SF-1.3)

A micro-oracle has no user. Its capability statement was written by this project
and then frozen; appearing in dossier S1 makes it stable and citable, not rank-1
user language. Ten statements across four packs carried
`DIRECT_USER_REQUIREMENT`.

New basis type **`PROJECT_DEFINED_CAPABILITY`**, whose authority is explicitly
human-reviewable. A product case may not use it and a micro-oracle may not use
`DIRECT_USER_REQUIREMENT`; both directions are BLOCKING.

This is not bookkeeping. Once the distinction was visible, two capability
statements turned out to have absorbed a mechanism — see SF-7.1 and SF-8.1.

### 0.3 "Cannot report PASS" was conflated with "cannot derive" (SF-1.4)

The coarse `blocks:` relation let a missing quantity suppress work that was fully
derivable. Replaced by `kind` plus explicit `block_scopes`. **A quantitative
unknown may never carry `blocks_structural_predicate`.**

Concretely: a missing disturbance magnitude no longer blocks the *existence* of a
load path; a missing effort ceiling no longer blocks *geometric* actuator
reachability; a missing stability criterion no longer blocks derivation of a
contact-derived resting configuration.

Exactly one unresolved in the whole set legitimately blocks a structural
predicate — `UNR-BM-001-2-003` — and it carries a written justification: under
AMB-001-2-01 the predicate's *domain* is undefined, not merely a threshold
missing.

### 0.4 Locator resolution was standing in for entailment (SF-1.5, SF-1.6)

Two review records now exist, and neither is Oracle evidence:

- **`SOURCE_ENTAILMENT_REVIEW.yaml`** — 73 statements. For each: the
  source-derived proposition written *before* comparing it to the statement, the
  entailment class, the counterexample tried, and its outcome. **20 directly
  entailed, 35 physically necessary, 18 conditional, 0 unsupported.**
- **`FIXTURE_PLAUSIBILITY_REVIEW.yaml`** — 41 admissible fixtures. For each: how
  it physically operates, what it assumes, and what would break it. Tags are
  authored by the same hand as the invariants and are not independent evidence,
  so the review may not be represented by copying them.

**All 41 fixtures are `NEEDS_GEOMETRY_VALIDATION`.** No CAD model and no physics
run exists for any of them. Nothing was upgraded to make the record look better.

---

## 1. Statements removed, weakened or made conditional

| Statement | Was | Is | Finding |
|---|---|---|---|
| `NRM-BM-001-003` | closure must vacate the aperture prism | must not obstruct the DECLARED usable access | SF-2.1 |
| `NRM-BM-001-005` | the open pose must be physically determined | conditional on a discrete open pose being declared | SF-2.2 |
| `NRM-BM-001-007` | repeatability declared, nothing marked single-use | a realizable engage/release/engage cycle | SF-2.4 |
| `NRM-BM-001-011` | all named interfaces reacted | conditional on interfaces that carry load | SF-2.3 |
| `NRM-BM-001-2-001` | the OPPOSITE exposed boundary | the exposed exterior boundary | SF-3.1 |
| `NRM-BM-001-3-002` | blocked by the missing stability criterion | structural; stability blocks only PASS and margin claims | SF-4.1 |
| `NRM-BM-002-002` | housing must support the crossing element | crossing realized and non-interfering | SF-5.2 |
| `NRM-BM-002-006` | for each rotating element: radial support | conditional on load components actually carried | SF-5.3 |
| `NRM-BM-002-007` | anti-rotation always required | guidance sufficient for the required behaviour | SF-5.4 |
| `NRM-BM-002-008` | proper subset of a travel corridor | non-intersection at required poses + traversability | SF-5.5 |
| `NRM-BM-002-009` | two distinct terminal determinants | conditional on a terminal being declared | SF-5.6 |
| `NRM-C4-005` | anti-rotation always required | guidance sufficient for the required behaviour | SF-6.1 |
| `NRM-C4-006` | drawer weight **and any contents load** | drawer weight, plus a declared contents load | SF-6.2 |
| `NRM-C4-007` | two distinct extreme determinants | conditional on an end of travel being declared | SF-6.3 |
| `NRM-C4-008` | cabinet must support the crossing | crossing realized and non-interfering | SF-6.4 |
| `NRM-C4-009` | radial + axial reaction on rotating elements | conditional on load components actually carried | SF-6.5 |
| `NRM-GS-002` | ALL non-translational freedoms removed | the freedoms the requirement depends on, rest declared | SF-7.1 |
| `NRM-GS-006` | proper subset of a travel corridor | non-intersection + traversability | SF-7.2 |
| `NRM-RL-001` | a localized engagement between input and output | an uninterrupted chain of localized interactions | SF-8.1 |
| `NRM-RL-002` | the relation is DECLARED | rotation causes translation over the declared range | SF-8.2 |
| `NRM-RL-004` | output rotation always restrained | conditional on the chain producing that moment | SF-8.1 |
| `NRM-RL-005` | conversion generally produces axial force | conditional on load components actually carried | SF-8.1 |
| `NRM-LR-002` | direct capability fragment, geometry on both bodies | derived consequence, identified participating material | SF-9.1 |
| `NRM-HS-003` | ONE constraint persists through the motion | continuous constraint COVERAGE, mode may change | SF-10.1 |
| `NRM-HS-005` | each extreme has its OWN condition | each extreme independently EVALUATED | SF-10.2 |

**Added:** `NRM-BM-002-004` (travel), `NRM-BM-002-005` (payload) — see below.
**Retired:** `UNR-C4-002`, reclassified as `LEGACY-CONFLICT-C4-01`.
**Statement count:** 66 → 73. Ten are `VERIFICATION_MINIMUM`, all with
`enables_claim`.

---

## 2. The most serious finding: BM-002 had lost its two stated quantities

BM-002 is the only case whose source states numbers: *approximately 80–100 mm* of
travel and *approximately 1 kg* of payload. The reviewed pack carried them only
as an unresolved question about the word "approximately". The acceptance model
therefore contained **no travel requirement and no payload requirement at all**.

A design declaring 45 mm of travel passed every invariant in the pack. That
design is now the inadmissible `INA-BM-002-I`, and a design declaring no payload
is `INA-BM-002-J`.

`NRM-BM-002-004` and `NRM-BM-002-005` restore both with the qualifier intact. No
tolerance was invented: values near a band edge yield INDETERMINATE, not PASS and
not FAIL. Payload *capacity* remains NOT_VERIFIED or UNSUPPORTED because
DOS-BM-002 S5 records no strength evidence at any fidelity.

The auditor now enforces `DIRECT_REQUIREMENT_COVERAGE_GAP`, and the mutation
suite reproduces this exact omission.

---

## 3. Premises withdrawn as false

Four physical premises were asserted as universal and are false. Each was
falsified by constructing a realization that satisfies the requirement while
violating the premise, and each such realization is now a fixture:

| Withdrawn premise | Falsified by | Finding |
|---|---|---|
| "A rotary conversion applies a moment about the platform travel direction" | a symmetric four-cable lift (`ADM-BM-002-C`); a centred crank-and-link (`ADM-BM-002-E`, `ADM-C4-D`) | SF-5.4, SF-6.1 |
| "Rotating elements need radial and axial reactions" | a cable drum, which carries no axial load; a rotating nut reacting through its screw (`ADM-BM-002-B`) | SF-5.3, SF-6.5, SF-8.1 |
| "A stated displacement implies physical ends of travel" | `ADM-BM-002-B` and `ADM-C4-C`, which declare none | SF-5.6, SF-6.3 |
| "A guided slider has all non-translational freedoms removed" | a rod in a plain round bore (`ADM-GS-E`) | SF-7.1 |

Two further readings were retired the same way: that a rotary-to-linear
conversion needs *direct* engagement between input and output bodies (falsified
by `ADM-RL-E`, a crank-link-slider — the most common such mechanism there is),
and that a bounded closure needs *one persistent* constraint (falsified by
`ADM-HS-E`, a flexure handing off to a rib).

---

## 4. Fixture decisions

Three admissible fixtures were revised because the physical review found their
narratives did not hold. None was rescued by its tags.

| Fixture | Problem | Resolution |
|---|---|---|
| `ADM-BM-001-3-B` | claimed three contact patches from a single spherical cap, which gives one ideal point contact | three raised lobes with coplanar apexes; coplanarity is now an explicit assumption pending CAD |
| `ADM-BM-001-3-C` | rested on a flat land, so its load-bearing contact was not on the curved back | the land became a non-load-bearing relieved recess; the old design is now `INA-BM-001-3-D` |
| `ADM-BM-002-C` | used *drum stall* as a travel determinant — an overload condition, conflicting with REQ-007 | a deliberate cable-length stop collar |

Six fixtures were added specifically so a future reader can tell whether a
correction has been undone: `ADM-BM-001-D`, `ADM-BM-001-2-D`, `ADM-BM-002-E`,
`ADM-C4-D`, `ADM-GS-E`, `ADM-RL-E`, `ADM-HS-E`, `ADM-HS-F`. Each was rejected by
the reviewed wording and is admitted by the corrected wording. If any of them
starts failing, the correction has regressed.

Every inadmissible fixture was re-checked to confirm it is rejected by the stated
defect and not because it belongs to an unfavoured mechanism family. `INA-C4-E`
and `INA-BM-002-B` in particular are rejected for failing a *required behaviour*,
not for lacking anti-rotation — `ADM-C4-D` and `ADM-BM-002-E` lack it too and are
admitted.

---

## 5. AMB-C4-01 reclassified, not resolved (SF-6.6)

Two legacy statements disagree about whether a toothed transmission is
over-engineered for a drawer: a rank-4 builder docstring says it is, a rank-5
benchmark scoring note says it is not.

Neither is the rank-1 command, which requires rotary-to-linear operation and
never mentions a gear. Two lower-rank commentaries disagreeing about a
realization the source never required **creates no ambiguity in the acceptance
model**, because neither could have bound the family in the first place.

It is now `LEGACY-CONFLICT-C4-01` with `blocks_nothing: true` and
`requires_human_decision: false`, and is cited as support for `FRE-C4-002`: two
competent readers of the same corpus disagreed about a realization, which is
evidence that mechanism choice must stay free. The former `UNR-C4-002` is listed
under `retired_unresolved` with the reason.

---

## 6. Auditor blind spots fixed

| Defect | Fix |
|---|---|
| `UNRESOLVED_REF_NOT_FOUND` contained `and False`, making one branch unreachable, and did not resolve parent ids | rewritten to walk the inheritance chain (SF-11.3) |
| `DIRECT_REQUIREMENT_COVERAGE_GAP` searched the whole pack blob, so a mention in a derivation premise counted as coverage | tightened to structured citations only (SF-11.4) |
| No check that a `VERIFICATION_MINIMUM` names what it enables | `POLICY_FIELD_MISSING` |
| No check that physical and evidence domains stay separate | `DESIGN_EVIDENCE_TAG_MIXED` |
| No check on unresolved block scopes | `UNRESOLVED_BLOCK_SCOPE_INVALID` |
| No check that entailment or plausibility had been reviewed | `SOURCE_ENTAILMENT_REVIEW_REQUIRED`, `FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED`, `STATEMENT_REVIEWED_UNSUPPORTED`, `REJECTED_FIXTURE_STILL_ADMISSIBLE` |
| No check on universal support predicates | `CONDITIONAL_LOAD_DOMAIN_VIOLATION` |
| No check on unconditional terminal obligations | `UNCONDITIONAL_TERMINAL_BOUND` |
| No check on fixed candidate plurality | `FIXED_CANDIDATE_PLURALITY` |
| No check on tier-appropriate basis types | `MICRO_ORACLE_CLAIMS_USER_REQUIREMENT`, `PRODUCT_CASE_CLAIMS_PROJECT_CAPABILITY` |
| Predicate/statement scope mismatch was unchecked | `PREDICATE_STRONGER_THAN_STATEMENT` — flagged mechanically where quantifiers differ, then requiring a **recorded review** rather than pretending the check is decidable |

**SF-11.4 deserves emphasis:** the coverage check was found to be too loose *by
the mutation suite*, not by inspection. The mutation designed to reproduce the
BM-002 omission did not fire, which is exactly what a mutation suite is for.

### The auditor now states its own scope

Its docstring, and every report it emits, says what it can and cannot establish.
It does not claim to prove physical truth. Fixture tags are authored by the same
hand as the invariants and are not independent evidence.

---

## 7. Mutation-test results

`ver3/oracle_tools/mutation_tests.py` — a versioned, re-runnable test definition,
not a scratch script.

```
total 45   defect cases 38   control cases 7   failed 0
```

Every rule has at least one injected defect. Every **relaxed** heuristic has a
control asserting the auditor stays silent:

| Control | Asserts |
|---|---|
| `anaphoric_count` | "the two bodies" is a relation's arity, not a part count |
| `user_stated_quantity` | BM-002's 80–100 mm is user-stated and flagged |
| `child_references_parent_unresolved` | a delta may reference a parent's unresolved id |
| `interpretive_blocks_structural_with_justification` | BM-001-2's genuine structural block is allowed |
| `needs_geometry_validation_is_fine` | pending physical validation is an honest status |
| `load_predicate_with_applies_when` | load-conditional predicates stay silent |
| `source_declared_terminal_states` | a capability whose bounds ARE its definition is exempt |

That last exemption is itself grounded: the pack declares a verbatim fragment and
the auditor verifies it against the frozen dossier text. An ungrounded
declaration is BLOCKING, and `terminal_exemption_fragment_not_in_dossier` proves
it.

---

## 8. Audit results

| Run | Result | Report |
|---|---|---|
| canonical, per pass 3A / 3B / 3C / 3D / 3E | 0 / 0 / 0 / 0 / 0 | `_audit/FINAL-3*.json` |
| canonical, all passes | **0 BLOCKING, 0 MAJOR** | `_audit/FINAL-canonical.json` |
| shuffled, seed 20260802 | 0 BLOCKING, 0 MAJOR | `_audit/FINAL-shuffled-20260802.json` |
| shuffled, seed 4177 | 0 BLOCKING, 0 MAJOR | `_audit/FINAL-shuffled-4177.json` |
| shuffled, seed 90210 | 0 BLOCKING, 0 MAJOR | `_audit/FINAL-shuffled-90210.json` |
| mutation suite | 45/45 | `_audit/MUTATION-final.json` |
| full restart after the last correction | identical | `_audit/RESTART-*.json` |

The pre-correction reports are preserved: `_audit/AUDIT-run1.json` (24 findings),
`_audit/CLEAN1-*.json` and `_audit/CLEAN2-seed*.json` (the earlier clean runs
this review found insufficient), and `_audit/CORR-run1.json` (the first run after
the semantic corrections, 6 findings).

---

## 9. Remaining ambiguities and exceptions

| ID | Pack | Status | Needs a human |
|---|---|---|---|
| `AMB-001-2-01` | BM-001-2 | **OPEN, BLOCKING** | **Yes.** Three readings of "worked from inside the enclosure", none selected. The predicate's domain is undefined. |
| `AMB-002-01` | BM-002 | open, non-blocking | eventually — is the crossing element part of the enclosed mechanism? |
| `AMB-002-02` | BM-002 | open, non-blocking | eventually — where is the compliance edge of "approximately"? |
| `AMB-001-3-01` | BM-001-3 | open, non-blocking | eventually — what does "rests" require of stability? |
| `RDG-BM-001-3-01` | BM-001-3 | reading recorded | **confirm or reject** — this pass adopted a reading of "rests on a curved back" and recorded it in one place so it can be rejected in one place |
| `LEGACY-CONFLICT-C4-01` | C4-drawer | reclassified | **No** — this is the withdrawal of a previously implied human decision |

**BM-001-2 is the only pack that is not lock-ready**, and it is blocked by a
genuine source ambiguity, not by a defect.

---

## 10. What is still pending, stated plainly

**Physical validation by CAD or simulation is pending for every fixture in every
pack.** All 41 admissible fixtures are `NEEDS_GEOMETRY_VALIDATION`. Their
physical operation is described and their assumptions are explicit, but nothing
has been drawn and nothing has been simulated. Several assumptions are load
bearing and openly uncertain — the coplanarity of `ADM-BM-001-3-B`'s three lobes,
the friction margin of `ADM-BM-001-D`, the coverage overlap of `ADM-HS-E`, the
crank throw of `ADM-BM-002-E` against a desktop envelope.

Also still absent, and deliberately: `LOCK.json`, any production pipeline code,
any CAD fixture, and any change to a file outside `ver3/`.

A clean report from the auditor means the pack set is internally consistent and
every semantic question carries a recorded human-readable review. It is not a
proof that the Oracles are right.
