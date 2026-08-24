"""THE OWNER REVISION LOOP: an upstream authoring defect is repaired by its
owner, and everything that rested on the old fact is rebuilt from current
premises. Bounded.

    check -> route each OWNER_REVISION finding to the pass that owns it
          -> the owner revises the fact it authored
          -> rebuild downstream: s03b where s03a revised; s04a then s04b,
             re-realized from the mechanism as it now stands; the bounded
             s04 repair loop over that realization
          -> re-check

A SIBLING OF THE PROGRESSION AND OF THE S04 REPAIR LOOP, and conceptually
apart from the latter: this loop asks S03 to revise OWNER_REVISION findings;
`repair` asks S04 to revise REPAIRABLE_S04 findings. Every pass is invoked
through the progression's one invocation path and its patch accepted by that
path's one rule; the feasibility patches - deterministic, owner-authored -
are applied and recorded by the shared check.

THE LOOP OWNS NO TRUTH. It routes by the typed owner the contract's
classification gives each finding, applies the owners' patches through the
boundary, and records what happened. It does not make a candidate easier to
pass, it does not choose a mechanism, and an owner that cannot resolve a
finding without replacing the architecture leaves it open, escalated - never
INFEASIBLE, which needs an argument no loop can write.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..stages.base import CAUSE_FINDINGS, CAUSE_UPSTREAM_REVISION, REPAIR_KEY, branch_records
from .progression import CONTRACT_CONDITION, Progression, execute_stage
from .repair import (BUDGET_EXHAUSTED, CYCLE, NO_EVIDENCE, NO_PROVIDER, SETTLED,
                     classified_findings, finding_signature, s04_re_realization,
                     s04_repair_rounds)

#: The finding class this loop routes, in the contract's word. Nothing else:
#: a repairable realization finding is s04's (Unit B), a deferred obligation
#: is s05/s06's, an unsupported analysis is nobody's to retry, and a
#: required-minimum absence is a fact no revision may invent.
OWNER_REVISION = "OWNER_REVISION"

#: The owners this loop routes to. An OWNER_REVISION finding whose owner is a
#: later stage is reported as unrouted and left exactly as found.
S03_OWNERS = ("s03a", "s03b")

#: How an owner-revision loop ends, beyond the endings it shares with the
#: repair loop. Every ending is evidence; none is a verdict.
REVISION_FAILED = "REVISION_FAILED"      # a revision or rebuild invocation did not land
ESCALATED = "ESCALATED"                  # the owner could not resolve it within its authority


@dataclass(frozen=True)
class OwnerRevisionRound:
    """One round: what was found, who it went to, what they did, what was
    rebuilt - in that order."""

    branch: str
    round: int
    #: The owner-revisable findings this round started from, as the typed
    #: identity `finding_signature` gives them.
    signature: Tuple[Tuple[str, ...], ...]
    #: (owner, code) for every finding routed this round.
    routed: Tuple[Tuple[str, str], ...] = ()
    #: The owner passes invoked, by responsibility.
    invoked: Tuple[str, ...] = ()
    #: The owner passes whose revision landed with at least one operation.
    revised: Tuple[str, ...] = ()
    #: Escalations, each "owner: statement" - the owner's declared ones and
    #: the architecture guard's refusals alike.
    escalated: Tuple[str, ...] = ()
    #: The passes re-run downstream of a revision, in order.
    rebuilt: Tuple[str, ...] = ()
    #: The s04 repair loop's record over the rebuilt realization, if it ran.
    repair: Optional[Dict[str, Any]] = None
    problems: Tuple[str, ...] = ()

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "round": self.round,
                "signature": [list(x) for x in self.signature],
                "routed": [list(x) for x in self.routed],
                "invoked": list(self.invoked), "revised": list(self.revised),
                "escalated": list(self.escalated), "rebuilt": list(self.rebuilt),
                "repair": dict(self.repair) if self.repair else None,
                "problems": list(self.problems)}


@dataclass
class OwnerRevisionOutcome:
    """How one branch's loop ended, and what it left open."""

    branch: str
    status: str
    rounds: List[OwnerRevisionRound] = field(default_factory=list)
    #: The s03-owned OWNER_REVISION findings still standing when the loop
    #: stopped: open obligations on the record, and nothing else.
    open: List[Dict[str, Any]] = field(default_factory=list)
    #: OWNER_REVISION findings whose owner is not an s03 pass: not this
    #: loop's to route, reported so nobody reads their absence as resolution.
    unrouted: List[Dict[str, Any]] = field(default_factory=list)
    escalated: List[str] = field(default_factory=list)
    #: The candidate-level status of the LAST check, and only when that check
    #: ran over a branch whose downstream was rebuilt after every revision
    #: that landed. None where the loop stopped before that - a check over a
    #: half-rebuilt branch is not one to trust.
    feasibility: Optional[str] = None

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "status": self.status,
                "rounds": [r.as_record() for r in self.rounds],
                "open": [dict(o) for o in self.open],
                "unrouted": [dict(o) for o in self.unrouted],
                "escalated": list(self.escalated),
                "feasibility": self.feasibility}


