"""S7-F: what stops being true when the design moves, and what must not.

Every probe runs the REAL chain - s01 through s04b, the real feasibility
responsibility, the real comparison, the real advisory pass, the real human
checkpoint - and then moves something underneath it. Nothing here hand-marks a
record stale: what is asserted is what the state engine and the deterministic
owners do on their own.

THE TWO MECHANISMS, AND WHY BOTH ARE NEEDED

    A NAMED PREMISE CHANGED. The premise graph is walked transitively, so an
    envelope moving reaches the feasibility verdict that read it, the assessment
    that aggregates the verdict, the comparison that rests on the population the
    assessment establishes, and the commitment made over that comparison - with
    nobody having had to copy the whole closure into every record.

    EVIDENCE APPEARED WHERE THERE WAS NONE. An answer that says NOT_ESTABLISHED
    because a load path does not exist cannot name the load path it is waiting
    for. No edge leads back to it, so the only honest way to notice is to ask the
    evaluator again - which is what reconciliation is, and why it uses the
    evaluator rather than a second set of rules about what probably matters.

AND THE THINGS THAT MUST NOT MOVE

    A preference is not evidence. Changing what somebody wants recomputes the
    comparison and reopens the choice, and it may not touch one feasibility
    verdict - the falsifier runs the whole lifecycle and asserts every assessment
    is untouched, entity for entity.

    An opinion is not a premise. Advisory wording forces a re-review before a
    person submits and disturbs nothing after they have committed.

    Reopening is not reselecting. A stale commitment goes back to a HUMAN: the
    old submission is never replayed, and the frontier, the recommendation and
    the sole eligible candidate are still not decisions.
"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import os
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.lifecycle.records as records                       # noqa: E402
import ver3.assy_v3.stages.feasibility as feas                         # noqa: E402
import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.selection_advisory as adv                   # noqa: E402
import ver3.assy_v3.stages.selection_decision as dec                   # noqa: E402
import ver3.assy_v3.state.design_state as ds                           # noqa: E402
from ver3.assy_v3.lifecycle import s7_reconcile as lc                  # noqa: E402
from ver3.assy_v3.state.patch import Op                                # noqa: E402
from ver3.tools import run_window2                                     # noqa: E402
from .test_s7_advisory import _Failing, concern, review                # noqa: E402
from .test_s7_human_decision import _Decision                          # noqa: E402
from .test_s7_selection import HIGH, MINIMIZE, MAXIMIZE, prefs         # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

STANDING, STALE, INVALIDATED = "STANDING", "STALE", "INVALIDATED"


def _source(*parts: str) -> str:
    with open(os.path.join(_REPO, *parts)) as fh:
        return fh.read()


def _code(source: str) -> str:
    """The source with docstrings blanked: WHAT ACTUALLY RUNS.

    These modules say the words "frontier", "provider" and "assurance" in order
    to state that none of them is reachable from here, and an audit that flagged
    the sentence saying so would be measuring the explanation.
    """
    lines = source.splitlines()
    blank = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and \
                isinstance(body[0].value, ast.Str):
            blank |= set(range(body[0].lineno - 1, body[0].value.end_lineno))
    kept = []
    for n, line in enumerate(lines):
        if n in blank:
            kept.append("")
            continue
        cut = line.find("#")
        kept.append(line[:cut] if cut >= 0 and line[:cut].count('"') % 2 == 0
                    and line[:cut].count("'") % 2 == 0 else line)
    return "\n".join(kept)


class _Lifecycle(_Decision):
    """A design that has been through all of S-7, and can be moved underneath."""

    ADVISORY = review(kind="PREFER_CANDIDATE", candidate="CND-A",
                      reasoning="A is simpler",
                      concerns=[concern("CND-B", "more joints to align")])

    # -- reading currentness -------------------------------------------
    def validity(self, state, eid: str) -> str:
        return state.entities[eid].get("_validity")

    def standing_ids(self, state, family: str):
        return sorted(e["entity_id"] for e in state.standing(family))

    def all_ids(self, state, family: str):
        return sorted(e["entity_id"] for e in state.family(family))

    def mfa(self, state, candidate="CND-A"):
        return records.current_assessment(state, candidate)

    def comparison(self, state):
        found = state.standing("CandidateComparison")
        return found[0] if len(found) == 1 else None

    # -- the whole chain, and one human commitment ----------------------
    def chain(self, advisory=None, candidates=("A", "B"), preferences=None):
        return self.reviewable(candidates=candidates, preferences=preferences,
                               advisory=advisory if advisory is not None
                               else self.ADVISORY)

    def committed(self, candidate="CND-A", **kw):
        state = self.chain(**kw)
        out = self.decide(state, candidate, "a recorded human reason")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        return state, self.committed_decision(state)["entity_id"]

    def reconcile(self, state, **kw):
        return lc.reconcile_s7(state, **kw)

    # -- moving the design ----------------------------------------------
    def withdraw(self, state, eid, stage="s04", why="withdrawn by a probe"):
        self.revise(state, Op("INVALIDATE", state.stored_family(eid), eid, {},
                              "t", reason=why), stage=stage)

    def supersede(self, state, eid, fields, stage="s04", why="revised by a probe"):
        self.revise(state, Op("SUPERSEDE", state.stored_family(eid), eid, fields,
                              "t", reason=why), stage=stage)

    def replace_envelope(self, state, body="BOD-G0A"):
        """Withdraw a body's envelope, then author a NEW one for the same body.

        The second half is the case no premise edge can carry: the answer that
        went NOT_ESTABLISHED depended on an ABSENCE, and the entity that ends the
        absence has an id nothing could have named in advance.
        """
        current = [e for e in state.standing("Envelope") if e.get("body") == body]
        self.assertEqual(1, len(current), current)
        fields = {k: v for k, v in current[0].items()
                  if not k.startswith("_") and k != "entity_id"}
        self.withdraw(state, current[0]["entity_id"], why="remeasured")
        return fields

    def author_envelope(self, state, fields, eid="ENV-REPLACEMENT"):
        self.revise(state, Op("CREATE", "Envelope", eid, fields, "t",
                              premise_refs=[fields["body"]]), stage="s04")
        return eid

    def add_candidate(self, state, suffix="C", embody=False):
        """A new alternative enters a design that already compared the others."""
        template = sorted(state.standing("Candidate"),
                          key=lambda c: c["entity_id"])[0]
        fields = {k: v for k, v in template.items()
                  if not k.startswith("_") and k != "entity_id"}
        eid = "CND-%s" % suffix
        self.revise(state, Op("CREATE", "Candidate", eid,
                              dict(fields, summary="alternative %s" % suffix),
                              "t",
                              premise_refs=list(template.get("addresses_obligations")
                                                or [])), stage="s02")
        if embody:
            self.hinge(state, sfx=suffix)
        return eid

    def interference(self, state):
        """Make two unconnected bodies of the four-bar occupy one place."""
        self.supersede(state, "ENV-G2B",
                       {"extent": {"centre": [1.5, 0, 0],
                                   "half_extent": [1.6, 0.3, 0.3]}},
                       why="placement corrected")

    def open_item(self, state, suffix="1"):
        """A recorded openness: in the review a reviewer would be shown, and in
        nothing the comparison rests on.

        The two views differ, which is the whole of F-I12: the advisory sees what
        the design has already recorded as open, and the deterministic comparison
        does not - so this moves one and not the other.
        """
        ambiguity = "AMB-OPEN%s" % suffix
        self.revise(state, Op("CREATE", "Ambiguity", ambiguity,
                              {"statement": "which fastening family",
                               "conflicting_clauses": [],
                               "resolvable_when": "the user says"}, "t"),
                    stage="s01")
        eid = "UNR-OPEN%s" % suffix
        self.revise(state, Op("CREATE", "UnresolvedDecision", eid,
                              {"decision": "which fastening family",
                               "why_open": "the source does not say",
                               "alternatives": ["one", "another"],
                               "alternatives_kind": "FREE_TEXT",
                               "blocks": [], "kept_open_by": [ambiguity]}, "t",
                              premise_refs=[ambiguity]), stage="s01")
        return eid

    def contradiction(self, state):
        """New evidence that positively contradicts a verdict: the reaction site
        the load routes to turns out to be inside the product, which is a FAIL
        rather than an absence."""
        self.supersede(state, "RSR-0001", {"boundary_side": "INTERNAL"},
                       stage="s02", why="the product boundary was corrected")

    def unrelated(self, state, eid="AMB-UNRELATED"):
        self.revise(state, Op("CREATE", "Ambiguity", eid,
                              {"statement": "an unrelated open question",
                               "conflicting_clauses": [],
                               "resolvable_when": "somebody says"}, "t"),
                    stage="s01")
        return eid


# =====================================================================
# F01-F07 - currentness is a property of the graph
# =====================================================================
class TestPropagation(_Lifecycle):

    def linked(self, state, n=4, family="Ambiguity"):
        """A chain of records, each naming the one before it as its premise."""
        made = []
        for i in range(n):
            eid = "AMB-CHAIN%d" % i
            self.revise(state, Op("CREATE", family, eid,
                                  {"statement": "link %d" % i,
                                   "conflicting_clauses": [],
                                   "resolvable_when": "the one before it"}, "t",
                                  premise_refs=made[-1:]), stage="s01")
            made.append(eid)
        return made

    def test_F01_a_revised_premise_stales_what_named_it(self):
        state = self.built()
        chain = self.linked(state, 2)
        self.withdraw(state, chain[0], stage="s01")
        self.assertEqual(STALE, self.validity(state, chain[1]))

    def test_F02_and_everything_that_rests_on_that(self):
        """A->B->C->D. The one-hop walk stopped at B and left C and D standing,
        which made correctness depend on every producer copying the whole
        closure into every record - and no producer can be relied on to remember
        that forever."""
        state = self.built()
        chain = self.linked(state, 4)
        self.withdraw(state, chain[0], stage="s01")
        for eid in chain[1:]:
            self.assertEqual(STALE, self.validity(state, eid), eid)
        for eid in chain[1:]:
            reasons = state.entities[eid]["_stale_because"]
            self.assertEqual(1, len(reasons), "logged more than once")
            self.assertEqual(chain[0], reasons[0]["root"])

    def test_F03_a_diamond_arrives_once(self):
        state = self.built()
        self.revise(state, Op("CREATE", "Ambiguity", "AMB-TOP",
                              {"statement": "the top", "conflicting_clauses": [],
                               "resolvable_when": "never"}, "t"), stage="s01")
        for side in ("L", "R"):
            self.revise(state, Op("CREATE", "Ambiguity", "AMB-%s" % side,
                                  {"statement": side, "conflicting_clauses": [],
                                   "resolvable_when": "never"}, "t",
                                  premise_refs=["AMB-TOP"]), stage="s01")
        self.revise(state, Op("CREATE", "Ambiguity", "AMB-BOTTOM",
                              {"statement": "both", "conflicting_clauses": [],
                               "resolvable_when": "never"}, "t",
                              premise_refs=["AMB-L", "AMB-R"]), stage="s01")
        self.withdraw(state, "AMB-TOP", stage="s01")
        for eid in ("AMB-L", "AMB-R", "AMB-BOTTOM"):
            self.assertEqual(STALE, self.validity(state, eid), eid)
        self.assertEqual(1, len(state.entities["AMB-BOTTOM"]["_stale_because"]),
                         "two paths made two transitions")

    def test_F04_a_cycle_terminates(self):
        """Asserted against the engine directly: a premise cycle cannot be built
        through the write boundary, because a record cannot name one that does
        not exist yet - and an algorithm that only terminates because its inputs
        happen to be acyclic is not cycle-safe."""
        entities = {
            "A": {"_validity": STANDING, "_premises": ["C"]},
            "B": {"_validity": STANDING, "_premises": ["A"]},
            "C": {"_validity": STANDING, "_premises": ["B"]},
            "OUT": {"_validity": STANDING, "_premises": []}}
        ds._propagate(entities, "A", "INVALIDATED", "a probe")
        self.assertEqual(STALE, entities["B"]["_validity"])
        self.assertEqual(STALE, entities["C"]["_validity"])
        self.assertEqual(STANDING, entities["OUT"]["_validity"])
        self.assertEqual(STANDING, entities["A"]["_validity"],
                         "the changed entity staled itself")

    def test_F05_an_unrelated_entity_is_untouched(self):
        state = self.built()
        chain = self.linked(state, 3)
        alone = self.unrelated(state)
        self.withdraw(state, chain[0], stage="s01")
        self.assertEqual(STANDING, self.validity(state, alone))
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual(STANDING, self.validity(state, "MFA-%s" % candidate))

    def test_F06_an_extension_reaches_a_conclusion_drawn_from_outside(self):
        """AN EXTENSION IS THE OWNER'S RECORD BEING COMPLETED, by exactly the
        stage the contract said would complete it - the write boundary allows
        nothing else, because changing an authored value is a SUPERSEDE. So the
        owner's own passes are not staled by it: s03b's DOF grid would be
        withdrawn the moment s04a placed the joint it was derived from, and no
        deterministic step could restore it.

        A conclusion drawn from OUTSIDE the owner is a different matter. It was
        decided over a record that has since gained authoritative content."""
        state = self.built()
        self.revise(state, Op("CREATE", "Joint", "JNT-PROBE",
                              {"joint_type": "REVOLUTE", "parent_group": "RGP-G0A",
                               "child_group": "RGP-G1A", "dof": "RZ",
                               # NAMES the frame the axis is expressed in; [] was a
                               # unit vector in no frame.
                               "axis_direction": "+Z",
                               "frame_ids": ["FRM-JNT-PROBE"]}, "t"),
                    stage="s03")
        self.revise(state, Op("CREATE", "FeasibilityDomainAssessment",
                              "FDA-OUTSIDE",
                              {"candidate": "CND-A", "domain": "a probe",
                               "status": "PASS", "reason_codes": []}, "t",
                              premise_refs=["JNT-PROBE"]), stage="feasibility")
        self.revise(state, Op("CREATE", "Body", "BOD-OWNER",
                              {"instance_identity": "link", "role": "STRUCTURE",
                               "created_by_stage": "s03"}, "t",
                              premise_refs=["JNT-PROBE"]), stage="s03")
        self.revise(state, Op("EXTEND", "Joint", "JNT-PROBE",
                              {"frame_origin": [0, 0, 0]}, "t"), stage="s04")
        self.assertEqual(STALE, self.validity(state, "FDA-OUTSIDE"))
        self.assertEqual(STANDING, self.validity(state, "BOD-OWNER"))
        self.assertEqual("EXTENDED",
                         state.entities["FDA-OUTSIDE"]["_stale_because"][0]
                         ["premise_change"])

    def test_F06b_an_extension_reaches_transitively_too(self):
        state = self.built()
        self.revise(state, Op("CREATE", "Joint", "JNT-PROBE2",
                              {"joint_type": "REVOLUTE", "parent_group": "RGP-G0A",
                               "child_group": "RGP-G1A", "dof": "RZ",
                               # NAMES the frame the axis is expressed in; [] was a
                               # unit vector in no frame.
                               "axis_direction": "+Z",
                               "frame_ids": ["FRM-JNT-PROBE"]}, "t"),
                    stage="s03")
        self.revise(state, Op("CREATE", "FeasibilityDomainAssessment", "FDA-FIRST",
                              {"candidate": "CND-A", "domain": "a probe",
                               "status": "PASS", "reason_codes": []}, "t",
                              premise_refs=["JNT-PROBE2"]), stage="feasibility")
        self.revise(state, Op("CREATE", "MechanicalFeasibilityAssessment",
                              "MFA-SECOND",
                              {"candidate": "CND-A", "status": "PASS",
                               "domain_assessments": ["FDA-FIRST"]}, "t",
                              premise_refs=["FDA-FIRST"]), stage="feasibility")
        self.revise(state, Op("EXTEND", "Joint", "JNT-PROBE2",
                              {"frame_origin": [0, 0, 0]}, "t"), stage="s04")
        self.assertEqual(STALE, self.validity(state, "MFA-SECOND"))

    def test_F07_a_considered_reference_is_not_a_premise(self):
        """The decision NAMES the advisory it considered and does not rest on
        it, so there is no edge for propagation to follow. Fixed where it
        belongs - in the premise set - and not by teaching the state engine
        about a family."""
        state, decision = self.committed()
        advisory = self.standing_ids(state, "SelectionAdvisory")[0]
        self.assertIn(advisory,
                      state.entities[decision]["considered_advisories"])
        self.assertNotIn(advisory, state.entities[decision]["_premises"])
        source = inspect.getsource(ds._propagate)
        for family in ("Advisory", "Selection", "Concern", "Human"):
            self.assertNotIn(family, source)


# =====================================================================
# F08-F18 - the deterministic answer is asked again, not guessed
# =====================================================================
class TestFeasibilityReconciliation(_Lifecycle):

    def test_F08_reconciling_an_unchanged_design_writes_nothing(self):
        state, _decision = self.committed()
        before = state.state_hash()
        out = self.reconcile(state)
        self.assertFalse(out.changed, out.as_dict())
        self.assertEqual([], out.written)
        self.assertEqual([], out.retired)
        self.assertEqual(before, state.state_hash())

    def test_F09_and_reconciling_twice_converges(self):
        state = self.chain()
        self.replace_envelope(state)
        first = self.reconcile(state)
        self.assertTrue(first.changed)
        settled = state.state_hash()
        second = self.reconcile(state)
        self.assertFalse(second.changed, second.as_dict())
        self.assertEqual(settled, state.state_hash())
        self.assertEqual(third_hash := state.state_hash(), settled)
        self.reconcile(state)
        self.assertEqual(third_hash, state.state_hash())

    def test_F10_evidence_that_appears_reopens_the_answer_that_lacked_it(self):
        """THE CASE NO PREMISE EDGE CAN CARRY. The verdict was NOT_ESTABLISHED
        because a body had no extent; the entity that ends that absence is a
        CREATE, and nothing could have named it in advance."""
        state = self.chain()
        fields = self.replace_envelope(state)
        self.reconcile(state)
        self.assertEqual("NOT_ESTABLISHED", self.mfa(state)["status"])
        self.author_envelope(state, fields)
        out = self.reconcile(state)
        self.assertEqual("FEASIBLE_FOR_SELECTION", out.feasibility["CND-A"])
        self.assertEqual("FEASIBLE_FOR_SELECTION", self.mfa(state)["status"])

    def test_F11_the_domain_that_was_waiting_is_the_one_that_moves(self):
        state = self.chain()
        fields = self.replace_envelope(state)
        self.reconcile(state)
        spatial = records.current_domain_assessment(state, "CND-A",
                                                    "spatial_realization")
        reachability = records.current_domain_assessment(
            state, "CND-A", "transition_reachability")
        self.assertEqual("NOT_ESTABLISHED", spatial["status"])
        self.assertEqual("PASS", reachability["status"])
        self.author_envelope(state, fields)
        self.reconcile(state)
        self.assertEqual("PASS", records.current_domain_assessment(
            state, "CND-A", "spatial_realization")["status"])

    def test_F12_new_contradicting_evidence_reopens_the_choice(self):
        """A POSITIVE CONTRADICTION, not an absence: the site the load routes to
        is inside the product, so the route closes in the wrong place. An
        overlap between unconnected boxes would not do - S7-B is deliberately
        conservative there, and lifecycle does not get to sharpen it.

        UNIT A. OLD ASSUMPTION: the contradiction made both candidates
        INFEASIBLE. NEW INVARIANT: each route is its owner's to re-author
        without changing the principle, so the REACTION_ROUTE fact is
        unestablished and both are NOT_ESTABLISHED - which is still
        INELIGIBLE, still no comparison, still a reopened commitment."""
        state, decision = self.committed()
        self.contradiction(state)
        out = self.reconcile(state)
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual("NOT_ESTABLISHED", out.feasibility[candidate])
            self.assertEqual("NOT_ESTABLISHED",
                             self.mfa(state, candidate)["status"])
            self.assertEqual("FAIL", records.current_domain_assessment(
                state, candidate, "load_reaction_closure")["status"])
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.comparison)
        self.assertIsNone(self.comparison(state))
        self.assertEqual(STALE, self.validity(state, decision))
        # and no preference rescues it
        again = self.reconcile(state, selection_preferences=prefs(
            rigid_body_count=(MAXIMIZE, HIGH)))
        self.assertEqual("NOT_ESTABLISHED", self.mfa(state, "CND-A")["status"])
        self.assertIsNone(self.comparison(state))
        self.assertEqual(lc.REVIEW_NOT_READY, again.human_state)

    def test_F13_the_same_verdict_over_revised_evidence_is_a_new_evaluation(self):
        """Two identical answers over two revisions of the evidence are two
        evaluations, and only one of them is about what the design currently
        says. "The answer did not change" is never on its own a reason to leave
        yesterday's evaluation standing - the compliance record below says
        NOT_YET_EVALUABLE both times, and the second one is an assessment of a
        requirement whose wording is not the wording the first one read."""
        state = self.chain()
        self.constraint(state, eid="DSC-SAME01", blocks=True)
        self.reconcile(state)
        before = records.current_compliance(state, "CND-A", "DSC-SAME01")
        self.supersede(state, "DSC-SAME01",
                       {"statement": "the same requirement, restated"},
                       stage="s01", why="the wording was corrected")
        self.reconcile(state)
        after = records.current_compliance(state, "CND-A", "DSC-SAME01")
        self.assertEqual(before["status"], after["status"])
        self.assertNotEqual(before["entity_id"], after["entity_id"])
        self.assertNotEqual(before["evaluation_basis"], after["evaluation_basis"])
        self.assertNotEqual(STANDING, self.validity(state, before["entity_id"]))
        self.assertEqual([], records.multiplicity(state, "CND-A"))

    def test_F14_the_old_evaluation_stays_readable(self):
        state = self.chain()
        before = self.mfa(state)["entity_id"]
        self.replace_envelope(state)
        self.reconcile(state)
        self.assertIn(before, self.all_ids(state,
                                           "MechanicalFeasibilityAssessment"))
        self.assertNotEqual(STANDING, self.validity(state, before))
        self.assertEqual("FEASIBLE_FOR_SELECTION",
                         state.entities[before]["status"],
                         "history was rewritten rather than kept")

    def test_F15_F16_F17_one_current_answer_at_every_address(self):
        state = self.chain()
        for n in range(2):
            fields = self.replace_envelope(state)
            self.reconcile(state)
            self.author_envelope(state, fields, "ENV-G0A-ROUND%d" % n)
            self.reconcile(state)
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual([], records.multiplicity(state, candidate))
            self.assertEqual(1, len([m for m in state.standing(
                "MechanicalFeasibilityAssessment")
                if m["candidate"] == candidate]))
            per_domain: dict = {}
            for row in state.standing("FeasibilityDomainAssessment"):
                if row["candidate"] == candidate:
                    per_domain[row["domain"]] = per_domain.get(row["domain"], 0) + 1
            self.assertEqual({1}, set(per_domain.values()) or {1})

    def test_F16b_a_second_current_answer_is_refused_rather_than_picked(self):
        """FOUND BY MUTATION. Every test above asserts that multiplicity does not
        ARISE; none asserted what the reader does if it ever did, so relaxing
        `len(found) == 1` to `found[0] if found else None` broke nothing. That is
        the whole defect class this layer exists to prevent: choosing the current
        answer by position rather than by currentness, which is right until the
        day two records are standing and then silently wrong."""
        state = self.chain()
        current = self.mfa(state)
        fields = {k: v for k, v in current.items()
                  if not k.startswith("_") and k != "entity_id"}
        self.revise(state, Op("CREATE", "MechanicalFeasibilityAssessment",
                              "MFA-CND-A-SECOND", fields, "t",
                              premise_refs=["CND-A"]), stage="feasibility")
        self.assertIsNone(records.current_assessment(state, "CND-A"),
                          "the reader picked one of two current answers")
        self.assertTrue(records.multiplicity(state, "CND-A"))
        out = feas.evaluate_candidate_feasibility(state, "CND-A")
        self.assertEqual(records.CURRENT_MULTIPLICITY, out.status)
        self.assertIsNone(out.patch)

        domain = records.current_domain_assessment(state, "CND-B",
                                                   "transition_reachability")
        fields = {k: v for k, v in domain.items()
                  if not k.startswith("_") and k != "entity_id"}
        self.revise(state, Op("CREATE", "FeasibilityDomainAssessment",
                              "FDA-CND-B-SECOND", fields, "t",
                              premise_refs=["CND-B"]), stage="feasibility")
        self.assertIsNone(records.current_domain_assessment(
            state, "CND-B", "transition_reachability"))
        self.assertTrue(records.multiplicity(state, "CND-B"))

    def test_F17b_one_current_compliance_record_per_requirement(self):
        state = self.chain()
        self.constraint(state, eid="DSC-ONCE01", blocks=True)
        self.reconcile(state)
        self.reconcile(state)
        for candidate in ("CND-A", "CND-B"):
            found = [h for h in state.standing("HardRequirementCompliance")
                     if h["candidate"] == candidate
                     and h["constraint"] == "DSC-ONCE01"]
            self.assertEqual(1, len(found), found)
            self.assertEqual([], records.multiplicity(state, candidate))

    def test_F18_one_candidates_change_does_not_re_evaluate_another(self):
        state = self.chain()
        untouched = {e["entity_id"]: json.dumps(e, sort_keys=True, default=str)
                     for e in state.family("FeasibilityDomainAssessment")
                     if e["candidate"] == "CND-B"}
        before = self.mfa(state, "CND-B")["entity_id"]
        self.replace_envelope(state)
        self.reconcile(state)
        self.assertEqual(before, self.mfa(state, "CND-B")["entity_id"])
        self.assertEqual(untouched,
                         {e["entity_id"]: json.dumps(e, sort_keys=True, default=str)
                          for e in state.family("FeasibilityDomainAssessment")
                          if e["candidate"] == "CND-B"})


# =====================================================================
# F19-F25 - what appears, and what a comparison may claim
# =====================================================================
class TestPopulation(_Lifecycle):

    def test_F19_F20_a_new_candidate_ends_the_old_comparison(self):
        """The old comparison cannot stay current merely because the new
        alternative had no id when it was made. Its population is not the
        design's population any more, and a subset is not an answer."""
        state = self.chain()
        old = self.comparison(state)["entity_id"]
        self.add_candidate(state)
        out = self.reconcile(state)
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.comparison)
        self.assertIsNone(self.comparison(state))
        self.assertNotEqual(STANDING, self.validity(state, old))
        self.assertEqual(lc.REVIEW_NOT_READY, out.human_state)

    def test_F21_and_a_new_comparison_appears_once_it_is_established(self):
        state = self.chain()
        self.add_candidate(state, embody=True)
        out = self.reconcile(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(["CND-A", "CND-B", "CND-C"],
                         sorted(self.comparison(state)["candidates"]))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state)

    def test_F22_a_withdrawn_candidate_leaves_the_population(self):
        state = self.chain()
        self.withdraw(state, "CND-B", stage="s02", why="the alternative was dropped")
        out = self.reconcile(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(["CND-A"], self.comparison(state)["candidates"])

    def test_F23_a_new_blocking_requirement_reopens_eligibility(self):
        """No old compliance record could have named it, and no default answers
        it: a requirement nobody has evaluated is NOT_YET_EVALUABLE, which is a
        different fact from satisfied and from violated.

        WHAT THAT DOES TO THE POPULATION is the requirement's declared
        evaluation point (Unit D). The fixture's kind is owed to a later stage,
        so the candidates stay eligible - carrying the debt - and the comparison
        is remade with it on the record; the person decided without seeing it,
        so the commitment reopens. A kind owed before selection empties the
        population instead, and no comparison may stand."""
        state, decision = self.committed()
        self.constraint(state, eid="DSC-NEW01", blocks=True)
        out = self.reconcile(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(["DSC-NEW01"],
                         [r["constraint"] for r in
                          self.comparison(state)["deferred_hard_requirements"]["CND-A"]])
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state)

        state, decision = self.committed()
        self.constraint(state, eid="DSC-NEW02", blocks=True,
                        kind="PROHIBITED_ENERGY_SOURCE")
        out = self.reconcile(state)
        self.assertEqual(sel.NO_ELIGIBLE_CANDIDATES, out.comparison)
        self.assertIsNone(self.comparison(state))
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertEqual(lc.REVIEW_NOT_READY, out.human_state)

    def test_F24_F25_a_new_requirement_defaults_to_nothing(self):
        state = self.chain()
        self.constraint(state, eid="DSC-NEW02", blocks=True)
        self.reconcile(state)
        for candidate in ("CND-A", "CND-B"):
            record = records.current_compliance(state, candidate, "DSC-NEW02")
            self.assertIsNotNone(record)
            self.assertNotIn(record["status"], (sel.SATISFIED, sel.VIOLATED))
            self.assertEqual(sel.NOT_YET_EVALUABLE, record["status"])

    def test_F25b_a_withdrawn_requirement_stops_governing(self):
        state = self.chain()
        self.constraint(state, eid="DSC-GONE01", blocks=True)
        self.reconcile(state)
        # the fixture's kind is deferred (Unit D): the comparison stands, with
        # the debt on it
        self.assertEqual(["DSC-GONE01"],
                         [r["constraint"] for r in
                          self.comparison(state)["deferred_hard_requirements"]["CND-A"]])
        self.withdraw(state, "DSC-GONE01", stage="s01",
                      why="the requirement was withdrawn")
        out = self.reconcile(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(["CND-A", "CND-B"],
                         sorted(self.comparison(state)["candidates"]))
        self.assertEqual({"CND-A": [], "CND-B": []},
                         self.comparison(state)["deferred_hard_requirements"])
        self.assertEqual(STALE, self.validity(
            state, [h["entity_id"] for h in state.family(
                "HardRequirementCompliance")
                if h["constraint"] == "DSC-GONE01"][0]))


# =====================================================================
# F26-F32 - a preference is not evidence
# =====================================================================
class TestPreferenceLifecycle(_Lifecycle):

    OTHER = prefs(rigid_body_count=(MAXIMIZE, HIGH))

    def feasibility_record(self, state):
        return {e["entity_id"]: (json.dumps(e, sort_keys=True, default=str),
                                 e.get("_validity"))
                for e in (state.family("MechanicalFeasibilityAssessment")
                          + state.family("FeasibilityDomainAssessment")
                          + state.family("HardRequirementCompliance"))}

    def test_F26_a_preference_change_touches_no_feasibility_record(self):
        """THE CENTRAL S-7 SEPARATION, asserted across the lifecycle rather than
        at one invocation: every assessment, every domain verdict and every
        compliance record is byte-for-byte what it was, including its validity."""
        state, decision = self.committed()
        before = self.feasibility_record(state)
        out = self.reconcile(state, selection_preferences=self.OTHER)
        self.assertEqual(before, self.feasibility_record(state))
        self.assertEqual({"CND-A": "FEASIBLE_FOR_SELECTION",
                          "CND-B": "FEASIBLE_FOR_SELECTION"}, out.feasibility)

    def test_F27_F28_the_comparison_is_remade_under_the_new_profile(self):
        state, decision = self.committed()
        old = self.comparison(state)["entity_id"]
        out = self.reconcile(state, selection_preferences=self.OTHER)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertNotEqual(STANDING, self.validity(state, old))
        current = self.comparison(state)
        profile = state.standing("SelectionProfile")[0]
        self.assertEqual(profile["entity_id"], current["profile"])
        self.assertEqual(self.OTHER, profile["criteria"])
        self.assertEqual(["CND-B"], current["frontier"])

    def test_F29_an_explicitly_empty_profile_is_a_profile(self):
        state = self.chain()
        out = self.reconcile(state, selection_preferences={})
        self.assertEqual(sel.PROFILE_WRITTEN, out.profile)
        profile = state.standing("SelectionProfile")[0]
        self.assertEqual({}, profile["criteria"])
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(sel.TRADEOFF_UNRESOLVED, self.comparison(state)["outcome"])

    def test_F30_F31_a_withdrawn_source_leaves_no_current_profile(self):
        """Absent is not `{}`. One says the user stopped stating preferences and
        the other says they state that nothing is ranked, and a snapshot left
        standing after the first would have the design keep asserting a
        preference nobody holds."""
        state = self.chain()
        out = self.reconcile(state, selection_preferences=lc.ABSENT)
        self.assertEqual(sel.PROFILE_RETIRED, out.profile)
        self.assertEqual([], state.standing("SelectionProfile"))
        self.assertEqual(1, len(state.family("SelectionProfile")))
        self.assertIsNone(self.comparison(state))
        self.assertEqual(lc.REVIEW_NOT_READY, out.human_state)

    def test_F32_and_the_commitment_made_under_it_reopens(self):
        state, decision = self.committed()
        self.reconcile(state, selection_preferences=lc.ABSENT)
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertIsNone(lc.current_commitment(state))

    def test_F32b_an_unspecified_source_touches_no_profile(self):
        state = self.chain()
        before = self.standing_ids(state, "SelectionProfile")
        out = self.reconcile(state)
        self.assertIsNone(out.profile)
        self.assertEqual(before, self.standing_ids(state, "SelectionProfile"))


# =====================================================================
# F33-F39 - a review is of a design, and the design moved
# =====================================================================
class TestAdvisoryLifecycle(_Lifecycle):

    def test_F33_a_revised_exposed_premise_stales_the_review(self):
        state = self.chain()
        advisory = self.standing_ids(state, "SelectionAdvisory")[0]
        self.replace_envelope(state)
        self.assertEqual(STALE, self.validity(state, advisory))

    def test_F34_F35_a_new_fact_in_the_review_context_retires_it(self):
        """`premise_refs` records what the reviewer was SHOWN, and propagation
        withdraws the review when one of those is revised. It cannot see the
        other half: an entity that did not exist then and would be in the payload
        now. The reviewer never saw it, and a review presented as current would
        claim to have considered something it could not have."""
        state = self.chain()
        advisory = self.standing_ids(state, "SelectionAdvisory")[0]
        digest = state.entities[advisory]["review_context_digest"]
        self.open_item(state, "34")
        status, current = adv.current_review_context(state)
        self.assertEqual("REVIEW_CONTEXT_CURRENT", status)
        self.assertNotEqual(digest, current)
        out = self.reconcile(state)
        self.assertEqual(adv.ADVISORY_RETIRED, out.advisory)
        self.assertEqual([], state.standing("SelectionAdvisory"))
        self.assertIn(advisory, self.all_ids(state, "SelectionAdvisory"))

    def test_F36_the_concerns_go_with_it(self):
        state = self.chain()
        concerns = self.standing_ids(state, "SelectionConcern")
        self.assertTrue(concerns)
        self.open_item(state, "36")
        self.reconcile(state)
        self.assertEqual([], state.standing("SelectionConcern"))
        for eid in concerns:
            self.assertEqual(STALE, self.validity(state, eid))

    def test_F37_nothing_is_asked_of_a_model_by_a_change(self):
        state = self.chain()
        self.open_item(state, "37")
        provider = _Failing()
        out = self.reconcile(state)
        self.assertEqual(0, provider.calls)
        self.assertEqual([], state.standing("SelectionAdvisory"))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state,
                         "a design with no current review became undecidable")
        source = inspect.getsource(lc.reconcile_s7)
        self.assertIn("advisory_provider is not None", source)

    def test_F38_an_explicit_refresh_goes_through_the_ordinary_boundary(self):
        from .test_s02_s03b_integration import _Canned

        state = self.chain()
        self.open_item(state, "38")
        self.reconcile(state)
        self.assertEqual([], state.standing("SelectionAdvisory"))
        refreshed = self.reconcile(state, advisory_provider=_Canned(review(
            kind="NO_CLEAR_PREFERENCE", reasoning="a second opinion")))
        self.assertEqual("SUCCESS", refreshed.advisory)
        current = state.standing("SelectionAdvisory")
        self.assertEqual(1, len(current))
        self.assertEqual("a second opinion", current[0]["reasoning"])
        status, digest = adv.current_review_context(state)
        self.assertEqual(digest, current[0]["review_context_digest"])

    def test_F39_an_advisory_revision_after_a_commitment_changes_nothing(self):
        state, decision = self.committed()
        advisory = self.standing_ids(state, "SelectionAdvisory")[0]
        self.withdraw(state, advisory, stage="selection", why="reworded")
        self.assertEqual(STANDING, self.validity(state, decision))
        out = self.reconcile(state)
        self.assertEqual(STANDING, self.validity(state, decision))
        self.assertEqual(lc.CURRENT_COMMITMENT, out.human_state)
        for candidate in ("CND-A", "CND-B"):
            self.assertEqual(STANDING, self.validity(state, "MFA-%s" % candidate))


# =====================================================================
# F40-F49 - a stale commitment reopens to a person
# =====================================================================
class TestReopening(_Lifecycle):

    def test_F40_an_engineering_revision_stales_the_commitment(self):
        state, decision = self.committed()
        self.replace_envelope(state)
        self.assertEqual(STALE, self.validity(state, decision))

    def test_F41_a_hard_requirement_revision_stales_it(self):
        """The compliance records here are written by hand, exactly as
        feasibility would write them if the design had a material authority to
        evaluate against - and deliberately WITHOUT a reconcile, because the
        real evaluators answer NOT_YET_EVALUABLE for every requirement this
        fixture can state, and that is S7-B's answer to give rather than this
        test's to arrange around."""
        state = self.chain()
        constraint = self.blocking(state, {"CND-A": sel.SATISFIED,
                                           "CND-B": sel.SATISFIED})
        out = self.compare(state, self.PREFS)
        self.assertEqual(sel.COMPARISON_WRITTEN, out.status, out.problems)
        decided = self.decide(state, "CND-A", "a reason")
        self.assertEqual(dec.SELECTION_COMMITTED, decided.status, decided.problems)
        decision = self.committed_decision(state)["entity_id"]
        self.withdraw(state, "HRC-CND-A-%s" % constraint, stage="feasibility",
                      why="re-evaluated on new evidence")
        self.assertEqual(STALE, self.validity(state, decision))

    def test_F42_a_preference_revision_stales_it(self):
        state, decision = self.committed()
        self.reconcile(state, selection_preferences=prefs(
            rigid_body_count=(MAXIMIZE, HIGH)))
        self.assertEqual(STALE, self.validity(state, decision))

    def test_F43_a_stale_commitment_is_not_the_current_one(self):
        state, decision = self.committed()
        self.replace_envelope(state)
        out = self.reconcile(state)
        self.assertIsNone(lc.current_commitment(state))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state)
        self.assertIn(decision, self.all_ids(state, "SelectionDecision"))

    def test_F44_F47_a_new_decision_needs_a_new_review(self):
        state, first = self.committed()
        self.replace_envelope(state)
        self.reconcile(state)
        snapshot = self.review_of(state)
        self.assertNotEqual(
            state.entities[state.standing("HumanDecisionInput")[0]
                           ["entity_id"]]["premise_digest"], snapshot.digest)
        out = self.decide(state, "CND-B", "the geometry moved, so B it is",
                          snapshot=snapshot)
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        second = self.committed_decision(state)
        self.assertEqual("CND-B", second["selected_candidate"])
        self.assertNotEqual(first, second["entity_id"])
        self.assertEqual(STALE, self.validity(state, first))

    def test_F45_F46_the_old_submission_is_history_and_is_never_replayed(self):
        state, decision = self.committed()
        submitted = state.standing("HumanDecisionInput")[0]
        self.replace_envelope(state)
        out = self.reconcile(state)
        self.assertEqual(STANDING, self.validity(state, submitted["entity_id"]),
                         "a human's submission went stale with the design")
        self.assertIsNone(lc.current_commitment(state))
        source = inspect.getsource(lc)
        self.assertNotIn("commit_human_selection", source)
        self.assertNotIn("materialize_human_decision_input", source)
        # and replaying it by hand is refused, because the screen has moved
        replay = dec.commit_human_selection(state, submitted["entity_id"])
        self.assertEqual(dec.STALE_SUBMISSION, replay.status)

    def test_F48_a_screen_from_before_the_change_cannot_commit(self):
        state = self.chain()
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.SELECT, "CND-A")
        self.replace_envelope(state)
        self.reconcile(state)
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.STALE_SUBMISSION, out.status)
        self.assertEqual([], state.family("SelectionDecision"))

    def test_F49_nothing_selects_during_a_reopen(self):
        state, decision = self.committed()
        self.replace_envelope(state)
        out = self.reconcile(state)
        self.assertEqual(1, len(state.family("SelectionDecision")))
        self.assertEqual(1, len(state.family("HumanDecisionInput")))
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state)
        source = _code(_source("assy_v3", "lifecycle", "s7_reconcile.py"))
        for auto in ("frontier", "recommended_candidate", "SOLE_ELIGIBLE",
                     "DOMINANT_UNDER_PROFILE", "selected_candidate"):
            self.assertNotIn(auto, source)


