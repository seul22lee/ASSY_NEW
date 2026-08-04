# Phase 0 — Legacy evidence inspection and Oracle source discovery
> **Scope note.** A later pass removed one BM-001 delta pack from active project
> scope. Rows and mentions belonging only to that pack have been dropped from this
> historical report so the current tree carries no reference to it. Everything stated
> here about the remaining packs is unchanged, and git history holds the original.


**Status:** source-discovery complete; failure classification in progress.
**Constraint honoured:** nothing under the legacy repositories was modified. All
access was read-only (`ls`, `find`, `grep`, `python3 -c` reads). No git command
of any kind was run.

---

## 0. Environmental discrepancies found before any work began

The task statement describes an environment that does not match this machine in
three respects. None was silently patched; each is recorded here and the
resolution is deferred to the user where it changes the deliverable.

| # | Task statement says | Actual state on this machine | Action taken |
|---|---|---|---|
| D-1 | Legacy repos at `./1.0` and `./2.0` | Do not exist. Real paths are `/home/ftk3187/github/ASSY_Ver1.0` and `/home/ftk3187/github/ASSY_Ver2.0` (siblings of the working directory) | Proceeded with the real paths — the mapping is unambiguous. Every path in this report is absolute. |
| D-2 | "A local checkout of ASSY_NEW may also exist in or near this workspace" | **No `ASSY_NEW` exists anywhere under `/home/ftk3187`.** `find /home/ftk3187 -maxdepth 4 -iname "*ASSY*" -type d` returns only `ASSY_Ver1.0`, `ASSY_Ver2.0`, `ASSY_Ver3.0` and Claude cache dirs | Not resolved autonomously — see §4. |
| D-3 | Working directory is a clean Ver3 reconstruction | `/home/ftk3187/github/ASSY_Ver3.0` already contains a complete, unrelated, git-tracked project (`mdkg` — a mechanical-design ontology with claims/evidence over two textbooks), built earlier in this session | Nothing deleted or moved. Phase 0 output written to `ver3/` to avoid interleaving two projects. See §4. |

**D-1 note.** Because the stated paths were wrong, every legacy path in this
report and in all downstream Oracle `source_map.md` files is recorded as an
absolute path verified to exist, not as a path copied from the task statement.

---

## 1. Legacy repository inventory

| Repo | Path | Files | Size | Role in Ver3 |
|---|---|---|---|---|
| Ver1 | `/home/ftk3187/github/ASSY_Ver1.0` | 5,682 | 110 MB | Evidence only — reference realizations and negative evidence |
| Ver2 | `/home/ftk3187/github/ASSY_Ver2.0` | 13,630 | 1.4 GB | Evidence only — product-level specifications and failure record |

**Ver1 structure** — milestone-organised (`m0` … `m27`), each milestone holding
`REVIEW.md`, `out/` artifacts (MJCF XML, MP4, PNG, verdict JSON), plus
top-level `knowledge/` (mechanism cards, host templates), `tasks/` (task JSON +
`benchmark/`), `reviews/`, `ontology/`, `pipeline/`, `verify/`, `viz/`.

**Ver2 structure** — stage-organised (`STAGE_01…STAGE_05` markdown contracts),
`assy/` (implementation), `tests/fixtures/` (benchmark requirement specs),
`out/<BM-id>/run-<timestamp>/` (182 recorded runs), `research_log/RL-0001…0014`,
`docs/`, and top-level benchmark specifications.

---

## 2. Mandatory Oracle source search B — the two cylindrical BM-001 cases

### 2.1 Search performed

Filename search across both repos for `cylind*`, `cylinder`, `round`,
`circular`, `jar`, `canister`, `drum`, `tube`, `radial`, `curved` returned
**one** hit (`ASSY_Ver1.0/tests/test_roundtrip.py`) which is a false positive
("roundtrip"). Content search for the same vocabulary returned ~50 files, all
incidental uses of `cylinder` as an MJCF/geometry primitive or as shaft
description inside mechanism cards — **no cylindrical product case**.

