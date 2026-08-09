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

**S-1 exit criteria were met as written at commit `2570aa4`.** A subsequent hardening pass
established that criterion 6 — *"no equivalent uncontrolled class-A path remains"* — was
**true only for the top-level shapes the historical defect used**, and not for the general
invariant. See §17. **The unqualified COMPLETE claim below is superseded by §17.20.**

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


---
---

# §17 S-1 AUTHORITY-BOUNDARY HARDENING

Second pass over S-1 only. No architecture decision reopened, no later unit begun, no stage
reasoning, prompt, validator, fixture or benchmark changed. The original `2570aa4` evidence
above is preserved unedited.

## 17.1 Why the first implementation was insufficient

`2570aa4` closed the historical `_absorb` path and guarded the entity table and entity
records. **That is the top level only.** The claim it supported was *"the historical bypass is
gone"*; the claim S-1 actually owes is *"authoritative mutation is impossible outside the
boundary."* Those are different, and the gap between them was executable.

Twenty-two of twenty-three reproduction tests failed against `2570aa4` — each one a real
bypass, not a hypothetical.

## 17.2 Findings, each reproduced before being fixed

| # | Finding | The bypass, executable |
|---|---|---|
| **A** | **Nested mutability** | `state.entities[eid]["volume"]["centre"][0] = 999` succeeded. The outer record was guarded; every value inside it was a plain dict or list. An authoritative spatial commitment could be changed with no patch, no provenance, no history and no propagation. |
| **B** | **Container API coverage** | `GuardedEntities` overrode six mutators and **not `popitem`** — `state.entities.popitem()` removed an entity silently. Nested values had no guard at all. Methods had been hand-listed, so one was missed. |
| **C** | **Entity-family authority spoofing** | `_extend_problems` looked up permissions using the caller-supplied `op.entity_type`. Declaring `entity_type="FunctionalRegion"` on a Joint borrowed `volume`'s extendability and wrote it onto the Joint. `SUPERSEDE` and `INVALIDATE` checked family not at all. |
| **D** | **Input and history aliasing** | `Op.fields` values were stored by reference. A caller that kept its list could mutate stored state afterwards. The prior value retained by `SUPERSEDE` was equally reachable. |
| **E** | **Gate exposure** | `state._gate` was a public attribute holding a public boolean switch: `with state._gate.unlocked(): ...` was a supported one-line bypass. Worse, `_gate` was in the settable-attribute whitelist, so the capability could be **replaced**. |

## 17.3 Selected hardening design

**Recursively guarded containers, wrapped on write.** `GuardedDict` and `GuardedList` replace
plain containers at *every depth*; mutating methods are **generated** from an enumerated list
rather than hand-written, so one cannot be left active by oversight — which is exactly how
`popitem` survived.

Evaluated against the criteria the brief names:

| Criterion | Recursive guards *(selected)* | Frozen/immutable storage | Deep-copy on read |
|---|---|---|---|
| runtime enforcement | **loud rejection at every depth** | rejection | **silent no-op** — caller believes the write worked |
| alias safety | **construction makes new containers, so input aliasing is closed by the same mechanism** | closed | closed |
| serialization | identical — subclasses of `dict`/`list` | `tuple` serializes, but round-trips differently | identical |
| existing readers | **unchanged** — `isinstance`, indexing, `.get`, iteration, `==` against a list, `len`, `min` all behave | **breaks**: `tuple != list` in every equality and in geometry code | unchanged |
| provenance | unaffected | unaffected | unaffected |
| performance | wrap once per write; **reads cost nothing** | one-time | **cost on every read** |
| complexity | two container types + one recursive `wrap` | conversion layer both ways | trivial |
| S-2/S-3 fit | `thaw()` gives class C its plain structures | conversion needed anyway | natural |

Frozen storage was rejected because it breaks reader equality against lists and the geometry
code that consumes these values. Deep-copy-on-read was rejected because a silent no-op is a
worse failure mode than a refusal.

