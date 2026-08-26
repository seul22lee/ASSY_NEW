# CND-0001 assembly-aware S05 fresh-authoring experiment

Scratch working experiment. **No production code, contract, ontology, validator
or stage semantics was changed, and nothing was committed.** Everything below is
measured from the actual S07-compiled B-reps or computed from the design's own
declared numbers. Claude Code did not look at the renders and contributed no
geometry diagnosis to any model prompt.

---

## 0. Step 1 — the confirmed S04 contradiction, corrected and verified

The CND-0001 pose tree made the lid the root, so the base translated hundreds of
millimetres in OPEN. The correction was made **at construction** (`rebuild_cnd1.py`),
not as a post-hoc revision, because the DesignState write boundary correctly
refuses one stage revising another stage's field, and a `SUPERSEDE` of
`Transition.path` staled the States, Transitions and SweptVolumes — which in turn
emptied `MFA-CND-0001.eligible` and broke selection.

Corrected at construction:

```
JNT-0001: RGP-0002 -> RGP-0001   becomes   RGP-0001 -> RGP-0002   (base -> pin, FIXED)
JNT-0002: RGP-0003 -> RGP-0002   becomes   RGP-0002 -> RGP-0003   (pin -> lid, REVOLUTE)
TRN-0001/TRN-0002 moving_groups: ['RGP-0002','RGP-0003','RGP-0004'] becomes ['RGP-0003','RGP-0004']
```

Joint identities, the hinge axis, the located hinge frame, the joint coordinate
values and the mechanism principle are all unchanged.

Focused regression `verify_hinge_poses.py` — **REGRESSION PASS**:

| state | BOD-0001 base | BOD-0003 pin | BOD-0002 lid |
|---|---|---|---|
| CLOSED | identity | identity | identity |
| OPEN | identity | identity | t = [−140, 0, 340], R = 90° about Y |

The hinge point [−240, 0, 100] is fixed under the lid's motion, so the rotation
is about the existing hinge frame. All Joints, States, Transitions and
SweptVolumes STANDING; state hash
`9e939ce4c2e799ab11f05c467afcaf5e634a0a2d148801982b483cc3e35fe25b`.

S04 was then frozen for the rest of the experiment.

---

## 1. What was asked of DeepSeek

A completely fresh design — neither previous CND-0001 design was reused or shown.
The prompt required whole-assembly reasoning before output: coherent connected
bodies, a complete hinge (both knuckle sets, coaxial bores, a pin that passes
through, clearance, an insertion direction, access, and stated axial retention),
a real compliant latch (connected root, arm, hook, catch, lead-in, deflection
space, release path), CLOSED/OPEN as two poses of one assembled mechanism, and
real free space for the FunctionalRegions.

The authoring language gained only design-level sections — `mating_sets`,
`assembly_sequence`, `state_expectations` — plus **one generic primitive**, a
`wedge` (general right triangular prism), lowered with existing IR opcodes only.
No ontology, no mechanism library, no canned realization pattern, and no
candidate-specific geometry or dimensions were given.

---

## 2. Round 1

One DeepSeek call, 18.4 s, 9 247 chars, **parsed with zero syntax edits**.

### Renders

| CLOSED | OPEN |
|---|---|
| ![](round1_CLOSED_isometric.png) | ![](round1_OPEN_isometric.png) |
| ![](round1_CLOSED_side.png) | ![](round1_OPEN_side.png) |
| ![](round1_CLOSED_front.png) | ![](round1_OPEN_front.png) |
| ![](round1_CLOSED_top.png) | ![](round1_OPEN_top.png) |

Per body: ![](round1_body_BOD-0001_isometric.png) ![](round1_body_BOD-0002_isometric.png) ![](round1_body_BOD-0003_isometric.png)

CLOSED/OPEN is derived from each state's own hinge coordinate — S04 names these
states only CFG-0001 / CFG-0002 — and the coordinates are printed on every image.

