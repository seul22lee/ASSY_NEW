# IMPL S-7 / U-8 — FEASIBILITY AND SELECTION

Baseline `9f98cbc`. S-3, S-4, S-5 and S-6 are closed and are not reopened.

This step is planned in six substeps (§20). **This document records S7-A
through S7-D.** S7-E and S7-F are not started.

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

## S7-A CLOSURE SWEEP (baseline `e815985`)

**Production diff is empty.** `ver3/assy_v3` and `ver3/tools` are byte-identical;
the change is five contract files and one test file.

### D.1 Blockers found in the full sweep

Two were named in the brief. **Ten more were not** — the sweep was written as a
scan of every canonical and projection file rather than a walk of known lines,
because the last three passes each turned up residue nobody had listed.

| # | file | CURRENT claim | why it contradicted |
|---|---|---|---|
| 1 | `S01_CONTRACT` | `prohibited_decisions`: *"name a mechanism, material, part or dimension"* | a blanket ban forbids **recording** a user who said "all parts must be plastic" |
| 2 | `S01_CONTRACT` | `structured_outputs` omitted `DesignConstraint` | the file's own `owned_decisions.creates` listed it — one contract, two answers |
| 3 | `S04_CONTRACT` | file header: *"The selection gate sits between them"* | the claim that made s04b unreachable, still at the top of the file |
| 4 | `S04_CONTRACT` | `prohibited_decisions`: *"which surviving candidate wins, **before the gate**"* | implied s04 may decide a winner afterwards. It may not, at any point |
| 5 | `S04_CONTRACT` | `selection_gate` comment: s04b's premise is *"staged behind that step"* | S7-A **retired** it; nothing is staged |
| 6 | `S04_CONTRACT` | `selection_gate.position`: *"the gate is S-7 / U-8"* | names a gate rather than the `selection` responsibility, and omits `feasibility` from the order |
| 7 | `DESIGN_STATE_CONTRACT` | `EliminationRecord.rules`: *"The gate that acts on it is U-8/M-5B and does not exist yet"* | what acts on it is `feasibility`. It was true of a gate that is not coming |
| 8 | `DESIGN_STATE_CONTRACT` | `prohibited_content`: *"a selected-candidate field before the **Stage 03/04 feasibility gate**"* | names the retired architecture. The true rule is stronger and simpler |
| 9 | `ENTITY_FAMILY_AUDIT` | `SelectionDecision.open_question`: *"If the gate produces no SelectionDecision…"* | a human records an UnresolvedDecision; no gate produces anything |
| 10 | `ENTITY_FAMILY_AUDIT` | `EliminationRecord.duplicates_note`: *"…WON, **at the gate** … before any gate exists"* | as above |
| 11 | `ENTITY_FAMILY_AUDIT` | `EliminationRecord.s1_note`: *"the gate that would act on it is U-8"* | as above |
| 12 | `S04_CONTRACT` | `runs_on`/prohibition wording implying selection precedes s04b | corrected with 3–6 |

**Classified and deliberately left:** `STAGE_PROGRESSION_CONTRACT`'s many uses of
"gate" mean the **stage-freeze** gate — a different, live concept — and
`Witness`'s *"before its stage's gate"* is that same one. `COMMITTED_BRANCH`
survives as a population **vocabulary term** and its resolver, which is correct:
it is how a post-selection consumer will scope itself. Every other occurrence is
inside a retirement record.

### D.2 Files changed

`stages/S01_CONTRACT.yaml` · `stages/S04_CONTRACT.yaml` ·
`DESIGN_STATE_CONTRACT.yaml` · `ENTITY_FAMILY_AUDIT.yaml` ·
`tests/meta/test_s7_authority_boundary.py`. Every retirement states what it used
to claim.

### D.3 The sweep is now a standing test

`TestNoResidueOfTheOldArchitecture` walks the seven canonical files, skips the
keys whose value is a **record of what something used to say** — a retirement
that could not quote what it retired would be a deletion — and fails on any
current claim matching a narrow phrase list. "Gate" alone is not banned, because
the progression contract legitimately uses the word; only the shapes that mean
*this* gate are.

Three more assertions hold the projections together: `s01`'s five projections
must all name `DesignConstraint`, no stage projection may name
`SelectionDecision`, and no prohibition about materials or dimensions may be
phrased as a blanket ban.

**Mutation checks:** reintroducing "before the gate" (1 failure), the blanket s01
ban (1), and dropping `DesignConstraint` from one projection (1) — each caught.

### D.4 S7-B producers are still absent

`grep` for the eight declared families across `ver3/assy_v3` and `ver3/tools`
returns **0**. Nothing produces a feasibility assessment, a compliance result, a
profile, a comparison, an advisory, a human input or a decision.

Regression, **secondary**: RUN 947 · PASS 947 · FAIL 0 · SKIP 22.

---

## S7-B — MECHANICAL FEASIBILITY (baseline `3c90632`)

One deterministic, candidate-local authority that turns what s01–s04 established
into an eligibility statement. **No provider is called and there is no prompt**:
a model may not declare a mechanism feasible, so the responsibility is a reading
of the evidence rather than a request for an opinion.

### B.0 One deviation from the brief's literal text, and why

The brief specified `ver3/assy_v3/stages/s07_mechanical_feasibility.py`. **`s07`
is already taken.** Pipeline stage s07 is geometry compilation and has its own
`S07_CONTRACT.yaml`; migration step S-7 is not pipeline stage s07, and §A.1 above
records S7-A declining this exact collision — *"they are responsibilities, as
`gate` already was: non-numbered"*. Under the brief's filename the progression
gate would also have passed **for the wrong reason**: it looks for
`S07_CONTRACT.yaml` and would have matched the compiler's.

The file is `ver3/assy_v3/stages/feasibility.py`, named for the responsibility id
that actually exists in the contracts. Nothing else about the brief's §1 shape
changed, and B25c asserts the module claims no pipeline stage id. Renaming it back
is three import lines if the pipeline is renumbered later.

### B.1 What was built

`ver3/assy_v3/stages/feasibility.py`, entered at
`evaluate_candidate_feasibility(state, candidate_id) -> FeasibilityOutcome`. It
builds `InvocationContext(branch=candidate_id)`, builds the real ConsumerView for
responsibility `feasibility`, **refuses to produce a patch unless the view is
`VIEW_READY`**, reasons only from `view.payload()`, and validates its
`StagePatch(stage_id="feasibility")` through the ordinary write boundary. Raw
`DesignState` is touched for the view, the parent hash and validation, and for no
engineering fact — a second context channel beside the view is what U-3 removed.

Nine domain evaluators behind one dispatch table, `DOMAIN_EVALUATORS`, and one
aggregation function whose whole body is the contract's `aggregation:` clause.
Three rules decide almost every verdict:

| | |
|---|---|
| applicability before status | `NOT_APPLICABLE` means the design poses no question here. It never blocks and it is not a weaker PASS. |
| absence is `NOT_ESTABLISHED` | never PASS, and never FAIL either. A missing envelope, an unchecked path and a conservative overlap are all things the design has not established. |
| FAIL needs a positive contradiction | a current typed fact that contradicts a requirement. Not an absence, and not a model's opinion. |

`gross_interference` therefore **has no FAIL path at all**, and that is a
statement about the evidence rather than about the mechanisms: an axis-aligned
box overlap is not a collision, so no-overlap proves clearance and overlap proves
nothing. Manufacturing a FAIL to balance the vocabulary was declined.

### B.2 No second formula

Every geometric and kinematic computation is the one s03/s04 already perform.
Three pure helpers were **extracted** from frozen code, with the callers' findings
and output strings preserved byte for byte:

| helper | from | now shared with |
|---|---|---|
| `box_gap(a, b)` | three inline copies in s04 | load hops, required contacts |
| `coordinate_change_disagreement(from, to, declared)` | `transition_realization_check` | `motion_and_transitions` |
| `assembly_order_problems(steps)` | `assembly_acyclic_check` | `assemblability` |

Reused unchanged: `free_dof`, `sweep_hull`, `overlaps`, `aabb`, `axis_index`,
`required_contacts`, `sample`/`SAMPLES` (the insertion hull is built with the same
span and sampling `assembly_path_check` uses). Checker-string parsing appears
nowhere; `assembly_order_problems` is the one place a returned string is
inspected, and only to separate a cycle from a dangling dependency — a
contradiction from an absence.

Equivalence evidence: the 123 S-5/S-6 tests over those checkers pass unchanged.

### B.3 Two input-boundary defects, found by building the consumer

Both are the same defect S7-A fixed once already: **a responsibility declaring a
domain whose evidence its own view could not contain.**

**`LoadPath` carried no semantic role at all.** A view is assembled from declared
roles, and nothing referenced a load path either, so it reached no consumer.
`load_reaction_closure` would have read an empty list as *nothing to close* and
reported PASS. Role `load_route` added — candidate-specific where the demand it
answers is not — and declared by the family.

**No premise class carried the design's demands.** Source A reached a
`PhysicalEffectObligation` only through the `PhysicalInteraction` that discharges
it, so **exactly the undischarged obligations — the ones the domain exists to
find — were the ones the view could not hold.** New class
`declared_physical_demand` (DESIGN_WIDE, MAY_BE_EMPTY) covering
`physical_effect_obligation`, `load_case`, `reaction_site`; and
`candidate_engineering_evidence` gained `topology_element`, `topology_relation`
and `load_route`, because "do the bodies the topology connects actually touch" is
asked of the joint graph and the CONTACT interfaces and Source A reached neither.

