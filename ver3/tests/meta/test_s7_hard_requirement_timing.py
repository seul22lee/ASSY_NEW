"""UNIT D: A HARD REQUIREMENT MUST ULTIMATELY BE SATISFIED, AND SELECTION MAY
HAPPEN BEFORE EVIDENCE THAT ONLY A LATER STAGE CAN PRODUCE EXISTS.

Strictness and timing are different facts. "Hard" says the requirement must be
met; the EVALUATION POINT - declared once, per kind, in the design-state
contract - says when the evidence that answers it can exist. The feasibility
responsibility stamps every HardRequirementCompliance with the point and the
evidence owner it evaluated under, and one function of feasibility's
(`compliance_blocks`) is the only reading of that record anywhere:

    SATISFIED                              does not block
    VIOLATED                               INELIGIBLE, at any point
    NOT_YET_EVALUABLE at PRE_SELECTION     INELIGIBLE: required evidence absent
    NOT_YET_EVALUABLE at DOWNSTREAM        eligible, WITH the debt on the record
    no record, or two                      UNRESOLVED - never compliance

WHAT THESE TESTS ARE GUARDING

    Selection reads the stamp and the status, never a reason, a sentence, a
    kind table of its own, or a candidate's name. Feasibility never relabels an
    unanswered requirement as satisfied, and a deferral never hides a
    violation the evidence establishes.

    The debt is visible everywhere a person or a later stage looks: the
    comparison, the review screen, the submission, the commitment.

    Absence is never compliance. A policy nobody declared fails closed; a
    deferral to nobody is refused at the boundary; a missing or duplicate
    record leaves eligibility unresolved.

    A changed requirement, evidence basis or evaluation policy reaches the
    standing screen through the ordinary lifecycle - nothing stands on a
    withdrawn basis.

    Units A-C are untouched: the mechanical answer, the finding classes and the
    owner-revision and repair routing know nothing of any of this.

Synthetic mechanisms only. No product noun, no benchmark id.
"""
from __future__ import annotations

import inspect
import json
import re
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.assurance as assurance                             # noqa: E402
import ver3.assy_v3.assurance.checks as checks                         # noqa: E402
import ver3.assy_v3.assurance.model as model                           # noqa: E402
import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.selection_decision as dec                   # noqa: E402
import ver3.assy_v3.ui.selection_checkpoint as ui                      # noqa: E402
from ver3.assy_v3.lifecycle import records                             # noqa: E402
from ver3.assy_v3.lifecycle import s7_reconcile as lc                  # noqa: E402
from ver3.assy_v3.pipeline import owner_revision as own                # noqa: E402
from ver3.assy_v3.pipeline import repair                               # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from .test_s7_feasibility import HINGE_BOXES, realization              # noqa: E402
from .test_s7_lifecycle import STALE, STANDING, _Lifecycle, _code       # noqa: E402
from .test_s7_selection import HIGH, MINIMIZE, infeasible, prefs        # noqa: E402

PRE, DOWN = s07.PRE_SELECTION, s07.DOWNSTREAM
NYE, SAT, VIO = s07.NOT_YET_EVALUABLE, s07.SATISFIED, s07.VIOLATED
#: The contract's own policy, read here only to name the kinds a probe uses.
DEFERRED_KIND = "MATERIAL_CLASS_ONLY"
REQUIRED_KIND = "PROHIBITED_ENERGY_SOURCE"


class _Timing(_Lifecycle):
    """A compared, reviewable design, with hard requirements stated as the
    profile ingester and the evaluator would state them."""

    P = prefs(joint_count=(MINIMIZE, HIGH))

    def stated(self, state, eid, kind, blocks=True, **parameters):
        fields = {"kind": kind, "statement": "a stated hard requirement",
                  "source": "profile", "blocks_selection": blocks,
                  "evaluability": "MACHINE_EVALUABLE" if parameters else "HUMAN_EVALUABLE"}
        if parameters:
            fields["parameters"] = dict(parameters)
        self.revise(state, Op("CREATE", "DesignConstraint", eid, fields, "t"),
                    stage="s01")
        return eid

    def population(self, state):
        return sel.eligibility(self.evidence(state))

    def compliance(self, state, candidate, constraint):
        return records.current_compliance(state, candidate, constraint)

    def with_policy(self, kind, point, owner):
        """A contract policy other than the declared one, for the length of one
        probe. Patches the ONE accessor the evaluator reads; nothing else in the
        pipeline knows the table exists, which is what this proves too."""
        real = s07.evaluation_timing

        def patched(k):
            if k == kind:
                return {"point": point, "evidence_owner": owner}
            return real(k)
        s07.evaluation_timing = patched
        return real

    def restore(self, real):
        s07.evaluation_timing = real

    def deferred_design(self, candidates=("A", "B")):
        """Both candidates feasible, one DOWNSTREAM requirement stated, the real
        evaluator run: every compliance record NOT_YET_EVALUABLE at DOWNSTREAM."""
        state = self.design(candidates)
        constraint = self.stated(state, "DSC-D001", DEFERRED_KIND)
        self.feasible(state, ["CND-%s" % s for s in candidates])
        return state, constraint


