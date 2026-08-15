"""When a live response may become a replay fixture, and what that fixture says.

PROVIDER SUCCESS IS NOT PROMOTION

A call can succeed on the wire and still produce something that will not parse.
A response can parse and still fail contract validation. A patch can validate and
still be refused by the state boundary. Each of those is a different fact, and
collapsing them into "it worked" is how a corpus fills with artifacts nobody can
account for. `AttemptOutcome` keeps the whole ladder, and promotion reads the top
of it rather than the bottom.

THE RULE IS FIXED BEFORE THE ANSWERS ARE SEEN

`FIRST_CONFORMING` is declared here, in code, before S9-E runs. Choosing after
looking at the engineering content - keeping the attempt whose mechanism reads
better - is resampling for a desired result, and it would make the corpus a record
of what the author preferred rather than of what the model produced.

FAILED ATTEMPTS ARE EVIDENCE

They are retained whatever a later attempt does. A corpus that shows only the
attempt that worked cannot answer how often the pipeline had to ask twice.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from ..providers import replay_integrity as ri

# --------------------------------------------------------------------------
# The ladder. Each rung is a different question with a different remedy.
# --------------------------------------------------------------------------

PROVIDER_FAILED = "PROVIDER_FAILED"
RESPONSE_UNUSABLE = "RESPONSE_UNUSABLE"
PARSER_FAILED = "PARSER_FAILED"
CONTRACT_FAILED = "CONTRACT_FAILED"
NOT_ACCEPTED = "NOT_ACCEPTED"
ACCEPTED = "ACCEPTED"

#: The only rung from which promotion may be considered. Reaching it means the
#: normal production path - real parser, real contracts, real write boundary -
#: took the response, which is what S9-I2 means by "conforming".
PROMOTABLE_FROM = ACCEPTED

#: THE SELECTION RULE, declared before S9-E. The first attempt that is eligible
#: is the one promoted; later attempts are retained and not consulted.
FIRST_CONFORMING = "FIRST_CONFORMING"
SELECTION_RULE = FIRST_CONFORMING


@dataclass(frozen=True)
class AttemptOutcome:
    """One live attempt, with every rung it reached recorded separately."""

    responsibility_id: str
    source_sha256: str
    #: The S9-B model-run identity. Not re-invented here.
    model_run_id: str
    attempt_index: int
    stage: str
    raw_response: Optional[str] = None
    problems: Sequence[str] = ()
    #: Set only when a human touched the response. Such an attempt can never be
    #: promoted, whatever else is true of it.
    hand_edited: bool = False

    @property
    def accepted(self) -> bool:
        return self.stage == ACCEPTED

    def as_record(self) -> Dict[str, Any]:
        return {"responsibility_id": self.responsibility_id,
                "source_sha256": self.source_sha256,
                "model_run_id": self.model_run_id,
                "attempt_index": self.attempt_index, "stage": self.stage,
                "raw_response_sha256": (sha256(self.raw_response)
                                        if self.raw_response else None),
                "problems": list(self.problems), "hand_edited": self.hand_edited}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def eligibility_problems(attempt: AttemptOutcome) -> List[str]:
    """Why this attempt may not become a fixture. Empty means it may."""
    problems: List[str] = []
    if attempt.hand_edited:
        # THE ONE DISQUALIFIER NOTHING OVERRIDES. A repaired response measures
        # the repair, and a fixture built from one would present the repair as
        # the model's output for every future run.
        problems.append("the response was edited by hand; a repaired response "
                        "is evidence about the repair")
    if attempt.stage != PROMOTABLE_FROM:
        problems.append("attempt reached %s, and only %s may be promoted"
                        % (attempt.stage, PROMOTABLE_FROM))
    if not attempt.raw_response:
        problems.append("no raw response was retained")
    if not attempt.model_run_id:
        problems.append("no model-run identity; the fixture could not say which "
                        "run produced it")
    if not attempt.source_sha256:
        problems.append("no source identity")
    if not attempt.responsibility_id:
        problems.append("no producing responsibility")
    return problems


def select_for_promotion(attempts: Sequence[AttemptOutcome]) -> Dict[str, Any]:
    """Apply the frozen rule. Returns the choice AND everything not chosen.

    The rejected attempts travel with the decision so that a corpus can always
    answer how many tries a fixture took, and on what grounds the others lost -
    which must always be conformance, never the engineering content.
    """
    considered = []
    chosen = None
    for attempt in attempts:
        problems = eligibility_problems(attempt)
        considered.append({"attempt": attempt.as_record(), "eligible": not problems,
                           "problems": problems})
        if not problems and chosen is None:
            chosen = attempt
    return {"rule": SELECTION_RULE, "chosen": chosen,
            "considered": considered,
            "eligible_count": sum(1 for c in considered if c["eligible"])}


def fixture_body(attempt: AttemptOutcome, prompt_text: str) -> str:
    """Package an accepted response as a replay fixture.

    PACKAGING, NOT AUTHORING. The response is parsed and re-emitted with a
    `_meta` block added beside it; no key of the model's answer is added, removed
    or altered, and `promotion_fidelity_problems` is what proves that afterwards.
    """
    if eligibility_problems(attempt):
        raise ValueError("attempt is not promotion-eligible: %s"
                         % "; ".join(eligibility_problems(attempt)))
    parsed = json.loads(attempt.raw_response)
    if not isinstance(parsed, dict):
        raise ValueError("only a JSON object can carry fixture provenance")
    body = dict(parsed)
    meta = dict(body.get("_meta") or {})
    meta.update({
        ri.PAIRING_KEY: ri.prompt_hash(prompt_text),
        ri.SOURCE_KEY: attempt.source_sha256,
        ri.RESPONSIBILITY_KEY: attempt.responsibility_id,
        ri.RESPONSE_KEY: sha256(attempt.raw_response),
        ri.PROMOTION_KEY: attempt.model_run_id,
    })
    body["_meta"] = meta
    return json.dumps(body, indent=1, sort_keys=True)


@dataclass
class PromotionLedger:
    """Every attempt, promoted or not. Nothing is dropped when a retry succeeds."""

    entries: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, decision: Dict[str, Any], promoted_path: Optional[str],
               problems: Sequence[str] = ()) -> None:
        self.entries.append({
            "rule": decision["rule"],
            "attempts": decision["considered"],
            "eligible_count": decision["eligible_count"],
            "promoted": promoted_path,
            "problems": list(problems),
        })

    def attempts_recorded(self) -> int:
        return sum(len(e["attempts"]) for e in self.entries)
