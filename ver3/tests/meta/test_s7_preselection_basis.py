"""WHAT FEASIBILITY MAY DECIDE ON BEFORE SELECTION, and what it may not.

Four evaluators could not return PASS for an ordinary correct mechanism, and a
benchmark of six candidates had no FAIL anywhere and no FEASIBLE_FOR_SELECTION
anywhere either. Each was a place where the evaluator held the design to a
standard nobody was contracted to meet, or asked a question the design had
already answered in a field the evaluator did not read:

  reach          NOT_ESTABLISHED on every demand, because "no deterministic
                 reach basis exists" - and no stage is contracted to produce
                 one. s04a's ReachResult is the contracted conclusion.
  assemblability an arriving part's conservative corridor passes through the
                 part it is declared to MEET, reported as an obstruction.
  spatial        the middle link of a serial chain is moved by both its joints,
                 reported as "ambiguous" because the evaluator wanted one.
  interference   two named features on one body pair - a journal and a snap
                 retainer - reported as the design contradicting itself.

And one place where a question that belongs to embodiment was asked before
selection: whether a declared snap-fit's flexure survives, with the qualitative
principle already stated.

None of this lowers a bar. Absence is still NOT_ESTABLISHED, a negative
conclusion is still FAIL, an undeclared overlap is still unestablished, and a
label with no principle behind it still establishes nothing.
"""
from __future__ import annotations

import copy
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, topology)

THREE = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
         "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
         "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])}


def with_region(top, actor="ACT-0001", rid="FRG-A", body="BOD-G0A"):
    out = dict(top)
    out["functional_regions"] = [{"id": rid, "role": "ACCESS",
                                  "owning_bodies": [body],
                                  "required_by_actors": [actor] if actor else []}]
    return out


def reach_arrangement(boxes, region, actor, reachable=True, target=None):
    """s04a's conclusion ABOUT THE REGION the actor is declared to need. A
    conclusion about some body is not a conclusion about this demand."""
    out = arrangement(boxes, steps=["ASY-0A"], region=region, actor=actor)
    for r in out["reach_results"]:
        r["reachable"] = reachable
        r["target"] = target or region
    return out


