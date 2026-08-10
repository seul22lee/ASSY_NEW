"""Refinement, refreshed premise, recomputation - in that order.

S-6 gave s04b a way to supersede a spatial commitment with a geometric reason.
It could do that in the SAME invocation that placed the mechanism, and every hook
reasons from `inputs[consumer_view]` - the view built when the invocation
started. So the swept occupancy was computed from the extent the same patch was
replacing, and it did not even go stale: it is created after the supersession, so
it was never a dependent of it. Current evidence, derived from geometry the design
had just withdrawn.

A revision is now a BARRIER. The invocation commits the revision alone, says so in
a field, and the caller refreshes and asks again; the second invocation reasons
from what the first committed. The realization is withheld, not discarded.
"""
from __future__ import annotations

import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion, aabb, sweep_hull)
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from ver3.tools import run_window2                                      # noqa: E402
from .test_s02_s03b_integration import _Canned                          # noqa: E402
from .test_s6_spatial import _S04Chain, s04a_response, s04b_response    # noqa: E402

BIG = [4, 4, 4]


def revision(env, half=None, why="the body cannot clear at the committed size"):
    return {"envelope": env, "half_extent": list(half or BIG),
            "centre": [0, 0, 0], "geometric_reason": why}


class _Barrier(_S04Chain):
    """s01..s04a through the real chain, then s04b under the caller's control."""

    def upto_s04a(self, shapes=(("A", 2, 2),)):
        state, _ = self.build(list(shapes))
        invs = {}
        for sfx, ng, _nc in shapes:
            inv = cv.InvocationContext(branch="CND-%s" % sfx)
            bodies = ["BOD-G0%s" % sfx, "BOD-G1%s" % sfx][:ng]
            provider = _Canned(s04a_response(bodies, step="ASY-%s" % sfx,
                                             actor="ACT-0001"))
            state.apply(S04AEnvelopeAndReach().invoke(
                provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
                attempt=1, invocation=inv).patch)
            invs[sfx] = inv
        return state, invs

    def call_s04b(self, state, inv, payload, sfx="A"):
        out = S04BPlacementAndMotion().invoke(
            _Canned(payload), state, state.run_id,
            {"candidate": "CND-%s" % sfx}, attempt=2, invocation=inv)
        self.assertIsNotNone(out.patch, out.problems)
        state.apply(out.patch)
        return out

    def realization(self, sfx="A", revisions=None):
        return s04b_response("JNT-%s" % sfx,
                             ["CFG-C0%s" % sfx, "CFG-C1%s" % sfx],
                             "RGP-G0%s" % sfx, revisions=revisions)

    def families(self, patch):
        return sorted({op.entity_type for op in patch.operations})


