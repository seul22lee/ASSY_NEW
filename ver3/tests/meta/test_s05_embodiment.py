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


def feature(fid, body, kind="FACE"):
    return {"id": fid, "body": body, "feature_kind": kind, "geometry": "a face"}


def realization(rid, obligations, features, predicate="the gap stays positive"):
    return {"id": rid, "addresses_obligations": list(obligations),
            "participating_features": list(features),
            "verification_predicate": predicate}


class TestC1InterfaceFeatures(unittest.TestCase):
    """S05-C1: every Interface has a Feature on EACH participant."""

    V = view(Interface=[{"entity_id": "IFC-1", "bodies": ["BOD-1", "BOD-2"],
                         "interaction_kind": "CONTACT"}])

    def test_a_feature_on_each_side_passes(self):
        parsed = {"features": [feature("FEA-1", "BOD-1"), feature("FEA-2", "BOD-2")]}
        self.assertEqual([], s05.check_c1_interface_features(parsed, self.V))

    def test_one_side_unrealised_is_reported(self):
        """Geometry that touches nothing. The other body has no surface to meet."""
        parsed = {"features": [feature("FEA-1", "BOD-1")]}
        problems = s05.check_c1_interface_features(parsed, self.V)
        self.assertTrue(any("BOD-2" in p for p in problems), problems)


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


class TestC8RegionIntrusion(unittest.TestCase):
    """S05-C8: no Feature intrudes into a FunctionalRegion."""

    V = view(FunctionalRegion=[{"entity_id": "FRG-1", "role": "ACCESS",
                                "owning_bodies": ["BOD-1"]}])

    def test_a_feature_outside_every_region_passes(self):
        self.assertEqual([], s05.check_c8_region_intrusion(
            {"features": [feature("FEA-1", "BOD-1")]}, self.V))

    def test_a_feature_declaring_intrusion_is_reported(self):
        parsed = {"features": [dict(feature("FEA-1", "BOD-1"),
                                    intrudes_region="FRG-1")]}
        problems = s05.check_c8_region_intrusion(parsed, self.V)
        self.assertTrue(any("FRG-1" in p for p in problems), problems)


class TestC9ClearanceConstraints(unittest.TestCase):
    """S05-C9: every declared clearance pair has a Constraint, per interface.

    In aggregate would not do: one constraint would cover five clearances, and
    the settlement loop can only converge on constraints it was given.
    """

    V = view(Interface=[
        {"entity_id": "IFC-1", "bodies": ["BOD-1", "BOD-2"], "interaction_kind": "CLEARANCE"},
        {"entity_id": "IFC-2", "bodies": ["BOD-2", "BOD-3"], "interaction_kind": "CLEARANCE"},
        {"entity_id": "IFC-3", "bodies": ["BOD-1", "BOD-3"], "interaction_kind": "CONTACT"}])

    def test_a_constraint_for_each_clearance_passes(self):
        parsed = {"constraints": [
            {"id": "CON-1", "kind": "CLEARANCE", "interface": "IFC-1"},
            {"id": "CON-2", "kind": "CLEARANCE", "interface": "IFC-2"}]}
        self.assertEqual([], s05.check_c9_clearance_constraints(parsed, self.V))

    def test_one_constraint_does_not_cover_two_clearances(self):
        parsed = {"constraints": [{"id": "CON-1", "kind": "CLEARANCE",
                                   "interface": "IFC-1"}]}
        problems = s05.check_c9_clearance_constraints(parsed, self.V)
        self.assertTrue(any("IFC-2" in p for p in problems), problems)

    def test_a_contact_interface_needs_no_clearance_constraint(self):
        parsed = {"constraints": [
            {"id": "CON-1", "kind": "CLEARANCE", "interface": "IFC-1"},
            {"id": "CON-2", "kind": "CLEARANCE", "interface": "IFC-2"}]}
        self.assertTrue(all("IFC-3" not in p for p in
                            s05.check_c9_clearance_constraints(parsed, self.V)))


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
        for op in S05Embodiment().to_operations(parsed):
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
