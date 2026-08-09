# PREMISE INSTANCE SELECTION — DESIGN DECISION AND SUBSTRATE

Baseline `475b7ca`. Bounded closure of the contract-representation gap that
blocked the final consumer migration. No architecture selection was reopened.

---

## 1. The question the system could not answer

A premise says **what kind** of information a reasoning step needs. Semantic roles
answer that, and have since S-2. Nothing answered the second half:

> from **what population**, with **what completeness**, under **what
> applicability conditions**?

With no answer declared, the resolver had exactly one relevance model — branch
lineage — and applied it to every premise. That is right for a commitment made on
one alternative. It is wrong for a demand made on the design.

## 2. Blocker, reproduced

Post-s02, identical shape on all three cases (`scratchpad/repro_scope_blocker.py`
at `475b7ca`):

| family | BM-001 | BM-002 | BM-003 |
| --- | --- | --- | --- |
| Scenario | 0/4 | 0/3 | 0/6 |
| LoadCase | 0/5 | 0/4 | 0/5 |
| Ambiguity | 0/6 | 0/7 | 0/10 |
| Freedom | 0/6 | 0/7 | 0/9 |
| Assumption | 0/2 | 0/1 | 0/2 |
| UnresolvedDecision | 0/3 | 0/3 | 0/4 |
| Obligation | 7/13 | 7/14 | 6/17 |
| **Requirement** | 6/10 | 6/11 | **9/19** |

The branch closure from a Candidate reaches `Obligation → Requirement → Actor` and
stops. Everything else has no branch evidence — and it is not supposed to have
any.

## 3. Why Candidate lineage alone cannot be the answer

**Engineering demands do not point at solutions.** A Scenario, a LoadCase, an open
Ambiguity and a Requirement are statements about what must hold; they exist before
and independently of any alternative and are not authored by one. The reference
graph is a *representational dependency* graph. Asking it "which branch does this
requirement belong to?" is a category error: the requirement belongs to the design.

## 4. Unaddressed is not irrelevant

BM-003's ten unreached requirements are the sharp case. A requirement that no
candidate addresses is **unaddressed**, and that is a finding a downstream stage
must be able to see. Hiding it makes the omission invisible at exactly the moment
it matters. Pinned by SELECT-07.

## 5. Rejected: manufacture the missing edges

Two shapes were available and both were rejected.

- **Add `Candidate → Requirement` / `Candidate → LoadCase` references.** These
  would be false. A candidate does not depend on a requirement it fails to
  address, and adding the edge would destroy the very signal in §4.
- **Populate s01/s02 producer premise lineage** so upstream material is reachable.
  Rejected on the same ground: `premise_refs` states a true engineering
  dependency, and adding one so the resolver can reach an entity makes the
  dependency graph a visibility mechanism. Where s01/s02 lineage is independently
  true it should still be added — as an engineering fact, not for visibility.

**Visibility is an instance-selection concern, not a dependency.** SELECT-20
asserts the unaddressed requirements arrive with `_premises == []` and the
candidate's `addresses_obligations` unchanged: they are visible and still
unaddressed.

## 6. All 28 premises, classified

Population and coverage were read from each premise's own frozen `what` prose —
"the FULL requirement set", "every recorded ambiguity", "the candidate-independent
load cases", "the full s03a topology", "every retained candidate's evidence", "the
selected candidate's arrangement". The meaning already existed; only its
machine-readable form was missing.

