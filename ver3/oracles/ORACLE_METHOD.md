# ORACLE_METHOD — how Ver3 Oracle Packs are derived, written, and locked

**Status:** authoritative. Written before any Oracle Pack content and before any
pipeline code.
**Scope:** governs every pack under `ver3/oracles/`.

---

## 1. What an Oracle Pack is, and is not

An Oracle Pack is a **semantic acceptance specification for one design problem**.

It **is not**:

- one exact expected JSON file;
- one prescribed mechanical solution;
- a golden output to diff against;
- a restatement of what Ver1 or Ver2 happened to produce.

A pack answers: *given this problem, what must be true of any acceptable
design, what may legitimately differ, what must remain open, and what would
count as evidence?*

Two designs that differ in mechanism family, part count, geometry and layout may
**both** satisfy the same pack. A design that reproduces a legacy output exactly
may **fail** it.

---

## 2. The seven-part content contract

Every pack contains exactly these parts. A part may be empty only with a written
reason; it may never be silently absent.

| Part | File | Question it answers |
|---|---|---|
| 1. Normative invariants | `normative.yaml` | What must every acceptable design satisfy? |
| 2. Allowed freedoms | `freedoms.yaml` | What may differ between two valid designs? |
| 3. Required unresolved values | `normative.yaml` → `required_unresolved` | What must stay open until evidence exists? |
| 4. Reference realizations | `reference_realizations/*.md` | What concrete example is known to satisfy part of the problem? |
| 5. Negative cases | `negative_cases.yaml` | What known-wrong design must be rejected, and for which reason? |
| 6. Evidence scope | `evidence_scope.yaml` | What was actually verified, by what model, and what was not? |
| 7. Stage projections | `stage_expectations.yaml` | After each stage: what must exist, what must not yet be decided, what may stay unresolved, what provenance must survive? |

Plus `source_map.md` (part 8) — the exact legacy files behind every statement —
and `README.md` (intent, freedoms, ambiguities, stressed capabilities,
overfitting definition).

---

## 3. Source precedence

Applied in strict order. A lower rank never overrides a higher one.

| Rank | Source class | Ver3 treatment |
|---|---|---|
| 1 | Explicit product intent and benchmark requirements | **Normative.** May become `normative.yaml` directly. |
| 2 | Explicit engineering review findings | **Normative** for the defect they identify. Primary source of negative cases. |
| 3 | Physically meaningful verified evidence **with a declared scope** | Normative **only inside the declared scope**; the scope is copied into `evidence_scope.yaml` verbatim. |
| 4 | Successful reference geometry or simulation within that scope | **Reference realization only.** Never normative. |
| 5 | Legacy golden outputs | **Historical example only.** Never normative, never a diff target. |
| 6 | Legacy implementation behaviour | **Never defines correctness.** May only supply *negative* evidence, and only when an independent rank 1–3 source says the behaviour was wrong. |

### 3.1 The rank-6 rule, stated sharply

*That Ver1 or Ver2 did X is not evidence that X is correct.*

A statement may enter `normative.yaml` on the strength of legacy code behaviour
**never**. If the only support for a statement is "the old pipeline did this",
the statement belongs in `freedoms.yaml` (as one permitted option) or in
`negative_cases.yaml` (if a review says it was wrong), or it is dropped.

### 3.2 The Ver1 catalogue rule — no card, template or validator may seed an Oracle

Ver1's mechanism cards (`ASSY_Ver1.0/knowledge/cards/*.py`), host templates
(`knowledge/templates/host_templates.py`) and validators
(`ontology/validators.py`, `V-01…V-17`) are **rank 6** and additionally carry a
specific hazard: a card is not a fact about a mechanism, it is a *pre-solved
sub-design* bundling geometry, parameter bounds and host-anchor expectations.

Therefore:

1. **No normative statement may name a Ver1 card, template or validator code**,
   or reproduce its parameter bounds, carve semantics or anchor set.
2. A card may be cited **only** in `reference_realizations/` — as one worked
   example — and only with its bundled assumptions written out, so a reader can
   see what was decided for it rather than by it.
3. **The existence of a card never makes something normative, and its absence
   never makes anything infeasible.** Ver1 returned `INFEASIBLE` for a screw
   jack while `knowledge/cards/lead_screw.py` sat in the repository
   (`tasks/benchmark/benchmark.py:159-162`). Absence of knowledge maps to
   `UNSUPPORTED`, never to `INFEASIBLE` — architecture invariant `INV-011`.
