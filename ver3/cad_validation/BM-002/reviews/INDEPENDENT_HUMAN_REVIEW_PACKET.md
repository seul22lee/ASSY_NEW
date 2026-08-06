# BM-002 / EXE-BM002-01 — independent human CAD review packet

**Status: HUMAN_REVIEW_PENDING. Nothing in this packet is approved.**
The author has self-reviewed the media for legibility and correctness against the
CAD. No one has yet reviewed the *design*. Every reviewer decision below is
**PENDING**.

| | |
|---|---|
| reference | `ver3/cad_validation/BM-002/executable_references/EXE-BM002-01/` |
| case | BM-002 — enclosed hand-cranked platform lift |
| geometry signature | `6824e5102424e3db883f16b684ab54f02c14eed19bead0116c704092156bc2ee` |
| Phase A result | 14 invariants PASS, 0 FAIL; 20 / 20 negative controls detected |
| maximum claim | **GEOMETRICALLY AND KINEMATICALLY ADMISSIBLE AT THE EVALUATED CAD FIDELITY** |
| media provenance | every image and video frame rendered from the reference's own B-rep solids. No generative imagery, no proxy geometry, no remodelling. |

---

## 1. What the machine is, in one page

An **in-line slider-crank platform lift**. The user turns a crank outside the
housing; a crank arm inside drives a fixed-length connecting rod; the rod drives a
platform held to a vertical line by two guide channels. A crank of radius `R`
driving a slider on a line through its own axis moves that slider by exactly `2R`,
so `R = 45` gives **90 mm** of travel — inside the source's *approximately
80–100 mm* band and 10 mm clear of both edges.

| | |
|---|---|
| overall | 125 × 140 × 224 mm (x −46…79, y 0…140, z 0…224) |
| crank-shaft axis | parallel to X, at y = 70, z = 60 |
| internal crank radius | **45 mm** |
| external hand-grip radius | **26 mm** — a different feature on the same body; there is no gearing |
| connecting rod | 85 mm between bore centres |
| platform pin | z = 100 at BOTTOM, z = 190 at TOP |
| support surface | z = 126 at BOTTOM, z = 216 at TOP; **measured travel 90.000000 mm** |
| housing rim | z = 224, i.e. 8 mm above the platform at TOP |
| shaft support | **two journal lands, both in the housing**, at x 0–8 and x 14–26, separated by a relief. The first land is also the boundary crossing. |
| crank | **overhung** — one arm, both journals on its −X side |
| rear panel | closes the +X side; carries the integral lands that stop both joint pins escaping in +X |
| guides | two channels integrated into the front and back inner walls |

**Seven product bodies:** HOUSING, REAR-PANEL, PLATFORM, CRANK-SHAFT,
CONNECTING-ROD, CRANK-JOINT-PIN, PLATFORM-JOINT-PIN.
**SCENARIO-PAYLOAD-1KG is a scenario object, not a product body.**

Two Phase A findings shaped this design and are worth knowing before you look:

* the crank axis had to move from 55 to 60 mm, because at 55 the crank arm's pin
  boss sat 3 mm inside the housing floor (measured interference 278.77 mm³);
* the rear panel **cannot** carry the second shaft journal, because the connecting
  rod occupies the crank axis, so the shaft cannot reach the panel. Hence the
  overhung crank and two housing-side lands.

Both are recorded with their measurements in
[`DESIGN_AND_OPERATION_RATIONALE.md`](../executable_references/EXE-BM002-01/DESIGN_AND_OPERATION_RATIONALE.md)
as CHG-01 and CHG-02.

---

## 2. Where to look

