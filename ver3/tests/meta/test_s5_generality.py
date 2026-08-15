"""What must be true of ANY candidate, not of the one in the fixture.

Every case here is stated over an entity family, a typed relationship, DOF
domain membership, configuration applicability and premise sufficiency. No
benchmark id, no mechanism name and no product noun appears, and the topology is
constructed to make the invariant fail on demand rather than to resemble
anything.

The distinction the whole file turns on: a field being PRESENT is not the same as
a premise being SUFFICIENT. `constraint_relation: "CRL-1"` proves nothing until
you ask whether CRL-1 covers THIS group, in THIS configuration, for THIS DOF.
"""
from __future__ import annotations

import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    DOF_NAMES, S03BMobilityAndAssembly, S03TopologyAndMobility,
    derive_mobility)
from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from .test_s02_s03b_integration import S02, _Canned                     # noqa: E402

# One joint, one relation, one irrelevance claim. Each names EXACTLY the cells it
# governs, which is what every applicability case below perturbs.
JOINT = {"entity_id": "JNT-1", "parent_group": "RGP-P", "child_group": "RGP-Q",
         "joint_type": "REVOLUTE", "axis_direction": "+Z"}
RELATION = {"id": "CRL-1", "retained_group": "RGP-Q", "blocked_dofs": ["TZ"],
            "configurations": ["CFG-1"], "driver": "LOAD",
            "provider_body": "BOD-P"}
IRRELEVANCE = {"rigid_group": "RGP-P", "configuration": "CFG-2",
               "dof": ["TX"], "scenario": "SCN-IDLE"}

GROUPS = ["RGP-P", "RGP-Q"]
CONFIGS = ["CFG-1", "CFG-2"]


def rows(joints=(JOINT,), constraints=(RELATION,), irrelevance=(IRRELEVANCE,),
         groups=GROUPS, configurations=CONFIGS):
    return derive_mobility(list(groups), list(configurations), list(joints),
                           list(constraints), list(irrelevance))


def cell(grid, group, cfg, dof):
    for r in grid:
        if (r["rigid_group"], r["configuration"], r["dof"]) == (group, cfg, dof):
            return r
    raise AssertionError("cell %s/%s/%s is not in the domain" % (group, cfg, dof))


# =====================================================================
# PRODUCER SINGULARITY
# =====================================================================

def _assurance(state, check_id):
    """The FAIL findings of one independent capability.

    S-8 / U-9 moved these out of the stage module: the code is the same
    and the position is not, which is the whole of what independence is.
    """
    from ver3.assy_v3.assurance import problems
    return problems(state, check_id)


