"""VIEW-*: Consumer Sufficiency (U-3 / M-3).

Deterministic contract interpretation. No model, no benchmark, no stage branch.
"""
from __future__ import annotations

import os
import re
import sys
import unittest

from . import _fixtures, _paths

REPO = _paths.REPO_ROOT
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.assy_v3.view import (Source, Sufficiency, ViewStatus,          # noqa: E402
                               build_consumer_view, derive_required_minimum,
                               derive_source_a, derive_source_b, render)
import ver3.assy_v3.view.consumer_view as cv                            # noqa: E402

STAGES = ("s01", "s02", "s03a", "s03b", "s04a", "feasibility", "selection", "s04b")

from .test_s3_interface_readiness import _code_only          # noqa: E402


class _Base(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")

    def state(self, run="t"):
        return DesignState(run)




class TestRequiredMinimum(_Base):

    def test_VIEW_01_source_a_derives(self):
        for sid in STAGES:
            a = derive_source_a(sid, self.c, self.resp)
            for r in a:
                self.assertIs(Source.REPRESENTATIONAL_DEPENDENCY, r.source)
                self.assertIn("declaration", r.trace)
                self.assertIn("DESIGN_STATE_CONTRACT", r.trace["source_contract"])

    def test_VIEW_02_source_b_derives(self):
        for sid in STAGES:
            for r in derive_source_b(sid, self.c, self.resp):
                self.assertIs(Source.REASONING_PREMISE, r.source)
                self.assertTrue(r.trace["requires_semantics"])
                self.assertTrue(r.trace["engineering_question"])
                self.assertIn("STAGE_RESPONSIBILITY_CONTRACT", r.trace["source_contract"])

    def test_VIEW_03_sources_are_independently_traceable(self):
        rm = derive_required_minimum("s04b", self.c, self.resp)
        a = rm.of(Source.REPRESENTATIONAL_DEPENDENCY)
        b = rm.of(Source.REASONING_PREMISE)
        self.assertTrue(a and b)
        for r in a:
            self.assertNotIn("requires_semantics", r.trace)
        for r in b:
            self.assertNotIn("declaration", r.trace)

    def test_VIEW_04_consumer_cannot_narrow_the_minimum(self):
        """There is no parameter through which a stage could subtract."""
        import inspect
        sig = inspect.signature(derive_required_minimum)
        self.assertEqual(["stage_id", "contracts", "responsibility"], list(sig.parameters))
        sig2 = inspect.signature(build_consumer_view)
        for banned in ("exclude", "only", "families", "narrow", "override", "skip"):
            self.assertNotIn(banned, sig2.parameters)


class TestSelection(_Base):

    def test_VIEW_05_06_eligibility_is_not_a_dump(self):
        """A qualifying instance in another branch is excluded."""
        s = self.state()
        self.add(s, "s02", "Candidate", "CND-A", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        self.add(s, "s02", "Candidate", "CND-B", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        self.add(s, "s03", "LoadPath", "LP-A", candidate="CND-A")
        self.add(s, "s03", "LoadPath", "LP-B", candidate="CND-B")
        self.add(s, "selection", "SelectionDecision", "SEL-1", selected_candidate="CND-A")
        self.assertEqual("CND-A", cv.committed_branch(s, self.c))
        v = build_consumer_view("s04b", s, self.c, self.resp)
        ids = {e["entity_id"] for e in v.entities}
        if "LP-A" in ids or "LP-B" in ids:
            self.assertIn("LP-A", ids)
            self.assertNotIn("LP-B", ids, "another candidate's instance leaked in")

    def test_VIEW_08_branches_do_not_contaminate(self):
        s = self.state()
        self.add(s, "s02", "Candidate", "CND-A", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        self.add(s, "s02", "Candidate", "CND-B", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        self.add(s, "selection", "SelectionDecision", "SEL-1", selected_candidate="CND-B")
        v = build_consumer_view("s04b", s, self.c, self.resp)
        self.assertEqual("CND-B", v.branch)
        for t in v.traces:
            self.assertNotEqual(["CND-A"], t.get("branch_scope"))

    def test_VIEW_07_reference_closure_supplies_referents(self):
        s = self.state()
        self.add(s, "s03", "Body", "BOD-1")
        self.add(s, "s03", "RigidGroup", "RGP-1", body="BOD-1")
        self.add(s, "s03", "Joint", "JNT-1", parent_group="RGP-1", child_group="RGP-1")
        v = build_consumer_view("s04b", s, self.c, self.resp)
        ids = {e["entity_id"] for e in v.entities}
        if "JNT-1" in ids:
            self.assertIn("RGP-1", ids, "a selected Joint left its groups behind")

    def test_VIEW_09_non_standing_state_is_not_presented_as_current(self):
        s = self.state()
        self.add(s, "s04", "ReferenceScale", "SCL-1", basis="RELATIVE")
        s.apply(StagePatch(patch_id="inv", run_id=s.run_id, stage_id="s04",
                           stage_attempt=2, parent_state_hash=s.state_hash(),
                           operations=[Op("INVALIDATE", "ReferenceScale", "SCL-1", {},
                                          "p", reason="withdrawn")],
                           execution_status="SUCCESS", provenance={"provider": "t"}))
        v = build_consumer_view("s04b", s, self.c, self.resp)
        self.assertNotIn("SCL-1", {e["entity_id"] for e in v.entities})


class TestSufficiency(_Base):

    def test_VIEW_10_absent_upstream_is_upstream_insufficiency(self):
        v = build_consumer_view("s04b", self.state(), self.c, self.resp)
        self.assertEqual(ViewStatus.UPSTREAM_INSUFFICIENCY, v.status)
        self.assertTrue([a for a in v.assessment
                         if a["verdict"] == Sufficiency.MISSING_UPSTREAM.value])

    def test_VIEW_11_existing_but_unselected_is_projection_failure(self):
        """The two are different findings with different owners."""
        s = self.state()
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        rm = derive_required_minimum("s04a", self.c, self.resp)
        req = [r for r in rm.requirements
               if r.by_role and "quantity_constraint" in r.by_role][0]
        rel = cv.relevant_ids(s, self.c, cv.committed_branch(s, self.c))
        self.assertIn("REQ-1", rel, "REQ-1 must be relevant for this to be OUR failure")
        # Fault injection: a RELEVANT qualifying instance exists and is omitted.
        a = cv._assess(s, self.c, req, [])
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value, a["verdict"])
        b = cv._assess(s, self.c, req, [{"entity_id": "REQ-1"}])
        self.assertEqual(Sufficiency.SATISFIED.value, b["verdict"])

    def test_VIEW_25_every_included_item_has_a_trace(self):
        s = self.state()
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        v = build_consumer_view("s04a", s, self.c, self.resp)
        for rec in v.entities:
            self.assertTrue(v.why(rec["entity_id"]),
                            "%s has no inclusion trace" % rec["entity_id"])

    def test_VIEW_24_derivation_is_deterministic(self):
        s = self.state()
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        a = build_consumer_view("s04a", s, self.c, self.resp).as_dict()
        b = build_consumer_view("s04a", s, self.c, self.resp).as_dict()
        self.assertEqual(a, b)


class TestHistoricalReplays(_Base):
    """Exact historical defects, resolved by the general mechanism - not by a
    rule naming the entity that used to be lost."""

    def _seeded(self):
        """Connected lineage, as accumulated state actually has.

        Relevance now requires POSITIVE evidence, so a substrate of two orphans
        would prove nothing. This carries the chain the historical runs had: a
        candidate, an obligation citing the requirement, and a placed joint whose
        frame cites the scale.

        The s03 topology and the s04a scale record the candidate they exist
        because of, which is what the migrated producer now writes. They are
        structurally scoped for the same reason they were always relevant: they
        were built AFTER the commitment, to embody it. Withdraw CND-0001 and none
        of them keeps unqualified standing - which is exactly FA-5, and exactly
        why the old fixture's silence about lineage was a defect in the fixture,
        not a reason to loosen the scope rule.
        """
        s = self.state("replay")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-0001", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-0001"])
        self.add(s, "s02", "Candidate", "CND-0001", principle={"h": "f"},
                 addresses_obligations=["OBL-0001"], obligations_created=[])
        self.add(s, "s04", "ReferenceScale", "SCL-0001", prem=["CND-0001"],
                 basis="RELATIVE")
        self.add(s, "s02", "LoadCase", "LC-0001")
        self.add(s, "s03", "Body", "BOD-0001", prem=["CND-0001"])
        self.add(s, "s03", "RigidGroup", "RGP-0001", prem=["CND-0001"],
                 body="BOD-0001")
        self.add(s, "s03", "LoadPath", "LP-0001", candidate="CND-0001",
                 load_case="LC-0001")
        return s

    def test_VIEW_13_requirement_quantity_is_not_lost_at_the_boundary(self):
        v = build_consumer_view("s04a", self._seeded(), self.c, self.resp)
        self.assertIn("REQ-0001", {e["entity_id"] for e in v.entities})
        reasons = v.why("REQ-0001")
        self.assertTrue(reasons)
        self.assertTrue(any(r.get("why_relevant") for r in reasons),
                        "included with no relevance reason")

    def test_VIEW_12_committed_spatial_state_reaches_s04b(self):
        s = self._seeded()
        # The joint is topology: it records the candidate it embodies, exactly as
        # the migrated s03 producer now writes it.
        s.apply(StagePatch(
            patch_id="topo", run_id=s.run_id, stage_id="s03", stage_attempt=1,
            parent_state_hash=s.state_hash(),
            operations=[Op("CREATE", "Joint", "JNT-0001",
                           self._fields_for(s, self.c, "s03", "Joint",
                                            {"parent_group": "RGP-0001",
                                             "child_group": "RGP-0001",
                                             "frame_origin": "SCL-0001"}), "p",
                           premise_refs=["CND-0001"])],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        v = build_consumer_view("s04b", s, self.c, self.resp)
        self.assertIn("SCL-0001", {e["entity_id"] for e in v.entities})
        self.assertTrue(any(r.get("why_relevant") for r in v.why("SCL-0001")))

    def test_the_replays_pass_without_naming_the_entity(self):
        src = open(cv.__file__).read()
        for token in ("ReferenceScale", "Requirement", "Envelope", "Joint"):
            self.assertNotIn('"%s"' % token, src,
                             "view code names family %s" % token)


class TestArchitecturalRegressions(_Base):

    PROD = ["ver3/assy_v3/view/consumer_view.py"]

    def _src(self):
        return "\n".join(open(os.path.join(REPO, p)).read() for p in self.PROD)

    def test_VIEW_15_no_stage_specific_branch(self):
        """No BRANCH on a stage id - which is the property, and is not the same
        as the word never appearing anywhere in the file.

        S-7 / U-8 named a responsibility `selection`, and `selection` is also
        what this module calls the instance-selection rule on a Requirement. A
        substring scan then failed on `__slots__`, which is a false alarm about a
        real rule. So the check reads the SYNTAX: a stage id used in a
        comparison, as a subscript, or as a `.get()` key is a branch; a string in
        a slots tuple is not.
        """
        import ast
        tree = ast.parse(self._src())
        keys = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for operand in [node.left] + list(node.comparators):
                    for sub in ast.walk(operand):
                        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                            keys.add(sub.value)
            elif isinstance(node, ast.Subscript):
                for sub in ast.walk(node.slice):
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                        keys.add(sub.value)
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get" and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                keys.add(node.args[0].value)
        for sid in STAGES:
            self.assertNotIn(sid, keys, "view code branches on stage %s" % sid)

    def test_VIEW_16_no_benchmark_logic(self):
        self.assertIsNone(re.search(r"(BM-\d|PRB-\d|CND-000|oracle)", self._src(), re.I))

    def test_VIEW_14_no_family_whitelist_anywhere_in_production(self):
        for dirpath, _d, names in os.walk(os.path.join(REPO, "ver3")):
            if "tests" in dirpath or "__pycache__" in dirpath:
                continue
            for n in names:
                if not n.endswith(".py"):
                    continue
                text = open(os.path.join(dirpath, n)).read()
                self.assertNotIn("S03_OWNED = (", text,
                                 "%s reintroduces a stage-family whitelist" % n)

    def test_VIEW_18_no_positional_truncation_remains(self):
        for dirpath, _d, names in os.walk(os.path.join(REPO, "ver3", "assy_v3")):
            for n in names:
                if not n.endswith(".py"):
                    continue
                text = open(os.path.join(dirpath, n)).read()
                self.assertNotIn("[:26000]", text, "%s still slices positionally" % n)

    def test_VIEW_19_20_budget_reduces_semantically_then_reports(self):
        s = self.state()
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        full = build_consumer_view("s04a", s, self.c, self.resp)
        tiny = build_consumer_view("s04a", s, self.c, self.resp, budget_chars=10)
        self.assertEqual(ViewStatus.BUDGET_INSUFFICIENT, tiny.status)
        self.assertTrue(tiny.omitted)
        self.assertEqual("required minimum exceeds budget", tiny.omitted[-1]["rule"])
        # A generous budget changes nothing.
        ok = build_consumer_view("s04a", s, self.c, self.resp, budget_chars=10 ** 7)
        self.assertEqual(full.counts(), ok.counts())


class TestContractGeneralization(_Base):
    """The main S-3 claim: contract changes move the view; code does not."""

    def test_VIEW_21_a_new_premise_role_changes_the_minimum(self):
        import copy
        resp = copy.deepcopy(self.resp)
        before = len(derive_source_b("s04a", self.c, resp))
        resp["stages"]["s04a"]["required_reasoning_premise_classes"].append({
            "class": "synthetic", "justified_by_question":
                resp["stages"]["s04a"]["engineering_questions"][0],
            "why": "control", "requires_semantics": ["configuration_state"],
            "instance_selection": {"population": "INVOCATION_BRANCH",
                                   "coverage": "ALL_APPLICABLE",
                                   "existence": "REQUIRED_NONEMPTY"}})
        after = derive_source_b("s04a", self.c, resp)
        self.assertEqual(before + 1, len(after))
        self.assertIn("Configuration", after[-1].families)

    def test_VIEW_22_a_new_qualifying_family_participates(self):
        class _C:
            def __init__(self, base):
                import copy
                self._f = copy.deepcopy(base.families)
                self._f["SyntheticCoupling"] = {
                    "owned_by": "s03", "required_fields": ["entity_id"],
                    "semantic_roles": ["topology_relation"]}
            @property
            def families(self):
                return self._f
            def field_semantics(self, fam):
                return (self._f.get(fam) or {}).get("field_semantics", {})
        before = {f for r in derive_source_b("s04b", self.c, self.resp) for f in r.families}
        after = {f for r in derive_source_b("s04b", _C(self.c), self.resp) for f in r.families}
        self.assertNotIn("SyntheticCoupling", before)
        self.assertIn("SyntheticCoupling", after)

    def test_VIEW_23_a_disconnected_instance_is_not_pulled_in(self):
        """Qualifying family, no relationship to the committed branch."""
        s = self.state()
        self.add(s, "s02", "Candidate", "CND-A", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        self.add(s, "s02", "Candidate", "CND-B", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        self.add(s, "selection", "SelectionDecision", "SEL", selected_candidate="CND-A")
        self.add(s, "s03", "LoadPath", "LP-OTHER", candidate="CND-B")
        v = build_consumer_view("s04b", s, self.c, self.resp)
        self.assertNotIn("LP-OTHER", {e["entity_id"] for e in v.entities})


class TestCoreCorrections(_Base):
    """VIEW-C: the four core semantics corrected before any consumer migration."""

    def test_VIEW_C01_C02_multi_role_premise_needs_every_role(self):
        """One satisfied role out of three does not satisfy the premise."""
        s = self.state()
        self.add(s, "s03", "Body", "BOD-1")            # topology_element only
        premise = [p for p in
                   self.resp["stages"]["s04a"]["required_reasoning_premise_classes"]
                   if len(p["requires_semantics"]) > 1][0]
        req = [r for r in derive_source_b("s04a", self.c, self.resp)
               if r.key == premise["class"]][0]
        self.assertEqual(len(premise["requires_semantics"]), len(req.atoms()))
        rel = cv.relevant_ids(s, self.c, None)
        sel, _ = cv.select_instances(s, self.c, req, None)
        a = cv._assess(s, self.c, req, sel)
        self.assertNotEqual(Sufficiency.SATISFIED.value, a["verdict"])
        self.assertEqual(len(premise["requires_semantics"]), len(a["coverage"]))

    def test_VIEW_C10_requirement_preserves_atomic_obligations(self):
        """Two premises resolving to the same family keep different WHY traces."""
        b = derive_source_b("s04b", self.c, self.resp)
        multi = [r for r in b if len(r.by_role) > 1]
        self.assertTrue(multi, "no compound premise to check")
        for r in multi:
            self.assertEqual(sorted(r.by_role), [n for n, _f in r.atoms()])
        keys = [r.key for r in b]
        self.assertEqual(len(keys), len(set(keys)), "premises collapsed together")

    def test_VIEW_C08_C09_source_a_is_a_true_union(self):
        """A field declaring both a reference and an explicit dependency keeps both."""
        import copy

        class _C:
            def __init__(self, base, extra):
                self._f = copy.deepcopy(base.families)
                self._f["Joint"]["field_semantics"]["probe"] = extra
            @property
            def families(self):
                return self._f
            def field_semantics(self, fam):
                return (self._f.get(fam) or {}).get("field_semantics", {})

        resp = copy.deepcopy(self.resp)
        resp["stages"]["s04b"]["permitted_output_semantics"] = ["Joint.probe"]
        ref_plus = {"kind": "reference", "target": "RigidGroup", "cardinality": "one",
                    "semantic_dependency": "ReferenceScale"}
        got = {d for r in derive_source_a("s04b", _C(self.c, ref_plus), resp)
               for d in r.families}
        self.assertEqual({"RigidGroup", "ReferenceScale"}, got)

        spatial_plus = {"kind": "spatial", "frame": "ReferenceScale",
                        "semantic_dependency": "Body"}
        got2 = {d for r in derive_source_a("s04b", _C(self.c, spatial_plus), resp)
                for d in r.families}
        self.assertEqual({"ReferenceScale", "Body"}, got2)

    def test_VIEW_C18_relevant_but_omitted_is_projection_failure(self):
        """Fault injection: the entity IS relevant and did not reach the view."""
        s = self.state()
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        req = [r for r in derive_source_b("s04a", self.c, self.resp)
               if r.by_role and "quantity_constraint" in r.by_role][0]
        rel = cv.relevant_ids(s, self.c, cv.committed_branch(s, self.c))
        self.assertIn("REQ-1", rel)
        a = cv._assess(s, self.c, req, [])
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value, a["verdict"])

    def test_VIEW_C19_absent_upstream_is_missing_not_projection_failure(self):
        s = self.state()
        req = [r for r in derive_source_b("s04a", self.c, self.resp)
               if r.by_role and "quantity_constraint" in r.by_role][0]
        a = cv._assess(s, self.c, req, [])
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value, a["verdict"])

    def test_VIEW_C06_other_branch_stays_excluded(self):
        s = self.state()
        for cid in ("CND-A", "CND-B"):
            self.add(s, "s02", "Candidate", cid, principle={"h": "f"},
                     addresses_obligations=[], obligations_created=[])
        self.add(s, "s02", "LoadCase", "LC-1")
        self.add(s, "s03", "LoadPath", "LP-A", candidate="CND-A", load_case="LC-1")
        self.add(s, "s03", "LoadPath", "LP-B", candidate="CND-B", load_case="LC-1")
        self.add(s, "selection", "SelectionDecision", "SEL", selected_candidate="CND-A")
        v = build_consumer_view("s04b", s, self.c, self.resp)
        ids = {e["entity_id"] for e in v.entities}
        self.assertNotIn("LP-B", ids, "another candidate's instance leaked in")

    def test_VIEW_C25_every_inclusion_carries_a_relevance_reason(self):
        s = self.state()
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        v = build_consumer_view("s04a", s, self.c, self.resp)
        for rec in v.entities:
            reasons = v.why(rec["entity_id"])
            self.assertTrue(reasons)
            self.assertTrue(any(r.get("why_relevant") for r in reasons),
                            "%s included with no relevance reason" % rec["entity_id"])

    def test_the_contract_gap_is_now_closed_by_premise_lineage(self):
        """Topology still cannot reach Candidate by REFERENCE - it never could.

        The gap is closed by PREMISE lineage instead: s03 records the candidate it
        embodies, so the depends-on graph carries the edge that the reference
        graph never had. An orphan is now distinguishable from a real topology
        element, and the PROVISIONAL fallback is gone.
        """
        edges = {}
        for fam, v in self.c.families.items():
            for _f, spec in ((v or {}).get("field_semantics") or {}).items():
                if spec.get("kind") == "reference":
                    # A target may name several legitimate families; each is its
                    # own edge in the reference graph.
                    target = spec["target"]
                    edges.setdefault(fam, set()).update(
                        target if isinstance(target, list) else [target])

        def reaches(fam, seen=None):
            seen = seen or set()
            if fam in seen:
                return False
            seen.add(fam)
            return any(t == "Candidate" or reaches(t, seen) for t in edges.get(fam, ()))

        for fam in ("Body", "RigidGroup", "Joint", "Interface", "Configuration"):
            self.assertFalse(reaches(fam), "%s now reaches Candidate - "
                             "the gap may be closeable; revisit the relevance rule" % fam)
        s = self.state()
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=[], obligations_created=[])
        # An orphan: no premise, no reference.
        self.add(s, "s03", "Body", "BOD-ORPHAN")
        # Real topology: records the candidate it was built on.
        s.apply(StagePatch(
            patch_id="topo", run_id=s.run_id, stage_id="s03", stage_attempt=1,
            parent_state_hash=s.state_hash(),
            operations=[Op("CREATE", "Body", "BOD-REAL",
                           self._fields_for(s, self.c, "s03", "Body", {}), "p",
                           premise_refs=["CND-1"])],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        fwd, rev = cv._reference_graph(s, self.c)
        cands = {"CND-1"}
        self.assertEqual(cv.UNSCOPED,
                         cv.scope_of("BOD-ORPHAN", fwd, rev, s, self.c, "CND-1", cands)[0])
        self.assertEqual(cv.ACTIVE_BRANCH,
                         cv.scope_of("BOD-REAL", fwd, rev, s, self.c, "CND-1", cands)[0])
        src = _code_only(cv.scope_of)
        self.assertNotIn("PROVISIONAL", src, "the unsound fallback is still present")


class TestBranchScopeLineage(_Base):
    """SCOPE-*: branch/common/unscoped from POSITIVE structured evidence.

    Two directions on the depends-on graph, meaning different things:
      entity ->* Candidate   built on it        -> branch membership
      Candidate ->* entity   rests on it        -> common upstream
    Neither -> UNSCOPED. "No path" never implies "common".
    """

    def _add(self, s, stage, fam, eid, prem=None, **ov):
        """Fill required fields, and fill DECLARED REFERENCES as references.

        "x" in a reference field is prose where an entity id belongs (R-20), so
        a family whose required fields are all references could not be built at
        all. A many-reference takes the empty list, which the contract states is
        a VALUE; a one-reference gets a minimal referent, built under its own
        declared owner, the way `_fixtures.StateBuilder` does it.
        """
        d = {}
        for f in self.c.required_fields(fam):
            if f == "entity_id" or f in ov:
                continue
            spec = self.c.reference_spec(fam, f)
            if spec is None:
                d[f] = "x"
            elif spec.get("cardinality") == "many":
                d[f] = []
            else:
                target = spec["target"]
                rid = "%s-AUTO" % target[:3].upper()
                if not s.has_entity(rid):
                    owner = self.c.owner_of(target)
                    at = owner if isinstance(owner, str) and owner != "any" else stage
                    self._add(s, at, target, rid)
                d[f] = rid
        d.update(ov)
        s.apply(StagePatch(patch_id="p" + eid, run_id=s.run_id, stage_id=stage,
                           stage_attempt=1, parent_state_hash=s.state_hash(),
                           operations=[Op("CREATE", fam, eid, d, "p",
                                          premise_refs=prem or [])],
                           execution_status="SUCCESS", provenance={"provider": "t"}))

    def _scope(self, s, eid, branch):
        fwd, rev = cv._reference_graph(s, self.c)
        cands = {e["entity_id"] for e in s.standing("Candidate")}
        return cv.scope_of(eid, fwd, rev, s, self.c, branch, cands)

    def _world(self):
        s = self.state("scope")
        self._add(s, "s01", "Requirement", "REQ-SHARED", quantity_class="BAND")
        self._add(s, "s02", "Obligation", "OBL-SHARED", scope="UNIVERSAL",
                  satisfiable_at="s03", derived_from_requirements=["REQ-SHARED"])
        for cid in ("CND-A", "CND-B"):
            self._add(s, "s02", "Candidate", cid, principle={"h": "f"},
                      addresses_obligations=["OBL-SHARED"], obligations_created=[])
        self._add(s, "s03", "Body", "BOD-A", prem=["CND-A"])
        self._add(s, "s03", "Body", "BOD-B", prem=["CND-B"])
        self._add(s, "s03", "Body", "BOD-ORPHAN")
        return s

    def test_SCOPE_01_02_03_branch_other_and_orphan(self):
        s = self._world()
        self._add(s, "selection", "SelectionDecision", "SEL", selected_candidate="CND-A")
        self.assertEqual(cv.ACTIVE_BRANCH, self._scope(s, "BOD-A", "CND-A")[0])
        self.assertEqual(cv.OTHER_BRANCH, self._scope(s, "BOD-B", "CND-A")[0])
        self.assertEqual(cv.UNSCOPED, self._scope(s, "BOD-ORPHAN", "CND-A")[0])

    def test_SCOPE_04_no_path_is_not_common(self):
        """The unsound fallback is gone."""
        s = self.state()
        self._add(s, "s02", "Candidate", "CND-A", principle={"h": "f"},
                  addresses_obligations=[], obligations_created=[])
        self._add(s, "s01", "Requirement", "REQ-U", quantity_class="BAND")
        scope, why = self._scope(s, "REQ-U", "CND-A")
        self.assertEqual(cv.UNSCOPED, scope)
        self.assertNotIn("PROVISIONAL", why)

    def test_SCOPE_05_06_common_upstream_needs_positive_evidence(self):
        s = self._world()
        self.assertEqual(cv.COMMON_UPSTREAM, self._scope(s, "REQ-SHARED", "CND-A")[0])
        bare = self.state()
        self._add(bare, "s02", "Candidate", "CND-A", principle={"h": "f"},
                  addresses_obligations=[], obligations_created=[])
        self._add(bare, "s01", "Requirement", "REQ-SHARED", quantity_class="BAND")
        self.assertEqual(cv.UNSCOPED, self._scope(bare, "REQ-SHARED", "CND-A")[0])

    def test_SCOPE_07_one_branch_upstream_is_not_common_to_all(self):
        s = self._world()
        self._add(s, "s01", "Requirement", "REQ-AONLY", quantity_class="BAND")
        self._add(s, "s02", "Obligation", "OBL-A", scope="CANDIDATE_DISCRIMINATING",
                  satisfiable_at="s03", derived_from_requirements=["REQ-AONLY"])
        s2 = self.state("only-b")
        self._add(s2, "s01", "Requirement", "REQ-AONLY", quantity_class="BAND")
        self._add(s2, "s02", "Obligation", "OBL-A", scope="UNIVERSAL",
                  satisfiable_at="s03", derived_from_requirements=["REQ-AONLY"])
        self._add(s2, "s02", "Candidate", "CND-A", principle={"h": "f"},
                  addresses_obligations=["OBL-A"], obligations_created=[])
        self._add(s2, "s02", "Candidate", "CND-B", principle={"h": "f"},
                  addresses_obligations=[], obligations_created=[])
        self.assertEqual(cv.COMMON_UPSTREAM, self._scope(s2, "REQ-AONLY", "CND-A")[0])
        self.assertEqual(cv.UNSCOPED, self._scope(s2, "REQ-AONLY", "CND-B")[0])

    def test_SCOPE_08_09_pre_and_post_selection(self):
        s = self._world()
        self.assertIsNone(cv.committed_branch(s, self.c))
        self.assertEqual(cv.ACTIVE_BRANCH, self._scope(s, "BOD-A", None)[0])
        self.assertEqual(cv.ACTIVE_BRANCH, self._scope(s, "BOD-B", None)[0])
        self._add(s, "selection", "SelectionDecision", "SEL", selected_candidate="CND-A")
        self.assertEqual("CND-A", cv.committed_branch(s, self.c))
        self.assertEqual(cv.OTHER_BRANCH, self._scope(s, "BOD-B", "CND-A")[0])

    def test_SCOPE_10_a_new_family_inherits_scope_generically(self):
        """No resolver change, no list, no stage branch."""
        s = self._world()
        self._add(s, "s03", "Interface", "IFC-A", prem=["CND-A"], bodies=["BOD-A"])
        self.assertEqual(cv.ACTIVE_BRANCH, self._scope(s, "IFC-A", "CND-A")[0])
        self.assertEqual(cv.OTHER_BRANCH, self._scope(s, "IFC-A", "CND-B")[0])

    def test_SCOPE_11_12_no_family_whitelist_or_benchmark_in_the_resolver(self):
        """The invariant is NO ENUMERATION, not "no family name ever appears".

        `Candidate` and `SelectionDecision` are typed IDENTITY semantics - the
        canonical names for "design alternative" and "the commitment to one". The
        resolver needs those two concepts the way it needs the notion of a
        reference; naming them is not the same as listing which families a
        consumer may see, which is what R-2 forbids. The narrow exception is
        stated here so it cannot quietly widen.
        """
        src = _code_only(cv.scope_of, cv._reachable, cv._reference_graph)
        IDENTITY = {"Candidate", "SelectionDecision"}
        named = {f for f in self.c.families if "'%s'" % f in src}
        self.assertTrue(named <= IDENTITY,
                        "resolver enumerates families beyond commitment identity: %s"
                        % sorted(named - IDENTITY))
        self.assertLessEqual(len(named), 2)
        self.assertIsNone(re.search(r"(BM-\d|PRB-\d|CND-|oracle)", src, re.I))

    def test_SCOPE_16_17_deterministic_and_cycle_safe(self):
        s = self._world()
        a = [self._scope(s, e, "CND-A") for e in sorted(s.entities)]
        b = [self._scope(s, e, "CND-A") for e in sorted(s.entities)]
        self.assertEqual(a, b)
        # A reference cycle must terminate.
        fwd = {"X": {"Y"}, "Y": {"X"}}
        self.assertEqual(set(), cv._reachable("X", fwd, {"Z"}))

    def test_SCOPE_18_unscoped_does_not_enter_the_view(self):
        s = self._world()
        self._add(s, "selection", "SelectionDecision", "SEL", selected_candidate="CND-A")
        v = build_consumer_view("s04b", s, self.c, self.resp)
        ids = {e["entity_id"] for e in v.entities}
        self.assertNotIn("BOD-ORPHAN", ids)
        self.assertNotIn("BOD-B", ids)

    def test_SCOPE_20_candidate_withdrawal_makes_its_topology_stale(self):
        """Premise lineage reuses S-1 staleness. This is why Candidate is a
        PREMISE rather than a duplicated field: withdrawing it must cost the
        topology built on it its unqualified standing, and FA-5 already says so."""
        s = self._world()
        s.apply(StagePatch(patch_id="inv", run_id=s.run_id, stage_id="s02",
                           stage_attempt=2, parent_state_hash=s.state_hash(),
                           operations=[Op("INVALIDATE", "Candidate", "CND-A", {}, "p",
                                          reason="withdrawn")],
                           execution_status="SUCCESS", provenance={"provider": "t"}))
        self.assertEqual("STALE", s.entities["BOD-A"]["_validity"])
        self.assertEqual("STANDING", s.entities["BOD-B"]["_validity"])
        self.assertNotIn("BOD-A", {e["entity_id"] for e in s.standing("Body")})
