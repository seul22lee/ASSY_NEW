"""Where a reference's referent may come from is the FIELD's to say.

Source A knew WHAT family a reference points at and assumed WHERE the referent
had to already be: the branch. For a load case that is circular - authoring
`LoadPath.load_case` is exactly what makes the load case branch material - so
s03b could never enter the state it was about to create. Making every dependency
design-wide instead admitted another branch's topology. Neither answer is
universal, so the contract declares it per field, and an undeclared field stays
branch-local.
"""
from __future__ import annotations

import ast
import inspect
import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402

_DS = os.path.join(_REPO, "ver3", "contracts", "DESIGN_STATE_CONTRACT.yaml")
_RESP = os.path.join(_REPO, "ver3", "contracts", "STAGE_RESPONSIBILITY_CONTRACT.yaml")

#: The smallest s03a response with a topology at all.
S03A = {
    "bodies": [{"id": "BOD-A", "instance_identity": "link", "role": "STRUCTURE"}],
    "rigid_groups": [{"id": "RGP-A", "body": "BOD-A", "members": ["BOD-A"]}],
    "joints": [{"id": "JNT-A", "joint_type": "REVOLUTE", "parent_group": "RGP-A",
                "child_group": "RGP-A", "dof": ["RZ"], "axis_direction": "+Z",
                "frame_ids": ["F1"]}],
    "interfaces": [{"id": "IFC-A", "bodies": ["BOD-A"],
                    "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"}],
    "configurations": [{"id": "CFG-A", "name": "home", "kind": "OPERATIONAL",
                        "bodies_present": ["BOD-A"], "expected_mobility": []}],
}
S03B = {
    "load_paths": [{"id": "LP-A", "load_case": "LC-1", "candidate": "CND-A",
                    "ordered_hops": ["IFC-A"]}],
    "blocking_relations": [{"rigid_group": "RGP-A", "configuration": "CFG-A",
                            "dof": "RZ", "driver": "JOINT_CLASS",
                            "holding_element": "JNT-A"}],
}


class _Counting:
    """A provider that answers in order and counts."""

    def __init__(self, *payloads):
        self.queue, self.calls = list(payloads), 0

    def capabilities(self):
        from ver3.assy_v3.providers.interfaces import ProviderCapabilities
        return ProviderCapabilities(
            provider_id="counting", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="structural test fixture")

    def generate(self, request, attempt_index=0):
        import json, time
        from ver3.assy_v3.providers.interfaces import (GenerationResponse,
                                                       GenerationResult)
        from ver3.assy_v3.providers.status import ExecutionStatus
        payload = self.queue[min(self.calls, len(self.queue) - 1)]
        self.calls += 1
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=json.dumps(payload),
                                        finish_reason="stop", truncated=False,
                                        input_tokens=None, output_tokens=None,
                                        served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(),
            ended_at=time.time(), from_cache=True)


class _Base(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        with open(_DS) as fh:
            cls.ds = yaml.safe_load(fh)
        with open(_RESP) as fh:
            cls.resp = yaml.safe_load(fh)
        cls.families = dict(cls.ds["entity_families"])
        cls.families.update(cls.ds["assurance_families"])

    def refs(self):
        for fam, spec in sorted(self.families.items()):
            for field, decl in ((spec or {}).get("field_semantics") or {}).items():
                if isinstance(decl, dict) and decl.get("kind") == "reference":
                    yield fam, field, decl

    def two_candidates(self):
        """Design-wide demands, plus a branch each. No fake lineage anywhere."""
        s = DesignState(run_id="rp")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-1")
        self.add(s, "s01", "Scenario", "SCN-1", actors=["ACT-1"])
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"],
                 involves_actors=["ACT-1"])
        self.add(s, "s02", "LoadCase", "LC-1", scenario="SCN-1")
        self.add(s, "s02", "PhysicalEffectObligation", "PEO-1",
                 between_roles=["ACT-1"], under_load_case="LC-1",
                 addresses_obligations=["OBL-1"])
        for cid in ("CND-A", "CND-B"):
            self.add(s, "s02", "Candidate", cid, principle={"h": "f"},
                     addresses_obligations=["OBL-1"], obligations_created=[])
        return s

    def branch_topology(self, s, candidate, suffix):
        self.add(s, "s03", "Body", "BOD-%s" % suffix, prem=[candidate])
        self.add(s, "s03", "RigidGroup", "RGP-%s" % suffix, prem=[candidate],
                 body="BOD-%s" % suffix)
        return "BOD-%s" % suffix


