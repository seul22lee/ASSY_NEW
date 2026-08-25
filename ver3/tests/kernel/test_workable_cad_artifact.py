"""UNIT G, with the kernel: the artifact is validated as a mechanism.

Features are built in frames derived from s04's datums; bodies are composed by
declared polarity; the same embodiment compiles to the same signature; posed
bodies are judged per interface at the features that realize it, under s04's
contact policy, in every state and along every transition; the exchange files
exist and read back; and nothing is invented for a body the pose law cannot
place."""

import os
import tempfile
import unittest

from ver3.assy_v3.downstream import compiler, execution as ex, findings
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.state.patch import Op
from ver3.tests.meta.test_workable_cad_foundation import apply, hinge

try:
    compiler.kernel()
except compiler.KernelUnavailable:                               # pragma: no cover
    raise unittest.SkipTest("OpenCascade kernel absent")


def chain(**kwargs):
    state = hinge(**kwargs)
    p = Progression()
    report, _ = ex.execute_settlement(state, p)
    assert report.solver_status == "feasible", report.problems
    out = tempfile.mkdtemp(prefix="unitG-")
    result, execution = ex.execute_compilation(state, p, out_dir=out)
    return state, result, execution, out


class TestFeaturesAreBuiltWhereTheirDatumsAre(unittest.TestCase):

    def test_the_bore_is_at_the_joint_frame_and_the_stock_at_the_envelope(self):
        state, result, execution, _out = chain()
        self.assertTrue(result.ok, result.problems)
        base = next(b for b in result.bodies if b.body_id == "BOD-A")
        full = 40 * 30 * 10
        # the bore along +Y through (40, 0, 10) removes a quarter cylinder at the edge
        self.assertLess(base.volume, full)
        self.assertGreater(base.volume, full - 3.1416 * 9 * 30)
        self.assertEqual([0.0, 0.0, 0.0], [round(v, 6) for v in base.bbox[:3]])
        lid = next(b for b in result.bodies if b.body_id == "BOD-B")
        self.assertEqual({"FEA-B-STOCK": "ADDITIVE", "FEA-B-PIN": "ADDITIVE"}, lid.feature_map)
        self.assertEqual({"FEA-A-STOCK": "ADDITIVE", "FEA-A-BORE": "SUBTRACTIVE"}, base.feature_map)

    def test_compilation_is_deterministic(self):
        _s1, r1, _e1, _o1 = chain()
        _s2, r2, _e2, _o2 = chain()
        self.assertEqual(r1.signature["signature_sha256"], r2.signature["signature_sha256"])


class TestTheArtifactIsJudgedAsAMechanism(unittest.TestCase):

    def test_expected_bodies_are_built_and_valid_and_features_trace(self):
        state, result, execution, _out = chain()
        report = result.artifact
        self.assertEqual(["BOD-A", "BOD-B"], report["expected_bodies"])
        self.assertEqual(["BOD-A", "BOD-B"], report["built_bodies"])
        for bid in report["built_bodies"]:
            self.assertTrue(report["body_validity"][bid]["valid"])
            self.assertTrue(report["body_validity"][bid]["single_connected_solid"])
        self.assertEqual({"body": "BOD-A", "polarity": "SUBTRACTIVE"}, report["feature_map"]["FEA-A-BORE"])
        signature = state.entities[execution.evidence_id]
        self.assertEqual("BOD-B", signature["feature_map"]["FEA-B-PIN"])
        for premise in ("FEA-A-BORE", "BOD-A", "PRM-R"):
            self.assertIn(premise, signature["_premises"])

    def test_the_interface_is_judged_at_its_realizing_features_in_every_state(self):
        state, result, execution, _out = chain(contact="CONTACT")
        report = result.artifact
        self.assertEqual(["STA-1", "STA-2"], sorted(report["states"]))
        for sid, st in report["states"].items():
            with self.subTest(state=sid):
                self.assertEqual(["BOD-A", "BOD-B"], st["posed_bodies"])
                self.assertLessEqual(st["pairs"]["BOD-A|BOD-B"]["shared_volume"],
                                     compiler.INTERFERENCE_VOLUME_TOLERANCE)
                iface = st["interfaces"]["IFC-1"]
                self.assertEqual(["FEA-A-BORE", "FEA-B-PIN"], iface["features"])
                self.assertLessEqual(iface["distance"], compiler.CONTACT_DISTANCE_TOLERANCE)
        self.assertEqual([], [f for f in report["findings"] if f["evaluable"]], report["findings"])
        self.assertEqual("compiled", execution.outcome)
        self.assertTrue(report["workable"])

    def test_a_declared_clearance_that_is_not_there_is_a_finding_at_that_interface(self):
        state, result, execution, _out = chain(contact="CLEARANCE")
        found = [f for f in result.artifact["findings"] if f["kind"] == findings.MATING_NOT_REALIZED]
        self.assertTrue(found)
        self.assertIn("IFC-1", found[0]["subjects"])
        self.assertEqual("compiled_with_findings", execution.outcome)

    def test_a_stop_in_the_way_blocks_the_travel_on_the_actual_solids(self):
        state, result, execution, _out = chain(with_stop=True)
        self.assertTrue(result.ok, result.problems)
        trn = result.artifact["transitions"]["TRN-1"]
        self.assertTrue(trn["blocked"])
        self.assertEqual(9, trn["sampling_declaration"]["samples"])
        self.assertEqual([], trn["samples"][0]["findings"])
        self.assertTrue(any(f["kind"] == findings.TRAVEL_BLOCKED for f in trn["samples"][-1]["findings"]))
        self.assertFalse(result.artifact["workable"])

    def test_exports_exist_and_read_back_with_both_bodies(self):
        state, result, execution, out = chain()
        exports = result.artifact["exports"]
        for path in exports["assembly_step_per_state"].values():
            self.assertTrue(os.path.isfile(path) and os.path.getsize(path) > 0, path)
        for path in exports["stl_per_body"].values():
            self.assertTrue(os.path.isfile(path), path)
        K = compiler.kernel()
        reader = K["STEPControl_Reader"]()
        reader.ReadFile(exports["assembly_step_per_state"]["STA-1"])
        reader.TransferRoots()
        exp = K["TopExp_Explorer"](reader.OneShape(), K["TopAbs_SOLID"])
        n = 0
        while exp.More():
            n += 1
            exp.Next()
        self.assertEqual(2, n)
        self.assertEqual(["BOD-A", "BOD-B"], sorted(result.exports["step_per_body"]))


class TestS07InventsNothing(unittest.TestCase):

    def test_a_withdrawn_joint_realization_makes_settlement_not_ready(self):
        state = hinge()
        self.assertEqual([], apply(state, "s05", [
            Op("INVALIDATE", "Feature", "FEA-B-PIN", {}, "s05:embodiment", reason="withdrawn")]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual("not_ready", report.solver_status)
        self.assertTrue(any("JNT-1" in x for x in report.problems), report.problems)

    def test_no_scale_means_no_compile(self):
        state = hinge(basis="RELATIVE")
        p = Progression()
        ex.execute_settlement(state, p)
        result, execution = ex.execute_compilation(state, p)
        self.assertFalse(result.ok)
        self.assertEqual("not_ready", execution.outcome)
        self.assertTrue(any("no scale authority" in x for x in result.problems), result.problems)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
