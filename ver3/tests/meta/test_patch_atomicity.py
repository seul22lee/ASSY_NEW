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
    """One entity, two legal mutations, one final record.

    The conditional rule must judge what the patch LEAVES, not each fragment.
    A SUPERSEDE that breaks a rule and a later one that repairs it end in a
    valid record; judged separately, the first would reject a patch whose result
    is fine.
    """

    def scaled(self):
        state = DesignState(run_id="multi")
        self.add(state, "s04", "ReferenceScale", "SCL-1", basis="ABSOLUTE",
                 absolute={"unit": "mm", "per_unit": 1.0})
        return state

    def test_multi_operation_conditional_record_is_validated_as_final_record(self):
        """Two revisions in one patch; the FINAL record is well formed."""
        state = self.scaled()
        problems = self.one_patch(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm"}}, "p:s04", reason="partial"),
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm", "per_unit": 4.0}}, "p:s04",
               reason="completed in the same patch")])
        self.assertEqual([], problems,
                         "the patch was judged on an intermediate fragment "
                         "rather than on the record it produces")
        self.assertEqual(4.0,
                         state.standing("ReferenceScale")[0]["absolute"]["per_unit"])

    def test_a_multi_operation_patch_whose_FINAL_record_is_broken_is_rejected(self):
        """The other direction, so the test above is not merely permissive."""
        state = self.scaled()
        problems = self.one_patch(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm", "per_unit": 4.0}}, "p:s04",
               reason="fine so far"),
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm"}}, "p:s04",
               reason="and then broken in the same patch")])
        self.assertTrue(any("absolute_scale_is_structured" in p
                            for p in problems), problems)


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
