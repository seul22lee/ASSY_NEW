"""S-6 / U-7: one spatial producer, one refinement lifecycle.

Before this step S04 was not a producer. The stages emitted envelopes, states and
transitions; a runner then read the raw response again and wrote the reference
scale, the reach results, the elimination record, the region volumes, the
insertion directions and the joint origins. Two authorities for one stage's
output, and a caller that did not know about the second got a DesignState missing
half of s04's conclusions with nothing saying so.

Three more things followed from the same shape. Motion evidence was declared from
a module constant before any sweep ran, and the sweep then read its density back
out of the declaration - the claim deciding the computation. A missing joint axis
became +Z at four separate call sites, so a mechanism the topology never gave an
axis produced a swept hull and the hull produced a clearance verdict. And S04B
could not be invoked at all: its premises resolved against a COMMITTED_BRANCH
that cannot exist until the S-7 gate, so the ConsumerView was UPSTREAM_INSUFFICIENCY
on every call.

Synthetic mechanisms throughout. No benchmark, no product noun, no state name.
"""
from __future__ import annotations

import json
import math
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion, axis_index, sweep_hull)
from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.tools import run_window2                                      # noqa: E402
from .test_s02_s03b_integration import _Canned                          # noqa: E402
from .test_s5_branch_and_premise import _Chain                          # noqa: E402


def state_fields(case, family):
    state, _ = case.spatial()
    return [{k: v for k, v in e.items() if not k.startswith("_")}
            for e in state.family(family)]


def s04a_response(bodies, sep=1.5, region=None, step=None, actor=None):
    """An arrangement for however many bodies a case has. No product nouns."""
    return {
        "scale": {"basis": "RELATIVE", "absolute": None, "note": "unit"},
        "envelopes": [
            {"id": "ENV-%d%s" % (i, bodies[i][-1]), "body": bodies[i],
             "half_extent": [1, 1, 1], "centre": [i * sep, 0, 0],
             "maturity": "PROVISIONAL"} for i in range(len(bodies))],
        "region_volumes": ([{"functional_region": region,
                             "half_extent": [1, 1, 1], "centre": [0, 0, 9]}]
                           if region else []),
        "reach_results": ([{"actor": actor, "target": bodies[0], "reachable": True,
                            "approach_side": "+Z", "why": "open"}] if actor else []),
        "assembly_directions": ([{"assembly_step": step, "direction": [0, 0, -1]}]
                                if step else []),
        "elimination": {"eliminated": False, "reason": None},
    }


def s04b_response(joint, configs, group, coords=(0, 90), changed=None,
                  revisions=None):
    a, b = configs[0], configs[1]
    return {
        "joint_placements": [{"joint": joint, "origin": [0, 0, 0]}],
        "state_coordinates": [
            {"configuration": a, "coordinates": {joint: coords[0]}},
            {"configuration": b, "coordinates": {joint: coords[1]}}],
        "transitions": [{"id": "TRN-%s" % joint.split("-")[-1], "from_configuration": a,
                         "to_configuration": b, "moving_groups": [group],
                         "changed_coordinates": (
                             [joint] if changed is None else changed)}],
        "envelope_revisions": list(revisions or []),
        "notes": "",
    }


class _S04Chain(_Chain):
    """s01..s03 through the real chain, then s04 on a named branch."""

    def spatial(self, shapes=(("A", 2, 2),), s04a=None, s04b=None,
                basis=None, apply_b=True):
        # The basis is s03's to author - it is a mobility statement, not a
        # geometry one - so it arrives through the topology response rather than
        # being written onto the configuration afterwards.
        state, outs = self.build(list(shapes), basis=basis)
        results = {}
        for sfx, _g, _c in shapes:
            inv = cv.InvocationContext(branch="CND-%s" % sfx)
            bodies = ["BOD-G0%s" % sfx, "BOD-G1%s" % sfx][: _g]
            pa = s04a if s04a is not None else s04a_response(
                bodies, step="ASY-%s" % sfx, actor="ACT-0001")
            pb = s04b if s04b is not None else s04b_response(
                "JNT-%s" % sfx, ["CFG-C0%s" % sfx, "CFG-C1%s" % sfx],
                "RGP-G0%s" % sfx)
            provider = _Canned(pa, pb)
            oa = S04AEnvelopeAndReach().invoke(
                provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
                attempt=1, invocation=inv)
            self.assertIsNotNone(oa.patch, oa.problems)
            state.apply(oa.patch)
            ob = None
            if apply_b:
                ob = S04BPlacementAndMotion().invoke(
                    provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
                    attempt=2, invocation=inv)
                self.assertIsNotNone(ob.patch, ob.problems)
                state.apply(ob.patch)
            results[sfx] = (oa, ob, inv)
        return state, results