### Overall and exterior
* [front-left isometric](../executable_references/EXE-BM002-01/screenshots/review_overall_front_iso.png) — start here
* [rear-right isometric](../executable_references/EXE-BM002-01/screenshots/review_overall_rear_iso.png)
* [left elevation, the crank face-on](../executable_references/EXE-BM002-01/screenshots/review_overall_left.png)
* [right elevation, the rear panel](../executable_references/EXE-BM002-01/screenshots/review_overall_right.png)
* [front elevation](../executable_references/EXE-BM002-01/screenshots/review_overall_front.png)
* [rear elevation](../executable_references/EXE-BM002-01/screenshots/review_overall_rear.png)
* [top view, platform at TOP](../executable_references/EXE-BM002-01/screenshots/review_overall_top.png)

### Body identification
* [all seven product bodies + the scenario payload](../executable_references/EXE-BM002-01/screenshots/review_body_identification.png)

### User input
* [external crank — 26 mm grip radius vs 45 mm crank radius, side by side](../executable_references/EXE-BM002-01/screenshots/review_external_crank_user_interface.png)

### Internal mechanism
* [rear panel removed, with an inset of what was removed](../executable_references/EXE-BM002-01/screenshots/review_internal_mechanism_rear_panel_removed.png)
* [cutaway isometric — handle and linkage in one view](../executable_references/EXE-BM002-01/screenshots/review_internal_mechanism_cutaway_iso.png)
* [kinematic chain, annotated with feature IDs](../executable_references/EXE-BM002-01/screenshots/review_kinematic_chain_annotated.png)

### Sections
* [overview with the section locations](../executable_references/EXE-BM002-01/screenshots/review_overview_operation_and_sections.png)
* **A-A** [shaft, boundary crossing and BOTH housing journal lands](../executable_references/EXE-BM002-01/screenshots/review_section_AA_shaft_and_dual_journals.png)
* **B-B** [crank/link/platform chain: BOTTOM](../executable_references/EXE-BM002-01/screenshots/review_section_BB_crank_link_platform_bottom.png) · [MID](../executable_references/EXE-BM002-01/screenshots/review_section_BB_crank_link_platform_mid.png) · [TOP](../executable_references/EXE-BM002-01/screenshots/review_section_BB_crank_link_platform_top.png)
* **C-C** [platform guides: BOTTOM](../executable_references/EXE-BM002-01/screenshots/review_section_CC_platform_guides_bottom.png) · [MID](../executable_references/EXE-BM002-01/screenshots/review_section_CC_platform_guides_mid.png) · [TOP](../executable_references/EXE-BM002-01/screenshots/review_section_CC_platform_guides_top.png)
* **D-D** [crank joint and axial retention](../executable_references/EXE-BM002-01/screenshots/review_section_DD_crank_joint_retention.png)
* **E-E** [platform joint and axial retention](../executable_references/EXE-BM002-01/screenshots/review_section_EE_platform_joint_retention.png)
* **F-F** [payload access: BOTTOM](../executable_references/EXE-BM002-01/screenshots/review_section_FF_payload_access_bottom.png) · [TOP](../executable_references/EXE-BM002-01/screenshots/review_section_FF_payload_access_top.png)

