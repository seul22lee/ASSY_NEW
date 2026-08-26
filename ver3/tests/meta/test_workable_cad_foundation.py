"""UNIT G. The generic foundation for workable CAD, kernel-free.

One spatial authority: s04's arrangement frame, its located joint frames, its
envelopes and regions, and its scale. A feature is placed relative to those
(a datum + an offset), owns its construction, and is composed into its body by
declared polarity. The pose law is derived from the located joint frames and
the joint coordinates. Nothing here names a mechanism, a candidate or a
benchmark. The solid-level claims live in tests/kernel/test_workable_cad_artifact.py.
"""

import unittest
from string import Formatter

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


def box(sid, dx, dy, dz):
    return {"id": sid, "operation": "BOX", "operands": [],
            "parameters": {"dx": dx, "dy": dy, "dz": dz}}


def cylinder(sid, radius, height):
    return {"id": sid, "operation": "CYLINDER", "operands": [],
            "parameters": {"radius": radius, "height": height}}


def feature(fid, body, kind, datum, steps, offset=None, axis=None, interface=None,
            premises=()):
    placement = {"datum": datum}
    if offset is not None:
        placement["offset"] = offset
    if axis is not None:
        placement["axis"] = axis
    fields = {"body": body, "feature_kind": kind, "geometry": "%s of %s" % (kind.lower(), body),
              "placement": placement, "construction": list(steps)}
    prem = [body, datum] + list(premises)
    if interface:
        fields["interface"] = interface
        prem.append(interface)
    return Op("CREATE", "Feature", fid, fields, "s05:embodiment", premise_refs=prem)


# ----------------------------------------------------------------------
# A two-body hinge as s03/s04 commit it: a base plate 40x30x10 at the origin,
# a lid plate 40x30x10 beyond its far edge, one revolute joint about +Y
# located along that edge, states at 0 and 90 degrees, a transition between.
# In the arrangement basis, with an ABSOLUTE scale of 1 mm per unit unless
# a RELATIVE basis is asked for.
# ----------------------------------------------------------------------
def hinge_upstream(state, joint_type="REVOLUTE", axis="+Y", basis="ABSOLUTE",
                   contact="CONTACT", locate_joint=True):
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
    ops = [
        Op("CREATE", "ReferenceScale", "SCL-1", scale, "s04:envelope"),
        Op("CREATE", "Envelope", "ENV-A", {"body": "BOD-A", "extent": {"centre": [20, 15, 5],
                                                                        "half_extent": [20, 15, 5]},
                                           "frame": "world", "maturity": "PROVISIONAL"},
           "s04:envelope", premise_refs=["SCL-1"]),
        Op("CREATE", "Envelope", "ENV-B", {"body": "BOD-B", "extent": {"centre": [60, 15, 15],
                                                                        "half_extent": [20, 15, 5]},
                                           "frame": "world", "maturity": "PROVISIONAL"},
           "s04:envelope", premise_refs=["SCL-1"]),
        Op("CREATE", "State", "STA-1", {"name": "closed", "configuration": "CFG-1",
                                        "joint_coordinates": {"JNT-1": 0.0}}, "s04:envelope"),
        Op("CREATE", "State", "STA-2", {"name": "open", "configuration": "CFG-2",
                                        "joint_coordinates": {"JNT-1": 90.0}}, "s04:envelope"),
        Op("CREATE", "Transition", "TRN-1", {"from_state": "STA-1", "to_state": "STA-2",
                                             "path": {"moving_groups": ["RGP-B"]},
                                             "changed_coordinates": ["JNT-1"]}, "s04:envelope")]
    if locate_joint:
        ops.append(Op("EXTEND", "Joint", "JNT-1", {"frame_origin": [40, 0, 10]}, "s04:envelope",
                      premise_refs=["SCL-1"]))
    assert [] == apply(state, "s04", ops)


