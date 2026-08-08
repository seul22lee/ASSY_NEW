# Implementation report — window S01 + S02

**Scope.** Close the RED contract defects, implement S01 and S02 as one
producer-consumer window, evaluate on all three benchmarks, classify every
failure, perform one integrated revision, run one regression.

**S03 and later were not implemented.**

**Final state:** 313 tests pass (309 meta + 4 window). All window checks report
nothing on all three cases.

---

## 1. RED fixes

Five failures in 309 meta tests, closed in one pass.

| defect | fix |
|---|---|
| `ENTITY_FAMILY_AUDIT` audited 32 families; the contract had 38 keys | audit re-run over the real set; five new entries with consumer justifications; scope note recording that the growth came from a contract change, not from the audit |
| `CompliantJoint` had its own family key and no owner | **folded into `Joint` as a `compliant_variant`.** This implements proposal decision D-2 ("compliance is a `Joint` between `RigidGroup`s") rather than making a new decision — a separate key contradicted it and left the variant ownerless |
| BM-003 descriptor said `positive_executable_reference: NOT_BUILT`; one exists | descriptor updated with location, `status: BUILT_VALIDATION_DEFERRED`, and an explicit `never_a_precondition` field |
| two meta tests asserted "no BM-003 reference exists" | rewritten to assert the **invariant they were protecting** — that a reference is never a precondition for scoring, and that no Oracle file cites one — instead of the absence that used to imply it |
| `AssemblyStep` duplicated `Configuration` without a recommendation | recorded `MERGE_CANDIDATE` with a recommendation and a deadline: keep both, revisit if s04 reads only one |

No architecture decision was reopened.

---

## 2. S01 implementation

`ver3/assy_v3/stages/s01_requirement_capture.py`

Prompt construction → provider call → parse → contract validation → `StagePatch`.
Creates `Requirement`, `SourceClause`, `Scenario`, `Actor`, `Freedom`,
`Ambiguity`, `Assumption`. Carries `quantity_class` per requirement and `kind`
per scenario, both required by the contract and both absent from the previous
architecture.

Three checks it owns: `sharpening_check` (no numeral in a requirement that is
absent from the source), `locator_check` (every requirement resolves to a
clause), `mechanism_leakage_check` (S01 names no mechanism the source did not).

## 3. S02 implementation

`ver3/assy_v3/stages/s02_obligation_and_candidates.py`

Consumes **only** `project_for("s02", state)`. The projection physically removes
`SourceClause`, so INV-002 is enforced by the boundary rather than by the stage
behaving well — the stage raises if handed source text.

Creates `Obligation`, `LoadCase`, `Candidate`, `AcceptanceContract`,
`UnresolvedDecision`, `Assumption`. Eleven checks, including the five added
during the revision.

**Knowledge boundary.** Two modules, both product-independent:

- `knowledge/principle_library.py` — 37 principle families indexed by **function
  class**, never by product noun. A stage supplies a function class it derived
  from obligations and receives every family that performs it. This is the
  structure that makes `box → hinge`, `shaft → bearing` and `lift → lead screw`
  unreachable: no key in the library is a product.
- `knowledge/capability_registry.py` — which analysis routes exist. Five of nine
  are unavailable, and S02 records that per candidate instead of quietly avoiding
  the families that need them.

No benchmark identifier appears anywhere in `assy_v3/`.

---

## 4. Benchmark results

| | BM-001 | BM-002 | BM-003 |
|---|---|---|---|
| S01 / S02 | SUCCESS / SUCCESS | SUCCESS / SUCCESS | SUCCESS / SUCCESS |
| requirements | 10 | 11 | 19 |
| obligations | 13 | 14 | 17 |
| load cases | 5 | 4 | 5 |
| candidates | 5 | 6 | 6 |
| unresolved decisions | 3 | 3 | 4 |
| freedoms / ambiguities | 6 / 6 | 7 / 7 | 9 / 10 |

Design space preserved in every case: five to six genuinely distinct candidates
survive, each differing in at least one principle family, with the openness
recorded rather than resolved. No candidate carries a score, a rank or a
selection field.

Two results worth naming, because they are the behaviours the architecture was
built for:

- **BM-002** produced six conversion families — crank-slider, screw-and-nut,
  rack-and-pinion, cam-and-follower, flexible-element, lever-linkage — and
  recorded that three of them depend on claims no available route can establish.
  It did not prefer the evidenceable ones.
- **BM-001** and **BM-003** produced load cases with `magnitude_or_status:
  UNSUPPORTED` throughout, because neither source states a load. The one
  magnitude in the corpus, BM-002's `approximately 1 kg`, was carried unsharpened
  from a `BAND` requirement.

---

## 5. Interface findings

`project_for("s02")` removed `SourceClause` on all three cases; S02 never saw
source text.

**What S02 needed that S01 did not provide:** nothing, after the revision.

**What S01 produced that S02 never used:** initially everything except
requirements and scenarios. After the revision, only items whose consumer is a
later stage — dimensional and material freedoms (S03/S05/S06), quantitative
ambiguities (S11 scope blocking), and ASSEMBLY/TRANSPORT scenarios (S03 assembly
plan). Recorded as debt D-1 rather than forced into S02.

**Information represented too weakly:** `UnresolvedDecision.alternatives` mixed
entity IDs with free text and principle-family names in one untyped list. Fixed.

---

## 6. Failure classification

Twelve findings. The first execution found five before any benchmark result
existed.

