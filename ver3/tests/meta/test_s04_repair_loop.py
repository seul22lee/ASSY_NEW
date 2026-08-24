"""UNIT B: S04 REALIZES, CHECKS, AND REPAIRS WHAT IT REALIZED - BOUNDED.

    realize -> check -> diagnose -> repair -> re-check

The check is the feasibility responsibility answering again over current
state; the diagnosis is the REPAIRABLE_S04 class its domain records carry
(Unit A); the repair is the owning s04 pass revising values it owns - by
derivation where it can, by a re-invocation with REPAIR CONTEXT where it must;
the re-check is the same evaluator again. The loop applies the owner's patches
and records what happened. It owns no truth and decides nothing.

WHAT THESE TESTS ARE GUARDING

    A REPAIRABLE_S04 finding triggers a revision of what stands, through the
    boundary's own operations, and is re-checked. The previous value is kept;
    what rested on it goes stale; the new evaluation is written beside the old.

    Deterministic first: what a derivation can repair is never asked of a model.

    Bounded and honest: a cycle or an exhausted budget leaves open obligations
    and never INFEASIBLE; nothing asks twice and keeps the better answer.

    The loop touches nothing but REPAIRABLE_S04: unsupported, deferred,
    owner-revisable and required-minimum findings are left exactly as found.

    One candidate's repair touches no other candidate; selection is untouched.

Synthetic mechanisms throughout. No product noun, no benchmark id.
"""
from __future__ import annotations

import copy
import inspect
import json
import re
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.pipeline import progression                          # noqa: E402
from ver3.assy_v3.pipeline import repair as prog                       # noqa: E402
from ver3.assy_v3.stages.base import REPAIR_KEY                        # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion)
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from ver3.assy_v3.view import InvocationContext                         # noqa: E402
from .test_s02_s03b_integration import _Canned                          # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, topology)
from .test_s7_human_decision import _code                               # noqa: E402
from .test_s7_mfa_viability import chain_probe                          # noqa: E402
from .test_s04_mating_geometry import _Mating, geometry                 # noqa: E402

APART = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]), "BOD-G1A": ([9, 0, 0], [1, 1, 1])}


class _Refusing:
    """A provider that must not be asked. Asking it is the failure."""

    def __init__(self):
        self.calls = 0

    def capabilities(self):
        raise AssertionError("the provider was asked")

    def generate(self, request, attempt_index=0):
        self.calls += 1
        raise AssertionError("the provider was asked")


class _Recording(_Canned):
    """A canned provider that also keeps every prompt it was sent."""

    def __init__(self, *payloads):
        super().__init__(*payloads)
        self.prompts = []

    def generate(self, request, attempt_index=0):
        self.prompts.append(request.prompt_text)
        return super().generate(request, attempt_index)


class _Loop(_Feas):

    def inv(self, sfx="A"):
        return InvocationContext(branch="CND-%s" % sfx)

    def repair(self, state, provider, rounds=2, sfx="A"):
        p = progression.Progression()
        out = prog.s04_repair_rounds(provider, state, p, self.inv(sfx), rounds=rounds)
        return out, p

    def mfas(self, state, cid="CND-A"):
        return sorted(((e, r["_validity"], r["status"]) for e, r in state.entities.items()
                       if r["_family"] == "MechanicalFeasibilityAssessment"
                       and r.get("candidate") == cid))

    def current_mfa(self, state, cid="CND-A"):
        found = [m for m in state.standing("MechanicalFeasibilityAssessment")
                 if m.get("candidate") == cid]
        self.assertEqual(1, len(found), found)
        return found[0]

    def repairable(self, state, cid="CND-A"):
        out = s07.evaluate_candidate_feasibility(state, cid)
        return sorted((r["domain"], r["code"]) for v in out.verdicts
                      for r in s07.classify(v)[0] if r["class"] == s07.REPAIRABLE_S04)

    def apart(self):
        return self.hinge(s04a=arrangement(APART, steps=["ASY-0A"]))


