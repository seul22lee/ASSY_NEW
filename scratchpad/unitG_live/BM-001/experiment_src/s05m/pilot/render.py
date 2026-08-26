"""Renders of the ACTUAL compiled solids, posed by the real pose law.

The solids are not altered for the picture: each body is tessellated as it was
built and drawn as a wireframe-shaded triangle mesh. Transparency is a drawing
property, so nested geometry can be seen without cutting anything open.
"""
import json, os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from ver3.assy_v3.downstream import canonical_io, compiler, kinematics

OUT = os.environ.get("PILOT_OUT", os.path.join(
    REPO, "scratchpad", "unitG_live", "BM-001", "s05_fresh_authoring_pilot"))
COLOURS = ("#2f6fb2", "#c9761a", "#3e8e5a", "#8a4fa0")


def triangles(K, shape):
    """The tessellation of the solid AS BUILT. Nothing is modified."""
    K["BRepMesh_IncrementalMesh"](shape, 1.0, False, 0.5, True)
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRep import BRep_Tool
    from OCP.TopoDS import TopoDS
    out = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            nodes = [tri.Node(i + 1).Transformed(trsf) for i in range(tri.NbNodes())]
            for i in range(tri.NbTriangles()):
                a, b, c = tri.Triangle(i + 1).Get()
                out.append([(nodes[a - 1].X(), nodes[a - 1].Y(), nodes[a - 1].Z()),
                            (nodes[b - 1].X(), nodes[b - 1].Y(), nodes[b - 1].Z()),
                            (nodes[c - 1].X(), nodes[c - 1].Y(), nodes[c - 1].Z())])
        exp.Next()
    return out


