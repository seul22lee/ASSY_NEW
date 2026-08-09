"""Branch lineage is authored by the producer, not by whoever ran it.

At dfbfb68 the candidate premise on s03 output was stamped by
`run_window2._stamp_branch_premise`. The same semantic s03 operation, given the
same candidate, therefore produced DIFFERENT authoritative lineage depending on
which runner made the call - and the scope resolver then read a different design
out of the same engineering result. These tests hold the fact at the producer.
"""
from __future__ import annotations

import ast
import io
import json
import os
import sys
import time
import unittest
from typing import Any, Dict, List

from . import _fixtures, _paths                                                    # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

import ver3.assy_v3.view.consumer_view as cv                            # noqa: E402
from ver3.assy_v3.providers.interfaces import (GenerationResponse,      # noqa: E402
                                               GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.providers.status import ExecutionStatus               # noqa: E402
from ver3.assy_v3.stages.base import Stage, carry_invocation_premises   # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (             # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.state.design_state import Contracts, DesignState       # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                      # noqa: E402

#: A structurally valid s03 response. Not a recording of any case: the ids are
#: sequential and the mechanism is the smallest one that has a topology at all.
S03A_RESPONSE: Dict[str, Any] = {
    "bodies": [{"id": "BOD-0001", "instance_identity": "link", "role": "STRUCTURE"}],
    "rigid_groups": [{"id": "RGP-0001", "body": "BOD-0001", "members": ["BOD-0001"]}],
    "joints": [{"id": "JNT-0001", "joint_type": "REVOLUTE", "parent_group": "RGP-0001",
                "child_group": "RGP-0001", "dof": ["RZ"], "axis_direction": "Z",
                "frame_ids": ["F1"]}],
    "interfaces": [{"id": "IFC-0001", "bodies": ["BOD-0001"],
                    "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"}],
    "configurations": [{"id": "CFG-0001", "name": "home", "kind": "OPERATIONAL",
                        "bodies_present": ["BOD-0001"], "expected_mobility": []}],
}
S03B_RESPONSE: Dict[str, Any] = {
    "load_paths": [{"id": "LP-0001", "load_case": "LC-0001", "candidate": "CND-0001",
                    "ordered_hops": ["IFC-0001"]}],
    "blocking_relations": [{"rigid_group": "RGP-0001", "configuration": "CFG-0001",
                            "dof": "RZ", "driver": "JOINT_CLASS",
                            "holding_element": "JNT-0001"}],
}


class _Canned:
    """Serves prepared responses in order. A provider, not a mock of a stage:
    the real stage does the parsing, the validation and the patch."""

    def __init__(self, *payloads: Dict[str, Any]) -> None:
        self.queue = list(payloads)
        self.calls = 0

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_id="canned", model_id="none", context_window_tokens=None,
            max_output_tokens=None, supports_structured_output=True,
            supports_seed=True, requests_per_minute=None, tokens_per_minute=None,
            daily_quota_requests=None, notes="structural test fixture")

    def generate(self, request, attempt_index: int = 0) -> GenerationResult:
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
    def setUpClass(cls) -> None:
        cls.c = Contracts()


    def upstream(self, run="lineage", candidates=("CND-0001",)):
        """Everything s03 rests on, and nothing s03 authors."""
        s = DesignState(run_id=run)
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s02", "Obligation", "OBL-0001", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-0001"],
                 involves_actors=["ACT-0001"])
        self.add(s, "s02", "LoadCase", "LC-0001")
        # s03a's declared premises. Enforcement blocks the invocation without
        # them, which is the point: the fixture supplies what the stage needs
        # rather than the boundary being loosened to let it run without.
        self.add(s, "s02", "PhysicalEffectObligation", "PEO-0001",
                 between_roles=["ACT-0001"], under_load_case="LC-0001",
                 addresses_obligations=["OBL-0001"])
        for cid in candidates:
            self.add(s, "s02", "Candidate", cid, principle={"h": "f"},
                     addresses_obligations=["OBL-0001"], obligations_created=[])
        return s

    def direct_s03(self, state, candidate_id):
        """The canonical producer path, with no runner helper anywhere near it.

        `run` rather than `invoke`: these tests hold the LINEAGE property - that a
        producer records what its result depends on - and drive the mechanical
        step with a supplied payload. Readiness enforcement is a different
        question with its own suite; asserting both here would make a lineage
        regression indistinguishable from an incomplete fixture.
        """
        provider = _Canned(S03A_RESPONSE, S03B_RESPONSE)
        a = S03TopologyAndMobility().run(
            provider, {"consumer_view": {}, "candidate": {"entity_id": candidate_id}},
            state, state.run_id)
        self.assertIsNotNone(a.patch, a.problems)
        state.apply(a.patch)
        b = S03BMobilityAndAssembly().run(
            provider, {"consumer_view": {}, "candidate": candidate_id}, state,
            state.run_id, attempt=2)
        self.assertIsNotNone(b.patch, b.problems)
        state.apply(b.patch)
        return a, b, {"candidate": candidate_id}

    def scopes(self, state, branch):
        fwd, rev = cv._reference_graph(state, self.c)
        return {eid: cv.scope_of(eid, fwd, rev, state, self.c, branch)[0]
                for eid in state.entities}

    def premises_of(self, patch):
        return {op.entity_id: list(op.premise_refs) for op in patch.operations}


