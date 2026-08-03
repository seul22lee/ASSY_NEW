# Post-human-review correction report — GATES 1–6

**Branch:** `ver3-oracle-phase1-review`
**Starting commit:** `abd4b6e1fcc58cbdca0b54c85b9c8085c93e6960`
**Final status:** `PRE_CAD_BASELINE_READY` — **not** LOCK_READY, **not**
PRODUCTION_READY, **not** CAD_VALIDATED.

Six gates were completed in order; no gate began before the previous one was
internally consistent and audited.

---

## GATE 1 — Cross-file semantic drift

The auditor was silent while five authoritative files still asserted rules the
normative files had withdrawn. Silence was not sufficient, and Pass **3F** now
exists to catch that class mechanically.

### 1.1 `ORACLE_METHOD.md` retired semantics

| Exact wording removed or superseded | Where | Replaced by |
|---|---|---|
| *"a guided translation must realize anti-rotation"* | §13.2 rule 1 | the freedoms the instantiating requirement depends on are constrained; the rest are declared (HSD-001) |
| *"a rotation-to-translation realization must localize engagement and react both radial and axial load"* | §13.2 rule 1 | an uninterrupted chain of localized interactions; reaction of load components actually carried (HSD-002) |
| *"a guide that permits translation but realizes no anti-rotation"* | §6 negative-case family | a guide leaving unaccounted for a freedom the requirement depends on |
| *"hinged closure with a travel limit"* | §13.1 micro-oracle definition | bounded two-state closure |
| *"Hinged closure, aperture clearance, real vs absent travel stop"* | §13.4 capability table | continuous constraint coverage with each bound physically produced (HSD-003) |
| *"Guided translation, anti-rotation, travel limits, assembly access"* | §13.4 capability table | guided translation with declared residual freedoms |
| *"Rotation→translation, localized engagement, ratio, radial+axial reaction"* | §13.4 capability table | uninterrupted chain; reaction of carried loads |
| the seven-part content contract | §2 | a **nine-part** contract with §2.1 declaring three fixture domains |

Both retired §13.2 examples are **preserved in a block quote** as illustrations of
the overfitting the document exists to prevent, rather than deleted. New §13.7
tabulates all eight retired rules with the fixture that falsified each.

### 1.2 Dossier amendments — originals preserved

Five additive amendments in `_dossier_amendments/AMENDMENTS.yaml`. **No frozen
dossier was edited.** Each records the original section verbatim, the original
whole-file sha256, the amended statement, an explicit
`scope_of_supersession`, and the approving decision.

| Amendment | Supersedes | Scope | Decision |
|---|---|---|---|
| `AMD-GS-001` | `DOS-guided-slider.md#S1` | capability statement only; S2–S7 keep full authority | HSD-001 |
| `AMD-RL-001` | `DOS-rotary-to-linear-engagement.md#S1` | capability statement only | HSD-002 |
| `AMD-HS-001` | `DOS-bounded-two-state-closure.md#S1` | constraint-persistence and bound-distinctness clauses only; the *bound is physically produced* clause is **unchanged** | HSD-003 |
| `AMD-C4-001` | `DOS-C4-drawer.md#S4` | the **classification** of S4 only; both quoted legacy statements unchanged | HSD-002 |
| `AMD-C4-002` | `DOS-C4-drawer.md#S2` | the reading of the motion fragment only | HSD-004 |

`FROZEN_DOSSIER_MUTATED` is BLOCKING: the auditor re-computes each original hash,
so a silent edit to a "frozen" file cannot pass.

### 1.3 guided-slider drift

| Stale wording removed | File |
|---|---|
| *"one translation retained, five removed"* | `stage_expectations.s04.freedom_accounting_note` |
| *"each of the five non-translational freedoms is shown removed…"* | `stage_expectations.s11 GS-C2` |
| *"swept volume shown to be a proper subset of the corridor"* | `stage_expectations.s11 GS-C5` |
| *"S1, with the non-translational freedoms removed"* as the basis of NRM-GS-002 | `source_map.md` |
| the freedom-accounting paragraph asserting five removals | `README.md` |

`GS-C2` is renamed `GS-C2_freedoms_accounted` and carries a `must_not_fail_when`
clause naming the declared-residual-freedom case.

### 1.4 rotary-to-linear-engagement drift

| Stale wording removed | Now |
|---|---|
| `engagement_site` (singular) at s04 | `interaction_sites` (a list) with a chain note |
| `radial_support_realization` required at s05 | `reaction_realizations_for_carried_loads` |
| `output_rotation_restraint` unconditional at s05 | required only where the chain applies the moment |
| `RL-C2_relation_declared` — a physical FAIL for a missing declaration | `RL-C2_rotation_causes_translation` — physical causation |
| `RL-C5` requiring radial support on the rotating body | reaction for load components actually carried |
| `RL-C1` requiring the engagement between input and output | the whole chain, with `must_not_fail_when` for no direct engagement |

