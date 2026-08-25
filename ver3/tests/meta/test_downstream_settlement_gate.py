"""UNIT F. Symbolic embodiment -> deterministic settlement -> CAD compilation.

The seam these tests guard: what s05 writes must be READABLE by s06 and s07
before it stands (one grammar, at the write boundary); a settled value must not
stale the symbolic definition it settles, while a revised declaration must; s06
may be asked only FOR an embodiment, and never reports the absence of one as an
empty problem that solved; s07 is entered only over a settled, non-empty,
kernel-unit program with no standing occupancy finding, and the geometry it
signs carries what it was concluded from.

Kernel-free: every refusal here happens before the kernel would be asked. The
compile-dependent claims live in tests/kernel/test_settlement_gate_geometry.py.
"""

import unittest

from ver3.assy_v3.downstream import (canonical_io, compiler, execution as ex, ir,
                                     settled_geometry, solver)
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.stages import s05_embodiment as s05
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

import os
import yaml
import ver3

CONTRACTS = os.path.join(os.path.dirname(ver3.__file__), "contracts")


MM = lambda v: {"const": v, "unit": "mm"}                        # noqa: E731
REF = lambda i: {"ref": i}                                       # noqa: E731


def apply(state, stage, ops, attempt=1):
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


def body(bid="BOD-0001", premises=()):
    return Op("CREATE", "Body", bid,
              {"instance_identity": bid, "role": "shell", "created_by_stage": "s03"},
              "s03:topology", premise_refs=list(premises))


def param(pid, symbol="w", unit="mm", **extra):
    fields = {"symbol": symbol, "unit": unit, "status": ir.DECLARED}
    fields.update(extra)
    return Op("CREATE", "Parameter", pid, fields, "s05:embodiment")


def equals(cid, lhs, rhs, params, relation="=="):
    return Op("CREATE", "Constraint", cid,
              {"kind": "DIMENSIONAL", "parameters": list(params),
               "expression": {"relation": relation, "lhs": lhs, "rhs": rhs}},
              "s05:embodiment", premise_refs=list(params))


def box(sid, dx, bid="BOD-0001", premises=(), **more):
    fields = {"body": bid, "operation": "BOX", "operands": [],
              "parameters": {"dx": dx, "dy": MM(10), "dz": MM(4)}}
    fields.update(more)
    return Op("CREATE", "ConstructionStatement", sid, fields, "s05:embodiment",
              premise_refs=[bid] + list(premises))


def feature(fid, envelope, premises=(), bid="BOD-0001"):
    return Op("CREATE", "Feature", fid,
              {"body": bid, "feature_kind": "STOP", "geometry": "the stop face",
               "envelope": envelope},
              "s05:embodiment", premise_refs=[bid] + list(premises))


SYMBOLIC = {"centre": [MM(0), MM(0), MM(0)],
            "half_extent": [REF("PRM-W"), REF("PRM-W"), REF("PRM-W")]}


class _Embodied(unittest.TestCase):
    """One body; one parameter settled by one constraint; a feature stated in
    it; a program that builds it. The minimum embodiment, well-formed."""

    def setUp(self):
        self.state = DesignState(run_id="gate")
        self.assertEqual([], apply(self.state, "s03", [body()]))
        self.assertEqual([], apply(self.state, "s05", [
            param("PRM-W"),
            equals("CON-W", REF("PRM-W"), MM(12), ["PRM-W"]),
            feature("FEA-1", SYMBOLIC, premises=["PRM-W"]),
            box("CST-1", REF("PRM-W"), premises=["PRM-W"])]))

    def validity(self, eid):
        return self.state.entities[eid].get("_validity", "STANDING")

    def settle(self):
        report, execution = ex.execute_settlement(self.state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status, report.problems)
        return report, execution


