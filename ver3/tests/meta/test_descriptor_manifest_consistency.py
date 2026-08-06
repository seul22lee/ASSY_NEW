"""A descriptor and its source manifest must never disagree silently.

Two files describe the same source. Whenever the same fact is written in two
places it can drift, and here the drift is dangerous in a specific way: the
freeze gate reads the MANIFEST, while a human skim-reading readiness is far more
likely to open the DESCRIPTOR. A descriptor claiming `frozen: true` over a
manifest that says otherwise would mislead exactly the reader who cannot see the
gate's answer.

So every duplicated fact is compared, and a missing field on either side is a
failure rather than a skip — an absent field is the easiest way for two records
to stop disagreeing without either becoming right.
"""

import hashlib
import os
import unittest

from . import _paths

#: (descriptor key under `source`, manifest envelope key)
MIRRORED_FIELDS = [
    ("frozen", "frozen"),
    ("authority_status", "authority_status"),
    ("request_sha256", "request_sha256"),
]


def _descriptor(bm):
    return _paths.load_yaml(os.path.join(_paths.BENCHMARKS, bm, "descriptor.yaml"))


class TestDescriptorManifestAgreement(unittest.TestCase):

    def test_benchmark_id_agrees(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertEqual(bm, _descriptor(bm)["benchmark_id"])
                self.assertEqual(bm, _paths.source_manifest(bm)["benchmark_id"])

    def test_descriptor_points_at_the_canonical_manifest(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                declared = _descriptor(bm)["source"]["manifest"]
                self.assertEqual("ver3/benchmarks/%s/source/source_manifest.yaml" % bm, declared)
                self.assertTrue(os.path.isfile(os.path.join(_paths.REPO_ROOT, declared)))

    def test_descriptor_points_at_the_canonical_request(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                declared = _descriptor(bm)["source"]["request_path"]
                self.assertEqual("ver3/benchmarks/%s/source/request.txt" % bm, declared)
                self.assertTrue(os.path.isfile(os.path.join(_paths.REPO_ROOT, declared)))

    def test_manifest_artifact_points_at_the_same_request(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertEqual(_descriptor(bm)["source"]["request_path"],
                                 _paths.source_manifest(bm)["artifact"])

    def test_mirrored_fields_are_equal_and_present_on_both_sides(self):
        for bm in _paths.BENCHMARK_IDS:
            desc, man = _descriptor(bm)["source"], _paths.source_manifest(bm)
            for dkey, mkey in MIRRORED_FIELDS:
                with self.subTest(benchmark=bm, field=dkey):
                    self.assertIn(dkey, desc, "descriptor is missing %s" % dkey)
                    self.assertIn(mkey, man, "manifest is missing %s" % mkey)
                    self.assertEqual(desc[dkey], man[mkey])

    def test_human_review_completion_agrees(self):
        """Spelled differently on each side, so compared by meaning."""
        for bm in _paths.BENCHMARK_IDS:
            desc, man = _descriptor(bm)["source"], _paths.source_manifest(bm)
            with self.subTest(benchmark=bm):
                self.assertEqual(desc["human_review"] == "HUMAN_REVIEW_COMPLETE",
                                 man["human_review_complete"])

    def test_production_readability_agrees(self):
        for bm in _paths.BENCHMARK_IDS:
            desc, man = _descriptor(bm)["source"], _paths.source_manifest(bm)
            with self.subTest(benchmark=bm):
                self.assertEqual("s01", desc["read_by"])
                self.assertTrue(man["production_readable"])

    def test_oracle_visibility_agrees_and_is_false(self):
        for bm in _paths.BENCHMARK_IDS:
            desc, man = _descriptor(bm), _paths.source_manifest(bm)
            with self.subTest(benchmark=bm):
                self.assertFalse(man["oracle_visible_to_production"])
                never = desc["oracle"]["never_visible_to"]
                for who in ("production_stages", "generation_models", "prompts", "retrieval"):
                    self.assertIn(who, never)

    def test_positive_reference_visibility_agrees_and_is_false(self):
        for bm in _paths.BENCHMARK_IDS:
            desc, man = _descriptor(bm), _paths.source_manifest(bm)
            with self.subTest(benchmark=bm):
                self.assertFalse(man["positive_reference_visible_to_production"])
                ref = desc["positive_executable_reference"]
                self.assertIn("NEVER a production input", ref["role"])
                self.assertIn("never a scoring input", ref["scoring"])

    def test_the_shared_hash_matches_the_file_on_disk(self):
        """Both sides may agree with each other and still be stale."""
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                with open(_paths.request_path(bm), "rb") as fh:
                    actual = hashlib.sha256(fh.read()).hexdigest()
                self.assertEqual(actual, _descriptor(bm)["source"]["request_sha256"])
                self.assertEqual(actual, _paths.source_manifest(bm)["request_sha256"])


class TestExactlyOneCanonicalArtifact(unittest.TestCase):

    def test_exactly_one_manifest_per_benchmark(self):
        found = {}
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn == "source_manifest.yaml":
                    bm = os.path.relpath(dirpath, _paths.BENCHMARKS).split(os.sep)[0]
                    found.setdefault(bm, []).append(os.path.join(dirpath, fn))
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertEqual([_paths.source_manifest_path(bm)], found.get(bm, []))

    def test_exactly_one_request_per_benchmark(self):
        found = {}
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn == "request.txt":
                    bm = os.path.relpath(dirpath, _paths.BENCHMARKS).split(os.sep)[0]
                    found.setdefault(bm, []).append(os.path.join(dirpath, fn))
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                self.assertEqual([_paths.request_path(bm)], found.get(bm, []))

    def test_no_symlink_redirect_or_duplicate_envelope(self):
        offenders = []
        for dirpath, dirnames, filenames in os.walk(_paths.BENCHMARKS):
            for name in list(dirnames) + list(filenames):
                full = os.path.join(dirpath, name)
                if os.path.islink(full):
                    offenders.append(("symlink", os.path.relpath(full, _paths.REPO_ROOT)))
                elif name.lower() in ("source_manifest.yml", "manifest.yaml",
                                      "source_manifest.bak", "source_manifest.old"):
                    offenders.append(("duplicate", os.path.relpath(full, _paths.REPO_ROOT)))
        self.assertEqual([], offenders)

    def test_the_resolver_has_no_fallback_path(self):
        """One expression, no existence check, no second location to try.

        A resolver that falls back makes two layouts permanently valid, which is
        the state normalization was meant to end.
        """
        import inspect
        src = inspect.getsource(_paths.source_manifest_path)
        body = [ln.strip() for ln in src.splitlines()
                if ln.strip() and not ln.strip().startswith(("#", '"', "'", "def"))]
        body = [ln for ln in body if not ln.endswith('"""')]
        self.assertEqual(1, len([ln for ln in body if ln.startswith("return")]))
        for forbidden in ("os.path.exists", "os.path.isfile", "if ", "try:", "except"):
            self.assertNotIn(forbidden, src.split('"""')[-1])


if __name__ == "__main__":
    unittest.main()
