"""UNIT F/G. Symbolic embodiment -> deterministic settlement -> CAD compilation.

The seam these tests guard: what s05 writes must be READABLE by s06 and s07
before it stands (one grammar, at the write boundary); a settled value must not
stale the symbolic definition it settles, while a revised declaration must; s06
may be asked only FOR an embodiment, and never reports the absence of one as an
empty problem that solved; s07 is entered only over a settled embodiment with a
scale authority and kernel-unit dimensions, and the geometry it signs carries
what it was concluded from.

Kernel-free: every refusal here happens before the kernel would be asked.
"""

import unittest

from ver3.assy_v3.downstream import canonical_io, compiler, execution as ex, ir, solver
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op
from ver3.tests.meta.test_workable_cad_foundation import MM, REF, apply, box, cylinder, feature


def body(state, bid="BOD-0001"):
    """A body and the s04 commitments an embodiment is placed against."""
    problems = apply(state, "s03", [Op("CREATE", "Body", bid,
                                       {"instance_identity": bid, "role": "shell",
                                        "created_by_stage": "s03"}, "s03:topology")])
    if problems:
        return problems
    ops = []
    if "SCL-1" not in state.entities:
        ops.append(Op("CREATE", "ReferenceScale", "SCL-1",
                      {"basis": "ABSOLUTE", "absolute": {"unit": "mm", "per_unit": 1.0}},
                      "s04:arrangement"))
    ops.append(Op("CREATE", "Envelope", "ENV-%s" % bid[4:],
                  {"body": bid, "extent": {"centre": [0, 0, 0], "half_extent": [10, 10, 10]},
                   "frame": "world", "maturity": "PROVISIONAL"}, "s04:arrangement",
                  premise_refs=["SCL-1"]))
    return apply(state, "s04", ops)


def param(pid, symbol="w", unit="mm", **extra):
    fields = {"symbol": symbol, "unit": unit, "status": ir.DECLARED}
    fields.update(extra)
    return Op("CREATE", "Parameter", pid, fields, "s05:embodiment")


def equals(cid, lhs, rhs, params, relation="=="):
    return Op("CREATE", "Constraint", cid,
              {"kind": "DIMENSIONAL", "parameters": list(params),
               "expression": {"relation": relation, "lhs": lhs, "rhs": rhs}},
              "s05:embodiment", premise_refs=list(params))


def stock(fid, dx, bid="BOD-0001", premises=(), steps=None):
    return feature(fid, bid, "STOCK", "ENV-%s" % bid[4:],
                   steps or [box("block", dx, MM(10), MM(4))], axis="+Z", premises=premises)


