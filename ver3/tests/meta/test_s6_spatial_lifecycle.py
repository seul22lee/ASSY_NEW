"""Every current spatial value answers two questions.

    What exact facts was I made from?
    Which of those changing means I must lose authority?

`_propagate` is ONE HOP. It stales the direct dependents of the entity that
changed and stops, so a derived value that names only the nearest link inherits
nothing from behind it: naming the Transition does not carry the endpoint states,
and naming the driving Joint does not carry the box that was swept.

Before this pass every s04b output carried the same list - every envelope in the
view - which was wrong in both directions at once. Too much: an unrelated body
being resized staled joint angles it cannot affect. Too little: none of them named
the Configuration, the endpoint States, the Transition or the moving RigidGroup,
so changing an endpoint coordinate left the swept occupancy STANDING with a hull
computed from the coordinate that had just been replaced.

The probe is a generic two-body hinge - a base, a moving member, one revolute
joint, two configurations, a transition between them - and the same rules are run
against a prismatic one. No product noun and no state name appears.
"""
from __future__ import annotations

import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion)
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s02_s03b_integration import _Canned                          # noqa: E402
from .test_s6_spatial import _S04Chain, s04a_response, s04b_response    # noqa: E402


class _Probe(_S04Chain):
    """A hinge, and the same code exercised as a slider."""

    def val(self, state, eid):
        return state.entities[eid].get("_validity")

    def prem(self, state, eid):
        return set(state.entities[eid].get("_premises") or [])

    def mutate(self, op):
        """A fresh probe, one controlled change, and what it reached."""
        state, _ = self.spatial()
        self.revise(state, op)
        return state


#: The candidate every s04 record was authored to embody. Present on all of them
#: for the reason S-5 established: withdraw the alternative and the work done to
#: embody it loses standing. It is lineage, and it is additional to - never a
#: substitute for - the computational premises below.
BRANCH = "CND-A"

IDS = {"state_a": "STA-CFG-C0A", "state_b": "STA-CFG-C1A",
       "transition": "TRN-A", "requirement": "TRQ-A",
       "sweep": "SWV-TRN-A-RGP-G0A",
       "joint": "JNT-A", "group": "RGP-G0A", "envelope": "ENV-0A",
       "other_envelope": "ENV-1A", "config": "CFG-C0A", "scale": "SCL-CND-A"}


