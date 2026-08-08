# Package 1 — COMPLETE

All 22 files read start-to-end in this session. This document records what was
read, the intended architecture reconstructed from the complete corpus, and the
places where the documents disagree with each other or with the repository.

**No fixes are proposed. Nothing was modified.**

---

## 1. Read register — 22 of 22 COMPLETE

| # | file | lines | read |
|---|---|---|---|
| 1 | `ver3/REBUILD_POLICY.md` | 261 | COMPLETE |
| 2 | `ver3/REPOSITORY_LAYOUT.md` | 182 | COMPLETE |
| 3 | `ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml` | 195 | COMPLETE |
| 4 | `ver3/RETIREMENT_MATRIX.yaml` | 645 | COMPLETE |
| 5 | `ver3/phase0/ARCHITECTURE_INVARIANTS.yaml` | 628 | COMPLETE |
| 6 | `ver3/phase0/VER2_RETIREMENT_MATRIX.md` | 138 | COMPLETE |
| 7 | `ver3/phase0/ARCHITECTURE_CHANGE_PROPOSALS.yaml` | 135 | COMPLETE |
| 8 | `ver3/phase0/ARCHITECTURE_COMPREHENSION_CHECK.md` | 398 | COMPLETE |
| 9 | `ver3/phase0/PHASE0_EVIDENCE_REPORT.md` | 1 | COMPLETE (title-only stub) |
| 10 | `docs/PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md` | 1,056 | COMPLETE |
| 11 | `docs/PIPELINE_CRITICAL_DESIGN_REVIEW.md` | 1,260 | COMPLETE |
| 12 | `docs/PIPELINE_HIGH_RISK_ARCHITECTURE_CHECK.md` | 552 | COMPLETE |
| 13 | `docs/PIPELINE_IMPLEMENTATION_PROPOSAL.md` | 1,130 | COMPLETE |
| 14 | `docs/PIPELINE_IMPLEMENTATION_READINESS.md` | 226 | COMPLETE |
| 15 | `docs/PIPELINE_STAGE_MATURITY_AUDIT.md` | 437 | COMPLETE |
| 16 | `docs/WINDOW_S01_S02_IMPLEMENTATION_REPORT.md` | 222 | COMPLETE |
| 17 | `docs/WINDOW_S01_S02_FREEZE_REVIEW.md` | 748 | COMPLETE |
| 18 | `docs/WINDOW_S03_S04_IMPLEMENTATION_REPORT.md` | 727 | COMPLETE |
| 19 | `docs/S02_S04_REASONING_GAP_ANALYSIS.md` | 294 | COMPLETE |
| 20 | `docs/VERIFICATION_PROVENANCE_AUDIT.md` | 118 | COMPLETE |
| 21 | `.github/workflows/ver3-boundaries.yml` | 48 | COMPLETE |
| 22 | `README.md` | 312 | COMPLETE |

Total 9,713 lines. Filesystem checks used to verify a document's factual claim
were run **after** the file was read, never in place of reading it.

---

## 2. The document succession, established from the documents themselves

Each link is stated by the later document, not inferred.

```
phase0 (FROZEN standing authority)
  ARCHITECTURE_INVARIANTS · VER2_RETIREMENT_MATRIX · ARCHITECTURE_CHANGE_PROPOSALS
        │  changed only through ACP-nnn
        ▼
rebuild governance
  REBUILD_POLICY ("loses to phase0") · REPOSITORY_LAYOUT · RETIREMENT_MATRIX.yaml
  ("the prose file wins and this file is wrong") · FORBIDDEN_LEGACY_DEPENDENCIES
        ▼
design chain
  GEOMETRY_AND_INFORMATION_PLAN
        ▼   "This document does not repeat it; it attacks it, and it overturns
            two of its conclusions"  (CRITICAL_DESIGN_REVIEW §intro)
  CRITICAL_DESIGN_REVIEW
        ▼   three falsification probes, verdict B, sixteen corrections
  HIGH_RISK_ARCHITECTURE_CHECK
        ▼   "This proposal *supersedes* their recommendations where they
            conflict, and it settles seven of the eight questions the critical
            review left open"  (PROPOSAL §intro)
  PIPELINE_IMPLEMENTATION_PROPOSAL — revision 2  ◄── ARCHITECTURE OF RECORD
        ▼   sixteen corrections applied to the contracts
  PIPELINE_IMPLEMENTATION_READINESS — verdict B
        ▼   "This corrects the basis of the previous task's verdict"
  PIPELINE_STAGE_MATURITY_AUDIT — contract layer RED, 7 of 309 tests failing
        ▼
implementation chain
  WINDOW_S01_S02_IMPLEMENTATION_REPORT
  WINDOW_S01_S02_FREEZE_REVIEW  (+ DeepSeek validation, Stabilization, Q-6 cycles)
  WINDOW_S03_S04_IMPLEMENTATION_REPORT  (+ Cycles 2, 3, 4, 5)
  S02_S04_REASONING_GAP_ANALYSIS  (+ appendix = the HEAD commit's result)
  VERIFICATION_PROVENANCE_AUDIT
```