# =====================================================================
# 1 - a repairable finding triggers a revision, and it is re-checked
# =====================================================================
class TestRepairTriggersRevision(_Loop):

    def test_a_placement_finding_is_repaired_by_s04a_and_rechecked(self):
        state = self.apart()
        self.assertIn(("load_reaction_closure", "HOP_BODIES_APART"), self.repairable(state))
        provider = _Recording(arrangement(HINGE_BOXES, steps=["ASY-0A"]))
        out, p = self.repair(state, provider)
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        self.assertEqual([], out.open)
        self.assertEqual("FEASIBLE_FOR_SELECTION", out.feasibility)
        # the owning pass was invoked once, with the findings as its context
        self.assertEqual(1, provider.calls)
        self.assertEqual(("s04a",), out.rounds[0].invoked)
        self.assertIn("REPAIR ROUND 1", provider.prompts[0])
        self.assertIn("HOP_BODIES_APART", provider.prompts[0])
        self.assertIn("WHAT YOU MAY NOT DO", provider.prompts[0])
        # and the check after the repair is the canonical evaluator
        self.assertTrue([e for e in p.deterministic if e.responsibility_id == "feasibility"])
        self.assertEqual([], self.repairable(state))

    def test_the_revised_value_is_superseded_and_history_kept(self):
        state = self.apart()
        before = copy.deepcopy(state.entities["ENV-G1A"]["extent"])
        self.repair(state, _Canned(arrangement(HINGE_BOXES, steps=["ASY-0A"])))
        env = state.entities["ENV-G1A"]
        self.assertEqual("STANDING", env["_validity"])
        self.assertNotEqual(before, env["extent"])
        self.assertEqual(1, len(env["_superseded"]))
        self.assertEqual(before, env["_superseded"][0]["prior_value"])
        self.assertIn("repair round 1", env["_superseded"][0]["reason"])
        self.assertIn("HOP_BODIES_APART", env["_superseded"][0]["reason"])
        # the unmoved body's extent was restated unchanged and records nothing
        self.assertNotIn("_superseded", state.entities["ENV-G0A"])

    def test_old_evidence_goes_stale_and_the_new_evaluation_is_written_beside_it(self):
        state = self.apart()
        first = self.current_mfa(state) if state.standing("MechanicalFeasibilityAssessment") \
            else None
        self.assertIsNone(first)
        self.repair(state, _Canned(arrangement(HINGE_BOXES, steps=["ASY-0A"])))
        rows = self.mfas(state)
        validities = {v for _e, v, _s in rows}
        self.assertIn("STANDING", validities)
        self.assertTrue(validities & {"STALE", "INVALIDATED"}, rows)
        self.assertEqual("FEASIBLE_FOR_SELECTION", self.current_mfa(state)["status"])
        # the first answer over the apart arrangement is still readable
        earliest = min(rows)
        self.assertEqual("NOT_ESTABLISHED", state.entities[earliest[0]]["status"])
        self.assertNotEqual("STANDING", earliest[1])
        # the occupancy computed over the old extent lost standing and was recomputed
        swept = {e: r["_validity"] for e, r in state.entities.items()
                 if r["_family"] == "SweptVolume"}
        self.assertIn("STALE", swept.values())
        self.assertIn("STANDING", swept.values())

    def test_a_realization_finding_is_repaired_by_s04b_as_one_coherent_set(self):
        state = self.hinge(s04b=motion("A", "JNT-0A", _group(1, "A"), changed=[]))
        self.assertIn(("motion_and_transitions", "UNDECLARED_COORDINATE_CHANGE"),
                      self.repairable(state))
        provider = _Recording(motion("A", "JNT-0A", _group(1, "A")))
        out, _p = self.repair(state, provider)
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        self.assertEqual(("s04b",), out.rounds[0].invoked)
        self.assertIn("UNDECLARED_COORDINATE_CHANGE", provider.prompts[0])
        realization = {e: r["_validity"] for e, r in state.entities.items()
                       if r["_family"] in ("State", "Transition", "SweptVolume")}
        self.assertEqual("INVALIDATED", realization["STA-CFG-C0A"])
        self.assertEqual("INVALIDATED", realization["TRN-A"])
        self.assertEqual("STANDING", realization["STA-CFG-C0A-R1"])
        self.assertEqual("STANDING", realization["TRN-A-R1"])
        self.assertEqual("STANDING", realization["SWV-TRN-A-R1-RGP-G1A"])
        self.assertEqual(["JNT-0A"], state.entities["TRN-A-R1"]["changed_coordinates"])
        self.assertEqual("STA-CFG-C0A-R1", state.entities["TRN-A-R1"]["from_state"])
        self.assertEqual("FEASIBLE_FOR_SELECTION", self.current_mfa(state)["status"])

    def test_a_model_local_negative_is_a_repair_signal_the_owner_answers(self):
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"], eliminated=True))
        self.assertIn(("spatial_realization", s07.MODEL_LOCAL_NEGATIVE), self.repairable(state))
        out, _p = self.repair(state, _Canned(arrangement(HINGE_BOXES, steps=["ASY-0A"])))
        self.assertEqual(prog.SETTLED, out.status)
        self.assertFalse(state.entities["ELM-CND-A"]["eliminated"])
        self.assertTrue(state.entities["ELM-CND-A"].get("_superseded"))
        self.assertEqual([], self.current_mfa(state)["open_obligations"])


