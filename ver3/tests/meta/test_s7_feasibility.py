"""S7-B: can this candidate work, decided from what the design established.

The `feasibility` responsibility is the first producer in the pipeline that asks
no model anything. Every test here therefore runs the REAL chain - s02, s03,
s03b, s04a, s04b through their real invocations - and then the real deterministic
evaluator over the real ConsumerView. Nothing is hand-written into state that a
producer would have written.

WHAT THESE TESTS ARE GUARDING

    A valid simple mechanism and a valid complex one get the same answer. If a
    hinge could come out feasible and a four-bar not, feasibility would be
    carrying a preference, and the whole reason the gate was split in two would
    be undone silently.

    Missing evidence never becomes PASS, and a conservative box overlap never
    becomes FAIL. Those are the two directions absence can be laundered into a
    verdict, and each has its own probe.

    A model-local conclusion decides nothing. A ReachResult and an
    EliminationRecord are s04a's opinions about its own arrangement; a
    deterministic wrapper that promoted either to a verdict would be publishing
    the model's answer under this responsibility's name.

    The premise set of every record is EXACTLY what was read. Stated as an
    equality both ways: dropping one real premise is caught by a mutation that
    should have staled the record and does not, and adding a visible-but-unused
    fact is caught by the same equality from the other side.

Synthetic mechanisms throughout: two bars on a pivot, four bars in a loop. No
product noun, no benchmark id, no state name.
"""
from __future__ import annotations

import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion)
from ver3.assy_v3.stages.feasibility import (                          # noqa: E402
    evaluate_candidate_feasibility)
from ver3.assy_v3.state.design_state import Contracts, DesignState      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.tools import run_window2                                      # noqa: E402
from .test_s02_s03b_integration import S02, _Canned                     # noqa: E402


# =====================================================================
# Two synthetic mechanisms, both mechanically sound
# =====================================================================
def _body(i, sfx):
    return "BOD-G%d%s" % (i, sfx)


def _group(i, sfx):
    return "RGP-G%d%s" % (i, sfx)


def topology(sfx, links, pairs, configs=2, basis=None, joint_type="REVOLUTE",
             axis="+Z"):
    """`links` bodies, one joint per `pairs` entry, one interface per pair.

    The interface list is the pairs the topology declares connected, so a
    mechanism is described once and both the contact requirement and the
    interference exemption follow from that one statement.
    """
    return {
        "bodies": [{"id": _body(i, sfx), "instance_identity": "link",
                    "role": "STRUCTURE"} for i in range(links)],
        "rigid_groups": [{"id": _group(i, sfx), "body": _body(i, sfx),
                          "members": [_body(i, sfx)]} for i in range(links)],
        "interfaces": [{"id": "IFC-%d%s" % (n, sfx),
                        "bodies": [_body(a, sfx), _body(b, sfx)],
                        "interaction_kind": "CONTACT",
                        "nominal_status": "NOMINAL"}
                       for n, (a, b) in enumerate(pairs)],
        "joints": [{"id": "JNT-%d%s" % (n, sfx), "joint_type": joint_type,
                    "parent_group": _group(a, sfx), "child_group": _group(b, sfx),
                    "dof": ["RZ"], "axis_direction": axis, "frame_ids": ["F1"]}
                   for n, (a, b) in enumerate(pairs)],
        "configurations": [
            dict({"id": "CFG-C%d%s" % (j, sfx), "name": "c%d" % j,
                  "kind": "OPERATIONAL",
                  "bodies_present": [_body(i, sfx) for i in range(links)],
                  "expected_mobility": []},
                 **({"distinguishing_basis": (basis or {}).get("CFG-C%d%s" % (j, sfx))}
                    if (basis or {}).get("CFG-C%d%s" % (j, sfx)) else {}))
            for j in range(configs)],
    }


def realization(sfx, hops=(0, 0), steps=(0,), terminates="RSR-0001",
                blocked=None, depends=None, path_kind="RIGID"):
    """s03b for the same mechanism: what discharges the effect, how the load is
    routed through the declared interfaces, and how it goes together."""
    rels = []
    # ONE RELATION ALWAYS. `candidate_engineering_evidence` requires the
    # constraint-relation role to be non-empty, so a probe with none is an
    # unready context rather than a feasible mechanism - and it would be testing
    # the fixture. The default blocks a DOF no probe below requires to move.
    if blocked is None:
        blocked = [(_group(0, sfx), ["TZ"], "CFG-C0%s" % sfx)]
    for n, (group, dofs, cfg) in enumerate(blocked or []):
        rels.append({"id": "CRL-%d%s" % (n, sfx), "retained_group": group,
                     "blocked_dofs": list(dofs), "configurations": [cfg],
                     "driver": "LOAD", "blocked_direction": "+Z",
                     "defeat_specification": "push",
                     "provider_reaction_site": "RSR-0001",
                     "provider_site": "IFC-0%s" % sfx,
                     "maintaining_interaction": "PHI-%s" % sfx})
    path = {"id": "LDP-%s" % sfx, "load_case": "LC-0001", "candidate": "CND-%s" % sfx,
            "ordered_hops": ["IFC-%d%s" % (h, sfx) for h in hops]}
    if terminates:
        path["terminates_at"] = terminates
    return {
        "physical_interactions": [
            {"id": "PHI-%s" % sfx, "groups": [_group(0, sfx)],
             "effect": "TRANSMIT_FORCE", "discharges_effect": "PEO-0001",
             "at_interface": "IFC-0%s" % sfx,
             "configurations": ["CFG-C0%s" % sfx]}],
        "constraint_relations": rels,
        "irrelevance": [],
        "load_paths": [path],
        "assembly_steps": [
            {"id": "ASY-%d%s" % (i, sfx), "order_index": i + 1,
             "body": _body(i, sfx), "access_side": "+Z", "activates": [],
             "termination_strategy": "NONE", "path_kind": path_kind,
             "depends_on": (depends or {}).get(i, [])} for i in steps],
        "unresolved": [],
    }


