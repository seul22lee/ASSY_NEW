"""The S01 -> S02 window holds on every recorded case.

Runs the real stages against the recorded provider responses and asserts that
every check the window owns reports nothing. It is deliberately case-agnostic:
it discovers cases from the fixtures directory rather than naming any, because a
benchmark identifier in a test is the same defect as one in production code.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from ver3.assy_v3.providers.offline import OfflineReplayProvider          # noqa: E402
from ver3.assy_v3.stages.s01_requirement_capture import (                 # noqa: E402
    S01RequirementCapture, sharpening_check, locator_check, mechanism_leakage_check)
from ver3.assy_v3.stages.s02_obligation_and_candidates import (           # noqa: E402
    S02ObligationAndCandidates, no_selection_check, load_case_check,
    candidate_distinctness_check, known_principle_check, evidence_route_check,
    magnitude_fidelity_check,
    created_obligations_check, requirement_coverage_check, obligation_scope_check,
    candidate_coverage_check, openness_citation_check, actor_citation_check)
from ver3.assy_v3.state import DesignState, project_for                   # noqa: E402

FIXTURES = os.path.join(_REPO, "ver3", "assy_v3", "fixtures", "responses")
BENCHMARKS = os.path.join(_REPO, "ver3", "benchmarks")
PROBES = os.path.join(_REPO, "ver3", "assy_v3", "probes")
CASES = sorted(d for d in os.listdir(FIXTURES) if os.path.isdir(os.path.join(FIXTURES, d)))
PROBE_CASES = sorted(d for d in os.listdir(PROBES) if os.path.isdir(os.path.join(PROBES, d)))


def _run(case, probe=False):
    if probe:
        from ver3.assy_v3.providers.agent_authored import AgentAuthoredProvider
        provider = AgentAuthoredProvider(PROBES, case)
        request = os.path.join(PROBES, case, "request.txt")
    else:
        provider = OfflineReplayProvider(FIXTURES, case)
        request = os.path.join(BENCHMARKS, case, "source", "request.txt")
    state = DesignState(run_id=case)
    with open(request) as fh:
        text = fh.read()
    o1 = S01RequirementCapture().run(provider, {"request_text": text}, state, case)
    assert o1.patch is not None, o1.problems
    state.apply(o1.patch)
    proj = project_for("s02", state)
    o2 = S02ObligationAndCandidates().run(provider, {"projection": proj}, state, case)
    assert o2.patch is not None, o2.problems
    state.apply(o2.patch)
    return state, text, proj, o1, o2


class TestWindow(unittest.TestCase):

    def test_there_is_at_least_one_case(self):
        self.assertTrue(CASES)

    def test_both_stages_succeed_and_every_check_is_clean(self):
        for case in CASES:
            with self.subTest(case=case):
                state, text, proj, o1, o2 = _run(case)
                self.assertEqual("SUCCESS", o1.execution_status.value, o1.problems)
                self.assertEqual("SUCCESS", o2.execution_status.value, o2.problems)
                for name, found in (
                        ("sharpening", sharpening_check(state, text)),
                        ("locator", locator_check(state)),
                        ("mechanism_leak", mechanism_leakage_check(state, text)),
                        ("no_selection", no_selection_check(state)),
                        ("load_case", load_case_check(state)),
                        ("magnitude_fidelity", magnitude_fidelity_check(state)),
                        ("distinctness", candidate_distinctness_check(state)),
                        ("known_principle", known_principle_check(state)),
                        ("evidence_route", evidence_route_check(state)),
                        ("created_obligations", created_obligations_check(state)),
                        ("requirement_coverage", requirement_coverage_check(state)),
                        ("obligation_scope", obligation_scope_check(state)),
                        ("candidate_coverage", candidate_coverage_check(state)),
                        ("openness_citation", openness_citation_check(state)),
                        ("actor_citation", actor_citation_check(state))):
                    self.assertEqual([], found, "%s/%s" % (case, name))

    def test_s02_never_sees_source_text(self):
        """INV-002 enforced by the projection, not by stage good behaviour."""
        for case in CASES:
            with self.subTest(case=case):
                _state, _text, proj, _o1, _o2 = _run(case)
                self.assertNotIn("SourceClause", proj)

    def test_design_space_is_not_collapsed(self):
        """More than one candidate survives, and openness is recorded."""
        for case in CASES:
            with self.subTest(case=case):
                state, _t, _p, _o1, _o2 = _run(case)
                self.assertGreater(len(state.family("Candidate")), 1)
                self.assertTrue(state.family("UnresolvedDecision"))

    def test_no_candidate_carries_a_ranking(self):
        for case in CASES:
            with self.subTest(case=case):
                state, _t, _p, _o1, _o2 = _run(case)
                self.assertEqual([], no_selection_check(state))


class TestProbesLiveReasoning(unittest.TestCase):
    """The probes are LIVE evidence, not regression fixtures.

    Their recordings declare the prompt they answer, so a change to a prompt or
    to the knowledge layer invalidates them instead of silently replaying an
    answer to a question no longer being asked. That is the property this suite
    is protecting; the check results are secondary to it.
    """

    def test_probe_recordings_answer_the_current_prompt(self):
        for case in PROBE_CASES:
            with self.subTest(case=case):
                _s, _t, _p, o1, o2 = _run(case, probe=True)
                self.assertEqual("SUCCESS", o1.execution_status.value, o1.problems)
                self.assertEqual("SUCCESS", o2.execution_status.value, o2.problems)

    def test_every_check_is_clean_on_unseen_inputs(self):
        for case in PROBE_CASES:
            with self.subTest(case=case):
                state, text, _p, _o1, _o2 = _run(case, probe=True)
                for name, found in (
                        ("sharpening", sharpening_check(state, text)),
                        ("mechanism_leak", mechanism_leakage_check(state, text)),
                        ("load_case", load_case_check(state)),
                        ("magnitude_fidelity", magnitude_fidelity_check(state)),
                        ("known_principle", known_principle_check(state)),
                        ("requirement_coverage", requirement_coverage_check(state)),
                        ("obligation_scope", obligation_scope_check(state)),
                        ("candidate_coverage", candidate_coverage_check(state)),
                        ("openness_citation", openness_citation_check(state)),
                        ("actor_citation", actor_citation_check(state))):
                    self.assertEqual([], found, "%s/%s" % (case, name))

    def test_reaction_sites_are_not_defaulted(self):
        """No probe stands on a desk; none may claim a desk reacts its load."""
        for case in PROBE_CASES:
            with self.subTest(case=case):
                state, _t, _p, _o1, _o2 = _run(case, probe=True)
                sites = {lc.get("reacted_at_role", "") for lc in state.family("LoadCase")}
                self.assertTrue(sites)
                self.assertTrue(any(s.strip() for s in sites))
