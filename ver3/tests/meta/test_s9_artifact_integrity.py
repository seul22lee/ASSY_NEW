"""S9-D: what a fixture must prove before it may be replayed as evidence.

WHAT THIS FALSIFIES

S9-A found integrity applied by corpus rather than by principle, and S9-C found
that replay addressed a producing pass by its OWNER - so `s03a` and `s03b`
resolved to one file and a substitution between them was undetectable. Neither
was a fixture-content problem. Both were identity problems.

A current fixture must bind four identities: which source it answers, which
producing pass produced it, which raw response it is, and which run promoted it.
Each test below removes or corrupts exactly one and requires detection.

NO PAID CALLS. Every response here is synthetic. Whether DeepSeek reasons well is
S9-F; whether this machinery can be lied to is decidable offline.
"""
from __future__ import annotations

import hashlib
import json
import os
import unittest

from . import _fixtures, _paths                                        # noqa: F401

from ver3.assy_v3.pipeline import PRODUCING_RESPONSIBILITIES           # noqa: E402
from ver3.assy_v3.pipeline import promotion as pr                      # noqa: E402
from ver3.assy_v3.providers import replay_integrity as ri              # noqa: E402
from ver3.assy_v3.providers.interfaces import GenerationRequest        # noqa: E402
from ver3.assy_v3.providers.offline import OfflineReplayProvider       # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.tools import artifact_inventory as inv                       # noqa: E402

PROMPT = "the prompt this fixture answers"
SOURCE = hashlib.sha256(b"a request").hexdigest()


def an_attempt(**kw) -> pr.AttemptOutcome:
    fields = dict(responsibility_id="s03b", source_sha256=SOURCE,
                  model_run_id="run-1|s03|sa2|a1", attempt_index=1,
                  stage=pr.ACCEPTED, raw_response=json.dumps({"answer": 1}))
    fields.update(kw)
    return pr.AttemptOutcome(**fields)


# =====================================================================
# Replay addressing is by producing responsibility
# =====================================================================
class TestResponsibilityAddressing(unittest.TestCase):

    def test_S9D_01_the_request_carries_owner_and_pass_separately(self):
        """FALSIFIES the identity collapse at the provider boundary."""
        req = GenerationRequest(purpose="p", stage_id="s03", prompt_text="x",
                                max_output_tokens=1, deadline_s=1.0,
                                responsibility_id="s03b")
        self.assertEqual("s03", req.stage_id)          # ownership, unchanged
        self.assertEqual("s03b", req.responsibility_id)
        self.assertEqual("s03b", ri.producing_identity(req))

    def test_S9D_02_a_request_without_a_pass_falls_back_to_the_owner(self):
        """Correct for s01 and s02, where the two identities are one string."""
        req = GenerationRequest(purpose="p", stage_id="s01", prompt_text="x",
                                max_output_tokens=1, deadline_s=1.0)
        self.assertEqual("s01", ri.producing_identity(req))

    def test_S9D_03_the_stage_driver_supplies_the_responsibility(self):
        """It must come from the stage, not from a caller-side mapping."""
        import ast
        with open(os.path.join(_paths.ASSY_V3, "stages", "base.py")) as fh:
            tree = ast.parse(fh.read())
        call = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.Call)
                    and getattr(n.func, "id", "") == "GenerationRequest")
        kwargs = {k.arg: k.value for k in call.keywords}
        self.assertIn("responsibility_id", kwargs)
        # ... and its value is the stage asking itself.
        self.assertEqual("responsibility_id",
                         getattr(kwargs["responsibility_id"].func, "attr", None))

    def test_S9D_04_replay_resolves_by_pass_not_by_owner(self):
        """FALSIFIES the S9-C finding: one file serving two passes.

        Every pair that shares an owner must address a different artifact.
        """
        provider = OfflineReplayProvider("/nowhere", "CASE")
        seen = {}
        for responsibility in PRODUCING_RESPONSIBILITIES:
            req = GenerationRequest(purpose="p", stage_id=ri and "s03",
                                    prompt_text="x", max_output_tokens=1,
                                    deadline_s=1.0,
                                    responsibility_id=responsibility)
            result = provider.generate(req)
            # No file exists, so the interesting evidence is the path it looked for.
            self.assertIs(ExecutionStatus.PROVIDER_UNAVAILABLE,
                          result.execution_status)
            seen[responsibility] = result.error_detail
        self.assertEqual(6, len(set(seen.values())),
                         "two producing responsibilities resolved to one artifact")
        for pair in (("s03a", "s03b"), ("s04a", "s04b")):
            self.assertNotEqual(seen[pair[0]], seen[pair[1]], pair)

    def test_S9D_05_a_pass_substitution_is_rejected(self):
        """s03a's answer offered for s03b, and every other such swap."""
        for produced, requested in (("s03a", "s03b"), ("s03b", "s03a"),
                                    ("s04a", "s04b"), ("s04b", "s04a")):
            body = _fixture(responsibility=produced)
            problems = ri.verify_current_fixture(
                body, prompt_text=PROMPT, source_sha256=SOURCE,
                responsibility_id=requested)
            self.assertTrue(any(produced in p and requested in p for p in problems),
                            "%s served as %s was not caught: %s"
                            % (produced, requested, problems))