**Capability instead of a public gate.** `WriteCapability` is held in a **module-private
`WeakKeyDictionary` keyed by the state object** — not on the instance at all. A name-mangled
attribute was tried first and rejected: it is still discoverable through `dir()` and reachable
by its mangled name, which makes it private by convention rather than private. The capability
is also **type-checked** at every guard, so a duck-typed object exposing `open = True` cannot
unlock anything.

**Stored-family resolution.** Every operation targeting an existing entity now resolves the
entity by id, reads its **stored** `_family`, rejects a mismatch, and only then evaluates
ownership, extendability and field permission. Caller-supplied `entity_type` is never the
source of truth for an entity that already exists.

## 17.4 Files changed in this pass

| File | Change |
|---|---|
| `ver3/assy_v3/state/authority.py` | rewritten: `WriteCapability`, generated mutator closure, `GuardedDict`/`GuardedList`, `wrap()`, `thaw()`, `_is_granted()` |
| `ver3/assy_v3/state/design_state.py` | capability moved to a module-private registry; recursive wrapping on every write; `stored_family()` and `_family_problem()`; history appends routed through `_log` |
| `ver3/assy_v3/state/projection.py` | a view is thawed — class C must be plain and freely mutable |
| `ver3/tools/run_window2.py` | the three projection helpers thawed |
| `ver3/assy_v3/stages/s04_envelope_and_motion.py` | **2 lines**: import `thaw`, use it in the mechanism projection. No engineering reasoning, no prompt |
| `ver3/tests/state/test_authority_hardening.py` | **new** — 34 tests |
| `ver3/tests/meta/test_no_uncontrolled_authoritative_writes.py` | capability-name and `object.__setattr__` detection; scope restated as defence in depth |

## 17.5 Before / after

| Bypass | Before (`2570aa4`) | After |
|---|---|---|
| `rec["volume"]["centre"][0] = 999` | succeeded | `AuthorityViolation` |
| `rec["owning_bodies"].append(...)` | succeeded | `AuthorityViolation` |
| `state.entities.popitem()` | succeeded | `AuthorityViolation` |
| every enumerated dict/list mutator | six of eight closed at top level; none nested | **all closed, at every depth, on every container** |
| `EXTEND` with a spoofed `entity_type` | wrote the borrowed field | `FAMILY_MISMATCH`; the field never reaches the entity |
| `SUPERSEDE` / `INVALIDATE` family | unchecked | `FAMILY_MISMATCH` |
| caller mutates a list it passed to `CREATE` | state changed | state unchanged |
| caller mutates a value it passed to `SUPERSEDE` | state changed | state unchanged |
| mutating the retained prior value | succeeded | `AuthorityViolation` |
| `state._gate` | public attribute, replaceable | **no such attribute**; nothing on the state is the capability |
| `with state._gate.unlocked():` | supported bypass | no supported path; also flagged statically |
| duck-typed fake capability | n/a | rejected by type check |

## 17.6 Tests added

34 tests in `test_authority_hardening.py`: nested-value bypass (4), container mutator coverage
(6, including a systematic assertion that **no** enumerated mutator is inherited unguarded),
family spoofing (6), input aliasing (4), capability exposure (4), and **AUTH-01…AUTH-08**
mechanism-independent properties (10).

The mutator-coverage tests enumerate the dict and list mutation APIs and assert each is
overridden, rather than testing named methods — so the next omission is a failure, not a
discovery.

## 17.7 ADR-001 Level 1 — exact historical replay

**8/8 pass, unchanged in intent.** The historical payload still drives the current code; the
engineering facts still arrive; they arrive through controlled operations with provenance; the
old bypass is absent; premise binding still marks dependents `STALE` while leaving values
intact. No assertion requires a historical value to be correct.

## 17.8 ADR-001 Level 2 — generalized invariant

**64/64 pass**, now covering every class the brief names: top-level direct write · nested
in-place mutation · external alias mutation · entity-table mutator bypass · family-spoofed
mutation · capability exposure and forgery. Plus the static scan (3 tests), which now also
rejects external use of capability names and `object.__setattr__`.

## 17.9 Runtime guarantee — stated precisely

> **Within the repository's supported mutation interfaces, authoritative engineering state
> cannot be changed outside the controlled mutation boundary — including through nested
> mutable values, retained input references, inherited container mutators, and
> family-authority spoofing.**

