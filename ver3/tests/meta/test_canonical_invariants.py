"""Canonical invariants hold over the RESULTING record, not over the write event.

Three properties, and one shared idea behind them: a rule about the design is a
rule about what the design IS, not about how a particular field arrived.

PROSPECTIVE RECORDS. Conditional requirements were validated against `op.fields`
in the CREATE path. That proves an invalid record cannot be born; it does not
prove one cannot be produced. A SUPERSEDE carrying a single field is always
well-formed on its own and can still leave a record that violates a rule about
the whole of it, and until now it did.

RELATIONAL INVARIANTS. Some canonical rules cannot be expressed as facts about
one record: "these two groups belong to the same body" and "at most one of these
may stand" both need other entities. Both were prose. The compliant-joint rule
had been prose since D-2, and a cross-body joint wearing the label became
standing state - which S05-C1 then read as grounds for omitting geometry.

SELECTION UNIQUENESS. Two standing SelectionDecisions were reachable through
ordinary legal writes, and `committed_branch` returned whichever the iteration
reached first. s05, s06 and s07 all followed that answer. Nothing recorded that
a second, contradictory decision existed - and the artifact at the end of it
looks exactly as authoritative as a correct one.
"""

import unittest

from . import _fixtures, _paths

from ver3.assy_v3.state.design_state import (Contracts, ContractError,
                                             DesignState,
                                             RELATIONAL_INVARIANTS)
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.view import AmbiguousSelection, committed_branch


