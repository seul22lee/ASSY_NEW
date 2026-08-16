"""s05 -> s06 -> s07 through canonical DesignState, with authority enforced.

The previous downstream tests exercised the solver and compiler cores directly.
These exercise the PIPELINE: state in, authorized patches out, real geometry at
the end. The difference matters because every defect this layer can have lives in
the seam - a write outside declared authority, a value the compiler was handed
that nobody solved, a branch reading another branch's parameters.
"""

import os
import tempfile
import unittest

from ver3.assy_v3.downstream import adapters, compiler, execution as ex, ir
from ver3.assy_v3.pipeline.progression import DeterministicExecution, Progression
from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

KERNEL = True
try:
    compiler.kernel()
except compiler.KernelUnavailable:                               # pragma: no cover
    KERNEL = False

MM = lambda v: {"const": v, "unit": "mm"}                        # noqa: E731
REF = lambda i: {"ref": i}                                       # noqa: E731


def apply(state, stage, ops, attempt=1, premises=None):
    patch = StagePatch(
        patch_id="%s-%d-%d" % (stage, attempt, len(state.applied_patches)),
        run_id=state.run_id, stage_id=stage, stage_attempt=attempt,
        parent_state_hash=state.state_hash(), operations=list(ops),
        execution_status="SUCCESS", provenance={"purpose": "t", "provider": "t"})
    problems = state.validate(patch)
    if problems:
        return problems
    state.apply(patch)
    return []


def param(pid, symbol, unit="mm"):
    return Op("CREATE", "Parameter", pid,
              {"symbol": symbol, "unit": unit, "status": ir.DECLARED},
              "s05:embodiment")


def equals(cid, lhs, rhs, params):
    return Op("CREATE", "Constraint", cid,
              {"kind": "DIMENSIONAL", "parameters": list(params),
               "expression": {"relation": "==", "lhs": lhs, "rhs": rhs}},
              "s05:embodiment")


def body(state, bid="BOD-0001"):
    return apply(state, "s03", [Op("CREATE", "Body", bid,
                                   {"instance_identity": bid, "role": "shell",
                                    "created_by_stage": "s03"}, "s03:topology")])


class TestSettlementWritesOnlyWhatItMay(unittest.TestCase):

    def setUp(self):
        self.state = DesignState(run_id="settle")
        self.assertEqual([], apply(self.state, "s05", [
            param("PRM-0001", "pin_r"), param("PRM-0002", "wall"),
            param("PRM-0003", "boss_r"),
            equals("CON-0001", REF("PRM-0003"),
                   {"op": "+", "args": [REF("PRM-0001"), REF("PRM-0002")]},
                   ["PRM-0001", "PRM-0002", "PRM-0003"]),
            equals("CON-0002", REF("PRM-0001"), MM(4), ["PRM-0001"]),
            equals("CON-0003", REF("PRM-0002"), MM(2), ["PRM-0002"])]))

    def test_a_feasible_settlement_is_written_with_its_evidence(self):
        report, execution = ex.execute_settlement(self.state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status)
        self.assertTrue(execution.patch_applied)
        rec = self.state.entities["PRM-0003"]
        self.assertAlmostEqual(6.0, rec["value"])
        self.assertTrue(rec["solved_by"], "a settled value with no solver artifact")

    def test_the_evidence_id_is_derived_from_the_system(self):
        """Same system, same evidence - determinism visible in state."""
        a, _ = ex.execute_settlement(self.state, Progression())
        self.assertEqual(adapters.evidence_identity(a),
                         self.state.entities["PRM-0003"]["solved_by"])

    def test_s07_may_not_write_a_parameter_value(self):
        """The authority that keeps compilation out of engineering decisions."""
        problems = apply(self.state, "s07",
                         [Op("EXTEND", "Parameter", "PRM-0001", {"value": 9.0},
                             "s07:compilation")])
        self.assertTrue(any("EXTEND_WRONG_STAGE" in p for p in problems), problems)

    def test_s05_may_not_write_a_parameter_value_either(self):
        """S05-C10 as an authority fact, not only as a completeness check."""
        problems = apply(self.state, "s05",
                         [Op("EXTEND", "Parameter", "PRM-0001", {"value": 9.0},
                             "s05:embodiment")])
        self.assertTrue(any("EXTEND_WRONG_STAGE" in p for p in problems), problems)

    def test_an_unsettled_system_writes_nothing(self):
        state = DesignState(run_id="free")
        self.assertEqual([], apply(state, "s05", [param("PRM-0009", "free")]))
        report, execution = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.UNDERDETERMINED, report.solver_status)
        self.assertFalse(execution.patch_applied)
        self.assertIsNone(state.entities["PRM-0009"].get("value"))


