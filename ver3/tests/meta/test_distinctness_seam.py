"""DECLARED DISTINCTNESS: ONE RULE, TWO READERS, AND NEITHER SIDE OF A JOINT.

`Configuration.distinguishing_basis` says two named states are not the same
state. Whether the numbers agree was decided in ONE place - feasibility - and the
pass that WRITES the numbers had no rule about it at all. A response stating two
configurations at one coordinate was therefore accepted by the producer and
convicted by the evaluator a stage later, by which time the response that could
have been asked again was already state.

The formula is `s04.distinctness_findings` now, and both sides ask it.

The second half of this file is the parent/child seam. A joint states a RELATIVE
relation between two groups; which of them is written as the parent says nothing
about which one travels in the world. Two readers were matching on `child_group`
alone - the joint that carries a declared distinction, and the joint that moves a
group a transition names as moving - so a group named on the parent side had no
joint at all, and the same mechanism described the other way round got a
different verdict.

WHAT THIS IS NOT. Nothing here is about reachability. Two states differing is not
a demand that either be reachable from the other; that demand is a
TransitionRequirement and `transition_reachability` answers it.
"""
from __future__ import annotations

import copy
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, topology)

#: One joint relating two groups, written parent -> child.
JOINT = {"id": "JNT-0A", "joint_type": "REVOLUTE",
         "parent_group": "RGP-G0A", "child_group": "RGP-G1A",
         "dof": ["RZ"], "axis_direction": "+Z", "frame_ids": ["F1"]}


def reversed_joint(j):
    out = copy.deepcopy(j)
    out["parent_group"], out["child_group"] = out["child_group"], out["parent_group"]
    return out


def basis_on(cfg, group, dof="RZ", differs=("CFG-C1A",)):
    return {cfg: [{"rigid_group": group, "dof": dof,
                   "differs_from": list(differs)}]}


# =====================================================================
# ONE RULE
# =====================================================================
class TestOneRule(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_D1_the_producer_and_the_evaluator_call_the_same_function(self):
        """Not "the same idea": the same callable, from both sides. A formula
        copied into two passes is two rules that agree until one is edited."""
        import inspect
        producer = inspect.getsource(s04.S04BPlacementAndMotion.completeness)
        evaluator = inspect.getsource(s07._required_configurations)
        self.assertIn("distinctness_findings(", producer)
        self.assertIn("distinctness_findings(", evaluator)
        # And neither side keeps a second copy of the comparison.
        for body in (producer, evaluator):
            self.assertNotIn("differs_from", body)
            self.assertNotIn("distinguishing_basis", body)

    def test_D2_the_contradiction_is_the_producers_and_never_the_mechanisms(self):
        """Two configurations declared to differ, given one coordinate.

        The pass that wrote them says so in the same invocation - and because it
        then writes no realization, the evaluator never gets the chance to
        convict the MECHANISM of it. That is the whole point of the split. When
        the numbers were admitted and merely reported, feasibility read them as
        records of a design and returned INFEASIBLE on
        `required_configurations`: a candidate condemned for a contradiction its
        author introduced rather than its geometry. What feasibility says now is
        that there is nothing to judge.
        """
        basis = basis_on("CFG-C0A", _group(1, "A"))
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       coords=(60, 60)))
        out = self.last_s04b
        self.assertTrue(
            any("both realize JNT-0A at 60" in p
                for p in out.declared_incompleteness),
            out.declared_incompleteness)
        verdict = s07.evaluate_candidate_feasibility(state, "CND-A")
        self.assertNotEqual(s07.INFEASIBLE, verdict.status)
        self.assertTrue(any("UPSTREAM" in p for p in verdict.problems),
                        verdict.problems)
        self.assertEqual([], state.family("State"))

    def test_D3_a_realized_distinction_is_reported_by_neither(self):
        basis = basis_on("CFG-C0A", _group(1, "A"))
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis))
        self.assertEqual([], [p for p in (self.last_s04b.declared_incompleteness or [])
                              if "realize" in p])
        v = self.domain(self.assess(state, apply_patch=False),
                        "required_configurations")
        self.assertEqual(s07.PASS, v.status, v.summary)

    def test_D4_the_driver_joint_is_a_premise_of_the_verdict_that_used_it(self):
        """It decides WHICH coordinate is compared, so a PASS rests on it as
        much as a FAIL does. Naming facts only when they convict would make
        provenance a record of complaints."""
        basis = basis_on("CFG-C0A", _group(1, "A"))
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis))
        v = self.domain(self.assess(state, apply_patch=False),
                        "required_configurations")
        self.assertEqual(s07.PASS, v.status)
        self.assertIn("JNT-0A", v.premises)

    def test_D5_distinctness_is_not_read_by_the_reachability_question(self):
        """The two must not be mixed back together. Structural, against the code
        rather than the prose: the rule that answers "are these two states the
        same" is not consulted by the rule that answers "can this change happen",
        and neither reads the other's field."""
        import ast
        import inspect
        import textwrap

        def code_only(fn):
            src = textwrap.dedent(inspect.getsource(fn))
            lines = src.splitlines()
            for node in ast.walk(ast.parse(src)):
                body = getattr(node, "body", None)
                if not isinstance(body, list):
                    continue
                for child in body:
                    if (isinstance(child, ast.Expr)
                            and isinstance(getattr(child, "value", None), ast.Constant)
                            and isinstance(child.value.value, str)):
                        for n in range(child.lineno - 1,
                                       (child.end_lineno or child.lineno)):
                            lines[n] = ""
            return "\n".join(l for l in lines if not l.strip().startswith("#"))

        for fn in (s07._transition_reachability, s07._release_findings,
                   s04.realization_findings):
            src = code_only(fn)
            self.assertNotIn("distinguishing_basis", src, fn.__name__)
            self.assertNotIn("distinctness", src, fn.__name__)
        distinct = code_only(s04.distinctness_findings)
        for foreign in ("TransitionRequirement", "required_relative_motions",
                        "released_constraints", "realizes_requirement"):
            self.assertNotIn(foreign, distinct, foreign)


