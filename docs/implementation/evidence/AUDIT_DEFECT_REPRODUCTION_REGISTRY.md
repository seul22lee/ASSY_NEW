# AUDIT DEFECT REPRODUCTION REGISTRY

Reproducible failure **mechanisms** established by the frozen audit (P4A/P5/P6), preserved so
that each implementation step can be tested against the path that produced the defect.

**This is not a benchmark expected-answer file.** Every entry describes a general mechanism.
The historical case is retained as *reproduction substrate* — the input that drives the path —
never as an answer template.

> **The distinction that governs every entry.**
> **BAD:** *"the three pivots must equal the old coordinates."*
> **GOOD:** *"if an upstream stage made an authoritative spatial commitment, the downstream
> stage must receive it and may not silently contradict it."*

**Three levels of evidence, never conflated:**

| Level | Question | What it establishes |
|---|---|---|
| **1 — exact replay** | does the historical path still produce the defect? | one known mechanism is gone |
| **2 — general invariant** | is the architectural mechanism that permitted it eliminated? | it cannot return under another name |
| **3 — live generalization** | does the live pipeline behave on unseen inputs? | **not** implied by 1 or 2 |

**Replay types:** `STRUCTURAL` (no model) · `DETERMINISTIC` (deterministic path only) ·
`STORED-STATE REPLAY` (rebuild consumer/check from saved state) · `MODEL REPLAY` (model
reasoning is part of the causal mechanism) · `LIVE END-TO-END`.

Use the cheapest replay that actually tests the mechanism. A defect in state mutation,
projection, deterministic derivation or evaluator logic is replayed at that layer; adding
model variability to such a test only weakens the evidence.

**Status vocabulary:** `NOT_YET_ADDRESSABLE` · `READY_TO_REPLAY` · `RESOLVED` ·
`STILL_FAILING` · `SUPERSEDED_BY_BETTER_TEST`. **`RESOLVED` requires replay evidence.**

---

## Index

| ID | Mechanism | Step | Replay type | Status |
|---|---|---|---|---|
| **ADR-001** | uncontrolled authoritative write / side-channel engineering fact | **S-1** | STRUCTURAL | **RESOLVED** — L1 at `2570aa4`; L2 took **four** passes (see the history) |
| ADR-002 | consumer-view omission of a required premise | S-3 | STORED-STATE REPLAY | NOT_YET_ADDRESSABLE |
| ADR-003 | S04A→S04B spatial commitment loss | S-6 | STORED-STATE REPLAY | NOT_YET_ADDRESSABLE |
| ADR-004 | silent positional context truncation | S-3 | STRUCTURAL | NOT_YET_ADDRESSABLE |
| ADR-005 | unsupported mobility completion from absence | S-5 | DETERMINISTIC | NOT_YET_ADDRESSABLE |
| ADR-006 | non-addressable blocking relation reference | S-4 | STRUCTURAL | NOT_YET_ADDRESSABLE |
| ADR-007 | state name without physical realization | S-6 | STORED-STATE REPLAY | NOT_YET_ADDRESSABLE |
| ADR-008 | transition without motion evidence | S-6 | DETERMINISTIC | NOT_YET_ADDRESSABLE |
| ADR-009 | unresolved recognised, commitment unaffected | S-7 | STORED-STATE REPLAY | NOT_YET_ADDRESSABLE |
| ADR-010 | self-fulfilling assurance | S-8 | DETERMINISTIC | NOT_YET_ADDRESSABLE |
| ADR-011 | spatial incidence observable but unchecked | S-8 | STORED-STATE REPLAY | NOT_YET_ADDRESSABLE |
| **ADR-012** | live contract backing mutable through supported access | **S-2** | STRUCTURAL | **RESOLVED** |
| **ADR-013** | non-authoritative contract file contradicts canonical semantics undeclared | **S-2** | STRUCTURAL | **RESOLVED** |

---