# =====================================================================
# F50-F54 - precision
# =====================================================================
class TestPrecision(_Lifecycle):

    def test_F50_an_invisible_fact_changes_nothing(self):
        state, decision = self.committed()
        before = state.state_hash()
        self.unrelated(state)
        out = self.reconcile(state)
        self.assertFalse(out.changed, out.as_dict())
        self.assertEqual(lc.CURRENT_COMMITMENT, out.human_state)
        self.assertEqual(STANDING, self.validity(state, decision))
        self.assertEqual(STANDING, self.validity(
            state, self.standing_ids(state, "SelectionAdvisory")[0]))

    def test_F51_branch_local_geometry_stays_branch_local(self):
        state = self.chain()
        before = {e["entity_id"]: e.get("_validity")
                  for e in state.family("FeasibilityDomainAssessment")
                  if e["candidate"] == "CND-B"}
        self.replace_envelope(state)
        after = {e["entity_id"]: e.get("_validity")
                 for e in state.family("FeasibilityDomainAssessment")
                 if e["candidate"] == "CND-B"}
        self.assertEqual(before, after)
        self.assertEqual(STANDING, self.validity(state, "MFA-CND-B"))
        stale = [e["entity_id"] for e in state.family("FeasibilityDomainAssessment")
                 if e["candidate"] == "CND-A" and e.get("_validity") == STALE]
        self.assertTrue(stale, "the change reached no verdict at all")
        self.assertEqual(STANDING, self.validity(
            state, records.current_domain_assessment(
                state, "CND-A", "transition_reachability")["entity_id"]))

    def test_F52_a_design_wide_answer_does_move(self):
        state = self.chain()
        comparison = self.comparison(state)["entity_id"]
        self.replace_envelope(state)
        self.assertEqual(STALE, self.validity(state, comparison))

    def test_F53_a_review_may_be_overtaken_while_the_comparison_stands(self):
        state = self.chain()
        comparison = self.comparison(state)["entity_id"]
        self.open_item(state, "53")
        out = self.reconcile(state)
        self.assertEqual(STANDING, self.validity(state, comparison))
        self.assertEqual(sel.COMPARISON_UNCHANGED, out.comparison)
        self.assertEqual([], state.standing("SelectionAdvisory"))

    def test_F54_considered_material_never_stales_a_commitment(self):
        state, decision = self.committed()
        for eid in (self.standing_ids(state, "SelectionConcern")
                    + self.standing_ids(state, "SelectionAdvisory")):
            self.withdraw(state, eid, stage="selection", why="reworded")
            self.assertEqual(STANDING, self.validity(state, decision), eid)


