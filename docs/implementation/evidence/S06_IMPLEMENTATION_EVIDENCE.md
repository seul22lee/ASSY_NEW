# IMPL S-6 / U-7 — SPATIAL COMMITMENT AND REFINEMENT

Baseline `3704432`. S-3, S-4 and S-5 are closed and are not reopened; the frozen
invariants are re-checked here, not revised.

---

## 1. PRE-FLIGHT — REPRODUCED BEFORE EDITING

| | condition | reproduced |
|---|---|---|
| **A** | direct `S04A.invoke()` vs the runner | the runner's `_commit_s04` added `SCL-0001`, `RCH-0001`, `ELM-0001` and EXTENDed `FunctionalRegion.volume` and `AssemblyStep.insertion_direction` **after the stage returned**. Direct invoke produced `Envelope` and nothing else |
| **B** | direct `S04B.invoke()` | `Joint.frame_origin` absent; only the runner wrote it |
| **C** | motion evidence | `sampling_declaration` written in `to_operations` from `SAMPLES = 9` before any sweep ran; `sampling_declaration_check` validated `SAMPLES - 2 >= 1`; `swept_clearance_check` read its density back **out of the declaration** |
| **D** | axis | `axis = str(... or "+Z")` and `AXIS_INDEX.get(..., 2)` at two more sites — a missing axis, an unrecognised axis and a genuine Z axis reached the geometry as one fact |
| **E** | arrangement as a premise | `prior_spatial_commitment` **was** declared REQUIRED_NONEMPTY — against `COMMITTED_BRANCH`, which made it unsatisfiable |
| **F** | configuration distinctness | `Configuration` had no distinguishing basis, `Transition` no changed coordinates, and no check compared coordinates at all |
| **G** | LoadPath | `load_path_reaction_check` filtered hops by membership in the **body**-keyed envelope map. With canonical Interface hops every hop was discarded: on bodies 9 units apart it returned `[]`; the identical geometry with body-id hops returned a finding |
| **H** | sequencing | `committed_branch(state) -> None`, so `COMMITTED_BRANCH` selected nothing and the s04b ConsumerView was `UPSTREAM_INSUFFICIENCY` on every call. **S04B was unreachable** |

> **GO — bounded U-7 migration is coherent.** Every condition is U-7 work named in
> plan M-8; none contradicts a frozen rule.

---

## 2. SEQUENCING DECISION

The plan is explicit: *"Does selection/gating wait for the semantics it evaluates?
**Yes** — U-8 (S-7) follows U-7 (S-6)"*, and S-6's own deferred column reads "the
selection gate (U-8)". The responsibility contract had encoded the **post**-gate
runtime state, which is why the stage the step exists to migrate could not run.

- every branch-scoped s04b premise resolves against `INVOCATION_BRANCH`;
- `selection_decision` moves to `premise_classes_pending_step`, keeping its
  `COMMITTED_BRANCH` population and gaining `activated_by: "S-7 / U-8"`. The view
  builder does not read that key, so it enforces nothing and asserts nothing;
- the branch is **named by the caller** — no fabricated `SelectionDecision`, no
  declaration-order inference, no gate.

S-7 moves the class back and restores the population. Nothing below depends on
which population supplied the branch, so the refinement semantics are untouched.

---

## 3. CANONICAL S04 OWNERSHIP

`tools/run_window2._commit_s04` is **retired**. Every fact it wrote is authored by
the stage that concluded it, in that stage's own patch, through a three-way split
made explicit on `Stage`:

| hook | act |
|---|---|
| `to_operations(parsed, inputs)` | what the stage **creates** |
| `refinement_operations(parsed, inputs, state)` | what it **EXTENDs or SUPERSEDEs** on entities that already exist |
| `derived_operations(parsed, inputs, state)` | class-B **recomputation** |

`to_operations` gained `inputs` because a stage that mints an id needs to know
which invocation it is serving: `SCL-0001` and `ELM-0001` were module constants,
so a second candidate collided and could not have a scale or an elimination
record at all — the `MEX-0001` defect S-5 found, in another family. Ids are keyed
to the branch.

`G1` compares the full canonical DesignState of a direct invoke against a runner
run and requires them **equal**. `G11` requires every family and field the retired
writer used to author to appear in a stage patch.

---

## 4. S04A → S04B COMMITMENT AND REFINEMENT

