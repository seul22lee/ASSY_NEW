"""UNIT G. The generic foundation for workable CAD, kernel-free.

Placement is one grammar with one frame convention; the pose law is derived
from placements and joint coordinates; an embodiment is complete when CAD can
be built from it; the gates refuse what s07 would otherwise have to invent; the
model is shown the language the boundary enforces. Nothing here names a
mechanism, a candidate or a benchmark. The solid-level claims live in
tests/kernel/test_workable_cad_artifact.py.
"""

import unittest

from ver3.assy_v3.downstream import (canonical_io, embodiment, execution as ex, findings,
                                     ir, kinematics, settled_geometry)
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.stages import s05_embodiment as s05
from ver3.assy_v3.stages import s03_topology_and_mobility as s03
from ver3.assy_v3.stages import s04_envelope_and_motion as s04
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

MM = lambda v: {"const": float(v), "unit": "mm"}                # noqa: E731
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


def place(origin, axis):
    return {"origin": [MM(c) for c in origin], "axis": axis}


# ----------------------------------------------------------------------
# A two-body hinge: a base plate and a lid plate joined by one revolute joint
# about +Y along the base's far edge. Generic: the same records serve a
# prismatic variant by changing one word.
# ----------------------------------------------------------------------
def hinge_upstream(state, joint_type="REVOLUTE", axis="+Y", basis="RELATIVE",
                   contact="CONTACT", with_stop=False):
    assert [] == apply(state, "s03", [
        Op("CREATE", "Body", "BOD-A", {"instance_identity": "base", "role": "base",
                                       "created_by_stage": "s03"}, "s03:topology"),
        Op("CREATE", "Body", "BOD-B", {"instance_identity": "lid", "role": "lid",
                                       "created_by_stage": "s03"}, "s03:topology"),
        Op("CREATE", "RigidGroup", "RGP-A", {"body": "BOD-A", "members": ["BOD-A"],
                                             "is_default": True}, "s03:topology"),
        Op("CREATE", "RigidGroup", "RGP-B", {"body": "BOD-B", "members": ["BOD-B"],
                                             "is_default": True}, "s03:topology"),
        Op("CREATE", "Joint", "JNT-1", {"joint_type": joint_type, "parent_group": "RGP-A",
                                        "child_group": "RGP-B", "dof": [],
                                        "axis_direction": axis, "frame_ids": ["FRM-1"]},
           "s03:topology"),
        Op("CREATE", "Interface", "IFC-1", {"bodies": ["BOD-A", "BOD-B"],
                                            "interaction_kind": contact, "nominal": "NOMINAL"},
           "s03:topology"),
        Op("CREATE", "Configuration", "CFG-1", {"name": "closed", "bodies_present": ["BOD-A", "BOD-B"],
                                                "expected_mobility": "x"}, "s03:topology"),
        Op("CREATE", "Configuration", "CFG-2", {"name": "open", "bodies_present": ["BOD-A", "BOD-B"],
                                                "expected_mobility": "x"}, "s03:topology")])
    scale = {"basis": basis}
    if basis == "ABSOLUTE":
        scale["absolute"] = {"unit": "mm", "per_unit": 1.0}
    assert [] == apply(state, "s04", [
        Op("CREATE", "ReferenceScale", "SCL-1", scale, "s04:envelope"),
        Op("CREATE", "State", "STA-1", {"name": "closed", "configuration": "CFG-1",
                                        "joint_coordinates": {"JNT-1": 0.0}}, "s04:envelope"),
        Op("CREATE", "State", "STA-2", {"name": "open", "configuration": "CFG-2",
                                        "joint_coordinates": {"JNT-1": 90.0}}, "s04:envelope"),
        Op("CREATE", "Transition", "TRN-1", {"from_state": "STA-1", "to_state": "STA-2",
                                             "path": {"moving_groups": ["RGP-B"]},
                                             "changed_coordinates": ["JNT-1"]}, "s04:envelope")])


