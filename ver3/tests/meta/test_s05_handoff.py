"""UNIT E: THE POST-SELECTION HANDOFF - current S01-S04 state plus the standing
human SelectionDecision becomes ONE canonical, current, correctly scoped s05
input branch.

    the branch is the decision's, never a caller's       (E1)
    every s05 fact rests on the decision and the candidate,
      and a revised selection withdraws it                (E2)
    an obligation is DISCHARGED at the stage it becomes
      satisfiable and PRESERVED after; visibility is not duty (E3)
    a feature names, by typed reference, the interface it
      realizes; an interaction is never invented here       (E4)
    s04's provisional arrangement is respected, never copied;
      an envelope is symbolic, never a bare number           (E5)
    the hard-requirement debt owed to s05 reaches s05 by
      typed fields, and nothing else's debt does             (E6)
    the provider is shown the declared minimum; the record
      keeps the decision's full lineage                      (E7)

Every probe runs on the Unit D fixture: a hinge and a four-bar, taken through
the real s03/s04 passes, assessed, compared, and committed to one of them by the
real backend writer - with a deferred hard-requirement debt on the commitment.
Synthetic throughout. No product noun, no benchmark id.
"""
from __future__ import annotations

import inspect
import json
import re
import textwrap
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s05_embodiment as s05                       # noqa: E402
import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.selection_decision as dec                   # noqa: E402
import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.pipeline.progression import Progression, execute_stage  # noqa: E402
from ver3.assy_v3.stages.s05_embodiment import S05Embodiment            # noqa: E402
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.assy_v3.view import InvocationContext, committed_branch        # noqa: E402
from .test_s7_hard_requirement_timing import _Timing                    # noqa: E402
from .test_s7_lifecycle import STALE, STANDING, _code                  # noqa: E402
from .test_selection_to_embodiment_seam import FixedProvider            # noqa: E402

S05_FAMILIES = ("Feature", "Realization", "Parameter", "Constraint",
                "ConstructionStatement")
NYE, VIO = s07.NOT_YET_EVALUABLE, s07.VIOLATED
PRE, DOWN = s07.PRE_SELECTION, s07.DOWNSTREAM


def mm(v):
    return {"const": float(v), "unit": "mm"}


def ref(pid):
    return {"ref": pid}


#: A symbolic envelope: where the material may be, in the dimensions declared.
SYMBOLIC = {"centre": [mm(0), mm(0), mm(0)],
            "half_extent": [ref("PRM-0001"), ref("PRM-0001"), mm(2)]}


def embodiment_from(view, *, cite=(), envelope=None, feature_kind="FACE",
                    occupancy=None):
    """A contract-valid embodiment of whatever branch the VIEW shows.

    Built from the projection - the bodies, the interfaces, the blocking
    relations, the clearances - so the same helper embodies either candidate
    and nothing here knows which is selected. Realizations cite only what the
    caller says; the duty split is the thing under test. Ids are minted past
    the namespace occupancy the view reports, as a model is told to.
    """
    taken = {fam: set(ids) for fam, ids in (occupancy or {}).items()}

    def free(prefix, family, n):
        while "%s%04d" % (prefix, n) in taken.get(family, set()):
            n += 1
        return n
    bodies = [b["entity_id"] for b in view.get("Body") or []]
    features, n = [], 0
    group_body = {g["entity_id"]: g.get("body") for g in view.get("RigidGroup") or []}
    limit_bodies = set()
    for rel in view.get("ConstraintRelation") or []:
        if rel.get("blocked_dofs"):
            limit_bodies |= {b for b in (rel.get("provider_body"),
                                         group_body.get(rel.get("retained_group"))) if b}
    for iface in view.get("Interface") or []:
        for body in iface.get("bodies") or []:
            n = free("FEA-", "Feature", n + 1)
            features.append({"id": "FEA-%04d" % n, "body": body,
                             "feature_kind": "STOP" if body in limit_bodies else feature_kind,
                             "geometry": "the face that meets the other body",
                             "interface": iface["entity_id"],
                             "envelope": envelope or SYMBOLIC})
    for body in bodies:
        if not any(f["body"] == body for f in features):
            n = free("FEA-", "Feature", n + 1)
            features.append({"id": "FEA-%04d" % n, "body": body, "feature_kind": "FACE",
                             "geometry": "a datum face", "envelope": envelope or SYMBOLIC})
    for body in limit_bodies - {f["body"] for f in features if f["feature_kind"] == "STOP"}:
        n = free("FEA-", "Feature", n + 1)
        features.append({"id": "FEA-%04d" % n, "body": body, "feature_kind": "STOP",
                         "geometry": "the stop face", "envelope": envelope or SYMBOLIC})
    prm = "PRM-%04d" % free("PRM-", "Parameter", 1)
    symbolic = envelope or {"centre": [mm(0), mm(0), mm(0)],
                            "half_extent": [ref(prm), ref(prm), mm(2)]}
    for f in features:
        if f["envelope"] is SYMBOLIC:
            f["envelope"] = symbolic
    k = free("CON-", "Constraint", 1)
    constraints = [{"id": "CON-%04d" % k, "kind": "DIMENSIONAL", "parameters": [prm],
                    "expression": {"relation": ">=", "lhs": ref(prm), "rhs": mm(0.75)}}]
    for iface in view.get("Interface") or []:
        if str(iface.get("interaction_kind", "")).upper() in s05.CLEARANCE_KINDS:
            k = free("CON-", "Constraint", k + 1)
            constraints.append({"id": "CON-%04d" % k, "kind": "CLEARANCE",
                                "parameters": [prm],
                                "governs_interface": iface["entity_id"],
                                "expression": {"relation": ">=", "lhs": ref(prm),
                                               "rhs": mm(0.1)}})
    statements, c = [], 0
    for body in bodies:
        c = free("CST-", "ConstructionStatement", c + 1)
        statements.append({"id": "CST-%04d" % c, "body": body, "operation": "BOX",
                           "operands": [],
                           "parameters": {"dx": ref(prm), "dy": mm(10), "dz": mm(4)}})
    r = free("RLZ-", "Realization", 1)
    realizations = [{"id": "RLZ-%04d" % r, "addresses_obligations": list(cite),
                     "participating_features": [features[0]["id"]],
                     "verification_predicate": "the faces meet where the relation says"}
                    ] if cite else []
    return {"features": features, "realizations": realizations,
            "parameters": [{"id": prm, "symbol": "t", "unit": "mm"}],
            "constraints": constraints, "construction_statements": statements,
            "unresolved": []}


