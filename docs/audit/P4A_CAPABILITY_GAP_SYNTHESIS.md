# P4A CAPABILITY-GAP SYNTHESIS

Axis A: **GENERATED EVIDENCE**. Axis B: **REVIEW RECORD**.

Synthesis of P3 (engineering reference) against P4A (raw pipeline output), preceded by
an independent re-check of the cumulative-state architecture question. No implementation
code was read. No experiment was run. Nothing was modified. No fix is proposed.

Companion documents: `P1_COMPLETE.md`, `P2_COMPLETE.md`, `P3_COMPLETE.md`,
`P4A_COMPLETE.md` (§A–§H). Those are unmodified; this document cross-references them.

---

## §A — VERIFIED CUMULATIVE-STATE ARCHITECTURE MODEL

**Answer: YES. The intended architecture is a single persistent DesignState that is
progressively enriched. It is not a chain of replacement answers.** Established from raw
contract text, not from memory or from the implementation.

### A.0 The governing sentence

`ver3/contracts/STAGE_PATCH_CONTRACT.yaml:3-6`

> "A stage does not mutate DesignState. It PROPOSES a StagePatch, the patch is validated
> against this contract and against STAGE_OWNERSHIP_MATRIX, and only then is it applied.
> A stage that could write directly to the state would make ownership advisory, and
> ownership is the mechanism INV-001 depends on."

### A.1 Question-by-question, with anchors

**A. What persists between stages?**
Everything ever created. `STAGE_PATCH_CONTRACT.yaml:106` — SUPERSEDE: *"Mark an entity
as replaced, **keeping both**"*, validation *"**Neither entity is deleted**"*.
`DESIGN_STATE_CONTRACT.yaml:99` — *"Candidates **PERSIST as branches**. Stage 02 has NO
selected-candidate field (INV-007)."* `DESIGN_STATE_CONTRACT.yaml:496` — *"Failed
alternatives are **retained, never deleted**. The package must be able to show them."*
`STAGE_PATCH_CONTRACT.yaml:138` — even a rejected patch is *"RETAINED with its rejection
reason"*, and `:140` *"Rejected patches are part of the run record, not debris."*

**B. What is added by StagePatch?**
`STAGE_PATCH_CONTRACT.yaml:72` — six operation kinds only:
`CREATE, EXTEND, RELATE, SUPERSEDE, RECORD_UNRESOLVED, RECORD_REJECTED`.
CREATE validation `:82` — *"Every reference field must name an existing entity ID (R-20)."*

**C. Is a stage allowed to replace prior state?**
**No.** `STAGE_PATCH_CONTRACT.yaml:89` — *"A field already set by the owning stage may
not be overwritten."* `:92-95` — *"A stage that needs a different value than the owner
set does NOT overwrite. It emits SUPERSEDE with a reason, or RECORD_UNRESOLVED.
Overwriting hides the disagreement, and the disagreement is usually the interesting
part."*

**D. What does EXTEND mean?**
`STAGE_PATCH_CONTRACT.yaml:85-90` — *"Add to an existing entity, by ID."* Requires the
entity to exist; the stage must appear in the family's `extends` or own the family;
owner-set fields are immutable; *"Append-only collections may only be appended to."*
Per-family permission is carried as `extendable_by`, e.g.
`DESIGN_STATE_CONTRACT.yaml` `Body.extendable_by: [s05, s06, s07]`,
`Joint.extendable_by: [s04, s05, s06]`.

**E. What does RELATE mean?**
`STAGE_PATCH_CONTRACT.yaml:98-102` — *"Create a typed relationship between two
**existing** entities."* Validation: *"Both endpoints must exist and be of the types the
relation permits"*; **"A free-string subject or object is a SCHEMA_FAILURE (R-20)."**
Reinforced by `DESIGN_STATE_CONTRACT.yaml:416` prohibited_content — *"a free-string
subject"*, INV-001, R-20.

**F. What does invalidation remove?**
**Nothing.** `STAGE_PATCH_CONTRACT.yaml:48-62` — the invalidation cone marks dependents
**STALE**; *"Checks outside the cone are **PRESERVED**, not recomputed."* Revision
`:171-175` explicitly forbids *"Rolling the state back to before the failed attempt"*
because *"That erases the evidence that the alternative was tried and failed."*

**G. What must remain available after later stages?**
All of it. `DESIGN_STATE_CONTRACT.yaml:434-438` — the assurance package is *"a
**PROJECTION** of this state. A projection can only show what the state holds, so every
element the package must be capable of containing needs a typed home here."*

**H. Persistent DesignState vs the stage-specific LLM view.**
These are **explicitly different**, and the difference is a designed boundary, not an
accident. `DESIGN_STATE_CONTRACT.yaml:401-403` prohibited_content — **"raw request text
at or after Stage 02"**, invariant **INV-002**, retirement row **R-13**. And
`DESIGN_STATE_CONTRACT.yaml:447` — `SourceClause` rules: *"The only family that may hold
source text. **Nothing downstream re-reads it (INV-002).**"*
`STAGE_PROGRESSION_CONTRACT.yaml:216-220` defines sufficiency as constructible *"using
only N's output **and the accumulated DesignState**"*, with an insufficiency signal
*"The downstream stage must re-read the source request (violates INV-002)."*

### A.2 The consequence that governs everything below

**TYPE B — persistence/state failure — is architecturally impossible under these
contracts, and no raw artifact in P4A establishes a single instance of it.** Nothing is
deleted, nothing is overwritten, invalidation only marks. Every "information was lost"
observation in P4A must therefore resolve to **capture (A)**, **projection (C)**,
**representation (D)**, **reasoning (E)** or **gating (F)** — never to deletion.

This is a substantive negative result and it reframes the audit: the pipeline's problem
is **not** that it forgets. It is what it never captured, what it does not show the next
reader, what it cannot express, and what it commits anyway.

