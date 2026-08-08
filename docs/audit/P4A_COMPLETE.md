# P4A — RAW PIPELINE OUTPUT REVIEW

Axis A: **GENERATED EVIDENCE** (this document) reviewing **GENERATED OUTPUT**.
Axis B: **REVIEW RECORD**.

This package reads the stage artifacts the pipeline actually produced and states what
engineering they contain. It does not inspect implementation, validators, prompts, or
contracts as a basis for judgement. No experiment was run; nothing was modified or rerun.

---

> **AMENDED — second evidence pass.** Sections §A–§F at the end of this document
> were added after reading the raw-model and provenance artifacts. They contain the
> raw-response comparison that §0.4 originally listed as missing, and they **correct
> two over-generalisations** in §2 and §5.4. Where §A–§F and the earlier sections
> disagree, §A–§F govern. §0 below is the first-pass ledger; §A.0 is the current one.

## §0 COVERAGE LEDGER — WHAT WAS ACTUALLY READ IN THIS SESSION

Complete reads only. Nothing below was skimmed, grepped, or inferred from filenames.

### 0.1 COMPLETE — the primary evidence (24/24 files)

Every stage artifact of all six cases in `ver3/live_runs/window2/r_final/responses/<case>/t1_CND-0001/`:

| Case | s03 | s03b | s04a | s04b |
|---|---|---|---|---|
| BM-001 | ✓ 171 L | ✓ 168 L | ✓ 86 L | ✓ 43 L |
| BM-002 | ✓ 179 L | ✓ 165 L | ✓ 88 L | ✓ 49 L |
| BM-003 | ✓ | ✓ | ✓ 125 L | ✓ 78 L |
| PRB-01 | ✓ 251 L | ✓ 263 L | ✓ 132 L | ✓ 74 L |
| PRB-02 | ✓ 219 L | ✓ 160 L | ✓ 103 L | ✓ 79 L |
| PRB-03 | ✓ 147 L | ✓ 121 L | ✓ 58 L | ✓ 39 L |

The P4A instruction named stored stage output as the primary evidence. That layer is 100 % complete.

### 0.2 COMPLETE — recorded upstream (6 files)

- `ver3/assy_v3/fixtures/responses/BM-001/s01.json` (290 L), `BM-001/s02.json` (545 L)
- `ver3/assy_v3/fixtures/responses/BM-002/s02.json` (567 L)
- `ver3/assy_v3/fixtures/responses/BM-003/s02.json` (669 L)
- `ver3/assy_v3/probes/PRB-03/s01.json` (230 L), `PRB-03/s02.json` (440 L)

### 0.3 COMPLETE — Window-1 live model output (1 file, a labelled sample)

- `ver3/live_runs/deepseek/q6_fix/responses/BM-003/t1/s02.json` (496 L)

Chosen because BM-003 is the case whose repository-authored counterpart I had just read in
full, giving a controlled same-case comparison. **This is 1 of ~35 Window-1 response files.**
Everything I say about live S01/S02 behaviour below is scoped to this one artifact and is
labelled as a sample, not as a population claim.

### 0.4 NOT READ — remaining P4A scope, carried forward

`BM-002/s01.json`, `BM-003/s01.json`, `PRB-01/s01.json`, `PRB-01/s02.json`,
`PRB-01/s02.pre_revision.json`, `PRB-02/s01.json`, `PRB-02/s02.json`;
`window2/r_final/trials.json` (1,831 L) and `model_run_records.json` (1,250 L);
the other 34 `q6_fix` response files plus its `trials.json` and `model_run_records.json`.

Consequence: **§7 (RAW MODEL RESPONSE vs STORED STAGE OUTPUT) is not answered in this
package.** That comparison requires `model_run_records.json`, which holds the raw response
text. I make no claim about parser repair, normalisation, or silent field rewriting, because
I have not seen the pre-parse text. Every provenance verdict below is therefore stated at the
level of *stored artifact*, and where a defect could in principle have been introduced by
deterministic code rather than by the model, I say so.

---

## §1 PROVENANCE — THE CHAIN IS NOT WHAT ITS DIRECTORY NAME SUGGESTS

The §8 warning in the instruction was correct, and the situation is one step further from
"live DeepSeek S01→S04" than the warning anticipated.

| Segment | Label | Evidence |
|---|---|---|
| PRB-01/02/03 S01, S02 | **REPOSITORY-AUTHORED FIXTURE** | `PRB-03/s01.json` and `s02.json` both carry `_meta.authored_by: "agent-in-repository"` |
| BM-001/002/003 S01, S02 | **RECORDED FIXTURE INPUT** | no `authored_by` key; carry `_meta.answers_prompt_sha256` and the *identical* `pairing_history` sentence as the PRB fixtures — "re-paired after the response-schema section was added to the prompt; content unchanged and re-verified against the parser, contract validation and completeness check" |
| all six S03, S03B, S04A, S04B | **DOWNSTREAM MODEL OUTPUT** | produced live on replayed upstream |
| `q6_fix` S01, S02 | **LIVE MODEL OUTPUT** | the only genuine model authorship of S01/S02 in the corpus |

**OBSERVED.** The shared `pairing_history` string means the BM and PRB upstream fixtures went
through the same authoring-and-repair process. The PRB files say outright that an agent working
in the repository wrote them.

**POSSIBLE IMPLICATION.** No Window-2 result is evidence about what the model does at S01 or
S02. Window-2 measures S03/S04 *given hand-authored upstream of a quality the model does not
itself produce* — see §2, which shows the two differ in kind, not merely in polish.

**NEEDS CROSS-READ.** Whether `BM-00x/s01.json` and `s02.json` were authored the same way, or
were captured model output subsequently edited. `BM-001/s01.json`'s `_meta` contains only
`answers_prompt_sha256`; the BM `s02` files add `pairing_history` but no `authored_by`.

---

## §2 WHAT DEEPSEEK ACTUALLY AUTHORS AT S02 — the controlled comparison

Same case (BM-003), same prompt family, two authors. Both files read completely.

| | LIVE MODEL OUTPUT (`q6_fix/BM-003/t1/s02.json`) | REPOSITORY FIXTURE (`fixtures/responses/BM-003/s02.json`) |
|---|---|---|
| obligations | 28 | 17 |
| `derivation_premises` | **absent from all 28** | present on all 17 |
| candidates | 3 | 6 |
| `principle` | **a bare string**, e.g. `"OVER_CENTRE"` | a dict of 5–7 keys, e.g. `{ACTUATE, BOUND_MOTION, MAINTAIN_CONFIGURATION, PERMIT_ASSEMBLY, PERMIT_RELATIVE_MOTION, RETAIN_BODY, TRANSMIT_LOAD}` |
| `obligations_created` | **OBL- ids of already-existing obligations** | prose commitments: *"a bounded stroke set by the crank radius"*, *"retention of the blocking member itself"* |
| `self_locking` | absent | present |
| acceptance contracts | 3 contracts, **identical 14-obligation list and identical 8 predicates in all three** | 4 contracts, 2–3 obligations each, predicates specific to the mechanism |

Classification of live S02 output:

- **DEEPSEEK_AUTHORED, engineering-inert.** The 28 obligations are largely requirement
  restatements. OBL-0002 / 0003 / 0012 / 0020 / 0028 all express *"parts stay attached"*;
  OBL-0008 / 0010 / 0019 / 0026 / 0027 all express *"does not fold unintentionally"*. The
  higher count carries less distinct content than the fixture's 17.
- **Discriminating machinery populated and inert.** `scope: "CANDIDATE_DISCRIMINATING"` is
  assigned, yet **all three candidates address the identical 25-obligation list**, and all
  three acceptance contracts carry the same predicates. Three different locking principles —
  over-centre, friction, detent — receive the same acceptance test. Nothing discriminates.
- **PHYSICALLY INCONSISTENT.** LC-0001, LC-0002, LC-0005, LC-0006 declare
  `reacted_at_role: "the user's hand while folding"` / `"…while opening"`. Four of eight load
  cases react at the actor. A load reacted at the operator's hand has no path through the
  product; the fixture reacts every case at the desk.
- **Circular derivation.** `obligations_created: ["OBL-0007","OBL-0008","OBL-0010","OBL-0019","OBL-0026"]`
  names obligations derived from requirements *before any candidate existed*. A candidate that
  "creates" only pre-existing obligations has recorded no new commitment.

**This is the most consequential finding in P4A.** The `principle` dict is the channel through
which S02 tells S03 what kind of machine to build — `CRANK_SLIDER`, `SEPARATE_RETAINING_MEMBER`,
`HARD_STOP`, `JOURNAL_SUPPORT`. In live model output that channel is a single string. Every
S03 result in Window 2 was produced from a structure the producing stage does not actually emit.

---

## §3 THE SPATIAL LAYER — S04B JOINT PLACEMENT

The instruction asked specifically for coincident joints, joints outside their bodies, and
collapsed repeated members, recorded with raw coordinates. All three occur, in five of six cases.

### 3.1 Coincident joint origins — raw values

| Case | Joints | Origin | Coincident |
|---|---|---|---|
| BM-001 | JNT-0001, JNT-0002 | `[0.0, 0.0, 0.0]` | **2 of 2** |
| BM-002 | JNT-0001, JNT-0002, JNT-0003 | `[0.0, 0.0, 2.5]` | **3 of 4** |
| BM-003 | JNT-0001, JNT-0002, JNT-0003 | `[0.0, 1.0, 0.0]` | **3** |
| BM-003 | JNT-0004, JNT-0005, JNT-0006 | `[0.0, 0.0, 0.5]` | **3** — 6 of 6 total |
| PRB-01 | — all five distinct: `[1,0,0]`, `[3,0,0]`, `[2,0,1]`, `[0,-3,0]`, `[2,-1,0]` | | **0 of 5** |
| PRB-02 | JNT-0001, JNT-0003 | `[0.0, 0.0, 0.0]` | **2 of 4** |
| PRB-03 | JNT-0001, JNT-0002, JNT-0003 | `[0.0, 0.0, 0.0]` | **3 of 3** |

**19 of 25 joints across the corpus sit on top of another joint.**

### 3.2 Joints outside the bodies they connect — raw envelopes vs raw origins

**BM-001, JNT-0002** (COMPLIANT, `parent_group: RGP-0003`, `child_group: RGP-0004`, both
groups of BOD-0003):
- `ENV-0003` BOD-0003: centre `[2.0, 1.0, 0.0]`, half_extent `[0.5, 0.5, 0.5]`
  → spans x ∈ [1.5, 2.5], y ∈ [0.5, 1.5], z ∈ [−0.5, 0.5]
- `JNT-0002` origin: `[0.0, 0.0, 0.0]`

The joint internal to BOD-0003 lies 1.5 units outside it in x and 0.5 in y. It is outside the
only body it is inside.

**BM-001, JNT-0001** (REVOLUTE, RGP-0001 ↔ RGP-0002):
- `ENV-0002` BOD-0002: centre `[1.5, 0.0, 0.0]`, half_extent `[0.5, 1.5, 1.0]` → x ∈ [1.0, 2.0]
- origin `[0,0,0]` — inside BOD-0001, **outside BOD-0002**. The hinge is not on the panel it hinges.

**BM-002**, origin `[0,0,2.5]` is inside `ENV-0002` (x,y ∈ [−0.5, 0.5], z ∈ [−2, 4]) but outside
`ENV-0003` (z ∈ [0.5, 1.5]) and outside `ENV-0004` (y ∈ [2, 4]).

### 3.3 Repeated members collapsed — and s04a already had it right

BM-003 is a three-leg stand. Its **s04a envelopes carry correct three-fold symmetry**:

```
ENV-0002 BOD-0002 centre [ 0.000,  1.0, 0.0]
ENV-0003 BOD-0003 centre [ 1.732, -1.0, 0.0]
ENV-0004 BOD-0004 centre [-1.732, -1.0, 0.0]     ← 120° apart at radius 2
```

Its **s04b collapses all three leg pivots to `[0.0, 1.0, 0.0]`** — the position of BOD-0002
alone. `[0,1,0]` is far outside BOD-0003 (x ∈ [1.232, 2.232]) and BOD-0004.

**OBSERVED.** The geometry needed to place the joints correctly existed in the immediately
preceding artifact of the same case and was not used.

**POSSIBLE IMPLICATION.** The collapse is not a failure to know where the legs are. It is a
failure at the s04a → s04b handoff.

### 3.4 No swept evidence anywhere

In **all six** `s04b.json` files, `transitions[]` entries contain exactly
`id`, `from_configuration`, `to_configuration`, `moving_groups`. There is **no path field, no
sampling declaration, and no swept volume in any transition in any case.** S04's "swept proof"
half produces no swept evidence at all.

### 3.5 Degenerate configurations and transitions

- **PRB-02**: CFG-0002 and CFG-0003 have byte-identical coordinates
  `{JNT-0001: 0.1, JNT-0002: 3.6, JNT-0003: 0.0, JNT-0004: 10.0}`, and `TRN-0002` between them
  has `moving_groups: []`. These configurations are named **"tightening"** and **"holding"** —
  for a clamp, the distinction that matters most. It is declared and then erased.
- **BM-003**: CFG-0001 ("deployed") and CFG-0003 ("released") have identical coordinates across
  all six joints. The release action changes nothing.
- **PRB-01**: `JNT-0004` has a placement `[0,-3,0]` and appears in **no** `state_coordinates`
  block. **PRB-03**: `JNT-0002` and `JNT-0003` likewise have placements and no coordinates.
- **BM-002**: only one transition exists (CFG-0001 → CFG-0002). The lift has no way down.

### 3.6 The model states its own basis — PRB-01 `s04b.json:73`

```
"notes": "Placed joints based on typical linkage arrangement. Coordinates chosen to allow
          motion along Y for gates, rotation about Z for linkage, compression along Y for spring."
```

**OBSERVED.** PRB-01 is the one case with five distinct joint origins, and its own notes field
attributes them to a *typical arrangement* rather than to the case's topology.

---

## §4 SIX ENGINEERING NARRATIVES

Reconstructed from the artifacts alone, then compared with P3.

### BM-001 — enclosure with hinged closure and compliant catch

**What the pipeline built.** Three bodies (base, closure, catch); the catch split into two rigid
groups for compliance; a REVOLUTE `RZ` hinge and a COMPLIANT `TY` joint; two configurations.

**Defects.**
- `BLK-0001`: `retained_group: "RGP-0001"`, `blocker_body: "BOD-0001"` — RGP-0001 *is* BOD-0001's
  group. **A body blocks itself in all six DOF.**
- **No blocking relation covers `RZ` of `RGP-0002` in `CFG-0001`** — the exact DOF the hinge
  permits. Nothing holds the lid shut. `BLK-0007` (blocker BOD-0003, the catch) blocks `TY`, a
  DOF `BLK-0002` already blocks in both configurations, making the catch redundant.
- **Three incompatible opening motions in one file**: `RZ` (JNT-0001), `+Y` translation
  (BLK-0007 defeat spec), `−Z` translation (BLK-0006 defeat spec).
- Every `LoadPath.ordered_hops` terminates in the literal string `"NONE"`, although S02 supplied
  `reacted_at_role` on all five load cases.
- `CFG-0002 "Open"` is `kind: "TRANSIENT"` for a box whose open state is what affords access.
- `FRG-0001` ACCESS (to the interior) is owned by the *moving closure*; `FRG-0004` APERTURE (to
  the release) is owned by the *base*. Apparently transposed. `FRG-0003` KEEP_OUT is owned by the
  moving body and its s04a volume x ∈ [1.2,1.8] overlaps FRG-0001's ACCESS volume x ∈ [1.1,1.9]
  almost entirely — **a keep-out and an access region in the same space**.
- `FRG-0002` SUPPORT (owner BOD-0001, y ∈ [−1.5,1.5]) has volume centre `[0,−0.8,0]`
  half `[1.8,1.2,0.8]` → y ∈ [−2.0, 0.4]. **The support region extends 0.5 units outside its
  own owning body.**
- s04a's `reach_results` say FRG-0001 is "on the top face… approach from +Z"; the declared centre
  is z = 0 with half-extent 0.8. Prose and coordinates disagree inside one file.
- `termination_strategy` inverted: the *compliant* catch gets `LATER_BODY_COVER`, the *rigid*
  closure gets `ELASTICITY`.

### BM-002 — hand-cranked lift

**Upstream (read in full).** `CND-0001.principle` = `{CONVERT_MOTION: CRANK_SLIDER,
GUIDE_MOTION: PRISMATIC_GUIDE, PERMIT_RELATIVE_MOTION: REVOLUTE_PAIR, ACTUATE: DIRECT_MANUAL,
TRANSMIT_LOAD: SHEAR_MEMBER}`. `obligations_created` includes **"a bounded stroke set by the
crank radius"**. LC-0001/LC-0004 carry a real magnitude, `"approximately 1 kg"`.

**What the pipeline built.** Base, rotary input shaft, crank link, slider platform;
JNT-0001 REVOLUTE `RZ`, JNT-0002 REVOLUTE `RY`, JNT-0003 REVOLUTE `RY`, JNT-0004 PRISMATIC `TZ`.
The body decomposition and joint types are a **faithful realization of CRANK_SLIDER** — the best
S02→S03 principle transfer in the corpus.

**Defects — and they are decisive.**
- **The input axis is parallel to the output axis.** JNT-0001 is `RZ` about `+Z`; JNT-0004 is
  `TZ` along `+Z`. A crank rotating about the same axis the slider translates along cannot drive it.
- **`JNT-0001` holds the value `0.0` in both CFG-0001 (LOWERED) and CFG-0002 (RAISED).** The
  rotary input — the entire point of the mechanism — does not move across the only transition.
  The platform rises 2.0 at JNT-0004 with no input. **The actuation is disconnected from the motion.**
- **Crank radius = 0.** JNT-0002 and JNT-0003 are the crank link's two pins and share
  `[0,0,2.5]`. The link has zero length; JNT-0002 = +90 and JNT-0003 = −90 cancel. The one
  dimension the upstream explicitly named as defining the stroke is produced as zero.
- ACC-0001's predicate *"the platform displacement between the extreme input positions lies in
  the stated band"* is falsified by s04b: there are no extreme input positions.
- **All four blocking relations are self-blocking** — every `retained_group`'s body is its own
  `blocker_body`. No relation names an external blocker.
- **DOF grid double-assignment.** For RGP-0003 the blocked set `{TX,TY,TZ,RX,RZ}` and the
  irrelevance set `{TX,TY,TZ,RX,RZ}` are identical; same for RGP-0004 `{TX,TY,RX,RZ}`; RGP-0002's
  `RY` is both blocked and irrelevant in both configurations. **Every blocked DOF is
  simultaneously declared irrelevant** for three of four groups.
- **`RGP-0004` `TZ` is blocked by nothing** — so the platform is free to fall in both
  configurations. UNR-0002 upstream asked precisely *"whether the product must hold its position
  when the input is released"*; it is never carried into S3U and the output leaves it physically open.
- `IFC-0004` (housing↔platform, the prismatic guide) appears in **no load path**. All platform
  load is routed through the crank link and input shaft instead of the guide that carries it.
- s04a's ENV-0001 "enclosure" spans z ∈ [−1, 1] while ENV-0002 spans z ∈ [−2, 4] and ENV-0004
  spans z ∈ [−1, 3]. **The enclosing body is smaller than two bodies it must enclose**, against OBL-0012.
- The `"approximately 1 kg"` magnitude reaches nothing downstream; `s04a.scale.absolute` is `null`.
- S3U-1001 states *"no explicit fixity to ground is modeled for the housing (BOD-0001)"* while
  `BLK-0001` in the same file asserts `promised_features: ["fixed to world"]`.
- `termination_strategy: "ELASTICITY"` for BOD-0002 and BOD-0003, both rigid, in a case where
  every joint has `compliance: null`.

### BM-003 — three-leg folding stand

**Upstream (read in full).** 17 obligations, each with derivation premises. `CND-0001.principle`
= `{MAINTAIN_CONFIGURATION: SEPARATE_RETAINING_MEMBER, BOUND_MOTION: HARD_STOP,
PERMIT_RELATIVE_MOTION: REVOLUTE_PAIR, RETAIN_BODY: LATER_BODY_COVER, …}`. **CND-0003 is the
compliant/detent alternative and its `evidence_route_verdict.available` is `false`** —
*"the hold is a deflection force and no available route establishes it."*

**Defects.**
- **The stand never folds.** JNT-0001/0002/0003 hold `0.0 / 120.0 / 240.0` in **all three**
  configurations. The only joints that change are the retention members' compliance coordinates.
  OBL-0009 (*"the folded configuration is smaller than the deployed one"*) is falsified by the output.
- **The selected candidate's mechanism was replaced by the rejected candidate's.** CND-0001 is
  `SEPARATE_RETAINING_MEMBER`; S03 attached the retaining members with **COMPLIANT** joints
  (`mode: TRANSLATION`) — the principle of CND-0003, whose evidence route the upstream declared
  **unavailable**. The design silently moves onto an evidence route the architecture had refused.
- **No hard stop exists**, though `BOUND_MOTION: HARD_STOP` is in the principle and
  `obligations_created` names *"a bound on the deployed travel"*. No blocking relation touches
  the legs' `RZ`. ACC-0001's first predicate — *"with the member in place, no continuous path
  leads from deployed toward folded"* — is falsified: the path is fully open.
- **All nine blocking relations name `BOD-0001` as blocker and `CFG-0001` as the only
  configuration.** CFG-0002 and CFG-0003 have an entirely empty blocking layer.
- `irrelevance: []`. DOF grid = 7 groups × 3 configs × 6 DOF = **126 cells; ~120 have no source.**
  RGP-0001 appears in no relation at all.
- **Two contradictory conventions for "down" in one file.** The legs are blocked `+Y`/`−Y` with
  defeat specs *"apply an upward force"* / *"sink into the ground"*; the retention members are
  blocked `+Z` with defeat spec *"press down… and observe it translate downward"* — i.e. `−Z`.
  **BLK-0007/0008/0009 block the direction opposite to the motion their own defeat spec describes.**
- **`LDP-0001` contains a cycle**: `[FRG-0001, BOD-0002, IFC-0001, BOD-0001, IFC-0004, BOD-0005,
  IFC-0007, BOD-0002, IFC-0001, BOD-0001]` — BOD-0002, BOD-0001 and IFC-0001 each appear twice.
  LDP-0003 and LDP-0005 are byte-identical to it.
- `FRG-0001` is owned by three spatially separate bodies and receives **one** s04a volume, placed
  at leg 1's azimuth. `FRG-0002` likewise. This is the concrete mechanism by which the three-fold
  symmetry present in s04a's envelopes is discarded.
- `instance_identity: "each of three identical"` on three separate body ids whose `role` says
  *"one of three"* — the record simultaneously describes 3 legs and 9.
- Eleven of seventeen obligations are referenced by no body — including OBL-0003 (folding path),
  OBL-0004 (footprint area), OBL-0008 (stays attached), OBL-0009 (compactness), OBL-0013
  (assembly), OBL-0014 (reversibility). **The obligations encoding the mechanism's actual
  difficulty are the ones nothing claims.**