def hinge_embodiment(state, axis="+Y", with_stop=False, lid_axis=None):
    """Base plate 40x30x10 with the joint axis along its far top edge; lid plate
    40x30x10 with the joint axis along its near bottom edge. At zero the lid
    lies flat beyond the base, touching it; at 90 degrees it stands up."""
    lid_axis = lid_axis or axis
    ops = [
        Op("CREATE", "Parameter", "PRM-W", {"symbol": "w", "unit": "mm", "status": ir.DECLARED},
           "s05:embodiment"),
        Op("CREATE", "Parameter", "PRM-R", {"symbol": "r", "unit": "mm", "status": ir.DECLARED},
           "s05:embodiment"),
        Op("CREATE", "Constraint", "CON-W", {"kind": "DIMENSIONAL", "parameters": ["PRM-W"],
                                             "expression": {"relation": "==", "lhs": REF("PRM-W"),
                                                            "rhs": MM(40)}},
           "s05:embodiment", premise_refs=["PRM-W"]),
        Op("CREATE", "Constraint", "CON-R", {"kind": "DIMENSIONAL", "parameters": ["PRM-R"],
                                             "expression": {"relation": "==", "lhs": REF("PRM-R"),
                                                            "rhs": MM(3)}},
           "s05:embodiment", premise_refs=["PRM-R"]),
        Op("CREATE", "Feature", "FEA-A", {"body": "BOD-A", "feature_kind": "BORE",
                                          "geometry": "hinge bore", "joint": "JNT-1",
                                          "interface": "IFC-1",
                                          "placement": place((40, 0, 10), axis)},
           "s05:embodiment", premise_refs=["BOD-A", "JNT-1"]),
        Op("CREATE", "Feature", "FEA-B", {"body": "BOD-B", "feature_kind": "PIN",
                                          "geometry": "hinge pin", "joint": "JNT-1",
                                          "interface": "IFC-1",
                                          "placement": place((0, 0, 0), lid_axis)},
           "s05:embodiment", premise_refs=["BOD-B", "JNT-1"]),
        Op("CREATE", "ConstructionStatement", "CST-A1", {"body": "BOD-A", "operation": "BOX",
                                                         "operands": [],
                                                         "parameters": {"dx": REF("PRM-W"),
                                                                        "dy": MM(30), "dz": MM(10)}},
           "s05:embodiment", premise_refs=["BOD-A", "PRM-W"]),
        Op("CREATE", "ConstructionStatement", "CST-A2", {"body": "BOD-A", "operation": "CYLINDER",
                                                         "operands": [], "feature": "FEA-A",
                                                         "parameters": {"radius": REF("PRM-R"),
                                                                        "height": MM(30)}},
           "s05:embodiment", premise_refs=["BOD-A", "PRM-R"]),
        Op("CREATE", "ConstructionStatement", "CST-A3", {"body": "BOD-A", "operation": "CUT",
                                                         "operands": ["CST-A1", "CST-A2"],
                                                         "parameters": {}},
           "s05:embodiment", premise_refs=["BOD-A", "CST-A1", "CST-A2"]),
        Op("CREATE", "ConstructionStatement", "CST-B1", {"body": "BOD-B", "operation": "BOX",
                                                         "operands": [],
                                                         "parameters": {"dx": REF("PRM-W"),
                                                                        "dy": MM(30), "dz": MM(10)}},
           "s05:embodiment", premise_refs=["BOD-B", "PRM-W"]),
        Op("CREATE", "ConstructionStatement", "CST-B2", {"body": "BOD-B", "operation": "CYLINDER",
                                                         "operands": [], "feature": "FEA-B",
                                                         "parameters": {"radius": REF("PRM-R"),
                                                                        "height": MM(30)}},
           "s05:embodiment", premise_refs=["BOD-B", "PRM-R"]),
        Op("CREATE", "ConstructionStatement", "CST-B3", {"body": "BOD-B", "operation": "UNION",
                                                         "operands": ["CST-B1", "CST-B2"],
                                                         "parameters": {}},
           "s05:embodiment", premise_refs=["BOD-B", "CST-B1", "CST-B2"]),
    ]
    if with_stop:
        # a block on the base beyond the hinge edge, in the lid's way at 90 degrees
        ops += [
            # a block under the plate's far end, sharing its bottom face, reaching
            # beyond the hinge line below the pin: clear at zero, in the lid's
            # way at 90 degrees
            Op("CREATE", "Feature", "FEA-S", {"body": "BOD-A", "feature_kind": "STOP",
                                              "geometry": "a block under the far end",
                                              "placement": place((30, 0, -10), "+Z")},
               "s05:embodiment", premise_refs=["BOD-A"]),
            Op("CREATE", "ConstructionStatement", "CST-A4", {"body": "BOD-A", "operation": "BOX",
                                                             "operands": [], "feature": "FEA-S",
                                                             "parameters": {"dx": MM(20), "dy": MM(30),
                                                                            "dz": MM(10)}},
               "s05:embodiment", premise_refs=["BOD-A"]),
            Op("CREATE", "ConstructionStatement", "CST-A5", {"body": "BOD-A", "operation": "UNION",
                                                             "operands": ["CST-A3", "CST-A4"],
                                                             "parameters": {}},
               "s05:embodiment", premise_refs=["BOD-A", "CST-A3", "CST-A4"]),
        ]
    return apply(state, "s05", ops)


