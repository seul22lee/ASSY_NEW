# IMPL S-4 — CANONICAL PHYSICAL REASONING MIGRATION

Baseline `b75d033`. This document opens Impl S-4. It records the S-3 closure boundary,
the residual owner map, and the entry-point analysis. **Impl S-4 implementation has not
been performed** — see §9 for exactly where it stands and why.

---

## 1. S-3 Closure Boundary and Post-S-3 Residual Ownership

**CLOSED: Impl S-3** — ConsumerView / invocation / reference-context architecture, at
commit `b75d033`.

**NEXT: Impl S-4** — canonical physical reasoning migration.

### 1.1 Frozen S-3 invariants

These are the baseline. They are not to be modified to make a later step easier.

1. Consumer Sufficiency = Source A ∪ Source B + justified contributory context.
2. Source A is contract-driven.
3. Reference population is declarative through canonical field semantics.
4. Unknown reference population stays conservatively `INVOCATION_BRANCH`.
5. `DESIGN_WIDE` visibility does not itself create Candidate lineage.
6. Candidate-specific authored relations may subsequently make design-wide material
   `COMMON_UPSTREAM`.
7. Same-invocation co-produced dependencies are not required pre-stage.
8. Later `EXTEND` fields are not charged to an earlier `CREATE` responsibility.
9. Optional/many reference existence does not imply `REQUIRED_NONEMPTY`.
10. `Stage.invoke` is the canonical boundary: build → record → enforce → invoke.
11. Known-insufficient context cannot reach `provider.generate`.
12. The exact ConsumerView is recorded for ready and blocked attempts.
13. Reference structure and referent existence are validated independently.
14. `resolvable` follows canonical meaning.
15. Direct and window canonical invocation reach the same depth and produce equivalent
    state, lineage and scope.
16. `COMMON_UPSTREAM` ≠ `UNSCOPED`.
17. No benchmark-specific or model-specific ConsumerView logic.

### 1.2 The 22 window skips are not S-3 failures

They are blocked by **R-B**: the recorded legacy Pipeline S02 response writes prose into
a canonical typed-reference field, and the write boundary correctly refuses it. **This
is not full-chain success**, and it is not evidence that the chain works. It is one
producer defect, owned by Impl S-4, stopping the replay at s02.

### 1.3 Rule for reopening S-3

A later-stage failure does **not** reopen S-3 merely because ConsumerView is involved.
Reopen only on a falsifier against §1.1 — required upstream information omitted, another
candidate's branch-local material leaking into a view, insufficient context reaching a
provider, the invocation view not recorded, direct/window divergence, or declarative
Source-A semantics being ignored.

If ConsumerView correctly transports **bad or incomplete engineering facts produced by
S02/S03**, that is the producing stage's defect, not an S-3 defect.

### 1.4 Residual owner map

| id | residual | owner |
|---|---|---|
| **R-A** | Physical scenario/actor applicability for candidate-independent demands | **S-4** |
| **R-B** | Legacy S02 producer writes prose into typed-reference fields | **S-4** |
| — | `PhysicalEffectObligation` → candidate-specific realization | **S-4** |
| — | `ConstraintRelation` candidate-specific physical constraint responsibility | **S-4** |
| — | Reaction / support / retention responsibility, symbolic maturity | **S-4** |
| — | `LoadPath` tied to a design-wide `LoadCase` | **S-4** |
| **R-C** | Deterministic mobility orchestration still runner-bound | **S-5** |
| **R-D** | DOF domain vs engineering disposition; `UNDISPOSITIONED`; no `MAINTAINED_BY_CLASS` from absence | **S-5** |
| **R-E** | Multi-anchor Configuration/Transition semantics | **S-6** |
| **R-F** | Exact S04A → S04B continuity | **S-6** |
| **R-G** | `ReferenceScale` exact instance/frame semantics | **S-6** |
| **R-H** | Runner-authored S04 premise/commitment boundary | **S-6** |
| — | Located axes, frame origins, distinctness, motion geometry | **S-6** |
| **R-I** | Retained candidate-set truth | **S-7** |
| **R-J** | Selected / committed / reopen semantics; `SelectionDecision` | **S-7** |
| **R-K** | Cross-role engineering establishment / assurance | **S-8** |
| **R-L** | *(narrowed)* a genuinely required dependency with no valid producer must stay visible, never silently suppressed | **S-8** |
| **R-M** | Whole-chain live/unseen generalization | **S-9** |

**R-L is narrowed to the general principle only.** Its two specific historical cases —
s03a's `Joint.axis_direction` → downstream `ReferenceScale`, and Source A demanding
branch-scoped existence of design-wide demand material — were both resolved in Impl S-3
and are not open replays.

