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


def carry_invocation_premises(ops: List[Op], premises: List[str]) -> List[Op]:
    """Put the stage's declared invocation premises onto the values it authored.

    This is NORMALIZATION, not authorship. The engineering fact - that this
    invocation rests on these entities - is stated by the stage in
    `Stage.invocation_premises`. All that happens here is union, dedup, and
    preservation: an operation that already declares premises keeps them, in
    order, and the invocation premises follow.

    Only CREATE carries it. `_merge_premises` records premises on the ENTITY, so
    stamping an EXTEND would say the extended entity exists because of this
    invocation - which is false for anything that existed beforehand. An s04
    extension of a requirement would move that requirement onto the branch. What
    an invocation premise can honestly say is "this record was authored to embody
    that", and only a CREATE authors a record.
    """
    if not premises:
        return ops
    out: List[Op] = []
    for op in ops:
        extra = [p for p in premises
                 if p != op.entity_id and p not in op.premise_refs]
        if op.kind != "CREATE" or not extra:
            out.append(op)
            continue
        out.append(Op(op.kind, op.entity_type, op.entity_id, op.fields,
                      op.provenance_ref,
                      premise_refs=list(op.premise_refs) + extra,
                      reason=op.reason))
    return out


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
    #: WHO OWNS THE WRITE. Provenance and ownership are per stage: both s03 passes
    #: author s03 state and are governed by s03's ownership.
    stage_id = "sXX"

    #: WHICH ENGINEERING RESPONSIBILITY IS REASONING. A stage may run in more than
    #: one pass, and the passes ask different questions of different premises, so
    #: they are different consumers. Defaults to the stage when there is only one.
    #:
    #: Declared here so a runner cannot get it wrong: the mapping from a pass to
    #: its contract used to live in whoever was calling, which is how "s03" - a
    #: string that is an owner and not a responsibility - reached a consumer
    #: lookup at all.
    pass_id = None

    purpose = ""

    @classmethod
    def responsibility_id(cls) -> str:
        return cls.pass_id or cls.stage_id

    # ------------------------------------------------------------ overridden
    def prompt(self, inputs: Dict[str, Any]) -> str:
        raise NotImplementedError

    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        raise NotImplementedError

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        """What the contract requires that this response did not supply."""
        return []

    def consumer_view(self, state, invocation=None, budget_chars=None):
        """This pass's engineering context. The ONE semantic boundary.

        Asked of the stage rather than of the runner, so every caller resolves the
        same responsibility and no tool keeps its own table of which contract a
        pass reads.
        """
        from ..view import consumer_view_for
        return consumer_view_for(self.responsibility_id(), state,
                                 budget_chars=budget_chars, invocation=invocation)

    def invocation_premises(self, inputs: Dict[str, Any]) -> List[str]:
        """Class-A entities that everything THIS invocation authors rests on.

        A stage that is invoked to embody a particular decision says so here, and
        the fact then travels with the patch no matter which runner called it.
        Only the stage can state this: the entity ids are in its own declared
        inputs, and whether they are genuine engineering premises is a question
        about the stage's responsibility, not about the write mechanism.

        Default: none - which is an honest absence, not an assertion that no
        premise exists.
        """
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
            ops = carry_invocation_premises(self.to_operations(parsed),
                                            self.invocation_premises(inputs))
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
