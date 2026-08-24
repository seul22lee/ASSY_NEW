"""THE HUMAN CHECKPOINT. One review, three controls, and no authority at all.

S7-E. This module draws what `selection_decision` assembled and hands back what a
person chose. It is written against a SURFACE - anything with the handful of
methods below - so the page logic is exercised by tests without a browser, and
the Streamlit entry point is a thin adapter that passes `streamlit` in as the
surface.

WHAT IT MAY NOT DO, AND WHY EACH ONE MATTERS

    IT MAY NOT WRITE A COMMITMENT. `SelectionDecision` appears nowhere in this
    file. A screen that could author one would be a client deciding, and every
    check the deterministic writer performs would be optional.

    IT MAY NOT READ STATE WHILE RENDERING. `render_review` is handed a snapshot
    and nothing else. A screen that re-queried the design between drawing the
    comparison and drawing the advisory would be showing a person two moments and
    calling it one review.

    IT MAY NOT PRESELECT A CANDIDATE. The candidate control starts on a
    placeholder, so a submission always carries an explicit human choice. A
    dropdown defaulted to the frontier is an answer somebody could submit without
    reading the question - and the frontier is not a winner.

    IT MAY NOT REFRESH AND RESUBMIT. When the design has moved under a review the
    person is told to look again. Rebuilding the snapshot and submitting the same
    action against it would erase the checkpoint entirely: the approval would be
    of material nobody read.

    IT MAY NOT TREAT AN ADVISORY AS A GATE. Absent advisory material is shown as
    absent and every control stays live. A provider outage that stopped a person
    deciding would have given a model a veto.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..stages import selection_decision as dec

#: What the screen says when something is not there. Absence is stated, never
#: filled in with a default nobody chose.
ADVISORY_ABSENT = "No advisory available."
CONCERNS_ABSENT = "No concerns were raised."
NO_PREFERENCE = "No ranked selection preference was stated."
NOT_AVAILABLE = "NOT_AVAILABLE"

#: The advisory is labelled every time it is shown. A recommendation printed
#: without this heading reads like an instruction.
ADVISORY_LABEL = "Advisory / reviewer opinion - not a decision"
CONCERN_LABEL = ("Concerns raised for a human to weigh. A concern decides "
                 "nothing, and importance is not authority.")

#: Every obligation row is followed by this, so a list of what a candidate
#: still owes cannot read as a list of reasons not to choose it.
OBLIGATION_LABEL = ("An obligation is work with an owner, recorded with the "
                    "feasibility answer. It decides nothing here.")

#: The candidate control starts here, and this is not a candidate.
CHOOSE_PLACEHOLDER = "- choose a candidate -"

REVIEW_SHOWN = "REVIEW_SHOWN"
NOTHING_TO_REVIEW = "NOTHING_TO_REVIEW"
NO_CHOICE_MADE = "NO_CHOICE_MADE"

STALE_MESSAGE = ("The design changed after this review was displayed. Refresh "
                 "the decision view and review the current evidence.")
NOT_READY_MESSAGE = ("There is nothing to decide yet: %s. A decision screen is "
                     "shown only when the design can say what the choice is "
                     "between.")

#: status -> what the person is told. Every refusal names what to do next, and
#: none of them offers to do it for them.
MESSAGES = {
    dec.SELECTION_COMMITTED: "Committed %s.",
    dec.SELECTION_REVISED: ("Revised the commitment to %s. The previous decision "
                            "is kept as history and everything built on it will "
                            "be re-established."),
    dec.SELECTION_UNCHANGED: "%s was already committed by this submission.",
    dec.HUMAN_KEPT_UNRESOLVED: ("Recorded: the decision is kept open. Nothing "
                                "was committed."),
    dec.MORE_EVIDENCE_REQUESTED: ("Recorded: more evidence was requested. "
                                  "Nothing was committed."),
    dec.STALE_SUBMISSION: STALE_MESSAGE,
    dec.SUBMISSION_CONTEXT_MISMATCH: STALE_MESSAGE,
    dec.SELECTION_NO_LONGER_ELIGIBLE: (
        "That candidate is no longer eligible on current evidence. Nothing was "
        "committed; review the current evidence and decide again."),
    dec.SELECTION_CONTEXT_INCONSISTENT: (
        "The eligible population has moved since this review was displayed. "
        "Nothing was committed; refresh the decision view."),
    dec.DECISION_ALREADY_STANDING: (
        "A selection already stands for this design. Changing a commitment is "
        "not something this screen does."),
    dec.NO_STANDING_COMMITMENT: (
        "The commitment this review showed no longer stands, so there is "
        "nothing to revise. Nothing was written; refresh the decision view."),
    dec.INVALID_HUMAN_INPUT: "That submission was not accepted: %s",
}


# =====================================================================
# the view model - derived from the snapshot and from nothing else
# =====================================================================
def _metric_cell(metric: Any) -> str:
    """One metric value as it is shown. NOT_AVAILABLE is shown as itself.

    Never blank, never a dash, and never a zero standing in for a measurement
    nobody made: unavailable is neither good nor bad, and a reader has to be able
    to tell it from a number.
    """
    if not isinstance(metric, dict):
        return NOT_AVAILABLE
    if metric.get("availability") != "AVAILABLE":
        return "%s (%s)" % (NOT_AVAILABLE, metric.get("reason_code") or "no reason")
    unit = metric.get("unit")
    return "%s %s" % (metric.get("value"), unit) if unit else str(metric.get("value"))


def comparison_rows(snapshot: dec.HumanReviewSnapshot) -> List[Dict[str, Any]]:
    """One row per candidate the human may choose between."""
    comparison = snapshot.comparison
    metrics = comparison.get("metrics") or {}
    frontier = list(comparison.get("frontier") or [])
    why = {r["candidate"]: r["why"] for r in snapshot.eligibility}
    rows = []
    for candidate in list(comparison.get("candidates") or []):
        rows.append({
            "candidate": candidate,
            "eligible_because": why.get(candidate, ""),
            # NOT "winner", NOT "best", NOT "selected". The frontier is what the
            # comparison could not tell apart, and naming it a winner on a screen
            # would make the deterministic step look like the decision.
            "in_frontier": candidate in frontier,
            "metrics": {criterion: _metric_cell((per or {}).get(candidate))
                        for criterion, per in sorted(metrics.items())}})
    return rows


def profile_rows(snapshot: dec.HumanReviewSnapshot) -> List[Dict[str, str]]:
    """The stated preferences, exactly. An empty profile stays empty."""
    criteria = snapshot.profile.get("criteria") or {}
    return [{"criterion": name, "objective": spec.get("objective"),
             "priority": spec.get("priority")}
            for name, spec in sorted(criteria.items()) if isinstance(spec, dict)]


def candidate_options(snapshot: dec.HumanReviewSnapshot) -> List[str]:
    """The placeholder first, then the candidates - in the order the comparison
    holds them, which is not a ranking and is not reordered here."""
    return [CHOOSE_PLACEHOLDER] + list(snapshot.comparison.get("candidates") or [])


def review_lines(snapshot: dec.HumanReviewSnapshot) -> List[str]:
    """Everything the screen states, as text, in order. Derived from the
    snapshot alone - which is what makes "the thing shown is the thing hashed"
    checkable rather than asserted."""
    lines = ["## The choice",
             "Comparison %s, outcome %s."
             % (snapshot.comparison.get("entity_id"),
                snapshot.comparison.get("outcome"))]
    if snapshot.standing_decision is not None:
        # A person shown a design that has already committed must see the
        # commitment: a SELECT on this screen asks to REVISE it.
        lines.append("**The design is currently committed to %s** (decision %s). "
                     "Selecting a different candidate revises that commitment; "
                     "the previous decision is kept as history."
                     % (snapshot.standing_decision.get("selected_candidate"),
                        snapshot.standing_decision.get("entity_id")))
    if snapshot.comparison.get("stopping_priority"):
        lines.append("The comparison stopped at priority %s."
                     % snapshot.comparison["stopping_priority"])
    for row in comparison_rows(snapshot):
        metrics = ", ".join("%s = %s" % (c, v)
                            for c, v in sorted(row["metrics"].items()))
        lines.append("- %s%s: %s%s"
                     % (row["candidate"],
                        " (in the deterministic frontier)" if row["in_frontier"] else "",
                        metrics or "no registered metric was requested",
                        " - eligible because %s" % row["eligible_because"]
                        if row["eligible_because"] else ""))
    unavailable = list(snapshot.comparison.get("unavailable_criteria") or [])
    if unavailable:
        lines.append("Not measurable on current evidence: %s. Unavailable is "
                     "neither good nor bad." % ", ".join(unavailable))

    lines.append("## The stated preferences (%s)" % snapshot.profile.get("entity_id"))
    rows = profile_rows(snapshot)
    lines.extend(["- %s: %s, priority %s" % (r["criterion"], r["objective"],
                                             r["priority"]) for r in rows]
                 or [NO_PREFERENCE])

    lines.append("## Why these candidates are eligible")
    for row in snapshot.eligibility:
        lines.append("- %s: %s (%s)" % (row["candidate"], row["verdict"], row["why"]))
    lines.append("Established from %d feasibility assessment(s), %d hard-requirement "
                 "result(s) and %d stated requirement(s)."
                 % (len(snapshot.feasibility_assessments),
                    len(snapshot.hard_requirement_results),
                    len(snapshot.design_constraints)))

    # WHAT EACH CANDIDATE CARRIES, as the feasibility answer recorded it. Read
    # off the records the eligibility basis names and rendered generically -
    # a row is shown for what it says, and nothing here branches on it,
    # classifies it, or lets it decide anything. A person choosing a candidate
    # with open obligations chooses with them on the screen.
    shown = False
    for record in snapshot.feasibility_assessments:
        rows = ([("not established", r)
                 for r in (record.get("blocking_findings") or [])]
                + [("open", r) for r in (record.get("open_obligations") or [])])
        if not rows:
            continue
        shown = True
        lines.append("## What %s still carries (%s)"
                     % (record.get("candidate"), record.get("entity_id")))
        for kind, r in rows:
            if not isinstance(r, dict):
                continue
            lines.append("- %s: %s %s [%s, owner %s]%s"
                         % (kind, r.get("domain"), r.get("code"), r.get("class"),
                            r.get("owner"),
                            " - leaves %s unestablished" % r["negates"]
                            if r.get("negates") else ""))
    if shown:
        lines.append(OBLIGATION_LABEL)

    lines.append("## %s" % ADVISORY_LABEL)
    if not snapshot.advisories:
        lines.append(ADVISORY_ABSENT)
    for advisory in snapshot.advisories:
        lines.append("- recommendation: %s%s"
                     % (advisory.get("recommendation"),
                        " (%s)" % advisory["recommended_candidate"]
                        if advisory.get("recommended_candidate") else ""))
        lines.append("  alignment with the deterministic comparison: %s"
                     % advisory.get("comparison_alignment"))
        lines.append("  reasoning: %s" % advisory.get("reasoning"))
        if advisory.get("sensitivity"):
            lines.append("  sensitivity: %s" % advisory["sensitivity"])

    lines.append("## %s" % CONCERN_LABEL)
    if not snapshot.concerns:
        lines.append(CONCERNS_ABSENT)
    for concern in snapshot.concerns:
        lines.append("- %s [%s, %s]: %s"
                     % (concern.get("candidate"), concern.get("importance"),
                        concern.get("evidence_status"), concern.get("issue")))
        if concern.get("evidence_note"):
            lines.append("  %s" % concern["evidence_note"])
    return lines


# =====================================================================
# drawing, and what comes back
# =====================================================================
class CheckpointOutcome:
    """What the screen did. `message` is what the person is told."""

    __slots__ = ("status", "message", "snapshot", "input_id", "decision_id",
                 "problems")

    def __init__(self, status, message="", snapshot=None, input_id=None,
                 decision_id=None, problems=None):
        self.status = status
        self.message = message
        self.snapshot = snapshot
        self.input_id = input_id
        self.decision_id = decision_id
        self.problems = list(problems or [])

    @property
    def committed(self) -> bool:
        return self.status in (dec.SELECTION_COMMITTED, dec.SELECTION_REVISED,
                               dec.SELECTION_UNCHANGED)


def render_review(surface, snapshot: dec.HumanReviewSnapshot) -> None:
    """Draw the review. TAKES NO STATE, so it cannot show anything else."""
    for line in review_lines(snapshot):
        surface.markdown(line)


def render_controls(surface, snapshot: dec.HumanReviewSnapshot) -> Dict[str, Any]:
    """The three actions, the candidate, the rationale, and one submit."""
    action = surface.radio("What do you want to record?", list(dec.ACTIONS), index=0)
    candidate = surface.selectbox("Candidate", candidate_options(snapshot), index=0)
    rationale = surface.text_area(
        "Why? (recorded with the decision, including when you choose against the "
        "comparison or the advisory)")
    return {"action": action, "candidate": candidate, "rationale": rationale,
            "submitted": bool(surface.button("Submit"))}


def submit(state, snapshot: dec.HumanReviewSnapshot, action: Any,
           selected_candidate: Any = None, rationale: Any = None,
           run_id: Optional[str] = None) -> CheckpointOutcome:
    """Record the submission, then ask the writer to commit it. NOTHING ELSE.

    Both patches come from the backend and are applied unchanged. There is no
    branch in here that constructs an operation, and none that retries: a refusal
    is shown to the person who submitted, and what happens next is theirs.
    """
    if action == dec.SELECT and selected_candidate == CHOOSE_PLACEHOLDER:
        # A placeholder is not a candidate. Reading it as one is how a default
        # becomes a decision nobody made.
        return CheckpointOutcome(NO_CHOICE_MADE, "Choose a candidate first.",
                                 snapshot)
    if action != dec.SELECT and selected_candidate == CHOOSE_PLACEHOLDER:
        selected_candidate = None

    recorded = dec.materialize_human_decision_input(
        state, snapshot, action, selected_candidate, rationale, run_id)
    if not recorded.ok:
        return CheckpointOutcome(
            dec.INVALID_HUMAN_INPUT,
            MESSAGES[dec.INVALID_HUMAN_INPUT] % "; ".join(recorded.problems),
            snapshot, problems=recorded.problems)
    if recorded.patch is not None:
        state.apply(recorded.patch)

    # ONE SUBMISSION, ONE WRITER - WHICH writer follows from what the screen
    # showed: a review displaying a standing commitment submits a SELECT to the
    # revision act, anything else to the commit act. Both are backend writers;
    # this file still constructs no operation and retries nothing.
    if snapshot.standing_decision is not None and action == dec.SELECT:
        out = dec.revise_human_selection(state, recorded.input_id, run_id)
    else:
        out = dec.commit_human_selection(state, recorded.input_id, run_id)
    if out.patch is not None:
        state.apply(out.patch)
    template = MESSAGES.get(out.status, out.status)
    message = template % selected_candidate if "%s" in template else template
    return CheckpointOutcome(out.status, message, out.snapshot,
                             recorded.input_id, out.decision_id, out.problems)


def checkpoint(surface, state, run_id: Optional[str] = None) -> CheckpointOutcome:
    """One pass of the screen: build, render, and submit if a human pressed it.

    THE SNAPSHOT IS BUILT ONCE and is what the submission is made against. A
    second build between rendering and submitting would be a different review.
    """
    review = dec.build_human_review_snapshot(state)
    if not review.ready:
        surface.warning(NOT_READY_MESSAGE % review.status)
        for problem in review.problems:
            surface.markdown("- %s" % problem)
        return CheckpointOutcome(NOTHING_TO_REVIEW, NOT_READY_MESSAGE % review.status)

    snapshot = review.snapshot
    render_review(surface, snapshot)
    controls = render_controls(surface, snapshot)
    if not controls["submitted"]:
        return CheckpointOutcome(REVIEW_SHOWN, "", snapshot)

    out = submit(state, snapshot, controls["action"], controls["candidate"],
                 controls["rationale"], run_id)
    (surface.success if out.committed else surface.warning)(out.message)
    return out
