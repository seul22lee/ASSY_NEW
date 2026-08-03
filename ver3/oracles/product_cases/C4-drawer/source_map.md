# C4-drawer — source map

> **Pack status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; not lock-ready, not
> CAD-validated. Every admissible fixture is `NEEDS_GEOMETRY_VALIDATION`.


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
| "horizontally" | NRM-C4-002 (direct, read as a straight horizontal axis per AMD-C4-002 / HSD-004) |
| "drawer slides" | NRM-C4-005, NRM-C4-006 (derived) |
| "Design a desktop cabinet" | NRM-C4-011 (derived); "desktop" carried unresolved as UNR-C4-006 |

## Normative invariants

| Statement | basis_type | Rank |
|---|---|---|
| NRM-C4-001 | DIRECT_USER_REQUIREMENT | 1 |
| NRM-C4-002 | DIRECT_USER_REQUIREMENT | 1 + AMD-C4-002 (reading, HSD-004) |
| NRM-C4-003 | DIRECT_USER_REQUIREMENT | 1 |
| NRM-C4-004 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-005 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-006 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-007 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-008 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-009 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-010 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-011 | NECESSARY_PHYSICAL_CONSEQUENCE | 1 → derived |
| NRM-C4-012 | VERIFICATION_MINIMUM | DOS S5 E2 |
| NRM-C4-013 | VERIFICATION_MINIMUM | DOS S5 E1 |

No invariant is grounded in a legacy realization, a benchmark field, or a
scoring note.

## Fields of the benchmark record that are NOT sources of requirements

| Field | Rank | Disposition |
|---|---|---|
| `base = "crank-lift"` | 6 | Pipeline plumbing. Establishes nothing about the product. |
| `axis = "constraint"` | 5 | Benchmark taxonomy. |
| `expected_class = "PASS"` | 5 | A prior expectation of the legacy run's outcome. Ver3 outcomes are conditional (s11 `outcome_rules`); a fixed expected outcome would freeze tooling capability. |
| `physics_implied = "m13 drawer V-A 5/5"` | 6 | Recorded in `evidence_scope.yaml` with its fidelity and its reuse limitation, never as a requirement. |
| `scoring_note` ("gear NOT over-engineered here") | 5 | One side of LEGACY-CONFLICT-C4-01. Cannot bind FRE-C4-002. |
| `certification_matrix` `verdict = "CERTIFIED"`, `"5 bodies"`, `"reused - PASS"` | 6 | Legacy run outcome. `"5 bodies"` is a realization outcome and may never be an acceptance criterion (NEG-C4-012). |

## Freedoms

All twelve freedoms are grounded in DOS S3 — criteria the command does not state —
except FRE-C4-002, which is additionally supported by LEGACY-CONFLICT-C4-01, and
FRE-C4-003 / FRE-C4-005 / FRE-C4-009, which additionally name the DOS S6
realization values they refuse to inherit.

## Legacy conflict recorded — NOT a source ambiguity

**`LEGACY-CONFLICT-C4-01`** (formerly AMB-C4-01, DOS S4, reclassified by
`AMD-C4-001` under **HSD-002**). `build_goldens.py:1142` calls the drawer's
rack-pinion "over-engineered"; the manifest `scoring_note` calls it "NOT
over-engineered here". Both are commentary about a realization; neither is the
rank-1 command.

Because neither could bind the conversion family, their disagreement creates **no
ambiguity in the acceptance model**. It `blocks_nothing`, `requires_human_decision:
false`, and is cited as support for `FRE-C4-002`. The disagreement itself stands
and is preserved verbatim in DOS S4 and in the amendment record; what is withdrawn
is the implication that a human must rule on whether a toothed transmission is
required. Enforced by NEG-C4-014.

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

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-6.1 | `NRM-C4-005` requires guidance sufficient for the required horizontal sliding behaviour. The universal moment premise is withdrawn. `ADM-C4-D` — a centred crank-and-link driving a tray whose angular position is immaterial — has no dedicated anti-rotation and is admissible. |
| SF-6.2 | `NRM-C4-006` ranges over the DRAWER'S OWN WEIGHT plus any contents load an instantiating requirement declares. "Any contents load" made the requirement unbounded and unfalsifiable. |
| SF-6.3 | `NRM-C4-007` applies only where a configuration is DECLARED a physical end of travel. DOS-C4-drawer S3 records explicitly that no travel limit is stated. New freedom `FRE-C4-011`; `ADM-C4-C` declares no end of travel. |
| SF-6.4 | `NRM-C4-008` no longer requires cabinet-local support at the crossing; it requires non-interference. New freedom `FRE-C4-012`. |
| SF-6.5 | `NRM-C4-009` is load-conditional. The premise that rotary-to-linear conversion generally creates axial force on the rotating element is withdrawn — false for toothed and for band drives. |
| SF-6.6 | **AMB-C4-01 is reclassified**, not resolved. See below. |
| SF-1.1 | `NRM-C4-012` (guidance observable must be able to fail) and `NRM-C4-013` (reused evidence must name its originating case) are now invariants with `enables_claim`, not prose in `evidence_scope.yaml`. |

### AMB-C4-01 → LEGACY-CONFLICT-C4-01

The "gear over-engineered / not over-engineered" disagreement is between a
rank-4 docstring and a rank-5 scoring note. Neither is the rank-1 command, which
requires rotary-to-linear operation and says nothing about a gear. Two lower-rank
commentaries disagreeing about a realization the source never required creates no
ambiguity in the acceptance model.

It is recorded as `legacy_conflicts.LEGACY-CONFLICT-C4-01` with
`blocks_nothing: true` and `requires_human_decision: false`, and is cited as
support for `FRE-C4-002`: two competent readers of the same corpus disagreed
about a realization, which is evidence that mechanism choice must stay free. The
former `UNR-C4-002` is listed under `retired_unresolved` with the reason.

## Dossier amendments

| Amendment | Supersedes | Scope | Decision |
|---|---|---|---|
| `AMD-C4-001` | `DOS-C4-drawer.md#S4` | the CLASSIFICATION of S4 only; the two quoted legacy statements are unchanged and still citable | HSD-002 |
| `AMD-C4-002` | `DOS-C4-drawer.md#S2` | the reading of the motion fragment only | HSD-004 |

`AMD-C4-002` records the reading adopted for `NRM-C4-002`: **"slides out
horizontally" means straight translation along one horizontal axis perpendicular
to gravity.** The curved-but-generally-horizontal reading is recorded as
REJECTED FOR THIS BASELINE, not left as an open alternative — the statement and
its predicate now agree, which they did not before (`NEG-C4-023`).

This is a human-approved product reading, not a verbatim geometric definition in
the one-sentence source.
