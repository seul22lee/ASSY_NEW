# S02→S03→S04 reasoning-gap analysis

Diagnosis only. Nothing was implemented. Evidence is the live runs under
`ver3/live_runs/`, the contracts, the validators and the benchmark references as
quality bars.

---

## 1. Current reasoning quality

| stage | live status (6 cases) | what the status actually reflects |
|---|---|---|
| S02 | 1 PASS, 3 WARNING, 2 FAIL | residual `obligations_created` closure, ~91%, already diagnosed as an emission-order limit |
| S03 | 5 CONTRACT_INCOMPLETE, 1 FAIL | **almost entirely one defect, and it is not a reasoning defect — see §3** |
| S04 | 5 CONTRACT_INCOMPLETE, 1 WARNING | **inherited from S03 by design; the propagation is working** |

Engineering content, benchmarks beside probes: bodies 3–6, joints 2–7,
configurations 2–4, interfaces 5–7, functional regions 2–4, load paths 3–6, DOF
coverage 1.000. **Probes are not behind benchmarks on any structural measure**;
PRB-03 produced the largest topology of the six. The maturity question is
therefore not "probe vs benchmark" — it is "why does every case end incomplete".

---

## 2. Major deficiencies observed

- **D-α** 262 `BLOCKED_BY` codes across five cases, and the completeness check
  reported **0** as carrying a defeat specification.
- **D-β** One body pair the topology connects placed 0.5 apart at S04a.
- **D-γ** `region_occupancy` fires on ACCESS and APERTURE regions overlapping
  their own owning body.
- **D-δ** `assembly_path` produces 15–29 findings per run, all NOT_VERIFIED.
- **D-ε** S02 `obligations_created` closure plateaus at ~91%.

---

## 3. Causal trace of D-α — the dominant deficiency

Symptom: `s04b` CONTRACT_INCOMPLETE → *"inherited from s03: 75 blocked DOF have
no defeat specification"* → `s03b` CONTRACT_INCOMPLETE → *"75 blocked DOF carry
no defeat specification"*.

Tracing upstream instead of accepting that:

| step | evidence |
|---|---|
| S01 output | scenarios, actors, requirements present |
| S02 output | LoadCases present — the `LOAD` driver is available upstream |
| S03 reasoning | **the model authored a complete relation for every B-coded DOF** |
| S03 output | `{"blocked_by": ["BOD-0002"], "direction": "-X", "test": "Attempt to translate BOD-0001 relative to BOD-0002 in X; if it moves, the catch is not engaged.", "reason": "LOAD"}` |
| validator | requires `blocker_body`, `blocked_direction`, `defeat_specification`, `driver` — **matches on names, finds none, reports 75 missing** |

**Earliest cause: the four required keys are described in prose and never shown
as keys.** Every other field in the S03 response schema appears as a named key;
these appear as `detail {<DOF>: {...}}` — literally `{...}` — with the names only
in the RULES sentence *"the BODY ID that stops it, the direction, how a test
would defeat it, and why it must be blocked"*. The model covered all four
concepts faithfully, with natural names, and even used a legal `driver` value
(`reason: "LOAD"`).

So the engineering reasoning is **present, complete and correct**, at a per-DOF
granularity, including a genuine defeat test. The pipeline reports it as absent.

**This is a false-negative cascade** — the exact mirror of the false-positive
cascade closed last cycle. Having stopped SUCCESS-on-missing-evidence, the
pipeline now produces INCOMPLETE-on-present-evidence. Both come from the same
place: status derived from a name match rather than from the engineering content.

Nothing downstream of this point is diagnosable until it is fixed. Roughly 95% of
current S03/S04 findings are downstream of it.

---

## 4. Competing hypotheses, tested

| hypothesis | supporting evidence sought | falsifying evidence found | verdict |
|---|---|---|---|
| **H1** Output budget: the model truncates before writing detail | responses at the cap, `finish_reason: length` | 12 of 13 S03 calls at **1380–7860 tokens with `finish: stop`**; details fully written | **falsified** |
| **H2** Model too weak to reason about constraint and its defeat | empty or vacuous detail | 28/30/56 complete relations per case, each with a named blocker, a direction and an executable test | **falsified — decisively** |
| **H3** Information unavailable upstream | no LoadCase, no scenario to cite | LoadCases present; the model used `LOAD` as its reason | **falsified** |
| **H4** DOF grid too large to reason about | detail present for early DOF, absent later | present uniformly across all 78 cells of PRB-01 | **falsified for detail**; remains live for §6 |
| **H5** Required keys unbound because shown as prose, not keys | model emits the concepts under its own names | **exactly that, in all five cases** | **supported** |
| **H6** Validator name-matching too literal | check passes when names are aligned | consistent with H5; same defect, other layer | **supported** |

H5 and H6 are one defect seen from two sides: the **producer was not told the
keys** and the **consumer matched only on keys**.

