"""THE S04 REPAIR LOOP: realize -> check -> diagnose -> repair -> re-check, bounded.

A SIBLING OF THE PROGRESSION, not part of it. `progression` owns which
producing passes run and how their patches are accepted, and it stops at
S04: nothing that READS S04's evidence runs inside it. This module is the S04
lifecycle that does read it - it asks the feasibility responsibility to
answer again over current state (the check), reads the REPAIRABLE_S04 rows
off its verdicts (the diagnosis, in the contract's classes), runs the
derivation passes that can repair without a model, and re-invokes the owning
pass through the progression's one invocation path with the findings as
REPAIR CONTEXT. Every stage patch is accepted by `execute_stage`'s rule; the
feasibility and derivation patches - deterministic, model-free, owner-
authored - are validated and applied here, and recorded.

THE LOOP OWNS NO TRUTH. It applies the owners' patches and records what
happened. A caller runs it AFTER the chain, per branch, with a provider or
without one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .progression import (CONTRACT_CONDITION, DeterministicExecution, Progression,
                          execute_stage)



#: The finding class the loop acts on, in the contract's word. Nothing else is
#: a repair: an owner-revisable defect is Unit C's, a deferred obligation is
#: s05/s06's, an unsupported analysis is nobody's to retry, and a required-
#: minimum absence is a fact the loop cannot invent.
REPAIRABLE_S04 = "REPAIRABLE_S04"

#: How a repair loop ends. Every ending is evidence; none is a verdict.
SETTLED = "SETTLED"                      # no repairable finding remains
CYCLE = "REPEATED_FINDINGS"              # the same findings came back
BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"    # the rounds ran out
NO_PROVIDER = "NO_PROVIDER"              # deterministic repairs only were possible
REPAIR_FAILED = "REPAIR_FAILED"          # a repair invocation did not land
NO_EVIDENCE = "NO_EVIDENCE"              # feasibility could not evaluate the branch


@dataclass(frozen=True)
class RepairRound:
    """One round: what was found, what was done about it, in that order."""

    branch: str
    round: int
    #: The repairable findings this round started from, as (domain, code).
    signature: Tuple[Tuple[str, str], ...]
    #: The derivation passes that ran and wrote, by responsibility.
    deterministic: Tuple[str, ...] = ()
    #: The producing passes re-invoked with repair context, by responsibility.
    invoked: Tuple[str, ...] = ()
    problems: Tuple[str, ...] = ()

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "round": self.round,
                "signature": [list(x) for x in self.signature],
                "deterministic": list(self.deterministic),
                "invoked": list(self.invoked), "problems": list(self.problems)}


@dataclass
class RepairOutcome:
    """How one branch's loop ended, and what it left open."""

    branch: str
    status: str
    rounds: List[RepairRound] = field(default_factory=list)
    #: The repairable findings still standing when the loop stopped: open
    #: obligations on the record, and nothing else. Never a reason for
    #: INFEASIBLE, which needs an argument no loop can supply.
    open: List[Dict[str, Any]] = field(default_factory=list)
    feasibility: Optional[str] = None

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "status": self.status,
                "rounds": [r.as_record() for r in self.rounds],
                "open": [dict(o) for o in self.open],
                "feasibility": self.feasibility}


def _repairable_findings(state, progression: Progression, branch: str):
    """(status, rows) - feasibility answered again over current state, and the
    REPAIRABLE_S04 rows of its domain verdicts. The answer is written through
    the owner's own entry point, so the check IS the canonical check."""
    from ..stages import feasibility as feas

    out = feas.evaluate_candidate_feasibility(state, branch)
    if out.patch is not None and not out.problems:
        state.apply(out.patch)
    progression.record_deterministic(DeterministicExecution(
        responsibility_id=feas.RESPONSIBILITY, stage_id=feas.RESPONSIBILITY,
        outcome=str(out.status), patch_applied=out.patch is not None and not out.problems,
        problems=tuple(out.problems)))
    if out.status is None:
        return None, []
    rows = []
    for v in out.verdicts:
        for row in feas.classify(v)[0]:
            if row.get("class") == REPAIRABLE_S04:
                rows.append(dict(row, note=v.summary))
    return out.status, rows


def _signature(rows) -> Tuple[Tuple[str, str], ...]:
    return tuple(sorted({(r["domain"], r["code"]) for r in rows}))


def _deterministic_repairs(state, progression: Progression, branch: str, rows,
                           stages, attempt: int) -> List[str]:
    """Every derivation pass whose findings are present, run and applied.

    DETERMINISTIC FIRST, ALWAYS. A finding a pass can repair by derivation is
    repaired by derivation, and no model is asked about it: asking would be
    resampling an answer the design already determines.
    """
    applied: List[str] = []
    codes = {r["code"] for r in rows}
    for stage in stages:
        if not codes & set(stage.DERIVED_REPAIRS):
            continue
        derive = (stage.derive_arrival if hasattr(stage, "derive_arrival")
                  else stage.derive_occupancy)
        patch = derive(state, branch, attempt)
        problems = state.validate(patch)
        wrote = bool(patch.operations) and not problems
        if wrote:
            state.apply(patch)
            applied.append(stage.responsibility_id())
        progression.record_deterministic(DeterministicExecution(
            responsibility_id=stage.responsibility_id(), stage_id=stage.stage_id,
            outcome="DERIVED" if wrote else ("REFUSED" if problems else "NOTHING_TO_DERIVE"),
            patch_applied=wrote, problems=tuple(problems)))
        if problems:
            progression.fail(CONTRACT_CONDITION, stage.responsibility_id(),
                             "a derivation patch was refused", problems)
    return applied


