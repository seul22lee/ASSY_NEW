"""s02 authors the physical demand, in entities, with ids.

Two producer gaps met here. `PhysicalEffectObligation` had been a declared s02
output since S-2 with nothing authoring it - its own contract rule says "S-2
defines it. S-4/U-5 is where s02 begins producing it." And R-B: the recorded
responses DESCRIBED the obligations a candidate creates instead of writing them,
so a typed reference held prose and the write boundary refused the patch.

An obligation says what must be true. A physical effect obligation says what
physical effect makes it true, between which roles, under which load case. They
are not the same fact, and neither is candidate-specific.
"""
from __future__ import annotations

import json
import os
import time
import unittest

from . import _fixtures, _paths                                        # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.providers.interfaces import (GenerationResponse,     # noqa: E402
                                               GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    EFFECT_KINDS, S02ObligationAndCandidates)
from ver3.assy_v3.state.design_state import (Contracts, ContractError,  # noqa: E402
                                             DesignState)


def _response(obligations_created, physical=True):
    """An s02 response. `obligations_created` is what R-B got wrong."""
    out = {
        "obligations": [
            {"id": "OBL-0001", "statement": "the joint must carry the applied load",
             "derived_from_requirements": ["REQ-0001"], "mandatory": True,
             "scope": "UNIVERSAL", "satisfiable_at": "s03",
             "evidence_route": "ANALYSIS", "route_available": True},
            {"id": "OBL-0002", "statement": "the rotating relation must be supported",
             "derived_from_requirements": ["REQ-0001"], "mandatory": True,
             "scope": "CANDIDATE_DISCRIMINATING", "satisfiable_at": "s03",
             "evidence_route": "ANALYSIS", "route_available": True}],
        "load_cases": [
            {"id": "LC-0001", "scenario": "SCN-0001", "applied_to_role": "the mover",
             "reacted_at_role": "the ground", "direction_class": "GRAVITY",
             "kind": "GRAVITY", "magnitude_or_status": "UNSUPPORTED"}],
        "candidates": [
            {"id": "CND-0001", "summary": "a pivoting arrangement", "family": "PIVOT",
             "principle": {"support": "PIVOT"},
             "obligations_addressed": ["OBL-0001"],
             "obligations_created": obligations_created,
             "evidence_route_verdict": {"route": "ANALYSIS", "available": True,
                                        "note": "n"}},
            {"id": "CND-0002", "summary": "a sliding arrangement", "family": "SLIDE",
             "principle": {"support": "SLIDE"},
             "obligations_addressed": ["OBL-0001"],
             "obligations_created": [],
             "evidence_route_verdict": {"route": "ANALYSIS", "available": True,
                                        "note": "n"}}],
        "acceptance_contracts": [], "unresolved": [], "assumptions": [],
    }
    if physical:
        out["physical_effect_obligations"] = [
            {"id": "PEO-0001", "effect": "TRANSMIT_FORCE",
             "between_roles": ["ACT-0001"], "addresses_obligations": ["OBL-0001"],
             "under_load_case": "LC-0001", "persistence": "PERSISTENT"},
            {"id": "PEO-0002", "effect": "PERMIT_MOTION",
             "between_roles": ["ACT-0001"], "addresses_obligations": ["OBL-0002"]}]
    return out


#: What the recorded corpus contains: the obligation described, never written.
R_B_RESPONSE = _response(["radial support and axial retention for the rotating relation"])
#: What a canonical producer emits: the obligation written, and its id referenced.
CANONICAL_RESPONSE = _response(["OBL-0002"])


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

    def upstream(self):
        """What s01 leaves behind. No candidate, no topology, no physical fact."""
        s = DesignState(run_id="s02")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        return s

    def run_s02(self, payload):
        s = self.upstream()
        out = S02ObligationAndCandidates().invoke(_Canned(payload), s, s.run_id)
        return s, out


