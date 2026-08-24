"""THE STATE CHANGE A DESIGN DEMANDS, AND WHETHER ANYTHING SUPPORTS IT.

`transition_reachability` replaced `mobility_disposition`. The domain it replaced
asked whether every cell of a six-DOF grid that some other fact implied had to
move was dispositioned free, and it derived those cells from three things the
representation does not say:

  from `Configuration.distinguishing_basis` - reading "these two states are not
  the same" as "one is reachable from the other";

  from `Joint.child_group` - reading which side of a relative relation is written
  second as a statement about which side travels in the world;

  and from a rule that the coordinate be free in BOTH endpoint configurations -
  which convicts every latch, every over-centre link and every detent, because
  being held in your stable states and released during the change between them is
  what those mechanisms ARE.

What is asked now is narrower and typed. A TransitionRequirement says which two
states, which joints have to move relative to each other, in which degree of
freedom, and which restraints the change defeats. Three things then have to hold:
the topology has to have the freedom, a realization has to exist and carry it
out, and the restraints active where the change begins have to be explicitly
released. Everything else is a question left open rather than an impossibility
claimed.

Nothing below is about a particular mechanism, and nothing reads a candidate
name.
"""
from __future__ import annotations

import copy
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, realization, topology)

DOMAIN = "transition_reachability"

#: Three bars in a row, the third of which no joint of the probe touches.
THREE_BOXES = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]),
               "BOD-G1A": ([1.5, 0, 0], [1, 1, 1]),
               "BOD-G2A": ([3.0, 0, 0], [1, 1, 1])}


def restraint(n=0, configurations=("CFG-C0A",), blocks=(("JNT-0A", "RZ"),),
              defeat="push", group="RGP-G1A", dofs=("RZ",)):
    """One ConstraintRelation, exactly as a producer would have stated it.

    `blocks` is what it says about relative joint motion and `None` is a relation
    that says nothing about it - a real and different answer from saying it
    restrains something else. `configurations` is where it holds, and `()` is a
    relation that holds nowhere rather than everywhere.
    """
    out = {"id": "CRL-%d A" % n, "retained_group": group,
           "blocked_dofs": list(dofs), "configurations": list(configurations),
           "driver": "LOAD", "blocked_direction": "+Z",
           "provider_reaction_site": "RSR-0001", "provider_site": "IFC-0A",
           "maintaining_interaction": "PHI-A"}
    out["id"] = "CRL-%dA" % n
    if blocks is not None:
        out["blocked_relative_motions"] = [{"joint": j, "dof": d} for j, d in blocks]
    if defeat:
        out["defeat_specification"] = defeat
    return out


def evidence(requires=(("JNT-0A", "RZ"),), releases=(), relations=(),
             frm="CFG-C0A", to="CFG-C1A", demand=True, **kw):
    """s03b: the demanded state change, and the restraints as stated."""
    r = realization("A", demand=None, **kw)
    r["constraint_relations"] = [copy.deepcopy(x) for x in relations]
    if demand:
        req = {"id": "TRQ-0A", "from_configuration": frm, "to_configuration": to,
               "required_relative_motions": [{"joint": j, "dof": d}
                                             for j, d in requires]}
        if releases:
            req["released_constraints"] = list(releases)
        r["transition_requirements"] = [req]
    return r


def realized(moving=("RGP-G1A",), coords=((0, 90),), joints=("JNT-0A",),
             changed=("JNT-0A",), configs=("CFG-C0A", "CFG-C1A"),
             realizes="TRQ-0A", transition=True):
    """s04b: where the joints are, what each state's coordinates are, and the path."""
    out = {
        "joint_placements": [{"joint": j, "origin": [0, 0, 0]} for j in joints],
        "state_coordinates": [
            {"configuration": c,
             "coordinates": {j: coords[k][i] for k, j in enumerate(joints)
                             if k < len(coords)}}
            for i, c in enumerate(configs)],
        "transitions": ([{"id": "TRN-A", "realizes_requirement": realizes,
                          "moving_groups": list(moving),
                          "changed_coordinates": list(changed)}]
                        if transition else []),
        "envelope_revisions": [], "notes": "",
    }
    return out


