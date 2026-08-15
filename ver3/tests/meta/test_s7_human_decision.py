"""S7-E: the human checkpoint, and everything that must not decide for them.

Every probe runs the REAL chain - s01 through s04b through feasibility, the real
selection comparison, the real advisory pass where one is wanted - and then the
real review builder, the real submission record and the real deterministic
writer. Nothing here hand-builds a snapshot: the digest is only worth testing if
it is the digest of what the pipeline actually assembles.

WHAT THESE TESTS ARE GUARDING

    NOTHING CHOOSES BUT A PERSON. A frontier of one, a dominant candidate and a
    reviewer's recommendation are all evidence, and none of them writes a
    commitment. The falsifiers run designs where each of the three would have
    picked something and assert the design is still undecided.

    THE SUBMISSION IS NOT TRUSTED. The digest is recomputed from current state
    and the eligible population is re-established from S7-C's own semantics - so
    an old screen cannot commit, and the comparison's candidate list is never the
    authority on whether its candidates are still choosable.

    THE DIGEST IS NEITHER TOO NARROW NOR TOO WIDE. What was shown changing forces
    a re-review; an entity nobody saw and nothing rests on does not.

    AN OPINION IS NOT A PREMISE. Advisory wording is inside the review a person
    submits against and outside the premise set of what gets committed - so it
    can force a re-review before, and cannot disturb a decision after.
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.selection_advisory as adv                   # noqa: E402
import ver3.assy_v3.stages.selection_decision as dec                   # noqa: E402
import ver3.assy_v3.ui.selection_checkpoint as ui                      # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.assy_v3.state import design_state as ds                      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                    # noqa: E402
from ver3.tools import run_window2                                     # noqa: E402
from .test_s7_advisory import _Advisory, _Failing, concern, review     # noqa: E402
from .test_s7_selection import HIGH, MINIMIZE, MAXIMIZE, prefs         # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _source(*parts: str) -> str:
    """A production file's text. `_REPO` is the `ver3` package root."""
    with open(os.path.join(_REPO, *parts)) as fh:
        return fh.read()


def _code(source: str) -> str:
    """The source with docstrings and comments blanked: WHAT ACTUALLY RUNS.

    A prose audit over raw text answers the wrong question. This module's own
    docstring says the words "provider" and "SelectionDecision" in order to state
    that neither is reachable, and an audit that flagged the sentence saying so
    would be measuring the explanation rather than the code.
    """
    lines = source.splitlines()
    blank = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and \
                isinstance(body[0].value, ast.Str):
            blank |= set(range(body[0].lineno - 1, body[0].value.end_lineno))
    kept = []
    for n, line in enumerate(lines):
        if n in blank:
            kept.append("")
            continue
        cut = line.find("#")
        kept.append(line[:cut] if cut >= 0 and line[:cut].count('"') % 2 == 0
                    and line[:cut].count("'") % 2 == 0 else line)
    return "\n".join(kept)


class _Surface:
    """A drawing surface that records instead of drawing.

    The Streamlit dependency is not installed in this environment, so the page
    logic is exercised through the same surface protocol the real entry point
    hands `streamlit` to. What is tested here is the HUMAN-CONTROL SEMANTICS -
    what is shown, what may be chosen, what a submission does - and not the
    browser, which is not claimed to have been tested at all.
    """

    def __init__(self, action=None, candidate=None, rationale="a reason",
                 submitted=False):
        self.action, self.candidate = action, candidate
        self.rationale, self.submitted = rationale, submitted
        self.lines, self.controls, self.said = [], [], []

    # -- what a page draws ---------------------------------------------
    def markdown(self, text):
        self.lines.append(str(text))

    def warning(self, text):
        self.said.append(("warning", str(text)))

    def success(self, text):
        self.said.append(("success", str(text)))

    def info(self, text):                                      # pragma: no cover
        self.said.append(("info", str(text)))

    # -- what a person operates ----------------------------------------
    def radio(self, label, options, index=0):
        self.controls.append({"kind": "radio", "label": label,
                              "options": list(options), "index": index})
        return self.action if self.action is not None else list(options)[index]

    def selectbox(self, label, options, index=0):
        self.controls.append({"kind": "selectbox", "label": label,
                              "options": list(options), "index": index})
        return self.candidate if self.candidate is not None else list(options)[index]

    def text_area(self, label):
        self.controls.append({"kind": "text_area", "label": label})
        return self.rationale

    def button(self, label):
        self.controls.append({"kind": "button", "label": label})
        return self.submitted

    # -- what a test asks ----------------------------------------------
    def text(self):
        return "\n".join(self.lines)

    def kinds(self):
        return [c["kind"] for c in self.controls]


class _Decision(_Advisory):
    """A design that has been compared, optionally reviewed, and is now a
    question for a person."""

    OTHER = prefs(rigid_body_count=(MAXIMIZE, HIGH))

    # -- building the situation ----------------------------------------
    def reviewable(self, candidates=("A", "B"), preferences=None, advisory=None,
                   state=None):
        state, _cmp = self.compared(candidates=candidates,
                                    preferences=preferences, state=state)
        if advisory is not None:
            state, out, _p = self.reviewed(advisory, state=state)
            self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status,
                             out.problems)
        return state

    def review_of(self, state):
        out = dec.build_human_review_snapshot(state)
        self.assertTrue(out.ready, (out.status, out.problems))
        return out.snapshot

    # -- the two backend acts ------------------------------------------
    def submit(self, state, snapshot, action=dec.SELECT, candidate=None,
               rationale="a considered reason"):
        out = dec.materialize_human_decision_input(state, snapshot, action,
                                                   candidate, rationale)
        if out.patch is not None:
            state.apply(out.patch)
        return out

    def commit(self, state, input_id):
        out = dec.commit_human_selection(state, input_id)
        if out.patch is not None:
            state.apply(out.patch)
        return out

    def decide(self, state, candidate, rationale="a considered reason",
               snapshot=None, action=dec.SELECT):
        snapshot = snapshot if snapshot is not None else self.review_of(state)
        submitted = self.submit(state, snapshot, action, candidate, rationale)
        self.assertTrue(submitted.ok, submitted.problems)
        return self.commit(state, submitted.input_id)

    def committed_decision(self, state):
        found = state.standing("SelectionDecision")
        self.assertEqual(1, len(found), found)
        return found[0]

    def assertNoCommitment(self, state, out=None):
        self.assertEqual([], state.family("SelectionDecision"),
                         "something was committed")
        if out is not None:
            self.assertIsNone(out.patch)
            self.assertFalse(out.committed)

    # -- moving the design under a review ------------------------------
    def invalidate(self, state, entity_id, stage="selection", why="a probe"):
        self.revise(state, Op("INVALIDATE", state.stored_family(entity_id),
                              entity_id, {}, "t", reason=why), stage=stage)

    def unrelated(self, state, eid="AMB-PROBE"):
        """An entity no premise class admits and nothing in the review rests on."""
        self.revise(state, Op("CREATE", "Ambiguity", eid,
                              {"statement": "an unrelated open question",
                               "conflicting_clauses": [],
                               "resolvable_when": "somebody says"}, "t"),
                    stage="s01")
        return eid

    def blocking(self, state, statuses, eid="DSC-Q001"):
        """A NEW blocking requirement plus its compliance records.

        Nothing is superseded, so the comparison stays standing and current while
        the eligible population underneath it moves - which is the only way to
        ask whether the writer re-establishes eligibility or reads it off the
        comparison.
        """
        self.constraint(state, eid=eid, blocks=True)
        for candidate, status in sorted(statuses.items()):
            self.hrc(state, candidate, eid, status)
        return eid

    def recompliance(self, state, candidate, constraint, status):
        """The same requirement, re-evaluated. The old record is withdrawn and a
        new one takes its place, which is what happens when evidence moves - and
        withdrawing it stales everything premised on it."""
        self.invalidate(state, "HRC-%s-%s" % (candidate, constraint),
                        stage="feasibility", why="re-evaluated on new evidence")
        self.revise(state, Op("CREATE", "HardRequirementCompliance",
                              "HRC-%s-%s-V2" % (candidate, constraint),
                              {"candidate": candidate, "constraint": constraint,
                               "status": status, "why": "probe"}, "t",
                              premise_refs=[candidate, constraint]),
                    stage="feasibility")

    def second_assessment(self, state, candidate="CND-A"):
        """A duplicate current feasibility assessment: eligibility unknown."""
        self.revise(state, Op("CREATE", "MechanicalFeasibilityAssessment",
                              "MFA-DUP-%s" % candidate,
                              {"candidate": candidate, "status": "FEASIBLE",
                               "domain_assessments": []}, "t",
                              premise_refs=[candidate]),
                    stage="feasibility")


