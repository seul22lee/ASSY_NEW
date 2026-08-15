"""S9-B: a generation parameter cannot diverge silently, and a record must conform.

WHAT THIS FALSIFIES

Before S-9 the DeepSeek adapter had six parameters and roughly as many authority
rules. `max_output_tokens` came from the stage and was clamped. `temperature` came
from the adapter and ignored the stage, but said so. `top_p`, `seed` and
`response_schema` were accepted on the request and dropped without trace, and
`deadline_s` was overridden with only the effective value recorded.

Each test below states the invariant it falsifies. They share one shape: build a
request, run it through a FAKE TRANSPORT that captures the body, and compare what
was resolved against what was actually about to be sent. No paid call is made and
none is needed - payload and provenance semantics are decidable offline, and a test
that needed a live model to prove a local rule would be measuring the model.

NOT TESTED HERE
    Whether DeepSeek reasons well. That is S9-F and S9-G, and it is a different
    question from whether this repository tells the truth about what it asked.
"""
from __future__ import annotations

import io
import json
import os
import unittest
from typing import Any, Dict, Optional

import yaml

from . import _fixtures, _paths                                        # noqa: F401

import ver3.live_providers.deepseek as ds                              # noqa: E402
from ver3.assy_v3.providers import resolution as res                   # noqa: E402
from ver3.assy_v3.providers.interfaces import GenerationRequest        # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402

CONTRACT = os.path.join(_paths.CONTRACTS, "MODEL_RUN_RECORD_CONTRACT.yaml")


# ---------------------------------------------------------------------------
# Fake transport. Captures the body and the timeout; returns a canned response.
# ---------------------------------------------------------------------------
class _FakeHTTPResponse:
    def __init__(self, body: Dict[str, Any]) -> None:
        self._body = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False


class _Transport:
    """Stands in for urlopen. Records what the provider tried to send."""

    def __init__(self, served_model: str = "deepseek-chat",
                 content: str = '{"ok": true}',
                 finish_reason: str = "stop") -> None:
        self.served_model = served_model
        self.content = content
        self.finish_reason = finish_reason
        self.payload: Optional[Dict[str, Any]] = None
        self.timeout: Optional[float] = None
        self.calls = 0

    def __call__(self, http, timeout=None):
        self.calls += 1
        self.payload = json.loads(http.data.decode("utf-8"))
        self.timeout = timeout
        return _FakeHTTPResponse({
            "model": self.served_model,
            "choices": [{"message": {"content": self.content},
                         "finish_reason": self.finish_reason}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 3},
        })


class _FlakyTransport(_Transport):
    """Rate-limits the first N calls, then succeeds.

    Exercises the retry path so that provider-attempt identity can be checked on
    two attempts of ONE stage attempt - the case where an identity built only from
    the stage's own fields would collide.
    """

    def __init__(self, fail_times: int = 1, **kw) -> None:
        super().__init__(**kw)
        self.fail_times = fail_times

    def __call__(self, http, timeout=None):
        if self.calls < self.fail_times:
            self.calls += 1
            self.payload = json.loads(http.data.decode("utf-8"))
            self.timeout = timeout
            raise ds.urllib.error.HTTPError(
                "https://api.deepseek.com/chat/completions", 429, "Too Many Requests",
                {}, io.BytesIO(b"rate limited"))
        return super().__call__(http, timeout=timeout)


def a_request(**kw) -> GenerationRequest:
    """A stage-shaped request. The defaults mirror what `base.run` actually asks
    for, so these tests exercise the real requested values rather than tidy ones."""
    fields = dict(purpose="test", stage_id="s01", prompt_text="say something",
                  max_output_tokens=32000, deadline_s=120.0, temperature=0.0,
                  seed=7, run_id="run-1", stage_attempt=1)
    fields.update(kw)
    return GenerationRequest(**fields)


class _ProviderCase(unittest.TestCase):
    """Builds a provider against the fake transport, never the network."""

    def setUp(self) -> None:
        # A dummy credential so construction succeeds without ver3/.env, and so a
        # test can never accidentally spend quota with a real one.
        self._saved = os.environ.get(ds.API_KEY_VAR)
        os.environ[ds.API_KEY_VAR] = "test-key-not-a-credential"
        self._saved_urlopen = ds.urllib.request.urlopen

    def tearDown(self) -> None:
        ds.urllib.request.urlopen = self._saved_urlopen
        if self._saved is None:
            os.environ.pop(ds.API_KEY_VAR, None)
        else:
            os.environ[ds.API_KEY_VAR] = self._saved

    def run_once(self, provider, request, transport=None):
        transport = transport or _Transport()
        ds.urllib.request.urlopen = transport
        result = provider.generate(request)
        return result, transport, provider.records[-1]


