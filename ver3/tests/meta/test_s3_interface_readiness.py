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

S01_S04 = ("s01", "s02", "s03a", "s03b", "s04a", "feasibility", "selection", "s04b")

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


# ---------------------------------------------------------------- SOURCE B
def families_with_role(fams, role):
    """Every family whose OWN declaration says it carries this semantic role."""
    return sorted(f for f, v in fams.items()
                  if role in ((v or {}).get("semantic_roles") or []))


def resolve_premise_semantics(premise, fams):
    """Which families satisfy a premise, and why.

    Generic and stage-agnostic: it reads the roles the premise REQUIRES and the
    roles each family DECLARES, and matches. It knows no family name, no stage id
    and no case identifier.

    Returns (families, trace); the trace explains each inclusion so S-3 can later
    record why an entity was selected.
    """
    trace = []
    out = set()
    for role in premise.get("requires_semantics", []):
        for fam in families_with_role(fams, role):
            out.add(fam)
            trace.append({"premise": premise.get("class"), "requires_semantics": role,
                          "family": fam, "because": "family declares this role"})
    return sorted(out), trace


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
        # A target may name several legitimate families; each is a dependency.
        # ANY names none, so it creates no dependency at all.
        target = spec["target"]
        if target != "ANY":
            deps.update(target if isinstance(target, list) else [target])
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
                target = spec.get("target")
                if target == "ANY":
                    continue          # explicitly unconstrained; names no family
                for one in (target if isinstance(target, list) else [target]):
                    if one not in self.fams:
                        problems.append("%s.%s -> %s" % (fam, fld, one))
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
    """SOURCEB-01..14. A premise states semantic requirements; canonical entity
    semantics decide which families satisfy them."""

    def premise_classes(self):
        for sid in S01_S04:
            for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]:
                yield sid, pc

    def test_SOURCEB_01_no_premise_enumerates_families(self):
        """The defect introduced at 6ef6dac, and plan R-2's own falsifier:
        'premise declarations start naming families directly'."""
        problems = []
        for sid, pc in self.premise_classes():
            for banned in ("satisfied_by", "families", "canonical_families"):
                if banned in pc:
                    problems.append("%s: %s declares %s" % (sid, pc["class"], banned))
            for role in pc.get("requires_semantics", []):
                if role in self.fams:
                    problems.append("%s: %s requires %r, a family name"
                                    % (sid, pc["class"], role))
        self.assertEqual([], problems)

    def test_SOURCEB_02_every_premise_has_a_semantic_selector(self):
        for sid, pc in self.premise_classes():
            with self.subTest(where="%s.%s" % (sid, pc["class"])):
                self.assertTrue(pc.get("requires_semantics"))

    def test_SOURCEB_03_every_selector_resolves(self):
        problems = []
        for sid, pc in self.premise_classes():
            fams, _t = resolve_premise_semantics(pc, self.fams)
            if not fams:
                problems.append("%s: %s resolves to nothing" % (sid, pc["class"]))
        self.assertEqual([], problems)

    def test_SOURCEB_04_every_role_has_declared_engineering_meaning(self):
        vocab = self.ds["semantic_role_vocabulary"]
        used = {r for _s, pc in self.premise_classes() for r in pc["requires_semantics"]}
        declared = {r for v in self.fams.values() for r in ((v or {}).get("semantic_roles") or [])}
        for role in used | declared:
            with self.subTest(role=role):
                self.assertIn(role, vocab)
                self.assertTrue(str(vocab[role]).strip())
        for role in vocab:
            if role != "extension_rule":
                self.assertIn(role, declared, "%r declared but no family carries it" % role)

    def test_SOURCEB_04b_no_role_is_a_disguised_whitelist(self):
        """A role must mean something outside the consumer using it."""
        for role, meaning in self.ds["semantic_role_vocabulary"].items():
            if role == "extension_rule":
                continue
            with self.subTest(role=role):
                for sid in S01_S04:
                    self.assertNotIn(sid, str(meaning).lower(),
                                     "%r is defined by naming a stage" % role)

    def test_SOURCEB_05_a_synthetic_family_participates_automatically(self):
        """The main evidence: a new family declaring an existing role is picked
        up with no resolver change and no stage-contract change."""
        import copy
        fams = copy.deepcopy(self.fams)
        premise = [pc for _s, pc in self.premise_classes()
                   if "topology_relation" in pc["requires_semantics"]][0]
        before, _ = resolve_premise_semantics(premise, self.fams)
        fams["SyntheticCoupling"] = {"owned_by": "s03", "required_fields": ["entity_id"],
                                     "semantic_roles": ["topology_relation"]}
        after, trace = resolve_premise_semantics(premise, fams)
        self.assertNotIn("SyntheticCoupling", before)
        self.assertIn("SyntheticCoupling", after)
        self.assertTrue([t for t in trace if t["family"] == "SyntheticCoupling"])

    def test_SOURCEB_06_removing_the_role_removes_participation(self):
        import copy
        fams = copy.deepcopy(self.fams)
        premise = [pc for _s, pc in self.premise_classes()
                   if "topology_relation" in pc["requires_semantics"]][0]
        self.assertIn("Joint", resolve_premise_semantics(premise, fams)[0])
        fams["Joint"]["semantic_roles"] = [r for r in fams["Joint"]["semantic_roles"]
                                           if r != "topology_relation"]
        self.assertNotIn("Joint", resolve_premise_semantics(premise, fams)[0])
        fams["Joint"]["semantic_roles"].append("topology_relation")
        self.assertIn("Joint", resolve_premise_semantics(premise, fams)[0])

    def test_SOURCEB_07_no_stage_contract_changes_for_a_new_family(self):
        import copy
        before = copy.deepcopy(self.resp)
        fams = copy.deepcopy(self.fams)
        fams["SyntheticCoupling"] = {"owned_by": "s03", "required_fields": ["entity_id"],
                                     "semantic_roles": ["topology_relation"]}
        for sid in S01_S04:
            for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]:
                resolve_premise_semantics(pc, fams)
        self.assertEqual(before, self.resp)

    def test_SOURCEB_08_09_resolver_has_no_family_or_stage_branch(self):
        src = _code_only(resolve_premise_semantics, families_with_role)
        for fam in self.fams:
            self.assertNotIn("'%s'" % fam, src, "resolver branches on family %s" % fam)
        for sid in S01_S04:
            self.assertNotIn("'%s'" % sid, src, "resolver branches on stage %s" % sid)
        for role in self.ds["semantic_role_vocabulary"]:
            self.assertNotIn("'%s'" % role, src, "resolver branches on role %s" % role)

    def test_SOURCEB_10_single_role_premises_use_the_same_mechanism(self):
        """No separate 1:1 binding rule exists, so none can widen into a
        whitelist. A premise needing one role is just a premise."""
        single = [(s, pc) for s, pc in self.premise_classes()
                  if len(pc["requires_semantics"]) == 1]
        self.assertTrue(single)
        for sid, pc in single:
            with self.subTest(where="%s.%s" % (sid, pc["class"])):
                self.assertNotIn("satisfied_by", pc)
                self.assertTrue(resolve_premise_semantics(pc, self.fams)[0])

    # The name carried "28" and the assertion had said 32 since S7-A: a test name
    # that states a count goes stale every time the count changes, and a stale
    # name on a passing test is the quietest kind of wrong. The count belongs in
    # the assertion, where changing it is a visible edit.
    def test_SOURCEB_11_every_premise_class_resolves(self):
        total = 0
        for sid, pc in self.premise_classes():
            fams, trace = resolve_premise_semantics(pc, self.fams)
            self.assertTrue(fams, "%s.%s" % (sid, pc["class"]))
            self.assertTrue(trace)
            total += 1
        # 32 live after the S7-A correction: `gate` (3) became `feasibility` (4)
        # and `selection` (4). s04b's `selection_decision` was RETIRED, not
        # staged - activating it would have meant SelectionDecision -> s04b while
        # the architecture requires s04b -> feasibility -> selection -> decision.
        # It moved to
        # `premise_classes_pending_step`: it resolves against COMMITTED_BRANCH,
        # which cannot exist until the S-7 gate, so requiring it made s04b
        # unreachable - the ConsumerView was UPSTREAM_INSUFFICIENCY on every
        # call. The class is preserved with the step that activates it, and the
        # pending corpus is pinned too so it cannot be quietly dropped.
        #
        # 33 at S7-B: `feasibility` gained `declared_physical_demand`. Two of its
        # nine domains are about what the design DEMANDS - an effect that must
        # occur, a load the world applies - and no class carried them, so the
        # undischarged obligations the domain exists to find were exactly what
        # its view could not contain.
        #
        # 35 at S7-C: `selection` gained the design-wide hard requirements and
        # the topology its counting metrics count.
        #
        # 36 at the S03a seam closure: s03a gained `open_question_to_cite`. Its
        # prompt demanded that UnresolvedDecision.kept_open_by cite the Ambiguity
        # or Freedom entities keeping a decision open, while the view carried
        # neither family - so the stage was asked to reference entities it could
        # not see.
        self.assertEqual(36, total)
        pending = [pc for s in self.resp["stages"].values()
                   for pc in (s.get("premise_classes_pending_step") or [])]
        self.assertEqual([], pending, "a pending class survived S7-A")
        retired = [pc for s in self.resp["stages"].values()
                   for pc in (s.get("retired_premise_classes") or [])]
        self.assertEqual(1, len(retired))
        self.assertEqual("S7-A", retired[0]["retired_by"])

    def test_SOURCEB_13_no_benchmark_identifier_participates(self):
        src = _code_only(resolve_premise_semantics, families_with_role)
        self.assertIsNone(BENCHMARK_TOKENS.search(src))
        for _s, pc in self.premise_classes():
            self.assertIsNone(BENCHMARK_TOKENS.search(str(pc.get("requires_semantics"))))
        for role, meaning in self.ds["semantic_role_vocabulary"].items():
            self.assertIsNone(BENCHMARK_TOKENS.search(str(meaning)), role)

    def test_SOURCEB_14_the_trace_is_reproducible(self):
        premise = [pc for _s, pc in self.premise_classes()
                   if pc["class"] == "topology_and_interaction"][0]
        _f, trace = resolve_premise_semantics(premise, self.fams)
        joint = [t for t in trace if t["family"] == "Joint"][0]
        self.assertEqual("topology_and_interaction", joint["premise"])
        self.assertEqual("topology_relation", joint["requires_semantics"])
        self.assertIn("topology_relation", self.fams["Joint"]["semantic_roles"])

    def test_READINESS_B01_every_premise_cites_a_declared_question(self):
        problems = []
        for sid, pc in self.premise_classes():
            if pc.get("justified_by_question") not in \
                    self.resp["stages"][sid]["engineering_questions"]:
                problems.append("%s: %s" % (sid, pc["class"]))
        self.assertEqual([], problems)

    def test_READINESS_B05_s04b_premises_match_the_frozen_proposal(self):
        """The plan claims mobility is a declared s04b premise; the frozen
        proposal §7.8 does not list it. Pinned so it cannot be resolved silently
        in the contract's direction. It concerns U-6 -> U-7 sequencing rationale,
        not S-3, which consumes this contract."""
        declared = {pc["class"] for pc in
                    self.resp["stages"]["s04b"]["required_reasoning_premise_classes"]}
        pending = {pc["class"] for pc in
                   self.resp["stages"]["s04b"].get("retired_premise_classes") or []}
        self.assertEqual(
            {"prior_spatial_commitment", "topology_with_axes", "required_distinctness",
             "configuration_basis", "constraint_relation", "travel_bounding_quantity"},
            declared)
        # The seventh is not resolved in the contract's direction and not lost:
        # S7-A RETIRED it, because activating it would have made the order
        # circular - SelectionDecision -> s04b, against s04b -> feasibility ->
        # selection -> SelectionDecision.
        self.assertEqual({"selection_decision"}, pending)
        roles = {r for pc in self.resp["stages"]["s04b"]
                 ["required_reasoning_premise_classes"] for r in pc["requires_semantics"]}
        self.assertNotIn("mobility_disposition", roles)


class TestSourcesStayIndependent(_Base):

    def test_CON_12_still_holds_and_is_strengthened(self):
        """Two constructs, two files, neither derived from the other."""
        self.assertIn("semantic_dependency", self.ds["field_semantics_rules"])
        self.assertNotIn("required_reasoning_premise_classes", self.ds)
        self.assertNotIn("field_semantics", self.resp)
        # A reference is not automatically a premise: at least one referenced
        # family is not bound as a premise anywhere, and vice versa.
        referenced = set()
        for v in self.fams.values():
            for spec in ((v or {}).get("field_semantics") or {}).values():
                if spec.get("kind") != "reference":
                    continue
                target = spec["target"]
                referenced.update(target if isinstance(target, list) else [target])
        premised = set()
        for sid in S01_S04:
            for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]:
                premised |= set(resolve_premise_semantics(pc, self.fams)[0])
        self.assertTrue(referenced - premised, "every referenced family is a premise")
        self.assertTrue(premised - referenced, "every premise family is referenced")
