"""S7-D: a reviewer that can say anything and decide nothing.

The first model call after the deterministic substrate. Every probe below runs
the real chain - s01 through feasibility through the deterministic comparison -
and then the real Stage invocation boundary with a canned or failing provider, so
what is exercised is the production path and not a helper.

WHAT THESE TESTS ARE GUARDING

    The model cannot reach eligibility. Not because the prompt asks it not to -
    a prompt is a request - but because the population it may speak about is
    copied from the comparison, a response naming anything else is discarded
    whole, and the eligible set is asserted entity-for-entity before and after.

    A concern may be important and unestablished at the same time. That is the
    point of the evidence vocabulary, and it is why an overclaim is DOWNGRADED
    rather than rejected: losing the concern would lose the engineering, and
    keeping the claim would launder judgement into evidence.

    A citation the reviewer could not have seen never enters state. A fabricated
    id resolves to nothing and would make invention look like provenance.

    What the review depends on is what the model was SHOWN, not what it chose to
    cite. Those answer two different questions and only one of them is about
    currentness.

Synthetic mechanisms only - the hinge and the four-bar the earlier suites probe
with. No product noun, no benchmark id.
"""
from __future__ import annotations

import ast
import json
import time
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.selection_advisory as adv                   # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                    # noqa: E402
from ver3.tools import run_window2                                     # noqa: E402
from .test_s02_s03b_integration import _Canned                         # noqa: E402
from .test_s7_selection import (                                       # noqa: E402
    HIGH, MEDIUM, LOW, MINIMIZE, MAXIMIZE, _Selection, prefs)


class _Failing:
    """A provider that never succeeds, and records that it was asked."""

    def __init__(self, status=ExecutionStatus.PROVIDER_TIMEOUT, raw=None,
                 truncated=False):
        self.status, self.raw, self.truncated, self.calls = status, raw, truncated, 0

    def capabilities(self):
        return _Canned().capabilities()

    def generate(self, request, attempt_index=0):
        from ver3.assy_v3.providers.interfaces import (GenerationResponse,
                                                        GenerationResult)
        self.calls += 1
        if self.raw is None:
            return GenerationResult(execution_status=self.status, response=None,
                                    attempt_index=attempt_index,
                                    started_at=time.time(), ended_at=time.time(),
                                    error_detail="probe", from_cache=True)
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=self.raw, finish_reason="stop",
                                        truncated=self.truncated,
                                        input_tokens=None, output_tokens=None,
                                        served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=True)


def review(kind="NO_CLEAR_PREFERENCE", candidate=None, reasoning="a review",
           concerns=(), **extra):
    """A model response of the shape the pass asks for."""
    out = {"recommendation": {"kind": kind, "candidate": candidate},
           "reasoning": reasoning, "concerns": list(concerns)}
    out.update(extra)
    return out


def concern(candidate, issue="a concern", importance="MEDIUM",
            evidence_status="PLAUSIBLE_NOT_ESTABLISHED", refs=(), **extra):
    out = {"candidate": candidate, "issue": issue, "importance": importance,
           "evidence_status": evidence_status, "supporting_refs": list(refs)}
    out.update(extra)
    return out


class _Advisory(_Selection):
    """A design with a current comparison, ready to be reviewed."""

    PREFS = prefs(joint_count=(MINIMIZE, HIGH))

    def compared(self, candidates=("A", "B"), preferences=None, state=None):
        state = state if state is not None else self.built(candidates)
        out = self.compare(state, preferences if preferences is not None
                           else self.PREFS)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.status, out.problems)
        return state, out

    def reviewed(self, response, state=None, provider=None, **kw):
        """The real Stage boundary. Returns (state, outcome, provider)."""
        if state is None:
            state, _cmp = self.compared(**kw)
        provider = provider or _Canned(response)
        out = adv.SelectionEngineeringReview().invoke(provider, state,
                                                      state.run_id)
        if out.patch is not None and not out.problems:
            state.apply(out.patch)
        return state, out, provider

    def advisory_of(self, state):
        found = state.family("SelectionAdvisory")
        self.assertEqual(1, len(found), found)
        return found[0]

    def snapshot(self, state):
        """Every deterministic record, with its validity - so "the advisory
        changed nothing" can be asserted entity for entity."""
        return {eid: (json.dumps({k: v for k, v in e.items()
                                  if not k.startswith("_")}, sort_keys=True),
                      e.get("_validity"))
                for eid, e in ((i, state.entities[i]) for i in state.entities)
                if e.get("_family") in ("MechanicalFeasibilityAssessment",
                                        "HardRequirementCompliance",
                                        "FeasibilityDomainAssessment",
                                        "CandidateComparison", "SelectionProfile")}


# =====================================================================
# D01-D05 - the review happens after the comparison, or not at all
# =====================================================================
class TestSequencing(_Advisory):

    def test_D01_no_comparison_means_no_provider_call(self):
        """A reviewer's opinion about a population nobody established is not a
        review. The Stage boundary refuses the unready view before the provider
        is reached, so the model is never asked."""
        state = self.built()
        self.assertEqual([], state.family("CandidateComparison"))
        provider = _Canned(review())
        out = adv.SelectionEngineeringReview().invoke(provider, state, state.run_id)
        self.assertEqual(0, provider.calls, "the provider was called anyway")
        self.assertEqual(ExecutionStatus.CONSUMER_CONTEXT_INSUFFICIENT,
                         out.execution_status)
        self.assertIsNone(out.patch)
        self.assertEqual([], state.family("SelectionAdvisory"))

    def test_D02_one_current_comparison_makes_the_context_ready(self):
        state, _cmp = self.compared()
        view = adv.SelectionEngineeringReview().consumer_view(state)
        self.assertEqual("VIEW_READY", view.status.value,
                         [a for a in view.assessment if a["verdict"] != "SATISFIED"])

    def test_D03_two_current_comparisons_are_ambiguity_not_a_choice(self):
        state, _cmp = self.compared()
        self.revise(state, Op("CREATE", "CandidateComparison", "CCP-SECOND",
                              {"candidates": ["CND-A"], "profile": state.standing(
                                  "SelectionProfile")[0]["entity_id"],
                               "metrics": {}, "outcome": "SOLE_ELIGIBLE",
                               "frontier": ["CND-A"]}, "t"), stage="selection")
        provider = _Canned(review())
        rec = run_window2.run_selection_advisory("SYN", state, provider, 1)
        self.assertEqual(0, provider.calls)
        self.assertEqual(adv.COMPARISON_AMBIGUOUS, rec["advisory_status"])
        self.assertEqual([], state.family("SelectionAdvisory"))

    def test_D04_the_profile_and_the_comparison_both_reach_the_reviewer(self):
        state, cmp_ = self.compared()
        payload = adv.SelectionEngineeringReview().consumer_view(state).payload()
        self.assertEqual(1, len(payload["CandidateComparison"]))
        self.assertEqual(1, len(payload["SelectionProfile"]))
        prompt = adv.SelectionEngineeringReview().prompt(
            {"consumer_view": payload})
        self.assertIn(cmp_.patch.operations[0].entity_id, prompt)
        self.assertIn("joint_count", prompt, "the stated profile is not shown")
        self.assertIn("CND-A", prompt)

    def test_D05_the_comparison_must_be_applied_first(self):
        """Computed and not applied is not current. A review of a record the
        design does not hold is a review of nothing."""
        state = self.built()
        self.profile(state, self.PREFS)
        out = sel.evaluate_candidate_comparison(state)
        self.assertIsNotNone(out.patch)                       # computed
        provider = _Canned(review())
        blocked = adv.SelectionEngineeringReview().invoke(provider, state,
                                                          state.run_id)
        self.assertEqual(0, provider.calls)
        state.apply(out.patch)                                # applied
        _s, ready, called = self.reviewed(review(), state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, ready.execution_status)
        self.assertEqual(1, called.calls)


