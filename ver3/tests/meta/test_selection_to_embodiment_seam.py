"""From a human choice to authored geometry, through the real stage seam.

Everything here goes through `S05Embodiment.invoke()` with a deterministic fake
provider. That matters more than it sounds: `to_operations()` can be called
directly with hand-written premises already on it, and a test built that way
proves the test author knows what the premises should be - not that production
puts them there. The invocation path is where `invocation_premises` is actually
consulted, so it is the only place the claim can be checked.

The provider returns a fixed, contract-valid response. It is not a model and
proves nothing about model quality; what it isolates is ORCHESTRATION - given a
standing choice, does the system carry that choice into every fact it authors.

The geometry-producing half of the seam is
ver3/tests/kernel/test_selected_seam_to_geometry.py, which reuses this fixture.
"""

import json
import time
import unittest

from . import _fixtures, _paths

from ver3.assy_v3.providers.interfaces import (GenerationResponse,
                                               GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.providers.status import ExecutionStatus
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch


def _mm(v):
    return {"const": float(v), "unit": "mm"}


def _ref(p):
    return {"ref": p}


EMBODIMENT = {
    "features": [{"id": "FEA-0001", "body": "BOD-0001", "feature_kind": "BORE",
                  "geometry": "axial bore",
                  "envelope": {"centre": [20.0, 15.0, 10.0],
                               "half_extent": [6.0, 6.0, 10.0]}}],
    "realizations": [{"id": "RLZ-0001", "addresses_obligations": ["OBL-0001"],
                      "participating_features": ["FEA-0001"],
                      "verification_predicate":
                          "the bore admits the retained member"}],
    "parameters": [{"id": "PRM-0001", "symbol": "pin_r", "unit": "mm"},
                   {"id": "PRM-0002", "symbol": "wall", "unit": "mm"},
                   {"id": "PRM-0003", "symbol": "boss_r", "unit": "mm"}],
    "constraints": [
        {"id": "CON-0001", "kind": "DIMENSIONAL", "parameters": ["PRM-0001"],
         "expression": {"relation": "==", "lhs": _ref("PRM-0001"), "rhs": _mm(4)}},
        {"id": "CON-0002", "kind": "DIMENSIONAL", "parameters": ["PRM-0002"],
         "expression": {"relation": "==", "lhs": _ref("PRM-0002"), "rhs": _mm(2)}},
        {"id": "CON-0003", "kind": "ENVELOPE",
         "parameters": ["PRM-0001", "PRM-0002", "PRM-0003"],
         "expression": {"relation": "==", "lhs": _ref("PRM-0003"),
                        "rhs": {"op": "+", "args": [_ref("PRM-0001"),
                                                    _ref("PRM-0002")]}}}],
    "construction_statements": [
        {"id": "CST-0001", "body": "BOD-0001", "operation": "BOX", "operands": [],
         "parameters": {"dx": _mm(40), "dy": _mm(30), "dz": _mm(20)}},
        {"id": "CST-0002", "body": "BOD-0001", "operation": "CYLINDER",
         "operands": [], "feature": "FEA-0001",
         "parameters": {"radius": _ref("PRM-0003"), "height": _mm(30)}},
        {"id": "CST-0003", "body": "BOD-0001", "operation": "TRANSLATE",
         "operands": ["CST-0002"],
         "parameters": {"dx": _mm(20), "dy": _mm(15), "dz": _mm(-5)}},
        {"id": "CST-0004", "body": "BOD-0001", "operation": "CUT",
         "operands": ["CST-0001", "CST-0003"], "parameters": {}}],
    "unresolved": [],
}


class FixedProvider:
    """Deterministic. Not a model, and never described as one."""

    def __init__(self, payload=EMBODIMENT):
        self.payload, self.calls = payload, 0

    def capabilities(self):
        return ProviderCapabilities(
            provider_id="fixed", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="deterministic seam fixture")

    def generate(self, request, attempt_index=0):
        self.calls += 1
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(
                raw_text=json.dumps(self.payload), finish_reason="stop",
                truncated=False, input_tokens=None, output_tokens=None,
                served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=True)


class SeamFixture(_fixtures.StateBuilder, unittest.TestCase):
    """A design that has branched, been decided, and is ready to be embodied."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")

    def selected_design(self, selected="CND-A", *, with_motion=True,
                        with_load=True, run="seam"):
        state = DesignState(run_id=run)
        A, B = ["CND-A"], ["CND-B"]
        self.add(state, "s02", "Candidate", "CND-A",
                 principle="a hinged cover retained by a snap latch")
        self.add(state, "s02", "Candidate", "CND-B",
                 principle="a sliding lid running in a groove")
        self.add(state, "selection", "SelectionDecision", "SEL-0001",
                 selected_candidate=selected)
        self.add(state, "s02", "Obligation", "OBL-0001", scope="UNIVERSAL",
                 satisfiable_at="s05", mandatory=True,
                 statement="the retained member is located",
                 evidence_route="MOBILITY_ANALYSIS", route_available=True,
                 derived_from_requirements=[])
        # The selected branch's decided mechanism.
        self.add(state, "s03", "Body", "BOD-0001", A, instance_identity="enclosure",
                 role="shell", created_by_stage="s03")
        self.add(state, "s03", "RigidGroup", "RGP-0001", A)
        self.add(state, "s03", "Interface", "IFC-0001", A, bodies=["BOD-0001"])
        self.add(state, "s03", "Joint", "JNT-0001", A)
        self.add(state, "s03", "PhysicalInteraction", "PIN-0001", A)
        # A CANONICAL role and a volume the embodiment stays out of. The
        # generic builder would supply role="x", which is not in the declared
        # vocabulary - S05-C8 reports that rather than passing it, so a fixture
        # relying on the default was describing a region the contract does not
        # define while calling itself a positive case.
        self.add(state, "s03", "FunctionalRegion", "FRG-0001", A,
                 role="KEEP_OUT",
                 volume={"centre": [200.0, 200.0, 200.0],
                         "half_extent": [5.0, 5.0, 5.0]})
        self.add(state, "s03", "AssemblyStep", "ASM-0001", A)
        self.add(state, "s04", "ReferenceScale", "SCL-0001", A, basis="ABSOLUTE",
                 absolute={"unit": "mm", "per_unit": 1.0})
        self.add(state, "s04", "Envelope", "ENV-0001", A)
        if with_motion:
            self.add(state, "s04", "State", "STA-0001", A)
            self.add(state, "s04", "Transition", "TRN-0001", A)
            self.add(state, "s04", "SweptVolume", "SWV-0001", A)
        if with_load:
            self.add(state, "s03", "LoadPath", "LDP-0001", A)
        # The OTHER branch exists too. A design with one candidate cannot show
        # that anything was excluded.
        self.add(state, "s03", "Body", "BOD-0002", B, instance_identity="lid",
                 role="cover", created_by_stage="s03")
        return state

    def embody(self, state, provider=None, run_id="seam-run"):
        """The real invocation path, committed exactly as production commits it."""
        provider = provider or FixedProvider()
        stage = S05Embodiment()
        outcome = stage.invoke(provider, state, run_id)
        self.assertIs(ExecutionStatus.SUCCESS, outcome.execution_status,
                      "the seam fixture did not reach the provider: %s"
                      % outcome.problems)
        self.assertEqual(1, provider.calls)
        # The STAGE built this patch, premises and all. Committing the stage's
        # own patch rather than rebuilding one from its operations is the point:
        # a test that reassembles the patch is testing its own assembly.
        self.assertIsNotNone(outcome.patch, "the stage produced no patch")
        problems = state.validate(outcome.patch)
        self.assertEqual([], problems, "s05 output was rejected: %s" % problems)
        state.apply(outcome.patch)
        return outcome


class TestTheViewCarriesTheDecidedMechanism(SeamFixture):
    """§4: the prompt says the mechanism is already decided. Prove it is IN there."""

    def setUp(self):
        self.view = S05Embodiment().consumer_view(self.selected_design())
        self.payload = self.view.payload()

    def test_the_view_is_ready(self):
        """Every assertion below is about a view that a provider would be given."""
        self.assertEqual("VIEW_READY", self.view.status.value)

    def test_the_selection_decision_is_present(self):
        self.assertEqual(["SEL-0001"],
                         [r["entity_id"] for r in self.payload["SelectionDecision"]])

    def test_the_selected_candidate_and_principle_are_present(self):
        candidates = self.payload["Candidate"]
        self.assertEqual(["CND-A"], [r["entity_id"] for r in candidates])
        self.assertIn("snap latch", candidates[0]["principle"])

    def test_the_decided_topology_is_present(self):
        for family in ("Body", "RigidGroup", "Interface", "Joint",
                       "PhysicalInteraction"):
            with self.subTest(family=family):
                self.assertTrue(self.payload.get(family),
                                "%s is not visible, so the 'already decided' "
                                "mechanism is partly invisible" % family)

    def test_motion_evidence_is_present_when_it_exists(self):
        """§4.2. A feature placed into a path already proven clear turns a
        moving design into one that binds."""
        for family in ("State", "Transition", "SweptVolume"):
            with self.subTest(family=family):
                self.assertTrue(self.payload.get(family))

    def test_load_route_is_present_when_it_exists(self):
        self.assertTrue(self.payload.get("LoadPath"))

    def test_the_spatial_basis_is_present_and_still_means_something(self):
        """§11.1. A coordinate has no meaning without its basis, so carrying the
        ReferenceScale but losing its unit or its per_unit would deliver a frame
        that cannot convert anything - and every dimensional comparison
        downstream would silently read a scale that says nothing."""
        scales = self.payload.get("ReferenceScale") or []
        self.assertTrue(scales)
        absolute = scales[0].get("absolute") or {}
        self.assertEqual("ABSOLUTE", scales[0].get("basis"))
        self.assertEqual("mm", absolute.get("unit"))
        self.assertEqual(1.0, absolute.get("per_unit"))

    def test_the_other_candidates_body_is_not_present(self):
        """Least privilege survives all of the above being added."""
        ids = [r["entity_id"] for r in self.payload.get("Body") or []]
        self.assertIn("BOD-0001", ids)
        self.assertNotIn("BOD-0002", ids)


class TestAStaticMechanismIsStillReady(SeamFixture):
    """§4.2: MAY_BE_EMPTY means what it says.

    A design with no motion must not be forced to author a Transition it does
    not have merely to satisfy s05's readiness. Inventing one to pass a gate
    would be inventing engineering.
    """

    def test_no_motion_and_no_load_still_reaches_the_provider(self):
        state = self.selected_design(with_motion=False, with_load=False)
        view = S05Embodiment().consumer_view(state)
        self.assertEqual("VIEW_READY", view.status.value)
        self.assertNotIn("Transition", view.payload())


class TestEveryAuthoredFactRestsOnTheChoice(SeamFixture):
    """§5: through `invoke`, not through `to_operations`."""

    def setUp(self):
        self.state = self.selected_design()
        self.outcome = self.embody(self.state)

    def test_the_invocation_actually_authored_something(self):
        """Otherwise the loops below iterate over nothing."""
        creates = [o for o in self.outcome.patch.operations if o.kind == "CREATE"]
        self.assertGreaterEqual(len(creates), 11)

    def test_every_created_entity_rests_on_the_selected_candidate(self):
        for op in self.outcome.patch.operations:
            if op.kind != "CREATE":
                continue
            with self.subTest(entity=op.entity_id):
                self.assertIn("CND-A", op.premise_refs)

    def test_every_created_entity_rests_on_the_selection_decision(self):
        """A different fact from the candidate. Withdraw the candidate and the
        geometry describes nothing; withdraw the decision and it describes
        something real the design is no longer pursuing."""
        for op in self.outcome.patch.operations:
            if op.kind != "CREATE":
                continue
            with self.subTest(entity=op.entity_id):
                self.assertIn("SEL-0001", op.premise_refs)

    def test_local_dependencies_are_not_replaced_by_the_invocation_premises(self):
        """Union, not overwrite. A constraint still rests on its parameters."""
        by_id = {o.entity_id: o for o in self.outcome.patch.operations}
        constraint = by_id["CON-0003"]
        for expected in ("PRM-0001", "PRM-0002", "PRM-0003"):
            with self.subTest(premise=expected):
                self.assertIn(expected, constraint.premise_refs)

    def test_the_committed_state_carries_the_same_premises(self):
        """Not only the operation: what actually landed in DesignState."""
        for family in ("Feature", "Parameter", "Constraint",
                       "ConstructionStatement", "Realization"):
            for record in self.state.family(family):
                with self.subTest(entity=record["entity_id"]):
                    self.assertIn("CND-A", record.get("_premises") or [])
                    self.assertIn("SEL-0001", record.get("_premises") or [])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
