"""Two questions that used to be one act.

    CAN THIS DESIGN WORK?      candidate-local, preference-blind, no winner
    WHICH WORKING DESIGN?      comparison, preferences, advice, a human

The `gate` responsibility asked both and answered them together, which is how a
preference could reach a feasibility judgement: nothing in that shape could say
that a four-bar which works is not less feasible than a hinge which works. And
because `gate` was a responsibility with no entry in the ownership matrix, its
one authoritative output was attributed to the nearest stage - so s04, which
sizes bodies and sweeps them, owned the decision about which candidate wins.

S7-A freezes the authority. These are the properties that must hold before any
of it is built, and the preference-isolation one is checked against the REAL
ConsumerView rather than against prose, because that is the only form of the
claim that cannot be satisfied by an instruction.
"""
from __future__ import annotations

import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    selection_gate_check)
from ver3.assy_v3.state.design_state import (Contracts, ContractError,  # noqa: E402
                                             DesignState)
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.assy_v3.view.boundary import responsibility_contract          # noqa: E402

PRE_SELECTION = ("s01", "s02", "s03a", "s03b", "s04a", "s04b", "feasibility")


class _Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.resp = responsibility_contract()
        cls.ds = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.matrix = _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")

    def families(self):
        f = dict(self.ds["entity_families"])
        f.update(self.ds["assurance_families"])
        return f


# =====================================================================
# The split itself
# =====================================================================
class TestTheSplit(_Base):

    def test_the_gate_no_longer_exists_as_one_responsibility(self):
        self.assertNotIn("gate", self.resp["stages"])
        self.assertIn("feasibility", self.resp["stages"])
        self.assertIn("selection", self.resp["stages"])

    def test_feasibility_may_not_author_a_decision(self):
        outputs = self.resp["stages"]["feasibility"]["permitted_output_semantics"]
        self.assertNotIn("SelectionDecision", outputs)
        self.assertEqual(["MechanicalFeasibilityAssessment",
                          "HardRequirementCompliance", "UnresolvedDecision"],
                         outputs)

    def test_only_selection_may(self):
        declaring = [sid for sid, spec in self.resp["stages"].items()
                     if "SelectionDecision" in (spec.get("permitted_output_semantics") or [])]
        self.assertEqual(["selection"], declaring)

    def test_selection_decision_is_no_longer_s04s(self):
        """It was s04's because `gate` had no ownership entry at all, so the one
        family it authored was attributed to the nearest stage."""
        self.assertEqual("selection", self.families()["SelectionDecision"]["owned_by"])
        self.assertNotIn("SelectionDecision", self.matrix["stages"]["s04"]["owns"])
        entries = self.matrix["responsibilities"]["entries"]
        self.assertIn("SelectionDecision", entries["selection"]["owns"])

    def test_the_write_boundary_enforces_it(self):
        """Not a table a reader consults: `may_create` refuses."""
        self.assertFalse(self.c.may_create("s04", "SelectionDecision"))
        self.assertTrue(self.c.may_create("selection", "SelectionDecision"))
        self.assertFalse(self.c.may_create("selection", "MechanicalFeasibilityAssessment"))
        self.assertTrue(self.c.may_create("feasibility", "MechanicalFeasibilityAssessment"))

    def test_a_responsibility_has_a_position(self):
        """`gate` had none, which is why an ordering check could not say whether
        a consumer preceded its owner."""
        for name in ("feasibility", "selection"):
            self.assertEqual("s04",
                             self.matrix["responsibilities"]["entries"][name]["runs_after"])