def hinge_embodiment(state, with_stop=False, scale_parameter=None):
    """Base stock at its envelope; lid stock at its envelope; a bore on the base
    and a pin on the lid, both AT the joint; one settled width and radius.
    `scale_parameter`: declare the RELATIVE basis's scale (mm per unit) as a
    settled parameter, bound FIRST so nothing placed against it is staled."""
    ops = []
    if scale_parameter is not None:
        ops += [
            Op("CREATE", "Parameter", "PRM-S", {"symbol": "scale", "unit": "mm", "status": ir.DECLARED,
                                                "role": "SCALE"}, "s05:embodiment"),
            Op("CREATE", "Constraint", "CON-S", {"kind": "DIMENSIONAL", "parameters": ["PRM-S"],
                                                 "expression": {"relation": "==", "lhs": REF("PRM-S"),
                                                                "rhs": MM(scale_parameter)}},
               "s05:embodiment", premise_refs=["PRM-S"])]
    ops += [
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
        feature("FEA-A-STOCK", "BOD-A", "STOCK", "ENV-A",
                [box("plate", REF("PRM-W"), MM(30), MM(10))],
                offset=[MM(-20), MM(-15), MM(-5)], axis="+Z", premises=["PRM-W"]),
        feature("FEA-B-STOCK", "BOD-B", "STOCK", "ENV-B",
                [box("plate", REF("PRM-W"), MM(30), MM(10))],
                offset=[MM(-20), MM(-15), MM(-5)], axis="+Z", premises=["PRM-W"]),
        feature("FEA-A-BORE", "BOD-A", "BORE", "JNT-1", [cylinder("hole", REF("PRM-R"), MM(30))],
                interface="IFC-1", premises=["PRM-R"]),
        feature("FEA-B-PIN", "BOD-B", "PIN", "JNT-1", [cylinder("pin", REF("PRM-R"), MM(30))],
                interface="IFC-1", premises=["PRM-R"]),
        # WHAT EMBODIES THE HINGE, said rather than inferred from where the
        # bore and the pin happen to sit.
        Op("CREATE", "KinematicRealization", "KRL-1",
           {"realizes": "JNT-1", "participating_features": ["FEA-A-BORE", "FEA-B-PIN"]},
           "s05:embodiment", premise_refs=["JNT-1", "FEA-A-BORE", "FEA-B-PIN"]),
    ]
    if with_stop:
        # a block under the base plate's far end, beyond the hinge line: clear
        # at zero, in the lid's way at 90 degrees
        ops.append(feature("FEA-S", "BOD-A", "STOP", "FEA-A-STOCK",
                           [box("block", MM(20), MM(30), MM(10))],
                           offset=[MM(30), MM(0), MM(-10)], axis="+Z"))
    return apply(state, "s05", ops)


def hinge(**kwargs):
    with_stop = kwargs.pop("with_stop", False)
    scale_parameter = kwargs.pop("scale_parameter", None)
    state = DesignState(run_id="hinge")
    hinge_upstream(state, **kwargs)
    problems = hinge_embodiment(state, with_stop=with_stop, scale_parameter=scale_parameter)
    assert problems == [], problems
    return state


