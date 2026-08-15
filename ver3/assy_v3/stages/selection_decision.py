"""WHAT DID THE HUMAN DECIDE, AND WAS IT STILL TRUE WHEN THEY SAID IT?

S7-E. The first place a SelectionDecision may exist, and the last place anything
in this pipeline gets to choose - because it does not choose. Three separate acts
live here and the separation is the whole design:

    BUILD THE REVIEW      one immutable snapshot of exactly what a person is
                          shown. No provider, no writes.
    RECORD THE SUBMISSION a HumanDecisionInput saying what they asked for and
                          what was on the screen when they asked.
    COMMIT, OR REFUSE     a deterministic writer that rebuilds the review from
                          CURRENT state and writes a commitment only if the two
                          are the same review.

WHY THE SNAPSHOT IS ONE OBJECT

A screen that queried state for the comparison, then for the profile, then for
the advisory, would be showing a person four answers taken at four moments and
calling it one review. The snapshot is assembled once, rendered from, and hashed
- so `premise_digest` is a digest of THE THING SHOWN rather than of whatever the
design happened to hold when the submit button was pressed.

WHY THE DIGEST IS NOT `state_hash()`

An entity that was neither shown nor part of the decision basis changing
somewhere else in the design must not invalidate a human approval. A whole-state
hash would make every unrelated write a reason to ask a person to look again,
which trains people to click through the thing that exists to stop them. The
digest covers the review material and the eligibility basis, and nothing else.

FOUR THINGS THIS WRITER WILL NOT DO

    IT WILL NOT CHOOSE. Not the frontier, not the advisory's recommendation, not
    the sole eligible candidate. A comparison of one candidate is the comparison
    running out of ways to tell alternatives apart; it is not a decision, and a
    design with one eligible candidate still waits for a person to say yes.

    IT WILL NOT TRUST THE SUBMISSION. `premise_digest` arrives from the client
    that is asking for a commitment. It is compared against a digest recomputed
    here, and the comparison's own candidate list is cross-checked rather than
    believed - eligibility is re-established from the same canonical semantics
    S7-C used, over current state.

    IT WILL NOT PREMISE A MODEL'S WORDING. Advisory material the person
    considered is RECORDED on the decision and is never in its premise set, so
    rewording a review afterwards cannot disturb a commitment the wording was
    never the ground of. Before submission the same material is inside the digest,
    because a person looking at an old opinion is looking at an old screen. The
    two are different questions and they have different answers.

    IT WILL NOT REOPEN. A standing commitment is left exactly as it is; changing
    one is lifecycle work this step does not do.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..state.patch import Op, StagePatch
from ..view.consumer_view import ViewStatus
from . import selection as sel

RESPONSIBILITY = "selection"
#: Two consumer passes of one owner. Everything below writes as `selection`.
REVIEW_PASS = "selection_human_review"
DECISION_PASS = "selection_decision"

#: What a person may submit. Exactly these three, matched exactly.
SELECT = "SELECT"
KEEP_UNRESOLVED = "KEEP_UNRESOLVED"
REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
ACTIONS = (SELECT, KEEP_UNRESOLVED, REQUEST_MORE_EVIDENCE)

#: Building the review.
REVIEW_READY = "REVIEW_READY"
NO_CURRENT_COMPARISON = "NO_CURRENT_COMPARISON"
REVIEW_CONTEXT_AMBIGUOUS = "REVIEW_CONTEXT_AMBIGUOUS"
REVIEW_CONTEXT_NOT_READY = "REVIEW_CONTEXT_NOT_READY"
REVIEW_PROFILE_NOT_CURRENT = "REVIEW_PROFILE_NOT_CURRENT"

#: Recording the submission.
HUMAN_INPUT_RECORDED = "HUMAN_INPUT_RECORDED"
HUMAN_INPUT_UNCHANGED = "HUMAN_INPUT_UNCHANGED"
INVALID_HUMAN_INPUT = "INVALID_HUMAN_INPUT"

#: Committing, or refusing to.
SELECTION_COMMITTED = "SELECTION_COMMITTED"
SELECTION_UNCHANGED = "SELECTION_UNCHANGED"
HUMAN_KEPT_UNRESOLVED = "HUMAN_KEPT_UNRESOLVED"
MORE_EVIDENCE_REQUESTED = "MORE_EVIDENCE_REQUESTED"
STALE_SUBMISSION = "STALE_SUBMISSION"
SUBMISSION_CONTEXT_MISMATCH = "SUBMISSION_CONTEXT_MISMATCH"
SELECTION_NO_LONGER_ELIGIBLE = "SELECTION_NO_LONGER_ELIGIBLE"
SELECTION_CONTEXT_INCONSISTENT = "SELECTION_CONTEXT_INCONSISTENT"
DECISION_ALREADY_STANDING = "DECISION_ALREADY_STANDING"

#: Outcomes that wrote nothing and are not failures: a person declining to commit
#: has answered the question they were asked.
ACCEPTED_WITHOUT_COMMITMENT = (HUMAN_KEPT_UNRESOLVED, MORE_EVIDENCE_REQUESTED)


# =====================================================================
# the review snapshot
# =====================================================================
def _shown(record: Dict[str, Any]) -> Dict[str, Any]:
    """One record as the screen sees it: the engineering values, and the family.

    The bookkeeping fields are deliberately out. `_premises` merging or a
    provenance id changing is not a change to what a person read, and putting
    them in the digest would ask people to review again over an internal detail.
    What DOES change the digest is any authored value changing - which is the
    whole of "same id, revised content".
    """
    out = {k: v for k, v in record.items() if not k.startswith("_")}
    out["family"] = record.get("_family")
    return out


def _by_id(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sorted by id, because these collections have no meaning in their order.

    A record arriving from a different direction is the same record. Ordered
    values INSIDE a record - a frontier, a candidate list the comparison authored
    - are left exactly as they were authored, because there the order is content.
    """
    return [_shown(r) for r in sorted(records, key=lambda r: r.get("entity_id") or "")]


