"""A responsibility's declared outputs must be what its code can actually create.

S9-E. `STAGE_RESPONSIBILITY_CONTRACT.permitted_output_semantics` was never checked
against the code, and three responsibilities had drifted:

    s02  created Assumption, declared nothing of the kind
    s01  created SourceClause, declared nothing of the kind
    s03a created LoadPath and AssemblyStep from response keys its own PROMPT
         never asks for - a second producer for two families s03b owns

Only the first was blocking, and it was blocking because this list is not
documentation. `derive_source_a` reads it to decide which families a consumer
CO-PRODUCES, so a family missing from it is a family the consumer view has no
reason to carry. s02 was therefore asked to author into a namespace it could not
see, and three independent live attempts died on DUPLICATE_ID: ASM-0001.

WHY THIS IS NOT `assertIn("Assumption", s02_outputs)`

That assertion would hold for exactly the family that had already collided. The
guard here DERIVES what each responsibility creates by reading every
`Op("CREATE", "<Family>", ...)` reachable from its class, and compares the whole
set. It names no family and no stage: the six responsibilities come from
`PRODUCING_RESPONSIBILITIES`, and each class answers `responsibility_id()` for
itself.
"""

import unittest

from . import _paths
from . import output_semantics_audit as audit

from ver3.assy_v3.pipeline.progression import PRODUCING_RESPONSIBILITIES
from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture
from ver3.assy_v3.stages.s02_obligation_and_candidates import S02ObligationAndCandidates
from ver3.assy_v3.stages.s03_topology_and_mobility import (
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.stages.s04_envelope_and_motion import (
    S04AEnvelopeAndReach, S04BPlacementAndMotion)

#: Every class that reasons as one of the producing responsibilities. Listed
#: because a class must be imported to be asked its own responsibility id; the
#: test below proves the list covers the contract rather than trusting it.
PRODUCING_CLASSES = (S01RequirementCapture, S02ObligationAndCandidates,
                     S03TopologyAndMobility, S03BMobilityAndAssembly,
                     S04AEnvelopeAndReach, S04BPlacementAndMotion)


class TestScanIsComplete(unittest.TestCase):
    """Before comparing anything, establish that the scan can see everything."""

    def test_every_producing_responsibility_has_a_class(self):
        found = set(audit.responsibility_creates(PRODUCING_CLASSES))
        self.assertEqual(set(PRODUCING_RESPONSIBILITIES), found)

    def test_no_create_names_its_family_dynamically(self):
        """A CREATE built from a variable is one this scan cannot read.

        Reported rather than ignored, because "the scan found no drift" and "the
        scan could not look" are different results and must not print the same.
        """
        self.assertEqual({}, audit.dynamic_create_sites(PRODUCING_CLASSES))

    def test_every_responsibility_creates_something(self):
        """A responsibility scanned as creating nothing is a scan that missed it."""
        creates = audit.responsibility_creates(PRODUCING_CLASSES)
        for rid in PRODUCING_RESPONSIBILITIES:
            with self.subTest(responsibility=rid):
                self.assertTrue(creates[rid],
                                "%s was scanned as creating no family at all" % rid)


class TestNoContractImplementationDrift(unittest.TestCase):
    """The guard itself, over all six responsibilities."""

    @classmethod
    def setUpClass(cls):
        cls.responsibility = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.ownership = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.actual = audit.responsibility_creates(PRODUCING_CLASSES)
        cls.universal = audit.universally_ownable(cls.ownership)

    def _problems(self, rid, declared=None):
        return audit.drift_problems(
            rid, self.actual[rid],
            self.declared(rid) if declared is None else declared,
            audit.may_create(self.ownership, audit.owner_of(rid)),
            self.universal)

    def declared(self, rid):
        return audit.declared_families(self.responsibility, rid)

    def test_no_responsibility_creates_what_it_does_not_declare(self):
        for rid in PRODUCING_RESPONSIBILITIES:
            with self.subTest(responsibility=rid):
                undeclared = sorted(self.actual[rid] - self.declared(rid))
                self.assertEqual([], undeclared)

    def test_no_responsibility_declares_what_it_may_not_write(self):
        for rid in PRODUCING_RESPONSIBILITIES:
            with self.subTest(responsibility=rid):
                authorized = audit.may_create(self.ownership, audit.owner_of(rid))
                self.assertEqual([], sorted(self.declared(rid) - authorized))

    def test_an_unproduced_declaration_is_a_universal_permission_or_nothing(self):
        for rid in PRODUCING_RESPONSIBILITIES:
            with self.subTest(responsibility=rid):
                unproduced = (self.declared(rid) - self.actual[rid]) - self.universal
                self.assertEqual([], sorted(unproduced))

    def test_the_whole_guard_is_clean(self):
        problems = []
        for rid in PRODUCING_RESPONSIBILITIES:
            problems.extend(self._problems(rid))
        self.assertEqual([], problems)


class TestTheGuardFailsOnTheDriftItWasWrittenFor(unittest.TestCase):
    """MUTATION. Each repaired drift, put back, must be rejected.

    Run against the real derived sets with only the declaration mutated, so these
    are the actual pre-fix repository states and not a hand-built analogy.
    """

    @classmethod
    def setUpClass(cls):
        cls.responsibility = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.ownership = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.actual = audit.responsibility_creates(PRODUCING_CLASSES)
        cls.universal = audit.universally_ownable(cls.ownership)

    def _problems(self, rid, declared):
        return audit.drift_problems(
            rid, self.actual[rid], declared,
            audit.may_create(self.ownership, audit.owner_of(rid)), self.universal)

    def test_the_s02_assumption_omission_is_rejected(self):
        """THE BLOCKER, exactly as the contract read before this commit."""
        declared = audit.declared_families(self.responsibility, "s02")
        self.assertIn("Assumption", declared, "the repair itself is missing")
        problems = self._problems("s02", declared - {"Assumption"})
        self.assertTrue(any("Assumption" in p and "does not declare" in p
                            for p in problems), problems)

    def test_the_s01_source_clause_omission_is_rejected(self):
        declared = audit.declared_families(self.responsibility, "s01")
        problems = self._problems("s01", declared - {"SourceClause"})
        self.assertTrue(any("SourceClause" in p and "does not declare" in p
                            for p in problems), problems)

    def test_a_declaration_beyond_the_write_boundary_is_rejected(self):
        """A family s02 could never write, claimed as an output."""
        declared = audit.declared_families(self.responsibility, "s02") | {"Body"}
        problems = self._problems("s02", declared)
        self.assertTrue(any("Body" in p and "would refuse" in p for p in problems),
                        problems)

    def test_a_stage_specific_family_nobody_produces_is_rejected(self):
        """`Envelope` is s04's and universally ownable by nobody."""
        declared = audit.declared_families(self.responsibility, "s02") | {"Envelope"}
        problems = self._problems("s02", declared)
        self.assertTrue(any("Envelope" in p for p in problems), problems)

    def test_an_unproduced_universally_ownable_family_is_accepted(self):
        """The rule that keeps the guard honest rather than merely strict.

        s01 declares `UnresolvedDecision` and produces none. That is a standing
        permission every stage holds, and a guard demanding exact equality would
        force it to be deleted - removing a legitimate permission to satisfy a
        test, which is the failure mode this whole commit exists to avoid.
        """
        self.assertEqual([], self._problems(
            "s01", audit.declared_families(self.responsibility, "s01")))
        self.assertIn("UnresolvedDecision",
                      audit.declared_families(self.responsibility, "s01"))
        self.assertNotIn("UnresolvedDecision", self.actual["s01"])


class TestS03ADoesNotSecondProduceS03BsFamilies(unittest.TestCase):
    """The third drift, kept as its own statement.

    s03a parsed `load_paths` and `assembly_steps`, which appear in no s03a prompt.
    A stale recording replayed through s03a could therefore create two families
    s03b owns, from a premise s03a does not have - it has decided no interaction
    yet. Removing the branches is what makes s03b's declaration true.
    """

    def test_s03a_creates_neither_load_path_nor_assembly_step(self):
        creates = audit.responsibility_creates(PRODUCING_CLASSES)
        self.assertNotIn("LoadPath", creates["s03a"])
        self.assertNotIn("AssemblyStep", creates["s03a"])

    def test_s03b_still_creates_both(self):
        """The families are not lost; they have one producer instead of two."""
        creates = audit.responsibility_creates(PRODUCING_CLASSES)
        self.assertIn("LoadPath", creates["s03b"])
        self.assertIn("AssemblyStep", creates["s03b"])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
