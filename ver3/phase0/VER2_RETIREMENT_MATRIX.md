# Ver2 retirement matrix

**Default disposition is RETIRE.** `REIMPLEMENT` means *the underlying
mathematics or mechanism may be written again from scratch, with new tests, and
without importing legacy code*. `REFERENCE_ONLY` means *read as evidence, never
executed, never imported*.

**The distinction this matrix must keep sharp:**

> Retiring a *failed abstraction* is not the same as refusing an
> *implementation detail*.
> Rigid-body transform composition is arithmetic and may be rewritten.
> `SpatialZone.CORE` is a policy about where things belong.
>
> **Refined by correction (1):** what is retired is the *authority* of such a
> label, not its existence. A coarse region label may annotate a metric pose,
> index entities, or seed a human-facing summary. It may never be the
> authoritative value of, or the proof of, a pose, extent, offset, path,
> contact, clearance or feasibility verdict. See `INV-003.permitted_uses`.

Legacy root paths: `V1 = /home/ftk3187/github/ASSY_Ver1.0`,
`V2 = /home/ftk3187/github/ASSY_Ver2.0`.

---

## 1. Spatial representation

| # | Legacy location | Thing | Why it failed | Disposition | Ver3 replacement | Preventing validator |
|---|---|---|---|---|---|---|
| R-01 | `V2 assy/domain/upstream.py:1724` `ConceptVisualization`; built at `assy/stages/s04_concept.py:1332` | Rendered sheet as Stage 04's authoritative output | Rendering is *total* — every glyph needs a position — while the model was *partial*. The renderer supplied the difference, so drawing decisions became design decisions. Ver2's own `RL-0012` states it: *"Observability of motion is a property of the model, not the drawing."* | **RETIRE** | Stage 04 emits `spatial_kinematic_definition.json` (frames, axes, joint frames, symbolic per-state poses, engagement sites, swept volumes with declared fidelity). `renders/` is non-authoritative output. | `INV-005` renderer-origin check: no DesignState entity may have provenance naming a render step |
| R-02 | `V2 assy/domain/upstream.py:1547` `SpatialZone` (`CORE`/`FLANKING`/`END`/`OFFSET`/`BOUNDARY`/`EXTERNAL`) | Coarse qualitative region as position | Cannot express clearance, parallelism, or corridor occupancy. Motion questions became unanswerable, so downstream stages invented answers. | **RETIRE** | Frames + transforms + explicit poses per state | `INV-003` — enum/ordinal metadata may annotate, never authorise, a geometric property |
| R-03 | `V2 assy/domain/upstream.py:1522` `AxisStation` (`NEGATIVE_END`/`MID_SPAN`/`POSITIVE_END`/`RANGE_MIN`/`RANGE_MAX`) | Ordinal station used as the authoritative limit location | Two stops at `POSITIVE_END` are indistinguishable, so one generic stop can silently satisfy two distinct extremes. | **RETIRE as authority** (permitted as annotation) | Joint-coordinate values with units, per state, per limit | `INV-003`; `INV-008` two_extremes_distinct — distinct *contact feature or predicate*, not necessarily distinct parts |
| R-04 | `V2 assy/domain/upstream.py:859` `RadialPosition` (`ON_AXIS`/`OFF_AXIS`) | Two-valued radial placement | Cannot express a mesh offset, a bearing bore, or an interference. `anchor_hard` needed `axis_off = rack_pitchline + d/2`; this type cannot hold it. | **RETIRE** | Offset vectors in a named frame, unit-bearing | `INV-003` |
| R-05 | `V2 assy/domain/upstream.py` `BodyPlacement.span: list[int]` — *"an ordinal interval … not a coordinate and not a dimension"* | Integer-slot occupancy | Self-documented as metric-free. A moving platform occupying its whole travel corridor is unrepresentable-as-wrong. | **RETIRE** | Swept volume with fidelity + corridor clearance predicate | `INV-003`; corridor-occupancy negative case |
| R-06 | `V2` Stage 04 state motion | Interval swapping presented as rotation | Exchanging two ordinal intervals is not a rotation; no axis, no path, no swept region, so clearance is undecidable. | **RETIRE** | Joint with axis, parent/child frames, path, swept volume | `INV-006` motion realization check |
| R-07 | `V2` Stage 04 state motion | Fixed-offset translation between states | A constant offset is not a motion model; it cannot show interference along the path, only at endpoints. | **RETIRE** | Parameterised path with sampled/analytic sweep, fidelity declared | `INV-006` |
| R-08 | `V2` Stage 04 | AABB label asserted as motion proof | A bounding box that does not overlap proves nothing about a swept solid; and equal boxes in two states hide a closure that changes size. | **RETIRE** | Swept-volume clearance predicate with declared fidelity; AABB permitted only as a *conservative* pre-filter, labelled as such | `INV-009` PASS-scope check |
| R-09 | `V1 knowledge/templates/host_templates.py` `TEMPLATES`; `V2` generic-block fallback | Generic rectangle as mechanical realization | A block is a placeholder, not an embodiment; it satisfies no obligation. | **RETIRE** | Realization must cite the obligations it discharges | `INV-008` obligation-realization check |

