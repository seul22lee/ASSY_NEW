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

import ast
import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s01_requirement_capture as s01            # noqa: E402
from ver3.assy_v3.stages.s01_requirement_capture import (             # noqa: E402
    CONSTRAINT_SECTION, S01RequirementCapture,
    ingest_design_constraints as s01_ingest)
import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
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
from .test_s5_branch_and_premise import (                      # noqa: E402
    authorized_stage as _authorized_stage)
from .test_s02_s03b_integration import S02, _Canned                     # noqa: E402
from .test_s3_interface_readiness import _code_only                     # noqa: E402


def s01_response(must_reach=(), requirements=(), hard_constraints=()):
    """What the capture stage returns. No product noun and no quantity.

    `requirements` and `hard_constraints` are what the model made of the extra
    sentences a probe puts in the request - transcription and classification,
    which is what s01 asks a model to do. Whether any of it becomes a
    DesignConstraint is decided afterwards by code, and that is what B36-B39
    are about."""
    return {
        "source_clauses": [{"id": "SRC-0001", "verbatim": "a synthetic request",
                            "locator": "L1", "quantity_kinds": [],
                            "directionality": "none"}],
        "requirements": [{"id": "REQ-0001",
                          "statement_verbatim": "a synthetic request",
                          "kind": "FUNCTIONAL", "verification_kind": "STRUCTURAL",
                          "observable_verbatim": "it holds", "source_locator": "L1",
                          "quantity_class": "NONE"}] + list(requirements),
        "scenarios": [{"id": "SCN-0001", "name": "use", "kind": "OPERATION",
                       "system_boundary": "the product inside, the surface it "
                                          "stands on outside",
                       "actors": ["ACT-0001"], "environment": "indoor"},
                      {"id": "SCN-IDLE", "name": "idle", "kind": "OPERATION",
                       "system_boundary": "the product inside, the surface it "
                                          "stands on outside",
                       "actors": ["ACT-0001"], "environment": "indoor"}],
        "actors": [{"id": "ACT-0001", "name": "the operator",
                    "must_reach": list(must_reach)}],
        "freedoms": [], "ambiguities": [], "assumptions": [],
        "hard_constraints": list(hard_constraints),
    }


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
                blocked=None, depends=None, path_kind="RIGID", demand=0):
    """s03b for the same mechanism: what discharges the effect, how the load is
    routed through the declared interfaces, and how it goes together."""
    rels = []
    # NO RELATION BY DEFAULT. There used to be one, forced in because
    # `candidate_engineering_evidence` demanded the constraint-relation role be
    # non-empty - a fixture inventing evidence to get past an input boundary,
    # which is a fixture testing the boundary rather than the mechanism. The
    # boundary was the defect and is fixed; a mechanism that blocks nothing is an
    # ordinary mechanism.
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
    # THE DEMANDED STATE CHANGE, symbolically. `demand` is the index of the
    # joint that has to turn for the mechanism to get from its first
    # configuration to its second; `None` is a mechanism asked for no state
    # change at all, which is an ordinary mechanism and not an omission.
    demanded = [] if demand is None else [
        {"id": "TRQ-0%s" % sfx,
         "from_configuration": "CFG-C0%s" % sfx,
         "to_configuration": "CFG-C1%s" % sfx,
         "required_relative_motions": [{"joint": "JNT-%d%s" % (demand, sfx),
                                        "dof": "RZ"}]}]
    return {
        "transition_requirements": demanded,
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


def side_of(direction):
    """The `access_side` a step must state for its body to MOVE along
    `direction`: the axis word on the opposite side. s04a derives the insertion
    vector from the side s03 states, so a fixture that wants a part to travel
    along +X has its step arrive from -X."""
    (i, v), = [(i, v) for i, v in enumerate(direction) if v]
    return ("-" if v > 0 else "+") + "XYZ"[i]


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
        # No `assembly_directions`: the insertion vector is DERIVED by s04a
        # from each step's `access_side`, not asked of the model. A fixture
        # that wants a body to travel some way states the side it arrives from.
        "elimination": {"eliminated": eliminated,
                        "reason": "no consistent arrangement" if eliminated else None},
    }


