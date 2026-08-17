"""What the paid run will actually put on the wire, proven without a wire.

No network. Every test here replaces `urllib.request.urlopen` inside the
DeepSeek client, so the transport is exercised up to the moment of sending and
the request that WOULD have gone is inspected instead. No API key is needed and
no host is contacted.

The distinction this file exists for: a configuration value that is recorded and
a configuration value that governs the call are different things, and a run
record cannot tell them apart. `GenerationSettings.max_attempts = 1` was written
into the record while the client retried on its own constructor default of
three - so a campaign would have paid for up to three transport attempts per
responsibility and filed evidence saying it made one. Asserting that the config
equals 1 would have passed throughout. These tests count attempts at the
transport instead.
"""

import json
import unittest
import urllib.error

from ver3.assy_v3.providers.interfaces import GenerationRequest
from ver3.assy_v3.providers.status import ExecutionStatus


API_KEY_ENV = "DEEPSEEK_API_KEY"


class _Transport:
    """Stands in for `urlopen`. Records every call; never opens anything."""

    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.bodies = []

    def __call__(self, http_request, timeout=None):
        self.bodies.append(json.loads(http_request.data.decode("utf-8")))
        return self.behaviour(len(self.bodies))

    @property
    def attempts(self):
        return len(self.bodies)


def _rate_limited(_n):
    """A retriable transport failure: exactly what a retry loop reacts to."""
    raise urllib.error.HTTPError(
        url="https://api.deepseek.com/chat/completions", code=429,
        msg="Too Many Requests", hdrs=None, fp=None)


class _DeepSeekCase(unittest.TestCase):
    """Builds a real client with a fake key and a fake transport."""

    @classmethod
    def setUpClass(cls):
        from ver3.live_providers import deepseek
        cls.deepseek = deepseek

    def setUp(self):
        import os
        self._prior = os.environ.get(API_KEY_ENV)
        # A syntactically present credential so construction succeeds. It is
        # never sent, because nothing here reaches a socket.
        os.environ[API_KEY_ENV] = "test-key-not-a-credential"

    def tearDown(self):
        import os
        if self._prior is None:
            os.environ.pop(API_KEY_ENV, None)
        else:
            os.environ[API_KEY_ENV] = self._prior

    def request(self, **over):
        fields = {"purpose": "readiness", "stage_id": "s05",
                  "prompt_text": "a prompt", "max_output_tokens": 65536,
                  "deadline_s": 120.0, "temperature": 1.0,
                  "responsibility_id": "s05", "run_id": "readiness",
                  "stage_attempt": 1}
        fields.update(over)
        return GenerationRequest(**fields)

    def call(self, request, behaviour=_rate_limited, **client):
        """One `generate`, with the transport replaced and time not slept."""
        transport = _Transport(behaviour)
        provider = self.deepseek.DeepSeekProvider(backoff_s=0.0, **client)
        real_urlopen = self.deepseek.urllib.request.urlopen
        try:
            self.deepseek.urllib.request.urlopen = transport
            result = provider.generate(request)
        finally:
            self.deepseek.urllib.request.urlopen = real_urlopen
        return transport, result


class TestTheAttemptBudgetReachesTheTransport(_DeepSeekCase):
    """Counted at the wire, not read back from the config."""

    def test_the_client_default_really_does_retry(self):
        """Otherwise 'one attempt' below could be true because nothing retries,
        and the test would pass on a client that never had the defect."""
        transport, result = self.call(self.request(max_attempts=None))
        self.assertEqual(3, transport.attempts,
                         "the client's own default is no longer 3, so this "
                         "file's premise needs rechecking")
        self.assertIs(ExecutionStatus.PROVIDER_RATE_LIMIT,
                      result.execution_status)

    def test_a_campaign_asking_for_one_attempt_makes_exactly_one(self):
        """The repair. Before it, this made three transport attempts while the
        run record said one."""
        transport, _result = self.call(self.request(max_attempts=1))
        self.assertEqual(1, transport.attempts,
                         "the request asked for one attempt and the client "
                         "retried anyway; a paid run would cost three times "
                         "what its record claims")

    def test_the_failure_is_still_reported_honestly(self):
        """One attempt must not turn a provider failure into silence."""
        _transport, result = self.call(self.request(max_attempts=1))
        self.assertIs(ExecutionStatus.PROVIDER_RATE_LIMIT,
                      result.execution_status)
        self.assertIsNone(result.response)

    def test_an_intermediate_budget_is_honoured_exactly(self):
        """Not merely 'one works': the request's number is the number."""
        transport, _result = self.call(self.request(max_attempts=2))
        self.assertEqual(2, transport.attempts)

    def test_a_request_asking_for_zero_still_makes_one_call(self):
        """Zero attempts is a result without a call. Clamped rather than
        returning a failure nobody caused."""
        transport, result = self.call(self.request(max_attempts=0))
        self.assertEqual(1, transport.attempts)
        self.assertIsNotNone(result)

    def test_a_success_does_not_retry(self):
        def succeeds(_n):
            class _Resp:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *exc):
                    return False

                @staticmethod
                def read():
                    return json.dumps({
                        "choices": [{"message": {"content": "{}"},
                                     "finish_reason": "stop"}],
                        "model": "deepseek-v4-pro",
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                    }).encode("utf-8")
            return _Resp()

        transport, result = self.call(self.request(max_attempts=3), succeeds)
        self.assertEqual(1, transport.attempts)
        self.assertIs(ExecutionStatus.SUCCESS, result.execution_status)