# =====================================================================
# 1-4 - the rule, status by status
# =====================================================================
class TestTheRule(_Timing):

    def test_T01_a_satisfied_blocking_requirement_does_not_block(self):
        for point, owner in ((PRE, None), (DOWN, "s05")):
            with self.subTest(point):
                state = self.built(("A", "B"))
                constraint = self.constraint(state)
                for candidate in ("CND-A", "CND-B"):
                    self.hrc(state, candidate, constraint, SAT, point, owner)
                out = self.compare(state, self.P)
                self.assertEqual(sel.COMPARISON_WRITTEN, out.status, out.problems)
                self.assertEqual(["CND-A", "CND-B"], out.eligible)
                self.assertEqual({"CND-A": [], "CND-B": []},
                                 self.comparison(state)["deferred_hard_requirements"])

    def test_T02_a_violated_requirement_is_ineligible_at_any_point(self):
        for point, owner in ((PRE, None), (PRE, "s02"), (DOWN, "s05")):
            with self.subTest(point):
                state = self.built(("A", "B"))
                constraint = self.constraint(state)
                self.hrc(state, "CND-A", constraint, VIO, point, owner)
                self.hrc(state, "CND-B", constraint, SAT, point, owner)
                verdict, why, used = self.population(state)["CND-A"]
                self.assertEqual(sel.INELIGIBLE, verdict)
                self.assertIn("violated", why)
                self.assertIn("HRC-CND-A-%s" % constraint, used)
                out = self.compare(state, self.P)
                self.assertEqual(["CND-B"], out.eligible)
                self.assertNotIn("CND-A", self.comparison(state)["deferred_hard_requirements"])

    def test_T03_pre_selection_not_yet_evaluable_is_ineligible(self):
        """Required evidence absent. By hand, and through the real evaluator on
        a kind the contract declares PRE_SELECTION."""
        state = self.built(("A", "B"))
        constraint = self.constraint(state)
        self.hrc(state, "CND-A", constraint, NYE, PRE, "s02")
        self.hrc(state, "CND-B", constraint, SAT, PRE, "s02")
        verdict, why, _used = self.population(state)["CND-A"]
        self.assertEqual(sel.INELIGIBLE, verdict)
        self.assertIn("required before selection", why)
        self.assertIn("s02", why)
        self.assertEqual(["CND-B"], self.compare(state, self.P).eligible)

        state = self.design(("A", "B"))
        stated = self.stated(state, "DSC-E001", REQUIRED_KIND, source="MAINS_ELECTRICAL")
        self.feasible(state)
        for candidate in ("CND-A", "CND-B"):
            record = self.compliance(state, candidate, stated)
            self.assertEqual(NYE, record["status"])
            self.assertEqual(PRE, record["evaluation_point"])
            self.assertEqual("s02", record["evidence_owner"])
            self.assertEqual(sel.INELIGIBLE, self.population(state)[candidate][0])
        out = self.compare(state, self.P)
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.status)
        self.assertIsNone(self.comparison(state))

    def test_T04_downstream_not_yet_evaluable_does_not_make_a_feasible_candidate_ineligible(self):
        state, constraint = self.deferred_design()
        for candidate in ("CND-A", "CND-B"):
            record = self.compliance(state, candidate, constraint)
            self.assertEqual(NYE, record["status"], "the evaluator relabelled it")
            self.assertEqual(DOWN, record["evaluation_point"])
            self.assertEqual("s05", record["evidence_owner"])
            self.assertEqual(s07.FEASIBLE, self.mfa(state, candidate)["status"])
            verdict, why, used = self.population(state)[candidate]
            self.assertEqual(sel.ELIGIBLE, verdict, why)
            self.assertIn("deferred", why)
            self.assertIn("%s -> s05" % constraint, why)
            self.assertIn(record["entity_id"], used, "the record was not read")
        out = self.compare(state, self.P)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.status, out.problems)
        self.assertEqual(["CND-A", "CND-B"], out.eligible)
        rows = self.comparison(state)["deferred_hard_requirements"]
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual([{"constraint": constraint,
                               "compliance": "HRC-%s-%s" % (candidate, constraint),
                               "evidence_owner": "s05"}], rows[candidate])

    def test_T04b_a_deferral_does_not_rescue_a_candidate_that_is_not_feasible(self):
        """The mechanical prerequisite is read first and is not weakened: a
        NOT_ESTABLISHED or INFEASIBLE candidate stays ineligible whatever its
        compliance records defer."""
        state = self.design(("A", "B"))
        constraint = self.stated(state, "DSC-D002", DEFERRED_KIND)
        self.feasible(state)
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-B", infeasible(), "t", reason="probe"),
                    stage="feasibility")
        self.assertEqual(DOWN, self.compliance(state, "CND-B", constraint)["evaluation_point"])
        verdict, why, _used = self.population(state)["CND-B"]
        self.assertEqual(sel.INELIGIBLE, verdict)
        self.assertIn("INFEASIBLE", why)
        self.assertEqual(["CND-A"], self.compare(state, self.P).eligible)

        state = self.seed()
        self.candidates(state, suffixes=("A",))
        self.hinge(state, sfx="A", s03b=realization("A", terminates=None))
        self.stated(state, "DSC-D003", DEFERRED_KIND)
        self.assess(state)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, self.mfa(state)["status"])
        verdict, why, _used = self.population(state)["CND-A"]
        self.assertEqual(sel.INELIGIBLE, verdict)
        self.assertIn("NOT_ESTABLISHED", why)


