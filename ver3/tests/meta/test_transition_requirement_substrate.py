"""The vocabulary for a stateful transition, before anything produces one.

A mechanism that holds its own configurations restrains them: a latch that keeps
a lid shut is a restraint that is active while shut and released to open. The
state so far can say the restraint is active - `MobilityExpectation` BLOCKED_BY -
and can say two configurations differ - `Configuration.distinguishing_basis` -
but it has no way to say WHAT STATE CHANGE MUST BE POSSIBLE. Consumers that
needed that have had to infer it, and every available inference is wrong:

  from `child_group`          which side of a joint moves in the world is a fact
                              about the whole mechanism, not about the joint
  from `distinguishing_basis` "these two states differ in this DOF" is not
                              "this DOF must be free"
  from BLOCKED_BY             "a restraint is active in this state" is not
                              "no transition can leave this state"

`TransitionRequirement` says it instead: directed, symbolic, and carrying no
realization. `ConstraintRelation.blocked_relative_motions` is the other half -
which relative joint motion a restraint removes, declared rather than matched out
of group ids.

UNIT 1 IS SUBSTRATE ONLY. No stage requires the family, no producer writes one,
and a state containing none is complete. These tests defend the vocabulary and
the canonical machinery it rides on; they name no candidate and no benchmark.
"""
import copy
import unittest

import yaml

import os
from . import _fixtures, _paths

from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

CONTRACT = os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                        "DESIGN_STATE_CONTRACT.yaml")
DOFS = ("TX", "TY", "TZ", "RX", "RY", "RZ")