# =====================================================================
# F55-F61 - who is allowed to write what
# =====================================================================
class TestAuthority(_Lifecycle):

    def test_F55_the_coordinator_owns_nothing(self):
        source = _source("assy_v3", "lifecycle", "s7_reconcile.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in (
                    "Op", "StagePatch"):
                self.fail("the coordinator constructed an operation itself")
        self.assertNotIn("Op(", source)
        self.assertNotIn("StagePatch(", source)

    def test_F56_F57_every_write_is_the_owner_s(self):
        state = self.chain()
        self.replace_envelope(state)
        self.reconcile(state, selection_preferences=prefs(
            joint_count=(MINIMIZE, HIGH), rigid_body_count=(MAXIMIZE, HIGH)))
        by_family = {}
        for eid in state.entities:
            rec = state.entities[eid]
            by_family.setdefault(rec["_family"], set()).add(rec["_created_by"])
        self.assertEqual({"feasibility"},
                         by_family["MechanicalFeasibilityAssessment"])
        self.assertEqual({"feasibility"},
                         by_family["FeasibilityDomainAssessment"])
        self.assertEqual({"selection"}, by_family["SelectionProfile"])
        self.assertEqual({"selection"}, by_family["CandidateComparison"])
        self.assertNotIn("lifecycle", set().union(*by_family.values()))

    def test_F58_no_screen_writes_engineering_state(self):
        source = _code(_source("assy_v3", "ui", "selection_checkpoint.py"))
        for family in ("MechanicalFeasibilityAssessment", "CandidateComparison",
                       "SelectionProfile", "SelectionDecision"):
            self.assertNotIn(family, source)
        self.assertNotIn("reconcile", source)
        self.assertNotIn("Op(", source)

    def test_F59_state_mutation_calls_no_provider_and_no_evaluator(self):
        """`apply` is controlled mutation and premise-graph invalidation. If it
        could run an evaluator, every write would be an evaluation and nothing
        could say which one produced an answer."""
        source = _code(_source("assy_v3", "state", "design_state.py"))
        for reach in ("provider", "generate(", "evaluate_candidate",
                      "reconcile", "consumer_view", "SelectionDecision",
                      "MechanicalFeasibilityAssessment"):
            self.assertNotIn(reach, source)

    def test_F60_F61_the_unattended_runner_still_fabricates_nothing(self):
        state = self.chain()
        rec = run_window2.run_s7_reconcile("probe", state, 1)
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, rec["checkpoint_status"])
        self.assertIsNone(rec["current_commitment"])
        self.assertEqual([], state.family("SelectionDecision"))
        self.assertEqual([], state.family("HumanDecisionInput"))
        source = _source("tools", "run_window2.py")
        for fabrication in ("materialize_human_decision_input",
                            "commit_human_selection", "HumanDecisionInput",
                            "frontier[0]", "candidates[0]",
                            "recommended_candidate"):
            self.assertNotIn(fabrication, source)

    def test_F61b_the_runner_never_reports_a_stale_decision_as_current(self):
        state, decision = self.committed()
        rec = run_window2.run_selection_checkpoint("probe", state, 1)
        self.assertEqual(decision, rec["current_commitment"])
        self.replace_envelope(state)
        self.reconcile(state)
        rec = run_window2.run_selection_checkpoint("probe", state, 1)
        self.assertIsNone(rec["current_commitment"])
        self.assertEqual([decision], rec["historical_decisions"])
        self.assertEqual(run_window2.AWAITING_HUMAN_DECISION,
                         rec["checkpoint_status"])