def _owner_findings(state, progression: Progression, branch: str):
    """(status, routed rows, unrouted rows) - the canonical check, and the
    OWNER_REVISION rows of its verdicts split by whether an s03 pass owns
    them. The class and the owner are the contract's; nothing here reads a
    status, a summary, or a candidate's name."""
    status, rows = classified_findings(state, progression, branch)
    if status is None:
        return None, [], []
    owned = [r for r in rows if r.get("class") == OWNER_REVISION]
    return (status,
            [r for r in owned if r.get("owner") in S03_OWNERS],
            [r for r in owned if r.get("owner") not in S03_OWNERS])


def _context(state, branch: str, owner: str, round: int, findings, upstream, cause: str
             ) -> Dict[str, Any]:
    """The OWNER REVISION CONTEXT one pass is given: the typed findings, the
    records they were found on that the pass does not own, and the pass's
    own standing records for this branch."""
    from ..stages.s03_topology_and_mobility import S03A_FAMILIES, S03B_FAMILIES

    current = branch_records(state, branch, S03A_FAMILIES if owner == "s03a"
                             else S03B_FAMILIES)
    shown = {r["entity_id"] for rows in current.values() for r in rows}
    premises: List[Dict[str, Any]] = []
    for eid in sorted({p for f in findings for p in (f.get("premises") or ())}):
        if eid in shown or not state.has_entity(eid):
            continue
        rec = state.entities[eid]
        if rec.get("_validity") == "STANDING":
            premises.append({k: v for k, v in rec.items() if not k.startswith("_")})
    return {"round": round, "cause": cause,
            "findings": [dict(f) for f in findings],
            "upstream": [dict(f) for f in upstream],
            "current": current, "premises": premises}


def _inputs(state, branch: str, owner: str, context) -> Dict[str, Any]:
    """The declared inputs of each pass, as the chain hands them over: s03a
    receives the candidate record, s03b its id."""
    if owner == "s03a":
        candidate: Dict[str, Any] = {"entity_id": branch}
        if state.has_entity(branch):
            candidate = {k: v for k, v in state.entities[branch].items()
                         if not k.startswith("_")}
        return {"candidate": candidate, REPAIR_KEY: context}
    return {"candidate": branch, REPAIR_KEY: context}


