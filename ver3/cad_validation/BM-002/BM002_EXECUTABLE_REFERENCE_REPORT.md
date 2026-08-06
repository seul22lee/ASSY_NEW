# BM-002 — executable reference report

**Case:** BM-002, enclosed hand-cranked platform lift.
**Reference:** `EXE-BM002-01`.
**Status: HUMAN_REVIEW_PENDING. Not production authority. Not locked.**

| | |
|---|---|
| geometry signature | `6824e5102424e3db883f16b684ab54f02c14eed19bead0116c704092156bc2ee` |
| product bodies | 7 |
| scenario objects | 1 (`SCENARIO-PAYLOAD-1KG`, not a product body) |
| measured travel | **90.000000 mm** |
| maximum claim | **GEOMETRICALLY AND KINEMATICALLY ADMISSIBLE AT THE EVALUATED CAD FIDELITY, WITH RIGID-BODY DYNAMICS AT THE DECLARED IDEAL-JOINT FIDELITY** |

This document is the single place a reader can see what BM-002 has, at what
fidelity, and what it still does not have. **The three phases are different kinds
of evidence and are never merged.**

---

## 1. The three phases, and what each one is

| phase | what it produced | what kind of evidence it is |
|---|---|---|
| **A — CAD** | seven B-rep bodies, 228-sample geometric motion validation, STEP/BREP round trip, deterministic rebuild, 14 Oracle predicates, 20 negative controls | **geometry and kinematics.** Exact solid measurement. No force anywhere. |
| **A-media — review** | 42 CAD-derived images, 13 sections, two **prescribed CAD animations** | **presentation of phase A.** The animations are prescribed pose laws, not physics. |
| **B — MuJoCo** | rigid-body dynamics, actuator torque, back-driving, ideal joint reactions, 7 plots, 3 **simulated** videos, 20 simulation controls | **rigid-body dynamics at an ideal-joint fidelity.** Forces, but no contact and no stress. |

**MuJoCo did not exist during Phase A and nothing in Phase A depends on it.** The
Phase A validator still runs and still passes unchanged; the geometry signature is
identical before and after Phase B.

The distinction that matters most:

* `validation/review/lift_cad_operation.mp4` is a **prescribed CAD kinematic
  animation**. Body positions come from a pose law.
* `validation/simulation/review/lift_mujoco_empty.mp4` is a **MuJoCo rigid-body
  simulation**. Body positions are read back from the solver.

Both are kept. Neither replaces the other, and neither is a contact simulation.

---

## 2. The design, in one page

An **in-line slider-crank platform lift**. A crank of radius `R` driving a slider
on a line through its own axis moves that slider by exactly `2R`, so `R = 45` gives
90 mm of travel — inside the source's *approximately 80–100 mm* band, 10 mm clear
of both edges.

| | |
|---|---|
| overall | 125 × 140 × 224 mm |
| crank axis | parallel to X at y = 70, z = 60 mm |
| internal crank radius | 45 mm |
| external hand-grip radius | 26 mm — a different feature on the same body; no gearing |
| connecting rod | 85 mm between bore centres |
| support surface | z = 126 (BOTTOM) → z = 216 (TOP) |
| shaft support | **two journal lands, both in the housing**, separated by a relief |
| crank | **overhung** — one arm, both journals on its −X side |
| rear panel | closes +X; carries the integral lands retaining both joint pins |
| guides | two channels integrated into the front and back inner walls |

Seven product bodies: HOUSING, REAR-PANEL, PLATFORM, CRANK-SHAFT, CONNECTING-ROD,
CRANK-JOINT-PIN, PLATFORM-JOINT-PIN.

Two Phase A findings shaped it, both recorded with their measurements in
`executable_references/EXE-BM002-01/DESIGN_AND_OPERATION_RATIONALE.md`:

* **CHG-01** the crank axis moved 55 → 60 mm, because at 55 the crank arm's pin
  boss sat 3 mm inside the housing floor (278.77 mm³ of measured interference);
