"""THE S05 AUTHORING BOUNDARY - the one focused target for the migration.

What is under test is the seam between what a provider may say and what
production derives: the duty manifest, exact coverage of it, local-key
resolution, the solid-tree lowering and its single-terminal guarantee, the
typed constraint lowering, the KinematicRealization and interface lowering, and
the external reaction-site semantics.

THE CROSS-MECHANISM MATRIX IS THE POINT OF THE LAST SECTION. Every fixture
below is a different machine - multi-rail guidance, pads in a recess, a rod
free to rotate in its bore, a compliant retainer internal to one body, a screw
and nut, a crank-link-slider - and every one is answered by the SAME
mechanism-blind builder over the SAME manifest. If any rule in the boundary
were hinge-shaped, these would not pass together.
"""
from __future__ import annotations

import copy
import unittest
from typing import Any, Dict, List

from ver3.assy_v3.downstream import duty_manifest, embodiment, ir, lowering, semantic
from ver3.assy_v3.stages import s05_embodiment as s05
from ver3.assy_v3.stages.base import StageError
from ver3.tests.meta import _s05_semantic as S


# ==========================================================================
# Upstream fixtures. Plain rows: the manifest and the lowerer read rows, and
# building them directly keeps the subject of these tests the AUTHORING
# boundary rather than the write boundary (which section H exercises).
# ==========================================================================
def body(bid):
    return {"entity_id": bid, "role": bid}


def group(gid, bid):
    return {"entity_id": gid, "body": bid}


def joint(jid, parent, child, joint_type="REVOLUTE", axis="+Y", dof=("RY",)):
    return {"entity_id": jid, "parent_group": parent, "child_group": child,
            "joint_type": joint_type, "axis_direction": axis, "dof": list(dof),
            "frame_origin": [0, 0, 0], "frame_ids": ["FRM-%s" % jid]}


def interface(iid, bodies, kind="CONTACT", mating=None):
    rec = {"entity_id": iid, "bodies": list(bodies), "interaction_kind": kind}
    if mating:
        rec["mating_geometry"] = mating
    return rec


def relation(rid, retained_group, blocked=("TX",), provider_body=None,
             reaction_site=None):
    rec = {"entity_id": rid, "retained_group": retained_group,
           "blocked_dofs": list(blocked), "driver": "KINEMATIC_NECESSITY"}
    if provider_body:
        rec["provider_body"] = provider_body
    if reaction_site:
        rec["provider_reaction_site"] = reaction_site
    return rec


def envelope(eid, bid):
    return {"entity_id": eid, "body": bid,
            "extent": {"centre": [0, 0, 0], "half_extent": [10, 10, 10]}}


def upstream(bodies, groups, joints=(), interfaces=(), relations=(), basis="ABSOLUTE"):
    scale = {"entity_id": "SCL-1", "basis": basis}
    if basis == "ABSOLUTE":
        scale["absolute"] = {"unit": "mm", "per_unit": 1.0}
    return {"Body": [body(b) for b in bodies],
            "RigidGroup": [group(g, b) for g, b in groups],
            "Joint": list(joints), "Interface": list(interfaces),
            "ConstraintRelation": list(relations),
            "Envelope": [envelope("ENV-%s" % b, b) for b in bodies],
            "FunctionalRegion": [], "ReferenceScale": [scale]}


# ---- the mechanisms ------------------------------------------------------
def multi_rail_carriage():
    """Two rails and two carriages embodying ONE guided relation together."""
    return upstream(
        ["BOD-RAILBASE", "BOD-CARRIER"],
        [("RGP-1", "BOD-RAILBASE"), ("RGP-2", "BOD-CARRIER")],
        joints=[joint("JNT-SLIDE", "RGP-1", "RGP-2", "PRISMATIC", "+X", ["TX"])],
        interfaces=[interface("IFC-RAIL-L", ["BOD-RAILBASE", "BOD-CARRIER"], "CLEARANCE"),
                    interface("IFC-RAIL-R", ["BOD-RAILBASE", "BOD-CARRIER"], "CLEARANCE")],
        relations=[relation("CRL-LIFT", "RGP-2", ["TZ", "RY"],
                            provider_body="BOD-RAILBASE")])


def transverse_pads():
    """Three pads bearing on three recess walls - guidance with no guide part,
    and nothing aligned with the direction of travel."""
    return upstream(
        ["BOD-SLIDE", "BOD-HOUSING"],
        [("RGP-1", "BOD-SLIDE"), ("RGP-2", "BOD-HOUSING")],
        joints=[joint("JNT-TRAVEL", "RGP-2", "RGP-1", "PRISMATIC", "+Y", ["TY"])],
        interfaces=[interface("IFC-PAD-%d" % n, ["BOD-SLIDE", "BOD-HOUSING"], "CONTACT")
                    for n in (1, 2, 3)],
        relations=[relation("CRL-LATERAL", "RGP-1", ["TX", "TZ", "RX", "RZ"],
                            provider_body="BOD-HOUSING")])


def rod_in_plain_bore():
    """A rod in a bore with axial rotation deliberately LEFT FREE. The mating
    geometry states the two sides' kinds, so those kinds are duties."""
    return upstream(
        ["BOD-ROD", "BOD-BLOCK"],
        [("RGP-1", "BOD-ROD"), ("RGP-2", "BOD-BLOCK")],
        joints=[joint("JNT-CYL", "RGP-2", "RGP-1", "CYLINDRICAL", "+Z", ["TZ", "RZ"])],
        interfaces=[interface("IFC-FIT", ["BOD-ROD", "BOD-BLOCK"], "CLEARANCE",
                              mating={"inner_body": "BOD-ROD", "inner_feature": "SHAFT",
                                      "outer_body": "BOD-BLOCK", "outer_feature": "BORE"})],
        relations=[relation("CRL-RADIAL", "RGP-1", ["TX", "TY"],
                            provider_body="BOD-BLOCK")])


def compliant_retention():
    """A COMPLIANT joint INTERNAL to one body - two rigid groups of the same
    body - plus an interference retention against a second body."""
    return upstream(
        ["BOD-CLIP", "BOD-CATCH"],
        [("RGP-ROOT", "BOD-CLIP"), ("RGP-ARM", "BOD-CLIP"), ("RGP-CATCH", "BOD-CATCH")],
        joints=[joint("JNT-FLEX", "RGP-ROOT", "RGP-ARM", "COMPLIANT", "+X", ["RX"])],
        interfaces=[interface("IFC-SNAP", ["BOD-CLIP", "BOD-CATCH"], "INTERFERENCE_FIT")],
        relations=[relation("CRL-RETAIN", "RGP-CATCH", ["TZ"], provider_body="BOD-CLIP")])