# =====================================================================
# 5 - the debt is visible wherever a person or a later stage looks
# =====================================================================
class TestVisibleDebt(_Timing):

    def test_T05_the_deferred_requirement_is_visible_on_the_comparison_the_screen_and_the_records(self):
        state, constraint = self.deferred_design()
        self.compare(state, self.P)
        snapshot = self.review_of(state)
        expected = [{"candidate": c, "constraint": constraint,
                     "compliance": "HRC-%s-%s" % (c, constraint), "evidence_owner": "s05"}
                    for c in ("CND-A", "CND-B")]
        self.assertEqual(expected, list(snapshot.deferred_hard_requirements))
        self.assertEqual(expected[:1], [dict(r, candidate="CND-A")
                                        for r in snapshot.deferred_for("CND-A")])
        # THE SCREEN says it under its own heading, names the owner, and never
        # folds it into why the candidate is eligible
        text = "\n".join(ui.review_lines(snapshot))
        self.assertIn(ui.DEFERRED_LABEL, text)
        self.assertIn(ui.DEFERRED_NOTE, text)
        self.assertNotIn(ui.DEFERRED_ABSENT, text)
        self.assertIn("CND-A: %s is NOT_YET_EVALUABLE now and must be established by s05"
                      % constraint, text)
        self.assertEqual([constraint], ui.comparison_rows(snapshot)[0]["deferred"])
        for row in snapshot.eligibility:
            self.assertEqual(sel.ELIGIBLE, row["verdict"])
        # THE DIGEST covers it: a review without the rows is a different review
        payload = snapshot.payload()
        self.assertEqual(expected, payload["deferred_hard_requirements"])
        stripped = dict(payload, deferred_hard_requirements=[])
        self.assertNotEqual(snapshot.digest, dec.human_review_digest(stripped))
        # THE SUBMISSION and THE COMMITMENT carry the chosen candidate's rows
        submitted = self.submit(state, snapshot, dec.SELECT, "CND-A")
        self.assertTrue(submitted.ok, submitted.problems)
        human = state.standing("HumanDecisionInput")[0]
        self.assertEqual([{"constraint": constraint,
                           "compliance": "HRC-CND-A-%s" % constraint,
                           "evidence_owner": "s05"}],
                         human["deferred_hard_requirements"])
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        decision = self.committed_decision(state)
        self.assertEqual(human["deferred_hard_requirements"],
                         decision["deferred_hard_requirements"])
        self.assertIn("HRC-CND-A-%s" % constraint, decision["hard_requirement_results"])
        self.assertIn("HRC-CND-A-%s" % constraint, decision["_premises"])

    def test_T05b_absence_of_debt_is_stated_as_absence(self):
        state = self.reviewable()
        snapshot = self.review_of(state)
        self.assertEqual((), snapshot.deferred_hard_requirements)
        text = "\n".join(ui.review_lines(snapshot))
        self.assertIn(ui.DEFERRED_ABSENT, text)
        self.assertNotIn(ui.DEFERRED_NOTE, text)
        self.assertEqual({"CND-A": [], "CND-B": []},
                         self.comparison(state)["deferred_hard_requirements"])
        submitted = self.submit(state, snapshot, dec.SELECT, "CND-A")
        self.assertEqual([], state.standing("HumanDecisionInput")[0]["deferred_hard_requirements"])
        self.commit(state, submitted.input_id)
        self.assertEqual([], self.committed_decision(state)["deferred_hard_requirements"])

    def test_T05c_a_keep_open_records_no_candidate_and_so_no_debt(self):
        state, _constraint = self.deferred_design()
        self.compare(state, self.P)
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.KEEP_UNRESOLVED, None)
        self.assertTrue(submitted.ok, submitted.problems)
        self.assertNotIn("deferred_hard_requirements",
                         state.standing("HumanDecisionInput")[0])