class _Handoff(_Timing):
    """The Unit D committed design, and the s05 seam over it."""

    def committed(self):
        """Both candidates feasible, one DOWNSTREAM requirement owed to s05, a
        comparison, and a commitment to CND-A written by the real writer."""
        state, constraint = self.deferred_design()
        self.compare(state, self.P)
        out = self.decide(state, "CND-A", "chosen with its debt on the screen")
        self.assertEqual(dec.SELECTION_COMMITTED, out.status, out.problems)
        return state, constraint, self.committed_decision(state)["entity_id"]

    def view_of(self, state, invocation=None):
        return S05Embodiment().consumer_view(state, invocation)

    def embody(self, state, payload=None, invocation=None, attempt=1):
        """Through the ONE invocation path, with a deterministic provider."""
        view = self.view_of(state)
        payload = payload if payload is not None else embodiment_from(
            view.provider_payload(), occupancy=view.occupancy)
        provider = FixedProvider(payload)
        p = Progression()
        out, ex = execute_stage(S05Embodiment(), provider, state, p,
                                invocation=invocation, attempt=attempt)
        return out, ex, provider, p

    def s05_records(self, state):
        return [r for f in S05_FAMILIES for r in state.family(f)]

    def revise_to(self, state, candidate):
        """A person changes the commitment, through the real revision writer."""
        snapshot = self.review_of(state)
        self.assertIsNotNone(snapshot.standing_decision, "no commitment on the screen")
        submitted = self.submit(state, snapshot, dec.SELECT, candidate)
        self.assertTrue(submitted.ok, submitted.problems)
        out = dec.revise_human_selection(state, submitted.input_id)
        self.assertEqual(dec.SELECTION_REVISED, out.status, out.problems)
        state.apply(out.patch)
        return out


# =====================================================================
# E1 - the branch is the decision's
# =====================================================================
class TestBranchAuthority(_Handoff):

    def test_01_no_standing_decision_means_no_call(self):
        state, _constraint = self.deferred_design()
        self.assertEqual([], state.standing("SelectionDecision"))
        out, _ex, provider, p = self.embody(state, payload={"features": []})
        self.assertEqual(0, provider.calls)
        self.assertEqual("CONSUMER_CONTEXT_INSUFFICIENT", out.execution_status.value)
        self.assertTrue(p.failures)

    def test_02_a_caller_cannot_direct_s05_to_another_candidate(self):
        state, _c, decision = self.committed()
        view = self.view_of(state, InvocationContext(branch="CND-B"))
        self.assertEqual("CND-A", view.branch, "the branch is the decision's, not the caller's")
        self.assertEqual("UPSTREAM_INSUFFICIENCY", view.status.value)
        detail = " ".join(a.get("detail", "") for a in view.assessment)
        self.assertIn("CND-B", detail)
        self.assertIn("CND-A", detail)
        self.assertIn("nobody chose", detail)
        out, _ex, provider, _p = self.embody(state, payload={"features": []},
                                             invocation=InvocationContext(branch="CND-B"))
        self.assertEqual(0, provider.calls)
        # naming the committed candidate is not a contradiction
        agreed = self.view_of(state, InvocationContext(branch="CND-A"))
        self.assertEqual("VIEW_READY", agreed.status.value)
        self.assertEqual("CND-A", agreed.branch)

    def test_02b_invocation_and_committed_populations_cannot_disagree(self):
        """Structurally: no s05 premise is drawn from a caller's branch, and the
        responsibility declares where its branch comes from."""
        s05_decl = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")["stages"]["s05"]
        self.assertEqual("SELECTION_DECISION", s05_decl["branch_authority"])
        self.assertEqual("DECLARED_ONLY", s05_decl["provider_projection"])
        for premise in s05_decl["required_reasoning_premise_classes"]:
            rule = premise["instance_selection"]
            populations = ([r["population"] for r in rule["by_role"]]
                           if rule.get("by_role") else [rule["population"]])
            with self.subTest(premise["class"]):
                self.assertNotIn("INVOCATION_BRANCH", populations)
                self.assertTrue(set(populations) <= {"COMMITTED_BRANCH", "DESIGN_WIDE"})
        # and the runtime agrees: a view asked for CND-B resolves every branch
        # population against CND-A
        state, _c, _d = self.committed()
        asked = self.view_of(state, InvocationContext(branch="CND-B"))
        bodies = {r["entity_id"] for r in asked.payload().get("Body") or []}
        self.assertTrue(bodies, "the probe is not probing")
        self.assertTrue(all(b.endswith("A") for b in bodies), bodies)
        # the stage keeps no second copy of the rule
        self.assertNotIn("nobody chose", _code(inspect.getsource(s05)))


