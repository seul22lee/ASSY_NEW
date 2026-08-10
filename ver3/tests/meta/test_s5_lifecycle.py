"""One mobility lifecycle: domain, dispositions, dependency and validity.

    CURRENT MOBILITY
      = deterministic domain from CURRENT branch topology
      + dispositions backed by explicit sufficient premises

and CURRENT means STANDING.

The repeated S-5 failures had one shape. The architecture splits mobility into a
DERIVED domain and an AUTHORITATIVE disposition, but the runtime reconstructed
"current mobility" through four paths that did not agree: the producer worked
from a standing-only ConsumerView, the domain checker took every record ever
written, dependency covered the dispositions and not the topology they address,
and family-level authority said AUTHORITATIVE for the whole entity while the
contract described half of it as derived. Each pass fixed one path and the next
one surfaced.

These cases hold the lifecycle as one property: change any premise of a branch's
current mobility and exactly that branch's current mobility responds.
"""
from __future__ import annotations

import inspect
import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    DOF_NAMES, S03BMobilityAndAssembly, current_dof_domain,
    current_mobility_cells, dof_totality_check)
from ver3.assy_v3.state.design_state import AuthorityClass, Contracts   # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s5_branch_and_premise import _Chain                          # noqa: E402

CELLS = len(DOF_NAMES)


class _Lifecycle(_Chain):
    """Generic branches. No naming logic reaches production; the helpers below
    read entity ids only to say which fixture entity a case is about."""

    def domain(self, state):
        return set(current_dof_domain(state))

    def groups_in(self, state):
        return {g for g, _c, _d in self.domain(state)}

    def configs_in(self, state):
        return {c for _g, c, _d in self.domain(state)}

    def validity(self, state, eid):
        return state.entities[eid].get("_validity")


# =====================================================================
# L1..L2 - the domain is what production built
# =====================================================================
class TestDomainAgreesWithProduction(_Lifecycle):

    def test_L1_current_domain_equals_the_produced_mobility_domain(self):
        """One branch, clean. The producer and the checker enumerate the same
        cells through the same function - `dof_domain` - one applied to the
        invocation's view and one to standing branch topology."""
        state, outs = self.build([("A", 2, 2)])
        produced = {(d["rigid_group"], d["configuration"], d["dof"])
                    for d in current_mobility_cells(state)}
        self.assertEqual(2 * 2 * CELLS, len(produced))
        self.assertEqual(self.domain(state), produced)
        self.assertEqual([], dof_totality_check(state))

    def test_L2_multiple_unequal_branches_union_their_domains(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3), ("C", 3, 1)])
        self.assertEqual((4 + 3 + 3) * CELLS, len(self.domain(state)))
        produced = {(d["rigid_group"], d["configuration"], d["dof"])
                    for d in current_mobility_cells(state)}
        self.assertEqual(self.domain(state), produced)
        self.assertEqual([], dof_totality_check(state))


