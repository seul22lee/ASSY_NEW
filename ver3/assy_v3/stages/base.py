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
from ..view.consumer_view import ViewStatus


def _unmet(assessment: Dict[str, Any]) -> str:
    """One unsatisfied obligation, said in full: what was expected, what arrived."""
    parts = []
    for atom in assessment.get("coverage") or []:
        if atom["verdict"] == "SATISFIED":
            continue
        parts.append("%s: %s (expected %d, selected %d)"
                     % (atom["obligation"], atom["verdict"],
                        atom.get("expected_count", 0), atom.get("selected_count", 0)))
    return "%s -> %s" % (assessment["requirement"], "; ".join(parts) or assessment["verdict"])


class StageError(Exception):
    """A programming error in the stage itself. Never a provider condition."""


def render_namespace_occupancy(occupancy: Optional[Dict[str, Any]]) -> str:
    """The ids already taken in the families this responsibility may create.

    ONE renderer for every stage, appended by `build_prompt` below, so no stage's
    prompt template mentions a family and no stage decides whether it needs this.
    A rule written as `if the stage is s02, show the assumption ids` would be the
    same defect in a new place: it would hold for exactly the collision that had
    already happened and for no other.

    Empty renders nothing. A first stage, or any stage whose creatable families
    are still empty, gets the prompt it always got - which is also why adding
    this changed no prompt that had nothing to be told.
    """
    if not occupancy:
        return ""
    lines = ["", "IDS ALREADY IN USE",
             "These entities already exist in the design state. The ids are listed",
             "so you do not reuse one: every id you emit must be new. This is an",
             "identity list and nothing more - it says which ids are taken, not",
             "what those entities say, and it is not something to reason from.",
             "The example ids in the response schema show the FORMAT of an id.",
             "They are not offers of an available id, and the first index is",
             "commonly the one already taken."]
    for family in sorted(occupancy):
        ids = list(occupancy[family] or [])
        if not ids:
            continue
        lines.append("  %s: %s" % (family, ", ".join(str(i) for i in ids)))
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class GenerationSettings:
    """What a CAMPAIGN asks of a provider, stated rather than defaulted.

    These were literals inside `Stage.run`: temperature 0.0 and a 32000-token
    request. Both are reasonable defaults for ordinary use and neither is what a
    diagnostic campaign wants - and the second is the more dangerous, because a
    provider CEILING of 65536 does not raise a request of 32000. A campaign that
    set only the ceiling would believe it had a budget it never asked for.

    `max_attempts` belongs here for the same reason: retrying changes what a
    result MEANS. One attempt records what the model did; three records the best
    of three, and reporting that as "the model produced this" overstates it.

    Frozen and passed explicitly, so a run record can carry exactly what was
    asked. Defaults reproduce the previous literals unchanged - existing callers
    keep their behaviour, and a campaign says what it wants out loud.
    """

    temperature: float = 0.0
    max_output_tokens: int = 32000
    #: One attempt. A campaign wanting FIRST_CONFORMING semantics sets it
    #: deliberately; nothing here retries on the caller's behalf.
    max_attempts: int = 1
    deadline_s: float = 120.0
    seed: Optional[int] = 7

    def as_record(self) -> Dict[str, Any]:
        """What was ASKED. Recorded beside what the provider resolved."""
        return {"temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "max_attempts": self.max_attempts,
                "deadline_s": self.deadline_s, "seed": self.seed}


