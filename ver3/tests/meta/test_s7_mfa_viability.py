"""UNIT A: A CURRENT REALIZATION FAILING IS NOT THE MECHANISM FAILING.

`MechanicalFeasibilityAssessment` is the ONE candidate-level pre-selection
answer, and its three values now mean three different things:

    INFEASIBLE              an architecture-level incompatibility, stated with a
                            structured physical argument and never without one
    NOT_ESTABLISHED         a fact of the declared pre-selection required
                            minimum is absent, ambiguous, or contradicted by a
                            realization its owner can still repair
    FEASIBLE_FOR_SELECTION  the minimum is shown and nothing established
                            contradicts the architecture - whatever else is
                            still owed, and what is owed is on the record

The detail is kept where it was: every `FeasibilityDomainAssessment` keeps its
own PASS / FAIL / NOT_ESTABLISHED / NOT_APPLICABLE, and every reason code it
carries is CLASSIFIED by the contract - repairable by s04, revisable by its
owner, owed downstream, unsupported by this pipeline, a required-minimum fact
the design lacks, or an incompatibility with an argument. The aggregate reads
the classes and never the statuses.

WHAT THESE TESTS ARE GUARDING

    Classification is TOTAL and comes from the contract. A code with no row
    is a finding the evaluator refuses to write an assessment over.

    The required minimum decides NOT_ESTABLISHED, and nothing else does.

    A repairable FAIL, an owner-revisable defect, a deferred obligation and an
    unsupported analysis each coexist with FEASIBLE_FOR_SELECTION, visibly.

    INFEASIBLE without a structured argument is impossible - in the aggregate,
    and at the write boundary for a hand that tries.

    Occupancy is accounted for per required (transition, moving group).

    Selection still reads one candidate-level answer and none of the detail;
    preference touches none of it; no benchmark is named anywhere.

Synthetic mechanisms throughout. No product noun, no benchmark id.
"""
from __future__ import annotations

import inspect
import re
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.state.design_state import ContractError, Contracts    # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from ver3.assy_v3.view import consumer_view_for                         # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, topology)
from .test_s7_transition_reachability import (                          # noqa: E402
    THREE_BOXES, evidence, realized)
from .test_s04_mating_geometry import _Mating, geometry                 # noqa: E402
from .test_s7_selection import HIGH, MINIMIZE, prefs                    # noqa: E402

#: Literals in the evaluator sources that are NOT reason codes: statuses,
#: vocabularies and operation names the same regex would otherwise collect.
NOT_A_CODE = {
    "PASS", "FAIL", "NOT_ESTABLISHED", "NOT_APPLICABLE", "FEASIBLE_FOR_SELECTION",
    "INFEASIBLE", "VALID", "CONTRADICTORY", "UNRESOLVED", "ESTABLISHED",
    "CONTRADICTED", "DEFERRED", "TOUCHES", "CLEAR", "UNDECLARED",
    "TRANSMIT_MOTION", "CONVERT_MOTION", "PERMIT_MOTION", "PREVENT_MOTION",
    "TRANSMIT_FORCE", "INTERFERENCE_FIT", "COMPLIANT_INTERACTION",
    "DEFORMATION_RESOLVED", "ELASTICITY", "KEEP_OUT", "ACCESS", "APERTURE",
    "EXTERNAL", "INTERNAL", "PROVISIONAL", "PRISMATIC", "FIXED", "ABSOLUTE",
    "ASSEMBLY_DEP_UNKNOWN", "ASSEMBLY_CYCLE", "ASSEMBLY_ORDER_CONTRADICTS_DEPENDENCY",
    "MODEL_LOCAL", "AXIS_STATED_TWICE",
    # the finding classes and argument keys, named in the module
    "REPAIRABLE_S04", "OWNER_REVISION", "DEFERRED_DOWNSTREAM", "UNSUPPORTED",
    "REQUIRED_MINIMUM_ABSENT", "ARGUMENT_KEYS", "OBLIGATION_CLASSES",
    "CURRENT_MULTIPLICITY", "INVOCATION_BRANCH", "VIEW_READY", "SUCCESS",
    "CREATE", "SUPERSEDE", "INVALIDATE", "EXTEND",
}
_LITERAL = re.compile(r'"([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)"')


