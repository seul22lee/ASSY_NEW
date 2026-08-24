"""UNIT C: AN UPSTREAM AUTHORING DEFECT IS REPAIRED BY ITS OWNER, AND EVERYTHING
THAT RESTED ON THE OLD FACT IS REBUILT FROM CURRENT PREMISES - BOUNDED.

    check -> route OWNER_REVISION to its owner -> the owner revises
          -> rebuild downstream (s03b, s04a, s04b, the s04 repair loop)
          -> re-check

The check is the feasibility responsibility answering again over current
state; the routing is the owner the contract's classification names for the
finding; the revision is that pass revising the fact it authored through the
boundary's own operations; the rebuild is every downstream realization
realized again from the mechanism as it now stands; the re-check is the same
evaluator again. The loop applies the owners' patches and records what
happened. It owns no truth and decides nothing.

WHAT THESE TESTS ARE GUARDING

    An s03a finding reaches s03a and only s03a; an s03b finding reaches s03b
    and only s03b; no other class enters the loop.

    A revision is canonical - SUPERSEDE with the reason, history kept - and
    what rested on the revised fact goes stale by ordinary propagation.

    S04 is realized again from the revised branch, and repaired where
    repairable, before any feasibility is offered.

    Bounded and honest: a cycle, an exhausted budget, a refused or escalated
    revision, an invocation that did not land, and an absent provider each
    leave an open obligation and never INFEASIBLE; nothing asks twice and
    keeps the better answer.

    One candidate's revision touches no other candidate; the architecture,
    the principle and the candidate cannot be silently replaced; selection
    and human authority are untouched.

Synthetic mechanisms throughout. No product noun, no benchmark id.
"""
from __future__ import annotations

import copy
import inspect
import json
import re
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.pipeline import owner_revision as own                # noqa: E402
from ver3.assy_v3.pipeline import progression                          # noqa: E402
from ver3.assy_v3.pipeline import repair                               # noqa: E402
from ver3.assy_v3.stages import base                                   # noqa: E402
from ver3.assy_v3.stages.base import (CAUSE_UPSTREAM_REVISION, REPAIR_KEY,  # noqa: E402
                                      revise_standing_operations)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from ver3.assy_v3.view import InvocationContext                         # noqa: E402
from .test_s02_s03b_integration import _Canned                          # noqa: E402
from .test_s04_mating_geometry import _Mating, geometry                 # noqa: E402
from .test_s04_repair_loop import APART, _Recording, _Refusing          # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, topology)
from .test_s7_human_decision import _code                               # noqa: E402
from .test_s7_mfa_viability import chain_probe                          # noqa: E402
from .test_s7_transition_reachability import evidence, restraint        # noqa: E402

REGION = "REGION_WITHOUT_OWNER"
RELEASE = "RELEASE_RELATION_NOT_APPLICABLE"
FAMILIES_S03 = ("Body", "RigidGroup", "Joint", "Interface", "Configuration",
                "FunctionalRegion", "ConstraintRelation", "PhysicalInteraction",
                "LoadPath", "AssemblyStep", "TransitionRequirement", "MobilityExpectation")


def region_topology(owners=(), **kw):
    """A hinge whose KEEP_OUT region names the owners given - none by default,
    which is the s03a authoring defect the gross-interference domain reports
    as REGION_WITHOUT_OWNER and the contract classifies as s03a's to revise."""
    t = topology("A", 2, [(0, 1)], **kw)
    t["functional_regions"] = [{"id": "FRG-A", "role": "KEEP_OUT",
                                "owning_bodies": list(owners),
                                "required_by_actors": [], "reach_targets": []}]
    return t


def placed(boxes=HINGE_BOXES):
    return arrangement(boxes, steps=["ASY-0A"], region="FRG-A")


def released(blocks=(("JNT-0A", "TX"),)):
    """s03b evidence whose demand releases a restraint that restrains some
    OTHER motion than the one demanded: RELEASE_RELATION_NOT_APPLICABLE, an
    s03b bookkeeping fact its owner may revise."""
    return evidence(releases=["CRL-0A"], relations=[restraint(blocks=list(blocks))])


class _Own(_Feas):

    def inv(self, sfx="A"):
        return InvocationContext(branch="CND-%s" % sfx)

    def loop(self, state, provider, rounds=2, sfx="A", repair_rounds=2):
        p = progression.Progression()
        out = own.s03_owner_revision_rounds(provider, state, p, self.inv(sfx),
                                            rounds=rounds, repair_rounds=repair_rounds)
        return out, p

    def current_mfa(self, state, cid="CND-A"):
        found = [m for m in state.standing("MechanicalFeasibilityAssessment")
                 if m.get("candidate") == cid]
        self.assertEqual(1, len(found), found)
        return found[0]

    def owner_rows(self, state, cid="CND-A"):
        out = s07.evaluate_candidate_feasibility(state, cid)
        return sorted((r["domain"], r["code"], r["owner"]) for v in out.verdicts
                      for r in s07.classify(v)[0] if r["class"] == s07.OWNER_REVISION)

    def region(self, owners=(), **kw):
        return self.hinge(s03a=region_topology(owners, **kw), s04a=placed())

    def release(self):
        return self.hinge(s03b=released())

    def snapshot(self, state, families=FAMILIES_S03, prefix=None):
        return {e: json.dumps(r, sort_keys=True, default=str)
                for e, r in state.entities.items()
                if r["_family"] in families and (prefix is None or e.startswith(prefix))}

    #: The recorded answers a settled region revision needs, in order: s03a
    #: revised, then the rebuild - s03b, s04a, s04b.
    def region_fix(self, boxes=HINGE_BOXES):
        return (region_topology(["BOD-G0A"]), realization("A"), placed(boxes),
                motion("A", "JNT-0A", _group(1, "A")))


