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

## 16.3 Instance-selection semantic completeness

Two gaps remained after the substrate. **Coverage was carrying existence**: zero standing
Ambiguities and zero standing Requirements both reported MISSING_UPSTREAM, though "every
recorded ambiguity" is fully satisfied by a design that recorded none. `existence`
(MAY_BE_EMPTY / REQUIRED_NONEMPTY) is now declared on all 29 role-rules with a stated why,
and assessment evaluates existence **before** coverage. 19 REQUIRED_NONEMPTY, 10
MAY_BE_EMPTY, decided by one stated rule: required where the premise's own `why` says the
reasoning is impossible without it, may-be-empty where the `what` is a record that may
legitimately be empty.

**Applicability had a seam but nothing to dispatch on**: only `branch` reached a rule, so a
scenario-specific premise could only be written by baking the scenario id into the rule.
`InvocationContext` now carries canonical typed anchors (family read from state, validated
against it), and one generic rule — `MATCHES_INVOCATION_ANCHORS` — compares an instance's
declared references against the invocation's declared anchors, naming neither. Same premise,
same state: `SCN-MAINT` yields `{LC-MAINT, REQ-GLOBAL}`, `SCN-OP` yields `{LC-OP,
REQ-GLOBAL}`. The same rule serves configuration and actor anchors with no new code.

Also corrected: the `57e241f` report's population counts summed to 30 for 28 premises; the
measured split is 13 / 6 / 6 / 2 / 1 mixed. And `INVOCATION_BRANCH` with zero candidates now
resolves to the design — the work has not branched, so a pre-candidate consumer no longer
reports its upstream absent while standing in front of it.

**577 tests OK.** Full record: sections 24-41 of
[S03_PREMISE_INSTANCE_SELECTION_DECISION.md](S03_PREMISE_INSTANCE_SELECTION_DECISION.md).

## 16.4 Superseded by §17

Unchanged from §15.5, and deliberately so: consumer-path migration (**s02**, **s03a**,
**s03b**), `project_for` retirement, ADR-002/003/004 replays.

**S-3 INSTANCE-SELECTION SEMANTICS COMPLETE — RESUME FINAL CONSUMER MIGRATION.**


---

# 17. ROOT-CAUSE CLOSURE AND FINAL CONSUMER MIGRATION

Baseline `e20d84f`.

## 17.1 Why this pass exists

Impl S-3 had expanded four times. Each newly discovered semantic question was pulled into
ConsumerView — family selection, semantic roles, branch scope, design-wide scope, coverage,
existence, applicability, invocation anchors — and each expansion was locally correct and
globally wrong: ConsumerView was becoming a general engine for proving the exact complete
instance set of every possible mechanical-engineering question.

The frozen architecture does not ask Consumer Sufficiency to do that.

## 17.2 Root-cause table

| Issue | Current implementation | The actual semantic question | Owner | S-3 blocker? | Disposition |
|---|---|---|---|---|---|
| Source-A demands a stage's own outputs beforehand | every output reference target is a required pre-stage input | is this referent a pre-existing INPUT or co-produced OUTPUT? | **S-3** | yes | **fixed** |
| Same-patch closure | already worked via `seen`, untested | does a reference to a co-created entity resolve? | **S-3** | no | **kept + tested** |
| `s03` reaching a consumer lookup | runners passed contract strings by hand | ownership identity vs reasoning responsibility | **S-3** | yes | **fixed** |
| Two reference authorities | write boundary read field SPELLING, view read `field_semantics` | what makes a field a reference? | **S-3** | yes | **fixed** |
| s02/s03a/s03b on `project_for` | a second context path | which consumer sees what | **S-3** | yes | **migrated** |
| s03 `[:24000]` | positional slice | may serialization position remove meaning? | **S-3** | yes | **removed** |
| Actor exists, no related FunctionalRegion | not represented | must the RELATION exist? | **S-8** | no | deferred R-K |
| Physical scenario/actor applicability | seam only | which facts physically apply | **S-4** | no | deferred R-A |
| `obligations_created` holds prose | unenforced (`resolvable: false`) | ids or statements? | **S-4** | no | deferred R-B |
| Mobility orchestration / disposition-from-absence | runner-bound | mobility semantics | **S-5** | no | deferred R-C/R-D |
| Multi-anchor same family | one anchor per family | ordered relations | **S-6** | no | deferred R-E |
| S04A→S04B continuity, ReferenceScale instance, `_commit_s04` | transport only | spatial commitment | **S-6** | no | deferred R-F/R-G/R-H |
| Retained / committed truth | selector substrate | selection semantics | **S-7** | no | deferred R-I/R-J |

