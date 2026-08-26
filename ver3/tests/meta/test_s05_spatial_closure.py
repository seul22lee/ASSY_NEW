"""S04 SPATIAL COMMITMENT -> S05 PHYSICAL DUTY -> S07 GEOMETRIC EVIDENCE.

s04's arrangement was visible to the s05 prompt and owed nothing. A branch
could declare an aperture, an embodiment could fill it with a solid, and every
structural check passed because none of them was about space. These tests are
the closure: what s04 commits becomes a duty s05 must route geometry to, and
what only a built solid can answer is carried to the stage that has one.

NOTHING BELOW READS A FEATURE NAME. A region duty comes from
`FunctionalRegion.role_policy`, a restraint duty from the coordinates a State
stands at, a path duty from a Transition. STOP, SLOT, RAIL, PIN and HINGE
appear in no rule.
"""
from __future__ import annotations

import copy
import unittest
from typing import Any, Dict, List

from ver3.assy_v3.downstream import duty_manifest, embodiment, ir, lowering, semantic
from ver3.assy_v3.stages import s05_embodiment as s05
from ver3.assy_v3.stages.base import StageError
from ver3.tests.meta import _s05_semantic as S
from ver3.tests.meta.test_s05_authoring_boundary import (
    MECHANISMS, body, envelope, facts_for, group, interface, joint, lower_ok, relation,
    upstream)


# ==========================================================================
# Fixtures that carry s04 spatial commitments
# ==========================================================================
def region(rid, role, bodies, centre=(0, 0, 0), half=(2, 2, 2)):
    return {"entity_id": rid, "role": role, "owning_bodies": list(bodies),
            "volume": {"centre": list(centre), "half_extent": list(half)}}


def state(sid, configuration, coordinates):
    return {"entity_id": sid, "name": sid, "configuration": configuration,
            "joint_coordinates": dict(coordinates)}


def transition(tid, frm, to, moving, changed, requirement=None):
    rec = {"entity_id": tid, "from_state": frm, "to_state": to,
           "path": {"moving_groups": list(moving)}, "changed_coordinates": list(changed)}
    if requirement:
        rec["realizes_requirement"] = requirement
    return rec


def requirement(rid, frm, to, motions, released=()):
    return {"entity_id": rid, "from_configuration": frm, "to_configuration": to,
            "required_relative_motions": [{"joint": j, "dof": d} for j, d in motions],
            "released_constraints": list(released)}


def assembly_step(sid, bodyid, order, direction=(0, 0, -1), access="+Z"):
    return {"entity_id": sid, "body": bodyid, "order_index": order,
            "access_side": access, "insertion_direction": list(direction),
            "activates": [], "depends_on": [], "termination_strategy": "SEAT",
            "path_kind": "RIGID"}


def housing_with_aperture():
    """A housing whose declared aperture a drawer passes through, with CLOSED
    and OPEN states at different coordinates of one prismatic joint."""
    view = upstream(
        ["BOD-HOUSING", "BOD-DRAWER"],
        [("RGP-H", "BOD-HOUSING"), ("RGP-D", "BOD-DRAWER")],
        joints=[joint("JNT-SLIDE", "RGP-H", "RGP-D", "PRISMATIC", "+X", ["TX"])],
        interfaces=[interface("IFC-WAY", ["BOD-HOUSING", "BOD-DRAWER"], "CLEARANCE")],
        relations=[dict(relation("CRL-CLOSED", "RGP-D", ["TX"],
                                 provider_body="BOD-HOUSING"),
                        configurations=["CFG-CLOSED"]),
                   dict(relation("CRL-OPEN", "RGP-D", ["TX"],
                                 provider_body="BOD-HOUSING"),
                        configurations=["CFG-OPEN"])])
    view["FunctionalRegion"] = [region("FRG-MOUTH", "APERTURE", ["BOD-HOUSING"]),
                                region("FRG-FOOT", "SUPPORT", ["BOD-HOUSING"])]
    view["Configuration"] = [{"entity_id": "CFG-CLOSED", "name": "closed"},
                             {"entity_id": "CFG-OPEN", "name": "open"}]
    view["State"] = [state("STA-CLOSED", "CFG-CLOSED", {"JNT-SLIDE": 0}),
                     state("STA-OPEN", "CFG-OPEN", {"JNT-SLIDE": 40})]
    view["TransitionRequirement"] = [
        requirement("TRQ-OUT", "CFG-CLOSED", "CFG-OPEN", [("JNT-SLIDE", "TX")],
                    released=["CRL-CLOSED"])]
    view["Transition"] = [transition("TRN-OUT", "STA-CLOSED", "STA-OPEN", ["RGP-D"],
                                     ["JNT-SLIDE"], "TRQ-OUT")]
    view["SweptVolume"] = [{"entity_id": "SWV-OUT", "transition": "TRN-OUT",
                            "rigid_group": "RGP-D", "fidelity": "SAMPLED",
                            "occupancy": {"aabb": [[-5, -5, -5], [45, 5, 5]]}}]
    view["AssemblyStep"] = [assembly_step("ASY-1", "BOD-HOUSING", 1),
                            assembly_step("ASY-2", "BOD-DRAWER", 2, direction=(-1, 0, 0))]
    return view