| stage | premise class | roles | population | coverage |
| --- | --- | --- | --- | --- |
| gate | candidate_spatial_evidence | spatial_commitment, reach_evidence, elimination_evidence | ALL_RETAINED_BRANCHES | ALL_APPLICABLE |
| gate | evidence_route_verdict | candidate | ALL_RETAINED_BRANCHES | ALL_APPLICABLE |
| gate | unresolved_blocking_scope | open_item | DESIGN_WIDE | ALL_APPLICABLE |
| s02 | requirement_set | source_requirement | DESIGN_WIDE | ALL_APPLICABLE |
| s02 | recorded_ambiguity | open_question | DESIGN_WIDE | ALL_APPLICABLE |
| s02 | scenario_boundary | scenario_context | DESIGN_WIDE | ALL_APPLICABLE |
| s02 | actor_and_reach_intent | actor_role | DESIGN_WIDE | ALL_APPLICABLE |
| s03a | physical_effect_obligation | physical_effect_obligation | DESIGN_WIDE | ALL_APPLICABLE |
| s03a | load_case | load_case | DESIGN_WIDE | ALL_APPLICABLE |
| s03a | candidate_principle | candidate | INVOCATION_BRANCH | ALL_APPLICABLE |
| s03a | topology_constraining_quantity | quantity_constraint | DESIGN_WIDE | ALL_APPLICABLE |
| s03b | topology | topology_element, topology_relation | INVOCATION_BRANCH | ALL_APPLICABLE |
| s03b | load_case | load_case | DESIGN_WIDE | ALL_APPLICABLE |
| s03b | physical_effect_obligation | physical_effect_obligation | DESIGN_WIDE | ALL_APPLICABLE |
| s03b | retention_obligation | physical_obligation | DESIGN_WIDE | ALL_APPLICABLE |
| s03b | configuration_basis | configuration_state | INVOCATION_BRANCH | ALL_APPLICABLE |
| s04a | topology_and_interaction | topology_element, topology_relation, physical_interaction | INVOCATION_BRANCH | ALL_APPLICABLE |
| s04a | extent_bounding_quantity | quantity_constraint | DESIGN_WIDE | ALL_APPLICABLE |
| s04a | **reach_requirement** | actor_role / functional_region | **DESIGN_WIDE / INVOCATION_BRANCH** | ALL_APPLICABLE |
| s04a | region_and_envelope_constraint | functional_region, spatial_commitment | INVOCATION_BRANCH | ALL_APPLICABLE |
| s04a | assembly_order_constraint | assembly_order | INVOCATION_BRANCH | ALL_APPLICABLE |
| s04b | prior_spatial_commitment | spatial_commitment | COMMITTED_BRANCH | ALL_APPLICABLE |
| s04b | topology_with_axes | topology_element, topology_relation, kinematic_axis | COMMITTED_BRANCH | ALL_APPLICABLE |
| s04b | required_distinctness | topology_relation | COMMITTED_BRANCH | ALL_APPLICABLE |
| s04b | configuration_basis | configuration_state | COMMITTED_BRANCH | ALL_APPLICABLE |
| s04b | constraint_relation | constraint_relation, physical_interaction | COMMITTED_BRANCH | ALL_APPLICABLE |
| s04b | travel_bounding_quantity | quantity_constraint | DESIGN_WIDE | ALL_APPLICABLE |
| s04b | selection_decision | selection_decision | COMMITTED_BRANCH | ALL_APPLICABLE |

**Representability: 28/28, with no information loss and no over-inclusion**, on
one condition — the model must allow a population **per role**, because exactly
one premise needs it.

## 7. The one premise that forced per-role declaration

`s04a.reach_requirement` needs *the actors* together with *the regions this branch
authored*. Actors are a demand on the design; regions are s03a output for one
candidate. Declaring the premise DESIGN_WIDE would import another branch's
regions; INVOCATION_BRANCH would drop actors an addressed obligation happens not
to involve. The contract therefore allows `by_role` where the roles genuinely
differ, and one declaration where they do not. The atomic-role structure already
existed (`by_role`/`atoms()`); selection attaches to the same unit.

## 8. Selected representation

```yaml
instance_selection:
  population: DESIGN_WIDE
  coverage: ALL_APPLICABLE
```

or, where roles differ:

```yaml
instance_selection:
  by_role:
  - role: actor_role
    population: DESIGN_WIDE
    coverage: ALL_APPLICABLE
    why: an actor is a demand on the design, not a product of any alternative
  - role: functional_region
    population: INVOCATION_BRANCH
    coverage: ALL_APPLICABLE
```

No Python in YAML, no family names, no benchmark ids, no stage conditions. Every
term is defined once in `instance_selection_vocabulary`.

**Alternatives considered.** A single `scope` string was rejected for collapsing
three independent questions into one word. A predicate/query DSL was rejected
under §20: the current corpus needs no Boolean composition, and an unused DSL is a
liability. A per-stage selection table was rejected as the whitelist in a new
shape.

## 9. Population vocabulary

- **DESIGN_WIDE** — every STANDING instance carrying a required role, whatever
  branch it is in and whether or not any alternative refers to it.
- **INVOCATION_BRANCH** — instances in scope for the branch this call is working
  on: the candidate it was told to embody, or the committed one when no target is
  given. Scope is the existing lineage relation, unchanged.