# =====================================================================
class TestRefinementBarrier(_Barrier):

    def test_R1_no_revision_realizes_in_one_invocation(self):
        state, invs = self.upto_s04a()
        out = self.call_s04b(state, invs["A"], self.realization())
        self.assertFalse(out.refinement_only)
        self.assertEqual("SUCCESS", out.execution_status.value,
                         out.declared_incompleteness)
        for family in ("State", "Transition", "SweptVolume"):
            self.assertTrue(state.family(family), family)
        self.assertEqual([0, 0, 0], state.entities["JNT-A"]["frame_origin"])

    def test_R2_a_revision_commits_the_revision_and_nothing_else(self):
        state, invs = self.upto_s04a()
        out = self.call_s04b(state, invs["A"],
                             self.realization(revisions=[revision("ENV-0A")]))
        self.assertTrue(out.refinement_only, "the barrier did not fire")
        self.assertEqual(["Envelope"], self.families(out.patch))
        self.assertEqual(BIG, state.entities["ENV-0A"]["extent"]["half_extent"])
        for family in ("State", "Transition", "SweptVolume"):
            self.assertEqual([], state.family(family),
                             "%s was realized from the arrangement being replaced"
                             % family)
        self.assertNotIn("frame_origin", state.entities["JNT-A"])
        self.assertTrue(out.declared_incompleteness[0].startswith("1 arrangement"),
                        out.declared_incompleteness)
        self.assertIn("ENV-0A", out.declared_incompleteness[0])

    def test_R3_the_second_invocation_sees_the_revised_values(self):
        state, invs = self.upto_s04a()
        before = S04BPlacementAndMotion().consumer_view(state, invs["A"]).payload()
        self.call_s04b(state, invs["A"],
                       self.realization(revisions=[revision("ENV-0A")]))
        after = S04BPlacementAndMotion().consumer_view(state, invs["A"]).payload()

        def extent(view):
            return {e["entity_id"]: e["extent"]["half_extent"]
                    for e in view.get("Envelope") or []}
        self.assertEqual([1, 1, 1], extent(before)["ENV-0A"])
        self.assertEqual(BIG, extent(after)["ENV-0A"],
                         "the refreshed view still holds the old arrangement")

    def test_R4_the_recomputed_geometry_follows_the_revision(self):
        """Same response, same joint, different committed extent - and the
        occupancy that comes out is different, which is what makes the barrier
        worth having."""
        plain, invs = self.upto_s04a()
        self.call_s04b(plain, invs["A"], self.realization())
        small = plain.family("SweptVolume")[0]["occupancy"]["aabb"]

        state, invs2 = self.upto_s04a()
        self.call_s04b(state, invs2["A"],
                       self.realization(revisions=[revision("ENV-0A")]))
        self.call_s04b(state, invs2["A"], self.realization())
        big = state.family("SweptVolume")[0]["occupancy"]["aabb"]
        self.assertNotEqual(small, big)
        joint = [j for j in state.family("Joint") if j["entity_id"] == "JNT-A"][0]
        expected = sweep_hull(aabb([0, 0, 0], BIG), joint, [0, 0, 0], 0.0, 90.0)
        self.assertEqual(expected["hull"], big,
                         "the occupancy was not computed from the revised extent")

    def test_R5_the_final_realization_is_current_and_rests_on_the_revision(self):
        state, invs = self.upto_s04a()
        self.call_s04b(state, invs["A"],
                       self.realization(revisions=[revision("ENV-0A")]))
        out = self.call_s04b(state, invs["A"], self.realization())
        self.assertFalse(out.refinement_only)
        for family in ("State", "Transition", "SweptVolume"):
            produced = state.family(family)
            self.assertTrue(produced, family)
            for e in produced:
                self.assertEqual("STANDING", e.get("_validity"), e["entity_id"])
        # The occupancy is what the revised extent was swept into, so it is what
        # names it. The coordinates do not: they are not computed from any box.
        self.assertIn("ENV-0A",
                      state.entities["SWV-TRN-A-RGP-G0A"].get("_premises") or [])
        self.assertEqual(BIG, state.entities["ENV-0A"]["extent"]["half_extent"])

    def test_R6_no_swept_volume_from_old_geometry_can_remain_current(self):
        """The exact defect. It used to be STANDING, with a hull four times too
        small, while the extent it was computed from had been superseded."""
        state, invs = self.upto_s04a()
        joint = [j for j in state.family("Joint") if j["entity_id"] == "JNT-A"][0]
        stale_hull = sweep_hull(aabb([0, 0, 0], [1, 1, 1]), joint,
                                [0, 0, 0], 0.0, 90.0)["hull"]
        self.call_s04b(state, invs["A"],
                       self.realization(revisions=[revision("ENV-0A")]))
        self.call_s04b(state, invs["A"], self.realization())
        for v in state.family("SweptVolume"):
            self.assertNotEqual(stale_hull, v["occupancy"]["aabb"],
                                "%s carries the pre-revision geometry"
                                % v["entity_id"])
        current = [v for v in state.standing("SweptVolume")]
        self.assertTrue(current)
        for v in current:
            self.assertEqual(BIG, state.entities["ENV-0A"]["extent"]["half_extent"])

    def test_R7_a_later_supersession_stales_what_was_already_produced(self):
        """The other half of the lifecycle, unchanged: a revision that arrives
        AFTER a realization exists reaches it through the premise substrate."""
        state, invs = self.upto_s04a()
        self.call_s04b(state, invs["A"], self.realization())
        for family in ("State", "Transition", "SweptVolume"):
            for e in state.family(family):
                self.assertEqual("STANDING", e.get("_validity"))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-0A",
                              {"extent": {"half_extent": BIG, "centre": [0, 0, 0]}},
                              "test", reason="a later geometric finding"))
        for e in state.family("SweptVolume"):
            self.assertEqual("STALE", e.get("_validity"), e["entity_id"])
        # And a change to what the coordinates ARE reaches them and the occupancy
        # that swept between them - the other half of the same rule.
        self.revise(state, Op("SUPERSEDE", "State", "STA-CFG-C1A",
                              {"joint_coordinates": {"JNT-A": 12}}, "test",
                              reason="the endpoint moved"))
        self.assertEqual("STALE", state.entities["TRN-A"].get("_validity"))

    def test_R8_a_refinement_on_one_branch_leaves_the_other_alone(self):
        state, invs = self.upto_s04a((("A", 2, 2), ("B", 1, 3)))
        self.call_s04b(state, invs["B"], self.realization("B"), sfx="B")
        b_before = json.dumps([v["occupancy"] for v in state.family("SweptVolume")],
                              sort_keys=True)
        out = self.call_s04b(state, invs["A"],
                             self.realization(revisions=[revision("ENV-0A")]))
        self.assertTrue(out.refinement_only)
        self.call_s04b(state, invs["A"], self.realization())
        b_after = [v for v in state.family("SweptVolume")
                   if v["rigid_group"].endswith("B")]
        self.assertEqual(1, len(b_after))
        self.assertEqual("STANDING", b_after[0].get("_validity"),
                         "another branch's refinement reached this one")
        self.assertEqual(json.loads(b_before)[0]["aabb"],
                         json.loads(json.dumps(b_after[0]["occupancy"]))["aabb"],
                         "the other branch's occupancy was recomputed")
        self.assertEqual([1, 1, 1],
                         state.entities["ENV-0B"]["extent"]["half_extent"])

    def test_R9_the_runner_reaches_the_same_state_as_manual_control(self):
        manual, invs = self.upto_s04a()
        self.call_s04b(manual, invs["A"],
                       self.realization(revisions=[revision("ENV-0A")]))
        self.call_s04b(manual, invs["A"], self.realization())

        runner, _ = self.build([("A", 2, 2)])
        inv = cv.InvocationContext(branch="CND-A")
        provider = _Canned(s04a_response(["BOD-G0A", "BOD-G1A"], step="ASY-A",
                                         actor="ACT-0001"),
                           self.realization(revisions=[revision("ENV-0A")]),
                           self.realization())
        rec = run_window2.run_s04("SYN", runner, provider, 1, invocation=inv)
        self.assertEqual("SUCCESS", rec["s04b_status"], rec["failures"])
        self.assertTrue(rec.get("s04b_refinements"), "no refinement was recorded")
        self.assertEqual([], [f for f in rec["failures"]
                              if f["kind"] == "CONTRACT_CONDITION"],
                         rec["failures"])

        def canonical(s):
            return {eid: json.dumps({k: v for k, v in s.entities[eid].items()
                                     if not k.startswith("_")}, sort_keys=True)
                    for eid in s.entities}
        self.assertEqual(canonical(manual), canonical(runner))

    def test_R9b_the_runner_bounds_the_refresh(self):
        """A stage that keeps revising is reported, not looped on."""
        runner, _ = self.build([("A", 2, 2)])
        inv = cv.InvocationContext(branch="CND-A")
        forever = self.realization(revisions=[revision("ENV-0A")])
        provider = _Canned(s04a_response(["BOD-G0A", "BOD-G1A"], step="ASY-A",
                                         actor="ACT-0001"), forever)
        rec = run_window2.run_s04("SYN", runner, provider, 1, invocation=inv)
        self.assertEqual(2, len(rec.get("s04b_refinements") or []))
        self.assertTrue(any("still revising" in str(f["what"])
                            for f in rec["failures"]), rec["failures"])
        self.assertEqual([], runner.family("SweptVolume"),
                         "a realization was committed from an unsettled arrangement")

    def test_R10_no_selection_semantics_were_used(self):
        state, invs = self.upto_s04a()
        self.call_s04b(state, invs["A"],
                       self.realization(revisions=[revision("ENV-0A")]))
        self.call_s04b(state, invs["A"], self.realization())
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertIsNone(cv.committed_branch(state, self.c))
        self.assertEqual([], s04.selection_gate_check(state))