class _Reach(_Feas):
    """One branch through the real chain, then the real feasibility evaluator."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def probe(self, state=None, s03a=None, s03b=None, s04a=None, s04b=None,
              boxes=None):
        return self.hinge(
            state=state,
            s03a=s03a if s03a is not None else topology("A", 2, [(0, 1)]),
            s03b=s03b if s03b is not None else evidence(),
            s04a=s04a if s04a is not None else arrangement(
                boxes if boxes is not None else HINGE_BOXES, steps=["ASY-0A"]),
            s04b=s04b if s04b is not None else realized())

    def reach(self, state=None, **kw):
        return self.domain(self.assess(state if state is not None
                                       else self.probe(**kw), apply_patch=False),
                           DOMAIN)


# =====================================================================
# CASES 1-3, 14-16 - what a restraint at the source does to a demand
# =====================================================================
class TestSourceRestraints(_Reach):

    def test_CASE1_blocked_at_the_source_and_released_is_not_a_failure(self):
        """The whole point of the replacement. A restraint holds where the change
        begins, the demand names it as one the change defeats, and the relation
        says how it is defeated - which is a described mechanism, not a
        contradiction, and the domain this replaced called it INFEASIBLE."""
        v = self.reach(s03b=evidence(releases=["CRL-0A"], relations=[restraint()]))
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("EVERY_DEMANDED_CHANGE_REACHABLE", v.reason_codes)

    def test_CASE2_an_unreleased_explicit_blocker_is_the_contradiction(self):
        """The same restraint, not named as released. Two current typed facts
        that cannot both hold: the motion is demanded where it is refused."""
        v = self.reach(s03b=evidence(relations=[restraint()]))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("UNRELEASED_REQUIRED_MOTION", v.reason_codes)
        self.assertIn("CRL-0A", v.premises)

    def test_CASE3_a_release_with_no_defeat_evidence_is_a_question(self):
        """How the release is achieved has not been stated. That is a fact the
        evidence does not carry, and answering INFEASIBLE would claim the design
        has shown the motion cannot happen - which it has not."""
        v = self.reach(s03b=evidence(releases=["CRL-0A"],
                                     relations=[restraint(defeat=None)]))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("RELEASE_EVIDENCE_NOT_ESTABLISHED", v.reason_codes)
        self.assertNotIn("UNRELEASED_REQUIRED_MOTION", v.reason_codes)

    def test_CASE14_a_release_naming_no_relative_motion_is_a_question(self):
        """The relation has not said WHICH relative motion it removes, so why
        releasing it matters is not established. Not a failure: a relation that
        has said nothing has not said the motion is impossible."""
        v = self.reach(s03b=evidence(releases=["CRL-0A"],
                                     relations=[restraint(blocks=None)]))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED", v.reason_codes)

    def test_CASE14b_unless_a_second_explicit_blocker_proves_it(self):
        """An independent, source-active, explicitly matching, unreleased
        restraint. THAT is the fact that convicts, and it convicts on its own
        terms rather than because the other declaration was untidy."""
        v = self.reach(s03b=evidence(
            releases=["CRL-0A"],
            relations=[restraint(blocks=None), restraint(n=1)]))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("UNRELEASED_REQUIRED_MOTION", v.reason_codes)
        self.assertIn("CRL-1A", v.premises)

    def test_CASE15_a_release_of_an_unrelated_motion_is_a_question(self):
        """It says which motion it restrains and it is not the one demanded."""
        v = self.reach(s03b=evidence(
            releases=["CRL-0A"],
            relations=[restraint(blocks=[("JNT-0A", "TX")])]))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("RELEASE_RELATION_NOT_APPLICABLE", v.reason_codes)

    def test_CASE15b_unless_a_second_explicit_blocker_proves_it(self):
        v = self.reach(s03b=evidence(
            releases=["CRL-0A"],
            relations=[restraint(blocks=[("JNT-0A", "TX")]), restraint(n=1)]))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("UNRELEASED_REQUIRED_MOTION", v.reason_codes)

    def test_CASE16_a_relation_that_holds_nowhere_blocks_no_source(self):
        """An empty `configurations` is a statement that the restraint holds in
        no state. Reading it as "everywhere" would make every relation a blocker
        of every transition, which is the reading that produces a contradiction
        out of an omission."""
        v = self.reach(s03b=evidence(relations=[restraint(configurations=())]))
        self.assertEqual(s07.PASS, v.status, v.summary)

    def test_CASE5_the_destination_may_lock_again(self):
        """Blocked, released, moved, blocked again. The same restraint is active
        in both stable states and the change defeats it in between - a latch, and
        an ordinary mechanism. Requiring the demanded freedom to survive into the
        destination is the rule that convicted every one of them."""
        v = self.reach(s03b=evidence(
            releases=["CRL-0A"],
            relations=[restraint(configurations=("CFG-C0A", "CFG-C1A"))]))
        self.assertEqual(s07.PASS, v.status, v.summary)

    def test_CASE_a_restraint_read_only_through_blocked_dofs_blocks_nothing(self):
        """`blocked_dofs` is about a group's mobility and `blocked_relative_motions`
        is about a joint's relative motion. They are separate statements, and
        matching a group's blocked DOF against a joint it happens to touch is the
        inference the replaced domain made."""
        v = self.reach(s03b=evidence(relations=[restraint(blocks=None,
                                                          dofs=("RZ",))]))
        self.assertEqual(s07.PASS, v.status, v.summary)


# =====================================================================
# CASES 4, 6 - what the topology has to have, and what it does not say
# =====================================================================
class TestTopologicalCapability(_Reach):

    def test_CASE4_a_demanded_freedom_the_joint_does_not_have_fails(self):
        v = self.reach(s03b=evidence(requires=(("JNT-0A", "RY"),)))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("DOF_NOT_SUPPORTED", v.reason_codes)

    def test_CASE6_reversing_parent_and_child_changes_no_status(self):
        """A joint states a RELATIVE relation between two groups. Which of them
        is written as the parent is not a statement about which one travels, so
        both descriptions of one mechanism have to give one answer."""
        forward = topology("A", 2, [(0, 1)])
        reverse = copy.deepcopy(forward)
        j = reverse["joints"][0]
        j["parent_group"], j["child_group"] = j["child_group"], j["parent_group"]
        for moving in (_group(0, "A"), _group(1, "A")):
            a = self.reach(s03a=forward, s04b=realized(moving=(moving,)))
            b = self.reach(s03a=reverse, s04b=realized(moving=(moving,)))
            self.assertEqual((a.status, tuple(a.reason_codes)),
                             (b.status, tuple(b.reason_codes)), moving)
            self.assertEqual(s07.PASS, a.status, a.summary)


# =====================================================================
# CASES 7-13 - the realization, and what makes the question apply at all
# =====================================================================
class TestRealization(_Reach):

    def test_CASE7_declared_distinctness_alone_asks_nothing_here(self):
        """Two states declared to differ is verified by `required_configurations`
        and demands no motion. It was the replaced domain's main source of
        required cells and it is not a demand."""
        basis = {"CFG-C0A": [{"joint": "JNT-0A", "dof": "RZ",
                              "differs_from": ["CFG-C1A"]}]}
        state = self.probe(s03a=topology("A", 2, [(0, 1)], basis=basis),
                           s03b=evidence(demand=False),
                           s04b=realized(transition=False))
        out = self.assess(state, apply_patch=False)
        v = self.domain(out, DOMAIN)
        self.assertEqual(s07.NOT_APPLICABLE, v.status, v.summary)
        self.assertIn("NO_REQUIRED_MOTION", v.reason_codes)
        self.assertNotEqual(s07.INFEASIBLE, out.status)
        # And the difference is still checked, where it belongs.
        self.assertEqual(s07.PASS,
                         self.domain(out, "required_configurations").status)

    def test_CASE8_a_demand_nothing_realizes_is_not_established(self):
        v = self.reach(s04b=realized(transition=False))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("REQUIRED_TRANSITION_NOT_REALIZED", v.reason_codes)

    def test_CASE8b_a_demand_realized_twice_has_no_single_answer(self):
        """Two records claim one demand. Which of them answers it is not decided
        by the order the family comes back in, and the ambiguity is the finding -
        so the answer is a question left open, not a verdict read off whichever
        record happened to be first."""
        payload = realized()
        second = copy.deepcopy(payload["transitions"][0])
        second["id"] = "TRN-B"
        payload["transitions"].append(second)
        v = self.reach(s04b=payload)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("TRANSITION_REQUIREMENT_REALIZED_MULTIPLE_TIMES",
                      v.reason_codes)
        self.assertIn("TRN-A", v.premises)
        self.assertIn("TRN-B", v.premises)

    def test_CASE8c_and_the_ambiguity_never_becomes_a_contradiction(self):
        """The second claimant moves the demanded coordinate and the first does
        not. Merging both records' endpoint numbers into one map would check one
        record's declaration against the other's coordinates and report the
        demanded motion as positively unrealized - a FAIL manufactured out of the
        ambiguity rather than read from either record."""
        payload = realized(coords=((0, 90),))
        still = copy.deepcopy(payload["transitions"][0])
        still["id"] = "TRN-B"
        payload["transitions"].append(still)
        v = self.reach(s04b=payload)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertNotIn("REQUIRED_RELATIVE_MOTION_NOT_REALIZED", v.reason_codes)

    def test_CASE9_a_realization_between_the_wrong_states_fails(self):
        """The written record claims to answer this demand and connects a
        different pair. A positive mismatch between two current facts."""
        state = self.probe(
            s03a=topology("A", 2, [(0, 1)], configs=3),
            s04b=realized(coords=((0, 90, 180),),
                          configs=("CFG-C0A", "CFG-C1A", "CFG-C2A")))
        self.revise(state, Op("SUPERSEDE", "Transition", "TRN-A",
                              {"to_state": "STA-CFG-C2A"}, "t",
                              reason="the path was re-aimed"))
        v = self.reach(state=state)
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("ENDPOINT_MISMATCH", v.reason_codes)

    def test_CASE10_a_required_coordinate_that_does_not_change_fails(self):
        v = self.reach(s04b=realized(coords=((30, 30),)))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("REQUIRED_RELATIVE_MOTION_NOT_REALIZED", v.reason_codes)

    def test_CASE11_a_required_coordinate_that_is_missing_is_a_question(self):
        """Two joints, and the demand is about the one no state states a
        coordinate for. Nothing says the motion did not happen; nothing says it
        did."""
        v = self.reach(s03a=topology("A", 3, [(0, 1), (1, 2)]),
                       boxes=THREE_BOXES,
                       s03b=evidence(requires=(("JNT-1A", "RZ"),)))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("REQUIRED_COORDINATE_ABSENT", v.reason_codes)

    def test_CASE12_no_claim_about_what_moves_is_a_question(self):
        v = self.reach(s04b=realized(moving=()))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("MOVING_SIDE_ABSENT", v.reason_codes)

    def test_CASE13_a_claim_naming_only_unrelated_groups_fails(self):
        """It has said what moves and what it named is nothing the demanded joint
        connects. That is an answer, and it is the wrong one - different from
        having said nothing."""
        v = self.reach(s03a=topology("A", 3, [(0, 1), (1, 2)]),
                       boxes=THREE_BOXES,
                       s04b=realized(moving=(_group(2, "A"),)))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("MOVING_SIDE_UNRELATED", v.reason_codes)

    def test_CASE_a_demand_with_no_requirement_but_a_motion_obligation(self):
        """A typed effect obligation that cannot be discharged without movement,
        and nothing states which state change. NOT_APPLICABLE would let the
        candidate excuse itself by having authored nothing."""
        import json
        from .test_s7_feasibility import S02
        s02 = json.loads(json.dumps(S02))
        s02["physical_effect_obligations"][0]["effect"] = "TRANSMIT_MOTION"
        state = self.seed()
        self.candidates(state, payload=s02)
        r = evidence(demand=False)
        r["physical_interactions"][0]["effect"] = "TRANSMIT_MOTION"
        self.probe(state=state, s03b=r, s04b=realized(transition=False))
        v = self.reach(state=state)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("MOTION_DEMANDED_WITHOUT_TRANSITION_REQUIREMENT",
                      v.reason_codes)


# =====================================================================
# THE VOCABULARY ITSELF
# =====================================================================
class TestTheVocabulary(_Reach):

    def test_V1_there_are_still_exactly_nine_domains(self):
        """Replaced, not added beside. A tenth domain overlapping this one would
        let one fact be counted twice in the aggregate."""
        self.assertEqual(9, len(s07.DOMAINS))
        self.assertEqual(9, len(set(s07.DOMAINS)))
        self.assertEqual(sorted(s07.DOMAINS), sorted(s07.DOMAIN_EVALUATORS))

    def test_V2_the_replaced_domain_is_gone_from_active_semantics(self):
        """Neither in the vocabulary nor reachable through dispatch, and no dead
        evaluator left in the module for a reader to mistake for live logic."""
        self.assertNotIn("mobility_disposition", s07.DOMAINS)
        self.assertNotIn("mobility_disposition", s07.DOMAIN_EVALUATORS)
        for gone in ("_mobility_disposition", "_required_motion_cells",
                     "_disposition_support"):
            self.assertFalse(hasattr(s07, gone), gone)
        self.assertIn(DOMAIN, s07.DOMAINS)

    def test_V3_the_contract_declares_the_same_nine(self):
        """The evaluator's tuple and the two canonical enumerations are one
        vocabulary. A verdict whose domain the contract does not know is a
        record the write boundary refuses, so a drift here is a silent stage."""
        fam = self.c.families
        for name in ("FeasibilityDomainAssessment", "MechanicalFeasibilityAssessment"):
            declared = (fam[name].get("domain")
                        or fam[name].get("evaluated_domains"))
            self.assertEqual(list(s07.DOMAINS), list(declared), name)

    def test_V4_the_domain_is_written_and_reportable(self):
        """It reaches state as its own assessment, under its own id."""
        state = self.probe()
        out = self.assess(state)
        eid = next(o.entity_id for o in out.patch.operations
                   if o.entity_type == "FeasibilityDomainAssessment"
                   and o.fields.get("domain") == DOMAIN)
        self.assertEqual("FDA-CND-A-TRANSITION-REACHABILITY", eid)
        self.assertIn(DOMAIN, state.entities[
            "MFA-CND-A"]["evaluated_domains"])

    def test_V4b_every_finding_the_shared_rules_can_produce_has_a_cost(self):
        """`_REALIZATION_COST[code]` is a subscript, not a `.get` with a default:
        a code the table does not know raises rather than being silently treated
        as harmless. That only helps if the table is complete, so the two are
        compared - the codes the shared rules can produce, and the costs this
        domain assigns them."""
        import ast
        import inspect
        import ver3.assy_v3.stages.s04_envelope_and_motion as s04
        tree = ast.parse(inspect.getsource(s04.realization_findings).lstrip())
        produced = {node.args[0].elts[0].value
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and getattr(node.func, "attr", None) == "append"
                    and node.args and isinstance(node.args[0], ast.Tuple)
                    and isinstance(node.args[0].elts[0], ast.Constant)}
        self.assertTrue(produced, "the probe read no codes")
        self.assertEqual(produced, set(s07._REALIZATION_COST))

    def test_V4c_no_absence_is_ever_costed_as_a_contradiction(self):
        """The rule the whole domain turns on, asserted against the table that
        now carries it. A code naming something MISSING, ABSENT or NOT
        ESTABLISHED is a question the evidence leaves open; FAIL is the claim
        that the design has shown the change cannot happen, and an absence has
        shown nothing."""
        absence = ("ABSENT", "NOT_A_NUMBER", "NOT_DECLARED", "NOT_RESOLVABLE",
                   "NO_REALIZATION", "MORE_THAN_ONCE")
        for code, cost in sorted(s07._REALIZATION_COST.items()):
            if any(word in code for word in absence):
                self.assertEqual(s07.NOT_ESTABLISHED, cost, code)
        # And the contradictions really are positive statements: a number that
        # did not move, a topology that cannot, a record connecting the wrong
        # pair, a claim about what moves that names the wrong groups.
        self.assertEqual(
            {"DOF_NOT_SUPPORTED", "ENDPOINT_MISMATCH",
             "REQUIRED_MOTION_NOT_REALIZED", "MOVING_SIDE_UNRELATED",
             "DECLARED_CHANGE_NOT_REALIZED"},
            {c for c, v in s07._REALIZATION_COST.items() if v == s07.FAIL})

    def test_V4d_nothing_in_the_path_reads_a_retired_inference(self):
        """Structural, and against the CODE rather than the prose. Three fields
        made the replaced domain unsound, and each is named in a docstring here
        saying it is not consulted - which is exactly the shape a test that
        greps raw source mistakes for the rule being implemented. The
        docstrings and comments are blanked first, so what is searched is what
        runs."""
        import ast
        import inspect
        import textwrap
        import ver3.assy_v3.stages.s04_envelope_and_motion as s04

        def code_only(fn):
            src = textwrap.dedent(inspect.getsource(fn))
            lines = src.splitlines()
            for node in ast.walk(ast.parse(src)):
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
            return "\n".join(l for l in lines
                              if not l.strip().startswith("#"))

        for fn in (s07._transition_reachability, s07._release_findings,
                   s07._realizations_of, s07._relative_motions, s07._active_at,
                   s04.realization_findings):
            src = code_only(fn)
            self.assertTrue(src.strip(), fn.__name__)
            for retired in ("distinguishing_basis", "blocked_dofs",
                            "retained_group"):
                self.assertNotIn(retired, src, (fn.__name__, retired))
            # `child_group` may appear ONLY beside `parent_group`: a joint's two
            # incident groups, read as the pair they are.
            if "child_group" in src:
                self.assertIn("parent_group", src, fn.__name__)

    def test_V5_the_aggregate_rule_reads_classes_not_statuses(self):
        """UNIT A. OLD ASSUMPTION: any applicable FAIL was INFEASIBLE. NEW
        INVARIANT: an unreleased explicit blocker is s03b's restraint against
        s03b's demand - an owner revision that leaves MOTION_REALIZED
        unestablished - so the domain keeps its FAIL and the candidate is
        NOT_ESTABLISHED, never INFEASIBLE without an argument. A demand nothing
        moves is a required-minimum absence, NOT_ESTABLISHED as before; a clean
        realization is feasible as before."""
        fail = self.assess(self.probe(s03b=evidence(relations=[restraint()])),
                           apply_patch=False)
        self.assertEqual(s07.FAIL, self.domain(fail, DOMAIN).status)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, fail.status)
        self.assertNotEqual(s07.INFEASIBLE, fail.status)

        open_ = self.assess(self.probe(s04b=realized(moving=())),
                            apply_patch=False)
        self.assertEqual(s07.NOT_ESTABLISHED, self.domain(open_, DOMAIN).status)
        self.assertNotEqual(s07.INFEASIBLE, open_.status)
        self.assertEqual(s07.MFA_NOT_ESTABLISHED, open_.status)

        clean = self.assess(self.probe(), apply_patch=False)
        self.assertEqual(s07.PASS, self.domain(clean, DOMAIN).status,
                         self.domain(clean, DOMAIN).summary)
        self.assertEqual(s07.FEASIBLE, clean.status,
                         [(v.domain, v.status, v.reason_codes)
                          for v in clean.verdicts if v.status != s07.PASS])


if __name__ == "__main__":
    unittest.main()
