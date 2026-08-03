# Micro-oracle — guided-slider

**Status:** STRUCTURALLY_COMPLETE — not yet audited, not locked.
**Tier:** micro_oracle. **Frozen dossier:** `../../_dossiers/DOS-guided-slider.md`.

## Capability

> Guided translation of one body relative to another along a defined line, with
> the non-translational freedoms removed.

That is the whole of it. This pack constrains a reusable capability, not a
product and not a mechanism.

## What this pack refuses to include

Every legacy fixture that exercised a slide also had a travel limit, and one of
them also had a latch. Neither belongs here. The capability defines guidance
*along a line*, not *between limits*, and says nothing about holding position.
Bounding is owned by `bounded-two-state-closure`; retention by `latch-retention`.

Keeping them out is not tidiness. If this pack required a travel limit, then
every design instantiating guidance would inherit a requirement no source ever
made — which is exactly how the legacy catalogue came to stand in for the design
space.

## The decisive evidence problem

The corpus reports off-axis deviation as **0.0 degrees exactly** against a 3.0
degree threshold, and counts it as a pass. Under a declared prismatic pair,
off-axis deviation is identically zero *because the model cannot produce
anything else*. The observable cannot fail, so it cannot pass in any evidential
sense.

`NRM-GS-007` generalises this into the pack's one verification-minimum
invariant: an observable offered as evidence of guidance must be able to take a
non-conforming value under the model that produced it. `EV-GS-002` records the
specific case; `NEG-GS-007` and `INA-GS-G` make crediting it a failure.

## Files

| File | Role |
|---|---|
| `normative.yaml` | 7 invariants + 3 required unresolved decisions + explicit scope exclusions |
| `freedoms.yaml` | 7 decisions no test may assert |
| `realizations.yaml` | 4 admissible + 7 inadmissible fixtures |
| `negative_cases.yaml` | 7 design + 5 process cases |
| `evidence_scope.yaml` | What the declared-pair evidence can and cannot support |
| `stage_expectations.yaml` | Representation obligations where the capability is instantiated |
| `source_map.md` | Every statement traced; every legacy value ranked and disposed of |

## The freedom-accounting rule

`stage_expectations.s04` requires all six relative freedoms to be accounted for
explicitly — one retained, five removed, each with the constraint that removes
it named. `ADM-GS-D` (a body located by three pads in a recess, with no guide
part at all) and `ADM-GS-B` (one non-circular bar) both satisfy this, which is
how the pack demonstrates it did not encode the legacy two-rail arrangement.