class TestBarrierGenerality(_Barrier):
    """The barrier is a property of the hook, not of s04b."""

    def test_a_stage_that_revises_nothing_has_no_barrier(self):
        from ver3.assy_v3.stages.base import Stage
        self.assertIsNone(Stage().refinement_barrier({}, {}, None))
        state, invs = self.upto_s04a()
        view = S04BPlacementAndMotion().consumer_view(state, invs["A"]).payload()
        self.assertIsNone(S04BPlacementAndMotion().refinement_barrier(
            self.realization(), {"consumer_view": view}, state))

    def test_an_unjustified_revision_neither_fires_nor_commits(self):
        """One reader decides both. A revision the commit would refuse must not
        fire the barrier - that would withhold the realization and commit
        nothing, a stall with no visible cause."""
        state, invs = self.upto_s04a()
        view = S04BPlacementAndMotion().consumer_view(state, invs["A"]).payload()
        inputs = {"consumer_view": view}
        stage = S04BPlacementAndMotion()
        for bad in (revision("ENV-0A", why=""),
                    revision("ENV-DOES-NOT-EXIST"),
                    {"envelope": "ENV-0A", "geometric_reason": "no extent given"}):
            payload = self.realization(revisions=[bad])
            self.assertIsNone(stage.refinement_barrier(payload, inputs, state),
                              bad)
            self.assertEqual([], stage._revision_ops(payload, inputs, state), bad)
        out = self.call_s04b(state, invs["A"],
                             self.realization(revisions=[revision("ENV-0A", why="")]))
        self.assertFalse(out.refinement_only)
        self.assertEqual([1, 1, 1], state.entities["ENV-0A"]["extent"]["half_extent"])
        self.assertTrue(state.family("SweptVolume"))

    def test_the_barrier_and_the_commit_cannot_disagree(self):
        from .test_s3_interface_readiness import _code_only
        for fn in (S04BPlacementAndMotion.refinement_barrier,
                   S04BPlacementAndMotion.refinement_operations):
            self.assertIn("_revision_ops", _code_only(fn), fn.__name__)


if __name__ == "__main__":
    unittest.main()