def emitted_codes():
    """Every reason-code literal the nine domains and their shared rules can
    emit, read off the sources. The renamed reachability codes are emitted as
    their renamed form, and the constants the module names are included."""
    sources = [inspect.getsource(fn) for fn in s07.DOMAIN_EVALUATORS.values()]
    sources += [inspect.getsource(fn) for fn in (
        s07._classify_path, s07._release_findings, s07._extent_finding,
        s07._realizations_of, s04.mating_relation, s04.mating_fit,
        s04.insertion_fit, s04.approach_direction, s04.distinctness_findings,
        s04.realization_findings)]
    found = {m.group(1) for src in sources for m in _LITERAL.finditer(src)}
    found |= set(s07._REALIZATION_COST)
    found = {s07._REACHABILITY_CODE.get(c, c) for c in found}
    found |= {s07.MODEL_LOCAL_NEGATIVE, s07.MODEL_LOCAL_POSITIVE,
              s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION,
              s07.ARCHITECTURE_INCOMPATIBILITY}
    return {c for c in found if c not in NOT_A_CODE}


def chain_probe(test, moving=("RGP-G1A", "RGP-G2A")):
    """Three links in a serial chain, G0-[J0]-G1-[J1]-G2, both joints turning in
    one transition. G1 is carried by both - a composition this method cannot
    sweep - and G2 by J1 alone, which it can."""
    return test.hinge(
        s03a=topology("A", 3, [(0, 1), (1, 2)]),
        s03b=evidence(),
        s04a=arrangement(THREE_BOXES, steps=["ASY-0A"]),
        s04b=realized(moving=moving, coords=((0, 90), (0, 45)),
                      joints=("JNT-0A", "JNT-1A"), changed=("JNT-0A", "JNT-1A")))


class _Viability(_Feas):

    def mfa(self, state, candidate="CND-A"):
        found = [m for m in state.standing("MechanicalFeasibilityAssessment")
                 if m.get("candidate") == candidate]
        self.assertEqual(1, len(found), found)
        return found[0]

    def fda(self, state, domain, candidate="CND-A"):
        found = [d for d in state.standing("FeasibilityDomainAssessment")
                 if d.get("candidate") == candidate and d.get("domain") == domain]
        self.assertEqual(1, len(found), found)
        return found[0]

    def argument(self, **over):
        out = {"contradiction": "the demanded rotation is about an axis the "
                                "committed pair cannot turn about",
               "premises": ["JNT-0A", "TRQ-0A"],
               "architectural_commitments": ["CND-A"]}
        out.update(over)
        return out