# =====================================================================
# D06-D10 - the population is the comparison's, not the model's
# =====================================================================
class TestPopulationAuthority(_Advisory):

    def test_D06_the_advisory_population_is_copied_from_the_comparison(self):
        state, cmp_ = self.compared()
        state, _out, _p = self.reviewed(review(), state=state)
        advisory = self.advisory_of(state)
        self.assertEqual(sorted(cmp_.eligible), sorted(advisory["candidates"]))
        self.assertEqual(cmp_.patch.operations[0].entity_id, advisory["comparison"])
        # AND THE MODEL WAS NEVER ASKED FOR IT. A response key it may not author
        # is refused, so it cannot supply one even by trying.
        self.assertNotIn("candidates", adv.RESPONSE_KEYS)

    def test_D07_recommending_a_candidate_outside_the_population_is_refused(self):
        """Not trimmed. Trimming would silently answer a different question than
        the one the reviewer asked."""
        state, _cmp = self.compared()
        for outsider in ("CND-C", "CND-NOWHERE"):
            _s, out, _p = self.reviewed(
                review("PREFER_CANDIDATE", outsider), state=state)
            self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)
            self.assertIsNone(out.patch)
            self.assertEqual([], state.family("SelectionAdvisory"))

    def test_D08_a_concern_about_a_candidate_outside_the_population_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(
            review(concerns=[concern("CND-A"), concern("CND-EXCLUDED")]),
            state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)
        self.assertEqual([], state.family("SelectionConcern"),
                         "the valid concern was kept and the response was wrong")

    def test_D09_D10_nothing_the_reviewer_says_moves_the_population(self):
        """Five candidates, three of them excluded upstream, and the reviewer
        given every chance: a HIGH concern, a departure from the frontier, prose
        calling one candidate unacceptable."""
        state = self.built(("A", "B", "C"))
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-C", {"status": "INFEASIBLE"}, "t",
                              reason="probe"), stage="feasibility")
        state, cmp_ = self.compared(state=state)
        self.assertEqual(["CND-A", "CND-B"], cmp_.eligible)
        before = self.snapshot(state)

        state, out, _p = self.reviewed(review(
            "PREFER_CANDIDATE", "CND-B",
            reasoning="CND-A is unacceptable and CND-C should be reconsidered",
            concerns=[concern("CND-A", "this candidate should not be chosen",
                              importance="HIGH")]), state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        self.assertEqual(before, self.snapshot(state),
                         "an advisory changed a deterministic record")
        self.assertEqual(["CND-A", "CND-B"],
                         sorted(self.advisory_of(state)["candidates"]))
        again = sel.evaluate_candidate_comparison(state)
        self.assertEqual(["CND-A", "CND-B"], again.eligible,
                         "the eligible population moved after a review")


# =====================================================================
# D11-D14 - what a response may contain
# =====================================================================
class TestResponseAuthority(_Advisory):

    def test_D11_only_advisory_and_concern_are_created(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(
            review(concerns=[concern("CND-A"), concern("CND-B")]), state=state)
        self.assertEqual({"SelectionAdvisory", "SelectionConcern"},
                         {op.entity_type for op in out.patch.operations})
        self.assertEqual({"CREATE"}, {op.kind for op in out.patch.operations})
        self.assertEqual(["SelectionAdvisory", "SelectionConcern"],
                         sorted(self.resp_outputs()))

    def resp_outputs(self):
        return _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")[
            "stages"]["selection_advisory"]["permitted_output_semantics"]

    def test_D11b_the_response_may_carry_exactly_four_keys(self):
        """The gate that makes every other refusal work. A key the model may
        author is a field it can decide; the four here are an opinion, a
        justification, a sensitivity note and a list of concerns - and not one of
        them is a structural field."""
        self.assertEqual({"recommendation", "reasoning", "sensitivity",
                          "concerns"}, set(adv.RESPONSE_KEYS))
        self.assertEqual({"candidate", "issue", "importance", "evidence_status",
                          "supporting_refs"}, set(adv.CONCERN_KEYS))
        for structural in ("candidates", "comparison", "comparison_alignment",
                           "alignment", "entity_id", "advisory",
                           "recommended_candidate", "evidence_note"):
            self.assertNotIn(structural, adv.RESPONSE_KEYS, structural)
            self.assertNotIn(structural, adv.CONCERN_KEYS, structural)

    def test_D11c_the_alignment_is_computed_from_the_comparison_alone(self):
        """It takes the comparison and the recommendation and nothing else - so
        there is no parameter through which a model's opinion about the metrics
        could reach it."""
        import inspect
        self.assertEqual(["comparison", "recommended"],
                         list(inspect.signature(adv.comparison_alignment).parameters))
        body = inspect.getsource(adv.comparison_alignment).split('"""', 2)[2]
        self.assertNotIn("parsed", body)
        self.assertIn('comparison.get("frontier")', body)

    def test_D12_D13_D14_a_response_shaped_like_an_authority_is_refused(self):
        """Every one of these is a model reaching for a verdict that is not
        its own. The whole response is discarded rather than the extra key
        dropped: a model that tried here may have tried where nothing checks."""
        state, _cmp = self.compared()
        for extra in ({"selected_candidate": "CND-A"},
                      {"eligibility": {"CND-A": "ELIGIBLE"}},
                      {"feasibility": {"CND-A": "FEASIBLE_FOR_SELECTION"}},
                      {"hard_requirement_status": {"CND-A": "SATISFIED"}},
                      {"score": {"CND-A": 0.9}},
                      {"weighted_score": 1.0},
                      {"selection_decision": "CND-A"}):
            _s, out, _p = self.reviewed(review(**extra), state=state)
            self.assertEqual(ExecutionStatus.SCHEMA_FAILURE,
                             out.execution_status, list(extra))
            self.assertIsNone(out.patch, list(extra))
        self.assertEqual([], state.family("SelectionAdvisory"))
        self.assertEqual([], state.family("SelectionDecision"))


# =====================================================================
# D15-D22 - the recommendation, and whether it agrees with the metrics
# =====================================================================
class TestRecommendation(_Advisory):

    def test_D15_a_preference_for_an_eligible_candidate_is_recorded(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(
            review("PREFER_CANDIDATE", "CND-A"), state=state)
        advisory = self.advisory_of(state)
        self.assertEqual("PREFER_CANDIDATE", advisory["recommendation"])
        self.assertEqual("CND-A", advisory["recommended_candidate"])

    def test_D16_no_clear_preference_is_a_complete_answer(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(), state=state)
        advisory = self.advisory_of(state)
        self.assertEqual("NO_CLEAR_PREFERENCE", advisory["recommendation"])
        # ABSENT, not null. A declared reference holding None is a reference to
        # nothing; the reviewer named nobody, which is a different statement.
        self.assertNotIn("recommended_candidate", advisory)

    def test_D17_a_preference_naming_nobody_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(review("PREFER_CANDIDATE", None), state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)
        self.assertIsNone(out.patch)

    def test_D18_no_preference_that_names_somebody_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(review("NO_CLEAR_PREFERENCE", "CND-A"),
                                    state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)

    def test_D18b_an_unknown_recommendation_kind_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(review("PICK_THIS_ONE", "CND-A"), state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)

    def test_D19_agreeing_with_a_frontier_of_one_aligns(self):
        state, cmp_ = self.compared()
        self.assertEqual(["CND-A"], cmp_.frontier)
        state, _out, _p = self.reviewed(review("PREFER_CANDIDATE", "CND-A"),
                                        state=state)
        self.assertEqual(adv.ALIGNS_WITH_FRONTIER,
                         self.advisory_of(state)["comparison_alignment"])

    def test_D20_preferring_the_other_eligible_candidate_departs(self):
        """LEGAL AND EXPLICIT. A reviewer may prefer a candidate the registered
        metrics do not favour - that is what a reviewer is for. What is forbidden
        is departing silently."""
        state, cmp_ = self.compared()
        state, _out, _p = self.reviewed(review("PREFER_CANDIDATE", "CND-B"),
                                        state=state)
        self.assertEqual(adv.DEPARTS_FROM_FRONTIER,
                         self.advisory_of(state)["comparison_alignment"])

    def test_D21_a_frontier_of_several_expresses_no_deterministic_preference(self):
        """Whatever the reviewer says. The metrics did not discriminate, so
        there is nothing to align with or depart from."""
        state, cmp_ = self.compared(preferences={})
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, cmp_.outcome)
        for response in (review("PREFER_CANDIDATE", "CND-A"),
                         review("PREFER_CANDIDATE", "CND-B"), review()):
            fresh, _c = self.compared(preferences={})
            fresh, _out, _p = self.reviewed(response, state=fresh)
            self.assertEqual(adv.NO_DETERMINISTIC_PREFERENCE,
                             self.advisory_of(fresh)["comparison_alignment"])

    def test_D21b_no_clear_preference_never_aligns_or_departs(self):
        state, cmp_ = self.compared()
        self.assertEqual(1, len(cmp_.frontier))
        state, _out, _p = self.reviewed(review(), state=state)
        self.assertEqual(adv.NO_DETERMINISTIC_PREFERENCE,
                         self.advisory_of(state)["comparison_alignment"])

    def test_D22_disagreement_leaves_the_comparison_exactly_as_it_was(self):
        state, cmp_ = self.compared()
        before = self.snapshot(state)
        state, _out, _p = self.reviewed(
            review("PREFER_CANDIDATE", "CND-B",
                   reasoning="the metrics are measuring the wrong thing"),
            state=state)
        self.assertEqual(before, self.snapshot(state))
        record = [c for c in state.family("CandidateComparison")][0]
        self.assertEqual(["CND-A"], record["frontier"])
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, record["outcome"])