## 17.3 The S-3 boundary, stated

S-3 answers **"was the consumer reliably given what its responsibility says it needs, with
no silent omission and no competing path?"** It does not answer **"are the engineering
relationships between those facts established?"** — that is producer semantics and S-8
assurance. Every deferred item has an owner, a replay and an exit falsifier in
[AUDIT_DEFECT_REPRODUCTION_REGISTRY.md](AUDIT_DEFECT_REPRODUCTION_REGISTRY.md) §POST-S3.

## 17.4 Source-A availability timing

Reproduced: `derive_source_a("s02", …)` demanded `Obligation`, `Candidate` and `LoadCase`
before s02 ran — the three families s02 creates. A candidate that addresses an obligation
s02 emitted in the same patch was read as "the obligation must be in the view beforehand",
which asks s02 to have already done its own work.

Fixed generically: a referent whose family is in the stage's own `permitted_output_semantics`
is **co-produced**, not a pre-stage input. Derived from the contract; no stage name, no family
pair, no exception. SA-TIME-05 asserts the derivation names neither. SA-TIME-06 invents a
future co-producing pair and it works with no resolver change.

Whether the co-produced referent actually resolves is real and is checked where it belongs:
the write boundary validates the patch that contains both (SA-TIME-03, and 03b proves order
inside the patch does not matter).

## 17.5 Responsibility identity

`Stage.stage_id` is **who owns the write**; `Stage.pass_id` / `responsibility_id()` is **which
engineering responsibility is reasoning**. Both s03 passes author s03 state under s03's
ownership and consume different contracts. `Stage.consumer_view(state, invocation)` resolves
it, so no runner keeps a pass→contract table — which is how `"s03"`, an owner and not a
responsibility, reached a consumer lookup at all. `"s03"` and `"s04"` still fail closed as
responsibilities (S3ROOT-18), and the two ids stay distinct (S3ROOT-18b).

## 17.6 Canonical reference integrity

The write boundary decided what a reference was from the field's **spelling** — anything
ending `_id`/`_ids`/`_refs`, plus a hand-kept list of five names that did not — and from the
**shape of the value**. The consumer boundary read `field_semantics`. Two authorities, and
they did not overlap: of the six references the contract declares `resolvable: true`
(`ConstraintRelation.provider_body`, `provider_site`, `maintaining_interaction`,
`PhysicalEffectObligation.between_roles`, `under_load_case`, `PhysicalInteraction.at_interface`)
the name-shape rule matched **none**. The boundary was enforcing a set of fields the contract
never described while ignoring every field it did.

`Contracts.reference_spec(family, field)` is now the single answer, asked by both boundaries.
Target family and declared cardinality are enforced. **`resolvable` is honoured as the
contract's own word**: 40 of 46 declared references say a referent need not exist, and
enforcing resolution everywhere would be a stricter engineering claim than the architecture
makes (REF-CANON-06).

This immediately surfaced two things worth recording:

1. Test fixtures had been putting the placeholder `"x"` and non-entities into typed reference
   fields, and creating referents after the entities that named them. The name-shape rule
   never looked. Fixtures now build structurally valid state (`ver3/tests/meta/_fixtures.py`).
2. Recorded s02 responses put **prose** in `Candidate.obligations_created`, which the prompt
   and the contract both declare to be obligation **ids**. `resolvable: false` means the
   boundary does not reject it. Registered as **R-B**, owner S-4 — not repaired here, and not
   hidden by weakening the check.

## 17.7 Migration

| consumer | before | after |
|---|---|---|
| S02 | `project_for("s02")` | `consumer_view` under responsibility `s02` |
| S03A | `project_for("s03")` — not even a responsibility | `consumer_view` under `s03a` + explicit candidate |
| S03B | ConsumerView **plus** raw `LoadCase`/`Obligation` demands | `consumer_view` under `s03b` + explicit candidate |
| S04A/S04B | ConsumerView | unchanged, now via `Stage.consumer_view` |

