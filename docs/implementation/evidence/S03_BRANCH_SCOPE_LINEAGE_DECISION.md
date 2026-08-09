# S-3 BRANCH / SCOPE LINEAGE — DESIGN DECISION AND MINIMAL SUBSTRATE

Baseline: `9bc838d` (S-3 core semantics green, branch scope PROVISIONAL).
Scope of this pass: decide how ASSY canonically represents and derives
CANDIDATE-BRANCH / COMMON-UPSTREAM / UNSCOPED lineage, and implement the minimum
substrate that makes the decision true. **Consumer migration (S02/S03A/S03B) has
NOT resumed** — see §26.

---

## 1. The question

At `9bc838d` a consumer view could say *which families* may satisfy an
obligation, and could say whether an instance reached the view. It could not say
**which branch an instance belongs to**. The provisional rule was:

> unreachable from every Candidate ⇒ COMMON_UPSTREAM

That is not an inference. An orphan and a shared premise are both unreachable, so
the rule put unconnected state into every view and could never exclude a losing
branch's topology.

## 2. What was measured before anything was proposed

Nothing below is inferred from field names. Each number is produced by reading
`DESIGN_STATE_CONTRACT.yaml` and the producer source.

| Measurement | Value |
| --- | --- |
| Entity families | 27 |
| Families with **any** declared `kind: reference` field | 18 of 27 |
| Families whose reference closure reaches `Candidate` | **2** — `LoadPath`, `EliminationRecord` |
| Families never named as a reference `target` by anyone | 14 |
| Producers writing `premise_refs` before this pass | **1** — the s04 commit path in `run_window2.py` |
| s03 producers writing `premise_refs` before this pass | **0** |

## 3. Family-by-family closure to `Candidate` by reference alone

```
AssemblyStep  s03  -      Interface        s03  -      RequirementEvaluation s11 -
Body          s03  -      Joint            s03  -      RigidGroup            s03 -
Candidate     s02  (self) LoadCase         s02  -      State                 s04 -
Constraint    s05  -      LoadPath         s03  REACHES Transition           s04 -
ConstraintRel s03  -      Obligation       s02  -      UnresolvedDecision    any -
EliminationRec s04 REACHES Parameter       s05  -      VerificationPlanItem  s08 -
EvidenceItem  s09  -      PhysEffectObl    s02  -
Feature       s05  -      PhysicalInteraction s03 -
FunctionalRegion s03 -    ReachResult      s04  -
                          Realization      s05  -
                          ReferenceScale   s04  -
```

**2 of 27.** Every s03 topology family — `Body`, `RigidGroup`, `Joint`,
`Interface`, `FunctionalRegion`, `AssemblyStep`, `ConstraintRelation`,
`PhysicalInteraction` — is invisible to a reference-only branch test. This is the
whole reason the provisional rule existed, and it is why option B alone cannot
work (§10).

## 4. Audit of substrate 1 — `premise_refs`

`premise_refs` is S-1 machinery: the entities a class-A write *rests on*. FA-5
already gives it teeth — supersede or invalidate a premise and STANDING
dependents become STALE.

Findings:

1. The only writer is the s04 commit path (`ver3/tools/run_window2.py`, the
   commit block around L410–442).
2. **No s03 producer wrote a single `premise_ref`.**
3. `run_s03(case_id, candidate, base_state, provider, trial)` **already receives
   the candidate**, passes it into the stage payload as
   `{"projection": ..., "candidate": candidate}`, and records it in
   `rec["candidate"]` for the run log — and then the authoritative write
   **discards it**.

Item 3 is the decisive finding of this pass. This is the same shape as the S-1
`_absorb` defect one level up: a true engineering fact is produced, used, and
then thrown away before it reaches authoritative state. The lineage was never
missing from the *process*; it was missing from the *record*.

## 5. Audit of substrate 2 — provenance `inputs`

Provenance records how a write was produced (provider, attempt, projection
hash). It is class-D assurance material. Two disqualifying properties:

1. It is *evidential*, not *semantic*. "This call saw candidate X" is a statement
   about an execution, not about what the entity depends on. Withdrawing X must
   change the entity's standing; it must not rewrite history.
2. FA-5 does not traverse it, and making it traverse provenance would make every
   assurance record a load-bearing semantic edge.

Rejected as a lineage substrate. It remains the right place for *what ran*.

## 6. Option A — explicit typed candidate / scope references

Add a declared `candidate` reference (or a `scope` block) to every branch-bearing
family.

