"""s03b authors how THIS candidate physically realizes a design-wide demand.

`PhysicalInteraction` and `ConstraintRelation` had been declared s03b outputs
since S-2 with nothing authoring them. An interaction TRANSMITS and a joint
CONSTRAINS - the freeze separates them deliberately - and until now the
transmission had no home, so it lived in prose.

The demand stays candidate-independent. Two candidates realize the same
PhysicalEffectObligation differently, and neither owns it.
"""
from __future__ import annotations

import inspect
import json
import time
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.providers.interfaces import (GenerationResponse,     # noqa: E402
                                               GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly)
from ver3.assy_v3.state.design_state import (Contracts, ContractError,  # noqa: E402
                                             DesignState)


def _s03b(suffix, effect="TRANSMIT_FORCE", hops=None, terminates="RSR-0001",
          discharges="PEO-0001"):
    """What s03b says about one candidate's physical realization."""
    out = {
        "physical_interactions": [
            {"id": "PHI-%s" % suffix, "groups": ["RGP-%s" % suffix],
             "effect": effect, "discharges_effect": discharges,
             "at_interface": "IFC-%s" % suffix}],
        "constraint_relations": [
            {"id": "CRL-%s" % suffix, "retained_group": "RGP-%s" % suffix,
             "blocked_dofs": ["TX"], "configurations": ["CFG-%s" % suffix],
             "driver": "LOAD", "provider_body": "BOD-%s" % suffix,
             "provider_site": "IFC-%s" % suffix,
             "maintaining_interaction": "PHI-%s" % suffix}],
        "load_paths": [
            {"id": "LDP-%s" % suffix, "load_case": "LC-0001",
             "candidate": "CND-%s" % suffix,
             "ordered_hops": hops if hops is not None else ["IFC-%s" % suffix]}],
        "assembly_steps": [], "blocking_relations": [], "unresolved": [],
    }
    if terminates:
        out["load_paths"][0]["terminates_at"] = terminates
    return out


class _Canned:
    def __init__(self, payload):
        self.payload = payload

    def capabilities(self):
        return ProviderCapabilities(
            provider_id="canned", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="structural test fixture")

    def generate(self, request, attempt_index=0):
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=json.dumps(self.payload),
                                        finish_reason="stop", truncated=False,
                                        input_tokens=None, output_tokens=None,
                                        served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=True)