---

## 2. Current physical fact inventory

| family | owner | permitted output of | produced by code today |
|---|---|---|---|
| Requirement / Scenario / Actor | s01 | s01 | s01 |
| LoadCase | s02 | s02 | **s02** |
| Obligation | s02 | s02 | **s02** |
| **PhysicalEffectObligation** | s02 | s02 | **NONE** |
| Candidate | s02 | s02 | **s02** |
| Body / RigidGroup / Joint / Interface | s03 | s03a | **s03a** |
| **PhysicalInteraction** | s03 | s03b | **NONE** |
| **ConstraintRelation** | s03 | s03b | **NONE** |
| LoadPath / AssemblyStep | s03 | s03b | **s03b** |

**This is the substance of Impl S-4.** Three physical families are declared in the
contract, listed in `permitted_output_semantics`, and required as consumer premises —
and **nothing authors them**. `PhysicalEffectObligation` is a declared s02 output with
no `to_operations` branch; `PhysicalInteraction` and `ConstraintRelation` are declared
s03b outputs with no branch either. The canonical physical reasoning chain

```
demand → candidate-independent physical effect obligation
       → candidate-specific interaction / constraint / load path
```

has contracts and consumers at every link and a producer at none of the middle ones.

---

## 3. R-B reproduced

```
BM-001  s02 ConsumerView : VIEW_READY
        s02 execution    : SCHEMA_FAILURE
        REFERENCE_NOT_AN_ID: CND-0001.obligations_created holds
            'radial support and axial retention for the rotating relation'
            'a deflection bound and a recovery for the catch'
            'a bound on the open travel'
```

The same response's `obligations_addressed` holds valid ids
(`OBL-0002 … OBL-0007`), and the response does emit `OBL-0001 … OBL-0006`. So the model
referenced correctly where it was pointing at obligations it had written, and wrote
prose where it was describing obligations **it had not written at all**.

---

## 4. `obligations_created` vs `addresses_obligations` — decided, not ambiguous

The frozen contract states it directly:

> *"obligations_created is required: a candidate that needs a bearing has CREATED a
> bearing obligation. Without it, an incomplete candidate looks cheaper than a complete
> one, which is R-16."*

| field | claim | obligation is |
|---|---|---|
| `addresses_obligations` | this principle intends to satisfy a demand that **already exists** | candidate-independent |
| `obligations_created` | this principle **introduces a new demand** by being chosen | authored by the candidate, and thereafter a design demand like any other |

Answers to B3: (1) as above; (2) an addressed obligation is candidate-independent, a
created one becomes one once authored; (3) **yes** — choosing a principle can create a
demand, which is precisely R-16; (4) both, in different fields; (5) **both are
genuinely needed** and neither is redundant; (6) neither is legacy; (7)
`addresses_obligations` for intent toward existing demand, `obligations_created` for
demand introduced; (8) the `Obligation` family owns the obligation, `owned_by: s02`.

**No STOP condition.** The architecture is unambiguous, and the defect is that the
producer describes created obligations instead of authoring them.

### 4.1 Consequence for the fix

R-B is fixed by making s02 **author** the obligations its candidates create and
reference them by id — same-patch closure, which the write boundary already validates.
It is **not** fixed by converting prose to ids, by a shim, or by relaxing R-20.

### 4.2 Consequence for the recorded corpus

The recorded BM responses will remain non-compliant after the producer is corrected,
because they are recordings of a model that was not asked for ids in that field.
Retiring the 22 skips therefore requires **regenerating those recordings with a live
model run**, which this pass is forbidden to perform. The producer fix and the corpus
refresh are separable, and only the first belongs to a no-model-call pass.

---

## 5. SLICE 1 — Pipeline S02 canonical physical-demand producer

Baseline for this slice: `2880db7`.

### 5.1 Obligation vs PhysicalEffectObligation — not duplication

| | Obligation | PhysicalEffectObligation |
|---|---|---|
| purpose (contract) | "A physical or functional thing that must be true for a requirement to hold." | "What physical effect must occur, between which ROLES, under which load case - stated without naming a mechanism." |
| required | statement, derived_from_requirements, mandatory, scope, satisfiable_at, evidence_route, route_available | effect (closed enum), between_roles, addresses_obligations |
| answers | **what must be true** | **what physical effect makes it true** |
| owner | s02 | s02 |

The second **refines** the first through `addresses_obligations` and adds what the
first cannot say: the effect kind, the roles it acts between, and the load case it
holds under. No semantic truth is stored twice. Its own rule settles the timing:
*"S-2 defines it. S-4/U-5 is where s02 begins producing it."*

