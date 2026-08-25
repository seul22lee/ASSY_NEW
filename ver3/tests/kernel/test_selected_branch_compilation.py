"""s07 compiles the selected candidate's program, and only that one.

The compiling half of the branch-isolation proof. Its kernel-free twin is
ver3/tests/meta/test_selected_branch_downstream.py, which holds the same
property for s06; the fixture is shared with it rather than rebuilt, so the two
halves cannot drift into testing different designs.

Why this half needs its own test rather than being implied by the s06 one: a
contaminated compile does not fail. Both candidates' construction statements are
valid programs, so building all of them emits real geometry with a real
GeometrySignature - one assembly containing two alternative designs at once,
described by a signature that looks exactly as authoritative as a correct one.
"""

import unittest

from ver3.assy_v3.downstream import execution
from ver3.assy_v3.pipeline.progression import Progression
from ver3.tests.meta.test_selected_branch_downstream import _TwoBranchState


class TestProductionCompilationBuildsOnlyTheSelection(_TwoBranchState):

    def _compiled(self, selected):
        state = self.two_branches(selected)
        execution.settle_current_selection(state, Progression())
        result, _ = execution.compile_current_selection(state, Progression())
        self.assertTrue(result.ok, result.problems)
        return state, result

    def test_selecting_a_compiles_only_a_body(self):
        _state, result = self._compiled("CND-A")
        built = {b.body_id for b in result.bodies}
        self.assertEqual({"BOD-A"}, built,
                         "the unselected candidate's body was compiled into the "
                         "selected design")

    def test_selecting_b_compiles_only_b_body(self):
        _state, result = self._compiled("CND-B")
        self.assertEqual({"BOD-B"}, {b.body_id for b in result.bodies})

    def test_the_geometry_is_the_selected_candidates_dimension(self):
        """Not merely the right id: the right NUMBER.

        A's width is 20 and B's is 55, so a compile that resolved the wrong
        branch's parameter would produce a body of the wrong size while still
        naming the right body.
        """
        _state, result = self._compiled("CND-A")
        body = result.bodies[0]
        x0, _y0, _z0, x1, _y1, _z1 = body.bbox
        self.assertAlmostEqual(20.0, x1 - x0, places=6)

    def test_the_reverse_selection_gives_the_other_dimension(self):
        _state, result = self._compiled("CND-B")
        body = result.bodies[0]
        x0, _y0, _z0, x1, _y1, _z1 = body.bbox
        self.assertAlmostEqual(55.0, x1 - x0, places=6)

    def test_the_signature_traces_only_selected_branch_statements(self):
        """Read from the compiled bodies, which is where the statement map is.

        `result.signature` is the compiler's own measurement record keyed by
        body; the statement-to-feature map lives on each CompiledBody and is
        what `compilation_operations` later copies onto the GeometrySignature
        entity. Asserting against the source keeps this test independent of that
        copy.
        """
        _state, result = self._compiled("CND-A")
        mapped = set()
        for body in result.bodies:
            mapped |= set(body.feature_map or {})
        self.assertTrue(result.bodies, "nothing compiled, so nothing is traced")
        self.assertNotIn("FEA-B", mapped)
        self.assertIn("FEA-A", mapped)


class TestProductionCompilationRefusesToGuess(_TwoBranchState):

    def test_a_withdrawn_selection_refuses_rather_than_building_everything(self):
        from ver3.assy_v3.state.patch import Op
        state = self.two_branches("CND-A")
        execution.settle_current_selection(state, Progression())
        self._commit(state, "selection", [
            Op("INVALIDATE", "SelectionDecision", "SEL-0001", {},
               "selection:reopened", reason="reopened for review")])
        with self.assertRaises(execution.NoStandingSelection):
            execution.compile_current_selection(state, Progression())


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