# =====================================================================
# L3..L4 - a DOMAIN premise changes: the cells themselves move
# =====================================================================
class TestDomainPremiseChanges(_Lifecycle):

    def test_L3_invalidating_a_rigid_group_removes_its_cells(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        before = len(self.domain(state))
        self.revise(state, Op("INVALIDATE", "RigidGroup", "RGP-G1A", {}, "test",
                              reason="the group was dropped"))
        self.assertNotIn("RGP-G1A", self.groups_in(state),
                         "a withdrawn group still defines current cells")
        self.assertEqual(before - 2 * CELLS, len(self.domain(state)))
        # Both grids of branch A carried its cells, so both lose standing.
        for eid in ("MEX-CFG-C0A", "MEX-CFG-C1A"):
            self.assertEqual("STALE", self.validity(state, eid), eid)
        # The other branch is untouched, in domain and in validity.
        self.assertEqual(1 * 3 * CELLS,
                         len([c for c in self.domain(state) if c[0].endswith("B")]))
        for eid in ("MEX-CFG-C0B", "MEX-CFG-C1B", "MEX-CFG-C2B"):
            self.assertEqual("STANDING", self.validity(state, eid), eid)

    def test_L3b_totality_is_quiet_afterwards_because_both_sides_moved(self):
        """The grids that described the withdrawn group stopped being current at
        the same moment its cells did. Neither side is checked against the
        other's currentness."""
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        self.revise(state, Op("INVALIDATE", "RigidGroup", "RGP-G1A", {}, "test",
                              reason="dropped"))
        # Branch A's grids are stale, so A contributes no current coverage - and
        # A's remaining group still has a current domain, which is a REAL gap.
        found = dof_totality_check(state)
        self.assertTrue(all("RGP-G1A" not in p for p in found),
                        "the withdrawn group is still being demanded: %s" % found)
        self.assertTrue(any("RGP-G0A" in p for p in found),
                        "branch A's surviving group lost its coverage and nothing "
                        "said so: %s" % found)

    def test_L4_superseding_a_configuration_stales_without_removing(self):
        """SUPERSEDE is not withdrawal. FA-1 retains both values and the entity
        keeps standing, so the configuration is still part of the mechanism -
        what changed is a premise, so the mobility resting on it loses
        unqualified authority. INVALIDATE is the operation that removes it, and
        the next case does that."""
        state, _ = self.build([("A", 2, 2)])
        self.revise(state, Op("SUPERSEDE", "Configuration", "CFG-C1A",
                              {"name": "renamed"}, "test",
                              reason="the state was redefined"))
        self.assertIn("CFG-C1A", self.configs_in(state))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C1A"))
        self.assertEqual("STANDING", self.validity(state, "MEX-CFG-C0A"))

    def test_L4b_invalidating_a_configuration_removes_its_cells(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        before = len(self.domain(state))
        self.revise(state, Op("INVALIDATE", "Configuration", "CFG-C1A", {},
                              "test", reason="the state was dropped"))
        self.assertNotIn("CFG-C1A", self.configs_in(state))
        self.assertEqual(before - 2 * CELLS, len(self.domain(state)))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C1A"))
        self.assertEqual("STANDING", self.validity(state, "MEX-CFG-C0B"))


# =====================================================================
# L5..L7 - a DISPOSITION premise changes: the cells stay, the claim falls
# =====================================================================
class TestDispositionPremiseChanges(_Lifecycle):

    def test_L5_invalidating_a_used_joint_leaves_the_domain_alone(self):
        state, _ = self.build([("A", 2, 2)])
        before = self.domain(state)
        self.revise(state, Op("INVALIDATE", "Joint", "JNT-A", {}, "test",
                              reason="the joint was removed"))
        self.assertEqual(before, self.domain(state),
                         "a disposition premise changed the domain")
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))

    def test_L6_invalidating_a_used_constraint_relation_does_the_same(self):
        state, _ = self.build([("A", 2, 2)])
        before = self.domain(state)
        self.revise(state, Op("INVALIDATE", "ConstraintRelation", "CRL-0A", {},
                              "test", reason="the provider was withdrawn"))
        self.assertEqual(before, self.domain(state))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))

    def test_L6b_the_bounded_scenario_premise_behaves_the_same_way(self):
        state, _ = self.build([("A", 2, 2)])
        before = self.domain(state)
        self.revise(state, Op("INVALIDATE", "Scenario", "SCN-IDLE", {}, "test",
                              reason="the scenario was withdrawn"))
        self.assertEqual(before, self.domain(state))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))

    def test_L7_an_unrelated_premise_changes_nothing(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        before = self.domain(state)
        for op in (Op("INVALIDATE", "ConstraintRelation", "CRL-0B", {}, "test",
                      reason="another branch"),
                   Op("INVALIDATE", "Joint", "JNT-B", {}, "test",
                      reason="another branch")):
            self.revise(state, op)
        self.assertEqual(before, self.domain(state),
                         "another branch's revision moved this branch's cells")
        for eid in ("MEX-CFG-C0A", "MEX-CFG-C1A"):
            self.assertEqual("STANDING", self.validity(state, eid), eid)


# =====================================================================
# L8..L10 - current coverage is current, and still sees a real gap
# =====================================================================
class TestCurrentCoverage(_Lifecycle):

    def test_L8_a_stale_grid_is_not_current_coverage(self):
        """The one that lets a design keep credit for what it dropped."""
        state, _ = self.build([("A", 2, 2)])
        self.assertEqual([], dof_totality_check(state))
        self.revise(state, Op("INVALIDATE", "Joint", "JNT-A", {}, "test",
                              reason="a disposition premise, so the domain stays"))
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))
        self.assertEqual(2 * 2 * CELLS, len(self.domain(state)),
                         "the domain moved when only a disposition premise did")
        self.assertEqual([], [c for c in current_mobility_cells(state)
                              if c["configuration"] == "CFG-C0A"],
                         "a stale grid is still being counted as current")
        found = dof_totality_check(state)
        self.assertTrue(any("CFG-C0A" in p for p in found),
                        "coverage lost with the stale grid was not reported: %s"
                        % found)

    def test_L9_a_genuinely_missing_current_cell_is_still_detected(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        mex = self.mex_for(state, "CFG-C0A")
        dropped = mex["dispositions"][0]
        self.revise(state, Op(
            "SUPERSEDE", "MobilityExpectation", mex["entity_id"],
            {"dispositions": mex["dispositions"][1:]}, "test",
            reason="drop one real cell"))
        found = dof_totality_check(state)
        self.assertEqual(1, len(found), found)
        for part in (dropped["rigid_group"], dropped["configuration"],
                     dropped["dof"]):
            self.assertIn(part, found[0])

    def test_L10_an_artificial_cross_branch_cell_is_out_of_domain(self):
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        mex = self.mex_for(state, "CFG-C0A")
        crossed = dict(mex["dispositions"][0])
        crossed["configuration"] = "CFG-C0B"
        self.revise(state, Op(
            "SUPERSEDE", "MobilityExpectation", mex["entity_id"],
            {"dispositions": mex["dispositions"] + [crossed]}, "test",
            reason="a cell belonging to no mechanism"))
        self.assertTrue(any("DOF_DISPOSITION_OUT_OF_DOMAIN" in p
                            for p in dof_totality_check(state)))


# =====================================================================
# L11 - the branch itself is withdrawn
# =====================================================================
class TestCandidateWithdrawal(_Lifecycle):

    def test_L11_withdrawing_a_candidate_withdraws_its_mobility_only(self):
        """Nothing here knows what a candidate is called. Invalidating it stales
        everything authored to embody it - which is the invocation premise every
        s03 record already carried - and standing-only currentness does the
        rest."""
        state, _ = self.build([("A", 2, 2), ("B", 1, 3)])
        self.revise(state, Op("INVALIDATE", "Candidate", "CND-A", {}, "test",
                              reason="the alternative was dropped"))
        self.assertEqual({"RGP-G0B"}, self.groups_in(state),
                         "the withdrawn branch still defines current cells")
        self.assertEqual(1 * 3 * CELLS, len(self.domain(state)))
        for eid in ("MEX-CFG-C0A", "MEX-CFG-C1A"):
            self.assertNotEqual("STANDING", self.validity(state, eid), eid)
        for eid in ("MEX-CFG-C0B", "MEX-CFG-C1B", "MEX-CFG-C2B"):
            self.assertEqual("STANDING", self.validity(state, eid), eid)
        self.assertEqual([], dof_totality_check(state),
                         "the surviving branch was disturbed")


# =====================================================================
# THE ROOT-CAUSE AUDIT, as assertions
# =====================================================================
class TestRootCauseAudit(_Lifecycle):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_AUDIT_1_there_is_one_executable_definition_of_the_domain(self):
        """Every reader goes through `current_dof_domain`, and it goes through
        `dof_domain`. No second formula."""
        readers = (s03.dof_totality_check, s03.current_dof_domain)
        self.assertIn("current_dof_domain",
                      inspect.getsource(s03.dof_totality_check))
        self.assertIn("dof_domain(", inspect.getsource(s03.current_dof_domain))
        module = inspect.getsource(s03)
        # The enumeration expression exists once, inside `dof_domain`.
        self.assertEqual(1, module.count("for d in DOF_NAMES]"),
                         "a second domain formula was written somewhere")

    def test_AUDIT_2_it_uses_standing_topology_only(self):
        src = inspect.getsource(s03.current_dof_domain)
        self.assertIn('state.standing("RigidGroup")', src)
        self.assertIn('state.standing("Configuration")', src)
        self.assertNotIn("state.family(", src)

    def test_AUDIT_3_history_cannot_enlarge_the_current_domain(self):
        state, _ = self.build([("A", 2, 2)])
        before = self.domain(state)
        self.revise(state, Op("INVALIDATE", "RigidGroup", "RGP-G1A", {}, "test",
                              reason="dropped"))
        self.assertTrue(state.entities["RGP-G1A"], "history was deleted")
        self.assertLess(len(self.domain(state)), len(before))
        self.assertNotIn("RGP-G1A", self.groups_in(state))

    def test_AUDIT_4_a_stale_grid_cannot_satisfy_current_totality(self):
        src = inspect.getsource(s03.current_mobility_cells)
        self.assertIn('state.standing("MobilityExpectation")', src)
        self.assertIn("current_mobility_cells",
                      inspect.getsource(s03.dof_totality_check))

    def test_AUDIT_5_6_every_grid_carries_both_halves_and_only_those(self):
        state, _ = self.build([("A", 2, 2)], relations=2)
        for mex in state.family("MobilityExpectation"):
            rows = mex["dispositions"]
            domain = set(s03.domain_premises(rows, mex["configuration"]))
            cited = set(s03.cited_premises(rows))
            stored = set(mex["_premises"])
            self.assertTrue(domain <= stored, mex["entity_id"])
            self.assertTrue(cited <= stored, mex["entity_id"])
            # Only those, plus the invocation premise the stage declares.
            self.assertEqual(set(), stored - domain - cited - {"CND-A"},
                             "an entity became a premise without being used")
            for eid in stored:
                self.assertIsNotNone(state.stored_family(eid),
                                     "a premise that resolves to nothing")

    def test_AUDIT_6b_undispositioned_contributes_no_engineering_premise(self):
        state, _ = self.build([("A", 2, 2)], relations=1, irrelevance=False)
        mex = self.mex_for(state, "CFG-C1A")
        undisposed = [d for d in mex["dispositions"]
                      if d["disposition"] == "UNDISPOSITIONED"]
        self.assertTrue(undisposed)
        self.assertEqual([], s03.cited_premises(undisposed))
        # Its cells still have DOMAIN premises: they exist, and that rests on
        # the topology. Existence and evidence are different claims.
        self.assertEqual(sorted({"CFG-C1A", "RGP-G0A", "RGP-G1A"}),
                         s03.domain_premises(undisposed, "CFG-C1A"))

    def test_AUDIT_7_8_the_two_premise_halves_have_different_consequences(self):
        state, _ = self.build([("A", 2, 2)])
        base = self.domain(state)
        self.revise(state, Op("INVALIDATE", "ConstraintRelation", "CRL-0A", {},
                              "test", reason="disposition premise"))
        self.assertEqual(base, self.domain(state), "a disposition premise moved cells")
        self.assertEqual("STALE", self.validity(state, "MEX-CFG-C0A"))

        state2, _ = self.build([("A", 2, 2)])
        self.revise(state2, Op("INVALIDATE", "RigidGroup", "RGP-G1A", {}, "test",
                               reason="domain premise"))
        self.assertLess(len(self.domain(state2)), len(base),
                        "a domain premise did not move cells")

    def test_AUDIT_9_producer_and_checker_share_the_domain(self):
        state, outs = self.build([("A", 2, 2), ("B", 1, 3)])
        for sfx in ("A", "B"):
            out, inv = outs[sfx]
            produced = {(d["rigid_group"], d["configuration"], d["dof"])
                        for op in out.patch.operations
                        if op.entity_type == "MobilityExpectation"
                        for d in op.fields["dispositions"]}
            branch = {c for c in self.domain(state) if c[0].endswith(sfx)}
            self.assertEqual(branch, produced, sfx)

    def test_AUDIT_10_executable_authority_matches_the_contract(self):
        """The declaration and the behaviour say the same thing.

        AUTHORITATIVE, declared on the family rather than defaulted onto it,
        because what this family STORES is dispositions. The derived half is not
        stored, so there is no field claiming a class runtime ignores - and that
        is checked by asking whether one exists.
        """
        me = self.c.families["MobilityExpectation"]
        self.assertEqual("AUTHORITATIVE", me.get("authority_class"),
                         "the class is defaulted, not declared")
        self.assertIs(AuthorityClass.AUTHORITATIVE,
                      self.c.authority_class("MobilityExpectation"))
        self.assertEqual([], [f for f, spec in (me.get("field_semantics") or {}).items()
                              if isinstance(spec, dict) and "authority_class" in spec],
                         "a field declares an authority class runtime does not read")
        split = me["authorship_split"]
        self.assertEqual("DERIVED", split["domain"]["authority_class"])
        self.assertFalse(split["domain"]["stored"],
                         "the derived half is stored inside an authoritative entity")
        self.assertEqual("stages.s03_topology_and_mobility.current_dof_domain",
                         split["domain"]["computed_by"])

    def test_AUDIT_10b_the_domain_is_recomputed_and_not_read_back(self):
        """Behavioural, not a source scan: topology changes with NO write to any
        MobilityExpectation, and the domain follows."""
        state, _ = self.build([("A", 2, 2)])
        before_grids = json.dumps([m["dispositions"]
                                   for m in state.family("MobilityExpectation")],
                                  sort_keys=True)
        before = len(self.domain(state))
        self.revise(state, Op("INVALIDATE", "RigidGroup", "RGP-G1A", {}, "test",
                              reason="dropped"))
        after_grids = json.dumps([m["dispositions"]
                                  for m in state.family("MobilityExpectation")],
                                 sort_keys=True)
        self.assertEqual(before_grids, after_grids,
                         "the stored grids were rewritten")
        self.assertLess(len(self.domain(state)), before,
                        "the domain was read back out of storage")

    def test_AUDIT_no_second_branch_or_currentness_rule(self):
        """`branch_membership` is the ConsumerView's relation, and the mobility
        lifecycle readers all use standing state."""
        self.assertIn("branch_membership", inspect.getsource(s03.current_dof_domain))
        for fn in (s03.dof_totality_check, s03.constraint_disposition_check,
                   s03.irrelevance_check):
            src = inspect.getsource(fn)
            self.assertNotIn('state.family("MobilityExpectation")', src,
                             "%s reads history as current" % fn.__name__)


if __name__ == "__main__":
    unittest.main()