`Envelope.commitment_class` is required, from the frozen vocabulary
(`PROVISIONAL · COMPARABLE · AUTHORITATIVE · OVERTURNABLE_WITH_REASON`). s04a
commits **COMPARABLE**: the arrangement exists so alternatives can be compared on
it.

s04b does one of two things, and the difference is the whole of U-7. It **extends**
— placing a joint origin, which s04a left open and which contradicts nothing — or
it **supersedes** an envelope with a `geometric_reason`, keeping both values. A
revision with no reason is **not applied** and is reported as incompleteness.

Every s04b spatial output carries the envelopes and the reference scale it rests
on in `Op.premise_refs` — the existing substrate, no second provenance system. So
`G3`: superseding one committed extent turns the `State`, the `Transition` and the
`SweptVolume` that rested on it **STALE**, and an unrelated branch's supersession
does not.

---

## 5. JOINT FRAME AND AXIS

`axis_index(axis)` returns `None` for a missing, empty, `NONE` or unrecognised
axis, and every consumer refuses rather than substituting. `rotate_about_axis`
raises rather than rotating about a fabricated axis. `sweep_hull` returns
`computable: False` with a reason and **no hull**. `joint_frame_check` reports a
placed joint whose axis names no coordinate; a FIXED joint legitimately has none
and is not asked. The s04b prompt says the axis is already fixed by the topology
and that a joint without one cannot be given one here.

---

## 6. CONFIGURATION AND TRANSITION REALIZATION

`Configuration.distinguishing_basis` — `{rigid_group, dof, differs_from}` — is
**optional and s03-authored**, because what makes two states different is a
mobility statement. `configuration_realization_check` is conditional on the
declaration: never "all configurations must differ", which would be a rule about
products. No state name appears anywhere; the basis names a group and a DOF, and
the joint driving that group carries the coordinate.

`Transition.changed_coordinates` is a declared **reference to Joint** — the field
holds joint ids, not coordinates. `transition_realization_check` compares it to
the endpoint states in both directions: a declared change the endpoints do not
make, and a change that happens undeclared.

---

## 7. MOTION EVIDENCE

`sampling_declaration` **left** `Transition`. The evidence lives once, on the
`SweptVolume` the computation produced: `sweep_hull` returns the hull together
with how many poses it evaluated, how many were interior, its method, and the
level implied by them. `SAMPLES` is now a parameter of the computation, not a
declaration about it.

The level is an **output**: `ENDPOINTS_ONLY` at two poses, `SAMPLED` with interior
ones, and **never** `SWEPT` or `CONTINUOUS` — this method unions the bounds of
discrete poses, and the vocabulary containing those words is not permission to
claim them. `motion_evidence_check` recomputes the level from the record and
refuses a claim the record does not support; a transition that moves something
with no SweptVolume is reported as never evidenced.

---

## 8. LOADPATH AND CONSTRAINT CANONICALIZATION

A hop is an **Interface**. The check resolves each hop to its bodies and reports
two distinct failures: an interface whose own bodies are placed apart carries
nothing across, and consecutive interfaces sharing no body are two crossings with
no route between them. `ordered_hops` declares `target: Interface`, so the retired
body reading is refused at the write boundary — `G10c` asserts exactly that.

`S04_CONTRACT.required_inputs` no longer names `blocking_relations`
(retired at S-4/U-5, last reader removed at the S-5 correction) or
`SelectionDecision`; it names `ConstraintRelation` and `Configuration`.

---

## 9. GENERALITY FALSIFIERS

| | claim | result |
|---|---|---|
| **G1** | direct invoke ≡ runner | full canonical state equality |
| **G2** | two candidates, no spatial leakage | no other branch's id in either realization |
| **G3** | binding arrangement changes → realization loses authority | State, Transition and SweptVolume all STALE; unrelated branch STANDING |
| **G4** | missing axis refuses, never defaults | `None`/`""`/`NONE`/`"diagonal"`/`7` all `computable: False`, no hull |
| **G5** | six axes × revolute and prismatic | one path; a prismatic joint grows the box on **its own** coordinate and no other |
| **G6** | declared distinctness violated → finding | `DECLARED_DISTINCTNESS_NOT_REALIZED`; **G6b** with no declaration, nothing demanded |
| **G7** | declared change not made → finding | and **G7b** an undeclared change that happens |
| **G8** | change the computation → the level changes | 2 poses `ENDPOINTS_ONLY`, 9 `SAMPLED`, and the two hulls differ |
| **G9** | a level the record does not support | `MOTION_EVIDENCE_OVERSTATED`; **G9b** the constant has no field to return to |
| **G10** | Interface hops interpreted through interfaces | changing incidence changes the result |
| **G11** | nothing lost with the runner writer | every retired family and field in a stage patch |