- **COMMITTED_BRANCH** — instances in scope for the branch named by the standing
  `SelectionDecision`. With no selection recorded the population is **empty** and
  that is reported; substituting anything else would let a stage that must realize
  *the chosen* alternative read another one.
- **ALL_RETAINED_BRANCHES** — instances in scope for **any** standing candidate,
  plus what they share. Retained means STANDING.

Each resolves against **its own** branch anchor. A single scope map computed once
per view could answer only one of these questions, which is why `_Scopes` is keyed
by anchor.

## 10. Coverage vocabulary

- **ALL_APPLICABLE** — every applicable member must be selected. A subset does not
  satisfy the premise.
- **AT_LEAST_ONE** — one is enough. This is what a representational dependency
  means: a value that points at something needs the something to exist, not all of
  them. Source A declares it explicitly rather than inheriting a default.

All 28 reasoning premises are ALL_APPLICABLE, because all 28 say "the full",
"every", "each" or "the" in their frozen prose. That is reported rather than
disguised: `AT_LEAST_ONE` is a real, exercised value (Source A uses it, SELECT-16
switches populations declaratively), so the vocabulary is not a single value
wearing two names.

## 11. Applicability — implemented as a seam, not a DSL

All 28 premises are representable with role + population + coverage, so no
applicability rule was needed. Per §7 the seam is real rather than reserved:

- `applicability:` is an optional declared key, defaulting to the named rule
  `ALL_MEMBERS`.
- `APPLICABILITY_RULES` is **one** registry; `_applicable(...)` is **one** dispatch
  point. SELECT-21c asserts both by AST.
- An undeclared rule name **fails closed** (SELECT-21b).

SELECT-21/22 falsify CASE A and CASE B by registering a rule that reads the
canonical declared reference `LoadCase.scenario -> Scenario` and narrows the
expected population to one scenario. Nothing in `select_instances`,
`_assess_atom`, `build_consumer_view` or `ConsumerView` is touched — that is the
property under test. A scenario- or configuration-specific requirement is
therefore a new named rule plus a contract line, not a redesign.

## 12. Sufficiency is now population-aware

`_assess_atom` compares **expected** against **selected**:

```
no applicable instance exists          -> MISSING_UPSTREAM
applicable instances exist, none in view -> PROJECTION_FAILURE
some in view, premise means all of them -> PROJECTION_FAILURE
```

Expected is derived from the contracts, authoritative standing state and the
premise's own declaration — **never** from the view (SELECT-15). Sufficiency that
read its expectation off the selection could only ever agree with itself.

One defect this exposed and closed: "all of nothing" was briefly SATISFIED. An
empty applicable population means the upstream material was never established, and
reporting that as satisfaction is precisely the confusion the taxonomy exists to
prevent.

Every assessment row now carries `population`, `coverage`, `applicability`,
`expected` ids and count, `selected` ids and count — so premise → role → population
→ rule → expected → selected → verdict is one readable chain.

## 13. The 19/9 case

| | before | after |
| --- | --- | --- |
| BM-003 requirements reaching s03a | 9 of 19 | **19 of 19** |
| verdict | SATISFIED | SATISFIED, `expected 19 / selected 19` |
| fault-injected 9 of 19 | SATISFIED | **PROJECTION_FAILURE** |

SELECT-04/05/06.

## 14. No-Candidate consumers

An s02 view before any candidate exists now carries the full design-wide
population — 10, 11 and 19 requirements plus ambiguities, freedoms, actors and
scenarios. No fake candidate is introduced; DESIGN_WIDE simply never consults the
branch graph. SELECT-03.

## 15. Unknown stage fails closed

`derive_required_minimum("s03", …)` raised nothing and returned an empty minimum,
which the view reported as **VIEW_READY with zero entities** — a consumer handed
nothing and told it had everything. It now raises `UnknownConsumer`, naming the
declared stages. Absence of a responsibility declaration cannot mean "nothing is
required". SELECT-13. A premise with no `instance_selection` fails closed the same
way (SELECT-13b).

## 16. Design-wide and branch-local in one view

SELECT-09/10/23: with candidates A and B, both carrying topology, an s03b view
invoked on A contains every requirement (including the unaddressed one) and A's
body, and does **not** contain B's. Two relevance models, one view, chosen by the
premise.