Every mutating method of every authoritative container, at every depth, refuses unless a
genuine `WriteCapability` is open; the capability is granted only inside `DesignState.apply()`
and is held off the state object in a module-private registry.

## 17.10 Static-analysis guarantee — and its limit

**The AST scan is DEFENCE IN DEPTH, not proof of authority safety.** This is asserted in the
test module's own docstring so it cannot be misread later. It catches the audited shapes plus
capability misuse at review time. It does **not** perform alias analysis, and a write reaching
state through an alias built in another function is invisible to it — and is caught at runtime
instead.

## 17.11 Guarantee limitations — stated, not hidden

1. **Introspection is not prevented.** `object.__setattr__` on a container's private slot with
   a genuine `WriteCapability` **does** bypass the guard. This is repository-level
   architectural enforcement, not a security sandbox. **There is an executable test asserting
   this limit is real** — the limit is evidence, not a sentence that may quietly stop being
   true.
2. **`thaw()` is deliberately unguarded.** That is what class C means.
3. **A holder of a live reference sees later authorised changes**, since guarded containers are
   live views. That is correct — it is state, not a snapshot.
4. **Wrapping costs one traversal per write.** Reads are free.

## 17.12 Failure classification for this pass

| Failure | Class | Action |
|---|---|---|
| 22 of 23 reproduction tests failing at `2570aa4` | **(B) previously missed S-1 write bypass** | fixed in this pass |
| `test_a_forged_capability_does_not_open_a_guarded_container` still failing after the first fix | **(A) hardening implementation defect** — the test asserted more than the design could honestly guarantee | fixed both ways: a type check now genuinely closes duck-typed forgery, and the test was rewritten to assert the honest guarantee plus an explicit test of the real limit |
| view consumers meeting guarded nested values | **(C) read-compatibility break** | fixed by thawing views (§17.4) |
| `test_package_path.test_only_permitted_historical_occurrences_remain` | **(E) pre-existing** | unchanged from §12; still verified failing at HEAD, still not fixed here |

No **(G) frozen-architecture contradiction** arose. No **(F)** dependency on a later unit was
encountered.

## 17.13 Broad validation

| Suite | Result |
|---|---|
| `ver3/tests/state` | **69/69 OK** (27 model + 8 replay + 34 hardening) |
| `ver3/tests/meta` (311) | **310 pass, 1 pre-existing failure** |
| `ver3/tests/window` | **8/8 OK** |
| ADR-001 Level 1 | **8/8 OK** |
| ADR-001 Level 2 | **64/64 OK** |
| static authority scan | **3/3 OK**, clean over `assy_v3/`, `tools/`, `live_providers/` |
| all stage, tool and provider modules import | **OK** |

**No model call. No benchmark rerun.**

## 17.20 Revised S-1 claim

> **S-1 is COMPLETE**, in the stronger sense: *within the repository's supported mutation
> interfaces, authoritative engineering state cannot be changed outside the controlled
> mutation boundary, including by nested mutable values, retained input aliases, inherited
> container mutators, family-authority spoofing, or access to the write capability.*

The limits of that claim are stated in §17.11 and are covered by executable tests. No claim of
Python-language impossibility is made.

> **⚠ THIS CLAIM WAS ALSO TOO STRONG, AND IS SUPERSEDED BY §18.** The hardening pass had not
> defined "supported interface" explicitly, and by leaving base-class calls, storage-root
> assignment and capability attributes outside its own definition by omission, it certified an
> invariant it had not tested. Five bypasses using **ordinary operations only** remained. See
> §18.


---
---

# §18 FINAL AUTHORITY ENCAPSULATION CORRECTION

Third and final S-1 pass. Baseline `65ebe1a`. No architecture decision reopened, no later unit
begun, no contract, prompt, validator, fixture or benchmark changed, no model called. The
`2570aa4` and hardening evidence above is preserved unedited, including both overclaims.

## 18.1 The previous claim, and why it was wrong

§17.20 asserted that authoritative state could not be changed "within the repository's
supported mutation interfaces". **The pass never defined that phrase.** Without a definition,
three whole categories fell outside it by omission rather than by argument — and each was
reachable with ordinary Python.

