"""S7-C: what the design can compare, and everything it must refuse to decide.

Every probe below runs the REAL chain - s01 through s04b through feasibility,
each candidate embodied into ONE accumulated DesignState - and then the real
selection evaluator over the real design-wide ConsumerView. Comparison is the one
question no single alternative can answer, so a fixture that seeds two isolated
states would be testing something the pipeline does not do.

WHAT THESE TESTS ARE GUARDING

    A preference cannot reach eligibility. The two questions are answered by
    different code reading different families, and the falsifier runs the same
    design under opposite preferences and asserts the eligible set is identical.

    A candidate whose eligibility cannot be established is not quietly dropped.
    `known ineligible` and `eligibility unknown` are different facts, and the
    second one stops the comparison entirely - comparing the subset that happened
    to be knowable would publish a conclusion about a design nobody has.

    No criterion gets a stand-in. `part_count` is not the Body count and
    `actuation_complexity` is not the Joint count, however well they correlate,
    and NOT_AVAILABLE is neither good nor bad - it stops the tier rather than
    scoring as infinity.

    A tradeoff at HIGH is never settled by MEDIUM. That is the difference between
    a comparison and a ranking, and it is what keeps the commitment a human's.

Synthetic mechanisms only: the hinge and the four-bar S7-B already probes with.
"""
from __future__ import annotations

import ast
import json
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.tools import run_window2                                      # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    FOURBAR_BOXES, HINGE_BOXES, _Feas, _group, arrangement, motion,
    realization, topology)

MINIMIZE, MAXIMIZE = "MINIMIZE", "MAXIMIZE"
HIGH, MEDIUM, LOW = "HIGH", "MEDIUM", "LOW"


def prefs(**criteria):
    """{criterion: {objective, priority}} from `criterion=(objective, priority)`."""
    return {c: {"objective": o, "priority": p} for c, (o, p) in criteria.items()}


def infeasible(**fields):
    """The fields a hand-written INFEASIBLE assessment must carry.

    UNIT A. The boundary refuses INFEASIBLE without a structured
    `physical_argument` (INV-011), so a probe that forces a candidate
    infeasible states one - a synthetic contradiction naming synthetic
    premises. The probes below are about what selection DOES with an
    infeasible candidate, not about how it became one.
    """
    out = {"status": "INFEASIBLE",
           "physical_argument": {
               "contradiction": "a probe-stated incompatibility",
               "premises": ["a premise the probe names"],
               "architectural_commitments": ["the probe's candidate"]}}
    out.update(fields)
    return out


class _Selection(_Feas):
    """One accumulated design holding as many candidate branches as a case wants."""

    #: Two mechanisms whose only difference the metrics can see: the four-bar has
    #: four bodies and four joints where the hinge has two and one.
    def design(self, candidates=("A", "B"), state=None, **kw):
        state = state if state is not None else self.seed(**kw)
        self.candidates(state, suffixes=tuple(candidates))
        for sfx in candidates:
            if sfx == "B":
                self.fourbar(state)
            else:
                self.hinge(state, sfx=sfx)
        return state

    def feasible(self, state, candidates=("CND-A", "CND-B")):
        """Run the real feasibility responsibility on each branch."""
        for candidate in candidates:
            self.assess(state, candidate)
        return state

    def built(self, candidates=("A", "B"), **kw):
        state = self.design(candidates, **kw)
        return self.feasible(state, ["CND-%s" % s for s in candidates])

    # -- geometry on an absolute basis, so a volume is comparable -------
    def absolute(self, sfx, boxes, per_unit=10.0, unit="mm"):
        return arrangement(boxes, steps=["ASY-0%s" % sfx], basis="ABSOLUTE",
                           absolute={"unit": unit, "per_unit": per_unit})

    def sized(self, per_unit=10.0, unit="mm", boxes=None):
        """Both candidates given an absolute basis AT CONSTRUCTION - never by
        superseding the scale afterwards, which would stale every envelope
        premised on it and leave feasibility with no arrangement to read."""
        state = self.seed()
        self.candidates(state)
        self.hinge(state, sfx="A",
                   s04a=self.absolute("A", boxes or HINGE_BOXES, per_unit, unit))
        self.fourbar(state, s04a=self.absolute("B", FOURBAR_BOXES, per_unit, unit))
        return self.feasible(state)

    def evidence(self, state):
        """The same `_Evidence` the evaluator builds, from the same real view.

        Used where the CHAIN cannot reach a metric because the defect being
        probed also makes the candidate ineligible - a body with no extent is not
        feasible, so it never gets as far as being measured. The metric is still
        exercised through the real design-wide view and the canonical branch
        helper; only the eligibility gate in front of it is stepped around.
        """
        from ver3.assy_v3.view import consumer_view_for
        view = consumer_view_for(sel.RESPONSIBILITY, state)
        payload = view.payload()
        admitted = sorted(e["entity_id"] for rows in payload.values() for e in rows
                          if isinstance(e, dict) and e.get("entity_id"))
        return sel._Evidence(payload, cv.branch_membership(state, state.c, admitted))

    # -- asking the question -------------------------------------------
    def profile(self, state, preferences, apply_patch=True):
        out = sel.materialize_selection_profile(state, preferences)
        if apply_patch and out.patch is not None:
            state.apply(out.patch)
        return out

    def compare(self, state, preferences=None, apply_patch=True):
        if preferences is not None:
            self.profile(state, preferences)
        out = sel.evaluate_candidate_comparison(state)
        if apply_patch and out.patch is not None:
            state.apply(out.patch)
        return out

    def metric(self, out, criterion, candidate):
        return out.metrics[criterion][candidate]

    def hrc(self, state, candidate, constraint, status, point="PRE_SELECTION",
            owner=None):
        """A compliance record as feasibility would have written it: the status
        and the stamped evaluation point (Unit D). PRE_SELECTION unless the probe
        says the requirement is honestly owed to a later owner, so every
        existing probe keeps asking what it asked - an unanswered requirement
        whose evidence is due before selection."""
        fields = {"candidate": candidate, "constraint": constraint,
                  "status": status, "why": "probe", "evaluation_point": point}
        if owner:
            fields["evidence_owner"] = owner
        self.revise(state, Op("CREATE", "HardRequirementCompliance",
                              "HRC-%s-%s" % (candidate, constraint), fields, "t",
                              premise_refs=[candidate, constraint]),
                    stage="feasibility")

    def constraint(self, state, eid="DSC-P001", blocks=True, kind=None):
        fields = {"kind": kind or "MATERIAL_CLASS_ONLY", "statement": "a probe",
                  "source": "profile", "evaluability": "HUMAN_EVALUABLE"}
        if blocks is not None:
            fields["blocks_selection"] = blocks
        self.revise(state, Op("CREATE", "DesignConstraint", eid, fields, "t"),
                    stage="s01")
        return eid