# =====================================================================
# 2 - deterministic first, and never a model for what a derivation repairs
# =====================================================================
class TestDeterministicFirst(_Loop):

    def test_an_insertion_direction_is_re_derived_without_a_provider(self):
        state = self.hinge()
        self.revise(state, Op("SUPERSEDE", "AssemblyStep", "ASY-0A",
                              {"insertion_direction": [0, 1, 0]}, "t",
                              reason="a vector that is not the motion from +Z"),
                    stage="s04")
        self.assertIn(("assemblability", "INSERTION_DIRECTION_CONTRADICTS_ACCESS_SIDE"),
                      self.repairable(state))
        provider = _Refusing()
        out, p = self.repair(state, provider)
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        self.assertEqual(0, provider.calls)
        self.assertEqual(("s04a",), out.rounds[0].deterministic)
        self.assertEqual((), out.rounds[0].invoked)
        self.assertEqual([0.0, 0.0, -1.0],
                         [float(x) for x in state.entities["ASY-0A"]["insertion_direction"]])
        self.assertEqual([], self.repairable(state))

    def test_a_missing_computable_occupancy_is_recomputed_without_a_provider(self):
        state = self.hinge()
        for v in state.standing("SweptVolume"):
            self.revise(state, Op("INVALIDATE", "SweptVolume", v["entity_id"], {}, "t",
                                  reason="withdrawn by a probe"), stage="s04")
        self.assertIn(("spatial_realization", "OCCUPANCY_NOT_COMPUTED"), self.repairable(state))
        out, _p = self.repair(state, _Refusing())
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        self.assertEqual(("s04b",), out.rounds[0].deterministic)
        standing = [v["entity_id"] for v in state.standing("SweptVolume")]
        self.assertEqual(["SWV-TRN-A-RGP-G1A-D1"], standing)
        self.assertIn("TRN-A", state.entities[standing[0]]["_premises"])

    def test_the_loop_is_beside_the_progression_and_invokes_through_it(self):
        """The producing progression stops at S04 (a frozen scope rule) and owns
        the one acceptance rule for a stage's patch. The loop lives beside it,
        invokes every pass through `execute_stage`, and applies only the
        deterministic, owner-authored feasibility and derivation patches."""
        chain = inspect.getsource(progression)
        self.assertNotIn("evaluate_candidate_feasibility", chain)
        self.assertNotIn("s04_repair_rounds", _code(chain))
        loop = _code(inspect.getsource(prog))
        self.assertIn("execute_stage(", loop)
        self.assertNotIn("stage.invoke(", loop)
        self.assertNotIn("provider.generate(", loop)

    def test_derivation_precedes_invocation_within_a_round(self):
        source = inspect.getsource(prog.s04_repair_rounds)
        self.assertLess(source.index("_deterministic_repairs("),
                        source.index("execute_stage("))


