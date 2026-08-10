"""Two questions that used to be one act.

    CAN THIS DESIGN WORK?      candidate-local, preference-blind, no winner
    WHICH WORKING DESIGN?      comparison, preferences, advice, a human

The `gate` responsibility asked both and answered them together, which is how a
preference could reach a feasibility judgement: nothing in that shape could say
that a four-bar which works is not less feasible than a hinge which works. And
because `gate` was a responsibility with no entry in the ownership matrix, its
one authoritative output was attributed to the nearest stage - so s04, which
sizes bodies and sweeps them, owned the decision about which candidate wins.

S7-A freezes the authority. These are the properties that must hold before any
of it is built, and the preference-isolation one is checked against the REAL
ConsumerView rather than against prose, because that is the only form of the
claim that cannot be satisfied by an instruction.
"""
from __future__ import annotations

import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    selection_gate_check)
from ver3.assy_v3.state.design_state import (Contracts, ContractError,  # noqa: E402
                                             DesignState)
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.assy_v3.view.boundary import responsibility_contract          # noqa: E402

PRE_SELECTION = ("s01", "s02", "s03a", "s03b", "s04a", "s04b", "feasibility")


class _Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = responsibility_contract()
        cls.ds = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.matrix = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")

    def families(self):
        f = dict(self.ds["entity_families"])
        f.update(self.ds["assurance_families"])
        return f


# =====================================================================
# The split itself
# =====================================================================
class TestTheSplit(_Base):

    def test_the_gate_no_longer_exists_as_one_responsibility(self):
        self.assertNotIn("gate", self.resp["stages"])
        self.assertIn("feasibility", self.resp["stages"])
        self.assertIn("selection", self.resp["stages"])

    def test_feasibility_may_not_author_a_decision(self):
        outputs = self.resp["stages"]["feasibility"]["permitted_output_semantics"]
        self.assertNotIn("SelectionDecision", outputs)
        self.assertEqual(["MechanicalFeasibilityAssessment",
                          "HardRequirementCompliance", "UnresolvedDecision"],
                         outputs)

    def test_only_selection_may(self):
        declaring = [sid for sid, spec in self.resp["stages"].items()
                     if "SelectionDecision" in (spec.get("permitted_output_semantics") or [])]
        self.assertEqual(["selection"], declaring)

    def test_selection_decision_is_no_longer_s04s(self):
        """It was s04's because `gate` had no ownership entry at all, so the one
        family it authored was attributed to the nearest stage."""
        self.assertEqual("selection", self.families()["SelectionDecision"]["owned_by"])
        self.assertNotIn("SelectionDecision", self.matrix["stages"]["s04"]["owns"])
        entries = self.matrix["responsibilities"]["entries"]
        self.assertIn("SelectionDecision", entries["selection"]["owns"])

    def test_the_write_boundary_enforces_it(self):
        """Not a table a reader consults: `may_create` refuses."""
        self.assertFalse(self.c.may_create("s04", "SelectionDecision"))
        self.assertTrue(self.c.may_create("selection", "SelectionDecision"))
        self.assertFalse(self.c.may_create("selection", "MechanicalFeasibilityAssessment"))
        self.assertTrue(self.c.may_create("feasibility", "MechanicalFeasibilityAssessment"))

    def test_a_responsibility_has_a_position(self):
        """`gate` had none, which is why an ordering check could not say whether
        a consumer preceded its owner."""
        for name in ("feasibility", "selection"):
            self.assertEqual("s04",
                             self.matrix["responsibilities"]["entries"][name]["runs_after"])


# =====================================================================
# F11 - preference isolation, against the real view
# =====================================================================
class TestPreferenceIsolation(_fixtures.StateBuilder, _Base):

    def world(self):
        """A design with a standing SelectionProfile in it, and candidates."""
        s = DesignState(run_id="pref")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-1")
        self.add(s, "s01", "Scenario", "SCN-1", actors=["ACT-1"])
        self.add(s, "s02", "Candidate", "CND-A")
        self.add(s, "s02", "Candidate", "CND-B")
        self.add(s, "selection", "SelectionProfile", "SPF-1",
                 profile_version="v1", source_hash="deadbeef",
                 criteria={"part_count": {"objective": "MINIMIZE",
                                          "priority": "HIGH"}})
        return s

    def test_F11_no_pre_selection_view_can_contain_a_profile(self):
        s = self.world()
        self.assertTrue(s.family("SelectionProfile"), "the probe is not probing")
        for sid in PRE_SELECTION:
            view = cv.build_consumer_view(
                sid, s, self.c, self.resp,
                invocation=cv.InvocationContext(branch="CND-A"))
            self.assertNotIn("SelectionProfile", view.payload(),
                             "%s can see what the user prefers" % sid)

    def test_F11b_the_isolation_is_structural_not_instructed(self):
        """No pre-selection responsibility declares the role, so the derivation
        cannot select one. A stage told to ignore a preference has seen it."""
        for sid in PRE_SELECTION:
            roles = {r for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]
                     for r in pc["requires_semantics"]}
            self.assertNotIn("selection_preference", roles, sid)
        roles = {r for pc in self.resp["stages"]["selection"]["required_reasoning_premise_classes"]
                 for r in pc["requires_semantics"]}
        self.assertIn("selection_preference", roles)

    def test_F11c_feasibility_declares_the_prohibition_too(self):
        spec = self.resp["stages"]["feasibility"]
        self.assertIn("Any selection preference or SelectionProfile",
                      spec["prohibited_inputs"])
        self.assertTrue(spec["input_isolation_rule"].strip())

    def test_the_profile_role_is_carried_by_the_profile_and_nothing_else(self):
        carriers = [f for f, v in self.families().items()
                    if "selection_preference" in (v.get("semantic_roles") or [])]
        self.assertEqual(["SelectionProfile"], carriers)


