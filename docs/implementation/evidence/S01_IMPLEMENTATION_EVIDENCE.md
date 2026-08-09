# S-1 IMPLEMENTATION EVIDENCE

**Step S-1 = U-1 + U-2A + U-4 (with M-5A), landed as one atomic migration.**

Authority: `docs/architecture/S01_S04_ARCHITECTURE_FREEZE.md` and
`docs/implementation/S01_S04_INTEGRATED_IMPLEMENTATION_PLAN.md` §24. No architecture decision
was reopened; no later migration unit was implemented.

---

## 1. Scope

| Unit | Delivered |
|---|---|
| **U-1** (M-1) | Authority classes; guarded class-A storage; the mutation gate |
| **U-2A** (M-2A) | The authority-critical contract substrate: the authority model, field-level extendability for the three formerly-direct-write fields, and canonical families for the three side-channel engineering conclusions |
| **U-4** (M-4) | The controlled mutation boundary; `_absorb` eliminated |
| **M-5A** | Commitment substrate: premise references, `SUPERSEDE`, `INVALIDATE`, premise-change propagation |

**Not in scope and not implemented:** consumer sufficiency (S-3), physical reasoning (S-4),
mobility (S-5), spatial refinement (S-6), the selection gate (S-7), the assurance layer (S-8).
No stage module, prompt, validator, fixture or benchmark input was modified.

---

## 2. Files changed

| File | Change |
|---|---|
| `ver3/assy_v3/state/authority.py` | **new** — authority classes, validity vocabulary, mutation gate, guarded containers |
| `ver3/assy_v3/state/design_state.py` | +209/−; authority-aware validation, the four operations, premise propagation, guarded storage, `__setattr__` guard, `standing()` |
| `ver3/assy_v3/state/patch.py` | +21/−; `SUPERSEDE`, `INVALIDATE`, `CONTROLLED_OPS`, `Op.premise_refs`, `Op.reason` |
| `ver3/contracts/DESIGN_STATE_CONTRACT.yaml` | +104; `authority_model` section, `extendable_fields` on three families, three new families |
| `ver3/contracts/STAGE_OWNERSHIP_MATRIX.yaml` | +6; s04 owns the three new families |
| `ver3/contracts/ENTITY_FAMILY_AUDIT.yaml` | +63; the three new families audited; scope and summary reconciled |
| `ver3/tools/run_window2.py` | +107/−; `_absorb` replaced by `_commit_s04` |
| `ver3/tests/state/test_authority_model.py` | **new** — 27 tests, the model itself |
| `ver3/tests/state/test_absorb_writepath_replay.py` | **new** — 8 tests, ADR-001 exact replay |
| `ver3/tests/meta/test_no_uncontrolled_authoritative_writes.py` | **new** — 2 tests, general invariant |
| `docs/implementation/evidence/replays/ADR-001_absorb_writepath.json` | **new** — 3.2 kB reproduction substrate |
| `docs/implementation/evidence/AUDIT_DEFECT_REPRODUCTION_REGISTRY.md` | **new** — ADR-001…ADR-011 |

---

## 3. Pre-implementation write-path inventory

Built from the working tree, not from audit line numbers. Every mutation of `state.entities`,
`state.by_family`, or a state attribute anywhere in `assy_v3/`, `tools/` and `live_providers/`:

