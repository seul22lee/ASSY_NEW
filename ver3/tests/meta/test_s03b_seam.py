"""The s03b producer, the contract and the deterministic checks, made to agree.

Six issues were alleged against this seam. Each is reproduced here against the
real six-branch state before it is repaired, and each test states the engineering
fact it is defending rather than the code path it walks.

  1 MOBILITY HAS ONE AUTHOR. A Joint declares its free DOF. The derivation used
    to ignore that and re-infer freedom from joint_type and axis_direction, which
    for a COMPLIANT joint meant a TRANSLATION along the axis - so every flexure
    hinge in the accepted corpus, each declaring a ROTATION about its axis, had
    its own canonical statement overruled by a rule of thumb. Two answers to one
    question is the defect; the declared one wins, and the type/axis semantics
    become a CONSISTENCY CHECK on the ordinary joint classes instead.

  2 NONE IS NOT A RETENTION STRATEGY. `termination_strategy` is a required field
    whose permitted values include NONE, and the retention check tested it for
    truthiness - so a body the design says is held, declaring NONE, passed the
    check that exists to ask how it is held.

  3 EVIDENCE MUST REACH A CELL. The mobility grid is groups x configurations x
    DOF. A relation blocking "ROLL", or naming a configuration of another branch,
    or an irrelevance claim naming a group that does not exist, disposes nothing -
    and used to satisfy completeness while disposing nothing.

  4 DISCHARGE IS ABOUT THE EFFECT. An interaction discharged a physical effect
    obligation by CITING it, whatever effect it claimed to produce. The assurance
    layer already compared the two; the stage that authors the interaction did
    not, so a mismatch committed and was found a layer later.

  5 A BRANCH MAY NOT AUTHOR INTO ANOTHER BRANCH. Every candidate's topology lives
    in one DesignState, so an id from another branch resolves. The contract
    already says which references are drawn from the invocation branch; nothing
    read that declaration when the reference was WRITTEN. `LoadPath.candidate`
    was worse: it was taken from the response, though the invocation already
    determines it.

  6 THE VIEW'S POPULATIONS ARE THE CONTRACT'S ROLES. A readiness report counted
    "topology relations" by a hand-written family list and reported zero, while
    the contract says topology_relation is Joint and Interface.

No compatibility layer, no repaired response, no weakened guard: every negative
below is a response the seam must refuse.
"""
import copy
import re
import time
import unittest

from . import _branches

from ver3.assy_v3.providers.interfaces import (ExecutionStatus, GenerationResponse,
                                               GenerationResult)
from ver3.assy_v3.stages.s03_topology_and_mobility import (
    DOF_NAMES, S03BMobilityAndAssembly, free_dof)
from ver3.assy_v3.view import InvocationContext

import json


class _Canned:
    """A provider that returns one prepared response. No network, no retry."""

    def __init__(self, response):
        self.response, self.calls = response, 0

    def capabilities(self):
        return {"supports_json": True}

    def generate(self, request, attempt_index=0):
        self.calls += 1
        started = time.time()
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=json.dumps(self.response),
                                        finish_reason="stop", truncated=False,
                                        input_tokens=0, output_tokens=0,
                                        served_model_id="canned"),
            attempt_index=attempt_index, started_at=started, ended_at=started,
            from_cache=False)