def _fixture(responsibility="s03b", source=SOURCE, prompt=PROMPT,
             model_run_id="run-1|s03|sa2|a1", answer=None, meta_extra=None,
             omit=()):
    raw = json.dumps(answer if answer is not None else {"answer": 1})
    meta = {ri.PAIRING_KEY: ri.prompt_hash(prompt),
            ri.SOURCE_KEY: source,
            ri.RESPONSIBILITY_KEY: responsibility,
            ri.RESPONSE_KEY: hashlib.sha256(raw.encode()).hexdigest(),
            ri.PROMOTION_KEY: model_run_id,
            ri.CONTENT_KEY: ri.canonical_content_hash(raw)}
    for key in omit:
        meta.pop(key, None)
    meta.update(meta_extra or {})
    body = json.loads(raw)
    body["_meta"] = meta
    return json.dumps(body)


# =====================================================================
# The four identities
# =====================================================================
class TestFixtureIntegrity(unittest.TestCase):

    def test_S9D_06_a_conforming_fixture_passes(self):
        self.assertEqual([], ri.verify_current_fixture(
            _fixture(), prompt_text=PROMPT, source_sha256=SOURCE,
            responsibility_id="s03b"))

    def test_S9D_07_each_missing_identity_is_named(self):
        """FALSIFIES a fixture that cannot say what it is."""
        for key in ri.REQUIRED_FIXTURE_IDENTITIES:
            problems = ri.verify_current_fixture(
                _fixture(omit=(key,)), prompt_text=PROMPT, source_sha256=SOURCE,
                responsibility_id="s03b")
            self.assertTrue(any(key in p for p in problems),
                            "missing %s was not reported: %s" % (key, problems))

    def test_S9D_08_a_fixture_for_another_source_is_rejected(self):
        """BM-001's answer replayed for BM-002."""
        other = hashlib.sha256(b"a different request").hexdigest()
        problems = ri.verify_current_fixture(
            _fixture(source=other), prompt_text=PROMPT, source_sha256=SOURCE,
            responsibility_id="s03b")
        self.assertTrue(any("source" in p for p in problems), problems)

    def test_S9D_09_a_changed_request_stales_the_pairing(self):
        """The source hash still matches; the question no longer does."""
        problems = ri.verify_current_fixture(
            _fixture(), prompt_text="a prompt built from changed upstream",
            source_sha256=SOURCE, responsibility_id="s03b")
        self.assertTrue(any("pairing is STALE" in p for p in problems), problems)

    def test_S9D_10_pairing_history_alone_cannot_rescue_a_fixture(self):
        """FALSIFIES S9-I14: the migration bridge as current authority.

        Everything current is wrong and the bridge asserts the pairing existed.
        It must still be rejected - and still be visible, because S-9 has to
        count what it is retiring.
        """
        body = _fixture(omit=ri.REQUIRED_FIXTURE_IDENTITIES,
                        meta_extra={ri.MIGRATION_BRIDGE_KEY: [
                            "re-paired after the response-schema section was added"]})
        problems = ri.verify_current_fixture(
            body, prompt_text="a different prompt", source_sha256=SOURCE,
            responsibility_id="s03b")
        self.assertTrue(problems)
        self.assertTrue(ri.integrity_report(body, PROMPT)["migration_bridge_present"])

    def test_S9D_11_one_source_identity_rule_covers_both_corpora(self):
        """FALSIFIES a probe-specific hash scheme.

        The benchmarks publish `request_sha256` in a manifest and the probes
        publish nothing, so the same function is computed over both and the
        benchmark's published value is what proves the function is the right one.
        """
        import yaml
        for bm in ("BM-001", "BM-002", "BM-003"):
            request = os.path.join(_paths.BENCHMARKS, bm, "source", "request.txt")
            manifest = yaml.safe_load(
                open(os.path.join(_paths.BENCHMARKS, bm, "source",
                                  "source_manifest.yaml")))
            self.assertEqual(manifest["request_sha256"],
                             ri.canonical_source_identity_of_file(request), bm)
        probes = os.path.join(_paths.ASSY_V3, "probes")
        for prb in sorted(os.listdir(probes)):
            request = os.path.join(probes, prb, "request.txt")
            if not os.path.isfile(request):
                continue
            identity = ri.canonical_source_identity_of_file(request)
            self.assertEqual(64, len(identity), prb)
            # No manifest is fabricated to obtain it.
            self.assertFalse(os.path.exists(
                os.path.join(probes, prb, "source_manifest.yaml")), prb)