@dataclass(frozen=True)
class HumanReviewSnapshot:
    """EPHEMERAL. Not a family, not state, and never written.

    It exists for the length of one review: assembled, rendered, hashed, and
    submitted against. Making it a DesignState family would create a record whose
    only content is what another record already says, and something downstream
    would eventually premise on it.
    """

    comparison: Dict[str, Any]
    profile: Dict[str, Any]
    candidates: Tuple[Dict[str, Any], ...]
    eligibility: Tuple[Dict[str, Any], ...]
    eligible_candidates: Tuple[str, ...]
    population_established: bool
    feasibility_assessments: Tuple[Dict[str, Any], ...]
    hard_requirement_results: Tuple[Dict[str, Any], ...]
    design_constraints: Tuple[Dict[str, Any], ...]
    advisories: Tuple[Dict[str, Any], ...]
    concerns: Tuple[Dict[str, Any], ...]
    digest: str

    def payload(self) -> Dict[str, Any]:
        """Exactly what the digest is taken over, and exactly what is rendered."""
        return {"comparison": self.comparison, "profile": self.profile,
                "candidates": list(self.candidates),
                "eligibility": list(self.eligibility),
                "eligible_candidates": list(self.eligible_candidates),
                "population_established": self.population_established,
                "feasibility_assessments": list(self.feasibility_assessments),
                "hard_requirement_results": list(self.hard_requirement_results),
                "design_constraints": list(self.design_constraints),
                "advisories": list(self.advisories),
                "concerns": list(self.concerns)}

    # -- what a renderer asks -------------------------------------------
    def advisory_ids(self) -> List[str]:
        return sorted(a["entity_id"] for a in self.advisories)

    def concern_ids(self) -> List[str]:
        return sorted(c["entity_id"] for c in self.concerns)

    def basis_refs(self) -> List[str]:
        """Every record the eligible population was established from.

        The premise set of a commitment made on this review, and nothing else:
        the assessments, the compliance records, the requirements consulted for
        their blocking semantics, and the candidates themselves.
        """
        return sorted({r["entity_id"] for r in self.feasibility_assessments}
                      | {r["entity_id"] for r in self.hard_requirement_results}
                      | {r["entity_id"] for r in self.design_constraints}
                      | {r["entity_id"] for r in self.candidates})