def s03_owner_revision_rounds(provider, state, progression: Progression, invocation, *,
                              rounds: int = 2, repair_rounds: int = 2,
                              refreshes: int = 1) -> OwnerRevisionOutcome:
    """Route -> revise -> rebuild -> re-check, BOUNDED, for one branch.

    Each round asks the feasibility responsibility to answer again over
    current state (the check), reads the OWNER_REVISION rows off its verdicts
    and routes each to the s03 pass the contract names as its owner - s03a
    for topology and ownership, s03b for mobility, assembly, load and release
    - with OWNER REVISION CONTEXT: the typed findings, the records they were
    found on, and the pass's own standing records. ONE INVOCATION PER OWNER
    PER ROUND, s03a before s03b, taken whatever it says: no favourable retry,
    nothing compared, nothing chosen.

    WHAT A REVISION CAUSES. Where any revision landed, the branch downstream
    of it is rebuilt from current premises: s03b is re-authored where s03a
    revised (in the same single invocation that carries s03b's own findings,
    if it has any); s04a and s04b are re-realized from the mechanism as it now
    stands - never reused merely because their ids still exist - and the
    bounded s04 repair loop runs over that realization. Only then is the
    branch checked again. A rebuild step that does not land ends the loop
    with no trusted feasibility.

    WHAT A REVISION MAY NOT DO. The owner may revise only facts it owns, and
    only where that keeps the candidate's architecture and the mechanism
    principle: the s03a pass refuses a revision that adds, removes or retypes
    a body, group or joint, and either pass may declare a finding ESCALATED
    rather than resolve it. Escalation, a cycle, an exhausted budget, a
    refused revision and an absent provider each end the loop with the
    obligation on the record - and none of them is INFEASIBLE.
    """
    from ..stages.s03_topology_and_mobility import (ARCHITECTURE_ESCALATION,
                                                    ESCALATED as DECLARED,
                                                    S03BMobilityAndAssembly,
                                                    S03TopologyAndMobility)
    branch = getattr(invocation, "branch", None)
    stages = {"s03a": S03TopologyAndMobility(), "s03b": S03BMobilityAndAssembly()}
    outcome = OwnerRevisionOutcome(branch=branch, status=BUDGET_EXHAUSTED)
    seen: List[Tuple[Tuple[str, ...], ...]] = []

    def invoke(owner: str, n: int, mine, upstream, cause: str):
        """One invocation of one owner, through the progression's one path.
        Returns (landed_with_operations, escalations, problem)."""
        context = _context(state, branch, owner, n, mine, upstream, cause)
        out, _ = execute_stage(stages[owner], provider, state, progression,
                               inputs=_inputs(state, branch, owner, context),
                               attempt=20 + 2 * n + (owner == "s03b"),
                               invocation=invocation)
        if out is None or out.patch is None or out.problems:
            refused = [str(p) for p in (out.problems if out is not None else ())
                       if str(p).startswith(ARCHITECTURE_ESCALATION)]
            if refused:
                return False, ["%s: %s" % (owner, p) for p in refused], None
            return False, [], "%s: the revision invocation did not land" % owner
        declared = ["%s: %s" % (owner, d) for d in (out.declared_incompleteness or ())
                    if str(d).startswith(DECLARED)]
        return bool(out.patch.operations), declared, None

    for n in range(1, rounds + 1):
        status, rows, unrouted = _owner_findings(state, progression, branch)
        outcome.unrouted = unrouted
        if status is None:
            outcome.status = NO_EVIDENCE
            return outcome
        if not rows:
            outcome.status, outcome.feasibility = SETTLED, status
            return outcome
        signature = finding_signature(state, rows)
        if signature in seen:
            outcome.status, outcome.open, outcome.feasibility = CYCLE, rows, status
            progression.fail(CONTRACT_CONDITION, "s03",
                             "owner revision round %d found the findings of an earlier "
                             "round over the same basis; this is a cycle and is not "
                             "looped on" % n, [list(x) for x in signature])
            return outcome
        seen.append(signature)
        if provider is None:
            outcome.status, outcome.open, outcome.feasibility = NO_PROVIDER, rows, status
            return outcome

        routed = tuple(sorted((r["owner"], r["code"]) for r in rows))
        invoked: List[str] = []
        revised: List[str] = []
        escalated: List[str] = []
        rebuilt: List[str] = []
        problems: List[str] = []
        s03a_rows = [r for r in rows if r.get("owner") == "s03a"]
        s03b_rows = [r for r in rows if r.get("owner") == "s03b"]

        # 1. THE TOPOLOGY OWNER, with its findings.
        upstream: List[Dict[str, Any]] = []
        if s03a_rows:
            invoked.append("s03a")
            landed, esc, problem = invoke("s03a", n, s03a_rows, [], CAUSE_FINDINGS)
            escalated += esc
            if problem:
                problems.append(problem)
            elif landed:
                revised.append("s03a")
                upstream = s03a_rows
        # 2. THE MOBILITY OWNER: its own findings, and what changed above it,
        # in ONE invocation.
        if (s03b_rows or upstream) and not problems:
            invoked.append("s03b")
            if upstream:
                rebuilt.append("s03b")
            landed, esc, problem = invoke(
                "s03b", n, s03b_rows, upstream,
                CAUSE_FINDINGS if s03b_rows else CAUSE_UPSTREAM_REVISION)
            escalated += esc
            if problem:
                problems.append(problem)
            elif landed:
                revised.append("s03b")
        outcome.escalated += escalated

        # 3. THE REALIZATION, rebuilt from the mechanism as it now stands, and
        # repaired where it is repairable.
        repair = None
        if revised and not problems:
            answered = [r for r in rows if r.get("owner") in revised]
            passes, rebuild_problems = s04_re_realization(
                provider, state, progression, invocation, round=n,
                findings=answered, refreshes=refreshes)
            rebuilt += passes
            problems += rebuild_problems
            if not problems:
                repair = s04_repair_rounds(provider, state, progression, invocation,
                                           rounds=repair_rounds).as_record()
        outcome.rounds.append(OwnerRevisionRound(
            branch=branch, round=n, signature=signature, routed=routed,
            invoked=tuple(invoked), revised=tuple(revised), escalated=tuple(escalated),
            rebuilt=tuple(rebuilt), repair=repair, problems=tuple(problems)))
        if problems:
            # A REVISION OR A REBUILD DID NOT LAND. What stands is recorded;
            # no check over a half-rebuilt branch is offered as feasibility.
            outcome.status, outcome.open = REVISION_FAILED, rows
            return outcome
        if not revised and escalated:
            # THE OWNER SAID IT CANNOT, within its authority. The finding stays
            # open, above this stage, and nothing is concluded from that.
            outcome.status, outcome.open, outcome.feasibility = ESCALATED, rows, status
            return outcome
        # Nothing landed and nothing was escalated: the owner restated what
        # stands. The next check finds the same findings over the same basis,
        # which the next round reports as a cycle.

    # THE BUDGET RAN OUT. The branch is checked once more so the record says
    # what is still open. Nothing is concluded from the count.
    status, rows, unrouted = _owner_findings(state, progression, branch)
    outcome.open, outcome.unrouted, outcome.feasibility = rows, unrouted, status
    outcome.status = SETTLED if not rows else BUDGET_EXHAUSTED
    return outcome