# =====================================================================
# E01-E11 - the review a human is shown
# =====================================================================
class TestReviewSnapshot(_Decision):

    def test_E01_a_compared_design_is_reviewable(self):
        state = self.reviewable()
        out = dec.build_human_review_snapshot(state)
        self.assertEqual(dec.REVIEW_READY, out.status, out.problems)
        snapshot = out.snapshot
        self.assertEqual(("CND-A", "CND-B"), snapshot.eligible_candidates)
        self.assertTrue(snapshot.population_established)
        self.assertTrue(snapshot.digest)
        self.assertEqual([], state.family("HumanDecisionInput"))
        self.assertEqual([], state.family("SelectionDecision"))

    def test_E02_no_comparison_is_no_checkpoint(self):
        """A screen asking a person to choose between candidates nobody compared
        would be asking them to choose from nothing established."""
        state = self.built()
        out = dec.build_human_review_snapshot(state)
        self.assertIn(out.status, (dec.NO_CURRENT_COMPARISON,
                                   dec.REVIEW_CONTEXT_NOT_READY))
        self.assertIsNone(out.snapshot)

    def test_E03_two_current_comparisons_are_a_question_not_a_tie(self):
        state = self.reviewable()
        current = state.standing("CandidateComparison")[0]
        self.revise(state, Op("CREATE", "CandidateComparison", "CCP-PROBE0002",
                              {k: v for k, v in current.items()
                               if not k.startswith("_") and k != "entity_id"},
                              "t"), stage="selection")
        out = dec.build_human_review_snapshot(state)
        self.assertEqual(dec.REVIEW_CONTEXT_AMBIGUOUS, out.status)
        self.assertIsNone(out.snapshot)

    def test_E04_the_profile_shown_is_the_one_the_comparison_was_made_under(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        self.assertEqual(snapshot.comparison["profile"],
                         snapshot.profile["entity_id"])
        self.assertEqual(self.PREFS, snapshot.profile["criteria"])

    def test_E04b_a_comparison_naming_a_superseded_profile_is_not_reviewable(self):
        """The guard, reached the only way it can be. Ordinarily a profile change
        stales the comparison premised on it and there is no review at all; this
        builds a comparison that names the OLD profile after a new one stands,
        which is the shape a screen must never quietly render."""
        state = self.reviewable()
        old_profile = state.standing("SelectionProfile")[0]["entity_id"]
        current = state.standing("CandidateComparison")[0]
        fields = {k: v for k, v in current.items()
                  if not k.startswith("_") and k != "entity_id"}
        self.profile(state, self.OTHER)
        self.assertNotEqual(old_profile,
                            state.standing("SelectionProfile")[0]["entity_id"])
        self.revise(state, Op("CREATE", "CandidateComparison", "CCP-PROBE0003",
                              fields, "t"), stage="selection")
        out = dec.build_human_review_snapshot(state)
        self.assertEqual(dec.REVIEW_PROFILE_NOT_CURRENT, out.status, out.problems)
        self.assertIsNone(out.snapshot)

    def test_E05_no_advisory_still_gives_a_checkpoint(self):
        """AN LLM HAS NO VETO. The provider failed, so no advisory exists; a
        person may still look at their own design and decide."""
        state, _cmp = self.compared()
        _s, out, provider = self.reviewed(None, state=state, provider=_Failing())
        self.assertIsNone(out.patch)
        self.assertEqual(1, provider.calls)
        self.assertEqual([], state.family("SelectionAdvisory"))
        snapshot = self.review_of(state)
        self.assertEqual((), snapshot.advisories)
        self.assertEqual((), snapshot.concerns)

    def test_E06_advisory_material_appears_exactly(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="A is simpler",
            concerns=[concern("CND-B", "more joints to align", importance="HIGH")]))
        snapshot = self.review_of(state)
        self.assertEqual([a["entity_id"] for a in state.standing("SelectionAdvisory")],
                         snapshot.advisory_ids())
        self.assertEqual([c["entity_id"] for c in state.standing("SelectionConcern")],
                         snapshot.concern_ids())
        self.assertEqual("A is simpler", snapshot.advisories[0]["reasoning"])
        self.assertEqual("more joints to align", snapshot.concerns[0]["issue"])

    def test_E07_mapping_order_is_not_meaning(self):
        """A dict built in another order is the same review. A digest that moved
        with insertion order would tell a person the design changed because a
        renderer iterated differently."""
        snapshot = self.review_of(self.reviewable())
        payload = snapshot.payload()

        def reordered(obj):
            if isinstance(obj, dict):
                return {k: reordered(obj[k]) for k in reversed(list(obj))}
            if isinstance(obj, list):
                return [reordered(v) for v in obj]
            return obj

        shuffled = reordered(payload)
        self.assertNotEqual(list(payload), list(shuffled))
        self.assertEqual(dec.human_review_digest(payload),
                         dec.human_review_digest(shuffled))
        self.assertEqual(snapshot.digest, dec.human_review_digest(shuffled))

    def test_E08_arrival_order_of_records_is_not_meaning(self):
        """The collections whose order carries nothing are ordered by id when the
        snapshot is built, so the order records happen to arrive in cannot reach
        the digest. What IS ordered - the comparison's own candidate list, its
        frontier - is left exactly as it was authored."""
        state = self.reviewable(advisory=review(
            concerns=[concern("CND-A", "one"), concern("CND-B", "two")]))
        snapshot = self.review_of(state)
        for collection in (snapshot.candidates, snapshot.feasibility_assessments,
                           snapshot.advisories, snapshot.concerns):
            ids = [r["entity_id"] for r in collection]
            self.assertEqual(sorted(ids), ids)
        records = list(snapshot.concerns)
        self.assertEqual(dec._by_id(records), dec._by_id(list(reversed(records))))
        self.assertEqual(list(snapshot.comparison["frontier"]),
                         state.standing("CandidateComparison")[0]["frontier"])

    def test_E09_a_revised_value_behind_the_same_id_is_a_different_review(self):
        """IDS ARE NOT THE REVIEW. A digest over identifiers alone would call a
        changed feasibility verdict the same screen."""
        snapshot = self.review_of(self.reviewable(advisory=review(
            concerns=[concern("CND-B", "the original wording")])))
        for path in ("feasibility_assessments", "concerns", "eligibility"):
            payload = snapshot.payload()
            row = dict(payload[path][0])
            row[sorted(k for k in row if isinstance(row[k], str))[0]] = "moved"
            payload[path] = [row] + payload[path][1:]
            self.assertNotEqual(snapshot.digest, dec.human_review_digest(payload),
                                "%s is not covered by the digest" % path)
        ids_only = {"comparison": snapshot.comparison["entity_id"],
                    "profile": snapshot.profile["entity_id"]}
        self.assertNotEqual(snapshot.digest, dec.human_review_digest(ids_only))

    def test_E10_an_entity_nobody_saw_is_not_part_of_the_review(self):
        state = self.reviewable()
        before = self.review_of(state).digest
        self.unrelated(state)
        self.assertEqual(before, self.review_of(state).digest)

    def test_E11_the_digest_is_not_the_state_hash(self):
        """A whole-state hash would make every unrelated write a reason to ask a
        person to look again, which is how a checkpoint becomes a click-through."""
        state = self.reviewable()
        snapshot = self.review_of(state)
        self.assertNotEqual(state.state_hash(), snapshot.digest)
        self.unrelated(state)
        self.assertNotEqual(state.state_hash(), snapshot.digest)
        self.assertEqual(snapshot.digest, self.review_of(state).digest)
        self.assertNotIn("state_hash", inspect.getsource(dec.build_human_review_snapshot))
        self.assertNotIn("state_hash", inspect.getsource(dec.human_review_digest))