def baseline(payload, candidate_id):
    """A complete, contract-shaped s03b response composed FROM THE VIEW.

    Built from the branch's own topology and the design-wide demands, so it is a
    response the seam should accept for any of the six candidates. Every negative
    case below is this response with one fact changed.
    """
    groups = [g["entity_id"] for g in payload.get("RigidGroup") or []]
    configs = [c["entity_id"] for c in payload.get("Configuration") or []]
    bodies = [b["entity_id"] for b in payload.get("Body") or []]
    ifaces = [i["entity_id"] for i in payload.get("Interface") or []]
    peos = payload.get("PhysicalEffectObligation") or []
    loads = payload.get("LoadCase") or []

    interactions = [
        {"id": "PHI-%04d" % (n + 1), "groups": groups[:2],
         # THE OBLIGATION'S OWN EFFECT. Discharge is a claim about the effect,
         # not about the citation.
         "effect": p.get("effect"), "discharges_effect": p["entity_id"],
         "configurations": configs[:1]}
        for n, p in enumerate(peos)]
    relations = [{"id": "CRL-0001", "retained_group": groups[-1],
                  "blocked_dofs": ["TX", "TY", "TZ"], "configurations": configs,
                  "driver": "KINEMATIC_NECESSITY", "blocked_direction": "+Z",
                  "provider_body": bodies[0],
                  "defeat_specification": "a pull that separates the two bodies"}]
    paths = [{"id": "LDP-%04d" % (n + 1), "load_case": l["entity_id"],
              "candidate": candidate_id, "ordered_hops": ifaces[:2],
              "terminates_at": l.get("reacted_at_site")}
             for n, l in enumerate(loads)]
    steps = [{"id": "ASY-%04d" % (n + 1), "order_index": n + 1, "body": b,
              "access_side": "+Z", "activates": ifaces[:1],
              "termination_strategy": "LATER_BODY_COVER", "path_kind": "RIGID",
              "depends_on": []}
             for n, b in enumerate(bodies)]
    return {"irrelevance": [], "physical_interactions": interactions,
            "constraint_relations": relations, "load_paths": paths,
            "assembly_steps": steps, "unresolved": []}


class _Seam(unittest.TestCase):
    """One six-branch state per class; each test invokes s03b against it."""

    @classmethod
    def setUpClass(cls):
        cls.state = _branches.six_branch_state()
        cls.stage = S03BMobilityAndAssembly()
        cls.views = {}
        for rec in sorted(cls.state.family("Candidate"), key=lambda r: r["entity_id"]):
            cid = rec["entity_id"]
            cls.views[cid] = cls.stage.consumer_view(
                cls.state, InvocationContext(branch=cid))

    def payload(self, cid):
        return self.views[cid].payload()

    def baseline(self, cid):
        return baseline(self.payload(cid), cid)

    def invoke(self, cid, response, apply_it=False):
        """The real invocation path, with the response canned.

        Returns what a caller can act on: the status, what canonical validation
        said, and what the stage declared incomplete. Those are three different
        answers and the tests below distinguish them.
        """
        provider = _Canned(response)
        outcome = self.stage.invoke(provider, self.state, self.state.run_id,
                                    {"candidate": _branches.candidate(self.state, cid)},
                                    invocation=InvocationContext(branch=cid))
        self.assertEqual(1, provider.calls)
        problems = (self.state.validate(outcome.patch) if outcome.patch is not None
                    else list(outcome.problems))
        if apply_it and not problems:
            self.state.apply(outcome.patch)
        return {"status": outcome.execution_status.value, "patch": outcome.patch,
                "problems": problems, "incomplete": list(outcome.declared_incompleteness),
                "refused": bool(problems) or bool(outcome.declared_incompleteness)}

    def cells(self, patch, group=None, dof=None, configuration=None):
        out = []
        for op in patch.operations:
            if op.entity_type != "MobilityExpectation":
                continue
            for row in op.fields.get("dispositions") or []:
                if group and row.get("rigid_group") != group:
                    continue
                if dof and row.get("dof") != dof:
                    continue
                if configuration and row.get("configuration") != configuration:
                    continue
                out.append(row)
        return out


# ======================================================================
# 0. The premise these tests stand on
# ======================================================================

class TestTheSixBranchesAreThere(_Seam):

    def test_all_six_s03b_consumer_views_are_ready(self):
        for cid, view in sorted(self.views.items()):
            with self.subTest(candidate=cid):
                self.assertEqual("VIEW_READY", view.status.value)

    def test_each_view_carries_exactly_its_own_candidate(self):
        for cid in sorted(self.views):
            with self.subTest(candidate=cid):
                seen = [c["entity_id"] for c in self.payload(cid).get("Candidate") or []]
                self.assertEqual([cid], seen)

    def test_no_view_carries_another_branch_topology(self):
        for cid in sorted(self.views):
            others = set(self.views) - {cid}
            for fam in ("Body", "RigidGroup", "Joint", "Interface", "Configuration"):
                for rec in self.payload(cid).get(fam) or []:
                    premises = set(rec.get("_premises") or [])
                    self.assertFalse(premises & others,
                                     "%s sees %s of %s" % (cid, rec["entity_id"], premises))

    def test_the_baseline_response_commits_for_a_revolute_candidate(self):
        r = self.invoke("CND-0003", self.baseline("CND-0003"))
        self.assertEqual([], r["problems"])
        self.assertEqual([], r["incomplete"])

    def test_the_baseline_response_commits_for_a_compliant_candidate(self):
        r = self.invoke("CND-0006", self.baseline("CND-0006"))
        self.assertEqual([], r["problems"])
        self.assertEqual([], r["incomplete"])


