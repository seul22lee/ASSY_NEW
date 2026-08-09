# S-2 IMPLEMENTATION EVIDENCE

**Step S-2 = U-2B — Remaining Canonical Contract Migration (M-2B).** Baseline `6ea8e33`.

S-1 remains regression-frozen: 69/69 authority tests pass unchanged. **S-3 has not begun.**

---

## 1. Scope

Canonical contract and semantic-schema migration only. One canonical language for S01–S04.
**No prompt rewrite, no stage reasoning change, no Consumer View, no `S03_OWNED` deletion, no
mobility derivation change, no S04 refinement, no gate, no evaluator/dashboard migration, no
fixture edits, no model calls.**

## 2. Files changed

| File | Change |
|---|---|
| `contracts/DESIGN_STATE_CONTRACT.yaml` | source of truth for entity semantics: `field_semantics` (60 fields), `principle_shape`, `authorship_split`, three new families, `blocked_by`/`retained_by`/`co_actuated_by` retired, `multi_owner_exceptions`, `legacy_producers` |
| `contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml` | **new** — source of truth for stage responsibility, engineering questions, reasoning-premise classes |
| `contracts/CONTRACT_AUTHORITY.yaml` | **new** — the authority hierarchy: one semantic fact, one authoritative definition |
| `contracts/STAGE_OWNERSHIP_MATRIX.yaml` | demoted to a checked projection; `owns`/`extends` rebuilt from the source of truth |
| `contracts/ENTITY_FAMILY_AUDIT.yaml` | demoted to a review record; three new families audited |
| `contracts/STATUS_SEMANTICS.yaml` | four status constructs declared and separated; downstream debt recorded |
| `contracts/stages/S02,S03_CONTRACT.yaml` | hypothesis families retired |
| `assy_v3/state/design_state.py` | `Contracts` made immutable; `field_semantics()` accessor |
| `assy_v3/stages/s02_obligation_and_candidates.py` | **2 mechanical lines** — see §18 |
| `tests/meta/test_canonical_contracts.py` | **new** — CON-01…CON-18, 22 tests |

## 3. Pre-edit discrepancy inventory

Computed from the working tree, not from audit line numbers.

| Concept | Current definitions | Conflict | Authoritative target | S-2 action | Later producer step |
|---|---|---|---|---|---|
| ownership | DESIGN_STATE `owned_by`, MATRIX `owns`, AUDIT `owning_stage` | 3 files, no stated authority; 2 families with multiple owners | DESIGN_STATE | matrix + audit become checked projections | — |
| extendability | MATRIX `extends` vs family `extendable_by`/`extendable_fields` | **16 stage/family pairs disagreed**; `extends` was free text with no field behind it | DESIGN_STATE `extendable_fields` | rebuilt; extension requires a declared field | — |
| `principle` | contract declared **no shape**; three shapes lived in prompts/fixtures | bare string vs parallel arrays vs mapping | mapping function_class → principle_family | one shape, no shim | S-4 prompt, S-9 fixtures |
| `blocked_by` | typed relation, no `entity_id` | non-addressable; a disposition citing it could not resolve | `ConstraintRelation` entity | retired with a record | S-4/U-5 |
| `retained_by`, `co_actuated_by` | typed relations, no `entity_id` | **same defect, not previously named** | ConstraintRelation / PhysicalInteraction | retired | S-4/U-5 |
| hypothesis families | required by S02/S03 contracts, defined nowhere | required-but-undefined | `PhysicalEffectObligation` → `PhysicalInteraction` | retired, replaced | S-4/U-5 |
| `required_by_actors`, `reach_targets` | s03 prompt prose only | no canonical home | FunctionalRegion optional fields | promoted | S-4 prompt |
| obligation reference | `obligations_addressed` (12) / `addresses_obligations` (8) / `discharges_obligations` (2) | three names, one concept | `addresses_obligations` | unified | S-4, S-9 |
| `MobilityExpectation` | one `dispositions` field | domain and disposition indistinguishable | `authorship_split` | split at contract level | S-5/U-6 |
| status | execution / evaluation / solver / observable vocabularies, no constructs | one badge could mean several things | four constructs | declared, separated | S-8/U-9 |
| references | none declared | integrity guessed by key suffix + is-upper-case heuristic | `field_semantics.kind: reference` | 33 declared with targets | — |
| spatial fields | none declared a frame | numbers with no meaning | `field_semantics.kind: spatial` | 10 declared with frames | — |
| contract mutability | plain nested dicts on `state.c` | rules editable at runtime | immutable `Contracts` | closed | — |

