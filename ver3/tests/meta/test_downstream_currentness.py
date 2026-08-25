"""Stale CAD may not masquerade as current.

There is ONE currentness mechanism in this repository: `_propagate` walks the
`_premises` graph and withdraws standing transitively. Nothing here adds a second
one. What this file establishes is that s05, s06 and s07 are IN that graph -
because an entity recording no premise can never go stale, and would sit in state
looking authoritative after the decision it rests on had been withdrawn.

THE THREE DEFECTS THIS FILE EXISTS TO KEEP FIXED

Getting the premises wrong is not a missing feature; it produces a chain that is
stale before anything changes, which is worse than one that never goes stale at
all because it looks like the mechanism is working.

    a statement premised on the parameters it reads    -> every statement stale
                                                          the moment s06 settled
    a statement premised on the feature it realizes    -> the dependency
                                                          inverted, so s07's own
                                                          record staled its input
    s07 extending Body/Feature with compilation facts  -> a successful compile
                                                          withdrew standing from
                                                          everything premised on
                                                          the body

So `test_a_clean_chain_is_entirely_standing` is the most important test here. The
propagation tests below are only meaningful if it passes.
"""

import os
import unittest

from ver3.assy_v3.downstream import compiler, execution as ex
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

KERNEL = True
try:
    compiler.kernel()
except compiler.KernelUnavailable:                               # pragma: no cover
    KERNEL = False

MM = lambda v: {"const": v, "unit": "mm"}                        # noqa: E731
REF = lambda i: {"ref": i}                                       # noqa: E731


def s05_response():
    """A stock block at the body's envelope and a bore placed against it. The
    construction is the features' own (Unit G)."""
    return {
        "features": [
            {"id": "FEA-1", "body": "BOD-1", "feature_kind": "STOCK", "geometry": "the block",
             "placement": {"datum": "ENV-1", "axis": "+Z"},
             "construction": [{"id": "block", "operation": "BOX", "operands": [],
                               "parameters": {"dx": MM(40), "dy": MM(30), "dz": MM(20)}}]},
            {"id": "FEA-2", "body": "BOD-1", "feature_kind": "BORE", "geometry": "axial bore",
             "placement": {"datum": "FEA-1", "offset": [MM(20), MM(15), MM(-5)], "axis": "+Z"},
             "construction": [{"id": "hole", "operation": "CYLINDER", "operands": [],
                               "parameters": {"radius": REF("PRM-R"), "height": MM(30)}}]}],
        "realizations": [{"id": "RLZ-1", "addresses_obligations": ["OBL-1"],
                          "participating_features": ["FEA-2"],
                          "verification_predicate": "the bore admits the pin"}],
        "parameters": [{"id": "PRM-R", "symbol": "r", "unit": "mm"}],
        "constraints": [{"id": "CON-R", "kind": "DIMENSIONAL",
                         "parameters": ["PRM-R"],
                         "expression": {"relation": "==", "lhs": REF("PRM-R"),
                                        "rhs": MM(6)}}],
    }


@unittest.skipUnless(KERNEL, "OpenCascade kernel absent")
class _Chain(unittest.TestCase):

    def setUp(self):
        self.state = DesignState(run_id="currentness")
        self.assertEqual([], self.apply("s03", [
            Op("CREATE", "Body", "BOD-1",
               {"instance_identity": "shell", "role": "shell",
                "created_by_stage": "s03"}, "s03:topology")]))
        self.assertEqual([], self.apply("s02", [
            Op("CREATE", "Obligation", "OBL-1",
               {"statement": "the pin is retained",
                "derived_from_requirements": [], "mandatory": True,
                "scope": "UNIVERSAL", "satisfiable_at": "s05",
                "evidence_route": "MOBILITY_ANALYSIS", "route_available": True},
               "s02:derivation")]))
        # The s04 commitments the embodiment is placed against (Unit G).
        self.assertEqual([], self.apply("s04", [
            Op("CREATE", "ReferenceScale", "SCL-1",
               {"basis": "ABSOLUTE", "absolute": {"unit": "mm", "per_unit": 1.0}},
               "s04:arrangement"),
            Op("CREATE", "Envelope", "ENV-1",
               {"body": "BOD-1", "extent": {"centre": [0, 0, 0], "half_extent": [20, 15, 10]},
                "frame": "world", "maturity": "PROVISIONAL"},
               "s04:arrangement", premise_refs=["SCL-1"])]))
        self.assertEqual([], self.apply(
            "s05", S05Embodiment().to_operations(
                s05_response(), {"consumer_view": {"ReferenceScale": [{"entity_id": "SCL-1"}]}})))
        progression = Progression()
        ex.execute_settlement(self.state, progression)
        _result, execution = ex.execute_compilation(self.state, progression)
        self.signature = execution.evidence_id
        self.assertIsNotNone(self.signature, "the chain did not compile")

    def apply(self, stage, ops):
        patch = StagePatch(
            patch_id="%s-%d" % (stage, len(self.state.applied_patches)),
            run_id=self.state.run_id, stage_id=stage, stage_attempt=1,
            parent_state_hash=self.state.state_hash(), operations=list(ops),
            execution_status="SUCCESS",
            provenance={"purpose": "t", "provider": "t"})
        problems = self.state.validate(patch)
        if problems:
            return problems
        self.state.apply(patch)
        return []

    def validity(self, eid):
        return self.state.entities[eid].get("_validity", "STANDING")


