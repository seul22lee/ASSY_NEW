# Package 3 — COMPLETE (visual inspection 99/99, outstanding 0)

A compact engineering reference frame for judging S01–S04 outputs in P4A.
**Not** an Oracle audit and **not** a CAD-validation audit. No experiments were
run; no verdict file was used as the reference. Nothing was modified.

---

## 0A. FINAL VISUAL INVENTORY — inspection closed

**Every assigned image has been opened and visually inspected. Outstanding: 0.**

| reference | mandatory | representative | total inspected | assigned |
|---|---|---|---|---|
| EXE-BM001-01 | 13 / 13 | 10 / 10 | **23** | 23 |
| EXE-BM001-02 | 14 / 14 | 10 / 10 | **24** | 24 |
| EXE-BM002-01 | 35 / 35 | 2 / 2 | **37** | 37 |
| EXE-BM003-01 | 11 / 11 | 3 / 3 + 1 extra | **15** | 14 |
| **total** | **73 / 73** | **25 / 25** | **99** | 97 (+2) |

The frozen scope in `AUDIT_SCOPE.md` §3E estimated ~97. The exact file-level total
is **99**: EXE-BM001-01 has ten pose-state isos where the scope estimated nine,
and `EXE-BM003-01/deployed_locked_top.png` was opened in addition to its eleven
mandatory items. No assigned file was skipped and no file was excluded on the
basis of its name.

**Count corrections.** The first issue of this document reported 16 images; the
actual figure for that pass was 18. The §0 amendment reported 40 cumulative; the
actual figure at that point was 54. Both were undercounts of my own tool calls.
The table above is a file-by-file count, not an estimate.

### 0A.1 Redundant images — inspected, attached, not separately described

Every image below was opened. Each is an unannotated render (a matplotlib-axes
plot with a title, axes in millimetres, and no callouts) showing a configuration
already described by an annotated section or storyboard frame. Each is recorded
here as inspected and attached to the group whose claim it repeats.

| images | attached to | claim they repeat |
|---|---|---|
| `EXE-BM001-01/{closed_latch_engaged, closed_latch_released, closed_reengaged, closing_latch_leadin, opening_started, pin_assembly_compressed, pin_assembly_recovered}_iso.png` (7) | G1, G2, G17 | closed / released / re-engaged poses of the hinged box; no dimension, no callout |
| `EXE-BM001-01/{open, section_knuckle_closed, section_knuckle_open}_iso.png` (3) | G4, G18 | the revolute open pose and the knuckle cut, from a third camera |
| `EXE-BM001-02/{closed_latch_engaged, closed_latch_released, closed_reengaged, closing_latch_leadin, opening_started, open_84, open_intermediate, s_closed_latched, s_closed_released, s_open}_iso.png` (10) | G5, G6, G20, G22 | slide positions and latch states of the sliding-cover box, as translucent wireframe |
| `EXE-BM003-01/{stored, deployed_locked, deployed_released, deployed_locked_section, stored_section}_iso.png` (5) | G12, G13, G28 | the three declared configurations and two section cuts |
| `EXE-BM002-01/review_operation_{02,04,06,07,08}.png` (5) | G25 | intermediate crank angles; each is annotated, and each simply extends the storyboard — 45° 133.0/21.98°, 135° 196.6/21.98°, 225° 196.6/−21.98°, 270° 158.1/−31.97°, 315° 133.0/−21.98°, i.e. the revolution is symmetric about TOP |
| `EXE-BM002-01/review_assembly_{01,02,03,05,08,09}.png` (6) | G11, G24, NEW-2 | the ordered build: empty housing → shaft in from +X → rod down through the open top, pin in along −X → platform pin through three bores → rear panel installed, both pins captured → seven bodies in place |
| `EXE-BM002-01/review_overall_{front,rear}_iso.png` (2) | G23, NEW-6 | overall product with the rear panel closing the +X side |
| `EXE-BM001-02/review_operation_{01,03}.png`, `review_assembly_{01,03}.png` (4) | G20, G21, NEW-4, NEW-5 | the latch cycle and the compliant assembly sequence |

None of the images in this table contradicted an existing claim.

### 0A.2 Substantive findings from the final pass

**NEW-1 — two radii on one body, explicitly not a ratio.**
`EXE-BM002-01/screenshots/review_external_crank_user_interface.png`
Raw text: *"the two radii below are DIFFERENT things on the SAME body"*;
"EXTERNAL HAND-GRIP RADIUS = 26 mm — the radius the user's hand actually turns
on"; "INTERNAL CRANK RADIUS = 45 mm — it sets the platform travel:
travel = 2 × 45 = 90 mm"; and decisively **"Both are features of
BODY-CRANK-SHAFT. They are NOT related by any gear ratio — this mechanism has no
gearing at all."** Also carries a HUMAN REVIEW QUESTIONS box and
**"ERGONOMIC ADEQUACY AND USER EFFORT ARE NOT CLAIMED."**
*Why it matters:* two radii on one body invite being read as an input/output pair
with a ratio. The reference forecloses that reading in the artifact itself.

**NEW-2 — a functional check inside the assembly sequence, before closure.**
`review_assembly_06_open_side_cycle_check.png`: *"Cycle check with the +X side
still open — the mechanism is complete and can be turned before it is closed up"*;
*"the crank has been turned to 120 deg here: the mechanism runs with the +X side
still open."* The design permits verifying the mechanism before the retention body
is installed.

**NEW-3 — guidance evidenced at three configurations with identical clearances.**
`review_section_CC_platform_guides_{bottom,mid,top}.png` each carry the same
measured line: *"Both guides engaged. Side clearance 0.2 each side, tip clearance
0.4, plate-edge gap 0.4 — all measured."* Strengthens G9 from one sample to three.

**NEW-4 — the compliant passage is numerically complete across three frames.**
`EXE-BM001-02/review_assembly_{01,02,03}.png` and `review_section_CC_assembly_snap.png`:
relaxed span **63.6 mm** → tabs held in 2.2 mm each side, span **61.2 mm** → passes
a **59.6 mm** opening → recovers with **2.0 mm of ear under the lip**, and
*"Relaxed span 63.6 mm against a 59.6 mm opening: it cannot go back out the way
it came."* I checked whether the "−1.6 mm clear" in section C-C conflicts with
"ear passing 0.2 mm clear of the lip" in assembly 02; they are a span measure and
a local per-ear measure at different instants of the same passage, and the
three-frame sequence is coherent. **Not recorded as a conflict.**

**NEW-5 — deflection is transient in both BM-001 references.**
`EXE-BM001-02/review_operation_03_slide_open.png`: *"the finger has sprung back:
it is only deflected while the tooth is alongside the end wall, the first 8 mm of
travel"* — 8 mm of an 84 mm stroke. `review_operation_05_reclosed_and_latched.png`:
*"the sloped face is the lead-in: pushing the cover shut drives it against the
keeper corner, which deflects the finger on its own"* and **"the same state as
OPERATION 1: the cycle returns what it started with."** Same pattern as ref-01
(G17): the compliant member is displaced only while clearing the keeper.

**NEW-6 — the product envelope is declared, not justified.**
`review_overall_front_iso.png` dimensions the housing **125 X × 140 Y × 224 Z**,
with the top payload opening at rim z = 224 and the platform at z = 126 when
lowered. The source says only "compact desktop"; UNR-BM-002-006 holds that
unresolved. The reference declares a size and claims no adequacy for it.

**NEW-7 — the actuator is outside the envelope, and is not a separate part.**
`EXE-BM001-02/review_operation_02_release_pressed.png`: *"11 mm of pad standing
outside the product envelope. No tool and no separate part."*

