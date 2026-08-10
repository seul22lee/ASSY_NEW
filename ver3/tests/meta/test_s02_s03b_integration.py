"""The physical chain, end to end, with nothing seeded that a producer should make.

s02 authors the candidate-independent demand -- obligation, load case, reaction
site, physical effect obligation, candidates. s03a authors one candidate's
topology. s03b authors how THAT candidate physically realizes the demand.

Every entity below comes from a real producer through the canonical invocation
boundary. The point of the test is that the chain closes without a single string
comparison: the load case names the site it reacts at by id, and the load path
terminates at that same id.
"""
from __future__ import annotations

import json
import time
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.providers.interfaces import (GenerationResponse,     # noqa: E402
                                               GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402

S02 = {
    "obligations": [
        {"id": "OBL-0001", "statement": "the load must reach the outside world",
         "derived_from_requirements": ["REQ-0001"], "mandatory": True,
         "scope": "UNIVERSAL", "satisfiable_at": "s03",
         "evidence_route": "ANALYSIS", "route_available": True}],
    "reaction_site_requirements": [
        {"id": "RSR-0001", "scenario": "SCN-0001", "boundary_side": "EXTERNAL",
         "at_role": "the surface the product stands on",
         "why": "the scenario boundary puts the supporting surface outside"}],
    "load_cases": [
        {"id": "LC-0001", "scenario": "SCN-0001", "applied_to_role": "the moving role",
         "reacted_at_role": "the surface the product stands on",
         "reacted_at_site": "RSR-0001", "direction_class": "GRAVITY",
         "kind": "GRAVITY", "magnitude_or_status": "UNSUPPORTED"}],
    "physical_effect_obligations": [
        {"id": "PEO-0001", "effect": "TRANSMIT_FORCE",
         # ROLE NAMES. Not Actor ids, and no entity of this name exists.
         "between_roles": ["the actuation role", "the closing role"],
         "addresses_obligations": ["OBL-0001"], "under_load_case": "LC-0001",
         "persistence": "PERSISTENT"}],
    "candidates": [
        {"id": "CND-A", "summary": "a pivoting arrangement", "family": "PIVOT",
         "principle": {"support": "PIVOT"}, "obligations_addressed": ["OBL-0001"],
         "obligations_created": [],
         "evidence_route_verdict": {"route": "ANALYSIS", "available": True, "note": "n"}},
        {"id": "CND-B", "summary": "a sliding arrangement", "family": "SLIDE",
         "principle": {"support": "SLIDE"}, "obligations_addressed": ["OBL-0001"],
         "obligations_created": [],
         "evidence_route_verdict": {"route": "ANALYSIS", "available": True, "note": "n"}}],
    "acceptance_contracts": [], "unresolved": [], "assumptions": [],
}


def _s03a(suffix):
    return {
        "bodies": [{"id": "BOD-%s" % suffix, "instance_identity": "link",
                    "role": "STRUCTURE"}],
        "rigid_groups": [{"id": "RGP-%s" % suffix, "body": "BOD-%s" % suffix,
                          "members": ["BOD-%s" % suffix]}],
        "interfaces": [{"id": "IFC-%s" % suffix, "bodies": ["BOD-%s" % suffix],
                        "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"},
                       {"id": "IFG-%s" % suffix, "bodies": ["BOD-%s" % suffix],
                        "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"}],
        "joints": [{"id": "JNT-%s" % suffix, "joint_type": "REVOLUTE",
                    "parent_group": "RGP-%s" % suffix,
                    "child_group": "RGP-%s" % suffix, "dof": ["RZ"],
                    "axis_direction": "+Z", "frame_ids": ["F1"]}],
        "configurations": [{"id": "CFG-%s" % suffix, "name": "home",
                            "kind": "OPERATIONAL", "bodies_present": ["BOD-%s" % suffix],
                            "expected_mobility": []}],
    }


def _s03b(suffix, effect="TRANSMIT_FORCE"):
    return {
        "physical_interactions": [
            {"id": "PHI-%s" % suffix, "groups": ["RGP-%s" % suffix],
             "effect": effect, "discharges_effect": "PEO-0001",
             "at_interface": "IFC-%s" % suffix,
             "configurations": ["CFG-%s" % suffix]}],
        "constraint_relations": [
            {"id": "CRL-%s" % suffix, "retained_group": "RGP-%s" % suffix,
             "blocked_dofs": ["TZ"], "configurations": ["CFG-%s" % suffix],
             "driver": "LOAD",
             # The provider is the DECLARED EXTERNAL SITE, not a body of the
             # product: the world is not a body. Where it acts is the local
             # interface, which is a different fact.
             "provider_reaction_site": "RSR-0001",
             "provider_site": "IFG-%s" % suffix,
             "maintaining_interaction": "PHI-%s" % suffix}],
        "load_paths": [
            {"id": "LDP-%s" % suffix, "load_case": "LC-0001",
             "candidate": "CND-%s" % suffix,
             "ordered_hops": ["IFC-%s" % suffix, "IFG-%s" % suffix],
             "terminates_at": "RSR-0001"}],
        "assembly_steps": [], "blocking_relations": [], "unresolved": [],
    }


class _Canned:
    def __init__(self, *payloads):
        self.queue, self.calls = list(payloads), 0

    def capabilities(self):
        return ProviderCapabilities(
            provider_id="canned", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="structural test fixture")

    def generate(self, request, attempt_index=0):
        payload = self.queue[min(self.calls, len(self.queue) - 1)]
        self.calls += 1
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=json.dumps(payload),
                                        finish_reason="stop", truncated=False,
                                        input_tokens=None, output_tokens=None,
                                        served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=True)


