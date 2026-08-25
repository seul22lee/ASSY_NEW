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

#: TWO CONVERGENCES, TWO BUDGETS. Declared before the loop runs and never tuned
#: to make a case converge.
#:
#: STRUCTURAL closure and NUMERICAL settlement are different questions asked of
#: different evidence: one supplies geometry the design commits to and the
#: embodiment lacks, the other settles dimensions once that geometry exists.
#: They shared one budget once, and structural rounds spent it before the solver
#: ever ran - a branch could exhaust "settlement" without a single settlement
#: having been attempted. Each now has its own bound, its own repeated-state
#: memory and its own verdict; neither can consume the other's.
DEFAULT_ROUND_BUDGET = 3
DEFAULT_STRUCTURAL_BUDGET = 3

#: Which convergence a round belongs to, decided by what the round found.
STRUCTURAL = "structural"
NUMERICAL = "numerical"

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
    # UNIT G. THE ARTIFACT IS VALIDATED AS A MECHANISM. Expected bodies,
    # feature correspondence, derived poses in every state, solid interference
    # under s04's contact policy, motion along every transition on s04's
    # sampling, reserved regions, exchange files. Findings are typed and owned;
    # a compile whose solids contradict the design is a compile with findings,
    # never a success by another name - and never a failure invented here.
    findings: tuple = ()
    if result.ok:
        from . import artifact
        report = artifact.validate(state, branch, result, out_dir=out_dir)
        result.artifact = report.as_record()
        findings = tuple(f.as_record() for f in report.findings)
    # The settled parameters the compiler actually consumed become premises of
    # the signature, so a re-solve stales the geometry it produced.
    ops = (canonical_io.compilation_operations(
        result, signature, sorted(canonical_io.resolved_values(state, branch)))
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
                          "failed_feature": result.failed_feature,
                          "failed_step": result.failed_step})
    contradicted = any(f.get("evaluable") and f.get("kind") != "NOT_EVALUABLE" for f in findings)
    execution = progression.record_deterministic(DeterministicExecution(
        responsibility_id="s07", stage_id="s07",
        outcome=("compiled_with_findings" if contradicted else "compiled") if result.ok
        else "compile_failed",
        input_digest=_digest([f.entity_id for f in canonical_io.read_features(state, branch)]),
        patch_applied=applied, problems=tuple(problems),
        evidence_id=signature if applied else None, findings=findings))
    return result, execution


