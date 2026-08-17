"""Invariants judge the state a patch would LEAVE, not one operation at a time.

Every test here builds exactly ONE StagePatch, and says so by asserting it. That
is the whole point of the file: the defects it pins were invisible to every
existing test because the fixtures applied one entity per patch, so no validator
was ever asked about a patch that did two things at once.

What one-operation-at-a-time got wrong, in both directions:

  two SelectionDecisions in one patch    each saw zero others and BOTH were
                                         accepted - the design ended with two
                                         contradictory commitments
  retire-old + record-new in one patch   the new one was judged while the old
                                         still stood, so the only atomic way to
                                         change a decision was REFUSED
  a Joint beside its own RigidGroups     the groups were not in storage yet, so
                                         the same-body invariant had nothing to
                                         compare and returned clean

The third is the worst kind. It did not reject something valid or accept
something invalid by a visible margin - it reported success for a check that had
not run, which is indistinguishable from the check being satisfied.
"""

import unittest

from . import _fixtures

from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.view import committed_branch


#: A COMPLIANT joint's declared variant fields. Contract-valid throughout.
COMPLIANT_VARIANT = {
    "mode": "BENDING", "direction": "z", "required_travel": 1.0,
    "allowable_travel": 2.0, "actuation": "PRESCRIBED_KINEMATIC",
    "compliant_element": "the cantilever arm", "root_interface": "IFC-0001",
    "activation_window": "0..1",
}


def body(identity="shell", role="shell"):
    return {"instance_identity": identity, "role": role,
            "created_by_stage": "s03"}


def rigid_group(owning_body):
    return {"body": owning_body, "members": [], "is_default": True}


def joint(parent, child, joint_type="COMPLIANT"):
    fields = {"joint_type": joint_type, "parent_group": parent,
              "child_group": child, "dof": ["RZ"], "axis_direction": "+Z",
              "frame_ids": ["FRM-1"]}
    if joint_type.upper() == "COMPLIANT":
        fields.update(COMPLIANT_VARIANT)
    return fields


def joint_with_groups(*, same_body):
    """A body, its rigid groups, and the COMPLIANT joint between them.

    Module level because two classes need the identical shape: one creates it
    all in a single patch, the other creates the groups in an earlier patch and
    only the joint here. If those shapes could drift, comparing their verdicts
    would prove nothing.
    """
    ops = [Op("CREATE", "Body", "BOD-1", body("enclosure"), "p:s03"),
           Op("CREATE", "RigidGroup", "RGP-1", rigid_group("BOD-1"), "p:s03")]
    if same_body:
        ops.append(Op("CREATE", "RigidGroup", "RGP-2",
                      rigid_group("BOD-1"), "p:s03"))
    else:
        ops.append(Op("CREATE", "Body", "BOD-2", body("lid", "cover"), "p:s03"))
        ops.append(Op("CREATE", "RigidGroup", "RGP-2",
                      rigid_group("BOD-2"), "p:s03"))
    ops.append(Op("CREATE", "Joint", "JNT-1", joint("RGP-1", "RGP-2"), "p:s03"))
    return ops