# =====================================================================
# 1 - classification is total, and it is the contract's
# =====================================================================
class TestClassificationIsTotal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.table = s07.classification()
        cls.fams = Contracts().families

    def test_every_emitted_code_has_a_class(self):
        missing = sorted(emitted_codes() - set(self.table["codes"]))
        self.assertEqual([], missing, "codes the contract does not classify")

    def test_no_dead_row(self):
        dead = sorted(set(self.table["codes"]) - emitted_codes())
        self.assertEqual([], dead, "classified codes nothing emits")

    def test_every_row_is_well_formed(self):
        classes = set(self.table["classes"])
        minimum = set(self.table["minimum"])
        for code, spec in sorted(self.table["codes"].items()):
            with self.subTest(code=code):
                self.assertIn(spec["class"], classes)
                if spec["class"] in (s07.ESTABLISHED, s07.NOT_APPLICABLE):
                    self.assertNotIn("owner", spec)
                    self.assertNotIn("negates", spec)
                else:
                    self.assertTrue(spec.get("owner"), "no owner")
                if spec.get("negates"):
                    self.assertIn(spec["negates"], minimum)

    def test_every_minimum_fact_can_be_negated_and_nothing_else_negates(self):
        negated = {spec["negates"] for spec in self.table["codes"].values()
                   if spec.get("negates")}
        self.assertEqual(set(self.table["minimum"]), negated)
        for fact in self.table["minimum"].values():
            self.assertTrue(fact.get("what") and fact.get("inv_007"))

    def test_the_table_is_read_from_the_contract_and_kept_nowhere_else(self):
        source = inspect.getsource(s07)
        self.assertNotIn("finding_classification = {", source)
        self.assertIn('finding_classification', source)
        self.assertEqual(self.fams["FeasibilityDomainAssessment"]
                         ["finding_classification"], self.table["codes"])
        self.assertEqual(self.fams["MechanicalFeasibilityAssessment"]
                         ["pre_selection_required_minimum"], self.table["minimum"])

    def test_only_the_argument_class_may_be_infeasible(self):
        granting = [c for c, spec in self.table["codes"].items()
                    if spec["class"] == s07.ARCHITECTURE_INCOMPATIBILITY]
        self.assertEqual([s07.ARCHITECTURE_INCOMPATIBILITY], granting)

    def test_an_unclassified_code_is_refused_not_guessed(self):
        rows, problems = s07.classify(
            s07.Verdict("reach", s07.NOT_ESTABLISHED, ["A_CODE_NOBODY_DECLARED"]))
        self.assertEqual([], rows)
        self.assertTrue(problems and "no classification" in problems[0])
        agg = s07.aggregate([s07.Verdict("reach", s07.NOT_ESTABLISHED,
                                         ["A_CODE_NOBODY_DECLARED"])])
        self.assertIsNone(agg.status)
        self.assertTrue(agg.problems)

    def test_a_weakened_domain_that_explains_nothing_is_refused(self):
        rows, problems = s07.classify(
            s07.Verdict("reach", s07.NOT_ESTABLISHED, ["EVERY_ACTOR_REACHES_ITS_REGION"]))
        self.assertEqual([], rows)
        self.assertTrue(problems and "has not said why" in problems[0])


# =====================================================================
# 2 - the required minimum decides NOT_ESTABLISHED, and nothing else does
# =====================================================================
class TestRequiredMinimum(_Viability):

    def test_a_route_that_closes_nowhere_is_not_established(self):
        """OLD ASSUMPTION: any NOT_ESTABLISHED domain made the candidate
        NOT_ESTABLISHED. NEW INVARIANT: it does so because a declared
        required-minimum fact - a reaction route that closes - is absent, and
        the record says which fact."""
        state = self.hinge(s03b=realization("A", terminates=None))
        out = self.assess(state)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        mfa = self.mfa(state)
        self.assertEqual("NOT_ESTABLISHED", mfa["status"])
        facts = {r["negates"] for r in mfa["blocking_findings"]}
        self.assertEqual({"REACTION_ROUTE"}, facts)
        self.assertEqual({"LOAD_PATH_OPEN"}, {r["code"] for r in mfa["blocking_findings"]})
        self.assertEqual(s07.REQUIRED_MINIMUM_ABSENT, mfa["blocking_findings"][0]["class"])
        self.assertEqual("s03b", mfa["blocking_findings"][0]["owner"])

    def test_a_body_with_no_extent_is_not_established(self):
        state = self.hinge(s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1])},
                                            steps=["ASY-0A"]))
        out = self.assess(state)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        self.assertIn("ARRANGEMENT",
                      {r["negates"] for r in self.mfa(state)["blocking_findings"]})

    def test_a_repairable_contradiction_of_a_minimum_fact_is_not_established_not_infeasible(self):
        """OLD ASSUMPTION (B8): a positive gap on the load route was
        INFEASIBLE. NEW INVARIANT: the gap is s04a's placement, which s04a may
        revise without changing the principle - a repair that leaves the
        ARRANGEMENT fact unestablished. The domain keeps its FAIL."""
        state = self.hinge(
            s04a=arrangement({"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
                              "BOD-G1A": ([9, 0, 0], [1, 1, 1])},
                             steps=["ASY-0A"]))
        out = self.assess(state)
        self.assertEqual(s07.FAIL, self.domain(out, "load_reaction_closure").status)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        rows = self.mfa(state)["blocking_findings"]
        apart = [r for r in rows if r["code"] == "HOP_BODIES_APART"]
        self.assertTrue(apart)
        self.assertEqual(s07.REPAIRABLE_S04, apart[0]["class"])
        self.assertEqual("ARRANGEMENT", apart[0]["negates"])
        self.assertNotIn("physical_argument", self.mfa(state))

    def test_the_domain_status_is_never_read_for_the_aggregate(self):
        """Structural: the aggregate reads classes and negations, and no
        domain status appears in it."""
        source = inspect.getsource(s07.aggregate)
        for status in ("v.status", "FAIL in", "NOT_ESTABLISHED in"):
            self.assertNotIn(status, source)