# =====================================================================
# 1 - routing: each finding reaches its owner, and only its owner
# =====================================================================
class TestRouting(_Own):

    def test_an_s03a_finding_routes_only_to_s03a(self):
        state = self.region()
        self.assertEqual([("gross_interference", REGION, "s03a")], self.owner_rows(state))
        provider = _Recording(*self.region_fix())
        out, p = self.loop(state, provider)
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual((("s03a", REGION),), out.rounds[0].routed)
        self.assertEqual("s03a", out.rounds[0].invoked[0])
        self.assertIn("OWNER REVISION ROUND 1", provider.prompts[0])
        self.assertIn(REGION, provider.prompts[0])
        self.assertIn("WHAT YOU MAY NOT DO", provider.prompts[0])
        # s03b was re-authored because s03a revised, and was given no finding
        # of its own to answer
        own_findings = provider.prompts[1].split("WHAT CHANGED UPSTREAM")[0]
        self.assertNotIn("OWNER REVISION ROUND", own_findings)
        self.assertEqual(["s03a", "s03b", "s04a", "s04b"],
                         [e.responsibility_id for e in p.executions])

    def test_an_s03b_finding_routes_only_to_s03b(self):
        state = self.release()
        self.assertEqual([("transition_reachability", RELEASE, "s03b")],
                         self.owner_rows(state))
        provider = _Recording(released([("JNT-0A", "RZ")]), placed(),
                              motion("A", "JNT-0A", _group(1, "A")))
        out, p = self.loop(state, provider)
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual((("s03b", RELEASE),), out.rounds[0].routed)
        self.assertEqual(("s03b",), out.rounds[0].invoked)
        self.assertIn("OWNER REVISION ROUND 1", provider.prompts[0])
        self.assertIn(RELEASE, provider.prompts[0])
        self.assertNotIn("WHAT CHANGED UPSTREAM", provider.prompts[0])
        self.assertNotIn("s03a", [e.responsibility_id for e in p.executions])

    def test_each_finding_reaches_its_owner_and_not_the_other(self):
        state = self.hinge(s03a=region_topology(), s03b=released(), s04a=placed())
        self.assertEqual([("gross_interference", REGION, "s03a"),
                          ("transition_reachability", RELEASE, "s03b")],
                         self.owner_rows(state))
        provider = _Recording(region_topology(["BOD-G0A"]), released([("JNT-0A", "RZ")]),
                              placed(), motion("A", "JNT-0A", _group(1, "A")))
        out, _p = self.loop(state, provider)
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual((("s03a", REGION), ("s03b", RELEASE)), out.rounds[0].routed)
        self.assertEqual(("s03a", "s03b"), out.rounds[0].invoked)
        a, b = provider.prompts[0], provider.prompts[1]
        self.assertIn(REGION, a)
        self.assertNotIn(RELEASE, a)
        b_own = b.split("WHAT CHANGED UPSTREAM")[0]
        self.assertIn(RELEASE, b_own)
        self.assertNotIn(REGION, b_own)
        self.assertIn(REGION, b.split("WHAT CHANGED UPSTREAM")[1])

    def test_other_classes_do_not_trigger_the_loop(self):
        """Repairable (s04's), unsupported (nobody's) and required-minimum
        (no revision may invent it) findings: the loop finds nothing to
        route, asks nobody, and settles."""
        for name, state in (("repairable", self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                                                        eliminated=True))),
                            ("unsupported", chain_probe(self)),
                            ("required_minimum", self.hinge(s03b=realization("A", terminates=None)))):
            with self.subTest(name):
                self.assertEqual([], self.owner_rows(state))
                before = self.snapshot(state)
                provider = _Refusing()
                out, _p = self.loop(state, provider)
                self.assertEqual(own.SETTLED, out.status, out.as_record())
                self.assertEqual(0, provider.calls)
                self.assertEqual([], out.rounds)
                self.assertEqual(before, self.snapshot(state))

    def test_the_trigger_is_the_class_and_the_owner_never_the_status(self):
        source = _code(inspect.getsource(own._owner_findings))
        self.assertIn("== OWNER_REVISION", source)
        self.assertIn("S03_OWNERS", source)
        for word in ("FEASIBLE_FOR_SELECTION", "NOT_ESTABLISHED", "INFEASIBLE",
                     "v.status", "blocking_findings", "open_obligations", "summary"):
            self.assertNotIn(word, source, word)
        self.assertEqual("OWNER_REVISION", own.OWNER_REVISION)
        self.assertEqual(("s03a", "s03b"), own.S03_OWNERS)

    def test_a_finding_owned_by_a_later_stage_is_reported_unrouted(self):
        rows = [{"domain": "d", "code": "A", "class": "OWNER_REVISION", "owner": "s03a"},
                {"domain": "d", "code": "B", "class": "OWNER_REVISION", "owner": "s06"},
                {"domain": "d", "code": "C", "class": "REPAIRABLE_S04", "owner": "s04a"}]
        real = own.classified_findings
        own.classified_findings = lambda *_a, **_k: ("FEASIBLE_FOR_SELECTION", rows)
        try:
            status, routed, unrouted = own._owner_findings(None, None, "x")
        finally:
            own.classified_findings = real
        self.assertEqual(["A"], [r["code"] for r in routed])
        self.assertEqual(["B"], [r["code"] for r in unrouted])
        # and the contract does classify such codes, so the split is not idle
        later = {code for code, spec in s07.classification()["codes"].items()
                 if spec.get("class") == "OWNER_REVISION"
                 and spec.get("owner") not in own.S03_OWNERS}
        self.assertTrue(later, "no later-owned OWNER_REVISION code in the contract")


