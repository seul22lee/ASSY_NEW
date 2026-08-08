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
from ver3.assy_v3.providers.status import ExecutionStatus

from .env import require

#: The credential's variable. Read from the environment and nowhere else.
API_KEY_VAR = "DEEPSEEK_API_KEY"

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

#: DeepSeek's documented output ceiling. A request above it is clamped, and the
#: clamp is recorded, because a silently reduced cap produces a truncation the
#: caller cannot explain.
MAX_OUTPUT_TOKENS_CEILING = 8192

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

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None,
                 temperature: float = 1.0, top_p: Optional[float] = None,
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

    # ------------------------------------------------------------ capability
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_id=self.provider_id, model_id=self.model,
            context_window_tokens=65536, max_output_tokens=MAX_OUTPUT_TOKENS_CEILING,
            supports_structured_output=True,
            # DeepSeek accepts no seed parameter. Declaring support would be a
            # determinism claim the provider does not make.
            supports_seed=False,
            requests_per_minute=None, tokens_per_minute=None, daily_quota_requests=None,
            notes=("Live HTTP provider. Serves a model alias, so the served model "
                   "is recorded per call and may differ from the one requested."))

    # ---------------------------------------------------------------- driver
    def generate(self, request: GenerationRequest, attempt_index: int = 0) -> GenerationResult:
        """Bounded retry over one logical call. Never raises on a provider
        condition; every attempt leaves its own record."""
        last: Optional[GenerationResult] = None
        waited = 0.0
        for attempt in range(1, self.max_attempts + 1):
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
            if attempt < self.max_attempts:
                wait = self.backoff_s * attempt
                waited += wait
                time.sleep(wait)
        return last                                     # type: ignore[return-value]

    # --------------------------------------------------------------- one try
    def _attempt(self, request: GenerationRequest, attempt: int,
                 retry_wait_s: float) -> GenerationResult:
        max_tokens = min(request.max_output_tokens or MAX_OUTPUT_TOKENS_CEILING,
                         MAX_OUTPUT_TOKENS_CEILING)
        clamped = (request.max_output_tokens or 0) > MAX_OUTPUT_TOKENS_CEILING

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt_text}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.json_object_mode:
            payload["response_format"] = {"type": "json_object"}

        timeout = self.timeout_s or request.deadline_s or 120.0
        started = time.time()

        # The header is built here and referenced nowhere else. It is not stored
        # on the instance, not put in the record, and not included in any error.
        http = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self._api_key})

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
                if served and served != self.model:
                    fallback = ("provider served %r for requested %r; recorded rather "
                                "than assumed equivalent" % (served, self.model))
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
        self.records.append({
            "stage_id": request.stage_id,
            "attempt_index": attempt,
            "purpose": request.purpose,
            "provider_id": self.provider_id,
            "model_id_requested": self.model,
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
                    request.max_output_tokens if clamped else None,
                "deadline_s": timeout,
                "parameters": {"temperature": self.temperature, "top_p": self.top_p,
                               "response_format": "json_object" if self.json_object_mode
                                                  else "text"},
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
                "temperature": self.temperature, "top_p": self.top_p,
                "seed": None,
                # The provider offers no seed guarantee. Claiming determinism it
                # does not offer would be worse than recording its absence.
                "seed_honoured": "UNKNOWN",
                "temperature_requested_by_stage": request.temperature,
                "temperature_actually_sent": self.temperature,
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