**Why the previous tests missed them.** Every test asked *"does this raise?"* about operations
routed through the guard. None asked *"is there a way in that never reaches the guard?"* The
guarded-container design answers the first question exhaustively and the second not at all:

- storage **roots** were never tested, because guarding was about container contents;
- the **capability** was tested for public reachability on `DesignState` and, once moved to a
  registry, declared closed — while every guarded container still carried it in a `__slots__`
  attribute that ordinary `rec._cap` reads;
- **base-class calls** were never considered, because the mental model was "we overrode the
  mutators", and an override is only consulted by normal dispatch.

## 18.2 Bypasses reproduced against `65ebe1a`

All five with **ordinary operations only** — no `object.__setattr__`, no reflection.

| Bypass | Reproduction | Result at `65ebe1a` |
|---|---|---|
| **ROOT** | `state.entities = {}` · `state.by_family = {}` · `state.applied_patches = []` | succeeded; the entire authoritative table was replaced with an empty dict, with no operation, provenance or history |
| **CAP-02** | `cap = state.family(f)[0]._cap` → `with cap.granted(): rec["role"] = ...` | succeeded; a record obtained from the **public read API** handed out write authority for the whole state |
| **CAP-03** | `state.entities[eid]["volume"]._cap` | succeeded; every nested value carried it too |
| **CAP-04** | `rec._cap = <other>` | succeeded; ordinary assignment replaced the capability |
| **MUT-04/05** | `dict.__setitem__(rec, k, v)` · `dict.pop(rec, k)` · `list.append(nested, v)` · `dict.__setitem__(state.entities, ...)` | succeeded; base-class calls do not dispatch through an override |

## 18.3 The structural finding

> **A representation whose authoritative storage IS a builtin mutable container can always be
> mutated by an ordinary base-class call, no matter how completely its methods are
> overridden.** `dict.__setitem__(obj, k, v)` is documented Python that any module may write.

This is not an oversight in the guarded-container implementation; it is a property of the
approach. **The guarded-subclass design was therefore not fixable and was abandoned.**

## 18.4 Alternatives considered

| | **A: composition + encapsulated storage** *(selected)* | **B: capability-checked builtin subclasses** *(previous)* | **C: immutable external representation** |
|---|---|---|---|
| base-class bypass | **impossible** — no authoritative builtin is ever handed out | **unavoidable** | closed |
| capability discovery | **no capability exists** | present on every container | none needed |
| root replacement | closed by attribute taxonomy | orthogonal, was open | orthogonal |
| nested values | closed — reads are copies | required recursive guarding | closed |
| input aliasing | closed by copy-in | closed by wrap | closed |
| existing readers | **unchanged** — plain `dict`/`list` | unchanged | **breaks**: `tuple != list` in equality and geometry |
| serialization | unchanged | unchanged | round-trips differently |
| history / provenance | unchanged | unchanged | unchanged |
| S-2/S-3 fit | views are already plain | needed `thaw` | conversion both ways |
| complexity | **lowest** — the guard classes disappear | two container types + generated mutators + capability | conversion layer |
| cost | copy per read | wrap per write | one-time |

**Selected: A.** It is the only option that closes the base-class bypass *structurally* rather
than by policing, and it removes code rather than adding it.

## 18.5 Selected design

**Authoritative storage is owned by `DesignState` and never leaves it.** Internally: plain
dicts and lists. Externally:

- **`entities`** → a `ReadOnlyTable`, derived from `collections.abc.Mapping` — **not from
  `dict`** — so there is no inherited mutator and no base-class call that could reach the
  backing store. Its own mutators refuse with `UNCONTROLLED_WRITE` and the reason.
- **`family()`, `standing()`, `entities[id]`, `by_family`, `applied_patches`** → plain
  recursive copies the caller owns.
- **`copy_in`** on every write closes input aliasing; **`copy_out`** on every read closes
  reference-based mutation.
- **No capability object exists anywhere.** `WriteCapability`, `GuardedDict` and `GuardedList`
  are deleted. There is nothing to discover, replace or forge.