def motion(sfx, joint, moving, coords=(0, 90), configs=("C0", "C1"),
           changed=None, transition=True, realizes=None):
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
        # NO ENDPOINTS HERE. Which two states a path runs between is the
        # requirement's statement, and this consumer names the requirement.
        out["transitions"] = [{"id": "TRN-%s" % sfx,
                               "realizes_requirement": (realizes if realizes
                                                        else "TRQ-0%s" % sfx),
                               "moving_groups": [moving],
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

    def seed(self, profile=None, must_reach=(), requirements=(),
             hard_constraints=()):
        """S01 THROUGH ITS REAL INVOCATION, profile and all.

        The requirement material used to be hand-written into state, which is
        fine for probing s03 and useless for probing an s01 ingress: a test that
        inserts the entity it is checking for proves the insertion. Everything
        below now arrives the way the pipeline makes it.

        `must_reach` is the reach DEMAND and defaults to none. An empty list is
        a value - this actor reaches for nothing - and the generic fixture
        placeholder used to fill it with prose, which read as a demand and made
        every clean mechanism NOT_ESTABLISHED on reach.
        """
        s = DesignState(run_id="feasibility")
        out = S01RequirementCapture().invoke(
            _Canned(s01_response(list(must_reach), requirements,
                                 hard_constraints)), s, s.run_id,
            {"request_text": "a synthetic request", "design_profile": profile})
        self.assertIsNotNone(out.patch, out.problems)
        s.apply(out.patch)
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
        self.last_s04a = oa
        if apply_b:
            ob = S04BPlacementAndMotion().invoke(
                provider, state, state.run_id, {"candidate": "CND-%s" % sfx},
                attempt=2, invocation=inv)
            self.assertIsNotNone(ob.patch, ob.problems)
            state.apply(ob.patch)
            # KEPT SO THE PRODUCER CAN BE ASKED WHAT IT SAID. Some properties
            # are about the pass that wrote the numbers rather than about the
            # state they became, and reading them off the state cannot tell a
            # response that declared a problem from one that did not.
            self.last_s04b = ob
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

    def fourbar(self, state=None, sfx="B", s04a=None):
        state = state if state is not None else self.seed()
        self.candidates(state)
        pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
        return self.branch(
            state, sfx, topology(sfx, 4, pairs),
            realization(sfx, hops=(0, 1), steps=(0,), demand=3),
            s04a if s04a is not None else
            arrangement({k.replace("B", sfx): v for k, v in FOURBAR_BOXES.items()},
                        steps=["ASY-0%s" % sfx]),
            # A SMALL ROTATION. The four-bar is judged on the same rules as the
            # hinge; sweeping a bar through the frame would be testing the probe.
            motion(sfx, "JNT-3%s" % sfx, _group(0, sfx), coords=(0, 10)))

    def candidates(self, state, payload=None, suffixes=("A", "B")):
        if state.family("Candidate"):
            return
        payload = json.loads(json.dumps(payload if payload is not None else S02))
        template = payload["candidates"][0]
        payload["candidates"] = [dict(template, id="CND-%s" % s,
                                      summary="alternative %s" % s)
                                 for s in suffixes]
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

    def revise(self, state, op, stage=None):
        state.apply(StagePatch(
            patch_id="rev-%d" % len(state.applied_patches), run_id=state.run_id,
            stage_id=stage or _authorized_stage(state, op), stage_attempt=9,
            parent_state_hash=state.state_hash(),
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

    def test_B4_a_declared_distinctness_that_is_not_realized_is_not_established(self):
        """Two configurations declared to differ, realized at the same
        coordinate. A positive contradiction: the design says the mechanism is
        in two states and the numbers say it is in one.

        UNIT A. OLD ASSUMPTION: the domain's FAIL made the candidate
        INFEASIBLE. NEW INVARIANT: the coordinates are s04b's, and s04b may
        state others without changing the principle - a repairable
        contradiction that leaves the MOTION_REALIZED fact of the required
        minimum unestablished. The domain keeps its FAIL; the candidate is
        NOT_ESTABLISHED, never INFEASIBLE.

        THE CONTRADICTION IS PUT INTO STATE BY A REVISION, because s04b refuses
        to author one: realizing declared distinctness is that pass's
        responsibility and a response contradicting it writes no realization at
        all. The evaluator's rule still holds and still has to be tested - a
        coordinate superseded afterwards, or evidence older than that gate, can
        present exactly this - and what must NOT happen is a producer admitting
        it and the mechanism being convicted for its author's mistake.
        """
        basis = {"CFG-C0A": [{"joint": "JNT-0A", "dof": "RZ",
                              "differs_from": ["CFG-C1A"]}]}
        state = self.hinge(s03a=topology("A", 2, [(0, 1)], basis=basis))
        self.revise(state, Op("SUPERSEDE", "State", "STA-CFG-C1A",
                              {"joint_coordinates": {"JNT-0A": 0}}, "t",
                              reason="the coordinate was revised to the other's"))
        out = self.assess(state)
        self.assertEqual(s07.FAIL, self.domain(out, "required_configurations").status)
        self.assertIn("DECLARED_DISTINCTNESS_NOT_REALIZED",
                      self.domain(out, "required_configurations").reason_codes)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        self.assertNotEqual(s07.INFEASIBLE, out.status)

    def test_B4b_a_transition_that_moves_what_it_did_not_declare_is_not_established(self):
        """UNIT A: the same shape as B4 - s04b's own declaration against
        s04b's own numbers, repairable by s04b, negating MOTION_REALIZED."""
        state = self.hinge(s04b=motion("A", "JNT-0A", _group(1, "A"), changed=[]))
        out = self.assess(state)
        self.assertEqual(s07.FAIL, self.domain(out, "motion_and_transitions").status)
        self.assertIn("UNDECLARED_COORDINATE_CHANGE",
                      self.domain(out, "motion_and_transitions").reason_codes)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)

    def test_B5_a_required_transition_that_is_absent_is_not_established(self):
        """NOT_APPLICABLE would be the wrong answer and the dangerous one: the
        design declares that a state change is required, so the question is
        asked and unanswered rather than not asked."""
        basis = {"CFG-C0A": [{"joint": "JNT-0A", "dof": "RZ",
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

    def test_B7_a_terminus_that_is_not_the_declared_site_is_not_established(self):
        """UNIT A. OLD ASSUMPTION: a route closing at the wrong site made the
        candidate INFEASIBLE. NEW INVARIANT: the route is s03b's, and s03b may
        re-route without changing the principle; the contradiction leaves the
        REACTION_ROUTE fact unestablished and is an owner revision, not an
        impossibility. The domain keeps its FAIL."""
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
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        self.assertNotEqual(s07.INFEASIBLE, out.status)

    def test_B7b_a_terminus_inside_the_product_is_not_established(self):
        """UNIT A: as B7 - the route may be re-authored to close outside."""
        state = self.hinge(s03b=realization("A", terminates="RSR-0001"))
        self.revise(state, Op("SUPERSEDE", "ReactionSiteRequirement", "RSR-0001",
                              {"boundary_side": "INTERNAL"}, "t",
                              reason="the boundary moved"), stage="s02")
        out = self.assess(state)
        v = self.domain(out, "load_reaction_closure")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("TERMINAL_SITE_INTERNAL", v.reason_codes)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)

    def test_B8_a_positive_gap_on_the_load_route_is_not_established(self):
        """A GAP IS PROOF, where an overlap is not: the real bodies are smaller
        than their boxes, so boxes that are apart are bodies that are apart.

        UNIT A. OLD ASSUMPTION: proof of a gap was proof of infeasibility.
        NEW INVARIANT: it is proof that THIS arrangement does not carry the
        load - s04a's placement, which s04a may revise - so the ARRANGEMENT
        fact is unestablished and the candidate NOT_ESTABLISHED. Both domains
        keep their FAIL."""
        state = self.hinge(
            s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                              "BOD-G1A": ([9, 0, 0], [1, 1, 1])},
                             steps=["ASY-0A"]))
        out = self.assess(state)
        v = self.domain(out, "load_reaction_closure")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("HOP_BODIES_APART", v.reason_codes)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        self.assertEqual(s07.FAIL, self.domain(out, "spatial_realization").status,
                         "the topology connects them and they are apart")

    #: THE RETIRED AUTHORITY. `mobility_disposition` decided whether a demanded
    #: motion was possible by reading the six-DOF grid, and `transition_
    #: reachability` replaced it. The three probes it had here are kept as their
    #: own inversions: what USED to decide the verdict, proving it no longer
    #: does. The new domain's own behaviour is in
    #: `test_s7_transition_reachability`.

    def test_B9_a_withdrawn_disposition_no_longer_decides_reachability(self):
        """MobilityExpectation is still valid evidence about a stable state and
        is no longer the authority on whether a change can happen. It says what
        is known about a cell of a grid; the demand says which relative joint
        motion has to occur, and only the second is what a transition needs."""
        state = self.hinge()
        before = self.domain(self.assess(state, apply_patch=False),
                             "transition_reachability")
        mex = [m for m in state.family("MobilityExpectation")][0]
        kept = [dict(d, disposition="UNDISPOSITIONED",
                     missing="withdrawn for this probe", by_joint=None)
                if d["rigid_group"] == _group(1, "A") and d["dof"] == "RZ" else d
                for d in mex["dispositions"]]
        self.revise(state, Op("SUPERSEDE", "MobilityExpectation", mex["entity_id"],
                              {"dispositions": kept}, "t",
                              reason="withdraw the disposition"), stage="s03")
        after = self.domain(self.assess(state), "transition_reachability")
        self.assertEqual(s07.PASS, before.status, before.summary)
        self.assertEqual((before.status, tuple(before.reason_codes)),
                         (after.status, tuple(after.reason_codes)))

    def test_B10_a_group_dof_block_is_not_a_relative_motion_block(self):
        """A ConstraintRelation whose `blocked_dofs` names the DOF the demanded
        joint turns, and which says nothing about relative joint motion.

        This was INFEASIBLE. `blocked_dofs` is about a GROUP's mobility and
        `blocked_relative_motions` is about a JOINT's relative motion; they are
        separate statements, and convicting on the first was matching a held
        group against a joint it happens to touch. A relation that has not said
        which relative motion it removes has not contradicted one."""
        state = self.hinge(s03b=realization(
            "A", blocked=[(_group(1, "A"), ["RZ"], "CFG-C0A")]))
        out = self.assess(state)
        v = self.domain(out, "transition_reachability")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertNotEqual(s07.INFEASIBLE, out.status)

    def test_B11_a_static_candidate_is_not_a_context_failure(self):
        """No transition and no demanded state change: the design poses no
        motion question, and NOT_APPLICABLE is the whole answer."""
        state = self.hinge(s03b=realization("A", demand=None),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       transition=False))
        out = self.assess(state)
        for name in ("motion_and_transitions", "transition_reachability"):
            self.assertEqual(s07.NOT_APPLICABLE, self.domain(out, name).status, name)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        self.assertEqual([], out.problems)


# =====================================================================
# B12-B13 - a model's conclusion is evidence, never a verdict
# =====================================================================
class TestModelLocalFindings(_Feas):

    def concluding_about(self, region):
        """s04a's conclusion about the REGION the actor needs. The harness's
        default conclusion is about a body, and a conclusion about some body is
        not a conclusion about this actor's demand."""
        arr = arrangement({k: v for k, v in HINGE_BOXES.items()},
                          steps=["ASY-0A"], region=region, actor="ACT-0001")
        for r in arr["reach_results"]:
            r["target"] = region
        return arr

    def test_B12_a_reach_result_is_the_contracted_pre_selection_basis(self):
        """THIS REVERSED. It used to assert that a ReachResult could neither
        pass nor fail the domain, and that s04a's conclusion must not even be a
        premise of the verdict - and the domain then could not PASS on any
        input, because nothing anywhere is contracted to produce the
        "deterministic reach basis" it waited for. s04a's contract is an
        arrangement "sufficient to decide reach", and the ReachResult is that
        decision, AUTHORITATIVE. Before selection it is the basis; the evidence
        level is written on the verdict beside the PASS, not hidden under a
        NOT_ESTABLISHED that meant "we never looked".

        The harness's actor reaches for nothing, so the demand is seeded.
        """
        state = self.seed(must_reach=["the latch"])
        self.candidates(state)
        self.hinge(
            state=state,
            s03a=dict(topology("A", 2, [(0, 1)]),
                      functional_regions=[{"id": "FRG-A", "role": "ACCESS",
                                           "owning_bodies": ["BOD-G0A"],
                                           "required_by_actors": ["ACT-0001"]}]),
            s04a=self.concluding_about("FRG-A"))
        self.assertTrue(state.family("ReachResult"), "the probe is not probing")
        out = self.assess(state)
        v = self.domain(out, "reach")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn(s07.MODEL_LOCAL_POSITIVE, v.reason_codes,
                      "the evidence level is part of the record")
        for r in state.family("ReachResult"):
            self.assertIn(r["entity_id"], v.premises,
                          "the conclusion the verdict rests on is its premise")

    def test_B13_an_elimination_record_alone_cannot_make_it_infeasible(self):
        """UNIT A. OLD ASSUMPTION: s04a's elimination weakened the candidate
        to NOT_ESTABLISHED. NEW INVARIANT: it weakens the DOMAIN, and is a
        REPAIRABLE_S04 obligation on a FEASIBLE_FOR_SELECTION answer - a
        model's opinion about an arrangement the same pass may revise names no
        required-minimum fact and proves nothing about the mechanism."""
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            eliminated=True))
        self.assertTrue([e for e in state.family("EliminationRecord")
                         if e.get("eliminated")], "the probe is not probing")
        out = self.assess(state)
        v = self.domain(out, "spatial_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn(s07.MODEL_LOCAL_NEGATIVE, v.reason_codes)
        self.assertNotEqual(s07.INFEASIBLE, out.status,
                            "a model-local elimination became the pipeline's verdict")
        self.assertEqual(s07.FEASIBLE, out.status)


# =====================================================================
# B14-B16 - hard requirements, and what makes one evaluable
# =====================================================================
class TestHardRequirements(_Feas):

    def constraint(self, state, kind, **params):
        self.add(state, "s01", "DesignConstraint", "DSC-P001", kind=kind,
                 statement="a stated hard requirement", source="profile",
                 evaluability="MACHINE_EVALUABLE", parameters=params or None,
                 blocks_selection=True)
        return state

    def status_of(self, out, cid="DSC-P001"):
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
        """The two ambiguities a canonical write can still produce.

        A third case used to be here: an ABSOLUTE basis whose `absolute` gave a
        unit and no per_unit, expecting SCALE_FACTOR_MISSING. That state is no
        longer constructible - `ReferenceScale.conditional_requirements` rejects
        it at the write boundary and `absolute` is not extendable, so there is no
        canonical path to it. Asserting downstream behaviour for an unreachable
        state would be asserting behaviour that cannot occur.

        `test_B16c` below now makes the stronger claim in its place.
        """
        for scale, code in (
                (self.hinge(), "SCALE_NOT_ABSOLUTE"),
                (self._absolute(unit="in"), "UNIT_AMBIGUOUS")):
            state = self.constraint(scale, "MAX_OVERALL_DIMENSION",
                                    axis="ANY", limit=10, unit="mm")
            status, codes, _used, why = self.status_of(self.assess(state))
            self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
            self.assertIn(code, codes)

    def test_B16c_a_scale_with_no_factor_cannot_be_written_at_all(self):
        """What replaced the SCALE_FACTOR_MISSING case, and why it is stronger.

        Downstream reporting "I cannot evaluate this" was the second-best
        outcome. The best is that the unusable scale never enters state, because
        every consumer of it then reasons about a basis that can actually
        convert something.
        """
        from ver3.assy_v3.state.design_state import ContractError
        with self.assertRaises(ContractError) as raised:
            self.constraint(self._absolute(per_unit=None),
                            "MAX_OVERALL_DIMENSION", axis="ANY", limit=10,
                            unit="mm")
        self.assertIn("absolute_scale_is_structured", str(raised.exception))

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
                ("ReferenceScale", "SCL-CND-A",
                 {"basis": "ABSOLUTE",
                  "absolute": {"unit": "mm", "per_unit": 1.0}}),
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
            # THE TWO MobilityExpectations LEFT THIS SET when
            # `transition_reachability` replaced `mobility_disposition`. The
            # grid is still in the view and still valid evidence about what is
            # known of a stable state; it is no longer read by any domain, so it
            # is no longer a premise of any verdict - which is the same rule
            # applied honestly, not a gap. TRQ-0A took its place: the demand is
            # what the reachability question is asked against.
            domains | {"CND-A", "ASY-0A", "BOD-G0A", "BOD-G1A", "CFG-C0A",
                       "CFG-C1A", "ENV-G0A", "ENV-G1A", "IFC-0A", "JNT-0A",
                       "LC-0001", "LDP-A", "TRQ-0A",
                       "PEO-0001", "PHI-A", "RGP-G0A", "RGP-G1A", "RSR-0001",
                       "SCL-CND-A", "STA-CFG-C0A", "STA-CFG-C1A",
                       "SWV-TRN-A-RGP-G1A", "TRN-A"},
            carried)
        # And what is visible, was not computed from, and is therefore absent:
        # the requirement the obligation came from, the scenario, the actor, the
        # obligation it addresses, and s04a's own elimination finding.
        for unused in ("REQ-0001", "SCN-0001", "ACT-0001", "OBL-0001",
                       "ELM-CND-A"):
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
        """THE DEMAND IS NAMED; THE MISSING ANSWER IS NOT.

        A TransitionRequirement is a present fact and the reason the domain is
        unsatisfied, so withdrawing it must cost this verdict its authority. The
        transition that would have realized it does not exist and gets no id:
        inventing one would make a missing fact look like a present one.

        The demand used to be a configuration's `distinguishing_basis`. Two
        states declared to differ are two states that differ - which
        `required_configurations` verifies - and not a statement that one is
        reachable from the other."""
        state = self.hinge(s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       transition=False))
        out = self.assess(state)
        v = self.domain(out, "motion_and_transitions")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("REQUIRED_TRANSITION_MISSING", v.reason_codes)
        self.assertEqual(["TRQ-0A"], v.premises)
        op = next(o for o in out.patch.operations
                  if o.entity_id == "FDA-CND-A-MOTION-AND-TRANSITIONS")
        self.assertEqual(["CND-A", "TRQ-0A"], sorted(op.premise_refs))
        # The withdrawn demand costs the verdict its standing, which is what
        # naming it was for.
        self.revise(state, Op("SUPERSEDE", "TransitionRequirement", "TRQ-0A",
                              {"required_relative_motions": [
                                  {"joint": "JNT-0A", "dof": "TX"}]}, "t",
                              reason="the change asked for was withdrawn"),
                    stage="s03")
        self.assertEqual("STALE",
                         self.val(state, "FDA-CND-A-MOTION-AND-TRANSITIONS"))


# =====================================================================
# B26-B27 - a hard requirement reaches the evaluator, a wish does not
# =====================================================================
PROFILE = {
    "design_constraints": [
        {"kind": "MAX_OVERALL_DIMENSION",
         "statement": "it must fit through a standard doorway",
         "parameters": {"axis": "ANY", "limit": 100, "unit": "mm"},
         "blocks_selection": True},
        {"kind": "MATERIAL_CLASS_ONLY",
         "statement": "every manufactured part must be plastic",
         "parameters": {"material_class": "PLASTIC"}, "blocks_selection": True},
    ],
    "selection_preferences": {"part_count": {"objective": "MINIMIZE",
                                             "priority": "HIGH"}},
}


