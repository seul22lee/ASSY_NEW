# Window 2 — S03 + S04 implementation report

**Scope actually delivered, stated first.** S03 is implemented, running live and
evaluated on all six cases. **S04 is not implemented.** The consumer-first audit
and the S03 evidence consumed the window, and reporting S04 as delivered would
be the one thing this pipeline is built to prevent. What S04 needs, and what it
turned out to require that nothing produces, is recorded in §2 and §7.

---

## 1. Evidence categories, kept separate

| category | what it is | where used |
|---|---|---|
| **Fixture** | S01 and S02 replayed from recorded responses | the upstream for every S03 run. Window 1 is frozen, so its stages are not re-tested here |
| **Benchmark** | BM-001/2/3 — quality reference, never target answers | 3 of the 6 S03 evaluations |
| **Probe** | PRB-01/2/3 — unseen generalization set | the other 3 |
| **Live provider** | DeepSeek, `deepseek-v4-flash` served, T=1.0 | **every S03 result in this report** |

No S03 output is fixture-backed. There are no recorded S03 responses and none
were authored, deliberately: a fixture written by the same agent that wrote the
checks is the failure mode Window 1 documented at length.

---

## 2. The consumer-first audit, run before any code

Two defects, both found by asking "does every consumer dependency have an
upstream producer, and does every producer have a representation?"

| id | defect | class |
|---|---|---|
| **W2-I1** | S03's contract required `BodyHypothesis` and `PhysicalInteractionHypothesis` **from S02**. Neither is a defined entity family and S02 produces neither. S03 already *owns* `Body` and `Interface` creation, so it cannot also consume them | interface |
| **W2-I2** | S04 is required to create `Envelope`, `SweptVolume` and `SelectionDecision`. **None of the three was defined in `DESIGN_STATE_CONTRACT`** — an s04a that must produce an Envelope had nowhere to put one | schema |

**W2-I1** was corrected by rewriting S03's `required_inputs` to what S02 actually
emits. **W2-I2** justified a schema addition under rule 8 on the strongest
possible grounds — not "the representation is awkward" but "the representation
does not exist". Three families added, 41 → 44.

This is the audit paying for itself: both defects would otherwise have surfaced
as mysterious stage failures after implementation.

**What the schema addition cost.** Adding three families turned the meta suite
red — 5 failures, then 10 while I was fixing it. The families needed an owner in
`STAGE_OWNERSHIP_MATRIX`, entries in `ENTITY_FAMILY_AUDIT` with a real downstream
consumer, an open question and a decision deadline apiece, and honest summary
totals (41 families; PROVISIONAL 3 → 6). The suite is green again at **316
tests**.

Two of those failures are worth naming because they are the contract system
working: the audit refused a `first_downstream_consumer` of `s04b` (not a stage),
and refused `package_items` I had invented to look complete. Inventing a package
id to satisfy that test would have been precisely the defect it exists to catch,
so all three families are recorded as **not yet in the assurance package**, with
the gap carried as `package_debt`.

---

## 3. S03 as built

`ver3/assy_v3/stages/s03_topology_and_mobility.py` — bodies, rigid groups,
joints, interfaces, configurations, a **total** DOF disposition, load paths,
assembly order with retention termination, and functional regions. Thirteen
checks.

**The one structural idea.** `MobilityExpectation` is a total function, not a
declared set. `dof_domain()` computes the domain — every rigid group × every
configuration × every one of six DOF — from the topology, and
`dof_totality_check` verifies coverage against *that*, never against anything the
response claimed. A declared set cannot fail by omission; a total function can.

---

## 4. First evidence: 0 of 6 cases completed

| id | failure | count | class |
|---|---|---|---|
| **W2-F1** | `DUPLICATE_ID: ASM-0001` — `AssemblyStep` used the `ASM-` prefix that `Assumption` already owns in the frozen S01/S02 output | 3/6 | **id namespace** |
| **W2-F2** | `axis_direction` missing on joints — a **FIXED joint has no axis**, and the permitted-value set had no way to say so, forcing a choice between inventing an axis and dropping a required field. It dropped the field | 2/6 | **enumeration gap** |
| **W2-F3** | `RESPONSE_TRUNCATED` | 3/6 | **output budget vs totality** |

**W2-F3 is the significant one.** Median output was **7265 tokens against an 8192
cap — 89% of budget**, and it failed two ways at once: three cases hit the API
cap outright, and PRB-01 *self*-truncated, emitting **42 of its 84 required
dispositions** while still closing valid JSON. The totality principle is correct
and is the reason the stage exists; inline emission of the grid simply does not
fit a one-pass response for a realistic mechanism.

### Root causes