# =====================================================================
# 3 - bounded, honest, and never a verdict
# =====================================================================
class TestBoundedAndHonest(_Loop):

    def test_the_same_findings_again_is_a_cycle_that_leaves_open_obligations(self):
        state = self.apart()
        provider = _Recording(arrangement(APART, steps=["ASY-0A"]))   # restates the defect
        out, p = self.repair(state, provider, rounds=3)
        self.assertEqual(prog.CYCLE, out.status, out.as_record())
        self.assertEqual(1, provider.calls, "a cycle was looped on")
        self.assertEqual(2, len(out.rounds) + 1)
        self.assertIn("HOP_BODIES_APART", {o["code"] for o in out.open})
        mfa = self.current_mfa(state)
        self.assertEqual("NOT_ESTABLISHED", mfa["status"])
        self.assertNotEqual("INFEASIBLE", mfa["status"])
        self.assertNotIn("physical_argument", mfa)
        self.assertTrue(any("cycle" in f["what"] for f in p.failures))

    def test_an_exhausted_budget_leaves_open_obligations_not_infeasible(self):
        state = self.apart()
        nearer = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]), "BOD-G1A": ([5, 0, 0], [1, 1, 1])}
        out, _p = self.repair(state, _Canned(arrangement(nearer, steps=["ASY-0A"])), rounds=1)
        self.assertEqual(prog.BUDGET_EXHAUSTED, out.status, out.as_record())
        self.assertEqual(1, len(out.rounds))
        self.assertIn("HOP_BODIES_APART", {o["code"] for o in out.open})
        # what the last revision left derivable was derived before the final check
        self.assertNotIn("OCCUPANCY_NOT_COMPUTED", {o["code"] for o in out.open})
        self.assertEqual([5, 0, 0], state.entities["ENV-G1A"]["extent"]["centre"])
        mfa = self.current_mfa(state)
        self.assertEqual("NOT_ESTABLISHED", mfa["status"])
        self.assertTrue({"HOP_BODIES_APART", "CONNECTED_BODIES_APART"}
                        <= {b["code"] for b in mfa["blocking_findings"]})

    def test_no_provider_means_derivations_only_and_the_rest_stays_open(self):
        state = self.apart()
        out, _p = self.repair(state, None)
        self.assertEqual(prog.NO_PROVIDER, out.status)
        self.assertIn("HOP_BODIES_APART", {o["code"] for o in out.open})
        self.assertEqual([9, 0, 0], state.entities["ENV-G1A"]["extent"]["centre"])

    def test_a_repair_that_does_not_land_ends_the_loop_and_changes_nothing(self):
        """An answer the boundary refuses - an extent for a body this branch does
        not have - lands nothing, is recorded, and ends the loop. (An answer
        that parses but states nothing is a different case: it is CONTRACT_
        INCOMPLETE, applied as such, and the unchanged findings are a cycle.)"""
        state = self.apart()
        bad = arrangement(dict(APART, **{"BOD-NOWHERE": ([0, 0, 0], [1, 1, 1])}),
                          steps=["ASY-0A"])
        out, p = self.repair(state, _Canned(bad))
        self.assertEqual(prog.REPAIR_FAILED, out.status, out.as_record())
        self.assertTrue(out.rounds[0].problems)
        # the failed invocation is recorded and nothing of it reached the state
        self.assertEqual([9, 0, 0], state.entities["ENV-G1A"]["extent"]["centre"])
        self.assertTrue(p.failures)

    def test_no_favourable_retry(self):
        """One invocation per pass per round, taken whatever it says. Nothing
        compares answers, keeps a better one, or asks again."""
        source = _code(inspect.getsource(prog))
        loop = _code(inspect.getsource(prog.s04_repair_rounds)).lower()
        for word in ("best", "max_attempts", "retry", "compare(", "score"):
            self.assertNotIn(word, loop, word)
        state = self.apart()
        provider = _Recording(arrangement(HINGE_BOXES, steps=["ASY-0A"]))
        out, _p = self.repair(state, provider, rounds=2)
        self.assertEqual(1, provider.calls)
        self.assertEqual(1, len([r for r in out.rounds if r.invoked]))
        # and a settings object with more than one attempt never reaches the call
        self.assertNotIn("GenerationSettings", source.split("def s04_repair_rounds")[1]
                         .split("def execute_s01_to_s04")[0])

    def test_exhaustion_writes_no_argument_and_the_status_is_the_minimum_s(self):
        """A candidate whose only defect is repairable and unrepaired is exactly
        as feasible as Unit A says: NOT_ESTABLISHED where the finding negates
        the minimum, FEASIBLE with an obligation where it does not."""
        state = self.hinge(s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"], eliminated=True))
        out, _p = self.repair(state, _Canned(arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                                          eliminated=True)), rounds=1)
        self.assertEqual(prog.BUDGET_EXHAUSTED, out.status, out.as_record())
        mfa = self.current_mfa(state)
        self.assertEqual("FEASIBLE_FOR_SELECTION", mfa["status"])
        self.assertIn(s07.MODEL_LOCAL_NEGATIVE, {o["code"] for o in mfa["open_obligations"]})


