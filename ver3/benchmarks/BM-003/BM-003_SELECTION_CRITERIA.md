# BM-003 — selection criteria and candidate briefs

> **SUPERSEDED IN PART — the subject is now fixed.**
>
> BM-003 is **Compact folding three-leg desktop stand**, fixed by instruction.
> None of the three briefs below was selected; the decision was made outside this
> analysis, which is what the document asked for. Sections 1–3 remain live: they
> are the coverage gaps and criteria the fixed subject must still be checked
> against, and section 5's post-selection sequence is now the active path.
>
> The source request exists at [`source/request.txt`](source/request.txt) and is
> **HUMAN_REVIEW_REQUIRED and unfrozen**. No Oracle has been authored.
>
> **How the fixed subject scores against section 3:** it exercises C1 (assembly
> order), C2 (leg joints retained), C3 (mobility differs between stored and
> deployed), C4 (legs must not fold, twist or work loose once open), C5
> (retention through the full cycle), C6 (the release admits many realizations),
> and C7 (decidable by mobility counting and interference sweeps, with load
> capacity explicitly out of scope). It is closest in spirit to Brief A, without
> being it.

This document narrowed the space and offered three briefs. It did not choose, and
choosing was not a step that could be delegated: BM-003 is the third witness in
the freeze gate, and a benchmark selected by the same process it is meant to test
would not be independent evidence.

Nothing here is an Oracle, a design, a positive reference or a Stage output. No
mechanism is specified, no geometry is proposed, and no expected outcome is
stated for any brief.

---

## 1. Why a third benchmark exists at all

`STAGE_PROGRESSION_CONTRACT.yaml` step 8 will not let a stage contract freeze
until **all three** benchmarks demonstrate downstream sufficiency from
source-only runs. Two is not enough for a specific reason: with two problems, a
stage that happens to fit both is indistinguishable from a stage that
generalises. The third exists to make accidental fit visible, and it earns that
role only by stressing what the first two do not.

So the selection question is not "what would be a good mechanical problem". It is
**"what can BM-001 and BM-002 not detect?"**

---

## 2. What is already covered

Established from the existing references and the frozen dossiers.

| | BM-001 | BM-002 |
|---|---|---|
| Product | latching storage box | enclosed hand-cranked platform lift |
| Bodies | 3 (EXE-01) / 2 (EXE-02) | 7 |
| Assembly steps | 3 / 2 | 9 |
| Declared interactions | 12 / 15 | 17 (+1) |
| Motion | two-state closure | continuous rotation → translation |
| Retention | compliant snap latch | pin capture by a rear panel |
| Mobility | constant | constant (1 DOF once assembled) |

Also already claimed by frozen dossiers, and therefore **not** available as novel
ground: `bounded-two-state-closure`, `guided-slider`, `latch-retention`,
`rotary-to-linear-engagement`, and `C4-drawer` — a Ver1 case whose source is
*"Design a desktop cabinet whose drawer slides out horizontally when you turn a
knob."* A drawer-on-rails problem would substantially re-run that case.

### What the two benchmarks genuinely do not exercise

1. **Mobility that depends on configuration.** Both mechanisms have a *constant*
   degree-of-freedom count once assembled. Neither can detect a pipeline that
   never models DOF as configuration-dependent, because neither has a
   configuration in which the count changes.

2. **Unintended DOF that must be prevented geometrically and shown absent.**
   BM-002's guide is an **IDEAL prismatic constraint** — the unintended DOF is
   suppressed by the model rather than by the design. Nothing yet forces a
   pipeline to prevent an unintended freedom with geometry and then demonstrate
   the prevention.

3. **Capture created *by* an assembly operation.** BM-002's pin retention is
   installed by a separate part in a separate step. Neither benchmark has a
   relationship where performing the assembly motion is itself what creates the
   capture, so neither can detect a pipeline that treats assembly and retention
   as independent concerns.

