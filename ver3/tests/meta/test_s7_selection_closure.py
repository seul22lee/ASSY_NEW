"""SELECTION FILTERS; IT NEVER RE-JUDGES, AND IT NEVER LEAKS A BRANCH.

Closure pins for the seams between the pre-selection maturity work and the
human selection authority - the invariants the two closures meet at:

  A DEFERRED OBLIGATION IS NOT A DISQUALIFICATION. Feasibility accepts a
  mating relation whose sizing is explicitly deferred to the embodiment
  block (MATING_RELATION_ESTABLISHED beside SIZING_DEFERRED_TO_EMBODIMENT)
  and aggregates FEASIBLE_FOR_SELECTION. Selection reads that aggregate and
  nothing finer: it does not know the reason codes exist, so it cannot
  reinterpret a deferral the evaluator already priced in - and a candidate
  carrying one is choosable through the whole authority chain.

  ONE BRANCH'S EVIDENCE AUTHORIZES ONE BRANCH. A current assessment naming
  candidate A leaves candidate B exactly where it was - unresolved - and an
  unresolved member makes the population unestablished, so nothing is
  compared and nothing can be chosen.

  SELECTION IS NOT DELETION, AND ITS WITHDRAWAL REACHES DOWNSTREAM. After a
  commitment the non-selected branch remains standing in canonical state,
  whole; and an artifact authored downstream ON the commitment loses
  standing with it, transitively, when the design moves underneath.
"""
from __future__ import annotations

import inspect
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.selection as sel                            # noqa: E402
import ver3.assy_v3.stages.selection_decision as dec                   # noqa: E402
from ver3.assy_v3.lifecycle import s7_reconcile as lc                  # noqa: E402
from ver3.assy_v3.state.patch import Op                                # noqa: E402
from .test_s04_mating_geometry import (                                 # noqa: E402
    PIN_IN_LID, arriving, geometry, pin_topology)
from .test_s7_feasibility import _group, arrangement, motion, realization  # noqa: E402
from .test_s7_lifecycle import _Lifecycle, STALE, STANDING              # noqa: E402


class _Closure(_Lifecycle):

    def deferred_pin_design(self):
        """Branch A: a pin nested in its lid, CLEARANCE declared, sizes
        representative - FEASIBLE with the fit explicitly deferred to the
        embodiment block. Branch B: the ordinary four-bar."""
        state = self.seed()
        self.candidates(state, suffixes=("A", "B"))
        r = arriving(realization("A", steps=(0, 1)), (0, 1, 0), index=1)
        r["assembly_steps"][1]["order_index"] = 2
        arr = arrangement(PIN_IN_LID, steps=["ASY-0A", "ASY-1A"])
        arr["mating_geometry"] = [geometry()]
        self.hinge(state, sfx="A", s03a=pin_topology("CLEARANCE", "+Y"), s03b=r,
                   s04a=arr, s04b=motion("A", "JNT-0A", _group(1, "A")))
        self.fourbar(state)
        return self.feasible(state)


