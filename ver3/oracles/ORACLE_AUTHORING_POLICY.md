# ORACLE_AUTHORING_POLICY

Operational rules for authoring every pack. Derived from the BM-001-family
classification report, which established the defects are systematic.

---

## 1. Normative content — admissible bases only

The admissible set depends on the tier, because **a micro-oracle has no user**.

### Product cases

| basis_type | Means | Requires |
|---|---|---|
| `DIRECT_USER_REQUIREMENT` | Restates a rank-1 source requirement | `support_type: direct`; a rank-1 source locator; the statement must not exceed the source |
| `NECESSARY_PHYSICAL_CONSEQUENCE` | Physically unavoidable given a rank-1 requirement | `support_type: derived`; `derivation_premises`; must survive counterexample search |
| `VERIFICATION_MINIMUM` | The least condition that makes a claimed verification meaningful | `enables_claim` **and** `requires_evidence_tags` |

### Micro-oracles

| basis_type | Means | Requires |
|---|---|---|
| `PROJECT_DEFINED_CAPABILITY` | Restates a fragment of the project-authored, then frozen, capability statement | `support_type: direct`; a locator resolving to **S1** of the capability's dossier |
| `NECESSARY_PHYSICAL_CONSEQUENCE` | as above | as above |
| `VERIFICATION_MINIMUM` | as above | as above |

**A micro-oracle must never use `DIRECT_USER_REQUIREMENT`** (finding SF-1.3). Its
capability statement was written by this project and then frozen; appearing in
dossier S1 does not make it user language and does not make it rank 1. It may
ground normative statements, but its authority is explicitly human-reviewable and
it must never be presented as a user requirement. A product case must
symmetrically never use `PROJECT_DEFINED_CAPABILITY`: it has a user. Both
directions are BLOCKING.

### Every VERIFICATION_MINIMUM must name what it enables

`enables_claim` states exactly which claim becomes admissible once the minimum is
satisfied. Placeholder text does not satisfy it. A verification minimum without
`enables_claim` or without `requires_evidence_tags` is `POLICY_FIELD_MISSING`,
BLOCKING.

## 2. Product normative content must NOT contain

- pipeline representation requirements ("expressed as", "declared … path", "recorded as a graph") — these belong in `stage_expectations`;
- architecture invariants already owned by `ARCHITECTURE_INVARIANTS.yaml` (units, provenance, duplicate entities, renderer/CAD authority);
- current tooling limitations;
- reference-realization details — mechanism names, part counts, dimensions, coordinates, bounds;
- unsupported interpretations — anything whose only support is rank 5–6;
- fixed expected outcomes caused by a capability gap.

## 3. Stage expectations

May state what the pipeline must **represent, preserve, defer or report**. May
not add a product requirement. If a statement would still be true of a product
built by hand with no pipeline, it is a product requirement and belongs in
`normative.yaml` — otherwise it belongs here.

## 4. Evidence scope

Records what current evidence **can** and **cannot** prove: `fidelity`,
`reused_from`, `in_scope`, `out_of_scope`, `structural_artifacts`. A value that
is exact by construction of the model is a structural artifact and is never
evidence.

## 5. Source ambiguities

Preserved explicitly in `_ambiguities/`. Never silently reconciled. They do not
stop authoring of other packs. They become lock blockers **only** when they
prevent a fair acceptance predicate for that specific pack.

## 6. Reference realizations

Never a normative target. Cited only in `reference_realizations/`, always with
their bundled decisions written out so a reader sees what was chosen *for* the
example rather than *by* the requirements.

## 7. Stage-11 outcomes are conditional

Expressed as `outcome_rules`, never fixed results:

```yaml
REQ-00X:
  pass_requires: "<the scoped evidence that would earn PASS>"
  fail_when: "<contradictory evidence>"
  if_capability_absent: UNSUPPORTED
  otherwise: NOT_VERIFIED
```

Never freeze today's inability into a permanent expected result.

## 8. Parent / delta packs

- inherit the parent unchanged (`inherits:`);
- add or narrow only what a rank-1 delta source supports;
- **never** compare a generated child design to a generated parent design;
- evaluate the delta requirement **directly** on the child design alone.

## 9. Fixtures — mandatory, machine-checked, and DOMAIN-SEPARATED

Physical design and verification process are separate domains and never share a
tag set (finding SF-1.1). A physical realization must not become inadmissible
merely because no test has yet been authored for it.

| File | Domain | Declares |
|---|---|---|
| `realizations.yaml` | physical design | `physical_tag_vocabulary`, `admissible_realizations`, `inadmissible_realizations` |
| `evidence_cases.yaml` | evidence and verification | `evidence_tag_vocabulary`, `admissible_evidence_cases`, `inadmissible_evidence_cases` |
| `negative_cases.yaml` | pipeline and process | design, evidence and process cases that must be rejected |