Prompt changes are plumbing only: `{projection}` → `{consumer_view}`; S03B's two sections —
"THE MECHANISM" and "THE LOAD CASES AND OBLIGATIONS" — became the one shape S03A already uses,
"THE CANDIDATE YOU ARE EMBODYING" plus "TYPED INPUT", because both were now fed from one
source and keeping two headers over one source would have been misleading. No reasoning
wording, no hints, no examples were added.

**Candidate identity survives as control, not context**: `InvocationContext(branch=…)` anchors
the branch, `inputs["candidate"]` feeds `invocation_premises`, and both s03 passes read the
same key. An id is not a fact.

`project_for` is **deleted**, along with `ver3/assy_v3/state/projection.py`. Its one
non-semantic rule — INV-002, only s01 may read source text — moved to the consumer boundary,
which is now the only place a consumer's context is built. `run_window.py`,
`run_live_window.py` and `repair_prompt_pairing.py` were migrated too; no production or test
code references it.

## 17.8 Truncation and budget

`s03._render`'s `[:24000]` is gone. ADR-004 is closed **behaviourally**: a payload whose
last-sorting entry falls beyond 26 000 characters is rendered whole, where the old slice
provably lost it. Under a budget it cannot meet, the same view returns `BUDGET_INSUFFICIENT`
with the omission recorded. No renderer in the production package slices (S3ROOT-12).

## 17.9 Production context path

```
   canonical contracts ──► RequiredMinimum ──┐
                                             ├──► ConsumerView ──► render() ──► stage prompt
   accumulated DesignState ──► relevance ────┘        │
     (authority · branch · population ·               └── assessment: expected vs selected
      coverage · existence · applicability)

   invocation identity (candidate / branch / anchors) ──► branch anchoring
                                                     └──► invocation premises (producer lineage)
```

There is no second engineering-context path. The invocation identity carries ids, never facts.

## 17.10 Regression

```
609 tests OK (skipped=1)      meta discover 529 OK
new: test_s3_root_closure.py  32 tests (SA-TIME, REF-CANON, S3ROOT, ADR replays)
static: project_for 0 · positional slices 0 · name-shape reference authority 0
        raw demands 0 · S03_OWNED tables 0 · benchmark/model literals 0
```

## 17.11 What this does NOT claim

Applicability semantics are not complete. Retained and committed branch semantics are not
complete. Mobility is not runner-independent. S04A→S04B spatial continuity is not solved.
Engineering establishment is not proven. Each is registered with an owner, a replay and a
falsifier.

## 17.12 Status

**S-3 COMPLETE — U-3 / M-3 CLOSED.** *(Superseded by §18: this claim was premature; three U-3 clauses were still unmet and are closed there.)*

The consumer context boundary is authoritative, generic, conservative, traceable, and free of
competing projection and truncation paths.

**Impl S-4 has NOT begun.**

---

# 18. FINAL INVOCATION BOUNDARY AND SOURCE-A REPRESENTATION CLOSURE

Baseline `c30bbeb`.

## 18.1 The prior claim was premature

`c30bbeb` said "S-3 COMPLETE — U-3 / M-3 CLOSED". Independent verification against the
frozen U-3 clauses found three unmet requirements. §17 stays as written; this section
records what it got wrong rather than editing it.

## 18.2 Three U-3 defects, reproduced

| U-3 clause | Behaviour at `c30bbeb` |
|---|---|
| plan §8 step 5: "emit CONTEXT_INSUFFICIENT / BUDGET_INSUFFICIENT **and do not call**"; exit criterion: "**No output is produced from a view known to be insufficient**" | `s02` view `UPSTREAM_INSUFFICIENCY` → **provider calls 1, patch produced**. No production code read `view.status` anywhere. |
| plan §8 build step 5: "**Recorded `ConsumerView`** — content, the minimum it was built against, what was compressed and by which rule" | `.payload()` taken, view discarded. `StageOutcome` carried nothing. |
| contract: "`resolvable` says whether an **unresolved value is legal**; the **default is false, so a dangling reference is a defect**" | Implemented **inverted** — resolution enforced only where `resolvable: true`. §17.6's claim that enforcing it everywhere would be "a stricter engineering claim than the architecture makes" was wrong; it was *looser* than the contract. |