# =====================================================================
# F11 - preference isolation, against the real view
# =====================================================================
class TestPreferenceIsolation(_fixtures.StateBuilder, _Base):

    def world(self):
        """A design with a standing SelectionProfile in it, and candidates."""
        s = DesignState(run_id="pref")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-1")
        self.add(s, "s01", "Scenario", "SCN-1", actors=["ACT-1"])
        self.add(s, "s02", "Candidate", "CND-A")
        self.add(s, "s02", "Candidate", "CND-B")
        self.add(s, "selection", "SelectionProfile", "SPF-1",
                 profile_version="v1", source_hash="deadbeef",
                 criteria={"part_count": {"objective": "MINIMIZE",
                                          "priority": "HIGH"}})
        return s

    def test_F11_no_pre_selection_view_can_contain_a_profile(self):
        s = self.world()
        self.assertTrue(s.family("SelectionProfile"), "the probe is not probing")
        for sid in PRE_SELECTION:
            view = cv.build_consumer_view(
                sid, s, self.c, self.resp,
                invocation=cv.InvocationContext(branch="CND-A"))
            self.assertNotIn("SelectionProfile", view.payload(),
                             "%s can see what the user prefers" % sid)

    def test_F11b_the_isolation_is_structural_not_instructed(self):
        """No pre-selection responsibility declares the role, so the derivation
        cannot select one. A stage told to ignore a preference has seen it."""
        for sid in PRE_SELECTION:
            roles = {r for pc in self.resp["stages"][sid]["required_reasoning_premise_classes"]
                     for r in pc["requires_semantics"]}
            self.assertNotIn("selection_preference", roles, sid)
        roles = {r for pc in self.resp["stages"]["selection"]["required_reasoning_premise_classes"]
                 for r in pc["requires_semantics"]}
        self.assertIn("selection_preference", roles)

    def test_F11c_feasibility_declares_the_prohibition_too(self):
        spec = self.resp["stages"]["feasibility"]
        self.assertIn("Any selection preference or SelectionProfile",
                      spec["prohibited_inputs"])
        self.assertTrue(spec["input_isolation_rule"].strip())

    def test_the_profile_role_is_carried_by_the_profile_and_nothing_else(self):
        carriers = [f for f, v in self.families().items()
                    if "selection_preference" in (v.get("semantic_roles") or [])]
        self.assertEqual(["SelectionProfile"], carriers)


# =====================================================================
# The semantics the later substeps must implement
# =====================================================================
class TestFrozenSemantics(_Base):

    def test_feasibility_is_three_state(self):
        fam = self.families()["MechanicalFeasibilityAssessment"]
        self.assertEqual(["FEASIBLE_FOR_SELECTION", "INFEASIBLE", "NOT_ESTABLISHED"],
                         fam["status"])

    def test_compliance_is_three_state_and_starts_unknown(self):
        fam = self.families()["HardRequirementCompliance"]
        self.assertEqual(["NOT_YET_EVALUABLE", "SATISFIED", "VIOLATED"], fam["status"])
        rules = " ".join(fam["rules"])
        self.assertIn("NOT_YET_EVALUABLE", rules)

    def test_missing_evidence_is_not_feasibility(self):
        rules = " ".join(self.families()["MechanicalFeasibilityAssessment"]["rules"])
        self.assertIn("MISSING EVIDENCE IS NOT FEASIBILITY", rules)
        self.assertIn("CANDIDATE-LOCAL", rules)

    def test_a_preference_can_never_make_a_candidate_ineligible(self):
        rules = " ".join(self.families()["SelectionProfile"]["rules"])
        self.assertIn("never a constraint", rules.lower())

    def test_a_metric_with_no_source_says_so(self):
        fam = self.families()["CandidateComparison"]
        self.assertEqual(["AVAILABLE", "NOT_AVAILABLE"], fam["availability"])
        self.assertIn("NO SILENT SURROGATE", " ".join(fam["rules"]))

    def test_an_advisory_may_not_author_authority(self):
        rules = " ".join(self.families()["SelectionAdvisory"]["rules"])
        for family in ("MechanicalFeasibilityAssessment", "HardRequirementCompliance",
                       "SelectionDecision"):
            self.assertIn(family, rules)
        self.assertEqual(["SUPPORTED_BY_STATE", "PLAUSIBLE_NOT_ESTABLISHED", "SPECULATIVE"],
                         self.families()["SelectionConcern"]["evidence_status"])

    def test_the_decision_separates_premises_from_considered(self):
        fam = self.families()["SelectionDecision"]
        self.assertIn("considered_advisories", fam["optional_fields"])
        self.assertIn("considered_concerns", fam["optional_fields"])
        for required in ("feasibility_assessments", "hard_requirement_results",
                         "selection_profile", "comparison", "human_decision"):
            self.assertIn(required, fam["required_fields"])
        self.assertIn("PREMISES vs CONSIDERED", " ".join(fam["rules"]))

    def test_the_ui_writes_an_input_and_not_a_decision(self):
        fam = self.families()["HumanDecisionInput"]
        self.assertEqual(["SELECT", "KEEP_UNRESOLVED", "REQUEST_MORE_EVIDENCE"],
                         fam["action"])
        self.assertIn("premise_digest", fam["required_fields"])
        self.assertIn("THE UI WRITES THIS AND NOTHING ELSE", " ".join(fam["rules"]))