class TestS02ToS03B(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def chain(self, suffix="A"):
        """s01 leaves the request behind; every other entity is PRODUCED."""
        s = DesignState(run_id="chain")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])

        provider = _Canned(S02, _s03a(suffix), _s03b(suffix))
        out2 = S02ObligationAndCandidates().invoke(provider, s, s.run_id)
        self.assertEqual("SUCCESS", out2.execution_status.value, out2.problems)
        s.apply(out2.patch)

        invocation = cv.InvocationContext(branch="CND-%s" % suffix)
        out3a = S03TopologyAndMobility().invoke(
            provider, s, s.run_id, {"candidate": {"entity_id": "CND-%s" % suffix}},
            invocation=invocation)
        self.assertEqual("SUCCESS", out3a.execution_status.value, out3a.problems)
        s.apply(out3a.patch)
        return s, provider, invocation

    # -- 1..4: what s02 produced -------------------------------------
    def test_INT_01_02_the_demand_is_produced_not_seeded(self):
        s, _p, _i = self.chain()
        self.assertTrue(s.has_entity("RSR-0001"), "s02 authored no reaction site")
        self.assertEqual("s02", s.entities["RSR-0001"]["_created_by"])
        self.assertEqual("EXTERNAL", s.entities["RSR-0001"]["boundary_side"])
        peo = s.entities["PEO-0001"]
        self.assertEqual("s02", peo["_created_by"])
        self.assertEqual(["the actuation role", "the closing role"],
                         peo["between_roles"])
        for role in peo["between_roles"]:
            self.assertFalse(s.has_entity(role),
                             "a role was required to be an entity")

    def test_INT_03_04_11_the_load_case_names_its_site_by_id(self):
        s, _p, _i = self.chain()
        lc = s.entities["LC-0001"]
        self.assertEqual("RSR-0001", lc["reacted_at_site"])
        self.assertEqual("ReactionSiteRequirement",
                         s.stored_family(lc["reacted_at_site"]))
        # The source wording is kept, and is NOT how the relation is found.
        self.assertEqual("the surface the product stands on", lc["reacted_at_role"])

    # -- 5..9: what s03b produced ------------------------------------
    def test_INT_05_06_07_08_09_s03b_realizes_the_demand(self):
        s, provider, invocation = self.chain()
        view = S03BMobilityAndAssembly().consumer_view(s, invocation)
        self.assertIs(cv.ViewStatus.VIEW_READY, view.status,
                      [c for a in view.assessment for c in a["coverage"]
                       if c["verdict"] != "SATISFIED"])
        before = provider.calls
        out = S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=invocation)
        self.assertEqual(before + 1, provider.calls, "the provider was not called")
        self.assertIsNotNone(out.patch, out.problems)
        s.apply(out.patch)

        self.assertEqual("PEO-0001", s.entities["PHI-A"]["discharges_effect"])
        crl = s.entities["CRL-A"]
        self.assertEqual("RSR-0001", crl["provider_reaction_site"])
        self.assertEqual("IFG-A", crl["provider_site"])
        self.assertNotIn("provider_body", crl,
                         "an external reaction was attributed to a body")
        path = s.entities["LDP-A"]
        self.assertEqual("LC-0001", path["load_case"])
        self.assertEqual("RSR-0001", path["terminates_at"])
        for hop in path["ordered_hops"]:
            self.assertEqual("Interface", s.stored_family(hop),
                             "a hop is the interface that carries the load")

    def test_INT_11_the_chain_closes_without_string_matching(self):
        """LoadCase -> its site -> the path that terminates there, all by id."""
        s, provider, invocation = self.chain()
        s.apply(S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=invocation).patch)
        site = s.entities["LC-0001"]["reacted_at_site"]
        closing = [p for p in s.family("LoadPath")
                   if p["load_case"] == "LC-0001" and p.get("terminates_at") == site]
        self.assertEqual(1, len(closing))
        self.assertEqual("EXTERNAL", s.entities[site]["boundary_side"],
                         "the path closes outside the product")

    def test_INT_10_12_everything_candidate_specific_belongs_to_this_candidate(self):
        s, provider, invocation = self.chain()
        s.apply(S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=invocation).patch)
        fwd, rev = cv._reference_graph(s, self.c)
        for eid in ("PHI-A", "CRL-A", "LDP-A"):
            self.assertEqual(cv.ACTIVE_BRANCH,
                             cv.scope_of(eid, fwd, rev, s, self.c, "CND-A")[0], eid)
        # The demand is upstream of the branch now, through authored references.
        for eid in ("PEO-0001", "LC-0001", "RSR-0001"):
            self.assertEqual(cv.COMMON_UPSTREAM,
                             cv.scope_of(eid, fwd, rev, s, self.c, "CND-A")[0], eid)
            self.assertEqual([], s.entities[eid].get("_premises", []),
                             "%s was reached by a stamped premise, not a relation"
                             % eid)