# =====================================================================
# 3 - obligations coexist with FEASIBLE_FOR_SELECTION, visibly
# =====================================================================
class TestObligationsCoexistWithFeasible(_Viability):

    def test_a_repairable_domain_NE_leaves_the_candidate_feasible(self):
        """OLD ASSUMPTION (B32): a CLEARANCE pair whose boxes overlap made
        the candidate NOT_ESTABLISHED. NEW INVARIANT: the domain stays
        NOT_ESTABLISHED, the candidate is FEASIBLE_FOR_SELECTION, and the
        overlap is an open obligation s04a owns."""
        top = topology("A", 2, [(0, 1)])
        top["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        state = self.hinge(s03a=top)
        out = self.assess(state)
        v = self.domain(out, "gross_interference")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("CLEARANCE_PAIR_OVERLAPS", v.reason_codes)
        self.assertEqual(s07.FEASIBLE, out.status)
        mfa = self.mfa(state)
        self.assertEqual("FEASIBLE_FOR_SELECTION", mfa["status"])
        self.assertEqual([], mfa["blocking_findings"])
        rows = [r for r in mfa["open_obligations"] if r["code"] == "CLEARANCE_PAIR_OVERLAPS"]
        self.assertEqual([{"domain": "gross_interference", "code": "CLEARANCE_PAIR_OVERLAPS",
                           "class": s07.REPAIRABLE_S04, "owner": "s04a"}], rows)
        # and the domain record carries the same reading, minus the domain
        fda = self.fda(state, "gross_interference")
        self.assertEqual("NOT_ESTABLISHED", fda["status"], "the detail was not softened")
        self.assertIn({"code": "CLEARANCE_PAIR_OVERLAPS", "class": s07.REPAIRABLE_S04,
                       "owner": "s04a"}, fda["obligations"])


class TestARepairableFailCoexistsWithFeasible(_Mating):

    def test_a_relation_contradicted_by_its_own_representative_number(self):
        """A FAIL that is nobody's impossibility: an engagement of nothing is
        s04a's own number against its own relation, and s04a may state
        another. The domain keeps its FAIL; the candidate is feasible with the
        repair on the record."""
        state = self.pin(geometry(engagement_length=0))
        out = self.assess(state)
        v = self.domain(out, "gross_interference")
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("REQUIRED_ENGAGEMENT_NOT_REALIZED", v.reason_codes)
        self.assertEqual(s07.FEASIBLE, out.status,
                         [(w.domain, w.status, w.reason_codes) for w in out.verdicts])
        mfa = [m for m in state.standing("MechanicalFeasibilityAssessment")][0]
        self.assertIn({"domain": "gross_interference",
                       "code": "REQUIRED_ENGAGEMENT_NOT_REALIZED",
                       "class": s07.REPAIRABLE_S04, "owner": "s04a"},
                      mfa["open_obligations"])
        self.assertNotIn("physical_argument", mfa)

    def test_a_deferred_obligation_is_listed_as_owed_downstream(self):
        state = self.pin(geometry())
        out = self.assess(state)
        self.assertEqual(s07.FEASIBLE, out.status)
        mfa = [m for m in state.standing("MechanicalFeasibilityAssessment")][0]
        owed = {(r["class"], r["owner"]) for r in mfa["open_obligations"]
                if r["code"] == "SIZING_DEFERRED_TO_EMBODIMENT"}
        self.assertEqual({(s07.DEFERRED_DOWNSTREAM, "s05")}, owed)


# =====================================================================
# 4 / 7 - unsupported analysis, accounted for per moving group
# =====================================================================
class TestUnsupportedAnalysis(_Viability):

    def test_a_composite_motion_is_unsupported_and_the_candidate_is_feasible(self):
        state = chain_probe(self)
        out = self.assess(state)
        v = self.domain(out, "spatial_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn(s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION, v.reason_codes)
        self.assertEqual(s07.FEASIBLE, out.status,
                         [(w.domain, w.status, w.reason_codes) for w in out.verdicts])
        mfa = self.mfa(state)
        self.assertEqual([], mfa["blocking_findings"])
        self.assertIn({"domain": "spatial_realization",
                       "code": s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION,
                       "class": s07.UNSUPPORTED, "owner": "s04b"},
                      mfa["open_obligations"])

    def test_unsupported_alone_never_makes_a_candidate_not_established(self):
        """Every UNSUPPORTED code is non-negating by declaration."""
        for code, spec in s07.classification()["codes"].items():
            if spec["class"] == s07.UNSUPPORTED:
                self.assertNotIn("negates", spec, code)

    def test_occupancy_is_accounted_per_moving_group(self):
        """The other group of the same transition IS swept: one SweptVolume on
        the transition used to evidence every group it moves."""
        state = chain_probe(self)
        swept = {(v["transition"], v["rigid_group"])
                 for v in state.standing("SweptVolume")}
        self.assertIn(("TRN-A", "RGP-G2A"), swept, "the probe is not probing")
        self.assertNotIn(("TRN-A", "RGP-G1A"), swept)
        out = self.assess(state, apply_patch=False)
        v = self.domain(out, "spatial_realization")
        self.assertIn(s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION, v.reason_codes)
        self.assertIn("RGP-G1A", v.summary)
        self.assertNotIn("RGP-G2A", v.summary)
        # and the s04 diagnostic names the same group
        found = [p for p in s04.motion_evidence_check(state) if "MOTION_NOT_COMPUTED" in p]
        self.assertTrue(any("RGP-G1A" in p for p in found), found)
        self.assertFalse(any("RGP-G2A" in p for p in found), found)

    def test_a_withdrawn_sweep_is_not_computed_and_not_unsupported(self):
        """One carrying joint, the sweep withdrawn: the producer did not
        deliver a computation it can make. Repairable, and named so."""
        state = self.hinge()
        for v in state.standing("SweptVolume"):
            self.revise(state, Op("INVALIDATE", "SweptVolume", v["entity_id"], {},
                                  "t", reason="withdrawn by a probe"), stage="s04")
        out = self.assess(state)
        v = self.domain(out, "spatial_realization")
        self.assertIn("OCCUPANCY_NOT_COMPUTED", v.reason_codes)
        self.assertNotIn(s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION, v.reason_codes)
        self.assertEqual(s07.FEASIBLE, out.status)
        self.assertIn({"domain": "spatial_realization", "code": "OCCUPANCY_NOT_COMPUTED",
                       "class": s07.REPAIRABLE_S04, "owner": "s04b"},
                      self.mfa(state)["open_obligations"])


# =====================================================================
# 5 - INFEASIBLE needs an argument, in the aggregate and at the boundary
# =====================================================================
class TestInfeasibleNeedsAnArgument(_Viability):

    def test_the_code_without_an_argument_is_refused(self):
        agg = s07.aggregate([s07.Verdict("transition_reachability", s07.FAIL,
                                         [s07.ARCHITECTURE_INCOMPATIBILITY])])
        self.assertIsNone(agg.status)
        self.assertTrue(any("no physical argument" in p for p in agg.problems), agg.problems)

    def test_a_malformed_argument_is_refused(self):
        for bad in ({"contradiction": ""},
                    {"contradiction": "x", "premises": [], "architectural_commitments": ["CND-A"]},
                    {"contradiction": "x", "premises": ["JNT-0A"]}):
            agg = s07.aggregate([s07.Verdict("transition_reachability", s07.FAIL,
                                             [s07.ARCHITECTURE_INCOMPATIBILITY],
                                             arguments=[bad])])
            self.assertIsNone(agg.status, bad)

    def test_a_structured_argument_makes_it_infeasible_and_is_carried(self):
        verdict = s07.Verdict("transition_reachability", s07.FAIL,
                              [s07.ARCHITECTURE_INCOMPATIBILITY],
                              premises=["JNT-0A", "TRQ-0A"],
                              arguments=[self.argument()])
        agg = s07.aggregate([verdict])
        self.assertEqual(s07.INFEASIBLE, agg.status)
        self.assertEqual(self.argument()["contradiction"],
                         agg.physical_argument["contradiction"])
        self.assertEqual("transition_reachability", agg.physical_argument["domain"])

    def test_an_argument_with_no_incompatibility_stated_is_refused(self):
        agg = s07.aggregate([s07.Verdict("reach", s07.FAIL,
                                         ["REACH_CONCLUDED_UNREACHABLE"],
                                         arguments=[self.argument()])])
        self.assertIsNone(agg.status)

    def test_the_boundary_refuses_a_hand_written_infeasible_without_one(self):
        state = self.hinge()
        self.assess(state)
        with self.assertRaises(ContractError) as raised:
            self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                                  "MFA-CND-A", {"status": "INFEASIBLE"}, "t",
                                  reason="a hand says so"), stage="feasibility")
        self.assertIn("physical_argument", str(raised.exception))
        self.assertEqual("FEASIBLE_FOR_SELECTION", self.mfa(state)["status"])
        # and accepts one that states its argument
        self.revise(state, Op("SUPERSEDE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-A", {"status": "INFEASIBLE",
                                            "physical_argument": self.argument()},
                              "t", reason="a stated argument"), stage="feasibility")
        self.assertEqual("INFEASIBLE", self.mfa(state)["status"])

    def test_no_evaluator_can_state_one_yet(self):
        """Documented, not hidden: nothing the nine domains read can prove
        that a mechanism cannot satisfy a demand under ANY admissible
        realization of its commitments, so no evaluator emits the code. When
        one can, this test moves; until then INFEASIBLE is unreachable from
        evidence and reachable only from an argument."""
        for name, fn in s07.DOMAIN_EVALUATORS.items():
            self.assertNotIn("ARCHITECTURE_INCOMPATIBILITY", inspect.getsource(fn), name)
        for fn in (s04.realization_findings, s04.distinctness_findings,
                   s07._release_findings, s07._classify_path):
            self.assertNotIn("ARCHITECTURE_INCOMPATIBILITY", inspect.getsource(fn))
        self.assertEqual(
            s07.ARCHITECTURE_INCOMPATIBILITY,
            Contracts().families["MechanicalFeasibilityAssessment"]
            ["conditional_requirements"][0]["applies_when"]["equals"]
            .replace("INFEASIBLE", s07.ARCHITECTURE_INCOMPATIBILITY))

    def test_infeasible_by_exhaustion_does_not_exist(self):
        """No code path counts attempts, rounds or retries into the status."""
        source = inspect.getsource(s07)
        for word in ("attempts", "rounds", "exhaust", "retry"):
            self.assertNotIn(word, source.lower().replace("stage_attempt", ""),
                             word)