def human_review_digest(payload: Dict[str, Any]) -> str:
    """SHA-256 over the canonical review. THE SAME MEANING IS THE SAME DIGEST.

    `sort_keys` recursively, so a mapping built in a different order hashes the
    same - key order is not meaning, and a screen that reordered its own dict
    must not tell a person the design moved. Separators are pinned so whitespace
    is not content either.
    """
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   default=str).encode()).hexdigest()


class HumanReviewOutcome:
    """The snapshot, or exactly why there is nothing a person may review yet."""

    __slots__ = ("status", "snapshot", "problems", "consumer_view")

    def __init__(self, status, snapshot=None, problems=None, consumer_view=None):
        self.status = status
        self.snapshot = snapshot
        self.problems = list(problems or [])
        self.consumer_view = consumer_view

    @property
    def ready(self) -> bool:
        return self.status == REVIEW_READY and self.snapshot is not None


def build_human_review_snapshot(state) -> HumanReviewOutcome:
    """Assemble the one thing a human is shown, from the one declared view.

    NO PROVIDER AND NO WRITE. Advisory material is admitted and never required:
    a reviewer that was never asked, or was asked and failed, cannot be allowed
    to decide whether a person may look at their own design.
    """
    from ..view import consumer_view_for

    view = consumer_view_for(REVIEW_PASS, state)
    unmet = [a["requirement"] for a in view.assessment
             if a["verdict"] != "SATISFIED"]
    if view.status is not ViewStatus.VIEW_READY:
        return HumanReviewOutcome(
            REVIEW_CONTEXT_NOT_READY,
            problems=["%s: consumer context is %s" % (REVIEW_PASS, view.status.value)]
                     + unmet, consumer_view=view.as_dict())

    payload = view.payload()
    comparisons = [c for c in (payload.get("CandidateComparison") or [])
                   if isinstance(c, dict)]
    if len(comparisons) != 1:
        # NEVER FIRST-WINS. Which comparison a person is being asked about is the
        # design's to say, and two of them is a question rather than a tie.
        return HumanReviewOutcome(
            NO_CURRENT_COMPARISON if not comparisons else REVIEW_CONTEXT_AMBIGUOUS,
            problems=["%d current deterministic comparisons: %s"
                      % (len(comparisons),
                         ", ".join(sorted(c.get("entity_id", "?")
                                          for c in comparisons)))],
            consumer_view=view.as_dict())
    comparison = comparisons[0]

    profiles = [p for p in (payload.get("SelectionProfile") or [])
                if isinstance(p, dict)]
    if len(profiles) != 1:
        return HumanReviewOutcome(
            REVIEW_CONTEXT_AMBIGUOUS if profiles else REVIEW_CONTEXT_NOT_READY,
            problems=["%d current selection profiles" % len(profiles)],
            consumer_view=view.as_dict())
    profile = profiles[0]
    if profile["entity_id"] != comparison.get("profile"):
        # THE PROFILE THE COMPARISON WAS MADE UNDER, not whichever one is current.
        # Showing a person today's preferences beside yesterday's comparison would
        # be showing them a judgement made under something else.
        return HumanReviewOutcome(
            REVIEW_PROFILE_NOT_CURRENT,
            problems=["the comparison was made under %s and the current profile "
                      "is %s" % (comparison.get("profile"), profile["entity_id"])],
            consumer_view=view.as_dict())

    # ELIGIBILITY THROUGH THE CANONICAL SEMANTICS, over the retained population -
    # not read off the comparison. What the comparison holds is evidence about a
    # moment; what this computes is the answer now.
    ev = sel.evidence_of(state, payload)
    population = sel.eligibility(ev)
    basis: set = set()
    rows = []
    for candidate in sorted(population):
        verdict, why, used = population[candidate]
        basis |= set(used)
        rows.append({"candidate": candidate, "verdict": verdict, "why": why,
                     "basis": sorted(used)})
    eligible = tuple(sorted(k for k, (v, _w, _u) in population.items()
                            if v == sel.ELIGIBLE))
    established = not any(v == sel.UNRESOLVED for v, _w, _u in population.values())

    def of(family: str) -> List[Dict[str, Any]]:
        return _by_id([r for r in (payload.get(family) or [])
                       if isinstance(r, dict) and r.get("entity_id") in basis])

    snapshot_fields = dict(
        comparison=_shown(comparison), profile=_shown(profile),
        candidates=tuple(_by_id([c for c in (payload.get("Candidate") or [])
                                 if isinstance(c, dict)])),
        eligibility=tuple(rows), eligible_candidates=eligible,
        population_established=established,
        feasibility_assessments=tuple(of("MechanicalFeasibilityAssessment")),
        hard_requirement_results=tuple(of("HardRequirementCompliance")),
        design_constraints=tuple(of("DesignConstraint")),
        advisories=tuple(_by_id([a for a in (payload.get("SelectionAdvisory") or [])
                                 if isinstance(a, dict)])),
        concerns=tuple(_by_id([c for c in (payload.get("SelectionConcern") or [])
                               if isinstance(c, dict)])))
    snapshot = HumanReviewSnapshot(digest="", **snapshot_fields)
    return HumanReviewOutcome(
        REVIEW_READY,
        HumanReviewSnapshot(digest=human_review_digest(snapshot.payload()),
                            **snapshot_fields),
        consumer_view=view.as_dict())