# =====================================================================
# C01-C09 - the preference snapshot
# =====================================================================
class TestSelectionProfile(_Selection):

    P = prefs(joint_count=(MINIMIZE, HIGH))

    def test_C01_a_preference_enters_state_only_here(self):
        """The materialiser is the first and only writer. Nothing upstream
        produces one, so there is no earlier snapshot to disagree with."""
        state = self.built()
        self.assertEqual([], state.family("SelectionProfile"))
        out = self.profile(state, self.P)
        self.assertEqual(sel.PROFILE_WRITTEN, out.status)
        self.assertEqual("selection",
                         state.entities[out.profile_id]["_created_by"])
        self.assertEqual({"selection"},
                         {e["_created_by"] for e in state.family("SelectionProfile")})
        self.assertEqual(1, len(state.family("SelectionProfile")))

    def test_C02_no_pre_selection_view_can_contain_it(self):
        """The isolation is the input boundary, not a prompt. Feasibility runs
        AFTER the profile exists here, which is the case that matters: a standing
        profile it still cannot see."""
        state = self.design()
        self.profile(state, self.P)
        self.assertTrue(state.family("SelectionProfile"))
        out = self.assess(state, "CND-A")
        self.assertNotIn("SelectionProfile", out.consumer_view["counts"])
        for op in out.patch.operations:
            self.assertNotIn("joint_count", json.dumps(op.fields))
            for ref in op.premise_refs:
                self.assertFalse(ref.startswith("SPF-"), ref)

    def test_C03_key_order_is_not_meaning(self):
        """The same preferences written in a different order are the same
        preferences. A hash over insertion order would reversion the profile for
        nothing and stale every comparison with it."""
        forward = prefs(joint_count=(MINIMIZE, HIGH),
                        package_volume=(MINIMIZE, MEDIUM))
        backward = {}
        for k in reversed(list(forward)):
            backward[k] = forward[k]
        self.assertNotEqual(list(forward), list(backward))
        a = sel.profile_identity(forward)
        b = sel.profile_identity(backward)
        self.assertEqual(a, b)
        state = self.built()
        first = self.profile(state, forward)
        second = self.profile(state, backward)
        self.assertEqual(sel.PROFILE_WRITTEN, first.status)
        self.assertEqual(sel.PROFILE_UNCHANGED, second.status,
                         "reordering the mapping made a second snapshot")
        self.assertEqual(1, len(state.standing("SelectionProfile")))

    def test_C04_an_invalid_objective_rejects_the_whole_snapshot(self):
        state = self.built()
        out = self.profile(state, {
            "joint_count": {"objective": "MINIMIZE", "priority": HIGH},
            "package_volume": {"objective": "SMALLER_IS_NICER", "priority": HIGH}})
        self.assertEqual(sel.PROFILE_INVALID, out.status)
        self.assertTrue(any("SMALLER_IS_NICER" in p for p in out.problems))
        self.assertEqual([], state.family("SelectionProfile"),
                         "a partial profile records preferences nobody stated")

    def test_C05_an_invalid_priority_rejects_the_whole_snapshot(self):
        state = self.built()
        out = self.profile(state, {
            "joint_count": {"objective": MINIMIZE, "priority": "URGENT"}})
        self.assertEqual(sel.PROFILE_INVALID, out.status)
        self.assertEqual([], state.family("SelectionProfile"))

    def test_C06_an_unknown_criterion_is_preserved(self):
        """The user may want something this pipeline cannot measure. Forgetting
        the request is a worse answer than saying the metric does not exist."""
        state = self.built()
        out = self.profile(state, prefs(maintainability=(MAXIMIZE, HIGH)))
        self.assertEqual(sel.PROFILE_WRITTEN, out.status)
        self.assertIn("maintainability",
                      state.entities[out.profile_id]["criteria"])

    def test_C07_no_source_invents_no_profile(self):
        state = self.built()
        out = self.profile(state, None)
        self.assertEqual(sel.NO_SELECTION_PREFERENCES, out.status)
        self.assertEqual([], state.family("SelectionProfile"))
        self.assertIsNone(out.patch)

    def test_C08_an_explicitly_empty_profile_invents_no_criterion(self):
        """Different from no source at all: the user was asked and said nothing
        is ranked. That is a snapshot, and comparison under it honestly reports
        that the evidence does not discriminate."""
        state = self.built()
        out = self.profile(state, {})
        self.assertEqual(sel.PROFILE_WRITTEN, out.status)
        self.assertEqual({}, state.entities[out.profile_id]["criteria"])
        result = self.compare(state)
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, result.outcome)
        self.assertEqual(["CND-A", "CND-B"], result.frontier)

    def test_C09_a_changed_preference_retires_the_old_snapshot(self):
        state = self.built()
        first = self.profile(state, prefs(joint_count=(MINIMIZE, HIGH)))
        comparison = self.compare(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, comparison.status)
        old_cc = comparison.patch.operations[0].entity_id
        self.assertEqual("STANDING", self.val(state, old_cc))

        second = self.profile(state, prefs(joint_count=(MAXIMIZE, HIGH)))
        self.assertEqual(sel.PROFILE_WRITTEN, second.status)
        self.assertNotEqual(first.profile_id, second.profile_id)
        self.assertNotEqual("STANDING", self.val(state, first.profile_id))
        self.assertEqual("STANDING", self.val(state, second.profile_id))
        self.assertEqual("STALE", self.val(state, old_cc),
                         "the comparison outlived the preferences it was made under")
        # AND THE ENGINEERING IS UNTOUCHED. Changing what you want reopens the
        # choice; it does not reopen whether a mechanism works.
        for eid in state.entities:
            if eid.startswith(("MFA-", "HRC-", "FDA-")):
                self.assertEqual("STANDING", self.val(state, eid), eid)