## 4. Canonical source-of-truth model

`CONTRACT_AUTHORITY.yaml` declares five sources and three projections. Entity semantics →
`DESIGN_STATE_CONTRACT`; stage responsibility → `STAGE_RESPONSIBILITY_CONTRACT`; status →
`STATUS_SEMANTICS`; mutation → `STAGE_PATCH_CONTRACT`; provenance → `PROVENANCE_CONTRACT`.
`STAGE_OWNERSHIP_MATRIX` and `ENTITY_FAMILY_AUDIT` are **projections**, checked rather than
manually reconciled. Prompts may explain a contract and may never be one.

## 5–8. Closure results

- **Ownership**: 47 families, each resolving to one owner, or to a **declared, reasoned,
  scheduled** `multi_owner_exception` (Witness, NegativeControl — both outside S01–S04). Any
  new multi-owner declaration is a defect.
- **Extendability**: 16 disagreements → 0. Extension needs a field; an owner may not also be
  an extender.
- **`principle`**: one mapping shape; rejected shapes named; no shim.
- **Relations**: three non-addressable typed relations retired; `ConstraintRelation` is
  addressable with an id and resolvable provider/site/interaction references.

## 9–13. Concept resolutions

Hypothesis families retired and replaced (families defined; **production is S-4/U-5**).
Prompt-only fields promoted with reference targets. `addresses_obligations` unified.
`MobilityExpectation.authorship_split` separates DERIVED domain (totality = **BOOKKEEPING**)
from AUTHORITATIVE disposition (premise required, target `ConstraintRelation`), with
`UNDISPOSITIONED` as vocabulary only. Four status constructs with disjoint vocabularies —
`PROVISIONAL` deliberately belongs to maturity alone.

## 14–15. Reference and frame coverage

**45 reference declarations** (target + cardinality + resolvability) and **10 spatial
declarations** (frame) across 26 families, where previously there were none. CON-03/04/06/18
prove no reference targets an undefined or retired family, no declaration names a field its
family does not have, and no spatial field lacks a frame. **Dangling references: recomputed
from the working tree, not assumed to be 14 — 0 remain in the canonical corpus.**

## 16. Stage responsibility matrix

Seven stages/gate (`s01 s02 s03a s03b s04a gate s04b`), **28 reasoning-premise classes**, each
citing a declared engineering question and a reason. CON-11 enforces the citation; CON-11b
requires a stage with no premises to say why (s01 — it is the only stage that reads source).
CON-12 keeps representational dependencies and reasoning premises in separate files and
constructs. **This is S-3's input; no derivation, view or sufficiency assessment exists.**

## 17. Contract immutability

`Contracts` holds its documents privately and every accessor returns a detached copy;
attribute assignment raises `IMMUTABLE_CONTRACT`. Mutating a read changes no rule — verified
against `extendable_fields`, `owner_of`, `authority_class` and `may_create`.

## 18. Producers intentionally left legacy

`legacy_producers` in the contract records six rows with migration steps. **No shim accepts a
rejected shape.**

**Two mechanical lines were changed in `s02_obligation_and_candidates.py`**, and they need
justification because a stage file changed. Both store/read the **canonical field name**; the
prompt and the model's response key are untouched, and the stage asks and answers exactly the
same question. Notably s03 *already* used `addresses_obligations` — s02 and the contract were
the outliers, so this is alignment, not a new decision. Without it the repository is
inoperable, which §24 permits only for non-semantic adaptation. It is that.

## 19–21. Tests, validation, exit criteria

**22 new tests** (CON-01…CON-18 plus authority-hierarchy and immutability checks).

| Suite | Result |
|---|---|
| `tests/state` (S-1 authority regression) | **69/69 OK** |
| `tests/meta` (334) | **333 pass, 1 pre-existing failure** (`test_package_path`, verified failing at HEAD since `dc65de9`) |
| `tests/window` | **8/8 OK** |

