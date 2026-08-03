# Micro-oracle — latch-retention

**Status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; **not** lock-ready,
**not** CAD-validated, **not** production authority. Every admissible fixture is
`NEEDS_GEOMETRY_VALIDATION`. Next authorized phase: adversarial CAD validation.

**Tier:** micro_oracle. **Frozen dossier:** `../../_dossiers/DOS-latch-retention.md`.

## Capability

> Holding two bodies in a defined relative state against a disturbance, and
> releasing them by a deliberate action, repeatably.

Three clauses, and each one carries an invariant: *holds against* (NRM-LR-002,
NRM-LR-003), *releases by a deliberate action* (NRM-LR-004, NRM-LR-005),
*repeatably* (NRM-LR-006).

## The invariant that does the real work

**NRM-LR-004: the release action must be distinguishable from the disturbance.**

It follows from the capability statement alone. If whatever releases the
retention is indistinguishable from the disturbance it is supposed to hold
against, then the disturbance releases it too — and it does not hold. This is a
question no legacy fixture ever asked, because every fixture declared a
retention force window and read it back.

The invariant names no mechanism and fixes no discriminant. Direction, magnitude,
point of application, sequence, and a separate actuating element are all
admissible. `ADM-LR-D` (a detent released along the same path as engagement,
discriminating by force magnitude) and `ADM-LR-B` (a magnetic pair discriminating
by peel versus straight pull) both satisfy it in different ways.

## The circularity finding

The legacy corpus reports retention against `event_force_window_N = [15.0, 60.0]`.
That window is an **input parameter of the task definition**, not a measured
property. The same window appears in two different tasks — a fact about how the
tasks were written and about nothing else. Reporting it as an achieved result
asserts as an outcome what was supplied as a condition.

`NRM-LR-008` forbids it. `NRM-LR-007` closes the neighbouring hole: a retention
claim must name the disturbance it holds against, or it states no proposition
that could be false.

## Four principles, only one of them a snap

The legacy corpus realizes retention **exclusively** by snap features. Magnetic,
over-centre, detent, friction and threaded retention are absent from the library
but plainly not from engineering. A pack derived from that corpus would reject
all four of them.

So `realizations.yaml` admits a snap, a magnetic pair, an over-centre link and a
spring detent. If any invariant rejected one, the pack would have encoded the
library instead of the capability.

## Files

| File | Role |
|---|---|
| `normative.yaml` | 8 invariants + 4 required unresolved decisions + scope exclusions |
| `freedoms.yaml` | 7 decisions no test may assert |
| `realizations.yaml` | 4 admissible + 8 inadmissible fixtures |
| `negative_cases.yaml` | 8 design + 6 process cases |
| `evidence_scope.yaml` | The circularity finding; 4 not-verified criteria |
| `stage_expectations.yaml` | Representation obligations; conditional s11 outcome rules |
| `source_map.md` | Every statement traced; every legacy value ranked |

## What is deliberately absent

No retention load, no release effort ceiling, no cycle count, no tool policy, and
no disturbance case. All four are held open. The retained state is not required
to be a closed state either — retention of an open or an intermediate position is
squarely within the capability, and `FRE-LR-001` says so.

## Corrected at the independent semantic review

- **SF-9.1** — `NRM-LR-002` was carried as a direct fragment of the capability
  statement. It is not: "geometry on both bodies" appears nowhere in that
  statement and is a *consequence* of the interaction being realized. It is now a
  `NECESSARY_PHYSICAL_CONSEQUENCE`, and its wording asks for identified
  participating **material** rather than touching surfaces, so `ADM-LR-B`'s
  magnetic pair is admissible on its own terms.
- **SF-9.2** — the disturbance-naming and force-provenance minima moved into
  `evidence_cases.yaml`. A physically realized latch is no longer inadmissible
  because no test has named its disturbance.
- **SF-9.3** — the fixed-plurality rule is withdrawn.
- **SF-1.3** — capability fragments carry `PROJECT_DEFINED_CAPABILITY`.

`NRM-LR-004` — the release action must be distinguishable from the disturbance —
is unchanged. It remains the statement this pack exists for.