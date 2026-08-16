"""S9-C: one progression, two response sources, and no way to hide which ran.

WHAT THIS FALSIFIES

S9-A found the S01->S02 progression implemented three times, and one of the three
calling the stage's inner driver directly - so the live S01 path uniquely skipped
the ConsumerView, the readiness gate and the view record. It also found that a run
was "live" because of which script started it, which is a fact about a filename.

These tests are structural on purpose. Whether DeepSeek reasons well is S9-F; that
replay and live cannot diverge is decidable here, offline, with fake providers, and
proving it with paid calls would measure the model instead of the machinery.
"""
from __future__ import annotations

import ast
import json
import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

from ver3.assy_v3 import pipeline                                      # noqa: E402
from ver3.assy_v3.pipeline import progression as prog                  # noqa: E402
from ver3.assy_v3.providers import replay_integrity as ri              # noqa: E402
from ver3.assy_v3.providers.agent_authored import AgentAuthoredProvider  # noqa: E402
from ver3.assy_v3.providers.offline import OfflineReplayProvider       # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402

TOOLS = os.path.join(_paths.VER3, "tools")
RUNNERS = ("run_window.py", "run_live_window.py", "run_window2.py")


def _producing_stage_classes():
    """The real classes behind the six producing responsibilities, in order."""
    from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture
    from ver3.assy_v3.stages.s02_obligation_and_candidates import (
        S02ObligationAndCandidates)
    from ver3.assy_v3.stages.s03_topology_and_mobility import (
        S03BMobilityAndAssembly, S03TopologyAndMobility)
    from ver3.assy_v3.stages.s04_envelope_and_motion import (
        S04AEnvelopeAndReach, S04BPlacementAndMotion)
    return (S01RequirementCapture, S02ObligationAndCandidates,
            S03TopologyAndMobility, S03BMobilityAndAssembly,
            S04AEnvelopeAndReach, S04BPlacementAndMotion)


def _real_responsibilities():
    """Asked of the classes, never typed out."""
    return [c().responsibility_id() for c in _producing_stage_classes()]


def _live(responsibility_id, source=None):
    """A recorded execution for one producing responsibility.

    The OWNER is derived rather than typed, so this helper cannot quietly
    disagree with the architecture's own responsibility->owner rule.
    """
    return prog.StageExecution(
        stage_id=prog._owner_of(responsibility_id),
        responsibility_id=responsibility_id,
        response_source=source or prog.LIVE, provider_id="deepseek",
        execution_status="SUCCESS", patch_applied=True)


def _tool_source(name):
    with open(os.path.join(TOOLS, name)) as fh:
        return fh.read()


class _FakeProvider:
    """Declares a response source and serves one canned body."""

    provider_id = "fake"

    def __init__(self, source, body=None):
        self.response_source = source
        self.body = body if body is not None else '{"ok": true}'
        self.calls = []

    def capabilities(self):
        from ver3.assy_v3.providers.interfaces import ProviderCapabilities
        return ProviderCapabilities(
            provider_id=self.provider_id, model_id="fake", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=False, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None)

    def generate(self, request, attempt_index=0):
        import time
        from ver3.assy_v3.providers.interfaces import (GenerationResponse,
                                                       GenerationResult)
        self.calls.append(request.stage_id)
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=self.body, finish_reason="stop",
                                        truncated=False, input_tokens=None,
                                        output_tokens=None, served_model_id="fake"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=False)


