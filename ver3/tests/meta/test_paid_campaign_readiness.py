"""What the first paid diagnostic will ask for, verified without asking for it.

Zero provider calls. Nothing here constructs a live client, and the one test
that touches a provider interface uses a recording fake that answers nothing.

The point is to find out BEFORE money is spent whether the settings the campaign
needs are reachable, because the failure mode is quiet: a provider CEILING of
65536 does not raise a stage REQUEST of 32000 - the resolution layer clamps
downward and never up - so a campaign configuring only the ceiling would believe
it had a budget it never asked for, and would read every truncation as a model
failure rather than as its own configuration.

The responsibility list is DERIVED, not written down here. A list typed from
memory is a list that stops matching the pipeline the first time the pipeline
changes, and this file would then be describing a campaign nobody is running.
"""

import unittest

from ver3.assy_v3.pipeline.progression import (DETERMINISTIC_RESPONSIBILITIES,
                                               PRODUCING_RESPONSIBILITIES)
from ver3.assy_v3.providers.interfaces import ProviderCapabilities
from ver3.assy_v3.providers.status import ExecutionStatus
from ver3.assy_v3.stages.base import GenerationSettings
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment


#: What the first bounded diagnostic will request. One attempt, because
#: retrying changes what a result MEANS: one attempt records what the model did,
#: three records the best of three.
CAMPAIGN = GenerationSettings(temperature=1.0, max_output_tokens=65536,
                              max_attempts=1)


class RecordingProvider:
    """Captures the request and answers nothing. No network, no model."""

    def __init__(self):
        self.requests = []

    def capabilities(self):
        return ProviderCapabilities(
            provider_id="recording", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="dry-run fixture; never answers")

    def generate(self, request, attempt_index=0):
        import time
        from ver3.assy_v3.providers.interfaces import GenerationResult
        self.requests.append(request)
        return GenerationResult(
            execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE, response=None,
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=False,
            error_detail="dry run: no provider was contacted")


class TestTheResponsibilitySequenceIsDerived(unittest.TestCase):

    def test_the_registry_names_both_kinds(self):
        """Otherwise the split below is being asserted rather than read."""
        self.assertTrue(PRODUCING_RESPONSIBILITIES)
        self.assertTrue(DETERMINISTIC_RESPONSIBILITIES)

    def test_the_two_kinds_do_not_overlap(self):
        """A responsibility that is both would be asked for a model call and
        also described as deciding nothing."""
        self.assertEqual(set(), set(PRODUCING_RESPONSIBILITIES)
                         & set(DETERMINISTIC_RESPONSIBILITIES))

    def test_the_deterministic_pair_is_exactly_s06_and_s07(self):
        """Pinned because the campaign must not pay for either. If a third
        deterministic responsibility appears, this fails and the manifest is
        rewritten deliberately."""
        self.assertEqual(("s06", "s07"), tuple(DETERMINISTIC_RESPONSIBILITIES))

    def test_embodiment_is_model_owned(self):
        """s05 is the one the campaign's second phase pays for."""
        self.assertIn("s05", PRODUCING_RESPONSIBILITIES)