class TestACleanChainIsCurrent(_Chain):
    """If a successful run leaves things stale, every test below is meaningless."""

    def test_a_clean_chain_is_entirely_standing(self):
        for eid in ("BOD-1", "OBL-1", "FEA-1", "RLZ-1", "PRM-R", "CON-R",
                    "FEA-2", self.signature):
            with self.subTest(entity=eid):
                self.assertEqual("STANDING", self.validity(eid))

    def test_the_settled_value_is_present_and_evidenced(self):
        self.assertAlmostEqual(6.0, self.state.entities["PRM-R"]["value"])
        self.assertTrue(self.state.entities["PRM-R"]["solved_by"])


class TestUpstreamChangeStalesDownstream(_Chain):

    def test_a_constraint_change_stales_the_value_and_the_geometry(self):
        """s05 Constraint -> s06 settlement -> s07 geometry."""
        self.assertEqual([], self.apply("s05", [
            Op("SUPERSEDE", "Constraint", "CON-R",
               {"expression": {"relation": "==", "lhs": REF("PRM-R"),
                               "rhs": MM(9)}},
               "s05:embodiment", reason="the bore is enlarged")]))
        self.assertEqual("STALE", self.validity("PRM-R"))
        self.assertEqual("STALE", self.validity(self.signature))

    def test_a_re_solved_value_stales_the_geometry(self):
        """s06 settlement -> s07 geometry."""
        self.assertEqual([], self.apply("s06", [
            Op("SUPERSEDE", "Parameter", "PRM-R", {"value": 9.0},
               "s06:settlement", reason="re-solved after refinement")]))
        self.assertEqual("STALE", self.validity(self.signature))

    def test_an_upstream_body_change_stales_the_embodiment_and_the_geometry(self):
        """s03 topology -> s05 feature and statements -> s07 geometry."""
        self.assertEqual([], self.apply("s03", [
            Op("SUPERSEDE", "Body", "BOD-1", {"role": "frame"},
               "s03:topology", reason="the body's role changed")]))
        self.assertEqual("STALE", self.validity("FEA-1"))
        self.assertEqual("STALE", self.validity("FEA-2"))
        self.assertEqual("STALE", self.validity(self.signature))

    def test_an_obligation_change_stales_the_realization(self):
        """s02 obligation -> s05 realization."""
        self.assertEqual([], self.apply("s02", [
            Op("SUPERSEDE", "Obligation", "OBL-1",
               {"statement": "the pin is retained under load"},
               "s02:derivation", reason="the obligation was sharpened")]))
        self.assertEqual("STALE", self.validity("RLZ-1"))

    def test_a_construction_change_stales_the_geometry(self):
        """Feature construction -> compiled artifact."""
        self.assertEqual([], self.apply("s05", [
            Op("SUPERSEDE", "Feature", "FEA-2",
               {"construction": [{"id": "hole", "operation": "CYLINDER", "operands": [],
                                  "parameters": {"radius": REF("PRM-R"), "height": MM(45)}}]},
               "s05:embodiment", reason="the bore is deeper")]))
        self.assertEqual("STALE", self.validity(self.signature))

    def test_a_moved_datum_stales_the_feature_placed_against_it(self):
        """s04 arrangement -> s05 placement -> s07 geometry: move the envelope
        the stock is placed at, and the stock, the bore against it and the
        geometry all lose standing."""
        self.assertEqual([], self.apply("s04", [
            Op("SUPERSEDE", "Envelope", "ENV-1",
               {"extent": {"centre": [5, 0, 0], "half_extent": [20, 15, 10]}},
               "s04:arrangement", reason="the block moved")]))
        for eid in ("FEA-1", "FEA-2", self.signature):
            with self.subTest(entity=eid):
                self.assertEqual("STALE", self.validity(eid))

    def test_staleness_is_dependency_local_not_global(self):
        """A change must not withdraw standing from everything indiscriminately.

        The obligation is upstream of the realization and of nothing else here,
        so the geometry is untouched by it.
        """
        self.apply("s02", [
            Op("SUPERSEDE", "Obligation", "OBL-1",
               {"statement": "sharpened"}, "s02:derivation", reason="r")])
        self.assertEqual("STALE", self.validity("RLZ-1"))
        self.assertEqual("STANDING", self.validity("FEA-2"))
        self.assertEqual("STANDING", self.validity(self.signature))