**NEW-8 — one pin, three bores, one motion.**
`review_assembly_05_platform_joint_pin.png`: the platform joint pin is pushed in
along −X *"through clevis lug B, the rod's platform bore and clevis lug A"*.

**No new conflicts were found.** The only unresolved visual conflict remains the
one recorded at §0.3.

---

## 0. Correction to the first issue of this document, and inspection history

**The first issue of this file was wrong about what had been inspected.** It
reported "16 PNGs inspected directly" and then described the remaining ~100 as
"Redundant groups not individually reported", with the claim that "Each shows the
same configuration as an inspected iso or section from a different camera and
adds no engineering fact beyond it."

That wording implies the orthographic sets were opened and merely not written up.
**They were not opened.** The redundancy claim was an inference from filenames,
not an observation, and the assigned budget in `AUDIT_SCOPE.md` §3E was ~97
images (73 mandatory + ~24 representatives), not 16.

**Inspection was resumed and 24 further images were opened. 40 of ~97 assigned
images have now been visually inspected. 57 remain unopened.** Two of the newly
opened images changed the record materially (§0.3), which is itself evidence that
the original redundancy inference was not safe.

### 0.1 Files opened — complete list (40)

**EXE-BM001-01 (13 of 13 mandatory — COMPLETE; 0 of 10 representative isos)**
`review_overview_latch_operation_and_sections` · `review_overview_section_lines` ·
`review_operation_01_closed_latched` · `review_operation_02_release_pressed` ·
`review_operation_03_opening_started` · `review_operation_04_open` ·
`review_operation_05_reclosed_latched` · `review_section_closure_knuckle_pin` ·
`review_section_enclosure_knuckle_pin` · `review_section_knuckle_side_context` ·
`review_section_latch_engaged` · `review_section_latch_released` ·
`review_section_pin_head_and_snap_barb` · plus `pin_assembly_compressed_iso`
(1 of the representative set)

**EXE-BM001-02 (11 of 14 mandatory; 0 of 10 representative isos)**
`review_overview_operation_and_sections` · `review_assembly_02_tabs_compressed` ·
`review_operation_04_full_open_captive` · `review_section_AA_captive_rail_closed` ·
`review_section_BB_captive_rail_full_open` · `review_section_CC_assembly_snap` ·
`review_section_DD_latch_engaged` · `review_section_DD_latch_released`

**EXE-BM002-01 (17 of 35 mandatory; 0 of 2 representative)**
`review_body_identification` · `review_kinematic_chain_annotated` ·
`review_internal_mechanism_rear_panel_removed` ·
`review_overview_operation_and_sections` · `review_assembly_04_platform_entering_guides` ·
`review_operation_01_bottom` · `review_operation_03_rising_90` ·
`review_operation_05_top` · `review_operation_09_bottom_return` ·
`review_section_AA_shaft_and_dual_journals` ·
`review_section_BB_crank_link_platform_bottom` ·
`review_section_BB_crank_link_platform_top` ·
`review_section_CC_platform_guides_mid` · `review_section_DD_crank_joint_retention` ·
`review_section_EE_platform_joint_retention` ·
`review_section_FF_payload_access_bottom` · `review_section_FF_payload_access_top`

**EXE-BM003-01 (11 of 11 mandatory — COMPLETE; 3 of 3 representative isos — COMPLETE)**
`exploded` · `assembly_steps` · `compare_stored_deployed` · `hub_locked` ·
`blocker_engaged` · `blocker_released` · `state_stored` · `state_deployed_locked` ·
`state_deployed_released` · `deployed_locked_section_iso` · `stored_section_iso` ·
`deployed_locked_top` · `stored_iso` · `deployed_locked_iso` · `deployed_released_iso`

### 0.2 Assigned but unopened at the time of the first amendment — NOW ALL OPENED

*(Superseded by §0A. Retained as the record of what was outstanding and when.)*

- **EXE-BM001-02 mandatory (3):** `review_assembly_01_aligned`,
  `review_assembly_03_tabs_recovered`, and operation frames `01_closed_latched`,
  `02_release_pressed`, `03_slide_open`, `05_reclosed_and_latched` *(6 items;
  3 assembly/operation groups)*.
- **EXE-BM002-01 mandatory (18):** `review_internal_mechanism_cutaway_iso`,
  `review_external_crank_user_interface`; assembly frames 01, 02, 03, 05, 06, 07,
  08, 09; operation frames 02, 04, 06, 07, 08; sections
  `BB_crank_link_platform_mid`, `CC_platform_guides_bottom`,
  `CC_platform_guides_top`.
- **Representative orthographic isos (22 of 25):** all 10 for EXE-BM001-01 except
  `pin_assembly_compressed_iso`, all 10 for EXE-BM001-02, both for EXE-BM002-01.
- **Never assigned, correctly excluded (~73):** the pure 4-view ortho duplicates
  (front/side/top companions of an inspected iso).

**What the opened sample of the representative family now establishes by
observation, not inference:** six members were opened across two references
(`stored_iso`, `deployed_locked_iso`, `deployed_released_iso`,
`deployed_locked_section_iso`, `stored_section_iso`, `pin_assembly_compressed_iso`).
All six are unannotated matplotlib-axes renders carrying a title, axes in mm and
no callouts. That is direct evidence about this family — but it is a sample of
six, not a statement about the other 22.

### 0.3 What opening the "redundant" images changed

**OBSERVATION.** `EXE-BM001-01/screenshots/review_overview_section_lines.png` is
annotated **"retention bolt through the closure"**, with a stippled circular
feature drawn at approximately (x 60, y 9). Its title lists the cuts as
"A-A, B-B and D-D", and it labels the snap barb "section C-C".

**CONFLICTING EVIDENCE.** Five other images in the same directory contradict it.
`review_overview_latch_operation_and_sections.png` shows "integral latch: beam,
tooth and release pad, all part of BODY-CLOSURE", lists the cuts as "A-A, B-B,
C-C and E-E", and labels the snap barb "section D-D".
`review_operation_01` through `_05` each carry the annotation **"no separate
bolt, knob, boss or socket exists in this product."**

**WHY IT IS STRANGE.** Two overview images of the same reference disagree about
whether a separate retention bolt exists, and use different section letters for
the same cuts. One of the two is stale relative to the other.

**STATUS: UNRESOLVED.** NEEDS LATER CROSS-READ. This was found only by opening an
image the first issue of this document had classified as redundant on the basis
of its filename.

---

## 1. Reference files read (complete reads)

| path | lines | why |
|---|---|---|
| `ver3/benchmarks/{BM-001,BM-002,BM-003}/source/request.txt` | 1 / 1 / 30 | the only raw text the pipeline reads |
| `ver3/assy_v3/probes/{PRB-01,PRB-02,PRB-03}/request.txt` | 4 each | probe sources |
| `ver3/oracles/product_cases/BM-001/normative.yaml` | 539 | 13 invariants, 9 required-unresolved |
| `ver3/oracles/product_cases/BM-001/freedoms.yaml` | 78 | 13 freedoms |
| `ver3/oracles/product_cases/BM-001/negative_cases.yaml` | 304 | 22 negative cases |
| `ver3/oracles/product_cases/BM-001/stage_expectations.yaml` | 181 | s01–s04 must_exist; evaluability prerequisites |
| `ver3/oracles/product_cases/BM-002/normative.yaml` | 503 | 14 invariants, 8 required-unresolved |
| `ver3/oracles/product_cases/BM-002/freedoms.yaml` | 65 | 11 freedoms |
| `ver3/oracles/held_out/BM-003/normative.yaml` | 525 | 18 invariants, 4 state-maintenance classes, 9 required-unresolved |
| `ver3/oracles/held_out/BM-003/freedoms.yaml` | 164 | 13 freedoms + binding rule |
| `ver3/oracles/held_out/BM-003/assembly_and_mobility_expectations.yaml` | 252 | 7 assembly + 9 mobility evidence expectations |
| `ver3/oracles/micro_oracles/*/README.md` (4 files, capability sections) | ~40 each | to judge probe applicability honestly |