class _Base(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def design(self):
        """Design-wide demand, then a branch each. No candidate owns the demand."""
        s = DesignState(run_id="s03b")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        self.add(s, "s02", "Obligation", "OBL-0001", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-0001"],
                 involves_actors=["ACT-0001"])
        self.add(s, "s02", "ReactionSiteRequirement", "RSR-0001",
                 scenario="SCN-0001", boundary_side="EXTERNAL",
                 at_role="the surface the product stands on")
        # Named explicitly: the field is required now, and letting the fixture
        # builder invent a referent would quietly create a SECOND reaction site.
        self.add(s, "s02", "LoadCase", "LC-0001", scenario="SCN-0001",
                 reacted_at_site="RSR-0001")
        self.add(s, "s02", "PhysicalEffectObligation", "PEO-0001",
                 effect="TRANSMIT_FORCE", between_roles=["the actuation role"],
                 addresses_obligations=["OBL-0001"], under_load_case="LC-0001")
        for suffix in ("A", "B"):
            self.add(s, "s02", "Candidate", "CND-%s" % suffix, principle={"h": "f"},
                     addresses_obligations=["OBL-0001"], obligations_created=[])
            self.topology(s, suffix)
        return s

    def topology(self, s, suffix):
        c = "CND-%s" % suffix
        self.add(s, "s03", "Body", "BOD-%s" % suffix, prem=[c])
        self.add(s, "s03", "RigidGroup", "RGP-%s" % suffix, prem=[c],
                 body="BOD-%s" % suffix)
        self.add(s, "s03", "Interface", "IFC-%s" % suffix, prem=[c],
                 bodies=["BOD-%s" % suffix])
        self.add(s, "s03", "Configuration", "CFG-%s" % suffix, prem=[c],
                 bodies_present=["BOD-%s" % suffix], expected_mobility=[])

    def realize(self, s, suffix, payload=None):
        return S03BMobilityAndAssembly().run(
            _Canned(payload or _s03b(suffix)),
            {"consumer_view": {}, "candidate": "CND-%s" % suffix},
            s, s.run_id, attempt=2)


class TestS03BProduces(_Base):

    def test_S4_PI_01_physical_interaction_now_has_a_producer(self):
        s = self.design()
        out = self.realize(s, "A")
        self.assertIsNotNone(out.patch, out.problems)
        s.apply(out.patch)
        rec = s.entities["PHI-A"]
        self.assertEqual("PhysicalInteraction", rec["_family"])
        self.assertEqual("TRANSMIT_FORCE", rec["effect"])
        self.assertEqual(["RGP-A"], rec["groups"])
        self.assertEqual("PEO-0001", rec["discharges_effect"])

    def test_S4_CR_01_02_constraint_relation_now_has_a_producer(self):
        s = self.design()
        s.apply(self.realize(s, "A").patch)
        rec = s.entities["CRL-A"]
        self.assertEqual("ConstraintRelation", rec["_family"])
        self.assertEqual("RGP-A", rec["retained_group"])
        self.assertEqual("LOAD", rec["driver"])
        # A provider is a resolvable reference or the relation is incomplete.
        self.assertTrue(s.has_entity(rec["provider_body"]))
        self.assertTrue(s.has_entity(rec["provider_site"]))
        self.assertTrue(s.has_entity(rec["maintaining_interaction"]))

    def test_S4_LP_02_03_04_load_path_is_candidate_specific_and_typed(self):
        s = self.design()
        s.apply(self.realize(s, "A").patch)
        rec = s.entities["LDP-A"]
        self.assertEqual("LC-0001", rec["load_case"])
        self.assertEqual("CND-A", rec["candidate"])
        self.assertEqual(["IFC-A"], rec["ordered_hops"])
        self.assertEqual("RSR-0001", rec["terminates_at"])
        for hop in rec["ordered_hops"]:
            self.assertEqual("Interface", s.stored_family(hop),
                             "a hop must name the Interface that carries it")

    def test_S4_LP_09_an_open_path_stays_open(self):
        """Terminating nowhere is a real answer. Nothing closes it for the model."""
        s = self.design()
        s.apply(self.realize(s, "A", _s03b("A", terminates=None)).patch)
        self.assertNotIn("terminates_at", s.entities["LDP-A"])

    def test_S4_08_nothing_is_invented_from_absence(self):
        """A response that authors no physical fact yields none. Deterministic
        code may validate and apply; it may not decide the engineering."""
        s = self.design()
        empty = {"physical_interactions": [], "constraint_relations": [],
                 "load_paths": [], "assembly_steps": [], "blocking_relations": [],
                 "unresolved": []}
        out = self.realize(s, "A", empty)
        created = [op.entity_type for op in out.patch.operations]
        self.assertEqual([], [f for f in created
                              if f in ("PhysicalInteraction", "ConstraintRelation",
                                       "LoadPath")])
        # Scan the CODE, not the prose that explains it.
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S03BMobilityAndAssembly.to_operations)
        for banned in ("MAINTAINED_BY_CLASS", "infer", "synthes", "default_"):
            self.assertNotIn(banned, src,
                             "the producer decides an engineering fact: %s" % banned)

    def test_S4_10_s03b_authors_no_spatial_or_mobility_disposition(self):
        s = self.design()
        s.apply(self.realize(s, "A").patch)
        for family in ("Envelope", "ReferenceScale", "State", "Transition",
                       "MobilityExpectation", "SelectionDecision"):
            self.assertEqual([], s.family(family),
                             "s03b authored %s, which belongs to a later step" % family)

    def test_S4_05_09_prose_and_foreign_references_are_refused(self):
        s = self.design()
        prose = _s03b("A")
        prose["physical_interactions"][0]["discharges_effect"] = "the force must pass"
        with self.assertRaises(ContractError) as caught:
            s.apply(self.realize(s, "A", prose).patch)
        self.assertIn("REFERENCE_NOT_AN_ID", str(caught.exception))

    def test_S4_PI_07_a_missing_referent_is_refused(self):
        s = self.design()
        bad = _s03b("A", discharges="PEO-NOWHERE")
        with self.assertRaises(ContractError) as caught:
            s.apply(self.realize(s, "A", bad).patch)
        self.assertIn("PEO-NOWHERE", str(caught.exception))