# =====================================================================
# D23-D24 - an empty profile is not an invitation to invent one
# =====================================================================
class TestEmptyProfile(_Advisory):

    def test_D23_the_prompt_forbids_inventing_a_preference(self):
        """Structural where it can be: the profile the reviewer is shown is the
        one the user stated, and it ranks nothing. The instruction not to invent
        one is in the prompt because that part cannot be structural - what IS
        structural is that no criterion appears in the context to be read as a
        preference."""
        state, cmp_ = self.compared(preferences={})
        payload = adv.SelectionEngineeringReview().consumer_view(state).payload()
        self.assertEqual({}, payload["SelectionProfile"][0]["criteria"])
        prompt = adv.SelectionEngineeringReview().prompt({"consumer_view": payload})
        self.assertIn("Do not invent a user preference", prompt)
        for invented in ("simplicity", "compactness", "reliability"):
            self.assertNotIn(invented, prompt.split("THE PROFILE THE USER")[1])

    def test_D24_concerns_are_still_reviewable_under_an_empty_profile(self):
        state, cmp_ = self.compared(preferences={})
        state, out, _p = self.reviewed(
            review(concerns=[concern("CND-A", "a real engineering worry",
                                     importance="HIGH")]), state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        self.assertEqual(1, len(state.family("SelectionConcern")))
        self.assertEqual(adv.NO_DETERMINISTIC_PREFERENCE,
                         self.advisory_of(state)["comparison_alignment"])


# =====================================================================
# D25-D32 - how well a concern is supported, said honestly
# =====================================================================
class TestConcernEvidence(_Advisory):

    def only(self, state):
        found = state.family("SelectionConcern")
        self.assertEqual(1, len(found), found)
        return found[0]

    def test_D25_state_support_with_a_valid_current_reference_stands(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", evidence_status="SUPPORTED_BY_STATE",
                    refs=["JNT-0A", "BOD-G0A"])]), state=state)
        record = self.only(state)
        self.assertEqual("SUPPORTED_BY_STATE", record["evidence_status"])
        self.assertEqual(["BOD-G0A", "JNT-0A"], record["supporting_refs"])
        self.assertIsNone(record.get("evidence_note"))

    def test_D26_state_support_with_no_reference_is_downgraded(self):
        """DOWNGRADED, NOT LOST. The reviewer may well be right that it matters;
        what is corrected is the claim about what it rests on."""
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "durability may be sensitive",
                    evidence_status="SUPPORTED_BY_STATE", refs=[])]), state=state)
        record = self.only(state)
        self.assertEqual("PLAUSIBLE_NOT_ESTABLISHED", record["evidence_status"])
        self.assertEqual([], record["supporting_refs"])
        self.assertIn("claimed state support", record["evidence_note"])
        self.assertEqual("durability may be sensitive", record["issue"])

    def test_D27_a_fabricated_reference_never_enters_state(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "invented citation only",
                    evidence_status="SUPPORTED_BY_STATE",
                    refs=["ENT-99999", "NOT-A-REAL-ID"]),
            concern("CND-B", "one real and one invented",
                    evidence_status="SUPPORTED_BY_STATE",
                    refs=["JNT-0B", "ENT-INVENTED"])]), state=state)
        blob = json.dumps([{k: v for k, v in c.items() if not k.startswith("_")}
                           for c in state.family("SelectionConcern")])
        for fake in ("ENT-99999", "NOT-A-REAL-ID", "ENT-INVENTED"):
            self.assertNotIn(fake, blob, fake)
        by_issue = {c["issue"]: c for c in state.family("SelectionConcern")}
        self.assertEqual("PLAUSIBLE_NOT_ESTABLISHED",
                         by_issue["invented citation only"]["evidence_status"])
        self.assertEqual("SUPPORTED_BY_STATE",
                         by_issue["one real and one invented"]["evidence_status"])
        self.assertEqual(["JNT-0B"],
                         by_issue["one real and one invented"]["supporting_refs"])

    def test_D28_D29_plausible_and_speculative_need_no_reference(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "plausible", evidence_status="PLAUSIBLE_NOT_ESTABLISHED"),
            concern("CND-B", "speculative", evidence_status="SPECULATIVE")]),
            state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        by_issue = {c["issue"]: c for c in state.family("SelectionConcern")}
        self.assertEqual("PLAUSIBLE_NOT_ESTABLISHED",
                         by_issue["plausible"]["evidence_status"])
        self.assertEqual("SPECULATIVE", by_issue["speculative"]["evidence_status"])
        for record in by_issue.values():
            self.assertIsNone(record.get("evidence_note"))

    def test_D29b_a_status_is_never_raised_because_refs_happened_to_resolve(self):
        """Refs resolving is not the same fact as those refs supporting the
        claim. Only the reviewer can say that, and only about what it saw."""
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "speculative but cited",
                    evidence_status="SPECULATIVE", refs=["JNT-0A", "BOD-G0A"])]),
            state=state)
        record = self.only(state)
        self.assertEqual("SPECULATIVE", record["evidence_status"])
        self.assertEqual(["BOD-G0A", "JNT-0A"], record["supporting_refs"])

    def test_D30_an_unknown_evidence_status_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", evidence_status="PROVEN")]), state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)

    def test_D31_an_unknown_importance_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", importance="CRITICAL")]), state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)

    def test_D31b_a_concern_field_the_pass_may_not_author_is_refused(self):
        state, _cmp = self.compared()
        _s, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", eligible=False)]), state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status)

    def test_D32_the_same_concerns_in_a_different_order_are_the_same_records(self):
        """A reordering is not new engineering, and identity taken from list
        position would have said it was."""
        first = [concern("CND-A", "one"), concern("CND-B", "two"),
                 concern("CND-A", "three")]
        ids = []
        for order in (first, list(reversed(first))):
            state, _cmp = self.compared()
            state, out, _p = self.reviewed(review(concerns=order), state=state)
            ids.append(sorted(op.entity_id for op in out.patch.operations
                              if op.entity_type == "SelectionConcern"))
            self.assertEqual(3, len(ids[-1]))
        self.assertEqual(ids[0], ids[1],
                         "concern identity moved with list position")


