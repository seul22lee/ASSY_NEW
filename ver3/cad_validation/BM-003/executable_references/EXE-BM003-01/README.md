# EXE-BM003-01

One positive executable CAD reference for BM-003: a compact folding desk stand,
built as exact OpenCascade B-rep solids through CadQuery.

> ## ⚠ VALIDATION STATUS: CERTIFICATION DEFERRED
>
> | field | value |
> |---|---|
> | development / fast validation | **PASS** |
> | full-sampling reference validation | **NOT COMPLETED** |
> | reason | execution environment wall-time limit |
> | engineering failure observed before interruption | **none** |
> | final positive-reference certification | **DEFERRED** |
> | manifest | **not generated** |
>
> The full-sampling run reached the end of step 7 with every measurement passing
> and was interrupted during finalisation. Three partial artifact sets exist on
> disk and none is a clean single-run set, so no manifest may be built from any
> of them. Machine-readable detail: [`VALIDATION_STATUS.yaml`](VALIDATION_STATUS.yaml).
>
> Do not read any `SUMMARY.json` in this directory as the reference's verdict.

> **This is an Oracle-aware executable evaluator fixture.** It is not a
> production ASSY result, not a golden design, not a mandatory mechanism, not a
> training or few-shot input, and not evidence that every realization family the
> BM-003 Oracle admits is executable. Its intended completion claim is
> `ONE_POSITIVE_EXECUTABLE_REFERENCE_VALIDATED`; that claim is currently
> **DEFERRED** and not made. See [`GOVERNANCE.yaml`](GOVERNANCE.yaml) and
> [`VALIDATION_STATUS.yaml`](VALIDATION_STATUS.yaml).

## The mechanism in one paragraph

A hub carries three hinged legs. Each leg has a heel that rises when the leg is
folded back. A captive ring on the hub column has three arms; lowered, each arm
sits a small gap above one heel, so folding back is stopped by hard geometric
interference. The ring cannot be turned while it is down, because ribs on the
column occupy keyways in its bore — so releasing takes a deliberate **lift and
turn**. Nothing can leave: the ring is trapped between the pedestal and the ring
captor, the captor and the top support are bayoneted to the column, and each
hinge pin is trapped between its own head and its turned end bar.

Declared state-maintenance class: **SMC-KINEMATIC_BLOCK**.
Declared realization class: **RIGID_MULTI_BODY**. Ten bodies.

## Files

| file | what it is |
|---|---|
| `parameters.yaml` | every dimension, with purpose, range and provenance. All fixture choices; none traceable to the source. |
| `build.py` | the authoritative design source with `parameters.yaml`. Builds the ten B-rep solids and defines the pose law. |
| `poses.yaml` | configurations, degrees of freedom, the six motion segments, the operational cycle |
| `assembly.yaml` | fifteen ordered steps with insertion directions and the relations each activates |
| `interactions.yaml` | thirty-four declared interactions with kinds and nominals |
| `validate.py` | the validator: engine steps 1–7 and 9, the mechanism evidence, seventeen negative controls, and step 8 |
| `expected_evaluation.yaml` | what the Oracle was expected to conclude, written before the run |
| `actual_evaluation.json` | what it did conclude |
| `geometry_signature.json` | the accepted geometry signature |
| `DESIGN_AND_OPERATION_RATIONALE.md` | how it works and every revision the exact B-rep forced |
| `GOVERNANCE.yaml` | reference class, what is and is not claimed, dynamics decision |
| `SELF_AUDIT.md` | twelve questions answered against what is actually here |
| `review_views.py`, `make_videos.py` | review media, rendered from these same solids |
| `VALIDATION_STATUS.yaml` | **authoritative status record — read first** |
| `validation/` | measurements as JSON. Currently a PARTIAL set; see the status record |
| `validation_interrupted_*/` | quarantined output of interrupted runs, kept for diagnosis, never a manifest source |
| `screenshots/` | rendered views |
| `export_artifacts.py` | the BREP → STEP export pass, in the required order |
| `make_manifest.py` | rebuild-determinism check and artifact manifest. **Not yet run** — no manifest exists |

## Running it

The toolchain is the one recorded in `ver3/cad_validation/TOOLCHAIN_LOCK.yaml`:
CadQuery 2.4.0 on cadquery-ocp 7.7.0, Python 3.8.

```
python validate.py                # full run
BM003_FAST=1 python validate.py   # reduced sampling, for iteration only
python review_views.py            # still images
python make_videos.py             # the two animations
```

`validation/SUMMARY.json` carries a run's own verdict — but see
`VALIDATION_STATUS.yaml` first: the sets currently on disk are partial and one of
them mixes two runs. `BM003_FAST=1` reduces sampling density only; it skips no
computation and disables no predicate, but it does not examine the two declared
refinement windows at the ends of each motion segment, so a fast PASS is not
admissible as the reference's recorded evidence.

## What the evidence establishes

Relations, measured by the kernel on the exact solids. **Every item below was
measured under FAST sampling and, for steps 1–7, also under full sampling before
the run was interrupted. None is yet certified by a complete full-sampling run —
see `VALIDATION_STATUS.yaml`.**

- fold-back from deployed is obstructed, for each of the three legs, short of stored;
- after the lift and the turn the whole fold path is clear;
- lifting without turning leaves the fold obstructed part way, so both motions are needed;
- the ring cannot be turned at the locked height and turns freely once lifted;
- swinging a leg past deployed is stopped;
- every body that could leave has a measured blocked escape direction and a named blocker;
- three ground contacts on a common plane bound a non-zero area;
- the stored envelope is smaller than the deployed one in x, in y and in maximum radial extent;
- every declared running pair stays engaged at every sample of the whole cycle;
- fifteen insertions and five bayonet turns are interference free.

## What it does not establish

Load capacity, disturbance tolerance, material, wear, lifetime, manufacturing
process, user effort, whether the footprint is large enough for anything, whether
the declared clearances are acceptable, and whether a bayonet could be turned
back by handling. Each is recorded in `actual_evaluation.json` against the
ambiguity that keeps it open.

No dynamics was run: `DYNAMICS_NOT_REQUIRED_FOR_THIS_REFERENCE`. Every question
this reference answers is about whether a rigid-body configuration exists.