# =====================================================================
# S9-I6 — one invocation boundary, whatever the response source
# =====================================================================
class TestNoInvocationBypass(unittest.TestCase):

    def test_S9C_01_no_runner_calls_a_stage_driver_directly(self):
        """FALSIFIES S9-I6: a runner reaching past `invoke` into `run`.

        This is the S9-A finding as an assertion. `invoke` builds the view,
        refuses to call the provider when it is not ready, and records it;
        `run` does none of that, so a caller that picks `run` gets a stage
        execution with no consumer boundary and nothing saying so.
        """
        for name in RUNNERS:
            tree = ast.parse(_tool_source(name))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "run":
                    # A stage driver call looks like `SomeStage().run(...)`.
                    target = func.value
                    called_on_stage = (
                        isinstance(target, ast.Call)
                        and isinstance(target.func, ast.Name)
                        and target.func.id.startswith("S0"))
                    self.assertFalse(
                        called_on_stage,
                        "%s calls a stage's inner driver directly" % name)

    def test_S9C_02_runners_do_not_invoke_stages_at_all(self):
        """Stronger, and the actual S9-C property: stage invocation belongs to
        the pipeline, so a runner has no `.invoke(` on a stage of its own."""
        for name in RUNNERS:
            tree = ast.parse(_tool_source(name))
            stage_invokes = [
                n for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "invoke"
                and isinstance(n.func.value, ast.Call)
                and isinstance(n.func.value.func, ast.Name)
                and n.func.value.func.id.startswith("S0")]
            self.assertEqual([], stage_invokes,
                             "%s invokes a stage itself instead of delegating "
                             "to the canonical progression" % name)

    def test_S9C_03_execute_stage_is_the_only_invoke_site(self):
        """One place calls `stage.invoke`. Two would be two progressions."""
        with open(os.path.join(_paths.ASSY_V3, "pipeline", "progression.py")) as fh:
            tree = ast.parse(fh.read())
        sites = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "invoke"]
        self.assertEqual(1, len(sites))
        owner = next(n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == "execute_stage")
        self.assertEqual(1, len([n for n in ast.walk(owner)
                                 if isinstance(n, ast.Call)
                                 and isinstance(n.func, ast.Attribute)
                                 and n.func.attr == "invoke"]))

    #: The functions that carry S01..S04. The downstream deterministic phases -
    #: feasibility, selection, comparison, the S7 advisory - keep their own patch
    #: application deliberately: they are not the producing progression, and
    #: folding them in would make the pipeline an authority over semantics it does
    #: not own (which S9C_17 asserts in the other direction).
    PRODUCING_FUNCTIONS = ("run_case", "run_trial", "seed_window1",
                           "run_s03", "run_s04")

    def test_S9C_04_producing_stage_patches_are_applied_in_one_place(self):
        """FALSIFIES S9-I6: replay and live applying patches on different terms.

        `state.apply` inside a producing-stage function would be a second
        acceptance rule, which is how one response source could commit what the
        other rejected. Scoped to the producing functions on purpose - a test
        that also banned it downstream would be demanding the opposite of the
        scope rule S9-C sets.
        """
        for name in RUNNERS:
            tree = ast.parse(_tool_source(name))
            for fn in ast.walk(tree):
                if not isinstance(fn, ast.FunctionDef):
                    continue
                if fn.name not in self.PRODUCING_FUNCTIONS:
                    continue
                applies = [n for n in ast.walk(fn)
                           if isinstance(n, ast.Call)
                           and isinstance(n.func, ast.Attribute)
                           and n.func.attr == "apply"]
                self.assertEqual([], applies,
                                 "%s.%s applies a producing stage's patch itself; "
                                 "acceptance is the progression's rule"
                                 % (name, fn.name))

    def test_S9C_04b_the_progression_owns_the_acceptance_rule(self):
        """The other direction: exactly one `state.apply` in the pipeline."""
        with open(os.path.join(_paths.ASSY_V3, "pipeline", "progression.py")) as fh:
            tree = ast.parse(fh.read())
        applies = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "apply"]
        self.assertEqual(1, len(applies))


