"""Artifact-hash manifests are built last and verified immediately.

Regression for a real defect: a BM-002 simulation run left four stale hashes,
because a second partial run rewrote reports and one video while a manifest from
the first run was already on disk. The manifest looked complete and four entries
were wrong.

Manually refreshing the manifest fixed that instance and fixed nothing about the
cause, so these tests exercise the shared utility rather than the artifacts. They
run entirely on temporary files — no simulation, no video rendering, no CAD.
"""

import hashlib
import os
import shutil
import sys
import tempfile
import unittest

from . import _paths

TOOLS = os.path.join(_paths.VER3, "cad_validation", "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import manifest_util as mu  # noqa: E402


class ManifestTempCase(unittest.TestCase):

    def setUp(self):
        self.here = tempfile.mkdtemp(prefix="manifest_regression_")
        self.out = os.path.join(self.here, "out")
        self.sim = os.path.join(self.here, "sim")
        os.makedirs(os.path.join(self.out, "plots"))
        os.makedirs(os.path.join(self.out, "review"))
        os.makedirs(self.sim)
        self.artifacts = {
            os.path.join(self.out, "report_a.json"): b'{"a": 1}',
            os.path.join(self.out, "report_b.json"): b'{"b": 2}',
            os.path.join(self.out, "plots", "plot.png"): b"\x89PNG fake",
            os.path.join(self.out, "review", "clip.mp4"): b"fake mp4 bytes",
            os.path.join(self.out, "review", "clip.json"): b'{"frames": 3}',
            os.path.join(self.sim, "model.xml"): b"<mujoco/>",
        }

    def tearDown(self):
        shutil.rmtree(self.here, ignore_errors=True)

    def _write_all(self):
        """Every artifact written and CLOSED before any manifest exists."""
        for path, data in self.artifacts.items():
            with open(path, "wb") as fh:
                fh.write(data)

    def _build(self):
        return mu.build_manifest([self.out, self.sim], self.here,
                                 extra={"reference_id": "TEST"})

    def _manifest_path(self):
        return os.path.join(self.out, mu.MANIFEST_FILENAME)


class TestOrdering(ManifestTempCase):

    def test_all_artifacts_exist_before_manifest_generation(self):
        self._write_all()
        for path in self.artifacts:
            self.assertTrue(os.path.isfile(path))
        self.assertFalse(os.path.exists(self._manifest_path()))
        doc = self._build()
        self.assertEqual(len(self.artifacts), doc["file_count"])

    def test_the_manifest_is_written_last(self):
        """Every tracked artifact must predate the manifest file."""
        self._write_all()
        doc = self._build()
        mu.write_manifest(doc, self._manifest_path())
        manifest_mtime = os.path.getmtime(self._manifest_path())
        for path in self.artifacts:
            with self.subTest(artifact=os.path.basename(path)):
                self.assertLessEqual(os.path.getmtime(path), manifest_mtime)

    def test_every_entry_rehashes_correctly(self):
        self._write_all()
        doc = self._build()
        mu.write_manifest(doc, self._manifest_path())
        self.assertEqual([], mu.verify(doc, self.here))
        for row in doc["files"]:
            with self.subTest(path=row["path"]):
                full = os.path.join(self.here, row["path"])
                with open(full, "rb") as fh:
                    self.assertEqual(row["sha256"], hashlib.sha256(fh.read()).hexdigest())

    def test_output_traversal_order_is_deterministic(self):
        """Row order must not depend on how the filesystem yields entries.

        A manifest whose ordering varies between runs cannot be diffed, which is
        most of what a manifest is for.
        """
        self._write_all()
        first = [r["path"] for r in self._build()["files"]]
        for _ in range(3):
            self.assertEqual(first, [r["path"] for r in self._build()["files"]])
        self.assertEqual(sorted(first), first)


class TestMutationDetection(ManifestTempCase):

    def test_changing_a_tracked_artifact_after_generation_is_detected(self):
        """The exact BM-002 failure: an artifact reaches final contents too late."""
        self._write_all()
        doc = self._build()
        mu.write_manifest(doc, self._manifest_path())
        self.assertEqual([], mu.verify(doc, self.here))

        victim = os.path.join(self.out, "report_a.json")
        with open(victim, "wb") as fh:
            fh.write(b'{"a": 1, "added_after_the_manifest": true}')

        problems = mu.verify(doc, self.here)
        self.assertEqual(1, len(problems))
        self.assertEqual("CHANGED", problems[0]["problem"])
        self.assertEqual("out/report_a.json", problems[0]["path"])
        self.assertNotEqual(problems[0]["recorded_sha256"], problems[0]["actual_sha256"])

    def test_a_deleted_artifact_is_detected(self):
        self._write_all()
        doc = self._build()
        os.remove(os.path.join(self.out, "review", "clip.mp4"))
        problems = mu.verify(doc, self.here)
        self.assertEqual(["MISSING"], [p["problem"] for p in problems])

    def test_a_same_length_edit_is_detected(self):
        """Byte count alone would miss this; the hash does not."""
        self._write_all()
        doc = self._build()
        victim = os.path.join(self.out, "report_b.json")
        with open(victim, "wb") as fh:
            fh.write(b'{"b": 3}')          # same length, different content
        problems = mu.verify(doc, self.here)
        self.assertEqual(1, len(problems))
        self.assertEqual("CHANGED", problems[0]["problem"])
        self.assertEqual(problems[0]["recorded_bytes"], problems[0]["actual_bytes"])

    def test_build_refuses_to_return_a_manifest_that_does_not_verify(self):
        """A manifest that is wrong at birth must not reach disk."""
        self._write_all()
        real_sha = mu.sha256_file

        calls = {"n": 0}

        def drifting(path):
            # First hash is recorded; the verification pass sees a different one,
            # standing in for a writer that was still open during collection.
            calls["n"] += 1
            if calls["n"] <= len(self.artifacts):
                return real_sha(path)
            return "0" * 64

        mu.sha256_file = drifting
        try:
            with self.assertRaises(mu.ManifestVerificationError):
                self._build()
        finally:
            mu.sha256_file = real_sha


class TestSelfHashing(ManifestTempCase):

    def test_the_manifest_does_not_hash_itself(self):
        """A self-hash is unsatisfiable: writing it in changes the file."""
        self._write_all()
        doc = self._build()
        mu.write_manifest(doc, self._manifest_path())
        paths = [r["path"] for r in doc["files"]]
        self.assertNotIn("out/" + mu.MANIFEST_FILENAME, paths)
        for p in paths:
            self.assertNotEqual(mu.MANIFEST_FILENAME, os.path.basename(p))

    def test_rebuilding_after_writing_still_excludes_the_manifest(self):
        """The second build must not pick up the first build's output."""
        self._write_all()
        mu.write_manifest(self._build(), self._manifest_path())
        second = mu.build_manifest([self.out, self.sim], self.here, extra={})
        self.assertEqual(len(self.artifacts), second["file_count"])

    def test_a_self_entry_is_reported_as_an_error_not_ignored(self):
        self._write_all()
        doc = self._build()
        mu.write_manifest(doc, self._manifest_path())
        doc["files"].append({"path": "out/" + mu.MANIFEST_FILENAME,
                             "bytes": 1, "sha256": "0" * 64})
        problems = mu.verify(doc, self.here)
        self.assertEqual(["SELF_ENTRY"], [p["problem"] for p in problems])


class TestRealBM002Manifests(unittest.TestCase):
    """The shipped manifests must verify with the same utility. No rerun."""

    EXE = os.path.join(_paths.VER3, "cad_validation", "BM-002",
                       "executable_references", "EXE-BM002-01")

    def _check(self, rel):
        import yaml
        path = os.path.join(self.EXE, rel)
        if not os.path.isfile(path):
            self.skipTest("%s not present" % rel)
        with open(path) as fh:
            doc = yaml.safe_load(fh)
        problems = mu.verify(doc, self.EXE)
        self.assertEqual([], problems, "%s: %s" % (rel, problems))

    def test_phase_a_manifest_verifies(self):
        self._check(os.path.join("validation", "artifact_hashes.yaml"))

    def test_simulation_manifest_verifies(self):
        self._check(os.path.join("validation", "simulation", "artifact_hashes.yaml"))

    def test_neither_manifest_hashes_itself(self):
        import yaml
        for rel in (os.path.join("validation", "artifact_hashes.yaml"),
                    os.path.join("validation", "simulation", "artifact_hashes.yaml")):
            path = os.path.join(self.EXE, rel)
            if not os.path.isfile(path):
                continue
            with open(path) as fh:
                doc = yaml.safe_load(fh)
            with self.subTest(manifest=rel):
                for row in doc["files"]:
                    self.assertNotEqual(mu.MANIFEST_FILENAME, os.path.basename(row["path"]))

    def test_the_generator_calls_the_shared_utility(self):
        """The permanent fix must be in the generator, not in a manual refresh."""
        gen = os.path.join(self.EXE, "simulate_lift.py")
        if not os.path.isfile(gen):
            self.skipTest("generator not present")
        with open(gen, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("manifest_util", src)
        self.assertIn("build_manifest", src)
        self.assertIn("ManifestVerificationError", src)


if __name__ == "__main__":
    unittest.main()
