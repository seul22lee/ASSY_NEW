# Micro-oracle — bounded-two-state-closure

**Status:** STRUCTURALLY_COMPLETE — not yet audited, not locked.
**Tier:** micro_oracle. **Frozen dossier:** `../../_dossiers/DOS-bounded-two-state-closure.md`.

## Capability

> A closure that reaches two defined states by a bounded motion, where the bound
> at each extreme is physically produced.

The pack was originally called `hinge-and-stop`. The auditor rejected that name
(F-3C-001) and it was right to: a capability identifier that names a joint type
and a feature type biases every reader toward them, which is exactly why the
rotary-to-linear micro-oracle was renamed earlier. Nothing here requires a hinge
or a stop feature — `ADM-HS-C` is a sliding cover, and `ADM-HS-D` bounds both
extremes by a pin running out in a slot, with no added feature at all.

## The evidence, stated exactly

The legacy m0 pair is the strongest evidence in the whole corpus: genuine **V-B
contact**, a matched control differing in exactly one feature — the presence of
the limit — at the same solver settings. That is a controlled experiment, and it
deserves to be recorded as one.

And it still does not show what it appears to show. **Every seed-0 criterion
passes in both members**: pin retention, travel interference, pin/bore
interface, settling, and the angle criterion. The unbounded control swings to
**219.65 degrees** — plainly far past any intended extreme — and the thresholded
criterion (`>= 90`) accepts it. The two verdicts differ only through seed
aggregation, 5/5 against 1/5.

What the pair supports: *removing the limit produced seed-level instability
across a five-seed sweep.*
What it does not supply: *a single-run criterion distinguishing a bounded closure
from an unbounded one.*

`NRM-HS-007` turns this into an invariant — a criterion offered as evidence that
a bound is present must be able to fail when the bound is removed. `UNR-HS-004`
records that no such criterion exists yet, and refuses to invent one.
`NEG-HS-014` requires any seed-aggregated verdict to carry its aggregation rule.

## Bounding is not holding

A bound determines where the motion ends. It does not keep the closure there.
`UNR-HS-002` holds that question open and `NEG-HS-011` forbids discharging a
holding obligation with a bounding realization — otherwise one feature would
appear to satisfy two capabilities.

## Files

| File | Role |
|---|---|
| `normative.yaml` | 7 invariants + 4 required unresolved decisions + scope exclusions |
| `freedoms.yaml` | 7 decisions no test may assert |
| `realizations.yaml` | 4 admissible + 7 inadmissible fixtures |
| `negative_cases.yaml` | 7 design + 7 process cases |
| `evidence_scope.yaml` | The matched-pair finding, with every seed-0 value recorded; 4 not-verified criteria |
| `stage_expectations.yaml` | Representation obligations; conditional s11 outcome rules |
| `source_map.md` | Every statement traced; every legacy value ranked |

## What is deliberately absent

No open angle — the 90 degrees everywhere in the corpus is the m0 fixture's own
threshold. No bounding principle: the corpus bounds motion *only* by a discrete
stop, while gravity rest, over-centre, detent, friction and geometric run-out are
absent from that library and entirely present in engineering. No load, no life,
no holding requirement.

## Corrected at the independent semantic review

- **SF-10.1** — `NRM-HS-003` required one identical relative constraint to persist
  through the whole motion. It now requires continuous constraint *coverage*:
  the mode may change and features may hand off. `ADM-HS-E`, a flexure handing off
  to a moulded rib, is in the set to keep that reading out.
- **SF-10.2** — `NRM-HS-005` required each extreme to have its "own condition",
  which read as a distinct feature per extreme. It now requires each extreme to be
  independently **evaluated**; one continuous slot (`ADM-HS-D`) or one magnetic
  field (`ADM-HS-F`) may produce both. What is forbidden is copying an evaluation
  result across extremes.
- **SF-10.4** — criterion discrimination moved into `evidence_cases.yaml`. Whether
  a test can distinguish a bounded closure from an unbounded control is a property
  of the test.
- **SF-1.3** — capability fragments carry `PROJECT_DEFINED_CAPABILITY`.

Bounding remains separate from holding (SF-10.3), and the mechanism-neutral name
is kept with `historical_aliases: [hinge-and-stop]`.