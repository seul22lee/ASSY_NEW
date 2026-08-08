# Audit evidence log

> # ⚠ SUPERSEDED HISTORICAL AUDIT RECORD
>
> **DO NOT USE THIS FILE AS CURRENT AUDIT COVERAGE OR CURRENT CONCLUSIONS.**
>
> This is a working record kept *during* the audit and frozen where it stood. Its
> coverage counts, `NOT READ` markers, open questions and provisional findings
> reflect a moment in the reading, **not the final state**. It stops inside Package 1 — its closing line reads "Package 1 continues" — and its PC-/OBS- entries are explicitly unresolved by design.
>
> **Current authorities:**
> - scope, corpus and coverage definitions → `AUDIT_SCOPE.md`
> - per-package findings and final coverage → `P1_COMPLETE.md` … `P6_COMPLETE.md`
> - final conclusions and requirement traceability → `P4B_FINAL_SYNTHESIS.md` (frozen, §21)
>
> Where this file and a `*_COMPLETE.md` report disagree, **the COMPLETE report
> governs**. Several findings recorded here were later withdrawn or narrowed on
> fuller evidence; those reversals are documented in `P5_COMPLETE.md` §14 and
> `P4A_COMPLETE.md` §H.
>
> Retained unedited for chronology. Nothing below has been rewritten to look current.

---

Session-scoped. Appended as reading proceeds. Findings during a package are
recorded as **Observation**, **Potential contradiction** or **Needs
verification** only; resolution waits until that package is complete.

`COMPLETE` here means read start-to-end in this session. No prior marking is
honoured.

---

> **Package 1 is COMPLETE.** The full read register, the reconstruction of the
> intended architecture, and the fourteen documented disagreements (DIS-1…DIS-14)
> plus ten recorded strange findings (SR-1…SR-10) are in
> [P1_COMPLETE.md](P1_COMPLETE.md). The partial findings below were written
> during the read and are superseded where the two differ — in particular PC-12
> and PC-13, which the complete corpus refines (see DIS-2, DIS-11, DIS-12).

## Read register

### Package 1 — intended S01–S04 architecture (9 of 22 at the time of this entry; now 22 of 22 — see P1_COMPLETE.md)

| # | file | lines | status |
|---|---|---|---|
| 1 | `ver3/REBUILD_POLICY.md` | 261 | **COMPLETE** |
| 2 | `ver3/REPOSITORY_LAYOUT.md` | 182 | **COMPLETE** |
| 3 | `ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml` | 195 | **COMPLETE** |
| 4 | `ver3/phase0/VER2_RETIREMENT_MATRIX.md` | 138 | **COMPLETE** |
| 5 | `ver3/phase0/ARCHITECTURE_INVARIANTS.yaml` | 628 | **COMPLETE** |
| 6 | `ver3/phase0/ARCHITECTURE_CHANGE_PROPOSALS.yaml` | 135 | **COMPLETE** |
| 7 | `ver3/phase0/PHASE0_EVIDENCE_REPORT.md` | 1 | **COMPLETE** (title-only stub, confirmed) |
| 8 | `ver3/phase0/ARCHITECTURE_COMPREHENSION_CHECK.md` | 398 | **COMPLETE** |
| 9 | `docs/PIPELINE_GEOMETRY_AND_INFORMATION_PLAN.md` | 1,056 | **COMPLETE** |
| 10–22 | remaining P1 | 6,703 | NOT READ |

---

## What the intended architecture says so far

Recorded as reconstruction, not conclusion.

**The three artifacts that may never be conflated** (`REBUILD_POLICY` §2). Hidden
Benchmark Oracle — human-authored, frozen before any source-only run, never
visible to production, **defines success**. Runtime Generated Assurance Package —
authored by the pipeline from its own state, during the run, *is* production
output, does **not** define success. Positive Executable Reference — human-built
working design, fixed before the benchmark is used, never visible to production,
does **not** define success; its purpose is to prove the *evaluator* works.
Similarity to it is never a scoring input: "scoring against it would convert 'did
the pipeline solve the problem' into 'did the pipeline reproduce this solution',
penalising every correct answer that differs."

