"""S04b REALIZES A DEMANDED STATE CHANGE; IT DOES NOT DECIDE ONE.

The pass that places joints and computes coordinates used to author its own
transitions: it was handed two configurations, told them apart by their numbers,
and wrote a path between whichever pair it liked. Two facts were being decided by
the same pass that had no standing to decide them - WHICH state change the
mechanism owes, and WHETHER the numbers carry it out - and the second cannot
check the first when both come out of one response.

They are separated now. s03b states the demand symbolically, as a
TransitionRequirement: from which configuration, to which, and which joint has to
move in which degree of freedom. s04b names the requirement it is realizing and
supplies only the numbers. The endpoints of a Transition are read from its
requirement and never from the response, so a realization cannot quietly run
between a different pair of states than the one that was asked for.

What is checked below is that separation, generically: nothing here is about a
particular mechanism, and nothing here reads a candidate name.
"""
from __future__ import annotations

import copy
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion)
from ver3.assy_v3.state.design_state import (                          # noqa: E402
    Contracts, ContractError, DesignState)
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from .test_s02_s03b_integration import _Canned                          # noqa: E402
from .test_s5_branch_and_premise import _Chain, _s03a, _s03b            # noqa: E402


def s04a_response(bodies):
    return {
        "scale": {"basis": "RELATIVE", "absolute": None, "note": "unit"},
        "envelopes": [{"id": "ENV-%d" % i, "body": b, "half_extent": [1, 1, 1],
                       "centre": [i * 3.0, 0, 0], "maturity": "PROVISIONAL"}
                      for i, b in enumerate(bodies)],
        "region_volumes": [], "reach_results": [],
        "assembly_directions": [{"assembly_step": "ASY-A", "direction": [0, 0, -1]}],
        "elimination": {"eliminated": False, "reason": None},
    }


def s04b_response(joint="JNT-A", realizes="TRQ-A", moving=("RGP-G0A",),
                  coords=(0, 90), changed=("JNT-A",), transitions=None):
    """One placement, coordinates for both states, and one realization."""
    a, b = "CFG-C0A", "CFG-C1A"
    out = {
        "joint_placements": [{"joint": joint, "origin": [0, 0, 0]}],
        "state_coordinates": [
            {"configuration": a, "coordinates": {joint: coords[0]}},
            {"configuration": b, "coordinates": {joint: coords[1]}}],
        "transitions": [{"id": "TRN-A", "realizes_requirement": realizes,
                         "moving_groups": list(moving),
                         "changed_coordinates": list(changed)}],
        "envelope_revisions": [], "notes": "",
    }
    if transitions is not None:
        out["transitions"] = copy.deepcopy(transitions)
    return out


