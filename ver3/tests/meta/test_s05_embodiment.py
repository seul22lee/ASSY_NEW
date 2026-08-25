"""s05: the ten exit checks, each falsified against the failure it prevents.

The checks take the CONSUMER VIEW and the RESPONSE, so each one can be exercised
on its own with the exact state that trips it. That is deliberate: a check that
can only be run by driving the whole pipeline is a check nobody falsifies.

Every case below is built from the real field names the contracts declare -
`ConstraintRelation.retained_group` and `provider_body`, not a `bodies` field it
does not have; `Interface.interaction_kind` from s03's own four-value vocabulary;
`MobilityExpectation.dispositions` as the premise-record list it is. An earlier
draft of these checks guessed those names, and every one of them would have read
a missing key and passed silently.
"""

import unittest

from ver3.assy_v3.downstream import ir
from ver3.assy_v3.stages import s05_embodiment as s05
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment

MM = {"const": 1.0, "unit": "mm"}


def view(**families):
    return {k: list(v) for k, v in families.items()}


def feature(fid, body, kind="FACE", interface=None):
    out = {"id": fid, "body": body, "feature_kind": kind, "geometry": "a face"}
    if interface:
        out["interface"] = interface
    return out


def realization(rid, obligations, features, predicate="the gap stays positive"):
    return {"id": rid, "addresses_obligations": list(obligations),
            "participating_features": list(features),
            "verification_predicate": predicate}


class TestC1InterfaceFeatures(unittest.TestCase):
    """S05-C1: every Interface has a Feature on EACH participant."""

    V = view(Interface=[{"entity_id": "IFC-1", "bodies": ["BOD-1", "BOD-2"],
                         "interaction_kind": "CONTACT"}])

    def test_a_feature_on_each_side_passes(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1")]}
        self.assertEqual([], s05.check_c1_interface_features(parsed, self.V))

    def test_one_side_unrealised_is_reported(self):
        """Geometry that touches nothing. The other body has no surface to meet."""
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1")]}
        problems = s05.check_c1_interface_features(parsed, self.V)
        self.assertTrue(any("BOD-2" in p for p in problems), problems)

    def test_a_feature_on_the_body_that_names_no_interface_realizes_nothing(self):
        """Unit E: the trace is typed. Some feature on BOD-2 is not a feature
        that realizes IFC-1's side on BOD-2."""
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2")]}
        problems = s05.check_c1_interface_features(parsed, self.V)
        self.assertTrue(any("BOD-2" in p and "IFC-1" in p for p in problems), problems)

    def test_an_interface_the_branch_does_not_carry_may_not_be_named(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1"),
                               feature("FEA-9", "BOD-1", interface="IFC-INVENTED")]}
        problems = s05.check_c1_interface_features(parsed, self.V)
        self.assertTrue(any("IFC-INVENTED" in p and "invented" in p for p in problems),
                        problems)

    def test_a_body_the_interface_does_not_involve_cannot_realize_it(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1"),
                               feature("FEA-3", "BOD-3", interface="IFC-1")]}
        problems = s05.check_c1_interface_features(parsed, self.V)
        self.assertTrue(any("BOD-3" in p and "does not involve" in p for p in problems),
                        problems)


class TestC2BlockingPairs(unittest.TestCase):
    """S05-C2: every blocking relation has a feature pair.

    The two sides are `provider_body` and the body owning `retained_group`.
    """

    V = view(
        ConstraintRelation=[{"entity_id": "CRL-1", "retained_group": "RGP-1",
                             "provider_body": "BOD-2", "blocked_dofs": ["TZ"]}],
        RigidGroup=[{"entity_id": "RGP-1", "body": "BOD-1"}])

    def test_both_sides_carrying_geometry_passes(self):
        parsed = {"features": [feature("FEA-1", "BOD-1"), feature("FEA-2", "BOD-2")]}
        self.assertEqual([], s05.check_c2_blocking_pairs(parsed, self.V))

    def test_a_block_realized_on_one_side_only_is_reported(self):
        parsed = {"features": [feature("FEA-1", "BOD-1")]}
        problems = s05.check_c2_blocking_pairs(parsed, self.V)
        self.assertTrue(any("BOD-2" in p for p in problems), problems)

    def test_a_relation_blocking_nothing_is_not_a_block(self):
        """`blocked_dofs` is what makes it a constraint geometry must produce."""
        v = view(ConstraintRelation=[{"entity_id": "CRL-2", "retained_group": "RGP-1",
                                      "provider_body": "BOD-2", "blocked_dofs": []}],
                 RigidGroup=[{"entity_id": "RGP-1", "body": "BOD-1"}])
        self.assertEqual([], s05.check_c2_blocking_pairs({"features": []}, v))