class _Embodied(unittest.TestCase):
    """One body; one parameter settled by one constraint; a stock feature that
    reads it. The minimum embodiment, well-formed."""

    def setUp(self):
        self.state = DesignState(run_id="gate")
        self.assertEqual([], body(self.state))
        self.assertEqual([], apply(self.state, "s05", [
            param("PRM-W"),
            equals("CON-W", REF("PRM-W"), MM(12), ["PRM-W"]),
            stock("FEA-1", REF("PRM-W"), premises=["PRM-W"])]))

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
        from ver3.assy_v3.state.design_state import Contracts
        fams = Contracts().families
        for family, kind in (("Parameter", "parameter"), ("Constraint", "constraint"),
                             ("Feature", "feature")):
            with self.subTest(family=family):
                self.assertEqual(kind, fams[family].get("ir_validation"))
                self.assertIn(kind, ir.IR_VALIDATION_KINDS)
        self.assertNotIn("ConstructionStatement", fams)

    def test_02_an_invalid_relation_is_refused_before_standing(self):
        problems = apply(self.state, "s05", [
            param("PRM-2"), equals("CON-2", REF("PRM-2"), MM(1), ["PRM-2"], relation=">")])
        self.assertTrue(any("relation" in p and "IR:" in p for p in problems), problems)
        self.assertNotIn("CON-2", self.state.entities)

    def test_03_a_malformed_expression_node_is_refused(self):
        for lhs in (5, {"ref": "PRM-W", "const": 1, "unit": "mm"}, {"op": "%", "args": []},
                    {"const": 1}):
            with self.subTest(lhs=lhs):
                problems = apply(self.state, "s05", [equals("CON-3", lhs, MM(1), ["PRM-W"])])
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

    def test_06_a_dangling_reference_is_rejected_and_a_same_patch_one_resolves(self):
        problems = apply(self.state, "s05", [equals("CON-6", REF("PRM-9"), MM(1), ["PRM-9"])])
        self.assertTrue(any("PRM-9" in p and "no standing Parameter" in p for p in problems), problems)
        self.assertEqual([], apply(self.state, "s05", [
            param("PRM-9"), equals("CON-6", REF("PRM-9"), MM(1), ["PRM-9"])]))

    def test_07_a_typed_zero_offset_is_representable_and_a_bare_zero_is_not(self):
        """The distinction is semantic, not lexical: `0 mm` is a coordinate; a
        bare 0 is a number somebody invented."""
        self.assertEqual([], apply(self.state, "s05", [
            feature("FEA-7", "BOD-0001", "BOSS", "FEA-1", [cylinder("c", MM(1), MM(1))],
                    offset=[MM(0), MM(0), MM(0)], axis="+Z")]))
        problems = apply(self.state, "s05", [
            Op("CREATE", "Feature", "FEA-8", {"body": "BOD-0001", "feature_kind": "BOSS",
                                              "geometry": "x",
                                              "placement": {"datum": "FEA-1", "offset": [0, 0, 0],
                                                            "axis": "+Z"},
                                              "construction": [cylinder("c", MM(1), MM(1))]},
               "s05:embodiment")])
        self.assertTrue(any("bare number" in p for p in problems), problems)

    def test_08_s05_does_not_author_a_parameter_value(self):
        problems = apply(self.state, "s05", [param("PRM-8", value=3.0)])
        self.assertTrue(any("solver artifact" in p for p in problems), problems)
        problems = apply(self.state, "s05", [
            Op("EXTEND", "Parameter", "PRM-W", {"value": 3.0}, "s05:embodiment")])
        self.assertTrue(any("EXTEND_WRONG_STAGE" in p for p in problems), problems)

    def test_09_an_unknown_opcode_or_a_missing_argument_is_refused(self):
        for steps in ([{"id": "t", "operation": "TORUS", "parameters": {"radius": MM(1)}}],
                      [{"id": "b", "operation": "BOX", "parameters": {"dx": MM(1), "dy": MM(1)}}],
                      [{"id": "b", "operation": "BOX", "parameters": [MM(1), MM(1), MM(1)]}]):
            with self.subTest(steps=steps):
                problems = apply(self.state, "s05", [
                    feature("FEA-9", "BOD-0001", "BOSS", "FEA-1", steps, axis="+Z")])
                self.assertTrue(any(p.startswith("IR:") for p in problems), problems)
        self.assertNotIn("FEA-9", self.state.entities)

    def test_10_a_step_that_consumes_no_earlier_step_is_refused(self):
        problems = apply(self.state, "s05", [
            feature("FEA-10", "BOD-0001", "BOSS", "FEA-1",
                    [cylinder("c", MM(1), MM(1)),
                     {"id": "cut", "operation": "CUT", "operands": ["c", "ghost"], "parameters": {}}],
                    axis="+Z")])
        self.assertTrue(any("ghost" in p for p in problems), problems)


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
        self.assertEqual(canonical_io.evidence_identity(a), canonical_io.evidence_identity(b))

    def test_12_settlement_does_not_stale_the_symbolic_definition(self):
        self.settle()
        self.assertAlmostEqual(12.0, self.state.entities["PRM-W"]["value"])
        for eid in ("PRM-W", "CON-W", "FEA-1"):
            with self.subTest(entity=eid):
                self.assertEqual("STANDING", self.validity(eid))

    def test_13_a_declaration_revision_stales_its_dependents(self):
        self.settle()
        self.assertEqual([], apply(self.state, "s05", [
            Op("SUPERSEDE", "Parameter", "PRM-W", {"unit": "cm"}, "s05:embodiment",
               reason="the quantity is restated")]))
        for eid in ("CON-W", "FEA-1"):
            with self.subTest(entity=eid):
                self.assertEqual("STALE", self.validity(eid))

    def test_14_a_constraint_revision_stales_the_settled_value(self):
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
        self.assertEqual(ir.FEASIBLE, self.state.entities["CON-W"]["settlement"]["solver_status"])
        self.assertIn("CON-W", rec["_premises"])


