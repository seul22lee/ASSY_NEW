# Architecture comprehension check — Ver1, Ver2, and what Ver3 changes

**Purpose:** demonstrate that the Ver3 constraints are understood as
*architectural consequences of observed failures*, not as a list copied from an
instruction. Every claim below is tied to a file and, where useful, a line.

**Method note:** I looked for the mechanism of each failure — the design
decision that made it possible — rather than for the symptom. Two failures with
the same symptom and different mechanisms are listed separately; two with
different symptoms and one mechanism are listed once.

---

## A. Why Ver1 failed

Ver1 works. That is the important part. It compiles geometry, runs MuJoCo, and
certifies benchmarks with real measured numbers. Its failure is not that it
produced wrong answers; it is that **the answers were already in the library**.

### A.1 The catalogue *is* the design space

`/home/ftk3187/github/ASSY_Ver1.0/knowledge/cards/` holds **19 files**, of which
~15 are mechanism cards: `pin_hinge`, `slide_rail`, `rack_pinion`, `lead_screw`,
`snap_hook`, `pawl_detent`, `stop_flange`, `bushing`, `journal_bearing`,
`press_fit`, `dowel_pin`, `screw_boss`, `coupling`, `universal_joint`.
`knowledge/templates/host_templates.py` holds a fixed `TEMPLATES` registry
(cabinet_shell, slide_carriage, drawer_tray, knob_shaft, …).
`ontology/validators.py` implements **17 hand-written validators, V-01 … V-17**.

A card carries not just a name but its own `carve` geometry, its parameter
bounds, and its host-anchor expectations. So a card is not a *fact about a
mechanism* — it is **a pre-solved sub-design**. When a task selects
`rack_pinion`, it inherits geometry, parameter ranges, and mesh offsets that a
person authored. The synthesis step is closer to *retrieval and parameter
substitution* than to design.

### A.2 Coverage grew one benchmark at a time — visible in the directory names

The repository is organised by milestone, and the milestones *are* the
vocabulary acquisitions:

`m1_gear` · `m7_rack_pinion` · `m8_pin_hinge_easy` · `m10_slide_rail` ·
`m11_rack_pinion` · `m17_gear_vb` · `m18_element_expansion` · `m19_lead_screw` ·
`m20_coupling` · `m21_universal_joint` · `m23_latch_physics` ·
`m27_angled_screw_lift`

Each milestone adds a card, then a benchmark that the new card satisfies. The
benchmark suite and the library co-evolved, so suite pass-rate measures *library
coverage of the suite*, not synthesis ability. A benchmark that needed a
sixteenth mechanism would have required a sixteenth milestone.

### A.3 The decisive failure: "my catalogue lacks it" reported as "physics forbids it"

This is the failure I consider most damaging, because it is the one that looks
like a *result*.

From `tasks/benchmark/manifest_draft.md:33` and `benchmark.py:145-150`:

> **C5-lift-nogear** — "Design a crank lift that holds a 0.5 kg load, but
> without any gear or ratchet."
> → `INFEASIBLE`, code `KG_NO_PERMITTED_REALIZER`
> rationale: *"a crank→lift needs rot_to_trans, whose **ONLY card** is
> rack_pinion; forbidding gear+ratchet leaves no realizer AND no hold."*

And `benchmark.py:159-162`:

> **D1-screw-jack** — "Design a threaded screw-jack that lifts a load by turning
> a leadscrew." → `INFEASIBLE`, validator `V-03`
> rationale: *"leadscrew card + column template ∉ vocabulary"*

Both verdicts are false as engineering statements. A hand-cranked lift without a
gear or ratchet is entirely realizable — a lead screw with a self-locking helix
angle, a worm, a friction brake, a capstan. And D1 is *especially* revealing:
`knowledge/cards/lead_screw.py` **exists in the repository** and `m19_lead_screw`
is a milestone. The mechanism was in the library and still returned
`INFEASIBLE`, because the *benchmark harness* had frozen a vocabulary that
predated it.

The architectural lesson is not "add more cards". It is that **a system with a
closed vocabulary cannot distinguish four different things**:

| Reality | Ver1 verdict |
|---|---|
| Physically impossible | `INFEASIBLE` |
| Possible, no knowledge encoded | `INFEASIBLE` |
| Possible, knowledge encoded but not wired into this harness | `INFEASIBLE` |
| Possible, but not verifiable by the available models | `INFEASIBLE` |