# =====================================================================
# D33-D35 - the model cannot become a metric engine
# =====================================================================
class TestHallucinationBoundary(_Advisory):

    def test_D33_an_unavailable_metric_cannot_become_a_state_backed_claim(self):
        """The reviewer may say part count is not established. It may not say a
        candidate has fewer parts AS IF the design had measured it - and the only
        way to say anything with state support is to cite state, which for a
        metric nobody computed does not exist."""
        state, cmp_ = self.compared(preferences=prefs(part_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.NOT_AVAILABLE,
                         cmp_.metrics["part_count"]["CND-A"]["availability"])
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "CND-A has fewer parts and is therefore preferable",
                    evidence_status="SUPPORTED_BY_STATE", refs=[])]), state=state)
        record = state.family("SelectionConcern")[0]
        self.assertEqual("PLAUSIBLE_NOT_ESTABLISHED", record["evidence_status"])
        # And the comparison still says the metric is unavailable.
        comparison = state.family("CandidateComparison")[0]
        self.assertEqual("NOT_AVAILABLE",
                         comparison["metrics"]["part_count"]["CND-A"]["availability"])
        self.assertEqual(["part_count"], comparison["unavailable_criteria"])

    def test_D34_no_advisory_prose_produces_a_feasibility_verdict(self):
        state, _cmp = self.compared()
        before = self.snapshot(state)
        state, out, _p = self.reviewed(review(
            "PREFER_CANDIDATE", "CND-A",
            reasoning="CND-B is not mechanically feasible and violates the "
                      "material requirement",
            concerns=[concern("CND-B", "this candidate cannot work",
                              importance="HIGH",
                              evidence_status="SUPPORTED_BY_STATE",
                              refs=["JNT-0B"])]), state=state)
        self.assertEqual(before, self.snapshot(state))
        self.assertEqual({"SelectionAdvisory", "SelectionConcern"},
                         {op.entity_type for op in out.patch.operations})

    def test_D35_a_durability_concern_stays_at_the_status_it_earned(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "repeated flexure may be durability-sensitive",
                    importance="HIGH", evidence_status="SUPPORTED_BY_STATE",
                    refs=[])]), state=state)
        record = state.family("SelectionConcern")[0]
        self.assertIn(record["evidence_status"],
                      ("PLAUSIBLE_NOT_ESTABLISHED", "SPECULATIVE"))
        self.assertEqual("HIGH", record["importance"],
                         "the downgrade touched the wrong field")


