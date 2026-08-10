"""Branch-safe bookkeeping, and citations that are dependencies.

Two things that look finished from inside one candidate and are not.

BOOKKEEPING SCOPE. Mobility production is branch-scoped: s03b derives a
candidate's grid from that candidate's view. `dof_totality_check` took the
product of EVERY group in state with EVERY configuration in state, so the moment
a design held two alternatives it demanded cells like "candidate A's group in
candidate B's configuration" - pairs no mechanism contains and no producer could
disposition. Bookkeeping over a domain production never had is not bookkeeping
about production.

CITATION vs DEPENDENCY. A disposition record cited `CRL-2` with the right family
and a referent that resolved. That is reference integrity, and it is not the same
fact as `Op.premise_refs`: nothing put CRL-2 into the dependency substrate, so
invalidating CRL-2 left the MobilityExpectation STANDING while it went on
claiming a DOF was held by something the design had withdrawn.

Every case here runs the real invocation path and the real controlled operations.
"""
from __future__ import annotations

import json
import os
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    DOF_NAMES, S03BMobilityAndAssembly, S03TopologyAndMobility,
    accumulated_dof_domain, cited_premises, dof_totality_check)
from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from .test_s02_s03b_integration import S02, _Canned                     # noqa: E402

CELLS = len(DOF_NAMES)


def _s02(suffixes):
    """The shared s02 payload, with one candidate per branch this case wants.

    Copied and extended rather than mutated: another module owns S02 and a test
    that edits it in place would decide what its neighbours see.
    """
    payload = json.loads(json.dumps(S02))
    template = payload["candidates"][0]
    payload["candidates"] = [
        dict(template, id="CND-%s" % sfx, summary="alternative %s" % sfx)
        for sfx in suffixes]
    return payload


def _s03a(sfx, ngroups, nconfigs):
    """A branch of any shape. Group and configuration COUNTS are parameters, so
    nothing below can be true only for a square topology."""
    gs = ["G%d" % i for i in range(ngroups)]
    return {
        "bodies": [{"id": "BOD-%s%s" % (g, sfx), "instance_identity": "link",
                    "role": "STRUCTURE"} for g in gs],
        "rigid_groups": [{"id": "RGP-%s%s" % (g, sfx), "body": "BOD-%s%s" % (g, sfx),
                          "members": ["BOD-%s%s" % (g, sfx)]} for g in gs],
        "interfaces": [{"id": "IFC-%s" % sfx, "bodies": ["BOD-G0%s" % sfx],
                        "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"},
                       {"id": "IFG-%s" % sfx, "bodies": ["BOD-G0%s" % sfx],
                        "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"}],
        "joints": [{"id": "JNT-%s" % sfx, "joint_type": "REVOLUTE",
                    "parent_group": "RGP-G0%s" % sfx, "child_group": "RGP-G0%s" % sfx,
                    "dof": ["RZ"], "axis_direction": "+Z", "frame_ids": ["F1"]}],
        "configurations": [{"id": "CFG-C%d%s" % (j, sfx), "name": "c%d" % j,
                            "kind": "OPERATIONAL",
                            "bodies_present": ["BOD-G0%s" % sfx],
                            "expected_mobility": []} for j in range(nconfigs)],
    }


