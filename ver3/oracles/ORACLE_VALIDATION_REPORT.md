# Oracle validation report — Passes 3A–6, then the independent semantic review

> **SUPERSEDED IN PART.** The clean result described below was real but
> insufficient: it proved internal structural consistency, not source fidelity.
> An independent human review then raised 45 semantic findings. See
> [INDEPENDENT_SEMANTIC_REVIEW_REPORT.md](INDEPENDENT_SEMANTIC_REVIEW_REPORT.md)
> for the corrections and the current audit results. This document is preserved
> as the record of the earlier pass, including the 24-finding blind run.
>
> **Status terminology has since changed.** Where this document says
> `SEMANTICALLY_AUDITED`, the current status is `PRE_CAD_SEMANTIC_REVIEWED` —
> semantic review clean, **not** lock-ready and **not** CAD-validated. See
> `PRE_CAD_BASELINE.yaml`.

**Result: 0 findings across 3A, 3B, 3C and 3D over all nine packs**, in canonical
order and under three independent shuffle seeds. No `LOCK.json` was created. No
production pipeline code exists.

Auditor: `ver3/oracle_tools/audit_oracles.py` — read-only, deterministic, never
writes to a pack, never runs as part of any pipeline.

## 1. What the audit passes check

| Pass | Question | Representative checks |
|---|---|---|
| 3A source fidelity | Does every statement resolve to its frozen dossier? | `PACK_FILE_MISSING`, `PACK_HAS_NO_INVARIANTS`, `LOCATOR_DOES_NOT_RESOLVE`, `DIRECT_WITHOUT_RANK1_LOCATOR`, `DIRECT_FROM_LEGACY_SECTION`, `MICRO_DIRECT_NOT_FROM_CAPABILITY`, `DERIVED_WITHOUT_PREMISES`, `POSSIBLY_STRONGER_THAN_SOURCE`, `AMBIGUITY_SILENTLY_RECONCILED` |
| 3B necessity | Is each invariant necessary, and is the set sufficient? | `NECESSITY_COUNTEREXAMPLE`, `REJECTS_ADMISSIBLE_REALIZATION`, `ADMITS_INADMISSIBLE_REALIZATION`, `FEWER_THAN_TWO_ADMISSIBLE` |
| 3C overfitting / ownership | Has a realization, a representation or a tooling limit been smuggled in? | `MECHANISM_NAME_IN_NORMATIVE`, `REPRESENTATION_REQUIREMENT_IN_NORMATIVE`, `TOOLING_LIMITATION_IN_NORMATIVE`, `DIMENSION_LEAK_IN_NORMATIVE`, `PART_COUNT_IN_NORMATIVE`, `REJECTED_BASIS_TYPE`, `NORMATIVE_CONSTRAINS_DECLARED_FREEDOM`, `MICRO_ORACLE_NAMED_FOR_MECHANISM` |
| 3D cross-pack / delta | Do deltas inherit honestly, and are outcomes conditional? | `PARENT_REQUIREMENT_DUPLICATED`, `OVERRIDE_WITHOUT_RANK1_SUPPORT`, `GENERATED_PARENT_COMPARISON`, `FIXED_STAGE11_OUTCOME`, `OUTCOME_RULE_NOT_CONDITIONAL`, `UNRESOLVED_REF_NOT_FOUND` |

3B is the anti-self-confirmation mechanism. Invariants declare `requires_tags`;
packs declare admissible and inadmissible realizations as tag sets; the auditor
evaluates every invariant against every fixture by pure tag algebra. The author's
opinion of an invariant has no role in the verdict.

## 2. Audit history

| Run | Scope | Findings | Report |
|---|---|---|---|
| pre-correction (blind) | BM-001, BM-001-2, BM-001-3 before the v0.2 rewrite | **32 BLOCKING** | reproduced every defect class found in the manual classification report |
| run 1 | all nine packs, first full sweep | **24** (21 BLOCKING, 3 MAJOR) | `_audit/AUDIT-run1.json` |
| run 2 | after arbitration and correction | 1 BLOCKING | `_audit/AUDIT-run2.json` |
| run 3 | after the rename | 0 | `_audit/AUDIT-run3.json` |
| clean audit 1 | canonical order, each pass separately then combined | 0 | `_audit/CLEAN1-{3A,3B,3C,3D,all}.json` |
| clean audit 2 | shuffled pack and statement order, seeds 20260802 / 7 / 991 | 0 | `_audit/CLEAN2-seed*.json` |