# =====================================================================
# E12-E22 - what a person may submit
# =====================================================================
class TestHumanInput(_Decision):

    def test_E12_a_select_writes_one_human_input_and_nothing_else(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        out = self.submit(state, snapshot, dec.SELECT, "CND-A")
        self.assertEqual(dec.HUMAN_INPUT_RECORDED, out.status, out.problems)
        record = state.standing("HumanDecisionInput")[0]
        self.assertEqual("CND-A", record["selected_candidate"])
        self.assertEqual("selection", record["_created_by"])
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual(1, len(state.family("HumanDecisionInput")))

    def test_E13_a_candidate_the_review_did_not_show_is_refused(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        for candidate in ("CND-ELSEWHERE", "CND-C"):
            out = self.submit(state, snapshot, dec.SELECT, candidate)
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status)
            self.assertIn("was not among the candidates", " ".join(out.problems))
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_E14_a_select_with_no_candidate_is_refused(self):
        state = self.reviewable()
        out = self.submit(state, self.review_of(state), dec.SELECT, None)
        self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status)
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_E15_a_candidate_that_is_not_a_string_is_refused(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        for bad in ("", "   ", 0, False, True, [], {}, ["CND-A"], 7):
            out = self.submit(state, snapshot, dec.SELECT, bad)
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status, repr(bad))
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_E16_keep_unresolved_may_not_name_a_candidate(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        for named in ("CND-A", "", 0, False, [], {}):
            out = self.submit(state, snapshot, dec.KEEP_UNRESOLVED, named)
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status, repr(named))
        ok = self.submit(state, snapshot, dec.KEEP_UNRESOLVED, None)
        self.assertEqual(dec.HUMAN_INPUT_RECORDED, ok.status, ok.problems)
        self.assertNotIn("selected_candidate",
                         state.standing("HumanDecisionInput")[0])

    def test_E17_request_more_evidence_may_not_name_a_candidate(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        for named in ("CND-A", "", 0, [], {}):
            out = self.submit(state, snapshot, dec.REQUEST_MORE_EVIDENCE, named)
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status, repr(named))
        ok = self.submit(state, snapshot, dec.REQUEST_MORE_EVIDENCE, None)
        self.assertEqual(dec.HUMAN_INPUT_RECORDED, ok.status, ok.problems)

    def test_E18_an_action_outside_the_vocabulary_is_refused(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        for bad in ("select", "COMMIT", "", None, 0, True, ["SELECT"], {}):
            out = self.submit(state, snapshot, bad, "CND-A")
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status, repr(bad))
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_E19_a_rationale_is_required_and_is_not_coerced(self):
        """The reason IS part of what a person decided, especially when they
        chose against the comparison. `0` is not the string "0"."""
        state = self.reviewable()
        snapshot = self.review_of(state)
        for bad in (None, "", "   ", 0, False, True, 12, [], {}):
            out = self.submit(state, snapshot, dec.SELECT, "CND-A", bad)
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status, repr(bad))
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_E20_the_same_submission_twice_is_one_submission(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        first = self.submit(state, snapshot, dec.SELECT, "CND-A", "same reason")
        second = self.submit(state, snapshot, dec.SELECT, "CND-A", "same reason")
        self.assertEqual(dec.HUMAN_INPUT_RECORDED, first.status)
        self.assertEqual(dec.HUMAN_INPUT_UNCHANGED, second.status)
        self.assertEqual(first.input_id, second.input_id)
        self.assertIsNone(second.patch)
        self.assertEqual(1, len(state.family("HumanDecisionInput")))

    def test_E21_a_different_reason_is_a_different_submission(self):
        """Both stay. A human input is historical provenance, not a value that
        gets updated when somebody changes their mind."""
        state = self.reviewable()
        snapshot = self.review_of(state)
        first = self.submit(state, snapshot, dec.SELECT, "CND-A", "for stiffness")
        second = self.submit(state, snapshot, dec.SELECT, "CND-A", "for cost")
        self.assertNotEqual(first.input_id, second.input_id)
        self.assertEqual(2, len(state.standing("HumanDecisionInput")))
        for record in state.standing("HumanDecisionInput"):
            self.assertEqual(snapshot.digest, record["premise_digest"])

    def test_E22_the_backend_fills_everything_structural(self):
        """A client cannot say which review it made its decision against. It is
        not given the chance: the structural fields come from the snapshot that
        was rendered, and the signature has no parameter for any of them."""
        state = self.reviewable(advisory=review(
            concerns=[concern("CND-A", "a concern")]))
        snapshot = self.review_of(state)
        out = self.submit(state, snapshot, dec.SELECT, "CND-A")
        record = state.standing("HumanDecisionInput")[0]
        self.assertEqual(snapshot.comparison["entity_id"], record["comparison"])
        self.assertEqual(snapshot.profile["entity_id"], record["profile"])
        self.assertEqual(snapshot.digest, record["premise_digest"])
        self.assertEqual(snapshot.advisory_ids(), record["reviewed_advisories"])
        self.assertEqual(snapshot.concern_ids(), record["reviewed_concerns"])
        self.assertEqual(out.input_id, record["entity_id"])
        parameters = list(inspect.signature(
            dec.materialize_human_decision_input).parameters)
        for structural in ("comparison", "profile", "premise_digest", "entity_id",
                           "reviewed_advisories", "reviewed_concerns"):
            self.assertNotIn(structural, parameters)

    def test_E22b_a_submission_needs_a_rendered_review(self):
        state = self.reviewable()
        for fake in (None, {}, "a digest", object()):
            out = dec.materialize_human_decision_input(state, fake, dec.SELECT,
                                                       "CND-A", "a reason")
            self.assertEqual(dec.INVALID_HUMAN_INPUT, out.status)
        self.assertEqual([], state.family("HumanDecisionInput"))


# =====================================================================
# E23-E32 - an old screen may not commit
# =====================================================================
class TestStaleSubmission(_Decision):

    def submitted(self, state=None, candidate="CND-A", **kw):
        """A submission made against a review, before the design moves."""
        state = state if state is not None else self.reviewable(**kw)
        snapshot = self.review_of(state)
        out = self.submit(state, snapshot, dec.SELECT, candidate)
        self.assertTrue(out.ok, out.problems)
        return state, snapshot, out.input_id

    def test_E23_an_unchanged_review_commits(self):
        state, snapshot, input_id = self.submitted()
        out = self.commit(state, input_id)
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.assertEqual(snapshot.digest, out.snapshot.digest)
        self.assertEqual("CND-A", self.committed_decision(state)["selected_candidate"])

    def test_E24_a_changed_profile_stops_the_submission(self):
        state, _snapshot, input_id = self.submitted()
        self.profile(state, self.OTHER)
        out = self.commit(state, input_id)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)
        self.assertNoCommitment(state, out)

    def test_E25_a_changed_comparison_stops_the_submission(self):
        state, _snapshot, input_id = self.submitted()
        current = state.standing("CandidateComparison")[0]
        fields = {k: v for k, v in current.items()
                  if not k.startswith("_") and k != "entity_id"}
        fields["outcome"] = sel.TRADEOFF_UNRESOLVED
        fields["frontier"] = list(fields["candidates"])
        self.invalidate(state, current["entity_id"])
        self.revise(state, Op("CREATE", "CandidateComparison", "CCP-PROBE0004",
                              fields, "t"), stage="selection")
        out = self.commit(state, input_id)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)
        self.assertNoCommitment(state, out)

    def test_E26_a_changed_advisory_stops_the_submission(self):
        """The person was reading an opinion that has since been withdrawn. What
        they approved is not what the screen would say now."""
        state, _snapshot, input_id = self.submitted(
            advisory=review(kind="PREFER_CANDIDATE", candidate="CND-A",
                            reasoning="the first opinion"))
        self.invalidate(state, state.standing("SelectionAdvisory")[0]["entity_id"])
        out = self.commit(state, input_id)
        self.assertIn(out.status, (dec.STALE_SUBMISSION,
                                   dec.SUBMISSION_CONTEXT_MISMATCH))
        self.assertNoCommitment(state, out)

    def test_E27_a_changed_concern_stops_the_submission(self):
        state, _snapshot, input_id = self.submitted(
            advisory=review(concerns=[concern("CND-B", "the first concern")]))
        self.invalidate(state, state.standing("SelectionConcern")[0]["entity_id"])
        out = self.commit(state, input_id)
        self.assertIn(out.status, (dec.STALE_SUBMISSION,
                                   dec.SUBMISSION_CONTEXT_MISMATCH))
        self.assertNoCommitment(state, out)

    def test_E28_a_changed_feasibility_assessment_stops_the_submission(self):
        state, _snapshot, input_id = self.submitted()
        self.invalidate(state, "MFA-CND-A", stage="feasibility",
                        why="reassessed on new evidence")
        out = self.commit(state, input_id)
        self.assertFalse(out.committed, out.status)
        self.assertNoCommitment(state, out)

    def test_E29_a_hard_requirement_that_becomes_violated_stops_it(self):
        state = self.reviewable()
        constraint = self.blocking(state, {"CND-A": sel.SATISFIED,
                                           "CND-B": sel.SATISFIED})
        self.compare(state)                       # a comparison under the new set
        state, _snapshot, input_id = self.submitted(state=state)
        self.recompliance(state, "CND-A", constraint, sel.VIOLATED)
        out = self.commit(state, input_id)
        self.assertFalse(out.committed, out.status)
        self.assertNoCommitment(state, out)

    def test_E30_a_hard_requirement_that_becomes_unevaluable_stops_it(self):
        state = self.reviewable()
        constraint = self.blocking(state, {"CND-A": sel.SATISFIED,
                                           "CND-B": sel.SATISFIED})
        self.compare(state)
        state, _snapshot, input_id = self.submitted(state=state)
        self.recompliance(state, "CND-A", constraint, sel.NOT_YET_EVALUABLE)
        out = self.commit(state, input_id)
        self.assertFalse(out.committed, out.status)
        self.assertNoCommitment(state, out)

    def test_E31_an_ambiguous_population_stops_it_however_fresh_the_screen(self):
        """THE CASE THAT PROVES ELIGIBILITY IS RE-ESTABLISHED. A second current
        assessment supersedes nothing, so the comparison stays standing and still
        lists both candidates - and the population underneath it is no longer
        established. A writer reading the comparison's list would commit."""
        state, _snapshot, stale_input = self.submitted()
        self.second_assessment(state, "CND-A")
        out = self.commit(state, stale_input)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)

        fresh = self.review_of(state)
        self.assertFalse(fresh.population_established)
        self.assertEqual(["CND-A", "CND-B"], sorted(fresh.comparison["candidates"]))
        submitted = self.submit(state, fresh, dec.SELECT, "CND-A")
        self.assertTrue(submitted.ok, submitted.problems)
        again = self.commit(state, submitted.input_id)
        self.assertEqual(dec.SELECTION_CONTEXT_INCONSISTENT, again.status)
        self.assertNoCommitment(state, again)

    def test_E32_an_unrelated_invisible_fact_does_not_stale_a_review(self):
        """The other half of the digest's job. Too wide is its own defect: a
        screen that goes stale on everything teaches people to press refresh
        without reading."""
        state, _snapshot, input_id = self.submitted()
        self.unrelated(state)
        out = self.commit(state, input_id)
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.assertEqual("CND-A", self.committed_decision(state)["selected_candidate"])

    def test_E23c_a_new_fact_in_the_basis_stales_a_screen_that_names_the_same_ids(self):
        """THE DIGEST DOING WORK NOTHING ELSE DOES. A requirement stated after
        the screen was drawn supersedes nothing: the comparison, the profile and
        the advisory material the submission names are all still exactly what it
        named. What changed is the evidence the eligible population was read from,
        and only a digest over the VALUES can see that."""
        state, snapshot, input_id = self.submitted()
        self.constraint(state, eid="DSC-N001", blocks=False)
        fresh = self.review_of(state)
        self.assertEqual(snapshot.comparison["entity_id"],
                         fresh.comparison["entity_id"])
        self.assertEqual(snapshot.profile["entity_id"], fresh.profile["entity_id"])
        self.assertEqual(snapshot.advisory_ids(), fresh.advisory_ids())
        self.assertEqual(snapshot.eligible_candidates, fresh.eligible_candidates)
        self.assertNotEqual(snapshot.digest, fresh.digest)
        out = self.commit(state, input_id)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)
        self.assertNoCommitment(state, out)

    def test_E23b_the_writer_recomputes_rather_than_trusting_the_digest(self):
        source = inspect.getsource(dec.commit_human_selection)
        self.assertIn("build_human_review_snapshot(state)", source)
        self.assertLess(source.index("build_human_review_snapshot(state)"),
                        source.index('human.get("premise_digest")'),
                        "the submitted digest is read before one is recomputed")


