# BM-002 — source map

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