- **RC-1** — id prefixes are not partitioned across stages (W2-F1).
- **RC-2** — a required field whose permitted values exclude a legitimate case
  (W2-F2). The same shape as Window 1's `directionality: null`.
- **RC-3** — the total disposition, transmitted one entry per object, exceeds the
  output budget (W2-F3).

---

## 5. One integrated revision

1. `AssemblyStep` ids move to `ASY-`.
2. `axis_direction` gains **`NONE`** as a value, with the rule that a FIXED joint
   uses it. `NONE` is a value, not an absence.
3. **The disposition is transmitted compactly**: one row per (group,
   configuration) carrying six one-letter codes, and a `detail` block expanded
   *only* for the dispositions that require justification (`BLOCKED_BY`,
   `IRRELEVANT_BECAUSE`). The disposition vocabulary is unchanged and nothing
   downstream ever sees a code — only the wire format changed, because the
   defect was in the wire format.

### Result

| | before | after |
|---|---|---|
| S03 completed | **0/6** | **4/6 SUCCESS, 2 CONTRACT_INCOMPLETE** |
| truncated | 3/6 | **0/6** |
| **DOF coverage** | 42/84 worst case | **1.000 on all six cases** |

The stage's central property — total disposition — now holds everywhere.

---

## 6. Engineering quality: benchmarks beside probes

Compared on maturity, never on content.

| | bodies | groups | joints | interfaces | configs | **DOF cov** | blocked DOF | load paths | regions |
|---|---|---|---|---|---|---|---|---|---|
| BM-001 | 4 | 4 | 3 | 6 | 2 | **1.000** | 10 | 5 | 4 |
| BM-002 | 6 | 6 | 5 | 5 | 3 | **1.000** | 0 | 4 | 4 |
| BM-003 | 3 | 3 | 3 | 5 | 3 | **1.000** | 26 | 5 | 4 |
| PRB-01 | 5 | 5 | 6 | 5 | 4 | **1.000** | 4 | 5 | 4 |
| PRB-02 | 5 | 5 | 4 | 7 | 2 | **1.000** | 0 | 3 | 4 |
| PRB-03 | 6 | 7 | 7 | 6 | 2 | **1.000** | 0 | 6 | 4 |

**Comparable**: DOF coverage, topology scale, interface enumeration, functional
regions (4 on every case), load-path count. Probes are not behind benchmarks on
any of these — PRB-03 produced the largest topology of all six.

**The one real gap, and it is not probe-specific.** `blocked DOF` is 0 on
BM-002, PRB-02 and PRB-03 — three of six, one benchmark and two probes. A
mechanism in which nothing is blocked is not a mechanism. Coverage is total but
**disposition is shallow**: the model reaches for `MAINTAINED_BY_CLASS`, which
costs nothing, and avoids `BLOCKED_BY`, which demands a direction, a named
blocker, a defeat specification and a driver. Totality made the omission
*visible*; it did not make it *stop*.

---

## 7. Second failure set — collected, deliberately not fixed

These became visible only once responses parsed. 105 findings; **~79 are defects
in my own checks**, which is itself the finding.

| id | finding | count | class |
|---|---|---|---|
| **W2-F4** | `OBLIGATION_UNOWNED_AT_S03` — **the S03 response schema contains no field for citing an obligation**, so no response can ever pass this check. 48 findings, **0 true positives** | 48 | **check + schema gap** |
| **W2-F5** | `LOADPATH_HOP_UNKNOWN` — the model traces `BOD → JNT → BOD → IFC → BOD`. An Interface hop is *correct*; my check excluded Interface | 31 | **check defect** |
| **W2-F6** | `interaction_kind: "FIXED"` — a joint-type word in an interface field. The same enumeration collision as Window 1's three `kind` fields | 10 | prompt |
| **W2-F7** | compliance `actuation: "PASSIVE"` — the model describes the physics; the contract wants the *modelling convention* `PRESCRIBED_KINEMATIC` declared, and the prompt never said why | 10 | prompt |
| **W2-F8** | `termination_strategy: "NONE"` — the first body placed needs no retention, and the enum has no way to say so. **Identical in shape to W2-F2** | 3 | enumeration gap |
| **W2-F9** | `blocker_body: "hard stop on housing"` — prose where a body id belongs; the reference target was never specified | 2 | prompt |
| **W2-F10** | `JOINT_GRAPH_DISCONNECTED: RGP-0002` — a rigid group joined to nothing. **A genuine topology defect, correctly caught** | 1 | reasoning |