# =====================================================================
# E33-E41 - the human is the only chooser
# =====================================================================
class TestSelectionAuthority(_Decision):

    def test_E33_a_sole_eligible_candidate_is_not_a_selection(self):
        """A comparison of one is the comparison running out of ways to tell
        alternatives apart. It is not a decision, and nobody has made one."""
        state = self.reviewable(candidates=("A",))
        comparison = state.standing("CandidateComparison")[0]
        self.assertEqual(sel.SOLE_ELIGIBLE, comparison["outcome"])
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual([], state.family("HumanDecisionInput"))
        self.assertTrue(self.review_of(state).digest)
        self.assertEqual([], state.family("SelectionDecision"))
        out = self.decide(state, "CND-A")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)

    def test_E34_a_dominant_candidate_is_not_a_selection(self):
        state = self.reviewable()
        comparison = state.standing("CandidateComparison")[0]
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, comparison["outcome"])
        self.assertEqual(["CND-A"], comparison["frontier"])
        run_window2.run_selection_checkpoint("probe", state, 1)
        self.assertEqual([], state.family("SelectionDecision"))

    def test_E35_an_advisory_recommendation_is_not_a_selection(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="A is simpler"))
        self.assertEqual("CND-A",
                         state.standing("SelectionAdvisory")[0]["recommended_candidate"])
        self.review_of(state)
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_E36_a_human_may_select_a_candidate_outside_the_frontier(self):
        state = self.reviewable()
        self.assertEqual(["CND-A"],
                         state.standing("CandidateComparison")[0]["frontier"])
        out = self.decide(state, "CND-B", "B is easier to make in our shop")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        decision = self.committed_decision(state)
        self.assertEqual("CND-B", decision["selected_candidate"])
        self.assertEqual(["CND-A"],
                         state.standing("CandidateComparison")[0]["frontier"],
                         "the comparison was reconciled to the human")

    def test_E37_a_human_may_select_against_the_advisory(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A"))
        advisory = dict(state.standing("SelectionAdvisory")[0])
        out = self.decide(state, "CND-B", "the reviewer did not weigh assembly")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.assertEqual("CND-B", self.committed_decision(state)["selected_candidate"])
        self.assertEqual({k: v for k, v in advisory.items() if not k.startswith("_")},
                         {k: v for k, v in state.standing("SelectionAdvisory")[0].items()
                          if not k.startswith("_")})

    def test_E38_against_both_the_frontier_and_the_advisory(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A",
            concerns=[concern("CND-B", "more parts", importance="HIGH")]))
        self.assertEqual(["CND-A"],
                         state.standing("CandidateComparison")[0]["frontier"])
        out = self.decide(state, "CND-B", "we accept the extra parts")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.assertEqual("CND-B", self.committed_decision(state)["selected_candidate"])

    def test_E39_an_ineligible_candidate_can_never_be_committed(self):
        state = self.reviewable()
        self.blocking(state, {"CND-A": sel.SATISFIED, "CND-B": sel.VIOLATED})
        fresh = self.review_of(state)
        self.assertEqual(("CND-A",), fresh.eligible_candidates)
        submitted = self.submit(state, fresh, dec.SELECT, "CND-B")
        self.assertTrue(submitted.ok, submitted.problems)
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.SELECTION_NO_LONGER_ELIGIBLE, out.status)
        self.assertNoCommitment(state, out)

    def test_E40_a_preference_cannot_rescue_an_ineligible_candidate(self):
        """The preference ranks B first and B is not choosable. Eligibility and
        preference are answered by different code reading different families, and
        this is the boundary between them at the last possible moment."""
        state = self.reviewable(preferences=self.OTHER)
        self.assertEqual(["CND-B"],
                         state.standing("CandidateComparison")[0]["frontier"])
        self.blocking(state, {"CND-A": sel.SATISFIED, "CND-B": sel.VIOLATED})
        fresh = self.review_of(state)
        submitted = self.submit(state, fresh, dec.SELECT, "CND-B")
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.SELECTION_NO_LONGER_ELIGIBLE, out.status)
        self.assertNoCommitment(state, out)

    def test_E41_a_high_concern_does_not_block_an_eligible_selection(self):
        """Importance says how much attention a concern deserves, not how much
        authority it has. A screen that gated on HIGH would let a model veto."""
        state = self.reviewable(advisory=review(concerns=[
            concern("CND-B", "a serious worry", importance="HIGH",
                    evidence_status="PLAUSIBLE_NOT_ESTABLISHED")]))
        out = self.decide(state, "CND-B", "we understand the worry")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.assertEqual("CND-B", self.committed_decision(state)["selected_candidate"])


