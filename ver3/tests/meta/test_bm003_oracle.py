"""The BM-003 held-out Oracle, and the mutations its auditor must catch.

A clean auditor report proves nothing on its own: an auditor that checks nothing
also reports clean. Each mutation below breaks the pack in one specific way and
asserts the auditor notices — which is what makes the clean run on the unmutated
pack mean something.

Every mutation runs against a temporary COPY. The frozen Oracle is never written
to, and a test that mutated it in place would be doing the one thing the freeze
exists to prevent.
"""

import os
import shutil
import sys
import tempfile
import unittest

import yaml

try:                                    # package import: python -m unittest ...
    from . import _paths
except ImportError:                     # direct execution: python <path>/test_bm003_oracle.py
    # Without this the file cannot be run directly at all, so its __main__ block
    # was never exercised and the mutations below never ran that way.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))
    from ver3.tests.meta import _paths

TOOLS = os.path.join(_paths.VER3, "oracle_tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import audit_bm003_oracle as auditor  # noqa: E402

PACK = os.path.join(_paths.VER3, "oracles", "held_out", "BM-003")
SOURCE = _paths.request_path("BM-003")


class OracleMutationCase(unittest.TestCase):
    """Copy the pack, break one thing, confirm the auditor sees it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bm003_oracle_mutation_")
        self.pack = os.path.join(self.tmp, "BM-003")
        shutil.copytree(PACK, self.pack)
        self.source = os.path.join(self.tmp, "request.txt")
        shutil.copy(SOURCE, self.source)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _load(self, key):
        with open(os.path.join(self.pack, auditor.FILES[key]), encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def _save(self, key, doc):
        with open(os.path.join(self.pack, auditor.FILES[key]), "w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, sort_keys=False, default_flow_style=False, width=120)

    def _audit(self):
        return auditor.audit(self.pack, self.source)

    def _codes(self):
        return {f.code for f in self._audit()}

    def assertDetected(self, code=None):
        findings = self._audit()
        blocking = [f for f in findings if f.severity == "BLOCKING"]
        self.assertTrue(blocking, "mutation went undetected")
        if code:
            self.assertIn(code, {f.code for f in blocking},
                          "detected, but not as %s: %s" % (code, [f.code for f in blocking]))


class TestUnmutatedPackPasses(OracleMutationCase):
    """The control. Without it every mutation test could pass on a broken auditor."""

    def test_the_frozen_pack_passes_its_own_auditor(self):
        findings = auditor.audit(PACK, SOURCE)
        blocking = [f.as_dict() for f in findings if f.severity == "BLOCKING"]
        self.assertEqual([], blocking)

    def test_the_copy_also_passes(self):
        self.assertEqual([], [f for f in self._audit() if f.severity == "BLOCKING"])

    def test_the_auditor_runs_every_declared_check(self):
        self.assertEqual(35, len(auditor.CHECKS))


class TestRequiredMutationsDetected(OracleMutationCase):

    def test_mandatory_latch_requirement(self):
        """A mechanism named as REQUIRED contradicts FRE-BM-003-001."""
        doc = self._load("normative")
        doc["invariants"][8]["statement"] = (
            "The deployed configuration is held by a latch that engages when the leg reaches position.")
        self._save("normative", doc)
        self.assertDetected("FREEDOM_CONTRADICTED")

    def test_fixed_body_count(self):
        """A body count contradicts FRE-BM-003-003, and is also a number."""
        doc = self._load("normative")
        doc["invariants"][0]["statement"] = (
            "The product consists of exactly 4 bodies: a body and three legs.")
        self._save("normative", doc)
        self.assertDetected("UNSTATED_NUMERIC_THRESHOLD")

    def test_numeric_impact_threshold(self):
        """The 'knocked it' failure: a disturbance the source never stated."""
        doc = self._load("normative")
        doc["invariants"][10]["verification_predicate"] = (
            "The deployed state survives a lateral impulse of 5 joules without folding.")
        self._save("normative", doc)
        self.assertDetected("UNSTATED_NUMERIC_THRESHOLD")

    def test_structural_capacity_pass_from_rigid_body_evidence(self):
        """Capacity must stay UNSUPPORTED however the evidence is arranged."""
        doc = self._load("stages")
        doc["stages"]["s11"]["outcome_rules"]["structural_capacity"] = {
            "pass_requires": "rigid-body reaction forces below the joint rating",
            "if_capability_absent": "PASS",
            "otherwise": "PASS",
        }
        self._save("stages", doc)
        self.assertDetected("CAPACITY_NOT_UNSUPPORTED")

    def test_removal_of_the_deliberate_release(self):
        """Without it the benchmark loses its distinguishing requirement."""
        doc = self._load("normative")
        doc["invariants"] = [i for i in doc["invariants"] if i["id"] != "NRM-BM-003-011"]
        for inv in doc["invariants"]:
            for field in ("statement", "verification_predicate"):
                if "deliberate" in str(inv.get(field, "")):
                    inv[field] = str(inv[field]).replace("deliberate", "ordinary")
        self._save("normative", doc)
        self.assertDetected("DELIBERATE_RELEASE_MISSING")

    def test_endpoint_only_operation_evidence(self):
        """Dropping interior sampling is how an unbuildable motion passes."""
        doc = self._load("expectations")
        doc["mobility_expectations"] = [
            e for e in doc["mobility_expectations"] if e["id"] != "MOB-BM-003-006"]
        self._save("expectations", doc)
        self.assertDetected("DANGLING_PREDICATE_REF")

    def test_deletion_of_a_source_clause(self):
        """A dropped clause is coverage the Oracle silently lost."""
        doc = self._load("ledger")
        doc["clauses"] = [c for c in doc["clauses"] if c["id"] != "SRC-BM003-011"]
        self._save("ledger", doc)
        self.assertDetected("SOURCE_CLAUSE_UNMAPPED")

    def test_dangling_reference(self):
        doc = self._load("negatives")
        doc["negative_cases"][0]["expected_detection_predicate"] = (
            "Retention active at every sampled interior configuration (NRM-BM-003-999).")
        self._save("negatives", doc)
        self.assertDetected("DANGLING_REFERENCE")

    def test_freedom_invariant_contradiction(self):
        """An invariant asserting a value a freedom declares free."""
        doc = self._load("normative")
        doc["invariants"][1]["verification_predicate"] = (
            "Each leg is connected to the body by a revolute joint about a fixed axis.")
        self._save("normative", doc)
        self.assertDetected("FREEDOM_CONTRADICTED")


class TestFurtherMutationsDetected(OracleMutationCase):
    """Beyond the required set: the joins most likely to rot quietly."""

    def test_source_hash_drift(self):
        with open(self.source, "a", encoding="utf-8") as fh:
            fh.write("And it should be blue.\n")
        self.assertDetected("SOURCE_HASH_MISMATCH")

    def test_preferred_realization_family(self):
        doc = self._load("realizations")
        doc["admissible_realizations"][0]["not_preferred"] = False
        self._save("realizations", doc)
        self.assertDetected("FAMILY_NOT_MARKED_UNPREFERRED")

    def test_too_few_admissible_families(self):
        doc = self._load("realizations")
        doc["admissible_realizations"] = doc["admissible_realizations"][:3]
        self._save("realizations", doc)
        self.assertDetected("TOO_FEW_ADMISSIBLE_FAMILIES")

    def test_a_family_that_does_not_declare_full_coverage(self):
        """A bookkeeping defect, and named as one.

        This used to report ADMISSIBLE_FAMILY_REJECTED - a physical verdict the
        data cannot support, since the tags and the requirements share an author.
        """
        doc = self._load("realizations")
        doc["admissible_realizations"][2]["declared_coverage_tags"] = [
            t for t in doc["admissible_realizations"][2]["declared_coverage_tags"]
            if t != "deployed_state_maintained"]
        self._save("realizations", doc)
        self.assertDetected("DECLARED_COVERAGE_INCOMPLETE")

    def test_invariant_without_source_backing(self):
        doc = self._load("normative")
        doc["invariants"][3]["source_clauses"] = []
        self._save("normative", doc)
        self.assertDetected("INVARIANT_WITHOUT_SOURCE")

    def test_invariant_without_a_verification_predicate(self):
        doc = self._load("normative")
        del doc["invariants"][5]["verification_predicate"]
        self._save("normative", doc)
        self.assertDetected("NO_VERIFICATION_PREDICATE")

    def test_evidence_class_missing_structural_artifacts(self):
        doc = self._load("evidence")
        del doc["evidence_classes"][4]["structural_artifacts"]
        self._save("evidence", doc)
        self.assertDetected("NO_STRUCTURAL_ARTIFACTS")

    def test_prohibited_inference_dropped_from_the_simulation_scope(self):
        """Removing an out_of_scope entry is how overreach becomes permitted."""
        doc = self._load("evidence")
        sim = next(c for c in doc["evidence_classes"]
                   if c["name"] == "continuous_kinematic_simulation")
        sim["out_of_scope"] = [o for o in sim["out_of_scope"] if "capacity" not in o.lower()]
        self._save("evidence", doc)
        self.assertDetected("PROHIBITED_INFERENCE_NOT_SCOPED")

    def test_negative_case_without_a_failure_mechanism(self):
        doc = self._load("negatives")
        del doc["negative_cases"][2]["why_a_model_might_do_this"]
        self._save("negatives", doc)
        self.assertDetected("NEGATIVE_CASE_INCOMPLETE")

    def test_stage_coverage_gap(self):
        doc = self._load("stages")
        del doc["stages"]["s07"]
        self._save("stages", doc)
        self.assertDetected("STAGE_COVERAGE_INCOMPLETE")

    def test_oracle_marked_visible_to_production(self):
        doc = self._load("governance")
        doc["production_visibility"]["visible_to_production"] = True
        self._save("governance", doc)
        self.assertDetected("ORACLE_VISIBLE_TO_PRODUCTION")

    def test_quantitative_ambiguity_blocking_a_structural_predicate(self):
        """A missing number does not undefine a geometric predicate."""
        doc = self._load("ambiguities")
        doc["ambiguities"][0]["block_scopes"] = ["blocks_structural_predicate"]
        self._save("ambiguities", doc)
        self.assertDetected("QUANTITATIVE_BLOCKS_STRUCTURAL")

    def test_duplicate_id(self):
        doc = self._load("normative")
        doc["invariants"][4]["id"] = doc["invariants"][3]["id"]
        self._save("normative", doc)
        self.assertDetected("DUPLICATE_ID")

    def test_clause_that_nothing_cites(self):
        doc = self._load("normative")
        for inv in doc["invariants"]:
            inv["source_clauses"] = [c for c in inv.get("source_clauses", [])
                                     if c != "SRC-BM003-005"]
        self._save("normative", doc)
        codes = self._codes()
        self.assertTrue({"CLAUSE_NEVER_USED", "INVARIANT_WITHOUT_SOURCE"} & codes,
                        "orphaned clause not detected: %s" % codes)


class TestOracleContentRequirements(unittest.TestCase):
    """The pack must actually contain what the Oracle was commissioned to contain."""

    @classmethod
    def setUpClass(cls):
        cls.docs = auditor.load(PACK)

    def test_source_hash_binds_to_the_frozen_source(self):
        import hashlib
        with open(SOURCE, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(actual, self.docs["ledger"]["source_sha256"])

    def test_every_source_clause_is_mapped(self):
        self.assertEqual(15, len(self.docs["ledger"]["clauses"]))

    def test_invariants_cover_the_required_subjects(self):
        """Searched over statement AND predicate.

        The footprint requirement is deliberately worded geometrically - the
        contacts are "neither coincident nor collinear" - rather than by using
        the word "footprint", because the geometric form is what a checker can
        evaluate. Matching on the concept keeps the test from rewarding a
        vaguer statement that happens to contain the right noun.
        """
        text = " ".join(
            "%s %s" % (i["statement"], i.get("verification_predicate", ""))
            for i in self.docs["normative"]["invariants"]).lower()
        for subject in ("three", "attached", "deployment", "collinear",
                        "deliberate", "assembly", "retention", "connected"):
            with self.subTest(subject=subject):
                self.assertIn(subject, text)

    def test_at_least_four_materially_different_families(self):
        fams = self.docs["realizations"]["admissible_realizations"]
        self.assertGreaterEqual(len(fams), 4)
        self.assertEqual(len(fams), len({f["family"] for f in fams}))
        for f in fams:
            with self.subTest(family=f["id"]):
                self.assertTrue(f["state_maintenance_principle"].strip())
                self.assertTrue(f["release_principle"].strip())
                self.assertTrue(f["materially_different_because"].strip())
                self.assertTrue(f["not_preferred"])

    def test_no_family_carries_geometry_or_dimensions(self):
        """Describing a family deeply enough to be a design would defeat the purpose."""
        import re
        for f in self.docs["realizations"]["admissible_realizations"]:
            blob = yaml.safe_dump(f)
            with self.subTest(family=f["id"]):
                self.assertEqual([], re.findall(r"\b\d+\s*(?:mm|cm|deg|degrees)\b", blob))

    def test_at_least_fifteen_negative_cases(self):
        self.assertGreaterEqual(len(self.docs["negatives"]["negative_cases"]), 15)

    def test_all_twelve_stages_have_expectations(self):
        self.assertEqual(["s%02d" % n for n in range(1, 13)],
                         sorted(self.docs["stages"]["stages"]))

    def test_required_ambiguities_are_preserved(self):
        questions = " ".join(a["question"] for a in self.docs["ambiguities"]["ambiguities"]).lower()
        for topic in ("compact", "object", "footprint", "effort", "knocked",
                      "material", "clearance", "manufacturing", "usable"):
            with self.subTest(topic=topic):
                self.assertIn(topic, questions)

    def test_freedoms_cover_the_required_decisions(self):
        decisions = " ".join(f["decision"] for f in self.docs["freedoms"]["freedoms"]).lower()
        for topic in ("locking", "joint type", "body count", "coordination",
                      "sequence", "retention", "hub", "material", "dimension"):
            with self.subTest(topic=topic):
                self.assertIn(topic, decisions)

    def test_governance_records_isolation_and_freeze(self):
        g = self.docs["governance"]
        self.assertEqual("FROZEN", g["authority"]["authority_status"])
        self.assertFalse(g["production_visibility"]["visible_to_production"])
        self.assertTrue(g["files_explicitly_not_read"])
        self.assertTrue(g["authoring"]["source_hash_verified_before_authoring"])

    def test_governance_discloses_prior_context_rather_than_claiming_perfect_isolation(self):
        """An isolation claim that omits the known contamination risk would be false."""
        g = self.docs["governance"]
        self.assertIn("prior_context_disclosure", g)
        self.assertTrue(g["prior_context_disclosure"]["residual_risk"].strip())

    def test_no_positive_reference_exists_for_bm003(self):
        cad = os.path.join(_paths.VER3, "cad_validation", "BM-003")
        self.assertFalse(os.path.exists(cad))




# ===========================================================================
# Semantic mutations, added at the semantic review.
#
# The structural mutations above prove the auditor notices a broken FILE. These
# prove it notices a broken ACCEPTANCE MODEL - an Oracle that parses perfectly,
# resolves every reference, and rejects designs it claims to admit.
#
# Each asserts a SPECIFIC finding code. Asserting merely "something failed" would
# let a mutation pass because it happened to break a reference, which is the
# failure mode these tests are most exposed to.
# ===========================================================================

class TestSemanticMutations(OracleMutationCase):

    def assertDetectedBy(self, code):
        blocking = [f for f in self._audit() if f.severity == "BLOCKING"]
        self.assertTrue(blocking, "semantic mutation went undetected")
        codes = {f.code for f in blocking}
        self.assertIn(code, codes,
                      "detected, but not as %s - it may have tripped an unrelated "
                      "structural check instead: %s" % (code, sorted(codes)))

    def test_over_centre_family_with_hard_dof_lock_only_invariant(self):
        """The original defect: persistence demanding kinematic absence."""
        doc = self._load("normative")
        inv = next(i for i in doc["invariants"] if i["id"] == "NRM-BM-003-009")
        inv["statement"] = ("The deployed configuration persists: the folding motion is "
                            "unavailable while the product is in the deployed state.")
        inv["verification_predicate"] = ("In the deployed configuration, the folding "
                                         "degree of freedom of each leg is shown blocked.")
        inv.pop("explicitly_does_not_require", None)
        self._save("normative", doc)
        self.assertDetectedBy("PERSISTENCE_REQUIRES_DOF_ABSENCE")

    def test_gravity_seated_family_with_all_folding_paths_forbidden(self):
        doc = self._load("normative")
        for c in doc["state_maintenance_classes"]:
            c["folding_path_may_exist"] = False
        self._save("normative", doc)
        self.assertDetectedBy("NON_BLOCK_CLASS_FORBIDS_FOLDING_PATH")

    def test_friction_family_accepted_on_zero_friction_evidence(self):
        """A route that cannot observe the mechanism the claim rests on."""
        doc = self._load("realizations")
        fam = next(f for f in doc["admissible_realizations"]
                   if f["state_maintenance_class"] == "SMC-CONTACT_OR_COMPLIANT_RETENTION")
        fam["required_evidence_route"] = "continuous_kinematic_simulation"
        fam["evidence_route_available_now"] = True
        fam["persistence_claim_status"] = "ESTABLISHABLE"
        self._save("realizations", doc)
        self.assertDetectedBy("EVIDENCE_ROUTE_INCOMPATIBLE_WITH_CLASS")

    def test_monolithic_compliant_blocked_by_two_body_interface_rule(self):
        doc = self._load("normative")
        vm = next(i for i in doc["invariants"] if i["id"] == "NRM-BM-003-016")
        vm["verification_predicate"] = ("For each declared relationship, both participating "
                                        "bodies expose the feature that realizes it.")
        vm.pop("realization_classes", None)
        self._save("normative", doc)
        self.assertDetectedBy("BILATERAL_INTERFACE_RULE")

    def test_assembly_endpoint_freedom_removed_from_the_graph(self):
        doc = self._load("configurations")
        t = next(x for x in doc["transitions"] if x["id"] == "TRN-BM-003-ASSEMBLE")
        t.pop("to_any_of")
        t["to"] = "CFG-BM-003-STORED"
        self._save("configurations", doc)
        self.assertDetectedBy("ASSEMBLY_ENDPOINT_FREEDOM_NOT_IN_GRAPH")

    def test_persistent_released_configuration_made_mandatory(self):
        doc = self._load("configurations")
        rel = next(c for c in doc["configurations"] if c["id"] == "CFG-BM-003-RELEASED")
        rel["representation_status"] = "MANDATORY"
        self._save("configurations", doc)
        self.assertDetectedBy("RELEASED_CONFIGURATION_MANDATORY")

    def test_exactly_one_changed_relationship_restriction_reintroduced(self):
        doc = self._load("configurations")
        rel = next(c for c in doc["configurations"] if c["id"] == "CFG-BM-003-RELEASED")
        rel["active_retention"] = ["The state-maintaining relationship is disengaged - and ONLY that one."]
        self._save("configurations", doc)
        self.assertDetectedBy("EXACTLY_ONE_CHANGE_RESTRICTION")

    def test_compactness_invariant_removed_while_its_negative_case_remains(self):
        doc = self._load("normative")
        doc["invariants"] = [i for i in doc["invariants"] if i["id"] != "NRM-BM-003-018"]
        self._save("normative", doc)
        self.assertDetectedBy("COMPACTNESS_WITHOUT_NORMATIVE_ANCHOR")

    def test_clause_ledger_reciprocity_broken(self):
        doc = self._load("ledger")
        doc["clauses"][0]["supports_invariants"] = ["NRM-BM-003-001"]
        self._save("ledger", doc)
        self.assertDetectedBy("CLAUSE_MAPPING_NOT_RECIPROCAL")

    def test_unresolved_item_disappears_at_s07(self):
        doc = self._load("stages")
        doc["stages"]["s07"]["must_preserve_unresolved"] = [
            a for a in doc["stages"]["s07"]["must_preserve_unresolved"]
            if a != "AMB-BM-003-005"]
        self._save("stages", doc)
        self.assertDetectedBy("UNRESOLVED_ITEM_DROPPED_AT_STAGE")

    def test_s05_forbidden_from_embodying_the_selected_candidate(self):
        doc = self._load("stages")
        doc["stages"]["s05"]["must_not_decide"].append("Which mechanism family is correct.")
        self._save("stages", doc)
        self.assertDetectedBy("S05_FORBIDDEN_TO_EMBODY")

    def test_descriptor_claims_independence_governance_denies(self):
        """Cross-file: the descriptor is outside the pack and still must agree."""
        import shutil
        desc_dir = os.path.join(self.tmp, "benchmarks", "BM-003")
        os.makedirs(desc_dir)
        real = os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml")
        shutil.copy(real, os.path.join(desc_dir, "descriptor.yaml"))
        d = _paths.load_yaml(os.path.join(desc_dir, "descriptor.yaml"))
        d["oracle"]["authored_independently"] = True
        with open(os.path.join(desc_dir, "descriptor.yaml"), "w") as fh:
            yaml.safe_dump(d, fh, sort_keys=False)
        findings = []
        auditor.check_descriptor_matches_governance(
            auditor.load(self.pack), findings,
            descriptor_path=os.path.join(desc_dir, "descriptor.yaml"))
        self.assertIn("DESCRIPTOR_OVERCLAIMS_INDEPENDENCE", {f.code for f in findings})

    def test_family_admissible_on_tags_alone_with_no_evidence_route(self):
        """Tags are self-assigned; without a route they prove only self-consistency."""
        doc = self._load("realizations")
        fam = doc["admissible_realizations"][0]
        fam.pop("required_evidence_route")
        self._save("realizations", doc)
        self.assertDetectedBy("FAMILY_WITHOUT_EVIDENCE_ROUTE")

    def test_unavailable_route_family_claims_established_persistence(self):
        doc = self._load("realizations")
        fam = next(f for f in doc["admissible_realizations"]
                   if f["evidence_route_available_now"] is False)
        fam["persistence_claim_status"] = "ESTABLISHABLE"
        self._save("realizations", doc)
        self.assertDetectedBy("PERSISTENCE_CLAIMED_WITHOUT_AN_AVAILABLE_ROUTE")

    def test_compliant_retention_passed_from_rigid_geometry_alone(self):
        """The compatibility rule is what stops rigid geometry standing in."""
        doc = self._load("evidence")
        doc.pop("class_evidence_compatibility_rule", None)
        for c in doc["evidence_classes"]:
            if c["id"] == "EVC-BM-003-CAD":
                c["establishes_class"] = "SMC-CONTACT_OR_COMPLIANT_RETENTION"
        self._save("evidence", doc)
        doc2 = self._load("realizations")
        fam = next(f for f in doc2["admissible_realizations"]
                   if f["state_maintenance_class"] == "SMC-CONTACT_OR_COMPLIANT_RETENTION")
        fam["required_evidence_route"] = "metric_cad_geometry"
        fam["evidence_route_available_now"] = True
        fam["persistence_claim_status"] = "ESTABLISHABLE"
        self._save("realizations", doc2)
        # CAD now claims to establish the compliant class, so the ROUTE check is
        # satisfied. The defect must still surface, as the missing rule that
        # would otherwise stop rigid geometry standing in for compliance.
        self.assertDetectedBy("NO_CLASS_EVIDENCE_COMPATIBILITY_RULE")


class TestSemanticChecksExistAndAreHonest(unittest.TestCase):

    def test_the_auditor_declares_what_it_cannot_check(self):
        """A condition that cannot be checked must be named, not assumed validated."""
        self.assertTrue(auditor.UNCHECKABLE_REQUIRING_HUMAN_REVIEW)
        for item in auditor.UNCHECKABLE_REQUIRING_HUMAN_REVIEW:
            self.assertTrue(item.strip())

    def test_the_auditor_is_named_for_what_it_does(self):
        self.assertIn("structural and declared-semantic", auditor.__doc__)
        self.assertNotIn("proves physical", auditor.__doc__)

    def test_semantic_checks_were_added(self):
        names = {fn.__name__ for fn in auditor.CHECKS}
        for required in ("check_clause_reciprocity", "check_family_class_and_route",
                         "check_folding_path_not_universally_forbidden",
                         "check_compliant_realization_not_excluded",
                         "check_assembly_endpoint_freedom",
                         "check_release_representation_freedom",
                         "check_unresolved_preservation_is_cumulative",
                         "check_s05_may_embody_selected_candidate",
                         "check_governance_independence_claims"):
            with self.subTest(check=required):
                self.assertIn(required, names)

    def test_at_least_four_materially_distinct_principles_remain_admissible(self):
        docs = auditor.load(PACK)
        fams = docs["realizations"]["admissible_realizations"]
        self.assertGreaterEqual(len(fams), 4)
        principles = {f["state_maintenance_class"] for f in fams}
        self.assertGreaterEqual(len(principles), 3,
                                "families must differ in PRINCIPLE, not only in shape")

    def test_families_whose_route_is_unavailable_remain_admissible(self):
        """Admissibility must not depend on the current toolset. Claims may."""
        docs = auditor.load(PACK)
        unverifiable = [f for f in docs["realizations"]["admissible_realizations"]
                        if f["evidence_route_available_now"] is False]
        self.assertTrue(unverifiable, "expected some family to outrun the toolset")
        for f in unverifiable:
            with self.subTest(family=f["id"]):
                self.assertEqual("NOT_VERIFIED", f["persistence_claim_status"])
                self.assertIn("ADMISSIBLE", f["admissible_despite_unavailable_route"])


class TestPropagationMutations(OracleMutationCase):
    """Mutations for the propagation review (P-01..P-09).

    Each reintroduces a stale statement from the pre-correction model in a place
    the previous auditor did not look. They exist because the last correction
    fixed each defect where a check happened to inspect, and a passing auditor
    is only meaningful if it looks everywhere the claim holds.
    """

    def assertDetectedBy(self, code):
        blocking = [f for f in self._audit() if f.severity == "BLOCKING"]
        self.assertTrue(blocking, "propagation mutation went undetected")
        codes = {f.code for f in blocking}
        self.assertIn(code, codes,
                      "detected, but not as %s - it may have tripped an unrelated "
                      "parse or reference error: %s" % (code, sorted(codes)))

    # -- Phase 2: mandatory persistent RELEASED ---------------------------
    def test_mandatory_persistent_released_configuration(self):
        doc = self._load("configurations")
        rel = next(c for c in doc["configurations"] if c["id"] == "CFG-BM-003-RELEASED")
        rel["representation_status"] = "MANDATORY"
        self._save("configurations", doc)
        self.assertDetectedBy("RELEASED_CONFIGURATION_MANDATORY")

    def test_literal_released_sequence_reintroduced(self):
        doc = self._load("normative")
        inv = next(i for i in doc["invariants"] if i["id"] == "NRM-BM-003-012")
        inv["verification_predicate"] = ("A continuous, sampled path exists from DEPLOYED "
                                         "through RELEASED and FOLDING to STORED.")
        inv.pop("no_literal_sequence_required", None)
        self._save("normative", doc)
        self.assertDetectedBy("MANDATORY_RELEASED_SEQUENCE")

    def test_fold_reachable_only_through_a_released_pose(self):
        """The graph-level form: folding routed through an optional node."""
        doc = self._load("configurations")
        fold = next(t for t in doc["transitions"] if t["id"] == "TRN-BM-003-FOLD")
        fold.pop("from_any_of")
        fold["from"] = "CFG-BM-003-RELEASED"
        self._save("configurations", doc)
        self.assertDetectedBy("FOLD_UNREACHABLE_WITHOUT_RELEASED_POSE")

    def test_released_assumed_to_be_a_state_in_an_expectation(self):
        doc = self._load("expectations")
        mob = next(e for e in doc["mobility_expectations"] if e["id"] == "MOB-BM-003-001")
        mob["detail"] = ("In STORED, each leg's unfolding motion is available. In RELEASED, "
                         "each leg's folding motion is available.")
        self._save("expectations", doc)
        self.assertDetectedBy("RELEASED_ASSUMED_AS_A_STATE")

    # -- Phase 3: hard-lock-only ------------------------------------------
    def test_hard_lock_only_rule_in_a_transition(self):
        doc = self._load("configurations")
        t = next(x for x in doc["transitions"] if x["id"] == "TRN-BM-003-DEPLOY")
        t["requires"] = ["Arrival at a state where folding is blocked (NRM-BM-003-009)."]
        self._save("configurations", doc)
        self.assertDetectedBy("HARD_LOCK_ONLY_RULE")

    def test_hard_lock_only_rule_in_a_freedom(self):
        """The sharpest form: the freedom that frees the principle constraining it."""
        doc = self._load("freedoms")
        fre = next(f for f in doc["freedoms"] if f["id"] == "FRE-BM-003-001")
        fre["oracle_constrains_only"] = "That folding is unavailable in DEPLOYED."
        self._save("freedoms", doc)
        self.assertDetectedBy("HARD_LOCK_ONLY_RULE")

    def test_over_centre_family_not_required_to_lack_a_folding_path(self):
        """Declaring a folding path must not itself be a defect."""
        doc = self._load("realizations")
        fam = next(f for f in doc["admissible_realizations"]
                   if f["state_maintenance_class"] == "SMC-STABLE_EQUILIBRIUM_OR_ENERGY_BARRIER")
        self.assertTrue(fam["folding_path_exists_in_deployed"])
        self.assertEqual([], [f for f in self._audit() if f.severity == "BLOCKING"],
                         "an over-centre family with a folding path must pass unmutated")

    def test_gravity_seated_family_forced_to_have_no_folding_path(self):
        doc = self._load("normative")
        for c in doc["state_maintenance_classes"]:
            if c["id"] == "SMC-STABLE_EQUILIBRIUM_OR_ENERGY_BARRIER":
                c["folding_path_may_exist"] = False
        self._save("normative", doc)
        self.assertDetectedBy("NON_BLOCK_CLASS_FORBIDS_FOLDING_PATH")

    # -- Phase 4: monolithic compliant ------------------------------------
    def test_stale_bilateral_wording_in_an_invariant_statement(self):
        """The statement, not the predicate - where the last fix did not reach."""
        doc = self._load("normative")
        inv = next(i for i in doc["invariants"] if i["id"] == "NRM-BM-003-016")
        inv["statement"] = ("Every declared joint and every declared retention relationship "
                            "is realized by identifiable geometry on each participating body.")
        self._save("normative", doc)
        self.assertDetectedBy("STALE_BILATERAL_INTERFACE_WORDING")

    def test_stale_bilateral_wording_in_an_assembly_expectation(self):
        doc = self._load("expectations")
        asm = next(e for e in doc["assembly_expectations"] if e["id"] == "ASM-BM-003-004")
        asm["detail"] = ("Each relationship is established at an identified assembly step, "
                         "and is realized by geometry on both participating bodies.")
        self._save("expectations", doc)
        self.assertDetectedBy("STALE_BILATERAL_INTERFACE_WORDING")

    def test_stale_bilateral_wording_in_a_freedom(self):
        doc = self._load("freedoms")
        fre = next(f for f in doc["freedoms"] if f["id"] == "FRE-BM-003-002")
        fre["oracle_constrains_only"] = "That each joint is realized by geometry on both bodies."
        self._save("freedoms", doc)
        self.assertDetectedBy("STALE_BILATERAL_INTERFACE_WORDING")

    # -- Phase 5: coverage tags are not evidence --------------------------
    def test_adding_coverage_tags_does_not_make_a_family_physically_accepted(self):
        """Tags gate bookkeeping. The evidence route gates acceptance."""
        doc = self._load("realizations")
        fam = next(f for f in doc["admissible_realizations"]
                   if f["evidence_route_available_now"] is False)
        fam["declared_coverage_tags"] = list(doc["declared_coverage_tag_vocabulary"])
        fam["persistence_claim_status"] = "ESTABLISHABLE"
        self._save("realizations", doc)
        self.assertDetectedBy("PERSISTENCE_CLAIMED_WITHOUT_AN_AVAILABLE_ROUTE")

    def test_coverage_vocabulary_is_not_named_as_physical_proof(self):
        doc = self._load("realizations")
        self.assertIn("declared_coverage_tag_vocabulary", doc)
        self.assertNotIn("physical_tag_vocabulary", doc)
        for fam in doc["admissible_realizations"]:
            self.assertIn("declared_coverage_tags", fam)
            self.assertNotIn("satisfies_tags", fam)

    # -- Phase 6: contact evidence ----------------------------------------
    def test_contact_dependence_denied(self):
        doc = self._load("evidence")
        contact = next(c for c in doc["evidence_classes"] if c["id"] == "EVC-BM-003-CONTACT")
        contact["consequence_of_absence"] = (
            "Every contact-dependent property is NOT_VERIFIED for BM-003. "
            "No invariant in this Oracle depends on one, which is deliberate.")
        self._save("evidence", doc)
        self.assertDetectedBy("CONTACT_DEPENDENCE_DENIED")

    def test_compliant_retention_passing_on_rigid_geometry(self):
        """A rigid route offered for a class that rigid geometry cannot observe."""
        doc = self._load("realizations")
        fam = next(f for f in doc["admissible_realizations"]
                   if f["state_maintenance_class"] == "SMC-CONTACT_OR_COMPLIANT_RETENTION")
        fam["required_evidence_route"] = "metric_cad_geometry"
        fam["evidence_route_available_now"] = True
        fam["persistence_claim_status"] = "ESTABLISHABLE"
        self._save("realizations", doc)
        self.assertDetectedBy("EVIDENCE_ROUTE_INCOMPATIBLE_WITH_CLASS")


class TestDirectExecutionIsWired(unittest.TestCase):
    """The file must run both ways, and cover everything either way."""

    def test_main_block_is_the_last_thing_in_the_file(self):
        """Placed mid-file it silently runs only the classes defined above it.

        Matched at line start: this test's own body mentions the literal, so a
        plain substring count would find its own text and never the block.
        """
        import re
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            text = fh.read()
        blocks = list(re.finditer(r"^if __name__ == .__main__.:", text, re.M))
        self.assertEqual(1, len(blocks), "expected exactly one entry-point block")
        after = text[blocks[0].start():]
        self.assertNotIn("\nclass ", after, "a test class is defined after the main block")

    def test_readiness_overclaim_is_detected(self):
        """A descriptor claiming nothing is outstanding must fail."""
        import shutil, tempfile
        tmp = tempfile.mkdtemp(prefix="bm003_readiness_")
        try:
            dp = os.path.join(tmp, "descriptor.yaml")
            shutil.copy(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"), dp)
            d = _paths.load_yaml(dp)
            d["oracle_status_notice"]["blocks"] = ["Nothing further from BM-003's side."]
            with open(dp, "w") as fh:
                yaml.safe_dump(d, fh, sort_keys=False)
            findings = []
            auditor.check_descriptor_readiness_matches(auditor.load(PACK), findings,
                                                       descriptor_path=dp)
            self.assertIn("READINESS_OVERCLAIMED", {f.code for f in findings})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_five_readiness_dimensions_are_separate(self):
        gov = auditor.load(PACK)["governance"]["readiness_dimensions"]
        self.assertEqual("SATISFIED", gov["structural_held_out_oracle_readiness"])
        self.assertEqual("COMPLETE", gov["semantic_self_review"])
        self.assertEqual("PENDING", gov["independent_human_semantic_approval"])
        self.assertEqual("PENDING_BEFORE_S03_S04_FREEZE",
                         gov["positive_executable_permissiveness_validation"])
        self.assertEqual("ENFORCED", gov["production_generation_isolation"])

    def test_the_module_imports_under_both_names(self):
        self.assertTrue(hasattr(_paths, "request_path"))
        self.assertTrue(hasattr(auditor, "CHECKS"))


if __name__ == "__main__":
    unittest.main()
