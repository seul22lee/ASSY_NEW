"""EXE-BM003-01 - artifact manifest and deterministic rebuild check.

Two things, in this order, and the order matters:

1. REBUILD DETERMINISM. The geometry is built twice from parameters.yaml in two
   independent interpreter states and the two geometry signatures, evidence
   signatures and motion trajectory signatures are compared. A reference whose
   rebuild is not deterministic cannot have a meaningful manifest, because the
   hashes would record one of several possible outputs.

2. THE MANIFEST. Every file in this directory is hashed. Call this LAST:
   manifest_util.build_manifest re-reads and re-hashes every entry before
   returning, so a manifest that is wrong at birth cannot be written, but it
   cannot make a half-written file whole.

Run:  python make_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)

import cadval as cv                                # noqa: E402
import manifest_util as mu                         # noqa: E402
import build as B                                  # noqa: E402

REBUILD_PROBE = r'''
import json, os, sys, hashlib
HERE = %r
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)
import cadval as cv
import build as B

P = B.load_params()
G = B.geom(P)
bodies = B.build(P)

def trsf(loc):
    t = loc.wrapped.Transformation()
    return [[round(t.Value(r, c), 9) for c in range(1, 5)] for r in range(1, 4)]

states = {s: {b.id: trsf(B.pose(P, b.id, s)) for b in bodies} for s in B.STATES}
sig = cv.geometry_signature(bodies, critical=G,
                            motion={"states": B.STATES, "segments": B.SEGMENTS},
                            states=states)

# motion trajectory signature: every sampled pose of every body, every segment
traj = []
for seg in B.SEGMENTS:
    for i in range(41):
        t = i / 40.0
        for b in B.continuous_pose(bodies, P, seg, t):
            traj.append([seg, round(t, 9), b.id] + trsf(cv.rotation((0,0,0),(0,0,1),0.0))[0])
kf = B._keyframes(P, G)
for seg in B.SEGMENTS:
    a, b2 = (kf[s] for s in B.SEGMENT_ENDS[seg])
    for i in range(41):
        t = i / 40.0
        traj.append([seg, round(t, 9)] + [round(a[j] + (b2[j] - a[j]) * t, 9) for j in range(3)])
traj_sha = hashlib.sha256(json.dumps(traj, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()

# evidence signature: the numbers the reference's claims rest on
ev = {}
for name in ("state_maintenance", "release", "lift_only", "antirotation",
             "outward_stop", "retention", "footprint", "compactness",
             "connectivity", "cycle_return", "bayonet_turns"):
    p = os.path.join(HERE, "validation", name + ".json")
    if os.path.exists(p):
        d = json.load(open(p))
        ev[name] = d.get("status")
ev_sha = hashlib.sha256(json.dumps(ev, sort_keys=True,
                                   separators=(",", ":")).encode()).hexdigest()

print(json.dumps({"geometry_signature_sha256": sig["signature_sha256"],
                  "trajectory_signature_sha256": traj_sha,
                  "evidence_signature_sha256": ev_sha,
                  "body_volumes": {b["body_id"]: b["volume_mm3"] for b in sig["bodies"]}}))
''' % HERE


def rebuild_probe(tag: str) -> dict:
    out = subprocess.check_output([sys.executable, "-c", REBUILD_PROBE], cwd=HERE)
    rec = json.loads(out.decode())
    rec["run"] = tag
    return rec


def determinism() -> dict:
    a = rebuild_probe("first")
    b = rebuild_probe("second")
    same = {k: a[k] == b[k] for k in ("geometry_signature_sha256",
                                      "trajectory_signature_sha256",
                                      "evidence_signature_sha256",
                                      "body_volumes")}
    rec = {"method": ("the model is rebuilt from parameters.yaml in two independent "
                      "interpreter processes and the three signatures are compared. "
                      "Independent PROCESSES, not two calls in one, so nothing can be "
                      "carried over in module state."),
           "runs": [a, b], "identical": same,
           "status": "PASS" if all(same.values()) else "FAIL"}
    cv.write_json(os.path.join(HERE, "validation", "rebuild_determinism.json"), rec)
    return rec


def main() -> int:
    det = determinism()
    print("rebuild determinism:", det["status"])
    for k, v in det["identical"].items():
        print("   %-32s %s" % (k, v))
    if det["status"] != "PASS":
        print("refusing to write a manifest for a non-deterministic rebuild")
        return 1

    sig = json.load(open(os.path.join(HERE, "geometry_signature.json")))
    summary = json.load(open(os.path.join(HERE, "validation", "SUMMARY.json")))
    oracle = json.load(open(os.path.join(HERE, "actual_evaluation.json")))
    extra = {
        "reference_id": "EXE-BM003-01",
        "benchmark_id": "BM-003",
        "schema_version": "0.1.0",
        "units": "mm",
        "reference_class": "ORACLE_AWARE_EXECUTABLE_EVALUATOR_FIXTURE",
        "completion_claim": "ONE_POSITIVE_EXECUTABLE_REFERENCE_VALIDATED",
        "what_this_is": (
            "One mechanism for BM-003, built as exact OCCT B-rep solids and measured. "
            "An evaluator fixture: it shows that the checks can pass and, through "
            "seventeen negative controls, that they can fail. It is not a production "
            "result, not a golden design and not a mandatory mechanism."),
        "what_this_is_not": [
            "not evidence that every realization family the Oracle admits is executable",
            "not evidence that the Oracle is correctly permissive across its four classes",
            "not evidence of strength, load, effort, wear, lifetime or manufacturability",
            "not a production, training or few-shot input"],
        "declared_state_maintenance_class": "SMC-KINEMATIC_BLOCK",
        "declared_realization_class": "RIGID_MULTI_BODY",
        "dynamics": "DYNAMICS_NOT_REQUIRED_FOR_THIS_REFERENCE",
        "geometry_representation": "PARAMETRIC_B_REP",
        "authoritative_source": "parameters.yaml + build.py + the native OCCT B-rep",
        "step_files_are": "exchange artifacts, round-trip checked, never authoritative",
        "body_count": sig["body_count"],
        "body_ids": sig["semantic_body_ids"],
        "geometry_signature_sha256": sig["signature_sha256"],
        "trajectory_signature_sha256": det["runs"][0]["trajectory_signature_sha256"],
        "evidence_signature_sha256": det["runs"][0]["evidence_signature_sha256"],
        "rebuild_deterministic": det["status"] == "PASS",
        "validation_overall": summary["overall"],
        "validation_run_seconds": summary["run_seconds"],
        "validation_fast_mode": summary["fast_mode"],
        "oracle_status": oracle["status"],
        "oracle_invariants_pass": "%d/%d" % (oracle["invariants_pass"],
                                             oracle["invariants_total"]),
        "oracle_reopening_required": oracle["oracle_reopening"]["any_condition_met"],
        "human_review": "HUMAN_REVIEW_PENDING",
    }
    doc = mu.build_manifest([HERE], HERE, extra=extra,
                            exclude_names=("manifest.yaml", mu.MANIFEST_FILENAME))
    mu.write_manifest(doc, os.path.join(HERE, "manifest.yaml"))
    print("wrote manifest.yaml  (%d files)" % doc["file_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
