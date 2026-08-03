# Dossier BM-001-3 — FROZEN

Parent dossier: `DOS-BM-001.md` (inherited unchanged).

## S1. Delta source requirement (rank 1)
Locator: `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001-3_requirementspec.json`. `meta.object_id = SPEC-001-3`.

`meta.notes[0]` verbatim: "BM-001 with one requirement added: the enclosure
rests on a curved back and opens through a flat top. Everything else is
identical, so any difference traces to that and nothing else."

| ID | kind | statement (verbatim) | verification.kind | observable (verbatim) |
|---|---|---|---|---|
| REQ-011 | environmental | The enclosure rests on a curved back and opens upward through a flat top face. | inspection | curved underside, flat opening on top |

All 8 BM-001 requirements and all other fields byte-identical to BM-001.

## S2. Missing criteria and quantities
- No curvature profile, radius, or single/double curvature.
- No stability criterion, tipping load, or definition of "rests".
- No support condition (feet, land, cradle) named.
- No curvature axis orientation.
- No top-face dimensions.

## S3. Freedoms visible in the source
"curved back" / "curved underside" requires curvature to exist and says nothing
about its form. The word *cylinder* does not occur. The aperture is fixed to the
top face; the closure-connection side is not stated.

## S4. Source conflicts / ambiguities — **AMB-001-3-01, recorded not resolved**
A curved underside may rock or roll. REQ-011 asserts the enclosure "rests" on it
but supplies no stability criterion and names no support condition. Whether
"rests" implies static stability, or merely names the orientation, is not
determinable from rank-1 sources.

## S5. Evidence available
None for the delta. `/home/ftk3187/github/ASSY_Ver2.0/out/BM-001-3/run-*` = 7 runs, rank 5.

## S6/S7. As DOS-BM-001.
