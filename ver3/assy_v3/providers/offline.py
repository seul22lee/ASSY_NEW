"""A provider that replays recorded responses.

Not a mock: the recorded text is a real model response, kept verbatim so the
pipeline is deterministic and testable without a network. A provider condition
still never becomes a statement about the design - a missing recording returns
PROVIDER_UNAVAILABLE, exactly as a real outage would.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

from .interfaces import (GenerationRequest, GenerationResponse, GenerationResult,
                         ProviderCapabilities)
from .status import ExecutionStatus


class OfflineReplayProvider:
    """Replays fixtures/responses/<case_id>/<stage_id>.json."""

    def __init__(self, root: str, case_id: str) -> None:
        self.root = root
        self.case_id = case_id

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_id="offline-replay", model_id="recorded",
            context_window_tokens=None, max_output_tokens=None,
            supports_structured_output=True, supports_seed=True,
            requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None,
            notes="Replays recorded responses. No network, no credentials.")

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
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(
                raw_text=raw, finish_reason="stop", truncated=False,
                input_tokens=None, output_tokens=None, served_model_id="recorded"),
            attempt_index=attempt_index, started_at=started, ended_at=time.time(),
            from_cache=True)