## ADR-001 — Uncontrolled authoritative write and side-channel engineering fact

**Status: RESOLVED** — Level 1 and Level 2 both established. Level 2 was claimed three times
before it was true; the history below records why, because that is the useful part.

| | |
|---|---|
| **General mechanism** | A runner or helper writes an authoritative engineering fact into accumulated state without an operation, ownership check, validation or provenance — or parks it as an attribute on the state object, where it has no identity and nothing can read it. Nothing in the system can detect either. |
| **Original observation** | `_absorb()` assigned three spatial commitments directly into entity dicts, and set three engineering conclusions as bare attributes. Confirmed as the only such path in the corpus; every other mutation went through `state.apply(patch)`. |
| **Original case / artifact** | The Window-2 runner, on every case and trial it ran. Not case-specific. |
| **Original causal path** | `run_window2.run_case` → `state.apply(out.patch)` → `_absorb(state, key, raw)` → `state.entities[id][field] = value` and `state.s04a_reach / s04a_elimination / s04a_scale = ...` |
| **Original evidence anchors** | `P4B_FINAL_SYNTHESIS.md` §2 (the unguarded write); `P5_COMPLETE.md` §14; plan §9 write-path inventory. Fields: `FunctionalRegion.volume`, `AssemblyStep.insertion_direction`, `Joint.frame_origin`. Attributes: `s04a_reach`, `s04a_elimination`, `s04a_scale` — **write-only; nothing in the repository read them.** |
| **Minimum reproduction input** | `replays/ADR-001_absorb_writepath.json` (3.2 kB) — the exact s04a/s04b payload fragments `_absorb` consumed, copied verbatim, plus the entity ids they refer to. |
| **Replay type** | **STRUCTURAL.** No model call. The defect was in state mutation, so the replay drives state mutation. |
| **Expected post-fix property** | Every class-A engineering fact enters accumulated state through `CREATE` / `EXTEND` / `SUPERSEDE` / `INVALIDATE` carried by a validated patch, with provenance and an owner. An engineering conclusion has an identity. |
| **Forbidden post-fix condition** | Any assignment into an entity record, entity table, or state attribute that places a class-A fact into state without an operation and provenance — **under any function name.** |
| **Responsible step** | **S-1** (U-1 + U-2A + U-4) |

### Before / after

| | Before | After |
|---|---|---|
| **path** | `_absorb` → `e["volume"] = {...}` | `_commit_s04` → `Op("EXTEND", …, provenance=…)` → `state.validate` → `state.apply` |
| **operation** | none | `EXTEND` (fields) / `CREATE` (conclusions) |
| **ownership** | unchecked | `s04` must be the declared extending stage; refused otherwise |
| **validation** | none | full contract validation; a rejected patch changes nothing |
| **provenance** | none | per act — creating, extending and revising authors all retained |
| **`s04a_reach`** | `state.s04a_reach = [...]`, unreadable | `ReachResult` entities with ids, owner and provenance |
| **`s04a_elimination`** | `state.s04a_elimination = {...}` | `EliminationRecord` entity |
| **`s04a_scale`** | `state.s04a_scale = {...}` | `ReferenceScale` entity, recorded as the **premise** of every coordinate expressed in it |
| **unresolvable target** | `if e is not None` — silently skipped | still not committed, but recorded in `rec["<pass>_uncommitted"]` |

**Cause removed.** The write path no longer exists, and re-creating it cannot work: the entity
table is a read-only mapping that refuses every mutator, a record obtained by reading is a
plain copy the caller owns, and `DesignState.__setattr__` refuses both side-channel attributes
and any attempt to replace a storage root. *(Superseded in mechanism by the third pass below;
the property is unchanged and now holds against a wider interface.)*

### Evidence

**Level 1 — exact replay.** `ver3/tests/state/test_absorb_writepath_replay.py`, driven by the
historical payload:

- the historical direct write raises `UNCONTROLLED_WRITE`;
- each of the three historical side-channel assignments raises `SIDE_CHANNEL_WRITE`;
- `_absorb` is absent from the module (gone, not renamed);
- **the same facts still reach authoritative state** — a boundary that silently dropped the
  engineering fact would be a regression, not a fix;
- they arrive with a recorded `EXTEND`, the right stage and non-empty provenance;
- reach / elimination / scale are addressable entities with owners and provenance;
- withdrawing the reference scale marks every dependent coordinate `STALE` while leaving its
  value untouched (FA-5, FA-1);
- an unresolvable target is recorded rather than silently dropped.

**No assertion in that file requires any historical coordinate, direction or verdict to be
correct.** Every assertion is about the path a value takes, and holds identically for an
unseen problem.

**Level 2 — general invariant.** `ver3/tests/meta/test_no_uncontrolled_authoritative_writes.py`
(AST scan of `assy_v3/`, `tools/`, `live_providers/` for both defect shapes, plus a
self-test that feeds it the historical code and confirms it fires) and
`ver3/tests/state/test_authority_model.py` (35 tests over the model itself).

**Level 3 — live generalization.** *Not established, and not claimed.* S-1 is structural. A
live claim requires S-9.

### Resolution history — why Level 2 took two passes

**This entry is kept in two stages deliberately.** The first pass looked resolved and was not,
and that is worth preserving: it is the concrete example of why the registry requires a general
invariant alongside an exact replay.

| Pass | Claim supported | What it missed |
|---|---|---|
| **Initial S-1** (`2570aa4`) | *Level 1:* the historical `_absorb` path is gone; the facts arrive through controlled operations with provenance | *Level 2 was overstated.* Guarding covered the **top level only** |
| **Hardening** | *Level 2:* authoritative mutation is impossible outside the boundary through any supported interface | — |

**Five bypass classes were executable after the initial pass**, each reproduced by a failing
test before any fix (22 of 23 failed):

| | Bypass | Evidence |
|---|---|---|
| **A** | nested value mutation — `rec["volume"]["centre"][0] = 999` changed an authoritative spatial commitment with no patch, provenance, history or propagation | the outer record was guarded; its contents were plain dicts and lists |
| **B** | `state.entities.popitem()` removed an entity silently — mutators were hand-listed and one was missed | six of eight dict mutators closed at the top level; none at any depth |
| **C** | family-authority spoofing — a declared `entity_type` borrowed another family's field permission; `SUPERSEDE`/`INVALIDATE` checked family not at all | permission was looked up from the caller's assertion, not the stored entity |
| **D** | input aliasing — a caller that kept the list it passed to an operation could mutate stored state afterwards, including the value `SUPERSEDE` retained | values were stored by reference |
| **E** | `with state._gate.unlocked():` was a supported one-line bypass, and the gate was replaceable | the capability was a public attribute holding a public boolean |

**After hardening.** Values are recursively guarded at every depth; every mutating method of
the dict and list APIs is generated-closed rather than hand-listed; operations resolve the
**stored** family before evaluating any permission; wrapping constructs new containers so
input aliasing is closed by the same mechanism; and the write capability is held in a
module-private registry with a type check, so nothing on a state object is the capability and
a duck-typed forgery cannot open one.

**Post-fix evidence.** Level 1: 8/8 unchanged in intent. Level 2: 64/64, covering top-level
write, nested mutation, alias mutation, container-mutator bypass, family spoofing and
capability exposure. Static scan: 3/3, now also rejecting capability names and
`object.__setattr__` outside the state package — **as defence in depth, explicitly not as
proof of authority safety.**

**Documented limit, with an executable test.** `object.__setattr__` on a container's private
slot with a genuine capability still bypasses the guard.

### Third pass — authority encapsulation *(final)*

**The hardening claim was also too strong, and for an instructive reason: it asserted a
guarantee over "supported mutation interfaces" without ever defining that phrase.** Three
categories fell outside it by omission rather than by argument, and each was reachable with
**ordinary operations only** — no reflection:

| | Bypass at `65ebe1a` | Why the previous tests missed it |
|---|---|---|
| **ROOT** | `state.entities = {}` replaced the whole authoritative table | every test asked "does this mutation raise?"; none asked "can the container be swapped out?" |
| **CAP** | `state.family(f)[0]._cap` handed write authority to any caller, from the **public read API**; and `rec._cap = other` replaced it | the capability had been checked for reachability on `DesignState` and declared closed, while every container still carried it in an ordinary attribute |
| **BASE** | `dict.__setitem__(rec, k, v)`, `list.append(nested, v)` | an override is only consulted by normal dispatch; base-class calls were never in the mental model |

**The structural finding.** A representation whose authoritative storage *is* a builtin mutable
container can always be mutated by an ordinary base-class call, however completely its methods
are overridden. The guarded-subclass approach was therefore **not fixable** and was abandoned.

**Final design — encapsulation.** Authoritative storage is owned by `DesignState` and never
leaves it. The entity table is exposed as a `Mapping` (not a `dict`, so no inherited mutator
exists); every read returns a plain recursive copy; `copy_in` on write closes input aliasing.
Storage roots are write-once. **No capability object exists at all** — `WriteCapability`,
`GuardedDict` and `GuardedList` were deleted, which is the rare fix that removes code.