# =====================================================================
# S9-I7 — requested, override, effective and sent are all distinguishable
# =====================================================================
class TestParameterAuthority(_ProviderCase):

    def test_S9B_01_experiment_temperature_override_reaches_the_wire(self):
        """FALSIFIES S9-I7: an override that does not change what is sent.

        The repeated-trial protocol depends on this: the stage asks for 0.0 and
        the experiment must be able to sample at 0.7.
        """
        p = ds.DeepSeekProvider(temperature=0.7)
        _r, transport, rec = self.run_once(p, a_request(temperature=0.0))
        self.assertEqual(0.7, transport.payload["temperature"])
        self.assertEqual(0.7, rec["request"]["parameters"]["temperature"])
        self.assertEqual(0.7, rec["determinism"]["temperature_actually_sent"])
        self.assertEqual("SENT_AS_OVERRIDDEN",
                         rec["request"]["parameter_resolution"]["temperature"]["status"])

    def test_S9B_02_the_overridden_stage_value_stays_visible(self):
        """FALSIFIES S9-I7: an override that erases what it overrode.

        A record that shows only 0.7 cannot answer "what did the stage ask for",
        and a fixture promoted from it could not either.
        """
        p = ds.DeepSeekProvider(temperature=0.7)
        _r, _t, rec = self.run_once(p, a_request(temperature=0.0))
        entry = rec["request"]["parameter_resolution"]["temperature"]
        self.assertEqual(0.0, entry["requested"])
        self.assertEqual(0.7, entry["override"])
        self.assertEqual(0.7, entry["effective"])
        self.assertEqual(0.0, rec["determinism"]["temperature_requested_by_stage"])

    def test_S9B_03_no_override_means_the_stage_value_stands(self):
        """A provider built with no temperature states no opinion.

        The old default was 1.0, which overrode every stage request without
        anyone writing an override - the invisible authority S9-B removes.

        `None` means EXACTLY "no experiment opinion". It must not become a null on
        the wire, must not drop a parameter the API expects, and must not replace
        the stage's value with a provider default under another name. All three
        would be the same defect wearing different clothes.
        """
        p = ds.DeepSeekProvider()
        _r, transport, rec = self.run_once(p, a_request(temperature=0.0))
        # Present, and equal to what the stage asked for - not absent, not null.
        self.assertIn("temperature", transport.payload)
        self.assertIsNotNone(transport.payload["temperature"])
        self.assertEqual(0.0, transport.payload["temperature"])
        entry = rec["request"]["parameter_resolution"]["temperature"]
        self.assertEqual((0.0, None, 0.0, "SENT_AS_REQUESTED"),
                         (entry["requested"], entry["override"], entry["effective"],
                          entry["status"]))
        self.assertEqual(0.0, rec["determinism"]["temperature_actually_sent"])

    def test_S9B_03b_a_non_default_stage_temperature_also_survives(self):
        """The stage value carries through whatever it is - 0.0 is not special.

        A rule that only worked for the falsy value would be indistinguishable
        from no rule at all on a value that happens to be zero.
        """
        for asked in (0.3, 1.0, 1.5):
            p = ds.DeepSeekProvider()
            _r, transport, rec = self.run_once(p, a_request(temperature=asked))
            self.assertEqual(asked, transport.payload["temperature"], asked)
            self.assertEqual(asked, rec["request"]["parameters"]["temperature"], asked)
            self.assertEqual("SENT_AS_REQUESTED",
                             rec["request"]["parameter_resolution"]
                                ["temperature"]["status"], asked)

    def test_S9B_04_top_p_cannot_be_silently_ignored(self):
        """FALSIFIES S9-I7: `top_p` accepted on the request and dropped."""
        # Requested by the stage, no override: it must reach the wire.
        p = ds.DeepSeekProvider()
        _r, transport, rec = self.run_once(p, a_request(top_p=0.9))
        self.assertEqual(0.9, transport.payload["top_p"])
        self.assertEqual("SENT_AS_REQUESTED",
                         rec["request"]["parameter_resolution"]["top_p"]["status"])
        # Overridden by the experiment: the override wins and both are visible.
        p2 = ds.DeepSeekProvider(top_p=0.5)
        _r2, t2, rec2 = self.run_once(p2, a_request(top_p=0.9))
        self.assertEqual(0.5, t2.payload["top_p"])
        entry = rec2["request"]["parameter_resolution"]["top_p"]
        self.assertEqual((0.9, 0.5), (entry["requested"], entry["override"]))
        # Asked for by nobody: absent from the body, and recorded as not asked for.
        p3 = ds.DeepSeekProvider()
        _r3, t3, rec3 = self.run_once(p3, a_request(top_p=None))
        self.assertNotIn("top_p", t3.payload)
        self.assertEqual("NOT_SENT_NOT_REQUESTED",
                         rec3["request"]["parameter_resolution"]["top_p"]["status"])

    def test_S9B_05_an_unsupported_seed_is_never_reported_as_honoured(self):
        """FALSIFIES S9-I7 and the determinism rule: inventing determinism.

        The stage asks for seed 7. DeepSeek accepts no seed. Both facts must
        survive: the request is retained, nothing is sent, and the record says
        NOT_SUPPORTED rather than the weaker UNKNOWN.
        """
        p = ds.DeepSeekProvider()
        _r, transport, rec = self.run_once(p, a_request(seed=7))
        self.assertNotIn("seed", transport.payload)
        entry = rec["request"]["parameter_resolution"]["seed"]
        self.assertEqual(7, entry["requested"])
        self.assertIsNone(entry["effective"])
        self.assertEqual("NOT_SENT_UNSUPPORTED", entry["status"])
        self.assertFalse(entry["sent"])
        self.assertEqual("NOT_SUPPORTED", rec["determinism"]["seed_honoured"])
        self.assertEqual(7, rec["determinism"]["seed_requested_by_stage"])
        # And the declaration the resolver reads is the one capabilities reports.
        self.assertEqual(ds.SUPPORTS_SEED, p.capabilities().supports_seed)

    def test_S9B_06_response_format_and_schema_are_different_facts(self):
        """FALSIFIES S9-I7: a schema accepted and silently discarded.

        The provider can transmit a FORMAT MODE. It cannot transmit a SCHEMA. A
        record that showed neither, or conflated them, would leave a reader unable
        to tell whether parse success came from the model or from enforcement.
        """
        p = ds.DeepSeekProvider(json_object_mode=True)
        _r, transport, rec = self.run_once(
            p, a_request(response_schema={"type": "object"}))
        self.assertEqual({"type": "json_object"}, transport.payload["response_format"])
        pr = rec["request"]["parameter_resolution"]
        self.assertEqual("json_object", pr["response_format"]["effective"])
        # The schema was asked for, is not on the wire, and says where it is honoured.
        self.assertEqual("NOT_SENT_PARSER_SIDE", pr["response_schema"]["status"])
        self.assertFalse(pr["response_schema"]["sent"])
        # Turning the mode off removes it from the body rather than sending "text".
        p2 = ds.DeepSeekProvider(json_object_mode=False)
        _r2, t2, _rec2 = self.run_once(p2, a_request())
        self.assertNotIn("response_format", t2.payload)

    def test_S9B_07_requested_and_effective_timeout_cannot_be_confused(self):
        """FALSIFIES S9-I7: an adapter timeout that overrides invisibly.

        Previously only the effective value was recorded, so a run could not say
        whether 120s was the stage's deadline or the adapter's override.
        """
        # No override: the stage's deadline is what the connection uses.
        p = ds.DeepSeekProvider()
        _r, transport, rec = self.run_once(p, a_request(deadline_s=120.0))
        self.assertEqual(120.0, transport.timeout)
        entry = rec["request"]["parameter_resolution"]["deadline_s"]
        self.assertEqual((120.0, None, "SENT_AS_REQUESTED"),
                         (entry["requested"], entry["override"], entry["status"]))
        # Override: the connection changes AND the stage's value survives.
        p2 = ds.DeepSeekProvider(timeout_s=30.0)
        _r2, t2, rec2 = self.run_once(p2, a_request(deadline_s=120.0))
        self.assertEqual(30.0, t2.timeout)
        e2 = rec2["request"]["parameter_resolution"]["deadline_s"]
        self.assertEqual((120.0, 30.0, 30.0),
                         (e2["requested"], e2["override"], e2["effective"]))
        self.assertEqual(30.0, rec2["request"]["deadline_s"])
        # A timeout is not a payload field; the model must not be sent one.
        self.assertNotIn("deadline_s", t2.payload)
        self.assertEqual("transport", e2["channel"])

    def test_S9B_08_max_token_clamping_is_truthful(self):
        """FALSIFIES S9-I7: a silently reduced cap.

        And it follows the SAME rule as everything else - requested, then a
        transport normalization that is recorded - rather than its own.
        """
        p = ds.DeepSeekProvider()
        _r, transport, rec = self.run_once(p, a_request(max_output_tokens=32000))
        self.assertEqual(ds.MAX_OUTPUT_TOKENS_CEILING, transport.payload["max_tokens"])
        self.assertEqual(32000, rec["request"]["max_output_tokens_clamped_from"])
        entry = rec["request"]["parameter_resolution"]["max_output_tokens"]
        self.assertEqual((32000, ds.MAX_OUTPUT_TOKENS_CEILING, "SENT_AS_CLAMPED"),
                         (entry["requested"], entry["effective"], entry["status"]))
        # Under the ceiling nothing is clamped and nothing claims to have been.
        p2 = ds.DeepSeekProvider()
        _r2, t2, rec2 = self.run_once(p2, a_request(max_output_tokens=100))
        self.assertEqual(100, t2.payload["max_tokens"])
        self.assertIsNone(rec2["request"]["max_output_tokens_clamped_from"])

    def test_S9B_09_requested_and_served_model_stay_distinguishable(self):
        """FALSIFIES PR-04: a substitution recorded as though it were the request.

        The live probe in S9-A observed `deepseek-chat` served as
        `deepseek-v4-flash`. The served name is whatever the provider says at
        runtime and is never hard-coded here.
        """
        p = ds.DeepSeekProvider(model="deepseek-chat")
        _r, transport, rec = self.run_once(
            p, a_request(), _Transport(served_model="some-other-model"))
        self.assertEqual("deepseek-chat", transport.payload["model"])
        self.assertEqual("deepseek-chat", rec["model_id_requested"])
        self.assertEqual("some-other-model", rec["model_id_served"])
        self.assertEqual("some-other-model", rec["model_version_string"])
        self.assertIn("recorded rather", rec["model_substitution"])
        # No substitution: the field asserts that none happened.
        p2 = ds.DeepSeekProvider(model="deepseek-chat")
        _r2, _t2, rec2 = self.run_once(
            p2, a_request(), _Transport(served_model="deepseek-chat"))
        self.assertIsNone(rec2["model_substitution"])


