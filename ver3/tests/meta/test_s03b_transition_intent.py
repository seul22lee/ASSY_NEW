"""s03b says which state changes must be possible, and checks what it said.

A mechanism whose configurations are each well held and none reachable from any
other is a solid object. Until now s03b could say what holds a body in a state
and could not say that the state must be leavable, so every consumer wanting
that had to infer it - and the available inferences are all wrong:

  a locked source            BLOCKED_BY is what a latch IS. Reading it as "no
                             transition can leave" makes every mechanism that
                             holds its own configurations look immobile.
  distinguishing_basis       says two states DIFFER, not that either is reachable
                             from the other, and not that the DOF is free in
                             either.
  child_group                orients a relative relation. Which side moves in the
                             world is a fact about the whole mechanism.

`TransitionRequirement` says it instead, and `ConstraintRelation.
blocked_relative_motions` says which relative motion a restraint removes - so
`transition_consistency` can compare a requirement against a restraint through
typed motion pairs and never through group identity.

WHAT THE CHECKS ARE FOR. They report; they do not repair, and nothing here
deletes a requirement that exposes a contradiction. A required motion the joint
does not have, or one an active unreleased restraint removes, is a design saying
two things that cannot both hold. A release whose relation states no defeat
specification is a design that may be right and has not said how. What either
costs a candidate is feasibility's question, in a later unit.

No candidate names, no benchmark fixtures.
"""
import unittest

from . import _fixtures

from ver3.assy_v3.stages.base import carry_invocation_premises
from ver3.assy_v3.stages.s03_topology_and_mobility import (
    RESPONSE_KEY_OF, S03B_PROMPT, S03BMobilityAndAssembly, reference_rules,
    render_reference_rules, transition_consistency)
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.view import InvocationContext


def motion(joint, dof):
    return {"joint": joint, "dof": dof}


def requirement(rid="TRQ-1", frm="CFG-1", to="CFG-2", motions=(("JNT-1", "RY"),),
                released=()):
    return {"id": rid, "from_configuration": frm, "to_configuration": to,
            "required_relative_motions": [motion(*m) for m in motions],
            "released_constraints": list(released)}


def relation(rid="CRL-1", configs=("CFG-1",), blocks=(("JNT-1", "RY"),),
             defeat="a pull that separates the two bodies", **over):
    out = {"id": rid, "retained_group": "RGP-2", "blocked_dofs": ["RY"],
           "configurations": list(configs), "driver": "KINEMATIC_NECESSITY",
           "provider_body": "BOD-1", "defeat_specification": defeat}
    if blocks is not None:
        out["blocked_relative_motions"] = [motion(*m) for m in blocks]
    out.update(over)
    return out


def joint(jid="JNT-1", dof=("RY",), parent="RGP-1", child="RGP-2"):
    return {"entity_id": jid, "joint_type": "REVOLUTE", "parent_group": parent,
            "child_group": child, "dof": list(dof), "axis_direction": "+Y",
            "frame_ids": ["FRM-1"]}


def findings(requirements, relations, joints, code=None):
    out = transition_consistency(requirements, relations, joints)
    return [f for f in out if code is None or f.startswith(code)]


# ======================================================================
# What the checks say, and what they refuse to say
# ======================================================================