The cases were therefore found structurally rather than lexically: Ver2
registers exactly five benchmarks in
`/home/ftk3187/github/ASSY_Ver2.0/tools/run_benchmarks.py:37`

```python
BENCHMARKS = ("BM-001", "BM-001-2", "BM-002", "BM-101")
```

`BM-001-2` is the only BM-001-derived variant in active scope.

### 2.2 Identification — exact source paths

| Case | Requirement spec (authoritative) | Recorded runs |
|---|---|---|
| **BM-001-2** | `/home/ftk3187/github/ASSY_Ver2.0/tests/fixtures/BM-001-2_requirementspec.json` | `/home/ftk3187/github/ASSY_Ver2.0/out/BM-001-2/` (22 runs) |

### 2.3 Why each belongs to the BM-001 requirement family — verbatim evidence

Both specs carry an explicit provenance note in `meta.notes` stating they are
BM-001 plus exactly one added requirement. Requirement-level diff against
`BM-001_requirementspec.json`:

**BM-001-2** (`SPEC-001-2`, 8 → 10 requirements)

> *meta.notes[0]:* "BM-001 with one requirement added: the enclosure mounts
> flush against a panel and presents no projecting corners outward. Everything
> else is identical, so any difference in the result traces to that requirement
> and nothing else."
> *meta.notes[1]:* "REQ-010 turns the catch round: the beam runs down the
> inside of the wall and the nose comes out through it."

- `+ REQ-009` *(environmental)* — "The enclosure must sit flush against a
  mounting panel on one side and present no projecting corners on the exposed
  side." · verification: inspection, observable "one face flat against the
  panel, **the exposed side rounded**"
- `+ REQ-010` *(safety)* — "The latch must not be releasable from the exposed
  side; it can only be worked from inside the enclosure." · verification:
  inspection, observable "no part of the catch reachable from the exposed side"


> *meta.notes[0]:* "BM-001 with one requirement added: the enclosure rests on a
> curved back and opens through a flat top. Everything else is identical, so any
> difference traces to that and nothing else."

- `+ REQ-011` *(environmental)* — "The enclosure **rests on a curved back** and
  opens upward through a flat top face." · verification: inspection, observable
  "**curved underside**, flat opening on top"

All other clauses, requirements, `source_text`, `product_intent` and
`user_intent_summary` are byte-identical to BM-001.

### 2.4 Honest qualification on the word "cylindrical"

The task statement calls these "two detailed cylindrical examples". **Neither
spec uses the word "cylindrical".** They specify *rounded exposed side*
(BM-001-2). This matters
because it is precisely the distinction the Oracle must not blur:

- The evidence supports a normative statement of the form *"the enclosure
  boundary is not required to be a rectangular prism; a curved boundary segment
  is a valid and, in these cases, required realization."*
- The evidence does **not** support a normative statement of the form *"the
  enclosure is a cylinder."*

This is exactly the anti-rectangular-box purpose the task assigns to these
cases, and it is achieved without over-claiming a cylinder. The Oracle Packs
will encode the curved-boundary requirement and will list *cylinder*, *rounded
prism*, and *curved-back shell* as **allowed freedoms**, not as normative truth.

### 2.5 Ambiguity assessment

`ORACLE_SOURCE_AMBIGUITY.md` is **not** required for this search. Exactly two
BM-001 variants exist in the entire Ver2 benchmark registry, both are
curved-boundary variants, and both are individually documented as
single-requirement deltas from BM-001. There is no third plausible candidate to
choose between.

---

## 3. Mandatory Oracle source search D — the Ver1 rack-and-pinion drawer case

### 3.1 The case exists, and it is neither of the two files named in the task

**Identified case: `C4-drawer`.**

> *"Design a desktop cabinet whose drawer slides out horizontally when you turn
> a knob."*