**Level-2 evidence.** An 18-row supported-interface matrix, each row executed: ROOT, CAP and
MUT rows are *supported and rejected* or *supported and safe (acts on the caller's copy)*;
AUTH rows confirm controlled mutation still works. **One row is outside the guarantee** —
reflection against name-mangled internal storage — and it carries its own executable test.
The supported interface was defined **before** the matrix was evaluated, and no path was moved
across that line to reach the result.

### Fourth pass — read-wrapper and internal-mutator encapsulation *(final)*

The encapsulation redesign was correct in representation and was verified against a matrix it
wrote itself. Two supported paths were not on that list, and both were reachable with
**ordinary operations only**:

| | Bypass at `14bed10` | Why it survived |
|---|---|---|
| **live backing** | `state.entities._backing["FRG-0001"]["role"] = "BYPASS"` changed authoritative state | the wrapper was read-only but **not detached** - it held the live store in an ordinary attribute, so a read-only wrapper around a live mutable object handed the caller exactly what it was protecting |
| **internal writers** | `state._create(patch, op)` placed an entity **with no validation and `_provenance: None`** | the primitives were still ordinary methods; single-underscore is a naming convention, and the pass's own definition counted ordinary method invocation as supported |

**Correction.** One change of shape applied to both: nothing that can reach storage is an
attribute of anything a caller holds. `ReadOnlyTable` holds a snapshot; the mutation primitives
moved to module-private functions taking the store explicitly; and the store itself moved off
the instance into a module-private registry — which also closed the path the new object-graph
test found next, since a name-mangled attribute is still reachable through `dir()` plus
`getattr`. A convenience property added during the fix (`state._s`) leaked storage again and was
caught by that same invariant within minutes, which is the intended behaviour of the test.

**Level-2 evidence.** An object-graph traversal from the whole supported read surface asserts no
path yields the live store, a capability, or a callable authoritative writer other than
`apply`; a companion test calls every public callable and confirms only `apply` moves the state
hash. Expanded Level 2: 65/65. Level 1 unchanged: 8/8.

**What the four passes together show.** An exact replay establishes that one path is closed. A
general invariant is only as strong as the interface definition it is tested against — and
then only as strong as the *enumeration* it is tested with. Three successive claims were true
of everything their authors thought to list. The durable fixes were the ones that removed the
category (no capability exists; no authoritative container is handed out; no storage-bearing
attribute exists) rather than the ones that policed it. That is the lesson this entry preserves
for ADR-002…ADR-011.

---

## Pre-registered mechanisms — later steps

Registered from the frozen audit. **No fix is implemented for any of these in S-1**, and none
is a new finding.

### ADR-002 — Consumer-view omission of a required premise

| | |
|---|---|
| **Mechanism** | An authoritative fact exists in accumulated state; the view built for the consuming stage omits a semantic dependency or reasoning premise the stage's decision requires. The stage then reasons without it, and nothing records that it was missing. |
| **Original observation** | Quantities constraining extent were present in state and absent from the s04 view; the projection boundary was one hand-written family tuple. |
| **Causal path** | `run_window2.S03_OWNED` (a literal tuple omitting `Requirement`, `LoadCase`, `Envelope`) → `mechanism_projection` → stage prompt. |
| **Anchors** | `P4B` C-05, C-12; `P5_COMPLETE.md` §20. |
| **Reproduction input** | A saved DesignState carrying an authoritative quantity, plus the consuming stage's declared minimum. |
| **Replay type** | STORED-STATE REPLAY — no model needed to show the view omits a class the contract requires. |
| **Expected post-fix property** | Every representational dependency and reasoning premise class derived from the two contracts is present in the view, or the run records an attributable insufficiency. |
| **Forbidden post-fix condition** | A required class present in accumulated state and absent from the view, with no finding. |
| **Step / status** | **S-3** · NOT_YET_ADDRESSABLE |

### ADR-003 — S04A→S04B spatial commitment loss

| | |
|---|---|
| **Mechanism** | An earlier pass makes an authoritative spatial commitment; the later pass that must extend it does not receive it, and re-derives geometry from nothing. |
| **Original observation** | S04B was instructed to place joints "in the same coordinates as the arrangement you were given" while the arrangement was in 0 of 6 prompts. |
| **Causal path** | `S03_OWNED` excludes `Envelope` → projection → s04b prompt. |
| **Anchors** | `P4B` C-12, C-13; `P5_COMPLETE.md` §20. |
| **Reproduction input** | A saved state with an S04A arrangement plus the S04B view built from it. |
| **Replay type** | STORED-STATE REPLAY. |
| **Expected post-fix property** | If an earlier pass made an authoritative spatial commitment that a later pass consumes, the later pass receives it and may not silently contradict it; a change must use the permitted supersession semantics. **The S-1 substrate for this exists** — `SUPERSEDE` retains both values with a reason, and premise change propagates — but the S04 refinement semantics that use it are S-6. |
| **Forbidden post-fix condition** | A downstream spatial value contradicting a binding upstream commitment with no supersession record. |
| **Step / status** | **S-6** · NOT_YET_ADDRESSABLE |

### ADR-004 — Silent positional context truncation

| | |
|---|---|
| **Mechanism** | A required semantic fact exists in the view and is removed by a fixed character slice applied at serialization, leaving no record. |
| **Original observation** | `json.dumps(obj, indent=1, sort_keys=True)[:26000]`; `RigidGroup` sorts last and fell beyond the slice in four of six s04b prompts. |
| **Causal path** | `s04_envelope_and_motion._render` → positional slice → prompt. |
| **Anchors** | `P4B` §8.2 *(note: grid size alone does not explain truncation — a 48-cell case truncated while two others did not; the sole-cause claim was withdrawn)*. |
| **Reproduction input** | Any view exceeding the budget. Mechanism-independent. |
| **Replay type** | STRUCTURAL. |
| **Expected post-fix property** | Reduction is semantic and recorded; required classes are never dropped; an unsatisfiable budget is a recorded condition. |
| **Forbidden post-fix condition** | Any positional slice of a serialized view. |
| **Step / status** | **S-3** · NOT_YET_ADDRESSABLE |

### ADR-005 — Unsupported mobility completion from absence

| | |
|---|---|
| **Mechanism** | A deterministic derivation, finding no premise for a cell of an enumerated domain, emits a positive engineering assertion instead of recording that nothing is known. |
| **Original observation** | The fallback branch wrote `MAINTAINED_BY_CLASS` with a holding class composed from the first joint of the group, or the literal string `"joint class of no joint"` when there was none. A check then validated the totality the same code guarantees. |
| **Causal path** | `s03_topology_and_mobility.derive_mobility` terminal `else` branch → patch → `dof_totality_check`. |
| **Anchors** | `P4B` §1 item 4, C-11, C-18. |
| **Reproduction input** | Groups, configurations and joints with at least one DOF cell covered by no relation and no authored irrelevance. Synthetic; no case needed. |
| **Replay type** | DETERMINISTIC. |
| **Expected post-fix property** | A cell with no covering premise is `UNDISPOSITIONED` and names what is missing. Disposition completeness is reported as a quantity; domain totality is reported as BOOKKEEPING and contributes to no establishment claim. |
| **Forbidden post-fix condition** | Any positive disposition whose premise does not resolve. |
| **Step / status** | **S-5** · NOT_YET_ADDRESSABLE |

### ADR-006 — Non-addressable blocking relation reference

| | |
|---|---|
| **Mechanism** | A derived conclusion refers to a relation that has no addressable entity, so the reference cannot be resolved, checked, or reasoned about. |
| **Original observation** | `blocked_by` was a nested structure inside another entity, with no id. "Is this DOF constrained?" and "what constrains it?" could not be answered separately. |
| **Anchors** | `P4B` C-10; R-10. |
| **Reproduction input** | A disposition citing a blocking relation. |
| **Replay type** | STRUCTURAL — reference resolution needs no model. |
| **Expected post-fix property** | Every relation the architecture treats as first-class has an id that resolves; an unresolvable reference refuses the patch. **The S-1 substrate exists** (`DANGLING_PREMISE` is refused, and stored-family resolution now prevents one family's permissions being used on another's entity); the `ConstraintRelation` family itself is S-4. |
| **Forbidden post-fix condition** | A conclusion citing a relation that is not an addressable entity. |
| **Step / status** | **S-4** · NOT_YET_ADDRESSABLE |

### ADR-007 — State name without physical realization

| | |
|---|---|
| **Mechanism** | Two named configurations exist and the physical variables that are supposed to distinguish them do not differ. The names carry the distinction; the representation does not. |
| **Original observation** | A configuration coordinate that had to change did not, in identifiable cases. |
| **Anchors** | `P4B` C-17; R-4. |
| **Reproduction input** | A saved state with two configurations and their realized coordinates. |
| **Replay type** | STORED-STATE REPLAY. |
| **Expected post-fix property** | Each configuration carries a distinguishing basis, and two configurations sharing one must differ in at least one of its coordinates. |
| **Forbidden post-fix condition** | Two named configurations identical on their declared distinguishing basis, with no finding. |
| **Step / status** | **S-6** · NOT_YET_ADDRESSABLE |

### ADR-008 — Transition without motion evidence

| | |
|---|---|
| **Mechanism** | A behaviour is asserted and the representation does not establish that the variable it depends on changes; the sampling *declaration* is produced from a constant rather than from the computation performed. |
| **Original observation** | `sampling_declaration` written from `SAMPLES = 9`, then validated by a check testing the property that constant guarantees. |
| **Causal path** | `s04_envelope_and_motion.S04BPlacementAndMotion.to_operations` → constant → check. |
| **Anchors** | `P4B` §1 items 4–5, C-18. |
| **Reproduction input** | Any transition and its path representation. Synthetic. |
| **Replay type** | DETERMINISTIC. |
| **Expected post-fix property** | A motion evidence level is a function of the computation actually performed and is recorded with its result; a transition declares the coordinates that change and the realization changes them. |
| **Forbidden post-fix condition** | An evidence level derivable from a constant rather than from a computation. |
| **Step / status** | **S-6** · NOT_YET_ADDRESSABLE |

### ADR-009 — Unresolved recognised, commitment unaffected

| | |
|---|---|
| **Mechanism** | The producer records an unresolved item that correctly names the defect the same artifact commits, and the commitment proceeds unchanged because nothing consumes the unresolved layer. |
| **Original observation** | `UnresolvedDecision` entries naming the exact defect committed in the same file, in multiple cases. No check, gate or stage reads the family. |
| **Anchors** | `P4B` §1 item 7, §11, C-20; R-8. *(Conditional: this is not a claim that the model always recognises its own errors.)* |
| **Reproduction input** | A saved state with an unresolved item naming a fact class a consumer's minimum marks required. |
| **Replay type** | STORED-STATE REPLAY. |
| **Expected post-fix property** | An unresolved item blocks exactly when it names a fact class the next consumer's or gate's required minimum marks required. Not every open item blocks. |
| **Forbidden post-fix condition** | A commitment made over a blocking unresolved item, with no `FALSE_ACCEPTANCE`. |
| **Step / status** | **S-7** · NOT_YET_ADDRESSABLE |

### ADR-010 — Self-fulfilling assurance

| | |
|---|---|
| **Mechanism** | A deterministic producer guarantees a property by construction; an evaluator then checks that property and reports engineering validity. |
| **Original observation** | Two confirmed instances: the DOF totality check against a deterministic enumerator, and the sampling check against a constant-written declaration. |
| **Anchors** | `P6_COMPLETE.md` §7; `P4B` §1 item 5, C-11, C-18; R-7. |
| **Reproduction input** | The producer and the check. Synthetic. |
| **Replay type** | DETERMINISTIC. |
| **Expected post-fix property** | Every check declares an independence degree and a claim class; only ENGINEERING CONSEQUENCE may contribute to `ENGINEERING_ESTABLISHED`; no check is reachable from a stage module. |
| **Forbidden post-fix condition** | A check whose passing is guaranteed by the producer of its input contributing to an establishment claim. |
| **Step / status** | **S-8** · NOT_YET_ADDRESSABLE |

### ADR-011 — Spatial incidence observable but unchecked

| | |
|---|---|
| **Mechanism** | The stored state contains everything needed to observe a defect, and the evaluator checks a different property, so the defect passes. |
| **Original observation** | Evaluator misses where the coordinates required to observe the defect were already in state. |
| **Anchors** | `P6_COMPLETE.md` §5 (FN-3/4/5/6 — establishable from the current representation, distinct from FN-12 which was not). |
| **Reproduction input** | A saved state with placements and the topology premises they must satisfy. |
| **Replay type** | STORED-STATE REPLAY. |
| **Expected post-fix property** | Where upstream topology establishes that two kinematic sites must be distinct for a mechanical relationship to exist, spatial realization must establish that the required distinctness is preserved. **Conditional on a declared premise — never "all joint pairs must differ".** |
| **Forbidden post-fix condition** | A declared required-distinctness violated by the realization, with no finding. |
| **Step / status** | **S-8** · NOT_YET_ADDRESSABLE |

---

## Maintenance rules

1. **`RESOLVED` requires replay evidence.** Not a passing test count; the actual before/after
   path.
2. **Replay at the earliest valid step.** If a structural replay can establish the fix at S-3,
   it is not deferred to S-9.
3. **Every replayed defect is paired with a general invariant.** Exact replay alone proves one
   mechanism is gone, not that it cannot return under another name.
4. **Never promote a historical output to an expected answer.** If an entry's test starts
   asserting a historical value, it has become an answer template and must be rewritten.
5. **Register only mechanisms the frozen audit established.** This registry does not create
   findings.


---

## ADR-012 — Live contract backing mutable through supported access

**Status: RESOLVED** *(S-2 closure)*

| | |
|---|---|
| **General mechanism** | The rules that decide what a mutation may do are held in an object the governed code can reach and edit. Authoritative state is never touched, so no authority check fires — but every later ownership, extendability, reference and authorization query observes the edited rule. |
| **Original observation** | `Contracts` stored the loaded documents in an ordinary attribute. `c._docs["families"][F]["owned_by"] = "s99"` succeeded, and `owner_of`, `extendable_fields`, `may_create` and `authority_class` all changed with it. The S-2 immutability claim was therefore false as implemented: public accessors returned copies while the backing stayed reachable. |
| **Anchors** | S-1 §19.11 deferred contract mutability to U-2B; S-2 implemented copy-on-read but not encapsulation. |
| **Reproduction input** | A loaded `Contracts` object. No case, no state, no model. |
| **Replay type** | **STRUCTURAL.** |
| **Expected post-fix property** | Loaded authoritative contract semantics cannot be modified through supported repository object access. |
| **Forbidden post-fix condition** | Any object reachable from `Contracts` whose mutation changes a later authorization answer. |
| **Step** | **S-2 closure** |

**Before / after.** Before: `c._docs` reachable; four authorization queries changed. After: the
documents live in a module-private registry keyed by the object, exactly the shape of fix that
closed the DesignState read surface at S-1; `hasattr(c, "_docs")` is false, mutating any read
changes no query, and every root refuses replacement with `IMMUTABLE_CONTRACT`.

**Level 1** — the reproduction, replayed: `CLOSURE-08` mutates a read and asserts four
authorization answers are unchanged. **Level 2** — the general invariant: a traversal of the
whole public `Contracts` surface asserts no attribute is the live store, and legitimate
queries still work.

---

## ADR-013 — Undeclared second semantic authority

**Status: RESOLVED** *(S-2 closure)*

| | |
|---|---|
| **General mechanism** | A file that is not the source of truth states a canonical semantic fact, and nothing marks it as a projection or as a description of legacy behaviour. Readers cannot tell whether it is authoritative, and it can drift from the source silently. |
| **Original observation** | Three instances, all found by a corpus-wide check rather than by name: **(a)** `S02_CONTRACT` claimed to create `PhysicalInteraction`, which s03 owns — an artefact of the S-2 hypothesis-family rename; **(b)** `S01_CONTRACT` claimed to create `SystemBoundary`, a family defined nowhere, when the boundary is a required FIELD of `Scenario`; **(c)** retired relation names and superseded field spellings sat in sections carrying no legacy marking. |
| **Anchors** | `CONTRACT_AUTHORITY.yaml`; the S-2 canonical corpus. |
| **Reproduction input** | The contract corpus. Structural. |
| **Replay type** | **STRUCTURAL.** |
| **Expected post-fix property** | Every semantic section of every stage contract declares its authority class — CANONICAL_PROJECTION, LEGACY_PRODUCER, OPERATIONAL or RETIRED — with no ambiguous fourth state; projections match their source; legacy sections name a replacement and a scheduled step. |
| **Forbidden post-fix condition** | A stage contract asserting canonical ownership, a field name or a relation meaning that the source of truth does not, without declaring itself legacy. |
| **Step** | **S-2 closure** |

**Before / after.** Before: seven stage files, none declaring authority status; two false
ownership claims; retired vocabulary indistinguishable from current meaning. After: 7/7 files
classified across 63 sections; both false claims corrected against the canonical source; legacy
vocabulary moved into explicitly legacy sections that name their replacement and step.

**Level 1** — the two ownership contradictions are the exact replay, and `CLOSURE-03` fails on
either if reintroduced. **Level 2** — `CLOSURE-01/02/04/05/06/07/09/10` are data-driven over
the whole `contracts/stages/*.yaml` corpus, so a new stage file, or a new alias in an old one,
is caught the same way rather than by name.

**Note on honesty.** The fix did **not** rewrite legacy sections to claim conformance. s03
still emits `blocked_by`/`retained_by` and does not yet emit `ConstraintRelation` or
`PhysicalInteraction`; that gap is now stated in a `current_producer` block with its migration
step, because weakening the canonical contract to match the producer would carry the audited
defect forward under a new name.
