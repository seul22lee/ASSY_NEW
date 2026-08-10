"""Domain is not disposition, and absence is not evidence.

The audited pipeline had no way to say "nothing is known about this DOF", so it
said "a joint class holds it" - composing a holding class from the first joint
reaching the group, or the literal string "joint class of no joint" when there was
none. A reviewer could not tell an evidenced disposition from a manufactured one.

`UNDISPOSITIONED` is the correction. These tests hold the two facts apart: the
enumerator makes every cell exist (bookkeeping), and only a present, typed,
referenceable premise says anything about one.
"""
from __future__ import annotations

import collections
import inspect
import json
import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    DOF_NAMES, S03BMobilityAndAssembly, derive_mobility)
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402

JOINT = {"entity_id": "JNT-A", "child_group": "RGP-A",
         "joint_type": "REVOLUTE", "axis_direction": "+Z"}
RELATION = {"id": "CRL-A", "retained_group": "RGP-A", "blocked_dofs": ["TZ"],
            "configurations": ["CFG-A"], "driver": "LOAD",
            "provider_body": "BOD-A"}


def _rows(joints=(JOINT,), constraints=(RELATION,), irrelevance=(),
          groups=("RGP-A",), configurations=("CFG-A",)):
    return derive_mobility(list(groups), list(configurations), list(joints),
                           list(constraints), list(irrelevance))


def _cell(rows, group, cfg, dof):
    for r in rows:
        if (r["rigid_group"], r["configuration"], r["dof"]) == (group, cfg, dof):
            return r
    raise AssertionError("cell %s/%s/%s is not in the domain" % (group, cfg, dof))


class TestDomain(unittest.TestCase):
    """S5-DOM. The domain is deterministic, total, and bookkeeping."""

    def test_S5_DOM_01_topology_creates_the_domain(self):
        rows = _rows()
        self.assertEqual(len(DOF_NAMES), len(rows),
                         "one cell per rigid-body DOF, per group, per configuration")
        self.assertEqual({("RGP-A", "CFG-A", d) for d in DOF_NAMES},
                         {(r["rigid_group"], r["configuration"], r["dof"])
                          for r in rows})

    def test_S5_DOM_02_a_constraint_cannot_invent_a_cell(self):
        """A relation naming a group the topology does not have adds nothing.

        The domain comes from the topology. A disposition can only speak about a
        cell that exists.
        """
        rows = _rows(constraints=[dict(RELATION, retained_group="RGP-GHOST")])
        self.assertEqual({"RGP-A"}, {r["rigid_group"] for r in rows})
        self.assertEqual(len(DOF_NAMES), len(rows))

    def test_S5_DOM_03_each_group_gets_its_own_domain(self):
        rows = _rows(groups=("RGP-A", "RGP-B"))
        counts = collections.Counter(r["rigid_group"] for r in rows)
        self.assertEqual({"RGP-A": len(DOF_NAMES), "RGP-B": len(DOF_NAMES)},
                         dict(counts))

    def test_S5_DOM_04_totality_is_bookkeeping_and_says_so(self):
        """It is guaranteed by the enumerator, so it may not be counted as
        assurance. The code has to say that where a reader will see it."""
        src = inspect.getsource(derive_mobility)
        self.assertIn("BOOKKEEPING", src.upper())
        checker = inspect.getsource(s03.dof_totality_check)
        self.assertTrue("BOOKKEEPING" in checker.upper()
                        or "bookkeeping" in checker,
                        "the totality check does not say it is bookkeeping")


