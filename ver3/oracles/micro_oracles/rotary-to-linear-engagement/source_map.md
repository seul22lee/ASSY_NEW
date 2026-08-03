# rotary-to-linear-engagement — source map (micro-oracle)

> **Pack status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; not lock-ready, not
> CAD-validated. Every admissible fixture is `NEEDS_GEOMETRY_VALIDATION`.


**Capability (rank 1 for this pack):** conversion of rotary input motion into
linear output motion through a localized engagement, with the reaction of the
resulting loads. Source: `ver3/oracles/_dossiers/DOS-rotary-to-linear-engagement.md` S1.

A micro-oracle has no user request. Its rank-1 source is the declared capability
statement; product cases and legacy fixtures rank below it and never define it.

## The name

This capability was renamed from a mechanism-named predecessor. The name states
what is achieved, not how. Rack-and-pinion survives only as a cited reference
realization and evidence source. `normative.naming_note` and `NEG-RL-011` keep it
that way.

## Statements

| Statement | basis_type | Grounded in |
|---|---|---|
| NRM-RL-001 | PROJECT_DEFINED_CAPABILITY | AMD-RL-001 (supersedes S1) — "an uninterrupted chain of realized localized interactions" — HSD-002 |
| NRM-RL-002 | PROJECT_DEFINED_CAPABILITY | AMD-RL-001 (supersedes S1) — physical causation, not declaration — HSD-002 |
| NRM-RL-003 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (conversion over a range) |
| NRM-RL-004 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (an offset engagement force applies a moment) |
| NRM-RL-005 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived |
| NRM-RL-005 | NECESSARY_PHYSICAL_CONSEQUENCE | AMD-RL-001 — reaction of load components ACTUALLY carried — HSD-002 |
| NRM-RL-006 | VERIFICATION_MINIMUM | S5 (V-B named-deferred; ratio exact by construction) |

## Boundaries with neighbouring capabilities

| Question | Owner | Why not here |
|---|---|---|
| What guides the output body along its line? | guided-slider | NRM-RL-004 requires only the restraint without which conversion would not occur. Letting the conversion discharge a guidance obligation would double-count one realization (NEG-RL-012). |
| Where does the output travel stop? | bounded-two-state-closure | Bounding is not conversion. |
| What holds the output in place? | latch-retention | Holding is not conversion. |

## Legacy material and its rank

| Item | Rank | Disposition |
|---|---|---|
| Involute pinion, straight rack flanks at the pressure angle, m=5, z=12 (S6) | 4 | FRE-RL-002, NEG-RL-009. |
| `L_rack >= stroke + pi*m*z/4` (S6) | 4 | A rack-and-pinion relation. FRE-RL-005. |
| `axis_off = rack_pitchline + d/2` (S6) | 4 | FRE-RL-007. |
| "P-GEAR passes V-A 5/5" (S3, S5) | 6 | EV-RL-001, with its fidelity and its own deferral statement. |
| "V-B is NAMED-DEFERRED, not silently dropped" (S5) | 6 | The corpus-level finding in `evidence_scope.yaml`. |
| `KG_NO_PERMITTED_REALIZER` INFEASIBLE while `lead_screw.py` existed (S7) | 6 | NEG-RL-008 and EV-RL-003. Process evidence, not design evidence. |

## The one thing this pack exists for

DOS S7 records a pipeline that held one conversion card, was asked for a
conversion without it, and answered INFEASIBLE — with a second conversion sitting
in the same repository. `FRE-RL-001` makes the family free, `NEG-RL-008` makes
that answer a defect, and `stage_expectations.s02.open_search_note` and
`s12.capability_gap_rule` place the obligation on specific stages.

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-1.3 | `PROJECT_DEFINED_CAPABILITY` replaces `DIRECT_USER_REQUIREMENT`. |
| SF-8.1 | **The capability statement was rewritten** to an uninterrupted chain of realized localized interactions. "through a localized engagement" was read as requiring DIRECT engagement between the rotating input body and the translating output body, which rejects every multi-stage conversion. `ADM-RL-E` (crank-link-slider) and `ADM-RL-F` (cam-follower-pushrod) falsify the retired reading. |
| SF-8.2 | `NRM-RL-002` concerns the actual kinematic relation — rotation causes translation over the declared range, possibly nonlinearly. The requirement that the relation be DECLARED and the driving body RECORDED moved to `stage_expectations.s04.representation_obligations`, where DesignState obligations belong. |
| SF-8.3 | The fixed-plurality rule is withdrawn. One candidate may legitimately remain after reasoned elimination; what must hold is open search, reasoned rejection, and UNSUPPORTED for an absent realizer. |
| SF-1.1 | `NRM-RL-006` uses `requires_evidence_tags`; fixtures in `evidence_cases.yaml`. |

## Capability authority after amendment AMD-RL-001

The frozen S1 wording "through a localized engagement" was read as requiring
DIRECT engagement between the rotating input body and the translating output body.
`AMD-RL-001`, approved by **HSD-002**, supersedes it for normative authority with
an uninterrupted-chain formulation. The original text is preserved verbatim in the
amendment; S2–S7 are unchanged.

`ADM-RL-E` (crank-link-slider) and `ADM-RL-F` (cam-follower-pushrod) have no
interaction at all between input body and output body. If either starts failing,
the retired reading has returned.
