"""There is exactly one Ver3 package path, and it is ver3/assy_v3/.

ACP-001 changed the planned path from `ver3/assy3/` to `ver3/assy_v3/` through
the procedure recorded in ver3/phase0/ARCHITECTURE_CHANGE_PROPOSALS.yaml. This
test keeps that single-path property true afterwards.

The property worth protecting is not the spelling. It is that no ALIAS exists. A
symlink, a compatibility package, or a second name that resolves to the same tree
would each leave "which path is authoritative" permanently open, and that
ambiguity is the aliasing rebuild policy rule 2 retires. A path can be renamed
again by another proposal; what must never appear is two of them at once.

Two occurrences of the old token survive in ver3/oracles/. They are historical
observations - whether a package existed at a past moment - and Oracle files are
immutable to implementation work under INV-017. They are allowed by name here so
that the check stays exact rather than approximate.
"""

import os
import unittest

from . import _paths

OLD_TOKEN = "assy" + "3"          # split so this file's own text is not a hit
NEW_PATH = "ver3/assy_v3"

#: Oracle files recording a past observation. INV-017 makes them immutable, and
#: ACP-001 records the decision to leave them alone.
PERMITTED_HISTORICAL = {
    os.path.join("ver3", "oracles", "PRE_CAD_CORRECTION_STATE.yaml"),
    os.path.join("ver3", "oracles", "FINAL_PRE_CAD_CORRECTION_STATE.yaml"),
}

#: The proposal itself must quote the previous value; that is its purpose.
PROPOSAL_FILE = os.path.join("ver3", "phase0", "ARCHITECTURE_CHANGE_PROPOSALS.yaml")

SCANNED_SUFFIXES = (".py", ".yaml", ".yml", ".md", ".json", ".toml", ".cfg", ".txt")
SKIP_DIRS = {".git", "__pycache__", "node_modules", "vendor", ".github"}


def _scan_repo_for_old_token():
    hits = []
    for dirpath, dirnames, filenames in os.walk(_paths.REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(SCANNED_SUFFIXES):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, _paths.REPO_ROOT)
            if rel == PROPOSAL_FILE or rel == os.path.join("ver3", "tests", "meta", "test_package_path.py"):
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                # `assy_v3` contains no occurrence of the old token, so a plain
                # substring test is exact here.
                if OLD_TOKEN in line:
                    hits.append((rel, i, line.strip()[:100]))
    return hits


