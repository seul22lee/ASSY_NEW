"""S7-F. ASK EVERY S-7 RESPONSIBILITY THE SAME QUESTION AGAIN, IN ORDER.

    is this candidate still eligible, over the evidence the design has NOW?
    do these preferences still say what the user says?
    do the alternatives still compare the way that record says?
    would the reviewer still be shown the design it reviewed?
    is there anything a person should be asked about?

IT DECIDES NOTHING. Every answer above is computed by the responsibility that
owns it - `feasibility` for eligibility, `selection` for the profile and the
comparison, the advisory pass for the review - through the same entry points a
first run uses. This module chooses the ORDER, applies what they produce, and
reports what moved. It owns no family, evaluates no domain, computes no metric,
and cannot select a candidate: the last of those is the point of the whole step.

WHY A COORDINATOR EXISTS AT ALL

Currentness propagates along named premises, and one thing can never be named:
an ABSENCE. `NOT_ESTABLISHED because no load path exists` depends on there being
no load path, and there is no id to put in `premise_refs` for a record that does
not exist. When one is finally authored, no edge leads back to the answer that
was waiting for it. The only honest way to notice is to ask the evaluator again -
which is what this does, and why it must use the evaluator rather than a second
set of rules about what "probably" affects feasibility.

WHAT IT WILL NOT DO

    IT WILL NOT CALL A MODEL BY ITSELF. A refresh happens only when a caller
    hands over a provider, because asking for an opinion is a decision somebody
    makes, not a consequence of the design having changed. Without one, an
    overtaken review is withdrawn and the design has no current advisory - an
    ordinary state, and one a human may still decide in.

    IT WILL NOT COMMIT ANYTHING. A stale commitment reopens to a PERSON. The old
    submission stays exactly where it is, is never replayed, and the frontier,
    the recommendation and the sole eligible candidate are still not decisions.

    IT WILL NOT WRITE WHEN NOTHING MOVED. Running it twice over an unchanged
    design writes nothing at all the second time, or every reconcile would be a
    revision and the history would fill with copies of one answer.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..stages import feasibility as feas
from ..stages import selection as sel
from ..stages import selection_advisory as adv
from ..stages import selection_decision as dec


class _Source:
    """A preference SOURCE, which is not the same thing as a preference.

    Three states, and collapsing any two of them loses a real distinction the
    design has to keep: nobody said anything about preferences on this call;
    the source that used to state them no longer does; and the source states
    exactly these, including the explicitly empty `{}` that says nothing is
    ranked.
    """

    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:                                   # pragma: no cover
        return self.name


#: Not passed: this reconcile is not about preferences and touches no profile.
UNSPECIFIED = _Source("UNSPECIFIED")
#: The source is gone. The old snapshot is not still what the user asks for.
ABSENT = _Source("ABSENT")

#: What the design is currently waiting for. Machine-readable, and deliberately
#: three things rather than one failure: a design with no comparison to review is
#: not a broken run, and a provider that failed is a different fact again.
CURRENT_COMMITMENT = "CURRENT_COMMITMENT"
AWAITING_HUMAN_DECISION = "AWAITING_HUMAN_DECISION"
REVIEW_NOT_READY = "REVIEW_NOT_READY"


class S7ReconcileOutcome:
    """What was already current, what was withdrawn, what is current now.

    EPHEMERAL. No family records that a reconciliation happened: the entities and
    their validity histories ARE the record, and a summary entity would be a
    second account of the same fact that something would eventually premise on.
    """

    __slots__ = ("human_state", "feasibility", "profile", "comparison",
                 "advisory", "retired", "written", "problems", "review")

    def __init__(self):
        self.human_state = REVIEW_NOT_READY
        #: candidate -> the status its evaluator reported this time.
        self.feasibility: Dict[str, str] = {}
        self.profile: Optional[str] = None
        self.comparison: Optional[str] = None
        self.advisory: Optional[str] = None
        #: ids that stopped being current, and ids that were written.
        self.retired: List[str] = []
        self.written: List[str] = []
        self.problems: List[str] = []
        self.review = None

    @property
    def changed(self) -> bool:
        return bool(self.retired or self.written)

    def as_dict(self) -> Dict[str, Any]:
        return {"human_state": self.human_state,
                "feasibility": dict(sorted(self.feasibility.items())),
                "profile": self.profile, "comparison": self.comparison,
                "advisory": self.advisory, "retired": sorted(self.retired),
                "written": sorted(self.written), "problems": list(self.problems),
                "changed": self.changed}


def _apply(state, patch, outcome: S7ReconcileOutcome) -> None:
    """Apply one owner's patch and record what it did. Never edits the patch."""
    if patch is None:
        return
    state.apply(patch)
    for op in patch.operations:
        if op.kind == "CREATE":
            outcome.written.append(op.entity_id)
        else:
            outcome.retired.append(op.entity_id)