**Reusable arithmetic underneath (not an exemption).** Homogeneous transforms,
frame composition, axis-angle/quaternion conversion, AABB/OBB intersection, and
swept-volume sampling are ordinary geometry. Ver3 will **REIMPLEMENT** them from
scratch with its own tests. No Ver2 module is imported, and no *policy* built on
them returns.

---

## 2. Decision heuristics

| # | Legacy location | Thing | Why it failed | Disposition | Ver3 replacement | Preventing validator |
|---|---|---|---|---|---|---|
| R-10 | `V2 assy/stages/s04_concept.py:308` `_zone_of(pl) -> SpatialZone` | Role → zone lookup | A role is a functional label; a position is a geometric fact. Mapping one to the other manufactures geometry from vocabulary. | **RETIRE** | Position derived from constraints, contacts and packaging obligations, with `derived_from` provenance | `INV-003` |
| R-11 | `V2` Stage 03 | Role → face / region-type → location | Same defect as R-10 at product scale: yields "automatic side drive", "fixed assembly opening". | **RETIRE** | Face/opening chosen only from access, load-path and assembly-dependency evidence, or left `UNRESOLVED` with alternatives | `INV-003`, `INV-008` |
| R-12 | `V2` downstream stages | Element/declaration order as an engineering decision (e.g. first element = support end) | Order is a serialization artifact. Reordering the input changes the design. | **RETIRE** | Explicit typed relations; determinism from canonical serialization, never from list order | `INV-014` order-independence: permute input entity order, output must be identical |
| R-13 | `V2 tools/run_benchmarks.py:42-49` — `spec=spec` passed to Stage 02 **and** Stage 03 | Re-reading the raw request downstream of Stage 01 | Each re-parse is an independent interpretation; two stages can disagree about the same sentence with no way to detect it. | **RETIRE** | Stage 01 is the sole consumer of raw text. Stages ≥02 receive typed projections only. | `INV-002`: raw-request field absent from every projection ≥ Stage 02 |
| R-14 | `V2` any stage | Benchmark-ID / product-name branches | Encodes the suite into the system; generalization becomes unmeasurable. | **RETIRE** | Behaviour depends only on typed content | `INV-015`: grep for case IDs in `assy3/`; plus renamed-case run must be identical |

---

## 3. Candidate handling

| # | Legacy location | Thing | Why it failed | Disposition | Ver3 replacement | Preventing validator |
|---|---|---|---|---|---|---|
| R-15 | `V2 assy/stages/s02_mechanical.py:408` `selected_id=best.id` | Stage 02 always names a winner | Selection precedes the evidence that could justify it. The same line admits ties are *"an arbitrary stable pick"*, yet still publishes the field, and every downstream stage reads it. | **RETIRE** | Candidates persist as branches; `SelectionDecision` is typed, evidence-bearing, and permitted only after Stage 03–04 comparable feasibility | `INV-007`: no `SelectionDecision` before completeness+feasibility gates |
| R-16 | `V2 s02_mechanical.py:408` rationale — *"ranked … on holding need, reversibility, unperformed functions and **element count**"* | Fixed heuristic scoring, part-count weighted | A candidate that has not yet realized its supports, stops, bearings and guides has fewer elements, so **incompleteness wins**. Ver2 concluded this itself in `RL-0013`. | **RETIRE** | Comparison only at equivalent obligation completeness; mandatory realization elements are never complexity penalties | `INV-007`; plus negative case "incomplete candidate wins on part count" |
| R-17 | `V2` Stage 02 | Stable sort used as an engineering decision | Reproducible ≠ justified. Determinism is a build property; it is not evidence. | **RETIRE** | Ties remain `UNRESOLVED` with named discriminating requirements | `INV-007` |

---

## 4. Product architecture and second design worlds