# =====================================================================
# E7 / E2 - what the provider is shown, and what every fact rests on
# =====================================================================
class TestProjectionAndPremises(_Handoff):

    def test_03_only_the_selected_branch_engineering_reaches_the_provider(self):
        state, _c, _d = self.committed()
        view = self.view_of(state)
        shown = view.provider_payload()
        for family in ("Body", "RigidGroup", "Joint", "Interface", "Envelope",
                       "PhysicalInteraction", "State", "Transition", "SweptVolume",
                       "MobilityExpectation", "LoadPath", "Configuration"):
            ids = [r["entity_id"] for r in shown.get(family) or []]
            with self.subTest(family):
                self.assertTrue(ids, "the fixture shows no %s" % family)
                self.assertTrue(all(i.endswith("A") for i in ids), ids)
        self.assertEqual(["CND-A"], [r["entity_id"] for r in shown["Candidate"]])
        self.assertEqual([state.standing("SelectionDecision")[0]["entity_id"]],
                         [r["entity_id"] for r in shown["SelectionDecision"]])

    def test_04_rejected_candidate_evidence_and_selection_bookkeeping_stay_off_the_prompt(self):
        state, constraint, decision = self.committed()
        view = self.view_of(state)
        shown = view.provider_payload()
        for family in ("MechanicalFeasibilityAssessment", "FeasibilityDomainAssessment",
                       "CandidateComparison", "SelectionProfile", "HumanDecisionInput"):
            self.assertNotIn(family, shown, family)
        self.assertNotIn("CND-B", [r["entity_id"] for r in shown["Candidate"]])
        self.assertEqual(["HRC-CND-A-%s" % constraint],
                         [r["entity_id"] for r in shown["HardRequirementCompliance"]])
        # the prompt is rendered from that projection and from nothing else
        stage = S05Embodiment()
        prompt = stage.build_prompt({stage.context_key: shown,
                                     stage.occupancy_key: view.occupancy})
        # the decision record still LISTS its lineage by id (that is what the
        # record says); what must be absent is the evidence content those ids
        # name - domain findings, metrics, preference criteria, a rationale
        # (the commitment record's own `rationale` - the person's stated reason
        # for THIS choice - stays, being a field of the decision itself)
        for absent in ("FDA-CND-B", '"metrics"', '"criteria"', '"reviewed_advisories"',
                       '"reason_codes"', '"open_obligations"', '"frontier"',
                       '"premise_digest"'):
            self.assertNotIn(absent, prompt, absent)
        self.assertIn(decision, prompt)
        rendered_records = json.loads(prompt.split("DECIDED MECHANISM AND SPATIAL CONTEXT")[1]
                                      .split("RESPONSE SCHEMA")[0].strip().split("\n", 1)[1])
        self.assertNotIn("MechanicalFeasibilityAssessment", rendered_records)
        self.assertNotIn("CandidateComparison", rendered_records)

    def test_24_the_record_keeps_the_decisions_full_lineage(self):
        """Reduction is of the RENDERING. The recorded view still holds every
        referent the commitment cites, so audit and currentness lose nothing."""
        state, constraint, decision = self.committed()
        view = self.view_of(state)
        audit = view.payload()
        for family, member in (("MechanicalFeasibilityAssessment", "MFA-CND-B"),
                               ("HardRequirementCompliance", "HRC-CND-B-%s" % constraint),
                               ("CandidateComparison", None), ("SelectionProfile", None),
                               ("HumanDecisionInput", None), ("Candidate", "CND-B")):
            ids = [r["entity_id"] for r in audit.get(family) or []]
            with self.subTest(family):
                self.assertTrue(ids)
                if member:
                    self.assertIn(member, ids)
        record = view.as_dict()
        self.assertEqual("DECLARED_ONLY", record["provider_projection"]["mode"])
        held = set(record["provider_projection"]["audit_only"])
        self.assertIn("MFA-CND-B", held)
        self.assertIn("CND-B", held)
        self.assertNotIn(decision, held)
        self.assertTrue({t["entity_id"] for t in view.traces if t["requirement"] == "closure"}
                        >= held)
        # and the recorded outcome carries the whole view
        out, _ex, _p, _pr = self.embody(state)
        self.assertIn("MFA-CND-B", json.dumps(out.consumer_view))

    def test_05_every_s05_fact_rests_on_the_candidate_and_the_decision(self):
        state, _c, decision = self.committed()
        out, ex, provider, p = self.embody(state)
        self.assertEqual(1, provider.calls)
        self.assertEqual([], list(out.problems), out.problems)
        self.assertEqual([], list(out.declared_incompleteness or []),
                         out.declared_incompleteness)
        self.assertTrue(ex.patch_applied)
        creates = [o for o in out.patch.operations if o.kind == "CREATE"]
        self.assertGreaterEqual(len(creates), 6)
        for op in creates:
            with self.subTest(op.entity_id):
                self.assertIn("CND-A", op.premise_refs)
                self.assertIn(decision, op.premise_refs)
        for rec in self.s05_records(state):
            self.assertIn(decision, rec["_premises"])
            self.assertEqual(STANDING, rec["_validity"])

    def test_06_a_revised_selection_withdraws_the_prior_embodiment(self):
        state, _c, old_decision = self.committed()
        self.embody(state)
        before = {r["entity_id"] for r in self.s05_records(state)}
        self.assertTrue(before)
        self.revise_to(state, "CND-B")
        self.assertEqual("INVALIDATED", self.validity(state, old_decision))
        new_decision = state.standing("SelectionDecision")[0]
        self.assertEqual("CND-B", new_decision["selected_candidate"])
        self.assertEqual("CND-B", committed_branch(state, state.c))
        for eid in sorted(before):
            with self.subTest(eid):
                self.assertEqual(STALE, self.validity(state, eid))
                self.assertEqual(old_decision, state.entities[eid]["_stale_because"][0]["root"])
                self.assertIn(eid, state.entities, "history was deleted")
        # nothing of A's embodiment is offered as B's
        view = self.view_of(state)
        self.assertEqual("CND-B", view.branch)
        shown = view.provider_payload()
        self.assertTrue(all(i not in before for f in S05_FAMILIES
                            for i in [r["entity_id"] for r in shown.get(f) or []]))


