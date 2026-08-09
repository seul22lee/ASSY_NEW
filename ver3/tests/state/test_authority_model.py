"""The authority model itself. Mechanism-independent: no case, no product, no model.

Migration step S-1 (U-1 + U-2A + U-4 + M-5A). Frozen architecture FA-1..FA-5.

These are LEVEL 2 evidence in the sense of the audit-defect registry: they test
that the architectural mechanism which permitted the defect is gone, not that one
historical case now behaves. The LEVEL 1 exact replay is in
test_absorb_writepath_replay.py.
"""
from __future__ import annotations

import os
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.state.authority import AuthorityClass, AuthorityViolation  # noqa: E402
from ver3.assy_v3.state.design_state import ContractError, DesignState       # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                          # noqa: E402


def _patch(state, stage, ops, pid="p1"):
    return StagePatch(
        patch_id=pid, run_id=state.run_id, stage_id=stage, stage_attempt=1,
        parent_state_hash=state.state_hash(), operations=ops,
        execution_status="SUCCESS", provenance={"provider": "test"})


def _state():
    return DesignState("test-run")


def _with_scale(state):
    state.apply(_patch(state, "s04", [
        Op("CREATE", "ReferenceScale", "SCL-0001",
           {"basis": "RELATIVE", "absolute": None}, "prov:test")]))
    return state


def _with_region(state, rid="FRG-0001"):
    state.apply(_patch(state, "s03", [
        Op("CREATE", "FunctionalRegion", rid,
           {"role": "ACCESS", "owning_bodies": ["BOD-0001"]}, "prov:test")], pid="p0"))
    return state