Rules:

- a non-`VERIFICATION_MINIMUM` invariant uses `requires_tags`, drawn only from
  the physical vocabulary;
- a `VERIFICATION_MINIMUM` uses `requires_evidence_tags`, drawn only from the
  evidence vocabulary;
- crossing the two is `DESIGN_EVIDENCE_TAG_MIXED`, BLOCKING;
- `admissible_realizations`: **>= 2 materially different** designs. Every
  physical invariant must admit **all** of them;
- `inadmissible_realizations`: each must be rejected by at least one physical
  invariant;
- the same two rules apply to evidence cases against the verification minima.

A pack that rejects an admissible realization is overfitted; one that admits an
inadmissible realization is too weak. Both are BLOCKING.

## 10. Unresolved decisions carry explicit block scopes

The coarse `blocks:` relation is retired (finding SF-1.4). Every unresolved
decision declares a `kind` and a set of `block_scopes`:

| kind | quantitative \| qualitative \| interpretive \| structural_choice |
|---|---|
| `blocks_structural_predicate` | the predicate's DOMAIN is undefined, not merely a threshold missing |
| `blocks_quantitative_acceptance` | a numeric acceptance cannot be evaluated |
| `blocks_PASS` | PASS may not be reported |
| `blocks_evidence_interpretation` | evidence cannot be interpreted against the requirement |

**A `quantitative` unknown may never carry `blocks_structural_predicate`.** A
missing effort ceiling does not block geometric actuator reachability; a missing
disturbance magnitude does not block the existence of a load path; a missing
stability criterion does not block derivation of a resting configuration. Any
use of `blocks_structural_predicate` requires a
`structural_block_justification` explaining why the domain, not the threshold,
is undefined.

## 11. Two review records, neither of which is Oracle evidence

- `SOURCE_ENTAILMENT_REVIEW.yaml` — for every normative statement: the
  source-derived proposition, the entailment class, the counterexample tried and
  its outcome. Locator resolution is not semantic entailment, and no statement
  may be called audited because its locator resolves (finding SF-1.5).
- `FIXTURE_PLAUSIBILITY_REVIEW.yaml` — for every admissible fixture: how it
  physically operates, what it assumes, what would break it, and a status
  (finding SF-1.6). Tags are authored by the same hand as the invariants and are
  not independent evidence, so the review may never be represented by copying
  them.

## 12. Open search, not fixed plurality

No pack may require a fixed number of candidates to survive a stage (finding
SF-8.3). One candidate may legitimately remain after source- and physics-based
elimination. What must hold instead:

- the solution space was not closed merely by current library availability;
- each rejected candidate carries a source, physical or feasibility reason;
- synthesis beyond the provider catalogue remained possible;
- an absent implemented realizer yields **UNSUPPORTED**, never INFEASIBLE.

---

## 12.5 Three domains: physical, representation, evidence

Adopted at PCF-004. The earlier passes had only two domains — physical and
evidence — and quietly used the physical one for a third kind of statement.

| Domain | Asks | Failure means |
|---|---|---|
| **PHYSICAL** | could this artifact exist and work? | the design is wrong |
| **REPRESENTATION / EVALUABILITY** | does the DesignState say enough to evaluate it? | the RECORD is incomplete |
| **EVIDENCE** | does something support the claim? | the CLAIM is unsupported |

**Physical properties** — no undeclared volumetric overlap; intended interaction
physically consistent; an installation process physically realizable; the
required motion physically realizable.

**Representation / evaluability properties** — interaction regions declared and
classified; numerical tolerance recorded; compliant region identified;
deformation assumptions represented; insertion direction recorded; process and
material assumptions recorded; evidence fidelity declared.

**Evidence properties** — geometry/contact evidence supports a claim;
control/ablation supports a claim; quantitative force or capacity evidence exists.

### 12.5.1 A physically valid design may be NOT_EVALUABLE

A design can be perfectly buildable while its DesignState is incomplete. That is
a **representation** failure, and reporting it as physical inadmissibility is a
category error — it tells the designer their product is wrong when the record is
wrong.

The correct outcome is:

```yaml
physical_predicate: NOT_EVALUABLE
reason: REPRESENTATION_INCOMPLETE
```

Never `FAIL`, and never a missing physical tag.

`interaction_regions_declared` was carried as a **physical** tag in the previous
pass. It is a representation property and is now owned by
`stage_expectations.evaluability_prerequisites`. It is not deprecated in place —
it is **removed from every physical contract**.

## 13. Intended interaction semantics — contact is not interference

Adopted at GATE 2. This definition is common to every pack and every stage
expectation, and the auditor enforces its schema.

### 13.1 The six regions

