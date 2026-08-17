"""DeepSeek chat-completions as a live ModelProvider.

An INDEPENDENT provider. Its value to this repository is precisely that it is
not the agent operating the repository: it cannot see the validators, the
Oracle packs or the expected answers, so a response it produces is evidence
about the prompt-plus-knowledge-plus-parser implementation rather than about the
author of that implementation.

WHAT IT GUARANTEES
    * A provider condition never becomes a statement about the design. Every
      failure returns a GenerationResult carrying a specific PROVIDER_* status
      (PR-01); nothing here raises on a provider condition.
    * Retries are bounded and every attempt is recorded separately (PR-02).
    * Truncation is read from the provider's finish reason, never guessed from
      the content, and a truncated response is never parsed (PR-05).
    * Model substitution is recorded. DeepSeek serves an alias, so the model it
      returns is compared with the one asked for and any difference is reported
      through served_model_id and fallback_reason (PR-04).
    * Credentials are read from the environment and never written to a record
      (PR-11). The Authorization header is built inside the call and is not
      retained anywhere.
    * No hidden chain of thought is stored. Reasoning-style models return a
      `reasoning_content` field; it is dropped, and only the fact that one was
      present is recorded.

WHAT IT DOES NOT DO
    It does not repair responses. No fence stripping, no brace balancing, no
    "extract the first JSON object" salvage. A response that will not parse is a
    RESPONSE_PARSE_FAILURE, because a repaired response measures the repair.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from ver3.assy_v3.providers.interfaces import (GenerationRequest, GenerationResponse,
                                               GenerationResult, ProviderCapabilities)
from ver3.assy_v3.providers.replay_integrity import LIVE
from ver3.assy_v3.providers.resolution import (ExperimentOverrides, ParameterResolution,
                                               resolve, verify_payload)
from ver3.assy_v3.providers.status import ExecutionStatus

from .env import require

#: The credential's variable. Read from the environment and nowhere else.
API_KEY_VAR = "DEEPSEEK_API_KEY"

DEFAULT_BASE_URL = "https://api.deepseek.com"

#: The model the paid diagnostic will actually call.
#:
#: Was `deepseek-chat`, which the official API documentation no longer lists
#: (checked 2026-08-17 against api-docs.deepseek.com). The documented model ids
#: are `deepseek-v4-flash` and `deepseek-v4-pro`, both of which resolve to their
#: current dated build - the docs state the calling method is unchanged and the
#: bare name reaches the latest version, so pinning a dated id here would freeze
#: the campaign to a build that moves on without it.
#:
#: PRO rather than FLASH. The diagnostic asks for multi-stage engineering
#: reasoning - requirement interpretation through to a construction program - at
#: a 65536-token output budget. Flash is the faster, cheaper tier; choosing it
#: to save money on the run whose entire purpose is to find out whether natural
#: model output can traverse the pipeline would make a capability answer that is
#: really a tier answer.
#:
#: Overridable by DEEPSEEK_MODEL, so a later comparison needs no code change.
DEFAULT_MODEL = "deepseek-v4-pro"

#: The output ceiling this client will request. A request above it is clamped, and
#: the clamp is recorded, because a silently reduced cap produces a truncation the
#: caller cannot explain.
#:
#: WAS 8192, AND THAT WAS THE HARM IT EXISTED TO PREVENT. The stage asks for
#: 32000; the clamp cut every request to 8192, so any responsibility whose answer
#: is larger truncated - which is exactly what happened to S02 on the first S9-E
#: regeneration attempt, at ~29k characters with finish_reason "length". The
#: pipeline behaved correctly throughout: it read the truncation from the finish
#: reason, refused to parse it, and recorded RESPONSE_TRUNCATED. What was wrong
#: was the declaration.
#:
#: Verified against the live endpoint before changing: 8192, 16384, 32768 and
#: 65536 are all accepted by the served model. A declared capability that
#: understates the provider is not conservative - it manufactures truncation and
#: then reports it as the model's failure.
MAX_OUTPUT_TOKENS_CEILING = 65536

#: DeepSeek's chat-completions API accepts no seed parameter. Declared here so the
#: resolution boundary can record a requested seed as UNSUPPORTED rather than
#: erasing it, and so `capabilities()` and the resolver cannot drift apart.
SUPPORTS_SEED = False

#: It accepts a response FORMAT MODE (`{"type": "json_object"}`) but no schema. The
#: shape itself is stated by the prompt and enforced by the parser, which is a
#: different mechanism and is recorded as one.
SUPPORTS_RESPONSE_SCHEMA = False

#: HTTP status -> execution status. Each maps to a DIFFERENT operational
#: response: a rate limit can be waited out, an exhausted quota cannot.
_HTTP_STATUS = {
    400: ExecutionStatus.MODEL_CAPABILITY_FAILURE,
    401: ExecutionStatus.PROVIDER_UNAVAILABLE,
    402: ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED,
    403: ExecutionStatus.PROVIDER_UNAVAILABLE,
    404: ExecutionStatus.PROVIDER_UNAVAILABLE,
    422: ExecutionStatus.MODEL_CAPABILITY_FAILURE,
    429: ExecutionStatus.PROVIDER_RATE_LIMIT,
    500: ExecutionStatus.PROVIDER_UNAVAILABLE,
    502: ExecutionStatus.PROVIDER_UNAVAILABLE,
    503: ExecutionStatus.PROVIDER_UNAVAILABLE,
    504: ExecutionStatus.PROVIDER_TIMEOUT,
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DeepSeekProvider:
    """Live DeepSeek provider.

    Parameters that matter for evidence:

    temperature
        The whole point of the repeated-trial protocol. Recorded per attempt as
        the value actually SENT, which is not assumed equal to the value the
        stage asked for: the stage driver currently hard-codes 0.0, and a run
        that silently used a different value would be unreproducible.

    json_object_mode
        DeepSeek's structured-output mode. A format constraint, not a prompt
        change - the prompt already asks for a single JSON object. Recorded, so
        a reader can tell whether parse success came from the model or from the
        provider's format enforcement.
    """

    provider_id = "deepseek"
    #: DECLARED. The orchestration reads this rather than inferring liveness from
    #: which script started the run, which is what made a full-live claim a
    #: statement about a filename.
    response_source = LIVE

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None,
                 temperature: Optional[float] = None, top_p: Optional[float] = None,
                 json_object_mode: bool = True, max_attempts: int = 3,
                 backoff_s: float = 4.0, timeout_s: Optional[float] = None) -> None:
        # Presence is checked here so a misconfiguration fails immediately and
        # by name, rather than as an authorization error mid-run.
        self._api_key = require(API_KEY_VAR)
        self.model = model or os.environ.get("DEEPSEEK_MODEL") or DEFAULT_MODEL
        self.base_url = (base_url or os.environ.get("DEEPSEEK_BASE_URL")
                         or DEFAULT_BASE_URL).rstrip("/")
        self.temperature = temperature
        self.top_p = top_p
        self.json_object_mode = json_object_mode
        self.max_attempts = max_attempts
        self.backoff_s = backoff_s
        self.timeout_s = timeout_s
        #: One ModelRunRecord per attempt, in order. The caller drains this.
        self.records: List[Dict[str, Any]] = []

    @property
    def overrides(self) -> ExperimentOverrides:
        """What THIS EXPERIMENT decides, separated from what a stage asks for.

        These are the constructor arguments, named for what they are. `temperature`
        defaults to None rather than to a number, so a provider built with no
        argument states no opinion and the stage's request stands — a numeric
        default would be an override nobody wrote down, which is the defect S9-B
        exists to remove.
        """
        return ExperimentOverrides(
            model=self.model, temperature=self.temperature, top_p=self.top_p,
            deadline_s=self.timeout_s,
            response_format="json_object" if self.json_object_mode else None)

    def resolve(self, request: GenerationRequest) -> ParameterResolution:
        """Stage request + experiment overrides -> the effective specification.

        Resolved BEFORE the transport boundary, so the provider never reinterprets
        a request after receiving it; `_attempt` builds its body from the result
        and from nothing else.
        """
        return resolve(request, self.overrides,
                       max_output_tokens_ceiling=MAX_OUTPUT_TOKENS_CEILING,
                       supports_seed=SUPPORTS_SEED,
                       supports_response_schema=SUPPORTS_RESPONSE_SCHEMA)

    # ------------------------------------------------------------ capability
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_id=self.provider_id, model_id=self.model,
            context_window_tokens=65536, max_output_tokens=MAX_OUTPUT_TOKENS_CEILING,
            supports_structured_output=True,
            # DeepSeek accepts no seed parameter. Declaring support would be a
            # determinism claim the provider does not make. Read from the same
            # constant the resolver uses, so the two cannot disagree.
            supports_seed=SUPPORTS_SEED,
            requests_per_minute=None, tokens_per_minute=None, daily_quota_requests=None,
            notes=("Live HTTP provider. Serves a model alias, so the served model "
                   "is recorded per call and may differ from the one requested."))

    # ---------------------------------------------------------------- driver
    def generate(self, request: GenerationRequest, attempt_index: int = 0) -> GenerationResult:
        """Bounded retry over one logical call. Never raises on a provider
        condition; every attempt leaves its own record."""
        last: Optional[GenerationResult] = None
        waited = 0.0
        # THE REQUEST DECIDES, and the client is the fallback. A provider built
        # once and reused across a run otherwise imposes one retry policy on
        # every responsibility, and a diagnostic that means to make exactly one
        # attempt cannot say so - it could only construct a second client, while
        # the attempt budget it recorded governed nothing.
        #
        # Clamped to at least one: a request asking for zero attempts is asking
        # for a result without a call, and returning None here would be a
        # provider failure nobody caused.
        attempts = self.max_attempts
        if request.max_attempts is not None:
            attempts = max(1, int(request.max_attempts))
        for attempt in range(1, attempts + 1):
            result = self._attempt(request, attempt, waited)
            last = result
            if result.execution_status is ExecutionStatus.SUCCESS:
                return result
            # A bounded backoff over conditions that can plausibly clear. Never
            # a retry on a response we simply did not like - that is resampling.
            if result.execution_status not in (ExecutionStatus.PROVIDER_RATE_LIMIT,
                                               ExecutionStatus.PROVIDER_UNAVAILABLE,
                                               ExecutionStatus.PROVIDER_TIMEOUT):
                return result
            if attempt < attempts:
                wait = self.backoff_s * attempt
                waited += wait
                time.sleep(wait)
        return last                                     # type: ignore[return-value]

    # --------------------------------------------------------------- one try
    def _attempt(self, request: GenerationRequest, attempt: int,
                 retry_wait_s: float) -> GenerationResult:
        # EVERY generation parameter is resolved here, before the transport
        # boundary, and the body is built from the resolution rather than from
        # this object's attributes. That is what makes "what was sent" and "what
        # was recorded" the same fact instead of two hopefully-equal ones.
        resolution = self.resolve(request)

        payload: Dict[str, Any] = {
            "messages": [{"role": "user", "content": request.prompt_text}],
            "stream": False,
        }
        payload.update(resolution.payload_fragment())

        # A body that contradicts its own resolution is a malformed request, which
        # the provider interface says is the one thing `generate` may raise on. It
        # is deliberately NOT an ExecutionStatus: the status vocabulary is the
        # contract's and describes how a call behaved, not how this code is wrong.
        mismatches = verify_payload(resolution, payload)
        if mismatches:
            raise ValueError("payload contradicts the resolved parameters: "
                             + "; ".join(mismatches))

        max_tokens = resolution.effective("max_output_tokens")
        timeout = resolution.transport_timeout() or 120.0
        started = time.time()

        # The header is built here and referenced nowhere else. It is not stored
        # on the instance, not put in the record, and not included in any error.
        http = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self._api_key})
        # The requested model is read back from the resolution rather than from
        # self.model, so substitution is compared against what was actually sent.
        requested_model = resolution.effective("model")

        status = ExecutionStatus.SUCCESS
        error_detail: Optional[str] = None
        body: Optional[Dict[str, Any]] = None
        try:
            with urllib.request.urlopen(http, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            status = _HTTP_STATUS.get(exc.code, ExecutionStatus.PROVIDER_UNAVAILABLE)
            try:
                detail = exc.read().decode("utf-8", "replace")[:500]
            except Exception:                                        # noqa: BLE001
                detail = ""
            error_detail = "HTTP %s: %s" % (exc.code, detail)
        except urllib.error.URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            status = (ExecutionStatus.PROVIDER_TIMEOUT if "timed out" in reason.lower()
                      else ExecutionStatus.PROVIDER_UNAVAILABLE)
            error_detail = "URLError: %s" % reason[:300]
        except Exception as exc:                                     # noqa: BLE001
            status = ExecutionStatus.PROVIDER_TIMEOUT if isinstance(exc, TimeoutError) \
                else ExecutionStatus.PROVIDER_UNAVAILABLE
            error_detail = "%s: %s" % (type(exc).__name__, str(exc)[:300])

        ended = time.time()
        response: Optional[GenerationResponse] = None
        served: Optional[str] = None
        fallback: Optional[str] = None
        usage: Dict[str, Any] = {"input_tokens": "NOT_REPORTED",
                                 "output_tokens": "NOT_REPORTED"}
        finish_reason = ""
        truncated = False
        raw_text = ""
        had_reasoning = False

        if body is not None:
            choices = body.get("choices") or []
            if not choices:
                status = ExecutionStatus.PROVIDER_UNAVAILABLE
                error_detail = "response contained no choices"
            else:
                message = choices[0].get("message") or {}
                raw_text = message.get("content") or ""
                # Hidden chain of thought is DISCARDED here and never leaves this
                # function. Only its presence is recorded.
                had_reasoning = bool(message.get("reasoning_content"))
                finish_reason = choices[0].get("finish_reason") or ""
                truncated = finish_reason == "length"
                served = body.get("model")
                u = body.get("usage") or {}
                usage = {
                    "input_tokens": u.get("prompt_tokens", "NOT_REPORTED"),
                    "output_tokens": u.get("completion_tokens", "NOT_REPORTED"),
                    "cached_input_tokens": u.get("prompt_cache_hit_tokens"),
                }
                if served and served != requested_model:
                    fallback = ("provider served %r for requested %r; recorded rather "
                                "than assumed equivalent" % (served, requested_model))
                if truncated:
                    # PR-05: never parsed, never repaired, reported as its own status.
                    status = ExecutionStatus.RESPONSE_TRUNCATED
                elif not raw_text.strip():
                    status = ExecutionStatus.PROVIDER_UNAVAILABLE
                    error_detail = "provider returned empty content"
                response = GenerationResponse(
                    raw_text=raw_text, finish_reason=finish_reason, truncated=truncated,
                    input_tokens=_int_or_none(usage.get("input_tokens")),
                    output_tokens=_int_or_none(usage.get("output_tokens")),
                    cached_input_tokens=_int_or_none(usage.get("cached_input_tokens")),
                    served_model_id=served)

        # ------------------------------------------------------ the record
        # Shaped by ver3/contracts/MODEL_RUN_RECORD_CONTRACT.yaml. No credential
        # appears in it; the only strings taken from the call are the prompt, the
        # response and the provider's own error text.
        run_id = request.run_id or "NOT_REPORTED"
        stage_attempt = request.stage_attempt if request.stage_attempt is not None else 1
        self.records.append({
            # ---- identity (MODEL_RUN_RECORD_CONTRACT required fields) --------
            # model_run_id is derived rather than random so that re-running the
            # same attempt of the same stage in the same run names the same
            # record. A random id would make two views of one attempt look like
            # two attempts.
            "model_run_id": "%s|%s|sa%s|a%d" % (run_id, request.stage_id,
                                                stage_attempt, attempt),
            "run_id": run_id,
            "stage_id": request.stage_id,
            "stage_attempt": stage_attempt,
            "attempt_index": attempt,
            "purpose": request.purpose,
            "provider_id": self.provider_id,
            # The contract asks for "the exact model identifier requested AND, if
            # different, the one served". model_id carries the requested identity;
            # the requested/served pair below answers the second half precisely.
            "model_id": requested_model,
            "model_version_string": served or "NOT_REPORTED",
            "model_id_requested": requested_model,
            "model_id_served": served or "NOT_REPORTED",
            "model_substitution": fallback,
            "request": {
                "prompt_sha256": sha256(request.prompt_text),
                # Retention is mandatory (MODEL_RUN_RECORD_CONTRACT): an
                # unretained prompt makes the response uninterpretable. No
                # credential is part of a prompt.
                "prompt_text": request.prompt_text,
                "prompt_chars": len(request.prompt_text),
                "max_output_tokens": max_tokens,
                "max_output_tokens_clamped_from":
                    request.max_output_tokens
                    if resolution.by_name("max_output_tokens").status == "SENT_AS_CLAMPED"
                    else None,
                "deadline_s": timeout,
                # The effective values, taken from the same resolution the body
                # was built from. Previously these were re-read off the adapter,
                # so a record could agree with the object while disagreeing with
                # the wire.
                "parameters": {
                    "temperature": resolution.effective("temperature"),
                    "top_p": resolution.effective("top_p"),
                    "response_format": resolution.effective("response_format"),
                },
                # The whole journey of every parameter: requested, override,
                # effective, whether it was sent, and why not when it was not.
                "parameter_resolution": resolution.as_record(),
                "experiment_overrides": self.overrides.as_record(),
            },
            "response": {
                "response_sha256": sha256(raw_text) if raw_text else None,
                # Retained verbatim, before any parsing. This is the only copy
                # of what the model actually said.
                "raw_text": raw_text,
                "response_chars": len(raw_text),
                "finish_reason": finish_reason or "NOT_REPORTED",
                "truncated": truncated,
                "reasoning_content_present": had_reasoning,
                "reasoning_content_stored": False,
            },
            "execution_status": status.value,
            "error_detail": error_detail,
            "usage": usage,
            "timing": {"started_at": started, "ended_at": ended,
                       "duration_s": round(ended - started, 3),
                       "retry_wait_s": retry_wait_s},
            "determinism": {
                "temperature": resolution.effective("temperature"),
                "top_p": resolution.effective("top_p"),
                "seed": resolution.effective("seed"),
                # The provider offers no seed guarantee. Claiming determinism it
                # does not offer would be worse than recording its absence.
                # NOT_SUPPORTED is stronger than UNKNOWN and is only used when the
                # provider declares it cannot carry a seed at all.
                "seed_honoured": ("UNKNOWN" if SUPPORTS_SEED else "NOT_SUPPORTED"),
                "seed_requested_by_stage": request.seed,
                "temperature_requested_by_stage": request.temperature,
                "temperature_actually_sent": resolution.effective("temperature"),
            },
        })

        return GenerationResult(
            execution_status=status,
            response=response if status in (ExecutionStatus.SUCCESS,
                                            ExecutionStatus.RESPONSE_TRUNCATED) else None,
            attempt_index=attempt, started_at=started, ended_at=ended,
            from_cache=False, error_detail=error_detail, fallback_reason=fallback)


def _int_or_none(value: Any) -> Optional[int]:
    return value if isinstance(value, int) else None