- Closes the graph explicitly and is self-documenting.
- **Cost:** a new field on 10+ families, a producer change in each, a contract
  concept (`scope`) that duplicates something the depends-on graph already
  expresses, and a second way to say "this rests on that" alongside
  `premise_refs` — with no rule for which wins when they disagree.
- Duplicates the candidate id across the state for every entity of the branch.

## 7. Option B — `premise_refs` as branch lineage

Treat the existing premise edges as the branch graph.

- No new contract concept; FA-5 semantics are already exactly right.
- **Alone it is insufficient:** premise edges are *downstream* edges (built-on).
  They cannot express COMMON_UPSTREAM, because upstream material by definition
  has no edge pointing at the branch. Used alone it reproduces the provisional
  rule's failure in the other direction: everything shared becomes UNSCOPED.

## 8. Option C — minimal hybrid (**SELECTED**)

Use **both directions of one graph**, and add no new concept:

- **Downstream (branch membership):** `entity ->* Candidate` — the entity was
  built on that candidate. Carried by `premise_refs`, which s03 now writes.
- **Upstream (common material):** `Candidate ->* entity`, seeded from the whole
  branch, not the candidate alone — the candidate *and the work built on it*
  rest on the entity.
- **Neither ⇒ UNSCOPED**, stated positively.

## 9. Decision matrix

| Criterion | A: typed refs | B: premises only | **C: hybrid** |
| --- | --- | --- | --- |
| Expresses branch membership | yes | yes | **yes** |
| Expresses common upstream | no | **no** | **yes** |
| New contract concept | yes (`scope`) | no | **no** |
| Producer changes | 10+ families | 1 site | **1 site** |
| Two ways to say "rests on" | yes | no | **no** |
| FA-5 already correct | no (new rule needed) | yes | **yes** |
| Duplicated candidate ids | one per entity | none | **none** |
| Survives a losing branch | yes | yes | **yes** |

## 10. Why C is not simply B

B and C share a substrate and differ in the *derivation*. B asks one question
(does this reach a candidate). C asks two, and the second one is what makes
upstream material expressible without inferring it from absence.

## 11. The positive definitions

All four are stated as evidence that must be **present**. None is defined by the
absence of a path.

- **ACTIVE_BRANCH** — the entity *is* the candidate under consideration, or a
  premise chain leads from the entity to it. It exists because that candidate was
  chosen.
- **OTHER_BRANCH** — a premise chain leads to one or more candidates, and the
  committed candidate is not among them. It exists because a *different*
  alternative was explored.
- **COMMON_UPSTREAM** — the entity lies in the forward (rests-on) closure of the
  active branch: the candidate, or work built on the candidate, depends on it.
  It is common exactly to the candidates whose branches reach it.
- **UNSCOPED** — neither form of evidence exists. Nothing was built on it and no
  relevant branch rests on it. This is a *conclusion from two failed positive
  tests*, not a definition by absence.

The retired rule is gone from the code, not merely unused:
`test_the_contract_gap_is_now_closed_by_premise_lineage` asserts the string
`PROVISIONAL` no longer appears in the resolver body.

## 12. Why the upstream direction starts from the branch, not the candidate

A first implementation seeded the forward closure at the candidate alone. It
classified `ReferenceScale` UNSCOPED in the s04b replay: the scale is named by
the *joint's* frame, and the candidate has no path to it. But a frame that only
the branch's topology names is still material that branch rests on, and a stage
reasoning about that topology cannot do it without the frame. Seeding from
`{candidate} ∪ {everything built on it}` is what "the branch rests on it"
actually means.

## 13. Changes, classified

Each change is classified by the *kind* of gap it closes. "S-2 gap" is not a
category.

| # | Change | Classification |
| --- | --- | --- |
| 1 | `Configuration.bodies_present` (assurance family) declared as a `reference` to `Body` | **CONTRACT REPRESENTATION GAP** — a real dependency the contract could not express. Changes no stage responsibility and no engineering meaning. |
| 2 | `_stamp_branch_premise` in `run_window2.py`: s03 records the candidate its topology embodies | **PRODUCER LINEAGE-POPULATION GAP** — the fact was known and discarded (§4.3). |
| 3 | `_reference_graph` includes `_premises` edges | **VIEW RESOLUTION GAP** — the depends-on graph was being read as if references were its only edges. |
| 4 | Directional `scope_of` + `_branch_rests_on` + `_closure` | **VIEW RESOLUTION GAP** — the derivation, not the data. |
| 5 | Replay fixture lineage (§18) | **fixture repair**, not a code change. |

