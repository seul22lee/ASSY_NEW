# ASSY human design review UI

An interface for inspecting what the pipeline actually did, so the mechanical
engineering judgment can be made by a person looking at the evidence.

## Launch

From the repository root:

```bash
python -m http.server 8000
```

then open:

```
http://localhost:8000/ver3/out/review/index.html
```

Over VS Code Remote SSH, forward port 8000 and use the same URL. The page is a
single self-contained file — inline CSS and JS, no CDN and no framework — so it
works with no internet access.

## Regenerating

```bash
python ver3/tools/run_trace.py       --case BM-001    # canonical execution -> trace
python ver3/tools/build_review_ui.py --case BM-001    # trace -> HTML
```

The two steps are separate on purpose. `run_trace.py` executes the real pipeline
and records what happened; `build_review_ui.py` only projects that record. The UI
opens no DesignState, parses no fixture and reads no contract, so there is exactly
one answer to "what did this stage see" and it is the pipeline's.

## What the two status badges mean

Every node carries two, and they are never merged:

| badge | what it means |
| --- | --- |
| `contract: ACCEPTED` | schema, references and authority were satisfied |
| `human review: NOT_REVIEWED` | **nobody has judged the engineering yet** |

A green contract badge is not a claim that the mechanism, proportions, load path,
kinematics, clearances or manufacturability are sound. Those are exactly what the
review is for, and nothing in this tool computes them. There is no automated
mechanical score, and no model is asked to judge a design.

`REPLAY` nodes are recorded responses replayed through the real parser and
contracts. That is not live-model evidence.

## Recording a review

Select a node, set PASS / FAIL / NEEDS_REVIEW, optionally pick a category, add a
comment, and save. Reviews are held in browser local storage and exported with
**Export all reviews (JSON)** as `human_review-<benchmark>.json`.

Human review is stored separately from the run trace and never mutates
DesignState. The trace is immutable execution evidence; a review is an annotation
on it, carrying the run, benchmark, responsibility and commit it refers to.

## What this run shows

`BM-001` replayed through s01 and s02. s01 is accepted; s02 is **rejected** — the
stored fixture predates the `reacted_at_site` requirement and the R-20
reference-must-be-an-id rule. That is the known corpus debt the 12-target
regeneration exists to clear, and it is visible here rather than hidden.

s03a, s03b, s04a and s04b are marked NOT_EXERCISED: no recorded response has ever
existed for them.

`S05`, `S06` and `S07` are marked NOT_IMPLEMENTED — embodiment, the parameter
solver, and the construction compiler that builds CAD. Each has a full contract
under `ver3/contracts/stages/` with numbered deterministic exit checks, and none
has any implementing code. `NOT_IMPLEMENTED` here means **specified and unbuilt**,
not undefined — see `docs/implementation/evidence/S09E_PIPELINE_MAP.md` and
`S05_CAD_GAP_SPEC.md`.

## The CAD shown here

Real geometry, and **not produced by the pipeline**. It is hand-authored reference
CAD under `ver3/cad_validation/`, built by scripts that call cadquery directly,
import no part of `assy_v3` and read no DesignState. No body or feature in it
resolves to a canonical design entity id. It is shown because it is the only real
geometry that exists, and labelled everywhere it appears so it is never mistaken
for pipeline output.