class TestC3LimitPairs(unittest.TestCase):
    """S05-C3: a declared limit needs a PRODUCING pair, not merely a pair.

    C2 asks whether both sides carry geometry. This asks whether that geometry
    can stop anything - a clearance pocket on both sides satisfies C2 and stops
    nothing.
    """

    V = view(
        MobilityExpectation=[{"entity_id": "MEX-1", "configuration": "CFG-1",
                              "dispositions": [{"disposition": "BLOCKED_BY",
                                                "dof": "TZ",
                                                "constraint_relation": "CRL-1"}]}],
        ConstraintRelation=[{"entity_id": "CRL-1", "retained_group": "RGP-1",
                             "provider_body": "BOD-2", "blocked_dofs": ["TZ"]}],
        RigidGroup=[{"entity_id": "RGP-1", "body": "BOD-1"}])

    def test_a_stop_pair_produces_the_limit(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", "STOP"),
                               feature("FEA-2", "BOD-2", "SHOULDER")]}
        self.assertEqual([], s05.check_c3_limit_pairs(parsed, self.V))

    def test_geometry_that_cannot_stop_anything_is_reported(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", "CLEARANCE_POCKET"),
                               feature("FEA-2", "BOD-2", "CLEARANCE_POCKET")]}
        problems = s05.check_c3_limit_pairs(parsed, self.V)
        self.assertTrue(any("CRL-1" in p for p in problems), problems)

    def test_an_intended_disposition_demands_no_stop(self):
        """Only BLOCKED_BY is a limit. INTENDED motion is meant to happen."""
        v = view(MobilityExpectation=[{"entity_id": "MEX-2", "configuration": "CFG-1",
                                       "dispositions": [{"disposition": "INTENDED",
                                                         "dof": "RZ",
                                                         "by_joint": "JNT-1"}]}])
        self.assertEqual([], s05.check_c3_limit_pairs({"features": []}, v))


class TestC4ObligationsRealized(unittest.TestCase):
    """S05-C4: every Obligation is cited by a Realization carrying a predicate."""

    V = view(Obligation=[{"entity_id": "OBL-1"}, {"entity_id": "OBL-2"}])

    def test_full_coverage_with_predicates_passes(self):
        parsed = {"realizations": [realization("RLZ-1", ["OBL-1", "OBL-2"], ["FEA-1"])]}
        self.assertEqual([], s05.check_c4_obligations_realized(parsed, self.V))

    def test_an_uncited_obligation_is_reported(self):
        parsed = {"realizations": [realization("RLZ-1", ["OBL-1"], ["FEA-1"])]}
        problems = s05.check_c4_obligations_realized(parsed, self.V)
        self.assertTrue(any("OBL-2" in p for p in problems), problems)

    def test_a_citation_without_a_predicate_discharges_nothing(self):
        """INV-008. The citation does not count, so the obligation stays uncited."""
        parsed = {"realizations": [realization("RLZ-1", ["OBL-1", "OBL-2"], ["FEA-1"],
                                               predicate="  ")]}
        problems = s05.check_c4_obligations_realized(parsed, self.V)
        self.assertTrue(any("no verification predicate" in p for p in problems))
        self.assertTrue(any("OBL-1" in p for p in problems), problems)


class TestC5ProgramTotality(unittest.TestCase):
    """S05-C5: every symbol the program references is declared."""

    def test_a_declared_symbol_passes(self):
        parsed = {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm"}],
                  "construction_statements": [
                      {"id": "CST-1", "body": "BOD-1", "operation": "CYLINDER",
                       "parameters": {"radius": {"ref": "PRM-1"}, "height": MM}}]}
        self.assertEqual([], s05.check_c5_program_totality(parsed))

    def test_an_undeclared_symbol_is_reported_before_the_kernel_sees_it(self):
        parsed = {"parameters": [],
                  "construction_statements": [
                      {"id": "CST-1", "body": "BOD-1", "operation": "CYLINDER",
                       "parameters": {"radius": {"ref": "PRM-GHOST"}, "height": MM}}]}
        problems = s05.check_c5_program_totality(parsed)
        self.assertTrue(any("PRM-GHOST" in p for p in problems), problems)

    def test_a_nested_reference_is_found(self):
        parsed = {"parameters": [],
                  "construction_statements": [
                      {"id": "CST-1", "body": "BOD-1", "operation": "BOX",
                       "parameters": {"dx": {"op": "+", "args": [MM, {"ref": "PRM-X"}]},
                                      "dy": MM, "dz": MM}}]}
        self.assertTrue(any("PRM-X" in p for p in s05.check_c5_program_totality(parsed)))


