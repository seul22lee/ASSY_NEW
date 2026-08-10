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

## CURRENT STATUS

> **S-7 / U-8 NOT CLOSED — S7-A (authority freeze) complete; S7-B through S7-F
> not started.**
>
> The boundary is executable where it can be without producers: the write
> boundary refuses s04 a `SelectionDecision`, and no pre-selection consumer view
> can contain a preference. Nothing yet produces a feasibility assessment, a
> comparison, an advisory or a decision.