---

## §B — PERSISTENT STATE vs CONSUMER VIEW: THE CORRECTION THIS FORCES

### B.1 `SourceClause` — RECLASSIFIED. Not a defect.

P4A §H.5 recorded that `SourceClause` appears in **0 of 18** s02 prompts and framed it as
an information-flow finding. Re-checked against raw contract text:

**INV-002 requires exactly this.** Raw request text is prohibited content at or after
Stage 02 (`DESIGN_STATE_CONTRACT.yaml:401`), and `SourceClause` is *"The only family that
may hold source text. Nothing downstream re-reads it."* The entity **persists in the
DesignState** — it is an `assurance_families` member owned by s01, projectable into the
assurance package — it is simply and deliberately **not projected into the S02 consumer
view**.

**Corrected classification: INTENDED PROJECTION BOUNDARY, correctly implemented.**
Not TYPE A, not TYPE B, not a TYPE C failure.

**A residual consequence remains, and is a genuine open question rather than a defect.**
Because the boundary is enforced, the s02 typed input contains `Requirement.source_locator`
values and `Ambiguity.conflicting_clauses` SRC- ids that **S02 cannot resolve to anything
it can see**. Whether references that are unresolvable inside the consumer view are
intended (they resolve in the persistent state) or are a projection-design question is
**for P5**. It is not evidence of loss.

### B.2 The general rule this establishes for the rest of this document

> A prompt omission is evidence about the **consumer view**, never about the
> **DesignState**, unless a raw artifact independently shows the entity was never created.

Applied throughout §D and §E below.

---

## §C — `ver3/live_runs/deepseek/phase1_s01/` CLASSIFICATION

**Classification: HISTORICAL PRECURSOR, and additionally PARTIAL / INTERRUPTED.**
**Not authoritative. Not equal in weight to the frozen P4A corpus.**

Evidence, from metadata and run records only (no deep re-audit):

| Fact | Value |
|---|---|
| Contents | 18 × `s01.json` only; no `s02.json` anywhere |
| `trials.json` | 18 entries; **`s01_status: "RAISED"`, `s02_status: null`, `counts: {}`** |
| `failures[].kind` | **`PARSER_DEFECT`** — a Python traceback recorded as trial data |
| Prompt size | `prompt_chars: 1635` vs the frozen corpus's **4795** for the same case |
| Prompt hash | `836b65c33e22…` for BM-001 vs frozen `8b0db4445daa…` — **a different prompt** |
| Fixture pairing | **No fixture's `answers_prompt_sha256` matches any prompt here** |
| Timestamps | `20:00–20:02`; `q6_fix` is `21:45–21:55` the same day — **precedes it by ~1h45m** |
| Determinism | same `reqT 0.0 / sentT 1.0`, same `deepseek-v4-flash` substitution |

**Why the classification.** Every trial terminated at s01 with `RAISED` and produced no
typed state (`counts: {}`), so nothing downstream exists to audit. The prompt is a
different, shorter artifact than the one the frozen corpus and every upstream fixture are
paired to by SHA (P4A §H.7). It therefore cannot be compared against the fixtures on the
same-prompt basis that makes the frozen corpus a controlled comparison.

**Action: left alone.** Nothing in this document or in P4A depends on it. Escalate only
if P5 needs the earlier prompt revision as history. *(The traceback text in `trials.json`
names implementation files; it was not opened, and no inference from it appears here.)*

---

## §D — P3 ↔ P4A CAPABILITY MATRIX

Mechanism-independent statements only. Reference basis is *why the capability matters*,
never *which mechanism the Oracle chose*.

Column key — **Boundary**: where the failure is first observable.
**Type**: A capture / B persistence / C projection / D representation / E reasoning /
F gating (§E defines these). **Attribution**: ESTABLISHED = settled from raw evidence;
P5 = not yet attributable.

---

### CAP-01 — Distinct-pivot preservation from topology to space

**Capability.** A mechanism whose function requires two or more kinematically distinct
connection locations must not realise them at one point. Coincident pivots collapse the
link between them to zero length and destroy the motion the topology declares.

**Reference basis (P3).** Every reference mechanism carrying a rotary-to-linear or
multi-leg function shows spatially separated pivots; P3 NEW-1 recorded a crank radius as
the dimension that sets the stroke. Mechanism-independent: *any* rotary-to-linear
conversion needs a non-zero throw.

**Raw evidence (P4A §3.1–3.3).** 19 of 25 joints across six cases share an origin with
another joint. BM-002 `s04b`: JNT-0001/0002/0003 all at `[0,0,2.5]` — the crank link's
two pins coincide, throw = 0, and JNT-0002 `+90` / JNT-0003 `−90` cancel. BM-003 `s04b`:
JNT-0001/0002/0003 all at `[0,1,0]` and JNT-0004/0005/0006 all at `[0,0,0.5]`. PRB-03:
all three at `[0,0,0]`. BM-001: both at `[0,0,0]`.

**Decisive internal contradiction.** BM-003 `s04a` places the three legs correctly at
120° / radius 2 (`[0,1,0]`, `[1.732,−1,0]`, `[−1.732,−1,0]`) and `s04b` collapses all
three pivots onto the first leg's position. **The geometry existed one artifact earlier
and was not used.**

**Boundary: S04A→S04B.** **Type: E, with a D component.** The s04b prompt provides the
s04a arrangement in its typed input (P4A §C.2), so the information was present. The D
component: the s04b schema collects `origin [x,y,z]` only, while
`DESIGN_STATE_CONTRACT` `Joint.fields_owned_by_s04b: [located_frame]` requires a *frame*;
the prompt asks for the axis in prose and provides no field for it (P4A §C.2a).
**Recurrence: CROSS-CASE (5/6), CROSS-TRIAL not testable (Window 2 is single-trial).**
**Severity:** the joint graph is required to be *"SIMULATION-COMPLETE: projectable into a
multibody model without re-derivation"* (`DESIGN_STATE_CONTRACT.yaml:135`). Coincident
pivots make it projectable and wrong. **Attribution: ESTABLISHED that it occurs and that
the information was available; WHY the s04a→s04b handoff does not carry it is P5.**