def _s03b(sfx, relations=1, irrelevance=True):
    rels = [{"id": "CRL-%d%s" % (k, sfx), "retained_group": "RGP-G0%s" % sfx,
             "blocked_dofs": [("TZ", "TX", "TY")[k]],
             "configurations": ["CFG-C0%s" % sfx], "driver": "LOAD",
             "blocked_direction": "+Z", "defeat_specification": "push",
             "provider_reaction_site": "RSR-0001",
             "provider_site": "IFG-%s" % sfx,
             "maintaining_interaction": "PHI-%s" % sfx} for k in range(relations)]
    return {
        "physical_interactions": [
            {"id": "PHI-%s" % sfx, "groups": ["RGP-G0%s" % sfx],
             "effect": "TRANSMIT_FORCE", "discharges_effect": "PEO-0001",
             "at_interface": "IFC-%s" % sfx,
             "configurations": ["CFG-C0%s" % sfx]}],
        "constraint_relations": rels,
        "irrelevance": ([{"rigid_group": "RGP-G0%s" % sfx,
                          "configuration": "CFG-C0%s" % sfx,
                          "dof": ["RX"], "scenario": "SCN-IDLE"}]
                        if irrelevance else []),
        "load_paths": [{"id": "LDP-%s" % sfx, "load_case": "LC-0001",
                        "candidate": "CND-%s" % sfx,
                        "ordered_hops": ["IFC-%s" % sfx, "IFG-%s" % sfx],
                        "terminates_at": "RSR-0001"}],
        "assembly_steps": [{"id": "ASY-%s" % sfx, "order_index": 1,
                            "body": "BOD-G0%s" % sfx, "access_side": "+Z",
                            "activates": [], "termination_strategy": "NONE",
                            "path_kind": "RIGID", "depends_on": []}],
        "unresolved": [],
    }


