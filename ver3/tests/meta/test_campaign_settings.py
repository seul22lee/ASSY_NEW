"""A campaign asks for its settings out loud, and the request carries them.

Written for the paid diagnostic that has not run yet, so the settings it will
need are known to be reachable BEFORE money is spent rather than discovered
afterwards in a run record.

The one that matters most is `max_output_tokens`. A provider CEILING of 65536
does not raise a stage REQUEST of 32000 - the resolution layer clamps downward,
never upward - so a campaign that configured only the ceiling would believe it
had a budget it never asked for, and would read every truncation as a model
failure. The test below asserts on the request the provider actually receives.

`max_attempts` is here because retrying changes what a result MEANS. One attempt
records what the model did. Three records the best of three, and reporting that
as "the model produced this" overstates it.

No provider is contacted. The fake records the request and returns nothing.
"""

import unittest

from ver3.assy_v3.providers.interfaces import ProviderCapabilities
from ver3.assy_v3.providers.status import ExecutionStatus
from ver3.assy_v3.stages.base import GenerationSettings
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment


class RecordingProvider:
    """Captures the request and refuses. Nothing here needs a response."""

    def __init__(self):
        self.requests = []

    def capabilities(self):
        return ProviderCapabilities(
            provider_id="recording", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="records the request only")

    def generate(self, request, attempt_index=0):
        from ver3.assy_v3.providers.interfaces import GenerationResult
        import time
        self.requests.append(request)
        return GenerationResult(
            execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE, response=None,
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=False,
            error_detail="recording fixture never answers")


class _Asked(unittest.TestCase):
    """Drive `run` directly: this is about the request, not about readiness."""

    def request_for(self, settings=None):
        provider = RecordingProvider()
        stage = S05Embodiment()
        inputs = {stage.context_key: {}, stage.occupancy_key: {}}
        stage.run(provider, inputs, None, "campaign-run", settings=settings)
        self.assertEqual(1, len(provider.requests),
                         "the provider was not asked, so there is no request "
                         "to make assertions about")
        return provider.requests[0]


class TestDefaultsAreUnchanged(_Asked):
    """This unit must not silently move normal production behaviour."""

    def test_the_default_temperature_is_still_zero(self):
        self.assertEqual(0.0, self.request_for().temperature)

    def test_the_default_token_request_is_unchanged(self):
        self.assertEqual(32000, self.request_for().max_output_tokens)

    def test_the_default_attempt_count_is_one(self):
        self.assertEqual(1, GenerationSettings().max_attempts)


class TestACampaignCanAskForWhatItNeeds(_Asked):

    CAMPAIGN = GenerationSettings(temperature=1.0, max_output_tokens=65536,
                                  max_attempts=1)

    def test_the_campaign_temperature_reaches_the_request(self):
        self.assertEqual(1.0, self.request_for(self.CAMPAIGN).temperature)

    def test_the_campaign_token_budget_IS_the_request(self):
        """Not merely the provider's ceiling. The resolution layer clamps a
        request DOWN to the ceiling and never up, so a ceiling of 65536 with a
        request of 32000 yields 32000 - and every truncation after that would be
        read as a model failure rather than as a budget nobody asked for."""
        self.assertEqual(65536,
                         self.request_for(self.CAMPAIGN).max_output_tokens)

    def test_the_settings_can_be_recorded_verbatim(self):
        """A run record must be able to say what was ASKED, not only what was
        resolved."""
        record = self.CAMPAIGN.as_record()
        self.assertEqual(1.0, record["temperature"])
        self.assertEqual(65536, record["max_output_tokens"])
        self.assertEqual(1, record["max_attempts"])

    def test_settings_are_frozen(self):
        """A campaign configuration something can edit mid-run is not a record
        of what the campaign asked for."""
        with self.assertRaises(Exception):
            self.CAMPAIGN.temperature = 0.5


class TestTheStageStillIdentifiesItself(_Asked):
    """Settings must not displace the identity the run record is built on."""

    def test_the_request_names_the_responsibility_and_the_run(self):
        request = self.request_for(TestACampaignCanAskForWhatItNeeds.CAMPAIGN)
        self.assertEqual("s05", request.stage_id)
        self.assertEqual("s05", request.responsibility_id)
        self.assertEqual("campaign-run", request.run_id)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