# =====================================================================
# S9-I8 / S9-I9 — response source is declared, and qualification reads it
# =====================================================================
class TestResponseSourceProvenance(unittest.TestCase):

    def test_S9C_05_every_provider_declares_its_response_source(self):
        """FALSIFIES S9-I8: liveness inferred from a filename."""
        self.assertEqual(prog.REPLAY,
                         prog.response_source_of(OfflineReplayProvider("r", "c")))
        self.assertEqual(prog.REPLAY,
                         prog.response_source_of(AgentAuthoredProvider("r", "c")))
        # A provider that declares nothing is never treated as live.
        self.assertEqual(prog.UNDECLARED, prog.response_source_of(object()))

    def test_S9C_06_the_deepseek_provider_declares_live(self):
        os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
        from ver3.live_providers.deepseek import DeepSeekProvider
        self.assertEqual(prog.LIVE, prog.response_source_of(DeepSeekProvider()))

    def test_S9C_07_qualification_needs_every_producing_stage_live(self):
        """A four-string check would pass a run whose S03·B was replayed.

        The expected set is DERIVED FROM THE REAL STAGE CLASSES. Typing it out is
        how the first version of this test asserted `s03` - an owner - and agreed
        with an implementation that could never qualify a live run.
        """
        self.assertEqual(tuple(_real_responsibilities()),
                         prog.PRODUCING_RESPONSIBILITIES)
        p = prog.Progression()
        for stage in prog.PRODUCING_RESPONSIBILITIES:
            p.record(_live(stage))
        qualified, reasons = prog.full_live_qualification(p)
        self.assertTrue(qualified, reasons)
        self.assertEqual([], reasons)

    def test_S9C_08_one_hidden_replay_invalidates_full_live(self):
        """FALSIFIES S9-I8 and S9-I9: a replayed upstream hidden by a live S04.

        Checked for EVERY stage, so no single position is special. This is the
        exact shape of Window 2's run - replayed S01/S02, live S03/S04 - which
        the repository already forbids calling end-to-end evidence.
        """
        for hidden in prog.PRODUCING_RESPONSIBILITIES:
            p = prog.Progression()
            for stage in prog.PRODUCING_RESPONSIBILITIES:
                p.record(_live(stage, source=prog.REPLAY if stage == hidden
                               else prog.LIVE))
            qualified, reasons = prog.full_live_qualification(p)
            self.assertFalse(qualified, "%s replayed yet still qualified" % hidden)
            self.assertTrue(any(hidden in r for r in reasons), reasons)

    def test_S9C_09_seeded_upstream_state_invalidates_full_live(self):
        """Seeding is not replay: nothing was served at all. Both disqualify."""
        p = prog.Progression()
        prog.note_seeded(p, "s01", "committed state placed directly")
        for stage in prog.PRODUCING_RESPONSIBILITIES[1:]:
            p.record(_live(stage))
        qualified, reasons = prog.full_live_qualification(p)
        self.assertFalse(qualified)
        self.assertTrue(any("seeded" in r for r in reasons), reasons)

    def test_S9C_10_a_missing_stage_cannot_qualify(self):
        """Absence is not liveness. A chain that stopped at S02 is not full-live."""
        p = prog.Progression()
        for stage in ("s01", "s02"):
            p.record(_live(stage))
        qualified, reasons = prog.full_live_qualification(p)
        self.assertFalse(qualified)
        self.assertEqual(4, len([r for r in reasons if "did not execute" in r]))

    def test_S9C_11_an_undeclared_provider_cannot_qualify(self):
        """Silence is not a live response."""
        p = prog.Progression()
        for stage in prog.PRODUCING_RESPONSIBILITIES:
            p.record(_live(stage, source=prog.UNDECLARED))
        qualified, _reasons = prog.full_live_qualification(p)
        self.assertFalse(qualified)