# =====================================================================
# S9-I5 — the record conforms to the contract that governs it
# =====================================================================
class TestRecordConformance(_ProviderCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open(CONTRACT) as fh:
            cls.contract = yaml.safe_load(fh)

    def test_S9B_10_the_record_carries_every_required_contract_field(self):
        """FALSIFIES S9-I5: a record called contract-shaped while fields are absent.

        S9-A found five required fields missing, which left a record unable to say
        which run or attempt produced it. Read from the contract rather than
        listed here, so a newly required field fails this test instead of being
        quietly unimplemented.
        """
        p = ds.DeepSeekProvider(temperature=0.7)
        _r, _t, rec = self.run_once(p, a_request())
        required = set(self.contract["model_run_record"]["required_fields"])
        self.assertEqual(set(), required - set(rec),
                         "required MODEL_RUN_RECORD fields are absent")
        # The subfields the contract names for the compound sections.
        fs = self.contract["model_run_record"]["field_semantics"]
        for section in ("request", "response", "determinism"):
            for sub in fs[section]["required_subfields"]:
                self.assertIn(sub, rec[section], "%s.%s" % (section, sub))

    def test_S9B_11_run_and_attempt_identity_are_the_callers(self):
        """A record must be tied back to the run and attempt that produced it."""
        p = ds.DeepSeekProvider()
        _r, _t, rec = self.run_once(
            p, a_request(run_id="live-BM-001-t3", stage_attempt=2, stage_id="s02"))
        self.assertEqual("live-BM-001-t3", rec["run_id"])
        self.assertEqual(2, rec["stage_attempt"])
        self.assertEqual("s02", rec["stage_id"])
        # Derived, not random: the same attempt names the same record twice.
        self.assertEqual("live-BM-001-t3|s02|sa2|a1", rec["model_run_id"])

    def test_S9B_12_a_caller_without_run_context_reports_absence(self):
        """NOT_REPORTED rather than a fabricated identity."""
        p = ds.DeepSeekProvider()
        _r, _t, rec = self.run_once(p, a_request(run_id=None, stage_attempt=None))
        self.assertEqual("NOT_REPORTED", rec["run_id"])
        self.assertEqual(1, rec["stage_attempt"])

    def test_S9B_12b_a_retry_never_masquerades_as_its_predecessor(self):
        """FALSIFIES the contract's retry rule: one provider attempt overwriting
        another, or two attempts sharing an identity.

        A single logical stage attempt can produce several PROVIDER attempts when
        a rate limit is retried. The stage-attempt identity is the same for all of
        them, so identity that stopped there would make two calls indistinguishable
        - and PR-02 requires that every attempt be recorded separately.

        Deterministic, not random: the components already in hand (run, stage,
        stage attempt, provider attempt) name the attempt exactly, and a UUID
        would make the same attempt unrecognisable across two readings of it.
        """
        p = ds.DeepSeekProvider(backoff_s=0.0, max_attempts=3)
        ds.urllib.request.urlopen = _FlakyTransport(fail_times=1)
        result = p.generate(a_request(run_id="run-7", stage_id="s02",
                                      stage_attempt=2))

        self.assertIs(ExecutionStatus.SUCCESS, result.execution_status)
        # Both attempts survive. The failed one is evidence, not noise.
        self.assertEqual(2, len(p.records))
        first, second = p.records
        self.assertEqual("PROVIDER_RATE_LIMIT", first["execution_status"])
        self.assertEqual("SUCCESS", second["execution_status"])

        # Same logical attempt on every axis the stage knows about ...
        for field in ("run_id", "stage_id", "stage_attempt"):
            self.assertEqual(first[field], second[field], field)
        # ... different provider attempt, therefore different identity.
        self.assertNotEqual(first["attempt_index"], second["attempt_index"])
        self.assertNotEqual(first["model_run_id"], second["model_run_id"])
        self.assertEqual({"run-7|s02|sa2|a1", "run-7|s02|sa2|a2"},
                         {first["model_run_id"], second["model_run_id"]})

    def test_S9B_12c_the_same_attempt_names_the_same_record_twice(self):
        """The other half: determinism. Reading one attempt twice must not look
        like two attempts."""
        p1 = ds.DeepSeekProvider()
        _r1, _t1, rec1 = self.run_once(p1, a_request(run_id="r", stage_attempt=1))
        p2 = ds.DeepSeekProvider()
        _r2, _t2, rec2 = self.run_once(p2, a_request(run_id="r", stage_attempt=1))
        self.assertEqual(rec1["model_run_id"], rec2["model_run_id"])

    def test_S9B_13_the_stage_driver_supplies_run_and_attempt(self):
        """The identity has to arrive from the stage, or the record cannot carry it.

        Asserted on the real driver rather than on a hand-built request, because
        the defect S9-A found was precisely that the caller never passed them.
        """
        import ast
        with open(os.path.join(_paths.ASSY_V3, "stages", "base.py")) as fh:
            tree = ast.parse(fh.read())
        kwargs = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == \
                    "GenerationRequest":
                kwargs = {k.arg for k in node.keywords}
        self.assertIn("run_id", kwargs)
        self.assertIn("stage_attempt", kwargs)


# =====================================================================
# S9-I7 — the body cannot disagree with the resolution
# =====================================================================
class TestPayloadAgreement(_ProviderCase):

    def test_S9B_14_a_body_contradicting_its_resolution_is_caught(self):
        """FALSIFIES S9-I7: effective provenance disagreeing with what was sent.

        The provider builds its body FROM the resolution, so agreement is
        structural. This proves the detector actually detects, by handing
        `verify_payload` the mismatches a future hand-built field would create.
        """
        p = ds.DeepSeekProvider(temperature=0.7)
        resolution = p.resolve(a_request(temperature=0.0, top_p=0.9))
        good = {"messages": [], "stream": False}
        good.update(resolution.payload_fragment())
        self.assertEqual([], res.verify_payload(resolution, good))

        # A value changed after resolution.
        bad = dict(good, temperature=0.0)
        self.assertTrue(any("temperature" in m
                            for m in res.verify_payload(resolution, bad)))
        # A resolved parameter dropped from the body.
        missing = {k: v for k, v in good.items() if k != "top_p"}
        self.assertTrue(any("top_p" in m
                            for m in res.verify_payload(resolution, missing)))
        # A parameter the resolution says was NOT sent, smuggled in.
        smuggled = dict(good, seed=7)
        self.assertTrue(any("seed" in m
                            for m in res.verify_payload(resolution, smuggled)))

    def test_S9B_15_the_provider_refuses_to_send_a_contradicting_body(self):
        """A malformed request raises; it never becomes an ExecutionStatus.

        The status vocabulary is STATUS_SEMANTICS' and describes how a call
        behaved. "This code built the wrong body" is not a way a call behaved, and
        giving it a status would corrupt the vocabulary S-8 froze.
        """
        p = ds.DeepSeekProvider(temperature=0.7)
        original = res.ParameterResolution.payload_fragment

        def corrupted(self):                       # drops a resolved parameter
            frag = original(self)
            frag.pop("temperature", None)
            return frag

        res.ParameterResolution.payload_fragment = corrupted
        try:
            ds.urllib.request.urlopen = _Transport()
            with self.assertRaises(ValueError) as caught:
                p.generate(a_request())
            self.assertIn("temperature", str(caught.exception))
        finally:
            res.ParameterResolution.payload_fragment = original

    def test_S9B_15b_the_invariant_error_is_not_converted_into_a_status(self):
        """FALSIFIES the failure-attribution rule: an internal defect wearing an
        engineering status.

        `base.run` converts exceptions from the RESPONSE-HANDLING block into
        RESPONSE_PARSE_FAILURE and SCHEMA_FAILURE - both statements about the
        model's answer. If `provider.generate` were called inside either block, a
        body that contradicts its own resolution would be reported as the model
        having produced a bad response, which is the precise inversion S9-I11
        forbids: our defect blamed on the design.

        Checked structurally, because the property is about where the call sits.
        """
        import ast
        with open(os.path.join(_paths.ASSY_V3, "stages", "base.py")) as fh:
            tree = ast.parse(fh.read())

        def generate_calls(node):
            return [n for n in ast.walk(node)
                    if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "generate"]

        run_fn = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "run")
        self.assertEqual(1, len(generate_calls(run_fn)),
                         "expected exactly one provider.generate call in run()")
        for handler in [n for n in ast.walk(run_fn) if isinstance(n, ast.Try)]:
            self.assertEqual([], generate_calls(handler),
                             "provider.generate sits inside a try block whose "
                             "handler assigns an ExecutionStatus")

    def test_S9B_16_every_resolved_parameter_declares_where_it_went(self):
        """No parameter may be resolved into silence.

        A parameter with no channel and no status is how the previous adapter lost
        three of them.
        """
        p = ds.DeepSeekProvider(temperature=0.7, top_p=0.5, timeout_s=30.0)
        resolution = p.resolve(a_request(response_schema={"type": "object"}))
        names = {x.name for x in resolution.parameters}
        self.assertEqual({"model", "temperature", "top_p", "max_output_tokens",
                          "deadline_s", "seed", "response_format", "response_schema"},
                         names)
        for entry in resolution.parameters:
            self.assertIn(entry.channel, (res.PAYLOAD, res.TRANSPORT, res.NOWHERE))
            self.assertTrue(entry.status, entry.name)
            if entry.sent:
                self.assertNotEqual(res.NOWHERE, entry.channel, entry.name)
            if not entry.sent:
                self.assertIn(entry.status, (res.NOT_SENT_UNSUPPORTED,
                                             res.NOT_SENT_NOT_REQUESTED,
                                             res.NOT_SENT_PARSER_SIDE), entry.name)


# =====================================================================
# The failure boundaries S9-B must not blur
# =====================================================================
class TestFailureAttribution(_ProviderCase):

    def test_S9B_17_a_truncated_response_is_recorded_and_never_parsed(self):
        """PR-05 still holds after the rewrite."""
        p = ds.DeepSeekProvider()
        result, _t, rec = self.run_once(
            p, a_request(), _Transport(content='{"partial": ', finish_reason="length"))
        self.assertIs(ExecutionStatus.RESPONSE_TRUNCATED, result.execution_status)
        self.assertTrue(rec["response"]["truncated"])
        self.assertEqual('{"partial": ', rec["response"]["raw_text"])

    def test_S9B_18_no_credential_reaches_the_record(self):
        """PR-11. The key is in the environment for these tests, so a leak here
        would be a real leak."""
        p = ds.DeepSeekProvider(temperature=0.7)
        _r, _t, rec = self.run_once(p, a_request())
        self.assertNotIn("test-key-not-a-credential", json.dumps(rec))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