class TestConstraintIngress(_Feas):

    def test_B26_a_stated_hard_requirement_reaches_the_evaluator(self):
        """THE WHOLE CHAIN, not an entity typed into state. The profile goes in
        as an s01 input, s01's own invocation emits the DesignConstraint, the
        feasibility view selects it because the responsibility declares the
        role, and the evaluator answers it."""
        state = self.hinge(state=self.seed(profile=PROFILE),
                           s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            basis="ABSOLUTE",
                                            absolute={"unit": "mm",
                                                      "per_unit": 10.0}))
        made = {c["entity_id"]: c for c in state.family("DesignConstraint")}
        self.assertEqual(["DSC-P001", "DSC-P002"], sorted(made))
        self.assertEqual("s01", state.entities["DSC-P001"]["_created_by"])
        self.assertEqual("s01:profile_ingest",
                         state.entities["DSC-P001"]["_provenance"])
        self.assertEqual("MAX_OVERALL_DIMENSION", made["DSC-P001"]["kind"])

        out = self.assess(state)
        visible = {e["entity_id"] for e in out.consumer_view["entities"]}
        self.assertIn("DSC-P001", visible, "the view cannot see the requirement")
        status = {c.get("entity_id"): s for c, s, _c, _u, _w in out.compliance}
        self.assertEqual({"DSC-P001": s07.SATISFIED,
                          "DSC-P002": s07.NOT_YET_EVALUABLE}, status)
        hrc = next(o for o in out.patch.operations
                   if o.entity_id == "HRC-CND-A-DSC-P001")
        self.assertIn("DSC-P001", hrc.premise_refs)
        self.assertIn("CND-A", hrc.premise_refs)
        self.assertIn("SCL-CND-A", hrc.premise_refs)

    def test_B26b_nothing_is_completed_that_the_user_left_incomplete(self):
        """A limit with no unit stays a limit with no unit. Inferring mm would
        answer the requirement from a number nobody supplied."""
        state = self.seed(profile={"design_constraints": [
            {"kind": "MAX_OVERALL_DIMENSION", "statement": "it must be small",
             "parameters": {"axis": "ANY", "limit": 100}}]})
        self.assertEqual({"axis": "ANY", "limit": 100},
                         state.entities["DSC-P001"]["parameters"])
        self.hinge(state=state, s04a=arrangement(
            HINGE_BOXES, steps=["ASY-0A"], basis="ABSOLUTE",
            absolute={"unit": "mm", "per_unit": 10.0}))
        status, codes, _u, _w = TestHardRequirements.status_of(
            self, self.assess(state))
        self.assertEqual(s07.NOT_YET_EVALUABLE, status)
        self.assertIn("UNIT_AMBIGUOUS", codes)

    def test_B26c_a_statement_without_parameters_is_for_a_person(self):
        state = self.seed(profile={"design_constraints": [
            {"kind": "LOAD_CAPACITY", "statement": "it must hold a full load"}]})
        self.assertEqual("HUMAN_EVALUABLE",
                         state.entities["DSC-P001"]["evaluability"])

    def test_B27_a_preference_is_not_ingested(self):
        """THE SECTION IS NEVER READ. Not filtered out afterwards - the ingester
        names one key, and a wish that became a DesignConstraint could make a
        candidate ineligible for being the kind somebody likes less."""
        state = self.seed(profile=PROFILE)
        for c in state.family("DesignConstraint"):
            self.assertNotIn("part_count", json.dumps(c))
        self.assertEqual([], state.family("SelectionProfile"))
        source = __import__("inspect").getsource(s01_ingest)
        self.assertNotIn("selection_preferences", source)
        self.assertNotIn("preference", source.lower().split("Deciding")[0]
                         .split("A selection")[0] or "")

    def test_B27b_a_profile_with_only_preferences_yields_nothing(self):
        state = self.seed(profile={"selection_preferences": {
            "part_count": {"objective": "MINIMIZE", "priority": "HIGH"}}})
        self.assertEqual([], state.family("DesignConstraint"))

    def test_B27c_an_entry_with_no_kind_is_not_invented_into_one(self):
        state = self.seed(profile={"design_constraints": [
            {"statement": "something the user typed"}]})
        self.assertEqual([], state.family("DesignConstraint"))


# =====================================================================
# B28-B32 - demand, address and typed semantics
# =====================================================================
class TestDemandDrivenApplicability(_Feas):

    def test_B28_a_restraint_holding_elsewhere_blocks_no_source(self):
        """SAME GROUP, SAME DOF, TWO CONFIGURATIONS, ONE RESTRAINT.

        The relation holds in the state the change does NOT start from. A
        restraint is compared against the source of the change it is claimed to
        obstruct, so one active somewhere else obstructs nothing here - and the
        record it is active in is not a premise of this verdict, so revising it
        changes nothing.

        The rule this replaced compared cells of a grid and required the demanded
        DOF to be free in BOTH endpoints, which convicted every mechanism that is
        held in its stable states and released during the change between them.
        """
        state = self.hinge(s03b=realization(
            "A", blocked=[(_group(1, "A"), ["RZ"], "CFG-C1A")]))
        out = self.assess(state)
        v = self.domain(out, "transition_reachability")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("TRQ-0A", v.premises)
        self.assertNotIn("CRL-0A", v.premises)
        self.revise(state, Op("SUPERSEDE", "ConstraintRelation", "CRL-0A",
                              {"blocked_dofs": ["TX"]}, "t", reason="probe"),
                    stage="s03")
        self.assertEqual("STANDING",
                         self.val(state, "FDA-CND-A-TRANSITION-REACHABILITY"))
        # The demand IS a premise, and withdrawing what it asks for costs the
        # verdict its standing.
        self.revise(state, Op("SUPERSEDE", "TransitionRequirement", "TRQ-0A",
                              {"required_relative_motions": [
                                  {"joint": "JNT-0A", "dof": "TX"}]}, "t",
                              reason="the motion asked for changed"), stage="s03")
        self.assertEqual("STALE",
                         self.val(state, "FDA-CND-A-TRANSITION-REACHABILITY"))

    def test_B29_a_reach_demand_with_no_realization_is_not_established(self):
        """The actor must reach something and this candidate declares no access
        region at all. NOT_APPLICABLE would have let the candidate excuse itself
        by ignoring the requirement."""
        state = self.hinge(state=self.seed(must_reach=["the inside"]))
        self.assertEqual([], [r for r in state.family("FunctionalRegion")],
                         "the probe is not probing")
        out = self.assess(state)
        v = self.domain(out, "reach")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("REACH_REALIZATION_ABSENT", v.reason_codes)
        self.assertEqual(["ACT-0001"], v.premises)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)

    def test_B29b_no_actor_demand_and_no_region_is_not_applicable(self):
        v = self.domain(self.assess(self.hinge()), "reach")
        self.assertEqual(s07.NOT_APPLICABLE, v.status)

    def test_B30_a_motion_demand_with_no_realization_is_not_established(self):
        """A typed effect obligation that cannot be discharged without movement,
        and nothing that moves. Both motion domains are applicable."""
        s02 = json.loads(json.dumps(S02))
        s02["physical_effect_obligations"][0]["effect"] = "TRANSMIT_MOTION"
        state = self.seed()
        self.candidates(state, payload=s02)
        r = realization("A", demand=None)
        r["physical_interactions"][0]["effect"] = "TRANSMIT_MOTION"
        self.hinge(state=state, s03b=r,
                   s04b=motion("A", "JNT-0A", _group(1, "A"), transition=False))
        self.assertEqual([], state.family("Transition"), "the probe is not probing")
        out = self.assess(state)
        for name, code in (("motion_and_transitions", "REQUIRED_TRANSITION_MISSING"),
                           ("transition_reachability",
                            "MOTION_DEMANDED_WITHOUT_TRANSITION_REQUIREMENT")):
            v = self.domain(out, name)
            self.assertEqual(s07.NOT_ESTABLISHED, v.status, name)
            self.assertIn(code, v.reason_codes)
            self.assertEqual(["PEO-0001"], v.premises, name)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)

    def test_B30b_a_non_motion_obligation_demands_no_motion(self):
        """PREVENT_MOTION is not this question asked backwards, and
        TRANSMIT_FORCE is not this question at all."""
        for effect in ("TRANSMIT_FORCE", "PREVENT_MOTION", "LOCATE"):
            s02 = json.loads(json.dumps(S02))
            s02["physical_effect_obligations"][0]["effect"] = effect
            state = self.seed()
            self.candidates(state, payload=s02)
            r = realization("A", demand=None)
            r["physical_interactions"][0]["effect"] = effect
            self.hinge(state=state, s03b=r,
                       s04b=motion("A", "JNT-0A", _group(1, "A"), transition=False))
            out = self.assess(state)
            self.assertEqual(s07.NOT_APPLICABLE,
                             self.domain(out, "motion_and_transitions").status,
                             effect)

    def test_B31_an_interaction_that_does_something_else_discharges_nothing(self):
        """It names the obligation and it does not produce the effect. Pointing
        at a demand is not answering it."""
        r = realization("A")
        r["physical_interactions"][0]["effect"] = "LOCATE"
        state = self.hinge(s03b=r)
        out = self.assess(state)
        v = self.domain(out, "physical_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("EFFECT_TYPE_MISMATCH", v.reason_codes)
        self.assertNotEqual(s07.FEASIBLE, out.status)
        # Both facts are named: the demand and the thing that failed to answer it.
        self.assertEqual(["PEO-0001", "PHI-A"], sorted(v.premises))

    def test_B31b_the_matching_effect_still_discharges(self):
        v = self.domain(self.assess(self.hinge()), "physical_realization")
        self.assertEqual(s07.PASS, v.status)

    def test_B32_a_clearance_pair_that_overlaps_is_not_established(self):
        """CLEARANCE is the design PROMISING these two stay apart. Treating it
        as an overlap exemption turned the strongest statement about a pair into
        the weakest."""
        top = topology("A", 2, [(0, 1)])
        top["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        state = self.hinge(s03a=top)
        out = self.assess(state)
        v = self.domain(out, "gross_interference")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("CLEARANCE_PAIR_OVERLAPS", v.reason_codes)
        self.assertNotEqual(s07.FAIL, v.status, "an overlap is not a collision")
        # UNIT A. OLD ASSUMPTION: the unestablished overlap made the candidate
        # NOT_ESTABLISHED. NEW INVARIANT: the domain stays unestablished and
        # the candidate is feasible with the overlap as an s04a obligation.
        self.assertEqual(s07.FEASIBLE, out.status)

    def test_B32b_a_clearance_pair_that_is_clear_passes(self):
        """The exemption question and the geometry question are different: a
        CLEARANCE pair held apart is the promise kept."""
        top = topology("A", 2, [(0, 1)])
        top["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        state = self.hinge(s03a=top,
                           s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                                             "BOD-G1A": ([9, 0, 0], [1, 1, 1])},
                                            steps=["ASY-0A"]),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       coords=(0, 0)))
        v = self.domain(self.assess(state), "gross_interference")
        self.assertEqual(s07.PASS, v.status, v.summary)

    def test_B32c_an_intended_contact_pair_is_still_exempt(self):
        """A pair declared to touch is supposed to overlap as boxes. Reporting
        it would be reporting the design."""
        v = self.domain(self.assess(self.hinge()), "gross_interference")
        self.assertEqual(s07.PASS, v.status, v.summary)


# =====================================================================
# B33-B34 - a dimension is of the whole thing or of nothing
# =====================================================================
class TestDimensionalCompleteness(_Feas):

    def dimensional(self, boxes, axis="ANY", limit=100, unit="mm",
                    absolute={"unit": "mm", "per_unit": 10.0}, basis="ABSOLUTE"):
        profile = {"design_constraints": [
            {"kind": "MAX_OVERALL_DIMENSION", "statement": "it must fit",
             "parameters": {"axis": axis, "limit": limit, "unit": unit}}]}
        state = self.hinge(state=self.seed(profile=profile),
                           s04a=arrangement(boxes, steps=["ASY-0A"],
                                            basis=basis, absolute=absolute))
        out = self.assess(state)
        for c, status, codes, used, why in out.compliance:
            if c["entity_id"] == "DSC-P001":
                return status, codes, used, why
        raise AssertionError("no compliance record")

    def test_B33_a_body_without_an_extent_makes_it_unevaluable(self):
        """One of two bodies placed. The measured subset was smaller than the
        product, so the more incomplete the arrangement the more comfortably it
        passed."""
        status, codes, used, why = self.dimensional(
            {"BOD-G0A": ([0, 0, 0], [1, 1, 1])})
        self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
        self.assertIn("EXTENT_INCOMPLETE", codes)
        self.assertIn("BOD-G1A", used, "the body that has no extent is the fact")

    def test_B33b_every_body_placed_decides_it(self):
        status, codes, _u, why = self.dimensional(HINGE_BOXES)
        self.assertEqual(s07.SATISFIED, status, why)
        self.assertIn("WITHIN_OVERALL_DIMENSION", codes)
        status, codes, _u, why = self.dimensional(HINGE_BOXES, limit=10)
        self.assertEqual(s07.VIOLATED, status, why)
        self.assertIn("OVERALL_DIMENSION_EXCEEDED", codes)

    def test_B34_an_unrecognised_axis_is_not_silently_x(self):
        status, codes, _u, why = self.dimensional(HINGE_BOXES, axis="DIAGONAL")
        self.assertEqual(s07.NOT_YET_EVALUABLE, status)
        self.assertIn("AXIS_NOT_RECOGNIZED", codes)
        self.assertIn("DIAGONAL", why)

    def test_B34b_each_recognised_axis_measures_its_own_span(self):
        """X spans 3.5 units and Y spans 2; at 10 mm each the same limit
        separates them. A fallback to X would have made them agree."""
        self.assertEqual(s07.VIOLATED,
                         self.dimensional(HINGE_BOXES, axis="X", limit=30)[0])
        self.assertEqual(s07.SATISFIED,
                         self.dimensional(HINGE_BOXES, axis="Y", limit=30)[0])

    def test_B34c_an_ambiguous_or_relative_scale_decides_nothing(self):
        """The reachable ambiguities. See `test_B16c` for the case that is now
        refused at the write boundary instead of tolerated downstream."""
        for kwargs, code in (
                ({"basis": "RELATIVE", "absolute": None}, "SCALE_NOT_ABSOLUTE"),
                ({"absolute": {"unit": "in", "per_unit": 10.0}}, "UNIT_AMBIGUOUS")):
            status, codes, _u, why = self.dimensional(HINGE_BOXES, **kwargs)
            self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
            self.assertIn(code, codes)

    def test_B34d_a_scale_with_no_factor_is_refused_before_it_can_decide(self):
        from ver3.assy_v3.state.design_state import ContractError
        with self.assertRaises(ContractError):
            self.dimensional(HINGE_BOXES, absolute={"unit": "mm"})