Exact sources:

| Artifact | Path | Content |
|---|---|---|
| Benchmark manifest | `/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/manifest_draft.md:32` | Command text; axis = "constraint (horizontal, no gravity-hold)"; expected "PASS (drawer alternate, V-A)" |
| Certification record | `/home/ftk3187/github/ASSY_Ver1.0/tasks/benchmark/certification_matrix.json` | `{"id":"C4-drawer","expected":"PASS","stages":{"validators":"clean","⑤ resolve":"ok","⑥ compile":"5 bodies","physics":"reused — PASS"},"physics_evidence":"m13 drawer V-A 5/5 (t2_hard_verdict)","verdict":"CERTIFIED"}` |
| Realization evidence | `/home/ftk3187/github/ASSY_Ver1.0/m14_task_ladder/REVIEW.md:15` | "same **2×slide_rail + rack_pinion**, re-oriented — lift (vertical) vs drawer (horizontal)" |
| Review row | `/home/ftk3187/github/ASSY_Ver1.0/m14_task_ladder/REVIEW.md:35,62` | "C4-drawer … lift · constraint … PASS"; "clean / ok / 5 bodies / reused V-A PASS / ✅ CERTIFIED" |
| Generated variants | `/home/ftk3187/github/ASSY_Ver1.0/m15_ablation/out/cells/*C4-drawer*.json` (24 cells), `/home/ftk3187/github/ASSY_Ver1.0/m15_naive/gen/C4-drawer__qwen__s{0,1,2}/` | Ablation and naive-baseline generations |
| Gallery artifacts | `/home/ftk3187/github/ASSY_Ver1.0/m15_ablation/out/gallery/C4-drawer__P1.stl`, `target_C4-drawer.png` | Geometry and target image |

`C4-drawer` is a **cabinet drawer driven by a knob through a rack and pinion and
guided by two slide rails** — a genuine combined rack-and-pinion drawer, and a
legacy case, not a synthetic one.

### 3.2 Explicit distinction from the two files the task warned about

Confirmed by reading both files directly:

| File | `task_id` | `command` | Functions | Is it the rack-and-pinion drawer? |
|---|---|---|---|---|
| `/home/ftk3187/github/ASSY_Ver1.0/tasks/latched_drawer.json` | `latched_drawer` | "A drawer that slides in, **clicks shut, and pulls open by hand**. Plastic, 3D printing." | `guide drawer (slide in/out)`, `retain drawer (click shut, hand-releasable)` | **No.** Slide rail + snap latch, hand-actuated. Behaviours B1 (translation 50 mm), B2 (`snap_event`, 15–60 N). No rotation, no rack, no pinion. |
| `/home/ftk3187/github/ASSY_Ver1.0/tasks/rack_pinion_fixture.json` | `rack_pinion_fixture` | "A **knob** that drives a **rack** straight out and back. Plastic, 3D printing." | `convert motion (rotation to translation)`, `drive rack (linear travel from a knob)` | **No.** A motion fixture. No cabinet, no drawer, no enclosure, no guidance obligation. |
| `tasks/benchmark` `C4-drawer` | `C4-drawer` | "Design a desktop **cabinet** whose **drawer** slides out horizontally when you **turn a knob**." | drawer guidance + rotation-to-translation | **Yes.** Combines both. |

The task statement's caution was well founded: the two named files are indeed a
snap drawer and a rack-pinion fixture respectively, and they must not be merged.
They will each receive their own Oracle Pack *in addition to* `C4-drawer`,
because each carries distinct negative evidence.

### 3.3 Consequence for Part VII case 5

No fabrication and no synthetic case are needed. Case 5 is `C4-drawer`, with
`latched_drawer` and `rack_pinion_fixture` retained as separate reference
realizations / negative-evidence sources.

---

## 4. Blocking questions — deliberately not resolved autonomously