# =====================================================================
# C10-C19 - the eligibility population
# =====================================================================
class TestEligibility(_Selection):

    def five(self):
        """A: eligible. B: eligible. C: infeasible. D: violated. E: unevaluable.

        C, D and E are made by revising the real feasibility artifacts, so the
        shapes are the ones the producer writes."""
        state = self.built(("A", "B", "C", "D", "E"))
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-C", infeasible(), "t",
                              reason="probe"), stage="feasibility")
        constraint = self.constraint(state)
        for candidate, status in (("CND-A", "SATISFIED"), ("CND-B", "SATISFIED"),
                                  ("CND-D", "VIOLATED"),
                                  ("CND-E", "NOT_YET_EVALUABLE")):
            self.hrc(state, candidate, constraint, status)
        return state

    def test_C10_the_eligible_population_is_exactly_the_two(self):
        state = self.five()
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.COMPARISON_WRITTEN, out.status, out.problems)
        self.assertEqual(["CND-A", "CND-B"], out.eligible)
        self.assertEqual({"CND-A": sel.ELIGIBLE, "CND-B": sel.ELIGIBLE,
                          "CND-C": sel.INELIGIBLE, "CND-D": sel.INELIGIBLE,
                          "CND-E": sel.INELIGIBLE},
                         {k: v[0] for k, v in out.population.items()})

    def test_C11_no_preference_can_move_an_ineligible_candidate_in(self):
        """THE CENTRAL INVARIANT, stated as an equality over opposite
        preferences. If a preference could reach eligibility at all, some pair of
        preferences would disagree about the population."""
        seen = []
        for preferences in (prefs(joint_count=(MINIMIZE, HIGH)),
                            prefs(joint_count=(MAXIMIZE, HIGH)),
                            prefs(package_volume=(MAXIMIZE, LOW)),
                            {}):
            state = self.five()
            out = self.compare(state, preferences)
            seen.append(tuple(out.eligible))
            for excluded in ("CND-C", "CND-D", "CND-E"):
                self.assertNotIn(excluded, out.eligible)
                self.assertNotIn(excluded, out.frontier)
        self.assertEqual(1, len(set(seen)), "the population moved with taste")

    def test_C12_a_non_blocking_requirement_does_not_exclude(self):
        state = self.built(("A",))
        blocking = self.constraint(state, "DSC-P001", blocks=True)
        optional = self.constraint(state, "DSC-P002", blocks=False)
        self.hrc(state, "CND-A", blocking, "SATISFIED")
        self.hrc(state, "CND-A", optional, "VIOLATED")
        out = self.compare(state, {})
        self.assertEqual(["CND-A"], out.eligible)
        self.assertEqual(sel.SOLE_ELIGIBLE, out.outcome)

    def test_C13_an_absent_blocks_selection_flag_blocks(self):
        """The contract's declared default is true. Reading the absence as false
        would let a requirement nobody marked stop blocking."""
        state = self.built(("A",))
        unmarked = self.constraint(state, "DSC-P001", blocks=None)
        self.assertIsNone(state.entities[unmarked].get("blocks_selection"))
        self.hrc(state, "CND-A", unmarked, "VIOLATED")
        out = self.compare(state, {})
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.status)
        self.assertEqual([], out.eligible)

    def test_C14_a_candidate_with_no_assessment_stops_the_comparison(self):
        """NOT excluded and NOT assumed. A candidate whose eligibility is unknown
        makes the POPULATION unknown, and there is nothing to compare."""
        state = self.design(("A", "B", "C"))
        self.feasible(state, ["CND-A", "CND-B"])         # C embodied, never assessed
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status)
        self.assertIsNone(out.patch)
        self.assertEqual([], state.family("CandidateComparison"))
        self.assertEqual(sel.UNRESOLVED, out.population["CND-C"][0])

    def test_C15_two_current_assessments_are_ambiguity_not_a_choice(self):
        state = self.built(("A", "B"))
        self.revise(state, Op("CREATE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-A-SECOND",
                              infeasible(candidate="CND-A", domain_assessments=[]),
                              "t",
                              premise_refs=["CND-A"]), stage="feasibility")
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status)
        self.assertEqual(sel.UNRESOLVED, out.population["CND-A"][0])
        self.assertEqual([], state.family("CandidateComparison"))

    def test_C16_a_missing_blocking_compliance_stops_the_comparison(self):
        state = self.built(("A", "B"))
        constraint = self.constraint(state)
        self.hrc(state, "CND-A", constraint, "SATISFIED")   # and none for B
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status)
        self.assertEqual(sel.UNRESOLVED, out.population["CND-B"][0])
        self.assertEqual(sel.ELIGIBLE, out.population["CND-A"][0])

    def test_C17_two_current_compliance_records_are_ambiguity(self):
        state = self.built(("A",))
        constraint = self.constraint(state)
        self.hrc(state, "CND-A", constraint, "SATISFIED")
        self.revise(state, Op("CREATE", "HardRequirementCompliance",
                              "HRC-CND-A-DUP",
                              {"candidate": "CND-A", "constraint": constraint,
                               "status": "VIOLATED", "why": "probe",
                               "evaluation_point": "PRE_SELECTION"}, "t",
                              premise_refs=["CND-A", constraint]),
                    stage="feasibility")
        out = self.compare(state, {})
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status)
        self.assertEqual(sel.UNRESOLVED, out.population["CND-A"][0])

    def test_C18_a_mechanically_infeasible_candidate_needs_no_compliance(self):
        """The prerequisite already failed. Nothing a hard requirement could say
        would make a broken mechanism choosable, so a missing record about it
        leaves nothing unresolved."""
        state = self.built(("A", "B"))
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-B", infeasible(), "t",
                              reason="probe"), stage="feasibility")
        constraint = self.constraint(state)
        self.hrc(state, "CND-A", constraint, "SATISFIED")   # and none for B
        out = self.compare(state, {})
        self.assertEqual(sel.COMPARISON_WRITTEN, out.status, out.problems)
        self.assertEqual(sel.INELIGIBLE, out.population["CND-B"][0])
        self.assertEqual(["CND-A"], out.eligible)

    def test_C19_stale_evidence_is_not_current_evidence(self):
        """An assessment whose premise was withdrawn has lost its authority. It
        is not a current answer, and treating it as one would let a superseded
        verdict decide a live population."""
        state = self.built(("A", "B"))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G1A",
                              {"extent": {"centre": [9, 0, 0],
                                          "half_extent": [1, 1, 1]}},
                              "t", reason="probe"))
        self.assertEqual("STALE", self.val(state, "MFA-CND-A"))
        out = self.compare(state, {})
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status)
        self.assertEqual(sel.UNRESOLVED, out.population["CND-A"][0])


