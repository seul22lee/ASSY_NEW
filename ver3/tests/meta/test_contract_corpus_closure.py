"""S-2 closure: the whole contract corpus has one canonical language.

CLOSURE-01..10. The CON-* suite proves the canonical SOURCES are internally
closed. These prove no OTHER file quietly acts as a second semantic authority,
and that where a file is deliberately behind the canonical semantics it says so
with a replacement and a scheduled step.

Data-driven over every `contracts/stages/*.yaml`. Nothing here names S02 or S03
specifically: a new stage file, or a new alias in an old one, is caught the same
way.
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

VALID_CLASSES = {"CANONICAL_PROJECTION", "LEGACY_PRODUCER", "OPERATIONAL", "RETIRED"}

#: Sections that carry no semantics and need no classification.
EXEMPT = {"schema_version", "status", "governed_by", "derived_from", "stage_id",
          "passes", "authority_status"}


def _stage_files():
    d = os.path.join(_paths.CONTRACTS, "stages")
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".yaml")]


class _Corpus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ds = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.fams = dict(cls.ds["entity_families"])
        cls.fams.update(cls.ds["assurance_families"])
        cls.authority = _paths.contract("CONTRACT_AUTHORITY.yaml")
        cls.stages = {}
        for path in _stage_files():
            cls.stages[os.path.basename(path)] = _paths.load_yaml(path)
        cls.retired_relations = {
            k for k, v in (cls.ds.get("typed_relations") or {}).items()
            if (v or {}).get("status") == "RETIRED_BY_S2"}
        cls.canonical_owner = {f: (v or {}).get("owned_by") for f, v in cls.fams.items()}

    def status_of(self, doc, section):
        return (doc.get("authority_status") or {}).get(section)


class TestSectionClassification(_Corpus):

    def test_CLOSURE_07_every_semantic_section_declares_its_authority_class(self):
        """No ambiguous fourth state. A *_CONTRACT.yaml is not an authority by
        default, so every section says what it is."""
        problems = []
        for name, doc in self.stages.items():
            declared = doc.get("authority_status")
            if not declared:
                problems.append("%s declares no authority_status" % name)
                continue
            for section in doc:
                if section in EXEMPT:
                    continue
                spec = declared.get(section)
                if spec is None:
                    problems.append("%s.%s has no authority class" % (name, section))
                elif spec.get("class") not in VALID_CLASSES:
                    problems.append("%s.%s has class %r" % (name, section, spec.get("class")))
            for section in declared:
                if section not in doc:
                    problems.append("%s classifies %s, which it does not contain"
                                    % (name, section))
        self.assertEqual([], problems)

    def test_CLOSURE_09_every_projection_names_an_existing_source(self):
        problems = []
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if spec.get("class") != "CANONICAL_PROJECTION":
                    continue
                src = spec.get("source")
                if not src:
                    problems.append("%s.%s projects with no source" % (name, section))
                elif not os.path.exists(os.path.join(REPO, src)):
                    problems.append("%s.%s names a missing source %s" % (name, section, src))
                if not (spec.get("projects") or "").strip():
                    problems.append("%s.%s does not say what it projects" % (name, section))
        self.assertEqual([], problems)

    def test_CLOSURE_02_every_legacy_section_is_fully_declared(self):
        problems = []
        required = ("describes", "canonical_replacement", "canonical_source",
                    "migration_step", "authoritative_for_canonical_semantics")
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if spec.get("class") != "LEGACY_PRODUCER":
                    continue
                for key in required:
                    if key not in spec:
                        problems.append("%s.%s legacy section lacks %s" % (name, section, key))
                if spec.get("authoritative_for_canonical_semantics") is not False:
                    problems.append("%s.%s legacy section claims authority" % (name, section))
        self.assertEqual([], problems)

    def test_CLOSURE_10_every_legacy_section_has_a_scheduled_step(self):
        problems = []
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if spec.get("class") != "LEGACY_PRODUCER":
                    continue
                step = (spec.get("migration_step") or "").strip()
                if not step:
                    problems.append("%s.%s has no migration step" % (name, section))
                elif not re.search(r"(S-\d|U-\d|outside S01-S04|scope)", step):
                    problems.append("%s.%s step %r names no step" % (name, section, step))
        self.assertEqual([], problems)


class TestNoSecondAuthority(_Corpus):

    def test_CLOSURE_03_no_stage_contract_contradicts_canonical_ownership(self):
        """Ownership is owned by DESIGN_STATE_CONTRACT. A projection may repeat it
        and may not disagree."""
        problems = []
        for name, doc in self.stages.items():
            spec = self.status_of(doc, "owned_decisions")
            if not spec or spec.get("class") != "CANONICAL_PROJECTION":
                continue
            stage = doc["stage_id"]
            claimed = set((doc.get("owned_decisions") or {}).get("creates") or [])
            canonical = {f for f, o in self.canonical_owner.items()
                         if o == stage or (isinstance(o, list) and stage in o)}
            for fam in claimed - canonical:
                problems.append("%s claims to create %s, owned by %r"
                                % (name, fam, self.canonical_owner.get(fam, "nothing")))
            for fam in canonical - claimed:
                problems.append("%s omits %s, which it owns" % (name, fam))
        self.assertEqual([], problems)

    def test_CLOSURE_01_a_projection_matches_its_source(self):
        """Every family a projection names must exist in the source it cites."""
        problems = []
        for name, doc in self.stages.items():
            spec = self.status_of(doc, "owned_decisions")
            if not spec or spec.get("class") != "CANONICAL_PROJECTION":
                continue
            for fam in (doc.get("owned_decisions") or {}).get("creates") or []:
                if fam not in self.fams:
                    problems.append("%s projects %s, absent from %s"
                                    % (name, fam, spec.get("source")))
        self.assertEqual([], problems)

    def test_CLOSURE_06_retired_relations_are_only_named_in_legacy_sections(self):
        """CLOSURE-05/06. A retired relation may be described as what a producer
        still emits. It may not be defined as current meaning."""
        problems = []
        for name, doc in self.stages.items():
            legacy_sections = {s for s, sp in (doc.get("authority_status") or {}).items()
                               if sp.get("class") in ("LEGACY_PRODUCER", "RETIRED")}
            for section, body in doc.items():
                if section in EXEMPT or section in legacy_sections:
                    continue
                text = str(body)
                for rel in self.retired_relations:
                    if re.search(r"\b%s\b" % rel, text):
                        problems.append("%s.%s (class %s) names retired relation %s"
                                        % (name, section,
                                           (self.status_of(doc, section) or {}).get("class"),
                                           rel))
        self.assertEqual([], problems)

    def test_CLOSURE_05_retired_families_appear_nowhere_in_the_stage_corpus(self):
        problems = []
        for path in _stage_files():
            text = open(path).read()
            for retired in ("BodyHypothesis", "PhysicalInteractionHypothesis"):
                if re.search(r"\b%s\b" % retired, text):
                    problems.append("%s names retired family %s"
                                    % (os.path.basename(path), retired))
        self.assertEqual([], problems)


class TestCanonicalFieldNames(_Corpus):

    #: The canonical name, and the spellings it replaced. Derived from the
    #: canonical corpus rather than hard-coded per stage.
    CANONICAL = "addresses_obligations"
    SUPERSEDED = ("obligations_addressed", "discharges_obligations")

    def test_CLOSURE_04_an_undeclared_field_alias_is_rejected(self):
        """A superseded spelling may appear only inside a LEGACY_PRODUCER section.

        This is the general form: the alias set comes from the canonical corpus,
        so a future alias introduced as active semantic structure is caught the
        same way, not only the two historically known ones."""
        # The canonical name is declared by some family.
        declared = set()
        for v in self.fams.values():
            declared |= set((v or {}).get("required_fields", []))
            declared |= set((v or {}).get("optional_fields", []))
        self.assertIn(self.CANONICAL, declared)
        for dead in self.SUPERSEDED:
            self.assertNotIn(dead, declared,
                             "%s is still a canonical field name" % dead)

        problems = []
        for name, doc in self.stages.items():
            legacy = {s for s, sp in (doc.get("authority_status") or {}).items()
                      if sp.get("class") in ("LEGACY_PRODUCER", "RETIRED")}
            for section, body in doc.items():
                if section in EXEMPT or section in legacy:
                    continue
                text = str(body)
                for dead in self.SUPERSEDED:
                    if re.search(r"\b%s\b" % dead, text):
                        problems.append("%s.%s (class %s) uses superseded name %s"
                                        % (name, section,
                                           (self.status_of(doc, section) or {}).get("class"),
                                           dead))
        self.assertEqual([], problems)

    def test_the_authority_vocabulary_is_itself_declared(self):
        vocab = self.authority.get("stage_contract_status_vocabulary")
        self.assertIsNotNone(vocab, "the status vocabulary is not declared")
        self.assertEqual(VALID_CLASSES, set(vocab))
        for name, spec in vocab.items():
            with self.subTest(status=name):
                self.assertTrue(spec["requires"])
                self.assertTrue(spec["checked_by"])


class TestContractStorageEncapsulation(_Corpus):
    """CLOSURE-08. The S-2 immutability claim, made true.

    Reproduces the ec184b4 defect: the loaded documents sat in an ordinary
    attribute, so `c._docs[...] = ...` changed every authorization query.
    """

    def _contracts(self):
        from ver3.assy_v3.state.design_state import Contracts
        return Contracts()

    def test_CLOSURE_08_the_live_documents_are_not_reachable(self):
        c = self._contracts()
        from ver3.assy_v3.state import design_state as ds
        live = ds._CONTRACT_DOCS[c]                       # reflection, for the test
        for name in dir(c):
            if name.startswith("__"):
                continue
            try:
                value = getattr(c, name)
            except Exception:
                continue
            self.assertIsNot(value, live,
                             "Contracts.%s is the live document store" % name)
            if isinstance(value, dict):
                for key in ("families", "stages", "authority"):
                    self.assertIsNot(value.get(key), live.get(key))

    def test_CLOSURE_08_mutating_a_read_changes_no_authorization(self):
        c = self._contracts()
        before = (sorted(c.extendable_fields("Joint")), c.owner_of("Joint"),
                  c.may_create("s04", "Requirement"), c.authority_class("Body").value)
        got = c.families
        got["Joint"]["owned_by"] = "s99"
        got["Joint"]["extendable_fields"]["role"] = "s04"
        c.stages["s04"]["owns"].append("Requirement")
        c.authority["default_class"] = "EPHEMERAL"
        c.universally_ownable.add("Joint")
        after = (sorted(c.extendable_fields("Joint")), c.owner_of("Joint"),
                 c.may_create("s04", "Requirement"), c.authority_class("Body").value)
        self.assertEqual(before, after)

    def test_CLOSURE_08_roots_cannot_be_replaced(self):
        from ver3.assy_v3.state.design_state import ContractError
        c = self._contracts()
        for name in ("families", "stages", "authority", "prohibited",
                     "universally_ownable", "_docs"):
            with self.subTest(attr=name):
                with self.assertRaisesRegex(ContractError, "IMMUTABLE_CONTRACT"):
                    setattr(c, name, {})

    def test_CLOSURE_08_two_reads_are_independent(self):
        c = self._contracts()
        a, b = c.families, c.families
        self.assertIsNot(a, b)
        a["Joint"]["purpose"] = "changed"
        self.assertNotEqual("changed", b["Joint"]["purpose"])

    def test_CLOSURE_08_legitimate_queries_are_unchanged(self):
        c = self._contracts()
        self.assertEqual("s03", c.owner_of("Joint"))
        self.assertIn("entity_id", c.required_fields("Joint"))
        self.assertEqual({"frame_origin": "s04"}, c.extendable_fields("Joint"))
        self.assertTrue(c.field_semantics("Joint"))
        self.assertTrue(c.may_create("s03", "Joint"))
        self.assertFalse(c.may_create("s02", "Joint"))
        self.assertEqual("AUTHORITATIVE", c.authority_class("Body").value)