class TestLineagePopulation(_Base):

    def test_LINEAGE_01_direct_s03a_preserves_candidate_lineage(self):
        s = self.upstream()
        a, _b, _d = self.direct_s03(s, "CND-0001")
        got = self.premises_of(a.patch)
        self.assertTrue(got, "s03a authored nothing")
        for eid, prem in got.items():
            self.assertIn("CND-0001", prem,
                          "%s was authored to embody the candidate and does not say so" % eid)

    def test_LINEAGE_02_direct_s03b_preserves_candidate_lineage(self):
        s = self.upstream()
        _a, b, _d = self.direct_s03(s, "CND-0001")
        got = self.premises_of(b.patch)
        self.assertTrue(got, "s03b authored nothing")
        for eid, prem in got.items():
            self.assertIn("CND-0001", prem, eid)

    def test_LINEAGE_02b_the_derived_disposition_carries_it_too(self):
        """The DOF totality is derived, not authored - and is still this
        candidate's, so it is stamped by the stage that derives it."""
        s = self.upstream()
        _a, _b, demands = self.direct_s03(s, "CND-0001")
        ops = S03BMobilityAndAssembly().derived_operations(
            S03B_RESPONSE, ["RGP-0001"], ["CFG-0001"],
            [dict(j) for j in s.family("Joint")], demands)
        self.assertTrue(ops, "no disposition derived")
        for op in ops:
            self.assertEqual(["CND-0001"], list(op.premise_refs))

    def test_LINEAGE_03_window_execution_preserves_the_same_lineage(self):
        from ver3.tools import run_window2
        s = self.upstream(run="window")
        rec = run_window2.run_s03("CASE", {"entity_id": "CND-0001"}, s,
                                  _Canned(S03A_RESPONSE, S03B_RESPONSE), 1)
        out = rec.get("_state")
        self.assertIsNotNone(out, rec.get("failures"))
        authored = [e for e in out.entities
                    if out.entities[e].get("_created_by") == "s03"]
        self.assertTrue(authored, "the window run authored no s03 entity")
        for eid in authored:
            self.assertIn("CND-0001", out.entities[eid].get("_premises", []), eid)

    def test_LINEAGE_04_canonical_invocation_is_runner_independent(self):
        """invoke() vs invoke(). EXACT equality, nothing relaxed.

        The earlier version of this test compared `run()` on one side against
        `invoke()` on the other, so the two paths executed to DIFFERENT DEPTHS:
        the direct side bypassed readiness and authored a LoadPath, which made
        its LoadCase COMMON_UPSTREAM, while the window side blocked s03b and left
        the same LoadCase UNSCOPED. That is not a runner difference - it is a
        comparison between an invocation that happened and one that did not, and
        weakening the assertion to absorb it would have hidden the real question.

        Both sides now go through the canonical boundary, so both reach the same
        depth and the comparison is exact: same entities, same premise lineage,
        same branch scope, same provider call count.
        """
        from ver3.tools import run_window2

        class _Counting(_Canned):
            def __init__(self, *payloads):
                _Canned.__init__(self, *payloads)
                self.n = 0

            def generate(self, request, attempt_index=0):
                self.n += 1
                return _Canned.generate(self, request, attempt_index)

        direct, dp = self.upstream(run="direct"), _Counting(S03A_RESPONSE, S03B_RESPONSE)
        invocation = cv.InvocationContext(branch="CND-0001")
        a = S03TopologyAndMobility().invoke(
            dp, direct, direct.run_id, {"candidate": {"entity_id": "CND-0001"}},
            invocation=invocation)
        self.assertEqual("SUCCESS", a.execution_status.value, a.problems)
        direct.apply(a.patch)
        b = S03BMobilityAndAssembly().invoke(
            dp, direct, direct.run_id, {"candidate": "CND-0001"}, attempt=2,
            invocation=invocation)

        wp = _Counting(S03A_RESPONSE, S03B_RESPONSE)
        window = run_window2.run_s03("CASE", {"entity_id": "CND-0001"},
                                     self.upstream(run="window"), wp, 1)["_state"]

        # Both must have reached s03b, or the rest of this test compares nothing.
        self.assertEqual("SUCCESS", a.execution_status.value, a.problems)
        self.assertNotEqual("CONSUMER_CONTEXT_INSUFFICIENT", b.execution_status.value,
                            "s03b never ran, so this proves no equivalence")
        self.assertIsNotNone(b.patch, b.problems)
        direct.apply(b.patch)
        # The deterministic DOF disposition is part of the same production step:
        # `derived_operations` lives on the stage, and the window path runs it. It
        # is included here rather than excluded from the comparison, so the R-C
        # residual (its orchestration is still runner-bound, owner S-5) cannot
        # hide a lineage difference behind it.
        ops = S03BMobilityAndAssembly().derived_operations(
            S03B_RESPONSE,
            [g["entity_id"] for g in direct.family("RigidGroup")],
            [c["entity_id"] for c in direct.family("Configuration")],
            [dict(j) for j in direct.family("Joint")],
            {"candidate": "CND-0001"})
        if ops:
            direct.apply(StagePatch(
                patch_id="%s-s03-derived" % direct.run_id, run_id=direct.run_id,
                stage_id="s03", stage_attempt=3,
                parent_state_hash=direct.state_hash(), operations=ops,
                execution_status="SUCCESS",
                provenance={"purpose": "derive the total DOF disposition",
                            "provider": "deterministic"}))
        self.assertEqual(dp.n, wp.n, "the two paths called the provider a "
                                     "different number of times")
        self.assertEqual(2, dp.n, "s03a and s03b must each have been called once")

        ds, ws = self.scopes(direct, "CND-0001"), self.scopes(window, "CND-0001")
        self.assertEqual(set(ds), set(ws), "the two paths authored different state")
        for eid in sorted(ds):
            self.assertEqual(ds[eid], ws[eid],
                             "%s is %s directly and %s through the window"
                             % (eid, ds[eid], ws[eid]))
            self.assertEqual(sorted(direct.entities[eid].get("_premises", [])),
                             sorted(window.entities[eid].get("_premises", [])),
                             "%s carries different lineage" % eid)
        # COMMON_UPSTREAM and UNSCOPED are different findings and are compared as
        # such: the loop above is exact equality, not a shared bucket. The load
        # case proves it carries weight - it is upstream material on BOTH sides
        # only because both authored the load path that reaches it.
        self.assertEqual(cv.COMMON_UPSTREAM, ds["LC-0001"])
        self.assertEqual(cv.COMMON_UPSTREAM, ws["LC-0001"])

    def test_LINEAGE_04b_s03b_is_ready_and_nothing_is_unmet(self):
        """The blocker recorded at 1fe7f26 is gone, and the fixture did not move.

        s03b used to be CONSUMER_CONTEXT_INSUFFICIENT here because two Source-A
        dependencies asked for BRANCH-SCOPED existence of material that is
        candidate-independent - which authoring the reference is what creates.
        The fields now declare where their referent comes from.
        """
        s = self.upstream()
        invocation = cv.InvocationContext(branch="CND-0001")
        a = S03TopologyAndMobility().invoke(
            _Canned(S03A_RESPONSE, S03B_RESPONSE), s, s.run_id,
            {"candidate": {"entity_id": "CND-0001"}}, invocation=invocation)
        s.apply(a.patch)
        view = S03BMobilityAndAssembly().consumer_view(s, invocation)
        unmet = [c["obligation"] for asm in view.assessment for c in asm["coverage"]
                 if c["verdict"] != "SATISFIED"]
        self.assertEqual([], unmet, "s03b is blocked again")
        self.assertIs(cv.ViewStatus.VIEW_READY, view.status)

    def test_LINEAGE_05_existing_premises_are_preserved(self):
        op = Op("CREATE", "Body", "BOD-9", {}, "p", premise_refs=["P1", "P2"])
        out = carry_invocation_premises([op], ["CND-0001"])
        self.assertEqual(["P1", "P2", "CND-0001"], out[0].premise_refs,
                         "an existing dependency was replaced or reordered")

    def test_LINEAGE_06_the_candidate_premise_is_not_duplicated(self):
        op = Op("CREATE", "Body", "BOD-9", {}, "p", premise_refs=["CND-0001"])
        out = carry_invocation_premises([op], ["CND-0001", "CND-0001"])
        self.assertEqual(["CND-0001"], out[0].premise_refs)
        # and stamping the same operation twice changes nothing
        twice = carry_invocation_premises(out, ["CND-0001"])
        self.assertEqual(["CND-0001"], twice[0].premise_refs)

    def test_LINEAGE_06b_a_candidate_is_never_its_own_premise(self):
        op = Op("CREATE", "Candidate", "CND-0001", {}, "p")
        self.assertEqual([], carry_invocation_premises([op], ["CND-0001"])[0].premise_refs)

    def test_LINEAGE_06c_only_created_records_carry_the_invocation_premise(self):
        """An EXTEND of an entity that already existed must not move it onto the
        branch: `_merge_premises` writes premises on the ENTITY, and the entity
        does not exist because of this invocation."""
        ext = Op("EXTEND", "Requirement", "REQ-0001", {"note": "x"}, "p")
        self.assertEqual([], carry_invocation_premises([ext], ["CND-0001"])[0].premise_refs)

    def test_LINEAGE_07_08_09_branch_other_branch_and_orphan(self):
        s = self.upstream(candidates=("CND-A", "CND-B"))
        self.add(s, "s03", "Body", "BOD-A", prem=["CND-A"])
        self.add(s, "s03", "Body", "BOD-B", prem=["CND-B"])
        self.add(s, "s03", "Body", "BOD-ORPHAN")
        sc = self.scopes(s, "CND-A")
        self.assertEqual(cv.ACTIVE_BRANCH, sc["BOD-A"])
        self.assertEqual(cv.OTHER_BRANCH, sc["BOD-B"])
        self.assertEqual(cv.UNSCOPED, sc["BOD-ORPHAN"])

    def test_LINEAGE_10_invalidating_the_candidate_costs_its_topology_standing(self):
        """FA-5, unchanged. No second branch-invalidity mechanism was added: the
        lineage is a premise, so the existing propagation does this already."""
        s = self.upstream()
        self.direct_s03(s, "CND-0001")
        before = {e: s.entities[e].get("_validity") for e in s.entities}
        self.assertTrue(all(v == "STANDING" for v in before.values()), before)
        s.apply(StagePatch(
            patch_id="withdraw", run_id=s.run_id, stage_id="s02", stage_attempt=9,
            parent_state_hash=s.state_hash(),
            operations=[Op("INVALIDATE", "Candidate", "CND-0001", {}, "p",
                           reason="the alternative was withdrawn")],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        topology = [e for e in s.entities
                    if "CND-0001" in s.entities[e].get("_premises", [])]
        self.assertTrue(topology, "nothing declared the candidate as a premise")
        for eid in topology:
            self.assertNotEqual("STANDING", s.entities[eid]["_validity"],
                                "%s kept unqualified standing after its premise "
                                "was withdrawn" % eid)
        self.assertEqual("STANDING", s.entities["REQ-0001"]["_validity"],
                         "upstream material was dragged down with the branch")


def _tool_sources():
    root = os.path.join(_REPO, "ver3", "tools")
    for name in sorted(os.listdir(root)):
        if name.endswith(".py"):
            yield os.path.join(root, name), open(os.path.join(root, name)).read()


class TestAuthorshipStaysInProductionCode(_Base):
    """The invariant: a runner may INVOKE a producer, but may not decide what an
    engineering result depends on. Checked structurally, so a rename or a
    reworded comment cannot make it pass or fail by accident."""

    #: The one place in `ver3/tools` still allowed to put premises on operations.
    #: It is the s04 commit path, which is S-4 work and is not migrated. Pinned by
    #: name so a NEW tool-side premise site fails this test instead of joining a
    #: crowd. Growing this set is a decision, not an accident.
    TOOL_PREMISE_SITES = {"_commit_s04"}

    def _premise_sites(self):
        """(file, enclosing function) for every premise authorship act in tools."""
        found = []
        for path, src in _tool_sources():
            base = os.path.basename(path)
            for fn in ast.walk(ast.parse(src)):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if "premise" in fn.name:
                    found.append((base, fn.name, "defines a premise helper"))
                for node in ast.walk(fn):
                    if isinstance(node, ast.Call):
                        for kw in node.keywords:
                            if kw.arg == "premise_refs":
                                found.append((base, fn.name, "builds premise_refs"))
                    if isinstance(node, (ast.Assign, ast.AugAssign)):
                        tgts = (node.targets if isinstance(node, ast.Assign)
                                else [node.target])
                        for tgt in tgts:
                            if isinstance(tgt, ast.Attribute) and tgt.attr == "premise_refs":
                                found.append((base, fn.name, "assigns .premise_refs"))
        return found

    def test_LINEAGE_11_no_tool_authors_s03_branch_lineage(self):
        offences = [s for s in self._premise_sites()
                    if "s03" in s[1] or "branch" in s[1] or "candidate" in s[1]]
        self.assertEqual([], offences,
                         "a runner is authoring s03 branch lineage again")

    def test_LINEAGE_11c_no_new_tool_side_premise_authorship_appears(self):
        """The s04 commit path still stamps its own premises. That is a separate
        boundary, on a stage this pass did not migrate - recorded, and fenced so
        it cannot spread."""
        sites = {fn for _f, fn, _w in self._premise_sites()}
        self.assertTrue(sites <= self.TOOL_PREMISE_SITES,
                        "new tool-side premise authorship: %s"
                        % sorted(sites - self.TOOL_PREMISE_SITES))

    def test_LINEAGE_11b_invocation_premises_is_declared_only_by_producers(self):
        """Positive half: the hook exists, and only stage code overrides it."""
        self.assertTrue(hasattr(Stage, "invocation_premises"))
        self.assertEqual([], Stage().invocation_premises({}),
                         "the default asserts a premise nothing declared")
        declared = []
        for base, _dirs, names in os.walk(os.path.join(_REPO, "ver3")):
            if "test" in base or "__pycache__" in base:
                continue
            for name in names:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(base, name)
                for node in ast.walk(ast.parse(open(path).read())):
                    if (isinstance(node, ast.FunctionDef)
                            and node.name == "invocation_premises"):
                        declared.append(os.path.relpath(path, _REPO))
        self.assertTrue(declared)
        for path in declared:
            self.assertTrue(path.startswith("ver3/assy_v3/stages/"),
                            "%s declares an invocation premise outside the "
                            "producers" % path)

    def test_LINEAGE_12_no_benchmark_or_model_identifier_participates(self):
        import inspect
        src = "\n".join(inspect.getsource(o) for o in (
            carry_invocation_premises, Stage.invocation_premises,
            S03TopologyAndMobility.invocation_premises,
            S03BMobilityAndAssembly.invocation_premises,
            S03BMobilityAndAssembly.derived_operations))
        import re
        self.assertIsNone(re.search(r"BM-\d|PRB-\d|deepseek|gpt-|claude", src, re.I))

    def test_LINEAGE_13_no_family_list_is_needed_to_stamp_lineage(self):
        """The premise goes on whatever the candidate-scoped invocation authored.
        Naming the families would make a new s03 family silently unscoped."""
        import inspect
        src = inspect.getsource(carry_invocation_premises)
        named = [f for f in self.c.families if '"%s"' % f in src or "'%s'" % f in src]
        self.assertEqual([], named, "the normalizer names families: %s" % named)
        # a family invented here, never mentioned anywhere, is stamped anyway
        op = Op("CREATE", "SomeFamilyThatDoesNotExistYet", "NEW-1", {}, "p")
        self.assertEqual(["CND-0001"],
                         carry_invocation_premises([op], ["CND-0001"])[0].premise_refs)


class TestPriorSuitesStillHold(_Base):
    """LINEAGE-14/15. The correction moved WHERE the fact is authored; it must
    not have changed WHAT the fact is."""

    def _run(self, *classes):
        suite = unittest.TestSuite()
        load = unittest.TestLoader().loadTestsFromTestCase
        for cls in classes:
            suite.addTests(load(cls))
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful(),
                        "\n".join(t + "\n" + e for t, e in
                                  result.failures + result.errors))

    def test_LINEAGE_14_scope_tests_remain_green(self):
        from .test_consumer_view import TestBranchScopeLineage
        self._run(TestBranchScopeLineage)

    def test_LINEAGE_15_view_and_core_tests_remain_green(self):
        from .test_consumer_view import (TestCoreCorrections, TestHistoricalReplays,
                                         TestSufficiency)
        self._run(TestCoreCorrections, TestHistoricalReplays, TestSufficiency)


if __name__ == "__main__":
    unittest.main()
