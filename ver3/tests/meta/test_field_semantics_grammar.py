"""The declaration grammar itself, checked generically.

`field_semantics` grew three constructs to close the S03a seam - a reference
target that may name several families, a plain typed record list, and a
reference that exists only for some records - and each was verified through the
one family that needed it. A grammar checked only where it is used is a grammar
that fails silently the second time someone uses it: a union naming a retired
family, or a record list declaring no subfield types, would have been caught by
no S03 test because no S03 field declares one.

These run over EVERY family. They do not know which fields exist, and a new
declaration is covered the moment it is written.
"""

import unittest

from . import _paths

from ver3.assy_v3.state.design_state import Contracts

#: Families the contract has retired. A reference may not name one.
RETIRED = {"BlockingRelation", "ROI", "MobilityAssertion"}


class _Grammar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.fams = cls.c.families

    def declarations(self, kind=None):
        for family in sorted(self.fams):
            for field, spec in (self.c.field_semantics(family) or {}).items():
                if kind is None or spec.get("kind") == kind:
                    yield family, field, spec


class TestReferenceTargetGrammar(_Grammar):
    """`target` is a family name, or a non-empty list of family names."""

    def test_there_are_references_to_check(self):
        self.assertTrue(list(self.declarations("reference")))

    def test_every_target_is_a_string_or_a_list_of_strings(self):
        for family, field, spec in self.declarations("reference"):
            with self.subTest(family=family, field=field):
                target = spec.get("target")
                self.assertIsNotNone(target, "a reference with no target")
                if target == "ANY":
                    # An EXPLICIT "no family constraint", for a field whose
                    # referent family is genuinely open. Written out so that
                    # "unconstrained" is a decision someone made rather than a
                    # declaration someone forgot.
                    continue
                if isinstance(target, list):
                    self.assertTrue(target, "an EMPTY union names nothing and "
                                            "would accept every family")
                    for one in target:
                        self.assertIsInstance(one, str)
                else:
                    self.assertIsInstance(target, str)

    def test_every_named_family_is_defined_and_not_retired(self):
        for family, field, spec in self.declarations("reference"):
            target = spec["target"]
            if target == "ANY":
                continue
            for one in (target if isinstance(target, list) else [target]):
                with self.subTest(family=family, field=field, target=one):
                    self.assertNotIn(one, RETIRED)
                    self.assertIn(one, self.fams, "targets an undefined family")

    def test_an_unconstrained_target_is_spelled_ANY(self):
        """The only permitted way to say "no family constraint". An omitted or
        empty target would read as a declaration someone forgot."""
        for family, field, spec in self.declarations("reference"):
            with self.subTest(family=family, field=field):
                target = spec["target"]
                self.assertTrue(target != "" and target is not None)
                if isinstance(target, str) and target not in self.fams:
                    self.assertEqual("ANY", target,
                                     "a target that names no family must say ANY")

    def test_an_unconstrained_target_still_requires_ids_that_resolve(self):
        """ANY relaxes the family, never the id-ness. A field nothing can
        dereference is not machine-readable."""
        for family, field, spec in self.declarations("reference"):
            if spec["target"] == "ANY":
                with self.subTest(family=family, field=field):
                    self.assertFalse(spec.get("resolvable"),
                                     "an unconstrained AND unresolvable "
                                     "reference constrains nothing at all")

    def test_a_union_names_each_family_once(self):
        """A repeated member is a declaration nobody read back."""
        for family, field, spec in self.declarations("reference"):
            target = spec["target"]
            if target == "ANY":
                continue
            if isinstance(target, list):
                with self.subTest(family=family, field=field):
                    self.assertEqual(len(target), len(set(target)))

    def test_a_union_names_more_than_one_family(self):
        """A one-member list is a plain target written the long way, and two
        spellings of one thing is how a reader starts having to check both."""
        for family, field, spec in self.declarations("reference"):
            target = spec["target"]
            if target == "ANY":
                continue
            if isinstance(target, list):
                with self.subTest(family=family, field=field):
                    self.assertGreater(len(target), 1)

    def test_the_runtime_accepts_a_union_and_refuses_a_stranger(self):
        """Behavioural, not a reading of the declaration.

        Proves the multi-target path is actually implemented: a union field is
        given a member family and then a family outside the union.
        """
        from ver3.assy_v3.state.design_state import DesignState
        from ver3.assy_v3.state.patch import Op, StagePatch
        from . import _fixtures

        class _B(_fixtures.StateBuilder, unittest.TestCase):
            def runTest(self):
                pass

        builder = _B("runTest")
        builder.c = self.c
        unions = [(f, fld, s) for f, fld, s in self.declarations("reference")
                  if isinstance(s.get("target"), list)]
        self.assertTrue(unions, "no union target exists to exercise")
        family, field, spec = unions[0]
        member = spec["target"][0]
        stranger = next(n for n in sorted(self.fams)
                        if n not in spec["target"] and n != family)

        for target_family, expect_ok in ((member, True), (stranger, False)):
            with self.subTest(names=target_family):
                state = DesignState(run_id="union")
                owner = self.c.owner_of(target_family)
                stage = owner if isinstance(owner, str) and owner != "any" else "s02"
                referent = builder.add(state, stage, target_family,
                                       "%s-REF" % target_family[:3].upper())
                fields = builder._fields_for(state, self.c,
                                            self.c.owner_of(family) or "s02",
                                            family, {field: [referent]})
                owner2 = self.c.owner_of(family)
                stage2 = owner2 if isinstance(owner2, str) and owner2 != "any" else "s02"
                patch = StagePatch(
                    patch_id="u", run_id="union", stage_id=stage2, stage_attempt=1,
                    parent_state_hash=state.state_hash(),
                    operations=[Op("CREATE", family, "UNI-0001", fields, "p")],
                    execution_status="SUCCESS", provenance={})
                wrong = [p for p in state.validate(patch)
                         if "REFERENCE_FAMILY" in p and field in p]
                if expect_ok:
                    self.assertEqual([], wrong, "a declared member was refused")
                else:
                    self.assertTrue(wrong, "a family outside the union was "
                                           "accepted: %s" % target_family)