# =====================================================================
# No second selection authority
# =====================================================================
class TestNoCompetingAuthority(_Base):

    def test_the_old_gate_check_authors_nothing(self):
        """It validates a decision that already exists. Left in place because
        relocating checks is S-8 / U-9's, and classified so it cannot be mistaken
        for the owner of selection."""
        import inspect
        src = inspect.getsource(selection_gate_check)
        for writing in ('Op("', ".apply(", "StagePatch("):
            self.assertNotIn(writing, src, "the gate check writes state")
        s = DesignState(run_id="gate")
        self.assertEqual([], selection_gate_check(s))

    def test_no_contract_places_selection_between_the_s04_passes(self):
        s04 = _paths.contract(__import__("os").path.join("stages", "S04_CONTRACT.yaml"))
        self.assertNotIn("between s04a and s04b", s04["selection_gate"]["position"])
        # The note QUOTES the retired claim while retiring it, which is how
        # every retirement in this corpus is written - so the assertion is about
        # the current claim, not about the words appearing.
        note = self.matrix["stages"]["s04"].get("pass_note", "")
        self.assertIn("is GONE", note)
        self.assertIn("selection follows s04", note)

    def test_the_profile_contract_keeps_the_two_inputs_apart(self):
        prof = _paths.contract("USER_DESIGN_PROFILE_CONTRACT.yaml")
        self.assertIn("design_constraints", prof)
        self.assertIn("selection_preferences", prof)
        self.assertIn("INVISIBLE UNTIL SELECTION",
                      prof["visibility"]["selection_preferences"])
        self.assertIn("DETERMINISTIC", prof["ingestion"]["design_constraints"])
        # The rule that stops absence becoming compliance, stated where the
        # ingester will read it.
        self.assertIn("NOT_YET_EVALUABLE", prof["design_constraints"]["evaluation_rule"])