# =====================================================================
# Promotion: provider success is not a fixture
# =====================================================================
class TestPromotionEligibility(unittest.TestCase):

    def test_S9D_12_only_an_accepted_attempt_may_be_promoted(self):
        """FALSIFIES the collapse of the whole ladder into "it worked"."""
        for stage in (pr.PROVIDER_FAILED, pr.RESPONSE_UNUSABLE, pr.PARSER_FAILED,
                      pr.CONTRACT_FAILED, pr.NOT_ACCEPTED):
            problems = pr.eligibility_problems(an_attempt(stage=stage))
            self.assertTrue(any(stage in p for p in problems), stage)
        self.assertEqual([], pr.eligibility_problems(an_attempt()))

    def test_S9D_13_a_hand_edited_response_can_never_be_promoted(self):
        """FALSIFIES S9-I3. Nothing else about the attempt overrides this."""
        problems = pr.eligibility_problems(an_attempt(hand_edited=True))
        self.assertTrue(any("hand" in p for p in problems), problems)
        with self.assertRaises(ValueError):
            pr.fixture_body(an_attempt(hand_edited=True), PROMPT)

    def test_S9D_14_missing_run_identity_blocks_promotion(self):
        problems = pr.eligibility_problems(an_attempt(model_run_id=""))
        self.assertTrue(any("model-run identity" in p for p in problems), problems)

    def test_S9D_15_promotion_packages_without_authoring(self):
        """FALSIFIES S9-I4: a fixture richer than the response it claims."""
        attempt = an_attempt(raw_response=json.dumps({"answer": 1, "keep": [2]}))
        body = pr.fixture_body(attempt, PROMPT)
        self.assertEqual([], ri.promotion_fidelity_problems(body,
                                                            attempt.raw_response))
        self.assertEqual([], ri.verify_current_fixture(
            body, prompt_text=PROMPT, source_sha256=SOURCE,
            responsibility_id="s03b"))

    def test_S9D_16_enrichment_and_deletion_are_both_caught(self):
        attempt = an_attempt(raw_response=json.dumps({"answer": 1, "keep": [2]}))
        good = json.loads(pr.fixture_body(attempt, PROMPT))

        enriched = dict(good, invented_fact="a clearance nobody computed")
        self.assertTrue(any("added" in p for p in ri.promotion_fidelity_problems(
            json.dumps(enriched), attempt.raw_response)))

        trimmed = {k: v for k, v in good.items() if k != "keep"}
        self.assertTrue(any("lost" in p for p in ri.promotion_fidelity_problems(
            json.dumps(trimmed), attempt.raw_response)))

        altered = dict(good, answer=999)
        self.assertTrue(ri.promotion_fidelity_problems(json.dumps(altered),
                                                       attempt.raw_response))

    def test_S9D_17_the_selection_rule_is_frozen_and_conformance_only(self):
        """FALSIFIES cherry-picking: a later attempt chosen for reading better."""
        first_bad = an_attempt(stage=pr.CONTRACT_FAILED, attempt_index=1,
                               raw_response=json.dumps({"answer": "malformed"}))
        first_good = an_attempt(attempt_index=2,
                                raw_response=json.dumps({"answer": "plain"}))
        later_nicer = an_attempt(attempt_index=3,
                                 raw_response=json.dumps({"answer": "elegant"}))
        decision = pr.select_for_promotion([first_bad, first_good, later_nicer])

        self.assertEqual(pr.FIRST_CONFORMING, decision["rule"])
        self.assertIs(first_good, decision["chosen"],
                      "the FIRST eligible attempt must win, not the best-looking")
        self.assertEqual(2, decision["eligible_count"])

    def test_S9D_18_failed_attempts_are_never_dropped(self):
        """FALSIFIES S9-I11: a corpus that shows only the try that worked."""
        attempts = [an_attempt(stage=pr.PROVIDER_FAILED, attempt_index=1),
                    an_attempt(stage=pr.PARSER_FAILED, attempt_index=2),
                    an_attempt(attempt_index=3)]
        decision = pr.select_for_promotion(attempts)
        ledger = pr.PromotionLedger()
        ledger.record(decision, promoted_path="fixtures/CASE/s03b.json")
        self.assertEqual(3, ledger.attempts_recorded())
        stages = [c["attempt"]["stage"] for c in decision["considered"]]
        self.assertEqual([pr.PROVIDER_FAILED, pr.PARSER_FAILED, pr.ACCEPTED], stages)

    def test_S9D_19_two_attempts_of_one_pass_keep_separate_identities(self):
        """A retry must not overwrite its predecessor's evidence."""
        decision = pr.select_for_promotion([
            an_attempt(stage=pr.PARSER_FAILED, attempt_index=1,
                       model_run_id="run-1|s03|sa2|a1"),
            an_attempt(attempt_index=2, model_run_id="run-1|s03|sa2|a2")])
        ids = [c["attempt"]["model_run_id"] for c in decision["considered"]]
        self.assertEqual(2, len(set(ids)))