No change to provenance was needed: this pass found no **PROVENANCE GAP**.
Nothing here is a later-stage (S-4+) gap.

## 14. The producer change, in full

```python
def _stamp_branch_premise(patch, candidate_id):
    """Persist the candidate the topology embodies. ... recorded as a PREMISE
    because that is what it is: the topology exists because that candidate was
    chosen to embody, and withdrawing the candidate must cost its topology
    unqualified standing. S-1's premise machinery already means exactly that
    (FA-5)..."""
```

Applied to s03 `CREATE` operations only, and never to the candidate itself. It
adds no field, no family, and no contract concept — it writes an existing field
that s03 was leaving empty.

## 15. Anti-whitelist invariant (plan R-2)

The falsifier is: *if premise declarations start naming families directly, the
derivation has degenerated.* The resolver is scanned with docstrings stripped
(`_code_only`), and the assertion now reads: the set of family names appearing in
the resolver must be a subset of `{Candidate, SelectionDecision}` and no larger
than 2.

That narrow exception is deliberate and is stated in the test. `Candidate` and
`SelectionDecision` are typed **identity** semantics — the canonical names for
"design alternative" and "the commitment to one". The resolver needs those two
concepts the way it needs the notion of a reference. Naming them is not the same
as listing which families a consumer may see, which is what R-2 forbids. Pinning
the exception at size 2 means it cannot quietly widen into a whitelist.

## 16. Falsification — graph-closure simulations

Executed directly against the implementation, not asserted.

| Case | Expected | Result |
| --- | --- | --- |
| Pre-selection, BOD-A (premise CND-A) | ACTIVE_BRANCH | ✅ "pre-selection: built on ['CND-A']" |
| Pre-selection, BOD-B (premise CND-B) | ACTIVE_BRANCH | ✅ both branches live before commitment |
| Post-selection on CND-A, BOD-A | ACTIVE_BRANCH | ✅ "built on the committed candidate CND-A" |
| Post-selection on CND-A, BOD-B | OTHER_BRANCH | ✅ "built only on ['CND-B']" |
| BOD-ORPHAN, no premise, no reference | UNSCOPED | ✅ |
| REQ-SHARED, both candidates rest on it | COMMON_UPSTREAM | ✅ |
| REQ-U, unlinked requirement | UNSCOPED | ✅ |
| ReferenceScale named only by branch topology | COMMON_UPSTREAM | ✅ (§12) |

The two that matter most: **BOD-ORPHAN and REQ-SHARED are now distinguishable**,
and they were not at `9bc838d`. That is the defect this pass exists to close.

## 17. Test coverage

`TestBranchScopeLineage` in `ver3/tests/meta/test_consumer_view.py` — 10 test
methods carrying coverage ids SCOPE-01..12, 16..18, 20. They cover: the four
classifications, "no path is not common", common-upstream requiring positive
evidence, one branch's upstream not being common to all, the pre/post-selection
transition, generic inheritance by a new family, the anti-whitelist invariant,
determinism and cycle safety, UNSCOPED never entering a view, and candidate
withdrawal making its topology stale.

SCOPE-13..15 and SCOPE-19 have no dedicated method: they concern consumer-path
behaviour that this pass deliberately did not migrate (§26). They are open, not
silently covered.

## 18. Fixture repairs — §27 policy

Two fixtures relied on *no Candidate path ⇒ common upstream*. Per policy the rule
was not weakened; the fixtures gained the structured lineage their semantics
actually require.

1. **`TestHistoricalReplays._seeded`** — `Body`, `RigidGroup` (s03) and
   `ReferenceScale` (s04a) now record `premise_refs=["CND-0001"]`.
   *Why it is now structurally scoped:* they were built **after** the commitment,
   to embody it. Withdraw CND-0001 and none of them keeps unqualified standing.
   That is FA-5. The old fixture's silence about lineage was a defect in the
   fixture.
2. **`test_VIEW_12_committed_spatial_state_reaches_s04b`** — the joint is created
   with the candidate as a premise, exactly as the migrated producer now writes
   it.
3. **`test_the_contract_gap_is_recorded_not_papered_over`** — this test pinned the
   provisional fallback, which no longer exists. Rewritten as
   `test_the_contract_gap_is_now_closed_by_premise_lineage`: it asserts an orphan
   is UNSCOPED, a premise-linked body is ACTIVE_BRANCH, and `PROVISIONAL` is
   absent from the resolver.