def hinge(joint_type="REVOLUTE", axis="+Y", basis="RELATIVE", contact="CONTACT",
          with_stop=False, lid_axis=None):
    state = DesignState(run_id="hinge")
    hinge_upstream(state, joint_type=joint_type, axis=axis, basis=basis, contact=contact)
    problems = hinge_embodiment(state, axis=axis, with_stop=with_stop, lid_axis=lid_axis)
    assert problems == [], problems
    return state


# ======================================================================
class TestOnePlacementGrammar(unittest.TestCase):

    def test_01_placement_is_origin_and_axis_and_nothing_else(self):
        p = ir.Placement.parse(place((1, 2, 3), "-x"))
        self.assertEqual("-X", p.axis)
        for bad in ({"origin": [0, 0, 0], "axis": "+Y"},               # bare numbers
                    {"origin": [MM(0)] * 2, "axis": "+Y"},              # two components
                    {"origin": [MM(0)] * 3, "axis": "Q"},               # no such axis
                    {"origin": [MM(0)] * 3, "axis": "+Y", "reference": "+X"},
                    [MM(0)] * 3):
            with self.subTest(bad=bad):
                with self.assertRaises(ir.IRError):
                    ir.Placement.parse(bad)

    def test_02_the_frame_convention_is_a_rule_not_a_choice(self):
        x, y, z = ir.frame_axes("+Y")
        self.assertEqual((0.0, 1.0, 0.0), z)
        self.assertEqual((0.0, 0.0, 1.0), x)          # Y -> Z, the canonical perpendicular
        self.assertEqual((1.0, 0.0, 0.0), y)          # right-handed
        for axis in ir.SIGNED_AXES:
            xa, ya, za = ir.frame_axes(axis)
            dot = sum(a * b for a, b in zip(xa, za))
            self.assertEqual(0.0, dot, axis)

    def test_03_there_is_one_axis_table(self):
        self.assertEqual(tuple(ir.SIGNED_AXES) + ("NONE",), s03.AXIS_DIRECTIONS)
        self.assertEqual(ir.AXIS_VECTORS, s04.AXIS_VECTORS)
        self.assertEqual(ir.AXIS_INDEX, s04.AXIS_INDEX)
        mating = Contracts().families["Interface"]["field_semantics"]["mating_geometry"]
        self.assertEqual(sorted(ir.SIGNED_AXES),
                         sorted(mating["record_field_semantics"]["axis_direction"]["values"]))

    def test_04_the_boundary_refuses_a_placement_it_cannot_read(self):
        state = DesignState(run_id="p")
        hinge_upstream(state)
        problems = apply(state, "s05", [
            Op("CREATE", "Feature", "FEA-X", {"body": "BOD-A", "feature_kind": "BORE",
                                              "geometry": "x", "placement": {"origin": [0, 0, 0],
                                                                             "axis": "+Y"}},
               "s05:embodiment")])
        self.assertTrue(any("IR:" in p and "bare number" in p for p in problems), problems)
        problems = apply(state, "s05", [
            Op("CREATE", "Feature", "FEA-X", {"body": "BOD-A", "feature_kind": "BORE",
                                              "geometry": "x", "placement": place((0, 0, 0), "+Y"),
                                              "joint": "JNT-9"}, "s05:embodiment")])
        self.assertTrue(any("JNT-9" in p for p in problems), problems)

    def test_05_the_feature_kind_vocabulary_is_the_contracts_and_is_enforced(self):
        declared = Contracts().families["Feature"]["field_semantics"]["feature_kind"]["values"]
        self.assertEqual(tuple(declared), s05.FEATURE_KINDS)
        mating = Contracts().families["Interface"]["field_semantics"]["mating_geometry"]
        inner = mating["record_field_semantics"]["inner_feature"]["values"]
        outer = mating["record_field_semantics"]["outer_feature"]["values"]
        self.assertTrue(set(inner + outer) <= set(declared))
        state = DesignState(run_id="k")
        hinge_upstream(state)
        problems = apply(state, "s05", [
            Op("CREATE", "Feature", "FEA-X", {"body": "BOD-A", "feature_kind": "FLANGE_THING",
                                              "geometry": "x"}, "s05:embodiment")])
        self.assertTrue(any("ENUM_VALUE" in p for p in problems), problems)