# =====================================================================
# 6-8 - absence is not compliance, and selection reads only the stamp
# =====================================================================
class TestAbsenceAndTheStamp(_Timing):

    def test_T06_a_missing_compliance_record_is_not_compliance(self):
        state = self.built(("A", "B"))
        constraint = self.constraint(state)
        self.hrc(state, "CND-A", constraint, NYE, DOWN, "s05")     # and none for B
        population = self.population(state)
        self.assertEqual(sel.ELIGIBLE, population["CND-A"][0])
        self.assertEqual(sel.UNRESOLVED, population["CND-B"][0])
        out = self.compare(state, self.P)
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status)
        self.assertIsNone(self.comparison(state))

    def test_T07_a_duplicate_compliance_record_is_not_compliance(self):
        state = self.built(("A",))
        constraint = self.constraint(state)
        self.hrc(state, "CND-A", constraint, NYE, DOWN, "s05")
        self.revise(state, Op("CREATE", "HardRequirementCompliance", "HRC-CND-A-DUP",
                              {"candidate": "CND-A", "constraint": constraint,
                               "status": SAT, "why": "probe", "evaluation_point": PRE},
                              "t", premise_refs=["CND-A", constraint]),
                    stage="feasibility")
        verdict, why, _used = self.population(state)["CND-A"]
        self.assertEqual(sel.UNRESOLVED, verdict)
        self.assertIn("2 current compliance records", why)
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, self.compare(state, self.P).status)

    def test_T08_selection_reads_the_stamp_and_never_a_reason_a_kind_or_a_name(self):
        # STRUCTURALLY: one reading, feasibility's, and no table of its own
        source = _code(inspect.getsource(sel.eligibility))
        self.assertIn("compliance_blocks(", source)
        for token in ("evaluation_point", "DOWNSTREAM", "PRE_SELECTION", '"why"',
                      "reason", "kind", "evidence_owner ==", "NOT_YET_EVALUABLE"):
            self.assertNotIn(token, source, token)
        module = _code(inspect.getsource(sel))
        for token in ("evaluation_policy", "evaluation_timing", '"kinds"', "Contracts("):
            self.assertNotIn(token, module, token)
        # BEHAVIOURALLY: the words on the record change nothing; the stamp does
        deferred = {"constraint": "DSC-X", "status": NYE, "evaluation_point": DOWN,
                    "evidence_owner": "s05", "why": "violated, exceeded, failed"}
        self.assertIsNone(s07.compliance_blocks(deferred))
        self.assertTrue(s07.compliance_deferred(deferred))
        self.assertIsNotNone(s07.compliance_blocks(dict(deferred, evaluation_point=PRE)))
        self.assertIsNotNone(s07.compliance_blocks(dict(deferred, evidence_owner="")))
        self.assertIsNotNone(s07.compliance_blocks(
            {k: v for k, v in deferred.items() if k != "evaluation_point"}))
        self.assertIsNotNone(s07.compliance_blocks(
            {k: v for k, v in deferred.items() if k != "evidence_owner"}))
        self.assertIsNotNone(s07.compliance_blocks(dict(deferred, status="PASS")))
        self.assertIsNotNone(s07.compliance_blocks(dict(deferred, status=VIO)))
        self.assertIsNone(s07.compliance_blocks({"constraint": "DSC-X", "status": SAT,
                                                 "why": "not yet evaluable"}))
        satisfied_words = dict(deferred, evaluation_point=PRE, why="SATISFIED")
        self.assertIn("required before selection", s07.compliance_blocks(satisfied_words))
        for record in (deferred, dict(deferred, status=VIO)):
            for name in ("CND-0001", "CND-Z"):
                self.assertEqual(s07.compliance_blocks(record),
                                 s07.compliance_blocks(dict(record, candidate=name)))

    def test_T08b_the_boundary_refuses_a_deferral_to_nobody_and_a_record_with_no_point(self):
        state = self.built(("A",))
        constraint = self.constraint(state)
        for fields, expected in (
                ({"status": NYE, "evaluation_point": DOWN}, "CONDITIONAL_REQUIRED"),
                ({"status": NYE}, "MISSING_REQUIRED"),
                ({"status": SAT}, "MISSING_REQUIRED")):
            with self.subTest(expected):
                problems = state.validate(StagePatch(
                    patch_id="bad", run_id=state.run_id, stage_id="feasibility",
                    stage_attempt=1, parent_state_hash=state.state_hash(),
                    operations=[Op("CREATE", "HardRequirementCompliance", "HRC-BAD",
                                   dict(fields, candidate="CND-A", constraint=constraint,
                                        why="probe"), "t")],
                    execution_status="SUCCESS", provenance={"provider": "t"}))
                self.assertTrue(any(expected in p for p in problems), problems)