class TestC6Units(unittest.TestCase):
    """S05-C6: no Parameter has a null unit. INV-004 / R-21."""

    def test_a_united_parameter_passes(self):
        self.assertEqual([], s05.check_c6_units(
            {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm"}]}))

    def test_a_null_unit_is_reported(self):
        for bad in (None, "", "   "):
            with self.subTest(unit=bad):
                problems = s05.check_c6_units(
                    {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": bad}]})
                self.assertTrue(problems)


class TestC7NoParameterCycle(unittest.TestCase):
    """S05-C7: no parameter dependency cycle."""

    @staticmethod
    def eq(cid, lhs, rhs):
        return {"id": cid, "kind": "ENVELOPE",
                "expression": {"relation": "==", "lhs": lhs, "rhs": rhs}}

    def test_a_chain_is_not_a_cycle(self):
        parsed = {"constraints": [
            self.eq("CON-1", {"ref": "PRM-B"}, {"op": "+", "args": [{"ref": "PRM-A"}, MM]}),
            self.eq("CON-2", {"ref": "PRM-C"}, {"op": "+", "args": [{"ref": "PRM-B"}, MM]})]}
        self.assertEqual([], s05.check_c7_no_parameter_cycle(parsed))

    def test_a_two_step_cycle_is_reported(self):
        """No ordering of the solve exists; it is a knot, not a definition set."""
        parsed = {"constraints": [
            self.eq("CON-1", {"ref": "PRM-A"}, {"op": "+", "args": [{"ref": "PRM-B"}, MM]}),
            self.eq("CON-2", {"ref": "PRM-B"}, {"op": "+", "args": [{"ref": "PRM-A"}, MM]})]}
        self.assertTrue(s05.check_c7_no_parameter_cycle(parsed))

    def test_an_inequality_defines_nothing_and_cannot_cycle(self):
        parsed = {"constraints": [
            {"id": "CON-1", "kind": "CLEARANCE",
             "expression": {"relation": ">=", "lhs": {"ref": "PRM-A"},
                            "rhs": {"ref": "PRM-B"}}},
            {"id": "CON-2", "kind": "CLEARANCE",
             "expression": {"relation": ">=", "lhs": {"ref": "PRM-B"},
                            "rhs": {"ref": "PRM-A"}}}]}
        self.assertEqual([], s05.check_c7_no_parameter_cycle(parsed))


def mm(v):
    return {"const": float(v), "unit": "mm"}


def box(cx, cy, cz, hx=1.0, hy=1.0, hz=1.0):
    """A fully constant envelope in millimetres (Unit E: never bare numbers)."""
    return {"centre": [mm(cx), mm(cy), mm(cz)],
            "half_extent": [mm(hx), mm(hy), mm(hz)]}


def region(rid, role, centre, half, bodies=("BOD-1",)):
    return {"entity_id": rid, "role": role, "owning_bodies": list(bodies),
            "volume": {"centre": list(centre), "half_extent": list(half)}}


#: The s04 basis a constant envelope is compared in: ABSOLUTE, one coordinate
#: per millimetre, so a constant of v mm is the coordinate v.
SCALE_MM = {"entity_id": "SCL-1", "basis": "ABSOLUTE",
            "absolute": {"unit": "mm", "per_unit": 1.0}}


class TestC8RegionIntrusion(unittest.TestCase):
    """S05-C8: real occupancy from canonical envelopes.

    The previous implementation read `intrudes_region` off the response - a key
    no contract declares and no producer emits - so it read None and passed on
    everything. These cases use `Feature.envelope`, which is canonical, and the
    same aabb/overlaps arithmetic s04b uses.
    """

    V = view(FunctionalRegion=[region("FRG-1", "ACCESS", (0, 0, 0), (5, 5, 5))],
             ReferenceScale=[SCALE_MM])

    def test_the_fixture_declares_a_usable_region(self):
        """Otherwise every case below passes for the wrong reason."""
        volume = self.V["FunctionalRegion"][0]["volume"]
        self.assertIn("centre", volume)
        self.assertIn("half_extent", volume)

    def test_a_feature_clearly_outside_the_region_passes(self):
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"),
                                    envelope=box(100, 100, 100))]}
        self.assertEqual([], s05.check_c8_region_intrusion(parsed, self.V))

    def test_a_feature_clearly_intruding_is_reported(self):
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"),
                                    envelope=box(0, 0, 0))]}
        problems = s05.check_c8_region_intrusion(parsed, self.V)
        self.assertTrue(any("FRG-1" in p for p in problems), problems)

    def test_a_touching_boundary_is_decided_deterministically(self):
        """Whatever the answer, it must be the SAME answer s04b would give -
        which is why the arithmetic is imported rather than reimplemented."""
        from ver3.assy_v3.stages.s04_envelope_and_motion import aabb, overlaps
        touching = box(6, 0, 0)          # region half-extent 5, feature half 1
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope=touching)]}
        numbers = lambda nodes: [n["const"] for n in nodes]           # noqa: E731
        expected = overlaps(aabb(numbers(touching["centre"]),
                                 numbers(touching["half_extent"])),
                            aabb([0, 0, 0], [5, 5, 5]))
        problems = s05.check_c8_region_intrusion(parsed, self.V)
        self.assertEqual(bool(expected), bool(problems))

    def test_a_feature_without_an_envelope_is_incomplete_not_clean(self):
        """The exact defect: silence about occupancy read as a pass."""
        parsed = {"features": [feature("FEA-1", "BOD-1")]}
        problems = s05.check_c8_region_intrusion(parsed, self.V)
        self.assertTrue(any("cannot be evaluated" in p for p in problems), problems)

    def test_a_support_region_permits_occupancy(self):
        """SUPPORT is where the product meets what carries it. Contact there is
        the POINT of the region, so reporting it would flag every design that
        actually rests on something.

        This used to use a role called GRIP, which the contract has never
        declared - so the test was asserting a policy for a role with no
        semantics, and the only thing it could prove was that an unknown role
        was silently ignored.
        """
        v = view(FunctionalRegion=[region("FRG-2", "SUPPORT", (0, 0, 0), (5, 5, 5))],
                 ReferenceScale=[SCALE_MM])
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope=box(0, 0, 0))]}
        self.assertEqual([], s05.check_c8_region_intrusion(parsed, v))

    def test_a_symbolic_envelope_is_deferred_not_judged(self):
        """Unit E. An envelope over declared parameters rests on dimensions
        settlement has not decided: no finding, and no claim of clearance."""
        parsed = {"parameters": [{"id": "PRM-R", "symbol": "r", "unit": "mm"}],
                  "features": [dict(feature("FEA-1", "BOD-1"), envelope={
                      "centre": [mm(0), mm(0), mm(0)],
                      "half_extent": [{"ref": "PRM-R"}, {"ref": "PRM-R"}, mm(1)]})]}
        self.assertEqual([], s05.check_c8_region_intrusion(parsed, self.V))

    def test_a_bare_number_in_an_envelope_is_refused(self):
        """Unit E. The contradiction removed: a number nobody solved."""
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope={
            "centre": [0, 0, 0], "half_extent": [mm(1), mm(1), mm(1)]})]}
        problems = s05.check_c8_region_intrusion(parsed, self.V)
        self.assertTrue(any("bare number" in p for p in problems), problems)
        # regions or no regions: the grammar is judged either way
        self.assertTrue(any("bare number" in p
                            for p in s05.check_c8_region_intrusion(parsed, view())))

    def test_an_undeclared_parameter_in_an_envelope_is_refused(self):
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope={
            "centre": [mm(0), mm(0), mm(0)],
            "half_extent": [{"ref": "PRM-NOBODY"}, mm(1), mm(1)]})]}
        problems = s05.check_c8_region_intrusion(parsed, self.V)
        self.assertTrue(any("PRM-NOBODY" in p for p in problems), problems)

    def test_a_relative_basis_defers_a_constant_envelope(self):
        """A constant in millimetres against a region in a RELATIVE basis is not
        comparable; nothing here invents the scale s04 left free."""
        v = view(FunctionalRegion=[region("FRG-1", "ACCESS", (0, 0, 0), (5, 5, 5))],
                 ReferenceScale=[{"entity_id": "SCL-1", "basis": "RELATIVE"}])
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope=box(0, 0, 0))]}
        self.assertEqual([], s05.check_c8_region_intrusion(parsed, v))

    def test_the_basis_factor_scales_a_constant_into_the_region_frame(self):
        """Ten millimetres per coordinate: a 100 mm centre is coordinate 10,
        which lies inside a region of half-extent 20 at the origin."""
        v = view(FunctionalRegion=[region("FRG-1", "ACCESS", (0, 0, 0), (20, 20, 20))],
                 ReferenceScale=[{"entity_id": "SCL-1", "basis": "ABSOLUTE",
                                  "absolute": {"unit": "mm", "per_unit": 10.0}}])
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope=box(100, 0, 0))]}
        problems = s05.check_c8_region_intrusion(parsed, v)
        self.assertTrue(any("FRG-1" in p for p in problems), problems)

    def test_an_undeclared_role_is_reported_rather_than_ignored(self):
        """An undeclared role has no occupancy policy. Passing it would be
        deciding the policy here, in a check, by omission."""
        v = view(FunctionalRegion=[region("FRG-9", "GRIP", (0, 0, 0), (5, 5, 5))],
                 ReferenceScale=[SCALE_MM])
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"), envelope=box(0, 0, 0))]}
        problems = s05.check_c8_region_intrusion(parsed, v)
        self.assertTrue(any("not in the declared vocabulary" in p
                            for p in problems), problems)

    def test_no_canonical_prose_makes_a_blanket_exclusion_claim(self):
        """The contract may not say something the role policy contradicts.

        It said "No Feature may intrude into a FunctionalRegion" while
        role_policy declares SUPPORT does not exclude occupancy - so the contract
        asserted two things at once, and a reader could take either as
        authoritative. Checked against the policy rather than against a fixed
        sentence: if a role that excludes occupancy is ever added or removed,
        this asks the question again instead of matching yesterday's wording.
        """
        import os
        from . import _paths
        permissive = [role for role, policy
                      in (self.role_policy() or {}).items()
                      if not policy.get("excludes_occupancy")]
        self.assertTrue(permissive,
                        "no role permits occupancy, so a blanket exclusion "
                        "claim would be true and this guard is meaningless")
        for name in ("DESIGN_STATE_CONTRACT.yaml",
                     os.path.join("stages", "S05_CONTRACT.yaml")):
            with self.subTest(contract=name):
                with open(os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                                       name)) as handle:
                    body = handle.read()
                for blanket in ("No Feature may intrude into a FunctionalRegion",
                                "no Feature intrudes into a FunctionalRegion"):
                    self.assertNotIn(
                        blanket, body,
                        "%s claims every FunctionalRegion excludes Features, "
                        "which role_policy contradicts for %s"
                        % (name, ", ".join(sorted(permissive))))

    def role_policy(self):
        from . import _paths
        contract = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        families = dict(contract["entity_families"])
        families.update(contract["assurance_families"])
        return families["FunctionalRegion"].get("role_policy") or {}

    def test_both_stages_read_the_same_occupancy_policy(self):
        """s04b and S05-C8 each used to carry their own tuple of roles. Two
        copies of a rule are two rules, and nothing made them agree."""
        import inspect
        from ver3.assy_v3.stages import s04_envelope_and_motion as s04
        for module in (s04, s05):
            with self.subTest(module=module.__name__):
                source = inspect.getsource(module)
                self.assertNotIn('("ACCESS", "APERTURE", "KEEP_OUT")', source,
                                 "an occupancy role list is hard-coded again")
        self.assertTrue(s04.excludes_occupancy("KEEP_OUT"))
        self.assertFalse(s04.excludes_occupancy("SUPPORT"))

    def test_no_regions_declared_means_nothing_to_intrude(self):
        parsed = {"features": [feature("FEA-1", "BOD-1")]}
        self.assertEqual([], s05.check_c8_region_intrusion(parsed, view()))