All 25 S-2 exit criteria hold. Failure classification: contract closure defects found by the
new tests were **(A)/(C)** and fixed; the producer name was **(E) legacy by design**, resolved
by the mechanical alignment above; the docs path reference is **(F) pre-existing**. No **(H)
sequencing contradiction** arose.

## 22–24. Residual risks and scope

Sprawl (plan R-1): adding a family means editing its own contract entry plus one projection
line, both structurally checked — no unrelated stage-pair whitelist. Field declarations are
required only where a field carries reference, spatial or authority semantics.

Residual: the canonical contract is **ahead of most producers by design**, and that gap is
recorded rather than concealed; `quality_profile.py` still reads a legacy key from raw model
JSON (not state), recorded as S-8 debt.

> **S-3 has not begun.**

> **⚠ The COMPLETE claim above is superseded by §25.** It was true of the canonical
> sources and their own tests. Two things it did not cover: the loaded contract documents
> were still reachable and mutable, so the immutability claim was false as implemented; and
> the stage-contract corpus was never classified, so three files stated canonical facts with
> no declared authority status. See §25. No required-minimum derivation, no view construction, no sufficiency
> assessment, no `ConsumerView`, no `UPSTREAM_INSUFFICIENCY`/`PROJECTION_FAILURE` behaviour,
> and `S03_OWNED` is untouched.


---
---

# §25 BOUNDED CONTRACT-CORPUS CLOSURE

Baseline `ec184b4`. Bounded closure of the gap between the declared authority model and the
actual corpus. **Not S-3.** No prompt, stage reasoning, mobility runtime, S04 behaviour,
fixture, benchmark, evaluator, architecture document or CI hygiene change.

## 25.1 Contract-storage mutability — reproduced first

`Contracts` stored the loaded documents in an ordinary attribute. Against `ec184b4`:

```
docs = c._docs                                   # ordinary attribute lookup
docs["families"]["Joint"]["owned_by"] = "s99"
docs["stages"]["s04"]["owns"].append("Requirement")
```

**All four authorization queries changed** — `owner_of` → `s99`, `extendable_fields` gained a
field, `may_create("s04","Requirement")` → True, `authority_class` → `EPHEMERAL`. Public
accessors returned copies while the backing stayed reachable, so **S-2's immutability claim
was false as implemented**.

## 25.2 Correction

The documents move to a **module-private `WeakKeyDictionary` keyed by the object** — the same
fix that closed the DesignState read surface at S-1, for the same reason: an object nobody can
reach cannot be edited. `hasattr(c, "_docs")` is now false; `_d` refuses. Roots still refuse
replacement with `IMMUTABLE_CONTRACT`. **DesignState authority storage was not reopened.**

## 25.3 Stage-contract classification

All seven files, **63 sections**, four classes and no ambiguous fourth state:

| File | CANONICAL_PROJECTION | LEGACY_PRODUCER | OPERATIONAL |
|---|---|---|---|
| S01 | 4 | — | 10 |
| S02 | 4 | 1 | 10 |
| S03 | 4 | 3 | 13 |
| S04 | 3 | — | 3 |
| S05 | 3 | 1 | 13 |
| S06 | 3 | — | 11 |
| S07 | 3 | — | 14 |

## 25.4 True canonical contradictions found — three

Each was resolved by asking the required first question: **is the canonical source wrong, or
is a projection stale?** In all three the source was right.

1. **`S02.creates` claimed `PhysicalInteraction`** — owned by s03. An artefact of the S-2
   rename that retired the hypothesis families. Removed; s02 states role-level effect
   obligations, and realising them is s03's decision.
2. **`S01.creates` claimed `SystemBoundary`** — a family defined nowhere. The boundary is a
   **required field of `Scenario`**. The same defect class as the retired hypothesis families,
   and **found by the corpus-wide check rather than by name** — which is the point of making
   the tests data-driven.
3. **Retired relations and superseded field spellings in unclassified sections** — moved into
   explicitly legacy sections.

`S03.creates` was also completed to match canonical ownership (it omitted `ConstraintRelation`
and `PhysicalInteraction`, which s03 **owns** even though it does not yet **produce** them).