# =====================================================================
# 9-10 - feasibility neither relabels nor launders
# =====================================================================
class TestTheEvaluatorIsHonest(_Timing):

    def test_T09_feasibility_never_relabels_not_yet_evaluable_as_satisfied(self):
        """The status is what the evidence established; the stamp is what the
        contract declared. Changing the policy changes the stamp and nothing
        else, and the evaluators cannot see the policy at all."""
        state = self.design(("A",))
        material = self.stated(state, "DSC-M001", DEFERRED_KIND, material_class="PLASTIC")
        load = self.stated(state, "DSC-L001", "LOAD_CAPACITY", magnitude=50, unit="N")
        out = self.assess(state)
        by_id = {c["entity_id"]: (status, codes) for c, status, codes, _u, _w in out.compliance}
        self.assertEqual(NYE, by_id[material][0])
        self.assertIn("NO_MATERIAL_AUTHORITY", by_id[material][1])
        self.assertEqual(NYE, by_id[load][0])
        self.assertIn("NO_EVALUATOR_FOR_KIND", by_id[load][1])
        for eid in (material, load):
            record = self.compliance(state, "CND-A", eid)
            self.assertEqual((NYE, DOWN, "s05"), (record["status"], record["evaluation_point"],
                                                  record["evidence_owner"]))
        real = self.with_policy(DEFERRED_KIND, PRE, "s02")
        try:
            out = self.assess(state)
            statuses = {c["entity_id"]: s for c, s, _c, _u, _w in out.compliance}
            self.assertEqual(NYE, statuses[material])
            record = self.compliance(state, "CND-A", material)
            self.assertEqual((NYE, PRE, "s02"), (record["status"], record["evaluation_point"],
                                                 record["evidence_owner"]))
        finally:
            self.restore(real)
        for fn in (s07.evaluate_hard_requirements, s07._material_class_only,
                   s07._max_overall_dimension, s07._prohibited_energy_source):
            source = _code(inspect.getsource(fn))
            for token in ("evaluation_point", "evaluation_timing", "DOWNSTREAM",
                          "PRE_SELECTION", "evidence_owner"):
                self.assertNotIn(token, source, "%s reads the policy" % fn.__name__)

    def test_T10_a_known_violation_is_not_laundered_by_downstream_timing(self):
        state = self.seed()
        self.candidates(state, suffixes=("A",))
        self.hinge(state, sfx="A", s04a=self.absolute("A", HINGE_BOXES, 10.0, "mm"))
        tight = self.stated(state, "DSC-X001", "MAX_OVERALL_DIMENSION",
                            axis="ANY", limit=10, unit="mm")
        real = self.with_policy("MAX_OVERALL_DIMENSION", DOWN, "s05")
        try:
            self.assess(state)
        finally:
            self.restore(real)
        record = self.compliance(state, "CND-A", tight)
        self.assertEqual((VIO, DOWN, "s05"), (record["status"], record["evaluation_point"],
                                              record["evidence_owner"]))
        self.assertFalse(s07.compliance_deferred(record))
        verdict, why, _used = self.population(state)["CND-A"]
        self.assertEqual(sel.INELIGIBLE, verdict)
        self.assertIn("violated", why)
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, self.compare(state, self.P).status)


