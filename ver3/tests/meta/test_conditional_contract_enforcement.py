"""A conditional rule the contract declares is a rule the write boundary enforces.

Some canonical requirements are narrower than a family: a Joint needs travel and
actuation only when it is COMPLIANT; a ReferenceScale needs a structured
`absolute` only when its basis is ABSOLUTE. Declaring those as `required_fields`
would reject every ordinary record of the family, so for a long time they were
written as prose beside the family instead.

Prose is not consumed by the write boundary. So the rules existed, read as
though they held, and did not - which is worse than not having them, because the
contract asserted them. A cross-body Joint labelled COMPLIANT with none of the
variant fields was accepted; `"80-100 mm"` was written into an ABSOLUTE scale's
`absolute` field and every dimensional comparison downstream then read a scale
that says nothing.

The first class below is the one that has to keep working. It does not test the
two rules that exist today - it derives the cases FROM the contract, so a rule
added tomorrow is covered the moment it is declared, and one declared but not
consumed fails here rather than being discovered by whatever it let through.
"""

import unittest

from . import _paths

from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch


def problems_for(family, fields, stage):
    state = DesignState(run_id="conditional")
    patch = StagePatch(
        patch_id="p", run_id="conditional", stage_id=stage, stage_attempt=1,
        parent_state_hash=state.state_hash(),
        operations=[Op("CREATE", family, "E-0001", dict(fields), "p:probe")],
        execution_status="SUCCESS", provenance={"purpose": "conditional test"})
    return state.validate(patch)


def conditional_problems(family, fields, stage):
    return [p for p in problems_for(family, fields, stage)
            if p.startswith("CONDITIONAL_")]