# ======================================================================
class TestThePoseLawIsDerived(unittest.TestCase):

    def _law(self, state, coordinates):
        joints = state.standing("Joint")
        groups = state.standing("RigidGroup")
        values = canonical_io.resolved_values(state)
        frames, notes = kinematics.realizations(state.standing("Feature"), values)
        self.assertEqual([], notes)
        law = kinematics.derive_poses(joints, groups, frames, coordinates, ["BOD-A", "BOD-B"])
        return law

    def test_06_revolute_placement_is_deterministic(self):
        state = hinge()
        ex.execute_settlement(state, Progression())
        law = self._law(state, {"JNT-1": 0.0})
        self.assertEqual("BOD-A", law.base)
        self.assertEqual([], [str(f) for f in law.findings])
        self.assertEqual([40.0, 0.0, 10.0],
                         [round(v, 9) for v in law.poses["BOD-B"].apply((0, 0, 0))])
        # 90 degrees about +Y through the base's far edge: the lid's +X goes to -Z
        law90 = self._law(state, {"JNT-1": 90.0})
        self.assertEqual([40.0, 0.0, 0.0],
                         [round(v, 9) for v in law90.poses["BOD-B"].apply((10, 0, 0))])
        again = self._law(state, {"JNT-1": 90.0})
        self.assertEqual(law90.as_record(), again.as_record())

    def test_07_prismatic_placement_is_deterministic(self):
        state = hinge(joint_type="PRISMATIC", axis="+X")
        ex.execute_settlement(state, Progression())
        law = self._law(state, {"JNT-1": 12.5})
        self.assertEqual([], [str(f) for f in law.findings])
        self.assertEqual([52.5, 0.0, 10.0],
                         [round(v, 9) for v in law.poses["BOD-B"].apply((0, 0, 0))])

    def test_08_mating_axes_are_checked_not_assumed(self):
        state = hinge(lid_axis="+Z")            # the lid realizes the hinge along the wrong axis
        ex.execute_settlement(state, Progression())
        law = self._law(state, {"JNT-1": 0.0})
        self.assertTrue(any(f.kind == findings.MATING_AXES_INCONSISTENT for f in law.findings),
                        [str(f) for f in law.findings])

    def test_09_a_prismatic_travel_in_a_relative_basis_is_not_a_length(self):
        state = hinge(joint_type="PRISMATIC", axis="+X", basis="RELATIVE")
        coords, notes = kinematics.coordinates_in_kernel_units(
            state.standing("Joint"), {"JNT-1": 12.5}, state.standing("ReferenceScale")[0])
        self.assertEqual({}, coords)
        self.assertEqual([findings.NOT_EVALUABLE], [f.kind for f in notes])
        self.assertFalse(notes[0].evaluable)
        state = hinge(joint_type="PRISMATIC", axis="+X", basis="ABSOLUTE")
        coords, notes = kinematics.coordinates_in_kernel_units(
            state.standing("Joint"), {"JNT-1": 12.5}, state.standing("ReferenceScale")[0])
        self.assertEqual({"JNT-1": 12.5}, coords)

    def test_10_no_pose_is_invented_for_an_unrealized_joint(self):
        state = DesignState(run_id="unrealized")
        hinge_upstream(state)
        law = kinematics.derive_poses(state.standing("Joint"), state.standing("RigidGroup"),
                                      {}, {"JNT-1": 0.0}, ["BOD-A", "BOD-B"])
        self.assertNotIn("BOD-B", law.poses)
        self.assertTrue(any(f.kind == findings.POSE_NOT_DERIVABLE for f in law.findings))

    def test_11_motion_is_sampled_as_s04_samples(self):
        samples, declaration = kinematics.motion_samples({"JNT-1": 0.0}, {"JNT-1": 90.0}, ["JNT-1"])
        self.assertEqual(s04.SAMPLES, len(samples))
        self.assertEqual(0.0, samples[0]["JNT-1"])
        self.assertEqual(90.0, samples[-1]["JNT-1"])
        self.assertFalse(declaration["adaptive"])


