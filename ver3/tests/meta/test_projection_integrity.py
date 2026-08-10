"""PROJ-01..10: a declared canonical projection is actually checked.

S-2 closure classified every stage-contract section, but a section could be
labelled CANONICAL_PROJECTION while naming only a FILE. Nothing resolved WHICH
fact it projected and nothing compared values, so the claim "one authoritative
edit per fact, plus checked projections" was broader than the enforcement: only
`owned_decisions` was really checked, and by hard-coded section name.

This validator is data-driven. It discovers every CANONICAL_PROJECTION in every
stage contract, resolves its source fragment, applies its declared relation, and
fails on mismatch. A new projection enters the validation set automatically.

The honest half matters as much: a paraphrase is NOT a projection. Sections
holding prose summaries or stage-local detail are OPERATIONAL, and PROJ-06 exists
so nobody can quietly promote prose to canonical equality later.
"""
from __future__ import annotations

import os
import sys
import unittest

from . import _paths

REPO = _paths.REPO_ROOT
if REPO not in sys.path:
    sys.path.insert(0, REPO)

#: The whole supported relation vocabulary. Deliberately tiny - a transformation
#: language would let a projection "match" by being clever rather than by being
#: the same fact.
RELATIONS = {"EXACT", "SUBSET", "ORDERED_SUBSET"}

OWNERSHIP_PATH_PREFIX = "entity_families+assurance_families[*].owned_by == "


def stage_ids_in(path):
    """The stage ids a canonical path refers to, for any depth.

    `stages.s02` and `stages.s02.engineering_questions` both name stage `s02`;
    only the segment after `stages.` is a stage id, and anything deeper is a
    field. The earlier form split the whole remainder on separators, so
    `stages.s02.engineering_questions` produced the single token
    `s02.engineering_questions` and would have been rejected as a nonexistent
    stage. No projection used a `stages.` path yet, so the check passed
    vacuously while being wrong.

    Also handles the prose-joined pointer forms the corpus uses, e.g.
    `stages.s03a and s03b` and `stages.s04a, gate and s04b`.
    """
    if not path.startswith("stages."):
        return []
    remainder = path[len("stages."):]
    head = remainder.split(".", 1)[0]           # drop any field path
    return [tok for tok in head.replace(" and ", " ").replace(",", " ").split() if tok]


def _stage_files():
    d = os.path.join(_paths.CONTRACTS, "stages")
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".yaml")]


def _resolve(spec, docs):
    """Resolve a declared source fragment to its canonical value.

    Two forms are supported, and nothing else: a dotted path into a canonical
    document, and the ownership derivation. An unresolvable form is a failure,
    never a silent pass.
    """
    path = spec["path"]
    if path.startswith(OWNERSHIP_PATH_PREFIX):
        stage = path[len(OWNERSHIP_PATH_PREFIX):].strip()
        ds = docs["ver3/contracts/DESIGN_STATE_CONTRACT.yaml"]
        fams = dict(ds["entity_families"])
        fams.update(ds["assurance_families"])
        return sorted(f for f, v in fams.items()
                      if (v or {}).get("owned_by") == stage
                      or (isinstance((v or {}).get("owned_by"), list)
                          and stage in (v or {}).get("owned_by")))
    node = docs[spec["file"]]
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