### Storyboards
* operation, nine frames: [01 BOTTOM](../executable_references/EXE-BM002-01/screenshots/review_operation_01_bottom.png) · [02 45°](../executable_references/EXE-BM002-01/screenshots/review_operation_02_rising_45.png) · [03 90°](../executable_references/EXE-BM002-01/screenshots/review_operation_03_rising_90.png) · [04 135°](../executable_references/EXE-BM002-01/screenshots/review_operation_04_rising_135.png) · [05 TOP](../executable_references/EXE-BM002-01/screenshots/review_operation_05_top.png) · [06 225°](../executable_references/EXE-BM002-01/screenshots/review_operation_06_lowering_225.png) · [07 270°](../executable_references/EXE-BM002-01/screenshots/review_operation_07_lowering_270.png) · [08 315°](../executable_references/EXE-BM002-01/screenshots/review_operation_08_lowering_315.png) · [09 BOTTOM RETURN](../executable_references/EXE-BM002-01/screenshots/review_operation_09_bottom_return.png)
* assembly, nine frames: [01](../executable_references/EXE-BM002-01/screenshots/review_assembly_01_empty_housing.png) · [02](../executable_references/EXE-BM002-01/screenshots/review_assembly_02_crank_shaft_inserted.png) · [03](../executable_references/EXE-BM002-01/screenshots/review_assembly_03_connecting_rod_and_crank_pin.png) · [04](../executable_references/EXE-BM002-01/screenshots/review_assembly_04_platform_entering_guides.png) · [05](../executable_references/EXE-BM002-01/screenshots/review_assembly_05_platform_joint_pin.png) · [06](../executable_references/EXE-BM002-01/screenshots/review_assembly_06_open_side_cycle_check.png) · [07](../executable_references/EXE-BM002-01/screenshots/review_assembly_07_rear_panel_approach.png) · [08](../executable_references/EXE-BM002-01/screenshots/review_assembly_08_rear_panel_installed.png) · [09](../executable_references/EXE-BM002-01/screenshots/review_assembly_09_completed_lift.png)

### Videos — CAD kinematic animations, not dynamics
* [operation, one full crank revolution (MP4, 10.0 s)](../executable_references/EXE-BM002-01/validation/review/lift_cad_operation.mp4) · [GIF](../executable_references/EXE-BM002-01/validation/review/lift_cad_operation.gif) · [manifest](../executable_references/EXE-BM002-01/validation/review/lift_cad_operation_video.json)
* [assembly, nine steps (MP4, 12.5 s)](../executable_references/EXE-BM002-01/validation/review/lift_cad_assembly.mp4) · [manifest](../executable_references/EXE-BM002-01/validation/review/lift_cad_assembly_video.json)

### Phase A validation evidence
* [SUMMARY.json](../executable_references/EXE-BM002-01/validation/SUMMARY.json)
* [motion_report.json](../executable_references/EXE-BM002-01/validation/motion_report.json) — 228 samples over 0–360°
* [assembly_report.json](../executable_references/EXE-BM002-01/validation/assembly_report.json)
* [interaction_report.json](../executable_references/EXE-BM002-01/validation/interaction_report.json) — 17 declared interactions
* [contact_resolution_report.json](../executable_references/EXE-BM002-01/validation/contact_resolution_report.json) — 18 interactions with fidelity and claim scope
* [predicate_report.json](../executable_references/EXE-BM002-01/validation/predicate_report.json) — the 14 Oracle invariants
* [payload_access_report.json](../executable_references/EXE-BM002-01/validation/payload_access_report.json)
* [geometry_signature.json](../executable_references/EXE-BM002-01/geometry_signature.json)
* [render_report.json](../executable_references/EXE-BM002-01/validation/render_report.json) · [PNG_REVIEW_AUDIT.md](../executable_references/EXE-BM002-01/validation/PNG_REVIEW_AUDIT.md) · [VIDEO_REVIEW_AUDIT.md](../executable_references/EXE-BM002-01/validation/VIDEO_REVIEW_AUDIT.md)
* [DESIGN_AND_OPERATION_RATIONALE.md](../executable_references/EXE-BM002-01/DESIGN_AND_OPERATION_RATIONALE.md)

---

## 3. Measured numbers a reviewer may rely on

All from the B-rep kernel in Phase A, not from an image.