# =====================================================================
# G1 - one write path
# =====================================================================
class TestCanonicalOwnership(_S04Chain):

    def test_G1_direct_invoke_equals_the_runner_state(self):
        """The runner adds nothing. It used to add three entities and two
        extensions that only it knew about."""
        direct, res = self.spatial()
        runner, _ = self.build([("A", 2, 2)])
        inv = cv.InvocationContext(branch="CND-A")
        provider = _Canned(s04a_response(["BOD-G0A", "BOD-G1A"], step="ASY-A",
                                         actor="ACT-0001"),
                           s04b_response("JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A"))
        rec = run_window2.run_s04("SYN", runner, provider, 1, invocation=inv)
        self.assertEqual("SUCCESS", rec["s04a_status"], rec["failures"])
        self.assertEqual("SUCCESS", rec["s04b_status"], rec["failures"])

        def canonical(s):
            return {eid: json.dumps({k: v for k, v in s.entities[eid].items()
                                     if not k.startswith("_")}, sort_keys=True)
                    for eid in s.entities}
        self.assertEqual(canonical(direct), canonical(runner))

    def test_G11_no_canonical_fact_was_lost_with_the_runner_writer(self):
        """Every family and field the retired `_commit_s04` used to author is
        authored by a stage, in the stage's own patch."""
        state, res = self.spatial()
        for family in ("ReferenceScale", "ReachResult", "EliminationRecord",
                       "Envelope", "State", "Transition", "SweptVolume"):
            self.assertTrue(state.family(family), "%s vanished" % family)
        self.assertIn("insertion_direction", state.entities["ASY-A"])
        self.assertEqual([0, 0, 0], state.entities["JNT-A"]["frame_origin"])
        oa, ob, _ = res["A"]
        produced = {op.entity_type for op in oa.patch.operations} | {
            op.entity_type for op in ob.patch.operations}
        for family in ("ReferenceScale", "ReachResult", "EliminationRecord",
                       "Envelope", "State", "Transition", "SweptVolume", "Joint",
                       "AssemblyStep"):
            self.assertIn(family, produced, "%s is not in any stage patch" % family)
        self.assertNotIn("_commit_s04", dir(run_window2))

    def test_G2_two_candidates_do_not_leak_spatially(self):
        state, res = self.spatial((("A", 2, 2), ("B", 1, 3)))
        for sfx in ("A", "B"):
            other = "B" if sfx == "A" else "A"
            for e in state.family("Envelope"):
                if e["body"].endswith(sfx):
                    self.assertNotIn(other, e["body"][-1])
            oa, ob, _ = res[sfx]
            blob = json.dumps([op.fields for op in ob.patch.operations])
            self.assertNotIn("-G0%s" % other, blob)
            self.assertNotIn("CFG-C0%s" % other, blob)


