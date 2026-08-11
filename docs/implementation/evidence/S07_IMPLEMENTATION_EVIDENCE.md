# IMPL S-7 / U-8 — FEASIBILITY AND SELECTION

Baseline `9f98cbc`. S-3, S-4, S-5 and S-6 are closed and are not reopened.

This step is planned in six substeps (§20). **This document records S7-A and
S7-B.** S7-C through S7-F are not started.

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

## CURRENT STATUS

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
> **S-7 / U-8 IS NOT CLOSED.** S7-C through S7-F are not started.

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