**Mutation checks**, which are the evidence that these bite: restoring the axis
default (2 failures), fixing the evidence level to a constant (1), dropping the
arrangement premise (1), restoring the body reading of hops (1), and removing one
of s04a's own writes (2 — including the ADR-001 replay).

---

## 10. REMAINING INCOMPLETENESS, WITH OWNERS

| residual | owner |
|---|---|
| the selection gate, `SelectionDecision`, committed-branch semantics, both gate poles | **S-7 / U-8** — the staged premise class names the step |
| relocating S04 checks out of the stage module; independence degrees | **S-8 / U-9 / M-9** |
| `S05_CONTRACT.required_inputs` still names `blocking_relations` | **S-8**, which owns that stage's contract; no live path reads it |
| pose law / `body_poses` derivation, witnesses | later stages (S04_CONTRACT `pose_law_rule`) |
| 21 recordings predating these prompts | **S-9** |

No S-6-owned residual was moved to a later step.

---

## 11. CLOSURE CRITERIA

| # | criterion | evidence |
|---|---|---|
| 1 | one canonical S04 semantic write path | G1, G11 |
| 2 | runner authors no S04 engineering meaning | `_commit_s04` retired; asserted absent |
| 3 | S04B consumes the s04a arrangement as a dependency | `_spatial_premises` on every s04b output; G3 |
| 4 | commitment/refinement/supersession executable | `commitment_class`; reasoned SUPERSEDE applied, unreasoned refused |
| 5 | joint frame + axis support deterministic motion | G4, G5, `joint_frame_check` |
| 6 | missing spatial premises never fabricated | G4; `computable: False` with no hull |
| 7 | distinguishing basis realized | G6, G6b |
| 8 | transition coordinate changes real | G7, G7b |
| 9 | evidence level from the computation | G8, G8b |
| 10 | constant `sampling_declaration` authority gone | G9b; the field left `Transition` |
| 11 | Interface-based LoadPath preserved | G10, G10c |
| 12 | `blocking_relations` absent from current S04 truth | S04_CONTRACT corrected |
| 13 | S04 contract matches production | §8, §3, C1/C9/C10/C11 |
| 14 | multi-candidate behaviour branch-safe | G2; branch-keyed ids |
| 15 | no S-7 semantics pulled forward | no SelectionDecision created; `selection_gate_check` empty |
| 16 | S-4 and S-5 invariants unchanged | `_s4_physical_problems == []`; `dof_totality_check == []`; domain 42 on two branches; every MobilityExpectation STANDING |

Regression, **secondary**: RUN 876 · PASS 876 · FAIL 0 · SKIP 22.

---

## 12. REFINEMENT-LIFECYCLE CORRECTION (baseline `2177266`)

### 12.1 The defect, reproduced before editing

An s04b response carrying both an envelope revision and a realization:

```
ENV-0A half_extent            [4, 4, 4]      <- revised, with a geometric reason
ENV-0A superseded?            True
SWV-TRN-A-RGP-G0A  hull       (-1.414, -1.414, -1) .. (1.414, 1.414, 1)
                   validity   STANDING
hull equals the OLD-geometry hull?              True
a hull computed from the REVISED extent would be (-5.657, ...) .. (5.657, ...)
State / Transition validity   STALE
```

The swept occupancy is **four times too small and STANDING** — current evidence
for an arrangement the same patch withdrew. `State` and `Transition` did go
STALE, and the difference is the mechanism: they come from `to_operations`, which
is ordered *before* the SUPERSEDE, so propagation reached them. The SweptVolume
comes from `derived_operations`, ordered *after* it, so **it was never a dependent
of the supersession at all**. The worst artifact was the one that stayed current.

All three hooks read `inputs[context_key]` — the view built when the invocation
started — confirmed by inspection of `Stage.run` and of each S04B hook.

### 12.2 The correction

`Stage.refinement_barrier(parsed, inputs, state)` returns `(ops, why)` or `None`.
When it returns operations, `Stage.run` commits **those and nothing else**,
records `why` as the declared incompleteness, and sets `StageOutcome.refinement_only`
— a field, so a caller acts on a fact rather than on prose.