# ==========================================================================
# A. FunctionalRegion -> material-space duty
# ==========================================================================
class TestRegionDutyDerivation(unittest.TestCase):

    def setUp(self):
        self.manifest = duty_manifest.from_rows(housing_with_aperture())

    def test_a_role_that_excludes_occupancy_becomes_a_free_space_duty(self):
        self.assertEqual(("FRG-MOUTH",),
                         tuple(d.region for d in self.manifest.free_space_regions()))

    def test_a_role_that_expects_material_owes_nothing(self):
        """SUPPORT is where the product meets what carries it; occupancy is the
        POINT of the region."""
        foot = self.manifest.region("FRG-FOOT")
        self.assertFalse(foot.excludes_occupancy)
        self.assertNotIn("FRG-FOOT", [d.region for d in self.manifest.free_space_regions()])

    def test_the_policy_is_the_contract_s_and_no_role_is_named_in_code(self):
        """Every role the contract declares is honoured, whatever it is - the
        rule reads `excludes_occupancy`, never a role literal."""
        import inspect

        from ver3.assy_v3.stages.s04_envelope_and_motion import _region_policy
        policy = _region_policy()
        self.assertTrue(policy, "the contract declares no region policy")
        rows = dict(housing_with_aperture())
        rows["FunctionalRegion"] = [region("FRG-%d" % i, role, ["BOD-HOUSING"])
                                    for i, role in enumerate(sorted(policy))]
        derived = {d.region: d.excludes_occupancy
                   for d in duty_manifest.from_rows(rows).regions}
        for i, role in enumerate(sorted(policy)):
            self.assertEqual(bool(policy[role].get("excludes_occupancy")),
                             derived["FRG-%d" % i], role)
        source = inspect.getsource(duty_manifest)
        for role in policy:
            self.assertNotIn('"%s"' % role, source,
                             "the manifest names the role %s instead of reading the policy"
                             % role)

    def test_an_unknown_role_is_carried_and_never_assumed(self):
        rows = dict(housing_with_aperture())
        rows["FunctionalRegion"] = [region("FRG-X", "SOMETHING_NEW", ["BOD-HOUSING"])]
        duty = duty_manifest.from_rows(rows).region("FRG-X")
        self.assertFalse(duty.known_role)
        self.assertFalse(duty.excludes_occupancy)
        self.assertIn("not in the declared vocabulary", duty.render())

    def test_the_duty_is_rendered_to_the_prompt(self):
        rendered = self.manifest.render()
        self.assertIn("FRG-MOUTH", rendered)
        self.assertIn("MUST BE FREE", rendered)
        self.assertIn("ENVELOPE IS NOT MATERIAL", rendered)


