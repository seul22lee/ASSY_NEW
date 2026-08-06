# Benchmarks

Three benchmarks: BM-001, BM-002, BM-003. Each is a source request plus a
descriptor, and nothing else that production code may read.

## What lives here, and what deliberately does not

```
ver3/benchmarks/BM-00N/
    descriptor.yaml     identity, scope, and where the pieces live
    source/request.txt   the raw request  -- read by s01 only, and only at run time
    runs/                pipeline output, one directory per run_id
    evaluations/         evaluator output, one directory per result_id
```

The **Oracle does not live here.** It lives in `ver3/oracles/`, is authored
independently, and is frozen before any source-only run. Keeping it in a separate
tree is what lets `ver3/oracles/` be listed as a BLOCKING forbidden path root in
`ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml` without also blocking the request text
the pipeline legitimately needs.

The **positive executable CAD references do not live here either.** They are in
`ver3/cad_validation/`, are development and evaluator-validation fixtures, and
are never production inputs, retrieval sources, templates or golden geometry.

## The rule that makes a benchmark meaningful

A run reads `source/request.txt` and nothing else from this tree. Production code
must not branch on which benchmark is running — `FORBIDDEN_LEGACY_DEPENDENCIES`
pattern FP-02 forbids `BM-\d{3}` in `assy_v3` for exactly that reason (INV-015,
retirement row R-14). A pipeline with a benchmark-shaped special case is not
being measured by the benchmark; it is being measured against itself.

`ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml` step 8 requires all three to
demonstrate downstream sufficiency before any stage contract is frozen. Three,
not two — one benchmark proves a stage works on one problem, and the third is
what makes an accidental fit visible.