# =====================================================================
# frozen upstream: s05 may not touch what it does not own
# =====================================================================
class TestUpstreamIsFrozen(_Handoff):

    def refused(self, state, ops):
        return state.validate(StagePatch(
            patch_id="probe", run_id=state.run_id, stage_id="s05", stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=ops,
            execution_status="SUCCESS", provenance={"provider": "t"}))

    def test_07_s05_cannot_mutate_the_selected_principle(self):
        state, _c, _d = self.committed()
        principle = dict(state.entities["CND-A"]["principle"])
        problems = self.refused(state, [Op("SUPERSEDE", "Candidate", "CND-A",
                                           {"principle": {"support": "SLIDE"}},
                                           "s05:embodiment", reason="probe")])
        self.assertTrue(any("OWNERSHIP" in p or "NOT_OWNER" in p or "may not" in p
                            for p in problems), problems)
        self.assertEqual(principle, state.entities["CND-A"]["principle"])
        source = _code(textwrap.dedent(inspect.getsource(S05Embodiment.to_operations)))
        for family in ('"Candidate"', '"SelectionDecision"', '"Body"', '"Joint"',
                       '"Interface"', '"Envelope"'):
            self.assertNotIn(family, source, family)

    def test_08_s05_cannot_revise_s03_topology(self):
        state, _c, _d = self.committed()
        for op in (Op("SUPERSEDE", "Joint", "JNT-0A", {"axis_direction": "+X"},
                      "s05:embodiment", reason="probe"),
                   Op("CREATE", "Body", "BOD-NEW", {"instance_identity": "x", "role": "x",
                                                    "created_by_stage": "s05"},
                      "s05:embodiment"),
                   Op("SUPERSEDE", "Interface", state.standing("Interface")[0]["entity_id"],
                      {"interaction_kind": "CLEARANCE"}, "s05:embodiment", reason="probe")):
            with self.subTest(op.entity_type):
                self.assertTrue(self.refused(state, [op]))

    def test_09_s05_cannot_revise_s04_spatial_facts(self):
        state, _c, _d = self.committed()
        for op in (Op("SUPERSEDE", "Envelope", "ENV-G0A",
                      {"extent": {"centre": [9, 0, 0], "half_extent": [1, 1, 1]}},
                      "s05:embodiment", reason="probe"),
                   Op("SUPERSEDE", "ReferenceScale", "SCL-CND-A", {"basis": "ABSOLUTE"},
                      "s05:embodiment", reason="probe")):
            with self.subTest(op.entity_type):
                self.assertTrue(self.refused(state, [op]))
        # and the embodiment itself writes nothing but its own families
        out, _ex, _p, _pr = self.embody(state)
        self.assertEqual({"Feature", "Parameter", "Constraint", "ConstructionStatement"},
                         {op.entity_type for op in out.patch.operations})

    def test_21_the_human_remains_the_only_chooser(self):
        state, _c, decision = self.committed()
        self.embody(state)
        self.assertEqual(decision, state.standing("SelectionDecision")[0]["entity_id"])
        self.assertEqual("CND-A", committed_branch(state, state.c))
        source = _code(inspect.getsource(s05)).lower()
        for token in ("eligible_candidates", "rank(", "best_candidate",
                      "selection_profile", "candidatecomparison", "frontier("):
            self.assertNotIn(token, source, token)

    def test_22_no_benchmark_or_candidate_literal(self):
        for module in (s05, cv):
            self.assertIsNone(re.search(r"\bBM-\d|\bCND-\d", inspect.getsource(module)),
                              module.__name__)


