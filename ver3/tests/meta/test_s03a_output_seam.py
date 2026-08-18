"""S03a's output must be the shape the canonical contract declares.

Six live DeepSeek responses for BM-001 all parsed and all failed canonical
validation. They are kept in `ver3/tests/fixtures/s03a_live/` and used here as
NEGATIVE fixtures: real model output, produced under a prompt that asked for
shapes the contract does not accept.

The seam had four independent divergences, and each was a place where the
prompt, the producer and the contract disagreed about one field:

  compliance     the prompt asked for a nested `compliance {...}` object and the
                 producer passed it through; the contract declares the eight
                 fields FLAT. Every COMPLIANT joint was rejected for eight
                 missing fields that were present all along, one level down. The
                 prompt also said `allowable_travel_status` where the contract
                 says `allowable_travel`.
  reach_targets  the prompt asked "what those actors must reach through it",
                 which invites prose; the contract types the field as references
                 to OTHER FunctionalRegions. All six responses wrote prose.
  frame_ids      the prompt never mentioned it, the producer defaulted it to [],
                 and `axis_direction` is declared spatial IN that frame. Every
                 joint declared a direction expressed in no frame.
  kept_open_by   the prompt demanded Ambiguity or Freedom ids while s03a's view
                 carried neither family, so the only ways to comply were to
                 invent an id or leave the field empty.

Two further mismatches were found by auditing every field rather than by the
run: `Body.addresses_obligations` and `Interface.addresses_obligations` were
written by the producer and declared by no family, so they entered state untyped
- prose or a dangling id would both have been accepted.

Nothing here weakens a canonical guard to admit the old output. The captured
responses are still rejected; what changed is that the prompt and producer now
ask for the shape the contract has always declared.
"""

import json
import os
import unittest

from . import _fixtures, _paths

from ver3.assy_v3.stages.s03_topology_and_mobility import (COMPLIANT_FIELDS,
                                                           PROMPT,
                                                           S03TopologyAndMobility)
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

FIXTURE = os.path.join(_paths.REPO_ROOT, "ver3", "tests", "fixtures",
                       "s03a_live", "bm001_s03a_responses.json")


def live_responses():
    with open(FIXTURE) as fh:
        return json.load(fh)


