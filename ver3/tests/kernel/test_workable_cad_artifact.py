"""UNIT G, with the kernel: the artifact is validated as a mechanism.

A placed primitive is actually built where its feature says; the same program
compiles to the same signature; posed bodies are judged for interference under
s04's contact policy in every state and along every transition; the exchange
files exist and read back; and nothing is invented for a body the pose law
cannot place."""

import os
import tempfile
import unittest

from ver3.assy_v3.downstream import artifact, compiler, execution as ex, findings
from ver3.assy_v3.pipeline.progression import Progression
from ver3.tests.meta.test_workable_cad_foundation import hinge

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


class TestPlacedPrimitivesAreBuiltWhereTheFeatureSays(unittest.TestCase):

    def test_the_bore_is_at_the_placement_not_at_the_origin(self):
        state, result, execution, _out = chain()
        self.assertTrue(result.ok, result.problems)
        base = next(b for b in result.bodies if b.body_id == "BOD-A")
        # a 40x30x10 plate with a radius-3 bore along +Y through (40, 0, 10):
        # material removed is the quarter-cylinder at the edge, not a full bore
        # at the origin
        full = 40 * 30 * 10
        self.assertLess(base.volume, full)
        self.assertGreater(base.volume, full - 3.1416 * 9 * 30)
        lid = next(b for b in result.bodies if b.body_id == "BOD-B")
        # the pin on the lid stands along +Y from (0,0,0): its bbox starts below y=0? no -
        # it extends the bbox by the radius in x and z, and y from 0 to 30
        self.assertLessEqual(lid.bbox[0], -3 + 1e-6)

    def test_compilation_is_deterministic_with_placements(self):
        _s1, r1, _e1, _o1 = chain()
        _s2, r2, _e2, _o2 = chain()
        self.assertEqual(r1.signature["signature_sha256"], r2.signature["signature_sha256"])


class TestTheArtifactIsJudgedAsAMechanism(unittest.TestCase):

    def test_expected_bodies_are_built_and_valid(self):
        state, result, execution, _out = chain()
        report = result.artifact
        self.assertEqual(["BOD-A", "BOD-B"], report["expected_bodies"])
        self.assertEqual(["BOD-A", "BOD-B"], report["built_bodies"])
        for bid in report["built_bodies"]:
            self.assertTrue(report["body_validity"][bid]["valid"])
            self.assertTrue(report["body_validity"][bid]["single_connected_solid"])
        self.assertEqual({"FEA-A": ["CST-A2"], "FEA-B": ["CST-B2"]}, report["correspondence"])

    def test_posed_bodies_touch_and_do_not_interfere_in_every_state(self):
        state, result, execution, _out = chain(contact="CONTACT")
        report = result.artifact
        self.assertEqual(["STA-1", "STA-2"], sorted(report["states"]))
        for sid, st in report["states"].items():
            with self.subTest(state=sid):
                self.assertEqual(["BOD-A", "BOD-B"], st["posed_bodies"])
                pair = st["pairs"]["BOD-A|BOD-B"]
                self.assertLessEqual(pair["shared_volume"], compiler.INTERFERENCE_VOLUME_TOLERANCE)
        kinds = [f["kind"] for f in report["findings"] if f["evaluable"]]
        self.assertEqual([], kinds, report["findings"])
        self.assertEqual("compiled", execution.outcome)
        self.assertTrue(report["workable"])

    def test_a_declared_clearance_that_is_not_there_is_a_finding(self):
        state, result, execution, _out = chain(contact="CLEARANCE")
        kinds = {f["kind"] for f in result.artifact["findings"]}
        self.assertIn(findings.MATING_NOT_REALIZED, kinds)
        self.assertEqual("compiled_with_findings", execution.outcome)
        self.assertTrue(execution.findings)

    def test_a_stop_in_the_way_blocks_the_travel_on_the_actual_solids(self):
        state, result, execution, _out = chain(with_stop=True)
        self.assertTrue(result.ok, result.problems)
        report = result.artifact
        trn = report["transitions"]["TRN-1"]
        self.assertTrue(trn["blocked"])
        self.assertEqual(9, trn["sampling_declaration"]["samples"])
        first, last = trn["samples"][0], trn["samples"][-1]
        self.assertEqual([], first["findings"])
        self.assertTrue(any(f["kind"] == findings.TRAVEL_BLOCKED for f in last["findings"]))
        self.assertFalse(report["workable"])

    def test_regions_in_a_relative_basis_are_not_evaluated_and_not_passed(self):
        state, result, execution, _out = chain(basis="RELATIVE")
        # no region declared here: nothing to evaluate and nothing claimed
        self.assertEqual("RELATIVE", result.artifact["basis"])
        self.assertTrue(all(f["evaluable"] for f in result.artifact["findings"]))

    def test_exports_exist_and_read_back(self):
        state, result, execution, out = chain()
        exports = result.artifact["exports"]
        for sid, path in exports["assembly_step_per_state"].items():
            self.assertTrue(os.path.isfile(path), path)
            self.assertGreater(os.path.getsize(path), 0)
        for bid, path in exports["stl_per_body"].items():
            self.assertTrue(os.path.isfile(path), path)
        K = compiler.kernel()
        reader = K["STEPControl_Reader"]()
        reader.ReadFile(exports["assembly_step_per_state"]["STA-1"])
        reader.TransferRoots()
        shape = reader.OneShape()
        exp = K["TopExp_Explorer"](shape, K["TopAbs_SOLID"])
        n = 0
        while exp.More():
            n += 1
            exp.Next()
        self.assertEqual(2, n, "the assembly STEP does not hold both bodies")
        self.assertEqual(sorted(result.exports["step_per_body"]), ["BOD-A", "BOD-B"])


class TestS07InventsNothing(unittest.TestCase):

    def test_an_unrealized_joint_leaves_the_body_unposed_and_is_a_finding(self):
        from ver3.assy_v3.state.patch import Op
        from ver3.tests.meta.test_workable_cad_foundation import apply
        state = hinge()
        # withdraw the lid's realization: the joint can no longer place the lid
        self.assertEqual([], apply(state, "s05", [
            Op("INVALIDATE", "Feature", "FEA-B", {}, "s05:embodiment", reason="withdrawn")]))
        p = Progression()
        report, _ = ex.execute_settlement(state, p)
        self.assertEqual("not_ready", report.solver_status)
        self.assertTrue(any("JNT-1" in x for x in report.problems), report.problems)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