### Evaluation — 0 of 13

Full table in [round1_evaluation.md](round1_evaluation.md). Summary: base
compiled as **3** disconnected solids, lid as **2**; the lid never touches
anything in either state (13–17 mm clear); the pin reaches the base bore only.

### The single dominant cause

`at` is the **centre** in this language, so `base_outer` at `[0,0,0]` puts the
base top at `base_height/2` = 20. The design placed base-side features in that
convention but every lid-side feature as if the base spanned 0…40:

| feature | declared z | convention |
|---|---|---|
| `hinge_bore_base` | `base_height/2` = 20 | base is centred ✔ |
| `latch_recess` | `base_height/2 − depth/2` = 18.5 | base is centred ✔ |
| `lid_plate` | `base_height` = 40 | base starts at 0 ✗ |
| `hinge_bore_lid` | `base_height + t/2` = 43 | base starts at 0 ✗ |
| `snap_hook` | `base_height + t` = 46 | base starts at 0 ✗ |

The whole lid is exactly `base_height/2` = 20 mm too high. Hinge bores 23 mm
apart, hook 27.5 mm above its recess. One internal datum inconsistency accounts
for every geometric failure in round 1.

---

## 3. The visual feedback iteration

deepseek-vl2-tiny, local, under psed310 with the scratch-local transformers
4.38.2 path. No new downloads, no Claude vision, no Claude subagent.

Its round-1 review ([deepseek_vlm_round1_review.md](deepseek_vlm_round1_review.md))
is saved verbatim and was passed verbatim as the only new evidence. It produced
part 1 only, then **degenerated into the same four sentences repeated until the
token limit**, never reaching parts 2 and 3, and misattributed the body colours
(it calls BOD-0001 "orange"). It never mentions height, datum or the lid being
displaced.

One DeepSeek redesign call followed — 19.8 s, 11 217 chars, **zero syntax edits**
— with only the corrected S04 input, the complete round-1 design and that
verbatim critique.

---

## 4. Round 2

### Renders

| CLOSED | OPEN |
|---|---|
| ![](round2_CLOSED_isometric.png) | ![](round2_OPEN_isometric.png) |
| ![](round2_CLOSED_side.png) | ![](round2_OPEN_side.png) |
| ![](round2_CLOSED_front.png) | ![](round2_OPEN_front.png) |
| ![](round2_CLOSED_top.png) | ![](round2_OPEN_top.png) |

Per body: ![](round2_body_BOD-0001_isometric.png) ![](round2_body_BOD-0002_isometric.png) ![](round2_body_BOD-0003_isometric.png)

### Round 1 vs round 2, measured

| measure | round 1 | round 2 |
|---|---|---|
| base solids | 3 | **2** |
| lid solids | 2 | 2 |
| pin solids | 1 | 1 |
| base↔lid CLOSED | 0 mm³, 13.0 mm apart | **373.17 mm³ overlap, touching** |
| base↔pin | 61.65 mm³ | 248.48 mm³ |
| lid↔pin CLOSED | 0 mm³, 15.0 mm apart | 0 mm³, **14.0 mm apart** |
| base↔lid OPEN | 0 mm³, 15.0 mm apart | 0 mm³, 12.0 mm apart |
| hinge bore axis separation | 23.00 mm | **23.00 mm** |
| hook ↔ recess | Δz 27.5, Δx 3.0 | Δz 9.0, **Δx 23.0** |
| S07 findings | 0 | 0 |

### What round 2 genuinely improved

- Both base knuckles are now bored (`bore_base` **and** `bore_base2`) — round 1
  bored a single hole at y = 0, between the two knuckles, where there was no
  knuckle material.
- The pin gained a real `pin_head` (r 3 mm at y = +31, just outside the base
  face at y = 30) — an axial-retention concept that exists as geometry, not only
  as prose.
