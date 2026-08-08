# Pipeline geometry and information plan — Stages 01–07

**Scope.** What each Stage must decide and output so that the next Stage can
proceed without re-reading the original request and without inventing missing
engineering content.

**Basis.** Reconstructed from the actual engineering work on BM-001, BM-002 and
BM-003 — the Oracle packs, the executable CAD references, the simulations, the
motion/contact/assembly checks, the negative controls, the human CAD review
decisions and the validator defect records. Not from the Stage documents alone.

**A framing fact that must be stated first.** `ver3/benchmarks/*/runs/` and
`ver3/benchmarks/*/evaluations/` are empty. `ver3/assy_v3/` contains provider
interfaces that raise `NotImplementedError` and nothing else. **No stage has ever
run.** Every piece of engineering content for all three benchmarks was produced
by hand. That is not a gap in the evidence — it is the best possible evidence,
because the manual process had to make every decision the pipeline will have to
make, and it recorded, in `DESIGN_AND_OPERATION_RATIONALE.md`, `CHG-*`, `DEF-*`,
`R1–R8` and `HUMAN_CAD_REVIEW_DECISIONS.yaml`, exactly where it had to invent and
exactly what it discovered too late. This document is the analysis of that record.

**Nothing here is implemented.** No code was modified in producing it.

---

## 1. Cross-benchmark retrospective

### 1.1 BM-001 — desktop storage box with a reusable latch

**What the user required** (`ver3/benchmarks/BM-001/source/request.txt`, four
sentences): a compact desktop storage box with a reusable latch; opens and closes
repeatedly; no accidental opening in normal handling; easy for a user to operate;
secure during transport; low-cost manufacturing; desktop-practical; mechanically
plausible; easy to assemble.

**What the Oracle produced:** 13 invariants, 9 unresolved items, 13 freedoms, 7
admissible / 12 inadmissible physical fixtures, 22 negative cases. The invariants
are deliberately mechanism-neutral: NRM-BM-001-001 asks for two states and a
motion connecting them, not a hinge; NRM-BM-001-006 asks for a retention
function, not a latch geometry.

**What was missing, or present only as prose.** Every quantity. "Reusable",
"easy to operate", "secure during transport" and "accidental opening" carry no
force, no disturbance magnitude and no cycle count. The Oracle correctly refused
to invent them, so nothing downstream could compare anything against anything.

**What CAD had to invent.** Effectively the entire product:

- **Closure motion type.** Not stated. Two references were built with different
  answers — EXE-BM001-01 revolute about a rear axis, EXE-BM001-02 prismatic in
  two side channels. `REFERENCE_SELECTION.yaml` records this as a deliberate
  topology difference, "not a cosmetic variation… they differ in the joint type,
  the number of bodies, the retention principle and the assembly process."
- **Whether a carrier body exists at all.** `BODY-PIN` in -01; no third body in
  -02, where the rails are integral to the enclosure.
- **The retention principle.** `REFERENCE_SELECTION.yaml` says of -01: "It adds a
  retention mechanism, which ADM-BM-001-E does not specify and NRM-BM-001-006
  requires; a rigid sliding bolt was chosen so retention adds no force-adequacy
  dependence." The retention principle was chosen *by the CAD author*, and chosen
  *for the convenience of the evidence route*.
- **The open-state determinant.** Both references declare a DISCRETE terminal
  pose and had to invent the feature that produces it — a flange meeting the rear
  wall in -01, a boss meeting the channel end in -02.
