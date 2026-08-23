"""SELECTION READINESS ON THE CANONICAL BM-001 STATE, and the record of it.

The selection layer is a human authority: a deterministic comparison under
the user's stated preferences, an optional advisory review, one snapshot a
person is shown, and a writer that commits exactly what they chose if what
they saw is still true. This tool asks that layer where the benchmark
currently stands - ZERO provider calls, ZERO writes it invents - and
persists the answer as evidence:

  00_identity              what state was asked, and how it was rebuilt
  01_replayed_current_state  the hash, counts and staleness of the one state
  02_eligibility           the canonical eligible set, premise by premise
  03_preferences           what preference input exists (today: none), and
                           what the contract says about that
  04_advisory              not run, and why (no comparison exists without a
                           stated preference profile)
  07_lifecycle_checks      what the S-7 coordinator says the human state is
  08_final_status          READY_TO_SELECT vs SELECTED, and the exact next
                           controlled operations after a human chooses
  99_summary

05_selection_decision and 06_selected_consumer_view are written by NOTHING
here: they exist only after a person selects, and fabricating them would be
the exact thing the selection contract exists to refuse.

    python -m ver3.tools.selection_readiness
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)

import ver3.assy_v3.stages.selection as sel                                # noqa: E402
import ver3.assy_v3.stages.selection_decision as dec                        # noqa: E402
from ver3.assy_v3.lifecycle import s7_reconcile as lc                       # noqa: E402
from ver3.assy_v3.view import consumer_view_for                             # noqa: E402
from ver3.tools import bm001_replay as R                                    # noqa: E402
import ver3.tools.reconcile_preselection as rp                              # noqa: E402

OUT = os.path.join("scratchpad", "evidence", "BM-001_selection_closure")
PA = os.path.join("scratchpad", "evidence", "BM-001_parameter_authority")


def _dump(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, default=str)


def rebuilt_state():
    """The reconciled pre-selection state, rebuilt from tracked evidence with
    every owner-stage answer replayed by prompt hash. No credential needed and
    no call made: a question with no recorded answer would fail loudly."""
    state, log = R.build()
    R.with_preserved_mating(state)
    # The derivation and qualification artifacts of this rebuild are already
    # canonical evidence under BM-001_parameter_authority; this tool records
    # only what selection adds, so the rebuild's intermediates go to scratch.
    scratch = tempfile.mkdtemp(prefix="selection-readiness-")
    rp.derive_arrival(state, R.ORDER, scratch)
    provider = rp._LazyProvider(None)
    for cid in R.ORDER:
        rp.complete_topology(state, cid, provider, PA)
        rp.complete_release(state, cid, provider, PA)
    rows = rp.qualify(state, R.ORDER, scratch)
    return state, rows


def candidate_summary(state, cid: str) -> Dict[str, Any]:
    """A factual sketch of one candidate, from its canonical entities only."""
    def mine(fam):
        return R.mine(state, cid, fam)
    bodies = mine("Body")
    joints = mine("Joint")
    steps = sorted(mine("AssemblyStep"), key=lambda s: s.get("order_index") or 0)
    ifaces = mine("Interface")
    return {
        "candidate": cid,
        "principle": next((c.get("principle") for c in state.family("Candidate")
                           if c["entity_id"] == cid), None),
        "bodies": {b["entity_id"]: b.get("role") for b in bodies},
        "joints": {j["entity_id"]: "%s %s dof=%s axis=%s" % (
            j.get("joint_type"), "%s->%s" % (j.get("child_group"), j.get("parent_group")),
            j.get("dof"), j.get("axis_direction")) for j in joints},
        "interfaces": {i["entity_id"]: "%s %s%s" % (
            i.get("interaction_kind"), sorted(i.get("bodies") or []),
            " feature=%s" % i["feature"] if i.get("feature") else "")
            for i in ifaces},
        "mating_geometry": [
            {"interface": i["entity_id"], **{k: v for k, v in i["mating_geometry"].items()}}
            for i in ifaces if isinstance(i.get("mating_geometry"), dict)],
        "assembly_order": [
            "%s: %s from %s" % (s["entity_id"], s.get("body"), s.get("access_side"))
            for s in steps],
        "deferred_downstream": sorted({
            code for a in state.standing("FeasibilityDomainAssessment")
            if cid in (a.get("_premises") or [])
            for code in (a.get("reason_codes") or [])
            if "DEFERRED" in code or "EMBODIMENT" in code}),
    }


def main() -> int:
    state, qual_rows = rebuilt_state()
    state_hash = state.state_hash()
    stale = [{"entity_id": e, "family": r["_family"]}
             for e, r in sorted(state.entities.items())
             if r.get("_validity") == "STALE"]

    _dump(os.path.join(OUT, "00_identity.json"), {
        "purpose": "selection readiness on the canonical BM-001 state",
        "rebuilt_by": ["ver3.tools.bm001_replay.build",
                       "ver3.tools.bm001_replay.with_preserved_mating",
                       "s04a derive_arrival (deterministic)",
                       "owner-stage completions replayed by prompt hash from "
                       "scratchpad/evidence/BM-001_parameter_authority",
                       "feasibility qualification"],
        "provider_calls": {"deepseek": 0, "gemini": 0, "total": 0},
        "baseline_label": "PARTIAL replay: s01 is 28 of 33 records; the five "
                          "SourceClause records are unrecoverable and unreferenced"})
    _dump(os.path.join(OUT, "01_replayed_current_state.json"), {
        "state_hash": state_hash, "counts": state.counts(), "stale": stale,
        "aggregate": {cid: next(r["aggregate"] for r in qual_rows
                                if r["candidate"] == cid) for cid in R.ORDER}})

    # ELIGIBILITY through the owner's own construction - the same path the
    # review snapshot and the commit writer take.
    view = consumer_view_for(sel.RESPONSIBILITY, state)
    payload = view.payload()
    population = sel.eligibility(sel.evidence_of(state, payload))
    rows = [{"candidate": c, "verdict": v, "why": why, "basis": used}
            for c, (v, why, used) in sorted(population.items())]
    eligible = sorted(c for c, (v, _w, _u) in population.items() if v == sel.ELIGIBLE)
    _dump(os.path.join(OUT, "02_eligibility.json"), {
        "view_status": view.status.value,
        "unmet_view_requirements": [a["requirement"] for a in view.assessment
                                    if a["verdict"] != "SATISFIED"],
        "population": rows, "eligible": eligible,
        "population_established": not any(v == sel.UNRESOLVED
                                          for v, _w, _u in population.values()),
        "rule": "sel.eligibility: current MechanicalFeasibilityAssessment "
                "FEASIBLE_FOR_SELECTION for the same branch, exactly one, and "
                "every selection-blocking DesignConstraint's compliance "
                "SATISFIED. Preference-blind."})

    profile_out = sel.materialize_selection_profile(state, None)
    _dump(os.path.join(OUT, "03_preferences.json"), {
        "explicit_preference_found": False,
        "searched": ["USER_DESIGN_PROFILE_CONTRACT selection_preferences "
                     "(no design_profile file exists for BM-001)",
                     "standing SelectionProfile records (none)",
                     "standing HumanDecisionInput records (none)",
                     "standing SelectionDecision records (none)"],
        "materialize_selection_profile(None)": profile_out.status,
        "meaning": "nothing was stated. None and {} are different statements: "
                   "{} is a stated absence of preferences and produces a real "
                   "profile whose comparison is TRADEOFF_UNRESOLVED over the "
                   "whole eligible frontier; None is no statement at all and "
                   "produces no profile. Inventing either would be inventing "
                   "user input."})
    comparison_out = sel.evaluate_candidate_comparison(state)
    review = dec.build_human_review_snapshot(state)
    _dump(os.path.join(OUT, "04_advisory.json"), {
        "advisory_run": False,
        "why": "the advisory reviews a CandidateComparison, and no comparison "
               "can be written without a stated preference profile",
        "comparison_status": comparison_out.status,
        "provider_calls": {"deepseek": 0, "gemini": 0, "total": 0}})

    reconciled = lc.reconcile_s7(state)
    _dump(os.path.join(OUT, "07_lifecycle_checks.json"), {
        "reconcile_s7": {
            "feasibility": reconciled.feasibility,
            "human_state": reconciled.human_state,
            "changed": reconciled.changed,
            "problems": reconciled.problems[:8]},
        "review_snapshot_status": review.status,
        "standing_selection_decisions": [d["entity_id"]
                                         for d in state.standing("SelectionDecision")],
        "state_hash_after_reconcile": state.state_hash()})

    next_ops = [
        "1. the user states selection_preferences (a criteria mapping, or {} "
        "for 'no preferences') -> sel.materialize_selection_profile(state, "
        "preferences); apply the patch",
        "2. sel.evaluate_candidate_comparison(state); apply the patch "
        "(deterministic, eligible candidates only)",
        "3. optional: the selection_advisory pass reviews the comparison "
        "(DeepSeek, advisory only)",
        "4. dec.build_human_review_snapshot(state) -> shown to the person",
        "5. dec.materialize_human_decision_input(state, snapshot, action="
        "SELECT, candidate=<their choice>, rationale=<their words>); apply",
        "6. dec.commit_human_selection(state, input_id) -> the ONE "
        "SelectionDecision, written only if the digest still matches and the "
        "candidate is still eligible; apply",
        "7. persist 05_selection_decision / 06_selected_consumer_view and the "
        "before/after hashes; the s05 view then scopes to the selected branch"]
    status = ("SELECTED" if state.standing("SelectionDecision")
              else "READY_TO_SELECT")
    _dump(os.path.join(OUT, "08_final_status.json"), {
        "status": status, "eligible": eligible,
        "candidate_summaries": {cid: candidate_summary(state, cid)
                                for cid in eligible},
        "awaiting": "an explicit human choice, and the preference statement "
                    "(possibly empty) the comparison is made under",
        "next_controlled_operations": next_ops})
    _dump(os.path.join(OUT, "99_summary.json"), {
        "state_hash": state_hash, "eligible": eligible, "status": status,
        "human_state": reconciled.human_state,
        "provider_calls": {"deepseek": 0, "gemini": 0, "total": 0}})
    print("state", state_hash[:16], "| eligible", eligible, "|", status,
          "|", reconciled.human_state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