* **CHG-02** the rear panel **cannot** carry the second shaft journal, because the
  connecting rod occupies the crank axis. Hence the overhung crank and two
  housing-side lands.

---

## 3. Phase A — CAD geometry and kinematics

| result | value |
|---|---|
| product bodies, all valid single solids | 7 |
| motion samples over 0–360° | 228 |
| maximum undeclared overlap | **0.000000e+00 mm³** |
| support surface, BOTTOM → TOP | 126.000000 → 216.000000 mm |
| platform pin, BOTTOM → TOP | 100.000000 → 190.000000 mm |
| measured travel, both measures | **90.000000 mm** |
| rod centre distance, all 9 states | 85.000000 mm, deviation 0.000000000 |
| joint clearances, all states | 0.100000 mm, zero common volume |
| guide clearances | 0.200 side, 0.400 tip, 0.400 plate edge |
| assembly, max common volume | 0.000000 mm³ |
| STEP/BREP re-import | PASS |
| deterministic rebuild | within tolerance **and** identical hash |
| Oracle predicates | **14 PASS, 0 FAIL** |
| negative controls | **20 / 20 detected** |

---

## 4. Phase B — MuJoCo rigid-body dynamics

**Engine:** MuJoCo 2.3.7, Python 3.8.10. Timestep 1/3000 s, integrator
`implicitfast`, Newton solver, 200 iterations, tolerance 1e-12. Gravity
`[0, 0, −9.81] m/s²`. Zero joint damping and zero friction in the primary model.

### Topology — the mechanism, not the answer

`crank` hinge about +X at the CAD crank axis → `rod` hinge about +X at the CAD
crank pin → **equality connect** at the CAD platform pin → `platform` slide along
+Z. Three joint DOF minus two in-plane constraint rows = **one net DOF**. Both
joint pins are welded into their CAD parents with their full mass and inertia
retained; each is a body of revolution about its joint axis, so the weld is exact.

There is **no crank-angle-to-platform-height equation in the model.** The
platform's height is whatever the solver produces.

### Mass, from the accepted CAD solids

Densities are **DECLARED SIMULATION ASSUMPTIONS — NOT SOURCE REQUIREMENTS, NOT
VERIFIED MATERIAL SELECTIONS**: polymer-like 1200 kg/m³ (housing, rear panel,
platform), metal-like 7850 kg/m³ (crank shaft, rod, both pins).

| body | mass (kg) |
|---|---|
| BODY-HOUSING | 0.53780 |
| BODY-REAR-PANEL | 0.33308 |
| BODY-PLATFORM | 0.06876 |
| BODY-CRANK-SHAFT | 1.59987 |
| BODY-CONNECTING-ROD | 0.16345 |
| BODY-CRANK-JOINT-PIN | 0.03440 |
| BODY-PLATFORM-JOINT-PIN | 0.02316 |
| **total product mass** | **2.76052** |
| moving mass | 1.88964 |

All masses positive; all inertia tensors positive-definite and satisfying the
triangle inequality.

### Cycle results, 30 s per revolution

| | empty | 1 kg payload |
|---|---|---|
| samples | 901 | 901 |
| measured travel | **90.0000 mm** | **90.0000 mm** |
| peak torque | **−0.15580 / +0.15580 N·m** | **−0.65691 / +0.65691 N·m** |
| at crank angle | 254.8° / 105.2° | 248.4° / 111.6° |
| RMS torque | 0.10649 N·m | 0.43031 N·m |
| max tracking error | 0.0300° | 0.0491° |
| loop-closure error | 0.000009 mm | 0.000014 mm |
| solver warnings | **0** | **0** |

### The robust result: incremental payload torque

| | |
|---|---|
| peak | **−0.50263 / +0.50263 N·m** |
| at crank angle | 246.8° / 113.2° |
| RMS | 0.32453 N·m |

The absolute torques scale with the declared densities. **The difference does
not** — the only thing that changed between the two runs is the 1.000 kg payload.

