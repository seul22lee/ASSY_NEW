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
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
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


def basis_on(cfg, joint="JNT-0A", dof="RZ", differs=("CFG-C1A",)):
    """A basis that NAMES ITS JOINT. The subject of the declaration is the
    generalized coordinate, so the joint is what it points at."""
    return {cfg: [{"joint": joint, "dof": dof, "differs_from": list(differs)}]}


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
        basis = basis_on("CFG-C0A")
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
        basis = basis_on("CFG-C0A")
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
        basis = basis_on("CFG-C0A")
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
        basis = basis_on("CFG-C0A")
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
        basis = basis_on("CFG-C0A", differs=("CFG-C1A",))
        top = topology("A", 2, [(0, 1)], basis=basis, configs=3)
        s04b = motion("A", "JNT-0A", _group(1, "A"), coords=(60, 60))
        s04b["state_coordinates"].append(
            {"configuration": "CFG-C2A", "coordinates": {"JNT-0A": 120}})
        state = self.hinge(s03a=top, s04b=s04b)
        self.assertEqual([], state.family("State"),
                         "an uncontradicted configuration was committed anyway")

    def test_D16_a_refused_realization_places_nothing_either(self):
        """THIS REVERSED. It asserted the placements still commit, on the
        reasoning that where a joint sits is a fact the coordinates do not
        contradict. True - and keeping them broke the next attempt: the
        `frame_origin` EXTEND from a refused response was already stored when a
        later, VALID realization placed the same joint, and the valid one was
        refused for EXTEND_OVER_EXISTING. A response the gate refuses did not
        happen; the next one is asked against an unchanged state."""
        state = self.contradicted()
        joint = next(j for j in state.family("Joint") if j["entity_id"] == "JNT-0A")
        self.assertIsNone(joint.get("frame_origin"))
        self.assertEqual({"Joint": 0},
                         {"Joint": sum(1 for op in self.last_s04b.patch.operations
                                       if op.entity_type == "Joint")})

    def test_D16b_and_a_valid_realization_after_a_refused_one_lands(self):
        """The case that found it. Refused first, then valid: the second
        places its joints and writes its states."""
        state = self.contradicted()
        self.assertEqual([], state.family("State"))
        good = motion("A", "JNT-0A", _group(1, "A"))
        import ver3.assy_v3.view.consumer_view as cv
        from ver3.assy_v3.stages.s04_envelope_and_motion import S04BPlacementAndMotion
        from .test_s02_s03b_integration import _Canned
        out = S04BPlacementAndMotion().invoke(
            _Canned(good), state, state.run_id, {"candidate": "CND-A"},
            attempt=3, invocation=cv.InvocationContext(branch="CND-A"))
        self.assertEqual([], state.validate(out.patch), out.problems)
        state.apply(out.patch)
        self.assertEqual(2, len(state.family("State")))
        joint = next(j for j in state.family("Joint") if j["entity_id"] == "JNT-0A")
        self.assertEqual([0, 0, 0], joint.get("frame_origin"))

    def test_D17_a_clean_response_is_admitted_unchanged(self):
        """The gate refuses a contradiction and nothing else."""
        basis = basis_on("CFG-C0A")
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis))
        self.assertEqual(["STA-CFG-C0A", "STA-CFG-C1A"],
                         sorted(st["entity_id"] for st in state.family("State")))
        self.assertTrue(state.family("Transition"))
        self.assertTrue(state.family("SweptVolume"))
        self.assertEqual([], self.last_s04b.declared_incompleteness)

    def test_D18_a_question_withholds_nothing_only_a_contradiction_does(self):
        """A basis naming a DOF its joint does not free is a question: the
        declaration identifies no coordinate. Refusing the write on it would let
        an unanswered question destroy a realization that may well be right, so
        only the positive contradiction gates."""
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A", dof="TX"))
        state = self.hinge(s03a=top)
        self.assertTrue(state.family("State"), "a question withheld the write")
        self.assertTrue(any("that joint declares" in p
                            for p in self.last_s04b.declared_incompleteness),
                        self.last_s04b.declared_incompleteness)