# =====================================================================
# F1 / F2 - one grammar, applied at the door
# =====================================================================
class TestOneGrammarAtTheBoundary(_Embodied):

    def test_01_the_ir_is_the_single_grammar_authority(self):
        fams = Contracts().families
        for family, kind in (("Parameter", "parameter"), ("Constraint", "constraint"),
                             ("ConstructionStatement", "statement"), ("Feature", "envelope")):
            with self.subTest(family=family):
                self.assertEqual(kind, fams[family].get("ir_validation"))
                self.assertIn(kind, ir.IR_VALIDATION_KINDS)
        # s05's envelope reading IS the IR's, renamed for the finding it raises
        bad = {"centre": [0, MM(0), MM(0)], "half_extent": [REF("PRM-X")] * 3}
        _e, from_ir = ir.envelope_problems("FEA-9", bad, set())
        _e, from_s05 = s05.envelope_expressions("FEA-9", bad, set())
        self.assertEqual([p.replace("IR: ", "S05-C8: ") for p in from_ir], from_s05)
        # and the solver's status vocabulary is the contract's, not_ready included
        with open(os.path.join(CONTRACTS, "stages", "S06_CONTRACT.yaml")) as fh:
            s06c = yaml.safe_load(fh)
        self.assertEqual(list(ir.SOLVER_STATUSES),
                         s06c["structured_outputs"]["solver_status"])

    def test_02_an_invalid_relation_is_refused_before_standing(self):
        problems = apply(self.state, "s05", [
            param("PRM-2"), equals("CON-2", REF("PRM-2"), MM(1), ["PRM-2"], relation=">")])
        self.assertTrue(any("relation" in p and "IR:" in p for p in problems), problems)
        self.assertNotIn("CON-2", self.state.entities)

    def test_03_a_malformed_expression_node_is_refused(self):
        for lhs in (5, {"ref": "PRM-W", "const": 1, "unit": "mm"}, {"op": "%", "args": []},
                    {"const": 1}):
            with self.subTest(lhs=lhs):
                problems = apply(self.state, "s05", [
                    equals("CON-3", lhs, MM(1), ["PRM-W"])])
                self.assertTrue(any(p.startswith("IR:") for p in problems), problems)
        self.assertNotIn("CON-3", self.state.entities)

    def test_04_typed_physical_constants_parse_and_untyped_ones_do_not(self):
        expr = ir.Expr.parse(MM(2.5))
        self.assertEqual((2.5, "mm"), (expr.const, expr.unit))
        with self.assertRaises(ir.IRError):
            ir.Expr.parse({"const": 2.5})

    def test_05_symbolic_parameter_references_parse(self):
        expr = ir.Expr.parse({"op": "+", "args": [REF("PRM-W"), MM(1)]})
        self.assertEqual({"PRM-W"}, expr.refs())
        self.assertEqual({"PRM-W"}, ir.Expr.parse(REF("PRM-W")).refs())

    def test_06_a_dangling_reference_is_rejected_and_a_same_patch_one_resolves(self):
        problems = apply(self.state, "s05", [
            equals("CON-6", REF("PRM-9"), MM(1), ["PRM-9"])])
        self.assertTrue(any("PRM-9" in p and "no standing Parameter" in p
                            for p in problems), problems)
        self.assertEqual([], apply(self.state, "s05", [
            param("PRM-9"), equals("CON-6", REF("PRM-9"), MM(1), ["PRM-9"])]))

    def test_07_a_frame_origin_zero_is_representable_and_a_bare_zero_is_not(self):
        """The distinction is semantic, not lexical: `0 mm` at the origin is a
        coordinate; a bare 0 is a dimension somebody invented."""
        self.assertEqual([], apply(self.state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-7",
               {"body": "BOD-0001", "operation": "TRANSLATE", "operands": ["CST-1"],
                "parameters": {"dx": MM(0), "dy": MM(0), "dz": MM(0)}},
               "s05:embodiment", premise_refs=["BOD-0001", "CST-1"])]))
        problems = apply(self.state, "s05", [
            feature("FEA-7", {"centre": [0, 0, 0], "half_extent": [REF("PRM-W")] * 3})])
        self.assertTrue(any("bare number" in p for p in problems), problems)
        self.assertIn("frame origin", ir.OPCODE_SEMANTICS["TRANSLATE"] + ir.OPCODE_SEMANTICS["BOX"])

    def test_08_s05_does_not_author_a_parameter_value(self):
        problems = apply(self.state, "s05", [param("PRM-8", value=3.0)])
        self.assertTrue(any("solver artifact" in p for p in problems), problems)
        problems = apply(self.state, "s05", [
            Op("EXTEND", "Parameter", "PRM-W", {"value": 3.0}, "s05:embodiment")])
        self.assertTrue(any("EXTEND_WRONG_STAGE" in p for p in problems), problems)

    def test_09_an_unknown_opcode_or_a_missing_argument_is_refused(self):
        problems = apply(self.state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-9",
               {"body": "BOD-0001", "operation": "TORUS", "operands": [],
                "parameters": {"radius": MM(1)}}, "s05:embodiment")])
        self.assertTrue(any(p.startswith("IR:") for p in problems), problems)
        problems = apply(self.state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-9",
               {"body": "BOD-0001", "operation": "BOX", "operands": [],
                "parameters": {"dx": MM(1), "dy": MM(1)}}, "s05:embodiment")])
        self.assertTrue(any(p.startswith("IR:") for p in problems), problems)
        self.assertNotIn("CST-9", self.state.entities)

    def test_31_a_list_shaped_parameters_field_is_refused_by_name_not_by_a_crash(self):
        """Observed live: a model wrote a statement's parameters positionally.
        The IR names the defect; s05's own operation builder must not be the
        place such a response dies."""
        problems = apply(self.state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-31",
               {"body": "BOD-0001", "operation": "BOX", "operands": [],
                "parameters": [MM(6), MM(4), MM(4)]}, "s05:embodiment")])
        self.assertTrue(any("parameters is not an object" in p for p in problems), problems)
        response = {"features": [], "realizations": [], "parameters": [], "constraints": [],
                    "construction_statements": [
                        {"id": "CST-31", "body": "BOD-0001", "operation": "BOX",
                         "operands": [], "parameters": [MM(6), MM(4), MM(4)]}]}
        ops = s05.S05Embodiment().to_operations(response)
        self.assertEqual(["CST-31"], [op.entity_id for op in ops])
        findings = s05.check_c5_program_totality(response)
        self.assertTrue(any("CST-31" in f and "not an object" in f for f in findings), findings)

    def test_10_an_operand_that_names_no_statement_is_refused(self):
        problems = apply(self.state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-10",
               {"body": "BOD-0001", "operation": "CUT", "operands": ["CST-1", "CST-99"],
                "parameters": {}}, "s05:embodiment")])
        self.assertTrue(any("CST-99" in p and "no standing ConstructionStatement" in p
                            for p in problems), problems)


