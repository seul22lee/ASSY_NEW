# Oracle pack — C4-drawer (knob-driven cabinet drawer)

**Status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; **not** lock-ready,
**not** CAD-validated, **not** production authority. Every admissible fixture is
`NEEDS_GEOMETRY_VALIDATION`. Next authorized phase: adversarial CAD validation.

**Tier:** product case. **Parent:** none.
**Frozen dossier:** `../../_dossiers/DOS-C4-drawer.md`.

## The whole rank-1 source

> "Design a desktop cabinet whose drawer slides out horizontally when you turn a knob."

That sentence is everything the user asked for. The legacy record around it —
five bodies, a 200×140×90 cabinet, rail spacing, module and tooth count, a
120 mm stroke, a `CERTIFIED` verdict — is realization detail and run outcome.
None of it is a requirement, and `source_map.md` disposes of each field
explicitly.

This makes C4-drawer the pack where **invention pressure is highest**. Eleven
invariants come from one sentence; every one of them is either a fragment of the
command or a physical consequence with its premises written out. Seven decisions
are held open rather than filled in, including the stroke — the single value the
legacy pipeline was most confident about.

## Files

| File | Role |
|---|---|
| `normative.yaml` | 11 invariants + 7 required unresolved decisions |
| `freedoms.yaml` | 10 decisions no test may assert |
| `realizations.yaml` | 3 admissible + 9 inadmissible fixtures, machine-checked by tag algebra |
| `negative_cases.yaml` | 9 design + 8 process cases that must be rejected |
| `evidence_scope.yaml` | What the reused legacy evidence can and cannot support; 7 not-verified items |
| `stage_expectations.yaml` | Per-stage representation obligations; conditional s11 outcome rules |
| `source_map.md` | Every statement traced to a command fragment or marked excluded |

## Three specific traps this pack exists to catch

**The structural artifact.** The legacy run reports `tracks_straight = 0.0`
degrees against a 3.0 degree threshold and counts it as a pass. Under a
declared-pair model the slide *is* a prismatic coupling, so off-axis deviation is
identically zero because the model cannot produce anything else. That number
proves nothing about guidance. `EV-C4-002` and `NEG-C4-010` make crediting it a
failure.

**The reused verdict.** `stages.physics = "reused - PASS"`. No simulation was
run for this case; the lift variant's result was carried across. `NEG-C4-011`
requires evidence reuse to name its originating case or be treated as absent.

**The label as authority.** The legacy frame convention `+X = FRONT` is how
"horizontal" was established. `NRM-C4-002` requires a geometric relation to the
gravity direction; a label may accompany it but may never be its authority.

## The ambiguity is carried

Two legacy statements contradict each other about whether a toothed transmission
is over-engineered for a drawer. Neither is the command, so neither can require
or forbid a conversion family. The disagreement is recorded as UNR-C4-002 and
left standing; ADM-C4-C — a band-and-drum drawer with no teeth and no sliding
rail — exists to prove the pack did not quietly pick a side.

## Not merged with neighbouring cases

The hand-pulled latched drawer and the knob-and-rack fixture are separate cases
(DOS S8). Importing either would silently answer a question this pack holds open:
whether the drawer must be retained closed, and whether it must also move by
hand.

## Corrected at the independent semantic review

One short sentence of source produced eleven derived invariants, and six of them
were stronger than that sentence:

- **SF-6.1** guidance is required for the *required sliding behaviour*, not
  unconditional anti-rotation. The universal moment premise is withdrawn.
- **SF-6.2** the load path covers the drawer's own weight, plus any contents load
  an instantiating requirement declares. "Any contents load" was unbounded.
- **SF-6.3** terminal determinants apply only where an end of travel is
  *declared*. The frozen dossier says explicitly that no travel limit is stated.
- **SF-6.4** the crossing must not interfere; the cabinet need not be the bearing.
- **SF-6.5** reaction requirements are conditional on loads actually produced.
- **SF-6.6** `AMB-C4-01` is **reclassified**, not resolved. Two lower-rank legacy
  commentaries disagreeing about whether a gear is over-engineered creates no
  acceptance ambiguity, because neither could bind the family. It is now
  `LEGACY-CONFLICT-C4-01`, blocks nothing, and needs no human ruling — it is
  evidence that mechanism choice must stay free.