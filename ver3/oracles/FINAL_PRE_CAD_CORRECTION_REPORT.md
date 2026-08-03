# Final bounded pre-CAD correction — FPC-001…007

**Branch:** `ver3-oracle-phase1-review`
**Starting commit:** `0b8442b4a0d16897c441ae700a24062ac0f23944`
**Final state:** `PRE_CAD_BASELINE_READY — STOPPED BEFORE CAD`

Scope was limited to active-contract defects that can misclassify a CAD design.
Everything else went to `PRE_CAD_BACKLOG.yaml` and does not delay CAD entry.

---

## FPC-001 — product assembly Stage rules required collision-free insertion

Three Stage rules still failed a design when "a part has no collision-free
installation path", while the normative invariants they project had already moved
to `installation_process_physically_realizable`. **A press fit has no
collision-free path and is still assemblable**, so these rules could FAIL a
physically valid design.

| Pack | Stage rule | Normative |
|---|---|---|
| BM-001 | `s11 REQ-007` | `NRM-BM-001-010` |
| BM-002 | `s11 REQ-006` | `NRM-BM-002-012` |
| C4-drawer | `s11 C4-R11_assembly` | `NRM-C4-011` |

Each re-authored with `pass_requires` (a realizable process through no
**undeclared** rigid material, plus an acyclic order), `must_not_fail_when`
(intended insertion contact; a declared snap/press/interference/compliant
insertion lacking a collision-free path but physically coherent; co-formed or
bonded regions owing no discrete path), `if_representation_incomplete:
NOT_EVALUABLE`, and a `fail_when` naming only genuine physical impossibility.

Force adequacy is explicitly **not** proven by a PASS and remains at
`UNR-BM-001-009`, `UNR-BM-002-008`, `UNR-C4-008`.

**Disposition: CORRECTED.** No active Stage rule now requires a collision-free path.

## FPC-002 — C4 clearance rule could reject intended guide contact

`s11 C4-R10_clearance_and_traversability` required the drawer "shown not to
intersect cabinet material at any configuration" and failed on "an intersection
occurs at any configuration". **A drawer rides on the guides it touches**, so the
rule could FAIL every physically valid guided design while `NRM-C4-010` already
prohibited only *undeclared* overlap.

Re-authored to no-undeclared-overlap, with an explicit `must_not_fail_when` for
declared guide, bearing and stop contact and for zero clearance at a declared
contact.

**Also corrected, same explicit retired wording:** `BM-001 s11 REQ-001`, whose
`fail_when` said "the transition **interferes**" — which a naive reader applies to
a hinge touching its own bore at every configuration. Narrowed to undeclared
overlap. BM-002's equivalent rule was inspected and did **not** carry the defect;
it was left unchanged.

**Disposition: CORRECTED.**

## FPC-003 — bounded Stage rule rejected admissible constraint hand-off

`HS-C3_constraint_persists` required "**the** relative constraint shown engaged at
the extremes and the interior" and failed when "the constraint lapses anywhere".
That rejects a flexure handing off to a moulded rib — the `ADM-HS-E` semantics
`AMD-HS-001` and `HSD-003` explicitly admit.

Renamed `HS-C3_constraint_coverage_continuous` and re-authored: coverage must be
continuous, the **active constraint may change**, hand-off and overlapping
coverage are admissible, and FAIL applies only to a genuine coverage **gap** or
unconstrained free flight.

**Disposition: CORRECTED.**

## FPC-004 — bounded Stage rule rejected a shared bounding mechanism

`HS-C5_bounds_distinct` required each extreme "determined by its **own**
condition" and failed when "one condition is credited to both extremes". That
rejects `ADM-HS-D` (one continuous slot arresting the pin at both ends) and
`ADM-HS-F` (one magnetic field with two stable seats), both admitted under
`HSD-003`.

Renamed `HS-C5_bounds_independently_evaluated`: each terminal carries its own
evaluation result and causal account; one feature, field or mechanism **may**
contribute to both; FAIL only when a **result** is copied or an endpoint has no
physically supported bound.

**The same defect was found in C4** by the new check: `s11
C4-R7_declared_ends_of_travel` carried the identical wording and would reject a
single rail abutting at both extremes. Re-authored the same way.

