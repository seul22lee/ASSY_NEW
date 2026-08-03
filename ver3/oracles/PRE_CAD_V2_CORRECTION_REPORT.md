# Pre-CAD V2 correction report — authority and fixture rebuild

**Branch:** `ver3-oracle-phase1-review`
**Starting commit:** `f7e3a22844fa3d3eef0b56c90aeba6d29b1a15af`
**Final status:** `PRE_CAD_BASELINE_READY` — **not** LOCK_READY, **not** LOCKED,
**not** CAD_VALIDATED, **not** PHYSICALLY_PROVEN, **not** PRODUCTION_READY.

Eleven findings were inventoried before any file changed, plus two more found by
the reviews themselves. This was a rebuild, not a patch pass: no contract was
"fixed" by adding a DEPRECATED label, no tag was bulk-assigned, and no defect was
resolved by changing only the auditor.

---

## PCF-001 — SOURCE_FREEZE conflated rank-1 user authority with project capability

All nine dossiers carried `authority_rank: "rank_1_for_S1_product_extracts"`.
That is **false for the four micro-oracle dossiers**: their S1 is a
project-authored capability definition, and a micro-oracle has no user.

`SOURCE_FREEZE.yaml` was **re-authored from the underlying files** with five
explicit authority types:

| Type | Count | Applies to |
|---|---|---|
| `FROZEN_PRODUCT_DOSSIER` | 6 | the five product dossiers + the index |
| `PROJECT_CAPABILITY_ORIGINAL` | 4 | the four micro-oracle dossiers |
| `FROZEN_AMBIGUITY_RECORD` | 2 | AMB-001-2-01, AMB-001-3-01 |
| `SOURCE_PRECEDENCE_POLICY` | 1 | ORACLE_METHOD §3 |

Each micro-oracle dossier records `source_rank: "NOT APPLICABLE to S1"`, whether
its original definition is currently superseded, and by which authority.
**Regression:** `PROJECT_CAPABILITY_MISLABELLED_RANK1`.

## PCF-002 — challengeable authority held inside the immutable freeze

`HUMAN_SEMANTIC_DECISIONS.yaml` and `AMENDMENTS.yaml` sat inside a freeze
declaring `challengeable_by_cad: false`, while every decision inside them declares
`challengeable_by_cad: true`.

**Three layers now exist:**

| Layer | Manifest | Fixes | CAD may change |
|---|---|---|---|
| A immutable source | `SOURCE_FREEZE.yaml` | what the source SAYS | no |
| B challengeable semantic authority | `SEMANTIC_AUTHORITY.yaml` | what it currently MEANS | **yes** |
| C current conclusions | `PRE_CAD_BASELINE.yaml` | what follows from it | **yes** |

**Regressions:** `CHALLENGEABLE_AUTHORITY_INSIDE_SOURCE_FREEZE`,
`SEMANTIC_AUTHORITY_MANIFEST_MISSING`.

## PCF-003 — stale current-state fields

`reviewed_commit: 3b64aee` (two commits stale), an audit scope naming only 3A–3E,
a 45-case mutation count, and an index claiming 41 admissible fixtures.

Current-state sections were **re-authored** and every total is now **computed from
the final snapshot**. The auditor compares the workflow totals and the index
fixture count against the snapshot itself.
**Regressions:** `WORKFLOW_CURRENT_STATE_STALE`, `INDEX_AUDIT_COUNT_STALE`.

## PCF-004 — representation declaration inside physical fixture truth

`interaction_regions_declared` was a **physical** tag in all nine packs. Whether a
design DECLARES its interaction regions is a DesignState property; a buildable
artifact whose record is incomplete was being reported physically inadmissible.

A **three-domain model** was added (policy §12.5, method §13.85): physical /
representation / evidence. The tag was **removed from every physical contract**
and re-homed as `stage_expectations.evaluability_prerequisites`, whose failure
outcome is:

```yaml
physical_predicate: NOT_EVALUABLE
reason: REPRESENTATION_INCOMPLETE
```

Three canonical physical tags replace the mixture:
`no_undeclared_volumetric_overlap`,
`intended_interaction_physically_consistent`,
`installation_process_physically_realizable`.
**Regression:** `REPRESENTATION_TAG_IN_PHYSICAL_DOMAIN`.

