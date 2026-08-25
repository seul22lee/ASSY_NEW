"""Two candidates in one DesignState must not settle as one design.

s05 may author geometry for candidate A and, historically or concurrently, for
candidate B. Both sets live in the same DesignState, because there is one design
graph and alternatives are part of it. So "which records are the input to s06"
is a real question with a wrong answer available: reading all of them settles A's
constraints against B's parameters and produces a system neither design
describes - and it does not fail while doing it, because a larger linear system
is still a linear system. It just answers a question nobody asked.

The production entries resolve the selection themselves. That is the property
here: not that a caller CAN pass the right branch, but that production does not
give a caller the chance to pass the wrong one.

The compilation half of this proof needs a CAD kernel and lives in
ver3/tests/kernel/test_selected_branch_compilation.py.
"""

import unittest

from . import _fixtures, _paths

from ver3.assy_v3.downstream import canonical_io, execution
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch


MM = {"unit": "mm"}


class _TwoBranchState(_fixtures.StateBuilder, unittest.TestCase):
    """A design with two embodied alternatives and a commitment to one."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")

    def _commit(self, state, stage, ops):
        patch = StagePatch(
            patch_id="%s-%d" % (stage, len(state.applied_patches)),
            run_id=state.run_id, stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS", provenance={"purpose": "branch test"})
        problems = state.validate(patch)
        self.assertEqual([], problems, "fixture rejected: %s" % problems)
        state.apply(patch)

    def _embody(self, state, branch, suffix, width):
        """One candidate's embodiment, every record premised on its candidate.

        Branch membership is the premise closure, which is what `_in_branch`
        reads. Nothing here writes a branch field, because the architecture has
        none - inventing one for the fixture would prove a mechanism that does
        not exist.
        """
        body = "BOD-%s" % suffix
        self._commit(state, "s03", [
            Op("CREATE", "Body", body,
               {"instance_identity": "part %s" % suffix, "role": "shell",
                "created_by_stage": "s03"}, "s03:topology",
               premise_refs=[branch])])
        # Unit G: the s04 commitments the embodiment is placed against - a scale
        # and the body's envelope - on this branch.
        self._commit(state, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-%s" % suffix,
               {"basis": "ABSOLUTE", "absolute": {"unit": "mm", "per_unit": 1.0}},
               "s04:arrangement", premise_refs=[branch]),
            Op("CREATE", "Envelope", "ENV-%s" % suffix,
               {"body": body, "extent": {"centre": [0, 0, 0], "half_extent": [30, 5, 2]},
                "frame": "world", "maturity": "PROVISIONAL"},
               "s04:arrangement", premise_refs=[branch, "SCL-%s" % suffix])])
        self._commit(state, "s05", [
            Op("CREATE", "Parameter", "PRM-%s" % suffix,
               {"symbol": "w", "unit": "mm", "status": "DECLARED"},
               "s05:embodiment", premise_refs=[branch]),
            Op("CREATE", "Constraint", "CON-%s" % suffix,
               {"kind": "DIMENSIONAL", "parameters": ["PRM-%s" % suffix],
                "expression": {"relation": "==",
                               "lhs": {"ref": "PRM-%s" % suffix},
                               "rhs": {"const": float(width), "unit": "mm"}}},
               "s05:embodiment", premise_refs=[branch, "PRM-%s" % suffix]),
            Op("CREATE", "Feature", "FEA-%s" % suffix,
               {"body": body, "feature_kind": "STOCK", "geometry": "the block",
                "placement": {"datum": "ENV-%s" % suffix, "axis": "+Z"},
                "construction": [{"id": "block", "operation": "BOX", "operands": [],
                                  "parameters": {"dx": {"ref": "PRM-%s" % suffix},
                                                 "dy": {"const": 10.0, "unit": "mm"},
                                                 "dz": {"const": 4.0, "unit": "mm"}}}]},
               "s05:embodiment", premise_refs=[branch, body, "ENV-%s" % suffix, "PRM-%s" % suffix])])

    def two_branches(self, selected):
        state = DesignState(run_id="branches")
        self.add(state, "s02", "Candidate", "CND-A", principle="a hinged cover")
        self.add(state, "s02", "Candidate", "CND-B", principle="a sliding lid")
        self.add(state, "selection", "SelectionDecision", "SEL-0001",
                 selected_candidate=selected)
        # Deliberately different widths, so a contaminated solve is visible as a
        # number rather than only as an extra id.
        self._embody(state, "CND-A", "A", 20.0)
        self._embody(state, "CND-B", "B", 55.0)
        return state


class TestTheFixtureReallyContainsBothBranches(_TwoBranchState):
    """Otherwise every isolation assertion below is about an absence."""

    def test_both_embodiments_are_committed_and_standing(self):
        state = self.two_branches("CND-A")
        ids = {r["entity_id"] for r in state.standing("Parameter")}
        self.assertEqual({"PRM-A", "PRM-B"}, ids)
        ids = {r["entity_id"] for r in state.standing("Feature")}
        self.assertEqual({"FEA-A", "FEA-B"}, ids)

    def test_an_unfiltered_read_really_would_see_both(self):
        """The defect this guards against, demonstrated on the low-level API.

        `branch=None` is legitimate for a diagnostic. What it must never be is
        how production decides what to settle.
        """
        state = self.two_branches("CND-A")
        params = canonical_io.read_parameters(state, None)
        self.assertEqual({"PRM-A", "PRM-B"}, {p.entity_id for p in params})


class TestProductionSettlementReadsOnlyTheSelection(_TwoBranchState):

    def test_selecting_a_settles_a_only(self):
        state = self.two_branches("CND-A")
        report, _ = execution.settle_current_selection(state, Progression())
        self.assertIn("PRM-A", report.settled)
        self.assertNotIn("PRM-B", report.settled,
                         "the unselected candidate's parameter was settled into "
                         "the selected design")
        self.assertAlmostEqual(20.0, report.settled["PRM-A"], places=9)

    def test_selecting_b_settles_b_only(self):
        """The reverse, so nothing above passes because A is alphabetically first."""
        state = self.two_branches("CND-B")
        report, _ = execution.settle_current_selection(state, Progression())
        self.assertIn("PRM-B", report.settled)
        self.assertNotIn("PRM-A", report.settled)
        self.assertAlmostEqual(55.0, report.settled["PRM-B"], places=9)

    def test_the_unselected_constraint_is_not_in_the_active_set(self):
        state = self.two_branches("CND-A")
        report, _ = execution.settle_current_selection(state, Progression())
        blob = " ".join(report.active_set) + " ".join(report.conflicting)
        self.assertNotIn("CON-B", blob)


class TestProductionRefusesToGuess(_TwoBranchState):

    def test_with_no_selection_settlement_refuses_rather_than_reading_everything(self):
        state = DesignState(run_id="nochoice")
        self.add(state, "s02", "Candidate", "CND-A", principle="a hinged cover")
        self.add(state, "s02", "Candidate", "CND-B", principle="a sliding lid")
        self._embody(state, "CND-A", "A", 20.0)
        self._embody(state, "CND-B", "B", 55.0)
        with self.assertRaises(execution.NoStandingSelection):
            execution.settle_current_selection(state, Progression())

    def test_a_withdrawn_selection_also_refuses(self):
        state = self.two_branches("CND-A")
        self._commit(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-0001", {},
               "selection:reopened", reason="reopened for review")])
        with self.assertRaises(execution.NoStandingSelection):
            execution.settle_current_selection(state, Progression())

    def test_the_resolver_agrees_with_the_view(self):
        """One authority. If these two ever disagreed, s05 would embody one
        candidate and s06 would settle another, and both would look correct."""
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
        state = self.two_branches("CND-A")
        self.assertEqual(S05Embodiment().consumer_view(state).branch,
                         execution.current_selection(state))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