def screw_and_nut():
    """A HELICAL pair: rotation at one end appears as translation at the other."""
    return upstream(
        ["BOD-SCREW", "BOD-NUT"],
        [("RGP-1", "BOD-SCREW"), ("RGP-2", "BOD-NUT")],
        joints=[joint("JNT-HELIX", "RGP-1", "RGP-2", "HELICAL", "+Z", ["TZ", "RZ"])],
        interfaces=[interface("IFC-THREAD", ["BOD-SCREW", "BOD-NUT"], "CONTACT",
                              mating={"inner_body": "BOD-SCREW", "inner_feature": "SHAFT",
                                      "outer_body": "BOD-NUT", "outer_feature": "BORE"})],
        relations=[relation("CRL-ANTIROT", "RGP-2", ["RZ"], provider_body="BOD-SCREW")])


def crank_link_slider():
    """Four joints over three moving bodies and a frame - a closed loop, where
    no relation has anything to do with any other relation's axis."""
    return upstream(
        ["BOD-FRAME", "BOD-CRANK", "BOD-LINK", "BOD-SLIDER"],
        [("RGP-F", "BOD-FRAME"), ("RGP-C", "BOD-CRANK"),
         ("RGP-L", "BOD-LINK"), ("RGP-S", "BOD-SLIDER")],
        joints=[joint("JNT-CRANK", "RGP-F", "RGP-C", "REVOLUTE", "+Y", ["RY"]),
                joint("JNT-PIN1", "RGP-C", "RGP-L", "REVOLUTE", "+Y", ["RY"]),
                joint("JNT-PIN2", "RGP-L", "RGP-S", "REVOLUTE", "+Y", ["RY"]),
                joint("JNT-SLIDE", "RGP-F", "RGP-S", "PRISMATIC", "+X", ["TX"])],
        interfaces=[interface("IFC-J1", ["BOD-FRAME", "BOD-CRANK"], "CLEARANCE"),
                    interface("IFC-J2", ["BOD-CRANK", "BOD-LINK"], "CLEARANCE"),
                    interface("IFC-J3", ["BOD-LINK", "BOD-SLIDER"], "CLEARANCE"),
                    interface("IFC-WAY", ["BOD-FRAME", "BOD-SLIDER"], "CLEARANCE")],
        relations=[relation("CRL-WAY", "RGP-S", ["TY", "TZ", "RX", "RZ"],
                            provider_body="BOD-FRAME")])


def external_reaction_site():
    """A relation whose provider is OUTSIDE this design's body set."""
    return upstream(
        ["BOD-PART"], [("RGP-1", "BOD-PART")],
        relations=[relation("CRL-EXT", "RGP-1", ["TX", "TY", "TZ"],
                            reaction_site="RSR-1")])


MECHANISMS = {
    "multi-rail / multi-carriage": multi_rail_carriage,
    "transverse pads in a recess": transverse_pads,
    "rod in a plain bore, rotation free": rod_in_plain_bore,
    "compliant retention": compliant_retention,
    "screw and nut": screw_and_nut,
    "crank / link / slider": crank_link_slider,
    "external reaction site": external_reaction_site,
}


def facts_for(view):
    return lowering.facts_from_rows(view)


def lower_ok(view, response=None, obligations=()):
    manifest = duty_manifest.from_rows(view, obligations_to_discharge=obligations)
    parsed = response if response is not None else S.minimal_response(view, obligations)
    return lowering.lower(semantic.SemanticResponse.parse(parsed), manifest, facts_for(view))


# ==========================================================================
# A. Duty manifest derivation
# ==========================================================================
class TestDutyManifestDerivation(unittest.TestCase):

    def test_every_joint_and_every_blocking_relation_is_a_required_target(self):
        view = crank_link_slider()
        manifest = duty_manifest.from_rows(view)
        self.assertEqual(
            {"JNT-CRANK", "JNT-PIN1", "JNT-PIN2", "JNT-SLIDE", "CRL-WAY"},
            set(manifest.required_realization_targets()))

    def test_a_relation_that_blocks_nothing_is_not_a_duty(self):
        view = upstream(["BOD-A"], [("RGP-1", "BOD-A")],
                        relations=[{"entity_id": "CRL-NOTE", "retained_group": "RGP-1",
                                    "blocked_dofs": []}])
        self.assertEqual((), duty_manifest.from_rows(view).required_realization_targets())

    def test_a_joint_whose_groups_resolve_to_no_body_is_skipped(self):
        view = upstream(["BOD-A"], [("RGP-1", "BOD-A")],
                        joints=[joint("JNT-X", "RGP-MISSING", "RGP-ALSO-MISSING")])
        self.assertEqual((), duty_manifest.from_rows(view).required_realization_targets())

    def test_an_external_reaction_site_owes_the_retained_side_only(self):
        """The thing bearing the load is outside this design's body set, and
        demanding a feature for it would force s05 to invent a body that is not
        the product."""
        manifest = duty_manifest.from_rows(external_reaction_site())
        duty = manifest.realization("CRL-EXT")
        self.assertEqual(("BOD-PART",), duty.bodies)
        self.assertEqual("RSR-1", duty.external_provider)
        self.assertIn("external reaction site RSR-1", duty.render())

    def test_a_provider_body_is_a_side_and_is_not_external(self):
        manifest = duty_manifest.from_rows(multi_rail_carriage())
        duty = manifest.realization("CRL-LIFT")
        self.assertEqual(("BOD-CARRIER", "BOD-RAILBASE"), tuple(sorted(duty.bodies)))
        self.assertIsNone(duty.external_provider)

    def test_only_a_clearance_or_interference_fit_owes_a_governing_constraint(self):
        manifest = duty_manifest.from_rows(rod_in_plain_bore())
        self.assertEqual(("IFC-FIT",), manifest.governed_interfaces())
        contact = duty_manifest.from_rows(transverse_pads())
        self.assertEqual((), contact.governed_interfaces())

    def test_stated_mating_geometry_becomes_a_per_side_kind_duty(self):
        duty = duty_manifest.from_rows(rod_in_plain_bore()).interface("IFC-FIT")
        self.assertEqual("SHAFT", duty.required_kind("BOD-ROD"))
        self.assertEqual("BORE", duty.required_kind("BOD-BLOCK"))
        self.assertIsNone(duty.required_kind("BOD-NOWHERE"))

    def test_a_relative_basis_owes_a_scale_and_an_absolute_one_does_not(self):
        self.assertTrue(duty_manifest.from_rows(
            upstream(["BOD-A"], [("RGP-1", "BOD-A")], basis="RELATIVE")).scale.required)
        self.assertFalse(duty_manifest.from_rows(
            upstream(["BOD-A"], [("RGP-1", "BOD-A")])).scale.required)

    def test_a_joint_that_declares_no_axis_is_listed_as_lending_none(self):
        view = upstream(["BOD-A", "BOD-B"], [("RGP-1", "BOD-A"), ("RGP-2", "BOD-B")],
                        joints=[joint("JNT-FIX", "RGP-1", "RGP-2", "FIXED", "NONE", [])])
        rendered = duty_manifest.from_rows(view).render()
        self.assertIn("LEND NO ORIENTATION", rendered)
        self.assertIn("JNT-FIX", rendered)

    def test_the_manifest_the_prompt_renders_is_the_manifest_that_validates(self):
        """One object. A duty the prompt never raises cannot be a check, and a
        check the prompt never raises cannot be a trap."""
        view = multi_rail_carriage()
        manifest = duty_manifest.from_rows(view)
        rendered = manifest.render()
        for target in manifest.required_realization_targets():
            self.assertIn(target, rendered)
        for iid in manifest.required_interfaces():
            self.assertIn(iid, rendered)