# =====================================================================
# what the human submitted
# =====================================================================
class HumanInputOutcome:
    """The submitted record, or why the submission was not one."""

    __slots__ = ("status", "input_id", "patch", "problems")

    def __init__(self, status, input_id=None, patch=None, problems=None):
        self.status = status
        self.input_id = input_id
        self.patch = patch
        self.problems = list(problems or [])

    @property
    def ok(self) -> bool:
        return self.status in (HUMAN_INPUT_RECORDED, HUMAN_INPUT_UNCHANGED)


def _text(value: Any, what: str, problems: List[str]) -> Optional[str]:
    """A non-empty string, with nothing coerced into being one.

    `bool` is excluded explicitly because it is an `int` subclass. A rationale of
    `0` is not the string "0": a person who submitted the wrong type submitted
    something this code would have to interpret, and interpreting a human's
    reason for a decision is the one thing it must never do.
    """
    if isinstance(value, bool) or not isinstance(value, str):
        problems.append("%s must be a string, not %s"
                        % (what, type(value).__name__))
        return None
    if not value.strip():
        problems.append("%s is empty" % what)
        return None
    return value.strip()


def input_identity(digest: str, action: str, candidate: Optional[str],
                   rationale: str) -> str:
    """Content identity over the submission. NO COUNTER AND NO CLOCK.

    The same person submitting the same thing twice submitted one thing. A
    different rationale is a different submission, because the reason IS part of
    what a human decided - and both stay, because a human input is historical
    provenance rather than a value to be updated.
    """
    payload = json.dumps([digest, action, candidate, rationale],
                         separators=(",", ":"), sort_keys=True)
    return "HDI-%s" % hashlib.sha256(payload.encode()).hexdigest()[:12].upper()


