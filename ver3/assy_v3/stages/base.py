"""What every stage does, in the same order, for the same reasons.

    build request -> call provider -> parse -> validate against the contract
                  -> emit a StagePatch carrying an execution status

The stage never raises on a provider condition and never repairs a response. A
response that will not parse yields RESPONSE_PARSE_FAILURE; one that parses but
violates the contract yields SCHEMA_FAILURE; one that parses and validates but
omits required content yields CONTRACT_INCOMPLETE with the omission declared.
None of the three is ever converted into a statement about the design.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..providers.interfaces import GenerationRequest
from ..providers.status import ExecutionStatus
from ..state.patch import Op, StagePatch


class StageError(Exception):
    """A programming error in the stage itself. Never a provider condition."""


def _provider_id(provider) -> str:
    """Who actually served the call, asked of the provider rather than assumed.

    A provider that cannot describe itself is recorded as unknown; guessing a
    name would put a false statement in the run's own record.
    """
    try:
        return provider.capabilities().provider_id
    except Exception:                                               # noqa: BLE001
        return "unknown"


@dataclass
class StageOutcome:
    stage_id: str
    execution_status: ExecutionStatus
    patch: Optional[StagePatch]
    problems: List[str] = field(default_factory=list)
    declared_incompleteness: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.execution_status is ExecutionStatus.SUCCESS


class Stage:
    stage_id = "sXX"
    purpose = ""

    # ------------------------------------------------------------ overridden
    def prompt(self, inputs: Dict[str, Any]) -> str:
        raise NotImplementedError

    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        raise NotImplementedError

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        """What the contract requires that this response did not supply."""
        return []

    # ---------------------------------------------------------------- driver
    def run(self, provider, inputs: Dict[str, Any], state, run_id: str,
            attempt: int = 1) -> StageOutcome:
        req = GenerationRequest(
            purpose=self.purpose, stage_id=self.stage_id,
            prompt_text=self.prompt(inputs), max_output_tokens=32000,
            deadline_s=120.0, temperature=0.0, seed=7)
        result = provider.generate(req)
        if result.execution_status is not ExecutionStatus.SUCCESS or result.response is None:
            return StageOutcome(self.stage_id, result.execution_status, None,
                                problems=[result.error_detail or "provider did not succeed"])
        if result.response.truncated:
            return StageOutcome(self.stage_id, ExecutionStatus.RESPONSE_TRUNCATED, None,
                                problems=["response truncated"],
                                raw_response=result.response.raw_text)
        try:
            parsed = json.loads(result.response.raw_text)
        except Exception as exc:                                    # noqa: BLE001
            return StageOutcome(self.stage_id, ExecutionStatus.RESPONSE_PARSE_FAILURE, None,
                                problems=["%s: %s" % (type(exc).__name__, exc)],
                                raw_response=result.response.raw_text)

        # A response that is valid JSON but not the shape the stage asked for is
        # a SCHEMA_FAILURE, which is what this module's own docstring promises.
        # Letting the KeyError escape instead made a malformed response crash the
        # caller, and a crash is not a status anything downstream can record.
        try:
            ops = self.to_operations(parsed)
            missing = self.completeness(parsed, inputs)
        except (KeyError, TypeError, AttributeError, IndexError, ValueError) as exc:
            return StageOutcome(
                self.stage_id, ExecutionStatus.SCHEMA_FAILURE, None,
                problems=["response shape: %s: %s" % (type(exc).__name__, exc)],
                raw_response=result.response.raw_text)

        patch = StagePatch(
            patch_id="%s-%s-a%d" % (run_id, self.stage_id, attempt),
            run_id=run_id, stage_id=self.stage_id, stage_attempt=attempt,
            parent_state_hash=state.state_hash(), operations=ops,
            execution_status=ExecutionStatus.SUCCESS.value,
            # Taken from the provider that actually served the call. A hard-coded
            # label made every record claim a replay, including live runs.
            provenance={"purpose": self.purpose,
                        "provider": _provider_id(provider)},
            declared_incompleteness=missing)
        problems = state.validate(patch)
        if problems:
            return StageOutcome(self.stage_id, ExecutionStatus.SCHEMA_FAILURE, patch,
                                problems=problems, declared_incompleteness=missing,
                                raw_response=result.response.raw_text)
        status = (ExecutionStatus.CONTRACT_INCOMPLETE if missing
                  else ExecutionStatus.SUCCESS)
        patch.execution_status = status.value
        return StageOutcome(self.stage_id, status, patch,
                            declared_incompleteness=missing,
                            raw_response=result.response.raw_text)
