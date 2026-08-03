# BM-001-3 — Latching storage box on a curved back, opening through a flat top

## Problem intent

BM-001 plus one environmental requirement: the enclosure rests on a curved back
and opens upward through a flat top face.

## Relationship to BM-001

A **documented single-requirement delta** (`inherits: BM-001`), on the spec's own
statement that everything else is identical. Three added invariants, three added
freedoms, two added unresolved decisions, three added negative cases.

## Fixed requirements (delta)

`NRM-BM-001-3-001` curved resting boundary + planar top containing the aperture ·
`NRM-BM-001-3-002` a *derived* resting configuration · `NRM-BM-001-3-003` the
closure sweep clears the curved boundary too.

## Freedoms (delta)

Curvature profile family, stabilisation strategy, curvature axis orientation.
`FRE-BM-001-006` is narrowed (no fully prismatic enclosure) and
`FRE-BM-001-003` is narrowed (aperture fixed to the top; connection side still
free).

## Known ambiguities

Two, both genuine. The curvature **form** is unstated, and — more interesting —
**how a curved-bottomed object rests stably is unstated**. A curved underside
may rock. The pack requires the resting configuration to be *derived* and marks
stability `NOT_VERIFIED` for want of a criterion.

## Why this case is included

This is the pack that most directly punishes a rectangular-box assumption. It
also introduces a property the BM-001 family otherwise lacks: a *resting*
configuration that is a mechanical consequence rather than a modelling
convention.

## Pipeline capabilities stressed

- Non-prismatic boundary geometry end-to-end, including CAD compilation.
- Swept clearance against a curved surface, not just planar walls.
- Deriving an orientation from contact geometry instead of a role label.
- Correct handling of a capability gap: `NEG-BM-001-3-002` accepts `UNSUPPORTED`
  but rejects continuing as if the enclosure were valid.

## What would constitute overfitting here

1. Encoding **"cylinder"**, or any specific radius or profile, as normative.
2. Fixing the stabilisation strategy — feet, land, cradle or mass distribution.
3. Fixing the curvature axis orientation.
4. Requiring the closure to be hinged at a particular edge of the flat top.
5. Any comparison against `V2/out/BM-001-3/run-*`.

## Corrected at the independent semantic review

- **SF-4.1** the missing stability criterion no longer blocks derivation of the
  resting configuration. Contact between a curved underside and a plane is
  computable from geometry; what the missing criterion blocks is a stability PASS
  and a tipping-margin claim.
- **SF-4.2** `ADM-BM-001-3-B` claimed three contact patches from a single
  spherical cap, which yields one ideal point contact. It was held together by its
  tags. Revised to three raised lobes with coplanar apexes.
- **SF-4.3** `ADM-BM-001-3-C` rested on a flat land, so its load-bearing contact
  was not on the curved back. The land became a non-load-bearing relieved recess.
  The design the old fixture described is now the inadmissible `INA-BM-001-3-D`.

A source reading is recorded explicitly as `RDG-BM-001-3-01` so a reviewer can
reject it in one place.