# =====================================================================
# C20-C31 - the metric registry
# =====================================================================
class TestMetrics(_Selection):

    def measured(self, criterion, state=None, candidates=("A", "B")):
        state = state if state is not None else self.built(candidates)
        out = self.compare(state, prefs(**{criterion: (MINIMIZE, HIGH)}))
        return out

    def test_C20_rigid_body_count_is_the_candidate_scoped_body_count(self):
        out = self.measured("rigid_body_count")
        self.assertEqual(2, self.metric(out, "rigid_body_count", "CND-A")["value"])
        self.assertEqual(4, self.metric(out, "rigid_body_count", "CND-B")["value"])
        self.assertEqual("count",
                         self.metric(out, "rigid_body_count", "CND-A")["unit"])

    def test_C21_joint_count_is_the_candidate_scoped_joint_count(self):
        out = self.measured("joint_count")
        self.assertEqual(1, self.metric(out, "joint_count", "CND-A")["value"])
        self.assertEqual(4, self.metric(out, "joint_count", "CND-B")["value"])

    def test_C22_a_body_count_is_never_called_part_count(self):
        """They correlate and they are not the same question. Whether two bodies
        are manufactured separately is a fact no contract here establishes."""
        state = self.built()
        out = self.compare(state, prefs(part_count=(MINIMIZE, HIGH),
                                        rigid_body_count=(MINIMIZE, LOW)))
        part = self.metric(out, "part_count", "CND-A")
        body = self.metric(out, "rigid_body_count", "CND-A")
        self.assertEqual(sel.NOT_AVAILABLE, part["availability"])
        self.assertIsNone(part["value"])
        self.assertEqual(2, body["value"])
        self.assertNotIn("part_count", sel.METRIC_REGISTRY)

    def test_C23_a_joint_count_is_never_called_actuation_complexity(self):
        state = self.built()
        out = self.compare(state, prefs(actuation_complexity=(MINIMIZE, HIGH)))
        m = self.metric(out, "actuation_complexity", "CND-A")
        self.assertEqual(sel.NOT_AVAILABLE, m["availability"])
        self.assertEqual("NO_CANONICAL_METRIC_SOURCE", m["reason_code"])
        self.assertNotIn("actuation_complexity", sel.METRIC_REGISTRY)

    def test_C24_C25_unsupported_criteria_stay_unavailable(self):
        state = self.built()
        out = self.compare(state, prefs(part_count=(MINIMIZE, HIGH),
                                        maintainability=(MAXIMIZE, HIGH),
                                        assembly_complexity=(MINIMIZE, HIGH)))
        for criterion in ("part_count", "maintainability", "assembly_complexity"):
            for candidate in ("CND-A", "CND-B"):
                m = self.metric(out, criterion, candidate)
                self.assertEqual(sel.NOT_AVAILABLE, m["availability"], criterion)
                self.assertEqual("NO_CANONICAL_METRIC_SOURCE", m["reason_code"])
                self.assertIsNone(m["value"])
                self.assertIsNone(m["unit"])
                self.assertEqual([], m["source_refs"],
                                 "a reference was invented for a missing fact")

    def test_C26_a_complete_absolute_arrangement_gives_a_volume(self):
        """The box enclosing the WHOLE candidate: the hinge spans 3.5 x 2 x 2
        relative units, and at 10 mm each that is 35 x 20 x 20."""
        out = self.measured("package_volume", state=self.sized())
        a = self.metric(out, "package_volume", "CND-A")
        self.assertEqual(sel.AVAILABLE, a["availability"])
        self.assertAlmostEqual(35.0 * 20.0 * 20.0, a["value"], places=6)
        self.assertEqual("mm^3", a["unit"])
        for ref in ("BOD-G0A", "BOD-G1A", "ENV-G0A", "ENV-G1A", "SCL-CND-A"):
            self.assertIn(ref, a["source_refs"], ref)

    def test_C26b_it_is_not_the_sum_of_the_bodies(self):
        """Two 20 mm cubes 15 mm apart enclose 35 x 20 x 20 = 14000, where the
        sum of their own boxes is 16000. A design is not its parts added up."""
        out = self.measured("package_volume", state=self.sized())
        self.assertAlmostEqual(14000.0,
                               self.metric(out, "package_volume", "CND-A")["value"])

    def test_C27_a_body_with_no_extent_makes_it_unavailable(self):
        """One of two bodies placed. An overall dimension read off the bodies
        that happen to have been placed is a smaller product answering for the
        real one.

        Probed at the metric, because the chain cannot reach it: a body with no
        extent is not feasible, so the candidate never becomes eligible and never
        gets measured. Both facts are correct and only one of them is this
        metric's."""
        state = self.seed()
        self.candidates(state, suffixes=("A",))
        self.hinge(state, sfx="A", s04a=self.absolute(
            "A", {"BOD-G0A": ([0, 0, 0], [1, 1, 1])}))
        self.feasible(state, ["CND-A"])
        self.profile(state, prefs(package_volume=(MINIMIZE, HIGH)))
        m = sel._package_volume(self.evidence(state), "CND-A")
        self.assertEqual(sel.NOT_AVAILABLE, m.availability)
        self.assertEqual("GEOMETRY_INCOMPLETE", m.reason_code)
        self.assertIsNone(m.value)
        # AND THE CHAIN AGREES for its own reason: an unplaced body is not a
        # feasible candidate, so it is not in the population either.
        out = self.compare(state)
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.status)

    def test_C28_a_doubled_extent_makes_it_unavailable_in_either_order(self):
        seen = []
        for order in (("near", "far"), ("far", "near")):
            boxes = {"near": ([1.5, 0, 0], [1, 1, 1]), "far": ([9, 0, 0], [1, 1, 1])}
            state = self.sized()
            for n, which in enumerate(order):
                self.revise(state, Op(
                    "CREATE", "Envelope", "ENV-DUP-%d" % n,
                    {"body": "BOD-G1A",
                     "extent": {"centre": boxes[which][0],
                                "half_extent": boxes[which][1]},
                     "frame": "world", "maturity": "PROVISIONAL"},
                    "t", premise_refs=["CND-A"]))
            out = self.compare(state, prefs(package_volume=(MINIMIZE, HIGH)))
            m = self.metric(out, "package_volume", "CND-A")
            seen.append((m["availability"], m["reason_code"]))
        self.assertEqual([(sel.NOT_AVAILABLE, "GEOMETRY_AMBIGUOUS")] * 2, seen)

    def test_C29_two_current_bases_make_it_unavailable(self):
        state = self.sized()
        self.revise(state, Op("CREATE", "ReferenceScale", "SCL-SECOND",
                              {"basis": "ABSOLUTE",
                               "absolute": {"unit": "mm", "per_unit": 1.0},
                               "note": "a second current basis"}, "t",
                              premise_refs=["CND-A"]))
        out = self.compare(state, prefs(package_volume=(MINIMIZE, HIGH)))
        m = self.metric(out, "package_volume", "CND-A")
        self.assertEqual(sel.NOT_AVAILABLE, m["availability"])
        self.assertEqual("SCALE_AMBIGUOUS", m["reason_code"])

    def test_C30_a_relative_or_unitless_basis_makes_it_unavailable(self):
        """A RELATIVE basis is honest and it is not a size; two candidates'
        relative volumes are two numbers that mean nothing to each other."""
        out = self.measured("package_volume")            # s04's default RELATIVE
        m = self.metric(out, "package_volume", "CND-A")
        self.assertEqual(sel.NOT_AVAILABLE, m["availability"])
        self.assertEqual("SCALE_NOT_ABSOLUTE", m["reason_code"])

    def test_C30b_a_scale_with_no_factor_never_reaches_a_metric(self):
        """This used to assert that a metric reports SCALE_FACTOR_MISSING for an
        ABSOLUTE basis carrying a unit and no per_unit.

        That state is no longer constructible: `ReferenceScale` declares a
        conditional requirement the write boundary enforces, and `absolute` is
        not extendable, so no canonical path reaches it. The metric's defensive
        branch remains, but the design can no longer arrive at it - and a scale
        that cannot convert anything never becoming the basis of a comparison is
        a better outcome than reporting it after the fact.
        """
        from ver3.assy_v3.state.design_state import ContractError
        state = self.seed()
        self.candidates(state, suffixes=("A",))
        with self.assertRaises(ContractError) as raised:
            self.hinge(state, sfx="A", s04a=arrangement(
                HINGE_BOXES, steps=["ASY-0A"], basis="ABSOLUTE",
                absolute={"unit": "mm"}))                # no per_unit
        self.assertIn("absolute_scale_is_structured", str(raised.exception))

    def test_C31_a_metric_never_reads_another_candidates_evidence(self):
        """Branch membership comes from the canonical helper, so a count is over
        the entities that helper says belong to the branch - never over the ids
        that happen to look like they do."""
        out = self.measured("rigid_body_count")
        for candidate, expected in (("CND-A", {"BOD-G0A", "BOD-G1A"}),
                                    ("CND-B", {"BOD-G0B", "BOD-G1B",
                                               "BOD-G2B", "BOD-G3B"})):
            refs = set(self.metric(out, "rigid_body_count", candidate)["source_refs"])
            self.assertEqual(expected, refs, candidate)
        joints = self.compare(self.built(), prefs(joint_count=(MINIMIZE, HIGH)))
        a = set(self.metric(joints, "joint_count", "CND-A")["source_refs"])
        b = set(self.metric(joints, "joint_count", "CND-B")["source_refs"])
        self.assertEqual(set(), a & b, "one candidate's joints counted for another")


# =====================================================================
# C32-C41 - tiered deterministic comparison
# =====================================================================
class TestComparison(_Selection):

    def outcome(self, criteria, values):
        """The pure algorithm over stated metric values. `values` is
        {criterion: {candidate: value or None}}; None means NOT_AVAILABLE."""
        metrics = {c: {k: (sel.Metric(sel.AVAILABLE, v, "count")
                           if v is not None else sel._unavailable("PROBE"))
                       for k, v in per.items()}
                   for c, per in values.items()}
        return sel.compare(criteria, metrics, sorted(next(iter(values.values()))))

    def test_C32_a_dominant_candidate_at_high_resolves_it(self):
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH)),
            {"package_volume": {"CND-A": 100, "CND-B": 120}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)
        self.assertEqual(HIGH, stopping)

    def test_C33_medium_cannot_overturn_a_resolved_high(self):
        """B is far better at MEDIUM and it does not matter: HIGH already
        discriminated, and the lower tier was never reached."""
        outcome, frontier, _s = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, MEDIUM)),
            {"package_volume": {"CND-A": 100, "CND-B": 120},
             "joint_count": {"CND-A": 40, "CND-B": 1}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)

    def test_C34_a_genuine_high_tradeoff_stays_unresolved(self):
        """A is smaller, B has fewer joints, and the user called both HIGH. That
        disagreement is the answer; MEDIUM does not get to settle it."""
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, HIGH),
                  rigid_body_count=(MINIMIZE, MEDIUM)),
            {"package_volume": {"CND-A": 100, "CND-B": 120},
             "joint_count": {"CND-A": 4, "CND-B": 1},
             "rigid_body_count": {"CND-A": 2, "CND-B": 99}})
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, outcome)
        self.assertEqual(["CND-A", "CND-B"], frontier)
        self.assertEqual(HIGH, stopping)

    def test_C35_an_exact_tie_at_high_lets_medium_decide(self):
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, MEDIUM)),
            {"package_volume": {"CND-A": 100, "CND-B": 100},
             "joint_count": {"CND-A": 1, "CND-B": 4}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)
        self.assertEqual(MEDIUM, stopping)

    def test_C36_an_unavailable_high_metric_stops_at_high(self):
        """No fallback to the tier below. The available subset is a different
        question from the one the user asked."""
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, MEDIUM)),
            {"package_volume": {"CND-A": 100, "CND-B": None},
             "joint_count": {"CND-A": 1, "CND-B": 4}})
        self.assertEqual(sel.NOT_COMPARABLE, outcome)
        self.assertEqual(HIGH, stopping)
        self.assertEqual(["CND-A", "CND-B"], frontier)

    def test_C36b_unavailable_is_neither_good_nor_bad(self):
        """Whichever candidate lacks the metric, the answer is the same. A
        sentinel would make one of them win and the other lose."""
        first = self.outcome(prefs(package_volume=(MINIMIZE, HIGH)),
                             {"package_volume": {"CND-A": 100, "CND-B": None}})
        second = self.outcome(prefs(package_volume=(MINIMIZE, HIGH)),
                              {"package_volume": {"CND-A": None, "CND-B": 100}})
        self.assertEqual(first, second)
        self.assertEqual(sel.NOT_COMPARABLE, first[0])

    def test_C37_an_unavailable_low_metric_does_not_undo_a_resolved_high(self):
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), maintainability=(MAXIMIZE, LOW)),
            {"package_volume": {"CND-A": 100, "CND-B": 120},
             "maintainability": {"CND-A": None, "CND-B": None}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)
        self.assertEqual(HIGH, stopping)

    def test_C38_a_tie_through_every_tier_is_unresolved(self):
        outcome, frontier, _s = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, LOW)),
            {"package_volume": {"CND-A": 100, "CND-B": 100},
             "joint_count": {"CND-A": 3, "CND-B": 3}})
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, outcome)
        self.assertEqual(["CND-A", "CND-B"], frontier)

    def test_C39_candidate_order_cannot_change_the_answer(self):
        """The whole comparison, through the real chain, with the two candidates
        embodied in either order - outcome, frontier AND premise set."""
        def run(order):
            state = self.seed()
            self.candidates(state)
            for sfx in order:
                if sfx == "B":
                    self.fourbar(state)
                else:
                    self.hinge(state, sfx=sfx)
            self.feasible(state)
            out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)),
                               apply_patch=False)
            op = out.patch.operations[0]
            return (out.outcome, tuple(out.frontier), tuple(out.eligible),
                    tuple(op.premise_refs))
        self.assertEqual(run(("A", "B")), run(("B", "A")))

    def test_C40_criterion_order_cannot_change_the_answer(self):
        forward = prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, HIGH))
        backward = {k: forward[k] for k in reversed(list(forward))}

        def run(preferences):
            state = self.built()
            out = self.compare(state, preferences, apply_patch=False)
            op = out.patch.operations[0]
            return (out.outcome, tuple(out.frontier), tuple(op.premise_refs),
                    json.dumps(op.fields["metrics"], sort_keys=True))
        self.assertEqual(run(forward), run(backward))

    def test_C41_no_candidate_id_breaks_a_tie(self):
        """Read from the algorithm: with identical vectors the frontier holds
        both, whatever the ids sort like."""
        for names in (("CND-A", "CND-B"), ("CND-Z", "CND-A")):
            outcome, frontier, _s = sel.compare(
                prefs(joint_count=(MINIMIZE, HIGH)),
                {"joint_count": {n: sel.Metric(sel.AVAILABLE, 3, "count")
                                 for n in names}}, sorted(names))
            self.assertEqual(sel.TRADEOFF_UNRESOLVED, outcome)
            self.assertEqual(sorted(names), frontier)