# =====================================================================
# A1 - the pre-selection reach basis
# =====================================================================
class TestReachBasis(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def demanding(self):
        """A design whose one actor must reach something. The harness's default
        actor reaches for nothing, which is a design with no reach question."""
        state = self.seed(must_reach=["the latch"])
        self.candidates(state)
        return state

    def test_R1_positive_current_evidence_passes(self):
        """An actor-required ACCESS region and s04a's positive conclusion about
        it. That is the contracted evidence level before selection, and the
        level is recorded on the verdict beside the PASS."""
        state = self.demanding()
        self.hinge(state=state, s03a=with_region(topology("A", 2, [(0, 1)])),
                   s04a=reach_arrangement(HINGE_BOXES, "FRG-A", "ACT-0001"))
        v = self.domain(self.assess(state, apply_patch=False), "reach")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("EVERY_ACTOR_REACHES_ITS_REGION", v.reason_codes)
        self.assertIn(s07.MODEL_LOCAL_POSITIVE, v.reason_codes,
                      "the evidence level is part of the record")
        # The conclusion and the region it is about are what the PASS rests on.
        self.assertIn("FRG-A", v.premises)
        self.assertTrue(any(p.startswith("RCH-") for p in v.premises))

    def test_R2_a_negative_conclusion_fails(self):
        """s04a looked at its own arrangement and said the actor cannot get
        there. That is positive evidence, not an absence."""
        state = self.demanding()
        self.hinge(state=state, s03a=with_region(topology("A", 2, [(0, 1)])),
                   s04a=reach_arrangement(HINGE_BOXES, "FRG-A", "ACT-0001",
                                          reachable=False))
        out = self.assess(state, apply_patch=False)
        v = self.domain(out, "reach")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("REACH_CONCLUDED_UNREACHABLE", v.reason_codes)
        self.assertIn(s07.MODEL_LOCAL_NEGATIVE, v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)

    def test_R3_a_region_with_no_conclusion_is_not_established(self):
        state = self.demanding()
        self.hinge(state=state, s03a=with_region(topology("A", 2, [(0, 1)])),
                   s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                    region="FRG-A", actor=None))
        v = self.domain(self.assess(state, apply_patch=False), "reach")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("REACH_CONCLUSION_ABSENT", v.reason_codes)

    def test_R3b_a_demand_with_no_region_is_not_established(self):
        state = self.demanding()
        self.hinge(state=state)
        v = self.domain(self.assess(state, apply_patch=False), "reach")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("REACH_REALIZATION_ABSENT", v.reason_codes)

    def test_R3c_a_region_declared_for_another_actor_answers_nobody(self):
        """A region present and a conclusion present, but the region is declared
        as a DIFFERENT actor's. Reach for an actor is established through a
        region the design says is that actor's."""
        state = self.demanding()
        self.add(state, "s01", "Actor", "ACT-OTHER", must_reach=[])
        self.hinge(state=state,
                   s03a=with_region(topology("A", 2, [(0, 1)]), actor="ACT-OTHER"),
                   s04a=reach_arrangement(HINGE_BOXES, "FRG-A", "ACT-0001"))
        v = self.domain(self.assess(state, apply_patch=False), "reach")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("REACH_REGION_NOT_DECLARED_FOR_ACTOR", v.reason_codes)

    def test_R4_another_candidates_conclusion_cannot_satisfy_this_one(self):
        """Two branches. B has the region and the positive conclusion; A has the
        demand and nothing. The view is branch-local, so B's answer is not in
        A's question."""
        state = self.demanding()
        self.hinge(state=state)                                  # A: demand only
        self.branch(state, "B",
                    with_region(topology("B", 2, [(0, 1)]), rid="FRG-B",
                                body="BOD-G0B"),
                    realization("B"),
                    reach_arrangement({k.replace("A", "B"): v
                                       for k, v in HINGE_BOXES.items()},
                                      "FRG-B", "ACT-0001"),
                    motion("B", "JNT-0B", _group(1, "B")))
        a = self.domain(self.assess(state, "CND-A", apply_patch=False), "reach")
        b = self.domain(self.assess(state, "CND-B", apply_patch=False), "reach")
        self.assertEqual(s07.NOT_ESTABLISHED, a.status)
        self.assertEqual(s07.PASS, b.status, b.summary)
        self.assertFalse({"FRG-B"} & set(a.premises))
        self.assertFalse(any(p.startswith("RCH-CND-B") for p in a.premises))