class TestTwoCandidatesThroughTheRealChain(unittest.TestCase, _fixtures.StateBuilder):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_INT_ISO_the_second_candidate_stays_isolated(self):
        s = DesignState(run_id="iso")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        provider = _Canned(S02, _s03a("A"), _s03b("A"), _s03a("B"),
                           _s03b("B", effect="PREVENT_MOTION"))
        s.apply(S02ObligationAndCandidates().invoke(provider, s, s.run_id).patch)
        for suffix in ("A", "B"):
            inv = cv.InvocationContext(branch="CND-%s" % suffix)
            s.apply(S03TopologyAndMobility().invoke(
                provider, s, s.run_id, {"candidate": {"entity_id": "CND-%s" % suffix}},
                invocation=inv).patch)
            s.apply(S03BMobilityAndAssembly().invoke(
                provider, s, s.run_id, {"candidate": "CND-%s" % suffix}, attempt=2,
                invocation=inv).patch)

        for eid in ("PHI-A", "CRL-A", "LDP-A"):
            self.assertNotIn("-B", json.dumps(s.entities[eid]), eid)
        # One demand, two realizations. Nothing was duplicated per candidate.
        self.assertEqual(1, len(s.family("PhysicalEffectObligation")))
        self.assertEqual(1, len(s.family("ReactionSiteRequirement")))
        self.assertNotEqual(s.entities["PHI-A"]["effect"], s.entities["PHI-B"]["effect"])
        fwd, rev = cv._reference_graph(s, self.c)
        self.assertEqual(cv.OTHER_BRANCH,
                         cv.scope_of("BOD-B", fwd, rev, s, self.c, "CND-A")[0])
        for branch in ("CND-A", "CND-B"):
            self.assertEqual(cv.COMMON_UPSTREAM,
                             cv.scope_of("RSR-0001", fwd, rev, s, self.c, branch)[0])


if __name__ == "__main__":
    unittest.main()