def arrangement(boxes, steps=(), region=None, actor=None, eliminated=False,
                basis="RELATIVE", absolute=None):
    """s04a: where each body is. `boxes` is {body: (centre, half_extent)}."""
    return {
        "scale": {"basis": basis, "absolute": absolute, "note": "unit"},
        "envelopes": [{"id": "ENV-%s" % b.split("-")[-1], "body": b,
                       "centre": list(c), "half_extent": list(h),
                       "maturity": "PROVISIONAL"}
                      for b, (c, h) in sorted(boxes.items())],
        "region_volumes": ([{"functional_region": region, "half_extent": [1, 1, 1],
                             "centre": [0, 0, 9]}] if region else []),
        "reach_results": ([{"actor": actor, "target": sorted(boxes)[0],
                            "reachable": True, "approach_side": "+Z",
                            "why": "open"}] if actor else []),
        "assembly_directions": [{"assembly_step": s, "direction": [0, 0, -1]}
                                for s in steps],
        "elimination": {"eliminated": eliminated,
                        "reason": "no consistent arrangement" if eliminated else None},
    }


def motion(sfx, joint, moving, coords=(0, 90), configs=("C0", "C1"),
           changed=None, transition=True):
    """s04b: the coordinates that realize each configuration, and the path."""
    a, b = ["CFG-%s%s" % (c, sfx) for c in configs]
    out = {
        "joint_placements": [{"joint": joint, "origin": [0, 0, 0]}],
        "state_coordinates": [
            {"configuration": a, "coordinates": {joint: coords[0]}},
            {"configuration": b, "coordinates": {joint: coords[1]}}],
        "transitions": [],
        "envelope_revisions": [], "notes": "",
    }
    if transition:
        out["transitions"] = [{"id": "TRN-%s" % sfx, "from_configuration": a,
                               "to_configuration": b, "moving_groups": [moving],
                               "changed_coordinates": ([joint] if changed is None
                                                       else list(changed))}]
    return out


#: A HINGE. Two bars whose boxes overlap on the axis the joint turns about, and
#: one declared interface for the pair, so the contact the topology requires and
#: the overlap the sweep produces are the same statement.
HINGE_BOXES = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
               "BOD-G1A": ([1.5, 0, 0], [1, 1, 1])}

#: A FOUR-BAR. Four bars in a closed loop, adjacent pairs touching and opposite
#: pairs well clear, so every overlap in it is one the topology declared.
FOURBAR_BOXES = {"BOD-G0B": ([1.5, 0, 0], [1.6, 0.3, 0.3]),
                 "BOD-G1B": ([3, 1.5, 0], [0.3, 1.6, 0.3]),
                 "BOD-G2B": ([1.5, 3, 0], [1.6, 0.3, 0.3]),
                 "BOD-G3B": ([0, 1.5, 0], [0.3, 1.6, 0.3])}


