"""Execution status vocabulary.

Definitions only. This module holds the twelve execution statuses and nothing
that decides which one applies — that is a stage and provider-layer concern, and
no stage logic exists in this package yet.

The authority is ver3/contracts/STATUS_SEMANTICS.yaml. This enum is a projection
of it, and ver3/tests/meta/test_status_semantics.py fails if the two disagree in
either direction. The test exists because a vocabulary that drifts from its
contract is worse than no vocabulary: the names still look right.

Why these are separate values at all
------------------------------------
Each pair that looks mergeable has a different operational response:

  RATE_LIMIT vs QUOTA_EXHAUSTED     one waits; the other cannot be waited out
  TIMEOUT vs UNAVAILABLE            one may have partial output; the other never does
  TRUNCATED vs PARSE_FAILURE        one parses and is silently short; the other does not parse
  SCHEMA_FAILURE vs CONTRACT_INCOMPLETE   one is malformed; the other is well-formed and under-covered
  MODEL_CAPABILITY_FAILURE vs any PROVIDER_*   one is about the model; the rest are about the wire

And two that carry the architecture's whole point:

  SAFE_REJECTION      the run declined a claim it could not support. Correct
                      behaviour, never penalised. Penalising it teaches overclaiming.
  FALSE_ACCEPTANCE    the run claimed something it had not earned. The most
                      serious defect class, and the one every other rule in this
                      repository is shaped to prevent.

None of these describes the DESIGN. A design does not become worse because a
server was busy (STATUS_SEMANTICS forbidden collapse C-04).
"""

import enum


class ExecutionStatus(enum.Enum):
    """How a step's machinery behaved. Never a statement about the design."""

    SUCCESS = "SUCCESS"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    PROVIDER_QUOTA_EXHAUSTED = "PROVIDER_QUOTA_EXHAUSTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    RESPONSE_TRUNCATED = "RESPONSE_TRUNCATED"
    RESPONSE_PARSE_FAILURE = "RESPONSE_PARSE_FAILURE"
    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    CONTRACT_INCOMPLETE = "CONTRACT_INCOMPLETE"
    MODEL_CAPABILITY_FAILURE = "MODEL_CAPABILITY_FAILURE"
    SAFE_REJECTION = "SAFE_REJECTION"
    FALSE_ACCEPTANCE = "FALSE_ACCEPTANCE"


#: Worst-first. Used only to roll a set of attempt statuses up to a run status.
#: This is an ordering over failure modes, not a quality score, and nothing may
#: reduce it to a number.
SEVERITY_ORDER = (
    ExecutionStatus.FALSE_ACCEPTANCE,
    ExecutionStatus.MODEL_CAPABILITY_FAILURE,
    ExecutionStatus.CONTRACT_INCOMPLETE,
    ExecutionStatus.SCHEMA_FAILURE,
    ExecutionStatus.RESPONSE_PARSE_FAILURE,
    ExecutionStatus.RESPONSE_TRUNCATED,
    ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED,
    ExecutionStatus.PROVIDER_TIMEOUT,
    ExecutionStatus.PROVIDER_UNAVAILABLE,
    ExecutionStatus.PROVIDER_RATE_LIMIT,
    ExecutionStatus.SAFE_REJECTION,
    ExecutionStatus.SUCCESS,
)

#: Statuses a bounded retry may follow. PR-02 requires the bound: retrying until
#: the answer is acceptable is resampling for a desired result, not a retry.
RETRYABLE = frozenset({
    ExecutionStatus.PROVIDER_RATE_LIMIT,
    ExecutionStatus.PROVIDER_UNAVAILABLE,
    ExecutionStatus.PROVIDER_TIMEOUT,
    ExecutionStatus.RESPONSE_TRUNCATED,
    ExecutionStatus.RESPONSE_PARSE_FAILURE,
    ExecutionStatus.SCHEMA_FAILURE,
    ExecutionStatus.CONTRACT_INCOMPLETE,
})

#: Statuses that say nothing whatsoever about the design. A benchmark result may
#: not convert any of these into a design finding (BENCHMARK_RESULT_CONTRACT SC-02).
PROVIDER_CONDITIONS = frozenset({
    ExecutionStatus.PROVIDER_RATE_LIMIT,
    ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED,
    ExecutionStatus.PROVIDER_UNAVAILABLE,
    ExecutionStatus.PROVIDER_TIMEOUT,
})