S04B fires it when its response carries a justified envelope revision.
`_revision_ops` is the **single reader** that decides what counts as one, shared
by the barrier and by `refinement_operations`: if they could disagree, an
invocation could withhold its realization and commit nothing — a stall with no
visible cause.

`run_s04` invokes, applies, and re-invokes **once** on `refinement_only`, which
refreshes the ConsumerView because `invoke` builds it from current state. The
refresh is bounded: a second refinement-only outcome is reported as "still
revising", and no realization is committed from an arrangement that never settled.

### 12.3 Files changed, and why each was necessary

| file | why |
|---|---|
| `stages/base.py` | the barrier hook, the control field, and the one branch in `run` that commits a barrier alone. Without it the lifecycle has nowhere to live |
| `stages/s04_envelope_and_motion.py` | `_revision_ops` as the single reader; `refinement_barrier` fires on it. This is the stage whose response can revise |
| `tools/run_window2.py` | bounded re-invocation. The runner invokes, applies, refreshes and asks again — it reads no response and decides no engineering |
| `contracts/stages/S04_CONTRACT.yaml` | the lifecycle stated where the stage's contract lives; and `owned_decisions` corrected to what the responsibility contract actually grants — Witness, `Interface engagement_site` and LoadPath maturity moved to `not_owned_here` with their owners rather than being implemented to make prose true |

`DesignState.apply`, `_propagate`, S-3/S-4/S-5 stages and every other stage's
semantics are **untouched** — the diff is four files.

### 12.4 R1–R10

| | claim | result |
|---|---|---|
| **R1** | no revision → one invocation realizes | `refinement_only` false, SUCCESS, State/Transition/SweptVolume produced, joint placed |
| **R2** | revision → revision only | patch families are `["Envelope"]` alone; no State, no Transition, no SweptVolume, no `frame_origin`; the reason names ENV-0A |
| **R3** | refreshed view | before `[1,1,1]`, after `[4,4,4]` |
| **R4** | recomputed geometry | the occupancy differs from the unrevised run and equals `sweep_hull` over the revised extent |
| **R5** | final currentness | State, Transition and SweptVolume STANDING, each carrying ENV-0A as a premise |
| **R6** | no stale masquerade | the pre-revision hull appears on no SweptVolume, standing or otherwise |
| **R7** | later supersession | a revision arriving after a realization stales State, Transition and SweptVolume through the existing substrate |
| **R8** | branch isolation | branch B's occupancy byte-identical and STANDING; `ENV-0B` unrevised |
| **R9** | runner neutrality | manual invoke/apply/reinvoke and `run_s04` produce equal canonical state; the refinement is recorded as a lifecycle event, not a failure. **R9b**: an always-revising stage is bounded and reported, and no SweptVolume is committed |
| **R10** | no S-7 dependency | no SelectionDecision, `committed_branch` still None, gate check empty |

Three further cases hold the barrier's own generality: the default hook returns
`None`; an unjustified revision neither fires the barrier nor commits (no reason,
unknown envelope, no extent); and both entry points are asserted to go through
`_revision_ops`.

**Mutation checks:** ignoring the barrier (8 failures), firing it but committing
the realization anyway (2 failures + 6 errors), and unbounding the refresh (1).

### 12.5 Newly discovered, and deliberately left alone

**A value created after a SUPERSEDE in the same patch is not a dependent of it.**
`_propagate` runs at the moment the SUPERSEDE is applied, so an op later in the
same patch enters STANDING. This is what let the old SweptVolume escape.

On inspection it is **not a substrate defect and was not patched**: a value
created after the supersession cites the entity's *current* value, so it is
correctly not stale. The defect was entirely that the derivation read a stale
*view*, which the barrier fixes. Changing `_propagate` would have made a correct
value stale. Recorded here because it is subtle and a reader will otherwise
wonder — owner: none, no change required.

Also observed and untouched: `S05_CONTRACT.required_inputs` still names
`blocking_relations` (owner **S-8**; no live path reads it).

---

## 13. ROOT-CAUSE SPATIAL LIFECYCLE PASS (baseline `d06e29b`)

### 13.1 Root gaps, reproduced before editing

**A.** `State.configuration` was written by the producer and declared nowhere:
absent from `required_fields`, absent from `field_semantics`,
`reference_spec("State", "configuration") → None`. The write boundary could not
check it and the realization check read it as a bare string.

