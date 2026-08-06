# REBUILD_POLICY

The Ver3 pipeline is a rebuild, not a refactor. Ver2 is frozen, read-only legacy.

This document is the governing statement for that rebuild. Where it and a
contract disagree, this document loses to `ver3/phase0/ARCHITECTURE_INVARIANTS.yaml`
and `ver3/phase0/VER2_RETIREMENT_MATRIX.md`, which were frozen before it and are
the standing authority.

---

## 1. The six rules

These are the constraints the rebuild operates under. They are stated first
because everything downstream is a consequence of them.

1. **All Ver2 pipeline code is frozen, read-only legacy.** It may be read by a
   human. It may not be executed, imported or adapted by Ver3.

2. **No Ver2 stage, schema, fallback, alias, mechanism card, rendered-sheet
   authority or CAD default may be imported into the new pipeline.** The list is
   specific because each item is a named defect in the retirement matrix, not a
   general suspicion about old code.

3. **No compatibility adapters without explicit approval.** An approval is an
   entry in `approved_exceptions` in `FORBIDDEN_LEGACY_DEPENDENCIES.yaml`,
   carrying an approver, a scope, an expiry and a removal plan. The list is empty
   and empty is the expected steady state.

4. **Positive executable CAD references and Oracles are evaluation artifacts, not
   production inputs.** Both trees are BLOCKING forbidden path roots for
   `assy_v3`.

5. **Only S01 may read raw source text.** Every later stage reads DesignState.

6. **No Stage logic is implemented in the foundation task.** Contracts and
   boundaries only.

### Why rule 3 is the one that decides the outcome

An adapter is always the cheapest next step and always the wrong one. It carries
a Ver2 structure into Ver3 wearing a Ver3 name, and once one exists, the argument
for the second is that the first already works. The retirement matrix's 32 rows
are what a decade of that reasoning produces. The approval requirement is not
bureaucracy; it is the only point at which the cost is visible before it is paid.

### Why rule 5 is not merely tidiness

Two stages reading the same sentence produce two interpretations of it, and
nothing in a typed state can tell which one a downstream entity depends on.
Single-reader is what makes interpretation a recorded, attributable act
(INV-002). The provenance methods `SOURCE_VERBATIM` and `SOURCE_DERIVED` are
available only to `s01` for the same reason, and the contract-reference test
checks it structurally.

---

## 2. The three artifacts that must never be conflated

This is the distinction the whole evaluation rests on. All three describe what a
design must satisfy. They differ in **who wrote them**, **when they were fixed
relative to the run**, and **who may see them**.

| | Hidden Benchmark Oracle | Runtime Generated Assurance Package | Positive Executable Reference |
|---|---|---|---|
| Authored by | a human, independently | the pipeline, from its own state | a human, as a fixture |
| Fixed | before any source-only run | during the run | before the benchmark is used |
| Lives at | `ver3/oracles/` | the run output directory | `ver3/cad_validation/` |
| Visible to production | **never** | it *is* production output | **never** |
| Defines success | **yes** | no | no |

**The Oracle** states what must be true of a run. It is authored independently and
frozen before the run. A stage that reads it is reading its own answer key, which
stops the benchmark measuring whether the pipeline can design and starts it
measuring whether the pipeline can copy.

**The assurance package** states what the run itself claims — established and
unestablished. It is generated only from the source request, the accumulated
typed DesignState, declared engineering knowledge, deterministic tool results and
the run's own revision history. It may legitimately resemble an Oracle in
structure and depth; that resemblance is the goal. What it must never do is
*define* success, because it was written by the same process whose success is in
question, and a criterion authored after seeing the result is not a criterion.

**The positive executable reference** is a human-built design that is known to
work. Its purpose is to prove the *evaluator* works: that it can recognise a good
design, and that a validator's negative controls can fail. It is never a
production input, retrieval source, template or golden geometry, and similarity to
it is never a scoring input. It is one valid design; scoring against it would
convert "did the pipeline solve the problem" into "did the pipeline reproduce this
solution", penalising every correct answer that differs.

### Naming

In production code the artifact is `GENERATED_DESIGN_ASSURANCE_PACKAGE`, or
equivalently `RUNTIME_ASSURANCE_RECORD`. It is **never** called an Oracle inside
`assy_v3`. The word appearing there as an identifier would mean the hidden answer
key had reached the system being judged, so the rule is enforced by test rather
than left to review — the point of the naming rule is that a leak becomes visible
at grep depth.

Contract: `ver3/contracts/GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml`.

---

## 3. The package is a projection, not a report

The assurance package is a **projection of the cumulative typed DesignState**. It
has no authoring channel of its own. Three things follow, and each of them rules
out a specific failure:

- **Not a second design world.** If the package could hold a fact the DesignState
  does not, the two could disagree, and the artifact would stop being evidence
  about the run.
- **Not a manually assembled report.** A hand-written narrative can describe a
  design the pipeline never produced. Every element must trace to an entity.
- **Not a final rendering step.** A terminal report can only show what survived.
  The requirement is *progressive* construction — S01 through S12 — so that what
  was tried, what was dropped and what was never checked all remain visible.

The practical consequence: the projection is built **before S01**, not last. Built
last it becomes a report generator, and a report generator invents structure the
stages never produced. Built first, every stage has somewhere to contribute, and
a section that is empty is empty because the state is empty.