- **The usable access region.** 84 mm declared usable from a 90 mm aperture. No
  source number exists; the human then froze it (HCR-BM001-003: "must not be
  narrowed to make the revised geometry easier").
- **Material classes and every compliant region.** `parameters.yaml` declares
  `BODY-COVER: GENERIC_COMPLIANT_POLYMER` and four compliant regions with
  `deflection_mm: 2.2` and a named direction, active only during `ASM-02` and
  declared service disassembly. Not one of those numbers is traceable to
  anything.

**What validation discovered too late.** All of it came from *human* review, not
from the checks:

| finding | what it was |
|---|---|
| HCR-BM001-002 | the hinge pin was retained in **one direction only**; the far end could walk out |
| HCR-BM001-004 | the cover was **liftable at full open** — captivity had been checked, but not across the whole travel |
| HCR-BM001-006 | the quarter-turn cam had **nothing holding its locked orientation** |
| HCR-BM001-005/008 | retention was implemented as a whole extra body plus knob, shaft, guide boss, enclosure socket and an extra assembly step — **disproportionate to its function** |
| HCR-BM001-008 | claim vocabulary drift: it was being described as a key/lock. "it is a latch, not a lock; do not imply authorized access" |

Two of these — 002 and 004 — had been *recorded as accepted limitations* in
`manifest.yaml` (LIM-01) before the human rejected them. The pipeline's own
machinery had classified a real defect as a declared limitation.

One further discovery came from the geometry itself, and is the most instructive:
a latch finger on the centreline "retracts *into the aperture* at full open and
stands in the way of the 84 mm the design promises." A **feature placement**
conflicted with a **declared functional region**. Nothing in the process related
those two facts until the solid existed.

**Compliant-force calculation: never performed.** This is the single largest
capability gap. Snap insertion force, retention strength, release effort, strain,
root stress, creep, fatigue, cycle life, wear, tolerance capability, moulding
feasibility and cost are all `NOT_VERIFIED` in both references, deliberately. The
simulation (`simulate_lid.py`) produces a hinge-effort curve only, on declared
density 1200 kg/m³, **zero friction** ("these curves are a lower bound on the
effort a real hinge would need, not a prediction of it") and an invented
minimum-jerk actuation profile.

**Benchmark-specific vs general.** Benchmark-specific: the aperture, the 84 mm,
the latch. General: every row of the table above.

### 1.2 BM-002 — enclosed crank-driven platform lift

**What the user required:** compact desktop platform lift enclosed in a housing;
external hand crank; platform rises and falls; **approximately 80–100 mm** of
travel; **approximately 1 kg** payload; mechanism enclosed during normal
operation; safe, mechanically plausible, easy to assemble, practical to
manufacture; avoid obvious jamming or unstable operation.

This is the only benchmark whose source contains numbers, and it is instructive
that only two of the fourteen invariants can use them.

**What CAD had to invent.** The mechanism family (in-line slider-crank), the
crank radius (R = 45 → travel exactly 2R = 90, "10 mm clear of both edges" of the
source band), the rod length (85), seven bodies, the guide channels and
followers, two journal lands separated by a relief, the rear panel's triple role,
and the overhung crank.

**What was discovered too late — the three `CHG` records.** These are the
sharpest evidence in the repository.

- **CHG-01 — crank axis height 55.0 → 60.0.** The crank arm must carry material
  around the crank pin bore: Ø10 pin plus a 4 mm wall gives a boss radius of
  9.000, so the arm's outer radius is 45 + 9 = 54.000. At `crank_axis_z = 55.0`
  the arm's lowest point at bottom dead centre is z = 1.000 and the floor top is
  z = 4.000. Measured interference: **278.7734 mm³**. *A layout dimension was
  fixed before the feature envelope that constrains it existed.* Note also what
  was explicitly refused: "The alternative was to raise `overlap_tol_mm3` above
  278.77… The first would have blinded the check that found this (and every
  other) interference."
- **CHG-02 — the second journal cannot live on the rear panel.** The provisional
  layout said it did. It cannot: the connecting rod **occupies the crank axis** —
  measured 64.0000 mm³ of rod inside a 4×4×4 probe centred on the axis, minimum
  distance from rod to axis line 0.0000. The two-web alternative also fails,
  because in the crank's rotating frame the rod sweeps through the axis, so
  `BODY-CRANK-SHAFT` would be two disconnected solids. *A support assignment made
  on topology alone was geometrically impossible, and only a swept-volume check
  could show it.*
- **CHG-03 — platform plate and rim heights.** Driven by the clevis offset, which
  is driven by the rod eye radius (9.5) plus the lug radius (11.0). Same class as
  CHG-01.

**The assembly path set a primary dimension.** "The **unusual choice** here is
that the hub diameter is the journal diameter. That is what makes the product
assemblable at all." The crank must be inserted from +X because the arm
(radius 54) cannot pass a 35.2-radius bore; inserting from +X means the handle
must pass through the whole bore; so the handle envelope must fit inside the
journal. Ø70 hub with a grip at radius 26 works; a small shaft with a big crank
does not. **The assembly path is a design driver, not a check.**

**Validator defects found during validation — `DEF-01/02/03`.** "Recorded because
a validator that never caught anything is not evidence that the design is right."

- DEF-01: the boundary-crossing control truncated the hub but left the handle
  outside, so 3166.7 mm³ still sat outside and the control did not register.
- DEF-02: the pitch/roll control removed the followers but left the plate edges
  0.400 from the guide bosses, so a 4° rotation still fouled them and "escape"
  was never achieved.
- DEF-03: guide engagement was measured from the **platform's** bounding box,
  which reaches 5 mm below the channel because the clevis hangs there. The check
  reported the followers leaving the channel at every sample when they never do.

Two weak controls and one measurement taken on the wrong entity. None was a CAD
change.

**The retention criterion had to be made two-part.** "the travel must be small
*and* the body that stops it must be the declared retention body. A pin that is
eventually stopped by some unrelated boss it happens to run into is not
retained." NC-07 removes the head; the pin is still stopped at 4 mm by the
housing journal boss, "and the control is detected precisely because the blocker
is wrong."

**What the simulation had to invent.** Densities (1200 polymer-like / 7850
metal-like), actuator gains (`kp=1500, kv=3`, after a first attempt at
`kp=4000, kv=200` for which "`kv*dt/I` = 77 and the integrator diverged on the
first step"), timestep, integrator, solver iterations and tolerance, zero joint
damping and friction, and — most importantly — **the entire multibody topology
mapping**: which CAD bodies become MuJoCo bodies, which pins are welded into
their parents, and how the closed loop is closed (`equality connect` between rod
and platform, "3 joint DOF minus 2 independent constraint rows in the plane = 1
net DOF"). The CAD declares interaction *kinds*; it does not carry a
simulation-ready joint graph, so the simulation re-derived one.

**Force and back-drive behaviour** exist only inside an ideal-joint, zero-friction
rigid-body model. NRM-BM-002-014 and NEG-BM-002-011 exist to stop that model
being cited for jamming; REQ-003 payload capacity is `UNSUPPORTED`; REQ-007
jamming is `NOT_VERIFIED`. The only robust dynamic result is the *difference*
between the payload and empty runs, which is independent of the invented
densities.

### 1.3 BM-003 — compact folding desk stand

**What the user required:** three legs folding close to the body; everything stays
attached while folded; nothing removed to fold; open by hand in a sequence that
makes sense; legs spread apart to give a usable footprint; nothing comes apart
while opening; no tools or motor; stays open on its own; legs must not fold back,
twist aside or come off; nothing turns on its own or moves in an unexpected
direction; **something deliberate** before it can fold again; folds back to the
same compact shape; repeatable; holds a small object; buildable and assemblable
in a sensible order.

**The source contains no digit.** FRE-BM-003-011 makes every dimension free. The
Oracle has 18 invariants, 13 freedoms, 10 ambiguities, 19 negative cases and four
state-maintenance classes of which only one has an available evidence route.

**What CAD had to invent.** Everything metric, plus: the body and joint topology
(10 bodies, 3 revolutes, 1 cylindrical); the locking principle (heel under a ring
arm); the two-motion release; the anti-rotation ribs and keyways; bayonet
retention on three pins, the ring captor and the top support; the outward stop
pads; the declared forbidden-mobility set; and a fixture-declared numeric bound
`outward_travel_max_deg = 3.0` which exists only because a predicate could not
otherwise discriminate.

**What was discovered too late — `R1–R8`.**

| id | discovery | class |
|---|---|---|
| R1 | the hub built as **seven disconnected solids** — the clevis plates missed the base-flange chord at their own y | B-rep validity, invisible symbolically |
| R2 | **nothing stopped a leg swinging past deployed.** The forbidden set was incomplete | forbidden-set incompleteness |
| R3 | the outward stop pad sat **inside the leg's hinge eye**. Diagnosed from the *signature*: 86.81988311 mm³ identical at every leg angle ⇒ the overlap is invariant under rotation about the hinge axis | layout dimension vs feature envelope |
| R4 | hinge capture took **three topologies**; a straight-insertion clip chain does not terminate, and a blind-bore-plus-head pin cannot be assembled | assembly/retention theorem, below |
| R5 | **the turn silently stopped being necessary.** Shortening the arms in R1 let the rising heel clear the arm's outer edge, because the heel moves outward as it rises. A functional property was destroyed as a side effect of a dimension change two revisions earlier | missing invalidation cone |
| R6 | the ring seat had to be **derived** from the heel's actual position, not chosen independently | derived-value ownership |
| R7 | **assembly must end DEPLOYED** — the ring cannot be seated over raised heels | assembly as design driver |
| R8 | two *checker* defects: connectivity treated a limit stop as a running pair; the outward-stop predicate did not discriminate because the base flange was an **accidental** stop | control adequacy |

**Two further process failures, in this session.**

- `poses.yaml` **does not parse** (`ParserError` at line 96) and nothing noticed,
  because no machine consumer reads it — `valcore` reads `assembly.yaml` and
  `interactions.yaml`, and the pose law lives in `build.py`.
- The full-sampling validation never completed, and an artifact directory ended
  up holding a fast-run `SUMMARY.json` beside full-run motion reports. This is
  the same failure `manifest_util`'s docstring says already happened once on
  BM-002.

**A reusable theorem, derived here and confirmed retrospectively on the other
two.** *A rigid part installed by a single straight translation always leaves the
reverse direction open. Retention therefore requires one of exactly three things:
(a) a later body that covers it, (b) a rotation — bayonet or twist, or (c)
elasticity.* BM-003 uses (b) five times; BM-002 uses (a) — the rear panel's two
lands "come into position in the same −X motion that seats the panel. Before that
motion both pins can be pushed out; after it neither can"; BM-001 uses (c) — the
snap barb and the four deflected tabs. This is a Stage 03 planning rule, not a
Stage 09 discovery.

---

## 2. Late-discovered or manually invented information

Consolidated. **Invented** means no source, no Oracle and no upstream artifact
supplied it, so a human chose it. **Late** means the pipeline as designed would
not have surfaced it before CAD or human review.

### 2.1 Invented by CAD

| information | BM-001 | BM-002 | BM-003 |
|---|---|---|---|
| mechanism family / joint type | revolute *and* prismatic (two references) | in-line slider-crank | 3 revolutes + 1 cylindrical |
| body count and split | 3 / 2 | 7 | 10 |
| existence of a carrier body | `BODY-PIN` or none | two pins | three pins |
| retention principle | bolt → snap latch; snap barb | rear-panel lands | five bayonets |
| retention **direction** completeness | missed | made two-part after NC-07 | missed until R2 |
| anti-rotation | missed on the cam | platform yaw probes | ribs+keyways, invented |
| terminal/limit pose producer | flange / boss | dead centres + guides | ring arm + stop pad |
| declared usable region | 84 mm of 90 | payload envelope 36×60×40 | platform top face |
| every clearance | 0.2 / 0.4 / 0.6 | 0.1 / 0.2 / 0.4 / 3.2 | 0.15 / 0.2 / 0.3 / 0.4 / 0.5 / 1.0 |
| material class | 2 classes | implied by density | not modelled |
| compliant region + deflection | 2.2 mm, named direction | none by design | none by design |
| assembly order and directions | 1 press | 9 steps, 2 forced | 15 steps, 5 turns |

### 2.2 Invented by simulation

Densities; friction (set to zero in both, with the consequence declared);
actuation profile; gravity and orientation; solver timestep, integrator,
iterations and tolerance; actuator gains (BM-002's first choice diverged); and
the multibody topology mapping including weld choices and loop closure.

**None of these has an owning Stage today.** `Parameter` is owned by s05 and
extended by s06, but a *simulation assumption* is not a design parameter — it is
an evidence-route input. The current DesignState has `Assumption` (any stage),
which is where they belong, but nothing requires s08 to enumerate them before
s09 runs.

### 2.3 Discovered too late

| discovery | earliest stage that *could* have caught it | stage that actually caught it |
|---|---|---|
| BM-001 one-direction pin retention | S03 (relation has a direction field) | human review |
| BM-001 cover liftable at full open | S04 (captivity over the whole path) | human review |
| BM-001 cam orientation unconstrained | S03 (DOF enumeration) | human review |
| BM-001 latch finger blocks the aperture | S04 (feature vs declared region) | CAD |
| BM-002 CHG-01 arm into floor | S05→S06 iteration | CAD |
| BM-002 CHG-02 journal on rear panel | S04 (swept occupancy of the axis) | CAD |
| BM-002 CHG-03 clevis offset | S05→S06 iteration | CAD |
| BM-002 hub Ø = journal Ø | S03/S04 (assembly path as driver) | CAD |
| BM-002 DEF-01/02/03 | S08 (control and observable design) | S09 |
| BM-003 R1 disconnected hub | S07 (validity) — genuinely not earlier | S07 |
| BM-003 R2 no outward stop | S03 (total DOF disposition) | CAD |
| BM-003 R3 pad in the eye | S05→S06 iteration | S09 |
| BM-003 R5 lost lift-only property | invalidation cone on a parameter change | S09 |
| BM-003 R8 accidental blocker | S08 (control must name the blocker) | S09 |

The column that matters is the second one. **Only one of these fourteen is
genuinely a CAD-stage discovery** (R1, B-rep connectivity). Everything else was
knowable earlier, from information the pipeline is already supposed to hold.

---

## 3. Repeated general failure patterns

Twelve patterns, each observed on **at least two** benchmarks. These are the
requirements the revised contracts have to satisfy.

**P-1 — Retention and blocking are recorded as facts, not as (direction, blocker,
feature-pair).**
BM-001 pin, cover and cam; BM-002's two-part criterion added only after NC-07;
BM-003 NC-17. *Fix:* a `BlockingRelation` is (retained body, blocked direction in
a named frame, blocker body, feature on each, engagement measure, states in which
it holds). Any missing field is `REPRESENTATION_INCOMPLETE`, never a pass.

**P-2 — The forbidden-mobility set is incomplete and nothing forces enumeration.**
BM-001 open-state captivity and cam orientation; BM-003 outward over-swing.
MOB-BM-003-004 already says unintended-DOF checking "is only meaningful against a
DECLARED forbidden set… without one it degenerates into 'nothing obviously
moved'". *Fix:* per body, per state, the disposition of **every** rigid-body DOF
must be a total function into
`{INTENDED, BLOCKED_BY(relation), MAINTAINED_BY_CLASS(c), IRRELEVANT_BECAUSE(r)}`.
Totality is what makes omission detectable.

**P-3 — Layout dimensions are fixed before the feature envelopes that constrain
them exist.**
BM-002 CHG-01 and CHG-03; BM-003 R3 and R6; BM-001's rail/tab pair. *Fix:*
features that generate envelope constraints must emit them as `Constraint`
entities that bind layout parameters, and S05↔S06 must iterate under a bound.

**P-4 — A support, reaction or interface assignment made on topology alone can be
geometrically impossible.**
BM-002 CHG-02 (canonical); BM-003 R7. *Fix:* every interface assignment carries
an occupancy obligation checked against the swept volumes of all bodies over all
states — which requires kinematic geometry (level G4), not topology (G1).

**P-5 — Negative controls that cannot fire, because the defeat is not the
mechanism.**
BM-002 DEF-01 and DEF-02; BM-003 NC-17. *Fix:* a control is authored from the
declared relation — remove exactly the named blocker's named feature, nothing
else — and must additionally assert that any surviving stop names a **different
blocker**. A control that only changes a number has not been shown to fire.

**P-6 — Evidence-route capability silently selects the mechanism.**
BM-001 rejected four admissible fixtures because their primary geometry needs
strain, friction or hoop-stress answers the toolchain cannot give; BM-002 chose a
design with no press, snap or interference fit anywhere; BM-003 declared
`SMC-KINEMATIC_BLOCK` because it is the only class with a route. Each decision is
defensible and each was recorded — but the aggregate effect is that **the Oracle's
permissiveness has never been tested**, and every reference sets
`cross_principle_permissiveness_validated: false`. *Fix:* make it a first-class
`EvidenceRouteDecision` with an owner, and make the resulting coverage gap a
required output rather than a footnote.

**P-7 — Declarations with no machine consumer drift and rot.**
BM-003 `poses.yaml` does not parse and nothing noticed. *Fix:* every structured
output names its consumer, or is explicitly marked
`NON_AUTHORITATIVE_NARRATIVE`.

**P-8 — Measurements taken on the wrong entity.**
BM-002 DEF-03 (platform box vs follower), BM-002 §8 (support surface would have
been 4 mm wrong from the box top), BM-003 station-B/C ROI hulls. *Fix:* every
measurement names the **feature** it is taken on. Feature identity is an S05
deliverable that S09 must consume, and a measurement whose subject is a whole
body must say so.

**P-9 — Terminal and limit poses asserted rather than produced.**
NRM-BM-001-005/012 and NRM-BM-002-009 exist for exactly this. All three
references had to add a producing feature. *Fix:* a declared limit without a
producing feature pair is `REPRESENTATION_INCOMPLETE`.

**P-10 — Claim vocabulary drifts beyond the evidence.**
BM-001 "key"/"lock" (HCR-BM001-008); BM-003 claimed
`ONE_POSITIVE_EXECUTABLE_REFERENCE_VALIDATED` in `GOVERNANCE.yaml` and `README`
before any complete run existed, and had to be downgraded to `DEFERRED`. *Fix:*
claim strings are **generated** from evidence status, never authored.

**P-11 — Run and artifact identity is not enforced.**
BM-003's mixed directory; `manifest_util`'s docstring records the same failure on
BM-002 ("four artifacts then reached their final contents afterwards… the
manifest looked complete and four of its hashes were wrong"). *Fix:* every
artifact carries its run id; a manifest over a mixed set is refused.

**P-12 — The assembly path is treated as a check, when it is a design driver.**
BM-002 hub Ø = journal Ø; BM-003 R4 and R7; BM-001's single press with four tabs
deflected. *Fix:* assembly order, directions and the retention-termination
strategy (later body / rotation / elasticity) are decided **with** the topology
at S03 and proven at S04, not discovered at S09.

### 3.1 Relation to the Ver2 retirement matrix

BM-001/002/003 empirically **confirm** R-02–R-08 (qualitative geometry cannot
answer motion questions), R-09 (a block is not an embodiment), R-11 (face/opening
must come from access and assembly evidence — BM-002's forced insertion direction
is the proof), R-24 (CAD must not repair; the three `CHG` records are what
happens when CAD *reports* instead) and R-28 (field presence is not design — the
whole point of the `HCR` rejections).

They also expose **four failure classes the matrix does not cover**, all of which
are about *completeness of a relation set* rather than about representation type:
P-1 (direction and blocker identity), P-2 (DOF totality), P-6 (evidence-route
selection pressure) and P-12 (assembly as driver).

---

## 4. Geometry-maturity hierarchy

Ten levels. The question "when does geometry begin?" has no binary answer; the
useful question is *which level is owned where, and what can be checked at it*.

| level | name | owner | what exists | what is still unresolved | checks possible at this level | what the next level needs from it |
|---|---|---|---|---|---|---|
| **G0** | functional / body class | S02 | function decomposition; obligations; candidate families; body *hypotheses* with roles | how many bodies; any position; any joint | obligation coverage; candidate completeness at equal obligation coverage | a body hypothesis set with roles and the obligations each addresses |
| **G1** | product topology | S03 | bodies, joints (type + parent/child), interfaces with `interaction_kind`, DOF inventory, **forbidden-DOF disposition**, load-path ownership, assembly dependency graph | any metric value | graph acyclicity; DOF totality (P-2); every interface classified; every obligation has an owning body pair | a joint graph rich enough to build a multibody model, and a total DOF disposition |
| **G2** | symbolic spatial geometry | S03 | frames, axes as unit vectors in named frames, adjacency, directions, sidedness, declared functional regions (access, support, aperture) | magnitudes | axis/frame consistency; direction algebra (an escape direction is opposite a blocking direction); region-to-body assignment | named frames and axes that G3 can attach numbers to |
| **G3** | envelopes and poses | S04 | metric extents per body; metric pose per body per state; declared usable regions as metric volumes | internal features; exact surfaces | envelope non-overlap per state; region occupancy per state; reach/access at endpoints | poses that G4 can interpolate |
| **G4** | kinematic geometry | S04 | motion paths with declared sampling; swept volumes; assembly insertion sweeps; contact/engagement sites as sites, not surfaces | feature shape; fillets; wall thicknesses | interference along paths, not just endpoints; **swept occupancy** (catches BM-002 CHG-02); captivity over the whole travel (catches BM-001 HCR-004); assembly path feasibility (catches BM-002 hub Ø) | a proven-feasible kinematic skeleton, and the list of sites features must realize |
| **G5** | feature-level embodiment | S05 | named features on named bodies; each interaction realized by a feature pair; retention/limit/stop producers; compliant regions with mode and direction | numeric values of feature dimensions | every interaction has features on all participants (or a declared monolithic-compliant region); every limit has a producer (P-9); every blocking relation has a feature pair (P-1) | a complete feature graph and the constraints features impose on layout |
| **G6** | parameterized construction intent | S05 | construction program (ordered, total); parameters with units; constraints including **envelope constraints generated by features** | parameter values | program totality; unit presence; constraint parse; dependency-cycle detection among parameters | a solvable constraint system |
| **G7** | solved geometry | S06 | every parameter has a value or an explicit non-value status; residuals; active set; margins | whether the solids are valid | `feasible` / `infeasible` / `underdetermined` / `unsupported_formulation` / `solver_failure`; residual bounds | values for every symbol the program references |
| **G8** | CadQuery / B-rep geometry | S07 | compiled OCCT solids; geometry signature; native BREP then STEP exports with round-trip | whether it satisfies the predicates | validity, single-connected-solid (catches BM-003 R1), volume positivity, round-trip fidelity, determinism | signed solids plus the pose law |
| **G9** | verified geometry | S09 → S11 | measured predicate outcomes with declared fidelity and contact resolution | nothing geometric; only force/material/process | every declared predicate measured on its named feature; controls fired | evidence bound to plan items |

**Reading of the hierarchy against the failures.** BM-002 CHG-02 is a G4 check
performed at G8. BM-002 CHG-01/03 and BM-003 R3/R6 are G5→G6→G7 feedback
performed at G9. BM-001 HCR-002/004/006 and BM-003 R2 are G1 completeness checked
by a human. Only BM-003 R1 is genuinely a G8 discovery. **The pipeline's defect
is not that geometry starts too late — it is that checks are performed several
levels above where their information already exists.**

---

## 5. Revised Stage 01–07 contracts

Each brief answers: engineering question, decisions owned, decisions prohibited,
required inputs, structured outputs, geometry maturity, LLM role, knowledge-base
role, deterministic checks, next-stage consumer requirements.

These refine — they do not contradict — the frozen Oracle `stage_expectations`
and `STAGE_OWNERSHIP_MATRIX.yaml`.

---

### Stage 01 — requirement capture

**Engineering question.** *What did the user actually say, and what did they
leave open?*

**Owns.** `Requirement`, `SourceClause`, `Freedom`, `Ambiguity`, `Scenario`,
`Observable`, `Actor`, `SystemBoundary`.

**Prohibited.** Inventing a requirement; sharpening a qualifier ("approximately
300 mm" stays approximate); resolving an ambiguity; naming any mechanism,
material, part or dimension.

**Inputs.** Raw source text — **exclusively**, INV-002.

**Outputs.** Verbatim clauses with locators; typed requirements each naming its
verification kind and observable; the scenario set; the ambiguity set with
`block_scopes`; the freedom set. Plus one output the current contract lacks:
**a quantity inventory** — for each requirement, whether the source supplies a
magnitude, a band, a comparative, or nothing. BM-002 supplies two magnitudes;
BM-001 and BM-003 supply none, and every downstream stage needs to know that as a
fact rather than discovering it.

**Geometry maturity.** None. No frames, no bodies.

**LLM role.** Extraction and classification, with verbatim preservation. High
value, low risk — the failure mode is sharpening, which is checkable.

**Knowledge-base role.** None. A KB at S01 would import assumptions.

**Deterministic checks.** Every requirement resolves to a clause locator; no
numeral appears in a requirement that does not appear in its clause; ambiguity
`block_scopes` reference real outcome names; re-running on the same text is
byte-identical.

**Consumer test (S02 must be able to answer "what must physically be true?").**
S02 needs: the requirement set, the observables, the scenario set, and the
quantity inventory. It must **not** need the raw text.

---

### Stage 02 — obligation and candidate formation

**Engineering question.** *What must physically be true, and what families of
mechanism could make it true?*

**Owns.** `Obligation`, `Candidate`, `AcceptanceContract`, plus (new)
`PhysicalInteractionHypothesis` and `BodyHypothesis`.

**Prohibited.** Selecting a winner (INV-007); penalising a candidate for element
count or for needing realization (R-16); rejecting a candidate for absence of a
library entry — that is `UNSUPPORTED` (INV-011); any position, any dimension.

**Inputs.** S01 output only.

**Outputs.** Obligations traced to requirements; candidates as persisting
branches, each with the obligations it addresses and the obligations it
*creates*; body hypotheses with roles; the physical interactions each candidate
implies. Plus, from P-6: an **`EvidenceRouteDecision` per candidate** — which
evidence route would be needed to establish this candidate's primary function,
and whether that route exists in the toolchain. BM-001's four rejected fixtures
and BM-003's class choice are exactly this decision, made informally at CAD time.

**Geometry maturity.** G0. Body *classes* only.

**LLM role.** Highest of any stage — candidate generation is genuinely
open-ended, and BM-001 demonstrates that two materially different topologies both
satisfy the same Oracle.

**Knowledge-base role.** The micro-oracles are the KB: `guided-slider`,
`rotary-to-linear-engagement`, `latch-retention`. All three benchmarks decompose
into them — BM-001-02 is guided-slider + latch-retention; BM-002 is
rotary-to-linear + guided-slider; BM-003 is a guided-slider (the ring) +
latch-retention (five bayonets). A candidate should be expressible as a
composition of capability packs, and the KB's role is to supply, per capability,
the obligations it *creates* (P-12's retention-termination trichotomy is such an
entry).

**Deterministic checks.** Every obligation traces to a requirement; no candidate
carries a score; candidates are comparable only at equal obligation coverage;
every candidate's evidence route is classified.

**Consumer test (S03 must be able to answer "what are the bodies and joints?").**
S03 needs body hypotheses with roles, the interaction hypotheses, and the
obligations each must discharge.

---

### Stage 03 — embodiment topology *(the stage that must change most)*

**Engineering question.** *What are the bodies, how are they connected, what can
move, what must not, and in what order does it go together?*

**Owns.** `Body`, `Joint`, `Interface`, `Configuration`, `MobilityExpectation`,
plus three new families the failure record demands:
**`BlockingRelation`** (P-1), **`DOFDisposition`** (P-2) and
**`AssemblyPlan`** (P-12).

**Prohibited.** Any qualitative region used as a position (R-02/03/04); an
unclassified body-pair meeting region; a generic block as an embodiment (R-09);
any feature shape; any dimension; selecting a candidate before the S03/S04
feasibility gate.

**Inputs.** S02 output only.

**Outputs.**

1. **Bodies** with roles and instance identity.
2. **Joints** with type, parent/child, axis as a unit vector in a named frame,
   and parent/child frames — *rich enough to build a multibody model without
   re-derivation*. BM-002's simulation had to invent this mapping; it should be a
   projection.
3. **Interfaces**, every meeting region classified into one of the five
   `interaction_kind` values.
4. **`DOFDisposition` — a total function.** For every body, in every declared
   configuration, every rigid-body DOF is assigned
   `INTENDED | BLOCKED_BY(relation_id) | MAINTAINED_BY_CLASS(class_id) |
   IRRELEVANT_BECAUSE(reason)`. Totality is checkable. This single output would
   have caught BM-001 HCR-002, -004 and -006, and BM-003 R2.
5. **`BlockingRelation`** for every `BLOCKED_BY`: retained body, blocked
   direction, blocker body, and the *promise* of a feature on each (realized at
   S05).
6. **Load-path ownership** — for each interface that carries load, the path to a
   reaction site, as a graph over bodies.
7. **`AssemblyPlan`**: order, per-step insertion direction, the relationships each
   step activates, the dependency graph, and — new — the **retention-termination
   strategy** per retained body, from the trichotomy: later-body cover, rotation,
   or elasticity. BM-003 R4 burned three topologies discovering that this must be
   decided up front.
8. **Declared functional regions** as symbolic volumes: access region, support
   region, aperture, keep-out.

**Geometry maturity.** G1 and G2. Frames, axes, directions, sidedness — **this is
where geometry first appears**, and it is symbolic.

**LLM role.** High for topology proposal; **none** for DOF disposition totality,
which is enumeration and must be generated mechanically from the joint graph and
then dispositioned.

**Knowledge-base role.** Supplies, per capability pack, the standard DOF
disposition template and the standard blocking relations — a revolute joint has
five DOF to dispose of, and the KB knows the usual answers, which is exactly the
checklist BM-001 lacked.

**Deterministic checks.** DOF totality; every `BLOCKED_BY` has a
`BlockingRelation` with a direction and a named blocker; assembly graph
acyclicity; every obligation owned by some body pair; every interface classified;
axis vectors are unit and live in declared frames; the retention-termination
strategy exists for every retained body.

**Consumer test (S04 must be able to answer "does the intended motion exist and
the forbidden motion not?").** S04 needs the joint graph with axes and frames,
the configuration set, the DOF disposition, the blocking relations, the assembly
plan with directions, and the declared regions. It must not need to invent a
joint, a direction or an ordering.

---

### Stage 04 — motion and state

**Engineering question.** *Where is everything in each state, what path connects
the states, and is that path — and every assembly path — actually clear?*

**Owns.** `State`, `Transition`, `Witness`, plus `Envelope` and `SweptVolume`.

**Prohibited.** A rendered sheet as the authoritative artifact (R-01, INV-005); a
constant offset as a motion model (R-07); undeclared adaptive sampling; final
dimensions; manufacturing features.

**Inputs.** S03 output only.

**Outputs.** Metric poses per body per state; motion paths with **declared**
sampling and refinement windows; swept volumes with declared fidelity; envelope
extents per state; **assembly insertion sweeps** in the configuration produced by
the preceding steps (ASM-BM-003-002's "not in isolation and not in the finished
product"); occupancy results for every declared region across every state and
path; the spatial feasibility record per retained candidate; and the
`SelectionDecision` gate.

**Geometry maturity.** G3 and G4. **This is where authoritative metric geometry
first appears.**

**Four checks here would have caught four late discoveries.** Swept occupancy of
the crank axis (BM-002 CHG-02); captivity sampled across the whole travel rather
than at endpoints (BM-001 HCR-004); assembly-path feasibility as a *driver*
(BM-002 hub Ø); region occupancy of the declared access volume (BM-001's latch
finger).

**LLM role.** Low. This stage is computation. The LLM's use is proposing
*candidate* poses and paths for a solver to check.

**Knowledge-base role.** Sampling policies per motion class; standard probe sets
(the pitch/roll/yaw escape probes BM-002 used, the rotate-and-lift probes BM-003
used).

**Deterministic checks.** Sampling declared and non-adaptive; interior samples
present, not endpoints only (NEG-BM-003-006); every declared region has an
occupancy result in every state; every assembly step has a swept path result;
selection gate refuses to fire before all retained candidates carry equal
evidence.

**Consumer test (S05 must be able to answer "what features make this real?").**
S05 needs poses, paths, engagement sites, the interface list with kinds, the
blocking relations and the region volumes. It must not need to choose a pose or a
direction.

---

### Stage 05 — feature and realization

**Engineering question.** *What actual geometry on which body makes each declared
relation physically real, and what does that geometry demand of the layout?*

**Owns.** `Feature`, `Realization`, `Parameter`, `Constraint`,
`ConstructionStatement`, plus (new) **`EnvelopeConstraint`**.

**Prohibited.** Creating a `Body` or `Joint` (INV-001, R-19) — it extends S03's;
discharging an obligation with a label (INV-008); a null unit (INV-004); solving
for values.

**Inputs.** S03 + S04 output only.

**Outputs.** A feature graph — every interface realized by a named feature on
**each** participant, or a declared monolithic-compliant region with its mode;
every blocking relation given its feature pair; every declared limit given its
producing feature pair; retention realizations; compliant regions with deflection
direction and magnitude and the operations during which they are active (BM-001's
`compliant_regions` block is the right shape); the load-path records; a **total**
construction program; parameters with units; and constraints.

**`EnvelopeConstraint` is the new and necessary output.** A feature that implies a
minimum envelope — a Ø10 pin needing a 4 mm wall gives a 9 mm boss radius, giving
a 54 mm arm radius — must emit that as a constraint binding a layout parameter.
BM-002 CHG-01/CHG-03 and BM-003 R3/R6 are all the absence of this.

**Geometry maturity.** G5 and G6.

**LLM role.** High for feature proposal and for the construction program's shape;
**none** for completeness — that is enumeration over S03's relation set.

**Knowledge-base role.** Highest of any stage. Feature patterns per capability
(clevis + pin + head + captor; rail + lip + tab; heel + arm), and with each
pattern its envelope constraints and its assembly implications. This is where the
retention trichotomy becomes concrete geometry.

**Deterministic checks.** Every interface has features on all participants; every
blocking relation has a feature pair; every limit has a producer; every obligation
cited by some realization with a verification predicate; construction program
totality (every referenced symbol declared); no parameter without a unit; no
dependency cycle among parameters.

**Consumer test (S06 must be able to answer "what are the values?").** S06 needs a
closed constraint system in which every symbol is declared with a unit. Nothing
else.

---

### Stage 06 — parameter resolution

**Engineering question.** *Do values exist that satisfy every constraint, and if
not, exactly which constraints conflict?*

**Owns.** Nothing new; extends `Parameter` and `Constraint`.

**Prohibited.** Defaulting a unit (R-21); reporting `feasible` for an
underdetermined system; silently picking one member of a solution family;
deferring a symbolic expression to CAD (R-22); copying existing values and calling
them solved (R-23).

**Inputs.** S05's constraint system only.

**Outputs.** Per parameter, a value or an explicit non-value status; residuals;
the active set; margins; and the solver status from the five-value vocabulary.
For an underdetermined system, the free directions are recorded as
`UnresolvedDecision`, not resolved.

**Geometry maturity.** G7.

**LLM role.** None. This is a solver. An LLM here re-introduces R-23.

**Knowledge-base role.** Standard constraint idioms and their solvability class.

**Deterministic checks.** Residuals below a declared bound; active set consistent
with the reported status; every symbol in the construction program has a value or
a recorded reason; determinism on re-run.

**Consumer test (S07 must be able to compile).** S07 needs the construction
program plus a value for every symbol it references. INV-006 says it receives
*only* those two things.

---

### Stage 07 — geometry compilation

**Engineering question.** *Does the declared program, with the solved values,
produce valid solids — and what are they?*

**Owns.** `GeometrySignature`; extends `Body` and `Feature` with compiled
geometry.

**Prohibited.** Consulting the source, the requirements or the candidates;
repairing an uncompilable statement — it **fails, citing the statement** (INV-006,
R-24); using an OCCT face index as identity; choosing a form, a placement, an
axis or a missing dimension.

**Inputs.** Construction program + resolved parameters. Nothing else.

**Outputs.** Compiled OCCT solids; per-body validity, volume positivity and
**single-connected-solid** result; the geometry signature over the kernel's own
mass properties; native BREP then STEP exports with independent re-import and
round-trip comparison; a determinism result from an independent rebuild.

**Geometry maturity.** G8. **This is where CadQuery first appears
authoritatively.**

**LLM role.** None whatsoever.

**Knowledge-base role.** None. A KB here would be a repair mechanism.

**Deterministic checks.** All of the above, plus: the export order is
BREP-bodies → BREP-assembly → STEP-bodies → STEP-assembly → re-import → compare,
with the signature taken from the **native** shapes *before* any export.

**Can S07 be a pure compiler? Yes — with one addition.** All three references'
`build.py` files *are* exactly such compilers. But BM-003 R1 shows S07 must also
be a **validity reporter**: a hub whose clevis plates miss the base-flange chord
at their own y is a fact discoverable nowhere earlier. So S07 = pure compiler +
validity reporter + exporter, with **no repair**. When it fails, it names the
construction statement and the dependency cone, and control returns to S05/S06.

**Consumer test (S08 must be able to plan verification).** S08 needs the solids,
the signature, the feature identities, and the declared predicate set from S03/S05.

---

## 6. Stage-to-stage information matrix

Read as: *the consumer's question, and the minimum the producer must hand over
for it to be answerable without re-reading the source or inventing content.*

| boundary | consumer's engineering question | minimum sufficient hand-over | failure if absent |
|---|---|---|---|
| **S01→S02** | what must physically be true? | requirements + observables + scenarios + **quantity inventory** + ambiguities with block scopes | S02 invents magnitudes (the failure BM-002's "approximately" band is designed to provoke) |
| **S02→S03** | what bodies and joints? | body hypotheses with roles; interaction hypotheses; obligations per candidate; **evidence-route classification** | S03 invents the mechanism; P-6 goes unrecorded |
| **S03→S04** | does the intended motion exist and the forbidden motion not? | joint graph with axes and frames; configurations; **total DOF disposition**; blocking relations; assembly plan with directions and termination strategy; declared regions | BM-001 HCR-002/004/006; BM-003 R2; BM-002's simulation re-deriving the topology |
| **S04→S05** | what features make this real? | metric poses; paths with declared sampling; swept volumes; engagement sites; region occupancy; feasibility record | BM-002 CHG-02 (impossible support), BM-001 latch finger in the aperture |
| **S05→S06** | what are the values? | closed constraint system; every symbol with a unit; **envelope constraints from features** | BM-002 CHG-01/CHG-03; BM-003 R3/R6 |
| **S06→S07** | does it compile? | construction program + a value for every referenced symbol | R-24: CAD acquires authority where the design is weakest |
| **S07→S08** | how will each requirement be checked? | valid solids; signature; feature identities; declared predicates | BM-002 DEF-03: measurement on the wrong entity |
| **S08→S09** | execute what, at what fidelity? | plan items bound to (requirement, criterion, scenario, observable); controls authored from declared relations; **simulation assumption inventory** | BM-002/BM-003 controls that cannot fire; undeclared densities and gains |

---

## 7. Requirement → CAD → evidence traces

Three representative traces per benchmark, each showing where the chain is
complete and where it is held together by an invention.

### BM-001

| requirement | Oracle invariant | what CAD had to create | evidence produced | gap |
|---|---|---|---|---|
| "open and close repeatedly" | NRM-BM-001-001 | closure motion type; a joint; a carrier body | two states + sampled transition; 16/16 controls | motion type **invented**; cycle count unverifiable |
| "without accidental opening" | NRM-BM-001-006/007 | the entire retention principle, twice | tooth 2.2 mm behind solid wall; measured 0.62 mm free play; 9.88 mm³ blocking after a closing sweep | force **never computed**; "accidental" has no magnitude |
| "easy to assemble" | NRM-BM-001-010 | one-press assembly with four tabs deflected 2.2 mm | swept common 0.000 mm³ | insertion force `NOT_VERIFIED`; the 2.2 mm is **invented** |

### BM-002

| requirement | Oracle invariant | what CAD had to create | evidence produced | gap |
|---|---|---|---|---|
| "approximately 80–100 mm" | NRM-BM-002-004 | R = 45 (travel = 2R) | measured 90.000000 mm at both extremes | the only requirement fully closed by geometry |
| "support ~1 kg" | NRM-BM-002-005 | platform, clevis, two-lug straddle, load path | structural path traced edge-by-edge to measured interactions | adequacy `UNSUPPORTED` — no strength route exists |
| "avoid obvious jamming" | NRM-BM-002-014 | guides, followers, 0.2 mm clearances | 37 samples, follower volume in channel constant; ideal-joint dynamics | `NOT_VERIFIED` **by construction**: the model resolves no contact, and NRM-BM-002-014 forbids citing it |

### BM-003

| requirement | Oracle invariant | what CAD had to create | evidence produced | gap |
|---|---|---|---|---|
| "stay open on its own" | NRM-BM-003-009 | the whole locking principle; class `SMC-KINEMATIC_BLOCK` | fold-back obstructed from θ = 28.5° for all three legs | class **chosen for route availability** (P-6); force never addressed |
| "something deliberate before folding" | NRM-BM-003-011 | ribs + keyways + a two-motion release | turning blocked at ±2.5° when down; lift alone stops the fold at 21.0° | the *necessity* of the turn was lost and restored (R5) — it is a fragile emergent property, not a designed invariant |
| "not fold back, twist aside, or come off" | NRM-BM-003-010 | forbidden set; stop pads; five bayonets | outward stop at 31.0°, residual 1.0°; 24 escape probes all blocked | the forbidden set was **incomplete** until R2; the bound `outward_travel_max_deg` is a fixture invention forced by NC-17 |

**The pattern across all nine traces.** Where the source supplies a magnitude
(BM-002 travel), the chain closes cleanly. Where it does not, the chain closes
*structurally* and the quantitative half is `NOT_VERIFIED` or `UNSUPPORTED` — and
in every such case the CAD had to invent the mechanism that makes the structural
half checkable at all.

---

## 8. CadQuery entry-point recommendation

**Where geometry first appears:** **S03**, as symbolic spatial geometry (G2) —
frames, axes, directions, sidedness, declared regions. Not S05.

**Where authoritative geometry first appears:** **S04** for metric poses,
envelopes, paths and swept volumes (G3/G4). This is authoritative in the INV-003
sense: it is metric and may be a predicate input.

**Where authoritative *solid* geometry first appears:** **S07** (G8).

**Where CadQuery first appears authoritatively:** **S07**, and only there.

**Is exploratory CadQuery useful earlier? Yes — and the evidence is
overwhelming.** Every one of BM-002 CHG-01, CHG-02, CHG-03, BM-003 R1, R3, R5 and
BM-001's latch-finger conflict would have been visible in a throwaway solid built
at S04 or S05, days or revisions before it was actually found. Forbidding
exploratory solids is what pushes these discoveries to G8.

**How it stays non-authoritative.** A **Scout** facility, permitted from S04
onward, under five hard rules:

1. **It may not create or extend any DesignState entity.** Its only output is a
   `ScoutFinding`.
2. **A `ScoutFinding` may only *raise*, never *set*.** It can raise an
   `UnresolvedDecision`, propose a `Constraint`, or report a measured conflict.
   It can never supply a value, a pose, a form or a placement. This is the exact
   line R-24 was written about.
3. **It must be re-derivable from the DesignState it read**, and it records that
   state's hash. A scout built from information not in the state is inadmissible.
4. **S07 must not read it.** INV-006 already says S07 receives only the program
   and the parameters; the scout must not become a back channel.
5. **Every scout finding must be discharged** — either by an entity change that
   the owning stage makes for its own reasons, or by a recorded decision not to.
   An undischarged scout finding blocks the stage gate.

Under those rules the scout is what the three `CHG` records already were: a
measurement that forced a decision, made by the stage that owns it.

**Where each spatial commitment is fixed.**

| commitment | fixed at | proven at |
|---|---|---|
| joint axes (symbolic) | S03 | — |
| joint axes (metric) | S04 | S04 |
| poses per state | S04 | S04 |
| declared support regions | S03 (assignment) | S04 (swept occupancy) |
| retention relations (direction + blocker) | S03 | S05 features, S09 measurement |
| stops and limits | S03 (declared) | S05 (producing feature), S09 (measured onset) |
| contacts | S03 (kind), S05 (feature pair) | S09 |
| access paths and regions | S03 (declared), S04 (metric volume) | S04 occupancy, S09 |
| assembly order and directions | S03 | S04 sweeps, S09 re-measured |
| detailed feature construction | S05 | S07 |
| dimensions solved | S06 | S07 |

**Does S05/S06 require bounded iteration? Yes, and it is not optional.** BM-002
CHG-01 and CHG-03, and BM-003 R3 and R6, are all feature-envelope constraints
that only exist once features exist, and that change layout parameters that
features were placed against. The bound: **a declared maximum number of rounds;
each round must strictly reduce the set of unsatisfied constraints; every round is
a `StagePatch` with `stage_attempt` incremented and both attempts retained; a
round that does not reduce the set terminates with `underdetermined` or
`infeasible` and a named conflicting set.** Unbounded iteration would be a solver
hiding inside two stages.

---

## 9. Shared-state representation recommendation

**Recommendation: DesignPatch operations onto one shared DesignState** — which is
what `STAGE_PATCH_CONTRACT.yaml` and `DESIGN_STATE_CONTRACT.yaml` already
specify — **plus one addition the current contract lacks: a dependency and
invalidation cone carried by every patch.**

The recommendation is made from the failures, not from elegance.

**Why not separate stage outputs.** BM-002 CHG-01 changed one parameter,
`crank_axis_z`, and *eight* derived heights followed: crank pin, platform pin,
plate, guide channel, rim, and the clevis offset that CHG-03 then had to change
again. With separate per-stage outputs, that propagation is manual — and BM-003
R5 is the recorded proof of what manual propagation does: shortening
`ring_arm_r` in R1 silently destroyed the lift-only property, and it was not
noticed until a predicate failed several revisions later. Separate outputs also
produced P-11 directly: BM-003's mixed artifact directory and the BM-002 manifest
incident that `manifest_util` was written after are both *files with no shared
identity*.

**Why not one shared mutable state.** Ver2's Stage 05 kept its own truth store
(R-19) and the result was a second design world. Direct mutation makes ownership
advisory, and ownership is the mechanism INV-001 depends on.

**Why patches, specifically.** The patch envelope already carries
`parent_state_hash`, which rejects a patch computed against one world and applied
to another — exactly the class of error that produced the mixed artifact set. It
carries `execution_status` and `declared_incompleteness`, which is how a degraded
run reports itself as degraded instead of as a worse design. And it retains
attempt *n* when attempt *n+1* is written, which is what makes the S05/S06
iteration auditable.

**The addition: an invalidation cone.** Every patch must declare, for each entity
it changes, the set of entities and evidence items whose validity depends on it.
Changing a `Parameter` must mark every derived value **and every EvidenceItem
computed from it** as `STALE`. BM-003 R5 is the exact failure this prevents:
changing `ring_arm_r` should have invalidated the `lift_only` evidence
immediately. Without a cone, a shared state is only a tidier way of losing track.

**A second, smaller addition: run identity on every artifact.** P-11 twice. Any
artifact written outside the DesignState carries the `run_id` and the
`parent_state_hash` it was produced from, and a manifest over a set with more
than one `run_id` is refused rather than written.

---

## 10. Minimal migration plan

Deliberately minimal, and ordered so that each step is verifiable before the next.
No stage is implemented in this plan.

1. **Fix the one broken artifact.** `ver3/cad_validation/BM-003/.../poses.yaml`
   does not parse. Fix it, and add a repository check that every `*.yaml` under
   `ver3/` parses. One line of CI closes P-7's most embarrassing instance.

2. **Add the three new entity families to `DESIGN_STATE_CONTRACT.yaml`:**
   `BlockingRelation`, `DOFDisposition`, `AssemblyPlan`. Add `EnvelopeConstraint`
   under s05. Assign ownership in `STAGE_OWNERSHIP_MATRIX.yaml`. This is contract
   work only, and it is what P-1, P-2, P-3 and P-12 require.

3. **Add the invalidation cone to `STAGE_PATCH_CONTRACT.yaml`** and `run_id` to
   the artifact rules. Contract work only.

4. **Write the downstream-sufficiency probes *before* any stage.**
   `STAGE_PROGRESSION_CONTRACT` step 6 already mandates them; they do not exist.
   Write them against the matrix in §6 — six probes, S01→S02 through S06→S07,
   each a minimal consumer that reports exactly what is missing.

5. **Retro-fit the three CAD references as probe fixtures.** They are the only
   ground truth in the repository. For each, hand-author the S03 and S04 outputs
   that *would* have produced it — the joint graph, the DOF disposition, the
   blocking relations, the assembly plan — and run the probes against them. Any
   probe that passes on a hand-authored input that is missing something the CAD
   needed is a probe defect, and the CAD record says exactly what was needed.
   **This step is the highest-value item in the plan** and requires no stage
   implementation at all.

6. **Author the Scout rules** (§8) as a contract, before any exploratory CadQuery
   is written, so the non-authoritative boundary exists before the temptation
   does.

7. **Then, and only then, begin S03** — the stage that must change most — under
   the existing eight-step progression.

**Explicitly not in this plan:** implementing any stage; changing any Oracle;
changing `cadval`/`valcore`; re-running BM-003's validation; touching the
BM-001/BM-002 references.

---

## 11. Risks and unresolved questions

**R-1 — This retrospective has no pipeline runs in it.** Every conclusion is
drawn from a manual process performed by an agent with the Oracle in view. An
uninformed pipeline run may fail in ways this document does not anticipate. The
mitigation is step 5 of the migration plan; the risk cannot be removed until a
stage actually runs.

**R-2 — The DOF-disposition totality requirement may be expensive or ambiguous
for compliant bodies.** A rigid body has six DOF. A compliant region does not
have a finite DOF set in the same sense. BM-001's four tabs and one latch finger
are the test case, and the contract for `DOFDisposition` over a
`MONOLITHIC_COMPLIANT` realization is genuinely unresolved.

**R-3 — The evidence-route capability gap is structural and this plan does not
close it.** No compliant-force route, no contact-resolving route, no stability
route exists. Three of BM-003's four state-maintenance classes, BM-001's snap
latch and BM-002's jamming question all sit outside what any stage can establish.
Making `EvidenceRouteDecision` explicit makes the gap *visible*; it does not make
it smaller. Until a compliance route exists, the pipeline will keep selecting
mechanisms it can evidence, and P-6 will keep operating.

**R-4 — Bounded S05/S06 iteration may not converge on a real problem.** The bound
proposed (strictly reducing unsatisfied constraints) is a heuristic. BM-002 needed
three rounds and BM-003 needed eight; neither is evidence that a bound exists in
general. The honest fallback is `underdetermined` with a named conflicting set,
which is a report rather than a design.

**R-5 — The scout boundary is enforceable only by discipline.** Rules 1–5 in §8
are contract statements; nothing mechanically prevents a value discovered in a
scout from being typed into a parameter with a plausible-sounding rationale. The
only real defence is that the parameter's provenance must cite a constraint, and
the constraint must be derivable from the state.

**R-6 — Micro-oracles as a knowledge base are unvalidated.** All three are
`PRE_CAD_SEMANTIC_REVIEWED` with every fixture `NEEDS_GEOMETRY_VALIDATION`. Using
them as the S02/S05 KB imports whatever is wrong in them.

**R-7 — Whether S03 can carry the assembly plan without metric geometry is
unproven.** BM-002's forced insertion direction was discovered *from* metric
geometry (the arm cannot pass the bore). S03 may only be able to declare the
*strategy* and the *order*, with the direction feasibility genuinely belonging to
S04. This document assigns order and direction to S03 and proof to S04, but the
BM-002 case is a warning that the direction itself may not be decidable that
early.

**R-8 — Nothing here addresses S08–S12.** The control-adequacy findings (P-5),
the measurement-subject findings (P-8) and the claim-vocabulary findings (P-10)
all land on S08–S11 and are recorded here only as consumer requirements.

---

*Produced from: `ver3/benchmarks/{BM-001,BM-002,BM-003}/source/`,
`ver3/oracles/product_cases/{BM-001,BM-002}/`, `ver3/oracles/held_out/BM-003/`,
`ver3/cad_validation/{BM-001,BM-002,BM-003}/`, `ver3/contracts/`,
`ver3/phase0/VER2_RETIREMENT_MATRIX.md`. No code or artifact was modified.*