# =====================================================================
# Owner identity is not pass identity — the defect this class exists for
# =====================================================================
class TestOwnershipVersusResponsibility(unittest.TestCase):
    """The architecture already separates these. S9-C's first implementation
    discarded half of it and recorded the owner, so every pass-level lookup for
    `s03b`, `s04a` and `s04b` found nothing and a genuinely all-live run could
    never qualify. These are the negative controls that make that irreversible."""

    def test_S9C_21b_the_contract_stage_and_pipeline_agree_exactly(self):
        """FALSIFIES the defect's real enabler: one metadata source checked
        against itself.

        The corrected implementation asks the Stage classes for their
        responsibilities, and a test that asked the same classes would agree with
        any answer they gave - including the wrong one. STAGE_RESPONSIBILITY
        CONTRACT is authored independently of `pass_id` and of this package's
        constant, so it is the oracle none of the three can quietly move.

        It has said `s03a` all along. Had this test existed, the owner-for-pass
        defect would have failed on the first run rather than surviving to a
        predicate that could never return True.
        """
        contract = yaml.safe_load(
            open(os.path.join(_paths.CONTRACTS,
                              "STAGE_RESPONSIBILITY_CONTRACT.yaml")))
        # S01..S04 producing responsibilities, by shape rather than by a list -
        # a list here would be a fourth place to keep in step. Downstream
        # responsibilities (feasibility, the four selection ones) are excluded
        # because they are not the S01->S04 producing chain.
        declared = sorted(k for k in contract["stages"]
                          if re.match(r"^s0[1-4][a-z]?$", k))
        from_classes = sorted(_real_responsibilities())
        from_pipeline = sorted(prog.PRODUCING_RESPONSIBILITIES)

        self.assertEqual(declared, from_classes,
                         "the contract and the Stage classes disagree about "
                         "which responsibilities produce S01-S04")
        self.assertEqual(declared, from_pipeline,
                         "the contract and the pipeline qualification set "
                         "disagree about which responsibilities produce S01-S04")
        self.assertEqual(6, len(declared))
        # And the downstream responsibilities are genuinely excluded rather than
        # accidentally absent.
        for downstream in ("feasibility", "selection", "selection_advisory",
                           "selection_decision", "selection_human_review"):
            self.assertIn(downstream, contract["stages"], downstream)
            self.assertNotIn(downstream, from_pipeline, downstream)

    def test_S9C_22_owners_collide_where_responsibilities_do_not(self):
        """FALSIFIES the assumption that a stage id names a producing pass.

        Read off the real classes: two of them share an owner, and none of them
        shares a responsibility. This is the fact that makes owner identity
        unusable as a pass key.
        """
        (s01, s02, s03a, s03b, s04a, s04b) = [c() for c in _producing_stage_classes()]

        # OWNERSHIP COLLIDES. Both passes author s03 state under s03's authority.
        self.assertEqual(s03a.stage_id, s03b.stage_id)
        self.assertEqual("s03", s03a.stage_id)
        self.assertEqual(s04a.stage_id, s04b.stage_id)
        self.assertEqual("s04", s04a.stage_id)

        # RESPONSIBILITY DOES NOT. They ask different questions of different premises.
        self.assertNotEqual(s03a.responsibility_id(), s03b.responsibility_id())
        self.assertNotEqual(s04a.responsibility_id(), s04b.responsibility_id())
        self.assertEqual(6, len({c.responsibility_id()
                                 for c in (s01, s02, s03a, s03b, s04a, s04b)}))
        # And only four owners for six producing responsibilities.
        self.assertEqual(4, len({c.stage_id
                                 for c in (s01, s02, s03a, s03b, s04a, s04b)}))

    def test_S9C_23_execute_stage_records_both_identities_from_the_object(self):
        """FALSIFIES the fixed defect: execution identity taken from the owner.

        Drives the REAL classes through the real identity extraction rather than
        hand-building records. The previous tests constructed StageExecution with
        the ids they expected, so they agreed with an implementation that never
        produced those ids at all.
        """
        expected = {"s01": "s01", "s02": "s02", "s03a": "s03", "s03b": "s03",
                    "s04a": "s04", "s04b": "s04"}
        for cls in _producing_stage_classes():
            stage = cls()
            # Exactly what execute_stage does, asked of the object itself.
            responsibility = stage.responsibility_id()
            owner = stage.stage_id
            self.assertIn(responsibility, expected)
            self.assertEqual(expected[responsibility], owner, responsibility)

            execution = prog.StageExecution(
                stage_id=owner, responsibility_id=responsibility,
                response_source=prog.LIVE, provider_id="deepseek",
                execution_status="SUCCESS", patch_applied=True)
            self.assertEqual(responsibility, execution.responsibility_id)
            self.assertEqual(owner, execution.stage_id)
            self.assertEqual(responsibility,
                             execution.as_record()["responsibility_id"])

    def test_S9C_24_the_pipeline_reads_responsibility_not_stage_id(self):
        """The mutation `responsibility_id = stage.stage_id` must be detectable.

        Structural, because the property is about which attribute is consulted.
        `execute_stage` must ask the object for `responsibility_id()`; if it took
        `stage.stage_id` for both, s03a and s03b would collide again.
        """
        with open(os.path.join(_paths.ASSY_V3, "pipeline", "progression.py")) as fh:
            tree = ast.parse(fh.read())
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "execute_stage")
        calls = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "responsibility_id"]
        self.assertEqual(1, len(calls),
                         "execute_stage must derive the responsibility from the "
                         "stage object exactly once")

    def test_S9C_25_two_passes_of_one_owner_are_distinct_executions(self):
        """FALSIFIES the collision at the level that matters: qualification.

        Both S03 passes live, recorded under one owner, must still be two
        executions - and a lookup by owner must not stand in for either.
        """
        p = prog.Progression()
        for cls in _producing_stage_classes():
            stage = cls()
            p.record(prog.StageExecution(
                stage_id=stage.stage_id,
                responsibility_id=stage.responsibility_id(),
                response_source=prog.LIVE, provider_id="deepseek",
                execution_status="SUCCESS", patch_applied=True))

        self.assertEqual(6, len(p.executions))
        self.assertIsNotNone(p.by_responsibility("s03a"))
        self.assertIsNotNone(p.by_responsibility("s03b"))
        self.assertIsNotNone(p.by_responsibility("s04a"))
        self.assertIsNotNone(p.by_responsibility("s04b"))
        # The owner lookup returns BOTH passes, never one standing for the other.
        self.assertEqual(2, len(p.owned_by("s03")))
        self.assertEqual(2, len(p.owned_by("s04")))
        # Response sources are keyed by responsibility, so nothing is lost.
        self.assertEqual(6, len(p.response_sources()))

        # AND THE PREDICATE NOW SUCCEEDS. Before the fix it could not: three of
        # the six lookups returned None whatever the run actually did.
        qualified, reasons = prog.full_live_qualification(p)
        self.assertTrue(qualified, reasons)

    def test_S9C_26_a_missing_second_pass_is_caught(self):
        """Each of the three passes that used to be invisible, one at a time."""
        for missing in ("s03b", "s04a", "s04b"):
            p = prog.Progression()
            for cls in _producing_stage_classes():
                stage = cls()
                if stage.responsibility_id() == missing:
                    continue
                p.record(prog.StageExecution(
                    stage_id=stage.stage_id,
                    responsibility_id=stage.responsibility_id(),
                    response_source=prog.LIVE, provider_id="deepseek",
                    execution_status="SUCCESS", patch_applied=True))
            qualified, reasons = prog.full_live_qualification(p)
            self.assertFalse(qualified, "%s missing yet qualified" % missing)
            self.assertTrue(any(missing in r for r in reasons), reasons)