- UNR-0002 (*"whether the supports move together or independently"*) and UNR-0004 (*"whether the
  product arrives folded or deployed"*) are both silently decided, never carried into S3U —
  **PREMATURE COMMITMENT** on explicitly flagged open decisions.

### PRB-01 — sequential dispenser (strongest case)

**Genuinely strong.** Seven functionally-named bodies including an explicit **hard stop**
(BOD-0007, `instance_identity: "integral with housing"`) and a **return spring** on a COMPLIANT
joint. A FIXED joint with `dof: []` and `axis_direction: "NONE"`. `BLK-0001..0004` use the hard
stop as blocker for the gates in ±Y with testable defeat specs — **the best blocking relations in
the corpus**. `termination_strategy: "ELASTICITY"` for the spring — the only correct use of that
value anywhere. Four substantial unresolved items with real alternatives, including S3U-1003 which
correctly notices that IFC-0003/IFC-0004 are typed CONTACT with no kinematic pairing.

**Defects.**
- **The interlock — the mechanism's defining function — is not in the topology.** BOD-0004's
  `role` string says the linkage *"connects input and output gates so they are never open
  together"*. But **there is no joint between the linkage and either gate**: JNT-0001 and JNT-0002
  are independent housing→gate prismatics, and the linkage appears only in two CONTACT interfaces.
  s04b asserts the alternation in coordinates (CFG-0002: 1/0; CFG-0003: 0/1) with nothing
  enforcing it. The one thing this probe tests lives in a prose field.
- `BLK-0008` has **`blocker_body: "NONE"`** — a blocking relation with no blocker, encoding
  "grounded to the wall".
- The gates' `TY` is blocked in **both directions in all three configurations** while s04b moves
  it 0 → 1 → 0. Likewise BLK-0005 blocks `RZ` of RGP-0005, the only DOF of JNT-0003, which moves
  0 → −10 → +10. **The relation cannot express a bounded range, only a block** — so a hard stop is
  recorded as an assertion that the motion is impossible.
- `LDP-0003`, `LDP-0004`, `LDP-0005` are all `["BOD-0001", "BOD-0001"]` — a self-loop standing in
  for three load paths. LDP-0001 is `[BOD-0001, BOD-0007, BOD-0001]`, also a cycle.
- All seven `rigid_groups[].members` are `[]`.
- **No interface is activated by any assembly step** in this case.
- s04a `FRG-0002` (y ∈ [−3.5,−2.5]) lies partly outside its owning housing (y ∈ [−3,3]).

### PRB-02 — screw clamp

**Strong in places.** A `HELICAL` joint for the lead screw; three well-formed unresolved items in
s03 with correctly-typed `kept_open_by: ["FRE-000N"]`; S3U-1001 and S3U-1002 in s03b diagnose the
grounding and axial-constraint gaps in plain, correct engineering language.

**Defects.**
- **The actuation does not reach the moving jaw.** JNT-0002 (HELICAL) joins the nut to the screw;
  JNT-0001 (PRISMATIC) joins fixed jaw to traveling jaw; **there is no joint between the screw and
  the traveling jaw** — only IFC-0003, a CONTACT interface. Turning the screw drives nothing.
- **`HELICAL` is given `dof: ["TY","RY"]`** — two DOF. A helical pair has one; the coupling *is*
  the lead screw. s04b then gives JNT-0002 a single scalar coordinate, so the artifact is
  internally inconsistent about the joint's own dimensionality.
- **Mutual grounding loop.** BLK-0001 grounds RGP-0001 on BOD-0004; BLK-0004 grounds RGP-0004 on
  BOD-0001. Neither reaches anything external. s03b's own S3U-1001 says so: *"the anchor nut is
  not fixed to anything. Thus, the assembly is not grounded."* **The blocking layer and the
  unresolved layer of one file directly contradict each other.**
- **`defeat_specification: "None"` on four of five blocking relations.** The falsifiability
  mechanism is absent 80 % of the time in this case.
- **BLK-0003 blocks the lead screw in all six DOF in CFG-0002, the configuration named
  "tightening"** — while JNT-0002's coordinate changes 0 → 3.6 into it.
- **A phantom body propagates two stages.** `"desk edge"` appears as a free-text entry in
  `IFC-0001.bodies` and `IFC-0002.bodies` (s03), then as `ENV-0006.body: "desk edge"` (s04a), then
  as a load-path hop (s03b). No stage rejects an untyped string in a body-reference field.
- `LDP-0001..0003` are `["arm", "BOD-0002", "BOD-0001", "desk edge"]` — identical, and beginning
  and ending outside the typed model. This is arguably the **most physically honest load path in
  the corpus**, and it is expressible only by abandoning the type system.
- BLK-0001 and BLK-0005 are one fact split across configurations under two ids.
- `access_side: "+Y"` on all five steps; `termination_strategy: "NONE"` on all five.

### PRB-03 — returning foot pedal

**Upstream (read in full, repository-authored).** `CND-0001.principle` = `{ACTUATE: STORED_ENERGY,
BOUND_MOTION: HARD_STOP, GUIDE_MOTION: JOURNAL_SUPPORT, MAINTAIN_CONFIGURATION:
SEPARATE_RETAINING_MEMBER, …}`. Eight obligations. OBL-0007: *"The travel of the pressed surface
is bounded at both ends."* ACC-0001 predicates include *"travel is bounded at both ends"*.
Two actors: ACT-0001 the operator, **ACT-0002 the machine**. OBL-0008 is the only
`satisfiable_at: "s04"` obligation in the case.

**Defects.**
- **The stored-energy element is modelled as rigid.** BOD-0003 is *"stored-energy element that
  returns the surface"* and JNT-0002 joining it is **FIXED** with `compliance: null`. There is
  **no joint at all between the spring and the pedal it returns** — only IFC-0003. PRB-03 contains
  **zero COMPLIANT joints**, in the one case that is entirely about compliance.
- **`BOUND_MOTION: HARD_STOP` — named in the principle, in OBL-0007, and in the acceptance
  predicate — produces no hard stop, no joint limit, and no blocking relation on `RZ`.** PRB-01
  invented a hard-stop body unprompted; PRB-03, told three times, produced none.
- **The stiffest member is grounded by the softest**: BLK-0001 declares RGP-0002 (the fixed
  support) blocked in all six DOF by BOD-0003 (the spring); BLK-0002 declares the reverse. Another
  mutual grounding loop — and BLK-0002 declares the spring immobile in all six DOF.
- **ACT-0002 vanishes.** No functional region carries it; OBL-0002 (*"the displacement… is
  available at the product boundary for the machine to detect"*) is addressed by nothing. UNR-0002
  upstream — *"where this product ends and the machine begins"* — is the most sophisticated
  reasoning in the fixture and is dropped, not refused, not deferred.
- **OBL-0008 (`satisfiable_at: "s04"`, SWEPT_INTERFERENCE, "an ordered installation sequence
  exists") is answered by `assembly_directions: []`** — the only empty assembly-direction list in
  the corpus.
- `LDP-0001` and `LDP-0003` are `["IFC-0001","JNT-0001","IFC-0004"]` — **no bodies at all**;
  LDP-0002 is `["BOD-0001","JNT-0001","BOD-0002"]`. Two hop vocabularies in one file.
- **`activates: ["CFG-0001","CFG-0002"]` on all four assembly steps** — configuration ids in the
  interface-activation field, identical on every step.
- `termination_strategy: "LATER_BODY_COVER"` for BOD-0004, which is the **last** body placed.
- `kept_open_by: ["None"]` — the literal string inside a list.
- s04a `ENV-0001` and `ENV-0002` share centre `[0,0,0]` with identical z-extent — BOD-0002 wholly
  inside BOD-0001. `FRG-0001`'s volume is **numerically identical to ENV-0001**: the "access
  region on the upper surface" is the entire body.

---

## §5 CROSS-CASE PATTERNS

### 5.1 Ground has no representation, and every case invents a different workaround

| Case | Encoding of "reacted by the world" |
|---|---|
| BM-001 | `BLK-0001`: body blocks **itself** |
| BM-002 | **all four** relations self-block |
| BM-003 | every relation blocked by BOD-0001; nothing grounds BOD-0001 |
| PRB-01 | `blocker_body: "NONE"` |
| PRB-02 | mutual loop, jaw ↔ nut |
| PRB-03 | mutual loop, support ↔ spring |

**Six cases, six degenerate encodings, zero valid external ground references.** Every upstream
fixture supplies `reacted_at_role` on every load case ("the desk surface the product stands on",
"the floor or bench"). The named reaction site is never representable.

### 5.2 The DOF grid is never a partition

`irrelevance` is `[]` in BM-001, BM-003, PRB-01, PRB-03. In BM-002 it **exactly duplicates** the
blocked sets. In PRB-02 it holds two entries. In no case does blocking ∪ irrelevance partition
the domain — it is either mostly empty or double-covered. Additionally, in PRB-01, PRB-02 and
BM-002 a DOF is simultaneously **BLOCKED and moving in `s04b`**.

### 5.3 The functional connection is repeatedly an interface, never a joint

- PRB-01: interlock — linkage↔gates are CONTACT interfaces, no joint.
- PRB-02: actuation — screw↔traveling jaw is a CONTACT interface, no joint.
- PRB-03: return — spring↔pedal is a COMPLIANT_INTERACTION interface, no joint.
- BM-002: input↔motion — joints exist but the input joint never moves.

In four of six cases the mechanism's defining force- or motion-transmitting relation is expressed
as an untyped interface or a prose `role` string rather than in the kinematic structure.

### 5.4 Enumerations are not enforced — one field, many vocabularies

| Field | Distinct values observed across six cases |
|---|---|
| `configurations[].kind` | `OPERATIONAL`, `TRANSIENT`, `INTENDED`, `TEMPORARY`, `REST`, `INTERMEDIATE`, `DISCRETE`, `assembly`, `operation` — **9, mixed case** |
| `nominal_status` | `OPEN`, `ASSEMBLED`, `ENGAGED`, `CONTACT`, `CLEARANCE`, `COMPRESSED`, `FIXED`, `engaged`, `sliding` — **9** |
| `interaction_kind` | `CONTACT`, `CLEARANCE`, `COMPLIANT_INTERACTION`, `FIXED` — contract enumeration is `DECLARED_CONTACT` etc.; **the prefix is dropped in every case** |
| `instance_identity` | `one`, `single`, `unique`, `each of three identical`, `integral with housing` — **5** |
| `rigid_groups[].members` | prose nouns / `[]` / the body's own id — **3 interpretations** |
| `allowable_travel_status` | `UNSUPPORTED`, `UNKNOWN`, `FREE` — **3** |
| `compliance` when absent | `null`, `{}` — **2** |
| `access_side` | `+Z`/`+X`/`+Y`/`-Y`, `top`/`front`/`bottom`, `TOP`/`FRONT`/`INTERNAL`/`NONE`/`ANY` — **3 systems** |
| `approach_side` (s04a) | `+Z`, `+X`, `+Y`, `TOP`, `FRONT`, `from above` — **3 systems** |
| `activates` | IFC- ids / JNT- ids / both / `[]` / **CFG- ids** — **5** |
| `depends_on` | ASY- ids (BM-002) vs BOD- ids (BM-003, PRB-01, PRB-02) — **2** |
| `LoadPath.ordered_hops` | BOD+IFC / BOD only / IFC+JNT only / FRG+BOD+IFC / free text / terminating `"NONE"` — **6** |

### 5.5 `kept_open_by` in `s03b` is wrong in all six cases — and right in `s03`

| Case | `s03b` `kept_open_by` | `s03` `kept_open_by` |
|---|---|---|
| BM-001 | `BLK-` ids | — |
| BM-002 | `OBL-` ids | `FRE-0003`, `FRE-0006` ✓ |
| BM-003 | `LC-` ids | `FRE-0006` ✓ |
| PRB-01 | `OBL-` ids | `FRE-0005` ✓ |
| PRB-02 | `JNT-` ids | `FRE-0005`, `FRE-0001`, `FRE-0004` ✓ |
| PRB-03 | `["None"]` | `FRE-0005`, `FRE-0007` ✓ |

**OBSERVED.** The same field, same contract requirement (Ambiguity/Freedom ids), is populated
correctly by `s03` in five of five cases where it appears, and incorrectly by `s03b` in six of six.

**POSSIBLE IMPLICATION.** This is not a model capability limit. Something differs between the two
stages' instruction or validation.

**NEEDS CROSS-READ (P5/P6).** The s03 vs s03b prompt and the validator for this field.

### 5.6 `termination_strategy` is anti-correlated with compliance

BM-001 gives `ELASTICITY` to the rigid closure and `LATER_BODY_COVER` to the compliant catch.
BM-002 gives `ELASTICITY` to two rigid members in a case with no compliance at all. BM-003 gives
`ROTATION` to the three compliant members. **Three of three benchmarks invert it.** PRB-01 is the
only correct use. PRB-02 and PRB-03 use `NONE`/`LATER_BODY_COVER` throughout.

### 5.7 Assembly `activates` treats interfaces as membership, not events

BM-002's ASY-0001 places BOD-0001 first and activates IFC-0001 and IFC-0004, whose partner bodies
arrive at steps 2 and 4. Every BM-002 interface is activated by two steps. In PRB-01 and PRB-03,
**no interface is activated by any step.** In PRB-03 every step activates every configuration.

### 5.8 Universals

`scale.basis: "RELATIVE"` and `scale.absolute: null` in **6/6**. Every envelope
`maturity: "PROVISIONAL"` in **6/6**. `elimination.eliminated: false` in **6/6** — the S04A
selection gate eliminated nothing in any case. No swept path or sampling in **6/6**.

---

## §6 UPSTREAM → DOWNSTREAM INFORMATION FLOW

**The producer supplies more than the consumer uses.** This is the opposite of the failure mode
I expected. The recorded S02 fixtures are rich: derivation premises, role→principle dicts, prose
obligations-created, mechanism-specific acceptance predicates, `reacted_at_role` on every load
case, and carefully-reasoned unresolved items. The loss is at **S02 → S03**.

Concretely, in the three cases where I read the upstream in full:

| Upstream content | Fate at S03/S04 |
|---|---|
| `BOUND_MOTION: HARD_STOP` (BM-003, PRB-03) | no stop, no limit, no relation |
| *"a bounded stroke set by the crank radius"* (BM-002) | crank radius = 0 |
| `reacted_at_role` on every load case (all) | no load path reaches a reaction site |
| `"approximately 1 kg"` (BM-002) | no dimensional commitment anywhere |
| ACT-0002, the machine (PRB-03) | absent from every functional region |
| UNR-0002, UNR-0004 (BM-003); UNR-0002 (BM-002) | silently decided, not carried to S3U |
| `evidence_route_verdict.available: false` on CND-0003 (BM-003) | its mechanism adopted anyway |
| OBL-0008 `satisfiable_at: "s04"` (PRB-03) | `assembly_directions: []` |

And per §2, the live model does not produce this upstream richness in the first place. So the
pipeline as measured has an information channel that is **wide in the fixtures and narrow in
reality**, feeding a consumer that uses little of either.

---

## §7 CLASSIFICATION SUMMARY

**SUPPORTED / strong reasoning.** PRB-01's body decomposition (explicit hard stop, return spring,
FIXED joint with empty DOF) and its BLK-0001..0004 hard-stop relations. BM-002's crank-slider body
and joint-type decomposition. PRB-02's HELICAL choice and its three s03 unresolved items.
BM-003's s04a 120° envelope symmetry. The `unresolved` layer generally: S3U-1001..1004 in PRB-01,
S3U-1001/1002 in PRB-02, S3U-1001 in BM-003 and PRB-03 all diagnose real gaps in correct language
— **in several cases the unresolved layer correctly names the defect the same file just committed.**

**PHYSICALLY INCONSISTENT.** BM-002's parallel input/output axes and stationary input; BM-002's
zero-length crank; BM-003's non-folding folding stand; BM-003's blocked-direction/defeat-motion
sign inversion; PRB-03's rigid spring; the six grounding degeneracies; every coincident joint in
§3.1; the joints outside their bodies in §3.2; the cyclic load paths in BM-003 and PRB-01.

**MISSING ENGINEERING REASONING.** No swept evidence in any case; `irrelevance` empty in four;
`defeat_specification: "None"` in PRB-02; `elimination` never exercised; `scale.absolute` never set.

**PREMATURE COMMITMENT.** BM-002's S3U-0001 declares the input axis orientation open while
JNT-0001 already commits `+Z` and s04a/s04b build on it. BM-003 decides UNR-0002 and UNR-0004
without record. BM-003 adopts a mechanism whose evidence route the upstream declared unavailable.

**UNJUSTIFIED ASSUMPTION.** PRB-01's *"typical linkage arrangement"* notes field; PRB-02's and
PRB-03's phantom/free-text bodies (`"desk edge"`, `"arm"`).

**LEGITIMATELY DEFERRED.** BM-003's S3U-1001 on the missing ground body; PRB-01's four unresolved
items; PRB-02's S3U-1001/1002; PRB-03's S3U-1001 on the unblocked `+Z` and `RX`/`RY`.

---

## §8 QUESTIONS CARRIED TO P5 / P6

1. Where is the s04a → s04b handoff, and why does BM-003's correct 120° envelope geometry not
   reach joint placement? (§3.3 — the sharpest single lead in P4A.)
2. Why is `kept_open_by` correct in `s03` and wrong in all six `s03b` outputs? (§5.5)
3. Is any enumeration in §5.4 enforced anywhere, or are all these fields free strings?
4. Does anything reject a free-text string in a body-reference field? (`"desk edge"` survived
   s03 → s03b → s04a.)
5. Is the DOF grid actually derived, and what does it do with a cell that is both BLOCKED and
   IRRELEVANT (BM-002), or a DOF that is BLOCKED and changes in `s04b` (PRB-01, PRB-02, BM-002)?
6. Can `BlockingRelation` express a bounded range at all, or only a full block? (PRB-01's hard
   stop had to be recorded as "this motion is impossible".)
7. Is there any check that a joint origin lies within the bodies it connects, or that two joints
   are not coincident?
8. What consumes `transitions`, given none carries a path or sampling declaration?
9. Does the S04A `elimination` gate have any condition that can fire?
10. Which stage, if any, is responsible for the S02 `principle` shape difference in §2 — and was
    the S03 stage ever exercised on live S02 output?

**Question 10 is the one that most affects the audit's ninth objective.** On the evidence read so
far, Window 2 does not measure whether the pipeline helps an inexpensive model reason like a
competent mechanical designer; it measures whether the model can elaborate a hand-authored
engineering brief. Answering that properly requires the artifacts listed in §0.4.

---
---

# §A — SECOND EVIDENCE PASS: RAW MODEL AND PROVENANCE

## §A.0 CURRENT COVERAGE LEDGER (supersedes §0)

### Read completely — added in this pass

**Upstream fixtures (7 of 7 outstanding, now 13 of 13 total):**
`probes/PRB-01/s01.json` (277 L), `probes/PRB-01/s02.json` (457 L),
`probes/PRB-01/s02.pre_revision.json` (41 L), `probes/PRB-02/s01.json` (243 L),
`probes/PRB-02/s02.json` (414 L), `fixtures/responses/BM-002/s01.json` (317 L),
`fixtures/responses/BM-003/s01.json` (525 L).

**Window-2 raw model evidence:** `window2/r_final/model_run_records.json` — all 24
records enumerated; record 0 (BM-001 s03) read in full including its 32,507-character
`prompt_text`; record 3 (BM-001 s04b) prompt and raw response read in full; the
`raw_text` of all 24 compared byte-for-byte against the 24 stored artifacts (§C.1).

**Window-1 raw model evidence:** `deepseek/q6_fix/model_run_records.json` — all 36
records enumerated on status, model, determinism, truncation and token caps;
`deepseek/q6_fix/trials.json` — all 18 trial entries enumerated on counts, failures,
projection families and unused-family accounting.

**Window-1 live S02 responses (8 of 17):** `BM-001/t1`, `BM-001/t2`, `BM-002/t1`,
`BM-002/t2`, `BM-003/t1`, `BM-003/t2`, `PRB-01/t1`, `PRB-02/t1`, `PRB-02/t2`,
`PRB-03/t1`. (Ten files; `BM-003/t3` has no s02 — see §C.4.)

### NOT read — remaining, stated plainly

- **Window-1 s01 responses: 0 of 18 read.** No claim in this document rests on them.
- **Window-1 s02 responses: 7 of 17 unread** — `BM-001/t3`, `BM-002/t3`, `PRB-01/t2`,
  `PRB-01/t3`, `PRB-02/t3`, `PRB-03/t2`, `PRB-03/t3`.
- Both `model_run_records.json` and both `trials.json` were read **structurally in
  full** (every record, every field name and value on the fields listed above) plus
  two records in full prose. The remaining 58 `prompt_text` / `raw_text` bodies in
  those files were not read as prose.

**P4A is therefore NOT closed.** The §11 stop condition is not met on two counts:
the Window-1 response corpus is 10/35, and the run-record prose is 2/60. Everything
below is scoped to what was actually read and is labelled accordingly.

---

## §B — FIXTURE PROVENANCE, FROM RAW METADATA ONLY

| Artifact | `authored_by` | `pairing_history` | `_meta` present | **Label** |
|---|---|---|---|---|
| `probes/PRB-01/s01.json` | `agent-in-repository` | yes | yes | **AGENT_IN_REPOSITORY** |
| `probes/PRB-01/s02.json` | `agent-in-repository` | yes | yes | **AGENT_IN_REPOSITORY** |
| `probes/PRB-01/s02.pre_revision.json` | `agent-in-repository` | no | yes | **AGENT_IN_REPOSITORY** |
| `probes/PRB-02/s01.json` | `agent-in-repository` | yes | yes | **AGENT_IN_REPOSITORY** |
| `probes/PRB-02/s02.json` | `agent-in-repository` | yes | yes | **AGENT_IN_REPOSITORY** |
| `probes/PRB-03/s01.json` | `agent-in-repository` | yes | yes | **AGENT_IN_REPOSITORY** |
| `probes/PRB-03/s02.json` | `agent-in-repository` | yes | yes | **AGENT_IN_REPOSITORY** |
| `fixtures/responses/BM-001/s01.json` | **absent** | absent | yes (sha only) | **UNKNOWN** |
| `fixtures/responses/BM-001/s02.json` | **absent** | yes | yes | **UNKNOWN** |
| `fixtures/responses/BM-002/s01.json` | **absent** | yes | yes | **UNKNOWN** |
| `fixtures/responses/BM-002/s02.json` | **absent** | yes | yes | **UNKNOWN** |
| `fixtures/responses/BM-003/s01.json` | **absent** | yes | yes | **UNKNOWN** |
| `fixtures/responses/BM-003/s02.json` | **absent** | yes | yes | **UNKNOWN** |

**All seven PRB fixtures carry an explicit `authored_by: "agent-in-repository"`.
No BM fixture carries any `authored_by` key.** Five of six BM fixtures carry the same
`pairing_history` sentence as the PRB files — *"re-paired after the response-schema
section was added to the prompt; content unchanged and re-verified against the parser,
contract validation and completeness check"* — but similarity is not provenance, and
per §5 of the instruction the BM fixtures are recorded as **UNKNOWN**. No `run_id`,
`generated_by`, `source response reference` or model/provider field appears in any of
the thirteen.

### §B.1 Engineering content present in the fixtures and absent from live output

Exact fields, no attribution of who inserted them:

- **`_meta.reasoning_note`** — `PRB-01/s02.pre_revision.json`: *"No function class in
  the offered library performs SEPARATION OF ONE ITEM FROM A GROUP… the separation
  itself is recorded as unserved rather than invented."* `PRB-03/s02.json`: *"Two
  obligations here sit outside mechanics: producing a signal, and a machine receiving
  it. Both are recorded with the boundary named rather than dropped or mechanised."*
  `PRB-02/s02.json`: *"Its central obligation - not slipping or rotating - is a
  friction claim with no available route."*
- **`_meta.revision_note`** — `PRB-01/s02.json` names its own superseded file.
- **`candidates[].principle` as a role→principle mapping** of 5–7 keys.
- **`candidates[].obligations_created` as prose commitments** — e.g. BM-002:
  *"a bounded stroke set by the crank radius"*; BM-003: *"retention of the blocking
  member itself"*; PRB-03: *"radial support and axial retention at the turning connection"*.
- **`acceptance_contracts[].predicates` specific to the candidate's mechanism** — e.g.
  BM-003 ACC-0001 *"with the member in place, no continuous path leads from deployed
  toward folded"* vs ACC-0003 *"the deployed configuration lies past the toggle point"*.
- **`obligations[].satisfiable_at: "s05"`** — `PRB-01/s02.json` OBL-0008 only.

---

## §C — RAW MODEL RESPONSE → STORED ARTIFACT

### §C.1 Window 2: the stored artifacts are the raw responses

`model_run_records[i].response.raw_text` compared to the corresponding
`responses/<case>/t1_CND-0001/<stage>.json`, all 24 pairs:

| | s03 | s03b | s04a | s04b |
|---|---|---|---|---|
| BM-001 | SAME (4966 B) | SAME (6096 B) | SAME (2040 B) | SAME (824 B) |
| BM-002 | SAME (4561 B) | SAME (6199 B) | SAME (1967 B) | SAME (919 B) |
| BM-003 | SAME (8370 B) | SAME (7251 B) | SAME (2857 B) | SAME (1575 B) |
| PRB-01 | SAME (7128 B) | SAME (9439 B) | SAME (2960 B) | SAME (1652 B) |
| PRB-02 | SAME (5809 B) | SAME (5080 B) | SAME (2341 B) | SAME (1590 B) |
| PRB-03 | SAME (3831 B) | SAME (3810 B) | SAME (1375 B) | SAME (671 B) |

**24 of 24 byte-identical.** No field renamed, no shape changed, no value changed, no
field added, no field dropped, nothing normalised or repaired between the model's text
and the file on disk.

**Consequence for §9 of the instruction.** Every engineering defect recorded in §3, §4
and §5 of this document is **DEEPSEEK_AUTHORED**. The coincident joint origins, the
zero-length crank, the joint outside its body, the non-folding stand, the self-blocking
relations, the cyclic load paths, the `"desk edge"` and `"arm"` free-text hops, the
`"None"` defeat specifications, the vocabulary drift — all of it is in the model's own
response text. None of it is a stored-artifact artefact.

### §C.2 What the stage prompt asks for — three findings that reclassify earlier ones

Read in full from `window2/r_final/model_run_records.json` record 0 (`s03`) and
record 3 (`s04b`).

**(a) The s04b schema has no path and no sampling field.** Verbatim:

```
  joint_placements[]   joint, origin [x,y,z]
  state_coordinates[]  configuration, coordinates {<joint id>: number}
  transitions[]        id "TRN-0001", from_configuration, to_configuration,
                       moving_groups[]
  notes                string, may be ""
```

§3.4 recorded that no transition in any case carries a path, sampling declaration or
swept volume. **That is correct as an observation and is not a model omission — the
stage never asks for one.** The same prompt also says *"Where each JOINT sits — its
frame origin … and the axis it turns or slides about"*, while the schema provides
**no field for the axis**. The instruction and the schema disagree inside one prompt.

**(b) The s03 prompt's `interaction_kind` enumeration carries no `DECLARED_` prefix.**
Verbatim: `interaction_kind    CONTACT | CLEARANCE | INTERFERENCE_FIT | COMPLIANT_INTERACTION`.
**§5.4's row saying the contract prefix "is dropped in every case" is corrected:** the
model emitted exactly the values the prompt permits. The divergence is between the
prompt and the contract enumeration recorded in P2, not between the model and either.

**(c) `required_by_actors` and `reach_targets` are demanded by the s03 prompt.**
Verbatim: `functional_regions[] id "FRG-0001", role, owning_bodies[],
required_by_actors[] … reach_targets[] (what those actors must reach through it)`.
The BM-001 narrative in §4 called these *"fields no contract defines (P2 §4.7)"*.
**Corrected: they are undefined in the contract and explicitly required by the prompt.**

Two further observations on the s03 prompt, recorded without explanation:
its numbered RULES run **1, 2, 3, 4, 5, 6, 9** — there is no rule 7 or 8; and the
blocks `RESPONSE SCHEMA (from functional_regions) / PERMITTED VALUES / IDS YOU EMIT
ARE NEW / REFERENCES BETWEEN ITEMS` appear **twice, verbatim**, inside one prompt.

### §C.3 Fields present in the typed state and absent from the stored stage artifact

From record 3's `THE MECHANISM AND ITS ARRANGEMENT` block (the s04b input):

| Entity | Field in typed input | In the stored s03/s03b artifact? | Status |
|---|---|---|---|
| `AssemblyStep` | `insertion_direction: [0,0,1]` | **no** | **FIELD ADDED** |
| `Configuration` | `expected_mobility: []` | **no** | **FIELD ADDED** |
| all | `_created_by`, `_family`, `_provenance`, `created_by_stage` | no | **FIELD ADDED** |

`AssemblyStep._provenance` is `"s03b:relations"` while `_created_by` is `"s03"` —
the two sub-stages are distinguished in one field and merged in the other.
**STATUS: UNEXPLAINED UNTIL P5.**

### §C.4 Execution facts from both run-record files

Applies to **all 24 Window-2 records and all 36 Window-1 records**:

- `model_id_requested: "deepseek-chat"` → `model_id_served: "deepseek-v4-flash"`, with
  `model_substitution: "provider served … recorded rather than assumed equivalent"`.
- `determinism.temperature_requested_by_stage: 0.0`,
  `determinism.temperature_actually_sent: 1.0`, `seed: null`, `seed_honoured: "UNKNOWN"`.
  **Every one of the 60 calls asked for temperature 0.0 and sent 1.0.**
- `max_output_tokens_clamped_from: 32000` → `max_output_tokens: 8192` on all 60 calls.
- Window 2: 24/24 `SUCCESS`, 0 truncated, `finish_reason: "stop"`, no retries, no errors.
- Window 1: **35/36 `SUCCESS`; record 29 is `RESPONSE_TRUNCATED`** with
  `finish_reason: "length"` and `truncated: true`. This is why
  `q6_fix/responses/BM-003/t3/` contains `s01.json` and **no `s02.json`** — the file
  count is 35, not 36, and the missing artifact is a truncation at the 8192 clamp.
- `reasoning_content_present: false`, `reasoning_content_stored: false` throughout.
- Window-2 `stage_id` is `"s03"` for both the s03 and s03b calls and `"s04"` for both
  s04a and s04b: **the run record cannot distinguish the sub-stages.**

### §C.5 `trials.json` records checks that fire and do not block

`q6_fix/trials.json` holds 18 entries (6 cases × 3 trials) with `counts`, `failures`,
`projection_families`, `unused_s01_families`, `s01_status`, `s02_status`, timings, and
`s01_provider`/`s02_provider` = `"deepseek (live)"`.

Observed `failures[]` entries are `kind: "CHECK_FINDING"`, e.g.
`LOADCASE_ROLE_READS_AS_A_PART: LC-0002.applied_to_role -> 'the latch'` (BM-001 t1),
`LOADCASE_NAMES_A_PART: LC-0003 -> 'the housing'` (BM-002 t1).
**Both trials still record `s02_status: "SUCCESS"`.** A check exists, it fires, it
names the defect precisely, and it does not change the outcome.
**STATUS: UNEXPLAINED UNTIL P5.**

`unused_s01_families` on BM-002 t1 reads **`"Freedom: 4/4 unreferenced"`** — the
repository's own instrumentation measuring upstream information that reached no
consumer. This corroborates §6 from a source independent of my reading.

Counts also show live S01 extracting far less than the fixture: BM-001 t1 records
`Ambiguity: 2, Freedom: 1` against the fixture's six and six.

---

## §D — LIVE S02 vs WINDOW-2 FIXTURE, PER CASE

### §D.1 CORRECTION to §2 — the `principle` shape claim was over-general

§2 stated that in live model output the principle channel *"is a single string."*
Across the ten live s02 files read, that is **true in nine and false in one**:

| Case / trial | `family` shape | `principle` shape | Example |
|---|---|---|---|
| BM-001 t1 | string | **string** | `"DETENT_OR_SNAP"` |
| BM-001 t2 | string | **string** | `"FRICTION_HOLD"` |
| BM-002 t1 | string | **string** | `"SCREW_AND_NUT"` |
| BM-002 t2 | string | **string** | `"CAM_AND_FOLLOWER"` |
| BM-003 t1 | string | **string** | `"OVER_CENTRE"` |
| BM-003 t2 | string | **string** | `"PLANAR_PAIR"` |
| PRB-01 t1 | string | **string** | `"INDEXING_ROTOR"` |
| PRB-02 t1 | string | **string** | `"DIRECT_MANUAL"` |
| PRB-02 t2 | string | **string** | `"SCREW_AND_NUT"` |
| **PRB-03 t1** | **array of 8** | **array of 8** | `["REVOLUTE_PAIR","CRANK_SLIDER","DETENT_OR_SNAP","HARD_STOP","JOURNAL_SUPPORT","DIRECT_BEARING","STRAIGHT_INSERTION","DIRECT_MANUAL"]` |
| all 13 fixtures | string | **dict of 5–7 keys** | `{ACTUATE: …, BOUND_MOTION: …, …}` |

**Corrected statement.** The same field takes **three incompatible shapes** in the
corpus — bare string, parallel array, and role→principle dict — and the shape is not
stable even within live output. PRB-03 t1's array carries the same information content
as the fixture's dict, positionally paired against a parallel `family` array. The
narrower and better-supported finding is: **the field has no enforced shape**, and in
nine of ten live files read it carries one principle where the fixture carries five to
seven. Seven live s02 files remain unread; this table is not a population claim.

### §D.2 Per-case comparison

**BM-001** — fixture UNKNOWN, 13 obligations, dict principle, ACC predicates
mechanism-specific. Live t1: 12 obligations of which **OBL-0005 and OBL-0012 have
byte-identical statements**; `principle` string; **all five candidates address the same
12 obligations and all five acceptance contracts carry the identical five predicates**
— *"Repeated operation passes 1000 cycles without failure"*, *"5N force"*,
*"between 2N and 10N"*, *"ABS plastic via injection molding"*, *"Assembly time less
than 30 seconds"*. Every requirement in BM-001's s01 has `quantity_class: "NONE"`.
**The live model fabricated five numeric acceptance thresholds from an input carrying
no quantity.** Live t2, same case, same prompt: **`predicates: []` on all three
contracts**, and all three candidates `evidence_route_verdict.available: false`.
**STRUCTURE REDUCED; and unstable between trials of one case.**

**BM-002** — fixture 14 obligations, six candidates, dict principle, `obligations_created`
naming *"a bounded stroke set by the crank radius"*. Live t1: 14 obligations, three
candidates, string principle, `obligations_created: ["OBL-0007","OBL-0008"]` identical
across all three; ACC predicates identical across all three but do at least carry the
real quantities (80–100 mm, 1 kg). Live t2: four candidates; **`self_locking` absent
from all four** though present in t1; **CAM_AND_FOLLOWER marked `available: true`
where the fixture marks the same principle `available: false`**; ACC obligation lists
and ACC predicates are **disjoint sets**. **STRUCTURE REDUCED.**

**BM-003** — fixture 17 obligations with derivation premises, six candidates, four
mechanism-specific contracts. Live t1: 28 obligations, ~10 of them restatements, no
`derivation_premises`, three candidates with identical 25-obligation lists and identical
8 predicates, four of eight load cases `reacted_at_role: "the user's hand"`. Live t2:
20 obligations **with** derivation premises; `obligations_created: ["OBL-0021","OBL-0022"]`
and acceptance contracts citing OBL-0021…OBL-0026 — **six obligation ids that exist
nowhere in the file**; and `predicates: ["All obligations are satisfied by the candidate
design."]` on all three contracts. **STRUCTURE REDUCED.**

**PRB-01** — fixture AGENT_IN_REPOSITORY, `METER_DISCRETE_QUANTITY` family, five
candidates, OBL-0008 at s05. Live t1 selects the same family and four of the same
principles (`INDEXING_ROTOR`, `GATED_PAIR`, `ESCAPEMENT`, `SINGLE_ITEM_POCKET`) —
**the library transfers correctly** — but `obligations_created` is identical across all
four candidates and every ACC predicate is a restatement of an obligation, identical
across all four contracts. OBL-0002 (*"a volume that holds approximately twenty items"*)
is routed to `MATERIAL_PROPERTY_ANALYSIS`; the fixture routes it to
`RIGID_KINEMATIC_GEOMETRY`. **STRUCTURE REDUCED.**

**PRB-02** — fixture five candidates across `MAINTAIN_CONFIGURATION` and `RETAIN_BODY`.
Live t1: **all three candidates have `family: "ACTUATE"` and `principle: "DIRECT_MANUAL"`
— the same value** — and UNR-0001's alternatives are
`["DIRECT_MANUAL","DIRECT_MANUAL","DIRECT_MANUAL"]`. Live t2: `self_locking: null` on
CND-0003 (a third value for that field); ACC predicates of the form *"Obligation
OBL-000N is satisfied if <restatement of OBL-000N>"*; OBL-0001's `derivation_premises`
contains *"Contents that cannot be reached are not stored."* — **a premise about stored
contents in a clamp case**. OBL-0002 (the 18–40 mm span) is routed
`TOLERANCE_ANALYSIS / available:false` in t1 and `SWEPT_INTERFERENCE / available:true`
in t2. **STRUCTURE REDUCED; and route availability unstable between trials.**

**PRB-03** — fixture's `_meta.reasoning_note` explicitly refuses to mechanise the
signal and records the product boundary instead. Live t1 emits OBL-0002 *"translate a
press … into a signal sent to the machine"* and OBL-0010 *"a mechanism to transmit the
pedal motion to a signal (e.g., electrical switch, mechanical valve)"* —
**the same case, mechanised.** Its CND-0001 principle array includes `"CRANK_SLIDER"`
for a mechanism its own summary describes as a revolute pivot with a spring return.
**STRUCTURALLY DIFFERENT (array form); and the refusal the fixture records is absent.**

### §D.3 Does S03 receive information unavailable from live S02?

**Yes, for every case, on three specific channels.** The s03 `prompt_text` in record 0
shows the typed input carrying `principle` as the **dict** and `obligations_created` as
**prose commitments** — the fixture's forms. In the nine live s02 files with a string
`principle`, neither is available. Concretely, S03 received for BM-001:

```
"principle": {"ACTUATE":"DIRECT_MANUAL", "BOUND_MOTION":"HARD_STOP",
  "MAINTAIN_CONFIGURATION":"DETENT_OR_SNAP", "PERMIT_ASSEMBLY":"ELASTIC_INSERTION",
  "PERMIT_RELATIVE_MOTION":"REVOLUTE_PAIR", "RETAIN_BODY":"ELASTIC_CAPTURE"},
"obligations_created": ["radial support and axial retention for the rotating relation",
  "a deflection bound and a recovery for the catch", "a bound on the open travel"]
```

Live BM-001 t1 offers `"principle": "DETENT_OR_SNAP"` and
`"obligations_created": ["OBL-0001","OBL-0002","OBL-0003"]`.

**The Window-2 S03/S04 results are therefore not evidence about a live S01→S04 chain.**
They measure S03/S04 given upstream that is richer than, and structurally different
from, what the same provider produces at S02.

---

## §E — CORRECTIONS TO EARLIER STATEMENTS

1. **§2, "in live model output that channel is a single string."** Over-general.
   Corrected in §D.1: nine of ten live files read, not all; PRB-03 t1 uses parallel
   arrays carrying equivalent content. Seven live s02 files remain unread.
2. **§2, "`derivation_premises` absent from all 28."** True of BM-003 t1 only.
   BM-001 t1/t2, BM-002 t1/t2, BM-003 t2, PRB-01 t1, PRB-02 t1/t2 and PRB-03 t1 all
   carry them. **The absence is a BM-003-t1 fact, not a live-output property.**
3. **§5.4, `interaction_kind` — "the prefix is dropped in every case."** Corrected in
   §C.2(b): the s03 prompt's enumeration has no prefix. Prompt-vs-contract divergence.
4. **§4 BM-001, `required_by_actors` / `reach_targets` "defined in no contract."**
   Corrected in §C.2(c): undefined in the contract, explicitly required by the prompt.
5. **§5.4, `activates` — "BM-001/2 only IFC-".** Wrong. BM-001's ASY-0003 activates
   `["JNT-0001","IFC-0001","IFC-0003"]`. BM-001 mixes JNT- and IFC- ids, as BM-003 does.
6. **§3.4, "no swept evidence in any case."** The observation stands; the attribution
   is corrected by §C.2(a) — the s04b schema does not request a path or sampling.
7. **§1 provenance table, BM fixtures labelled RECORDED FIXTURE INPUT.** Corrected in
   §B to **UNKNOWN**: no `authored_by` key exists in any of the six.

Two earlier statements are **confirmed and strengthened**, not corrected: §C.1 shows
every §3–§5 defect is DEEPSEEK_AUTHORED, and §C.5 shows the repository's own
`unused_s01_families` instrumentation independently records the §6 information loss.

Two further facts, recorded without explanation:
**two of six cases ran S03/S04 on a candidate whose own
`evidence_route_verdict.available` is `false`** — BM-001 CND-0001 (*"the catch holds by
deflecting; no route here can establish its force"*) and PRB-02 CND-0001 (*"the hold is
friction"*). Both directories are named `t1_CND-0001`. And in **all six cases the
Window-2 selection is CND-0001**, the first candidate by id.

---

## §F — UNRESOLVED TRANSFORMATIONS CARRIED INTO P5

Each is an observed difference with no root cause assigned.

1. `AssemblyStep.insertion_direction` and `Configuration.expected_mobility` appear in
   the s04b typed input and in no stored s03/s03b artifact. Where are they produced?
2. `_provenance: "s03b:relations"` vs `_created_by: "s03"` on the same entity; and the
   run record's `stage_id` collapses s03/s03b and s04a/s04b into one label each.
3. `temperature_requested_by_stage: 0.0` → `temperature_actually_sent: 1.0` on 60/60 calls.
4. `max_output_tokens` clamped 32000 → 8192 on 60/60 calls, causing the one
   `RESPONSE_TRUNCATED` failure that left `BM-003/t3` without an s02 artifact.
5. `CHECK_FINDING` entries (`LOADCASE_ROLE_READS_AS_A_PART`, `LOADCASE_NAMES_A_PART`)
   are recorded in `trials.json` while the trial reports `s02_status: "SUCCESS"`.
6. `unused_s01_families: "Freedom: 4/4 unreferenced"` is computed and recorded. What,
   if anything, consumes it?
7. The s03 prompt omits rules 7 and 8 and duplicates a ~1,500-character block.
8. The s04b prompt asks for a joint axis its own response schema cannot hold; and asks
   for no path or sampling, which the S04 contract (per P2) requires as swept proof.
9. `interaction_kind` and `functional_regions[].required_by_actors` / `reach_targets`:
   prompt and contract disagree on the permitted values and on the field set.
10. Selection is `CND-0001` in 6/6 cases including 2 whose evidence route is declared
    unavailable. Is the selection gate indexed rather than evidence-driven?

---
---

# §G — WINDOW-1 RAW S01: COMPLETE SUB-CORPUS (18/18)

All eighteen `ver3/live_runs/deepseek/q6_fix/responses/<case>/t<n>/s01.json` files read
beginning to end. This is the model's own extraction, read directly — not inferred from
any downstream state. Every statement in §G is scoped to these eighteen files.

## §G.1 Where the loss happens: S01 or later?

The instruction's §3 question, answered per item.

**ALREADY MISSING AT S01** (present in the fixture, absent from the raw live response):

| Fact | Fixture | Live S01 |
|---|---|---|
| Product-identity requirement | BM-003 REQ-0001, PRB-03 REQ-0001 | **no requirement emitted** in BM-003 t1 (clause dropped from `source_clauses` entirely), BM-003 t2, PRB-03 t1, PRB-03 t3 |
| Repetition of the return (*"every time"*) | PRB-03 REQ-0004, `verification_kind: QUANTITATIVE` → OBL-0004 `route_available: false` | **merged into the return requirement in all three PRB-03 trials**; no separate requirement exists |
| Slip vs rotate as two freedoms | PRB-02 REQ-0003 + REQ-0004 → OBL-0003 + OBL-0004 | **merged into one requirement in all three PRB-02 trials** |
| Wall type / permitted fixings | PRB-01 AMB-0005 (the wall is the reaction site for every load) | **absent in all three PRB-01 trials**; covered only as a freedom, never as an ambiguity |
| Signal scope — *"is producing it within this product's scope?"* | PRB-03 AMB-0001 | **absent in all three PRB-03 trials.** `FRE-000n` covers signal *type*; the product-boundary question is never raised |
| Knock-disturbance magnitude | BM-003 AMB-0005 (the reason the retention obligation is unverifiable) | **absent in all three BM-003 trials** |
| Assembly / installation scenario | PRB-01 SCN-0004, PRB-03 SCN-0003, BM-002 SCN-0003 | absent in PRB-01 t1/t2/t3, PRB-03 t1/t2/t3, BM-002 t1/t2 |

**PRESENT AT S01, LOST LATER** — one clear case, and it is chain-specific:
`ACT-0002` = *"the machine"* exists in the PRB-03 fixture **and** in live PRB-03 **t2**
(`must_reach: ["pedal (receives signal)"]`). It is absent from PRB-03 t1 and t3.
**§4's statement "ACT-0002 vanishes" is therefore correct only for the Window-2 chain**
(fixture upstream → S03), and is **CASE/TRIAL-SPECIFIC** for the live chain.

## §G.2 The one consistent strength

**Quantity handling is correct wherever the source states a quantity, in every trial read.**
BM-002 (80–100 mm, 1 kg): `quantity_kinds: ["length"]`/`["mass"]`, `quantity_class: "BAND"`,
`directionality: "vertical"` — t1, t2, t3. PRB-01 (twenty, exactly one):
`quantity_class: "BAND"` and `"MAGNITUDE"` respectively — t1, t2, t3, matching the fixture
exactly. PRB-02 (18–40 mm): `["length"]` + `BAND` — t1, t2, t3.

The converse also occurs: **quantity kinds are invented where the source has none.**
BM-001 t2 records `["count"]`, `["force"]`, `["cost"]` on clauses containing no quantity
(t1 and t3 of the same case record `[]`). PRB-02 t1/t2/t3 all record `["force"]` on
*"must not slip or rotate"*, which names no force. BM-003 t2 records `["length"]` on
*"narrow and compact"*.

## §G.3 Field-level shape findings across 18 files

**`source_clauses[].locator` — nine distinct conventions, none repeated across all trials
of a case:** `REQ-001` (BM-001 t1 — points at a requirement id), `clause 1` (BM-001 t2,
PRB-01 t2), `SRC-0001` (BM-001 t3, BM-003 t2, PRB-02 t2 — self-referential), `L1`
(BM-002 t1, PRB-02 t1, PRB-02 t3, PRB-03 t2), `req-intro` (BM-002 t2), `1` (BM-002 t3),
`intro`/`para1` (BM-003 t3), `Request-1` (PRB-03 t1), `request-1` (PRB-03 t3),
`line 1`/`line 1-2` (PRB-01 t3). Fixture uses `sentence-1` / `para-2-s1`.

**`ambiguities[].block_scopes` — the fixture vocabulary
(`blocks_quantitative_acceptance` | `blocks_PASS` | `blocks_evidence_interpretation`)
is used in 0 of 18 files.** Live populations observed: `REQ-` ids (BM-001 t1/t2/t3,
BM-003 t2/t3, PRB-03 t1/t2/t3, PRB-02 t1(prose)/t2/t3); `SCN-` ids (BM-002 t2, PRB-01 t2);
free prose (BM-002 t1 `"platform travel specification"`, PRB-02 t1
`"Structural design of the clamp"`); a **mis-cased id** (`"ReQ-0003"`, BM-002 t2);
empty `[]` (BM-003 t1, PRB-01 t1); and **the key absent entirely** (PRB-01 t3 AMB-0001 and
AMB-0002, PRB-02 t2 AMB-0002).

**`source_clauses[].directionality`** — the fixture's enumerated values appear in
**PRB-03 t3 only** (`downward`, `upward`, `lateral`). Elsewhere the field carries prose
echoed from the requirement text: `"different directions"`, `"direction I was not
expecting"`, `"back down"` (BM-003 t1); `"close to the body"`, `"unexpected direction"`
(BM-003 t3); `"sideways"` (PRB-03 t1/t2).

**`observable_verbatim`** is **byte-identical to `statement_verbatim`** for six
requirements in BM-003 t3 (REQ-0002, 0003, 0006, 0008, 0009, 0012) and is a lowercase
copy in PRB-03 t3. Elsewhere it is a paraphrase. The fixture's is a distinct
observable-level restatement (*"an enclosed volume that stores contents"*).

**Passive objects promoted to `actors`** — four instances: `"payload"` (BM-002 t1),
`"Small object"` (BM-003 t1, BM-003 t2), `"user's foot"` / `"User's foot"` (PRB-03 t1,
PRB-03 t3), `"Monitor arm"` (PRB-02 t2). Also `"external object"` (PRB-03 t2).
**`ACT-0002` denotes a different entity in different trials of one case**: `"payload"`
in BM-002 t1 and `"Assembler"` in BM-002 t3.

## §G.4 Requirement decomposition is trial-dependent, not stage behaviour

| Case | t1 | t2 | t3 | fixture |
|---|---|---|---|---|
| BM-001 | 5 clauses → 5 reqs (1:1) | 5 → 5 | **5 → 9 (decomposed)** | 5 → 10 |
| BM-002 | 7 → 7 | 6 → 6 | **6 → 9** | 6 → 11 |
| BM-003 | 14 → 14 | 15 → 14 | 15 → 14 | 15 → 19 |
| PRB-01 | 4 → 6 | 6 → 6 | 5 → 5 | 5 → 7 |
| PRB-02 | 4 → 4 | 4 → 4 | 4 → 4 | 4 → 6 |
| PRB-03 | 4 → **3** | 4 → 4 | 4 → **3** | 4 → 5 |

**In no case does any trial reach the fixture's requirement count.**

## §G.5 Same input, different answer across trials

- **`verification_kind` on identical requirement text.** BM-001 REQ-0005: `QUANTITATIVE`
  (t1) vs `STRUCTURAL` (t2). PRB-02 REQ-0003: `KINEMATIC` (t1), `KINEMATIC` (t2),
  `QUANTITATIVE` (t3). PRB-02 REQ-0004: `STRUCTURAL` (t1), `QUANTITATIVE` (t2),
  `KINEMATIC` (t3) — three trials, three values.
- **Scenario `kind` on the same activity.** PRB-01 refilling: `OPERATION` (t1),
  `SERVICE` (t2), `SERVICE` (t3). The fixture raises this exact question as AMB-0006 —
  *"Is refilling ordinary use or a maintenance activity?"* — and **the live model silently
  answers it differently in different trials without ever recording it as an ambiguity.**
  PRB-02 removal/relocation: `SERVICE` (t1), `OPERATION` (t2), `SERVICE` (t3).
- **Scenario count.** BM-001: 3 / 4 / 3. BM-003: 4 / 5 / 4. PRB-02: 3 / 2 / 3.
- **Ambiguity count.** BM-001: 2 / 3 / 6. BM-003: 3 / 2 / 3 (fixture 10).
  PRB-01: 4 / 1 / 2 (fixture 6). PRB-02: 3 / 2 / 1 (fixture 6).
- **Freedom count.** BM-001: 1 / 3 / 4 (fixture 6). PRB-02: 3 / 5 / 1 (fixture 6).

## §G.6 System-boundary placement of the load source

**PRB-02, all three trials, place the monitor arm INSIDE the system boundary**
(t1 SCN-0001 *"Inside: the clamp and the monitor arm it fixes"*; t2 both scenarios;
t3 all three scenarios). The fixture places it outside: *"the monitor arm and its load
are outside it and act on it"*. **BM-003 t2 SCN-0003 likewise places
*"the small object it holds"* inside.** A load source inside the boundary is not an
external load case. **STATUS: recorded, not explained.**

One boundary statement is notably correct: **PRB-01 t2 SCN-0001** records the items as
*"outside … (which enter and leave the boundary during operation)"*.

## §G.7 Self-contradiction within a single file

**BM-002 t2** — `AMB-0002` states *"The system boundary is not specified, so it is
ambiguous what loads must be reacted and where"*, while `SCN-0001` in the same file
declares a `system_boundary`. The same case's live s02 (t2) carries this forward as
`UNR-0002` with `alternatives: []`.

## §G.8 Genuine engineering reasoning observed in raw S01

- **BM-002 t3 AMB-0002**: *"the mechanism remains enclosed … could conflict with an
  external hand crank, which may be considered part of the mechanism"*, with
  `conflicting_clauses: ["SRC-0002","SRC-0004"]` correctly typed. This is the same
  conflict the fixture encodes as OBL-0007.
- **BM-002 t1/t2 AMB-0001**: the 80–100 mm total-vs-one-direction question — the fixture
  raises the same thing as AMB-0002.
- **PRB-01 t1 REQ-0002/0003/0004** decompose *"hold about twenty … release exactly one …
  never two at once"* into three requirements with `BAND` / `MAGNITUDE` / `NONE`,
  matching the fixture's structure.
- **PRB-03 t2** models the machine and the brushing object as distinct actors.

## §G.9 Coverage after this pass

- **Window-1 raw responses: 29 / 35.** s01 **18/18 complete**; s02 **11/17**.
  Unread: `BM-001/t3/s02`, `BM-002/t3/s02`, `PRB-01/t2/s02`, `PRB-01/t3/s02`,
  `PRB-02/t3/s02`, `PRB-03/t2/s02`.

  **`PRB-03/t3/s02` read in this pass sharpens §D.1.** Its `principle` is a
  **bare string** (`"LEVER_LINKAGE"`, `"CRANK_SLIDER"`, `"CAM_AND_FOLLOWER"`) while
  `PRB-03/t1/s02`'s is an **8-element array**. The shape is therefore unstable
  **within a single case**, not merely across cases. It also emits
  `predicates: []` on all three acceptance contracts (the second such instance,
  after `BM-001/t2`), `obligations_created: []` on all three, no `self_locking`
  field, `OBL-0005` with `derived_from_requirements: []`, `UNR-0002` with
  `blocks: []`, and `UNR-0001.why_open` populated with entity ids
  (`"AMB-0001 and FRE-0003"`) rather than a reason.
- **model-run prose bodies: 2 / 60.** Read in full: `window2/r_final` record 0
  (s03 prompt + response) and record 3 (s04b prompt + response). All 60 records were
  read structurally (status, model ids, determinism, truncation, token caps, purpose)
  and those results stand in §C.4; the remaining 58 `prompt_text` / `raw_text` bodies
  have **not** been read as prose.

**P4A remains open on these two counts.** No claim in §G depends on the unread files.

---
---

# §H — P4A CLOSE: RAW-MODEL AND PROMPT COVERAGE COMPLETE

## §H.1 Final inventory

**Window-1 raw responses: 35 / 35.** All 18 `s01.json` and all 17 `s02.json` under
`ver3/live_runs/deepseek/q6_fix/responses/<case>/t<n>/` read beginning to end.
(`BM-003/t3/s02.json` does not exist — see §H.6.)

**Model-run prose bodies: 60 / 60.** Composed as follows, every part read as text:

| Group | Records | Instruction block | Typed input | Response |
|---|---|---|---|---|
| `window2` s03 | 6 | 1 template, 7,349 ch, sha `d02b4c97` — **byte-identical across all six** | serialised upstream state | 6 raw texts |
| `window2` s03b | 6 | 1 template, 2,632 ch, sha `48bb6fec` — identical across six | serialised s03 state | 6 raw texts |
| `window2` s04a | 6 | **6 variants**, 3,491–3,707 ch — differ only in the per-case must-touch list (§H.4) | serialised s03/s03b state | 6 raw texts |
| `window2` s04b | 6 | 1 template, 1,529 ch, sha `af23fd63` — identical across six | serialised s03/s03b/s04a state | 6 raw texts |
| `q6_fix` s01 | 18 | **1 template**, sha `4b8f20b9` — identical across all 18 | the raw request text | 18 raw texts |
| `q6_fix` s02 | 18 | **1 template**, sha `e21e3a3e` — identical across all 18 | serialised s01 output | 18 raw texts |

Every distinct instruction template was read in full. The typed-input blocks are
serialisations of artifacts already read in full elsewhere; this was verified, not
assumed, by matching field values (§H.2) and by extracting the projected family set
of all 18 s02 prompts (§H.5).

## §H.2 Every stored artifact in both windows is the raw model text

Extending §C.1 to Window 1: `response.raw_text` compared byte-for-byte and by parsed
JSON against every stored response file.

- **Window 2: 24 / 24 identical.**
- **Window 1: 35 / 35 identical, 0 differing.** The 36th record is the truncation.

**59 of 59 stored artifacts across both windows are byte-identical to the model's own
response text. There is no deterministic transformation anywhere in either window** —
nothing renamed, repaired, defaulted, normalised or dropped between the provider's
text and the file on disk.

## §H.3 The `principle` shape — §2's headline is INVERTED

The `q6_fix` s02 prompt's PERMITTED VALUES block reads, verbatim:

```
  family            one of the FUNCTION CLASSES listed above
  principle         one of the PRINCIPLE FAMILIES listed above
```

**Singular. One family, one principle, per candidate.** Therefore:

| Form | Count | Verdict against the prompt |
|---|---|---|
| bare string (live) | **15 / 17** | **compliant — exactly what is asked** |
| parallel arrays (live: `BM-001/t3`, `PRB-03/t1`) | 2 / 17 | violates the schema |
| role→principle dict (fixtures) | **13 / 13** | **violates the schema** |

**§2 stated that the dict "is the channel through which S02 tells S03 what kind of
machine to build" and that live output is deficient because it emits a string. That is
corrected: the prompt asks for a single principle, the live model complies, and the
enrichment lives in the fixtures, which do not conform.**

The downstream consequence survives and sharpens: **Window-2 S03 was fed a six-key
role→principle map that no prompt-conforming S02 output would ever contain.** The
attribution moves from "model shortfall" to **fixture-vs-prompt divergence**.

**The prompt contradicts itself on this point.** Rule 3 says *"A candidate names the
FUNCTION CLASSES it must perform and the PRINCIPLE FAMILY it uses for each"* — a
mapping — while PERMITTED VALUES says *"one of … one of"*. Both live forms are
readings of one prompt. **STATUS: UNEXPLAINED UNTIL P5.**

## §H.4 What the prompts actually ask — findings that reclassify earlier ones

**`obligations_created` — §2 and §D were backwards.** s02 Rule 4, verbatim:
*"obligations_created holds the IDS of obligations you already wrote in the obligations
list under rule 1 — it is a reference list, not a place to introduce something new. If
you find yourself needing an id that is not already in that list, the omission happened
back at rule 1."* **The live model's OBL- ids are compliant; the fixtures' prose
commitments violate the rule.** And `BM-003/t2` (OBL-0021…0026) and `BM-001/t3`
(OBL-0022…0024) are precisely the failure Rule 4 predicts.

**`"the body the product grips"` is the prompt's own example**, not cross-case
contamination. s02 Rule 2 lists the role examples *"the surface the product stands on",
"the body the product grips", "the moving closing role"*. `BM-001/t3`'s use of it is a
copy of the instruction.

**Load reaction — finding strengthens.** Rule 2: *"Every load terminates somewhere
OUTSIDE the product … a load reacted against the product itself has not been reacted."*
`PRB-02/t3` LC-0004 reacts at *"the clamp body"*; `PRB-01/t2` LC-0001 both applies and
reacts at *"the wall"*, omitting the product. Rule 2 also bans naming a part —
*"`base`, `housing`, `PLATFORM`, `box_body` all name things that do not exist yet"* —
which is exactly what `trials.json`'s `LOADCASE_ROLE_READS_AS_A_PART` and
`LOADCASE_NAMES_A_PART` findings flag, non-blockingly (§C.5).

**`satisfiable_at` — the fixture violates the rule.** Rule 1: *"an obligation about
elements, contacts or dimensions is not satisfiable at s02 and must say so."* The
first-pass finding that `BM-001` fixture OBL-0003 is `satisfiable_at: "s02"` with
`evidence_route: SWEPT_INTERFERENCE` now has its governing rule. **Confirmed.**

**Rule 7 — "Never name a dimension or a position."** `BM-001/t1`'s acceptance
predicates (*1000 cycles, 5N, 2N–10N, ABS via injection molding, 30 seconds*) and
`BM-001/t3`'s (*X N, Y N, Z degrees*) violate it directly. **Strengthens.**

**Route availability is given in the prompt.** The s02 prompt lists all nine routes with
explicit `available:` flags. Every observed `route_available` value matches the table, so
`BM-002/t2`'s `CAM_AND_FOLLOWER … available: true` is **correct**, and its divergence
from the fixture is a *route-choice* judgement (kinematic vs contact), not an error.
**Reclassified.** `PRB-01`'s routing of a capacity-of-twenty question to
`MATERIAL_PROPERTY_ANALYSIS` (t1) and `MANUFACTURING_PROCESS_ANALYSIS` (t3) remain wrong
route choices.

**Fields that are explicitly optional — earlier notes withdrawn.**
`self_locking (optional)`, `derivation_premises[] (optional)`, `involves_actors[]
(optional)` in s02; `promised_features[] (optional)` in s03b; `block_scopes[] (optional)`
in s01. **Their absence is compliance, not defect.** This withdraws the §5 observation
about `promised_features` presence/absence and completes the §E-2 narrowing on
`derivation_premises`.

**Fields the prompts never constrain.** s01 gives **no format for `locator`** (only that
`source_locator` must match one — satisfied in all 18 files); `directionality` and
`quantity_kinds` are given by illustration (*"such as …"*); **`block_scopes` has no
stated vocabulary at all.** §G.3's nine locator conventions and the 0/18 `block_scopes`
result therefore **reclassify from model defect to prompt-vs-contract divergence** —
the same class as `interaction_kind` (§C.2b) and `kept_open_by` (§H.4 below).
`BM-001/t2`'s `["force"]`, `["cost"]` on quantity-free clauses remains a defect, because
*"[] if it states none"* is binding.

**`kept_open_by`, resolved.** The s01, s02 and s03 prompts each state the constraint
(s02 Rule 6: *"must CITE, by id, the Ambiguity or Freedom entities"*; s03: *"Ambiguity
or Freedom ids from the input"*). **The s03b prompt has no REFERENCES block and never
says what the field holds.** Outputs track the constraint's presence exactly: correct in
s03 in 5/5, wrong in s03b in 6/6. **§F question 2 is answered from raw evidence.**

**s03b reclassifications.** *"IRRELEVANCE. Only for a DOF that is BOTH unloaded AND
unactuated … Most mechanisms need none"* — `irrelevance: []` in four of six cases is
**compliance**, correcting §5.2's framing. *"a body that must stay put needs
LATER_BODY_COVER, ROTATION or ELASTICITY"* — **ELASTICITY is not tied to compliance by
the prompt**, correcting §5.6. *"Hops are body, joint or interface ids"* — `PRB-03`'s
interface/joint-only path is permitted; `BM-001`'s literal `"NONE"` and `PRB-02`'s
`"arm"`/`"desk edge"` are not ids. *"blocker_body — a body id, not a description"* is
explicit, and `PRB-01`'s `blocker_body: "NONE"` violates it.

**s04a reclassifications — two corrections to §4.** Rule 2 injects a computed
**"THESE BODY PAIRS MUST TOUCH"** list per case; BM-001's names all three pairs, so the
mutual envelope overlap recorded as an anomaly in §4 is **prompt compliance**. And the
prompt states *"You receive ONLY the mechanism … You do not receive the original
request"* — **the requirements are not in the s04a input**, so `scale.note: "No absolute
dimensions given"` is **true of s04a's own input**. The BM-002 80–100 mm and PRB-02
18–40 mm quantities are lost at the **s03→s04a projection**, not misreported by the
model. `maturity "PROVISIONAL"` is written into the schema, so §5.8's universal
PROVISIONAL is prompt-dictated. `approach_side` has **no enumerated values**, explaining
the vocabulary spread.

**The `"desk edge"` phantom body — origin located.** The PRB-02 s04a prompt's must-touch
list literally contains `BOD-0001 and desk edge must touch` and `BOD-0002 and desk edge
must touch`. The deterministically built list carried the free-text string from s03's
`IFC-0001.bodies` into the prompt **as a body id**, and Rule 1 says *"Every body gets an
extent and a centre."* `ENV-0006.body: "desk edge"` is the model obeying its prompt. The
origin is s03; the propagation is the prompt builder. **STATUS: UNEXPLAINED UNTIL P5.**

## §H.5 `SourceClause` reaches S02 in 0 of 18 prompts

Top-level families in the s02 typed input, extracted from all eighteen prompts:
`Actor, Ambiguity, Assumption, Freedom, Requirement, Scenario` — in every one.
(`Assumption` is absent only from `BM-001/t1`, whose s01 emitted `assumptions: []`.)

**`SourceClause` is never projected.** S01 captures the verbatim request text into
`source_clauses[]`; S02 never sees it. Consequently every `Requirement.source_locator`
in the s02 input points at a locator whose clause is absent, and every
`Ambiguity.conflicting_clauses` holds SRC- ids S02 cannot resolve. The only text S02 has
is the requirement statements themselves — which bears directly on why live obligations
so often restate requirements. **STATUS: UNEXPLAINED UNTIL P5.**

## §H.6 The truncation, read directly

Record 29 (`BM-003 t3 s02`): `execution_status: RESPONSE_TRUNCATED`,
`finish_reason: "length"`, `truncated: true`, `response_chars: 27454`, cap
`8192` clamped from `32000`. The raw text was read; it ends mid-string inside
`acceptance_contracts[0].predicates[0]` (*"All three legs rotate about revolute joints
relative to"*). Before cutting off it had reached **OBL-0038** — the largest obligation
set attempted anywhere in the corpus, against 28 in t1 and 20 in t2 of the same case —
and its `obligations_addressed` lists skip ids (0021, 0022, 0028, 0033, 0034, 0037 are
absent). **The truncation is the tail of obligation-set inflation meeting the output cap.**

## §H.7 P4A stop condition

| Condition | Status |
|---|---|
| 24 primary stage artifacts read | ✅ §0.1 |
| all assigned upstream fixtures read | ✅ 13/13, §0.2 + §A.0 |
| both `trials.json` read | ✅ §C.5 |
| both `model_run_records.json` read structurally | ✅ §C.4 |
| all 60 prompt/response prose bodies read | ✅ §H.1 |
| all 35 Window-1 raw responses read | ✅ §H.1 |
| raw ↔ stored comparisons complete | ✅ 59/59 identical, §H.2 |
| live ↔ Window-2 fixture comparisons complete | ✅ §D.2, §G.1, §H.3 |
| provenance labels based on raw evidence | ✅ §B, and the SHA match below |
| prior over-generalisations rechecked | ✅ §E, §H.3, §H.4 |

**Provenance, closed by SHA.** The six distinct live s01 prompt hashes equal the
`_meta.answers_prompt_sha256` recorded in the six upstream s01 fixtures —
`8b0db4445daa…`/`8b0db4445daac1de` (BM-001), `2f4defd9b40a…`/`2f4defd9b40a49e5`
(BM-002), `19c1292199d2…`/`19c1292199d2ecf6` (BM-003), `9a14b16df78a…`/`9a14b16df78aebc1`
(PRB-01), `d34b9269ed07…`/`d34b9269ed07e92f` (PRB-02), `6b38053b5524…`/`6b38053b55247c33`
(PRB-03). **Every upstream s01 fixture is an answer paired to the exact prompt the live
model received** — a controlled same-prompt comparison, confirmed from raw evidence. The
six s02 fixture hashes match none of the eighteen live s02 prompt hashes, so the fixture
s02 answers were paired to an s02 prompt built from the **fixture** s01.

**P4A is COMPLETE.** Not proceeding to P5.

## §H.8 Carried into P5 (added to §F)

11. Rule 3 and PERMITTED VALUES contradict each other on `principle` inside one prompt.
12. `SourceClause` is emitted by s01 and projected to s02 in 0 of 18 prompts.
13. The s04a must-touch list propagates a free-text interface participant as a body id.
14. The s04a input excludes the requirements, so stated absolute quantities cannot reach it.
15. `block_scopes` (s01) and `kept_open_by` (s03b) are required-shaped fields whose
    content the prompt never specifies, while the contract does.
16. The s03 prompt duplicates a ~1,500-character block and skips rules 7 and 8;
    the s02 prompt states the `satisfiable_at` rule twice.

## §H.9 Out of frozen scope — flagged, not read

`ver3/live_runs/deepseek/phase1_s01/` is a **third run directory** not present in the
frozen P4A corpus (which covers `window2/r_final` and `deepseek/q6_fix` only). It was not
read and nothing in this document depends on it. It should be classified before P5.
