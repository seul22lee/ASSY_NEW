# BM-001-3 — source map

> **Pack status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; not lock-ready, not
> CAD-validated. Every admissible fixture is `NEEDS_GEOMETRY_VALIDATION`.


Inherits `BM-001/source_map.md` in full. Delta sources only.

## Rank 1 — delta requirement

| Source id | Path | Key | Verbatim | Used by |
|---|---|---|---|---|
| SRC-BM-001-3-SPEC | `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001-3_requirementspec.json` | `meta.object_id = SPEC-001-3` | — | pack identity |
| SRC-BM-001-3-META | same | `meta.notes[0]` | "BM-001 with one requirement added: the enclosure rests on a curved back and opens through a flat top. Everything else is identical, so any difference traces to that and nothing else." | inheritance claim; NEG-001 |
| SRC-BM-001-3-REQ-011 | same | `requirements[REQ-011]`, kind `environmental` | "The enclosure rests on a curved back and opens upward through a flat top face." · verification: inspection, observable "curved underside, flat opening on top" | NRM-BM-001-3-001, 002, 003; UNR-BM-001-3-001, 002 |

## Terminology note

The task brief calls this a *cylindrical* case. The spec says **"curved back"**
and **"curved underside"** — it never says cylinder. The pack therefore requires
*non-zero curvature on the resting boundary* and lists half-cylinder,
cylindrical segment, elliptical arc, spherical cap and lofted freeform as equally
admissible (`FRE-BM-001-3-001`).

## Rank 5 — historical only

`/home/ftk3187/github/ASSY_Ver2.0/out/BM-001-3/run-*` — 7 recorded runs.

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-4.1 | `UNR-BM-001-3-002` (stability) no longer blocks `NRM-BM-001-3-002`. Contact between a curved underside and a plane is computable from geometry; the missing criterion blocks a stability PASS, a tipping-margin claim and any adequacy claim. |
| SF-4.2 | `ADM-BM-001-3-B` revised. A single spherical cap on a plane gives ONE ideal point contact, not the three patches the fixture claimed; three raised lobes with coplanar apexes now make three contacts physically possible. Coplanarity is an explicit assumption pending CAD. |
| SF-4.3 | `ADM-BM-001-3-C` revised. Resting on a flat LAND puts the load-bearing contact off the curved back. The land became a non-load-bearing relieved recess, with the resting contact on the two curved bands flanking it. The design the old fixture described is now `INA-BM-001-3-D`. |

A source reading is now recorded explicitly as `RDG-BM-001-3-01`: "rests on a
curved back" is read as requiring the LOAD-BEARING resting contact to lie on the
curved region. The alternative reading is stated and rejected as vacuous.
