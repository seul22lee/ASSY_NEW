# Dossier C4-drawer — FROZEN

## S1. Direct source requirement (rank 1)
Locator: `/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/manifest.json`, record `id = "C4-drawer"`.

`command` verbatim: **"Design a desktop cabinet whose drawer slides out
horizontally when you turn a knob."**

Other fields of that record: `base = "crank-lift"`, `axis = "constraint"`,
`expected_class = "PASS"`, `physics_implied = "m13 drawer V-A 5/5
(t2_hard_verdict)"`, `scoring_note = "constraint: HORIZONTAL travel (no
gravity-hold) - the drawer alternate, gear NOT over-engineered here."`

`/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/manifest_draft.md:32` restates the command and gives
axis "constraint (horizontal, no gravity-hold)", expected "PASS (drawer
alternate, V-A)".

`/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/certification_matrix.json` record: `stages.validators =
"clean"`, `stages."(5) resolve" = "ok"`, `stages."(6) compile" = "5 bodies"`,
`stages.physics = "reused - PASS"`, `physics_evidence = "m13 drawer V-A 5/5
(t2_hard_verdict)"`, `verdict = "CERTIFIED"`.

## S2. What the command states, decomposed (no interpretation added)
- artifact: a desktop **cabinet**
- moving part: a **drawer**
- motion: **slides out**, **horizontally**
- user input: **turn a knob** (rotary)
- therefore: rotary input, linear output

## S3. Missing criteria and quantities
- No stroke, no travel distance.
- No payload, drawer load, or drawer contents.
- No knob torque or turns-to-full-travel.
- No cabinet dimensions.
- No guidance method, no anti-rotation statement.
- No travel limit at either extreme.
- No retention, latching or hold-closed requirement.
- No material or process.
- No transmission ratio.
- No statement about back-drive.

## S4. Source conflicts / ambiguities — **AMB-C4-01, recorded not resolved**
Two rank-1/rank-5 legacy statements conflict about whether a gear transmission is
appropriate for the drawer variant:
- `/home/ftk3187/github/ASSY_Ver1.0/tasks/build_goldens.py:1142` docstring: "a **drawer's rack-pinion is
  over-engineered**; a good model would omit it - but a vertical lift needs it".
- `/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/manifest.json` C4-drawer `scoring_note`: "the drawer
  alternate, **gear NOT over-engineered here**".

Note the command itself specifies "**when you turn a knob**", which makes a
rotary-to-linear conversion a *stated user input*, not an elective addition.
This observation is recorded; the conflict between the two legacy statements is
**not** resolved here.

## S5. Evidence available, with fidelity
| Evidence | Path | Fidelity | What it is |
|---|---|---|---|
| Drawer slide + gear | `/home/ftk3187/github/ASSY_Ver1.0/m13_hard_anchor/out/t2_hard_verdict.json` | **V-A declared pairs** | `decision_row` = "m13 Hard anchor - P-SLIDE V-A + P-GEAR V-A (declared pairs)"; P-SLIDE-VA 5/5 |
| P-SLIDE-VA seed 0 criteria | same | V-A | `reaches_stroke` 127.3 mm vs threshold 120.0 -> pass; `tracks_straight (<=3 deg)` **0.0** vs 3.0 -> pass; `converged` false vs false -> pass |
| Rack-pinion card | `/home/ftk3187/github/ASSY_Ver1.0/m11_rack_pinion/REVIEW.md` | V-A 5/5; **V-B NAMED-DEFERRED** | mesh not contact-verified |

### E1. Limitation — physics is REUSED, not executed for C4-drawer
`certification_matrix.json` gives `stages.physics = "reused - PASS"` and
`benchmark.py:143` gives `physics=dict(tier="reused", ...)`. No simulation was run
for C4-drawer itself; the m13 lift-variant result was carried across.

### E2. Limitation — structural artifact
`tracks_straight` is **0.0 degrees exactly**. Under a V-A declared-pair model the
slide is a prismatic joint, so off-axis deviation is identically zero **by
construction of the coupling**. This value is not evidence that guidance was
demonstrated.

### E3. Limitation
The gear mesh is V-A only; engagement, backlash and tooth contact are unverified.

## S6. Decisions made only by legacy reference realizations
`/home/ftk3187/github/ASSY_Ver1.0/tasks/build_goldens.py:1142 anchor_hard("drawer")` -> 5 bodies: P1
`cabinet_shell` (200x140x90, wall 4), P2/P3 `slide_carriage`, P4 `drawer_tray`
(tray_w 115.30 derived), P5 `knob_shaft`; elements 2x `slide_rail` + 1x
`rack_pinion`; frame convention +X = FRONT; rail_gap 80; m=5, z=12; stroke 120;
derived `drawer_w = 132 - 2*8.35 = 115.30`, `L_rack >= 120 + 47.12 = 167.12`.
**None of this appears in the C4-drawer command.**

## S7. Legacy behaviour that must not define correctness
As DOS-BM-001 S7, plus the `KG_NO_PERMITTED_REALIZER` verdict pattern.

## S8. Cases that must NOT be merged into this one
- `/home/ftk3187/github/ASSY_Ver1.0/tasks/latched_drawer.json` — "A drawer that slides in, clicks shut, and
  pulls open **by hand**." Functions: guide drawer; retain drawer (click shut,
  hand-releasable). **No rotary input, no rack, no pinion.**
- `/home/ftk3187/github/ASSY_Ver1.0/tasks/rack_pinion_fixture.json` — "A **knob** that drives a **rack**
  straight out and back." Functions: convert motion (rotation to translation);
  drive rack. **No cabinet, no drawer, no enclosure, no guidance obligation.**