# =====================================================================
# F4 - the s06 entry gate
# =====================================================================
class TestSettlementEntryGate(unittest.TestCase):

    def test_16_a_missing_embodiment_is_not_ready(self):
        state = DesignState(run_id="noemb")
        body(state)
        report, execution = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.NOT_READY, report.solver_status)
        self.assertEqual(ir.NOT_READY, execution.outcome)
        self.assertFalse(execution.patch_applied)
        self.assertTrue(any("no current embodiment" in x for x in report.problems), report.problems)

    def test_17_an_empty_solve_cannot_stand_in_for_a_missing_embodiment(self):
        core = solver.solve([], [])
        self.assertEqual((ir.FEASIBLE, 0), (core.solver_status, core.unknown_count))
        state = DesignState(run_id="noemb2")
        body(state)
        apply(state, "s05", [param("PRM-L")])
        outcome = ex.settle(state, Progression())
        self.assertEqual(ex.NOT_READY, outcome.status)
        self.assertIsNone(state.entities["PRM-L"].get("value"))

    def test_18_a_legitimate_empty_settlement_is_explicit(self):
        state = DesignState(run_id="constants")
        body(state)
        self.assertEqual([], apply(state, "s05", [stock("FEA-K", MM(30))]))
        ready, why = canonical_io.settlement_readiness(state)
        self.assertTrue(ready, why)
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual((ir.FEASIBLE, 0), (report.solver_status, report.unknown_count))

    def test_19_a_withdrawn_embodiment_is_not_ready(self):
        t = _Embodied("setUp")
        t.setUp()
        self.assertEqual([], apply(t.state, "s05", [
            Op("INVALIDATE", "Feature", "FEA-1", {}, "s05:embodiment", reason="withdrawn")]))
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
            "feature": Op("CREATE", "Feature", "FEA-9", {"body": "BOD-0001", "feature_kind": "STOP",
                          "geometry": "x", "placement": {"datum": "FEA-1", "axis": "+Z"},
                          "construction": [box("b", MM(1), MM(1), MM(1))]}, S06),
            "constraint": Op("CREATE", "Constraint", "CON-9",
                             {"kind": "DIMENSIONAL", "parameters": ["PRM-W"],
                              "expression": {"relation": "==", "lhs": REF("PRM-W"), "rhs": MM(1)}},
                             S06),
            "declaration": Op("SUPERSEDE", "Parameter", "PRM-W", {"unit": "cm"}, S06, reason="x"),
            "construction": Op("SUPERSEDE", "Feature", "FEA-1",
                               {"construction": [box("b", MM(1), MM(1), MM(1))]}, S06, reason="x"),
        }
        for name, op in attempts.items():
            with self.subTest(decision=name):
                self.assertTrue(apply(self.state, "s06", [op]), "s06 was allowed to decide %s" % name)
        self.assertEqual({"ACTUATE": "DIRECT"}, self.state.entities["CND-A"]["principle"])