| Region | Meaning | Admissible? |
|---|---|---|
| `declared_contact` | two bodies are intended to touch here — a guide face, a pin/bore, a stop face, a seat | **yes**, and zero clearance here is correct |
| `declared_clearance` | two bodies are intended not to touch, with a stated gap | yes; violating the gap is a defect |
| `declared_interference_fit` | material overlap intended and taken up by elastic strain — a press fit | yes **only** with explicit process and material assumptions |
| `declared_compliant_interaction` | overlap taken up by a represented deformation — a snap beam flexing past a lip | yes **only** where the deformation is represented |
| `undeclared_volumetric_overlap` | solids occupy the same space and nothing declares it | **no — always FAIL** |
| `numerical_tolerance` | the penetration depth below which a contact solver reports contact rather than overlap | a declared property of the evaluation, never of the design |

### 13.2 The rule

> **No undeclared volumetric overlap is permitted.**

The rule is **not** "every pair of parts must maintain positive clearance
everywhere". That formulation makes every guide, pin, dovetail, snap, flexure and
stop into a collision, which is precisely backwards: those features exist in order
to touch.

- declared contact is admissible;
- zero clearance at a declared contact is admissible;
- a declared interference fit is admissible when its process and material
  assumptions are explicit;
- a declared compliant interaction is admissible when the deformation is
  represented;
- undeclared penetration remains FAIL, at any depth beyond the declared numerical
  tolerance.

### 13.2.1 Physical tag vocabulary for interaction

Exactly three physical tags carry interaction meaning. Any other interaction
concept is representation or evidence, not physical truth.

| Physical tag | Means |
|---|---|
| `no_undeclared_volumetric_overlap` | no two solids occupy the same space outside a declared contact, interference-fit or compliant-interaction region, under the declared tolerance |
| `intended_interaction_physically_consistent` | each intended interaction is physically coherent: a compliant region can actually deflect, an interference fit is takeable up in strain, a contact face exists on both bodies |
| `installation_process_physically_realizable` | see §14 |

The corresponding **representation** expectations live in stage expectations:

`interaction_regions_declared`, `interaction_kind_recorded`,
`numerical_tolerance_recorded`, `compliant_region_recorded`,
`assembly_assumptions_recorded`.

### 13.3 Predicate form

A motion or pose predicate must be written in the form:

```
no volumetric overlap between <bodies> outside declared contact, declared
interference-fit and declared compliant-interaction regions, under the declared
tolerance and at the declared fidelity
```

and **not** as `clearance(...) > 0` against a whole enclosing solid, nor as
`intersect(a, b) is empty` everywhere. Both retired forms are detected as
`BLANKET_CLEARANCE_PREDICATE`.

## 14. Assembly semantics — insertion is a process, not a collision test

Adopted at GATE 2.

The requirement is **not** "a fully collision-free installation path exists".
A press fit has no collision-free path and is still assemblable.

An assembly predicate must require:

- a **realizable installation process** exists;
- no part passes through **undeclared rigid** material;
- intended contact during insertion is allowed;
- press fit, snap fit, interference fit and compliant insertion are allowed **only
  when explicitly declared**, with their required deformation, material
  assumptions, insertion direction and process assumptions represented;
- co-formed, bonded or permanently joined regions declare that relationship
  instead of owing a path.

Four questions are kept apart and never conflated:

| Question | Where it lives |
|---|---|
| geometric insertion feasibility | the physical invariant |
| compliant assembly feasibility | the physical invariant, conditional on a declared compliant region |
| force / process adequacy | `required_unresolved` — a quantitative question |
| what evidence earns an assembly PASS | `stage_expectations` s11 |

## 14.1 The retired assembly contract

`assembly_paths_exist` — *"each discretely-installed part has a collision-free
installation path"* — is **retired**, not deprecated. It excluded every press fit
and every snap fit from being assemblable.

It must not appear in any active `requires_tags`, physical tag vocabulary, fixture
tag list, negative-case rejection, stage PASS condition, or auditor-required tag
set. It survives only in an explicit `retired_contracts` block that contributes
nothing to evaluation. `DEPRECATED_TAG_ACTIVE` is BLOCKING.

The active physical contract is `installation_process_physically_realizable`.

## 15. Causal verification minima — a control is not the only proof

Adopted at GATE 2, approved as HSD-006.

Where a verification minimum asks whether a feature is real, it must accept
**either**:

- **A. direct causal evidence** — the feature's geometry exists, contact occurs at
  the relevant configuration, and the observed behaviour is caused by that
  contact; or
- **B. discriminating evidence** — a control, ablation or sensitivity result
  showing the criterion fails when the feature is removed.

A realized stop may be evidenced by explicit stop faces, contact at the terminal
configuration, and kinematic termination caused by that contact, **without**
building a second model with the stop deleted. A control remains valuable and is
still admissible; it is no longer mandatory.