# =====================================================================
# The declaration
# =====================================================================
class TestReferentPopulationContract(_Base):

    def test_RP_01_an_undeclared_reference_stays_branch_local(self):
        undeclared = [(f, k) for f, k, d in self.refs()
                      if "referent_population" not in d]
        self.assertTrue(undeclared,
                        "every reference declares one, so the default is untested")
        self.assertIn(("PhysicalInteraction", "groups"), undeclared)
        req = [r for r in cv.derive_source_a("s03b", self.c, self.resp)
               if r.trace.get("output_field") == "PhysicalInteraction.groups"]
        self.assertTrue(req)
        rule = req[0].selection_for(req[0].atoms()[0][0])
        self.assertEqual(cv.INVOCATION_BRANCH, rule["population"],
                         "an unclassified reference widened what a consumer sees")

    def test_RP_02_03_the_two_cross_scope_fields_derive_design_wide(self):
        got = {}
        for r in cv.derive_source_a("s03b", self.c, self.resp):
            for obligation, _fams in r.atoms():
                got[obligation] = r.selection_for(obligation)["population"]
        self.assertEqual(
            cv.DESIGN_WIDE,
            got["LoadPath.load_case -[reference]-> LoadCase"])
        self.assertEqual(
            cv.DESIGN_WIDE,
            got["PhysicalInteraction.discharges_effect -[reference]-> "
                "PhysicalEffectObligation"])

    def test_RP_04_05_no_family_or_stage_heuristic_decides_population(self):
        src = inspect.getsource(cv.derive_source_a)
        named = [f for f in self.c.families if re.search(r"['\"]%s['\"]" % f, src)]
        self.assertEqual([], named, "Source A names families: %s" % named)
        self.assertIsNone(re.search(r"['\"]s0\d", src), "Source A names a stage")
        self.assertIsNone(re.search(r"owned_by|owner_of", src),
                          "population is decided from ownership, not declaration")

    def test_RP_06_candidate_specific_topology_stays_branch_local(self):
        branch_bearing = {"Body", "RigidGroup", "Joint", "Interface", "Configuration",
                          "FunctionalRegion", "Candidate", "PhysicalInteraction",
                          "AssemblyStep", "Feature", "Envelope", "State", "Transition"}
        for fam, field, decl in self.refs():
            if decl.get("target") in branch_bearing:
                self.assertNotEqual(cv.DESIGN_WIDE, decl.get("referent_population"),
                                    "%s.%s -> %s is design-wide"
                                    % (fam, field, decl.get("target")))

    def test_RP_08_population_and_existence_are_independent(self):
        seen = set()
        for r in cv.derive_source_a("s03b", self.c, self.resp):
            for obligation, _f in r.atoms():
                rule = r.selection_for(obligation)
                seen.add((rule["population"], rule["existence"]))
        self.assertGreater(len({p for p, _e in seen}), 1, "one population only")
        self.assertGreater(len({e for _p, e in seen}), 1, "one existence only")

    def test_RP_09_optional_and_many_existence_is_unchanged(self):
        by_field = {}
        for r in cv.derive_source_a("s03b", self.c, self.resp):
            for obligation, _f in r.atoms():
                by_field[r.trace["output_field"]] = r.selection_for(obligation)
        self.assertEqual(cv.MAY_BE_EMPTY,
                         by_field["PhysicalInteraction.at_interface"]["existence"])
        self.assertEqual(cv.MAY_BE_EMPTY,
                         by_field["AssemblyStep.activates"]["existence"])
        self.assertEqual(cv.REQUIRED_NONEMPTY,
                         by_field["LoadPath.load_case"]["existence"])

    def test_RP_10_co_produced_dependencies_are_still_excluded(self):
        keys = {r.key for r in cv.derive_source_a("s02", self.c, self.resp)}
        self.assertFalse(any(k.endswith("-> Obligation") for k in keys),
                         "s02 demands an obligation it creates itself")

    # -- validation ---------------------------------------------------
    def test_RP_11_only_reference_fields_may_declare_it(self):
        for fam, spec in self.families.items():
            for field, decl in ((spec or {}).get("field_semantics") or {}).items():
                if isinstance(decl, dict) and "referent_population" in decl:
                    self.assertEqual("reference", decl.get("kind"),
                                     "%s.%s is not a reference" % (fam, field))

    def test_RP_12_only_canonical_vocabulary_is_accepted(self):
        vocab = set(self.resp["instance_selection_vocabulary"]["population"])
        for fam, field, decl in self.refs():
            pop = decl.get("referent_population")
            if pop is not None:
                self.assertIn(pop, vocab, "%s.%s" % (fam, field))

    def test_RP_13_an_invalid_declaration_fails_closed(self):
        import copy
        resp = copy.deepcopy(self.resp)

        class _C:
            def __init__(self, base):
                self._b = base

            def __getattr__(self, n):
                return getattr(self._b, n)

            @property
            def families(self):
                fams = copy.deepcopy(self._b.families)
                fams["Joint"]["field_semantics"]["parent_group"][
                    "referent_population"] = "EVERYWHERE"
                return fams

        with self.assertRaises(ValueError):
            cv.derive_source_a("s03a", _C(self.c), resp)

    def test_RP_14_the_declaration_does_not_touch_cardinality_or_resolvable(self):
        for fam, field, decl in self.refs():
            if decl.get("referent_population"):
                self.assertIn("cardinality", decl, "%s.%s" % (fam, field))
                self.assertIn("resolvable", decl, "%s.%s" % (fam, field))