| quantity | measured |
|---|---|
| support surface, BOTTOM → TOP | 126.000000 → 216.000000 mm |
| platform-pin, BOTTOM → TOP | 100.000000 → 190.000000 mm |
| travel, both measures | **90.000000 mm** |
| connecting-rod centre distance, all 9 states | 85.000000 mm, max deviation 0.000000000 |
| maximum rod angle | 31.9657° |
| journal land 1 / relief / land 2 clearance | 0.2000 / 3.2000 / 0.2000 mm |
| crank-pin and platform-pin bore clearance, all states | 0.100000 mm, zero common volume |
| crank pin axial free travel | −X 0.000 (blocked by the rod) · +X 2.000 (blocked by the rear panel) |
| platform pin axial free travel | −X 0.000 (blocked by the platform) · +X 2.000 (blocked by the rear panel) |
| guide clearances | 0.200 side, 0.400 tip, 0.400 plate edge |
| guide engagement | 2329.600 mm³ per side at every one of 37 cycle samples |
| orientation probes | 18 probes at BOTTOM / MID / TOP, all obstructed |
| undeclared overlap, 228 cycle samples × 21 body pairs | **0.000000e+00 mm³** |
| assembly, max common volume with placed material | 0.000000 mm³ |
| payload access | 0.000000 mm³ overlap during descent; seats at 0.000000 mm on the platform |

---

## 4. Reviewer questions — every decision PENDING

### Product and scale
| # | question | decision |
|---|---|---|
| P1 | Does this read as a coherent desktop lift? | **PENDING** |
| P2 | Are the overall proportions (125 × 140 × 224) acceptable? | **PENDING** |
| P3 | Is the open-top payload arrangement acceptable? | **PENDING** |

### User input
| # | question | decision |
|---|---|---|
| U1 | Is the external crank accessible? | **PENDING** |
| U2 | Is a 26 mm hand radius credible for this product? | **PENDING** |
| U3 | Is its sweep acceptable? The grip's lowest point is z = 34, i.e. 34 mm above the surface the housing stands on. | **PENDING** |
| U4 | Should the handle be larger, or shaped differently? | **PENDING** |

### Mechanism
| # | question | decision |
|---|---|---|
| M1 | Is the overhung crank shaft credible as a reference architecture? | **PENDING** |
| M2 | Are two housing-side journal lands understandable and mechanically plausible? | **PENDING** |
| M3 | Is the crank / link / platform chain clear? | **PENDING** |
| M4 | Does any body appear unnecessary? | **PENDING** |

### Guidance and payload
| # | question | decision |
|---|---|---|
| G1 | Do the front and back guide channels appear sufficient to maintain orientation? | **PENDING** |
| G2 | Is payload access adequate at BOTTOM (98 mm below the rim) and at TOP (8 mm)? | **PENDING** |
| G3 | Is the 8 mm top recess acceptable? | **PENDING** |

### Joints and assembly
| # | question | decision |
|---|---|---|
| J1 | Are both joint pins sufficiently retained *geometrically*? | **PENDING** |
| J2 | Are the rear-panel retention lands understandable? | **PENDING** |
| J3 | Is the assembly sequence credible? | **PENDING** |
| J4 | Does the rear panel perform enough necessary functions to justify being a body? | **PENDING** |

### Claims
| # | question | decision |
|---|---|---|
| C1 | Are strength, effort, jamming, safety and manufacture correctly left unverified? | **PENDING** |
| C2 | Is further engineering analysis required before treating this as a practical 1 kg product? | **PENDING** |

---

## 5. Author self-review — concerns a reviewer should weigh

Raised by the author while making this media. **None of these is a defect in the
CAD**; each is a design question only a human can settle.

1. **The Ø70 hub is unusual and it is load-bearing in three ways at once** — it is
   the exterior crank body, the boundary-crossing element, and the journal surface
   for both lands. It is that large because the shaft must be inserted from the
   open +X side, so the handle end has to pass through the whole journal bore; a
   small shaft with a large offset crank could not be assembled. A reviewer should
   decide whether a Ø70 plain journal is acceptable, or whether the product should
   be split differently. *See A-A and the crank user-interface image.*
2. **26 mm is a small hand-crank radius.** It is bounded above by the hub radius
   (35 mm) for the same assembly reason. Growing it means growing the hub and the
   bore.