# =====================================================================
# G3 - refinement is a real commitment relation
# =====================================================================
class TestCommitmentAndRefinement(_S04Chain):

    def test_every_s04a_spatial_value_carries_a_commitment_class(self):
        state, _ = self.spatial()
        classes = Contracts().families["Envelope"]["commitment_class"]
        for e in state.family("Envelope"):
            self.assertIn(e.get("commitment_class"), classes, e["entity_id"])

    def test_G3_superseding_an_arrangement_stales_what_it_computed(self):
        """SUPERSEDES the blanket version of this test.

        It used to require the State and the Transition to stale too, because
        every s04b output carried every envelope in the view. They do not depend
        on any extent: a joint angle is not computed from a body's box, and
        saying it was made an unrelated resize look like it invalidated the
        kinematics. What an extent change reaches is the OCCUPANCY that was swept
        from it - and that is the evidence, so that is what must lose authority.
        """
        state, res = self.spatial()
        for v in state.family("SweptVolume"):
            self.assertEqual("STANDING", v.get("_validity"))
        self.assertIn("ENV-0A", state.entities["SWV-TRN-A-RGP-G0A"]["_premises"])
        self.assertNotIn("ENV-0A", state.entities["STA-CFG-C0A"]["_premises"])
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-0A",
                              {"extent": {"half_extent": [2, 2, 2],
                                          "centre": [0, 0, 0]}}, "test",
                              reason="the body does not fit at the size committed"))
        self.assertTrue(state.family("SweptVolume"))
        for v in state.family("SweptVolume"):
            self.assertEqual("STALE", v.get("_validity"),
                             "an occupancy survived the extent it was swept from")
        self.assertEqual("STANDING", state.entities["STA-CFG-C0A"].get("_validity"),
                         "a joint angle was staled by a body being resized")

    def test_an_unrelated_supersession_does_not_stale_it(self):
        state, _ = self.spatial((("A", 2, 2), ("B", 1, 3)))
        other = [e for e in state.family("Envelope") if e["body"].endswith("B")][0]
        self.revise(state, Op("SUPERSEDE", "Envelope", other["entity_id"],
                              {"extent": {"half_extent": [3, 3, 3],
                                          "centre": [0, 0, 0]}}, "test",
                              reason="another branch"))
        for t in state.family("Transition"):
            if t["entity_id"].endswith("1"):
                continue
        self.assertEqual("STANDING", state.entities["STA-CFG-C0A"].get("_validity"))

    def test_s04b_supersedes_only_with_a_geometric_reason(self):
        """A revision with a reason is applied and retains both values; one
        without is not applied at all."""
        with_reason = s04b_response(
            "JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A",
            revisions=[{"envelope": "ENV-0A", "half_extent": [2, 2, 2],
                        "centre": [0, 0, 0],
                        "geometric_reason": "the arm cannot clear at the committed size"}])
        state, _ = self.spatial(s04b=with_reason)
        env = state.entities["ENV-0A"]
        self.assertEqual([2, 2, 2], env["extent"]["half_extent"])
        self.assertTrue(env.get("_superseded"), "the prior value was not retained")

        silent = s04b_response(
            "JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A",
            revisions=[{"envelope": "ENV-0A", "half_extent": [2, 2, 2],
                        "centre": [0, 0, 0], "geometric_reason": ""}])
        state2, res2 = self.spatial(s04b=silent)
        self.assertEqual([1, 1, 1], state2.entities["ENV-0A"]["extent"]["half_extent"],
                         "a commitment was contradicted with no reason")
        self.assertTrue(any("no geometric reason" in p or "geometric reason" in p
                            for p in res2["A"][1].declared_incompleteness),
                        res2["A"][1].declared_incompleteness)