# =====================================================================
# R-B
# =====================================================================
class TestRB(_Base):

    def test_S4_RB_01_04_prose_in_a_typed_reference_is_still_refused(self):
        s, out = self.run_s02(R_B_RESPONSE)
        self.assertEqual("SCHEMA_FAILURE", out.execution_status.value)
        self.assertTrue(any("REFERENCE_NOT_AN_ID" in p and "obligations_created" in p
                            for p in out.problems), out.problems)
        with self.assertRaises(ContractError):
            s.apply(out.patch)

    def test_S4_RB_01b_the_producer_reports_it_as_its_own_finding(self):
        """Attribution: the stage says the reference is not an id, so the failure
        reads as the producer's and not as a contract problem."""
        missing = S02ObligationAndCandidates().completeness(R_B_RESPONSE, {})
        self.assertTrue(any("obligations_created" in m and "not an entity id" in m
                            for m in missing), missing)
        self.assertEqual([], [m for m in
                              S02ObligationAndCandidates().completeness(
                                  CANONICAL_RESPONSE, {})
                              if "not an entity id" in m])

    def test_S4_RB_02_03_07_10_canonical_output_closes_in_one_patch(self):
        s, out = self.run_s02(CANONICAL_RESPONSE)
        self.assertEqual("SUCCESS", out.execution_status.value, out.problems)
        s.apply(out.patch)
        self.assertEqual(["OBL-0002"], s.entities["CND-0001"]["obligations_created"])
        self.assertTrue(s.has_entity("OBL-0002"),
                        "the created obligation was referenced and never written")
        self.assertEqual("Obligation", s.stored_family("OBL-0002"))

    def test_S4_RB_05_06_no_shim_and_no_benchmark_repair(self):
        import inspect
        src = inspect.getsource(S02ObligationAndCandidates)
        for banned in ("BM-0", "PRB-0", "generate_id", "_coerce", "_repair",
                       "slugify", "uuid", "hashlib"):
            self.assertNotIn(banned, src, "a compatibility shim appeared: %s" % banned)
        # completeness REPORTS; it must not write into the parsed response.
        before = json.dumps(R_B_RESPONSE, sort_keys=True)
        S02ObligationAndCandidates().completeness(R_B_RESPONSE, {})
        self.assertEqual(before, json.dumps(R_B_RESPONSE, sort_keys=True),
                         "the producer rewrote the model's answer")


