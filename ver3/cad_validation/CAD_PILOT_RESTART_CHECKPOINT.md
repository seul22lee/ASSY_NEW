# CAD-1 restart checkpoint

Written at a deliberate pause for a machine shutdown, mid-way through
EXE-BM001-01. Nothing here is a result; it is a record of exactly where the work
stopped so it can resume without re-deriving anything.

## Position

| | |
|---|---|
| Branch | `ver3-cad-positive-reference-pilot` |
| HEAD before this checkpoint commit | `83fc12d46ad8c5fad36afcfe5b6e916822a41118` |
| Phase | CAD-1 positive realizability pilot |
| State | `BM001_EXECUTABLE_REFERENCE_PILOT_IN_PROGRESS` — **not** `..._READY` |

## What exists

### Toolchain and plan
- `ver3/cad_validation/TOOLCHAIN_LOCK.yaml` — verified versions, platform, capability probes, and now a `recreation_contract` section.
- `ver3/cad_validation/requirements-cad.txt` — pinned lock file (new).
- `ver3/cad_validation/tools/create_env.sh` — env builder taking a caller-supplied path (new).
- `ver3/cad_validation/CAD_VALIDATION_PLAN.yaml` — 9-step chain, plus a new `claim_fidelity` section.
- `ver3/cad_validation/tools/cadval.py` — shared build/measure library.

### BM-001
- `source_only_packet/` — 7 files, rebuilt as a **strictly rank-1** packet (see below).
- `evaluator_only/` — packet manifest, `S2_SOURCE_SILENCE.md`, README.
- `demonstrations/README.md` — directory intentionally empty.
- `reviews/REFERENCE_SELECTION.yaml` — **frozen before any geometry**, as required.

### EXE-BM001-01 — partially built
| File | State |
|---|---|
| `parameters.yaml` | complete |
| `build.py` | complete; builds and prints body stats |
| `manifest.yaml` | complete |
| `poses.yaml` | complete |
| `assembly.yaml` | complete |
| `interactions.yaml` | complete — 13 declared interactions |
| `validate.py` | **not written** |
| `model.step` / `model.brep` | not exported |
| `validation/*.json` | none |
| `screenshots/` | none |
| `expected_evaluation.yaml` | not written |

## Latest build result

`python build.py`, all four bodies:

```
BODY-ENCLOSURE   valid=True  vol=  91630.201 mm^3  bbox=(120.00 x 90.00 x 56.00)
BODY-CLOSURE     valid=True  vol=  43037.583 mm^3  bbox=(120.00 x 95.70 x 15.00)
BODY-PIN         valid=True  vol=   1050.234 mm^3  bbox=( 77.80 x  7.00 x  7.00)
BODY-BOLT        valid=True  vol=   2513.274 mm^3  bbox=( 16.00 x 16.00 x 32.00)
```

`BRepCheck_Analyzer` passes on all four. **That is the only validation that has
been run.** No interference, motion, assembly, re-import, determinism or
predicate check has executed yet. Nothing in this pilot is claimed to pass.

## The rotation-axis bug that was corrected

`cadval.rotation()` was:

```python
return cq.Location(cq.Vector(*axis_origin), cq.Vector(*axis_dir), degrees)
```

CadQuery's three-argument `Location(t, ax, angle)` is *translation `t`* combined
with *rotation about `ax` through the world origin* — not rotation about the line
through `t`. The intended hinge axis was therefore not fixed by the motion. It
was caught because the closure's bounding box came out 71.6 mm tall instead of
15 mm: the stop block, which is constructed in the open configuration and rotated
back, landed in the wrong place.

Fixed by conjugating with the origin translation:

```python
o = cq.Vector(*axis_origin)
spin = cq.Location(cq.Vector(0, 0, 0), cq.Vector(*axis_dir), degrees)
return cq.Location(o) * spin * cq.Location(o * -1)
```

Verified: a vertex on the axis maps to itself under `open_rotation(p, 110)`, and
the closure's rear extent is now 95.70 mm, matching the hand calculation for the
rotated-back stop block to 0.01 mm.

**This bug would have invalidated every motion result.** Any future edit to
`cadval.rotation` must re-run the axis-fixed-point check.

## The bolt_y / boss adjustment

`BODY-BOLT`'s knob (Ø16) centred at `bolt_y = 7.0` reached `y = -1.0`, overhanging
the enclosure's front face. Changed:

- `bolt_y`: 7.0 → **9.0**
- `bolt_boss_y1`: 12.0 → **16.0** (the Ø8.2 bore at y = 9 spans 4.9–13.1, so the
  boss had to grow to keep ~2.9 mm of material behind it)

Both bosses use the same parameters, so enclosure and closure moved together.
Rebuilt and re-checked after the change — the four volumes above are post-change.

## Exact next step on resume

Write `ver3/cad_validation/BM-001/executable_references/EXE-BM001-01/validate.py`,
implementing steps 1–9 of `CAD_VALIDATION_PLAN.yaml` against `build.py`:

1. build report
2. solid validity
3. STEP + BREP export and independent re-import
4. geometry signature and rebuild determinism (build twice, compare)
5. motion sampling — `M1_RELEASE` and `M2_OPEN`, pairwise `common_volume` at every
   sample, with refinement near the terminal angle
6. interaction classification against `interactions.yaml`
7. assembly path sampling per `assembly.yaml`
8. Oracle predicate evaluation
9. renders + human review checklist

Then the causal probe for the terminal condition: evaluate the model at angles
either side of 110° and show the common volume is zero before and positive after.
This is a measurement on the admissible model — it exports nothing and creates no
inadmissible artifact.

## EXE-BM001-02

**Not started.** No directory, no files. Its design is recorded in
`BM-001/reviews/REFERENCE_SELECTION.yaml`: a rigid captive sliding closure on
realized rails with terminal bounds, retained by a quarter-turn cam, three
bodies. That selection is frozen and must not be redesigned on resume.

## Environment

The run used a disposable virtualenv, **not** committed and not the reproduction
path:

```
/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/6f9fb2e4-bcd0-4d48-a59c-38efe85c40e5/scratchpad/ver3cad
```

That path will not survive the reboot. Recreate persistently with the committed
contract:

```bash
ver3/cad_validation/tools/create_env.sh ~/.venvs/ver3cad python3.8
~/.venvs/ver3cad/bin/python ver3/cad_validation/BM-001/executable_references/EXE-BM001-01/build.py
```

`create_env.sh` bootstraps pip, installs `requirements-cad.txt`, and runs a
B-rep kernel probe before reporting success. CPython 3.8 is required —
`cadquery-ocp 7.7.0` publishes cp38 wheels and the pinned set was verified only
there.

## Source-boundary correction — complete

The four corrections requested mid-run are done:

1. **`source_only_packet/` rebuilt as strictly rank-1.** S1 verbatim only; S2 and
   its interpretation removed; ambiguity IDs from other cases removed; every
   mechanism and topology name removed; artifact requirements reworded to body A
   / body B / intended interaction / terminal condition; no statement that any
   other CAD exists. A grep for `hinge|slider|flexure|snap|magnet|detent|pivot|bore|rim|knuckle|lid|reference design`
   over the packet returns nothing.
2. **S2 and excluded Oracle information moved outside the packet**, to
   `BM-001/evaluator_only/`, with a README stating it must not reach a
   Demonstration author.
3. **Pinned recreation contract added** — `requirements-cad.txt` and
   `tools/create_env.sh`, both recorded in `TOOLCHAIN_LOCK.yaml`.
4. **Claim fidelity phrased correctly** — `CAD_VALIDATION_PLAN.yaml`
   `claim_fidelity` lists what may reach PASS (geometry, kinematics, existence of
   an assembly ordering, existence of a load path) and what remains
   `NOT_VERIFIED` by construction (REQ-002/004 disturbance capacity, REQ-003
   effort, REQ-005 cost, REQ-007 ease, REQ-008 durability, REQ-006 envelope),
   with a reporting rule forbidding sentences that mix the two.

## Oracle files unchanged

No file under `ver3/oracles/`, `ver3/oracle_tools/` or `ver3/phase0/` was read
for modification or written in this run. `git status --short` over those three
paths is empty, verified immediately before this checkpoint commit. The Oracle
commit this pilot is pinned to remains
`83fc12d46ad8c5fad36afcfe5b6e916822a41118`.

## What is NOT claimed

This checkpoint asserts only that four B-rep solids build and are valid. It does
not assert that they do not interfere, that the motion is traversable, that the
assembly is realizable, or that any Oracle predicate passes. Those are the
unrun checks listed above.
