# Interruption recovery report

The CAD-1 run was interrupted part-way through the second executable reference,
leaving a dirty worktree on top of a good commit. This records what was found,
what was kept, what was repaired, and why nothing was thrown away.

## Baseline

| | |
|---|---|
| Branch | `ver3-cad-positive-reference-pilot` |
| Committed HEAD | `37957f59833126d233431d7965e4bd27ea1a80a2` |
| Remote at same commit | yes — verified before any work |
| Files modified outside `ver3/cad_validation/` | none |
| `git diff --check` | clean |
| Environment | `~/.venvs/ver3cad` — Python 3.8.10, all 15 pins match `requirements-cad.txt` exactly |

The activated shell interpreter (`/usr/bin/python3`) has no CadQuery at all, so
every command below used the locked interpreter explicitly.

## The interrupted task

EXE-BM001-01 was complete and committed. Work then continued on two fronts:

1. extracting the shared validation engine into `tools/valcore.py` so the second
   reference would not duplicate ~450 lines of it, and
2. authoring EXE-BM001-02.

The interruption landed after the extraction was working and after
EXE-BM001-02's build and contract files were written, but before EXE-BM001-02
had a validator.

**Resume point:** write `EXE-BM001-02/validate.py` and run the chain.

## Classification of every dirty path

### `GENERATED_REPRODUCIBLE` — regenerated outputs, no semantic change

| Path | Finding |
|---|---|
| `EXE-BM001-01/bolt.step` | bytes differ, geometry identical |
| `EXE-BM001-01/closure.step` | bytes differ, geometry identical |
| `EXE-BM001-01/enclosure.step` | bytes differ, geometry identical |
| `EXE-BM001-01/pin.step` | bytes differ, geometry identical |
| `EXE-BM001-01/model.step` | bytes differ, geometry identical |

**These are not geometry changes.** The committed and worktree STEP files were
both re-imported and compared on volume:

```
file          committed mm3   worktree mm3        delta
bolt            2513.274123    2513.274123     0.00e+00
closure        43598.651223   43598.651223     0.00e+00
enclosure      94247.266221   94247.266221     0.00e+00
pin             1050.234424   1050.234424      0.00e+00
model         141409.425991  141409.425991     0.00e+00
```

The byte difference is one line of the STEP header:

```
< FILE_NAME('Open CASCADE Shape Model','2026-08-03T21:22:00',('Author'),(
> FILE_NAME('Open CASCADE Shape Model','2026-08-03T21:44:32',('Author'),(
```

An export timestamp. This is exactly why the pilot uses a semantic geometry
signature rather than a file hash as its reproducibility criterion — and the
strongest single piece of evidence is that
`validation/geometry_signature.json` is **byte-identical to the committed
version**: git does not list it as modified at all. Signature
`5586b96cc2e92e113a87ecb7180e8f8e2a3f820585c2a9d75fa6c8fdb13f2ee8`, four bodies,
same volumes, same bounding boxes, same critical dimensions, same state
transforms.

`solid_validity.json`, `interaction_report.json` and `render_report.json` are
also unmodified.

### `COMPLETE_INTENTIONAL` — changed on purpose, all strictly additive

Every difference in the seven changed reports was diffed key by key. No `status`
field anywhere changed value.

| Path | What changed | Why |
|---|---|---|
| `EXE-BM001-01/validate.py` | rewritten as a thin adapter over `valcore` | removes the duplication; same ROIs, same sampling, same predicates |
| `EXE-BM001-01/assembly.yaml` | `kind:` added to each step | the shared engine dispatches on it; ASM-01 previously relied on `direction: null` |
| `validation/build_report.json` | `notes` field added to each body | `valcore` records `Body.notes`; all four are `""` |
| `validation/reimport_report.json` | 5 × `step_sha256` | follows the timestamp above |
| `validation/assembly_report.json` | `seated_at_offset_mm` added; method wording | the engine supports steps that seat at an offset, which EXE-BM001-02 needs |
| `validation/motion_report.json` | `discriminates` added; `elapsed_seconds` | timing, plus an explicit flag the engine reads |
| `validation/predicate_report.json` | `blocking_probe` added; wording of 9 `measured` strings | new measurement, see below |
| `validation/checker_selftest.json` | 6 → 7 controls, all detected | new control CTL-07 |
| `validation/SUMMARY.json` | `run_seconds` 63.8 → 67.5 | timing |

The one substantive addition is the **retention blocking probe**. The committed
report asserted that the opening rotation "is not traversable before the lift"
without measuring it. It is now measured, and the new control CTL-07 exists to
make sure the measurement can fail.

That control immediately caught an overclaim of mine: I had assumed the bolt
blocks rotation from zero. It does not. Near the closed pose the closure's motion
at the bolt is almost entirely *along* the bolt axis, so the bore slides on the
shaft before it bears on it, and the declared 0.1 mm running clearances give
**0.75° of free play** before the block engages. Beyond that the rotation is
blocked at every probed angle; once released it is free at every probed angle.
The report now states the measured onset instead of an assumed one. The geometry
did not change — only the claim about it.