W2-F4 and W2-F5 deserve the emphasis. A check that fires 48 times with zero true
positives is worse than no check: it is the `actor_citation` and `PART_NOUNS`
lesson from Window 1, repeated by me one window later. W2-F8 repeating W2-F2
inside the same window says the enumeration-gap class needs a standing rule —
every closed value set needs a member meaning "legitimately none" — rather than
being rediscovered per field.

---

## 8. Remaining debts

| id | debt |
|---|---|
| **D2-1** | **S04 is not implemented.** S04a (envelopes, reach, AABB feasibility) and S04b (placement, sampling, swept occupancy) are both computational rather than LLM work; the families they need now exist, and nothing else blocks them |
| **D2-2** | W2-F4/F5: two checks must be corrected before their findings mean anything. W2-F4 additionally needs a schema field — obligations cannot be *owned* by a mechanism that has no way to cite them |
| **D2-3** | Shallow disposition (§6): totality is achieved, depth is not |
| **D2-4** | S03 runs at ~89% of output budget even after compaction. Adding S04's per-body content to one response will not fit; S04 must be its own call, which the two-pass contract already anticipates |
| **D2-5** | Every S03 result is one model, one temperature, one candidate per case. INV-007 wants every retained candidate embodied; the harness supports it and cost did not permit it |
| **D2-6** | No maturity profiler exists for S03 output. §6 is hand-built; the Window 1 profiler does not cover topology |

---

## 9. Recommendation

> ## WINDOW 2 REQUIRES ONE MORE STABILIZATION CYCLE

S03 is real: it runs live on all six cases, achieves **total DOF coverage on
every one**, produces comparable topology, load paths and functional regions for
probes and benchmarks alike, and no benchmark-specific reasoning was introduced —
no case identifier, product noun or mechanism name appears anywhere in
`assy_v3`.

But the window cannot be frozen against its own stop criterion. S04 does not
exist, so "S04 produces a geometry-independent embodiment definition suitable for
S05" is not merely unmet but untested. Two S03 checks are known to be wrong, one
of them unpassable by construction. And the disposition depth gap (§6) is a
quality deficiency in exactly the sense this window is meant to close.

The next cycle is well defined: correct W2-F4/F5 and the two enumeration gaps in
one pass, address disposition depth the way Window 1 addressed reasoning depth —
by stating what the field is *for* — and then implement S04a and S04b as the
computational stages they are.

---

# Cycle 2 — S04 implemented, S03→S04 exercised

## 10. S03 stabilization, limited to what blocked S04

Four corrections, no other polishing:

| was | now |
|---|---|
| `obligation_ownership_check` searched a JSON blob for an obligation id, which **no response could satisfy** because the schema had no field to cite one — 48 findings, 0 true positives | bodies and interfaces carry `addresses_obligations`; the check reads that field. The property became *expressible* rather than merely unmeasured |
| `load_path_check` rejected Interface hops — 31 findings describing correct paths | an Interface is a legitimate hop: a load crosses it |
| `termination_strategy` had no value for a body nothing retains | `NONE` added. **Second instance of this shape in one window** (after `axis_direction`), which is why it is now a stated rule: every closed value set needs a member meaning "legitimately none" |
| blocked-DOF depth: `blocker_body` took prose | must be a body **id**, with the reason stated — *"a mechanism in which nothing is blocked is a pile of loose parts, and the next stage has nothing to prove clear"* |

---

## 11. S04 as built

`ver3/assy_v3/stages/s04_envelope_and_motion.py`. Two passes, nine checks.

**The division of labour is the design.** The model proposes **extents and
placements**; it is never asked whether anything overlaps. Interference, reach,
swept occupancy, assembly paths and load-path continuity are **computed** from
its numbers. An LLM asked "do these interfere?" will answer, and the answer is
unfalsifiable. Asking only for the inputs keeps every spatial verdict
reproducible.

**Conservatism is stated once and honoured everywhere.** Every extent is an
axis-aligned box, so **no-overlap is a proof of clearance and overlap is not a
proof of collision** — the real bodies are smaller than their boxes, and the
rotation re-bound only ever grows them. Every overlap-derived result is therefore
reported `NOT_VERIFIED`, never `FAIL`. `FAIL` is deliberately absent from the
overlap vocabulary; reporting AABB overlap as interference would manufacture
failures the geometry cannot support.

Sampling is declared once, non-adaptive, with interior points — endpoint-only
evidence is the most effective way to make an unbuildable mechanism look correct,
because the endpoints are where a designer has already looked.

---

## 12. Producer-consumer: can S04 work from S03 alone?

**Enforced by whitelist, not by hope.** `mechanism_projection()` passes exactly
the nine S03-owned families and nothing else. A blacklist would quietly admit
every family added later, and this boundary is the thing under test.