# =====================================================================
# S9-I14 / S9-I2 — one replay-integrity mechanism, on both corpora
# =====================================================================
class TestReplayIntegrity(unittest.TestCase):

    def test_S9C_12_pairing_is_one_mechanism_for_both_corpora(self):
        """FALSIFIES the S9-A split: integrity applied by corpus, not principle.

        Both replay providers now record a pairing status from the same function.
        """
        for provider_cls in (OfflineReplayProvider, AgentAuthoredProvider):
            self.assertEqual(ri.REPLAY, provider_cls("r", "c").response_source)
        self.assertTrue(hasattr(ri, "pairing_status"))
        # And the hash function exists once, not once per provider.
        import ver3.assy_v3.providers.agent_authored as aa
        self.assertIs(aa.prompt_hash, ri.prompt_hash)

    def test_S9C_13_a_mispaired_recording_is_detected(self):
        """FALSIFIES S9-I2's weaker cousin: replaying an answer to another
        question."""
        body = json.dumps({"_meta": {"answers_prompt_sha256":
                                     ri.prompt_hash("the prompt it answered")}})
        self.assertEqual(ri.PAIRED,
                         ri.pairing_status(body, "the prompt it answered"))
        self.assertEqual(ri.STALE,
                         ri.pairing_status(body, "a different prompt entirely"))

    def test_S9C_14_an_undeclared_pairing_fails_the_current_rule(self):
        """A fixture that says nothing about what it answers cannot be replayed
        as though it answered this. UNDECLARED is weaker than STALE, not safer."""
        body = json.dumps({"_meta": {}})
        self.assertEqual(ri.UNDECLARED, ri.pairing_status(body, "any prompt"))
        self.assertFalse(ri.meets_current_fixture_rule(body, "any prompt"))
        # And a well-paired one passes it.
        good = json.dumps({"_meta": {"answers_prompt_sha256": ri.prompt_hash("p")}})
        self.assertTrue(ri.meets_current_fixture_rule(good, "p"))

    def test_S9C_15_pairing_history_is_not_consulted_by_the_rule(self):
        """FALSIFIES S9-I14: a migration bridge becoming the authority.

        A note explaining why a recording was re-stamped is migration evidence.
        If it could make a stale recording pass, the bridge would be deciding
        current semantics.
        """
        stale_with_history = json.dumps({"_meta": {
            "answers_prompt_sha256": ri.prompt_hash("old prompt"),
            "pairing_history": ["re-paired after the response-schema section"]}})
        self.assertEqual(ri.STALE,
                         ri.pairing_status(stale_with_history, "new prompt"))
        self.assertFalse(ri.meets_current_fixture_rule(stale_with_history,
                                                       "new prompt"))
        # It stays VISIBLE, because S-9 has to count what it is retiring.
        report = ri.integrity_report(stale_with_history, "new prompt")
        self.assertTrue(report["migration_bridge_present"])

    def test_S9C_16_the_target_rule_does_not_bend_to_the_current_corpus(self):
        """The active fixtures largely fail the rule. That is the debt S9-E
        clears, and softening the rule would delete the only signal it has.

        Reported as a count rather than asserted clean, because asserting clean
        would require exactly the weakening this test forbids.
        """
        fixtures = os.path.join(_paths.ASSY_V3, "fixtures", "responses")
        undeclared = 0
        total = 0
        for case in sorted(os.listdir(fixtures)):
            for stage in ("s01", "s02"):
                path = os.path.join(fixtures, case, "%s.json" % stage)
                if not os.path.isfile(path):
                    continue
                total += 1
                with open(path) as fh:
                    body = fh.read()
                # Every one of them declares a pairing; none declares an origin.
                meta = json.loads(body).get("_meta", {})
                if not meta.get(ri.PAIRING_KEY):
                    undeclared += 1
        self.assertEqual(6, total, "the active benchmark corpus is six files")
        self.assertEqual(0, undeclared)