class _S04B(_Chain):
    """s01..s03b through the real chain, then one s04 pair on one branch.

    Every probe below hands this the same three payloads and changes one thing.
    The chain is real to the last stage: a defect that only a produced patch can
    show - a reference to a record nothing wrote - is not visible to a test that
    calls `completeness` directly.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def run_chain(self, s03a=None, s03b=None, s04b=None, apply_b=True):
        from ver3.assy_v3.stages.s02_obligation_and_candidates import (
            S02ObligationAndCandidates)
        from ver3.assy_v3.stages.s03_topology_and_mobility import (
            S03BMobilityAndAssembly, S03TopologyAndMobility)
        from .test_s5_branch_and_premise import _s02
        s = DesignState(run_id="branch")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        self.add(s, "s01", "Scenario", "SCN-IDLE", actors=["ACT-0001"])
        provider = _Canned(
            _s02(["A"]),
            s03a if s03a is not None else _s03a("A", 2, 2, None),
            s03b if s03b is not None else _s03b("A", demand=True),
            s04a_response(["BOD-G0A", "BOD-G1A"]),
            s04b if s04b is not None else s04b_response())
        s.apply(S02ObligationAndCandidates().invoke(provider, s, s.run_id).patch)
        inv = cv.InvocationContext(branch="CND-A")
        s.apply(S03TopologyAndMobility().invoke(
            provider, s, s.run_id, {"candidate": {"entity_id": "CND-A"}},
            invocation=inv).patch)
        out = S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=inv)
        self.assertIsNotNone(out.patch, out.problems)
        s.apply(out.patch)
        oa = S04AEnvelopeAndReach().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=1,
            invocation=inv)
        self.assertIsNotNone(oa.patch, oa.problems)
        s.apply(oa.patch)
        ob = S04BPlacementAndMotion().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=inv)
        if apply_b and ob.patch is not None:
            s.apply(ob.patch)
        return s, ob

    def chain(self, s04b_payload=None, **kw):
        return self.run_chain(s04b=s04b_payload, **kw)

    # -- readers -------------------------------------------------------
    def said(self, outcome):
        return " | ".join(outcome.declared_incompleteness or [])

    def transitions(self, state):
        return {t["entity_id"]: t for t in state.family("Transition")}


# =====================================================================
# THE PATH IS BACKED BY A DEMAND
# =====================================================================
class TestBacking(_S04B):

    def test_R1_an_unbacked_transition_is_not_written(self):
        """No requirement named at all. There is nothing to write endpoints
        from, so the record does not come into existence and the run says so."""
        state, ob = self.chain(s04b_payload=s04b_response(realizes=None))
        self.assertEqual({}, self.transitions(state))
        self.assertIn("realizes no requirement", self.said(ob))

    def test_R2_a_wrong_requirement_reference_is_refused(self):
        """A name that resolves to nothing this consumer was given. Guessing the
        endpoints from the response is exactly the inference being removed."""
        state, ob = self.chain(s04b_payload=s04b_response(realizes="TRQ-ELSEWHERE"))
        self.assertEqual({}, self.transitions(state))
        self.assertIn("which this consumer was not given", self.said(ob))

    def test_R3_the_endpoints_come_from_the_requirement(self):
        """The response states no endpoints and the written record has both.

        The pair is the requirement's, so a Transition can only ever run between
        the two states somebody asked to get between.
        """
        state, ob = self.chain()
        t = self.transitions(state)["TRN-A"]
        self.assertEqual("STA-CFG-C0A", t["from_state"])
        self.assertEqual("STA-CFG-C1A", t["to_state"])
        self.assertEqual("TRQ-A", t["realizes_requirement"])
        self.assertEqual([], ob.declared_incompleteness, self.said(ob))

    def test_R4_no_response_field_can_move_the_endpoints(self):
        """Endpoints named in the response are not read - not preferred, not
        merged, not consulted. The one before this change would have used them."""
        payload = s04b_response()
        payload["transitions"][0]["from_configuration"] = "CFG-C1A"
        payload["transitions"][0]["to_configuration"] = "CFG-C0A"
        state, _ = self.chain(s04b_payload=payload)
        t = self.transitions(state)["TRN-A"]
        self.assertEqual(("STA-CFG-C0A", "STA-CFG-C1A"),
                         (t["from_state"], t["to_state"]))


# =====================================================================
# EVERY DEMAND IS ANSWERED, AND ANSWERED ONCE
# =====================================================================
class TestCoverage(_S04B):

    def test_R5_a_demand_nothing_realizes_is_reported(self):
        state, ob = self.chain(s04b_payload=s04b_response(transitions=[]))
        self.assertIn("nothing realizes it", self.said(ob))

    def test_R6_a_demand_realized_twice_has_no_single_answer(self):
        payload = s04b_response()
        second = copy.deepcopy(payload["transitions"][0])
        second["id"] = "TRN-B"
        payload["transitions"].append(second)
        _, ob = self.chain(s04b_payload=payload)
        self.assertIn("is realized 2 times", self.said(ob))
        self.assertIn("TRN-A, TRN-B", self.said(ob))

    def test_R7_an_endpoint_with_no_coordinates_is_reported(self):
        payload = s04b_response()
        payload["state_coordinates"] = [payload["state_coordinates"][0]]
        _, ob = self.chain(s04b_payload=payload)
        self.assertIn("no coordinates are stated for it", self.said(ob))


# =====================================================================
# THE NUMBERS DO WHAT THE DEMAND ASKED FOR
# =====================================================================
class TestTheNumbers(_S04B):

    def test_R8_a_required_joint_that_does_not_move_is_reported(self):
        _, ob = self.chain(s04b_payload=s04b_response(coords=(30, 30)))
        self.assertIn("its coordinate is 30 at both ends", self.said(ob))

    def test_R9_a_required_joint_absent_from_changed_coordinates_is_reported(self):
        _, ob = self.chain(s04b_payload=s04b_response(changed=()))
        self.assertIn("does not list it among the coordinates it changes",
                      self.said(ob))

    def test_R10_a_changed_coordinate_that_did_not_change_is_reported(self):
        """The other direction: a coordinate claimed to change whose endpoints
        are equal. A claim about motion is checked against the numbers either
        way round, so neither a silent omission nor a silent addition passes."""
        s03a = _s03a("A", 2, 2, None)
        s03a["joints"].append(dict(s03a["joints"][0], id="JNT-A2"))
        payload = s04b_response()
        payload["joint_placements"].append({"joint": "JNT-A2", "origin": [0, 0, 0]})
        for st in payload["state_coordinates"]:
            st["coordinates"]["JNT-A2"] = 5
        payload["transitions"][0]["changed_coordinates"] = ["JNT-A", "JNT-A2"]
        _, ob = self.run_chain(s03a=s03a, s04b=payload)
        self.assertIn("its endpoints are both 5", self.said(ob))

    def test_R11_a_multi_dof_joint_cannot_evidence_one_of_its_freedoms(self):
        """One scalar per joint says a coordinate changed and cannot say WHICH
        freedom it was. Reading the required one into it manufactures evidence."""
        s03a = _s03a("A", 2, 2, None)
        s03a["joints"][0]["dof"] = ["RZ", "TZ"]
        s03a["joints"][0]["joint_type"] = "CYLINDRICAL"
        _, ob = self.run_chain(s03a=s03a)
        self.assertIn("cannot say which of them moved", self.said(ob))



# =====================================================================
# WHAT MOVES IS RELATIVE, SO EITHER SIDE COUNTS
# =====================================================================
class TestWhatMoves(_S04B):

    JOINTS = [{"id": "JNT-A", "joint_type": "REVOLUTE",
               "parent_group": "RGP-G0A", "child_group": "RGP-G1A",
               "dof": ["RZ"], "axis_direction": "+Z", "frame_ids": ["F1"]}]

    def two_group_joint(self, moving, reversed_=False):
        """The default topology's one joint, rewired to relate two groups."""
        s03a = _s03a("A", 2, 2, None)
        j = copy.deepcopy(self.JOINTS[0])
        if reversed_:
            j["parent_group"], j["child_group"] = j["child_group"], j["parent_group"]
        s03a["joints"] = [j]
        return self.run_chain(s03a=s03a, s04b=s04b_response(moving=moving))

    def test_R12_the_parent_moving_establishes_the_motion(self):
        state, ob = self.two_group_joint(("RGP-G0A",))
        self.assertNotIn("names no group of that joint", self.said(ob))
        self.assertEqual(["RGP-G0A"],
                         self.transitions(state)["TRN-A"]["path"]["moving_groups"])

    def test_R12b_and_so_does_the_child(self):
        """A joint states a RELATIVE relation. Crediting only the child would be
        reading its parent/child labels as a statement about the world."""
        state, ob = self.two_group_joint(("RGP-G1A",))
        self.assertNotIn("names no group of that joint", self.said(ob))
        self.assertEqual(["RGP-G1A"],
                         self.transitions(state)["TRN-A"]["path"]["moving_groups"])

    def test_R13_a_group_the_joint_does_not_touch_establishes_nothing(self):
        s03a = _s03a("A", 3, 2, None)
        s03a["joints"] = [copy.deepcopy(self.JOINTS[0])]
        _, ob = self.run_chain(s03a=s03a,
                               s04b=s04b_response(moving=("RGP-G2A",)))
        self.assertIn("names no group of that joint", self.said(ob))

    def test_R14_reversing_parent_and_child_changes_no_verdict(self):
        """The same numbers, the same demand, the joint described the other way
        round. Both readings have to give the same answer or the verdict is
        about the description rather than the mechanism."""
        forward = self.said(self.two_group_joint(("RGP-G1A",))[1])
        reverse = self.said(self.two_group_joint(("RGP-G1A",), reversed_=True)[1])
        self.assertEqual(forward, reverse)