# =====================================================================
# The physical demand
# =====================================================================
class TestPhysicalEffectObligation(_Base):

    def test_S4_S02_05_the_producer_now_exists(self):
        s, out = self.run_s02(CANONICAL_RESPONSE)
        s.apply(out.patch)
        peos = {e["entity_id"] for e in s.family("PhysicalEffectObligation")}
        self.assertEqual({"PEO-0001", "PEO-0002"}, peos,
                         "s02 still authors no physical effect obligation")
        rec = s.entities["PEO-0001"]
        self.assertEqual("TRANSMIT_FORCE", rec["effect"])
        self.assertEqual(["ACT-0001"], rec["between_roles"])
        self.assertEqual(["OBL-0001"], rec["addresses_obligations"])
        self.assertEqual("LC-0001", rec["under_load_case"])

    def test_S4_S02_05b_the_effect_vocabulary_is_the_contracts(self):
        declared = self.c.families["PhysicalEffectObligation"]["effect"]
        self.assertEqual(tuple(declared), EFFECT_KINDS)
        prompt = S02ObligationAndCandidates().prompt({"consumer_view": {}})
        for effect in declared:
            self.assertIn(effect, prompt)

    def test_S4_S02_01_02_07_the_demand_is_candidate_independent(self):
        s, out = self.run_s02(CANONICAL_RESPONSE)
        s.apply(out.patch)
        for eid in ("PEO-0001", "PEO-0002"):
            rec = s.entities[eid]
            self.assertEqual([], rec.get("_premises", []),
                             "%s was tied to a candidate" % eid)
            self.assertNotIn("candidate", rec)
        # Both alternatives address the same demand; neither owns it.
        for cid in ("CND-0001", "CND-0002"):
            self.assertIn("OBL-0001", s.entities[cid]["addresses_obligations"])
        self.assertEqual(1, len([e for e in s.family("PhysicalEffectObligation")
                                 if e["addresses_obligations"] == ["OBL-0001"]]),
                         "the demand was duplicated per candidate")

    def test_S4_S02_08_created_and_addressed_are_not_confused(self):
        s, out = self.run_s02(CANONICAL_RESPONSE)
        s.apply(out.patch)
        a, b = s.entities["CND-0001"], s.entities["CND-0002"]
        self.assertEqual(["OBL-0001"], a["addresses_obligations"])
        self.assertEqual(["OBL-0002"], a["obligations_created"])
        self.assertEqual([], b["obligations_created"],
                         "a candidate that creates nothing was given something")
        self.assertNotEqual(a["addresses_obligations"], a["obligations_created"])

    def test_S4_S02_04_the_demand_traces_to_its_reason(self):
        s, out = self.run_s02(CANONICAL_RESPONSE)
        s.apply(out.patch)
        peo = s.entities["PEO-0001"]
        obligation = s.entities[peo["addresses_obligations"][0]]
        self.assertEqual(["REQ-0001"], obligation["derived_from_requirements"])
        self.assertTrue(s.has_entity(peo["under_load_case"]))
        self.assertTrue(s.has_entity(peo["between_roles"][0]))

    def test_S4_S02_05c_06_07_s02_authors_no_candidate_specific_realization(self):
        s, out = self.run_s02(CANONICAL_RESPONSE)
        s.apply(out.patch)
        for family in ("PhysicalInteraction", "ConstraintRelation", "LoadPath",
                       "Body", "RigidGroup", "Joint", "Envelope"):
            self.assertEqual([], s.family(family),
                             "s02 authored %s, which is not its to author" % family)


# =====================================================================
# An unseen shape
# =====================================================================
class TestUnseenShape(_Base):
    """Not a benchmark: a demand no recorded case contains."""

    def test_S4_S02_09_a_metering_demand_between_two_actors(self):
        payload = _response(["OBL-0002"])
        payload["physical_effect_obligations"] = [
            {"id": "PEO-9001", "effect": "METER", "between_roles": ["ACT-0001"],
             "addresses_obligations": ["OBL-0001", "OBL-0002"],
             "persistence": "INTERMITTENT"}]
        s, out = self.run_s02(payload)
        self.assertEqual("SUCCESS", out.execution_status.value, out.problems)
        s.apply(out.patch)
        rec = s.entities["PEO-9001"]
        self.assertEqual("METER", rec["effect"])
        self.assertEqual(["OBL-0001", "OBL-0002"], rec["addresses_obligations"])
        self.assertNotIn("under_load_case", rec,
                         "an optional field was filled in for the model")

    def test_S4_S02_10_between_roles_is_a_role_not_an_entity(self):
        """"Roles, never bodies" - and never Actors either.

        This field used to be declared a reference to Actor, which conflated the
        EXTERNAL participant with the product/function role the freeze means:
        "a force must pass from the actuation role to the closing role". It is
        now a role name, carried the way `LoadCase.applied_to_role` already
        carries one, so there is no entity for it to name wrongly.

        Discharge stays checkable through `PhysicalInteraction.discharges_effect`,
        which IS addressable - that never depended on roles being entities.
        """
        spec = self.c.field_semantics("PhysicalEffectObligation")["between_roles"]
        self.assertEqual("role_name", spec["kind"])
        self.assertIsNone(self.c.reference_spec("PhysicalEffectObligation",
                                                "between_roles"))
        s, out = self.run_s02(CANONICAL_RESPONSE)
        s.apply(out.patch)
        self.assertEqual(["ACT-0001"], s.entities["PEO-0001"]["between_roles"],
                         "the value is carried verbatim, not resolved")


if __name__ == "__main__":
    unittest.main()