4. **A genuinely wide solution space.** BM-002's architecture was *forced* — the
   connecting rod sweeps the crank axis, so an overhung crank is the only option.
   BM-001's latch is similarly determined. Neither can detect a pipeline that
   collapses to one candidate prematurely, because on these problems there is
   very nearly one candidate.

5. **Interfaces that could plausibly disengage during operation.** Both keep
   their interfaces engaged trivially. Persistence has never had to be *earned*.

6. **More than one moving output.** Every mechanism so far has a single moving
   chain.

---

## 3. Criteria

A candidate must satisfy all seven. They are ordered by how much each adds over
the existing coverage, not by importance.

| # | Criterion | Why it is required | Covered today? |
|---|---|---|---|
| C1 | **Nontrivial assembly sequence** — order is forced by geometry, and at least one order is impossible | Detects a pipeline that emits a parts list and calls it an assembly | partly (BM-002) |
| C2 | **Retention or capture relationships** — at least one body held by two others jointly, or captured by the assembly motion itself | Detects retention treated as a label rather than an embodiment | weakly |
| C3 | **Configuration-dependent mobility** — the DOF count differs between two named configurations | Detects mobility modelled as a constant property | **no** |
| C4 | **Target vs unintended DOF** — at least one unintended freedom must be prevented by geometry and its absence demonstrated | Detects unintended-DOF checking that only works when the forbidden set is trivial | **no** |
| C5 | **Full-operation persistence of assembly interfaces** — an interface that could credibly disengage mid-operation must be shown not to, across the whole range | Detects persistence asserted at endpoints only | **no** |
| C6 | **Multiple admissible realizations** — at least three genuinely different mechanisms satisfy the source | Detects premature convergence to one candidate (INV-007) | **no** |
| C7 | **First-order verification suffices** — decidable by mobility counting, interference sweeps, engagement measurement and rigid-body dynamics, with **no FEM and no CFD** | A benchmark whose verdict needs machinery the pipeline does not have produces UNSUPPORTED, which measures nothing | yes (both) |

### Two disqualifiers

- **Anything whose verdict turns on stress, deflection, friction coefficients,
  fatigue, sealing or flow.** That is C7 inverted. It would yield UNSUPPORTED,
  which is the correct answer and a useless benchmark.
- **Anything substantially re-running a frozen dossier**, in particular the
  knob-driven drawer.

---

## 4. Candidate briefs

Three, deliberately different in *which* criteria they stress hardest. Each is a
problem statement only. **No mechanism is prescribed, and the mechanism named in
"why it is hard" is illustrative of the space, not a proposed answer.**

### Brief A — insert-and-turn captive coupling

> A component must be attachable and removable by hand, without tools, by
> inserting it and turning it. Once turned to its engaged position it must not
> come off along the insertion direction. It must be removable again by
> reversing the operation, repeatedly.

| Criterion | How it is stressed |
|---|---|
| C1 | Insertion strictly precedes rotation; the reverse order is geometrically impossible |
| C2 | **Strongest.** The capture is created by the assembly motion itself, not by a separate part |
| C3 | **Strongest.** Aligned: axially free. Engaged: axially captured. The DOF count differs between two named configurations of the *same* two bodies |
| C4 | In the engaged configuration, axial withdrawal is the unintended DOF and must be absent by geometry |
| C5 | Engagement must persist through the full rotation, not merely at the end |
| C6 | Lug count, lead geometry, thread-like vs stepped, detented vs plain — several are admissible |
| C7 | Mobility count per configuration and a swept interference check decide it |

*Risk:* the "hold it there" requirement invites a friction or spring answer,
which is C7-hostile. Mitigated by the source not requiring resistance to
rotation — only that it cannot come off *axially*.

### Brief B — retained removable carrier

> A tray must slide into a housing and be held so that it cannot fall out or be
> pulled free during normal use, yet a user must be able to release and remove it
> deliberately. The tray must stay level and square to the housing throughout.