**`PIPELINE_IMPLEMENTATION_PROPOSAL.md` revision 2 is the architecture of
record.** It says so, it incorporates the falsification pass, and the readiness
document translates it into contracts. Where the geometry plan or the critical
review disagrees with it, the proposal governs — by its own declaration and by
sequence.

---

## 3. What S01–S04 were intended to be

Reconstructed from the complete corpus. Sources are named per claim.

### 3.1 The governing purpose

`ARCHITECTURE_COMPREHENSION_CHECK` §D states the research hypothesis:

> Can a stable, typed, shared design state support progressive mechanical
> synthesis and verification without either manually encoding complete product
> solutions as in Ver1, or allowing weak stage summaries and heuristics to invent
> missing embodiment as in Ver2?

and its wager: *"A system that reliably reports `UNRESOLVED` and `UNSUPPORTED` in
the right places is more useful, and more falsifiable, than one that always emits
a complete-looking design."*

Ver1's central failure: *"the design space was enumerated in advance by hand, so
synthesis degenerated to retrieval, and every gap in the enumeration was reported
as a fact about physics."* Ver2's: *"there was no single design. Each stage owned
a private document, so identity, geometry and intent were re-derived at every
boundary, and every re-derivation needed a heuristic to fill what the previous
representation could not carry."*

### 3.2 Seven design principles (`PROPOSAL` §1)

1. A stage owns a **question**, not a representation.
2. Commitment follows evidence; **maturity is per value**, not per stage.
3. Checks run at the **cheapest maturity at which they mean something** —
   "thirteen of the fourteen late discoveries were knowable before CAD."
4. **Completeness is enforced by totality, not by declaration.** "A declared set
   can omit. A total function over an enumerable domain cannot."
5. **Every constraint carries the means of its own refutation** — the defeat
   specification is authored with the relation.
6. Feed-forward with **two declared bounded loops** (S05↔S06; S04·B→S05→S06→
   re-validate). "Pretending it is a DAG is what produced `CHG-01`."
7. What cannot be evidenced is declared unevaluable **at S02**, not discovered at
   S11.

### 3.3 The four stages, as intended

**S01 — requirement capture.** *What did the user actually say, and what did they
leave open?* Owns `Requirement`, `SourceClause`, `Freedom`, `Ambiguity`,
`Scenario` (with `kind ∈ OPERATION|SERVICE|ASSEMBLY|TRANSPORT`), `Actor`,
`SystemBoundary`, observables, and a **quantity inventory** — per requirement,
whether the source gives a magnitude, a band, a comparative, or **nothing**, with
*none* recorded explicitly. Sole reader of raw source text (INV-002). Failure mode
is **sharpening**, mechanically checkable. Knowledge base: **none** — "a KB here
imports assumptions."

**S02 — obligation, load and candidate formation.** *What must physically be
true, what loads exist, what families could satisfy both, and which of those can
we evidence?* Owns `Obligation`, `Candidate`, `AcceptanceContract`, `LoadCase`,
and per candidate an `evidence_route_verdict`. `LoadCase` is
**candidate-independent**: scenario, applied-to **role**, `reacted_at_role`,
direction class, `kind ∈ GRAVITY|PAYLOAD|ACTOR_APPLIED|REACTION`, magnitude or
`UNSUPPORTED`. Never selects a winner (INV-007), never scores (R-16), never
reports absence-from-a-library as anything but `UNSUPPORTED` (INV-011). Must
record the obligations each candidate **creates**, not only those it addresses.
LLM role: **highest of any stage**.

**S03 — topology, mobility and assembly strategy.** *What things are there, how
are they connected, what may move, what must not, what reacts what, and in what
order does it go together?* The stage that "owns the mechanism". Owns `Body`,
`RigidGroup`, `Joint` (type, participants, DOF, **axis direction only**),
compliant `Joint`, `Interface`, `MobilityExpectation`, `blocked_by` relations,
`LoadPath` (per candidate, maturity `HYPOTHESIS`), `AssemblyStep`,
`FunctionalRegion` (role only), `Configuration`.

Its central obligation is **DOF totality**: every rigid group × every
configuration × every rigid-body DOF maps to exactly one of `INTENDED` /
`BLOCKED_BY(relation)` / `MAINTAINED_BY_CLASS(class)` / `IRRELEVANT_BECAUSE(reason)`.
Called "the mechanical FMEA … obtained free from the joint graph"
(`CRITICAL_DESIGN_REVIEW` §A2.1) and "the single highest-value change in this
review".

