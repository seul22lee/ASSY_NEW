"""s05 embodies THE selected candidate, or it does not run.

Production s05 is not "embody whichever branch the caller names". It runs once,
after a human has chosen, and the thing it embodies is the choice. That makes
three failures possible which a caller-supplied branch would hide:

  no commitment          - there is nothing to embody, and a stage that proceeds
                           is embodying whatever it was handed
  a withdrawn commitment - the choice was reopened, so the design is back to
                           having alternatives and none of them is THE one
  a contradicted one     - the caller names a candidate the design did not
                           select, which is not a scoping choice but a request
                           to build a design nobody chose

In all three the provider must not be called. That is the assertion these tests
actually make - not "an error was returned" but `provider.calls == 0`. A stage
that calls a model and then discards the answer has still spent the money and
still produced a record someone can mistake for evidence.

`SelectionDecision.selected_candidate` is the single authority throughout. No
test here sets a parallel branch variable, because production has none.
"""

import json
import time
import unittest

from . import _fixtures, _paths

from ver3.assy_v3.providers.interfaces import (GenerationResponse,
                                               GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.providers.status import ExecutionStatus
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.view import InvocationContext


class CountingProvider:
    """Records that it was asked. The whole point is the count, not the answer."""

    def __init__(self, payload=None):
        self.payload = payload if payload is not None else _EMPTY_RESPONSE
        self.calls = 0

    def capabilities(self):
        return ProviderCapabilities(
            provider_id="counting", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="structural test fixture")

    def generate(self, request, attempt_index=0):
        self.calls += 1
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(
                raw_text=json.dumps(self.payload), finish_reason="stop",
                truncated=False, input_tokens=None, output_tokens=None,
                served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=True)


_EMPTY_RESPONSE = {"features": [], "realizations": [], "parameters": [],
                   "constraints": [],
                   "unresolved": []}


class _SelectionBase(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")

    def two_candidates(self, run="sel"):
        """A design that has branched but not yet chosen."""
        state = DesignState(run_id=run)
        self.add(state, "s02", "Candidate", "CND-A",
                 principle="a hinged cover with a snap latch")
        self.add(state, "s02", "Candidate", "CND-B",
                 principle="a sliding lid running in a groove")
        return state

    def commit_to(self, state, candidate):
        self.add(state, "selection", "SelectionDecision", "SEL-0001",
                 selected_candidate=candidate)
        return state


class TestNoCommitmentMeansNoCall(_SelectionBase):

    def test_the_fixture_really_has_candidates_to_choose_between(self):
        """Otherwise 'not ready' would be true for a reason this test is not about."""
        state = self.two_candidates()
        self.assertEqual(2, len(state.standing("Candidate")))
        self.assertEqual([], list(state.standing("SelectionDecision")))

    def test_without_a_selection_decision_s05_is_not_ready(self):
        view = S05Embodiment().consumer_view(self.two_candidates())
        self.assertNotEqual("VIEW_READY", view.status.value)

    def test_without_a_selection_decision_the_provider_is_not_called(self):
        provider = CountingProvider()
        outcome = S05Embodiment().invoke(provider, self.two_candidates(), "r1")
        self.assertEqual(0, provider.calls,
                         "s05 called a model with no committed selection; there "
                         "was nothing for it to embody")
        self.assertIs(ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT,
                      outcome.execution_status)

    def test_the_blocked_outcome_still_carries_the_view_it_was_blocked_on(self):
        """A refusal that records nothing is indistinguishable from silence."""
        provider = CountingProvider()
        outcome = S05Embodiment().invoke(provider, self.two_candidates(), "r1")
        self.assertTrue(outcome.consumer_view)
        self.assertTrue(outcome.problems)


class TestAWithdrawnCommitmentMeansNoCall(_SelectionBase):

    def _reopened(self):
        state = self.commit_to(self.two_candidates(), "CND-A")
        # Reopening the choice: the decision stops standing. Through the
        # canonical INVALIDATE operation, not by deleting the record - the
        # history of having chosen is not erased by choosing again, and a test
        # that removed the row would be testing a state the system cannot reach.
        patch = StagePatch(
            patch_id="reopen", run_id=state.run_id, stage_id="selection",
            stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=[Op("INVALIDATE", "SelectionDecision", "SEL-0001", {},
                           "selection:reopened",
                           reason="the choice was reopened for review")],
            execution_status="SUCCESS", provenance={"purpose": "test"})
        problems = state.validate(patch)
        assert not problems, problems
        state.apply(patch)
        return state

    def test_the_fixture_really_did_withdraw_the_decision(self):
        state = self._reopened()
        self.assertTrue(state.has_entity("SEL-0001"),
                        "the record must still exist; only its standing changed")
        self.assertEqual([], list(state.standing("SelectionDecision")))

    def test_a_withdrawn_selection_does_not_reach_the_provider(self):
        provider = CountingProvider()
        outcome = S05Embodiment().invoke(provider, self._reopened(), "r1")
        self.assertEqual(0, provider.calls,
                         "s05 embodied a selection that had been withdrawn")
        self.assertIs(ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT,
                      outcome.execution_status)


class TestACallerMayNotOverruleTheCommitment(_SelectionBase):

    def test_asking_for_a_non_selected_candidate_is_refused(self):
        state = self.commit_to(self.two_candidates(), "CND-A")
        provider = CountingProvider()
        outcome = S05Embodiment().invoke(
            provider, state, "r1", invocation=InvocationContext(branch="CND-B"))
        self.assertEqual(0, provider.calls,
                         "s05 was routed to a candidate the design did not select")
        self.assertIs(ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT,
                      outcome.execution_status)

    def test_the_refusal_names_both_candidates(self):
        """So a reviewer can see it was a contradiction, not a missing premise."""
        state = self.commit_to(self.two_candidates(), "CND-A")
        view = S05Embodiment().consumer_view(
            state, InvocationContext(branch="CND-B"))
        detail = " ".join(a.get("detail", "") for a in view.assessment)
        self.assertIn("CND-B", detail)
        self.assertIn("CND-A", detail)

    def test_naming_the_selected_candidate_is_not_refused_on_that_ground(self):
        """The guard must catch contradiction, not agreement."""
        state = self.commit_to(self.two_candidates(), "CND-A")
        view = S05Embodiment().consumer_view(
            state, InvocationContext(branch="CND-A"))
        contradictions = [a for a in view.assessment
                          if "nobody chose" in a.get("detail", "")]
        self.assertEqual([], contradictions)


class TestTheRecordedViewIsScopedToTheCommitment(_SelectionBase):

    def test_the_view_branch_comes_from_the_decision(self):
        state = self.commit_to(self.two_candidates(), "CND-A")
        self.assertEqual("CND-A", S05Embodiment().consumer_view(state).branch)

    def test_the_selection_decision_itself_is_visible(self):
        """s05's prompt says the mechanism is already decided. The decision has
        to be IN the view, or that sentence refers to something absent."""
        state = self.commit_to(self.two_candidates(), "CND-A")
        payload = S05Embodiment().consumer_view(state).payload()
        self.assertIn("SelectionDecision", payload)
        self.assertEqual(["SEL-0001"],
                         [r["entity_id"] for r in payload["SelectionDecision"]])

    def test_the_selected_candidate_and_its_principle_are_visible(self):
        state = self.commit_to(self.two_candidates(), "CND-A")
        payload = S05Embodiment().consumer_view(state).payload()
        candidates = payload.get("Candidate") or []
        self.assertEqual(["CND-A"], [r["entity_id"] for r in candidates])
        self.assertEqual("a hinged cover with a snap latch",
                         candidates[0].get("principle"),
                         "the principle IS the mechanism decision; a view "
                         "carrying the candidate without it says which design "
                         "was chosen but not what it is")

    def test_the_unselected_candidate_is_not_visible(self):
        """Least privilege, and the reason it matters here: geometry proposed
        while looking at both alternatives is geometry for neither."""
        state = self.commit_to(self.two_candidates(), "CND-A")
        payload = S05Embodiment().consumer_view(state).payload()
        ids = [r["entity_id"] for r in (payload.get("Candidate") or [])]
        self.assertNotIn("CND-B", ids)

    def test_selecting_the_other_candidate_moves_the_view(self):
        """The same assertions with the choice reversed, so nothing above is
        passing because CND-A happens to be first."""
        state = self.commit_to(self.two_candidates(), "CND-B")
        view = S05Embodiment().consumer_view(state)
        self.assertEqual("CND-B", view.branch)
        ids = [r["entity_id"] for r in (view.payload().get("Candidate") or [])]
        self.assertEqual(["CND-B"], ids)


class TestInvocationPremisesComeFromTheCommitment(_SelectionBase):

    def test_both_the_candidate_and_the_decision_are_premises(self):
        """Two different facts. Withdraw the candidate and the geometry
        describes nothing; withdraw the decision and it describes something real
        the design is no longer pursuing."""
        stage = S05Embodiment()
        state = self.commit_to(self.two_candidates(), "CND-A")
        view = stage.consumer_view(state)
        premises = stage.invocation_premises({stage.context_key: view.payload()})
        self.assertIn("CND-A", premises)
        self.assertIn("SEL-0001", premises)

    def test_no_commitment_yields_no_invented_premise(self):
        stage = S05Embodiment()
        view = stage.consumer_view(self.two_candidates())
        self.assertEqual([], stage.invocation_premises(
            {stage.context_key: view.payload()}))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