| Criterion | How it is stressed |
|---|---|
| C1 | The tray must be inserted before the retaining element can be installed |
| C2 | The tray is captured by housing and retainer **jointly** — neither alone suffices |
| C3 | Retained: bounded travel, cannot be withdrawn. Released: withdrawable. Two configurations, different mobility |
| C4 | **Strongest.** "Level and square" names three unintended DOF — pitch, yaw, roll — each of which must be prevented geometrically and shown absent |
| C5 | The guiding interfaces must stay engaged across the entire travel, including near full extension where engagement is least |
| C6 | Rails, grooves, tabs, opposed flanges, over-and-under captures |
| C7 | Mobility count, interference sweep, engagement-length measurement at every sampled position |

*Risk:* closest of the three to `C4-drawer` and `guided-slider`. **Distinguished
only by the retention-and-release requirement and the explicit squareness
constraint**; if the human selects this, the source must be worded so that
neither reduces to a rail problem. This risk is why it is not recommended first.

### Brief C — one input, two synchronised outputs

> Turning a single control must move two opposed carriers equally and in
> opposite directions, so that whatever is placed between them is held centred.
> The carriers must stay parallel and must not move independently of one another.

| Criterion | How it is stressed |
|---|---|
| C1 | Two chains must be assembled in a fixed relative order to establish the coupling |
| C2 | Each carrier is captured by its guide; the coupling itself must be retained |
| C3 | Weakest of the three — mobility is largely constant, though a disengaged-coupling configuration would add it |
| C4 | **Strongest.** Independent motion of the carriers *is* the unintended DOF, and the whole point is that it must be impossible rather than merely unlikely |
| C5 | Synchronisation must hold across the full range, not at the centre only |
| C6 | **Strongest.** Rack-and-pinion, scissor linkage, opposed-hand screw, cam-and-follower, cable loop — all admissible, all genuinely different |
| C7 | Symmetry and synchronisation are kinematic; a sampled sweep decides them |

*Risk:* the weakest on C3. If configuration-dependent mobility is judged the most
important gap, this brief is the poorest fit despite being the strongest on C6.

### How they compare

| | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| **A** insert-and-turn | ✔ | **strong** | **strong** | ✔ | ✔ | ✔ | ✔ |
| **B** retained carrier | ✔ | **strong** | ✔ | **strong** | ✔ | ✔ | ✔ |
| **C** synchronised outputs | ✔ | ✔ | weak | **strong** | ✔ | **strong** | ✔ |

No recommendation is made. The three differ in which gap they close hardest, and
which gap matters most is a judgement about what the pipeline is most likely to
get wrong — which is exactly the judgement being reserved.

---

## 5. What must happen after the subject is chosen

In this order. The ordering is not administrative: an Oracle written after a run
is a description of that run, and `BENCHMARK_RESULT_CONTRACT` invalidates the
result outright when `oracle_frozen_before_run` is false.

1. Write the source request. It states a **problem**, never a mechanism. The
   leakage test in `test_benchmark_skeleton.py` scans for solution language.
2. Freeze it, with a `source/source_manifest.yaml` carrying provenance and hashes.
3. Author the Oracle **independently**, in `ver3/oracles/`, and freeze it
   **before** the first source-only run.
4. Optionally build a positive executable reference in `ver3/cad_validation/`,
   to validate the evaluator. Never as a scoring target (SC-01).
5. Update `descriptor.yaml` from `PLACEHOLDER`, which un-blocks the freeze gate.

---

## 6. Status

```yaml
benchmark_subject: "BM-003 - COMPACT FOLDING THREE-LEG DESKTOP STAND"
subject_status: FIXED_BY_INSTRUCTION
candidate_briefs: [A, B, C]        # none selected; superseded by the fixed subject
source_request: AUTHORED           # HUMAN_REVIEW_REQUIRED, unfrozen
oracle: NOT_AUTHORED
positive_reference: NOT_BUILT
blocks: freezing any stage contract
```

BM-003 remains a declared placeholder and no stage contract may freeze — enforced
by `test_benchmark_skeleton.py`. The source being written does not change that:
the gate needs a **frozen** source and an Oracle frozen **before** the first run,
and neither exists.