## PCF-005 — new physical tags bulk-certified across old fixtures

The previous pass appended three new tags to ~100 fixtures by script, without
reading a narrative. That certification was **withdrawn**.

`PHYSICAL_FIXTURE_REVIEW.yaml` now holds **108 individual reviews**
(44 admissible, 64 inadmissible). Each records the narrative support, the
representation prerequisites, the assumptions needed, the unresolved physical
questions, and a status. Tags were then derived **from the review**, and every
fixture carries a `physical_review` pointer.

The record states plainly that **a tag is a review conclusion, not independent
physical evidence** — it is authored by the same hand as the invariant it
satisfies.

Notable individual judgements, none of which a bulk script would have reached:

- `INA-BM-001-D` (extent shrunk at OPEN) **loses** `no_undeclared_volumetric_overlap`: altering
  the body extent means the true solid does overlap and the representation hides it.
- `INA-C4-E` (a drawer that skews and **jams**) loses it too: jamming is undeclared
  contact at an unintended configuration, not merely a behaviour failure.
- `INA-LR-E` (engagement interference with no declared deflection) loses it — the
  only latch-retention fixture whose defect is genuinely an overlap.
- BM-001-2 carries **only** `intended_interaction_physically_consistent`: the delta
  states no motion path and no assembly, so assigning the other two would be the
  bulk certification being withdrawn.

**Regression:** `FIXTURE_TAG_WITHOUT_INDIVIDUAL_REVIEW`.

## PCF-006 — deprecated `assembly_paths_exist` still active

It had been relabelled `DEPRECATED` in its vocabulary description while remaining
in `requires_tags` and in every fixture tag list — so it still decided PASS/FAIL.

**Removed from every active contract.** Replaced by
`installation_process_physically_realizable`. It survives only in
`retired_contracts`, which contributes nothing to evaluation.
**Regression:** `DEPRECATED_TAG_ACTIVE`, with a control proving a `retired_contracts`
mention stays silent.

## PCF-007 — statement, tag and predicate disagreed on intended contact

`NRM-BM-001-003`'s predicate had been corrected to no-undeclared-overlap while its
**statement** still said the swept region "does not intersect the enclosure solid"
and its **tag** `sweep_clears_enclosure` still meant the same thing.

Six statements re-authored; five blanket tags retired
(`sweep_clears_enclosure`, `pose_clearances_satisfied`, `travel_clearances_satisfied`,
`crossing_non_interfering`, `transition_free_of_interference`).
**Regression:** `STATEMENT_PREDICATE_INTERACTION_MISMATCH`.

## PCF-008 — superseded dossier sections cited as sole authority

Fifteen micro-oracle statements cited a superseded S1 alone. A pack-level
`dossier_amendment` block is not a per-statement citation.

All **73** statements now carry `current_authority`. `AMD-HS-001` is applied only
within its declared partial scope: `NRM-HS-003` and `NRM-HS-005` cite the
amendment, while `NRM-HS-004` retains the **unchanged** original S1 clause, which
the amendment explicitly excludes and which grounds
`source_declares_terminal_states`.
**Regression:** `SUPERSEDED_LOCATOR_WITHOUT_CURRENT_AUTHORITY`.

## PCF-009 — the revision procedure was internally impossible

Step 4 said a CAD counterexample revises `HUMAN_SEMANTIC_DECISIONS.yaml`; step 6
and the freeze said the freeze is not revised by CAD — and the file was **inside**
the freeze. The procedure required changing a hash it forbade changing.

Resolved by the PCF-002 layering. The procedure is now executable, and the
baseline states why.
**Regression:** `SOURCE_FREEZE_REVISION_PARADOX`, with a control confirming that
layer B *declaring* challengeability is the resolution, not the paradox.

## PCF-010 — the auditor reported clean while all of the above were present

Pass **3H** added, with fourteen checks. Each fires on a defect that **actually
existed in this repository** while passes 3A–3G reported clean. The mutation suite
grew from 69 to **88 cases (70 defects, 18 controls)**.

## PCF-011 — assembly unresolved decisions cited methodology, not source silence