class TestSinglePackagePath(unittest.TestCase):

    def test_package_exists_at_the_new_path(self):
        self.assertTrue(os.path.isdir(_paths.ASSY_V3))
        self.assertTrue(os.path.isfile(os.path.join(_paths.ASSY_V3, "__init__.py")))

    def test_old_path_does_not_exist_on_disk(self):
        self.assertFalse(os.path.exists(os.path.join(_paths.VER3, OLD_TOKEN)))

    def test_no_alias_symlink_anywhere_under_ver3(self):
        """No symlink may resolve into the package tree.

        A symlink is the cheapest possible alias and the hardest to see in a
        diff, which is why it gets its own check rather than relying on the
        text scan.
        """
        aliases = []
        for dirpath, dirnames, filenames in os.walk(_paths.VER3):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in list(dirnames) + list(filenames):
                full = os.path.join(dirpath, name)
                if os.path.islink(full):
                    aliases.append((os.path.relpath(full, _paths.REPO_ROOT), os.readlink(full)))
        self.assertEqual([], aliases, "symlinks under ver3/: %s" % aliases)

    def test_no_compatibility_package_for_the_old_name(self):
        offenders = []
        for dirpath, dirnames, filenames in os.walk(_paths.VER3):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in list(dirnames) + [f[:-3] for f in filenames if f.endswith(".py")]:
                if name == OLD_TOKEN:
                    offenders.append(os.path.relpath(os.path.join(dirpath, name), _paths.REPO_ROOT))
        self.assertEqual([], offenders)

    def test_phase0_carries_no_reference_to_the_old_path(self):
        hits = [h for h in _scan_repo_for_old_token() if h[0].startswith(os.path.join("ver3", "phase0"))]
        self.assertEqual([], hits, "phase0 still references the old path:\n%s" % hits)

    def test_only_permitted_historical_occurrences_remain(self):
        hits = _scan_repo_for_old_token()
        unexpected = [h for h in hits if h[0] not in PERMITTED_HISTORICAL]
        self.assertEqual([], unexpected,
                         "unexpected old-path references:\n" +
                         "\n".join("%s:%d %s" % h for h in unexpected))

    def test_invariants_planned_validators_use_the_new_path(self):
        inv = _paths.load_yaml(os.path.join(_paths.VER3, "phase0", "ARCHITECTURE_INVARIANTS.yaml"))
        wrong = []
        for entry in inv["invariants"]:
            pv = entry.get("planned_validator", "")
            if pv.startswith("ver3/") and not (pv.startswith(NEW_PATH) or pv.startswith("ver3/tests/")):
                wrong.append((entry["invariant_id"], pv))
        self.assertEqual([], wrong, "planned validators outside the package path: %s" % wrong)

    def test_invariants_file_still_parses_and_is_intact(self):
        """A path substitution must not have disturbed the file's content.

        Counts are asserted because a careless sed is exactly how an authority
        file loses an entry without anyone noticing.
        """
        inv = _paths.load_yaml(os.path.join(_paths.VER3, "phase0", "ARCHITECTURE_INVARIANTS.yaml"))
        self.assertEqual(18, len(inv["invariants"]))
        self.assertEqual(32, len(inv["retirement_coverage"]))
        ids = [e["invariant_id"] for e in inv["invariants"]]
        self.assertEqual(["INV-%03d" % n for n in range(1, 19)], ids)


class TestChangeProposalRecord(unittest.TestCase):
    """The change is only legitimate because it is recorded. Check the record."""

    @classmethod
    def setUpClass(cls):
        cls.doc = _paths.load_yaml(os.path.join(_paths.REPO_ROOT, PROPOSAL_FILE))
        cls.acp001 = next(p for p in cls.doc["proposals"] if p["proposal_id"] == "ACP-001")

    def test_every_proposal_has_the_required_fields(self):
        required = {"proposal_id", "date", "status", "targets", "previous_value",
                    "new_value", "rationale", "semantic_change",
                    "affected_validators", "not_changed", "verification", "accepted_by"}
        for p in self.doc["proposals"]:
            with self.subTest(proposal=p.get("proposal_id")):
                self.assertEqual(set(), required - set(p))

    def test_acp001_records_both_values(self):
        self.assertEqual("ver3/" + OLD_TOKEN + "/", self.acp001["previous_value"])
        self.assertEqual(NEW_PATH + "/", self.acp001["new_value"])

    def test_acp001_declares_whether_the_change_is_semantic(self):
        self.assertIsInstance(self.acp001["semantic_change"], bool)
        self.assertFalse(self.acp001["semantic_change"])
        self.assertTrue(self.acp001["semantic_change_justification"].strip())

    def test_acp001_lists_every_affected_invariant(self):
        listed = set(self.acp001["affected_invariants"]["invariants"])
        self.assertEqual(15, len(listed))
        self.assertEqual(16, self.acp001["affected_invariants"]["count"])

    def test_acp001_validator_entries_are_a_before_and_after_pair(self):
        for entry in self.acp001["affected_validators"]:
            with self.subTest(invariant=entry["invariant"]):
                self.assertIn(OLD_TOKEN, entry["previous"])
                self.assertIn("assy_v3", entry["new"])
                self.assertNotIn(OLD_TOKEN, entry["new"])

    def test_acp001_explains_what_it_left_alone(self):
        """The Oracle occurrences must be justified, not merely missed."""
        untouched = {e["path"] for e in self.acp001["not_changed"]}
        for p in PERMITTED_HISTORICAL:
            self.assertIn(p.replace(os.sep, "/"), untouched)
        for e in self.acp001["not_changed"]:
            self.assertTrue(e["why"].strip())


if __name__ == "__main__":
    unittest.main()