- A `hinge_stop` was added, and a third mating set declares it limits the lid to 90°.
- The latch recess was raised from z 18.5 to 35.5, cutting the hook/recess
  vertical error from 27.5 mm to 9.0 mm.
- The base is one solid fewer, and in CLOSED the lid finally makes contact with
  the base rather than floating 13 mm above it.

### What round 2 did not fix — 0 of 13 again

The datum inconsistency is **unchanged**: `lid_main` still at `base_height` = 40,
`bore_lid` still at 43, base bore still at 20. The hinge axis separation is
identical to the millimetre. The lid is still never connected to the pin, and in
OPEN it is a free body 12 mm from the base. The lid still compiles as 2 solids.
The snap beam moved outboard (`base_width/2 + beam_length/2` = 60), so the hook
is now at x 71.5 against a recess at x 48.5 — 23 mm away, worse than round 1's
3 mm. The base↔lid contact in CLOSED is 373 mm³ of **interpenetration**, not
seating, and the pin's 248 mm³ overlap is the pin passing through undrilled base
wall between the two bores, not a fit.

### Final VLM comparison

[deepseek_vlm_round2_comparison.md](deepseek_vlm_round2_comparison.md), verbatim.
It restated the question — "The images also show the hinge continuity and whether
the pin passes through the hinge…" — and made **no comparative observation at
all**. No third redesign was run.

---

## 5. Success criterion

**Not met.** The criterion was a recognizable connected mechanism, not
`CompileResult.ok` (which was `False` in both rounds anyway).

| required | round 1 | round 2 |
|---|---|---|
| one connected base | ✗ 3 solids | ✗ 2 solids |
| one connected lid | ✗ 2 solids | ✗ 2 solids |
| real hinge mating geometry | ✗ | ✗ bores 23 mm apart |
| inserted / retained pin | ✗ | partial — head exists, insertion does not |
| lid attached through OPEN/CLOSED | ✗ | ✗ |
| actual latch hook/catch | ✗ never meets | ✗ never meets |
| plausible assembly sequence | declared only | declared only |
| no floating features / body splits | ✗ | ✗ |

---

## 6. Where the remaining failures belong

### S04
**None.** The one confirmed S04 defect was corrected and verified before the
experiment, and S04 caused no failure in either round. The corrected hinge tree
held throughout: base and pin identity in both states, the lid rotating about the
existing hinge frame.

### DeepSeek physical design — the dominant failure
1. **An internal datum inconsistency**, present identically in both rounds: the
   base is placed centred on the origin while every lid-side feature is placed as
   if the base started at z = 0. This one error causes the non-coaxial hinge, the
   unreachable pin, the floating lid and the unengaged latch.
2. **Declared relationships not realized in geometry.** Both rounds declare
   `mating_sets` binding real participants to the upstream `IFC-*`/`JNT-*`/`PHI-*`
   ids, and a step-by-step `assembly_sequence` with insertion directions, access
   and retention. Round 2's step 3 says the lid slides onto the pin; they are 14 mm
   apart. The prompt's rule that no mating relationship may be satisfied by prose
   alone was violated in both rounds — but the new sections made the violation
   **measurable**, which is what they were added for.
3. **Elements that do not join their own body.** Round 1's lid knuckle, beam and
   hook do not intersect the lid plate; the base's bore at y = 0 cuts air between
   the knuckles. Round 2 improved this but still splits both the base and the lid.
4. **A regression under revision.** Round 2 moved the snap beam outboard,
   worsening the hook/recess x error from 3 mm to 23 mm while improving the z
   error.

### Assembly realization
The model reasons about assembly at the **declaration** level competently — a
pin head for axial retention, a hinge stop, insertion directions, both knuckles
bored on the second attempt — but does not check that its own coordinates make
those declarations true. Nothing in the pipeline enforces agreement between a
declared mating set and the geometry, so a fully-specified assembly intent can
coexist with parts 23 mm apart.