class TestDependencyGraph(_Probe):

    def test_L7_the_premise_set_is_exactly_what_reproduces_the_value(self):
        """Neither more nor less. Stated as an equality, because a subset
        assertion cannot catch over-declaration and a superset cannot catch
        under-declaration."""
        state, _ = self.spatial()
        self.assertEqual(
            {IDS["config"], IDS["joint"], IDS["scale"], BRANCH},
            self.prem(state, IDS["state_a"]),
            "State: the configuration it realizes, the joints its coordinates "
            "are of, and the basis they are in")
        self.assertEqual(
            {IDS["requirement"], IDS["state_a"], IDS["state_b"], IDS["group"],
             IDS["joint"], IDS["scale"], BRANCH},
            self.prem(state, IDS["transition"]),
            "Transition: the requirement that decides its endpoints and the "
            "motion it has to carry out, both endpoints, what moves, which "
            "coordinate changes")
        self.assertEqual(
            {IDS["transition"], IDS["group"], IDS["state_a"], IDS["state_b"],
             IDS["joint"], IDS["envelope"], IDS["scale"], BRANCH},
            self.prem(state, IDS["sweep"]),
            "SweptVolume: exactly what sweep_hull read")

    def test_L9_a_visible_fact_that_was_not_used_is_not_a_premise(self):
        """The other body's envelope is in the view and in no computation here."""
        state, res = self.spatial()
        view = S04BPlacementAndMotion().consumer_view(state, res["A"][2]).payload()
        visible = {e["entity_id"] for e in view.get("Envelope") or []}
        self.assertIn(IDS["other_envelope"], visible, "the probe is not probing")
        for eid in (IDS["state_a"], IDS["transition"], IDS["sweep"]):
            self.assertNotIn(IDS["other_envelope"], self.prem(state, eid), eid)
        # The placement extension names the BASIS - withdraw it and the origin
        # is three numbers meaning nothing - and no extent. Recording extents
        # there would say the topology lost authority because a body got bigger.
        self.assertNotIn(IDS["other_envelope"], self.prem(state, IDS["joint"]))
        self.assertNotIn(IDS["envelope"], self.prem(state, IDS["joint"]))
        self.assertIn(IDS["scale"], self.prem(state, IDS["joint"]))

    def test_L8_dropping_one_real_premise_is_caught(self):
        """Each computational fact, removed one at a time: the value it should
        have staled stays STANDING. This is what makes L7's equality mean
        something rather than describe an accident."""
        for premise, mutation in (
                (IDS["state_b"], Op("SUPERSEDE", "State", IDS["state_b"],
                                    {"joint_coordinates": {IDS["joint"]: 12}},
                                    "t", reason="endpoint moved")),
                (IDS["joint"], Op("SUPERSEDE", "Joint", IDS["joint"],
                                  {"axis_direction": "+X"}, "t",
                                  reason="axis changed")),
                (IDS["envelope"], Op("SUPERSEDE", "Envelope", IDS["envelope"],
                                     {"extent": {"half_extent": [3, 3, 3],
                                                 "centre": [0, 0, 0]}},
                                     "t", reason="extent changed")),
                (IDS["group"], Op("SUPERSEDE", "RigidGroup", IDS["group"],
                                  {"members": []}, "t", reason="group changed")),
                (IDS["transition"], Op("SUPERSEDE", "Transition", IDS["transition"],
                                       {"path": {"moving_groups": []}}, "t",
                                       reason="what moves changed"))):
            state = self.mutate(mutation)
            self.assertIn(premise, self.prem(state, IDS["sweep"]), premise)
            self.assertEqual("STALE", self.val(state, IDS["sweep"]),
                             "changing %s left the occupancy current" % premise)