# =====================================================================
# 11 - the lifecycle: nothing stands on a withdrawn basis
# =====================================================================
class TestLifecycle(_Timing):

    def committed_with_debt(self):
        state, constraint = self.deferred_design()
        self.compare(state, self.P)
        out = self.decide(state, "CND-A", "chosen with its debt on the screen")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        return state, constraint, self.committed_decision(state)["entity_id"]

    def test_T11_a_changed_evaluation_policy_rebuilds_the_records_and_reopens_the_screen(self):
        state, constraint, decision = self.committed_with_debt()
        old = {c: self.compliance(state, c, constraint)["entity_id"] for c in ("CND-A", "CND-B")}
        real = self.with_policy(DEFERRED_KIND, PRE, "s02")
        try:
            out = self.reconcile(state)
        finally:
            self.restore(real)
        for candidate, eid in old.items():
            self.assertEqual("INVALIDATED", self.validity(state, eid))
            new = self.compliance(state, candidate, constraint)
            self.assertNotEqual(eid, new["entity_id"])
            self.assertEqual((NYE, PRE, "s02"), (new["status"], new["evaluation_point"],
                                                 new["evidence_owner"]))
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.comparison)
        self.assertIsNone(self.comparison(state))
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertIsNone(lc.current_commitment(state))
        # AND BACK: the declared policy again re-creates the deferred records
        # and a fresh comparison; the old commitment stays history
        again = self.reconcile(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, again.comparison)
        self.assertEqual(DOWN, self.compliance(state, "CND-A", constraint)["evaluation_point"])
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertIsNone(lc.current_commitment(state))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, again.human_state)

    def test_T11b_a_revised_requirement_stales_the_record_and_the_screen(self):
        state, constraint, decision = self.committed_with_debt()
        hrc = self.compliance(state, "CND-A", constraint)["entity_id"]
        self.supersede(state, constraint, {"kind": REQUIRED_KIND}, stage="s01",
                       why="the user restated the requirement")
        self.assertEqual(STALE, self.validity(state, hrc))
        self.assertEqual(STALE, self.validity(state, decision))
        out = self.reconcile(state)
        new = self.compliance(state, "CND-A", constraint)
        self.assertEqual((NYE, PRE, "s02"), (new["status"], new["evaluation_point"],
                                             new["evidence_owner"]))
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.comparison)
        self.assertIsNone(lc.current_commitment(state))

    def test_T11c_an_unchanged_design_reconciles_to_nothing(self):
        state, _constraint, decision = self.committed_with_debt()
        out = self.reconcile(state)
        self.assertFalse(out.changed, out.as_dict())
        self.assertEqual(STANDING, self.validity(state, decision))
        self.assertEqual(lc.CURRENT_COMMITMENT, out.human_state)

    def test_T11d_a_new_deferred_requirement_reopens_the_review_not_the_population(self):
        """A requirement stated after the commitment defers to a later stage:
        the candidates stay eligible, but the person decided without seeing
        the debt, so the comparison is remade and the commitment reopens."""
        state, decision = self.committed()
        self.stated(state, "DSC-NEW", DEFERRED_KIND)
        out = self.reconcile(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(["CND-A", "CND-B"], sorted(self.comparison(state)["candidates"]))
        self.assertEqual(["DSC-NEW"], [r["constraint"] for r in
                                       self.comparison(state)["deferred_hard_requirements"]["CND-A"]])
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertIsNone(lc.current_commitment(state))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state)

    def test_T11e_a_deferral_arriving_under_a_screen_stales_it_and_a_fresh_screen_commits(self):
        """E30's counterpart. The screen the person submitted from did not show
        the debt, so the submission is refused; a screen that shows it commits."""
        state = self.reviewable()
        constraint = self.blocking(state, {"CND-A": SAT, "CND-B": SAT})
        self.compare(state)
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.SELECT, "CND-A")
        self.recompliance(state, "CND-A", constraint, NYE, DOWN, "s05")
        out = self.commit(state, submitted.input_id)
        self.assertFalse(out.committed, out.status)
        self.assertNoCommitment(state, out)
        self.reconcile(state)
        fresh = self.review_of(state)
        self.assertEqual([constraint], [r["constraint"] for r in fresh.deferred_for("CND-A")])
        again = self.decide(state, "CND-A", "seen, and chosen anyway", snapshot=fresh)
        self.assertEqual(dec.SELECTION_COMMITTED, again.status, again.problems)
        # the record the reconcile wrote over the hand-written one, whatever id
        # the lifecycle gave it - read, never guessed
        current = self.compliance(state, "CND-A", constraint)
        self.assertEqual((NYE, DOWN, "s05"), (current["status"], current["evaluation_point"],
                                              current["evidence_owner"]))
        self.assertEqual([{"constraint": constraint, "compliance": current["entity_id"],
                           "evidence_owner": "s05"}],
                         self.committed_decision(state)["deferred_hard_requirements"])