class TestTheCampaignCanAskForWhatItNeeds(unittest.TestCase):

    def request_for(self, settings):
        provider = RecordingProvider()
        stage = S05Embodiment()
        inputs = {stage.context_key: {}, stage.occupancy_key: {}}
        stage.run(provider, inputs, None, "dry-run", settings=settings)
        self.assertEqual(1, len(provider.requests))
        return provider.requests[0]

    def test_the_token_budget_IS_the_request_not_merely_the_ceiling(self):
        """The quiet failure this file exists for."""
        self.assertEqual(65536, self.request_for(CAMPAIGN).max_output_tokens)

    def test_the_campaign_temperature_reaches_the_request(self):
        self.assertEqual(1.0, self.request_for(CAMPAIGN).temperature)

    def test_the_provider_ceiling_would_not_clamp_this_request(self):
        """Read from the client's declared ceiling, so a lowered ceiling fails
        here rather than silently truncating a paid run."""
        from ver3.live_providers.deepseek import MAX_OUTPUT_TOKENS_CEILING
        self.assertGreaterEqual(MAX_OUTPUT_TOKENS_CEILING,
                                CAMPAIGN.max_output_tokens)

    def test_one_attempt_and_no_hidden_retry(self):
        self.assertEqual(1, CAMPAIGN.max_attempts)

    def test_the_settings_are_recordable_verbatim(self):
        record = CAMPAIGN.as_record()
        self.assertEqual({"temperature": 1.0, "max_output_tokens": 65536,
                          "max_attempts": 1},
                         {k: record[k] for k in ("temperature",
                                                 "max_output_tokens",
                                                 "max_attempts")})

    def test_ordinary_production_defaults_are_untouched(self):
        """The campaign configures itself; it does not move normal behaviour."""
        default = GenerationSettings()
        self.assertEqual(0.0, default.temperature)
        self.assertEqual(32000, default.max_output_tokens)


class TestTheDeterministicTailPaysForNothing(unittest.TestCase):

    def test_settlement_and_compilation_take_no_provider(self):
        """Their entry points have no provider parameter at all, which is a
        stronger guarantee than passing None: there is nothing to pass."""
        import inspect
        from ver3.assy_v3.downstream import execution
        for name in ("settle_current_selection", "compile_current_selection"):
            with self.subTest(entry=name):
                params = inspect.signature(
                    getattr(execution, name)).parameters
                self.assertNotIn("provider", params)

    def test_deterministic_records_carry_no_provider_field(self):
        from ver3.assy_v3.pipeline.progression import DeterministicExecution
        import dataclasses
        fields = {f.name for f in dataclasses.fields(DeterministicExecution)}
        self.assertNotIn("provider_id", fields)
        self.assertNotIn("response_source", fields)


class TestHumanSelectionRemainsTheCheckpoint(unittest.TestCase):
    """The campaign is two phases because the choice is a person's.

    Phase A runs to a comparison and STOPS. Phase B resumes the persisted state
    and embodies the selected candidate. There is no automatic selection, and
    these are the mechanisms that make an accidental one impossible.
    """

    def test_s05_will_not_run_without_a_standing_decision(self):
        from ver3.assy_v3.state.design_state import DesignState
        provider = RecordingProvider()
        outcome = S05Embodiment().invoke(provider, DesignState("phaseA"), "r")
        self.assertEqual(0, len(provider.requests),
                         "phase B would begin without a human choice")
        self.assertIs(ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT,
                      outcome.execution_status)

    def test_the_downstream_refuses_to_guess_a_selection(self):
        from ver3.assy_v3.downstream import execution
        from ver3.assy_v3.state.design_state import DesignState
        with self.assertRaises(execution.NoStandingSelection):
            execution.current_selection(DesignState("phaseA"))

    def test_nothing_in_production_selects_a_candidate_automatically(self):
        """A SelectionDecision may only be written by the selection owner."""
        from ver3.assy_v3.state.design_state import Contracts
        self.assertEqual("selection",
                         Contracts().owner_of("SelectionDecision"))


class TestTheDryRunContactedNobody(unittest.TestCase):
    """Said in the suite as well as in the report."""

    def test_this_module_constructs_no_live_client(self):
        import ast
        tree = ast.parse(open(__file__).read())
        constructed = {n.func.id for n in ast.walk(tree)
                       if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Name)}
        self.assertNotIn("DeepSeekProvider", constructed)

    def test_the_only_provider_here_answers_nothing(self):
        provider = RecordingProvider()
        result = provider.generate(object())
        self.assertIsNone(result.response)
        self.assertIs(ExecutionStatus.PROVIDER_UNAVAILABLE,
                      result.execution_status)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