# =====================================================================
# A1-A10 - the S7-A correction
# =====================================================================
class TestFeasibilityInputSufficiency(_Base):
    """A declared domain whose evidence the view cannot contain is a contract
    that cannot be satisfied - and S7-A declared four of them."""

    def probe(self):
        from .test_s6_spatial_lifecycle import TestDependencyGraph
        case = TestDependencyGraph(
            "test_L7_the_premise_set_is_exactly_what_reproduces_the_value")
        case.setUpClass()
        state, _ = case.spatial()
        return state, case

    def view(self, state, branch="CND-A"):
        return cv.build_consumer_view(
            "feasibility", state, self.c, self.resp,
            invocation=cv.InvocationContext(branch=branch))

    def test_A1_the_declared_motion_domains_have_their_evidence(self):
        state, _ = self.probe()
        for family in ("State", "Transition", "SweptVolume"):
            self.assertTrue(state.family(family), "the probe has no %s" % family)
        view = self.view(state)
        self.assertIs(cv.ViewStatus.VIEW_READY, view.status,
                      [a["requirement"] for a in view.assessment
                       if a["verdict"] != "SATISFIED"])
        payload = view.payload()
        for family in ("State", "Transition", "SweptVolume", "Joint",
                       "Configuration", "Envelope", "MobilityExpectation",
                       "ConstraintRelation", "PhysicalInteraction"):
            self.assertIn(family, payload,
                          "%s decides a declared domain and is not in the view"
                          % family)

    def test_A2_no_blanket_s04_dump(self):
        """A Witness is s04-owned and carries no semantic role at all, so it has
        no reason to be here - being s04's is not a reason."""
        state, case = self.probe()
        case.add(state, "s04", "Witness", "WIT-1", subject="BOD-G0A")
        self.assertTrue(state.family("Witness"))
        self.assertNotIn("Witness", self.view(state).payload())

    def test_A3_still_no_preference_leakage(self):
        state, case = self.probe()
        case.add(state, "selection", "SelectionProfile", "SPF-9",
                 profile_version="v1", source_hash="abc",
                 criteria={"part_count": {"objective": "MINIMIZE",
                                          "priority": "HIGH"}})
        self.assertTrue(state.family("SelectionProfile"))
        self.assertNotIn("SelectionProfile", self.view(state).payload())

    def test_the_three_motion_roles_are_not_disguised_whitelists(self):
        """Each names an engineering meaning, and only families that carry that
        meaning declare it."""
        fams = self.families()
        for role, carriers in (("realized_configuration", ["State"]),
                               ("motion_path", ["Transition"]),
                               ("motion_occupancy", ["SweptVolume"])):
            meaning = self.ds["semantic_role_vocabulary"][role]
            self.assertTrue(meaning.strip())
            for sid in self.resp["stages"]:
                self.assertNotIn(sid, meaning.lower(),
                                 "%s is defined by naming a stage" % role)
            declaring = [f for f, v in fams.items()
                         if role in (v.get("semantic_roles") or [])]
            self.assertEqual(carriers, declaring, role)


class TestOrderingAndRetirement(_Base):

    def test_A4_nothing_requires_a_decision_before_s04b(self):
        b = self.resp["stages"]["s04b"]
        for pc in b["required_reasoning_premise_classes"]:
            self.assertNotIn("selection_decision", pc["requires_semantics"])
            self.assertNotEqual("COMMITTED_BRANCH",
                                pc["instance_selection"]["population"])
        self.assertEqual([], b.get("premise_classes_pending_step") or [],
                         "a rule that would create SelectionDecision -> s04b is "
                         "still waiting to be activated")
        retired = {c["class"]: c for c in b.get("retired_premise_classes") or []}
        self.assertIn("selection_decision", retired)
        self.assertIn("CIRCULAR", retired["selection_decision"]["why_retired"])

    def test_A4b_nothing_live_is_staged_for_activation(self):
        """Structural, not a substring scan: the retirement record QUOTES what
        the rule used to say, `activated_by` and all, which is how every
        retirement in this corpus is written. What must not exist is a LIVE
        declaration waiting to be switched on."""
        for sid, spec in self.resp["stages"].items():
            self.assertEqual([], spec.get("premise_classes_pending_step") or [],
                             "%s stages a premise for activation" % sid)
            for retired in spec.get("retired_premise_classes") or []:
                self.assertIn("retired_by", retired)
                self.assertNotIn("activated_by", retired,
                                 "a retired class still declares its activation "
                                 "step outside the record of what it used to say")
                self.assertIn("activated_by", retired["was"])

    def test_A5_the_order_resolves_to_s04_feasibility_selection(self):
        entries = self.matrix["responsibilities"]["entries"]
        self.assertEqual("s04", entries["feasibility"]["runs_after"])
        self.assertIsNone(entries["feasibility"].get("runs_after_responsibility"))
        self.assertEqual("s04", entries["selection"]["runs_after"])
        self.assertEqual("feasibility",
                         entries["selection"]["runs_after_responsibility"])
        # Resolved, rather than left to the incidental fact that one requires the
        # other's output.
        order, seen = [], dict(entries)
        for name in ("feasibility", "selection"):
            after = seen[name].get("runs_after_responsibility")
            order.append((after or seen[name]["runs_after"], name))
        self.assertEqual([("s04", "feasibility"), ("feasibility", "selection")],
                         order)