### 1.5 C4 horizontal statement/predicate mismatch

The statement said *"Does not require the travel to be a straight line, only that
its direction is horizontal"* while the predicate evaluated **one travel axis**.
Statement and predicate disagreed.

Adopted (HSD-004, AMD-C4-002): *the drawer translates along a single straight axis
perpendicular to the gravity direction.* The curved reading is recorded under
`rejected_readings` with its reason, and `NEG-C4-023` makes accepting a curved
path a defect. `realizations.yaml` tag text and `stage_expectations` C4-R2 were
brought into agreement.

### 1.6 Status synchronization

`PRE_CAD_SEMANTIC_REVIEWED` for eight packs, `BLOCKED_BY_SOURCE_AMBIGUITY` for
BM-001-2. `lock_status:` is renamed `pack_status:` everywhere. Status banners were
added to all nine READMEs and all nine source maps. `SEMANTICALLY_AUDITED`,
`STRUCTURALLY_COMPLETE`, `UNDER_SEMANTIC_CORRECTION`, `lock-ready` and
`CAD validated` are gone from every current file; the two historical reports carry
a superseded-terminology banner instead of being rewritten.
`historical_aliases: [hinge-and-stop]` is retained.

### 1.7 Drift checks added (Pass 3F)

`STALE_PACK_STATUS`, `RETIRED_CONTRACT_PRESENT`,
`STAGE_DEMANDS_PERMITTED_FREEDOM`,
`STAGE_UNCONDITIONAL_WHERE_NORMATIVE_CONDITIONAL`,
`SUPERSEDED_SOURCE_WITHOUT_AMENDMENT_REF`, `FROZEN_DOSSIER_MUTATED`,
`AMBIGUITY_BLOCKING_DISAGREEMENT`, `HUMAN_DECISION_REF_UNRESOLVED`.

**Two defects in my own new checks were found by their own tests**, not by
inspection: `"NON_BLOCKING"` contains the substring `BLOCK` and was read as
blocking, and requiring freedoms to be *accounted for* was matched by a pattern
meant to catch requiring them *removed*. Both are fixed and both have controls.

**These checks cannot prove semantic equivalence.** They detect explicit stale
contracts by pattern and by cross-file comparison. Two files can still disagree in
ways no pattern catches.

---

## GATE 2 — Intended contact and assembly

### 2.1 Intended interaction semantics (policy §13)

Six regions are now distinguished: `declared_contact`, `declared_clearance`,
`declared_interference_fit`, `declared_compliant_interaction`,
`undeclared_volumetric_overlap`, and the evaluation's `numerical_tolerance`.

> **The rule is: no undeclared volumetric overlap.**
> The rule is **not**: every pair of parts maintains positive clearance everywhere.

### 2.2 Motion predicates corrected

| Statement | Retired predicate | Now |
|---|---|---|
| `NRM-BM-001-003` | `clearance(swept_volume(closure), enclosure_solid) > 0` | no volumetric overlap outside declared contact / interference-fit / compliant regions |
| `NRM-BM-001-008` | *"does not intersect solid material"* | no undeclared volumetric overlap along the access path |
| `NRM-BM-001-3-003` | `clearance(...) > 0` | same no-undeclared-overlap form |
| `NRM-BM-002-008` | `intersect(platform_solid, housing_material) is empty` | same |
| `NRM-C4-010` | `intersect(drawer_solid, cabinet_material) is empty` | same |
| `NRM-GS-006` | `intersect(...) is empty outside the intended interaction` | same |

`ADM-BM-001-E` — a pin/knuckle joint with **three declared contacts** — is the
fixture that fails if the blanket form returns. Under the retired predicate it
failed three times over for doing exactly what it is designed to do.

### 2.3 Assembly predicates corrected

`NRM-BM-001-010`, `NRM-BM-002-012` and `NRM-C4-011` all read *"exists(installation_path)
**collision-free** against already-placed parts"*. A press fit has no
collision-free path and is still assemblable.

Now: a **realizable installation process** passing through no **undeclared rigid**
material, with intended contact allowed, and press / snap / interference /
compliant insertion allowed **only when declared** with deformation, material,
direction and process assumptions represented. Force adequacy is separated into
three new quantitative unresolved decisions — `UNR-BM-001-009`, `UNR-BM-002-008`,
`UNR-C4-008` — none of which blocks a structural predicate.

### 2.4 Fixtures added

**Admissible:** `ADM-BM-001-E` (pin/guide with declared contact),
`ADM-BM-001-F` (snap fit with declared compliant insertion), `ADM-BM-001-G`
(interference fit with explicit process and material assumptions). Each carries an
`interaction_regions[]` classification.

