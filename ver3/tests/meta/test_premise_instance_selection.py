"""A premise says WHAT it needs. It must also say WHICH instances.

Semantic roles answer "what kind of information". They cannot answer "from what
population, how completely". Without that second answer the resolver had one
relevance model - branch lineage - and applied it to everything, so a demand on
the whole design was answered from one alternative's material: nineteen standing
requirements, nine delivered, and the premise reported SATISFIED.

These tests hold the separation: role, population, coverage - independently
declared, independently traceable, and neither of them a family name.
"""
from __future__ import annotations

import copy
import io
import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                                    # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

import ver3.assy_v3.view.consumer_view as cv                            # noqa: E402
from ver3.assy_v3.state.design_state import Contracts, DesignState       # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                      # noqa: E402
from ver3.assy_v3.view import (Sufficiency, ViewStatus,                  # noqa: E402
                               build_consumer_view, derive_required_minimum)

_RESP_PATH = os.path.join(_REPO, "ver3", "contracts",
                          "STAGE_RESPONSIBILITY_CONTRACT.yaml")

POPULATIONS = {cv.DESIGN_WIDE, cv.INVOCATION_BRANCH, cv.COMMITTED_BRANCH,
               cv.ALL_RETAINED_BRANCHES}
COVERAGES = {cv.ALL_APPLICABLE, cv.AT_LEAST_ONE}


def _premises(resp):
    for sid, stage in sorted((resp.get("stages") or {}).items()):
        for p in (stage or {}).get("required_reasoning_premise_classes") or []:
            yield sid, p


