"""UNIT F, with the kernel: the gate admits a settled chain, the signature it
registers rests on what it was compiled from, and the same program compiles to
the same signature every time."""

import unittest

from ver3.assy_v3.downstream import compiler, execution as ex, ir
from ver3.assy_v3.pipeline.progression import Progression
from ver3.tests.meta.test_downstream_settlement_gate import _Embodied, apply
from ver3.assy_v3.state.patch import Op

try:
    compiler.kernel()
except compiler.KernelUnavailable:                               # pragma: no cover
    raise unittest.SkipTest("OpenCascade kernel absent")


class TestSettledChainCompiles(_Embodied):

    def test_the_gate_admits_a_settled_program_and_signs_it_with_premises(self):
        self.settle()
        result, execution = ex.execute_compilation(self.state, Progression())
        self.assertTrue(result.ok, result.problems)
        self.assertTrue(execution.patch_applied)
        signature = self.state.entities[execution.evidence_id]
        self.assertTrue(signature["_premises"])
        self.assertIn("CST-1", signature["_premises"])
        self.assertIn("PRM-W", signature["_premises"])
        self.assertEqual(1, len(result.bodies))

    def test_compilation_is_deterministic(self):
        self.settle()
        a, _ = ex.execute_compilation(self.state, Progression())
        other = _Embodied("setUp")
        other.setUp()
        other.settle()
        b, _ = ex.execute_compilation(other.state, Progression())
        self.assertEqual(a.signature["signature_sha256"], b.signature["signature_sha256"])

    def test_a_constraint_revision_stales_the_compiled_geometry(self):
        self.settle()
        _r, execution = ex.execute_compilation(self.state, Progression())
        self.assertEqual([], apply(self.state, "s05", [
            Op("SUPERSEDE", "Constraint", "CON-W",
               {"expression": {"relation": "==", "lhs": {"ref": "PRM-W"},
                               "rhs": {"const": 15, "unit": "mm"}}},
               "s05:embodiment", reason="enlarged")]))
        self.assertEqual("STALE", self.validity(execution.evidence_id))
        self.assertEqual("STALE", self.validity("PRM-W"))
        ready, why = ex.canonical_io.compilation_readiness(self.state)
        self.assertFalse(ready, "stale geometry would be recompiled over a stale value")


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