Contradictory evidence recorded: PRB-02's S03 pass B *did* hit the cap
(8192, `finish: length`), so budget is a real but **secondary** constraint — it
explains one case out of thirteen calls, not the 262 relations.

---

## 5. Missing intermediate representations

- **M-1 — no retention-relation entity.** The engineering fact is *"body A is
  retained against body B in direction d, because of driver x, defeated by test
  t"* — a handful per mechanism. The pipeline has no place to put it, so it is
  expressed 6×(groups×configurations) times inside the DOF grid. BM-003 authored
  56 grid details for what is mechanically a few retention facts. The totality is
  correct **as a check** and wrong **as an authoring unit**.
- **M-2 — no physical-effect chain between S02 and S03.** S02 yields a principle
  family; S03 must produce bodies, joints and interfaces. Nothing in between
  states *what physically acts on what, in what order*. `JOINT_GRAPH_DISCONNECTED`
  and D-β are the signature of topology invented rather than derived.
- **M-3 — no symbolic spatial relations.** S04a places bodies from a prose list
  of pairs that must touch. There is no typed relation (`coaxial`, `seated_on`,
  `inside`) that placement could satisfy, so placement is free invention checked
  afterwards. D-β follows directly.
- **M-4 — no engagement localisation.** `Interface.engagement_site` is in the
  s04b contract and unimplemented, so "where do these bodies actually meet" has
  nowhere to live.

---

## 6. Stage-decomposition problems

- **Discovery and verification are combined.** `defeat_specification` is a
  *verification design* artifact demanded inside a *topology* step. It belongs
  with the negative-control planning that S08 owns. The model can write it — it
  did — but requiring it here makes topology quality contingent on test design.
- **Authoring granularity mismatched to the engineering unit** (M-1). Real
  boundary: author retention relations, then **derive** the DOF grid mechanically
  from the joint graph plus those relations, and let the existing totality check
  verify. The S03 contract already says the LLM role is *NONE* for totality —
  the implementation contradicts its own contract by asking the model to author
  the whole grid.
- **S04a places before relations are typed** (M-3).
- **Checks run after the stage that could have used them.** `required_contacts`
  is computed and handed to s04a as prose, then checked afterwards; nothing lets
  s04a satisfy it constructively.

Not a decomposition problem: the S03 A/B split. It corresponds to a real
boundary (what exists / how it behaves) and it removed truncation.

---

## 7. Knowledge-layer gaps

Failures are **not** knowledge failures. The model supplied support, retention
and defeat reasoning unprompted. Two general primitives would nevertheless make
the reasoning derivable rather than re-invented per case:

- **K-1 retention-termination templates.** The trichotomy (LATER_BODY_COVER /
  ROTATION / ELASTICITY) exists as an enumeration but carries no *consequences*.
  A template stating what each strategy requires geometrically would let S03
  derive the blocked directions instead of asserting them.
- **K-2 load-path templates per function class.** The principle library states
  what each family *does*, not what it *needs reacted*. `Candidate.obligations_created`
  currently asks the model to re-derive that every time.

Both are indexed by function class, not product — the existing library's rule.
Neither is required to fix D-α.

---

## 8. Validator defects and blind spots

| finding | classification |
|---|---|
| `blocking_relation` / s03b completeness, 262 relations | **false positive** — content present under other names (§3) |
| `region_occupancy` on ACCESS (8) and APERTURE (1) | **false positive by construction** — an access void or aperture is normally a hole *in* its owning body, so overlap with its own owner is expected geometry |
| `region_occupancy` on KEEP_OUT (6) | **true positive** — the promiser entering its own keep-out is a real contradiction |
| `assembly_path` (15–29/run) | **unverifiable with current representation** — a swept AABB along a full-span ray will meet almost anything; conservative and near-vacuous |
| `configuration_interference` | **partly unverifiable** — same AABB conservatism |
| `joint_geometry` (D-β) | **true positive** |
| `dof_totality` | **true positive, working** — 1.000 coverage after the split |

Two lessons repeat from Window 1: a check that fires with no true positives is
worse than no check, and a curated-name match generalises badly. §3 is the same
failure at the field-name level.

---

## 9. Model-capability limits remaining after pipeline causes are ruled out

Only one survives: **S02 `obligations_created` closure at ~91%**, already
diagnosed as an emission-order limit — a list cannot be appended to after it is
closed, and the model sustains the forward plan over ~12 items but not ~20.

Everything else attributed to model weakness this window was wrong. The evidence
in §3 shows a cheap model producing per-DOF constraint reasoning with executable
defeat tests. **"The model is weak" is not available as an explanation here.**

---

## 10. Ranked improvements

Ranked by engineering-reasoning gain ÷ pipeline complexity.

### R-1 — Show every required key as a key (root cause D-α)
Root cause: unbound field names. **Stages:** S03 (and audit every schema for
prose-described fields). **General:** it is a statement about response contracts,
not about products. **Model-independent:** a weaker model benefits more — it has
less capacity to infer intent from prose. **Benchmarks/probes:** identical effect;
this is not case-dependent. **Weaker models:** large gain. **Complexity:**
trivial. **Risk of premature constraint:** none — no engineering content changes.
**Measure:** blocking relations recognised / relations authored, currently 0/262.