class TestTransitionConsistency(unittest.TestCase):

    def test_a_locked_source_released_for_a_supported_motion_is_clean(self):
        """The case the old semantics could not express: leaving a held state by
        defeating what held it is what a latch is FOR."""
        self.assertEqual([], transition_consistency(
            [requirement(released=["CRL-1"])], [relation()], [joint()]))

    def test_the_destination_may_re_establish_a_restraint(self):
        """Arriving somewhere that locks again contradicts nothing."""
        arriving = relation("CRL-2", configs=("CFG-2",))
        self.assertEqual([], transition_consistency(
            [requirement(released=["CRL-1"])], [relation(), arriving], [joint()]))

    def test_an_active_blocker_that_nothing_releases_is_a_contradiction(self):
        found = findings([requirement()], [relation()], [joint()],
                         "UNRELEASED_REQUIRED_MOTION")
        self.assertTrue(found, "an unreleased restraint on a required motion "
                               "passed unreported")
        self.assertIn("CRL-1", found[0])

    def test_a_release_without_defeat_evidence_is_incompleteness_not_a_failure(self):
        out = transition_consistency([requirement(released=["CRL-1"])],
                                     [relation(defeat="")], [joint()])
        self.assertEqual(1, len(out), out)
        self.assertTrue(out[0].startswith("RELEASE_EVIDENCE_NOT_ESTABLISHED"), out)
        self.assertNotIn("UNRELEASED_REQUIRED_MOTION", " ".join(out),
                         "missing evidence was reported as a contradiction")

    def test_a_motion_the_joint_does_not_have_is_reported(self):
        found = findings([requirement(motions=(("JNT-1", "TX"),))],
                         [relation(blocks=None)], [joint(dof=("RY",))],
                         "TRANSITION_DOF_NOT_SUPPORTED")
        self.assertTrue(found, "a transition required a DOF the joint lacks")
        self.assertIn("TX", found[0])

    def test_an_empty_configuration_list_means_nowhere_not_everywhere(self):
        """`configurations` is the complete list of where a relation holds, so
        an empty one holds NOWHERE. Reading it as "everywhere" would turn an
        author's silence into the widest possible claim and let a relation that
        restrains nothing block every transition in the design."""
        released = findings([requirement(released=["CRL-1"])],
                            [relation(configs=())], [joint()])
        self.assertTrue([f for f in released
                         if f.startswith("RELEASE_NOT_ACTIVE_AT_SOURCE")], released)

    def test_an_empty_configuration_list_blocks_nothing(self):
        self.assertEqual([], findings([requirement()], [relation(configs=())],
                                      [joint()], "UNRELEASED_REQUIRED_MOTION"))

    def test_a_relation_active_elsewhere_blocks_nothing_here(self):
        self.assertEqual([], findings([requirement()],
                                      [relation(configs=("CFG-9",))], [joint()],
                                      "UNRELEASED_REQUIRED_MOTION"))

    def test_a_release_naming_no_relative_motion_is_incompleteness(self):
        """The relation was named as one that must be released and has not said
        which motion it removes. Distinct from naming a different motion: absent
        is not disjoint, and reading it as 'restrains nothing relevant' would be
        inventing the answer."""
        out = findings([requirement(released=["CRL-1"])],
                       [relation(blocks=())], [joint()])
        codes = {f.split(":")[0] for f in out}
        self.assertIn("RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED", codes)
        self.assertNotIn("RELEASE_RELATION_NOT_APPLICABLE", codes)
        self.assertNotIn("UNRELEASED_REQUIRED_MOTION", codes)

    def test_an_absent_field_is_the_same_answer_as_an_empty_one(self):
        for blocks in (None, ()):
            with self.subTest(blocks=blocks):
                out = findings([requirement(released=["CRL-1"])],
                               [relation(blocks=blocks)], [joint()],
                               "RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED")
                self.assertTrue(out, out)

    def test_a_release_naming_a_different_motion_is_a_mismatch_not_a_silence(self):
        out = findings([requirement(released=["CRL-1"])],
                       [relation(blocks=(("JNT-9", "TZ"),))],
                       [joint(), joint("JNT-9", dof=("TZ",))])
        codes = {f.split(":")[0] for f in out}
        self.assertIn("RELEASE_RELATION_NOT_APPLICABLE", codes)
        self.assertNotIn("RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED", codes)

    def test_an_intersecting_release_establishes_applicability(self):
        out = findings([requirement(released=["CRL-1"])], [relation()], [joint()])
        codes = {f.split(":")[0] for f in out}
        self.assertNotIn("RELEASE_RELATION_NOT_APPLICABLE", codes)
        self.assertNotIn("RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED", codes)

    def test_activity_is_read_from_configurations_and_nothing_else(self):
        from .test_s3_interface_readiness import _code_only
        from ver3.assy_v3.stages.s03_topology_and_mobility import _active_in
        code = _code_only(_active_in)
        for token in ("retained_group", "child_group", "parent_group",
                      "blocked_dofs", "name"):
            self.assertNotIn(token, code)

    def test_a_release_that_is_not_active_at_the_source_is_reported(self):
        found = findings([requirement(released=["CRL-1"])],
                         [relation(configs=("CFG-2",))], [joint()],
                         "RELEASE_NOT_ACTIVE_AT_SOURCE")
        self.assertTrue(found, found)

    def test_a_release_unrelated_to_the_required_motion_is_reported(self):
        found = findings([requirement(released=["CRL-1"])],
                         [relation(blocks=(("JNT-9", "TZ"),))],
                         [joint(), joint("JNT-9", dof=("TZ",))],
                         "RELEASE_RELATION_NOT_APPLICABLE")
        self.assertTrue(found, found)

    def test_reversing_the_joint_orientation_changes_no_answer(self):
        """Parent and child orient a RELATIVE relation. Swapping them keeps the
        same capability, and every rule above matches on (joint, dof)."""
        for case in ([requirement()], [requirement(released=["CRL-1"])],
                     [requirement(motions=(("JNT-1", "TX"),))]):
            for relations in ([relation()], [relation(configs=("CFG-2",))],
                              [relation(configs=())], [relation(blocks=())]):
                with self.subTest(case=case[0]["id"], relations=relations[0]["id"]):
                    forward = transition_consistency(case, relations, [joint()])
                    reversed_ = transition_consistency(
                        case, relations,
                        [joint(parent="RGP-2", child="RGP-1")])
                    self.assertEqual(forward, reversed_)

    def test_a_relation_naming_no_relative_motion_blocks_nothing_here(self):
        """Optional means optional: a restraint that has not said which motion it
        removes is not silently assumed to remove the one in question."""
        self.assertEqual([], findings([requirement()], [relation(blocks=None)],
                                      [joint()], "UNRELEASED_REQUIRED_MOTION"))

    def test_it_reads_no_group_identity(self):
        from .test_s3_interface_readiness import _code_only
        code = _code_only(transition_consistency)
        for token in ("child_group", "parent_group", "retained_group",
                      "distinguishing_basis"):
            self.assertNotIn(token, code)

    def test_nothing_is_generated_from_distinguishing_basis(self):
        """A basis says two states differ. It creates no requirement and implies
        no free mobility."""
        stage = S03BMobilityAndAssembly()
        view = {"Configuration": [
            {"entity_id": "CFG-1", "distinguishing_basis": [
                {"rigid_group": "RGP-2", "dof": "RY", "differs_from": ["CFG-2"]}]},
            {"entity_id": "CFG-2", "distinguishing_basis": [
                {"rigid_group": "RGP-2", "dof": "RY", "differs_from": ["CFG-1"]}]}],
            "Joint": [joint()]}
        ops = stage.to_operations({"constraint_relations": [], "load_paths": [],
                                   "assembly_steps": [], "unresolved": [],
                                   "physical_interactions": []},
                                  {"candidate": {"entity_id": "CND-X"},
                                   stage.context_key: view})
        self.assertEqual([], [o for o in ops
                              if o.entity_type == "TransitionRequirement"])
        self.assertEqual([], transition_consistency([], [], view["Joint"]))

    def test_a_forward_transition_implies_no_reverse(self):
        forward = requirement("TRQ-1", "CFG-1", "CFG-2")
        self.assertEqual([], transition_consistency(
            [forward], [relation(blocks=None)], [joint()]))
        # nothing produced the reverse, and no rule asked for it
        stage = S03BMobilityAndAssembly()
        ops = stage.to_operations({"transition_requirements": [forward],
                                   "constraint_relations": [], "load_paths": [],
                                   "assembly_steps": [], "unresolved": [],
                                   "physical_interactions": []},
                                  {"candidate": {"entity_id": "CND-X"}})
        written = [o for o in ops if o.entity_type == "TransitionRequirement"]
        self.assertEqual(1, len(written))
        self.assertEqual(("CFG-1", "CFG-2"),
                         (written[0].fields["from_configuration"],
                          written[0].fields["to_configuration"]))


