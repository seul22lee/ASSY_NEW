"""A human choice, carried all the way to a solid, and then withdrawn again.

The whole seam in one place:

    standing SelectionDecision
      -> recorded s05 ConsumerView
      -> S05.invoke() with a deterministic provider
      -> committed DesignState
      -> settle_current_selection   (s06)
      -> compile_current_selection  (s07)
      -> OpenCascade geometry

The fixture is imported from ver3/tests/meta/test_selection_to_embodiment_seam.py
rather than rebuilt, so the kernel-free half and this half cannot drift into
proving things about two different designs.

The second class is the one that matters most. Producing geometry from a choice
is worth little if the geometry keeps looking authoritative after the choice is
withdrawn - that is precisely the state in which someone builds the wrong thing.
So the choice is reopened and the geometry must STOP standing; and separately an
unrelated candidate is revised and the geometry must KEEP standing, because a
currentness rule that stales everything is as useless as one that stales nothing.
"""

import unittest

from ver3.assy_v3.downstream import execution
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.tests.meta.test_selection_to_embodiment_seam import SeamFixture


class _Built(SeamFixture):

    def build(self, selected="CND-A"):
        state = self.selected_design(selected)
        outcome = self.embody(state)
        progression = Progression()
        report, _ = execution.settle_current_selection(state, progression)
        result, _ = execution.compile_current_selection(state, progression)
        return state, outcome, report, result

    def _commit(self, state, stage, ops):
        patch = StagePatch(
            patch_id="%s-%d" % (stage, len(state.applied_patches)),
            run_id=state.run_id, stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS", provenance={"purpose": "lifecycle"})
        problems = state.validate(patch)
        self.assertEqual([], problems, "lifecycle step rejected: %s" % problems)
        state.apply(patch)


class TestTheChoiceReachesGeometry(_Built):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.state, self.outcome, self.report, self.result = self.build()

    def test_the_settlement_settled_the_selected_system(self):
        self.assertEqual("feasible", self.report.solver_status,
                         self.report.problems)
        # boss_r = pin_r + wall, solved as a coupled system.
        self.assertAlmostEqual(6.0, self.report.settled["PRM-0003"], places=9)

    def test_real_geometry_was_produced(self):
        self.assertTrue(self.result.ok, self.result.problems)
        self.assertEqual(["BOD-0001"], [b.body_id for b in self.result.bodies])
        self.assertGreater(self.result.bodies[0].volume, 0)

    def test_the_bore_actually_removed_material(self):
        """Otherwise 'it compiled' is true of a solid block, and the feature the
        realization cites would have discharged its obligation with nothing."""
        box = 40.0 * 30.0 * 20.0
        self.assertLess(self.result.bodies[0].volume, box)

    def test_the_signature_traces_back_to_the_authored_statement(self):
        mapped = {}
        for body in self.result.bodies:
            mapped.update({fid: body.body_id for fid in (body.feature_map or {})})
        self.assertEqual("BOD-0001", mapped.get("FEA-0002"))

    def test_the_geometry_signature_is_committed_and_standing(self):
        signatures = self.state.standing("GeometrySignature")
        self.assertEqual(1, len(signatures))

    def test_the_deterministic_records_carry_no_model_provenance(self):
        """s06 and s07 are deterministic. A provider id on either would be a
        claim that a model decided a dimension or a solid.

        Checked on the EXECUTION RECORD rather than the patch: `DeterministicExecution`
        is a separate type from `StageExecution` precisely so that
        `response_source` and `provider_id` do not exist on it, and asserting
        their absence is asserting that separation held.
        """
        progression = Progression()
        state = self.selected_design()
        self.embody(state)
        execution.settle_current_selection(state, progression)
        execution.compile_current_selection(state, progression)
        runs = progression.deterministic
        self.assertTrue(runs, "no deterministic execution was recorded")
        for run in runs:
            with self.subTest(responsibility=run.responsibility_id):
                record = run.as_record()
                self.assertNotIn("response_source", record)
                self.assertNotIn("provider_id", record)

    def test_nothing_from_the_other_branch_was_built(self):
        self.assertNotIn("BOD-0002",
                         [b.body_id for b in self.result.bodies])


class TestWithdrawingTheChoiceStalesWhatRestedOnIt(_Built):
    """§13.2. The property that makes the premise stamping worth having."""

    def setUp(self):
        self.state, _o, _r, self.result = self.build()

    def _standing_ids(self, family):
        return {r["entity_id"] for r in self.state.standing(family)}

    def test_before_withdrawal_everything_stands(self):
        """The baseline. Without it, 'nothing stands afterwards' could be true
        because nothing stood in the first place."""
        for family in ("Feature", "Parameter",
                       "GeometrySignature"):
            with self.subTest(family=family):
                self.assertTrue(self._standing_ids(family))

    def test_reopening_the_selection_withdraws_the_embodiment(self):
        self._commit(self.state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-0001", {},
               "selection:reopened", reason="the choice was reopened")])
        for family in ("Feature", "Realization", "Parameter", "Constraint"):
            with self.subTest(family=family):
                self.assertEqual(set(), self._standing_ids(family),
                                 "%s still stands after the choice it embodies "
                                 "was withdrawn" % family)

    def test_reopening_the_selection_withdraws_the_geometry_too(self):
        """Transitively. The signature never referenced the decision directly;
        it rests on the statements and settled values, which rest on the choice."""
        self._commit(self.state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-0001", {},
               "selection:reopened", reason="the choice was reopened")])
        self.assertEqual(set(), self._standing_ids("GeometrySignature"),
                         "the compiled geometry still stands after the design "
                         "it is geometry FOR was unchosen")

    def test_the_records_still_exist_after_withdrawal(self):
        """Standing was withdrawn, not history. What was built and why remains
        readable; it simply no longer speaks for the design."""
        self._commit(self.state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-0001", {},
               "selection:reopened", reason="the choice was reopened")])
        self.assertTrue(self.state.has_entity("FEA-0001"))
        self.assertTrue(self.state.family("GeometrySignature"))


class TestAnUnrelatedBranchDoesNotStaleTheSelection(_Built):
    """Dependency-local, not global. A rule that stales everything is no rule."""

    def test_revising_the_other_candidate_leaves_the_geometry_standing(self):
        state, _o, _r, _result = self.build()
        self.assertTrue(state.standing("GeometrySignature"))
        # The unselected alternative's body is withdrawn. It shares no premise
        # with the selected branch's geometry, so nothing here depends on it.
        self._commit(state, "s03", [
            Op("INVALIDATE", "Body", "BOD-0002", {}, "s03:topology",
               reason="the unselected alternative was dropped")])
        self.assertTrue(state.standing("GeometrySignature"),
                        "revising a candidate nobody selected withdrew the "
                        "selected design's geometry; currentness is supposed to "
                        "be dependency-local")
        self.assertTrue(state.standing("Feature"))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