Deliberately **not** read: Oracle governance and correction history, mutation
suites, auditor implementations, `_dossiers/`, `evidence_cases`,
`evidence_scope`, `source_map`, `realizations` beyond what freedoms already
enumerate, the `C4-drawer` pack, all CAD `validate.py` / `build.py` /
`simulate_*.py`, all numeric validation JSON, and both interrupted BM-003
validation directories.

---

## 2. PNG files inspected directly (16), grouped by visual purpose

Prior review documents were **not** used as substitutes. Every claim below is
what the image itself shows.

### G1 — BM-001 ref-01: overall arrangement and closed/latched state
`EXE-BM001-01/screenshots/review_overview_latch_operation_and_sections.png`
**Visible:** plan at Z=47, three bodies; hinge axis marked at Y≈86 with five
interleaved knuckles on a pin; closure plate covering the aperture; "integral
latch: beam, tooth and release pad, all part of BODY-CLOSURE"; keeper rib on the
enclosure front face; cut lines A-A, B-B, C-C, E-E; release direction "PULL THE
PAD OUT (−Y)".
**Supports:** a revolute closure with a *single-body integral* latch, and an
actuator reachable from outside.
**Does not prove:** that the hinge or latch functions; only that the geometry and
its cut planes exist.

### G2 — BM-001 ref-01: retention engagement, engaged vs released
`review_section_latch_engaged.png` · `review_section_latch_released.png`
Same cut plane (X=60), same scale.
**Visible, engaged:** `FEA-E-KEEPER` is a rib on the enclosure's own front face,
"its UNDERSIDE is the blocking face"; 2.2 mm of tooth lies under the keeper;
`FEA-C-LATCH-SHOULDER` sits 0.4 mm below the keeper as declared closed free play;
`FEA-C-RELEASE-PAD` is outside the product; arrow "OPENING BLOCKED" pointing +Z.
**Visible, released:** "declared compliant configuration: the beam pulled 2.4 mm
outward"; "the keeper is untouched — it is still there; the tooth has moved past
it"; "the tooth is now outboard of the keeper's front face, so nothing stands
over it"; arrow "NOW FREE TO OPEN".
**Supports:** retention is a *localized feature pair* with a *named blocked
direction*; the released state is a *different pose of a declared compliant
region*, not a changed enclosure; the keeper is not consumed, so the cycle can
repeat.
**Does not prove:** any force, any strain, or that the beam can actually deflect
2.4 mm in a real material.

### G3 — BM-001 ref-01: pin retention, both axial directions
`review_section_pin_head_and_snap_barb.png`
**Visible:** section C-C at Z=50 through the hinge pin. "head shoulder bears on
the counterbore: blocks travel toward +X"; "recovered lug shoulders bear on the
last knuckle face: block travel toward −X"; "arms split here"; title says "both
axial directions blocked".
**Supports:** a retention claim needs **one identified feature per blocked
direction** — two different features here, not one relation labelled "retained".
**Does not prove:** that the barb recovers, or that either shoulder is strong
enough.

### G4 — BM-001 ref-01: open state and its determinant
`review_operation_04_open.png`
**Visible:** OPEN at 110°; "stop block on the rear wall; the pin still carries the
hinge"; "no separate bolt, knob, boss or socket exists in this product".
**Supports:** the terminal open pose is produced by a *realized* feature (a stop
block), and retention is achieved without a separate carrier body.
**Does not prove:** that 110° is required or adequate — the Oracle leaves the
open-state form free.

### G5 — BM-001 ref-02: a materially different topology for the same source
`EXE-BM001-02/screenshots/review_overview_operation_and_sections.png`
**Visible:** **two** bodies. "BODY-ENCLOSURE: cavity, top panel, two captive
rails"; "BODY-COVER: plate, four retention tabs, one latch finger. Everything
that retains or latches it belongs to it"; "COVER SLIDES OPEN" (−X); "retention
tab: cantilever beam + ear under the lip (×4)"; "latch finger and tooth, out
through the end wall. **Over the rail, not over the aperture** — so at full open
it retracts over the ledge and not into the opening."
**Supports:** the same source admits a **prismatic** closure with a different body
count, a different retention principle and a different assembly — the two BM-001
references are the corpus's own demonstration that no single mechanism is the
answer. Also: a feature's retracted position was explicitly kept out of the
declared access region.
**Does not prove:** which of the two is better; the Oracle forbids that comparison.

### G6 — BM-001 ref-02: captivity across the whole travel
`review_section_BB_captive_rail_full_open.png`
**Visible:** "the same capture at FULL OPEN — nothing about it has changed"; "the
ear is under the lip here exactly as it is when closed. **A 3 mm lift meets
124.8 mm³ of solid at 0, 10, 40, 70 and 84 mm**"; "no opening, no relief, no
removal position"; arrow "ORDINARY REMOVAL DIRECTION".
**Supports:** captivity is demonstrated at **five interior positions** across the
travel against a named escape direction — not at the endpoints.
**Does not prove:** behaviour under load, or that 3 mm is the right probe.

### G7 — BM-002: the kinematic chain, named end to end
`EXE-BM002-01/screenshots/review_kinematic_chain_annotated.png`
**Visible:** an explicit chain — "grip → shaft → journal land 1 → journal land 2 →
crank arm → crank joint pin → connecting rod → platform joint pin → platform
clevis → platform → guide followers → guide channels → housing". Feature IDs 1–10.
`FEATURE-SHAFT-CRANK-ARM R 45`; `BODY-CONNECTING-ROD 85 mm between bore centres`;
**two distinct pins** — `BODY-CRANK-JOINT-PIN` and `BODY-PLATFORM-JOINT-PIN`, in
different bores; **two guide pairs** — front and back, each a housing channel plus
a platform follower.
**Supports:** an uninterrupted, localized interaction chain from external input to
a reaction site; two revolute joints at distinct locations; crank radius and rod
length as two distinct non-zero values.
**Does not prove:** any force, torque or jamming behaviour.

### G8 — BM-002: shaft support, and a support that was refused
`review_section_AA_shaft_and_dual_journals.png`
**Visible:** "**BOTH journal lands belong to BODY-HOUSING. The rear panel is not a
shaft journal: the connecting rod occupies the crank axis, so the shaft cannot
reach the panel.**" `BODY-REAR-PANEL … carries NO shaft journal`. Detail 1: LAND 1
(x 0–8) and LAND 2 (x 14–26) with a RELIEF between them (x 8–14), 0.2 mm running
clearance at each land. Detail 2: a Ø80 thrust collar as a pull-out stop, 1.0 mm
clearance. `FEATURE-SHAFT-HUB Ø70 crosses the wall AND is the journal surface for
both lands`; `FEATURE-SHAFT-GRIP Ø12 at radius 26, entirely outside the housing`;
overhung crank arm at x 30–40 with both lands on its −X side.
**Supports:** a support assignment that is topologically plausible can be
*geometrically impossible*, and the reference records the refusal in the geometry
itself. Also: the boundary crossing is realized and the crossing element is
supported elsewhere.
**Does not prove:** bearing adequacy, wear or alignment.
**Image carries its own limit:** "CAD geometry only. Structural strength, user
effort, jamming, safety and manufacture are NOT VERIFIED."