# =====================================================================
# A CONTRADICTED REALIZATION IS NOT ADMITTED
# =====================================================================
class TestTheWriteGate(_Feas):
    """Realizing declared distinctness numerically is S04b's RESPONSIBILITY.

    Detecting the contradiction is not discharging it. A response giving two
    configurations the design says are different states one coordinate has not
    realized them, and admitting it - reporting the problem and committing the
    numbers anyway - converts an invalid realization into evidence about the
    MECHANISM: the candidate is then convicted, a stage later, of a
    contradiction its author introduced rather than its geometry.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def contradicted(self):
        basis = basis_on("CFG-C0A", _group(1, "A"))
        return self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis),
                          s04b=motion("A", "JNT-0A", _group(1, "A"),
                                      coords=(60, 60)))

    def test_D12_no_state_coordinate_is_written(self):
        """The numbers do not become state. This is the whole criterion: the
        contradiction is refused at the write, not merely noted beside it."""
        state = self.contradicted()
        self.assertEqual([], state.family("State"))
        for op in self.last_s04b.patch.operations:
            self.assertNotEqual("State", op.entity_type, op.entity_id)

    def test_D13_and_nothing_computed_from_them_is_either(self):
        """A path between endpoint states nothing wrote, and an occupancy swept
        between them, would reference records that do not exist."""
        state = self.contradicted()
        self.assertEqual([], state.family("Transition"))
        self.assertEqual([], state.family("SweptVolume"))

    def test_D14_the_response_is_not_a_successful_realization(self):
        """It says so itself, in the same invocation, naming the contradiction."""
        self.contradicted()
        out = self.last_s04b
        self.assertEqual("CONTRACT_INCOMPLETE", out.execution_status.value)
        self.assertTrue(any("both realize JNT-0A at 60" in p
                            for p in out.declared_incompleteness),
                        out.declared_incompleteness)

    def test_D15_every_state_is_withheld_and_not_only_the_colliding_pair(self):
        """The coordinates are ONE answer. Keeping whichever configurations
        happen not to collide would commit a realization nobody produced."""
        basis = basis_on("CFG-C0A", _group(1, "A"), differs=("CFG-C1A",))
        top = topology("A", 2, [(0, 1)], basis=basis, configs=3)
        s04b = motion("A", "JNT-0A", _group(1, "A"), coords=(60, 60))
        s04b["state_coordinates"].append(
            {"configuration": "CFG-C2A", "coordinates": {"JNT-0A": 120}})
        state = self.hinge(s03a=top, s04b=s04b)
        self.assertEqual([], state.family("State"),
                         "an uncontradicted configuration was committed anyway")

    def test_D16_the_placement_still_commits(self):
        """Where a joint sits is a separate fact these coordinates do not
        contradict. Withholding the realization and committing what stands is
        the shape the refinement barrier already uses."""
        state = self.contradicted()
        joint = next(j for j in state.family("Joint") if j["entity_id"] == "JNT-0A")
        self.assertEqual([0, 0, 0], joint.get("frame_origin"))

    def test_D17_a_clean_response_is_admitted_unchanged(self):
        """The gate refuses a contradiction and nothing else."""
        basis = basis_on("CFG-C0A", _group(1, "A"))
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis))
        self.assertEqual(["STA-CFG-C0A", "STA-CFG-C1A"],
                         sorted(st["entity_id"] for st in state.family("State")))
        self.assertTrue(state.family("Transition"))
        self.assertTrue(state.family("SweptVolume"))
        self.assertEqual([], self.last_s04b.declared_incompleteness)

    def test_D18_a_question_about_the_driver_withholds_nothing(self):
        """A distinction the topology does not RESOLVE is a question, not a
        contradiction. Refusing the write on it would let an unanswered question
        destroy a realization that may well be right."""
        joints = [dict(JOINT, id="JNT-0A"),
                  dict(JOINT, id="JNT-1A", parent_group="RGP-G1A",
                       child_group="RGP-G0A")]
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A", _group(1, "A")))
        top["joints"] = joints
        s04b = motion("A", "JNT-0A", _group(1, "A"))
        s04b["joint_placements"].append({"joint": "JNT-1A", "origin": [0, 0, 0]})
        for st in s04b["state_coordinates"]:
            st["coordinates"]["JNT-1A"] = 0
        state = self.hinge(s03a=top, s04b=s04b)
        self.assertTrue(state.family("State"), "a question withheld the write")
        self.assertTrue(any("could be carried by" in p
                            for p in self.last_s04b.declared_incompleteness),
                        self.last_s04b.declared_incompleteness)


# =====================================================================
# NEITHER SIDE OF A JOINT
# =====================================================================
class TestParentChildNeutral(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def probe(self, joint, basis_group, moving, boxes=None):
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A", basis_group))
        top["joints"] = [copy.deepcopy(joint)]
        return self.hinge(s03a=top,
                          s04a=arrangement(boxes or HINGE_BOXES,
                                           steps=["ASY-0A"]),
                          s04b=motion("A", "JNT-0A", moving))

    def verdicts(self, state):
        out = self.assess(state, apply_patch=False)
        return {name: (self.domain(out, name).status,
                       tuple(sorted(self.domain(out, name).reason_codes)))
                for name in ("required_configurations", "spatial_realization")}

    def test_D6_a_distinction_on_the_parent_side_resolves(self):
        """The basis is about the group written as the joint's PARENT. Matching
        on `child_group` found no joint and reported that the topology does not
        support the distinction - about a joint that is right there."""
        v = self.verdicts(self.probe(JOINT, _group(0, "A"), _group(1, "A")))
        self.assertEqual(s07.PASS, v["required_configurations"][0],
                         v["required_configurations"])

    def test_D7_a_moving_group_on_the_parent_side_has_a_joint(self):
        """`MOVING_GROUP_HAS_NO_JOINT` about a group the only joint relates."""
        v = self.verdicts(self.probe(JOINT, _group(1, "A"), _group(0, "A")))
        self.assertNotIn("MOVING_GROUP_HAS_NO_JOINT",
                         v["spatial_realization"][1])

    def test_D8_reversing_parent_and_child_changes_no_verdict(self):
        """The same mechanism described the other way round. Every combination
        of which side carries the basis and which side is named as moving."""
        for basis_group in (_group(0, "A"), _group(1, "A")):
            for moving in (_group(0, "A"), _group(1, "A")):
                forward = self.verdicts(self.probe(JOINT, basis_group, moving))
                reverse = self.verdicts(self.probe(reversed_joint(JOINT),
                                                   basis_group, moving))
                self.assertEqual(forward, reverse,
                                 "basis on %s, moving %s" % (basis_group, moving))

    def test_D9_a_group_the_joint_does_not_touch_still_has_no_joint(self):
        """Neutrality is not permissiveness. A group neither side of any joint
        names is a group nothing moves, and that is still the finding."""
        boxes = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                 "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
                 "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])}
        top = topology("A", 3, [(0, 1)], basis=basis_on("CFG-C0A", _group(1, "A")))
        top["joints"] = [copy.deepcopy(JOINT)]
        state = self.hinge(s03a=top,
                           s04a=arrangement(boxes, steps=["ASY-0A"]),
                           s04b=motion("A", "JNT-0A", _group(2, "A")))
        v = self.domain(self.assess(state, apply_patch=False), "spatial_realization")
        self.assertIn("MOVING_GROUP_HAS_NO_JOINT", v.reason_codes)

    def test_D10_two_incident_joints_that_both_move_are_ambiguous(self):
        """The ambiguity semantics are preserved where they mean something: two
        joints of one group whose coordinates BOTH change, with nothing saying
        which produced the motion. Being incident to two joints is not itself
        ambiguous - every bar of a four-bar is - so what selects is the
        transition's own `changed_coordinates`."""
        top = topology("A", 3, [(0, 1), (1, 2)],
                       basis=basis_on("CFG-C0A", _group(1, "A")))
        boxes = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                 "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
                 "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])}
        s04b = motion("A", "JNT-0A", _group(1, "A"))
        s04b["joint_placements"].append({"joint": "JNT-1A", "origin": [0, 0, 0]})
        for st in s04b["state_coordinates"]:
            st["coordinates"]["JNT-1A"] = 0 if st["configuration"].endswith("C0A") else 45
        s04b["transitions"][0]["changed_coordinates"] = ["JNT-0A", "JNT-1A"]
        state = self.hinge(s03a=top, s03b=realization("A", hops=(0, 0)),
                           s04a=arrangement(boxes, steps=["ASY-0A"]), s04b=s04b)
        v = self.domain(self.assess(state, apply_patch=False), "spatial_realization")
        self.assertIn("MOVING_GROUP_DRIVER_AMBIGUOUS", v.reason_codes)

    def test_D11_two_compatible_drivers_for_a_distinction_stay_ambiguous(self):
        """The other ambiguity, unchanged by neutrality: two incident joints
        both leaving the declared DOF free. Picking one is what let a slider
        answer for a hinge."""
        joints = [dict(JOINT, id="JNT-0A"),
                  dict(JOINT, id="JNT-1A", parent_group="RGP-G1A",
                       child_group="RGP-G0A")]
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A", _group(1, "A")))
        top["joints"] = joints
        s04b = motion("A", "JNT-0A", _group(1, "A"))
        s04b["joint_placements"].append({"joint": "JNT-1A", "origin": [0, 0, 0]})
        for st in s04b["state_coordinates"]:
            st["coordinates"]["JNT-1A"] = 0
        state = self.hinge(s03a=top, s04b=s04b)
        v = self.domain(self.assess(state, apply_patch=False),
                        "required_configurations")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("DISTINCTNESS_DRIVER_AMBIGUOUS", v.reason_codes)


if __name__ == "__main__":
    unittest.main()