# =====================================================================
# G4, G5 - the axis
# =====================================================================
class TestJointFrameAndAxis(_S04Chain):

    JOINT = {"entity_id": "JNT-X", "joint_type": "REVOLUTE", "axis_direction": "+Z",
             "child_group": "RGP-1"}
    BOX = ([-1, -1, -1], [1, 1, 1])

    def test_G4_a_missing_axis_refuses_to_compute(self):
        for axis in (None, "", "NONE", "diagonal", 7):
            self.assertIsNone(axis_index(axis), repr(axis))
            got = sweep_hull(self.BOX, dict(self.JOINT, axis_direction=axis),
                             [0, 0, 0], 0.0, 90.0)
            self.assertFalse(got["computable"], repr(axis))
            self.assertIn("names no coordinate", got["why"])

    def test_G4b_it_never_defaults_to_Z(self):
        """The defaults are gone from the source and from the behaviour: a
        no-axis sweep and a Z sweep must not agree, because one of them does not
        happen."""
        from .test_s3_interface_readiness import _code_only
        # CODE, not prose: the docstrings quote the defaults they describe, and a
        # scan that read them would fail on the explanation of the fix.
        for fn in (s04.sweep_hull, s04.rotate_about_axis, s04.axis_index,
                   s04.swept_clearance_check, s04.joint_frame_check):
            src = _code_only(fn)
            self.assertNotIn('"+Z"', src, fn.__name__)
            self.assertNotIn(', 2)', src, fn.__name__)
        z = sweep_hull(self.BOX, self.JOINT, [0, 0, 0], 0.0, 90.0)
        self.assertTrue(z["computable"])
        blank = sweep_hull(self.BOX, dict(self.JOINT, axis_direction=None),
                           [0, 0, 0], 0.0, 90.0)
        self.assertNotIn("hull", blank)

    def test_G5_every_axis_and_both_joint_kinds_take_the_same_path(self):
        seen = {}
        for axis in ("+X", "-X", "+Y", "-Y", "+Z", "-Z"):
            for kind in ("REVOLUTE", "PRISMATIC"):
                j = dict(self.JOINT, joint_type=kind, axis_direction=axis)
                got = sweep_hull(self.BOX, j, [0, 0, 0], 0.0, 2.0)
                self.assertTrue(got["computable"], "%s %s" % (kind, axis))
                seen[(kind, axis)] = got["hull"]
        # The axis actually decides the geometry: a prismatic joint grows the box
        # along its own coordinate and no other.
        for axis in ("+X", "+Y", "+Z"):
            idx = axis_index(axis)
            lo, hi = seen[("PRISMATIC", axis)]
            for i in range(3):
                grew = (hi[i] - lo[i]) > 2.0 + 1e-9
                self.assertEqual(i == idx, grew, "%s grew on %d" % (axis, i))

    def test_G4c_the_check_reports_an_unusable_frame(self):
        state, _ = self.spatial()
        self.assertEqual([], s04.joint_frame_check(state))
        self.revise(state, Op("SUPERSEDE", "Joint", "JNT-A",
                              {"axis_direction": "NONE"}, "test",
                              reason="the axis was withdrawn"))
        found = s04.joint_frame_check(state)
        self.assertTrue(any("JOINT_FRAME_INCOMPLETE" in p for p in found), found)


# =====================================================================
# G6, G7 - configurations and transitions are realized
# =====================================================================
class TestRealization(_S04Chain):

    BASIS = {"CFG-C0A": [{"rigid_group": "RGP-G0A", "dof": "RZ",
                          "differs_from": ["CFG-C1A"]}]}

    def test_G6_declared_distinctness_that_realization_violates_is_a_finding(self):
        ok, _ = self.spatial(basis=self.BASIS)
        self.assertEqual([], s04.configuration_realization_check(ok))
        same = s04b_response("JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A",
                             coords=(30, 30), changed=[])
        bad, _ = self.spatial(s04b=same, basis=self.BASIS)
        found = s04.configuration_realization_check(bad)
        self.assertTrue(any("DECLARED_DISTINCTNESS_NOT_REALIZED" in p for p in found),
                        found)

    def test_G6b_without_a_declared_basis_nothing_is_demanded(self):
        """Conditional on the premise, never 'all configurations must differ'."""
        same = s04b_response("JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A",
                             coords=(30, 30), changed=[])
        state, _ = self.spatial(s04b=same)
        self.assertEqual([], s04.configuration_realization_check(state))

    def test_G7_a_declared_change_the_endpoints_do_not_make_is_a_finding(self):
        state, _ = self.spatial(
            s04b=s04b_response("JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A",
                               coords=(30, 30), changed=["JNT-A"]))
        found = s04.transition_realization_check(state)
        self.assertTrue(any("DECLARED_CHANGE_NOT_REALIZED" in p for p in found), found)

    def test_G7b_a_change_that_happens_and_is_not_declared_is_also_a_finding(self):
        state, _ = self.spatial(
            s04b=s04b_response("JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A",
                               coords=(0, 90), changed=[]))
        found = s04.transition_realization_check(state)
        self.assertTrue(any("UNDECLARED_COORDINATE_CHANGE" in p for p in found), found)

    def test_G7c_a_truthful_transition_is_quiet(self):
        state, _ = self.spatial()
        self.assertEqual([], s04.transition_realization_check(state))