# =====================================================================
# E42-E44 - a provider failure is not a decision failure
# =====================================================================
class TestAdvisoryOptional(_Decision):

    def unreviewed(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(None, state=state, provider=_Failing())
        self.assertIsNone(out.patch)
        return state

    def test_E42_a_failed_provider_does_not_stop_a_human_selecting(self):
        state = self.unreviewed()
        out = self.decide(state, "CND-A", "we can decide without a review")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        decision = self.committed_decision(state)
        self.assertEqual([], decision["considered_advisories"])
        self.assertEqual([], decision["considered_concerns"])

    def test_E43_an_advisory_that_raised_no_concern_stops_nothing(self):
        state = self.reviewable(advisory=review(reasoning="nothing to add"))
        self.assertEqual([], state.family("SelectionConcern"))
        out = self.decide(state, "CND-A")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.assertEqual([a["entity_id"] for a in state.standing("SelectionAdvisory")],
                         self.committed_decision(state)["considered_advisories"])

    def test_E44_absence_is_shown_as_absence(self):
        """Not filled in, not defaulted, and not silently omitted - a person has
        to be able to tell "no reviewer said anything" from "no reviewer ran"."""
        snapshot = self.review_of(self.unreviewed())
        text = "\n".join(ui.review_lines(snapshot))
        self.assertIn(ui.ADVISORY_ABSENT, text)
        self.assertIn(ui.CONCERNS_ABSENT, text)
        self.assertNotIn("PREFER_CANDIDATE", text)
        self.assertEqual((), snapshot.advisories)


# =====================================================================
# E45-E48 - declining to commit is an answer
# =====================================================================
class TestNonSelectActions(_Decision):

    def test_E45_keep_unresolved_records_the_action_and_commits_nothing(self):
        state = self.reviewable()
        out = self.decide(state, None, "we want to see a prototype first",
                          action=dec.KEEP_UNRESOLVED)
        self.assertEqual(dec.HUMAN_KEPT_UNRESOLVED, out.status)
        self.assertNoCommitment(state, out)
        record = state.standing("HumanDecisionInput")[0]
        self.assertEqual(dec.KEEP_UNRESOLVED, record["action"])
        self.assertNotIn("selected_candidate", record)

    def test_E46_request_more_evidence_records_the_action_and_commits_nothing(self):
        state = self.reviewable()
        out = self.decide(state, None, "measure the package volume first",
                          action=dec.REQUEST_MORE_EVIDENCE)
        self.assertEqual(dec.MORE_EVIDENCE_REQUESTED, out.status)
        self.assertNoCommitment(state, out)
        self.assertEqual(dec.REQUEST_MORE_EVIDENCE,
                         state.standing("HumanDecisionInput")[0]["action"])

    def test_E47_no_open_item_evidence_is_fabricated(self):
        """UnresolvedDecision REQUIRES `kept_open_by` to cite the Ambiguity or
        Freedom entities keeping the item open. A person declining to commit
        creates no such entity, and manufacturing one to satisfy a generic schema
        would invent the typed evidence the family exists to carry."""
        state = self.reviewable()
        for action in (dec.KEEP_UNRESOLVED, dec.REQUEST_MORE_EVIDENCE):
            self.decide(state, None, "a reason for %s" % action, action=action)
        self.assertEqual([], state.family("UnresolvedDecision"))
        self.assertEqual([], state.family("Ambiguity"))
        self.assertEqual([], state.family("Freedom"))
        source = _source("assy_v3", "stages", "selection_decision.py")
        for fabricated in ("UnresolvedDecision", "kept_open_by", "Ambiguity",
                           "Freedom"):
            self.assertNotIn('"%s"' % fabricated, source)

    def test_E48_a_non_select_action_is_not_a_failure(self):
        state = self.reviewable()
        for action in (dec.KEEP_UNRESOLVED, dec.REQUEST_MORE_EVIDENCE):
            out = self.decide(state, None, "a reason for %s" % action,
                              action=action)
            self.assertTrue(out.accepted, out.status)
            self.assertFalse(out.committed)
            self.assertEqual([], out.problems)

    def test_E48b_a_non_select_action_still_needs_a_current_review(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.KEEP_UNRESOLVED, None)
        self.profile(state, self.OTHER)
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)


