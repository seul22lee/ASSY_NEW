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
    d = ry(r, f"{P}/BM-001-2/normative.yaml")
    d["invariants"][0]["related_unresolved"] = ["UNR-BM-001-2-001", "UNR-BM-001-001"]
    wy(r, f"{P}/BM-001-2/normative.yaml", d)


@case("override_without_rank1", "defect", "OVERRIDE_WITHOUT_RANK1_SUPPORT",
      "a delta override with no rank-1 delta source")
def _(r):
    d = ry(r, f"{P}/BM-001-2/normative.yaml")
    d["overrides"][0].pop("rank1_support", None)
    wy(r, f"{P}/BM-001-2/normative.yaml", d)


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
        if x["fixture_id"] == "ADM-BM-001-B":
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


# ---------------------------------------------------------------- 3G (GATE-2 contact / assembly)
@case("blanket_clearance_predicate", "defect", "BLANKET_CLEARANCE_PREDICATE",
      "GATE-2: the retired clearance>0 form returning to a motion predicate")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-002-008":
            i["verification_predicate"] = "clearance(swept_volume(platform), housing_solid) > 0 at every pose."
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("blanket_collision_free_assembly", "defect", "BLANKET_CLEARANCE_PREDICATE",
      "GATE-2: the retired collision-free-path assembly form returning")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-C4-011":
            i["verification_predicate"] = ("for each discretely-installed part: exists(installation_path) "
                                           "collision-free against already-placed parts.")
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("no_undeclared_overlap_form_is_fine", "control", "BLANKET_CLEARANCE_PREDICATE",
      "RELAXED HEURISTIC CONTROL: the baseline predicates mention overlap and must stay silent")
def _(r):
    pass  # baseline


@case("interference_fit_without_assumptions", "defect", "DECLARED_FIT_WITHOUT_ASSUMPTIONS",
      "GATE-2: a declared interference fit with no material or process assumption")
def _(r):
    d = ry(r, f"{P}/BM-001/realizations.yaml")
    for a in d["admissible_realizations"]:
        if a["id"] == "ADM-BM-001-G":
            for reg in a["interaction_regions"]:
                if reg["kind"] == "declared_interference_fit":
                    reg.pop("material_assumption", None)
                    reg.pop("process_assumption", None)
    wy(r, f"{P}/BM-001/realizations.yaml", d)


@case("compliant_interaction_without_deformation", "defect", "DECLARED_FIT_WITHOUT_ASSUMPTIONS",
      "GATE-2: a declared compliant insertion with no represented deformation")
def _(r):
    d = ry(r, f"{P}/BM-001/realizations.yaml")
    for a in d["admissible_realizations"]:
        if a["id"] == "ADM-BM-001-F":
            for reg in a["interaction_regions"]:
                if reg["kind"] == "declared_compliant_interaction":
                    reg.pop("deflection_represented", None)
    wy(r, f"{P}/BM-001/realizations.yaml", d)


@case("interaction_region_unclassified", "defect", "INTERACTION_REGION_UNCLASSIFIED",
      "GATE-2: an interaction region with no admissible kind")
def _(r):
    d = ry(r, f"{P}/BM-001/realizations.yaml")
    for a in d["admissible_realizations"]:
        if a["id"] == "ADM-BM-001-E":
            a["interaction_regions"][0]["kind"] = "touching"
    wy(r, f"{P}/BM-001/realizations.yaml", d)


@case("declared_contact_stays_admissible", "control", "NECESSITY_COUNTEREXAMPLE",
      "RELAXED HEURISTIC CONTROL: ADM-BM-001-E has three declared contacts and must remain "
      "admissible - it failed three times under the retired blanket-clearance predicate")
def _(r):
    pass  # baseline


@case("ablation_only_verification_minimum", "defect", "ABLATION_ONLY_VERIFICATION_MINIMUM",
      "GATE-2/HSD-006: a verification minimum accepting only an ablated control")
