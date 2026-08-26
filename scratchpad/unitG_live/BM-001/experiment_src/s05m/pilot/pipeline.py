"""translate -> S06 -> S07 -> renders, in one pass over one rebuilt state."""
import json, os, sys, traceback
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import translate
from ver3.assy_v3.downstream import canonical_io, embodiment, execution as dex
from ver3.assy_v3.pipeline.progression import Progression
from ver3.assy_v3.stages.s05_embodiment import outstanding_duties
from ver3.assy_v3.downstream import duty_manifest

OUT = translate.OUT
CID = translate.CID
report = {}

state, log = translate.main()
report["translation"] = log
if not log["accepted"]:
    json.dump(report, open(os.path.join(OUT, "pipeline_result.json"), "w"), indent=1,
              sort_keys=True, default=str)
    print("STOP: translation refused at the write boundary"); sys.exit(0)

rows = embodiment.rows_from_state(state, CID)
manifest = duty_manifest.from_rows(rows, branch=CID)
structural = embodiment.structural_problems(rows)
duties = outstanding_duties(manifest, rows)
ready, why_not = canonical_io.settlement_readiness(state, CID)
report["s05_state"] = {
    "counts": {f: len(rows.get(f) or []) for f in
               ("Feature", "Constraint", "KinematicRealization")},
    "structural_problems": structural, "outstanding_duties": duties,
    "settlement_readiness": ready, "why_not": why_not}
print("structural:", len(structural), "| duties:", len(duties), "| ready:", ready, flush=True)
for p in (structural + duties)[:12]:
    print("   -", str(p)[:170], flush=True)

progression = Progression()
solver_report, s06exec = dex.execute_settlement(state, progression, branch=CID)
params = {r["entity_id"]: {"symbol": r.get("symbol"), "unit": r.get("unit"),
                           "value": r.get("value"), "status": r.get("status"),
                           "solved_by": r.get("solved_by")}
          for r in sorted(state.standing("Parameter"), key=lambda x: x["entity_id"])
          if CID in (r.get("_premises") or [])}
report["s06"] = {"solver_status": solver_report.solver_status,
                 "problems": list(solver_report.problems or []),
                 "patch_applied": bool(getattr(s06exec, "patch_applied", False)),
                 "parameter_count": len(params),
                 "constraint_count": len(rows.get("Constraint") or []),
                 "parameters": params}
print("S06:", solver_report.solver_status, "| params", len(params),
      "| constraints", len(rows.get("Constraint") or []), flush=True)
for p in (solver_report.problems or [])[:6]:
    print("   -", str(p)[:170], flush=True)

cad = os.path.join(OUT, "cad")
os.makedirs(cad, exist_ok=True)
result, s07exec = dex.execute_compilation(state, progression, out_dir=cad, branch=CID)
art = getattr(result, "artifact", None) or {}
blocking = [f for f in (art.get("findings") or [])
            if f.get("evaluable") and f.get("kind") != "NOT_EVALUABLE"]
report["s07"] = {"ok": bool(getattr(result, "ok", False)),
                 "problems": [str(p) for p in (result.problems or [])],
                 "bodies": [b.as_record() for b in (result.bodies or [])],
                 "workable": art.get("workable"),
                 "findings": art.get("findings") or [],
                 "blocking_findings": blocking,
                 "artifacts": sorted(os.listdir(cad)) if os.path.isdir(cad) else []}
print("S07 ok:", getattr(result, "ok", False), "| bodies",
      [b.body_id for b in (result.bodies or [])],
      "| blocking findings", len(blocking), flush=True)
for f in blocking[:10]:
    print("   -", f.get("kind"), f.get("owner"), str(f.get("detail"))[:160], flush=True)
json.dump(art, open(os.path.join(OUT, "s07_artifact_report.json"), "w"), indent=1,
          sort_keys=True, default=str)
json.dump(report, open(os.path.join(OUT, "pipeline_result.json"), "w"), indent=1,
          sort_keys=True, default=str)
print("WROTE", os.path.join(OUT, "pipeline_result.json"), flush=True)