**Answer: yes, with one recorded gap.** Every case that reached S04 completed both
passes from the mechanism alone. Nothing was reconstructed from S01, S02, the
request text, the CAD references or the Oracle packs.

| id | producer-consumer finding | class |
|---|---|---|
| **W2-P1** | **s04a's contract requires `actor_reach_requirements` from s03. S03 owns no family and no field that carries an actor's reach forward.** `Actor` is an S01 family, so reach feasibility cannot be evaluated from S03 output at all | **interface** |

W2-P1 was **recorded on all four runs and never worked around**. The instruction
was explicit that a missing input is an interface failure, not a licence to reach
back, and reaching back to `Actor` would have been the easy and wrong move: it
would have made s04a work while leaving the boundary broken.

**A second producer-consumer defect, found by computation rather than by audit:**
`JOINED_BODIES_DO_NOT_MEET: JNT-0001 joins BOD-0005 and BOD-0004, separated by 5`
— S04a placed bodies that S03 declared jointed so that they do not touch. Neither
stage is individually wrong; the *pair* is inconsistent, and only a check that
reads both catches it.

---

## 13. Evidence

| category | content |
|---|---|
| **Fixture** | S01+S02 replayed for all six cases |
| **Live provider** | every S03, s04a and s04b result — `deepseek-v4-flash`, T=1.0 |
| **Benchmark** | BM-001/2/3 — **3/3 completed the full chain** |
| **Probe** | PRB-01/2/3 — **1/3 completed it** |

| | S03 | s04a | s04b |
|---|---|---|---|
| SUCCESS | 4/6 | **4/4 of those reaching it** | **4/4** |
| RESPONSE_TRUNCATED | 2/6 (PRB-01, PRB-03) | — | — |

**Every case that produced a mechanism produced a complete spatial evaluation.**
S04 did not fail once.

**The truncation is a regression I caused.** Adding `addresses_obligations` to the
S03 schema in §10 grew the response, and the two largest topologies — both probes
— now exceed the 8192-token cap that the compact mobility encoding had just
brought them under. The schema fix and the budget fix are in tension, and I
traded one for the other without noticing until the run.

### Engineering maturity, benchmarks beside probes

| case | kind | bodies | joints | configs | envelopes | region volumes | s04 findings |
|---|---|---|---|---|---|---|---|
| BM-001 | bench | 3 | 2 | 2 | 3 | 4 | 10 |
| BM-002 | bench | 5 | 5 | 3 | 5 | 4 | 24 |
| BM-003 | bench | 5 | 4 | 2 | 5 | 2 | 14 |
| PRB-02 | probe | 3 | 2 | 2 | 3 | 4 | 11 |

PRB-02 is indistinguishable from BM-001 on every column. **But one probe is not
evidence about probes.** Two of three never reached S04, so criterion 4 rests on a
single case and cannot be claimed.

### The 59 S04 findings

Dominated by `swept_clearance` (18), `assembly_path` (15), `region_occupancy` (11)
and `configuration_interference` (10) — the stage doing exactly its job. Nearly
all are `NOT_VERIFIED` by construction. Two are of a different quality:
`REGION_OCCUPIED_BY_ITS_OWNER` (a design promising ACCESS and putting a body in
it) and `JOINED_BODIES_DO_NOT_MEET`. Whether the NOT_VERIFIED volume reflects
genuinely tight arrangements or an over-conservative box model is **not yet
established**, and stating which would be guessing.

### Knowledge boundary and benchmark neutrality

No case identifier, product noun, mechanism name or benchmark-derived topology
appears anywhere in `assy_v3` — grep-verified. S04 knows nothing about products:
it knows boxes, axes, samples and interfaces. **316 tests pass**; the frozen
Window 1 fixture path is unchanged (SUCCESS/SUCCESS on all three benchmarks).

---

## 14. Failures, classified

| id | finding | count | class |
|---|---|---|---|
| **W2-P1** | `actor_reach_requirements` has no producer | 4/4 | **interface** |
| **W2-F11** | S03 truncates on the two largest topologies after the schema addition | 2/6 | representation vs output budget |
| **W2-F12** | `addresses_obligations` present in the schema but unpopulated | 19 | prompt |
| **W2-F13** | S04a places jointed bodies apart | 3 | reasoning |
| **W2-F14** | `interaction_kind` still receives joint-type words | 4 | prompt |
| **W2-F15** | `IRRELEVANT_BECAUSE` cites a scenario carrying a load case | 4 | reasoning |

Root causes: **RC-4** — the S03 response carries the whole mechanism *and* the
whole mobility grid *and* now obligation traceability in one emission, and the
budget is the binding constraint (W2-F11, and the cause of the W2-F12 omissions).
**RC-5** — fields added to a schema without stating what they are *for* get
omitted or filled with the nearest vocabulary to hand (W2-F12, W2-F14); the same
lesson Window 1 recorded, arriving again.