# =====================================================================
# NEITHER SIDE OF A JOINT
# =====================================================================
class TestParentChildNeutral(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def probe(self, joint, moving, boxes=None):
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A"))
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

    def test_D6_the_basis_names_the_joint_and_not_a_side_of_it(self):
        """A distinction is about a joint COORDINATE, so which of the joint's two
        groups is written as the parent cannot enter the question at all."""
        v = self.verdicts(self.probe(JOINT, _group(1, "A")))
        self.assertEqual(s07.PASS, v["required_configurations"][0],
                         v["required_configurations"])

    def test_D7_a_moving_group_on_the_parent_side_has_a_joint(self):
        """`MOVING_GROUP_HAS_NO_JOINT` about a group the only joint relates."""
        v = self.verdicts(self.probe(JOINT, _group(0, "A")))
        self.assertNotIn("MOVING_GROUP_HAS_NO_JOINT",
                         v["spatial_realization"][1])

    def test_D8_reversing_parent_and_child_changes_no_verdict(self):
        """The same mechanism described the other way round, with each side in
        turn named as moving."""
        for moving in (_group(0, "A"), _group(1, "A")):
            forward = self.verdicts(self.probe(JOINT, moving))
            reverse = self.verdicts(self.probe(reversed_joint(JOINT), moving))
            self.assertEqual(forward, reverse, "moving %s" % moving)

    def test_D9_a_group_the_joint_does_not_touch_still_has_no_joint(self):
        """Neutrality is not permissiveness. A group neither side of any joint
        names is a group nothing moves, and that is still the finding."""
        boxes = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                 "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
                 "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])}
        top = topology("A", 3, [(0, 1)], basis=basis_on("CFG-C0A"))
        top["joints"] = [copy.deepcopy(JOINT)]
        state = self.hinge(s03a=top,
                           s04a=arrangement(boxes, steps=["ASY-0A"]),
                           s04b=motion("A", "JNT-0A", _group(2, "A")))
        v = self.domain(self.assess(state, apply_patch=False), "spatial_realization")
        self.assertIn("MOVING_GROUP_HAS_NO_JOINT", v.reason_codes)

    def test_D10_two_incident_joints_that_both_move_are_a_chain_not_an_ambiguity(self):
        """THIS REVERSED. It asserted MOVING_GROUP_DRIVER_AMBIGUOUS for a group
        whose two incident joints both change - and that is the middle link of
        a serial chain, moved by both, with the transition saying so in full
        through `changed_coordinates`. There was never a single driver to
        find. What is still asked is that every carrying joint be usable."""
        top = topology("A", 3, [(0, 1), (1, 2)],
                       basis=basis_on("CFG-C0A"))
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
        self.assertNotIn("MOVING_GROUP_DRIVER_AMBIGUOUS", v.reason_codes)
        self.assertIn("JNT-0A", v.premises)
        self.assertIn("JNT-1A", v.premises)

    def test_D11_a_serial_chain_with_two_incident_joints_is_deterministic(self):
        """THE CASE THE OLD ADDRESS COULD NOT ANSWER.

        On G0-[J0]-G1-[J1]-G2 the middle link touches two joints that both free
        RY, so a basis naming the GROUP had no determinate answer: the child-side
        convention picked one silently, and incidence called it ambiguous. The
        basis names J1, so there is nothing to resolve and nothing to be
        ambiguous about - and naming J0 instead is a different, equally
        determinate question.
        """
        joints = [dict(JOINT, id="JNT-0A", parent_group="RGP-G0A",
                       child_group="RGP-G1A"),
                  dict(JOINT, id="JNT-1A", parent_group="RGP-G1A",
                       child_group="RGP-G2A")]
        boxes = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                 "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
                 "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])}
        def build(named):
            top = topology("A", 3, [(0, 1), (1, 2)],
                           basis=basis_on("CFG-C0A", joint=named))
            top["joints"] = [copy.deepcopy(j) for j in joints]
            s04b = motion("A", "JNT-1A", _group(1, "A"))
            s04b["joint_placements"].append({"joint": "JNT-0A",
                                             "origin": [0, 0, 0]})
            for st in s04b["state_coordinates"]:
                st["coordinates"]["JNT-0A"] = 0
            return self.hinge(s03a=top, s03b=realization("A", hops=(0, 0)),
                              s04a=arrangement(boxes, steps=["ASY-0A"]),
                              s04b=s04b)

        # JNT-1A is the one that moves, and a basis naming it is realized.
        v = self.domain(self.assess(build("JNT-1A"), apply_patch=False),
                        "required_configurations")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertNotIn("DISTINCTNESS_DRIVER_AMBIGUOUS", v.reason_codes)
        self.assertIn("JNT-1A", v.premises)
        self.assertNotIn("JNT-0A", v.premises, "a joint nothing named was read")

        # A basis naming the OTHER incident joint is a different question with an
        # equally determinate answer - and it is a contradiction, so the write
        # gate refuses the realization rather than letting it be judged.
        other = build("JNT-0A")
        self.assertEqual([], other.family("State"))
        self.assertTrue(any("both realize JNT-0A" in p
                            for p in self.last_s04b.declared_incompleteness),
                        self.last_s04b.declared_incompleteness)

    def test_D19_a_joint_that_does_not_free_the_named_dof(self):
        """No coordinate in that degree of freedom means no value to compare.
        Substituting the one the joint DOES free would answer a question the
        design did not ask."""
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A", dof="TX"))
        state = self.hinge(s03a=top)
        v = self.domain(self.assess(state, apply_patch=False),
                        "required_configurations")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("DISTINCTNESS_DOF_NOT_SUPPORTED", v.reason_codes)

    def test_D20_a_multi_dof_joint_is_never_guessed(self):
        """`State.joint_coordinates` holds ONE scalar per joint, so on a joint
        freeing several it cannot say which of them a value is about. Reading the
        scalar as the named DOF would manufacture evidence for exactly the
        degree of freedom under question - so the answer is that it is not
        established, and this unit invents no vector coordinate to fix it."""
        top = topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A"))
        top["joints"][0]["dof"] = ["RZ", "TZ"]
        top["joints"][0]["joint_type"] = "CYLINDRICAL"
        state = self.hinge(s03a=top)
        v = self.domain(self.assess(state, apply_patch=False),
                        "required_configurations")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("DISTINCTNESS_COORDINATE_NOT_RESOLVABLE", v.reason_codes)

    def test_D21_an_old_schema_basis_cannot_be_written_at_all(self):
        """A row naming a rigid group and no joint names no coordinate.

        THERE IS NO SHIM, and there is no place to put one: `joint` is required,
        so the old shape is refused at the write boundary rather than carried
        forward for some consumer to work out. Converting it there would be the
        inference this schema change removed, moved one layer down and made
        invisible - and the conversion is not even available, because the group
        the old row names may touch two compatible joints or none.
        """
        from ver3.assy_v3.state.design_state import ContractError
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A")))
        with self.assertRaises(ContractError) as raised:
            self.revise(state, Op("SUPERSEDE", "Configuration", "CFG-C0A",
                                  {"distinguishing_basis": [
                                      {"rigid_group": "RGP-G1A", "dof": "RZ",
                                       "differs_from": ["CFG-C1A"]}]}, "t",
                                  reason="an output written under the old schema"),
                        stage="s03")
        self.assertIn("RECORD_REQUIRED", str(raised.exception))
        self.assertIn("joint", str(raised.exception))

    def test_D21b_and_a_row_naming_no_degree_of_freedom_is_refused_too(self):
        """The pair IS the coordinate. A joint without a DOF names a joint, not
        a value."""
        from ver3.assy_v3.state.design_state import ContractError
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A")))
        with self.assertRaises(ContractError) as raised:
            self.revise(state, Op("SUPERSEDE", "Configuration", "CFG-C0A",
                                  {"distinguishing_basis": [
                                      {"joint": "JNT-0A",
                                       "differs_from": ["CFG-C1A"]}]}, "t",
                                  reason="half a coordinate"), stage="s03")
        self.assertIn("RECORD_REQUIRED", str(raised.exception))
        self.assertIn("dof", str(raised.exception))

    def test_D22_a_basis_still_demands_no_transition_and_no_mobility(self):
        """The declaration is configuration identity. It creates no requirement
        to move and no claim that anything is free."""
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis_on("CFG-C0A")),
                           s03b=realization("A", demand=None),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       transition=False))
        self.assertEqual([], state.family("TransitionRequirement"))
        self.assertEqual([], state.family("Transition"))
        out = self.assess(state, apply_patch=False)
        for domain in ("transition_reachability", "motion_and_transitions"):
            self.assertEqual(s07.NOT_APPLICABLE, self.domain(out, domain).status,
                             domain)
        self.assertEqual(s07.PASS,
                         self.domain(out, "required_configurations").status)


if __name__ == "__main__":
    unittest.main()