class TestDeterministicExecutionCarriesNoModelProvenance(unittest.TestCase):
    """s06 and s07 contact no provider, so the fields must not exist."""

    def test_the_record_has_no_response_source_or_provider(self):
        rec = DeterministicExecution(responsibility_id="s06", stage_id="s06",
                                     outcome=ir.FEASIBLE)
        self.assertFalse(hasattr(rec, "response_source"))
        self.assertFalse(hasattr(rec, "provider_id"))
        self.assertNotIn("response_source", rec.as_record())
        self.assertNotIn("provider_id", rec.as_record())

    def test_deterministic_runs_are_not_in_the_live_executions_list(self):
        """Otherwise full-live qualification would have to special-case them."""
        state = DesignState(run_id="sep")
        apply(state, "s05", [param("PRM-1", "x")])
        p = Progression()
        ex.execute_settlement(state, p)
        self.assertEqual([], p.executions)
        self.assertEqual(1, len(p.deterministic))

    def test_the_record_says_what_it_was_given(self):
        state = DesignState(run_id="dig")
        apply(state, "s05", [param("PRM-1", "x")])
        p = Progression()
        _r, execution = ex.execute_settlement(state, p)
        self.assertTrue(execution.input_digest)


class TestBoundedConvergence(unittest.TestCase):
    """The loop's termination rule is the contract's, not monotone reduction."""

    def _coupled(self, determined=True):
        state = DesignState(run_id="conv")
        ops = [param("PRM-A", "a"), param("PRM-B", "b")]
        if determined:
            ops += [
                equals("CON-1", {"op": "+", "args": [REF("PRM-A"), REF("PRM-B")]},
                       MM(10), ["PRM-A", "PRM-B"]),
                equals("CON-2", {"op": "-", "args": [REF("PRM-A"), REF("PRM-B")]},
                       MM(2), ["PRM-A", "PRM-B"])]
        self.assertEqual([], apply(state, "s05", ops))
        return state

    def test_a_determined_system_settles_in_one_round(self):
        state = self._coupled()
        outcome = ex.settle(state, Progression())
        self.assertEqual(ex.SETTLED, outcome.status)
        self.assertEqual(1, outcome.rounds)
        self.assertAlmostEqual(6.0, state.entities["PRM-A"]["value"])

    def test_nobody_able_to_refine_escalates_rather_than_guessing(self):
        state = self._coupled(determined=False)
        outcome = ex.settle(state, Progression())
        self.assertEqual(ex.ESCALATED, outcome.status)
        self.assertIsNone(state.entities["PRM-A"].get("value"))

    def test_a_refiner_that_changes_nothing_is_a_cycle_not_a_budget(self):
        """The repeated-state rule. Asking again would get the same answer."""
        state = self._coupled(determined=False)
        outcome = ex.settle(state, Progression(), refine=lambda i, r: True)
        self.assertEqual(ex.CYCLE, outcome.status)
        self.assertEqual(2, outcome.rounds)

    def test_every_round_is_recorded(self):
        state = self._coupled(determined=False)
        p = Progression()
        ex.settle(state, p, refine=lambda i, r: True)
        self.assertEqual(2, len(p.deterministic_by_responsibility("s06")))

    def test_a_refiner_that_supplies_the_missing_constraint_converges(self):
        state = self._coupled(determined=False)

        def refine(round_index, report):
            apply(state, "s05", [
                equals("CON-R1", REF("PRM-A"), MM(7), ["PRM-A"]),
                equals("CON-R2", REF("PRM-B"), MM(3), ["PRM-B"])],
                attempt=round_index + 1)
            return True

        outcome = ex.settle(state, Progression(), refine=refine)
        self.assertEqual(ex.SETTLED, outcome.status)
        self.assertAlmostEqual(7.0, state.entities["PRM-A"]["value"])