**Inadmissible:** `INA-BM-001-H` (undeclared overlapping solids), `INA-BM-001-I`
(3 mm penetration labelled "contact"), `INA-BM-001-J` (rigid pin through an
installed rigid wall), `INA-BM-001-K` (snap narrative with no compliant region),
`INA-BM-001-L` (interference fit with no process assumption). Seven negative cases
`NEG-BM-001-016…022` accompany them.

Physical and evidence domains remain separate: all seven new fixtures are physical.

### 2.5 Causal verification minima (HSD-006)

`NRM-BM-001-012`, `NRM-HS-007` and `NRM-GS-007` accepted **only** an ablated
control. They now accept **either** direct causal evidence — realizing geometry
exists, the interaction occurs at the relevant configuration, and the behaviour is
caused by it — **or** a discriminating control. A direct-causal admissible
evidence case was added to each of the three packs.

The discrimination requirement is **not** withdrawn: a criterion that cannot fail
under its own model is still inadmissible under either branch.

### GATE 2 checks (Pass 3G)

`BLANKET_CLEARANCE_PREDICATE`, `INTERACTION_REGION_UNCLASSIFIED`,
`DECLARED_FIT_WITHOUT_ASSUMPTIONS`, `ABLATION_ONLY_VERIFICATION_MINIMUM`.

A third check defect was found by its own test: `[^)]*` stops at the first `)`, so
`clearance(swept_volume(x), y) > 0` — the exact nested form the check exists to
catch — slipped through. Fixed.

---

## GATE 3 — Human semantic decisions

`HUMAN_SEMANTIC_DECISIONS.yaml`, six decisions, each with alternatives considered,
the approved interpretation, what was rejected and why, affected files and
statement IDs, and `challengeable_by_cad: true`.

| ID | Kind | Summary |
|---|---|---|
| **HSD-001** | PROJECT_DEFINED_CAPABILITY | guided-slider constrains only the freedoms the instantiating requirement depends on; residual freedoms are **declared**, not forbidden. Rejected: all five always removed. |
| **HSD-002** | PROJECT_DEFINED_CAPABILITY | rotary-to-linear is an uninterrupted **chain**; reactions apply only to loads actually carried. Rejected: one direct engagement, universal radial/axial support. Also reclassifies AMB-C4-01. |
| **HSD-003** | PROJECT_DEFINED_CAPABILITY | bounded-two-state-closure requires continuous constraint **coverage**; the active constraint may change. Rejected: one persistent constraint; endpoint bounds with free flight between. **Scope limit: not every product closure instantiates this micro-oracle.** |
| **HSD-004** | PRODUCT_LANGUAGE_INTERPRETATION | "slides out horizontally" = straight translation along one horizontal axis. Rejected for this baseline: a curved generally-horizontal path. |
| **HSD-005** | PRODUCT_LANGUAGE_INTERPRETATION | "rests on a curved back" requires the **load-bearing** contact on the curved region. Stability remains unresolved. |
| **HSD-006** | VERIFICATION_METHODOLOGY | direct causal evidence **or** a discriminating control; a control is not mandatory. |

The three decision kinds keep project-defined capabilities distinguishable from
product readings and from evidence methodology. **None is a user requirement**, and
the record says so.

---

## GATE 4 — Audit provenance

Every report now carries: `run_id`, UTC timestamp, `base_commit_sha` with an
explicit note that it identifies the *starting commit only*, worktree state and
tracked-change count, `snapshot_manifest_hash`, `oracle_tree_hash`, file count,
auditor sha256, mutation-suite sha256, Python version, runtime, exact command,
audit mode, shuffle seed, exact pack order, pack-order digest, and counts by pass
and severity.

The worktree is **uncommitted**, and the reports say so rather than implying a
committed snapshot.

Prior `FINAL-*` and `RESTART-*` reports are preserved untouched. New reports use
`POST_HUMAN3-*` and `POST_HUMAN3_RESTART-*`.

| Report | Result |
|---|---|
| `_audit/POST_HUMAN3_RESTART-canonical.json` | 0 BLOCKING, 0 MAJOR across 3A–3G |
| `_audit/POST_HUMAN3_RESTART-shuffled-20260802.json` | 0 / 0 |
| `_audit/POST_HUMAN3_RESTART-shuffled-4177.json` | 0 / 0 |
| `_audit/POST_HUMAN3_RESTART-shuffled-90210.json` | 0 / 0 |
| `_audit/POST_HUMAN3_RESTART-mutation.json` | 69/69 — 57 injected defects caught, 12 controls silent |

All four audit reports share snapshot manifest
`e9d1de30592cfcf132708231d4ab91c2accfe075683e0a13c64dd127d2db83df`.