**A third, found by B11.** `realized_motion` declared one existence rule for four
roles: `REQUIRED_NONEMPTY`, reason *"a mechanism with no realized motion has no
motion to judge"* — which is the reason a motion domain reports NOT_APPLICABLE,
written as the rule that makes the whole context UNREADY. A static candidate got
no assessment at all. Split `by_role`: a configuration no state realizes is
missing evidence (`REQUIRED_NONEMPTY`); a path that does not exist and an
occupancy for a motion nobody declared are absences the design meant
(`MAY_BE_EMPTY`).

### B.4 The domain is the unit of dependency

`FeasibilityDomainAssessment` is one record per domain per candidate, because a
motion verdict and a load verdict rest on different facts and a single record for
all nine could carry only their union — so an envelope changing would have staled
the load closure it cannot affect, and STALE that fires for no reason is STALE
nobody reads. It has **no `evidence_refs` field**: the operation's `premise_refs`
*are* the evidence, and a second reference list beside them would be a second
answer to "what did you use".

On the hinge probe, exactly:

| domain | premises |
|---|---|
| physical_realization | `PEO-0001 PHI-A` |
| load_reaction_closure | `LC-0001 LDP-A IFC-0A RSR-0001 ENV-G0A ENV-G1A SCL-CND-A` |
| mobility_disposition | `TRN-A JNT-0A MEX-CFG-C0A MEX-CFG-C1A` |
| required_configurations | `CFG-C0A CFG-C1A STA-CFG-C0A STA-CFG-C1A SCL-CND-A` |
| motion_and_transitions | `TRN-A STA-CFG-C0A STA-CFG-C1A SCL-CND-A` |
| spatial_realization | `BOD-* RGP-* JNT-0A IFC-0A ENV-* SWV-* SCL-CND-A` |
| reach | *(none — a requirement with no deterministic basis names nothing)* |
| assemblability | `ASY-0A ENV-G0A ENV-G1A SCL-CND-A` |
| gross_interference | `BOD-* IFC-0A ENV-* SWV-* SCL-CND-A` |

Visible in the same view and in none of them: `REQ-0001`, `SCN-0001`,
`ACT-0001`, `OBL-0001`, `CRL-0A` (a relation blocking a DOF nothing requires to
move), and the `ReachResult`. Both directions are asserted as one equality in
B22.

**The reference scale was missing from every geometric domain in the first cut**,
and the exact-set test is what found it. Naming only the envelope does not carry
the basis it is expressed in: `_propagate` is one hop, so superseding the scale
stales the envelope and stops, leaving the verdict standing on numbers that had
just lost their meaning. The same reason the MFA carries the **raw union** of its
domains' premises rather than only the nine domain ids.

### B.5 Hard requirements

`CONSTRAINT_EVALUATORS[kind]`, one `HardRequirementCompliance` per current
`DesignConstraint`, and a kind with no entry answers `NOT_YET_EVALUABLE` — which
is the honest answer, not a gap.

* `MATERIAL_CLASS_ONLY` → `NOT_YET_EVALUABLE`. No canonical material assignment
  exists anywhere in the representation, and a candidate's prose is not one.
* `PROHIBITED_ENERGY_SOURCE` → `NOT_YET_EVALUABLE`. Same shape.
* `MAX_OVERALL_DIMENSION` → decides **only** when `ReferenceScale.basis` is
  ABSOLUTE and `absolute` states both the unit and what one coordinate is worth
  in it. `per_unit` is not defaulted to 1: what a coordinate is worth is the
  whole content of an absolute basis. The condition is now a rule on
  `ReferenceScale` rather than a shape assumed by the consumer.

A design that states no hard requirement produces no compliance record, and that
is a complete answer.

### B.6 Runner

`run_feasibility(case_id, state, trial, invocation=None)` in `run_window2.py`,
after `run_s04`, on the state s04 actually modified. **Its signature has no
`provider` parameter.** It invokes, applies and records; it reads no domain
verdict, aggregates nothing, and names no engineering status — B24 asserts that
by scanning its source for every verdict token. It runs unconditionally on s04's
check findings: whether any of them stops the candidate is this responsibility's
question, and skipping the call when a check fired would answer that question in
the runner.

### B.7 Behavioural evidence — 33 tests in `test_s7_feasibility.py`

Every test runs the real chain (s02 → s03 → s03b → s04a → s04b) and then the real
evaluator over the real view. Two synthetic mechanisms: two bars on a pivot, and
four bars in a closed loop.

| | |
|---|---|
| B1–B3 | hinge FEASIBLE, four-bar FEASIBLE, and **the same domain map** — complexity is not an input, asserted by running both |
| B4, B4b | unrealized declared distinctness, and a transition moving what it did not declare → FAIL → INFEASIBLE |
| B5 | required transition absent → NOT_ESTABLISHED, **not** NOT_APPLICABLE |
| B6 | conservative overlap → never FAIL, in any domain |
| B7, B7b | terminus that is not the declared site; terminus inside the product → INFEASIBLE |
| B8 | positive gap on the load route → INFEASIBLE (and spatial realization FAILs on the same fact) |
| B9, B10 | required cell UNDISPOSITIONED → NOT_ESTABLISHED; required cell BLOCKED_BY → INFEASIBLE |
| B11 | static candidate → NOT_APPLICABLE, not a context failure |
| B12 | `ReachResult` alone cannot PASS or FAIL, and is not a premise of the verdict |
| B13 | `EliminationRecord.eliminated` alone → NOT_ESTABLISHED, never INFEASIBLE |
| B14–B16 | material, energy, unknown kind → NOT_YET_EVALUABLE; absolute scale → SATISFIED/VIOLATED; three ambiguous-scale shapes → NOT_YET_EVALUABLE |
| B17 | a standing `SelectionProfile` is absent from the view, the premises and the fields |
| B18 | another candidate's geometry changing leaves this one STANDING |
| B19 | a fact this candidate used stales the domain **and the MFA directly** |
| B20 | a visible fact nothing computed from is not a premise and does not stale |
| B21 | **12 mutations**, one premise at a time, each caught |
| B22, B22b, B22c | the exact premise set both directions; per-domain isolation; an absence gets no fabricated premise |
| B23 | no provider import, no provider parameter, no invocation-shaped call — read from the AST |
| B24 | the runner records and decides nothing |
| B25, B25b, B25c | no other stage may author the three families; an unready context yields a refusal, not an assessment; the module claims no pipeline stage number |

### B.8 Scope held

`SelectionProfile` production, candidate comparison, ranking, advisory, human UI,
`SelectionDecision`, preference handling and S7-F re-evaluation are all absent.
`DesignState._propagate` and the generic stale semantics are unchanged, and no
S-4/S-5/S-6 engineering meaning was altered.

### B.9 Newly discovered, with owners

* **S7-F** — a second `evaluate_candidate_feasibility` on the same state would
  CREATE ids that already exist. Re-evaluation is a revision lifecycle and is
  S7-F's; nothing here pretends otherwise.
* **S-8** — `reach` is NOT_ESTABLISHED on every design that asks a reach
  question, because no deterministic reach basis exists (no hand envelope, no
  access trajectory, no clearance corridor). This is reported as the true
  evidence limitation rather than weakened into a PASS.
* **S-8** — no canonical material or energy/actuation assignment exists, so two
  of three constraint kinds can only answer NOT_YET_EVALUABLE today.

Regression, **secondary**: RUN 981 · PASS 981 · FAIL 0 · SKIP 22.

---

## S7-B CORRECTION + CLOSURE SWEEP (baseline `b55c00a`)

**Eight blockers reproduced before a line was edited**, and the reproduction
script is what set the order of work. The correction found three more of the same
classes on its own sweep. The architecture is unchanged: same view, same three
families, same one-hop raw-premise union, still no provider.

### C.1 The blockers, and the root cause of each

| | reproduced | root cause |
|---|---|---|
| **1** | `DesignConstraint` in state: `[]`; s01 emits none | The family, its rules and its s01 ownership were all declared at S7-A and **no code ever read a profile**. `USER_DESIGN_PROFILE_CONTRACT` said "the ingester is S7-B" and S7-B built the consumer without building the producer. |
| **2a** | `Actor.must_reach` set, `reach → NOT_APPLICABLE` | Applicability was read off `FunctionalRegion` — the candidate's ANSWER. A candidate that ignored the actor entirely was indistinguishable from a design with no actor. |
| **2b** | motion PEO present, no Transition, `motion → NOT_APPLICABLE` | Same shape: the demand was never consulted, only the realization. |
| **3** | `(RGP-G1A, CFG-C0A, RZ)=BLOCKED_BY`, `(…, CFG-C1A, …)=INTENDED` → `FAIL` | The lookup matched `g == group and x == dof` and **dropped the configuration**, asking "is this DOF blocked anywhere" instead of "is this cell free". A latch free when open and held when closed read as a contradiction. |
| **4** | `PEO.effect=TRANSMIT_FORCE`, interaction `effect=LOCATE` → `PASS` | Discharge was accepted on `discharges_effect == PEO.id` alone. `effect` and `discharges_effect` are two fields precisely because they can disagree, and checking only the reference made the typed vocabulary decorative. |
| **5** | `CLEARANCE` pair, overlapping boxes → `PASS` | `declared` was every interface with two bodies. "An interface exists" was read as "these two may overlap" — inverting CLEARANCE, the one kind that promises they stay apart. |
| **6a** | one of two bodies enveloped → `SATISFIED` | "Overall" was measured over `boxes`, the placed subset. The more incomplete the arrangement, the more comfortably it passed. |
| **6b** | `axis: DIAGONAL` → `SATISFIED` | `AXIS_INDEX.get(axis, 0)` answered a requirement about a direction nobody named by silently measuring X. |

