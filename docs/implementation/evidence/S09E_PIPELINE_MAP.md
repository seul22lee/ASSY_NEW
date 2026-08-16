# The real production pipeline, mapped to its actual end

Derived mechanically from production code at `2ee1098`, not from stage names or
prior notes. The question this had to answer before any paid call was "which
responsibilities are model-owned, which are deterministic, and where does CAD
happen". The answer to the third part is: **it does not happen in production.**

## What exists

| # | responsibility | write owner | kind | creates |
| --- | --- | --- | --- | --- |
| 1 | `s01` requirement capture | s01 | **LLM** | SourceClause, Requirement, Actor, Scenario, Freedom, Ambiguity, Assumption, DesignConstraint |
| 2 | `s02` obligation / demand / principle | s02 | **LLM** | Obligation, LoadCase, ReactionSiteRequirement, PhysicalEffectObligation, Candidate, AcceptanceContract, UnresolvedDecision, Assumption |
| 3 | `s03a` mechanism topology | s03 | **LLM** | Body, RigidGroup, Joint, Interface, Configuration, FunctionalRegion, UnresolvedDecision |
| 4 | `s03b` interaction and constraint | s03 | **LLM** | PhysicalInteraction, ConstraintRelation, MobilityExpectation, LoadPath, AssemblyStep, UnresolvedDecision |
| 5 | `s04a` envelope and reach | s04 | **LLM** | Envelope, ReachResult, EliminationRecord, ReferenceScale |
| 6 | `s04b` placement and motion | s04 | **LLM** | State, Transition, SweptVolume |
| 7 | feasibility | — | deterministic | assessment only |
| 8 | selection (comparison) | selection | deterministic | CandidateComparison |
| 9 | selection advisory review | selection | **LLM** | SelectionAdvisory, SelectionConcern |
| 10 | selection decision / checkpoint | selection | deterministic + human | SelectionDecision, HumanDecisionInput |
| 11 | assurance pass | s08-ish | deterministic | assurance status |
| 12 | S7 reconcile | lifecycle | deterministic | lifecycle records |

That is the whole canonical chain. `execute_s01_to_s04` in
`assy_v3/pipeline/progression.py` is the authoritative source-text-to-committed-
S04 path; `tools/run_window2.py` extends it through feasibility, selection,
advisory, assurance and reconcile.

## What does not exist

Families that a contract declares an owner for and **no production code creates**:

| owner | declared families | producing code |
| --- | --- | --- |
| s05 | Constraint, ConstructionStatement, Feature, Parameter, Realization | **none** |
| s07 | GeometrySignature | none |
| s08 | NegativeControl, VerificationPlanItem | none |
| s09 | EvidenceItem, NegativeControl, Witness | none |
| s11 | ExcludedClaim, RequirementEvaluation | none |
| s12 | FailureProvenance, HumanReviewQuestion | none |
| s04 | Witness | none |

`s05` is the one that matters here. It is the embodiment layer — features,
parameters, constraints, construction statements, realization — and it is the
layer that would turn a committed DesignState into something a CAD kernel could
build. It is fully specified in `DESIGN_STATE_CONTRACT` and
`STAGE_OWNERSHIP_MATRIX`, and **nothing writes it.**

The specification goes further than the family tables. `ver3/contracts/stages/`
holds full contracts for `S05`, `S06` and `S07` — engineering question, `llm_role`,
owned decisions, and numbered deterministic exit checks (S05-C1…C6, S06-C1…C6,
S07-C1…C6). s06 is declared a deterministic solver service and s07 a deterministic
compiler that "owns NO engineering decision". So the missing layer is unbuilt, not
undefined; [S05_CAD_GAP_SPEC.md](S05_CAD_GAP_SPEC.md) separates the two.

Consequently there is no solver stage, no construction-program generator, no CAD
builder and no CAD exporter anywhere in `assy_v3`. Checked three ways:

- no file under `ver3/assy_v3` imports `cadquery`, `build123d`, `OCC`, or writes
  `.step`/`.stl`;
- no `Op("CREATE", ...)` anywhere names any s05 family;
- no file that touches `DesignState` also touches geometry export — the
  intersection is empty.

## The CAD that does exist, and what it is

`ver3/cad_validation/*/executable_references/*/` holds real CAD: 26 STEP, 26
BREP, 204 PNG, 10 MP4. It is produced by hand-authored `build.py` scripts that
call `cadquery` directly.

Those scripts **do not import `assy_v3` and do not read DesignState.** They are
executable REFERENCES — independent evidence that a design satisfying a benchmark
source can be built as valid solids. They are not pipeline output, and no
traceability links their bodies or features back to canonical design entity ids.

`cadquery` is also not installed in `psed310` or the system interpreter, so those
references cannot currently be rebuilt in this environment either.

## What this means for an end-to-CAD campaign

A live sweep can exercise, at most:

```
source text
  → s01 → s02 → s03a → s03b → s04a → s04b        6 LLM responsibilities
  → feasibility → selection → advisory(LLM) → assurance → reconcile
  → END
```

There is no continuation from that committed state into embodiment, solving, or
CAD, because the code to do it has not been written. A paid sweep cannot reach
CAD, and no amount of deterministic continuation after the sweep can either.

This is a gap in the implementation, not a defect in any of the six
responsibilities, and it is recorded here so the campaign plan rests on what the
repository actually does.