Collapsing these four into one verdict is what makes the system unfalsifiable:
you cannot tell a capability gap from a physical law.

### A.4 The reference examples already contain the answer

`tasks/build_goldens.py:1142` `anchor_hard()` — the builder behind C4-drawer —
is ~70 lines that already fix the frame convention (`+X = FRONT`), the rail
count (two), the rail gap (80 mm), the seat coordinates
(`seat_x=76, seat_y=60, seat_z=30`), the module and tooth count (`m=5, z=12`),
and the derived constraint chain:

```
drawer_w = cab_inner_w − 2(rail_w+cl) = 132 − 2·8.35 = 115.30 mm
L_rack  ≥ stroke + πmz/4              = 120 + 47.12  = 167.12 mm
```

These are correct, and they are *human engineering*, embedded in the golden
builder. Any pipeline evaluated against this golden is being graded on whether
it can reproduce a solution it was handed.

### A.5 The risk this creates for Ver3

If Ver3 ships a mechanism library and selects from it, Ver3 becomes Ver1 with
better bookkeeping. The specific traps:

1. Importing Ver1 cards "just to have a baseline" — the cards carry geometry and
   bounds, so importing one imports a design.
2. Letting a knowledge lookup return `INFEASIBLE`. It may only ever return
   `UNSUPPORTED` — the distinction is invariant `INV-011`.
3. Treating the Ver1 goldens as targets rather than as one sample from an
   allowed set — the reason `ORACLE_METHOD.md` ranks goldens at **rank 5**.

**Central failure mechanism of Ver1: the design space was enumerated in advance
by hand, so synthesis degenerated to retrieval, and every gap in the enumeration
was reported as a fact about physics.**

---

## B. Why Ver2 failed

Ver2 diagnosed Ver1 correctly — it replaced cards with staged reasoning. Its
failure is different in kind, and its own research log names most of it.

### B.1 Stage-local truth stores: the same design, recreated five times

The stage signature in `tools/run_benchmarks.py:42-49` is the whole problem in
seven lines:

```python
mech    = MechanicalArchitectureGenerator().run(spec=spec)
product = ProductArchitecturePlanner().run(spec=spec, mechanical=mech)
converged = resolve(spec, mech, product)
km, definition = converged.kinematic, converged.engineering
solved  = ParametricSolver().run(definition=definition)
```

Each stage returns **a new document** — `MechanicalArchitecture`,
`ProductArchitecture`, a kinematic model, an `engineering` definition, a
`SolvedDesign`. A downstream stage receives an upstream *document* and builds
its own. Nothing is a shared, additive store.

Two consequences follow mechanically, not accidentally:

- **Identity is not preserved.** A body that exists in `mech` is *described* to
  the product planner, which creates its own body. Nothing forces the two to be
  the same entity, so nothing can detect when they diverge.
- **Meaning degrades at every boundary.** Each stage re-derives intent from the
  previous stage's summary. This is lossy compression applied five times in
  series.

Note also `spec=spec` being passed to **both** stage 02 and stage 03. The
original requirement document is still an input two stages downstream — so
prose re-interpretation is not a bug, it is the wiring.

### B.2 Ordinal space standing in for geometry

`assy/domain/upstream.py` defines the spatial vocabulary:

- `AxisStation` (line 1522): `NEGATIVE_END`, `MID_SPAN`, `POSITIVE_END`,
  `RANGE_MIN`, `RANGE_MAX`
- `SpatialZone` (line 1547): `CORE`, `FLANKING`, `END`, `OFFSET`, `BOUNDARY`,
  `EXTERNAL`
- `RadialPosition` (line 859): `ON_AXIS`, `OFF_AXIS`
- `BodyPlacement.span: list[int]` — documented as *"an ordinal interval on the
  principal axis: a relative position, **not a coordinate and not a
  dimension**"*

The docstrings are honest, and that honesty is the indictment. A model that
explicitly cannot express a coordinate cannot answer *does the lid clear the
aperture when it swings*, *do the two rails stay parallel*, *does the platform
fit its corridor at both extremes*. Those are the questions the product needs.

Because the representation cannot answer them, downstream stages had to invent
answers — which is where fixed-offset motion and interval-swapping "rotation"
came from. They are not sloppiness; they are the only moves available once the
spatial type system has no metric.

### B.3 A rendered sheet promoted to a design definition

`ConceptVisualization` (upstream.py:1724) was Stage 04's product, built by
`s04_concept.py:1332`, with `_zone_of()` (s04_concept.py:308) mapping placements
to zones. Ver2's own log states the conclusion:

- `RL-0012` — *"Observability of motion is a property of the model, not the
  drawing"*
- `RL-0005`, `RL-0007` — visualization and renderer-coverage audits
- `RL-0014` — *"A stage that is never asked for its output is not in the
  pipeline"*

A drawing has to place every glyph. If the model does not say where a body is,
the renderer still must draw it somewhere — and that "somewhere" then reads back
as a design commitment. The renderer became an engineering decision-maker by
default, because rendering is total and the model was partial.

### B.4 Selection before the candidates were comparable

`assy/stages/s02_mechanical.py:408` always sets `selected_id=best.id`. The
rationale string in the same object records the ranking:

> *"ranked lexicographically on holding need, reversibility, unperformed
> functions and **element count**"* … and, when tied, *"NOT DERIVED — these rank
> exactly equal on every criterion and `{best.id}` is an **arbitrary stable
> pick** among them"*

Two defects, one line apart:

1. **`element count` as a ranking key.** A candidate that has not yet realized
   its supports, bearings, stops and guides has fewer elements — so incomplete
   candidates outrank complete ones. Ver2 reached this conclusion itself in
   `RL-0013`: *"Ranking measured how well a family was described, not how good
   it is."*
2. **An arbitrary tie-break emitted as a selection.** The code is admirably
   candid — it records `NOT DERIVED` — but it still populates `selected_id`, and
   every downstream stage reads that field. Candour in a rationale string does
   not stop a downstream consumer.

### B.5 Silent defaults

`assy/stages/s06_solver.py:51`:

```python
unit=c.unit or "mm",
```

A constraint with no unit becomes millimetres. Nothing is logged, nothing is
`UNRESOLVED`, and the resulting number is dimensionally unverifiable — yet it is
indistinguishable downstream from a unit the user actually stated.

This is the general shape of the Ver2 fallback family: *the pipeline must
produce an artifact, so a missing input is replaced by a plausible one.* Default
faces, default axes, origin placement for missing bodies, generic blocks for
unknown forms, and CAD-time fallback geometry are all the same move.

### B.6 Declarations accepted as realizations

The failure the negative Oracles must target hardest. A `revolute` label with no
fixed-side/moving-side realization, a coupling relation with no localized
engagement, a stop present in the physics XML but absent from the design — in
each case a *field exists*, a schema validator passes, and no physical thing has
been designed.

Tests that assert field presence certify this state as correct, which is why
`ORACLE_METHOD.md` §6.1 forbids negative cases that are mere inversions: the
dangerous case is the one that *looks* well-formed.

### B.7 Requirement evidence matched by weak proxy

Matching a requirement to evidence by *unit* means any millimetre satisfies any
millimetre requirement. Stroke satisfies clearance; deflection satisfies
tolerance. Evidence identity must be `(requirement_id, criterion_id, scenario_id,
observable)` — never dimension.

**Central failure mechanism of Ver2: there was no single design. Each stage
owned a private document, so identity, geometry and intent were re-derived at
every boundary, and every re-derivation needed a heuristic to fill what the
previous representation could not carry.**

---

## C. What is fundamentally different in Ver3

Each item states the failure it closes.

### C.1 One authoritative DesignState; stages emit patches

There is one store. A stage reads a **typed projection** of it and returns a
**DesignPatch** — additive, referencing existing entities by stable ID. No stage
returns a replacement document. *(Closes B.1.)*

The practical test: after Stage 05, the body created in Stage 02 must still be
*the same entity*, not a same-named copy.

### C.2 Stable identity, and extension instead of recreation

An entity is created once by exactly one owning stage. Others extend it. The
`STAGE_OWNERSHIP_MATRIX` makes "who may create this" a checkable property, so
duplicate-creation is a validator failure rather than a code review opinion.
*(Closes B.1.)*

### C.3 Explicit unknowns, alternatives, assumptions, maturity

Missing information becomes a typed value — `UNRESOLVED`, `NOT_VERIFIED`,
`UNSUPPORTED`, `CONTRADICTION`, `BLOCKING_ERROR` — never a default. Maturity is
a separate axis from existence: a body can exist and be `PROPOSED`, and a
`revolute` label never advances anything to `SPATIALLY_INSTANTIATED`.
*(Closes B.5, B.6.)*

### C.4 The obligation chain is the acceptance criterion

```
Requirement → Scenario → Obligation → Realization → Verification predicate → Evidence
```