## 25.5 Legacy retained honestly

Five legacy sections, each naming a canonical replacement, a canonical source, a migration step
and `authoritative_for_canonical_semantics: false`. s03 gains a `current_producer` block stating
plainly that it emits `blocked_by`/`retained_by` and does **not** yet emit `ConstraintRelation`
or `PhysicalInteraction`, migration S-4/U-5.

**Nothing was rewritten to claim conformance**, and the canonical contract was not weakened to
match a producer — that would carry the audited defect forward under a new name.

## 25.6 Source-of-truth coverage

`CONTRACT_AUTHORITY` now covers the stage corpus, with the four-class vocabulary declared and
each class bound to the CLOSURE checks that enforce it. A projection may name several declared
categories; every one must exist.

**How many places must be edited to change one canonical fact?** One authoritative edit, plus
checked projections. Family owner, field name, reference target, relation meaning, stage
responsibility and status meaning each have exactly one source; a stale projection now fails a
test rather than waiting for a reader to notice.

## 25.7 Tests added

**15 CLOSURE tests**, data-driven over `contracts/stages/*.yaml` — none names S02 or S03.
CLOSURE-01 projection matches source · 02 legacy fully declared · 03 no contradicted ownership ·
04 no undeclared field alias · 05 retired families absent · 06 retired relations only in legacy
sections · 07 every section classified · 08 contract storage encapsulated · 09 every projection
names an existing source · 10 every legacy section has a scheduled step.

One existing CON assertion was **generalised, not weakened**: a projection may name several
declared categories, and every one must still exist.

## 25.8 Validation

| Suite | Result |
|---|---|
| S-1 state authority | **69/69 OK** |
| ADR-001 Level 1 / Level 2 | **8/8 · 65/65 OK** |
| S-2 CON (original) | **22/22 OK** |
| S-2 CLOSURE (new) | **15/15 OK** |
| Full meta | **352 OK** (skipped 1) — no failures |
| CI workflow-equivalent, all three steps | **OK**, hygiene from `ec184b4` intact |
| Window | **8/8 OK** |

Classification: contract storage **(A)**; the three contradictions **(B)/(C)**; unclassified
legacy **(D)**. All fixed here. No **(E) canonical source error** — every discrepancy resolved
to a stale projection. No **(F)**, **(G)**, **(H)** or **(I)**.

## 25.9 The two-line S02 change from S-2, re-audited

Verified against the current tree: the prompt still asks for `obligations_addressed`, the model
response key is unchanged, and the parser maps it to the canonical stored name. No engineering
decision changed. **The statement remains accurate**, and it was not expanded here.

## 25.10 Deferred

s02 physical reasoning, s03 `PhysicalInteraction` and `ConstraintRelation` production, mobility
disposition runtime, S04 spatial behaviour, Consumer Sufficiency, prompt rewrite, fixture
regeneration, evaluator migration — all unchanged and all scheduled.

> **S-2 CLOSED.** All 16 closure exit criteria hold. **S-3 has not begun.**

> **⚠ Superseded by §26.** The closure classified every section, but a section could be
> labelled CANONICAL_PROJECTION while naming only a source FILE. 24 were so labelled and
> **0 carried a resolvable fragment**, so "one authoritative edit per fact, plus checked
> projections" was broader than the enforcement. See §26.


---
---

# §26 CANONICAL PROJECTION INTEGRITY CORRECTION

Baseline `e520048`. Very narrow: make the declared projection invariant true. **Not S-3, not a
producer migration, not prompt work.** No implementation code changed.

## 26.1 The gap, reproduced first

**24 sections labelled CANONICAL_PROJECTION; 0 with a machine-resolvable source fragment.**
Every one named a file and nothing more. Only `owned_decisions` was really checked, and by
CLOSURE-01/03 hard-coding that one section name — so 21 of 24 were unenforced.

## 26.2 Breakdown after honest classification

| | Count |
|---|---|
| **Valid projections** (structured value, resolvable fragment, checkable relation) | **3** — `owned_decisions` on S01, S02, S03 |
| **Operational summaries misclassified as projections** | **21** |
| Stale contradictions | 0 new — the three found at S-2 closure remain fixed |