| Path | Wrote | Classification | Disposition |
|---|---|---|---|
| `design_state.py` `apply()` CREATE | entity record + family index | **LEGITIMATE CONTROLLED MUTATION** | kept; extended with authority class, validity, premises |
| `design_state.py` `apply()` EXTEND | `dict.update`, unguarded, no owner check, no provenance | **LEGITIMATE BUT INSUFFICIENTLY CONTROLLED** | kept and guarded. **Never exercised in the audited corpus**, so no behaviour depended on the permissive form |
| `run_window2._absorb` → `e["volume"]` | `FunctionalRegion.volume` | **DIRECT WRITE — class A spatial commitment** | eliminated; now `EXTEND` |
| `run_window2._absorb` → `e["insertion_direction"]` | `AssemblyStep.insertion_direction` | **DIRECT WRITE — class A** | eliminated; now `EXTEND` |
| `run_window2._absorb` → `e["frame_origin"]` | `Joint.frame_origin` | **DIRECT WRITE — class A, the most consequential spatial commitment in the pipeline** | eliminated; now `EXTEND` |
| `run_window2._absorb` → `state.s04a_reach` | reach conclusions | **SIDE-CHANNEL — class A, no identity, no owner, no provenance** | eliminated; now `ReachResult` entities |
| `run_window2._absorb` → `state.s04a_elimination` | elimination decision | **SIDE-CHANNEL — class A** | eliminated; now `EliminationRecord` |
| `run_window2._absorb` → `state.s04a_scale` | reference basis | **SIDE-CHANNEL — class A** | eliminated; now `ReferenceScale` |
| `projection.py:20` `dict(state.entities[i])` | a copy into a view | **EPHEMERAL WRITE (class C)** | unchanged; correct as-is |
| `s03…derive_mobility` → patch | `MobilityExpectation` | derived, but with one branch authoring class A from absence | **DEFERRED to U-6/S-5** (ADR-005) |
| `s04…sampling_declaration` | class A from a constant | **DEFERRED to U-7/S-6** (ADR-008) |
| Layer-B checks in `stages/*.py` | findings into `rec` | **ASSURANCE ARTIFACT (class D)** | not in state; relocation is U-9/S-8 |

**A material finding of the inventory:** the three side-channel attributes were **write-only**.
Nothing anywhere in the repository read them. Giving them entities therefore carried **zero
downstream read risk**, and no compatibility bridge was needed.

---

## 4. Authority classification

| Class | Status after S-1 |
|---|---|
| **A — authoritative** | **Fully operational.** Declared per family with a strict default; enforced at runtime by guarded containers and a mutation gate; the only write path is a validated patch. |
| **B — derived** | **Vocabulary and premise mechanism exist; population is later.** `Op.premise_refs` and `_premises` are live and used. The one derivation that authors class A from absence is `derive_mobility`, whose split is U-6 (ADR-005) and is deliberately untouched. |
| **C — ephemeral** | **Structurally distinguishable.** A projection returns plain `dict` copies outside the state entirely; the test asserts a view can be freely mutated with no effect on state, and that a view record is not a guarded record. |
| **D — assurance** | **Unchanged and already separate.** Check findings go into the runner's record, never into `DesignState`. Relocating the checks off the stages is U-9. |

**Stated precisely so it is not over-read:** S-1 makes the class *mechanism* explicit and
enforces class A. Completing the per-family classification — in particular splitting
`MobilityExpectation` and reclassifying the `assurance_families` block — is U-2B/U-6 and is
recorded as such in the contract itself (`authority_model.class_overrides_note`).

---

## 5. U-2A substrate added

**Authority model** (`DESIGN_STATE_CONTRACT.authority_model`): the four classes, a **strict
default** (`AUTHORITATIVE`) so no family escapes controlled mutation by omission, an empty
`class_overrides` map with its deferral recorded, the four controlled operations, the mutation
rule, the validity vocabulary, and the premise rule.

**Field-level extendability** — the contract now decides what may be extended and by whom:

| Family | Field | Extending stage | Note |
|---|---|---|---|
| `FunctionalRegion` | `volume` | s04 | already listed under `authoritative_geometry_fields` |
| `AssemblyStep` | `insertion_direction` | s04 | **had no contract declaration at all** before S-1 |
| `Joint` | `frame_origin` | s04 | see the divergence below |

**Three canonical families**, fields mirroring what s04a already emits — no new semantics:

- `ReachResult` — `actor`, `target`, `reachable`, `approach_side`, `why`
- `EliminationRecord` — `eliminated`, `reason`, `candidate`
- `ReferenceScale` — `basis`, `absolute`, `note`

**One divergence found and deliberately deferred.** `Joint` declares
`fields_owned_by_s04b: [located_frame]`, but no code produces or consumes `located_frame`;
the implementation writes and reads `frame_origin`. S-1 declares the field **actually in
use** and renames neither. Renaming would change what `s04_envelope_and_motion.py` reads,
which is engineering behaviour and outside S-1. **Deferred to U-2B.**

---

## 6. Old write paths removed