class _Base(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        with open(_RESP_PATH) as fh:
            cls.resp = yaml.safe_load(fh)


    def responsibility(self, stage_id, *premises, **stage_extra):
        """A responsibility contract holding exactly the premises under test."""
        resp = copy.deepcopy(self.resp)
        stage = resp["stages"][stage_id]
        stage["required_reasoning_premise_classes"] = list(premises)
        stage.update(stage_extra)
        return resp

    def view(self, stage_id, s, *premises, **kw):
        return build_consumer_view(stage_id, s, self.c,
                                   self.responsibility(stage_id, *premises), **kw)

    def atom(self, view, premise_class):
        """The one atomic obligation of the premise under test.

        A view also carries the stage's Source-A dependencies, which have their
        own verdicts; picking `assessment[0]` would assert about whichever of
        those happened to sort first.
        """
        for a in view.assessment:
            if a["requirement"] == premise_class:
                self.assertEqual(1, len(a["coverage"]), premise_class)
                return a["coverage"][0]
        raise AssertionError("no assessment for %s" % premise_class)

    def premise(self, name, roles, population, coverage=cv.ALL_APPLICABLE,
                applicability=None, existence=cv.REQUIRED_NONEMPTY):
        p = {"class": name, "requires_semantics": list(roles),
             "justified_by_question": "control", "why": "control",
             "instance_selection": {"population": population, "coverage": coverage,
                                    "existence": existence}}
        if applicability:
            p["instance_selection"]["applicability"] = applicability
        return p


# =====================================================================
# The contract corpus
# =====================================================================
class TestDeclaredCorpus(_Base):

    def test_SELECT_01_every_premise_declares_which_instances_it_needs(self):
        rows = list(_premises(self.resp))
        # 32 after the S7-A correction: `feasibility` gained the two classes its
        # declared domains actually need - realized motion, and the
        # candidate-local geometric findings - without which it declared domains
        # whose evidence its view could not contain.
        #
        # 33 at S7-B, for the third instance of the same defect. Two domains are
        # about DEMANDS - effects that must occur, loads the world applies, sites
        # a reaction must reach - and the class that would carry them did not
        # exist, so an undischarged obligation was exactly what the view could
        # not contain.
        #
        # 35 at S7-C: `selection` gained the design-wide hard requirements, whose
        # blocking half decides eligibility, and the topology its counting
        # metrics are counts of. Both are asked for by engineering role.
        #
        # 41 at S7-D: the `selection_advisory` pass declares six of its own. A
        # reviewer asked what the deterministic comparison does NOT represent has
        # to see the comparison, the profile it was made under, why the
        # population is eligible, and the engineering state a concern could come
        # from - a reviewer shown only the metrics could only restate them.
        #
        # 53 at S7-E: the two downstream selection passes declare six each. The
        # review pass needs the comparison, the profile it was made under, why
        # the population is eligible, the retained population itself, the
        # requirements that decide blocking, and - MAY_BE_EMPTY - whatever a
        # reviewer said. The writer needs the same five plus the submitted human
        # decision, because a commitment rests on two independent facts: a person
        # asked for it, and what they were shown is still what the design says.
        # 59 at S-9: s05 declares six. Embodiment needs the interactions it
        # realizes, the topology it attaches geometry to, the spatial commitment
        # its envelope constraints bind, the full obligation set S05-C4 checks
        # coverage against, and - MAY_BE_EMPTY - the declared clearances S05-C9
        # turns into constraints and the regions S05-C8 keeps features out of.
        #
        # 60 at S-9 semantic hardening: s05 declares a seventh, `limit_to_produce`.
        # S05-C3 asks whether a feature pair can PRODUCE a travel limit that a
        # MobilityExpectation dispositions as BLOCKED_BY - and the mobility
        # dispositions were not among the six. The check read a family the view
        # never granted, `_rows` returned the empty list it returns for anything
        # absent, every cell was skipped, and the check reported compliance while
        # being unable to fail on any input. The premise is the repair rather
        # than a deleted check, because a stage cannot be asked to satisfy a
        # demand it was never shown.
        #
        # 66 at the selection->embodiment closure: s05 declares six more, and
        # they are all about WHICH design it is embodying. Two make the
        # commitment visible - the standing SelectionDecision (DESIGN_WIDE,
        # because the decision is not branch-local; it is what NAMES the branch)
        # and the selected Candidate with its principle. One scopes obligation
        # applicability to that candidate, so C4 stops demanding the selected
        # candidate discharge another candidate's obligations. Three carry the
        # branch's established configurations, motions and load routes, all
        # MAY_BE_EMPTY: a static mechanism has no motion, and forcing it to
        # author one to satisfy readiness would be inventing engineering.
        #
        # 67 at the S03a seam closure: s03a declares `open_question_to_cite`.
        # Its prompt already demanded that `UnresolvedDecision.kept_open_by` cite
        # the Ambiguity or Freedom entities keeping a decision open, by id, while
        # the view carried neither family - so the stage was asked to reference
        # entities it could not see, and the only ways to comply were to invent
        # an id or to leave the field empty. MAY_BE_EMPTY: a fully determinate
        # source leaves no open question, and demanding one would make s01 invent
        # an ambiguity.
        #
        # 69 at the motion-semantics migration: `demanded_state_change` is
        # declared twice, by the pass that REALIZES a required state change and
        # by the responsibility that judges whether it is reachable. Both were
        # deciding for themselves whether one was required - s04b by inventing
        # which two configurations a transition connects, feasibility by reading
        # a configuration's `distinguishing_basis` as a demand - because the
        # family that states it was in neither view. MAY_BE_EMPTY on both: a
        # mechanism asked for no state change is an ordinary mechanism, and
        # demanding a requirement before the question may be asked would make
        # every static candidate unready.
        # 70 at the parameter authority closure: `embodiment_settlement`,
        # declared by feasibility, MAY_BE_EMPTY. A fit a domain deferred to the
        # embodiment block must be read as discharged once the block has
        # settled it, and the Constraint that carries the settlement was in no
        # feasibility view.
        # 71 at the selection revision closure: `standing_commitment`, declared
        # by the human review pass, MAY_BE_EMPTY. A person shown a design that
        # has already committed must see the commitment their SELECT would
        # revise, and the decision family was in no review view.
        # 73 at the post-selection handoff closure (Unit E): s05 declares
        # `hard_requirement_to_honour` (every stated hard requirement,
        # DESIGN_WIDE) and `hard_requirement_debt_to_carry` (the compliance
        # records owed to s05, COMMITTED_BRANCH, applicability
        # DEFERRED_TO_INVOKING_RESPONSIBILITY), both MAY_BE_EMPTY.
        self.assertEqual(73, len(rows), "the premise corpus changed size")
        for sid, p in rows:
            sel = p.get("instance_selection")
            self.assertTrue(sel, "%s/%s declares no instance_selection"
                            % (sid, p.get("class")))
            rules = ([dict(r) for r in sel["by_role"]] if sel.get("by_role")
                     else [sel])
            for r in rules:
                self.assertIn(r["population"], POPULATIONS, "%s/%s" % (sid, p["class"]))
                self.assertIn(r["coverage"], COVERAGES, "%s/%s" % (sid, p["class"]))

    def test_SELECT_01b_every_premise_resolves_to_a_rule_for_every_role(self):
        for sid, p in _premises(self.resp):
            rule = cv._selection_of(p, list(p.get("requires_semantics") or []))
            for role in p.get("requires_semantics") or []:
                self.assertIn(role, rule, "%s/%s has no rule for %s"
                              % (sid, p["class"], role))

    def test_SELECT_02_no_selector_names_a_canonical_family(self):
        """A population says WHERE to look. The role says what qualifies. If a
        selector named a family it would be a whitelist wearing a new word."""
        blob = yaml.safe_dump([p.get("instance_selection")
                               for _s, p in _premises(self.resp)])
        named = [f for f in self.c.families if re.search(r"\b%s\b" % f, blob)]
        self.assertEqual([], named, "instance selectors name families: %s" % named)

    def test_SELECT_02b_each_vocabulary_term_is_defined_once(self):
        vocab = self.resp["instance_selection_vocabulary"]
        self.assertEqual(POPULATIONS, set(vocab["population"]))
        self.assertEqual(COVERAGES, set(vocab["coverage"]))
        for group in ("population", "coverage"):
            for term, text in vocab[group].items():
                self.assertGreater(len(text.split()), 12,
                                   "%s is named but not defined" % term)

    def test_SELECT_14_role_population_and_coverage_are_separately_traceable(self):
        rm = derive_required_minimum("s04a", self.c, self.resp)
        req = [r for r in rm.requirements if r.key == "reach_requirement"][0]
        # The one premise whose roles genuinely live in different populations.
        self.assertEqual(cv.DESIGN_WIDE, req.selection_for("actor_role")["population"])
        self.assertEqual(cv.INVOCATION_BRANCH,
                         req.selection_for("functional_region")["population"])
        d = req.as_dict()
        self.assertIn("selection", d)
        self.assertIn("requires_semantics", d["trace"])

    def test_SELECT_17_18_19_no_benchmark_model_or_creation_order_logic(self):
        import inspect
        src = "\n".join(inspect.getsource(o) for o in (
            cv._population_members, cv._applicable, cv.expected_instances,
            cv._selection_of, cv.select_instances, cv._assess_atom))
        self.assertIsNone(re.search(r"BM-\d|PRB-\d|deepseek|gpt-|claude", src, re.I))
        self.assertIsNone(re.search(r"created_at|timestamp|creation_order|_created_by",
                                    src),
                          "creation order is not engineering scope")

    def test_SELECT_13_unknown_consumer_fails_closed(self):
        for sid in ("s02", "s03a", "s03b", "s04a", "s04b", "selection"):
            self.assertTrue(derive_required_minimum(sid, self.c, self.resp).requirements
                            or sid == "s01")
        for sid in ("s05",):
            self.assertTrue(derive_required_minimum(sid, self.c, self.resp).requirements,
                            "s05 is a declared responsibility and must resolve")
        # `s03` is an OWNER and not a responsibility, which is the distinction
        # this test exists for; "" is the empty case. `s05` used to appear here
        # and no longer can - it is declared.
        for unknown in ("s03", ""):
            with self.assertRaises(cv.UnknownConsumer):
                derive_required_minimum(unknown, self.c, self.resp)

    def test_SELECT_13b_a_premise_with_no_declaration_fails_closed(self):
        with self.assertRaises(KeyError):
            cv._selection_of({"class": "undeclared"}, ["actor_role"])


# =====================================================================
# Populations, against state
# =====================================================================
class TestPopulations(_Base):

    def design(self, n_requirements=19, n_addressed=9, candidates=("CND-A",)):
        """N requirements; only the first `n_addressed` are reachable from a
        candidate. The rest are UNADDRESSED - which is a finding, not a reason to
        hide them."""
        s = DesignState(run_id="sel")
        ids = []
        for i in range(1, n_requirements + 1):
            ids.append(self.add(s, "s01", "Requirement", "REQ-%02d" % i,
                                quantity_class="BAND"))
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=ids[:n_addressed])
        for cid in candidates:
            self.add(s, "s02", "Candidate", cid, principle={"h": "f"},
                     addresses_obligations=["OBL-1"], obligations_created=[])
        return s, ids


    # -- 04 / 05 / 06 / 07: the 19 of 19 case ------------------------
    def test_SELECT_04_full_population_means_every_applicable_standing_instance(self):
        s, ids = self.design()
        v = self.view("s02", s, self.premise("full_requirements", ["source_requirement"],
                                             cv.DESIGN_WIDE))
        got = {e["entity_id"] for e in v.entities if e.get("_family") == "Requirement"}
        self.assertEqual(set(ids), got, "the full requirement set is not full")
        a = self.atom(v, "full_requirements")
        self.assertEqual(19, a["expected_count"])
        self.assertEqual(19, a["selected_count"])
        self.assertEqual(Sufficiency.SATISFIED.value, a["verdict"])

    def test_SELECT_05_06_nineteen_expected_nine_selected_is_not_satisfied(self):
        """The exact blocker. Nine arrive, the premise means all of them."""
        s, ids = self.design()
        rm = derive_required_minimum(
            "s02", self.c, self.responsibility(
                "s02", self.premise("full_requirements", ["source_requirement"],
                                    cv.DESIGN_WIDE)))
        req = rm.requirements[-1]
        # Fault injection: exactly the nine that carry candidate lineage arrive.
        nine = [{"entity_id": i} for i in ids[:9]]
        a = cv._assess(s, self.c, req, nine)
        cover = a["coverage"][0]
        self.assertEqual(19, cover["expected_count"])
        self.assertEqual(9, cover["selected_count"])
        self.assertNotEqual(Sufficiency.SATISFIED.value, cover["verdict"])
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value, cover["verdict"],
                         "all nineteen exist upstream, so an incomplete view is ours")

    def test_SELECT_07_an_unaddressed_requirement_stays_visible(self):
        """Not addressed is not irrelevant. It may be the finding."""
        s, ids = self.design()
        v = self.view("s02", s, self.premise("full_requirements", ["source_requirement"],
                                             cv.DESIGN_WIDE))
        got = {e["entity_id"] for e in v.entities}
        for eid in ids[9:]:
            self.assertIn(eid, got, "%s is addressed by no candidate and vanished" % eid)
            why = v.why(eid)[0]
            self.assertEqual(cv.UNSCOPED, why["branch_scope"],
                             "it really has no branch lineage")
            self.assertEqual(cv.DESIGN_WIDE, why["population"])

    def test_SELECT_20_visibility_added_no_engineering_dependency(self):
        """The unaddressed requirements are visible and still unaddressed: no
        premise or reference was invented to reach them."""
        s, ids = self.design()
        for eid in ids[9:]:
            rec = s.entities[eid]
            self.assertEqual([], rec.get("_premises", []),
                             "a premise was fabricated for visibility")
        cand = s.entities["CND-A"]
        self.assertEqual(["OBL-1"], cand["addresses_obligations"])

    # -- 03: before any candidate exists -----------------------------
    def test_SELECT_03_design_wide_premises_work_before_any_candidate(self):
        s = DesignState(run_id="pre")
        for i in range(1, 4):
            self.add(s, "s01", "Requirement", "REQ-%d" % i, quantity_class="BAND")
        self.add(s, "s01", "Ambiguity", "AMB-1")
        self.add(s, "s01", "Actor", "ACT-1")
        self.assertEqual([], list(s.standing("Candidate")), "no fake candidate")
        v = self.view("s02", s,
                      self.premise("full_requirements", ["source_requirement"],
                                   cv.DESIGN_WIDE),
                      self.premise("every_ambiguity", ["open_question"], cv.DESIGN_WIDE))
        got = {e["entity_id"] for e in v.entities}
        for eid in ("REQ-1", "REQ-2", "REQ-3", "AMB-1"):
            self.assertIn(eid, got, "%s missing from a pre-candidate view" % eid)
        for name in ("full_requirements", "every_ambiguity"):
            self.assertEqual(Sufficiency.SATISFIED.value,
                             self.atom(v, name)["verdict"], name)

    # -- 08 / 09 / 10 / 23: populations side by side -----------------
    def branched(self):
        s, ids = self.design(n_requirements=2, n_addressed=1,
                             candidates=("CND-A", "CND-B"))
        self.add(s, "s02", "LoadCase", "LC-1")
        self.add(s, "s03", "Body", "BOD-A", prem=["CND-A"])
        self.add(s, "s03", "Body", "BOD-B", prem=["CND-B"])
        return s

    def test_SELECT_08_candidate_independent_load_cases_need_no_lineage(self):
        s = self.branched()
        self.assertEqual([], s.entities["LC-1"].get("_premises", []))
        v = self.view("s03a", s, self.premise("loads", ["load_case"], cv.DESIGN_WIDE),
                      invocation_branch="CND-A")
        self.assertIn("LC-1", {e["entity_id"] for e in v.entities})

    def test_SELECT_09_10_23_design_wide_and_branch_local_coexist(self):
        """One view, two relevance models: every requirement, and only this
        branch's topology."""
        s = self.branched()
        v = self.view("s03b", s,
                      self.premise("full_requirements", ["source_requirement"],
                                   cv.DESIGN_WIDE),
                      self.premise("this_topology", ["topology_element"],
                                   cv.INVOCATION_BRANCH),
                      invocation_branch="CND-A")
        got = {e["entity_id"] for e in v.entities}
        self.assertIn("REQ-01", got)
        self.assertIn("REQ-02", got, "the unaddressed requirement is still required")
        self.assertIn("BOD-A", got, "the invocation branch's own topology")
        self.assertNotIn("BOD-B", got, "another branch's topology reached the view")

    def test_SELECT_11_all_retained_branches_is_representable(self):
        s = self.branched()
        v = self.view("selection", s, self.premise("compare", ["topology_element"],
                                              cv.ALL_RETAINED_BRANCHES),
                      invocation_branch="CND-A")
        got = {e["entity_id"] for e in v.entities}
        self.assertIn("BOD-A", got)
        self.assertIn("BOD-B", got, "comparison cannot be done from one alternative")

    def test_SELECT_12_committed_branch_is_representable(self):
        s = self.branched()
        p = self.premise("committed", ["topology_element"], cv.COMMITTED_BRANCH)
        v = self.view("s04b", s, p, invocation_branch="CND-A")
        self.assertEqual(set(), {e["entity_id"] for e in v.entities},
                         "no selection is recorded, so there is no committed branch")
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value,
                         self.atom(v, "committed")["verdict"])
        self.add(s, "selection", "SelectionDecision", "SEL-1", selected_candidate="CND-B")
        v2 = self.view("s04b", s, p, invocation_branch="CND-A")
        got = {e["entity_id"] for e in v2.entities}
        self.assertIn("BOD-B", got, "the committed branch is the selected one")
        self.assertNotIn("BOD-A", got)

    # -- 15: expected is not read off the view -----------------------
    def test_SELECT_15_expected_population_is_independent_of_the_view(self):
        s, ids = self.design()
        rule = {"population": cv.DESIGN_WIDE, "coverage": cv.ALL_APPLICABLE,
                "existence": cv.REQUIRED_NONEMPTY, "applicability": cv.ALL_MEMBERS}
        expected = cv.expected_instances(s, self.c, ["Requirement"], rule, None)
        self.assertEqual(set(ids), expected)
        # No view was built. Sufficiency that derived its expectation from the
        # selection could only ever agree with itself.
        empty = cv._assess(s, self.c, cv.Requirement(
            cv.Source.REASONING_PREMISE, "p", ["Requirement"], {},
            by_role={"source_requirement": ["Requirement"]},
            selection={"source_requirement": rule}), [])
        self.assertEqual(19, empty["coverage"][0]["expected_count"])
        self.assertEqual(0, empty["coverage"][0]["selected_count"])

    def test_SELECT_15b_genuine_upstream_absence_is_not_projection_failure(self):
        s = DesignState(run_id="bare")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        v = self.view("s03a", s, self.premise("loads", ["load_case"], cv.DESIGN_WIDE))
        a = self.atom(v, "loads")
        self.assertEqual(0, a["expected_count"])
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value, a["verdict"])
        self.assertEqual(ViewStatus.UPSTREAM_INSUFFICIENCY, v.status)