class TestDeferredDoesNotTrigger(_Mating):

    def test_a_deferred_obligation_is_not_an_owner_revision(self):
        state = self.pin(geometry())
        p = progression.Progression()
        provider = _Refusing()
        out = own.s03_owner_revision_rounds(provider, state, p,
                                            InvocationContext(branch="CND-A"), rounds=2)
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual(0, provider.calls)


# =====================================================================
# 2 - the revision, what it stales, and what is rebuilt from it
# =====================================================================
class TestRevisionAndRebuild(_Own):

    def test_the_owner_revises_canonically_and_history_is_kept(self):
        state = self.region()
        ids_before = set(state.entities)
        untouched = self.snapshot(state, ("Body", "RigidGroup", "Joint", "Interface",
                                          "Configuration", "Candidate"))
        out, _p = self.loop(state, _Canned(*self.region_fix()))
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        region = state.entities["FRG-A"]
        self.assertEqual("STANDING", region["_validity"])
        self.assertEqual(["BOD-G0A"], region["owning_bodies"])
        self.assertEqual(1, len(region["_superseded"]))
        self.assertEqual([], region["_superseded"][0]["prior_value"])
        self.assertEqual("s03", region["_superseded"][0]["stage"])
        self.assertIn("s03a owner revision round 1", region["_superseded"][0]["reason"])
        self.assertIn(REGION, region["_superseded"][0]["reason"])
        # nothing deleted, and nothing the revision did not need to touch moved
        self.assertTrue(ids_before <= set(state.entities))
        self.assertEqual(untouched, {e: self.snapshot(state)[e] if e in self.snapshot(state)
                                     else json.dumps(state.entities[e], sort_keys=True, default=str)
                                     for e in untouched})

    def test_changed_s03_premises_stale_dependent_evidence_by_ordinary_propagation(self):
        """The s03a pass revises a joint's axis through the boundary. The
        states realized in that joint's coordinate, the transition between
        them and its occupancy, and the domain records decided from the joint
        lose standing by propagation - nobody marks them by hand."""
        state = self.hinge()
        self.assess(state)
        # what rests on the joint directly, and what rests on that
        direct = {e for e, r in state.entities.items()
                  if "JNT-0A" in (r.get("_premises") or []) and r["_validity"] == "STANDING"}
        dependent = set(direct)
        grew = True
        while grew:
            more = {e for e, r in state.entities.items()
                    if set(r.get("_premises") or []) & dependent and r["_validity"] == "STANDING"}
            grew = not (more <= dependent)
            dependent |= more
        families = {state.entities[e]["_family"] for e in dependent}
        self.assertTrue({"State", "Transition", "SweptVolume", "MobilityExpectation",
                         "FeasibilityDomainAssessment", "MechanicalFeasibilityAssessment"}
                        <= families, families)
        old = dependent
        context = own._context(state, "CND-A", "s03a", 1,
                               [{"domain": "motion_and_transitions", "code": "JOINT_AXIS_UNUSABLE",
                                 "class": "OWNER_REVISION", "owner": "s03a",
                                 "premises": ["JNT-0A"]}], [], base.CAUSE_FINDINGS)
        outcome = S03TopologyAndMobility().invoke(
            _Canned(topology("A", 2, [(0, 1)], axis="+X")), state, state.run_id,
            own._inputs(state, "CND-A", "s03a", context), attempt=21, invocation=self.inv())
        self.assertIsNotNone(outcome.patch, outcome.problems)
        self.assertEqual([("SUPERSEDE", "JNT-0A", ["axis_direction"])],
                         [(o.kind, o.entity_id, sorted(o.fields)) for o in outcome.patch.operations])
        state.apply(outcome.patch)
        self.assertEqual("+X", state.entities["JNT-0A"]["axis_direction"])
        self.assertEqual("STANDING", state.entities["JNT-0A"]["_validity"])
        self.assertEqual("+Z", state.entities["JNT-0A"]["_superseded"][0]["prior_value"])
        for eid in sorted(old):
            with self.subTest(eid):
                self.assertEqual("STALE", state.entities[eid]["_validity"])
                self.assertEqual("JNT-0A", state.entities[eid]["_stale_because"][0]["root"])
        # and what does not rest on the joint keeps standing: the region, the
        # bodies, the envelopes
        for eid in ("BOD-G0A", "ENV-G0A", "ENV-G1A", "CFG-C0A"):
            self.assertEqual("STANDING", state.entities[eid]["_validity"], eid)

    def test_a_region_owner_revision_stales_the_domain_record_decided_over_it(self):
        state = self.region()
        self.assess(state)
        fda = [d for d in state.standing("FeasibilityDomainAssessment")
               if d["domain"] == "gross_interference"][0]
        self.assertIn(REGION, fda["reason_codes"])
        mfa = self.current_mfa(state)
        rows = [r for r in self.owner_rows(state)]
        context = own._context(state, "CND-A", "s03a", 1,
                               [{"domain": d, "code": c, "class": "OWNER_REVISION",
                                 "owner": o, "premises": ["FRG-A"]} for d, c, o in rows],
                               [], base.CAUSE_FINDINGS)
        outcome = S03TopologyAndMobility().invoke(
            _Canned(region_topology(["BOD-G0A"])), state, state.run_id,
            own._inputs(state, "CND-A", "s03a", context), attempt=21, invocation=self.inv())
        state.apply(outcome.patch)
        self.assertEqual("STALE", state.entities[fda["entity_id"]]["_validity"])
        self.assertEqual("STALE", state.entities[mfa["entity_id"]]["_validity"])
        self.assertEqual("FRG-A", state.entities[mfa["entity_id"]]["_stale_because"][0]["root"])

    def test_s04_is_re_realized_from_the_revised_branch_before_feasibility_is_offered(self):
        state = self.region()
        out, p = self.loop(state, _Canned(*self.region_fix()))
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual(("s03b", "s04a", "s04b"), out.rounds[0].rebuilt)
        realization_ = {e: r["_validity"] for e, r in state.entities.items()
                        if r["_family"] in ("State", "Transition", "SweptVolume")}
        self.assertEqual("INVALIDATED", realization_["STA-CFG-C0A"])
        self.assertEqual("INVALIDATED", realization_["TRN-A"])
        self.assertEqual("STANDING", realization_["STA-CFG-C0A-R1"])
        self.assertEqual("STANDING", realization_["TRN-A-R1"])
        self.assertEqual("STANDING", realization_["SWV-TRN-A-R1-RGP-G1A"])
        self.assertIn("re-realization after upstream revision round 1",
                      state.entities["TRN-A"]["_invalidations"][0]["reason"])
        # the answer offered rests on the fresh realization, not the retired one
        mfa = self.current_mfa(state)
        self.assertIn("TRN-A-R1", mfa["_premises"])
        self.assertNotIn("TRN-A", mfa["_premises"])
        self.assertEqual("FEASIBLE_FOR_SELECTION", out.feasibility)
        # every rebuild pass ran after the owner, through the one invocation path
        self.assertEqual(["s03a", "s03b", "s04a", "s04b"],
                         [e.responsibility_id for e in p.executions])

    def test_a_rebuild_that_does_not_land_offers_no_feasibility(self):
        state = self.region()
        bad = placed(dict(HINGE_BOXES, **{"BOD-NOWHERE": ([0, 0, 0], [1, 1, 1])}))
        out, p = self.loop(state, _Canned(region_topology(["BOD-G0A"]), realization("A"), bad))
        self.assertEqual(own.REVISION_FAILED, out.status, out.as_record())
        self.assertIsNone(out.feasibility)
        self.assertEqual(("s03b", "s04a"), out.rounds[0].rebuilt)
        self.assertTrue(any("s04a" in x for x in out.rounds[0].problems))
        self.assertIsNone(out.rounds[0].repair)
        self.assertTrue(p.failures)

    def test_the_s04_repair_loop_runs_over_the_rebuilt_realization(self):
        """After the revision, s04a realizes the bodies apart - a repairable
        finding of its own - and the s04 repair loop, nested, repairs it."""
        state = self.region()
        provider = _Recording(region_topology(["BOD-G0A"]), realization("A"), placed(APART),
                              motion("A", "JNT-0A", _group(1, "A")), placed(HINGE_BOXES))
        out, _p = self.loop(state, provider)
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        rep = out.rounds[0].repair
        self.assertEqual(repair.SETTLED, rep["status"], rep)
        self.assertEqual(["s04a"], rep["rounds"][0]["invoked"])
        self.assertIn("HOP_BODIES_APART", [c for row in rep["rounds"][0]["signature"] for c in row])
        self.assertIn("REPAIR ROUND 1", provider.prompts[4])
        self.assertEqual(5, provider.calls)
        self.assertEqual([0, 0, 0], state.entities["ENV-G0A"]["extent"]["centre"])
        self.assertEqual("FEASIBLE_FOR_SELECTION", self.current_mfa(state)["status"])

    def test_a_successful_revision_removes_the_obligation(self):
        state = self.region()
        self.assess(state)
        self.assertIn(REGION, {o["code"] for o in self.current_mfa(state)["open_obligations"]})
        out, _p = self.loop(state, _Canned(*self.region_fix()))
        self.assertEqual(own.SETTLED, out.status)
        self.assertEqual([], out.open)
        mfa = self.current_mfa(state)
        self.assertEqual("FEASIBLE_FOR_SELECTION", mfa["status"])
        self.assertNotIn(REGION, {o["code"] for o in mfa["open_obligations"]})
        self.assertEqual([], self.owner_rows(state))

    def test_an_s03b_revision_settles_a_release_finding(self):
        state = self.release()
        out, _p = self.loop(state, _Canned(released([("JNT-0A", "RZ")]), placed(),
                                           motion("A", "JNT-0A", _group(1, "A"))))
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        relation = state.entities["CRL-0A"]
        self.assertEqual([{"joint": "JNT-0A", "dof": "RZ"}], relation["blocked_relative_motions"])
        self.assertEqual([{"joint": "JNT-0A", "dof": "TX"}],
                         relation["_superseded"][0]["prior_value"])
        self.assertIn("s03b owner revision round 1", relation["_superseded"][0]["reason"])
        self.assertEqual(("s04a", "s04b"), out.rounds[0].rebuilt)
        self.assertNotIn(RELEASE, {o["code"] for o in self.current_mfa(state)["open_obligations"]})

    def test_a_restated_record_that_lost_standing_is_re_created_beside_itself(self):
        """The generic rule for a stale record: a supersession does not
        restore standing, so the restatement is INVALIDATE and CREATE under a
        fresh revision id, with the stale record kept."""
        state = self.hinge()
        swept = state.standing("SweptVolume")[0]
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G1A",
                              {"extent": {"half_extent": [2, 2, 2], "centre": [0, 0, 0]}},
                              "t", reason="probe"), stage="s04")
        self.assertEqual("STALE", state.entities[swept["entity_id"]]["_validity"])
        fields = {k: v for k, v in swept.items() if not k.startswith("_") and k != "entity_id"}
        ops = revise_standing_operations(
            state, [Op("CREATE", "SweptVolume", swept["entity_id"], fields, "p",
                       premise_refs=list(swept["_premises"]))], "why")
        self.assertEqual([("INVALIDATE", swept["entity_id"]),
                          ("CREATE", swept["entity_id"] + "-R1")],
                         [(o.kind, o.entity_id) for o in ops])
        self.assertEqual("why", ops[0].reason)

    def test_realization_generations_do_not_collide_across_nested_loops(self):
        """An s04 repair before the owner revision minted the first
        generation; the re-realization after it mints the second, not a
        second first."""
        state = self.hinge(s03a=region_topology(), s04a=placed(),
                           s04b=motion("A", "JNT-0A", _group(1, "A"), changed=[]))
        rep = repair.s04_repair_rounds(_Canned(motion("A", "JNT-0A", _group(1, "A"))), state,
                                       progression.Progression(), self.inv(), rounds=2)
        self.assertEqual(repair.SETTLED, rep.status, rep.as_record())
        self.assertEqual("STANDING", state.entities["STA-CFG-C0A-R1"]["_validity"])
        out, _p = self.loop(state, _Canned(*self.region_fix()))
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual("INVALIDATED", state.entities["STA-CFG-C0A-R1"]["_validity"])
        self.assertEqual("STANDING", state.entities["STA-CFG-C0A-R2"]["_validity"])
        self.assertEqual(3, s04.next_realization_generation(state, "CND-A"))


