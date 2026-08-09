"""VIEW-*: Consumer Sufficiency (U-3 / M-3).

Deterministic contract interpretation. No model, no benchmark, no stage branch.
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

from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.assy_v3.view import (Source, Sufficiency, ViewStatus,          # noqa: E402
                               build_consumer_view, derive_required_minimum,
                               derive_source_a, derive_source_b, render)
import ver3.assy_v3.view.consumer_view as cv                            # noqa: E402

STAGES = ("s01", "s02", "s03a", "s03b", "s04a", "gate", "s04b")


class _Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")

    def state(self, run="t"):
        return DesignState(run)

    def req(self, fam, **over):
        d = {f: "x" for f in self.c.required_fields(fam) if f != "entity_id"}
        d.update(over)
        return d

    def add(self, s, stage, fam, eid, **over):
        s.apply(StagePatch(patch_id="p-%s" % eid, run_id=s.run_id, stage_id=stage,
                           stage_attempt=1, parent_state_hash=s.state_hash(),
                           operations=[Op("CREATE", fam, eid, self.req(fam, **over), "p")],
                           execution_status="SUCCESS", provenance={"provider": "t"}))
        return eid


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
        self.add(s, "s04", "SelectionDecision", "SEL-1", selected_candidate="CND-A")
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
        self.add(s, "s04", "SelectionDecision", "SEL-1", selected_candidate="CND-B")
        v = build_consumer_view("s04b", s, self.c, self.resp)
        self.assertEqual("CND-B", v.branch)
        for t in v.traces:
            self.assertNotEqual(["CND-A"], t.get("branch_scope"))

    def test_VIEW_07_reference_closure_supplies_referents(self):
        s = self.state()
        self.add(s, "s03", "RigidGroup", "RGP-1", body="BOD-1")
        self.add(s, "s03", "Body", "BOD-1")
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
        a = cv._assess(s, self.c, req, [], rel)
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value, a["verdict"])
        b = cv._assess(s, self.c, req, [{"entity_id": "REQ-1"}], rel)
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
        """
        s = self.state("replay")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-0001", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-0001"])
        self.add(s, "s02", "Candidate", "CND-0001", principle={"h": "f"},
                 addresses_obligations=["OBL-0001"], obligations_created=[])
        self.add(s, "s04", "ReferenceScale", "SCL-0001", basis="RELATIVE")
        self.add(s, "s03", "Body", "BOD-0001")
        self.add(s, "s03", "RigidGroup", "RGP-0001", body="BOD-0001")
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
        self.add(s, "s03", "Joint", "JNT-0001", parent_group="RGP-0001",
                 child_group="RGP-0001", frame_origin="SCL-0001")
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
        src = self._src()
        for sid in STAGES:
            self.assertNotIn('"%s"' % sid, src, "view code branches on stage %s" % sid)

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
            "why": "control", "requires_semantics": ["configuration_state"]})
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
        self.add(s, "s04", "SelectionDecision", "SEL", selected_candidate="CND-A")
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
        a = cv._assess(s, self.c, req, sel, rel)
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
        a = cv._assess(s, self.c, req, [], rel)
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value, a["verdict"])

    def test_VIEW_C19_absent_upstream_is_missing_not_projection_failure(self):
        s = self.state()
        req = [r for r in derive_source_b("s04a", self.c, self.resp)
               if r.by_role and "quantity_constraint" in r.by_role][0]
        a = cv._assess(s, self.c, req, [], cv.relevant_ids(s, self.c, None))
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value, a["verdict"])

    def test_VIEW_C06_other_branch_stays_excluded(self):
        s = self.state()
        for cid in ("CND-A", "CND-B"):
            self.add(s, "s02", "Candidate", cid, principle={"h": "f"},
                     addresses_obligations=[], obligations_created=[])
        self.add(s, "s03", "LoadPath", "LP-A", candidate="CND-A", load_case="LC")
        self.add(s, "s03", "LoadPath", "LP-B", candidate="CND-B", load_case="LC")
        self.add(s, "s04", "SelectionDecision", "SEL", selected_candidate="CND-A")
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

    def test_the_contract_gap_is_recorded_not_papered_over(self):
        """No topology family reaches Candidate through any declared reference.

        Until a structured candidate link exists, an orphan and a real topology
        element are indistinguishable, so the classification says PROVISIONAL
        rather than asserting shared relevance it cannot establish.
        """
        edges = {}
        for fam, v in self.c.families.items():
            for _f, spec in ((v or {}).get("field_semantics") or {}).items():
                if spec.get("kind") == "reference":
                    edges.setdefault(fam, set()).add(spec["target"])

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
        self.add(s, "s03", "Body", "BOD-1")
        fwd, rev = cv._reference_graph(s, self.c)
        scope, why = cv.scope_of("BOD-1", fwd, rev, s, self.c, None)
        self.assertEqual(cv.COMMON_UPSTREAM, scope)
        self.assertIn("PROVISIONAL", why)