# =====================================================================
# Extension
# =====================================================================
class TestExtension(_Base):

    def test_SELECT_16_a_new_premise_changes_selection_with_no_resolver_change(self):
        """Declaration only: same role, different population, different view."""
        s = DesignState(run_id="ext")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-1"])
        self.add(s, "s01", "Requirement", "REQ-LOOSE", quantity_class="BAND")
        self.add(s, "s02", "Candidate", "CND-A", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        role = ["source_requirement"]
        narrow = build_consumer_view("s02", s, self.c, self.responsibility(
            "s02", self.premise("p_new", role, cv.INVOCATION_BRANCH)),
            invocation_branch="CND-A")
        broad = build_consumer_view("s02", s, self.c, self.responsibility(
            "s02", self.premise("p_new", role, cv.DESIGN_WIDE)),
            invocation_branch="CND-A")
        # Assert on the premise under test, not on the whole view: the view also
        # carries this stage's Source-A dependencies, and one of those legitimately
        # supplies requirements design-wide. What the declaration controls is what
        # THIS premise expects and selects.
        na, ba = self.atom(narrow, "p_new"), self.atom(broad, "p_new")
        self.assertNotIn("REQ-LOOSE", na["expected"])
        self.assertIn("REQ-LOOSE", ba["expected"])
        self.assertLess(na["expected_count"], ba["expected_count"],
                        "one declaration changed, the population changed with it")
        self.assertEqual(na["selected"], na["expected"])
        self.assertEqual(ba["selected"], ba["expected"])

    def test_SELECT_21_22_applicability_is_a_registered_rule_not_a_redesign(self):
        """CASE A / CASE B. A requirement that applies only in one scenario, or
        only in one configuration, is a NEW NAMED RULE resolved at one point.

        The rule below is registered by this test, reads a canonical declared
        reference, and narrows the expected population. Nothing in
        `select_instances`, `_assess_atom`, `build_consumer_view` or `ConsumerView`
        is touched - which is the property being falsified.
        """
        s = DesignState(run_id="appl")
        self.add(s, "s01", "Scenario", "SCN-MAINT")
        self.add(s, "s01", "Scenario", "SCN-OP")
        self.add(s, "s02", "LoadCase", "LC-MAINT", scenario="SCN-MAINT")
        self.add(s, "s02", "LoadCase", "LC-OP", scenario="SCN-OP")

        def same_scenario(ids, ctx):
            state = ctx["state"]
            return {i for i in ids
                    if state.entities[i].get("scenario") == "SCN-MAINT"}

        before = set(cv.APPLICABILITY_RULES)
        cv.APPLICABILITY_RULES["IN_INVOCATION_SCENARIO"] = same_scenario
        try:
            resp = self.responsibility("s03a", self.premise(
                "loads", ["load_case"], cv.DESIGN_WIDE,
                applicability="IN_INVOCATION_SCENARIO"))
            v = build_consumer_view("s03a", s, self.c, resp)
            got = {e["entity_id"] for e in v.entities
                   if e.get("_family") == "LoadCase"}
            self.assertEqual({"LC-MAINT"}, got)
            a = self.atom(v, "loads")
            self.assertEqual(1, a["expected_count"])
            self.assertEqual("IN_INVOCATION_SCENARIO", a["applicability"])
            self.assertEqual(Sufficiency.SATISFIED.value, a["verdict"])
        finally:
            cv.APPLICABILITY_RULES.pop("IN_INVOCATION_SCENARIO", None)
        self.assertEqual(before, set(cv.APPLICABILITY_RULES))

    def test_SELECT_21b_an_undeclared_applicability_rule_fails_closed(self):
        with self.assertRaises(ValueError):
            cv._applicable({"X"}, "NOT_A_RULE", {})

    def test_SELECT_21c_the_seam_is_one_dispatch_point(self):
        import inspect
        import ast
        tree = ast.parse(inspect.getsource(cv))
        registries = [n for n in ast.walk(tree)
                      if isinstance(n, (ast.Assign, ast.AnnAssign))
                      and any(getattr(t2, "id", None) == "APPLICABILITY_RULES"
                              for t2 in (n.targets if isinstance(n, ast.Assign)
                                         else [n.target]))]
        self.assertEqual(1, len(registries), "more than one rule registry")
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", None) == "_applicable"]
        self.assertEqual(1, len(calls),
                         "applicability is resolved in more than one place")


class TestPriorSuitesStillHold(_Base):
    """SELECT-24."""

    def test_SELECT_24_view_scope_and_lineage_suites_remain_green(self):
        from .test_consumer_view import (TestBranchScopeLineage, TestCoreCorrections,
                                         TestHistoricalReplays, TestSufficiency)
        suite = unittest.TestSuite()
        load = unittest.TestLoader().loadTestsFromTestCase
        for cls in (TestBranchScopeLineage, TestCoreCorrections,
                    TestHistoricalReplays, TestSufficiency):
            suite.addTests(load(cls))
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful(),
                        "\n".join("%s\n%s" % (case, err) for case, err in
                                  result.failures + result.errors))