# =====================================================================
# A2 - the insertion corridor and the pair it is arriving at
# =====================================================================
class TestInsertionCorridor(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    NESTED = {"BOD-G0A": ([0, 0, 0], [3, 2, 2]),
              "BOD-G1A": ([0.5, 0, 0], [2.5, 1.5, 1.5])}

    def steps(self, sfx="A", second_dir=(1, 0, 0)):
        r = realization(sfx, steps=(0, 1))
        r["assembly_steps"][1]["order_index"] = 2
        return r

    def test_I1_a_declared_mating_target_is_not_an_obstruction(self):
        """BOD-G1A nests inside BOD-G0A, and the topology declares them in
        CONTACT. The corridor of the arriving part passes through the box it
        is going to sit in. That is arriving, not colliding."""
        top = topology("A", 2, [(0, 1)])                 # one CONTACT interface
        arr = arrangement(self.NESTED, steps=["ASY-0A", "ASY-1A"])
        arr["assembly_directions"][1]["direction"] = [1, 0, 0]
        state = self.hinge(s03a=top, s03b=self.steps(), s04a=arr)
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertNotIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes, v.summary)
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("IFC-0A", v.premises, "the declaring interface is the premise")

    def test_I2_an_unrelated_prior_body_still_weakens(self):
        """Three bodies; the arriving one is declared to meet G1 and its
        corridor also crosses G2, which nothing declares. G2 still counts."""
        # IFC-0A is what the harness's load path and interaction hang on, so
        # it is kept and re-pointed at the pair that IS declared: G1-G2.
        top = topology("A", 3, [(1, 2)])
        # G2 sits between G0 and G1 along X, arriving along -X: its corridor
        # crosses G1 (declared) and then G0 (not).
        boxes = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                 "BOD-G1A": ([3.0, 0, 0], [1, 1, 1]),
                 "BOD-G2A": ([1.5, 0, 0], [1, 1, 1])}
        r = realization("A", steps=(0, 1, 2))
        for n, s in enumerate(r["assembly_steps"]):
            s["order_index"] = n + 1
        arr = arrangement(boxes, steps=["ASY-0A", "ASY-1A", "ASY-2A"])
        for d in arr["assembly_directions"]:
            d["direction"] = [-1, 0, 0]
        state = self.hinge(s03a=top, s03b=r, s04a=arr)
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes)
        self.assertIn("BOD-G2A entering meets BOD-G0A", v.summary)
        self.assertNotIn("BOD-G2A entering meets BOD-G1A", v.summary,
                         "the declared mating target was reported as an obstacle")

    def test_I3_an_undeclared_pair_is_not_exempt(self):
        """Three bodies. The only declared interface is G0-G2; G1 nests into
        G0 with nothing declared between them, and that corridor is exactly
        what the design has not shown to be clear."""
        top = topology("A", 3, [(0, 2)])
        boxes = dict(self.NESTED, **{"BOD-G2A": ([9, 0, 0], [1, 1, 1])})
        arr = arrangement(boxes, steps=["ASY-0A", "ASY-1A"])
        arr["assembly_directions"][1]["direction"] = [1, 0, 0]
        state = self.hinge(s03a=top, s03b=self.steps(), s04a=arr)
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes)
        self.assertIn("BOD-G1A entering meets BOD-G0A", v.summary)

    def test_I3b_a_clearance_pair_is_not_exempt_either(self):
        """Declared to stay CLEAR is the opposite of declared to meet."""
        top = topology("A", 2, [(0, 1)])
        top["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        arr = arrangement(self.NESTED, steps=["ASY-0A", "ASY-1A"])
        arr["assembly_directions"][1]["direction"] = [1, 0, 0]
        state = self.hinge(s03a=top, s03b=self.steps(), s04a=arr)
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes)

    def test_I4_step_order_is_deterministic(self):
        top = topology("A", 2, [(0, 1)])
        arr = arrangement(self.NESTED, steps=["ASY-0A", "ASY-1A"])
        arr["assembly_directions"][1]["direction"] = [1, 0, 0]

        def run(reverse):
            r = self.steps()
            if reverse:
                r["assembly_steps"] = list(reversed(r["assembly_steps"]))
            state = self.hinge(s03a=top, s03b=r, s04a=arr)
            v = self.domain(self.assess(state, apply_patch=False), "assemblability")
            return v.status, tuple(v.reason_codes), tuple(v.premises)
        self.assertEqual(run(False), run(True))