class TestHardConstraintVisibility(_fixtures.StateBuilder, _Base):

    def world(self, with_constraint=True):
        s = DesignState(run_id="hard")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-1")
        self.add(s, "s01", "Scenario", "SCN-1", actors=["ACT-1"])
        self.add(s, "s02", "Candidate", "CND-A")
        if with_constraint:
            self.add(s, "s01", "DesignConstraint", "DSC-1",
                     kind="MATERIAL_CLASS_ONLY",
                     statement="every manufactured part must be plastic",
                     source="user_design_profile", evaluability="MACHINE_EVALUABLE",
                     parameters={"material_class": "PLASTIC"},
                     blocks_selection=True)
        return s

    def test_A6_a_structured_constraint_is_created_by_its_early_owner(self):
        """Deterministic ingestion: the field is carried, not paraphrased."""
        s = self.world()
        rec = s.entities["DSC-1"]
        self.assertEqual("s01", rec["_created_by"])
        self.assertEqual({"material_class": "PLASTIC"}, rec["parameters"])
        self.assertEqual("MACHINE_EVALUABLE", rec["evaluability"])
        self.assertTrue(self.c.may_create("s01", "DesignConstraint"))
        self.assertFalse(self.c.may_create("s02", "DesignConstraint"))

    def test_A7_visibility_is_selective_not_global(self):
        """It exists from s01 and appears only where the reasoning needs it."""
        s = self.world()
        declaring = [sid for sid, spec in self.resp["stages"].items()
                     if any("design_constraint" in pc["requires_semantics"]
                            for pc in spec["required_reasoning_premise_classes"])]
        self.assertEqual(["feasibility"], declaring)
        for sid in ("s02", "s03a", "s03b", "s04a"):
            view = cv.build_consumer_view(
                sid, s, self.c, self.resp,
                invocation=cv.InvocationContext(branch="CND-A"))
            self.assertNotIn("DesignConstraint", view.payload(),
                             "%s received a hard requirement it never asked for"
                             % sid)

    def test_A7b_a_consumer_that_declares_it_does_receive_it(self):
        from .test_s6_spatial_lifecycle import TestDependencyGraph
        case = TestDependencyGraph(
            "test_L7_the_premise_set_is_exactly_what_reproduces_the_value")
        case.setUpClass()
        state, _ = case.spatial()
        case.add(state, "s01", "DesignConstraint", "DSC-2",
                 kind="MATERIAL_CLASS_ONLY", statement="plastic only",
                 source="user_design_profile", evaluability="MACHINE_EVALUABLE")
        view = cv.build_consumer_view(
            "feasibility", state, self.c, self.resp,
            invocation=cv.InvocationContext(branch="CND-A"))
        self.assertIn("DesignConstraint", view.payload())

    def test_A7c_a_design_with_no_hard_requirement_is_not_blocked(self):
        """The compliance output is produced PER constraint. None declared means
        none produced, which is a complete answer - it used to leave the
        feasibility view UPSTREAM_INSUFFICIENCY."""
        spec = self.resp["stages"]["feasibility"]
        self.assertIn("HardRequirementCompliance", spec["conditional_outputs"])
        self.assertEqual("DesignConstraint",
                         spec["conditional_outputs"]["HardRequirementCompliance"]["produced_per"])

    def test_A8_carrying_is_not_inventing(self):
        s01 = self.resp["stages"]["s01"]
        self.assertIn("DesignConstraint", s01["permitted_output_semantics"])
        prohibited = " ".join(s01["prohibited_decisions"])
        self.assertIn("INVENTING", prohibited)
        self.assertIn("the source did not state", prohibited)
        self.assertIn("CARRYING one the source states", s01["carrying_versus_inventing"])
        # And the contract that governs ingestion says the same thing.
        prof = _paths.contract("USER_DESIGN_PROFILE_CONTRACT.yaml")
        self.assertIn("DETERMINISTIC", prof["ingestion"]["design_constraints"])
        self.assertIn("EXISTENCE IS NOT VISIBILITY",
                      prof["visibility"]["design_constraints"])
        self.assertIn("MUST NOT", prof["visibility"]["the_asymmetry"])


