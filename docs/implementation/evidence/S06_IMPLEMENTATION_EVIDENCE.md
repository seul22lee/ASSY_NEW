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

## CURRENT STATUS

> **S-6 VERIFIED CLOSED — CANONICAL SPATIAL COMMITMENT AND REFINEMENT LIFECYCLE
> COMPLETE.**
>
> S04 authors its own conclusions, in its own patches, so a direct invocation and
> a runner run produce the same canonical state. s04a commits an arrangement with
> a class; s04b extends it or supersedes it with a geometric reason, carrying the
> commitments it rests on as premises, so a changed arrangement costs the
> realization its authority. A joint without a usable axis computes nothing rather
> than rotating about a fabricated one. Declared distinctness and declared
> coordinate changes are checked against the coordinates. The motion evidence
> level is an output of the sweep and cannot be raised by declaring it. Load paths
> are read through Interfaces, as S-4 made them.
>
> S-3, S-4 and S-5 are unchanged and verified so. **Impl S-7 has NOT begun.**