# =====================================================================
# E3 - duties, not visibility
# =====================================================================
class TestObligationDuties(_Handoff):

    def obligation(self, oid, at, scope="UNIVERSAL"):
        return {"entity_id": oid, "statement": "something must hold", "scope": scope,
                "mandatory": True, "satisfiable_at": at, "evidence_route": "ANALYSIS",
                "route_available": True, "derived_from_requirements": []}

    def test_10_applicable_obligations_split_into_discharge_and_preserve(self):
        obligations = [self.obligation("OBL-S3", "s03"), self.obligation("OBL-S4", "s04"),
                       self.obligation("OBL-S5", "s05"), self.obligation("OBL-UNDATED", ""),
                       self.obligation("OBL-OTHER", "s05", "CANDIDATE_DISCRIMINATING")]
        duties = cv.obligation_duties(obligations, [], "s05")
        self.assertEqual({"OBL-S5", "OBL-UNDATED"}, duties[cv.DISCHARGE])
        self.assertEqual({"OBL-S3", "OBL-S4"}, duties[cv.PRESERVE])
        self.assertNotIn("OBL-OTHER", duties[cv.DISCHARGE] | duties[cv.PRESERVE])
        taken = cv.obligation_duties(obligations, [{"candidate": "CND-A",
                                                    "obligations": ["OBL-OTHER"]}], "s05")
        self.assertIn("OBL-OTHER", taken[cv.DISCHARGE])
        # the fixture's own obligation became satisfiable at s03: preserved
        state, _c, _d = self.committed()
        view = self.view_of(state).provider_payload()
        duties = s05.embodiment_duties(view)
        self.assertEqual({"OBL-0001"}, duties[cv.PRESERVE])
        self.assertEqual(set(), duties[cv.DISCHARGE])
        text = s05.render_duties(view)
        self.assertIn("PRESERVE", text)
        self.assertIn("OBL-0001 (satisfiable at s03)", text)
        self.assertIn("DISCHARGE", text)

    def test_11_a_visible_obligation_is_not_a_duty_to_claim(self):
        state, _c, _d = self.committed()
        view = self.view_of(state).provider_payload()
        claimed = embodiment_from(view, cite=["OBL-0001"])
        problems = s05.check_c4_obligations_realized(claimed, view)
        self.assertTrue(any("OBL-0001" in p and "preserves it" in p for p in problems),
                        problems)
        out, ex, _p, _pr = self.embody(state, payload=claimed)
        self.assertTrue(any("preserves it" in d for d in out.declared_incompleteness))
        # a discharge duty, once dated at s05, is demanded
        dated = dict(view, Obligation=[dict(view["Obligation"][0], satisfiable_at="s05")])
        problems = s05.check_c4_obligations_realized(embodiment_from(dated), dated)
        self.assertTrue(any("cited by no realization" in p for p in problems), problems)
        self.assertEqual([], s05.check_c4_obligations_realized(
            embodiment_from(dated, cite=["OBL-0001"]), dated))
        # the prompt and the check read one rule
        self.assertIn("obligation_duties(", _code(inspect.getsource(s05.embodiment_duties)))
        self.assertIn("embodiment_duties(", _code(inspect.getsource(s05.render_duties)))
        self.assertIn("embodiment_duties(",
                      _code(inspect.getsource(s05.check_c4_obligations_realized)))