### C.2 Three more of the same classes, found by the sweep

* **A changed coordinate that names no Joint** produced no requirement at all —
  the declared motion vanishing instead of being questioned. Now
  `CHANGED_COORDINATE_NOT_A_JOINT`.
* **`free_dof` defaults an unreadable axis to Z.** That is S-5's settled
  behaviour and stays so; what was wrong was a feasibility cell address built
  from the default. Now refused as `REQUIRED_MOTION_AXIS_UNREADABLE`, using the
  same `axis_index` test `spatial_realization` already applies.
* **`by_joint` was taken on trust.** The write boundary checks the reference
  resolves to a Joint, not that the joint's class and axis leave that DOF of that
  group free — the same defect as the effect discharge, one family over.
  `_disposition_support` now reads `free_dof`, so the question has the one answer
  s03's derivation used to author the claim.
* **`_assemblability` skipped unplaced prior bodies in silence** — partial
  geometry read as complete, one domain over from §6. Now
  `INSERTION_GEOMETRY_INCOMPLETE`.

### C.3 The ingress

`ingest_design_constraints(profile)` in `s01_requirement_capture.py`, called from
s01's own `to_operations` so the constraints are in s01's own patch.

**Two inputs, two paths, and only one goes near a model.** The request text is
prose and a model reads it. The profile is already structured — a section that
says `PLASTIC_ONLY` says it in a field — so it is mapped across without asking
anything. Nothing is completed: a limit with no unit stays a limit with no unit,
and the compliance record downstream says `NOT_YET_EVALUABLE`.

`evaluability` says WHO the requirement is addressed to, not whether the answer
will succeed — structured parameters mean a check, a bare sentence means a
person. Deriving it from whether some registry currently holds an evaluator would
make an s01 fact depend on what a later stage happens to implement.

**The preference section is never read.** Not filtered afterwards — the ingester
names one key, `CONSTRAINT_SECTION`, and B27 asserts the source contains no other.
Ids are `DSC-%04d` in the profile's own order, so the same profile always ingests
to the same ids and no counter exists.

Wired live: `run_window2.design_profile(case_id)` reads `design_profile.json|yaml`
beside the request and passes it to s01. Not replayed, because it was never a
model response.

### C.4 Applicability is now read from the demand

| domain | demand | with no realization |
|---|---|---|
| reach | `Actor.must_reach` non-empty | `NOT_ESTABLISHED` + `REACH_REALIZATION_ABSENT` |
| motion_and_transitions | a `Configuration.distinguishing_basis`, **or** a PEO whose effect is one of `TRANSMIT_MOTION` / `CONVERT_MOTION` / `PERMIT_MOTION` | `NOT_ESTABLISHED` + `REQUIRED_TRANSITION_MISSING` |
| mobility_disposition | the same motion obligations | `NOT_ESTABLISHED` + `MOTION_DEMANDED_WITHOUT_REALIZATION` |

`PREVENT_MOTION` is deliberately not a motion demand: it requires that motion
*not* occur, which is a different question and not this one asked backwards
(B30b). `actor_role` was added to the `declared_physical_demand` premise class —
without it an actor reached the view only when some candidate happened to
reference it, so applicability was still being read off the answer one level up.

### C.5 Files changed

| file | why |
|---|---|
| `stages/feasibility.py` | six corrections above, plus the three the sweep found |
| `stages/s01_requirement_capture.py` | the ingress (+59 lines, one new function) |
| `stages/s04_envelope_and_motion.py` | `interface_expectation` / `INTENDED_CONTACT_KINDS` extracted; `required_contacts` and `configuration_interference_check` now call it. Findings and strings byte-identical |
| `contracts/DESIGN_STATE_CONTRACT.yaml` | `Interface.interaction_kinds` corrected to the vocabulary in force; `spatial_expectation` declared; `NOT_INTENDED_TO_INTERACT` recorded as declared-and-never-producible |
| `contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml` | `actor_role` on `declared_physical_demand` |
| `contracts/ENTITY_FAMILY_AUDIT.yaml` | four "S7-B has not yet emitted it" statements retired; the S-2 growth note dated so it cannot read as current |
| `contracts/stages/S01_CONTRACT.yaml` | the profile input and `constraint_ingress`; `llm_role` split by input |
| `contracts/USER_DESIGN_PROFILE_CONTRACT.yaml` | `ingester_status: LIVE` |
| `tools/run_window2.py` | `design_profile()`; s01 receives it |
| `tests/meta/test_s7_feasibility.py` | B26–B35, the closure sweep, and the fixture now runs the real s01 |

**The `Interface` vocabulary had NOT ONE VALUE IN COMMON with the producer's.**
The contract said `DECLARED_CONTACT…NOT_INTENDED_TO_INTERACT`; s03 has always
emitted, validated and checked `CONTACT`/`CLEARANCE`/`INTERFERENCE_FIT`/
`COMPLIANT_INTERACTION`. Every interface in every recording would have failed the
contract's list, and every value the contract named would have been refused by
s03's own validator. Nothing read the contract, so nothing noticed. Corrected
toward the runtime — it is frozen S-4/S-6 behaviour with recordings behind it —
and what is lost by choosing that direction is written down rather than dropped:
`NOT_INTENDED_TO_INTERACT` is the only kind from which gross interference could
ever produce a FAIL, and reintroducing it is a producer change owned by **S-8**.

### C.6 Production diff summary

`feasibility.py` +352/−? against `b55c00a`; `s01_requirement_capture.py` +59;
`s04_envelope_and_motion.py` +29/−9 (extraction only — the 162 S-4/S-5/S-6 tests
over those checkers pass unchanged); `run_window2.py` +23. No change to
`DesignState._propagate`, to the generic stale semantics, or to any S-4/S-5/S-6
engineering meaning.

### C.7 B26–B35, and the sweep

**72 tests** in `test_s7_feasibility.py` — the 34 from S7-B, plus:

| | |
|---|---|
| B26, B26b, B26c | profile → s01 → `DesignConstraint` → feasibility view → `HardRequirementCompliance`, with `_created_by == "s01"` asserted; an incomplete parameter set stays incomplete; a bare statement is `HUMAN_EVALUABLE` |
| B27, B27b, B27c | a preference creates nothing, a preference-only profile creates nothing, an entry with no kind is not invented into one |
| B28, B28b | same group/DOF, opposite dispositions in two configurations: the basis uses its own configuration's cell **and mutating the other one does not stale the verdict**; a transition still requires the cell at both its ends |
| B29, B29b | reach demand with no realization → `NOT_ESTABLISHED`; no demand and no region → `NOT_APPLICABLE` |
| B30, B30b | typed motion PEO with no Transition → both motion domains `NOT_ESTABLISHED`; `TRANSMIT_FORCE`/`PREVENT_MOTION`/`LOCATE` demand no motion |
| B31, B31b | mismatched effect cannot PASS, and names both facts; the matching effect still discharges |
| B32, B32b, B32c | `CLEARANCE` + overlap → `NOT_ESTABLISHED` (never FAIL); `CLEARANCE` held apart → PASS; intended contact still exempt |
| B33, B33b | one body without an extent → `NOT_YET_EVALUABLE`, naming the unplaced body; every body placed decides it both ways |
| B34, B34b, B34c | unknown axis → `AXIS_NOT_RECOGNIZED`; X and Y measure different spans (a fallback would have made them agree); three ambiguous-scale shapes |
| B35 – B35f | no active statement says these families are unproduced; the declared ingress is the one that runs; the interface vocabulary matches the producer's; declared domains == evaluators; motion effects come from the declared vocabulary; every demand's role is in the required minimum |
| SWEEP_01 – SWEEP_10 | the ten defect **classes**, scanned over the module: silent enum defaults, reduced composite keys, id-only typed relations, blanket interface exemption, partial geometry, demand-driven applicability, model-local findings, absence beside FAIL, S7-C leakage, candidate crossing |

**Mutation-tested, not only asserted.** Reinstating the axis fallback (1 failure),
collapsing the mobility address (1), exempting every interface (1), letting the
ingester read the preference section (1), and restoring the `DECLARED_`
vocabulary (1) — each reintroduction is caught by the test written for it.

### C.8 Newly discovered, with owners

* **S-8** — `NOT_INTENDED_TO_INTERACT` is declared and unproducible; it is the
  only shape from which `gross_interference` could yield a positive FAIL.