---

### CAP-02 — Configuration distinctness as physical realisation

**Capability.** Two configurations declared distinct must correspond to physically
different realisations of the declared DOFs. A named state that resolves to the same
coordinates as another is not a state.

**Reference basis (P3).** Stored/deployed, open/closed, tight/holding are the
distinctions the reference mechanisms exist to produce.

**Raw evidence.** BM-003: JNT-0001/0002/0003 hold `0 / 120 / 240` in **all three**
configurations — the folding stand's legs never fold; CFG-0001 and CFG-0003 are
coordinate-identical. PRB-02: CFG-0002 *"tightening"* and CFG-0003 *"holding"* are
byte-identical and `TRN-0002` between them has `moving_groups: []`. BM-002: JNT-0001, the
rotary input, holds `0.0` across the only transition.

**Boundary: S04B.** **Type: E.** All configuration ids, joint ids and DOF are in the
s04b input; nothing needed was missing. **Recurrence: CROSS-CASE (3/6).**
**Severity:** `Configuration.required_fields` includes `expected_mobility`
(`DESIGN_STATE_CONTRACT`), and a configuration that is not physically distinct cannot
carry a distinct mobility expectation. **Attribution: ESTABLISHED.**

---

### CAP-03 — Actuation connected to the motion it produces

**Capability.** The input a mechanism exists to receive must be kinematically connected
to the output it produces, and must change when the output changes.

**Raw evidence.** BM-002: the s03 chain is JNT-0001 `RZ` about `+Z` (input) → JNT-0004
`TZ` along `+Z` (output). Input rotation axis is **parallel** to output translation axis;
and in `s04b` the input coordinate does not move while the platform rises 2.0. PRB-02:
the lead screw has **no joint to the traveling jaw** — only `IFC-0003`, a CONTACT
interface. PRB-01: the linkage has **no joint to either gate**; the interlock exists only
in `BOD-0004.role` prose. PRB-03: the return spring has **no joint to the pedal** — only
`IFC-0003`, and `JNT-0002` fixes it rigidly.

**Boundary: S03.** **Type: E, with a D component.** The s02 candidate reached s03 with an
explicit `principle` naming the conversion; the failure is in realising it. The D
component: an `Interface` can carry `interaction_kind` but has **no field expressing
force or motion transmission**, so a transmitting relation that is not a joint has
nowhere typed to live. **Recurrence: CROSS-CASE (4/6).** **Severity:** the highest of any
finding — in four cases the mechanism's defining function is absent from the structure and
present only in prose. **Attribution: ESTABLISHED that it occurs; whether the Interface
family can express transmission at all is a P5/contract question.**

---

### CAP-04 — Load-reaction closure to something outside the product

**Capability.** Every load must terminate at a site the system boundary places outside
the product. A load reacted against the product itself has not been reacted.

**Reference basis.** Every upstream fixture supplies `reacted_at_role` on every load case
(*"the desk surface the product stands on"*, *"the wall the product is fixed to"*,
*"the edge the product grips"*). The s02 prompt states the rule verbatim (P4A §H.4).

**Raw evidence.** **No load path in any of the six cases terminates at an external
reaction site.** BM-001: every `ordered_hops` ends in the literal string `"NONE"`.
BM-002: all terminate at BOD-0001. BM-003: cyclic — `LDP-0001` revisits BOD-0002,
BOD-0001 and IFC-0001. PRB-01: `LDP-0003/0004/0005` are `["BOD-0001","BOD-0001"]`.
PRB-02: `["arm","BOD-0002","BOD-0001","desk edge"]` — reaches outside only by leaving the
type system. PRB-03: `["IFC-0001","JNT-0001","IFC-0004"]` — no bodies at all.

**And the world has no representation.** Six cases produced six different degenerate
encodings of "grounded": self-blocking (BM-001, BM-002), a chain grounded on nothing
(BM-003), `blocker_body: "NONE"` (PRB-01), and mutual two-body loops (PRB-02, PRB-03).

**Boundary: S03 (`s03b`).** **Type: D primarily, E secondarily.**
`DESIGN_STATE_CONTRACT` derives *reaction* from *"the terminal hop of a LoadPath"* and
*support* from *"an Interface of contact kind appearing in a LoadPath"* — both become
underivable when the terminal hop is a literal or a free string, and PRB-01's paths
contain no interfaces at all. `blocked_by.required_fields` has **no identifier and no
way to name a non-body reaction site** (P2 CI-5). **Recurrence: CROSS-CASE (6/6) —
universal.** **Severity:** load-path closure is the precondition for every structural
claim downstream. **Attribution: ESTABLISHED as universal; whether the entity model can
express an external ground is a P5/contract question.**

---

### CAP-05 — Retention expressed as a testable, directed, externally-blocked relation

**Capability.** A retained state requires a localised interaction that blocks the
specific disturbance, names a blocker other than the retained body, and states how a test
would defeat it.

**Reference basis.** `DESIGN_STATE_CONTRACT` `blocked_by` rules, verbatim: *"Direction
and blocker are required TOGETHER. A blocking fact without a direction cannot be tested,
and one without a named blocker passes when an unrelated body happens to be in the way."*
And *"defeat_specification is authored HERE, with the relation, never reconstructed from
geometry at s08."*

