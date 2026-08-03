# Dossier BM-001-2 — FROZEN

Parent dossier: `DOS-BM-001.md` (inherited unchanged).

## S1. Delta source requirements (rank 1)
Locator: `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001-2_requirementspec.json`. `meta.object_id = SPEC-001-2`.

`meta.notes[0]` verbatim: "BM-001 with one requirement added: the enclosure
mounts flush against a panel and presents no projecting corners outward.
Everything else is identical, so any difference in the result traces to that
requirement and nothing else."

`meta.notes[1]` verbatim: "REQ-010 turns the catch round: the beam runs down the
inside of the wall and the nose comes out through it."

| ID | kind | statement (verbatim) | verification.kind | observable (verbatim) |
|---|---|---|---|---|
| REQ-009 | environmental | The enclosure must sit flush against a mounting panel on one side and present no projecting corners on the exposed side. | inspection | one face flat against the panel, the exposed side rounded |
| REQ-010 | safety | The latch must not be releasable from the exposed side; it can only be worked from inside the enclosure. | inspection | no part of the catch reachable from the exposed side |

All 8 BM-001 requirements, `source_text`, `product_intent`,
`user_intent_summary` and clauses are byte-identical to BM-001.

## S2. Missing criteria and quantities
- No rounding radius, chamfer size or profile.
- No definition of "projecting".
- No mounting-panel load, fastening scheme or panel stiffness.
- No reach model defining "reachable".
- No statement of which face mounts.

## S3. Freedoms visible in the source
The **statement** requires *no projecting corners*; the **observable** offers
"the exposed side rounded" as one way to see it. The source constrains
non-projection, not a specific profile. The word *cylinder* does not occur.

## S4. Source conflicts / ambiguities — **AMB-001-2-01, recorded not resolved**
REQ-010 states the latch "**can only be worked from inside the enclosure**".
REQ-001 requires repeated opening and closing; REQ-003 requires the latch be
easy for a user to operate. Read literally, a latch workable only from inside a
closed enclosure cannot be operated to open that enclosure.

`meta.notes[1]` describes the Ver2 realization ("the beam runs down the inside
of the wall and the nose comes out through it") but this is a **feature-level
description of one solution**, rank 5, and does not resolve the requirement-level
tension.

Candidate readings, **none selected**:
(a) "inside" = the enclosure interior, reachable only when already open;
(b) "inside" = interior of the wall, actuated through a port on a non-exposed side;
(c) "inside" = the mounting side, accessible before mounting only.
No rank-1 source distinguishes them.

## S5. Evidence available
None for the delta. `/home/ftk3187/github/ASSY_Ver2.0/out/BM-001-2/run-*` = 22 runs, rank 5 pipeline output, not physical evidence.

## S6. Decisions made only by legacy reference realizations
The inside-the-wall beam-and-nose catch (`meta.notes[1]`) is one realization.

## S7. Legacy behaviour that must not define correctness
As DOS-BM-001 S7.
