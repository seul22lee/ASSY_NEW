# REPOSITORY_LAYOUT

Where everything lives in `ver3/`, what may read what, and what gets built next.

---

## 1. Layout

```
ver3/
    REBUILD_POLICY.md                  governing statement for the rebuild
    REPOSITORY_LAYOUT.md               this file
    RETIREMENT_MATRIX.yaml             machine-readable legacy classification
    FORBIDDEN_LEGACY_DEPENDENCIES.yaml data consumed by the boundary test
    __init__.py                        namespace, so assy_v3 imports as a package

    phase0/                            FROZEN. The standing authority.
        ARCHITECTURE_INVARIANTS.yaml       INV-001..INV-018
        VER2_RETIREMENT_MATRIX.md          R-01..R-32, U-01..U-05
        ARCHITECTURE_CHANGE_PROPOSALS.yaml the only way a phase0 authority changes
        PHASE0_EVIDENCE_REPORT.md
        ARCHITECTURE_COMPREHENSION_CHECK.md

    contracts/                         ten contracts, all draft
        DESIGN_STATE_CONTRACT.yaml
        STAGE_PATCH_CONTRACT.yaml
        STAGE_OWNERSHIP_MATRIX.yaml
        STATUS_SEMANTICS.yaml
        PROVENANCE_CONTRACT.yaml
        MODEL_RUN_RECORD_CONTRACT.yaml
        BENCHMARK_RESULT_CONTRACT.yaml
        GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml
        STAGE_PROGRESSION_CONTRACT.yaml
        ENTITY_FAMILY_AUDIT.yaml           consumer justification for all 32 families

    assy_v3/                           THE PIPELINE. Empty of stage logic.
        __init__.py
        providers/                     boundary definitions only, no live calls
            __init__.py
            status.py                  the twelve execution statuses
            interfaces.py              provider, cache, replay, tool runner

    benchmarks/                        source requests and run output
        README.md
        SOURCE_FREEZE_REVIEW.md            consolidated review, all decisions PENDING
        BM-001/  BM-002/  BM-003/          ONE canonical layout, no exceptions
            descriptor.yaml
            source/request.txt             the only raw text a run reads
            source/source_manifest.yaml    common envelope + class-specific detail
            runs/  evaluations/
        BM-003/                            additionally:
            BM-003_SELECTION_CRITERIA.md   criteria + 3 briefs (subject now fixed)
            BM003_SOURCE_AUTHORING_RECORD.md
            BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md

    tests/meta/                        boundary and contract enforcement
        _paths.py
        test_no_legacy_imports.py
        test_contracts_parse.py
        test_contract_references.py
        test_status_semantics.py
        test_no_stage_implementation.py
        test_benchmark_skeleton.py
        test_package_path.py
        test_entity_family_audit.py

    oracles/                           FROZEN. Hidden answer keys.
    oracle_tools/                      FROZEN. Oracle tooling.
    cad_validation/                    Positive executable references.
```

---

## 2. Who may read what

This is the part worth getting right. Three trees are unreachable from the
pipeline, and two of them are unreachable for reasons that are easy to argue
away in the moment.

| Tree | `assy_v3` may read | Evaluator may read | Why |
|---|---|---|---|
| `phase0/` | no | yes | Governing prose; not a runtime input |
| `contracts/` | as schema definitions | yes | The contracts the code implements |
| `benchmarks/*/source/request.txt` | **s01 only, at run time** | yes | The request is the legitimate input |
| `benchmarks/*/source/source_manifest.yaml` | no | yes | Provenance and review state, not a runtime input |
| `benchmarks/*/descriptor.yaml` | no | yes | Branching on it is FP-02 / INV-015 / R-14 |
| `oracles/` | **never (BLOCKING)** | yes | An Oracle states what must be true of a run. Reading it is reading the answer key. |
| `cad_validation/` | **never (BLOCKING)** | yes | Positive references. Reproducing one is not designing. |
| `oracle_tools/` | never | yes | Evaluation tooling |
| repository root (`ontology/`, `data/`, `rules/`, `build/`, `outputs/`) | never | n/a | Separate KG project (INV-016) |