class TestBranchIsolation(unittest.TestCase):
    """Two alternatives in one DesignState must not settle against each other."""

    def setUp(self):
        self.state = DesignState(run_id="branch")
        def candidate(cid, principle):
            return Op("CREATE", "Candidate", cid,
                      {"summary": cid, "family": "ACTUATE",
                       "principle": {"ACTUATE": principle},
                       "addresses_obligations": [], "obligations_created": [],
                       "evidence_route_verdict": {"route": "MOBILITY_ANALYSIS",
                                                  "available": True}},
                      "s02:derivation")
        # Asserted, because a silently rejected setUp makes every isolation
        # assertion below vacuously true.
        self.assertEqual([], apply(self.state, "s02",
                                   [candidate("CND-A", "DIRECT_MANUAL"),
                                    candidate("CND-B", "STORED_ENERGY")]))
        for branch, pid, value in (("CND-A", "PRM-A1", 10), ("CND-B", "PRM-B1", 99)):
            self.assertEqual([], apply(self.state, "s05", [
                Op("CREATE", "Parameter", pid,
                   {"symbol": "w", "unit": "mm", "status": ir.DECLARED},
                   "s05:embodiment", premise_refs=[branch]),
                Op("CREATE", "Constraint", "CON-%s" % pid,
                   {"kind": "DIMENSIONAL", "parameters": [pid],
                    "expression": {"relation": "==", "lhs": REF(pid),
                                   "rhs": MM(value)}},
                   "s05:embodiment", premise_refs=[branch])]))

    def test_a_branch_reads_only_its_own_parameters(self):
        self.assertEqual(["PRM-A1"],
                         [p.entity_id for p in
                          adapters.read_parameters(self.state, "CND-A")])
        self.assertEqual(["PRM-B1"],
                         [p.entity_id for p in
                          adapters.read_parameters(self.state, "CND-B")])

    def test_settling_one_branch_leaves_the_other_unsettled(self):
        report, _ = ex.execute_settlement(self.state, Progression(), branch="CND-A")
        self.assertEqual(ir.FEASIBLE, report.solver_status)
        self.assertAlmostEqual(10.0, self.state.entities["PRM-A1"]["value"])
        self.assertIsNone(self.state.entities["PRM-B1"].get("value"))

    def test_the_compiler_is_given_only_its_branch_values(self):
        ex.execute_settlement(self.state, Progression(), branch="CND-A")
        self.assertEqual({"PRM-A1"},
                         set(adapters.resolved_values(self.state, "CND-A")))