The sequence was restarted in full after the last correction, as required — the
first restart was invalidated when status files were edited, and it was re-run.

**This audit does not prove CAD or physical truth**, and the auditor's own
docstring and every report say so.

---

## GATE 5 — Source freeze

`SOURCE_FREEZE.yaml` — `freeze_scope: SOURCE_ONLY`, `semantic_lock: false`,
`cad_validated: false`, `challengeable_by_cad: false`.

15 artifacts: nine frozen dossiers, the dossier index, the amendments record, the
human decisions record, two ambiguity records, and `ORACLE_METHOD.md` for its
source-precedence content only. Each carries path, role, original-or-amendment,
sha256, authority rank, supersession relation, applicable pack, unresolved
ambiguity IDs and human decision IDs.

**Source manifest hash:** `771fd04413ec966da09666d765d193e11cdf4f74d7433d44411b6423b9199e1e`

Not frozen: normative conclusions as physically final, physical fixtures, evidence
fixtures, stage expectations, CAD predicates, evaluator outputs, future CAD
results.

The source is not challengeable by CAD; conclusions drawn from it are. BM-001-2
retains `AMB-001-2-01` as a **source-level** lock blocker: not a missing quantity
but an undefined predicate domain. Every normative source locator was verified to
resolve through the freeze or an approved amendment.

---

## GATE 6 — Pre-CAD baseline

`PRE_CAD_BASELINE.yaml` — `status: PRE_CAD_BASELINE_READY`,
`baseline_type: CHALLENGEABLE_SEMANTIC_BASELINE`, `source_frozen: true`,
`semantic_final: false`, `cad_validated: false`, `production_authority: false`.

**Baseline manifest hash:** `e4b05bac815c362e28c887a74ff46a29c599798e98b65da5c55a212dd0a57dfe`
over **113 files** — policy, method, decisions, freeze, all nine packs' seven YAML
files plus source map and README, dossiers, ambiguities, amendments, the three
review records, both tools, and the five final audit reports.

Ten physical uncertainties `PU-01…PU-10` are named as first CAD targets, and a
seven-step revision procedure distinguishes a wrong statement from a wrong fixture
from a wrong **decision** from a wrong **reading** — a decision is never revised
implicitly by editing a pack, and a CAD result never revises the source freeze.

---

## Files amended rather than overwritten

| File | How |
|---|---|
| nine `_dossiers/DOS-*.md` | **untouched**; superseded sections carry additive amendments with the original text verbatim and the original hash |
| `ORACLE_METHOD.md` §13.2 | retired examples preserved in a block quote, marked retired |
| `ORACLE_VALIDATION_REPORT.md` | superseded-terminology banner added; body preserved |
| `INDEPENDENT_SEMANTIC_REVIEW_REPORT.md` | preserved as the record of the previous pass |
| `_audit/FINAL-*`, `_audit/RESTART-*`, `_audit/CLEAN*`, `_audit/AUDIT-run1` | preserved untouched |
| `product_cases/C4-drawer` `UNR-C4-002` | retained under `retired_unresolved` with its reason |

---

## Remaining source ambiguities

| ID | Pack | Blocking | Note |
|---|---|---|---|
| `AMB-001-2-01` | BM-001-2 | **yes, source-level** | three readings of "worked from inside the enclosure"; none selected |
| `AMB-002-01` | BM-002 | no | is the crossing element part of the enclosed mechanism? |
| `AMB-002-02` | BM-002 | no | where is the compliance edge of "approximately"? |
| `AMB-001-3-01` | BM-001-3 | no | what does "rests" require of stability? |

`AMB-C4-01` is retired to `LEGACY-CONFLICT-C4-01` — conflicting lower-rank legacy
commentary, blocking nothing, requiring no human ruling.

---

## Physical questions deferred to CAD

All 44 admissible fixtures are `NEEDS_GEOMETRY_VALIDATION`; none was upgraded.
`PU-01…PU-10` in the baseline name the ten sharpest, including whether
`ADM-BM-001-3-B`'s three lobe apexes are coplanar, whether `ADM-HS-E`'s flexure
and rib overlap in coverage or leave an unconstrained band, whether
`ADM-BM-002-E`'s required 40–50 mm crank throw fits a desktop envelope, and
whether `ADM-BM-001-E`'s declared numerical contact tolerance is small enough that
no real penetration hides inside a contact declaration.

---

## No final lock was created

**No `LOCK.json` exists.** No production pipeline code, no CAD, STEP, B-rep, STL,
mesh or geometry fixture, and no file outside `ver3/` was modified. The only two
Python files under `ver3/` are the read-only auditor and its mutation suite.

The next authorized phase is **adversarial CAD validation** — not production
implementation and not a final Oracle lock.