**The LLM role for totality is explicitly `NONE`** — "the domain is enumerated
mechanically; the LLM only dispositions each entry" (`PROPOSAL` §3 S03).

Never decides: any axis **placement** (S-3, `CHG-01`); any magnitude; any feature
shape; a selected candidate.

**S04 — two passes with the selection gate between them.**
*S04·A envelope and reach feasibility* — provisional envelopes, metric functional-
region volumes, actor reach, conservative AABB interference, candidate
elimination with a stated geometric reason. Then the **SELECTION GATE**.
*S04·B placement, motion and spatial proof* — located joint frames
(`PROVISIONAL`), states, transitions with **declared non-adaptive sampling and
interior samples**, swept volumes, assembly insertion sweeps computed against the
configuration produced by the preceding steps, occupancy per region per state and
path, and confirmation or refutation of every provisional load path.

"The pose law is not authored" — with located frames and joint coordinates every
pose is derivable (D-7). The two-pass split exists because a single-fidelity gate
was counted as unaffordable: the Oracles list 7 and 5 admissible fixtures; the
manual process carried 2, 1 and 1 (D-5).

### 3.4 The representation

Five new families, count 32 → 37: `RigidGroup`, `LoadCase`, `LoadPath`,
`FunctionalRegion`, `AssemblyStep`. Cross-cutting **fields, not families**:
`maturity ∈ SYMBOLIC|PROVISIONAL|AUTHORITATIVE|FROZEN` on every geometric value;
four-way provenance; defeat specification; envelope. Typed **relations, not
families**: `blocked_by`, `retained_by`, assembly precedence. Explicitly
**derived, never stored**: support, contact, reaction, **element load
components**, pose law, motion path.

The single sharpest data rule (`PROPOSAL` §8, D-3): *"Per-element load components
are DERIVED from the load path and are never stored. A stored 'this shaft carries
a transverse load' field is a candidate-independent-looking assertion about a
candidate-dependent fact."* Its authority is the Oracle's own closing finding
SF-5.3.

### 3.5 The prescribed order of work

Four documents independently specify what must happen before a stage is
implemented, and three of them use the phrase "highest value".

| document | prerequisite steps | then |
|---|---|---|
| `GEOMETRY_AND_INFORMATION_PLAN` §10 | 1 fix the unparseable `poses.yaml` + add a repo-wide YAML check · 2 add families · 3 patch contract · **4 write the six sufficiency probes** · **5 retro-fit the CAD references as probe fixtures — "the highest-value item in the plan … requires no stage implementation at all"** · 6 Scout contract | *"7. **Then, and only then, begin S03**"* |
| `CRITICAL_DESIGN_REVIEW` §B8 | 1–4 contract work · **5 nine sufficiency probes, "STAGE_PROGRESSION_CONTRACT step 6 mandates them and they do not exist"** · **6 hand-author S03/S04·B outputs for the three references and run the probes — "Highest value per unit of effort in this list; needs no stage implementation"** · 7 Scout contract | *"8. **Then implement**"* |
| `IMPLEMENTATION_READINESS` §6 | **1 write the nine sufficiency probes** · **2 hand-author S03/S04·B outputs and run the probes — "Highest value per unit of effort; still no stage implementation"** · 3 resolve the Oracle-freeze ruling D-2 | 4 S01, S02 · 5 S03 · 6 S04 · 7 S06 then S05 · 8 S07. *"Steps 1–3 involve no stage code. **If the architecture is wrong, step 2 finds it before anything is built.**"* |
| `STAGE_MATURITY_AUDIT` §2.5 | **0 close the RED contract layer** · **1 nine probes** · **2 hand-authored fixtures from the CAD references** | 3 S01 · 4 S02 · 4b candidate-generation method + capability registry · 5 S03 · **6 S07 out of order** · 7 S04 · 8 constraint language · 9 S06 then S05 |

`STAGE_PROGRESSION_CONTRACT` step 6 — "demonstrate downstream sufficiency" — is
the gate all four are describing. `REBUILD_POLICY` §5 calls it "the real gate":

> Schema validity is cheap: a stage can emit a well-formed structure that is
> substantively empty, and the downstream stage then compensates with a default.
> Every retirement row R-01..R-32 is a compensation that was made because the
> upstream output was insufficient and nothing forced the issue back upstream.

---

## 4. Where the documents disagree

Each entry: what one artifact says, what another says, why it is strange, status.
**No root cause is proposed.**

### DIS-1 — The CI gate forbids the tree that exists

**OBSERVATION** — `.github/workflows/ver3-boundaries.yml:41-47`, step
*"No stages package exists"*: `if [ -d ver3/assy_v3/stages ]; then … exit 1`,
with the message *"stage implementation has begun without the progression gate."*