# =====================================================================
# F3 / F5 - settlement and currentness
# =====================================================================
class TestSettlementAndCurrentness(_Embodied):

    def test_11_settlement_is_deterministic(self):
        a, _ = canonical_io.solve_from_state(self.state)
        other = _Embodied("setUp")
        other.setUp()
        b, _ = canonical_io.solve_from_state(other.state)
        self.assertEqual(a.formulation_sha256, b.formulation_sha256)
        self.assertEqual(a.settled, b.settled)
        self.assertEqual(canonical_io.evidence_identity(a), canonical_io.evidence_identity(b))

    def test_12_settlement_does_not_stale_the_symbolic_definition(self):
        self.settle()
        self.assertAlmostEqual(12.0, self.state.entities["PRM-W"]["value"])
        for eid in ("PRM-W", "CON-W", "FEA-1", "CST-1"):
            with self.subTest(entity=eid):
                self.assertEqual("STANDING", self.validity(eid))

    def test_13_a_declaration_revision_stales_its_dependents(self):
        self.settle()
        self.assertEqual([], apply(self.state, "s05", [
            Op("SUPERSEDE", "Parameter", "PRM-W", {"unit": "cm"}, "s05:embodiment",
               reason="the quantity is restated")]))
        for eid in ("CON-W", "FEA-1", "CST-1"):
            with self.subTest(entity=eid):
                self.assertEqual("STALE", self.validity(eid))

    def test_14_a_constraint_revision_stales_the_settled_value(self):
        """The value rested on the constraint; the revised constraint still
        resolves to the declared parameter (a stale declaration is not a
        withdrawn one), which is what lets it be re-settled at all."""
        self.settle()
        self.assertEqual([], apply(self.state, "s05", [
            Op("SUPERSEDE", "Constraint", "CON-W",
               {"expression": {"relation": "==", "lhs": REF("PRM-W"), "rhs": MM(15)}},
               "s05:embodiment", reason="the width is enlarged")]))
        self.assertEqual("STALE", self.validity("PRM-W"))
        self.assertEqual("STANDING", self.validity("CON-W"))

    def test_15_settlement_evidence_is_recorded_with_the_value(self):
        report, execution = self.settle()
        rec = self.state.entities["PRM-W"]
        self.assertEqual(canonical_io.evidence_identity(report), rec["solved_by"])
        self.assertEqual(execution.evidence_id, rec["solved_by"])
        self.assertEqual(ir.FEASIBLE,
                         self.state.entities["CON-W"]["settlement"]["solver_status"])
        self.assertIn("CON-W", rec["_premises"], "the value does not cite what settled it")