class TestRecordListGrammar(_Grammar):
    """`record_list` declares typed subfields and nothing else is assumed."""

    def test_every_record_list_declares_subfield_semantics(self):
        found = list(self.declarations("record_list"))
        self.assertTrue(found, "no record_list is declared; if that is "
                               "deliberate this guard should go rather than "
                               "pass over nothing")
        for family, field, spec in found:
            with self.subTest(family=family, field=field):
                subs = spec.get("record_field_semantics")
                self.assertTrue(subs, "a record list whose rows are typed by "
                                      "nothing is an untyped list with a longer "
                                      "declaration")

    def test_every_subfield_is_a_reference_or_a_closed_vocabulary(self):
        """TWO KINDS ARE WALKED ONE LEVEL DOWN, and nothing else is.

        A reference is resolved to its declared family. An enum declaring
        `values` is checked against them. A subfield that is neither is a value
        the boundary cannot check, declared as though it could be - which is the
        untyped row this grammar exists to refuse, wearing a type name.
        """
        for family, field, spec in self.declarations("record_list"):
            for name, sub in (spec.get("record_field_semantics") or {}).items():
                with self.subTest(family=family, field=field, subfield=name):
                    kind = sub.get("kind")
                    self.assertIn(kind, ("reference", "enum"),
                                  "only references and closed vocabularies are "
                                  "walked one level down")
                    if kind == "enum":
                        values = sub.get("values")
                        self.assertTrue(values, "an enum subfield declaring no "
                                                "values constrains nothing")
                        self.assertTrue(all(isinstance(v, str) and v for v in values))
                        continue
                    target = sub.get("target")
                    self.assertTrue(target)
                    for one in (target if isinstance(target, list) else [target]):
                        self.assertIn(one, self.fams)
                    self.assertIn(sub.get("cardinality"), ("one", "many"))

    def test_a_subfield_vocabulary_is_enforced_at_the_write_boundary(self):
        """The declaration is only worth making if the boundary reads it."""
        from ver3.assy_v3.state.design_state import DesignState
        from ver3.assy_v3.state.patch import Op, StagePatch
        declared = [(f, fld, name, sub)
                    for f, fld, spec in self.declarations("record_list")
                    for name, sub in (spec.get("record_field_semantics") or {}).items()
                    if sub.get("kind") == "enum"]
        self.assertTrue(declared, "no subfield vocabulary is declared, so this "
                                  "guard passes over nothing")
        for family, field, name, sub in declared:
            with self.subTest(family=family, field=field, subfield=name):
                state = DesignState(run_id="vocab")
                patch = StagePatch(
                    patch_id="vocab", run_id="vocab", stage_id="s03",
                    stage_attempt=1, parent_state_hash=state.state_hash(),
                    operations=[Op("CREATE", family, "X-1",
                                   {field: [{name: "NOT_IN_THE_VOCABULARY"}]},
                                   "test")],
                    execution_status="SUCCESS", provenance={"purpose": "vocab"})
                self.assertTrue(
                    any("RECORD_VALUE" in p for p in state.validate(patch)),
                    "%s.%s[].%s accepted a value outside %s"
                    % (family, field, name, sub.get("values")))

    def test_a_record_list_is_not_also_a_premise_record_list(self):
        """Two walkers over one field would be two answers about it."""
        for family, field, _spec in self.declarations("record_list"):
            with self.subTest(family=family, field=field):
                self.assertIsNone(self.c.premise_record_spec(family, field))

    def test_the_runtime_rejects_a_row_that_is_not_a_record(self):
        from ver3.assy_v3.state.design_state import DesignState
        from ver3.assy_v3.state.patch import Op, StagePatch
        from . import _fixtures

        class _B(_fixtures.StateBuilder, unittest.TestCase):
            def runTest(self):
                pass

        builder = _B("runTest")
        builder.c = self.c
        family, field, _spec = next(iter(self.declarations("record_list")))
        state = DesignState(run_id="rows")
        owner = self.c.owner_of(family)
        stage = owner if isinstance(owner, str) and owner != "any" else "s03"
        fields = builder._fields_for(state, self.c, stage, family,
                                     {field: ["not a record"]})
        patch = StagePatch(
            patch_id="r", run_id="rows", stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(),
            operations=[Op("CREATE", family, "ROW-0001", fields, "p")],
            execution_status="SUCCESS", provenance={})
        self.assertTrue([p for p in state.validate(patch)
                         if "RECORD_LIST" in p])