No expected result was altered to chase a green test. In every case the
*classification* the test asserts is unchanged; what changed is that the fixture
now contains the evidence that classification requires.

## 19. Regression

```
ver3/tests/meta/test_consumer_view.py     41 tests   OK
full suite (ver3/tests)                  520 tests   OK (skipped=1)
```

Green throughout: S-1 authority and encapsulation, S-2 contract corpus closure,
projection integrity, meta/schema hygiene, S-2→S-3 interface readiness, consumer
view, state, Window, CI boundary checks.

## 20. What is preserved from `9bc838d`

Atomic multi-role coverage, the Source-A dependency union, `Requirement.by_role`
and `atoms()`, the scope classification infrastructure, accumulated-state-based
`PROJECTION_FAILURE` (computed from `relevant_ids`, never from the view's own
contents), closure traces, and ConsumerView structure. `project_for` is
untouched.

## 21. Residual gap — frame instances are not referenceable

`ReferenceScale` is never the `target` of any declared reference. Six families
carry `kind: spatial` fields naming a frame **family** (`Joint.axis_direction`,
`Joint.frame_origin`, `Transition.path`, `FunctionalRegion.volume`,
`AssemblyStep.insertion_direction`, `ConstraintRelation.blocked_direction`), but
the contract has no way to say **which frame instance** a value is expressed in.

Classification: **CONTRACT REPRESENTATION GAP**. Deliberately **not** closed
here — closing it means deciding whether a spatial value cites a frame instance
directly or through the entity's own `frame_ids` declaration, which is a spatial
representation decision, not a lineage decision. It is recorded, not papered
over. In the interim, a frame reaches a consumer through the branch-rests-on
direction (§12), which is correct but coarser than a declared citation.

## 22. Residual gap — 14 families are never referenced by anyone

`Constraint`, `ConstraintRelation`, `EliminationRecord`, `EvidenceItem`, `Joint`,
`LoadPath`, `Parameter`, `ReachResult`, `Realization`, `ReferenceScale`,
`RequirementEvaluation`, `Transition`, `UnresolvedDecision`,
`VerificationPlanItem`. Most are terminal by nature (records and evaluations);
some are not. Recorded for the S-4 contract pass.

## 23. Residual gap — premise lineage depends on the producer being migrated

The substrate is only as good as its population. s03 is migrated (§14). Later
stages that create branch-bearing entities must stamp the same premise. Until
each is migrated, its entities classify UNSCOPED rather than being silently
admitted — the failure mode is now *visible exclusion*, not *invisible
inclusion*, which is the correct direction for a defect to fail.

## 24. Bounds

`_closure` is cycle-safe (visited set) and depth-bounded (`limit=64`). A
reference cycle terminates; a pathological graph cannot run away.

## 25. Frozen architecture

No frozen architectural decision was contradicted by this pass. No STOP-on-J
condition arose. FA-5 is used exactly as written; the hybrid authority model,
the Source A / Source B independence, and eligibility ≠ relevance are all
unchanged.

## 26. What this pass did NOT do

- **S02/S03A/S03B consumer migration has NOT resumed.** No consumer path was
  switched to `build_consumer_view`.
- `project_for` was not retired.
- S-4 was not begun.
- No prompt, stage reasoning, mobility runtime, S04 runtime, fixture regeneration,
  benchmark rerun, or model call.

## 27. Files changed

| File | Change |
| --- | --- |
| `ver3/contracts/DESIGN_STATE_CONTRACT.yaml` | `Configuration.bodies_present` declared as a reference (assurance families block) |
| `ver3/assy_v3/view/consumer_view.py` | premise edges in the graph; `_closure`, `_reachable`, `_branch_rests_on`; directional `scope_of`; provisional fallback removed |
| `ver3/tools/run_window2.py` | `_stamp_branch_premise` on the two s03 write sites |
| `ver3/tests/meta/test_consumer_view.py` | `TestBranchScopeLineage` (SCOPE-01..20); `add(prem=...)`; three fixture repairs |

## 28. Status

**S-3 BRANCH/SCOPE SUBSTRATE READY — RESUME CONSUMER MIGRATION.**

Not "S-3 COMPLETE". The substrate is decided, implemented, populated by s03, and
falsified. What remains for S-3 is the consumer migration this pass deliberately
left untouched.
