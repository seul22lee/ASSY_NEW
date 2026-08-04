# CAD revision restart checkpoint

Written at a deliberate pause part-way through the BM-001 CAD revision. Geometry
was not modified and no validation was run while producing this file.

**Nothing here is a validated result.** The snap-barb geometry builds and its
envelopes measure as stated; it has not been through the validation chain.

## Position

| | |
|---|---|
| Branch | `ver3-cad-positive-reference-pilot` |
| Committed Oracle scope commit | `0af83c90bbda611182d0544cc736f09ae89fc718` |
| Oracle files changed since that commit | **none** — `ver3/oracles/`, `ver3/oracle_tools/` and `ver3/phase0/` are byte-identical to it |
| Environment | `~/.venvs/ver3cad` (Python 3.8.10, cadquery 2.4.0, cadquery-ocp 7.7.0) |

## Verification run for this checkpoint

- 89 YAML files parse, 0 failures
- 9 Python files compile, 0 failures
- 31 JSON files parse, 0 failures
- EXE-BM001-01 builds four valid solids:

```
BODY-ENCLOSURE   valid  vol  94247.266   120.00 x 92.00 x 56.00
BODY-CLOSURE     valid  vol  43598.651   120.00 x 98.39 x 15.00
BODY-PIN         valid  vol   1067.937    85.80 x  7.00 x  7.00
BODY-BOLT        valid  vol   2513.274    16.00 x 16.00 x 32.00
compressed pin   valid  vol   1063.853
```

## What was done — EXE-BM001-01 hinge pin

The pin now carries an enlarged head at the insertion side and **two integral
cantilever snap arms** at the far side, giving bilateral axial retention:

| | |
|---|---|
| Bore diameter | **4.2 mm** |
| Relaxed lug span | **6.000 mm** |
| Shoulder projection past the bore | **0.9 mm** per side |
| Compressed insertion envelope | **4.154 × 2.400 mm** |
| Declared deformation volume difference | **4.08 mm³ (0.38%)** |

The compressed envelope fits the 4.2 mm bore in both directions, so the arms can
pass; the relaxed 6.000 mm span cannot return through it, so the shoulder blocks
withdrawal toward the head. The head blocks the other direction as before.

### The mistake this design replaced

The first attempt was a full-diameter cone split by one slot. Measured
compressed, it was **5.09 × 5.58 mm** against a 4.2 mm bore — it could not be
assembled at all. Splitting a cone compresses it only *across* the slot;
perpendicular to the slot its extent is unchanged, so it still cannot enter a
round bore.

Cantilever beams carrying lugs work because each beam is narrow in the direction
it does not move. The reasoning is in the `build_pin` docstring so it is not
rediscovered the hard way.

### The 4.08 mm³ deformation difference

The compressed configuration is produced by rotating each arm inward about its
root. That opens a small wedge at the root, so the compressed solid is 4.08 mm³
(0.38%) smaller than the relaxed one. This is a modelling artifact of the
articulated representation, not a physical claim, and it must be **reported as
the declared deformation magnitude** rather than hidden. Do not assert exact
volume conservation between the two configurations.

## What is pending

### EXE-BM001-01 — metadata and validation not done

| File | State |
|---|---|
| `build.py` | revised, builds |
| `parameters.yaml` | revised (snap-barb parameters added) |
| `manifest.yaml` | **stale** — no barb features; LIM-01 still records the one-direction limitation that HCR-BM001-002 rejected |
| `interactions.yaml` | **stale** — no barb shoulder / retaining-face interactions |
| `assembly.yaml` | **stale** — still describes a slip-fit pin, not a snap-in process |
| `poses.yaml` | not reviewed against the revision |
| `validate.py` | **not updated** — no axial-retention or compressed-envelope checks |
| `expected_evaluation.yaml`, `actual_evaluation.json` | stale |
| STEP / BREP / signature / validation reports | stale, from the pre-revision geometry |

**Known inconsistency:** `build.build()` hard-codes `BODY-PIN` as
`GENERIC_RIGID_METAL`, while `parameters.yaml` now declares
`GENERIC_COMPLIANT_POLYMER`. The build output above still shows the metal string.
This must be reconciled — a rigid metal pin cannot elastically snap, and the
whole point of the revision is a compliant split tip.

### Geometry signature

| | |
|---|---|
| Previous (committed, pre-revision) | `5586b96cc2e92e113a87ecb7180e8f8e2a3f820585c2a9d75fa6c8fdb13f2ee8` |
| Revised | **not computed** — the validator has not been re-run |

The signature will change: `BODY-PIN`'s volume moved from 1050.234 to 1067.937.

### EXE-BM001-02 — untouched

Unchanged from commit `94f3128`. It still contains `BODY-CAM`, the quarter-turn
cam geometry, the keyed bore, the keeper, the cam poses and assembly steps, and
still declares the cover liftable at full open. Human decisions HCR-BM001-004,
-005, -006 and -007 reject all of that; **none of that redesign has started.**

### Other gates not started

Requested section views (three for reference 1, five for reference 2); the
targeted validation checks; the report update; the human-review packet; the
sealed source-only packet; final revalidation.

## Recorded human decisions

`BM-001/reviews/HUMAN_CAD_REVIEW_DECISIONS.yaml` is complete and holds
HCR-BM001-001 through HCR-BM001-007. Independent human review of the revised
geometry remains **PENDING** and must not be claimed.

## Exact next step

**Finish EXE-BM001-01's metadata and validate it**, in this order:

1. reconcile the `BODY-PIN` material class between `build.py` and
   `parameters.yaml`;
2. update `manifest.yaml` — barb features, retire LIM-01, declare the compliant
   region;
3. update `interactions.yaml` — barb shoulder against the last knuckle's far
   face, arm-to-bore clearance;
4. update `assembly.yaml` — the six-step snap-in process;
5. add the axial-retention and compressed-envelope checks to `validate.py`;
6. run the validator and record the revised signature and the reason it changed.

Only then move to the three section views, and after that to EXE-BM001-02.

## Not created

No Demonstration CAD. No failure or inadmissible CAD corpus. No mutation CAD
artifacts. No `LOCK.json`. No production pipeline code. No Oracle file was
changed during the CAD work.
