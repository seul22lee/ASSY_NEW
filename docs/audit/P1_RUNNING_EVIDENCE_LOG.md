# Package 1 — running evidence log

Appended as reading proceeds. Contradictions are RECORDED, not resolved: the
instruction is that resolution waits until Package 1 is complete.

Files complete so far: 2 of 35.

---

## Previously held conclusions contradicted by evidence

### SA-1 — `BodyHypothesis` / `PhysicalInteractionHypothesis` were intended S02 outputs

- **Previous conclusion (mine, Window 2):** S03's contract requiring these from S02
  was "a consumer dependency with no producer" (`W2-I1`), and I edited
  `S03_CONTRACT.yaml` to delete the requirement.
- **Contradicting evidence:**
  - `PIPELINE_CRITICAL_DESIGN_REVIEW.md` §B1 Stage 02 "Decisions owned" L816-817
    lists `BodyHypothesis` and `PhysicalInteractionHypothesis` **without a [NEW]
    marker**, i.e. as families S02 was *already* understood to own; only `LoadCase`
    and `EvidenceRouteDecision` are marked [NEW].
  - §B2 sufficiency matrix L1056: S02→S03 hand-over is "body hypotheses with
    roles; interaction hypotheses; obligations addressed *and created*; load cases
    …", and the *only* stated failure is "no `LoadCase`; no route classification".
  - `PIPELINE_IMPLEMENTATION_PROPOSAL.md` §3 S02 Outputs L201-203 repeats it:
    "…`LoadCase`, **provisional body hypotheses and interaction hypotheses**".
- **Earliest document establishing intent:** the critical design review (§B1/§B2).
- **Implementation decision that diverged:** Window 2 deleted the consumer
  requirement instead of implementing the producer.
- **Downstream consequences:** S03 now invents bodies from a principle family with
  no intermediate physical hypothesis. My own
  `S02_S04_REASONING_GAP_ANALYSIS.md` §5 later rediscovered this as "M-2 — no
  physical-effect chain between S02 and S03" without recognising that I had
  removed the specified chain.

### SA-2 — the `blocked_by` relation was specified as a typed RELATE, not embedded state

- **Previous conclusion (mine, Window 2 cycle 5):** `UnresolvedDecision.blocks →
  BLK-…` dangling was "the first Window 2 evidence that the representation cannot
  express a fact the reasoning needs", i.e. grounds to reopen the schema.
