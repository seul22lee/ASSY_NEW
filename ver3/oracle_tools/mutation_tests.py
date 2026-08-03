#!/usr/bin/env python3
"""Reproducible mutation tests for the Oracle auditor.

WHY THIS EXISTS
    A clean audit means nothing if the auditor is blind. Every time a check is
    relaxed to remove a false positive, the relaxation can silently disable the
    check. This suite injects a known defect for every rule and asserts the
    auditor reports it, and injects a CONTROL for every relaxed heuristic and
    asserts the auditor stays silent.

    It is a test definition, not a one-off script run in a temporary directory:
    it is versioned beside the auditor and re-runnable.

HOW IT WORKS
    Each case copies the whole `ver3/` tree to a scratch directory, applies one
    mutation, runs the auditor against the copy, and compares the set of defect
    types reported. Nothing under the real tree is written.

USAGE
    python3 ver3/oracle_tools/mutation_tests.py [--keep] [--scratch DIR]
    Exit code 0 = every case behaved as specified.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
import yaml

VER3 = Path(__file__).resolve().parent.parent
P, M = "oracles/product_cases", "oracles/micro_oracles"

CASES = []


def case(name, kind, expect, note):
    """kind: 'defect' (expect must appear) or 'control' (expect must NOT appear)."""
    def deco(fn):
        CASES.append(dict(name=name, kind=kind, expect=expect, note=note, fn=fn))
        return fn
    return deco


def ry(root, rel):
    return yaml.safe_load((root / rel).read_text())


def wy(root, rel, d):
    (root / rel).write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))


# ---------------------------------------------------------------- 3A
@case("locator_req_unresolvable", "defect", "LOCATOR_DOES_NOT_RESOLVE",
      "a citation of a REQ id absent from the frozen dossier")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["invariants"][0]["source_locators"] = ["DOS-BM-002 S1 REQ-999"]
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("locator_section_unresolvable", "defect", "LOCATOR_DOES_NOT_RESOLVE",
      "a citation of a dossier section that does not exist")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    d["invariants"][0]["source_locators"] = ["DOS-guided-slider S99"]
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("direct_from_legacy_section", "defect", "DIRECT_FROM_LEGACY_SECTION",
      "a capability/user statement grounded in S6 realization detail")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    d["invariants"][0]["source_locators"] = ["DOS-guided-slider S1", "DOS-guided-slider S6"]
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("derived_without_premises", "defect", "DERIVED_WITHOUT_PREMISES",
      "a derived statement with no derivation premises")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    d["invariants"][1].pop("derivation_premises", None)
    wy(r, f"{P}/BM-001/normative.yaml", d)


# ---------------------------------------------------------------- 3B
@case("necessity_counterexample", "defect", "NECESSITY_COUNTEREXAMPLE",
      "an admissible design stripped of a tag a derived invariant demands")
def _(r):
    d = ry(r, f"{P}/BM-002/realizations.yaml")
    a = d["admissible_realizations"][0]
    a["tags"] = [t for t in a["tags"] if t != "loaded_elements_reacted"]
    wy(r, f"{P}/BM-002/realizations.yaml", d)


@case("admits_inadmissible", "defect", "ADMITS_INADMISSIBLE_REALIZATION",
      "an inadmissible design given every tag")
def _(r):
    d = ry(r, f"{P}/C4-drawer/realizations.yaml")
    d["inadmissible_realizations"][0]["tags"] = list(d["admissible_realizations"][0]["tags"])
    wy(r, f"{P}/C4-drawer/realizations.yaml", d)


@case("rejects_admissible_evidence_case", "defect", "REJECTS_ADMISSIBLE_EVIDENCE_CASE",
      "an admissible evidence case stripped of a tag a verification minimum demands")
def _(r):
    d = ry(r, f"{M}/latch-retention/evidence_cases.yaml")
    a = d["admissible_evidence_cases"][0]
    a["tags"] = [t for t in a["tags"] if t != "retention_claim_names_its_disturbance"]
    wy(r, f"{M}/latch-retention/evidence_cases.yaml", d)


@case("admits_inadmissible_evidence_case", "defect", "ADMITS_INADMISSIBLE_EVIDENCE_CASE",
      "an inadmissible evidence case given every evidence tag")
def _(r):
    d = ry(r, f"{M}/latch-retention/evidence_cases.yaml")
    d["inadmissible_evidence_cases"][0]["tags"] = list(d["admissible_evidence_cases"][0]["tags"])
    wy(r, f"{M}/latch-retention/evidence_cases.yaml", d)


# ---------------------------------------------------------------- 3C
@case("mechanism_name_in_normative", "defect", "MECHANISM_NAME_IN_NORMATIVE",
      "a mechanism noun in a normative statement")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    d["invariants"][3]["statement"] = "A rack and pinion converts the knob rotation into drawer travel."
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("part_count_prescriptive", "defect", "PART_COUNT_IN_NORMATIVE",
      "a prescribed element count")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["invariants"][6]["statement"] = "The platform is carried on two rails fixed to the housing."
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("anaphoric_count", "control", "PART_COUNT_IN_NORMATIVE",
      "RELAXED HEURISTIC CONTROL: 'the two bodies' is a relation's arity, not a part count")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["invariants"][6]["statement"] = "A constraint acts between the two bodies at every point of travel."
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("dimension_leak", "defect", "DIMENSION_LEAK_IN_NORMATIVE",
      "an unflagged dimensional quantity")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    d["invariants"][2]["statement"] = "The drawer travels 120 mm between its configurations."
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("user_stated_quantity", "control", "DIMENSION_LEAK_IN_NORMATIVE",
      "RELAXED HEURISTIC CONTROL: BM-002's 80-100 mm is user-stated and flagged as such")
def _(r):
    pass  # baseline already contains NRM-BM-002-004 with quantity_is_user_stated


@case("rejected_basis_type", "defect", "REJECTED_BASIS_TYPE",
      "a normative statement grounded in reference-realization detail")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    d["invariants"][2]["basis_type"] = "REFERENCE_REALIZATION_DETAIL"
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("micro_oracle_claims_user_requirement", "defect", "MICRO_ORACLE_CLAIMS_USER_REQUIREMENT",
      "SF-1.3: a micro-oracle presenting its project-authored capability as user language")
def _(r):
    d = ry(r, f"{M}/latch-retention/normative.yaml")
    d["invariants"][0]["basis_type"] = "DIRECT_USER_REQUIREMENT"
    wy(r, f"{M}/latch-retention/normative.yaml", d)


@case("product_case_claims_project_capability", "defect", "PRODUCT_CASE_CLAIMS_PROJECT_CAPABILITY",
      "SF-1.3: a product case, which has a user, using the capability basis")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["invariants"][0]["basis_type"] = "PROJECT_DEFINED_CAPABILITY"
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("micro_oracle_named_for_mechanism", "defect", "MICRO_ORACLE_NAMED_FOR_MECHANISM",
      "a capability pack named after one of its realizations")
def _(r):
    shutil.move(str(r / M / "guided-slider"), str(r / M / "dovetail-slide"))


# ---------------------------------------------------------------- 3D
@case("fixed_stage11_outcome", "defect", "FIXED_STAGE11_OUTCOME",
      "a frozen expected outcome at stage 11")
def _(r):
    d = ry(r, f"{P}/BM-001/stage_expectations.yaml")
    d["stages"]["s11"]["expected_outcomes"] = {"REQ-001": "PASS"}
    wy(r, f"{P}/BM-001/stage_expectations.yaml", d)


@case("unresolved_ref_not_found", "defect", "UNRESOLVED_REF_NOT_FOUND",
      "REGRESSION for the dead `and False` branch: a reference to an undefined unresolved id")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["invariants"][0]["related_unresolved"] = ["UNR-BM-002-999"]
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("child_references_parent_unresolved", "control", "UNRESOLVED_REF_NOT_FOUND",
      "RELAXED HEURISTIC CONTROL: a delta pack may reference an unresolved id defined by its parent")
def _(r):
    d = ry(r, f"{P}/BM-001-3/normative.yaml")
    d["invariants"][0]["related_unresolved"] = ["UNR-BM-001-3-001", "UNR-BM-001-001"]
    wy(r, f"{P}/BM-001-3/normative.yaml", d)


@case("override_without_rank1", "defect", "OVERRIDE_WITHOUT_RANK1_SUPPORT",
      "a delta override with no rank-1 delta source")
def _(r):
    d = ry(r, f"{P}/BM-001-3/normative.yaml")
    d["overrides"][0].pop("rank1_support", None)
    wy(r, f"{P}/BM-001-3/normative.yaml", d)


# ---------------------------------------------------------------- 3E (new rules)
@case("policy_field_missing_enables_claim", "defect", "POLICY_FIELD_MISSING",
      "SF-1.2: a VERIFICATION_MINIMUM that does not name the claim it enables")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    for i in d["invariants"]:
        if i["basis_type"] == "VERIFICATION_MINIMUM":
            i.pop("enables_claim", None)
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("policy_field_missing_evidence_tags", "defect", "POLICY_FIELD_MISSING",
      "SF-1.2: a VERIFICATION_MINIMUM with no evidence tags")
def _(r):
    d = ry(r, f"{M}/bounded-two-state-closure/normative.yaml")
    for i in d["invariants"]:
        if i["basis_type"] == "VERIFICATION_MINIMUM":
            i.pop("requires_evidence_tags", None)
    wy(r, f"{M}/bounded-two-state-closure/normative.yaml", d)


@case("design_evidence_mixed_physical_uses_evidence_tag", "defect", "DESIGN_EVIDENCE_TAG_MIXED",
      "SF-1.1: a physical design made inadmissible for want of a test")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    d["invariants"][0]["requires_evidence_tags"] = ["guidance_observable_can_fail"]
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("design_evidence_mixed_vm_uses_physical_tag", "defect", "DESIGN_EVIDENCE_TAG_MIXED",
      "SF-1.1: a verification minimum constraining a physical design")
def _(r):
    d = ry(r, f"{M}/latch-retention/normative.yaml")
    for i in d["invariants"]:
        if i["basis_type"] == "VERIFICATION_MINIMUM":
            i["requires_tags"] = ["retained_state_defined"]
            break
    wy(r, f"{M}/latch-retention/normative.yaml", d)


@case("design_evidence_mixed_undeclared_tag", "defect", "DESIGN_EVIDENCE_TAG_MIXED",
      "SF-1.1: a tag outside the pack's declared physical vocabulary")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    d["invariants"][0]["requires_tags"] = ["some_undeclared_tag"]
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("direct_requirement_coverage_gap", "defect", "DIRECT_REQUIREMENT_COVERAGE_GAP",
      "SF-5.1 REGRESSION: this is exactly the omission of BM-002 travel and payload")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["invariants"] = [i for i in d["invariants"] if i["id"] != "NRM-BM-002-004"]
    # REQ-002 must disappear from the pack ENTIRELY, or coverage genuinely still
    # exists and the auditor is right to stay quiet. An earlier version of this
    # mutation left it cited by two other invariants and mis-reported the auditor
    # as blind.
    for i in d["invariants"]:
        i["source_locators"] = [x for x in i.get("source_locators", []) if "REQ-002" not in str(x)]
    for u in d["required_unresolved"]:
        u["source_locators"] = [x for x in u.get("source_locators", []) if "REQ-002" not in str(x)]
    wy(r, f"{P}/BM-002/normative.yaml", d)
    s = (r / P / "BM-002" / "stage_expectations.yaml").read_text().replace("REQ-002", "REQ-00X")
    (r / P / "BM-002" / "stage_expectations.yaml").write_text(s)
    for f in ("negative_cases.yaml", "evidence_scope.yaml", "freedoms.yaml", "realizations.yaml",
              "evidence_cases.yaml"):
        fp = r / P / "BM-002" / f
        fp.write_text(fp.read_text().replace("REQ-002", "REQ-00X"))


@case("unresolved_block_scope_quantitative_blocks_structural", "defect", "UNRESOLVED_BLOCK_SCOPE_INVALID",
      "SF-1.4: a missing quantity claiming to block an independent structural predicate")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    d["required_unresolved"][0]["block_scopes"] = ["blocks_structural_predicate"]
    d["required_unresolved"][0]["structural_block_justification"] = "asserted"
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("unresolved_block_scope_unknown", "defect", "UNRESOLVED_BLOCK_SCOPE_INVALID",
      "SF-1.4: an unrecognised block scope")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    d["required_unresolved"][0]["block_scopes"] = ["blocks_everything"]
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("unresolved_legacy_blocks_relation", "defect", "UNRESOLVED_BLOCK_SCOPE_INVALID",
      "SF-1.4: the retired coarse `blocks:` relation reappearing")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    d["required_unresolved"][0]["blocks"] = ["NRM-BM-001-011"]
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("interpretive_blocks_structural_with_justification", "control", "UNRESOLVED_BLOCK_SCOPE_INVALID",
      "RELAXED HEURISTIC CONTROL: BM-001-2's AMB-001-2-01 legitimately blocks a structural "
      "predicate, because the predicate's DOMAIN is undefined rather than a threshold missing")
def _(r):
    pass  # baseline already contains it


@case("source_entailment_review_missing_entry", "defect", "SOURCE_ENTAILMENT_REVIEW_REQUIRED",
      "SF-1.5: a statement with no recorded entailment review")
def _(r):
    d = ry(r, "oracles/SOURCE_ENTAILMENT_REVIEW.yaml")
    d["reviews"] = [x for x in d["reviews"] if x["statement_id"] != "NRM-C4-005"]
    wy(r, "oracles/SOURCE_ENTAILMENT_REVIEW.yaml", d)


@case("statement_reviewed_unsupported", "defect", "STATEMENT_REVIEWED_UNSUPPORTED",
      "SF-1.5: a statement the review itself concluded is unsupported")
def _(r):
    d = ry(r, "oracles/SOURCE_ENTAILMENT_REVIEW.yaml")
    for x in d["reviews"]:
        if x["statement_id"] == "NRM-C4-005":
            x["review_result"] = "unsupported"
    wy(r, "oracles/SOURCE_ENTAILMENT_REVIEW.yaml", d)


@case("fixture_plausibility_missing", "defect", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
      "SF-1.6: an admissible fixture with no plausibility review")
def _(r):
    d = ry(r, "oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml")
    d["reviews"] = [x for x in d["reviews"] if x["fixture_id"] != "ADM-BM-002-C"]
    wy(r, "oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml", d)


@case("fixture_plausibility_no_assumptions", "defect", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
      "SF-1.6: a fixture presented as admissible with no explicit assumptions")
def _(r):
    d = ry(r, "oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml")
    for x in d["reviews"]:
        if x["fixture_id"] == "ADM-BM-002-C":
            x["assumptions"] = []
    wy(r, "oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml", d)


@case("rejected_fixture_still_admissible", "defect", "REJECTED_FIXTURE_STILL_ADMISSIBLE",
      "SF-1.6: a fixture reviewed as physically REJECTED but still listed admissible")
def _(r):
    d = ry(r, "oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml")
    for x in d["reviews"]:
        if x["fixture_id"] == "ADM-BM-001-3-B":
            x["status"] = "REJECTED"
    wy(r, "oracles/FIXTURE_PLAUSIBILITY_REVIEW.yaml", d)


@case("needs_geometry_validation_is_fine", "control", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
      "RELAXED HEURISTIC CONTROL: every fixture is NEEDS_GEOMETRY_VALIDATION in the baseline "
      "and that is an honest status, not a defect")
def _(r):
    pass  # baseline


@case("conditional_load_domain_violation", "defect", "CONDITIONAL_LOAD_DOMAIN_VIOLATION",
      "SF-5.3/SF-6.5: a support predicate quantifying over elements that carry no such load")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-002-006":
            i["verification_predicate"] = "for each rotating element: exists(radial support realization)."
            i.pop("applies_when", None)
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("load_predicate_with_applies_when", "control", "CONDITIONAL_LOAD_DOMAIN_VIOLATION",
      "RELAXED HEURISTIC CONTROL: the baseline's load-conditional predicates must stay silent")
def _(r):
    pass  # baseline


@case("unconditional_terminal_bound", "defect", "UNCONDITIONAL_TERMINAL_BOUND",
      "SF-5.6/SF-6.3: a terminal determinant demanded where the source declares no travel limit")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-C4-007":
            i.pop("applies_when", None)
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("source_declared_terminal_states", "control", "UNCONDITIONAL_TERMINAL_BOUND",
      "RELAXED HEURISTIC CONTROL: bounded-two-state-closure's bounds ARE its capability "
      "statement, verified against the frozen dossier text")
def _(r):
    pass  # baseline


@case("terminal_exemption_fragment_not_in_dossier", "defect", "UNCONDITIONAL_TERMINAL_BOUND",
      "the source-declared exemption must be grounded, not asserted")
def _(r):
    d = ry(r, f"{M}/bounded-two-state-closure/normative.yaml")
    d["source_declares_terminal_states"]["verbatim_fragment"] = "this text is not in the dossier"
    wy(r, f"{M}/bounded-two-state-closure/normative.yaml", d)


@case("fixed_candidate_plurality", "defect", "FIXED_CANDIDATE_PLURALITY",
      "SF-8.3: a rule requiring more than one candidate to survive")
def _(r):
    d = ry(r, f"{M}/rotary-to-linear-engagement/stage_expectations.yaml")
    d["stages"]["s02"]["plurality_note"] = "More than one conversion family must survive s02."
    wy(r, f"{M}/rotary-to-linear-engagement/stage_expectations.yaml", d)


@case("predicate_stronger_than_statement", "defect", "PREDICATE_STRONGER_THAN_STATEMENT",
      "a predicate universally quantified where its statement is not, with no recorded review")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-001-001":
            i["verification_predicate"] = "for every state of the design: the transition is traversable."
    wy(r, f"{P}/BM-001/normative.yaml", d)
    e = ry(r, "oracles/SOURCE_ENTAILMENT_REVIEW.yaml")
    for x in e["reviews"]:
        if x["statement_id"] == "NRM-BM-001-001":
            x["predicate_scope_reviewed"] = False
    wy(r, "oracles/SOURCE_ENTAILMENT_REVIEW.yaml", e)


@case("pack_file_missing", "defect", "PACK_FILE_MISSING",
      "an unauthored pack file must never pass silently")
def _(r):
    (r / M / "guided-slider" / "evidence_cases.yaml").unlink()


def run_case(c, scratch, keep):
    root = scratch / c["name"]
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(VER3, root, ignore=shutil.ignore_patterns("_audit", "__pycache__"))
    c["fn"](root)
    proc = subprocess.run([sys.executable, str(root / "oracle_tools" / "audit_oracles.py"),
                           "--pass", "all"], capture_output=True, text=True)
    types = {l.split()[-1] for l in proc.stdout.splitlines() if l.strip().startswith("[")}
    ok = (c["expect"] in types) if c["kind"] == "defect" else (c["expect"] not in types)
    if not keep:
        shutil.rmtree(root, ignore_errors=True)
    return ok, sorted(types)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep mutated trees for inspection")
    ap.add_argument("--scratch", type=Path, default=None)
    ap.add_argument("--json-out", type=Path)
    a = ap.parse_args()
    scratch = a.scratch or Path(tempfile.mkdtemp(prefix="oracle-mut-"))
    scratch.mkdir(parents=True, exist_ok=True)

    rows, failed = [], 0
    for c in CASES:
        ok, types = run_case(c, scratch, a.keep)
        rows.append(dict(name=c["name"], kind=c["kind"], expect=c["expect"],
                         note=c["note"], passed=ok, reported=types))
        if not ok:
            failed += 1
        flag = "ok  " if ok else "FAIL"
        print(f"  [{flag}] {c['kind']:7s} {c['name']:<48s} {c['expect']}")
        if not ok:
            print(f"          reported: {types}")
    defects = sum(1 for c in CASES if c["kind"] == "defect")
    controls = len(CASES) - defects
    summary = dict(total=len(CASES), defect_cases=defects, control_cases=controls,
                   failed=failed, passed=len(CASES) - failed)
    print(json.dumps(summary, indent=2))
    if a.json_out:
        a.json_out.write_text(json.dumps(dict(summary=summary, cases=rows), indent=2) + "\n")
    if not a.keep:
        shutil.rmtree(scratch, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