class TestLifecycleFalsifiers(_Probe):

    def test_L1_configuration_change_stales_its_state(self):
        state = self.mutate(Op("INVALIDATE", "Configuration", IDS["config"], {},
                               "t", reason="the configuration was withdrawn"))
        self.assertEqual("STALE", self.val(state, IDS["state_a"]))
        self.assertEqual("STANDING", self.val(state, IDS["state_b"]),
                         "the sibling configuration's state was disturbed")

    def test_L2_endpoint_coordinate_change_stales_transition_and_sweep(self):
        state = self.mutate(Op("SUPERSEDE", "State", IDS["state_b"],
                               {"joint_coordinates": {IDS["joint"]: 12}}, "t",
                               reason="the endpoint moved"))
        self.assertEqual("STALE", self.val(state, IDS["transition"]))
        self.assertEqual("STALE", self.val(state, IDS["sweep"]),
                         "an occupancy swept between coordinates that changed")

    def test_L3_driving_joint_change_stales_the_sweep(self):
        for fields, why in (({"axis_direction": "+X"}, "axis"),
                            ({"frame_origin": [9, 9, 9]}, "frame origin"),
                            ({"joint_type": "PRISMATIC"}, "joint class")):
            state = self.mutate(Op("SUPERSEDE", "Joint", IDS["joint"], fields,
                                   "t", reason="the %s changed" % why))
            self.assertEqual("STALE", self.val(state, IDS["sweep"]), why)

    def test_L4_moving_group_envelope_change_stales_the_sweep(self):
        state = self.mutate(Op("SUPERSEDE", "Envelope", IDS["envelope"],
                               {"extent": {"half_extent": [3, 3, 3],
                                           "centre": [0, 0, 0]}}, "t",
                               reason="the extent changed"))
        self.assertEqual("STALE", self.val(state, IDS["sweep"]))

    def test_L5_an_unrelated_spatial_value_leaves_everything_current(self):
        state = self.mutate(Op("SUPERSEDE", "Envelope", IDS["other_envelope"],
                               {"extent": {"half_extent": [7, 7, 7],
                                           "centre": [30, 0, 0]}}, "t",
                               reason="a body this sweep never touched"))
        for eid in (IDS["state_a"], IDS["state_b"], IDS["transition"],
                    IDS["sweep"]):
            self.assertEqual("STANDING", self.val(state, eid), eid)

    def test_L5b_the_scale_reaches_everything_because_everything_is_in_it(self):
        """The one premise that IS universal, and it is universal for a reason
        the contract states: a coordinate has no meaning without its basis."""
        # A COMPLETE absolute basis. Revising `basis` alone leaves a record
        # promising comparability with no factor to convert by, which the
        # prospective-record check now refuses - correctly, and for a reason
        # this test is not about.
        state = self.mutate(Op("SUPERSEDE", "ReferenceScale", IDS["scale"],
                               {"basis": "ABSOLUTE",
                                "absolute": {"unit": "mm", "per_unit": 1.0}},
                               "t", reason="the basis changed"))
        for eid in (IDS["state_a"], IDS["transition"], IDS["sweep"]):
            self.assertEqual("STALE", self.val(state, eid), eid)

    def test_L6_a_change_on_one_branch_leaves_the_other_alone(self):
        state, _ = self.spatial((("A", 2, 2), ("B", 1, 3)))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-0B",
                              {"extent": {"half_extent": [5, 5, 5],
                                          "centre": [0, 0, 0]}}, "t",
                              reason="another alternative"))
        self.assertEqual("STALE", self.val(state, "SWV-TRN-B-RGP-G0B"))
        for eid in (IDS["state_a"], IDS["transition"], IDS["sweep"]):
            self.assertEqual("STANDING", self.val(state, eid), eid)

    def test_L10_a_same_invocation_revision_still_obeys_the_barrier(self):
        state, res = self.spatial()
        inv = res["A"][2]
        payload = s04b_response("JNT-A", ["CFG-C0A", "CFG-C1A"], "RGP-G0A")
        payload["envelope_revisions"] = [
            {"envelope": "ENV-0A", "half_extent": [4, 4, 4], "centre": [0, 0, 0],
             "geometric_reason": "it does not clear at the committed size"}]
        out = S04BPlacementAndMotion().invoke(
            _Canned(payload), state, state.run_id, {"candidate": "CND-A"},
            attempt=2, invocation=inv)
        self.assertTrue(out.refinement_only)
        self.assertEqual(["Envelope"],
                         sorted({o.entity_type for o in out.patch.operations}))
        state.apply(out.patch)
        # The pre-revision occupancy staled the moment its extent was replaced.
        self.assertEqual("STALE", self.val(state, IDS["sweep"]))

    def test_L11_a_prismatic_joint_takes_the_same_dependency_path(self):
        """Nothing in the graph branches on joint class. Same premises, same
        consequences, different geometry."""
        state, _ = self.spatial()
        self.revise(state, Op("SUPERSEDE", "Joint", IDS["joint"],
                              {"joint_type": "PRISMATIC", "axis_direction": "+X"},
                              "t", reason="the same rules, a sliding member"))
        self.assertEqual("STALE", self.val(state, IDS["sweep"]))
        self.assertEqual(
            {IDS["transition"], IDS["group"], IDS["state_a"], IDS["state_b"],
             IDS["joint"], IDS["envelope"], IDS["scale"], BRANCH},
            self.prem(state, IDS["sweep"]))
        # And the geometry follows the class: a slider grows the box along its
        # own coordinate, a hinge re-bounds it about the axis.
        joint = dict(state.entities[IDS["joint"]])
        box = s04.aabb([0, 0, 0], [1, 1, 1])
        slid = s04.sweep_hull(box, joint, [0, 0, 0], 0.0, 90.0)
        hinged = s04.sweep_hull(box, dict(joint, joint_type="REVOLUTE",
                                          axis_direction="+Z"),
                                [0, 0, 0], 0.0, 90.0)
        self.assertNotEqual(slid["hull"], hinged["hull"])