# =====================================================================
# E4 - the typed trace to the interaction
# =====================================================================
class TestInteractionTrace(_Handoff):

    def test_12_a_feature_names_the_interface_it_realizes_by_typed_reference(self):
        state, _c, _d = self.committed()
        out, _ex, _p, _pr = self.embody(state)
        interface = state.standing("Interface")[0]["entity_id"]
        realizing = [f for f in state.standing("Feature") if f.get("interface")]
        self.assertEqual(2, len(realizing), "one side each")
        for f in realizing:
            self.assertEqual(interface, f["interface"])
            self.assertIn(interface, f["_premises"])
            self.assertIn(f["body"], state.entities[interface]["bodies"])
        spec = Contracts().field_semantics("Feature")["interface"]
        self.assertEqual(("reference", "Interface", "one"),
                         (spec["kind"], spec["target"], spec["cardinality"]))
        # the boundary refuses a feature naming an interface that does not exist
        problems = state.validate(StagePatch(
            patch_id="probe", run_id=state.run_id, stage_id="s05", stage_attempt=2,
            parent_state_hash=state.state_hash(), execution_status="SUCCESS",
            provenance={"provider": "t"},
            operations=[Op("CREATE", "Feature", "FEA-9999",
                           {"body": "BOD-G0A", "feature_kind": "FACE", "geometry": "x",
                            "interface": "IFC-INVENTED"}, "s05:embodiment")]))
        self.assertTrue(any("DANGLING" in p for p in problems), problems)
        # and the check refuses one the branch does not carry, before the boundary
        view = self.view_of(state).provider_payload()
        probe = embodiment_from(view)
        probe["features"][0]["interface"] = "IFC-INVENTED"
        self.assertTrue(any("invented" in p for p in
                            s05.check_c1_interface_features(probe, view)))

    def test_13_a_revised_interface_stales_the_geometry_that_realized_it(self):
        """Two things happen when s03 restates an interface, and both are
        ordinary propagation. The features that named it go stale DIRECTLY -
        the typed `interface` premise, one hop, no special case. And because
        the interface was a premise of the feasibility evidence the comparison
        and the commitment rested on, the commitment itself reopens, so nothing
        of the embodiment is offered as current: a revised architecture is not
        something a standing selection survives."""
        state, _c, decision = self.committed()
        self.embody(state)
        interface = state.standing("Interface")[0]["entity_id"]
        features = [f["entity_id"] for f in state.standing("Feature") if f.get("interface")]
        self.assertEqual(2, len(features))
        everything = [r["entity_id"] for r in self.s05_records(state)]
        self.supersede(state, interface, {"nominal": "revised by the owner"},
                       stage="s03", why="the interface was restated")
        for eid in features:
            with self.subTest(eid):
                self.assertEqual(STALE, self.validity(state, eid))
                because = state.entities[eid]["_stale_because"][0]
                self.assertEqual(interface, because["premise"])
                self.assertEqual(1, because["hops"], "the typed edge is direct")
        self.assertEqual(STALE, self.validity(state, decision),
                         "a revised interface reopens the selection that rested on it")
        for eid in everything:
            self.assertEqual(STALE, self.validity(state, eid), eid)
            self.assertIn(eid, state.entities, "history was deleted")
        # and the stage may not run on the reopened design
        out, _ex, provider, _p = self.embody(state, payload={"features": []})
        self.assertEqual(0, provider.calls)


# =====================================================================
# E5 - the s04 bridge
# =====================================================================
class TestSpatialBridge(_Handoff):

    def test_14_a_relative_extent_is_never_a_dimension(self):
        state, _c, _d = self.committed()
        scale = state.entities["SCL-CND-A"]
        self.assertEqual("RELATIVE", scale["basis"], "the probe is not probing")
        out, _ex, _p, _pr = self.embody(state)
        self.assertEqual([], list(out.declared_incompleteness or []))
        for p in state.standing("Parameter"):
            self.assertNotIn("value", p)
            self.assertEqual("DECLARED", p["status"])
        # every constant embodiment states is typed and unit-bearing, and in a
        # RELATIVE basis none of them is comparable with an s04 extent - so no
        # s04 number can have become a dimension by conversion
        for c in state.standing("Constraint"):
            for node in (c["expression"]["lhs"], c["expression"]["rhs"]):
                self.assertIsInstance(node, dict)
        for f in state.standing("Feature"):
            exprs, problems = s05.envelope_expressions(
                f["entity_id"], f["envelope"], {p["entity_id"] for p in state.standing("Parameter")})
            self.assertEqual([], problems)
            self.assertIsNone(s05.envelope_box(exprs, scale))
        # a constant in millimetres cannot be placed in a RELATIVE basis
        self.assertIsNone(s05._constant_in_basis(s05.ir.Expr.parse(mm(5)), scale))
        self.assertIsNone(s05.envelope_box(
            {"centre": [s05.ir.Expr.parse(mm(0))] * 3,
             "half_extent": [s05.ir.Expr.parse(mm(1))] * 3}, scale))

    def test_15_an_embodiment_with_unsolved_symbols_is_representable(self):
        state, _c, _d = self.committed()
        out, ex, _p, _pr = self.embody(state)
        self.assertTrue(ex.patch_applied)
        self.assertEqual([], list(out.declared_incompleteness or []))
        for f in state.standing("Feature"):
            env = f["envelope"]
            self.assertEqual(SYMBOLIC, env)
            for node in env["centre"] + env["half_extent"]:
                self.assertIsInstance(node, dict)
            self.assertNotIn("PRM-0001", f["_premises"],
                             "a symbolic reference is not a premise")
        self.assertEqual([], [p for p in state.standing("Parameter") if "value" in p])

    def test_16_the_numeric_envelope_contradiction_is_gone_from_production(self):
        instructions = s05.PROMPT.split("DECIDED MECHANISM")[0]
        self.assertIn("NEVER a bare number", instructions)
        self.assertIn("never copy a provisional extent", instructions)
        self.assertNotIn("so its occupancy can be checked against the regions the design "
                         "reserved", instructions)
        fams = Contracts().families
        self.assertIn("never a bare number", " ".join(fams["Feature"]["rules"]))
        bare = {"features": [{"id": "FEA-1", "body": "BOD-1", "feature_kind": "FACE",
                              "geometry": "x", "envelope": {"centre": [0, 0, 0],
                                                            "half_extent": [1, 1, 1]}}]}
        self.assertTrue(any("bare number" in p for p in
                            s05.check_c8_region_intrusion(bare, {})))
        s05c = _paths.load_yaml(_paths.CONTRACTS + "/stages/S05_CONTRACT.yaml")
        self.assertIn("never a bare number", json.dumps(s05c["post_selection_handoff"]))


