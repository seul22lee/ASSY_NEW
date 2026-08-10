"""S-2 / U-2B: the canonical contract corpus is closed and self-consistent.

CON-01..CON-18. Mechanism-independent: no case, no product, no model, and no
statement about what any stage currently produces - several producers are
deliberately behind these contracts and are registered as legacy.
"""
from __future__ import annotations

import os
import re
import sys
import unittest

from . import _paths

REPO = _paths.REPO_ROOT
if REPO not in sys.path:
    sys.path.insert(0, REPO)

RETIRED_FAMILIES = ("BodyHypothesis", "PhysicalInteractionHypothesis")
STAGES_UNDER_S2 = ("s01", "s02", "s03a", "s03b", "s04a", "gate", "s04b")


def _yaml(name):
    return _paths.contract(name)


class _Corpus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ds = _yaml("DESIGN_STATE_CONTRACT.yaml")
        cls.fams = dict(cls.ds["entity_families"])
        cls.fams.update(cls.ds["assurance_families"])
        cls.matrix = _yaml("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.audit = _yaml("ENTITY_FAMILY_AUDIT.yaml")
        cls.resp = _yaml("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.authority = _yaml("CONTRACT_AUTHORITY.yaml")
        cls.status = _yaml("STATUS_SEMANTICS.yaml")

    def semantics(self, fam):
        return (self.fams.get(fam) or {}).get("field_semantics", {}) or {}

    def fields(self, fam):
        v = self.fams.get(fam) or {}
        return list(v.get("required_fields", [])) + list(v.get("optional_fields", []))


class TestFamilyClosure(_Corpus):

    def test_CON_01_every_family_has_exactly_one_owner(self):
        """The source of truth declares it, and every projection agrees."""
        owns = {}
        for sid, s in self.matrix["stages"].items():
            for f in (s.get("owns") or []):
                owns.setdefault(f, []).append(sid)
        uni = {e["family"] for e in self.matrix["universally_ownable"] if "family" in e}
        excepted = {r["family"]: r for r in
                    (self.ds.get("multi_owner_exceptions", {}).get("rows") or [])}
        problems = []
        for fam, v in sorted(self.fams.items()):
            if fam in uni:
                continue
            owner = (v or {}).get("owned_by")
            if isinstance(owner, list):
                # A multi-owner family needs a declared, reasoned, scheduled
                # exception. Without one it is an undeclared contradiction.
                row = excepted.get(fam)
                if not row:
                    problems.append("%s declares owners %s with no exception" % (fam, owner))
                elif sorted(row["owners"]) != sorted(owner) or not row.get("resolution_step"):
                    problems.append("%s exception does not match or has no step" % fam)
                continue
            if not owner:
                problems.append("%s declares no owner" % fam)
                continue
            projected = owns.get(fam, [])
            if projected != [owner]:
                problems.append("%s: owned_by=%s but matrix projects %s"
                                % (fam, owner, projected))
            audited = (self.audit["families"].get(fam) or {}).get("owning_stage")
            if audited is not None and audited != owner:
                problems.append("%s: owned_by=%s but audit record says %s"
                                % (fam, owner, audited))
        self.assertEqual([], problems)

    def test_CON_02_every_family_has_exactly_one_shape_definition(self):
        """A family is defined once. It may not appear in both blocks."""
        dup = set(self.ds["entity_families"]) & set(self.ds["assurance_families"])
        self.assertEqual(set(), dup)
        for fam, v in self.fams.items():
            with self.subTest(family=fam):
                self.assertIsNotNone(v, "%s is declared with no definition" % fam)
                self.assertIn("required_fields", v)
                self.assertIn("entity_id", v["required_fields"])

    def test_CON_07_every_family_resolves_to_an_authority_class(self):
        from ver3.assy_v3.state.design_state import Contracts
        c = Contracts()
        for fam in self.fams:
            with self.subTest(family=fam):
                self.assertTrue(c.authority_class(fam).value)

    def test_CON_08_extension_is_field_and_stage_specific(self):
        """`extends` is not shared ownership: it needs a declared field."""
        problems = []
        ext_by = {}
        for fam, v in self.fams.items():
            for fld, stage in ((v or {}).get("extendable_fields", {}) or {}).items():
                ext_by.setdefault(stage, set()).add(fam)
                if fld not in self.fields(fam):
                    problems.append("%s.%s is extendable but not a declared field"
                                    % (fam, fld))
                if (v or {}).get("owned_by") == stage:
                    problems.append("%s: owner %s also listed as extender" % (fam, stage))
        for sid, s in self.matrix["stages"].items():
            declared = set(s.get("extends") or [])
            derived = ext_by.get(sid, set())
            if declared != derived:
                problems.append("%s extends %s but field declarations give %s"
                                % (sid, sorted(declared), sorted(derived)))
        self.assertEqual([], problems)


class TestReferenceClosure(_Corpus):

    def test_CON_03_every_reference_field_declares_a_valid_target(self):
        problems = []
        for fam in self.fams:
            for fld, spec in self.semantics(fam).items():
                if spec.get("kind") != "reference":
                    continue
                if not spec.get("target"):
                    problems.append("%s.%s declares no target" % (fam, fld))
                if spec.get("cardinality") not in ("one", "many"):
                    problems.append("%s.%s declares no cardinality" % (fam, fld))
        self.assertEqual([], problems)

    def test_CON_04_no_reference_targets_an_undefined_or_retired_family(self):
        problems = []
        for fam in self.fams:
            for fld, spec in self.semantics(fam).items():
                target = spec.get("target")
                if not target:
                    continue
                if target in RETIRED_FAMILIES:
                    problems.append("%s.%s targets RETIRED %s" % (fam, fld, target))
                elif target not in self.fams:
                    problems.append("%s.%s targets undefined %s" % (fam, fld, target))
        self.assertEqual([], problems)

    def test_CON_05_every_addressable_relation_has_an_identity(self):
        for name, rel in (self.ds.get("typed_relations") or {}).items():
            with self.subTest(relation=name):
                if rel.get("status") == "RETIRED_BY_S2":
                    self.assertFalse(rel.get("may_be_referenced", True))
                    self.assertIn("superseded_by", rel)
                    continue
                self.assertIn("entity_id", rel.get("required_fields", []),
                              "%s may be cited but has no id" % name)
        rel_fam = self.fams.get("ConstraintRelation")
        self.assertIsNotNone(rel_fam)
        self.assertTrue(rel_fam.get("addressable"))
        self.assertIn("entity_id", rel_fam["required_fields"])

    def test_CON_18_no_declared_reference_field_is_undeclared_in_the_family(self):
        """A field_semantics entry for a field the family does not declare is a
        dangling declaration - the mirror of a dangling reference."""
        problems = []
        for fam in self.fams:
            declared = set(self.fields(fam))
            for fld in self.semantics(fam):
                if fld not in declared:
                    problems.append("%s.field_semantics declares %s, not a field of %s"
                                    % (fam, fld, fam))
        self.assertEqual([], problems)


class TestSpatialClosure(_Corpus):

    #: Names that denote a measured spatial quantity. Used to FIND candidates;
    #: the declaration itself is semantic, not name-derived.
    LOOKS_SPATIAL = re.compile(
        r"(?:^|_)(origin|centre|center|extent|extents|volume|axis|frame|frames|"
        r"pose|offset|position|coordinate|coordinates|translation|rotation|"
        r"envelope|sweep|placement)(?:$|_)", re.I)

    def test_CON_06_every_spatial_field_declares_frame_semantics(self):
        problems = []
        for fam in self.fams:
            sem = self.semantics(fam)
            for fld in self.fields(fam):
                if fld == "entity_id":
                    continue
                spec = sem.get(fld, {})
                if spec.get("kind") == "spatial":
                    if not spec.get("frame"):
                        problems.append("%s.%s is spatial with no frame" % (fam, fld))
                elif self.LOOKS_SPATIAL.search(fld) and spec.get("kind") not in (
                        "enum", "reference", "derived", "engineering_conclusion"):
                    problems.append("%s.%s looks spatial and declares nothing"
                                    % (fam, fld))
            for fld, spec in ((self.fams[fam] or {}).get("extendable_fields", {}) or {}).items():
                s = sem.get(fld, {})
                if self.LOOKS_SPATIAL.search(fld) and s.get("kind") != "spatial":
                    problems.append("extendable %s.%s looks spatial and declares nothing"
                                    % (fam, fld))
        self.assertEqual([], problems)


class TestConceptResolutions(_Corpus):

    def test_CON_13_principle_has_one_canonical_shape(self):
        shape = self.fams["Candidate"].get("principle_shape")
        self.assertIsNotNone(shape, "Candidate.principle declares no shape")
        self.assertEqual("mapping", shape["kind"])
        self.assertIn("bare string", shape["rejected_shapes"])
        self.assertIn("principle", self.fams["Candidate"]["required_fields"])

    def test_CON_14_retired_hypothesis_families_are_not_contract_targets(self):
        problems = []
        for dirpath, _d, names in os.walk(_paths.CONTRACTS):
            for n in sorted(names):
                if not n.endswith(".yaml"):
                    continue
                path = os.path.join(dirpath, n)
                text = open(path).read()
                for retired in RETIRED_FAMILIES:
                    if re.search(r"\b%s\b" % retired, text):
                        problems.append("%s still names %s"
                                        % (os.path.relpath(path, REPO), retired))
        self.assertEqual([], problems)
        for retired in RETIRED_FAMILIES:
            self.assertNotIn(retired, self.fams)
        for replacement in ("PhysicalEffectObligation", "PhysicalInteraction"):
            self.assertIn(replacement, self.fams)
            self.assertTrue(self.fams[replacement].get("owned_by"))

    def test_addresses_obligations_has_one_meaning(self):
        users, problems = [], []
        for fam, v in self.fams.items():
            if "addresses_obligations" in self.fields(fam):
                users.append(fam)
                spec = self.semantics(fam).get("addresses_obligations", {})
                if spec.get("target") != "Obligation":
                    problems.append("%s: addresses_obligations targets %s"
                                    % (fam, spec.get("target")))
        self.assertEqual([], problems)
        self.assertTrue(users, "no family declares the canonical name")
        # The divergent spellings are gone from the canonical corpus.
        for dead in ("obligations_addressed", "discharges_obligations"):
            for fam in self.fams:
                self.assertNotIn(dead, self.fields(fam),
                                 "%s still uses %s" % (fam, dead))

    def test_CON_15_mobility_domain_and_disposition_are_distinguishable(self):
        me = self.fams["MobilityExpectation"]
        split = me.get("authorship_split")
        self.assertIsNotNone(split, "MobilityExpectation declares no authorship split")
        self.assertEqual("DERIVED", split["domain"]["authority_class"])
        self.assertEqual("AUTHORITATIVE", split["disposition"]["authority_class"])
        self.assertTrue(split["disposition"]["premise_required"])
        # WHICH premise is per disposition. A single premise_target named only
        # BLOCKED_BY's, so INTENDED and IRRELEVANT_BECAUSE had no declared
        # evidence type at all - and none of the three was checkable, because a
        # premise inside a list of records was invisible to both boundaries.
        self.assertEqual("field_semantics.dispositions.premise_field",
                         split["disposition"]["premise_target"])
        premise = me["field_semantics"]["dispositions"]
        self.assertEqual("premise_record_list", premise["kind"])
        self.assertEqual("disposition", premise["discriminator"])
        self.assertEqual({"INTENDED": "by_joint",
                          "BLOCKED_BY": "constraint_relation",
                          "IRRELEVANT_BECAUSE": "scenario",
                          "UNDISPOSITIONED": None}, premise["premise_field"])
        for field, target in (("by_joint", "Joint"),
                              ("constraint_relation", "ConstraintRelation"),
                              ("scenario", "Scenario")):
            spec = premise["record_field_semantics"][field]
            self.assertEqual("reference", spec["kind"])
            self.assertEqual(target, spec["target"])
            self.assertFalse(spec["resolvable"], "%s may dangle" % field)
        self.assertIn("UNDISPOSITIONED", me["disposition_values"])
        # Retired, with the record of why kept beside the live vocabulary.
        self.assertNotIn("MAINTAINED_BY_CLASS", me["disposition_values"])
        self.assertIn("MAINTAINED_BY_CLASS", me["retired_disposition_values"])
        # Totality is bookkeeping, and the contract says so in as many words.
        self.assertIn("BOOKKEEPING", split["domain"]["totality"])

    def test_CON_09_no_model_output_field_is_defined_only_in_prompt_prose(self):
        """The fields the audit found prompt-only now have canonical homes."""
        promoted = ("required_by_actors", "reach_targets")
        declared = set()
        for fam in self.fams:
            declared |= set(self.fields(fam))
        for fld in promoted:
            self.assertIn(fld, declared, "%s has no canonical contract home" % fld)
        fr = self.fams["FunctionalRegion"]
        for fld in promoted:
            self.assertIn(fld, fr.get("optional_fields", []))
            self.assertEqual("reference", self.semantics("FunctionalRegion")[fld]["kind"])


class TestStageResponsibility(_Corpus):

    def test_CON_10_every_stage_and_the_gate_declare_responsibility(self):
        self.assertEqual(set(STAGES_UNDER_S2), set(self.resp["stages"]))
        for sid, s in self.resp["stages"].items():
            with self.subTest(stage=sid):
                self.assertTrue(s["responsibility"].strip())
                self.assertTrue(s["engineering_questions"])
                self.assertIn("permitted_output_semantics", s)
                self.assertIn("prohibited_decisions", s)

    def test_CON_11_every_premise_class_is_justified_by_an_engineering_question(self):
        problems = []
        for sid, s in self.resp["stages"].items():
            questions = set(s["engineering_questions"])
            for pc in s["required_reasoning_premise_classes"]:
                if not pc.get("class"):
                    problems.append("%s: a premise class has no name" % sid)
                q = pc.get("justified_by_question")
                if q not in questions:
                    problems.append("%s: premise %r cites a question that is not declared: %r"
                                    % (sid, pc.get("class"), q))
                if not (pc.get("why") or "").strip():
                    problems.append("%s: premise %r gives no reason" % (sid, pc.get("class")))
        self.assertEqual([], problems)

    def test_CON_11b_a_stage_with_no_premises_says_why(self):
        for sid, s in self.resp["stages"].items():
            with self.subTest(stage=sid):
                if not s["required_reasoning_premise_classes"]:
                    self.assertTrue((s.get("no_premises_because") or "").strip(),
                                    "%s declares no premises and no reason" % sid)

    def test_CON_12_representational_and_reasoning_constructs_stay_distinct(self):
        """Two sources, two files, and neither may be derived from the other."""
        # Representational dependencies live per field in the entity contract.
        self.assertIn("semantic_dependency", self.ds["field_semantics_rules"])
        # Reasoning premises live per stage in the responsibility contract.
        for s in self.resp["stages"].values():
            self.assertIn("required_reasoning_premise_classes", s)
        # The entity contract must not carry reasoning-premise declarations...
        self.assertNotIn("required_reasoning_premise_classes", self.ds)
        # ...and the responsibility contract must not carry field semantics.
        self.assertNotIn("field_semantics", self.resp)
        # And the separation is stated, so a later reader cannot merge them by
        # accident (S-3 is where they are unioned).
        self.assertIn("NOT the reasoning-premise half",
                      self.ds["field_semantics_rules"]["semantic_dependency"])


class TestStatusAndAuthority(_Corpus):

    def test_CON_16_the_four_status_constructs_are_distinct(self):
        constructs = self.status["status_constructs"]
        self.assertEqual({"EXECUTION", "CONTRACT_COMPLETENESS", "EVIDENCE_MATURITY",
                          "ENGINEERING_ESTABLISHMENT"}, set(constructs))
        seen = {}
        for name, c in constructs.items():
            for term in c.get("vocabulary", []):
                self.assertNotIn(term, seen,
                                 "%r belongs to both %s and %s" % (term, seen.get(term), name))
                seen[term] = name
            self.assertTrue(c["asserts"].strip())
            self.assertTrue(c["does_not_assert"].strip())
        self.assertTrue(self.status["status_construct_rules"])

    def test_contract_authority_names_one_source_per_semantic_category(self):
        srcs = self.authority["sources_of_truth"]
        files = [v["file"] for v in srcs.values()]
        self.assertEqual(len(files), len(set(files)), "two categories share a file")
        for cat, v in srcs.items():
            with self.subTest(category=cat):
                self.assertTrue(v["owns"])
                self.assertTrue(os.path.exists(os.path.join(REPO, v["file"])))
        for proj in self.authority["projections"]:
            # A projection may legitimately project more than one category (the
            # stage corpus projects entity semantics AND stage responsibility).
            # Every category it names must still be a declared source.
            named = proj["projects"]
            for cat in (named if isinstance(named, list) else [named]):
                with self.subTest(projection=proj["file"], category=cat):
                    self.assertIn(cat, srcs)


class TestContractImmutability(_Corpus):

    def test_CON_17_loaded_contract_semantics_cannot_be_modified(self):
        """The S-1 deferral, closed. Mutating a read changes no rule."""
        from ver3.assy_v3.state.design_state import ContractError, Contracts
        c = Contracts()
        before = sorted(c.extendable_fields("Joint"))

        got = c.families
        got["Joint"]["extendable_fields"]["role"] = "s04"
        got["Joint"]["owned_by"] = "s99"
        c.stages["s04"]["owns"].append("Requirement")
        c.authority["default_class"] = "EPHEMERAL"
        c.universally_ownable.add("Joint")

        self.assertEqual(before, sorted(c.extendable_fields("Joint")))
        self.assertEqual("s03", c.owner_of("Joint"))
        self.assertEqual("AUTHORITATIVE", c.authority_class("Joint").value)
        self.assertFalse(c.may_create("s04", "Requirement"))

        for name in ("families", "stages", "authority", "prohibited",
                     "universally_ownable"):
            with self.subTest(attr=name):
                with self.assertRaisesRegex(ContractError, "IMMUTABLE_CONTRACT"):
                    setattr(c, name, {})

    def test_CON_17b_two_reads_are_independent_and_readers_still_work(self):
        from ver3.assy_v3.state.design_state import Contracts
        c = Contracts()
        a, b = c.families, c.families
        self.assertIsNot(a, b)
        a["Joint"]["purpose"] = "changed"
        self.assertNotEqual("changed", b["Joint"]["purpose"])
        self.assertTrue(c.required_fields("Joint"))
        self.assertTrue(c.field_semantics("Joint"))
        self.assertTrue(c.may_create("s03", "Joint"))