`_absorb` is **deleted**, not renamed — the replay test asserts the attribute is absent from
the module. Its replacement, `_commit_s04`, builds real `Op`s, validates them and applies a
patch. Three protections make re-creating the old path fail:

1. `GuardedRecord` / `GuardedEntities` raise `AuthorityViolation` on any write while the gate
   is closed;
2. `DesignState.__setattr__` refuses any attribute outside the object's six declared ones;
3. an AST scan over `assy_v3/`, `tools/` and `live_providers/` fails on either defect shape,
   **and carries a self-test that feeds it the historical code and confirms it fires** — a
   guard nobody has seen fail is not evidence.

**One behaviour deliberately preserved and made visible.** A payload naming an entity that
does not exist was silently skipped (`if e is not None`). It is still not committed —
inventing the entity would be worse — but the drop is now recorded in
`rec["<pass>_uncommitted"]` instead of being invisible.

---

## 7. Controlled mutation implemented

| Operation | Semantics enforced |
|---|---|
| `CREATE` | owner check, required fields, provenance mandatory; stamps authority class and `STANDING` |
| `EXTEND` | entity must exist; field must be contract-declared extendable; **by the declared stage**; **never over an existing value** — that is refused with `EXTEND_OVER_EXISTING`, naming `SUPERSEDE` as the remedy; provenance mandatory; the extending author is recorded separately from the creating author |
| `SUPERSEDE` | reason mandatory; the field must have a prior value; **the prior value is retained** in `_superseded` with its stage, reason and provenance; propagates |
| `INVALIDATE` | reason mandatory; **the record remains readable**; validity becomes `INVALIDATED`; propagates |

A declared premise that does not resolve is refused (`DANGLING_PREMISE`) — a dependency that
cannot be resolved is fiction, and FA-5 cannot be computed from it. A rejected patch changes
nothing: asserted by test, comparing state hashes.

---

## 8. M-5A commitment substrate

`Op.premise_refs` records the class-A ids a value depends on; they accumulate on the entity as
`_premises`. When a premise is superseded or invalidated, every `STANDING` dependent becomes
`STALE` with a `_stale_because` record naming the premise and what happened to it. The
dependent's **value is untouched** — it loses authority, not existence (FA-1 + FA-5).
`state.standing(family)` returns only entities that still carry unqualified authority.

**Propagation strategy:** eager on write, because the premise references needed to compute it
are recorded at write time. The freeze leaves the strategy open (§9); this is the one that
needs no additional bookkeeping. It is an implementation choice and is revisable.

**The binding used in the runner is representational, not invented engineering.** Every s04
spatial value is expressed in the reference scale, so the scale is recorded as their premise.
Withdrawing the basis therefore costs every coordinate expressed in it its unqualified
authority. No engineering premise was fabricated to demonstrate the mechanism.

---

## 9. Compatibility bridges

**None.** No read adapter was needed, and none was written.

- The three formerly-direct-written fields keep their names and positions on the same
  entities, so `s04_envelope_and_motion.py` reads them unchanged.
- The three side-channel attributes were write-only, so nothing lost a reader.
- `state.family()` still returns every entity regardless of validity, so no existing consumer
  changes behaviour. `standing()` is additive.

**There is exactly one write authority.** No release contains both a controlled and an
uncontrolled class-A path — which is why S-1 was atomic across three units.

---

## 10. Tests added

| File | Tests | Level |
|---|---|---|
| `tests/state/test_authority_model.py` | 27 | **2** — the model itself, mechanism-independent |
| `tests/state/test_absorb_writepath_replay.py` | 8 | **1** — ADR-001 exact replay |
| `tests/meta/test_no_uncontrolled_authoritative_writes.py` | 2 | **2** — general invariant + self-test |

Written as stdlib `unittest`, matching the repository's deliberate no-pytest convention
(`.github/workflows/ver3-boundaries.yml`).

Coverage of the required invariants A–J: **A** create+provenance · **B** permitted extend ·
**C** four refusal modes · **D** supersede retains history · **E** invalidate retains record ·
**F** premise propagation, both directions, plus dangling-premise refusal · **G** four
uncontrolled-write shapes + the side-channel shape · **H** ephemeral projection + declared
classes · **I** the three new families, ownership and required fields · **J** provenance and
references survive every mutation, and a rejected patch changes nothing.

---