class _Seam(_fixtures.StateBuilder, unittest.TestCase):
    """A contract-valid upstream state for s03a to author against."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def upstream(self, run="seam"):
        state = DesignState(run_id=run)
        self.add(state, "s02", "Candidate", "CND-A", principle="a hinged cover")
        self.add(state, "s02", "Obligation", "OBL-0001", scope="UNIVERSAL",
                 satisfiable_at="s03", mandatory=True,
                 statement="the lid is retained", evidence_route="MOBILITY_ANALYSIS",
                 route_available=True, derived_from_requirements=[])
        self.add(state, "s01", "Ambiguity", "AMB-0001", statement="compact",
                 conflicting_clauses=[], resolvable_when="a size is given",
                 block_scopes=[])
        self.add(state, "s01", "Freedom", "FRE-0001",
                 decision="the latch mechanism", why_free="unspecified")
        return state

    def commit(self, state, ops, stage="s03"):
        patch = StagePatch(
            patch_id="s03a-%d" % len(state.applied_patches), run_id=state.run_id,
            stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS", provenance={"purpose": "seam test"})
        problems = state.validate(patch)
        if not problems:
            state.apply(patch)
        return problems

    def author(self, state, response):
        """The real producer path: parsed response -> canonical operations."""
        return S03TopologyAndMobility().to_operations(
            response, {"candidate": {"entity_id": "CND-A"}})


# ======================================================================
# The captured live responses, as negative fixtures
# ======================================================================

class TestTheCapturedLiveResponsesAreStillRejected(_Seam):
    """Not one of the six becomes acceptable because the seam was repaired."""

    def test_the_fixture_holds_all_six_responses(self):
        r = live_responses()
        self.assertEqual(6, len(r))
        self.assertTrue(all(v.get("joints") for v in r.values()),
                        "a response with no joints would exercise nothing")

    def test_every_captured_response_still_fails_canonical_validation(self):
        for cid, response in sorted(live_responses().items()):
            with self.subTest(candidate=cid):
                state = self.upstream(run=cid)
                problems = self.commit(state, self.author(state, response))
                self.assertTrue(problems,
                                "%s was accepted after the repair; the guards "
                                "were weakened to admit the old output" % cid)

    def test_the_nested_compliance_shape_is_not_silently_accepted(self):
        """Three of the six nested the variant. The producer no longer forwards
        that key, so the eight fields are simply absent and the conditional rule
        says so - it is not quietly unpacked into validity."""
        nested = {c: r for c, r in live_responses().items()
                  if any("compliance" in j for j in r.get("joints") or [])}
        self.assertTrue(nested, "no captured response nests the variant")
        for cid, response in sorted(nested.items()):
            with self.subTest(candidate=cid):
                state = self.upstream(run=cid)
                problems = self.commit(state, self.author(state, response))
                self.assertTrue(any("compliant_joint_variant" in p
                                    for p in problems), problems)
                joint_ops = [o for o in self.author(state, response)
                             if o.entity_type == "Joint"]
                self.assertFalse(any("compliance" in (o.fields or {})
                                     for o in joint_ops),
                                 "the producer still forwards the nested object")

    def test_prose_in_a_typed_reference_field_is_rejected(self):
        """All six wrote prose into reach_targets."""
        for cid, response in sorted(live_responses().items()):
            with self.subTest(candidate=cid):
                state = self.upstream(run=cid)
                problems = self.commit(state, self.author(state, response))
                self.assertTrue(any("REFERENCE_NOT_AN_ID" in p for p in problems),
                                problems)

    def test_the_missing_frame_is_now_reported(self):
        """Every captured joint declares an axis and names no frame. Before the
        rule, the producer defaulted it to [] and nothing objected."""
        for cid, response in sorted(live_responses().items()):
            with self.subTest(candidate=cid):
                state = self.upstream(run=cid)
                problems = self.commit(state, self.author(state, response))
                self.assertTrue(any("axis_needs_a_named_frame" in p
                                    for p in problems), problems)


# ======================================================================
# The intended shapes
# ======================================================================

def joint(jid, jtype="REVOLUTE", frame=("FRM-JNT-1",), **over):
    out = {"id": jid, "joint_type": jtype, "parent_group": "RGP-1",
           "child_group": "RGP-2", "dof": ["RZ"], "axis_direction": "+Z",
           "frame_ids": list(frame)}
    out.update(over)
    return out


COMPLIANT_OK = {
    "mode": "BENDING", "direction": "+Y", "required_travel": "1 unit of travel",
    # A STATUS, not a number and not a verdict. The contract says allowable
    # travel is a material fact whose status is UNSUPPORTED until a compliance
    # route exists, and s03 has no material.
    "allowable_travel": "UNSUPPORTED",
    "actuation": "PRESCRIBED_KINEMATIC", "compliant_element": "the snap arm",
    "root_interface": "IFC-1", "activation_window": "0..open",
}

BASE_BODIES = [{"id": "BOD-1", "role": "shell", "instance_identity": "box",
                "addresses_obligations": ["OBL-0001"]},
               {"id": "BOD-2", "role": "cover", "instance_identity": "lid",
                "addresses_obligations": []}]
BASE_GROUPS = [{"id": "RGP-1", "body": "BOD-1", "members": [], "is_default": True},
               {"id": "RGP-2", "body": "BOD-1", "members": [], "is_default": False}]


def response(joints, **over):
    """A fresh, contract-valid s03a response every call.

    DEEP-COPIED, because several tests below mutate one field to prove a guard
    fires. Returning the shared module-level lists let one such mutation poison
    every test that ran after it - the failures appeared in tests that never
    touched the field, which is exactly how a shared mutable fixture hides.
    """
    import copy
    out = {
        "bodies": copy.deepcopy(BASE_BODIES),
        "rigid_groups": copy.deepcopy(BASE_GROUPS), "joints": joints,
        "interfaces": [{"id": "IFC-1", "bodies": ["BOD-1", "BOD-2"],
                        "interaction_kind": "CONTACT", "nominal": "NOMINAL",
                        "addresses_obligations": ["OBL-0001"]}],
        "configurations": [{"id": "CFG-1", "name": "closed", "kind": "OPERATIONAL",
                            "bodies_present": ["BOD-1", "BOD-2"],
                            "expected_mobility": [],
                            "distinguishing_basis": [
                                {"rigid_group": "RGP-1", "dof": "RZ",
                                 "differs_from": ["CFG-2"]}]},
                           {"id": "CFG-2", "name": "open", "kind": "OPERATIONAL",
                            "bodies_present": ["BOD-1", "BOD-2"],
                            "expected_mobility": []}],
        "functional_regions": [
            {"id": "FRG-1", "role": "APERTURE", "owning_bodies": ["BOD-1"],
             "required_by_actors": [], "reach_targets": ["FRG-2"]},
            {"id": "FRG-2", "role": "ACCESS", "owning_bodies": ["BOD-1"],
             "required_by_actors": [], "reach_targets": []}],
        "unresolved": [{"id": "S3U-1", "decision": "the latch geometry",
                        "why_open": "no size is given", "alternatives": [],
                        "alternatives_kind": "FREE_TEXT",
                        "kept_open_by": ["AMB-0001", "FRE-0001"], "blocks": []}],
    }
    out.update(over)
    return out


class TestTheIntendedShapesCommit(_Seam):
    """Both a compliant and a non-compliant candidate, through the real path."""

    def test_a_non_compliant_candidate_commits(self):
        state = self.upstream("plain")
        problems = self.commit(state, self.author(state, response([joint("JNT-1")])))
        self.assertEqual([], problems, problems)
        self.assertEqual(2, len(state.standing("Body")))
        self.assertEqual(1, len(state.standing("Joint")))
        self.assertEqual(2, len(state.standing("Configuration")))
        self.assertEqual(2, len(state.standing("FunctionalRegion")))
        self.assertEqual(1, len(state.standing("UnresolvedDecision")))

    def test_a_compliant_candidate_commits_with_the_flat_variant(self):
        state = self.upstream("compliant")
        ops = self.author(state, response(
            [joint("JNT-1"),
             joint("JNT-2", "COMPLIANT", **COMPLIANT_OK)]))
        self.assertEqual([], self.commit(state, ops))
        rec = [j for j in state.standing("Joint")
               if j["entity_id"] == "JNT-2"][0]
        for name in COMPLIANT_FIELDS:
            with self.subTest(field=name):
                self.assertIn(name, rec, "the flat variant did not reach state")
        self.assertEqual("UNSUPPORTED", rec["allowable_travel"])

    def test_a_prismatic_candidate_commits(self):
        state = self.upstream("prismatic")
        self.assertEqual([], self.commit(state, self.author(
            state, response([joint("JNT-1", "PRISMATIC")]))))

    def test_the_committed_records_carry_their_obligation_references(self):
        state = self.upstream("obl")
        self.commit(state, self.author(state, response([joint("JNT-1")])))
        body = [b for b in state.standing("Body") if b["entity_id"] == "BOD-1"][0]
        iface = state.standing("Interface")[0]
        self.assertEqual(["OBL-0001"], body["addresses_obligations"])
        self.assertEqual(["OBL-0001"], iface["addresses_obligations"])


class TestEachGuardStillFailsWhenItShould(_Seam):
    """A repaired seam that accepts anything would be worse than the old one."""

    def reject(self, state, resp):
        problems = self.commit(state, self.author(state, resp))
        self.assertTrue(problems, "this should not have been accepted")
        return problems

    def test_a_compliant_joint_missing_one_variant_field_is_rejected(self):
        for omitted in COMPLIANT_FIELDS:
            with self.subTest(omitted=omitted):
                variant = {k: v for k, v in COMPLIANT_OK.items() if k != omitted}
                problems = self.reject(self.upstream("miss-" + omitted), response(
                    [joint("JNT-2", "COMPLIANT", **variant)]))
                self.assertTrue(any("compliant_joint_variant" in p
                                    for p in problems), problems)

    def test_an_empty_frame_list_is_rejected(self):
        problems = self.reject(self.upstream("noframe"),
                               response([joint("JNT-1", frame=())]))
        self.assertTrue(any("axis_needs_a_named_frame" in p for p in problems),
                        problems)

    def test_prose_in_reach_targets_is_rejected(self):
        resp = response([joint("JNT-1")])
        resp["functional_regions"][0]["reach_targets"] = ["latch"]
        problems = self.reject(self.upstream("prose"), resp)
        self.assertTrue(any("REFERENCE_NOT_AN_ID" in p for p in problems), problems)

    def test_a_reach_target_naming_a_body_is_rejected(self):
        """Typed to FunctionalRegion. A real id of the wrong family is the
        subtler failure and must not pass."""
        resp = response([joint("JNT-1")])
        resp["functional_regions"][0]["reach_targets"] = ["BOD-1"]
        problems = self.reject(self.upstream("wrongfam"), resp)
        self.assertTrue(any("REFERENCE_FAMILY" in p for p in problems), problems)

    def test_kept_open_by_naming_the_wrong_family_is_rejected(self):
        resp = response([joint("JNT-1")])
        resp["unresolved"][0]["kept_open_by"] = ["OBL-0001"]
        problems = self.reject(self.upstream("keptfam"), resp)
        self.assertTrue(any("REFERENCE_FAMILY" in p for p in problems), problems)

    def test_kept_open_by_accepts_both_permitted_families(self):
        for cited in (["AMB-0001"], ["FRE-0001"], ["AMB-0001", "FRE-0001"]):
            with self.subTest(cited=cited):
                state = self.upstream("kept-%d" % len(cited))
                resp = response([joint("JNT-1")])
                resp["unresolved"][0]["kept_open_by"] = cited
                self.assertEqual([], self.commit(state, self.author(state, resp)))

    def test_kept_open_by_prose_is_rejected(self):
        resp = response([joint("JNT-1")])
        resp["unresolved"][0]["kept_open_by"] = ["the size is unknown"]
        problems = self.reject(self.upstream("keptprose"), resp)
        self.assertTrue(any("REFERENCE_NOT_AN_ID" in p for p in problems), problems)

    def test_a_distinguishing_basis_naming_the_wrong_family_is_rejected(self):
        """The nested references were unreachable by any boundary before."""
        resp = response([joint("JNT-1")])
        resp["configurations"][0]["distinguishing_basis"][0]["rigid_group"] = "BOD-1"
        problems = self.reject(self.upstream("basisfam"), resp)
        self.assertTrue(any("REFERENCE_FAMILY" in p for p in problems), problems)

    def test_a_distinguishing_basis_naming_a_missing_configuration_is_rejected(self):
        resp = response([joint("JNT-1")])
        resp["configurations"][0]["distinguishing_basis"][0]["differs_from"] = ["CFG-9"]
        problems = self.reject(self.upstream("basisdangle"), resp)
        self.assertTrue(any("DANGLING_REF" in p for p in problems), problems)

    def test_an_obligation_reference_naming_prose_is_rejected(self):
        resp = response([joint("JNT-1")])
        resp["bodies"][0]["addresses_obligations"] = ["because it must latch"]
        problems = self.reject(self.upstream("oblprose"), resp)
        self.assertTrue(any("REFERENCE_NOT_AN_ID" in p for p in problems), problems)


class TestTheSeamAgreesWithItself(unittest.TestCase):
    """Prompt, producer and contract describing ONE representation."""

    def test_the_producer_reads_the_variant_from_the_contract(self):
        declared = None
        for rule in Contracts().conditional_requirements("Joint"):
            if rule.get("name") == "compliant_joint_variant":
                declared = tuple(rule["additional_required_fields"])
        self.assertEqual(declared, COMPLIANT_FIELDS,
                         "the producer's variant list has drifted from the "
                         "contract it is supposed to be reading")

    def test_the_prompt_asks_for_the_flat_variant(self):
        for name in COMPLIANT_FIELDS:
            with self.subTest(field=name):
                self.assertIn(name, PROMPT)
        self.assertNotIn("compliance {{", PROMPT,
                         "the prompt still asks for a nested variant object")
        self.assertNotIn("allowable_travel_status", PROMPT)

    def test_the_prompt_asks_for_a_named_frame(self):
        self.assertIn("frame_ids", PROMPT)

    def test_the_prompt_states_the_reach_semantics_it_types(self):
        self.assertIn("OTHER functional region ids", PROMPT)

    def test_the_prompt_does_not_invite_a_strain_verdict(self):
        """`allowable_travel` is UNSUPPORTED at s03: there is no material yet.

        The prompt DOES name WITHIN_ELASTIC_LIMIT - to forbid it. Asserting the
        string is absent would fail on the sentence doing the forbidding, so what
        is checked is that it appears only as a prohibition.
        """
        self.assertIn("UNSUPPORTED", PROMPT)
        self.assertIn("do not write a verdict such as", PROMPT)
        for line in PROMPT.splitlines():
            if "WITHIN_ELASTIC_LIMIT" in line:
                self.assertIn("do not write", PROMPT[:PROMPT.index(line) + len(line)][-220:],
                              "WITHIN_ELASTIC_LIMIT appears outside its prohibition")

    def test_s03a_can_see_the_families_kept_open_by_must_cite(self):
        from ver3.assy_v3.view import derive_required_minimum
        fams = derive_required_minimum(
            "s03a", Contracts(),
            _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")).families()
        self.assertIn("Ambiguity", fams)
        self.assertIn("Freedom", fams)

    def test_every_field_the_producer_writes_is_declared(self):
        """The audit that found `addresses_obligations` and `Configuration.kind`
        undeclared - a field the producer writes and no family declares enters
        state untyped, so prose or a dangling id are both accepted and no
        consumer can dereference it.

        BEHAVIOURAL: the producer is run on a full response and the operations it
        actually emits are compared against the contract. An earlier version
        scanned the source with a regex window, which spilled from one family's
        block into the next and reported fields against the wrong family.
        """
        c = Contracts()
        ops = S03TopologyAndMobility().to_operations(
            response([joint("JNT-1"), joint("JNT-2", "COMPLIANT", **COMPLIANT_OK)]),
            {"candidate": {"entity_id": "CND-A"}})
        self.assertTrue(ops, "the producer emitted nothing to audit")
        undeclared = []
        for op in ops:
            declared = set(c.required_fields(op.entity_type)) | set(
                (c.families.get(op.entity_type) or {}).get("optional_fields") or [])
            for key in sorted(op.fields or {}):
                if key not in declared:
                    undeclared.append("%s.%s" % (op.entity_type, key))
        self.assertEqual([], sorted(set(undeclared)),
                         "the producer writes fields no family declares")

    def test_the_audit_covers_every_family_s03a_can_create(self):
        """Otherwise the audit above could pass by emitting only easy families."""
        ops = S03TopologyAndMobility().to_operations(
            response([joint("JNT-1")]), {"candidate": {"entity_id": "CND-A"}})
        produced = {op.entity_type for op in ops}
        for family in ("Body", "RigidGroup", "Joint", "Interface",
                       "Configuration", "FunctionalRegion", "UnresolvedDecision"):
            with self.subTest(family=family):
                self.assertIn(family, produced)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