# ==========================================================================
# B. Exact coverage of the required targets
# ==========================================================================
class TestExactCoverage(unittest.TestCase):

    def setUp(self):
        self.view = multi_rail_carriage()
        self.manifest = duty_manifest.from_rows(self.view)
        self.response = S.minimal_response(self.view)

    def _problems(self, mutate):
        parsed = copy.deepcopy(self.response)
        mutate(parsed)
        return lowering.validate(semantic.SemanticResponse.parse(parsed),
                                 self.manifest, facts_for(self.view))

    def test_the_unmodified_response_discharges_every_duty(self):
        self.assertEqual([], lowering.validate(
            semantic.SemanticResponse.parse(self.response), self.manifest,
            facts_for(self.view)))

    def test_a_missing_target_is_refused(self):
        problems = self._problems(
            lambda p: p["realization_assignments"].pop("CRL-LIFT"))
        self.assertTrue(any("omits CRL-LIFT" in p for p in problems), problems)

    def test_an_extra_target_is_refused(self):
        problems = self._problems(
            lambda p: p["realization_assignments"].update(
                {"JNT-INVENTED": {"BOD-CARRIER": ["stock_BOD-CARRIER"]}}))
        self.assertTrue(any("JNT-INVENTED" in p and "no relation this branch owes" in p
                            for p in problems), problems)

    def test_an_empty_side_is_refused(self):
        problems = self._problems(
            lambda p: p["realization_assignments"]["JNT-SLIDE"].__setitem__("BOD-CARRIER", []))
        self.assertTrue(any("assigns no feature" in p for p in problems), problems)

    def test_a_missing_required_side_is_refused(self):
        """The side is a KEY that must be filled in, not a body that has to be
        spotted missing from a flat list."""
        problems = self._problems(
            lambda p: p["realization_assignments"]["JNT-SLIDE"].pop("BOD-CARRIER"))
        self.assertTrue(any("states no side for BOD-CARRIER" in p for p in problems),
                        problems)

    def test_a_side_the_relation_does_not_relate_is_refused(self):
        problems = self._problems(
            lambda p: p["realization_assignments"]["JNT-SLIDE"].update(
                {"BOD-ELSEWHERE": ["stock_BOD-CARRIER"]}))
        self.assertTrue(any("does not relate" in p for p in problems), problems)

    def test_a_flat_participant_list_is_refused_outright(self):
        problems_raised = None
        parsed = copy.deepcopy(self.response)
        parsed["realization_assignments"]["JNT-SLIDE"] = ["stock_BOD-CARRIER"]
        try:
            semantic.SemanticResponse.parse(parsed)
        except semantic.SemanticError as exc:
            problems_raised = str(exc)
        self.assertIsNotNone(problems_raised, "a flat list was accepted")
        self.assertIn("SIDE BY SIDE", problems_raised)

    def test_a_feature_assigned_to_the_wrong_side_is_refused(self):
        problems = self._problems(
            lambda p: p["realization_assignments"]["JNT-SLIDE"].__setitem__(
                "BOD-CARRIER", ["stock_BOD-RAILBASE"]))
        self.assertTrue(any("which is on BOD-RAILBASE" in p for p in problems), problems)

    def test_an_interface_side_left_unassigned_is_refused(self):
        def drop_side(p):
            p["interface_assignments"]["IFC-RAIL-L"]["sides"].pop("BOD-CARRIER")
        problems = self._problems(drop_side)
        self.assertTrue(any("realizes no side on BOD-CARRIER" in p for p in problems),
                        problems)

    def test_a_governing_constraint_of_a_non_governing_kind_is_refused(self):
        """A constraint that NAMES an interface without governing it was a live
        failure: the response looked complete and the clearance was ungoverned."""
        def wrong_kind(p):
            p["interface_assignments"]["IFC-RAIL-L"]["governing_constraint"]["kind"] = \
                "DIMENSIONAL"
        problems = self._problems(wrong_kind)
        self.assertTrue(any("of kind DIMENSIONAL" in p for p in problems), problems)

    def test_one_constraint_cannot_be_shared_between_two_interfaces(self):
        """A live refusal: one constraint named as governing three clearances
        is ONE canonical record carrying ONE `governs_interface`, so two of the
        three read ungoverned. A governing constraint is now declared inside
        the assignment, so it cannot be shared and cannot dangle."""
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.InterfaceAssignment.parse(
                "IFC-1", {"sides": {"BOD-A": ["f"]}, "governing_constraint": "shared_key"})
        self.assertIn("would leave the others ungoverned", str(caught.exception))

    def test_each_governed_interface_gets_its_own_canonical_constraint(self):
        view = multi_rail_carriage()
        out = lower_ok(view)
        governed = {}
        for c in out.constraints:
            if c.get("governs_interface"):
                governed.setdefault(c["governs_interface"], []).append(c["entity_id"])
        self.assertEqual({"IFC-RAIL-L", "IFC-RAIL-R"}, set(governed))
        ids = [i for v in governed.values() for i in v]
        self.assertEqual(len(ids), len(set(ids)),
                         "one Constraint record was reused for two interfaces")

    def test_a_body_without_additive_material_is_refused(self):
        def strip(p):
            p["features"] = [f for f in p["features"]
                             if not (f["body"] == "BOD-CARRIER"
                                     and f["feature_kind"] in ("STOCK", "FACE"))]
            for target, sides in list(p["realization_assignments"].items()):
                p["realization_assignments"][target] = {
                    b: [k for k in ks if any(f["key"] == k for f in p["features"])]
                    for b, ks in sides.items()}
            for iid, a in list(p["interface_assignments"].items()):
                a["sides"] = {b: [k for k in ks if any(f["key"] == k for f in p["features"])]
                              for b, ks in a["sides"].items()}
        problems = self._problems(strip)
        self.assertTrue(any("no additive feature" in p for p in problems), problems)

    def test_a_stated_mating_kind_that_is_not_realized_is_refused(self):
        view = rod_in_plain_bore()
        manifest = duty_manifest.from_rows(view)
        parsed = S.minimal_response(view)
        for f in parsed["features"]:
            if f["key"] == "if_IFC-FIT_BOD-ROD":
                f["feature_kind"] = "FACE"
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed), manifest,
                                     facts_for(view))
        self.assertTrue(any("states a SHAFT on BOD-ROD" in p for p in problems), problems)


