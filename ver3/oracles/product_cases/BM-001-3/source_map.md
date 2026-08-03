# BM-001-3 — source map

Inherits `BM-001/source_map.md` in full. Delta sources only.

## Rank 1 — delta requirement

| Source id | Path | Key | Verbatim | Used by |
|---|---|---|---|---|
| SRC-BM-001-3-SPEC | `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001-3_requirementspec.json` | `meta.object_id = SPEC-001-3` | — | pack identity |
| SRC-BM-001-3-META | same | `meta.notes[0]` | "BM-001 with one requirement added: the enclosure rests on a curved back and opens through a flat top. Everything else is identical, so any difference traces to that and nothing else." | inheritance claim; NEG-001 |
| SRC-BM-001-3-REQ-011 | same | `requirements[REQ-011]`, kind `environmental` | "The enclosure rests on a curved back and opens upward through a flat top face." · verification: inspection, observable "curved underside, flat opening on top" | NRM-3-001, 002, 003; UNR-3-001, 002 |

## Terminology note

The task brief calls this a *cylindrical* case. The spec says **"curved back"**
and **"curved underside"** — it never says cylinder. The pack therefore requires
*non-zero curvature on the resting boundary* and lists half-cylinder,
cylindrical segment, elliptical arc, spherical cap and lofted freeform as equally
admissible (`FRE-BM-001-3-001`).

## Rank 5 — historical only

`/home/ftk3187/github/ASSY_Ver2.0/out/BM-001-3/run-*` — 7 recorded runs.