#: THE INPUT KEY THAT MAKES AN INVOCATION A REPAIR. A caller that asks a pass
#: to revise what it produced puts the classified findings here, and the pass
#: renders them into its prompt and turns its answer into revisions of what
#: stands rather than a second copy of it. Absent, an invocation is what it
#: always was. Declared once, here, so the loop and the stages cannot spell it
#: differently.
REPAIR_KEY = "repair"


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
    #: THE STAGE ASKED TO BE CALLED AGAINST REFRESHED PREMISES.
    #:
    #: A CONTROL SIGNAL, not a status: this invocation committed a justified
    #: revision of something it was given, and withheld everything that would
    #: have been reasoned from the pre-revision value. It is machine-readable so
    #: a caller re-invokes on the fact rather than on prose, and it carries its
    #: own reason so a run record says why a second call happened.
    refinement_only: bool = False

    #: THE EXACT VIEW THIS INVOCATION USED, serialized at the moment of use.
    #:
    #: U-3 asks for a recorded ConsumerView: its content, the minimum it was built
    #: against, and what was compressed by which rule. Production used to take
    #: `.payload()` and drop the view, so afterwards the only way to ask what a
    #: stage was given was to rebuild a view from state that had since moved -
    #: which answers a different question. Recorded here, on the outcome of the
    #: call, so the record and the call cannot drift apart.
    consumer_view: Optional[Dict[str, Any]] = None

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

    #: The input key this stage reads its engineering context from. One key, one
    #: channel; `invoke` fills it and nothing else may.
    context_key = "consumer_view"

    #: The input key carrying IDENTITY-LEVEL NAMESPACE OCCUPANCY, filled from the
    #: same ConsumerView by the same `invoke`. A SECOND KEY rather than a second
    #: entry in the payload above, because that payload is family -> entity
    #: records and every stage's renderer walks it as such; an id list wearing a
    #: family's place in it would be a different shape under the same contract.
    #: Separate keys keep both readable and let a stage that renders neither stay
    #: unchanged.
    occupancy_key = "namespace_occupancy"

    @classmethod
    def responsibility_id(cls) -> str:
        return cls.pass_id or cls.stage_id

    # ------------------------------------------------------------ overridden
    def prompt(self, inputs: Dict[str, Any]) -> str:
        raise NotImplementedError

    def build_prompt(self, inputs: Dict[str, Any]) -> str:
        """THE prompt text actually sent. `prompt` plus what every stage is owed.

        A stage writes the question it is asking. This adds what no stage should
        have to remember: which ids are already spent in the families it is about
        to author into. Applied here, once, for the same reason `invoke` enforces
        view readiness here - a rule each stage has to opt into is a rule the next
        stage will be written without.

        `prompt` stays the stage's own, so a stage that wants the occupancy
        somewhere other than the end can render it from `inputs` itself; this
        appends what it was given and nothing else.
        """
        return self.prompt(inputs) + render_namespace_occupancy(
            inputs.get(self.occupancy_key))

    def to_operations(self, parsed: Dict[str, Any],
                      inputs: Optional[Dict[str, Any]] = None) -> List[Op]:
        """What this stage CREATES from its response.

        `inputs` is this invocation's own declared inputs - the same dict
        `completeness` and `invocation_premises` read. A stage that mints an id
        needs it: an id built from a module-local counter or constant is the same
        for every branch, so two candidates collide and only one can have the
        entity. A stage that keys its output to what it was invoked to embody
        cannot. Optional so a stage that mints nothing ignores it.
        """
        raise NotImplementedError

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        """What the contract requires that this response did not supply."""
        return []

    def refinement_barrier(self, parsed: Dict[str, Any], inputs: Dict[str, Any],
                           state):
        """Operations that must be committed ALONE, and why - or None.

        THE PROBLEM THIS SOLVES. `to_operations`, `refinement_operations` and
        `derived_operations` all reason from `inputs[context_key]`, which is the
        view built when the invocation started. That is correct until the same
        invocation REVISES something in that view: everything else it produces is
        then reasoned from a value the same patch is replacing. At S-6 an s04b
        response revising an envelope and placing the mechanism did exactly that -
        the swept occupancy was computed from the old extent and entered state
        STANDING, because it is created after the supersession and so was never a
        dependent of it. Current evidence, derived from geometry the design had
        just withdrawn.

        Returning `(ops, why)` makes the invocation a BARRIER: those operations
        are committed, nothing else is, and the outcome says so. A caller
        refreshes the view and calls again, and the second call reasons from what
        the first committed. Bounded by the caller, not open-ended.

        Default: None - a stage that revises nothing has no barrier, and its
        invocation is unchanged.
        """
        return None

    def refinement_operations(self, parsed: Dict[str, Any], inputs: Dict[str, Any],
                              state) -> List[Op]:
        """What this stage authors ONTO entities that already exist.

        `to_operations` CREATES; this EXTENDs and SUPERSEDEs. The difference is
        not cosmetic: refining an upstream value needs state, both to resolve the
        target's family and to decide whether this is an extension of a standing
        commitment or a supersession of one - a question a CREATE never has to
        ask.

        It exists because the alternative was a runner reading the raw response
        and writing the engineering facts the stage did not: joint origins,
        region volumes, insertion directions. Those are the stage's conclusions,
        and a caller that did not know to perform that second step got a
        DesignState missing them with nothing saying so.

        Default: none. Ordered before `derived_operations` so a class-B
        recomputation sees the refined values in the same patch.
        """
        return []

    def derived_operations(self, parsed: Dict[str, Any], inputs: Dict[str, Any],
                           state) -> List[Op]:
        """Class-B state this stage derives from what it has just authored.

        FA-4 state, strictly recomputed from premises the stage itself produced
        or received - never a second engineering opinion, and never authored.

        It belongs to the STAGE and not to a runner. The DOF disposition grid was
        derived by `tools/run_window2.py` after s03b returned, which meant a
        second valid caller of `invoke` observed a DesignState with no mobility
        in it at all: the derivation happened because one tool remembered to ask
        for it. Two canonical callers may not see different state because of what
        one of them remembered.

        Emitted into the SAME patch as the authored operations, so it is validated
        at the same write boundary and cannot be applied without them. Authorship
        stays distinguishable per operation through `provenance_ref`.

        Default: none. A stage that derives nothing says so by deriving nothing.
        """
        return []

    def repair_operations(self, ops: List[Op], inputs: Dict[str, Any],
                          state) -> List[Op]:
        """What this response means when it is a REPAIR of what already stands.

        Called only when `inputs[REPAIR_KEY]` is present, after the ordinary
        operations are assembled and before the patch is built. The ordinary
        hooks say what the response STATES; this says how a statement about an
        entity that already exists is recorded - a SUPERSEDE with the round's
        reason where a value changed, nothing where it did not, a retirement
        and a re-creation where a realization is one coherent set. Default: the
        response is not a repair of anything, so nothing is rewritten.
        """
        return ops

    def invoke(self, provider, state, run_id: str, inputs: Optional[Dict[str, Any]] = None,
               attempt: int = 1, invocation=None,
               budget_chars: Optional[int] = None,
               settings: Optional["GenerationSettings"] = None) -> StageOutcome:
        """THE canonical consumer invocation boundary. Build, enforce, record, run.

        U-3: "No output is produced from a view known to be insufficient", and the
        budget ordering ends "otherwise emit CONTEXT_INSUFFICIENT /
        BUDGET_INSUFFICIENT AND DO NOT CALL". Enforced here, once, so a runner
        cannot forget it and no runner has to remember how.

        A blocked invocation is not a provider failure and is not silence: it
        returns an outcome carrying the responsibility, the view, its status, its
        assessment and the reason - everything needed to say later that the model
        was never asked, rather than that it was asked and failed.
        """
        view = self.consumer_view(state, invocation, budget_chars)
        record = view.as_dict()
        if view.status is not ViewStatus.VIEW_READY:
            return StageOutcome(
                self.stage_id, ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT, None,
                problems=["%s: consumer context is %s; the provider was not called"
                          % (self.responsibility_id(), view.status.value)]
                         + [_unmet(a) for a in view.assessment
                            if a["verdict"] != "SATISFIED"],
                consumer_view=record)
        payload = dict(inputs or {})
        payload[self.context_key] = view.payload()
        # From the VIEW, not from state. Prompt code never queries DesignState:
        # the view is what was recorded, what carries provenance and what a
        # reviewer can read back, and a second path to the same facts would be a
        # second answer to what the consumer was given.
        payload[self.occupancy_key] = view.occupancy
        out = self.run(provider, payload, state, run_id, attempt, settings)
        out.consumer_view = record
        return out

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
            attempt: int = 1, settings: Optional["GenerationSettings"] = None
            ) -> StageOutcome:
        settings = settings or GenerationSettings()
        req = GenerationRequest(
            purpose=self.purpose, stage_id=self.stage_id,
            prompt_text=self.build_prompt(inputs),
            max_output_tokens=settings.max_output_tokens,
            deadline_s=settings.deadline_s, temperature=settings.temperature,
            seed=settings.seed,
            # The attempt budget travels WITH the call. Without this the value
            # was recorded by `GenerationSettings.as_record` and read by nobody,
            # so a campaign asking for one attempt got the provider's default.
            max_attempts=settings.max_attempts,
            # The run and attempt are the caller's to state, and the provider's
            # record is required to carry both. Passing them here is what lets a
            # model-run record be tied back to the run that produced it.
            run_id=run_id, stage_attempt=attempt,
            # WHICH PASS IS ASKING. Taken from the stage, because the stage is
            # the only thing that knows: `stage_id` above is the owner, and both
            # passes of s03 and s04 share it.
            responsibility_id=self.responsibility_id())
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
        refinement_only = False
        try:
            barrier = self.refinement_barrier(parsed, inputs, state)
            if barrier is not None:
                # ONLY the revision. Everything this response also proposed was
                # reasoned from the value being replaced, so committing it here
                # would be committing evidence for an arrangement that no longer
                # exists. It is not lost - the caller refreshes and calls again.
                ops, why = barrier
                ops = carry_invocation_premises(ops, self.invocation_premises(inputs))
                missing, refinement_only = [why], True
            else:
                ops = carry_invocation_premises(self.to_operations(parsed, inputs),
                                                self.invocation_premises(inputs))
                ops = ops + self.refinement_operations(parsed, inputs, state)
                ops = ops + self.derived_operations(parsed, inputs, state)
                if inputs.get(REPAIR_KEY):
                    # A REPAIR REVISES WHAT STANDS. The same three hooks said
                    # what the response states; this rewrites CREATE-of-what-
                    # exists and EXTEND-over-a-value into the controlled
                    # revisions the boundary accepts, with this round as the
                    # reason on every one of them.
                    ops = self.repair_operations(ops, inputs, state)
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
                            refinement_only=refinement_only,
                            raw_response=result.response.raw_text)