# =====================================================================
# C42-C48 - what the comparison depends on
# =====================================================================
class TestDependency(_Selection):

    def premises(self, out):
        return set(out.patch.operations[0].premise_refs)

    def test_C42_a_volume_comparison_premises_the_facts_it_measured(self):
        state = self.sized()
        out = self.compare(state, prefs(package_volume=(MINIMIZE, HIGH)),
                           apply_patch=False)
        carried = self.premises(out)
        for eid in ("SPF-", ):
            self.assertTrue(any(p.startswith(eid) for p in carried))
        for eid in ("CND-A", "CND-B", "MFA-CND-A", "MFA-CND-B",
                    "BOD-G0A", "BOD-G1A", "ENV-G0A", "ENV-G1A", "SCL-CND-A"):
            self.assertIn(eid, carried, eid)

    def test_C43_a_count_comparison_does_not_premise_geometry(self):
        """Exactness in the other direction: an envelope the comparison never
        measured is not a dependency, and staling on it would be STALE that
        fires for no reason."""
        state = self.built()
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)),
                           apply_patch=False)
        carried = self.premises(out)
        self.assertIn("JNT-0A", carried)
        for eid in ("ENV-G0A", "ENV-G1A", "SCL-CND-A"):
            self.assertNotIn(eid, carried, eid)

    def test_C44_superseding_a_measured_fact_stales_the_comparison(self):
        state = self.sized()
        out = self.compare(state, prefs(package_volume=(MINIMIZE, HIGH)))
        eid = out.patch.operations[0].entity_id
        self.assertEqual("STANDING", self.val(state, eid))
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G0A",
                              {"extent": {"centre": [0, 0, 0],
                                          "half_extent": [3, 3, 3]}},
                              "t", reason="probe"))
        self.assertEqual("STALE", self.val(state, eid))

    def test_C45_a_fact_no_metric_read_still_reaches_the_population(self):
        """RESTATED AT S7-F, and the restatement is the point.

        This pinned one-hop precision: a geometry change did not stale a
        comparison of JOINT COUNTS, because no metric here read the geometry.
        With transitive currentness the same change reaches the comparison by a
        different road - the envelope is what the spatial verdict was decided
        over, that verdict is what the feasibility assessment aggregates, and
        that assessment is what makes the candidate part of the population being
        compared. A comparison whose eligibility evidence has been withdrawn is
        not a current comparison, whatever its metrics happened to read.

        What must still be precise is the SCOPE: the other candidate's evidence
        is untouched, and the comparison comes back saying the same thing about
        joint counts once feasibility has been re-established."""
        state = self.built()
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        eid = out.patch.operations[0].entity_id
        self.revise(state, Op("SUPERSEDE", "Envelope", "ENV-G0A",
                              {"extent": {"centre": [0, 0, 0],
                                          "half_extent": [3, 3, 3]}},
                              "t", reason="probe"))
        self.assertEqual("STALE", self.val(state, eid))
        self.assertEqual("STANDING", self.val(state, "MFA-CND-B"),
                         "one candidate's geometry reached the other's evidence")

    def test_C45b_an_unrelated_fact_leaves_it_standing(self):
        """The precision half, with a fact nothing in the chain rests on."""
        state = self.built()
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        eid = out.patch.operations[0].entity_id
        self.revise(state, Op("CREATE", "Ambiguity", "AMB-PROBE",
                              {"statement": "an unrelated open question",
                               "conflicting_clauses": [],
                               "resolvable_when": "somebody says"}, "t"),
                    stage="s01")
        self.assertEqual("STANDING", self.val(state, eid))
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual("STANDING", self.val(state, "MFA-%s" % candidate))

    def test_C46_an_excluded_candidates_assessment_change_stales_it(self):
        """The population is part of the answer. A candidate that was ineligible
        becoming eligible is a different comparison."""
        state = self.built(("A", "B"))
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-B", infeasible(), "t",
                              reason="probe"), stage="feasibility")
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        eid = out.patch.operations[0].entity_id
        self.assertEqual(["CND-A"], out.eligible)
        self.assertIn("MFA-CND-B", self.premises(out),
                      "the excluded candidate's evidence is what excluded it")
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-B", {"status": "FEASIBLE_FOR_SELECTION"},
                              "t", reason="probe"), stage="feasibility")
        self.assertEqual("STALE", self.val(state, eid))

    def test_C47_a_preference_change_leaves_every_feasibility_artifact_alone(self):
        state = self.built()
        first = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        before = {eid: self.val(state, eid) for eid in state.entities
                  if eid.startswith(("MFA-", "HRC-", "FDA-"))}
        self.assertTrue(before)
        self.compare(state, prefs(joint_count=(MAXIMIZE, HIGH)))
        self.assertEqual("STALE", self.val(state, first.patch.operations[0].entity_id))
        after = {eid: self.val(state, eid) for eid in before}
        self.assertEqual(before, after,
                         "changing what is wanted reopened whether it works")

    def test_C48_repeating_the_invocation_creates_nothing_new(self):
        state = self.built()
        preferences = prefs(joint_count=(MINIMIZE, HIGH))
        first = self.compare(state, preferences)
        profiles = len(state.family("SelectionProfile"))
        second = self.profile(state, preferences)
        self.assertEqual(sel.PROFILE_UNCHANGED, second.status)
        self.assertEqual(profiles, len(state.family("SelectionProfile")))
        again = sel.evaluate_candidate_comparison(state)
        # THE SAME COMPARISON OF THE SAME EVIDENCE IS NOT A SECOND COMPARISON.
        # This used to be enforced by the write boundary refusing a duplicate id,
        # which was true and was the wrong reason: it made "did anything change?"
        # a question about identity collisions. S7-F asks it directly, so
        # repeating the invocation is silent rather than rejected - and a
        # reconcile over a design nobody touched writes nothing at all.
        self.assertEqual(sel.COMPARISON_UNCHANGED, again.status)
        self.assertIsNone(again.patch)
        self.assertEqual([], again.problems)
        self.assertEqual(1, len(state.family("CandidateComparison")))
        self.assertEqual(1, len(state.family("CandidateComparison")))


