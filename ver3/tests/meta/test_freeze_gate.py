"""Three envelope fields block the Stage freeze gate, each on its own.

The independence claim is what these tests are for. It is easy to write a gate
that appears to check three things but really checks one — three conditions
OR-ed into a single flag look identical from outside until the day two of them
disagree.

The method: start from a fully SETTLED envelope, break exactly ONE field, and
assert the gate still closes. If it does, that field closed it by itself.
"""

import unittest

from . import _paths
from . import freeze_gate as fg


class TestGateOnRealSources(unittest.TestCase):
    """The gate must be closed right now — no source has been reviewed."""

    def test_gate_is_currently_closed(self):
        self.assertFalse(fg.stage_freeze_permitted())

    def test_every_benchmark_currently_blocks(self):
        blocked = {b["benchmark_id"] for b in fg.all_source_blockers()}
        self.assertEqual(set(_paths.BENCHMARK_IDS), blocked)

    def test_each_benchmark_blocks_on_all_three_fields(self):
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                fields = {b["field"] for b in fg.source_blockers(bm)}
                self.assertEqual(set(_paths.FREEZE_BLOCKING_FIELDS), fields)

    def test_every_blocker_states_a_reason(self):
        for b in fg.all_source_blockers():
            with self.subTest(benchmark=b["benchmark_id"], field=b["field"]):
                self.assertTrue(b["reason"].strip())

    def test_no_stage_contract_is_frozen_while_the_gate_is_closed(self):
        if fg.stage_freeze_permitted():
            self.skipTest("gate is open; this test guards the closed case")
        frozen = [n for n in _paths.CONTRACT_FILES
                  if _paths.contract(n).get("status") == "frozen"]
        self.assertEqual([], frozen, "contracts frozen behind a closed gate: %s" % frozen)


class TestEachFieldBlocksIndependently(unittest.TestCase):
    """One broken field at a time, against an otherwise settled envelope."""

    def _one(self, **overrides):
        return {"BM-001": fg.settled_envelope(**overrides)}

    def test_a_fully_settled_envelope_opens_the_gate(self):
        """The control. Without it, a gate that never opens would pass every test below."""
        self.assertTrue(fg.stage_freeze_permitted(["BM-001"], self._one()))

    def test_human_review_complete_false_blocks_alone(self):
        m = self._one(human_review_complete=False)
        blockers = fg.all_source_blockers(["BM-001"], m)
        self.assertFalse(fg.stage_freeze_permitted(["BM-001"], m))
        self.assertEqual(["human_review_complete"], [b["field"] for b in blockers])

    def test_frozen_false_blocks_alone(self):
        m = self._one(frozen=False)
        blockers = fg.all_source_blockers(["BM-001"], m)
        self.assertFalse(fg.stage_freeze_permitted(["BM-001"], m))
        self.assertEqual(["frozen"], [b["field"] for b in blockers])

    def test_authority_status_not_frozen_blocks_alone(self):
        m = self._one(authority_status="PROPOSED")
        blockers = fg.all_source_blockers(["BM-001"], m)
        self.assertFalse(fg.stage_freeze_permitted(["BM-001"], m))
        self.assertEqual(["authority_status"], [b["field"] for b in blockers])

    def test_superseded_authority_status_blocks_even_when_reviewed_and_frozen(self):
        """A superseded revision can be both reviewed and frozen and still be wrong.

        This is the case `frozen` alone cannot catch, and the reason
        authority_status is a separate field rather than a derived one.
        """
        m = self._one(authority_status="SUPERSEDED")
        self.assertFalse(fg.stage_freeze_permitted(["BM-001"], m))
        self.assertEqual(["authority_status"],
                         [b["field"] for b in fg.all_source_blockers(["BM-001"], m)])

    def test_frozen_without_review_blocks(self):
        """Marked frozen but never reviewed. `frozen` alone would let this through."""
        m = self._one(human_review_complete=False)
        self.assertFalse(fg.stage_freeze_permitted(["BM-001"], m))

    def test_reviewed_but_not_frozen_blocks(self):
        """Reviewed, bytes still open. `human_review_complete` alone would let this through."""
        m = self._one(frozen=False)
        self.assertFalse(fg.stage_freeze_permitted(["BM-001"], m))

    def test_a_missing_field_blocks_rather_than_defaulting_open(self):
        """An absent field must never read as satisfied.

        A gate that treats missing as passing fails open, which is the one
        direction a gate must never fail.
        """
        for field in _paths.FREEZE_BLOCKING_FIELDS:
            with self.subTest(missing=field):
                env = fg.settled_envelope()
                del env[field]
                self.assertFalse(fg.stage_freeze_permitted(["BM-001"], {"BM-001": env}))

    def test_one_unsettled_benchmark_blocks_all_three(self):
        """Two settled sources do not make up for a third that is not.

        The freeze rule needs all three; a majority is not a quorum here.
        """
        manifests = {
            "BM-001": fg.settled_envelope(),
            "BM-002": fg.settled_envelope(),
            "BM-003": fg.settled_envelope(frozen=False),
        }
        self.assertFalse(fg.stage_freeze_permitted(_paths.BENCHMARK_IDS, manifests))
        blockers = fg.all_source_blockers(_paths.BENCHMARK_IDS, manifests)
        self.assertEqual(["BM-003"], [b["benchmark_id"] for b in blockers])

    def test_all_three_settled_opens_the_gate(self):
        manifests = {bm: fg.settled_envelope() for bm in _paths.BENCHMARK_IDS}
        self.assertTrue(fg.stage_freeze_permitted(_paths.BENCHMARK_IDS, manifests))


class TestGateMatchesTheContract(unittest.TestCase):
    """The gate implemented here must be the gate the contract describes."""

    @classmethod
    def setUpClass(cls):
        cls.progression = _paths.contract("STAGE_PROGRESSION_CONTRACT.yaml")

    def test_contract_names_the_three_blocking_fields(self):
        precondition = str(self.progression["freeze_rule"].get("source_preconditions", ""))
        for field in _paths.FREEZE_BLOCKING_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, precondition)

    def test_contract_requires_the_frozen_authority_status(self):
        self.assertIn(fg.REQUIRED_AUTHORITY_STATUS,
                      str(self.progression["freeze_rule"]["source_preconditions"]))

    def test_contract_still_requires_all_three_benchmarks(self):
        self.assertIn("ALL THREE", str(self.progression["progression_steps"][7]["precondition"]))


if __name__ == "__main__":
    unittest.main()