class TestTwoCandidateIsolation(_Base):
    """The central falsifier: one demand, two realizations, no leakage."""

    def test_S4_PI_02_04_05_06_LP_05_06_07(self):
        s = self.design()
        s.apply(self.realize(s, "A").patch)

        # A's facts reference only A's topology.
        for eid in ("PHI-A", "CRL-A", "LDP-A"):
            blob = json.dumps(s.entities[eid])
            self.assertNotIn("-B", blob, "%s reached candidate B's topology" % eid)

        fwd, rev = cv._reference_graph(s, self.c)
        # The demand is upstream of A now, because A's interaction reaches it.
        self.assertEqual(cv.COMMON_UPSTREAM,
                         cv.scope_of("PEO-0001", fwd, rev, s, self.c, "CND-A")[0])
        self.assertEqual(cv.COMMON_UPSTREAM,
                         cv.scope_of("LC-0001", fwd, rev, s, self.c, "CND-A")[0])
        # B is untouched by A's realization.
        self.assertEqual(cv.UNSCOPED,
                         cv.scope_of("PEO-0001", fwd, rev, s, self.c, "CND-B")[0])
        self.assertEqual(cv.OTHER_BRANCH,
                         cv.scope_of("BOD-B", fwd, rev, s, self.c, "CND-A")[0])

        # B may realize the SAME demand differently, and the demand is not copied.
        s.apply(self.realize(s, "B", _s03b("B", effect="PREVENT_MOTION")).patch)
        self.assertEqual(1, len(s.family("PhysicalEffectObligation")),
                         "the demand was duplicated per candidate")
        self.assertEqual("PEO-0001", s.entities["PHI-B"]["discharges_effect"])
        self.assertNotEqual(s.entities["PHI-A"]["effect"],
                            s.entities["PHI-B"]["effect"])
        fwd, rev = cv._reference_graph(s, self.c)
        for branch in ("CND-A", "CND-B"):
            self.assertEqual(cv.COMMON_UPSTREAM,
                             cv.scope_of("PEO-0001", fwd, rev, s, self.c, branch)[0])


class TestReactionSiteRequirement(_Base):

    def test_the_site_is_candidate_independent_and_typed(self):
        s = self.design()
        rec = s.entities["RSR-0001"]
        self.assertEqual("EXTERNAL", rec["boundary_side"])
        self.assertEqual("SCN-0001", rec["scenario"])
        self.assertEqual([], rec.get("_premises", []),
                         "the reaction site was tied to a candidate")
        self.assertEqual("s02", self.c.owner_of("ReactionSiteRequirement"))

    def test_both_candidates_close_at_the_same_declared_site(self):
        s = self.design()
        s.apply(self.realize(s, "A").patch)
        s.apply(self.realize(s, "B").patch)
        self.assertEqual("RSR-0001", s.entities["LDP-A"]["terminates_at"])
        self.assertEqual("RSR-0001", s.entities["LDP-B"]["terminates_at"])
        self.assertEqual(1, len(s.family("ReactionSiteRequirement")))


if __name__ == "__main__":
    unittest.main()