# =====================================================================
# WHAT NO LONGER CREATES A DEMAND, AND WHAT A DEMAND NOW CARRIES
# =====================================================================
class TestScopeAndLifecycle(_S04B):

    def test_R15_declared_distinctness_demands_no_transition(self):
        """Two configurations declared to differ is a statement that they are
        not the same state. It is not a statement that either is reachable from
        the other, and reading it as one was the inference being removed."""
        basis = {"CFG-C0A": [{"rigid_group": "RGP-G0A", "dof": "RZ",
                              "differs_from": ["CFG-C1A"]}]}
        state, _ = self.build([("A", 2, 2)], basis=basis)   # and no demand
        self.assertTrue(any(c.get("distinguishing_basis")
                            for c in state.family("Configuration")),
                        "the probe is not probing")
        self.assertEqual([], state.family("TransitionRequirement"))
        inv = cv.InvocationContext(branch="CND-A")
        provider = _Canned(s04a_response(["BOD-G0A", "BOD-G1A"]),
                           s04b_response(transitions=[]))
        state.apply(S04AEnvelopeAndReach().invoke(
            provider, state, state.run_id, {"candidate": "CND-A"},
            attempt=1, invocation=inv).patch)
        ob = S04BPlacementAndMotion().invoke(
            provider, state, state.run_id, {"candidate": "CND-A"},
            attempt=2, invocation=inv)
        self.assertEqual([], [p for p in (ob.declared_incompleteness or [])
                              if "TRQ" in p or "realiz" in p], self.said(ob))

    def test_R16_a_requirement_from_another_branch_is_refused(self):
        """Two branches, and a realization naming the other one's demand. The
        consumer view is branch-local, so the reference resolves to nothing
        here - which is the answer, and not an accident of ordering."""
        state, _ = self.build([("A", 2, 2), ("B", 2, 2)], demand=True)
        self.assertIn("TRQ-B", {r["entity_id"]
                                for r in state.family("TransitionRequirement")},
                      "the probe is not probing")
        inv = cv.InvocationContext(branch="CND-A")
        provider = _Canned(s04a_response(["BOD-G0A", "BOD-G1A"]),
                           s04b_response(realizes="TRQ-B"))
        state.apply(S04AEnvelopeAndReach().invoke(
            provider, state, state.run_id, {"candidate": "CND-A"},
            attempt=1, invocation=inv).patch)
        ob = S04BPlacementAndMotion().invoke(
            provider, state, state.run_id, {"candidate": "CND-A"},
            attempt=2, invocation=inv)
        state.apply(ob.patch)
        self.assertEqual([], state.family("Transition"))
        self.assertIn("which this consumer was not given", self.said(ob))

    def test_R17_a_transition_stales_when_its_requirement_is_revised(self):
        """The requirement decides the endpoints and the motion owed, so the
        realization has no standing once the demand it answers has changed."""
        state, _ = self.chain()
        self.assertEqual("STANDING", state.entities["TRN-A"].get("_validity"))
        state.apply(StagePatch(
            patch_id="rev", run_id=state.run_id, stage_id="s03", stage_attempt=9,
            parent_state_hash=state.state_hash(),
            operations=[Op("SUPERSEDE", "TransitionRequirement", "TRQ-A",
                           {"required_relative_motions": [
                               {"joint": "JNT-A", "dof": "TZ"}]}, "t",
                           reason="the motion asked for changed")],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        self.assertEqual("STALE", state.entities["TRN-A"].get("_validity"))


if __name__ == "__main__":
    unittest.main()
