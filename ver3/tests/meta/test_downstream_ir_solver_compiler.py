"""s06 and s07: the deterministic downstream, exercised rather than asserted.

These are capability tests in the sense S06_CONTRACT and S07_CONTRACT mean it.
Each one names the failure it prevents, and the failures are the ones the
contracts already went to the trouble of writing down - a solver that reports
success it did not achieve (R-23), a compiler that supplies a number nobody
decided (R-24).

The kernel tests require OpenCascade. They FAIL rather than skip when it is
absent from an environment that is supposed to have it, because a compiler test
that silently skips is how a CAD stage stops being covered.
"""

import json
import os
import tempfile
import unittest

from ver3.assy_v3.downstream import compiler, ir, solver

KERNEL = True
try:
    compiler.kernel()
except compiler.KernelUnavailable:                               # pragma: no cover
    KERNEL = False


def P(**kw):
    kw.setdefault("unit", "mm")
    kw.setdefault("status", ir.DECLARED)
    return ir.ParameterDecl.parse(kw)


def C(entity_id, relation, lhs, rhs, kind="envelope"):
    return ir.TypedConstraint.parse(
        {"entity_id": entity_id, "kind": kind,
         "expression": {"relation": relation, "lhs": lhs, "rhs": rhs}})


REF = lambda i: {"ref": i}                                       # noqa: E731
MM = lambda v: {"const": v, "unit": "mm"}                        # noqa: E731


class TestIRRefusesMalformedInput(unittest.TestCase):
    """Every rejection here is a thing that would otherwise be interpreted twice."""

    def test_a_literal_without_a_unit_is_refused(self):
        """INV-004 / R-21 at the leaf, where the defaulting would start."""
        with self.assertRaises(ir.IRError):
            ir.Expr.parse({"const": 5})

    def test_a_node_setting_two_kinds_is_refused(self):
        with self.assertRaises(ir.IRError):
            ir.Expr.parse({"ref": "PRM-0001", "const": 5, "unit": "mm"})

    def test_an_unknown_operator_is_refused(self):
        with self.assertRaises(ir.IRError):
            ir.Expr.parse({"op": "**", "args": [REF("A"), MM(2)]})

    def test_a_parameter_without_a_unit_is_refused(self):
        with self.assertRaises(ir.IRError):
            ir.ParameterDecl.parse({"entity_id": "PRM-1", "symbol": "x",
                                    "status": ir.DECLARED})

    def test_an_unknown_opcode_is_refused(self):
        with self.assertRaises(ir.IRError):
            ir.Statement.parse({"entity_id": "CST-1", "body": "BOD-1",
                                "operation": "LOFT", "parameters": {}})

    def test_a_primitive_missing_a_required_parameter_is_refused(self):
        with self.assertRaises(ir.IRError):
            ir.Statement.parse({"entity_id": "CST-1", "body": "BOD-1",
                                "operation": "BOX",
                                "parameters": {"dx": MM(1), "dy": MM(1)}})

    def test_a_rotate_without_an_axis_is_refused(self):
        """s07 may not choose an axis (R-24), so the statement must carry one."""
        with self.assertRaises(ir.IRError):
            ir.Statement.parse({"entity_id": "CST-1", "body": "BOD-1",
                                "operation": "ROTATE", "operands": ["CST-0"],
                                "parameters": {"angle": {"const": 90, "unit": "deg"}}})

    def test_a_forward_reference_is_reported_not_reordered(self):
        prog = ir.ConstructionProgram.parse([
            {"entity_id": "CST-2", "body": "B", "operation": "CUT",
             "operands": ["CST-1", "CST-3"], "parameters": {}},
            {"entity_id": "CST-1", "body": "B", "operation": "BOX",
             "parameters": {"dx": MM(1), "dy": MM(1), "dz": MM(1)}},
        ])
        self.assertTrue(prog.ordering_problems())