**B/C.** The premise sets were wrong **in both directions at once**:

```
STA-CFG-C0A   ['CND-A', 'ENV-0A', 'ENV-1A', 'SCL-CND-A']
TRN-A         ['CND-A', 'ENV-0A', 'ENV-1A', 'SCL-CND-A']
SWV-...       ['ENV-0A', 'ENV-1A', 'JNT-A', 'SCL-CND-A']
```

Every output carried every envelope in the view — including `ENV-1A`, the other
body's, which no computation here reads — and **none** named the Configuration,
the endpoint States, the Transition or the moving RigidGroup.

**D.** With `_propagate` one-hop, that left this:

| change | sweep | state | transition |
|---|---|---|---|
| endpoint State coordinate | **STANDING** | STANDING | STANDING |
| driving Joint axis | STALE | STANDING | STANDING |
| Transition moving groups | **STANDING** | STANDING | STANDING |
| Configuration withdrawn | **STANDING** | **STANDING** | STANDING |
| moving RigidGroup | **STANDING** | STANDING | STANDING |

An occupancy swept between coordinates that had just been replaced stayed
current.

**E.** Only `Envelope` had an executable commitment class. `ReferenceScale`,
`FunctionalRegion.volume` and `AssemblyStep.insertion_direction` had none.

**F.** Contract contradictions: **duplicate `S04B-C9`**; `S04B-C2` and the
SweptVolume rule both declaring endpoint-only sampling **REFUSED**; a Transition
rule still saying "Sampling is DECLARED" after sampling left the family; and
`s04a.owned_decisions.creates` claiming "endpoint State poses", a producer that
never existed.

### 13.2 The canonical dependency graph

`_propagate` is **one hop**, so a derived value that names only the nearest link
inherits nothing from behind it. Each value names every fact it was made from:

```
State        Configuration it realizes · the Joints its coordinates are OF · ReferenceScale
Transition   both endpoint States · the RigidGroups it moves · the Joints it declares changed · ReferenceScale
SweptVolume  the Transition · the moving RigidGroup · both endpoint States ·
             the driving Joint · the ONE Envelope whose box was swept · ReferenceScale
placement    ReferenceScale only — see 13.4
```

Plus the invocation premise on all of them, which is lineage (S-5), never a
substitute for a computational premise.

**Not** the other bodies' envelopes, and **not** the extents under a joint angle:
a coordinate is not computed from a box, and saying it was made an unrelated
resize look like it invalidated the kinematics — which teaches a reader to ignore
STALE.

### 13.3 Commitment representation

`spatial_commitments` in the canonical contract, in two kinds because s04a
authors two kinds:

- **entity-level** — `Envelope`, `ReferenceScale` — carry `commitment_class` on
  the entity;
- **field-level** — `FunctionalRegion.volume`, `AssemblyStep.insertion_direction`
  — **cannot**. Runtime has no per-field authority, and inventing a field to hold
  one would declare an enforcement that does not exist. What is enforced is what
  the boundary already enforces: the field is extendable by s04 and by no one
  else, and a later change is a SUPERSEDE, which requires a reason.

`spatial_commitment_check` reads that declaration — so a family added there is
checked without editing code — and validates **vocabulary membership**, which a
required-field rule never could: a class of `"x"` satisfies `required_fields` and
means nothing. That is why `commitment_class` is in neither family's
`required_fields`: it would move enforcement to a weaker place and oblige every
fixture building one of these for an unrelated reason to carry a field it is not
about.

### 13.4 One correction inside this pass

I first removed **all** premises from the field-level extensions, reasoning that
premises on an EXTEND land on the entity and would stale an s03-owned Joint when
an envelope changed. The ADR-001 replay failed, and it was right to: its frozen
property is *"a coordinate has no meaning without its basis, so withdrawing the
basis must cost every coordinate its unqualified authority."* The distinction I
had missed is that the **basis** is a premise of the coordinate's meaning while
another body's **extent** is not a premise of the origin at all. The placement
extension names the scale and no extent.

### 13.5 L1–L11

