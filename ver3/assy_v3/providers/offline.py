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
from .replay_integrity import (CURRENT_REPLAY, INTEGRITY_ESTABLISHED,
                               INTEGRITY_NOT_ESTABLISHED, LEGACY_REPLAY, REPLAY,
                               current_replay_problems, pairing_status,
                               producing_identity)
from .status import ExecutionStatus


class OfflineReplayProvider:
    """Replays fixtures/responses/<case_id>/<responsibility_id>.json.

    ADDRESSED BY THE PRODUCING PASS, not by the owner. Keying on `stage_id`
    resolved both s03 passes to one file, so s03b was served s03a's answer and
    the difference was undetectable. s01 and s02 are unaffected: their owner and
    their responsibility are the same string.
    """

    provider_id = "offline-replay"
    #: DECLARED, not inferred. A run used to be "live" because a particular
    #: script started it, which is a fact about a filename rather than about
    #: where the response came from.
    response_source = REPLAY

    def __init__(self, root: str, case_id: str, trust: str = LEGACY_REPLAY,
                 source_sha256: Optional[str] = None,
                 ledger: Optional[dict] = None) -> None:
        """`trust` decides whether integrity is CHECKED or merely RECORDED.

        LEGACY is the default because the corpus predates S9-E: every active
        artifact is agent-authored and carries none of the current identities.
        Defaulting to CURRENT would break the regression suite the corpus still
        supports, and the only way to keep it working would be to stamp the
        identities on by hand - which is the forgery S9-E exists to avoid.

        LEGACY never becomes CURRENT by accident: a legacy replay reports
        integrity NOT_ESTABLISHED, and nothing reads that as a current fixture.
        """
        if trust not in (LEGACY_REPLAY, CURRENT_REPLAY):
            raise ValueError("unknown replay trust class %r" % trust)
        self.root = root
        self.case_id = case_id
        self.trust = trust
        #: The canonical identity of the request being replayed. Required in
        #: CURRENT mode: without it a fixture can only be checked against itself.
        self.source_sha256 = source_sha256
        #: Retained promotion evidence. The trusted side of the anchor.
        self.ledger = ledger
        self.last_integrity: dict = {}

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
        path = os.path.join(self.root, self.case_id,
                            "%s.json" % producing_identity(request))
        if not os.path.isfile(path):
            return GenerationResult(
                execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE, response=None,
                attempt_index=attempt_index, started_at=started, ended_at=time.time(),
                from_cache=False, error_detail="no recording at %s" % path)
        with open(path) as fh:
            raw = fh.read()
        # INTEGRITY IS RECORDED FOR EVERY REPLAY and ENFORCED for a current one.
        # Recording alone was the S9-D gap: the rule existed, promotion and the
        # audits called it, and the ordinary path returned SUCCESS whatever it
        # said.
        self.last_pairing = pairing_status(raw, request.prompt_text)
        responsibility = producing_identity(request)
        problems = current_replay_problems(
            raw, prompt_text=request.prompt_text,
            source_sha256=self.source_sha256, responsibility_id=responsibility,
            ledger=self.ledger)
        established = self.trust == CURRENT_REPLAY and not problems
        self.last_integrity = {
            "trust": self.trust,
            "current_fixture_integrity": (INTEGRITY_ESTABLISHED if established
                                          else INTEGRITY_NOT_ESTABLISHED),
            "responsibility_id": responsibility,
            "pairing": self.last_pairing,
            "problems": problems,
        }
        if self.trust == CURRENT_REPLAY and problems:
            # THE ARTIFACT CANNOT BE SERVED. Reported exactly as a missing
            # recording is, because that is what it amounts to: there is no
            # usable response here for this request. It is deliberately not a
            # schema, contract or assurance status - nothing about the DESIGN
            # failed, and saying otherwise would blame the model for our corpus.
            return GenerationResult(
                execution_status=ExecutionStatus.PROVIDER_UNAVAILABLE, response=None,
                attempt_index=attempt_index, started_at=started, ended_at=time.time(),
                from_cache=False,
                error_detail="current-fixture integrity not established for %s: %s"
                             % (responsibility, "; ".join(problems)))
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(
                raw_text=raw, finish_reason="stop", truncated=False,
                input_tokens=None, output_tokens=None, served_model_id="recorded"),
            attempt_index=attempt_index, started_at=started, ended_at=time.time(),
            from_cache=True)