# ==========================================================================
# B. The realization route, and Envelope != material
# ==========================================================================
class TestRegionRealizationRoute(unittest.TestCase):

    def setUp(self):
        self.view = housing_with_aperture()
        self.manifest = duty_manifest.from_rows(self.view)
        self.response = S.minimal_response(self.view)

    def _problems(self, mutate=None):
        parsed = copy.deepcopy(self.response)
        if mutate:
            mutate(parsed)
        return lowering.validate(semantic.SemanticResponse.parse(parsed), self.manifest,
                                 facts_for(self.view))

    def test_the_builder_s_response_routes_every_spatial_duty(self):
        self.assertEqual([], self._problems())

    def test_an_unassigned_free_space_region_is_refused(self):
        problems = self._problems(lambda p: p["region_assignments"].pop("FRG-MOUTH"))
        self.assertTrue(any("omits FRG-MOUTH" in p for p in problems), problems)

    def test_a_body_that_only_adds_material_clears_nothing(self):
        """The counterexample class: a solid body and an aperture inside it."""
        def additive(p):
            key = p["region_assignments"]["FRG-MOUTH"]["BOD-HOUSING"][0]
            for f in p["features"]:
                if f["key"] == key:
                    f["feature_kind"] = "STOCK"
        problems = self._problems(additive)
        self.assertTrue(any("ADDS material" in p for p in problems), problems)

    def test_clearing_geometry_must_sit_at_the_region(self):
        def elsewhere(p):
            key = p["region_assignments"]["FRG-MOUTH"]["BOD-HOUSING"][0]
            for f in p["features"]:
                if f["key"] == key:
                    f["placement"]["datum"] = {"kind": "ENVELOPE",
                                               "ref": "ENV-BOD-HOUSING"}
        problems = self._problems(elsewhere)
        self.assertTrue(any("clears a region by being AT it" in p for p in problems), problems)

    def test_a_region_that_owes_no_free_space_may_not_be_assigned(self):
        problems = self._problems(
            lambda p: p["region_assignments"].update({"FRG-FOOT": {"BOD-HOUSING": []}}))
        self.assertTrue(any("owes no free space" in p for p in problems), problems)

    def test_the_standing_state_asks_the_same_question(self):
        """One derivation. What s05 refuses, the settlement gate refuses too."""
        out = lower_ok(self.view, self.response)
        rows = embodiment.rows_from_response(s05.lowered_as_parsed(out), self.view)
        self.assertEqual([], embodiment.free_space_findings(rows))
        self.assertEqual([], s05.outstanding_duties(self.manifest, rows))
        stripped = dict(rows)
        stripped["Feature"] = [f for f in rows["Feature"]
                               if (f.get("placement") or {}).get("datum") != "FRG-MOUTH"]
        self.assertTrue(embodiment.free_space_findings(stripped))
        self.assertTrue(s05.outstanding_duties(self.manifest, stripped))
        self.assertTrue(embodiment.structural_problems(stripped),
                        "the S06 entry gate accepts an embodiment s05 would refuse")

    def test_the_prompt_no_longer_asks_for_an_envelope_filled_with_stock(self):
        view = dict(self.view)
        view["SelectionDecision"] = [{"entity_id": "SLD-1", "selected_candidate": "CND-X"}]
        instructions = s05.S05Embodiment().prompt(
            {"consumer_view": view}).split("DECIDED MECHANISM")[0]
        flat = " ".join(instructions.split())
        self.assertIn("AN ENVELOPE IS NOT MATERIAL", flat)
        self.assertNotIn("give each body one STOCK feature", flat)
        self.assertNotIn("placed at the body's Envelope, and place", flat)


