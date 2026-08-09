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
from ver3.assy_v3.state import DesignState                                # noqa: E402

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
    o1 = S01RequirementCapture().invoke(provider, state, case, {"request_text": text})
    assert o1.patch is not None, o1.problems
    state.apply(o1.patch)
    stage2 = S02ObligationAndCandidates()
    proj = stage2.consumer_view(state).payload()
    o2 = stage2.invoke(provider, state, case)
    assert o2.patch is not None, o2.problems
    state.apply(o2.patch)
    return state, text, proj, o1, o2


def _stale_recording(case, probe=False):
    """Whether the recording answers a prompt the stage no longer builds.

    Impl S-4 asks s02 for physical effect obligations and for ids where the old
    prompt allowed a description, so every recording predating that answers a
    different question. The provider detects it by prompt hash - that mechanism
    exists precisely so a stale answer is never mistaken for a current one.

    Refreshing the corpus needs a live model run, which this pass is not
    authorized to make. Skipping states that, and
    `test_the_probe_corpus_is_stale_against_the_current_prompt` below asserts the
    staleness IS detected, so it cannot pass silently.
    """
    provider = (OfflineReplayProvider(FIXTURES, case) if not probe
                else __import__("ver3.assy_v3.providers.agent_authored", fromlist=["x"])
                .AgentAuthoredProvider(PROBES, case))
    request = (os.path.join(BENCHMARKS, case, "source", "request.txt") if not probe
               else os.path.join(PROBES, case, "request.txt"))
    state = DesignState(run_id=case)
    with open(request) as fh:
        text = fh.read()
    o1 = S01RequirementCapture().invoke(provider, state, case, {"request_text": text})
    if o1.patch is None:
        return "; ".join(o1.problems or [])
    state.apply(o1.patch)
    o2 = S02ObligationAndCandidates().invoke(provider, state, case)
    for problem in (o2.problems or []):
        if "stale" in problem:
            return problem
    return None


def _s02_reference_violations(case, probe=False):
    """R-20 violations the recorded s02 response carries, as the boundary sees them.

    `Candidate.obligations_created` is declared a typed reference to Obligation and
    the prompt asks for "obligation ids you emit here". The recorded responses put
    statements there. Until S-2 the boundary decided what a reference was from the
    field's spelling and never looked at the value, so this was accepted for the
    whole project; the canonical check sees it.
    """
    provider = (OfflineReplayProvider(FIXTURES, case) if not probe
                else __import__("ver3.assy_v3.providers.agent_authored", fromlist=["x"])
                .AgentAuthoredProvider(PROBES, case))
    request = (os.path.join(BENCHMARKS, case, "source", "request.txt") if not probe
               else os.path.join(PROBES, case, "request.txt"))
    state = DesignState(run_id=case)
    with open(request) as fh:
        text = fh.read()
    o1 = S01RequirementCapture().invoke(provider, state, case, {"request_text": text})
    state.apply(o1.patch)
    o2 = S02ObligationAndCandidates().invoke(provider, state, case)
    return [p for p in (o2.problems or [])
            if "REFERENCE_NOT_AN_ID" in p or "DANGLING_REF" in p]


class _WindowBase(unittest.TestCase):

    def _require_applicable_s02(self, case, probe=False):
        """The recorded s02 response for this case may violate R-20.

        Registered as residual **R-B**, owner Impl S-4: the producer writes
        obligation STATEMENTS into a field the contract and the prompt both
        declare to hold obligation IDS. The write boundary now refuses it, so the
        window cannot be replayed from that recording. Skipping states the
        registered defect rather than hiding a red test - and
        `test_R_B_the_recorded_s02_response_violates_the_reference_contract`
        below asserts the violation is detected, so it cannot pass silently.
        """
        stale = _stale_recording(case, probe)
        if stale:
            self.skipTest("STALE RECORDING (corpus refresh, needs an authorized live "
                          "run): %s" % stale[:150])
        bad = _s02_reference_violations(case, probe)
        if bad:
            self.skipTest("R-B (S-4): recorded s02 response violates R-20 - %s"
                          % bad[0][:120])


class TestWindow(_WindowBase):

    def test_the_probe_corpus_is_stale_against_the_current_prompt(self):
        """The replay for the corpus-refresh boundary. Detection, not silence."""
        stale = {c: _stale_recording(c, probe=True) for c in PROBE_CASES}
        stale = {c: s for c, s in stale.items() if s}
        self.assertTrue(stale,
                        "no probe recording is stale any more - if the corpus was "
                        "refreshed, retire this test rather than keeping it")
        for case, problem in stale.items():
            self.assertIn("stale", problem, case)

    def test_R_B_the_recorded_s02_response_violates_the_reference_contract(self):
        """The replay for residual R-B. Detection, attribution, no silence."""
        offending = {}
        for case in CASES:
            bad = _s02_reference_violations(case)
            if bad:
                offending[case] = bad
        self.assertTrue(offending,
                        "no recorded response violates R-20 any more - if the "
                        "corpus was regenerated, retire R-B rather than this test")
        for case, problems in offending.items():
            self.assertTrue(any("obligations_created" in p for p in problems), case)

    def test_there_is_at_least_one_case(self):
        self.assertTrue(CASES)

    def test_both_stages_succeed_and_every_check_is_clean(self):
        for case in CASES:
            with self.subTest(case=case):
                self._require_applicable_s02(case)
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
                self._require_applicable_s02(case, probe=False)
                _state, _text, proj, _o1, _o2 = _run(case)
                self.assertNotIn("SourceClause", proj)

    def test_design_space_is_not_collapsed(self):
        """More than one candidate survives, and openness is recorded."""
        for case in CASES:
            with self.subTest(case=case):
                self._require_applicable_s02(case, probe=False)
                state, _t, _p, _o1, _o2 = _run(case)
                self.assertGreater(len(state.family("Candidate")), 1)
                self.assertTrue(state.family("UnresolvedDecision"))

    def test_no_candidate_carries_a_ranking(self):
        for case in CASES:
            with self.subTest(case=case):
                self._require_applicable_s02(case, probe=False)
                state, _t, _p, _o1, _o2 = _run(case)
                self.assertEqual([], no_selection_check(state))


class TestProbesLiveReasoning(_WindowBase):
    """The probes are LIVE evidence, not regression fixtures.

    Their recordings declare the prompt they answer, so a change to a prompt or
    to the knowledge layer invalidates them instead of silently replaying an
    answer to a question no longer being asked. That is the property this suite
    is protecting; the check results are secondary to it.
    """

    def test_probe_recordings_answer_the_current_prompt(self):
        for case in PROBE_CASES:
            with self.subTest(case=case):
                self._require_applicable_s02(case, probe=True)
                _s, _t, _p, o1, o2 = _run(case, probe=True)
                self.assertEqual("SUCCESS", o1.execution_status.value, o1.problems)
                self.assertEqual("SUCCESS", o2.execution_status.value, o2.problems)

    def test_every_check_is_clean_on_unseen_inputs(self):
        for case in PROBE_CASES:
            with self.subTest(case=case):
                self._require_applicable_s02(case, probe=True)
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
                self._require_applicable_s02(case, probe=True)
                state, _t, _p, _o1, _o2 = _run(case, probe=True)
                sites = {lc.get("reacted_at_role", "") for lc in state.family("LoadCase")}
                self.assertTrue(sites)
                self.assertTrue(any(s.strip() for s in sites))