class _OnePatch(_fixtures.StateBuilder, unittest.TestCase):
    """Everything below goes through a SINGLE patch, asserted rather than assumed."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def run_placeholder(self):
        """Only so this class can be instantiated as a fixture builder."""

    def one_patch(self, state, stage, ops):
        """Validate one patch containing every operation. Applies if clean.

        Deliberately NOT a loop over `self.add`. The helper that applies one
        entity per patch is what hid these defects, so a test written with it
        cannot make the claim this file exists to make.
        """
        self.assertGreater(
            len(ops), 1,
            "this helper is for MULTI-OPERATION patches; a single-op fixture "
            "cannot show anything about patch-level semantics")
        patch = StagePatch(
            patch_id="atomic-%d" % len(state.applied_patches),
            run_id=state.run_id, stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS", provenance={"purpose": "atomicity"})
        self.assertEqual(len(ops), len(patch.operations),
                         "the fixture did not put every operation in one patch")
        before = len(state.applied_patches)
        problems = state.validate(patch)
        if not problems:
            state.apply(patch)
            self.assertEqual(before + 1, len(state.applied_patches),
                             "more than one patch was applied")
        return problems

    def selection_fields(self, state, candidate):
        return self._fields_for(state, self.c, "selection", "SelectionDecision",
                                {"selected_candidate": candidate})

    def branched(self, run="atomic"):
        state = DesignState(run_id=run)
        self.add(state, "s02", "Candidate", "CND-A", principle="a hinged cover")
        self.add(state, "s02", "Candidate", "CND-B", principle="a sliding lid")
        return state


class TestTwoSelectionsInOnePatch(_OnePatch):

    def test_two_selection_decisions_created_in_one_patch_are_rejected(self):
        state = self.branched()
        problems = self.one_patch(state, "selection", [
            Op("CREATE", "SelectionDecision", "SEL-A",
               self.selection_fields(state, "CND-A"), "p:selection"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        self.assertTrue(problems,
                        "one patch created two standing commitments and the "
                        "design now contradicts itself")
        self.assertTrue(any("one_standing_selection" in p for p in problems),
                        problems)

    def test_the_rejection_names_both_decisions(self):
        """A reviewer must be able to see WHICH two, not merely that there were
        two - the fix is to retire one of them, and that requires knowing them."""
        state = self.branched()
        problems = self.one_patch(state, "selection", [
            Op("CREATE", "SelectionDecision", "SEL-A",
               self.selection_fields(state, "CND-A"), "p:selection"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        joined = " ".join(problems)
        self.assertIn("SEL-A", joined)
        self.assertIn("SEL-B", joined)

    def test_neither_decision_landed(self):
        state = self.branched()
        self.one_patch(state, "selection", [
            Op("CREATE", "SelectionDecision", "SEL-A",
               self.selection_fields(state, "CND-A"), "p:selection"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        self.assertEqual([], list(state.standing("SelectionDecision")))
        self.assertIsNone(committed_branch(state, self.c))


class TestAtomicSelectionReplacement(_OnePatch):
    """Retiring one decision and recording another, in a single patch.

    This is how a design changes its mind atomically, and it was refused: the
    new decision was judged against a state where the old one still stood. A
    caller could only comply by splitting it into two patches, which leaves a
    moment with no committed selection at all.
    """

    def decided(self):
        state = self.branched()
        self.add(state, "selection", "SelectionDecision", "SEL-A",
                 selected_candidate="CND-A")
        return state

    def test_the_fixture_starts_with_exactly_one_decision(self):
        state = self.decided()
        self.assertEqual(["SEL-A"],
                         [r["entity_id"]
                          for r in state.standing("SelectionDecision")])

    def test_invalidate_old_and_create_new_selection_in_one_patch_is_accepted(self):
        state = self.decided()
        problems = self.one_patch(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-A", {}, "p:selection",
               reason="review changed the choice"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        self.assertEqual([], problems,
                         "an atomic selection replacement was refused, so the "
                         "only way to change a decision leaves a gap with no "
                         "committed selection")

    def test_the_final_standing_selection_is_exactly_the_new_one(self):
        state = self.decided()
        self.one_patch(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-A", {}, "p:selection",
               reason="review changed the choice"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        self.assertEqual(["SEL-B"],
                         [r["entity_id"]
                          for r in state.standing("SelectionDecision")])

    def test_the_retired_decision_remains_in_history(self):
        state = self.decided()
        self.one_patch(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-A", {}, "p:selection",
               reason="review changed the choice"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        self.assertTrue(state.has_entity("SEL-A"),
                        "the previous choice was erased rather than retired")

    def test_all_three_consumers_observe_the_replacement(self):
        """The point of atomicity: s05, s06 and s07 must not disagree about
        which design it is at any moment."""
        from ver3.assy_v3.downstream import execution
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
        state = self.decided()
        self.one_patch(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-A", {}, "p:selection",
               reason="review changed the choice"),
            Op("CREATE", "SelectionDecision", "SEL-B",
               self.selection_fields(state, "CND-B"), "p:selection")])
        self.assertEqual("CND-B", committed_branch(state, self.c))
        self.assertEqual("CND-B", S05Embodiment().consumer_view(state).branch)
        self.assertEqual("CND-B", execution.current_selection(state))


class TestCompliantJointBesideItsOwnGroups(_OnePatch):
    """A Joint and the RigidGroups it relates, created together.

    Which is how s03 would author them: a body, its groups, and the joints
    between them are one topological statement, not four.
    """

    def test_same_patch_same_body_compliant_joint_is_accepted(self):
        state = DesignState(run_id="compliant-ok")
        self.assertEqual([], self.one_patch(state, "s03",
                                            joint_with_groups(same_body=True)))

    def test_same_patch_cross_body_compliant_joint_is_rejected(self):
        """The silent failure. The groups were not in storage when the joint was
        judged, so the invariant compared nothing and reported clean."""
        state = DesignState(run_id="compliant-bad")
        problems = self.one_patch(state, "s03", joint_with_groups(same_body=False))
        self.assertTrue(problems,
                        "a cross-body COMPLIANT joint was accepted because the "
                        "invariant could not see its own patch")
        self.assertTrue(any("compliant_joint_is_internal_to_one_body" in p
                            for p in problems), problems)

    def test_the_rejected_joint_and_its_siblings_did_not_land(self):
        """A patch is all or nothing. A rejected joint must not leave its bodies
        behind as though half the statement were true."""
        state = DesignState(run_id="compliant-bad")
        self.one_patch(state, "s03", joint_with_groups(same_body=False))
        for eid in ("BOD-1", "BOD-2", "RGP-1", "RGP-2", "JNT-1"):
            with self.subTest(entity=eid):
                self.assertFalse(state.has_entity(eid))

    def test_the_invariant_ran_rather_than_being_skipped(self):
        """Proves the accepted case above is accepted for the right reason.

        If the same-body rule silently returned clean whenever it could not
        resolve its references, the positive case would pass identically. Making
        the groups genuinely cross-body must therefore change the verdict - and
        it does, which is what distinguishes 'checked and satisfied' from 'not
        checked'.
        """
        ok = DesignState(run_id="ran-ok")
        bad = DesignState(run_id="ran-bad")
        self.assertEqual([], self.one_patch(ok, "s03", joint_with_groups(same_body=True)))
        self.assertNotEqual([], self.one_patch(bad, "s03",
                                               joint_with_groups(same_body=False)))

    def test_a_non_compliant_cross_body_joint_in_one_patch_stays_legal(self):
        """A revolute joint between two bodies is what a hinge IS."""
        state = DesignState(run_id="revolute")
        ops = joint_with_groups(same_body=False)
        ops[-1] = Op("CREATE", "Joint", "JNT-1",
                     joint("RGP-1", "RGP-2", "REVOLUTE"), "p:s03")
        self.assertEqual([], self.one_patch(state, "s03", ops))


class TestSiblingReferences(_OnePatch):
    """Reference resolution across one patch. Verified, not assumed.

    The relational invariants rely on this: if the reference layer did not
    already resolve sibling CREATEs, the same-body rule would be reporting
    dangling references rather than same-body violations.
    """

    def test_same_patch_sibling_reference_resolves(self):
        state = DesignState(run_id="sibling")
        self.assertEqual([], self.one_patch(state, "s03", [
            Op("CREATE", "Body", "BOD-1", body(), "p:s03"),
            Op("CREATE", "RigidGroup", "RGP-1", rigid_group("BOD-1"), "p:s03")]))

    def test_same_patch_missing_reference_still_fails(self):
        state = DesignState(run_id="dangling")
        problems = self.one_patch(state, "s03", [
            Op("CREATE", "Body", "BOD-1", body(), "p:s03"),
            Op("CREATE", "RigidGroup", "RGP-1", rigid_group("BOD-X"), "p:s03")])
        self.assertTrue(any("DANGLING_REF" in p for p in problems), problems)

    def test_a_sibling_reference_of_the_wrong_family_still_fails(self):
        """Resolving within the patch must not weaken the type check."""
        state = DesignState(run_id="wrongfam")
        problems = self.one_patch(state, "s03", [
            Op("CREATE", "Body", "BOD-1", body(), "p:s03"),
            Op("CREATE", "RigidGroup", "RGP-1", rigid_group("RGP-1"), "p:s03")])
        self.assertTrue(any("REFERENCE_FAMILY" in p for p in problems), problems)


class TestMultiOperationConditionalRecord(_OnePatch):
    """One patch, several operations, ONE final record judged as a whole.

    An earlier version of this class proved the point with two SUPERSEDEs of the
    same field - a malformed intermediate value repaired by a later one in the
    same patch. That fixture is no longer legal: a patch may author a canonical
    field once, so it was demonstrating final-record evaluation by way of a
    patch the contract now refuses. Different FIELDS contributing to one final
    record makes the same point without relying on a write it forbids.
    """

    def scaled(self):
        """A complete scale. Every field the tests revise already has a value,
        because SUPERSEDE displaces a prior value and refuses where there is
        none - so a fixture seeded with less would fail for that reason instead
        of the one under test.
        """
        state = DesignState(run_id="multi")
        self.add(state, "s04", "ReferenceScale", "SCL-1", basis="ABSOLUTE",
                 absolute={"unit": "mm", "per_unit": 1.0},
                 note="the basis as first measured")
        return state

    def test_two_fields_of_one_record_are_judged_together(self):
        """`basis` and `absolute` are written by separate operations, and the
        conditional rule is about their COMBINATION - an ABSOLUTE basis needs a
        structured absolute. Judged per operation, neither is wrong."""
        state = self.scaled()
        problems = self.one_patch(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1", {"note": "re-measured"},
               "p:s04", reason="the basis was re-measured"),
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm", "per_unit": 4.0}}, "p:s04",
               reason="and here is what one unit is now worth")])
        self.assertEqual([], problems,
                         "the patch was judged on fragments rather than on the "
                         "record it produces")
        record = state.standing("ReferenceScale")[0]
        self.assertEqual("re-measured", record["note"])
        self.assertEqual(4.0, record["absolute"]["per_unit"])

    def test_a_patch_whose_FINAL_record_is_broken_is_rejected(self):
        """The other direction, so the test above is not merely permissive.

        The scale factor is withdrawn while the basis stays ABSOLUTE, so the
        record the patch leaves promises a comparability it cannot deliver. The
        annotation beside it is unremarkable, and neither operation is malformed
        considered alone.
        """
        state = self.scaled()
        problems = self.one_patch(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm"}}, "p:s04",
               reason="the scale factor was withdrawn"),
            Op("SUPERSEDE", "ReferenceScale", "SCL-1", {"note": "measured"},
               "p:s04", reason="an unrelated annotation")])
        self.assertTrue(any("absolute_scale_is_structured" in p
                            for p in problems), problems)


class TestOnePatchAuthorsAFieldOnce(_OnePatch):
    """Two writes to one field inside one patch, each legal on its own.

    This is the defect the rule exists for. Two EXTENDs of `Parameter.value`
    both consulted pre-patch storage, both found the field absent, and both were
    approved - then application ran them in order and the second silently
    overwrote the first. EXTEND's own contract says it adds an ABSENT field and
    that writing over a value requires revision, so the pair contradicted the
    operation's meaning without producing a single diagnostic.
    """

    def declared(self):
        state = DesignState(run_id="fields")
        self.add(state, "s05", "Parameter", "PRM-1", symbol="r", unit="mm",
                 status="DECLARED")
        return state

    def settled(self):
        """A parameter that already carries a value, so SUPERSEDE is legal."""
        state = self.declared()
        patch = StagePatch(
            patch_id="settle", run_id=state.run_id, stage_id="s06",
            stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=[Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0},
                           "p:s06")],
            execution_status="SUCCESS", provenance={})
        self.assertEqual([], state.validate(patch))
        state.apply(patch)
        return state

    def test_the_single_write_this_is_derived_from_is_legal(self):
        """Otherwise the rejections below could be about EXTEND authority."""
        state = self.declared()
        patch = StagePatch(
            patch_id="single", run_id=state.run_id, stage_id="s06",
            stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=[Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0},
                           "p:s06")],
            execution_status="SUCCESS", provenance={})
        self.assertEqual([], state.validate(patch))

    def test_two_extends_of_same_field_in_one_patch_are_rejected(self):
        state = self.declared()
        problems = self.one_patch(state, "s06", [
            Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0}, "p:s06"),
            Op("EXTEND", "Parameter", "PRM-1", {"value": 2.0}, "p:s06")])
        self.assertTrue(any("PATCH_FIELD_CONFLICT" in p for p in problems),
                        problems)

    def test_no_silent_last_write_wins_remains(self):
        """The specific behaviour: before the rule, this left value 2.0 in state
        with nothing recording that 1.0 had been authored and discarded."""
        state = self.declared()
        self.one_patch(state, "s06", [
            Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0}, "p:s06"),
            Op("EXTEND", "Parameter", "PRM-1", {"value": 2.0}, "p:s06")])
        self.assertIsNone(state.standing("Parameter")[0].get("value"),
                          "one of two conflicting writes landed anyway")

    def test_the_conflict_names_the_field(self):
        """A reviewer must know WHICH field to state once."""
        state = self.declared()
        problems = self.one_patch(state, "s06", [
            Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0}, "p:s06"),
            Op("EXTEND", "Parameter", "PRM-1", {"value": 2.0}, "p:s06")])
        conflict = [p for p in problems if "PATCH_FIELD_CONFLICT" in p][0]
        self.assertIn("PRM-1.value", conflict)

    def test_two_supersedes_of_same_field_in_one_patch_are_rejected(self):
        state = self.settled()
        problems = self.one_patch(state, "s06", [
            Op("SUPERSEDE", "Parameter", "PRM-1", {"value": 5.0}, "p:s06",
               reason="a"),
            Op("SUPERSEDE", "Parameter", "PRM-1", {"value": 9.0}, "p:s06",
               reason="b")])
        self.assertTrue(any("PATCH_FIELD_CONFLICT" in p for p in problems),
                        problems)

    def test_extend_then_supersede_same_field_in_one_patch_is_rejected(self):
        """Already refused before the rule, but for an incidental reason -
        SUPERSEDE_ABSENT, because the value was not yet in storage. It is now
        refused for what it actually is: two writes to one field."""
        state = self.declared()
        problems = self.one_patch(state, "s06", [
            Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0}, "p:s06"),
            Op("SUPERSEDE", "Parameter", "PRM-1", {"value": 7.0}, "p:s06",
               reason="c")])
        self.assertTrue(any("PATCH_FIELD_CONFLICT" in p for p in problems),
                        problems)

    def test_two_different_fields_on_one_entity_remain_legal(self):
        """The rule must not forbid a producer stating everything it concluded."""
        state = self.declared()
        self.assertEqual([], self.one_patch(state, "s06", [
            Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0}, "p:s06"),
            Op("EXTEND", "Parameter", "PRM-1", {"solved_by": "SLV-1"},
               "p:s06")]))

    def test_the_same_field_on_two_entities_remains_legal(self):
        state = self.declared()
        self.add(state, "s05", "Parameter", "PRM-2", symbol="w", unit="mm",
                 status="DECLARED")
        self.assertEqual([], self.one_patch(state, "s06", [
            Op("EXTEND", "Parameter", "PRM-1", {"value": 1.0}, "p:s06"),
            Op("EXTEND", "Parameter", "PRM-2", {"value": 2.0}, "p:s06")]))

    def test_invalidate_authors_no_field_and_does_not_conflict(self):
        """It withdraws standing rather than writing a value."""
        state = self.settled()
        self.assertEqual([], self.one_patch(state, "s06", [
            Op("SUPERSEDE", "Parameter", "PRM-1", {"value": 5.0}, "p:s06",
               reason="revised"),
            Op("INVALIDATE", "Parameter", "PRM-1", {}, "p:s06",
               reason="and then withdrawn")]))


class TestPremiseResolutionIsOrderIndependent(_OnePatch):
    """A patch is atomic, so a premise resolves wherever its target is created.

    Resolution consulted a set that grew as the operation loop advanced, so the
    same two CREATEs passed in one order and failed in the other. Nothing in the
    architecture gives operation ORDER meaning - ordinary typed references
    already resolve against the whole patch - so this was a producer being asked
    to topologically sort its output to satisfy a validator.
    """

    def bodies(self, reverse=False):
        first = Op("CREATE", "Body", "BOD-A", body("first"), "p:s03")
        second = Op("CREATE", "Body", "BOD-B", body("second"), "p:s03",
                    premise_refs=["BOD-A"])
        return [second, first] if reverse else [first, second]

    def test_forward_sibling_premise_resolves(self):
        state = DesignState(run_id="fwd")
        self.assertEqual([], self.one_patch(state, "s03", self.bodies()))

    def test_backward_sibling_premise_resolves(self):
        """The identical patch, listed the other way round."""
        state = DesignState(run_id="bwd")
        self.assertEqual([], self.one_patch(state, "s03",
                                            self.bodies(reverse=True)))

    def test_both_orders_reach_the_same_verdict(self):
        forward = DesignState(run_id="f2")
        backward = DesignState(run_id="b2")
        self.assertEqual(self.one_patch(forward, "s03", self.bodies()),
                         self.one_patch(backward, "s03",
                                        self.bodies(reverse=True)))

    def test_the_premise_actually_landed(self):
        """Order-independence must not be achieved by dropping the premise."""
        state = DesignState(run_id="landed")
        self.one_patch(state, "s03", self.bodies(reverse=True))
        record = [r for r in state.family("Body")
                  if r["entity_id"] == "BOD-B"][0]
        self.assertIn("BOD-A", record.get("_premises") or [])

    def test_a_genuinely_missing_premise_still_fails(self):
        state = DesignState(run_id="missing")
        problems = self.one_patch(state, "s03", [
            Op("CREATE", "Body", "BOD-A", body("first"), "p:s03"),
            Op("CREATE", "Body", "BOD-B", body("second"), "p:s03",
               premise_refs=["BOD-NOWHERE"])])
        self.assertTrue(any("DANGLING_PREMISE" in p for p in problems), problems)


class TestProspectiveEqualsActual(_OnePatch):
    """The claim the whole design rests on, checked rather than asserted.

    `_Prospective` says it represents the state a patch would leave. Earlier it
    represented an APPROXIMATION of that state - its own small replay of CREATE,
    EXTEND, SUPERSEDE and INVALIDATE which deliberately skipped premise
    propagation, on the argument that omitting it could only over-count standing
    and so fail conservatively. Conservative or not, an invariant reading it was
    reasoning about a state that never happens.

    It now deep-copies the state and applies the patch with `_MUTATORS` - the
    same functions `apply` calls, in the same order, reaching the same
    `_propagate` with the same skip set. Equivalence is therefore structural,
    and these tests exist to notice if that ever stops being true.
    """

    def _predict_then_apply(self, state, stage, ops):
        """Prospective view first, then the real apply. Same patch, both."""
        from ver3.assy_v3.state.design_state import _Prospective
        patch = StagePatch(
            patch_id="equiv-%d" % len(state.applied_patches),
            run_id=state.run_id, stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS", provenance={"purpose": "equivalence"})
        self.assertEqual([], state.validate(patch),
                         "the equivalence fixture was rejected")
        predicted = _Prospective(state, patch)
        self.assertTrue(predicted.usable)
        snapshot = {fam: {r["entity_id"]: r.get("_validity", "STANDING")
                          for r in predicted.family(fam)}
                    for fam in ("Body", "Parameter", "ReferenceScale")}
        state.apply(patch)
        actual = {fam: {r["entity_id"]: r.get("_validity", "STANDING")
                        for r in state.family(fam)}
                  for fam in ("Body", "Parameter", "ReferenceScale")}
        return snapshot, actual

    def chain(self):
        """A premise and something that rests on it, in separate patches."""
        state = DesignState(run_id="lifecycle")
        self.add(state, "s04", "ReferenceScale", "SCL-1", basis="ABSOLUTE",
                 absolute={"unit": "mm", "per_unit": 1.0})
        self.add(state, "s03", "Body", "BOD-DEP", ["SCL-1"],
                 **body("dependent"))
        self.add(state, "s03", "Body", "BOD-FREE", **body("independent"))
        return state

    def test_the_chain_starts_standing(self):
        state = self.chain()
        for eid in ("BOD-DEP", "BOD-FREE"):
            with self.subTest(entity=eid):
                self.assertIn(eid, [r["entity_id"]
                                    for r in state.standing("Body")])

    def test_invalidating_a_premise_predicts_exactly_what_apply_does(self):
        state = self.chain()
        predicted, actual = self._predict_then_apply(state, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-1", {}, "p:s04",
               reason="the basis was withdrawn")])
        self.assertEqual(actual, predicted,
                         "the prospective view disagreed with the state the "
                         "patch actually produced")

    def test_the_dependent_actually_lost_standing(self):
        """Otherwise the equivalence above could be equality of two no-ops."""
        state = self.chain()
        predicted, actual = self._predict_then_apply(state, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-1", {}, "p:s04",
               reason="the basis was withdrawn")])
        self.assertNotEqual("STANDING", actual["Body"]["BOD-DEP"])
        self.assertEqual(actual["Body"]["BOD-DEP"],
                         predicted["Body"]["BOD-DEP"])

    def test_superseding_a_premise_predicts_exactly_what_apply_does(self):
        state = self.chain()
        predicted, actual = self._predict_then_apply(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm", "per_unit": 2.0}}, "p:s04",
               reason="the basis was re-measured")])
        self.assertEqual(actual, predicted)
        self.assertNotEqual("STANDING", actual["Body"]["BOD-DEP"],
                            "superseding a premise left its dependent standing, "
                            "so this test proves nothing about propagation")

    def test_the_independent_body_stays_standing_in_both(self):
        """Dependency-LOCAL. A rule that stales everything is no rule."""
        state = self.chain()
        predicted, actual = self._predict_then_apply(state, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-1", {}, "p:s04",
               reason="withdrawn")])
        self.assertEqual("STANDING", actual["Body"]["BOD-FREE"])
        self.assertEqual("STANDING", predicted["Body"]["BOD-FREE"])

    def test_a_patch_own_creation_is_not_staled_by_its_own_change(self):
        """`skip` semantics: a patch co-authors its outputs and must not
        invalidate its own work in the act of doing it.

        The new scale is premised on the very body this patch stales, and must
        still stand. Reached through the real mutators, so the rule holds here
        without being restated - which is the point of not reimplementing them.

        A patch carries ONE stage_id, so the created entity is an s04 family:
        s04 may not create a Body, and using one would fail for ownership before
        this property was reached.
        """
        state = self.chain()
        predicted, actual = self._predict_then_apply(state, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-1", {}, "p:s04",
               reason="withdrawn"),
            Op("CREATE", "ReferenceScale", "SCL-2", {"basis": "RELATIVE"},
               "p:s04", premise_refs=["BOD-DEP"])])
        self.assertEqual("STANDING", actual["ReferenceScale"]["SCL-2"])
        self.assertEqual("STANDING", predicted["ReferenceScale"]["SCL-2"])

    def test_create_extend_and_field_results_match(self):
        """Not only validity: the FIELDS the patch leaves."""
        from ver3.assy_v3.state.design_state import _Prospective
        state = DesignState(run_id="fields-equiv")
        self.add(state, "s05", "Parameter", "PRM-1", symbol="r", unit="mm",
                 status="DECLARED")
        patch = StagePatch(
            patch_id="fe", run_id=state.run_id, stage_id="s06", stage_attempt=1,
            parent_state_hash=state.state_hash(),
            operations=[Op("EXTEND", "Parameter", "PRM-1", {"value": 3.0},
                           "p:s06")],
            execution_status="SUCCESS", provenance={})
        self.assertEqual([], state.validate(patch))
        predicted = _Prospective(state, patch).record_after_patch("PRM-1")
        state.apply(patch)
        actual = {k: v for k, v in state.entities["PRM-1"].items()
                  if not k.startswith("_")}
        self.assertEqual(actual, predicted)
        self.assertEqual(3.0, actual["value"])


class TestSelectionCardinalityUsesExactStanding(_OnePatch):
    """Cardinality counts the FINAL standing set, including propagation.

    Now that the prospective view runs real propagation, a decision that stops
    standing for any canonical reason - not only explicit INVALIDATE - is no
    longer counted against the limit.
    """

    def test_a_decision_staled_by_its_own_premise_does_not_block_a_new_one(self):
        """Staling and recording cannot share a patch, and that is not a gap.

        A StagePatch carries ONE stage_id, and s04 may not create a
        SelectionDecision - so "withdraw the premise and record a new decision
        atomically" is not an expressible patch, by ownership rather than by
        oversight. The reachable form is two patches, and the property under
        test survives it: cardinality counts what STANDS, so a decision staled
        by its premise does not block a successor even though its record is
        still there.
        """
        state = self.branched()
        self.add(state, "s04", "ReferenceScale", "SCL-1", basis="RELATIVE")
        self.add(state, "selection", "SelectionDecision", "SEL-A", ["SCL-1"],
                 selected_candidate="CND-A")
        self.assertEqual(["SEL-A"],
                         [r["entity_id"]
                          for r in state.standing("SelectionDecision")])

        # s04 withdraws the basis the decision rested on.
        withdraw = StagePatch(
            patch_id="withdraw", run_id=state.run_id, stage_id="s04",
            stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=[Op("INVALIDATE", "ReferenceScale", "SCL-1", {},
                           "p:s04", reason="the basis was withdrawn")],
            execution_status="SUCCESS", provenance={})
        self.assertEqual([], state.validate(withdraw))
        state.apply(withdraw)
        self.assertEqual([], list(state.standing("SelectionDecision")),
                         "the decision still stands, so the rest of this test "
                         "would not be about a staled one")
        self.assertTrue(state.has_entity("SEL-A"), "history was erased")

        # A new decision is now free to be recorded.
        record = StagePatch(
            patch_id="record", run_id=state.run_id, stage_id="selection",
            stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=[Op("CREATE", "SelectionDecision", "SEL-B",
                           self.selection_fields(state, "CND-B"),
                           "p:selection")],
            execution_status="SUCCESS", provenance={})
        problems = state.validate(record)
        self.assertEqual([], problems,
                         "the new decision was counted against one that no "
                         "longer stands: %s" % problems)
        state.apply(record)
        self.assertEqual(["SEL-B"],
                         [r["entity_id"]
                          for r in state.standing("SelectionDecision")])
        self.assertEqual("CND-B", committed_branch(state, self.c))


class TestRelationalInvariantsDoNotReadRawStorage(unittest.TestCase):
    """§11. No invariant may depend on WHEN an entity was created.

    A behavioural guard rather than a source-code one where possible: the
    same-body rule is exercised with its groups created in an earlier patch and
    again with them created in the same patch, and must reach the same verdict.
    If it read raw storage the second case would pass while the first failed.
    """

    def test_the_verdict_is_the_same_whichever_patch_created_the_groups(self):
        builder = _OnePatch("run_placeholder")
        builder.setUpClass()

        # A: groups created by EARLIER patches, joint added afterwards.
        earlier = DesignState(run_id="earlier")
        builder.add(earlier, "s03", "Body", "BOD-1", **body())
        builder.add(earlier, "s03", "Body", "BOD-2", **body("lid", "cover"))
        builder.add(earlier, "s03", "RigidGroup", "RGP-1", **rigid_group("BOD-1"))
        builder.add(earlier, "s03", "RigidGroup", "RGP-2", **rigid_group("BOD-2"))
        historical = earlier.validate(StagePatch(
            patch_id="late-joint", run_id="earlier", stage_id="s03",
            stage_attempt=1, parent_state_hash=earlier.state_hash(),
            operations=[Op("CREATE", "Joint", "JNT-1",
                           joint("RGP-1", "RGP-2"), "p:s03")],
            execution_status="SUCCESS", provenance={}))

        # B: the identical joint, groups created in the SAME patch.
        together = DesignState(run_id="together")
        sibling = together.validate(StagePatch(
            patch_id="all-at-once", run_id="together", stage_id="s03",
            stage_attempt=1, parent_state_hash=together.state_hash(),
            operations=joint_with_groups(same_body=False),
            execution_status="SUCCESS", provenance={}))

        rule = "compliant_joint_is_internal_to_one_body"
        self.assertTrue(any(rule in p for p in historical),
                        "the historical case did not even fire: %s" % historical)
        self.assertTrue(any(rule in p for p in sibling),
                        "the same violation went unreported when the groups "
                        "were created in the same patch: %s" % sibling)

    def test_no_relational_implementation_reads_the_store_directly(self):
        """The architectural half. `_STORAGE` in a rule means it can see the
        past but not the patch, which is exactly the defect this file pins."""
        import inspect
        from ver3.assy_v3.state import design_state as ds
        for name, fn in sorted(ds.RELATIONAL_INVARIANTS.items()):
            with self.subTest(rule=name):
                source = inspect.getsource(fn)
                self.assertNotIn("_STORAGE", source,
                                 "%s reads the live store; it must read the "
                                 "prospective patch view" % name)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()


class TestCoreSuitesAreInvokedByCI(unittest.TestCase):
    """A core test package outside CI reports nothing until someone runs it.

    `ver3/tests/state` was not in the boundaries workflow. Two of its tests had
    been failing across three consecutive GREEN runs, both broken by repairs to
    the very layer they cover - SUPERSEDE authority and the ReferenceScale
    conditional rule - and nothing said so. The suites existed, passed review,
    and were simply never executed.

    Deliberately NOT a snapshot of the workflow file: that would fail on every
    unrelated edit and teach people to update it without reading it. It asserts
    one property - the dependency-free core packages are invoked - and says
    which, so adding a third core package is a deliberate act rather than an
    omission nobody notices.
    """

    #: Packages that must run in the stdlib boundaries job. Both are
    #: kernel-free; anything needing OpenCascade belongs to ver3/tests/kernel
    #: and the downstream job.
    CORE_SUITES = ("ver3/tests/meta", "ver3/tests/state")

    @classmethod
    def setUpClass(cls):
        import os
        import yaml
        from . import _paths
        path = os.path.join(_paths.REPO_ROOT, ".github", "workflows",
                            "ver3-boundaries.yml")
        with open(path) as handle:
            cls.workflow = yaml.safe_load(handle)
        # PARSED, not sliced. Splitting the file text on "downstream:" put the
        # comment block that introduces that job into the boundaries half, so
        # the kernel-absence check read a sentence explaining why the kernel
        # lives elsewhere and failed on it.
        cls.boundaries = cls.workflow["jobs"]["boundaries"]["steps"]
        cls.commands = "\n".join(str(step.get("run") or "")
                                  for step in cls.boundaries)

    def test_the_workflow_was_actually_read(self):
        """Otherwise every assertion below is about an empty string."""
        self.assertIn("downstream", self.workflow["jobs"])
        self.assertTrue(self.commands.strip())

    def test_every_core_suite_is_invoked_by_the_boundaries_job(self):
        for suite in self.CORE_SUITES:
            with self.subTest(suite=suite):
                self.assertIn("discover -s %s" % suite, self.commands,
                              "%s is not run by the boundaries job; a core "
                              "package outside CI can regress through any "
                              "number of green runs" % suite)

    def test_the_boundaries_job_installs_no_cad_kernel(self):
        """The separation the downstream job exists for. Installing OpenCascade
        here to make a suite pass would erase it."""
        self.assertNotIn("cadquery", self.commands)
        self.assertNotIn("OCP", self.commands)

    def test_the_core_suites_exist_and_are_kernel_free(self):
        """A named suite that is empty, missing, or kernel-dependent would make
        the invocation above meaningless."""
        import os
        from . import _paths
        for suite in self.CORE_SUITES:
            with self.subTest(suite=suite):
                directory = os.path.join(_paths.REPO_ROOT, *suite.split("/"))
                self.assertTrue(os.path.isdir(directory))
                files = [f for f in os.listdir(directory)
                         if f.startswith("test_") and f.endswith(".py")]
                self.assertTrue(files, "%s contains no tests" % suite)
                for name in files:
                    with self.subTest(module=name):
                        self.assertFalse(
                            self._imports_kernel(os.path.join(directory, name)),
                            "%s/%s imports a CAD kernel and cannot run in the "
                            "stdlib job" % (suite, name))

    @staticmethod
    def _imports_kernel(path):
        """Real IMPORT statements, not a substring scan.

        A text search finds this guard's own message and fails on the
        explanation rather than on a violation - which makes a test that cannot
        pass rather than one that catches anything.
        """
        import ast
        with open(path) as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name.split(".")[0] == "OCP" for a in node.names):
                    return True
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "OCP":
                    return True
        return False