def _(r):
    d = ry(r, f"{M}/bounded-two-state-closure/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-HS-007":
            i["verification_predicate"] = ("for each criterion mapped to the bound: a configuration is "
                                           "identified in which the criterion fails when the bound is removed.")
    wy(r, f"{M}/bounded-two-state-closure/normative.yaml", d)


@case("direct_causal_evidence_is_admissible", "control", "ABLATION_ONLY_VERIFICATION_MINIMUM",
      "RELAXED HEURISTIC CONTROL: the baseline minima mention removal as ALTERNATIVE B and "
      "must stay silent because alternative A is offered")
def _(r):
    pass  # baseline


# ---------------------------------------------------------------- 3F (cross-file drift)
@case("stale_pack_status_normative", "defect", "STALE_PACK_STATUS",
      "GATE-1: a pack still declaring a retired status")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    d["pack_status"] = "SEMANTICALLY_AUDITED"
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("stale_pack_status_readme", "defect", "STALE_PACK_STATUS",
      "GATE-1: a README still declaring a retired status")
def _(r):
    fp = r / P / "C4-drawer" / "README.md"
    fp.write_text(fp.read_text().replace(
        "**Status: `PRE_CAD_SEMANTIC_REVIEWED`**", "**Status: STRUCTURALLY_COMPLETE**"))


@case("retired_contract_freedom_count", "defect", "RETIRED_CONTRACT_PRESENT",
      "GATE-1: the retired strict-prismatic rule returning to a stage expectation")
def _(r):
    d = ry(r, f"{M}/guided-slider/stage_expectations.yaml")
    d["stages"]["s11"]["outcome_rules"]["GS-C2_freedoms_accounted"]["pass_requires"] = \
        "each of the five non-translational freedoms is shown removed by an engagement"
    wy(r, f"{M}/guided-slider/stage_expectations.yaml", d)


@case("retired_contract_proper_subset", "defect", "RETIRED_CONTRACT_PRESENT",
      "GATE-1: the retired proper-subset corridor rule returning")
def _(r):
    d = ry(r, f"{P}/BM-002/stage_expectations.yaml")
    d["stages"]["s04"]["corridor_note"] = "the swept volume must be a proper subset of the corridor"
    wy(r, f"{P}/BM-002/stage_expectations.yaml", d)


@case("retired_contract_singular_engagement_site", "defect", "RETIRED_CONTRACT_PRESENT",
      "GATE-1: a singular engagement_site expectation where the normative permits a chain")
def _(r):
    d = ry(r, f"{M}/rotary-to-linear-engagement/stage_expectations.yaml")
    d["stages"]["s04"]["must_exist"] = ["input_axis", "engagement_site", "output_range"]
    wy(r, f"{M}/rotary-to-linear-engagement/stage_expectations.yaml", d)


@case("stage_demands_permitted_freedom", "defect", "STAGE_DEMANDS_PERMITTED_FREEDOM",
      "GATE-1: a stage demanding removal of a freedom the normative permits to remain")
def _(r):
    d = ry(r, f"{M}/guided-slider/stage_expectations.yaml")
    d["stages"]["s04"]["freedom_accounting_note"] = \
        "All six relative freedoms: one translation retained and all five non-translational freedoms removed."
    wy(r, f"{M}/guided-slider/stage_expectations.yaml", d)


@case("freedom_accounting_is_not_removal", "control", "STAGE_DEMANDS_PERMITTED_FREEDOM",
      "RELAXED HEURISTIC CONTROL: requiring all six freedoms to be ACCOUNTED FOR is correct; "
      "only requiring them REMOVED conflicts with a permitted residual freedom")
def _(r):
    pass  # baseline wording


@case("stage_unconditional_where_normative_conditional", "defect",
      "STAGE_UNCONDITIONAL_WHERE_NORMATIVE_CONDITIONAL",
      "GATE-1: an outcome rule quantifying support universally over a conditional invariant")
def _(r):
    d = ry(r, f"{P}/C4-drawer/stage_expectations.yaml")
    rule = d["stages"]["s11"]["outcome_rules"]["C4-R9_carried_loads_reacted"]
    rule["pass_requires"] = "a radial support realization for every rotating element and an axial reaction for each"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{P}/C4-drawer/stage_expectations.yaml", d)


@case("superseded_source_without_amendment_ref", "defect",
      "SUPERSEDED_SOURCE_WITHOUT_AMENDMENT_REF",
      "GATE-1: a pack whose capability was amended but which does not declare the amendment")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    d.pop("dossier_amendment", None)
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("frozen_dossier_mutated", "defect", "FROZEN_DOSSIER_MUTATED",
      "GATE-1: a 'frozen' dossier edited after an amendment recorded its hash")
def _(r):
    fp = r / "oracles" / "_dossiers" / "DOS-guided-slider.md"
    fp.write_text(fp.read_text() + "\n<!-- silent edit -->\n")


@case("ambiguity_blocking_disagreement", "defect", "AMBIGUITY_BLOCKING_DISAGREEMENT",
      "GATE-1: an ambiguity recorded blocking in one file and non-blocking in another")
def _(r):
    d = ry(r, "oracles/ORACLE_WORKFLOW_STATE.yaml")
    d["source_ambiguities"]["AMB-002-01"]["status"] = "OPEN_BLOCKING"
    wy(r, "oracles/ORACLE_WORKFLOW_STATE.yaml", d)


@case("non_blocking_ambiguity_stays_silent", "control", "AMBIGUITY_BLOCKING_DISAGREEMENT",
      "RELAXED HEURISTIC CONTROL: OPEN_NON_BLOCKING contains the substring BLOCK and must "
      "not be read as blocking")
def _(r):
    pass  # baseline


@case("human_decision_ref_unresolved", "defect", "HUMAN_DECISION_REF_UNRESOLVED",
      "GATE-3: a pack citing a decision id that is not defined")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-C4-002":
            i["human_decision_ref"] = "HSD-099"
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("human_decisions_file_missing", "defect", "HUMAN_DECISION_REF_UNRESOLVED",
      "GATE-3: the decision record deleted while amendments still cite it")
def _(r):
    (r / "oracles" / "HUMAN_SEMANTIC_DECISIONS.yaml").unlink()


@case("hsd_cited_in_prose_unresolved", "defect", "HUMAN_DECISION_REF_UNRESOLVED",
      "GATE-3: a decision id cited in prose that does not resolve")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    d["invariants"][1]["conclusion_scope"] = "Removal of the freedoms per HSD-042."
    wy(r, f"{M}/guided-slider/normative.yaml", d)


# ---------------------------------------------------------------- 3H (PCF-001..011)
@case("micro_oracle_s1_mislabelled_rank1", "defect", "PROJECT_CAPABILITY_MISLABELLED_RANK1",
      "PCF-001: a micro-oracle capability definition labelled rank-1 user source")
def _(r):
    d = ry(r, "oracles/SOURCE_FREEZE.yaml")
    for a in d["artifacts"]:
        if a["path"].endswith("DOS-guided-slider.md"):
            a["authority_type"] = "RANK_1_USER_SOURCE"
            a["source_rank"] = "rank_1_for_S1_product_extracts"
    wy(r, "oracles/SOURCE_FREEZE.yaml", d)


@case("hsd_inside_source_freeze", "defect", "CHALLENGEABLE_AUTHORITY_INSIDE_SOURCE_FREEZE",
      "PCF-002: the challengeable decision record listed as immutable source authority")
def _(r):
    d = ry(r, "oracles/SOURCE_FREEZE.yaml")
    d["artifacts"].append({"path": "HUMAN_SEMANTIC_DECISIONS.yaml", "artifact_role": "decisions",
                           "authority_type": "RANK_1_USER_SOURCE", "applicable_pack": "all",
                           "artifact_status": "ORIGINAL_AND_CURRENT", "source_rank": None,
                           "ambiguity_ids": [], "may_be_superseded_semantically": False,
                           "superseding_authority": None, "sha256": "0" * 64, "note": None})
    wy(r, "oracles/SOURCE_FREEZE.yaml", d)


@case("semantic_authority_manifest_missing", "defect", "SEMANTIC_AUTHORITY_MANIFEST_MISSING",
      "PCF-002: the layer-B manifest deleted")
def _(r):
    (r / "oracles" / "SEMANTIC_AUTHORITY.yaml").unlink()


@case("representation_tag_in_physical_requires", "defect", "REPRESENTATION_TAG_IN_PHYSICAL_DOMAIN",
      "PCF-004: interaction_regions_declared inserted into a physical requires_tags")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-001-003":
            i["requires_tags"] = list(i["requires_tags"]) + ["interaction_regions_declared"]
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("deprecated_assembly_tag_reactivated", "defect", "DEPRECATED_TAG_ACTIVE",
      "PCF-006: the retired assembly_paths_exist contract put back into a requires_tags")
def _(r):
    d = ry(r, f"{P}/BM-002/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-002-012":
            i["requires_tags"] = ["assembly_paths_exist"]
    wy(r, f"{P}/BM-002/normative.yaml", d)


@case("fixture_tag_without_individual_review", "defect", "FIXTURE_TAG_WITHOUT_INDIVIDUAL_REVIEW",
      "PCF-005: an old fixture given a physical tag its review does not assign")
def _(r):
    d = ry(r, f"{P}/BM-001-2/realizations.yaml")
    a = d["admissible_realizations"][0]
    a["tags"] = list(a["tags"]) + ["no_undeclared_volumetric_overlap"]
    wy(r, f"{P}/BM-001-2/realizations.yaml", d)


@case("statement_predicate_interaction_mismatch", "defect", "STATEMENT_PREDICATE_INTERACTION_MISMATCH",
      "PCF-007: a statement asserting no intersection beside a contact-permitting predicate")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-001-003":
            i["statement"] = ("In the open state the closure does not obstruct the declared usable "
                              "access, and the swept region does not intersect the enclosure solid.")
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("superseded_locator_without_current_authority", "defect",
      "SUPERSEDED_LOCATOR_WITHOUT_CURRENT_AUTHORITY",
      "PCF-008: a statement citing a superseded S1 with no current authority declared")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-GS-002":
            i["source_locators"] = ["DOS-guided-slider S1"]
            i.pop("current_authority", None)
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("workflow_records_old_audit_scope", "defect", "WORKFLOW_CURRENT_STATE_STALE",
      "PCF-003: the workflow state carrying a superseded reviewed_commit")
def _(r):
    d = ry(r, "oracles/ORACLE_WORKFLOW_STATE.yaml")
    d["reviewed_commit"] = "3b64aee601985ba509d2420462af624ed5616cc2"
    wy(r, "oracles/ORACLE_WORKFLOW_STATE.yaml", d)


@case("index_fixture_count_stale", "defect", "INDEX_AUDIT_COUNT_STALE",
      "PCF-003: the index stating a fixture count the snapshot contradicts")
def _(r):
    # Derive the corruption from whatever the index currently states. A
    # hard-coded pair silently becomes a no-op the moment the real count
    # changes, and a no-op mutation reports nothing and looks like a checker
    # regression. This one cannot rot: it reads the live number and writes a
    # different one, and fails loudly if it matched nothing.
    import re as _re
    fp = r / "oracles" / "ORACLE_INDEX.md"
    txt = fp.read_text()
    m = _re.search(r"(\d+) admissible \+", txt)
    assert m, "ORACLE_INDEX.md no longer states an admissible fixture count"
    wrong = int(m.group(1)) + 3
    out = txt.replace(m.group(0), "%d admissible +" % wrong, 1)
    assert out != txt, "mutation changed nothing"
    fp.write_text(out)


@case("source_freeze_revision_paradox", "defect", "SOURCE_FREEZE_REVISION_PARADOX",
      "PCF-009: the freeze declaring itself challengeable, which source bytes are not")
def _(r):
    d = ry(r, "oracles/SOURCE_FREEZE.yaml")
    d["challengeable_by_cad"] = True
    wy(r, "oracles/SOURCE_FREEZE.yaml", d)


@case("assembly_unresolved_cites_policy_only", "defect", "ASSEMBLY_SOURCE_SILENCE_LOCATOR_MISSING",
      "PCF-011: an assembly unresolved citing the policy instead of the dossier silence")
def _(r):
    d = ry(r, f"{P}/C4-drawer/normative.yaml")
    for u in d["required_unresolved"]:
        if u["id"] == "UNR-C4-008":
            u["source_locators"] = ["ORACLE_AUTHORING_POLICY 14"]
    wy(r, f"{P}/C4-drawer/normative.yaml", d)


@case("physical_predicate_requires_recording", "defect", "PHYSICAL_PREDICATE_REQUIRES_RECORDING",
      "RR-H-01: a recording obligation embedded in a physical assembly predicate - a physically coherent "
      "press fit whose assumptions are unrecorded would fail a PHYSICAL invariant")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-001-010":
            i["verification_predicate"] = ("a realizable installation process exists, and its required "
                                           "deformation, material assumption, insertion direction and "
                                           "process assumption are represented.")
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("conditional_on_a_declaration_is_not_a_recording_obligation", "control",
      "PHYSICAL_PREDICATE_REQUIRES_RECORDING",
      "CONTROL: 'where the design declares a terminal, it must be physically produced' is a SCOPE "
      "CONDITION, not a requirement to record anything, and must stay silent")
def _(r):
    pass  # baseline: NRM-BM-001-005, NRM-BM-002-009, NRM-C4-007, NRM-GS-002


# ---- controls: these must all stay silent
@case("frozen_micro_dossier_bytes_are_allowed", "control", "PROJECT_CAPABILITY_MISLABELLED_RANK1",
      "CONTROL: freezing the ORIGINAL bytes of a superseded micro-oracle dossier is correct when "
      "labelled PROJECT_CAPABILITY_ORIGINAL and marked superseded")
def _(r):
    pass  # baseline


@case("representation_prerequisite_is_not_physical_failure", "control",
      "REPRESENTATION_TAG_IN_PHYSICAL_DOMAIN",
      "CONTROL: interaction_regions_declared living in stage_expectations.evaluability_prerequisites "
      "is correct and must not be read as a physical tag")
def _(r):
    pass  # baseline


@case("retired_contract_in_historical_section_is_silent", "control", "DEPRECATED_TAG_ACTIVE",
      "CONTROL: assembly_paths_exist named in a retired_contracts block contributes nothing to "
      "evaluation and must stay silent")
def _(r):
    pass  # baseline


@case("semantic_authority_is_revisable", "control", "SOURCE_FREEZE_REVISION_PARADOX",
      "CONTROL: SEMANTIC_AUTHORITY declaring challengeable_by_cad: true is the resolution, not the "
      "paradox - only the FREEZE claiming challengeability is a defect")
def _(r):
    pass  # baseline


@case("source_bytes_remain_immutable", "control", "CHALLENGEABLE_AUTHORITY_INSIDE_SOURCE_FREEZE",
      "CONTROL: the nine frozen dossiers and two ambiguity records legitimately sit in the source "
      "freeze and must stay silent")
def _(r):
    pass  # baseline


# ---------------------------------------------------------------- 3I (FPC-001..007)
def _rule(r, pack, rid):
    d = ry(r, f"{pack}/stage_expectations.yaml")
    return d, d["stages"]["s11"]["outcome_rules"][rid]


@case("bm001_stage_assembly_requires_collision_free", "defect",
      "STAGE_ASSEMBLY_REQUIRES_COLLISION_FREE",
      "FPC-001: BM-001 assembly Stage rule requiring a collision-free insertion path")
def _(r):
    d, rule = _rule(r, f"{P}/BM-001", "REQ-007")
    rule["fail_when"] = "a part has no collision-free installation path, or the order contains a cycle"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{P}/BM-001/stage_expectations.yaml", d)


@case("bm002_stage_assembly_requires_collision_free", "defect",
      "STAGE_ASSEMBLY_REQUIRES_COLLISION_FREE",
      "FPC-001: BM-002 assembly Stage rule requiring a collision-free insertion path")
def _(r):
    d, rule = _rule(r, f"{P}/BM-002", "REQ-006")
    rule["fail_when"] = "a part has no collision-free installation path, or the order contains a cycle"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{P}/BM-002/stage_expectations.yaml", d)


@case("c4_stage_assembly_requires_collision_free", "defect",
      "STAGE_ASSEMBLY_REQUIRES_COLLISION_FREE",
      "FPC-001: C4 assembly Stage rule requiring a collision-free insertion path")
def _(r):
    d, rule = _rule(r, f"{P}/C4-drawer", "C4-R11_assembly")
    rule["fail_when"] = "a part has no collision-free installation path, or the order contains a cycle"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{P}/C4-drawer/stage_expectations.yaml", d)


@case("c4_stage_clearance_rejects_all_contact", "defect",
      "STAGE_CLEARANCE_REJECTS_INTENDED_CONTACT",
      "FPC-002: C4 clearance Stage rule rejecting every drawer/cabinet contact")
def _(r):
    d, rule = _rule(r, f"{P}/C4-drawer", "C4-R10_clearance_and_traversability")
    rule["pass_requires"] = ("the drawer shown not to intersect cabinet material at any configuration "
                             "of the travel, and the path shown traversable")
    rule["fail_when"] = "an intersection occurs at any configuration"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{P}/C4-drawer/stage_expectations.yaml", d)


@case("hs_c3_requires_single_persistent_constraint", "defect",
      "STAGE_REQUIRES_SINGLE_PERSISTENT_CONSTRAINT",
      "FPC-003: HS-C3 requiring one identical constraint throughout the motion")
def _(r):
    d, rule = _rule(r, f"{M}/bounded-two-state-closure", "HS-C3_constraint_coverage_continuous")
    rule["pass_requires"] = ("the relative constraint shown engaged at the extremes and the interior "
                             "of the motion")
    rule["fail_when"] = "the constraint lapses anywhere within the motion"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{M}/bounded-two-state-closure/stage_expectations.yaml", d)


@case("hs_c5_rejects_shared_field_bound", "defect", "STAGE_REJECTS_SHARED_BOUND_MECHANISM",
      "FPC-004: HS-C5 rejecting one field or feature contributing to both bounds")
def _(r):
    d, rule = _rule(r, f"{M}/bounded-two-state-closure", "HS-C5_bounds_independently_evaluated")
    rule["pass_requires"] = "each extreme shown determined by its own condition, evaluated at its own configuration"
    rule["fail_when"] = "one condition is credited to both extremes"
    rule.pop("must_not_fail_when", None)
    wy(r, f"{M}/bounded-two-state-closure/stage_expectations.yaml", d)


@case("nrm_hs_006_asserts_two_bounding_contacts", "defect",
      "NORMATIVE_ASSERTS_BOUNDING_CONTACT_COUNT",
      "FPC-005: NRM-HS-006 asserting exactly two bounding contacts")
def _(r):
    d = ry(r, f"{M}/bounded-two-state-closure/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-HS-006":
            i["statement"] = ("Along the motion the two bodies share no volume outside the interaction "
                              "regions the design declares, of which the bounding contacts are two.")
    wy(r, f"{M}/bounded-two-state-closure/normative.yaml", d)


@case("bm001_012_discrimination_only", "defect", "VERIFICATION_MINIMUM_DISCRIMINATION_ONLY",
      "FPC-006: NRM-BM-001-012 admitting only an ablation/control route")
def _(r):
    d = ry(r, f"{P}/BM-001/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-BM-001-012":
            i["statement"] = ("A criterion offered as evidence must be able to fail when that "
                              "determinant is removed.")
            i["verification_predicate"] = ("a configuration is identified in which the criterion fails "
                                           "when the determinant is removed.")
            i.pop("evidence_branches", None)
    wy(r, f"{P}/BM-001/normative.yaml", d)


@case("gs_007_discrimination_only", "defect", "VERIFICATION_MINIMUM_DISCRIMINATION_ONLY",
      "FPC-006: NRM-GS-007 admitting only a discriminating-failure route")
def _(r):
    d = ry(r, f"{M}/guided-slider/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-GS-007":
            i["statement"] = ("An observable offered as evidence of guidance must be able to take a "
                              "non-conforming value under the model that produces it.")
            i["verification_predicate"] = ("the model admits at least one configuration in which the "
                                           "observable violates its threshold.")
            i.pop("evidence_branches", None)
    wy(r, f"{M}/guided-slider/normative.yaml", d)


@case("hs_007_discrimination_only", "defect", "VERIFICATION_MINIMUM_DISCRIMINATION_ONLY",
      "FPC-006: NRM-HS-007 admitting only a discriminating-unbounded-case route")
def _(r):
    d = ry(r, f"{M}/bounded-two-state-closure/normative.yaml")
    for i in d["invariants"]:
        if i["id"] == "NRM-HS-007":
            i["statement"] = ("A criterion offered as evidence that a bound is present must be able to "
                              "distinguish a bounded closure from an otherwise identical unbounded one.")
            i["verification_predicate"] = ("a configuration is identified in which the criterion fails "
                                           "without the bound.")
            i.pop("evidence_branches", None)
    wy(r, f"{M}/bounded-two-state-closure/normative.yaml", d)


@case("stage_projects_discrimination_only", "defect", "STAGE_REQUIRES_DISCRIMINATION_ONLY",
      "FPC-006: a Stage rule projecting a two-branch minimum as branch B only")
def _(r):
    d, rule = _rule(r, f"{M}/bounded-two-state-closure", "HS-C7_evidence_admissibility")
    rule["pass_requires"] = ("every criterion mapped to the presence of a bound carries a configuration "
                             "in which it fails without the bound")
    wy(r, f"{M}/bounded-two-state-closure/stage_expectations.yaml", d)


# ---- FPC controls: these must all stay silent
@case("declared_snap_insertion_is_admissible", "control", "STAGE_ASSEMBLY_REQUIRES_COLLISION_FREE",
      "CONTROL: the corrected assembly rules name 'collision-free' only inside must_not_fail_when, "
      "where it is the EXEMPTION for a declared snap or press insertion")
def _(r):
    pass  # baseline


@case("intended_drawer_guide_contact_is_admissible", "control",
      "STAGE_CLEARANCE_REJECTS_INTENDED_CONTACT",
      "CONTROL: the corrected C4 clearance rule permits declared guide, bearing and stop contact")
def _(r):
    pass  # baseline


@case("constraint_hand_off_is_admissible", "control",
      "STAGE_REQUIRES_SINGLE_PERSISTENT_CONSTRAINT",
      "CONTROL: HS-C3 permits the active constraint to change along the path (ADM-HS-E)")
def _(r):
    pass  # baseline


@case("one_field_at_both_bounds_is_admissible", "control", "STAGE_REJECTS_SHARED_BOUND_MECHANISM",
      "CONTROL: HS-C5 and C4-R7 permit one feature or field to contribute to both bounds "
      "(ADM-HS-D, ADM-HS-F)")
def _(r):
    pass  # baseline


@case("direct_causal_evidence_needs_no_ablation", "control",
      "VERIFICATION_MINIMUM_DISCRIMINATION_ONLY",
      "CONTROL: all four two-branch minima state EITHER/OR, so branch A alone is admissible")
def _(r):
    pass  # baseline


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