### Independent analytic cross-check

`τ = m g dz/dθ`, re-derived inside `simulate_lift.py` from R, L and the axis
height — it does **not** call `build.py`'s pose law, so the two sides of the
comparison are not the same function.

| | |
|---|---|
| max \|MuJoCo − analytic\| | **0.0000703 N·m** |
| RMS difference | 0.0000379 N·m |
| declared tolerance (2 % of analytic peak) | 0.010052 N·m |
| within tolerance | **yes**, by a factor of 143 |
| platform position vs analytic | max 0.000009 mm |

Near the dead centres `dz/dθ → 0`, and the incremental torque passes through zero
at 0° and 180° in both the simulation and the analytic expression.

### Speed sensitivity

| period | empty RMS | payload RMS |
|---|---|---|
| 30 s (slow, primary) | 0.10649 | 0.43031 |
| 12 s (nominal) | 0.10640 | 0.42995 |
| 6 s (fast) | 0.10627 | 0.42938 |

RMS torque changes by **0.2 %** across a 5× speed range, so the reported torque is
essentially quasi-static and the inertial contribution is small. A declared
0.01 N·m·s/rad damping variant adds +0.000108 N·m RMS.

### Back-driving, actuator released

Sixteen cases — eight release angles × two scenarios, 2.0 s of free integration
with zero damping and zero friction.

| release | empty: crank swing / platform drop | 1 kg: crank swing / platform drop |
|---|---|---|
| 0° | **no motion — kinematic dead centre** | **no motion — kinematic dead centre** |
| 45° | 89.97° / 7.001 mm | 89.95° / 7.006 mm |
| 90° | 179.94° / 32.112 mm | 179.86° / 32.142 mm |
| 135° | 270.00° / 70.656 mm | 269.37° / 70.555 mm |
| 180° | **no motion — kinematic dead centre** | **no motion — kinematic dead centre** |
| 225° | 270.00° / 70.656 mm | 269.37° / 70.555 mm |
| 270° | 179.94° / 32.112 mm | 179.86° / 32.142 mm |
| 315° | 89.97° / 7.001 mm | 89.95° / 7.006 mm |

Figures are the **maximum excursion** over the 2 s window, which is the honest
measure: the model is undamped, so the mechanism swings like a pendulum and a
snapshot at t = 2 s catches it at an arbitrary point of that swing. Both the
final and the maximum values are recorded per case in `backdrive_report.json`.

The platform drop is a clean physical check on the integration: in every case it
equals exactly the height from the release position down to the bottom of travel
(z = 126). At 135° the platform sits at 196.6 mm and falls 70.66 mm; at 90° it
sits at 158.1 mm and falls 32.11 mm; at 45° it sits at 133.0 mm and falls
7.00 mm. Energy is conserved, as an undamped model requires.

**12 of 16 cases back-drive.** The four that do not are the two dead centres,
where `dz/dθ = 0` so gravity exerts no crank torque — these are **kinematic
extrema, not physical hard stops**. No numerical divergence in any case.

**This mechanism does not hold position when released.** The source states **no**
holding, self-locking or back-drive requirement (UNR-BM-002-004, FRE-BM-002-008),
so this is a **behaviour, not a requirement failure**. Imposing a holding
requirement because a legacy realization used a pawl is NEG-BM-002-014.

### Ideal joint and constraint reactions

**Labelled IDEAL JOINT / CONSTRAINT REACTION. Never contact pressure, bearing
stress, pin stress or guide contact stress.**

| reaction | empty | 1 kg payload |
|---|---|---|
| crank bearing (shaft → housing) | 18.568 N | 29.245 N |
| crank joint (rod → crank) | 2.722 N | 14.260 N |
| platform joint (rod → platform) | 1.394 N | 12.900 N |
| ideal guide (platform → housing) | 1.063 N | 7.186 N |
| ideal guide moment | 0.1128 N·m | 0.8227 N·m |

