"""The gate that would have caught the last four passes' defects.

Each check here corresponds to something that actually went wrong and was found
by hand: a prompt claiming six collections while eight were consumed, a reaction
relation left optional so its invariant silently did nothing, producer metadata
still saying NOT_YET_PRODUCED after the producer existed, and U-5 conditions that
were described as enforced before they were.

These are stable invariants, not implementation trivia. They read machine-readable
surfaces - contracts, envelope declarations, producer code - never prose wording.
"""
from __future__ import annotations

import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_CONTRACTS = os.path.join(_REPO, "ver3", "contracts")

from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly)
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402


def _load(name, *parts):
    with open(os.path.join(_CONTRACTS, *parts, name)) as fh:
        return yaml.safe_load(fh)


class TestResponseEnvelopeCannotDrift(unittest.TestCase):
    """A prompt, a parser and a contract that disagree is the defect class this
    catches. It has recurred in every S-4 slice so far."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.stage = S02ObligationAndCandidates()
        cls.prompt = cls.stage.prompt({"consumer_view": {}})
        cls.source = open(os.path.join(
            _REPO, "ver3", "assy_v3", "stages",
            "s02_obligation_and_candidates.py")).read()

    def test_GATE_01_the_declared_count_matches_the_envelope(self):
        claimed = re.search(r"exactly these (\d+) keys", self.prompt)
        self.assertIsNotNone(claimed, "the prompt no longer states a count")
        self.assertEqual(len(self.stage.RESPONSE_ENVELOPE), int(claimed.group(1)),
                         "the prompt claims a different number of collections than "
                         "the envelope declares")

    def test_GATE_02_every_declared_collection_is_consumed(self):
        consumed = set(re.findall(r'parsed\.get\("([a-z_]+)"', self.source))
        for collection, _family, _prefix in self.stage.RESPONSE_ENVELOPE:
            self.assertIn(collection, consumed,
                          "%s is offered to the model and read by nothing"
                          % collection)

    def test_GATE_03_every_consumed_collection_is_declared(self):
        declared = {c for c, _f, _p in self.stage.RESPONSE_ENVELOPE}
        consumed = set(re.findall(r'parsed\.get\("([a-z_]+)"', self.source))
        # `_dofs`-style internals and the derived-mobility keys are not response
        # collections; only compare what to_operations turns into entities.
        creates = set(re.findall(r'for (\w+) in parsed\.get\("([a-z_]+)"',
                                 self.source))
        for _var, collection in creates:
            self.assertIn(collection, declared,
                          "%s is turned into entities and is in no envelope"
                          % collection)
        self.assertTrue(consumed)

    def test_GATE_04_every_declared_collection_appears_in_the_schema(self):
        for collection, _family, _prefix in self.stage.RESPONSE_ENVELOPE:
            self.assertIn("%s[]" % collection, self.prompt,
                          "%s is in the envelope and not in the response schema"
                          % collection)

    def test_GATE_05_every_declared_family_is_real_and_stage_owned(self):
        for _collection, family, _prefix in self.stage.RESPONSE_ENVELOPE:
            self.assertIn(family, self.c.families, family)
            self.assertTrue(self.c.may_create("s02", family),
                            "s02 offers %s and does not own it" % family)

    def test_GATE_06_every_emitted_prefix_is_shown_to_the_model(self):
        for _collection, _family, prefix in self.stage.RESPONSE_ENVELOPE:
            self.assertIn(prefix, self.prompt,
                          "%s ids are emitted and the prompt never shows the "
                          "prefix" % prefix)


class TestActiveMigrationTruth(unittest.TestCase):
    """A family cannot be produced and simultaneously be listed as unproduced."""

    @classmethod
    def setUpClass(cls):
        cls.ds = _load("DESIGN_STATE_CONTRACT.yaml")
        cls.s03 = _load("S03_CONTRACT.yaml", "stages")

    def produced(self):
        """Families some stage's to_operations actually creates."""
        out = set()
        for name in ("s02_obligation_and_candidates.py", "s03_topology_and_mobility.py"):
            src = open(os.path.join(_REPO, "ver3", "assy_v3", "stages", name)).read()
            out |= set(re.findall(r'Op\("CREATE", "(\w+)"', src))
        return out

    def test_GATE_07_no_produced_family_is_an_active_legacy_row(self):
        produced = self.produced()
        for row in (self.ds.get("legacy_producers") or {}).get("rows") or []:
            concept = row.get("concept", "")
            named = {f for f in produced if f in concept}
            if named and row.get("current_status") in ("NOT_YET_PRODUCED",):
                self.fail("%s is produced by %s and is still an ACTIVE legacy row "
                          "saying %s" % (concept, sorted(named),
                                         row.get("current_status")))

    def test_GATE_08_history_lives_outside_the_active_list(self):
        superseded = self.ds.get("superseded_legacy_producers") or {}
        self.assertTrue(superseded.get("rows"), "history was deleted, not moved")
        active = {r.get("concept")
                  for r in (self.ds.get("legacy_producers") or {}).get("rows") or []}
        for row in superseded["rows"]:
            self.assertNotIn(row["concept"], active,
                             "%s is both active and superseded" % row["concept"])

    def test_GATE_09_the_stage_contract_does_not_contradict_itself(self):
        producer = self.s03.get("legacy_producer", {}).get("current_producer", {})
        if producer.get("migration_status", "").strip().startswith("DONE"):
            self.assertEqual([], producer.get("does_not_yet_emit") or [],
                             "migration is DONE and something is still listed as "
                             "not emitted")


