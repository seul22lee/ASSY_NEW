"""The benchmark tree is a skeleton, and its boundaries are the ones that matter.

Two things are checked here that are easy to get wrong quietly:

* No Oracle and no positive executable reference may sit inside a benchmark
  directory. Both must stay in their own trees so that `ver3/oracles/` and
  `ver3/cad_validation/` can remain BLOCKING forbidden path roots without also
  blocking the source request the pipeline legitimately reads.
* BM-003 must announce that it is a placeholder. A skeleton missing its third
  benchmark makes STAGE_PROGRESSION_CONTRACT's freeze gate look satisfiable when
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

    def test_bm003_is_declared_a_placeholder(self):
        data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))
        self.assertEqual("PLACEHOLDER", data["status"])
        self.assertIn("placeholder_notice", data)
        self.assertFalse(data["oracle"]["frozen_before_source_only_runs"])

    def test_bm003_blocks_the_freeze_gate(self):
        """An incomplete benchmark set must block freezing, and must say so."""
        data = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, "BM-003", "descriptor.yaml"))
        blocks = " ".join(data["placeholder_notice"]["blocks"]).lower()
        self.assertIn("freez", blocks)

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