# =====================================================================
# 3 - bounded, honest, and never a verdict
# =====================================================================
class TestBoundedAndHonest(_Own):

    def test_the_same_findings_over_the_same_basis_is_a_cycle(self):
        state = self.region()
        provider = _Recording(region_topology())      # restates the defect unchanged
        out, p = self.loop(state, provider, rounds=3)
        self.assertEqual(own.CYCLE, out.status, out.as_record())
        self.assertEqual(1, provider.calls, "a cycle was looped on")
        self.assertEqual(1, len(out.rounds))
        self.assertEqual((), out.rounds[0].revised)
        self.assertIn(REGION, {o["code"] for o in out.open})
        self.assertTrue(any("cycle" in f["what"] for f in p.failures))
        mfa = self.current_mfa(state)
        self.assertNotEqual("INFEASIBLE", mfa["status"])
        self.assertNotIn("physical_argument", mfa)
        self.assertIn(REGION, {o["code"] for o in mfa["open_obligations"]})

    def test_an_exhausted_budget_leaves_the_obligation_open_not_infeasible(self):
        """The owner revises a fact - a joint's frame - and leaves the region
        ownerless. Something landed, so the branch is rebuilt and checked;
        the finding stands, the budget is out, and nothing is concluded."""
        state = self.region()
        revised = region_topology()
        revised["joints"][0]["frame_ids"] = ["F2"]
        provider = _Recording(revised, realization("A"), placed(),
                              motion("A", "JNT-0A", _group(1, "A")))
        out, _p = self.loop(state, provider, rounds=1)
        self.assertEqual(own.BUDGET_EXHAUSTED, out.status, out.as_record())
        # s03a revised; s03b's re-authoring re-derived the grid that cited
        # the joint, so it landed too
        self.assertEqual("s03a", out.rounds[0].revised[0])
        self.assertEqual(("s03b", "s04a", "s04b"), out.rounds[0].rebuilt)
        self.assertEqual(4, provider.calls)
        self.assertEqual(["F2"], state.entities["JNT-0A"]["frame_ids"])
        self.assertIn(REGION, {o["code"] for o in out.open})
        mfa = self.current_mfa(state)
        self.assertEqual("FEASIBLE_FOR_SELECTION", mfa["status"])
        self.assertNotIn("physical_argument", mfa)
        self.assertIn(REGION, {o["code"] for o in mfa["open_obligations"]})

    def test_a_revision_that_would_add_a_body_is_refused_and_escalated(self):
        state = self.region()
        before = self.snapshot(state)
        third = topology("A", 3, [(0, 1), (1, 2)])
        third["functional_regions"] = region_topology(["BOD-G0A"])["functional_regions"]
        provider = _Recording(third)
        out, p = self.loop(state, provider)
        self.assertEqual(own.ESCALATED, out.status, out.as_record())
        self.assertEqual(1, provider.calls)
        self.assertEqual(1, len(out.escalated))
        self.assertTrue(out.escalated[0].startswith("s03a: " + s03.ARCHITECTURE_ESCALATION),
                        out.escalated)
        self.assertIn("adds Body BOD-G2A", out.escalated[0])
        self.assertEqual((), out.rounds[0].revised)
        self.assertEqual(before, self.snapshot(state), "a refused revision moved the state")
        self.assertIn(REGION, {o["code"] for o in out.open})
        self.assertNotEqual("INFEASIBLE", self.current_mfa(state)["status"])
        self.assertTrue(any(e.responsibility_id == "s03a" and not e.patch_applied
                            for e in p.executions))

    def test_a_revision_that_would_retype_a_joint_is_refused(self):
        state = self.region()
        before = self.snapshot(state)
        retyped = region_topology(["BOD-G0A"], joint_type="PRISMATIC")
        out, _p = self.loop(state, _Canned(retyped))
        self.assertEqual(own.ESCALATED, out.status, out.as_record())
        self.assertIn("changes Joint.joint_type of JNT-0A", out.escalated[0])
        self.assertEqual(before, self.snapshot(state))

    def test_an_owner_may_declare_a_finding_escalated_and_it_stays_open(self):
        state = self.region()
        before = self.snapshot(state)
        declared = region_topology()
        declared["escalations"] = [{"code": REGION, "why": "the region belongs to a "
                                    "part this candidate does not have"}]
        provider = _Recording(declared)
        out, _p = self.loop(state, provider)
        self.assertEqual(own.ESCALATED, out.status, out.as_record())
        self.assertEqual(1, provider.calls)
        self.assertEqual(["s03a: %s %s: the region belongs to a part this candidate "
                          "does not have" % (s03.ESCALATED, REGION)], out.escalated)
        self.assertEqual(before, self.snapshot(state))
        self.assertIn(REGION, {o["code"] for o in out.open})
        self.assertIn("escalations", provider.prompts[0])

    def test_no_provider_routes_and_stops(self):
        state = self.region()
        before = self.snapshot(state)
        out, _p = self.loop(state, None)
        self.assertEqual(own.NO_PROVIDER, out.status, out.as_record())
        self.assertEqual([("s03a", REGION)], [(o["owner"], o["code"]) for o in out.open])
        self.assertEqual(before, self.snapshot(state))
        self.assertEqual("FEASIBLE_FOR_SELECTION", out.feasibility)

    def test_a_revision_that_does_not_land_ends_the_loop_and_changes_nothing(self):
        state = self.region()
        before = self.snapshot(state)
        out, p = self.loop(state, _Canned(region_topology(["BOD-NOWHERE"])))
        self.assertEqual(own.REVISION_FAILED, out.status, out.as_record())
        self.assertIsNone(out.feasibility)
        self.assertTrue(out.rounds[0].problems)
        self.assertEqual(before, self.snapshot(state))
        self.assertTrue(p.failures)

    def test_no_favourable_retry(self):
        loop = _code(inspect.getsource(own)).lower()
        for word in ("best", "max_attempts", "retry", "compare(", "score", "generationsettings"):
            self.assertNotIn(word, loop, word)
        state = self.region()
        provider = _Recording(*self.region_fix())
        out, _p = self.loop(state, provider, rounds=2)
        self.assertEqual(own.SETTLED, out.status)
        # one call per pass: s03a once, the rebuild once each, nothing again
        self.assertEqual(4, provider.calls)
        self.assertEqual(1, len(out.rounds))

    def test_exhaustion_is_never_a_verdict_in_the_code_either(self):
        self.assertNotIn("INFEASIBLE", _code(inspect.getsource(own)))
        self.assertNotIn("physical_argument", _code(inspect.getsource(own)))