### `PARTIAL_RECOVERABLE` — kept and completed

| Path | Finding |
|---|---|
| `tools/valcore.py` | complete, intentional extraction — see below |
| `EXE-BM001-02/build.py` | complete; compiles; builds three valid solids |
| `EXE-BM001-02/parameters.yaml` | complete, 38 parameters |
| `EXE-BM001-02/manifest.yaml` | complete |
| `EXE-BM001-02/interactions.yaml` | complete, 13 interactions |
| `EXE-BM001-02/assembly.yaml` | complete, 5 steps |

### `INVALID_OR_TRUNCATED` — one file, repaired

| Path | Defect | Repair |
|---|---|---|
| `EXE-BM001-02/poses.yaml` | would not parse: `causal_probe:` was indented as a member of the `terminal_conditions` list instead of a top-level key | promoted to top-level `terminal_condition_causal_probe:`. No content was discarded. |

This was the only parse failure across 15 YAML and 11 JSON files. Every Python
file compiles. No file is zero-byte or truncated.

### `CACHE_OR_SCRATCH` — not staged

`__pycache__/` under `tools/`, `EXE-BM001-01/` and `EXE-BM001-02/`. Excluded by
`ver3/cad_validation/.gitignore` and by an explicit pathspec at staging time.

## `tools/valcore.py`

A **complete intentional extraction**, not an interrupted edit. It holds steps
1–7 and 9, which are identical in method for every reference; step 8 — what the
Oracle concludes — stays with each reference, because that is the part that
genuinely differs.

Checked against the constraints on shared validation code:

- **Computes, does not author.** No status literal is assigned without a
  comparison against a measured number.
- **Contact is not overlap.** `common_volume` and `min_distance` are separate
  queries and are reported separately. Overlap is never inferred from distance.
- **Rotation about an arbitrary line is untouched.** `valcore` does not
  reimplement it; it calls `cadval.rotation`, which retains the conjugated form.
- **No transient face indices.** Interactions are localized by declared
  axis-aligned regions and semantic body IDs.
- **Sampling limitation reported.** `motion_report.evidence_is_sampled` states
  that dense sampling is not a proof over the continuum.
- **Missing evidence is never PASS.** `NOT_EVALUABLE` is emitted when a region
  contains no geometry, and step 8 keeps `NOT_VERIFIED` / `NOT_EVALUABLE`.
- **EXE-BM001-01 is not weakened.** Same signature, same twelve PASS and one
  NOT_EVALUABLE, and the self-test went from six controls to seven.

### New: `tools/test_primitives.py`

Targeted self-tests for the shared primitives whose failure would corrupt *both*
references while still producing a clean-looking report. 29 checks, all passing,
each against a closed-form answer rather than another run of the same code:

- rotation about a line: axis fixed at every angle; closed-form 90° result;
  composition with its inverse; volume preserved; **and an explicit assertion
  that the naive three-argument `Location` does *not* fix the axis**, which pins
  the original bug so it cannot return unnoticed
- `common_volume`: exact known interpenetration; touching gives zero; disjoint
  gives zero; sub-tolerance penetration is still reported rather than rounded away
- `min_distance`: exact known gap; and the assertion that overlapping solids are
  *also* at distance zero — the reason both primitives must exist
- `clip`: exact clipped volume; empty region returns `None`; clipping genuinely
  restricts; region with an excluded cylinder is exact to 1e-4
- `geometry_signature` / `compare_signatures`: identical rebuild matches; a 1 µm
  change is caught; a changed critical dimension is caught even when the solids
  are identical; a changed motion record changes the hash
- STEP and BREP round trips preserve volume and validity
- translation, `Body.moved` identity preservation

One finding came out of writing them: `cadval.bbox_of` returns a box **inflated
by ~1e-7 mm per face**, because OCCT's `Bnd_Box` carries a default gap. It is
deterministic and well inside `compare_signatures`' 1e-6 tolerance, so it was
documented and pinned rather than removed — removing it would change every
recorded signature for a tenth-of-a-micron cosmetic gain, including the committed
one. No geometric claim uses `bbox_of`; overlap and clearance go through the
exact primitives.

## EXE-BM001-01 revalidation

Rerun end to end on the locked interpreter after all of the above:

```
1 build            4 bodies          5 motion           PASS
2 solid validity   PASS              6 interactions     PASS
3 re-import        PASS              7 assembly         PASS
4 signature        PASS  5586b96c…   8 predicates       PASS  {PASS: 12, NOT_EVALUABLE: 1}
                                     9 render           PASS  20 images
  checker self-test PASS  7/7        overall: PASS      findings: 0
```

Independent rotation-axis fixed-point check: max deviation **1.421e-14 mm**.
`SUMMARY.json` is self-consistent and its signature agrees with
`geometry_signature.json`.

**The committed EXE-BM001-01 baseline remains valid.**

## What was not done

Nothing was reset, cleaned, stashed, checked out over, or restored. No
uncommitted work was discarded. The only file whose content was altered for
correctness rather than regeneration is `EXE-BM001-02/poses.yaml`, and that was a
repair of an indentation defect, not a rewrite.
