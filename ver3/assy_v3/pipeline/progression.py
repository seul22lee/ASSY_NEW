"""Stage progression, patch acceptance and response-source provenance.

WHAT THIS OWNS

    which stages run, in what order, with what invocation identity
    how a stage is invoked - always through the authoritative boundary
    when an outcome is accepted into the DesignState and when it is not
    which layer a failure belongs to
    where each stage's response came from, as a recorded fact

WHAT IT DOES NOT OWN

    where a case lives on disk, and what a case is called. A case identifier
    inside this package would be FP-02, so the orchestration takes source TEXT
    and a provider, and the tools keep the directory layout.

RESPONSE SOURCE IS DECLARED, NEVER INFERRED

A run used to be "live" because it was started by the live runner. That is a fact
about a filename. Each provider now declares `response_source`, the progression
records what the provider serving each stage declared, and full-live qualification
reads those records. A provider that declares nothing is UNDECLARED and can never
satisfy a live claim - silence is not a live response.

WHY SIX STAGES AND NOT FOUR

"S01 to S04" names four contracts and SIX producing responsibilities: S03 is split
into topology and mobility passes, S04 into envelope and placement passes, because
one response could not carry either pair. A full-live check that tested four
strings would pass a run whose S03·B was replayed.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..providers.status import ExecutionStatus

# --------------------------------------------------------------------------
# Response source
# --------------------------------------------------------------------------

#: The response came from a provider contacted during this run.
LIVE = "LIVE"
#: The response was recorded earlier and is being replayed.
REPLAY = "REPLAY"
#: The provider declares nothing. Never treated as live.
UNDECLARED = "UNDECLARED"

#: Every LLM-producing RESPONSIBILITY from S01 through S04, in progression order.
#:
#: NOT stages. `s03` and `s04` are OWNERS - they say who may write the state - and
#: each owns two reasoning passes that ask different questions of different
#: premises. A set written in owner identities would contain `s03` once where two
#: distinct model calls happen, so a run whose S03·B was replayed would satisfy it.
#: The name says responsibilities because the first version of this said stages and
#: was wrong in exactly that way.
PRODUCING_RESPONSIBILITIES = ("s01", "s02", "s03a", "s03b", "s04a", "s04b")

# --------------------------------------------------------------------------
# Failure layers. Previously duplicated in two runners with slightly different
# membership, which is how the same condition came to have two names.
# --------------------------------------------------------------------------

#: The wire. Says nothing whatsoever about the design.
PROVIDER_CONDITION = "PROVIDER_CONDITION"
#: The response arrived and could not be used as one - truncated or unparseable.
RESPONSE_CONDITION = "RESPONSE_CONDITION"
#: Our code raised on a shape it did not expect. A defect in us, not in the model.
PARSER_DEFECT = "PARSER_DEFECT"
#: Well-formed and under-covered, or rejected by contract validation.
CONTRACT_CONDITION = "CONTRACT_CONDITION"
#: A validator objects to valid content. The only kind that is about reasoning.
CHECK_FINDING = "CHECK_FINDING"
#: What one stage could see of another's output.
INTERFACE_FINDING = "INTERFACE_FINDING"
#: The consumer context was insufficient, so the provider was never called.
#: Deliberately its own layer: "never asked" is not "asked and failed".
VIEW_INSUFFICIENT = "VIEW_INSUFFICIENT"

_PROVIDER_STATUSES = (ExecutionStatus.PROVIDER_RATE_LIMIT,
                      ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED,
                      ExecutionStatus.PROVIDER_UNAVAILABLE,
                      ExecutionStatus.PROVIDER_TIMEOUT)
_RESPONSE_STATUSES = (ExecutionStatus.RESPONSE_TRUNCATED,
                      ExecutionStatus.RESPONSE_PARSE_FAILURE)


def response_source_of(provider) -> str:
    """What the provider says it is. Never guessed from a class name or a path."""
    return getattr(provider, "response_source", UNDECLARED)


def provider_id_of(provider) -> str:
    pid = getattr(provider, "provider_id", None)
    if pid:
        return pid
    try:
        return provider.capabilities().provider_id
    except Exception:                                               # noqa: BLE001
        return "UNKNOWN"


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class StageExecution:
    """One producing pass's execution, as evidence rather than as a log line.

    TWO IDENTITIES, BECAUSE THERE ARE TWO QUESTIONS.

        stage_id          WHO OWNS THE WRITE. Both S03 passes author s03 state
                          under s03's authority, and `DesignState.may_create`
                          resolves permission with this.
        responsibility_id WHICH PASS WAS REASONING. s03a and s03b ask different
                          questions of different premises, so they are different
                          consumers and different producing responsibilities.

    One field carried both meanings in the first version of this module, holding
    the owner. Every pass-level lookup then asked for `s03b` and got nothing, so a
    genuinely all-live run could never qualify. Keeping them apart is what the
    Stage base class already does; this just stops discarding half of it.
    """

    stage_id: str
    responsibility_id: str
    response_source: str
    provider_id: str
    execution_status: str
    #: The ConsumerView's status, and whether a view record exists at all. A live
    #: stage with no view record is the S9-A bypass, and it is visible here.
    view_status: Optional[str] = None
    consumer_view_recorded: bool = False
    patch_applied: bool = False
    problems: Tuple[str, ...] = ()
    #: True when committed state for this stage was placed without invoking it.
    #: A seeded stage is not a replayed stage: nothing was served at all.
    seeded: bool = False

    def as_record(self) -> Dict[str, Any]:
        return {"stage_id": self.stage_id,
                "responsibility_id": self.responsibility_id,
                "response_source": self.response_source,
                "provider_id": self.provider_id,
                "execution_status": self.execution_status,
                "view_status": self.view_status,
                "consumer_view_recorded": self.consumer_view_recorded,
                "patch_applied": self.patch_applied,
                "seeded": self.seeded, "problems": list(self.problems)}


@dataclass
class Progression:
    """The executions of one chain, in order, with their failures."""

    executions: List[StageExecution] = field(default_factory=list)
    failures: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, execution: StageExecution) -> StageExecution:
        self.executions.append(execution)
        return execution

    def fail(self, layer: str, stage: str, what: str, detail: Any = None) -> None:
        self.failures.append({"kind": layer, "stage": stage, "what": what,
                              "detail": detail})

    def by_responsibility(self, responsibility_id: str) -> Optional[StageExecution]:
        """The execution of one PRODUCING PASS.

        Named for what it looks up. The previous `by_stage` took an owner, so
        `by_stage("s03b")` was always None and `by_stage("s03")` returned
        whichever of the two passes ran first.
        """
        for e in self.executions:
            if e.responsibility_id == responsibility_id:
                return e
        return None

    def owned_by(self, stage_id: str) -> List[StageExecution]:
        """Every pass an OWNER ran. Two for s03 and s04, one for s01 and s02."""
        return [e for e in self.executions if e.stage_id == stage_id]

    def response_sources(self) -> Dict[str, str]:
        """Keyed by responsibility: an owner key would lose one of two passes."""
        return {e.responsibility_id: e.response_source for e in self.executions}

    def as_record(self) -> Dict[str, Any]:
        return {"executions": [e.as_record() for e in self.executions],
                "response_sources": self.response_sources(),
                "failures": list(self.failures)}


# --------------------------------------------------------------------------
# The one invocation path
# --------------------------------------------------------------------------

def execute_stage(stage, provider, state, progression: Progression, *,
                  inputs: Optional[Dict[str, Any]] = None, attempt: int = 1,
                  invocation=None, apply_patch: bool = True):
    """Invoke one stage through the authoritative boundary and accept its patch.

    THE ONLY PLACE A STAGE IS INVOKED. `stage.invoke` builds the ConsumerView,
    refuses to call the provider when the view is not ready, and records the view;
    calling the inner driver instead skips all three, which is exactly what the
    live S01 path used to do. Routing every stage through here is what makes
    "replay and live share one path" a structural fact rather than a convention.

    Returns (outcome, execution). Never raises on a provider or response
    condition; a raise from our own code is caught, classified as PARSER_DEFECT
    and recorded, because a traceback in one stage would otherwise destroy the
    evidence from every stage after it.
    """
    # BOTH taken from the stage itself. A caller cannot supply the responsibility,
    # because the stage is the only thing that knows which pass it is - which is
    # the whole reason `pass_id` is declared on the class rather than passed in.
    stage_id = stage.stage_id
    responsibility_id = stage.responsibility_id()
    source = response_source_of(provider)
    pid = provider_id_of(provider)

    try:
        outcome = stage.invoke(provider, state, state.run_id, inputs or {},
                               attempt=attempt, invocation=invocation)
    except Exception as exc:                                        # noqa: BLE001
        progression.fail(PARSER_DEFECT, responsibility_id,
                         "%s: %s" % (type(exc).__name__, exc),
                         traceback.format_exc(limit=6))
        return None, progression.record(StageExecution(
            stage_id=stage_id, responsibility_id=responsibility_id,
            response_source=source, provider_id=pid,
            execution_status="RAISED", problems=("%s: %s" % (type(exc).__name__, exc),)))

    view = outcome.consumer_view or {}
    view_status = view.get("status") if isinstance(view, dict) else None
    status = outcome.execution_status

    # ---- the layer this failure belongs to -----------------------------
    if status is ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT:
        progression.fail(VIEW_INSUFFICIENT, responsibility_id, status.value,
                         outcome.problems)
    elif status in _PROVIDER_STATUSES:
        progression.fail(PROVIDER_CONDITION, responsibility_id, status.value,
                         outcome.problems)
    elif status in _RESPONSE_STATUSES:
        progression.fail(RESPONSE_CONDITION, responsibility_id, status.value,
                         outcome.problems)
    elif outcome.patch is None:
        progression.fail(CONTRACT_CONDITION, responsibility_id,
                         "no patch: %s" % status.value, outcome.problems)
    elif outcome.problems:
        progression.fail(CONTRACT_CONDITION, responsibility_id,
                         "contract validation", outcome.problems)
    elif outcome.declared_incompleteness and not outcome.refinement_only:
        progression.fail(CONTRACT_CONDITION, responsibility_id,
                         "declared incomplete", outcome.declared_incompleteness)

    # ---- acceptance ----------------------------------------------------
    # One rule for both response sources: a patch is committed when it exists and
    # contract validation raised nothing. A runner that applied on slightly
    # different terms would be a second state semantics.
    applied = False
    if apply_patch and outcome.patch is not None and not outcome.problems:
        state.apply(outcome.patch)
        applied = True

    execution = progression.record(StageExecution(
        stage_id=stage_id, responsibility_id=responsibility_id,
        response_source=source, provider_id=pid,
        execution_status=status.value, view_status=view_status,
        consumer_view_recorded=bool(view), patch_applied=applied,
        problems=tuple(outcome.problems or ())))
    return outcome, execution


def note_seeded(progression: Progression, responsibility_id: str, why: str,
                stage_id: Optional[str] = None) -> StageExecution:
    """Record that a stage's state was placed without the stage being invoked.

    Seeding is not replay. Replay serves a recorded RESPONSE through the real
    parser and contracts; seeding puts committed state there directly. Both
    disqualify a full-live claim, and conflating them would hide which happened.
    """
    progression.fail(VIEW_INSUFFICIENT, responsibility_id, "seeded upstream state",
                     why)
    return progression.record(StageExecution(
        # The owner defaults to the responsibility with any pass letter removed,
        # which is the mapping `_authority_of` already uses elsewhere.
        stage_id=stage_id or _owner_of(responsibility_id),
        responsibility_id=responsibility_id,
        response_source=UNDECLARED, provider_id="NONE",
        execution_status="SEEDED", seeded=True, problems=(why,)))


def _owner_of(responsibility_id: str) -> str:
    """s03a -> s03. The same rule the state and view layers already apply."""
    import re
    return (responsibility_id[:-1]
            if re.match(r"^s\d+[a-z]$", responsibility_id) else responsibility_id)


# --------------------------------------------------------------------------
# Window 1 - the progression that existed three times
# --------------------------------------------------------------------------

def window1(provider, state, request_text: str, progression: Progression, *,
            design_profile: Any = None, s01_provider=None):
    """S01 then S02, through the authoritative boundary, for either source.

    `s01_provider` exists for the diagnostic that replays S01 while S02 runs live.
    It is a separate PROVIDER, not a separate code path: the same invocation, the
    same acceptance, the same records - and the response source it declares is
    what stops such a run from later being called full-live.

    The design profile travels with S01's inputs for BOTH sources. It used to be
    passed only on the seeding path, so a live run silently ingested no profile
    while a replayed one did - a divergence that produced different committed
    state from the same source.
    """
    out1, _e1 = execute_stage(
        _S01(), s01_provider or provider, state, progression,
        inputs={"request_text": request_text, "design_profile": design_profile})
    if out1 is None or out1.patch is None or out1.problems:
        return out1, None

    stage2 = _S02()
    # The interface question: what S02 can see of S01's output. Recorded as an
    # interface finding rather than raised, because INV-002 is enforced by the
    # boundary and this is the harness reporting on it.
    view2 = stage2.consumer_view(state)
    if "SourceClause" in view2.payload():
        progression.fail(INTERFACE_FINDING, "s02", "source text reached s02",
                         sorted(view2.payload()))

    out2, _e2 = execute_stage(stage2, provider, state, progression)
    return out1, out2


def _S01():
    from ..stages.s01_requirement_capture import S01RequirementCapture
    return S01RequirementCapture()


def _S02():
    from ..stages.s02_obligation_and_candidates import S02ObligationAndCandidates
    return S02ObligationAndCandidates()


# --------------------------------------------------------------------------
# Window 2 - the passes that carry one candidate into geometry
# --------------------------------------------------------------------------

def s03_passes(provider, state, progression: Progression, candidate: Any,
               invocation=None):
    """S03·A then S03·B for ONE candidate.

    Two passes because one response could not carry both the topology and the
    mobility grid. Pass B is attempt 2 of the same responsibility and shares the
    invocation identity, so its patch is attributed to the same branch.
    """
    from ..stages.s03_topology_and_mobility import (S03BMobilityAndAssembly,
                                                    S03TopologyAndMobility)
    out_a, _ = execute_stage(S03TopologyAndMobility(), provider, state, progression,
                             inputs={"candidate": candidate}, attempt=1,
                             invocation=invocation)
    if out_a is None or out_a.patch is None or out_a.problems:
        return out_a, None
    branch = candidate.get("entity_id") if isinstance(candidate, dict) else candidate
    out_b, _ = execute_stage(S03BMobilityAndAssembly(), provider, state, progression,
                             inputs={"candidate": branch}, attempt=2,
                             invocation=invocation)
    return out_a, out_b


def s04_passes(provider, state, progression: Progression, invocation=None,
               refreshes: int = 1):
    """S04·A then S04·B, each with a bounded refinement refresh.

    A stage reporting refinement-only committed a justified revision and withheld
    everything it had reasoned from the value it replaced. It is asked again
    against a view that now holds the revision. ONE refresh: a second
    refinement-only outcome is a stage revising without converging, which is
    reported rather than looped on.
    """
    from ..stages.s04_envelope_and_motion import (S04AEnvelopeAndReach,
                                                  S04BPlacementAndMotion)
    outcomes = []
    branch = getattr(invocation, "branch", None)
    for attempt, stage in enumerate((S04AEnvelopeAndReach(),
                                     S04BPlacementAndMotion()), start=1):
        out = None
        for refresh in range(refreshes + 1):
            out, _ = execute_stage(stage, provider, state, progression,
                                   inputs={"candidate": branch}, attempt=attempt,
                                   invocation=invocation)
            if out is None or out.patch is None or out.problems:
                return outcomes + [out]
            if not out.refinement_only:
                break
            if refresh == refreshes:
                progression.fail(
                    CONTRACT_CONDITION, stage.responsibility_id(),
                    "still revising after %d refresh(es); the realization was never "
                    "reasoned from a settled arrangement" % refreshes,
                    out.declared_incompleteness)
        outcomes.append(out)
    return outcomes


def execute_s01_to_s04(provider, state, request_text: str, choose_candidate, *,
                       design_profile: Any = None, s01_provider=None,
                       invocation_for=None, progression: Optional[Progression] = None
                       ) -> Progression:
    """THE canonical chain: source text in, committed S01..S04 state out.

    `choose_candidate` is supplied by the caller because embodying every candidate
    is what keeps the design space open until the gate has evidence (INV-007), and
    deciding which to carry is a harness policy rather than a stage semantic. What
    is NOT the caller's is anything below: order, invocation, acceptance and
    provenance are the same whatever the response source.

    Everything downstream of S04 - feasibility, comparison, selection and its human
    authority, lifecycle, and the independent assurance snapshot - is deliberately
    NOT run here. Those already have exactly one implementation each in their own
    modules, and folding them in would make this function an authority over
    semantics it does not own.
    """
    progression = progression or Progression()
    _out1, out2 = window1(provider, state, request_text, progression,
                          design_profile=design_profile, s01_provider=s01_provider)
    if out2 is None or out2.patch is None or out2.problems:
        return progression

    candidate = choose_candidate(state)
    if candidate is None:
        progression.fail(CONTRACT_CONDITION, "s03",
                         "no candidate to embody; s02 produced none")
        return progression

    invocation = invocation_for(candidate) if invocation_for else None
    _a, out_b = s03_passes(provider, state, progression, candidate,
                           invocation=invocation)
    if out_b is None or out_b.patch is None or out_b.problems:
        return progression
    s04_passes(provider, state, progression, invocation=invocation)
    return progression


# --------------------------------------------------------------------------
# Full-live qualification
# --------------------------------------------------------------------------

def full_live_qualification(progression: Progression,
                            required: Sequence[str] = PRODUCING_RESPONSIBILITIES
                            ) -> Tuple[bool, List[str]]:
    """Does this run qualify as end-to-end live evidence, and if not, why not?

    Every required producing stage must have executed, against a provider that
    declared LIVE, with nothing seeded. The reasons are returned rather than a
    bare False, because "which stage was not live" is the whole question.

    A replayed S01 cannot be hidden by a live S04. That is the failure mode this
    predicate exists to make impossible.
    """
    reasons: List[str] = []
    for responsibility_id in required:
        execution = progression.by_responsibility(responsibility_id)
        if execution is None:
            reasons.append("%s did not execute" % responsibility_id)
            continue
        if execution.seeded:
            reasons.append("%s was seeded, not executed" % responsibility_id)
            continue
        if execution.response_source != LIVE:
            reasons.append("%s response source is %s, not LIVE"
                           % (responsibility_id, execution.response_source))
    return (not reasons), reasons