class TestArtifactAuthorityFollowsCurrentness(_Chain):
    """A file on disk is not a claim about the current design."""

    def test_the_signature_is_the_artifact_authority_and_it_goes_stale(self):
        self.assertEqual("STANDING", self.validity(self.signature))
        self.apply("s06", [Op("SUPERSEDE", "Parameter", "PRM-R", {"value": 9.0},
                              "s06:settlement", reason="re-solved")])
        self.assertEqual("STALE", self.validity(self.signature))

    def test_a_stale_signature_is_retained_rather_than_deleted(self):
        """FA-1: the record stays readable. What it loses is authority."""
        self.apply("s06", [Op("SUPERSEDE", "Parameter", "PRM-R", {"value": 9.0},
                              "s06:settlement", reason="re-solved")])
        self.assertIn(self.signature, self.state.entities)
        self.assertTrue(self.state.entities[self.signature]["signature_sha256"])

    def test_a_stale_signature_is_not_in_the_standing_set(self):
        """How a reader asks for current geometry rather than any geometry."""
        self.apply("s06", [Op("SUPERSEDE", "Parameter", "PRM-R", {"value": 9.0},
                              "s06:settlement", reason="re-solved")])
        standing = {e["entity_id"] for e in self.state.standing("GeometrySignature")}
        self.assertNotIn(self.signature, standing)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()


@unittest.skipUnless(KERNEL, "OpenCascade kernel absent")
class TestIntegratedDevelopmentChain(unittest.TestCase):
    """The canonical chain end to end, through the public interfaces.

    A DEVELOPMENT / CONTRACT FIXTURE: not live, not a benchmark result, not an
    S9-E promotion. It exists because a downstream that only ever runs from
    hand-built solver input is a downstream nobody has seen work.
    """

    @classmethod
    def setUpClass(cls):
        import tempfile
        from ver3.tools import run_trace as rt
        cls.dir = tempfile.mkdtemp(prefix="assy-dev-cad-")
        cls.trace = rt.build_development_trace(cls.dir)
        cls.by_id = {n["responsibility_id"]: n for n in cls.trace["nodes"]}

    def test_it_declares_what_it_is(self):
        self.assertFalse(self.trace["is_live"])
        self.assertFalse(self.trace["is_benchmark_result"])
        self.assertIn("not live", self.trace["provenance"])

    def test_the_chain_compiled(self):
        self.assertTrue(self.trace["compile_ok"])

    def test_all_three_downstream_nodes_executed(self):
        self.assertEqual("MODEL", self.by_id["s05"]["kind"])
        self.assertEqual("ACCEPTED", self.by_id["s05"]["contract"])
        for rid in ("s06", "s07"):
            with self.subTest(node=rid):
                self.assertTrue(self.by_id[rid]["status"].startswith("EXECUTED"))

    def test_the_envelope_constraint_settled_coupled(self):
        """boss_r = pin_r + wall, solved as a system rather than by substitution."""
        settled = self.by_id["s06"]["settled"]
        self.assertAlmostEqual(6.0, settled["PRM-0003"]["value"])
        self.assertTrue(settled["PRM-0003"]["solved_by"])

    def test_obligation_reaches_geometry_by_real_ids(self):
        """The traceability chain, read from the trace rather than asserted."""
        realization = self.by_id["s05"]["realization_graph"][0]
        self.assertIn("OBL-0001", realization["addresses_obligations"])
        self.assertIn("FEA-0002", realization["participating_features"])
        signature = self.by_id["s07"]["signatures"][0]
        self.assertEqual("BOD-0001", signature["feature_map"]["FEA-0002"])
        body = signature["compiled_bodies"][0]
        self.assertTrue(body["single_connected_solid"])
        self.assertGreater(body["volume"], 0)

    def test_the_geometry_is_current(self):
        self.assertEqual("STANDING", self.by_id["s07"]["signatures"][0]["validity"])

    def test_the_deterministic_nodes_carry_no_model_provenance(self):
        for rid in ("s06", "s07"):
            record = self.by_id[rid]["execution"]
            with self.subTest(node=rid):
                self.assertNotIn("response_source", record)
                self.assertNotIn("provider_id", record)

    def test_artifacts_were_written_and_round_tripped(self):
        # Both loops below are vacuous on an empty export map, and an empty map
        # is exactly what a compile that produced no geometry leaves behind.
        self.assertTrue(self.trace["exports"]["step_per_body"],
                        "nothing was exported, so the round-trip proves nothing")
        self.assertTrue(self.trace["roundtrip"]["brep"],
                        "no body was re-read, so the tolerance holds trivially")
        for path in self.trace["exports"]["step_per_body"].values():
            self.assertTrue(os.path.isfile(path))
        for delta in self.trace["roundtrip"]["brep"].values():
            self.assertLessEqual(delta, compiler.BREP_VOLUME_TOLERANCE)

    def test_no_benchmark_identity_leaks_into_the_fixture(self):
        blob = __import__("json").dumps(self.trace)
        for banned in ("BM-001", "BM-002", "BM-003", "cad_validation"):
            with self.subTest(term=banned):
                self.assertNotIn(banned, blob)