# ======================================================================
# 1. Mobility has one author
# ======================================================================

class TestMobilityHasOneAuthor(_Seam):

    def compliant_joint(self, cid):
        for j in self.payload(cid).get("Joint") or []:
            if j.get("joint_type") == "COMPLIANT":
                return j
        raise AssertionError("%s has no compliant joint" % cid)

    def test_the_accepted_corpus_declares_rotational_compliance(self):
        """The premise of this whole section: the live responses say RY/RZ where
        the axis rule says TY/TZ. If they agreed there would be nothing to fix."""
        seen = 0
        for cid in sorted(self.views):
            for j in self.payload(cid).get("Joint") or []:
                if j.get("joint_type") != "COMPLIANT":
                    continue
                seen += 1
                self.assertTrue(j.get("dof"), "%s declares no dof" % j["entity_id"])
                self.assertNotEqual(set(j["dof"]),
                                    free_dof("COMPLIANT", j.get("axis_direction")))
        self.assertGreaterEqual(seen, 3, "the corpus lost its compliant joints")

    def test_a_compliant_joint_keeps_the_dof_it_declares(self):
        for cid in ("CND-0001", "CND-0002", "CND-0006"):
            with self.subTest(candidate=cid):
                joint = self.compliant_joint(cid)
                r = self.invoke(cid, self.baseline(cid))
                self.assertEqual([], r["problems"])
                free = self.cells(r["patch"], group=joint["child_group"])
                intended = {row["dof"] for row in free
                            if row.get("disposition") == "INTENDED"
                            and row.get("by_joint") == joint["entity_id"]}
                self.assertEqual(set(joint["dof"]), intended,
                                 "%s declares %s; the grid says %s"
                                 % (joint["entity_id"], joint["dof"], sorted(intended)))

    def test_no_cell_is_freed_by_a_dof_no_joint_declared(self):
        """The other half: not merely that RY is INTENDED, but that TY is not."""
        for cid in ("CND-0001", "CND-0006"):
            with self.subTest(candidate=cid):
                joint = self.compliant_joint(cid)
                r = self.invoke(cid, self.baseline(cid))
                for row in self.cells(r["patch"]):
                    if row.get("by_joint") != joint["entity_id"]:
                        continue
                    self.assertIn(row["dof"], joint["dof"],
                                  "the grid credits %s with %s, which it does not "
                                  "declare" % (joint["entity_id"], row["dof"]))

    def test_an_ordinary_joint_whose_dof_contradicts_its_type_is_detected(self):
        """REVOLUTE about +Z frees RZ. A joint saying TZ is not a second opinion
        about kinematics, it is a mistake, and only a check can say so."""
        from ver3.assy_v3.stages.s03_topology_and_mobility import joint_dof_consistency_check
        bad = {"entity_id": "JNT-BAD", "joint_type": "REVOLUTE",
               "axis_direction": "+Z", "dof": ["TZ"], "parent_group": "RGP-0001",
               "child_group": "RGP-0002", "frame_ids": ["FRM-1"]}
        problems = joint_dof_consistency_check(_State([bad]))
        self.assertTrue(any("JNT-BAD" in p for p in problems), problems)

    def test_the_accepted_ordinary_joints_are_all_consistent(self):
        from ver3.assy_v3.stages.s03_topology_and_mobility import joint_dof_consistency_check
        self.assertEqual([], joint_dof_consistency_check(self.state))

    def test_a_compliant_joint_is_not_judged_by_the_axis_rule(self):
        """Compliance couples an axis to a deflection in a way this stage does not
        decide, so the declared DOF is preserved rather than checked against the
        translation the axis rule would infer."""
        from ver3.assy_v3.stages.s03_topology_and_mobility import joint_dof_consistency_check
        rotational = {"entity_id": "JNT-FLEX", "joint_type": "COMPLIANT",
                      "axis_direction": "+Y", "dof": ["RY"],
                      "parent_group": "RGP-0001", "child_group": "RGP-0002",
                      "frame_ids": ["FRM-1"]}
        self.assertEqual([], joint_dof_consistency_check(_State([rotational])))

    def test_a_compliant_joint_declaring_no_dof_is_detected(self):
        from ver3.assy_v3.stages.s03_topology_and_mobility import joint_dof_consistency_check
        empty = {"entity_id": "JNT-NIL", "joint_type": "COMPLIANT",
                 "axis_direction": "+Y", "dof": [], "parent_group": "RGP-0001",
                 "child_group": "RGP-0002", "frame_ids": ["FRM-1"]}
        self.assertTrue(joint_dof_consistency_check(_State([empty])))