# ======================================================================
# The producer, through the canonical write path
# ======================================================================

class TestTheProducerAuthorsIt(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.stage = S03BMobilityAndAssembly()

    def branch(self, run="trq", candidate="CND-A"):
        s = DesignState(run_id=run)
        self.add(s, "s02", "Candidate", candidate, principle={"h": "f"})
        ops = [
            Op("CREATE", "Body", "BOD-1",
               {"instance_identity": "one", "role": "base",
                "created_by_stage": "s03"}, "s03:topology", premise_refs=[candidate]),
            Op("CREATE", "RigidGroup", "RGP-1",
               {"body": "BOD-1", "members": ["BOD-1"], "is_default": True},
               "s03:topology", premise_refs=[candidate]),
            Op("CREATE", "RigidGroup", "RGP-2",
               {"body": "BOD-1", "members": ["BOD-1"], "is_default": False},
               "s03:topology", premise_refs=[candidate]),
            Op("CREATE", "Joint", "JNT-1",
               {"joint_type": "REVOLUTE", "parent_group": "RGP-1",
                "child_group": "RGP-2", "dof": ["RY"], "axis_direction": "+Y",
                "frame_ids": ["FRM-1"]}, "s03:topology", premise_refs=[candidate]),
            Op("CREATE", "Configuration", "CFG-1",
               {"name": "shut", "kind": "STABLE", "bodies_present": ["BOD-1"],
                "expected_mobility": []}, "s03:topology", premise_refs=[candidate]),
            Op("CREATE", "Configuration", "CFG-2",
               {"name": "open", "kind": "STABLE", "bodies_present": ["BOD-1"],
                "expected_mobility": []}, "s03:topology", premise_refs=[candidate]),
        ]
        patch = StagePatch(patch_id="topology-" + candidate, run_id=s.run_id,
                           stage_id="s03", stage_attempt=1,
                           parent_state_hash=s.state_hash(), operations=ops,
                           execution_status="SUCCESS",
                           provenance={"purpose": "transition intent test"})
        problems = s.validate(patch)
        self.assertEqual([], problems, problems[:4])
        s.apply(patch)
        return s

    def author(self, state, parsed, candidate="CND-A"):
        cand = next(c for c in state.family("Candidate")
                    if c["entity_id"] == candidate)
        view = self.stage.consumer_view(state, InvocationContext(branch=candidate))
        inputs = {"candidate": cand, self.stage.context_key: view.payload()}
        full = {"physical_interactions": [], "constraint_relations": [],
                "load_paths": [], "assembly_steps": [], "unresolved": [],
                "transition_requirements": []}
        full.update(parsed)
        ops = carry_invocation_premises(self.stage.to_operations(full, inputs),
                                        self.stage.invocation_premises(inputs))
        patch = StagePatch(patch_id="s03b-%d" % len(state.applied_patches),
                           run_id=state.run_id, stage_id="s03", stage_attempt=1,
                           parent_state_hash=state.state_hash(), operations=ops,
                           execution_status="SUCCESS",
                           provenance={"purpose": "transition intent test"})
        problems = state.validate(patch)
        if not problems:
            state.apply(patch)
        return problems, self.stage.completeness(full, inputs)

    def test_a_requirement_reaches_canonical_state(self):
        s = self.branch()
        problems, _ = self.author(s, {
            "constraint_relations": [relation()],
            "transition_requirements": [requirement(released=["CRL-1"])]})
        self.assertEqual([], problems, problems[:4])
        stored = s.family("TransitionRequirement")
        self.assertEqual(1, len(stored))
        self.assertEqual("CFG-1", stored[0]["from_configuration"])
        self.assertEqual([{"joint": "JNT-1", "dof": "RY"}],
                         stored[0]["required_relative_motions"])
        self.assertEqual(["CRL-1"], stored[0]["released_constraints"])

    def test_blocked_relative_motions_is_preserved_verbatim(self):
        s = self.branch()
        problems, _ = self.author(s, {"constraint_relations": [relation()]})
        self.assertEqual([], problems, problems[:4])
        stored = next(r for r in s.family("ConstraintRelation"))
        self.assertEqual([{"joint": "JNT-1", "dof": "RY"}],
                         stored["blocked_relative_motions"])

    def test_a_relation_may_still_name_no_relative_motion(self):
        s = self.branch()
        problems, _ = self.author(s, {"constraint_relations": [relation(blocks=None)]})
        self.assertEqual([], problems, problems[:4])
        stored = next(r for r in s.family("ConstraintRelation"))
        self.assertNotIn("blocked_relative_motions", stored)

    def test_a_one_configuration_mechanism_may_emit_none(self):
        s = self.branch()
        problems, incomplete = self.author(s, {"constraint_relations": [relation()]})
        self.assertEqual([], problems, problems[:4])
        self.assertEqual([], s.family("TransitionRequirement"))
        self.assertEqual([], [x for x in incomplete
                              if "TRANSITION" in x or "RELEASE" in x])

    def test_a_contradiction_is_reported_and_still_committed(self):
        """Preserved as evidence: deleting it would answer an eligibility
        question invisibly, and that question is not this pass's."""
        s = self.branch()
        problems, incomplete = self.author(s, {
            "constraint_relations": [relation()],
            "transition_requirements": [requirement()]})
        self.assertEqual([], problems, "a canonical error was raised for an "
                                       "engineering fact")
        self.assertEqual(1, len(s.family("TransitionRequirement")))
        self.assertTrue([x for x in incomplete
                         if x.startswith("UNRELEASED_REQUIRED_MOTION")], incomplete)

    def test_a_foreign_branch_reference_is_refused(self):
        s = self.branch()
        other = self.branch(run="trq", candidate="CND-B")
        for field, value in (("from_configuration", "CFG-9"),
                             ("to_configuration", "CFG-9")):
            with self.subTest(field=field):
                fresh = self.branch(run="trq-%s" % field)
                problems, _ = self.author(fresh, {
                    "transition_requirements": [requirement(**{
                        "frm" if field == "from_configuration" else "to": value})]})
                self.assertTrue(problems, "a dangling configuration was accepted")

    def test_it_is_branch_local_through_the_canonical_resolver(self):
        from ver3.assy_v3.view.consumer_view import branch_membership
        s = self.branch()
        problems, _ = self.author(s, {
            "constraint_relations": [relation()],
            "transition_requirements": [requirement(released=["CRL-1"])]})
        self.assertEqual([], problems, problems[:4])
        membership = branch_membership(s, s.c, ["TRQ-1"])
        self.assertEqual({"CND-A"}, membership["TRQ-1"],
                         "the requirement is not scoped to the branch that "
                         "authored it")


# ======================================================================
# The prompt says what the contract declares
# ======================================================================

class TestThePromptCarriesTheSemantics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.prompt = S03BMobilityAndAssembly().prompt(
            {"consumer_view": {}, "candidate": {"entity_id": "CND-X"}})

    def test_the_response_key_is_registered(self):
        self.assertEqual("transition_requirements",
                         RESPONSE_KEY_OF["TransitionRequirement"])

    def test_the_schema_and_the_rules_are_in_the_prompt(self):
        for token in ("transition_requirements[]", "THE STATE MACHINE",
                      "A -> B is not B -> A", "NOT A COMPLETE GRAPH",
                      "ADJACENCY IS NOT IN distinguishing_basis",
                      "A LOCKED SOURCE IS NORMAL", "THE DESTINATION MAY RE-LOCK",
                      "blocked_relative_motions"):
            with self.subTest(token=token):
                self.assertIn(token, self.prompt)

    def test_every_nested_reference_is_specified(self):
        for name in ("transition_requirements[].required_relative_motions[].joint",
                     "transition_requirements[].required_relative_motions[].dof",
                     "constraint_relations[].blocked_relative_motions[].joint",
                     "constraint_relations[].blocked_relative_motions[].dof"):
            with self.subTest(field=name):
                self.assertIn(name, self.prompt)

    def test_the_dof_vocabulary_is_stated_not_implied(self):
        block = render_reference_rules()
        row = [r for r in reference_rules()
               if r["field"] == "required_relative_motions[].dof"]
        self.assertTrue(row)
        self.assertEqual("vocabulary", row[0]["kind"])
        for dof in ("TX", "TY", "TZ", "RX", "RY", "RZ"):
            self.assertIn(dof, block)

    def test_the_prompt_forbids_deriving_the_linkage(self):
        for token in ("retained_group", "parent", "child"):
            self.assertIn(token, self.prompt)
        self.assertIn("Do not produce one by matching", self.prompt)

    def test_the_prompt_says_the_new_field_is_additive(self):
        """One saved response filled `blocked_relative_motions` and left
        `blocked_dofs` empty, so the relation restrained nothing anywhere. The
        prompt now says which question each answers and that neither is computed
        from the other."""
        self.assertIn("IT ADDS TO `blocked_dofs`; IT DOES NOT REPLACE IT",
                      self.prompt)
        self.assertIn("Fill in `blocked_dofs` for every relation that restrains",
                      self.prompt)
        self.assertIn("means it holds NOWHERE", self.prompt)

    def test_it_asks_for_no_realization(self):
        """Capability only: no force, energy, trigger, angle or trajectory."""
        # THE SECTION, not everything after the first mention of its name: the
        # schema line above points at it by name, and slicing from there would
        # sweep in the effect vocabulary - where "TRANSMIT_FORCE" is a legitimate
        # word about something else entirely.
        start = self.prompt.rindex("THE STATE MACHINE")
        section = self.prompt[start:self.prompt.index(
            "WHEN A RESTRAINT NAMES THE MOTION IT REMOVES", start)]
        for token in ("force", "energy", "trigger", "angle", "trajectory",
                      "torque", "newton", "millimetre"):
            with self.subTest(token=token):
                self.assertNotIn(token, section.lower())


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