class TestDisposition(unittest.TestCase):
    """S5-DISP / S5-INF. Every disposition names its premise, or is UNDISPOSITIONED."""

    def test_S5_DISP_01_a_constraint_relation_disposes_its_dofs(self):
        cell = _cell(_rows(), "RGP-A", "CFG-A", "TZ")
        self.assertEqual("BLOCKED_BY", cell["disposition"])
        self.assertEqual("CRL-A", cell["constraint_relation"],
                         "BLOCKED_BY must cite an addressable ConstraintRelation")

    def test_S5_DISP_01b_a_joint_leaves_its_dof_intended(self):
        cell = _cell(_rows(), "RGP-A", "CFG-A", "RZ")
        self.assertEqual("INTENDED", cell["disposition"])
        self.assertEqual("JNT-A", cell["by_joint"])

    def test_S5_DISP_02_an_uncovered_dof_is_UNDISPOSITIONED(self):
        cell = _cell(_rows(), "RGP-A", "CFG-A", "TX")
        self.assertEqual("UNDISPOSITIONED", cell["disposition"])
        self.assertIn("ConstraintRelation", cell["missing"],
                      "the cell must name what would have covered it")

    def test_S5_DISP_03_INF_01_02_absence_never_becomes_MAINTAINED_BY_CLASS(self):
        """The exact defect S-5 exists to remove.

        With a joint present and nothing covering the other DOFs, the old code
        wrote MAINTAINED_BY_CLASS with a class composed from that joint. With no
        joint at all it wrote "joint class of no joint".
        """
        for joints in ((JOINT,), ()):
            rows = _rows(joints=joints, constraints=())
            dispositions = {r["disposition"] for r in rows}
            self.assertNotIn("MAINTAINED_BY_CLASS", dispositions,
                             "absence produced a class-based disposition")
            self.assertIn("UNDISPOSITIONED", dispositions)
        blob = json.dumps(_rows(joints=(), constraints=()))
        self.assertNotIn("joint class", blob)

    def test_S5_DISP_03b_the_absence_branch_is_deleted_not_reworded(self):
        from .test_s3_interface_readiness import _code_only
        src = _code_only(derive_mobility)     # the CODE; the docstring explains it
        self.assertNotIn("holding_class", src,
                         "the class-from-absence branch is still here")
        self.assertNotIn("joint class of", src)

    def test_S5_DISP_04_a_disposition_cannot_reach_outside_the_domain(self):
        rows = _rows(constraints=[dict(RELATION, blocked_dofs=["TZ", "NOT_A_DOF"])])
        self.assertEqual({d for d in DOF_NAMES}, {r["dof"] for r in rows},
                         "a relation naming a non-DOF widened the domain")

    def test_S5_DISP_05_a_configuration_specific_constraint_stays_there(self):
        rows = _rows(configurations=("CFG-A", "CFG-B"))
        self.assertEqual("BLOCKED_BY", _cell(rows, "RGP-A", "CFG-A", "TZ")["disposition"])
        self.assertEqual("UNDISPOSITIONED",
                         _cell(rows, "RGP-A", "CFG-B", "TZ")["disposition"],
                         "a constraint declared for one configuration governed another")

    def test_S5_DISP_06_a_relation_naming_no_configuration_covers_all(self):
        """`configurations: []` means the relation holds wherever the group is."""
        rows = _rows(constraints=[dict(RELATION, configurations=[])],
                     configurations=("CFG-A", "CFG-B"))
        for cfg in ("CFG-A", "CFG-B"):
            self.assertEqual("BLOCKED_BY", _cell(rows, "RGP-A", cfg, "TZ")["disposition"])

    def test_S5_INF_03_unrelated_entities_do_not_dispose_a_cell(self):
        before = _cell(_rows(), "RGP-A", "CFG-A", "TX")["disposition"]
        after = _cell(_rows(irrelevance=[{"rigid_group": "RGP-OTHER",
                                          "configuration": "CFG-A",
                                          "dof": ["TX"], "scenario": "SCN-1"}]),
                      "RGP-A", "CFG-A", "TX")["disposition"]
        self.assertEqual("UNDISPOSITIONED", before)
        self.assertEqual(before, after, "an unrelated entity dispositioned a cell")

    def test_S5_DISP_07_irrelevance_must_name_its_scenario(self):
        rows = _rows(irrelevance=[{"rigid_group": "RGP-A", "configuration": "CFG-A",
                                   "dof": ["TX"], "scenario": "SCN-1"}])
        cell = _cell(rows, "RGP-A", "CFG-A", "TX")
        self.assertEqual("IRRELEVANT_BECAUSE", cell["disposition"])
        self.assertEqual("SCN-1", cell["scenario"])


class TestCanonicalConstraintInput(unittest.TestCase):
    """S5-CR / S5-LEGACY. The premise is the S-4 physical truth, not the legacy shape."""

    @classmethod
    def setUpClass(cls):
        cls.stage = S03BMobilityAndAssembly()
        cls.source = open(os.path.join(_REPO, "ver3", "assy_v3", "stages",
                                       "s03_topology_and_mobility.py")).read()

    def test_S5_CR_02_a_legacy_blocking_relation_disposes_nothing(self):
        """It has no identity, so BLOCKED_BY could never have cited it."""
        legacy = {"id": "BLK-1", "retained_group": "RGP-A",
                  "blocked_direction": "+Z", "blocker_body": "BOD-A",
                  "configurations": ["CFG-A"], "dofs": ["TZ"], "driver": "LOAD"}
        rows = derive_mobility(["RGP-A"], ["CFG-A"], [JOINT], [legacy], [])
        self.assertEqual("UNDISPOSITIONED",
                        _cell(rows, "RGP-A", "CFG-A", "TZ")["disposition"],
                        "a legacy blocking relation still creates mobility truth")

    def test_S5_LEGACY_01_the_model_is_no_longer_asked_for_it(self):
        prompt = self.stage.prompt({"consumer_view": {}, "candidate": "CND-A"})
        self.assertNotIn("blocking_relations", prompt)
        self.assertIn("constraint_relations[]", prompt)

    def test_S5_LEGACY_02_the_derivation_does_not_read_it(self):
        from .test_s3_interface_readiness import _code_only
        src = _code_only(derive_mobility)
        self.assertNotIn("blocking_relations", src)
        # The legacy key exactly - `blocked_dofs` legitimately contains "_dofs".
        self.assertNotIn("'_dofs'", src, "the legacy dof shape is still read")
        from .test_s3_interface_readiness import _code_only as _c
        derived = _c(S03BMobilityAndAssembly.derived_operations)
        self.assertNotIn("relations_of", derived,
                         "the derivation still parses the legacy channel")

    def test_S5_LEGACY_03_a_response_without_it_derives_normally(self):
        parsed = {"constraint_relations": [RELATION], "irrelevance": []}
        rows = self.stage.derived_operations(
            parsed, ["RGP-A"], ["CFG-A"], [JOINT], {"candidate": "CND-A"})
        self.assertTrue(rows, "no mobility was derived without the legacy channel")
        dispositions = {d["disposition"]
                        for op in rows for d in op.fields["dispositions"]}
        self.assertIn("BLOCKED_BY", dispositions)
        self.assertIn("UNDISPOSITIONED", dispositions)