# =====================================================================
# D36-D42 - what the review depends on
# =====================================================================
class TestDependency(_Advisory):

    def premises(self, state, eid):
        return set(state.entities[eid].get("_premises") or [])

    def test_D36_the_advisory_premises_exactly_what_the_model_was_shown(self):
        """Not the subset it cited. A deterministic stage knows which fields it
        computed from; a model can use anything it was shown, and pretending
        otherwise would be a currentness claim the reviewer never made."""
        state, cmp_ = self.compared()
        exposure = set(adv.visible_ids(
            adv.SelectionEngineeringReview().consumer_view(state).payload()))
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", evidence_status="SUPPORTED_BY_STATE",
                    refs=["JNT-0A"])]), state=state)
        advisory = self.advisory_of(state)["entity_id"]
        carried = self.premises(state, advisory)
        self.assertEqual(exposure, carried,
                         "the premise set is not the provider exposure")
        for required in (cmp_.patch.operations[0].entity_id,
                         state.standing("SelectionProfile")[0]["entity_id"],
                         "MFA-CND-A", "BOD-G0A"):
            self.assertIn(required, carried, required)
        self.assertGreater(len(carried), 1,
                           "only the cited reference was premised")

    def test_D37_a_concern_premises_the_advisory_and_the_same_exposure(self):
        state, cmp_ = self.compared()
        state, out, _p = self.reviewed(review(concerns=[concern("CND-A")]),
                                        state=state)
        advisory = self.advisory_of(state)["entity_id"]
        concern_id = state.family("SelectionConcern")[0]["entity_id"]
        carried = self.premises(state, concern_id)
        self.assertIn(advisory, carried)
        self.assertTrue(self.premises(state, advisory) <= carried,
                        "the concern rests on less than the review did")

    def test_D38_D39_changing_a_shown_engineering_fact_stales_both(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[concern("CND-A")]),
                                        state=state)
        advisory = self.advisory_of(state)["entity_id"]
        concern_id = state.family("SelectionConcern")[0]["entity_id"]
        self.assertEqual("STANDING", self.val(state, advisory))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G0A",
                              {"extent": {"centre": [0, 0, 0],
                                          "half_extent": [4, 4, 4]}},
                              "t", reason="probe"))
        self.assertEqual("STALE", self.val(state, advisory))
        self.assertEqual("STALE", self.val(state, concern_id))

    def test_D40_changing_the_preferences_stales_the_review(self):
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(), state=state)
        advisory = self.advisory_of(state)["entity_id"]
        self.profile(state, prefs(joint_count=(MAXIMIZE, HIGH)))
        self.assertEqual("STALE", self.val(state, advisory))

    def test_D41_a_review_stales_no_deterministic_record(self):
        """Advisory causality runs downstream only. Rewording an opinion cannot
        reopen whether a mechanism works."""
        state, _cmp = self.compared()
        before = self.snapshot(state)
        state, _out, _p = self.reviewed(review(reasoning="one reading"),
                                        state=state)
        self.assertEqual(before, self.snapshot(state))
        state, _out, _p = self.reviewed(
            review(reasoning="quite a different reading",
                   concerns=[concern("CND-A", "and a new concern")]),
            state=state)
        self.assertEqual(before, self.snapshot(state),
                         "a second review disturbed the deterministic record")

    def test_D42_an_entity_the_model_never_saw_is_not_a_premise(self):
        state, cmp_ = self.compared()
        payload = adv.SelectionEngineeringReview().consumer_view(state).payload()
        exposure = set(adv.visible_ids(payload))
        unseen = sorted(eid for eid in state.entities if eid not in exposure)
        self.assertTrue(unseen, "the probe is not probing")
        state, out, _p = self.reviewed(review(), state=state)
        carried = self.premises(state, self.advisory_of(state)["entity_id"])
        for eid in unseen:
            self.assertNotIn(eid, carried, eid)
        # And such a fact changing leaves the review standing.
        source = [e for e in unseen if e.startswith("SRC-")]
        if source:
            self.revise(state, Op("SUPERSEDE", "SourceClause", source[0],
                                  {"directionality": "changed"}, "t",
                                  reason="probe"), stage="s01")
            self.assertEqual("STANDING",
                             self.val(state, self.advisory_of(state)["entity_id"]))


# =====================================================================
# D43-D48 - the provider, and what a failure means
# =====================================================================
class TestProviderBoundary(_Advisory):

    def test_D43_a_ready_context_calls_the_provider_exactly_once(self):
        state, _cmp = self.compared()
        _s, out, provider = self.reviewed(review(), state=state)
        self.assertEqual(1, provider.calls)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)

    def test_D44_an_insufficient_context_calls_it_zero_times(self):
        state = self.built()
        provider = _Canned(review())
        out = adv.SelectionEngineeringReview().invoke(provider, state, state.run_id)
        self.assertEqual(0, provider.calls)
        self.assertIsNotNone(out.consumer_view, "the refusal is not recorded")
        self.assertNotEqual("VIEW_READY", out.consumer_view["status"])

    def test_D45_D46_D47_a_provider_failure_writes_nothing(self):
        """AND IT IS NOT 'NO CONCERN EXISTS'. Being asked and not answering is a
        different fact from being asked and finding nothing."""
        state, _cmp = self.compared()
        before = self.snapshot(state)
        for provider, expected in (
                (_Failing(ExecutionStatus.PROVIDER_TIMEOUT),
                 ExecutionStatus.PROVIDER_TIMEOUT),
                (_Failing(raw="{not json"), ExecutionStatus.RESPONSE_PARSE_FAILURE),
                (_Failing(raw=json.dumps(review()), truncated=True),
                 ExecutionStatus.RESPONSE_TRUNCATED)):
            out = adv.SelectionEngineeringReview().invoke(provider, state,
                                                          state.run_id)
            self.assertEqual(expected, out.execution_status)
            self.assertIsNone(out.patch)
            self.assertEqual(1, provider.calls)
        self.assertEqual([], state.family("SelectionAdvisory"))
        self.assertEqual([], state.family("SelectionConcern"))
        self.assertEqual(before, self.snapshot(state),
                         "a provider failure disturbed the comparison")

    def test_D48_a_malformed_advisory_is_not_partially_materialised(self):
        state, _cmp = self.compared()
        for response in ({"reasoning": "no recommendation at all", "concerns": []},
                         {"recommendation": "PREFER_CANDIDATE", "reasoning": "x",
                          "concerns": []},
                         review(reasoning=""),
                         review(reasoning=None)):
            provider = _Canned(response)
            out = adv.SelectionEngineeringReview().invoke(provider, state,
                                                          state.run_id)
            self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status,
                             response)
            self.assertIsNone(out.patch)
        self.assertEqual([], state.family("SelectionAdvisory"))