**Raw evidence.** `blocked_direction: "NONE"` on 4/7 (BM-001), 4/4 (BM-002), 4/10
(PRB-01), 4/5 (PRB-02), 4/4 (PRB-03). `blocker_body` equal to the retained group's own
body in BM-001 BLK-0001 and **all four** BM-002 relations. `blocker_body: "NONE"` in
PRB-01 BLK-0008 — while the s03b prompt states *"blocker_body — a body id, not a
description."* `defeat_specification: "None"` on 4 of 5 PRB-02 relations. And the DOF
that most needs blocking is unblocked: BM-001 `RZ` of RGP-0002 in CFG-0001 (nothing holds
the lid shut), BM-003 the legs' `RZ` in the deployed configuration, PRB-03 the pedal's `RZ`.

**Boundary: S03 (`s03b`).** **Type: E.** The rule is stated in the contract *and* in the
prompt; the required fields exist; the model had the topology. **Recurrence: CROSS-CASE
(6/6).** **Severity:** `MobilityExpectation` requires *"BLOCKED_BY must resolve to a
`blocked_by` relation carrying a direction, a named blocker and a defeat specification"* —
a relation with `"NONE"` in either field **cannot satisfy any disposition**.
**Attribution: ESTABLISHED.**

---

### CAP-06 — DOF totality as a partition

**Capability.** Every (rigid group, configuration, DOF) triple must map to exactly one
disposition. Omission and double-assignment are both failures of totality.

**Reference basis.** `DESIGN_STATE_CONTRACT` `MobilityExpectation` TOTALITY rule: *"for
every rigid group in the configuration, every rigid-body DOF maps to **exactly one**
value. A declared set that omits a DOF cannot fail, and all three BM-001 human-review
rejections plus BM-003 R2 were omissions from declared sets."* Proposal D-11 restates it.

**Raw evidence.** **No case produces a partition.** BM-003: 7 groups × 3 configs × 6 DOF
= 126 cells; blocking covers 6 cells in one configuration and `irrelevance` is `[]` —
~120 cells unsourced, and RGP-0001 appears in no relation at all. BM-002: for three of
four groups the blocked set and the irrelevance set are **identical**, so those cells are
double-assigned. PRB-01, PRB-02, BM-002: a DOF is simultaneously BLOCKED and changes
value in `s04b`.

**Boundary: CONTRACT-LEVEL — and this is the sharpest producer-consumer impossibility in
the audit.** `MobilityExpectation` is `owned_by: s03`. **No s03 or s03b prompt contains a
`mobility_expectations` key.** The s03 prompt says *"A later step dispositions every
degree of freedom"*; the s03b prompt collects `blocking_relations` and `irrelevance`.
**The entity the architecture calls *"a mechanical FMEA obtained free from the joint
graph"* is owned by a stage that is never asked to author it.**
**Type: D (contract-level).** **Recurrence: CONTRACT-LEVEL + CROSS-CASE (6/6).**
**Severity:** totality is the architecture's central safety property against
FALSE_ACCEPTANCE. **Attribution: ESTABLISHED as a contract-vs-prompt impossibility; the
derivation path is P5.**

---

### CAP-07 — Producer→consumer representation closure for the candidate principle

**Capability.** The structure by which S02 tells S03 what kind of machine to build must
be one structure, and the same one on both sides.

**Raw evidence (P4A §H.3).** Three incompatible shapes exist for one field:
bare string (15/17 live), parallel arrays (2/17 live — `BM-001/t3`, `PRB-03/t1`),
role→principle dict (13/13 fixtures). The s02 prompt's PERMITTED VALUES says
*"principle — **one of** the PRINCIPLE FAMILIES listed above"* (singular), while Rule 3 of
the same prompt says a candidate names *"the FUNCTION CLASSES it must perform and the
PRINCIPLE FAMILY it uses **for each**"* (a mapping). `DESIGN_STATE_CONTRACT`
`Candidate.required_fields` names `principle` without specifying a shape.

**Boundary: S02, and S02→S03.** **Type: D.** **Recurrence: CONTRACT-LEVEL and
CROSS-TRIAL within a single case — `BM-001` is string/string/array, `PRB-03` is
array/string/string.** **Severity:** this is the only channel carrying `HARD_STOP`,
`SEPARATE_RETAINING_MEMBER`, `CRANK_SLIDER` into S03. Window-2's S03 was fed a six-key map
that **no prompt-conforming S02 output would ever contain**. **Attribution: ESTABLISHED
that three shapes exist and that the prompt contradicts itself; the canonical shape is a
P5/contract decision.**

---

### CAP-08 — Selected principle actually realised downstream

**Capability.** The mechanism S03 builds must be the mechanism the selected candidate
names, and must not silently adopt a principle whose evidence route was declared
unavailable.