# =====================================================================
# The chain
# =====================================================================
class _Feas(_fixtures.StateBuilder, unittest.TestCase):
    """s01..s04 through the real stages, then the real feasibility evaluator."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def seed(self):
        s = DesignState(run_id="feasibility")
        self.add(s, "s01", "Requirement", "REQ-0001", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-0001")
        self.add(s, "s01", "Scenario", "SCN-0001", actors=["ACT-0001"])
        return s

    def branch(self, state, sfx, s03a, s03b, s04a, s04b, apply_b=True):
        inv = cv.InvocationContext(branch="CND-%s" % sfx)
        provider = _Canned(s03a, s03b, s04a, s04b)
        state.apply(S03TopologyAndMobility().invoke(
            provider, state, state.run_id,
            {"candidate": {"entity_id": "CND-%s" % sfx}}, invocation=inv).patch)
        out = S03BMobilityAndAssembly().invoke(
            provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
            attempt=2, invocation=inv)
        self.assertIsNotNone(out.patch, out.problems)
        state.apply(out.patch)
        oa = S04AEnvelopeAndReach().invoke(
            provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
            attempt=1, invocation=inv)
        self.assertIsNotNone(oa.patch, oa.problems)
        state.apply(oa.patch)
        if apply_b:
            ob = S04BPlacementAndMotion().invoke(
                provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
                attempt=2, invocation=inv)
            self.assertIsNotNone(ob.patch, ob.problems)
            state.apply(ob.patch)
        return state

    # -- the two probes ------------------------------------------------
    def hinge(self, state=None, sfx="A", s03a=None, s03b=None, s04a=None,
              s04b=None, **kw):
        state = state if state is not None else self.seed()
        self.candidates(state)
        return self.branch(
            state, sfx,
            s03a if s03a is not None else topology(sfx, 2, [(0, 1)]),
            s03b if s03b is not None else realization(sfx),
            s04a if s04a is not None else arrangement(
                {k.replace("A", sfx): v for k, v in HINGE_BOXES.items()},
                steps=["ASY-0%s" % sfx]),
            s04b if s04b is not None else motion(
                sfx, "JNT-0%s" % sfx, _group(1, sfx)), **kw)

    def fourbar(self, state=None, sfx="B"):
        state = state if state is not None else self.seed()
        self.candidates(state)
        pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
        return self.branch(
            state, sfx, topology(sfx, 4, pairs),
            realization(sfx, hops=(0, 1), steps=(0,)),
            arrangement({k.replace("B", sfx): v for k, v in FOURBAR_BOXES.items()},
                        steps=["ASY-0%s" % sfx]),
            # A SMALL ROTATION. The four-bar is judged on the same rules as the
            # hinge; sweeping a bar through the frame would be testing the probe.
            motion(sfx, "JNT-3%s" % sfx, _group(0, sfx), coords=(0, 10)))

    def candidates(self, state):
        if state.family("Candidate"):
            return
        payload = json.loads(json.dumps(S02))
        template = payload["candidates"][0]
        payload["candidates"] = [dict(template, id="CND-%s" % s,
                                      summary="alternative %s" % s)
                                 for s in ("A", "B")]
        state.apply(S02ObligationAndCandidates().invoke(
            _Canned(payload), state, state.run_id).patch)

    # -- asking the question -------------------------------------------
    def assess(self, state, candidate="CND-A", apply_patch=True):
        out = evaluate_candidate_feasibility(state, candidate)
        self.assertEqual([], out.problems, "the patch did not validate")
        self.assertIsNotNone(out.patch)
        if apply_patch:
            state.apply(out.patch)
        return out

    def domain(self, out, name):
        for v in out.verdicts:
            if v.domain == name:
                return v
        raise AssertionError("no verdict for %s" % name)

    def prem(self, state, eid):
        return set(state.entities[eid].get("_premises") or [])

    def val(self, state, eid):
        return state.entities[eid].get("_validity")

    def revise(self, state, op, stage="s04"):
        state.apply(StagePatch(
            patch_id="rev-%d" % len(state.applied_patches), run_id=state.run_id,
            stage_id=stage, stage_attempt=9, parent_state_hash=state.state_hash(),
            operations=[op], execution_status="SUCCESS",
            provenance={"provider": "t"}))


# =====================================================================
# B1-B3 - a valid mechanism is feasible, however many joints it has
# =====================================================================
class TestValidMechanisms(_Feas):

    def test_B1_a_simple_revolute_hinge_is_feasible(self):
        out = self.assess(self.hinge())
        self.assertEqual(s07.FEASIBLE, out.status,
                         [(v.domain, v.status, v.reason_codes) for v in out.verdicts
                          if v.status not in (s07.PASS, s07.NOT_APPLICABLE)])

    def test_B2_a_mechanically_sound_four_bar_is_feasible(self):
        out = self.assess(self.fourbar(), "CND-B")
        self.assertEqual(s07.FEASIBLE, out.status,
                         [(v.domain, v.status, v.reason_codes) for v in out.verdicts
                          if v.status not in (s07.PASS, s07.NOT_APPLICABLE)])

    def test_B3_more_joints_does_not_change_the_answer(self):
        """THE POINT OF THE SPLIT. Complexity is not an input here, and the only
        way to be sure is to run both and compare the answers, not the code."""
        simple = self.assess(self.hinge())
        complex_ = self.assess(self.fourbar(), "CND-B")
        self.assertEqual(simple.status, complex_.status)
        self.assertLess(simple.consumer_view["counts"]["Joint"],
                        complex_.consumer_view["counts"]["Joint"],
                        "the probes are not actually different mechanisms")
        self.assertEqual(
            {v.domain: v.status for v in simple.verdicts
             if v.status != s07.NOT_APPLICABLE},
            {v.domain: v.status for v in complex_.verdicts
             if v.status != s07.NOT_APPLICABLE},
            "two valid mechanisms were judged differently")


# =====================================================================
# B4-B11 - what each domain does with a contradiction and with an absence
# =====================================================================
class TestDomainPolicy(_Feas):

    def test_B4_a_declared_distinctness_that_is_not_realized_is_infeasible(self):
        """Two configurations declared to differ, realized at the same
        coordinate. A positive contradiction: the design says the mechanism is
        in two states and the numbers say it is in one."""
        basis = {"CFG-C0A": [{"rigid_group": _group(1, "A"), "dof": "RZ",
                              "differs_from": ["CFG-C1A"]}]}
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       coords=(60, 60)))
        out = self.assess(state)
        self.assertEqual(s07.FAIL, self.domain(out, "required_configurations").status)
        self.assertIn("DECLARED_DISTINCTNESS_NOT_REALIZED",
                      self.domain(out, "required_configurations").reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)

    def test_B4b_a_transition_that_moves_what_it_did_not_declare_is_infeasible(self):
        state = self.hinge(s04b=motion("A", "JNT-0A", _group(1, "A"), changed=[]))
        out = self.assess(state)
        self.assertEqual(s07.FAIL, self.domain(out, "motion_and_transitions").status)
        self.assertIn("UNDECLARED_COORDINATE_CHANGE",
                      self.domain(out, "motion_and_transitions").reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)

    def test_B5_a_required_transition_that_is_absent_is_not_established(self):
        """NOT_APPLICABLE would be the wrong answer and the dangerous one: the
        design declares that a state change is required, so the question is
        asked and unanswered rather than not asked."""
        basis = {"CFG-C0A": [{"rigid_group": _group(1, "A"), "dof": "RZ",
                              "differs_from": ["CFG-C1A"]}]}
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       transition=False))
        out = self.assess(state)
        v = self.domain(out, "motion_and_transitions")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("REQUIRED_TRANSITION_MISSING", v.reason_codes)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)

    def test_B6_a_conservative_overlap_is_never_infeasible(self):
        """Two bodies the topology does not connect, placed overlapping. The
        boxes are bigger than the bodies, so an overlap is what has not been
        established - the opposite direction from a gap, which is proof."""
        state = self.hinge(
            s03a=topology("A", 2, [(0, 1)]),
            s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                              "BOD-G1A": ([0.2, 0, 0], [1, 1, 1])},
                             steps=["ASY-0A"]))
        out = self.assess(state)
        v = self.domain(out, "gross_interference")
        self.assertNotEqual(s07.FAIL, v.status)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        for w in out.verdicts:
            self.assertNotEqual(s07.FAIL, w.status,
                                "%s turned an overlap into a contradiction" % w.domain)

    def test_B7_a_terminus_that_is_not_the_declared_site_is_infeasible(self):
        # The site EXISTS, is EXTERNAL, and is not the one the load case names.
        # A dangling reference and an internal terminus are different findings,
        # and this probe is about closing in the wrong place.
        state = self.seed()
        self.candidates(state)
        self.add(state, "s02", "ReactionSiteRequirement", "RSR-OTHER",
                 scenario="SCN-0001", boundary_side="EXTERNAL",
                 at_role="a different outside surface")
        self.hinge(state=state, s03b=realization("A", terminates="RSR-OTHER"))
        out = self.assess(state)
        v = self.domain(out, "load_reaction_closure")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("TERMINUS_NOT_THE_DECLARED_SITE", v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)

    def test_B7b_a_terminus_inside_the_product_is_infeasible(self):
        state = self.hinge(s03b=realization("A", terminates="RSR-0001"))
        self.revise(state, Op("SUPERSEDE", "ReactionSiteRequirement", "RSR-0001",
                              {"boundary_side": "INTERNAL"}, "t",
                              reason="the boundary moved"), stage="s02")
        out = self.assess(state)
        v = self.domain(out, "load_reaction_closure")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("TERMINAL_SITE_INTERNAL", v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)

    def test_B8_a_positive_gap_on_the_load_route_is_infeasible(self):
        """A GAP IS PROOF, where an overlap is not: the real bodies are smaller
        than their boxes, so boxes that are apart are bodies that are apart."""
        state = self.hinge(
            s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                              "BOD-G1A": ([9, 0, 0], [1, 1, 1])},
                             steps=["ASY-0A"]))
        out = self.assess(state)
        v = self.domain(out, "load_reaction_closure")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("HOP_BODIES_APART", v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)
        self.assertEqual(s07.FAIL, self.domain(out, "spatial_realization").status,
                         "the topology connects them and they are apart")

    def test_B9_an_undispositioned_required_cell_is_not_established(self):
        """The cell is required to move and the design says nothing about it."""
        state = self.hinge()
        mex = [m for m in state.family("MobilityExpectation")][0]
        kept = [dict(d, disposition="UNDISPOSITIONED",
                     missing="withdrawn for this probe", by_joint=None)
                if d["rigid_group"] == _group(1, "A") and d["dof"] == "RZ" else d
                for d in mex["dispositions"]]
        self.revise(state, Op("SUPERSEDE", "MobilityExpectation", mex["entity_id"],
                              {"dispositions": kept}, "t",
                              reason="withdraw the disposition"), stage="s03")
        out = self.assess(state)
        v = self.domain(out, "mobility_disposition")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)

    def test_B10_a_cell_required_to_move_and_blocked_is_infeasible(self):
        """A ConstraintRelation blocking the DOF a transition turns. Two current
        typed facts that cannot both be honoured."""
        state = self.hinge(s03b=realization(
            "A", blocked=[(_group(1, "A"), ["RZ"], "CFG-C0A")]))
        out = self.assess(state)
        v = self.domain(out, "mobility_disposition")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("REQUIRED_MOTION_CONTRADICTED", v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)

    def test_B11_a_static_candidate_is_not_a_context_failure(self):
        """No transition and no declared distinctness: the design poses no
        motion question, and NOT_APPLICABLE is the whole answer."""
        state = self.hinge(s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       transition=False))
        out = self.assess(state)
        for name in ("motion_and_transitions", "mobility_disposition"):
            self.assertEqual(s07.NOT_APPLICABLE, self.domain(out, name).status, name)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        self.assertEqual([], out.problems)


# =====================================================================
# B12-B13 - a model's conclusion is evidence, never a verdict
# =====================================================================
class TestModelLocalFindings(_Feas):

    def test_B12_a_reach_result_alone_cannot_pass_or_fail_the_domain(self):
        state = self.hinge(
            s03a=dict(topology("A", 2, [(0, 1)]),
                      functional_regions=[{"id": "FRG-A", "role": "ACCESS",
                                           "owning_bodies": ["BOD-G0A"],
                                           "required_by_actors": ["ACT-0001"]}]),
            s04a=arrangement({k: v for k, v in HINGE_BOXES.items()},
                             steps=["ASY-0A"], region="FRG-A", actor="ACT-0001"))
        self.assertTrue(state.family("ReachResult"), "the probe is not probing")
        out = self.assess(state)
        v = self.domain(out, "reach")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("REACH_BASIS_NOT_ESTABLISHED", v.reason_codes)
        self.assertIn(s07.MODEL_LOCAL_POSITIVE, v.reason_codes)
        self.assertEqual([], v.premises,
                         "a model's conclusion was recorded as a premise of the "
                         "verdict, which would make it evidence for itself")

    def test_B13_an_elimination_record_alone_cannot_make_it_infeasible(self):
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            eliminated=True))
        self.assertTrue([e for e in state.family("EliminationRecord")
                         if e.get("eliminated")], "the probe is not probing")
        out = self.assess(state)
        v = self.domain(out, "spatial_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn(s07.MODEL_LOCAL_NEGATIVE, v.reason_codes)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status,
                         "a model-local elimination became the pipeline's verdict")


# =====================================================================
# B14-B16 - hard requirements, and what makes one evaluable
# =====================================================================
class TestHardRequirements(_Feas):

    def constraint(self, state, kind, **params):
        self.add(state, "s01", "DesignConstraint", "DSC-0001", kind=kind,
                 statement="a stated hard requirement", source="profile",
                 evaluability="MACHINE_EVALUABLE", parameters=params or None,
                 blocks_selection=True)
        return state

    def status_of(self, out, cid="DSC-0001"):
        for constraint, status, codes, used, why in out.compliance:
            if constraint.get("entity_id") == cid:
                return status, codes, used, why
        raise AssertionError("no compliance record for %s" % cid)

    def test_B14_a_material_requirement_with_no_material_authority(self):
        """Nothing in the representation assigns a material, so the answer is
        about the evidence. SATISFIED because nothing contradicts it would be
        absence becoming compliance."""
        state = self.constraint(self.hinge(), "MATERIAL_CLASS_ONLY",
                                material_class="PLASTIC")
        status, codes, used, _why = self.status_of(self.assess(state))
        self.assertEqual(s07.NOT_YET_EVALUABLE, status)
        self.assertIn("NO_MATERIAL_AUTHORITY", codes)
        self.assertEqual([], used, "a premise was fabricated for a missing fact")

    def test_B14b_an_energy_requirement_with_no_energy_authority(self):
        state = self.constraint(self.hinge(), "PROHIBITED_ENERGY_SOURCE",
                                source="MAINS_ELECTRICAL")
        status, codes, _used, _why = self.status_of(self.assess(state))
        self.assertEqual(s07.NOT_YET_EVALUABLE, status)
        self.assertIn("NO_ENERGY_AUTHORITY", codes)

    def test_B14c_a_kind_with_no_evaluator_is_not_yet_evaluable(self):
        state = self.constraint(self.hinge(), "SOME_KIND_NOBODY_IMPLEMENTED")
        status, codes, _used, _why = self.status_of(self.assess(state))
        self.assertEqual(s07.NOT_YET_EVALUABLE, status)
        self.assertIn("NO_EVALUATOR_FOR_KIND", codes)

    def _absolute(self, sfx="A", per_unit=10.0, unit="mm"):
        return self.hinge(s04a=arrangement(
            HINGE_BOXES, steps=["ASY-0%s" % sfx], basis="ABSOLUTE",
            absolute={"unit": unit, "per_unit": per_unit}))

    def test_B15_a_dimensional_requirement_with_an_absolute_scale_decides(self):
        """The hinge spans 3.5 relative units; at 10 mm each that is 35 mm."""
        state = self.constraint(self._absolute(), "MAX_OVERALL_DIMENSION",
                                axis="ANY", limit=100, unit="mm")
        status, codes, used, why = self.status_of(self.assess(state))
        self.assertEqual(s07.SATISFIED, status, why)
        self.assertIn("WITHIN_OVERALL_DIMENSION", codes)
        self.assertIn("SCL-CND-A", used, "the basis is what made it comparable")

        tight = self.constraint(self._absolute(), "MAX_OVERALL_DIMENSION",
                                axis="ANY", limit=10, unit="mm")
        status, codes, _used, why = self.status_of(self.assess(tight))
        self.assertEqual(s07.VIOLATED, status, why)
        self.assertIn("OVERALL_DIMENSION_EXCEEDED", codes)

    def test_B16_the_same_requirement_with_an_ambiguous_scale(self):
        for scale, code in (
                (self.hinge(), "SCALE_NOT_ABSOLUTE"),
                (self._absolute(unit="in"), "UNIT_AMBIGUOUS"),
                (self._absolute(per_unit=None), "SCALE_FACTOR_MISSING")):
            state = self.constraint(scale, "MAX_OVERALL_DIMENSION",
                                    axis="ANY", limit=10, unit="mm")
            status, codes, _used, why = self.status_of(self.assess(state))
            self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
            self.assertIn(code, codes)

    def test_B16b_a_design_that_states_no_hard_requirement_produces_none(self):
        out = self.assess(self.hinge())
        self.assertEqual([], out.compliance)
        self.assertEqual([], [op for op in out.patch.operations
                              if op.entity_type == "HardRequirementCompliance"])


# =====================================================================
# B17-B22 - isolation, and premise sets that are exactly what was read
# =====================================================================
class TestIsolationAndDependency(_Feas):

    def test_B17_a_selection_profile_never_reaches_this_responsibility(self):
        """PREFERENCE BLINDNESS IS STRUCTURAL. The profile is standing in state,
        and the view cannot contain it because nothing here declares the role."""
        state = self.hinge()
        self.add(state, "selection", "SelectionProfile", "SPF-0001",
                 profile_version="1", source_hash="h",
                 criteria=[{"criterion": "part_count", "objective": "MINIMIZE",
                            "priority": "HIGH"}])
        self.assertTrue(state.family("SelectionProfile"), "the probe is not probing")
        out = self.assess(state)
        self.assertNotIn("SelectionProfile", out.consumer_view["counts"])
        self.assertNotIn("SPF-0001",
                         {e["entity_id"] for e in out.consumer_view["entities"]})
        for op in out.patch.operations:
            self.assertNotIn("SPF-0001", op.premise_refs)
        blob = json.dumps([op.fields for op in out.patch.operations])
        self.assertNotIn("SPF-0001", blob)
        self.assertNotIn("part_count", blob)

    def test_B18_another_candidates_change_leaves_this_one_standing(self):
        state = self.hinge()
        self.fourbar(state)
        self.assess(state, "CND-A")
        self.assertEqual("STANDING", self.val(state, "MFA-CND-A"))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G0B",
                              {"extent": {"centre": [0, 0, 0],
                                          "half_extent": [4, 4, 4]}},
                              "t", reason="the other alternative changed"))
        self.assertEqual("STANDING", self.val(state, "MFA-CND-A"),
                         "another candidate's geometry staled this one's verdict")
        for v in s07.DOMAINS:
            eid = "FDA-CND-A-%s" % v.upper().replace("_", "-")
            self.assertEqual("STANDING", self.val(state, eid), eid)

    def test_B19_a_fact_this_candidate_used_stales_the_domain_AND_the_whole(self):
        """DIRECTLY, not by inheritance. `_propagate` is one hop, so an
        assessment that named only its domain records would sit STANDING on a
        staled domain verdict."""
        state = self.hinge()
        self.assess(state)
        self.assertIn("ENV-G1A", self.prem(state, "FDA-CND-A-SPATIAL-REALIZATION"))
        self.assertIn("ENV-G1A", self.prem(state, "MFA-CND-A"),
                      "the raw union was not carried")
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G1A",
                              {"extent": {"centre": [9, 0, 0],
                                          "half_extent": [1, 1, 1]}},
                              "t", reason="the arrangement changed"))
        self.assertEqual("STALE", self.val(state, "FDA-CND-A-SPATIAL-REALIZATION"))
        self.assertEqual("STALE", self.val(state, "MFA-CND-A"),
                         "the whole assessment survived a change to a fact it used")

    def test_B20_a_visible_fact_no_evaluator_used_is_not_a_premise(self):
        """The other candidate's material is not in the view at all; this probe
        needs something IN the view and unused, and the reach domain supplies
        it: a ReachResult is visible, contributes a reason code, and is used by
        no computation."""
        state = self.hinge(
            s03a=dict(topology("A", 2, [(0, 1)]),
                      functional_regions=[{"id": "FRG-A", "role": "ACCESS",
                                           "owning_bodies": ["BOD-G0A"],
                                           "required_by_actors": ["ACT-0001"]}]),
            s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"], region="FRG-A",
                             actor="ACT-0001"))
        out = self.assess(state)
        reach = [r["entity_id"] for r in state.family("ReachResult")]
        self.assertTrue(reach, "the probe is not probing")
        visible = {e["entity_id"] for e in out.consumer_view["entities"]}
        self.assertTrue(set(reach) & visible, "the finding is not even in the view")
        for op in out.patch.operations:
            for r in reach:
                self.assertNotIn(r, op.premise_refs, op.entity_id)
        self.revise(state, Op("SUPERSEDE", "ReachResult", reach[0],
                              {"reachable": False}, "t", reason="reconsidered"))
        self.assertEqual("STANDING", self.val(state, "MFA-CND-A"),
                         "a fact nothing computed from staled the assessment")

    def test_B21_dropping_one_real_premise_is_caught(self):
        """Each raw fact the assessment used, changed one at a time: without it
        in the premise set the record it should have staled stays STANDING. This
        is what makes the equality below mean something."""
        for family, eid, fields in (
                ("Envelope", "ENV-G1A", {"extent": {"centre": [9, 0, 0],
                                                    "half_extent": [1, 1, 1]}}),
                ("State", "STA-CFG-C1A", {"joint_coordinates": {"JNT-0A": 12}}),
                ("Joint", "JNT-0A", {"axis_direction": "+X"}),
                ("Transition", "TRN-A", {"changed_coordinates": []}),
                ("LoadPath", "LDP-A", {"maturity": "HYPOTHESIS"}),
                # THE BASIS. Every extent and every coordinate above is
                # expressed in it, and naming only the envelope would not carry
                # it: `_propagate` stales the envelope and stops, leaving the
                # verdict standing on a number that has lost its meaning.
                ("ReferenceScale", "SCL-CND-A", {"basis": "ABSOLUTE"}),
                # The topology's own statement of which pairs must touch.
                ("Interface", "IFC-0A", {"interaction_kind": "CLEARANCE"}),
                ("RigidGroup", "RGP-G1A", {"members": []}),
                ("PhysicalEffectObligation", "PEO-0001",
                 {"persistence": "TRANSIENT"}),
                ("LoadCase", "LC-0001", {"magnitude_or_status": "SUPPORTED"}),
                ("AssemblyStep", "ASY-0A", {"access_side": "-Z"}),
                ("Configuration", "CFG-C1A", {"name": "renamed"}),
                ("SweptVolume", "SWV-TRN-A-RGP-G1A",
                 {"fidelity": "ENDPOINTS_ONLY"})):
            state = self.hinge()
            self.assess(state)
            self.assertIn(eid, self.prem(state, "MFA-CND-A"),
                          "%s was read and is not a premise" % eid)
            self.revise(state, Op("SUPERSEDE", family, eid, fields, "t",
                                  reason="probe"))
            self.assertEqual("STALE", self.val(state, "MFA-CND-A"),
                             "%s changed and the assessment did not notice" % eid)

    def test_B22_the_premise_set_is_not_everything_in_the_view(self):
        """The other direction of the same equality. A blanket 'everything
        visible' would make an unrelated change stale every verdict, and STALE
        that fires for no reason is STALE nobody reads."""
        state = self.hinge()
        out = self.assess(state)
        visible = {e["entity_id"] for e in out.consumer_view["entities"]}
        carried = set(next(op for op in out.patch.operations
                           if op.entity_type == "MechanicalFeasibilityAssessment"
                           ).premise_refs)
        # The domain records are co-produced in this same patch, so they are not
        # in the view and are not part of the "did it copy the view" question.
        raw = {p for p in carried if not p.startswith("FDA-")}
        self.assertTrue(raw < visible,
                        "the assessment carries everything it could see")
        # The exact set, both directions at once. Its members are the facts nine
        # domain evaluations actually read - no more, and no fewer.
        domains = {"FDA-CND-A-%s" % d.upper().replace("_", "-") for d in s07.DOMAINS}
        self.assertEqual(
            domains | {"CND-A", "ASY-0A", "BOD-G0A", "BOD-G1A", "CFG-C0A",
                       "CFG-C1A", "ENV-G0A", "ENV-G1A", "IFC-0A", "JNT-0A",
                       "LC-0001", "LDP-A", "MEX-CFG-C0A", "MEX-CFG-C1A",
                       "PEO-0001", "PHI-A", "RGP-G0A", "RGP-G1A", "RSR-0001",
                       "SCL-CND-A", "STA-CFG-C0A", "STA-CFG-C1A",
                       "SWV-TRN-A-RGP-G1A", "TRN-A"},
            carried)
        # And what is visible, was not computed from, and is therefore absent:
        # the requirement the obligation came from, the scenario, the actor, the
        # relation that constrains a DOF nothing requires to move, and s04a's
        # own elimination finding.
        for unused in ("REQ-0001", "SCN-0001", "ACT-0001", "OBL-0001", "CRL-0A"):
            self.assertIn(unused, visible, "the probe is not probing")
            self.assertNotIn(unused, carried)

    def test_B22b_each_domain_carries_only_its_own_evidence(self):
        """The reason the domain is the unit of dependency. A load verdict does
        not rest on an envelope the load route never touched, so an arrangement
        change must not stale the load closure it cannot affect."""
        state = self.hinge()
        self.assess(state)
        load = self.prem(state, "FDA-CND-A-LOAD-REACTION-CLOSURE")
        motion_ = self.prem(state, "FDA-CND-A-MOTION-AND-TRANSITIONS")
        self.assertIn("LDP-A", load)
        self.assertNotIn("LDP-A", motion_)
        self.assertIn("TRN-A", motion_)
        self.assertNotIn("TRN-A", load)
        self.revise(state, Op("SUPERSEDE", "Transition", "TRN-A",
                              {"changed_coordinates": ["JNT-0A"]}, "t",
                              reason="restated"))
        self.assertEqual("STALE", self.val(state, "FDA-CND-A-MOTION-AND-TRANSITIONS"))
        self.assertEqual("STANDING", self.val(state, "FDA-CND-A-LOAD-REACTION-CLOSURE"),
                         "a motion change staled a load verdict it cannot affect")

    def test_B22c_an_absence_does_not_get_a_fabricated_premise(self):
        """NOT_ESTABLISHED by absence names no entity, because there is none to
        name. Inventing one would make a missing fact look like a present one."""
        basis = {"CFG-C0A": [{"rigid_group": _group(1, "A"), "dof": "RZ",
                              "differs_from": ["CFG-C1A"]}]}
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       transition=False))
        out = self.assess(state)
        v = self.domain(out, "motion_and_transitions")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertEqual([], v.premises)
        op = next(o for o in out.patch.operations
                  if o.entity_id == "FDA-CND-A-MOTION-AND-TRANSITIONS")
        self.assertEqual(["CND-A"], op.premise_refs)


# =====================================================================
# B23-B25 - who is allowed to say this, and how
# =====================================================================
class TestAuthority(_Feas):

    def test_B23_feasibility_invokes_no_provider(self):
        """NOT ASSERTED ABOUT A PROMPT - there is no prompt. Three structural
        facts instead: the entry point takes no provider, the module imports
        nothing from any provider package, and it calls nothing named like a
        model invocation. Read from the AST, so a mention in a docstring is not
        mistaken for a call and a call is not hidden by one."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(s07))
        self.assertNotIn("provider", inspect.signature(
            evaluate_candidate_feasibility).parameters)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
            elif isinstance(node, ast.Import):
                imported += [a.name for a in node.names]
        self.assertEqual([], [m for m in imported
                              if "provider" in m or "live" in m], imported)
        called = {node.func.attr for node in ast.walk(tree)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)}
        for name in ("invoke", "complete", "chat", "generate", "call"):
            self.assertNotIn(name, called, "S7-B reaches for a model")

    def test_B24_the_runner_records_and_decides_nothing(self):
        state = self.hinge()
        rec = run_window2.run_feasibility(
            "SYN", state, 1, invocation=cv.InvocationContext(branch="CND-A"))
        self.assertEqual(s07.FEASIBLE, rec["feasibility_status"], rec["failures"])
        self.assertEqual([], rec["failures"])
        self.assertEqual("STANDING", self.val(state, "MFA-CND-A"),
                         "the runner did not apply the patch it was given")
        source = __import__("inspect").getsource(run_window2.run_feasibility)
        for verdict in ("FEASIBLE_FOR_SELECTION", "INFEASIBLE", "PASS", "FAIL",
                        "NOT_ESTABLISHED", "NOT_APPLICABLE"):
            self.assertNotIn('"%s"' % verdict, source,
                             "the runner names an engineering verdict")
        self.assertNotIn("provider", __import__("inspect").signature(
            run_window2.run_feasibility).parameters)

    def test_B25_no_other_stage_may_author_these_families(self):
        state = self.hinge()
        for family, eid in (("MechanicalFeasibilityAssessment", "MFA-X"),
                            ("HardRequirementCompliance", "HRC-X"),
                            ("FeasibilityDomainAssessment", "FDA-X")):
            for stage in ("s03", "s04", "selection"):
                problems = state.validate(StagePatch(
                    patch_id="bad", run_id=state.run_id, stage_id=stage,
                    stage_attempt=1, parent_state_hash=state.state_hash(),
                    operations=[Op("CREATE", family, eid,
                                   {"candidate": "CND-A", "status": "PASS"}, "t")],
                    execution_status="SUCCESS", provenance={"provider": "t"}))
                self.assertTrue(any("OWNERSHIP" in p or "may_create" in p
                                    or "NOT_OWNER" in p for p in problems),
                                "%s was allowed to author %s: %s"
                                % (stage, family, problems))

    def test_B25c_the_module_does_not_squat_on_a_pipeline_stage_number(self):
        """A RESPONSIBILITY IS NOT A NUMBERED STAGE, which is what S7-A settled
        when it declined to call these two "Stage 7" and "Stage 8". Pipeline s07
        is geometry compilation and has its own contract; a module named for it
        would take a second meaning for one identifier AND satisfy the
        progression gate by matching the compiler's contract file."""
        import os
        from . import _paths
        base = os.path.basename(s07.__file__)
        for stage_id in _paths.STAGE_IDS:
            self.assertFalse(base.startswith(stage_id + "_") or base == stage_id + ".py",
                             "%s claims pipeline stage %s" % (base, stage_id))
        self.assertEqual("feasibility", s07.RESPONSIBILITY)
        self.assertIn(s07.RESPONSIBILITY, base)

    def test_B25b_the_evaluator_refuses_when_its_context_is_not_ready(self):
        """A REFUSAL IS A RESULT. Without s04 there is no arrangement to read,
        and an assessment produced anyway would be feasibility asserted from an
        absence - exactly what every domain rule above forbids."""
        state = self.seed()
        self.candidates(state)
        out = evaluate_candidate_feasibility(state, "CND-A")
        self.assertIsNone(out.patch)
        self.assertIsNone(out.status)
        self.assertTrue(out.problems)
        self.assertFalse(out.ok)
        self.assertNotEqual("VIEW_READY", out.consumer_view["status"])


if __name__ == "__main__":
    unittest.main()