`UNR-BM-001-009`, `UNR-BM-002-008` and `UNR-C4-008` cited only
`ORACLE_AUTHORING_POLICY 14`. A policy section describes how to handle a silence;
it is not the silence. Each now cites `DOS-BM-001 S2`, `DOS-BM-002 S3` and
`DOS-C4-drawer S3` as `primary_source_of_silence`.
**Regression:** `ASSEMBLY_SOURCE_SILENCE_LOCATOR_MISSING`.

---

## Two further findings, from the reviews rather than the inventory

**RR-H-01** — the three assembly predicates still required that deformation,
material, insertion direction and process assumptions "**are represented**". A
physically coherent press fit whose assumptions were unrecorded would have failed
a **physical** invariant: the PCF-004 defect class surviving inside the new
assembly contract. The auditor did not catch it; GATE 7 pass H did.
**Regression:** `PHYSICAL_PREDICATE_REQUIRES_RECORDING`, with a control proving
that "where the design declares X, Y must hold" is a scope condition and not a
recording obligation.

**PCF-B-01** — once the representation tag was removed, `INA-BM-001-K` (a rigid
snap that cannot deflect) and `INA-BM-001-L` (an interference with no material
relation) passed **every** BM-001 physical invariant, because no BM-001 invariant
owned interaction coherence. `NRM-BM-001-002` was extended to own it. Found by
pass 3B.

## Four check defects found by their own tests

| Check | Defect |
|---|---|
| `AMBIGUITY_BLOCKING_DISAGREEMENT` | `"NON_BLOCKING"` contains the substring `BLOCK` |
| `STAGE_DEMANDS_PERMITTED_FREEDOM` | matched "accounted for" as if it were "removed" |
| `BLANKET_CLEARANCE_PREDICATE` | `[^)]*` stopped at the first `)`, missing nested calls |
| `RR-H-01` | read a disclaiming exclusion as an assertion |

---

## Contracts completely replaced, not deprecated

| Retired | Replaced by |
|---|---|
| `assembly_paths_exist` | `installation_process_physically_realizable` |
| `interaction_regions_declared` (physical) | `evaluability_prerequisites` (representation) |
| `sweep_clears_enclosure` | `no_undeclared_volumetric_overlap` |
| `pose_clearances_satisfied` | `no_undeclared_volumetric_overlap` |
| `travel_clearances_satisfied` | `no_undeclared_volumetric_overlap` |
| `crossing_non_interfering` | `no_undeclared_volumetric_overlap` |
| `transition_free_of_interference` | `no_undeclared_volumetric_overlap` |
| `assembly_process_realizable` | `installation_process_physically_realizable` |
| `no_undeclared_overlap_on_transition` | `no_undeclared_volumetric_overlap` |

Each survives only in a pack's `retired_contracts` block, which contributes
nothing to any PASS/FAIL decision.

## Manifests

| Manifest | Artifacts | Hash |
|---|---|---|
| `SOURCE_FREEZE.yaml` | 13 | `cb74bd8711bbd3a4c71a8038838ca997a559ac6902a099d04a6dda48acfcb1a5` |
| `SEMANTIC_AUTHORITY.yaml` | 2 | `9d447f0092defe22c92f7fe2dda7cd93af4168a3f9ac0ebbef43b352a6d0c600` |

Both were verified by a **second, independent process** that recomputed every
artifact hash from disk, recomputed each manifest hash, confirmed neither manifest
lists itself, and confirmed the two layers share no artifact.

## Remaining ambiguities

`AMB-001-2-01` (BM-001-2, **blocking, source-level**), `AMB-002-01`, `AMB-002-02`,
`AMB-001-3-01` (non-blocking). `AMB-C4-01` remains retired to
`LEGACY-CONFLICT-C4-01`.

## Physical questions deferred to CAD

All **108** reviewed fixtures are `NEEDS_GEOMETRY_VALIDATION`; none was upgraded, and
no CAD or physics work exists. Twelve specific uncertainties `PU-01…PU-12` are
recorded in the baseline as first targets.

## No lock, no CAD, no production code

No `LOCK.json`. No STEP, B-rep, STL, mesh or geometry file. No production pipeline
code — the only two Python files under `ver3/` are the read-only auditor and its
mutation suite. No `ver3/assy3`. No file outside `ver3/` was modified.

The next authorized phase is **adversarial CAD validation**.