class TestProducerSingularity(unittest.TestCase):
    """One live route into MobilityExpectation, and it is the derived one.

    s03a carried two undocumented parses - `mobility` in a compact per-DOF form
    and `dof_dispositions` in a long one - that took a disposition straight from
    the response with its premise unexamined. They outlived the prompt that asked
    for them, so no reader of the stage would have found them, and a recording in
    the old shape replayed through the topology pass still created
    MAINTAINED_BY_CLASS cells after S-5 believed the migration was finished.
    """

    LEGACY_COMPACT = {
        "bodies": [], "rigid_groups": [], "joints": [], "interfaces": [],
        "configurations": [], "load_paths": [], "assembly_steps": [],
        "functional_regions": [], "unresolved": [],
        "mobility": [{"rigid_group": "RGP-P", "configuration": "CFG-1",
                      "dof": {"TZ": "M"},
                      "detail": {"TZ": {"holding_class": "REVOLUTE"}}}]}
    LEGACY_LONG = {
        "bodies": [], "rigid_groups": [], "joints": [], "interfaces": [],
        "configurations": [], "load_paths": [], "assembly_steps": [],
        "functional_regions": [], "unresolved": [],
        "dof_dispositions": [{"rigid_group": "RGP-P", "configuration": "CFG-1",
                              "dof": "RX", "disposition": "MAINTAINED_BY_CLASS",
                              "holding_class": "invented"}]}

    def families(self, parsed):
        return {op.entity_type
                for op in S03TopologyAndMobility().to_operations(parsed)}

    def test_GEN_PROD_01_legacy_mobility_creates_nothing(self):
        self.assertNotIn("MobilityExpectation", self.families(self.LEGACY_COMPACT))

    def test_GEN_PROD_02_legacy_dof_dispositions_creates_nothing(self):
        self.assertNotIn("MobilityExpectation", self.families(self.LEGACY_LONG))

    def test_GEN_PROD_02b_a_legacy_payload_is_not_merely_ignored_quietly(self):
        """It produces NOTHING - not a stripped record, not an empty family."""
        both = dict(self.LEGACY_COMPACT)
        both["dof_dispositions"] = self.LEGACY_LONG["dof_dispositions"]
        ops = S03TopologyAndMobility().to_operations(both)
        self.assertNotIn("MAINTAINED_BY_CLASS", json.dumps([o.fields for o in ops]))

    def test_GEN_PROD_03_the_canonical_path_still_produces_it(self):
        ops = S03BMobilityAndAssembly().derived_operations(
            {"constraint_relations": [RELATION], "irrelevance": [IRRELEVANCE]},
            {"consumer_view": {
                "RigidGroup": [{"entity_id": g} for g in GROUPS],
                "Configuration": [{"entity_id": c} for c in CONFIGS],
                "Joint": [JOINT]}, "candidate": "CND-A"}, None)
        self.assertEqual({"MobilityExpectation"}, {op.entity_type for op in ops})

    def test_GEN_PROD_04_only_one_responsibility_declares_the_output(self):
        """A family with two producers was declared as the output of neither."""
        import yaml
        import os
        with open(os.path.join(os.path.dirname(cv.__file__), "..", "..",
                               "contracts",
                               "STAGE_RESPONSIBILITY_CONTRACT.yaml")) as fh:
            resp = yaml.safe_load(fh)
        declaring = [sid for sid, spec in resp["stages"].items()
                     if "MobilityExpectation" in
                     (spec.get("permitted_output_semantics") or [])]
        self.assertEqual(["s03b"], declaring)


# =====================================================================
# DOMAIN
# =====================================================================
class TestDomainGenerality(unittest.TestCase):
    """The domain is a product of the topology and of nothing else."""

    def test_GEN_DOM_01_N_groups_by_M_configurations_by_six(self):
        for n, m in ((1, 1), (2, 3), (4, 2)):
            grid = rows(groups=["RGP-%d" % i for i in range(n)],
                        configurations=["CFG-%d" % j for j in range(m)],
                        joints=(), constraints=(), irrelevance=())
            self.assertEqual(n * m * len(DOF_NAMES), len(grid))
            self.assertEqual(n * m * len(DOF_NAMES),
                             len({(r["rigid_group"], r["configuration"], r["dof"])
                                  for r in grid}), "a cell was enumerated twice")

    def test_GEN_DOM_02_evidence_changes_dispositions_not_domain_size(self):
        bare = rows(constraints=(), irrelevance=())
        full = rows()
        self.assertEqual(len(bare), len(full))
        self.assertNotEqual([r["disposition"] for r in bare],
                            [r["disposition"] for r in full],
                            "adding a premise changed nothing at all")

    def test_GEN_DOM_03_an_unrelated_candidates_topology_is_not_in_the_domain(self):
        mine = rows()
        theirs = rows(groups=GROUPS + ["RGP-OTHER"])
        self.assertEqual(len(mine) + len(CONFIGS) * len(DOF_NAMES), len(theirs))
        self.assertNotIn("RGP-OTHER", {r["rigid_group"] for r in mine})