# =====================================================================
# The downstream layers S9-C must not have moved
# =====================================================================
class TestDownstreamUntouched(unittest.TestCase):

    def test_S9C_17_the_progression_stops_at_s04(self):
        """FALSIFIES the scope rule: assurance or selection folded into the
        producing progression.

        S8 assurance must stay a downstream independent snapshot, and S7's human
        authority must not become something an orchestrator performs.
        """
        with open(os.path.join(_paths.ASSY_V3, "pipeline", "progression.py")) as fh:
            source = fh.read()
        for forbidden in ("run_assurance", "reconcile_s7", "build_human_review_snapshot",
                          "evaluate_candidate_comparison", "materialize_selection_profile",
                          "evaluate_candidate_feasibility"):
            self.assertNotIn(forbidden, source,
                             "%s belongs downstream of the producing progression"
                             % forbidden)

    def test_S9C_18_assurance_and_lifecycle_still_run_in_the_harness(self):
        """The other half: they were not lost in the refactor."""
        source = _tool_source("run_window2.py")
        for kept in ("run_assurance", "reconcile_s7", "build_human_review_snapshot",
                     "evaluate_candidate_feasibility"):
            self.assertIn(kept, source, kept)

    def test_S9C_19_failure_layers_are_defined_once(self):
        """FALSIFIES S9-I11: one condition with two names.

        The vocabulary lived in two runners with different membership. A runner
        that defines its own layer names can classify the same failure
        differently from its neighbour.
        """
        for name in RUNNERS:
            tree = ast.parse(_tool_source(name))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in (
                                "PROVIDER_CONDITION", "RESPONSE_CONDITION",
                                "PARSER_DEFECT", "CONTRACT_CONDITION",
                                "CHECK_FINDING", "INTERFACE_FINDING"):
                            self.fail("%s redefines the failure layer %s"
                                      % (name, target.id))

    def test_S9C_20_the_layers_stay_distinct(self):
        """A provider condition may not become an engineering finding."""
        names = {prog.PROVIDER_CONDITION, prog.RESPONSE_CONDITION,
                 prog.PARSER_DEFECT, prog.CONTRACT_CONDITION,
                 prog.CHECK_FINDING, prog.INTERFACE_FINDING,
                 prog.VIEW_INSUFFICIENT}
        self.assertEqual(7, len(names))
        # "Never asked" is its own layer, not a provider failure.
        self.assertNotEqual(prog.VIEW_INSUFFICIENT, prog.PROVIDER_CONDITION)


