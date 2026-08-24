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

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..stages.base import (CAUSE_FINDINGS, CAUSE_UPSTREAM_REVISION, REPAIR_KEY,
                           authored_families)
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



def s04_families() -> Tuple[str, ...]:
    """What an s04 pass is shown of its own previous answer when asked to
    restate it: the families the two passes may author, from the contract."""
    return authored_families("s04a", "s04b")


@dataclass(frozen=True)
class RepairRound:
    """One round: what was found, what was done about it, in that order."""

    branch: str
    round: int
    #: The repairable findings this round started from, as the TYPED identity
    #: `finding_signature` gives them: (domain, code, owner, basis), where the
    #: basis is a digest over the current revisions of the premises the
    #: finding was found on.
    signature: Tuple[Tuple[str, ...], ...]
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


def classified_findings(state, progression: Progression, branch: str):
    """(status, rows) - feasibility answered again over current state, and
    EVERY classified obligation row of its domain verdicts, each carrying the
    domain's note and the premises the verdict was decided from. The answer
    is written through the owner's own entry point, so the check IS the
    canonical check; a caller reads the class it acts on off the rows."""
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
            rows.append(dict(row, note=v.summary, premises=sorted(v.premises)))
    return out.status, rows


def _repairable_findings(state, progression: Progression, branch: str):
    """(status, rows) - the REPAIRABLE_S04 rows of the canonical check."""
    status, rows = classified_findings(state, progression, branch)
    return status, [r for r in rows if r.get("class") == REPAIRABLE_S04]


def finding_signature(state, rows) -> Tuple[Tuple[str, ...], ...]:
    """The TYPED identity of a set of findings over the basis they rest on.

    (domain, code, owner, basis) per finding, where the basis is a digest over
    the CURRENT REVISION of every premise the finding's verdict was decided
    from (`entity_revision_digest`: a lifecycle question, not an engineering
    one). Two rounds that find the same code over a basis that changed in
    between are two different findings - the earlier repair moved something
    and the problem is now a different one - and only the same code over the
    same basis is the same finding come back. No free text enters: a summary
    reworded is not a finding changed, and a finding changed under an
    unchanged summary is not the same finding.
    """
    out = set()
    for r in rows:
        basis = hashlib.sha256("|".join(
            "%s=%s" % (p, state.entity_revision_digest(p))
            for p in sorted(r.get("premises") or ())).encode()).hexdigest()[:16]
        out.add((r["domain"], r["code"], r.get("owner") or "", basis))
    return tuple(sorted(out))


def _signature(state, rows):
    return finding_signature(state, rows)


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
    from ..stages.s04_envelope_and_motion import (S04AEnvelopeAndReach,
                                                  S04BPlacementAndMotion,
                                                  branch_realization,
                                                  next_realization_generation)
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
        signature = _signature(state, rows)
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
        current = branch_realization(state, branch, s04_families())
        generation = next_realization_generation(state, branch)
        invoked: List[str] = []
        problems: List[str] = []
        for pass_id in ("s04a", "s04b"):
            mine = [r for r in rows if r.get("owner") == pass_id]
            if not mine:
                continue
            stage = stages[pass_id]
            repair = {"round": n, "cause": CAUSE_FINDINGS, "findings": mine,
                      "current": current, "generation": generation}
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


def s04_re_realization(provider, state, progression: Progression, invocation, *,
                       round: int, findings, refreshes: int = 1
                       ) -> Tuple[List[str], List[str]]:
    """Realize the branch AGAIN, from the mechanism as it now stands.

    UNIT C'S CALL INTO S04'S LIFECYCLE. An upstream owner revised a fact the
    standing realization was reasoned from, so the realization is not
    evidence about the mechanism as it stands - whether or not any of its
    records went stale by premises: a still-standing realization is not
    reused merely because its ids exist. Both passes are re-invoked, s04a
    then s04b, each with RE-REALIZATION CONTEXT (the upstream findings, for
    orientation, and its own previous values, to revise rather than
    re-imagine) and the ordinary bounded refinement refresh. Their answers
    are recorded as revisions of what stands: s04a's changed values are
    superseded and unchanged ones write nothing; s04b's realization is
    retired whole and re-created whole under the branch's next generation.
    One invocation per pass; nothing is compared and nothing retried.

    Returns (invoked, problems). A pass that does not land ends the
    re-realization - what stands is then a realization of the OLD mechanism
    with an upstream revision beside it, and the caller reports that rather
    than trusting a check over it.
    """
    from ..stages.s04_envelope_and_motion import (S04AEnvelopeAndReach,
                                                  S04BPlacementAndMotion,
                                                  branch_realization,
                                                  next_realization_generation)
    branch = getattr(invocation, "branch", None)
    invoked: List[str] = []
    problems: List[str] = []
    generation = next_realization_generation(state, branch)
    for attempt, stage in enumerate((S04AEnvelopeAndReach(), S04BPlacementAndMotion()),
                                    start=1):
        context = {"round": round, "cause": CAUSE_UPSTREAM_REVISION,
                   "findings": [dict(f) for f in findings],
                   "current": branch_realization(state, branch, s04_families()),
                   "generation": generation}
        out = None
        for refresh in range(refreshes + 1):
            out, _ = execute_stage(stage, provider, state, progression,
                                   inputs={"candidate": branch, REPAIR_KEY: context},
                                   attempt=20 + 2 * round + attempt, invocation=invocation)
            if out is None or out.patch is None or out.problems:
                break
            if not out.refinement_only:
                break
        invoked.append(stage.responsibility_id())
        if out is None or out.patch is None or out.problems:
            problems.append("%s: the re-realization did not land"
                            % stage.responsibility_id())
            break
    return invoked, problems