class _Substrate(_fixtures.StateBuilder, unittest.TestCase):
    """Two configurations and a joint, with nothing benchmark-specific in them."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        with open(CONTRACT) as fh:
            cls.doc = yaml.safe_load(fh)
        cls.families = dict(cls.doc["entity_families"])
        cls.families.update(cls.doc.get("assurance_families") or {})

    def upstream(self, run="substrate"):
        s = DesignState(run_id=run)
        self.add(s, "s03", "Body", "BOD-1")
        self.add(s, "s03", "RigidGroup", "RGP-1", body="BOD-1", members=["BOD-1"],
                 is_default=True)
        self.add(s, "s03", "RigidGroup", "RGP-2", body="BOD-1", members=["BOD-1"],
                 is_default=False)
        self.add(s, "s03", "Joint", "JNT-1", joint_type="REVOLUTE",
                 parent_group="RGP-1", child_group="RGP-2", dof=["RZ"],
                 axis_direction="+Z", frame_ids=["FRM-1"])
        for cid, name in (("CFG-1", "one"), ("CFG-2", "two")):
            self.add(s, "s03", "Configuration", cid, name=name, kind="STABLE",
                     bodies_present=["BOD-1"], expected_mobility=[])
        self.add(s, "s03", "ConstraintRelation", "CRL-1", retained_group="RGP-2",
                 blocked_dofs=["RZ"], configurations=["CFG-1"],
                 driver="KINEMATIC_NECESSITY", provider_body="BOD-1")
        return s

    def requirement(self, **over):
        fields = {"from_configuration": "CFG-1", "to_configuration": "CFG-2",
                  "required_relative_motions": [{"joint": "JNT-1", "dof": "RZ"}],
                  "released_constraints": ["CRL-1"]}
        fields.update(over)
        return fields

    def commit(self, state, family, eid, fields, stage="s03"):
        patch = StagePatch(
            patch_id="%s-%d" % (eid, len(state.applied_patches)), run_id=state.run_id,
            stage_id=stage, stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=[Op("CREATE", family, eid, dict(fields), "s03b:relations")],
            execution_status="SUCCESS", provenance={"purpose": "substrate test"})
        problems = state.validate(patch)
        if not problems:
            state.apply(patch)
        return problems


# ======================================================================
# The family, and the references it declares
# ======================================================================

class TestTransitionRequirementIsCanonical(_Substrate):

    def test_a_valid_directed_requirement_is_accepted(self):
        s = self.upstream()
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        stored = next(r for r in s.family("TransitionRequirement")
                      if r["entity_id"] == "TRQ-1")
        self.assertEqual("CFG-1", stored["from_configuration"])
        self.assertEqual("CFG-2", stored["to_configuration"])

    def test_direction_is_carried_and_the_reverse_is_a_different_record(self):
        """A -> B does not imply B -> A: a mechanism that closes and cannot
        reopen satisfies one and fails the other."""
        s = self.upstream()
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        self.assertEqual([], self.commit(
            s, "TransitionRequirement", "TRQ-2",
            self.requirement(from_configuration="CFG-2", to_configuration="CFG-1")))
        pair = {r["entity_id"]: (r["from_configuration"], r["to_configuration"])
                for r in s.family("TransitionRequirement")}
        self.assertEqual(("CFG-1", "CFG-2"), pair["TRQ-1"])
        self.assertEqual(("CFG-2", "CFG-1"), pair["TRQ-2"])

    def test_the_endpoints_must_be_configurations(self):
        for field in ("from_configuration", "to_configuration"):
            with self.subTest(field=field):
                s = self.upstream()
                problems = self.commit(s, "TransitionRequirement", "TRQ-X",
                                       self.requirement(**{field: "JNT-1"}))
                self.assertTrue(any("REFERENCE_FAMILY" in p and field in p
                                    for p in problems), problems)

    def test_an_endpoint_that_resolves_to_nothing_is_refused(self):
        s = self.upstream()
        problems = self.commit(s, "TransitionRequirement", "TRQ-X",
                               self.requirement(to_configuration="CFG-NOWHERE"))
        self.assertTrue(problems)

    def test_a_required_motion_names_a_joint(self):
        s = self.upstream()
        problems = self.commit(
            s, "TransitionRequirement", "TRQ-X",
            self.requirement(required_relative_motions=[{"joint": "RGP-2",
                                                         "dof": "RZ"}]))
        self.assertTrue(any("REFERENCE_FAMILY" in p and "joint" in p
                            for p in problems), problems)

    def test_a_required_motion_uses_the_canonical_dof_vocabulary(self):
        s = self.upstream()
        problems = self.commit(
            s, "TransitionRequirement", "TRQ-X",
            self.requirement(required_relative_motions=[{"joint": "JNT-1",
                                                         "dof": "SPIN"}]))
        self.assertTrue(any("RECORD_VALUE" in p and "SPIN" in p for p in problems),
                        problems)

    def test_every_canonical_dof_is_accepted(self):
        for dof in DOFS:
            with self.subTest(dof=dof):
                s = self.upstream()
                self.assertEqual([], self.commit(
                    s, "TransitionRequirement", "TRQ-%s" % dof,
                    self.requirement(required_relative_motions=[{"joint": "JNT-1",
                                                                 "dof": dof}])))

    def test_a_requirement_that_requires_no_motion_is_refused(self):
        """A transition requirement naming no motion requires nothing."""
        s = self.upstream()
        problems = self.commit(s, "TransitionRequirement", "TRQ-X",
                               self.requirement(required_relative_motions=[]))
        self.assertTrue(any("transition_requires_motion" in p for p in problems),
                        problems)

    def test_released_constraints_must_be_constraint_relations(self):
        s = self.upstream()
        problems = self.commit(s, "TransitionRequirement", "TRQ-X",
                               self.requirement(released_constraints=["JNT-1"]))
        self.assertTrue(any("REFERENCE_FAMILY" in p and "released_constraints" in p
                            for p in problems), problems)

    def test_released_constraints_may_be_empty(self):
        s = self.upstream()
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement(released_constraints=[])))

    def test_it_carries_no_realization(self):
        """No angle, displacement, pose, path or swept volume. A requirement
        holding one would look like evidence that it was met."""
        declared = set(self.families["TransitionRequirement"]["required_fields"])
        declared |= set(self.families["TransitionRequirement"].get("optional_fields")
                        or [])
        for token in ("angle", "displacement", "coordinate", "pose", "path",
                      "swept", "origin", "extent", "distance", "travel"):
            for field in declared:
                self.assertNotIn(token, field.lower())


# ======================================================================
# The other half of the bridge
# ======================================================================

class TestBlockedRelativeMotions(_Substrate):

    def relation(self, **over):
        fields = {"retained_group": "RGP-2", "blocked_dofs": ["RZ"],
                  "configurations": ["CFG-1"], "driver": "KINEMATIC_NECESSITY",
                  "provider_body": "BOD-1"}
        fields.update(over)
        return fields

    def test_a_declared_linkage_is_accepted(self):
        s = self.upstream()
        self.assertEqual([], self.commit(
            s, "ConstraintRelation", "CRL-2",
            self.relation(blocked_relative_motions=[{"joint": "JNT-1",
                                                     "dof": "RZ"}])))

    def test_its_joint_must_resolve_to_a_joint(self):
        s = self.upstream()
        problems = self.commit(
            s, "ConstraintRelation", "CRL-2",
            self.relation(blocked_relative_motions=[{"joint": "CFG-1",
                                                     "dof": "RZ"}]))
        self.assertTrue(any("REFERENCE_FAMILY" in p for p in problems), problems)

    def test_its_dof_uses_the_canonical_vocabulary(self):
        s = self.upstream()
        problems = self.commit(
            s, "ConstraintRelation", "CRL-2",
            self.relation(blocked_relative_motions=[{"joint": "JNT-1",
                                                     "dof": "sideways"}]))
        self.assertTrue(any("RECORD_VALUE" in p for p in problems), problems)

    def test_a_relation_without_it_remains_valid(self):
        """Existing relations declared none, and nothing may require one yet."""
        s = self.upstream()
        self.assertEqual([], self.commit(s, "ConstraintRelation", "CRL-2",
                                         self.relation()))

    def test_blocked_dofs_needs_no_matching_entry_yet(self):
        s = self.upstream()
        self.assertEqual([], self.commit(
            s, "ConstraintRelation", "CRL-2",
            self.relation(blocked_dofs=["TX", "TY", "RZ"],
                          blocked_relative_motions=[{"joint": "JNT-1",
                                                     "dof": "RZ"}])))

    def test_the_field_is_optional_in_the_contract(self):
        spec = self.families["ConstraintRelation"]
        self.assertIn("blocked_relative_motions", spec["optional_fields"])
        self.assertNotIn("blocked_relative_motions", spec["required_fields"])


# ======================================================================
# It rides the existing canonical machinery, and adds none of its own
# ======================================================================

class TestItUsesTheCanonicalMachinery(_Substrate):

    def test_it_survives_replay_and_hashes_like_any_other_entity(self):
        s = self.upstream(run="replay-a")
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        again = self.upstream(run="replay-a")
        self.assertEqual([], self.commit(again, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        self.assertEqual(s.state_hash(), again.state_hash())
        self.assertEqual(s.counts(), again.counts())

    def test_its_record_survives_a_read_unchanged(self):
        s = self.upstream()
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        stored = next(r for r in s.family("TransitionRequirement"))
        self.assertEqual([{"joint": "JNT-1", "dof": "RZ"}],
                         stored["required_relative_motions"])
        stored["required_relative_motions"].append({"joint": "JNT-1", "dof": "TX"})
        fresh = next(r for r in s.family("TransitionRequirement"))
        self.assertEqual(1, len(fresh["required_relative_motions"]),
                         "the read surface handed out state's own object")

    def test_its_references_are_in_the_canonical_dependency_graph(self):
        """Through `_reference_graph`, which every branch and currentness answer
        already uses. A custom traversal here would be a second graph."""
        from ver3.assy_v3.view.consumer_view import _reference_graph
        s = self.upstream()
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        fwd, rev = _reference_graph(s, s.c)
        self.assertIn("CFG-1", fwd.get("TRQ-1", set()))
        self.assertIn("CFG-2", fwd.get("TRQ-1", set()))
        self.assertIn("CRL-1", fwd.get("TRQ-1", set()))
        self.assertIn("JNT-1", fwd.get("TRQ-1", set()),
                      "the nested joint reference is not in the graph")
        self.assertIn("TRQ-1", rev.get("CFG-1", set()))

    def test_a_withdrawn_endpoint_reaches_it(self):
        """Currentness rides the same edges: what it depends on is what can
        stale it. Asserted through the graph rather than by running lifecycle."""
        from ver3.assy_v3.view.consumer_view import _reference_graph, _closure
        s = self.upstream()
        self.assertEqual([], self.commit(s, "TransitionRequirement", "TRQ-1",
                                         self.requirement()))
        _fwd, rev = _reference_graph(s, s.c)
        self.assertIn("TRQ-1", _closure({"CFG-2"}, rev))

    def test_write_authority_is_declared_and_projected(self):
        from ver3.assy_v3.state.design_state import Contracts
        c = Contracts()
        self.assertEqual("s03", self.families["TransitionRequirement"]["owned_by"])
        self.assertTrue(c.may_create("s03", "TransitionRequirement"))
        with open(os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                               "STAGE_OWNERSHIP_MATRIX.yaml")) as fh:
            matrix = yaml.safe_load(fh)
        self.assertIn("TransitionRequirement", matrix["stages"]["s03"]["owns"])

    def test_no_other_stage_may_create_one(self):
        from ver3.assy_v3.state.design_state import Contracts
        c = Contracts()
        for stage in ("s01", "s02", "s04", "s05"):
            with self.subTest(stage=stage):
                self.assertFalse(c.may_create(stage, "TransitionRequirement"))


# ======================================================================
# Nothing requires one yet
# ======================================================================

class TestTheSubstrateChangesNothingYet(_Substrate):

    def test_a_state_with_no_transition_requirement_is_valid(self):
        s = self.upstream()
        self.assertEqual([], s.family("TransitionRequirement"))
        self.assertEqual([], self.commit(s, "ConstraintRelation", "CRL-2",
                                         {"retained_group": "RGP-2",
                                          "blocked_dofs": ["RZ"],
                                          "configurations": ["CFG-1"],
                                          "driver": "LOAD",
                                          "provider_body": "BOD-1"}))

    def test_no_responsibility_requires_it_as_a_premise(self):
        """Producing it is not requiring it. Unit 2 gave s03b the question; no
        consumer has been pointed at the answer yet."""
        with open(os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                               "STAGE_RESPONSIBILITY_CONTRACT.yaml")) as fh:
            responsibility = yaml.safe_load(fh)
        roles = set(self.families["TransitionRequirement"]["semantic_roles"])
        for name, stage in responsibility["stages"].items():
            for premise in stage.get("required_reasoning_premise_classes") or []:
                needed = set(premise.get("requires_semantics") or [])
                if not (needed & roles):
                    continue
                # A role this family shares with another may legitimately be
                # required; what must not exist yet is a premise satisfied ONLY
                # by this family.
                satisfying = {f for f, spec in self.families.items()
                              if set(spec.get("semantic_roles") or []) & needed}
                self.assertNotEqual({"TransitionRequirement"}, satisfying,
                                    "%s already requires it as a premise" % name)

    def test_only_s03b_writes_one(self):
        """Unit 1 asserted that NOBODY wrote one, which was true of the unit that
        defined the vocabulary. Unit 2 gave it a producer, so the property worth
        holding is the narrower one: s03 authors it and s04 does not touch it.
        The write boundary enforces the same thing through ownership; this says
        it about the code, so a stage that started emitting one would be visible
        here as well as refused there."""
        import inspect
        import ver3.assy_v3.stages.s03_topology_and_mobility as s03
        import ver3.assy_v3.stages.s04_envelope_and_motion as s04
        self.assertIn('"TransitionRequirement"', inspect.getsource(s03))
        self.assertNotIn('"TransitionRequirement"', inspect.getsource(s04))


# ======================================================================
# The three meanings the contract now states outright
# ======================================================================

class TestTheContractSaysWhatTheseDoNotMean(_Substrate):

    def family_text(self, name):
        """The declaration's own text, comments included: the clarifications are
        prose about meaning, and prose is where a reader looks for it."""
        with open(CONTRACT) as fh:
            text = fh.read()
        start = text.index("\n  %s:\n" % name)
        after = text.find("\n  ", start + len(name) + 5)
        while after != -1 and not text[after + 3:after + 4].isupper():
            after = text.find("\n  ", after + 1)
        return text[start:after if after != -1 else len(text)]

    def test_child_group_is_not_the_absolute_moving_side(self):
        text = self.family_text("Joint")
        self.assertIn("RELATIVE KINEMATIC RELATION", text)
        self.assertIn("WHICH BODY MOVES IN THE WORLD", text)
        self.assertIn("blocked_relative_motions", text,
                      "the contract does not point at what to use instead")

    def test_distinguishing_basis_is_not_required_free_mobility(self):
        text = self.family_text("Configuration")
        self.assertIn("DOES NOT SAY", text)
        self.assertIn("FREE", text)

    def test_blocked_by_is_not_transition_impossibility(self):
        self.assertEqual("CONFIGURATION_LOCAL",
                         self.families["MobilityExpectation"]["disposition_scope"])
        text = self.family_text("MobilityExpectation")
        self.assertIn("CONFIGURATION-LOCAL", text)
        self.assertIn("TransitionRequirement", text)

    def test_the_retired_field_is_gone_from_every_declared_field_list(self):
        spec = self.families["ConstraintRelation"]
        self.assertNotIn("release_transition", spec["optional_fields"])
        self.assertNotIn("release_transition", spec["required_fields"])
        self.assertNotIn("release_transition", spec.get("field_semantics") or {})

    def test_the_retirement_is_not_an_alias(self):
        """The replacement points the other way: a transition names the
        restraints it releases, not a restraint naming a transition."""
        spec = self.families["TransitionRequirement"]
        self.assertIn("released_constraints", spec["optional_fields"])
        self.assertEqual("ConstraintRelation",
                         spec["field_semantics"]["released_constraints"]["target"])


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