# =====================================================================
# 4 - branch-local, the owner's hand only, authority untouched
# =====================================================================
class TestBranchLocalAndAuthority(_Own):

    def test_one_candidates_revision_touches_no_other_candidate(self):
        state = self.region()
        self.fourbar(state=state)
        other = {e: json.dumps(r, sort_keys=True, default=str)
                 for e, r in state.entities.items()
                 if "CND-B" in (r.get("_premises") or []) or e.endswith("B")}
        self.assertTrue(other, "the probe is not probing")
        out, _p = self.loop(state, _Canned(*self.region_fix()))
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        after = {e: json.dumps(r, sort_keys=True, default=str)
                 for e, r in state.entities.items() if e in other}
        self.assertEqual(other, after, "another candidate's record moved")

    def test_every_write_is_an_owners_and_the_architecture_stands(self):
        state = self.region()
        before = {e: json.dumps(r, sort_keys=True, default=str) for e, r in state.entities.items()}
        out, p = self.loop(state, _Canned(*self.region_fix()))
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual({"s03", "s04"}, {e.stage_id for e in p.executions})
        self.assertEqual({"feasibility"}, {e.stage_id for e in p.deterministic})
        for eid, rec in state.entities.items():
            if before.get(eid) == json.dumps(rec, sort_keys=True, default=str):
                continue
            acts = ([rec.get("_created_by")]
                    + [x["stage"] for x in rec.get("_superseded", [])]
                    + [x["stage"] for x in rec.get("_invalidations", [])]
                    + [x["stage"] for x in rec.get("_extensions", [])])
            self.assertTrue(set(acts) <= {"s03", "s04", "feasibility"}, (eid, acts))
            self.assertNotIn(rec["_family"], ("SelectionDecision", "CandidateComparison",
                                              "SelectionProfile", "HumanDecisionInput",
                                              "Candidate", "Body", "RigidGroup", "Joint"))
        self.assertEqual(before["CND-A"], json.dumps(state.entities["CND-A"], sort_keys=True,
                                                     default=str))

    def test_selection_and_the_principle_know_nothing_of_owner_revision(self):
        import ver3.assy_v3.stages.s02_obligation_and_candidates as s02
        import ver3.assy_v3.stages.selection as sel
        import ver3.assy_v3.stages.selection_decision as dec
        from ver3.assy_v3.lifecycle import s7_reconcile as lc
        for module in (sel, dec, lc, s02):
            source = _code(inspect.getsource(module))
            for token in ("owner_revision", "s03_owner_revision_rounds", "REPAIR_KEY",
                          "from ..pipeline", "import pipeline"):
                self.assertNotIn(token, source, "%s reads %r" % (module.__name__, token))
        loop = _code(inspect.getsource(own))
        for token in ("selection", "SelectionDecision", "HumanDecision", "s02_obligation",
                      "\"Candidate\"", "principle"):
            self.assertNotIn(token, loop, token)
        # the s03 passes emit no candidate and no principle
        import textwrap
        for method in (S03TopologyAndMobility.to_operations, S03BMobilityAndAssembly.to_operations):
            self.assertNotIn('"Candidate"', _code(textwrap.dedent(inspect.getsource(method))))

    def test_no_benchmark_or_candidate_is_named(self):
        for module in (own, s03, repair):
            self.assertIsNone(re.search(r"\bBM-\d|\bCND-\d", inspect.getsource(module)),
                              module.__name__)

    def test_the_loop_is_beside_the_progression_and_invokes_through_it(self):
        chain = _code(inspect.getsource(progression))
        for token in ("owner_revision", "s03_owner_revision_rounds", "evaluate_candidate_feasibility"):
            self.assertNotIn(token, chain, token)
        loop = _code(inspect.getsource(own))
        self.assertIn("execute_stage(", loop)
        self.assertNotIn("stage.invoke(", loop)
        self.assertNotIn("provider.generate(", loop)
        self.assertNotIn("state.apply(", loop)
        # unit c calls into the s04 lifecycle, never the other way round
        self.assertNotIn("owner_revision", _code(inspect.getsource(repair)))


