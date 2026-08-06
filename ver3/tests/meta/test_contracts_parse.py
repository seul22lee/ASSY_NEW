"""Every contract parses and declares the minimum a contract must declare.

A contract that does not parse is not a contract, and one without a schema
version cannot be amended safely. This test is cheap and catches the class of
error that silently disables everything downstream of it.
"""

import os
import unittest

from . import _paths


class TestContractsParse(unittest.TestCase):

    def test_all_contract_files_exist(self):
        missing = [n for n in _paths.CONTRACT_FILES
                   if not os.path.isfile(os.path.join(_paths.CONTRACTS, n))]
        self.assertEqual([], missing)

    def test_all_contracts_parse(self):
        for name in _paths.CONTRACT_FILES:
            with self.subTest(contract=name):
                data = _paths.contract(name)
                self.assertIsInstance(data, dict, "%s must be a mapping at the top level" % name)

    def test_top_level_yaml_parses(self):
        for path in (_paths.FORBIDDEN_YAML, _paths.RETIREMENT_YAML):
            with self.subTest(path=os.path.basename(path)):
                self.assertIsInstance(_paths.load_yaml(path), dict)

    def test_every_contract_declares_a_schema_version(self):
        for name in _paths.CONTRACT_FILES:
            with self.subTest(contract=name):
                self.assertIn("schema_version", _paths.contract(name))

    def test_every_contract_declares_status(self):
        """draft or frozen. STAGE_PROGRESSION_CONTRACT step 8 is what moves one."""
        for name in _paths.CONTRACT_FILES:
            with self.subTest(contract=name):
                self.assertIn(_paths.contract(name).get("status"), ("draft", "frozen"))

    def test_referenced_contracts_exist(self):
        """Every path in a contract's `references` list resolves on disk.

        A dangling reference makes a contract look more connected than it is.
        """
        violations = []
        for name in _paths.CONTRACT_FILES:
            for ref in _paths.contract(name).get("references", []) or []:
                if not os.path.exists(os.path.join(_paths.REPO_ROOT, ref)):
                    violations.append("%s references missing %s" % (name, ref))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_governing_authority_exists(self):
        for name in _paths.CONTRACT_FILES:
            with self.subTest(contract=name):
                gov = _paths.contract(name).get("governed_by")
                self.assertTrue(gov, "%s declares no governing authority" % name)
                self.assertTrue(os.path.exists(os.path.join(_paths.REPO_ROOT, gov)))


if __name__ == "__main__":
    unittest.main()