class TestC9ClearanceConstraints(unittest.TestCase):
    """S05-C9: the link is a typed canonical reference, not an injected key."""

    V = view(Interface=[
        {"entity_id": "IFC-1", "bodies": ["BOD-1", "BOD-2"],
         "interaction_kind": "CLEARANCE"},
        {"entity_id": "IFC-2", "bodies": ["BOD-2", "BOD-3"],
         "interaction_kind": "CLEARANCE"},
        {"entity_id": "IFC-3", "bodies": ["BOD-1", "BOD-3"],
         "interaction_kind": "CONTACT"}])

    @staticmethod
    def clearance(cid, interface):
        return {"id": cid, "kind": "CLEARANCE", "parameters": [],
                "expression": {"relation": ">=", "lhs": {"ref": "PRM-1"},
                               "rhs": {"const": 0.5, "unit": "mm"}},
                "governs_interface": interface}

    def test_a_governing_constraint_for_each_clearance_passes(self):
        parsed = {"constraints": [self.clearance("CON-1", "IFC-1"),
                                  self.clearance("CON-2", "IFC-2")]}
        self.assertEqual([], s05.check_c9_clearance_constraints(parsed, self.V))

    def test_one_constraint_cannot_speak_for_two_clearances(self):
        parsed = {"constraints": [self.clearance("CON-1", "IFC-1")]}
        problems = s05.check_c9_clearance_constraints(parsed, self.V)
        self.assertTrue(any("IFC-2" in p for p in problems), problems)

    def test_a_constraint_with_no_governed_interface_does_not_count(self):
        """The false-green shape: a clearance constraint that names nothing."""
        parsed = {"constraints": [dict(self.clearance("CON-1", "IFC-1"),
                                       governs_interface=None)]}
        problems = s05.check_c9_clearance_constraints(parsed, self.V)
        self.assertTrue(any("IFC-1" in p for p in problems), problems)

    def test_a_non_clearance_interface_needs_no_such_constraint(self):
        parsed = {"constraints": [self.clearance("CON-1", "IFC-1"),
                                  self.clearance("CON-2", "IFC-2")]}
        self.assertTrue(all("IFC-3" not in p for p in
                            s05.check_c9_clearance_constraints(parsed, self.V)))

    def test_a_dimensional_constraint_naming_an_interface_does_not_satisfy_it(self):
        parsed = {"constraints": [dict(self.clearance("CON-1", "IFC-1"),
                                       kind="DIMENSIONAL"),
                                  self.clearance("CON-2", "IFC-2")]}
        problems = s05.check_c9_clearance_constraints(parsed, self.V)
        self.assertTrue(any("IFC-1" in p for p in problems), problems)

    def test_the_relation_survives_the_patch_path(self):
        """Production must be able to express every positive case above."""
        ops = S05Embodiment().to_operations(
            {"constraints": [self.clearance("CON-1", "IFC-1")]})
        self.assertEqual("IFC-1", ops[0].fields["governs_interface"])
        self.assertIn("IFC-1", ops[0].premise_refs)