Shuffling was verified to be real: with three defects injected into three
different packs, the finding order changes with the seed while the finding set
does not.

## 3. Arbitration record — run 1

Every finding was arbitrated as either an Oracle defect or a tool defect. The
distinction matters: a tool that is wrong and an Oracle that is wrong look
identical in a report, and weakening an Oracle to silence a false positive is the
failure this whole exercise exists to prevent.

### 3.1 Tool defects — the auditor was wrong

**TOOL-003 — `DIRECT_WITHOUT_RANK1_LOCATOR` ×13.**
The check required a `REQ-nnn` locator on every DIRECT statement. Two of the
three source shapes in this corpus are not REQ-numbered: C4-drawer, whose entire
rank-1 source is one free-text command, and every micro-oracle, whose rank-1
source is its declared capability statement. The check reported thirteen
correctly-grounded statements as ungrounded.

Fixed by resolving locators against the frozen dossier's actual section
structure. The fix was made **stricter**, not looser, in two ways:

- `DIRECT_FROM_LEGACY_SECTION` — a DIRECT statement citing S6 (realization
  detail) or S7 (legacy behaviour) is now BLOCKING. Those sections are rank 4–6
  by construction.
- `MICRO_DIRECT_NOT_FROM_CAPABILITY` — a micro-oracle's DIRECT statement must be
  grounded in S1, its capability statement, and nowhere else.

**TOOL-004 — `PART_COUNT_IN_NORMATIVE` ×6.**
The regex fired on "between **the two bodies**". A count is a defect when it
*prescribes* how many elements a design has. A count preceded by a definite
article is anaphoric: it refers to participants the statement has just named, and
expresses the arity of a relation, not a realization decision. "Two rails"
prescribes; "the two bodies" does not. Narrowed accordingly, and the noun list
was extended with `guides, fasteners, springs, bearings`.

**TOOL-005 — `NORMATIVE_CONSTRAINS_DECLARED_FREEDOM` ×3 (MAJOR).**
The freedom-overlap heuristic extracted `['states', 'state']` from the freedom
"which two states, and which is the rest state", treated them as two independent
concepts, and reported overlap wherever both appeared. Two morphological variants
of one word are one concept; a key set built from stem variants co-occurs
trivially. Keys are now deduplicated by stem.

This is the same class as **TOOL-001**, arbitrated earlier: word overlap is not
domain overlap.

### 3.2 Oracle defect — the auditor was right

**ORA-001 — `REPRESENTATION_REQUIREMENT_IN_NORMATIVE` on `NRM-GS-001`.**
The statement read "a line of travel **expressed as** a geometric relation". That
is a requirement on the design record, not on the design. The product-level fact
is that the travel direction is *determinate*; how it is expressed belongs in
`stage_expectations` and in the verification predicate, where it already was.
Restated as "a line of travel whose direction is determinate relative to both
bodies". `NRM-C4-002` already used this pattern and was not flagged.

### 3.3 Naming defect — the auditor was right, and it was mine

**F-3C-001 — `MICRO_ORACLE_NAMED_FOR_MECHANISM`: pack id `hinge-and-stop`.**
"Hinge" is a joint type and "stop" is a feature type. Nothing in the pack requires
either: one admitted realization is a sliding cover, another bounds both extremes
by a pin running out in a slot with no added feature at all.

This is the identical defect that produced the earlier rename of the
rotary-to-linear micro-oracle. The name originated in my own reclassification of
the Oracle set, not in a source. Renamed to **`bounded-two-state-closure`**,
along with its frozen dossier; the dossier's evidence sections S1–S7 are
unchanged, and the rename is recorded in both files.

*This is the one correction that changed an identifier the operator had used in
writing, and it is flagged for review on that basis.*

## 4. Mutation test — is a clean report worth anything?

A clean audit means nothing if the auditor has been relaxed into blindness. Three
checks were loosened in §3.1, so the auditor was tested against thirteen injected
defects on throwaway copies of the tree.

