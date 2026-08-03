# guided-slider — source map (micro-oracle)

**Capability (rank 1 for this pack):** guided translation of one body relative to
another along a defined line, with the non-translational freedoms removed.
Source: `ver3/oracles/_dossiers/DOS-guided-slider.md` S1.

A micro-oracle has no user request. Its rank-1 source is the declared capability
statement; product cases and legacy fixtures are ranked below it and never define
it. See `normative.yaml.basis_semantics`.

## Statements

| Statement | basis_type | Grounded in |
|---|---|---|
| NRM-GS-001 | DIRECT_USER_REQUIREMENT | S1, "one body relative to another along a defined line" |
| NRM-GS-002 | DIRECT_USER_REQUIREMENT | S1, "with the non-translational freedoms removed" |
| NRM-GS-003 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (constraints act through material) |
| NRM-GS-004 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (guidance along the line, not at a point on it) |
| NRM-GS-005 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (removing a freedom means carrying its load) |
| NRM-GS-006 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived |
| NRM-GS-007 | VERIFICATION_MINIMUM | S5 (structural artifact) |

## What is deliberately absent

The capability says nothing about bounding travel, retaining position, or driving
the motion. Three neighbouring capabilities own those:

| Question | Owner |
|---|---|
| Where does travel stop? | bounded-two-state-closure |
| What holds it there? | latch-retention |
| What drives it? | rotary-to-linear-engagement, among others |

UNR-GS-003 exists to keep bounding out. NEG-GS-009 and NEG-GS-010 enforce it.
This separation is the reason the pack has no travel-limit invariant, despite
every legacy fixture having one.

## Legacy material and its rank

| Item | Rank | Disposition |
|---|---|---|
| `latched_drawer.json` B1 `range_value 50.0 mm`, `bound min`, `axis_hint horizontal` | 4 | Fixture fields. UNR-GS-001, FRE-GS-002. |
| Two rails at a fixed gap; a carriage per rail (S6) | 4 | FRE-GS-003. |
| Rail width 8.0, height 8.0, clearance 0.35 (S6) | 4 | FRE-GS-006. |
| `slide_rail.carve` replaces its mover piece (S6) | 6 | CURRENT_TOOLING_LIMITATION. FRE-GS-007, NEG-GS-012. |
| Anti-rotation realized by using two rails (S7) | 6 | The mechanism, not the requirement. NEG-GS-008. |
| `tracks_straight = 0.0` (S5) | 6 | Structural artifact. EV-GS-002, NRM-GS-007. |
| `P-SLIDE-VA` 5/5 (S3) | 6 | EV-GS-001, with its fidelity. |

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-1.3 | Basis type for capability fragments is `PROJECT_DEFINED_CAPABILITY`, not `DIRECT_USER_REQUIREMENT`. A micro-oracle has no user; this capability statement was project-authored and then frozen. |
| SF-7.1 | **The capability statement was rewritten.** "with the non-translational freedoms removed" defines a strict prismatic joint, which is narrower than the ordinary sense of "guided slider" and than any project source. It now reads "with the freedoms constrained that the instantiating motion requirement depends on". `ADM-GS-E` — a rod in a plain round bore with declared free axial rotation — falsifies the retired reading. New freedom `FRE-GS-008`; new unresolved `UNR-GS-004`. |
| SF-7.2 | `NRM-GS-006` replaces proper-subset corridor containment with non-intersection and traversability. |
| SF-1.1 | `NRM-GS-007` now uses `requires_evidence_tags`; the structural-artifact property moved out of the physical fixture tags into `evidence_cases.yaml`. A physical guide is no longer inadmissible for want of a test. |

If a future project source genuinely requires strict single-degree-of-freedom
guidance, that is a DIFFERENT capability and belongs in a separate pack named
`single-dof-linear-guidance`. The retired statement is preserved in
`capability_statement_history`.