class TestAFeatureRestsOnItsDatumAndTheScale(unittest.TestCase):
    """A feature is placed relative to an s04 commitment, and rests on it.

    s04 states the rule for its own coordinates: "withdraw the basis and the
    numbers mean nothing." A feature placed against a joint frame, an envelope
    or a region inherits that: the datum and the scale every datum coordinate
    is stated in are premises, so a moved joint or a revised basis withdraws
    standing from the geometry placed against them (Unit G).
    """

    def _feature(self, placement):
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
        stage = S05Embodiment()
        feature = {"id": "FEA-1", "body": "BOD-1", "feature_kind": "STOCK", "geometry": "a block",
                   "placement": placement,
                   "construction": [{"id": "b", "operation": "BOX", "operands": [],
                                     "parameters": {"dx": MM(1), "dy": MM(1), "dz": MM(1)}}]}
        view = {"ReferenceScale": [{"entity_id": "SCL-CND-0001"}]}
        ops = stage.to_operations({"features": [feature]}, {stage.context_key: view})
        return [o for o in ops if o.entity_id == "FEA-1"][0]

    def test_the_fixture_supplies_a_scale_to_depend_on(self):
        op = self._feature({"datum": "ENV-1", "axis": "+Z"})
        self.assertIn("BOD-1", op.premise_refs)

    def test_a_placement_rests_on_its_datum_and_on_the_reference_scale(self):
        op = self._feature({"datum": "ENV-1", "axis": "+Z"})
        self.assertIn("ENV-1", op.premise_refs)
        self.assertIn("SCL-CND-0001", op.premise_refs,
                      "the datum's coordinates are expressed in this basis; without the "
                      "premise a revised basis leaves the placement current")

    def test_a_joint_datum_is_a_premise_too(self):
        op = self._feature({"datum": "JNT-1"})
        self.assertIn("JNT-1", op.premise_refs)


class TestGovernsInterfaceIsADependency(unittest.TestCase):
    """S05-C9's typed reference is also a currentness edge.

    A CLEARANCE constraint speaks FOR an interface. If the interface is revised,
    the constraint that expressed its clearance no longer stands on what it was
    derived from - so `governs_interface` must be a premise, not only a field
    the check can read.
    """

    def test_a_clearance_constraint_rests_on_the_interface_it_governs(self):
        from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
        ops = S05Embodiment().to_operations({"constraints": [{
            "id": "CON-1", "kind": "CLEARANCE", "parameters": ["PRM-1"],
            "governs_interface": "IFC-1",
            "expression": {"relation": ">=", "lhs": {"ref": "PRM-1"},
                           "rhs": {"const": 0.5, "unit": "mm"}}}]}, None)
        op = [o for o in ops if o.entity_id == "CON-1"][0]
        self.assertIn("IFC-1", op.premise_refs)
        self.assertIn("PRM-1", op.premise_refs)