**CONFLICTING EVIDENCE** — `ver3/assy_v3/stages/` contains `__init__.py`,
`base.py`, `s01_requirement_capture.py`, `s02_obligation_and_candidates.py`,
`s03_topology_and_mobility.py`, `s04_envelope_and_motion.py`.
`WINDOW_S03_S04_IMPLEMENTATION_REPORT` §18 and §24 report **"316 tests pass"**
across five cycles.

**WHY IT IS STRANGE** — the only automated gate in the repository asserts a
condition the repository violates, while every implementation report cites a
green test count that this job would never reach. The workflow triggers on
`paths: ['ver3/**']`, which every one of those commits touched.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P6: whether the meta suite's
`test_no_stage_implementation.py` encodes the same or a different rule).

### DIS-2 — Four documents make the sufficiency probes a precondition; they do not exist

**OBSERVATION** — the four prerequisite lists in §3.5 above, plus
`REBUILD_POLICY` §5 step 6 and `STAGE_PROGRESSION_CONTRACT` step 6.

**CONFLICTING EVIDENCE** — no probe file exists under `ver3/`. No `s03` or `s04`
fixture exists for any case; `ver3/assy_v3/fixtures/responses/` holds `s01.json`
and `s02.json` for BM-001/2/3 only. S01, S02, S03, S04·A and S04·B are all
implemented and have produced live output on six cases.

**WHY IT IS STRANGE** — the step three documents call the highest-value item, and
which each says needs *no stage implementation at all*, was skipped, and the work
it was meant to de-risk was done instead. `IMPLEMENTATION_READINESS` §6 states the
purpose of the skipped step explicitly: *"If the architecture is wrong, step 2
finds it before anything is built."*

**STATUS** — UNRESOLVED.

### DIS-3 — U-05 is recorded as blocking Stage 02, and Stage 02 is implemented

**OBSERVATION** — `RETIREMENT_MATRIX.yaml` §6:
```yaml
- id: U-05
  concept: where mechanism knowledge comes from at all
  provisional: >
    KnowledgeProvider is a boundary, deliberately unimplemented. It must not be
    closed by importing Ver1 cards or the root ontology.
  blocks: "Stage 02 implementation"
  note: >
    LOAD-BEARING. This is exactly where Ver3 could silently become Ver1.
```
`VER2_RETIREMENT_MATRIX.md` §8 carries the same row and closes: *"U-05 is the
load-bearing one: it is exactly where Ver3 could silently become Ver1 again."*
`ARCHITECTURE_COMPREHENSION_CHECK` §C.13 adds the criterion: *"a knowledge base
that answers 'which mechanism' is a card library **regardless of how well sourced
it is**."*

**CONFLICTING EVIDENCE** — `ver3/assy_v3/knowledge/principle_library.py` exists
and, per `WINDOW_S01_S02_FREEZE_REVIEW` §3, holds **10 function classes and 42
principle families**, consulted by S02. The same document's criterion 9 declares
the knowledge boundary intact on the grounds that the index key is a function
class and no key is a product noun. `ARCHITECTURE_CHANGE_PROPOSALS.yaml` contains
exactly one proposal, ACP-001, which renames a path and records
`semantic_change: false`.

**WHY IT IS STRANGE** — the same file that records U-05 has a demonstrated
mechanism for recording a resolution — U-03 carries
`status: RESOLVED_BY_THIS_TASK` with a `resolved_by` explanation. U-05 carries no
such field. So a blocking, self-described load-bearing undecided was crossed
without using the resolution mechanism that sits three rows above it, and the
justification lives only in an implementation report.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P5: complete read of
`principle_library.py` against the "regardless of how well sourced" criterion).

### DIS-4 — The architecture of record names a knowledge base the boundary rules forbid

**OBSERVATION** — `PROPOSAL` §3 S02, *Knowledge-base role*: **"The micro-oracle
capability packs are the KB."** Repeated in `CRITICAL_DESIGN_REVIEW` §B1 S02 and
`GEOMETRY_AND_INFORMATION_PLAN` §5 S02, naming `guided-slider`,
`rotary-to-linear-engagement`, `latch-retention`.

**CONFLICTING EVIDENCE** — those packs live under `ver3/oracles/micro_oracles/`.
`FORBIDDEN_LEGACY_DEPENDENCIES.yaml` lists `ver3/oracles/` with
`severity: BLOCKING`. `REPOSITORY_LAYOUT` §2: `assy_v3` may read `oracles/`
**"never (BLOCKING)"**. `RETIREMENT_MATRIX.yaml` §5:
`prohibition: "assy_v3 must not import or read ver3/oracles at runtime."`

