# BM-002 — source map

> **Pack status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; not lock-ready, not
> CAD-validated. Every admissible fixture is `NEEDS_GEOMETRY_VALIDATION`.


Every normative statement, freedom and unresolved decision traced to its origin.
Rank 1 = explicit product intent / benchmark requirement. Rank 6 = legacy
implementation behaviour, which never defines correctness.

Frozen dossier: `ver3/oracles/_dossiers/DOS-BM-002.md`.

## Normative invariants

| Statement | basis_type | Source | Rank |
|---|---|---|---|
| NRM-BM-002-001 | DIRECT_USER_REQUIREMENT | DOS S1 REQ-001 | 1 |
| NRM-BM-002-002 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-001 + REQ-004 | 1 → derived |
| NRM-BM-002-003 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-001 | 1 → derived |
| NRM-BM-002-004 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-001, REQ-003, REQ-007 | 1 → derived |
| NRM-BM-002-005 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-001 + REQ-007 | 1 → derived |
| NRM-BM-002-006 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-002 | 1 → derived |
| NRM-BM-002-007 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-002 + REQ-007 | 1 → derived |
| NRM-BM-002-008 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-003 | 1 → derived |
| NRM-BM-002-009 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-003 | 1 → derived |
| NRM-BM-002-010 | NECESSARY_PHYSICAL_CONSEQUENCE | DOS S1 REQ-006 | 1 → derived |
| NRM-BM-002-011 | DIRECT_USER_REQUIREMENT | DOS S1 REQ-009 | 1 |

No invariant is grounded in a legacy realization. Rank-4/6 material appears only
in `evidence_scope.yaml` (bounded, with fidelity) and in `negative_cases.yaml`
(as behaviour to reject).

## Requirement coverage

| Requirement | Where it lands |
|---|---|
| REQ-001 | NRM-001, NRM-002, NRM-003, NRM-004, NRM-005 |
| REQ-002 | NRM-006, NRM-007; UNR-002 (AMB-002-02) |
| REQ-003 | NRM-004, NRM-008, NRM-009; not_verified (capacity) |
| REQ-004 | NRM-002; UNR-001 (AMB-002-01) |
| REQ-005 | UNR-005; not_verified |
| REQ-006 | NRM-010; not_verified (effort, manufacturability) |
| REQ-007 | NRM-004, NRM-005, NRM-007; UNR-005; not_verified (jamming) |
| REQ-008 | UNR-006; not_verified |
| REQ-009 | NRM-011 |

Every requirement is either carried by an invariant, carried as an unresolved
decision, or recorded as not verified with the reason. None is dropped.

## Freedoms

All nine freedoms are grounded in DOS S3 (criteria the source does not state) or,
for FRE-BM-002-002 and FRE-BM-002-008, in DOS S6/S7 — decisions made only by a
legacy realization, which are freedoms in Ver3 precisely because no requirement
makes them.

## Ambiguities carried, not resolved

- **AMB-002-01** (DOS S4) → UNR-BM-002-001, `NRM-BM-002-002.acknowledges_ambiguity`,
  `NEG-BM-002-013`, s11 `REQ-004.if_unresolved: INDETERMINATE`.
- **AMB-002-02** (DOS S4) → UNR-BM-002-002, `NEG-BM-002-012`,
  s11 `REQ-002.if_unresolved: INDETERMINATE`.

## Explicitly excluded from normative status

| Legacy item | Rank | Why excluded |
|---|---|---|
| Rack-pinion m=5, z=12; rail gap 80 mm; seat (76,60,30); cabinet 200×140×90; wall 4 mm (DOS S6) | 4 | REFERENCE_REALIZATION_DETAIL. Appears in no requirement. |
| Pawl hold, 5 mm hold-drift limit (DOS S5) | 4/6 | Realization choice + a legacy benchmark threshold. See UNR-BM-002-004. |
| `KG_NO_PERMITTED_REALIZER` INFEASIBLE verdict (DOS S7) | 6 | Library gap reported as physics. Recorded as NEG-BM-002-009. |
| "over-engineered" / "FUNCTIONALLY NECESSARY" docstring judgements (DOS S6) | 6 | Author commentary on a realization. |

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-5.1 | **The travel and payload requirements were missing entirely.** `NRM-BM-002-004` (approximately 80-100 mm, in mm, observed as vertical displacement) and `NRM-BM-002-005` (approximately 1 kg) restore them, with the source's "approximately" qualifier preserved and edge compliance INDETERMINATE at `UNR-BM-002-002`. A 45 mm design passed every invariant in the reviewed pack. |
| SF-5.2 | `NRM-BM-002-002` no longer requires housing-local support at the crossing. It requires the crossing to exist and not interfere; support is wherever the selected realization needs it. New freedom `FRE-BM-002-011`. |
| SF-5.3 | `NRM-BM-002-006` is load-conditional. A cable drum carries no axial load; a rotating nut reacts axially through its screw. The universal form encoded the screw family. |
| SF-5.4 | `NRM-BM-002-007` requires guidance sufficient for the REQUIRED behaviour. The premise that every rotary conversion applies a moment about the travel direction is **withdrawn** — false for a symmetric four-cable lift and for a centred linkage. Anti-rotation is required only where the scenario or the conversion needs it. |
| SF-5.5 | `NRM-BM-002-008` replaces proper-subset corridor containment with non-intersection at required poses plus traversability. |
| SF-5.6 | `NRM-BM-002-009` applies only where a terminal is DECLARED a physical end of travel. A displacement requirement is not a travel-limit requirement. New freedom `FRE-BM-002-010`. |
| SF-5.7 | The drum-stall terminal is gone. `ADM-BM-002-C` now uses a deliberate cable-length stop collar; a stall is an overload condition, not a travel determinant, and conflicted with REQ-007. |
| SF-5.8 | Five conversion families are now fixtures: direct screw, rotating nut on a fixed screw, cable and drum, scissor linkage, and a non-geared crank and link. Every derived invariant was re-tested against all five. |
| SF-1.1 | `NRM-BM-002-014` (declared-pair evidence may not support engagement or jamming claims) with `enables_claim`; fixtures in `evidence_cases.yaml`. |