## 18.3 The s03a blocker, traced

```
s03a permitted output: Joint
  → Joint.axis_direction   kind: spatial, frame: ReferenceScale
    → ReferenceScale owned by s04a (downstream)
      → s03a Source A requires it, REQUIRED_NONEMPTY
        → s03a ConsumerView can never be VIEW_READY
```

## 18.4 Frozen meaning versus the declaration

The contract contradicted itself. Joint's own rule says **"s03 cannot know where an axis
is: the located FRAME is owned by s04b"**, and `frame_ids` is declared *"this field IS
the frame declaration other spatial values cite"* — while `axis_direction` cited a scale
that does not exist yet. The producer emits a token from a closed set
(`+X/-X/+Y/-Y/+Z/-Z/NONE`), not a located vector.

**Representation correction, no engineering meaning changed:**

- `Joint.axis_direction.frame`: `ReferenceScale` → **`Joint.frame_ids`** — the joint's own
  declaration, which the contract already says is what other spatial values cite.
- `ConstraintRelation.blocked_direction`: `spatial/ReferenceScale` → **`kind: enum`** — the
  same symbolic token, and that family declares no frame of its own.

The located axis and origin remain s04b's, through `frame_origin` and `located_frame`.

## 18.5 Source A derives from AUTHORABLE output semantics

A field the contract says another stage **extends** is that stage's to author, so its
dependencies are that stage's to have. Derived from `extendable_fields`; no stage name,
no field list. Three cases now distinguished:

| case | treatment |
|---|---|
| **pre-existing input** | required in the ConsumerView |
| **same-invocation co-produced** | not required pre-stage; validated at patch closure |
| **later-EXTEND** | not the creating responsibility's requirement at all |

**The rejected rule is absent.** "No upstream producer ⇒ ignore" appears nowhere: a
dependency nothing can author must stay visible (registry R-L). After the correction:

```
s02 / s03a / s03b / s04a  ReferenceScale demanded: False
s04b                      ReferenceScale demanded: True   ← correct; s04b authors
                                                            frame_origin, s04a creates
                                                            the scale upstream
```

## 18.6 `resolvable`, and structure versus existence

Two independent checks:

- **Structure, always.** A typed reference holds an entity id per
  `identity.entity_id.format`. R-20: "a free-string subject is a SCHEMA ERROR, not a
  warning." Prose is rejected whatever the referent's fate.
- **Existence, per field.** `resolvable: false` (the default, 40 of 46 declarations)
  **requires** resolution; the six declaring `true` tolerate an unresolved id.

`resolvable: true` never disables the structural check.

## 18.7 The legacy s02 producer now fails honestly

```
BM-001  s02 view VIEW_READY → provider called → write boundary:
        SCHEMA_FAILURE: REFERENCE_NOT_AN_ID: CND-0001.obligations_created holds
        'radial support and axial retention for the rotating relation'
```

Attributed to the **producer**, not to ConsumerView. No shim, no prompt change, no
fixture regeneration. Registered as **R-B, owner Impl S-4, OPEN — EXPECTED NEXT-STEP
BLOCKER**.

## 18.8 The canonical invocation boundary

`Stage.invoke(provider, state, run_id, inputs, attempt, invocation, budget_chars)`:
build the view → record it → enforce readiness → run only when `VIEW_READY`. Verified:

| case | provider calls | patch | status | view recorded |
|---|---|---|---|---|
| insufficient s02 | **0** | none | `CONSUMER_CONTEXT_INSUFFICIENT` | yes (8 requirements) |
| s04b, no SelectionDecision | **0** | none | `CONSUMER_CONTEXT_INSUFFICIENT` | yes |
| ready s02 (real case) | 1 | — | `SCHEMA_FAILURE` at the write boundary | yes |

`CONSUMER_CONTEXT_INSUFFICIENT` is declared in `STATUS_SEMANTICS.yaml` as explicitly not
a provider condition: "the model was never asked" and "the model was asked and failed"
are different findings, and conflating them destroys the attribution U-3 exists to make.
No SelectionDecision was invented — s04b is refused, and S-7 will make that state real.