| id | finding | class | sub-class |
|---|---|---|---|
| F-1 | validator treated `[]` as a missing required field | validator | representation too weak |
| F-2 | `Actor` created by S01's contract, absent from `DESIGN_STATE_CONTRACT` | specification/contract | missing information |
| F-3 | mechanism-leak check flagged source vocabulary (`crank`) and function words (`support`, `hold`, `turn`) — 11 false positives, 0 true | validator | unsupported inference |
| F-4 | the harness carried benchmark IDs inside `assy_v3/` (FP-02, R-14) | pipeline/interface | — |
| F-5 | the no-stage-implementation guard needed the conversion its own docstring described | validator | — |
| F-6 | every `Freedom` and every `Ambiguity` unreferenced by S02 on all three cases | pipeline/interface | **consumer reconstruction** |
| F-7 | `Actor` unreferenced on all three cases | pipeline/interface | dead information |
| F-8 | `alternatives` list untyped | representation/schema | representation too weak |
| F-9 | 2–3 requirements per case silently un-obligated | specification/contract | missing information |
| F-10 | `Candidate.family` redundant with `principle` | representation/schema | dead information |
| F-11 | 7–9 mandatory obligations per case unaddressed by any candidate | representation/schema | **missing information** |
| F-12 | no coverage checks existed at all | validator | missing information |

### Root causes

- **RC-A — S02 restated in prose what S01 had already typed.** F-6, F-7, and half
  of F-9. Its `why_open` fields re-derived ambiguities that arrived as entities,
  so nothing could tell whether the two agreed.
- **RC-B — the obligation model had no dimensions with which to read coverage.**
  F-11, F-9. An obligation every candidate must satisfy looked identical to one
  every candidate ignored.
- **RC-C — validators were crude or absent.** F-3, F-8, F-10, F-12.

---

## 7. Integrated revision

One revision, then one regression.

**RC-A.** `UnresolvedDecision` gains `kept_open_by` (typed refs to `Ambiguity` /
`Freedom`) and `alternatives_kind`. `Obligation` gains `involves_actors`. S02's
prompt now forbids restating an ambiguity it was given as an entity.

**RC-B.** `Obligation` gains three fields:

- `scope: UNIVERSAL | CANDIDATE_DISCRIMINATING` — an assembly sequence is
  universal; which conversion family satisfies a motion obligation is not.
- `satisfiable_at: s02 | s03 | s04 | s05` — **added during the regression.** A
  candidate at S02 is a principle family, not a mechanism, so "every element
  carrying a load component has a reaction" cannot be addressed there at all.
  Without this, coverage flagged every such obligation and the one real omission
  was invisible among nine false ones.
- `evidence_route` + `route_available` — a requirement whose route does not exist
  is *addressed and un-evidenceable*, which is a different thing from a
  requirement nobody derived an obligation from. Both are now visible.

**RC-C.** The mechanism-leak check now exempts any token present in the source
and uses distinctive mechanism nouns rather than words decomposed out of family
names. Five checks added: `requirement_coverage`, `obligation_scope`,
`candidate_coverage`, `openness_citation`, `actor_citation`.

**Regression.** All findings cleared except one, which was the check working:
BM-002's `OBL-0009` ("driven only by the user's input") is genuinely
candidate-discriminating at S02 — every candidate uses `DIRECT_MANUAL` and so
does address it — and the recorded response had simply omitted it. Corrected.

---

## 8. Remaining debts

| id | debt | blocks S03? |
|---|---|---|
| D-1 | Freedoms, ambiguities and non-operational scenarios are consumed at S03+/S11, not S02. The harness reports them as unused; they are not dead. | no |
| D-2 | The recorded responses are authored fixtures, not live provider output. The window is deterministic and testable; it has not been run against a live model. | no |
| D-3 | `Candidate.family` remains redundant with `principle` (F-10). Harmless; folding it in is a contract change with no current consumer. | no |
| D-4 | `Actor` and the five new families are still not projected by `GENERATED_ASSURANCE_PACKAGE_CONTRACT`. Recorded in the family audit as `package_debt`. | no |
| D-5 | Obligation `scope` and `satisfiable_at` were assigned in fixtures partly by keyword heuristic and hand-corrected where the checks objected. A live S02 must derive them, and D-3 from the maturity audit — LLM disposition reliability — applies. | no |
| D-6 | S02's candidate-generation *method* is still the prompt plus the principle library. The maturity audit rated this L2 for that reason and the rating stands. | no |

---

## 9. Window readiness verdict

Against the eight completion criteria:

1. **S01 satisfies its objective** — typed requirements with quantity classes,
   scenarios with kinds, actors, freedoms, ambiguities, provenance to clauses,
   no sharpening, no mechanism the source did not name. ✔
2. **S02 satisfies its objective** — obligations with scope and evidence route,
   candidate-independent load cases, five to six distinct candidate families,
   obligations created as well as addressed, openness preserved. ✔
3. **S02 operates from S01 structured output alone** — enforced by the
   projection, asserted by a test. ✔
4. **No benchmark-specific logic** — no case identifier in `assy_v3/`; the
   harness and the window test discover cases from the fixtures directory. ✔
5. **Knowledge boundary preserved** — principle families indexed by function
   class, evidence routes in a registry; no product noun is a key anywhere. ✔
6. **Major contract and representation failures corrected** — RC-A, RC-B, RC-C. ✔
7. **Remaining debts recorded and non-blocking** — six, none blocking S03. ✔

**Verdict: the S01 + S02 window is provisionally frozen.**

The next window is **S03 + S04**. S03 inherits from this window: obligations
carrying `satisfiable_at: s03` are the explicit work handover, and
`deferred_obligation_report()` lists them.