# =====================================================================
# 5 - unit b closure: the prompt, and the typed signature
# =====================================================================
class TestUnitBClosure(_Own):

    def test_the_s04a_prompt_reports_and_never_eliminates(self):
        text = s04.S04A_PROMPT
        for stale in ("it eliminates a candidate cheaply", "what this pass is for",
                      "CANNOT be given a consistent arrangement"):
            self.assertNotIn(stale, text, stale)
        self.assertIn("nothing you state here eliminates a candidate", text)
        self.assertIn("never a verdict on the candidate", text)

    def test_the_same_code_over_a_changed_basis_is_not_a_cycle(self):
        """Round 1 moves a body and leaves the pair apart; round 2 finds the
        same code over a different envelope. That is a new finding, not the
        old one come back, so it is answered - and the budget ends it."""
        state = self.hinge(s04a=arrangement(APART, steps=["ASY-0A"]))
        nearer = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]), "BOD-G1A": ([5, 0, 0], [1, 1, 1])}
        provider = _Recording(arrangement(nearer, steps=["ASY-0A"]),
                              arrangement(dict(nearer, **{"BOD-G1A": ([4, 0, 0], [1, 1, 1])}),
                                          steps=["ASY-0A"]))
        out = repair.s04_repair_rounds(provider, state, progression.Progression(), self.inv(),
                                       rounds=2)
        self.assertEqual(repair.BUDGET_EXHAUSTED, out.status, out.as_record())
        self.assertEqual(2, provider.calls)
        self.assertEqual(2, len(out.rounds))
        self.assertNotEqual(out.rounds[0].signature, out.rounds[1].signature)
        for n in (0, 1):
            self.assertIn("HOP_BODIES_APART", {r[1] for r in out.rounds[n].signature})
            self.assertEqual(("s04a",), out.rounds[n].invoked)

    def test_the_signature_is_typed_and_free_text_does_not_enter_it(self):
        state = self.hinge(s04a=arrangement(APART, steps=["ASY-0A"]))
        p = progression.Progression()
        _status, rows = repair.classified_findings(state, p, "CND-A")
        rows = [r for r in rows if r["class"] == "REPAIRABLE_S04"]
        self.assertTrue(rows)
        first = repair.finding_signature(state, rows)
        for row in first:
            self.assertEqual(4, len(row))
            self.assertTrue(all(isinstance(x, str) for x in row))
        reworded = [dict(r, note="a different sentence about the same thing") for r in rows]
        self.assertEqual(first, repair.finding_signature(state, reworded))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G1A",
                              {"extent": {"half_extent": [1, 1, 1], "centre": [5, 0, 0]}},
                              "t", reason="probe"), stage="s04")
        self.assertNotEqual(first, repair.finding_signature(state, rows))
        source = _code(inspect.getsource(repair.finding_signature))
        for word in ("note", "summary", "reason"):
            self.assertNotIn(word, source, word)