# =====================================================================
# C49-C51 - the edges of the population
# =====================================================================
class TestPopulationEdges(_Selection):

    def test_C49_no_eligible_candidate_writes_nothing(self):
        state = self.built(("A",))
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-A", infeasible(), "t",
                              reason="probe"), stage="feasibility")
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.status)
        self.assertIsNone(out.patch)
        self.assertEqual([], state.family("CandidateComparison"))
        self.assertTrue(state.standing("SelectionProfile"),
                        "the profile is still what the user said")

    def test_C50_one_eligible_candidate_is_not_a_decision(self):
        state = self.built(("A",))
        out = self.compare(state, prefs(part_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.SOLE_ELIGIBLE, out.outcome)
        self.assertEqual(["CND-A"], out.frontier)
        self.assertEqual([], state.family("SelectionDecision"))
        fields = out.patch.operations[0].fields
        for forbidden in ("selected_candidate", "winner", "score",
                          "weighted_score"):
            self.assertNotIn(forbidden, fields)

    def test_C51_no_stated_criterion_discriminates_nothing(self):
        state = self.built()
        out = self.compare(state, {})
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, out.outcome)
        self.assertEqual(["CND-A", "CND-B"], out.frontier)


# =====================================================================
# C52-C57 - authority, the runner, and the design-wide state
# =====================================================================
class TestAuthority(_Selection):

    def test_C52_selection_invokes_no_provider(self):
        import inspect
        tree = ast.parse(inspect.getsource(sel))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
            elif isinstance(node, ast.Import):
                imported += [a.name for a in node.names]
        self.assertEqual([], [m for m in imported
                              if "provider" in m or "live" in m], imported)
        called = {n.func.attr for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        for name in ("invoke", "complete", "chat", "generate"):
            self.assertNotIn(name, called)
        for fn in (sel.materialize_selection_profile,
                   sel.evaluate_candidate_comparison):
            self.assertNotIn("provider", inspect.signature(fn).parameters)

    def test_C53_no_other_stage_may_author_these_families(self):
        state = self.built()
        for family, eid in (("SelectionProfile", "SPF-X"),
                            ("CandidateComparison", "CCP-X")):
            for stage in ("s01", "s04", "feasibility"):
                problems = state.validate(StagePatch(
                    patch_id="bad", run_id=state.run_id, stage_id=stage,
                    stage_attempt=1, parent_state_hash=state.state_hash(),
                    operations=[Op("CREATE", family, eid, {}, "t")],
                    execution_status="SUCCESS", provenance={"provider": "t"}))
                self.assertTrue(any("OWNERSHIP" in p or "NOT_OWNER" in p
                                    for p in problems),
                                "%s authored %s: %s" % (stage, family, problems))

    def test_C54_s7c_creates_no_decision_shaped_artifact(self):
        import inspect
        source = inspect.getsource(sel)
        for family in ("SelectionAdvisory", "SelectionConcern",
                       "HumanDecisionInput", "SelectionDecision",
                       "UnresolvedDecision"):
            self.assertNotIn(family, source, family)
        state = self.built()
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual({"SelectionProfile", "CandidateComparison"},
                         {e["_family"] for eid in state.entities
                          for e in [state.entities[eid]]
                          if e.get("_created_by") == "selection"})

    def test_C55_the_comparison_runs_on_one_accumulated_design(self):
        """Every candidate's branch evidence, every assessment and the profile in
        ONE state - and the design-wide view sees all of it. Two states cannot be
        compared, and the fixture proves the pipeline does not make two."""
        state = self.built(("A", "B"))
        out = self.compare(state, prefs(joint_count=(MINIMIZE, HIGH)))
        counts = out.consumer_view["counts"]
        self.assertEqual(2, counts["Candidate"])
        self.assertEqual(2, counts["MechanicalFeasibilityAssessment"])
        self.assertEqual(6, counts["Body"], "both branches' bodies")
        entities = {e["entity_id"] for e in out.consumer_view["entities"]}
        for eid in ("CND-A", "CND-B", "MFA-CND-A", "MFA-CND-B",
                    "BOD-G0A", "BOD-G3B"):
            self.assertIn(eid, entities, eid)
        self.assertIsNone(out.consumer_view["branch"],
                          "a design-wide question was asked from inside a branch")

    def test_C55b_the_runner_accumulates_rather_than_copying(self):
        """The orchestration defect this pass fixed: `run_s03` used to embody
        each candidate into `copy.deepcopy(base_state)`, so the run ended with N
        private designs and nothing to compare."""
        import inspect
        source = inspect.getsource(run_window2.run_s03)
        body = source.split('"""', 2)[2]
        self.assertNotIn("deepcopy", body)
        self.assertNotIn("import copy", body)
        self.assertIn("state = base_state", body)

    def test_C56_the_runner_records_and_decides_nothing(self):
        state = self.built()
        rec = run_window2.run_selection("SYN", state, 1,
                                        prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertEqual(sel.PROFILE_WRITTEN, rec["profile_status"])
        self.assertEqual(sel.COMPARISON_WRITTEN, rec["comparison_status"])
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, rec["outcome"])
        self.assertEqual(["CND-A"], rec["frontier"])
        self.assertEqual([], rec["failures"])
        self.assertEqual("STANDING", self.val(state, "CCP-%s" % state.standing(
            "SelectionProfile")[0]["source_hash"][:12].upper()))
        # AND IT COMPUTES NONE OF IT. Every engineering value it records is
        # copied off the outcome object; the runner calls no comparison helper,
        # reads no metric and evaluates no dominance.
        import inspect
        body = inspect.getsource(run_window2.run_selection).split('"""', 2)[2]
        for helper in ("eligibility(", "compare(", "evaluate_metric(",
                       "METRIC_REGISTRY", "_dominates", "Metric("):
            self.assertNotIn(helper, body, "the runner computes %r itself" % helper)
        for engineering in ("outcome", "frontier", "eligible", "population"):
            self.assertIn("comparison.%s" % engineering, body, engineering)

    def test_C57_a_comparison_cannot_be_built_from_private_states(self):
        """The evaluator takes ONE state and reads ONE view. It has no parameter
        through which a second design could arrive, and no candidate branch
        through which it could be called once per alternative."""
        import inspect
        params = inspect.signature(sel.evaluate_candidate_comparison).parameters
        self.assertEqual(["state", "run_id", "attempt"], list(params))
        for word in ("invocation", "branch", "candidate_id"):
            self.assertNotIn(word, params)
        source = inspect.getsource(sel.evaluate_candidate_comparison)
        self.assertIn("consumer_view_for(RESPONSIBILITY, state)", source)
        self.assertNotIn("InvocationContext", source)
        # Two designs, each holding one candidate: neither can answer the
        # question, and the answer is upstream insufficiency rather than a
        # comparison of one.
        alone = self.built(("A",))
        out = sel.evaluate_candidate_comparison(alone)
        self.assertEqual(sel.PROFILE_MISSING, out.status)


# =====================================================================
# C58-C60 - the runner must not collapse an explicit empty profile
# =====================================================================
class TestRunnerProfileSemantics(_Selection):
    """PRESENCE AND VALUE ARE DIFFERENT QUESTIONS, and truthiness cannot tell
    them apart. `{}` is falsy, so the orchestration turned an explicit "I have
    preferences and none of them is ranked" into "no preference source exists" -
    and the design lost a snapshot the user had actually supplied. The
    materialiser always understood the difference; the runner threw it away
    before getting there.

    Composed exactly as `main` composes it: the extractor, then the runner."""

    def through_the_runner(self, document, state=None):
        preferences = run_window2.selection_preferences(document)
        state = state if state is not None else self.built()
        return state, run_window2.run_selection("SYN", state, 1, preferences)

    def test_C58_an_explicit_empty_profile_survives_the_runner(self):
        state, rec = self.through_the_runner({"selection_preferences": {}})
        self.assertEqual(sel.PROFILE_WRITTEN, rec["profile_status"])
        self.assertNotEqual(sel.NO_SELECTION_PREFERENCES, rec["profile_status"])
        profiles = state.standing("SelectionProfile")
        self.assertEqual(1, len(profiles))
        self.assertEqual({}, profiles[0]["criteria"])
        self.assertEqual([], list(profiles[0]["criteria"]))

    def test_C59_an_absent_source_still_creates_nothing(self):
        for document in (None, {"design_constraints": []}):
            state, rec = self.through_the_runner(document)
            self.assertEqual(sel.NO_SELECTION_PREFERENCES, rec["profile_status"],
                             repr(document))
            self.assertEqual([], state.family("SelectionProfile"))
            self.assertIsNone(rec.get("outcome"))
            self.assertEqual([], rec["failures"])

    def test_C59b_the_extractor_reads_presence_not_truth(self):
        """The three inputs are three different statements. Only the third is
        the user saying they have no ranking."""
        self.assertIsNone(run_window2.selection_preferences(None))
        self.assertIsNone(run_window2.selection_preferences({"design_constraints": []}))
        self.assertEqual({}, run_window2.selection_preferences(
            {"selection_preferences": {}}))
        import inspect
        body = inspect.getsource(run_window2.selection_preferences).split('"""', 2)[2]
        self.assertIn('"selection_preferences" not in profile', body)
        self.assertNotIn("or None", body)

    def test_C60_an_explicit_empty_profile_discriminates_nothing(self):
        """Two eligible candidates and no stated ranking. The honest answer is
        that the evidence does not discriminate - not whichever candidate sorts
        first."""
        state, rec = self.through_the_runner({"selection_preferences": {}})
        self.assertEqual(sel.COMPARISON_WRITTEN, rec["comparison_status"])
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, rec["outcome"])
        self.assertEqual(["CND-A", "CND-B"], sorted(rec["frontier"]))
        self.assertEqual(2, len(rec["frontier"]))
        self.assertEqual([], state.family("SelectionDecision"))