* **S-8** — `assemblability` does not require an AssemblyStep per body, so a
  partial order passes. **Deliberately not fixed here:** under box geometry an
  arriving body always overlaps the one it lands on, so requiring a step per body
  would make the domain `NOT_ESTABLISHED` for every mechanism whose parts touch —
  correct-looking and vacuous. It needs exact geometry, not a rule change.
* **S-8** — `free_dof` silently defaults an unreadable axis to Z. Left alone as
  frozen S-5 behaviour; S7-B now refuses to consume the default, which contains
  the damage without redefining mobility.
* **S7-C** — a hard requirement stated only in the request prose is not ingested.
  Reading it out of prose is the inference `DesignConstraint` exists to avoid, so
  the honest consequence is that the channel is structured-only.
  **This was wrong, and §D fixes it.** The inference to avoid is *deriving* a
  constraint from prose; *capturing* one the user explicitly stated is what s01
  does with every other sentence, and calling the whole thing an inference lost a
  demand rather than protecting one.

Regression, **secondary**: RUN 1019 · PASS 1019 · FAIL 0 · SKIP 22.

---

## S7-B FINAL CORRECTION + SAME-DEFECT-CLASS SWEEP (baseline `1b4ed24`)

Four named blockers, all reproduced before editing, and five more found by the
sweep. One theme runs through every one of them: **something was substituted for
a fact that was named or missing** — another sibling for the one a reference
names, another joint for the one a DOF requires, another route for the one the
design declared, a structured profile for a sentence the user typed.

### D.1 The blockers, reproduced

| | reproduced from `1b4ed24` | root cause |
|---|---|---|
| **1** | request states "All parts must be plastic", no profile → `DesignConstraint: []` | The ingress read `design_profile.design_constraints` and nothing else. A hard requirement the user typed vanished on every design that shipped without a structured file — a family declared authoritative, owned by s01, unreachable from the only input most designs have. |
| **2** | `differs_from: ["CFG-GONE"]`, CFG-GONE nowhere → **PASS** | `[o for o in named if o in realized] or [k for k in realized if k != cid]` — a named reference filtered to nothing, then replaced by whatever else was realized. A reference to an entity the design does not have earned a PASS from an entity nobody named. |
| **3** | group with `JNT-PA` (PRISMATIC X) and `JNT-RA` (REVOLUTE Z), basis on `RZ` → **FAIL** | `driving_joint` returned the first joint whose `child_group` matched, ignoring the DOF half of the address. The slider holds the same value in both configurations, so the arbitrary pick did not merely fail to answer — **it manufactured a positive contradiction and declared a working mechanism infeasible.** |
| **4** | one valid route + one closing internally: `(good, bad)` → FAIL, `(bad, good)` → **PASS** | `paths = {p.load_case: p}` kept whichever was written last. The verdict on a load turned on insertion order. |

### D.2 Five more of the same classes, found by the sweep

* **`Envelope` per body** — `{e["body"]: e["entity_id"]}` in two places. A body
  with two standing extents silently got the last one, and every geometric answer
  rested on a choice nothing made. Now `BODY_ENVELOPED_TWICE` across all four
  geometry-reading domains and the dimensional evaluator.
* **Disposition per cell** — `disposed[(g, c, d)] = ...` kept the last record, so
  whether a required cell read INTENDED or BLOCKED_BY could turn on order. Now
  `CELL_DISPOSITIONED_TWICE`.
* **`State` per configuration** — `state_for` returned the first match. Now
  `CONFIGURATION_REALIZED_TWICE`.
* **Interface expectation per pair** — a pair declared both CONTACT and CLEARANCE
  resolved by insertion order. Now `INTERFACE_EXPECTATION_CONFLICT`, and a
  conflicted pair exempts nothing.
* **`order_index` is not a total order** — two steps sharing an index were
  installed in view order, so which corridor each was tested against depended on
  it. Now sorted by `(order_index, entity_id)` and reported as
  `ASSEMBLY_ORDER_NOT_TOTAL`.
* **Moving-group driver** — `spatial_realization` checked the first joint on a
  moving group and left the others uninspected. Now every joint is checked and
  the ambiguity is reported.

### D.3 The source-capture channel

`capture_design_constraints(parsed)` in s01, beside the profile ingester. Neither
gates the other and B55 asserts they compose.

**THE MODEL TRANSCRIBES; CODE DECIDES.** Classifying a sentence as a material
requirement is reading, which is what s01 asks a model to do everywhere else —
so rule 9 of the prompt asks for it, and the response carries
`hard_constraints[]`, each naming the Requirement it came from. Turning one into
a constraint is not reading, and every gate is a typed fact:

```
kind ∈ DesignConstraint.kinds          (the contract's own vocabulary)
requirement ∈ this response            (traceability is a condition of existence)
quantitative kind ⟹ that requirement's quantity_class == MAGNITUDE
                    and a numeric value in the kind's own parameter
```

That last gate is the one that matters. "Keep it reasonably compact" arrives as a
requirement whose `quantity_class` is NONE — **the model offered it as
`MAX_OVERALL_DIMENSION` in the live run and was refused** — while "no wider than
100 mm" arrives as MAGNITUDE and passes. Neither outcome required a line of code
to look at a word. There is no keyword mining anywhere.

Nothing is completed: a stated limit with no axis is carried with no axis, and
`params.get("axis", "ANY")` — which answered a limit that named no direction by
measuring the largest span — is gone.

### D.4 Multiplicity, stated rather than assumed

The contract does not guarantee one LoadPath per LoadCase, so S7-B defines the
policy rather than assuming uniqueness. Each route is classified alone —
`VALID` / `CONTRADICTORY` / `UNRESOLVED` — and then:

```
any CONTRADICTORY  → FAIL          the design asserts a route that contradicts itself
else any UNRESOLVED → NOT_ESTABLISHED   a declared route it has not shown
else               → PASS
```

No selection of first, last, shortest or lexicographically smallest. B46–B48
assert the verdict **and its premise set** are identical under both insertion
orders.

### D.5 Files changed

| file | change |
|---|---|
| `stages/feasibility.py` | +469/−162: exact `differs_from`, `_resolve_driver` on `(group, dof)`, `_classify_path` + multiplicity policy, five multiplicity guards, no default axis |
| `stages/s01_requirement_capture.py` | +129: prompt rule 9 and the `hard_constraints[]` schema, `capture_design_constraints`, `CONSTRAINT_KINDS`, split id sequences |
| `contracts/DESIGN_STATE_CONTRACT.yaml` | `DesignConstraint.kinds` and `.origins` declared; both channels stated as live |
| `contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml` | `candidate_engineering_evidence` split `by_role` — three roles whose absence is a FINDING were `REQUIRED_NONEMPTY` |
| `contracts/stages/S01_CONTRACT.yaml` | both producers, the source gate, the id note |
| `tests/meta/test_s7_feasibility.py` | +602: B36–B56 and SWEEP_11–15 |

**`s04_envelope_and_motion.py` is untouched this pass**, as are `_propagate`,
the stale semantics and every S-4/S-5/S-6 meaning.

### D.6 A sixth input-boundary defect, found by B49

`candidate_engineering_evidence` declared one `REQUIRED_NONEMPTY` rule for seven
roles, and for three of them it said the wrong thing — the third instance of
exactly this shape in S-7. A candidate that routes no load has `LOAD_PATH_MISSING`
to answer for; the boundary made its whole view `UPSTREAM_INSUFFICIENCY`, so
**nine domains went unanswered in order to hide one finding**. Same for an effect
discharged by nothing, and for a mechanism that blocks nothing — which is an
ordinary mechanism. Split `by_role`; the four whose absence means there is no
candidate to judge stay required.

The probe fixture had been *forcing* a ConstraintRelation to get past that
boundary, with a comment admitting it was testing the fixture. That is gone too.

### D.7 B36–B56, and the sweep

**105 tests.** B36–B39 (source capture: material survives, dimension decides,
preference and vague prose refused), B40–B42 (exact `differs_from`), B43–B45
(driver by `(group, dof)`, ambiguity, no compatible joint), B46–B49 (multiplicity
in both orders), B50–B52 (configuration / joint / load-path permutation ⇒
identical verdict AND premises), B53 (only the sibling compared is read), B54
(provenance back to the sentence), B55 (no profile dependency), B56 (changing a
preference changes nothing, entity for entity), SWEEP_11–15 (named-reference
substitution, single-valued indexes, no expression picking among same-family
entities, the driver address, no hard demand lost).

**Eight mutations, each caught by the test written for it:** restoring the
sibling fallback (1 failure), first-joint driver (3), last-path-wins (4), default
axis (1), removing the source channel (3 + 3 errors), dropping the MAGNITUDE gate
(1), accepting any kind the model names (1).

### D.8 The live chain, from request text alone

s01 → s02 → s03 → s03b → s04a → s04b → feasibility, real invocations, **no
`design_profile` input at all**:

```
Requirements captured : REQ-0001 … REQ-0005
DesignConstraints made: DSC-S001, DSC-S002
   DSC-S001 MATERIAL_CLASS_ONLY    from REQ-0002  locator=line 2
   DSC-S002 MAX_OVERALL_DIMENSION  from REQ-0003  locator=line 3
                                                  {axis:X, limit:100, unit:mm}
   "Prefer fewer parts" and "Keep it reasonably compact" produced nothing

REQ-0002 "All parts must be plastic."
  -> DSC-S001 -> HRC-CND-A-DSC-S001 = NOT_YET_EVALUABLE
REQ-0003 "The assembled mechanism must be no wider than 100 mm."
  -> DSC-S002 -> HRC-CND-A-DSC-S002 = SATISFIED
     premises: BOD-G0A BOD-G1A CND-A DSC-S002 ENV-G0A ENV-G1A SCL-CND-A

SelectionProfile in the feasibility view: False
```

### D.9 Final scope audit

`git diff --check` clean. Six files, all in scope. No producer for any S7-C–F
family (`SelectionProfile`, `CandidateComparison`, `SelectionAdvisory`,
`SelectionConcern`, `HumanDecisionInput`: **0 references in production**;
`SelectionDecision`: 4, all pre-existing readers — the branch resolver and
`selection_gate_check`, which writes nothing). `_propagate` untouched. No
`.gitignoreJoey…` file touched. Every `[0]` in the module is a geometry corner or
sits under an explicit length test; `next(` appears in no code.

### D.10 Still open, with owners

* **S-8** — `NOT_INTENDED_TO_INTERACT` declared and unproducible; the only shape
  from which `gross_interference` could yield a FAIL.
* **S-8** — `assemblability` does not require a step per body. Unchanged and for
  the reason given in §C.8: under box geometry the rule would be correct-looking
  and vacuous.
* **S-8** — `free_dof` defaults an unreadable axis to Z. S7-B now refuses to
  consume that default in **three** places (cell address, distinctness driver,
  disposition support) rather than redefining mobility.
* **S-8** — `configuration_realization_check` (frozen s04) still carries the
  sibling fallback S7-B removed. It reports findings and decides nothing, so it
  can only under-report where feasibility is now exact; relocating checks is S-8's.
* **S7-C** — a hard requirement the source states but s01 does not classify into
  a declared kind stays a Requirement. That is the correct floor: the vocabulary
  is the gate, and widening it is a contract change, not a code change.

Regression, **secondary**: RUN 1052 · PASS 1052 · FAIL 0 · SKIP 22.

---

## S7-B CLOSURE PASS (baseline `b761bbb`)

Two named blockers, both reproduced before editing; two more of the same classes
found by the sweep. Narrow by construction: **no S7-B area was reopened**, and
every existing invariant is asserted unchanged.

### E.1 The two blockers

**Structured profile bypassed the kind vocabulary.** The source channel gated on
`CONSTRAINT_KINDS`; the profile channel took the file's word for it, on the
reasoning that a structured input is already a fact. So a section headed
`design_constraints` could carry `MINIMIZE_PART_COUNT` and make a wish into a
hard requirement **by the one route the other channel is built to refuse**.
Reproduced: `MINIMIZE_PART_COUNT` and `UNKNOWN_CUSTOM_KIND` both ingested. Fixed
with the same call the source channel makes — one table, no second list. Being
structured says a value was not inferred; it does not say the value is one
anything can act on.

**Ambiguity detected and then measured anyway.** `BODY_ENVELOPED_TWICE` was
reported and `_weaken`-ed to NOT_ESTABLISHED — and `_weaken` does not undo a
FAIL, so the arbitrarily-chosen box went on to produce a positive contradiction:

```
order (near, far):  spatial_realization   FAIL   CONNECTED_BODIES_APART
                    load_reaction_closure FAIL   HOP_BODIES_APART
order (far, near):  spatial_realization   NOT_ESTABLISHED
                    load_reaction_closure NOT_ESTABLISHED
```

A recognised ambiguity deciding the verdict, and deciding it differently
depending on which envelope was written last.

### E.2 The quarantine

One strict accessor rather than a detector beside a lookup that ignores it.
`_Evidence.extent_status(body)` answers **UNIQUE / MISSING / AMBIGUOUS**, and
`boxes()` returns only UNIQUE bodies — so an ambiguous body is simply *absent*
from the geometry map and behaves exactly as an unplaced one, which every
predicate already refuses to measure. `envelope_of()` excludes it too, because
naming one of two competing envelopes as a premise would record a dependency on
a record nothing selected.

Nothing had to be added at each FAIL site: the quarantine is upstream of all of
them. `duplicated()` is retired, and the retirement says why — *a detector beside
a lookup that ignores it is worse than neither*.

Reported per body where the body is actually read, not as a blanket prefix, so
B64 holds: a duplicate on a body no load route measures leaves
`load_reaction_closure` PASS **with an unchanged premise set**, while
`spatial_realization` and `gross_interference` — which genuinely read every body
— report it.

`s04._view_boxes` is untouched and still keeps the last envelope per body; it is
s04's own refinement barrier that reads it, and feasibility simply stopped
consuming it for an authoritative verdict.

### E.3 Two more of the same class, found by the sweep

* **A pair described two ways still required a contact.**
  `gross_interference` refused to exempt a pair declared both CONTACT and
  CLEARANCE — and `spatial_realization` went on requiring the contact and
  **FAILING** when the boxes were apart. Being apart contradicts one declaration
  and satisfies the other, so the FAIL reported a broken mechanism where the
  description is what is broken. `pair_expectation()` is now one reader for both
  domains, and a conflicted pair requires nothing it can be held to.
* **Two current ReferenceScales still fed `box_gap`.** `SCALE_AMBIGUOUS` was
  reported by the dimensional evaluator and by nothing else, so two bases could
  produce a geometric FAIL — arithmetic across a boundary nothing defines.
  `boxes()` now returns nothing at all when the basis is ambiguous, which routes
  it through the same quarantine.

The other six recognised ambiguities were checked and are already safe:
`CONFIGURATION_REALIZED_TWICE`, `CELL_DISPOSITIONED_TWICE`,
`DISTINCTNESS_DRIVER_AMBIGUOUS` all `continue` before the comparison;
`ASSEMBLY_ORDER_NOT_TOTAL` and `MOVING_GROUP_DRIVER_AMBIGUOUS` weaken and cannot
reach a FAIL that depends on the tie-break; `SCALE_AMBIGUOUS` returns early in
the dimensional evaluator. None was reopened.

### E.4 B57–B64

| | |
|---|---|
| B57 | three unsupported profile kinds → no `DesignConstraint` |
| B58 | a declared kind → ingested with source, statement, parameters and `blocks_selection` exact |
| B59 | both channels consult `CONSTRAINT_KINDS.get(` — asserted structurally *and* behaviourally, same kind and same refusal through either door |
| B60 | doubled extent + load route → `NOT_ESTABLISHED` in both orders, no `HOP_BODIES_APART` |
| B61 | → `NOT_ESTABLISHED`, no `CONNECTED_BODIES_APART` |
| B62 / B62b | → `NOT_ESTABLISHED`, no `NO_CONSERVATIVE_OVERLAP`, no `ORDER_CONSISTENT_AND_PATHS_CLEAR` |
| B62c / B62d | *(sweep)* conflicted pair requires no contact; two bases measure nothing |
| B63 / B63b | doubled extent → `NOT_YET_EVALUABLE` in both orders; one extent each still decides SATISFIED |
| B64 | an unrelated doubled extent does not contaminate — same verdict **and same premises** |

**117 tests.** Five mutations, each caught by the test written for it: removing
the profile gate (2 failures), removing the source gate (1), restoring
last-envelope-wins (5), letting a conflicted pair require a contact (1),
measuring across two bases (1).

### E.5 Files changed

`feasibility.py` (+228/−69 — the quarantine, `pair_expectation`, `_extent_finding`),
`s01_requirement_capture.py` (+13/−4 — the profile gate), three contracts stating
the two invariants, and the tests. **No S4/S5/S6 production, no `_propagate`, no
view module.**

### E.6 Scope audit

`git diff --check` clean. Six files. Zero references to `SelectionProfile`,
`CandidateComparison`, `SelectionAdvisory`, `SelectionConcern` or
`HumanDecisionInput` in production; `SelectionDecision` appears only in the three
pre-existing readers. No `.gitignoreJoey…` file touched. No hidden default was
introduced — the fix makes geometry *unavailable*, which is the opposite of a
default.

Regression, **secondary**: RUN 1065 · PASS 1065 · FAIL 0 · SKIP 22.

---

## S7-C — DETERMINISTIC SELECTION SUBSTRATE (baseline `4cc10f8`)

S7-B asked "can this candidate work" one candidate at a time. S7-C asks the one
question no single branch can answer — how the retained alternatives compare —
and it asks it of one accumulated DesignState. **It does not choose.** Every
outcome is a statement about the evidence, and the commitment is a human's.

### F.1 Production architecture

`ver3/assy_v3/stages/selection.py`, named for the responsibility as `feasibility`
is. Two deliberate phases:

```
materialize_selection_profile(state, selection_preferences) -> SelectionProfileOutcome
        ↓  apply through DesignState
evaluate_candidate_comparison(state)                        -> SelectionComparisonOutcome
```

The profile must be in state before the view is built. Building the view first
and special-casing the missing profile would make the preference a side channel
rather than the authoritative snapshot it is. No provider, no prompt, and
`evaluate_candidate_comparison` takes **no invocation and no branch** — the
question is design-wide, so there is no parameter through which one alternative's
private state could arrive (C57).

