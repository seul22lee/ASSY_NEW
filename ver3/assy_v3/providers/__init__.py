"""Provider boundary.

Interface definitions only — no live implementation, no network, no credentials.
See interfaces.py for the contract an implementation must meet, and
ver3/contracts/MODEL_RUN_RECORD_CONTRACT.yaml for the requirements PR-01..PR-11
that shape it.
"""

from .status import (
    PROVIDER_CONDITIONS,
    RETRYABLE,
    SEVERITY_ORDER,
    ExecutionStatus,
)
from .interfaces import (
    GenerationRequest,
    GenerationResponse,
    GenerationResult,
    ModelProvider,
    ProviderCapabilities,
    ReplayProvider,
    ResponseCache,
    ToolResult,
    ToolRunner,
)

__all__ = [
    "ExecutionStatus",
    "SEVERITY_ORDER",
    "RETRYABLE",
    "PROVIDER_CONDITIONS",
    "ProviderCapabilities",
    "GenerationRequest",
    "GenerationResponse",
    "GenerationResult",
    "ModelProvider",
    "ResponseCache",
    "ReplayProvider",
    "ToolRunner",
    "ToolResult",
]
