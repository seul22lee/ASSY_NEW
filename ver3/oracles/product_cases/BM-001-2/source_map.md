# BM-001-2 — source map

Inherits `BM-001/source_map.md` in full. Delta sources only.

Legacy roots: `V1 = /home/ftk3187/github/ASSY_Ver1.0`, `V2 = /home/ftk3187/github/ASSY_Ver2.0`.

## Rank 1 — delta requirements

| Source id | Path | Key | Verbatim | Used by |
|---|---|---|---|---|
| SRC-BM-001-2-SPEC | `V2/tests/fixtures/BM-001-2_requirementspec.json` | `meta.object_id = SPEC-001-2` | — | pack identity |
| SRC-BM-001-2-META | same | `meta.notes[0]` | "BM-001 with one requirement added: the enclosure mounts flush against a panel and presents no projecting corners outward. Everything else is identical, so any difference in the result traces to that requirement and nothing else." | inheritance claim; NEG-001 |
| SRC-BM-001-2-META2 | same | `meta.notes[1]` | "REQ-010 turns the catch round: the beam runs down the inside of the wall and the nose comes out through it." | context for REQ-010 |
| SRC-BM-001-2-REQ-009 | same | `requirements[REQ-009]`, kind `environmental` | "The enclosure must sit flush against a mounting panel on one side and present no projecting corners on the exposed side." · verification: inspection, observable "one face flat against the panel, the exposed side rounded" | NRM-BM-001-2-001; UNR-BM-001-2-001, UNR-BM-001-2-002 |
| SRC-BM-001-2-REQ-010 | same | `requirements[REQ-010]`, kind `safety` | "The latch must not be releasable from the exposed side; it can only be worked from inside the enclosure." · verification: inspection, observable "no part of the catch reachable from the exposed side" | NRM-BM-001-2-002; NEG-003 |

## Terminology note — recorded to prevent over-claiming

The task brief refers to this case as *cylindrical*. **The spec does not use that
word.** Its observable is "the exposed side **rounded**". The pack therefore
requires *absence of projecting corners on the exposed side* and lists
half-cylinder, filleted prism, dome and swept curved shell as equally admissible
(`FRE-BM-001-2-001`). Encoding "cylinder" as normative would be an
over-claim beyond rank 1 evidence.

`meta.notes[1]` describes the *catch* as round — a feature-level observation
about the Ver2 realization, not an enclosure requirement. It is recorded as
context and used by no normative statement.

## Rank 5 — historical only

`V2/out/BM-001-2/run-*` — 22 recorded runs. Pipeline outputs, not evidence.

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-3.1 | `NRM-BM-001-2-001` no longer asserts that the exposed boundary is OPPOSITE the seating region. REQ-009 never relates the two sides geometrically. New fixture `ADM-BM-001-2-D` — an L-shaped body whose exposed boundary wraps three adjoining faces — falsifies the retired wording. New unresolved `UNR-BM-001-2-004` (which portion of the exterior counts as exposed). |
| SF-1.4 | `UNR-BM-001-2-003` is the ONLY unresolved in the whole set that legitimately carries `blocks_structural_predicate`, with a justification: AMB-001-2-01 leaves the predicate's DOMAIN undefined, not merely a threshold missing. That is why this pack alone remains BLOCKED_BY_SOURCE_AMBIGUITY. |

AMB-001-2-01 is preserved. The three candidate readings are unresolved and the
exact wording "worked from inside the enclosure" is unchanged.