## 17. Future-complexity falsification

| case | result |
| --- | --- |
| A — scenario-specific requirement | Representable via a registered applicability rule; demonstrated end to end (SELECT-21/22) |
| B — configuration-specific constraint | Same seam, same shape; the rule reads a canonical reference |
| C — all retained alternatives | ALL_RETAINED_BRANCHES; both branches' topology present (SELECT-11) |
| D — selected branch only | COMMITTED_BRANCH; empty and reported before selection, B's material after (SELECT-12) |
| E — unaddressed design-wide requirement | Expected and included (SELECT-07) |

## 18. Extension rule

- **New family** → declare its semantic roles in its own definition. Nothing else.
- **New premise need** → declare role + population + coverage (+ applicability) in
  the responsibility contract. Nothing else.
- **New applicability condition** → one named rule in the registry, reading
  canonical structured relations.

SELECT-16 proves the declarative part: the same role with two different populations
produces two different views, with no resolver change, no family edit, no stage
branch. SELECT-02 asserts no selector names a family; SELECT-17/18/19 assert no
benchmark id, no model id, and no creation-order heuristic — creation order was
considered and rejected as not being engineering semantics.

## 19. Files changed

| file | change |
| --- | --- |
| `ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml` | `instance_selection` on all 28 premises; `instance_selection_vocabulary` defining every term |
| `ver3/assy_v3/view/consumer_view.py` | population/coverage/applicability vocabulary; `_Scopes` (per-anchor); `_population_members`; `expected_instances`; `_applicable` + `APPLICABILITY_RULES`; `_selection_of`; population-aware `select_instances` and `_assess_atom`; `UnknownConsumer`; `build_consumer_view(invocation_branch=…)` |
| `ver3/tests/meta/test_premise_instance_selection.py` | SELECT-01..24 (24 tests) |
| `ver3/tests/meta/test_consumer_view.py` | fixture repairs, §20 below |

## 20. Fixture repairs

- Synthetic premises in `TestContractGeneralization` and `TestCoreCorrections` now
  declare `instance_selection`. A premise that says what it needs without saying
  which instances is no longer resolvable — that is the point, and the fixtures
  were relying on the gap.
- Three `_assess(...)` call sites passed a relevance map where the signature now
  takes the branch anchor. Mechanical.

No expected result was changed to chase a green test.

## 21. Regression

```
test_premise_instance_selection    24 tests   OK
full suite (ver3/tests)           562 tests   OK (skipped=1)
CI: meta discover 485 OK · import boundary OK · run_window2 imports OK
```

## 22. Residual limitations

1. **The `ReferenceScale` instance gap is untouched**, as instructed.
2. **`AT_LEAST_ONE` is used only by Source A** among current declarations. Honest
   consequence of the frozen prose, not a modelling shortcut.
3. **No applicability rule ships**. The seam is exercised only by tests. Declaring
   the first real one is a contract decision, deliberately not taken here.
4. **s01/s02 producer premise lineage is still absent.** It should be added where
   independently true — never for visibility (§5).
5. **`_Scopes` computes one map per anchor per view.** Bounded by the number of
   distinct anchors a stage declares (currently ≤ 3).

## 23. Status

**S-3 INSTANCE-SELECTION SUBSTRATE READY — RESUME FINAL CONSUMER MIGRATION.**

Not S-3 COMPLETE. The final consumer migration has **not** resumed: `project_for`
is untouched, S03B's raw demands are untouched, the s03 positional truncation is
untouched, and Impl S-4 has not begun.

---

# SEMANTIC COMPLETENESS CLOSURE

Baseline `57e241f`. Two remaining gaps: coverage was carrying existence, and
applicability had a dispatch seam but no invocation context to dispatch on.

## 24. Correction to the prior report

The population counts in the `57e241f` report were wrong — they summed to 30 for
28 premises. Measured from the contract:

| population | premises |
| --- | --- |
| DESIGN_WIDE | 13 |
| INVOCATION_BRANCH | 6 |
| COMMITTED_BRANCH | 6 |
| ALL_RETAINED_BRANCHES | 2 |
| mixed (`by_role`) | 1 |
| **total** | **28** |

The prior text said 8 INVOCATION_BRANCH. §6's table above was and remains
correct; only the summary arithmetic was wrong. Recorded rather than quietly
adjusted.