`ver3/oracles/` and `ver3/cad_validation/` are the two BLOCKING entries in
`FORBIDDEN_LEGACY_DEPENDENCIES.yaml`. Neither has an approved exception, and the
empty exception list is the expected steady state rather than a gap waiting to be
filled.

Legacy roots `/home/ftk3187/github/ASSY_Ver1.0` and `ASSY_Ver2.0` are outside this
repository and are forbidden as path literals and import roots alike.

---

## 3. Contract dependency order

Read them in this order; each assumes the ones above it.

```
ARCHITECTURE_INVARIANTS.yaml  (frozen authority)
  └── DESIGN_STATE_CONTRACT ........... what may exist
        ├── STAGE_OWNERSHIP_MATRIX .... who may create it, and what each stage owes the package
        ├── PROVENANCE_CONTRACT ....... where every value came from
        └── STAGE_PATCH_CONTRACT ...... the only way the state changes
              └── STATUS_SEMANTICS .... what every outcome means, and must not mean
                    ├── MODEL_RUN_RECORD_CONTRACT ......... provider and tool reality
                    ├── GENERATED_ASSURANCE_PACKAGE_CONTRACT  the projection
                    ├── BENCHMARK_RESULT_CONTRACT ......... what the evaluator writes
                    └── STAGE_PROGRESSION_CONTRACT ........ how stages get built and frozen
```

All ten are `draft`. None may become `frozen` while BM-003 is a placeholder —
checked by `test_benchmark_skeleton.py` and again by `test_entity_family_audit.py`.

`ENTITY_FAMILY_AUDIT.yaml` sits beside `DESIGN_STATE_CONTRACT.yaml` rather than
under it: it is a review of that contract, and its findings are recorded rather
than applied. Two families are `MERGE_CANDIDATE`, three are `PROVISIONAL`, and
two expressiveness gaps (retention capture, assembly ordering) need typed
relations before `s03` — none of which adds a family.

---

## 4. Next implementation order

Nothing below is implemented. Each item is gated by the eight steps in
`STAGE_PROGRESSION_CONTRACT.yaml`.

### Phase 1 — the substrate, before any stage

1. **`assy_v3/state/`** — DesignState types from `DESIGN_STATE_CONTRACT`.
   Entity identity, instance identity, typed references, canonical serialization
   and the state hash. Everything else depends on this hash being stable.
2. **`assy_v3/provenance/`** — provenance records and chain walking. Built with
   the state, not after it: a value that enters the state without provenance
   cannot have it added retroactively with any credibility.
3. **`assy_v3/patch/`** — StagePatch, its validator, atomic application, and
   rejected-patch retention.
4. **`assy_v3/status/`** — the remaining vocabularies (evaluation outcomes,
   solver, observable). Execution statuses already exist in `providers/status.py`.
5. **`assy_v3/assurance/`** — the projection. **Built here, before S01.** Built
   last it becomes a report generator, and a report generator invents structure
   the stages never produced.
6. **`assy_v3/providers/`** — implementations behind the existing interfaces:
   bounded retry, explicit fallback, cache with recorded hits, offline replay.
   Free-tier limits are normal operating conditions, not error handling.
7. **Harness** — run directory layout, the file-access audit that makes an
   Oracle-leak claim checkable, and the benchmark runner.

### Phase 2 — stages, strictly in order

`s01 → s02 → s03 → s04 → s05 → s06 → s07 → s08 → s09 → s10 → s11 → s12`

Forward order is forced: each stage's gate is its *successor's* needs, so building
out of order means gating against a consumer that does not exist yet.

Creating `assy_v3/stages/` is the act that starts this phase, and
`test_no_stage_implementation.py` fails the moment it appears.

### Blocking prerequisite

**BM-003 must be defined** — a frozen source request and an independently authored
Oracle, frozen *before* its first source-only run. Until then no stage contract
can be frozen, because the freeze rule requires all three benchmarks and two
benchmarks cannot distinguish a general stage from one that happens to fit.

---

## 5. Running the checks

```
python3 -m unittest discover -s ver3/tests/meta -t .
```

Requires PyYAML and nothing else. CI: `.github/workflows/ver3-boundaries.yml`.
108 tests.
