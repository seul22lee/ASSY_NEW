"""The S05 -> S06 -> S07 matrix harness. One scratch state per candidate.

The upstream is BM-001's, rebuilt deterministically. The SELECTION is synthetic
- a scratch commitment written by the real writer chain so s05 has a committed
branch to embody - and is labelled as such: it is not BM-001's decision.
"""
import json, os, sys, time, traceback
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rebuild import build
from ver3.assy_v3.downstream import canonical_io, duty_manifest, embodiment, execution as dex
from ver3.assy_v3.pipeline.progression import Progression, execute_stage
from ver3.assy_v3.stages import selection as SEL, selection_decision as SD
from ver3.assy_v3.stages.s05_embodiment import (S05Embodiment, carried_spatial_duties,
                                                outstanding_duties)
from ver3.assy_v3.view import InvocationContext


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, default=str)


def synthetic_selection(state, cid):
    """A scratch commitment through the REAL writer chain. Not BM-001's."""
    profile = SEL.materialize_selection_profile(state, {})
    if profile.patch is not None and not state.validate(profile.patch):
        state.apply(profile.patch)
    comparison = SEL.evaluate_candidate_comparison(state)
    if comparison.patch is not None and not state.validate(comparison.patch):
        state.apply(comparison.patch)
    row_eligible = list(getattr(comparison, "eligible", ()) or ())
    review = SD.build_human_review_snapshot(state)
    if review.snapshot is None:
        return None, {"stage": "review", "problems": list(review.problems or []),
                      "eligible": row_eligible}
    human = SD.materialize_human_decision_input(
        state, review.snapshot, "SELECT", cid,
        "scratch selection for the S05 authoring-boundary matrix; NOT BM-001's decision")
    if human.patch is None or state.validate(human.patch):
        return None, {"stage": "human_input", "status": human.status,
                      "problems": list(human.problems or [])
                      or (state.validate(human.patch) if human.patch else []),
                      "eligible": row_eligible}
    state.apply(human.patch)
    commit = SD.commit_human_selection(state, human.input_id)
    if commit.patch is None or state.validate(commit.patch):
        return None, {"stage": "commit", "status": commit.status,
                      "problems": list(commit.problems or [])
                      or (state.validate(commit.patch) if commit.patch else []),
                      "eligible": row_eligible}
    state.apply(commit.patch)
    return commit.decision_id, None


def _by_owner(findings):
    """Which stage owns each violated premise. s07 reports; it never repairs."""
    out = {}
    for f in findings:
        out.setdefault(f.get("owner") or "?", []).append(f.get("kind"))
    return {k: sorted(v) for k, v in sorted(out.items())}


def branch_rows(state, cid):
    return embodiment.rows_from_state(state, cid)