# ======================================================================
class TestOnePlacementAuthority(unittest.TestCase):

    def test_01_a_feature_is_placed_against_a_datum_and_never_at_a_position(self):
        p = ir.Placement.parse({"datum": "JNT-1"})
        self.assertEqual("JNT-1", p.datum)
        self.assertIsNone(p.axis)
        for bad in ({"origin": [MM(0)] * 3, "axis": "+Y"},        # the retired absolute form
                    {"datum": "ENV-A", "offset": [0, 0, 0]},        # bare numbers
                    {"datum": "ENV-A", "axis": "Q"},
                    {"datum": ""}, "JNT-1"):
            with self.subTest(bad=bad):
                with self.assertRaises(ir.IRError):
                    ir.Placement.parse(bad)

    def test_02_the_boundary_refuses_a_second_spatial_truth(self):
        state = DesignState(run_id="p")
        hinge_upstream(state)
        stock = feature("FEA-1", "BOD-A", "STOCK", "ENV-A", [box("b", MM(1), MM(1), MM(1))], axis="+Z")
        self.assertEqual([], apply(state, "s05", [stock]))
        cases = {
            "an axis on a joint datum that disagrees with the joint": feature(
                "FEA-2", "BOD-A", "BORE", "JNT-1", [cylinder("c", MM(1), MM(1))], axis="+Z"),
            "unknown datum": feature("FEA-2", "BOD-A", "BOSS", "JNT-9",
                                     [cylinder("c", MM(1), MM(1))]),
            "another body's envelope": feature("FEA-2", "BOD-A", "BOSS", "ENV-B",
                                               [cylinder("c", MM(1), MM(1))], axis="+Z"),
            "another body's feature": feature("FEA-2", "BOD-B", "BOSS", "FEA-1",
                                              [cylinder("c", MM(1), MM(1))], axis="+Z"),
            "no construction": Op("CREATE", "Feature", "FEA-2",
                                  {"body": "BOD-A", "feature_kind": "BOSS", "geometry": "x",
                                   "placement": {"datum": "ENV-A", "axis": "+Z"},
                                   "construction": []}, "s05:embodiment"),
            "two terminals": feature("FEA-2", "BOD-A", "BOSS", "ENV-A",
                                     [cylinder("c1", MM(1), MM(1)), cylinder("c2", MM(1), MM(1))],
                                     axis="+Z"),
        }
        for name, op in cases.items():
            with self.subTest(case=name):
                problems = apply(state, "s05", [op])
                self.assertTrue(any(p.startswith("IR:") or "DANGLING" in p for p in problems), problems)
                self.assertNotIn("FEA-2", state.entities)

    def test_02b_a_consistent_restatement_and_an_omitted_axis_are_not_second_truths(self):
        state = DesignState(run_id="p2")
        hinge_upstream(state)
        self.assertEqual([], apply(state, "s05", [
            feature("FEA-1", "BOD-A", "STOCK", "ENV-A", [box("b", MM(1), MM(1), MM(1))]),
            feature("FEA-2", "BOD-A", "BORE", "JNT-1", [cylinder("c", MM(1), MM(1))], axis="+Y")]))
        per_unit, how, frames, notes = canonical_io.scale_and_frames(state)
        z = [frames["FEA-1"].r[i][2] for i in range(3)]
        self.assertEqual([0.0, 0.0, 1.0], z, "an envelope's frame is the arrangement's")
        z = [frames["FEA-2"].r[i][2] for i in range(3)]
        self.assertEqual([0.0, 1.0, 0.0], z, "a joint datum's axis is the joint's")

    def test_03_there_is_one_axis_table(self):
        self.assertEqual(tuple(ir.SIGNED_AXES) + ("NONE",), s03.AXIS_DIRECTIONS)
        self.assertEqual(ir.AXIS_VECTORS, s04.AXIS_VECTORS)
        mating = Contracts().families["Interface"]["field_semantics"]["mating_geometry"]
        self.assertEqual(sorted(ir.SIGNED_AXES),
                         sorted(mating["record_field_semantics"]["axis_direction"]["values"]))
        placement = Contracts().families["Feature"]["field_semantics"]["placement"]
        self.assertEqual(sorted(ir.SIGNED_AXES),
                         sorted(placement["record_field_semantics"]["axis"]["values"]))

    def test_04_the_scale_authority_is_the_reference_scales(self):
        self.assertEqual((None,), kinematics.scale_authority({"basis": "RELATIVE"}, {})[:1])
        self.assertEqual(2.0, kinematics.scale_authority(
            {"basis": "ABSOLUTE", "absolute": {"unit": "mm", "per_unit": 2.0}}, {})[0])
        self.assertIsNone(kinematics.scale_authority(
            {"basis": "ABSOLUTE", "absolute": {"unit": "in", "per_unit": 2.0}}, {})[0])
        scale_param = [{"entity_id": "PRM-S", "role": "SCALE"}]
        self.assertIsNone(kinematics.scale_authority({"basis": "RELATIVE"}, {}, scale_param)[0])
        self.assertEqual(3.0, kinematics.scale_authority({"basis": "RELATIVE"}, {"PRM-S": 3.0},
                                                         scale_param)[0])
        self.assertIsNone(kinematics.scale_authority({"basis": "RELATIVE"}, {"PRM-S": 3.0, "PRM-T": 1.0},
                                                     scale_param + [{"entity_id": "PRM-T", "role": "SCALE"}])[0])

    def test_05_the_feature_kind_vocabulary_and_polarity_are_the_contracts(self):
        fam = Contracts().families["Feature"]
        self.assertEqual(tuple(fam["field_semantics"]["feature_kind"]["values"]), s05.FEATURE_KINDS)
        polarity = embodiment.polarity_table()
        self.assertEqual(set(s05.FEATURE_KINDS), set(polarity))
        self.assertEqual("ADDITIVE", polarity["STOCK"])
        self.assertEqual("SUBTRACTIVE", polarity["BORE"])
        mating = fam and Contracts().families["Interface"]["field_semantics"]["mating_geometry"]
        inner = mating["record_field_semantics"]["inner_feature"]["values"]
        outer = mating["record_field_semantics"]["outer_feature"]["values"]
        self.assertTrue(set(inner + outer) <= set(s05.FEATURE_KINDS))