| | claim | result |
|---|---|---|
| **L1** | Configuration withdrawn | its State STALE; the sibling's untouched |
| **L2** | endpoint coordinate changed | Transition **and** SweptVolume STALE |
| **L3** | driving Joint axis / frame_origin / class changed | SweptVolume STALE in all three |
| **L4** | moving group's Envelope extent changed | SweptVolume STALE |
| **L5** | an unrelated body's Envelope changed | State, Transition and SweptVolume all STANDING |
| **L5b** | the ReferenceScale changed | all three STALE — the one genuinely universal premise, for the reason the contract states |
| **L6** | branch B's envelope changed | B's sweep STALE, A's realization untouched |
| **L7** | the premise set is **exactly** what reproduces the value | asserted as set equality, because a subset assertion cannot catch over-declaration and a superset cannot catch under-declaration |
| **L8** | each premise is load-bearing | five facts changed one at a time; each stales the occupancy |
| **L9** | a visible fact that was not used | `ENV-1A` is in the view and in no premise set |
| **L10** | same-invocation revision | the barrier still fires, patch is `["Envelope"]` alone, and the pre-revision occupancy stales |
| **L11** | prismatic | identical premise set, same code path, different geometry |

**Mutation checks:** restoring the blanket envelope premise (4 failures), the
sweep naming only the joint (4), State forgetting its Configuration (2), and the
basis leaving the placement extension (2 — including ADR-001).

### 13.6 Contract corrections

`State.configuration` typed and required · dependency rules stated on State,
Transition and SweptVolume · `spatial_commitments` declared ·
`ReferenceScale.commitment_class` vocabulary · endpoint-only **no longer refused**
anywhere, in the contract, the check or the sampler — it is a level, and whether
it suffices is an assurance question (S-8 / U-9) · the Transition sampling rule
removed · duplicate `S04B-C9` renumbered to C12–C14 · `s04a.owned_decisions`
corrected to what it creates and extends.

### 13.7 Newly discovered, with owners

- **`S05_CONTRACT.required_inputs` still names `blocking_relations`** — owner
  **S-8**; no live path reads it. Untouched.
- **`sample()` refuses fewer than 3 poses** while `sweep_hull` supports 2 for
  ENDPOINTS_ONLY. `sweep_hull` handles the 2-pose case itself, so no current
  behaviour is wrong; the floor inside `sample` is now redundant rather than
  contradictory. Owner **S-8** if it ever matters. Untouched.

### 13.8 Closure audit

1 machine-identifiable commitments ✅ · 2 correct granularity ✅ · 3 canonical
Configuration relation ✅ · 4 actual premises ✅ (L7) · 5 used premise stales
exactly ✅ (L1–L4, L8) · 6 unrelated leaves current ✅ (L5) · 7 stale endpoints
cannot support a standing sweep ✅ (L2) · 8 old-envelope computation cannot
masquerade ✅ (L4, L10) · 9 across branches and joint types ✅ (L6, L11) · 10
contracts describe the implementation ✅ (13.6) · 11 barrier preserved ✅ (L10 and
the R-suite) · 12 S-7/S-8/S-9 outside ✅.

Regression, **secondary**: RUN 907 · PASS 907 · FAIL 0 · SKIP 22.

---

## 14. CONTRACT-TRUTH PASS (baseline `6a73f8d`)

Runtime frozen. **The diff is two contract files** — `ver3/assy_v3`, `ver3/tools`
and `ver3/tests` are byte-identical.

### 14.1 Contradictions reproduced

| | claim, live at `6a73f8d` | why it contradicted the runtime |
|---|---|---|
| **A** | `Transition.rules`: *"Sampling is DECLARED, never adaptive-and-unrecorded."* | sampling is not a Transition field; the rule sat **beside** the S-6 rule that replaced it, so the family carried both readings |
| **B** | `SweptVolume.rules`: *"endpoint-only sampling is refused."* | sat beside a rule naming ENDPOINTS_ONLY as a level this method produces, and beside a `fidelity` vocabulary containing it — the family refused a value it enumerated |
| **C** | `spatial_commitments.granularity_rule`: entity commitments *"carry `commitment_class` as a required field"* while `enforced_by` says it is deliberately **not** in `required_fields` | one structure, two answers |
| **D** | `s04a.maturity_expectations.geometry: [ENVELOPES, ENDPOINT_POSES]` | s04a authors no State |
| **E** | `selection_gate.position: "between s04a and s04b"` | the gate is S-7/U-8 and follows S-6; this was the same claim that made s04b unreachable |
| **F** | `S04B-C6` over *"every declared blocking relation"* | producer retired at S-4/U-5, last reader at the S-5 correction |
| **G/I** | `S04B-C9` *"every Interface has a metric engagement_site"* | S04 owns no such field; `not_owned_here` already said so |
| **H** | `needs: [… paths_with_declared_sampling, engagement_sites, confirmed_load_paths]` | sampling is not a path declaration; engagement sites are later-owned; the check refutes, it does not confirm |