class _Writes(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def write(self, state, stage, ops):
        """Returns the validation problems; applies only when there are none."""
        patch = StagePatch(
            patch_id="p-%d" % len(state.applied_patches), run_id=state.run_id,
            stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS", provenance={"purpose": "invariant test"})
        problems = state.validate(patch)
        if not problems:
            state.apply(patch)
        return problems


# ======================================================================
# The mechanism itself
# ======================================================================

class TestDeclarationAndRuntimeAgree(unittest.TestCase):
    """Neither an invariant that is only prose, nor code nothing declares."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.declared = {}
        for family in sorted(cls.c.families):
            for rule in cls.c.relational_invariants(family):
                cls.declared.setdefault(rule.get("rule"), []).append(family)

    def test_there_are_declared_invariants(self):
        """Otherwise both directions below are vacuously satisfied."""
        self.assertTrue(self.declared)

    def test_every_declared_invariant_has_an_implementation(self):
        for rule, families in sorted(self.declared.items()):
            with self.subTest(rule=rule, families=families):
                self.assertIn(rule, RELATIONAL_INVARIANTS,
                              "%s is declared by %s and implemented nowhere; "
                              "the contract asserts a rule the runtime cannot "
                              "keep" % (rule, families))

    def test_every_implementation_is_declared_by_something(self):
        for rule in sorted(RELATIONAL_INVARIANTS):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.declared,
                              "%s is implemented and no family declares it, so "
                              "it runs against nothing" % rule)

    def test_every_declared_invariant_says_why(self):
        for family in sorted(self.c.families):
            for rule in self.c.relational_invariants(family):
                with self.subTest(family=family, rule=rule.get("name")):
                    self.assertTrue(rule.get("name"))
                    self.assertTrue((rule.get("why") or "").strip(),
                                    "an invariant that rejects a write must say "
                                    "what it protects")

    def test_an_undeclared_rule_name_fails_closed(self):
        """A declaration naming no implementation must REJECT the write.

        The dangerous alternative is silence: a contract asserting a rule while
        the runtime skips it is the exact drift this whole mechanism exists to
        prevent, and it would look identical to the rule passing.

        Driven through a stub contract rather than by editing the canonical one,
        so the check does not depend on a broken declaration existing on disk.
        """
        from ver3.assy_v3.state import design_state as ds

        class _StateWithABrokenDeclaration:
            class c:                                        # noqa: N801
                @staticmethod
                def relational_invariants(_family):
                    return [{"name": "invented", "rule": "no_such_rule",
                             "why": "declared and never implemented"}]

        problems = ds._relational_problems(                 # noqa: SLF001
            _StateWithABrokenDeclaration(), "Body", "BOD-1", {}, None, None)
        self.assertTrue(any("RELATIONAL_UNIMPLEMENTED" in p for p in problems),
                        problems)


# ======================================================================
# Prospective records
# ======================================================================

class TestConditionalRulesHoldAfterMutation(_Writes):
    """The invariant belongs to the record, not to CREATE."""

    def scale(self, state):
        problems = self.write(state, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-1",
               {"basis": "ABSOLUTE", "absolute": {"unit": "mm", "per_unit": 1.0}},
               "p:s04")])
        self.assertEqual([], problems, "the fixture itself was rejected")
        return state

    def test_the_starting_record_is_valid(self):
        """Otherwise the mutations below start from something already broken."""
        state = self.scale(DesignState("prospective"))
        self.assertEqual(1, len(state.standing("ReferenceScale")))

    def test_a_revision_that_preserves_validity_is_accepted(self):
        state = self.scale(DesignState("prospective"))
        self.assertEqual([], self.write(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm", "per_unit": 2.0}}, "p:s04",
               reason="the basis was re-measured")]))

    def test_a_revision_that_breaks_the_conditional_rule_is_REJECTED(self):
        """The defect this closes. The operation carries one well-formed field;
        the record it would leave behind is a scale that cannot convert."""
        state = self.scale(DesignState("prospective"))
        problems = self.write(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm"}}, "p:s04", reason="revise")])
        self.assertTrue(problems, "a revision produced an unusable scale")
        self.assertTrue(any("absolute_scale_is_structured" in p for p in problems),
                        problems)

    def test_the_rejected_revision_did_not_land(self):
        state = self.scale(DesignState("prospective"))
        self.write(state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm"}}, "p:s04", reason="revise")])
        record = state.standing("ReferenceScale")[0]
        self.assertEqual(1.0, record["absolute"]["per_unit"])

    def test_invalidate_does_not_revalidate_the_withdrawn_shape(self):
        """Withdrawing standing is a lifecycle act, not a field change. A record
        must stay retirable after the rules around it move."""
        state = self.scale(DesignState("prospective"))
        self.assertEqual([], self.write(state, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-1", {}, "p:s04",
               reason="the basis was withdrawn")]))
        self.assertEqual([], list(state.standing("ReferenceScale")))

    def test_authority_is_still_checked_before_shape(self):
        """An unauthorised write must be rejected for being unauthorised. Adding
        'and it would also be malformed' invites making it well-formed rather
        than authorised."""
        state = self.scale(DesignState("prospective"))
        problems = self.write(state, "s05", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1",
               {"absolute": {"unit": "mm"}}, "p:s05", reason="not mine to revise")])
        self.assertTrue(problems)
        self.assertTrue(any("SUPERSEDE" in p and "s05" in p for p in problems),
                        problems)
        self.assertFalse(any("absolute_scale_is_structured" in p
                             for p in problems),
                         "shape was reported for a write that was never allowed")


# ======================================================================
# COMPLIANT joints
# ======================================================================

class TestCompliantJointIsInternalToOneBody(_Writes):

    VARIANT = {"mode": "BENDING", "direction": "z", "required_travel": 1.0,
               "allowable_travel": 2.0, "actuation": "PRESCRIBED_KINEMATIC",
               "compliant_element": "the cantilever arm",
               "root_interface": "IFC-0001", "activation_window": "0..1"}

    def groups(self, *, same_body):
        """Two rigid groups, on one body or on two. Contract-valid throughout."""
        state = DesignState("compliant")
        self.add(state, "s03", "Body", "BOD-1", instance_identity="shell",
                 role="shell", created_by_stage="s03")
        self.add(state, "s03", "RigidGroup", "RGP-1", body="BOD-1")
        if same_body:
            self.add(state, "s03", "RigidGroup", "RGP-2", body="BOD-1")
        else:
            self.add(state, "s03", "Body", "BOD-2", instance_identity="lid",
                     role="cover", created_by_stage="s03")
            self.add(state, "s03", "RigidGroup", "RGP-2", body="BOD-2")
        return state

    def joint(self, jtype="COMPLIANT", **over):
        fields = {"joint_type": jtype, "parent_group": "RGP-1",
                  "child_group": "RGP-2", "dof": ["RZ"],
                  "axis_direction": "+Z", "frame_ids": ["FRM-1"]}
        if jtype.upper() == "COMPLIANT":
            fields.update(self.VARIANT)
        fields.update(over)
        return Op("CREATE", "Joint", "JNT-1", fields, "p:s03")

    def test_the_fixture_really_places_the_groups_where_it_says(self):
        """Both cases below turn on this, so it is asserted rather than assumed."""
        same = self.groups(same_body=True)
        bodies = {g["entity_id"]: g["body"] for g in same.standing("RigidGroup")}
        self.assertEqual({"RGP-1": "BOD-1", "RGP-2": "BOD-1"}, bodies)
        split = self.groups(same_body=False)
        bodies = {g["entity_id"]: g["body"] for g in split.standing("RigidGroup")}
        self.assertEqual({"RGP-1": "BOD-1", "RGP-2": "BOD-2"}, bodies)

    def test_a_compliant_joint_within_one_body_is_accepted(self):
        state = self.groups(same_body=True)
        self.assertEqual([], self.write(state, "s03", [self.joint()]))

    def test_a_compliant_joint_across_two_bodies_is_REJECTED_at_the_boundary(self):
        """Not merely reported later by S05-C1: refused entry to state."""
        state = self.groups(same_body=False)
        problems = self.write(state, "s03", [self.joint()])
        self.assertTrue(problems, "a cross-body COMPLIANT joint became state")
        self.assertTrue(any("compliant_joint_is_internal_to_one_body" in p
                            for p in problems), problems)

    def test_the_rejected_joint_is_not_in_state(self):
        state = self.groups(same_body=False)
        self.write(state, "s03", [self.joint()])
        self.assertFalse(state.has_entity("JNT-1"))

    def test_an_ordinary_cross_body_joint_remains_legal(self):
        """Only COMPLIANT carries the intra-body requirement. A revolute joint
        between two bodies is what a hinge IS."""
        state = self.groups(same_body=False)
        self.assertEqual([], self.write(state, "s03", [self.joint("REVOLUTE")]))

    def test_the_variant_fields_are_still_required_too(self):
        """The relational invariant did not replace the conditional one."""
        state = self.groups(same_body=True)
        problems = self.write(state, "s03", [
            Op("CREATE", "Joint", "JNT-1",
               {"joint_type": "COMPLIANT", "parent_group": "RGP-1",
                "child_group": "RGP-2", "dof": ["RZ"], "axis_direction": "+Z",
                "frame_ids": ["FRM-1"]}, "p:s03")])
        self.assertTrue(any("compliant_joint_variant" in p for p in problems),
                        problems)


# ======================================================================
# Selection uniqueness
# ======================================================================

class TestExactlyOneSelectionMaySpeakForTheDesign(_Writes):

    def branched(self):
        state = DesignState("selection")
        self.add(state, "s02", "Candidate", "CND-A", principle="a hinged cover")
        self.add(state, "s02", "Candidate", "CND-B", principle="a sliding lid")
        return state

    def decide(self, state, eid, candidate):
        """A contract-valid SelectionDecision, referents and all.

        Built through the fixture's own field resolver rather than by writing
        referent ids by hand: a decision naming a SelectionProfile that does not
        exist is rejected for dangling references, and the test would then be
        passing for a reason that has nothing to do with uniqueness.
        """
        fields = self._fields_for(state, self.c, "selection", "SelectionDecision",
                                  {"selected_candidate": candidate})
        return self.write(state, "selection", [
            Op("CREATE", "SelectionDecision", eid, fields, "p:selection")])

    def test_zero_decisions_means_no_committed_branch(self):
        self.assertIsNone(committed_branch(self.branched(), self.c))

    def test_one_decision_gives_exactly_its_candidate(self):
        state = self.branched()
        self.assertEqual([], self.decide(state, "SEL-A", "CND-A"))
        self.assertEqual("CND-A", committed_branch(state, self.c))

    def test_a_second_standing_decision_is_REJECTED(self):
        """The falsification that motivated this. Before the invariant, both
        writes succeeded and the design carried two contradictory commitments."""
        state = self.branched()
        self.assertEqual([], self.decide(state, "SEL-A", "CND-A"))
        problems = self.decide(state, "SEL-B", "CND-B")
        self.assertTrue(problems, "two SelectionDecisions now stand")
        self.assertTrue(any("one_standing_selection" in p for p in problems),
                        problems)

    def test_only_the_first_decision_stands(self):
        state = self.branched()
        self.decide(state, "SEL-A", "CND-A")
        self.decide(state, "SEL-B", "CND-B")
        self.assertEqual(["SEL-A"],
                         [r["entity_id"] for r in state.standing("SelectionDecision")])
        self.assertEqual("CND-A", committed_branch(state, self.c))

    def test_changing_the_choice_has_a_canonical_path_that_keeps_history(self):
        """Refusing a second decision must not make the design unable to change
        its mind. Withdrawing the standing one and recording a new one works,
        and the withdrawn record remains readable."""
        state = self.branched()
        self.decide(state, "SEL-A", "CND-A")
        self.assertEqual([], self.write(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-A", {}, "p:selection",
               reason="the choice was reopened")]))
        self.assertEqual([], self.decide(state, "SEL-B", "CND-B"))
        self.assertEqual("CND-B", committed_branch(state, self.c))
        self.assertTrue(state.has_entity("SEL-A"),
                        "the superseded decision was erased rather than retired")

    def test_revising_the_standing_decision_also_works(self):
        """The other canonical path: SUPERSEDE the decision in place."""
        state = self.branched()
        self.decide(state, "SEL-A", "CND-A")
        self.assertEqual([], self.write(state, "selection", [
            Op("SUPERSEDE", "SelectionDecision", "SEL-A",
               {"selected_candidate": "CND-B"}, "p:selection",
               reason="review changed the choice")]))
        self.assertEqual("CND-B", committed_branch(state, self.c))

    def test_ambiguity_fails_closed_if_it_is_ever_reached(self):
        """Defence in depth. The write boundary refuses to produce this state;
        if some path ever does, choosing between two commitments is a selection,
        and selection is a human authority no resolver may exercise."""
        state = self.branched()
        self.decide(state, "SEL-A", "CND-A")

        class _TwoStanding:
            """The same state with one extra standing decision, and nothing else
            changed - so the failure below is about ambiguity alone."""

            def __init__(self, real):
                self._real = real

            def standing(self, family):
                rows = list(self._real.standing(family))
                if family == "SelectionDecision":
                    rows.append({"entity_id": "SEL-B",
                                 "selected_candidate": "CND-B"})
                return rows

            def __getattr__(self, name):
                return getattr(self._real, name)

        with self.assertRaises(AmbiguousSelection) as raised:
            committed_branch(_TwoStanding(state), self.c)
        self.assertIn("SEL-A", str(raised.exception))
        self.assertIn("SEL-B", str(raised.exception))


class TestEveryStageInheritsTheSameSelectionAuthority(_Writes):
    """s05, s06 and s07 must not be able to disagree about which design it is."""

    def selected(self):
        state = DesignState("authority")
        self.add(state, "s02", "Candidate", "CND-A", principle="a hinged cover")
        self.add(state, "s02", "Candidate", "CND-B", principle="a sliding lid")
        self.add(state, "selection", "SelectionDecision", "SEL-A",
                 selected_candidate="CND-A")
        return state

    def test_the_view_and_the_downstream_resolver_agree(self):
        from ver3.assy_v3.downstream import execution
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
        state = self.selected()
        branch = committed_branch(state, self.c)
        self.assertEqual(branch, S05Embodiment().consumer_view(state).branch)
        self.assertEqual(branch, execution.current_selection(state))

    def test_all_three_lose_the_branch_together(self):
        from ver3.assy_v3.downstream import execution
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
        state = self.selected()
        self.write(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-A", {}, "p:selection",
               reason="reopened")])
        self.assertIsNone(committed_branch(state, self.c))
        self.assertNotEqual("VIEW_READY",
                            S05Embodiment().consumer_view(state).status.value)
        with self.assertRaises(execution.NoStandingSelection):
            execution.current_selection(state)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