# ======================================================================
class TestFramesAndPosesAreDerived(unittest.TestCase):

    def _frames(self, state):
        ex.execute_settlement(state, Progression())
        per_unit, how, frames, notes = canonical_io.scale_and_frames(state)
        return per_unit, frames, notes

    def test_06_a_feature_frame_comes_from_its_datum_the_scale_and_the_offset(self):
        state = hinge()
        per_unit, frames, notes = self._frames(state)
        self.assertEqual(1.0, per_unit)
        self.assertEqual([], [str(n) for n in notes])
        self.assertEqual([0.0, 0.0, 0.0], [round(v, 9) for v in frames["FEA-A-STOCK"].t])
        self.assertEqual([40.0, 0.0, 10.0], [round(v, 9) for v in frames["FEA-A-BORE"].t])
        z = [frames["FEA-A-BORE"].r[i][2] for i in range(3)]
        self.assertEqual([0.0, 1.0, 0.0], [round(v, 9) for v in z])         # the joint's +Y

    def test_07_no_scale_means_no_frame_and_no_invented_one(self):
        state = hinge(basis="RELATIVE")
        per_unit, frames, notes = self._frames(state)
        self.assertIsNone(per_unit)
        self.assertEqual({}, frames)
        self.assertTrue(all(n.kind == findings.NOT_EVALUABLE and not n.evaluable for n in notes))
        ready, why = canonical_io.compilation_readiness(state)
        self.assertFalse(ready)
        self.assertTrue(any("no scale authority" in w for w in why), why)

    def test_08_a_settled_scale_parameter_is_a_scale_authority(self):
        state = hinge(basis="RELATIVE", scale_parameter=2)
        per_unit, frames, notes = self._frames(state)
        self.assertEqual(2.0, per_unit)
        self.assertEqual([80.0, 0.0, 20.0], [round(v, 9) for v in frames["FEA-A-BORE"].t])

    def test_09_the_pose_law_rotates_about_the_located_joint_frame(self):
        state = hinge()
        ex.execute_settlement(state, Progression())
        joints, groups = state.standing("Joint"), state.standing("RigidGroup")
        law0 = kinematics.derive_poses(joints, groups, {"JNT-1": 0.0}, 1.0, ["BOD-A", "BOD-B"])
        self.assertEqual("BOD-A", law0.base)
        self.assertEqual([], law0.findings)
        self.assertEqual([50.0, 0.0, 10.0], [round(v, 9) for v in law0.poses["BOD-B"].apply((50, 0, 10))])
        law90 = kinematics.derive_poses(joints, groups, {"JNT-1": 90.0}, 1.0, ["BOD-A", "BOD-B"])
        # a lid point 10 beyond the hinge line swings to 10 below it
        self.assertEqual([40.0, 0.0, 0.0], [round(v, 9) for v in law90.poses["BOD-B"].apply((50, 0, 10))])
        self.assertEqual(law90.as_record(), kinematics.derive_poses(
            joints, groups, {"JNT-1": 90.0}, 1.0, ["BOD-A", "BOD-B"]).as_record())

    def test_10_a_prismatic_joint_translates_along_its_axis_through_the_scale(self):
        state = hinge(joint_type="PRISMATIC", axis="+X")
        joints, groups = state.standing("Joint"), state.standing("RigidGroup")
        coords, notes = kinematics.coordinates_in_kernel_units(joints, {"JNT-1": 12.5}, 2.0)
        self.assertEqual({"JNT-1": 25.0}, coords)
        law = kinematics.derive_poses(joints, groups, coords, 2.0, ["BOD-A", "BOD-B"])
        self.assertEqual([25.0, 0.0, 0.0], [round(v, 9) for v in law.poses["BOD-B"].apply((0, 0, 0))])
        coords, notes = kinematics.coordinates_in_kernel_units(joints, {"JNT-1": 12.5}, None)
        self.assertEqual({}, coords)
        self.assertEqual([findings.NOT_EVALUABLE], [n.kind for n in notes])

    def test_11_an_unlocated_joint_gives_no_pose_and_no_default(self):
        state = DesignState(run_id="unlocated")
        hinge_upstream(state, locate_joint=False)
        law = kinematics.derive_poses(state.standing("Joint"), state.standing("RigidGroup"),
                                      {"JNT-1": 0.0}, 1.0, ["BOD-A", "BOD-B"])
        self.assertNotIn("BOD-B", law.poses)
        self.assertEqual([findings.POSE_NOT_DERIVABLE], [f.kind for f in law.findings if f.owner == "s04"][:1])

    def test_12_an_unsupported_joint_class_is_reported_not_approximated(self):
        state = hinge(joint_type="SPHERICAL")
        law = kinematics.derive_poses(state.standing("Joint"), state.standing("RigidGroup"),
                                      {"JNT-1": 0.0}, 1.0, ["BOD-A", "BOD-B"])
        self.assertTrue(any(f.kind == findings.UNSUPPORTED_OPERATION for f in law.findings))
        self.assertNotIn("BOD-B", law.poses)

    def test_13_motion_is_sampled_as_s04_samples(self):
        samples, declaration = kinematics.motion_samples({"JNT-1": 0.0}, {"JNT-1": 90.0}, ["JNT-1"])
        self.assertEqual(s04.SAMPLES, len(samples))
        self.assertEqual((0.0, 90.0), (samples[0]["JNT-1"], samples[-1]["JNT-1"]))
        self.assertFalse(declaration["adaptive"])