### G9 — BM-002: guidance engaged mid-travel
`review_section_CC_platform_guides_mid.png`
**Visible:** section at mid-stroke, crank 90°. "Both guides engaged. Side
clearance 0.2 each side, tip clearance 0.4, plate-edge gap 0.4 — all measured."
Front and back follower details; front follower x 22–48 in a 21.8–48.2 slot.
**Supports:** guidance is evidenced **at an interior configuration**, on both
guides, with the clearances declared.
**Does not prove:** absence of binding, friction or wear.

### G10 — BM-002: motion extremum, honestly labelled
`review_operation_05_top.png`
**Visible:** crank 180°, support-surface z = 216.0, connecting-rod angle 0.00°
from vertical, state TOP. Legend names seven entities including
`PAYLOAD (SCENARIO)` marked "scenario object, moves with the platform for
visualisation only". Footer: "**KINEMATIC EXTREMUM — NOT A VERIFIED PHYSICAL HARD
STOP. Turning the crank further carries the platform back the other way.**"
**Supports:** a travel extreme may be a *dead-centre kinematic* extremum with no
physical stop, and saying so is correct rather than a gap; the payload is a
scenario object, not a product body.
**Does not prove:** anything about holding position at the top.

### G11 — BM-002: assembly insertion
`review_assembly_04_platform_entering_guides.png`
**Visible:** "Platform lowered into BOTH guide channels; the followers enter the
channels from their open upper ends; the clevis comes down either side of the
rod"; insertion direction −Z. Footer: "GEOMETRIC ASSEMBLY-SEQUENCE
REPRESENTATION. INSERTION FORCE NOT VERIFIED. No contact and no force is
simulated."
**Supports:** each assembly step has a named body, a named direction and the
relationships it establishes.
**Does not prove:** that the path is clear — the image is a representation, not
the sweep.

### G12 — BM-003: bodies and repeated members
`EXE-BM003-01/screenshots/exploded.png`
**Visible:** ten bodies — HUB, LEG-A/B/C, PIN-A/B/C, RING, RING-CAPTOR,
TOP-SUPPORT — displaced along their own installation directions. Three legs each
with **its own pin**; a ring and a separate ring captor.
**Supports:** repeated members are individually identified and individually
retained.
**Does not prove:** assemblability — the caption states "displacement is for
display only and is not an assembly path".

### G13 — BM-003: stored vs deployed, reported relationally
`compare_stored_deployed.png`
**Visible:** same camera, same scale. STORED bbox x 96.9 / y 88.8 / z 259.4;
DEPLOYED bbox x 204.2 / y 176.9 / z 237.4. Caption: "**x and y shrink when
folded; z grows, and that is reported rather than hidden.**"
**Supports:** compactness stated as a *relation on a declared extent*, with the
extent that grew reported rather than suppressed.
**Does not prove:** that the folded envelope is "compact" in any absolute sense —
the image says that meaning is unresolved.

### G14 — BM-003: state maintenance engaged vs released
`blocker_engaged.png` · `blocker_released.png` (same camera, same cutaway)
**Visible, engaged:** "the arm is directly over the heel; folding back drives the
heel into it" — a ring arm sits above the leg's heel.
**Visible, released:** "the ring has been lifted **and** turned; the arm is no
longer over the heel" — the ring is visibly higher and rotated, the arm clear.
**Supports:** the released configuration is **geometrically distinct** from the
engaged one, and the deliberate action is a **two-motion** (lift + turn) change of
a real body's pose — not a flag.
**Does not prove:** the gap, the fold-back angle or any disturbance resistance;
both images state those numbers live in `validation/state_maintenance.json`.
**Both carry:** "CUTAWAY FOR DISPLAY ONLY … the model is unchanged."

### G15 — BM-003: deployed footprint
`deployed_locked_top.png`
**Visible:** plan view; three legs radiating at roughly equal angular spacing;
three ground contacts near (0,+115), (−105,−55), (+100,−55) — non-coincident,
non-collinear, bounding a clear area.
**Supports:** a non-degenerate footprint.
**Does not prove:** stability, tipping margin or load capacity.

### G16 — BM-003: assembly sequence and retention termination
`assembly_steps.png`
**Visible:** fifteen declared steps, each frame the configuration *after* the
step: HUB fit → LEG-A fit → PIN-A fit → **PIN-A turn** → LEG-B fit → PIN-B fit →
**PIN-B turn** → LEG-C fit → PIN-C fit → **PIN-C turn** → RING fit → RING-CAPTOR
fit → **RING-CAPTOR turn** → TOP-SUPPORT fit → **TOP-SUPPORT turn**. Every frame
from AS-05 on shows the legs spread — **the assembly ends DEPLOYED**.
**Supports:** five "fit-then-turn" pairs, i.e. retention terminated by *rotation*
five times; an explicit ordering; and an assembly that must finish in the deployed
configuration.
**Does not prove:** path clearance — the caption says the sweeps are in
`validation/assembly_report.json`.

### G17 — BM-001 ref-01: the five-frame operation cycle
`review_operation_01_closed_latched` · `_02_release_pressed` · `_03_opening_started`
· `_04_open` · `_05_reclosed_latched` — all cut at X=60, same scale.
**Visible:** 01 "the tooth is behind the keeper; the lid cannot be lifted",
OPENING BLOCKED. 02 "the beam is deflected 2.4 mm; the tooth is clear", PULL THE
PAD (−Y). 03 **"the tooth is above the keeper, so the beam has already sprung
back"**, LID ROTATES OPEN. 04 OPEN at 110°, "stop block on the rear wall". 05
**"the lead-in ramp did the work; nothing was pushed back by hand"**, PUSH SHUT —
THE LATCH SNAPS BACK. All five carry "no separate bolt, knob, boss or socket
exists in this product".
**Supports:** the compliant deflection is **transient** — needed only to clear the
keeper, recovered before the lid has opened; and re-engagement is driven by a
lead-in ramp, not a second manual action. Together these realize the
engage → release → re-engage cycle as a physical sequence.
**Does not prove:** any force, or that the beam survives repetition.

### G18 — BM-001 ref-01: the hinge realized on both bodies
`review_section_closure_knuckle_pin` · `review_section_enclosure_knuckle_pin` ·
`review_section_knuckle_side_context`
**Visible:** A-A "closure knuckle on the pin … pin shaft, 0.1 radial running
clearance … closure plate seats on the rim here". B-B "enclosure knuckle on the
pin (head-side segment) … pin in the enclosure bore … enclosure knuckle and its
web down to the rear wall". D-D on the hinge axis: **"enclosure segments (3)
alternate with closure segments (2)"**, "pin runs the full width".
**Supports:** engagement geometry exists on **each** participating body, at a
declared running clearance, interleaved 3+2 across the full width.
**Does not prove:** bearing life or pin strength.

### G19 — BM-001 ref-02: one rail performing three functions
`review_section_AA_captive_rail_closed`
**Visible:** three numbered callouts on one feature pair — "1. LEDGE — carries the
cover (INT-01/02)"; "2. GUIDE WALL — locates it sideways, 0.2 mm on the tab tip
(INT-03/04)"; "3. RETAINING LIP — overhangs the ear and blocks lift (INT-05/06)".
Plus "the plate passes between the lips — which is how it got in, and why no
relief is cut anywhere in the rails."
**Supports:** support, guidance and retention as three separately identified
interactions on one geometric pair, each with its own interaction IDs.
**Does not prove:** any load capacity.