# =====================================================================
# 6 - a model-local negative is a repair signal, never a proof
# =====================================================================
class TestModelLocalNegatives(_Viability):

    def test_an_elimination_record_is_a_repair_obligation(self):
        """OLD ASSUMPTION (B13): an EliminationRecord made the candidate
        NOT_ESTABLISHED. NEW INVARIANT: it is s04a's opinion about an
        arrangement s04a may revise - a REPAIRABLE_S04 obligation on a
        FEASIBLE answer, and never an argument."""
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            eliminated=True))
        out = self.assess(state)
        v = self.domain(out, "spatial_realization")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn(s07.MODEL_LOCAL_NEGATIVE, v.reason_codes)
        self.assertEqual(s07.FEASIBLE, out.status)
        self.assertIn({"domain": "spatial_realization", "code": s07.MODEL_LOCAL_NEGATIVE,
                       "class": s07.REPAIRABLE_S04, "owner": "s04a"},
                      self.mfa(state)["open_obligations"])

    def test_a_negative_reach_conclusion_is_repairable_and_never_infeasible(self):
        """It negates the ACCESS fact of the minimum - the arrangement, as
        concluded, does not reach - so the candidate is NOT_ESTABLISHED; it is
        s04a's conclusion about s04a's arrangement, so it is a repair and not
        an argument."""
        from .test_s7_preselection_basis import reach_arrangement, with_region
        state = self.seed(must_reach=["the latch"])
        self.candidates(state)
        self.hinge(state=state, s03a=with_region(topology("A", 2, [(0, 1)])),
                   s04a=reach_arrangement(HINGE_BOXES, "FRG-A", "ACT-0001",
                                          reachable=False))
        out = self.assess(state)
        v = self.domain(out, "reach")
        self.assertEqual(s07.FAIL, v.status)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, out.status)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        rows = [r for r in self.mfa(state)["blocking_findings"]
                if r["code"] == "REACH_CONCLUDED_UNREACHABLE"]
        self.assertEqual([{"domain": "reach", "code": "REACH_CONCLUDED_UNREACHABLE",
                           "class": s07.REPAIRABLE_S04, "owner": "s04a",
                           "negates": "ACCESS"}], rows)
        self.assertNotIn("physical_argument", self.mfa(state))

    def test_neither_model_local_code_can_grant_the_argument_class(self):
        table = s07.classification()["codes"]
        for code in (s07.MODEL_LOCAL_NEGATIVE, "REACH_CONCLUDED_UNREACHABLE"):
            self.assertEqual(s07.REPAIRABLE_S04, table[code]["class"])