class _Projections(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.docs = {}
        for name in ("DESIGN_STATE_CONTRACT.yaml", "STAGE_RESPONSIBILITY_CONTRACT.yaml",
                     "CONTRACT_AUTHORITY.yaml", "STATUS_SEMANTICS.yaml"):
            cls.docs["ver3/contracts/" + name] = _paths.contract(name)
        cls.stages = {os.path.basename(p): _paths.load_yaml(p) for p in _stage_files()}
        cls.canonical_stages = set(
            cls.docs["ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml"]["stages"])

    def projections(self):
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if spec.get("class") == "CANONICAL_PROJECTION":
                    yield name, doc, section, spec


class TestProjectionMetadata(_Projections):

    def test_PROJ_01_every_projection_names_a_resolvable_source_file(self):
        problems = []
        for name, _doc, section, spec in self.projections():
            src = (spec.get("canonical_source") or {}).get("file")
            if not src:
                problems.append("%s.%s names no source file" % (name, section))
            elif not os.path.exists(os.path.join(REPO, src)):
                problems.append("%s.%s names missing %s" % (name, section, src))
        self.assertEqual([], problems)

    def test_PROJ_02_every_projection_names_a_resolvable_source_fragment(self):
        problems = []
        for name, _doc, section, spec in self.projections():
            cs = spec.get("canonical_source") or {}
            if not cs.get("path"):
                problems.append("%s.%s names no source path" % (name, section))
                continue
            try:
                _resolve(cs, self.docs)
            except Exception as exc:
                problems.append("%s.%s path %r does not resolve (%s)"
                                % (name, section, cs["path"], type(exc).__name__))
        self.assertEqual([], problems)

    def test_PROJ_03_every_projection_declares_a_supported_relation(self):
        problems = []
        for name, _doc, section, spec in self.projections():
            rel = (spec.get("canonical_source") or {}).get("relation")
            if rel not in RELATIONS:
                problems.append("%s.%s declares relation %r" % (name, section, rel))
            if not spec.get("projected_key"):
                problems.append("%s.%s names no projected key" % (name, section))
        self.assertEqual([], problems)

    def test_PROJ_04_every_projection_satisfies_its_relation(self):
        problems = []
        for name, doc, section, spec in self.projections():
            cs = spec["canonical_source"]
            canonical = _resolve(cs, self.docs)
            projected = doc[section]
            key = spec.get("projected_key")
            if key:
                projected = (projected or {}).get(key)
            problems += _compare(name, section, cs["relation"], projected, canonical)
        self.assertEqual([], problems)

    def test_PROJ_05_no_unresolved_canonical_stage_identifier(self):
        """A stage file may not project a canonical stage that does not exist.

        The current S03 contract is one file while the canonical architecture
        defines s03a and s03b. Inventing a canonical `s03` to satisfy a test
        would create a fact rather than check one, so any pointer to a
        non-existent canonical stage is a failure.
        """
        problems = []
        for name, doc, section, spec in self.projections():
            path = (spec.get("canonical_source") or {}).get("path", "")
            for sid in stage_ids_in(path):
                if sid not in self.canonical_stages:
                    problems.append("%s.%s projects canonical stage %r, which does not exist"
                                    % (name, section, sid))
        self.assertEqual([], problems)

    def test_PROJ_05b_non_binding_pointers_are_not_dangling(self):
        """NON-BINDING means "not semantically equal", not "unchecked".

        A section that claims the canonical value lives somewhere must point
        somewhere real: the file exists, the path resolves, and any stage id in it
        is a real canonical stage. A dangling pointer misdirects a reader as
        effectively as a wrong value. Equality is still never compared."""
        problems = []
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                see = spec.get("see_canonical")
                if not see:
                    continue
                if see.get("binding", False):
                    problems.append("%s.%s pointer claims to be binding" % (name, section))
                if not os.path.exists(os.path.join(REPO, see.get("file", ""))):
                    problems.append("%s.%s pointer names missing file %r"
                                    % (name, section, see.get("file")))
                    continue
                for sid in stage_ids_in(see.get("path", "")):
                    if sid not in self.canonical_stages:
                        problems.append("%s.%s pointer names stage %r, which does not exist"
                                        % (name, section, sid))
                if not see.get("path", "").startswith("stages."):
                    try:
                        _resolve({"file": see["file"], "path": see["path"]}, self.docs)
                    except Exception:
                        problems.append("%s.%s pointer path %r does not resolve"
                                        % (name, section, see.get("path")))
        self.assertEqual([], problems)

    def test_PROJ_06_prose_cannot_pass_as_an_exact_projection(self):
        """A paraphrase is not equality.

        Every EXACT projection must compare structured values. A plain string
        projected against a canonical list would only ever "match" by a fuzzy
        rule, and no fuzzy rule is supported.
        """
        problems = []
        for name, doc, section, spec in self.projections():
            cs = spec["canonical_source"]
            canonical = _resolve(cs, self.docs)
            projected = doc[section]
            if spec.get("projected_key"):
                projected = (projected or {}).get(spec["projected_key"])
            if isinstance(projected, str) and not isinstance(canonical, str):
                problems.append("%s.%s projects prose onto a %s"
                                % (name, section, type(canonical).__name__))
            if isinstance(projected, str) and isinstance(canonical, str) \
                    and projected.strip() != canonical.strip():
                problems.append("%s.%s claims EXACT prose equality and differs"
                                % (name, section))
        self.assertEqual([], problems)


class TestClassificationIntegrity(_Projections):

    def test_PROJ_07_every_section_has_exactly_one_classification(self):
        problems = []
        exempt = {"schema_version", "status", "governed_by", "derived_from",
                  "stage_id", "passes", "authority_status"}
        for name, doc in self.stages.items():
            declared = doc.get("authority_status") or {}
            for section in doc:
                if section in exempt:
                    continue
                if section not in declared:
                    problems.append("%s.%s unclassified" % (name, section))
            for section in declared:
                if section not in doc:
                    problems.append("%s classifies absent %s" % (name, section))
        self.assertEqual([], problems)

    def test_PROJ_08_legacy_sections_declare_replacement_and_step(self):
        problems = []
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if spec.get("class") != "LEGACY_PRODUCER":
                    continue
                for key in ("canonical_replacement", "migration_step"):
                    if not (spec.get(key) or "").strip():
                        problems.append("%s.%s lacks %s" % (name, section, key))
                if spec.get("authoritative_for_canonical_semantics") is not False:
                    problems.append("%s.%s claims authority" % (name, section))
        self.assertEqual([], problems)

    def test_PROJ_09_operational_sections_are_non_authoritative(self):
        problems = []
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if spec.get("class") != "OPERATIONAL":
                    continue
                if spec.get("authoritative_for_canonical_semantics") is not False:
                    problems.append("%s.%s does not declare itself non-authoritative"
                                    % (name, section))
                if not (spec.get("note") or "").strip():
                    problems.append("%s.%s has no note" % (name, section))
        self.assertEqual([], problems)


def _compare(name, section, relation, projected, canonical):
    """The whole relation vocabulary, in one place."""
    if relation == "EXACT":
        if projected != canonical:
            missing = ([x for x in canonical if x not in (projected or [])]
                       if isinstance(canonical, list) else canonical)
            extra = ([x for x in (projected or []) if x not in canonical]
                     if isinstance(canonical, list) else projected)
            return ["%s.%s EXACT mismatch: missing=%s extra=%s"
                    % (name, section, missing, extra)]
    elif relation == "SUBSET":
        extra = [x for x in (projected or []) if x not in canonical]
        if extra:
            return ["%s.%s SUBSET violated: %s" % (name, section, extra)]
    elif relation == "ORDERED_SUBSET":
        it = iter(canonical)
        if not all(any(x == y for y in it) for x in (projected or [])):
            return ["%s.%s ORDERED_SUBSET violated" % (name, section)]
    else:
        return ["%s.%s unsupported relation %r" % (name, section, relation)]
    return []


class TestNegativeControls(_Projections):
    """PROJ-10. A validator nobody has seen fail is not evidence.

    Each control perturbs a synthetic copy - never the repository - and asserts
    the mechanism reports it. They prove the validator checks ARBITRARY
    projections, not the examples that happen to exist today.
    """

    def _synthetic(self):
        import copy
        return copy.deepcopy(self.docs)

    def test_A_a_stale_ownership_projection_is_caught(self):
        docs = self._synthetic()
        ds = docs["ver3/contracts/DESIGN_STATE_CONTRACT.yaml"]
        ds["entity_families"]["Joint"]["owned_by"] = "s99"      # canonical moved
        spec = {"file": "ver3/contracts/DESIGN_STATE_CONTRACT.yaml",
                "path": OWNERSHIP_PATH_PREFIX + "s03", "relation": "EXACT"}
        canonical = _resolve(spec, docs)
        stale = sorted(set(canonical) | {"Joint"})              # projection not updated
        self.assertTrue(_compare("X", "owned_decisions", "EXACT", stale, canonical))

    def test_B_a_stale_question_projection_is_caught(self):
        docs = self._synthetic()
        spec = {"file": "ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml",
                "path": "stages.s02.engineering_questions", "relation": "EXACT"}
        canonical = _resolve(spec, docs)
        stale = list(canonical)[:-1]
        self.assertTrue(_compare("X", "q", "EXACT", stale, canonical))

    def test_C_a_bad_canonical_source_path_is_caught(self):
        with self.assertRaises(KeyError):
            _resolve({"file": "ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml",
                      "path": "stages.s99.engineering_questions"}, self.docs)

    def test_D_an_undeclared_relation_is_caught(self):
        self.assertTrue(_compare("X", "s", "FUZZY_MATCH", ["a"], ["a"]))

    def test_E_an_unresolved_s03_canonical_stage_is_caught(self):
        """`s03` is not a canonical stage; s03a and s03b are."""
        self.assertNotIn("s03", self.canonical_stages)
        self.assertIn("s03a", self.canonical_stages)
        self.assertIn("s03b", self.canonical_stages)
        with self.assertRaises(KeyError):
            _resolve({"file": "ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml",
                      "path": "stages.s03.engineering_questions"}, self.docs)

    def test_F_prose_marked_as_an_exact_projection_is_caught(self):
        docs = self._synthetic()
        canonical = _resolve({"file": "ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml",
                              "path": "stages.s02.engineering_questions"}, docs)
        prose = "What must physically be true, and what loads exist?"
        self.assertIsInstance(canonical, list)
        self.assertIsInstance(prose, str)
        self.assertTrue(_compare("X", "q", "EXACT", prose, canonical),
                        "prose compared equal to a canonical list")

    def test_G_the_live_corpus_still_passes_after_the_controls(self):
        """The controls perturbed copies only."""
        for name, doc, section, spec in self.projections():
            canonical = _resolve(spec["canonical_source"], self.docs)
            projected = doc[section]
            if spec.get("projected_key"):
                projected = (projected or {}).get(spec["projected_key"])
            self.assertEqual([], _compare(name, section,
                                          spec["canonical_source"]["relation"],
                                          projected, canonical))


# =====================================================================
# META-01..08 - the declared schema describes what is actually enforced
# =====================================================================
class TestSchemaMetadataHygiene(_Projections):
    """A schema that describes something other than what is checked is the same
    defect this corpus exists to prevent, one level up."""

    def _vocab(self):
        return self.docs["ver3/contracts/CONTRACT_AUTHORITY.yaml"][
            "stage_contract_status_vocabulary"]["CANONICAL_PROJECTION"]

    def test_META_01_schema_names_the_fields_actually_required(self):
        v = self._vocab()
        self.assertEqual({"canonical_source", "projected_key", "projects"},
                         set(v["requires"]))
        self.assertEqual({"file", "path", "relation"},
                         set(v["requires_nested"]["canonical_source"]))
        # And what it names is what the corpus actually carries.
        for name, _doc, section, spec in self.projections():
            with self.subTest(where="%s.%s" % (name, section)):
                for key in v["requires"]:
                    self.assertIn(key, spec)
                for key in v["requires_nested"]["canonical_source"]:
                    self.assertIn(key, spec["canonical_source"])

    def test_META_02_checked_by_names_the_actual_enforcement(self):
        v = self._vocab()
        self.assertTrue([c for c in v["checked_by"] if c.startswith("PROJ-")],
                        "checked_by names no PROJ check while PROJ enforces this")
        # The still-relevant CLOSURE checks were not dropped.
        for kept in ("CLOSURE-01", "CLOSURE-03", "CLOSURE-09"):
            self.assertIn(kept, v["checked_by"])

    def test_META_03_a_bare_stage_path_resolves_its_stage_id(self):
        self.assertEqual(["s02"], stage_ids_in("stages.s02"))

    def test_META_04_a_field_path_resolves_the_same_stage_id(self):
        """The bug: this previously produced 's02.engineering_questions'."""
        self.assertEqual(["s02"], stage_ids_in("stages.s02.engineering_questions"))
        self.assertEqual(["s01"], stage_ids_in("stages.s01.required_reasoning_premise_classes"))
        # Prose-joined pointer forms the corpus actually uses.
        self.assertEqual(["s03a", "s03b"], stage_ids_in("stages.s03a and s03b"))
        self.assertEqual(["s04a", "s04b"], stage_ids_in("stages.s04a and s04b"))
        # Not a stage path at all.
        self.assertEqual([], stage_ids_in(OWNERSHIP_PATH_PREFIX + "s03"))

    def test_META_05_a_nonexistent_stage_id_is_rejected(self):
        for sid in stage_ids_in("stages.s99.engineering_questions"):
            self.assertNotIn(sid, self.canonical_stages)
        # And a real one is accepted, so the check is not vacuous.
        self.assertIn(stage_ids_in("stages.s02.engineering_questions")[0],
                      self.canonical_stages)

    def test_META_06_a_valid_non_binding_pointer_resolves(self):
        spec = {"file": "ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml",
                "path": "stages.s02.engineering_questions"}
        self.assertTrue(_resolve(spec, self.docs))
        self.assertTrue(all(s in self.canonical_stages
                            for s in stage_ids_in(spec["path"])))

    def test_META_07_a_dangling_non_binding_pointer_is_rejected(self):
        with self.assertRaises(KeyError):
            _resolve({"file": "ver3/contracts/STAGE_RESPONSIBILITY_CONTRACT.yaml",
                      "path": "stages.s02.no_such_field"}, self.docs)
        self.assertEqual(["s99"], stage_ids_in("stages.s99"))
        self.assertNotIn("s99", self.canonical_stages)

    def test_META_08_operational_prose_is_never_compared_for_equality(self):
        """A pointer is a courtesy, not an authority claim. No OPERATIONAL
        section is in the projection set, so nothing compares its prose."""
        projected_sections = {(n, s) for n, _d, s, _sp in self.projections()}
        checked_pointers = 0
        for name, doc in self.stages.items():
            for section, spec in (doc.get("authority_status") or {}).items():
                if not spec.get("see_canonical"):
                    continue
                checked_pointers += 1
                self.assertEqual("OPERATIONAL", spec["class"])
                self.assertNotIn((name, section), projected_sections)
                self.assertIs(False, spec["see_canonical"].get("binding"))
                self.assertIs(False, spec.get("authoritative_for_canonical_semantics"))
        self.assertTrue(checked_pointers, "no pointers exercised")