class _Chain(_fixtures.StateBuilder, unittest.TestCase):
    """One accumulated DesignState holding as many branches as a case wants."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def build(self, shapes, relations=1, irrelevance=True):
        """`shapes` is [(suffix, n_groups, n_configurations), ...]."""
        s = DesignState(run_id="branch")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        self.add(s, "s01", "Scenario", "SCN-IDLE", actors=["ACT-0001"])
        payloads = [_s02([sfx for sfx, _g, _c in shapes])]
        for sfx, ng, nc in shapes:
            payloads += [_s03a(sfx, ng, nc), _s03b(sfx, relations, irrelevance)]
        provider = _Canned(*payloads)
        s.apply(S02ObligationAndCandidates().invoke(provider, s, s.run_id).patch)
        outs = {}
        for sfx, ng, nc in shapes:
            inv = cv.InvocationContext(branch="CND-%s" % sfx)
            s.apply(S03TopologyAndMobility().invoke(
                provider, s, s.run_id,
                {"candidate": {"entity_id": "CND-%s" % sfx}},
                invocation=inv).patch)
            out = S03BMobilityAndAssembly().invoke(
                provider, s, s.run_id, {"candidate": "CND-%s" % sfx},
                attempt=2, invocation=inv)
            self.assertIsNotNone(out.patch, out.problems)
            s.apply(out.patch)
            outs[sfx] = (out, inv)
        return s, outs

    def cells_of(self, state, sfx):
        return {(d["rigid_group"], d["configuration"], d["dof"])
                for m in state.family("MobilityExpectation")
                for d in m["dispositions"] if d["rigid_group"].endswith(sfx)}

    def mex_for(self, state, config):
        for m in state.family("MobilityExpectation"):
            if m["configuration"] == config:
                return m
        raise AssertionError("no MobilityExpectation for %s" % config)

    def validity(self, state, eid):
        return state.entities[eid].get("_validity")

    def revise(self, state, op):
        state.apply(StagePatch(
            patch_id="rev-%d" % len(state.applied_patches), run_id=state.run_id,
            stage_id="s03", stage_attempt=9, parent_state_hash=state.state_hash(),
            operations=[op], execution_status="SUCCESS",
            provenance={"provider": "t"}))


# =====================================================================
# ISSUE A - the domain is the union of the branches', never the product
# =====================================================================
class TestBranchSafeTotality(_Chain):

    def test_A_TOTAL_01_one_candidate_behaves_exactly_as_before(self):
        """The correction must not be a special case for multi-candidate state."""
        state, _ = self.build([("A", 2, 2)])
        self.assertEqual(2 * 2 * CELLS, len(accumulated_dof_domain(state)))
        self.assertEqual([], dof_totality_check(state))

    def test_A_TOTAL_02_two_equal_branches_report_nothing(self):
        state, _ = self.build([("A", 2, 2), ("B", 2, 2)])
        self.assertEqual([], dof_totality_check(state),
                         "a second alternative was reported as missing mobility")
        self.assertEqual(2 * (2 * 2 * CELLS), len(accumulated_dof_domain(state)))

    def test_A_TOTAL_03_unequal_branches_sum_their_own_domains(self):
        """2x2 and 1x3. The product of all groups with all configurations is 90;
        the design has 42 cells and is complete."""
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        self.assertEqual(2 * 2 * CELLS, len(self.cells_of(state, "A")))
        self.assertEqual(1 * 3 * CELLS, len(self.cells_of(state, "B")))
        self.assertEqual(2 * 2 * CELLS + 1 * 3 * CELLS,
                         len(accumulated_dof_domain(state)))
        groups = len(state.family("RigidGroup"))
        configs = len(state.family("Configuration"))
        self.assertNotEqual(groups * configs * CELLS,
                            len(accumulated_dof_domain(state)),
                            "the domain is still the design-wide product")
        self.assertEqual([], dof_totality_check(state))

    def test_A_TOTAL_04_adding_a_branch_leaves_the_first_untouched(self):
        alone, _ = self.build([("A", 2, 2)])
        together, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        mine = {c for c in accumulated_dof_domain(together) if c[0].endswith("A")}
        self.assertEqual(set(accumulated_dof_domain(alone)), mine)
        self.assertEqual(self.cells_of(alone, "A"), self.cells_of(together, "A"))

    def test_A_TOTAL_05_three_branches_are_the_union_of_three(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3), ("C", 3, 1)])
        self.assertEqual((2 * 2 + 1 * 3 + 3 * 1) * CELLS,
                         len(accumulated_dof_domain(state)))
        self.assertEqual([], dof_totality_check(state))

    def test_A_TOTAL_06_a_genuinely_missing_branch_local_cell_is_caught(self):
        """THE ONE THAT MATTERS. Branch-safe must not mean blind.

        A real omission inside candidate A, made through the real SUPERSEDE
        operation, and the checker still names exactly that cell.
        """
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        mex = self.mex_for(state, "CFG-C0A")
        dropped = mex["dispositions"][0]
        self.revise(state, Op(
            "SUPERSEDE", "MobilityExpectation", mex["entity_id"],
            {"dispositions": mex["dispositions"][1:]}, "test",
            reason="drop one cell to prove the checker still sees it"))
        found = dof_totality_check(state)
        self.assertEqual(1, len(found), found)
        self.assertIn("DOF_NOT_DISPOSITIONED", found[0])
        for part in (dropped["rigid_group"], dropped["configuration"], dropped["dof"]):
            self.assertIn(part, found[0])

    def test_A_TOTAL_07_a_cross_branch_pair_is_not_demanded(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        domain = set(accumulated_dof_domain(state))
        crossed = [(g, c) for g, c, _d in domain
                   if g.endswith("A") != c.endswith("A")]
        self.assertEqual([], crossed, "a cell spanning two alternatives")
        self.assertEqual([], [p for p in dof_totality_check(state)
                              if "DOF_NOT_DISPOSITIONED" in p])

    def test_A_TOTAL_08_a_cross_branch_cell_that_EXISTS_is_out_of_domain(self):
        """The dual. The domain shrank, so a cell outside it is now detectable."""
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        mex = self.mex_for(state, "CFG-C0A")
        crossed = dict(mex["dispositions"][0])
        crossed["configuration"] = "CFG-C0B"        # A's group, B's configuration
        self.revise(state, Op(
            "SUPERSEDE", "MobilityExpectation", mex["entity_id"],
            {"dispositions": mex["dispositions"] + [crossed]}, "test",
            reason="a cell belonging to no mechanism"))
        found = dof_totality_check(state)
        self.assertTrue(any("DOF_DISPOSITION_OUT_OF_DOMAIN" in p for p in found),
                        found)

    def test_A_TOTAL_09_it_is_still_bookkeeping(self):
        """Branch-safety is not a promotion. The check says so itself, and the
        stage contract classifies it."""
        doc = s03.dof_totality_check.__doc__
        self.assertIn("BOOKKEEPING", doc)
        c = _paths.contract(os.path.join("stages", "S03_CONTRACT.yaml"))
        c1 = [x for x in c["deterministic_exit_checks"] if x["id"] == "S03-C1"][0]
        self.assertEqual("BOOKKEEPING", c1["claim_class"])

    def test_A_TOTAL_10_branch_membership_is_not_a_second_ontology(self):
        """It is the relation the ConsumerView already uses to scope a branch."""
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        fwd, rev = cv._reference_graph(state, self.c)
        candidates = {e["entity_id"] for e in state.standing("Candidate")}
        membership = cv.branch_membership(
            state, self.c, {"RGP-G0A", "CFG-C0A", "RGP-G0B"})
        for eid, expected in (("RGP-G0A", "CND-A"), ("CFG-C0A", "CND-A"),
                              ("RGP-G0B", "CND-B")):
            self.assertEqual({expected}, membership[eid])
            self.assertEqual(cv.ACTIVE_BRANCH,
                             cv.scope_of(eid, fwd, rev, state, self.c, expected)[0])
            other = "CND-B" if expected == "CND-A" else "CND-A"
            self.assertEqual(cv.OTHER_BRANCH,
                             cv.scope_of(eid, fwd, rev, state, self.c, other)[0])


# =====================================================================
# ISSUE B - a cited premise is a dependency
# =====================================================================
class TestPremiseDependency(_Chain):

    def premises(self, state, config):
        return set(self.mex_for(state, config).get("_premises") or [])

    def test_B_PREM_01_a_blocking_relation_is_cited_AND_depended_on(self):
        state, _ = self.build([("A", 2, 2)])
        mex = self.mex_for(state, "CFG-C0A")
        self.assertTrue(any(d.get("constraint_relation") == "CRL-0A"
                            for d in mex["dispositions"]), "not cited")
        self.assertIn("CRL-0A", self.premises(state, "CFG-C0A"),
                      "cited but not depended on: citation is not dependency")

    def test_B_PREM_02_invalidating_a_used_relation_stales_the_mobility(self):
        state, _ = self.build([("A", 2, 2)])
        self.assertEqual("STANDING", self.validity(state, "MEX-CFG-C0A"))
        self.revise(state, Op("INVALIDATE", "ConstraintRelation", "CRL-0A", {},
                              "test", reason="the provider was withdrawn"))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"),
                         "the design still claims a DOF is held by a withdrawn "
                         "relation")

    def test_B_PREM_03_invalidating_an_unrelated_relation_does_nothing(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        self.revise(state, Op("INVALIDATE", "ConstraintRelation", "CRL-0B", {},
                              "test", reason="another branch's relation"))
        self.assertEqual("STANDING", self.validity(state, "MEX-CFG-C0A"))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0B"))

    def test_B_PREM_04_an_intending_joint_enters_the_dependency_set(self):
        state, _ = self.build([("A", 2, 2)])
        mex = self.mex_for(state, "CFG-C0A")
        self.assertTrue(any(d.get("by_joint") == "JNT-A" for d in mex["dispositions"]))
        self.assertIn("JNT-A", self.premises(state, "CFG-C0A"))

    def test_B_PREM_05_superseding_the_joint_stales_the_mobility(self):
        """SUPERSEDE, not INVALIDATE: both are premise changes under FA-5 and the
        dependent must lose unqualified authority either way."""
        state, _ = self.build([("A", 2, 2)])
        self.revise(state, Op("SUPERSEDE", "Joint", "JNT-A",
                              {"joint_type": "FIXED"}, "test",
                              reason="the class was wrong"))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))

    def test_B_PREM_06_an_unrelated_joint_has_no_effect(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        self.revise(state, Op("INVALIDATE", "Joint", "JNT-B", {}, "test",
                              reason="another branch's joint"))
        self.assertEqual("STANDING", self.validity(state, "MEX-CFG-C0A"))

    def test_B_PREM_07_the_set_is_the_union_of_what_was_actually_used(self):
        """Several premise kinds at once, counted from the produced rows."""
        state, _ = self.build([("A", 2, 2)], relations=3)
        mex = self.mex_for(state, "CFG-C0A")
        used = {d[s03.PREMISE_FIELD[d["disposition"]]]
                for d in mex["dispositions"]
                if s03.PREMISE_FIELD[d["disposition"]]}
        self.assertEqual({"JNT-A", "CRL-0A", "CRL-1A", "CRL-2A", "SCN-IDLE"}, used)
        # The invocation premise is additional, not a replacement for these.
        self.assertEqual(used | {"CND-A"}, self.premises(state, "CFG-C0A"))

    def test_B_PREM_08_undispositioned_fabricates_no_premise(self):
        state, _ = self.build([("A", 2, 2)], relations=1, irrelevance=False)
        mex = self.mex_for(state, "CFG-C1A")     # no relation reaches CFG-C1A
        self.assertEqual({"UNDISPOSITIONED"},
                         {d["disposition"] for d in mex["dispositions"]}
                         - {"INTENDED"})
        undisposed = [d for d in mex["dispositions"]
                      if d["disposition"] == "UNDISPOSITIONED"]
        self.assertTrue(undisposed)
        self.assertEqual([], cited_premises(undisposed),
                         "a cell that knows nothing acquired a dependency")

    def test_B_PREM_09_a_premise_used_many_times_appears_once(self):
        rows = [{"disposition": "BLOCKED_BY", "constraint_relation": "CRL-1"},
                {"disposition": "BLOCKED_BY", "constraint_relation": "CRL-1"},
                {"disposition": "BLOCKED_BY", "constraint_relation": "CRL-1"}]
        self.assertEqual(["CRL-1"], cited_premises(rows))

    def test_B_PREM_10_visibility_alone_is_not_dependency(self):
        """A Joint and a Scenario the view HOLDS but no cell USED must not become
        dependencies. Availability is not a claim."""
        state, outs = self.build([("A", 2, 2)], irrelevance=False)
        view = S03BMobilityAndAssembly().consumer_view(state, outs["A"][1]).payload()
        visible = {e["entity_id"] for fam in ("Joint", "Scenario", "Interface",
                                              "Body", "Configuration")
                   for e in view.get(fam) or []}
        self.assertIn("SCN-IDLE", visible, "the unused premise was not even visible")
        premises = self.premises(state, "CFG-C0A")
        self.assertNotIn("SCN-IDLE", premises,
                         "an available entity became a dependency without being used")
        self.assertTrue(visible - premises, "everything visible became a premise")

    def test_B_PREM_11_the_collection_reads_the_contract_not_a_field_list(self):
        """Mechanical, from the disposition -> premise-field map. A new
        disposition kind needs no change here."""
        from .test_s3_interface_readiness import _code_only
        src = _code_only(s03.cited_premises)
        self.assertIn("PREMISE_FIELD", src)
        for hard_coded in ("constraint_relation", "by_joint", "scenario",
                           "BLOCKED_BY", "INTENDED", "IRRELEVANT_BECAUSE"):
            self.assertNotIn(hard_coded, src,
                             "%s is named in the collector" % hard_coded)

    def test_B_PREM_12_no_second_provenance_system_was_built(self):
        """The existing substrate, used. Not a new one beside it."""
        from .test_s3_interface_readiness import _code_only
        derived = _code_only(S03BMobilityAndAssembly.derived_operations)
        self.assertIn("premise_refs", derived)
        self.assertIn("carry_invocation_premises", derived)


# =====================================================================
# THE CLOSURE PROBE
# =====================================================================
class TestClosureProbe(_Chain):
    """Three branches of three different shapes, through the canonical path."""

    def probe(self):
        return self.build([("A", 2, 2), ("B", 1, 3), ("C", 3, 1)], relations=2)

    def test_PROBE_domain_is_branch_union_and_bookkeeping_is_quiet(self):
        state, _ = self.probe()
        self.assertEqual((2 * 2 + 1 * 3 + 3 * 1) * CELLS,
                         len(accumulated_dof_domain(state)))
        self.assertEqual([], dof_totality_check(state))
        for sfx, n in (("A", 2 * 2), ("B", 1 * 3), ("C", 3 * 1)):
            self.assertEqual(n * CELLS, len(self.cells_of(state, sfx)), sfx)

    def test_PROBE_every_disposition_kind_occurs_and_is_premise_backed(self):
        state, _ = self.probe()
        kinds = {}
        for m in state.family("MobilityExpectation"):
            for d in m["dispositions"]:
                kinds.setdefault(d["disposition"], 0)
                kinds[d["disposition"]] += 1
                field = s03.PREMISE_FIELD[d["disposition"]]
                if field:
                    self.assertTrue(d.get(field), d)
                    self.assertIsNotNone(state.stored_family(d[field]))
        self.assertEqual({"INTENDED", "BLOCKED_BY", "IRRELEVANT_BECAUSE",
                          "UNDISPOSITIONED"}, set(kinds))

    def test_PROBE_dependency_holds_and_is_selective(self):
        state, _ = self.probe()
        for m in state.family("MobilityExpectation"):
            expected = set(cited_premises(m["dispositions"]))
            stored = set(m.get("_premises") or [])
            self.assertTrue(expected <= stored, m["entity_id"])
        self.revise(state, Op("INVALIDATE", "ConstraintRelation", "CRL-0A", {},
                              "test", reason="withdrawn"))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))
        for other in ("MEX-CFG-C0B", "MEX-CFG-C0C"):
            self.assertEqual("STANDING", self.validity(state, other),
                             "one branch's revision reached another")

    def test_PROBE_the_frozen_layers_are_unchanged(self):
        import json
        state, outs = self.probe()
        stage = S03BMobilityAndAssembly()
        for sfx in ("A", "B", "C"):
            out, inv = outs[sfx]
            parsed = json.loads(out.raw_response)
            view = stage.consumer_view(state, inv).payload()
            self.assertEqual([], stage._s4_physical_problems(
                parsed, {"consumer_view": view}), "S-4 broke: %s" % sfx)
            self.assertEqual([], stage._s5_mobility_problems(
                parsed, {"consumer_view": view}), sfx)
            self.assertEqual("SUCCESS", out.execution_status.value,
                             out.declared_incompleteness)

    def test_PROBE_producer_singularity_survives(self):
        state, outs = self.probe()
        produced = {op.provenance_ref for sfx in ("A", "B", "C")
                    for op in outs[sfx][0].patch.operations
                    if op.entity_type == "MobilityExpectation"}
        self.assertEqual({"s03:derivation"}, produced)
        legacy = {"mobility": [{"rigid_group": "RGP-G0A",
                                "configuration": "CFG-C0A", "dof": {"TZ": "M"}}],
                  "bodies": [], "rigid_groups": [], "joints": [], "interfaces": [],
                  "configurations": [], "load_paths": [], "assembly_steps": [],
                  "functional_regions": [], "unresolved": []}
        self.assertNotIn("MobilityExpectation",
                         {op.entity_type for op in
                          S03TopologyAndMobility().to_operations(legacy)})


if __name__ == "__main__":
    unittest.main()