| Injected defect | Caught as |
|---|---|
| DIRECT statement grounded in a legacy section | `DIRECT_FROM_LEGACY_SECTION` + `MICRO_DIRECT_NOT_FROM_CAPABILITY` |
| prescriptive part count ("two rails") | `PART_COUNT_IN_NORMATIVE` |
| **anaphoric count ("the two bodies") — control, must NOT fire** | **(none) ✓** |
| mechanism name in a normative statement | `MECHANISM_NAME_IN_NORMATIVE` |
| admissible fixture stripped of a required tag | `REJECTS_ADMISSIBLE_REALIZATION` |
| inadmissible fixture given every tag | `ADMITS_INADMISSIBLE_REALIZATION` |
| citation of a non-existent REQ | `LOCATOR_DOES_NOT_RESOLVE` |
| citation of a non-existent dossier section | `LOCATOR_DOES_NOT_RESOLVE` |
| fixed Stage-11 outcome | `FIXED_STAGE11_OUTCOME` |
| deleted pack file | `PACK_FILE_MISSING` |
| dimensional leak into a normative statement | `DIMENSION_LEAK_IN_NORMATIVE` |
| `REFERENCE_REALIZATION_DETAIL` basis type | `REJECTED_BASIS_TYPE` |
| representation requirement in a normative statement | `REPRESENTATION_REQUIREMENT_IN_NORMATIVE` |

Twelve of twelve defects caught; the one control correctly stayed silent.

## 5. What the packs decline to claim

The audit is clean. The evidence is not, and the packs say so. These are findings
about the legacy corpus, recorded in `evidence_scope.yaml` and enforced by
invariants:

- **No contact-level evidence exists for any rotary-to-linear conversion anywhere
  in the corpus.** The card review states it: "P-GEAR passes V-A 5/5"; "V-B is
  NAMED-DEFERRED, not silently dropped". Under declared pairs the ratio is exact
  by construction, so agreement between commanded input and observed output
  reports the declaration, not the artifact. Engagement, backlash, friction,
  efficiency and jamming are NOT_VERIFIED for every realization.

- **The slide's off-axis deviation of 0.0 degrees is a structural artifact.**
  Under a declared prismatic pair the model admits no other value. An observable
  that cannot fail cannot pass in any evidential sense.

- **The m0 matched pair — the best evidence in the corpus, genuine V-B contact
  with a one-feature control — does not discriminate.** Every seed-0 criterion
  passes in *both* members. The unbounded control swings to 219.65 degrees and
  still clears the ≥90 degree threshold. The verdicts differ only at 5/5 against
  1/5 seeds. So the pair supports "removing the limit produced seed-level
  instability across a five-seed sweep", and supports no single-run criterion for
  the presence of a bound.

- **The retention force windows are inputs, not measurements.** `[15.0, 60.0] N`
  appears in two different task definitions; that is a fact about how the tasks
  were authored. Citing it as an achieved result asserts as an outcome what was
  supplied as a condition.

Each of these has an invariant. NOT_VERIFIED is never INFEASIBLE.

## 6. Not done, deliberately

- No `LOCK.json`. The workflow stops at READY_FOR_HUMAN_REVIEW.
- No production pipeline code.
- BM-001-2 remains **BLOCKED_BY_SOURCE_AMBIGUITY** (AMB-001-2-01). Its rank-1
  requirement's exact wording is preserved and three candidate readings are
  recorded with none selected.
- AMB-002-01 and AMB-002-02 are carried as required-unresolved decisions. They
  bound the evaluation of specific requirements without blocking their packs.
- AMB-C4-01 was later **reclassified** as `LEGACY-CONFLICT-C4-01` — conflicting
  lower-rank legacy commentary, blocking nothing and requiring no human decision
  (AMD-C4-001, HSD-002). It is no longer a required-unresolved decision.

---

## 7. What happened after this report

The audit above was clean and the pack set was still wrong in several places.
The corrections are recorded in
[INDEPENDENT_SEMANTIC_REVIEW_REPORT.md](INDEPENDENT_SEMANTIC_REVIEW_REPORT.md);
the headline items:

- **BM-002's stated travel and payload requirements had no normative
  representation at all.** A design declaring 45 mm of travel passed every
  invariant in the pack.
- Physical design and verification process shared one all-or-nothing tag set, so
  a buildable latch could be rejected for want of a test.
- Micro-oracles presented their project-authored capability statements as rank-1
  user language.
- Four physical premises were asserted as universal and are false.
- The auditor contained an `and False` sub-expression making one check
  unreachable, and its requirement-coverage check counted a passing mention in a
  derivation premise as coverage.

The auditor gained ten new checks and a mutation suite of 45 cases with 7
controls, and it now documents its own scope: it does not establish physical
truth, and fixture tags are not independent evidence.