### F.2 The orchestration defect, reproduced and fixed

`run_s03` did `state = copy.deepcopy(base_state)` per candidate, so a run ended
with **N private designs and no design**. Selection compares retained
alternatives; there was nothing to compare, and merging two entity dictionaries
would have bypassed the write boundary that makes an entity authoritative.

Isolation between candidates was never the state's job — it is the ConsumerView's,
which is branch-scoped by construction. Copying the state to get isolation solved
a solved problem in the one place that also destroyed the design-wide question.
The copy is gone; every candidate is embodied into one accumulated state, and
`run_selection` is called once per case after the last alternative is in.

### F.3 Profile materialisation

| | |
|---|---|
| `source_hash` | SHA-256 over the canonicalized preference mapping **alone**. Key order is not meaning, so the same preferences in any order are the same snapshot and the same entity id (`SPF-<hash>`). No counter exists. |
| idempotent | calling twice returns `PROFILE_UNCHANGED` and writes nothing |
| changed preferences | the standing profile is INVALIDATED, not overwritten; the comparison built on it goes STALE by ordinary propagation |
| malformed | an invalid objective or priority rejects the **whole** snapshot — dropping the bad criterion would record a preference set the user never stated |
| unknown criterion name | **preserved**. The user may want something this pipeline cannot measure, and the registry answers NOT_AVAILABLE rather than the profile forgetting the request |
| no source | `NO_SELECTION_PREFERENCES`, no profile. Inventing one would invent the user's answer |
| explicitly empty | a real snapshot of "nothing ranked" — one eligible candidate is SOLE_ELIGIBLE, several are TRADEOFF_UNRESOLVED |
| already ambiguous | more than one standing profile refuses comparison rather than picking |

### F.4 Eligibility, and the population rule

Read from upstream truth and never recomputed. `eligibility(ev)` **has no
parameter through which a preference could arrive**, and its body names no
criterion, objective or priority — asserted structurally, which is C-I1 in its
strongest form.

```
no current MFA            → UNRESOLVED
two current MFAs          → UNRESOLVED          (never first-wins)
MFA != FEASIBLE           → INELIGIBLE          (no compliance record needed:
                                                 the prerequisite already failed)
blocking HRC missing/dup  → UNRESOLVED
any blocking VIOLATED     → INELIGIBLE
any blocking not SATISFIED→ INELIGIBLE at current maturity
otherwise                 → ELIGIBLE
```

`blocks_selection` absent is **true**, the contract's declared default.
Non-blocking constraints do not affect eligibility, and every constraint is a
premise because whether it blocks is the fact being used.

**Any** unresolved candidate makes the population unestablished and **no
CandidateComparison is written at all**. `known ineligible` and `eligibility
unknown` are different facts.

### F.5 Metric registry

| supported | means | unit |
|---|---|---|
| `rigid_body_count` | candidate-relevant standing Body count | count |
| `joint_count` | candidate-relevant standing Joint count | count |
| `package_volume` | volume of the box enclosing the **whole** candidate | `<unit>^3` |

`package_volume` requires every candidate body to have exactly one usable extent
on exactly one ABSOLUTE basis with a stated unit and `per_unit` — missing,
doubled, relative or unfactored geometry is NOT_AVAILABLE, never approximate. It
is not the sum of the bodies' boxes: two 20 mm cubes 15 mm apart enclose 14 000
mm³ where the sum is 16 000 (C26b).

Everything else — `part_count`, `assembly_complexity`, `actuation_complexity`,
`maintainability` — is `NOT_AVAILABLE` / `NO_CANONICAL_METRIC_SOURCE`. A Body is
not a manufactured part and a Joint is not an actuator, however well they
correlate, and no alias exists in the table.

Branch partitioning is `branch_membership`, the canonical helper, applied only to
ids the view already admitted. Nothing is inferred from an id's spelling, its
position or the order it was created in.

### F.6 Comparison

```
1 eligible                → SOLE_ELIGIBLE
tier: any metric missing  → NOT_COMPARABLE at that tier, no lower-tier fallback
tier: one dominates       → DOMINANT_UNDER_PROFILE
tier: exact tie           → descend to the next tier
tier: genuine tradeoff    → TRADEOFF_UNRESOLVED at that tier, STOP
all tiers exhausted       → TRADEOFF_UNRESOLVED
```

Pareto dominance per criterion on its own objective. `compare`, `_dominates` and
`_better` contain **no arithmetic across criteria at all** — asserted from the
AST — so there is no weight, no normalization and no utility function to hide one
in. No candidate id, insertion order or criterion order is ever consulted.

### F.7 Dependencies

`CandidateComparison.premise_refs` carries, directly: the profile; every
Candidate; every MFA read; every DesignConstraint whose `blocks_selection` was
inspected; every blocking HRC required; and the exact source facts of every
metric computed. Because propagation is one hop, premising the profile and the
assessments would leave the record standing when an envelope a volume was
measured from is superseded.

Exactness both ways: a `joint_count`-only comparison does **not** premise
envelopes or scales (C43), a `package_volume` one does (C42/C44), an excluded
candidate's MFA changing **does** stale it because the population may have moved
(C46), and an unrelated fact does not (C45).

### F.8 In-scope defects found and fixed during the pass

* **The runner's per-candidate `deepcopy`** — §F.2. Without it there is no
  accumulated state and C-I9 is unimplementable.
* **`candidate_spatial_evidence` demanded `reach_evidence` and
  `elimination_evidence`** as REQUIRED_NONEMPTY — the fourth appearance of this
  shape in S-7. A design whose actors reach for nothing produces no ReachResult
  and a candidate nobody eliminated produces no EliminationRecord, so the
  selection view was UPSTREAM_INSUFFICIENCY on an ordinary design and the
  comparison could not be asked at all. Neither is read by any metric. Split
  `by_role`; `spatial_commitment` stays required.
* **Selection could not see the design-wide `DesignConstraint` set** — reaching
  constraints only through the compliance records that cite them would make a
  MISSING blocking record invisible, which is precisely the case C-I2 exists to
  detect. Added the `hard_design_constraint` premise class.
* **No topology in the view** — `rigid_body_count` and `joint_count` are counts
  of canonical entities. Added `candidate_topology_evidence` by engineering role,
  not by a family list written for this consumer.
* **`ENTITY_FAMILY_AUDIT` claimed both families were unproduced.**

### F.9 C01–C57

**68 tests** in `test_s7_selection.py`, all against the real ConsumerView and the
real write boundary. C01–C09 profile; C10–C19 eligibility over five candidates
(A/B eligible, C infeasible, D violated, E unevaluable); C20–C31 metrics;
C32–C41 dominance; C42–C48 dependency and lifecycle; C49–C51 population edges;
C52–C57 authority and the design-wide runner. C11 runs the same design under four
opposite preference sets and asserts the eligible set is byte-identical.

**Ten mutations, each caught by the test written for it:** preference reaching
eligibility (2 failures), `part_count` answered by the Body count (2),
NOT_AVAILABLE as infinity (2), MEDIUM resolving a HIGH tradeoff (1), first MFA
wins (1), first HRC wins (1), candidate id breaking a tie (2), reading raw state
instead of the view (1), premising the whole view (2), the runner computing the
winner (1).

### F.10 Scope audit

`git diff --check` clean. Zero production references to `SelectionAdvisory`,
`SelectionConcern` or `HumanDecisionInput`; `SelectionDecision`'s four are the
same pre-existing readers as before this pass, and `selection.py` names none of
them. `_propagate` untouched. No S4/S5/S6/S7-B production file changed. No
`.gitignoreJoey…` file touched.

Regression, **secondary**: RUN 1133 · PASS 1133 · FAIL 0 · SKIP 22.

---

## S7-C CORRECTION PASS (baseline `853e42f`)

Two runtime blockers, both reproduced before editing. The structure was right;
both defects were at a **boundary** — one where the orchestration handed the
materialiser its input, one where two established values met.

### G.1 An explicit empty profile did not survive the runner

The frozen semantics distinguish "no preference source" from
`selection_preferences: {}` — the second is the user saying they have a snapshot
and nothing in it is ranked. The materialiser always understood the difference.
The orchestration threw it away first:

```
no profile at all           -> None
profile with no key         -> None
selection_preferences: {}   -> None      ← the same as "no source"
```

`{}` is falsy, so `profile.get("selection_preferences") or None` collapsed it.
**Presence and value are different questions and truthiness cannot tell them
apart.** `selection_preferences(profile)` now reads by key presence, and `main`
calls it. Explicit `{}` reaches the materialiser, becomes a real versioned
profile with `criteria == {}`, and two eligible candidates under it come out
`TRADEOFF_UNRESOLVED` — not whichever sorts first.

### G.2 Metric values were compared across incompatible units

`package_volume` records a value **and a unit**, and `compare` read only the
value. Reproduced live, with the two candidates' arrangements stated on different
bases:

```
CND-A  AVAILABLE  14000.0 mm^3
CND-B  AVAILABLE  7.776   cm^3
outcome: DOMINANT_UNDER_PROFILE   frontier: ['CND-B']
```

`7.776 < 14000` is arithmetic, not physics. The verdict happened to be right for
these numbers and would have been wrong for `1000 mm^3` against `2 cm^3`.

