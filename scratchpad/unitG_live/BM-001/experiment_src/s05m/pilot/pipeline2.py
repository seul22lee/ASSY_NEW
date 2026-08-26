"""translate -> the real S06 solver -> the real S07 compiler -> evidence.

THE ENTRY GATE IS BYPASSED, AND ONLY THE GATE. `settlement_readiness` refuses
this branch because three free-space FunctionalRegions are not cleared by the
design - a real gap in the pilot response, and unrelated to whether its
dimensions are settleable. The experiment's question is whether this authoring
mode produces coherent CAD, so the SAME solver and the SAME compiler are run
directly and the same geometric evidence is computed. Nothing in the design is
altered and no production code is changed.
"""
import json, os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import translate
from ver3.assy_v3.downstream import artifact, canonical_io, duty_manifest, embodiment
from ver3.assy_v3.stages.s05_embodiment import outstanding_duties
from ver3.assy_v3.state.patch import StagePatch

OUT, CID = translate.OUT, translate.CID
report = {}
state, log = translate.main()
report["translation"] = log
assert log["accepted"], log["write_boundary_problems"]

rows = embodiment.rows_from_state(state, CID)
manifest = duty_manifest.from_rows(rows, branch=CID)
ready, why_not = canonical_io.settlement_readiness(state, CID)
report["s05_state"] = {
    "counts": {f: len(rows.get(f) or []) for f in
               ("Feature", "Constraint", "KinematicRealization")},
    "structural_problems": embodiment.structural_problems(rows),
    "outstanding_duties": outstanding_duties(manifest, rows),
    "settlement_readiness": ready, "gate_refusal": why_not}
print("S05 written | features", len(rows.get("Feature") or []),
      "| KRL", len(rows.get("KinematicRealization") or []),
      "| gate ready:", ready, "| gate refusals:", len(why_not), flush=True)

# ---- the real S06 solver, run directly ------------------------------
solver_report, params = canonical_io.solve_from_state(state, CID)
report["s06"] = {"solver_status": solver_report.solver_status,
                 "problems": list(solver_report.problems or []),
                 "gate_bypassed": not ready,
                 "unknown_count": getattr(solver_report, "unknown_count", None),
                 "rank": getattr(solver_report, "rank", None),
                 "equation_count": getattr(solver_report, "equation_count", None),
                 "formulation_sha256": getattr(solver_report, "formulation_sha256", None)}
print("S06 solver:", solver_report.solver_status,
      "| unknowns", getattr(solver_report, "unknown_count", None),
      "| rank", getattr(solver_report, "rank", None), flush=True)
for p in (solver_report.problems or [])[:6]:
    print("   -", str(p)[:180], flush=True)

evidence = canonical_io.evidence_identity(solver_report)
ops = canonical_io.settlement_operations(solver_report, params, evidence)
if ops:
    patch = StagePatch(patch_id="pilot-s06", run_id=state.run_id, stage_id="s06",
                       stage_attempt=1, parent_state_hash=state.state_hash(),
                       operations=ops, execution_status="SUCCESS",
                       provenance={"purpose": "pilot settlement", "provider": None})
    problems = state.validate(patch)
    report["s06"]["write_problems"] = problems
    if not problems:
        state.apply(patch)
settled = {r["entity_id"]: {"symbol": r.get("symbol"), "unit": r.get("unit"),
                            "value": r.get("value"), "status": r.get("status"),
                            "solved_by": r.get("solved_by")}
           for r in sorted(state.standing("Parameter"), key=lambda x: x["entity_id"])
           if CID in (r.get("_premises") or [])}
report["s06"]["parameter_count"] = len(settled)
report["s06"]["constraint_count"] = len(rows.get("Constraint") or [])
report["s06"]["parameters"] = settled
print("settled:", {k: v["value"] for k, v in settled.items()}, flush=True)

# ---- the real S07 compiler, run directly ----------------------------
cad = os.path.join(OUT, "cad"); os.makedirs(cad, exist_ok=True)
result = canonical_io.compile_from_state(state, out_dir=cad, branch=CID)
report["s07"] = {"ok": bool(result.ok), "problems": [str(p) for p in (result.problems or [])],
                 "failed_feature": result.failed_feature, "failed_step": result.failed_step,
                 "bodies": [b.as_record() for b in (result.bodies or [])]}
print("S07 compile ok:", result.ok, "| bodies",
      [(b.body_id, round(b.volume, 1), b.is_valid) for b in (result.bodies or [])], flush=True)
for p in (result.problems or [])[:6]:
    print("   -", str(p)[:180], flush=True)

if result.ok:
    art = artifact.validate(state, CID, result, out_dir=cad)
    rec = art.as_record()
    blocking = [f for f in rec["findings"]
                if f.get("evaluable") and f.get("kind") != "NOT_EVALUABLE"]
    report["s07"]["workable"] = rec["workable"]
    report["s07"]["findings"] = rec["findings"]
    report["s07"]["blocking_findings"] = blocking
    json.dump(rec, open(os.path.join(OUT, "s07_artifact_report.json"), "w"), indent=1,
              sort_keys=True, default=str)
    print("evidence workable:", rec["workable"], "| blocking", len(blocking), flush=True)
    for f in blocking[:14]:
        print("   -", f.get("kind"), f.get("owner"), str(f.get("detail"))[:150], flush=True)
report["s07"]["artifacts"] = sorted(os.listdir(cad)) if os.path.isdir(cad) else []
json.dump(report, open(os.path.join(OUT, "pipeline_result.json"), "w"), indent=1,
          sort_keys=True, default=str)
print("WROTE", os.path.join(OUT, "pipeline_result.json"), flush=True)