# =====================================================================
# E49-E56 - what the commitment records
# =====================================================================
class TestSelectionDecision(_Decision):

    def committed(self, candidate="CND-B", advisory=None, **kw):
        state = self.reviewable(advisory=advisory, **kw)
        out = self.decide(state, candidate, "a recorded human reason")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        return state, out

    def test_E49_an_accepted_select_writes_exactly_one_decision(self):
        state, out = self.committed()
        self.assertEqual(1, len(state.family("SelectionDecision")))
        self.assertEqual(1, len(out.patch.operations))
        self.assertEqual("selection", out.patch.stage_id)
        self.assertEqual("SelectionDecision", out.patch.operations[0].entity_type)

    def test_E50_the_selected_candidate_is_the_human_s(self):
        state, _out = self.committed(candidate="CND-B")
        decision = self.committed_decision(state)
        human = state.standing("HumanDecisionInput")[0]
        self.assertEqual(human["selected_candidate"], decision["selected_candidate"])
        self.assertEqual("CND-B", decision["selected_candidate"])
        self.assertEqual(["CND-A"],
                         state.standing("CandidateComparison")[0]["frontier"])

    def test_E51_the_eligible_set_is_the_current_one(self):
        state, out = self.committed()
        decision = self.committed_decision(state)
        self.assertEqual(list(out.snapshot.eligible_candidates),
                         decision["eligible_candidates"])
        self.assertEqual(["CND-A", "CND-B"], decision["eligible_candidates"])

    def test_E52_the_evidence_fields_are_the_records_eligibility_was_read_from(self):
        state = self.reviewable()
        constraint = self.blocking(state, {"CND-A": sel.SATISFIED,
                                           "CND-B": sel.SATISFIED})
        self.compare(state)
        out = self.decide(state, "CND-A", "a reason")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        decision = self.committed_decision(state)
        self.assertEqual(["MFA-CND-A", "MFA-CND-B"],
                         sorted(decision["feasibility_assessments"]))
        self.assertEqual(["HRC-CND-A-%s" % constraint, "HRC-CND-B-%s" % constraint],
                         sorted(decision["hard_requirement_results"]))
        self.assertEqual(state.standing("SelectionProfile")[0]["entity_id"],
                         decision["selection_profile"])
        self.assertEqual(state.standing("CandidateComparison")[0]["entity_id"],
                         decision["comparison"])
        self.assertEqual(state.standing("HumanDecisionInput")[0]["entity_id"],
                         decision["human_decision"])

    def test_E52b_no_compliance_is_fabricated_where_no_requirement_exists(self):
        state, _out = self.committed()
        self.assertEqual([], self.committed_decision(state)["hard_requirement_results"])
        self.assertEqual([], state.family("HardRequirementCompliance"))

    def test_E53_considered_material_is_exactly_what_was_reviewed(self):
        state, _out = self.committed(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A",
            concerns=[concern("CND-B", "a concern")]))
        decision = self.committed_decision(state)
        human = state.standing("HumanDecisionInput")[0]
        self.assertEqual(sorted(human["reviewed_advisories"]),
                         decision["considered_advisories"])
        self.assertEqual(sorted(human["reviewed_concerns"]),
                         decision["considered_concerns"])
        self.assertEqual(1, len(decision["considered_advisories"]))
        self.assertEqual(1, len(decision["considered_concerns"]))

    def test_E54_the_rationale_is_the_person_s_words(self):
        state = self.reviewable()
        typed = "  B is easier to make, and we own the tooling  "
        out = self.decide(state, "CND-B", typed)
        self.assertEqual(dec.SELECTION_COMMITTED, out.status)
        # The documented trim: surrounding whitespace is not content. Nothing
        # inside the sentence is touched, and nothing is reworded.
        self.assertEqual(typed.strip(), self.committed_decision(state)["rationale"])
        self.assertEqual(typed.strip(),
                         state.standing("HumanDecisionInput")[0]["rationale"])

    def test_E55_replaying_an_accepted_submission_changes_nothing(self):
        state, first = self.committed()
        before = self.committed_decision(state)
        again = self.commit(state, state.standing("HumanDecisionInput")[0]["entity_id"])
        self.assertEqual(dec.SELECTION_UNCHANGED, again.status)
        self.assertTrue(again.committed)
        self.assertIsNone(again.patch)
        self.assertEqual(first.decision_id, again.decision_id)
        self.assertEqual(1, len(state.family("SelectionDecision")))
        self.assertEqual(before, self.committed_decision(state))

    def test_E56_a_standing_decision_is_not_replaced(self):
        """Reopening a commitment is lifecycle work with its own rules. Doing it
        here would be that work done without any of them."""
        state, first = self.committed(candidate="CND-A")
        standing = self.committed_decision(state)
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.SELECT, "CND-B",
                                "actually, B")
        self.assertTrue(submitted.ok, submitted.problems)
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.DECISION_ALREADY_STANDING, out.status)
        self.assertIsNone(out.patch)
        self.assertEqual(standing, self.committed_decision(state))
        self.assertEqual(1, len(state.family("SelectionDecision")))

    def test_E56b_a_later_keep_unresolved_does_not_uncommit(self):
        state, _first = self.committed(candidate="CND-A")
        standing = self.committed_decision(state)
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.KEEP_UNRESOLVED, None,
                                "let us reopen this")
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.DECISION_ALREADY_STANDING, out.status)
        self.assertEqual(standing, self.committed_decision(state))
        self.assertEqual("STANDING",
                         state.entities[standing["entity_id"]]["_validity"])

    def test_E56c_the_identity_is_content_derived(self):
        state, out = self.committed()
        decision = self.committed_decision(state)
        human = state.standing("HumanDecisionInput")[0]
        self.assertEqual(
            decision["entity_id"],
            dec.decision_identity(human, decision["selected_candidate"],
                                  decision["comparison"],
                                  decision["selection_profile"],
                                  out.snapshot.basis_refs()))
        source = inspect.getsource(dec)
        for forbidden in ("uuid", "time.time", "datetime", "random"):
            self.assertNotIn(forbidden, source)


# =====================================================================
# E57-E65 - what a commitment depends on, and what it does not
# =====================================================================
class TestDependency(_Decision):

    def committed(self, advisory=None, candidate="CND-A"):
        state = self.reviewable(advisory=advisory)
        out = self.decide(state, candidate, "a recorded human reason")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        return state, self.committed_decision(state)["entity_id"]

    def validity(self, state, eid):
        return state.entities[eid]["_validity"]

    def test_E57_a_revised_feasibility_assessment_stales_the_decision(self):
        state, decision = self.committed()
        self.invalidate(state, "MFA-CND-A", stage="feasibility")
        self.assertEqual("STALE", self.validity(state, decision))

    def test_E58_a_revised_hard_requirement_result_stales_the_decision(self):
        state = self.reviewable()
        constraint = self.blocking(state, {"CND-A": sel.SATISFIED,
                                           "CND-B": sel.SATISFIED})
        self.compare(state)
        out = self.decide(state, "CND-A", "a reason")
        decision = self.committed_decision(state)["entity_id"]
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        self.invalidate(state, "HRC-CND-A-%s" % constraint, stage="feasibility")
        self.assertEqual("STALE", self.validity(state, decision))

    def test_E59_a_revised_profile_stales_the_decision(self):
        state, decision = self.committed()
        self.profile(state, self.OTHER)
        self.assertEqual("STALE", self.validity(state, decision))

    def test_E60_a_revised_comparison_stales_the_decision(self):
        state, decision = self.committed()
        self.invalidate(state, state.standing("CandidateComparison")[0]["entity_id"])
        self.assertEqual("STALE", self.validity(state, decision))

    def test_E61_invalidating_the_human_input_stales_the_decision(self):
        state, decision = self.committed()
        self.invalidate(state, state.standing("HumanDecisionInput")[0]["entity_id"],
                        why="the submission was withdrawn")
        self.assertEqual("STALE", self.validity(state, decision))

    def test_E62_a_reworded_advisory_leaves_the_decision_standing(self):
        """The distinction the whole design turns on. Before submission the
        wording is inside the digest; after commitment it is outside the premise
        set, because the sentence was never what made the candidate choosable."""
        state, decision = self.committed(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A"))
        self.invalidate(state, state.standing("SelectionAdvisory")[0]["entity_id"],
                        why="the reviewer reworded it")
        self.assertEqual("STANDING", self.validity(state, decision))

    def test_E63_a_reworded_concern_leaves_the_decision_standing(self):
        state, decision = self.committed(advisory=review(
            concerns=[concern("CND-B", "the first wording")]))
        self.invalidate(state, state.standing("SelectionConcern")[0]["entity_id"],
                        why="the concern was reworded")
        self.assertEqual("STANDING", self.validity(state, decision))

    def test_E64_advisory_ids_are_never_premises(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A",
            concerns=[concern("CND-B", "a concern")]))
        out = self.decide(state, "CND-A", "a reason")
        decision = self.committed_decision(state)
        premises = set(state.entities[decision["entity_id"]]["_premises"])
        advisory_ids = {a["entity_id"] for a in state.standing("SelectionAdvisory")}
        concern_ids = {c["entity_id"] for c in state.standing("SelectionConcern")}
        self.assertTrue(advisory_ids and concern_ids)
        self.assertEqual(set(), premises & (advisory_ids | concern_ids))
        self.assertEqual(set(), set(out.patch.operations[0].premise_refs)
                         & (advisory_ids | concern_ids))
        self.assertTrue(advisory_ids <= set(decision["considered_advisories"]))
        self.assertTrue(concern_ids <= set(decision["considered_concerns"]))

    def test_E65_the_premise_set_is_the_basis_and_nothing_else(self):
        """Not the view, not the design. A decision premised on everything it
        could see would go stale on every write anywhere and mean nothing."""
        state = self.reviewable(advisory=review(
            concerns=[concern("CND-B", "a concern")]))
        out = self.decide(state, "CND-A", "a reason")
        premises = set(out.patch.operations[0].premise_refs)
        expected = set(out.snapshot.basis_refs()) | {
            state.standing("HumanDecisionInput")[0]["entity_id"],
            out.snapshot.comparison["entity_id"],
            out.snapshot.profile["entity_id"]}
        self.assertEqual(expected, premises)
        families = {state.stored_family(p) for p in premises}
        self.assertEqual({"Candidate", "MechanicalFeasibilityAssessment",
                          "CandidateComparison", "SelectionProfile",
                          "HumanDecisionInput"}, families)
        self.assertLess(len(premises), len(state.entities) / 2)

    def test_E61b_a_human_input_does_not_go_stale_with_the_design(self):
        """It is a historical fact about a person, not a conclusion about the
        design - and a submission that went stale with the comparison could not
        be found afterwards to be refused."""
        state = self.reviewable()
        submitted = self.submit(state, self.review_of(state), dec.SELECT, "CND-A")
        self.profile(state, self.OTHER)
        record = state.entities[submitted.input_id]
        self.assertEqual("STANDING", record["_validity"])
        self.assertEqual([], record.get("_premises", []))
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)