4. **No pack may require a specific mechanism family.** If removing a mechanism
   name from a normative statement makes it unsatisfiable, the statement was a
   reference realization wearing an invariant's clothes.

This rule exists because the cheapest way to rebuild Ver1 is to transcribe its
library into Oracle "requirements" and then congratulate the pipeline for
retrieving it.

### 3.3 The Ver2 stage-summary rule — golden stage outputs do not define stages

Ver2's per-stage documents — `BM-001_GOLDEN_STAGE_OUTPUTS.md`,
`BM-002_GOLDEN_STAGE_OUTPUTS.md`, and the `out/<BM>/run-*/` artifacts — are
**rank 5** historical examples. They are especially hazardous for
`stage_expectations.yaml`, because they are shaped exactly like the thing that
file must contain.

Therefore:

1. `stage_expectations.yaml` is derived **from the Ver3 stage contracts and from
   what the downstream consumer requires**, never from what a Ver2 stage
   happened to emit.
2. A `must_exist` entry may not be justified by "Ver2 Stage NN produced this
   field". It must be justified by a downstream consumer that would otherwise be
   unable to proceed, or by a rank 1–3 requirement.
3. Ver2 artifacts **may** be cited to populate `negative_cases.yaml` — but only
   where a rank 1–3 source (typically a `research_log/RL-*.md` finding)
   identifies the behaviour as defective. Example: `RL-0013` establishes that
   ranking on element count rewards incompleteness, so the corresponding
   negative case is admissible; the ranking code alone would not be.
4. **Entity vocabulary is not inherited.** `SpatialZone`, `AxisStation`,
   `RadialPosition`, ordinal `span`, and `ConceptVisualization` are retired
   (see `ver3/phase0/VER2_RETIREMENT_MATRIX.md`). No Oracle statement may
   require, mention as required, or presuppose them.

---

## 4. Deriving normative statements — the four tests

Before a statement enters `normative.yaml` it must pass all four:

**T1 — Solution-neutrality.** Could two mechanically different designs both
satisfy it? If only one mechanism family can, it is a *reference realization*,
not an invariant.

> ✗ "The closure uses a pin hinge."
> ✓ "The closure reaches both the closed and open states through a continuous
> motion, and the moving side is supported against the fixed side throughout."

**T2 — Obligation form.** Is it expressible as
*Obligation → Realization → Verification predicate → Evidence*?
A statement with no possible verification predicate is intent, not an invariant;
it belongs in `README.md`.

**T3 — Source rank.** Is it backed by a rank 1–3 source, cited by exact path and
line/key in `source_map.md`?

**T4 — Non-inversion.** Is it more than the negation of one legacy design? A
normative statement written by inverting a single observed failure encodes that
failure's shape and overfits. See §6.

---

## 5. Freedoms are first-class

`freedoms.yaml` is not a leftovers list. Every freedom is an explicit assertion
that **the Oracle refuses to constrain this**, with the reason.

A decision belongs in `freedoms.yaml` when:

- no rank 1–3 source constrains it; **and**
- constraining it would make the pack reject a design that is mechanically sound.

Typical freedoms across these packs: mechanism family, hinge or drive side, part
count, material and process, exact dimensions, internal layout, enclosure cross
-section, fastening strategy, number of guides.

**Consequence for tests:** a test may not assert any value that `freedoms.yaml`
declares free. This is checked mechanically (§9, check C-6).

---

## 6. Negative cases — derivation and the anti-inversion rule

A negative case states: *this design is wrong, for this reason, detectable at
this stage, by this predicate.*

Each entry carries:

| Field | Purpose |
|---|---|
| `id` | Stable `NEG-<case>-<nnn>` |
| `failure_class` | Which forbidden pattern it instantiates |
| `description` | The wrong design, stated positively |
| `why_wrong` | The physical or logical reason — never "because the Oracle says so" |
| `detect_stage` | Earliest stage that can detect it |
| `detect_predicate` | The deterministic check that must fire |
| `must_not_be_reported_as` | The status it must **not** receive (e.g. `PASS`, `INFEASIBLE`) |
| `source` | Rank 1–3 evidence that this is genuinely wrong |

### 6.1 The anti-inversion rule

> A negative case must not be the bare logical inverse of one reference
> realization.

If `normative` says *"the open state must clear the aperture"* and the only
negative case is *"the open state does not clear the aperture"*, the pack has
added nothing: it has restated the invariant. A useful negative case describes a
design that **looks acceptable to a naive checker** and is still wrong —
typically because a *label*, *field*, *relationship* or *simulation artefact* is
present while the *physical realization* is absent.

