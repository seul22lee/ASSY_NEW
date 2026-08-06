"""The contracts agree with each other.

Nine YAML files that each look reasonable in isolation can still describe
incompatible systems. This test checks the joins: does every stage that owns a
family exist, does every family a stage owns exist, does every assurance-package
item project something real, and does every forbidden collapse name a status that
is actually defined.

The joins are where the architecture lives. A stage owning a family nobody
defined is exactly the kind of gap that gets filled later by a default.
"""

import unittest

from . import _paths


class TestContractCrossReferences(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.state = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.ownership = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.patch = _paths.contract("STAGE_PATCH_CONTRACT.yaml")
        cls.status = _paths.contract("STATUS_SEMANTICS.yaml")
        cls.provenance = _paths.contract("PROVENANCE_CONTRACT.yaml")
        cls.runrec = _paths.contract("MODEL_RUN_RECORD_CONTRACT.yaml")
        cls.result = _paths.contract("BENCHMARK_RESULT_CONTRACT.yaml")
        cls.package = _paths.contract("GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml")
        cls.progression = _paths.contract("STAGE_PROGRESSION_CONTRACT.yaml")

        cls.families = dict(cls.state["entity_families"])
        cls.families.update(cls.state["assurance_families"])

    # -- stages and families -------------------------------------------------

    def test_ownership_matrix_covers_twelve_stages(self):
        self.assertEqual(_paths.STAGE_IDS, sorted(self.ownership["stages"]))

    def test_every_owned_family_is_defined(self):
        violations = []
        for stage_id, spec in self.ownership["stages"].items():
            for fam in spec.get("owns", []):
                if fam not in self.families:
                    violations.append("%s owns undefined family %r" % (stage_id, fam))
            for fam in spec.get("extends", []):
                if fam not in self.families:
                    violations.append("%s extends undefined family %r" % (stage_id, fam))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_every_family_has_an_owner(self):
        """No family may be ownerless.

        An ownerless family is one any stage may create, which defeats INV-001's
        duplicate detection: with no owner there is nothing to duplicate against.
        """
        universal = {e["family"] for e in self.ownership["universally_ownable"] if "family" in e}
        owned = set()
        for spec in self.ownership["stages"].values():
            owned.update(spec.get("owns", []))
        ownerless = sorted(set(self.families) - owned - universal)
        self.assertEqual([], ownerless, "families with no owning stage: %s" % ownerless)

    def test_family_owned_by_matches_ownership_matrix(self):
        """DESIGN_STATE_CONTRACT's `owned_by` and the matrix must not disagree."""
        violations = []
        universal = {e["family"] for e in self.ownership["universally_ownable"] if "family" in e}
        for fam, spec in self.families.items():
            declared = spec.get("owned_by")
            if declared in (None, "any"):
                continue
            owners = [declared] if isinstance(declared, str) else list(declared)
            for owner in owners:
                if owner not in self.ownership["stages"]:
                    violations.append("%s declares unknown owner %r" % (fam, owner))
                elif fam not in self.ownership["stages"][owner].get("owns", []) and fam not in universal:
                    violations.append("%s says owner %s, matrix disagrees" % (fam, owner))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_only_s01_reads_source_text(self):
        """Rebuild policy rule 5 and INV-002, checked structurally."""
        self.assertEqual("EXCLUSIVE", self.ownership["stages"]["s01"]["source_text_access"])
        for stage_id, spec in self.ownership["stages"].items():
            if stage_id != "s01":
                self.assertNotIn("source_text_access", spec,
                                 "%s must not declare source text access" % stage_id)
        source_methods = {"SOURCE_VERBATIM", "SOURCE_DERIVED"}
        for name in source_methods:
            self.assertEqual("s01", self.provenance["methods"][name]["only_available_to"])

    # -- statuses ------------------------------------------------------------

    def test_execution_statuses_are_the_required_twelve(self):
        required = {
            "SUCCESS", "PROVIDER_RATE_LIMIT", "PROVIDER_QUOTA_EXHAUSTED",
            "PROVIDER_UNAVAILABLE", "PROVIDER_TIMEOUT", "RESPONSE_TRUNCATED",
            "RESPONSE_PARSE_FAILURE", "SCHEMA_FAILURE", "CONTRACT_INCOMPLETE",
            "MODEL_CAPABILITY_FAILURE", "SAFE_REJECTION", "FALSE_ACCEPTANCE",
        }
        self.assertEqual(required, set(self.status["execution_statuses"]))

    def test_severity_order_covers_every_execution_status(self):
        self.assertEqual(
            set(self.status["execution_statuses"]),
            set(self.status["severity_order"]["order"]),
        )

    def test_every_status_declares_a_meaning(self):
        for group in ("execution_statuses", "evaluation_outcomes"):
            for name, spec in self.status[group].items():
                with self.subTest(status=name):
                    self.assertTrue(str(spec.get("meaning", "")).strip(),
                                    "%s has no meaning" % name)

    def test_forbidden_collapses_name_real_statuses(self):
        """Every collapse's `correct` alternative must exist in some vocabulary.

        A collapse pointing at a status nobody defined tells an implementer to do
        something impossible, which in practice means they will do the collapse.
        """
        known = set()
        for group in ("execution_statuses", "evaluation_outcomes", "solver_statuses",
                      "observable_statuses"):
            known.update(self.status[group])
        known.add("REPRESENTATION_INCOMPLETE")  # DESIGN_STATE_CONTRACT Interface rule
        violations = []
        for entry in self.status["forbidden_collapses"]:
            correct = entry["correct"]
            if not any(tok in known for tok in correct.replace(",", " ").split()):
                violations.append("%s: correct=%r names no known status" % (entry["id"], correct))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_patch_contract_uses_the_status_vocabulary(self):
        text = str(self.patch["patch_envelope"]["field_rules"]["execution_status"])
        self.assertIn("STATUS_SEMANTICS", text)

    # -- assurance package ---------------------------------------------------

    def test_package_is_never_called_an_oracle_in_production(self):
        self.assertEqual("GENERATED_DESIGN_ASSURANCE_PACKAGE", self.package["artifact_name"])
        self.assertEqual("RUNTIME_ASSURANCE_RECORD", self.package["artifact_alias"])
        self.assertIn("Oracle", self.package["forbidden_names_in_production_code"])

    def test_three_way_distinction_is_complete(self):
        dist = self.package["three_way_distinction"]
        for key in ("hidden_benchmark_oracle", "runtime_generated_assurance_package",
                    "positive_executable_reference"):
            self.assertIn(key, dist)
        self.assertEqual("YES", dist["hidden_benchmark_oracle"]["defines_success"])
        self.assertEqual("NO", dist["runtime_generated_assurance_package"]["defines_success"])
        self.assertEqual("NO", dist["positive_executable_reference"]["defines_success"])

    def test_package_items_project_defined_families(self):
        violations = []
        for item in self.package["required_contents"]:
            for fam in item["projects"]:
                if fam in ("all", "ModelRunRecord", "ToolRunRecord"):
                    continue
                if fam not in self.families:
                    violations.append("%s projects undefined family %r" % (item["id"], fam))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_package_items_name_real_stages(self):
        violations = []
        for item in self.package["required_contents"]:
            stage = item["first_stage"]
            if stage != "any" and stage not in self.ownership["stages"]:
                violations.append("%s first_stage=%r is not a stage" % (item["id"], stage))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_every_package_item_states_what_it_prevents(self):
        """An item with no failure behind it is decoration and will be dropped."""
        for item in self.package["required_contents"]:
            with self.subTest(item=item["id"]):
                self.assertTrue(str(item.get("prevents", "")).strip())

    def test_every_stage_contributes_to_the_package(self):
        contributions = self.ownership["assurance_contributions"]
        self.assertEqual(_paths.STAGE_IDS, sorted(contributions))
        for stage_id, spec in contributions.items():
            with self.subTest(stage=stage_id):
                self.assertTrue(spec.get("adds"), "%s adds nothing" % stage_id)
                self.assertTrue(spec.get("package_sections"))

    def test_contributed_sections_are_declared_package_sections(self):
        declared = {item["section"] for item in self.package["required_contents"]}
        # Section names used by stages that group several items under one heading.
        declared.update({
            "scope_and_source", "freedoms", "open_questions", "obligations",
            "candidate_space", "rejected_alternatives", "architecture",
            "interaction_inventory", "mobility", "operation", "witnesses",
            "realization_map", "parameters", "construction_program",
            "unsupported_formulations", "as_built_geometry", "verification_plan",
            "negative_controls", "evidence_scope", "evidence", "execution_record",
            "coverage", "contradictions", "evaluation", "excluded_claims",
            "obligation_closure", "failure_attribution", "revision_history",
            "human_review_queue",
        })
        violations = []
        for stage_id, spec in self.ownership["assurance_contributions"].items():
            for section in spec["package_sections"]:
                if section not in declared:
                    violations.append("%s contributes to unknown section %r" % (stage_id, section))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    # -- progression and results --------------------------------------------

    def test_progression_has_eight_steps_in_order(self):
        steps = self.progression["progression_steps"]
        self.assertEqual(list(range(1, 9)), [s["step"] for s in steps])

    def test_freeze_requires_all_three_benchmarks(self):
        precondition = str(steps_by_name(self.progression, "freeze_stage_contract")["precondition"])
        self.assertIn("ALL THREE", precondition)

    def test_implementation_order_is_the_twelve_stages(self):
        self.assertEqual(_paths.STAGE_IDS, self.progression["implementation_order"]["order"])

    def test_pipeline_does_not_score_itself(self):
        must_not = self.result["duties"]["pipeline_must_not_produce"]
        joined = " ".join(must_not).lower()
        for phrase in ("score", "verdict", "oracle"):
            self.assertIn(phrase, joined)

    def test_provider_requirements_are_identified(self):
        ids = [r["id"] for r in self.runrec["provider_requirements"]]
        self.assertEqual(sorted(set(ids)), sorted(ids), "duplicate provider requirement ids")
        self.assertGreaterEqual(len(ids), 11)


def steps_by_name(progression, name):
    for step in progression["progression_steps"]:
        if step["name"] == name:
            return step
    raise AssertionError("no progression step named %r" % name)


if __name__ == "__main__":
    unittest.main()