# =====================================================================
# 4 - what the loop does not touch
# =====================================================================
class TestOnlyRepairableIsTouched(_Loop):

    def test_unsupported_composite_motion_is_left_exactly_as_found(self):
        """The probe carries an UNSUPPORTED occupancy and one repairable sweep
        finding. With no provider the loop derives what it can - nothing, for
        a composition - and stops: the unsupported row is not in what it left
        open, no s04 patch was written, and the finding stands as found."""
        state = chain_probe(self)
        s04_before = {e: json.dumps(r, sort_keys=True, default=str)
                      for e, r in state.entities.items() if r.get("_created_by") == "s04"}
        out, p = self.repair(state, None)
        self.assertEqual(prog.NO_PROVIDER, out.status, out.as_record())
        self.assertNotIn(s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION,
                         {o["code"] for o in out.open})
        s04_after = {e: json.dumps(r, sort_keys=True, default=str)
                     for e, r in state.entities.items() if r.get("_created_by") == "s04"}
        self.assertEqual(s04_before, s04_after, "an s04 record moved with no provider")
        self.assertIn(s07.OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION,
                      {o["code"] for o in self.current_mfa(state)["open_obligations"]})
        # nothing was derivable: the only repairable row is a sweep finding an
        # owner pass would answer, so no derivation ran and none was recorded
        self.assertEqual({"feasibility"}, {e.responsibility_id for e in p.deterministic})
        self.assertEqual({"SWEEP_MEETS_UNDECLARED_BODY"}, {o["code"] for o in out.open})

    def test_a_required_minimum_absence_is_not_a_repair(self):
        state = self.hinge(s03b=realization("A", terminates=None))
        out, _p = self.repair(state, _Refusing())
        self.assertEqual(prog.SETTLED, out.status)
        self.assertEqual("NOT_ESTABLISHED", self.current_mfa(state)["status"])

    def test_the_trigger_is_the_class_and_never_the_status(self):
        source = inspect.getsource(prog._repairable_findings)
        self.assertIn('== REPAIRABLE_S04', source)
        for status in ("FEASIBLE_FOR_SELECTION", "NOT_ESTABLISHED", "INFEASIBLE",
                       "v.status", "blocking_findings", "open_obligations"):
            self.assertNotIn(status, source, status)
        self.assertEqual("REPAIRABLE_S04", prog.REPAIRABLE_S04)