@dataclass
class ConvergenceOutcome:  # noqa: D101
    """What the settlement loop concluded, and how it got there."""

    status: str
    rounds: int = 0
    reports: List[Any] = field(default_factory=list)
    states_seen: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = field(default_factory=list)
    escalation: Optional[str] = None

    refinements: List[Dict[str, Any]] = field(default_factory=list)
    #: Repair rounds spent in each convergence, separately. `rounds` is every
    #: round the loop ran; these say which budget paid for what.
    structural_rounds: int = 0
    settlement_rounds: int = 0
    #: The convergence the loop ended in, so a verdict is read against the
    #: question it answers.
    phase: Optional[str] = None

    def as_record(self) -> Dict[str, Any]:
        return {"status": self.status, "rounds": self.rounds, "phase": self.phase,
                "structural_rounds": self.structural_rounds,
                "settlement_rounds": self.settlement_rounds,
                "refinements": [dict(r) for r in self.refinements],
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
#: UNIT G. The structural convergence spent its own budget without the entry
#: gate admitting the branch: the embodiment never became buildable, so no
#: settlement was ever attempted. Distinct from BUDGET_EXHAUSTED, which means
#: the solver ran and the numbers did not converge.
STRUCTURE_UNCLOSED = "STRUCTURE_UNCLOSED"


def settle(state, progression: Progression, *,
           refine: Optional[Callable[[int, Any], bool]] = None,
           branch: Optional[str] = None,
           round_budget: int = DEFAULT_ROUND_BUDGET,
           structural_budget: int = DEFAULT_STRUCTURAL_BUDGET) -> ConvergenceOutcome:
    """The bounded s05 <-> s06 loop, as TWO bounded convergences.

    `refine` is supplied by the caller and is what re-invokes the producing
    responsibility that owns the decision - the loop itself changes nothing,
    because a loop that mutated state directly would be a second producer. It
    returns True when it actually changed something; False means nobody could,
    and the loop stops rather than spinning.

    UNIT G. STRUCTURAL CLOSURE AND NUMERICAL SETTLEMENT ARE BOUNDED SEPARATELY.
    A round is structural when the entry gate refused the embodiment - geometry
    the design commits to is missing, no solver ran, and what is owed is a
    feature or a constraint. It is numerical when the solver ran and the numbers
    did not hold. These consumed one budget once, and the consequence was not a
    slow loop but a wrong verdict: three structural rounds exhausted "settlement"
    on a branch whose numbers had never once been solved, and the run reported a
    settlement failure for a design that never reached settlement. Each phase now
    spends its own budget, remembers its own states, and ends in its own verdict
    - STRUCTURE_UNCLOSED when the embodiment never became buildable,
    BUDGET_EXHAUSTED when the numbers would not converge. Raising a budget would
    not have fixed this; only telling the two questions apart does.

    Termination, per phase: its budget of repair rounds, or a repeated state -
    the typed causes together with the identity of the embodiment itself. Not
    monotone reduction. A phase's budget bounds the REPAIRS it may ask for; the
    round that follows a repair is the check on it and is always run.
    """
    outcome = ConvergenceOutcome(status=BUDGET_EXHAUSTED)
    budgets = {STRUCTURAL: structural_budget, NUMERICAL: round_budget}
    spent = {STRUCTURAL: 0, NUMERICAL: 0}
    seen: Dict[str, List[Any]] = {STRUCTURAL: [], NUMERICAL: []}
    while True:
        outcome.rounds += 1
        report, _ = execute_settlement(state, progression, branch=branch,
                                       attempt=outcome.rounds)
        outcome.reports.append(report)
        if report.solver_status == ir.FEASIBLE:
            outcome.status = SETTLED
            return outcome

        # WHICH CONVERGENCE THIS ROUND BELONGS TO, read from what it found.
        phase = STRUCTURAL if report.solver_status == ir.NOT_READY else NUMERICAL
        outcome.phase = phase
        if phase is STRUCTURAL and refine is None:
            # UNIT F. No producer was supplied to answer the gate: the branch is
            # not ready and nothing here can supply what it lacks. A numerical
            # round with no producer falls through to the escalation below,
            # which is what it has always been.
            outcome.status = NOT_READY
            return outcome

        # UNIT G. WHAT "THE SAME STATE" MEANS. The typed causes - the solver's
        # status, the constraints in conflict, the parameters left free, the
        # prerequisite kinds and their subjects - together with the IDENTITY OF
        # THE EMBODIMENT ITSELF. Two of those were free-text problem strings
        # once, which made a repeat depend on how a message was worded and let a
        # reworded report read as progress; and comparing causes alone called it
        # a cycle when a revision HAD changed the design and the solver happened
        # to report the same conflict. A round repeats only when nothing about
        # the embodiment or the report changed. Each phase remembers its own:
        # a structural state and a numerical one are not the same question, and
        # returning to a structural defect after settling numbers is not a loop.
        causes = _settlement_causes(state, report, branch)
        signature = (report.solver_status, tuple(sorted(report.conflicting)),
                     tuple(sorted(report.free_parameters)), causes,
                     embodiment_identity(state, branch))
        if signature in seen[phase]:
            # The same unanswered question over the same embodiment: asking
            # again would receive the same answer.
            outcome.status = CYCLE
            progression.fail(CONTRACT_CONDITION, "s06",
                             "%s convergence repeated a state; this is a cycle" % phase,
                             {"phase": phase, "solver_status": report.solver_status,
                              "conflicting": list(report.conflicting),
                              "free": list(report.free_parameters),
                              "prerequisites": [list(c) for c in causes],
                              "embodiment": signature[-1]})
            return outcome
        seen[phase].append(signature)
        outcome.states_seen.append(signature)

        if spent[phase] >= budgets[phase]:
            # THIS phase is out of repairs. The other's budget is not borrowed:
            # a structural failure never spends a settlement round, and the
            # verdict says which question went unanswered.
            outcome.status = (STRUCTURE_UNCLOSED if phase is STRUCTURAL
                              else BUDGET_EXHAUSTED)
            outcome.escalation = (
                "%s convergence spent its budget of %d repair round(s); %s"
                % (phase, budgets[phase],
                   "the embodiment never became buildable and no settlement was "
                   "attempted" if phase is STRUCTURAL
                   else "the numbers did not converge"))
            progression.fail(CONTRACT_CONDITION, "s06", outcome.escalation,
                             {"phase": phase, "budget": budgets[phase],
                              "structural_rounds": outcome.structural_rounds,
                              "settlement_rounds": outcome.settlement_rounds})
            return outcome

        spent[phase] += 1
        outcome.structural_rounds = spent[STRUCTURAL]
        outcome.settlement_rounds = spent[NUMERICAL]
        if refine is None or not refine(outcome.rounds, report):
            outcome.status = (NOT_READY if phase is STRUCTURAL else ESCALATED)
            outcome.escalation = (
                "no authorized producer changed a placement, a dimension or a "
                "feature alternative; what remains is owned elsewhere and "
                "escalates rather than being changed here")
            progression.fail(CONTRACT_CONDITION, "s05", outcome.escalation,
                             {"phase": phase, "solver_status": report.solver_status,
                              "may_not_change": list(MAY_NOT_CHANGE)})
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


# ==========================================================================
# UNIT G. THE EMBODIMENT LOOP: s06's report as s05's repair input.
#
# An infeasible or underdetermined settlement is EMBODIMENT SETTLEMENT
# FEEDBACK (S06_CONTRACT): not a mechanism verdict, not something the solver
# fixes, and not something the compiler builds around. The producing
# responsibility revises - through the one invocation boundary, in the stage
# framework's own repair mode, one ordinary attempt per round, bounded by
# `settle`'s round budget - and the solver is asked again. This is the refine
# hook `settle` always took; what was missing was the report becoming the
# stage's input.
# ==========================================================================
def settlement_findings(state, report, branch: Optional[str]) -> List[Dict[str, Any]]:
    """The solver's report as typed rows a producing stage can answer."""
    from ..stages.s05_embodiment import (SETTLEMENT_INFEASIBLE, SETTLEMENT_UNDERDETERMINED,
                                         SETTLEMENT_UNSUPPORTED)

    rows: List[Dict[str, Any]] = []
    if report.solver_status == ir.NOT_READY:
        # THE ENTRY GATE'S REFUSAL IS A TYPED FINDING, NOT A VERDICT AND NOT A
        # SENTENCE (Unit G). What the gate refuses - an interface with no
        # realizing feature, a clearance no constraint governs, a body with no
        # material - is a STRUCTURAL defect: the design committed to something
        # the embodiment does not contain, and no number would express it. It
        # comes from the shared embodiment layer with its kind, its subjects and
        # its OWNER, and it is routed by that owner: s05's to revise, anyone
        # else's to escalate. Returning it as a dead end left the branch exactly
        # as unbuildable as before, with the one producer able to fix it never
        # asked; collapsing it into a settlement code would have told that
        # producer to adjust a number instead.
        return [{"code": f.kind, "owner": f.owner, "subjects": list(f.subjects),
                 "detail": f.detail, "structural": True}
                for f in canonical_io.prerequisite_findings(state, branch)]
    constraints = {c["entity_id"]: c for c in state.standing("Constraint")}
    parameters = {p["entity_id"]: p for p in state.standing("Parameter")}
    detail_by_constraint: Dict[str, str] = {}
    for problem in report.problems:
        for cid in report.conflicting:
            if cid in problem:
                detail_by_constraint[cid] = problem
    for cid in sorted(report.conflicting):
        rec = constraints.get(cid) or {}
        rows.append({"code": SETTLEMENT_INFEASIBLE, "constraint": cid,
                     "expression": json.dumps(rec.get("expression"), sort_keys=True),
                     "detail": detail_by_constraint.get(cid, "in the conflicting set")})
    for pid in sorted(report.free_parameters):
        rec = parameters.get(pid) or {}
        rows.append({"code": SETTLEMENT_UNDERDETERMINED, "parameter": pid,
                     "symbol": rec.get("symbol")})
    if report.solver_status == ir.UNSUPPORTED_FORMULATION:
        # the solver names the constraint it could not reduce, first
        for problem in report.problems:
            head, _, why = problem.partition(":")
            cid = head.strip()
            rec = constraints.get(cid) or {}
            rows.append({"code": SETTLEMENT_UNSUPPORTED, "constraint": cid if rec else None,
                         "expression": json.dumps(rec.get("expression"), sort_keys=True) if rec else None,
                         "detail": why.strip() or problem})
    if not rows and report.solver_status not in (ir.FEASIBLE, ir.NOT_READY):
        rows.append({"code": report.solver_status.upper(), "detail": "; ".join(report.problems)})
    return rows


def _row_text(family: str, rec: Dict[str, Any]) -> str:
    """One standing record as the line the producing stage reads it back in."""
    eid = rec["entity_id"]
    if family == "Parameter":
        return "%s %s [%s]%s" % (eid, rec.get("symbol"), rec.get("unit"),
                                 " role=" + str(rec.get("role")) if rec.get("role") else "")
    if family == "Constraint":
        return "%s %s %s" % (eid, rec.get("basis") or "",
                             json.dumps(rec.get("expression"), sort_keys=True))
    if family == "Feature":
        return "%s %s on %s at %s" % (eid, rec.get("feature_kind"), rec.get("body"),
                                      (rec.get("placement") or {}).get("datum"))
    if family == "Realization":
        return "%s discharges %s: %s" % (eid, ", ".join(rec.get("addresses_obligations") or ()),
                                         rec.get("verification_predicate"))
    if family == "UnresolvedDecision":
        return "%s %s" % (eid, rec.get("decision"))
    return "%s %s" % (eid, "; ".join("%s=%s" % (k, v) for k, v in sorted(rec.items())
                                     if not k.startswith("_") and k != "entity_id"))


def standing_embodiment(state, branch: Optional[str]) -> Dict[str, List[str]]:
    """What the branch's embodiment is, by family and id, for the revising
    invocation - EVERY family the producing stage authors, because a revision
    withdraws by omission and the model may only omit what it was shown."""
    from ..stages.s05_embodiment import S05Embodiment

    snapshot = S05Embodiment().embodiment_snapshot(state, branch)
    return {family: [_row_text(family, state.entities[eid]) for eid in ids]
            for family, ids in sorted(snapshot.items())}


def embodiment_identity(state, branch: Optional[str]) -> str:
    """WHAT THE EMBODIMENT IS, as one value. The same snapshot the model is
    shown and a revision withdraws from, hashed over its declared fields, so
    "did anything actually change?" is answered by the state rather than by
    whether a report's wording moved."""
    from ..stages.s05_embodiment import S05Embodiment

    snapshot = S05Embodiment().embodiment_snapshot(state, branch)
    payload = {family: [{k: v for k, v in sorted(state.entities[eid].items())
                         if not k.startswith("_")} for eid in ids]
               for family, ids in sorted(snapshot.items())}
    return _digest({"branch": branch, "embodiment": payload})


def _settlement_causes(state, report, branch: Optional[str]):
    """The prerequisite findings as typed, comparable causes: (kind, subjects).
    Empty whenever the gate let the solve run - a numerical report has no
    structural cause."""
    if report.solver_status != ir.NOT_READY:
        return ()
    return tuple(sorted((f.kind,) + tuple(f.subjects)
                        for f in canonical_io.prerequisite_findings(state, branch)))


def embodiment_refinement(provider, state, progression: Progression, branch: Optional[str],
                          invocation=None):
    """A `settle` refine hook: hand s06's report to s05 as a repair round."""
    from ..pipeline.progression import execute_stage
    from ..stages.base import CAUSE_FINDINGS, CAUSE_PREREQUISITES, REPAIR_KEY
    from ..stages.s05_embodiment import S05Embodiment

    def refine(round_index: int, report) -> bool:
        rows = settlement_findings(state, report, branch)
        if not rows:
            return False
        structural = [r for r in rows if r.get("structural")]
        # ROUTED BY OWNER (Unit G). A prerequisite finding names whose record is
        # at fault. A malformed Joint is s03's; asking s05 to embody around it
        # would be asking one stage to answer for another's record, so the loop
        # escalates instead of inventing a repair.
        foreign = sorted({r.get("owner") for r in structural
                          if r.get("owner") != S05Embodiment.stage_id})
        if foreign:
            refine.records.append({
                "round": round_index, "findings": [r.get("code") for r in rows],
                "status": None, "problems": ["owned by %s, not s05" % ", ".join(foreign)],
                "declared_incompleteness": None, "patch_applied": False})
            return False
        cause = CAUSE_PREREQUISITES if structural else CAUSE_FINDINGS
        repair = {"round": round_index, "cause": cause, "findings": rows,
                  "settled": {k: round(v, 6) for k, v in sorted(report.settled.items())},
                  "current": standing_embodiment(state, branch)}
        outcome, execution = execute_stage(S05Embodiment(), provider, state, progression,
                                           inputs={"candidate": branch, REPAIR_KEY: repair},
                                           attempt=10 + round_index, invocation=invocation)
        applied = bool(execution is not None and getattr(execution, "patch_applied", False))
        # WHAT THE REVISION RETURNED, kept with the loop: a loop that escalates
        # must say whether the producing stage answered, was refused, or wrote.
        refine.records.append({
            "round": round_index, "findings": [r.get("code") for r in rows],
            "status": getattr(getattr(outcome, "execution_status", None), "value", None)
            if outcome is not None else None,
            "problems": list(getattr(outcome, "problems", None) or [])[:12] if outcome is not None else [],
            "declared_incompleteness": len(getattr(outcome, "declared_incompleteness", None) or [])
            if outcome is not None else None,
            "patch_applied": applied})
        return applied
    refine.records = []
    return refine


def settle_with_embodiment(state, progression: Progression, provider, *,
                           branch: Optional[str] = None, invocation=None,
                           round_budget: int = DEFAULT_ROUND_BUDGET,
                           structural_budget: int = DEFAULT_STRUCTURAL_BUDGET
                           ) -> ConvergenceOutcome:
    """s06 with s05 revising on feedback, bounded. The production loop.

    Two budgets, passed through as they are declared: closing the embodiment
    structurally may not spend the rounds settlement is allowed.
    """
    refine = embodiment_refinement(provider, state, progression, branch, invocation)
    outcome = settle(state, progression, branch=branch, round_budget=round_budget,
                     structural_budget=structural_budget, refine=refine)
    outcome.refinements = list(refine.records)
    return outcome