# =====================================================================
# The semantics the later substeps must implement
# =====================================================================
class TestFrozenSemantics(_Base):

    def test_feasibility_is_three_state(self):
        fam = self.families()["MechanicalFeasibilityAssessment"]
        self.assertEqual(["FEASIBLE_FOR_SELECTION", "INFEASIBLE", "NOT_ESTABLISHED"],
                         fam["status"])

    def test_compliance_is_three_state_and_starts_unknown(self):
        fam = self.families()["HardRequirementCompliance"]
        self.assertEqual(["NOT_YET_EVALUABLE", "SATISFIED", "VIOLATED"], fam["status"])
        rules = " ".join(fam["rules"])
        self.assertIn("NOT_YET_EVALUABLE", rules)

    def test_missing_evidence_is_not_feasibility(self):
        rules = " ".join(self.families()["MechanicalFeasibilityAssessment"]["rules"])
        self.assertIn("MISSING EVIDENCE IS NOT FEASIBILITY", rules)
        self.assertIn("CANDIDATE-LOCAL", rules)

    def test_a_preference_can_never_make_a_candidate_ineligible(self):
        rules = " ".join(self.families()["SelectionProfile"]["rules"])
        self.assertIn("never a constraint", rules.lower())

    def test_a_metric_with_no_source_says_so(self):
        fam = self.families()["CandidateComparison"]
        self.assertEqual(["AVAILABLE", "NOT_AVAILABLE"], fam["availability"])
        self.assertIn("NO SILENT SURROGATE", " ".join(fam["rules"]))

    def test_an_advisory_may_not_author_authority(self):
        rules = " ".join(self.families()["SelectionAdvisory"]["rules"])
        for family in ("MechanicalFeasibilityAssessment", "HardRequirementCompliance",
                       "SelectionDecision"):
            self.assertIn(family, rules)
        self.assertEqual(["SUPPORTED_BY_STATE", "PLAUSIBLE_NOT_ESTABLISHED", "SPECULATIVE"],
                         self.families()["SelectionConcern"]["evidence_status"])

    def test_the_decision_separates_premises_from_considered(self):
        fam = self.families()["SelectionDecision"]
        self.assertIn("considered_refs", fam["optional_fields"])
        for required in ("feasibility_assessments", "hard_requirement_results",
                         "selection_profile", "comparison", "human_decision"):
            self.assertIn(required, fam["required_fields"])
        self.assertIn("PREMISES vs CONSIDERED", " ".join(fam["rules"]))

    def test_the_ui_writes_an_input_and_not_a_decision(self):
        fam = self.families()["HumanDecisionInput"]
        self.assertEqual(["SELECT", "KEEP_UNRESOLVED", "REQUEST_MORE_EVIDENCE"],
                         fam["action"])
        self.assertIn("premise_digest", fam["required_fields"])
        self.assertIn("THE UI WRITES THIS AND NOTHING ELSE", " ".join(fam["rules"]))


# =====================================================================
# No second selection authority
# =====================================================================
class TestNoCompetingAuthority(_Base):

    def test_the_old_gate_check_authors_nothing(self):
        """It validates a decision that already exists. Left in place because
        relocating checks is S-8 / U-9's, and classified so it cannot be mistaken
        for the owner of selection."""
        import inspect
        src = inspect.getsource(selection_gate_check)
        for writing in ('Op("', ".apply(", "StagePatch("):
            self.assertNotIn(writing, src, "the gate check writes state")
        s = DesignState(run_id="gate")
        self.assertEqual([], selection_gate_check(s))

    def test_no_contract_places_selection_between_the_s04_passes(self):
        s04 = _paths.contract(__import__("os").path.join("stages", "S04_CONTRACT.yaml"))
        self.assertNotIn("between s04a and s04b", s04["selection_gate"]["position"])
        # The note QUOTES the retired claim while retiring it, which is how
        # every retirement in this corpus is written - so the assertion is about
        # the current claim, not about the words appearing.
        note = self.matrix["stages"]["s04"].get("pass_note", "")
        self.assertIn("is GONE", note)
        self.assertIn("selection follows s04", note)

    def test_the_profile_contract_keeps_the_two_inputs_apart(self):
        prof = _paths.contract("USER_DESIGN_PROFILE_CONTRACT.yaml")
        self.assertIn("design_constraints", prof)
        self.assertIn("selection_preferences", prof)
        self.assertIn("INVISIBLE UNTIL SELECTION",
                      prof["visibility"]["selection_preferences"])
        self.assertIn("DETERMINISTIC", prof["ingestion"]["design_constraints"])
        # The rule that stops absence becoming compliance, stated where the
        # ingester will read it.
        self.assertIn("NOT_YET_EVALUABLE", prof["design_constraints"]["evaluation_rule"])


if __name__ == "__main__":
    unittest.main()
