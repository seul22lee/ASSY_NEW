"""assy_v3 cannot reach legacy, evaluation artifacts, or the KG project.

This test is the enforcement half of ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml.
The YAML is data, not documentation; this file is what makes it binding.

Rebuild policy rules enforced here:
  2. No Ver2 stage, schema, fallback, alias, mechanism card, rendered-sheet
     authority or CAD default may be imported into the new pipeline.
  3. Compatibility adapters require explicit approval, recorded with an expiry.
  4. Positive executable CAD references and Oracles are evaluation artifacts,
     never production inputs.

The two BLOCKING path roots are the ones worth restating. ver3/oracles/ holds the
statement of what must be true of a run; a stage reading it is reading its own
answer key. ver3/cad_validation/ holds human-built designs that are known to
work; reproducing one is not designing.
"""

import re
import unittest

from . import _paths


class TestForbiddenImports(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rules = _paths.load_yaml(_paths.FORBIDDEN_YAML)
        cls.sources = list(_paths.parsed_assy_v3())
        assert cls.sources, "assy_v3 contains no Python files; the scan would pass vacuously."

    def test_protected_package_is_this_tree(self):
        self.assertEqual(self.rules["protected_package"]["path"], "ver3/assy_v3")

    def test_no_forbidden_import_roots(self):
        forbidden = {entry["name"]: entry["why"] for entry in self.rules["forbidden_import_roots"]}
        violations = []
        for rel, _src, tree in self.sources:
            for line, root in _paths.import_roots(tree):
                if root in forbidden:
                    violations.append("%s:%d imports %r -- %s" % (rel, line, root, forbidden[root]))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_no_forbidden_path_literals(self):
        """No string in assy_v3 code points into a forbidden tree.

        Docstrings are exempt: this module's own package docstring names
        ver3/oracles/ in order to say it is unreachable, and a rule that made
        explaining itself a violation would just get the explanation deleted.
        """
        entries = self.rules["forbidden_path_roots"]
        violations = []
        for rel, _src, tree in self.sources:
            for line, text in _paths.code_strings(tree):
                for entry in entries:
                    root = entry["path"]
                    if root in text:
                        violations.append(
                            "%s:%d string %r reaches forbidden root %r (severity %s)"
                            % (rel, line, text, root, entry.get("severity", "normal"))
                        )
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_no_forbidden_symbols(self):
        forbidden = {e["symbol"]: e["why"] for e in self.rules["forbidden_symbols"]}
        violations = []
        for rel, _src, tree in self.sources:
            for line, name in _paths.identifiers(tree):
                if name in forbidden:
                    violations.append("%s:%d defines/uses %r -- %s" % (rel, line, name, forbidden[name]))
            for line, text in _paths.code_strings(tree):
                for sym in forbidden:
                    if sym in text:
                        violations.append("%s:%d string contains %r" % (rel, line, sym))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_no_forbidden_patterns(self):
        """Regexes over raw source, minus comment and docstring lines.

        Applied to raw text rather than the AST because these patterns describe
        code shapes (``or "mm"``, ``sys.path.insert``) that are easier to match
        textually than structurally, and a miss here is a silent default.
        """
        patterns = self.rules["forbidden_patterns"]
        violations = []
        for rel, src, tree in self.sources:
            doc_lines = _paths.docstring_line_numbers(tree)
            for entry in patterns:
                exempt = entry.get("exempt_paths", [])
                if any(rel.startswith(p) for p in exempt):
                    continue
                rx = re.compile(entry["pattern"])
                for i, line_text in enumerate(src.splitlines(), start=1):
                    if i in doc_lines:
                        continue
                    if line_text.lstrip().startswith("#"):
                        continue
                    if rx.search(line_text):
                        violations.append(
                            "%s:%d matches %s (%s) -- %s"
                            % (rel, i, entry["id"], entry["pattern"], entry["why"].strip().splitlines()[0])
                        )
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_approved_exceptions_are_well_formed(self):
        """An exception is a debt with a due date, not a permission.

        The list is expected to be empty. If it is not, every entry must carry an
        approver, a scope, an expiry and a removal plan -- an entry without an
        expiry is a decision to keep legacy, and that belongs in the retirement
        matrix instead.
        """
        required = set(self.rules["exception_requirements"]["required_fields"])
        for entry in self.rules["approved_exceptions"]:
            missing = required - set(entry)
            self.assertEqual(set(), missing, "exception %r missing %s" % (entry.get("id"), sorted(missing)))

    def test_no_adapter_modules(self):
        """Rebuild policy rule 3: no compatibility adapter without approval."""
        approved = {e.get("scope") for e in self.rules["approved_exceptions"]}
        suspicious = ("adapter", "compat", "legacy", "shim", "bridge_v2")
        violations = [
            rel for rel, _src, _tree in self.sources
            if any(word in rel.lower() for word in suspicious) and rel not in approved
        ]
        self.assertEqual([], violations, "unapproved adapter-shaped modules: %s" % violations)


if __name__ == "__main__":
    unittest.main()