class TestReviewedConcernProvenance(_Base):

    def test_A9_a_human_can_record_both_kinds_of_reviewed_material(self):
        hdi = self.families()["HumanDecisionInput"]
        specs = hdi["field_semantics"]
        self.assertEqual("SelectionAdvisory", specs["reviewed_advisories"]["target"])
        self.assertEqual("SelectionConcern", specs["reviewed_concerns"]["target"])
        for f in ("reviewed_advisories", "reviewed_concerns"):
            self.assertIn(f, hdi["optional_fields"])
            self.assertEqual("many", specs[f]["cardinality"])

    def test_A10_reviewing_something_does_not_make_it_a_premise(self):
        sel = self.families()["SelectionDecision"]
        for considered in ("considered_advisories", "considered_concerns"):
            self.assertIn(considered, sel["optional_fields"])
            self.assertNotIn(considered, sel["required_fields"])
        # The premises are the factual ones, and they are the required set.
        for premise in ("feasibility_assessments", "hard_requirement_results",
                        "comparison", "selection_profile"):
            self.assertIn(premise, sel["required_fields"])
        rules = " ".join(sel["rules"])
        self.assertIn("PREMISES vs CONSIDERED", rules)
        self.assertIn("rewording it invalidates nothing", rules)


# =====================================================================
# The corpus sweep, as a standing test
# =====================================================================
class TestNoResidueOfTheOldArchitecture(_Base):
    """Every CURRENT claim in the canonical corpus agrees with

        s04a -> s04b -> feasibility -> selection

    Written as a scanner rather than as a list of known lines, because the last
    three passes each found residue nobody had listed: a claim in a file nobody
    thought to look at is exactly the failure this catches.
    """

    #: Keys whose VALUE is a record of what something used to say. A retirement
    #: that could not quote the claim it retired would be a deletion, and this
    #: corpus writes retirements the other way on purpose.
    HISTORICAL_KEYS = frozenset((
        "was", "why_retired", "retired_by", "superseded", "superseded_by",
        "why_it_lingered", "why_it_took_two_passes", "why_recorded_historical",
        "historical_data", "s1_note", "s7_note", "migration_status",
        "not_a_refusal", "never_a_declaration", "why_not_a_whitelist",
        "note_on_window2_growth", "pass_note", "why", "note", "rule",
        "granularity_rule", "runs_after_rule", "input_isolation_rule",
        "refinement_lifecycle", "conditional_outputs", "open_question",
        "carrying_versus_inventing", "duplicates_note", "consumer_note",
        "why_it_is_here", "position", "the_asymmetry", "visibility",
        "engagement_site_status", "retired_shapes", "retired_premise_classes",
        "retired_disposition_values", "superseded_legacy_producers",
        "not_owned_here", "later_owned", "declared_by", "meaning", "purpose"))

    FILES = ("DESIGN_STATE_CONTRACT.yaml", "STAGE_RESPONSIBILITY_CONTRACT.yaml",
             "STAGE_OWNERSHIP_MATRIX.yaml", "ENTITY_FAMILY_AUDIT.yaml",
             "USER_DESIGN_PROFILE_CONTRACT.yaml",
             "stages/S01_CONTRACT.yaml", "stages/S04_CONTRACT.yaml")

    #: Phrases that can only be a CURRENT claim of the retired architecture.
    #: Deliberately narrow: "gate" alone is a legitimate word - the progression
    #: contract uses it for a stage-freeze - so only the shapes that mean THIS
    #: gate are listed.
    BANNED = (
        "gate sits between",
        "selection gate sits",
        "before the gate",
        "at the gate",
        "the gate that acts on it",
        "the gate that would act on it",
        "feasibility gate",
        "if the gate produces",
    )

    def current_strings(self, node, key=None, path=""):
        """Every string that is a CURRENT claim, with where it came from."""
        if isinstance(node, dict):
            for k, v in node.items():
                if k in self.HISTORICAL_KEYS:
                    continue
                for item in self.current_strings(v, k, "%s.%s" % (path, k)):
                    yield item
        elif isinstance(node, list):
            for i, v in enumerate(node):
                for item in self.current_strings(v, key, "%s[%d]" % (path, i)):
                    yield item
        elif isinstance(node, str):
            yield path, node

    def test_no_current_claim_of_the_retired_gate_architecture(self):
        import os
        found = []
        for name in self.FILES:
            doc = _paths.contract(os.path.join(*name.split("/")))
            for where, text in self.current_strings(doc, path=name):
                low = text.lower()
                for phrase in self.BANNED:
                    if phrase in low:
                        found.append("%s: %r ... %s" % (where, phrase, text[:90]))
        self.assertEqual([], found, "\n".join(found))

    def test_no_current_claim_that_s04_selects(self):
        """The matrix's `responsibilities` block names it because `selection`
        owns it, which is the point - so only the STAGE projection is scanned."""
        import os
        found = []
        for name, doc in (
                ("stages/S04_CONTRACT.yaml",
                 _paths.contract(os.path.join("stages", "S04_CONTRACT.yaml"))),
                ("STAGE_OWNERSHIP_MATRIX.stages",
                 _paths.contract("STAGE_OWNERSHIP_MATRIX.yaml")["stages"])):
            for where, text in self.current_strings(doc, path=name):
                if "selectiondecision" in text.lower().replace(" ", ""):
                    found.append("%s: %s" % (where, text[:90]))
        self.assertEqual([], found, "\n".join(found))

    def test_s01_prohibits_invention_and_not_recording(self):
        import os
        s01 = _paths.contract(os.path.join("stages", "S01_CONTRACT.yaml"))
        for entry in s01["prohibited_decisions"]:
            what = entry["what"].lower()
            if "material" in what or "dimension" in what or "mechanism" in what:
                self.assertTrue(
                    "invent" in what or "did not state" in what,
                    "a blanket ban would forbid recording a user who SAID it: %r"
                    % entry["what"])

    def test_s01_projections_agree_about_the_family_it_owns(self):
        import os
        s01 = _paths.contract(os.path.join("stages", "S01_CONTRACT.yaml"))
        self.assertIn("DesignConstraint", s01["owned_decisions"]["creates"])
        self.assertIn("DesignConstraint", s01["structured_outputs"])
        self.assertIn("DesignConstraint",
                      self.resp["stages"]["s01"]["permitted_output_semantics"])
        self.assertIn("DesignConstraint", self.matrix["stages"]["s01"]["owns"])
        self.assertEqual("s01", self.families()["DesignConstraint"]["owned_by"])
        self.assertEqual("s01", _paths.contract("ENTITY_FAMILY_AUDIT.yaml")
                         ["families"]["DesignConstraint"]["owning_stage"])

    def test_every_projection_agrees_about_who_owns_the_decision(self):
        self.assertEqual("selection", self.families()["SelectionDecision"]["owned_by"])
        self.assertEqual("selection", _paths.contract("ENTITY_FAMILY_AUDIT.yaml")
                         ["families"]["SelectionDecision"]["owning_stage"])
        self.assertIn("SelectionDecision",
                      self.matrix["responsibilities"]["entries"]["selection"]["owns"])
        for sid, spec in self.matrix["stages"].items():
            self.assertNotIn("SelectionDecision", spec.get("owns") or [], sid)


if __name__ == "__main__":
    unittest.main()