**No integrated revision was applied this cycle.** These were collected after the
evaluation, and the instruction permits one revision — spending it without a
regression run would leave the window in a less-known state than it is now.

---

## 15. Remaining debts

| id | debt |
|---|---|
| **D2-7** | **W2-P1.** Either S03 carries actor reach forward as a `FunctionalRegion` role with an actor reference, or the s04a contract drops the requirement. It cannot stay as it is |
| **D2-8** | S03 output does not fit one response for larger topologies. The mobility grid was compacted once; the mechanism itself is now the cost. S03 probably has to become two calls, as S04 already is |
| **D2-9** | Probe coverage of S04 is 1/3. Criterion 4 is unevidenced, not failed |
| **D2-10** | Whether the NOT_VERIFIED volume is real tightness or box conservatism is unmeasured |
| **D2-11** | The selection gate is implemented and checked but never exercised: one candidate per case was embodied, so no gate decision was ever taken |
| **D2-12** | S04's numbers are relative. Nothing yet checks that a relative system stays consistent between s04a and s04b |

---

## 16. Recommendation

> ## WINDOW 2 REQUIRES ONE MORE STABILIZATION CYCLE

Against the six criteria: **(1) S04 fulfils its responsibility** — it ran four
times and completed both passes every time, producing computed, conservative,
reproducible spatial verdicts. **(2) S04 operates on S03 output alone** —
whitelisted, with the single missing input recorded rather than reconstructed.
**(5) No benchmark-specific reasoning** — verified. **(6) Limitations documented.**

But **(3) producer-consumer boundaries are not stable**: W2-P1 is a live gap and
W2-F13 shows the S03/S04 pair can be mutually inconsistent. And **(4) probe
maturity is unevidenced**: one probe of three reached S04, because my own S03
schema addition reintroduced truncation on the largest topologies.

The next cycle is small and well defined: close W2-P1 at the contract level, split
S03's emission the way S04 is already split, and re-run — at which point criteria
3 and 4 can be answered with evidence rather than with one case.

---

# Cycle 3 — blockers closed, full regression, dashboard

## 17. The three blockers

### A. `actor_reach_requirements` — RESOLVED

The correct owner was already in S03's responsibilities. An ACCESS or APERTURE
`FunctionalRegion` exists *because* some actor must get to something, so the
region now carries `required_by_actors` and `reach_targets`. No new family, no
backward reach to `Actor`, no contract rewrite.

The gap check was made **evidence-based** rather than unconditional: it fires
only when a case declares access regions and none names an actor.

**Result: 0 actor-reach interface gaps across all six cases** (was 4/4).

### B. `JOINED_BODIES_DO_NOT_MEET` — PARTIALLY RESOLVED

The general invariant is *a body pair the topology connects must be placed
touching*. It is now derived once, by `required_contacts()`, from S03's own joint
graph and CONTACT/INTERFERENCE/COMPLIANT interfaces — and **the same derived set
feeds both the s04a prompt and the check**, so producer and checker cannot
disagree about what the rule is. The pairs are handed to s04a as data, not prose.

**Result: 2 occurrences remain** across six cases. Improved, not eliminated. No
product was patched.

### C. Token budget — RESOLVED

S03 was split into two passes, mirroring S04's existing two-pass structure:
**s03** emits the mechanism (bodies, groups, joints, interfaces, configurations,
functional regions); **s03b** emits the mobility grid, load paths and assembly
order, consuming the topology s03 just fixed.

No obligation was dropped, no topology truncated, no probe simplified and no
limit raised. Every field survives; only the emission is halved.

**Result: 0 truncations. All six cases reach S04** (was 4/6).

One further defect surfaced and was fixed as part of the same revision: a
`detail` block returned as a non-mapping raised `ValueError`, which `base.py`
did not catch. A response-shape problem must be `SCHEMA_FAILURE`, never a crash.

---

## 18. Full regression — all benchmarks, all probes

| case | s03 | s03b | s04a | s04b |
|---|---|---|---|---|
| BM-001 | CONTRACT_INCOMPLETE | SUCCESS | SUCCESS | SUCCESS |
| BM-002 | SUCCESS | SUCCESS | SUCCESS | SUCCESS |
| BM-003 | SUCCESS | SUCCESS | SUCCESS | SUCCESS |
| PRB-01 | CONTRACT_INCOMPLETE | SUCCESS | SUCCESS | SUCCESS |
| PRB-02 | SUCCESS | SUCCESS | SUCCESS | SUCCESS |
| PRB-03 | CONTRACT_INCOMPLETE | SUCCESS | SUCCESS | CONTRACT_INCOMPLETE |