The fix is at the comparison layer, where it belongs: **the incompatibility is a
property of the PAIR, not of either record** — both metrics are perfectly
AVAILABLE, each computed correctly from its own basis. Before dominance, every
criterion of the tier being evaluated must hold one unit across the frontier;
otherwise the tier stops as `NOT_COMPARABLE`, and `incomparable_criteria` on the
record says which criterion did not meet.

**No conversion was invented.** Nothing in this repository is an authority on
what one unit is worth in another, and a table here would have made this file
that authority. C64c asserts it structurally: the four functions that decide an
ordering contain no numeric literal other than 0 and 1.

### G.3 One more C-I violation, found and fixed in the same pass

The runner recorded `NO_SELECTION_PREFERENCES`, `ELIGIBILITY_NOT_ESTABLISHED`
and `NO_ELIGIBLE_CANDIDATES` as `CONTRACT_CONDITION` **failures**, because each
carries problems explaining itself. That made "the design has nothing to choose
between" indistinguishable from "the pipeline is broken" — a runner changing an
already-frozen S7-C meaning, which is §5's third audit class. It now classifies:
a result is not a failure, and a missing profile is a result only when no
preference was stated.

### G.4 C58–C64

| | |
|---|---|
| C58 | explicit `{}` through the real runner → `PROFILE_WRITTEN`, one standing profile, `criteria == {}` |
| C59 / C59b | `None` and a document with no key → no profile, no failure; the extractor reads presence, and its body contains no `or None` |
| C60 | explicit `{}` + two eligible → `TRADEOFF_UNRESOLVED`, frontier `[A, B]`, no decision |
| C61 / C61b | `1000 mm^3` vs `2 cm^3` → `NOT_COMPARABLE` at HIGH, and the answer is the same whichever candidate holds the odd unit |
| C62 / C62b | same unit still compares; `count` is always commensurate |
| C63 | MEDIUM discriminates cleanly and does not get to |
| C64 / C64b / C64c | an unreached LOW mismatch cannot undo a resolved HIGH; the live record names `package_volume` as incomparable with `unavailable_criteria` empty; no conversion factor exists |

### G.5 Bounded audit

**Presence/value collapse** — every `or {}` / `or []` / `or None` in the
selection path reviewed. All are constructor defaults or absent-vs-empty reads
where the two forms mean the same thing; none collapses a state the S7-C contract
distinguishes.

**Metric comparability** — all three registered metrics emit an explicit unit on
every AVAILABLE record (`count`, `count`, `<unit>^3`), and the gate runs before
any ordering.

**Runner/component mismatch** — `run_selection` contains none of `eligibility(`,
`compare(`, `evaluate_metric(`, `METRIC_REGISTRY`, `_dominates`, `Metric(` or
`incomparable_criteria(`. Fixed the one mismatch found (§G.3).

### G.6 Files changed

`tools/run_window2.py` (the extractor, the result/failure classification),
`assy_v3/stages/selection.py` (unit gate, `incomparable_criteria`),
`contracts/DESIGN_STATE_CONTRACT.yaml` (the field and the rule), and the tests.
No `_propagate` change, no S7-B production file, no S4/S5/S6 semantic change.

Regression, **secondary**: RUN 1145 · PASS 1145 · FAIL 0 · SKIP 22.

---

## S7-D — LLM ENGINEERING ADVISORY (baseline `fe87859`)

The first model call after the deterministic substrate, and the whole of its job
is the question no registered metric can answer. **It decides nothing.**

### H.1 Production architecture

`ver3/assy_v3/stages/selection_advisory.py`, class
`SelectionEngineeringReview`, with `stage_id = "selection"` and
`pass_id = "selection_advisory"` — a SECOND CONSUMER PASS of one owner, exactly
as s03a/s03b are. It is a separate pass because the deterministic comparison is
its INPUT: making `CandidateComparison` a required premise of the `selection`
view would demand the entity before the pass that creates it could run.

It goes through the ordinary `Stage` boundary and builds no parallel caller, so
it inherits view-sufficiency enforcement (the provider is not called on an
unready view), provider status handling, JSON parse handling, the recorded
ConsumerView, and normal write validation.

### H.2 The advisory ConsumerView

Six premise classes: the comparison (`selection_evidence`, REQUIRED_NONEMPTY —
with none the provider is never reached), the profile it was made under, the
eligibility evidence, the reviewable engineering state, the design-wide hard
constraints and the open items.

The engineering class is declared `by_role`, because the absences are
legitimate: `topology_element`, `topology_relation`, `spatial_commitment` and
`mobility_disposition` are REQUIRED_NONEMPTY; `motion_path`, `motion_occupancy`,
`physical_interaction`, `load_route`, `assembly_order` and `reach_evidence` are
MAY_BE_EMPTY. A static mechanism, a design with no actor and a candidate with no
load case are ordinary — and S-7 has already made the mistake of demanding each
of those and rendering a view unready for a question it could have answered.

### H.3 The model schema, and what it may not carry

```json
{"recommendation": {"kind": "PREFER_CANDIDATE|NO_CLEAR_PREFERENCE",
                    "candidate": "id or null"},
 "reasoning": "...", "sensitivity": "...",
 "concerns": [{"candidate", "issue", "importance", "evidence_status",
               "supporting_refs"}]}
```

Exactly four top-level keys and five concern keys, pinned by test. A response
carrying `selected_candidate`, `eligibility`, `feasibility`,
`hard_requirement_status`, `score`, `weighted_score` or `selection_decision` is
**discarded whole** — not trimmed. A model that tried to author a verdict here
may have tried where nothing checks.

### H.4 What the producer owns, so the model cannot

| field | derived from |
|---|---|
| `candidates` | copied from `CandidateComparison.candidates` |
| `comparison` | the comparison's own id |
| `comparison_alignment` | the comparison's outcome and frontier — `comparison_alignment(comparison, recommended)` takes no other parameter |
| `recommended_candidate` | validated against the population; omitted, not null, when there is none |
| every entity id | content hashes, no counter |

`PREFER_CANDIDATE` requires a candidate and `NO_CLEAR_PREFERENCE` forbids one; a
frontier of one gives ALIGNS or DEPARTS, and a frontier of several gives
NO_DETERMINISTIC_PREFERENCE whatever the reviewer says. **Departing is legal and
explicit** — that is what a reviewer is for; what is forbidden is departing
silently.

### H.5 Evidence calibration

`SUPPORTED_BY_STATE` with no reference that is current in the reviewed view is
downgraded to `PLAUSIBLE_NOT_ESTABLISHED`, with `evidence_note` recording why.
**Downgraded, not rejected** — the reviewer may well be right that it matters,
and losing the concern would lose the engineering. It is never raised the other
way: refs happening to resolve is not the same fact as those refs supporting the
claim. A fabricated id is dropped before it can enter state, and dropping it is
what triggers the downgrade.

### H.6 Dependencies

`invocation_premises` returns `visible_ids(payload)` — **the exact provider
exposure**, so every entity serialized into the prompt becomes a premise of
everything the call authors. Deliberately broader than the refs the model cited:
a deterministic stage knows which fields it computed from, a model can use
anything it was shown, and premising only the citations would be a currentness
claim the reviewer never made. `supporting_refs` answers "what supports this
concern"; `premise_refs` answers "what could have shaped this text". Different
questions, and D36/D37/D42 assert the distinction.

### H.7 D01–D55

**55 tests** in `test_s7_advisory.py`, all against the real Stage boundary with
canned and failing providers. Sequencing D01–D05 (no comparison ⇒ zero provider
calls; two comparisons ⇒ zero; the comparison must be applied, not merely
computed). Population D06–D10. Response authority D11–D14. Recommendation
D15–D22. Empty profile D23–D24. Evidence D25–D32. Hallucination boundary
D33–D35. Dependency D36–D42. Provider D43–D48. Runner and scope D49–D55.

**Nine mutations, each caught by the test written for it:** recommending an
excluded candidate (1 failure), letting the model author the population (1),
keeping SUPPORTED_BY_STATE with no refs (2), allowing a fabricated ref (1),
premising only the citations (3), letting the model author the alignment (1
after the gap it exposed was closed), creating a decision from the
recommendation (1), calling the provider with no comparison (1), letting the
runner normalize the output (1).

### H.8 In-scope defects found and fixed during the pass

* **A null reference is not an absent field.** `recommended_candidate: None` was
  refused by the write boundary — correctly: a declared reference holding None is
  a reference to nothing, and `NO_CLEAR_PREFERENCE` means the reviewer named
  nobody. The field is now omitted.
* **Advisory identity moved with concern order.** The id hashed the raw response,
  so reordering the concern list produced a new advisory and, through it, new
  concern ids — a reordering looking like new engineering. The hash is taken over
  a normalized response.
* **Nothing asserted that the model could not author the alignment.** Found by
  the mutation pass rather than by the tests: widening the response keys and
  reading `alignment` from the model went undetected. D11b and D11c close it.
* `ENTITY_FAMILY_AUDIT` claimed both families were unproduced.

### H.9 Bounded D-I1…D-I12 audit

