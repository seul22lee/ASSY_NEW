"""Running the deterministic downstream, and the settlement loop around it.

WHAT THE LOOP IS FOR

S06_CONTRACT names a convergence block of s04b, s05 and s06 - the "geometric
settlement loop". s05 proposes geometry and the constraints it implies; s06 says
whether values exist. When they do not, something has to change, and the contract
is specific about what may: placements, dimensions and feature alternatives. Body,
RigidGroup, Joint, interaction_kind, MobilityExpectation, LoadPath and AssemblyStep
may NOT - those escalate to s03, because a loop permitted to change them would
mean "redo the whole design".

TERMINATION IS NOT MONOTONE, AND THE CONTRACT SAYS WHY

The obvious rule - stop when the unsatisfied set stops shrinking - is written down
in S06_CONTRACT as WRONG, with the replay that falsifies it: round 1 fixes a
clearance while round 2 breaks a lift-only property, leaving the set the same size
in a problem that was solvable and was solved. So termination is a ROUND BUDGET or
a REPEATED STATE, where a state is the pair (unsatisfied constraints, changed
parameters). A repeated state is a genuine cycle and is reported as one.

EVERY ROUND IS RECORDED

Not just the last. A settlement that took three rounds is three
DeterministicExecutions, and the escalation that ended a failing loop is a
recorded failure naming the responsibility that owns the decision.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..pipeline.progression import (CONTRACT_CONDITION, DeterministicExecution,
                                    Progression)
from ..state.patch import StagePatch
from . import canonical_io, ir

#: Declared before the loop runs, never tuned to make a case converge.
DEFAULT_ROUND_BUDGET = 3

#: What the loop may change, from S06_CONTRACT.convergence_block.scope.
MAY_CHANGE = ("placements", "dimensions", "feature alternatives")
#: What it may not. Reaching one of these ends the loop in an ESCALATION.
MAY_NOT_CHANGE = ("Body", "RigidGroup", "Joint", "interaction_kind",
                  "MobilityExpectation", "LoadPath", "AssemblyStep")


def _digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   default=str).encode()).hexdigest()


def _patch(state, stage_id: str, ops, attempt: int) -> StagePatch:
    return StagePatch(
        patch_id="%s-%s-d%d" % (state.run_id, stage_id, attempt),
        run_id=state.run_id, stage_id=stage_id, stage_attempt=attempt,
        parent_state_hash=state.state_hash(), operations=list(ops),
        execution_status="SUCCESS",
        provenance={"purpose": "deterministic downstream", "provider": None})


def execute_settlement(state, progression: Progression, *,
                       branch: Optional[str] = None, attempt: int = 1
                       ) -> Tuple[Any, DeterministicExecution]:
    """Run s06 against committed state and record what it concluded.

    Writes only on FEASIBLE. An infeasible or underdetermined report is evidence
    and evidence does not become a value - which is the whole reason the loop
    exists rather than a fallback.

    UNIT F. THE ENTRY GATE COMES FIRST. A branch with no current embodiment
    program is `not_ready`: no solver runs, nothing is written, the failure is
    recorded. "s05 produced nothing" must never read as "the empty system
    solved".
    """
    ready, why_not = canonical_io.settlement_readiness(state, branch)
    if not ready:
        report = canonical_io._solver.SolverReport(
            solver_status=ir.NOT_READY, problems=list(why_not),
            formulation_sha256=_digest({"branch": branch, "not_ready": why_not}))
        progression.fail(CONTRACT_CONDITION, "s06", ir.NOT_READY, why_not)
        execution = progression.record_deterministic(DeterministicExecution(
            responsibility_id="s06", stage_id="s06", outcome=ir.NOT_READY,
            input_digest=report.formulation_sha256, patch_applied=False,
            problems=tuple(why_not), evidence_id=None))
        return report, execution
    report, params = canonical_io.solve_from_state(state, branch)
    evidence = canonical_io.evidence_identity(report)
    ops = canonical_io.settlement_operations(report, params, evidence)
    problems: List[str] = list(report.problems)
    applied = False
    if ops:
        patch = _patch(state, "s06", ops, attempt)
        refusals = state.validate(patch)
        if refusals:
            problems.extend(refusals)
        else:
            state.apply(patch)
            applied = True
    if report.solver_status != ir.FEASIBLE:
        progression.fail(CONTRACT_CONDITION, "s06", report.solver_status,
                         report.problems)
    execution = progression.record_deterministic(DeterministicExecution(
        responsibility_id="s06", stage_id="s06", outcome=report.solver_status,
        input_digest=report.formulation_sha256, patch_applied=applied,
        problems=tuple(problems),
        evidence_id=evidence if applied else None))
    return report, execution


def execute_compilation(state, progression: Progression, *,
                        out_dir: Optional[str] = None,
                        branch: Optional[str] = None, attempt: int = 1
                        ) -> Tuple[Any, DeterministicExecution]:
    """Run s07 against committed state and register what compiled.

    A failed compile registers nothing. There is no partial signature and no
    half-written artifact reference, because an artifact that exists in state is
    read as current.

    UNIT F. THE ENTRY GATE COMES FIRST. No program, an unsettled reference, an
    unfeasible or absent settlement, a statement in the wrong unit, or a
    standing post-settlement occupancy finding refuses compilation before the
    kernel is asked; the reason is recorded and nothing is written. A compile
    over nothing was once a success with a signature over `{}`; it is not.
    """
    ready, why_not = canonical_io.compilation_readiness(state, branch)
    if not ready:
        result = canonical_io._compiler.CompileResult(ok=False, problems=list(why_not))
        progression.fail(CONTRACT_CONDITION, "s07", "compilation not ready",
                         {"problems": why_not})
        execution = progression.record_deterministic(DeterministicExecution(
            responsibility_id="s07", stage_id="s07", outcome="not_ready",
            input_digest=_digest({"branch": branch, "not_ready": why_not}),
            patch_applied=False, problems=tuple(why_not), evidence_id=None))
        return result, execution
    result = canonical_io.compile_from_state(state, out_dir=out_dir, branch=branch)
    signature = canonical_io.signature_identity(result) if result.ok else None
    # The settled parameters the compiler actually consumed become premises of
    # the signature, so a re-solve stales the geometry it produced.
    ops = (canonical_io.compilation_operations(
        result, signature, sorted(canonical_io.resolved_values(state, branch)),
        statements_compiled=[s.entity_id for s in
                             canonical_io.read_program(state, branch).statements])
        if result.ok else [])
    problems = list(result.problems)
    applied = False
    if ops:
        patch = _patch(state, "s07", ops, attempt)
        refusals = state.validate(patch)
        if refusals:
            problems.extend(refusals)
        else:
            state.apply(patch)
            applied = True
    if not result.ok:
        progression.fail(CONTRACT_CONDITION, "s07", "compile failed",
                         {"problems": result.problems,
                          "failed_statement": result.failed_statement,
                          "dependency_cone": result.dependency_cone})
    execution = progression.record_deterministic(DeterministicExecution(
        responsibility_id="s07", stage_id="s07",
        outcome="compiled" if result.ok else "compile_failed",
        input_digest=_digest([s.entity_id for s in
                              canonical_io.read_program(state, branch).statements]),
        patch_applied=applied, problems=tuple(problems),
        evidence_id=signature if applied else None))
    return result, execution


@dataclass
class ConvergenceOutcome:
    """What the settlement loop concluded, and how it got there."""

    status: str
    rounds: int = 0
    reports: List[Any] = field(default_factory=list)
    states_seen: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = field(default_factory=list)
    escalation: Optional[str] = None

    def as_record(self) -> Dict[str, Any]:
        return {"status": self.status, "rounds": self.rounds,
                "escalation": self.escalation,
                "round_outcomes": [r.solver_status for r in self.reports],
                "states_seen": [list(map(list, s)) for s in self.states_seen]}


#: Loop verdicts.
SETTLED = "SETTLED"
BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
CYCLE = "REPEATED_STATE"
ESCALATED = "ESCALATED"
#: UNIT F. The branch had no embodiment program to settle for; the loop does
#: not spin on it - refining a placement cannot supply a program.
NOT_READY = "NOT_READY"


def settle(state, progression: Progression, *,
           refine: Optional[Callable[[int, Any], bool]] = None,
           branch: Optional[str] = None,
           round_budget: int = DEFAULT_ROUND_BUDGET) -> ConvergenceOutcome:
    """The bounded s05 <-> s06 loop.

    `refine` is supplied by the caller and is what re-invokes the producing
    responsibility that owns the decision - the loop itself changes nothing,
    because a loop that mutated state directly would be a second producer. It
    returns True when it actually changed something; False means nobody could,
    and the loop stops rather than spinning.

    Termination is the contract's: a round budget, or a repeated
    (unsatisfied-constraint, changed-parameter) state. Not monotone reduction.
    """
    outcome = ConvergenceOutcome(status=BUDGET_EXHAUSTED)
    for round_index in range(1, round_budget + 1):
        outcome.rounds = round_index
        report, _ = execute_settlement(state, progression, branch=branch,
                                       attempt=round_index)
        outcome.reports.append(report)
        if report.solver_status == ir.FEASIBLE:
            outcome.status = SETTLED
            return outcome
        if report.solver_status == ir.NOT_READY:
            outcome.status = NOT_READY
            return outcome

        signature = (tuple(sorted(report.conflicting)),
                     tuple(sorted(report.free_parameters)))
        if signature in outcome.states_seen:
            # The same unsatisfied set with the same free directions: refining
            # again would ask the same question and receive the same answer.
            outcome.status = CYCLE
            progression.fail(CONTRACT_CONDITION, "s06",
                             "settlement repeated a state; this is a cycle",
                             {"conflicting": list(signature[0]),
                              "free": list(signature[1])})
            return outcome
        outcome.states_seen.append(signature)

        if refine is None or not refine(round_index, report):
            outcome.status = ESCALATED
            outcome.escalation = (
                "no authorized producer changed a placement, a dimension or a "
                "feature alternative; what remains is owned elsewhere and "
                "escalates rather than being changed here")
            progression.fail(CONTRACT_CONDITION, "s05", outcome.escalation,
                             {"solver_status": report.solver_status,
                              "may_not_change": list(MAY_NOT_CHANGE)})
            return outcome
    return outcome


# ==========================================================================
# PRODUCTION ENTRY - the deterministic downstream of the SELECTED candidate
# ==========================================================================
#
# `execute_settlement` and `execute_compilation` take an optional branch, which
# is right for a test or a diagnostic that is deliberately looking at one
# alternative. It is wrong for production, twice over: `branch=None` reads every
# candidate's records at once and settles a system no single design describes,
# and a caller passing a branch string is a second place that decides which
# design is being built.
#
# There is one authority for that, and it is the same one s05 embodies against:
# a standing SelectionDecision. These entries resolve it themselves so no
# orchestrator has to, and so no orchestrator can resolve it differently.

class NoStandingSelection(RuntimeError):
    """Asked to run the downstream of the selected design when none is selected.

    Raised rather than defaulted. Falling back to "all branches" here would
    settle A's constraints against B's parameters and produce a design neither
    of them describes - silently, and with a GeometrySignature on the end of it.
    """


def current_selection(state) -> str:
    """The candidate the design is committed to, or refuse to guess.

    Delegates to the same `committed_branch` the ConsumerView uses. Branch
    resolution is not reimplemented here: two implementations of "which design
    are we building" is exactly one more than the architecture permits.
    """
    from ..state.design_state import Contracts
    from ..view.consumer_view import committed_branch

    branch = committed_branch(state, Contracts())
    if not branch:
        raise NoStandingSelection(
            "no standing SelectionDecision names a candidate, so there is no "
            "selected design to settle or compile")
    return branch


def settle_current_selection(state, progression: Progression, *,
                             attempt: int = 1):
    """s06 over the selected candidate's system, and nothing else."""
    return execute_settlement(state, progression,
                              branch=current_selection(state), attempt=attempt)


def compile_current_selection(state, progression: Progression, *,
                              out_dir: Optional[str] = None, attempt: int = 1):
    """s07 over the selected candidate's construction program, and nothing else."""
    return execute_compilation(state, progression, out_dir=out_dir,
                               branch=current_selection(state), attempt=attempt)