# =====================================================================
# 12-15 - Units A-C untouched, the human, and locality
# =====================================================================
class TestUntouchedAndLocal(_Timing):

    def test_T12_the_mechanical_answer_and_its_classes_are_unchanged(self):
        state, _constraint = self.deferred_design()
        mfa = self.mfa(state)
        self.assertEqual(s07.FEASIBLE, mfa["status"])
        self.assertNotIn("evaluation_point", json.dumps(mfa))
        self.assertEqual(sorted(s07.DOMAINS), sorted(mfa["evaluated_domains"]))
        table = s07.classification()
        self.assertEqual({"class": "OWNER_REVISION", "owner": "s03a"},
                         {k: table["codes"]["REGION_WITHOUT_OWNER"][k] for k in ("class", "owner")})
        self.assertEqual("REPAIRABLE_S04", table["codes"]["HOP_BODIES_APART"]["class"])
        self.assertNotIn("evaluation", json.dumps(table))
        source = _code(inspect.getsource(sel.eligibility))
        self.assertIn('mfa.get("status")', source)

    def test_T13_owner_revision_and_repair_routing_know_nothing_of_it(self):
        for module in (own, repair):
            source = _code(inspect.getsource(module))
            for token in ("HardRequirementCompliance", "evaluation_point", "compliance_",
                          "DesignConstraint", "DOWNSTREAM"):
                self.assertNotIn(token, source, "%s reads %r" % (module.__name__, token))
        state, constraint = self.deferred_design(("A",))
        before = json.dumps(self.compliance(state, "CND-A", constraint), sort_keys=True, default=str)
        from ver3.assy_v3.pipeline import progression
        from ver3.assy_v3.view import InvocationContext
        inv = InvocationContext(branch="CND-A")
        rep = repair.s04_repair_rounds(None, state, progression.Progression(), inv, rounds=2)
        out = own.s03_owner_revision_rounds(None, state, progression.Progression(), inv, rounds=2)
        self.assertEqual(repair.SETTLED, rep.status, rep.as_record())
        self.assertEqual(own.SETTLED, out.status, out.as_record())
        self.assertEqual([], out.open + out.unrouted)
        self.assertEqual(before, json.dumps(self.compliance(state, "CND-A", constraint),
                                            sort_keys=True, default=str))

    def test_T14_the_human_remains_the_only_chooser(self):
        state, _constraint = self.deferred_design(("A",))
        out = self.compare(state, self.P)
        self.assertEqual(sel.SOLE_ELIGIBLE, out.outcome)
        self.reconcile(state)
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual([], state.family("HumanDecisionInput"))
        for module in (sel, dec, ui, s07):
            source = _code(inspect.getsource(module))
            for token in ("auto_select", "best_candidate", "rank(", "score("):
                self.assertNotIn(token, source, "%s: %s" % (module.__name__, token))
        source = _code(inspect.getsource(dec.commit_human_selection))
        self.assertNotIn("deferred", source, "the writer branches on the debt")
        self.assertEqual(s07.FEASIBLE, self.mfa(state)["status"])

    def test_T15_one_candidates_compliance_moves_no_other_candidate(self):
        state, constraint = self.deferred_design()
        self.compare(state, self.P)
        # B's OWN records: candidate-scoped, never the design-wide comparison,
        # which rests on every candidate's evidence and is expected to move
        other = {e: json.dumps(r, sort_keys=True, default=str)
                 for e, r in state.entities.items()
                 if (r.get("candidate") == "CND-B" or e.endswith("B"))
                 and r.get("_family") not in ("CandidateComparison", "SelectionProfile")}
        self.assertTrue(other)
        self.assertIn("HRC-CND-B-%s" % constraint, other)
        self.recompliance(state, "CND-A", constraint, VIO, DOWN, "s05")
        population = self.population(state)
        self.assertEqual(sel.INELIGIBLE, population["CND-A"][0])
        self.assertEqual(sel.ELIGIBLE, population["CND-B"][0])
        for eid, before in other.items():
            self.assertEqual(before, json.dumps(state.entities[eid], sort_keys=True,
                                                default=str), eid)
        out = self.compare(state, self.P)
        self.assertEqual(["CND-B"], out.eligible)
        self.assertEqual(["CND-B"], sorted(self.comparison(state)["deferred_hard_requirements"]))

    def test_T16_no_benchmark_or_candidate_is_named(self):
        for module in (sel, s07, dec, ui, checks):
            self.assertIsNone(re.search(r"\bBM-\d|\bCND-\d", inspect.getsource(module)),
                              module.__name__)