### G20 — BM-001 ref-02: latch blocked direction and released pose
`review_section_DD_latch_engaged` · `review_section_DD_latch_released`
**Visible, engaged:** "one connected feature, from pad to tooth"; keeper is "the
end wall standing beside the slot, 2.2 mm of it behind the tooth"; "tooth, 2.6 mm
outboard of the finger"; slot edge at y = 5.6; **BLOCKED** arrow in −X, the
slide-open direction. **Released:** "declared compliant configuration: finger and
tooth pushed 2.6 mm inboard"; "the tooth is now inboard of y = 5.6, the slot edge,
so the whole assembly passes out through the slot"; "the keeper strip is
untouched. It is still there; the tooth has simply moved past it"; NOW FREE TO
SLIDE.
**Supports:** the blocked direction here is **translation**, where ref-01's is
**lift** — two mechanisms, two different named blocked directions, and in both the
keeper is untouched while the compliant member moves.

### G21 — BM-001 ref-02: assembly by declared compliant passage
`review_section_CC_assembly_snap` · `review_assembly_02_tabs_compressed`
**Visible:** both titled "geometric state illustration of a declared compliant
configuration — **not a deformation simulation**". COMPRESSED: "ear tip at
y = 5.4, inboard of the lip inner edge at y = 5.2. Span 61.2 mm through a 59.6 mm
gap, −1.6 mm clear." RECOVERED: "the tip returns to y = 3.2 and 2.0 mm of ear sits
under the lip"; "the beam deflects into a 2.4 mm slot cut in the plate";
"recovery on release". And: **"limiting opening 59.6 mm: the real gap between the
lip inner edges, not an axis-aligned bounding box"**; "ear passing 0.2 mm clear of
the lip"; "two bodies only — nothing is inserted here".
**Supports:** an insertion with **negative** clearance (−1.6 mm) declared as a
compliant passage rather than reported as interference; and the limiting dimension
taken from the real feature pair, explicitly not from a bounding box.
**Does not prove:** insertion force, or that the material tolerates 1.6 mm.

### G22 — BM-001 ref-02: declared usable access and the open bound
`review_operation_04_full_open_captive`
**Visible:** "FULL OPEN — 84 mm of the 90 mm aperture is clear, and the cover is
still captive"; "84 mm USABLE OPENING"; "aperture, now uncovered from x = 103 to
x = 187"; "all four retention tabs are still inside the rails, under lips that run
the whole length"; "the cover has not left the rails and cannot"; **"open bound:
the cover's end face on solid material at x = 13. A stop, not a relief — there is
no gap in the rails to lift through."**
**Supports:** the declared usable access region as a measured sub-region of the
aperture; the open-state determinant as a realized stop; and captivity maintained
at the open extreme.

### G23 — BM-002: seven bodies, and the scenario object excluded
`review_body_identification`
**Visible:** "seven product bodies", numbered 1 BODY-HOUSING, 2 BODY-REAR-PANEL,
3 BODY-PLATFORM, 4 BODY-CRANK-SHAFT, 5 BODY-CONNECTING-ROD, 6 BODY-CRANK-JOINT-PIN,
7 BODY-PLATFORM-JOINT-PIN. Separately boxed in red: "SCENARIO-PAYLOAD-1KG —
**SCENARIO OBJECT — NOT A PRODUCT BODY**". Banner: "DISPLAY CUTAWAY — THE MODEL IS
UNCHANGED".
**Supports:** the product body set is closed and the payload is explicitly outside
it.

### G24 — BM-002: both pins captured by one later body
`review_section_DD_crank_joint_retention` · `review_section_EE_platform_joint_retention`
· `review_internal_mechanism_rear_panel_removed`
**Visible, D-D:** "−X STOP: the pin head seats on the rod's +X face. Measured free
travel 0.000"; "+X STOP: FEATURE-PANEL-CRANK-PIN-LAND, integral to
BODY-REAR-PANEL. Annulus r 36–54, **so it faces the pin head at EVERY crank
angle**"; "The rear-panel land is INTEGRAL to the panel. It is not a separate
retainer: **there is no circlip, washer or screw anywhere in this product**";
measured −X 0.000 blocked by the rod, +X 2.000 blocked by the rear panel; 0.1 mm
radial running clearance.
**Visible, E-E:** the same two-stop pattern for the platform pin; "+X STOP …
spans z 94–200, the pin's whole travel"; "two lugs straddle the rod, **so the
joint is not a cantilever**"; and **"Both lands arrive in the SAME −X motion that
seats the panel, so the pins are captured the moment the product is closed and
not before."**
**Visible, panel removed:** banner "REAR PANEL REMOVED FOR REVIEW — IT IS PART OF
THE PRODUCT"; inset of the panel's inner face "It carries BOTH pin-retention
lands", PLATFORM-PIN-LAND y 61–79 z 94–200, CRANK-PIN-LAND annulus r 36–54.
**Supports:** the *later-body-cover* retention strategy realized once for two
joints, with each pin's two axial stops separately identified and measured, and
each land shown to remain effective across the whole motion.

### G25 — BM-002: the cycle returns, sampled across a full revolution
`review_operation_01_bottom` · `_03_rising_90` · `_05_top` · `_09_bottom_return`
**Visible:** 01 crank 0°, support z = 126.0, rod 0.00° from vertical, BOTTOM.
03 crank 90°, support z = 158.1, rod 31.97°, RISING. 05 crank 180°, support
z = 216.0, rod 0.00°, TOP. 09 crank 360°, support z = 126.0, rod −0.00°, BOTTOM
RETURN. Identical camera and scale in all nine frames.
**Supports:** travel 126.0 → 216.0 = **90.0 mm = 2R** with R = 45, confirmed at
both extremes; a genuinely swinging rod at the interior sample; and a full
revolution returning to the same support height.
**Does not prove:** anything dynamic — every frame carries the kinematic-extremum
and NOT-VERIFIED footers.

### G26 — BM-002: payload access terminating at the platform, with open questions
`review_section_FF_payload_access_bottom` · `_top`
**Visible:** "HOUSING RIM z = 224 — **this is the APERTURE, not the endpoint**";
"FEATURE-PLATFORM-SUPPORT-SURFACE — the access path ENDS on this face"; measured
blocks giving rim-to-support 98 mm at bottom and 8 mm at top, "overlap during
descent 0.000000 mm³". And: **"The endpoint is the PLATFORM SURFACE. Accepting
the rim as the endpoint is the defect NEG-BM-002-007 describes, and negative
control NC-14 tests for it."** Also "1 KG SCENARIO DECLARED. STRUCTURAL CAPACITY
NOT VERIFIED — no strength evidence exists at any fidelity."
Both images carry a **HUMAN REVIEW QUESTIONS** box: "Is payload access adequate at
BOTTOM and at TOP? Is the 8 mm top recess acceptable…? Is an open-top arrangement
acceptable for this product?"
**Supports:** an access path whose endpoint is the functional surface, not the
boundary — and a reference that carries its own unresolved human-review questions
on the artifact instead of asserting adequacy.

### G27 — BM-002: section index and the three-configuration sections
`review_overview_operation_and_sections` · `review_section_BB_…_bottom` · `_top`
**Visible:** the index lists A-A through F-F with each cut's purpose, and records
that **B-B and C-C are each taken at BOTTOM, MID-STROKE and TOP**. B-B bottom and
top are dimensioned on the image: **ROD CENTRES 85** and **CRANK RADIUS 45** with
arrows; crank axis y 70, z 60; platform joint z = 100.0 at bottom and z = 190.0 at
top; guide channel travel direction vertical.
**Supports:** crank radius and rod length as two distinct dimensioned values, and
the chain evaluated at three configurations rather than two.

