# CI HYGIENE CORRECTION — POST-S2

Narrow correction of stale CI enforcement. **Not S-3, not an architecture review, not a
continuation of S-2.** No stage engineering behaviour, prompt, fixture, benchmark, model
behaviour, architecture document or canonical S-2 semantic was changed.

---

## 1. Baseline

| | |
|---|---|
| **HEAD at start** | `9f43bfd` |
| **S-2 implementation commit** | `9f43bfd` — *S-2: canonical contract migration (U-2B / M-2B)* |
| **Branch → upstream** | `ver3-cad-positive-reference-pilot` → `origin/ver3-windows-s01-s04` (in sync) |
| **Working tree** | clean apart from the two untracked `.gitignoreJoey…` files, deliberately untouched |

## 2. CI failures before correction

Captured by running the current `.github/workflows/ver3-boundaries.yml` step by step. **The
post-S2 failure set was verified, not assumed** — and it is exactly two.

| Failure | Exact command | Current error | From S-2? | Pre-existing? | Stale rule? | Real defect? | Action |
|---|---|---|---|---|---|---|---|
| `test_only_permitted_historical_occurrences_remain` | `python -m unittest discover -s ver3/tests/meta -t .` | `docs/audit/AUDIT_EVIDENCE_LOG.md:310` contains the old package token | **No** | **Yes** — since `dc65de9`, the audit documentation commit | **Yes** | No | **CLASS A** — corrected |
| `No stages package exists` | `if [ -d ver3/assy_v3/stages ]; then exit 1; fi` | the directory exists (6 modules) | No | Yes — since stages were built | **Yes** | No | **CLASS A** — retired, property preserved |

**Steps that passed:** meta discover (apart from the row above), and the `assy_v3` import
boundary.

## 3. Classification

- **CLASS A — stale CI / false positive:** both failures. Fixed here.
- **CLASS B — real regression caused by S-2:** **none.** All 22 S-2 contract tests
  (CON-01…CON-18, authority hierarchy, contract immutability) passed *before* this correction
  and pass after. No S-2 check was weakened, and none was reclassified as hygiene.
- **CLASS C — pre-existing real defect:** none found in scope.

## 4. Stale rule 1 — package path

**The rule's own docstring already states the property:** *"The property worth protecting is
not the spelling. It is that no ALIAS exists."* The scan had drifted from that: it read a
**frozen record describing the rename** — "the path went from X to Y" — as an active path
reference.

The two available bad fixes were rejected: falsifying a frozen audit record, and pinning one
exact line. Instead the rule now distinguishes, semantically:

| | |
|---|---|
| **ACTIVE SURFACE** | code, configuration, workflows, current authoritative documentation — **all still scanned** |
| **FROZEN HISTORICAL EVIDENCE** | declared by directory class with a reason. One entry: `docs/audit/` — the frozen audit corpus. P4B is COMPLETE AND FROZEN and three records carry SUPERSEDED HISTORICAL AUDIT RECORD banners; one records the rename event itself |

`.github/` is deliberately **not** frozen: a workflow is active configuration. `ver3/oracles/`
keeps its existing file-level allowlist, which `ACP-001.not_changed` justifies — that coupling
is untouched.

`_scan_repo_for_old_token()` is now parameterised by root so the rule itself is testable.

## 5. Stale rule 2 — "No stages package exists"

| | |
|---|---|
| **Original purpose** | the progression gate: stage code must not appear before its contract has been through `STAGE_PROGRESSION_CONTRACT` step 1 |
| **What is obsolete** | the **lifecycle assumption**, not the purpose — that the correct number of stage modules is zero |
| **Current reality** | S01–S04 exist deliberately; S-1 and S-2 have already migrated them |
| **Still valid?** | **No** as written. `"stages exist"` cannot be a failure condition |
| **Action** | retired, and **not** replaced with unconditional success |

**The property outlived the assertion.** `tests/meta/test_no_stage_implementation.py` already
carries the evolved form — *"once stage work begins, it fails on any stage module whose
contract has not been through step 1"* — and passes 6/6. The workflow step now invokes that
test plus `test_no_legacy_imports` and `test_package_path` **by name**, so a failure reports
the property rather than the milestone, and retiring the shell check reduces no coverage.

## 6. Adjacent rules reviewed (§5)

| Rule | Original purpose | Current reality | Still valid? | Action |
|---|---|---|---|---|
| `Meta tests (discover)` | run every boundary check | unchanged, now 337 tests | **Yes** | none |
| `assy_v3 imports cleanly` | catch an import-time dependency the AST scan misses | the **rule** is valid and now more meaningful; only its stated premise (*"an empty boundary that imports nothing"*) was scaffold-era | **Yes** | comment premise corrected, **rule unchanged** |
| `Install PyYAML` | stdlib-only, no project install | unchanged | **Yes** | none |
| `on: paths: ['ver3/**', ...]` | trigger scope | **Observation, not changed:** the package-path scan treats `docs/architecture` and `docs/implementation` as active surface, but a change there alone does not trigger the workflow. This is a trigger-scope gap that pre-dates the stage transition and is not a stale lifecycle assertion; changing it would alter when CI runs, which is outside this task | n/a | documented only |

## 7. Negative controls

A green workflow is not evidence on its own. Three controls were added:

| Control | Expectation | Result |
|---|---|---|
| old token in `ver3/assy_v3/*.py`, `ver3/contracts/*.yaml`, `.github/workflows/*.yml`, `docs/architecture/*.md` | **rejected** | all 4 detected |
| old token in a `docs/audit/` record describing the rename | **allowed** | no hit |
| the frozen class stays narrow | exactly one directory; `ver3`, `docs/architecture`, `docs/implementation`, `.github` are all active | holds |

For the stage rule the control is the retained test itself: a stage module whose contract has
not been through step 1 still fails, while the intentional existence of six stage modules does
not.

## 8–10. Regression results

| Suite | Result |
|---|---|
| **S-1** state authority | **69/69 OK** |
| **S-1** ADR-001 Level 1 | **8/8 OK** |
| **S-1** ADR-001 Level 2 | **65/65 OK** |
| **S-2** canonical contracts (CON-01…CON-18, immutability) | **22/22 OK** |
| Full meta suite | **337 tests, OK (1 skipped)** — was 334 with 1 failure |
| Workflow step: `assy_v3` import boundary | **OK** |
| Workflow step: progression gate + package boundary | **30/30 OK** |
| `tests/window` (not in CI) | **8/8 OK** |

## 11. Remaining failures

**None.** Every step of the workflow equivalent passes locally.

## 12. Expected GitHub Actions outcome

**Green**, for the first time since the stage modules were built. The two failing conditions
were the only ones, both were stale lifecycle encodings, and neither was silenced: one was
narrowed semantically with negative controls, the other was replaced by the test that carries
its evolved property.

**Local expected green is not remote actual green.** If the remote run fails for a new reason,
that reason is to be classified before anything is edited.

## 13. Files changed

`.github/workflows/ver3-boundaries.yml` · `ver3/tests/meta/test_package_path.py` ·
`docs/implementation/evidence/CI_HYGIENE_CORRECTION.md` (new).

**No contract, no stage module, no prompt, no fixture, no architecture document and no S-1 or
S-2 implementation file was touched.** No frozen audit text was altered.

> **CI HYGIENE COMPLETE — CURRENT CI IS ALIGNED WITH POST-S2 REPOSITORY.**
>
> S-3 has not begun.