class TestMobilityCompleteness(unittest.TestCase):
    """The S-5 layer reports evidence problems; it does not repair them."""

    @classmethod
    def setUpClass(cls):
        cls.stage = S03BMobilityAndAssembly()

    def problems(self, entries, relations=(RELATION,)):
        return self.stage._s5_mobility_problems(
            {"constraint_relations": list(relations), "_derived_mobility": entries},
            {"consumer_view": {}})

    def test_an_undispositioned_cell_is_not_an_error(self):
        """It is the honest state. Reporting it is the point of the value."""
        self.assertEqual([], self.problems(
            [{"rigid_group": "RGP-A", "configuration": "CFG-A", "dof": "TX",
              "disposition": "UNDISPOSITIONED", "missing": "nothing covers it"}]))

    def test_a_disposition_whose_premise_does_not_resolve_is_reported(self):
        found = self.problems(
            [{"rigid_group": "RGP-A", "configuration": "CFG-A", "dof": "TZ",
              "disposition": "BLOCKED_BY", "constraint_relation": "CRL-GHOST"}])
        self.assertTrue(found and "CRL-GHOST" in found[0], found)

    def test_a_disposition_citing_nothing_is_reported(self):
        for entry, marker in (
                ({"disposition": "BLOCKED_BY"}, "no premise"),
                ({"disposition": "INTENDED"}, "no joint"),
                ({"disposition": "IRRELEVANT_BECAUSE"}, "no named scenario"),
                ({"disposition": "MAINTAINED_BY_CLASS"}, "no class named")):
            base = {"rigid_group": "RGP-A", "configuration": "CFG-A", "dof": "TX"}
            base.update(entry)
            found = self.problems([base])
            self.assertTrue(found and marker in found[0],
                            "%s: %s" % (entry["disposition"], found))

    def test_it_reports_and_does_not_repair(self):
        entries = [{"rigid_group": "RGP-A", "configuration": "CFG-A", "dof": "TZ",
                    "disposition": "BLOCKED_BY", "constraint_relation": "CRL-GHOST"}]
        before = json.dumps(entries, sort_keys=True)
        self.problems(entries)
        self.assertEqual(before, json.dumps(entries, sort_keys=True))

    def test_MAINTAINED_BY_CLASS_survives_only_when_justified(self):
        """The contract keeps the value; S-5 removes it as an absence default."""
        contracts = Contracts()
        values = contracts.families["MobilityExpectation"]["disposition_values"]
        self.assertIn("MAINTAINED_BY_CLASS", values)
        self.assertIn("UNDISPOSITIONED", values)
        self.assertEqual([], self.problems(
            [{"rigid_group": "RGP-A", "configuration": "CFG-A", "dof": "TX",
              "disposition": "MAINTAINED_BY_CLASS", "holding_class": "REVOLUTE"}]))


class TestS5Metadata(unittest.TestCase):

    def test_S5_META_01_no_active_s5_mobility_migration_row_remains(self):
        with open(os.path.join(_REPO, "ver3", "contracts",
                               "DESIGN_STATE_CONTRACT.yaml")) as fh:
            ds = yaml.safe_load(fh)
        offending = [r.get("concept")
                     for r in (ds.get("legacy_producers") or {}).get("rows") or []
                     if re.search(r"\bS-5\b", str(r.get("migration_step")))]
        self.assertEqual([], offending,
                         "S-5 cannot close while it owns an active migration row: "
                         "%s" % offending)

    def test_S5_META_02_the_history_is_kept(self):
        with open(os.path.join(_REPO, "ver3", "contracts",
                               "DESIGN_STATE_CONTRACT.yaml")) as fh:
            ds = yaml.safe_load(fh)
        superseded = (ds.get("superseded_legacy_producers") or {}).get("rows") or []
        self.assertTrue(any("Mobility" in r["concept"] for r in superseded),
                        "the mobility migration history was deleted, not moved")