3. **The grip reaches z = 34 at its lowest**, 34 mm above the desk. Whether
   knuckles clear the surface is a human judgement; nothing here measures it.
4. **The 8 mm recess at TOP** is what the frozen concept asked for, and it is
   tight for placing a payload by hand. G2 and G3 exist for this.
5. **The overhung crank is a consequence, not a preference** — see CHG-02. A
   reviewer may still judge it the wrong architecture.
6. **No holding feature.** Release the crank and nothing in this design holds the
   platform. The source states no such requirement (UNR-BM-002-004), so none was
   added; imposing one because a legacy design used a pawl would be
   NEG-BM-002-014. If the product needs one, that is a source question.
7. **The product is tall and narrow** (140 deep, 224 high, 71 wide excluding the
   handle). "Desktop-sized" has no stated envelope (UNR-BM-002-006).

---

## 6. What is NOT established, and must not be read into this packet

* payload capacity, strength, stress, deflection or margin — **REQ-003 UNSUPPORTED**;
  no strength evidence exists at any fidelity
* crank torque, effort or mechanical advantage — UNR-BM-002-003
* jamming, stability, smooth operation — **REQ-007 NOT_VERIFIED**; contact-level,
  and no V-B evidence exists
* safety and pinch hazards — **REQ-005 INDETERMINATE**; no criterion is stated
* manufacturability, assembly force, tooling, tolerance capability, cost
* wear, fatigue, life
* position holding after release, self-locking
* whether the boundary-crossing hub counts as "enclosed" — **REQ-004
  INDETERMINATE**, AMB-002-01 is carried unresolved
* the compliance edge of "approximately" — UNR-BM-002-002 is carried unresolved;
  90 mm is mid-band, so it does not bite here

**No MuJoCo was run. No FEA was run. No force, stress or strength was simulated.
No demonstration CAD, failure corpus, LOCK file or production code exists.**

---

## 7. Sign-off

| | |
|---|---|
| author self-review of the media | **complete** |
| independent human CAD review | **not started** |
| status | **HUMAN_REVIEW_PENDING** |

The author does not approve this design. Recording the decisions in §4 is the
reviewer's act, not the author's.

---

# PART 2 — Phase B: MuJoCo rigid-body dynamics

**Added after Phase A. The CAD did not change: the geometry signature is
identical, `6824e510…6bc2ee`, and the Phase A validator still passes unchanged.**

Three kinds of evidence now exist and they are **not interchangeable**:

| | what it is | computes |
|---|---|---|
| Part 1 above | CAD geometry and kinematics | exact solid measurement, **no force** |
| `lift_cad_operation.mp4` | **prescribed** CAD animation | a pose law, **no force** |
| Part 2 here | **MuJoCo** rigid-body dynamics | forces, at an **ideal-joint** fidelity, **no contact** |

## 8. What the dynamics model is

The actual joint topology — revolute crank on the CAD crank axis, revolute crank
joint, fixed-length rod, platform joint closed as an equality constraint at the
CAD platform-pin axis, platform on one translational DOF. One net degree of
freedom. **No crank-angle-to-height equation exists in the model**; the platform's
height is whatever the solver produces.

MuJoCo 2.3.7, timestep 1/3000 s, `implicitfast`, Newton solver, gravity
[0, 0, −9.81] m/s², **zero damping and zero friction** in the primary model.

**Densities are DECLARED ASSUMPTIONS — not source requirements, not verified
material selections:** 1200 kg/m³ (housing, panel, platform) and 7850 kg/m³
(shaft, rod, pins). Total product mass **2.76052 kg**, moving mass **1.88964 kg**.

## 9. Results a reviewer may rely on

| quantity | empty | 1 kg payload |
|---|---|---|
| measured travel | **90.0000 mm** | **90.0000 mm** |
| peak actuator torque | **±0.15580 N·m** | **±0.65691 N·m** |
| at crank angle | 105.2° / 254.8° | 111.6° / 248.4° |
| RMS torque | 0.10649 N·m | 0.43031 N·m |
| loop-closure error | 0.000009 mm | 0.000014 mm |
| solver warnings | **0** | **0** |

