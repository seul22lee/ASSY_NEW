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

from . import _paths

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
        self.assertEqual(16, len(auditor.CHECKS))


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

    def test_an_invariant_that_rejects_an_admissible_family(self):
        """Overfitting, caught mechanically: permissiveness has a floor."""
        doc = self._load("realizations")
        doc["admissible_realizations"][2]["satisfies_tags"] = [
            t for t in doc["admissible_realizations"][2]["satisfies_tags"]
            if t != "deployed_state_maintained"]
        self._save("realizations", doc)
        self.assertDetected("ADMISSIBLE_FAMILY_REJECTED")

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


if __name__ == "__main__":
    unittest.main()