**WHY IT IS STRANGE** — the architecture of record assigns S02 a knowledge base
that the boundary rules make unreachable from the stage that must consult it.
Neither the proposal nor the readiness document notices. `PROPOSAL` §11 D-12
separately reasons that the *evidence route* belongs outside DesignState in a
capability registry — but says nothing about the KB itself.
`GEOMETRY_AND_INFORMATION_PLAN` §11 R-6 adds that the micro-oracles are
unvalidated: *"All three are `PRE_CAD_SEMANTIC_REVIEWED` with every fixture
`NEEDS_GEOMETRY_VALIDATION`. Using them as the S02/S05 KB imports whatever is
wrong in them."*

**STATUS** — UNRESOLVED.

### DIS-5 — The eighteen planned validators were replaced without a proposal

**OBSERVATION** — `ARCHITECTURE_INVARIANTS.yaml` gives every invariant a
`planned_validator`. Thirteen point into `ver3/assy_v3/validation/`; five into
`ver3/tests/meta/`. Thirteen invariants are `severity: BLOCKING`. Five named
ablation/invariance experiments exist only there: `role_rename_invariance`,
`annotation_ablation`, `case_rename_run`, `paraphrase_invariance`,
`double_run_compare`.

**CONFLICTING EVIDENCE** — there is no `ver3/assy_v3/validation/` package. None
of the sixteen named files exists. None of the ten named check functions appears
in any file under `ver3/`. `ver3/oracles/LOCK.json`, which INV-017's validator
would hash, does not exist. `ACP-001` states of the thirteen it renamed: *"Every
one is PLANNED. None exists yet"* — accurate on 2026-08-05 — and no later
proposal exists. What exists instead is per-stage `deterministic_checks` embedded
in the stage contracts and implemented inside the stage modules.

**WHY IT IS STRANGE** — the FROZEN standing authority specifies a detection
strategy per invariant, and a different mechanism was built. Whether checks owned
by the stage they judge can discharge INV-008's `label_is_not_realization` or
INV-003's `annotation_ablation` is not addressed by any document in the corpus.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P2 stage contracts, P6
validators).

### DIS-6 — The prescribed pre-stage substrate was not built

**OBSERVATION** — `REPOSITORY_LAYOUT` §4, "Phase 1 — the substrate, before any
stage", lists seven items including `assy_v3/provenance/` — *"Built with the
state, not after it: a value that enters the state without provenance cannot have
it added retroactively with any credibility"* — and `assy_v3/assurance/` —
*"**Built here, before S01.** Built last it becomes a report generator, and a
report generator invents structure the stages never produced."* `REBUILD_POLICY`
§3 specifies the assurance package as a projection of DesignState with 34
enumerated items PKG-01..PKG-34, and states a required item with nothing to report
is emitted **empty with a stated reason**; omitting it is `CONTRACT_INCOMPLETE`.

**CONFLICTING EVIDENCE** — `ver3/assy_v3/` contains `state/`, `providers/`,
`stages/`, `knowledge/`, `fixtures/`, `probes/`. No `provenance/`, no
`assurance/`. `WINDOW_S03_S04_IMPLEMENTATION_REPORT` §19 describes
`ver3/tools/build_pipeline_dashboard.py` producing a 9.8 MB HTML report after the
run. `WINDOW_S03_S04_IMPLEMENTATION_REPORT` §2 records three families as
*"not yet in the assurance package, with the gap carried as `package_debt`"*, and
`WINDOW_S01_S02_IMPLEMENTATION_REPORT` D-4 records the same for `Actor` and five
others.

**WHY IT IS STRANGE** — the assurance package is referenced as an existing thing
that families can be missing from, while no module implements it; and the only
artifact of that shape is a last-running report generator, which is exactly the
shape `REPOSITORY_LAYOUT` §4 and `REBUILD_POLICY` §3 forbid it to be.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P2
`GENERATED_ASSURANCE_PACKAGE_CONTRACT`, P6 dashboard).

### DIS-7 — Two governing documents describe a repository state that no longer exists

**OBSERVATION** — `REPOSITORY_LAYOUT` §1: `assy_v3/` is *"THE PIPELINE. Empty of
stage logic"*, listing only `providers/`. §3: *"All ten are `draft`. None may
become `frozen` while BM-003 is a placeholder."* §5: *"108 tests."*
`REBUILD_POLICY` §5: *"BM-003 is currently a placeholder with no source request
and no Oracle, and it therefore **blocks freezing any stage contract**."* §8:
*"**BM-003's subject.** Deliberately unchosen."*

**CONFLICTING EVIDENCE** — BM-003 has a 30-line frozen source request, a 14-file
held-out Oracle, and a descriptor recording `authority_status: FROZEN`. The
implementation reports cite 309, 313 and 316 tests. Window 1 is "provisionally
frozen"; Window 2 is "FROZEN".

