"""Provider boundary — interface definitions only.

NO LIVE IMPLEMENTATION. There is no HTTP call, no client library, no credential
read and no retry loop in this module. Every method raises NotImplementedError.

The pipeline will run against real providers, including free-tier APIs with hard
rate limits, small quotas, aggressive timeouts and low output caps. Those are
NORMAL OPERATING CONDITIONS here, not exceptions, and the shape of this interface
is chosen so that a degraded run reports itself as degraded instead of as a worse
design.

Contract: ver3/contracts/MODEL_RUN_RECORD_CONTRACT.yaml (PR-01..PR-11).

The one rule everything else follows from
-----------------------------------------
A provider condition must never be convertible into a statement about the design.
Concretely, that is why `generate` returns a result carrying an ExecutionStatus
rather than raising on failure: an exception forces the caller to interpret, and
the interpretation is where a rate limit quietly becomes an infeasible design.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence

from .status import ExecutionStatus


# ---------------------------------------------------------------------------
# Declared capabilities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderCapabilities:
    """What a provider can actually do, declared rather than discovered.

    PR-09. A caller that cannot see the output cap will generate work that is
    guaranteed to truncate, then record RESPONSE_TRUNCATED and retry into the
    same wall. Limits are part of the interface for that reason.

    Fields whose value is genuinely unknown are None, never a hopeful default.
    """

    provider_id: str
    model_id: str
    context_window_tokens: Optional[int]
    max_output_tokens: Optional[int]
    supports_structured_output: bool
    supports_seed: bool
    #: None when the provider makes no published guarantee. Not zero, not infinity.
    requests_per_minute: Optional[int]
    tokens_per_minute: Optional[int]
    daily_quota_requests: Optional[int]
    notes: str = ""


# ---------------------------------------------------------------------------
# Request and response
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GenerationRequest:
    """One model call, fully described before it is made.

    `purpose` is recorded before the call rather than inferred from the response
    afterwards. A purpose read off the output is a description of what happened,
    not a record of what was intended.
    """

    purpose: str
    stage_id: str
    prompt_text: str
    max_output_tokens: int
    deadline_s: float
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    seed: Optional[int] = None
    response_schema: Optional[Mapping[str, Any]] = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResponse:
    """What came back, before any parsing or repair.

    `raw_text` is retained exactly as received. `truncated` is taken from the
    provider's finish reason and never guessed from the content — a structured
    response that stops mid-object often still parses, and a patch built from it
    is silently missing its tail, which nothing downstream can detect.
    """

    raw_text: str
    finish_reason: str
    truncated: bool
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    cached_input_tokens: Optional[int] = None
    #: The model the provider actually served, when it differs from the one asked
    #: for. A run whose model is unknown is not reproducible (PR-04).
    served_model_id: Optional[str] = None


@dataclass(frozen=True)
class GenerationResult:
    """Outcome of an attempt: always returned, never raised.

    Both `response` and `error_detail` may be present. A timeout that delivered
    partial text carries both, and the partial text is retained without being
    treated as complete.
    """

    execution_status: ExecutionStatus
    response: Optional[GenerationResponse]
    attempt_index: int
    started_at: float
    ended_at: float
    from_cache: bool
    error_detail: Optional[str] = None
    #: Set only when an explicit, recorded fallback occurred. Silent fallback is
    #: forbidden (PR-04); an unset field here asserts that none happened.
    fallback_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# The provider interface
# ---------------------------------------------------------------------------

class ModelProvider:
    """A language-model provider.

    Implementations live outside this rebuild task. The contract an implementation
    must meet:

    * `generate` returns a GenerationResult for every outcome and raises only on
      programming errors (a malformed request), never on a provider condition.
    * Each attempt produces its own result. A retry never overwrites its
      predecessor, and the caller records every one (PR-02).
    * Truncation is reported, never parsed around (PR-05).
    * Model substitution is reported through `served_model_id` and
      `fallback_reason` (PR-04).
    * Credentials come from the environment and never appear in a record (PR-11).
    * No prompt may contain benchmark-answer-key or positive-reference content
      (PR-07). The provider layer cannot verify this; the file-access audit and
      the import test are what make a violation visible.
    """

    def capabilities(self) -> ProviderCapabilities:
        raise NotImplementedError("Provider interfaces are definitions only.")

    def generate(self, request: GenerationRequest, attempt_index: int) -> GenerationResult:
        raise NotImplementedError("Provider interfaces are definitions only.")


class ResponseCache:
    """Cache keyed on (provider_id, model_id, prompt_sha256, parameters).

    PR-06: a cache hit is recorded AS a cache hit. Two runs that appear
    independent but shared a cached response are not two runs, and a benchmark
    that treats them as independent is measuring one run twice.
    """

    def get(self, key: str) -> Optional[GenerationResponse]:
        raise NotImplementedError("Provider interfaces are definitions only.")

    def put(self, key: str, response: GenerationResponse) -> None:
        raise NotImplementedError("Provider interfaces are definitions only.")


class ReplayProvider(ModelProvider):
    """Offline replay from recorded run records.

    PR-10. Re-executing a run without contacting any provider is how a degraded
    run is analysed after the fact, and how the deterministic parts of the
    pipeline are tested without spending quota that the free tier will not
    refund.

    A replay that cannot find a recorded response for a request must report the
    absence rather than fall through to a live call. Falling through would make
    the replay silently partly-live, and its result would describe neither run.
    """

    def __init__(self, records: Sequence[Dict[str, Any]]) -> None:
        raise NotImplementedError("Provider interfaces are definitions only.")


class ToolRunner:
    """Deterministic tools: geometry kernel, mesh queries, solvers, integrators.

    Distinguished from a model provider because the failure modes differ. A tool
    does not get rate-limited; it crashes, or it fails to converge. A crash is
    EXECUTION_FAILED and never becomes a measured value (forbidden collapse C-03),
    and a value arriving without a unit is a boundary SCHEMA_FAILURE (INV-004).
    """

    def tool_version(self, tool_id: str) -> str:
        raise NotImplementedError("Provider interfaces are definitions only.")

    def run(self, tool_id: str, inputs: Mapping[str, Any]) -> "ToolResult":
        raise NotImplementedError("Provider interfaces are definitions only.")


@dataclass(frozen=True)
class ToolResult:
    """A deterministic tool's outcome.

    `inputs_sha256` covers the numerical settings — tolerance, sampling,
    integrator, seed — because they determine the result and are otherwise easy
    to treat as incidental configuration that need not be recorded.
    """

    tool_id: str
    tool_version: str
    inputs_sha256: str
    outputs: Mapping[str, Any]
    execution_status: ExecutionStatus
    started_at: float
    ended_at: float
    error_detail: Optional[str] = None