Its other rule — *"Roles, never bodies. s02 may not decide topology"* — is why
`between_roles` targets Actor, and why a body in that field is refused
(S4-S02-10).

### 5.2 addresses_obligations vs obligations_created — both needed

| field | claim |
|---|---|
| `addresses_obligations` | this principle intends to satisfy a demand that **already exists** |
| `obligations_created` | this principle **introduces a new demand** by being chosen |

From the contract: *"a candidate that needs a bearing has CREATED a bearing
obligation. Without it, an incomplete candidate looks cheaper than a complete one,
which is R-16."* Both target `Obligation`; the obligation itself is owned by the
`Obligation` family, `owned_by: s02`. Neither field is legacy and neither is
redundant.

### 5.3 R-B root cause

The recorded response referenced correctly wherever it had **written** the
obligation, and wrote prose wherever it had **not written one at all**:

```
obligations_addressed : ['OBL-0002' ... 'OBL-0007']          ids
obligations_created   : ['radial support and axial retention for the rotating
                         relation', ...]                      prose
```

So R-B is not a formatting slip. The candidate-created obligations were never
authored as entities, which is the same producer gap as the missing
`PhysicalEffectObligation`: s02 described physical demand instead of writing it.

### 5.4 Producer changes

`ver3/assy_v3/stages/s02_obligation_and_candidates.py`:

- **`to_operations` authors `PhysicalEffectObligation`** — the branch that did not
  exist. Required fields from the response; `under_load_case` and `persistence`
  written only when the model supplies them, never defaulted in.
- **Prompt** gains the `physical_effect_obligations[]` schema, its three reference
  lines, a rule stating the effect level ("say the effect, never the mechanism";
  "name ROLES, never bodies"), and a blunt rule that a reference field is never a
  description — *"if a candidate creates an obligation, write that obligation,
  give it an id, and put THAT ID in obligations_created."*
- The effect vocabulary is **read from the contract**, not restated in the prompt,
  so the two cannot drift (S4-S02-05b).
- **`completeness` reports a reference answered in prose**, attributing it to the
  producer instead of leaving a downstream schema failure to read as a contract
  problem. It **reports and does not repair**: no id is invented, and a test
  asserts the parsed response is not mutated.

No shim, no prose-to-id conversion, no benchmark branch, no weakening of R-20.

### 5.5 Before / after

```
R-B response       -> SCHEMA_FAILURE, REFERENCE_NOT_AN_ID on obligations_created,
                      write boundary refuses the patch          (unchanged)
canonical response -> SUCCESS, patch applies, CND-0001.obligations_created
                      = ['OBL-0002'] and OBL-0002 exists as an Obligation
```

Canonical shape:

```json
"obligations": [{"id": "OBL-0002", "statement": "the rotating relation must be
                  supported", "scope": "CANDIDATE_DISCRIMINATING", ...}],
"physical_effect_obligations": [
  {"id": "PEO-0001", "effect": "TRANSMIT_FORCE", "between_roles": ["ACT-0001"],
   "addresses_obligations": ["OBL-0001"], "under_load_case": "LC-0001"}],
"candidates": [{"id": "CND-0001", "obligations_addressed": ["OBL-0001"],
                "obligations_created": ["OBL-0002"], ...}]
```

Same-patch closure: the candidate references an obligation created in the same
patch, and the write boundary validates it as one act.

### 5.6 Candidate-independence

`PEO-0001` and `PEO-0002` are authored with **no premise and no candidate field**.
Two candidates address the same `OBL-0001`, and exactly one physical demand exists
for it — not one per candidate. A candidate that creates nothing has an empty
`obligations_created`; created and addressed are never conflated.

### 5.7 What s02 still does not author

Asserted, not assumed: after a successful s02 patch, `PhysicalInteraction`,
`ConstraintRelation`, `LoadPath`, `Body`, `RigidGroup`, `Joint` and `Envelope` are
all empty. Candidate-specific realization remains the next slice.

### 5.8 Tests

`ver3/tests/meta/test_s02_physical_demand.py` — 12 tests: R-B before/after,
producer attribution, no-shim scan, PEO production, contract-sourced vocabulary,
candidate-independence, created-vs-addressed, traceability, the negative list of
families s02 must not author, plus an **unseen shape** (a `METER` demand between
roles addressing two obligations, with no load case) and the roles-never-bodies
refusal.

### 5.9 Recording corpus — a new, honest consequence

Changing the s02 prompt **invalidates every recording made against the old one**,
and the repo detects it by prompt hash:

```
recording answers prompt 4894d3f97ea8c29b but the stage built 1eaa4e75e5078e3c;
the response is stale
```

That mechanism exists precisely so a stale answer is never mistaken for a current
one. The 9 probe replays are now skipped as **STALE RECORDING** rather than R-B,
with `test_the_probe_corpus_is_stale_against_the_current_prompt` asserting the
staleness is detected so it cannot pass silently. The benchmark replays remain
R-B.

**No skip was retired.** Both blockers now need the same thing — a corpus refresh
from an authorized live run — which this pass is not permitted to make. Retiring
them on stale recordings would have been the mistake §10 warns about.

### 5.10 Regression

`640 run · 640 pass · 0 fail · 22 skipped` — 9 stale-recording (probe), 12 R-B
(benchmark), 1 unrelated freeze-gate skip. Static scans clean: no benchmark id, no
`slugify`/`generate_id`/`_coerce` in production.

### 5.11 Next S-4 slice

**S03B physical realization**: `PhysicalInteraction` and `ConstraintRelation`
producers (both still declared-with-no-producer), reaction/support/retention at
symbolic maturity, and `LoadPath` tied to the design-wide `LoadCase` through
authored interactions. S-5/S-6/S-7 ownership is unchanged.

## 6. SLICE 2 — Physical contract alignment, then the S03B realization producer

Baseline for this slice: `b848d3b`.

### 6.1 `PhysicalEffectObligation.between_roles` — Actor was the wrong identity

The freeze: *"between which roles (never bodies — they do not exist yet)"*, and its
example is *"a force must pass from the actuation role to the closing role"*. Those
are **product/function roles**. An `Actor` is an **external** participant — the
architecture keeps the two apart, and the contract had conflated them by declaring
`between_roles` a reference to `Actor`.

No new ontology was invented, because the freeze never gives a role an addressable
identity and an existing representation already carries roles the same way:
`LoadCase.applied_to_role` and `reacted_at_role` are declared values, not references.
So `between_roles` is now `kind: role_name`, matching its siblings.

Discharge stays checkable through `PhysicalInteraction.discharges_effect`, which **is**
addressable — the checkability the freeze asks for never depended on roles being
entities.

### 6.2 `ReactionSiteRequirement` — the family the plan recorded as missing

Plan M-7: *"Reaction sites do not exist as a type, so a load path cannot terminate
outside the product."* Freeze: *"a typed, addressable site derived from a scenario's
system boundary, marked external or internal."* Added, owned by **s02**,
candidate-independent:

```yaml
ReactionSiteRequirement:
  semantic_roles: [reaction_site]
  field_semantics:
    scenario: {kind: reference, target: Scenario, resolvable: true,
               referent_population: DESIGN_WIDE}
  owned_by: s02
  required_fields: [entity_id, scenario, boundary_side, at_role]
  boundary_side: [EXTERNAL, INTERNAL]
```

EXTERNAL/INTERNAL is read from the scenario's boundary, never from what kind of thing
the site is — *"whether an actor may be a reaction site is a property of that boundary
(R-12), never a rule about hands."* Without it the world had to be modelled as a body,
and it is not one.

### 6.3 `LoadPath` — typed hops and typed closure

`ordered_hops` was untyped, so a path could be a list of prose and no closure was
checkable. The family's **own rule already said what a hop is** — *"Each hop names the
Interface that carries it"* — so hops are now a typed reference to `Interface`,
INVOCATION_BRANCH. Added `terminates_at` → `ReactionSiteRequirement`, DESIGN_WIDE,
**optional**: a path terminating inside the product is OPEN, which R-12 calls a
legitimate recorded state, and making closure mandatory would force the model to close
a path it had not established.

### 6.4 No duplicate canonical truth

| | | |
|---|---|---|
| candidate-independent | `LoadCase` · `PhysicalEffectObligation` · `ReactionSiteRequirement` | what the world does · what effect must occur · where a reaction may be taken |
| candidate-specific | `PhysicalInteraction` · `ConstraintRelation` · `LoadPath` | how THIS candidate transmits · what it constrains · how the load reaches the site |
| external | `Actor` | a participant outside the product |
| product/function role | declared value (`role_name`, `applied_to_role`, `at_role`) | not an entity, by the freeze's own silence |

Three different facts about load — what the world does, where the reaction may be
taken, and the route to it — with three owners.

### 6.5 The S03B producer

`to_operations` gained the two branches that did not exist: `PhysicalInteraction` and
`ConstraintRelation`. `LoadPath` gained typed closure. Optional fields are written only
when the model supplies them — `terminates_at` above all, because filling it in would be
this code deciding the engineering.