**The assurance package is a projection, not a report** (§3). It has no authoring
channel of its own; every element must trace to an entity; it is built
**before S01**, not last, "because built last it becomes a report generator, and
a report generator invents structure the stages never produced." It must be able
to show 34 enumerated items (PKG-01..34) by S12. A required item with nothing to
report is emitted **empty with a stated reason**; omitting it is
`CONTRACT_INCOMPLETE`. *"We found no ambiguities" and "we never looked for
ambiguities" are different claims, and only the second is a defect.*

**Statuses describe the run, never the design** (§4). Twelve of them.
`SAFE_REJECTION` — declined a claim it could not support; correct behaviour,
never penalised. `FALSE_ACCEPTANCE` — claimed something it had not earned; "the
most serious defect class. Every other rule here is shaped to make it
detectable."

**How a stage gets built** (§5, eight steps). Contract → *define what the stage
must refuse, before implementing* → implement → source-only on all three
benchmarks → contract completeness → **downstream sufficiency** → leakage and
determinism → freeze. Step 6 is named "the real gate": *"Schema validity is
cheap: a stage can emit a well-formed structure that is substantively empty, and
the downstream stage then compensates with a default. Every retirement row
R-01..R-32 is a compensation that was made because the upstream output was
insufficient and nothing forced the issue back upstream."*

**Read permissions** (`REPOSITORY_LAYOUT` §2). `assy_v3` may read
`benchmarks/*/source/request.txt` **s01 only, at run time**; may read contracts
as schema definitions; may **never** read `descriptor.yaml` (branching on it is
FP-02 / INV-015 / R-14), `source_manifest.yaml`, `oracles/` (BLOCKING),
`cad_validation/` (BLOCKING), `oracle_tools/`, or the repository root.

**Retirement rows most relevant to the S03/S04 engineering review**: R-06
(interval swapping is not rotation — needs axis, parent/child frames, path, swept
region), R-07 (a fixed offset is not a motion model — cannot show interference
*along* the path), R-08 (an AABB label is not motion proof; permitted only as a
*conservative* pre-filter, labelled as such), R-09 (a generic block is a
placeholder, not an embodiment — realization must cite the obligations it
discharges), R-12 (declaration order is a serialization artifact, never an
engineering decision), R-15/16/17 (S02 naming a winner; part-count ranking, under
which **incompleteness wins**; stable sort as decision), R-21 (`or "mm"`), R-27
(missing knowledge reported as INFEASIBLE), and **R-28** — *"Field-presence
acceptance. Certifies that a schema was populated, not that a thing was designed.
A `revolute` label passes."* Its intended replacement is
**obligation→realization→predicate→evidence assertions**. R-28 is the audit's
objective 7 written down in advance.

**INV-008 `two_extremes_distinct`** already states the rule the S04 review needs:
each travel extreme must be discharged by its **own** contact feature or **own**
limit predicate at that extreme's joint coordinate. One physical part carrying two
terminal faces satisfies it; both extremes citing the same feature, one extreme
citing none, or a single predicate credited to both, violates it.

**INV-003** permits qualitative labels as annotation and forbids
label-as-authority, with two ablation tests named: `role_rename_invariance`
(rename every role string to an opaque token; authoritative geometry must be
byte-identical) and `annotation_ablation` (drop all annotation fields before S04
validation; every geometric predicate must reach the same verdict).

**U-05, recorded as the load-bearing open question** (`VER2_RETIREMENT_MATRIX`
§8): *"If Ver3 has no card library, what proposes candidates in Stage 02? Open
research question. `KnowledgeProvider` is a boundary, deliberately unimplemented.
Must not be closed by importing V1 cards or the root ASSY_NEW ontology."* The
matrix closes: *"U-05 is the load-bearing one: it is exactly where Ver3 could
silently become Ver1 again."*

---

## Findings

### PC-08 — Every named validator for every BLOCKING invariant is absent

**Potential contradiction. Verified by filesystem check, not inferred.**

`ARCHITECTURE_INVARIANTS.yaml` — phase0, described by `REPOSITORY_LAYOUT` §1 as
"FROZEN. The standing authority" — declares a `planned_validator` for each of
INV-001..INV-018. Sixteen of the eighteen name a file that does not exist
anywhere in the repository:

| invariant | planned validator | on disk |
|---|---|---|
| INV-001 | `assy_v3/validation/identity.py::check_single_denotation` | **absent** |
| INV-002 | `assy_v3/validation/projection.py::check_no_raw_request` | **absent** (`assy_v3/state/projection.py` exists but is the projection builder, not a check) |
| INV-003 | `assy_v3/validation/spatial.py::check_geometric_authority` | **absent** |
| INV-004 | `assy_v3/validation/defaults.py::check_no_silent_default` | **absent** |
| INV-005 | `assy_v3/validation/render_boundary.py` | **absent** |
| INV-006 | `assy_v3/validation/cad_boundary.py` | **absent** |
| INV-007 | `assy_v3/validation/selection.py::check_selection_gate` | **absent** |
| INV-008 | `assy_v3/validation/obligations.py::check_obligation_closure` | **absent** |
| INV-009 | `assy_v3/validation/verification.py::check_pass_scope` | **absent** |
| INV-010 | `assy_v3/validation/solver.py::check_solver_status` | **absent** |
| INV-011 | `assy_v3/validation/status.py::check_unsupported_vs_infeasible` | **absent** (`providers/status.py` is the enum, not a check) |
| INV-012 | `assy_v3/validation/evidence_match.py::check_semantic_identity` | **absent** |
| INV-013 | `assy_v3/validation/evidence_completeness.py::check_observable_bijection` | **absent** |
| INV-014 | `tests/meta/test_no_overfit_assertions.py` | **absent** |
| INV-015 | `tests/meta/test_no_benchmark_branches.py` | **absent** |
| INV-016 | `tests/meta/test_no_external_dependency.py` | **absent** |
| INV-017 | `tests/meta/test_oracle_lock.py` | **absent**; `ver3/oracles/LOCK.json`, which it would hash, is also absent |
| INV-018 | `tests/meta/test_stage_determinism.py` | **absent** |

There is **no `ver3/assy_v3/validation/` package**. None of the ten named check
functions appears anywhere under `ver3/` in any file.

Thirteen of these invariants are `severity: BLOCKING`. Among them are exactly the
ones that would decide the questions this audit asks: INV-003 (geometry proven by
geometry), INV-007 (no selection before comparable completeness), INV-008
(obligation closure; `label_is_not_realization`; `two_extremes_distinct`),
INV-004 (no silent default), INV-015 (no benchmark branching).

What *does* exist is validation embedded inside `s01`–`s04` themselves. That is a
different architecture from the one the standing authority specifies — checks
owned by the stage they judge rather than by an independent validation layer.
Whether the embedded checks cover the same ground, and whether a stage checking
itself can detect INV-008-class failures, is a P5/P6 question and is **not
resolved here**.

Related: INV-014's `freedom_assertion_scan`, INV-003's `role_rename_invariance`
and `annotation_ablation`, INV-015's `case_rename_run`, and INV-018's
`double_run_compare` are the five named ablation/invariance experiments. No file
implementing any of them exists.

### PC-09 — The prescribed pre-stage substrate was skipped; stages were built anyway

**Potential contradiction.**

`REPOSITORY_LAYOUT` §4 fixes the implementation order. Phase 1, "the substrate,
before any stage", lists seven items: `state/`, `provenance/`, `patch/`,
`status/`, `assurance/`, `providers/`, harness. Phase 2 is stages, "strictly in
order", and §4 states "Creating `assy_v3/stages/` is the act that starts this
phase".

On disk `assy_v3/` contains `state/`, `providers/`, `stages/`, `knowledge/`,
`fixtures/`, `probes/`. There is no `provenance/` package, no `assurance/`
package, no `patch/` package (a `state/patch.py` module exists), and no harness
directory — the harnesses live in `ver3/tools/`.

Two of the missing three are the ones §4 argues hardest for:

- **`provenance/`** — "Built with the state, not after it: a value that enters the
  state without provenance cannot have it added retroactively with any
  credibility." This bears directly on audit objective 4, which requires
  separating DEEPSEEK_AUTHORED from DETERMINISTICALLY_DERIVED from
  INVENTED_WITHOUT_ENGINEERING_EVIDENCE. If no provenance layer exists, the
  question is whether that separation is recoverable from the outputs at all.
- **`assurance/`** — "**Built here, before S01.** Built last it becomes a report
  generator, and a report generator invents structure the stages never
  produced." The only artifact resembling an assurance projection is
  `ver3/tools/build_pipeline_dashboard.py`, which is a report generator, runs
  last, and lives outside `assy_v3`. `REBUILD_POLICY` §3 forbids exactly this
  shape for the assurance package. **Needs verification** in P6 whether the
  dashboard is being treated as, or mistaken for, the assurance package — they
  are different artifacts with different authority, and PKG-01..PKG-34 is the
  test.

### PC-10 — `principle_library.py` may close U-05 without a recorded decision

**Potential contradiction.**

`VER2_RETIREMENT_MATRIX` §8 records U-05 — what proposes candidates in Stage 02 —
as an open research question, states `KnowledgeProvider` is "a boundary,
deliberately unimplemented", and warns it "must not be closed by importing V1
cards or the root ASSY_NEW ontology". `INV-016` lists U-05 among what it closes.

`ver3/assy_v3/knowledge/principle_library.py` (180 lines) exists and, per its own
docstring, indexes mechanical principle families by function class and returns
"every family that performs it" to a stage. `capability_registry.py` (88 lines) is
"consulted by s02".

The library is not a V1 card import and not the root ontology, and it is indexed
by function class rather than product noun — which is the stated defence against
R-10. Whether that constitutes a legitimate answer to U-05 or an unrecorded
closure of it depends on whether any proposal authorises it.
`ARCHITECTURE_CHANGE_PROPOSALS.yaml` (not yet read) is the only place such an
authorisation could exist. **Deferred to the next read.**

### PC-11 — `FP-02`'s exempt path does not match where fixtures now live

**Potential contradiction, low severity, precise.**

`FORBIDDEN_LEGACY_DEPENDENCIES.yaml` forbids the pattern `BM-\d{3}` inside
`ver3/assy_v3`, exempting `ver3/benchmarks/`, `ver3/oracles/` and
`ver3/tests/fixtures/`. `ver3/tests/fixtures/` does not exist. The fixtures are
at `ver3/assy_v3/fixtures/responses/BM-001/…` — **inside the protected package**,
under directory names that are literal benchmark IDs.

Whether this trips the scan depends on whether it reads file contents or paths,
which is `test_no_legacy_imports.py` in P6. Recorded now because the exemption
list names a path that was never created, which means the exemption was written
for a layout that is not the layout in use.

### OBS-14 — `REBUILD_POLICY` and `REPOSITORY_LAYOUT` both describe a repository
### state that no longer exists

**Observation.** Not a defect in itself; it bears on which document is
authoritative for intent.

- `REBUILD_POLICY` §5: "BM-003 is currently a placeholder with no source request
  and no Oracle, and it therefore **blocks freezing any stage contract**." BM-003
  now has a 30-line frozen source request and a 14-file held-out Oracle.
- `REBUILD_POLICY` §8: "**BM-003's subject.** Deliberately unchosen." It is chosen.
- `REPOSITORY_LAYOUT` §1: `assy_v3/` is "THE PIPELINE. Empty of stage logic",
  listing only `providers/` beneath it (PC-06 in the scope document, now
  confirmed against the file itself).
- `REPOSITORY_LAYOUT` §3: "All ten are `draft`. None may become `frozen` while
  BM-003 is a placeholder."
- `REPOSITORY_LAYOUT` §5: "108 tests." Not yet counted.

The two governing documents therefore describe the repository as it was before
the single commit `b8da4dd` that created the entire pipeline (finding G-1). Both
are still nominated as governing. Which of them remains authoritative for
*intent*, and which is merely stale *description*, is a P1 question that the
proposal and readiness documents may settle.

### OBS-15 — `ENTITY_FAMILY_AUDIT` recorded two expressiveness gaps as
### prerequisites for S03