All five runners route through it; no runner keeps its own readiness check.

## 18.9 WIP patch disposition

**Reused:** `Stage.invoke`, `CONSUMER_CONTEXT_INSUFFICIENT`, `StageOutcome.consumer_view`,
runner routing, the structural-reference check, the `resolvable` correction.
**Rejected:** nothing was imported that suppresses a dependency for want of a producer,
weakens typed references, or reinterprets prose. **Added here:** the two representation
corrections and the authorable-field Source-A derivation, neither of which was in the WIP.

## 18.10 Fixture repairs

Fixtures had been putting non-entities in typed reference fields and naming referents
nothing created — the old name-shape rule never looked. Repaired to build structurally
valid state (an Actor for the reach results, bodies for the groups, groups for the
joints). The lineage suite drives `run` rather than `invoke`, because it holds the
lineage property; readiness has its own suite, and asserting both in one place would
make a lineage regression indistinguishable from an incomplete fixture.

## 18.11 Regression

```
610 tests OK · meta discover 532 OK · imports OK
static: project_for 0 · name-shape reference authority 0 · raw demands 0 ·
        provider.generate outside the boundary 0 · payload()→run bypass 0 ·
        producer-absence suppression 0
```

## 18.12 Expected live-chain stop

s01 succeeds → s02 view READY → s02 responds → **write boundary rejects the recorded
`obligations_created` prose** → stop, attributed to R-B / Impl S-4. Full-chain success is
Impl S-9's. A truthful blocked pipeline is preferred to silent acceptance.

## 18.13 Status

**S-3 COMPLETE — U-3 / M-3 CLOSED**, with the explicit boundary:

> Consumer context and invocation enforcement are complete. The canonical boundary may
> intentionally stop the legacy pipeline on producer violations owned by later steps.

Not claimed: applicability completeness, retained/committed semantics, mobility runner
independence, S04A→S04B spatial continuity, engineering establishment. Owners and
falsifiers are in the registry. **Impl S-4 has NOT begun.**

---

# 19. LINEAGE-04 CANONICAL INVOCATION EQUIVALENCE AUDIT

Baseline `831c176`. One question: for the same state, candidate, responsibility and
canned responses, does direct canonical invocation produce the same authoritative
state, lineage and scope as window invocation?

## 19.1 Why the historical comparison was invalid

At `831c176` LINEAGE-04 compared `run()` on the direct side against `invoke()` on the
window side. Those execute to **different depths**: the direct side bypassed readiness
and authored `LP-0001`, whose `load_case` reference made `LC-0001` COMMON_UPSTREAM,
while the window side blocked s03b and left the same `LC-0001` UNSCOPED. `SCE-AUTO`
followed it for the same reason.

That is not a runner difference — it is a comparison between an invocation that
happened and one that did not. The relaxation added at `831c176` (compare only jointly
authored state; permit COMMON_UPSTREAM vs UNSCOPED upstream) absorbed the symptom
instead of the cause. **It was not justified**, and it is removed.

## 19.2 The five s03b readiness failures, classified before touching anything

All five were **Source A**, all `INVOCATION_BRANCH / AT_LEAST_ONE / REQUIRED_NONEMPTY`:

| dependency | field is | classification |
|---|---|---|
| `PhysicalInteraction.at_interface -> Interface` | **optional**, one | **B — Source-A false requirement** |
| `ConstraintRelation.provider_site -> Interface` | **optional**, one | **B — Source-A false requirement** |
| `AssemblyStep.activates -> Interface` | required, **many** | **B — Source-A false requirement** |
| `LoadPath.load_case -> LoadCase` | required, one | **F — later/other-owned population question** |
| `PhysicalInteraction.discharges_effect -> PhysicalEffectObligation` | required, one | **F** |

**No Interface was invented** and **no LoadCase was made branch-local.** The first three
were a derivation defect, not fixture incompleteness.

## 19.3 Correction: existence follows the field's own declaration