The prompt now asks for physical realization explicitly, with the effect vocabulary read
from the contract rather than restated: *"An interaction TRANSMITS; a joint CONSTRAINS.
They are not the same fact and a joint is not a substitute for one."* And on closure:
*"an open path is a real answer and saying so is better than closing it with something
you did not establish."*

Authored shapes:

```json
"physical_interactions": [{"id": "PHI-A", "groups": ["RGP-A"],
   "effect": "TRANSMIT_FORCE", "discharges_effect": "PEO-0001",
   "at_interface": "IFC-A"}]
"constraint_relations": [{"id": "CRL-A", "retained_group": "RGP-A",
   "blocked_dofs": ["TX"], "configurations": ["CFG-A"], "driver": "LOAD",
   "provider_body": "BOD-A", "provider_site": "IFC-A",
   "maintaining_interaction": "PHI-A"}]
"load_paths": [{"id": "LDP-A", "load_case": "LC-0001", "candidate": "CND-A",
   "ordered_hops": ["IFC-A"], "terminates_at": "RSR-0001"}]
```

### 6.6 Two-candidate isolation

One `LoadCase`, one `PhysicalEffectObligation`, one `ReactionSiteRequirement`; two
candidates with their own topology. After A realizes it:

- A's three authored facts contain **no B id at all**;
- `PEO-0001` and `LC-0001` are **COMMON_UPSTREAM for A** — the authored relation created
  the lineage, exactly as S-3 supports;
- they remain **UNSCOPED for B**, and `BOD-B` is **OTHER_BRANCH** from A;
- B then realizes the **same** obligation with a different effect, and there is still
  exactly **one** `PhysicalEffectObligation` — the demand was not duplicated per
  candidate. Both paths close at the same declared site.

### 6.7 Nothing is invented

A response authoring no physical fact produces none. A prose value in
`discharges_effect` is refused (`REFERENCE_NOT_AN_ID`); a missing referent is refused by
id. `to_operations` is scanned with docstrings stripped for `MAINTAINED_BY_CLASS`,
`infer`, `synthes`, `default_`. After a successful s03b patch, `Envelope`,
`ReferenceScale`, `State`, `Transition`, `MobilityExpectation` and `SelectionDecision`
are all empty — no mobility, spatial or selection work was pulled forward.

### 6.8 Fixture repairs

The typed hops immediately caught canned responses putting a **Body** where the rule
says an Interface carries the hop. Those fixtures now emit an interface and hop through
it — the correction working on its first contact, not a test being bent.

### 6.9 Contract bookkeeping

`ENTITY_FAMILY_AUDIT` 47 → 48 families with an `s4_growth_note` recording why;
`STAGE_OWNERSHIP_MATRIX` and `S02_CONTRACT` give s02 the new family; the
`reaction_site` semantic role is declared with its engineering meaning.

### 6.10 Regression

`651 run · 651 pass · 0 fail · 22 skipped` — 9 stale-recording, 12 R-B, 1 unrelated.
Unchanged: the corpus refresh is deliberately still pending (§11 of the slice brief).

### 6.11 Remaining S-4

Assembly-relevant physical interactions beyond the three families; the R-A applicability
treatment beyond what s02/s03b responsibilities already require; and the corpus refresh,
which needs an authorized live run. S-5/S-6/S-7/S-8/S-9 ownership is unchanged.

## 7. Impl S-5 has NOT begun.

## 9. Status

**S-4 IN PROGRESS — S03B PHYSICAL REALIZATION PRODUCER COMPLETE.**

Slice 1 (§5) and slice 2 (§6) are done: s02 authors the candidate-independent physical
demand, and s03b authors the candidate-specific realization. The corpus refresh and the
remaining S-4 exit criteria are not.

What is complete: the S-3 closure boundary is recorded and frozen (§1), every residual
has an owner (§1.4), the physical fact inventory is measured (§2), R-B is pinned (§3),
and the `obligations_created` semantics question is decided from the frozen contract
rather than invented (§4).

What remains, in order:

1. **s02 producer**: author `PhysicalEffectObligation` entities and the obligations
   candidates create; reference them by id. Prompt and `to_operations` both.
2. **s03b producer**: author `PhysicalInteraction` and `ConstraintRelation` — the two
   declared outputs with no producer.
3. Reaction/support/retention representation at symbolic maturity; `LoadPath` tied to
   the design-wide `LoadCase` through authored interactions.
4. The two-candidate isolation probe, the S4-* test matrix, and the R-B replay after
   the producer fix.

Each needs producer work of a size that should be started with a full context budget,
not appended to an analysis pass.
