# The embodiment-to-CAD layer: what is specified, and what is unimplemented

Scoped, not implemented. Nothing here changes production code.

The pipeline terminates at `s04b`. Nothing turns a committed DesignState into
buildable geometry — see [S09E_PIPELINE_MAP.md](S09E_PIPELINE_MAP.md).

**The gap is implementation, not specification.** An earlier draft of this
document claimed `ConstructionStatement` had no required fields and that "the
contract does not yet say" what a construction program is. That was wrong, and it
was wrong because the audit behind it looked only in `entity_families` and
silently treated a miss as an empty definition. `ConstructionStatement` is in
`assurance_families`, and it is fully typed. The audit below reads both sections
and fails loudly on absence.

## One nuance that governs everything below

`ver3/contracts/stages/S05_CONTRACT.yaml`, `S06_CONTRACT.yaml` and
`S07_CONTRACT.yaml` all exist and are detailed. Every one of them classifies its
own content as `OPERATIONAL` and says so explicitly:

> No canonical stage responsibility exists for s05/s06/s07: the frozen
> architecture defines s01, s02, s03a, s03b, s04a, gate and s04b only. Inventing
> one to satisfy a projection test would create a fact rather than check one.

So these stages are **operationally specified and deliberately outside the frozen
canonical scope**. They explain; they do not define canonical semantics. Building
them is a scope decision, not a matter of filling in an unspecified area.

## Already defined by contract — families

All five s05 families and the one s07 family are fully typed. Read from
`DESIGN_STATE_CONTRACT` across both `entity_families` and `assurance_families`.

| family | owner | required fields | declared references |
| --- | --- | --- | --- |
| `Parameter` | s05 | `symbol`, `unit`, `status` | — |
| `Constraint` | s05 | `expression`, `parameters`, `kind` | — |
| `Feature` | s05 | `body`, `feature_kind`, `geometry` | `body → Body` |
| `Realization` | s05 | `addresses_obligations`, `participating_features`, `verification_predicate` | `→ Obligation`, `→ Feature` |
| `ConstructionStatement` | s05 | `operation`, `operands`, `parameters` | — |
| `GeometrySignature` | s07 | `signature_sha256`, `per_body`, `critical_dimensions` | — |

Contract rules already attached to these:

- `ConstructionStatement` — *"Stage 07 compiles these or fails, preserving the
  originating statement (INV-006)."*
- `Realization` — must cite the obligation ids it discharges (INV-008); one with
  no verification predicate discharges nothing.
- `Parameter` — `unit` is mandatory; a null unit is a schema error (INV-004).
- `Feature` — OCCT/CAD face indices are never a persistent identity.

That last one matters for the traceability the reviewer needs. `Feature.body →
Body` and `Realization.addresses_obligations → Obligation` already make *why does
this CAD feature exist, and which upstream decision caused it* an expressible
query. No new ontology is required for it.

## Already defined by contract — roles and checks

| | s05 | s06 | s07 |
| --- | --- | --- | --- |
| question | what geometry makes each declared relation real | do values satisfy every constraint, and if not which conflict | does the declared program with solved values produce valid solids |
| `llm_role` | **High** for feature proposal and program shape; **NONE** for completeness | **NONE** | **NONE** |
| creates | Feature, Realization, Constraint, Parameter declarations, ConstructionStatement, ROI definitions | — | GeometrySignature |
| extends | Body, RigidGroup, Joint, Interface, compliant Joint geometry | Parameter values, Constraint status | Body, Feature |
| exit checks | S05-C1…C6 | S06-C1…C6 | S07-C1…C6 |

s06 is declared a **deterministic solver service**, invocable by s05 within one
stage attempt rather than a sequential barrier — `s05` and `s06` form one bounded
convergence block with `s04b`. It owns no family and may not default a missing
unit, report `feasible` for an underdetermined system, or silently pick one
solution from a family without recording the freedom.

s07 *"owns NO engineering decision. It owns only facts about what compiled."*

The exit checks are already written and are unusually concrete — S05-C4 requires
every Obligation to be cited by some Realization carrying a verification
predicate; S06-C6 requires identical input to produce identical output; S07-C2
requires every body to be a single connected solid; S07-C3/C4 bound BREP and STEP
round-trip volume deltas; S07-C6 requires a failure to cite the originating
`ConstructionStatement` and its dependency cone.

So the acceptance criteria for this layer exist. What does not exist is anything
that runs.

## What is actually missing

Implementation only, in dependency order:

1. **An s05 producer.** No code creates any of its five families. Per contract
   this is partly model-owned (feature proposal, program shape) and partly
   deterministic (completeness is enumeration over s03's relation set).
2. **An s06 solver.** No solver module exists anywhere in `assy_v3`.
   `Parameter.status` implies solved / unsolved / over-constrained states that
   nothing computes.
3. **An s07 compiler.** Nothing consumes `ConstructionStatement` or builds
   geometry. `cadquery` is not installed in `psed310` either.
4. **The convergence block wiring** between s04b, s05 and s06 that the contracts
   describe.
5. **A trace/UI extension** so the existing review interface can show features,
   parameters, the solver result and the compiled solids. The trace already
   records these nodes as `NOT_IMPLEMENTED` rather than omitting them.

## What must not be done when it is built

- **Do not let the compiler invent geometry.** A construction statement missing a
  dimension must produce a recorded deterministic failure citing the originating
  statement — which is exactly what S07-C6 already requires. Silent defaulting
  would be invisible in the resulting solid.
- **Do not create a second design authority.** Features and realizations belong in
  DesignState under s05's ownership, addressed by canonical ids. A CAD-side
  identity scheme that does not resolve to them reproduces the traceability gap
  the existing `cad_validation` references already have.
- **Do not let a solved value read as a good value.** `Parameter.status = SOLVED`
  is a statement about the equations, not about the engineering.

## The existing reference CAD

`ver3/cad_validation/*/executable_references/*/build.py` already produce valid
B-rep solids for these benchmarks with named bodies and declared motion states.
They are hand-authored, call cadquery directly, import no part of `assy_v3` and
read no DesignState, so they cannot be promoted into the pipeline. They do show
the granularity a `ConstructionStatement` sequence would need to reach, and they
are worth reading as a target when this layer is scheduled.