## 11. Broad validation results

One coherent pass, run after the migration was complete.

| Suite | Result |
|---|---|
| `ver3/tests/state` (new) | **35/35 OK** |
| `ver3/tests/meta` (full, 310 tests) | **309 pass, 1 failure** — pre-existing, see §12 |
| `ver3/tests/window` (S01→S02 with real stages over recorded responses) | **8/8 OK** |
| `assy_v3` import boundary (CI step) | **OK** |
| Runner modules import (`run_window2`, `run_window`, `run_live_window`, `repair_prompt_pairing`) | **OK** |
| Static scan for remaining direct class-A writes | **clean**, and the scan's self-test confirms it detects the historical code |

**No model call was made.** No benchmark was rerun. S-1 is structural, and the plan does not
require model runs for it.

---

## 12. Failures encountered and classification

| Failure | Class | Action |
|---|---|---|
| `test_entity_family_audit` × 3 — 44 families vs 41 audited | **(C) U-2A contract insufficiency** | **Fixed within S-1.** The three new families were added to `ENTITY_FAMILY_AUDIT.yaml` with their six required facts; `families_audited` 41→44, `CORE` 32→35, with a note recording the S-1 growth. `families_added` stays 0 — that field records the *audit's* own additions, and the audit still adds none. |
| `test_package_path.test_only_permitted_historical_occurrences_remain` | **(E) pre-existing, unrelated to S-1** | **Not fixed. Documented.** Verified failing at HEAD before any S-1 change (via `git stash`). Cause: `docs/audit/AUDIT_EVIDENCE_LOG.md` quotes the pre-rename package path while recording the rename event itself — introduced by the audit documentation commit `dc65de9`. Fixing it properly requires either adding the file to a frozen allowlist whose every entry must be justified in a **frozen change-proposal record**, or rewording a **frozen audit record**. Neither belongs in S-1. Recorded here so it is not mistaken for an S-1 regression. |

No failure was classified **(G) architecture contradiction**. Nothing in S-1 required
reopening a frozen decision.

**One separate observation, not a test failure.** The CI workflow's final step asserts that
`ver3/assy_v3/stages` does not exist. It does exist (s01–s04). That step has been stale since
the stages were built and is unrelated to S-1; it is noted, not changed.

---

## 13. Audit-defect replay

**ADR-001 — uncontrolled authoritative write and side-channel engineering fact.**
Registry: `AUDIT_DEFECT_REPRODUCTION_REGISTRY.md`. Substrate:
`replays/ADR-001_absorb_writepath.json`.

**Historical reproduction path.**
`run_window2.run_case` → `state.apply(out.patch)` → `_absorb(state, key, raw)` →
`state.entities[id][field] = value` (three spatial fields) and
`state.s04a_reach / s04a_elimination / s04a_scale = ...` (three engineering conclusions).
No operation, no ownership check, no validation, no provenance, and nothing in the system
could detect it.

**Post-S-1 replay procedure.** Seed a `DesignState` with the upstream entities the historical
payload refers to; drive the current code over the **historical payload verbatim**; assert
properties of the path, never of the values. `ver3/tests/state/test_absorb_writepath_replay.py`.

**Before / after.**

| | Before | After |
|---|---|---|
| direct field write | succeeded silently | raises `UNCONTROLLED_WRITE` |
| side-channel attribute | succeeded silently | raises `SIDE_CHANNEL_WRITE` |
| `_absorb` | present | absent from the module |
| the three spatial facts | in state, no provenance | in state, via `EXTEND`, stage `s04`, provenance recorded |
| reach / elimination / scale | unreadable attributes | entities with ids, owners and provenance |
| premise binding | none possible | coordinates bind to the scale they are expressed in; withdrawing it marks them `STALE` while leaving values intact |
| unresolvable target | silently skipped | recorded in `rec["<pass>_uncommitted"]` |

**Generalized invariant result.** The AST scan over `assy_v3/`, `tools/` and `live_providers/`
reports no direct class-A write and no side-channel state attribute, and its self-test
confirms the scan fires on the historical code. 27 further tests establish the model itself.

**LLM call required: none.** REPLAY TYPE `STRUCTURAL`. The defect was in state mutation, so
the replay drives state mutation; adding model variability would weaken the evidence.