### Geometry-language limitation
1. The language defines a dimension as **one number**. Round 1 invented a
   vector-valued dimension (`lid_plate_size: [100, 60, 6]`), used its name where a
   size triple was expected, and indexed it (`lid_plate_size[2]`). The translator
   was extended to read both faithfully — see [translator_fixes.md](translator_fixes.md).
2. The language has no way to say *"this face lies on that face"*. Every position
   is an absolute expression, so a datum convention exists only in the model's
   head. This is the most likely single cause of the failure being repeated
   verbatim across two independent designs.
3. `wedge` was sufficient for the round-1 hook; round 2 chose a plain box instead.

### VLM resolution — the limiting factor of the feedback loop
deepseek-vl2-tiny produced no usable signal in either call. The round-1 review
looped four sentences to the token limit, never reached parts 2 and 3, and got
the body colours wrong; the final comparison restated the prompt and observed
nothing. It never once mentioned the 20 mm vertical displacement that dominates
both pictures. **The revision therefore had no real visual evidence to act on**,
and it is unsurprising that round 2 fixed local details it could reason about
from its own design text while leaving the global datum error untouched. A
larger VLM is the prerequisite for testing whether visual feedback works at all.

### Translator
Two fixes, both recorded, neither altering a number, shape, position or
relationship: the generic `wedge` lowering (existing IR opcodes only), and
reading vector-valued dimensions and their indexed components. One disclosed
**reference repair** in the round-1 design text — the design declared
`wall_thickness` and referred to it as `wall` in six geometry expressions;
identifier spelling only, prose untouched, all six sites listed in
`round1_reference_repair.json` with the pre-repair design preserved. That is a
DeepSeek authoring inconsistency, not a translator limitation. No other
translator defect appeared; both rounds translated and settled cleanly.

### S06
**No failure.** `feasible` in both rounds — round 2 with 21 unknowns at rank 21,
fully determined. S06 settled exactly what it was given; nothing was left
under-determined for it to guess.

### S07 / evidence
S07 compiled real B-reps, STEP and BREP for every body in both rounds and posed
them with the real pose law. But it reported **0 findings** for two assemblies in
which nothing mates, bodies are split, and parts interpenetrate by 373 mm³. The
`ok = False` verdict carried no explanation of what was wrong. **The evidence
layer does not currently detect body splitting, unrealized mating sets,
non-coaxial declared-coaxial bores, or interpenetration between bodies in a
declared state** — all four were found here only by measuring the compiled solids
directly. That gap is the clearest actionable finding of this experiment.

---

## 7. Files

| file | what it is |
|---|---|
| `s04_input.json` | the corrected, frozen S04/S03 standing state |
| `round1_prompt.txt`, `round2_prompt.txt` | the exact prompts sent |
| `round1_raw_deepseek_response.txt`, `round2_raw_deepseek_response.txt` | byte-exact model output |
| `round1_parse_repair.json`, `round2_parse_repair.json` | syntax edits (zero in both) |
| `round1_reference_repair.json` | the six disclosed `wall` → `wall_thickness` sites |
| `round1_design_plan.pre_reference_repair.json` | the design before that repair |
| `round1_design_plan.json`, `round2_design_plan.json` | the parsed designs |
| `round1_translation_log.json`, `round2_translation_log.json` | every translator choice |
| `round1_assembly_evidence.json`, `round2_assembly_evidence.json` | measured solids, overlaps, distances |
| `round1_evaluation.md` | the 13-question round-1 evaluation |
| `deepseek_vlm_round1_review.md`, `deepseek_vlm_round2_comparison.md` | verbatim VLM output |
| `translator_fixes.md` | both translator fixes and the reference repair |
| `cad_round1/`, `cad_round2/` | STL, STEP, BREP per body and posed assembly STEP per state |
| `round1_*.png`, `round2_*.png` | CLOSED/OPEN isometric, side, front, top and per-body renders |