# =====================================================================
# 6 - the words: contexts, occupancy, contracts
# =====================================================================
class TestWordsAndContracts(_Own):

    def test_the_owner_revision_context_states_the_boundary(self):
        for stage in (S03TopologyAndMobility(), S03BMobilityAndAssembly()):
            text = s03.revision_context_text(
                {REPAIR_KEY: {"round": 1, "findings": [{"domain": "d", "code": "C",
                                                        "premises": ["X-1"]}],
                              "current": {}}}, stage.REVISION_MAY_REVISE)
            self.assertIn("OWNER REVISION ROUND 1", text)
            self.assertIn("WHAT YOU MAY NOT DO", text)
            self.assertIn("escalations", text)
            self.assertIn("SAME IDS", text)
            for word in ("body", "joint", "principle", "candidate", "OWNER_REVISION"):
                self.assertIn(word, text)
        self.assertEqual("", s03.revision_context_text({}, "x"))
        upstream = s03.revision_context_text(
            {REPAIR_KEY: {"round": 2, "cause": CAUSE_UPSTREAM_REVISION, "findings": [],
                          "upstream": [{"domain": "d", "code": "C"}], "current": {}}}, "x")
        self.assertIn("WHAT CHANGED UPSTREAM (round 2)", upstream)
        self.assertNotIn("OWNER REVISION ROUND", upstream)
        self.assertEqual("s03b re-authoring after upstream revision round 2: C",
                         s03.revision_reason({REPAIR_KEY: {"round": 2, "cause": CAUSE_UPSTREAM_REVISION,
                                                           "upstream": [{"code": "C"}]}}, "s03b"))

    def test_the_re_realization_context_states_the_boundary(self):
        for stage in (s04.S04AEnvelopeAndReach(), s04.S04BPlacementAndMotion()):
            inputs = {REPAIR_KEY: {"round": 1, "cause": CAUSE_UPSTREAM_REVISION,
                                   "findings": [{"domain": "d", "code": "C"}], "current": {}}}
            text = s04.repair_context_text(inputs, stage.REPAIR_MAY_REVISE)
            self.assertIn("RE-REALIZATION ROUND 1", text)
            self.assertIn("AS IT STANDS NOW", text.upper())
            self.assertIn("WHAT YOU MAY NOT DO", text)
            self.assertEqual("s04 re-realization after upstream revision round 1: C",
                             s04.repair_reason(inputs))
        # and the ordinary repair context is unchanged
        text = s04.repair_context_text({REPAIR_KEY: {"round": 1, "findings": [], "current": {}}}, "x")
        self.assertIn("REPAIR ROUND 1", text)
        self.assertNotIn("RE-REALIZATION", text)

    def test_the_occupancy_list_is_rendered_for_a_revision(self):
        plain = base.render_namespace_occupancy({"Body": ["BOD-1"]})
        revising = base.render_namespace_occupancy({"Body": ["BOD-1"]}, revising=True)
        self.assertIn("must be new", plain)
        self.assertNotIn("must be new", revising)
        self.assertIn("revision of that record", revising)
        self.assertIn("BOD-1", revising)
        self.assertEqual("", base.render_namespace_occupancy({}, revising=True))

    def test_the_architecture_is_declared_and_the_guard_reads_it(self):
        self.assertEqual({"Body", "RigidGroup", "Joint"}, set(s03.ARCHITECTURE))
        ops = [Op("SUPERSEDE", "Joint", "J", {"axis_direction": "+X"}, "p", reason="r"),
               Op("SUPERSEDE", "Joint", "J", {"joint_type": "PRISMATIC"}, "p", reason="r"),
               Op("CREATE", "Body", "B", {}, "p"),
               Op("INVALIDATE", "RigidGroup", "G", {}, "p", reason="r"),
               Op("SUPERSEDE", "Interface", "I", {"interaction_kind": "CLEARANCE"}, "p", reason="r")]
        self.assertEqual(["changes Joint.joint_type of J", "adds Body B", "removes RigidGroup G"],
                         s03.architecture_problems(ops))

    def test_the_contracts_state_the_lifecycle(self):
        c = _paths.load_yaml(_paths.CONTRACTS + "/stages/S03_CONTRACT.yaml")
        life = c["owner_revision_lifecycle"]
        for key in ("principle", "trigger", "owner_reinvocation", "legal_revision_scope",
                    "how_a_revision_is_recorded", "what_a_revision_causes", "bound", "ending"):
            self.assertIn(key, life)
        self.assertIn("OWNER_REVISION", life["trigger"])
        self.assertIn("s03a", life["trigger"])
        self.assertIn("ARCHITECTURE_ESCALATION", life["legal_revision_scope"])
        self.assertIn("never reused merely because its ids exist", life["what_a_revision_causes"])
        self.assertIn("NO FAVOURABLE RETRY", life["bound"])
        self.assertIn("never a free-text summary", life["bound"])
        self.assertIn("never INFEASIBLE by exhaustion", life["ending"])
        self.assertEqual("OPERATIONAL", c["authority_status"]["owner_revision_lifecycle"]["class"])
        resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")["stages"]
        for sid in ("s03a", "s03b"):
            prohibited = " ".join(resp[sid]["prohibited_decisions"])
            self.assertIn("In an owner revision", prohibited)
            self.assertIn("OWNER_REVISION", prohibited)
        s04c = _paths.load_yaml(_paths.CONTRACTS + "/stages/S04_CONTRACT.yaml")["repair_lifecycle"]
        self.assertIn("re_realization_after_upstream_revision", s04c)
        self.assertIn("OVER THE SAME BASIS", s04c["bound"])

    def test_every_s03_owned_revision_code_is_routable(self):
        table = s07.classification()["codes"]
        owners = {spec.get("owner") for spec in table.values()
                  if spec.get("class") == "OWNER_REVISION"}
        self.assertTrue({"s03a", "s03b"} <= owners)
        self.assertTrue(all(o in own.S03_OWNERS or o.startswith("s0") for o in owners), owners)
        for code in (REGION, RELEASE):
            self.assertEqual("OWNER_REVISION", table[code]["class"])
        self.assertEqual("s03a", table[REGION]["owner"])
        self.assertEqual("s03b", table[RELEASE]["owner"])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