**Disposition: CORRECTED.**

## FPC-005 — NRM-HS-006 asserted exactly two bounding contacts

The statement ended "…the interaction regions the design declares, **of which the
bounding contacts are two**", asserting both a count and a kind. Admissible bounds
may arise from contact, geometric run-out, an engagement ending, force or field
equilibrium, or one field participating at both endpoints.

The invariant was **re-authored completely** — statement, derivation premises,
conclusion scope, exclusions, predicate, tags and evaluability prerequisites — to:

> Along the required motion the two bodies have no undeclared volumetric overlap.
> Intended bounding and constraining interactions are admissible and are not
> treated as interference.

Its Stage projection was renamed `HS-C6_no_undeclared_overlap` and re-authored to
match.

**Disposition: CORRECTED.**

## FPC-006 — HSD-006 statements and Stage projections still required a control

The three predicates had been made two-branch in the previous pass, but the
**statements** and **Stage rules** had not. A design with perfectly good direct
causal evidence could be reported NOT_VERIFIED for want of an ablation model.

| Artifact | Was | Now |
|---|---|---|
| `NRM-BM-001-012` | "must be able to fail when that determinant is removed" | either branch |
| `NRM-GS-007` | "must be able to take a non-conforming value" | either branch |
| `NRM-HS-007` | "must be able to distinguish a bounded closure from an unbounded one" | either branch |
| `NRM-C4-012` | same defect, found by the new check | either branch |
| `s11 GS-C6` → `GS-C6_evidence_admissibility` | branch B only | either branch |
| `s11 HS-C4_bounds_physically_realized` | "a criterion demonstrated to discriminate" + `if_criterion_does_not_discriminate: NOT_VERIFIED` | either branch |
| `s11 HS-C7` → `HS-C7_evidence_admissibility` | branch B only | either branch |

Each now carries an explicit `evidence_branches` block with
`relation: ALTERNATIVES`, and each Stage rule carries `must_not_fail_when: no
control or ablation model exists, provided branch A is adequately supported`.
Absence of a control is **NOT_VERIFIED at worst, never a physical FAIL**.

`NEG-HS-008` was scoped rather than changed: it concerns branch B only, and says
so.

`UNR-HS-004` records that the corpus supplies no discriminating single-run
criterion. Under the corrected contract that no longer blocks a PASS, because
branch A is an alternative route.

**BM-001 had no separate Stage rule projecting `NRM-BM-001-012`**; the minimum
reaches `REQ-001` through `NRM-BM-001-005`, and `REQ-001` never required
discrimination. Nothing to correct there.

**Disposition: CORRECTED.**

## FPC-007 — duplicate keys and stale current state

- `NRM-HS-001` carried `current_authority` and `authority_note` **twice**. YAML
  silently keeps the last, so a contradictory value could have hidden. Removed —
  7 occurrences for 7 invariants.
- `BM-002 s11 REQ-002` carried `if_capability_absent` twice. Removed.
- `ORACLE_WORKFLOW_STATE.yaml` and `ORACLE_INDEX.md` totals **recomputed from the
  final snapshot**; audit scope updated to 3A–3I; `starting_commit` updated.

**One further bookkeeping defect was found by the audit itself:** `NOT_EVALUABLE`
was defined by the three-domain model (policy §12.5.1) and used by every
`evaluability_prerequisites` block, but was never added to the auditor's
`STATUS_VALUES`. Four correctly-authored Stage rules were reported
`INVALID_STATUS_VALUE`. Added.

**Disposition: CORRECTED.**

---

## Targeted regressions — pass 3I

Eleven defect mutations, five controls, all behaving:

| Mutation | Detects |
|---|---|
| `bm001/bm002/c4_stage_assembly_requires_collision_free` | `STAGE_ASSEMBLY_REQUIRES_COLLISION_FREE` |
| `c4_stage_clearance_rejects_all_contact` | `STAGE_CLEARANCE_REJECTS_INTENDED_CONTACT` |
| `hs_c3_requires_single_persistent_constraint` | `STAGE_REQUIRES_SINGLE_PERSISTENT_CONSTRAINT` |
| `hs_c5_rejects_shared_field_bound` | `STAGE_REJECTS_SHARED_BOUND_MECHANISM` |
| `nrm_hs_006_asserts_two_bounding_contacts` | `NORMATIVE_ASSERTS_BOUNDING_CONTACT_COUNT` |
| `bm001_012 / gs_007 / hs_007_discrimination_only` | `VERIFICATION_MINIMUM_DISCRIMINATION_ONLY` |
| `stage_projects_discrimination_only` | `STAGE_REQUIRES_DISCRIMINATION_ONLY` |