# ==========================================================================
# C. Local keys and reference resolution
# ==========================================================================
class TestLocalKeyResolution(unittest.TestCase):

    def test_a_canonical_looking_key_is_refused(self):
        """A dangling future canonical id is unsayable rather than caught."""
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticResponse.parse({
                "features": [{"key": "FEA-0001", "body": "BOD-A", "feature_kind": "STOCK",
                              "geometry": "g",
                              "placement": {"datum": {"kind": "ENVELOPE", "ref": "ENV-A"}},
                              "solid": {"shape": "SPHERE", "radius": {
                                  "kind": "number", "value": 1, "unit": "mm"}}}],
                "constraints": [], "realization_assignments": {},
                "interface_assignments": {}})
        self.assertIn("canonical entity id", str(caught.exception))

    def test_a_duplicate_feature_key_is_refused(self):
        def one(key):
            return {"key": key, "body": "BOD-A", "feature_kind": "STOCK", "geometry": "g",
                    "placement": {"datum": {"kind": "ENVELOPE", "ref": "ENV-A"}},
                    "solid": {"shape": "SPHERE", "radius": {"kind": "number", "value": 1,
                                                            "unit": "mm"}}}
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticResponse.parse({
                "features": [one("f"), one("f")], "constraints": [],
                "realization_assignments": {}, "interface_assignments": {}})
        self.assertIn("used twice", str(caught.exception))

    def test_a_parameter_cannot_dangle_because_using_one_declares_it(self):
        """The class of failure this correction removed. A `param` node names
        AND declares; there is no separate list to fall out of step with."""
        response = semantic.SemanticResponse.parse({
            "features": [{"key": "f", "body": "BOD-A", "feature_kind": "STOCK",
                          "geometry": "g",
                          "placement": {"datum": {"kind": "ENVELOPE", "ref": "ENV-A"}},
                          "solid": {"shape": "SPHERE", "radius": {
                              "kind": "param", "param": "r", "unit": "mm"}}}],
            "constraints": [], "realization_assignments": {}, "interface_assignments": {}})
        self.assertEqual({"r"}, set(response.parameters))
        self.assertEqual("mm", response.parameters["r"]["unit"])
        self.assertEqual("r", response.parameters["r"]["symbol"])

    def test_a_parameter_reference_without_a_unit_is_refused(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.TypedExpr.parse({"kind": "param", "param": "r"}, "e")
        self.assertIn("no unit", str(caught.exception))

    def test_two_mentions_of_one_name_must_agree(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticResponse.parse({
                "features": [{"key": "f", "body": "BOD-A", "feature_kind": "STOCK",
                              "geometry": "g",
                              "placement": {"datum": {"kind": "ENVELOPE", "ref": "ENV-A"}},
                              "solid": {"shape": "CYLINDER",
                                        "radius": {"kind": "param", "param": "r",
                                                   "unit": "mm"},
                                        "height": {"kind": "param", "param": "r",
                                                   "unit": "deg"}}}],
                "constraints": [], "realization_assignments": {},
                "interface_assignments": {}})
        self.assertIn("one unit and one role", str(caught.exception))

    def test_a_dangling_assignment_key_is_refused(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticResponse.parse({
                "features": [], "constraints": [],
                "realization_assignments": {"JNT-1": {"BOD-A": ["ghost"]}},
                "interface_assignments": {}})
        self.assertIn("does not declare", str(caught.exception))

    def test_an_interface_cannot_be_a_datum_at_all(self):
        """A datum is a PLACE. An Interface is an interaction between bodies,
        and a live response placed two features on one."""
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticDatum.parse({"kind": "INTERFACE", "ref": "IFC-1"}, "d")
        self.assertIn("not a place", str(caught.exception))

    def test_a_bare_string_datum_is_refused(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticDatum.parse("IFC-1", "d")
        self.assertIn("states WHAT KIND of place", str(caught.exception))

    def test_a_datum_must_resolve_in_the_family_it_declares(self):
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        parsed["features"][0]["placement"]["datum"] = {"kind": "JOINT",
                                                       "ref": "ENV-BOD-CARRIER"}
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed),
                                     duty_manifest.from_rows(view), facts_for(view))
        self.assertTrue(any("is a Envelope" in p or "is an Envelope" in p for p in problems),
                        problems)

    def test_a_datum_naming_nothing_committed_is_refused(self):
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        parsed["features"][0]["placement"]["datum"] = {"kind": "JOINT", "ref": "JNT-GHOST"}
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed),
                                     duty_manifest.from_rows(view), facts_for(view))
        self.assertTrue(any("no committed Joint" in p for p in problems), problems)

    def test_a_feature_datum_may_name_another_feature_by_key(self):
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        parsed["features"].append({
            "key": "on_stock", "body": "BOD-CARRIER", "feature_kind": "RIB",
            "geometry": "rib on the stock", "solid": {"shape": "SPHERE", "radius": {
                "kind": "param", "param": "thick", "unit": "mm"}},
            "placement": {"datum": {"kind": "FEATURE", "ref": "stock_BOD-CARRIER"},
                          "axis": "+Z"}})
        out = lower_ok(view, parsed)
        rib = next(f for f in out.features if f["feature_kind"] == "RIB")
        stock = next(f for f in out.features if f["feature_kind"] == "STOCK"
                     and f["body"] == "BOD-CARRIER")
        self.assertEqual(stock["entity_id"], rib["placement"]["datum"],
                         "a local feature datum was not resolved to its allocated id")

    def test_a_cycle_of_feature_datums_is_refused(self):
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        by_key = {f["key"]: f for f in parsed["features"]}
        a, b = "stock_BOD-CARRIER", "if_IFC-RAIL-L_BOD-CARRIER"
        by_key[a]["placement"] = {"datum": {"kind": "FEATURE", "ref": b}, "axis": "+Z"}
        by_key[b]["placement"] = {"datum": {"kind": "FEATURE", "ref": a}, "axis": "+Z"}
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed),
                                     duty_manifest.from_rows(view), facts_for(view))
        self.assertTrue(any("cycle of features" in p for p in problems), problems)

    def test_production_allocates_every_id_and_the_response_names_none(self):
        out = lower_ok(multi_rail_carriage())
        for record in out.features + out.parameters + out.constraints + \
                out.kinematic_realizations:
            self.assertRegex(record["entity_id"], r"^(FEA|PRM|CON|KRL)-\d{4}$")

    def test_allocation_skips_ids_state_already_holds(self):
        out = lowering.lower(
            semantic.SemanticResponse.parse(S.minimal_response(multi_rail_carriage())),
            duty_manifest.from_rows(multi_rail_carriage()),
            facts_for(multi_rail_carriage()),
            occupied={"Feature": ["FEA-0001", "FEA-0002"]})
        self.assertNotIn("FEA-0001", [f["entity_id"] for f in out.features])
        self.assertEqual("FEA-0003", out.features[0]["entity_id"])


