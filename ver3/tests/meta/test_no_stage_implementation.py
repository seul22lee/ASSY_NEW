"""No Stage logic exists in assy_v3, and none may appear without its contract.

Rebuild policy rule 6 for this task: do not implement any Stage logic. This test
holds that line, and keeps holding it afterwards -- once stage work begins, it
fails on any stage module whose contract has not been through
STAGE_PROGRESSION_CONTRACT step 1.

The failure this guards against is the one that produced Ver2: a stage written
first, whose contract is then reverse-engineered from what it happens to emit. A
contract derived from an implementation cannot constrain that implementation.

It also guards the naming rule. GENERATED_ASSURANCE_PACKAGE_CONTRACT forbids the
word Oracle as an identifier inside production code, because the word appearing
there would mean the hidden answer key had reached the system being judged.
"""

import os
import unittest

from . import _paths


class TestNoStageImplementation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sources = list(_paths.parsed_assy_v3())
        cls.package = _paths.contract("GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml")

    def test_every_stage_module_has_a_contract(self):
        """A stage module may exist only if its contract does.

        This guard was "no stage may exist" while none did. Stage work has begun,
        so it now holds the line the docstring always described: the contract
        comes first (STAGE_PROGRESSION_CONTRACT step 1), and a stage whose
        contract was reverse-engineered from its own output is the Ver2 failure.
        """
        contracts_dir = os.path.join(_paths.CONTRACTS, "stages")
        violations = []
        for rel, _src, _tree in self.sources:
            base = os.path.basename(rel)
            for stage_id in _paths.STAGE_IDS:
                if base.startswith(stage_id + "_") or base == stage_id + ".py":
                    contract = os.path.join(contracts_dir, "%s_CONTRACT.yaml" % stage_id.upper())
                    if not os.path.isfile(contract):
                        violations.append("%s has no %s" % (rel, os.path.basename(contract)))
        self.assertEqual([], violations, "\n".join(violations))

    def test_only_contracted_stages_are_implemented(self):
        """No stage module may appear for a stage whose contract is unwritten."""
        contracts_dir = os.path.join(_paths.CONTRACTS, "stages")
        implemented = set()
        for rel, _src, _tree in self.sources:
            base = os.path.basename(rel)
            for stage_id in _paths.STAGE_IDS:
                if base.startswith(stage_id + "_") or base == stage_id + ".py":
                    implemented.add(stage_id)
        contracted = {s for s in _paths.STAGE_IDS
                      if os.path.isfile(os.path.join(contracts_dir, "%s_CONTRACT.yaml" % s.upper()))}
        self.assertEqual(set(), implemented - contracted,
                         "implemented without a contract: %s" % sorted(implemented - contracted))

    def test_provider_interfaces_have_no_implementation(self):
        """Deliverable M is definitions only.

        Every public method body must be a docstring plus NotImplementedError. An
        interface that quietly starts working is no longer a boundary.
        """
        import ast
        violations = []
        for rel, _src, tree in self.sources:
            if not rel.endswith(os.path.join("providers", "interfaces.py")):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                body = [n for n in node.body
                        if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
                if len(body) != 1 or not isinstance(body[0], ast.Raise):
                    violations.append("%s:%d %s has a body" % (rel, node.lineno, node.name))
        self.assertEqual([], violations, "\n".join(violations))

    def test_no_network_or_subprocess_in_assy_v3(self):
        """A boundary that can already make a call is not a boundary."""
        import ast
        banned = {"requests", "httpx", "urllib", "http", "socket", "subprocess", "openai", "anthropic"}
        violations = []
        for rel, _src, tree in self.sources:
            for line, root in _paths.import_roots(tree):
                if root in banned:
                    violations.append("%s:%d imports %s" % (rel, line, root))
        self.assertEqual([], violations, "\n".join(violations))

    def test_forbidden_naming_absent_from_production_code(self):
        """Identifiers and non-docstring strings only.

        Prose explaining why the word is forbidden is the one permitted
        occurrence, so docstrings are exempt -- a rule that punished its own
        explanation would just get the explanation removed.
        """
        forbidden = self.package["forbidden_names_in_production_code"]
        violations = []
        for rel, _src, tree in self.sources:
            for line, name in _paths.identifiers(tree):
                for bad in forbidden:
                    if bad in name:
                        violations.append("%s:%d identifier %r contains %r" % (rel, line, name, bad))
            for line, text in _paths.code_strings(tree):
                for bad in forbidden:
                    if bad in text:
                        violations.append("%s:%d string %r contains %r" % (rel, line, text, bad))
        self.assertEqual([], violations, "\n" + "\n".join(violations))

    def test_no_module_file_named_for_a_forbidden_concept(self):
        forbidden = [n.lower() for n in self.package["forbidden_names_in_production_code"]]
        violations = [
            rel for rel, _src, _tree in self.sources
            if any(bad in os.path.basename(rel).lower() for bad in forbidden)
        ]
        self.assertEqual([], violations, "module names: %s" % violations)


if __name__ == "__main__":
    unittest.main()
