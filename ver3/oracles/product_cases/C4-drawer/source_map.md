# C4-drawer — source map

The rank-1 source is one sentence, quoted verbatim from
`/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/manifest.json`, record `id = "C4-drawer"`:

> **"Design a desktop cabinet whose drawer slides out horizontally when you turn a knob."**

Frozen dossier: `ver3/oracles/_dossiers/DOS-C4-drawer.md`.

Rank 1 = the command. Rank 4 = reference-realization detail. Rank 5 = benchmark
scoring commentary. Rank 6 = legacy implementation behaviour. Ranks 4–6 never
define correctness.

## Command fragments and what each supports

| Fragment | Statements grounded in it |
|---|---|
| "turn a knob" | NRM-C4-001 (direct), NRM-C4-004, NRM-C4-008, NRM-C4-009 (derived) |
| "slides out" | NRM-C4-003 (direct), NRM-C4-007, NRM-C4-010 (derived) |
| "horizontally" | NRM-C4-002 (direct) |
| "drawer slides" | NRM-C4-005, NRM-C4-006 (derived) |
| "Design a desktop cabinet" | NRM-C4-011 (derived); "desktop" carried unresolved as UNR-C4-006 |

## Normative invariants

| Statement | basis_type | Rank |
|---|---|---|
| NRM-C4-001 | DIRECT_USER_REQUIREMENT | 1 |
| NRM-C4-002 | DIRECT_USER_REQUIREMENT | 1 |
| NRM-C4-003 | DIRECT_USER_REQUIREMENT | 1 |
| NRM-C4-004 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-005 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-006 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-007 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-008 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-009 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-010 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-011 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |

No invariant is grounded in a legacy realization, a benchmark field, or a
scoring note.

## Fields of the benchmark record that are NOT sources of requirements

| Field | Rank | Disposition |
|---|---|---|
| `base = "crank-lift"` | 6 | Pipeline plumbing. Establishes nothing about the product. |
| `axis = "constraint"` | 5 | Benchmark taxonomy. |
| `expected_class = "PASS"` | 5 | A prior expectation of the legacy run's outcome. Ver3 outcomes are conditional (s11 `outcome_rules`); a fixed expected outcome would freeze tooling capability. |
| `physics_implied = "m13 drawer V-A 5/5"` | 6 | Recorded in `evidence_scope.yaml` with its fidelity and its reuse limitation, never as a requirement. |
| `scoring_note` ("gear NOT over-engineered here") | 5 | One side of AMB-C4-01. Recorded in UNR-C4-002; cannot bind FRE-C4-002. |
| `certification_matrix` `verdict = "CERTIFIED"`, `"5 bodies"`, `"reused - PASS"` | 6 | Legacy run outcome. `"5 bodies"` is a realization outcome and may never be an acceptance criterion (NEG-C4-012). |

## Freedoms

All ten freedoms are grounded in DOS S3 — criteria the command does not state —
except FRE-C4-002, which is additionally grounded in DOS S4 (AMB-C4-01), and
FRE-C4-003 / FRE-C4-005 / FRE-C4-009, which additionally name the DOS S6
realization values they refuse to inherit.

## Ambiguity carried, not resolved

**AMB-C4-01** (DOS S4). `build_goldens.py:1142` calls the drawer's rack-pinion
"over-engineered"; the manifest `scoring_note` calls it "NOT over-engineered
here". Both statements are commentary about a realization, and neither is the
command. Recorded as UNR-C4-002 and `NRM-C4-004.acknowledges_ambiguity`; enforced
by NEG-C4-014. What is settled here is only the *rank* of the two statements —
which the precedence model already fixes — not the disagreement between them.
The disagreement stands.

## Cases deliberately kept separate

Per DOS S8, `latched_drawer.json` and `rack_pinion_fixture.json` are not merged
into this case. The former states retention and hand release and no rotary input;
the latter states no cabinet, drawer or guidance obligation. Importing either
would silently decide UNR-C4-003 or UNR-C4-007. Enforced by NEG-C4-015.

## Explicitly excluded from normative status

| Legacy item | Rank | Why excluded |
|---|---|---|
| 5 bodies; cabinet 200×140×90; wall 4 mm; rail_gap 80; m=5, z=12; stroke 120; drawer_w 115.30; L_rack ≥ 167.12 (DOS S6) | 4 | REFERENCE_REALIZATION_DETAIL. None appears in the command. |
| Frame convention +X = FRONT (DOS S6) | 4 | A label of one realization. NEG-C4-013 forbids it as authority for horizontality. |
| `tracks_straight = 0.0` (DOS S5 E2) | 6 | Structural artifact of the declared coupling. EV-C4-002. |
| `stages.physics = "reused - PASS"` (DOS S5 E1) | 6 | Evidence carried from another case. EV-C4-001 reuse_note. |
| `KG_NO_PERMITTED_REALIZER` verdict pattern (DOS S7) | 6 | Library gap reported as physics. NEG-C4-016. |
