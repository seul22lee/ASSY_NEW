# BM-001 — rank-1 source, verbatim

Reproduced without alteration from the frozen dossier. Nothing has been added,
summarised or interpreted.

**Frozen dossier:** `ver3/oracles/_dossiers/DOS-BM-001.md`
**SHA-256:** `78bd0fe614033da1b90f29adf48397239b9a10426d6fa6f27e4a84b46b715bb1`

---

## S1. Direct source requirements (rank 1)
Locator: `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001_requirementspec.json`, key `requirements[<id>]`.
Product doc: `/home/ftk3187/github/ASSY_Ver2.0/BM-001_LATCHING_STORAGE_BOX.md`.
`product_intent`: "A compact desktop storage box with a reusable latch mechanism that enables repeated opening and closing operations while maintaining security during transport and normal handling."

| ID | kind | statement (verbatim) | verification.kind | observable (verbatim) |
|---|---|---|---|---|
| REQ-001 | functional | The product must provide a mechanism for repeatedly opening and closing the storage box. | demonstration | box opening and closing operations |
| REQ-002 | performance | The product must remain securely closed during normal handling and transport without accidental opening. | demonstration | box remaining closed under handling/transport |
| REQ-003 | usability | The product must have a latch that is easy for a user to operate. | demonstration | ease of operation by user |
| REQ-004 | safety | The product must maintain secure closure during transport. | demonstration | box remaining closed during transport |
| REQ-005 | manufacturing | The product must be suitable for low-cost manufacturing. | inspection | manufacturing cost |
| REQ-006 | usability | The product must be practical for desktop use. | demonstration | practical desktop use |
| REQ-007 | manufacturing | The product must be mechanically plausible and easy to assemble. | inspection | mechanical plausibility and ease of assembly |
| REQ-008 | performance | The product must have a reusable latch mechanism. | demonstration | reusable latch mechanism |

Clause: `clauses[C-006]` source=clarification — "Approximate product size: desktop-sized (roughly hand-held)."
