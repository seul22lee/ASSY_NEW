"""The benchmark tree is a skeleton, and its boundaries are the ones that matter.

Two things are checked here that are easy to get wrong quietly:

* No Oracle and no positive executable reference may sit inside a benchmark
  directory. Both must stay in their own trees so that `ver3/oracles/` and
  `ver3/cad_validation/` can remain BLOCKING forbidden path roots without also
  blocking the source request the pipeline legitimately reads.
* BM-003 must be internally consistent about its readiness. A benchmark whose
  descriptor overstates its state makes the freeze gate look satisfiable when
  it is not, and a gate that appears passable is worse than a missing one.
"""

import os
import unittest

from . import _paths

BENCHMARK_IDS = ["BM-001", "BM-002", "BM-003"]


class TestBenchmarkSkeleton(unittest.TestCase):

    def test_all_three_benchmarks_exist(self):
        for bm in BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertTrue(os.path.isdir(os.path.join(_paths.BENCHMARKS, bm)))

    def test_each_has_a_parsable_descriptor(self):
        for bm in BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, bm, "descriptor.yaml"))
                self.assertEqual(bm, data["benchmark_id"])
                for key in ("source", "oracle", "positive_executable_reference", "output"):
                    self.assertIn(key, data)

    def test_source_is_read_only_by_s01(self):
        for bm in BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, bm, "descriptor.yaml"))
                self.assertEqual("s01", data["source"]["read_by"])

    def test_no_oracle_lives_inside_a_benchmark_directory(self):
        """The answer key stays in its own tree.

        A directory or file named for an oracle under ver3/benchmarks/ would sit
        outside the BLOCKING path root and become reachable.
        """
        violations = []
        for bm in BENCHMARK_IDS:
            for dirpath, dirnames, filenames in os.walk(os.path.join(_paths.BENCHMARKS, bm)):
                for name in list(dirnames) + list(filenames):
                    lowered = name.lower()
                    if "oracle" in lowered and not lowered.endswith("descriptor.yaml"):
                        violations.append(os.path.join(dirpath, name))
        self.assertEqual([], violations, "oracle material inside benchmark tree: %s" % violations)

    def test_no_cad_geometry_inside_a_benchmark_directory(self):
        """No positive executable reference, no golden geometry."""
        suspicious = (".step", ".stp", ".brep", ".stl", ".iges", ".igs", ".sldprt", ".f3d")
        violations = []
        for bm in BENCHMARK_IDS:
            for dirpath, _dirnames, filenames in os.walk(os.path.join(_paths.BENCHMARKS, bm)):
                for name in filenames:
                    if name.lower().endswith(suspicious):
                        violations.append(os.path.join(dirpath, name))
        self.assertEqual([], violations, "geometry inside benchmark tree: %s" % violations)

    def test_descriptors_state_the_oracle_is_never_visible_to_production(self):
        for bm in BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, bm, "descriptor.yaml"))
                never = data["oracle"]["never_visible_to"]
                for who in ("production_stages", "generation_models", "prompts", "retrieval"):
                    self.assertIn(who, never)

    def test_extracted_sources_have_a_manifest(self):
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                d = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, bm, "descriptor.yaml"))
                if not d["source"].get("present"):
                    self.skipTest("%s source not extracted yet" % bm)
                self.assertTrue(os.path.isfile(_paths.request_path(bm)))
                self.assertTrue(os.path.isfile(_paths.source_manifest_path(bm)))

    def test_request_matches_its_recorded_hash(self):
        """The copy must be verifiable, not merely asserted."""
        import hashlib
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                path = os.path.join(_paths.REPO_ROOT, man["artifact"])
                with open(path, "rb") as fh:
                    raw = fh.read()
                self.assertEqual(man["extraction"]["hashes"]["file_sha256"],
                                 hashlib.sha256(raw).hexdigest())
                self.assertEqual(man["request_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(man["extraction"]["hashes"]["bytes"], len(raw))
                # content hash excludes the one appended newline
                self.assertEqual(man["extraction"]["hashes"]["content_sha256"],
                                 hashlib.sha256(raw[:-1]).hexdigest())

    def test_manifest_declares_no_oracle_and_no_reference_content(self):
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                absent = man["declared_absent"]
                for key in ("oracle_semantics", "positive_reference_information",
                            "ver2_derived_interpretation"):
                    self.assertFalse(absent[key]["present"], "%s declares %s present" % (bm, key))
                    self.assertTrue(absent[key]["statement"].strip())

    def test_manifest_records_a_human_review_status(self):
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                self.assertTrue(man["human_review_required"])
                if not man["human_review_complete"]:
                    self.assertTrue(man["human_review"]["questions"],
                                    "review outstanding but no question stated")

    def test_extraction_applied_no_interpretation(self):
        """The forbidden transformations must be named, not merely avoided."""
        forbidden = {"interpretation", "normalization", "summarization",
                     "clarification", "enrichment", "reordering"}
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                declared = set(man["extraction"]["transformations_NOT_applied"])
                self.assertEqual(set(), forbidden - declared)
                self.assertEqual("VERBATIM_FIELD_COPY", man["extraction"]["method"])

    def test_source_provenance_is_not_an_oracle_path(self):
        """The extraction must not have come from ver3/oracles/.

        Reading the dossier would mean the answer key's analytical sections were
        a source for the one tree production code is allowed to read.
        """
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                for witness in ("primary_witness", "corroborating_witness"):
                    path = man["provenance"][witness]["path"]
                    self.assertNotIn("ver3/oracles", path)
                    self.assertNotIn("cad_validation", path)

    def test_request_contains_no_mechanism_or_geometry_leakage(self):
        """A source request states a problem. It must not name a solution.

        A leaked mechanism noun here would mean the pipeline was handed its
        answer in its only legitimate input.
        """
        leaks = ("slider-crank", "crank shaft", "connecting rod", "clevis",
                 "snap latch", "cantilever", "b-rep", "step file", "cadquery",
                 "mujoco", "body count", "overhung")
        for bm in ("BM-001", "BM-002"):
            with self.subTest(benchmark=bm):
                with open(_paths.request_path(bm),
                          encoding="utf-8") as fh:
                    text = fh.read().lower()
                found = [w for w in leaks if w in text]
                self.assertEqual([], found, "solution language in the source request: %s" % found)

    def test_bm003_authored_source_was_frozen_by_human_decision(self):
        """An authored source has no witness, so only a human could accept it.

        BM-001 and BM-002 were extracted and are checkable against a fixture.
        BM-003 was written, so its acceptance rests entirely on human judgement -
        which is why the decision record, not the envelope alone, is the evidence
        that the freeze was legitimate.
        """
        path = _paths.source_manifest_path("BM-003")
        if not os.path.isfile(path):
            self.skipTest("BM-003 source not authored yet")
        man = _paths.load_yaml(path)
        self.assertEqual("AUTHORED", man["provenance"]["origin"])
        self.assertEqual("NEWLY_AUTHORED", man["source_class"])
        self.assertTrue(man["human_review_required"])
        self.assertTrue(man["human_review_complete"])
        self.assertTrue(man["frozen"])
        self.assertFalse(man["subject"]["chosen_by_this_session"])

    def test_bm003_request_matches_its_recorded_hash(self):
        import hashlib
        path = _paths.source_manifest_path("BM-003")
        if not os.path.isfile(path):
            self.skipTest("BM-003 source not authored yet")
        man = _paths.load_yaml(path)
        with open(os.path.join(_paths.REPO_ROOT, man["artifact"]), "rb") as fh:
            raw = fh.read()
        self.assertEqual(man["authoring"]["hashes"]["file_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(man["request_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(man["authoring"]["hashes"]["bytes"], len(raw))

    def test_bm003_request_is_within_the_length_target(self):
        path = _paths.request_path("BM-003")
        if not os.path.isfile(path):
            self.skipTest("BM-003 source not authored yet")
        with open(path, encoding="utf-8") as fh:
            words = len(fh.read().split())
        self.assertTrue(150 <= words <= 300, "request is %d words; target 150-300" % words)

    def test_bm003_source_declares_no_oracle_exists(self):
        path = _paths.source_manifest_path("BM-003")
        if not os.path.isfile(path):
            self.skipTest("BM-003 source not authored yet")
        man = _paths.load_yaml(path)
        self.assertFalse(man["declared_absent"]["oracle_semantics"]["present"])
        self.assertFalse(man["declared_absent"]["solution_content"]["present"])
        for item in ("an Oracle", "a mechanism selection", "CAD", "an evaluation"):
            self.assertIn(item, man["this_task_did_not_produce"])

    def test_bm003_status_means_what_it_says(self):
        """The status must not round self-review up to approval.

        Four things are simultaneously true and the status name has to carry all
        of them: the Oracle is frozen, it has been semantically reviewed, the
        benchmark is structurally scorable, and NO human has independently
        approved it. A status of ORACLE_READY would have asserted the fourth
        away.
        """
        d = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))
        self.assertEqual("ORACLE_SEMANTIC_REVIEW_COMPLETE_HUMAN_APPROVAL_PENDING", d["status"])
        self.assertTrue(_paths.source_manifest("BM-003")["frozen"])
        self.assertEqual("FROZEN", d["oracle"]["authority_status"])
        self.assertTrue(d["oracle"]["frozen_before_source_only_runs"])
        self.assertEqual("SELF_REVIEW_COMPLETE", d["oracle"]["semantic_review_status"])
        self.assertEqual("PENDING", d["oracle"]["human_semantic_approval"])
        self.assertTrue(os.path.isdir(os.path.join(
            _paths.VER3, "oracles", "held_out", "BM-003")))

    def test_bm003_descriptor_does_not_claim_independent_authorship(self):
        """It must not claim more independence than GOVERNANCE.yaml supports."""
        d = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))["oracle"]
        self.assertNotIn("authored_independently", d)
        self.assertFalse(d["independent_author"])
        self.assertEqual("SAME_AGENT_SEPARATE_TASK", d["author_independence_status"])
        self.assertTrue(d["production_generation_isolated"])
        self.assertEqual("PENDING", d["human_independence_review"])

    def test_bm003_still_has_no_positive_executable_reference(self):
        """An Oracle defines success; a positive reference only validates the evaluator.

        BM-003 is scorable without one, and adding one must never become a
        precondition - it would turn "did the pipeline solve the problem" into
        "did it reproduce our example".
        """
        data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))
        self.assertEqual("NOT_BUILT", data["positive_executable_reference"]["location"])
        self.assertFalse(os.path.exists(os.path.join(_paths.VER3, "cad_validation", "BM-003")))

    def test_stage_freeze_is_still_blocked_by_everything_except_bm003(self):
        """BM-003 is ready; stage freezing is not.

        FSF-02 hidden-Oracle readiness is now satisfied for this benchmark. The
        remaining inputs are not, because no stage exists to run - and satisfying
        one input is not partial permission.
        """
        data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))
        notice = data["oracle_status_notice"]
        self.assertIn("no stage is implemented", notice["still_outstanding_elsewhere"])
        progression = _paths.contract("STAGE_PROGRESSION_CONTRACT.yaml")
        inputs = progression["freeze_rule"]["full_stage_freeze_inputs"]["required_inputs"]
        unsatisfied = [i["input"] for i in inputs if i["state"] != "SATISFIED"]
        self.assertTrue(unsatisfied, "no stage may freeze while inputs remain unsatisfied")
        frozen = [n for n in _paths.CONTRACT_FILES
                  if _paths.contract(n).get("status") == "frozen"]
        self.assertEqual([], frozen)

    def test_no_stage_contract_is_frozen_while_bm003_is_a_placeholder(self):
        """Consistency between the descriptor's claim and the contracts on disk.

        If a contract were frozen today it would have been frozen on two
        benchmarks, which is exactly what the freeze rule forbids.
        """
        data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))
        if data["status"] != "PLACEHOLDER":
            self.skipTest("BM-003 is defined; the freeze gate is reachable.")
        frozen = [n for n in _paths.CONTRACT_FILES if _paths.contract(n).get("status") == "frozen"]
        self.assertEqual([], frozen, "frozen contracts with an undefined third benchmark: %s" % frozen)


if __name__ == "__main__":
    unittest.main()
