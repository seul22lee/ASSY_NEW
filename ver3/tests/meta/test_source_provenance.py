"""Extracted sources declare immutable, reproducible provenance.

A local absolute path records how an extraction happened on one machine. It is
not provenance: it is machine-specific and version-blind, so it cannot tell a
third party WHICH bytes the request came from. The immutable fields — repository,
commit, repo-relative path and content hashes — can.

These tests never touch an absolute home directory. Where the origin repository
happens to sit beside this one they verify the declared hashes against it; where
it does not, they skip. A test that only passes inside one developer's home
directory is not a check, it is a coincidence.
"""

import hashlib
import json
import os
import subprocess
import unittest

from . import _paths

EXTRACTED = ["BM-001", "BM-002"]

REQUIRED_ORIGIN_FIELDS = [
    "origin_repository",
    "origin_commit",
    "repo_relative_path",
    "origin_file_sha256",
    "extracted_field",
    "extracted_value_sha256",
    "local_path_at_extraction",
]

#: Sibling-directory guess only. Never an absolute home path.
CANDIDATE_ORIGIN_ROOTS = [
    os.path.join(os.path.dirname(_paths.REPO_ROOT), "ASSY_Ver2.0"),
]


def _origin_root():
    for root in CANDIDATE_ORIGIN_ROOTS:
        if os.path.isdir(os.path.join(root, ".git")):
            return root
    return None