# =====================================================================
# G8, G9 - motion evidence follows the computation
# =====================================================================
class TestMotionEvidence(_S04Chain):

    JOINT = {"entity_id": "JNT-X", "joint_type": "REVOLUTE", "axis_direction": "+Z",
             "child_group": "RGP-1"}
    BOX = ([-1, -1, -1], [1, 1, 1])

    def test_G8_changing_the_computation_changes_the_level(self):
        two = sweep_hull(self.BOX, self.JOINT, [0, 0, 0], 0.0, 90.0, samples=2)
        many = sweep_hull(self.BOX, self.JOINT, [0, 0, 0], 0.0, 90.0, samples=9)
        self.assertEqual("ENDPOINTS_ONLY", two["motion_evidence_level"])
        self.assertEqual("SAMPLED", many["motion_evidence_level"])
        self.assertEqual(2, two["sampling_declaration"]["samples"])
        self.assertEqual(9, many["sampling_declaration"]["samples"])
        self.assertNotEqual(two["hull"], many["hull"],
                            "the two computations produced the same geometry, so "
                            "the level would be labelling nothing")

    def test_G8b_the_level_this_method_cannot_support_is_never_claimed(self):
        for n in (2, 3, 5, 9, 33):
            got = sweep_hull(self.BOX, self.JOINT, [0, 0, 0], 0.0, 90.0, samples=n)
            self.assertIn(got["motion_evidence_level"],
                          ("ENDPOINTS_ONLY", "SAMPLED"))
            self.assertNotIn(got["motion_evidence_level"], ("SWEPT", "CONTINUOUS"))

    def test_G9_a_declared_level_the_record_does_not_support_is_caught(self):
        state, _ = self.spatial()
        self.assertEqual([], s04.motion_evidence_check(state))
        v = state.family("SweptVolume")[0]["entity_id"]
        self.revise(state, Op("SUPERSEDE", "SweptVolume", v,
                              {"fidelity": "CONTINUOUS"}, "test",
                              reason="claim a level the computation did not make"))
        found = s04.motion_evidence_check(state)
        self.assertTrue(any("MOTION_EVIDENCE_OVERSTATED" in p for p in found), found)

    def test_G9b_the_constant_declaration_has_no_home_to_come_back_to(self):
        """The retired shape: a declaration written by the parser, before any
        sweep, on the Transition. Neither the writer nor the field survives."""
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S04BPlacementAndMotion.to_operations)
        self.assertNotIn("sampling_declaration", src,
                         "the parser writes a declaration again, before any sweep")
        self.assertNotIn("SAMPLES", src)
        for t in state_fields(self, "Transition"):
            self.assertNotIn("sampling_declaration", t)
            self.assertNotIn("motion_evidence_level", t)
        fields = Contracts().required_fields("Transition")
        self.assertNotIn("sampling_declaration", fields)

    def test_G9c_a_transition_that_moves_with_no_computation_says_so(self):
        state, _ = self.spatial()
        for v in state.family("SweptVolume"):
            self.revise(state, Op("INVALIDATE", "SweptVolume", v["entity_id"], {},
                                  "test", reason="the computation is withdrawn"))
        found = s04.motion_evidence_check(state)
        self.assertTrue(any("MOTION_NOT_COMPUTED" in p for p in found), found)

    def test_the_evidence_carries_the_premises_it_was_computed_from(self):
        state, _ = self.spatial()
        v = state.family("SweptVolume")[0]
        self.assertIn("JNT-A", v["_premises"])
        self.assertIn("ENV-0A", v["_premises"])
        self.assertIn(v["fidelity"], ("ENDPOINTS_ONLY", "SAMPLED"))


# =====================================================================
# G10 - LoadPath hops are Interfaces
# =====================================================================
class TestLoadPathSpatial(_S04Chain):

    def test_G10_hops_are_interpreted_through_interfaces(self):
        state, _ = self.spatial()
        lp = state.family("LoadPath")[0]
        for h in lp["ordered_hops"]:
            self.assertEqual("Interface", state.stored_family(h))
        self.assertEqual([], s04.load_path_reaction_check(state))

    def test_G10b_changing_interface_incidence_changes_the_result(self):
        """The same envelopes, a different body pair on the interface."""
        state, _ = self.spatial()
        before = s04.load_path_reaction_check(state)
        self.revise(state, Op("SUPERSEDE", "Interface", "IFG-A",
                              {"bodies": ["BOD-G0A", "BOD-G1A"]}, "test",
                              reason="the interface joins the far pair"))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-1A",
                              {"extent": {"half_extent": [1, 1, 1],
                                          "centre": [40, 0, 0]}}, "test",
                              reason="move the far body away"))
        after = s04.load_path_reaction_check(state)
        self.assertEqual([], before)
        self.assertTrue(any("LOADPATH_HOP_DISJOINT" in p for p in after), after)

    def test_G10c_the_retired_body_reading_cannot_even_enter_state(self):
        """Stronger than a check: `ordered_hops` declares Interface, so a body id
        is refused at the write boundary. The check's own hop-not-an-interface
        finding covers a hop that resolves to nothing at all."""
        from ver3.assy_v3.state.design_state import ContractError
        state, _ = self.spatial()
        with self.assertRaises(ContractError) as caught:
            self.revise(state, Op("SUPERSEDE", "LoadPath", "LDP-A",
                                  {"ordered_hops": ["BOD-G0A", "BOD-G1A"]}, "test",
                                  reason="body ids, the retired reading"))
        self.assertIn("REFERENCE_FAMILY", str(caught.exception))