An obligation is discharged only by traversing the whole chain. A label, a field,
a relationship or a simulation side-effect discharges nothing. *(Closes B.6.)*

### C.5 Candidates survive until they are comparable

No `selected_id` before every candidate has reached equivalent completeness —
obligations realized, packaging feasible, supports and reactions present, access
demonstrated, first-order parameters feasible. Mandatory realization elements
are **not** complexity penalties. Selection is a typed `SelectionDecision` with
evidence, rejected alternatives, unresolved equivalences and assumption
sensitivity. *(Closes B.4.)*

### C.6 Authoritative, executable spatial/kinematic semantics

Stage 04 produces frames, axes, joint parent/child frames, symbolic poses per
state, motion paths, engagement sites and swept volumes with **declared
fidelity** — enough to *evaluate* clearance, not merely to name it.

Qualitative labels are not banned; their **authority** is. A coarse region name
may annotate a metric pose or group entities for a report, but no geometric
predicate may take it as input, and dropping every annotation must leave every
clearance verdict unchanged (`INV-003.annotation_ablation`). What Ver2 lacked
was not labels — it was anything underneath them. *(Closes B.2.)*

### C.7 Rendering is a projection with a fixed decision budget

The renderer may choose camera, projection, transparency, section, label layout,
and explicitly-isolated display substitutions. Nothing it chooses re-enters
DesignState. If an image cannot answer "what moves, about which axis, reacted
where", the correct response is to classify *why* — incomplete model, renderer
gap, or out of scope — and never to add a label that papers over it.
*(Closes B.3.)*

### C.8 Embodiment and solving as a controlled coupled search

Stage 05 extends the existing entities into realizations and emits a solver
problem; Stage 06 actually solves it and reports `feasible` /
`infeasible` / `underdetermined` / `unsupported formulation` / `solver failure`.
Copying a value is not solving; an unparsed constraint is not satisfied.
*(Closes B.5, and Ver1's parameter-substitution habit.)*

### C.9 CAD compiles; it does not design

Stage 07 may only build what the ConstructionProgram and SolvedDesign specify. A
missing dimension is a build failure with a preserved dependency cone — never a
fallback block at the origin. *(Closes B.5.)*

### C.10 Evidence identity is semantic

Requirement ↔ evidence is linked by requirement ID, criterion, scenario and
observable semantics. Unit agreement is necessary and nowhere near sufficient.
*(Closes B.7.)*

### C.11 Dependency-based invalidation

Every entity records provenance, so a failed evaluation yields a dependency
cone, a repair set, an owning decision and a rerun closure — instead of a coarse
error enum mapped to a stage. *(Closes B.1's untraceability.)*

### C.12 Five distinct outcomes, and the one that matters most

`PASS` (scoped) · `FAIL` · `NOT_VERIFIED` · `UNSUPPORTED` · `INFEASIBLE`.

**`UNSUPPORTED` must never be reported as `INFEASIBLE`.** This single
distinction is Ver1's central lesson, promoted to an architectural invariant
(`INV-011`). Every `PASS` names its model, assumptions, state/scenario,
fidelity, evidence and excluded properties — so `PASS` is always a scoped claim.

### C.13 No runtime dependency on ASSY_NEW

The repository root (`seul22lee/ASSY_NEW.git`, the mdkg ontology) is read-only
reference material. Ver3 must run with the root `ontology/`, `data/` and `rules/`
directories renamed or absent. `KnowledgeProvider` is a documented boundary, not
an implemented adapter. *(Prevents re-creating Ver1's catalogue dependence
through a side door — a knowledge base that answers "which mechanism" is a card
library regardless of how well sourced it is.)*

---

## D. Research hypothesis

> **Can a stable, typed, shared design state support progressive mechanical
> synthesis and verification without either manually encoding complete product
> solutions as in Ver1, or allowing weak stage summaries and heuristics to
> invent missing embodiment as in Ver2?**

Ver1 answered "what mechanism" by enumeration and could not tell a missing card
from a physical impossibility. Ver2 answered "what design" by re-derivation and
had to guess whatever the previous representation could not carry.

Ver3's wager is that if identity, provenance, obligation and maturity are
carried in one shared state, and if every gap must be *named* rather than
filled, then a pipeline can make genuine partial progress — and, crucially, can
say precisely where it stopped and why. A system that reliably reports
`UNRESOLVED` and `UNSUPPORTED` in the right places is more useful, and more
falsifiable, than one that always emits a complete-looking design.