# ======================================================================
class TestCompletenessMeansConstructible(unittest.TestCase):

    def test_12_an_unrealized_joint_is_named(self):
        state = DesignState(run_id="c")
        hinge_upstream(state)
        rows = embodiment.rows_from_state(state, None)
        problems = embodiment.structural_problems(rows)
        self.assertTrue(any("JNT-1" in p and "BOD-A" in p for p in problems), problems)
        self.assertTrue(any("BOD-B has no construction statement" in p for p in problems), problems)

    def test_13_a_complete_embodiment_has_no_structural_problem(self):
        state = hinge()
        self.assertEqual([], embodiment.structural_problems(embodiment.rows_from_state(state, None)))

    def test_14_a_placed_feature_nothing_builds_is_named(self):
        state = hinge()
        self.assertEqual([], apply(state, "s05", [
            Op("CREATE", "Feature", "FEA-Q", {"body": "BOD-A", "feature_kind": "STOP",
                                              "geometry": "x", "placement": place((1, 1, 1), "+Z")},
               "s05:embodiment")]))
        problems = embodiment.structural_problems(embodiment.rows_from_state(state, None))
        self.assertTrue(any("FEA-Q" in p and "nothing is built" in p for p in problems), problems)

    def test_15_the_settlement_gate_refuses_a_non_constructible_embodiment(self):
        state = DesignState(run_id="g")
        hinge_upstream(state)
        self.assertEqual([], apply(state, "s05", [
            Op("CREATE", "ConstructionStatement", "CST-A1", {"body": "BOD-A", "operation": "BOX",
                                                             "operands": [],
                                                             "parameters": {"dx": MM(1), "dy": MM(1),
                                                                            "dz": MM(1)}},
               "s05:embodiment")]))
        report, execution = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.NOT_READY, report.solver_status)
        self.assertTrue(any("JNT-1" in p for p in report.problems), report.problems)

    def test_16_s05_reports_the_same_checks_by_name_before_writing(self):
        state = DesignState(run_id="v")
        hinge_upstream(state)
        view = {fam: state.standing(fam) for fam in ("Body", "RigidGroup", "Joint", "Interface")}
        response = {"features": [{"id": "FEA-1", "body": "BOD-A", "feature_kind": "BORE",
                                  "geometry": "x", "joint": "JNT-1",
                                  "placement": place((0, 0, 0), "+Z")}],
                    "construction_statements": [], "parameters": []}
        c11 = s05.check_c11_joints_realized(response, view)
        self.assertTrue(any("BOD-B" in p for p in c11), c11)
        self.assertTrue(any("+Z" in p and "+Y" in p for p in c11), c11)
        c12 = s05.check_c12_bodies_built(response, view)
        self.assertEqual(2, len(c12), c12)
        c13 = s05.check_c13_placed_features_built(response, view)
        self.assertTrue(any("FEA-1" in p for p in c13), c13)

    def test_17_mating_kinds_are_checked_against_s04s_mating_geometry(self):
        rows = {"Body": [], "RigidGroup": [], "Joint": [], "ConstructionStatement": [],
                "Interface": [{"entity_id": "IFC-1", "bodies": ["BOD-A", "BOD-B"],
                               "mating_geometry": {"inner_feature": "PIN", "outer_feature": "BORE",
                                                   "inner_body": "BOD-B", "outer_body": "BOD-A"}}],
                "Feature": [{"entity_id": "F1", "body": "BOD-A", "feature_kind": "BORE",
                             "interface": "IFC-1"},
                            {"entity_id": "F2", "body": "BOD-B", "feature_kind": "FACE",
                             "interface": "IFC-1"}]}
        problems = embodiment.mating_kind_problems(rows)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("PIN", problems[0])