# =====================================================================
# B36-B39, B54-B56 - a hard requirement stated in the REQUEST
# =====================================================================
def stated(requirement_id, statement, quantity_class, kind=None, parameters=None,
           locator="L2"):
    """One extra sentence in the request, as s01 captures it."""
    req = {"id": requirement_id, "statement_verbatim": statement,
           "kind": "FUNCTIONAL", "verification_kind": "STRUCTURAL",
           "observable_verbatim": statement, "source_locator": locator,
           "quantity_class": quantity_class}
    entry = ({"requirement": requirement_id, "kind": kind,
              "statement_verbatim": statement, "parameters": parameters}
             if kind else None)
    return req, entry


class TestSourceCapture(_Feas):
    """A hard requirement the user typed must not need a second file to survive."""

    def capture(self, *pairs, **kw):
        reqs = [r for r, _e in pairs]
        entries = [e for _r, e in pairs if e]
        return self.seed(requirements=reqs, hard_constraints=entries, **kw)

    def test_B36_a_material_requirement_in_the_request_survives(self):
        """No structured profile anywhere. The whole chain from the sentence to
        the compliance record, and the answer is about the evidence: nothing in
        the representation assigns a material yet."""
        state = self.capture(stated("REQ-0002", "All parts must be plastic.",
                                    "NONE", "MATERIAL_CLASS_ONLY",
                                    {"material_class": "PLASTIC"}))
        made = state.family("DesignConstraint")
        self.assertEqual(1, len(made), made)
        self.assertEqual("MATERIAL_CLASS_ONLY", made[0]["kind"])
        self.assertEqual("s01:source_capture",
                         state.entities[made[0]["entity_id"]]["_provenance"])
        self.assertEqual([], state.family("SelectionProfile"))

        self.hinge(state=state)
        out = self.assess(state)
        visible = {e["entity_id"] for e in out.consumer_view["entities"]}
        self.assertIn(made[0]["entity_id"], visible)
        status, codes, used, _why = TestHardRequirements.status_of(
            self, out, made[0]["entity_id"])
        self.assertEqual(s07.NOT_YET_EVALUABLE, status)
        self.assertIn("NO_MATERIAL_AUTHORITY", codes)

    def test_B37_a_stated_dimensional_limit_is_preserved_and_decided(self):
        """100 mm on a named axis, from the request alone."""
        state = self.capture(stated(
            "REQ-0002", "The assembled mechanism must be no wider than 100 mm.",
            "MAGNITUDE", "MAX_OVERALL_DIMENSION",
            {"axis": "X", "limit": 100, "unit": "mm"}))
        made = state.family("DesignConstraint")[0]
        self.assertEqual({"axis": "X", "limit": 100, "unit": "mm"},
                         made["parameters"], "the stated values changed")
        self.hinge(state=state, s04a=arrangement(
            HINGE_BOXES, steps=["ASY-0A"], basis="ABSOLUTE",
            absolute={"unit": "mm", "per_unit": 10.0}))
        status, _c, _u, why = TestHardRequirements.status_of(
            self, self.assess(state), made["entity_id"])
        self.assertEqual(s07.SATISFIED, status, why)

    def test_B37b_without_geometry_the_same_limit_decides_nothing(self):
        state = self.capture(stated(
            "REQ-0002", "It must be no wider than 100 mm.", "MAGNITUDE",
            "MAX_OVERALL_DIMENSION", {"axis": "X", "limit": 100, "unit": "mm"}))
        self.hinge(state=state)          # RELATIVE basis, as s04 leaves it
        status, codes, _u, why = TestHardRequirements.status_of(
            self, self.assess(state), "DSC-S001")
        self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
        self.assertIn("SCALE_NOT_ABSOLUTE", codes)

    def test_B37c_an_unstated_axis_is_never_invented(self):
        """"no wider than 100 mm" with no axis captured. The limit is preserved
        and the question stays open; choosing ANY would answer a different
        requirement, and a more permissive one."""
        state = self.capture(stated(
            "REQ-0002", "It must be no wider than 100 mm.", "MAGNITUDE",
            "MAX_OVERALL_DIMENSION", {"limit": 100, "unit": "mm"}))
        self.assertEqual({"limit": 100, "unit": "mm"},
                         state.entities["DSC-S001"]["parameters"])
        self.hinge(state=state, s04a=arrangement(
            HINGE_BOXES, steps=["ASY-0A"], basis="ABSOLUTE",
            absolute={"unit": "mm", "per_unit": 10.0}))
        status, codes, _u, why = TestHardRequirements.status_of(
            self, self.assess(state), "DSC-S001")
        self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
        self.assertIn("AXIS_NOT_RECOGNIZED", codes)

    def test_B38_a_preference_creates_no_constraint(self):
        """Both directions. The model classifying it correctly emits nothing;
        the model classifying it WRONGLY is refused by the kind vocabulary,
        which contains no way to say 'fewer would be nicer'."""
        state = self.capture(stated("REQ-0002", "Prefer fewer parts.", "NONE"))
        self.assertEqual([], state.family("DesignConstraint"))

        state = self.capture(stated("REQ-0002", "Prefer fewer parts.", "NONE",
                                    "MINIMIZE_PART_COUNT", {"objective": "MIN"}))
        self.assertEqual([], state.family("DesignConstraint"),
                         "a wish reached the hard-requirement family")

    def test_B39_ambiguous_prose_is_not_normalized_into_a_limit(self):
        """"Keep it reasonably compact" is a requirement with no quantity. The
        refusal is s01's OWN typed capture - quantity_class NONE - not this code
        reading the sentence."""
        state = self.capture(stated("REQ-0002", "Keep it reasonably compact.",
                                    "NONE", "MAX_OVERALL_DIMENSION", None))
        self.assertEqual([], state.family("DesignConstraint"))
        self.assertTrue([r for r in state.family("Requirement")
                         if r["entity_id"] == "REQ-0002"],
                        "the requirement itself was lost")

    def test_B39b_an_approximate_quantity_is_not_a_limit_either(self):
        """BAND, not MAGNITUDE. "approximately 100 mm" is not a limit anything
        can be checked against, and sharpening it is the one thing s01 exists to
        prevent."""
        state = self.capture(stated(
            "REQ-0002", "It should be approximately 100 mm wide.", "BAND",
            "MAX_OVERALL_DIMENSION", {"axis": "X", "limit": 100, "unit": "mm"}))
        self.assertEqual([], state.family("DesignConstraint"))

    def test_B39c_a_constraint_naming_no_requirement_is_not_ingested(self):
        """Traceability is a condition of existence, not a decoration."""
        state = self.seed(hard_constraints=[
            {"requirement": "REQ-NOWHERE", "kind": "MATERIAL_CLASS_ONLY",
             "statement_verbatim": "plastic", "parameters": {"material_class": "P"}}])
        self.assertEqual([], state.family("DesignConstraint"))

    def test_B54_a_source_constraint_points_back_at_its_sentence(self):
        state = self.capture(stated("REQ-0002", "All parts must be plastic.",
                                    "NONE", "MATERIAL_CLASS_ONLY",
                                    {"material_class": "PLASTIC"},
                                    locator="para 2"))
        made = state.entities["DSC-S001"]
        self.assertEqual(["REQ-0002"], made["derived_from_requirements"])
        self.assertEqual("para 2", made["source"])
        self.assertEqual("All parts must be plastic.", made["statement"])
        self.assertIn("REQ-0002", state.entities["REQ-0002"]["entity_id"])

    def test_B55_the_constraint_does_not_depend_on_a_profile(self):
        """THE BLOCKER, stated as an equality. The same request with and without
        a structured profile must not differ in what it demands of the design."""
        pair = stated("REQ-0002", "All parts must be plastic.", "NONE",
                      "MATERIAL_CLASS_ONLY", {"material_class": "PLASTIC"})
        without = self.capture(pair)
        with_profile = self.capture(pair, profile={"design_constraints": [
            {"kind": "PROHIBITED_ENERGY_SOURCE", "statement": "no mains",
             "parameters": {"source": "MAINS_ELECTRICAL"}}]})
        kinds = lambda s: sorted(c["kind"] for c in s.family("DesignConstraint"))
        self.assertEqual(["MATERIAL_CLASS_ONLY"], kinds(without))
        self.assertEqual(["MATERIAL_CLASS_ONLY", "PROHIBITED_ENERGY_SOURCE"],
                         kinds(with_profile),
                         "the two channels do not compose")

    def test_B56_changing_a_preference_changes_nothing(self):
        """Not "the preference is filtered" - the whole downstream answer is
        identical, entity for entity."""
        def run(wish):
            state = self.capture(
                stated("REQ-0002", "All parts must be plastic.", "NONE",
                       "MATERIAL_CLASS_ONLY", {"material_class": "PLASTIC"}),
                stated("REQ-0003", wish, "NONE"),
                profile={"selection_preferences": {"part_count": {
                    "objective": "MINIMIZE", "priority": "HIGH"}}})
            self.hinge(state=state)
            out = self.assess(state, apply_patch=False)
            return (sorted(c["kind"] for c in state.family("DesignConstraint")),
                    [(c.get("entity_id"), s) for c, s, _c, _u, _w in out.compliance],
                    out.status,
                    {v.domain: v.status for v in out.verdicts})
        self.assertEqual(run("Prefer fewer parts."),
                         run("Minimise cost wherever possible."))