# =====================================================================
# The inventory, and exactly one disposition each
# =====================================================================
class TestArtifactInventory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.inv = inv.inventory()

    def test_S9D_20_every_replay_resolvable_artifact_is_inventoried(self):
        """FALSIFIES an artifact becoming consumable without a disposition.

        Derived by resolution rather than listed, so a new file that a replay
        provider could serve appears here the moment it exists.
        """
        resolvable = [a for a in self.inv["active"] if a["resolvable"]]
        for artifact in resolvable:
            self.assertIn(artifact["responsibility"], PRODUCING_RESPONSIBILITIES)
            self.assertEqual(inv.CURRENT_REGENERATION_TARGET,
                             artifact["disposition"])
        self.assertEqual(sorted(a["path"] for a in resolvable),
                         self.inv["regeneration_targets"])

    def test_S9D_21_no_artifact_carries_two_dispositions(self):
        seen = {}
        for group in ("active", "historical_live", "frozen"):
            for artifact in self.inv[group]:
                path = artifact["path"]
                self.assertNotIn(path, seen,
                                 "%s classified twice: %s and %s"
                                 % (path, seen.get(path), artifact["disposition"]))
                seen[path] = artifact["disposition"]
        self.assertIn(seen[self.inv["regeneration_targets"][0]],
                      inv.DISPOSITIONS)

    def test_S9D_22_historical_live_artifacts_are_never_current(self):
        """FALSIFIES S9-A's frozen policy being quietly reversed."""
        self.assertTrue(self.inv["historical_live"])
        for artifact in self.inv["historical_live"]:
            self.assertEqual(inv.HISTORICAL_LIVE_EVIDENCE, artifact["disposition"])
            self.assertNotIn(artifact["path"], self.inv["regeneration_targets"])

    def test_S9D_23_frozen_sources_are_never_regeneration_targets(self):
        """Source truth is not derived and is not S-9's to regenerate."""
        self.assertTrue(self.inv["frozen"])
        for artifact in self.inv["frozen"]:
            self.assertEqual(inv.FROZEN_SOURCE_OR_REFERENCE,
                             artifact["disposition"])
            self.assertNotIn(artifact["path"], self.inv["regeneration_targets"])

    def test_S9D_24_the_pre_revision_artifact_is_migration_evidence(self):
        """It resolves for no responsibility, so it is not a fixture - and it is
        retained rather than deleted, because it records why the answer moved."""
        migration = [a for a in self.inv["active"] if not a["resolvable"]]
        self.assertEqual(1, len(migration))
        self.assertIn("pre_revision", migration[0]["path"])
        self.assertEqual(inv.HISTORICAL_MIGRATION_EVIDENCE,
                         migration[0]["disposition"])

    def test_S9D_25_the_regeneration_target_set_is_exact(self):
        """The S9-E cost, derived rather than assumed.

        Twelve, not the thirteen a file count suggests: the pre-revision artifact
        is migration evidence and no replay can resolve it.
        """
        targets = self.inv["regeneration_targets"]
        self.assertEqual(12, len(targets))
        self.assertEqual(6, len([t for t in targets if "fixtures/responses" in t]))
        self.assertEqual(6, len([t for t in targets if "probes" in t]))

    def test_S9D_26_the_current_corpus_fails_the_current_rule(self):
        """FALSIFIES a corpus made current by metadata repair.

        Every active fixture is missing every S9-D identity. That is the finding,
        asserted rather than described: they cannot be re-stamped into validity,
        because the identities they lack are facts about a live execution that
        never happened.
        """
        for artifact in self.inv["active"]:
            if not artifact["resolvable"]:
                continue
            self.assertEqual(sorted(ri.REQUIRED_FIXTURE_IDENTITIES),
                             sorted(artifact["missing_identities"]),
                             artifact["path"])

    def test_S9D_27_old_owner_keyed_replay_could_not_reach_69_artifacts(self):
        """The S9-C defect, counted in the historical corpus it stranded."""
        unreachable = self.inv["old_addressing_unreachable"]
        self.assertEqual(69, len(unreachable))
        for path in unreachable:
            self.assertTrue(any(path.endswith("%s.json" % r)
                                for r in ("s03b", "s04a", "s04b")), path)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()