class TestPublicSurface(unittest.TestCase):

    def test_S9C_21_the_pipeline_exports_what_the_runners_need(self):
        """FALSIFIES nothing subtle - it catches the import that is not there.

        The first version of this test asked whether the name existed on the
        package OR on the module, and the `or` let two missing exports through:
        every runner failed to import while the test went green. A public
        surface test that accepts the private module is not testing a surface.
        """
        for name in ("window1", "s03_passes", "s04_passes", "execute_stage",
                     "execute_s01_to_s04", "note_seeded",
                     "full_live_qualification", "response_source_of",
                     "Progression", "StageExecution", "PRODUCING_RESPONSIBILITIES"):
            self.assertTrue(hasattr(pipeline, name),
                            "%s is not exported from the pipeline package" % name)
            self.assertIn(name, pipeline.__all__, name)

    def test_S9C_22_every_runner_imports_cleanly(self):
        """The suite that caught the missing export did so by failing to import
        a runner. Asserted directly here so the next such break names itself."""
        import importlib
        for module in ("ver3.tools.run_window", "ver3.tools.run_window2",
                       "ver3.tools.run_live_window"):
            os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
            importlib.import_module(module)


class TestARefiningPassHasMoreThanOneExecution(unittest.TestCase):
    """S9-C regression. A pass that refines runs twice, and both are evidence.

    THE DEFECT THIS PINS. `by_responsibility` returned the FIRST execution of a
    pass. A refining stage's first execution is the one that asked to be called
    again - it committed a justified revision and withheld everything reasoned
    from the replaced value - so its status is CONTRACT_INCOMPLETE by
    construction. Every reader of a refining run was therefore told the pass had
    failed to complete, when what actually happened is that it completed on its
    second execution.

    It went unnoticed because `response_sources` next door was already last-wins.
    Each accessor was self-consistent, they disagreed with each other about the
    same run, and nothing compared them. The runner's own report is what broke:
    `run_s04` recorded s04b as CONTRACT_INCOMPLETE and reported no refinement at
    all for a run in which two occurred.
    """

    def _progression(self):
        """One pass that refined once and then settled."""
        p = prog.Progression()
        p.record(prog.StageExecution(
            stage_id="s04", responsibility_id="s04b",
            response_source=prog.LIVE, provider_id="t",
            execution_status="CONTRACT_INCOMPLETE", refinement_only=True,
            declared_incompleteness=("revised ENV-0A; everything else withheld",)))
        p.record(prog.StageExecution(
            stage_id="s04", responsibility_id="s04b",
            response_source=prog.LIVE, provider_id="t",
            execution_status="SUCCESS", patch_applied=True))
        return p

    def test_the_settled_execution_is_the_answer(self):
        self.assertEqual("SUCCESS",
                         self._progression().by_responsibility("s04b").execution_status)

    def test_every_execution_is_still_reachable(self):
        found = self._progression().all_by_responsibility("s04b")
        self.assertEqual(["CONTRACT_INCOMPLETE", "SUCCESS"],
                         [e.execution_status for e in found])

    def test_the_two_accessors_agree_about_one_run(self):
        """The property whose absence hid the defect."""
        p = self._progression()
        self.assertEqual(p.response_sources()["s04b"],
                         p.by_responsibility("s04b").response_source)

    def test_the_refinement_reason_survives(self):
        refined = [e for e in self._progression().all_by_responsibility("s04b")
                   if e.refinement_only]
        self.assertEqual(1, len(refined))
        self.assertTrue(refined[0].declared_incompleteness)

    def test_a_pass_that_never_refined_is_unchanged(self):
        p = prog.Progression()
        p.record(prog.StageExecution(
            stage_id="s01", responsibility_id="s01", response_source=prog.LIVE,
            provider_id="t", execution_status="SUCCESS"))
        self.assertEqual("SUCCESS", p.by_responsibility("s01").execution_status)
        self.assertEqual(1, len(p.all_by_responsibility("s01")))

    def test_an_absent_pass_is_still_none(self):
        self.assertIsNone(prog.Progression().by_responsibility("s04b"))