# =====================================================================
# A3 - a serial chain's middle link
# =====================================================================
class TestSerialChain(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    JOINTS = [{"id": "JNT-0A", "joint_type": "REVOLUTE", "parent_group": "RGP-G0A",
               "child_group": "RGP-G1A", "dof": ["RZ"], "axis_direction": "+Z",
               "frame_ids": ["F1"]},
              {"id": "JNT-1A", "joint_type": "REVOLUTE", "parent_group": "RGP-G1A",
               "child_group": "RGP-G2A", "dof": ["RZ"], "axis_direction": "+Z",
               "frame_ids": ["F1"]}]

    def chain(self, joints=None, changed=("JNT-0A", "JNT-1A"), moving=("RGP-G1A",)):
        top = topology("A", 3, [(0, 1), (1, 2)])
        top["joints"] = copy.deepcopy(joints or self.JOINTS)
        r = realization("A", hops=(0, 0), demand=None)
        r["transition_requirements"] = [{
            "id": "TRQ-0A", "from_configuration": "CFG-C0A",
            "to_configuration": "CFG-C1A",
            "required_relative_motions": [{"joint": j, "dof": "RZ"} for j in changed]}]
        s04b = motion("A", "JNT-0A", moving[0])
        s04b["transitions"][0]["moving_groups"] = list(moving)
        s04b["transitions"][0]["changed_coordinates"] = list(changed)
        s04b["joint_placements"] = [{"joint": j["id"], "origin": [0, 0, 0]}
                                    for j in top["joints"]]
        for st in s04b["state_coordinates"]:
            for j in top["joints"]:
                st["coordinates"][j["id"]] = (0 if st["configuration"].endswith("C0A")
                                              else (90 if j["id"] in changed else 0))
        return self.hinge(s03a=top, s03b=r,
                          s04a=arrangement(THREE, steps=["ASY-0A"]), s04b=s04b)

    def test_S1_a_middle_link_moved_by_both_joints_is_not_ambiguous(self):
        """G1 sits between J0 and J1 and both turn. It is moved by both - that
        is what a chain is - and the transition says so in full."""
        v = self.domain(self.assess(self.chain(), apply_patch=False),
                        "spatial_realization")
        self.assertNotIn("MOVING_GROUP_DRIVER_AMBIGUOUS", v.reason_codes)
        self.assertNotIn("MOVING_GROUP_HAS_NO_JOINT", v.reason_codes)
        self.assertIn("JNT-0A", v.premises)
        self.assertIn("JNT-1A", v.premises)

    def test_S2_each_carrying_joint_must_still_be_usable(self):
        joints = copy.deepcopy(self.JOINTS)
        joints[1]["axis_direction"] = "DIAGONAL"
        v = self.domain(self.assess(self.chain(joints=joints), apply_patch=False),
                        "spatial_realization")
        self.assertIn("JOINT_AXIS_UNUSABLE", v.reason_codes)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)

    def test_S3_a_changed_joint_the_group_does_not_touch_does_not_count(self):
        """G0 is moved, and the only changed joint it touches is J0. J1 changing
        says nothing about G0: an unreadable axis on J1 must not reach G0's
        verdict, where it would if J1 were counted as carrying G0."""
        joints = copy.deepcopy(self.JOINTS)
        joints[1]["axis_direction"] = "DIAGONAL"
        v = self.domain(self.assess(self.chain(joints=joints, changed=("JNT-0A",),
                                               moving=("RGP-G0A",)),
                                    apply_patch=False), "spatial_realization")
        self.assertNotIn("JOINT_AXIS_UNUSABLE", v.reason_codes, v.summary)
        self.assertNotIn("MOVING_GROUP_HAS_NO_JOINT", v.reason_codes)

    def test_S3b_a_moving_group_none_of_the_changed_joints_touch(self):
        v = self.domain(self.assess(self.chain(changed=("JNT-1A",),
                                               moving=("RGP-G0A",)),
                                    apply_patch=False), "spatial_realization")
        self.assertIn("MOVING_GROUP_HAS_NO_JOINT", v.reason_codes)

    def test_S4_reversing_parent_and_child_changes_nothing(self):
        def run(reverse):
            joints = copy.deepcopy(self.JOINTS)
            if reverse:
                for j in joints:
                    j["parent_group"], j["child_group"] = (j["child_group"],
                                                           j["parent_group"])
            v = self.domain(self.assess(self.chain(joints=joints),
                                        apply_patch=False), "spatial_realization")
            return v.status, tuple(v.reason_codes), tuple(v.premises)
        self.assertEqual(run(False), run(True))

    def test_S5_the_code_no_longer_speaks_of_a_single_driver(self):
        import inspect
        self.assertNotIn("MOVING_GROUP_DRIVER_AMBIGUOUS",
                         inspect.getsource(s07._spatial_realization))