## 25. The empty-population defect, reproduced

At `57e241f`, one rule handled every empty population:

```
recorded_ambiguity   0 standing Ambiguity   -> MISSING_UPSTREAM
requirement_set      0 standing Requirement -> MISSING_UPSTREAM
```

The two are **not** the same finding. A request that left nothing ambiguous
recorded no ambiguity, and the premise "every recorded ambiguity" is completely
satisfied by that. A design with no requirement has nothing to derive obligations
from. Both reported identically. Classification **A / C — empty-population
semantic defect, coverage and existence conflated**.

## 26. Existence vocabulary

- **MAY_BE_EMPTY** — an empty applicable population is a valid design state.
  Selecting all of nothing *is* all of it.
- **REQUIRED_NONEMPTY** — the reasoning step cannot proceed without at least one
  applicable instance. Reported as upstream insufficiency **before** coverage is
  considered, because nothing was lost and blaming projection would name the
  wrong party.

Nothing larger was introduced. No premise in the corpus needs a numeric
cardinality beyond zero-versus-nonzero, so no min/max language exists to be
misused.

## 27. How each premise was classified

The rule applied, stated so it can be checked rather than trusted:

> **REQUIRED_NONEMPTY** where the premise's own `why` says the reasoning is
> impossible without it. **MAY_BE_EMPTY** where the `what` is a record of things
> that may simply not have been recorded.

19 REQUIRED_NONEMPTY, 10 MAY_BE_EMPTY (29 role-rules across 28 premises; the
mixed premise declares per role). Every one carries an `existence_why`.

MAY_BE_EMPTY: `unresolved_blocking_scope` (nothing unresolved is the desired
state), `recorded_ambiguity`, `topology_constraining_quantity`,
`retention_obligation`, `reach_requirement` (both roles — a mechanism with no
actor has no reach to evaluate), `region_and_envelope_constraint`,
`required_distinctness`, `constraint_relation`, `travel_bounding_quantity`.

One classification was corrected during the pass: `extent_bounding_quantity` was
first marked MAY_BE_EMPTY and changed to REQUIRED_NONEMPTY, because its own frozen
`why` reads *"a scale-dependent judgement without the scale is not a judgement"* —
which says the judgement cannot be made from an empty set. The rule above decided
it, not the test that caught it.

## 28. Assessment order

```
1. derive the applicable expected population   (contracts + state + declaration)
2. does its cardinality satisfy EXISTENCE?     -> MISSING_UPSTREAM if not
3. does selected-vs-expected satisfy COVERAGE? -> PROJECTION_FAILURE if not
```

The generic `if not expected: missing` rule is gone. Every assessment row carries
`population`, `existence`, `coverage`, `applicability`, expected ids and count,
selected ids and count.

Orthogonality is pinned by SELECT-C04, which exercises all four combinations and
gets four different outcomes.

## 29. Applicability context — audit at `57e241f`

| question | answer |
| --- | --- |
| What structured context reached a rule? | `state`, `contracts`, `families`, `branch` |
| Scenario? | **no** |
| Configuration? | **no** |
| Actor? | **no** |
| Generic, or branch-only? | **branch-only** |
| Two scenario anchors, same state, different populations? | **no** |
| Two configuration anchors? | **no** |

Reproduced concretely: the scenario rule written at `57e241f` had to compare
against the literal `"SCN-MAINT"` inside the rule body. That is a fixture id in
production logic, and it does not generalise to a second scenario at all — the
rule can only ever answer one question. Classification **D / E**.

## 30. Generic invocation context

`InvocationContext(branch, anchors)`. An anchor is a canonical entity id; its
family is read from standing state rather than declared, so no family is
enumerated and a new anchor kind needs no code. `InvocationContext.of(state,
branch, *ids)` validates each id against state — an anchor that names nothing
fails there rather than silently selecting nothing later.

It carries **identity, never facts**. It guides selection; it is not a second
engineering-context channel beside the view.

## 31. One rule, every anchor kind

`MATCHES_INVOCATION_ANCHORS`: an instance applies unless a canonical reference it
declares to an anchored family holds something other than that anchor. An instance
that declares no such reference applies **everywhere** — it was never scoped to one
context, so no anchor can exclude it.

It compares **declared relations** against **declared anchors** and names neither.
SELECT-C11/C13/C22 assert the rule body contains no fixture id, no model name, no
family name and no substring matching.