class _State:
    """A read-only stand-in exposing `family` for the joint checks.

    The checker is exercised on records the write boundary would refuse, which is
    exactly what a checker must handle: a check reachable only through a gate
    that already rejects its input is a check nobody can run.
    """

    def __init__(self, joints):
        self._joints = list(joints)

    def family(self, name):
        return list(self._joints) if name == "Joint" else []

    def standing(self, name):
        return self.family(name)


# ======================================================================
# 2. NONE is not a retention strategy
# ======================================================================

class TestTerminationSemantics(_Seam):

    def retained_body(self, cid, response):
        """A body the design says is held: some group of it is BLOCKED_BY."""
        r = self.invoke(cid, response)
        groups = {g["entity_id"]: g.get("body")
                  for g in self.payload(cid).get("RigidGroup") or []}
        for row in self.cells(r["patch"]):
            if row.get("disposition") == "BLOCKED_BY":
                return groups.get(row["rigid_group"]), r
        raise AssertionError("nothing is retained in %s" % cid)

    def test_a_retained_body_declaring_NONE_is_reported(self):
        from ver3.assy_v3.stages.s03_topology_and_mobility import retention_check
        cid = "CND-0003"
        body, first = self.retained_body(cid, self.baseline(cid))
        response = copy.deepcopy(self.baseline(cid))
        for step in response["assembly_steps"]:
            if step["body"] == body:
                step["termination_strategy"] = "NONE"
        r = self.invoke(cid, response)
        self.assertEqual([], r["problems"], "the shape is valid; the semantics are not")
        state = _StateOf(r["patch"], self.payload(cid))
        self.assertTrue(any("RETAINED_BODY_WITHOUT_TERMINATION" in p and body in p
                            for p in retention_check(state)),
                        retention_check(state))

    def test_NONE_is_legitimate_for_a_body_nothing_retains(self):
        from ver3.assy_v3.stages.s03_topology_and_mobility import retention_check
        cid = "CND-0003"
        retained, _ = self.retained_body(cid, self.baseline(cid))
        response = copy.deepcopy(self.baseline(cid))
        free = [s for s in response["assembly_steps"] if s["body"] != retained]
        self.assertTrue(free, "every body is retained here; pick another candidate")
        for step in free:
            step["termination_strategy"] = "NONE"
        r = self.invoke(cid, response)
        state = _StateOf(r["patch"], self.payload(cid))
        for problem in retention_check(state):
            for step in free:
                self.assertNotIn(step["body"], problem)

    def test_the_permitted_values_agree_across_prompt_contract_and_runtime(self):
        from ver3.assy_v3.stages.s03_topology_and_mobility import (S03B_PROMPT,
                                                                   TERMINATION_STRATEGIES)
        for value in TERMINATION_STRATEGIES:
            self.assertIn(value, S03B_PROMPT.replace("{terminations}",
                                                     " | ".join(TERMINATION_STRATEGIES)))
        self.assertIn("NONE", TERMINATION_STRATEGIES)


class _StateOf:
    """A state view over one patch plus the branch's own topology."""

    def __init__(self, patch, payload):
        self.records = {}
        for fam, rows in (payload or {}).items():
            self.records[fam] = [dict(r) for r in rows]
        for op in (patch.operations if patch is not None else []):
            rec = dict(op.fields or {})
            rec["entity_id"] = op.entity_id
            self.records.setdefault(op.entity_type, []).append(rec)

    def family(self, name):
        return list(self.records.get(name) or [])

    def standing(self, name):
        return self.family(name)


# ======================================================================
# 3. Evidence must reach a cell
# ======================================================================