class TestS4ExitAudit(_fixtures.StateBuilder, unittest.TestCase):
    """The S-4 exit checks: references that must resolve, and demand that must be
    answered or declared open."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def base(self):
        s = DesignState(run_id="exit")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        provider = _Canned(S02, _s03a("A"), _s03b("A"))
        s.apply(S02ObligationAndCandidates().invoke(provider, s, s.run_id).patch)
        inv = cv.InvocationContext(branch="CND-A")
        s.apply(S03TopologyAndMobility().invoke(
            provider, s, s.run_id, {"candidate": {"entity_id": "CND-A"}},
            invocation=inv).patch)
        return s, inv

    # -- every S-4 reference must resolve when it is authored ---------
    def test_S4_REF_a_named_referent_that_does_not_exist_is_refused(self):
        from ver3.assy_v3.state.design_state import ContractError
        cases = {
            "LoadPath.terminates_at": ("load_paths", 0, "terminates_at", "RSR-NOWHERE"),
            "LoadPath.ordered_hops": ("load_paths", 0, "ordered_hops", ["IFC-NOWHERE"]),
            "ConstraintRelation.provider_reaction_site":
                ("constraint_relations", 0, "provider_reaction_site", "RSR-NOWHERE"),
            "ConstraintRelation.provider_site":
                ("constraint_relations", 0, "provider_site", "IFC-NOWHERE"),
            "PhysicalInteraction.at_interface":
                ("physical_interactions", 0, "at_interface", "IFC-NOWHERE"),
            "PhysicalInteraction.discharges_effect":
                ("physical_interactions", 0, "discharges_effect", "PEO-NOWHERE"),
        }
        for label, (collection, idx, field, value) in cases.items():
            s, inv = self.base()
            payload = json.loads(json.dumps(_s03b("A")))
            payload[collection][idx][field] = value
            out = S03BMobilityAndAssembly().run(
                _Canned(payload), {"consumer_view": {}, "candidate": "CND-A"},
                s, s.run_id, attempt=2)
            with self.assertRaises(ContractError, msg=label) as caught:
                s.apply(out.patch)
            self.assertIn("DANGLING_REF", str(caught.exception), label)

    def test_S4_REF_load_case_reacted_at_site_must_resolve(self):
        from ver3.assy_v3.state.design_state import ContractError
        s = DesignState(run_id="lc")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        payload = json.loads(json.dumps(S02))
        payload["load_cases"][0]["reacted_at_site"] = "RSR-NOWHERE"
        out = S02ObligationAndCandidates().invoke(_Canned(payload), s, s.run_id)
        with self.assertRaises(ContractError) as caught:
            s.apply(out.patch)
        self.assertIn("DANGLING_REF", str(caught.exception))

    def test_S4_REF_optional_is_not_the_same_as_unresolved(self):
        """Omitting the field is fine. Naming something that is not there is not."""
        s, inv = self.base()
        payload = json.loads(json.dumps(_s03b("A")))
        del payload["load_paths"][0]["terminates_at"]
        payload["unresolved"] = [
            {"id": "S3U-1001", "decision": "where this load is reacted",
             "why_open": "no external site is reachable in this arrangement",
             "alternatives": [], "alternatives_kind": "FREE_TEXT",
             "kept_open_by": [], "blocks": ["LDP-A"]}]
        out = S03BMobilityAndAssembly().run(
            _Canned(payload), {"consumer_view": {}, "candidate": "CND-A"},
            s, s.run_id, attempt=2)
        s.apply(out.patch)
        self.assertNotIn("terminates_at", s.entities["LDP-A"])

    # -- demand must be answered, or declared open --------------------
    def test_S4_COMPLETE_silence_about_a_given_demand_is_reported(self):
        s, inv = self.base()
        view = S03BMobilityAndAssembly().consumer_view(s, inv).payload()
        silent = {"physical_interactions": [], "constraint_relations": [],
                  "load_paths": [], "assembly_steps": [],
                  "blocking_relations": [], "unresolved": []}
        missing = S03BMobilityAndAssembly().completeness(
            silent, {"consumer_view": view})
        self.assertTrue(any("PEO-0001" in m for m in missing), missing)
        self.assertTrue(any("LC-0001" in m for m in missing), missing)

    def test_S4_COMPLETE_an_explicit_open_answer_is_accepted(self):
        s, inv = self.base()
        view = S03BMobilityAndAssembly().consumer_view(s, inv).payload()
        declared = {"physical_interactions": [], "constraint_relations": [],
                    "load_paths": [], "assembly_steps": [],
                    "blocking_relations": [],
                    "unresolved": [{"id": "S3U-1001", "decision": "d",
                                    "why_open": "w", "alternatives": [],
                                    "alternatives_kind": "FREE_TEXT",
                                    "kept_open_by": [],
                                    "blocks": ["PEO-0001", "LC-0001"]}]}
        missing = S03BMobilityAndAssembly().completeness(
            declared, {"consumer_view": view})
        self.assertEqual([], [m for m in missing
                              if "PEO-0001" in m or "LC-0001" in m])

    def test_S4_COMPLETE_nothing_is_repaired(self):
        """Completeness reports. It does not write into the response."""
        s, inv = self.base()
        view = S03BMobilityAndAssembly().consumer_view(s, inv).payload()
        silent = {"physical_interactions": [], "constraint_relations": [],
                  "load_paths": [], "assembly_steps": [],
                  "blocking_relations": [], "unresolved": []}
        before = json.dumps(silent, sort_keys=True)
        S03BMobilityAndAssembly().completeness(silent, {"consumer_view": view})
        self.assertEqual(before, json.dumps(silent, sort_keys=True))

    # -- the boundary S-4 must not cross ------------------------------
    def test_S4_no_later_stage_work_was_pulled_forward(self):
        s, inv = self.base()
        provider = _Canned(_s03b("A"))
        s.apply(S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=inv).patch)
        for family in ("MobilityExpectation", "Envelope", "ReferenceScale",
                       "State", "Transition", "SweptVolume", "SelectionDecision",
                       "EliminationRecord"):
            self.assertEqual([], s.family(family),
                             "%s belongs to a later step" % family)
