"""Deterministic evidence for the 13 round-1 assembly questions.

Everything printed here is measured from the ACTUAL S07-compiled B-reps, posed
by the real pose law, or read from the design's own declarations. Nothing is
inferred from a picture and no repair advice is produced.
"""
import json, os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
from ver3.assy_v3.downstream import canonical_io, compiler, kinematics
import translate

OUT = os.environ["PILOT_OUT"]
PREFIX = os.environ.get("PILOT_PREFIX", "round1_")
plan = json.load(open(os.path.join(OUT, os.environ.get("PILOT_PLAN",
                                                       "round1_design_plan.json"))))


def volume(K, shape):
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def common_volume(K, a, b):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    op = BRepAlgoAPI_Common(a, b)
    op.Build()
    if not op.IsDone():
        return None
    return volume(K, op.Shape())


def gap(K, a, b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a, b)
    d.Perform()
    return d.Value() if d.IsDone() else None


def main():
    state, log = translate.main()
    assert log["accepted"], log
    from ver3.assy_v3.state.patch import StagePatch
    report, sparams = canonical_io.solve_from_state(state, translate.CID)
    ops = canonical_io.settlement_operations(report, sparams,
                                             canonical_io.evidence_identity(report))
    if ops:
        patch = StagePatch(patch_id="eval-s06", run_id=state.run_id, stage_id="s06",
                           stage_attempt=1, parent_state_hash=state.state_hash(),
                           operations=ops, execution_status="SUCCESS",
                           provenance={"purpose": "pilot settlement", "provider": None})
        problems = state.validate(patch)
        assert not problems, problems[:3]
        state.apply(patch)
    result = canonical_io.compile_from_state(state, out_dir=None, branch=translate.CID)
    K = compiler.kernel()
    ev = {"solver_status": report.solver_status, "s07_ok": result.ok,
          "bodies": [], "states": {}, "declared": {}, "findings": []}

    for b in result.bodies:
        ev["bodies"].append({"body": b.body_id, "solids": b.solid_count,
                             "volume_mm3": round(b.volume, 1)})

    art = getattr(result, "artifact", None)
    for f in (getattr(art, "findings", None) or []):
        ev["findings"].append({"code": getattr(f, "code", None),
                               "subject": getattr(f, "subject", None),
                               "detail": str(getattr(f, "detail", ""))[:200]})

    joints = [r for r in state.standing("Joint") if translate.CID in (r.get("_premises") or [])]
    groups = [r for r in state.standing("RigidGroup") if translate.CID in (r.get("_premises") or [])]
    states = [r for r in sorted(state.standing("State"), key=lambda x: x["entity_id"])
              if translate.CID in (r.get("_premises") or [])]
    values = canonical_io.resolved_values(state, translate.CID)
    scale = canonical_io.reference_scale(state, translate.CID)
    per_unit, _ = kinematics.scale_authority(
        scale, values, canonical_io.read_parameters(state, translate.CID))
    bodies = [b["entity_id"] for b in state.standing("Body")
              if translate.CID in (b.get("_premises") or [])]

    for st in states:
        hinge = (st.get("joint_coordinates") or {}).get("JNT-0002")
        word = "CLOSED" if hinge in (0, 0.0) else "OPEN"
        coords, _ = kinematics.coordinates_in_kernel_units(
            joints, st.get("joint_coordinates") or {}, per_unit)
        law = kinematics.derive_poses(joints, groups, coords, per_unit, bodies)
        posed = compiler.posed_shapes(K, result.bodies, law.poses)
        pairs = {}
        ids = sorted(posed)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                cv = common_volume(K, posed[a], posed[b])
                g = gap(K, posed[a], posed[b])
                pairs["%s|%s" % (a, b)] = {
                    "interpenetration_mm3": None if cv is None else round(cv, 2),
                    "closest_distance_mm": None if g is None else round(g, 3)}
        ev["states"][word] = {"state": st["entity_id"],
                              "joint_coordinates": st.get("joint_coordinates"),
                              "pairs": pairs}

    ev["declared"]["mating_sets"] = [
        {"name": m.get("name"), "purpose": m.get("purpose"),
         "upstream": m.get("upstream_relationships"),
         "participants": m.get("participants"),
         "fit": m.get("intended_fit"), "motion_after": m.get("motion_after_assembly")}
        for m in (plan.get("mating_sets") or [])]
    ev["declared"]["assembly_sequence"] = plan.get("assembly_sequence")
    ev["declared"]["state_expectations"] = plan.get("state_expectations")

    path = os.path.join(OUT, "%sassembly_evidence.json" % PREFIX)
    json.dump(ev, open(path, "w"), indent=1, default=str)
    print("wrote", path)
    print("solver:", ev["solver_status"], "| s07 ok:", ev["s07_ok"])
    for b in ev["bodies"]:
        print("  body %s: %d solid(s), %.1f mm3" % (b["body"], b["solids"], b["volume_mm3"]))
    for word, d in ev["states"].items():
        print(" ", word, d["joint_coordinates"])
        for k, v in d["pairs"].items():
            print("    %-24s overlap %-10s closest %s" % (k, v["interpenetration_mm3"],
                                                          v["closest_distance_mm"]))
    print("findings:", len(ev["findings"]))


if __name__ == "__main__":
    main()