# =====================================================================
# F62-F69 - the whole of S-7, twice
# =====================================================================
class TestFullChain(_Lifecycle):

    def test_F62_to_F69_the_chain_reopens_and_closes_again(self):
        """One design, one engineering revision, two human decisions. What is
        being asserted is the SEQUENCE: that the deterministic chain rebuilds
        itself, that the checkpoint reopens, that nothing commits in between, and
        that both decisions remain readable with only the second one current."""
        state = self.chain()                                          # F62
        self.assertEqual(lc.AWAITING_HUMAN_DECISION,
                         self.reconcile(state).human_state)
        first = self.decide(state, "CND-A", "A for now")               # F63
        self.assertEqual(dec.SELECTION_COMMITTED, first.status, first.problems)
        first_id = self.committed_decision(state)["entity_id"]
        self.assertEqual(lc.CURRENT_COMMITMENT, self.reconcile(state).human_state)

        self.replace_envelope(state)                                   # F64
        self.assertEqual(STALE, self.validity(state, first_id))
        self.assertIsNone(self.comparison(state))
        out = self.reconcile(state)                                    # F65
        self.assertEqual(sel.COMPARISON_WRITTEN, out.comparison)
        self.assertEqual(["CND-B"], self.comparison(state)["candidates"])
        self.assertEqual(lc.AWAITING_HUMAN_DECISION, out.human_state)  # F66
        self.assertIsNone(lc.current_commitment(state))                # F67

        second = self.decide(state, "CND-B", "B, now that A is unestablished")
        self.assertEqual(dec.SELECTION_COMMITTED, second.status, second.problems)
        second_id = self.committed_decision(state)["entity_id"]        # F68
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(sorted([first_id, second_id]),                # F69
                         self.all_ids(state, "SelectionDecision"))
        self.assertEqual(STALE, self.validity(state, first_id))
        self.assertEqual(STANDING, self.validity(state, second_id))
        self.assertEqual(2, len(state.family("HumanDecisionInput")))
        self.assertEqual("CND-A", state.entities[first_id]["selected_candidate"])

    def test_F69b_reconciling_the_reopened_design_is_idempotent(self):
        state = self.chain()
        self.decide(state, "CND-A", "A for now")
        self.replace_envelope(state)
        self.reconcile(state)
        settled = state.state_hash()
        for _round in range(3):
            out = self.reconcile(state)
            self.assertFalse(out.changed, out.as_dict())
        self.assertEqual(settled, state.state_hash())

    def test_F69c_order_does_not_change_the_answer(self):
        """Two designs, the same two changes applied in opposite orders, and one
        answer. Reconciliation that depended on the order it was asked in would
        be an answer about the caller rather than about the design."""
        first, second = self.chain(), self.chain()
        self.replace_envelope(first)
        self.constraint(first, eid="DSC-ORDER", blocks=True)
        self.reconcile(first)
        self.constraint(second, eid="DSC-ORDER", blocks=True)
        self.replace_envelope(second)
        self.reconcile(second)

        def answer(state):
            return {c: (records.current_assessment(state, c) or {}).get("status")
                    for c in ("CND-A", "CND-B")}, \
                   sorted((self.comparison(state) or {}).get("candidates") or [])

        self.assertEqual(answer(first), answer(second))