def reconcile_s7(state, selection_preferences: Any = UNSPECIFIED,
                 advisory_provider: Any = None,
                 run_id: Optional[str] = None) -> S7ReconcileOutcome:
    """Re-establish what S-7 currently says, in dependency order.

    The order is the pipeline's own and is not negotiable: eligibility is decided
    before anything may be compared, the preferences are the profile a comparison
    is made under, the review is of a comparison, and the human checkpoint is of
    all of it. Running them in any other order would compare a population that
    was about to change.
    """
    outcome = S7ReconcileOutcome()

    # 1 - ELIGIBILITY, per retained candidate, through the owner's own evaluator.
    # A candidate the design cannot yet evaluate is reported as such and is NOT
    # skipped: an unevaluable alternative is what makes a population
    # unestablished, and quietly leaving it out would compare the subset that
    # happened to be knowable.
    for candidate in sorted(c["entity_id"] for c in state.standing("Candidate")):
        out = feas.evaluate_candidate_feasibility(state, candidate, run_id)
        outcome.feasibility[candidate] = out.status or "NOT_EVALUABLE"
        if out.problems:
            outcome.problems += ["%s: %s" % (candidate, p) for p in out.problems]
        _apply(state, out.patch, outcome)

    # 2 - THE PREFERENCE SOURCE, only when this call was told about it.
    if selection_preferences is ABSENT:
        out = sel.retire_selection_profile(state, run_id)
        outcome.profile = out.status
        outcome.problems += out.problems
        _apply(state, out.patch, outcome)
    elif selection_preferences is not UNSPECIFIED:
        out = sel.materialize_selection_profile(state, selection_preferences,
                                                run_id)
        outcome.profile = out.status
        outcome.problems += out.problems
        _apply(state, out.patch, outcome)

    # 3 - THE COMPARISON. When the evaluator says none may exist, the one that
    # stands is withdrawn: yesterday's comparison is not today's answer merely
    # because today produced no replacement.
    compared = sel.evaluate_candidate_comparison(state, run_id)
    outcome.comparison = compared.status
    if compared.status in sel.NO_COMPARISON_POSSIBLE:
        retired = sel.retire_candidate_comparison(
            state, "the current evidence supports no comparison (%s)"
                   % compared.status, run_id)
        outcome.problems += retired.problems
        _apply(state, retired.patch, outcome)
    else:
        outcome.problems += compared.problems
        _apply(state, compared.patch, outcome)

    # 4 - THE REVIEW, retired when the reviewer would now be shown something
    # else. Never replaced: an advisory is assurance, and asking for a new
    # opinion is a person's decision rather than a consequence of a change.
    status, patch, retired = adv.retire_overtaken_advisories(state, run_id)
    outcome.advisory = status
    _apply(state, patch, outcome)
    if retired and patch is None:
        outcome.problems += retired

    # 5 - AND ONLY IF A CALLER EXPLICITLY HANDED OVER A PROVIDER, through the
    # ordinary Stage boundary - the same view, the same refusal to call it on an
    # unready context, the same strict response schema.
    if advisory_provider is not None:
        review = adv.SelectionEngineeringReview().invoke(
            advisory_provider, state, run_id or state.run_id)
        outcome.advisory = review.execution_status.value
        if review.patch is not None and not review.problems:
            _apply(state, review.patch, outcome)
        else:
            outcome.problems += list(review.problems or [])

    # 6 - WHAT THE DESIGN IS WAITING FOR. Reported, never acted on.
    outcome.review = dec.build_human_review_snapshot(state)
    if state.standing("SelectionDecision"):
        outcome.human_state = CURRENT_COMMITMENT
    elif outcome.review.ready:
        outcome.human_state = AWAITING_HUMAN_DECISION
    else:
        outcome.human_state = REVIEW_NOT_READY
    return outcome


def current_commitment(state):
    """The standing SelectionDecision, or None. NEVER a stale one.

    A decision that lost its premises is history: it says what somebody chose and
    on what, and it stops saying that the design is committed. Reading it as
    current is the one way a lifecycle can quietly un-reopen a choice.
    """
    standing = state.standing("SelectionDecision")
    return standing[0] if len(standing) == 1 else None