def materialize_human_decision_input(state, snapshot: HumanReviewSnapshot,
                                     action: Any, selected_candidate: Any = None,
                                     rationale: Any = None,
                                     run_id: Optional[str] = None,
                                     attempt: int = 1) -> HumanInputOutcome:
    """Turn what a person controlled into the one record they may author.

    THE HUMAN SUPPLIES THREE THINGS: an action, a candidate when the action is
    SELECT, and their reason. Everything structural - which comparison, which
    profile, which advisory material was on the screen, and the digest of all of
    it - comes from the snapshot that was actually rendered. A client cannot
    claim to have reviewed one thing while submitting against another, because it
    never gets to say what it reviewed.
    """
    problems: List[str] = []
    if not isinstance(snapshot, HumanReviewSnapshot):
        return HumanInputOutcome(
            INVALID_HUMAN_INPUT,
            problems=["a submission must be made against a rendered review, not "
                      "against %s" % type(snapshot).__name__])
    if isinstance(action, bool) or action not in ACTIONS:
        problems.append("action is %r; the vocabulary is %s"
                        % (action, list(ACTIONS)))
    text = _text(rationale, "rationale", problems)

    population = list(snapshot.comparison.get("candidates") or [])
    if action == SELECT:
        candidate = _text(selected_candidate, "selected_candidate", problems)
        if candidate is not None and candidate not in population:
            # AGAINST WHAT WAS SHOWN. Whether it is still eligible is asked again
            # by the writer, against current state; this asks the narrower
            # question a submission can answer - was it even on the screen.
            problems.append("%s was not among the candidates this review showed "
                            "(%s)" % (candidate, ", ".join(sorted(population))))
    else:
        candidate = None
        if selected_candidate is not None:
            # EXACTLY None. `if selected_candidate:` would read "", 0, False and
            # [] as "no candidate", which are four malformed submissions wearing
            # the one legitimate way to say a person named nobody.
            problems.append("%s names %r; only an absent candidate means none was "
                            "selected" % (action, selected_candidate))
    if problems:
        return HumanInputOutcome(INVALID_HUMAN_INPUT, problems=problems)

    fields: Dict[str, Any] = {
        "action": action, "rationale": text,
        "comparison": snapshot.comparison["entity_id"],
        "profile": snapshot.profile["entity_id"],
        "premise_digest": snapshot.digest,
        "reviewed_advisories": snapshot.advisory_ids(),
        "reviewed_concerns": snapshot.concern_ids()}
    if candidate is not None:
        fields["selected_candidate"] = candidate
    eid = input_identity(snapshot.digest, action, candidate, text)
    if state.has_entity(eid):
        # IDEMPOTENT, AND NOT AN UPDATE. The same submission is one submission;
        # a second record would say a person decided twice.
        return HumanInputOutcome(HUMAN_INPUT_UNCHANGED, eid)

    # NO PREMISE REFS, DELIBERATELY. "I submitted this after seeing snapshot X"
    # stays true when X stops being current - that is exactly the fact a stale
    # submission is made of, and a record that went STALE with the comparison
    # could not be found later to be refused. What was shown is recorded in the
    # fields and in the digest; the record claims nothing about it still holding.
    op = Op("CREATE", "HumanDecisionInput", eid, fields, "selection:human_input")
    patch = StagePatch(
        patch_id="%s-human-decision-%s" % (run_id or state.run_id, eid),
        run_id=run_id or state.run_id, stage_id=RESPONSIBILITY,
        stage_attempt=attempt, parent_state_hash=state.state_hash(),
        operations=[op], execution_status="SUCCESS",
        provenance={"purpose": "record what the human submitted at the decision "
                               "screen", "provider": "human"})
    problems = state.validate(patch)
    return HumanInputOutcome(
        HUMAN_INPUT_RECORDED if not problems else INVALID_HUMAN_INPUT, eid,
        None if problems else patch, problems)


# =====================================================================
# the deterministic commitment
# =====================================================================
class SelectionCommitOutcome:
    """What the writer did, and - when it did nothing - exactly why not."""

    __slots__ = ("status", "decision_id", "patch", "problems", "snapshot",
                 "human_input")

    def __init__(self, status, decision_id=None, patch=None, problems=None,
                 snapshot=None, human_input=None):
        self.status = status
        self.decision_id = decision_id
        self.patch = patch
        self.problems = list(problems or [])
        self.snapshot = snapshot
        self.human_input = human_input

    @property
    def committed(self) -> bool:
        return self.status in (SELECTION_COMMITTED, SELECTION_UNCHANGED)

    @property
    def accepted(self) -> bool:
        """The human's action was recorded and understood. NOT the same as
        committed: declining to commit is an answer, not a failure."""
        return self.committed or self.status in ACCEPTED_WITHOUT_COMMITMENT


def decision_identity(human_input: Dict[str, Any], candidate: str,
                      comparison: str, profile: str,
                      basis: Sequence[str]) -> str:
    """Content identity over the commitment. Same accepted submission, same id."""
    payload = json.dumps([human_input["entity_id"], candidate, comparison, profile,
                          sorted(basis)], separators=(",", ":"), sort_keys=True)
    return "SLD-%s" % hashlib.sha256(payload.encode()).hexdigest()[:12].upper()


def _submitted(state, human_decision_id: Any):
    """The named submission, read through this pass's own declared view."""
    from ..view import consumer_view_for

    if not isinstance(human_decision_id, str) or not human_decision_id.strip():
        return None, ["a human decision id is required, not %s"
                      % type(human_decision_id).__name__]
    view = consumer_view_for(DECISION_PASS, state)
    found = [h for h in (view.payload().get("HumanDecisionInput") or [])
             if isinstance(h, dict) and h.get("entity_id") == human_decision_id]
    if len(found) != 1:
        return None, ["%s is not a current human decision input"
                      % human_decision_id]
    return found[0], []