# =====================================================================
# F4 - the s06 entry gate
# =====================================================================
class TestSettlementEntryGate(unittest.TestCase):

    def test_16_a_missing_s05_program_is_not_ready(self):
        state = DesignState(run_id="noprog")
        apply(state, "s03", [body()])
        p = Progression()
        report, execution = ex.execute_settlement(state, p)
        self.assertEqual(ir.NOT_READY, report.solver_status)
        self.assertEqual(ir.NOT_READY, execution.outcome)
        self.assertFalse(execution.patch_applied)
        self.assertTrue(any("no current construction program" in x for x in report.problems),
                        report.problems)
        self.assertEqual({}, report.settled)

    def test_17_an_empty_solve_cannot_stand_in_for_a_missing_embodiment(self):
        """The solver core answers an empty system honestly - feasible, no
        unknowns - and that is exactly why the gate, not the solver, decides
        whether there was anything to ask."""
        core = solver.solve([], [])
        self.assertEqual((ir.FEASIBLE, 0), (core.solver_status, core.unknown_count))
        state = DesignState(run_id="noprog2")
        apply(state, "s03", [body()])
        apply(state, "s05", [param("PRM-L")])
        outcome = ex.settle(state, Progression())
        self.assertEqual(ex.NOT_READY, outcome.status)
        self.assertEqual(1, outcome.rounds)
        self.assertIsNone(state.entities["PRM-L"].get("value"))

    def test_18_a_legitimate_empty_settlement_is_explicit(self):
        state = DesignState(run_id="constants")
        apply(state, "s03", [body()])
        self.assertEqual([], apply(state, "s05", [box("CST-K", MM(30))]))
        ready, why = canonical_io.settlement_readiness(state)
        self.assertTrue(ready, why)
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status)
        self.assertEqual(0, report.unknown_count)
        self.assertNotEqual(ir.NOT_READY, report.solver_status)

    def test_19_a_withdrawn_program_is_not_ready(self):
        t = _Embodied("setUp")
        t.setUp()
        self.assertEqual([], apply(t.state, "s05", [
            Op("INVALIDATE", "ConstructionStatement", "CST-1", {}, "s05:embodiment",
               reason="withdrawn")]))
        report, execution = ex.execute_settlement(t.state, Progression())
        self.assertEqual(ir.NOT_READY, report.solver_status)
        self.assertFalse(execution.patch_applied)


# =====================================================================
# F5 - s06 does not design
# =====================================================================
class TestS06DoesNotDesign(_Embodied):

    def test_20_s06_cannot_alter_principle_architecture_or_feature_strategy(self):
        self.assertEqual([], apply(self.state, "s02", [
            Op("CREATE", "Candidate", "CND-A",
               {"summary": "a", "family": "ACTUATE", "principle": {"ACTUATE": "DIRECT"},
                "addresses_obligations": [], "obligations_created": [],
                "evidence_route_verdict": {"route": "MOBILITY_ANALYSIS", "available": True}},
               "s02:derivation")]))
        S06 = "s06:settlement"
        attempts = {
            "principle": Op("SUPERSEDE", "Candidate", "CND-A",
                            {"principle": {"ACTUATE": "STORED_ENERGY"}}, S06, reason="x"),
            "topology": Op("CREATE", "Body", "BOD-9", {"instance_identity": "BOD-9",
                           "role": "shell", "created_by_stage": "s03"}, S06),
            "feature": Op("CREATE", "Feature", "FEA-9", {"body": "BOD-0001",
                          "feature_kind": "STOP", "geometry": "x"}, S06),
            "construction": Op("CREATE", "ConstructionStatement", "CST-9",
                               {"body": "BOD-0001", "operation": "BOX", "operands": [],
                                "parameters": {"dx": MM(1), "dy": MM(1), "dz": MM(1)}}, S06),
            "constraint": Op("CREATE", "Constraint", "CON-9",
                             {"kind": "DIMENSIONAL", "parameters": ["PRM-W"],
                              "expression": {"relation": "==", "lhs": REF("PRM-W"),
                                             "rhs": MM(1)}}, S06),
            "declaration": Op("SUPERSEDE", "Parameter", "PRM-W", {"unit": "cm"}, S06,
                              reason="x"),
        }
        for name, op in attempts.items():
            with self.subTest(decision=name):
                problems = apply(self.state, "s06", [op])
                self.assertTrue(problems, "s06 was allowed to decide %s" % name)
        self.assertEqual({"ACTUATE": "DIRECT"}, self.state.entities["CND-A"]["principle"])
        self.assertEqual("mm", self.state.entities["PRM-W"]["unit"])


