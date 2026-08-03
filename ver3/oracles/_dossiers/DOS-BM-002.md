# Dossier BM-002 — FROZEN

## S1. Direct source requirements (rank 1)
Locator: `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-002_requirementspec.json`. Product doc:
`/home/ftk3187/github/ASSY_Ver2.0/BM-002_ENCLOSED_HAND_CRANKED_PLATFORM_LIFT.md`.
`product_intent`: "A compact desktop platform-lifting device that enables manual lifting and lowering of a platform within a housing through external hand crank rotation while maintaining enclosed operation."

| ID | kind | statement (verbatim) | verification.kind | observable (verbatim) |
|---|---|---|---|---|
| REQ-001 | functional | The device must enable a user to rotate an external hand crank to raise and lower an internal platform | demonstration | platform movement in response to hand crank rotation |
| REQ-002 | performance | The platform must move approximately 80-100 mm during operation | measurement | platform vertical displacement |
| REQ-003 | performance | The platform must support a payload of approximately 1 kg | measurement | maximum supported payload |
| REQ-004 | functional | The mechanism must remain enclosed within the housing during normal operation | inspection | housing integrity during operation |
| REQ-005 | safety | The product must be safe to use | inspection | safety features compliance |
| REQ-006 | manufacturing | The product must be mechanically plausible, easy to assemble, and practical to manufacture | inspection | design feasibility for manufacturing |
| REQ-007 | performance | The product must avoid obvious jamming or unstable operation | demonstration | smooth operation without jamming or instability |
| REQ-008 | usability | The product must be desktop-sized | measurement | product dimensions |
| REQ-009 | functional | The product must operate manually only | inspection | absence of power source |

## S2. Quantities that ARE stated (unusually, unlike BM-001)
- Travel: **approximately 80-100 mm** (REQ-002), unit mm, observable "platform vertical displacement".
- Payload: **approximately 1 kg** (REQ-003), observable "maximum supported payload".
- Both are qualified "approximately"; no tolerance is given for the qualifier.

## S3. Missing criteria and quantities
- No crank torque, effort or speed.
- No jamming criterion, no stability metric, no efficiency target.
- No definition of "safe to use"; no standard cited.
- No desktop envelope numbers (REQ-008 says "desktop-sized" only).
- No transmission type, ratio, or self-locking requirement.
- No statement of platform guidance method or anti-rotation.
- No statement of where the crank crosses the housing, or on which face.
- No statement of how a payload is placed on or removed from the platform.
- No service or maintenance access requirement.
- No duty cycle or life.

## S4. Source conflicts / ambiguities — **AMB-002-01, recorded not resolved**
REQ-004 requires the mechanism to "remain enclosed within the housing during
normal operation", while REQ-001 requires an **external** hand crank. The
boundary must therefore be crossed by the drive. The source does not state
whether the crank shaft, its seal/bushing, or the crank handle counts as part of
"the mechanism". Whether a rotating element penetrating the housing violates
REQ-004 is not determinable from rank-1 sources.

**AMB-002-02:** "approximately 80-100 mm" is itself a range with an
"approximately" qualifier. Whether 78 mm or 104 mm complies is undetermined.

## S5. Evidence available, with fidelity
| Evidence | Path | Fidelity | What it is |
|---|---|---|---|
| Crank lift, hold under load | `/home/ftk3187/github/ASSY_Ver1.0/m13_hard_anchor/out/t2_hard_verdict.json` | **V-A declared pairs** | `decision_row` = "m13 Hard anchor - P-SLIDE V-A + P-GEAR V-A (declared pairs)"; 5/5 seeds |
| Hold-drift (pawl) | `/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/benchmark.py:138` | reused, analytic | "m13 P-FULL hold-drop 3.37 mm <= 5 mm (pawl)" |
| Rack-pinion card certification | `/home/ftk3187/github/ASSY_Ver1.0/m11_rack_pinion/REVIEW.md:1-6` | **V-A 5/5**; "**V-B is NAMED-DEFERRED**, not silently dropped" | gear mesh never contact-verified |
| Lead-screw milestone | `/home/ftk3187/github/ASSY_Ver1.0/m19_lead_screw/`, `/home/ftk3187/github/ASSY_Ver1.0/knowledge/cards/lead_screw.py` | card exists | an alternative conversion exists in the legacy library |
| Angled screw lift | `/home/ftk3187/github/ASSY_Ver1.0/m27_angled_screw_lift/` | milestone | another conversion topology |

### E1. Limitation
All lift kinematic evidence is **V-A declared-pair**. Under declared coupling the
transmission ratio is exact by construction and contact-level behaviour
(backlash, tooth/thread engagement, friction, efficiency, jamming) is **not**
observed. REQ-007 ("avoid obvious jamming") cannot be supported by V-A evidence.

### E2. Limitation
`/home/ftk3187/github/ASSY_Ver1.0/m11_rack_pinion/REVIEW.md` explicitly records V-B as deferred. Any claim
requiring contact physics for the conversion is out of scope of this evidence.

## S6. Decisions made only by legacy reference realizations
`/home/ftk3187/github/ASSY_Ver1.0/tasks/build_goldens.py:1142 anchor_hard(variant="lift")` fixes: two floor
rails at +/- rail_gap/2 (80 mm); rack-pinion transmission with m=5, z=12; seat at
(76, 60, 30); stroke scaled to 120 mm; cabinet 200x140x90; wall 4 mm. **None
appears in any BM-002 requirement.** Its own docstring states the drawer variant's
rack-pinion is "over-engineered" while the lift's is "FUNCTIONALLY NECESSARY".

## S7. Legacy behaviour that must not define correctness
`/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/benchmark.py:145-150` C5-lift-nogear -> INFEASIBLE with
`KG_NO_PERMITTED_REALIZER` because "the ONLY card is rack_pinion". A hand-cranked
lift without gear or ratchet is realizable; this verdict is a library gap
reported as physics. Plus DOS-BM-001 S7 items.