# ======================================================================
class TestCompletenessMeansConstructible(unittest.TestCase):

    def test_14_an_unrealized_joint_and_a_bodiless_stock_are_named(self):
        state = DesignState(run_id="c")
        hinge_upstream(state)
        problems = embodiment.structural_problems(embodiment.rows_from_state(state, None))
        self.assertTrue(any("JNT-1" in p and "BOD-A" in p for p in problems), problems)
        self.assertTrue(any("BOD-B has no additive feature" in p for p in problems), problems)

    def test_15_a_complete_embodiment_has_no_structural_problem(self):
        self.assertEqual([], embodiment.structural_problems(embodiment.rows_from_state(hinge(), None)))

    def test_16_the_settlement_gate_refuses_a_non_constructible_embodiment(self):
        state = DesignState(run_id="g")
        hinge_upstream(state)
        self.assertEqual([], apply(state, "s05", [
            feature("FEA-1", "BOD-A", "STOCK", "ENV-A", [box("b", MM(1), MM(1), MM(1))], axis="+Z")]))
        report, execution = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.NOT_READY, report.solver_status)
        self.assertTrue(any("JNT-1" in p for p in report.problems), report.problems)

    def test_17_s05_reports_the_grammar_and_the_structure_by_name_before_writing(self):
        state = DesignState(run_id="v")
        hinge_upstream(state)
        view = {fam: state.standing(fam) for fam in ("Body", "RigidGroup", "Joint", "Interface",
                                                    "Envelope", "FunctionalRegion")}
        response = {"features": [{"id": "FEA-1", "body": "BOD-A", "feature_kind": "BORE",
                                  "geometry": "x",
                                  "placement": {"datum": "JNT-1", "axis": "+Z"},
                                  "construction": [cylinder("c", MM(1), MM(1))]}],
                    "parameters": []}
        c5 = s05.check_c5_program_totality(response, view)
        self.assertEqual([], c5, "a feature at a joint may be oriented as it likes")
        c11 = s05.check_c11_joints_realized(response, view)
        self.assertTrue(any("JNT-1" in p for p in c11), c11)
        self.assertTrue(any("no KinematicRealization names it" in p for p in c11),
                        "placement is not realization: the claim is what is read")
        c12 = s05.check_c12_bodies_built(response, view)
        self.assertEqual(2, len(c12), c12)

    def test_18_mating_kinds_are_checked_against_s04s_mating_geometry(self):
        rows = {"Body": [], "RigidGroup": [], "Joint": [],
                "Interface": [{"entity_id": "IFC-1", "bodies": ["BOD-A", "BOD-B"],
                               "mating_geometry": {"inner_feature": "PIN", "outer_feature": "BORE",
                                                   "inner_body": "BOD-B", "outer_body": "BOD-A"}}],
                "Feature": [{"entity_id": "F1", "body": "BOD-A", "feature_kind": "BORE",
                             "interface": "IFC-1"},
                            {"entity_id": "F2", "body": "BOD-B", "feature_kind": "FACE",
                             "interface": "IFC-1"}]}
        found = embodiment.mating_kind_findings(rows)
        self.assertEqual(1, len(found), found)
        self.assertEqual(findings.MATING_KIND_UNREALIZED, found[0].kind)
        self.assertEqual("s05", found[0].owner)
        self.assertIn("PIN", found[0].detail)