# ==========================================================================
# C. Restraints stand at a position
# ==========================================================================
class TestStateCoordinateRestraints(unittest.TestCase):

    def setUp(self):
        self.view = housing_with_aperture()
        self.manifest = duty_manifest.from_rows(self.view)

    def test_a_relation_active_in_a_configuration_carries_its_coordinates(self):
        duties = {d.relation: d for d in self.manifest.state_restraints}
        self.assertEqual({"CRL-CLOSED", "CRL-OPEN"}, set(duties))
        self.assertEqual(0, duties["CRL-CLOSED"].joint_coordinates["JNT-SLIDE"])
        self.assertEqual(40, duties["CRL-OPEN"].joint_coordinates["JNT-SLIDE"])

    def test_two_limits_at_one_place_on_one_joint_are_refused(self):
        """The concrete defect, stated generically: one solid cannot stop a
        joint at two different positions."""
        parsed = S.minimal_response(self.view)
        closed = parsed["realization_assignments"]["CRL-CLOSED"]
        parsed["realization_assignments"]["CRL-OPEN"] = copy.deepcopy(closed)
        problems = lowering.validate(semantic.SemanticResponse.parse(parsed), self.manifest,
                                     facts_for(self.view))
        self.assertTrue(any("two different positions of the same joint" in p
                            for p in problems), problems)

    def test_distinct_placements_for_distinct_coordinates_pass(self):
        parsed = S.minimal_response(self.view)
        for f in parsed["features"]:
            if f["key"].startswith("rz_CRL-OPEN_"):
                f["placement"]["offset"] = [40, 0, 0]
        self.assertEqual([], lowering.validate(
            semantic.SemanticResponse.parse(parsed), self.manifest, facts_for(self.view)))

    def test_no_feature_name_is_consulted(self):
        import inspect
        import ast
        tree = ast.parse(inspect.getsource(lowering._state_restraint_problems).lstrip())
        body = tree.body[0].body
        rest = body[1:] if isinstance(body[0], ast.Expr) else body
        code = " ".join(ast.dump(n) for n in rest)
        for word in ("STOP", "SHOULDER", "KEEPER", "LATCH", "CAM", "PAD", "feature_kind"):
            self.assertNotIn(word, code,
                             "the rule reads %s instead of where the material sits" % word)

    def test_a_relation_naming_no_configuration_gets_no_coordinate_duty(self):
        rows = dict(housing_with_aperture())
        rows["ConstraintRelation"] = [relation("CRL-ALWAYS", "RGP-D", ["TZ"],
                                               provider_body="BOD-HOUSING")]
        self.assertEqual((), duty_manifest.from_rows(rows).state_restraints)


# ==========================================================================
# D. Motion, sweep and assembly duties are carried
# ==========================================================================
class TestCarriedSpatialDuties(unittest.TestCase):

    def setUp(self):
        self.manifest = duty_manifest.from_rows(housing_with_aperture())

    def test_required_motion_and_released_restraint_are_a_duty(self):
        duty = self.manifest.released_motions[0]
        self.assertEqual("TRN-OUT", duty.transition)
        self.assertEqual(("CRL-CLOSED",), duty.released_constraints)
        self.assertEqual((("JNT-SLIDE", "TX"),), duty.required_motions)

    def test_the_transition_and_its_swept_evidence_are_a_duty(self):
        duty = self.manifest.transitions[0]
        self.assertEqual(("RGP-D",), duty.moving_groups)
        self.assertEqual(("SWV-OUT",), duty.swept_volumes)

    def test_assembly_steps_carry_their_insertion_direction(self):
        steps = {d.step: d for d in self.manifest.assembly}
        self.assertEqual((-1.0, 0.0, 0.0), steps["ASY-2"].insertion_direction)
        self.assertEqual(1, steps["ASY-1"].order_index)

    def test_the_carried_duties_travel_to_whoever_can_answer_them(self):
        carried = s05.carried_spatial_duties(self.manifest)
        self.assertEqual(["FRG-MOUTH"], carried["free_space_regions"])
        self.assertEqual(["TRN-OUT"], carried["transitions"])
        self.assertTrue(carried["state_restraints"])
        self.assertTrue(carried["assembly"])

    def test_they_are_rendered_to_the_prompt_as_duties(self):
        rendered = self.manifest.render()
        for token in ("TRN-OUT", "CRL-CLOSED", "ASY-2", "PATHS ALREADY PROVED CLEAR"):
            self.assertIn(token, rendered)


