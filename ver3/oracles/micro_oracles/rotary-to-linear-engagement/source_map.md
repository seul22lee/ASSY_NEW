# rotary-to-linear-engagement — source map (micro-oracle)

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
| NRM-RL-001 | DIRECT_USER_REQUIREMENT | S1, "through a localized engagement" |
| NRM-RL-002 | DIRECT_USER_REQUIREMENT | S1, "conversion of rotary input into linear output" |
| NRM-RL-003 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (conversion over a range) |
| NRM-RL-004 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (an offset engagement force applies a moment) |
| NRM-RL-005 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived |
| NRM-RL-006 | NECESSARY_PHYSICAL_CONSEQUENCE | S1, "with the reaction of the resulting loads" → derived |
| NRM-RL-007 | VERIFICATION_MINIMUM | S5 (V-B named-deferred; ratio exact by construction) |

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
that answer a defect, and `stage_expectations.s02.plurality_note` and
`s12.capability_gap_rule` place the obligation on specific stages.