class TestDeferredIsNotTouched(_Mating):

    def test_a_deferred_obligation_is_not_a_repair(self):
        state = self.pin(geometry())
        p = progression.Progression()
        out = prog.s04_repair_rounds(_Refusing(), state, p,
                                     InvocationContext(branch="CND-A"), rounds=2)
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        mfa = [m for m in state.standing("MechanicalFeasibilityAssessment")][0]
        self.assertIn("SIZING_DEFERRED_TO_EMBODIMENT", {o["code"] for o in mfa["open_obligations"]})


# =====================================================================
# 5 - branch-local, and selection untouched
# =====================================================================
class TestBranchLocalAndSelectionUntouched(_Loop):

    def test_one_candidates_repair_touches_no_other_candidate(self):
        state = self.apart()
        self.fourbar(state=state)
        other = {e: json.dumps(r, sort_keys=True, default=str)
                 for e, r in state.entities.items()
                 if "CND-B" in (r.get("_premises") or []) or e.endswith("B")}
        self.assertTrue(other, "the probe is not probing")
        out, _p = self.repair(state, _Canned(arrangement(HINGE_BOXES, steps=["ASY-0A"])))
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        after = {e: json.dumps(r, sort_keys=True, default=str)
                 for e, r in state.entities.items() if e in other}
        self.assertEqual(other, after, "another candidate's record moved")

    def test_every_write_is_the_owners(self):
        state = self.apart()
        before = {e: json.dumps(r, sort_keys=True, default=str) for e, r in state.entities.items()}
        out, p = self.repair(state, _Canned(arrangement(HINGE_BOXES, steps=["ASY-0A"])))
        self.assertEqual(prog.SETTLED, out.status, out.as_record())
        # every execution the loop caused is an s04 pass or the feasibility evaluator
        self.assertEqual({"s04"}, {e.stage_id for e in p.executions})
        self.assertEqual({"s04", "feasibility"}, {e.stage_id for e in p.deterministic})
        # and every record that moved carries one of those two authorities
        for eid, rec in state.entities.items():
            if before.get(eid) == json.dumps(rec, sort_keys=True, default=str):
                continue
            acts = ([rec.get("_created_by")]
                    + [x["stage"] for x in rec.get("_superseded", [])]
                    + [x["stage"] for x in rec.get("_invalidations", [])]
                    + [x["stage"] for x in rec.get("_extensions", [])])
            self.assertTrue(set(acts) <= {"s04", "feasibility"}, (eid, acts))
            self.assertNotIn(rec["_family"], ("SelectionDecision", "CandidateComparison",
                                              "SelectionProfile", "HumanDecisionInput",
                                              "Candidate", "Body", "Joint", "Interface"))

    def test_selection_knows_nothing_of_repair(self):
        import ver3.assy_v3.stages.selection as sel
        import ver3.assy_v3.stages.selection_decision as dec
        from ver3.assy_v3.lifecycle import s7_reconcile as lc
        for module in (sel, dec, lc):
            source = _code(inspect.getsource(module))
            for token in ("repair", "REPAIR_KEY", "s04_repair_rounds", "from ..pipeline",
                          "import pipeline"):
                self.assertNotIn(token, source, "%s reads %r" % (module.__name__, token))

    def test_no_benchmark_or_candidate_is_named(self):
        for module in (prog, s04):
            self.assertIsNone(re.search(r"\bBM-\d|\bCND-\d", inspect.getsource(module)),
                              module.__name__)