Found by the full-file sweep rather than from the list:

| | | |
|---|---|---|
| **J** | `S04B-C14.rationale` still argued the retired endpoint-only refusal | left behind when C9 was renumbered to C12–C14 |
| **K** | `Interface.fields_owned_by_s04b: [engagement_site]` | the two files disagreed about the same ownership |
| **L** | `SweptVolume.purpose`: *"at declared sampling"* | same class as B |
| **M** | `Witness` multi-owner row: *"s04 produces motion witnesses"* | present tense for a producer that does not exist |
| **N** | `prohibited_decisions`: *"adaptive sampling that is not declared"* | true, and phrased as though a model declares it |
| **O** | `knowledge_base_role`: *"Sampling policies per motion class"* | a policy fixing density from outside puts the claim back in front of the work |

### 14.2 Corrections

Each retired claim is **replaced by the corrected one and marked with what it
used to say**, so a reader sees the change rather than a silent absence.

`DESIGN_STATE_CONTRACT` — the Transition sampling rule retired; the SweptVolume
refusal retired and its purpose corrected; `granularity_rule` reconciled with
`enforced_by`; `Interface.fields_owned_by_s04b` → `engagement_site_status` with
its owner; the Witness row's tense corrected.

`S04_CONTRACT` — `ENDPOINT_POSES` removed; `selection_gate.position` → *"after
s04b; the gate is S-7 / U-8"*; C6 restated over `ConstraintRelation`; C9 retired
with its id **not reused**; next-stage needs corrected and `engagement_sites`
moved to `later_owned`; C14's rationale replaced with the axis argument;
`prohibited_decisions` and `knowledge_base_role` reworded.

### 14.3 Reclassified, not implemented

`engagement_site`, `Witness` production, the selection gate, `blocking_relations`
— **later-owned or retired**, each pointing at its owner. No production behaviour
was added to make any of them true.

### 14.4 Full-file sweep

Every remaining occurrence of the listed vocabulary classifies as **CURRENT AND
TRUE** (the `fidelity` vocabulary, the S-6 dependency and evidence rules,
`spatial_commitments`, `commitment_class`, the corrected checks), **HISTORICAL**
(the S-4/S-5 superseded-producer rows, the retirement notes added here),
**RETIRED** (the `blocking_relations` corpus residuals, C9) or **LATER-OWNED**
(`SelectionDecision`/`selection_gate`, `Witness`, `engagement_site`). No
contradictory CURRENT claim remains in either file.

### 14.5 C1–C12

All pass. C11 confirmed by an empty diff over `ver3/assy_v3`, `ver3/tools` and
`ver3/tests`.

### 14.6 Newly discovered

None beyond the contract claims above; nothing runtime. The two items carried
from the previous pass are unchanged and untouched: `S05_CONTRACT` still names
`blocking_relations` (**S-8**, no live reader), and `sample()`'s three-pose floor
is redundant beside `sweep_hull`'s own two-pose handling (**S-8** if it matters).

Regression, **secondary**: RUN 907 · PASS 907 · FAIL 0 · SKIP 22.

---

## CURRENT STATUS

> **S-6 VERIFIED CLOSED — RUNTIME AND AUTHORITATIVE CONTRACT TRUTH CONSISTENT.**
>
> s04a commits an arrangement whose every value declares the class it is
> committed at. s04b extends it, or supersedes it with a geometric reason — and a
> supersession is a barrier, so the realization is withheld until it can be
> reasoned from the arrangement the design now holds. Every current spatial value
> names exactly the facts it was made from, so changing one stales exactly what it
> can have made wrong and changing anything else leaves the rest current. The
> motion evidence level is an output of the computation, endpoint-only is a level
> rather than a refusal, and no declaration or constant establishes evidence
> maturity. The authoritative contracts now say all of that and nothing that
> contradicts it: what S04 does not own is named with its owner, and what was
> retired is marked with what it used to claim.
>
> S-3, S-4 and S-5 are unchanged and verified so. **Impl S-7 has NOT begun.**