# ==========================================================================
# D. The solid tree and its lowering
# ==========================================================================
class TestSolidLowering(unittest.TestCase):
    """The material a feature IS, and its lowering to the unchanged Step IR."""

    PARAMS = {"t": "PRM-0001"}

    def tree(self, node):
        return lowering.lower_solid(semantic.Solid.parse(node), self.PARAMS)

    def num(self, v=1.0):
        return {"kind": "number", "value": v, "unit": "mm"}

    def test_a_primitive_lowers_to_one_step_that_is_the_terminal(self):
        steps = self.tree({"shape": "SPHERE", "radius": self.num(3)})
        self.assertEqual(1, len(steps))
        self.assertEqual([], steps[0].get("operands", []))
        self.assertEqual("SPHERE", steps[0]["operation"])

    def test_each_shape_lowers_to_its_existing_opcode(self):
        for shape, node, opcode in (
                ("BLOCK", {"shape": "BLOCK", "dx": 1, "dy": 2, "dz": 3}, "BOX"),
                ("CYLINDER", {"shape": "CYLINDER", "radius": 1, "height": 2}, "CYLINDER"),
                ("SPHERE", {"shape": "SPHERE", "radius": 1}, "SPHERE")):
            with self.subTest(shape=shape):
                self.assertEqual(opcode, self.tree(node)[-1]["operation"])
        self.assertEqual("UNION", self.tree({"shape": "COMPOUND", "parts": [
            {"shape": "SPHERE", "radius": 1}, {"shape": "SPHERE", "radius": 2}]})[-1]["operation"])
        self.assertEqual("INTERSECT", self.tree({"shape": "COMMON", "parts": [
            {"shape": "SPHERE", "radius": 1}, {"shape": "SPHERE", "radius": 2}]})[-1]["operation"])
        self.assertEqual("CUT", self.tree({"shape": "RELIEVED",
                                           "base": {"shape": "SPHERE", "radius": 2},
                                           "relief": [{"shape": "SPHERE", "radius": 1}]}
                                          )[-1]["operation"])

    def test_children_are_emitted_before_the_step_that_consumes_them(self):
        steps = self.tree({"shape": "RELIEVED",
                           "base": {"shape": "BLOCK", "dx": 1, "dy": 1, "dz": 1},
                           "relief": [{"shape": "CYLINDER", "radius": 1, "height": 1}]})
        order = [st["id"] for st in steps]
        consumer = steps[-1]
        for operand in consumer["operands"]:
            self.assertLess(order.index(operand), order.index(consumer["id"]),
                            "a step consumes a later step")

    def test_the_base_is_the_first_operand_of_the_difference(self):
        """A relief is taken out of the BASE, and the IR reads the first
        operand as the thing being reduced."""
        steps = self.tree({"shape": "RELIEVED",
                           "base": {"shape": "BLOCK", "dx": 9, "dy": 9, "dz": 9},
                           "relief": [{"shape": "SPHERE", "radius": 1}]})
        cut = steps[-1]
        base = next(st for st in steps if st["operation"] == "BOX")
        self.assertEqual(base["id"], cut["operands"][0])

    def test_exactly_one_step_is_unconsumed_however_deep(self):
        deep = {"shape": "COMPOUND", "parts": [
            {"shape": "RELIEVED", "base": {"shape": "BLOCK", "dx": 1, "dy": 1, "dz": 1},
             "relief": [{"shape": "SPHERE", "radius": 1}]},
            {"shape": "AT", "offset": [0, 0, 4], "turn": {"axis": "Z", "angle": 90},
             "of": {"shape": "CYLINDER", "radius": 1, "height": 1}}]}
        steps = self.tree(deep)
        consumed = {o for st in steps for o in st.get("operands", [])}
        finals = [st["id"] for st in steps if st["id"] not in consumed]
        self.assertEqual(1, len(finals), "the tree produced %d results" % len(finals))
        self.assertEqual(steps[-1]["id"], finals[0], "the root is not the terminal")

    def test_the_lowered_program_reads_as_the_executable_ir(self):
        steps = self.tree({"shape": "RELIEVED",
                           "base": {"shape": "BLOCK", "dx": 1, "dy": 1, "dz": 1},
                           "relief": [{"shape": "CYLINDER", "radius": 1, "height": 1}]})
        spec = ir.FeatureSpec.parse({
            "entity_id": "FEA-0001", "body": "BOD-A", "feature_kind": "BORE",
            "geometry": "g", "placement": {"datum": "ENV-A", "axis": "+Z"},
            "construction": steps})
        self.assertEqual(steps[-1]["id"], spec.terminal)

    def test_identical_semantic_input_lowers_to_identical_ir(self):
        node = {"shape": "COMPOUND", "parts": [
            {"shape": "BLOCK", "dx": 1, "dy": 2, "dz": 3},
            {"shape": "SPHERE", "radius": 4}]}
        self.assertEqual(self.tree(copy.deepcopy(node)), self.tree(copy.deepcopy(node)))

    def test_at_turns_before_it_offsets(self):
        steps = self.tree({"shape": "AT", "offset": [1, 0, 0],
                           "turn": {"axis": "Y", "angle": 30},
                           "of": {"shape": "SPHERE", "radius": 1}})
        self.assertEqual(["SPHERE", "ROTATE", "TRANSLATE"],
                         [st["operation"] for st in steps])

    def test_body_subtraction_cannot_be_expressed_at_all(self):
        """The unary CUT that meant 'remove this feature from its body' has no
        spelling: the only difference names a base AND at least one relief, and
        no shape names the body."""
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.Solid.parse({"shape": "RELIEVED",
                                  "base": {"shape": "SPHERE", "radius": 1}})
        self.assertIn("relieves nothing", str(caught.exception))
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.Solid.parse({"shape": "RELIEVED",
                                  "relief": [{"shape": "SPHERE", "radius": 1}]})
        self.assertIn("that is the feature's KIND", str(caught.exception))

    def test_a_compiler_operation_is_refused_with_the_shapes_named(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.Solid.parse({"op": "CUT", "of": [{"shape": "SPHERE", "radius": 1}]})
        self.assertIn("described by its SHAPE", str(caught.exception))

    def test_a_combining_shape_needs_two_or_more_parts(self):
        for shape in ("COMPOUND", "COMMON"):
            with self.subTest(shape=shape):
                with self.assertRaises(semantic.SemanticError):
                    semantic.Solid.parse({"shape": shape,
                                          "parts": [{"shape": "SPHERE", "radius": 1}]})

    def test_a_primitive_missing_a_dimension_is_refused_not_defaulted(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.Solid.parse({"shape": "CYLINDER", "radius": 1})
        self.assertIn("omits required dimension", str(caught.exception))

    def test_a_turn_must_name_a_real_axis(self):
        with self.assertRaises(semantic.SemanticError):
            semantic.Solid.parse({"shape": "AT", "turn": {"axis": "W", "angle": 5},
                                  "of": {"shape": "SPHERE", "radius": 1}})

    def test_no_step_id_ordering_or_terminal_can_be_authored(self):
        for extra in ({"id": "S9"}, {"operands": ["S1"]}, {"terminal": True}):
            node = dict({"shape": "SPHERE", "radius": 1}, **extra)
            with self.assertRaises(semantic.SemanticError):
                semantic.Solid.parse(node)


class TestContextualLiterals(unittest.TestCase):
    """Where the FIELD fixes the dimension, a plain number is the quantity."""

    def test_a_shape_dimension_may_be_a_plain_number(self):
        solid = semantic.Solid.parse({"shape": "BLOCK", "dx": 2, "dy": 3, "dz": 4})
        step = lowering.lower_solid(solid, {})[0]
        self.assertEqual({"const": 2.0, "unit": "mm"}, step["parameters"]["dx"])

    def test_a_placement_offset_may_be_a_plain_number(self):
        placement = semantic.SemanticPlacement.parse(
            {"datum": {"kind": "ENVELOPE", "ref": "ENV-A"}, "offset": [1, 0, -2]}, "p")
        self.assertEqual(1.0, placement.offset[0].value)
        self.assertEqual("mm", placement.offset[0].unit)
        self.assertEqual(-2.0, placement.offset[2].value)

    def test_a_turn_angle_may_be_a_plain_number_and_is_degrees(self):
        turn = semantic.Turn.parse({"axis": "Z", "angle": 45}, "t")
        self.assertEqual("deg", turn.angle.unit)

    def test_a_constraint_still_refuses_a_bare_number(self):
        """The one place the dimension is what is under discussion."""
        with self.assertRaises(semantic.SemanticError):
            semantic.SemanticConstraint.parse(
                {"kind": "ENVELOPE", "basis": "DESIGN_CHOICE", "relation": "==",
                 "lhs": {"kind": "param", "param": "a", "unit": "mm"}, "rhs": 4}, "c")


# ==========================================================================
# E. Typed constraints
# ==========================================================================
class TestTypedConstraintLowering(unittest.TestCase):

    PARAMS = {"a": "PRM-0001", "b": "PRM-0002"}

    def lower(self, node):
        return lowering.lower_expression(semantic.TypedExpr.parse(node, "e"), self.PARAMS)

    def test_each_typed_form_lowers_to_the_canonical_ast(self):
        self.assertEqual({"ref": "PRM-0001"},
                         self.lower({"kind": "param", "param": "a", "unit": "mm"}))
        self.assertEqual({"const": 2.0, "unit": "mm"},
                         self.lower({"kind": "number", "value": 2, "unit": "mm"}))
        self.assertEqual(
            {"op": "+", "args": [{"ref": "PRM-0001"}, {"ref": "PRM-0002"}]},
            self.lower({"kind": "sum", "terms": [
                {"kind": "param", "param": "a", "unit": "mm"},
                {"kind": "param", "param": "b", "unit": "mm"}]}))
        self.assertEqual(
            {"op": "-", "args": [{"ref": "PRM-0001"}]},
            self.lower({"kind": "negate",
                        "of": {"kind": "param", "param": "a", "unit": "mm"}}))
        self.assertEqual(
            {"op": "*", "args": [{"ref": "PRM-0001"}, {"const": 100.0, "unit": "1"}]},
            self.lower({"kind": "scale_by",
                        "of": {"kind": "param", "param": "a", "unit": "mm"},
                        "factor": 100}))

    def test_every_lowered_expression_reads_as_the_existing_ir(self):
        node = {"kind": "difference",
                "left": {"kind": "sum", "terms": [
                    {"kind": "param", "param": "a", "unit": "mm"},
                    {"kind": "number", "value": 1, "unit": "mm"}]},
                "right": {"kind": "divide_by",
                          "of": {"kind": "param", "param": "b", "unit": "mm"},
                          "divisor": 2}}
        parsed = ir.Expr.parse(self.lower(node))
        self.assertEqual({"PRM-0001", "PRM-0002"}, parsed.refs())

    def test_a_literal_with_no_unit_is_unsayable(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.TypedExpr.parse({"kind": "number", "value": 3}, "e")
        self.assertIn("defaulting", str(caught.exception))

    def test_a_product_of_two_parameters_is_unsayable(self):
        """The formulation the solver reports as unsupported cannot be written."""
        for attempt in ({"kind": "scale_by",
                         "of": {"kind": "param", "param": "a", "unit": "mm"},
                         "factor": {"kind": "param", "param": "b", "unit": "mm"}},
                        {"kind": "product", "terms": []}):
            with self.assertRaises(semantic.SemanticError):
                semantic.TypedExpr.parse(attempt, "e")

    def test_constraint_parameters_are_derived_and_cannot_be_authored(self):
        view = multi_rail_carriage()
        out = lower_ok(view)
        for record in out.constraints:
            used = ir.TypedConstraint.parse(record).refs()
            self.assertEqual(sorted(used), record["parameters"],
                             "the derived list and the expression disagree")
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticConstraint.parse(
                {"kind": "ENVELOPE", "relation": "==",
                 "lhs": {"kind": "param", "param": "a", "unit": "mm"},
                 "rhs": {"kind": "number", "value": 1, "unit": "mm"},
                 "parameters": ["PRM-0001"]}, "c")
        self.assertIn("already names every parameter", str(caught.exception))

    def test_a_constraint_carries_no_key_because_nothing_names_one(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticConstraint.parse(
                {"key": "c", "kind": "ENVELOPE", "relation": "==",
                 "lhs": {"kind": "param", "param": "a", "unit": "mm"},
                 "rhs": {"kind": "number", "value": 1, "unit": "mm"}}, "c")
        self.assertIn("referenced by nothing", str(caught.exception))

    def test_a_parameter_no_constraint_determines_is_refused(self):
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        parsed["features"][0]["solid"] = {
            "shape": "SPHERE", "radius": {"kind": "param", "param": "loose", "unit": "mm"}}
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed),
                                     duty_manifest.from_rows(view), facts_for(view))
        self.assertTrue(any("free direction" in p for p in problems), problems)

    def test_a_parameter_may_not_carry_a_value(self):
        """There is nowhere to put one: a param node takes a name, a unit, a
        symbol and a role, and a value is not among them."""
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.TypedExpr.parse(
                {"kind": "param", "param": "t", "unit": "mm", "value": 4.0}, "e")
        self.assertIn("does not have", str(caught.exception))

    def test_a_dimensional_mismatch_is_refused_before_the_write(self):
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        parsed["constraints"].append({
            "kind": "DIMENSIONAL", "basis": "GEOMETRIC_RELATION",
            "relation": "==", "lhs": {"kind": "param", "param": "thick", "unit": "mm"},
            "rhs": {"kind": "number", "value": 1, "unit": "deg"}})
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed),
                                     duty_manifest.from_rows(view), facts_for(view))
        self.assertTrue(problems, "an angle equated to a length was accepted")