### R-2 — Accept the engineering fact, not the spelling
Root cause: consumer matching only on keys. **Stages:** S03/S04 completeness.
A named-key requirement should be paired with an explicit alias set, or the
binding checked once at parse and reported as a *shape* problem rather than as
missing engineering evidence. **General:** distinguishes "not supplied" from
"supplied differently" — a distinction any pipeline needs. **Complexity:** low.
**Risk:** aliasing could mask genuine absence; mitigate by reporting the
rename explicitly rather than silently normalising.

### R-3 — Author retention relations; derive the DOF grid (M-1, §6)
Root cause: authoring unit ≠ engineering unit. **Stages:** S03. **General:** a
total function should be *computed* from a small authored set, which is what the
S03 contract already specifies. **Model-independent:** turns 78 authored cells
into ~5 authored facts — the largest reduction in reasoning load available, and
it helps weak models most. **Benchmarks/probes:** both. **Complexity:** medium.
**Risk:** a derivation rule that is wrong would silently mis-disposition; keep
the totality check as the independent verifier. **Measure:** authored facts per
case, and DOF coverage staying at 1.000.

### R-4 — Fix `region_occupancy` role semantics (§8)
An ACCESS/APERTURE region overlapping its owner is expected; KEEP_OUT is not.
**Complexity:** trivial. **Risk:** none. **Measure:** false-positive count → 0.

### R-5 — Typed symbolic spatial relations at S03 (M-3, D-β)
Root cause: placement invented then checked. **Stages:** S03 produces, S04a
consumes. **General:** relations before coordinates is ordinary mechanical
practice. **Complexity:** medium-high — a new field on `Interface`, justified only
if R-1..R-4 leave D-β standing. **Risk:** premature constraint if the relation
vocabulary is guessed rather than derived from observed need.

### R-6 — Move `defeat_specification` to the verification stage (§6)
Root cause: discovery and verification combined. **Complexity:** contract change,
so lowest priority; and the evidence shows the model *can* do it here, so this is
a cleanliness argument, not a capability one.

**Rejected:** longer prompts (R-1 is shorter, not longer); more knowledge (§7 —
knowledge is not the binding constraint); model-specific handling; anything
requiring a benchmark to justify.

---

## Smallest coherent set

**R-1 + R-2 + R-4.**

Together: one schema-shape correction, one producer/consumer binding rule, one
validator-semantics fix. No new entity, no contract change, no knowledge
addition, no prompt lengthening.

Expected effect: the ~95% of S03/S04 findings that are downstream of D-α resolve
or become genuinely diagnosable, and the CONTRACT_INCOMPLETE cascade should
collapse to whatever engineering deficiencies actually remain — which is the
first point at which the real reasoning quality of S03 and S04 becomes visible
at all.

**R-3 is the highest-value structural change**, but it should be measured only
after R-1/R-2/R-4, because the current evidence about grid-authoring cost is
confounded by a defect that made all of that reasoning appear absent.

---

# Appendix — outcome of the R-1..R-4 revision

The diagnosis above was acted on as one integrated revision. Measured result:

| measure | before | after |
|---|---|---|
| full chain SUCCESS (s03→s03b→s04a→s04b) | **0 / 6** | **4 / 6** |
| total findings | 313 | 240 |
| DOF grid cells authored by the LLM | 48–126 per case | **0** |
| blocking relations authored by the LLM | 0 recognised of 262 emitted | **31 recognised of 31** |
| DOF entries derived by the pipeline | 0 | **420** |
| bookkeeping ratio (derived ÷ authored) | — | **13.5×** |
| s03b prompt | 3294 chars | **2684 chars** |
| field renames needed | n/a | **0** |

**H5 confirmed in the strongest way available.** Once the contract's key names were
shown as keys, the alias map bound **nothing** — the model used the canonical
names immediately. The 262 "missing" relations were never a reasoning problem and
never a compliance problem; they were an unbound schema. R-2's alias map remains
as a safety net that records any rename rather than silently normalising it, and
in this run it had no work to do.

**R-3 confirmed.** 31 engineering facts now generate 420 exhaustive entries, each
citing the relation or joint that produced it. Nothing was compressed: the total
function is still total, still checked by `dof_totality_check` against a domain
computed independently, and every entry carries its reason.

**New finding, not fixed** (one revision per cycle): `UnresolvedDecision.blocks`
references `BLK-` relation ids, and a blocking relation has no entity to be — it
lives inside `MobilityExpectation.dispositions`. This is the first evidence in
Window 2 that the current representation **cannot express a fact the reasoning
needs**: a relation the design must be able to point at. That is the bar rule 8
sets for reopening the schema, and it should be the next cycle's single change.