An **optional** field may simply not be authored, so nothing has to exist for it to
point at. A **many** field is satisfied by the empty list, which this contract states
elsewhere is a VALUE. Only a **required single-valued** reference cannot be authored
without a referent. Source A now derives existence from `required_fields` and
`cardinality` — existing contract vocabulary, no family or stage named. Three of the
five failures were false and are gone.

## 19.4 The remaining two, and a falsified hypothesis

`LoadPath.load_case` and `PhysicalInteraction.discharges_effect` demand that
candidate-independent material be **branch-scoped already** — but its branch-visibility
is created BY the reference s03b is about to author. The responsibility contract calls
load cases "the candidate-independent load cases" and declares that premise DESIGN_WIDE,
which is satisfied; Source A asks for something stricter.

**Hypothesis tested: make Source-A population DESIGN_WIDE. FALSIFIED.** It admitted
another branch's topology through the reference dependency and broke
SELECT-09/10/23 and S3ROOT-16/17. The branch-local reading stands; the change was
reverted and the falsification recorded in the code so it is not retried blind.

No further change was made. Narrowing this correctly needs a discriminator between
branch-bearing and design-wide referent families that the contracts do not currently
declare, and inventing one is the instance-selection redesign this pass forbids.

## 19.5 Equivalence result — invoke vs invoke

```
DIRECT  s03a=SUCCESS  s03b=CONSUMER_CONTEXT_INSUFFICIENT  provider calls=1
WINDOW  s03a=SUCCESS  s03b=CONSUMER_CONTEXT_INSUFFICIENT  provider calls=1

entity sets equal        : True   (none only-direct, none only-window)
exact scope differences  : NONE
premise lineage diffs    : NONE
```

Both paths reach the same depth, author the same entities, carry the same candidate
lineage, and classify every entity identically — COMMON_UPSTREAM and UNSCOPED compared
as the distinct findings they are, not merged into a bucket.

## 19.6 Tests

`LINEAGE-04` is now `invoke` vs `invoke` with exact equality on entity set, premise
lineage and scope, and asserts equal provider call counts first so a depth difference
fails rather than being absorbed. `LINEAGE-04b` pins the exact set of unmet s03b
premises, so the §19.4 finding cannot drift silently. The producer-unit tests
(LINEAGE-01/02) keep using `run()` and say why: they hold the lineage property, not
readiness.

## 19.7 Outcome

**A — test-boundary defect confirmed**, with one recorded derivation correction
(§19.3) and one recorded open finding (§19.4). Canonical invocation is runner
independent, exactly.

## 19.8 Regression

`610 tests · 610 pass · 0 fail · 22 skipped` — the 22 skips are the R-B window replays
owned by Impl S-4, unrelated to this audit.

**S-3 remains CLOSED.** Impl S-4 has not begun.

---

# 20. FINAL SOURCE-A REFERENT-POPULATION CLOSURE

Baseline `1fe7f26`.

## 20.1 What §19 got right, and what it got wrong

§19's equivalence finding was sound: direct and window canonical invocation agree
exactly, and the historical mismatch was a `run()`-vs-`invoke()` depth artifact. But
its closing label, **"S-3 VERIFIED CLOSED", was premature**: it recorded in §19.4 that
s03b could not reach VIEW_READY on any sufficient fixture and then closed anyway.
"Both paths block identically" is not the same as "the consumer can receive what it
needs". That is corrected here rather than rewritten.

## 20.2 The two blockers, and why they were circular

```
LoadPath.load_case               -> LoadCase                  INVOCATION_BRANCH
PhysicalInteraction.discharges_effect -> PhysicalEffectObligation  INVOCATION_BRANCH
```

Both are demands on the design, not products of any alternative. Requiring them to be
**branch-scoped already** is circular: authoring `LoadPath.load_case` is precisely what
makes that load case branch material. s03b could never enter the state it existed to
create.

## 20.3 Rejected: make Source A design-wide

Tried at `1fe7f26` and **falsified** — it admitted another branch's topology through
the reference dependency and broke SELECT-09/10/23 and S3ROOT-16/17. Neither answer is
universal, which is why the population is now declared per field rather than assumed.

## 20.4 Declarative referent population

```yaml
some_reference:
  kind: reference
  target: SomeFamily
  cardinality: one
  resolvable: false
  referent_population: DESIGN_WIDE
```