@unittest.skipUnless(KERNEL, "OpenCascade kernel absent")
class TestCompilationFromCanonicalState(unittest.TestCase):
    """The end of the chain: canonical state to a real solid."""

    def setUp(self):
        self.state = DesignState(run_id="compile")
        self.assertEqual([], body(self.state))
        self.assertEqual([], apply(self.state, "s05", [
            param("PRM-R", "boss_r"),
            equals("CON-R", REF("PRM-R"), MM(6), ["PRM-R"]),
            Op("CREATE", "Feature", "FEA-0001",
               {"body": "BOD-0001", "feature_kind": "BORE", "geometry": "axial bore"},
               "s05:embodiment"),
            Op("CREATE", "ConstructionStatement", "CST-0001",
               {"body": "BOD-0001", "operation": "BOX", "operands": [],
                "parameters": {"dx": MM(40), "dy": MM(30), "dz": MM(20)}},
               "s05:embodiment"),
            Op("CREATE", "ConstructionStatement", "CST-0002",
               {"body": "BOD-0001", "operation": "CYLINDER", "operands": [],
                "feature": "FEA-0001",
                "parameters": {"radius": REF("PRM-R"), "height": MM(30)}},
               "s05:embodiment"),
            Op("CREATE", "ConstructionStatement", "CST-0003",
               {"body": "BOD-0001", "operation": "TRANSLATE", "operands": ["CST-0002"],
                "parameters": {"dx": MM(20), "dy": MM(15), "dz": MM(-5)}},
               "s05:embodiment"),
            Op("CREATE", "ConstructionStatement", "CST-0004",
               {"body": "BOD-0001", "operation": "CUT",
                "operands": ["CST-0001", "CST-0003"], "parameters": {}},
               "s05:embodiment")]))

    def test_the_chain_compiles_and_registers_a_signature(self):
        p = Progression()
        ex.execute_settlement(self.state, p)
        result, execution = ex.execute_compilation(self.state, p)
        self.assertTrue(result.ok, result.problems)
        self.assertTrue(execution.patch_applied)
        signature = self.state.entities[execution.evidence_id]
        self.assertEqual(result.signature["signature_sha256"],
                         signature["signature_sha256"])

    def test_geometry_traces_back_to_the_statement_and_feature(self):
        """`Why does this CAD feature exist` has to be answerable."""
        p = Progression()
        ex.execute_settlement(self.state, p)
        ex.execute_compilation(self.state, p)
        self.assertEqual("CST-0002",
                         self.state.entities["FEA-0001"]["compiled_by_statement"])
        self.assertTrue(self.state.entities["BOD-0001"]["compiled"]["is_valid"])

    def test_a_value_with_no_solver_evidence_never_reaches_the_kernel(self):
        """R-23 at the last door. The compiler compiles solved decisions only."""
        state = DesignState(run_id="unsolved")
        self.assertEqual([], body(state))
        self.assertEqual([], apply(state, "s05", [
            param("PRM-X", "r"),
            Op("CREATE", "ConstructionStatement", "CST-1",
               {"body": "BOD-0001", "operation": "CYLINDER", "operands": [],
                "parameters": {"radius": REF("PRM-X"), "height": MM(5)}},
               "s05:embodiment")]))
        result, execution = ex.execute_compilation(state, Progression())
        self.assertFalse(result.ok)
        self.assertEqual("CST-1", result.failed_statement)
        self.assertFalse(execution.patch_applied)

    def test_a_failed_compile_registers_no_artifact(self):
        state = DesignState(run_id="nofact")
        self.assertEqual([], body(state))
        apply(state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-1",
               {"body": "BOD-0001", "operation": "BOX", "operands": [],
                "parameters": {"dx": MM(-1), "dy": MM(1), "dz": MM(1)}},
               "s05:embodiment")])
        result, execution = ex.execute_compilation(state, Progression())
        self.assertFalse(result.ok)
        self.assertIsNone(execution.evidence_id)
        self.assertEqual([], state.family("GeometrySignature"))

    def test_exports_land_where_asked_and_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Progression()
            ex.execute_settlement(self.state, p)
            result, _ = ex.execute_compilation(self.state, p, out_dir=d)
            self.assertTrue(result.ok, result.problems)
            for path in result.exports["step_per_body"].values():
                self.assertTrue(os.path.isfile(path))
            for delta in result.roundtrip["brep"].values():
                self.assertLessEqual(delta, compiler.BREP_VOLUME_TOLERANCE)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