# ======================================================================
class TestGatesRefuseWhatS07WouldInvent(unittest.TestCase):

    def test_19_an_unsettled_offset_parameter_blocks_compilation(self):
        state = hinge()
        self.assertEqual([], apply(state, "s05", [
            Op("CREATE", "Parameter", "PRM-H", {"symbol": "h", "unit": "mm", "status": ir.DECLARED},
               "s05:embodiment"),
            feature("FEA-L", "BOD-A", "LUG", "FEA-A-STOCK", [box("b", MM(5), MM(5), MM(5))],
                    offset=[MM(0), MM(0), REF("PRM-H")], axis="+Z", premises=["PRM-H"])]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.UNDERDETERMINED, report.solver_status)
        ready, why = canonical_io.compilation_readiness(state)
        self.assertFalse(ready)
        self.assertTrue(any("PRM-H" in w for w in why), why)

    def test_20_a_non_positive_settled_dimension_is_refused_before_the_kernel(self):
        state = hinge()
        self.assertEqual([], apply(state, "s05", [
            Op("SUPERSEDE", "Constraint", "CON-R", {"expression": {"relation": "==", "lhs": REF("PRM-R"),
                                                                    "rhs": MM(-3)}},
               "s05:embodiment", reason="a negative radius")]))
        report, _ = ex.execute_settlement(state, Progression())
        self.assertEqual(ir.FEASIBLE, report.solver_status)
        problems = settled_geometry.construction_problems(state)
        self.assertTrue(any("CONSTRUCTION_INVALID" in p and "FEA-A-BORE" in p for p in problems), problems)
        self.assertFalse(canonical_io.compilation_readiness(state)[0])

    def test_21_a_length_in_the_wrong_unit_is_refused_and_not_converted(self):
        state = hinge()
        self.assertEqual([], apply(state, "s05", [
            Op("CREATE", "Parameter", "PRM-M", {"symbol": "m", "unit": "m", "status": ir.DECLARED},
               "s05:embodiment"),
            Op("CREATE", "Constraint", "CON-M", {"kind": "DIMENSIONAL", "parameters": ["PRM-M"],
                                                 "expression": {"relation": "==", "lhs": REF("PRM-M"),
                                                                "rhs": {"const": 0.05, "unit": "m"}}},
               "s05:embodiment", premise_refs=["PRM-M"]),
            feature("FEA-M", "BOD-A", "BOSS", "FEA-A-STOCK", [cylinder("c", REF("PRM-M"), MM(2))],
                    axis="+Z", premises=["PRM-M"])]))
        ex.execute_settlement(state, Progression())
        problems = canonical_io.construction_unit_problems(state)
        self.assertTrue(any("FEA-M.c.radius" in p and "no conversion" in p for p in problems), problems)

    def test_21b_a_constraint_relates_quantities_of_one_dimension_or_does_not_stand(self):
        """Observed live: `length + 2` (dimensionless) == 5 mm reached settlement
        and failed there as an unsupported formulation. Dimension is
        well-formedness: the boundary asks the solver's own reduction before
        the record stands, and S05-C6 reports the same thing by name."""
        state = hinge()
        mixed = {"relation": "==", "lhs": {"op": "+", "args": [REF("PRM-W"), {"const": 2, "unit": "1"}]},
                 "rhs": MM(5)}
        problems = apply(state, "s05", [
            Op("CREATE", "Constraint", "CON-X", {"kind": "DIMENSIONAL", "parameters": ["PRM-W"],
                                                 "expression": mixed},
               "s05:embodiment", premise_refs=["PRM-W"])])
        self.assertTrue(any("combines dimensions" in p for p in problems), problems)
        self.assertNotIn("CON-X", state.entities)
        problems = apply(state, "s05", [
            Op("CREATE", "Constraint", "CON-Y", {"kind": "DIMENSIONAL", "parameters": ["PRM-W"],
                                                 "expression": {"relation": "==", "lhs": REF("PRM-W"),
                                                                "rhs": {"const": 5, "unit": "deg"}}},
               "s05:embodiment", premise_refs=["PRM-W"])])
        self.assertTrue(any("relates mm to deg" in p for p in problems), problems)
        # a bare zero asserts no dimension; a product of unknowns is the solver's
        # report, not the grammar's
        self.assertEqual([], apply(state, "s05", [
            Op("CREATE", "Constraint", "CON-Z", {"kind": "DIMENSIONAL", "parameters": ["PRM-W", "PRM-R"],
                                                 "expression": {"relation": ">=",
                                                                "lhs": {"op": "*", "args": [REF("PRM-W"), REF("PRM-R")]},
                                                                "rhs": {"const": 0, "unit": "1"}}},
               "s05:embodiment", premise_refs=["PRM-W", "PRM-R"])]))
        response = {"parameters": [{"id": "PRM-1", "symbol": "w", "unit": "mm"}],
                    "constraints": [{"id": "CON-1", "kind": "DIMENSIONAL", "parameters": ["PRM-1"],
                                     "expression": {"relation": "==", "lhs": REF("PRM-1"),
                                                    "rhs": {"const": 5, "unit": "deg"}}}]}
        self.assertTrue(any("CON-1" in p and "relates mm to deg" in p for p in s05.check_c6_units(response)))

    def test_22_findings_are_typed_and_owned(self):
        f = findings.Finding(findings.BODY_INTERFERENCE, "s05", ("BOD-A", "BOD-B"), "they overlap")
        self.assertEqual("s05", f.as_record()["owner"])
        with self.assertRaises(ValueError):
            findings.Finding("SOMETHING_ELSE", "s05", (), "x")
        self.assertEqual([], findings.blocking([findings.Finding(
            findings.NOT_EVALUABLE, "s04", (), "no scale", evaluable=False)]))


# ======================================================================
class TestTheModelIsShownTheLanguageTheBoundaryEnforces(unittest.TestCase):

    def test_23_the_grammar_and_schema_are_rendered_from_the_contract_and_the_ir(self):
        grammar = s05.S05Embodiment.render_grammar()
        for op in ir.OPCODES:
            self.assertIn(op, grammar)
        self.assertIn('"datum"', grammar)
        self.assertIn("negate", grammar)
        for axis in ir.SIGNED_AXES:
            self.assertIn('"%s"' % axis, grammar)
        schema = " ".join(s05.S05Embodiment.render_response_schema().split())
        self.assertIn('"placement"', schema)
        self.assertIn('"solid": <solid>', schema)
        self.assertIn('"realization_assignments"', schema)
        self.assertIn('"interface_assignments"', schema)
        # THE BOOKKEEPING IS GONE FROM THE SURFACE, not merely unused. A schema
        # that still teaches step ids leaves the old format as a fallback.
        for retired in ("construction", "operands", "terminal", "kinematic_realizations",
                        '"parameters"'):
            self.assertNotIn(retired, schema,
                             "%r is still taught by the response schema" % retired)
        slots = {name for _, name, _, _ in Formatter().parse(s05.PROMPT) if name}
        self.assertIn("STOCK", s05.PROMPT.format(**{k: "" for k in slots}))

    def test_23b_new_objects_are_named_by_local_key_and_never_by_canonical_id(self):
        """A canonical id for a record this response CREATES is unsayable.

        The dangling-future-id class of failure is closed by the schema, not by
        a check: the only ids in it name things the design has already
        committed.
        """
        import re
        schema = s05.S05Embodiment.render_response_schema()
        self.assertEqual([], re.findall(r'"[A-Z][A-Z0-9]*-\d+"', schema),
                         "the schema shows an instantiable canonical id")
        self.assertIn('"key": "<local key>"', schema)
        self.assertIn('"unit"', schema)
        self.assertIn("<Body id>", schema)
        self.assertIn("<Joint or ConstraintRelation id>", schema)

    def test_23c_the_duties_are_rendered_from_the_topology_by_the_one_manifest(self):
        """The relations an embodiment must realize are ENUMERATED from s03's
        joints and groups - not left as a rule - and by the same manifest that
        validates the response and answers the settlement gate."""
        from ver3.assy_v3.downstream import duty_manifest

        state = DesignState(run_id="jd")
        hinge_upstream(state, joint_type="PRISMATIC", axis="+X")
        view = {fam: state.standing(fam) for fam in
                ("Joint", "RigidGroup", "Body", "Interface", "ConstraintRelation",
                 "ReferenceScale")}
        manifest = duty_manifest.from_rows(view)
        block = manifest.render()
        for token in ("JNT-1", "PRISMATIC", "+X", "BOD-A, BOD-B"):
            self.assertIn(token, block)
        self.assertEqual(("JNT-1",), manifest.required_realization_targets())
        self.assertIn("none", duty_manifest.from_rows({}).render())
        prompt = s05.S05Embodiment().prompt({"consumer_view": view})
        self.assertIn("DUTIES OF THIS EMBODIMENT", prompt)
        section = prompt.split("DUTIES OF THIS EMBODIMENT")[1].split("OBLIGATION DUTIES")[0]
        self.assertIn("JNT-1", section)

    # THE PRODUCER'S PREMISES moved to `test_s05_authoring_boundary`. The
    # property - a Feature rests on its body, its datum, the scale that datum's
    # coordinates are in, every interaction it realizes and every parameter it
    # reads - is a property of the semantic boundary, and it is asserted where
    # that boundary is exercised rather than against a fixture that has to
    # guess which datum the builder chose.


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
