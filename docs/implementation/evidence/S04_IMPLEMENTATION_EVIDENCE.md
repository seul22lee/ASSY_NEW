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

## 6. Impl S-5 has NOT begun.

## 9. Status

**S-4 IN PROGRESS — S02 CANONICAL PHYSICAL-DEMAND PRODUCER COMPLETE.**

Slice 1 is done (§5). Candidate-specific physical realization is not.

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