# =====================================================================
# D49-D55 - the runner, and the scope boundary
# =====================================================================
class TestRunnerAndScope(_Advisory):

    def test_D49_the_runner_reviews_only_after_the_comparison(self):
        state = self.built()
        provider = _Canned(review())
        early = run_window2.run_selection_advisory("SYN", state, provider, 1)
        self.assertEqual(adv.ADVISORY_NOT_APPLICABLE, early["advisory_status"])
        self.assertEqual(0, provider.calls)
        self.assertEqual([], early["failures"], "a result was recorded as a failure")

        state, _cmp = self.compared(state=state)
        rec = run_window2.run_selection_advisory("SYN", state, provider, 1)
        self.assertEqual("SUCCESS", rec["advisory_status"])
        self.assertEqual(1, provider.calls)
        self.assertEqual(1, len(rec["advisory"]))

    def test_D50_D51_D52_the_runner_adjudicates_nothing(self):
        import inspect
        body = inspect.getsource(run_window2.run_selection_advisory).split('"""', 2)[2]
        for helper in ("SUPPORTED_BY_STATE", "PLAUSIBLE_NOT_ESTABLISHED",
                       "evidence_status", "supporting_refs", "visible_ids",
                       "comparison_alignment", "PREFER_CANDIDATE",
                       "recommended_candidate", "json.loads", "frontier"):
            self.assertNotIn(helper, body, "the runner does %r itself" % helper)
        # It calls the producer through the ordinary Stage boundary and applies
        # what comes back.
        self.assertIn("SelectionEngineeringReview().invoke(", body)
        self.assertIn("state.apply(out.patch)", body)

    def test_D53_D54_no_decision_shaped_artifact_is_produced(self):
        import inspect
        source = inspect.getsource(adv)
        for family in ("HumanDecisionInput", "SelectionDecision",
                       "UnresolvedDecision", "MechanicalFeasibilityAssessment",
                       "HardRequirementCompliance", "FeasibilityDomainAssessment"):
            self.assertNotIn(family, source, family)
        state, _cmp = self.compared()
        state, _out, _p = self.reviewed(review("PREFER_CANDIDATE", "CND-A"),
                                        state=state)
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual([], state.family("HumanDecisionInput"))

    def test_D55_no_advisory_changes_deterministic_eligibility(self):
        """The whole population, recomputed after the review, entity for
        entity."""
        state, cmp_ = self.compared()
        state, _out, _p = self.reviewed(review(
            "PREFER_CANDIDATE", "CND-B",
            concerns=[concern("CND-A", "serious", importance="HIGH",
                              evidence_status="SUPPORTED_BY_STATE",
                              refs=["JNT-0A"])]), state=state)
        again = sel.evaluate_candidate_comparison(state)
        self.assertEqual(cmp_.eligible, again.eligible)
        self.assertEqual({k: v[0] for k, v in cmp_.population.items()},
                         {k: v[0] for k, v in again.population.items()})

    def test_D55b_only_selection_may_author_these_families(self):
        state, _cmp = self.compared()
        for family in ("SelectionAdvisory", "SelectionConcern"):
            for stage in ("s01", "s04", "feasibility"):
                problems = state.validate(StagePatch(
                    patch_id="bad", run_id=state.run_id, stage_id=stage,
                    stage_attempt=1, parent_state_hash=state.state_hash(),
                    operations=[Op("CREATE", family, "XXX-1", {}, "t")],
                    execution_status="SUCCESS", provenance={"provider": "t"}))
                self.assertTrue(any("OWNERSHIP" in p or "NOT_OWNER" in p
                                    for p in problems),
                                "%s authored %s" % (stage, family))
        # And the pass writes AS selection, not as a new owner.
        self.assertEqual("selection", adv.SelectionEngineeringReview.stage_id)
        self.assertEqual("selection_advisory",
                         adv.SelectionEngineeringReview.responsibility_id())