def s04_repair_rounds(provider, state, progression: Progression, invocation, *,
                      rounds: int = 2, refreshes: int = 1) -> RepairOutcome:
    """Realize -> check -> diagnose -> repair -> re-check, BOUNDED, for one branch.

    THE LOOP OWNS NO TRUTH. Each round asks the feasibility responsibility to
    answer again over current state (the check), reads the REPAIRABLE_S04 rows
    off its verdicts (the diagnosis, in the contract's classes), runs the
    derivation passes that can repair without a model, and then - only for what
    remains, and only with a provider - re-invokes the owning s04 pass with the
    findings as REPAIR CONTEXT. Every write is the owner's, through the ordinary
    boundary, with the round as its reason; the loop applies patches and
    records what happened.

    NO FAVOURABLE RETRY. One invocation per pass per round, taken whatever it
    says; nothing here compares two answers or keeps the better one. The loop
    stops when no repairable finding remains, when the same findings come back
    (a cycle), when the rounds run out, when no provider was offered for what
    remains, or when a repair invocation does not land - and every ending
    leaves what is still open as open obligations on the record. None of them
    is INFEASIBLE, which needs an argument no loop can write.
    """
    from ..stages.s04_envelope_and_motion import (REPAIR_KEY, S04AEnvelopeAndReach,
                                                  S04BPlacementAndMotion,
                                                  branch_realization)
    branch = getattr(invocation, "branch", None)
    stages = {"s04a": S04AEnvelopeAndReach(), "s04b": S04BPlacementAndMotion()}
    outcome = RepairOutcome(branch=branch, status=BUDGET_EXHAUSTED)
    seen: List[Tuple[Tuple[str, str], ...]] = []
    for n in range(1, rounds + 1):
        status, rows = _repairable_findings(state, progression, branch)
        if status is None:
            outcome.status = NO_EVIDENCE
            return outcome
        if not rows:
            outcome.status, outcome.feasibility = SETTLED, status
            return outcome
        signature = _signature(rows)
        if signature in seen:
            outcome.status, outcome.open, outcome.feasibility = CYCLE, rows, status
            progression.fail(CONTRACT_CONDITION, "s04",
                             "repair round %d found the findings of an earlier round; "
                             "this is a cycle and is not looped on" % n,
                             [list(x) for x in signature])
            return outcome
        seen.append(signature)
        record = RepairRound(branch=branch, round=n, signature=signature)
        # 1. DETERMINISTIC REPAIRS, then look again: what a derivation repaired
        # is not asked of a model.
        derived = _deterministic_repairs(state, progression, branch, rows,
                                         stages.values(), attempt=10 + n)
        if derived:
            record = RepairRound(branch=branch, round=n, signature=signature,
                                 deterministic=tuple(derived))
            status, rows = _repairable_findings(state, progression, branch)
            if not rows:
                outcome.rounds.append(record)
                outcome.status, outcome.feasibility = SETTLED, status
                return outcome
        # 2. THE OWNING PASS, with the findings, once per pass per round.
        if provider is None:
            outcome.rounds.append(record)
            outcome.status, outcome.open, outcome.feasibility = NO_PROVIDER, rows, status
            return outcome
        current = branch_realization(state, branch, (
            "ReferenceScale", "Envelope", "FunctionalRegion", "Interface", "ReachResult",
            "EliminationRecord", "AssemblyStep", "Joint", "State", "Transition"))
        invoked: List[str] = []
        problems: List[str] = []
        for pass_id in ("s04a", "s04b"):
            mine = [r for r in rows if r.get("owner") == pass_id]
            if not mine:
                continue
            stage = stages[pass_id]
            repair = {"round": n, "findings": mine, "current": current}
            out = None
            for refresh in range(refreshes + 1):
                out, _ = execute_stage(stage, provider, state, progression,
                                       inputs={"candidate": branch, REPAIR_KEY: repair},
                                       attempt=10 + n, invocation=invocation)
                if out is None or out.patch is None or out.problems:
                    break
                if not out.refinement_only:
                    break
            invoked.append(pass_id)
            if out is None or out.patch is None or out.problems:
                problems.append("%s: the repair invocation did not land" % pass_id)
        outcome.rounds.append(RepairRound(branch=branch, round=n, signature=signature,
                                          deterministic=tuple(derived),
                                          invoked=tuple(invoked),
                                          problems=tuple(problems)))
        if problems:
            status, rows = _repairable_findings(state, progression, branch)
            outcome.status, outcome.open, outcome.feasibility = REPAIR_FAILED, rows, status
            return outcome
    # THE BUDGET RAN OUT. What the last round's revisions left derivable is
    # derived - a derivation is not a round, it asks nobody anything - and what
    # stands is checked once more so the record says what is still open.
    # Nothing is concluded from the count.
    status, rows = _repairable_findings(state, progression, branch)
    if rows and _deterministic_repairs(state, progression, branch, rows,
                                       stages.values(), attempt=10 + rounds + 1):
        status, rows = _repairable_findings(state, progression, branch)
    outcome.open, outcome.feasibility = rows, status
    outcome.status = SETTLED if not rows else BUDGET_EXHAUSTED
    return outcome