`Op(CREATE, …)` appears for exactly two families. The module contains no
`state.family(`, `state.standing(`, `state.entities`, `DesignState` or
`request_text` — it reads `inputs[context_key]` and nothing else, so the reviewer
sees only the recorded view and there is no second channel. Zero references to
`SelectionDecision`, `HumanDecisionInput`, `UnresolvedDecision`, `MFA`, `HRC` or
`FeasibilityDomainAssessment`. All three `[0]` subscripts sit under an explicit
length test. D41 asserts entity-for-entity that a review disturbs no
deterministic record; D55 recomputes the whole population after one.

### H.10 Scope

No `HumanDecisionInput` producer, no `SelectionDecision` producer, no UI, no
S7-F machinery. `_propagate` untouched. S7-B and S7-C production files untouched.

Regression, **secondary**: RUN 1202 · PASS 1202 · FAIL 0 · SKIP 22.

---

## CURRENT STATUS

> **S7-D VERIFIED CLOSED — LLM REVIEW IS ELIGIBLE-POPULATION-BOUND,
> EVIDENCE-CALIBRATED, NON-AUTHORITATIVE AND DECISION-SAFE.**
>
> The provider cannot be reached without one current comparison, and the
> population the reviewer may speak about is copied from it — a response naming
> anyone else is discarded whole rather than trimmed. Nothing the model writes
> touches eligibility, the comparison or a decision, and the eligible set is
> asserted entity-for-entity across a review that argues against it. A
> recommendation is machine-readable, names only an eligible candidate, and its
> agreement or disagreement with the deterministic frontier is computed rather
> than claimed. A concern may be important and unestablished at once; claimed
> state support without a current reference is downgraded rather than lost, and a
> fabricated citation never enters state. What the review depends on is what the
> model was SHOWN, not what it chose to cite — so a fact it read changing costs it
> its standing, while rewording it costs the engineering nothing.
>
> **S-7 / U-8 IS NOT CLOSED.** S7-E and S7-F are not started.

---

## S7-C FINAL STATUS

> **S7-C VERIFIED CLOSED — LIVE PROFILE SEMANTICS AND CROSS-CANDIDATE METRIC
> COMPARABILITY ARE CONSISTENT.**
>
> An explicit empty preference snapshot survives the real orchestration as a real
> versioned profile, and an absent source still creates nothing — because the
> runner reads presence rather than truth. Two established metric values are never
> ordered across units that do not meet: the incompatibility stops the tier being
> evaluated, a lower tier cannot bypass it, an unreached tier cannot undo a result
> already established above it, and no conversion factor exists anywhere in the
> comparison. Every S7-C invariant from the previous pass holds unchanged.
>
> **S-7 / U-8 IS NOT CLOSED.** S7-D, S7-E and S7-F are not started.

---

## S7-C FIRST-PASS STATUS (superseded by the above; kept, not deleted)

> **S7-C VERIFIED CLOSED — ELIGIBILITY POPULATION, VERSIONED PREFERENCES,
> CANONICAL METRICS AND TIERED DETERMINISTIC COMPARISON CONSISTENT.**
>
> A preference enters state once, at the selection boundary, as a content-hashed
> snapshot no earlier consumer can see — and it cannot reach eligibility, which is
> read from upstream truth by a function that has no parameter through which one
> could arrive. Every retained candidate is accounted for before anything is
> compared, and one whose eligibility is unknown stops the comparison rather than
> vanishing from it. Three metrics measure exactly what they are named for and
> everything else stays NOT_AVAILABLE, which is neither an advantage nor a
> disadvantage. Tiers are evaluated HIGH then MEDIUM then LOW, a lower one reached
> only after an exact tie, and a genuine tradeoff stays a tradeoff. There is no
> weighted score and no tie-break of any kind. The comparison names the raw facts
> it used, and it runs on one accumulated design that every candidate was embodied
> into.
>
> Superseded in scope by §G: the orchestration collapsed an explicit empty
> preference snapshot, and the comparison ordered values across units that do not
> meet. Every claim above still holds.

---

## S7-B FINAL STATUS

> **S7-B VERIFIED CLOSED — ALL HARD-CONSTRAINT INGRESSES SHARE ONE VOCABULARY
> AUTHORITY AND AMBIGUOUS GEOMETRY CANNOT PRODUCE AUTHORITATIVE VERDICTS.**
>
> A hard requirement enters through two doors and both ask the same table what a
> kind means, so a preference cannot become a constraint by arriving in a
> structured file. A body the design describes twice has no extent any verdict
> may use — not a noted duplicate beside a box that still measures, but no box at
> all — and the same holds for a pair described two ways and for coordinates
> stated in two bases. Every domain answers `NOT_ESTABLISHED` there, in either
> insertion order, and a duplicate on a body a domain does not measure changes
> neither its verdict nor its premises.
>
> **S-7 / U-8 IS NOT CLOSED.** S7-C through S7-F are not started.

---

## S7-B FINAL-CORRECTION STATUS (superseded by the above; kept, not deleted)

> **S7-B VERIFIED CLOSED — EXPLICIT HARD DEMANDS, EXACT REFERENCES, COMPOSITE
> ADDRESSES AND MULTIPLICITY ARE DETERMINISTIC.**
>
> A hard requirement the user typed into the request survives with no structured
> profile anywhere, traceable back to the sentence that created it, and a
> preference cannot become one through either channel. A named reference resolves
> exactly or becomes unresolved — no sibling stands in for the one a basis names.
> A requirement addressed to `(group, dof)` is answered by the joint that carries
> that DOF or by nothing, and two candidates for it are an ambiguity rather than a
> pick. Every declared load route is evaluated, and the verdict and its premises
> are identical under any insertion order. Six single-valued indexes that kept
> whichever record came last now report the duplicate instead of resolving it.
> Missing evidence is still never replaced with convenient evidence.
>
> Superseded in scope by §E: reporting a duplicate is not quarantining it, and
> the profile channel was still taking a file's word for what a hard requirement
> is. Every claim above still holds.

---

## S7-B CORRECTION-PASS STATUS (superseded by the above; kept, not deleted)

> **S7-B VERIFIED CLOSED — DETERMINISTIC FEASIBILITY, DEMAND-DRIVEN
> APPLICABILITY, TYPED PHYSICAL SEMANTICS AND HARD-CONSTRAINT EVALUATION
> CONSISTENT.**
>
> An explicit hard requirement enters through s01's own invocation and comes out
> the other end as a compliance record. Applicability is read from the demand, so
> a candidate cannot escape a domain by declining to build the thing that domain
> examines. A mobility cell is addressed by all three of its components. An
> interaction discharges an obligation only if it produces that obligation's
> effect, and a disposition is supported only if the joint it cites really frees
> that cell. `CLEARANCE` cannot hide a conservative overlap, and a dimensional
> limit cannot be answered from a partial arrangement or an unrecognised axis.
> Missing evidence is still never PASS and a conservative overlap is still never
> FAIL. The contracts describe what runs, and each defect class is a standing
> test rather than a fixed line.
>
> Superseded in scope by §D: this pass read only the structured profile, so a
> hard requirement typed into the request disappeared; and it still substituted
> another entity for a named one in four places. Every claim above still holds.

---

## S7-B FIRST-PASS STATUS (superseded by the above; kept, not deleted)

> **S7-B VERIFIED CLOSED — DETERMINISTIC, CANDIDATE-LOCAL MECHANICAL FEASIBILITY
> AND HARD-REQUIREMENT EVALUATION CONSISTENT.**
>
> Nine domain policies are machine-readable, dispatched from one table and tested
> one at a time. No missing evidence becomes PASS and no conservative overlap
> becomes FAIL. A `ReachResult` and an `EliminationRecord` contribute a reason
> code and decide nothing. A hinge and a four-bar that both work get the same
> answer. Every record's premise set is exactly the current positive facts it
> read — asserted as an equality in both directions, with the raw union carried
> directly because propagation is one hop. Hard requirements answer
> NOT_YET_EVALUABLE where the design has not yet said, and never guess. The
> evaluator reads the real ConsumerView and refuses to produce a patch without
> one. No provider is called.
>
> Superseded in scope by §C: this pass had built the consumer without the
> producer, read applicability off the realization rather than the demand, and
> accepted three typed references on their ids alone. Every claim above still
> holds; what it did not yet say is recorded there.

---

## S7-A STATUS (superseded by the above only in scope, not in content)

> **S7-A VERIFIED CLOSED — AUTHORITY, INPUT SUFFICIENCY, ORDERING,
> HARD-CONSTRAINT SEMANTICS AND PREFERENCE ISOLATION CONSISTENT.**
>
> Every canonical file and projection now agrees on `s04a → s04b → feasibility →
> selection`. Feasibility is candidate-local and preference-blind, and its view
> carries the evidence its declared domains are decided on. A hard requirement is
> authoritative from s01 and visible only where the reasoning asks for it, and
> recording one a user stated is required where inventing one is forbidden.
> `SelectionDecision` is owned by `selection` alone and no stage projection
> claims it. Nothing requires a decision before s04b, and the rule that would
> have is retired rather than waiting. Advisory material is considered, never
> premise. The sweep that found this residue is a test now, so a reintroduction
> fails rather than waiting for someone to look.
>
> Recorded at the time as "S7-B through S7-F are not started". S7-B is now built;
> §B.3 records the three input-boundary defects it found in the contract this
> pass froze, each of the same kind S7-A had already fixed once.