# ==========================================================================
# F. KinematicRealization and interface lowering
# ==========================================================================
class TestRealizationAndInterfaceLowering(unittest.TestCase):

    def test_one_row_per_required_target_with_a_production_id(self):
        view = crank_link_slider()
        out = lower_ok(view)
        targets = [r["realizes"] for r in out.kinematic_realizations]
        self.assertEqual(sorted(duty_manifest.from_rows(view).required_realization_targets()),
                         sorted(targets))
        self.assertEqual(len(targets), len(set(targets)),
                         "a target is claimed by more than one record")
        for row in out.kinematic_realizations:
            self.assertRegex(row["entity_id"], r"^KRL-\d{4}$")
            self.assertEqual({"entity_id", "realizes", "participating_features"}, set(row))

    def test_participating_features_are_the_assigned_features_resolved(self):
        view = multi_rail_carriage()
        response = S.minimal_response(view)
        out = lower_ok(view, response)
        row = next(r for r in out.kinematic_realizations if r["realizes"] == "JNT-SLIDE")
        duty = duty_manifest.from_rows(view).realization("JNT-SLIDE")
        sides = response["realization_assignments"]["JNT-SLIDE"]
        expected = [out.keys[k] for body in duty.bodies for k in sides[body]]
        self.assertEqual(expected, row["participating_features"],
                         "the participant list is not the sides flattened in manifest order")

    def test_a_kinematic_realization_cannot_be_authored_at_all(self):
        with self.assertRaises(semantic.SemanticError) as caught:
            semantic.SemanticResponse.parse({
                "parameters": [], "features": [], "constraints": [],
                "realization_assignments": {}, "interface_assignments": {},
                "kinematic_realizations": [{"id": "KRL-1", "realizes": "JNT-1",
                                            "participating_features": []}]})
        self.assertIn("no longer authors", str(caught.exception))

    def test_the_feature_interface_field_is_written_from_the_assignment(self):
        view = rod_in_plain_bore()
        out = lower_ok(view)
        realizing = [f for f in out.features if "IFC-FIT" in (f.get("interfaces") or [])]
        self.assertEqual({"BOD-ROD", "BOD-BLOCK"}, {f["body"] for f in realizing})
        self.assertEqual({"SHAFT", "BORE"}, {f["feature_kind"] for f in realizing})

    def test_one_feature_may_realize_several_interactions(self):
        """A rail face carries two carriages; a pin passes through two bores.
        ONE physical feature, several declared interfaces - and the record
        stays one, because duplicating it would be material the body does not
        have."""
        view = multi_rail_carriage()
        parsed = S.minimal_response(view)
        shared = parsed["interface_assignments"]["IFC-RAIL-L"]["sides"]["BOD-CARRIER"][0]
        parsed["interface_assignments"]["IFC-RAIL-R"]["sides"]["BOD-CARRIER"] = [shared]
        parsed["features"] = [f for f in parsed["features"]
                              if f["key"] != "if_IFC-RAIL-R_BOD-CARRIER"]
        self.assertEqual([], lowering.validate(
            semantic.SemanticResponse.parse(parsed), duty_manifest.from_rows(view),
            facts_for(view)))
        out = lower_ok(view, parsed)
        record = next(f for f in out.features if f["entity_id"] == out.keys[shared])
        self.assertEqual(["IFC-RAIL-L", "IFC-RAIL-R"], sorted(record["interfaces"]))
        rows = embodiment.rows_from_response(s05.lowered_as_parsed(out), view)
        self.assertEqual([], embodiment.structural_problems(rows),
                         "a feature realizing two interfaces did not satisfy both sides")

    def test_the_canonical_feature_carries_a_list_of_interfaces(self):
        out = lower_ok(rod_in_plain_bore())
        realizing = [f for f in out.features if f.get("interfaces")]
        self.assertTrue(realizing)
        for record in realizing:
            self.assertIsInstance(record["interfaces"], list)
            ir.FeatureSpec.parse(record)      # the IR reads the multi-reference

    def test_the_governing_constraint_is_written_as_governs_interface(self):
        view = rod_in_plain_bore()
        out = lower_ok(view)
        governing = [c for c in out.constraints if c.get("governs_interface") == "IFC-FIT"]
        self.assertEqual(1, len(governing))
        self.assertIn(governing[0]["kind"], lowering.GOVERNING_KINDS)

    def test_realization_is_read_only_from_the_assignment(self):
        """Not from a name, not from an axis that happens to match, not from a
        count of one feature per relation. The features embodying JNT-CYL below
        are ordinary faces on both bodies and are named nothing special."""
        view = rod_in_plain_bore()
        out = lower_ok(view)
        row = next(r for r in out.kinematic_realizations if r["realizes"] == "JNT-CYL")
        kinds = {f["feature_kind"] for f in out.features
                 if f["entity_id"] in row["participating_features"]}
        self.assertNotIn("BEARING", kinds)
        self.assertTrue(row["participating_features"])