### G28 — BM-003: the three declared configurations and the lock mechanism
`state_stored` · `state_deployed_locked` · `state_deployed_released` · `hub_locked`
**Visible:** STORED "legs alongside the column; ring lifted and turned so its arms
clear the heels". DEPLOYED, LOCKED "ring down on the pedestal, **each arm a
declared gap above one heel**". DEPLOYED, RELEASED "ring lifted clear of the ribs
and turned; the arms have moved off the heels". HUB, LOCKED "**ring seated on the
pedestal; ribs inside the ring's keyways; ring captor above**".
**Supports:** the release is a genuine **two-motion** sequence with a geometric
reason for its order — the ring must lift clear of the hub ribs before it can
turn, because the ribs sit in its keyways when seated. The ring captor is a
separate body retaining the ring. Locking is a declared gap above a heel, not a
contact.
**Does not prove:** the gap value or the fold-back angle; all four images point to
`validation/state_maintenance.json` for those, and three carry "Review aid only;
every geometric claim is a kernel measurement in validation/".

**All remaining assigned images were subsequently opened.** The 45 inspected in
the final pass are recorded in §0A: those carrying new engineering content appear
as NEW-1 … NEW-8, and those that repeat an existing claim are listed image-by-image
in §0A.1 with the group each is attached to. The earlier claim that unopened
images "add no engineering fact" was withdrawn before this pass, and the final
pass justified withdrawing it — `review_external_crank_user_interface.png`
(NEW-1) was in the not-yet-opened set and carries a fact available nowhere else.

---

## 3. BM-001 engineering reference sheet

*Source: one paragraph — compact desktop storage box, reusable latch, opens and
closes repeatedly, no accidental opening in normal handling, easy to operate,
secure in transport, low-cost, desktop-practical, mechanically plausible, easy to
assemble.*

**A. Problem-level.** Two states — closed and open — connected by a motion in both
directions (`NRM-BM-001-001`). An interior cavity reachable through the aperture
at open (`-009`). A user who operates a retention release (`-008`). Ambiguity is
recorded, not resolved.

**B. Mechanical.** A physically realized closure connection: engagement geometry
on **each** participating body wherever the concept declares contact, and support
present wherever the chosen concept depends on it (`-002`). A retention function
holding closed against a *declared* disturbance, released by a deliberate action,
with engagement **localized on both bodies** (`-006`). One full engage → release →
re-engage cycle realizable with every participating feature's retention-critical
geometry still present (`-007`). For each load-carrying interface, a path to a
reaction site (`-011`). Each discretely installed part has a realizable
installation *process* through no **undeclared** rigid material (`-010`).

**C. Spatial / kinematic by S04.** At open, the closure does not obstruct the
**declared** usable access region; along the transition there is no volumetric
overlap outside declared contact / interference / compliant regions (`-003`).
Material content conserved across states; any shape change is a declared
compliant deformation (`-004`). Where a discrete terminal open pose is declared it
must reference a **realized determinant**; where an open configuration *region*
is declared instead, that is equally admissible (`-005`).
*Reference demonstrations:* the two references answer this with different
topologies — revolute + integral compliant latch + stop block (G1–G4), and
prismatic + four captive tabs + rail lip, with captivity sampled at five travel
positions (G5–G6).

**D. Negative cases that matter (22 total; the classes a superficially plausible
design must survive).** Open pose produced only by an analysis-model joint range
(`NEG-001`). A joint type with correct axis and poses but no engagement geometry
on either body (`-002`). A closure lying across its own declared access at open,
passing an endpoint-only check (`-003`). A transition through solid, stored as two
endpoints (`-004`). Extent shrunk at open to achieve clearance (`-005`). A typed,
directional retention relation with no engagement site, no feature pair and no
contact normal (`-006`). An access path terminating at the exterior surface
*beside* the actuator (`-007`). A body given the world origin because nothing
derived its placement (`-008`). An incomplete candidate winning on part count
(`-009`). Retention released by breaking a tab — physically single-use while
declaring `reusable: true` (`-013`). A 3 mm penetration labelled "contact"
(`-017`). A snap declared with no compliant region anywhere (`-019`).
Two **process** negatives run the other way: intended contact reported as
interference must be **rejected** (`-021`), and a declared snap/press insertion
reported unassemblable because no collision-free path exists must be **rejected**
(`-022`).

**E. Freedoms (13).** Closure mechanism family; retention mechanism family; which
boundary carries the aperture; **motion type** (rotation, translation, compound
and detachment equally admissible); part count and decomposition; enclosure form;
all dimensions, tolerances and clearances; material and process; what determines
the open pose; number and arrangement of retention sites; **whether the closure
stays attached at open**; whether the open state is a discrete pose or a
configuration region; which region of the aperture is the usable access.

---

## 4. BM-002 engineering reference sheet

*Source: enclosed desktop platform lift, external hand crank, platform rises and
falls ≈80–100 mm, payload ≈1 kg, mechanism enclosed in normal operation, safe,
assemblable, manufacturable, avoid obvious jamming or unstable operation.*

**A. Problem-level.** A user-operated rotary input **outside** the housing driving
a platform **inside** it, through an uninterrupted chain of realized interactions
(`NRM-BM-002-001`). Manual drive only — no stored or supplied energy source
(`-013`). A payload placeable on and removable from the platform along an access
path terminating **at the platform**, not the housing boundary (`-010`).

**B. Mechanical.** Rotary→linear conversion through at least one realized
interaction with participating geometry identified on **each** body it acts
between (`-003`). The boundary crossing realized without unintended interference,
with whatever support the selected realization needs present **somewhere** — not
necessarily at the crossing (`-002`). Every element carrying a transverse/radial
load has a realized radial reaction; every element carrying axial load has an
axial reaction — **only for the components that realization actually produces**
(`-006`). Platform load path to a reaction site (`-011`). Assembly per `-012`.

**C. Spatial / kinematic by S04.** Declared travel ≈80–100 mm with the qualifier
preserved (`-004`). Guidance sufficient to preserve the travel and orientation the
scenario requires — **anti-rotation only where the scenario or the conversion
needs it** (`-007`). At every required pose, no undeclared overlap between
platform and housing, and the required path traversable (`-008`). Where a travel
extreme is declared a *physical end of travel*, it is produced by a realized
condition evaluated **at its own configuration**, with no result copied between
extremes (`-009`).
*Reference demonstrations:* the named chain and two distinct pins (G7); both
journal lands on the housing with the rear panel explicitly refused as a journal
(G8); both guides engaged mid-stroke (G9); TOP declared a kinematic extremum and
**not** a hard stop (G10).

**D. Negative-case classes.** `NRM-BM-002-014` is the sharpest: evidence from a
model that imposes the input/output relation **by declaration** may not be cited
for the existence, engagement or contact behaviour of the conversion — under
declared coupling the transmission relation is exact by construction, so the
observable reports the declaration.

**E. Freedoms (11).** Chain topology; conversion family (helical thread, rack,
cable-and-drum, crank-and-link, cam, scissor); guidance strategy, guide count,
**and whether platform rotation is restrained at all**; where and how the chain
crosses the boundary; support arrangement for rotating elements; what determines
each travel extreme and whether the two share a part; payload access; **whether
the mechanism holds position when released**; housing form, part count, material,
process; **whether physical ends of travel are declared at all**; where the
crossing element is supported.

---

## 5. BM-003 engineering reference sheet

*Source: 30 lines, containing no digit. Compact folding desk stand, three legs
folding close to the body, everything stays attached, nothing removed, opens by
hand in a sensible sequence, legs spread to a usable footprint, nothing comes
apart while opening, stays open on its own, legs must not fold back / twist aside
/ come off, something deliberate before it can fold again, folds back to the same
compact shape, repeatable, holds a small object, buildable in a sensible order.*

**A. Problem-level.** Three distinguishable legs, each with a stored pose close to
the body (`NRM-BM-003-001`). Stored configuration singly connected (`-002`).
Ordinary folding/unfolding requires no removal and no loose item (`-003`). A
manual, comprehensible deployment sequence to DEPLOYED (`-004`). No tool, motor or
external fixture (`-008`). A support region identifiable and geometrically
available in DEPLOYED (`-007`).