# ======================================================================
class TestGatesRefuseWhatS07WouldInvent(unittest.TestCase):

    def test_18_an_unsettled_placement_parameter_blocks_compilation(self):
        state = DesignState(run_id="u")
        hinge_upstream(state)
        self.assertEqual([], apply(state, "s05", [
            Op("CREATE", "Parameter", "PRM-H", {"symbol": "h", "unit": "mm", "status": ir.DECLARED},
               "s05:embodiment"),
            Op("CREATE", "Feature", "FEA-A", {"body": "BOD-A", "feature_kind": "BORE", "geometry": "x",
                                              "joint": "JNT-1",
                                              "placement": {"origin": [MM(0), MM(0), REF("PRM-H")],
                                                            "axis": "+Y"}}, "s05:embodiment"),
            Op("CREATE", "Feature", "FEA-B", {"body": "BOD-B", "feature_kind": "PIN", "geometry": "x",
                                              "joint": "JNT-1", "placement": place((0, 0, 0), "+Y")},
               "s05:embodiment"),
            Op("CREATE", "ConstructionStatement", "CST-A", {"body": "BOD-A", "operation": "CYLINDER",
                                                            "operands": [], "feature": "FEA-A",
                                                            "parameters": {"radius": MM(3),
                                                                           "height": MM(5)}},
               "s05:embodiment"),
            Op("CREATE", "ConstructionStatement", "CST-B", {"body": "BOD-B", "operation": "CYLINDER",
                                                            "operands": [], "feature": "FEA-B",
                                                            "parameters": {"radius": MM(3),
                                                                           "height": MM(5)}},
               "s05:embodiment")]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.UNDERDETERMINED, report.solver_status)
        ready, why = canonical_io.compilation_readiness(state)
        self.assertFalse(ready)
        self.assertTrue(any("PRM-H" in w for w in why), why)

    def test_19_a_non_positive_settled_dimension_is_refused_before_the_kernel(self):
        state = DesignState(run_id="np")
        hinge_upstream(state)
        self.assertEqual([], hinge_embodiment(state))
        self.assertEqual([], apply(state, "s05", [
            Op("SUPERSEDE", "Constraint", "CON-R", {"expression": {"relation": "==", "lhs": REF("PRM-R"),
                                                                    "rhs": MM(-3)}},
               "s05:embodiment", reason="a negative radius")]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status)
        problems = settled_geometry.construction_problems(state)
        self.assertTrue(any("CONSTRUCTION_INVALID" in p and "CST-A2" in p for p in problems), problems)
        ready, why = canonical_io.compilation_readiness(state)
        self.assertFalse(ready)

    def test_20_findings_are_typed_and_owned(self):
        f = findings.Finding(findings.BODY_INTERFERENCE, "s05", ("BOD-A", "BOD-B"), "they overlap",
                             evidence={"shared_volume": 1.0})
        self.assertEqual("s05", f.as_record()["owner"])
        with self.assertRaises(ValueError):
            findings.Finding("SOMETHING_ELSE", "s05", (), "x")
        with self.assertRaises(ValueError):
            findings.Finding(findings.BODY_INTERFERENCE, "cad", (), "x")
        note = findings.Finding(findings.NOT_EVALUABLE, "s04", (), "no scale", evaluable=False)
        self.assertEqual([], findings.blocking([note]))


# ======================================================================
class TestTheModelIsShownTheLanguageTheBoundaryEnforces(unittest.TestCase):

    def test_21_the_grammar_section_is_rendered_from_the_ir(self):
        grammar = s05.S05Embodiment.render_grammar()
        for op in ir.OPCODES:
            self.assertIn(op, grammar)
            self.assertIn(ir.OPCODE_SEMANTICS[op], grammar)
        for axis in ir.SIGNED_AXES:
            self.assertIn('"%s"' % axis, grammar)
        for relation in ir.RELATIONS:
            self.assertIn('"%s"' % relation, grammar)
        self.assertIn(ir.KERNEL_LENGTH_UNIT, grammar)
        self.assertIn('"origin"', grammar)
        self.assertIn("PARALLEL", grammar)

    def test_21b_negation_is_one_form_and_means_minus(self):
        """A placement below the origin needs "minus this"; the one-argument
        `-` is negation for the parser, the solver and the compiler alike."""
        from ver3.assy_v3.downstream import compiler, solver
        node = {"op": "-", "args": [{"op": "/", "args": [REF("PRM-W"), {"const": 2, "unit": "1"}]}]}
        expr = ir.Expr.parse(node)
        self.assertEqual(-20.0, compiler.resolve(expr, {"PRM-W": 40.0}))
        form = solver.reduce_expr(expr, {"PRM-W": "mm"})
        self.assertEqual(-0.5, form.terms["PRM-W"])
        for bad in ({"op": "+", "args": [REF("PRM-W")]}, {"op": "-", "args": []}):
            with self.subTest(bad=bad):
                with self.assertRaises(ir.IRError):
                    ir.Expr.parse(bad)
        grammar = s05.S05Embodiment.render_grammar()
        self.assertIn("negation", grammar)
        self.assertIn("never its symbol", grammar)
        self.assertIn("operands: two or more; parameters: none", grammar)

    def test_22_the_response_schema_offers_placement_and_joint(self):
        schema = s05.S05Embodiment.render_response_schema()
        self.assertIn("placement", schema)
        self.assertIn("joint", schema)

    def test_23_to_operations_carries_placement_and_joint_as_typed_premises(self):
        response = {"features": [{"id": "FEA-1", "body": "BOD-A", "feature_kind": "BORE",
                                  "geometry": "x", "joint": "JNT-1",
                                  "placement": {"origin": [REF("PRM-1"), MM(0), MM(0)], "axis": "+Y"}}],
                    "realizations": [], "parameters": [{"id": "PRM-1", "symbol": "a", "unit": "mm"}],
                    "constraints": [], "construction_statements": [], "unresolved": []}
        ops = s05.S05Embodiment().to_operations(response)
        feature = next(op for op in ops if op.entity_type == "Feature")
        self.assertEqual("JNT-1", feature.fields["joint"])
        self.assertIn("JNT-1", feature.premise_refs)
        self.assertIn("PRM-1", feature.premise_refs)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
