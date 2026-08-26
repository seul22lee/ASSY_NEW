"""Render review PNGs directly from the existing CAD files. Nothing is healed,
redesigned or modified: each STEP is read, tessellated as-is, and drawn."""
import os, sys, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh

CAD = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
COLOURS = ("#2f6fb2", "#c9761a", "#3e8e5a", "#8a4fa0", "#b0413e")
VIEWS = {"isometric": (22, -60), "front": (0, -90), "side": (0, 0), "top": (89, -90)}
created = []


def read_step(path):
    reader = STEPControl_Reader()
    if reader.ReadFile(path) != IFSelect_RetDone:
        raise RuntimeError("could not read %s" % path)
    reader.TransferRoots()
    return reader.OneShape()


def solids(shape):
    out, exp = [], TopExp_Explorer(shape, TopAbs_SOLID)
    while exp.More():
        out.append(TopoDS.Solid_s(exp.Current()))
        exp.Next()
    return out or [shape]


def triangles(shape):
    BRepMesh_IncrementalMesh(shape, 0.8, False, 0.4, True)
    out, exp = [], TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            t = loc.Transformation()
            nodes = [tri.Node(i + 1).Transformed(t) for i in range(tri.NbNodes())]
            for i in range(tri.NbTriangles()):
                a, b, c = tri.Triangle(i + 1).Get()
                out.append([(nodes[a-1].X(), nodes[a-1].Y(), nodes[a-1].Z()),
                            (nodes[b-1].X(), nodes[b-1].Y(), nodes[b-1].Z()),
                            (nodes[c-1].X(), nodes[c-1].Y(), nodes[c-1].Z())])
        exp.Next()
    return out


def draw(parts, path, title, subtitle, view):
    elev, azim = VIEWS[view]
    fig = plt.figure(figsize=(10, 8), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    pts = []
    for i, (label, tris) in enumerate(parts):
        if not tris:
            continue
        pts.extend(p for t in tris for p in t)
        c = COLOURS[i % len(COLOURS)]
        ax.add_collection3d(Poly3DCollection(tris, alpha=0.45, facecolor=c,
                                             edgecolor=c, linewidths=0.15))
    if pts:
        arr = np.array(pts); lo, hi = arr.min(axis=0), arr.max(axis=0)
        mid, span = (lo + hi) / 2.0, max(hi - lo) / 2.0 or 1.0
        ax.set_xlim(mid[0]-span, mid[0]+span)
        ax.set_ylim(mid[1]-span, mid[1]+span)
        ax.set_zlim(mid[2]-span, mid[2]+span)
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.set_zlabel("Z (mm)")
    ax.view_init(elev=elev, azim=azim); ax.set_box_aspect((1, 1, 1))
    fig.suptitle(title, fontsize=14, fontweight="bold", x=0.02, ha="left")
    fig.text(0.02, 0.945, subtitle, fontsize=9, color="#6b7580")
    fig.text(0.02, 0.02, "SOURCE: read directly from the existing CAD file. Geometry is "
                         "unmodified; transparency is a drawing property.",
             fontsize=8, color="#6b7580")
    handles = [plt.Line2D([], [], color=COLOURS[i % len(COLOURS)], linewidth=6, label=l)
               for i, (l, _t) in enumerate(parts)]
    if handles:
        ax.legend(handles=handles, loc="upper right", fontsize=9)
    fig.savefig(path, dpi=140, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    created.append((path, view))
    print("png:", os.path.basename(path), flush=True)


bodies = sorted(glob.glob(os.path.join(CAD, "BOD-*.step")))
body_ids = [os.path.splitext(os.path.basename(p))[0] for p in bodies]

for asm in sorted(glob.glob(os.path.join(CAD, "assembly_*.step"))):
    state = os.path.splitext(os.path.basename(asm))[0].replace("assembly_", "")
    tag = state.replace("STA-", "")
    ss = solids(read_step(asm))
    labels = body_ids if len(ss) == len(body_ids) else \
        ["solid %d" % (i + 1) for i in range(len(ss))]
    parts = [(labels[i], triangles(s)) for i, s in enumerate(ss)]
    for view in VIEWS:
        draw(parts, os.path.join(OUT, "round1_%s_%s.png" % (tag, view)),
             "Round 1 assembly - %s" % state,
             "%s | %d solid(s) | source: %s" % (state, len(ss), os.path.basename(asm)),
             view)

for path, bid in zip(bodies, body_ids):
    parts = [(bid, triangles(read_step(path)))]
    draw(parts, os.path.join(OUT, "round1_%s_isometric.png" % bid),
         "Round 1 body - %s" % bid,
         "source: %s" % os.path.basename(path), "isometric")

print("TOTAL PNGS:", len(created))