# =====================================================================
# 17-19 - the contract, the policy accessor, and the external check
# =====================================================================
class TestContractAndAssurance(_Timing):

    def test_T17_the_policy_is_declared_once_and_read_from_there(self):
        from ver3.assy_v3.state.design_state import Contracts
        fams = Contracts().families
        stages = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")["stages"]
        hrc = fams["HardRequirementCompliance"]
        self.assertEqual(["PRE_SELECTION", "DOWNSTREAM"], hrc["evaluation_point"])
        self.assertIn("evaluation_point", hrc["required_fields"])
        self.assertIn("evidence_owner", hrc["optional_fields"])
        self.assertEqual(["a_deferral_names_its_owner"],
                         [r["name"] for r in hrc["conditional_requirements"]])
        kinds = fams["DesignConstraint"]["kinds"]
        self.assertTrue(kinds)
        for kind, spec in kinds.items():
            with self.subTest(kind):
                policy = spec["evaluation"]
                self.assertIn(policy["point"], hrc["evaluation_point"])
                self.assertIn(policy["evidence_owner"], stages,
                              "%s names an owner no responsibility declares" % kind)
                self.assertEqual(policy, s07.evaluation_policy()[kind])
                self.assertEqual(policy, s07.evaluation_timing(kind))
        self.assertEqual({DEFERRED_KIND: DOWN, REQUIRED_KIND: PRE},
                         {k: s07.evaluation_timing(k)["point"] for k in (DEFERRED_KIND, REQUIRED_KIND)})
        for family in ("CandidateComparison", "HumanDecisionInput", "SelectionDecision"):
            self.assertIn("deferred_hard_requirements", fams[family]["optional_fields"], family)
        rules = " ".join(hrc["rules"])
        for phrase in ("NOT AN INFERENCE", "WHAT SELECTION MAY DO WITH IT", "never launders"):
            self.assertIn(phrase, rules)
        # NO SECOND TABLE anywhere the pipeline reads timing from
        for module in (sel, dec, ui, checks, lc):
            source = _code(inspect.getsource(module))
            self.assertNotIn("MATERIAL_CLASS_ONLY", source, module.__name__)
            self.assertNotIn("evaluation_policy", source, module.__name__)

    def test_T17b_an_undeclared_policy_fails_closed(self):
        self.assertEqual({"point": PRE, "evidence_owner": None},
                         s07.evaluation_timing("SOME_KIND_NOBODY_DECLARED"))
        self.assertEqual({"point": PRE, "evidence_owner": None}, s07.evaluation_timing(None))
        saved = s07._EVALUATION_POLICY
        try:
            s07._EVALUATION_POLICY = {"K": {"point": DOWN},
                                      "L": {"point": DOWN, "evidence_owner": ""},
                                      "M": {"point": "LATER", "evidence_owner": "s05"}}
            for kind in ("K", "L", "M"):
                self.assertEqual(PRE, s07.evaluation_timing(kind)["point"], kind)
        finally:
            s07._EVALUATION_POLICY = saved
        state = self.design(("A",))
        undeclared = self.stated(state, "DSC-U001", "SOME_KIND_NOBODY_IMPLEMENTED")
        self.assess(state)
        record = self.compliance(state, "CND-A", undeclared)
        self.assertEqual((NYE, PRE), (record["status"], record["evaluation_point"]))
        self.assertNotIn("evidence_owner", record)
        self.assertEqual(sel.INELIGIBLE, self.population(state)["CND-A"][0])

    def test_T19_the_external_check_reads_the_same_rule(self):
        source = _code(inspect.getsource(checks.commitment_validity))
        self.assertIn("compliance_blocks(", source)
        self.assertNotIn('"SATISFIED"', source)
        state, constraint = self.deferred_design()
        self.compare(state, self.P)
        out = self.decide(state, "CND-A", "a reason")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        decision = self.committed_decision(state)["entity_id"]
        snapshot = assurance.run_assurance(state)
        prop = "commitment_validity:%s" % decision
        self.assertEqual(model.ENGINEERING_ESTABLISHED, snapshot.establishment()[prop])
        passed = [f for f in snapshot.findings(model.PASS) if f.property_id == prop]
        self.assertTrue(passed)
        self.assertIn("deferred hard requirements: %s (owed by s05)" % constraint,
                      passed[0].detail)
        # A REQUIREMENT STATED AFTER THE COMMITMENT supersedes nothing, so the
        # decision stays STANDING - the shape only an external reader can see.
        # Deferred: still a pass, and the new debt is reported beside it.
        later = self.constraint(state, "DSC-LATER", blocks=True)
        self.hrc(state, "CND-A", later, NYE, DOWN, "s05")
        self.assertEqual(STANDING, self.validity(state, decision))
        again = assurance.run_assurance(state)
        self.assertEqual(model.ENGINEERING_ESTABLISHED, again.establishment()[prop])
        detail = [f for f in again.findings(model.PASS) if f.property_id == prop][0].detail
        self.assertIn("%s (owed by s05)" % later, detail)
        # Violated at a DOWNSTREAM point: the deferral hides nothing.
        self.invalidate(state, "HRC-CND-A-%s" % later, stage="feasibility", why="probe")
        self.assertEqual(STANDING, self.validity(state, decision),
                         "the probe record was a premise of the commitment")
        self.revise(state, Op("CREATE", "HardRequirementCompliance", "HRC-CND-A-LATER-V2",
                              {"candidate": "CND-A", "constraint": later, "status": VIO,
                               "why": "probe", "evaluation_point": DOWN,
                               "evidence_owner": "s05"}, "t",
                              premise_refs=["CND-A", later]), stage="feasibility")
        failed = assurance.run_assurance(state)
        failures = [f for f in failed.findings(model.FAIL) if f.property_id == prop]
        self.assertTrue(failures)
        self.assertEqual(model.FALSE_ACCEPTANCE, failures[0].code)
        self.assertIn("violated", failures[0].detail)
        # Unanswered at a PRE_SELECTION point: required evidence absent.
        self.invalidate(state, "HRC-CND-A-LATER-V2", stage="feasibility", why="probe")
        self.revise(state, Op("CREATE", "HardRequirementCompliance", "HRC-CND-A-LATER-V3",
                              {"candidate": "CND-A", "constraint": later, "status": NYE,
                               "why": "probe", "evaluation_point": PRE}, "t",
                              premise_refs=["CND-A", later]), stage="feasibility")
        absent = [f for f in assurance.run_assurance(state).findings(model.FAIL)
                  if f.property_id == prop]
        self.assertTrue(absent)
        self.assertIn("required before selection", absent[0].detail)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