# =====================================================================
# The regeneration loop, end to end, with no paid call
# =====================================================================
class TestRegenerationDryRun(unittest.TestCase):
    """fake accepted response -> promotion -> integrity -> replay -> canonical
    orchestration. The point is that the LAST step is the ordinary pipeline: a
    fixture that needed a special loader would prove nothing about replay."""

    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.mkdtemp(prefix="s9d_dryrun_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.case = "CASE-DRY"
        os.makedirs(os.path.join(self.tmp, self.case))
        with open(os.path.join(_paths.BENCHMARKS, "BM-001", "source",
                               "request.txt")) as fh:
            self.request_text = fh.read()
        self.source_sha = ri.canonical_source_identity(
            self.request_text.encode("utf-8"))
        # A real prior S01 answer stands in for a live response. It is not
        # promoted anywhere: it is a body known to parse and satisfy S01's
        # contract, which is what the loop needs to exercise.
        with open(os.path.join(_paths.ASSY_V3, "fixtures", "responses",
                               "BM-001", "s01.json")) as fh:
            body = json.loads(fh.read())
        body.pop("_meta", None)
        self.accepted_raw = json.dumps(body)

    def _capturing_provider(self, root):
        """A replay provider that also remembers the prompt it was asked."""
        provider = OfflineReplayProvider(root, self.case)
        provider.prompts = {}
        original = provider.generate

        def generate(request, attempt_index=0):
            provider.prompts[ri.producing_identity(request)] = request.prompt_text
            return original(request, attempt_index)

        provider.generate = generate
        return provider

    def _run_s01(self, root):
        from ver3.assy_v3.pipeline import Progression, window1
        from ver3.assy_v3.state import DesignState
        state = DesignState(run_id="dry-%s" % self.case)
        progression = Progression()
        provider = self._capturing_provider(root)
        out1, _out2 = window1(provider, state, self.request_text, progression)
        return out1, progression, provider, state

    def test_S9D_28_promote_then_replay_through_canonical_orchestration(self):
        """The positive path, ending in the ordinary pipeline."""
        # PASS 1 - discover the prompt the stage actually builds. Nothing is
        # promoted yet, so the replay finds nothing and reports it honestly.
        _out, _prog, prober, _state = self._run_s01(self.tmp)
        prompt = prober.prompts["s01"]

        # PROMOTE the accepted response under the frozen rule.
        attempt = pr.AttemptOutcome(
            responsibility_id="s01", source_sha256=self.source_sha,
            model_run_id="dry-CASE-DRY|s01|sa1|a1", attempt_index=1,
            stage=pr.ACCEPTED, raw_response=self.accepted_raw)
        decision = pr.select_for_promotion([attempt])
        self.assertIs(attempt, decision["chosen"])
        body = pr.fixture_body(attempt, prompt)

        # The promoted artifact is faithful and fully bound.
        self.assertEqual([], ri.promotion_fidelity_problems(body,
                                                            self.accepted_raw))
        self.assertEqual([], ri.verify_current_fixture(
            body, prompt_text=prompt, source_sha256=self.source_sha,
            responsibility_id="s01"))

        # It is addressed by the producing responsibility.
        path = os.path.join(self.tmp, self.case, "s01.json")
        with open(path, "w") as fh:
            fh.write(body)

        # PASS 2 - the ordinary pipeline, no special loader.
        out1, progression, provider, state = self._run_s01(self.tmp)
        self.assertIsNotNone(out1)
        self.assertIs(ExecutionStatus.SUCCESS, out1.execution_status)
        execution = progression.by_responsibility("s01")
        self.assertTrue(execution.patch_applied)
        self.assertTrue(execution.consumer_view_recorded,
                        "the replayed pass went through the ConsumerView boundary")
        self.assertEqual("REPLAY", execution.response_source)
        self.assertEqual(ri.PAIRED, provider.last_pairing)
        self.assertTrue(state.counts())

    def test_S9D_29_a_replayed_promotion_can_never_qualify_as_full_live(self):
        """FALSIFIES S9-I9: regenerated fixtures becoming capability evidence."""
        from ver3.assy_v3.pipeline import full_live_qualification
        attempt = pr.AttemptOutcome(
            responsibility_id="s01", source_sha256=self.source_sha,
            model_run_id="dry|s01|sa1|a1", attempt_index=1, stage=pr.ACCEPTED,
            raw_response=self.accepted_raw)
        _out, _p, prober, _s = self._run_s01(self.tmp)
        with open(os.path.join(self.tmp, self.case, "s01.json"), "w") as fh:
            fh.write(pr.fixture_body(attempt, prober.prompts["s01"]))
        _out1, progression, _pv, _st = self._run_s01(self.tmp)
        qualified, reasons = full_live_qualification(progression)
        self.assertFalse(qualified)
        self.assertTrue(any("s01" in r and "REPLAY" in r for r in reasons), reasons)

    def test_S9D_30_a_hand_enriched_promotion_is_refused_before_it_is_written(self):
        """The enrichment never reaches the corpus, because promotion refuses."""
        _out, _p, prober, _s = self._run_s01(self.tmp)
        prompt = prober.prompts["s01"]
        enriched = json.loads(self.accepted_raw)
        enriched["invented_clearance_mm"] = 12
        attempt = pr.AttemptOutcome(
            responsibility_id="s01", source_sha256=self.source_sha,
            model_run_id="dry|s01|sa1|a1", attempt_index=1, stage=pr.ACCEPTED,
            raw_response=json.dumps(enriched), hand_edited=True)
        with self.assertRaises(ValueError):
            pr.fixture_body(attempt, prompt)
        # And had it been written anyway, fidelity against the true accepted
        # response would still catch it.
        allowed = pr.AttemptOutcome(
            responsibility_id="s01", source_sha256=self.source_sha,
            model_run_id="dry|s01|sa1|a1", attempt_index=1, stage=pr.ACCEPTED,
            raw_response=json.dumps(enriched))
        body = pr.fixture_body(allowed, prompt)
        self.assertTrue(any("added" in p for p in ri.promotion_fidelity_problems(
            body, self.accepted_raw)))

    def test_S9D_31_a_fixture_bound_to_another_source_is_detected(self):
        """The artifact is well-formed and answers the wrong request."""
        _out, _p, prober, _s = self._run_s01(self.tmp)
        attempt = pr.AttemptOutcome(
            responsibility_id="s01",
            source_sha256=ri.canonical_source_identity(b"some other request"),
            model_run_id="dry|s01|sa1|a1", attempt_index=1, stage=pr.ACCEPTED,
            raw_response=self.accepted_raw)
        body = pr.fixture_body(attempt, prober.prompts["s01"])
        problems = ri.verify_current_fixture(
            body, prompt_text=prober.prompts["s01"],
            source_sha256=self.source_sha, responsibility_id="s01")
        self.assertTrue(any("source" in p for p in problems), problems)


# =====================================================================
# One guard for the mistake that has now appeared twice
# =====================================================================
class TestOwnerResponsibilityAcrossLayers(unittest.TestCase):
    """Each subsystem must use the identity its question needs.

    The confusion has appeared twice - once in the pipeline's execution record,
    once in replay addressing - so this asserts the whole map rather than either
    site. Write authority is an OWNER question; consuming, producing, qualifying
    and addressing are PASS questions.
    """

    def test_S9D_32_write_authority_uses_the_owner(self):
        """FALSIFIES the inverse mistake: responsibility used for ownership.

        `may_create` resolves permission from the patch's stage. Passing s03b
        there would ask the ownership matrix about a stage it does not list, and
        both passes legitimately author s03 state.
        """
        import ast
        with open(os.path.join(_paths.ASSY_V3, "state", "design_state.py")) as fh:
            source = fh.read()
        self.assertIn("may_create(patch.stage_id", source)
        self.assertNotIn("may_create(patch.responsibility", source)
        # The patch carries the owner, and nothing renamed that.
        with open(os.path.join(_paths.ASSY_V3, "state", "patch.py")) as fh:
            self.assertIn("stage_id", fh.read())
        del ast

    def test_S9D_33_consumer_view_selection_uses_the_pass(self):
        """The contract a pass reads is chosen by its responsibility."""
        with open(os.path.join(_paths.ASSY_V3, "stages", "base.py")) as fh:
            source = fh.read()
        self.assertIn("consumer_view_for(self.responsibility_id()", source)

    def test_S9D_34_producing_and_qualifying_use_the_pass(self):
        with open(os.path.join(_paths.ASSY_V3, "pipeline",
                               "progression.py")) as fh:
            source = fh.read()
        self.assertIn("responsibility_id = stage.responsibility_id()", source)
        self.assertIn("by_responsibility(responsibility_id)", source)

    def test_S9D_35_replay_addressing_uses_the_pass(self):
        """FALSIFIES the reintroduction of owner-keyed replay."""
        for module in ("offline.py", "agent_authored.py"):
            with open(os.path.join(_paths.ASSY_V3, "providers", module)) as fh:
                source = fh.read()
            self.assertIn("producing_identity(request)", source, module)
            self.assertNotIn('"%s.json" % request.stage_id', source, module)

    def test_S9D_36_fixture_binding_uses_source_and_pass(self):
        self.assertIn(ri.SOURCE_KEY, ri.REQUIRED_FIXTURE_IDENTITIES)
        self.assertIn(ri.RESPONSIBILITY_KEY, ri.REQUIRED_FIXTURE_IDENTITIES)

    def test_S9D_37_owner_collision_is_expected_and_pass_collision_is_not(self):
        """The architectural fact the whole map rests on."""
        from ver3.assy_v3.stages.s03_topology_and_mobility import (
            S03BMobilityAndAssembly, S03TopologyAndMobility)
        from ver3.assy_v3.stages.s04_envelope_and_motion import (
            S04AEnvelopeAndReach, S04BPlacementAndMotion)
        pairs = ((S03TopologyAndMobility, S03BMobilityAndAssembly),
                 (S04AEnvelopeAndReach, S04BPlacementAndMotion))
        for first, second in pairs:
            self.assertEqual(first.stage_id, second.stage_id)
            self.assertNotEqual(first().responsibility_id(),
                                second().responsibility_id())


# =====================================================================
# S9-D CLOSURE HARDENING — the rule enforced on the path it was written for
# =====================================================================
class TestCurrentReplayEnforcement(unittest.TestCase):
    """Every test here drives the ORDINARY replay boundary.

    The gap this closes: `verify_current_fixture` was called by promotion, by the
    dry run and by audits, and by no replay. A rule enforced only where it is
    convenient is a rule the target path does not have - so these assert on the
    provider's own GenerationResult, never on a helper invocation.
    """

    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.mkdtemp(prefix="s9d_strict_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.case = "CASE-STRICT"
        os.makedirs(os.path.join(self.tmp, self.case))
        self.prompt = "the prompt the stage built"
        self.raw = json.dumps({"answer": 1})
        self.source = ri.canonical_source_identity(b"the request bytes")
        self.attempt = pr.AttemptOutcome(
            responsibility_id="s03b", source_sha256=self.source,
            model_run_id="run-9|s03|sa2|a1", attempt_index=1,
            stage=pr.ACCEPTED, raw_response=self.raw)
        self.ledger = pr.build_ledger([self.attempt])
        self._write(pr.fixture_body(self.attempt, self.prompt))

    def _write(self, body, name="s03b.json"):
        with open(os.path.join(self.tmp, self.case, name), "w") as fh:
            fh.write(body)

    def _replay(self, trust=ri.CURRENT_REPLAY, source=None, ledger="default",
                responsibility="s03b", prompt=None):
        provider = OfflineReplayProvider(
            self.tmp, self.case, trust=trust,
            source_sha256=self.source if source is None else source,
            ledger=self.ledger if ledger == "default" else ledger)
        request = GenerationRequest(
            purpose="p", stage_id="s03", prompt_text=prompt or self.prompt,
            max_output_tokens=1, deadline_s=1.0,
            responsibility_id=responsibility)
        return provider, provider.generate(request)

    # ---------------------------------------------------------- positive
    def test_S9D_38_a_conforming_current_fixture_replays(self):
        provider, result = self._replay()
        self.assertIs(ExecutionStatus.SUCCESS, result.execution_status)
        self.assertEqual(self.raw, json.dumps(
            {k: v for k, v in json.loads(result.response.raw_text).items()
             if k != "_meta"}))
        self.assertEqual(ri.INTEGRITY_ESTABLISHED,
                         provider.last_integrity["current_fixture_integrity"])
        self.assertEqual(ri.CURRENT_REPLAY, provider.last_integrity["trust"])
        self.assertEqual([], provider.last_integrity["problems"])

    # ---------------------------------------------------------- negatives
    def _rejected(self, result, provider, needle):
        self.assertIs(ExecutionStatus.PROVIDER_UNAVAILABLE,
                      result.execution_status,
                      "an invalid current fixture returned a usable response")
        self.assertIsNone(result.response)
        self.assertIn("integrity not established", result.error_detail)
        self.assertIn(needle, result.error_detail)
        self.assertEqual(ri.INTEGRITY_NOT_ESTABLISHED,
                         provider.last_integrity["current_fixture_integrity"])

    def test_S9D_39_wrong_source_is_rejected_at_the_boundary(self):
        provider, result = self._replay(
            source=ri.canonical_source_identity(b"a different benchmark"))
        self._rejected(result, provider, "source")

    def test_S9D_40_a_missing_source_identity_cannot_be_waved_through(self):
        """Replaying "for whatever request this is" is how one benchmark's
        answer serves another."""
        provider, result = self._replay(source="")
        self._rejected(result, provider, "canonical source identity")

    def test_S9D_41_a_pass_substitution_is_rejected_at_the_boundary(self):
        """s03b's artifact requested as s03a, and the s04 pair too."""
        self._write(pr.fixture_body(self.attempt, self.prompt), "s03a.json")
        provider, result = self._replay(responsibility="s03a")
        self._rejected(result, provider, "s03b")

        s04 = pr.AttemptOutcome(
            responsibility_id="s04a", source_sha256=self.source,
            model_run_id="run-9|s04|sa1|a1", attempt_index=1,
            stage=pr.ACCEPTED, raw_response=self.raw)
        self.ledger = pr.build_ledger([self.attempt, s04])
        self._write(pr.fixture_body(s04, self.prompt), "s04b.json")
        provider, result = self._replay(responsibility="s04b")
        self._rejected(result, provider, "s04a")

    def test_S9D_42_a_broken_raw_response_identity_is_rejected(self):
        body = json.loads(pr.fixture_body(self.attempt, self.prompt))
        body["_meta"][ri.RESPONSE_KEY] = "0" * 64
        self._write(json.dumps(body))
        provider, result = self._replay()
        self._rejected(result, provider, ri.RESPONSE_KEY)

    def test_S9D_43_an_unresolvable_model_run_id_is_rejected(self):
        """FALSIFIES the "non-empty therefore real" reading of an identity."""
        body = json.loads(pr.fixture_body(self.attempt, self.prompt))
        body["_meta"][ri.PROMOTION_KEY] = "run-invented|s03|sa2|a1"
        self._write(json.dumps(body))
        provider, result = self._replay()
        self._rejected(result, provider, "no retained promotion record")

    def test_S9D_44_no_ledger_means_no_current_claim(self):
        provider, result = self._replay(ledger=None)
        self._rejected(result, provider, "no promotion ledger")

    def test_S9D_45_a_stale_pairing_is_rejected(self):
        provider, result = self._replay(prompt="a prompt built from moved state")
        self._rejected(result, provider, "pairing is STALE")

    def test_S9D_46_pairing_history_cannot_rescue_a_current_replay(self):
        """FALSIFIES S9-I14 at the boundary rather than in a helper."""
        body = json.loads(pr.fixture_body(self.attempt, self.prompt))
        for key in ri.REQUIRED_FIXTURE_IDENTITIES:
            body["_meta"].pop(key, None)
        body["_meta"][ri.MIGRATION_BRIDGE_KEY] = ["re-paired; content unchanged"]
        self._write(json.dumps(body))
        provider, result = self._replay()
        self._rejected(result, provider, ri.SOURCE_KEY)

    def test_S9D_47_a_fixture_mutated_after_promotion_is_rejected(self):
        """The artifact was valid when written and was edited afterwards."""
        body = json.loads(pr.fixture_body(self.attempt, self.prompt))
        body["invented_clearance_mm"] = 12          # hand enrichment
        self._write(json.dumps(body))
        provider, result = self._replay()
        # CAUGHT BY RECOMPUTATION, not by comparing two copies of one claim.
        # Every declared identity still agrees with the ledger - the edit changed
        # the content, and the content hash is the only one derived from what is
        # actually there.
        self._rejected(result, provider, "altered after promotion")
        self.assertTrue(ri.promotion_fidelity_problems(json.dumps(body), self.raw))

    # ---------------------------------------------------- legacy vs current
    def test_S9D_48_the_same_stale_artifact_is_legacy_yes_current_no(self):
        """FALSIFIES the shortcut that would make S9-E unnecessary.

        One artifact, two trust classes. Legacy keeps the intermediate
        regression capability; current refuses it, so a metadata-poor response
        can never be counted as regenerated.
        """
        stale = json.dumps({"answer": 1, "_meta": {
            ri.PAIRING_KEY: ri.prompt_hash(self.prompt),
            ri.MIGRATION_BRIDGE_KEY: ["re-paired after the schema section"]}})
        self._write(stale)

        legacy_provider, legacy = self._replay(trust=ri.LEGACY_REPLAY)
        self.assertIs(ExecutionStatus.SUCCESS, legacy.execution_status)
        self.assertEqual(ri.LEGACY_REPLAY, legacy_provider.last_integrity["trust"])
        self.assertEqual(ri.INTEGRITY_NOT_ESTABLISHED,
                         legacy_provider.last_integrity["current_fixture_integrity"])
        self.assertTrue(legacy_provider.last_integrity["problems"],
                        "legacy still REPORTS why it is not current")

        current_provider, current = self._replay(trust=ri.CURRENT_REPLAY)
        self._rejected(current, current_provider, ri.SOURCE_KEY)

    def test_S9D_49_legacy_is_the_default_and_current_is_opt_in(self):
        """Defaulting to strict would break the regression the corpus supports,
        and the only way to keep it would be to forge the identities."""
        provider = OfflineReplayProvider(self.tmp, self.case)
        self.assertEqual(ri.LEGACY_REPLAY, provider.trust)
        with self.assertRaises(ValueError):
            OfflineReplayProvider(self.tmp, self.case, trust="SOMEWHAT")

    def test_S9D_50_the_twelve_targets_are_not_current_and_are_unmodified(self):
        """FALSIFIES §16: stale artifacts stamped into compliance.

        Every regeneration target must still be missing every current identity.
        If one ever passes, it was either regenerated by S9-E or forged.
        """
        for path in inv.inventory()["regeneration_targets"]:
            with open(os.path.join(_paths.REPO_ROOT, path)) as fh:
                body = fh.read()
            identities = ri.fixture_identities(body)
            self.assertEqual([], [k for k, v in identities.items() if v],
                             "%s carries a current identity it cannot have "
                             "earned before S9-E" % path)

    def test_S9D_51_an_integrity_rejection_is_never_an_engineering_finding(self):
        """FALSIFIES the attribution collapse §10 forbids.

        A corpus defect must not be reported as the design failing, so the
        status may not be a schema, contract or assurance term.
        """
        _provider, result = self._replay(source="")
        for forbidden in (ExecutionStatus.SCHEMA_FAILURE,
                          ExecutionStatus.CONTRACT_INCOMPLETE,
                          ExecutionStatus.FALSE_ACCEPTANCE,
                          ExecutionStatus.SAFE_REJECTION,
                          ExecutionStatus.MODEL_CAPABILITY_FAILURE):
            self.assertIsNot(forbidden, result.execution_status)

    def test_S9D_52_a_current_replay_still_cannot_qualify_as_full_live(self):
        """Enforced integrity makes a fixture trustworthy, not live."""
        from ver3.assy_v3.pipeline import (LIVE, REPLAY, Progression,
                                           StageExecution,
                                           full_live_qualification)
        provider, result = self._replay()
        self.assertIs(ExecutionStatus.SUCCESS, result.execution_status)
        self.assertEqual(REPLAY, provider.response_source)
        p = Progression()
        for responsibility in ("s01", "s02", "s03a", "s03b", "s04a", "s04b"):
            p.record(StageExecution(
                stage_id="s03", responsibility_id=responsibility,
                response_source=REPLAY if responsibility == "s03b" else LIVE,
                provider_id="x", execution_status="SUCCESS", patch_applied=True))
        qualified, reasons = full_live_qualification(p)
        self.assertFalse(qualified)
        self.assertTrue(any("s03b" in r for r in reasons), reasons)