# =====================================================================
# E6 - the debt s05 owes
# =====================================================================
class TestHardRequirementDebt(_Handoff):

    def test_17_s05_receives_exactly_the_debt_it_owes(self):
        state, constraint, _d = self.committed()
        view = self.view_of(state)
        owed = [r for r in view.provider_payload().get("HardRequirementCompliance") or []]
        self.assertEqual(["HRC-CND-A-%s" % constraint], [r["entity_id"] for r in owed])
        self.assertEqual((NYE, DOWN, "s05"), (owed[0]["status"], owed[0]["evaluation_point"],
                                              owed[0]["evidence_owner"]))
        self.assertEqual([constraint], [r["entity_id"] for r in
                                        view.provider_payload()["DesignConstraint"]])
        traces = [t for t in view.traces if t["entity_id"] == "HRC-CND-A-%s" % constraint]
        self.assertIn("hard_requirement_debt_to_carry", {t["requirement"] for t in traces})
        self.assertIn(cv.DEFERRED_TO_INVOKING_RESPONSIBILITY,
                      {t.get("applicability") for t in traces})
        text = s05.render_hard_requirements(view.provider_payload())
        self.assertIn("OWED", text)
        self.assertIn("HRC-CND-A-%s owes %s" % (constraint, constraint), text)
        self.assertIn("HONOUR", text)
        self.assertIn(constraint, text.split("OWED")[0])
        stage = S05Embodiment()
        prompt = stage.build_prompt({stage.context_key: view.provider_payload(),
                                     stage.occupancy_key: view.occupancy})
        self.assertIn("HRC-CND-A-%s owes" % constraint, prompt)

    def test_18_debt_owed_to_another_owner_is_not_routed_to_s05(self):
        state, constraint, _d = self.committed()
        later = self.constraint(state, "DSC-LATER", blocks=True)
        earlier = self.constraint(state, "DSC-EARLIER", blocks=True)
        self.hrc(state, "CND-A", later, NYE, DOWN, "s06")
        self.hrc(state, "CND-A", earlier, NYE, PRE, "s02")
        view = self.view_of(state)
        owed = [r["entity_id"] for r in view.provider_payload().get("HardRequirementCompliance") or []]
        self.assertEqual(["HRC-CND-A-%s" % constraint], owed)
        premised = {t["entity_id"] for t in view.traces
                    if t["requirement"] == "hard_requirement_debt_to_carry"}
        self.assertEqual({"HRC-CND-A-%s" % constraint}, premised)
        # every stated requirement is still shown as one to honour
        self.assertEqual({constraint, later, earlier},
                         {r["entity_id"] for r in view.provider_payload()["DesignConstraint"]})
        # the rule delegates to feasibility's one reading and adds only the owner
        source = _code(inspect.getsource(cv._deferred_to_invoking_responsibility))
        self.assertIn("compliance_deferred(", source)
        for literal in ("PRE_SELECTION", "DOWNSTREAM", "NOT_YET_EVALUABLE", "MATERIAL"):
            self.assertNotIn(literal, source, literal)

    def test_19_a_known_violation_is_never_deferred_work(self):
        state, _c, _d = self.committed()
        broken = self.constraint(state, "DSC-BROKEN", blocks=True)
        self.hrc(state, "CND-A", broken, VIO, DOWN, "s05")
        record = state.entities["HRC-CND-A-%s" % broken]
        self.assertFalse(s07.compliance_deferred(record))
        self.assertEqual(set(), cv._deferred_to_invoking_responsibility(
            {record["entity_id"]}, {"state": state, "contracts": state.c,
                                    "responsibility": "s05"}))
        view = self.view_of(state)
        self.assertNotIn(record["entity_id"],
                         [r["entity_id"] for r in view.provider_payload().get(
                             "HardRequirementCompliance") or []])

    def test_20_missing_evidence_never_becomes_satisfied(self):
        state, constraint, _d = self.committed()
        out, _ex, _p, _pr = self.embody(state)
        self.assertNotIn("HardRequirementCompliance",
                         {op.entity_type for op in out.patch.operations})
        record = self.compliance(state, "CND-A", constraint)
        self.assertEqual((NYE, STANDING), (record["status"], record["_validity"]))
        problems = state.validate(StagePatch(
            patch_id="probe", run_id=state.run_id, stage_id="s05", stage_attempt=3,
            parent_state_hash=state.state_hash(), execution_status="SUCCESS",
            provenance={"provider": "t"},
            operations=[Op("SUPERSEDE", "HardRequirementCompliance", record["entity_id"],
                           {"status": s07.SATISFIED}, "s05:embodiment", reason="probe")]))
        self.assertTrue(problems)
        self.assertEqual(NYE, self.compliance(state, "CND-A", constraint)["status"])
        # the stage's own words: it reads the debt and never writes or judges it
        source = _code(inspect.getsource(s05))
        self.assertIn('_rows(view, "HardRequirementCompliance")', source)
        for token in ('Op("CREATE", "HardRequirementCompliance"', '"SUPERSEDE"',
                      "SATISFIED", "evaluation_point", "compliance_blocks",
                      "compliance_deferred"):
            self.assertNotIn(token, source, token)