# ==========================================================================
# E. The evidence route, and ownership
# ==========================================================================
class TestEvidenceRouteAndOwnership(unittest.TestCase):

    def test_the_artifact_report_declares_what_it_judged_against(self):
        from ver3.assy_v3.downstream import artifact
        self.assertIn("spatial_duties", artifact.ArtifactReport(branch=None).as_record())
        self.assertIn("assembly", artifact.ArtifactReport(branch=None).as_record())

    def test_a_region_intrusion_is_owned_by_the_embodiment_not_the_compiler(self):
        """s04 supplied a valid aperture; material in it is s05's choice."""
        import inspect
        source = inspect.getsource(embodiment.free_space_findings)
        self.assertIn("_finding(", source)
        finding = embodiment.free_space_findings(
            {**housing_with_aperture(), "Feature": []})[0]
        self.assertEqual("s05", finding.owner)

    def test_the_compiler_never_repairs_what_it_finds(self):
        """S07 evaluates and reports. It must not hollow, move or invent."""
        import inspect

        from ver3.assy_v3.downstream import artifact
        source = inspect.getsource(artifact.validate)
        for verb in ("Cut(", "MakeCut", "Fuse(", "MakeFuse"):
            self.assertNotIn(verb, source,
                             "the evidence pass modifies geometry instead of judging it")

    def test_every_spatial_finding_kind_is_in_the_declared_vocabulary(self):
        from ver3.assy_v3.downstream import findings as F
        for kind in (F.FEATURE_OUTSIDE_REGION, F.TRAVEL_BLOCKED, F.ASSEMBLY_BLOCKED,
                     F.BODY_INTERFERENCE, F.EMBODIMENT_INCOMPLETE):
            self.assertIn(kind, F.FINDING_KINDS)


# ==========================================================================
# F. Cross-mechanism: the same closure, no BM-001 shape
# ==========================================================================
class TestSpatialClosureIsNotMechanismSpecific(unittest.TestCase):

    def test_every_mechanism_still_lowers_with_the_spatial_duties_in_force(self):
        for name, build in sorted(MECHANISMS.items()):
            with self.subTest(mechanism=name):
                view = build()
                manifest = duty_manifest.from_rows(view)
                out = lower_ok(view)
                rows = embodiment.rows_from_response(s05.lowered_as_parsed(out), view)
                self.assertEqual([], embodiment.structural_problems(rows))
                self.assertEqual([], s05.outstanding_duties(manifest, rows))

    def test_a_free_space_region_on_any_mechanism_becomes_a_duty(self):
        """The rule is the region's, not the machine's."""
        for name, build in sorted(MECHANISMS.items()):
            with self.subTest(mechanism=name):
                view = build()
                first = view["Body"][0]["entity_id"]
                view["FunctionalRegion"] = [region("FRG-OPEN", "APERTURE", [first])]
                manifest = duty_manifest.from_rows(view)
                self.assertEqual(("FRG-OPEN",),
                                 tuple(d.region for d in manifest.free_space_regions()))
                out = lower_ok(view)
                rows = embodiment.rows_from_response(s05.lowered_as_parsed(out), view)
                self.assertEqual([], s05.outstanding_duties(manifest, rows),
                                 "%s did not route the region duty" % name)

    def test_no_mechanism_or_role_literal_appears_in_the_spatial_rules(self):
        """The CODE decides; the prose explains.

        Docstrings are excluded deliberately: naming the cases a rule must not
        break - "a stop face, a latch, a shoulder, a pad, a cam surface" - is
        how the reasoning is checked by a reader, and it is the opposite of
        branching on one. What must contain no mechanism and no role is what
        the rule actually reads and reports.
        """
        import ast
        import inspect

        banned = ("hinge", "drawer", "housing", "rail", "carriage", "latch", "snap",
                  "bm-001", "cnd-", "aperture", "keep_out", "'stop'", '"stop"')
        for fn in (duty_manifest.region_duties, duty_manifest.state_restraint_duties,
                   duty_manifest.transition_duties, duty_manifest.assembly_duties,
                   lowering._region_problems, lowering._state_restraint_problems,
                   embodiment.free_space_findings):
            tree = ast.parse(inspect.getsource(fn).lstrip())
            docs = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                     ast.Module)):
                    body = getattr(node, "body", None) or []
                    if body and isinstance(body[0], ast.Expr) \
                            and isinstance(body[0].value, ast.Constant) \
                            and isinstance(body[0].value.value, str):
                        docs.add(id(body[0].value))
            live: List[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and id(node) not in docs:
                    live.append(node.value)
                elif isinstance(node, ast.Name):
                    live.append(node.id)
                elif isinstance(node, ast.Attribute):
                    live.append(node.attr)
            source = " ".join(live).lower()
            for word in banned:
                with self.subTest(fn=fn.__name__, word=word):
                    self.assertNotIn(word, source)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