| # | Legacy location | Thing | Why it failed | Disposition | Ver3 replacement | Preventing validator |
|---|---|---|---|---|---|---|
| R-18 | `V2` Stage 03 `ProductArchitecturePlanner` | Placeholder product architecture — role→region conversion, default two-piece shell, automatic side drive, fixed assembly opening, generic load-path prose | Product prose generated from role names, unconnected to obligations. | **RETIRE** | Enclosure/cavity topology, openings, access paths, interface and load-path ownership, assembly dependencies — each traced to an obligation or explicitly `UNRESOLVED` | `INV-008` |
| R-19 | `V2` Stage 05 Engineering Integration | Independent commitment truth store | A second design world with its own entities; upstream IDs no longer authoritative. | **RETIRE** | Stage 05 emits a patch extending existing bodies/joints/interfaces by ID | `INV-001` duplicate-entity check |
| R-20 | `V2` Stage 05 | Free-string subjects; catalogue reseeding | A string subject cannot be dereferenced, so it cannot be validated, invalidated or traced. | **RETIRE** | Typed references only; every subject resolves to an existing entity | `INV-001`; reference-resolution validator |

---

## 5. Solving, CAD, evidence

| # | Legacy location | Thing | Why it failed | Disposition | Ver3 replacement | Preventing validator |
|---|---|---|---|---|---|---|
| R-21 | `V2 assy/stages/s06_solver.py:51` `unit=c.unit or "mm"` | Default unit | Silently makes a dimensionless number metric. Indistinguishable downstream from a user-stated unit. | **RETIRE** | Missing unit ⇒ `UNRESOLVED` / `BLOCKING_ERROR`; units validated dimensionally | `INV-004` silent-default check |
| R-22 | `V2` Stage 06 | Symbolic expression deferred to CAD time | Defers the decision to a stage that has no authority to make it; the solver reports success for something unsolved. | **RETIRE** | Stage 06 returns `feasible` / `infeasible` / `underdetermined` / `unsupported formulation` / `solver failure` | `INV-010`; unparsed constraint ⇒ `unsupported formulation` |
| R-23 | `V2` Stage 06 | Copying existing values and calling them solved; objectives recorded but not optimized | No residuals, no active set, no margins — a report shaped like a solution. | **RETIRE** | `constraint_residuals.json`, active constraints, margins; optimality only with optimization evidence | `INV-010` |
| R-24 | `V2` Stage 07 | CAD fallback geometry and placement — missing placement → origin, unknown form → block | CAD acquires design authority precisely where the design is weakest, hiding the gap. | **RETIRE** | Build failure preserving originating construction statements + dependency cone | `INV-006` CAD-origin check |
| R-25 | `V2` Stage 11 | Unit-based evidence matching | Any millimetre satisfies any millimetre requirement — stroke satisfies clearance. | **RETIRE** | Match on `(requirement_id, criterion_id, scenario_id, observable)` | `INV-012` semantic-identity check |
| R-26 | `V2` Stage 10 | Missing metric omitted from the report | Absence reads as "nothing to report"; a requirement then passes on surviving metrics. | **RETIRE** | Exactly one outcome per planned observable: `MEASURED`/`NOT_MEASURED`/`INVALID`/`NOT_APPLICABLE`/`EXECUTION_FAILED` | `INV-013` observable-completeness check |
| R-27 | `V1` `KG_NO_PERMITTED_REALIZER` (`benchmark.py:145-150`), `V-03` out-of-vocabulary (`benchmark.py:159-162`) | Missing knowledge reported as `INFEASIBLE` | `lead_screw.py` *existed* in the library and D1-screw-jack was still `INFEASIBLE`. Conflates four distinct situations into one verdict. | **RETIRE** | `UNSUPPORTED` is a distinct terminal status; `INFEASIBLE` requires a physical argument | `INV-011` — highest severity |

---

## 6. Tests

| # | Legacy location | Thing | Why it failed | Disposition | Ver3 replacement | Preventing validator |
|---|---|---|---|---|---|---|
| R-28 | `V2 tests/` | Field-presence acceptance | Certifies that a schema was populated, not that a thing was designed. A `revolute` label passes. | **RETIRE** | Obligation→realization→predicate→evidence assertions | `INV-008` |
| R-29 | `V2 tests/` | Glyph-per-schema-field render acceptance | Confirms the renderer drew a field; says nothing about whether the model held the information. | **RETIRE** | Visual review answers the twelve Stage-04 questions, or classifies why it cannot | `INV-005` |
| R-30 | `V1/V2 tests/` | Benchmark-specific exact layout / coordinate tests | Freezes one solution as truth; any equally valid design fails. | **RETIRE** | Exact comparison confined to IDs, schema versions, units, user-stated requirements, provenance, declared equations, canonical serialization, Oracle metadata | `INV-014`; `ORACLE_METHOD.md` §11 |
| R-31 | `V1 tasks/benchmark/goldens/`, `V2 BM-*_GOLDEN_STAGE_OUTPUTS.md` | Legacy golden equality | Golden outputs are one sample from an allowed set, and were produced by the systems under audit. | **REFERENCE_ONLY** | Rank-5 historical example in `source_map.md`; never an assertion target | `ORACLE_METHOD.md` §3 rank rule, check C-4 |
| R-32 | Any | Passing-test count as evidence of correctness | Counts measure coverage of what was asked, not of what matters. | **RETIRE** | Oracle stage projections + negative cases + capability gaps reported explicitly | Completion criteria, not a test |