**Observation / Needs verification.**

`REPOSITORY_LAYOUT` §3: the family audit's findings are "recorded rather than
applied. Two families are `MERGE_CANDIDATE`, three are `PROVISIONAL`, and two
expressiveness gaps (**retention capture, assembly ordering**) need typed
relations before `s03` — none of which adds a family."

S03 is implemented. Retention and assembly ordering are both named in the audit's
S03 review list. Whether the typed relations were added before S03 was built is a
P2 question (`ENTITY_FAMILY_AUDIT.yaml`, `DESIGN_STATE_CONTRACT.yaml`) and a P4A
question (does the S03 output actually express retention responsibility and
assembly dependency, or only name them).

---

### ACP-001 is the only change proposal that has ever been recorded

**Observation, bearing on every drift finding.**

`ARCHITECTURE_CHANGE_PROPOSALS.yaml` contains exactly one proposal. ACP-001
(2026-08-05, `ACCEPTED_AND_APPLIED`) renames a planned package path from
`ver3/assy3/` to `ver3/assy_v3/`. It records `semantic_change: false` and
justifies it: *"NO INVARIANT'S MEANING CHANGES. Every edit is to a path literal."*
It also states of the thirteen validators it renames: **"Every one is PLANNED.
None exists yet, so nothing was renamed on disk and no test changed behaviour as a
result of this proposal."**

That was accurate on 2026-08-05. The pipeline was committed on 2026-08-07.
No proposal exists for anything that happened in between. The file is the sole
authorisation channel the standing authority recognises, so for every drift
recorded in this log the answer to *"was it authorised?"* is the same: **no
recorded proposal exists.** Whether a proposal was required in each case is a
separate question, deferred to the proposal and readiness documents.

### PC-10 (extended) — phase0 warns specifically against a knowledge base that
### answers "which mechanism", regardless of sourcing

**Potential contradiction, strengthened by direct quotation.**