# =====================================================================
# E2 / E7 under revision, and the contracts
# =====================================================================
class TestLocalityAndContracts(_Handoff):

    def test_25_branch_locality_holds_across_a_revision(self):
        state, _c, old_decision = self.committed()
        self.embody(state)
        a_facts = {r["entity_id"] for r in self.s05_records(state)}
        self.revise_to(state, "CND-B")
        new_decision = state.standing("SelectionDecision")[0]["entity_id"]
        out, ex, _p, _pr = self.embody(state)
        self.assertTrue(ex.patch_applied, out.problems)
        self.assertEqual([], list(out.declared_incompleteness or []))
        b_facts = {r["entity_id"] for r in self.s05_records(state)
                   if r["_validity"] == STANDING}
        self.assertTrue(b_facts and not (b_facts & a_facts))
        for eid in b_facts:
            self.assertIn("CND-B", state.entities[eid]["_premises"])
            self.assertIn(new_decision, state.entities[eid]["_premises"])
            self.assertNotIn(old_decision, state.entities[eid]["_premises"])
        for eid in a_facts:
            self.assertEqual(STALE, self.validity(state, eid))
        bodies = {f["body"] for f in state.standing("Feature")}
        self.assertTrue(bodies and all(b.endswith("B") for b in bodies), bodies)

    def test_the_contracts_declare_the_handoff_once(self):
        resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")
        vocab = resp["instance_selection_vocabulary"]["applicability"]
        self.assertIn("DEFERRED_TO_INVOKING_RESPONSIBILITY", vocab)
        self.assertIn(cv.DEFERRED_TO_INVOKING_RESPONSIBILITY, cv.APPLICABILITY_RULES)
        self.assertEqual(["INVOCATION", "SELECTION_DECISION"],
                         resp["post_selection_consumer_declarations"]["branch_authority"]["values"])
        self.assertEqual(["FULL", "DECLARED_ONLY"],
                         resp["post_selection_consumer_declarations"]["provider_projection"]["values"])
        classes = {c["class"]: c for c in resp["stages"]["s05"]["required_reasoning_premise_classes"]}
        self.assertEqual(["hard_requirement_compliance"],
                         classes["hard_requirement_debt_to_carry"]["requires_semantics"])
        self.assertEqual(["design_constraint"],
                         classes["hard_requirement_to_honour"]["requires_semantics"])
        fams = Contracts().families
        self.assertIn("hard_requirement_compliance",
                      fams["HardRequirementCompliance"]["semantic_roles"])
        self.assertIn("interface", fams["Feature"]["optional_fields"])
        self.assertIn("obligation_duties", " ".join(fams["Obligation"]["rules"]))
        # no other post-selection consumer exists yet; nothing pre-selection declares these
        for sid, spec in resp["stages"].items():
            if sid != "s05":
                self.assertNotIn("branch_authority", spec, sid)
                self.assertNotIn("provider_projection", spec, sid)

    def test_the_s05_stage_contract_is_subordinate_and_canonical(self):
        doc = _paths.load_yaml(_paths.CONTRACTS + "/stages/S05_CONTRACT.yaml")
        status = doc["authority_status"]
        self.assertEqual("OPERATIONAL", status["structured_outputs"]["class"])
        self.assertEqual("OPERATIONAL", status["post_selection_handoff"]["class"])
        self.assertEqual("RETIRED", status["roi_rule"]["class"])
        self.assertFalse(any(v.get("authoritative_for_canonical_semantics")
                             for v in status.values()))
        fams = Contracts().families
        for family, fields in doc["structured_outputs"].items():
            with self.subTest(family):
                declared = set(fams[family]["required_fields"]) | set(
                    fams[family].get("optional_fields") or [])
                self.assertTrue(set(fields) <= declared, set(fields) - declared)
        text = json.dumps(doc)
        for legacy in ("rigid_group", "discharges_obligations", "ROI definitions"):
            self.assertNotIn(legacy, text, legacy)
        self.assertEqual([], doc["owned_decisions"]["extends"])
        self.assertIn("subordinate", status["post_selection_handoff"]["note"])

    def test_no_second_source_of_branch_or_timing_truth(self):
        # the stage resolves no branch of its own and reads no timing table
        source = _code(inspect.getsource(s05))
        for token in ("committed_branch(", "standing(\"SelectionDecision\")",
                      "evaluation_policy", "evaluation_timing", "\"kinds\""):
            self.assertNotIn(token, source, token)
        self.assertNotIn("consumer_view", S05Embodiment.__dict__,
                         "the stage keeps its own branch rule beside the builder's")
        # selection reads no timing table either
        for module in (sel, dec):
            self.assertNotIn("evaluation_policy", _code(inspect.getsource(module)))
        view_source = _code(inspect.getsource(cv))
        self.assertEqual(1, view_source.count("def committed_branch("))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