# =====================================================================
# F6 / F8 - units, bases, post-settlement s04 commitments
# =====================================================================
class TestUnitsAndBases(_Embodied):

    def test_21_units_are_explicit(self):
        problems = apply(self.state, "s05", [param("PRM-21", unit="")])
        self.assertTrue(any("declares no unit" in p for p in problems), problems)
        problems = apply(self.state, "s05", [
            equals("CON-21", REF("PRM-W"), {"const": 1}, ["PRM-W"])])
        self.assertTrue(any(p.startswith("IR:") for p in problems), problems)

    def test_22_a_length_in_the_wrong_unit_is_refused_before_the_kernel(self):
        state = DesignState(run_id="metres")
        apply(state, "s03", [body()])
        self.assertEqual([], apply(state, "s05", [
            param("PRM-M", unit="m"),
            Op("CREATE", "Constraint", "CON-M",
               {"kind": "DIMENSIONAL", "parameters": ["PRM-M"],
                "expression": {"relation": "==", "lhs": REF("PRM-M"),
                               "rhs": {"const": 0.05, "unit": "m"}}},
               "s05:embodiment", premise_refs=["PRM-M"]),
            box("CST-M", REF("PRM-M"), premises=["PRM-M"])]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status, report.problems)
        problems = canonical_io.program_unit_problems(state)
        self.assertTrue(any("CST-M.dx" in p and "no conversion" in p for p in problems), problems)
        result, execution = ex.execute_compilation(state, Progression())
        self.assertFalse(result.ok)
        self.assertFalse(execution.patch_applied)
        self.assertEqual([], state.family("GeometrySignature"))

    def _regions(self, scale):
        ops = [Op("CREATE", "FunctionalRegion", "FRG-1",
                  {"role": "KEEP_OUT", "owning_bodies": ["BOD-0001"],
                   "volume": {"centre": [0, 0, 0], "half_extent": [1, 1, 1]}},
                  "s03:topology")]
        self.assertEqual([], apply(self.state, "s03", ops))
        if scale is not None:
            self.assertEqual([], apply(self.state, "s04", [
                Op("CREATE", "ReferenceScale", "SCL-1", scale, "s04:envelope")]))

    def test_23_relative_s04_geometry_is_never_read_as_millimetres(self):
        self._regions({"basis": "RELATIVE"})
        self.settle()
        report = settled_geometry.evaluate(self.state)
        self.assertEqual(settled_geometry.NOT_COMPARABLE, report.features["FEA-1"]["status"])
        self.assertEqual([], report.findings)
        self.assertNotIn("box", report.features["FEA-1"])

    def test_24_post_settlement_checks_read_the_current_s04_region(self):
        self._regions({"basis": "ABSOLUTE", "absolute": {"unit": "mm", "per_unit": 1}})
        self.settle()
        report = settled_geometry.evaluate(self.state)
        self.assertEqual(settled_geometry.INTRUDES, report.features["FEA-1"]["status"])
        self.assertEqual(["FRG-1"], report.features["FEA-1"]["regions"])
        ready, why = canonical_io.compilation_readiness(self.state)
        self.assertFalse(ready)
        self.assertTrue(any("post-settlement" in w and "FRG-1" in w for w in why), why)
        # the volume is s04's to move (FunctionalRegion.volume is extendable by s04)
        self.assertEqual([], apply(self.state, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-1",
               {"volume": {"centre": [100, 100, 100], "half_extent": [1, 1, 1]}},
               "s04:envelope", reason="the keep-out moved")]))
        report = settled_geometry.evaluate(self.state)
        self.assertEqual(settled_geometry.RESOLVED, report.features["FEA-1"]["status"])
        self.assertEqual([], report.findings)

    def test_25_an_unresolved_scale_stays_unresolved(self):
        self._regions(None)
        self.settle()
        report = settled_geometry.evaluate(self.state)
        entry = report.features["FEA-1"]
        self.assertEqual(settled_geometry.NOT_COMPARABLE, entry["status"])
        self.assertIn("missing", entry["why"])
        self.assertIsNone(report.basis)
        self.assertEqual([], report.findings)