# =====================================================================
# F70-F75 - scope
# =====================================================================
class TestScope(_Lifecycle):

    LIFECYCLE = (("assy_v3", "lifecycle", "s7_reconcile.py"),
                 ("assy_v3", "lifecycle", "records.py"))

    def test_F70_F71_no_case_and_no_name_parsing(self):
        for parts in self.LIFECYCLE:
            source = _code(_source(*parts))
            for benchmark in ("BM-00", "guided-slider", "CND-A", "CND-B",
                              "endswith(", 'split("-")', "[-1]",
                              'startswith("CND'):
                self.assertNotIn(benchmark, source, "%s in %s" % (benchmark, parts))

    def test_F72_no_criterion_is_named_in_the_lifecycle_layer(self):
        for parts in self.LIFECYCLE:
            source = _source(*parts)
            for criterion in ("joint_count", "rigid_body_count", "package_volume",
                              "MINIMIZE", "MAXIMIZE"):
                self.assertNotIn(criterion, _code(source))

    def test_F73_nothing_here_implements_a_later_step(self):
        for parts in self.LIFECYCLE:
            source = _source(*parts)
            for later in ("VerificationPlanItem", "EvidenceItem",
                          "RequirementEvaluation", "s08", "s09",
                          "AssurancePackage"):
                self.assertNotIn(later, _code(source))

    def test_F74_the_retired_s04b_dependency_stays_retired(self):
        resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        for premise in resp["stages"]["s04b"]["required_reasoning_premise_classes"]:
            rule = premise["instance_selection"]
            populations = ([r["population"] for r in rule["by_role"]]
                           if rule.get("by_role") else [rule["population"]])
            self.assertNotIn("COMMITTED_BRANCH", populations)
            self.assertNotIn("selection_decision", premise["requires_semantics"])

    def test_F75_the_earlier_boundaries_are_where_they_were(self):
        resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        preference_readers = sorted(
            sid for sid, spec in resp["stages"].items()
            if any("selection_preference" in (p.get("requires_semantics") or [])
                   for p in spec.get("required_reasoning_premise_classes") or []))
        self.assertNotIn("feasibility", preference_readers)
        for sid in preference_readers:
            self.assertEqual("selection",
                             resp["stages"][sid].get("authority_stage", sid))
        self.assertEqual(["SelectionAdvisory", "SelectionConcern"],
                         resp["stages"]["selection_advisory"]
                         ["permitted_output_semantics"])
        self.assertEqual(["SelectionDecision"],
                         resp["stages"]["selection_decision"]
                         ["permitted_output_semantics"])