That is precisely the failure family Ver1/Ver2 exhibited, so it is the family
the negative cases must target:

- a stop that exists in the physics model but not in the design;
- a `revolute` label with no fixed-side and moving-side realization;
- a coupling relationship with no localized engagement;
- a guide that permits translation but realizes no anti-rotation;
- a V-A declared-pair result reported as contact-physics evidence;
- a metric that vanishes instead of becoming `NOT_MEASURED`;
- a requirement passing because an unrelated metric shares its unit.

---

## 7. Evidence scope — the declared-scope discipline

`evidence_scope.yaml` records, per evidence item:

```yaml
- id: EV-<case>-<nnn>
  claim:            # what it is offered as evidence for
  model:            # e.g. MuJoCo rigid-body, declared kinematic pairs
  fidelity:         # V-A (declared pairs) | V-B (contact) | analytic | geometric
  reused_from:      # if not executed for this case, the case it came from
  observables:      # measured quantity, threshold, unit
  in_scope:         # what this genuinely supports
  out_of_scope:     # what it does NOT support, stated explicitly
  structural_artifacts: # values that are trivially satisfied by the model form
```

**`structural_artifacts` is mandatory and is the field Ver1/Ver2 lacked.**
Example, taken from the C4-drawer trace: under a V-A declared-pair model the
measured `offaxis_max_deg` is `0.0` **by construction of the coupling**, not
because guidance was demonstrated. Recording it as evidence of straight tracking
is a category error. The field forces that admission into the pack.

Rules:

1. `fidelity: V-A` may never be cited for a claim requiring contact behaviour.
2. `reused_from` non-empty means the evidence was **not** executed for this
   case; any claim built on it inherits the source case's assumptions.
3. Anything not in `observables` is `NOT_MEASURED`, never absent.

---

## 8. Stage projections

`stage_expectations.yaml` gives, for each of Stages 01–12, four lists:

| Key | Meaning | Violation is |
|---|---|---|
| `must_exist` | Entities/decisions that must be present after this stage | missing obligation |
| `must_not_be_decided` | Decisions this stage is forbidden to make | ownership violation |
| `may_remain_unresolved` | Legitimately open items | — |
| `provenance_required` | Links that must survive into the next stage | trace break |

These are written **against the stage contracts**, not against any
implementation, and they are what Phase 6 vertical slices are graded on.

---

## 9. Internal validation before lock

`ver3/oracles/` is checked mechanically before `LOCK.json` is written. Every
check is deterministic and reruns in CI.

| ID | Check | Fails when |
|---|---|---|
| C-1 | ID uniqueness | Two entities share an ID within a pack |
| C-2 | Reference resolution | An ID referenced in any file is undefined |
| C-3 | Source-map completeness | A normative/negative statement cites no source, or cites a path that does not exist |
| C-4 | Source-rank legality | A normative statement's only support is rank 5–6 |
| C-5 | Prescription check (T1) | A normative statement names a specific mechanism, part count, material or dimension not fixed by the user |
| C-6 | Freedom/normative disjointness | A decision appears in both `normative.yaml` and `freedoms.yaml` |
| C-7 | Anti-inversion (§6.1) | A negative case is the bare negation of a normative statement with no additional failure mechanism |
| C-8 | Evidence-scope completeness | An evidence item lacks `fidelity`, `in_scope`, `out_of_scope`, or `structural_artifacts` |
| C-9 | Fidelity legality | A V-A evidence item is cited for a contact-dependent claim |
| C-10 | Stage-projection coverage | A stage lacks all four keys, or `must_not_be_decided` is empty for a stage that owns nothing |
| C-11 | Contradiction scan | Two statements in the same pack, or a pack and its parent case, assert incompatible things |
| C-12 | Excluded-case scan | Any file references `BM-101` or `Geneva` |
| C-13 | Ver1 catalogue leakage (§3.2) | A normative statement names a Ver1 card/template/validator code, reproduces its bounds, or requires a specific mechanism family |
| C-14 | Ver2 vocabulary leakage (§3.3) | Any file requires or presupposes `SpatialZone`, `AxisStation`, `RadialPosition`, ordinal `span`/slot, or `ConceptVisualization`; or a `must_exist` entry whose only justification is a Ver2 golden stage output |
| C-15 | Micro-oracle scope (§13) | A micro-oracle asserts a product-level invariant, or a product pack delegates a product-level obligation to a micro-oracle |

