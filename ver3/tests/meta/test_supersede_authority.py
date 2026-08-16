"""SUPERSEDE may not bypass ownership.

THE GAP THIS FILE CLOSES

`DesignState.validate` routed SUPERSEDE to a method that took only the operation,
not the patch - so it could not see `patch.stage_id` even in principle, and a
supersession was checked for evidence and never for authority. Reproduced before
it was repaired: s01 rewrote the `symbol` of an s05-owned Parameter and nothing
objected. EXTEND had always been gated by exactly the same question, which is
what made the asymmetry a defect rather than a design.

THE RULE, DERIVED RATHER THAN INVENTED

The contracts define SUPERSEDE's effect (both values retained) and its evidence
requirements (provenance, reason, a prior value) and never say who may perform
one. So the rule comes from the authority the runtime already enforces:

    a delegated field belongs to its DELEGATE, and
    every other field belongs to the family's OWNER.

The delegation check comes first, and that ordering is load-bearing: `Parameter`
is owned by s05, so testing ownership first would let s05 supersede `value` - the
one thing S05-C10 exists to prevent.
"""

import unittest

from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op, StagePatch


def patch(state, stage, ops, attempt=1):
    return StagePatch(
        patch_id="%s-%d-%d" % (stage, attempt, len(state.applied_patches)),
        run_id=state.run_id, stage_id=stage, stage_attempt=attempt,
        parent_state_hash=state.state_hash(), operations=list(ops),
        execution_status="SUCCESS", provenance={"purpose": "t", "provider": "t"})


class _Base(unittest.TestCase):

    def setUp(self):
        self.state = DesignState(run_id="supersede")
        self.assertEqual([], self.apply("s05", [
            Op("CREATE", "Parameter", "PRM-1",
               {"symbol": "r", "unit": "mm", "status": "DECLARED"},
               "s05:embodiment")]))
        # s06 settles it through the field it was granted, so `value` has a
        # prior value and a supersession of it is well formed apart from
        # authority - which is the only thing under test.
        self.assertEqual([], self.apply("s06", [
            Op("EXTEND", "Parameter", "PRM-1",
               {"value": 5.0, "solved_by": "SLV-1"}, "s06:settlement")]))

    def apply(self, stage, ops):
        p = patch(self.state, stage, ops)
        problems = self.state.validate(p)
        if problems:
            return problems
        self.state.apply(p)
        return []

    def supersede(self, stage, fields):
        return self.apply(stage, [Op("SUPERSEDE", "Parameter", "PRM-1", fields,
                                     "%s:test" % stage, reason="a stated reason")])


class TestUnauthorizedSupersessionIsRefused(_Base):

    def test_an_unrelated_stage_cannot_revise_an_owned_field(self):
        """The reproduction: s01 rewriting an s05-owned Parameter's symbol."""
        problems = self.supersede("s01", {"symbol": "hijacked"})
        self.assertTrue(any("SUPERSEDE_NOT_PERMITTED" in p for p in problems),
                        problems)
        self.assertEqual("r", self.state.entities["PRM-1"]["symbol"])

    def test_the_compiler_cannot_revise_a_solver_field(self):
        problems = self.supersede("s07", {"value": 1.0})
        self.assertTrue(any("SUPERSEDE_WRONG_STAGE" in p for p in problems),
                        problems)
        self.assertAlmostEqual(5.0, self.state.entities["PRM-1"]["value"])

    def test_the_compiler_cannot_revise_an_owned_field(self):
        problems = self.supersede("s07", {"status": "SOLVED"})
        self.assertTrue(any("SUPERSEDE_NOT_PERMITTED" in p for p in problems),
                        problems)

    def test_the_owner_cannot_revise_a_field_it_delegated(self):
        """The ordering that matters. s05 owns Parameter and still may not set a
        value: granting `value` to s06 is giving it away, and S05-C10 depends on
        that being true at the write boundary and not only in a checker."""
        problems = self.supersede("s05", {"value": 1.0})
        self.assertTrue(any("SUPERSEDE_WRONG_STAGE" in p for p in problems),
                        problems)
        self.assertAlmostEqual(5.0, self.state.entities["PRM-1"]["value"])

    def test_a_refusal_names_the_stage_that_may(self):
        problems = self.supersede("s05", {"value": 1.0})
        self.assertTrue(any("s06" in p for p in problems), problems)


class TestAuthorizedSupersessionStillWorks(_Base):
    """The repair must not make legitimate revision impossible."""

    def test_the_owner_may_revise_a_field_it_kept(self):
        self.assertEqual([], self.supersede("s05", {"symbol": "boss_r"}))
        self.assertEqual("boss_r", self.state.entities["PRM-1"]["symbol"])

    def test_the_delegate_may_revise_its_own_field(self):
        """The convergence loop's second round depends on exactly this: a
        re-solve cannot EXTEND over an existing value, so it supersedes."""
        self.assertEqual([], self.supersede("s06", {"value": 7.0}))
        self.assertAlmostEqual(7.0, self.state.entities["PRM-1"]["value"])

    def test_the_prior_value_is_retained(self):
        self.supersede("s06", {"value": 7.0})
        history = self.state.entities["PRM-1"].get("_superseded") or []
        self.assertTrue(any(h.get("prior_value") == 5.0 for h in history), history)

    def test_evidence_requirements_are_unchanged(self):
        """Authority is added to the existing checks, not swapped for them."""
        silent = Op("SUPERSEDE", "Parameter", "PRM-1", {"symbol": "x"},
                    "s05:embodiment")
        self.assertTrue(any("NO_REASON" in p for p in
                            self.state.validate(patch(self.state, "s05", [silent]))))

    def test_a_field_with_no_prior_value_is_still_refused(self):
        problems = self.supersede("s05", {"lower": 1.0})
        self.assertTrue(any("SUPERSEDE_ABSENT" in p for p in problems), problems)


class TestInvalidateIsUnchanged(_Base):
    """INVALIDATE names no field and withdraws standing rather than replacing a
    value. Gating it on family ownership would be a different rule about a
    different operation, and lifecycle coordination retires entities across
    families by design."""

    def test_invalidate_remains_available(self):
        self.assertEqual([], self.apply("s07", [
            Op("INVALIDATE", "Parameter", "PRM-1", {}, "s07:compilation",
               reason="withdrawn by a coordinator")]))
        self.assertEqual("INVALIDATED", self.state.entities["PRM-1"]["_validity"])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