## 32. Scenario, end to end

Same premise, same state, two invocations:

| invocation anchor | expected population |
| --- | --- |
| `SCN-MAINT` | `LC-MAINT`, `REQ-GLOBAL` |
| `SCN-OP` | `LC-OP`, `REQ-GLOBAL` |

`REQ-GLOBAL` declares no reference to Scenario and survives both. No scenario id
appears in the rule. SELECT-C10.

## 33. Configuration, end to end

A different anchor **kind**, the same rule, no new code:
`CFG-STOWED → {MEX-STOWED}`, `CFG-DEPLOYED → {MEX-DEPLOYED}`. SELECT-C12.

## 34. Actor seam

Proven, not implemented as a production declaration: an Actor anchor is accepted
and typed by `InvocationContext.of` (SELECT-C14), and SELECT-C16 anchors on Actor
through `Obligation.involves_actors` — a canonical relation nothing anticipated —
using the shipped rule with no change to selection or assessment. No speculative
Actor applicability was added to the contract, because no current premise needs
one.

## 35. Coverage AT_LEAST_ONE versus existence REQUIRED_NONEMPTY

They are not the same term twice.

- **Existence** is about upstream, before projection: may the applicable
  population be empty?
- **Coverage** is about projection, given a non-empty population: how much of it
  must arrive?

All four combinations are meaningful and all four are exercised (SELECT-C04). No
change to Source A was needed or made.

## 36. Regressions held

| | result |
| --- | --- |
| 19 of 19 | SATISFIED |
| 19 expected / 9 selected | PROJECTION_FAILURE |
| unaddressed requirement | still expected and included |
| design-wide + branch-local in one view | A's body in, B's out |
| no-candidate s02 | design-wide premises resolve |
| unknown consumer stage | `UnknownConsumer` |
| unknown applicability rule | fails closed, view build raises |
| no fake candidate lineage | `_premises == []` on the unaddressed ones |

## 37. One completeness fix inside the population model

`INVOCATION_BRANCH` with **zero standing candidates** returned nothing, so a
consumer running before candidate generation reported its upstream absent while
standing in front of it. It now resolves to the whole design: positive and
observable — no alternative has been proposed, so the work has not branched and
"the branch this invocation is working on" is the design. This is the degenerate
case of the existing definition, not a new population.

## 38. Files changed

| file | change |
| --- | --- |
| `ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml` | `existence` + `existence_why` on all 29 role-rules; `existence` and anchor vocabulary defined |
| `ver3/assy_v3/view/consumer_view.py` | `MAY_BE_EMPTY`/`REQUIRED_NONEMPTY`; existence assessed before coverage; `InvocationContext`; `MATCHES_INVOCATION_ANCHORS`; invocation threaded through selection and assessment; pre-branch `INVOCATION_BRANCH` |
| `ver3/tests/meta/test_premise_instance_selection.py` | SELECT-C01..C23 (15 new tests, 39 total) |
| `ver3/tests/meta/test_consumer_view.py` | synthetic premises declare `existence` |

## 39. Regression

```
test_premise_instance_selection    39 tests   OK
full suite (ver3/tests)           577 tests   OK (skipped=1)
```

## 40. Residual limitations

1. **Source-A self-reference.** At s02, atoms like
   `Candidate.addresses_obligations -> Obligation` report MISSING_UPSTREAM because
   obligations do not exist yet — and s02 is the stage that creates them. The
   report is accurate about absence; what is questionable is treating a stage's
   own output family as upstream. That is Source-A design and was not reopened.
2. **`AT_LEAST_ONE` is still used only by Source A** among current declarations.
   Now demonstrably distinct from existence (§35), so it is a real term, but the
   reasoning corpus does not use it.
3. **No applicability declaration ships on any of the 28 premises.** The rule and
   the context are production code and are exercised end to end by tests;
   declaring the first real one is a contract decision, deliberately not taken.
4. `ReferenceScale` instance representation unchanged.

## 41. Status

**S-3 INSTANCE-SELECTION SEMANTICS COMPLETE — RESUME FINAL CONSUMER MIGRATION.**

Impl S-3 is not complete. `project_for`, S03B's raw demands, the `[:24000]`
truncation and the final ADR replays are all untouched; Impl S-4 has not begun.
