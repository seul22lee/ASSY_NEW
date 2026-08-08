"""A provider whose model is the agent operating this repository.

WHAT THIS IS
    The reasoning implementation under test is (prompt + knowledge layer + parser
    + validators). The MODEL is the agent. This provider records a response the
    agent produced by reading the prompt the stage actually built, and returns it
    with a recorded prompt hash so the pairing can be checked afterwards.

WHY IT IS NOT THE REPLAY PROVIDER
    OfflineReplayProvider returns whatever is on disk for a case, and says nothing
    about where it came from. A response recorded here asserts something stronger
    and narrower: it was produced FROM THIS PROMPT, and the hash proves the
    pairing. If the prompt changes, the recording is stale and this provider says
    so instead of replaying a response to a question that is no longer being
    asked.

WHAT IT IS NOT EVIDENCE OF
    It is not evidence about any other model, and it is not an automated provider.
    The agent authoring a response can see the repository, so a response recorded
    for an input whose validators were written first is fitted, not reasoned. That
    is why live evidence in this repository is collected on UNSEEN probe inputs
    and why fixture evidence and live evidence are reported separately.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from .interfaces import (GenerationRequest, GenerationResponse, GenerationResult,
                         ProviderCapabilities)
from .status import ExecutionStatus


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class AgentAuthoredProvider:
    """Serves recordings that declare the prompt they answer."""

    def __init__(self, root: str, case_id: str, strict_prompt: bool = True) -> None:
        self.root = root
        self.case_id = case_id
        self.strict_prompt = strict_prompt

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_id="agent-authored", model_id="agent-in-repository",
            context_window_tokens=None, max_output_tokens=None,
            supports_structured_output=True, supports_seed=False,
            requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None,
            notes=("The model is the agent operating this repository. Not an "
                   "automated provider and not evidence about any other model."))

    def generate(self, request: GenerationRequest, attempt_index: int = 0) -> GenerationResult:
        started = time.time()
        path = os.path.join(self.root, self.case_id, "%s.json" % request.stage_id)
        if not os.path.isfile(path):
            return GenerationResult(
                execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE, response=None,
                attempt_index=attempt_index, started_at=started, ended_at=time.time(),
                from_cache=False, error_detail="no recording at %s" % path)
        with open(path) as fh:
            raw = fh.read()
        try:
            parsed = json.loads(raw)
        except Exception:                                          # noqa: BLE001
            parsed = {}
        declared = (parsed.get("_meta") or {}).get("answers_prompt_sha256")
        actual = prompt_hash(request.prompt_text)
        if self.strict_prompt and declared and declared != actual:
            return GenerationResult(
                execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE, response=None,
                attempt_index=attempt_index, started_at=started, ended_at=time.time(),
                from_cache=False,
                error_detail=("recording answers prompt %s but the stage built %s; "
                              "the response is stale" % (declared, actual)))
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(
                raw_text=raw, finish_reason="stop", truncated=False,
                input_tokens=None, output_tokens=None,
                served_model_id="agent-in-repository"),
            attempt_index=attempt_index, started_at=started, ended_at=time.time(),
            from_cache=False)