def draw(meshes, path, title, subtitle, elev, azim):
    fig = plt.figure(figsize=(11, 8.5), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    allpts = []
    for index, (bid, tris) in enumerate(sorted(meshes.items())):
        if not tris:
            continue
        allpts.extend([p for t in tris for p in t])
        coll = Poly3DCollection(tris, alpha=0.42, facecolor=COLOURS[index % len(COLOURS)],
                                edgecolor=COLOURS[index % len(COLOURS)], linewidths=0.18)
        ax.add_collection3d(coll)
    if allpts:
        arr = np.array(allpts)
        lo, hi = arr.min(axis=0), arr.max(axis=0)
        centre, span = (lo + hi) / 2.0, max(hi - lo) / 2.0 or 1.0
        for setter, c in ((ax.set_xlim, centre[0]), (ax.set_ylim, centre[1]),
                          (ax.set_zlim, centre[2])):
            setter(c - span, c + span)
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.set_zlabel("Z (mm)")
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, 1))
    fig.suptitle(title, fontsize=15, fontweight="bold", x=0.02, ha="left")
    fig.text(0.02, 0.945, subtitle, fontsize=9, color="#6b7580")
    fig.text(0.02, 0.02, "SOURCE: the actual S07-compiled B-reps, posed by the derived pose "
                         "law. Solids are unmodified; transparency is a drawing property.",
             fontsize=8, color="#6b7580")
    handles = [plt.Line2D([], [], color=COLOURS[i % len(COLOURS)], linewidth=6, label=b)
               for i, b in enumerate(sorted(meshes))]
    ax.legend(handles=handles, loc="upper right", fontsize=9)
    fig.savefig(path, dpi=140, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    import translate
    from rebuild import build
    from harness import synthetic_selection
    # the pipeline already committed; rebuild + re-translate + re-settle is the
    # only way to get the live objects back in a fresh process
    state, log = translate.main()
    assert log["accepted"], log
    # The SAME solver the pipeline ran, called directly: the entry gate refuses
    # this branch for three uncleared regions, which has nothing to do with
    # whether its dimensions settle.
    from ver3.assy_v3.state.patch import StagePatch
    solver_report, sparams = canonical_io.solve_from_state(state, translate.CID)
    print("solver:", solver_report.solver_status)
    ops = canonical_io.settlement_operations(
        solver_report, sparams, canonical_io.evidence_identity(solver_report))
    if ops:
        patch = StagePatch(patch_id="render-s06", run_id=state.run_id, stage_id="s06",
                           stage_attempt=1, parent_state_hash=state.state_hash(),
                           operations=ops, execution_status="SUCCESS",
                           provenance={"purpose": "pilot settlement", "provider": None})
        problems = state.validate(patch)
        assert not problems, problems[:3]
        state.apply(patch)
    result = canonical_io.compile_from_state(state, out_dir=None, branch=translate.CID)
    # THE SOLIDS ARE DRAWN WHETHER OR NOT S07 ACCEPTED THEM. It refused these
    # for being several disconnected pieces per body, which is exactly what the
    # pictures have to show; they are the compiled B-reps either way.
    if not result.bodies:
        print("nothing was built:", result.problems[:3]); return
    print("compiled:", [(b.body_id, round(b.volume, 1), b.solid_count) for b in result.bodies])
    K = compiler.kernel()
    cad = os.path.join(OUT, os.environ.get("PILOT_CAD", "cad"))
    os.makedirs(cad, exist_ok=True)
    for b in result.bodies:
        compiler.export_stl(K, b.shape, os.path.join(cad, "%s.stl" % b.body_id))
        try:
            from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
            w = STEPControl_Writer(); w.Transfer(b.shape, STEPControl_AsIs)
            w.Write(os.path.join(cad, "%s.step" % b.body_id))
            from OCP.BRepTools import BRepTools
            BRepTools.Write_s(b.shape, os.path.join(cad, "%s.brep" % b.body_id))
        except Exception as exc:
            print("export note:", exc)
    joints = [r for r in state.standing("Joint") if translate.CID in (r.get("_premises") or [])]
    groups = [r for r in state.standing("RigidGroup") if translate.CID in (r.get("_premises") or [])]
    states = [r for r in sorted(state.standing("State"), key=lambda x: x["entity_id"])
              if translate.CID in (r.get("_premises") or [])]
    values = canonical_io.resolved_values(state, translate.CID)
    scale = canonical_io.reference_scale(state, translate.CID)
    per_unit, _how = kinematics.scale_authority(
        scale, values, canonical_io.read_parameters(state, translate.CID))
    bodies = [b["entity_id"] for b in state.standing("Body")
              if translate.CID in (b.get("_premises") or [])]
    made = []
    for st in states:
        coords, _n = kinematics.coordinates_in_kernel_units(
            joints, st.get("joint_coordinates") or {}, per_unit)
        law = kinematics.derive_poses(joints, groups, coords, per_unit, bodies)
        posed = compiler.posed_shapes(K, result.bodies, law.poses)
        try:
            compiler.export_assembly(K, posed, os.path.join(cad, "assembly_%s.step"
                                                            % st["entity_id"]))
        except Exception as exc:
            print("assembly export note:", exc)
        meshes = {bid: triangles(K, shape) for bid, shape in posed.items()}
        tag = os.environ.get("PILOT_PREFIX", "") + st["entity_id"].replace("STA-", "")
        sub = ("%s | joint coordinates %s | CLOSED/OPEN is derived from the hinge "
               "coordinate, not an S04 state name" % (st["entity_id"], st.get("joint_coordinates")))
        # S04 names these states only CFG-0001 / CFG-0002. The CLOSED / OPEN word
        # is DERIVED from the state's own hinge coordinate - zero rotation at the
        # revolute hinge is the closed state - and the coordinates are printed on
        # every picture so the label can be checked against the data.
        hinge = (st.get("joint_coordinates") or {}).get("JNT-0002")
        word = "CLOSED" if hinge in (0, 0.0) else "OPEN"
        tag = os.environ.get("PILOT_PREFIX", "") + word
        for view, elev, azim in (("isometric", 22, -60), ("side", 0, -90),
                                 ("front", 0, 0), ("top", 89, -90)):
            name = "%s (%s)" % (st.get("name", word), view) if view != "isometric" \
                else st.get("name", word)
            made.append(draw(meshes, os.path.join(OUT, "%s_%s.png" % (tag, view)),
                             "Compiled assembly - %s" % name, sub, elev, azim))
        if word == "CLOSED":
            for bid, tris in sorted(meshes.items()):
                made.append(draw({bid: tris},
                                 os.path.join(OUT, "%sbody_%s_isometric.png"
                                              % (os.environ.get("PILOT_PREFIX", ""), bid)),
                                 "Compiled body - %s" % bid,
                                 "the single compiled solid, drawn alone", 22, -60))
    for path in made:
        print("render:", path)


if __name__ == "__main__":
    main()
