# Generic CAD artifact requirements

These are format and record-keeping requirements. They say nothing about what to
design.

## Representation

Parametric **B-rep** solids. Every body must be a valid solid with non-zero
volume. A mesh is not a substitute.

## Deliverables

| File | Contains |
|---|---|
| `build.py` | the complete model, generated from parameters |
| `parameters.yaml` | every parameter: stable name, unit, value, purpose, allowable range where meaningful |
| `manifest.yaml` | bodies with stable semantic IDs, material class, role |
| `poses.yaml` | named states and the transform of each body that moves |
| `interactions.yaml` | every region where two bodies meet, classified (below) |
| `assembly.yaml` | ordered installation process |
| `model.step`, `model.brep` | exported geometry, both re-importable |
| `screenshots/` | readable views, including a section through each region where bodies are intended to meet |

Use millimetres throughout. Do not bury critical geometry in unexplained numeric
literals — if a number matters, it is a named parameter with a stated purpose.

## Stable identity

Bodies, features, axes, frames, states, interactions and assembly steps all need
stable IDs. Do not use transient kernel face indices as the persistent identity of
a feature; use construction-level semantic IDs.

## Interaction classification

For every region where body A and body B meet, assign exactly one of:

```
DECLARED_CONTACT
DECLARED_CLEARANCE
DECLARED_INTERFERENCE_FIT
DECLARED_COMPLIANT_INTERACTION
PERMANENT_JOIN
NOT_INTENDED_TO_INTERACT
```

Record for each: interaction ID, the two bodies, the participating feature IDs,
the type, the states or motion interval over which it is active, the nominal
clearance or interference, the numerical evaluation tolerance, and the physical
role.

If any motion in your design ends at a terminal condition rather than continuing
indefinitely, record what produces that terminal condition and classify the
interaction that realizes it.

## The one hard geometric prohibition

**No undeclared volumetric overlap.** Two solids may touch, and touching is not
interference. What is forbidden is two solids occupying the same space with
nothing declaring it.

The numerical tolerance is an *evaluation* tolerance, not a material allowance.
It may never be enlarged to hide macroscopic penetration:

```
contact_tolerance_mm <= min(0.02, 1% of the smallest local feature dimension)
```

Record and justify any different value.