**Read semantics, stated plainly:** mutating a read result is **legal, ordinary, and
ineffective** — the semantics of `dict.copy()`, which every Python reader already understands.
It is not rejected. What matters is not that it raises but that authoritative state is
unreachable that way.

## 18.6 Storage-root protection — the §4 attribute taxonomy

| Class | Members | Rule |
|---|---|---|
| **INITIALIZATION-ONLY INTERNAL ROOT** | the three private storage roots, `run_id`, `c` | written once in `__init__`; `PROTECTED_ROOT` thereafter |
| **PUBLIC READ INTERFACE** | `entities`, `by_family`, `applied_patches` | properties; assignment is `PROTECTED_ROOT` |
| **DERIVED / EPHEMERAL** | *(none yet)* | declared when a later unit needs one; freely replaceable because not authoritative |
| **anything else** | — | `SIDE_CHANNEL_WRITE` |

`_SETTABLE_AFTER_INIT` is **empty**. `__delattr__` is refused. The previous broad whitelist —
which permitted replacing the authority container itself — is gone.

## 18.7 Final supported-interface matrix

Verified by executing each path against the implementation:

| ID | Path | Result |
|---|---|---|
| ROOT-01 | `state.entities = {}` | **SUPPORTED AND REJECTED** — `PROTECTED_ROOT` |
| ROOT-02 | `state.by_family = {}` / `applied_patches = []` | **SUPPORTED AND REJECTED** |
| CAP-01 | capability from `DesignState` | **does not exist** — `AttributeError` |
| CAP-02 | capability from a record | **does not exist** |
| CAP-03 | capability from a nested value | **does not exist** |
| CAP-04 | replace capability by assignment | **SUPPORTED AND REJECTED** |
| MUT-01 | `entities["X"] = {}` | **SUPPORTED AND REJECTED** |
| MUT-02 | nested mutation on a read record | **SUPPORTED AND SAFE** — acts on the caller's copy; state unchanged |
| MUT-03 | external alias mutation | **SUPPORTED AND SAFE** — state unchanged |
| MUT-04 | `dict.__setitem__(entities, …)` | **SUPPORTED AND REJECTED** — `TypeError`; the table is not a dict |
| MUT-04b | `dict.__setitem__(record, …)` | **SUPPORTED AND SAFE** — acts on the copy |
| MUT-05 | `list.append(nested, …)` | **SUPPORTED AND SAFE** — acts on the copy |
| MUT-06 | `del entities[id]` | **SUPPORTED AND REJECTED** |
| READ-01 | mutate a `family()` / `standing()` / `counts()` result | **SUPPORTED AND SAFE** — state unchanged |
| AUTH-01 | family-spoofed controlled mutation | **SUPPORTED AND REJECTED** — `FAMILY_MISMATCH` |
| AUTH-02 | legitimate `apply()` | **SUPPORTED AND SAFE** — works, with full history |
| AUTH-03 | supersede/invalidate propagation | **SUPPORTED AND SAFE** — dependents go `STALE` |
| EXCL-01 | `getattr(state, "_DesignState__entities")` then mutate | **OUTSIDE THE GUARANTEE** — reflection; **state does change** |

**No path was moved into "outside the guarantee" to make a test pass.** The single excluded
row is reading another object's name-mangled private storage, which is deliberately
implementation-breaking rather than an operation a normal module would perform on something it
was handed. It has its own executable test so the exclusion cannot quietly become untrue.

## 18.8 Supported interface — the definition now written down

**Included:** attribute lookup · attribute assignment · method invocation on returned objects ·
**base-class Python-callable mutation APIs**. Base-class calls are inside the contract because
they are ordinary documented Python; excluding them by omission is what left the hole.

**Excluded:** reading another object's name-mangled private attribute · `object.__setattr__`
against internals · `ctypes` / memory mutation · monkey-patching interpreter internals.
Excluded because they are deliberately implementation-breaking, **not because they are hard**.

## 18.9 Files changed