**WHY IT IS STRANGE** — both documents are still nominated as governing —
`REBUILD_POLICY` is "the governing statement for that rebuild" — while describing
preconditions that have since been met and a package layout that has since
changed. Nothing in the corpus marks either as superseded.

**STATUS** — UNRESOLVED (staleness, not conflict of intent).

### DIS-8 — "S04 is not implemented" stands as the header of a document whose later half implements it

**OBSERVATION** — `WINDOW_S03_S04_IMPLEMENTATION_REPORT.md:3-7`: *"**Scope
actually delivered, stated first.** S03 is implemented, running live and evaluated
on all six cases. **S04 is not implemented.**"*

**CONFLICTING EVIDENCE** — §11 of the same file, *"Cycle 2 — S04 implemented,
S03→S04 exercised … `ver3/assy_v3/stages/s04_envelope_and_motion.py`. Two passes,
nine checks."* §13: *"S04 did not fail once."* §24 gives S04 badges for all six
cases.

**WHY IT IS STRANGE** — the report is a five-cycle accretion under one Cycle-1
header. A reader taking the stated-first scope at face value would conclude the
opposite of what the document later records. This is the direct source of the
contradiction carried into this audit's scope as PC-02.

**STATUS** — RESOLVED at document level: the header is stale relative to Cycles
2–5 in the same file. Recorded because a prior claim in this corpus is unreliable
at its most prominent point.

### DIS-9 — The entity-family count is stated five different ways

**OBSERVATION**, in sequence:

| document | statement |
|---|---|
| `REPOSITORY_LAYOUT` §1 | `ENTITY_FAMILY_AUDIT.yaml` — "consumer justification for all **32** families" |
| `PROPOSAL` §2.1, §8 | "No family is removed. The count goes **32 → 37**." |
| `IMPLEMENTATION_READINESS` §1 | "Family count: **37**, plus `CompliantJoint` documented under its own key — **38 keys, 37 families**." |
| `STAGE_MATURITY_AUDIT` §0 | RED: "`ENTITY_FAMILY_AUDIT.yaml` still lists **32** families; `DESIGN_STATE_CONTRACT` now has **38** keys" and "`CompliantJoint` … Either it becomes a real family (38, owned by s03) or it moves inside `Joint` (37, no new key). **That is a contract decision, not a test fix**, and it is unresolved." |
| `WINDOW_S01_S02_IMPLEMENTATION_REPORT` §1 | "`CompliantJoint` … **folded into `Joint` as a `compliant_variant`**" |
| `WINDOW_S03_S04_IMPLEMENTATION_REPORT` §2 | "Three families added, **41 → 44**" — and, seven lines later, "honest summary totals (**41 families**; PROVISIONAL 3 → 6)" |

**WHY IT IS STRANGE** — the last row states two different post-change totals in
one section. The path 37 → 41 is never explained by any document.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P2: `ENTITY_FAMILY_AUDIT.yaml`
and `DESIGN_STATE_CONTRACT.yaml` are the only things that can settle the count).

### DIS-10 — A frozen window was modified after being frozen

**OBSERVATION** — `WINDOW_S03_S04_IMPLEMENTATION_REPORT` §26: *"**WINDOW 2
FROZEN.** Frozen means the boundaries and the reporting are trustworthy."*

**CONFLICTING EVIDENCE** — "Cycle 5 — structural ambiguity removed (R-1..R-4)"
follows in the same file and changes the S03 implementation (370 lines in commit
`ef437cd`), makes `S03_CONTRACT.blocking_relation_rule` authoritative in code,
adds `canonicalise_blocking()`, `derive_mobility()` and `free_dof()`, and rewrites
the s03b prompt.

**WHY IT IS STRANGE** — no document defines what a window freeze permits.
`STAGE_PROGRESSION_CONTRACT` step 8 defines a *stage contract* freeze; the window
freezes are a separate vocabulary introduced by the implementation reports and
never contracted.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P2:
`STAGE_PROGRESSION_CONTRACT`).

### DIS-11 — The architecture of record's decision against a blocking-relation entity is contradicted by its own live evidence

**OBSERVATION** — `PROPOSAL` §8 classifies retention/blocking as a **typed
relation, not a family**: `blocked_by(group, direction, blocker, features,
configurations, defeat_spec)`, "RELATE, per GAP-01's own recommendation".
`CRITICAL_DESIGN_REVIEW` §A7.4 similarly rejects a `DOFDisposition` family in
favour of a totality requirement on `MobilityExpectation`.