# =====================================================================
# B40-B45, B50-B53 - a named reference is an address
# =====================================================================
class TestExactReferences(_Feas):

    def basis_probe(self, differs_from, configs=2, joints=None, coords=None,
                    basis_on="CFG-C0A", joint="JNT-0A", dof="RZ"):
        """A hinge whose CFG basis names exactly the siblings given.

        THE BASIS NAMES ITS JOINT. It named a rigid group and left every reader
        to work out which joint expressed that group's DOF; `joint` is the
        subject of the declaration now, and `joints` is still the topology's
        joint list where a probe needs to replace it.
        """
        basis = {basis_on: [{"joint": joint, "dof": dof,
                             "differs_from": list(differs_from)}]}
        top = topology("A", 2, [(0, 1)], basis=basis, configs=configs)
        if joints is not None:
            top["joints"] = joints
        placements = [{"joint": j["id"], "origin": [0, 0, 0]}
                      for j in top["joints"]]
        s04b = {"joint_placements": placements,
                "state_coordinates": [
                    {"configuration": c, "coordinates": dict(v)}
                    for c, v in (coords or {}).items()],
                "transitions": [], "envelope_revisions": [], "notes": ""}
        # NO DEMANDED STATE CHANGE. These probes replace the joint list, so a
        # demand naming the default hinge joint would name a joint this
        # mechanism does not have; and what they are probing is which existing
        # joint answers a described difference, not what was asked for.
        return self.hinge(s03a=top, s03b=realization("A", demand=None),
                          s04b=s04b)

    JOINTS = [{"id": "JNT-PA", "joint_type": "PRISMATIC",
               "parent_group": _group(0, "A"), "child_group": _group(1, "A"),
               "dof": ["TX"], "axis_direction": "+X", "frame_ids": ["F1"]},
              {"id": "JNT-RA", "joint_type": "REVOLUTE",
               "parent_group": _group(0, "A"), "child_group": _group(1, "A"),
               "dof": ["RZ"], "axis_direction": "+Z", "frame_ids": ["F1"]}]

    def test_B40_an_absent_named_sibling_cannot_be_written_at_all(self):
        """A basis naming a configuration the design does not have.

        This used to assert what FEASIBILITY concluded about such a state:
        NOT_ESTABLISHED, because comparing against the sibling that happens to be
        there answers a reference to an entity that does not exist.

        The state is no longer constructible. `distinguishing_basis` is a record
        list whose `joint` and `differs_from` members are typed, so a dangling
        sibling is refused by the write boundary - earlier, and for the same
        reason. The domain branch that reported it remains as defence in
        depth; nothing can reach it through a canonical write.
        """
        from ver3.assy_v3.state.design_state import ContractError
        with self.assertRaises(ContractError) as raised:
            self.basis_probe(["CFG-GONE"], coords={
                "CFG-C0A": {"JNT-0A": 0}, "CFG-C1A": {"JNT-0A": 90}})
        self.assertIn("DANGLING_REF", str(raised.exception))
        self.assertIn("differs_from", str(raised.exception))

    def test_B41_a_named_sibling_that_is_equal_fails(self):
        """The named sibling, equal. Written into state by a revision for the
        reason B4 gives: the producer no longer authors this."""
        state = self.basis_probe(["CFG-C1A"], coords={
            "CFG-C0A": {"JNT-0A": 60}, "CFG-C1A": {"JNT-0A": 90}})
        self.revise(state, Op("SUPERSEDE", "State", "STA-CFG-C1A",
                              {"joint_coordinates": {"JNT-0A": 60}}, "t",
                              reason="the coordinate was revised to the other's"))
        v = self.domain(self.assess(state), "required_configurations")
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("DECLARED_DISTINCTNESS_NOT_REALIZED", v.reason_codes)

    def test_B42_an_unnamed_configuration_cannot_change_the_answer(self):
        """CFG-C2A is present, realized, and equal to the subject. It is not
        named, so it is not compared - and the verdict is the one the named
        sibling earns."""
        state = self.basis_probe(["CFG-C1A"], configs=3, coords={
            "CFG-C0A": {"JNT-0A": 0}, "CFG-C1A": {"JNT-0A": 90},
            "CFG-C2A": {"JNT-0A": 0}})
        v = self.domain(self.assess(state), "required_configurations")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertNotIn("DECLARED_DISTINCTNESS_NOT_REALIZED", v.reason_codes)

    def test_B43_the_basis_names_its_own_joint_and_nothing_else_is_read(self):
        """A slider and a hinge on one group, and a basis about the hinge.

        This used to be about RESOLUTION: the basis named a group, two joints
        touched it, and the code had to choose - which it did by taking the one
        whose child was the group, so an arbitrary pick could land on the slider
        and report FAIL because a translation is equal in both configurations.
        The declaration names the joint now. Nothing is chosen, the other joint
        is not read, and the order the joints arrive in cannot matter."""
        for order in (self.JOINTS, list(reversed(self.JOINTS))):
            state = self.basis_probe(
                ["CFG-C1A"], joint="JNT-RA", joints=[dict(j) for j in order],
                coords={"CFG-C0A": {"JNT-PA": 0, "JNT-RA": 0},
                        "CFG-C1A": {"JNT-PA": 0, "JNT-RA": 90}})
            v = self.domain(self.assess(state), "required_configurations")
            self.assertEqual(s07.PASS, v.status,
                             "order %s: %s" % ([j["id"] for j in order], v.summary))
            self.assertIn("JNT-RA", v.premises)
            self.assertNotIn("JNT-PA", v.premises,
                             "a joint the declaration does not name")

    def test_B44_two_joints_on_one_group_no_longer_make_it_ambiguous(self):
        """The case the old address could not resolve: two compatible joints on
        one group. There is nothing to resolve - the basis says which."""
        joints = [dict(j, id="JNT-R%dA" % n, joint_type="REVOLUTE",
                       axis_direction="+Z", dof=["RZ"])
                  for n, j in enumerate(self.JOINTS)]
        state = self.basis_probe(
            ["CFG-C1A"], joint="JNT-R1A", joints=joints,
            coords={"CFG-C0A": {"JNT-R0A": 0, "JNT-R1A": 0},
                    "CFG-C1A": {"JNT-R0A": 0, "JNT-R1A": 90}})
        v = self.domain(self.assess(state), "required_configurations")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertNotIn("DISTINCTNESS_DRIVER_AMBIGUOUS", v.reason_codes)
        self.assertIn("JNT-R1A", v.premises)
        self.assertNotIn("JNT-R0A", v.premises)

    def test_B45_a_joint_that_does_not_free_the_named_dof(self):
        """PRISMATIC along X, and a basis about RZ. The joint has no coordinate
        in that degree of freedom, so there is no value to compare - and
        substituting the one it DOES free would answer a different question."""
        joints = [dict(self.JOINTS[0])]
        state = self.basis_probe(["CFG-C1A"], joint="JNT-PA", joints=joints,
                                 coords={"CFG-C0A": {"JNT-PA": 0},
                                         "CFG-C1A": {"JNT-PA": 1}})
        v = self.domain(self.assess(state), "required_configurations")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("DISTINCTNESS_DOF_NOT_SUPPORTED", v.reason_codes)

    def test_B45b_a_joint_this_candidate_does_not_have_cannot_be_written(self):
        """A named reference is an address. `joint` is a typed reference now, so
        one that resolves to nothing is refused by the write boundary - earlier
        than any verdict, and for the same reason a dangling sibling is."""
        from ver3.assy_v3.state.design_state import ContractError
        with self.assertRaises(ContractError) as raised:
            self.basis_probe(["CFG-C1A"], joint="JNT-NOWHERE",
                             coords={"CFG-C0A": {"JNT-0A": 0},
                                     "CFG-C1A": {"JNT-0A": 90}})
        self.assertIn("DANGLING_REF", str(raised.exception))
        self.assertIn("joint", str(raised.exception))

    def test_B50_configuration_order_cannot_change_the_answer(self):
        """The whole assessment, entity for entity, under a permuted view."""
        def run(reverse):
            top = topology("A", 2, [(0, 1)], configs=3, basis={
                "CFG-C0A": [{"joint": "JNT-0A", "dof": "RZ",
                             "differs_from": ["CFG-C1A"]}]})
            if reverse:
                top["configurations"] = list(reversed(top["configurations"]))
            coords = {"CFG-C0A": {"JNT-0A": 0}, "CFG-C1A": {"JNT-0A": 90},
                      "CFG-C2A": {"JNT-0A": 0}}
            s04b = {"joint_placements": [{"joint": "JNT-0A", "origin": [0, 0, 0]}],
                    "state_coordinates": [{"configuration": c, "coordinates": v}
                                          for c, v in coords.items()],
                    "transitions": [], "envelope_revisions": [], "notes": ""}
            out = self.assess(self.hinge(s03a=top, s04b=s04b), apply_patch=False)
            return (out.status,
                    {v.domain: (v.status, tuple(v.reason_codes), tuple(v.premises))
                     for v in out.verdicts})
        self.assertEqual(run(False), run(True))

    def test_B51_joint_order_cannot_change_the_answer(self):
        def run(order):
            state = self.basis_probe(
                ["CFG-C1A"], joint="JNT-RA", joints=[dict(j) for j in order],
                coords={"CFG-C0A": {"JNT-PA": 0, "JNT-RA": 0},
                        "CFG-C1A": {"JNT-PA": 0, "JNT-RA": 90}})
            v = self.domain(self.assess(state, apply_patch=False),
                            "required_configurations")
            return v.status, tuple(v.reason_codes), tuple(v.premises)
        self.assertEqual(run(self.JOINTS), run(list(reversed(self.JOINTS))))

    def test_B53_only_the_sibling_actually_compared_is_read(self):
        """CFG-C2A is realized and equal to the subject; CFG-C1A is the named
        sibling and differs. Making the UNNAMED one equal cannot change the
        verdict - which is the whole content of "a named reference is an
        address"."""
        def run(unnamed_coordinate):
            state = self.basis_probe(["CFG-C1A"], configs=3, coords={
                "CFG-C0A": {"JNT-0A": 0}, "CFG-C1A": {"JNT-0A": 90},
                "CFG-C2A": {"JNT-0A": unnamed_coordinate}})
            v = self.domain(self.assess(state, apply_patch=False),
                            "required_configurations")
            return v.status, tuple(v.reason_codes)
        self.assertEqual(run(0), run(45))
        self.assertEqual((s07.PASS, ("EVERY_CONFIGURATION_REALIZED",)), run(0))


# =====================================================================
# B46-B49, B52 - one load case, several declared routes
# =====================================================================
class TestLoadPathMultiplicity(_Feas):

    GOOD = {"id": "LDP-A", "load_case": "LC-0001", "candidate": "CND-A",
            "ordered_hops": ["IFC-0A", "IFC-0A"], "terminates_at": "RSR-0001"}
    ALSO_GOOD = {"id": "LDP-2A", "load_case": "LC-0001", "candidate": "CND-A",
                 "ordered_hops": ["IFC-0A"], "terminates_at": "RSR-0001"}
    WRONG_SITE = {"id": "LDP-3A", "load_case": "LC-0001", "candidate": "CND-A",
                  "ordered_hops": ["IFC-0A"], "terminates_at": "RSR-BAD"}
    OPEN = {"id": "LDP-4A", "load_case": "LC-0001", "candidate": "CND-A",
            "ordered_hops": ["IFC-0A"]}

    def routed(self, *paths):
        state = self.seed()
        self.candidates(state)
        self.add(state, "s02", "ReactionSiteRequirement", "RSR-BAD",
                 scenario="SCN-0001", boundary_side="INTERNAL", at_role="inside")
        r = realization("A")
        r["load_paths"] = [dict(p) for p in paths]
        self.hinge(state=state, s03b=r)
        return state

    def verdict(self, *paths):
        out = self.assess(self.routed(*paths), apply_patch=False)
        v = self.domain(out, "load_reaction_closure")
        return v.status, tuple(v.reason_codes), tuple(v.premises)

    def test_B46_two_valid_routes_pass_in_either_order(self):
        forward = self.verdict(self.GOOD, self.ALSO_GOOD)
        backward = self.verdict(self.ALSO_GOOD, self.GOOD)
        self.assertEqual(s07.PASS, forward[0], forward)
        self.assertEqual(forward, backward,
                         "the verdict or its premises depend on insertion order")

    def test_B47_a_valid_route_does_not_excuse_a_contradictory_one(self):
        """The design asserts both, and one of them closes at the wrong site.
        Keeping whichever came last decided this by nothing at all."""
        forward = self.verdict(self.GOOD, self.WRONG_SITE)
        backward = self.verdict(self.WRONG_SITE, self.GOOD)
        self.assertEqual(s07.FAIL, forward[0])
        self.assertIn("TERMINUS_NOT_THE_DECLARED_SITE", forward[1])
        self.assertIn("DECLARED_ROUTE_CONTRADICTS_ITSELF", forward[1])
        self.assertEqual(forward, backward)

    def test_B48_a_valid_route_does_not_excuse_an_unresolved_one(self):
        forward = self.verdict(self.GOOD, self.OPEN)
        backward = self.verdict(self.OPEN, self.GOOD)
        self.assertEqual(s07.NOT_ESTABLISHED, forward[0])
        self.assertIn("LOAD_PATH_OPEN", forward[1])
        self.assertEqual(forward, backward)

    def test_B49_no_route_at_all_is_not_established(self):
        state = self.seed()
        self.candidates(state)
        r = realization("A")
        r["load_paths"] = []
        self.hinge(state=state, s03b=r)
        v = self.domain(self.assess(state), "load_reaction_closure")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("LOAD_PATH_MISSING", v.reason_codes)

    def test_B52_the_whole_assessment_is_order_independent(self):
        def run(paths):
            out = self.assess(self.routed(*paths), apply_patch=False)
            return (out.status,
                    {v.domain: (v.status, tuple(v.reason_codes), tuple(v.premises))
                     for v in out.verdicts})
        self.assertEqual(run((self.GOOD, self.ALSO_GOOD)),
                         run((self.ALSO_GOOD, self.GOOD)))