class TestAuthorityModel(unittest.TestCase):

    # ---------------------------------------------------------------- A. CREATE
    def test_A_create_succeeds_and_records_provenance_and_authority(self):
        s = _with_scale(_state())
        rec = s.family("ReferenceScale")[0]
        assert rec["_provenance"] == "prov:test"
        assert rec["_created_by"] == "s04"
        assert rec["_authority"] == AuthorityClass.AUTHORITATIVE.value
        assert rec["_validity"] == "STANDING"


    def test_A_create_without_provenance_is_refused(self):
        s = _state()
        with self.assertRaisesRegex(ContractError, "NO_PROVENANCE"):
            s.apply(_patch(s, "s04", [
                Op("CREATE", "ReferenceScale", "SCL-0001", {"basis": "RELATIVE"}, None)]))


    # ---------------------------------------------------------------- B. EXTEND
    def test_B_extend_succeeds_for_a_declared_field_and_stage(self):
        s = _with_region(_state())
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001",
               {"volume": {"half_extent": [1, 1, 1], "centre": [0, 0, 0]}}, "prov:s04a")]))
        rec = s.family("FunctionalRegion")[0]
        assert rec["volume"]["centre"] == [0, 0, 0]
        # The extending stage is a different author from the creating stage and both
        # must stay visible.
        assert rec["_created_by"] == "s03"
        assert rec["_extensions"][0]["stage"] == "s04"
        assert rec["_extensions"][0]["provenance"] == "prov:s04a"


    # ------------------------------------------------------- C. illegal EXTEND
    def test_C_extend_of_an_undeclared_field_is_refused(self):
        s = _with_region(_state())
        with self.assertRaisesRegex(ContractError, "EXTEND_NOT_PERMITTED"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "FRG-0001", {"role": "KEEPOUT"}, "p")]))


    def test_C_extend_by_the_wrong_stage_is_refused(self):
        s = _with_region(_state())
        with self.assertRaisesRegex(ContractError, "EXTEND_WRONG_STAGE"):
            s.apply(_patch(s, "s02", [
                Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {}}, "p")]))


    def test_C_extend_over_an_existing_value_is_refused_and_names_the_remedy(self):
        s = _with_region(_state())
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {"centre": [0, 0, 0]}}, "p")]))
        with self.assertRaisesRegex(ContractError, "EXTEND_OVER_EXISTING"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "FRG-0001",
                   {"volume": {"centre": [9, 9, 9]}}, "p")], pid="p2"))


    def test_C_extend_of_an_unknown_entity_is_refused(self):
        s = _state()
        with self.assertRaisesRegex(ContractError, "EXTEND_UNKNOWN"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "FRG-9999", {"volume": {}}, "p")]))


    # ------------------------------------------------------------- D. SUPERSEDE
    def test_D_supersede_retains_the_prior_value_and_establishes_the_replacement(self):
        s = _with_region(_state())
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {"centre": [0, 0, 0]}}, "p")]))
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [1, 2, 3]}}, "prov:refine",
               reason="refined against the realized topology")], pid="p3"))
        rec = s.family("FunctionalRegion")[0]
        assert rec["volume"]["centre"] == [1, 2, 3]                       # replacement
        hist = rec["_superseded"][0]
        assert hist["prior_value"] == {"centre": [0, 0, 0]}               # FA-1: retained
        assert hist["reason"] == "refined against the realized topology"


    def test_D_supersede_without_a_reason_is_refused(self):
        s = _with_scale(_state())
        with self.assertRaisesRegex(ContractError, "NO_REASON"):
            s.apply(_patch(s, "s04", [
                Op("SUPERSEDE", "ReferenceScale", "SCL-0001", {"basis": "ABSOLUTE"}, "p")],
                pid="p2"))


    def test_D_supersede_of_a_field_with_no_prior_value_is_refused(self):
        s = _with_scale(_state())
        with self.assertRaisesRegex(ContractError, "SUPERSEDE_ABSENT"):
            s.apply(_patch(s, "s04", [
                Op("SUPERSEDE", "ReferenceScale", "SCL-0001", {"never_set": 1}, "p",
                   reason="r")], pid="p2"))


    # ------------------------------------------------------------ E. INVALIDATE
    def test_E_invalidate_keeps_the_record_and_removes_unqualified_authority(self):
        s = _with_scale(_state())
        s.apply(_patch(s, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-0001", {}, "prov:withdraw",
               reason="basis was not established")], pid="p2"))
        rec = s.family("ReferenceScale")[0]
        assert rec["_validity"] == "INVALIDATED"
        assert rec["basis"] == "RELATIVE"                                 # FA-1: not deleted
        assert rec["_invalidations"][0]["reason"] == "basis was not established"
        assert s.standing("ReferenceScale") == []


    def test_E_invalidate_without_a_reason_is_refused(self):
        s = _with_scale(_state())
        with self.assertRaisesRegex(ContractError, "NO_REASON"):
            s.apply(_patch(s, "s04", [
                Op("INVALIDATE", "ReferenceScale", "SCL-0001", {}, "p")], pid="p2"))


    # --------------------------------------------- F. premise change propagation
    def test_F_invalidating_a_premise_makes_the_dependent_lose_unqualified_authority(self):
        s = _with_region(_with_scale(_state()))
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {"centre": [0, 0, 0]}},
               "p", premise_refs=["SCL-0001"])], pid="p2"))
        assert s.family("FunctionalRegion")[0]["_validity"] == "STANDING"

        s.apply(_patch(s, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-0001", {}, "p",
               reason="the basis it declared was withdrawn")], pid="p3"))

        dep = s.family("FunctionalRegion")[0]
        assert dep["_validity"] == "STALE"                                # FA-5
        assert dep["volume"]["centre"] == [0, 0, 0]                       # value untouched
        assert dep["_stale_because"][0]["premise"] == "SCL-0001"
        assert s.standing("FunctionalRegion") == []


    def test_F_superseding_a_premise_also_propagates(self):
        s = _with_region(_with_scale(_state()))
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {"centre": [0, 0, 0]}},
               "p", premise_refs=["SCL-0001"])], pid="p2"))
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-0001", {"basis": "ABSOLUTE"}, "p",
               reason="an absolute basis became available")], pid="p3"))
        assert s.family("FunctionalRegion")[0]["_validity"] == "STALE"


    def test_F_a_premise_that_does_not_resolve_is_refused(self):
        s = _with_region(_state())
        with self.assertRaisesRegex(ContractError, "DANGLING_PREMISE"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {}}, "p",
                   premise_refs=["SCL-NOPE"])], pid="p2"))


    # ------------------------------------------------- G. uncontrolled mutation
    def test_G_direct_field_assignment_on_a_read_record_cannot_change_state(self):
        """The exact shape of the audited defect: e["field"] = value.

        A read hands back a plain copy the caller owns, so the assignment is
        ordinary and legal - and completely ineffective. What matters is not that
        it raises but that authoritative state is unreachable this way."""
        s = _with_scale(_state())
        before = s.state_hash()
        rec = s.entities["SCL-0001"]
        rec["basis"] = "ABSOLUTE"
        rec.update({"note": "injected"})
        self.assertEqual("RELATIVE", s.entities["SCL-0001"]["basis"])
        self.assertNotIn("note", s.entities["SCL-0001"])
        self.assertEqual(before, s.state_hash())


    def test_G_writing_to_the_entity_table_is_refused(self):
        s = _with_scale(_state())
        for call in (lambda: s.entities.__setitem__("X", {}),
                     lambda: s.entities.update({"X": {}}),
                     lambda: s.entities.pop("SCL-0001"),
                     lambda: s.entities.popitem()):
            with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
                call()


    def test_G_inserting_an_entity_directly_is_refused(self):
        s = _state()
        with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
            s.entities["SCL-0001"] = {"basis": "RELATIVE"}


    def test_G_replacing_a_storage_root_is_refused(self):
        s = _with_scale(_state())
        for name in ("entities", "by_family", "applied_patches"):
            with self.subTest(root=name):
                with self.assertRaisesRegex(AuthorityViolation, "PROTECTED_ROOT"):
                    setattr(s, name, {})


    def test_G_deleting_an_entity_is_refused(self):
        s = _with_scale(_state())
        with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
            del s.entities["SCL-0001"]


    def test_G_a_side_channel_attribute_on_the_state_is_refused(self):
        """The other half of the audited defect: state.s04a_reach = [...]."""
        s = _state()
        for name in ("s04a_reach", "s04a_elimination", "s04a_scale"):
            with self.assertRaisesRegex(AuthorityViolation, "SIDE_CHANNEL_WRITE"):
                setattr(s, name, ["anything"])


    # ------------------------------------------------- H. derived and ephemeral
    def test_H_a_projection_is_ephemeral_and_carries_no_mutation_semantics(self):
        """Class C is structurally distinguishable: it leaves the state entirely."""
        from ver3.assy_v3.state.projection import project_for
        s = _with_scale(_state())
        view = project_for("s04", s)
        view["ReferenceScale"][0]["basis"] = "ANYTHING"          # freely regenerable
        assert s.family("ReferenceScale")[0]["basis"] == "RELATIVE"
        assert type(view["ReferenceScale"][0]) is dict           # a plain structure


    def test_H_authority_class_is_declared_by_contract_with_a_strict_default(self):
        s = _state()
        assert s.c.authority_class("ReachResult") is AuthorityClass.AUTHORITATIVE
        # A family with no explicit declaration falls back to the strict class, so
        # nothing escapes controlled mutation by omission.
        assert s.c.authority_class("Body") is AuthorityClass.AUTHORITATIVE


    # ------------------------------------------------------- I. the S-1 families
    def test_I_the_former_side_channel_facts_have_owners_and_provenance(self):
        s = _state()
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReachResult", "RCH-0001",
               {"actor": "ACT-0001", "target": "a region", "reachable": True}, "s04a:response"),
            Op("CREATE", "EliminationRecord", "ELM-0001",
               {"eliminated": False, "reason": None}, "s04a:response"),
        ]))
        for fam in ("ReachResult", "EliminationRecord"):
            rec = s.family(fam)[0]
            assert rec["_created_by"] == "s04"
            assert rec["_provenance"] == "s04a:response"
            assert rec["_authority"] == "AUTHORITATIVE"


    def test_I_a_stage_that_does_not_own_the_family_may_not_create_it(self):
        s = _state()
        with self.assertRaisesRegex(ContractError, "OWNERSHIP"):
            s.apply(_patch(s, "s02", [
                Op("CREATE", "ReachResult", "RCH-0001",
                   {"actor": "A", "target": "T", "reachable": True}, "p")]))


    def test_I_a_missing_required_field_is_refused(self):
        s = _state()
        with self.assertRaisesRegex(ContractError, "MISSING_REQUIRED"):
            s.apply(_patch(s, "s04", [
                Op("CREATE", "ReachResult", "RCH-0001", {"actor": "ACT-0001"}, "p")]))


    # --------------------------------------------------------- J. integrity
    def test_J_provenance_and_references_survive_every_mutation(self):
        s = _with_region(_with_scale(_state()))
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001", {"volume": {"centre": [0, 0, 0]}},
               "prov:a", premise_refs=["SCL-0001"])], pid="p2"))
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001", {"volume": {"centre": [1, 1, 1]}},
               "prov:b", reason="refined")], pid="p3"))
        rec = s.family("FunctionalRegion")[0]
        assert rec["_provenance"] == "prov:test"                  # creating author
        assert rec["_extensions"][0]["provenance"] == "prov:a"    # extending author
        assert rec["_superseded"][0]["provenance"] == "prov:b"    # revising author
        assert rec["_premises"] == ["SCL-0001"]
        assert rec["owning_bodies"] == ["BOD-0001"]               # nothing lost


    def test_J_a_rejected_patch_changes_nothing(self):
        s = _with_scale(_state())
        before = s.state_hash()
        with self.assertRaises(ContractError):
            s.apply(_patch(s, "s04", [
                Op("CREATE", "ReferenceScale", "SCL-0002", {"basis": "RELATIVE"}, None)],
                pid="p2"))
        assert s.state_hash() == before


if __name__ == "__main__":
    unittest.main()