# =====================================================================
# F6 / F8 - units and the scale authority
# =====================================================================
class TestUnitsAndScale(_Embodied):

    def test_21_units_are_explicit(self):
        problems = apply(self.state, "s05", [param("PRM-21", unit="")])
        self.assertTrue(any("declares no unit" in p for p in problems), problems)
        problems = apply(self.state, "s05", [equals("CON-21", REF("PRM-W"), {"const": 1}, ["PRM-W"])])
        self.assertTrue(any(p.startswith("IR:") for p in problems), problems)

    def test_22_a_length_in_the_wrong_unit_is_refused_before_the_kernel(self):
        state = DesignState(run_id="metres")
        body(state)
        self.assertEqual([], apply(state, "s05", [
            param("PRM-M", unit="m"),
            Op("CREATE", "Constraint", "CON-M",
               {"kind": "DIMENSIONAL", "parameters": ["PRM-M"],
                "expression": {"relation": "==", "lhs": REF("PRM-M"),
                               "rhs": {"const": 0.05, "unit": "m"}}},
               "s05:embodiment", premise_refs=["PRM-M"]),
            stock("FEA-M", REF("PRM-M"), premises=["PRM-M"])]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status, report.problems)
        problems = canonical_io.construction_unit_problems(state)
        self.assertTrue(any("FEA-M.block.dx" in p and "no conversion" in p for p in problems), problems)
        result, execution = ex.execute_compilation(state, Progression())
        self.assertFalse(result.ok)
        self.assertEqual([], state.family("GeometrySignature"))

    def test_23_a_relative_basis_has_no_scale_and_none_is_invented(self):
        self.assertEqual([], apply(self.state, "s04", [
            Op("SUPERSEDE", "ReferenceScale", "SCL-1", {"basis": "RELATIVE", "absolute": None},
               "s04:arrangement", reason="no absolute size is stated")]))
        # the stock rests on the envelope, which rests on the scale: it is stale
        # now, and the embodiment must be re-issued against the revised basis
        self.assertEqual("STALE", self.validity("FEA-1"))
        self.assertEqual([], apply(self.state, "s05", [stock("FEA-2", REF("PRM-W"), premises=["PRM-W"])]))
        self.settle()
        ready, why = canonical_io.compilation_readiness(self.state)
        self.assertFalse(ready)
        self.assertTrue(any("no scale authority" in w and "RELATIVE" in w for w in why), why)

    def test_24_an_absent_reference_scale_is_no_scale_authority(self):
        from ver3.assy_v3.downstream import kinematics
        per_unit, how = kinematics.scale_authority(None, {}, [])
        self.assertIsNone(per_unit)
        self.assertIn("no ReferenceScale", how)


# =====================================================================
# F7 / F8 - non-vacuous s07 entry, premised evidence, no invention
# =====================================================================
class TestCompilationEntryGate(_Embodied):

    def test_25_s07_refuses_a_missing_settlement_basis(self):
        result, execution = ex.execute_compilation(self.state, Progression())
        self.assertFalse(result.ok)
        self.assertTrue(any("PRM-W" in p and "no standing settled value" in p for p in result.problems),
                        result.problems)
        self.assertIsNone(result.failed_feature, "the kernel was asked")
        self.assertEqual("not_ready", execution.outcome)
        self.assertEqual([], self.state.family("GeometrySignature"))

    def test_26_no_zero_body_design_can_stand(self):
        state = DesignState(run_id="zero")
        body(state)
        result, execution = ex.execute_compilation(state, Progression())
        self.assertFalse(result.ok)
        self.assertFalse(execution.patch_applied)
        self.assertEqual([], state.family("GeometrySignature"))
        empty = compiler.compile_embodiment([], {}, {}, {})
        self.assertFalse(empty.ok)

    def test_27_a_geometry_signature_cannot_be_premise_less(self):
        fields = {"signature_sha256": "ab" * 32, "per_body": {}, "critical_dimensions": {}}
        problems = apply(self.state, "s07", [
            Op("CREATE", "GeometrySignature", "GSG-1", fields, "s07:compilation")])
        self.assertTrue(any("PREMISELESS_EVIDENCE" in p for p in problems), problems)
        self.assertEqual([], apply(self.state, "s07", [
            Op("CREATE", "GeometrySignature", "GSG-1", fields, "s07:compilation",
               premise_refs=["FEA-1", "PRM-W"])]))

    def test_28_geometry_stales_when_its_premises_move(self):
        self.settle()
        fields = {"signature_sha256": "cd" * 32, "per_body": {}, "critical_dimensions": {}}
        self.assertEqual([], apply(self.state, "s07", [
            Op("CREATE", "GeometrySignature", "GSG-2", fields, "s07:compilation",
               premise_refs=["FEA-1", "PRM-W"])]))
        self.assertEqual([], apply(self.state, "s05", [
            Op("SUPERSEDE", "Parameter", "PRM-W", {"symbol": "w2"}, "s05:embodiment",
               reason="restated")]))
        self.assertEqual("STALE", self.validity("GSG-2"))

    def test_29_s07_carries_no_engineering_logic(self):
        import inspect
        from ver3.assy_v3.downstream import artifact, kinematics, settled_geometry
        for module in (compiler, canonical_io, ex, settled_geometry, artifact, kinematics):
            src = inspect.getsource(module)
            with self.subTest(module=module.__name__):
                for banned in ("CND-000", "BM-00", "default_thickness", "material ="):
                    self.assertNotIn(banned, src)
        with self.assertRaises(ir.IRError):
            compiler.resolve(ir.Expr.parse(REF("PRM-NONE")), {})
        self.assertEqual(set(ir.OPCODES), set(ir.OPCODE_SEMANTICS))
        self.assertEqual(set(ir.OPCODES), set(ir.OPCODE_PARAMETER_KINDS))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