# =====================================================================
# The S-7 lifecycle matrix, pinned so it cannot drift
# =====================================================================
class TestLifecycleMatrix(_Lifecycle):
    """One row per kind of change, and what each one may and may not touch.

    The matrix is the closure argument of the whole of S-7: feasibility answers
    what can work, comparison answers how the workable ones differ, the advisory
    says what neither represents, a human commits - and every one of those loses
    or keeps authority for a stated reason when the design moves.
    """

    def picture(self, state):
        def val(family, eid=None):
            if eid is None:
                found = state.standing(family)
                return found[0]["entity_id"] if len(found) == 1 else None
            return self.validity(state, eid)
        return {"feasibility": {c: (records.current_assessment(state, c) or {}).get(
                                    "entity_id") for c in ("CND-A", "CND-B")},
                "comparison": val("CandidateComparison"),
                "advisory": val("SelectionAdvisory"),
                "commitment": (lc.current_commitment(state) or {}).get("entity_id")}

    def test_MATRIX_01_an_unrelated_invisible_fact_changes_nothing(self):
        state, _d = self.committed()
        before = self.picture(state)
        self.unrelated(state, "AMB-MATRIX1")
        self.reconcile(state)
        self.assertEqual(before, self.picture(state))

    def test_MATRIX_02_a_relevant_engineering_revision_reopens_everything(self):
        state, _d = self.committed()
        before = self.picture(state)
        self.replace_envelope(state)
        self.reconcile(state)
        after = self.picture(state)
        self.assertNotEqual(before["feasibility"]["CND-A"],
                            after["feasibility"]["CND-A"])
        self.assertEqual(before["feasibility"]["CND-B"],
                         after["feasibility"]["CND-B"])
        self.assertNotEqual(before["comparison"], after["comparison"])
        self.assertIsNone(after["advisory"])
        self.assertIsNone(after["commitment"])

    def test_MATRIX_03_evidence_filling_an_absence_reopens_the_answer(self):
        state = self.chain()
        fields = self.replace_envelope(state)
        self.reconcile(state)
        waiting = self.picture(state)
        self.author_envelope(state, fields, "ENV-MATRIX3")
        self.reconcile(state)
        after = self.picture(state)
        self.assertNotEqual(waiting["feasibility"]["CND-A"],
                            after["feasibility"]["CND-A"])
        self.assertEqual("FEASIBLE_FOR_SELECTION",
                         self.mfa(state, "CND-A")["status"])
        self.assertIsNotNone(after["comparison"])

    def test_MATRIX_04_a_new_candidate_ends_the_old_comparison(self):
        state, _d = self.committed()
        self.add_candidate(state, "D")
        self.reconcile(state)
        after = self.picture(state)
        self.assertIsNone(after["comparison"])
        self.assertIsNone(after["commitment"])

    def test_MATRIX_05_a_new_blocking_requirement_reopens_eligibility(self):
        """Unit D: by the requirement's declared evaluation point. A kind owed
        downstream keeps the population and remakes the comparison with the
        debt on it; a kind owed before selection empties the population. Both
        reopen the commitment, which was made without the requirement."""
        state, _d = self.committed()
        self.constraint(state, eid="DSC-MATRIX5", blocks=True)
        self.reconcile(state)
        picture = self.picture(state)
        self.assertIsNotNone(picture["comparison"])
        self.assertIsNone(lc.current_commitment(state))
        record = records.current_compliance(state, "CND-A", "DSC-MATRIX5")
        self.assertEqual(sel.NOT_YET_EVALUABLE, record["status"])
        self.assertEqual("DOWNSTREAM", record["evaluation_point"])

        state, _d = self.committed()
        self.constraint(state, eid="DSC-MATRIX5B", blocks=True,
                        kind="PROHIBITED_ENERGY_SOURCE")
        self.reconcile(state)
        self.assertIsNone(self.picture(state)["comparison"])
        self.assertIsNone(lc.current_commitment(state))
        record = records.current_compliance(state, "CND-A", "DSC-MATRIX5B")
        self.assertEqual(sel.NOT_YET_EVALUABLE, record["status"])
        self.assertEqual("PRE_SELECTION", record["evaluation_point"])

    def test_MATRIX_06_a_preference_change_leaves_feasibility_alone(self):
        state, _d = self.committed()
        before = self.picture(state)
        self.reconcile(state, selection_preferences=prefs(
            rigid_body_count=(MAXIMIZE, HIGH)))
        after = self.picture(state)
        self.assertEqual(before["feasibility"], after["feasibility"])
        self.assertNotEqual(before["comparison"], after["comparison"])
        self.assertIsNone(after["advisory"])
        self.assertIsNone(after["commitment"])

    def test_MATRIX_07_a_withdrawn_preference_source_leaves_no_comparison(self):
        state, _d = self.committed()
        before = self.picture(state)
        self.reconcile(state, selection_preferences=lc.ABSENT)
        after = self.picture(state)
        self.assertEqual(before["feasibility"], after["feasibility"])
        self.assertIsNone(after["comparison"])
        self.assertIsNone(after["commitment"])
        self.assertEqual(lc.REVIEW_NOT_READY, self.reconcile(state).human_state)

    def test_MATRIX_08_advisory_wording_after_a_commitment_changes_nothing(self):
        state, decision = self.committed()
        before = self.picture(state)
        self.withdraw(state, before["advisory"], stage="selection",
                      why="reworded")
        after = self.picture(state)
        self.assertEqual(before["feasibility"], after["feasibility"])
        self.assertEqual(before["comparison"], after["comparison"])
        self.assertIsNone(after["advisory"])
        self.assertEqual(decision, after["commitment"])

    def test_MATRIX_09_human_history_alone_changes_nothing(self):
        state, decision = self.committed()
        before = self.picture(state)
        snapshot = self.review_of(state)
        submitted = self.submit(state, snapshot, dec.KEEP_UNRESOLVED, None,
                                "recording a second opinion")
        self.assertTrue(submitted.ok, submitted.problems)
        out = self.commit(state, submitted.input_id)
        self.assertEqual(dec.DECISION_ALREADY_STANDING, out.status)
        self.assertEqual(before, self.picture(state))
        self.assertEqual(decision, lc.current_commitment(state)["entity_id"])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