# =====================================================================
# A4 - two features on one pair
# =====================================================================
class TestFeatureExpectation(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def pair(self, kinds_and_names):
        top = topology("A", 2, [(0, 1)])
        top["interfaces"] = [{"id": "IFC-%dA" % n, "bodies": ["BOD-G0A", "BOD-G1A"],
                              "interaction_kind": k, "nominal": name,
                              "addresses_obligations": []}
                             for n, (k, name) in enumerate(kinds_and_names)]
        return self.hinge(s03a=top)

    def test_F1_two_named_features_with_different_kinds_do_not_conflict(self):
        state = self.pair([("CLEARANCE", "ROTATING_JOURNAL"),
                           ("INTERFERENCE_FIT", "SNAP_RETENTION")])
        out = self.assess(state, apply_patch=False)
        for d in ("gross_interference", "spatial_realization"):
            self.assertNotIn("INTERFACE_EXPECTATION_CONFLICT",
                             self.domain(out, d).reason_codes, d)
        # And the pair is known to touch - the retainer grips.
        self.assertEqual(s07.PASS, self.domain(out, "spatial_realization").status,
                         self.domain(out, "spatial_realization").summary)

    def test_F2_the_same_named_feature_described_two_ways_conflicts(self):
        state = self.pair([("CLEARANCE", "JOURNAL"), ("CONTACT", "JOURNAL")])
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertIn("INTERFACE_EXPECTATION_CONFLICT", v.reason_codes)

    def test_F3_unnamed_duplicates_that_disagree_stay_conservative(self):
        """`nominal: true` names no feature. Two such rows are one feature
        described twice, and if they disagree that is the conflict."""
        state = self.pair([("CLEARANCE", True), ("CONTACT", True)])
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertIn("INTERFACE_EXPECTATION_CONFLICT", v.reason_codes)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)

    def test_F4_a_named_and_an_unnamed_feature_are_two_features(self):
        state = self.pair([("CLEARANCE", "JOURNAL"), ("CONTACT", True)])
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertNotIn("INTERFACE_EXPECTATION_CONFLICT", v.reason_codes)


# =====================================================================
# A5 - a deformation-resolved path, before selection
# =====================================================================
class TestDeformationPath(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def snap(self, termination="ELASTICITY", kind="INTERFERENCE_FIT",
             activates=("IFC-0A",)):
        top = topology("A", 2, [(0, 1)])
        top["interfaces"][0]["interaction_kind"] = kind
        r = realization("A", path_kind="DEFORMATION_RESOLVED")
        r["assembly_steps"][0]["termination_strategy"] = termination
        r["assembly_steps"][0]["activates"] = list(activates)
        return self.hinge(s03a=top, s03b=r)

    def test_P1_an_established_elastic_fit_passes_with_a_deferred_obligation(self):
        v = self.domain(self.assess(self.snap(), apply_patch=False), "assemblability")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("DEFORMATION_RESOLVED_BY_ELASTIC_FIT", v.reason_codes)
        self.assertIn("SIZING_DEFERRED_TO_EMBODIMENT", v.reason_codes)
        self.assertIn("IFC-0A", v.premises)

    def test_P2_a_bare_label_is_not_established(self):
        """DEFORMATION_RESOLVED with no elastic retention named: a path nothing
        holds."""
        v = self.domain(self.assess(self.snap(termination="NONE"), apply_patch=False),
                        "assemblability")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("DEFORMATION_RESOLVED_PATH_UNSUPPORTED", v.reason_codes)

    def test_P2b_elasticity_into_no_fit_is_not_established(self):
        v = self.domain(self.assess(self.snap(kind="CONTACT"), apply_patch=False),
                        "assemblability")
        self.assertIn("DEFORMATION_RESOLVED_PATH_UNSUPPORTED", v.reason_codes)

    def test_P3_a_positive_contradiction_still_fails(self):
        """A contradicted assembly ORDER is still a FAIL whatever the path
        kind says."""
        state = self.snap()
        self.revise(state, Op("SUPERSEDE", "AssemblyStep", "ASY-0A",
                              {"depends_on": ["ASY-0A"]}, "t",
                              reason="a step that depends on itself"), stage="s03")
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("ASSEMBLY_ORDER_CONTRADICTED", v.reason_codes)


if __name__ == "__main__":
    unittest.main()