# =====================================================================
# D56-D68 - the response boundary is a closed, strictly typed schema
# =====================================================================
class TestResponseSchema(_Advisory):
    """THE MODEL IS OUTSIDE THE AUTHORITY BOUNDARY, so the parse is part of the
    safety contract rather than a convenience.

    Every case here crossed the boundary before this pass. The one that shows why
    strictness matters most is D60: `supporting_refs: "JNT-0A"` was iterated
    CHARACTER BY CHARACTER, so a malformed field became six references that
    resolve to nothing - and the concern was then downgraded for lacking support
    it had in fact supplied in the wrong shape. A schema failure laundered into
    an evidence finding tells the model nothing and tells the record something
    false about why."""

    def refused(self, response, state=None):
        state = state if state is not None else self.compared()[0]
        _s, out, _p = self.reviewed(response, state=state)
        self.assertEqual(ExecutionStatus.SCHEMA_FAILURE, out.execution_status,
                         json.dumps(response, default=str)[:200])
        self.assertIsNone(out.patch)
        self.assertEqual([], state.family("SelectionAdvisory"))
        self.assertEqual([], state.family("SelectionConcern"))
        return out

    def recommendation(self, **block):
        return {"recommendation": block, "reasoning": "a review", "concerns": []}

    def test_D56_a_nested_authority_field_is_refused(self):
        """The top level was pinned and the recommendation was read with `.get`,
        so a forbidden field one object deeper was merely ignored. Being ignored
        by this reader is not a defence - the next one might not."""
        for hidden in ("selected_candidate", "winner", "score", "eligibility",
                       "comparison_alignment", "recommended_candidate",
                       "selection_decision", "premise_refs", "entity_id"):
            self.refused(self.recommendation(
                **{"kind": "PREFER_CANDIDATE", "candidate": "CND-A",
                   hidden: "CND-A"}))

    def test_D57_an_unknown_nested_field_is_refused(self):
        """A CLOSED SCHEMA, not a blacklist. A blacklist has to anticipate the
        name; this does not."""
        for unknown in ("foo", "note", "confidence", "rationale"):
            self.refused(self.recommendation(
                **{"kind": "PREFER_CANDIDATE", "candidate": "CND-A",
                   unknown: "bar"}))

    def test_D57b_a_recommendation_missing_a_required_key_is_refused(self):
        """Both directions. A response that omits `candidate` does not say what
        it means either."""
        self.refused(self.recommendation(kind="NO_CLEAR_PREFERENCE"))
        self.refused(self.recommendation(candidate=None))
        self.refused({"reasoning": "x", "concerns": []})

    def test_D58_no_clear_preference_requires_exactly_null(self):
        """Five falsy values were being accepted as the one legitimate way to say
        nothing was preferred."""
        for masquerade in ("", 0, False, True, [], {}, "CND-A"):
            self.refused(self.recommendation(kind="NO_CLEAR_PREFERENCE",
                                             candidate=masquerade))
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(
            self.recommendation(kind="NO_CLEAR_PREFERENCE", candidate=None),
            state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)

    def test_D59_prefer_candidate_requires_a_non_empty_eligible_string(self):
        for bad in (None, "", 0, False, [], {}, ["CND-A"], "CND-ELSEWHERE"):
            self.refused(self.recommendation(kind="PREFER_CANDIDATE",
                                             candidate=bad))
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(
            self.recommendation(kind="PREFER_CANDIDATE", candidate="CND-A"),
            state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)

    def test_D60_a_bare_string_of_refs_is_refused_not_iterated(self):
        self.refused(review(concerns=[dict(
            concern("CND-A", evidence_status="SUPPORTED_BY_STATE"),
            supporting_refs="JNT-0A")]))

    def test_D61_a_mixed_type_ref_list_is_refused(self):
        for refs in (["JNT-0A", 7], [1, 2], ["JNT-0A", None], ["JNT-0A", ""],
                     ["JNT-0A", ["JNT-0B"]], None, {}, 7):
            self.refused(review(concerns=[dict(
                concern("CND-A", evidence_status="SUPPORTED_BY_STATE"),
                supporting_refs=refs)]))

    def test_D62_a_fabricated_ref_still_downgrades_rather_than_refusing(self):
        """THE DISTINCTION THIS WHOLE CLASS IS ABOUT. A well-formed list holding
        an id that does not exist is a claim about evidence, not a malformed
        response - so the concern is kept and its status corrected."""
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[
            concern("CND-A", "possible fatigue sensitivity", importance="HIGH",
                    evidence_status="SUPPORTED_BY_STATE", refs=["FAKE-ID"])]),
            state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        record = state.family("SelectionConcern")[0]
        self.assertEqual("PLAUSIBLE_NOT_ESTABLISHED", record["evidence_status"])
        self.assertEqual([], record["supporting_refs"])
        self.assertIn("claimed state support", record["evidence_note"])
        self.assertEqual("HIGH", record["importance"])

    def test_D63_a_sensitivity_of_the_wrong_type_is_refused(self):
        for bad in (None, 0, True, [], {}, 1.5):
            self.refused(review(sensitivity=bad))
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(sensitivity="a real statement"),
                                        state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        self.assertEqual("a real statement",
                         self.advisory_of(state)["sensitivity"])

    def test_D63b_an_absent_sensitivity_is_valid_and_writes_no_field(self):
        """Absent means no statement. `null` is not the way to say that."""
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(), state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        self.assertNotIn("sensitivity", self.advisory_of(state))

    def test_D64_a_reasoning_of_the_wrong_type_is_refused(self):
        for bad in (None, 123, [], {}, True, "", "   "):
            self.refused(review(reasoning=bad))

    def test_D65_concerns_must_be_a_list(self):
        # Built by hand: the helper coerces with `list(...)`, which is exactly
        # the leniency under test.
        # No tuple case: the boundary is JSON, which has no tuples - one would
        # arrive as a list and the test would be asserting about the encoder.
        for bad in (None, {}, "none", 0, "  ", "[]", 1.0, True):
            self.refused(dict(review(), concerns=bad))
        state, _cmp = self.compared()
        state, out, _p = self.reviewed(review(concerns=[]), state=state)
        self.assertEqual(ExecutionStatus.SUCCESS, out.execution_status)
        self.assertEqual([], state.family("SelectionConcern"))

    def test_D66_a_concern_carrying_an_extra_key_is_refused(self):
        for hidden in ("eligibility", "feasibility", "score", "decision",
                       "hard_requirement_status", "comparison_alignment",
                       "entity_id", "premise_refs", "advisory", "foo"):
            self.refused(review(concerns=[
                dict(concern("CND-A"), **{hidden: "INELIGIBLE"})]))

    def test_D66b_a_concern_missing_a_required_key_is_refused(self):
        for dropped in ("candidate", "issue", "importance", "evidence_status",
                        "supporting_refs"):
            partial = concern("CND-A")
            del partial[dropped]
            self.refused(review(concerns=[partial]))

    def test_D66c_concern_field_types_are_strict(self):
        for field, bad in (("candidate", 0), ("candidate", ""),
                           ("candidate", ["CND-A"]), ("issue", None),
                           ("issue", 123), ("issue", ""),
                           ("importance", 0), ("importance", True),
                           ("importance", ["HIGH"]),
                           ("evidence_status", None), ("evidence_status", 1)):
            self.refused(review(concerns=[dict(concern("CND-A"),
                                               **{field: bad})]))

    def test_D67_one_malformed_concern_writes_nothing_at_all(self):
        """Writing the valid ones and dropping the rest would publish a review
        the model did not give, and the reader would have no way to know."""
        state, _cmp = self.compared()
        self.refused(review(concerns=[
            concern("CND-A", "a perfectly good concern", importance="HIGH"),
            dict(concern("CND-B", "the malformed one"), eligibility="NO")]),
            state=state)

    def test_D68_no_producer_field_can_be_authored_at_any_level(self):
        """Top level, inside the recommendation, and inside a concern. The same
        closed-key rule refuses all three."""
        producer_owned = ("candidates", "comparison", "comparison_alignment",
                          "recommended_candidate", "entity_id", "premise_refs",
                          "selected_candidate", "winner", "eligibility",
                          "feasibility", "hard_requirement_status", "score",
                          "weighted_score", "selection_decision")
        for field in producer_owned:
            self.refused(review(**{field: "CND-A"}))
            self.refused(self.recommendation(
                **{"kind": "NO_CLEAR_PREFERENCE", "candidate": None,
                   field: "CND-A"}))
            self.refused(review(concerns=[dict(concern("CND-A"),
                                               **{field: "CND-A"})]))

    def test_D68b_one_extra_key_refuses_every_model_owned_object(self):
        """THE PROPERTY, not the examples. Any extra key at any model-owned
        level, whatever it is called - so the same gap cannot reappear under a
        name nobody thought to blacklist."""
        for extra in ("x", "note", "verdict", "authority", "_meta", "1",
                      "candidate_id", "status"):
            self.refused(review(**{extra: "anything"}))
            self.refused(self.recommendation(
                **{"kind": "NO_CLEAR_PREFERENCE", "candidate": None,
                   extra: "anything"}))
            self.refused(review(concerns=[dict(concern("CND-A"),
                                               **{extra: "anything"})]))

    def test_D68c_the_closed_key_sets_are_the_declared_schema(self):
        self.assertEqual({"recommendation", "reasoning", "sensitivity",
                          "concerns"}, set(adv.RESPONSE_KEYS))
        self.assertEqual({"sensitivity"}, set(adv.RESPONSE_OPTIONAL))
        self.assertEqual({"kind", "candidate"}, set(adv.RECOMMENDATION_KEYS))
        self.assertEqual({"candidate", "issue", "importance", "evidence_status",
                          "supporting_refs"}, set(adv.CONCERN_KEYS))

    def test_D68d_structure_is_validated_before_evidence_ever_runs(self):
        """The two are different questions and the order is the whole point: a
        malformed field must never reach the evidence validator, where it would
        arrive disguised as a weak claim."""
        import inspect
        writer = inspect.getsource(adv.SelectionEngineeringReview.to_operations)
        self.assertLess(writer.index("validate_response("),
                        writer.index("calibrate("),
                        "evidence is calibrated before the shape is checked")
        calibrate = inspect.getsource(adv.calibrate)
        for structural in ("isinstance", "raise ValueError"):
            self.assertNotIn(structural, calibrate,
                             "the evidence validator does structural work")