# =====================================================================
# sequencing, and the frozen layers
# =====================================================================
class TestSequencingAndFreeze(_S04Chain):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_s04b_is_reachable_without_a_selection_decision(self):
        state, _ = self.build([("A", 2, 2)])
        self.assertEqual([], state.standing("SelectionDecision"))
        self.assertIsNone(cv.committed_branch(state, self.c))
        provider = _Canned(s04a_response(["BOD-G0A", "BOD-G1A"], step="ASY-A",
                                         actor="ACT-0001"))
        inv = cv.InvocationContext(branch="CND-A")
        state.apply(S04AEnvelopeAndReach().invoke(
            provider, state, state.run_id, {"candidate": "CND-A"},
            attempt=1, invocation=inv).patch)
        view = S04BPlacementAndMotion().consumer_view(state, inv)
        self.assertIs(cv.ViewStatus.VIEW_READY, view.status,
                      [a for a in view.assessment if a["verdict"] != "SATISFIED"])

    def test_no_selection_decision_was_fabricated(self):
        state, _ = self.spatial()
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual([], s04.selection_gate_check(state))

    def test_the_retired_premise_is_recorded_not_deleted(self):
        """S-6 staged it behind S-7. S7-A retired it instead: activating it would
        have meant SelectionDecision -> s04b, while the architecture requires
        s04b -> feasibility -> selection -> SelectionDecision. What it used to
        say is kept beside the reason it cannot come back."""
        from ver3.assy_v3.view.boundary import responsibility_contract
        b = responsibility_contract()["stages"]["s04b"]
        live = {c["class"] for c in b["required_reasoning_premise_classes"]}
        self.assertNotIn("selection_decision", live)
        self.assertEqual([], b.get("premise_classes_pending_step") or [])
        retired = {c["class"]: c for c in b.get("retired_premise_classes") or []}
        self.assertIn("selection_decision", retired)
        self.assertEqual("S7-A", retired["selection_decision"]["retired_by"])
        self.assertEqual("COMMITTED_BRANCH",
                         retired["selection_decision"]["was"]["population"])

    def test_s04a_arrangement_is_a_real_premise_of_s04b(self):
        state, _ = self.build([("A", 2, 2)])
        inv = cv.InvocationContext(branch="CND-A")
        view = S04BPlacementAndMotion().consumer_view(state, inv)
        self.assertIsNot(cv.ViewStatus.VIEW_READY, view.status,
                         "s04b was ready with no arrangement to extend")

    def test_S4_and_S5_invariants_are_untouched(self):
        from ver3.assy_v3.stages.s03_topology_and_mobility import (
            S03BMobilityAndAssembly, current_dof_domain, dof_totality_check)
        state, res = self.spatial((("A", 2, 2), ("B", 1, 3)))
        self.assertEqual([], dof_totality_check(state))
        self.assertEqual((2 * 2 + 1 * 3) * 6, len(current_dof_domain(state)))
        for mex in state.family("MobilityExpectation"):
            self.assertEqual("STANDING", mex.get("_validity"))
        self.assertEqual([], S03BMobilityAndAssembly()._s4_physical_problems(
            {"constraint_relations": [], "load_paths": [], "unresolved": [],
             "physical_interactions": []},
            {"consumer_view": {}}))


if __name__ == "__main__":
    unittest.main()