class TestEveryDeclaredConditionalRuleIsActuallyEnforced(unittest.TestCase):
    """The anti-drift guard. Derived from the contract, not from a list here.

    For each declared rule it builds two records: one that does not trigger the
    rule, and one that triggers it and breaks it. The second must be rejected
    and the first must not be rejected BY THIS RULE. A rule the runtime never
    reads fails the second assertion, which is exactly the drift this exists to
    make impossible.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.rules = []
        for family in sorted(cls.c.families):
            for rule in cls.c.conditional_requirements(family):
                cls.rules.append((family, rule))

    def _base_fields(self, family, rule):
        """A record carrying every unconditionally required field."""
        out = {}
        for name in self.c.required_fields(family):
            if name == "entity_id":
                continue
            out[name] = "x"
        # Reference-valued and list-valued fields take a shape "x" cannot be.
        for name, spec in (self.c.field_semantics(family) or {}).items():
            if name in out and spec.get("cardinality") == "many":
                out[name] = []
        return out

    def test_there_are_declared_rules_to_check(self):
        """Otherwise this whole class passes by iterating over nothing."""
        self.assertTrue(self.rules,
                        "no conditional_requirements are declared anywhere; if "
                        "that is deliberate this guard should be removed rather "
                        "than left passing vacuously")

    def test_a_record_that_triggers_a_rule_and_breaks_it_is_rejected(self):
        for family, rule in self.rules:
            with self.subTest(family=family, rule=rule.get("name")):
                when = rule["applies_when"]
                owner = self.c.owner_of(family)
                stage = owner if isinstance(owner, str) and owner != "any" else "s03"
                fields = self._base_fields(family, rule)
                fields[when["field"]] = when["equals"]
                # Break it: strip every field the rule adds, and any field it
                # constrains the shape of.
                for name in rule.get("additional_required_fields") or []:
                    fields.pop(name, None)
                for name in rule.get("required_shape") or {}:
                    fields.pop(name, None)
                self.assertTrue(
                    conditional_problems(family, fields, stage),
                    "%s declares conditional rule %r and the write boundary "
                    "accepted a record that triggers and violates it; the "
                    "declaration is not being consumed"
                    % (family, rule.get("name")))

    def test_a_record_that_does_not_trigger_the_rule_is_not_rejected_by_it(self):
        """A conditional rule that fires on everything is an unconditional one
        written in the wrong place."""
        for family, rule in self.rules:
            with self.subTest(family=family, rule=rule.get("name")):
                when = rule["applies_when"]
                owner = self.c.owner_of(family)
                stage = owner if isinstance(owner, str) and owner != "any" else "s03"
                fields = self._base_fields(family, rule)
                fields[when["field"]] = "SOMETHING_ELSE_ENTIRELY"
                for name in rule.get("additional_required_fields") or []:
                    fields.pop(name, None)
                self.assertEqual(
                    [], conditional_problems(family, fields, stage),
                    "%s rule %r fired on a record it does not govern"
                    % (family, rule.get("name")))

    def test_every_rule_is_named_and_says_why(self):
        for family, rule in self.rules:
            with self.subTest(family=family, rule=rule.get("name")):
                self.assertTrue(rule.get("name"))
                self.assertTrue((rule.get("why") or "").strip(),
                                "a rule that rejects a write must say what "
                                "engineering fact it is protecting")

    def test_every_rule_declares_a_trigger_the_runtime_understands(self):
        for family, rule in self.rules:
            with self.subTest(family=family, rule=rule.get("name")):
                when = rule.get("applies_when") or {}
                self.assertIn("field", when)
                self.assertIn("equals", when)


class TestAbsoluteScaleMustBeUsable(unittest.TestCase):
    """§11. An ABSOLUTE basis promises comparability. Keep the promise or don't
    make it."""

    def scale(self, **over):
        return conditional_problems("ReferenceScale", dict({"basis": "ABSOLUTE"},
                                                           **over), "s04")

    def test_a_relative_scale_needs_no_absolute_and_is_not_defaulted(self):
        """The contract is explicit: RELATIVE with absolute null is a
        legitimate, honest value and must never be given an invented number."""
        self.assertEqual([], conditional_problems(
            "ReferenceScale", {"basis": "RELATIVE"}, "s04"))
        self.assertEqual([], conditional_problems(
            "ReferenceScale", {"basis": "RELATIVE", "absolute": None}, "s04"))

    def test_a_well_formed_absolute_scale_is_accepted(self):
        self.assertEqual([], self.scale(absolute={"unit": "mm", "per_unit": 1.0}))

    def test_a_quantity_written_as_prose_is_rejected(self):
        """The failure that motivated this: a travel window arriving as text."""
        self.assertTrue(self.scale(absolute="80-100 mm"))

    def test_a_bare_number_is_rejected(self):
        self.assertTrue(self.scale(absolute=80))

    def test_an_empty_mapping_is_rejected(self):
        self.assertTrue(self.scale(absolute={}))

    def test_half_a_scale_is_rejected(self):
        self.assertTrue(self.scale(absolute={"unit": "mm"}))
        self.assertTrue(self.scale(absolute={"per_unit": 1.0}))

    def test_a_missing_absolute_is_rejected(self):
        self.assertTrue(self.scale())

    def test_an_unusable_per_unit_is_rejected(self):
        for bad in (0, -1.0, float("inf"), float("nan"), "1.0", True):
            with self.subTest(per_unit=bad):
                self.assertTrue(self.scale(absolute={"unit": "mm",
                                                     "per_unit": bad}),
                                "per_unit=%r was accepted; a scale factor that "
                                "is not a usable positive number cannot convert "
                                "anything" % (bad,))

    def test_an_empty_unit_is_rejected(self):
        self.assertTrue(self.scale(absolute={"unit": "  ", "per_unit": 1.0}))

    def test_nothing_was_silently_repaired(self):
        """A rejected write must not become an accepted-and-corrected one."""
        state = DesignState(run_id="norepair")
        patch = StagePatch(
            patch_id="p", run_id="norepair", stage_id="s04", stage_attempt=1,
            parent_state_hash=state.state_hash(),
            operations=[Op("CREATE", "ReferenceScale", "SCL-1",
                           {"basis": "ABSOLUTE", "absolute": "80-100 mm"},
                           "p:probe")],
            execution_status="SUCCESS", provenance={})
        self.assertTrue(state.validate(patch))
        self.assertEqual([], list(state.family("ReferenceScale")),
                         "the malformed scale reached state anyway")


class TestCompliantJointMustCarryItsVariant(unittest.TestCase):
    """§9.3. A joint_type label alone is inert, enforced where it is written."""

    BASE = {"joint_type": "REVOLUTE", "parent_group": "RGP-1",
            "child_group": "RGP-2", "dof": "1", "axis_direction": "x",
            "frame_ids": []}
    VARIANT = {"mode": "BENDING", "direction": "z", "required_travel": 1.0,
               "allowable_travel": 2.0, "actuation": "PRESCRIBED_KINEMATIC",
               "compliant_element": "the cantilever arm",
               "root_interface": "IFC-0001", "activation_window": "0..1"}

    def test_an_ordinary_joint_needs_no_variant_fields(self):
        self.assertEqual([], conditional_problems("Joint", self.BASE, "s03"))

    def test_a_compliant_joint_without_its_variant_is_rejected(self):
        fields = dict(self.BASE, joint_type="COMPLIANT")
        self.assertTrue(conditional_problems("Joint", fields, "s03"),
                        "a COMPLIANT label with no travel, no actuation and no "
                        "compliant element was accepted; nothing downstream "
                        "could model it and nothing could check it")

    def test_a_complete_compliant_joint_is_accepted(self):
        fields = dict(self.BASE, joint_type="COMPLIANT", **self.VARIANT)
        self.assertEqual([], conditional_problems("Joint", fields, "s03"))

    def test_each_variant_field_is_individually_required(self):
        """Otherwise 'the variant is required' could hold while any one of them
        is quietly optional."""
        for omitted in self.VARIANT:
            with self.subTest(omitted=omitted):
                fields = dict(self.BASE, joint_type="COMPLIANT", **self.VARIANT)
                fields.pop(omitted)
                self.assertTrue(conditional_problems("Joint", fields, "s03"),
                                "a COMPLIANT joint missing %r was accepted"
                                % omitted)

    def test_the_trigger_is_case_insensitive_on_the_value(self):
        """`compliant` and `COMPLIANT` are the same engineering claim."""
        fields = dict(self.BASE, joint_type="compliant")
        self.assertTrue(conditional_problems("Joint", fields, "s03"))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