C-11 operates **across** packs for the BM-001 family: BM-001-2 and BM-001-3 are
documented single-requirement deltas of BM-001, so any statement they inherit
must not conflict with the parent pack.

---

## 10. Locking and change control

1. All checks in §9 pass.
2. `LOCK.json` records, per file: relative path, SHA-256, byte length, and the
   pack it belongs to.
3. A test recomputes every hash. **Any drift fails the suite.**
4. After lock, **pipeline implementation may not edit any file under
   `ver3/oracles/`.**

### 10.1 Changing a locked Oracle

Requires `ORACLE_CHANGE_PROPOSAL.md` containing: old statement; proposed
statement; the **new evidence** (with source rank); why the old statement is
defective — not merely inconvenient; impact on every other pack; and an explicit
benchmark-overfitting risk assessment.

A proposal is **never applied automatically**, and never as part of a commit
that also changes implementation code.

> An Oracle is not weakened to make a test pass. If implementation cannot meet a
> locked Oracle, the correct outcomes are `UNSUPPORTED` or a documented
> capability gap — not a softer Oracle.

---

## 11. Overfitting — the standing definition

A pack is overfitted if it would reject a mechanically sound design that a
competent engineer would accept for the stated problem.

Concretely, a pack overfits when it asserts any of:

- a specific mechanism family (pin hinge, rack and pinion, lead screw…);
- a specific part count or body count;
- a specific coordinate, dimension or tolerance not stated by the user;
- a specific side, face, or handedness not stated by the user;
- a specific material or process not stated by the user;
- an exact serialized output.

Each pack's `README.md` closes with a **"what would constitute overfitting
here"** section naming the concrete temptations for that case — for the BM-001
family, most importantly: *assuming a rectangular prismatic enclosure*, and
*assuming the latch is a snap-fit*.

---

## 12. Excluded material

`BM-101` and Geneva mechanisms are excluded from architecture, implementation,
tests and Oracle authoring by instruction. They were located during Phase 0 and
deliberately not read for design content. Check C-12 enforces their absence.

---

## 13. Two tiers: product cases and micro-oracles

```
oracles/
  product_cases/   BM-001  BM-001-2  BM-001-3  BM-002  C4-drawer
  micro_oracles/   guided-slider  rotary-to-linear-engagement
                   latch-retention  hinge-and-stop
```

### 13.1 What distinguishes them

A **product case** starts from a user-level request and must traverse the whole
chain — requirement, obligation, product topology, spatial realization,
embodiment, parameters, CAD, verification, evaluation. Its Oracle constrains the
*product*.

A **micro-oracle** constrains **one reusable mechanical capability** in
isolation: guided translation; rotation-to-translation conversion; retention and
release; hinged closure with a travel limit. It exists to give a capability its
own negative cases and its own evidence-scope discipline, independent of any
product.

### 13.2 The rule that keeps micro-oracles from becoming a card library

This is the load-bearing constraint of the two-tier split.

1. **A micro-oracle is not a solution.** It states obligations and predicates for
   a capability — *"a guided translation must realize anti-rotation"*,
   *"a rotation-to-translation realization must localize engagement and react
   both radial and axial load"*. It does **not** name a mechanism, supply
   geometry, or supply parameter bounds. If it did, it would be a Ver1 card with
   a YAML extension.
2. **Micro-oracles are never a source of design.** They are acceptance criteria
   applied to whatever the pipeline produced. See §13.3 for the exact access
   boundary.
3. **The name states a capability, never a mechanism.** The capability is
   `rotary-to-linear-engagement`, not "rack and pinion". Rack-and-pinion is one
   *reference realization* of it, cited as evidence; so are lead screw, cam,
   crank-slider, capstan and worm. A micro-oracle named after a mechanism is a
   card with a YAML extension — which is why this one was renamed.
4. **A product case never delegates.** A product pack states its own obligations
   in full. A micro-oracle may be *referenced* to reuse a predicate definition,
   but a product obligation is never discharged by "see micro-oracle" — check
   C-15.
5. **Micro-oracles carry no product-level invariants.** No enclosure, no access
   path, no assembly sequence, no user-facing requirement.
6. **They are derived from legacy fixtures as evidence, not as targets.**
   `latched_drawer` and `rack_pinion_fixture` are Ver1 *fixtures*: small,
   pre-solved, and shaped by the card that realized them. They are cited in
   `source_map.md` as rank 4–5 reference realizations and as sources of negative
   cases. They are **not** peer product goldens, because passing them would
   measure the same thing Ver1 measured — whether the library reproduces its own
   fixtures.

### 13.3 Oracle access boundary — who may read `oracles/`