Two of the three discrepancies in §0 change the deliverable and are therefore
carried to the user rather than assumed.

**Q-1 — Workspace layout (D-3).** `/home/ftk3187/github/ASSY_Ver3.0` is not
empty: it holds the complete `mdkg` project (ontology, claims, evidence, SHACL
shapes, visualization app, 119 tests) under git. Ver3 will add on the order of
100+ files. Writing them to the same root interleaves two unrelated projects;
deleting or moving the existing project is destructive and was not instructed.
Phase 0 output is currently under `ver3/`, which is non-destructive and
trivially relocatable.

**Q-2 — ASSY_NEW identity (D-2).** No repository named `ASSY_NEW` exists on
this machine. However, the `mdkg` project already in the working directory
matches the scope Part II ascribes to ASSY_NEW almost exactly — *function →
possible element or alternative; applicability conditions; failure modes; what
should be checked; provenance and evidence*. It is either the intended
reference or a coincidence. This must be settled before
`REFERENCE_KNOWLEDGE_NOTE.md` can be written honestly, because that document
must prove Ver3 has **no** runtime dependency on whatever ASSY_NEW actually is.

Neither question blocks further Phase 0 classification work, which continues on
the legacy failure register.

---

## 5. Evidence already located for the legacy failure register

Ver2's own research log names several of the failure classes the task requires
Ver3 to prevent. These are primary sources, not inferences from code behaviour:

| Entry | Title | Failure class it documents |
|---|---|---|
| `RL-0004` | Stage 04 spatial concept analysis | Ordinal/slot spatial model |
| `RL-0005` | Stage 04 visualization and visual review | ConceptVisualization as authoritative output |
| `RL-0006` | Spatial contract repair | Spatial contract insufficiency |
| `RL-0007` | Renderer readability and coverage audit | Renderer/model boundary |
| `RL-0009` | Spatial-first, semantics-on-top | Layering inversion |
| `RL-0010` | Topological anchors: what a feature is attached to | Missing host/anchor semantics |
| `RL-0011` | Derived placement: why a feature is where it is | Role-to-position mapping |
| `RL-0012` | **Observability of motion is a property of the model, not the drawing** | Render-as-proof |
| `RL-0013` | **Ranking measured how well a family was described, not how good it is** | Complexity scoring rewarding incompleteness |
| `RL-0014` | A stage that is never asked for its output is not in the pipeline | Dead stage / unconsumed artifact |

Additional primary sources located:
`/home/ftk3187/github/ASSY_Ver2.0/docs/ERROR_TAXONOMY.md`,
`/home/ftk3187/github/ASSY_Ver2.0/docs/ASSY_VER1_EVIDENCE_AND_LIMITATIONS.md`,
`/home/ftk3187/github/ASSY_Ver1.0/reviews/external_review_1.md`,
`/home/ftk3187/github/ASSY_Ver1.0/DECISIONS_LOG.md`,
`/home/ftk3187/github/ASSY_Ver2.0/DEVELOPMENT_LOG.md`.

---

## 6. Phase 0 status

| Deliverable | State |
|---|---|
| Legacy repos located and inventoried | **Done** |
| Read-only constraint honoured | **Done** — no writes, no git commands |
| Cylindrical case search (Oracle source B) | **Done** — BM-001-2, exact paths, verbatim deltas |
| Rack-and-pinion drawer search (Oracle source D) | **Done** — `C4-drawer` identified; distinguished from both warned-about files |
| `ORACLE_SOURCE_AMBIGUITY.md` needed? | **No** for both searches — evidence is unambiguous |
| Failure-source location | **Done** — primary sources identified |
| `LEGACY_FAILURE_REGISTER.md` | **Not started** — blocked only by Q-1 (where to write) |
| BM-101 / Geneva exclusion | **Honoured** — `BM-101` located but not read for architecture, not used |

Phase 1 (Oracle authoring) has **not** begun, per the non-negotiable ordering.