# ==========================================================================
# G. THE CROSS-MECHANISM MATRIX
# ==========================================================================
class TestTheBoundaryIsNotMechanismSpecific(unittest.TestCase):
    """The same builder, the same manifest and the same lowerer over six
    different machines and an external reaction site."""

    def test_every_mechanism_lowers_and_leaves_no_duty_outstanding(self):
        for name, build in sorted(MECHANISMS.items()):
            with self.subTest(mechanism=name):
                view = build()
                manifest = duty_manifest.from_rows(view)
                out = lower_ok(view)
                rows = embodiment.rows_from_response(s05.lowered_as_parsed(out), view)
                self.assertEqual([], embodiment.structural_problems(rows),
                                 "%s left structural problems" % name)
                self.assertEqual([], s05.outstanding_duties(manifest, rows),
                                 "%s left duties outstanding" % name)

    def test_every_mechanism_lowers_to_a_readable_executable_ir(self):
        for name, build in sorted(MECHANISMS.items()):
            with self.subTest(mechanism=name):
                view = build()
                out = lower_ok(view)
                known = ir.Known(
                    parameters={p["entity_id"] for p in out.parameters},
                    datums={**{e["entity_id"]: "Envelope" for e in view["Envelope"]},
                            **{j["entity_id"]: "Joint" for j in view["Joint"]},
                            **{f["entity_id"]: "Feature" for f in out.features}},
                    feature_bodies={f["entity_id"]: f["body"] for f in out.features},
                    datum_bodies={e["entity_id"]: {e["body"]} for e in view["Envelope"]},
                    joint_axes={j["entity_id"]: j["axis_direction"] for j in view["Joint"]},
                    units={p["entity_id"]: p["unit"] for p in out.parameters})
                for record in out.features:
                    self.assertEqual([], ir.feature_record_problems(record, known),
                                     "%s: %s" % (name, record["entity_id"]))

    def test_no_mechanism_family_name_appears_in_the_production_boundary(self):
        """The rule that keeps this generic, asserted rather than trusted.

        DOCSTRINGS ARE EXCLUDED AND THAT IS THE POINT. Prose that explains why
        a rule is general - "three pads bearing on three recess walls embody
        guidance with no guide part at all" - is the reasoning, and naming the
        cases it must not break is how the reasoning is checked by a reader.
        What must contain no mechanism is the CODE: the identifiers it branches
        on and the messages it emits.
        """
        import ast
        import inspect

        banned = ("hinge", "latch", "snap_arm", "revolute", "prismatic", "helical",
                  "compliant", "carriage", "crank", "slider", "bm-001", "cnd-")
        for module in (duty_manifest, semantic, lowering):
            tree = ast.parse(inspect.getsource(module))
            docstrings = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)):
                    body = getattr(node, "body", None) or []
                    if body and isinstance(body[0], ast.Expr) and \
                            isinstance(body[0].value, ast.Constant) and \
                            isinstance(body[0].value.value, str):
                        docstrings.add(id(body[0].value))
            live: List[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and id(node) not in docstrings:
                    live.append(node.value)
                elif isinstance(node, ast.Name):
                    live.append(node.id)
                elif isinstance(node, ast.Attribute):
                    live.append(node.attr)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    live.append(node.name)
            source = " ".join(live).lower()
            for word in banned:
                with self.subTest(module=module.__name__, word=word):
                    self.assertNotIn(word, source,
                                     "%s branches on or reports a mechanism-specific name"
                                     % module.__name__)

    def test_the_manifest_and_the_standing_state_checks_require_the_same_thing(self):
        """Six surfaces, one derivation. What the manifest says is owed is
        exactly what the prerequisite findings ask of standing rows, for every
        mechanism - otherwise a branch could be accepted by one and refused by
        the other, which is how a design came to be settled while its own
        producing stage had declared an interface unrealized."""
        for name, build in sorted(MECHANISMS.items()):
            with self.subTest(mechanism=name):
                view = build()
                manifest = duty_manifest.from_rows(view)
                out = lower_ok(view)
                rows = embodiment.rows_from_response(s05.lowered_as_parsed(out), view)
                self.assertEqual([], embodiment.structural_problems(rows))
                self.assertEqual([], s05.outstanding_duties(manifest, rows))
                # and when a duty is removed from the ROWS, both surfaces object
                stripped = dict(rows)
                stripped["KinematicRealization"] = []
                by_manifest = s05.outstanding_duties(manifest, stripped)
                by_findings = embodiment.structural_problems(stripped)
                self.assertTrue(by_manifest and by_findings,
                                "%s: one surface accepted an embodiment the other refused"
                                % name)
                self.assertEqual(
                    len([d for d in manifest.realizations]), len(by_manifest),
                    "%s: the manifest and its own duty count disagree" % name)

    def test_the_external_reaction_site_never_demands_a_feature_for_it(self):
        view = external_reaction_site()
        out = lower_ok(view)
        bodies = {f["body"] for f in out.features}
        self.assertEqual({"BOD-PART"}, bodies,
                         "a body outside the design's body set was invented")
        row = next(r for r in out.kinematic_realizations if r["realizes"] == "CRL-EXT")
        self.assertTrue(row["participating_features"])


# ==========================================================================
# H. Through the stage, to operations - refuse whole or write whole
# ==========================================================================
class TestTheStageRefusesWholeOrWritesWhole(unittest.TestCase):

    def view(self):
        view = multi_rail_carriage()
        view["SelectionDecision"] = [{"entity_id": "SLD-1", "selected_candidate": "CND-1"}]
        return view

    def test_a_complete_response_becomes_operations_for_every_family(self):
        view = self.view()
        ops = s05.S05Embodiment().to_operations(S.minimal_response(view),
                                                {"consumer_view": view})
        families = {op.entity_type for op in ops}
        self.assertEqual({"Feature", "Parameter", "Constraint", "KinematicRealization"},
                         families)
        self.assertTrue(all(op.kind == "CREATE" for op in ops))

    def test_an_incomplete_response_produces_no_operation_at_all(self):
        """Not a partial patch with a declared incompleteness beside it: the
        fragment is what a later round would have to repair."""
        view = self.view()
        parsed = S.minimal_response(view)
        parsed["realization_assignments"].pop("JNT-SLIDE")
        with self.assertRaises(StageError) as caught:
            s05.S05Embodiment().to_operations(parsed, {"consumer_view": view})
        self.assertIn("JNT-SLIDE", str(caught.exception))

    def test_completeness_is_empty_for_a_response_that_was_accepted(self):
        view = self.view()
        self.assertEqual([], s05.S05Embodiment().completeness(
            S.minimal_response(view), {"consumer_view": view}))

    def test_every_output_carries_the_premises_it_was_derived_from(self):
        """A Feature rests on its body, the datum it is placed against, the
        scale that datum's coordinates are in, every interaction it realizes,
        and every parameter it reads. Without those, an entity is one no
        upstream change can ever stale."""
        view = self.view()
        view["ReferenceScale"] = [{"entity_id": "SCL-1", "basis": "ABSOLUTE",
                                   "absolute": {"unit": "mm", "per_unit": 1.0}}]
        ops = s05.S05Embodiment().to_operations(S.minimal_response(view),
                                                {"consumer_view": view})
        feature = next(op for op in ops if op.entity_type == "Feature"
                       and op.fields.get("interfaces"))
        self.assertIn(feature.fields["body"], feature.premise_refs)
        self.assertIn(feature.fields["placement"]["datum"], feature.premise_refs)
        self.assertIn("SCL-1", feature.premise_refs)
        for iid in feature.fields["interfaces"]:
            self.assertIn(iid, feature.premise_refs,
                          "an interaction the feature realizes is not a premise")
        self.assertTrue([p for p in feature.premise_refs if p.startswith("PRM-")],
                        "the parameters the feature reads are not premises")
        self.assertEqual([], [op for op in ops if op.entity_type == "ReferenceScale"],
                         "s04's scale record is never written by s05")
        realization = next(op for op in ops
                           if op.entity_type == "KinematicRealization")
        self.assertEqual([realization.fields["realizes"]], list(realization.premise_refs),
                         "a KinematicRealization rests on its target and nothing else")

    def test_the_prompt_renders_the_manifest_and_teaches_no_bookkeeping(self):
        """The manifest is rendered, and the retired FIELDS are unteachable.

        The test is over the field names a writer of the old format would need,
        not over prose: the instructions deliberately DENY those fields in
        words ("you never write construction steps or their order"), and a
        denial is the opposite of teaching one.
        """
        view = self.view()
        prompt = s05.S05Embodiment().prompt({"consumer_view": view})
        for target in duty_manifest.from_rows(view).required_realization_targets():
            self.assertIn(target, prompt)
        for retired in ('"construction"', '"operands"', '"kinematic_realizations"',
                        '"terminal"', '"op":'):
            self.assertNotIn(retired, prompt,
                             "the prompt still offers the retired field %s" % retired)
        # The constraint record specifically: its `parameters` list was the
        # duplicated authority, and the schema must not offer it. (The response
        # DOES have a top-level "parameters" collection - that is the
        # declarations themselves, and it stays.)
        schema = s05.S05Embodiment.render_response_schema()
        constraint_block = schema.split('"constraints"')[1].split('"realization_assignments"')[0]
        self.assertNotIn("parameters", constraint_block,
                         "the schema still offers a constraint-level parameters list")
        # Whitespace-normalised: the template wraps, and a denial that spans a
        # line break is the same denial.
        instructions = " ".join(prompt.split("DECIDED MECHANISM")[0].lower().split())
        for denial in ("you never write construction steps or their order",
                       "the tree has no ids, no ordering and no result to declare",
                       "production allocates every canonical id"):
            self.assertIn(denial, instructions,
                          "the prompt does not deny the retired surface: %r" % denial)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