def commit_human_selection(state, human_decision_id: str,
                           run_id: Optional[str] = None,
                           attempt: int = 1) -> SelectionCommitOutcome:
    """Commit what a human selected, if what they saw is still what is true.

    NO PROVIDER, NO PROMPT, NO SCREEN. The order of the checks below is part of
    the contract: the submission is resolved, an existing commitment is protected,
    the review is rebuilt from CURRENT state, the digest is recomputed rather than
    trusted, the named context is cross-checked, the action is honoured, and only
    then is eligibility re-established and a record written.
    """
    human, problems = _submitted(state, human_decision_id)
    if human is None:
        return SelectionCommitOutcome(INVALID_HUMAN_INPUT, problems=problems)

    # STEP 2 - AN EXISTING COMMITMENT IS NOT THIS STEP'S TO MOVE. Reopening and
    # reselection are lifecycle work; silently superseding here would be that
    # work done without any of its rules.
    standing = state.standing("SelectionDecision")
    if standing:
        replay = [d for d in standing
                  if d.get("human_decision") == human["entity_id"]]
        if replay:
            return SelectionCommitOutcome(SELECTION_UNCHANGED,
                                          replay[0]["entity_id"],
                                          snapshot=None, human_input=human)
        return SelectionCommitOutcome(
            DECISION_ALREADY_STANDING,
            problems=["%s already stands for %s; changing a commitment is not "
                      "this step's to do"
                      % (", ".join(sorted(d["entity_id"] for d in standing)),
                         ", ".join(sorted(str(d.get("selected_candidate"))
                                          for d in standing)))],
            human_input=human)

    # STEP 3 - THE CURRENT REVIEW, rebuilt. Never a cached snapshot and never the
    # one the client is holding.
    review = build_human_review_snapshot(state)
    if not review.ready:
        # The material moved so far that there is no review to compare against.
        # That is a stale screen by definition: the person must look again.
        return SelectionCommitOutcome(
            STALE_SUBMISSION,
            problems=["the current review context is %s" % review.status]
                     + review.problems, human_input=human)
    snapshot = review.snapshot

    # STEP 4 - THE DIGEST, RECOMPUTED. The submitted one is a claim about a
    # screen; this is the design saying what that screen would show now.
    if human.get("premise_digest") != snapshot.digest:
        return SelectionCommitOutcome(
            STALE_SUBMISSION,
            problems=["the submission was made against %s and the current review "
                      "is %s" % (str(human.get("premise_digest"))[:12],
                                 snapshot.digest[:12])],
            snapshot=snapshot, human_input=human)

    # STEP 5/6 - the named context, explicitly. The digest already covers all of
    # it; naming the mismatch is what makes the refusal auditable.
    named = [("comparison", human.get("comparison"), snapshot.comparison["entity_id"]),
             ("profile", human.get("profile"), snapshot.profile["entity_id"]),
             ("reviewed_advisories", sorted(human.get("reviewed_advisories") or []),
              snapshot.advisory_ids()),
             ("reviewed_concerns", sorted(human.get("reviewed_concerns") or []),
              snapshot.concern_ids())]
    mismatched = ["the submission names %s %r and the current review is %r"
                  % (what, was, now) for what, was, now in named if was != now]
    if mismatched:
        return SelectionCommitOutcome(SUBMISSION_CONTEXT_MISMATCH,
                                      problems=mismatched, snapshot=snapshot,
                                      human_input=human)

    # STEP 7 - a person who declined to commit has answered the question. Nothing
    # is written, nothing is chosen for them, and it is not a failure.
    if human.get("action") == KEEP_UNRESOLVED:
        return SelectionCommitOutcome(HUMAN_KEPT_UNRESOLVED, snapshot=snapshot,
                                      human_input=human)
    if human.get("action") == REQUEST_MORE_EVIDENCE:
        return SelectionCommitOutcome(MORE_EVIDENCE_REQUESTED, snapshot=snapshot,
                                      human_input=human)
    if human.get("action") != SELECT:
        return SelectionCommitOutcome(
            INVALID_HUMAN_INPUT,
            problems=["action %r is not one this writer knows"
                      % human.get("action")], snapshot=snapshot, human_input=human)

    # STEP 8 - ELIGIBILITY, RE-ESTABLISHED. `population_established` is False when
    # any retained candidate's eligibility cannot currently be decided, and an
    # unknown candidate makes the whole population unknown: committing from the
    # subset that happened to be knowable would commit against a design nobody has.
    candidate = human.get("selected_candidate")
    if not snapshot.population_established:
        return SelectionCommitOutcome(
            SELECTION_CONTEXT_INCONSISTENT,
            problems=["the eligible population is not currently established: %s"
                      % "; ".join("%s is %s (%s)" % (r["candidate"], r["verdict"],
                                                     r["why"])
                                  for r in snapshot.eligibility
                                  if r["verdict"] == sel.UNRESOLVED)],
            snapshot=snapshot, human_input=human)
    if candidate not in snapshot.eligible_candidates:
        return SelectionCommitOutcome(
            SELECTION_NO_LONGER_ELIGIBLE,
            problems=["%s is not currently eligible: %s"
                      % (candidate,
                         "; ".join(r["why"] for r in snapshot.eligibility
                                   if r["candidate"] == candidate) or "unknown")],
            snapshot=snapshot, human_input=human)

    # STEP 9 - the comparison is CROSS-CHECKED against the recomputed population,
    # never used in place of it. A comparison whose population no longer matches
    # the eligible set is evidence about a design that has moved.
    if sorted(snapshot.comparison.get("candidates") or []) != \
            sorted(snapshot.eligible_candidates):
        return SelectionCommitOutcome(
            SELECTION_CONTEXT_INCONSISTENT,
            problems=["the comparison holds %s and the currently eligible set is "
                      "%s" % (sorted(snapshot.comparison.get("candidates") or []),
                              sorted(snapshot.eligible_candidates))],
            snapshot=snapshot, human_input=human)

    # STEP 10 - the commitment.
    basis = snapshot.basis_refs()
    eid = decision_identity(human, candidate, snapshot.comparison["entity_id"],
                            snapshot.profile["entity_id"], basis)
    fields = {
        "selected_candidate": candidate,
        "eligible_candidates": list(snapshot.eligible_candidates),
        "feasibility_assessments": [r["entity_id"]
                                    for r in snapshot.feasibility_assessments],
        "hard_requirement_results": [r["entity_id"]
                                     for r in snapshot.hard_requirement_results],
        "selection_profile": snapshot.profile["entity_id"],
        "comparison": snapshot.comparison["entity_id"],
        "human_decision": human["entity_id"],
        # CONSIDERED, exactly as submitted. Not whatever advisory happens to be
        # newest at commit time: what a decision may record is what the person
        # actually read, and the digest is what guarantees that was current.
        "considered_advisories": sorted(human.get("reviewed_advisories") or []),
        "considered_concerns": sorted(human.get("reviewed_concerns") or [])}
    if human.get("rationale"):
        fields["rationale"] = human["rationale"]
    # PREMISES ARE THE FACTS, and the human's request. Advisory material is in
    # the fields above and NOT here, so rewording a review after the fact leaves
    # this standing - the wording was never what made the candidate choosable.
    premises = sorted(set(basis) | {human["entity_id"],
                                    snapshot.comparison["entity_id"],
                                    snapshot.profile["entity_id"]})
    op = Op("CREATE", "SelectionDecision", eid, fields, "selection:decision",
            premise_refs=premises)
    patch = StagePatch(
        patch_id="%s-selection-decision-%s" % (run_id or state.run_id, eid),
        run_id=run_id or state.run_id, stage_id=RESPONSIBILITY,
        stage_attempt=attempt, parent_state_hash=state.state_hash(),
        operations=[op], execution_status="SUCCESS",
        provenance={"purpose": "commit the candidate the human selected",
                    "provider": "deterministic"})
    problems = state.validate(patch)
    return SelectionCommitOutcome(
        SELECTION_COMMITTED if not problems else SELECTION_CONTEXT_INCONSISTENT,
        eid, None if problems else patch, problems, snapshot, human)