**6/6 reach a meaningful S04 outcome. 3/3 probes reach it** (was 1/3).

`CONTRACT_INCOMPLETE` is a declared, itemised omission — not a failure and not a
silent pass.

**S03**: DOF totality clean on the split cases; interfaces, load paths and
functional regions produced for every case; referential integrity holds.
**S04**: envelopes, region volumes, reach results, joint placements, state
coordinates, transitions with declared non-adaptive sampling, swept occupancy,
assembly paths and load-path continuity — computed for every case.
**Interface**: S04 consumed the nine-family whitelist only; no reconstruction
from S01, S02, request text, CAD or Oracle packs.

Remaining findings are dominated by `blocking_relation` (191) — B-coded DOF whose
`detail` is not expanded. Real, general, and the depth debt named in §6, now
counted once per relation rather than once per missing field.

**Benchmark vs probe maturity**: probes produce the same artifact classes at the
same completeness as benchmarks. PRB-03 is the only case whose s04b is
CONTRACT_INCOMPLETE, and it declares why.

**No benchmark-specific logic**: grep-verified; **316 tests pass**; Window 1
fixture path unchanged.

---

## 19. Dashboard

`ver3/out/pipeline_dashboard.html` rebuilt — 9.8 MB, 0 broken links, well-formed.
Discovery stayed generic: any `live_runs/<provider>/<label>/responses/<case>/
<variant>/s??.json` is picked up, so a new stage or run label appears without
editing the generator.

Per case, S01–S04: complete structured output (collapsible, never summarised),
per-family tables, producer handoff, and **24 harness finding tables reproduced
verbatim**. The dashboard computes no verdict of its own — live output is
labelled `NOT VERIFIED`, and PASS/FAIL/WARNING appear only as the harness
recorded them.

### Visualisations now available (36 SVG views, 3 per case per run)

Derived **only** from S04 structured output: body envelopes as scaled
axis-aligned boxes in XZ/XY/YZ, functional-region volumes as dashed boxes, joint
origins as markers with their axis on hover. Every view is labelled *inspection
view only — not CAD, not authoritative geometry*. A body S03 declared but S04
never sized is **listed as unplaced rather than drawn**; nothing is invented.

### Not possible from current stage data

Swept-volume *envelopes* (computed transiently inside the check, never stored as
the `SweptVolume` family the schema now defines); motion paths as curves (only
endpoint coordinates and a sample count exist); engagement sites (s04b's contract
extends `Interface.engagement_site`, which is not implemented); true part shape
(no feature exists before S05). Each is shown as structured data with the
visualisation marked unavailable.

The hand-built CAD references remain in their separate labelled track.

---

## 20. Freeze decision

| # | criterion | verdict |
|---|---|---|
| 1 | three blockers resolved | **A yes, C yes, B partially** — 2 occurrences remain |
| 2 | all cases reach a meaningful S04 outcome | **yes, 6/6** |
| 3 | S03→S04 handoff structurally sufficient | **yes** — whitelist enforced, 0 interface gaps, no reconstruction |
| 4 | probe maturity comparable | **yes** — same artifact classes at the same completeness, 3/3 |
| 5 | no benchmark-specific logic | **yes** |
| 6 | no known false pass | **no** — see below |
| 7 | remaining issues are debts, not architecture blockers | **yes** |

> ## WINDOW 2 REQUIRES ONE MORE STABILIZATION CYCLE

Five of seven conditions are met outright, and the window is in far better shape
than at the start of this cycle: every case now completes the chain, the actor
gap is closed at the right layer, and the token regression is gone.

Two things prevent a freeze, and both are stated rather than argued away:

- **Blocker B is not closed.** Two placements still contradict the topology that
  produced them. The invariant is now derived once and shared, which is the right
  structure, but the reasoning still violates it.
- **A known false pass exists.** `blocking_relation` fires 191 times, meaning the
  B-coded DOF carry no defeat specification — yet s04b returns SUCCESS and the
  swept-clearance check reports on motion whose blocking relations were never
  specified. A stage that passes while the evidence for its central claim is
  missing is exactly the condition criterion 6 forbids.

Neither is architectural. The next cycle is small: require `detail` for every
B-coded DOF at the completeness level so an unexpanded relation is
`CONTRACT_INCOMPLETE` rather than a finding beside a SUCCESS, and give s04a the
touching constraint as a post-condition it must satisfy rather than an
instruction it may overlook.

**Do not begin S05.**

---

# Cycle 4 — completion semantics, provenance, freeze

