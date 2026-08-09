# S-3 IMPLEMENTATION EVIDENCE — U-3 / M-3 CONSUMER SUFFICIENCY

Baseline `decd81e`. **First S-3 pass. Status is stated honestly in §14: the core is
implemented and verified; four exit criteria are not yet evidenced.**

## 1. Pre-S3 consumer boundary

| | |
|---|---|
| producer | s01–s04 via `state.apply(patch)` |
| projection | `projection.py::project_for` (strips one family) and `run_window2.S03_OWNED`, a hand-written tuple of nine family names |
| consumer input | `mechanism_projection(state)` → prompt |
| loss path | `S03_OWNED` omitted `Requirement`, `LoadCase`, `Envelope`; `_render(...)[:26000]` sliced positionally with `sort_keys=True`, so `RigidGroup` fell off the end |

## 2. What was built

**`assy_v3/view/consumer_view.py`** — the one semantic boundary.

- **`RequiredMinimum`** of `Requirement` objects, each carrying `source`, `key`,
  `families` and a **trace**. The trace is architecture, not debugging: a required set with
  no reasons is indistinguishable from a whitelist.
- **Source A** — for each permitted output semantic → field → declared reference target,
  spatial frame, or explicit `semantic_dependency`. **Structured metadata only**; `rules:`
  prose is never read.
- **Source B** — premise class → `requires_semantics` → families declaring those roles.
  Reuses the S-2 substrate. No family or stage is named.
- **Instance selection** — eligibility by family is necessary and **not sufficient**. An
  instance is included on POSITIVE evidence only: it was built on the committed candidate,
  or that branch rests on it. *(Superseded in §16 — at the time of writing, reaching no
  candidate was read as common upstream. It is not evidence, and it now admits nothing.)*
  A qualifying instance of a *different* branch is excluded.
- **`committed_branch`** — read from a standing `SelectionDecision` via its declared
  reference, not a case convention.
- **Bounded closure** — a selected value's referents come too, depth- and visited-bounded.
- **Authority** — only `standing()` entities enter; superseded / invalidated / stale never
  appear as unqualified current facts.
- **Sufficiency**, assessed structurally with no model asked:
  `SATISFIED` · `MISSING_UPSTREAM` (nothing upstream established it) ·
  `PROJECTION_FAILURE` (**it exists and we failed to carry it**) · `UNRESOLVED`.
- **Budget** — contributory context reduced first; if the required minimum alone will not
  fit, `BUDGET_INSUFFICIENT` is **recorded**, never sliced.

Derivation for all seven consumers: s01 1 req · s02 14 · s03a 14 · s03b 21 · s04a 11 ·
gate 4 · s04b 14.

## 3. Retirements

| | |
|---|---|
| `S03_OWNED` | **retired**, not renamed. Replaced by contract derivation; a static check rejects its return anywhere in production |
| `mechanism_projection` | now returns `consumer_view_for(stage).payload()` |
| `[:26000]` | **removed**; `_render` is total. The literal appears nowhere in `assy_v3` |
| `projection.py` | **still present**, used only by the S01→S02 path — see §14 |

## 4. Historical replays — passing by the general mechanism

| Replay | Result |
|---|---|
| Requirement/quantity omitted from the s04 consumer | `REQ-0001` reaches s04a **because** the `extent_bounding_quantity` premise requires the `quantity_constraint` role, which `Requirement` declares |
| S04A spatial commitment absent from s04b | `SCL-0001` reaches s04b **because** `Joint.frame_origin` declares a spatial-frame dependency on `ReferenceScale` |

**Neither is a rule naming the entity that used to be lost** — a test asserts the view code
contains no family name.

## 5. Tests

**23 VIEW tests.** Sources derive and stay independently traceable; the consumer has no
parameter through which to narrow; branch isolation; closure; non-standing exclusion;
`MISSING_UPSTREAM` vs `PROJECTION_FAILURE` distinguished on the same state; determinism;
every item traceable; budget reduces then reports; a synthetic premise role and a synthetic
qualifying family both change the view **with no code change**; a disconnected qualifying
instance is **not** pulled in.

## 6. Regression

**69/69** state · **425 meta OK** · **8/8** window · all CI steps OK.

## 7. Deferred and reminders

Legacy producers are **not** repaired inside the view: where a canonical premise has no
migrated producer, the honest result is `UPSTREAM_INSUFFICIENCY`, not a substitute. s04b on
sparse state reports exactly that for `constraint_relation`, `required_distinctness` and
`selection_decision` — all owned by S-4/S-5/S-6.

> **REMINDER — MUST RECONCILE BEFORE S-5/S-6:** the implementation plan claims
> `MobilityExpectation` is a declared S04B premise; the frozen proposal §7.8 does not list
> it. Not reopened here; S-3 consumes the current canonical contract.

## 14. Honest status

**S-3 is NOT COMPLETE.** The core mechanism is implemented, wired and verified, and the
legacy boundary is retired. Four exit criteria lack evidence and I will not claim them:

| # | Criterion | State |
|---|---|---|
| 19 | `projection.py` semantic selection retired | **partial** — `S03_OWNED` is gone and s03/s04 consume ConsumerView, but `project_for` still feeds the S01→S02 path. Two selection systems still coexist |
| 20 | no raw-DesignState prompt path bypasses ConsumerView | **not established** — the s01/s02 path is unmigrated, and no test yet proves the absence of a competing path |
| 17 | `S03_OWNED` determines no consumer's context | **met for s03/s04**, not proven for s01/s02 |
| 28 | exact historical replays resolved | **two of four** replayed; the truncation and continuity-under-live-state replays are not yet driven end to end |

Nothing above is an architecture contradiction — it is remaining implementation. The
mechanism generalises; what is missing is coverage of the S01→S02 consumer and the removal
of the second selection system.

> **S-3 IN PROGRESS — CORE IMPLEMENTED, U-3 NOT YET CLOSED. S-4 has not begun.**


---

## §15 CORE SEMANTICS CORRECTION (pre-migration)

Baseline `3c9a8eb`, reproduced from scratch. Consumer-path migration deliberately **not**
started: the core semantics had to be right first, or the migration would have propagated
them.

## 15.1 Reproduced before editing

| | Reproduction | Result at `3c9a8eb` |
|---|---|---|
| **A** | `s04a.topology_and_interaction` requires three roles; only a `Body` present | **`SATISFIED`** — the family union was non-empty, so "did we select anything?" answered yes while two thirds of the premise was missing |
| **B** | a `Body` with no path to any candidate | **included**, recorded as `"common upstream"` |
| **C** | a field declaring `target: RigidGroup` **and** `semantic_dependency: ReferenceScale` | yielded **only `ReferenceScale`** — one mutable variable, second declaration overwrote the first |

## 15.2 Corrections landed

1. **`Requirement.by_role` + `atoms()`** — a premise naming three roles is three obligations.
2. **Source A is a true union** — a field may yield several dependencies, each with its own trace.
3. **`scope_of` / `relevant_ids`** — relevance is a named classification (`ACTIVE_BRANCH`,
   `COMMON_UPSTREAM`, `OTHER_BRANCH`, `UNSCOPED`) computed from the reference graph
   **independently of what any requirement selected**.
4. **`_assess_atom`** — per-obligation verdicts, worst-wins aggregation. A compound premise
   cannot be `SATISFIED` while a required role is not. `PROJECTION_FAILURE` is decided against
   accumulated state, never against the view — otherwise a selection error would conclude
   upstream absence, the one misdiagnosis this taxonomy exists to prevent.

Closure traces now also carry a relevance reason, so **every** inclusion is explainable.

## 15.3 CONTRACT GAP — why B is landed as PROVISIONAL

Implementing B strictly emptied every s04 view. The cause is not the fix:

> **No topology family — `Body`, `RigidGroup`, `Joint`, `Interface`, `Configuration`,
> `FunctionalRegion`, `AssemblyStep` — can reach `Candidate` through any declared reference.
> Only `LoadPath` can.**

The runner runs s03 once per candidate, but **nothing in state records which candidate a
`Body` embodies**. An orphan and a real topology element are therefore *structurally
identical*, and the contracts cannot tell them apart.

Both available options were wrong: requiring positive evidence empties the views; inferring
"no candidate path ⇒ common" is the unsound step the fix exists to remove. So the
classification is returned as **`COMMON_UPSTREAM` marked `PROVISIONAL`**, with the reason
stated in the trace, and the gap is recorded rather than papered over. **Closing it needs a
structured candidate link on topology — an S-2 contract decision, not a view-layer choice.**

A test pins this: if any topology family later *does* reach `Candidate`, it fails and says to
revisit the relevance rule.

## 15.4 Tests and regression

**31 VIEW tests** (8 new: multi-role coverage, atomic preservation, both Source-A union
shapes, fault-injected `PROJECTION_FAILURE`, absent-upstream, other-branch exclusion,
universal relevance reasons, and the contract-gap pin).

**69/69** state · **433 meta OK** · **8/8** window · CI boundary and gate OK.

Classification: **A** compound-premise sufficiency · **C** Source-A union · **E** sufficiency
classification — all fixed. **B** is **I — contract semantic gap**, recorded, not
casually resolved by reopening S-2.

## 15.5 Still open