**B. Mechanical.** The deployed configuration persists without continuous user
support and does not enter folding before the deliberate release (`-009`). No
unintended gross rigid-body freedom in DEPLOYED — a leg cannot fold back, twist
aside, translate out of place or detach; per leg the design declares intended and
**forbidden** mobility, and each forbidden freedom is either kinematically
unavailable **or** covered by a declared state-maintenance class (`-010`). A
deliberate action gates folding, in four parts: folding does not begin
unintentionally; the action **changes the system** so folding can proceed; the
complete return path then exists; retention stays coherent through it (`-011`).
Every declared motion, constraint or retention relationship has an identifiable
physical realization on **all** participating bodies **or functional regions**
appropriate to its realization class, and for retention the **blocked escape
direction** is identified (`-016`). A physically coherent assembly sequence, each
step's path evaluated *in the configuration produced by the preceding steps*, the
dependency relation acyclic (`-014`); every operational relationship activated by
some assembly step (`-015`).

**C. Spatial / kinematic by S04.** Connectedness preserved at **every sampled
point** of the deployment path, not only endpoints (`-005`). Three legs extending
in materially different directions with ground contacts neither coincident nor
collinear — convex hull of non-zero area (`-006`). A continuous return path to the
**same** stored configuration, repeatable, no one-way step (`-012`). Every normal
component attached and every retention active at every sampled configuration of
the full cycle (`-013`). No interpenetration at any sampled point on any declared
path, except a declared deformation-resolved path with its region and mode
identified (`-017`). At least one declared storage-relevant extent smaller in
STORED than DEPLOYED (`-018`).
*Reference demonstrations:* ten bodies with per-leg pins (G12); stored/deployed
extents reported with the growing axis stated (G13); engaged vs released as two
distinct ring poses via lift+turn (G14); non-degenerate footprint (G15);
fifteen steps with five fit-then-turn retention terminations, ending deployed
(G16).

**D. The four state-maintenance classes** — the single most important structural
idea in this pack. A design **declares one class**; the class determines what must
be shown and what evidence can show it, and **never** whether the design is
admissible.
`SMC-KINEMATIC_BLOCK` — folding path absent; mobility analysis with the
obstructing geometry identified. `SMC-STABLE_EQUILIBRIUM_OR_ENERGY_BARRIER` —
folding path **may exist**; stability or potential-energy evidence.
`SMC-CONTACT_OR_COMPLIANT_RETENTION` — path may exist; contact-resolving or
reduced-order compliance evidence. `SMC-OTHER_DECLARED_PHYSICAL_PRINCIPLE` — a
principle the Oracle's author did not anticipate, with its predicate and route.
Only the first has an available route in this toolset; the other three are
**admissible with persistence NOT_VERIFIED**. Rejecting a design because a folding
path exists is a defect, not a finding.

**E. Negative-case classes named in the material.** Insertion checked against the
empty frame rather than the partially built product; endpoint-only path evidence;
evidence for one leg taken as evidence for the stand (`three_leg_completeness_rule`);
treating a spring/detent/collar as mandatory (`FRE-BM-003-008` → `NEG-BM-003-013`);
a friction- or compliance-dependent claim reported PASS from a zero-friction
ideal-joint rigid model.

**F. Freedoms (13), binding on the Oracle itself.** Locking principle; joint type
everywhere; **body count** ("three legs" is a count of supports, not of bodies);
central vs distributed coordination; deployment sequence and step count; retention
realization; hub arrangement **or its absence**; use or absence of springs,
detents, braces, collars, rings, captive sliders, over-centre geometry; whether
state maintenance and release are one feature or two; materials; **all dimensions,
angles, proportions and clearances** — "no predicate in this Oracle may compare
any dimension against a threshold"; aesthetics; which configuration assembly ends
in.

---

## 6. PRB-01 / PRB-02 / PRB-03 capability reference sheets

The four micro-oracle capabilities are: *bounded-two-state-closure* (two defined
states by a bounded motion, each extreme physically produced), *guided-slider*
(guided translation along a declared line/path, with the freedoms constrained that
the motion requirement depends on), *latch-retention* (holding two bodies in a
defined relative state against a disturbance, released by a deliberate action,
repeatably), *rotary-to-linear-engagement* (rotary→linear through an uninterrupted
chain of realized localized interactions, with reaction of the loads produced).

### PRB-01 — wall-mounted dispenser, one item per lever press
**Capability tested:** metering — separating **exactly one** item from a group, on
each actuation, with refill from above and continued function when nearly empty.
**No authoritative micro-oracle applies to the central capability.** None of the
four describes controlling the passage of *external items through* a product;
all four describe relative motion of the product's own bodies. This is the gap the
corpus itself recorded when the probe was first run. *Secondary, partial
applicability:* the lever's actuation is a bounded two-state motion
(`bounded-two-state-closure`), and a translating gate would instantiate
`guided-slider`.
**Facts a design that understands the capability should establish:** a containing
volume and a release boundary; a metering interaction that admits one item and
blocks the next *in the same operation* — i.e. two blocking relations whose states
alternate; an actuation reaching the metering element from outside; a refill path
that does not pass through the fixing; a load path from the stored items to the
wall; and an explicit statement that "does not jam when nearly empty" depends on
how loose items bear on one another — a contact question with no available route.
**Mechanism-independent:** escapement, single-item pocket, indexing rotor, gated
pair, metered aperture are all admissible.
**Obvious physical failure:** a single gate that opens a passage without a second
element restraining the following item — "exactly one" then rests on timing, not
on geometry.