class TestC1RequiresBothSidesAndCompliantJointsAreInternal(unittest.TestCase):
    """S05-C1 has no compliant exception, and the reason is the ontology.

    An earlier version let a two-body Interface skip a feature on one side when
    some COMPLIANT joint connected the same pair. It read the contract's word
    "compliant" as an alternative to realizing an interface. It is not: compliance
    is declared as "a joint_type of Joint between RigidGroups of ONE body", an
    INTERNAL relation where part of a body flexes relative to the rest of it. A
    joint spanning two bodies is not that thing, so the exception was admitting a
    malformed record as grounds for omitting geometry.

    The Joint contract is also unconditional about it: "A joint_type label alone
    is inert. A realization on each side is required (INV-008)."

    So: two bodies that touch need two features, always. A flexure is geometry on
    its own body and gets a feature like anything else.
    """

    @staticmethod
    def joint(jid, jtype="COMPLIANT", parent="RGP-1", child="RGP-2", **over):
        rec = {"entity_id": jid, "joint_type": jtype, "parent_group": parent,
               "child_group": child, "dof": ["RZ"], "axis_direction": "+Z",
               "frame_ids": ["FRM-1"]}
        rec.update(over)
        return rec

    #: An ordinary two-body interface.
    TWO_BODY = view(Interface=[{"entity_id": "IFC-1",
                                "bodies": ["BOD-1", "BOD-2"],
                                "interaction_kind": "CONTACT"}])

    def internal_compliant(self, **over):
        """THE CANONICAL SHAPE: one body, two of ITS rigid groups.

        The previous positive fixture put RGP-1 on BOD-1 and RGP-2 on BOD-2 and
        called the result legitimate. That fixture described a joint the
        ontology does not model, so nothing built on it could be evidence.
        """
        return view(
            Interface=[{"entity_id": "IFC-1", "bodies": ["BOD-1", "BOD-2"],
                        "interaction_kind": "CONTACT"}],
            RigidGroup=[{"entity_id": "RGP-1", "body": "BOD-1"},
                        {"entity_id": "RGP-2", "body": "BOD-1"}],
            Joint=[self.joint("JNT-1", **over)])

    def test_a_two_body_interface_needs_both_sides(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1")]}
        problems = s05.check_c1_interface_features(parsed, self.TWO_BODY)
        self.assertTrue(any("BOD-2" in p for p in problems), problems)

    def test_both_sides_featured_passes(self):
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1")]}
        self.assertEqual([], s05.check_c1_interface_features(parsed, self.TWO_BODY))

    def test_an_internal_compliant_joint_does_not_excuse_the_other_body(self):
        """The repair, stated directly. A flexure inside BOD-1 says nothing
        about whether BOD-2 was given the face it touches."""
        parsed = {"features": [feature("FEA-1", "BOD-1", "SNAP_ARM", interface="IFC-1")]}
        problems = s05.check_c1_interface_features(parsed, self.internal_compliant())
        self.assertTrue(any("BOD-2" in p for p in problems),
                        "a compliant joint internal to BOD-1 was allowed to "
                        "excuse the missing realization on BOD-2: %s" % problems)

    def test_an_internal_compliant_joint_is_not_itself_reported(self):
        """It is canonical. Featuring both sides must leave it uncomplained-about."""
        parsed = {"features": [feature("FEA-1", "BOD-1", "SNAP_ARM", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1")]}
        self.assertEqual([], s05.check_c1_interface_features(
            parsed, self.internal_compliant()))

    def test_a_cross_body_compliant_joint_is_reported_as_malformed(self):
        """The record that used to excuse a missing feature is now the failure."""
        v = self.internal_compliant()
        v["RigidGroup"] = [{"entity_id": "RGP-1", "body": "BOD-1"},
                           {"entity_id": "RGP-2", "body": "BOD-2"}]
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1")]}
        problems = s05.check_c1_interface_features(parsed, v)
        self.assertTrue(any("ONE body" in p for p in problems), problems)

    def test_a_non_compliant_cross_body_joint_is_not_reported(self):
        """A revolute joint between two bodies is ordinary. Only COMPLIANT
        carries the intra-body requirement."""
        v = self.internal_compliant(jtype="REVOLUTE")
        v["RigidGroup"] = [{"entity_id": "RGP-1", "body": "BOD-1"},
                           {"entity_id": "RGP-2", "body": "BOD-2"}]
        parsed = {"features": [feature("FEA-1", "BOD-1", interface="IFC-1"),
                               feature("FEA-2", "BOD-2", interface="IFC-1")]}
        self.assertEqual([], s05.check_c1_interface_features(parsed, v))

    def test_the_internal_helper_keys_by_body_not_by_pair(self):
        joints = s05.internal_compliant_joints(self.internal_compliant())
        self.assertEqual(["BOD-1"], sorted(joints))

    def test_the_helper_ignores_an_incomplete_joint_record(self):
        """`A joint_type label alone is inert.`"""
        self.assertEqual({}, s05.internal_compliant_joints(
            self.internal_compliant(axis_direction="")))


class TestC1MakesNoClaimAboutCompliantElementGeometry(unittest.TestCase):
    """§9.4: do not pretend to verify what canonical data cannot answer.

    `compliant_element` names the geometry a reduced-order beam model would
    consume, and it is an untyped prose field - no `field_semantics`, no
    reference to a Feature. Whether that element was actually drawn cannot be
    determined from typed state, so C1 must not claim it.
    """

    def test_compliant_element_is_still_untyped_in_the_contract(self):
        """If it ever gains a typed reference, this test should fail and the
        claim should be upgraded rather than left unmade."""
        from . import _paths
        contract = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        families = dict(contract["entity_families"])
        families.update(contract["assurance_families"])
        semantics = families["Joint"].get("field_semantics") or {}
        self.assertNotIn("compliant_element", semantics,
                         "compliant_element is now typed; C1 can and should "
                         "check that the compliant geometry exists")

    def test_c1_does_not_read_compliant_element(self):
        """The CODE, not the prose. The docstring names the field precisely to
        record that it is not consulted, so a raw substring scan finds the
        explanation and fails on it - which would make this test impossible to
        pass rather than able to catch anything."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(s05.check_c1_interface_features))
        fn = tree.body[0]
        body = fn.body[1:] if ast.get_docstring(fn) else fn.body
        literals = {n.value for stmt in body for n in ast.walk(stmt)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        self.assertNotIn("compliant_element", literals,
                         "C1 reads an untyped prose field; a claim derived from "
                         "it would be reading a sentence as a structural fact")


class TestC10SolverEvidence(unittest.TestCase):
    """S05-C10: no Parameter value without a cited solver artifact. R-23."""

    def test_a_declaration_without_a_value_passes(self):
        self.assertEqual([], s05.check_c10_no_unsolved_values(
            {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm"}]}))

    def test_a_bare_number_is_reported(self):
        """A guess wearing a solved answer's clothes."""
        problems = s05.check_c10_no_unsolved_values(
            {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm", "value": 6.0}]})
        self.assertTrue(any("PRM-1" in p for p in problems), problems)

    def test_a_value_citing_a_solver_artifact_is_permitted(self):
        self.assertEqual([], s05.check_c10_no_unsolved_values(
            {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm",
                             "value": 6.0, "solved_by": "SLV-1"}]}))


class TestS05ProducesCanonicalNames(unittest.TestCase):
    """The retired draft spellings must not come back through the producer."""

    def test_operations_use_canonical_fields(self):
        parsed = {
            "features": [feature("FEA-1", "BOD-1")],
            "realizations": [realization("RLZ-1", ["OBL-1"], ["FEA-1"])],
            "parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm"}],
            "constraints": [{"id": "CON-1", "kind": "ENVELOPE",
                             "expression": {"relation": "==", "lhs": {"ref": "PRM-1"},
                                            "rhs": MM}, "parameters": ["PRM-1"]}],
            "construction_statements": [
                {"id": "CST-1", "body": "BOD-1", "operation": "BOX",
                 "parameters": {"dx": MM, "dy": MM, "dz": MM}}],
        }
        ops = S05Embodiment().to_operations(parsed)
        by_family = {o.entity_type: o for o in ops}
        self.assertIn("body", by_family["Feature"].fields)
        self.assertNotIn("rigid_group", by_family["Feature"].fields)
        self.assertIn("addresses_obligations", by_family["Realization"].fields)
        self.assertNotIn("discharges_obligations", by_family["Realization"].fields)
        self.assertNotIn("ROI", by_family)

    def test_a_parameter_is_always_authored_as_declared(self):
        """s05 may not claim a settled status it has no solver evidence for."""
        ops = S05Embodiment().to_operations(
            {"parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm",
                             "status": ir.SOLVED, "value": 9.0}]})
        self.assertEqual(ir.DECLARED, ops[0].fields["status"])
        self.assertNotIn("value", ops[0].fields)

    def test_every_created_family_is_one_the_contract_permits(self):
        from . import _paths
        resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        permitted = set(resp["stages"]["s05"]["permitted_output_semantics"])
        parsed = {"features": [feature("FEA-1", "BOD-1")],
                  "realizations": [realization("RLZ-1", [], [])],
                  "parameters": [{"id": "PRM-1", "symbol": "r", "unit": "mm"}],
                  "constraints": [{"id": "CON-1", "kind": "ENVELOPE",
                                   "expression": {}, "parameters": []}],
                  "construction_statements": [
                      {"id": "CST-1", "body": "B", "operation": "BOX", "parameters": {}}],
                  "unresolved": [{"id": "S5U-1", "decision": "d", "why_open": "w",
                                  "alternatives_kind": "FREE_TEXT"}]}
        ops = S05Embodiment().to_operations(parsed)
        self.assertTrue(ops, "no operation was produced, so nothing is checked")
        for op in ops:
            with self.subTest(family=op.entity_type):
                self.assertIn(op.entity_type, permitted)