---

## 7. Explicitly *not* retired

| Concept | Legacy trace | Disposition | Condition |
|---|---|---|---|
| Stable typed IDs | V1 `Piece.id`, `ElementInstance.id`; V2 `ObjectMeta.object_id` | **REIMPLEMENT** | New ID grammar, ownership rules in `STAGE_OWNERSHIP_MATRIX.md`; no legacy ID format |
| Unit-bearing values | V2 `Quantity`-like fields | **REIMPLEMENT** | Unit mandatory; `dimensionless` explicit; no `or "mm"` |
| Provenance / `derived_from` | V2 `BodyPlacement.derived_from` | **REIMPLEMENT** | Extended to invalidation + supersession + dependency cone |
| States and transitions | V1 `Behavior`, V2 state sets | **REIMPLEMENT** | Must carry poses and swept regions, not ordinal intervals |
| Joints and couplings | V1 cards, V2 kinematic model | **REIMPLEMENT** | Joint requires axis + parent/child frames + realization; a label alone is inert |
| Access paths | V2 access notions | **REIMPLEMENT** | Must terminate at the actual target (platform, not enclosure) |
| Obligation ownership | V2 obligation ideas | **REIMPLEMENT** | Realization must cite discharged obligations |
| Invalidation / supersession | V2 partial | **REIMPLEMENT** | Dependency-cone driven |
| Frame & transform mathematics | V1 physics tilt, V2 layout maths | **REIMPLEMENT** | Pure geometry, new tests; no legacy policy on top |
| Deterministic validation patterns | V1 `V-01…V-17` | **REFERENCE_ONLY** | Read for *what* they checked; Ver3 validators are contract-derived, not ported |
| Ver1 mechanism cards / host templates | `V1 knowledge/` | **REFERENCE_ONLY** | Reading a card imports a pre-solved sub-design (§A.1). Never imported, never a knowledge source |
| MuJoCo V-A/V-B protocol distinction | V1 `m0`, `m13`, `m17_gear_vb` | **REFERENCE_ONLY** → later **REIMPLEMENT** | The V-A/V-B *distinction* is sound and directly informs `evidence_scope.fidelity`. Harness not ported |

---

## 8. Uncertain dispositions

Recorded rather than forced. Each blocks nothing today.

| # | Concept | Question | Provisional |
|---|---|---|---|
| U-01 | MuJoCo as Ver3's kinematic evidence engine | Is a rigid-body engine with declared pairs the right fidelity for Stage 09, given that V-A results carry structural artifacts (`offaxis_max_deg = 0.0` by construction)? | Keep as *one* capability with mandatory `fidelity` + `structural_artifacts`; decide at Stage 08/09 contract time |
| U-02 | `HostTemplate` / anchor idea | Is "named attachment site on a host body" a sound primitive, or Ver1's card model in disguise? | Lean **REIMPLEMENT** as a pure topological anchor (V2 `RL-0010`) with **no** geometry or parameter bounds attached |
| U-03 | Ver2 `UnresolvedLayoutChoice` / `LayoutConflict` | These are genuinely good — they record openness instead of resolving it. Reimplement, or is this subsumed by the general `UNRESOLVED` type? | Lean subsume; revisit at `DESIGN_STATE_CONTRACT.md` |
| U-04 | Ver1 `carve` composition semantics (`replace` vs `union`) | Real embodiment knowledge — but it arrives bonded to card geometry. | Defer to Stage 05 contract; do not import |
| U-05 | Where mechanism knowledge comes from at all | If Ver3 has no card library, what proposes candidates in Stage 02? | Open research question. `KnowledgeProvider` is a boundary, deliberately unimplemented. Must not be closed by importing V1 cards or the root ASSY_NEW ontology |

U-05 is the load-bearing one: it is exactly where Ver3 could silently become
Ver1 again.