**CONFLICTING EVIDENCE** — `WINDOW_S03_S04_IMPLEMENTATION_REPORT` Cycle 5,
"Remaining, with earliest cause": *"`UnresolvedDecision.blocks → BLK-0001`
dangling (BM-002, PRB-03 s03b) — **representation** — a blocking relation has no
entity to be referenced. **First Window 2 evidence meeting rule 8's bar.**"*
`S02_S04_REASONING_GAP_ANALYSIS` §appendix records the same and adds: *"This is
the first evidence in Window 2 that the current representation **cannot express a
fact the reasoning needs**: a relation the design must be able to point at."*
Its §5 M-1 states the cost independently: *"BM-003 authored 56 grid details for
what is mechanically a few retention facts."*

**WHY IT IS STRANGE** — this is the corpus contradicting its own architecture of
record on the strength of live output, and both documents say the evidentiary bar
for reopening the schema is now met. Nothing has been reopened.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P4A: the dangling `BLK-` ids in
the raw `s03b` output; P2: whether `DESIGN_STATE_CONTRACT` gives blocking any
addressable identity).

### DIS-12 — `BodyHypothesis` and `PhysicalInteractionHypothesis` have four different statuses across the corpus

**OBSERVATION**, in sequence:

| document | status assigned |
|---|---|
| `GEOMETRY_AND_INFORMATION_PLAN` §5 S02 | "Owns … plus **(new)** `PhysicalInteractionHypothesis` and `BodyHypothesis`" |
| §6 information matrix, S02→S03 | minimum sufficient hand-over; failure if absent: *"S03 invents the mechanism"* |
| `CRITICAL_DESIGN_REVIEW` §B1 S02 | listed under "Decisions owned", **without** a `[NEW]` marker |
| `PROPOSAL` §3 S02 Outputs | "provisional body hypotheses and interaction hypotheses" — lower-case prose; **absent** from §8's five new families and from the changed-families list |
| `WINDOW_S03_S04_IMPLEMENTATION_REPORT` §2 W2-I1 | *"S03's contract required `BodyHypothesis` and `PhysicalInteractionHypothesis` **from S02**. Neither is a defined entity family and S02 produces neither … corrected by rewriting S03's `required_inputs` to what S02 actually emits"* |

**CONFLICTING EVIDENCE** — each string still occurs exactly once in
`S02_CONTRACT.yaml` and once in `S03_CONTRACT.yaml`, and nowhere in
`DESIGN_STATE_CONTRACT.yaml`, `STAGE_OWNERSHIP_MATRIX.yaml` or any `.py` under
`ver3/assy_v3/`.

**WHY IT IS STRANGE** — a family named by the information matrix as the thing
whose absence causes *"S03 invents the mechanism"* was progressively demoted from
`[NEW] owned family` to prose to `does not exist`, with no document stating what
replaced its function at the S02→S03 boundary.

**STATUS** — UNRESOLVED. NEEDS LATER CROSS-READ (P2: in what capacity the four
surviving mentions appear; P4A: what S02 actually hands S03 in the raw output).

### DIS-13 — The ver3 pipeline's design documents live in a directory ver3 classifies as non-pipeline

**OBSERVATION** — `RETIREMENT_MATRIX.yaml` §4, this repository's root tree:
```yaml
- path: docs/
  disposition: KEEP_NON_PIPELINE
  reason: "KG project documentation."
```
`README.md:169` agrees: `docs/` holds "design, extraction, coverage, cross-book,
substitution, CQs" — six mdkg documents.

**CONFLICTING EVIDENCE** — `docs/` also holds all eleven pipeline architecture,
review, readiness and window documents, i.e. the entire design record of S01–S12.

**WHY IT IS STRANGE** — the classification is machine-readable and is the same
file that declares `ver3/oracles/` and `ver3/cad_validation/` hard prohibitions.
`KEEP_NON_PIPELINE` is defined as *"Belongs to a different project that happens to
share this repository."*

**STATUS** — UNRESOLVED (classification staleness).

### DIS-14 — The repository's front door describes a different system

**OBSERVATION** — `README.md` describes **mdkg**, an ontology and knowledge graph
built from two textbooks, over 312 lines. It names no stage, no benchmark, no
probe, and neither ASSY nor ver3.

**WHY IT IS STRANGE** — recorded so the exclusion of the mdkg corpus from this
audit is visible rather than silent, and because Q1 — *what was ASSY intended to
become?* — cannot be answered from the repository's README at all.

**STATUS** — RESOLVED as scope: mdkg is a separate project sharing the
repository, and `FORBIDDEN_LEGACY_DEPENDENCIES.yaml` already makes six of its
trees forbidden roots for `assy_v3`.

---

## 5. Strange things recorded, not yet explained

Facts the corpus states about itself that bear directly on later packages.