# =====================================================================
# INTENDED
# =====================================================================
class TestIntendedPremise(unittest.TestCase):
    """A Joint implies freedom in the DOFs ITS OWN CLASS leaves free."""

    def test_GEN_INT_01_the_joint_class_decides_which_dof(self):
        for joint_type, axis, expected in (
                ("REVOLUTE", "+Z", {"RZ"}), ("PRISMATIC", "+X", {"TX"}),
                ("CYLINDRICAL", "+Y", {"RY", "TY"}),
                ("SPHERICAL", "+Z", {"RX", "RY", "RZ"}),
                ("PLANAR", "+Z", {"TX", "TY", "RZ"}), ("FIXED", "NONE", set())):
            grid = rows(joints=[dict(JOINT, joint_type=joint_type,
                                     axis_direction=axis)],
                        constraints=(), irrelevance=())
            free = {r["dof"] for r in grid
                    if r["rigid_group"] == "RGP-Q" and r["configuration"] == "CFG-1"
                    and r["disposition"] == "INTENDED"}
            self.assertEqual(expected, free, joint_type)

    def test_GEN_INT_02_every_other_dof_stays_undispositioned(self):
        grid = rows(constraints=(), irrelevance=())
        for dof in DOF_NAMES:
            got = cell(grid, "RGP-Q", "CFG-1", dof)["disposition"]
            self.assertEqual("INTENDED" if dof == "RZ" else "UNDISPOSITIONED",
                             got, dof)

    def test_GEN_INT_03_a_joint_on_another_group_supports_nothing_here(self):
        """The premise must reach THIS group. A joint elsewhere is not evidence."""
        grid = rows(joints=[dict(JOINT, child_group="RGP-ELSEWHERE")],
                    constraints=(), irrelevance=())
        self.assertEqual({"UNDISPOSITIONED"}, {r["disposition"] for r in grid})

    def test_GEN_INT_04_the_cited_joint_is_the_one_that_frees_the_dof(self):
        second = {"entity_id": "JNT-2", "child_group": "RGP-Q",
                  "joint_type": "PRISMATIC", "axis_direction": "+X"}
        grid = rows(joints=[JOINT, second], constraints=(), irrelevance=())
        self.assertEqual("JNT-1", cell(grid, "RGP-Q", "CFG-1", "RZ")["by_joint"])
        self.assertEqual("JNT-2", cell(grid, "RGP-Q", "CFG-1", "TX")["by_joint"])


# =====================================================================
# BLOCKED_BY
# =====================================================================
class TestBlockedByPremise(unittest.TestCase):
    """A ConstraintRelation covers the cells it DECLARES, and only those."""

    def test_GEN_BLK_01_only_its_own_retained_group(self):
        grid = rows()
        self.assertEqual("BLOCKED_BY", cell(grid, "RGP-Q", "CFG-1", "TZ")["disposition"])
        self.assertEqual("UNDISPOSITIONED",
                         cell(grid, "RGP-P", "CFG-1", "TZ")["disposition"])

    def test_GEN_BLK_02_only_its_own_configurations(self):
        grid = rows()
        self.assertEqual("BLOCKED_BY", cell(grid, "RGP-Q", "CFG-1", "TZ")["disposition"])
        self.assertEqual("UNDISPOSITIONED",
                         cell(grid, "RGP-Q", "CFG-2", "TZ")["disposition"])

    def test_GEN_BLK_03_only_its_own_dofs(self):
        grid = rows()
        for dof in ("TX", "TY", "RX", "RY"):
            self.assertEqual("UNDISPOSITIONED",
                             cell(grid, "RGP-Q", "CFG-1", dof)["disposition"], dof)

    def test_GEN_BLK_04_a_valid_relation_elsewhere_supports_nothing_here(self):
        """Every field well-formed, every reference resolvable, wrong cell."""
        elsewhere = dict(RELATION, id="CRL-2", retained_group="RGP-P",
                         blocked_dofs=["RX"], configurations=["CFG-2"])
        grid = rows(constraints=[elsewhere], irrelevance=())
        self.assertEqual("BLOCKED_BY", cell(grid, "RGP-P", "CFG-2", "RX")["disposition"])
        self.assertEqual("UNDISPOSITIONED",
                         cell(grid, "RGP-Q", "CFG-1", "TZ")["disposition"])

    def test_GEN_BLK_05_the_citation_is_checked_where_state_changes(self):
        """A dangling premise fails at the WRITE BOUNDARY, not in a stage method.

        The stage cannot be the place: a rule in one producer's completeness
        method binds that producer. `TestPremiseIsTyped` in test_s5_mobility
        drives the boundary directly; this asserts the declaration it reads is
        the one this family carries.
        """
        spec = Contracts().premise_record_spec("MobilityExpectation", "dispositions")
        self.assertEqual("disposition", spec["discriminator"])
        self.assertEqual("ConstraintRelation",
                         spec["record_field_semantics"]["constraint_relation"]["target"])
        self.assertFalse(spec["record_field_semantics"]
                         ["constraint_relation"]["resolvable"],
                         "a dangling premise would be legal")

    def test_GEN_BLK_06_the_cell_carries_the_relations_own_detail(self):
        rich = dict(RELATION, blocked_direction="+Z", defeat_specification="push it")
        got = cell(rows(constraints=[rich]), "RGP-Q", "CFG-1", "TZ")
        self.assertEqual("CRL-1", got["constraint_relation"])
        self.assertEqual("+Z", got["blocked_direction"])
        self.assertEqual("push it", got["defeat_specification"])