class TestS05SchemaDoesNotAnchorOnOccupiedIds(unittest.TestCase):

    def test_no_schema_example_is_an_instantiable_id(self):
        import re
        schema = S05Embodiment.render_response_schema()
        self.assertEqual([], re.findall(r'id "[A-Z][A-Z0-9]*-\d+"', schema))

    def test_the_prompt_teaches_the_typed_constraint_shape(self):
        prompt = S05Embodiment().prompt({"consumer_view": {}})
        self.assertIn('"relation"', prompt)
        self.assertIn("AREA", prompt)          # a length times a length


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()


class TestNoCheckReadsAFamilyTheViewNeverGrants(unittest.TestCase):
    """The structural false-green, closed statically.

    `_rows` returns `[]` for a family the consumer view does not carry, and the
    payload omits an empty family entirely - so at runtime "granted but nothing
    there" and "never granted at all" are the same empty list. A check reading
    an ungranted family therefore cannot fail on ANY input, and reports
    compliance while asking nothing.

    S05-C3 was exactly that: it read `MobilityExpectation` to find the DOFs
    dispositioned BLOCKED_BY, and the s05 required minimum did not include it.
    Every cell was skipped, the check returned no problems, and the suite was
    green. The repair was a premise class (`limit_to_produce`), not a deleted
    check - a stage cannot be asked to satisfy a demand it was never shown.

    This asserts the property rather than the instance: every family literal
    reachable from any check function must be in the derived required minimum.
    It runs off the AST and the contract, so a new check that reads a new family
    fails here until the premise granting it is declared.
    """

    @classmethod
    def setUpClass(cls):
        import ast
        from ver3.assy_v3.state.design_state import Contracts
        from ver3.assy_v3.view import derive_required_minimum
        from . import _paths

        cls.granted = derive_required_minimum(
            "s05", Contracts(),
            _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")).families()

        source = open(s05.__file__).read()
        tree = ast.parse(source)
        # Helpers that read the view, and the checks that call them. Resolved
        # one level deep so `_blocking_relations(view)` counts as a read of
        # ConstraintRelation by whichever check calls it.
        reads, helpers = {}, {}
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            direct, called = set(), set()
            for n in ast.walk(fn):
                if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Name):
                    continue
                if n.func.id in ("_rows", "_ids"):
                    if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                        direct.add(n.args[1].value)
                else:
                    called.add(n.func.id)
            (reads if fn.name.startswith("check_c") else helpers)[fn.name] = \
                (direct, called)
            if fn.name.startswith("check_c"):
                helpers[fn.name] = (direct, called)
        cls.reads, cls.helpers = reads, helpers

    def _families_of(self, name):
        direct, called = self.helpers[name]
        out = set(direct)
        for callee in called:
            if callee in self.helpers and callee != name:
                out |= self.helpers[callee][0]
        return out

    def test_the_audit_found_the_checks(self):
        """Otherwise the loop below iterates over nothing and proves nothing."""
        self.assertEqual(14, len(self.reads),
                         "expected fourteen checks; the AST scan found %d"
                         % len(self.reads))

    def test_every_family_a_check_reads_is_granted_to_s05(self):
        for name in sorted(self.reads):
            for family in sorted(self._families_of(name)):
                with self.subTest(check=name, family=family):
                    self.assertIn(
                        family, self.granted,
                        "%s reads %s, which the s05 consumer view does not "
                        "grant. The read returns [] on every input, so the "
                        "check cannot fail. Declare the premise class that "
                        "grants it, or drop the check." % (name, family))

    def test_c3_specifically_can_now_see_the_dispositions(self):
        """The instance that was broken, pinned so it cannot silently return."""
        self.assertIn("MobilityExpectation", self._families_of("check_c3_limit_pairs"))
        self.assertIn("MobilityExpectation", self.granted)