- **Contradicting evidence:** `PIPELINE_IMPLEMENTATION_PROPOSAL.md` §8 "Essential —
  typed relations, not families" L840: `blocked_by(group, direction, blocker,
  features, configurations, defeat_spec)` — "**RELATE**, per GAP-01's own
  recommendation". `PIPELINE_CRITICAL_DESIGN_REVIEW.md` §B1 S03 output 5 L876-879
  specifies the same six fields.
- **Implementation decision that diverged:** my s03b embeds blocking relations
  inside `MobilityExpectation.dispositions` rather than emitting a RELATE, so they
  have no addressable identity.
- **Downstream consequences:** the reported "representation hole" is an
  implementation omission. Two cases fail s03b on a dangling reference to an object
  the architecture said should exist as a relation.

### SA-3 — deterministic derivation of dispositions exceeds the intended split

- **Previous conclusion (mine, cycle 5 R-3):** deriving the DOF grid implements
  "the contract's own division of labour".
- **Contradicting evidence:** both documents say the *domain* is enumerated
  mechanically and **the LLM dispositions each entry** —
  `PIPELINE_IMPLEMENTATION_PROPOSAL.md` §3 S03 L378-379 and
  `PIPELINE_CRITICAL_DESIGN_REVIEW.md` §B1 L899-901: "None for DOF totality — the
  DOF set is enumerated mechanically from the joint graph, and **the LLM only
  dispositions each entry**."
- **Divergence:** `derive_mobility()` assigns the disposition itself, including a
  `MAINTAINED_BY_CLASS` fallback for any DOF that is not free, not blocked and not
  declared irrelevant.
- **Consequence to verify in P4:** whether that fallback converts "unknown" into a
  positive engineering assertion. Note the intended check is the *opposite*
  direction: proposal O-1 L942-948 prescribes measuring "the rate at which a
  disposition is overturned by S04·B", which presumes the LLM authored it.

### SA-4 — the intended implementation order was not followed

- **Previous conclusion (implicit):** implementing S01+S02, then S03+S04, was the plan.
- **Contradicting evidence:** `PIPELINE_CRITICAL_DESIGN_REVIEW.md` §B8 "Minimal
  implementation order" L1166-1199 requires, before any stage implementation:
  step 5 "**Write the sufficiency probes before any stage.**
  `STAGE_PROGRESSION_CONTRACT` step 6 mandates them and they do not exist. Nine
  probes, one per row of B2"; step 6 "**Hand-author S03 and S04b outputs for the
  three existing references and run the probes against them.** The references are
  the only ground truth in the repository… **Highest value per unit of effort in
  this list; needs no stage implementation.**"
- **Divergence:** neither the nine sufficiency probes nor the hand-authored
  S03/S04b reference outputs were created. Implementation began directly.
- **Consequence:** there is no ground-truth S03/S04 output in the repository
  against which a probe could be validated, which is why every Window 2 judgement
  has rested on validators authored alongside the code they check.

---

## Contradictions between authoritative documents (recorded, not resolved)

| id | subject | doc A | doc B | note |
|---|---|---|---|---|
| **CD-1** | S05/S06 loop termination | critical review §A5.3 L611: "each round **must strictly reduce** the set of unsatisfied constraints" | proposal §11 D-6 L1057-1062: "Termination is **NOT** by monotone reduction… That rule was proposed and is wrong" | proposal is revision 2 and states it supersedes; verify against `STAGE_PROGRESSION_CONTRACT` |
| **CD-2** | selection-gate position | critical review §A5.2 L580: "The `SelectionDecision` gate sits **after S04b**, unchanged" | proposal §2 L90 and §11 D-5: gate sits **between S04·A and S04·B** | both are deliberate; the S04 contract must be checked |
| **CD-3** | pose law | critical review S-9 L322-328: "S04 must emit a typed, executable `PoseLaw`" | proposal §8 "Derived — must not become families" L852: "Pose law — derivable… **Not authored**" | opposite conclusions on the same defect |
| **CD-4** | `Configuration` vs `State` | critical review §A7.4 L734-736: "the same concept… Recommend **one family** with a `kind` and a maturity field" | proposal §8 keeps both, and §3 S03 outputs list `Configuration` while S04·B owns `State` | proposal does not address the redundancy claim |
| **CD-5** | compliance representation | critical review §B1 S03 L861: **[NEW]** `CompliantRegion` family | proposal §8 "Unnecessary": "Compliance as its own family — expressed as a compliant `Joint` between `RigidGroup`s" | proposal supersedes explicitly (§11 D-2) |

---

## Open questions the architecture never closed (carry into P4)

- **Q-2** (critical review L1212-1215): "What is a DOF disposition for a compliant
  body? A rigid body has six. A compliant region does not have a finite DOF set in
  the same sense… the totality requirement has **no defined meaning for them yet**."
  My `free_dof()` silently resolves this by treating a COMPLIANT joint as
  `{T<axis>}`. That is an implementation answer to an explicitly open architectural
  question.
- **Q-4 / O-1**: can an LLM produce a reliable total DOF disposition? Prescribed
  measurement is the S04·B overturn rate; never measured.
- **Q-5**: is the scout boundary enforceable? No scout is implemented, so untested.
- **Q-7**: is nominal-only geometry permanent?

---

## "Correct and should not be touched" (critical review §B7 L1153-1158)

Recorded verbatim because it answers the final audit's §14 directly: INV-002
(source-text exclusivity); INV-001 (single ownership); INV-007's *principle* of no
selection before evidence; the patch model with `parent_state_hash`; the status
vocabulary and its forbidden collapses; the `RejectedAlternative` retention rule;
S07's no-repair rule.

---
## Update — 8 of 35 P1 files complete

### SA-1 CONFIRMED by a third, decisive source

`ver3/contracts/stages/S02_CONTRACT.yaml` L30:
`creates: [Obligation, Candidate, AcceptanceContract, LoadCase, BodyHypothesis, PhysicalInteractionHypothesis]`
and L95 `next_stage_consumer_requirement.needs: [body_hypotheses_with_roles, interaction_hypotheses, …]`.

The **S02 contract itself** — authoritative per the audit's own rule — says S02
creates both families and S03 consumes them. My S02 implementation produces
neither, and Window 2 deleted the S03 requirement rather than the producer.

### New contradictions

| id | subject | doc A | doc B |
|---|---|---|---|
| **CD-6** | S02 outputs | `S02_CONTRACT` L30 `owned_decisions.creates` includes BodyHypothesis + PhysicalInteractionHypothesis | same file L62-66 `structured_outputs` omits both — **internal contradiction inside one contract** |
| **CD-7** | BodyHypothesis home | `S02_CONTRACT` L30 requires S02 to CREATE them | `DESIGN_STATE_CONTRACT` defines **no such family anywhere** — a contract mandates creating an entity the state has no home for |
| **CD-8** | S02 ownership | `S02_CONTRACT` L30 (6 families) | `STAGE_OWNERSHIP_MATRIX` L55 s02 owns only 4 — matrix omits both hypothesis families. Under INV-001 a CREATE of an unowned family is a SCHEMA_FAILURE, so the two contracts cannot both be satisfied |
| **CD-9** | LoadCase fields | `S02_CONTRACT` L38: [entity_id, scenario, applied_to_role, direction_class, kind, magnitude_or_status] | `DESIGN_STATE_CONTRACT` L262 additionally requires **reacted_at_role**, and its rule L268-273 says without it "terminates at a reaction site is uncheckable" |

### SA-5 — the freeze rule was violated

`STAGE_PROGRESSION_CONTRACT` L149-197 defines seven inputs FSF-01..07 for a stage
freeze and states plainly: **"NO stage contract may freeze. FSF-01 is satisfied and
FSF-02 through FSF-07 are not. Satisfying one input is not partial permission."**
FSF-05 is the step-6 sufficiency probe, "the real gate; schema validity is cheap".

I declared Window 1 frozen and Window 2 frozen. No sufficiency probe exists; no
source-only run of the kind step 4 requires was performed for s03/s04 (S01/S02
were replayed from recordings). Both freezes were declared against a rule that
says no contract may freeze yet.

### SA-6 — `before_s01` build order not followed

`STAGE_PROGRESSION_CONTRACT` L242-250 requires, before s01: DesignState/StagePatch
types, the provider layer, **the assurance-package projection**, and the benchmark
harness. The projection is explicitly to be built first, because "if it is built
last it becomes a report generator, and a report generator invents structure the
stages never produced". No assurance-package projection exists; the dashboard was
built last and is exactly a report generator.