These are **resultants of ideal constraints in a rigid-body model**. No area, no
pressure, no stress and no deflection is computed anywhere, so none of them can
support a strength, bearing or wear statement.

### Simulation negative controls

**20 / 20 detected.** Two of them found real defects in this session's own code
before they were fixed:

* **NC-S17** exposed that comparing MuJoCo warning counts before and after a run
  reports **zero** for a run that diverged, because `mj_checkPos` resets `MjData`
  and clears the counters. The runs now carry an in-run `Divergence` watch.
* **NC-S16** is the class of defect that MuJoCo itself caught at load time: the
  first inertia derivation applied a parallel-axis shift to a tensor OCCT already
  refers to the centre of mass, producing negative eigenvalues.

---

## 5. Requirement position — unchanged by MuJoCo where it must be

| requirement | position | why |
|---|---|---|
| REQ-001 crank raises and lowers the platform | **PASS at the evaluated fidelity** | complete cycle in CAD kinematics **and** in rigid-body dynamics |
| REQ-002 ≈80–100 mm travel | **PASS structurally**; numeric edge bounded | 90.000000 mm measured, mid-band (UNR-BM-002-002 carried) |
| REQ-003 ≈1 kg payload | **UNSUPPORTED — unchanged** | a constraint reaction is not a stress; this model computes none (UNR-BM-002-007) |
| REQ-004 mechanism enclosed | **INDETERMINATE — unchanged** | AMB-002-01 / UNR-BM-002-001 carried |
| REQ-005 safe to use | **INDETERMINATE — unchanged** | no criterion stated (UNR-BM-002-005) |
| REQ-006 assemble / manufacture | **PARTIAL**: installation paths exist; the rest NOT_VERIFIED | no process evidence exists |
| REQ-007 avoid obvious jamming | **NOT_VERIFIED — unchanged** | the guide is an **ideal prismatic constraint**; no contact is resolved (NRM-BM-002-014, NEG-BM-002-011) |
| REQ-008 desktop-sized | **INDETERMINATE — unchanged** | no envelope stated (UNR-BM-002-006) |
| REQ-009 manual only | **PASS** | no powered or stored-energy element anywhere |

**MuJoCo upgraded nothing.** It added torque, back-driving and reaction evidence
at a declared fidelity; it did not move REQ-003 or REQ-007, and it was never
capable of doing so.

---

## 6. What is still not established

payload structural capacity, stress, deflection, pin bending, shaft strength ·
bearing pressure or local guide pressure · fatigue, wear, life · manufacturing
feasibility and physical assembly force · user ergonomic suitability and
acceptable crank effort · pinch safety and any safety property · contact-level
jamming and tolerance-induced binding · self-locking outside the exact tested
model · whether the boundary-crossing hub counts as "enclosed" · the compliance
edge of "approximately".

**No FEA was run. No contact model exists. No demonstration CAD, failure corpus,
LOCK file or production code exists.**

---

## 7. Where the evidence is

```
BM-002/
  BM002_EXECUTABLE_REFERENCE_REPORT.md      this file
  reviews/
    INDEPENDENT_HUMAN_REVIEW_PACKET.md      the packet a reviewer reads
    HUMAN_REVIEW_STATUS.yaml                every decision PENDING
    REFERENCE_SELECTION.yaml                frozen before geometry existed
  executable_references/EXE-BM002-01/
    build.py  validate.py                   phase A: geometry and its validator
    review_views.py  make_videos.py         phase A media
    simulate_lift.py                        phase B: MuJoCo
    simulation/                             MuJoCo inputs: MJCF, masses, mapping
    screenshots/                            42 CAD-derived review images
    validation/                             phase A reports + prescribed CAD videos
    validation/simulation/                  phase B reports, 7 plots, 3 videos
```

**Human review status: HUMAN_REVIEW_PENDING.** The author has reviewed the media
and the evidence for internal consistency. Nobody has reviewed the design.