## 21. What prevented false-positive completion

`blocking_relation` ran as a **post-hoc check**, after the stage had already
returned SUCCESS. A BLOCKED_BY without its defeat specification is a claim
without its evidence, and the stage was passing anyway — 191 findings sitting
beside a green status. s04b then reported motion clear against constraints
nobody had specified, and reset the incompleteness it had inherited.

## 22. How completion semantics were corrected

Mandatory evidence moved from *checks* into `completeness()`, which is what makes
a stage CONTRACT_INCOMPLETE. Three places, one principle:

- **s03b** — a `BLOCKED_BY` missing any of `blocked_direction`, `blocker_body`,
  `defeat_specification`, `driver`, or an `IRRELEVANT_BECAUSE` naming no
  scenario, is declared incompleteness.
- **s04a** — a body pair the topology connects, placed apart, is declared
  incompleteness. This also resolved blocker **B** by attribution: gaps of
  1.0–1.5 in a system whose bodies are a few units across are **s04a reasoning**,
  not checker tolerance, so the responsible layer now declares it.
- **s04b** — **propagation**. Where the consumed `MobilityExpectation` carries
  blocked DOF with no defeat specification, s04b inherits that incompleteness
  instead of resetting it.

No validator was suppressed and no finding downgraded.

Demonstrated on PRB-01: s03b declares 75 blocked DOF without defeat
specification → s04a declares one pair placed 0.5 apart → s04b inherits both.
Three stages, three declarations, **no SUCCESS anywhere on the chain**.

## 23. Dashboard provenance fix

`stage_evidence()` now reads **both** artifact families — `window_report*.json`
(fixture replay) and `live_runs/*/trials.json` (live provider) — and reports the
**strongest** recorded evidence, naming its source beside every badge. Two rules
proved necessary and both were found by testing the fix against itself:

- **Within one evidence tier the WORST status wins.** The first version preferred
  SUCCESS, which let a passing pass mask an incomplete sibling — the same masking
  the whole fix exists to remove.
- **Scoping is PER STAGE**, to the newest run carrying a status for that stage. A
  global "newest run" filter erased S01/S02 evidence (Window 2 runs replay those
  stages and record nothing for them); no filter at all resurrected defects
  already fixed.

`run_window.py` was **not** modified: manufacturing fixture verdicts for probes
would cure the symptom with weaker evidence.

**Result: 0 panels say NOT VERIFIED while holding a live artifact** (was every
probe stage). 75 provenance labels; 45 CONTRACT INCOMPLETE pills, visually
distinct from PASS, FAIL, WARNING and NOT VERIFIED.

## 24. Final regression — all badges from live provider validation

| case | S01 | S02 | S03 | S04 |
|---|---|---|---|---|
| BM-001 | PASS | FAIL | CONTRACT_INCOMPLETE | CONTRACT_INCOMPLETE |
| BM-002 | PASS | WARNING | CONTRACT_INCOMPLETE | CONTRACT_INCOMPLETE |
| BM-003 | PASS | FAIL | CONTRACT_INCOMPLETE | CONTRACT_INCOMPLETE |
| PRB-01 | PASS | WARNING | CONTRACT_INCOMPLETE | CONTRACT_INCOMPLETE |
| PRB-02 | PASS | WARNING | FAIL | WARNING |
| PRB-03 | PASS | PASS | CONTRACT_INCOMPLETE | CONTRACT_INCOMPLETE |

**All six cases reach S04.** Benchmark and probe distributions are
indistinguishable — the only PASS at S02 is a probe, and the only S03 FAIL is a
probe's token-budget truncation. **316 tests pass.**

## 25. Are the remaining blockers architectural?

**No.** Every one is reasoning, prompt or budget:

| debt | class |
|---|---|
| blocked DOF carry no defeat specification (75 on PRB-01) | **reasoning** — now declared, not hidden |
| one body pair still placed apart (0.5) | **reasoning** — now declared by its owner |
| PRB-02 s03b truncation | **budget** — pass B grew when detail became mandatory |
| `SweptVolume` computed transiently, never stored | representation debt |
| selection gate implemented, never exercised | unevidenced capability |
| S02 FAIL/WARNING on four cases | inherited Window 1 capability limit, already recorded |

Nothing requires a schema or architecture change. The representation expressed
every fact this cycle needed.

## 26. Can Window 2 be permanently frozen?