**Incremental 1 kg payload torque: ±0.50263 N·m, RMS 0.32453, peaks at 113.2° and
246.8°.** This is the **density-independent** result — the only difference between
the two runs is the payload — and it agrees with an **independently implemented**
analytic `τ = m g dz/dθ` to **0.0000703 N·m**, against a declared 2 % tolerance of
0.010052 N·m.

**Speed sensitivity:** RMS torque changes **0.2 %** across a 5× speed range, so the
figures are essentially quasi-static.

**Back-driving:** **12 of 16** release cases move under gravity when the actuator
is released. The four that do not are the 0° and 180° **kinematic dead centres**,
where `dz/dθ = 0`. Maximum platform drop: **70.66 mm** released at 135° or 225°,
**32.11 mm** at 90° or 270°, **7.00 mm** at 45° or 315° — in every case exactly
the height from the release position down to the bottom of travel. The model is
undamped, so the mechanism then swings back like a pendulum. **This mechanism
does not hold position when released.** The source states **no** holding
requirement (UNR-BM-002-004), so this is a **behaviour for a reviewer to weigh,
not a failure**.

**Ideal joint and constraint reactions** — labelled as such, never as contact
pressure or stress:

| reaction | empty | 1 kg payload |
|---|---|---|
| crank bearing | 18.568 N | 29.245 N |
| crank joint | 2.722 N | 14.260 N |
| platform joint | 1.394 N | 12.900 N |
| ideal guide | 1.063 N | 7.186 N |
| ideal guide moment | 0.1128 N·m | 0.8227 N·m |

## 10. Phase B media

* [platform height vs crank angle](../executable_references/EXE-BM002-01/validation/simulation/plots/platform_height_vs_crank_angle.png)
* [actuator torque, empty vs 1 kg](../executable_references/EXE-BM002-01/validation/simulation/plots/actuator_torque_empty_vs_payload.png)
* [incremental payload torque vs analytic](../executable_references/EXE-BM002-01/validation/simulation/plots/payload_incremental_torque.png)
* [rod angle vs crank angle](../executable_references/EXE-BM002-01/validation/simulation/plots/rod_angle_vs_crank_angle.png)
* [ideal joint reactions](../executable_references/EXE-BM002-01/validation/simulation/plots/joint_reactions_vs_crank_angle.png)
* [constraint error vs time](../executable_references/EXE-BM002-01/validation/simulation/plots/constraint_error_vs_time.png)
* [back-drive response](../executable_references/EXE-BM002-01/validation/simulation/plots/backdrive_response.png)

**MuJoCo videos** — simulated, not prescribed:

* [empty cycle, 12.0 s](../executable_references/EXE-BM002-01/validation/simulation/review/lift_mujoco_empty.mp4) · [manifest](../executable_references/EXE-BM002-01/validation/simulation/review/lift_mujoco_empty_video.json)
* [1 kg payload cycle, 12.0 s](../executable_references/EXE-BM002-01/validation/simulation/review/lift_mujoco_payload_1kg.mp4) · [manifest](../executable_references/EXE-BM002-01/validation/simulation/review/lift_mujoco_payload_1kg_video.json)
* [back-drive, four release angles, 10.0 s](../executable_references/EXE-BM002-01/validation/simulation/review/lift_mujoco_backdrive.mp4) · [manifest](../executable_references/EXE-BM002-01/validation/simulation/review/lift_mujoco_backdrive_video.json)