| File | Change |
|---|---|
| `ver3/assy_v3/state/authority.py` | rewritten: `copy_in`/`copy_out`/`thaw`, `ReadOnlyTable`. `WriteCapability`, `GuardedDict`, `GuardedList` **deleted** |
| `ver3/assy_v3/state/design_state.py` | private storage roots; `entities`/`by_family`/`applied_patches` as read-only properties; §4 attribute taxonomy in `__setattr__`/`__delattr__`; copy-in on write, copy-out on read; capability removed from `apply()` |
| `ver3/tests/state/test_authority_hardening.py` | rewritten to the matrix — 26 tests |
| `ver3/tests/state/test_authority_model.py` | three tests re-expressed from the retired mechanism to the invariant; root-protection tests added |
| `ver3/tests/state/test_absorb_writepath_replay.py` | one test re-expressed the same way |
| `ver3/tests/meta/test_no_uncontrolled_authoritative_writes.py` | protected-root assignment and reflective-handle detection; scope restated |

`projection.py`, `run_window2.py` and `s04_envelope_and_motion.py` needed **no further change**
— `thaw` is retained as an alias of `copy_out`, so the read-compatibility edits from the
previous pass remain correct.

## 18.10 Runtime guarantee

> **Repository code using ordinary interfaces cannot replace an authoritative storage root,
> acquire or replace write authority, mutate authoritative state through a reference a read
> returned, bypass through an ordinary container interface including base-class calls, or
> otherwise change authoritative engineering state except through
> `DesignState.apply(StagePatch)`.**

## 18.11 Static-analysis guarantee

Unchanged in kind and restated in the module's own docstring: **enforcement is encapsulation;
the scan is early warning.** It now also flags protected-root assignment and reflective
handles on internal storage. It does not, and does not claim to, prove the absence of Python
aliasing or reflection.

## 18.12 Residual limitation

**One, and it is the excluded region:** reflection against internal storage — reading a
name-mangled private attribute, `object.__setattr__`, `ctypes`, monkey-patching. `EXCL-01`
demonstrates it changes state, deliberately. This is repository-level architectural
enforcement, not a security sandbox.

Two consequences of the design, neither a defect: reads cost a copy (state is small; suites
run in seconds), and a read is a **snapshot**, not a live view — a caller wanting current
values re-reads.

## 18.13 Failure classification

| Failure | Class | Action |
|---|---|---|
| 5 bypass classes open at `65ebe1a` | **(B) supported bypass still open** | fixed |
| 3 tests asserting `AuthorityViolation` on a returned record | **(A) encapsulation implementation** — they encoded the retired mechanism, not the invariant | re-expressed to assert state is unchanged, which is stronger and mechanism-independent |
| capability-name scan matching `_propagate` and `str.capitalize` | **(A)** | token-bounded regex |
| `test_package_path` | **(E) pre-existing** | unchanged; still not fixed here |

No **(C) reader-compatibility break** arose — readers get plain structures. No **(D)
controlled-mutation regression** — all four operations, provenance, history, premise
propagation and family validation pass unchanged. No **(F)**. No **(G) frozen-architecture
contradiction**.

## 18.14 Broad validation

| Suite | Result |
|---|---|
| `ver3/tests/state` | **62/62 OK** |
| `ver3/tests/meta` (312) | **311 pass, 1 pre-existing failure** |
| `ver3/tests/window` | **8/8 OK** |
| ADR-001 Level 1 | **8/8 OK** |
| ADR-001 Level 2 | **58/58 OK** |
| static scan | **4/4 OK** |
| all stage, tool and provider modules import | **OK** |

## 18.20 Final S-1 status

Against the sixteen completion criteria: `_absorb` remains resolved (1); nested values,
aliases and container mutators cannot reach state (2, 3, 4); storage roots are not replaceable
(5); no write authority exists to acquire or replace (6); base-class APIs cannot reach storage
(7); family authority comes from stored identity (8); the four operations, provenance, history
and premise propagation are unchanged (9, 10); reads remain usable without conferring write
authority (11); the scan is defence in depth only (12); both ADR-001 levels pass (13, 14); and
the one residual bypass requires explicitly excluded reflection (15).

> **S-1 is COMPLETE.**

The supported interface was defined **before** the matrix was evaluated, and no path was moved
across that line to reach this result.