**Raw evidence.** BM-003 `CND-0001` is `MAINTAIN_CONFIGURATION: SEPARATE_RETAINING_MEMBER`
with `BOUND_MOTION: HARD_STOP`. S03 attached the retaining members with **COMPLIANT**
joints (`mode: TRANSLATION`) — the principle of `CND-0003`, whose
`evidence_route_verdict.available` is **`false`** (*"the hold is a deflection force and no
available route establishes it"*). No hard stop was produced despite `HARD_STOP` appearing
in the principle, in `obligations_created` (*"a bound on the deployed travel"*) and in
`ACC-0001`'s predicates. PRB-03 shows the mirror case: `BOUND_MOTION: HARD_STOP` named
three times upstream, no stop produced — while **PRB-01 invented a hard-stop body
(`BOD-0007`) unprompted**, so the capability exists.

**Boundary: S02→S03.** **Type: E, with F.** The E part: the principle was in the input and
was not realised. The F part: adopting a mechanism whose route is unavailable moves the
design onto evidence the architecture had refused, and nothing stopped it.
**Recurrence: CROSS-CASE (2/6 for substitution; 2/6 for HARD_STOP omission).**
**Severity:** this is the FALSE_ACCEPTANCE pole — the machinery for refusing unsupportable
claims is bypassed by the downstream stage building something else.
**Attribution: ESTABLISHED.**

---

### CAP-09 — Quantitative continuity to the stage that needs the quantity

**Capability.** A dimensional quantity stated in the source must reach the stage that
commits dimensions, or its absence must be explicit.

**Raw evidence.** BM-002 states *"approximately 80-100 mm"* and *"approximately 1 kg"*;
PRB-02 states *"between 18 and 40 mm thick"*. S01 captures both correctly as
`quantity_class: BAND` in **all three trials of each case** — a real strength (§F).
S02 carries `magnitude_or_status: "approximately 1 kg"` (BM-002 t1, and the fixture).
**S04A receives neither.** Its prompt states *"You receive ONLY the mechanism: bodies,
rigid groups, joints, configurations, assembly steps, functional regions, and the actors
… You do not receive the original request"*. All six cases emit
`scale: {basis: "RELATIVE", absolute: null}`.

**Boundary: S03→S04A.** **Type: C — projection, and by the rule of §B.2 this is a true
projection finding, because the entity demonstrably exists upstream** (`Requirement`
with `quantity_class: BAND` in the s02 typed input, read directly).
**Not TYPE B** — the Requirement is not deleted; it is not projected.
**Not a model failure** — s04a's note *"No absolute dimensions given"* is **true of its own
input**. **Recurrence: CROSS-CASE (2/6 cases have a stated quantity; both lose it).**
**Severity:** PRB-02's entire discriminating obligation is spanning 18–40 mm, and its
`s04b` jaw joint moves `0 → 0.1` in relative units. **Attribution: ESTABLISHED as a
projection boundary; whether it is intended is P5.**

---

### CAP-10 — Typed-relation integrity for participants that are not product bodies

**Capability.** An interaction with something outside the product must be expressible
without putting an untyped string in a body-reference field.

**Raw evidence.** PRB-02 s03 emits `IFC-0001.bodies: ["BOD-0001", "desk edge"]`. The
s04a prompt's computed must-touch list then contains, verbatim, `BOD-0001 and desk edge
must touch`, and Rule 1 says *"Every body gets an extent and a centre"* — so `s04a` emits
`ENV-0006.body: "desk edge"`, and `s03b` emits load-path hops `"arm"` and `"desk edge"`.
The string crosses three stages. `STAGE_PATCH_CONTRACT:102` and
`DESIGN_STATE_CONTRACT:416` both name this: **"A free-string subject or object is a
SCHEMA_FAILURE (R-20)"**, INV-001.

**Boundary: S03, propagating through S03→S04A.** **Type: D (the model has no typed way to
name the desk) then C (the untyped value is carried into the next consumer view).**
**Recurrence: SINGLE-CASE for the exact string; CROSS-CASE as a class — every case needed
to name an external reaction site and none could (CAP-04).**
**Severity:** the most physically honest load path in the corpus
(`["arm","BOD-0002","BOD-0001","desk edge"]`) is expressible **only** by violating INV-001.
**Attribution: ESTABLISHED.**

---

### CAP-11 — Swept-motion evidence for declared transitions

**Capability.** A transition claimed between two configurations must carry evidence that
the motion is clear, not merely that two endpoints exist.

**Reference basis.** BM-003's own upstream OBL-0003 requires *"a continuous path …
with every component connected at every point along it"*, `evidence_route:
SWEPT_INTERFERENCE`. P3 recorded interior-sampling as the discriminating check.

**Raw evidence.** **No transition in any of the six cases carries a path, a sampling
declaration or a swept volume.** The s04b RESPONSE SCHEMA has **no field for any of
them**: `joint_placements`, `state_coordinates`, `transitions {id, from, to,
moving_groups}`, `notes`.

**Boundary: CONTRACT-LEVEL / S04B.** **Type: D — the consumer view cannot express it.
Explicitly NOT a model reasoning failure**, per §9 of the audit instruction.
**Recurrence: CROSS-CASE (6/6) and CONTRACT-LEVEL.** **Severity:** S04's stated purpose
is the swept proof; the artifact that would carry it does not exist.
**Attribution: ESTABLISHED.**

---

### CAP-12 — Unresolved evidence gating commitment

**Capability.** When a stage's own output records that a required fact is absent,
contradictory or unevidenced, the pipeline should not commit an authoritative downstream
state as though it were settled.

**Raw evidence — the pipeline diagnoses its own defects and proceeds anyway.**
- PRB-02 `s03b` emits `BLK-0001` and `BLK-0004` asserting mutual grounding, **and in the
  same file** `S3U-1001` states *"the anchor nut is not fixed to anything. Thus, the
  assembly is not grounded."*
- BM-002 `s03b` emits `BLK-0001` with `promised_features: ["fixed to world"]`, **and in
  the same file** `S3U-1001` states *"no explicit fixity to ground is modeled for the
  housing (BOD-0001)"* — and `blocks` all four of its own blocking relations.
- BM-003 `s03b` `S3U-1001`: *"The load paths reference the ground but no ground body is
  modeled."*
- PRB-03 `s03b` `S3U-1001` correctly names the unblocked `+Z`, `RX`, `RY`.
- Two of six cases ran S03/S04 on a candidate whose own
  `evidence_route_verdict.available` is **`false`** (BM-001 CND-0001, PRB-02 CND-0001).
- `trials.json` records `CHECK_FINDING` entries — `LOADCASE_ROLE_READS_AS_A_PART`,
  `LOADCASE_NAMES_A_PART` — naming the exact defect, while the trial reports
  **`s02_status: "SUCCESS"`**.
- All six Window-2 cases ran only `t1_CND-0001`, while `SelectedCandidate` *"May exist
  only after **every retained candidate** carries s03 and s04a evidence at equal
  obligation coverage (INV-007)"*, and `elimination.eliminated` is `false` in 6/6.

**Boundary: every stage boundary.** **Type: F.** **Recurrence: CROSS-CASE (6/6).**
**Severity:** the architecture's `SAFE_REJECTION` / `FALSE_ACCEPTANCE` poles depend
entirely on this. The *recognition* capability is demonstrably present — the unresolved
layer is the strongest output in the corpus. What is absent is any consequence.
**Attribution: ESTABLISHED that recognition occurs and commitment proceeds; the gating
mechanism is P5.**

---

### CAP-13 — Requirement atomisation and ambiguity preservation at capture

**Capability.** Distinct obligations bound in one sentence must be separated, and a
genuine ambiguity must be recorded rather than silently answered.

**Raw evidence (P4A §G).** **Type A — capture.** The information never entered the state.
- *"every time"* (repetition of the return) is merged into the return requirement in
  **all three PRB-03 trials**; the fixture makes it a separate requirement whose
  obligation carries `route_available: false`.
- *"must not slip **or rotate**"* is merged in **all three PRB-02 trials**; the fixture
  separates them because they are different freedoms.
- The product-identity clause yields no requirement in BM-003 t1/t2 and PRB-03 t1/t3.
- Fixture ambiguities with **no live counterpart in any trial**: the wall type and
  permitted fixings (PRB-01, the reaction site for every load); the signal *scope*
  question (PRB-03); the knock-disturbance magnitude (BM-003, the reason the retention
  obligation is unverifiable).
- PRB-01's refilling is typed `OPERATION` / `SERVICE` / `SERVICE` across trials — the
  fixture raises exactly this as `AMB-0006`, and **the live model answers it differently
  each trial without ever recording it as an ambiguity.**

**Boundary: S01.** **Type: A.** **Recurrence: CROSS-CASE and CROSS-TRIAL.**
**Severity:** an obligation that was never derived cannot be discharged, refused or
counted; a silently-answered ambiguity is a commitment with no record.
**Attribution: ESTABLISHED.** *Note:* `block_scopes` has **no stated vocabulary in the s01
prompt** and is marked optional, so its 0/18 non-conformance is **D, not A** — see §H.

---

### CAP-14 — Repeated-member spatial consistency

**Capability.** N functionally identical members must be realisable as N spatially
distinct instances, and a region owned by several separated bodies must not be collapsed
to one location.

**Raw evidence.** BM-003 `s03` labels three legs `instance_identity: "each of three
identical"` while giving each its own body id — the record simultaneously describes three
legs and nine. `FRG-0001` is owned by `["BOD-0002","BOD-0003","BOD-0004"]` and `s04a`
gives it **one** volume, at leg 1's azimuth; `FRG-0002` likewise. All three functional
regions lie on the `x=0` plane.

**Boundary: S03 (identity), S03→S04A (region multiplicity).** **Type: D.** `region_volumes[]`
is one volume per functional region by schema, so a region owned by three separated bodies
has no way to be three volumes. **Recurrence: SINGLE-CASE in the current corpus (BM-003
is the only multi-instance case) — DO NOT GENERALISE (§H).**
**Severity:** BM-003's OBL-0004 (*"the three ground contacts bound a non-zero area"*)
is satisfied by `s04a` and destroyed by `s04b`. **Attribution: NOT YET ATTRIBUTABLE — P5.**

---

## §E — FAILURE-MODE CLASSIFICATION OF THE NAMED P4A EXAMPLES

Format: source fact → first authoritative representation → still in later stored state? →
does the consumer prompt receive it? → what the consumer produced → **type**.

| # | Item | First authoritative rep. | Still in state? | In consumer prompt? | Consumer output | Type |
|---|---|---|---|---|---|---|
| 1 | `SourceClause` | `s01` `source_clauses[]`, owned by s01 | **Yes** — assurance family, never deleted | **No, by INV-002** | s02 works from requirement statements | **INTENDED BOUNDARY — not a failure** |
| 2 | Stated dimensions (80–100 mm; 18–40 mm) | `s01` `Requirement.quantity_class: BAND` | **Yes** — present in the s02 typed input, read directly | **No** at s04a (prompt excludes requirements) | `scale.absolute: null`, 6/6 | **C** |
| 3 | *"every time"* (PRB-03) | **none** | **Never created** | n/a | no repetition obligation exists | **A** |
| 4 | *"slip or rotate"* (PRB-02) | one merged requirement | merged form persists | yes (merged) | one obligation instead of two | **A** |
| 5 | Fixture ambiguities absent from live s01 | **none** | **Never created** | n/a | decisions made silently | **A** |
| 6 | `principle` representation | `s02` `Candidate.principle` | yes, in whatever shape emitted | yes | S03 reads a shape S02 need not emit | **D** |
| 7 | `BodyHypothesis` / `PhysicalInteractionHypothesis` | **none anywhere** | **no such entity in any artifact or contract family list** | n/a | S03 receives principle + summary prose only | **A at family level — the concept has no home** |
| 8 | `required_by_actors` / `reach_targets` | `s03` output | yes | yes (s03 prompt demands them) | populated | **D — prompt requires, contract does not define** |
| 9 | `blocked_by` referenceability | `s03b` relations | yes | yes | `"NONE"` in direction and/or blocker | **E** (rule stated in contract *and* prompt) |
| 10 | `addresses_obligations` | `s03` bodies/interfaces | yes | yes | BM-003: 11 of 17 obligations claimed by nothing | **E** |
| 11 | Mobility / DOF disposition | **`MobilityExpectation` never authored** | **no instance in any artifact** | **no prompt collects it** | blocking + irrelevance, neither a partition | **D — contract-level impossibility** |
| 12 | Unresolved diagnosing a committed defect | `s03b` `unresolved[]` | yes | yes | commitment proceeds unchanged | **F** |

**No item in the corpus classifies as TYPE B.** Consistent with §A.2: the contracts make
deletion impossible and no raw artifact shows it.

**Item 7 deserves emphasis.** `BodyHypothesis` and `PhysicalInteractionHypothesis` appear
in **no** S02 artifact (live or fixture), in **no** prompt, and in **no**
`DESIGN_STATE_CONTRACT` family. What S03 receives about *what things there are* is the
candidate's `principle` plus a one-sentence `summary`. This is not a lost entity; it is a
**concept with no typed home**, which is why CAP-03's transmitting relations end up in
prose.

---

## §F — CAPABILITIES ALREADY DEMONSTRATED

Stated because a synthesis that reports only gaps is not evidence-based.

1. **Quantity capture and qualifier preservation at S01.** Where the source states a
   quantity, all three trials of every relevant case record `quantity_kinds` and
   `quantity_class` correctly, and `"approximately 1 kg"` survives S02 with its qualifier.
   *Caveat: BM-002's 80–100 mm is the s01 prompt's own worked example, so PRB-01
   (twenty / exactly one) and PRB-02 (18–40 mm) carry the weight of this claim.*
2. **Principle-library selection.** PRB-01 selects `METER_DISCRETE_QUANTITY` and four of
   the fixture's own principles in a live trial. BM-002 selects four distinct conversion
   principles and differentiates `self_locking` correctly (screw true, rack false).
3. **Body decomposition from a named principle.** BM-002 realises `CRANK_SLIDER` as base /
   shaft / crank link / slider with the right joint *types*. PRB-01 invents a hard-stop
   body and a return spring unprompted.
4. **The unresolved layer.** The strongest output in the corpus. `S3U-1001..1004` in
   PRB-01 correctly names the missing kinematic pairing at IFC-0003/IFC-0004 — the exact
   interlock gap of CAP-03. PRB-02, BM-002, BM-003 and PRB-03 each diagnose their own
   grounding or blocking gap in correct engineering language.
5. **Route-availability discipline.** Every observed `route_available` matches the prompt's
   table in every file read.
6. **Envelope symmetry.** BM-003's `s04a` produces exact 120° three-fold symmetry.
7. **Deterministic fidelity.** 59 of 59 stored artifacts across both windows are
   byte-identical to `response.raw_text`. There is no silent repair anywhere.

---

## §G — RECURRENT GENERAL CAPABILITY GAPS

Meeting the §10 threshold: recurrent across unrelated cases, or a direct
contract/representation contradiction, or a producer-consumer impossibility.

| Gap | Recurrence | Type | Threshold met by |
|---|---|---|---|
| **G-1** Load-reaction closure to an external site | 6/6 cases | D+E | universal recurrence + derived-value impossibility |
| **G-2** Retention as a directed, externally-blocked, testable relation | 6/6 cases | E | universal recurrence + explicit contract rule |
| **G-3** DOF totality as a partition | 6/6 + contract | D | producer-consumer impossibility (`MobilityExpectation` owned but never authored) |
| **G-4** Unresolved evidence gating commitment | 6/6 cases | F | universal recurrence + INV-007 text |
| **G-5** Swept-motion evidence for transitions | 6/6 + contract | D | schema cannot express it |
| **G-6** Distinct-pivot / non-degenerate spatial realisation | 5/6 cases | E | cross-case + within-case contradiction (BM-003 s04a vs s04b) |
| **G-7** Functional connection carried in structure, not prose | 4/6 cases | E+D | cross-case + no typed home for transmission |
| **G-8** Candidate representation stability | contract + 2 within-case trial flips | D | prompt self-contradiction |
| **G-9** Requirement atomisation and ambiguity preservation | cross-case + cross-trial | A | recurrence across unrelated cases and trials |
| **G-10** Configuration physical distinctness | 3/6 cases | E | cross-case |

---

## §H — CASE-SPECIFIC ANOMALIES THAT MUST **NOT** BE GENERALISED

- **BM-002's parallel input/output axes** and **zero-length crank**: one case. The
  *general* statement is CAP-01/CAP-03, not "the crank was wrong".
- **PRB-02's `"desk edge"` string**: one case. Generalise only to CAP-10.
- **BM-003's repeated-member collapse**: BM-003 is the only multi-instance case in the
  corpus. **CAP-14 is single-case and is marked NOT YET ATTRIBUTABLE.**
- **BM-001 t1's fabricated numeric predicates** (1000 cycles, 5N, ABS): one trial. Its
  siblings emit `[]` (t2) and `X/Y/Z` placeholders (t3). The general statement is
  *instability of the acceptance-predicate strategy*, not "the model fabricates numbers".
- **BM-003 t3's truncation**: one record, a consequence of obligation-set inflation
  meeting the 8192 cap. Not a reasoning finding.
- **Vocabulary spread** (`configuration.kind` 9 values, `access_side` 3 systems,
  `approach_side` 6 forms, `locator` 9 conventions): **these are unconstrained fields.**
  The s01 prompt gives no `locator` format and no `block_scopes` vocabulary; `Configuration`
  has no `kind` field in `DESIGN_STATE_CONTRACT` at all; `approach_side` has no enumeration
  in the s04a schema. **Reclassify from model defect to D (contract-vs-prompt divergence).**
- **`promised_features`, `self_locking`, `derivation_premises`, `involves_actors`,
  `block_scopes`**: all explicitly optional in their prompts. Their absence is compliance.
  *(One genuine contradiction survives: `blocked_by.required_fields` in
  `DESIGN_STATE_CONTRACT` **requires** `promised_features`, while the s03b prompt marks it
  optional.)*
- **`irrelevance: []`** and **`ELASTICITY` on rigid members**: prompt-compliant. Withdrawn
  as defects.
- **BM-001 envelope overlap**: the s04a prompt told it all three pairs must touch.
  Withdrawn.

---

## §I — ANSWERS TO §12, AND THE QUESTIONS P5 MUST RESOLVE

**1. Is the intended architecture cumulative progressive enrichment?**
**Yes**, established from `STAGE_PATCH_CONTRACT`, `STAGE_PROGRESSION_CONTRACT` and
`DESIGN_STATE_CONTRACT` (§A). Nothing is deleted; nothing is overwritten; invalidation
marks STALE; sufficiency is defined against *"the accumulated DesignState"*.

**2. Where does current evidence show each failure mode?**
**Capture (A)** at S01 — CAP-13, and the absence of any `BodyHypothesis`-like family.
**Persistence (B)** — **nowhere.** Architecturally impossible and evidentially absent.
**Projection (C)** at S03→S04A — CAP-09, the only clean projection loss in the corpus.
**Representation (D)** at contract level — CAP-06, CAP-07, CAP-11, CAP-04's ground,
CAP-10's untyped participant.
**Reasoning (E)** at S03 and S04B — CAP-01, CAP-02, CAP-03, CAP-05, CAP-08.
**Gating (F)** at every boundary — CAP-12.

**3. Already strong:** quantity capture, principle-library selection, body decomposition
from a principle, the unresolved layer, route-availability discipline, deterministic
fidelity (§F).

**4. Repeatedly failing across BM and PRB:** G-1 through G-10 (§G), of which four are
universal (6/6): load-reaction closure, retention testability, DOF totality, and gating.

**5. Apparent model failures that are actually input or representation problems:**
s04a's *"no absolute dimensions"* (its input excludes the requirements); the absence of
swept evidence (no schema field); `irrelevance: []`, `ELASTICITY` on rigid members and the
BM-001 envelope overlap (prompt-compliant); the vocabulary spread (unconstrained fields);
`SourceClause` (INV-002 requires it); the bare-string `principle` (the prompt asks for one).

**6. Failures with sufficient information available:** CAP-01 (s04a's own geometry was in
s04b's input), CAP-02 (all ids and DOF present), CAP-05 (the rule is in both the contract
and the prompt), CAP-08 (the principle was in the input), CAP-04's cyclic and self-looping
paths (the topology was fully supplied).

**7. Scientifically unsupported boundaries on current evidence:**
- **S03→S04A.** It drops the requirements, so no stated quantity can inform the first
  stage that assigns extents (CAP-09).
- **S04A→S04B.** It demonstrably fails to carry arrangement information the very next
  stage needs (CAP-01, BM-003).
- **S03 / S03B.** `MobilityExpectation` is owned here and authored nowhere (CAP-06); the
  `kept_open_by` constraint is stated at s01, s02 and s03 and absent at s03b, and the
  outputs track that exactly (P4A §H.4).

**8. Architecture-level questions for P5 — WHY, not how to fix:**
1. Why is `MobilityExpectation` owned by s03 and collected by no prompt?
2. Where, if anywhere, does the DOF grid get derived from `blocking_relations` +
   `irrelevance`, and what does it do with a cell that is both BLOCKED and IRRELEVANT, or
   BLOCKED and changing in `s04b`?
3. Can `blocked_by` name a reaction site that is not a product body? If not, what is the
   intended encoding of "grounded to the world"?
4. Can `Interface` express force/motion transmission, or must every transmitting relation
   be a `Joint`?
5. What is the canonical shape of `Candidate.principle`, given the s02 prompt contradicts
   itself and the contract does not say?
6. Why does the s04a projection exclude `Requirement`, and is that intended?
7. What consumes `transitions`, given no schema field carries a path or sampling?
8. Does the S04A `elimination` gate have any condition that can fire? It is `false` in 6/6.
9. What is the consequence of a `CHECK_FINDING`, given `s02_status: "SUCCESS"` alongside one?
10. How is `t1_CND-0001` selected in 6/6 cases, given INV-007 requires equal-coverage
    evidence across **all** retained candidates before a selection may exist?
11. Why does the s03b prompt omit the `REFERENCES BETWEEN ITEMS` block the s03 prompt has?
12. What propagates a free-string interface participant into the s04a must-touch list as a
    body id, when INV-001/R-20 names that a SCHEMA_FAILURE?

---

## §J — RAW EVIDENCE ANCHORS

**Architecture.** `ver3/contracts/STAGE_PATCH_CONTRACT.yaml` (:3-6, :48-62, :72, :82,
:85-95, :98-102, :105-107, :131-140, :164-175); `ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml`
(:215-226, :242-250); `ver3/contracts/DESIGN_STATE_CONTRACT.yaml` (:99, :135, :330-342,
:344-364, :372-382, :400-421, :434-438, :442-447, :496, :510-525, :607-610);
`docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md` (:1098-1103 D-11, :1105-1113 D-12).

**Pipeline output.** `ver3/live_runs/window2/r_final/responses/<case>/t1_CND-0001/{s03,s03b,s04a,s04b}.json`
— all 24, read in full; byte-identical to `model_run_records.json` `response.raw_text`.

**Prompts.** `ver3/live_runs/window2/r_final/model_run_records.json` records 0 (s03), 1
(s03b), 2 (s04a), 3 (s04b) and the six s04a must-touch blocks;
`ver3/live_runs/deepseek/q6_fix/model_run_records.json` records 0 (s01 template) and 1
(s02 template, instructions + routes + schema + references + permitted values).

**Live model output.** `ver3/live_runs/deepseek/q6_fix/responses/<case>/t{1,2,3}/{s01,s02}.json`
— 35 of 35 read; record 29 is `RESPONSE_TRUNCATED`.

**Upstream fixtures.** `ver3/assy_v3/fixtures/responses/BM-00{1,2,3}/{s01,s02}.json`;
`ver3/assy_v3/probes/PRB-0{1,2,3}/{s01,s02}.json` + `PRB-01/s02.pre_revision.json` — 13 of 13.
Prompt pairing confirmed by SHA (P4A §H.7).

**Run records.** Both `trials.json`; both `model_run_records.json`.

**Precursor.** `ver3/live_runs/deepseek/phase1_s01/` — metadata only (§C).

---

**Stop condition met. P5 is not started. No fix, prompt change, validator or architecture
change is proposed anywhere in this document.**
