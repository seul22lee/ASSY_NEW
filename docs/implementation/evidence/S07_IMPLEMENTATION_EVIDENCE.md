# IMPL S-7 / U-8 — FEASIBILITY AND SELECTION

Baseline `9f98cbc`. S-3, S-4, S-5 and S-6 are closed and are not reopened.

This step is planned in six substeps (§20). **This document records S7-A only.**

---

## S7-A — AUTHORITY / CONTRACT FREEZE

### A.1 The collision, found before editing

The brief names the two responsibilities "Stage 7" and "Stage 8". **Pipeline
stages `s07` and `s08` already exist and mean other things** — `s07` is solid
generation ("does the declared program, with the solved values, produce valid
solids?"), `s08` is negative controls and the verification plan. Squatting on
those numbers would have renumbered the pipeline, which §Root forbids.

They are **responsibilities**, as `gate` already was: non-numbered, declared in
`STAGE_RESPONSIBILITY_CONTRACT`, and now also in the ownership matrix. Named
`feasibility` and `selection`.

### A.2 What was actually wrong with `gate`

| | |
|---|---|
| it asked **two questions and answered them in one act** | "can this candidate work" and "which candidate is wanted". Nothing in that shape could say that a four-bar which works is not less feasible than a hinge which works |
| it had **no entry in the ownership matrix** | so its one authoritative output was attributed to the nearest stage. `SelectionDecision.owned_by: s04` — the stage that sizes bodies and sweeps them owned the decision about which candidate wins |
| it sat **between s04a and s04b** | a position S-6 already found to be the claim that made s04b unreachable |

### A.3 Authority decisions

**Two responsibilities.**

`feasibility` — candidate-local, preference-blind. Outputs
`MechanicalFeasibilityAssessment`, `HardRequirementCompliance`,
`UnresolvedDecision`. Explicitly prohibited from comparing candidates, from
preferring a simpler mechanism, from receiving any preference, from authoring a
decision, and from turning missing evidence into feasibility.

`selection` — outputs `SelectionProfile`, `CandidateComparison`,
`SelectionAdvisory`, `SelectionConcern`, `HumanDecisionInput`,
`SelectionDecision`, `UnresolvedDecision`. **The only responsibility in the
pipeline that declares the `selection_preference` role.**

**Preference isolation is an input-boundary property.** Nothing before
`selection` declares the role, so the ConsumerView derivation cannot select a
profile — there is no instruction to ignore and therefore nothing to ignore.

**Hard requirement ≠ preference, and existence ≠ evaluability.**
`DesignConstraint` is s01-owned and deterministically ingested (a profile that
already says `PLASTIC_ONLY` is a fact, not something to reinterpret).
`HardRequirementCompliance` is three-state, and the rule is written where the
ingester will read it: absence of a material assignment is `NOT_YET_EVALUABLE`,
never satisfied and never violated.

**Feasibility ≠ compliance.** Two families, because a violated requirement is not
a broken mechanism.

**Premises vs considered.** A decision's premises are the assessments, the
compliance results, the comparison and the profile; advisories are `considered`.
Rewording a model's opinion invalidates nothing, because the wording was never
the ground of the choice.

**`selection_gate_check` is not the owner of selection.** It validates a decision
that already exists and writes nothing — asserted by reading its source for
`Op("`, `.apply(`, `StagePatch(`. Relocating checks is **S-8 / U-9**'s, so it
stays where it is and is classified rather than moved.

### A.4 Files changed, and why each was necessary

| file | why |
|---|---|
| `DESIGN_STATE_CONTRACT.yaml` | eight new families with their vocabularies and rules; `SelectionDecision` reshaped and re-owned; six new semantic roles; `MobilityExpectation` gains the role it always carried and never declared |
| `STAGE_RESPONSIBILITY_CONTRACT.yaml` | `gate` → `feasibility` + `selection`, with premises, prohibitions and the isolation rule |
| `STAGE_OWNERSHIP_MATRIX.yaml` | a `responsibilities` block with `runs_after`. `gate` having no entry here is the root of the s04 mis-ownership |
| `ENTITY_FAMILY_AUDIT.yaml` | eight audit entries; the corpus gate requires every family to be audited |
| `S01_CONTRACT.yaml` | its ownership projection must list `DesignConstraint` |
| `S04_CONTRACT.yaml` | three `stages.s04a, gate and s04b` pointers now dangle |
| `USER_DESIGN_PROFILE_CONTRACT.yaml` (new) | the two-section input split, its visibility rule and its evaluability rule |
| `design_state.py` | **the only production change**: `Contracts` merges responsibilities into the ownership table, so `may_create` refuses `s04 → SelectionDecision`. Without it the boundary could not enforce the split |
| six test files | contract-truth assertions that pinned `gate`, the premise count, the audit count, and fixtures creating a decision as s04 |

### A.5 Two test gates were wrong, not just outdated

`VIEW_15` asserted the view module contains no stage-id substring. `selection` is
also what that module calls the instance-selection rule on a `Requirement`, so
the check failed on `__slots__` — a false alarm about a real rule. It now walks
the **AST** and looks for a stage id used in a comparison, a subscript or a
`.get()` key, which is what a branch is actually made of.

`test_consumer_view._add` filled every required field with `"x"`, which is prose
where an entity id belongs (R-20). It now fills declared references as
references. Neither change weakens a property; both make the check test the
property it names.

### A.6 Behavioural evidence — 21 cases in `test_s7_authority_boundary.py`

| | claim | how |
|---|---|---|
| **F11** | no pre-selection view can contain a profile | a real `SelectionProfile` in state, then `build_consumer_view` for **all seven** pre-selection responsibilities — none contains it |
| **F11b** | the isolation is structural | no pre-selection responsibility declares the role; `selection` does |
| — | the split exists | `gate` gone; feasibility cannot author a decision; exactly one responsibility declares `SelectionDecision` |
| — | **the write boundary enforces it** | `may_create("s04", "SelectionDecision")` is **False**; `may_create("selection", …)` is True; feasibility may create an assessment and selection may not |
| — | a responsibility has a position | `runs_after: s04`, which `gate` never had |
| — | the frozen semantics | three-state feasibility, three-state compliance, "missing evidence is not feasibility", "a preference is never a constraint", `NOT_AVAILABLE` metrics, an advisory that may not author authority, premises vs considered, the UI writing an input |
| — | no competing authority | the gate check writes nothing; no contract places selection between the s04 passes; the profile contract keeps the two inputs apart |

### A.7 Newly discovered, with owners

| | | owner |
|---|---|---|
| `MobilityExpectation` carried **no semantic role**, so a responsibility needing a DOF disposition could not ask for it by role | declared, since S7-A needs it | fixed here |
| `gate`'s absence from the ownership matrix is the mechanism of the s04 mis-ownership, not a separate bug | fixed here | — |
| `S05_CONTRACT` still names `blocking_relations` | untouched | **S-8** |
| `sample()`'s three-pose floor is redundant beside `sweep_hull`'s two-pose handling | untouched | **S-8** |

### A.8 Exact remaining work

**S-7 / U-8 IS NOT CLOSED.** S7-A froze the authority; nothing produces any of it.

| substep | work |
|---|---|
| **S7-B** | the profile ingester; `DesignConstraint`; candidate-local `MechanicalFeasibilityAssessment` and `HardRequirementCompliance` over the nine declared domains. F2, F3, F4, F5, F12 |
| **S7-C** | `SelectionProfile` materialisation; the eligibility population; deterministic metrics with availability and source refs; `CandidateComparison`. F1, F7 |
| **S7-D** | `SelectionAdvisory`, `SelectionConcern`, evidence-status validation. F6, F7 |
| **S7-E** | the Streamlit checkpoint, `HumanDecisionInput`, the deterministic decision writer, stale-submit protection. F13, F14, F15, F16, UI1–UI8 |
| **S7-F** | reopening lifecycle and generalisation. F8, F9, F10 |

Regression, **secondary**: RUN 928 · PASS 928 · FAIL 0 · SKIP 22.

---

## S7-A CORRECTION PASS (baseline `4c2cb32`)

### C.1 Blockers reproduced before editing

**A — feasibility declared domains whose evidence its view could not contain.**
The real `feasibility` ConsumerView, built over a candidate with S04B evidence
standing in state:

```
status          UPSTREAM_INSUFFICIENCY
State           in view: False | in state: 2
Transition      in view: False | in state: 1
SweptVolume     in view: False | in state: 1
Joint           in view: False | in state: 1
```

Four of the nine declared domains — required configurations, motion and
transitions, spatial realization, gross interference — were decided on facts the
view could not carry.

**Root cause, found by the reproduction:** `State`, `Transition` and
`SweptVolume` carry **no semantic role at all**. No responsibility could ask for
them without naming the family, which is the whitelist U-3 exists to remove. The
same gap `MobilityExpectation` had.

**Sixth blocker, also found by the reproduction:** the view was
`UPSTREAM_INSUFFICIENCY` for a different reason —
`HardRequirementCompliance.constraint → DesignConstraint` is a required
single-valued reference, so Source A made it REQUIRED_NONEMPTY. A design that
states no hard requirement produces no compliance records, and an output that
need not be produced was blocking the stage that need not produce it.

**B — the pending S04B rule is circular.** `selection_decision`,
`COMMITTED_BRANCH`, `REQUIRED_NONEMPTY`, `activated_by: S-7 / U-8`. Activating it
means `SelectionDecision → s04b`, while the architecture is
`s04b → feasibility → selection → SelectionDecision`. **S7-A is the step that
would have activated it.**

**C — existence conflated with visibility.** The profile contract said "every
stage may see them"; exactly one responsibility declares the role.

**D — reviewed concerns unrecordable.** `HumanDecisionInput` and
`SelectionDecision.considered_refs` could name a `SelectionAdvisory` and nothing
could name a `SelectionConcern` — the thing a reviewer is actually for.

**E — ordering ambiguous.** Both responsibilities said `runs_after: s04` and
nothing said which came first.

### C.2 The feasibility ConsumerView, before and after

```
BEFORE  UPSTREAM_INSUFFICIENCY
        18 families, none of State / Transition / SweptVolume / Joint

AFTER   VIEW_READY
        24 families, including State, Transition, SweptVolume, Joint
        Witness           absent  (s04-owned, carries no role — not a dump)
        SelectionProfile  absent  (F11 unchanged)
```

### C.3 Roles added, and why none is a whitelist

| role | meaning | carried by |
|---|---|---|
| `realized_configuration` | the coordinate values that realize one named configuration — what the mechanism is SET TO, as against the configuration, which only names it | `State` |
| `motion_path` | a path between two realized configurations and which coordinates it changes — how a design says a motion HAPPENS | `Transition` |
| `motion_occupancy` | the space a moving group occupies along a motion, and at what evidence level | `SweptVolume` |

Each states an engineering meaning, none names a stage, and only the family that
carries that meaning declares it — asserted as an **equality**, so a fourth
family quietly acquiring one of these roles fails.

Two premise classes were added to `feasibility`: `realized_motion` (the three
roles above plus `kinematic_axis`) and `candidate_local_geometric_finding`
(`reach_evidence`, `elimination_evidence`, `assembly_order`) — the second because
a local geometric finding is **input** to eligibility and not a verdict on it.

### C.4 The S04B selection dependency, retired

Not deferred — **retired**, with what it used to say kept beside the reason it
cannot come back. `retired_premise_classes` on s04b records the population, the
existence, the activation step it claimed, and the circularity. s04b runs
candidate-locally on the branch its invocation names. No provisional decision is
invented and no candidate is selected in order to run it.

### C.5 Hard-constraint existence and visibility

> `DesignConstraint` is **authoritative from early requirement capture** and
> **visible only where the reasoning requires it**.

The asymmetry is stated because it is not symmetric: a hard requirement **may**
legitimately affect upstream reasoning, and each responsibility exercises that by
declaring the role; a preference **must not**, ever, and that is enforced by no
responsibility declaring the other role at all. "May affect" is not "inject into
every view".

`s01` gains `DesignConstraint` as a permitted output, and its prohibition is
sharpened from "naming any mechanism, material or dimension" — which would have
forbidden recording a user who **said** "all parts must be plastic" — to
**inventing** one the source did not state. The test is the source, not the
vocabulary.

### C.6 Sequencing

`runs_after_responsibility: feasibility` on `selection`. The resolved order is
`s04 → feasibility → selection`, asserted by walking the declarations rather than
by trusting that one happens to require the other's output.

### C.7 Reviewed-concern provenance

`HumanDecisionInput.reviewed_concerns → SelectionConcern[]`, and
`SelectionDecision.considered_refs` splits into `considered_advisories` and
`considered_concerns`. Both stay **optional**, both stay out of `required_fields`,
and the premise fields are untouched — so rewording an advisory or a concern
stales nothing.

### C.8 Production changed, and why it was unavoidable

| file | change | why |
|---|---|---|
| `view/consumer_view.py` | 9 lines: a family listed in the responsibility's `conditional_outputs` has its Source-A referent treated as MAY_BE_EMPTY for **readiness** | without it, a stage is blocked on the referent of an output it need not produce. The record's own requirement is untouched — a compliance record still cannot exist without its constraint, and the write boundary still says so |
| `stages/s04_envelope_and_motion.py` | **docstring only**: "two passes, one selection gate" retired | the corpus sweep required no CURRENT occurrence to contradict `s04b → feasibility → selection`, and that line did. Zero behavioural change, verified by reading the diff |

No S7-B…S7-F producer exists.

### C.9 A1–A10

| | claim | result |
|---|---|---|
| **A1** | the declared motion domains have their evidence | VIEW_READY; nine families present including State, Transition, SweptVolume, Joint |
| **A2** | no blanket S04 dump | a `Witness` created under s04 does **not** enter — being s04's is not a reason |
| **A3** | no preference leakage | a standing `SelectionProfile` is still absent |
| **A4** | nothing requires a decision before s04b | no live class, no COMMITTED_BRANCH population, retirement records the circularity |
| **A4b** | nothing live is staged for activation | structural: no `premise_classes_pending_step` anywhere; `activated_by` exists only inside the `was:` record of what a retired rule used to say |
| **A5** | the order resolves | `s04 → feasibility → selection`, walked from the declarations |
| **A6** | early ingestion by the declared owner | `DSC-1` created by s01 with parameters carried verbatim; `may_create("s02", …)` is False |
| **A7** | visibility is selective | exactly one responsibility declares the role; s02/s03a/s03b/s04a receive none |
| **A7b** | a consumer that declares it receives it | `DesignConstraint` in the feasibility view |
| **A7c** | a design with none is not blocked | the conditional-output declaration |
| **A8** | carrying is not inventing | s01 may output it; the prohibition names INVENTING; both contracts agree |
| **A9** | both kinds of reviewed material | `reviewed_advisories` and `reviewed_concerns`, distinct typed many-references |
| **A10** | review does not create a premise | considered fields optional and separate; the premise set is the required one |

### C.10 Newly discovered, with owners

| | | owner |
|---|---|---|
| `State`, `Transition`, `SweptVolume` carried no semantic role — three S-6 families no responsibility could ask for | declared here, because S7-A cannot proceed without them | fixed here |
| an output produced per-instance blocked its stage when the instance count was zero | one general declaration + 9 lines | fixed here |
| `s04` module docstring claimed a gate between the passes | docstring only | fixed here |
| `S05_CONTRACT` still names `blocking_relations` | untouched | **S-8** |
| `sample()`'s three-pose floor is redundant | untouched | **S-8** |

Regression, **secondary**: RUN 942 · PASS 942 · FAIL 0 · SKIP 22.

---

## CURRENT STATUS

> **S7-A VERIFIED CLOSED — FEASIBILITY / SELECTION AUTHORITY, INPUT SUFFICIENCY,
> ORDERING AND PREFERENCE ISOLATION CONSISTENT.**
>
> The split holds and the write boundary enforces it. The feasibility view now
> contains the evidence its declared domains are decided on, and contains neither
> a preference nor an s04 family that carries none of its semantics. The order
> `s04 → feasibility → selection` is machine-readable, and the rule that would
> have made it circular is retired rather than waiting. A hard requirement exists
> early and is visible only where the reasoning asks for it; a preference is
> visible nowhere before selection. A human can record which concerns they read,
> and reading one creates no premise.
>
> **S-7 / U-8 IS NOT CLOSED.** S7-B through S7-F are not started: nothing
> produces a feasibility assessment, a compliance result, a profile, a
> comparison, an advisory, a human input or a decision.
