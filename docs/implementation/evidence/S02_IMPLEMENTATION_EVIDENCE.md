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

> **S-3 has not begun.** No required-minimum derivation, no view construction, no sufficiency
> assessment, no `ConsumerView`, no `UPSTREAM_INSUFFICIENCY`/`PROJECTION_FAILURE` behaviour,
> and `S03_OWNED` is untouched.
