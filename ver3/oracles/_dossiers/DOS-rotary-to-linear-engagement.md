# Dossier rotary-to-linear-engagement — FROZEN (micro-oracle)

**Tier:** micro_oracle. Constrains **one reusable mechanical capability**, never a
product and never a mechanism. Legacy fixtures below are cited as evidence and as
sources of negative cases; they are **not** acceptance targets.

## S1. Capability
Conversion of rotary input motion into linear output motion through a localized
engagement, with the reaction of the resulting loads.

## S2. Legacy fixtures (rank 4-5 evidence, not targets)
| Fixture | Path | What its source says |
|---|---|---|
| Rack-pinion fixture | `/home/ftk3187/github/ASSY_Ver1.0/tasks/rack_pinion_fixture.json` | command: "A knob that drives a rack straight out and back." functions: convert motion (rotation to translation); drive rack (linear travel from a knob). |
| Rack-pinion milestone | `/home/ftk3187/github/ASSY_Ver1.0/m7_rack_pinion/`, `/home/ftk3187/github/ASSY_Ver1.0/m11_rack_pinion/` | card built |
| Lead screw | `/home/ftk3187/github/ASSY_Ver1.0/m19_lead_screw/`, `/home/ftk3187/github/ASSY_Ver1.0/knowledge/cards/lead_screw.py` | a **different** conversion exists in the legacy library |
| Angled screw lift | `/home/ftk3187/github/ASSY_Ver1.0/m27_angled_screw_lift/` | a third conversion topology |

## S3. Explicit observables
- `P-GEAR` V-A pass/fail, 5 seeds. Source `/home/ftk3187/github/ASSY_Ver1.0/m11_rack_pinion/REVIEW.md`.
- m13 combined: `/home/ftk3187/github/ASSY_Ver1.0/m13_hard_anchor/out/t2_hard_verdict.json`, `decision_row` =
  "P-SLIDE V-A + P-GEAR V-A (declared pairs)".

## S4. Missing criteria
No capability-level ratio, torque, efficiency, backlash, engagement-length or
load rating is defined by any source.

## S5. Evidence fidelity and limitations — **decisive for this dossier**
`/home/ftk3187/github/ASSY_Ver1.0/m11_rack_pinion/REVIEW.md` states verbatim: "the card is built and P-GEAR
passes **V-A 5/5**" and "**V-B is NAMED-DEFERRED**, not silently dropped".

Therefore: **no contact-level evidence exists for any rotary-to-linear conversion
in the legacy corpus.** Ratio is exact by construction under declared pairs.
Engagement, backlash, tooth/thread contact, friction, efficiency and jamming are
all unobserved.

## S6. Decisions made only by legacy realizations
Involute pinion reusing `m1_gear/gear_geom.build_gear`; straight rack flanks at
the pressure angle; m=5, z=12; `L_rack >= stroke + pi*m*z/4`; mesh offset
`axis_off = rack_pitchline + d/2`. These are **rack-and-pinion facts**, not
capability facts.

## S7. Legacy behaviour that must not define correctness
`/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/benchmark.py:145-150` treated rack_pinion as "the ONLY
rot_to_trans realizer" and returned INFEASIBLE when it was forbidden — while
`lead_screw.py` existed in the same repository. The capability has many
realizations; the library had one wired in.