Consumer-path migration (**s02**, **s03a**, **s03b**'s raw `demands` channel),
`project_for` retirement, ADR-002/003/004 replays. **S-3 remains IN PROGRESS.**

---

# 16. BRANCH / SCOPE LINEAGE SUBSTRATE

Full record: [S03_BRANCH_SCOPE_LINEAGE_DECISION.md](S03_BRANCH_SCOPE_LINEAGE_DECISION.md).

§15.4's **B — contract semantic gap** is now closed. It was: no s03 topology family reaches
`Candidate` through any declared reference (measured: **2 of 27** families do, `LoadPath` and
`EliminationRecord`), so relevance fell back to *unreachable from every Candidate ⇒
COMMON_UPSTREAM* — which cannot tell an orphan from a shared premise.

**Decision:** minimal hybrid over one graph, no new contract concept. `premise_refs` carries
branch membership downstream (`entity ->* Candidate`); the forward closure of the whole branch
carries common upstream (`Candidate` *and work built on it* `->* entity`); neither ⇒ UNSCOPED,
stated positively. The provisional fallback is removed from the code, and a test asserts the
string is gone.

**The decisive finding:** `run_s03` already received the candidate, passed it to the stage, and
recorded it in the run log — then the authoritative write discarded it. Same shape as the S-1
`_absorb` defect, one level up. `_stamp_branch_premise` now persists it.

**Classified changes:** contract representation gap (`Configuration.bodies_present`) · producer
lineage-population gap (`_stamp_branch_premise`) · view resolution gap (premise edges in the
graph; directional `scope_of`).

**Regression:** 41 VIEW tests (10 new SCOPE methods) · **520 tests OK**, whole suite.

Three fixtures relied on the unsound fallback. Per policy the rule was not weakened: each gained
the lineage its semantics require — s03 topology and the s04a scale were built *after*
commitment to embody it, so withdrawing the candidate must cost their standing (FA-5).

**Residual, recorded not resolved:** `ReferenceScale` is never a reference `target`, so no
spatial value can say which frame *instance* it is expressed in (six families name a frame
*family* only). Fourteen families are never referenced by anyone. Later branch-bearing producers
must stamp the same premise; until migrated their entities classify UNSCOPED — visible exclusion
rather than invisible inclusion.

## 16.1 Lineage population boundary

The candidate premise was stamped by `run_window2._stamp_branch_premise`, so the same
semantic s03 operation given the same candidate produced **different authoritative lineage
depending on which runner called it** — reproduced before editing: direct execution left
BOD/RGP/JNT/CFG UNSCOPED where the Window path made them ACTIVE_BRANCH.

Authorship moved to the producer: `Stage.invocation_premises(inputs)` (default none), carried
onto authored operations by `carry_invocation_premises` in `Stage.run`. Both s03 passes declare
the candidate from their own inputs; `derived_operations` moved out of the runner so the derived
DOF disposition carries the same lineage. Only CREATE is stamped — `_merge_premises` writes on
the entity, so stamping an EXTEND would move a pre-existing requirement onto the branch.
`_stamp_branch_premise` is deleted, and an AST invariant fences the one remaining tool-side
premise site (`_commit_s04`, S-4 work) so a new one cannot appear quietly.

Found in passing and closed minimally: `copy.deepcopy(DesignState)` was broken by the S-1
storage encapsulation, so the Window s03 path could not execute at all.

**538 tests OK.** Full record: §29–45 of
[S03_BRANCH_SCOPE_LINEAGE_DECISION.md](S03_BRANCH_SCOPE_LINEAGE_DECISION.md).

## 16.2 Premise instance selection

The final consumer migration was attempted and **stopped**: migrating s02/s03a off
`project_for` would have dropped whole populations. Post-s02, branch closure from a
Candidate reaches `Obligation -> Requirement -> Actor` and stops; Scenario, LoadCase,
Ambiguity, Freedom, Assumption and UnresolvedDecision were 0-in-scope on every case, and
BM-003 delivered **9 of 19 requirements** while reporting SATISFIED.

Diagnosis: a premise declared WHAT it needed (semantic roles) and never WHICH instances, so
one relevance model — branch lineage — was applied to everything. Engineering demands do not
point at solutions, so design-wide material can carry no branch evidence, and a requirement
no candidate addresses is *unaddressed*, which is a finding rather than a reason to hide it.

Closed as a **contract representation gap**: all 28 premises now declare
`instance_selection` (population + coverage, per role where the roles genuinely differ —
one premise does), with every term defined once in the contract. Sufficiency compares an
independently derived EXPECTED against SELECTED, so 19/9 is a PROJECTION_FAILURE and "all of
nothing" is MISSING_UPSTREAM. Manufacturing `Candidate -> Requirement` edges, and adding
producer premise lineage for visibility, were both rejected: visibility is an
instance-selection concern, not an engineering dependency.

BM-003 s03a now receives **19 of 19**; s02 works before any candidate exists; an unknown
stage id fails closed instead of reporting VIEW_READY with nothing.

**562 tests OK.** Full record:
[S03_PREMISE_INSTANCE_SELECTION_DECISION.md](S03_PREMISE_INSTANCE_SELECTION_DECISION.md).

## 16.3 Still open

Unchanged from §15.5, and deliberately so: consumer-path migration (**s02**, **s03a**,
**s03b**), `project_for` retirement, ADR-002/003/004 replays.

**S-3 INSTANCE-SELECTION SUBSTRATE READY — RESUME FINAL CONSUMER MIGRATION.**
