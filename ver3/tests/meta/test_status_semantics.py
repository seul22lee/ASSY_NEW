"""The ExecutionStatus enum and STATUS_SEMANTICS.yaml cannot drift apart.

Checked in both directions. A value in the enum that the contract does not define
has no agreed meaning; a value in the contract that the enum lacks cannot be
recorded. Either way the names still look right, which is what makes drift here
worth a test rather than a review habit.
"""

import importlib.util
import os
import unittest

from . import _paths


def _load(module_name, relpath):
    """Load a module by path, without importing the ver3 package tree."""
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(_paths.ASSY_V3, relpath))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestStatusSemantics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.contract = _paths.contract("STATUS_SEMANTICS.yaml")
        cls.mod = _load("_status_under_test", os.path.join("providers", "status.py"))

    def test_enum_matches_contract_exactly(self):
        contract_names = set(self.contract["execution_statuses"])
        enum_names = {s.name for s in self.mod.ExecutionStatus}
        self.assertEqual(contract_names, enum_names)

    def test_enum_values_equal_their_names(self):
        """Serialized form is the name. A value that differs invites a mapping table."""
        for status in self.mod.ExecutionStatus:
            self.assertEqual(status.name, status.value)

    def test_severity_order_matches_contract(self):
        contract_order = self.contract["severity_order"]["order"]
        enum_order = [s.name for s in self.mod.SEVERITY_ORDER]
        self.assertEqual(contract_order, enum_order)

    def test_false_acceptance_is_the_worst(self):
        """It is the failure the architecture exists to prevent."""
        self.assertIs(self.mod.SEVERITY_ORDER[0], self.mod.ExecutionStatus.FALSE_ACCEPTANCE)

    def test_success_is_the_best(self):
        self.assertIs(self.mod.SEVERITY_ORDER[-1], self.mod.ExecutionStatus.SUCCESS)

    def test_safe_rejection_ranks_above_every_failure(self):
        """Correct restraint is not a defect.

        A benchmark that penalises SAFE_REJECTION produces a pipeline that
        overclaims, so it must sit below every genuine failure in severity.
        """
        order = self.mod.SEVERITY_ORDER
        safe = order.index(self.mod.ExecutionStatus.SAFE_REJECTION)
        worst_failure = order.index(self.mod.ExecutionStatus.PROVIDER_RATE_LIMIT)
        self.assertGreater(safe, worst_failure)

    def test_retryable_matches_contract(self):
        contract_retryable = {
            name for name, spec in self.contract["execution_statuses"].items()
            if spec.get("retryable") is True
        }
        enum_retryable = {s.name for s in self.mod.RETRYABLE}
        self.assertEqual(contract_retryable, enum_retryable)

    def test_quota_exhausted_is_not_retryable(self):
        """Distinct from a rate limit precisely because it cannot be waited out."""
        self.assertNotIn(self.mod.ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED, self.mod.RETRYABLE)

    def test_provider_conditions_carry_no_design_implication(self):
        for status in self.mod.PROVIDER_CONDITIONS:
            with self.subTest(status=status.name):
                spec = self.contract["execution_statuses"][status.name]
                self.assertEqual("NONE", spec["design_implication"])

    def test_model_capability_failure_is_not_a_provider_condition(self):
        """Forbidden collapse C-10: otherwise the benchmark measures the model."""
        self.assertNotIn(
            self.mod.ExecutionStatus.MODEL_CAPABILITY_FAILURE,
            self.mod.PROVIDER_CONDITIONS,
        )

    def test_every_status_declares_what_it_never_means(self):
        """The `never_means` list is what stops a status absorbing a neighbour."""
        exempt = {"SUCCESS"}
        for name, spec in self.contract["execution_statuses"].items():
            if name in exempt:
                continue
            with self.subTest(status=name):
                self.assertTrue(
                    spec.get("never_means") or spec.get("forbidden") or spec.get("must_not_be_collapsed_into"),
                    "%s does not say what it must not mean" % name,
                )

    def test_collapse_ids_are_unique(self):
        ids = [c["id"] for c in self.contract["forbidden_collapses"]]
        self.assertEqual(sorted(set(ids)), sorted(ids))

    def test_known_historical_collapses_are_covered(self):
        """The Ver2 defects this vocabulary was shaped by must each have a row."""
        collapses = " ".join(c["collapse"] for c in self.contract["forbidden_collapses"])
        for fragment in ("missing capability", "no evidence", "execution failure",
                         "provider failure", "truncated", "missing unit"):
            self.assertIn(fragment, collapses)


if __name__ == "__main__":
    unittest.main()