# =====================================================================
# C61-C64 - two established values are not two comparable numbers
# =====================================================================
class TestUnitComparability(_Selection):

    def outcome(self, criteria, values):
        """`values` is {criterion: {candidate: (value, unit) or None}}."""
        metrics = {c: {k: (sel.Metric(sel.AVAILABLE, v[0], v[1])
                           if v is not None else sel._unavailable("PROBE"))
                       for k, v in per.items()}
                   for c, per in values.items()}
        population = sorted(next(iter(values.values())))
        return sel.compare(criteria, metrics, population)

    def test_C61_differing_units_are_not_compared_numerically(self):
        """`2 < 1000` is arithmetic, not physics. A is the smaller volume and the
        numbers say the opposite."""
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH)),
            {"package_volume": {"CND-A": (1000, "mm^3"), "CND-B": (2, "cm^3")}})
        self.assertEqual(sel.NOT_COMPARABLE, outcome)
        self.assertEqual(HIGH, stopping)
        self.assertEqual(["CND-A", "CND-B"], frontier)

    def test_C61b_and_the_direction_of_the_mismatch_does_not_matter(self):
        """Whichever candidate holds the odd unit, the answer is the same - so
        no unit is quietly canonical."""
        first = self.outcome(prefs(package_volume=(MINIMIZE, HIGH)),
                             {"package_volume": {"CND-A": (1000, "mm^3"),
                                                 "CND-B": (2, "cm^3")}})
        second = self.outcome(prefs(package_volume=(MINIMIZE, HIGH)),
                              {"package_volume": {"CND-A": (2, "cm^3"),
                                                  "CND-B": (1000, "mm^3")}})
        self.assertEqual(first, second)

    def test_C62_the_same_unit_still_compares(self):
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH)),
            {"package_volume": {"CND-A": (1000, "mm^3"), "CND-B": (2000, "mm^3")}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)

    def test_C62b_counts_are_always_commensurate(self):
        """`count` is one unit, so the counting metrics never trip this."""
        outcome, frontier, _s = self.outcome(
            prefs(joint_count=(MINIMIZE, HIGH)),
            {"joint_count": {"CND-A": (1, "count"), "CND-B": (4, "count")}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)

    def test_C63_an_incompatible_tier_is_not_bypassed_by_the_next_one(self):
        """MEDIUM discriminates cleanly and does not get to. The user called
        package volume the important question; it is unanswerable, and answering
        a different one instead would be answering a question nobody asked."""
        outcome, frontier, stopping = self.outcome(
            prefs(package_volume=(MINIMIZE, HIGH), joint_count=(MINIMIZE, MEDIUM)),
            {"package_volume": {"CND-A": (1000, "mm^3"), "CND-B": (2, "cm^3")},
             "joint_count": {"CND-A": (10, "count"), "CND-B": (1, "count")}})
        self.assertEqual(sel.NOT_COMPARABLE, outcome)
        self.assertEqual(HIGH, stopping)
        self.assertEqual(["CND-A", "CND-B"], frontier)

    def test_C64_an_unreached_tier_cannot_undo_a_resolved_one(self):
        """HIGH already discriminated, so LOW was never evaluated and its unit
        mismatch is irrelevant."""
        outcome, frontier, stopping = self.outcome(
            prefs(joint_count=(MINIMIZE, HIGH), package_volume=(MINIMIZE, LOW)),
            {"joint_count": {"CND-A": (1, "count"), "CND-B": (4, "count")},
             "package_volume": {"CND-A": (1000, "mm^3"), "CND-B": (2, "cm^3")}})
        self.assertEqual(sel.DOMINANT_UNDER_PROFILE, outcome)
        self.assertEqual(["CND-A"], frontier)
        self.assertEqual(HIGH, stopping)

    def test_C64b_the_record_says_which_criteria_did_not_meet(self):
        """Through the real chain, on two candidates measured in different units
        because their arrangements were stated on different bases. Both metrics
        are AVAILABLE - the incompatibility is a property of the pair."""
        state = self.seed()
        self.candidates(state)
        self.hinge(state, sfx="A",
                   s04a=self.absolute("A", HINGE_BOXES, per_unit=10.0, unit="mm"))
        self.fourbar(state,
                     s04a=self.absolute("B", FOURBAR_BOXES, per_unit=1.0, unit="cm"))
        self.feasible(state)
        out = self.compare(state, prefs(package_volume=(MINIMIZE, HIGH)))
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual(sel.AVAILABLE,
                             self.metric(out, "package_volume", candidate)["availability"])
        self.assertEqual(sel.NOT_COMPARABLE, out.outcome)
        self.assertEqual(HIGH, out.stopping_priority)
        fields = out.patch.operations[0].fields
        self.assertEqual(["package_volume"], fields["incomparable_criteria"])
        self.assertEqual([], fields["unavailable_criteria"],
                         "an incompatible pair is not an unavailable metric")

    def test_C64c_no_conversion_table_was_invented(self):
        """Nothing in this repository is an authority on what one unit is worth
        in another. A conversion would have to be a NUMBER somewhere in the
        comparison path, so the assertion is structural: the four functions that
        decide an ordering contain no numeric literal other than 0 and 1 - the
        length tests - and nothing in the module is named for converting."""
        import inspect
        for fn in (sel.compare, sel._dominates, sel._better,
                   sel.incomparable_criteria):
            tree = ast.parse(inspect.getsource(fn).lstrip())
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(
                        node.value, (int, float)) and not isinstance(node.value, bool):
                    self.assertIn(node.value, (0, 1),
                                  "%s contains the factor %r"
                                  % (fn.__name__, node.value))
        for name in vars(sel):
            for word in ("CONVERSION", "convert", "FACTOR", "SI_"):
                self.assertNotIn(word, name, name)
        # And the check that replaced it is a comparison of the units themselves.
        self.assertIn("len({metrics[c][k].unit for k in frontier}) > 1",
                      inspect.getsource(sel.compare))

# =====================================================================
# The contracts describe what runs
# =====================================================================
class TestContractTruth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.state = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        cls.matrix = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")
        cls.audit = _paths.contract("ENTITY_FAMILY_AUDIT.yaml")
        cls.profile = _paths.contract("USER_DESIGN_PROFILE_CONTRACT.yaml")
        cls.fams = dict(cls.state["entity_families"])
        cls.fams.update(cls.state["assurance_families"])

    def test_the_outcome_vocabulary_is_the_one_the_code_emits(self):
        declared = self.fams["CandidateComparison"]["outcome"]
        self.assertEqual(sorted(declared),
                         sorted([sel.SOLE_ELIGIBLE, sel.DOMINANT_UNDER_PROFILE,
                                 sel.TRADEOFF_UNRESOLVED, sel.NOT_COMPARABLE]))
        self.assertEqual(sorted(self.fams["CandidateComparison"]["availability"]),
                         sorted([sel.AVAILABLE, sel.NOT_AVAILABLE]))
        self.assertEqual(sorted(self.fams["CandidateComparison"]["stopping_priority"]),
                         sorted(sel.PRIORITIES))
        for field in ("outcome", "frontier"):
            self.assertIn(field, self.fams["CandidateComparison"]["required_fields"])
        # A NOT_COMPARABLE record must say which of its two reasons it had.
        for field in ("stopping_priority", "unavailable_criteria",
                      "incomparable_criteria"):
            self.assertIn(field,
                          self.fams["CandidateComparison"]["optional_fields"], field)
        rules = " ".join(self.fams["CandidateComparison"]["rules"])
        self.assertIn("TWO ESTABLISHED VALUES ARE NOT TWO COMPARABLE NUMBERS", rules)

    def test_no_scoring_word_appears_in_the_declaration(self):
        blob = json.dumps(self.fams["CandidateComparison"])
        for forbidden in ("selected_candidate", "winner", "weighted_score"):
            self.assertNotIn(forbidden, blob)

    def test_both_families_are_owned_by_selection_and_produced(self):
        for family in ("SelectionProfile", "CandidateComparison"):
            self.assertEqual("selection", self.fams[family]["owned_by"])
            self.assertIn(family,
                          self.matrix["responsibilities"]["entries"]["selection"]["owns"])
            entry = json.dumps(self.audit["families"][family])
            for phrase in ("has not yet emitted", "no producer"):
                self.assertNotIn(phrase, entry, "%s: %r" % (family, phrase))

    def test_selection_declares_the_roles_its_reasoning_needs(self):
        roles = {r for p in self.resp["stages"]["selection"]
                 ["required_reasoning_premise_classes"]
                 for r in p["requires_semantics"]}
        for family, role in (("MechanicalFeasibilityAssessment", "eligibility_evidence"),
                             ("HardRequirementCompliance", "eligibility_evidence"),
                             ("DesignConstraint", "design_constraint"),
                             ("Body", "topology_element"),
                             ("Joint", "topology_relation"),
                             ("Envelope", "spatial_commitment"),
                             ("ReferenceScale", "spatial_commitment"),
                             ("SelectionProfile", "selection_preference")):
            self.assertIn(role, roles, family)
            self.assertIn(role, self.fams[family]["semantic_roles"], family)

    def test_no_pre_selection_responsibility_declares_the_preference_role(self):
        """The isolation is about WHO IS BEFORE THE BOUNDARY, not about a count.
        All four declarers are passes of ONE owner and all four are at the
        boundary: the reviewer must know the exact profile the comparison was
        made under or its sensitivity statement would be about a preference it
        invented; the human review must show what the comparison was computed
        under rather than let a reader assume a default; and the writer records
        the decision under a named profile version. Every responsibility upstream
        declares none, which is the property - not the number."""
        declaring = [sid for sid, spec in self.resp["stages"].items()
                     if any("selection_preference" in (p.get("requires_semantics") or [])
                            for p in spec.get("required_reasoning_premise_classes") or [])]
        self.assertEqual(["selection", "selection_advisory", "selection_decision",
                          "selection_human_review"], sorted(declaring))
        for upstream in ("s01", "s02", "s03a", "s03b", "s04a", "s04b",
                         "feasibility"):
            self.assertNotIn(upstream, declaring, upstream)
        for sid in declaring:
            self.assertEqual("selection",
                             self.resp["stages"][sid].get("authority_stage", sid),
                             "%s is not a pass of the selection owner" % sid)

    def test_eligibility_cannot_see_a_preference_at_all(self):
        """C-I1 IN ITS STRONGEST FORM. Not "the code does not use the profile" -
        the function has no parameter through which one could arrive, and its
        source names no criterion, objective or priority."""
        import inspect
        params = list(inspect.signature(sel.eligibility).parameters)
        self.assertEqual(["ev"], params)
        body = inspect.getsource(sel.eligibility).split('"""', 2)[2]
        for word in ("criteri", "profile", "objective", "priority", "metric",
                     "preference"):
            self.assertNotIn(word, body.lower(), word)

    def test_every_single_valued_index_is_guarded(self):
        """Each `[0]` in the module sits under an explicit length test, and each
        guard is named here so a new subscript has to be justified."""
        import inspect
        body = inspect.getsource(sel)
        for guard in ("if len(standing) > 1:", "if len(assessments) > 1:",
                      "if len(records) != 1:", "if len(scales) > 1:",
                      "if len(found) != 1:", "if len(profiles) != 1:"):
            self.assertIn(guard, body, guard)
        self.assertNotIn("next(", body)

    def test_no_scalar_aggregate_decides_the_comparison(self):
        """C-I6. A weight, a normalization or a utility function would have to
        collapse a criterion vector into one number, so the comparison collapses
        nothing: `compare` and `_dominates` contain no arithmetic across criteria
        at all - only per-criterion `<` and `>` on their own objectives.

        Scoped to those two functions. The module's `min`/`max` are spatial
        corner reductions inside one metric, which is a volume rather than a
        ranking."""
        import inspect
        for fn in (sel.compare, sel._dominates, sel._better):
            tree = ast.parse(inspect.getsource(fn).lstrip())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, ("sum", "min", "max", "abs",
                                                    "round", "float"),
                                     "%s aggregates across criteria" % fn.__name__)
                if isinstance(node, ast.BinOp):
                    self.assertNotIsInstance(
                        node.op, (ast.Add, ast.Mult, ast.Div, ast.Sub),
                        "%s does arithmetic on metric values" % fn.__name__)

    def test_the_metric_registry_names_no_surrogate(self):
        """The three supported metrics are named for what they count. None of the
        four the brief calls out is in the table, and none is aliased to one."""
        self.assertEqual(sorted(["package_volume", "rigid_body_count",
                                 "joint_count"]),
                         sorted(sel.METRIC_REGISTRY))
        for absent in ("part_count", "assembly_complexity",
                       "actuation_complexity", "maintainability"):
            self.assertNotIn(absent, sel.METRIC_REGISTRY, absent)


if __name__ == "__main__":
    unittest.main()