# =====================================================================
# Readiness, isolation, and post-authoring lineage
# =====================================================================
class TestS03BReadiness(_Base):

    def prepared(self):
        s = self.two_candidates()
        self.branch_topology(s, "CND-B", "B")
        provider = _Counting(S03A, S03B)
        a = S03TopologyAndMobility().invoke(
            provider, s, s.run_id, {"candidate": {"entity_id": "CND-A"}},
            invocation=cv.InvocationContext(branch="CND-A"))
        self.assertEqual("SUCCESS", a.execution_status.value, a.problems)
        s.apply(a.patch)
        return s, provider

    def test_S3B_RDY_01_02_03_04_ready_with_demands_and_without_the_other_branch(self):
        s, _p = self.prepared()
        view = S03BMobilityAndAssembly().consumer_view(
            s, cv.InvocationContext(branch="CND-A"))
        unmet = [c["obligation"] for a in view.assessment for c in a["coverage"]
                 if c["verdict"] != "SATISFIED"]
        self.assertEqual([], unmet, "s03b is still blocked")
        self.assertIs(cv.ViewStatus.VIEW_READY, view.status)
        ids = {e["entity_id"] for e in view.entities}
        self.assertIn("LC-1", ids, "the design-wide load case is not visible")
        self.assertIn("PEO-1", ids, "the design-wide effect obligation is not visible")
        self.assertIn("BOD-A", ids, "this branch's own topology is missing")
        self.assertNotIn("BOD-B", ids, "the other candidate's topology leaked in")

    def test_S3B_RDY_05_the_provider_is_called_once_when_ready(self):
        s, provider = self.prepared()
        before = provider.calls
        b = S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=cv.InvocationContext(branch="CND-A"))
        self.assertEqual(before + 1, provider.calls)
        self.assertIsNotNone(b.patch, b.problems)
        self.assertNotEqual("CONSUMER_CONTEXT_INSUFFICIENT", b.execution_status.value)

    def test_S3B_RDY_06_07_no_fake_lineage_was_needed(self):
        s, _p = self.prepared()
        for eid in ("LC-1", "PEO-1"):
            self.assertEqual([], s.entities[eid].get("_premises", []),
                             "%s was given a premise it does not have" % eid)
        cand = s.entities["CND-A"]
        self.assertEqual(["OBL-1"], cand["addresses_obligations"],
                         "an edge was invented to reach design-wide material")
        fwd, rev = cv._reference_graph(s, self.c)
        for eid in ("LC-1", "PEO-1"):
            self.assertEqual(cv.UNSCOPED,
                             cv.scope_of(eid, fwd, rev, s, self.c, "CND-A")[0],
                             "%s is visible, and that is NOT the same as being "
                             "branch material" % eid)