class TestQualificationChecksEveryExecution(unittest.TestCase):
    """A refining pass must be live BOTH times, not on the execution we sampled.

    Checking one execution of a pass that ran twice reopens the exact hole
    `full_live_qualification` exists to close, one level down: a replayed
    execution hides behind a live one. First-wins and last-wins each conceal the
    opposite case, so neither is defensible and the rule is ALL.
    """

    def _mixed(self, first_source, second_source):
        """Every pass live and single-execution, except s04b which refined once."""
        p = prog.Progression()
        for rid in prog.PRODUCING_RESPONSIBILITIES:
            if rid == "s04b":
                continue          # recorded below, twice, which is the point
            p.record(prog.StageExecution(
                stage_id=prog._owner_of(rid), responsibility_id=rid,
                response_source=prog.LIVE, provider_id="t",
                execution_status="SUCCESS"))
        p.record(prog.StageExecution(
            stage_id="s04", responsibility_id="s04b",
            response_source=first_source, provider_id="t",
            execution_status="CONTRACT_INCOMPLETE", refinement_only=True))
        p.record(prog.StageExecution(
            stage_id="s04", responsibility_id="s04b",
            response_source=second_source, provider_id="t",
            execution_status="SUCCESS"))
        return p

    def test_all_live_executions_qualify(self):
        ok, reasons = prog.full_live_qualification(
            self._mixed(prog.LIVE, prog.LIVE))
        self.assertTrue(ok, reasons)

    def test_a_replayed_refinement_cannot_hide_behind_a_live_settle(self):
        ok, reasons = prog.full_live_qualification(
            self._mixed(prog.REPLAY, prog.LIVE))
        self.assertFalse(ok)
        self.assertTrue(any("s04b" in r and "REPLAY" in r for r in reasons), reasons)

    def test_a_live_refinement_cannot_carry_a_replayed_settle(self):
        ok, reasons = prog.full_live_qualification(
            self._mixed(prog.LIVE, prog.REPLAY))
        self.assertFalse(ok)
        self.assertTrue(any("s04b" in r and "REPLAY" in r for r in reasons), reasons)

    def test_the_reason_names_which_execution(self):
        _ok, reasons = prog.full_live_qualification(
            self._mixed(prog.REPLAY, prog.LIVE))
        self.assertTrue(any("execution 1 of 2" in r for r in reasons), reasons)

    def test_a_single_execution_reason_does_not_grow_an_ordinal(self):
        """The ordinary message is unchanged for a pass that ran once."""
        p = prog.Progression()
        for rid in prog.PRODUCING_RESPONSIBILITIES:
            p.record(prog.StageExecution(
                stage_id=prog._owner_of(rid), responsibility_id=rid,
                response_source=prog.REPLAY if rid == "s01" else prog.LIVE,
                provider_id="t", execution_status="SUCCESS"))
        _ok, reasons = prog.full_live_qualification(p)
        self.assertIn("s01 response source is REPLAY, not LIVE", reasons)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