# =====================================================================
# E66-E72 - the screen
# =====================================================================
class TestCheckpointScreen(_Decision):

    def shown(self, state, **kw):
        surface = _Surface(**kw)
        outcome = ui.checkpoint(surface, state)
        return surface, outcome

    def test_E66_the_screen_renders_the_snapshot_and_nothing_else(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A",
            concerns=[concern("CND-B", "a concern", importance="HIGH")]))
        snapshot = self.review_of(state)
        surface, _out = self.shown(state)
        self.assertEqual(ui.review_lines(snapshot), surface.lines)
        self.assertEqual(["snapshot"],
                         list(inspect.signature(ui.render_review).parameters)[1:])
        text = surface.text()
        for shown in (snapshot.comparison["entity_id"], snapshot.profile["entity_id"],
                      "CND-A", "CND-B", "prefer A", "a concern", "HIGH"):
            self.assertIn(shown, text)

    def test_E66b_the_screen_never_reads_state_while_rendering(self):
        """Structural, not a convention: the rendering functions have no state
        parameter and reach for no state method, so there is nowhere for a second
        moment of the design to enter the screen."""
        tree = ast.parse(_source("assy_v3", "ui", "selection_checkpoint.py"))
        rendering = {"review_lines", "comparison_rows", "profile_rows",
                     "candidate_options", "render_review", "render_controls",
                     "_metric_cell"}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name in rendering):
                continue
            self.assertNotIn("state", [a.arg for a in node.args.args], node.name)
            for inner in ast.walk(node):
                if isinstance(inner, ast.Name):
                    self.assertNotEqual("state", inner.id, node.name)
                if isinstance(inner, ast.Attribute):
                    self.assertNotIn(inner.attr,
                                     ("standing", "family", "entities", "apply",
                                      "validate"), node.name)

    def test_E67_no_screen_may_author_a_commitment(self):
        for module in (("assy_v3", "ui", "selection_checkpoint.py"),
                       ("tools", "selection_checkpoint.py")):
            source = _code(_source(*module))
            for forbidden in ("SelectionDecision", "CandidateComparison",
                              "SelectionProfile", "SelectionAdvisory",
                              "SelectionConcern",
                              "MechanicalFeasibilityAssessment",
                              "HardRequirementCompliance", "Op(", "StagePatch("):
                self.assertNotIn(forbidden, source, "%s in %s" % (forbidden, module))
        self.assertNotIn("apply", _code(_source("tools", "selection_checkpoint.py")))

    def test_E68_no_candidate_is_preselected(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        options = ui.candidate_options(snapshot)
        self.assertEqual(ui.CHOOSE_PLACEHOLDER, options[0])
        self.assertNotIn(ui.CHOOSE_PLACEHOLDER, snapshot.comparison["candidates"])
        surface, _out = self.shown(state)
        chooser = [c for c in surface.controls if c["kind"] == "selectbox"][0]
        self.assertEqual(0, chooser["index"])
        self.assertEqual(ui.CHOOSE_PLACEHOLDER, chooser["options"][0])
        # And pressing submit on the placeholder decides nothing.
        surface, out = self.shown(state, action=dec.SELECT, submitted=True)
        self.assertEqual(ui.NO_CHOICE_MADE, out.status)
        self.assertEqual([], state.family("HumanDecisionInput"))
        self.assertEqual([], state.family("SelectionDecision"))

    def test_E68b_the_frontier_is_not_relabelled_as_a_winner(self):
        state = self.reviewable()
        surface, _out = self.shown(state)
        text = surface.text().lower()
        for verdict in ("winner", "best", "recommended choice", "selected candidate"):
            self.assertNotIn(verdict, text)
        self.assertIn("frontier", text)

    def test_E69_a_stale_screen_asks_for_a_re_review_and_retries_nothing(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        self.profile(state, self.OTHER)
        out = ui.submit(state, snapshot, dec.SELECT, "CND-A", "a reason")
        self.assertEqual(dec.STALE_SUBMISSION, out.status)
        self.assertEqual(ui.STALE_MESSAGE, out.message)
        self.assertNoCommitment(state)
        source = inspect.getsource(ui.submit)
        self.assertNotIn("build_human_review_snapshot", source,
                         "the screen rebuilt the review and submitted again")
        self.assertEqual(1, source.count("commit_human_selection("))

    def test_E70_advisory_absence_leaves_every_control_live(self):
        state, _cmp = self.compared()
        self.reviewed(None, state=state, provider=_Failing())
        surface, out = self.shown(state)
        self.assertEqual(ui.REVIEW_SHOWN, out.status)
        self.assertEqual(["radio", "selectbox", "text_area", "button"],
                         surface.kinds())
        self.assertIn(ui.ADVISORY_ABSENT, surface.text())
        # and a selection made without an advisory commits
        surface, out = self.shown(state, action=dec.SELECT, candidate="CND-A",
                                  rationale="no reviewer needed", submitted=True)
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)

    def test_E71_the_advisory_is_labelled_as_an_opinion(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A"))
        surface, _out = self.shown(state)
        text = surface.text()
        self.assertIn(ui.ADVISORY_LABEL, text)
        self.assertIn("not a decision", ui.ADVISORY_LABEL)
        self.assertIn("importance is not authority", text)
        self.assertLess(text.index(ui.ADVISORY_LABEL), text.index("prefer A"))

    def test_E72_all_three_actions_are_offered(self):
        state = self.reviewable()
        surface, _out = self.shown(state)
        chooser = [c for c in surface.controls if c["kind"] == "radio"][0]
        self.assertEqual(list(dec.ACTIONS), chooser["options"])
        for action, expected in ((dec.KEEP_UNRESOLVED, dec.HUMAN_KEPT_UNRESOLVED),
                                 (dec.REQUEST_MORE_EVIDENCE,
                                  dec.MORE_EVIDENCE_REQUESTED)):
            _s, out = self.shown(state, action=action, rationale="a reason",
                                 submitted=True)
            self.assertEqual(expected, out.status)
        self.assertEqual([], state.family("SelectionDecision"))

    def test_E72b_no_review_means_no_controls(self):
        state = self.built()
        surface, out = self.shown(state)
        self.assertEqual(ui.NOTHING_TO_REVIEW, out.status)
        self.assertEqual([], surface.controls)
        self.assertEqual("warning", surface.said[0][0])


# =====================================================================
# E73-E78 - the runner, and the edges of this step
# =====================================================================
class TestRunnerAndScope(_Decision):

    def test_E73_the_batch_runner_records_that_it_is_waiting(self):
        state = self.reviewable()
        rec = run_window2.run_selection_checkpoint("probe", state, 1)
        self.assertEqual(run_window2.AWAITING_HUMAN_DECISION,
                         rec["checkpoint_status"])
        self.assertEqual(self.review_of(state).digest, rec["premise_digest"])
        self.assertEqual([], state.family("HumanDecisionInput"))
        self.assertEqual([], rec["failures"])

    def test_E74_the_batch_runner_commits_nothing(self):
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A"))
        before = {eid: dict(state.entities[eid]) for eid in state.entities}
        run_window2.run_selection_checkpoint("probe", state, 1)
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual(before, {eid: dict(state.entities[eid])
                                  for eid in state.entities})

    def test_E75_the_runner_cannot_choose(self):
        """RESTATED AT S7-F. The runner must now say whether the decision it
        reports is the CURRENT commitment or history, so the family name alone
        stopped being the right thing to forbid - a read is how it tells the
        truth about currentness, and refusing to look was how it could have
        reported a stale decision as a settled design.

        What is forbidden is AUTHORING. Every mention of the family in the runner
        is an argument to a state READ, asserted by AST rather than by spelling."""
        source = _source("tools", "run_window2.py")
        for fabrication in ("materialize_human_decision_input",
                            "commit_human_selection", "HumanDecisionInput",
                            "frontier[0]", "candidates[0]",
                            "recommended_candidate"):
            self.assertNotIn(fabrication, source)
        tree = ast.parse(source)
        reads = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in ("family", "standing"):
                for arg in node.args:
                    if isinstance(arg, ast.Str):
                        reads.add((id(node), arg.s))
        mentions = [n for n in ast.walk(tree)
                    if isinstance(n, ast.Str) and n.s == "SelectionDecision"]
        self.assertTrue(mentions)
        self.assertEqual(len(mentions),
                         len([r for r in reads if r[1] == "SelectionDecision"]),
                         "the runner names SelectionDecision somewhere that is "
                         "not a read of current state")
        for op in ("Op(", "StagePatch("):
            self.assertNotIn(op, inspect.getsource(
                run_window2.run_selection_checkpoint))
        checkpoint = inspect.getsource(run_window2.run_selection_checkpoint)
        self.assertNotIn("apply", checkpoint)
        self.assertNotIn("Op(", checkpoint)

    def test_E75b_nothing_reaches_a_selected_candidate_without_a_human(self):
        """The audit in one assertion: every path that sets `selected_candidate`
        reads it from the human input."""
        tree = ast.parse(_source("assy_v3", "stages", "selection_decision.py"))
        assignments = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Str) and key.s == "selected_candidate":
                        assignments.append(ast.dump(value))
        self.assertTrue(assignments)
        for value in assignments:
            self.assertIn("candidate", value)
        source = _source("assy_v3", "stages", "selection_decision.py")
        for auto in ("frontier[0]", "candidates[0]", "eligible[0]",
                     "recommended_candidate", "SOLE_ELIGIBLE",
                     "DOMINANT_UNDER_PROFILE"):
            self.assertNotIn(auto, source)

    def test_E76_no_provider_is_reachable_from_this_step(self):
        """No model is asked anything here. The word `provider` survives in
        exactly two places - the provenance of the two patches, saying that a
        human and a deterministic function produced them."""
        source = _source("assy_v3", "stages", "selection_decision.py")
        code = _code(source)
        # `execution_status` is not on this list: it is an ordinary StagePatch
        # field that every deterministic writer sets, and a patch saying SUCCESS
        # is not evidence that anything was generated.
        for llm in ("PROMPT", "generate(", "invoke(", "raw_text", "GenerationRe",
                    "Stage)", "attempt_index", "finish_reason"):
            self.assertNotIn(llm, code)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("provider", node.module or "")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("provider", alias.name)
        self.assertEqual(['"provider": "human"', '"provider": "deterministic"'],
                         [m.group(0) for m in
                          __import__("re").finditer(r'"provider": "\w+"', code)])

    def test_E77_propagation_is_untouched(self):
        """S7-E adds no propagation rule and no exception to one. What stales a
        decision is which ids it recorded as premises, which is ordinary."""
        source = inspect.getsource(ds._propagate)
        for special_case in ("Selection", "Advisory", "Human", "Concern",
                             "considered"):
            self.assertNotIn(special_case, source)
        self.assertEqual(1, source.count('rec["_validity"] = ValidityStatus.STALE.value'))

    def test_E78_the_frozen_producers_are_untouched(self):
        """S7-B, S7-C and S7-D semantics run unchanged underneath: the whole
        deterministic record is asserted entity for entity across a full human
        decision."""
        state = self.reviewable(advisory=review(
            kind="PREFER_CANDIDATE", candidate="CND-A", reasoning="prefer A",
            concerns=[concern("CND-B", "a concern")]))
        before = self.snapshot(state)
        before.update({a["entity_id"]: json.dumps(
            {k: v for k, v in a.items() if not k.startswith("_")}, sort_keys=True)
            for a in state.standing("SelectionAdvisory")})
        out = self.decide(state, "CND-B", "a reason")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        after = self.snapshot(state)
        after.update({a["entity_id"]: json.dumps(
            {k: v for k, v in a.items() if not k.startswith("_")}, sort_keys=True)
            for a in state.standing("SelectionAdvisory")})
        self.assertEqual(before, after)
        written = {op.entity_type for op in out.patch.operations}
        self.assertEqual({"SelectionDecision"}, written)

    def test_E78b_this_step_writes_exactly_two_families(self):
        source = _source("assy_v3", "stages", "selection_decision.py")
        tree = ast.parse(source)
        created = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Op":
                created.add(node.args[1].s)
        self.assertEqual({"HumanDecisionInput", "SelectionDecision"}, created)


# =====================================================================
# The contracts describe what runs
# =====================================================================
class TestContractTruth(_Decision):

    @classmethod
    def setUpClass(cls):
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.ds = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.audit = _paths.contract("ENTITY_FAMILY_AUDIT.yaml")

    def test_E79_both_passes_are_declared_under_the_selection_owner(self):
        for pass_id in (dec.REVIEW_PASS, dec.DECISION_PASS):
            entry = self.resp["stages"][pass_id]
            self.assertEqual("selection", entry["authority_stage"])
            self.assertTrue(entry["required_reasoning_premise_classes"])
        self.assertEqual(["HumanDecisionInput"],
                         self.resp["stages"][dec.REVIEW_PASS]
                         ["permitted_output_semantics"])
        self.assertEqual(["SelectionDecision"],
                         self.resp["stages"][dec.DECISION_PASS]
                         ["permitted_output_semantics"])

    def test_E80_the_existing_selection_passes_stayed_out_of_it(self):
        """C would be circular if `selection` required the entity it creates, and
        D's provider context is frozen."""
        for pass_id in ("selection", "selection_advisory"):
            declared = {p["class"] for p in
                        self.resp["stages"][pass_id]
                        ["required_reasoning_premise_classes"]}
            self.assertNotIn("human_decision", declared)
            roles = {r for p in self.resp["stages"][pass_id]
                     ["required_reasoning_premise_classes"]
                     for r in p["requires_semantics"]}
            self.assertNotIn("human_decision", roles)
            self.assertNotIn("selection_decision", roles)
        self.assertNotIn("selection_evidence",
                         {r for p in self.resp["stages"]["selection"]
                          ["required_reasoning_premise_classes"]
                          for r in p["requires_semantics"]})

    def test_E81_the_advisory_is_admitted_and_never_required(self):
        material = [p for p in self.resp["stages"][dec.REVIEW_PASS]
                    ["required_reasoning_premise_classes"]
                    if "advisory" in p["requires_semantics"]]
        self.assertEqual(1, len(material))
        self.assertEqual("MAY_BE_EMPTY",
                         material[0]["instance_selection"]["existence"])

    def test_E82_the_unresolved_decision_distinction_is_recorded(self):
        rules = " ".join(self.ds["assurance_families"]["SelectionDecision"]["rules"])
        self.assertIn("TRADEOFF_UNRESOLVED", rules)
        self.assertIn("KEEP_UNRESOLVED", rules)
        self.assertIn("kept_open_by", rules)
        self.assertNotIn("an undiscriminated tie is an UnresolvedDecision instead",
                         rules)
        required = self.ds["entity_families"]["UnresolvedDecision"]["required_fields"]
        self.assertIn("kept_open_by", required)

    def test_E83_both_producers_are_recorded_as_live(self):
        for family in ("HumanDecisionInput", "SelectionDecision"):
            row = self.audit["families"][family]
            self.assertEqual("selection", row["owning_stage"])
            self.assertEqual("CORE", row["status"])

    def test_E84_the_retired_s04b_dependency_stays_retired(self):
        s04b = self.resp["stages"]["s04b"]
        for premise in s04b["required_reasoning_premise_classes"]:
            rule = premise["instance_selection"]
            populations = ([r["population"] for r in rule["by_role"]]
                           if rule.get("by_role") else [rule["population"]])
            self.assertNotIn("COMMITTED_BRANCH", populations)
            self.assertNotIn("selection_decision", premise["requires_semantics"])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
