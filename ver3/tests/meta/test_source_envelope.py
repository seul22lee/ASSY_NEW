"""One canonical source layout, and one common envelope across all three sources.

Normalization is only worth doing if it stays done. These tests hold two things:

* There is exactly ONE place a source manifest lives. No duplicate, no
  compatibility copy, no redirect, no symlink, and no resolver that tries a
  second path — because a fallback makes both layouts permanently valid, which
  is the state normalization was meant to end.
* Every manifest carries the same envelope, whatever its source class. The
  envelope is what the freeze gate reads, so a manifest that omits a field would
  be read as a manifest that satisfies it.
"""

import os
import unittest

from . import _paths

VALID_SOURCE_CLASSES = {"EXTRACTED_VERBATIM", "NEWLY_AUTHORED"}
VALID_AUTHORITY_STATUSES = {"PROPOSED", "FROZEN", "SUPERSEDED"}


class TestCanonicalLayout(unittest.TestCase):

    def test_every_benchmark_has_the_canonical_pair(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertTrue(os.path.isfile(_paths.request_path(bm)))
                self.assertTrue(os.path.isfile(_paths.source_manifest_path(bm)))

    def test_no_manifest_outside_the_canonical_location(self):
        """A second copy anywhere is a second source of truth."""
        strays = []
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn != "source_manifest.yaml":
                    continue
                full = os.path.join(dirpath, fn)
                if full not in [_paths.source_manifest_path(b) for b in _paths.BENCHMARK_IDS]:
                    strays.append(os.path.relpath(full, _paths.REPO_ROOT))
        self.assertEqual([], strays, "manifests outside the canonical path: %s" % strays)

    def test_no_request_outside_the_canonical_location(self):
        strays = []
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn != "request.txt":
                    continue
                full = os.path.join(dirpath, fn)
                if full not in [_paths.request_path(b) for b in _paths.BENCHMARK_IDS]:
                    strays.append(os.path.relpath(full, _paths.REPO_ROOT))
        self.assertEqual([], strays, "requests outside the canonical path: %s" % strays)

    def test_no_symlinks_in_the_benchmark_tree(self):
        links = []
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            for name in list(dirnames) + list(filenames):
                full = os.path.join(dirpath, name)
                if os.path.islink(full):
                    links.append(os.path.relpath(full, _paths.REPO_ROOT))
        self.assertEqual([], links, "symlinks: %s" % links)

    def test_descriptors_point_at_the_canonical_manifest(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                d = _paths.load_yaml(os.path.join(_paths.BENCHMARKS, bm, "descriptor.yaml"))
                declared = d["source"].get("manifest")
                if declared is None:
                    self.skipTest("%s descriptor declares no manifest" % bm)
                self.assertEqual("ver3/benchmarks/%s/source/source_manifest.yaml" % bm, declared)

    def test_no_documentation_references_the_old_location(self):
        """Docs pointing at a path that no longer exists teach the wrong layout."""
        stale = []
        for dirpath, dirnames, filenames in os.walk(_paths.VER3):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for fn in filenames:
                if not fn.endswith((".md", ".yaml", ".yml", ".py")):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, _paths.REPO_ROOT)
                if rel.startswith(os.path.join("ver3", "oracles")):
                    continue
                # This file necessarily contains the literal it searches for.
                if rel == os.path.join("ver3", "tests", "meta", "test_source_envelope.py"):
                    continue
                with open(full, encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, start=1):
                        if "../source_manifest.yaml" in line:
                            stale.append("%s:%d" % (rel, i))
        self.assertEqual([], stale, "references to the pre-normalization path: %s" % stale)


class TestCommonEnvelope(unittest.TestCase):

    def test_every_manifest_carries_the_full_envelope(self):
        for bm in _paths.BENCHMARK_IDS:
            man = _paths.source_manifest(bm)
            for field in _paths.SOURCE_ENVELOPE_FIELDS:
                with self.subTest(benchmark=bm, field=field):
                    self.assertIn(field, man)

    def test_envelope_field_order_is_identical_across_manifests(self):
        """Same shape, not merely the same set.

        A shared envelope a reader can scan without re-orienting is the point;
        reordered fields make three manifests read as three formats.
        """
        orders = {}
        for bm in _paths.BENCHMARK_IDS:
            man = _paths.source_manifest(bm)
            orders[bm] = [k for k in man if k in _paths.SOURCE_ENVELOPE_FIELDS]
        first = orders[_paths.BENCHMARK_IDS[0]]
        for bm, order in orders.items():
            with self.subTest(benchmark=bm):
                self.assertEqual(first, order)

    def test_benchmark_id_matches_its_directory(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertEqual(bm, _paths.source_manifest(bm)["benchmark_id"])

    def test_source_class_is_from_the_vocabulary(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertIn(_paths.source_manifest(bm)["source_class"], VALID_SOURCE_CLASSES)

    def test_authority_status_is_from_the_vocabulary(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertIn(_paths.source_manifest(bm)["authority_status"], VALID_AUTHORITY_STATUSES)

    def test_request_sha256_matches_the_file(self):
        import hashlib
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                with open(_paths.request_path(bm), "rb") as fh:
                    raw = fh.read()
                self.assertEqual(_paths.source_manifest(bm)["request_sha256"],
                                 hashlib.sha256(raw).hexdigest())

    def test_source_word_count_matches_the_file(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                with open(_paths.request_path(bm), encoding="utf-8") as fh:
                    words = len(fh.read().split())
                self.assertEqual(_paths.source_manifest(bm)["source_word_count"], words)

    def test_request_is_production_readable_and_the_hidden_trees_are_not(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                self.assertTrue(man["production_readable"])
                self.assertFalse(man["oracle_visible_to_production"])
                self.assertFalse(man["positive_reference_visible_to_production"])

    def test_review_flags_are_booleans(self):
        """A string here would be truthy and would silently open the gate."""
        for bm in _paths.BENCHMARK_IDS:
            man = _paths.source_manifest(bm)
            for field in ("human_review_required", "human_review_complete", "frozen",
                          "production_readable", "oracle_visible_to_production",
                          "positive_reference_visible_to_production"):
                with self.subTest(benchmark=bm, field=field):
                    self.assertIsInstance(man[field], bool)

    def test_nothing_is_marked_approved_or_frozen_yet(self):
        """No source may be self-approved. Freezing is a human act."""
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                man = _paths.source_manifest(bm)
                self.assertFalse(man["human_review_complete"])
                self.assertFalse(man["frozen"])
                self.assertEqual("PROPOSED", man["authority_status"])

    def test_frozen_implies_reviewed(self):
        """A frozen source that was never reviewed is a contradiction.

        Currently vacuous — nothing is frozen — and deliberately kept so that it
        starts biting the moment something is.
        """
        for bm in _paths.BENCHMARK_IDS:
            man = _paths.source_manifest(bm)
            if man["frozen"]:
                with self.subTest(benchmark=bm):
                    self.assertTrue(man["human_review_complete"])
                    self.assertEqual("FROZEN", man["authority_status"])

    def test_extracted_sources_name_a_witness_and_authored_ones_say_they_have_none(self):
        for bm in _paths.BENCHMARK_IDS:
            man = _paths.source_manifest(bm)
            with self.subTest(benchmark=bm, source_class=man["source_class"]):
                if man["source_class"] == "EXTRACTED_VERBATIM":
                    self.assertTrue(man["provenance"]["primary_witness"]["path"])
                else:
                    self.assertEqual("AUTHORED", man["provenance"]["origin"])
                    self.assertNotIn("primary_witness", man["provenance"])


class TestSourceFreezeReview(unittest.TestCase):
    """The consolidated review must be present, current, and undecided."""

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(_paths.BENCHMARKS, "SOURCE_FREEZE_REVIEW.md")
        with open(cls.path, encoding="utf-8") as fh:
            cls.text = fh.read()

    def test_review_document_exists(self):
        self.assertTrue(os.path.isfile(self.path))

    def test_it_covers_all_three_benchmarks(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertIn(bm, self.text)

    def test_it_quotes_the_current_hash_of_every_request(self):
        """A review document showing a stale hash reviews a file that no longer exists."""
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertIn(_paths.source_manifest(bm)["request_sha256"], self.text)

    def test_it_quotes_the_current_word_count_of_every_request(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                count = _paths.source_manifest(bm)["source_word_count"]
                self.assertIn("**Word count:** %d" % count, self.text)

    def test_it_contains_the_exact_request_text(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                with open(_paths.request_path(bm), encoding="utf-8") as fh:
                    body = fh.read().rstrip("\n")
                self.assertIn(body, self.text)

    def test_every_human_decision_is_pending(self):
        """Nothing may be approved or frozen autonomously."""
        self.assertIn("PENDING", self.text)
        for forbidden in ("HUMAN_APPROVED", "authority_status: FROZEN\nfrozen: true"):
            self.assertNotIn(forbidden, self.text)

    def test_it_records_the_bm002_quantity_discrepancy_without_normalizing_it(self):
        """Both renderings must appear; recording it is the point."""
        self.assertIn("80-100 mm", self.text)
        self.assertIn("80--100 mm", self.text)

    def test_it_records_that_bm003_has_no_independent_witness(self):
        self.assertIn("no independent verbatim witness", self.text)

    def test_no_source_is_marked_approved_anywhere_in_the_tree(self):
        strays = []
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if not fn.endswith((".md", ".yaml", ".yml")):
                    continue
                full = os.path.join(dirpath, fn)
                with open(full, encoding="utf-8", errors="replace") as fh:
                    if "HUMAN_APPROVED" in fh.read():
                        strays.append(os.path.relpath(full, _paths.REPO_ROOT))
        self.assertEqual([], strays, "self-approved sources: %s" % strays)


if __name__ == "__main__":
    unittest.main()