# =====================================================================
# O - a deferral feasibility accepted is not selection's to reopen
# =====================================================================
class TestDeferredSizingStaysSelectable(_Closure):

    def test_O1_a_deferred_fit_candidate_is_eligible(self):
        state = self.deferred_pin_design()
        deferred = [a for a in state.standing("FeasibilityDomainAssessment")
                    if "CND-A" in (a.get("_premises") or [])
                    and "SIZING_DEFERRED_TO_EMBODIMENT" in (a.get("reason_codes") or [])]
        self.assertTrue(deferred, "the probe is not probing: nothing was deferred")
        population = sel.eligibility(self.evidence(state))
        verdict, why, used = population["CND-A"]
        self.assertEqual(sel.ELIGIBLE, verdict, why)
        # The basis is the aggregate and the facts eligibility read - never
        # the domain records whose codes carry the deferral.
        self.assertFalse(set(a["entity_id"] for a in deferred) & set(used),
                         "eligibility read the domain records behind the aggregate")

    def test_O2_and_choosable_through_the_whole_authority_chain(self):
        state = self.deferred_pin_design()
        out = self.profile(state, {})
        self.assertIsNotNone(out.patch)
        cmp_out = self.compare(state)
        self.assertEqual(sel.COMPARISON_WRITTEN, cmp_out.status, cmp_out.problems)
        committed = self.decide(state, "CND-A",
                                "the deferred sizing is embodiment's, priced in")
        self.assertEqual(dec.SELECTION_COMMITTED, committed.status,
                         committed.problems)
        self.assertEqual("CND-A",
                         self.committed_decision(state)["selected_candidate"])

    def test_O3_selection_cannot_even_see_the_deferral(self):
        """Structural: no selection module knows the reason-code vocabulary,
        the domain-assessment family, or any fit semantics. What feasibility
        accepted cannot be re-judged by code that cannot read it."""
        import ver3.assy_v3.stages.selection_advisory as adv
        for module in (sel, dec, adv, lc):
            source = inspect.getsource(module)
            for token in ("SIZING_DEFERRED", "reason_codes",
                          "FeasibilityDomainAssessment", "mating_fit",
                          "mating_geometry"):
                self.assertNotIn(token, source,
                                 "%s reads %r" % (module.__name__, token))


# =====================================================================
# N - one branch's evidence authorizes one branch
# =====================================================================
class TestBranchLocalEvidence(_Closure):

    def test_N1_an_assessment_for_A_leaves_B_unresolved(self):
        state = self.design()
        self.assess(state, "CND-A")            # only A is qualified
        population = sel.eligibility(self.evidence(state))
        self.assertEqual(sel.ELIGIBLE, population["CND-A"][0])
        verdict, why, _used = population["CND-B"]
        self.assertEqual(sel.UNRESOLVED, verdict)
        self.assertIn("no current feasibility assessment", why)

    def test_N2_an_unestablished_population_compares_nothing(self):
        state = self.design()
        self.assess(state, "CND-A")
        self.profile(state, {})
        out = sel.evaluate_candidate_comparison(state)
        self.assertEqual(sel.ELIGIBILITY_NOT_ESTABLISHED, out.status, out.status)
        self.assertIsNone(out.patch)
        self.assertEqual([], state.family("CandidateComparison"))


# =====================================================================
# selection is not deletion, and its withdrawal reaches downstream
# =====================================================================
class TestCommitmentReachAndRetention(_Closure):

    def test_R1_the_non_selected_branch_remains_whole(self):
        state, _decision = self.committed("CND-A")
        self.assertEqual({"CND-A", "CND-B"},
                         {c["entity_id"] for c in state.standing("Candidate")})
        b_local = [e for e, r in state.entities.items()
                   if "CND-B" in (r.get("_premises") or [])]
        self.assertTrue(b_local, "the probe is not probing")
        withdrawn = [e for e in b_local
                     if self.validity(state, e) not in (STANDING,)]
        self.assertEqual([], withdrawn,
                         "selection withdrew the non-selected branch")

    def test_R2_a_downstream_artifact_on_the_commitment_stales_with_it(self):
        """The other half of one-downstream-branch: geometry authored ON the
        decision follows the decision. Move the design, reconcile - the
        commitment reopens, and the artifact premised on it has no standing
        left to borrow."""
        state, decision = self.committed("CND-A")
        self.revise(state, Op("CREATE", "Feature", "FEA-CLOSURE-1",
                              {"body": "BOD-G0A", "feature_kind": "BOSS",
                               "geometry": {"centre": [0, 0, 0],
                                            "half_extent": [1, 1, 1]}},
                              "s05:embodiment",
                              premise_refs=["CND-A", decision]), stage="s05")
        self.assertEqual(STANDING, self.validity(state, "FEA-CLOSURE-1"))
        self.replace_envelope(state)
        self.reconcile(state)
        self.assertEqual(STALE, self.validity(state, decision))
        self.assertEqual(STALE, self.validity(state, "FEA-CLOSURE-1"),
                         "downstream geometry outlived the commitment it was "
                         "authored on")
        self.assertIsNone(lc.current_commitment(state))


if __name__ == "__main__":
    unittest.main()