| # | condition | verdict |
|---|---|---|
| 1 | no known false-positive completion | **yes** — mandatory evidence gates SUCCESS at three stages |
| 2 | incomplete evidence propagates as CONTRACT_INCOMPLETE | **yes** — demonstrated end to end |
| 3 | S03→S04 consistency stable | **yes** — whitelist projection, 0 interface gaps, inconsistency attributed to its owner |
| 4 | comparable benchmark/probe maturity | **yes** — same artifact classes, same status distribution |
| 5 | all probes have real recorded validation evidence | **yes** — and the dashboard now shows it |
| 6 | no benchmark-specific reasoning | **yes** — grep-verified |
| 7 | remaining issues explicit debts | **yes** — six, all named above |

> ## WINDOW 2 FROZEN

Frozen means the **boundaries and the reporting are trustworthy**: S04 works from
S03's projection alone, a stage cannot claim SUCCESS while the evidence for its
claim is missing, incompleteness propagates rather than resetting, and no badge
asserts more than its artifact supports.

It does **not** mean the designs are complete. Most cases end CONTRACT_INCOMPLETE,
and that is the window working as intended — the incompleteness was always there,
and until this cycle it was reported as success.

**Do not begin S05 without addressing the blocked-DOF depth debt**, which is now
the largest declared gap and the one S05 would inherit.

---

# Cycle 5 — structural ambiguity removed (R-1..R-4)

One integrated revision, four coordinated changes, no benchmark- or
model-specific behaviour.

**R-1 consistency.** `S03_CONTRACT.blocking_relation_rule` was made authoritative
in code: `BLOCKING_REQUIRED` is its field list, and the prompt now shows those
names **as keys**. The contract had always modelled a blocking relation as a
first-class thing carrying `retained_group` and `configurations` — relation-level
facts. The implementation had buried them in per-DOF detail, which caused both the
name drift and the bookkeeping explosion.

**R-2 false negatives.** `canonicalise_blocking()` binds one explicit, documented
alias set and **records every rename**, so a supplied fact is never reported
missing and a rename is never mistaken for a native field. `relations_of()` also
accepts relations still expressed in the older per-DOF shape. The validator was
not weakened: the same seven fields are still required.

**R-3 deterministic derivation.** `derive_mobility()` computes the total DOF
disposition from joint classes, blocking relations and irrelevance claims:
free-by-class → INTENDED, covered by a relation → BLOCKED_BY, declared → 
IRRELEVANT_BECAUSE, otherwise MAINTAINED_BY_CLASS. `free_dof()` is ordinary
axis-relative kinematics, product-independent. This finally implements the
contract's own statement that the LLM role for totality is NONE.

**R-4 prompt simplification.** s03b: 3294 → **2684 chars**, while gaining the
explicit key list it previously lacked. Shorter *and* more precise.

## Quantified result

| | before | after |
|---|---|---|
| full chain SUCCESS | 0/6 | **4/6** (BM-001, BM-003, PRB-01, PRB-02·s04b) |
| findings | 313 | **240** |
| grid cells authored by LLM | 48–126/case | **0** |
| relations recognised | 0 of 262 | **31 of 31** |
| entries derived | 0 | **420 (13.5×)** |
| renames required | — | **0** |
| tests | 316 pass | **316 pass** |

**False-negative reduction:** the entire 262-relation class disappeared, and it
disappeared because the information was there all along. 73 findings resolved net.

## Acceptance criteria

1. false negatives substantially reduced — **yes**, the dominant class is gone.
2. contract/prompt/parser/validator agree — **yes**, one vocabulary from the contract.
3. LLM bookkeeping reduced — **yes**, 13.5× moved to deterministic derivation.
4. prompt complexity reduced — **yes**, shorter and more precise.
5. benchmark and probe maturity improve together — **yes**: 2 of 3 benchmarks and
   2 of 3 probes now complete the chain; both groups improved from zero.
6. no benchmark-specific behaviour — **yes**, grep-verified.
7. no model-specific behaviour — **yes**; the alias map is declared, recorded, and
   was unused this run.

## Remaining, with earliest cause

| finding | earliest cause |
|---|---|
| `UnresolvedDecision.blocks → BLK-0001` dangling (BM-002, PRB-03 s03b) | **representation** — a blocking relation has no entity to be referenced. First Window 2 evidence meeting rule 8's bar |
| `configuration_interference` 47, `assembly_path` 39, `swept_clearance` 24 | **validator** — AABB conservatism; near-vacuous, all NOT_VERIFIED |
| `dof_totality` 26 | **derivation** — groups with no joint get no free DOF; needs review |
| `region_occupancy` 10 | **validator** — ACCESS/APERTURE overlapping its owner is expected (R-4 of the analysis, not yet applied) |
| `obligation_ownership` 19 | **prompt** — `addresses_obligations` still unpopulated |
| S02 closure ~91% | **model capability**, already recorded |

Nothing here is architectural except the first, which is a schema question with
evidence behind it for the first time.