if __name__ == "__main__":
    unittest.main()


# =====================================================================
# Semantic completeness: existence, and a generic invocation context
# =====================================================================
class TestExistenceSemantics(_Base):
    """Coverage says how completely to select. It cannot also say whether the
    population may be empty. "Every recorded ambiguity" is satisfied by a design
    that recorded none; "the full requirement set" is not."""

    def bare(self):
        s = DesignState(run_id="exist")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        return s

    def test_SELECT_C01_C07_all_of_nothing_satisfies_a_may_be_empty_premise(self):
        s = self.bare()
        self.assertEqual([], list(s.standing("Ambiguity")))
        v = self.view("s02", s, self.premise(
            "recorded_ambiguity", ["open_question"], cv.DESIGN_WIDE,
            existence=cv.MAY_BE_EMPTY))
        a = self.atom(v, "recorded_ambiguity")
        self.assertEqual(0, a["expected_count"])
        self.assertEqual(Sufficiency.SATISFIED.value, a["verdict"])
        self.assertIn("permits", a["why"])

    def test_SELECT_C02_C09_required_nonempty_with_nothing_is_missing_upstream(self):
        s = DesignState(run_id="exist")
        v = self.view("s02", s, self.premise(
            "requirement_set", ["source_requirement"], cv.DESIGN_WIDE,
            existence=cv.REQUIRED_NONEMPTY))
        a = self.atom(v, "requirement_set")
        self.assertEqual(0, a["expected_count"])
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value, a["verdict"])

    def test_SELECT_C02b_the_two_empty_cases_differ(self):
        """The defect at 57e241f: both were MISSING_UPSTREAM, indistinguishable."""
        s = self.bare()
        v = self.view("s02", s,
                      self.premise("legal_empty", ["open_question"], cv.DESIGN_WIDE,
                                   existence=cv.MAY_BE_EMPTY),
                      self.premise("illegal_empty", ["physical_effect_obligation"],
                                   cv.DESIGN_WIDE, existence=cv.REQUIRED_NONEMPTY))
        self.assertEqual(0, self.atom(v, "legal_empty")["expected_count"])
        self.assertEqual(0, self.atom(v, "illegal_empty")["expected_count"])
        self.assertEqual(Sufficiency.SATISFIED.value,
                         self.atom(v, "legal_empty")["verdict"])
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value,
                         self.atom(v, "illegal_empty")["verdict"])

    def test_SELECT_C08_zero_unresolved_items_is_a_desired_state(self):
        s = self.bare()
        decl = [p for _sid, p in _premises(self.resp)
                if p["class"] == "unresolved_blocking_scope"][0]
        self.assertEqual(cv.MAY_BE_EMPTY, decl["instance_selection"]["existence"])
        v = self.view("selection", s, decl)
        self.assertEqual(Sufficiency.SATISFIED.value,
                         self.atom(v, "unresolved_blocking_scope")["verdict"])

    def test_SELECT_C03_every_premise_role_declares_existence(self):
        seen = {cv.MAY_BE_EMPTY: 0, cv.REQUIRED_NONEMPTY: 0}
        for sid, p in _premises(self.resp):
            sel = p["instance_selection"]
            rows = sel["by_role"] if sel.get("by_role") else [sel]
            for r in rows:
                self.assertIn("existence", r, "%s/%s" % (sid, p["class"]))
                self.assertIn(r["existence"], seen, "%s/%s" % (sid, p["class"]))
                self.assertTrue(r.get("existence_why"), "%s/%s" % (sid, p["class"]))
                seen[r["existence"]] += 1
        self.assertTrue(all(seen.values()), "one existence value is never used: %s" % seen)

    def test_SELECT_C04_coverage_and_existence_are_independent(self):
        """Four combinations, four outcomes. Neither term implies the other."""
        s, ids = TestPopulations.design(self, n_requirements=3, n_addressed=1)
        rule = lambda cov, ex: {"population": cv.DESIGN_WIDE, "coverage": cov,
                                "existence": ex, "applicability": cv.ALL_MEMBERS}
        req = lambda cov, ex: cv.Requirement(
            cv.Source.REASONING_PREMISE, "p", ["Requirement"], {},
            by_role={"source_requirement": ["Requirement"]},
            selection={"source_requirement": rule(cov, ex)})
        one = [{"entity_id": ids[0]}]
        self.assertEqual(Sufficiency.SATISFIED.value,
                         cv._assess(s, self.c, req(cv.AT_LEAST_ONE, cv.REQUIRED_NONEMPTY),
                                    one)["verdict"])
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value,
                         cv._assess(s, self.c, req(cv.ALL_APPLICABLE, cv.REQUIRED_NONEMPTY),
                                    one)["verdict"])
        empty = DesignState(run_id="none")
        self.assertEqual(Sufficiency.SATISFIED.value,
                         cv._assess(empty, self.c, req(cv.ALL_APPLICABLE, cv.MAY_BE_EMPTY),
                                    [])["verdict"])
        self.assertEqual(Sufficiency.MISSING_UPSTREAM.value,
                         cv._assess(empty, self.c,
                                    req(cv.AT_LEAST_ONE, cv.REQUIRED_NONEMPTY),
                                    [])["verdict"])

    def test_SELECT_C05_C06_the_19_of_19_and_19_of_9_behaviour_is_intact(self):
        s, ids = TestPopulations.design(self)
        v = self.view("s02", s, self.premise("full_requirements",
                                             ["source_requirement"], cv.DESIGN_WIDE))
        a = self.atom(v, "full_requirements")
        self.assertEqual((19, 19), (a["expected_count"], a["selected_count"]))
        self.assertEqual(Sufficiency.SATISFIED.value, a["verdict"])
        rm = derive_required_minimum("s02", self.c, self.responsibility(
            "s02", self.premise("full_requirements", ["source_requirement"],
                                cv.DESIGN_WIDE)))
        nine = [{"entity_id": i} for i in ids[:9]]
        cover = cv._assess(s, self.c, rm.requirements[-1], nine)["coverage"][0]
        self.assertEqual((19, 9), (cover["expected_count"], cover["selected_count"]))
        self.assertEqual(Sufficiency.PROJECTION_FAILURE.value, cover["verdict"])

    def test_SELECT_C21_no_fake_candidate_lineage_was_introduced(self):
        s, ids = TestPopulations.design(self)
        for eid in ids[9:]:
            self.assertEqual([], s.entities[eid].get("_premises", []))
        self.assertEqual([], list(DesignState(run_id="x").standing("Candidate")))