if __name__ == "__main__":
    unittest.main()


class TestS4FreezeAndChain(_fixtures.StateBuilder, unittest.TestCase):
    """S5-S4. The physical layer is untouched, and the chain still closes."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def chain(self):
        import ver3.tests.meta.test_s02_s03b_integration as I
        tc = I.TestS02ToS03B("test_INT_01_02_the_demand_is_produced_not_seeded")
        tc.setUpClass()
        return tc, I

    def test_S5_S4_01_02_03_04_the_physical_layer_still_answers_empty(self):
        import ver3.assy_v3.view.consumer_view as cv
        tc, I = self.chain()
        s, provider, invocation = tc.chain()
        view = S03BMobilityAndAssembly().consumer_view(s, invocation)
        out = S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=invocation)
        parsed = json.loads(out.raw_response)
        self.assertEqual([], S03BMobilityAndAssembly()._s4_physical_problems(
            parsed, {"consumer_view": view.payload()}),
            "an S-5 edit broke a frozen U5 invariant")
        s.apply(out.patch)
        self.assertEqual("PEO-0001", s.entities["PHI-A"]["discharges_effect"])
        self.assertEqual("RSR-0001", s.entities["LDP-A"]["terminates_at"])
        self.assertEqual("RSR-0001", s.entities["LC-0001"]["reacted_at_site"])

    def test_S5_S4_05_the_mobility_change_is_confined_to_the_derivation(self):
        """`_s4_physical_problems` is not touched by S-5."""
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S03BMobilityAndAssembly._s4_physical_problems)
        for marker in ("U5-1", "U5-2", "U5-3"):
            self.assertIn(marker, src)
        self.assertNotIn("disposition", src,
                         "the S-4 layer started reasoning about mobility")

    def test_S5_CHAIN_the_probe_derives_mobility_from_its_own_topology(self):
        tc, I = self.chain()
        s, provider, invocation = tc.chain()
        out = S03BMobilityAndAssembly().invoke(
            provider, s, s.run_id, {"candidate": "CND-A"}, attempt=2,
            invocation=invocation)
        s.apply(out.patch)
        parsed = json.loads(out.raw_response)
        ops = S03BMobilityAndAssembly().derived_operations(
            parsed, [g["entity_id"] for g in s.family("RigidGroup")],
            [c["entity_id"] for c in s.family("Configuration")],
            [dict(j) for j in s.family("Joint")], {"candidate": "CND-A"})
        cells = [d for op in ops for d in op.fields["dispositions"]]
        self.assertTrue(cells, "no mobility was derived")
        self.assertEqual({"RGP-A"}, {c["rigid_group"] for c in cells},
                         "candidate B topology entered A's mobility domain")
        blob = json.dumps(cells)
        self.assertNotIn("MAINTAINED_BY_CLASS", blob)
        self.assertIn("UNDISPOSITIONED", blob,
                      "a probe with one constraint should leave cells uncovered")
        for cell in cells:
            if cell["disposition"] == "BLOCKED_BY":
                self.assertIn(cell["constraint_relation"],
                              {r["id"] for r in parsed["constraint_relations"]})

    def test_S5_CHAIN_a_dof_without_disposition_stays_visible(self):
        """The second variant: remove the constraint and nothing fills the gap."""
        tc, I = self.chain()
        s, provider, invocation = tc.chain()
        parsed = json.loads(json.dumps(I._s03b("A")))
        parsed["constraint_relations"] = []
        ops = S03BMobilityAndAssembly().derived_operations(
            parsed, ["RGP-A"], ["CFG-A"], [dict(j) for j in s.family("Joint")],
            {"candidate": "CND-A"})
        cells = [d for op in ops for d in op.fields["dispositions"]]
        self.assertEqual(len(DOF_NAMES), len(cells),
                         "the domain shrank when evidence was removed")
        undispositioned = [c for c in cells if c["disposition"] == "UNDISPOSITIONED"]
        self.assertTrue(undispositioned, "the uncovered cells vanished")
        self.assertNotIn("MAINTAINED_BY_CLASS",
                         {c["disposition"] for c in cells})
        completeness = s03.disposition_completeness(cells)
        self.assertEqual(len(DOF_NAMES), completeness["domain_cells"])
        self.assertTrue(completeness["cells_without_evidence"])
        self.assertLess(completeness["fraction"], 1.0)