class TestImmutableOriginDeclared(unittest.TestCase):

    def test_extracted_sources_declare_an_immutable_origin(self):
        for bm in EXTRACTED:
            with self.subTest(benchmark=bm):
                self.assertIn("immutable_origin", _paths.source_manifest(bm))

    def test_declared_origin_is_complete_or_explicitly_unresolved(self):
        """Either every field is present, or the gap is structured and named.

        A half-filled origin block is the failure mode: it looks like provenance
        and cannot be acted on.
        """
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            with self.subTest(benchmark=bm):
                if origin["status"] == "ESTABLISHED":
                    for field in REQUIRED_ORIGIN_FIELDS:
                        self.assertIn(field, origin)
                        self.assertTrue(str(origin[field]).strip())
                else:
                    self.assertEqual("HUMAN_PROVENANCE_CHECK_REQUIRED", origin["status"])
                    self.assertTrue(origin["missing"])
                    self.assertTrue(origin["evidence_available"])

    def test_origin_commit_is_a_commit_not_a_branch(self):
        """A branch moves. Provenance that moves is not provenance."""
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            if origin["status"] != "ESTABLISHED":
                continue
            with self.subTest(benchmark=bm):
                commit = origin["origin_commit"]
                self.assertEqual(40, len(commit))
                self.assertTrue(all(c in "0123456789abcdef" for c in commit))
                for branchy in ("main", "master", "HEAD", "develop"):
                    self.assertNotEqual(branchy, commit)

    def test_local_path_is_marked_non_authoritative(self):
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            if origin["status"] != "ESTABLISHED":
                continue
            with self.subTest(benchmark=bm):
                self.assertEqual("NON_AUTHORITATIVE_EXTRACTION_HISTORY",
                                 origin["local_path_authority"])

    def test_no_test_or_contract_depends_on_an_absolute_home_path(self):
        """Absolute home paths may appear as recorded history, never as a dependency.

        Scanned over the test tree rather than the manifests: a manifest may
        record where an extraction happened, but nothing executable may rely on
        it.
        """
        offenders = []
        tests_dir = os.path.join(_paths.VER3, "tests")
        for dirpath, dirnames, filenames in os.walk(tests_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                with open(full, encoding="utf-8") as fh:
                    for i, line in enumerate(fh, start=1):
                        if "/home/" in line and "REPO_ROOT" not in line:
                            offenders.append("%s:%d" % (os.path.relpath(full, _paths.REPO_ROOT), i))
        self.assertEqual([], offenders, "tests depending on a home directory: %s" % offenders)

    def test_bm003_declares_that_it_has_no_witness(self):
        """The authored source must not acquire a fake origin by symmetry."""
        man = _paths.source_manifest("BM-003")
        self.assertNotIn("immutable_origin", man)
        self.assertEqual("AUTHORED", man["provenance"]["origin"])
        self.assertNotIn("primary_witness", man["provenance"])


class TestImmutableOriginVerifiable(unittest.TestCase):
    """Verified against the origin repository when it is actually available."""

    @classmethod
    def setUpClass(cls):
        cls.root = _origin_root()

    def _skip_unless_available(self):
        if self.root is None:
            self.skipTest("origin repository not available beside this one")

    def test_declared_origin_file_hash_matches_the_real_file(self):
        self._skip_unless_available()
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            if origin["status"] != "ESTABLISHED":
                continue
            path = os.path.join(self.root, origin["repo_relative_path"])
            if not os.path.isfile(path):
                self.skipTest("origin file not present: %s" % origin["repo_relative_path"])
            with self.subTest(benchmark=bm):
                with open(path, "rb") as fh:
                    self.assertEqual(origin["origin_file_sha256"],
                                     hashlib.sha256(fh.read()).hexdigest())

    def test_extracted_value_hash_matches_the_declared_field(self):
        self._skip_unless_available()
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            if origin["status"] != "ESTABLISHED":
                continue
            path = os.path.join(self.root, origin["repo_relative_path"])
            if not os.path.isfile(path):
                self.skipTest("origin file not present")
            with self.subTest(benchmark=bm):
                with open(path, encoding="utf-8") as fh:
                    value = json.load(fh)[origin["extracted_field"]]
                self.assertEqual(origin["extracted_value_sha256"],
                                 hashlib.sha256(value.encode()).hexdigest())

    def test_the_request_is_that_value_plus_one_newline(self):
        """Closes the loop: declared origin -> extracted field -> frozen request."""
        self._skip_unless_available()
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            if origin["status"] != "ESTABLISHED":
                continue
            path = os.path.join(self.root, origin["repo_relative_path"])
            if not os.path.isfile(path):
                self.skipTest("origin file not present")
            with self.subTest(benchmark=bm):
                with open(path, encoding="utf-8") as fh:
                    value = json.load(fh)[origin["extracted_field"]]
                with open(_paths.request_path(bm), encoding="utf-8") as fh:
                    request = fh.read()
                self.assertEqual(value + "\n", request)

    def test_the_declared_commit_exists_and_contains_that_content(self):
        self._skip_unless_available()
        for bm in EXTRACTED:
            origin = _paths.source_manifest(bm)["immutable_origin"]
            if origin["status"] != "ESTABLISHED":
                continue
            with self.subTest(benchmark=bm):
                try:
                    blob = subprocess.check_output(
                        ["git", "show", "%s:%s" % (origin["origin_commit"],
                                                   origin["repo_relative_path"])],
                        cwd=self.root, stderr=subprocess.DEVNULL)
                except (subprocess.CalledProcessError, OSError):
                    self.skipTest("commit not reachable in the available clone")
                self.assertEqual(origin["origin_file_sha256"],
                                 hashlib.sha256(blob).hexdigest())


class TestBM002WitnessDiscrepancyPreserved(unittest.TestCase):
    """The two renderings must both survive the freeze."""

    def test_the_authoritative_quantity_is_the_fixture_spelling(self):
        with open(_paths.request_path("BM-002"), encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        self.assertIn("approximately 80-100 mm", text)
        self.assertNotIn("80--100", text)

    def test_the_discrepancy_is_still_recorded(self):
        man = _paths.source_manifest("BM-002")
        recorded = str(man["witness_comparison"])
        self.assertIn("80-100", recorded)
        self.assertIn("80--100", recorded)

    def test_the_review_document_still_shows_both_renderings(self):
        """A resolved decision is not a difference that never existed."""
        path = os.path.join(_paths.BENCHMARKS, "SOURCE_FREEZE_REVIEW.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("80-100 mm", text)
        self.assertIn("80--100 mm", text)


if __name__ == "__main__":
    unittest.main()