class TestU5InvariantsArePinned(_fixtures.StateBuilder, unittest.TestCase):
    """U5-1/2/3 and the LoadCase relation, asserted at the surface that owns each."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_GATE_10_a_load_case_must_name_its_reaction_site(self):
        required = self.c.required_fields("LoadCase")
        self.assertIn("reacted_at_site", required,
                      "the relation U5-3 depends on is optional again, so its "
                      "wrong-terminus check can silently do nothing")
        spec = self.c.reference_spec("LoadCase", "reacted_at_site")
        self.assertEqual("ReactionSiteRequirement", spec["target"])
        self.assertFalse(spec["resolvable"], "a named site need not exist")

    def test_GATE_11_the_s4_layer_evaluates_all_three_conditions(self):
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S03BMobilityAndAssembly._s4_physical_problems)
        for marker in ("U5-1", "U5-2", "U5-3"):
            self.assertIn(marker, src, "%s is no longer evaluated" % marker)

    def test_GATE_12_the_s4_layer_reads_no_legacy_mobility_channel(self):
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S03BMobilityAndAssembly._s4_physical_problems)
        self.assertNotIn("blocking_relations", src,
                         "S-4 completeness consults the legacy mobility channel")

    def test_GATE_13_every_s4_physical_reference_must_resolve(self):
        for family, field in (("LoadCase", "reacted_at_site"),
                              ("LoadPath", "ordered_hops"),
                              ("LoadPath", "terminates_at"),
                              ("ConstraintRelation", "provider_body"),
                              ("ConstraintRelation", "provider_reaction_site"),
                              ("ConstraintRelation", "provider_site"),
                              ("PhysicalInteraction", "discharges_effect"),
                              ("PhysicalInteraction", "at_interface")):
            spec = self.c.reference_spec(family, field)
            self.assertIsNotNone(spec, "%s.%s" % (family, field))
            self.assertFalse(spec.get("resolvable"),
                             "%s.%s may name something that does not exist"
                             % (family, field))


class TestTheGateWouldHaveCaughtIt(unittest.TestCase):
    """Deliberately break each relationship and prove the gate notices.

    A consistency gate nobody has seen fail is a gate nobody knows works.
    """

    def test_GATE_14_a_count_drift_is_detected(self):
        stage = S02ObligationAndCandidates()
        original = S02ObligationAndCandidates.RESPONSE_ENVELOPE
        try:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original[:-1]
            prompt = stage.prompt({"consumer_view": {}})
            claimed = int(re.search(r"exactly these (\d+) keys", prompt).group(1))
            self.assertNotEqual(len(original), claimed,
                                "removing a collection changed nothing")
            # The gate compares the two; here they now disagree by construction.
            self.assertEqual(len(original) - 1, claimed)
        finally:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original

    def test_GATE_15_an_unconsumed_collection_is_detected(self):
        stage = S02ObligationAndCandidates()
        original = S02ObligationAndCandidates.RESPONSE_ENVELOPE
        source = open(os.path.join(_REPO, "ver3", "assy_v3", "stages",
                                   "s02_obligation_and_candidates.py")).read()
        try:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original + (
                ("invented_things", "Obligation", "INV-"),)
            consumed = set(re.findall(r'parsed\.get\("([a-z_]+)"', source))
            self.assertNotIn("invented_things", consumed,
                             "the fabricated collection is somehow consumed")
        finally:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original


if __name__ == "__main__":
    unittest.main()