def run_candidate(cid, provider, out_dir, run_s06=True, run_s07=True):
    row = {"candidate": cid}
    state = build()
    row["upstream_state_hash"] = state.state_hash()

    decision, why = synthetic_selection(state, cid)
    row["selection"] = {"decision": decision, "problems": why}
    if decision is None:
        row["s05"] = {"status": "NOT_ATTEMPTED",
                      "reason": "no committed branch: %s" % json.dumps(why, default=str)}
        return row, state

    stage = S05Embodiment()
    view = stage.consumer_view(state, InvocationContext(branch=cid))
    row["view_status"] = view.status.value
    # THE STAGE'S OWN MANIFEST. Building a second one here from a hand-listed
    # family set is how the recorded duties came to be a shorter list than the
    # ones the prompt rendered and the boundary enforced.
    manifest = stage.duty_manifest({stage.context_key: view.provider_payload()})
    dump(os.path.join(out_dir, cid, "duty_manifest.json"), manifest.as_record())
    dump(os.path.join(out_dir, cid, "carried_spatial_duties.json"),
         carried_spatial_duties(manifest))
    # The S04 rows this branch is embodied against, so the review can draw the
    # arrangement the geometry is placed in.
    s04 = {fam: [r for r in state.standing(fam) if cid in (r.get("_premises") or [])]
           for fam in ("Body", "RigidGroup", "Envelope", "FunctionalRegion", "Joint",
                       "Interface", "PhysicalInteraction", "ConstraintRelation",
                       "Configuration", "State", "Transition", "SweptVolume",
                       "ReferenceScale", "MobilityExpectation", "TransitionRequirement")}
    s04 = {f: sorted(rows, key=lambda r: r["entity_id"]) for f, rows in s04.items() if rows}
    dump(os.path.join(out_dir, cid, "s04_state.json"),
         {"SOURCE": "accepted canonical DesignState (deterministic replay; zero provider calls)",
          "branch": cid, "state_hash": row["upstream_state_hash"],
          "counts": {f: len(r) for f, r in sorted(s04.items())}, "entities": s04})
    dump(os.path.join(out_dir, cid, "prompt.txt.json"),
         {"chars": len(stage.build_prompt({stage.context_key: view.provider_payload(),
                                           stage.occupancy_key: view.occupancy}))})
    with open(os.path.join(out_dir, cid, "prompt.txt"), "w") as fh:
        fh.write(stage.build_prompt({stage.context_key: view.provider_payload(),
                                     stage.occupancy_key: view.occupancy}))

    before = set(state.entities)
    progression = Progression()
    t0 = time.time()
    try:
        outcome, execution = execute_stage(stage, provider, state, progression,
                                           attempt=1, invocation=InvocationContext(branch=cid))
    except Exception:
        row["s05"] = {"status": "RAISED", "traceback": traceback.format_exc(limit=8)}
        return row, state
    elapsed = round(time.time() - t0, 1)
    raw = getattr(outcome, "raw_response", None) if outcome is not None else None
    if raw:
        with open(os.path.join(out_dir, cid, "raw_model_response.txt"), "w") as fh:
            fh.write(raw)
    if outcome is None:
        row["s05"] = {"status": "NO_OUTCOME", "elapsed_s": elapsed}
        return row, state

    created = sorted(set(state.entities) - before)
    by_family = {}
    for eid in created:
        fam = state.entities[eid]["_family"]
        by_family[fam] = by_family.get(fam, 0) + 1
    applied = bool(getattr(execution, "patch_applied", False))
    row["s05"] = {
        "status": outcome.execution_status.value,
        "elapsed_s": elapsed,
        "raw_chars": len(raw or ""),
        "patch_applied": applied,
        "problems": list(outcome.problems or []),
        "declared_incompleteness": list(outcome.declared_incompleteness or []),
        "entities_written": by_family,
        "duties_required": {"realization_targets": list(manifest.required_realization_targets()),
                            "interfaces": list(manifest.required_interfaces()),
                            "bodies": list(manifest.bodies)},
    }
    if not applied:
        row["s05"]["accepted"] = False
        row["s06"] = {"entered": False, "reason": "S05 was refused; nothing stands to settle"}
        row["s07"] = {"entered": False, "reason": "S06 not entered"}
        return row, state

    row["s05"]["accepted"] = True
    rows = branch_rows(state, cid)
    structural = embodiment.structural_problems(rows)
    outstanding = outstanding_duties(manifest, rows)
    ready, why_not = canonical_io.settlement_readiness(state, cid)
    row["s05"]["structural_problems"] = structural
    row["s05"]["outstanding_duties"] = outstanding
    row["s05"]["settlement_readiness"] = ready
    row["s05"]["settlement_readiness_why_not"] = why_not
    dump(os.path.join(out_dir, cid, "accepted_s05_state.json"),
         {fam: [ {k: v for k, v in r.items()} for r in rows.get(fam) or []]
          for fam in ("Feature", "Parameter", "Constraint", "KinematicRealization")})

    if not (run_s06 and ready):
        row["s06"] = {"entered": False,
                      "reason": "settlement_readiness == %s" % ready, "why_not": why_not}
        row["s07"] = {"entered": False, "reason": "S06 not entered"}
        return row, state

    report, s06exec = dex.execute_settlement(state, progression, branch=cid)
    row["s06"] = {"entered": True, "solver_status": report.solver_status,
                  "problems": list(report.problems or []),
                  "patch_applied": bool(getattr(s06exec, "patch_applied", False)),
                  "formulation_sha256": getattr(report, "formulation_sha256", None)}
    settled = {}
    for rec in sorted(state.standing("Parameter"), key=lambda r: r["entity_id"]):
        if cid in (rec.get("_premises") or []):
            settled[rec["entity_id"]] = {"symbol": rec.get("symbol"), "unit": rec.get("unit"),
                                         "status": rec.get("status"), "value": rec.get("value"),
                                         "solved_by": rec.get("solved_by")}
    row["s06"]["parameters"] = settled
    dump(os.path.join(out_dir, cid, "s06_settlement.json"), row["s06"])

    if not run_s07:
        row["s07"] = {"entered": False, "reason": "not requested"}
        return row, state

    cad_dir = os.path.join(out_dir, cid, "cad")
    os.makedirs(cad_dir, exist_ok=True)
    try:
        result, s07exec = dex.execute_compilation(state, progression, out_dir=cad_dir,
                                                  branch=cid)
        # THE EVIDENCE, NOT ONLY THE FILES. `CompileResult.ok` says the solids
        # built; the artifact report says whether they are the design. Reading
        # only the first is how a housing that buried its own aperture was
        # recorded as a success.
        report = getattr(result, "artifact", None) or {}
        blocking = [f for f in (report.get("findings") or [])
                    if f.get("evaluable") and f.get("kind") != "NOT_EVALUABLE"]
        row["s07"] = {"entered": True,
                      "compiled": bool(getattr(result, "ok", False)),
                      "bodies": [b.get("body_id") for b in
                                 (getattr(result, "as_record", lambda: {})().get("bodies") or [])],
                      "problems": [str(p) for p in (getattr(result, "problems", None) or [])],
                      "workable": bool(report.get("workable")),
                      "findings": report.get("findings") or [],
                      "blocking_findings": blocking,
                      "findings_by_owner": _by_owner(blocking),
                      "spatial_duties_judged": report.get("spatial_duties") or {},
                      "assembly": report.get("assembly") or {},
                      "patch_applied": bool(getattr(s07exec, "patch_applied", False)),
                      "artifacts": sorted(os.listdir(cad_dir)) if os.path.isdir(cad_dir) else []}
        dump(os.path.join(out_dir, cid, "s07_artifact_report.json"), report)
    except Exception:
        row["s07"] = {"entered": True, "status": "RAISED",
                      "traceback": traceback.format_exc(limit=8),
                      "artifacts": sorted(os.listdir(cad_dir)) if os.path.isdir(cad_dir) else []}
    return row, state