`ARCHITECTURE_COMPREHENSION_CHECK` §C.13: *"`KnowledgeProvider` is a documented
boundary, not an implemented adapter. (Prevents re-creating Ver1's catalogue
dependence through a side door — **a knowledge base that answers 'which
mechanism' is a card library regardless of how well sourced it is**.)"*
§A.5 trap 1: *"If Ver3 ships a mechanism library and selects from it, Ver3
becomes Ver1 with better bookkeeping."*

`assy_v3/knowledge/principle_library.py` is a knowledge base consulted by S02
that returns principle families for a function class. Its own docstring argues the
defence: the index key is a *physical function class*, not a product noun, so it
cannot encode "a box has a hinge" (R-10 at product scale).

A second, independent tension: `PIPELINE_GEOMETRY_AND_INFORMATION_PLAN` §5 names
a **different** knowledge base for S02 — *"The micro-oracles are the KB:
`guided-slider`, `rotary-to-linear-engagement`, `latch-retention`."* Those live
under `ver3/oracles/`, which is a **BLOCKING** forbidden path root for `assy_v3`.
The intended KB is therefore unreachable from the pipeline by the boundary rule,
and a different KB was written instead. §11 R-6 also records that the
micro-oracles as a KB are *unvalidated*.

Not resolved. `principle_library.py` must be read completely in P5, and the
proposal and readiness documents may address it.

### PC-12 — the migration plan's own ordering was not followed, and its
### step 7 was reached anyway

**Potential contradiction. Each line verified against the repository.**

`PIPELINE_GEOMETRY_AND_INFORMATION_PLAN` §10 gives a seven-step plan,
"deliberately minimal, and ordered so that each step is verifiable before the
next", ending: *"7. **Then, and only then, begin S03** — the stage that must
change most."* S03 and S04 are implemented.

| step | required | state on disk |
|---|---|---|
| 1 | Fix `EXE-BM003-01/poses.yaml` (does not parse) and add a CI check that every `*.yaml` under `ver3/` parses | **NOT DONE.** The file still raises `ParserError` ("while parsing a block mapping"). No repo-wide YAML-parse check exists; the CI job runs the meta suite, an import check and a stages-absence check only |
| 2 | Add `BlockingRelation`, `DOFDisposition`, `AssemblyPlan` to `DESIGN_STATE_CONTRACT.yaml`; add `EnvelopeConstraint` under s05; assign ownership in `STAGE_OWNERSHIP_MATRIX.yaml` | **NOT DONE under these names.** None of the four strings occurs in `DESIGN_STATE_CONTRACT.yaml`, `STAGE_OWNERSHIP_MATRIX.yaml`, any of S01–S04's contracts, or any file under `assy_v3/`. `EvidenceRouteDecision` likewise occurs nowhere |
| 3 | Add the invalidation cone to `STAGE_PATCH_CONTRACT.yaml` and `run_id` to the artifact rules | **DONE.** Both fields are present, and the contract's prose cites the BM-003 R5 lift-only failure as its reason |
| 4 | Write the six downstream-sufficiency probes **before any stage** — "`STAGE_PROGRESSION_CONTRACT` step 6 already mandates them; they do not exist" | **NOT DONE.** No probe file exists. The only `sufficiency` hits under `ver3/` are the phrase inside `freeze_gate.py`/`test_freeze_gate.py` and an unrelated CAD validator |
| 5 | Retro-fit the three CAD references as probe fixtures by hand-authoring the S03/S04 outputs that would have produced them — *"**This step is the highest-value item in the plan** and requires no stage implementation at all"* | **NOT DONE.** `assy_v3/fixtures/responses/` holds `s01`/`s02` only, for BM-001/2/3. No `s03` or `s04` fixture exists for any case (OBS-9) |
| 6 | Author the Scout rules as a contract before any exploratory CadQuery | **PARTIAL — needs verification.** The token `scout` occurs in `S07_CONTRACT.yaml` and `DESIGN_STATE_CONTRACT.yaml`. Whether the five §8 rules are present is a P2 read |
| 7 | *"Then, and only then, begin S03"* | **DONE** — S03 (979 lines) and S04 (687 lines) are implemented and have produced live output on six cases |

**Needs verification, not concluded:** step 2 was checked by name. The contracts
may express the same engineering content under different names, and P2's complete
read is what settles it. What is established now is that the four names the plan
specifies do not appear anywhere, and that no change proposal records a decision
to express them differently.

### PC-13 — two entity families are required by stage contracts, defined by no
### contract, owned by no stage, and produced by no code

**Potential contradiction. Verified by name search; scope of the search stated.**

`BodyHypothesis` and `PhysicalInteractionHypothesis` are named in
`PIPELINE_GEOMETRY_AND_INFORMATION_PLAN` §5 as new families **S02 owns**, and the
S02→S03 row of the §6 information matrix makes them the minimum sufficient
hand-over: *"S03 needs body hypotheses with roles; interaction hypotheses;
obligations per candidate; evidence-route classification"*, with the stated
failure if absent being *"S03 invents the mechanism."*

On disk each string occurs exactly twice: once in `S02_CONTRACT.yaml` and once in
`S03_CONTRACT.yaml`. Neither occurs in `DESIGN_STATE_CONTRACT.yaml`, in
`STAGE_OWNERSHIP_MATRIX.yaml`, or in any `.py` file under `ver3/assy_v3/`.

So a consumer contract requires them, a producer contract mentions them, the
representation does not define them, the ownership matrix does not assign them,
and no implementation emits or reads them. Whether S03 consequently invents the
mechanism — the failure the matrix predicts — is exactly a P4A question and is
**not** answered here. The prior audit reached a conclusion about these two
families; that conclusion is not consulted.

---

## Carried forward from scope construction

PC-01 (CI fails if `assy_v3/stages` exists — it does) · PC-02 (report says S04 not
implemented; it is) · PC-03 (source freeze PENDING vs FROZEN) · PC-04
(`production_pipeline_code_exists: false`) · PC-05 (two `window_report.json`) ·
PC-06 (**confirmed** against `REPOSITORY_LAYOUT` §1) · PC-07 (HEAD claims to make
the S03 contract authoritative without touching it) · G-1..G-3 (single-commit
architecture; three usable diffs) · OBS-1..OBS-13.

**Nothing above is resolved. Package 1 continues.**