**Precise claim established.** *The historical authoritative-write bypass no longer exists,
the same engineering facts still reach authoritative state through controlled operations
carrying provenance, and the class of defect is refused at runtime and detected statically
under any function name.*

**What remains unestablished.** That the pipeline reasons better; that any downstream
consumer uses the new representation (nothing reads `ReachResult`, `EliminationRecord` or
`ReferenceScale` yet — consumers are S-3 onward); and anything about live behaviour. **No
Level-3 claim is made.**

---

## 14. Exit criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Four authority categories operationally distinguishable where needed | **MET**, with §4's precision: A enforced; B/C/D declared, C structurally distinguishable, full population is later units |
| 2 | One controlled mutation boundary for authoritative state | **MET** |
| 3 | `CREATE` / `EXTEND` / `SUPERSEDE` / `INVALIDATE` operational | **MET** |
| 4 | U-2A provides the minimum representation to eliminate every audited direct/side-channel write | **MET** — three extendable fields, three families |
| 5 | `_absorb` no longer performs direct assignment | **MET** — deleted |
| 6 | No equivalent uncontrolled class-A path remains | **MET** — runtime guards + AST scan with self-test |
| 7 | Provenance survives authoritative mutation | **MET** — creating, extending and revising authors all retained |
| 8 | Premise dependencies representable | **MET** |
| 9 | Premise change prevents silent dependent authority | **MET** |
| 10 | Historical facts preserved, not overwritten or deleted | **MET** |
| 11 | Derived/ephemeral recomputable without being mistaken for authored | **MET for C**; class-B population deferred to U-6 as planned |
| 12 | Downstream continues without a second write authority | **MET** — window suite 8/8, no compatibility bridge needed |
| 13 | New invariant tests pass | **MET** — 37/37 |
| 14 | Relevant regression passes, or failures explicitly separated | **MET** — 1 pre-existing failure, verified at HEAD, classified in §12 |
| 15 | No S-2+ functionality prematurely implemented | **MET** — no stage, prompt or validator touched; diff reviewed |

**S-1 is COMPLETE.**

---

## 15. Residual risks

1. **The AST scan is intentionally narrow.** It catches the two shapes the audit found. A
   write reaching state through an aliased local (`e = state.entities[i]` in one function,
   `e[k] = v` in another) would evade the scan — but **not** the runtime guard, which is the
   enforcement. The scan is early warning, not the boundary.
2. **Eager propagation is O(entities) per revision.** Fine at current scale; if revisions
   become frequent the strategy is revisable without touching the semantics, which is why the
   freeze leaves it open.
3. **`_premises` is only as good as what producers declare.** S-1 populates it where the
   dependency is representational and certain. Broader premise binding is engineering
   knowledge and belongs to the units that own those facts.
4. **Nothing reads the three new families yet.** They are correctly represented and currently
   unconsumed. That is expected at S-1 and is the shape of the work S-3 onward.
5. **`located_frame` vs `frame_origin` remains divergent** in the `Joint` contract. Recorded
   in §5; deferred to U-2B.
6. **The strict default classifies every family as class A.** Deliberate — it errs toward
   rigor. It means some genuinely derived or assurance families are currently held to
   controlled mutation. No defect follows; the correction is U-2B/U-6.

---

## 16. Deferred to later units

| Item | Unit / step |
|---|---|
| Full per-family authority classification; `MobilityExpectation` domain/disposition split | U-2B / U-6 · S-2, S-5 |
| `located_frame` / `frame_origin` divergence | U-2B · S-2 |
| Principle shape, `ConstraintRelation`, hypothesis-family retirement, dangling references | U-2B · S-2 |
| Consumer sufficiency; the positional slice; `S03_OWNED` | U-3 · S-3 |
| `derive_mobility`'s authoring-from-absence branch (ADR-005) | U-6 · S-5 |
| `sampling_declaration` from a constant (ADR-008) | U-7 · S-6 |
| Selection gate, blocking semantics, the two poles (ADR-009) | U-8 · S-7 |
| Assurance relocation and claim classes (ADR-010, ADR-011) | U-9 · S-8 |
| Fixture regeneration and the live chain | S-9 |

**Implementation stops here. S-2 is not begun.**