class TestCommitmentRepresentation(_Probe):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def declaration(self):
        return _paths.contract("DESIGN_STATE_CONTRACT.yaml")["spatial_commitments"]

    def test_every_s04a_spatial_commitment_is_machine_identifiable(self):
        decl = self.declaration()
        entity = {d["family"] for d in decl["entity_level"]}
        field = {(d["family"], d["field"]) for d in decl["field_level"]}
        self.assertEqual({"Envelope", "ReferenceScale"}, entity)
        # `Interface.mating_geometry` joined the declaration at the parameter
        # authority closure: it had been the one s04a value committed under no
        # class at all, and read as if solved.
        self.assertEqual({("FunctionalRegion", "volume"),
                          ("AssemblyStep", "insertion_direction"),
                          ("Interface", "mating_geometry")}, field)

    def test_entity_level_commitments_carry_their_class_and_field_ones_do_not(self):
        """The granularity rule, checked rather than described. A class on the
        entity is enforceable; a class on a field is not, because runtime has no
        per-field authority - so it is declared, not faked."""
        state, _ = self.spatial()
        for d in self.declaration()["entity_level"]:
            vocab = self.c.families[d["family"]][d["class_field"]]
            for e in state.family(d["family"]):
                self.assertIn(e.get(d["class_field"]), vocab, e["entity_id"])
        # NOT via required_fields: a class of "x" would satisfy that and mean
        # nothing. `spatial_commitment_check` reads the declaration and validates
        # vocabulary membership, which is the stronger and single enforcement.
        self.assertEqual([], s04.spatial_commitment_check(state))
        for d in self.declaration()["field_level"]:
            fam = self.c.families[d["family"]]
            self.assertNotIn("commitment_class", fam.get("required_fields", []),
                             "a field-level commitment grew a fake entity class")
            self.assertEqual("s04", (fam.get("extendable_fields") or {}).get(d["field"]),
                             "%s.%s is not enforceably s04's to author"
                             % (d["family"], d["field"]))

    def test_the_check_reads_the_declaration_and_catches_an_unclassified_one(self):
        state, _ = self.spatial()
        self.assertEqual([], s04.spatial_commitment_check(state))
        self.revise(state, Op("SUPERSEDE", "Envelope", IDS["envelope"],
                              {"commitment_class": "SOMETHING"}, "t",
                              reason="a class that is not one"))
        found = s04.spatial_commitment_check(state)
        self.assertTrue(any("SPATIAL_COMMITMENT_UNCLASSIFIED" in p for p in found),
                        found)

    def test_the_declaration_matches_what_s04a_actually_writes(self):
        state, _ = self.spatial()
        self.assertTrue(state.entities["ENV-0A"].get("commitment_class"))
        self.assertTrue(state.entities["SCL-CND-A"].get("commitment_class"))
        self.assertIn("insertion_direction", state.entities["ASY-A"])

    def test_every_state_declares_the_configuration_it_realizes(self):
        state, _ = self.spatial()
        spec = self.c.reference_spec("State", "configuration")
        self.assertIsNotNone(spec, "State.configuration is still a bare string")
        self.assertEqual("Configuration", spec["target"])
        self.assertIn("configuration", self.c.required_fields("State"))
        for st in state.family("State"):
            self.assertEqual("Configuration",
                             state.stored_family(st["configuration"]))


if __name__ == "__main__":
    unittest.main()