Semantics: *the population a consumer may resolve this field's pre-existing referent
from.* Selection scope for the referent — not applicability, not ownership, not branch
lineage. It does not touch `cardinality` or `resolvable`. Documented in
`field_semantics_rules`; vocabulary is the existing population vocabulary; an
unrecognised value fails closed (`ValueError` naming the field and the vocabulary).

**Default: `INVOCATION_BRANCH`.** An unclassified reference must not silently widen
what a consumer sees. 30 of the 46 declared references are undeclared and keep it.

## 20.5 Bounded S01–S04 reference audit

16 fields declared `DESIGN_WIDE`, and every one targets material the responsibility
contract already calls a design-wide demand: **Requirement, Scenario, Actor, LoadCase,
PhysicalEffectObligation, Obligation**. Everything else — Body, RigidGroup, Joint,
Interface, Configuration, FunctionalRegion, Candidate, PhysicalInteraction,
AssemblyStep, Feature, Envelope, State, Transition — stays branch-local, asserted by
RP-06. Resolved Source-A populations:

```
s03a  FunctionalRegion.required_by_actors  DESIGN_WIDE
s03b  PhysicalInteraction.groups           INVOCATION_BRANCH
      PhysicalInteraction.at_interface     INVOCATION_BRANCH
      PhysicalInteraction.discharges_effect DESIGN_WIDE
      ConstraintRelation.retained_group    INVOCATION_BRANCH
      LoadPath.load_case                   DESIGN_WIDE
      LoadPath.candidate                   INVOCATION_BRANCH
      AssemblyStep.body / activates        INVOCATION_BRANCH
s04a  Envelope.body                        INVOCATION_BRANCH
      ReachResult.actor                    DESIGN_WIDE
      EliminationRecord.candidate          INVOCATION_BRANCH
```

`derive_source_a` contains no family name, no stage name, and no ownership lookup
(RP-04/05). The 1fe7f26 existence rule is untouched (RP-09), as is co-production
(RP-10); population and existence are independently declared (RP-08).

## 20.6 Visibility is not lineage

| | LC-1 | PEO-1 |
|---|---|---|
| before s03b runs | visible in the view, scope **UNSCOPED** | visible, scope **UNSCOPED** |
| after the relation is authored | **COMMON_UPSTREAM** | **COMMON_UPSTREAM** |

No premise was stamped on either, and `Candidate.addresses_obligations` is unchanged —
they are visible **and still not branch material** until a real relation exists
(S3B-RDY-06/07, POST-LIN-01..05). Candidate B gains nothing from A's relation.

## 20.7 s03b is READY, and runs

```
s03b view                : VIEW_READY, zero unmet obligations
LC-1 / PEO-1 in view     : yes          BOD-B (other branch) in view: no
provider calls           : exactly 1    patch: produced
```

## 20.8 Canonical equivalence, at full depth

```
DIRECT  s03a SUCCESS (1 call) → s03b SUCCESS (1 call) → deterministic derivation
WINDOW  s03a SUCCESS (1 call) → s03b SUCCESS (1 call) → deterministic derivation
entity sets equal: True · scope differences: NONE · lineage differences: NONE
LC-0001 COMMON_UPSTREAM on both sides
```

The deterministic DOF derivation is **included** on both sides rather than excluded, so
the R-C residual (its orchestration is runner-bound, owner S-5) cannot hide a
difference behind it.

## 20.9 One test corrected, not weakened

SELECT-16 asserted a narrow premise excludes a loose requirement from the *whole view*.
Source A now legitimately supplies requirements design-wide, so the assertion was
confounded. It now asserts on the premise under test — its expected and selected sets —
which is what the declaration actually controls, and is a stronger claim.

## 20.10 Regression

`627 run · 627 pass · 0 fail · 22 skipped`. The 22 skips are the R-B window replays,
owned by **Impl S-4**, unchanged and unrelated.

## 20.11 Status

**S-3 COMPLETE — U-3 / M-3 CLOSED.** Consumer context, invocation enforcement, view
recording and reference integrity are complete, and the canonical boundary may still
stop the legacy pipeline on producer violations owned by later steps (R-B).

**Impl S-4 has NOT begun.**