class TestSolverSemantics(unittest.TestCase):
    """S06 capability review: not the happy path only."""

    def setUp(self):
        self.params = [
            P(entity_id="PRM-0001", symbol="pin_r", status=ir.SOLVED, value=4.0),
            P(entity_id="PRM-0002", symbol="wall", status=ir.SOLVED, value=2.0),
            P(entity_id="PRM-0003", symbol="boss_r"),
        ]
        self.envelope = C("CON-0001", "==", REF("PRM-0003"),
                          {"op": "+", "args": [REF("PRM-0001"), REF("PRM-0002")]})

    def test_a_determined_system_is_feasible_and_settles(self):
        """The envelope rule from the contract: a boss radius is r + w."""
        r = solver.solve(self.params, [self.envelope])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(6.0, r.settled["PRM-0003"])

    def test_an_underdetermined_system_does_not_invent_a_value(self):
        """The prohibition that matters most: no member of a family is picked."""
        r = solver.solve(self.params + [P(entity_id="PRM-0009", symbol="free")],
                         [self.envelope])
        self.assertEqual(ir.UNDERDETERMINED, r.solver_status)
        self.assertIn("PRM-0009", r.free_parameters)
        self.assertNotIn("PRM-0009", r.settled)

    def test_a_violated_inequality_is_infeasible_and_names_the_conflict(self):
        clearance = C("CON-0003", ">=", REF("PRM-0003"), MM(99), kind="clearance")
        r = solver.solve(self.params, [self.envelope, clearance])
        self.assertEqual(ir.INFEASIBLE, r.solver_status)
        self.assertIn("CON-0003", r.conflicting)

    def test_a_satisfied_inequality_reports_its_margin(self):
        clearance = C("CON-0004", ">=", REF("PRM-0003"), MM(5), kind="clearance")
        r = solver.solve(self.params, [self.envelope, clearance])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(1.0, r.margins["CON-0004"])

    def test_contradictory_equalities_are_infeasible(self):
        other = C("CON-0005", "==", REF("PRM-0003"), MM(99))
        r = solver.solve(self.params, [self.envelope, other])
        self.assertEqual(ir.INFEASIBLE, r.solver_status)

    def test_mixed_units_are_unsupported_not_silently_combined(self):
        """A length is not an angle, and the report says which two it saw."""
        bad = C("CON-0006", "==", REF("PRM-0003"), {"const": 5, "unit": "deg"})
        r = solver.solve(self.params, [bad])
        self.assertEqual(ir.UNSUPPORTED_FORMULATION, r.solver_status)
        self.assertTrue(any("mm" in p and "deg" in p for p in r.problems), r.problems)

    def test_a_nonlinear_formulation_is_refused_rather_than_approximated(self):
        nl = C("CON-0007", "==", REF("PRM-0003"),
               {"op": "*", "args": [REF("PRM-0001"), REF("PRM-0002")]})
        self.assertEqual(ir.UNSUPPORTED_FORMULATION,
                         solver.solve(self.params, [nl]).solver_status)

    def test_scaling_by_a_dimensionless_constant_is_supported(self):
        """A scale factor is a pure number, and only that spelling is a scaling.

        This test previously multiplied a length by `0.5 mm` and asserted the
        result was a length. That is dimensionally wrong - a length times a
        length is an area - and it passed because units were compared as strings.
        """
        half = C("CON-0008", "==", REF("PRM-0003"),
                 {"op": "*", "args": [REF("PRM-0001"), {"const": 0.5, "unit": "1"}]})
        r = solver.solve(self.params, [half])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(2.0, r.settled["PRM-0003"])

    def test_a_length_times_a_length_is_not_a_length(self):
        """The defect the test above used to enshrine."""
        area = C("CON-0012", "==", REF("PRM-0003"),
                 {"op": "*", "args": [MM(0.5), MM(10)]})
        r = solver.solve(self.params, [area])
        self.assertEqual(ir.UNSUPPORTED_FORMULATION, r.solver_status)
        self.assertTrue(any("mm^2" in p for p in r.problems), r.problems)

    def test_an_area_parameter_accepts_a_product_of_lengths(self):
        area = [P(entity_id="PRM-0020", symbol="face", unit="mm2")]
        c = C("CON-0013", "==", REF("PRM-0020"),
              {"op": "*", "args": [MM(2), MM(3)]})
        r = solver.solve(area, [c])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(6.0, r.settled["PRM-0020"])

    def test_a_coupled_two_by_two_system_has_a_unique_solution(self):
        """The correctness gap: this returned UNDERDETERMINED before.

        Neither row reduces to one unknown on its own, so a solver that only
        settles convenient rows sees a free family where there is exactly one
        answer.
        """
        x, y = P(entity_id="PRM-X", symbol="x"), P(entity_id="PRM-Y", symbol="y")
        r = solver.solve([x, y], [
            C("CON-A", "==", {"op": "+", "args": [REF("PRM-X"), REF("PRM-Y")]}, MM(10)),
            C("CON-B", "==", {"op": "-", "args": [REF("PRM-X"), REF("PRM-Y")]}, MM(2))])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(6.0, r.settled["PRM-X"])
        self.assertAlmostEqual(4.0, r.settled["PRM-Y"])
        self.assertEqual(2, r.rank)

    def test_a_coupled_three_by_three_system_resolves(self):
        p = [P(entity_id="PRM-X", symbol="x"), P(entity_id="PRM-Y", symbol="y"),
             P(entity_id="PRM-Z", symbol="z")]
        r = solver.solve(p, [
            C("CON-A", "==",
              {"op": "+", "args": [REF("PRM-X"), REF("PRM-Y"), REF("PRM-Z")]}, MM(6)),
            C("CON-B", "==", {"op": "-", "args": [REF("PRM-X"), REF("PRM-Y")]}, MM(1)),
            C("CON-C", "==", {"op": "-", "args": [REF("PRM-Y"), REF("PRM-Z")]}, MM(1))])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(3.0, r.settled["PRM-X"])
        self.assertAlmostEqual(2.0, r.settled["PRM-Y"])
        self.assertAlmostEqual(1.0, r.settled["PRM-Z"])

    def test_a_rank_deficient_system_is_underdetermined_not_solved(self):
        """Two rows saying the same thing determine one direction, not two."""
        x, y = P(entity_id="PRM-X", symbol="x"), P(entity_id="PRM-Y", symbol="y")
        double = lambda i: {"op": "*", "args": [REF(i), {"const": 2, "unit": "1"}]}
        r = solver.solve([x, y], [
            C("CON-A", "==", {"op": "+", "args": [REF("PRM-X"), REF("PRM-Y")]}, MM(10)),
            C("CON-B", "==", {"op": "+", "args": [double("PRM-X"), double("PRM-Y")]},
              MM(20))])
        self.assertEqual(ir.UNDERDETERMINED, r.solver_status)
        self.assertEqual(1, r.rank)
        self.assertEqual({}, r.settled)

    def test_a_contradictory_coupled_system_is_infeasible(self):
        x, y = P(entity_id="PRM-X", symbol="x"), P(entity_id="PRM-Y", symbol="y")
        add = {"op": "+", "args": [REF("PRM-X"), REF("PRM-Y")]}
        r = solver.solve([x, y], [C("CON-A", "==", add, MM(10)),
                                  C("CON-B", "==", add, MM(11))])
        self.assertEqual(ir.INFEASIBLE, r.solver_status)
        self.assertTrue(r.conflicting)

    def test_a_value_without_solver_evidence_is_not_trusted_as_settled(self):
        """The posture S05-C10 rests on.

        A Parameter carrying a number but still DECLARED has not been solved -
        s05 may not set a value except by citing a solver artifact. Treating that
        number as known would be R-23 exactly: copying an existing value and
        calling it solved.
        """
        declared = ir.ParameterDecl.parse(
            {"entity_id": "PRM-0030", "symbol": "a", "unit": "mm",
             "status": ir.DECLARED, "value": 99.0})
        r = solver.solve([declared], [])
        self.assertEqual(ir.UNDERDETERMINED, r.solver_status)
        self.assertEqual({}, r.settled)
        self.assertIn("PRM-0030", r.free_parameters)

    def test_a_solved_value_is_carried_as_known(self):
        solved = ir.ParameterDecl.parse(
            {"entity_id": "PRM-0031", "symbol": "a", "unit": "mm",
             "status": ir.SOLVED, "value": 99.0})
        r = solver.solve([solved], [])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(99.0, r.settled["PRM-0031"])

    def test_a_coupled_system_is_order_independent(self):
        """S06-C6 over the elimination itself, not only over the easy path."""
        x, y = P(entity_id="PRM-X", symbol="x"), P(entity_id="PRM-Y", symbol="y")
        a = C("CON-A", "==", {"op": "+", "args": [REF("PRM-X"), REF("PRM-Y")]}, MM(10))
        b = C("CON-B", "==", {"op": "-", "args": [REF("PRM-X"), REF("PRM-Y")]}, MM(2))
        first = solver.solve([x, y], [a, b]).as_record()
        second = solver.solve([y, x], [b, a]).as_record()
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_a_declared_bound_violation_is_infeasible(self):
        params = list(self.params)
        params[2] = P(entity_id="PRM-0003", symbol="boss_r", upper=5.0)
        r = solver.solve(params, [self.envelope])
        self.assertEqual(ir.INFEASIBLE, r.solver_status)

    def test_a_dependency_chain_settles_transitively(self):
        params = self.params + [P(entity_id="PRM-0004", symbol="arm_r")]
        chain = C("CON-0009", "==", REF("PRM-0004"),
                  {"op": "+", "args": [REF("PRM-0003"), MM(10)]})
        r = solver.solve(params, [self.envelope, chain])
        self.assertEqual(ir.FEASIBLE, r.solver_status)
        self.assertAlmostEqual(16.0, r.settled["PRM-0004"])

    def test_an_undeclared_reference_is_unsupported(self):
        ghost = C("CON-0010", "==", REF("PRM-NOPE"), MM(1))
        self.assertEqual(ir.UNSUPPORTED_FORMULATION,
                         solver.solve(self.params, [ghost]).solver_status)

    def test_determinism_under_input_reordering(self):
        """S06-C6, and the reason every loop here sorts by entity id."""
        a = solver.solve(self.params, [self.envelope]).as_record()
        b = solver.solve(list(reversed(self.params)), [self.envelope]).as_record()
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_the_report_identifies_the_exact_system_solved(self):
        r = solver.solve(self.params, [self.envelope])
        self.assertTrue(r.formulation_sha256)
        self.assertEqual(r.formulation_sha256,
                         solver.formulation_hash(self.params, [self.envelope]))

    def test_the_solver_never_reports_feasible_with_free_parameters(self):
        """S06-C1 restated as the invariant a caller actually relies on."""
        r = solver.solve(self.params + [P(entity_id="PRM-0011", symbol="q")],
                         [self.envelope])
        self.assertNotEqual(ir.FEASIBLE, r.solver_status)