**SR-1 — the S01/S02 upstream of every Window-2 run is the corpus's own weakest
evidence category.** `run_window2.py` replays S01 and S02 from the recorded
fixtures. `WINDOW_S01_S02_FREEZE_REVIEW` §2 classifies those recordings as
*"**weak by construction**: those recordings were authored with the validators in
view, so they are regression fixtures and not evidence that the reasoning works"*.
`WINDOW_S01_S02_IMPLEMENTATION_REPORT` D-5 adds that obligation `scope` and
`satisfiable_at` were *"assigned in fixtures partly by keyword heuristic and
hand-corrected where the checks objected"*. `W-6` records the fixtures remain
*"richer than live output"*. Every S03/S04 engineering result therefore rests on
an upstream the documents themselves decline to treat as evidence.

**SR-2 — a check that fires with no true positives has now happened four times.**
`actor_citation` 4 findings / 0 true (Window 1 L-1); `PART_NOUNS` matching `pin`
inside `gripping` (L-2); `OBLIGATION_UNOWNED_AT_S03` 48 findings / 0 true and
*"no response can ever pass this check"* (W2-F4); `LOADPATH_HOP_UNKNOWN` 31
findings describing correct paths (W2-F5). `WINDOW_S03_S04` §7 states the pattern:
*"a check that fires 48 times with zero true positives is worse than no check: it
is the `actor_citation` and `PART_NOUNS` lesson from Window 1, repeated by me one
window later."*

**SR-3 — the corpus states plainly that model weakness is not available as an
explanation.** `S02_S04_REASONING_GAP_ANALYSIS` §9: *"The evidence in §3 shows a
cheap model producing per-DOF constraint reasoning with executable defeat tests.
'The model is weak' is not available as an explanation here."* §3 records that
262 blocking relations were authored complete and reported absent because the
required keys were described in prose rather than shown as keys — a
**false-negative cascade**, ~95% of S03/S04 findings downstream of it.

**SR-4 — the enumeration-gap class recurred inside a single window.**
`axis_direction` had no value for a FIXED joint (W2-F2); `termination_strategy`
had no value for the first body placed (W2-F8). Cycle 2 §10 records the standing
rule this produced: *"every closed value set needs a member meaning 'legitimately
none'."*

**SR-5 — S04's spatial verdicts are conservative by construction and their
meaning is unmeasured.** Every extent is an axis-aligned box, so overlap is never
`FAIL`; `FAIL` is deliberately absent from the overlap vocabulary. D2-10:
*"Whether the NOT_VERIFIED volume is real tightness or box conservatism is
unmeasured."* Cycle 5 counts `configuration_interference` 47, `assembly_path` 39,
`swept_clearance` 24, all classed *"validator — AABB conservatism; near-vacuous,
all NOT_VERIFIED."*

**SR-6 — the selection gate has never been exercised.** D2-11: *"the selection
gate is implemented and checked but never exercised: one candidate per case was
embodied, so no gate decision was ever taken."* INV-007 is the invariant the gate
exists to enforce.

**SR-7 — the model substitution is recorded, not assumed.** `deepseek-chat` was
requested; `deepseek-v4-flash` was served on 26/26 calls, temperature 1.0,
`seed_honoured: UNKNOWN`. W-5: *"One model, one vendor, one temperature."*

**SR-8 — granularity is unconstrained and invisible.** W-4: BM-003 yields 14–24
requirements across three trials at T=1.0. *"Nothing in the fourteen checks
constrains granularity, so this is invisible to the pipeline today."*

**SR-9 — the disposition-depth gap survives every cycle.** Window 2 §6: blocked
DOF is 0 on three of six cases; *"a mechanism in which nothing is blocked is not a
mechanism … the model reaches for `MAINTAINED_BY_CLASS`, which costs nothing, and
avoids `BLOCKED_BY`, which demands a direction, a named blocker, a defeat
specification and a driver. Totality made the omission visible; it did not make it
stop."* Cycle 4 closes with *"Do not begin S05 without addressing the blocked-DOF
depth debt, which is now the largest declared gap."*

**SR-10 — one artifact the corpus quotes is a model inventing a container.**
`PRB-02/t3` emitted a top-level key the schema does not define,
`_obligations_created`, holding fully-formed obligation objects. The freeze review
calls it *"the decisive artifact"*. It is a specific raw file this audit can open
in P4A.

---

## 6. What Package 1 does not settle

- Whether the contracts express the architecture of record. **P2.**
- What the stage contracts actually require of S01–S04, and in what capacity the
  four surviving `BodyHypothesis` / `PhysicalInteractionHypothesis` mentions
  appear. **P2.**
- The true entity-family count and whether the five proposal families exist under
  those names. **P2.**
- What the raw stage outputs actually describe as mechanisms. **P4A.**
- Which facts DeepSeek authored and which deterministic code derived. **P4A/P5.**
- Whether the embedded per-stage checks discharge the eighteen invariants.
  **P5/P6.**
- Whether the dashboard is, or is mistaken for, the assurance package. **P6.**

---

*Package 1 complete. Nothing in this document is a recommendation, and no file in
the repository was modified.*