# =====================================================================
# 8 / 9 / 10 - the seam, preference, and generality
# =====================================================================
class TestSelectionSeamAndGenerality(_Viability):

    def population(self, state):
        view = consumer_view_for(sel.RESPONSIBILITY, state)
        payload = view.payload()
        admitted = sorted(e["entity_id"] for rows in payload.values() for e in rows
                          if isinstance(e, dict) and e.get("entity_id"))
        return sel.eligibility(sel._Evidence(
            payload, cv.branch_membership(state, self.c, admitted)))

    def test_selection_reads_one_candidate_level_answer_and_no_detail(self):
        import ver3.assy_v3.stages.selection_advisory as adv
        import ver3.assy_v3.stages.selection_decision as dec
        from ver3.assy_v3.lifecycle import s7_reconcile as lc
        for module in (sel, dec, adv, lc):
            source = inspect.getsource(module)
            for token in ("open_obligations", "blocking_findings", "finding_class",
                          "negates", "REPAIRABLE_S04", "classify(", "physical_argument",
                          "FeasibilityDomainAssessment", "reason_codes"):
                self.assertNotIn(token, source, "%s reads %r" % (module.__name__, token))
        source = inspect.getsource(sel.eligibility)
        self.assertIn('mfa.get("status")', source)

    def test_a_feasible_candidate_with_obligations_is_eligible(self):
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            eliminated=True))
        self.assess(state)
        self.assertTrue(self.mfa(state)["open_obligations"], "the probe is not probing")
        verdict, why, _used = self.population(state)["CND-A"]
        self.assertEqual(sel.ELIGIBLE, verdict, why)

    def test_a_not_established_candidate_is_still_ineligible(self):
        """Unit A does not weaken NOT_ESTABLISHED through selection."""
        state = self.hinge(s03b=realization("A", terminates=None))
        self.assess(state)
        verdict, why, _used = self.population(state)["CND-A"]
        self.assertEqual(sel.INELIGIBLE, verdict)
        self.assertIn("NOT_ESTABLISHED", why)

    def test_preference_changes_no_finding_class_or_answer(self):
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                            eliminated=True))
        before = self.assess(state)
        picture = (self.mfa(state), [self.fda(state, d) for d in s07.DOMAINS])
        out = sel.materialize_selection_profile(state, prefs(joint_count=(MINIMIZE, HIGH)))
        self.assertIsNotNone(out.patch, out.problems)
        state.apply(out.patch)
        again = s07.evaluate_candidate_feasibility(state, "CND-A")
        self.assertIsNone(again.patch, "a preference re-evaluated feasibility")
        self.assertEqual(before.status, again.status)
        self.assertEqual(picture, (self.mfa(state), [self.fda(state, d) for d in s07.DOMAINS]))
        self.assertEqual([(v.domain, v.status, v.reason_codes) for v in before.verdicts],
                         [(v.domain, v.status, v.reason_codes) for v in again.verdicts])

    def test_nothing_names_a_benchmark_or_a_candidate(self):
        import json
        source = inspect.getsource(s07)
        fams = Contracts().families
        table = json.dumps([fams["FeasibilityDomainAssessment"]["finding_classification"],
                            fams["FeasibilityDomainAssessment"]["finding_classes"],
                            fams["MechanicalFeasibilityAssessment"]
                            ["pre_selection_required_minimum"]])
        for text, where in ((source, "feasibility.py"), (table, "the classification")):
            self.assertIsNone(re.search(r"\bBM-\d|\bCND-\d", text), where)
        for word in ("hinge", "drawer", "four-bar", "latch"):
            self.assertNotIn(word, inspect.getsource(s07.aggregate).lower())
            self.assertNotIn(word, inspect.getsource(s07.classify).lower())

    def test_the_mfa_open_obligations_are_exactly_the_domains_non_negating_rows(self):
        state = chain_probe(self)
        self.assess(state)
        mfa = self.mfa(state)
        from_domains = []
        for domain in s07.DOMAINS:
            for row in self.fda(state, domain)["obligations"]:
                from_domains.append(dict(row, domain=domain))
        import json

        def canon(rows):
            return sorted(json.dumps(r, sort_keys=True) for r in rows)
        expected_open = [r for r in from_domains if not r.get("negates")]
        expected_block = [r for r in from_domains if r.get("negates")]
        self.assertEqual(canon(expected_open), canon(mfa["open_obligations"]))
        self.assertEqual(canon(expected_block), canon(mfa["blocking_findings"]))

    def test_the_contract_states_the_collapse_this_unit_removes(self):
        collapses = {c["id"]: c for c in _paths.contract("STATUS_SEMANTICS.yaml")
                     ["forbidden_collapses"]}
        self.assertIn("C-13", collapses)
        self.assertIn("unsupported analysis", collapses["C-13"]["collapse"])
        self.assertIn("FEASIBLE_FOR_SELECTION", collapses["C-13"]["correct"])
        rules = " ".join(Contracts().families["MechanicalFeasibilityAssessment"]["rules"])
        self.assertIn("MISSING EVIDENCE IS NOT FEASIBILITY", rules)
        self.assertIn("NOT INFEASIBILITY", rules)
        self.assertIn("A CURRENT REALIZATION FAILING IS NOT THE MECHANISM FAILING", rules)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