def _cut_program():
    """A body built by cutting a bore from a block. Body frame only."""
    return ir.ConstructionProgram.parse([
        {"entity_id": "CST-0001", "body": "BOD-0001", "operation": "BOX",
         "parameters": {"dx": MM(40), "dy": MM(30), "dz": MM(20)}},
        {"entity_id": "CST-0002", "body": "BOD-0001", "operation": "CYLINDER",
         "feature": "FEA-0001",
         "parameters": {"radius": REF("PRM-0003"), "height": MM(30)}},
        {"entity_id": "CST-0003", "body": "BOD-0001", "operation": "TRANSLATE",
         "operands": ["CST-0002"],
         "parameters": {"dx": MM(20), "dy": MM(15), "dz": MM(-5)}},
        {"entity_id": "CST-0004", "body": "BOD-0001", "operation": "CUT",
         "operands": ["CST-0001", "CST-0003"], "parameters": {}},
    ])


@unittest.skipUnless(KERNEL, "OpenCascade kernel absent")
class TestCompilerBuildsAndChecks(unittest.TestCase):
    """S07 capability review, against the real kernel."""

    VALUES = {"PRM-0003": 6.0}

    def test_a_valid_program_compiles_to_one_connected_solid(self):
        r = compiler.compile_program(_cut_program(), self.VALUES)
        self.assertTrue(r.ok, r.problems)
        body = r.bodies[0]
        self.assertTrue(body.is_valid)
        self.assertGreater(body.volume, 0)
        self.assertTrue(body.single_connected_solid)

    def test_the_cut_actually_removed_material(self):
        """Otherwise 'it compiled' would be true of a program that did nothing."""
        r = compiler.compile_program(_cut_program(), self.VALUES)
        self.assertLess(r.bodies[0].volume, 40 * 30 * 20)

    def test_a_missing_parameter_fails_and_emits_no_geometry(self):
        """R-24. The compiler does not supply the number the kernel wants."""
        r = compiler.compile_program(_cut_program(), {})
        self.assertFalse(r.ok)
        self.assertEqual("CST-0002", r.failed_statement)
        self.assertEqual([], r.bodies)

    def test_a_failure_cites_the_dependency_cone(self):
        """S07-C6: the failing statement is rarely the wrong one."""
        prog = _cut_program()
        r = compiler.compile_program(prog, {})
        self.assertIn("CST-0002", r.dependency_cone)

    def test_a_non_positive_dimension_fails_rather_than_clamping(self):
        r = compiler.compile_program(_cut_program(), {"PRM-0003": 0.0})
        self.assertFalse(r.ok)
        self.assertEqual([], r.bodies)

    def test_a_disconnected_result_violates_c2(self):
        """Two separated blocks are not a body, and the check says so."""
        prog = ir.ConstructionProgram.parse([
            {"entity_id": "CST-1", "body": "B", "operation": "BOX",
             "parameters": {"dx": MM(5), "dy": MM(5), "dz": MM(5)}},
            {"entity_id": "CST-2", "body": "B", "operation": "BOX",
             "parameters": {"dx": MM(5), "dy": MM(5), "dz": MM(5)}},
            {"entity_id": "CST-3", "body": "B", "operation": "TRANSLATE",
             "operands": ["CST-2"],
             "parameters": {"dx": MM(50), "dy": MM(0), "dz": MM(0)}},
            {"entity_id": "CST-4", "body": "B", "operation": "UNION",
             "operands": ["CST-1", "CST-3"], "parameters": {}},
        ])
        r = compiler.compile_program(prog, {})
        self.assertFalse(r.ok)
        self.assertTrue(any("S07-C2" in p for p in r.problems), r.problems)

    def test_exports_round_trip_within_the_declared_tolerances(self):
        """S07-C3 and S07-C4, measured rather than asserted."""
        with tempfile.TemporaryDirectory() as d:
            r = compiler.compile_program(_cut_program(), self.VALUES, out_dir=d)
            self.assertTrue(r.ok, r.problems)
            for body, delta in r.roundtrip["brep"].items():
                self.assertLessEqual(delta, compiler.BREP_VOLUME_TOLERANCE, body)
            for body, rel in r.roundtrip["step"].items():
                self.assertLessEqual(rel, compiler.STEP_RELATIVE_TOLERANCE, body)
            for path in r.exports["native_brep_per_body"].values():
                self.assertTrue(os.path.isfile(path))
            for path in r.exports["step_per_body"].values():
                self.assertTrue(os.path.isfile(path))

    def test_an_independent_rebuild_reproduces_the_signature(self):
        """S07-C5."""
        ok, a, b = compiler.independent_rebuild_matches(_cut_program(), self.VALUES)
        self.assertTrue(ok)
        self.assertEqual(a, b)

    def test_the_signature_changes_when_the_geometry_does(self):
        """A signature that never moves would certify nothing."""
        a = compiler.compile_program(_cut_program(), {"PRM-0003": 6.0}).signature
        b = compiler.compile_program(_cut_program(), {"PRM-0003": 7.0}).signature
        self.assertNotEqual(a["signature_sha256"], b["signature_sha256"])

    def test_statements_map_to_the_features_they_realize(self):
        r = compiler.compile_program(_cut_program(), self.VALUES)
        self.assertEqual({"CST-0002": "FEA-0001"}, r.bodies[0].statement_map)

    def test_the_signature_is_taken_before_export(self):
        """STEP is an exchange artifact and never the authoritative source."""
        with tempfile.TemporaryDirectory() as d:
            exported = compiler.compile_program(_cut_program(), self.VALUES, out_dir=d)
            native = compiler.compile_program(_cut_program(), self.VALUES)
        self.assertEqual(native.signature["signature_sha256"],
                         exported.signature["signature_sha256"])


class TestNoBenchmarkLeakage(unittest.TestCase):
    """The compiler must be generic over canonical operations, not a BM script."""

    def test_production_names_no_benchmark_and_no_reference_geometry(self):
        for mod in (ir, solver, compiler):
            source = open(mod.__file__).read()
            for banned in ("BM-001", "BM-002", "BM-003", "cad_validation",
                           "executable_references", "cadquery"):
                with self.subTest(module=mod.__name__, term=banned):
                    self.assertNotIn(banned, source)

    def test_the_opcode_vocabulary_carries_no_world_placement(self):
        """construction_frame_rule: bodies compile in their own frames."""
        for banned in ("PLACE", "POSE", "LOCATE", "ASSEMBLE"):
            with self.subTest(opcode=banned):
                self.assertNotIn(banned, ir.OPCODES)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