class TestPostAuthoringLineage(_Base):

    def test_POST_LIN_01_02_a_load_path_makes_its_load_case_common_upstream(self):
        s = self.two_candidates()
        self.branch_topology(s, "CND-B", "B")
        provider = _Counting(S03A, S03B)
        inv = cv.InvocationContext(branch="CND-A")
        a = S03TopologyAndMobility().invoke(
            provider, s, s.run_id, {"candidate": {"entity_id": "CND-A"}}, invocation=inv)
        s.apply(a.patch)
        fwd, rev = cv._reference_graph(s, self.c)
        self.assertEqual(cv.UNSCOPED, cv.scope_of("LC-1", fwd, rev, s, self.c, "CND-A")[0])
        b = S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2, invocation=inv)
        s.apply(b.patch)
        self.assertIn("LP-A", s.entities, "s03b authored no load path")
        fwd, rev = cv._reference_graph(s, self.c)
        self.assertEqual(cv.COMMON_UPSTREAM,
                         cv.scope_of("LC-1", fwd, rev, s, self.c, "CND-A")[0],
                         "the authored reference did not establish lineage")
        self.assertEqual(cv.OTHER_BRANCH,
                         cv.scope_of("BOD-B", fwd, rev, s, self.c, "CND-A")[0])

    def test_POST_LIN_03_04_05_an_interaction_does_the_same_for_its_obligation(self):
        """The relation, applied through the authoritative write path.

        The current s03b producer authors load paths and assembly steps but no
        PhysicalInteraction - that producer gap is S-4's. What S-3 owns is whether
        the AUTHORED RELATION establishes lineage, so the relation is written here
        and the graph is asked.
        """
        s = self.two_candidates()
        self.branch_topology(s, "CND-A", "A")
        self.branch_topology(s, "CND-B", "B")
        fwd, rev = cv._reference_graph(s, self.c)
        self.assertEqual(cv.UNSCOPED, cv.scope_of("PEO-1", fwd, rev, s, self.c, "CND-A")[0])
        fields = self._fields_for(s, self.c, "s03", "PhysicalInteraction",
                                  {"groups": ["RGP-A"], "discharges_effect": "PEO-1"})
        s.apply(StagePatch(
            patch_id="pi", run_id=s.run_id, stage_id="s03", stage_attempt=2,
            parent_state_hash=s.state_hash(),
            operations=[Op("CREATE", "PhysicalInteraction", "PI-A", fields, "p",
                           premise_refs=["CND-A"])],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        fwd, rev = cv._reference_graph(s, self.c)
        self.assertEqual(cv.COMMON_UPSTREAM,
                         cv.scope_of("PEO-1", fwd, rev, s, self.c, "CND-A")[0])
        self.assertEqual(cv.OTHER_BRANCH,
                         cv.scope_of("BOD-B", fwd, rev, s, self.c, "CND-A")[0],
                         "the other branch became upstream material")
        self.assertEqual(cv.UNSCOPED,
                         cv.scope_of("PEO-1", fwd, rev, s, self.c, "CND-B")[0],
                         "B gained lineage from A's interaction")


if __name__ == "__main__":
    unittest.main()