# =====================================================================
# B57-B59 - one vocabulary authority, whichever door the constraint came in
# =====================================================================
class TestIngressVocabulary(_Feas):

    def test_B57_a_profile_kind_nothing_can_act_on_is_not_ingested(self):
        """BEING STRUCTURED IS NOT A LICENCE. A section headed
        `design_constraints` could carry a wish, and the profile channel took
        the file's word for it - making a preference into a hard requirement by
        the one route the other channel is built to refuse."""
        state = self.seed(profile={"design_constraints": [
            {"kind": "MINIMIZE_PART_COUNT", "statement": "prefer fewer parts",
             "parameters": {"objective": "MINIMIZE"}},
            {"kind": "PREFER_SIMPLE_ASSEMBLY", "statement": "simple would be nice"},
            {"kind": "UNKNOWN_CUSTOM_KIND", "statement": "whatever"}]})
        self.assertEqual([], state.family("DesignConstraint"))

    def test_B58_a_profile_kind_the_vocabulary_declares_is_ingested_exactly(self):
        state = self.seed(profile={"design_constraints": [
            {"kind": "MATERIAL_CLASS_ONLY",
             "statement": "every manufactured part must be plastic",
             "source": "the profile the user supplied",
             "parameters": {"material_class": "PLASTIC"},
             "blocks_selection": True}]})
        made = state.entities["DSC-P001"]
        self.assertEqual("MATERIAL_CLASS_ONLY", made["kind"])
        self.assertEqual({"material_class": "PLASTIC"}, made["parameters"])
        self.assertEqual("the profile the user supplied", made["source"])
        self.assertEqual("every manufactured part must be plastic",
                         made["statement"])
        self.assertTrue(made["blocks_selection"])

    def test_B59_both_channels_ask_the_same_authority(self):
        """Not "both happen to accept the same list" - the same table object,
        consulted the same way. A second list would drift the first time a kind
        is added, and the two channels would disagree about what a hard
        requirement is."""
        import inspect
        for name in ("ingest_design_constraints", "capture_design_constraints"):
            body = inspect.getsource(getattr(s01, name))
            self.assertIn("CONSTRAINT_KINDS.get(", body,
                          "%s does not consult the canonical vocabulary" % name)
        # And behaviourally: the same kind through either door, the same refusal
        # through either door.
        for kind, expected in (("MATERIAL_CLASS_ONLY", 1),
                               ("MINIMIZE_PART_COUNT", 0)):
            profile = self.seed(profile={"design_constraints": [
                {"kind": kind, "statement": "s",
                 "parameters": {"material_class": "PLASTIC"}}]})
            source = self.seed(hard_constraints=[
                {"requirement": "REQ-0001", "kind": kind, "statement_verbatim": "s",
                 "parameters": {"material_class": "PLASTIC"}}])
            self.assertEqual(expected, len(profile.family("DesignConstraint")), kind)
            self.assertEqual(expected, len(source.family("DesignConstraint")), kind)