class TestTheStageCarriesTheBudgetToTheProvider(_DeepSeekCase):
    """The seam between `GenerationSettings` and the request the client sees."""

    def test_the_stage_puts_the_settings_attempt_budget_on_the_request(self):
        from ver3.assy_v3.stages.base import GenerationSettings
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment

        seen = []

        class _Capture:
            def capabilities(self):
                from ver3.assy_v3.providers.interfaces import ProviderCapabilities
                return ProviderCapabilities(
                    provider_id="capture", model_id="none",
                    context_window_tokens=None, max_output_tokens=None,
                    supports_structured_output=True, supports_seed=True,
                    requests_per_minute=None, tokens_per_minute=None,
                    daily_quota_requests=None, notes="readiness")

            def generate(self, request, attempt_index=0):
                import time
                from ver3.assy_v3.providers.interfaces import GenerationResult
                seen.append(request)
                return GenerationResult(
                    execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE,
                    response=None, attempt_index=attempt_index,
                    started_at=time.time(), ended_at=time.time(),
                    from_cache=False, error_detail="readiness fixture")

        stage = S05Embodiment()
        stage.run(_Capture(), {stage.context_key: {}, stage.occupancy_key: {}},
                  None, "readiness",
                  settings=GenerationSettings(temperature=1.0,
                                              max_output_tokens=65536,
                                              max_attempts=1))
        self.assertEqual(1, len(seen))
        self.assertEqual(1, seen[0].max_attempts,
                         "the stage dropped the attempt budget, so the provider "
                         "would fall back to its own default")


class TestTheCampaignValuesAreOnTheWire(_DeepSeekCase):
    """The actual outgoing body, read from the intercepted request."""

    def body(self, **over):
        transport, _result = self.call(self.request(**over))
        self.assertTrue(transport.bodies, "nothing was sent")
        return transport.bodies[0]

    def test_the_model_in_the_body_is_the_current_documented_one(self):
        """`deepseek-chat` is no longer listed by the official API docs; the
        documented ids are the v4 pair. Asserted on the BODY, because the
        constant and what is sent are two different facts."""
        self.assertEqual("deepseek-v4-pro", self.body()["model"])

    def test_the_default_constant_agrees_with_the_body(self):
        self.assertEqual(self.deepseek.DEFAULT_MODEL, self.body()["model"])

    def test_the_temperature_on_the_wire_is_the_campaign_temperature(self):
        self.assertEqual(1.0, self.body()["temperature"])

    def test_the_token_budget_on_the_wire_is_the_campaign_budget(self):
        """65536 as the REQUEST, not merely as the provider's ceiling - the
        resolution layer clamps downward and never up."""
        self.assertEqual(65536, self.body()["max_tokens"])

    def test_the_budget_is_not_silently_clamped(self):
        self.assertLessEqual(65536, self.deepseek.MAX_OUTPUT_TOKENS_CEILING)

    def test_an_explicit_model_override_reaches_the_body(self):
        """So a later comparison needs no code change, and so this test is not
        passing merely because one constant equals another."""
        transport, _result = self.call(self.request(),
                                       model="deepseek-v4-flash")
        self.assertEqual("deepseek-v4-flash", transport.bodies[0]["model"])


class TestNoNetworkWasUsed(unittest.TestCase):
    """Said in the suite as well as in the report."""

    def test_this_module_never_calls_urlopen_itself(self):
        import ast
        tree = ast.parse(open(__file__).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "urlopen":
                # Only ever assigned to or restored, never invoked as a call.
                self.assertNotIsInstance(getattr(node, "parent", None), ast.Call)

    def test_the_fake_transport_opens_nothing(self):
        import inspect
        source = inspect.getsource(_Transport)
        self.assertNotIn("urlopen(", source)
        self.assertNotIn("socket", source)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