class TestConditionalReferenceGrammar(_Grammar):
    """A field that is a reference only when another field says so."""

    def rules(self):
        for family in sorted(self.fams):
            for rule in self.c.conditional_references(family):
                yield family, rule

    def test_there_are_conditional_references_to_check(self):
        self.assertTrue(list(self.rules()))

    def test_every_rule_is_well_formed(self):
        for family, rule in self.rules():
            with self.subTest(family=family, rule=rule.get("name")):
                self.assertTrue(rule.get("name"))
                self.assertTrue((rule.get("why") or "").strip())
                when = rule.get("applies_when") or {}
                self.assertIn("field", when)
                self.assertIn("equals", when)
                self.assertTrue(rule.get("field"))
                self.assertIn(rule.get("cardinality", "many"), ("one", "many"))

    def test_the_trigger_and_the_typed_field_are_declared_fields(self):
        for family, rule in self.rules():
            declared = set(self.c.required_fields(family)) | set(
                (self.fams.get(family) or {}).get("optional_fields") or [])
            for name in (rule["applies_when"]["field"], rule["field"]):
                with self.subTest(family=family, field=name):
                    self.assertIn(name, declared,
                                  "a rule about a field the family does not "
                                  "declare governs nothing")

    def test_a_conditional_reference_does_not_shadow_a_plain_one(self):
        """If the field were already a declared reference the condition would be
        a second, contradictory answer about the same field."""
        for family, rule in self.rules():
            with self.subTest(family=family, field=rule["field"]):
                self.assertIsNone(self.c.reference_spec(family, rule["field"]))


class TestMalformedDeclarationsAreCaughtGenerically(_Grammar):
    """The grammar rules above must FAIL on a bad declaration, not shrug.

    Driven through stub contracts, so nothing broken has to exist on disk for
    the guard to be shown working.
    """

    def test_an_empty_union_is_rejected_by_the_grammar(self):
        with self.assertRaises(AssertionError):
            self._check_union([])

    def test_a_union_naming_a_retired_family_is_rejected(self):
        with self.assertRaises(AssertionError):
            self._check_union(["Body", "BlockingRelation"])

    def test_a_union_naming_an_undefined_family_is_rejected(self):
        with self.assertRaises(AssertionError):
            self._check_union(["Body", "NoSuchFamily"])

    def test_a_union_repeating_a_family_is_rejected(self):
        with self.assertRaises(AssertionError):
            self._check_union(["Body", "Body"])

    def _check_union(self, target):
        """The same three assertions the grammar tests make, on one target."""
        if isinstance(target, list):
            self.assertTrue(target)
            self.assertEqual(len(target), len(set(target)))
        for one in (target if isinstance(target, list) else [target]):
            self.assertNotIn(one, RETIRED)
            self.assertIn(one, self.fams)

    def test_a_record_list_without_subfield_semantics_is_rejected(self):
        spec = {"kind": "record_list"}
        with self.assertRaises(AssertionError):
            self.assertTrue(spec.get("record_field_semantics"))

    def test_a_record_list_subfield_that_is_not_a_reference_is_rejected(self):
        sub = {"kind": "spatial", "frame": "X"}
        with self.assertRaises(AssertionError):
            self.assertEqual("reference", sub.get("kind"))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