# =====================================================================
# B60-B64 - an ambiguous extent measures nothing
# =====================================================================
class TestAmbiguousGeometry(_Feas):
    """Detecting a duplicate is not enough: the arbitrary box must be gone.

    `_weaken` does not undo a FAIL, so a domain that noticed the ambiguity and
    went on measuring could still report a positive contradiction - and which
    one depended on which envelope the index kept."""

    NEAR = ([1.5, 0, 0], [1, 1, 1])          # touching BOD-G0A
    FAR = ([9, 0, 0], [1, 1, 1])             # a positive gap from it

    def doubled(self, body="BOD-G1A", order=("NEAR", "FAR"), state=None,
                **kw):
        """`body` ends up with two standing extents, in the order given."""
        state = state if state is not None else self.hinge(**kw)
        first, second = (getattr(self, o) for o in order)
        eid = self.envelope_for(state, body)
        self.revise(state, Op("SUPERSEDE", "Envelope", eid,
                              {"extent": {"centre": first[0],
                                          "half_extent": first[1]}},
                              "t", reason="probe"))
        self.revise(state, Op("CREATE", "Envelope", "ENV-DUP-%s" % body[-3:],
                              {"body": body,
                               "extent": {"centre": second[0],
                                          "half_extent": second[1]},
                               "frame": "world", "maturity": "PROVISIONAL"}, "t"))
        self.assertEqual(2, len([e for e in state.family("Envelope")
                                 if e["body"] == body]), "the probe is not probing")
        return state

    def envelope_for(self, state, body):
        found = [e["entity_id"] for e in state.family("Envelope")
                 if e["body"] == body]
        self.assertEqual(1, len(found), found)
        return found[0]

    def both_orders(self, domain, **kw):
        out = []
        for order in (("NEAR", "FAR"), ("FAR", "NEAR")):
            v = self.domain(self.assess(self.doubled(order=order, **kw),
                                        apply_patch=False), domain)
            out.append((v.status, tuple(v.reason_codes)))
        self.assertEqual(out[0], out[1],
                         "%s depends on which extent was written last" % domain)
        return out[0]

    def test_B60_a_doubled_extent_cannot_close_or_break_a_load_route(self):
        """One extent touches the hop's other body, the other is a positive gap
        away. Whichever won decided PASS or FAIL."""
        status, codes = self.both_orders("load_reaction_closure")
        self.assertEqual(s07.NOT_ESTABLISHED, status)
        self.assertIn("BODY_ENVELOPED_TWICE", codes)
        self.assertNotIn("HOP_BODIES_APART", codes,
                         "a positive contradiction from an arbitrary box")

    def test_B61_a_doubled_extent_cannot_establish_the_arrangement(self):
        status, codes = self.both_orders("spatial_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, status)
        self.assertIn("BODY_ENVELOPED_TWICE", codes)
        self.assertNotIn("CONNECTED_BODIES_APART", codes)

    def test_B62_a_doubled_extent_cannot_clear_or_convict_a_pair(self):
        status, codes = self.both_orders("gross_interference")
        self.assertEqual(s07.NOT_ESTABLISHED, status)
        self.assertIn("BODY_ENVELOPED_TWICE", codes)
        self.assertNotIn("NO_CONSERVATIVE_OVERLAP", codes,
                         "a clearance PASS from an arbitrary box")

    def test_B62b_and_neither_can_it_pass_assemblability(self):
        status, codes = self.both_orders("assemblability")
        self.assertEqual(s07.NOT_ESTABLISHED, status)
        self.assertIn("BODY_ENVELOPED_TWICE", codes)
        self.assertNotIn("ORDER_CONSISTENT_AND_PATHS_CLEAR", codes)

    def test_B63_a_doubled_extent_decides_no_dimensional_requirement(self):
        """One extent is within the limit, the other exceeds it."""
        profile = {"design_constraints": [
            {"kind": "MAX_OVERALL_DIMENSION", "statement": "it must fit",
             "parameters": {"axis": "X", "limit": 40, "unit": "mm"}}]}
        seen = []
        for order in (("NEAR", "FAR"), ("FAR", "NEAR")):
            state = self.doubled(
                order=order, state=self.hinge(state=self.seed(profile=profile),
                                              s04a=arrangement(
                    HINGE_BOXES, steps=["ASY-0A"], basis="ABSOLUTE",
                    absolute={"unit": "mm", "per_unit": 10.0})))
            status, codes, _u, why = TestHardRequirements.status_of(
                self, self.assess(state, apply_patch=False))
            seen.append((status, tuple(codes)))
            self.assertEqual(s07.NOT_YET_EVALUABLE, status, why)
            self.assertIn("BODY_ENVELOPED_TWICE", codes)
        self.assertEqual(seen[0], seen[1])

    def test_B63b_one_extent_each_still_decides_it(self):
        """The quarantine must not swallow the ordinary case."""
        profile = {"design_constraints": [
            {"kind": "MAX_OVERALL_DIMENSION", "statement": "it must fit",
             "parameters": {"axis": "X", "limit": 40, "unit": "mm"}}]}
        state = self.hinge(state=self.seed(profile=profile),
                           s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            basis="ABSOLUTE",
                                            absolute={"unit": "mm",
                                                      "per_unit": 10.0}))
        status, _c, _u, why = TestHardRequirements.status_of(
            self, self.assess(state))
        self.assertEqual(s07.SATISFIED, status, why)

    def test_B62c_a_pair_described_two_ways_requires_no_contact(self):
        """FOUND BY THE SWEEP, not by the brief. `gross_interference` refused to
        exempt a pair declared both CONTACT and CLEARANCE - and
        `spatial_realization` went on requiring the contact and FAILING when the
        boxes were apart. A recognised ambiguity leaking into a positive
        contradiction one domain over."""
        top = topology("A", 2, [(0, 1)])
        top["interfaces"].append({"id": "IFC-CLR", "bodies": ["BOD-G0A", "BOD-G1A"],
                                  "interaction_kind": "CLEARANCE",
                                  "nominal_status": "NOMINAL"})
        state = self.hinge(s03a=top,
                           s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                                             "BOD-G1A": ([9, 0, 0], [1, 1, 1])},
                                            steps=["ASY-0A"]),
                           s04b=motion("A", "JNT-0A", _group(1, "A"),
                                       coords=(0, 0)))
        out = self.assess(state, apply_patch=False)
        v = self.domain(out, "spatial_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("INTERFACE_EXPECTATION_CONFLICT", v.reason_codes)
        self.assertNotIn("CONNECTED_BODIES_APART", v.reason_codes,
                         "a contradictory description produced a broken mechanism")
        self.assertEqual(s07.NOT_ESTABLISHED,
                         self.domain(out, "gross_interference").status)

    def test_B62d_two_current_bases_measure_nothing(self):
        """Also from the sweep. `SCALE_AMBIGUOUS` was reported by the dimensional
        evaluator and by nothing else, so two current bases still fed box_gap -
        arithmetic across a boundary nothing defines, and it could FAIL."""
        state = self.hinge()
        # ON THE BRANCH, or the view never sees it and the probe proves nothing:
        # an unscoped entity is not this candidate's evidence.
        self.revise(state, Op("CREATE", "ReferenceScale", "SCL-SECOND",
                              {"basis": "RELATIVE", "absolute": None,
                               "note": "a second current basis"}, "t",
                              premise_refs=["CND-A"]))
        self.assertEqual(2, len(state.family("ReferenceScale")))
        out = self.assess(state, apply_patch=False)
        for name in ("spatial_realization", "load_reaction_closure",
                     "gross_interference", "assemblability"):
            v = self.domain(out, name)
            self.assertEqual(s07.NOT_ESTABLISHED, v.status, name)
            self.assertIn("SCALE_AMBIGUOUS", v.reason_codes, name)
        self.assertNotEqual(s07.INFEASIBLE, out.status)

    def test_B64_an_unrelated_doubled_extent_does_not_contaminate(self):
        """A third body, doubled, that no load route touches. The domains that
        genuinely read every body say so; the one that does not is untouched -
        and does not carry the duplicate envelopes as premises."""
        state = self.hinge(s03a=topology("A", 3, [(0, 1), (1, 2)]),
                           s03b=realization("A", hops=(0, 0)),
                           s04a=arrangement(
                               {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                                "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
                                "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])},
                               steps=["ASY-0A"]))
        clean = self.domain(self.assess(state, apply_patch=False),
                            "load_reaction_closure")
        self.assertEqual(s07.PASS, clean.status, clean.summary)

        doubled = self.doubled(body="BOD-G2A", state=state,
                               order=("NEAR", "FAR"))
        out = self.assess(doubled, apply_patch=False)
        route = self.domain(out, "load_reaction_closure")
        self.assertEqual(s07.PASS, route.status,
                         "an unrelated body's ambiguity reached a route that "
                         "never measured it")
        self.assertEqual(clean.premises, route.premises,
                         "the premise set moved for a body nothing measured")
        for eid in ("ENV-DUP-G2A",):
            self.assertNotIn(eid, route.premises)
        # The domains that DO read every body report it, as they should.
        for name in ("spatial_realization", "gross_interference"):
            v = self.domain(out, name)
            self.assertEqual(s07.NOT_ESTABLISHED, v.status, name)
            self.assertIn("BODY_ENVELOPED_TWICE", v.reason_codes, name)


# =====================================================================
# B35 and the closure sweep - the contracts describe what runs
# =====================================================================
class TestContractTruth(unittest.TestCase):
    """Not "is the contract self-consistent" - is it TRUE of the code.

    Each assertion below is a defect class the S7-B correction found, written so
    that reintroducing it fails here rather than waiting for someone to read the
    file next to the one they changed."""

    @classmethod
    def setUpClass(cls):
        cls.state = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.matrix = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.audit = _paths.contract("ENTITY_FAMILY_AUDIT.yaml")
        cls.s01 = _paths.contract("stages/S01_CONTRACT.yaml")
        cls.profile = _paths.contract("USER_DESIGN_PROFILE_CONTRACT.yaml")
        cls.fams = dict(cls.state["entity_families"])
        cls.fams.update(cls.state["assurance_families"])

    #: The three families S7-B produces, and the one it consumes as its input.
    PRODUCED = ("FeasibilityDomainAssessment", "MechanicalFeasibilityAssessment",
                "HardRequirementCompliance")

    def test_B35_no_active_statement_says_these_have_no_producer(self):
        """A contract claiming a live family is unproduced is worse than silence:
        it tells a reader the check they are looking for cannot exist."""
        for family in self.PRODUCED + ("DesignConstraint",):
            entry = self.audit["families"][family]
            blob = json.dumps(entry)
            for phrase in ("has not yet emitted", "ahead of its producer",
                           "no producer", "not yet produced"):
                self.assertNotIn(phrase, blob,
                                 "%s: %r is no longer true" % (family, phrase))
        for family in self.PRODUCED:
            self.assertEqual("feasibility", self.fams[family]["owned_by"])
            self.assertIn(family,
                          self.matrix["responsibilities"]["entries"]["feasibility"]["owns"])

    def test_B35b_the_declared_ingress_is_the_one_that_runs(self):
        """The contract names a producer, a key it reads and a key it does not.
        All three are read off the code, not off a neighbouring sentence."""
        import inspect
        ingress = self.s01["constraint_ingress"]
        self.assertIn("ingest_design_constraints", ingress["producer"])
        self.assertIn("DesignConstraint", self.s01["owned_decisions"]["creates"])
        self.assertIn("DesignConstraint", self.s01["structured_outputs"])
        self.assertEqual(CONSTRAINT_SECTION, ingress["reads"].split(".")[-1])
        source = inspect.getsource(s01_ingest)
        self.assertIn("CONSTRAINT_SECTION", source)
        self.assertNotIn("selection_preferences", source)
        self.assertIn("LIVE", self.profile["ingester_status"])

    def test_B35g_the_constraint_kinds_are_one_vocabulary(self):
        """Declared in the contract, mirrored in the ingester, and the mirror is
        checked - a vocabulary living in two places drifts, and this one decides
        which stated requirements survive."""
        declared = self.fams["DesignConstraint"]["kinds"]
        self.assertEqual(sorted(declared), sorted(s01.CONSTRAINT_KINDS))
        for kind, spec in declared.items():
            mirror = s01.CONSTRAINT_KINDS[kind]
            self.assertEqual(spec["quantitative"], mirror["quantitative"], kind)
            if spec["quantitative"]:
                self.assertEqual(spec["quantity"], mirror["quantity"], kind)
        # Every kind the evaluator can decide must be one the ingester can make.
        for kind in s07.CONSTRAINT_EVALUATORS:
            self.assertIn(kind, declared, kind)

    def test_B35h_both_origins_are_declared_and_neither_is_deferred(self):
        """The contract may not say a source-stated hard requirement waits for a
        later substep. It does not wait; it is produced here, and prose claiming
        otherwise would send a reader looking for a producer that exists."""
        origins = self.fams["DesignConstraint"]["origins"]
        self.assertEqual({"user_design_profile", "explicit_source_requirement"},
                         set(origins))
        # Only the statements ABOUT HARD REQUIREMENTS. The profile contract may
        # still say the PREFERENCE materialiser is S7-C's, because it is.
        blob = (json.dumps(self.fams["DesignConstraint"])
                + json.dumps(self.profile["ingestion"]["design_constraints"])
                + json.dumps(self.profile["visibility"]["design_constraints"]))
        for deferral in ("S7-C", "S7-D", "S7-E", "S7-F"):
            self.assertNotIn(deferral, blob,
                             "a hard requirement is described as deferred")
        self.assertIn("S7-C", json.dumps(
            self.profile["ingestion"]["selection_preferences"])
            + self.profile["ingester_status"],
            "the preference materialiser has lost its owner")
        self.assertEqual("s01", self.fams["DesignConstraint"]["owned_by"])
        self.assertIn("DesignConstraint",
                      self.matrix["stages"]["s01"]["owns"])

    def test_B35i_the_contracts_state_the_two_closure_invariants(self):
        """Both are properties a reader must be able to find without running the
        code: one vocabulary authority for every ingress, and geometry that
        cannot establish a verdict when it is ambiguous."""
        rules = " ".join(self.fams["DesignConstraint"]["rules"])
        self.assertIn("ONE VOCABULARY AUTHORITY", rules)
        self.assertIn("kinds",
                      self.profile["ingestion"]["design_constraints"])
        self.assertIn("shared_gate", self.s01["constraint_ingress"])
        source = _paths.CONTRACTS + "/DESIGN_STATE_CONTRACT.yaml"
        with open(source) as fh:
            text = fh.read()
        self.assertIn("AMBIGUOUS GEOMETRY ESTABLISHES NOTHING", text)

    def test_B35c_the_interface_vocabulary_is_the_one_the_producer_emits(self):
        """It was not. Two lists with NOT ONE VALUE IN COMMON, and nothing read
        the contract's, so every interface in every recording would have failed
        it and every value it named would have been refused by the validator."""
        self.assertEqual(sorted(s03.INTERACTION_KINDS),
                         sorted(self.fams["Interface"]["interaction_kinds"]))
        expectation = self.fams["Interface"]["spatial_expectation"]
        self.assertEqual(sorted(s04.INTENDED_CONTACT_KINDS),
                         sorted(expectation["TOUCHES"]))
        for kind in expectation["TOUCHES"]:
            self.assertEqual(s04.TOUCHES,
                             s04.interface_expectation({"interaction_kind": kind}))
        for kind in expectation["CLEAR"]:
            self.assertEqual(s04.CLEAR,
                             s04.interface_expectation({"interaction_kind": kind}))
        for kind in expectation["TOUCHES"] + expectation["CLEAR"]:
            self.assertIn(kind, s03.INTERACTION_KINDS)

    def test_B35d_every_declared_domain_has_an_evaluator_and_the_reverse(self):
        declared = self.fams["FeasibilityDomainAssessment"]["domain"]
        self.assertEqual(sorted(declared), sorted(s07.DOMAINS))
        self.assertEqual(sorted(declared), sorted(s07.DOMAIN_EVALUATORS))
        self.assertEqual(
            sorted(declared),
            sorted(self.fams["MechanicalFeasibilityAssessment"]["evaluated_domains"]))
        for status in (s07.PASS, s07.FAIL, s07.NOT_ESTABLISHED, s07.NOT_APPLICABLE):
            self.assertIn(status, self.fams["FeasibilityDomainAssessment"]["status"])
        for status in (s07.FEASIBLE, s07.INFEASIBLE, s07.MFA_NOT_ESTABLISHED):
            self.assertIn(status,
                          self.fams["MechanicalFeasibilityAssessment"]["status"])
        for status in (s07.SATISFIED, s07.VIOLATED, s07.NOT_YET_EVALUABLE):
            self.assertIn(status, self.fams["HardRequirementCompliance"]["status"])

    def test_B35e_the_motion_effects_come_from_the_declared_vocabulary(self):
        """A demand vocabulary invented beside the contract's would decide which
        obligations count as motion without saying so anywhere readable."""
        declared = self.fams["PhysicalEffectObligation"]["effect"]
        for effect in s07.MOTION_EFFECTS:
            self.assertIn(effect, declared)
        self.assertNotIn("PREVENT_MOTION", s07.MOTION_EFFECTS,
                         "demanding that motion NOT occur is a different question")

    def test_B35f_feasibility_declares_the_roles_its_demands_need(self):
        """Every applicability test reads a family, and a family reaches the view
        only because some premise class names its role. A demand-driven domain
        whose demand is not in the required minimum is a rule that cannot fire."""
        roles = {r for p in self.resp["stages"]["feasibility"]
                 ["required_reasoning_premise_classes"]
                 for r in p["requires_semantics"]}
        for family, role in (("Actor", "actor_role"),
                             ("PhysicalEffectObligation", "physical_effect_obligation"),
                             ("LoadCase", "load_case"),
                             ("LoadPath", "load_route"),
                             ("DesignConstraint", "design_constraint"),
                             ("Interface", "topology_relation"),
                             ("Body", "topology_element")):
            self.assertIn(role, roles, family)
            self.assertIn(role, self.fams[family]["semantic_roles"], family)


class TestClosureSweep(unittest.TestCase):
    """The defect CLASSES, swept over the S7-B corpus rather than the lines.

    Every one of these was a real finding somewhere in this pass. A scan is worth
    more than a fixed list because the last four passes each turned up residue
    nobody had listed - so what is checked is the shape, everywhere it could
    recur."""

    @classmethod
    def setUpClass(cls):
        import inspect
        cls.src = inspect.getsource(s07)
        cls.tree = ast.parse(cls.src)
        # THE CODE, WITH THE PROSE REMOVED. `_code_only` returns an AST dump on
        # this interpreter, which quietly turns every substring assertion about
        # an expression into a vacuous one. This blanks the docstring LINES
        # instead, so what is searched is still source - and a rule explained in
        # a docstring is not mistaken for the rule being implemented.
        lines = cls.src.splitlines()
        for node in ast.walk(cls.tree):
            body = getattr(node, "body", None)
            if not isinstance(body, list):
                continue
            for child in body:
                if (isinstance(child, ast.Expr)
                        and isinstance(getattr(child, "value", None), ast.Constant)
                        and isinstance(child.value.value, str)):
                    for n in range(child.lineno - 1,
                                   (child.end_lineno or child.lineno)):
                        lines[n] = ""
        cls.code = "\n".join(lines)

    def test_SWEEP_01_no_unknown_key_is_silently_defaulted(self):
        """`AXIS_INDEX.get(axis, 0)` answered a requirement about a direction
        nobody named. Any `.get(x, <literal>)` on a vocabulary lookup is the same
        shape, so the vocabulary tables may only be subscripted."""
        for node in ast.walk(self.tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get" and len(node.args) == 2):
                continue
            target = node.func.value
            name = getattr(target, "attr", None) or getattr(target, "id", "")
            self.assertNotIn("INDEX", str(name).upper(),
                             "line %d defaults a vocabulary lookup" % node.lineno)
            self.assertNotIn("AXES", str(name).upper(),
                             "line %d defaults a vocabulary lookup" % node.lineno)

    def test_SWEEP_02_a_required_motion_keeps_both_of_its_components(self):
        """A required relative motion is (joint, dof), and a restraint blocks it
        only when it names the SAME pair. Matching on the joint alone would let a
        relation that removes a translation convict a demanded rotation of it;
        matching on the DOF alone would let any relation anywhere convict any
        joint. Both components select, and neither is dropped.

        This replaced a three-component address - (rigid_group, configuration,
        dof) - because the cell it addressed is no longer what the question is
        about. The configuration went with it: a restraint is compared against
        the source of the change it is claimed to obstruct, not against a grid.
        """
        self.assertEqual({("JNT-1", "RZ")}, s07._relative_motions(
            [{"joint": "JNT-1", "dof": "RZ"}]))
        for partial in ([{"joint": "JNT-1"}], [{"dof": "RZ"}], [{}], None):
            self.assertEqual(set(), s07._relative_motions(partial), partial)
        for pair in s07._relative_motions([{"joint": "JNT-1", "dof": "RZ"}]):
            self.assertEqual(2, len(pair))

    def test_SWEEP_03_a_typed_relation_is_never_accepted_on_the_id_alone(self):
        """Three references decide a verdict here, and each one's TYPE is
        checked as well as its resolution: the effect an interaction produces,
        the family a changed coordinate names, and whether a cited joint frees
        the cell citing it."""
        self.assertIn('i.get("effect") == effect', self.src)
        # A REQUIRED MOTION'S JOINT IS LOOKED UP IN THE JOINT FAMILY, so a
        # reference that names an entity of some other family finds nothing and
        # is reported. The check used to be a rejection after an id lookup -
        # `joint.get("_family") != "Joint"` beside a `by_id` read - and doing it
        # by construction is the same rule with no way to forget it.
        self.assertIn('joints = {j.get("entity_id"): j for j in ev.fam("Joint")}',
                      self.code)
        self.assertIn("JOINT_ABSENT", self.src)
        # And a restraint answers a demanded motion only where it explicitly
        # names the same relative motion, never because it was pointed at.
        self.assertIn('_relative_motions(relation.get("blocked_relative_motions"))',
                      self.code)

    def test_SWEEP_04_interface_existence_is_never_a_blanket_exemption(self):
        """The exemption set is built from `interface_expectation`, so it cannot
        contain a kind whose meaning is that the pair stays apart."""
        self.assertIn("interface_expectation", self.code)
        self.assertNotIn("in declared", self.code)
        self.assertIn("if e == s04.TOUCHES", self.code)
        for kind in s03.INTERACTION_KINDS:
            expectation = s04.interface_expectation({"interaction_kind": kind})
            self.assertIn(expectation, (s04.TOUCHES, s04.CLEAR, s04.UNDECLARED))
            if expectation == s04.TOUCHES:
                self.assertIn(kind, s04.INTENDED_CONTACT_KINDS)

    def test_SWEEP_05_partial_geometry_is_never_read_as_complete(self):
        """Three domains measure across bodies, and each says so when one of
        them has no extent: the dimensional limit, the insertion corridor and
        the interference sweep. A subset silently measured is a smaller product
        answering for the real one."""
        for code in ("EXTENT_INCOMPLETE", "INSERTION_GEOMETRY_INCOMPLETE",
                     "INTERFERENCE_GEOMETRY_MISSING", "BODY_WITHOUT_ENVELOPE"):
            self.assertIn(code, self.src, code)

    def test_SWEEP_06_every_demand_has_an_applicability_test(self):
        """NOT_APPLICABLE may only be returned where the DEMAND is absent. Each
        occurrence is checked by hand below because the rule is semantic; what
        this pins is that the demand readers exist and are the ones consulted."""
        self.assertIn("reach_demands", self.code)
        self.assertIn("motion_demands", self.code)
        for domain, reader in (("_reach", "reach_demands"),
                               ("_transition_reachability", "motion_demands"),
                               ("_motion_and_transitions", "motion_demands")):
            body = self.src.split("def %s(" % domain)[1].split("\ndef ")[0]
            self.assertIn(reader, body, domain)
            self.assertIn("NOT_APPLICABLE", body, domain)

    def test_SWEEP_07_an_elimination_record_never_decides_and_a_reach_result_is_labelled(self):
        """An EliminationRecord may weaken and may not decide: s04a saying "this
        arrangement cannot exist" is a geometric finding by a model, not a
        contradiction. Read structurally: never compared to PASS or FAIL.

        A ReachResult is DIFFERENT, and deliberately so since the pre-selection
        basis was defined: it is the contracted conclusion on reach at this
        stage, so it may decide - and every verdict that rests on one carries
        the MODEL_LOCAL evidence level beside its status, which is what keeps a
        conclusion about boxes and sides from being mistaken for a sweep
        through a solid."""
        after = self.src.split('fam("EliminationRecord")')[1]
        branch = "\n".join(after.splitlines()[:6])
        self.assertNotIn("status = PASS", branch)
        self.assertNotIn("status = FAIL", branch)
        self.assertIn("MODEL_LOCAL", branch)
        reach = self.src.split("def _reach(")[1].split("\ndef ")[0]
        self.assertIn("MODEL_LOCAL_POSITIVE", reach)
        self.assertIn("MODEL_LOCAL_NEGATIVE", reach)
        self.assertIn("REACH_CONCLUDED_UNREACHABLE", reach)

    def test_SWEEP_08_no_absence_produces_pass_or_fail(self):
        """Every branch that reports something MISSING weakens to
        NOT_ESTABLISHED. Read from the source of each evaluator: a code naming an
        absence must not sit in the same statement as FAIL."""
        absence = ("MISSING", "ABSENT", "NOT_COMPUTED", "INCOMPLETE",
                   "NOT_ESTABLISHED", "UNKNOWN", "NOT_DISPOSITIONED",
                   "UNDISPOSITIONED", "NOT_CLEAR", "OVERLAPS", "NOT_GIVEN",
                   "TOO_SHORT", "AMBIGUOUS", "UNREADABLE", "NOT_A_JOINT",
                   "MISMATCH", "NOT_RESOLVABLE", "NOT_YET")
        for node in ast.walk(self.tree):
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
                continue
            target, value = node.targets[0], node.value
            if not (isinstance(target, ast.Name) and target.id == "status"):
                continue
            if not (isinstance(value, ast.Name) and value.id == "FAIL"):
                continue
            window = self.src.splitlines()[max(node.lineno - 6, 0):node.lineno]
            for line in window:
                for word in absence:
                    self.assertNotIn('"%s' % word, line,
                                     "line %d: an absence sits beside a FAIL:\n%s"
                                     % (node.lineno, "\n".join(window)))

    def test_SWEEP_09_no_s7c_functionality_is_present(self):
        """Selection is the other half of the split and is not started. Its
        families are named nowhere in this module, and neither is any word for
        ranking one candidate against another."""
        for family in ("SelectionProfile", "CandidateComparison",
                       "SelectionAdvisory", "SelectionConcern",
                       "HumanDecisionInput", "SelectionDecision"):
            self.assertNotIn(family, self.src, family)
        for word in ("preference", "rank", "score", "weight", "better",
                     "prefer", "winner", "best"):
            self.assertNotIn(word, self.code.lower(), word)

    def test_SWEEP_10_nothing_crosses_a_candidate(self):
        """The view is the only engineering channel, so a candidate cannot see
        another's evidence. `state` appears in the entry point and in no
        evaluator: an evaluator taking it could reach unscoped state."""
        import inspect
        for name, fn in vars(s07).items():
            if not (inspect.isfunction(fn) and fn.__module__ == s07.__name__):
                continue
            if name in ("evaluate_candidate_feasibility",):
                continue
            self.assertNotIn("state", inspect.signature(fn).parameters, name)
        entry = self.src.split("def evaluate_candidate_feasibility(")[1]
        for reach in ("state.family(", "state.standing("):
            self.assertNotIn(reach, entry,
                             "the entry point reads unscoped state")

    def test_SWEEP_11_no_named_reference_is_answered_by_another_entity(self):
        """A canonical reference resolves exactly or becomes unresolved. The one
        substitution that existed compared a configuration against "some other
        realized one" when the sibling it named was absent."""
        self.assertNotIn("or [k for k in realized", self.code)
        for marker in ("TERMINAL_SITE_NOT_GIVEN",
                       "ENDPOINT_MISMATCH",
                       "JOINT_ABSENT",
                       "HOP_NOT_AN_INTERFACE"):
            self.assertIn(marker, self.src, marker)
        # THE SAME RULE WHERE THE RULE NOW LIVES. Declared distinctness is
        # checked by the pass that writes the coordinates and by the
        # responsibility that judges them, so the formula - and the refusal to
        # answer a named sibling with a different one - is asserted in the shared
        # module rather than dropped from the sweep.
        import inspect
        shared = inspect.getsource(s04.distinctness_findings)
        for marker in ("DISTINCTNESS_SIBLING_NOT_REALIZED",
                       "DISTINCTNESS_NAMES_NO_SIBLING"):
            self.assertIn(marker, shared, marker)
        # A named sibling is answered by THAT sibling or by nothing: the only
        # lookup keyed on the name, and no fallback beside it.
        self.assertIn('if other not in coordinates:', shared)
        self.assertIn('p = (coordinates.get(other) or {}).get(jid)', shared)
        for fallback in ("or [k for k in", "for k in coordinates if k !=",
                         "any(", "next("):
            self.assertNotIn(fallback, shared, fallback)

    def test_SWEEP_12_every_single_valued_index_is_guarded(self):
        """`d[k] = v` over a semantic key keeps the last writer. Each index that
        assumes uniqueness either keys on entity_id - which the write boundary
        makes unique - or reports the duplicate instead of resolving it."""
        for guard in ("def extent_status",
                      "CONFIGURATION_REALIZED_TWICE",
                      "REALIZED_MORE_THAN_ONCE",
                      "INTERFACE_EXPECTATION_CONFLICT",
                      "SCALE_AMBIGUOUS",
                      "ASSEMBLY_ORDER_NOT_TOTAL"):
            self.assertIn(guard, self.src, guard)
        # And the multiplicity that is genuinely allowed is accumulated, never
        # assigned: two paths for one load case, two interactions for one demand,
        # two records claiming to realize one demanded change.
        for accumulate in ("by_case.setdefault", "by_demand.setdefault",
                           "out.append({\"id\": t.get(\"entity_id\")"):
            self.assertIn(accumulate, self.code, accumulate)
        # The one index built by name is keyed on entity_id, which the write
        # boundary makes unique - so it resolves exactly or not at all.
        self.assertIn('relations = {r.get("entity_id"): r', self.code)

    def test_SWEEP_13_no_expression_picks_among_same_family_entities(self):
        """`next(...)` is the shape that cannot be guarded by a length test, so
        it is absent from the code entirely; the helper that used it is gone. The
        remaining `[0]`s are geometry corners or sit under an explicit length
        test, and each is named here so a new one has to be justified."""
        self.assertNotIn("next(", self.code)
        self.assertNotIn("driving_joint", self.code)
        for expression in ('states[0]', 'sorted(e)[0]', 'scales[0]'):
            self.assertIn(expression, self.src, expression)
        # `sorted(e)[0]` over a feature's expectations is guarded by the
        # conflict test one line above it: a feature with more than one
        # expectation is conflicted and never indexed.
        for guard in ("len(states) > 1", "len(e) > 1 for e in by_feature",
                      "len(scales) > 1"):
            self.assertIn(guard, self.code, guard)
        # THE SAME RULE WHERE THE RULE NOW LIVES. Choosing among the records
        # that claim to realize one demanded change is shared with the pass that
        # writes them, so the guard is asserted there rather than dropped here.
        import inspect
        shared = inspect.getsource(s04.realization_findings)
        self.assertIn("realizations[0]", shared)
        self.assertIn("len(realizations) > 1", shared)
        # Choosing the joint that carries a declared distinction is GONE, not
        # moved: the declaration names it, so there is no set to pick from.
        self.assertFalse(hasattr(s04, "distinctness_driver"))

    def test_SWEEP_14_a_distinction_names_its_own_coordinate(self):
        """THERE IS NO DRIVER TO RESOLVE ANY MORE.

        The address was (rigid_group, dof), and no rigid group has a coordinate -
        so every consumer had to decide which joint expressed it, and every way
        of deciding was a convention: the child-side joint read a relative
        relation as a statement about which side moves, and any-incident-joint
        made the middle link of a chain ambiguous. The declaration names the
        joint. Nothing here resolves one, and nothing here may."""
        import inspect
        self.assertFalse(hasattr(s04, "distinctness_driver"))
        for gone in ("_resolve_driver", "drivers_for", "joints_of",
                     "DISTINCTNESS_DRIVER_AMBIGUOUS", "DISTINCTNESS_DRIVER_UNKNOWN",
                     "DISTINCTNESS_DRIVER_AXIS_UNREADABLE"):
            self.assertNotIn(gone, self.src, gone)
        body = self.src.split("def _required_configurations(")[1].split("\ndef ")[0]
        self.assertIn("s04.distinctness_findings(", body)
        # And the shared rule reads the named joint rather than searching for one.
        shared = inspect.getsource(s04.distinctness_findings)
        self.assertIn('jid, dof = item.get("joint"), item.get("dof")', shared)
        for inference in ("incident_joints", "child_group", "parent_group",
                          "rigid_group"):
            self.assertNotIn(inference, shared, inference)

    def test_SWEEP_15_no_hard_demand_is_lost_between_s01_and_feasibility(self):
        """The two ingestion channels exist, neither depends on the other, and
        the role that carries the result to feasibility is declared."""
        import inspect
        src = inspect.getsource(s01)
        self.assertIn("def ingest_design_constraints", src)
        self.assertIn("def capture_design_constraints", src)
        emitted = src.split("def to_operations")[1].split("\n    # ")[0]
        for call in ("ingest_design_constraints(", "capture_design_constraints("):
            self.assertIn(call, emitted, "%s is never called" % call)
        # Neither channel gates the other: the profile ingester never looks at
        # the parsed response, and the source capture never looks at the profile.
        self.assertNotIn("design_profile",
                         src.split("def capture_design_constraints")[1]
                         .split("\ndef ")[0])
        self.assertNotIn("parsed",
                         src.split("def ingest_design_constraints")[1]
                         .split("\ndef ")[0])


class _EV(s07._Evidence):
    """An _Evidence over a literal view. For the structural sweeps only."""

    def __init__(self, view):
        s07._Evidence.__init__(self, view, "CND-A")


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