### PRB-02 — desk-edge clamp for a monitor arm, 18–40 mm, tool-free removal
**`latch-retention` applies directly.** Its capability statement — hold two bodies
in a defined relative state against a disturbance, release by a deliberate action,
repeatably — is this probe verbatim, with two distinguishing features: one
participating body is **external and not designed** (the desk), and its thickness
is a **band**, not a value. `rotary-to-linear-engagement` applies *if* the design
uses a screw, and is free.
**Facts a design should establish:** a clamping interaction with identified
participating regions on the product **and** on the external body; a declared
disturbance (the arm's weight and its moment) with a load path to the desk;
restraint of **both** slip along the edge and rotation about it — two distinct
constrained freedoms, not one; an actuation reachable without tools; and the range
18–40 mm expressed as a *travel* the mechanism must cover, not a fixed dimension.
**The micro-oracle's sharpest invariant transfers:** `NRM-LR-004` — the release
action must be **distinguishable from the disturbance**. If tool-free release is
indistinguishable from the load, the load releases it.
**Obvious physical failure:** friction-only retention with no declared friction
assumption, or a clamp whose grip is stated for one thickness and asserted across
the band.

### PRB-03 — foot pedal, press → signal, self-return, no sideways movement
**Partial applicability.** `bounded-two-state-closure` covers the two defined
states (rest and pressed) and the requirement that each extreme be physically
produced. `guided-slider` covers the constrained lateral freedom *if* the pedal
translates; for a pivoting pedal only its principle transfers — constrain the
freedoms the motion requirement depends on, and no others.
**No micro-oracle covers self-return.** Restoring to a rest position without user
input is a state-maintenance behaviour of the kind BM-003 classifies, and no
micro-oracle states it.
**Facts a design should establish:** two states with a realized determinant at
each; a return effect declared as a *principle* (elastic, gravitational,
over-centre) with the region that provides it identified; a **declared forbidden
lateral freedom** with a named blocker and direction — the source states it
explicitly, so it is a requirement, not an inference; the signal boundary as the
edge of mechanical scope, recorded rather than mechanised; and a load path from the
foot to the bench.
**Obvious physical failure:** a rest position produced only by a modelled joint
limit; or lateral restraint asserted by a joint type with no engagement geometry.

---

## 7. Cross-case engineering invariants useful for P4A

Each holds across at least two cases and names no mechanism.

1. **A label is not a realization.** A joint type, an interaction kind or a
   retention relation with no engagement geometry on the participating bodies
   discharges nothing. (`NRM-BM-001-002`, `-006`; `NRM-BM-002-003`;
   `NRM-BM-003-016`.)
2. **Engagement is localized and two-sided.** Participating geometry is identified
   on *each* body — or, for a monolithic compliant realization, the compliant
   region and its adjacent functional regions are identified.
3. **A blocking claim needs a direction and a blocker.** Retention without an
   identified escape direction cannot be tested; without a named blocker it passes
   when an unrelated body happens to be in the way. One feature per blocked
   direction (G3 shows two).
4. **Paths, not endpoints.** Connectedness, retention, captivity and interference
   are evaluated at declared interior samples. Endpoint-only evidence is the most
   effective way to make an unbuildable mechanism look correct.
5. **Declared contact is not interference; undeclared overlap always is.** Zero
   clearance at a declared contact is correct. Overlap outside declared contact,
   interference-fit and compliant regions is a failure at any tolerance.
6. **Material is conserved across states.** A shape change is a declared compliant
   deformation or it is a defect.
7. **A declared terminal state needs a realized determinant, evaluated at its own
   configuration** — and a design that declares no physical end of travel owes
   none (G10).
8. **Assembly is evaluated in the configuration the preceding steps produce**, and
   the dependency relation is acyclic. Retention terminates by one of three
   strategies — a later body, a rotation, or elasticity (G16 shows rotation ×5;
   G5–G6 elasticity; BM-002's rear panel a later body).
9. **Existence of a load path is structural; its adequacy is quantitative.** A
   missing magnitude never makes the structural predicate underivable.
10. **Which components an element carries depends on the conversion family
    selected, not on the requirement.** No element acquires a reaction obligation
    from its type.
11. **Capability absence is UNSUPPORTED, never INFEASIBLE.**
12. **A model that imposes the relation by declaration cannot evidence the
    engagement.** Nor can rigid geometry evidence a deformation-resolved path, nor
    a zero-friction model a friction-dependent retention.

---

## 8. Freedoms that forbid answer-similarity scoring

Recorded so P4A cannot drift into comparing outputs to the references.

- **Mechanism family is free in all three cases** — closure and retention (BM-001),
  rotary-to-linear conversion and guidance (BM-002), locking and joint type
  (BM-003). BM-001 has **two accepted references with different joint types, body
  counts, retention principles and assembly processes** (G1 vs G5). Either is a
  correct answer; neither is the answer.
- **Body count is free everywhere.** BM-003 states it explicitly: "three legs" is a
  count of *supports*, not of bodies.
- **All dimensions are free in BM-001 and BM-003.** BM-003's source contains no
  digit, and its freedoms forbid any predicate comparing a dimension to a
  threshold. Only BM-002 supplies numbers — a travel band and a payload — both
  qualified "approximately", with the qualifier preserved.
- **Motion type is free** (BM-001 admits rotation, translation, compound and
  detachment); **whether the closure stays attached at open** is free; **whether
  the open state is a pose or a region** is free.
- **Anti-rotation is not universally required** (BM-002); **springs, detents,
  collars, rings and over-centre geometry are neither required nor forbidden**
  (BM-003); **whether physical ends of travel exist at all** is free (BM-002).
- **The state-maintenance principle is free** (BM-003), and three of its four
  classes have no available evidence route — so `NOT_VERIFIED` on persistence is
  the honest and correct outcome, not a deficiency.

---

## 9. Reference limitations — what this material does not establish

- **No Oracle pack is CAD-validated.** Every product pack carries
  `physical_validation: PENDING_CAD` and `pack_status:
  PRE_CAD_SEMANTIC_REVIEWED`, described in its own text as "a semantic status
  only … NOT lock-ready, NOT CAD-validated and NOT production authority".
- **The CAD references state their own limits on the images.** BM-002's sections
  carry "CAD geometry only. Structural strength, user effort, jamming, safety and
  manufacture are NOT VERIFIED"; its assembly frames carry "INSERTION FORCE NOT
  VERIFIED. No contact and no force is simulated"; BM-003's blocker views carry
  "CUTAWAY FOR DISPLAY ONLY" and point to JSON for every number.
- **No force, strain, friction, wear, fatigue, tolerance or manufacturability
  result exists** for any case. Every such requirement resolves to `UNSUPPORTED`
  or `NOT_VERIFIED` by construction of the evidence scope.
- **Images show arrangement, not behaviour.** An exterior or exploded view proves
  nothing about hidden geometry; the exploded view explicitly is *not* an assembly
  path; captivity, clearance and interference numbers all live in validation JSON
  that this package deliberately did not read.
- **PRB-01's central capability has no authoritative reference**, and PRB-03's
  self-return has none. Neither gap was filled by invention.
- **These are engineering bars, not answers.** Nothing here may be used to score a
  pipeline output on resemblance.

---

## 10. Checklist to carry into P4A

Mechanism-independent. None reproduces a reference design.

**Topology and realization**
1. Is every required motion supported by a physically coherent joint chain that is
   connected end to end, with each link naming its participating bodies?
2. Does every declared joint, interface and retention relation have identified
   participating geometry on **each** participant — or, for a single-body
   realization, an identified compliant region?
3. Is every region where two bodies meet classified?

**Distinctness and non-degeneracy**
4. Are joints the mechanism requires to be distinct actually at distinct
   locations, and are link lengths and radii distinct non-zero values?
5. Where a member is repeated, is each instance individually identified,
   individually retained, and consistently arranged?
6. Do bodies the topology connects actually meet where it says they do?

**Mobility, blocking and release**
7. For every DOF the design says is not intended: is there a named blocker, a named
   blocked direction, and a way to defeat it for testing — or a declared class that
   keeps the product out of it?
8. Is a retained state maintained by an identifiable physical interaction rather
   than by an assertion or a joint limit?
9. Is the released state **geometrically different** from the retained state, and
   does the difference follow from a deliberate action on a real body?
10. Can the retained state be re-entered, with every participating feature still
    present?

**Guidance and spatial realization**
11. Does the declared guidance constrain the freedoms the motion depends on
    without removing the motion itself — and is it evidenced at an interior
    configuration, not only at the ends?
12. Does the S04 spatial realization actually close the S03 topology: every body
    placed, every joint located, every declared region given a volume?
13. Are paths evaluated at declared interior samples, and is any overlap either
    inside a declared interaction region or reported as a defect?
14. Where a terminal state is declared as a physical end, is a realized
    determinant named — and where none is declared, is that stated rather than
    silently missing?

**Load, assembly, honesty**
15. Is there a load path from each declared applied load to a reaction site, with
    each hop naming the interface that carries it?
16. Does each assembly step name a body, a direction and the relationships it
    activates, evaluated against the configuration the preceding steps produce,
    with an acyclic order and a retention-termination strategy per retained body?
17. Are quantities the source did not supply left `UNSUPPORTED` rather than
    invented — and are structural predicates still evaluated despite them?
18. Is a capability the toolchain lacks reported as unsupported rather than as a
    property of the design?

---

*Package 3 complete. Twelve reference files read start to end. **Visual
inspection closed at 99 of 99 assigned images — 73/73 mandatory and 25/25
representative across all four executable references; outstanding: 0.** Every
image was opened; none was excluded on the basis of its filename. One visual
conflict remains unresolved (§0.3) and is carried into P4B. No experiment was run
and nothing in the repository was modified.*