# =====================================================================
# The contracts describe what runs
# =====================================================================
class TestContractTruth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.state = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.matrix = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.audit = _paths.contract("ENTITY_FAMILY_AUDIT.yaml")
        cls.fams = dict(cls.state["entity_families"])
        cls.fams.update(cls.state["assurance_families"])

    def test_the_vocabularies_are_the_ones_the_code_emits(self):
        advisory = self.fams["SelectionAdvisory"]
        self.assertEqual(sorted(adv.RECOMMENDATIONS),
                         sorted(advisory["recommendation"]))
        self.assertEqual(sorted([adv.ALIGNS_WITH_FRONTIER,
                                 adv.DEPARTS_FROM_FRONTIER,
                                 adv.NO_DETERMINISTIC_PREFERENCE]),
                         sorted(advisory["comparison_alignment"]))
        for field in ("recommendation", "comparison_alignment"):
            self.assertIn(field, advisory["required_fields"], field)
        self.assertIn("recommended_candidate", advisory["optional_fields"])
        record = self.fams["SelectionConcern"]
        self.assertEqual(sorted(adv.IMPORTANCE), sorted(record["importance"]))
        self.assertEqual(sorted(adv.EVIDENCE_STATUS),
                         sorted(record["evidence_status"]))
        self.assertIn("evidence_note", record["optional_fields"])

    def test_both_families_are_assurance_and_owned_by_selection(self):
        for family in ("SelectionAdvisory", "SelectionConcern"):
            self.assertEqual("selection", self.fams[family]["owned_by"])
            self.assertEqual("ASSURANCE", self.fams[family]["authority_class"])
            self.assertIn(family,
                          self.matrix["responsibilities"]["entries"]["selection"]["owns"])
            entry = json.dumps(self.audit["families"][family])
            for phrase in ("has not yet emitted", "no producer"):
                self.assertNotIn(phrase, entry, "%s: %r" % (family, phrase))

    def test_the_pass_is_a_second_view_of_one_owner(self):
        """Not a new owner. `authority_stage` says whose it writes as, and the
        ownership matrix gains no entry - a responsibility that owns nothing new
        is a consumer pass, which is what this is."""
        entry = self.resp["stages"]["selection_advisory"]
        self.assertEqual("selection", entry["authority_stage"])
        self.assertEqual(["SelectionAdvisory", "SelectionConcern"],
                         entry["permitted_output_semantics"])
        self.assertNotIn("selection_advisory",
                         self.matrix["responsibilities"]["entries"])

    def test_the_reviewer_declares_the_roles_its_question_needs(self):
        roles = {r for p in self.resp["stages"]["selection_advisory"]
                 ["required_reasoning_premise_classes"]
                 for r in p["requires_semantics"]}
        for family, role in (("CandidateComparison", "selection_evidence"),
                             ("SelectionProfile", "selection_preference"),
                             ("MechanicalFeasibilityAssessment", "eligibility_evidence"),
                             ("Body", "topology_element"),
                             ("Joint", "topology_relation"),
                             ("Envelope", "spatial_commitment"),
                             ("Transition", "motion_path"),
                             ("SweptVolume", "motion_occupancy"),
                             ("MobilityExpectation", "mobility_disposition"),
                             ("PhysicalInteraction", "physical_interaction"),
                             ("LoadPath", "load_route"),
                             ("AssemblyStep", "assembly_order"),
                             ("ReachResult", "reach_evidence"),
                             ("DesignConstraint", "design_constraint")):
            self.assertIn(role, roles, family)
            self.assertIn(role, self.fams[family]["semantic_roles"], family)

    def test_the_legitimately_absent_evidence_is_not_required(self):
        """The mistake S-7 has already made five times. A static mechanism, a
        design with no actor and a candidate with no load case are ordinary, and
        demanding their evidence would make the view unready for a question it
        could have answered."""
        by_role = {}
        for premise in self.resp["stages"]["selection_advisory"][
                "required_reasoning_premise_classes"]:
            for rule in (premise["instance_selection"].get("by_role") or []):
                by_role[rule["role"]] = rule["existence"]
        for optional in ("motion_path", "motion_occupancy", "physical_interaction",
                         "load_route", "assembly_order", "reach_evidence"):
            self.assertEqual("MAY_BE_EMPTY", by_role.get(optional), optional)
        for required in ("topology_element", "spatial_commitment"):
            self.assertEqual("REQUIRED_NONEMPTY", by_role.get(required), required)


if __name__ == "__main__":
    unittest.main()
