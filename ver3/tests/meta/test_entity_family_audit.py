"""Every DesignState family has a consumer-based justification.

The audit's value is that it is COMPLETE and stays complete. A family added later
without an audit entry is a family nobody asked "who consumes this?" of, and that
question is the only thing standing between a typed state and a pile of fields.

These tests check the audit against the contracts rather than against itself, so
the two cannot drift apart silently.
"""

import unittest

from . import _paths

VALID_STATUSES = {"CORE", "PROVISIONAL", "MERGE_CANDIDATE", "UNSUPPORTED"}


class TestEntityFamilyAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.audit = _paths.contract("ENTITY_FAMILY_AUDIT.yaml")
        cls.state = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.ownership = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.package = _paths.contract("GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml")
        cls.families = dict(cls.state["entity_families"])
        cls.families.update(cls.state["assurance_families"])
        cls.entries = cls.audit["families"]

    def test_audit_covers_every_family_and_nothing_else(self):
        self.assertEqual(set(self.families), set(self.entries))

    def test_audit_count_matches_reality(self):
        self.assertEqual(len(self.families), self.audit["audit_scope"]["families_audited"])

    def test_no_family_was_added_or_deleted(self):
        scope = self.audit["audit_scope"]
        self.assertEqual(0, scope["families_added"])
        self.assertEqual(0, scope["families_deleted"])

    def test_every_entry_records_the_six_required_facts(self):
        required = {"owning_stage", "first_downstream_consumer",
                    "unique_responsibility", "duplicates",
                    "required_for_assurance_package", "status"}
        for name, entry in self.entries.items():
            with self.subTest(family=name):
                self.assertEqual(set(), required - set(entry))

    def test_every_status_is_from_the_vocabulary(self):
        for name, entry in self.entries.items():
            with self.subTest(family=name):
                self.assertIn(entry["status"], VALID_STATUSES)

    def test_summary_counts_match_the_entries(self):
        actual = {}
        for entry in self.entries.values():
            actual[entry["status"]] = actual.get(entry["status"], 0) + 1
        summary = {k: v for k, v in self.audit["summary"].items() if k in VALID_STATUSES}
        for status in VALID_STATUSES:
            with self.subTest(status=status):
                self.assertEqual(actual.get(status, 0), summary.get(status, 0))

    def test_summary_totals_to_the_family_count(self):
        total = sum(v for k, v in self.audit["summary"].items() if k in VALID_STATUSES)
        self.assertEqual(len(self.families), total)

    def test_owning_stage_agrees_with_the_ownership_matrix(self):
        for name, entry in self.entries.items():
            with self.subTest(family=name):
                declared = self.families[name].get("owned_by")
                self.assertEqual(declared, entry["owning_stage"])

    def test_first_downstream_consumer_is_a_real_stage(self):
        for name, entry in self.entries.items():
            with self.subTest(family=name):
                self.assertIn(entry["first_downstream_consumer"], self.ownership["stages"])

    def test_consumer_is_never_earlier_than_the_owner(self):
        """A family cannot be consumed before it exists.

        Catches the mistake of naming a plausible-sounding consumer that in fact
        runs first, which would make the justification fictional.
        """
        problems = []
        for name, entry in self.entries.items():
            owner = entry["owning_stage"]
            owners = [owner] if isinstance(owner, str) else list(owner)
            if owners == ["any"]:
                continue
            earliest_owner = min(owners)
            if entry["first_downstream_consumer"] < earliest_owner:
                problems.append((name, owners, entry["first_downstream_consumer"]))
        self.assertEqual([], problems, "consumer precedes owner: %s" % problems)

    def test_package_requirement_matches_the_package_contract(self):
        """`required_for_assurance_package` must be true iff a PKG item projects it."""
        projected = set()
        for item in self.package["required_contents"]:
            projected.update(item["projects"])
        problems = []
        for name, entry in self.entries.items():
            claimed = bool(entry["required_for_assurance_package"])
            actually = name in projected
            if claimed != actually:
                problems.append((name, claimed, actually))
        self.assertEqual([], problems, "audit disagrees with the package contract: %s" % problems)

    def test_listed_package_items_exist(self):
        known = {item["id"] for item in self.package["required_contents"]}
        for name, entry in self.entries.items():
            for pkg in entry.get("package_items", []):
                with self.subTest(family=name, item=pkg):
                    self.assertIn(pkg, known)

    def test_duplicates_field_names_a_real_family_or_none(self):
        for name, entry in self.entries.items():
            dup = entry["duplicates"]
            if dup in (None, "none"):
                continue
            with self.subTest(family=name):
                self.assertIn(dup, self.families)
                self.assertNotEqual(dup, name)

    def test_merge_candidates_carry_a_recommendation_and_a_deadline(self):
        """A merge candidate with no recommendation is an observation, not a finding."""
        for name, entry in self.entries.items():
            if entry["status"] != "MERGE_CANDIDATE":
                continue
            with self.subTest(family=name):
                self.assertTrue(entry.get("recommendation", "").strip())
                self.assertTrue(entry.get("decision_required_before", "").strip())
                self.assertNotIn(entry["duplicates"], (None, "none"))

    def test_provisional_families_carry_an_open_question_and_a_deadline(self):
        for name, entry in self.entries.items():
            if entry["status"] != "PROVISIONAL":
                continue
            with self.subTest(family=name):
                self.assertTrue(entry.get("open_question", "").strip())
                self.assertTrue(entry.get("decision_required_before", "").strip())

    def test_duplicate_claims_are_symmetric_or_explained(self):
        """If A duplicates B, B's entry must acknowledge the overlap.

        A one-sided duplication claim usually means only one of the two families
        was actually examined.
        """
        problems = []
        for name, entry in self.entries.items():
            dup = entry["duplicates"]
            if dup in (None, "none"):
                continue
            other = self.entries[dup]
            if other["duplicates"] != name and not other.get("overlap_note", "").strip():
                problems.append((name, dup))
        self.assertEqual([], problems, "one-sided duplication claims: %s" % problems)

    def test_overlap_groups_reference_real_families(self):
        for group in self.audit["overlap_analysis"]:
            for fam in group["group"]:
                with self.subTest(group=group["id"], family=fam):
                    self.assertIn(fam, self.families)

    def test_every_overlap_group_reaches_an_action(self):
        for group in self.audit["overlap_analysis"]:
            with self.subTest(group=group["id"]):
                self.assertTrue(group["finding"].strip())
                self.assertTrue(group["action"].strip())

    def test_the_flagged_overlap_areas_were_all_examined(self):
        """The areas singled out for attention must each appear in a group."""
        examined = set()
        for group in self.audit["overlap_analysis"]:
            examined.update(group["group"])
        for fam in ("Joint", "Interface", "Constraint", "Witness", "EvidenceItem"):
            with self.subTest(family=fam):
                self.assertIn(fam, examined)

    def test_retention_and_assembly_gaps_are_recorded(self):
        """Retention and assembly relations have no family; that must be stated."""
        concerns = " ".join(g["concern"].lower() for g in self.audit["expressiveness_gaps"])
        self.assertIn("retention", concerns)
        self.assertIn("assembly", concerns)

    def test_gaps_do_not_silently_add_families(self):
        for gap in self.audit["expressiveness_gaps"]:
            with self.subTest(gap=gap["id"]):
                self.assertIn("NO NEW FAMILY REQUIRED", gap["proposed_resolution"])

    def test_audit_freezes_nothing(self):
        self.assertTrue(self.audit["audit_scope"]["no_stage_contract_frozen_by_this_audit"])
        frozen = [n for n in _paths.CONTRACT_FILES if _paths.contract(n).get("status") == "frozen"]
        self.assertEqual([], frozen)


if __name__ == "__main__":
    unittest.main()