class TestMobilityEvidenceReachesACell(_Seam):

    def test_blocked_dofs_outside_the_canonical_vocabulary_is_refused(self):
        cid = "CND-0003"
        response = copy.deepcopy(self.baseline(cid))
        response["constraint_relations"][0]["blocked_dofs"] = ["ROLL"]
        r = self.invoke(cid, response)
        self.assertTrue(r["refused"], "a relation blocking ROLL disposed nothing "
                                      "and nothing said so")
        self.assertTrue(any("ROLL" in p for p in r["problems"] + r["incomplete"]),
                        r["problems"] + r["incomplete"])

    def test_a_relation_naming_a_configuration_of_another_branch_is_refused(self):
        cid, other = "CND-0003", "CND-0004"
        foreign = [c["entity_id"] for c in self.payload(other).get("Configuration") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["constraint_relations"][0]["configurations"] = foreign[:1]
        r = self.invoke(cid, response)
        self.assertTrue(r["refused"],
                        "a relation holding in another candidate's configuration "
                        "was accepted because the id resolves globally")

    def test_a_relation_naming_a_group_of_another_branch_is_refused(self):
        cid, other = "CND-0003", "CND-0004"
        foreign = [g["entity_id"] for g in self.payload(other).get("RigidGroup") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["constraint_relations"][0]["retained_group"] = foreign[0]
        r = self.invoke(cid, response)
        self.assertTrue(r["refused"])

    def test_an_irrelevance_claim_naming_an_unknown_group_is_refused(self):
        cid = "CND-0003"
        configs = [c["entity_id"] for c in self.payload(cid).get("Configuration") or []]
        scenario = (self.payload(cid).get("Scenario") or [{}])[0].get("entity_id")
        response = copy.deepcopy(self.baseline(cid))
        response["irrelevance"] = [{"rigid_group": "RGP-9999",
                                    "configuration": configs[0], "dof": ["TX"],
                                    "scenario": scenario}]
        r = self.invoke(cid, response)
        self.assertTrue(r["refused"], "an irrelevance claim about a group that does "
                                      "not exist made nothing irrelevant anywhere")

    def test_an_irrelevance_claim_naming_an_unknown_scenario_is_refused(self):
        cid = "CND-0003"
        groups = [g["entity_id"] for g in self.payload(cid).get("RigidGroup") or []]
        configs = [c["entity_id"] for c in self.payload(cid).get("Configuration") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["irrelevance"] = [{"rigid_group": groups[0],
                                    "configuration": configs[0], "dof": ["TX"],
                                    "scenario": "SCN-9999"}]
        self.assertTrue(self.invoke(cid, response)["refused"])

    def test_valid_evidence_still_produces_the_expected_cells(self):
        cid = "CND-0003"
        response = copy.deepcopy(self.baseline(cid))
        relation = response["constraint_relations"][0]
        r = self.invoke(cid, response)
        self.assertEqual([], r["problems"])
        self.assertEqual([], r["incomplete"])
        for cfg in relation["configurations"]:
            for dof in relation["blocked_dofs"]:
                rows = self.cells(r["patch"], group=relation["retained_group"],
                                  dof=dof, configuration=cfg)
                self.assertEqual(1, len(rows), (cfg, dof, rows))
                self.assertEqual("BLOCKED_BY", rows[0]["disposition"])
                self.assertEqual(relation["id"], rows[0]["constraint_relation"])

    def test_a_valid_irrelevance_claim_disposes_its_own_cell(self):
        cid = "CND-0003"
        payload = self.payload(cid)
        groups = [g["entity_id"] for g in payload.get("RigidGroup") or []]
        configs = [c["entity_id"] for c in payload.get("Configuration") or []]
        scenario = (payload.get("Scenario") or [{}])[0].get("entity_id")
        response = copy.deepcopy(self.baseline(cid))
        response["constraint_relations"][0]["blocked_dofs"] = ["TX", "TY"]
        response["irrelevance"] = [{"rigid_group": groups[0],
                                    "configuration": configs[0], "dof": ["RX"],
                                    "scenario": scenario}]
        r = self.invoke(cid, response)
        self.assertEqual([], r["problems"])
        rows = self.cells(r["patch"], group=groups[0], dof="RX",
                          configuration=configs[0])
        self.assertEqual(["IRRELEVANT_BECAUSE"], [x["disposition"] for x in rows])
        self.assertEqual(scenario, rows[0]["scenario"])

    def test_every_derived_dof_is_canonical_vocabulary(self):
        cid = "CND-0003"
        r = self.invoke(cid, self.baseline(cid))
        for row in self.cells(r["patch"]):
            self.assertIn(row["dof"], DOF_NAMES)


# ======================================================================
# 4. Discharge is about the effect
# ======================================================================

class TestPhysicalEffectDischarge(_Seam):

    def test_an_interaction_claiming_another_effect_does_not_discharge(self):
        cid = "CND-0003"
        response = copy.deepcopy(self.baseline(cid))
        target = response["physical_interactions"][0]
        peo = {p["entity_id"]: p for p in self.payload(cid).get("PhysicalEffectObligation") or []}
        required = peo[target["discharges_effect"]]["effect"]
        target["effect"] = next(e for e in ("TRANSMIT_FORCE", "CONTAIN", "METER")
                                if e != required)
        r = self.invoke(cid, response)
        self.assertTrue(r["refused"],
                        "an interaction producing %r was accepted as discharging an "
                        "obligation requiring %r" % (target["effect"], required))
        self.assertTrue(any(target["discharges_effect"] in p
                            for p in r["problems"] + r["incomplete"]))

    def test_a_matching_effect_discharges(self):
        cid = "CND-0003"
        r = self.invoke(cid, self.baseline(cid))
        self.assertEqual([], r["problems"])
        self.assertEqual([], r["incomplete"])

    def test_an_interaction_effect_outside_the_vocabulary_is_refused(self):
        cid = "CND-0003"
        response = copy.deepcopy(self.baseline(cid))
        response["physical_interactions"][0]["effect"] = "HOLD_TIGHT"
        self.assertTrue(self.invoke(cid, response)["refused"])

    def test_an_obligation_recorded_open_is_not_a_failure(self):
        """Saying an effect is not discharged is a real answer; only silence is not."""
        cid = "CND-0003"
        response = copy.deepcopy(self.baseline(cid))
        dropped = response["physical_interactions"].pop(0)
        response["unresolved"] = [{
            "id": "S3U-9001", "decision": "how this effect is produced",
            "why_open": "no principle has been chosen for it",
            "alternatives": [], "alternatives_kind": "FREE_TEXT",
            "kept_open_by": [], "blocks": [dropped["discharges_effect"]]}]
        r = self.invoke(cid, response)
        self.assertEqual([], r["problems"])
        self.assertEqual([], r["incomplete"])


# ======================================================================
# 5. A branch may not author into another branch
# ======================================================================

class TestBranchLocality(_Seam):

    def test_a_load_path_hopping_through_a_foreign_interface_is_refused(self):
        cid, other = "CND-0003", "CND-0005"
        foreign = [i["entity_id"] for i in self.payload(other).get("Interface") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["load_paths"][0]["ordered_hops"] = foreign[:1]
        r = self.invoke(cid, response)
        self.assertTrue(r["refused"], "a load path routed through another "
                                      "candidate's interface was accepted")

    def test_the_foreign_reference_is_refused_at_the_write_boundary(self):
        """Not merely reported: a CONTRACT_INCOMPLETE patch is still applicable,
        so a producer-level finding is a warning. Canonical validation is what
        makes it impossible to author."""
        cid, other = "CND-0003", "CND-0005"
        foreign = [i["entity_id"] for i in self.payload(other).get("Interface") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["load_paths"][0]["ordered_hops"] = foreign[:1]
        r = self.invoke(cid, response)
        self.assertTrue(any("FOREIGN_BRANCH" in p for p in r["problems"]),
                        r["problems"])

    def test_the_guard_governs_only_fields_that_declare_it(self):
        """A design-wide field naming a design-wide entity is untouched by the
        rule, which is why nothing had to be narrowed to make it hold."""
        from ver3.assy_v3.state.design_state import Contracts
        c = Contracts()
        self.assertEqual("DESIGN_WIDE",
                         c.reference_spec("LoadPath", "load_case")["referent_population"])
        self.assertEqual("INVOCATION_BRANCH",
                         c.reference_spec("LoadPath", "ordered_hops")["referent_population"])

    def test_an_interaction_between_foreign_groups_is_refused(self):
        cid, other = "CND-0003", "CND-0005"
        foreign = [g["entity_id"] for g in self.payload(other).get("RigidGroup") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["physical_interactions"][0]["groups"] = foreign[:2]
        self.assertTrue(self.invoke(cid, response)["refused"])

    def test_an_assembly_step_installing_a_foreign_body_is_refused(self):
        cid, other = "CND-0003", "CND-0005"
        foreign = [b["entity_id"] for b in self.payload(other).get("Body") or []]
        response = copy.deepcopy(self.baseline(cid))
        response["assembly_steps"][0]["body"] = foreign[0]
        self.assertTrue(self.invoke(cid, response)["refused"])

    def test_the_load_path_candidate_is_the_invocation_not_the_response(self):
        cid, other = "CND-0003", "CND-0005"
        response = copy.deepcopy(self.baseline(cid))
        for path in response["load_paths"]:
            path["candidate"] = other
        r = self.invoke(cid, response)
        for op in (r["patch"].operations if r["patch"] is not None else []):
            if op.entity_type == "LoadPath":
                self.assertEqual(cid, op.fields.get("candidate"))
        self.assertTrue(r["refused"], "the response named another candidate and "
                                      "nothing said so")

    def test_design_wide_references_stay_design_wide(self):
        """LoadCase, the effect obligations and the reaction sites are candidate-
        independent by declaration; branch-locality must not have narrowed them."""
        cid = "CND-0003"
        r = self.invoke(cid, self.baseline(cid))
        self.assertEqual([], r["problems"])
        self.assertEqual([], r["incomplete"])

    def test_same_branch_references_are_accepted(self):
        for cid in sorted(self.views):
            with self.subTest(candidate=cid):
                r = self.invoke(cid, self.baseline(cid))
                self.assertEqual([], r["problems"])

    def test_the_derived_grid_stays_inside_the_branch(self):
        cid = "CND-0003"
        own = {g["entity_id"] for g in self.payload(cid).get("RigidGroup") or []}
        owncfg = {c["entity_id"] for c in self.payload(cid).get("Configuration") or []}
        r = self.invoke(cid, self.baseline(cid))
        for row in self.cells(r["patch"]):
            self.assertIn(row["rigid_group"], own)
            self.assertIn(row["configuration"], owncfg)


# ======================================================================
# 6. The view's populations are the contract's roles
# ======================================================================

class TestReadinessCountsComeFromTheContract(_Seam):

    def test_topology_relation_is_joint_and_interface(self):
        from ver3.assy_v3.view.consumer_view import role_populations
        for cid in sorted(self.views):
            with self.subTest(candidate=cid):
                roles = role_populations(self.views[cid])
                payload = self.payload(cid)
                expected = len(payload.get("Joint") or []) + len(payload.get("Interface") or [])
                self.assertEqual(expected, len(roles["topology_relation"]))
                self.assertGreater(expected, 0, "a branch with no relation at all")

    def test_topology_element_is_body_and_rigid_group(self):
        from ver3.assy_v3.view.consumer_view import role_populations
        cid = "CND-0003"
        payload = self.payload(cid)
        roles = role_populations(self.views[cid])
        self.assertEqual(len(payload.get("Body") or []) + len(payload.get("RigidGroup") or []),
                         len(roles["topology_element"]))

    def test_every_required_role_of_the_responsibility_is_reported(self):
        from ver3.assy_v3.view.consumer_view import role_populations
        from ver3.assy_v3.view.consumer_view import Source
        view = self.views["CND-0003"]
        roles = role_populations(view)
        for requirement in view.required.of(Source.REASONING_PREMISE):
            for role, _families in requirement.atoms():
                self.assertIn(role, roles)

    def test_a_role_no_family_carries_is_not_invented(self):
        from ver3.assy_v3.view.consumer_view import role_populations
        roles = role_populations(self.views["CND-0003"])
        self.assertNotIn("motion_occupancy", roles,
                         "a role this responsibility does not require was counted")


# ======================================================================
# The bounded field audit, as a standing check rather than a one-off
# ======================================================================

class TestEveryS03bFieldAgreesAcrossTheSeam(_Seam):
    """prompt -> response -> to_operations -> contract -> checker.

    Run mechanically over every response key rather than over the fields someone
    remembered, because the four divergences that closed the s03a seam were each
    a field where two of these five disagreed and nobody was comparing them.
    """

    KEY_FAMILY = {"physical_interactions": "PhysicalInteraction",
                  "constraint_relations": "ConstraintRelation",
                  "load_paths": "LoadPath",
                  "assembly_steps": "AssemblyStep",
                  "unresolved": "UnresolvedDecision"}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from ver3.assy_v3.state.design_state import Contracts
        cls.contracts = Contracts()

    def authored(self, cid="CND-0003"):
        """family -> the fields the producer actually writes, from a real run."""
        response = self.baseline(cid)
        inputs = {"candidate": _branches.candidate(self.state, cid),
                  self.stage.context_key: self.payload(cid)}
        out = {}
        for op in self.stage.to_operations(response, inputs):
            out.setdefault(op.entity_type, set()).update(
                k for k, v in (op.fields or {}).items() if v is not None)
        return out

    def test_the_producer_writes_no_field_the_contract_does_not_declare(self):
        for family, fields in sorted(self.authored().items()):
            declared = set(self.contracts.required_fields(family)) | set(
                self.contracts.families.get(family, {}).get("optional_fields") or [])
            with self.subTest(family=family):
                self.assertEqual(set(), fields - declared,
                                 "%s would enter state untyped" % family)

    def test_every_required_field_of_every_authored_family_is_written(self):
        for family, fields in sorted(self.authored().items()):
            required = {f for f in self.contracts.required_fields(family)
                        if f != "entity_id"}
            with self.subTest(family=family):
                self.assertEqual(set(), required - fields)

    def test_the_prompt_asks_for_every_required_field_it_expects_back(self):
        """Except what the pipeline itself supplies: `maturity` is a producer
        constant and `candidate` is the invocation's, so neither is asked."""
        from ver3.assy_v3.stages.s03_topology_and_mobility import S03B_PROMPT
        supplied = {"entity_id", "maturity", "candidate"}
        for key, family in sorted(self.KEY_FAMILY.items()):
            for field in self.contracts.required_fields(family):
                if field in supplied:
                    continue
                with self.subTest(family=family, field=field):
                    self.assertIn(field, S03B_PROMPT,
                                  "%s.%s is required and the prompt never names it"
                                  % (family, field))

    def test_the_producer_forwards_no_field_the_prompt_never_asks_for(self):
        """A field no question produced can only arrive unasked, and it would
        enter canonical state carrying whatever it happened to hold."""
        from ver3.assy_v3.stages.s03_topology_and_mobility import S03B_PROMPT
        import inspect
        source = inspect.getsource(self.stage.__class__.to_operations)
        for name in re.findall(r'"(\w+)"', source):
            if name in self.KEY_FAMILY or name in ("id", "s03b:relations",
                                                   "CREATE", "HYPOTHESIS"):
                continue
            if name in ("PhysicalInteraction", "ConstraintRelation", "LoadPath",
                        "AssemblyStep", "UnresolvedDecision",
                        "TransitionRequirement", "maturity", "candidate",
                        "irrelevance"):
                continue
            with self.subTest(field=name):
                self.assertIn(name, S03B_PROMPT,
                              "%s is parsed and never asked for" % name)

    def test_every_branch_local_reference_is_declared_by_the_contract(self):
        """The locality rule reads `referent_population`; a field the contract
        does not type as a reference is not governed by it at all."""
        for family, fields in sorted(self.authored().items()):
            for field in sorted(fields):
                spec = self.contracts.reference_spec(family, field)
                if spec is None:
                    continue
                population = spec.get("referent_population") or "INVOCATION_BRANCH"
                with self.subTest(family=family, field=field):
                    self.assertIn(population, ("INVOCATION_BRANCH", "DESIGN_WIDE",
                                               "COMMITTED_BRANCH",
                                               "ALL_RETAINED_BRANCHES"))

    def test_the_design_wide_fields_are_exactly_the_ones_named(self):
        """A record of what may cross a branch boundary, so narrowing or widening
        one is a decision someone has to make here rather than a side effect."""
        crossing = set()
        for family, fields in sorted(self.authored().items()):
            for field in sorted(fields):
                spec = self.contracts.reference_spec(family, field) or {}
                if spec.get("referent_population") == "DESIGN_WIDE":
                    crossing.add("%s.%s" % (family, field))
        self.assertEqual({"PhysicalInteraction.discharges_effect",
                          "LoadPath.load_case", "LoadPath.terminates_at"},
                         crossing)


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