The rule is about *influence on design generation*, not about file permissions.

**MUST NOT read any Oracle file — production synthesis, Stages S01–S12:**
requirement formalization, functional/physical architecture, product and
packaging architecture, spatial and kinematic synthesis, embodiment, the
parametric solver, CAD compilation, verification planning, verification
execution, evidence extraction, requirement evaluation, revision routing — and
any library they call, including a future `KnowledgeProvider`.

An Oracle states what a correct answer looks like. A stage that reads one is
being graded on a test whose answers it has seen, and the pipeline's apparent
capability becomes unmeasurable.

**MAY read Oracle files — evaluation and audit tooling, outside the synthesis
path:**

| Consumer | Purpose |
|---|---|
| Oracle validation suite | Checks C-1…C-15 over the packs themselves |
| Lock verifier | Recomputes `LOCK.json` hashes |
| Stage-projection evaluator | Grades a produced DesignState against `stage_expectations.yaml` |
| Negative-case runner | Confirms each `NEG-*` fails for its declared reason |
| Freedom-assertion scanner (`INV-014`) | Cross-references test literals against `freedoms.yaml` |
| Reporting / traceability tools | Build human-facing coverage reports |

**The enforced boundary:**

1. No module reachable from a stage's execution path may import an Oracle
   reader or open a path under `oracles/`. Checked by import scan and by a
   runtime `open()` audit (`INV-016` machinery).
2. Evaluation tools run **after** a stage has produced its patch, and receive
   the patch as input. They never return a value into DesignState.
3. Oracle content may never enter candidate generation, candidate ranking, or a
   `SelectionDecision` — directly or through a cached artifact.
4. The pipeline must produce byte-identical authoritative artifacts with
   `oracles/` renamed or absent. This is the operational test of the whole rule,
   and it is run as part of `INV-016`'s absence-run.

---

### 13.4 Why the reclassification matters

Promoting `latched-drawer` and `rack-pinion-fixture` to product-level Oracles
would have quietly reintroduced Ver1's evaluation model: a suite of
mechanism-shaped tasks, each satisfied by the mechanism it was built from, with
suite pass-rate reported as synthesis capability. Demoting them to
capability-scoped acceptance criteria keeps their genuine value — they contain
real contact-physics and engagement evidence — while ensuring that the only
things graded end-to-end are five *product* requests whose solutions are not
supplied.

The capability each supports, and the product case that must exercise it
end-to-end:

| Micro-oracle | Capability | Legacy evidence (rank 4–5) | Product case that must realize it |
|---|---|---|---|
| `guided-slider` | Guided translation, anti-rotation, travel limits, assembly access | `V1 tasks/latched_drawer.json`, `m10_slide_rail/`, `m22_composition/`, `m25_contact_layer/` | C4-drawer, BM-002 |
| `rotary-to-linear-engagement` | Rotation→translation, localized engagement, ratio, radial+axial reaction, V-A vs V-B fidelity | `V1 tasks/rack_pinion_fixture.json`, `m7_rack_pinion/`, `m11_rack_pinion/REVIEW.md`, `m13_hard_anchor/out/t2_hard_verdict.json` | C4-drawer, BM-002 |
| `latch-retention` | Retention, hand release, overload, repeated cycling | `V1 tasks/snap_panel.json`, `m6_ms_closeout/`, `m23_latch_physics/` | BM-001, BM-001-2, BM-001-3 |
| `hinge-and-stop` | Hinged closure, aperture clearance, real vs absent travel stop | `V1 m0/` (`stop/` and `nostop/` variants), `tasks/m0_hinge_box_{stop,nostop}.json` | BM-001, BM-001-2, BM-001-3 |

The `m0/out/stop` vs `m0/out/nostop` pair is particularly valuable: it is a
matched pair differing only in whether a real stop exists, which is exactly the
"stop exists only in the physics model" negative class.

---

## 14. Relationship to the root ASSY_NEW knowledge project

`/home/ftk3187/github/ASSY_Ver3.0` (repository root, remote
`seul22lee/ASSY_NEW.git`) is the local ASSY_NEW reference source. Per Part II it
is **read-only reference material**:

- no Oracle statement derives from it;
- it is not cited in any `source_map.md` as evidence;
- it is not a source rank in §3;
- the Ver3 subtree must run with the root ontology/data/rules directories
  renamed or absent.

Its only future role is as a candidate `KnowledgeProvider`, documented in
`ver3/docs/REFERENCE_KNOWLEDGE_NOTE.md`.