class TestInvocationContext(_Base):
    """Same premise, same state, different invocation - different population.

    At 57e241f the only structured context reaching an applicability rule was the
    branch: no scenario, no configuration, no actor. A scenario-specific premise
    could only be expressed by writing the scenario id INTO the rule, which is a
    fixture literal in production logic and does not generalise to a second
    scenario at all.
    """

    def scenarios(self):
        s = DesignState(run_id="anchor")
        self.add(s, "s01", "Scenario", "SCN-MAINT")
        self.add(s, "s01", "Scenario", "SCN-OP")
        self.add(s, "s02", "LoadCase", "LC-MAINT", scenario="SCN-MAINT")
        self.add(s, "s02", "LoadCase", "LC-OP", scenario="SCN-OP")
        # Declares no reference to Scenario at all, so no scenario anchor can
        # exclude it: it was never scoped to one.
        self.add(s, "s01", "Requirement", "REQ-GLOBAL", quantity_class="BAND")
        return s

    def loads(self):
        return self.premise("loads", ["load_case", "source_requirement"],
                            cv.DESIGN_WIDE,
                            applicability=cv.MATCHES_INVOCATION_ANCHORS)

    def test_SELECT_C10_scenario_anchor_changes_the_expected_population(self):
        s = self.scenarios()
        resp = self.responsibility("s03a", self.loads())
        seen = {}
        for anchor in ("SCN-MAINT", "SCN-OP"):
            v = build_consumer_view("s03a", s, self.c, resp,
                                    invocation=cv.InvocationContext.of(s, None, anchor))
            seen[anchor] = {e["entity_id"] for e in v.entities
                            if e.get("_family") in ("LoadCase", "Requirement")}
        self.assertEqual({"LC-MAINT", "REQ-GLOBAL"}, seen["SCN-MAINT"])
        self.assertEqual({"LC-OP", "REQ-GLOBAL"}, seen["SCN-OP"])
        self.assertNotEqual(seen["SCN-MAINT"], seen["SCN-OP"],
                            "the same state gave the same answer to two questions")

    def test_SELECT_C11_C13_C22_the_rule_holds_no_id_of_any_kind(self):
        import inspect
        src = inspect.getsource(cv._matches_invocation_anchors)
        self.assertIsNone(re.search(r"SCN-|CFG-|LC-|BM-\d|PRB-\d|ACT-", src),
                          "a fixture id is baked into production applicability")
        self.assertIsNone(re.search(r"deepseek|gpt-|claude", src, re.I))
        named = [f for f in self.c.families if re.search(r"['\"]%s['\"]" % f, src)]
        self.assertEqual([], named, "the rule names families: %s" % named)
        self.assertNotIn("in rec", src, "no substring matching")

    def test_SELECT_C12_configuration_anchor_does_the_same(self):
        """A different anchor KIND, the same rule, no new code."""
        s = DesignState(run_id="cfg")
        self.add(s, "s03", "Body", "BOD-1")
        self.add(s, "s03", "Configuration", "CFG-STOWED", name="stowed",
                 bodies_present=["BOD-1"], expected_mobility=[])
        self.add(s, "s03", "Configuration", "CFG-DEPLOYED", name="deployed",
                 bodies_present=["BOD-1"], expected_mobility=[])
        self.add(s, "s03", "MobilityExpectation", "MEX-STOWED",
                 configuration="CFG-STOWED", dispositions=[])
        self.add(s, "s03", "MobilityExpectation", "MEX-DEPLOYED",
                 configuration="CFG-DEPLOYED", dispositions=[])
        rule = {"population": cv.DESIGN_WIDE, "coverage": cv.ALL_APPLICABLE,
                "existence": cv.REQUIRED_NONEMPTY,
                "applicability": cv.MATCHES_INVOCATION_ANCHORS}
        got = {}
        for anchor in ("CFG-STOWED", "CFG-DEPLOYED"):
            got[anchor] = cv.expected_instances(
                s, self.c, ["MobilityExpectation"], rule, None, None,
                cv.InvocationContext.of(s, None, anchor))
        self.assertEqual({"MEX-STOWED"}, got["CFG-STOWED"])
        self.assertEqual({"MEX-DEPLOYED"}, got["CFG-DEPLOYED"])

    def test_SELECT_C14_C17_anchors_are_canonical_and_typed_not_free_text(self):
        s = self.scenarios()
        self.add(s, "s01", "Actor", "ACT-1")
        ctx = cv.InvocationContext.of(s, "CND-X", "SCN-MAINT", "ACT-1")
        self.assertEqual({"Scenario": "SCN-MAINT", "Actor": "ACT-1"}, ctx.anchors,
                         "the family comes from state, not from the caller")
        self.assertEqual("CND-X", ctx.branch)
        self.assertIn("anchors", ctx.as_dict())
        with self.assertRaises(ValueError):
            cv.InvocationContext.of(s, None, "not an entity")

    def test_SELECT_C15_unknown_applicability_rule_still_fails_closed(self):
        with self.assertRaises(ValueError):
            cv._applicable({"X"}, "NOT_A_RULE", {})
        s = self.scenarios()
        resp = self.responsibility("s03a", self.premise(
            "loads", ["load_case"], cv.DESIGN_WIDE, applicability="NOT_A_RULE"))
        with self.assertRaises(ValueError):
            build_consumer_view("s03a", s, self.c, resp)

    def test_SELECT_C16_a_new_relation_needs_no_change_to_the_selection_core(self):
        """Anchoring on a family nothing anticipated, using the shipped rule."""
        s = DesignState(run_id="new")
        self.add(s, "s01", "Actor", "ACT-A")
        self.add(s, "s01", "Actor", "ACT-B")
        self.add(s, "s02", "Obligation", "OBL-A", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=[],
                 involves_actors=["ACT-A"])
        self.add(s, "s02", "Obligation", "OBL-B", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=[],
                 involves_actors=["ACT-B"])
        rule = {"population": cv.DESIGN_WIDE, "coverage": cv.ALL_APPLICABLE,
                "existence": cv.REQUIRED_NONEMPTY,
                "applicability": cv.MATCHES_INVOCATION_ANCHORS}
        for anchor, expect in (("ACT-A", "OBL-A"), ("ACT-B", "OBL-B")):
            got = cv.expected_instances(s, self.c, ["Obligation"], rule, None, None,
                                        cv.InvocationContext.of(s, None, anchor))
            self.assertEqual({expect}, got, anchor)

    def test_SELECT_C18_C19_C20_prior_behaviour_is_unchanged(self):
        s, _ids = TestPopulations.design(self, n_requirements=2, n_addressed=1,
                                         candidates=("CND-A", "CND-B"))
        self.add(s, "s03", "Body", "BOD-A", prem=["CND-A"])
        self.add(s, "s03", "Body", "BOD-B", prem=["CND-B"])
        v = build_consumer_view("s03b", s, self.c, self.responsibility(
            "s03b",
            self.premise("full_requirements", ["source_requirement"], cv.DESIGN_WIDE),
            self.premise("this_topology", ["topology_element"], cv.INVOCATION_BRANCH)),
            invocation=cv.InvocationContext(branch="CND-A"))
        got = {e["entity_id"] for e in v.entities}
        self.assertIn("REQ-01", got)
        self.assertIn("REQ-02", got)
        self.assertIn("BOD-A", got)
        self.assertNotIn("BOD-B", got)
        # no candidate at all
        pre = DesignState(run_id="pre")
        self.add(pre, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        v2 = build_consumer_view("s02", pre, self.c, self.responsibility(
            "s02", self.premise("full_requirements", ["source_requirement"],
                                cv.DESIGN_WIDE)))
        self.assertIn("REQ-1", {e["entity_id"] for e in v2.entities})
        # `s05` was an unknown consumer until it was declared; `s03` still is,
        # because it names an owner rather than a producing responsibility.
        for unknown in ("s03", "s04"):
            with self.assertRaises(cv.UnknownConsumer):
                build_consumer_view(unknown, pre, self.c, self.resp)
