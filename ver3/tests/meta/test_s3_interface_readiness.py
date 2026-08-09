"""READINESS-A/B: can S-3 derive both Consumer Sufficiency sources from contracts?

Not S-3. No view is built. This proves only that the two required INPUTS exist in
machine-consumable form, so U-3 can derive them generically rather than inventing
a stage-pair whitelist.

SOURCE A - representational dependencies, from the entity semantic contract.
SOURCE B - reasoning premise classes, from the stage responsibility contract.

They stay independent (CON-12). A reference relationship is not automatically an
engineering premise, and a premise is not automatically referenced by an output.
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

S01_S04 = ("s01", "s02", "s03a", "s03b", "s04a", "gate", "s04b")

#: Tokens that would mean the derivation had learned from a case rather than a
#: contract. None may appear in any structured field the derivation reads.
BENCHMARK_TOKENS = re.compile(r"(BM-\d|PRB-\d|oracle|CND-\d)", re.I)


def _code_only(*funcs):
    """Source with docstrings removed.

    The prose in a docstring explains why the derivation is benchmark-independent
    and may legitimately use those words. What must be clean is the CODE - what
    the derivation actually reads.
    """
    import ast
    import inspect
    out = []
    for fn in funcs:
        tree = ast.parse(inspect.getsource(fn).lstrip())
        node = tree.body[0]
        body = node.body[1:] if (isinstance(node.body[0], ast.Expr)
                                 and isinstance(getattr(node.body[0], "value", None), ast.Constant)
                                 and isinstance(node.body[0].value.value, str)) else node.body
        out.extend(ast.dump(b) for b in body)
    return "\n".join(out)


# ---------------------------------------------------------------- SOURCE A
def derive_representational_dependencies(fams, family, field):
    """The one canonical Source-A rule.

    A field's representational dependencies are what must exist for its value to
    MEAN something, read only from structured metadata:

      reference  -> the target family
      spatial    -> the frame that gives the numbers meaning
      explicit   -> a declared semantic_dependency, for meaning that reference
                    and frame cannot express
      otherwise  -> the empty set, which is a legitimate answer and is
                    distinguishable from an absent declaration

    Free-form `rules:` prose is never read. It carries historical and audit
    rationale, including case identifiers, and machine derivation must not depend
    on it or the result would not be benchmark-independent.
    """
    spec = ((fams.get(family) or {}).get("field_semantics") or {}).get(field)
    if spec is None:
        return set(), "UNDECLARED"
    kind = spec.get("kind")
    deps = set()
    if kind == "reference":
        deps.add(spec["target"])
    elif kind == "spatial":
        frame = spec.get("frame")
        if frame and frame != "SELF_DECLARING":
            deps.add(frame.split(".")[0])
    if "semantic_dependency" in spec:
        deps.add(str(spec["semantic_dependency"]).split(".")[0])
    return deps, kind


def closure(fams, family, field, seen=None):
    """Bounded transitive closure.

    Follows a dependency to the family it names, then only that family's OWN
    declared spatial frames - never every field of it. Pulling a whole family
    because one unrelated field has a dependency would make the set meaningless.
    """
    seen = seen or set()
    direct, _kind = derive_representational_dependencies(fams, family, field)
    out = set(direct)
    for dep in direct:
        if dep in seen or dep not in fams:
            continue
        seen.add(dep)
        for f2, s2 in ((fams[dep] or {}).get("field_semantics") or {}).items():
            if s2.get("kind") == "spatial" and s2.get("frame") not in (None, "SELF_DECLARING"):
                out.add(s2["frame"].split(".")[0])
    return out


class _Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ds = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.fams = dict(cls.ds["entity_families"])
        cls.fams.update(cls.ds["assurance_families"])
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")

    def outputs(self, sid):
        return self.resp["stages"][sid]["permitted_output_semantics"]

    def resolve(self, semantic):
        """`Family` or `Family.field` -> (family, field or None)."""
        if "." in semantic:
            fam, fld = semantic.split(".", 1)
            return fam, fld
        return semantic, None


class TestSourceA(_Base):

    def test_READINESS_A01_every_permitted_output_resolves_to_canonical(self):
        problems = []
        for sid in S01_S04:
            for sem in self.outputs(sid):
                fam, fld = self.resolve(sem)
                if fam not in self.fams:
                    problems.append("%s: %s -> unknown family %s" % (sid, sem, fam))
                elif fld:
                    declared = (list((self.fams[fam] or {}).get("required_fields", []))
                                + list((self.fams[fam] or {}).get("optional_fields", [])))
                    if fld not in declared:
                        problems.append("%s: %s -> %s has no field %s" % (sid, sem, fam, fld))
        self.assertEqual([], problems)

    def test_READINESS_A02_every_reference_dependency_names_a_valid_target(self):
        problems = []
        for fam, v in self.fams.items():
            for fld, spec in ((v or {}).get("field_semantics") or {}).items():
                if spec.get("kind") != "reference":
                    continue
                if spec.get("target") not in self.fams:
                    problems.append("%s.%s -> %s" % (fam, fld, spec.get("target")))
        self.assertEqual([], problems)

    def test_READINESS_A03_every_spatial_dependency_resolves_to_a_frame(self):
        problems = []
        for fam, v in self.fams.items():
            for fld, spec in ((v or {}).get("field_semantics") or {}).items():
                if spec.get("kind") != "spatial":
                    continue
                frame = spec.get("frame")
                if not frame:
                    problems.append("%s.%s declares no frame" % (fam, fld))
                elif frame != "SELF_DECLARING" and frame.split(".")[0] not in self.fams:
                    problems.append("%s.%s frame %r is not a canonical family" % (fam, fld, frame))
        self.assertEqual([], problems)

    def test_READINESS_A04_explicit_dependencies_name_valid_targets(self):
        problems = []
        for fam, v in self.fams.items():
            for fld, spec in ((v or {}).get("field_semantics") or {}).items():
                dep = spec.get("semantic_dependency")
                if dep is None:
                    continue
                if str(dep).split(".")[0] not in self.fams:
                    problems.append("%s.%s explicit dependency %r is not canonical"
                                    % (fam, fld, dep))
        self.assertEqual([], problems)

    def test_READINESS_A05_no_dependency_comes_from_prose(self):
        """The derivation must be benchmark-independent, so it may only read
        structured metadata. Prose `rules:` carry case identifiers; if the
        derivation read them the result would depend on the audit corpus."""
        src = _code_only(derive_representational_dependencies, closure)
        for forbidden in ("rules", "purpose", "note", "why", "rationale"):
            self.assertNotIn("'%s'" % forbidden, src,
                             "derivation reads free-form %r" % forbidden)
        self.assertIsNone(BENCHMARK_TOKENS.search(src),
                          "derivation code mentions a case identifier")
        # And prose really does contain such tokens, so the exclusion matters.
        prose = " ".join(str((v or {}).get("rules", "")) for v in self.fams.values())
        self.assertTrue(BENCHMARK_TOKENS.search(prose),
                        "no case identifiers in prose - the control is vacuous")

    def test_READINESS_A06_every_output_has_a_derivable_dependency_set(self):
        """Including the legitimate empty set, which must be distinguishable from
        an absent declaration."""
        problems = []
        for sid in S01_S04:
            for sem in self.outputs(sid):
                fam, fld = self.resolve(sem)
                if fam not in self.fams:
                    continue
                fields = ([fld] if fld else
                          [f for f in (list((self.fams[fam] or {}).get("required_fields", []))
                                       + list((self.fams[fam] or {}).get("optional_fields", [])))
                           if f != "entity_id"])
                for f in fields:
                    deps, kind = derive_representational_dependencies(self.fams, fam, f)
                    if kind == "UNDECLARED" and deps:
                        problems.append("%s.%s: deps without a declaration" % (fam, f))
        self.assertEqual([], problems)

    def test_READINESS_A07_a_synthetic_declaration_changes_the_set(self):
        """Generalisation control: no derivation code changes."""
        import copy
        fams = copy.deepcopy(self.fams)
        fams["Scenario"].setdefault("field_semantics", {})["environment"] = {
            "kind": "reference", "target": "Actor", "cardinality": "one"}
        before, _ = derive_representational_dependencies(self.fams, "Scenario", "environment")
        after, _ = derive_representational_dependencies(fams, "Scenario", "environment")
        self.assertEqual(set(), before)
        self.assertEqual({"Actor"}, after)

    def test_READINESS_A08_removing_a_declaration_is_detectable(self):
        import copy
        fams = copy.deepcopy(self.fams)
        del fams["Joint"]["field_semantics"]["parent_group"]
        deps, kind = derive_representational_dependencies(fams, "Joint", "parent_group")
        self.assertEqual("UNDECLARED", kind)
        self.assertEqual(set(), deps)
        live, live_kind = derive_representational_dependencies(self.fams, "Joint", "parent_group")
        self.assertEqual({"RigidGroup"}, live)
        self.assertEqual("reference", live_kind)

    def test_closure_is_bounded_and_traceable(self):
        deps = closure(self.fams, "Joint", "frame_origin")
        self.assertIn("ReferenceScale", deps)
        self.assertLess(len(deps), len(self.fams),
                        "closure pulled most of the corpus - it is not bounded")


class TestSourceB(_Base):

    def premise_classes(self):
        for sid in S01_S04:
            for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]:
                yield sid, pc

    def test_READINESS_B01_every_premise_cites_a_declared_question(self):
        problems = []
        for sid, pc in self.premise_classes():
            qs = self.resp["stages"][sid]["engineering_questions"]
            if pc.get("justified_by_question") not in qs:
                problems.append("%s: %s cites an undeclared question" % (sid, pc["class"]))
        self.assertEqual([], problems)

    def test_READINESS_B02_every_premise_has_a_machine_resolvable_binding(self):
        problems = []
        for sid, pc in self.premise_classes():
            sb = pc.get("satisfied_by")
            if not sb:
                problems.append("%s: %s has no binding" % (sid, pc["class"]))
            elif sb.get("kind") != "canonical_families" or not sb.get("families"):
                problems.append("%s: %s binding is not resolvable" % (sid, pc["class"]))
        self.assertEqual([], problems)

    def test_READINESS_B03_no_binding_points_to_an_undefined_family(self):
        problems = []
        for sid, pc in self.premise_classes():
            for fam in (pc.get("satisfied_by") or {}).get("families", []):
                if fam not in self.fams:
                    problems.append("%s: %s binds to undefined %s" % (sid, pc["class"], fam))
        self.assertEqual([], problems)

    def test_READINESS_B04_a_binding_names_families_never_a_stage(self):
        """A premise binding is not an ownership projection and must not let a
        consuming stage acquire a family."""
        stage_ids = set(self.resp["stages"]) | {"s01", "s02", "s03", "s04", "s05", "s06", "s07"}
        for sid, pc in self.premise_classes():
            for fam in (pc.get("satisfied_by") or {}).get("families", []):
                self.assertNotIn(fam, stage_ids)

    def test_READINESS_B05_s04b_premises_match_the_frozen_proposal(self):
        """The plan claims mobility is a declared s04b premise; the frozen
        proposal §7.8 does not list it. The contract projects the proposal, and
        this test pins that agreement so the contradiction cannot be resolved
        silently in the contract's direction."""
        declared = {pc["class"] for pc in
                    self.resp["stages"]["s04b"]["required_reasoning_premise_classes"]}
        self.assertEqual(
            {"prior_spatial_commitment", "topology_with_axes", "required_distinctness",
             "configuration_basis", "constraint_relation", "travel_bounding_quantity",
             "selection_decision"}, declared)
        self.assertNotIn("MobilityExpectation",
                         {f for pc in self.resp["stages"]["s04b"]
                          ["required_reasoning_premise_classes"]
                          for f in (pc.get("satisfied_by") or {}).get("families", [])})

    def test_READINESS_B06_a_synthetic_premise_changes_the_set(self):
        """Generalisation control: adding a premise in the contract changes the
        derived requirement with no derivation-code change."""
        import copy
        resp = copy.deepcopy(self.resp)
        before = len(resp["stages"]["s04a"]["required_reasoning_premise_classes"])
        resp["stages"]["s04a"]["required_reasoning_premise_classes"].append({
            "class": "synthetic", "what": "x",
            "justified_by_question": resp["stages"]["s04a"]["engineering_questions"][0],
            "why": "control",
            "satisfied_by": {"kind": "canonical_families", "families": ["Body"]}})
        after = resp["stages"]["s04a"]["required_reasoning_premise_classes"]
        self.assertEqual(before + 1, len(after))
        self.assertEqual(["Body"], after[-1]["satisfied_by"]["families"])

    def test_no_stage_pair_whitelist_exists_in_derivation_code(self):
        """The mandatory negative control: stage-specific knowledge lives in the
        contract, never in Python."""
        src = _code_only(derive_representational_dependencies, closure)
        for sid in S01_S04:
            self.assertNotIn("'%s'" % sid, src, "derivation branches on stage %s" % sid)
        self.assertIsNone(BENCHMARK_TOKENS.search(src))


class TestSourcesStayIndependent(_Base):

    def test_CON_12_still_holds_and_is_strengthened(self):
        """Two constructs, two files, neither derived from the other."""
        self.assertIn("semantic_dependency", self.ds["field_semantics_rules"])
        self.assertNotIn("required_reasoning_premise_classes", self.ds)
        self.assertNotIn("field_semantics", self.resp)
        # A reference is not automatically a premise: at least one referenced
        # family is not bound as a premise anywhere, and vice versa.
        referenced = {s["target"] for v in self.fams.values()
                      for s in ((v or {}).get("field_semantics") or {}).values()
                      if s.get("kind") == "reference"}
        premised = {f for sid in S01_S04
                    for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]
                    for f in (pc.get("satisfied_by") or {}).get("families", [])}
        self.assertTrue(referenced - premised, "every referenced family is a premise")
        self.assertTrue(premised - referenced, "every premise family is referenced")