class TestTheStageIsJudgedOnWhatItWasAsked(unittest.TestCase):
    """A check whose subject the prompt never raises is a trap, not a check.

    S05-C4 was one: the prompt said "for every obligation below" while the
    validator wanted a subset. S05-C3 was another and lasted longer - it asks
    whether a feature pair PRODUCES a declared travel limit, and the prompt said
    nothing about limits, blocked degrees of freedom, or stopping anything. A
    model cannot satisfy a demand nobody made, and a run failing that way reads
    as a model failure when it is a specification failure.

    This maps each check to a word the instructions must contain. Deliberately
    coarse - it asserts the SUBJECT was raised, never how it was worded - because
    a test that pinned phrasing would fail on every honest rewrite.
    """

    #: check -> a term whose absence means the prompt never raised the subject.
    SUBJECTS = {
        "check_c1_interface_features": ("interaction", "feature"),
        "check_c2_blocking_pairs": ("feature",),
        "check_c3_limit_pairs": ("blocked_by", "limit"),
        "check_c4_obligations_realized": ("obligation", "realization"),
        "check_c5_program_totality": ("parameter", "construction program"),
        "check_c6_units": ("unit",),
        "check_c7_no_parameter_cycle": ("parameter",),
        "check_c8_region_intrusion": ("functional region", "envelope"),
        "check_c9_clearance_constraints": ("clearance", "governs_interface"),
        "check_c10_no_unsolved_values": ("value",),
        # Unit G: CAD-constructibility
        "check_c11_joints_realized": ("joint", "placement"),
        "check_c12_bodies_built": ("every body", "construction program"),
        "check_c13_placed_features_built": ("placed feature",),
        "check_c14_mating_kinds": ("mating",),
    }

    @classmethod
    def setUpClass(cls):
        # The INSTRUCTIONS, not the rendered projection: the projection is the
        # view dumped in, and finding a word there would only prove the data
        # arrived, not that anything was asked of it.
        cls.instructions = s05.PROMPT.split("DECIDED MECHANISM")[0].lower()

    def test_the_instructions_were_actually_isolated(self):
        """Otherwise every assertion below searches the whole prompt."""
        self.assertIn("rules", self.instructions)
        self.assertNotIn("{projection}", self.instructions)

    def test_every_check_has_its_subject_raised_by_the_prompt(self):
        for name, terms in sorted(self.SUBJECTS.items()):
            with self.subTest(check=name):
                self.assertTrue(
                    any(t in self.instructions for t in terms),
                    "%s judges something the prompt never asks for; none of %s "
                    "appears in the instructions" % (name, list(terms)))

    def test_every_check_in_the_module_is_covered_by_this_map(self):
        """A new check must declare the subject it judges, or this fails."""
        import inspect
        checks = {n for n, _ in inspect.getmembers(s05, inspect.isfunction)
                  if n.startswith("check_c")}
        self.assertEqual(checks, set(self.SUBJECTS),
                         "a check exists that this guard does not map to a "
                         "prompt subject")