| Control | Asserts silence |
|---|---|
| `declared_snap_insertion_is_admissible` | "collision-free" inside `must_not_fail_when` is the exemption, not the rule |
| `intended_drawer_guide_contact_is_admissible` | declared guide contact is not interference |
| `constraint_hand_off_is_admissible` | the active constraint may change (ADM-HS-E) |
| `one_field_at_both_bounds_is_admissible` | one field may bound both extremes (ADM-HS-D, ADM-HS-F) |
| `direct_causal_evidence_needs_no_ablation` | branch A alone is admissible |

Pass 3I reads explicit schema fields — `pass_requires`, `fail_when`,
`must_not_fail_when` of named outcome rules — not free text anywhere in the tree,
and treats a phrase appearing only inside `must_not_fail_when` as the exemption it
is.

## Audit results

| Run | Result |
|---|---|
| canonical, 3A–3I | **0 BLOCKING, 0 MAJOR** |
| shuffled 20260802 / 4177 / 90210 | 0 / 0 at every seed |
| mutation suite | **104/104** — 81 defects caught, 23 controls silent |

Reports: `_audit/FINAL_PRECAD-*.json`, then `_audit/FINAL_PRECAD_RESTART-*.json`
after the last correction. All restart reports share one snapshot-manifest hash.

**This is not physical validation.** No CAD or physics work exists.

## Manifests

| Manifest | Artifacts | Hash |
|---|---|---|
| `SOURCE_FREEZE.yaml` | 13 | `cb74bd8711bbd3a4c71a8038838ca997a559ac6902a099d04a6dda48acfcb1a5` |
| `SEMANTIC_AUTHORITY.yaml` | 2 | `9d447f0092defe22c92f7fe2dda7cd93af4168a3f9ac0ebbef43b352a6d0c600` |

Neither changed this pass — no source or semantic-authority artifact was touched,
which is correct: only active conclusions were corrected. Both were re-verified by
an independent process: every artifact hash recomputed, no self-reference, no
overlap between layers. The CAD-counterexample procedure remains executable —
source bytes immutable, semantic authority versioned and challengeable.

## Remaining ambiguities

`AMB-001-2-01` (BM-001-2, **blocking, source-level**), `AMB-002-01`, `AMB-002-02`,
`AMB-001-3-01` (non-blocking). BM-001-2 remains `BLOCKED_BY_SOURCE_AMBIGUITY`; no
new rank-1 source material was supplied.

## Unresolved CAD questions

All 44 admissible fixtures remain `NEEDS_GEOMETRY_VALIDATION`. `PU-01…PU-12` in
the baseline are unchanged. Three were re-confirmed as the direct consequence of
this pass's corrections: `PU-03` (does `ADM-HS-E`'s flexure/rib coverage actually
overlap — now admissible where it was rejected), `PU-07` (is the declared contact
tolerance small enough that no real penetration hides inside it), and
`ADM-HS-F`'s field barrier.

## Backlogged rather than corrected

8 entries in `PRE_CAD_BACKLOG.yaml` —
2 documentation-only,
2 future auditor enhancements,
1 post-CAD cleanup,
3 physical questions for CAD.
**None blocks CAD entry.** Each records why it fails the scope test, so a later
reader can see it was deferred deliberately rather than missed.

## No lock, no CAD, no production code

No `LOCK.json`. No STEP, B-rep, STL, mesh or geometry file. No executable geometry
fixture. No production pipeline code — the only two Python files under `ver3/` are
the read-only auditor and its mutation suite. No `ver3/assy3`. No file outside
`ver3/` was modified.

---

**This was the final bounded pre-CAD semantic correction. Further Oracle changes
require an actual CAD counterexample, newly supplied source material, or a defect
that demonstrably changes CAD classification.**