# =====================================================================
# IRRELEVANCE
# =====================================================================
class TestIrrelevancePremise(_fixtures.StateBuilder, unittest.TestCase):
    """Irrelevance is AUTHORED, cell-scoped, and cross-checked against load.

    The frozen bound matters and is stated rather than exceeded. Proposal 11.2
    makes IRRELEVANT authored "then cross-checked against LoadCases", and the
    implementation plan puts the real cross-premise consistency assurance - a DOF
    marked irrelevant that a load case loads - in U-9, at PREMISE independence.
    What S-5 owes is that the claim reaches exactly its own cell, that its
    scenario RESOLVES, and that the bounded scenario-level contradiction is
    reported. Per-DOF load and actuation resolution is not claimed here.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_GEN_IRR_01_an_authored_claim_disposes_its_own_cell(self):
        got = cell(rows(), "RGP-P", "CFG-2", "TX")
        self.assertEqual("IRRELEVANT_BECAUSE", got["disposition"])
        self.assertEqual("SCN-IDLE", got["scenario"])

    def test_GEN_IRR_01b_and_no_other_cell(self):
        grid = rows()
        for group, cfg, dof in (("RGP-Q", "CFG-2", "TX"), ("RGP-P", "CFG-1", "TX"),
                                ("RGP-P", "CFG-2", "TY")):
            self.assertNotEqual("IRRELEVANT_BECAUSE",
                                cell(grid, group, cfg, dof)["disposition"],
                                "%s/%s/%s" % (group, cfg, dof))

    def _state_with(self, scenario):
        s = DesignState(run_id="irr")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-1")
        self.add(s, "s01", "Scenario", "SCN-IDLE", actors=["ACT-1"])
        self.add(s, "s01", "Scenario", "SCN-LOAD", actors=["ACT-1"])
        self.add(s, "s03", "Body", "BOD-P")
        self.add(s, "s03", "Configuration", "CFG-2", bodies_present=["BOD-P"])
        self.add(s, "s02", "LoadCase", "LC-1", scenario="SCN-LOAD")
        s.apply(_fixtures.StagePatch(
            patch_id="mex", run_id=s.run_id, stage_id="s03", stage_attempt=1,
            parent_state_hash=s.state_hash(),
            operations=[_fixtures.Op(
                "CREATE", "MobilityExpectation", "MEX-CFG-2",
                {"configuration": "CFG-2",
                 "dispositions": [{"rigid_group": "RGP-P", "configuration": "CFG-2",
                                   "dof": "TX", "disposition": "IRRELEVANT_BECAUSE",
                                   "scenario": scenario}]}, "s03:derivation")],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        return s

    def test_GEN_IRR_02_the_same_claim_fails_when_the_load_fact_changes(self):
        """Only the scenario the claim rests on differs between these two."""
        # S-8 / U-9: the same computation, asked by the independent layer. A
        # DOF called irrelevant in a scenario that carries a load is a
        # contradiction between two AUTHORS - s02 wrote the load case and s03
        # wrote the disposition - which is why it is the check that establishes
        # rather than merely reports.
        self.assertEqual([], _assurance(self._state_with("SCN-IDLE"),
                                        "mobility_cross_premise_consistency"))
        found = _assurance(self._state_with("SCN-LOAD"),
                           "mobility_cross_premise_consistency")
        self.assertTrue(found and "IRRELEVANCE_CONTRADICTED" in found[0], found)

    def test_GEN_IRR_03_what_a_bare_scenario_id_does_and_does_not_establish(self):
        """A resolvable Scenario carrying no load case IS sufficient here.

        Saying otherwise would be inventing a rule the frozen sources do not
        state. What a bare id does NOT survive is the write boundary - it must
        name a real Scenario - and the U-9 check that will ask whether THIS DOF
        is loaded rather than whether the scenario is.
        """
        spec = Contracts().premise_record_spec(
            "MobilityExpectation", "dispositions")["record_field_semantics"]
        self.assertEqual("Scenario", spec["scenario"]["target"])
        self.assertFalse(spec["scenario"]["resolvable"])
        self.assertEqual([], _assurance(self._state_with("SCN-IDLE"),
                                        "mobility_cross_premise_consistency"))

    def test_GEN_IRR_04_a_claim_that_reaches_no_cell_is_reported(self):
        found = S03BMobilityAndAssembly()._s5_mobility_problems(
            {"constraint_relations": [RELATION],
             "irrelevance": [dict(IRRELEVANCE, scenario="")]},
            {"consumer_view": {}})
        self.assertTrue(found and "scenario" in found[0], found)


# =====================================================================
# UNDISPOSITIONED
# =====================================================================
class TestUndispositioned(unittest.TestCase):

    def test_GEN_UND_01_no_premise_means_undispositioned(self):
        grid = rows(joints=(), constraints=(), irrelevance=())
        self.assertEqual({"UNDISPOSITIONED"}, {r["disposition"] for r in grid})
        for r in grid:
            self.assertTrue(r["missing"].strip(),
                            "a cell said nothing about what is missing")

    def test_GEN_UND_02_unrelated_premises_do_not_change_it(self):
        before = rows(joints=(), constraints=(), irrelevance=())
        after = rows(joints=[dict(JOINT, child_group="RGP-ELSEWHERE")],
                     constraints=[dict(RELATION, retained_group="RGP-ELSEWHERE")],
                     irrelevance=[dict(IRRELEVANCE, rigid_group="RGP-ELSEWHERE")])
        self.assertEqual([r["disposition"] for r in before],
                         [r["disposition"] for r in after])

    def test_GEN_UND_03_no_absence_path_reaches_a_retired_disposition(self):
        """Exhaustive over the shapes that used to trigger the else branch."""
        for joints in ((), (JOINT,), (dict(JOINT, joint_type="FIXED",
                                           axis_direction="NONE"),)):
            grid = rows(joints=joints, constraints=(), irrelevance=())
            self.assertNotIn("MAINTAINED_BY_CLASS",
                             {r["disposition"] for r in grid})
            self.assertTrue({r["disposition"] for r in grid}
                            <= set(s03.DISPOSITIONS))

    def test_GEN_UND_04_completeness_counts_what_rests_on_evidence(self):
        report = s03.disposition_completeness(rows())
        self.assertEqual(len(GROUPS) * len(CONFIGS) * len(DOF_NAMES),
                         report["domain_cells"])
        # RZ intended in both configurations, one blocked cell, one irrelevant.
        self.assertEqual(4, report["dispositioned_by_evidence"])
        self.assertEqual(report["domain_cells"] - 4, report["undispositioned"])
        self.assertIn("RGP-Q/CFG-2/TZ", report["cells_without_evidence"])


# =====================================================================
# BRANCH GENERALITY AND THE CANONICAL PROBE
# =====================================================================
def _s03a(suffix, groups=("P", "Q")):
    return {
        "bodies": [{"id": "BOD-%s%s" % (g, suffix), "instance_identity": "link",
                    "role": "STRUCTURE"} for g in groups],
        "rigid_groups": [{"id": "RGP-%s%s" % (g, suffix),
                          "body": "BOD-%s%s" % (g, suffix),
                          "members": ["BOD-%s%s" % (g, suffix)]} for g in groups],
        "interfaces": [{"id": "IFC-%s" % suffix, "bodies": ["BOD-P%s" % suffix],
                        "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"},
                       {"id": "IFG-%s" % suffix, "bodies": ["BOD-Q%s" % suffix],
                        "interaction_kind": "CONTACT", "nominal_status": "NOMINAL"}],
        "joints": [{"id": "JNT-%s" % suffix, "joint_type": "REVOLUTE",
                    "parent_group": "RGP-P%s" % suffix,
                    "child_group": "RGP-Q%s" % suffix, "dof": ["RZ"],
                    "axis_direction": "+Z", "frame_ids": ["F1"]}],
        "configurations": [
            {"id": "CFG-1%s" % suffix, "name": "open", "kind": "OPERATIONAL",
             "bodies_present": ["BOD-P%s" % suffix], "expected_mobility": []},
            {"id": "CFG-2%s" % suffix, "name": "shut", "kind": "OPERATIONAL",
             "bodies_present": ["BOD-P%s" % suffix], "expected_mobility": []}],
    }


def _s03b(suffix):
    return {
        "physical_interactions": [
            {"id": "PHI-%s" % suffix, "groups": ["RGP-P%s" % suffix],
             "effect": "TRANSMIT_FORCE", "discharges_effect": "PEO-0001",
             "at_interface": "IFC-%s" % suffix,
             "configurations": ["CFG-1%s" % suffix]}],
        "constraint_relations": [
            {"id": "CRL-%s" % suffix, "retained_group": "RGP-Q%s" % suffix,
             "blocked_dofs": ["TZ"], "configurations": ["CFG-1%s" % suffix],
             "driver": "LOAD", "blocked_direction": "+Z",
             "defeat_specification": "push it back",
             "provider_reaction_site": "RSR-0001",
             "provider_site": "IFG-%s" % suffix,
             "maintaining_interaction": "PHI-%s" % suffix}],
        # ONE justified irrelevance, in a scenario that carries no load case.
        "irrelevance": [{"rigid_group": "RGP-P%s" % suffix,
                         "configuration": "CFG-2%s" % suffix,
                         "dof": ["TX"], "scenario": "SCN-IDLE"}],
        "load_paths": [
            {"id": "LDP-%s" % suffix, "load_case": "LC-0001",
             "candidate": "CND-%s" % suffix,
             "ordered_hops": ["IFC-%s" % suffix, "IFG-%s" % suffix],
             "terminates_at": "RSR-0001"}],
        "assembly_steps": [
            {"id": "ASY-%s" % suffix, "order_index": 1,
             "body": "BOD-P%s" % suffix, "access_side": "+Z", "activates": [],
             "termination_strategy": "NONE", "path_kind": "RIGID",
             "depends_on": []}],
        "unresolved": [],
    }


class TestCanonicalProbe(_fixtures.StateBuilder, unittest.TestCase):
    """Two groups, two configurations, one joint, one relation, one justified
    irrelevance and cells nothing covers - through the real invocation path.

    Nothing is seeded that a producer should make. MobilityExpectation in
    particular is never written by the test.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def chain(self, suffixes=("A",)):
        s = DesignState(run_id="probe")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        # A second scenario that carries NO load case. Without one, an honest
        # irrelevance claim has nothing it could name.
        self.add(s, "s01", "Scenario", "SCN-IDLE", actors=["ACT-0001"])
        payloads = [S02]
        for suffix in suffixes:
            payloads += [_s03a(suffix), _s03b(suffix)]
        provider = _Canned(*payloads)
        s.apply(S02ObligationAndCandidates().invoke(provider, s, s.run_id).patch)
        outs = {}
        for suffix in suffixes:
            inv = cv.InvocationContext(branch="CND-%s" % suffix)
            s.apply(S03TopologyAndMobility().invoke(
                provider, s, s.run_id,
                {"candidate": {"entity_id": "CND-%s" % suffix}},
                invocation=inv).patch)
            out = S03BMobilityAndAssembly().invoke(
                provider, s, s.run_id, {"candidate": "CND-%s" % suffix},
                attempt=2, invocation=inv)
            self.assertIsNotNone(out.patch, out.problems)
            s.apply(out.patch)
            outs[suffix] = (out, inv)
        return s, outs

    def cells(self, s):
        return [d for m in s.family("MobilityExpectation") for d in m["dispositions"]]

    def test_PROBE_01_the_domain_is_deterministic_and_total(self):
        s, _ = self.chain()
        cells = self.cells(s)
        self.assertEqual(2 * 2 * len(DOF_NAMES), len(cells))
        self.assertEqual(len(cells),
                         len({(c["rigid_group"], c["configuration"], c["dof"])
                              for c in cells}))

    def test_PROBE_02_every_disposition_appears_where_its_premise_applies(self):
        s, _ = self.chain()
        by_cell = {(c["rigid_group"], c["configuration"], c["dof"]): c
                   for c in self.cells(s)}
        self.assertEqual("BLOCKED_BY", by_cell[("RGP-QA", "CFG-1A", "TZ")]["disposition"])
        self.assertEqual("CRL-A", by_cell[("RGP-QA", "CFG-1A", "TZ")]["constraint_relation"])
        self.assertEqual("INTENDED", by_cell[("RGP-QA", "CFG-1A", "RZ")]["disposition"])
        self.assertEqual("JNT-A", by_cell[("RGP-QA", "CFG-1A", "RZ")]["by_joint"])
        self.assertEqual("IRRELEVANT_BECAUSE",
                         by_cell[("RGP-PA", "CFG-2A", "TX")]["disposition"])
        self.assertEqual("SCN-IDLE", by_cell[("RGP-PA", "CFG-2A", "TX")]["scenario"])
        self.assertEqual("UNDISPOSITIONED",
                         by_cell[("RGP-QA", "CFG-2A", "TZ")]["disposition"],
                         "a relation scoped to one configuration reached another")

    def test_PROBE_03_every_positive_premise_resolves_to_its_own_family(self):
        s, _ = self.chain()
        field_family = {"constraint_relation": "ConstraintRelation",
                        "by_joint": "Joint", "scenario": "Scenario"}
        seen = set()
        for c in self.cells(s):
            field = s03.PREMISE_FIELD[c["disposition"]]
            if field is None:
                continue
            seen.add(field)
            self.assertEqual(field_family[field], s.stored_family(c[field]),
                             "%s cited a %s" % (field, s.stored_family(c[field])))
        self.assertEqual(set(field_family), seen, "a disposition kind never occurred")

    def test_PROBE_04_no_legacy_shape_and_no_retired_value_survives(self):
        s, _ = self.chain()
        blob = json.dumps(self.cells(s))
        for banned in ("MAINTAINED_BY_CLASS", "holding_class", "blocker_body",
                       "blocking_relation"):
            self.assertNotIn(banned, blob)

    def test_PROBE_05_the_frozen_S4_layer_still_answers_empty(self):
        s, outs = self.chain()
        out, inv = outs["A"]
        view = S03BMobilityAndAssembly().consumer_view(s, inv)
        self.assertEqual([], S03BMobilityAndAssembly()._s4_physical_problems(
            json.loads(out.raw_response), {"consumer_view": view.payload()}),
            "an S-5 correction broke a frozen U5 invariant")

    def test_PROBE_06_the_stage_checks_pass_on_it(self):
        s, _ = self.chain()
        self.assertEqual([], _assurance(s, "mobility_disposition_completeness"))
        self.assertEqual([], _assurance(s, "mobility_cross_premise_consistency"))
        self.assertEqual([], s03.dof_totality_check(s))

    def test_PROBE_07_it_does_not_force_success(self):
        """What the probe reports is recorded, not arranged."""
        s, outs = self.chain()
        out, inv = outs["A"]
        self.assertEqual([], S03BMobilityAndAssembly()._s5_mobility_problems(
            json.loads(out.raw_response), {"consumer_view": {}}))
        self.assertEqual("SUCCESS", out.execution_status.value,
                         out.declared_incompleteness)
        report = s03.disposition_completeness(self.cells(s))
        self.assertLess(report["fraction"], 1.0,
                        "a probe this small should not have full coverage")
        self.assertTrue(report["cells_without_evidence"])

    def test_GEN_BRANCH_01_one_candidates_mobility_holds_no_other_topology(self):
        s, _ = self.chain(("A", "B"))
        for m in s.family("MobilityExpectation"):
            other = "B" if m["configuration"].endswith("A") else "A"
            blob = json.dumps(m["dispositions"])
            for entity in ("RGP-P", "RGP-Q", "CFG-1", "CFG-2", "JNT-", "CRL-"):
                self.assertNotIn(entity + other, blob,
                                 "%s carries %s material" % (m["entity_id"], other))

    def test_GEN_BRANCH_02_both_candidates_realize_one_demand_independently(self):
        s, _ = self.chain(("A", "B"))
        self.assertEqual(1, len(s.family("PhysicalEffectObligation")))
        self.assertEqual(1, len(s.family("ReactionSiteRequirement")))
        configs = {m["configuration"] for m in s.family("MobilityExpectation")}
        self.assertEqual({"CFG-1A", "CFG-2A", "CFG-1B", "CFG-2B"}, configs,
                         "the second candidate's mobility collided or vanished")
        for suffix in ("A", "B"):
            mine = [c for m in s.family("MobilityExpectation")
                    if m["configuration"].endswith(suffix)
                    for c in m["dispositions"]]
            self.assertEqual(2 * 2 * len(DOF_NAMES), len(mine), suffix)


if __name__ == "__main__":
    unittest.main()