The package must be able to show, by S12: source scope, interpretation with stated
and inferred separated, freedoms, open questions, obligations, the full candidate
space, rejected alternatives with real reasons, architecture, every interaction
classified, mobility including forbidden DOF, operation, witnesses, the
realization map, parameters with units, the construction program, the solver
record, as-built geometry, the verification plan, negative controls with measured
detection, evidence with fidelity, what the evidence *cannot* support, coverage
gaps, unmerged contradictions, per-requirement evaluation with scope, explicitly
excluded claims, obligation closure, failure attribution, revision history, human
review questions, provenance, the execution record and the determinism record.
Thirty-four items, enumerated as PKG-01..PKG-34.

A required item with nothing to report is emitted **empty with a stated reason**.
Omitting it is `CONTRACT_INCOMPLETE`. "We found no ambiguities" and "we never
looked for ambiguities" are different claims, and only the second is a defect.

---

## 4. Statuses: the failure this architecture exists to prevent

The recurring Ver2 failure was never a wrong status. It was a status that could
absorb a situation it did not describe — missing knowledge became INFEASIBLE
(R-27), a crashed check became a negative result, a proxy check became a PASS.

`ver3/contracts/STATUS_SEMANTICS.yaml` gives every status an explicit
`never_means`, and names twelve forbidden collapses (C-01..C-12) directly.

Twelve execution statuses describe the **run**, never the **design**:
`SUCCESS`, `PROVIDER_RATE_LIMIT`, `PROVIDER_QUOTA_EXHAUSTED`,
`PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`, `RESPONSE_TRUNCATED`,
`RESPONSE_PARSE_FAILURE`, `SCHEMA_FAILURE`, `CONTRACT_INCOMPLETE`,
`MODEL_CAPABILITY_FAILURE`, `SAFE_REJECTION`, `FALSE_ACCEPTANCE`.

Two of them carry the architecture's whole point:

- **`SAFE_REJECTION`** — the run declined a claim it could not support. This is
  correct behaviour and is never penalised. A benchmark that penalises it produces
  a pipeline that overclaims.
- **`FALSE_ACCEPTANCE`** — the run claimed something it had not earned. The most
  serious defect class. Every other rule here is shaped to make it detectable.

The pipeline will run against real providers, including free-tier APIs with hard
rate limits, small quotas, aggressive timeouts and low output caps. Those are
**normal operating conditions**, not exceptions. A degraded run reports itself as
degraded; it never reports itself as a worse design.

---

## 5. How stages get built

`ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml`, eight steps per stage:

1. Define the stage contract.
2. Define what the stage must **refuse** to do — before implementing it, because
   a prohibition invented afterwards usually describes what the code already does.
3. Implement.
4. Run source-only on BM-001, BM-002 and BM-003.
5. Check contract completeness.
6. **Demonstrate downstream sufficiency** — the next stage can consume the output
   with no default, no alias, no fallback, no re-reading of the source, no
   benchmark special case.
7. Verify no leakage and determinism.
8. Freeze — **only** after steps 4–7 pass on all three benchmarks.

Step 6 is the real gate. Schema validity is cheap: a stage can emit a well-formed
structure that is substantively empty, and the downstream stage then compensates
with a default. Every retirement row R-01..R-32 is a compensation that was made
because the upstream output was insufficient and nothing forced the issue back
upstream.

Freezing on two benchmarks is what makes an accidental fit invisible. BM-003 is
currently a placeholder with no source request and no Oracle, and it therefore
**blocks freezing any stage contract** — recorded in its descriptor and checked by
`test_benchmark_skeleton.py`, so the gate cannot quietly appear passable.

---

## 6. Enforcement

`ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml` is data consumed by a test, not
documentation that happens to describe a rule.

| Test | Enforces |
|---|---|
| `test_no_legacy_imports.py` | rules 1–4: import roots, path roots, symbols, patterns, adapters |
| `test_contracts_parse.py` | every contract parses and declares its authority |
| `test_contract_references.py` | the nine contracts agree with each other |
| `test_status_semantics.py` | the enum and the status contract cannot drift |
| `test_no_stage_implementation.py` | rule 6, and the naming rule |
| `test_benchmark_skeleton.py` | Oracle and reference stay outside the benchmark tree |

Run: `python3 -m unittest discover -s ver3/tests/meta -t .`
CI: `.github/workflows/ver3-boundaries.yml`.

Stdlib-only, deliberately — a boundary check that needs an environment built
first is a boundary check that gets skipped when the environment breaks.

---

## 7. What this policy does not settle

Recorded rather than resolved, because resolving them quietly is the failure mode
this whole document is about.

- **`assy_v3` vs `assy3`.** `ver3/phase0/ARCHITECTURE_INVARIANTS.yaml` names the
  package `ver3/assy3/` in its `planned_validator` paths. The rebuild task
  specified `assy_v3`, and `ver3/assy_v3/` is what exists. It satisfies INV-016
  either way. The invariants file is frozen and wins on conflict, so the divergence
  must be reconciled through that file's own change process rather than by editing
  it here.
- **U-02, Ver1 host templates.** Undecided in the retirement matrix. Not
  admissible to `assy_v3` until decided; `HostTemplate` is a forbidden symbol in
  the meantime.
- **BM-003's subject.** Deliberately unchosen. Picking it inside this task would
  make it a benchmark shaped by the architecture it is meant to test.
- **Prompt-level leakage (AL-03).** No prompt, template, fixture or retrieval
  corpus may embed Oracle content. This is a review obligation plus the file-access
  audit; it is not fully automatable, and claiming otherwise would be worse than
  saying so.