# =====================================================================
# F7 / F8 - non-vacuous s07 entry, premised evidence, no invention
# =====================================================================
class TestCompilationEntryGate(_Embodied):

    def test_26_s07_refuses_a_missing_settlement_basis(self):
        result, execution = ex.execute_compilation(self.state, Progression())
        self.assertFalse(result.ok)
        self.assertTrue(any("PRM-W" in p and "no standing settled value" in p
                            for p in result.problems), result.problems)
        self.assertIsNone(result.failed_statement, "the kernel was asked")
        self.assertEqual("not_ready", execution.outcome)
        self.assertEqual([], self.state.family("GeometrySignature"))

    def test_27_no_zero_body_design_can_stand(self):
        state = DesignState(run_id="zero")
        apply(state, "s03", [body()])
        result, execution = ex.execute_compilation(state, Progression())
        self.assertFalse(result.ok)
        self.assertTrue(any("no current construction program" in p for p in result.problems),
                        result.problems)
        self.assertFalse(execution.patch_applied)
        self.assertEqual([], state.family("GeometrySignature"))
        # and the hash of nothing, however it is produced, is not evidence
        empty = compiler.compile_program(ir.ConstructionProgram(statements=[]), {})
        self.assertEqual([], canonical_io.compilation_operations(empty, state)
                         if not empty.ok else [])

    def test_28_a_geometry_signature_cannot_be_premise_less(self):
        fields = {"signature_sha256": "ab" * 32, "per_body": {}, "critical_dimensions": {}}
        problems = apply(self.state, "s07", [
            Op("CREATE", "GeometrySignature", "GSG-1", fields, "s07:compilation")])
        self.assertTrue(any("PREMISELESS_EVIDENCE" in p for p in problems), problems)
        self.assertEqual([], apply(self.state, "s07", [
            Op("CREATE", "GeometrySignature", "GSG-1", fields, "s07:compilation",
               premise_refs=["CST-1", "PRM-W"])]))

    def test_29_geometry_stales_when_its_premises_move(self):
        self.settle()
        fields = {"signature_sha256": "cd" * 32, "per_body": {}, "critical_dimensions": {}}
        self.assertEqual([], apply(self.state, "s07", [
            Op("CREATE", "GeometrySignature", "GSG-2", fields, "s07:compilation",
               premise_refs=["CST-1", "PRM-W"])]))
        self.assertEqual("STANDING", self.validity("GSG-2"))
        self.assertEqual([], apply(self.state, "s05", [
            Op("SUPERSEDE", "Parameter", "PRM-W", {"symbol": "w2"}, "s05:embodiment",
               reason="restated")]))
        self.assertEqual("STALE", self.validity("GSG-2"))

    def test_30_s07_carries_no_engineering_logic(self):
        import inspect
        for module in (compiler, canonical_io, ex, settled_geometry):
            src = inspect.getsource(module)
            with self.subTest(module=module.__name__):
                for banned in ("CND-000", "BM-00", "default_thickness", "material ="):
                    self.assertNotIn(banned, src)
        with self.assertRaises(ir.IRError):
            compiler.resolve(ir.Expr.parse(REF("PRM-NONE")), {})
        self.assertEqual(set(ir.OPCODES), set(ir.OPCODE_SEMANTICS))
        self.assertEqual(set(ir.OPCODES), set(ir.OPCODE_PARAMETER_KINDS))
        for op, params in ir.OPCODES.items():
            with self.subTest(opcode=op):
                self.assertEqual(set(params), set(ir.OPCODE_PARAMETER_KINDS[op]))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