# =====================================================================
# 6 - the revision rule, and the contracts that state it
# =====================================================================
class TestRevisionRule(_Loop):

    def test_unchanged_is_nothing_changed_is_superseded_absent_is_extended(self):
        state = self.hinge()
        env = state.entities["ENV-G0A"]
        ops = [Op("CREATE", "Envelope", "ENV-G0A",
                  {k: v for k, v in env.items() if not k.startswith("_") and k != "entity_id"},
                  "p"),
               Op("CREATE", "Envelope", "ENV-G1A",
                  {"body": "BOD-G1A", "extent": {"half_extent": [2, 2, 2], "centre": [1.5, 0, 0]},
                   "frame": "world", "maturity": "PROVISIONAL"}, "p"),
               Op("EXTEND", "AssemblyStep", "ASY-0A", {"insertion_direction": [0, 0, -1]}, "p"),
               Op("EXTEND", "Joint", "JNT-0A", {"frame_origin": [1, 1, 1]}, "p"),
               Op("CREATE", "Envelope", "ENV-NEW", {"body": "BOD-G0A", "extent": {},
                                                   "frame": "world", "maturity": "PROVISIONAL"}, "p")]
        out = s04.re_realize_operations(state, ops, "why")
        kinds = [(o.kind, o.entity_id, sorted(o.fields)) for o in out]
        self.assertEqual([("SUPERSEDE", "ENV-G1A", ["extent"]),
                          ("SUPERSEDE", "JNT-0A", ["frame_origin"]),
                          ("CREATE", "ENV-NEW", ["body", "extent", "frame", "maturity"])], kinds)
        self.assertTrue(all(o.reason == "why" for o in out if o.kind == "SUPERSEDE"))

    def test_a_retired_realization_is_invalidated_not_deleted(self):
        state = self.hinge()
        out = s04.re_realize_operations(state, [], "why", retire=[("State", "STA-CFG-C0A")])
        self.assertEqual([("INVALIDATE", "STA-CFG-C0A")], [(o.kind, o.entity_id) for o in out])

    def test_a_repair_keeps_the_scale(self):
        state = self.apart()
        changed = arrangement(HINGE_BOXES, steps=["ASY-0A"], basis="ABSOLUTE",
                              absolute={"unit": "mm", "per_unit": 2.0})
        out, _p = self.repair(state, _Canned(changed))
        self.assertEqual("RELATIVE", state.entities["SCL-CND-A"]["basis"])
        self.assertNotIn("_superseded", state.entities["SCL-CND-A"])

    def test_the_prompt_states_the_boundary(self):
        for stage in (S04AEnvelopeAndReach(), S04BPlacementAndMotion()):
            text = s04.repair_context_text(
                {REPAIR_KEY: {"round": 1, "findings": [{"domain": "d", "code": "C"}],
                              "current": {}}}, stage.REPAIR_MAY_REVISE)
            self.assertIn("WHAT YOU MAY NOT DO", text)
            for word in ("body", "joint", "interface", "configuration", "principle",
                         "scale basis"):
                self.assertIn(word, text)
        self.assertEqual("", s04.repair_context_text({}, "x"))

    def test_the_contracts_state_the_lifecycle(self):
        c = _paths.load_yaml(_paths.CONTRACTS + "/stages/S04_CONTRACT.yaml")
        life = c["repair_lifecycle"]
        for key in ("trigger", "deterministic_first", "owner_reinvocation",
                    "how_a_revision_is_recorded", "bound", "ending"):
            self.assertIn(key, life)
        self.assertIn("REPAIRABLE_S04", life["trigger"])
        self.assertIn("NO FAVOURABLE RETRY", life["bound"])
        self.assertIn("never INFEASIBLE by exhaustion", life["ending"])
        self.assertEqual("OPERATIONAL", c["authority_status"]["repair_lifecycle"]["class"])
        resp = _paths.contract("STAGE_RESPONSIBILITY_CONTRACT.yaml")["stages"]
        for sid in ("s04a", "s04b"):
            prohibited = " ".join(resp[sid]["prohibited_decisions"])
            self.assertIn("In a repair", prohibited)
            self.assertIn("REPAIRABLE_S04", prohibited)
        for stage in (S04AEnvelopeAndReach, S04BPlacementAndMotion):
            for code in stage.DERIVED_REPAIRS:
                self.assertEqual(s07.REPAIRABLE_S04,
                                 s07.classification()["codes"][code]["class"], code)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