The 21 were prose: `engineering_question` and `engineering_responsibility` are **strings**
while the canonical source holds **lists**, and `prohibited_decisions` carries stage-local
detail (invariant ids, retirement rows) the canonical list does not. **A paraphrase is not
equality.** Rather than invent a fuzzy comparison, they are now OPERATIONAL with a
`see_canonical` pointer marked `binding: false`.

## 26.3 S03 aggregate disposition

The canonical architecture defines `s03a` and `s03b`; the contract file is one `s03`. **No
fake canonical `s03` entry was created** — that would manufacture a fact rather than check
one. Its prose sections are OPERATIONAL pointing non-bindingly at `stages.s03a and s03b`; its
`owned_decisions` is a real EXACT projection of `owned_by == s03`, which needs no aggregation.
PROJ-05 fails on any pointer to a canonical stage that does not exist.

The same reasoning applies to S05–S07: the frozen architecture defines no canonical
responsibility for them, so their sections carry a `see_canonical_note` saying so rather than
a pointer to nothing.

## 26.4 Projection metadata

```yaml
canonical_source:
  file:     ver3/contracts/DESIGN_STATE_CONTRACT.yaml
  path:     "entity_families+assurance_families[*].owned_by == s03"
  relation: EXACT
projected_key: creates
```

Relations are deliberately tiny — `EXACT`, `SUBSET`, `ORDERED_SUBSET`. A larger transformation
language would let a projection pass by being clever rather than by being the same fact.

## 26.5 Generalized validator

`test_projection_integrity.py` discovers every CANONICAL_PROJECTION in every stage file,
resolves its fragment, applies its relation and fails on mismatch. **No special case for S02,
S03, ownership or questions** — a new projection enters the set automatically.

PROJ-01 resolvable file · 02 resolvable fragment · 03 supported relation · 04 relation
satisfied · 05 no unresolved canonical stage id · 06 prose cannot pass as EXACT · 07 exactly
one classification per section · 08 legacy declares replacement + step · 09 operational is
non-authoritative · 10 negative controls.

## 26.6 Negative controls

Six, each perturbing a synthetic copy and asserting the mechanism reports it: **A** stale
ownership projection · **B** stale question projection · **C** bad source path · **D**
undeclared relation · **E** unresolved `s03` → `s03a`/`s03b` · **F** prose marked EXACT. A
seventh asserts the live corpus still passes, proving the controls touched copies only.

## 26.7 Source-of-truth result

**Before:** 24 declared projections, 3 enforceable. **After:** 3 declared projections, 3
enforceable — and changing the canonical `owned_by` without updating the projection now fails
CI, demonstrated by control A. The claim is narrower and, for the first time, true.

## 26.8 An error I made and corrected

A regex rewrite of the classification blocks **destroyed all seven stage contracts** —
top-level keys fell from ~20 to 3. Caught immediately by a key-count assertion, restored with
`git checkout`, and redone by exact line-span replacement with a per-file assertion that the
key count is unchanged. No content was lost; the committed diff shows only the
`authority_status` blocks changing.

## 26.9 Deferred

**Benchmark-specific operational content.** Some OPERATIONAL and legacy sections cite benchmark
identifiers and retirement rows. It is **not** canonical authority, is not a projection, and
must never feed automatic Consumer Sufficiency derivation. Recorded as later cleanup debt;
**not started here**.

Producer migrations unchanged: s02 physical reasoning, s03 canonical family production,
mobility runtime, S04 spatial, Consumer Sufficiency, prompts, fixtures, evaluator.

## 26.10 Regression

**69/69** state · **368 meta OK** · **8/8** window · ADR-001 L1/L2 OK · **22/22** CON ·
**15/15** CLOSURE · **16/16** PROJ · all CI steps OK. Two existing CLOSURE assertions were
**updated to the nested metadata schema, not weakened** — they now additionally require a
fragment and a relation.

Classification: the gap was **(A) projection metadata defect**; the 21 reclassifications were
**(C) misclassified operational**. No **(B)**, **(E)**, **(F)**, **(G)**, **(H)** or **(I)**.

> **S-2 FINAL FROZEN.** All 19 freeze criteria hold. **S-3 has not begun.**