**Reports:** [SUMMARY](../executable_references/EXE-BM002-01/validation/simulation/SUMMARY.json) ·
[environment](../executable_references/EXE-BM002-01/validation/simulation/environment.json) ·
[mass properties](../executable_references/EXE-BM002-01/validation/simulation/mass_properties_report.json) ·
[model consistency](../executable_references/EXE-BM002-01/validation/simulation/model_consistency_report.json) ·
[empty cycle](../executable_references/EXE-BM002-01/validation/simulation/empty_cycle_report.json) ·
[1 kg cycle](../executable_references/EXE-BM002-01/validation/simulation/payload_1kg_cycle_report.json) ·
[torque comparison](../executable_references/EXE-BM002-01/validation/simulation/torque_comparison_report.json) ·
[speed sensitivity](../executable_references/EXE-BM002-01/validation/simulation/speed_sensitivity_report.json) ·
[back-drive](../executable_references/EXE-BM002-01/validation/simulation/backdrive_report.json) ·
[joint reactions](../executable_references/EXE-BM002-01/validation/simulation/joint_reaction_report.json) ·
[constraint stability](../executable_references/EXE-BM002-01/validation/simulation/constraint_stability_report.json) ·
[negative controls](../executable_references/EXE-BM002-01/validation/simulation/negative_control_report.json) ·
[model inputs](../executable_references/EXE-BM002-01/simulation/README.md)

## 11. What Phase B did NOT change

* **REQ-003 payload capacity: UNSUPPORTED — unchanged.** A constraint reaction is
  a resultant, not a stress. No area, no pressure, no deflection, no stress is
  computed anywhere (UNR-BM-002-007).
* **REQ-007 jamming: NOT_VERIFIED — unchanged.** The guide here is a **single
  ideal prismatic constraint**; the real guide is two channels with 0.2 and 0.4 mm
  clearances. No contact is resolved (NRM-BM-002-014, NEG-BM-002-011).
* Safety, manufacturability, effort, wear and life are untouched.

**MuJoCo upgraded nothing, and was never capable of doing so.**

## 12. Additional reviewer questions — all PENDING

| # | question | decision |
|---|---|---|
| D1 | Is a peak crank torque of ~0.66 N·m with 1 kg acceptable for a hand crank at a 26 mm grip radius? That is about **25 N at the grip**. | **PENDING** |
| D2 | The mechanism **back-drives** at every angle except the two dead centres. Is that acceptable for this product, or should a holding feature be added — noting the source requires none? | **PENDING** |
| D3 | Are the declared densities (1200 / 7850 kg/m³) reasonable placeholders, and is the resulting 2.76 kg product mass plausible? | **PENDING** |
| D4 | The crank shaft alone is **1.60 kg** of the 2.76 kg total, because the Ø70 hub is modelled as steel. Should that body be a lighter material or a lighter section? | **PENDING** |
| D5 | Is an ideal-joint rigid-body model the right next fidelity step, or is a contact-resolving model needed before anything further is claimed? | **PENDING** |
| D6 | Given the ideal guide, what evidence would a reviewer want before REQ-007 could move off NOT_VERIFIED? | **PENDING** |

## 13. Author self-review — additional Phase B concerns

* **SC-08 — the crank shaft dominates the mass.** 1.60 kg of a 2.76 kg product,
  from a Ø70 × 45 mm steel hub. The hub is that large because the assembly route
  forces it (SC-01). A reviewer may reasonably ask for a hollow or polymer hub.
* **SC-09 — no holding feature, and it back-drives.** Released at 135° the
  platform falls **70.66 mm**, the full height back to the bottom of its travel.
  Nothing in the source requires holding, but a desktop lift that will not stay
  put may still be judged unacceptable.
* **SC-10 — the torque figures are assumption-dependent.** Only the incremental
  1 kg result is robust. A reviewer should treat the empty and absolute payload
  torques as scaling with the declared densities.
* **SC-11 — zero friction is optimistic.** Real friction would add to the crank
  torque and would damp the back-driving. Both reported behaviours are therefore
  bounds, not predictions.

**Human review remains PENDING. The author does not approve this design.**
