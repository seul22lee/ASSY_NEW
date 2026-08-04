"""Shared build and validation library for the Ver3 CAD pilot.

Everything a reference needs in order to make a claim about its own geometry
lives here, so that two references make their claims the same way and a reader
can check the method once.

Design rules this module enforces by construction:

* Every body is a B-rep solid and is checked with BRepCheck_Analyzer. Meshes are
  produced only for rendering and never for measurement.
* Overlap is measured as the VOLUME of the boolean common, not inferred from a
  distance query. A distance of zero is contact; a positive common volume is
  penetration, and the two are different questions.
* Bodies carry stable semantic IDs. OCCT face indices are never used as the
  persistent identity of a feature.
* Nothing here decides a PASS. It computes numbers; the reference's
  expected_evaluation.yaml states what those numbers have to be, and the
  predicate evaluator compares them.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import cadquery as cq
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepTools import BRepTools
from OCP.GProp import GProp_GProps
from OCP.TopoDS import TopoDS_Shape

MM = "mm"
ROUND = 6


# --------------------------------------------------------------------- bodies
@dataclass
class Body:
    """A rigid B-rep solid with a stable semantic identity."""
    id: str
    name: str
    material_class: str
    shape: cq.Shape
    role: str = ""
    installed_as: str = "DISCRETE"     # DISCRETE | CO_FORMED | PERMANENT_JOIN
    notes: str = ""

    def moved(self, loc: cq.Location) -> "Body":
        return Body(self.id, self.name, self.material_class, self.shape.moved(loc),
                    self.role, self.installed_as, self.notes)


def _gprops_volume(shape: cq.Shape) -> float:
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, p)
    return p.Mass()


def _gprops_area(shape: cq.Shape) -> float:
    p = GProp_GProps()
    BRepGProp.SurfaceProperties_s(shape.wrapped, p)
    return p.Mass()


def _com(shape: cq.Shape) -> Tuple[float, float, float]:
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, p)
    c = p.CentreOfMass()
    return (c.X(), c.Y(), c.Z())


def bbox_of(shape: cq.Shape) -> Dict[str, float]:
    """Axis-aligned bounding box, INFLATED by OCCT's default Bnd_Box gap.

    Bnd_Box carries a gap of about 1e-7 mm, so every face of the returned box
    stands roughly 1e-7 outside the true extent. That is deterministic, and both
    the geometry signature and compare_signatures (len_tol 1e-6) tolerate it, so
    it is left in place rather than removed - removing it would change every
    recorded signature for a tenth-of-a-micron cosmetic gain.

    Do not use this for a geometric claim. Overlap and clearance claims go
    through common_volume and min_distance, which are exact. test_primitives.py
    pins the inflation so it cannot silently grow.
    """
    b = Bnd_Box()
    BRepBndLib.Add_s(shape.wrapped, b)
    xm, ym, zm, xM, yM, zM = b.Get()
    return {"xmin": xm, "ymin": ym, "zmin": zm, "xmax": xM, "ymax": yM, "zmax": zM,
            "dx": xM - xm, "dy": yM - ym, "dz": zM - zm}


def is_valid(shape: cq.Shape) -> bool:
    return bool(BRepCheck_Analyzer(shape.wrapped).IsValid())


# ------------------------------------------------------------- interference
def common_volume(a: cq.Shape, b: cq.Shape) -> float:
    """Volume shared by two solids. 0.0 means they do not interpenetrate.

    This is the primitive the whole no-undeclared-overlap contract rests on.
    Touching solids have common volume 0 and a distance of 0; penetrating solids
    have a positive common volume. Only the second is an overlap.
    """
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.Build()
    if not op.IsDone():
        raise RuntimeError("boolean common failed")
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), p)
    v = p.Mass()
    return 0.0 if v < 0 else v


def min_distance(a: cq.Shape, b: cq.Shape) -> float:
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    if not d.IsDone():
        raise RuntimeError("distance query failed")
    return d.Value()


# ------------------------------------------------------------------- export
def export_step(shape: cq.Shape, path: str) -> int:
    cq.exporters.export(cq.Workplane("XY").add(shape), path, exportType="STEP")
    return os.path.getsize(path)


def export_brep(shape: cq.Shape, path: str) -> int:
    BRepTools.Write_s(shape.wrapped, path)
    return os.path.getsize(path)


def import_step(path: str) -> cq.Shape:
    return cq.importers.importStep(path).val()


def import_brep(path: str) -> cq.Shape:
    sh = TopoDS_Shape()
    BRepTools.Read_s(sh, path, BRep_Builder())
    return cq.Shape.cast(sh)


def compound(bodies: Sequence[Body]) -> cq.Shape:
    return cq.Compound.makeCompound([b.shape for b in bodies])


# --------------------------------------------------------------- signature
def geometry_signature(bodies: Sequence[Body], *, critical: Dict[str, float],
                       motion: Dict, states: Dict) -> Dict:
    """Deterministic semantic description of the built geometry.

    STEP bytes vary between exporter builds, so file hashes cannot be the
    reproducibility criterion. This can: it is computed from the kernel's own
    mass properties and is stable under re-export.
    """
    per_body = []
    for b in sorted(bodies, key=lambda x: x.id):
        per_body.append({
            "body_id": b.id, "name": b.name, "material_class": b.material_class,
            "volume_mm3": round(_gprops_volume(b.shape), ROUND),
            "area_mm2": round(_gprops_area(b.shape), ROUND),
            "bbox_mm": {k: round(v, ROUND) for k, v in bbox_of(b.shape).items()},
            "centre_of_mass_mm": [round(c, ROUND) for c in _com(b.shape)],
        })
    overall = bbox_of(compound(bodies))
    sig = {
        "body_count": len(bodies),
        "semantic_body_ids": [b.id for b in sorted(bodies, key=lambda x: x.id)],
        "bodies": per_body,
        "overall_bbox_mm": {k: round(v, ROUND) for k, v in overall.items()},
        "critical_dimensions_mm": {k: round(v, ROUND) for k, v in critical.items()},
        "motion": motion,
        "state_transforms": states,
        "units": MM,
    }
    payload = json.dumps(sig, sort_keys=True, separators=(",", ":")).encode()
    sig["signature_sha256"] = hashlib.sha256(payload).hexdigest()
    return sig


def compare_signatures(a: Dict, b: Dict, *, vol_tol_mm3: float = 1e-6,
                       len_tol_mm: float = 1e-6) -> Dict:
    """Compare two signatures within declared tolerances, field by field."""
    diffs: List[str] = []
    if a["body_count"] != b["body_count"]:
        diffs.append(f"body_count {a['body_count']} != {b['body_count']}")
    if a["semantic_body_ids"] != b["semantic_body_ids"]:
        diffs.append("semantic_body_ids differ")
    for ba, bb in zip(a["bodies"], b["bodies"]):
        if ba["body_id"] != bb["body_id"]:
            diffs.append(f"body id {ba['body_id']} != {bb['body_id']}")
            continue
        if abs(ba["volume_mm3"] - bb["volume_mm3"]) > vol_tol_mm3:
            diffs.append(f"{ba['body_id']} volume {ba['volume_mm3']} != {bb['volume_mm3']}")
        for k in ("dx", "dy", "dz"):
            if abs(ba["bbox_mm"][k] - bb["bbox_mm"][k]) > len_tol_mm:
                diffs.append(f"{ba['body_id']} bbox.{k} differs")
    for k, va in a["critical_dimensions_mm"].items():
        vb = b["critical_dimensions_mm"].get(k)
        if vb is None or abs(va - vb) > len_tol_mm:
            diffs.append(f"critical dimension {k} differs")
    return {"identical_hash": a.get("signature_sha256") == b.get("signature_sha256"),
            "within_tolerance": not diffs, "differences": diffs,
            "vol_tol_mm3": vol_tol_mm3, "len_tol_mm": len_tol_mm}


# ------------------------------------------------------------------ motion
def rotation(axis_origin, axis_dir, degrees: float) -> cq.Location:
    """Rotation about the LINE through `axis_origin` along `axis_dir`.

    cq.Location(t, ax, angle) is translation + rotation about an axis through
    the world origin, which is not the same thing and silently produces a
    rigid motion that does not fix the intended axis. Conjugating by the
    origin translation gives the rotation actually wanted here.
    """
    o = cq.Vector(*axis_origin)
    spin = cq.Location(cq.Vector(0, 0, 0), cq.Vector(*axis_dir), degrees)
    return cq.Location(o) * spin * cq.Location(o * -1)


def translation(vec) -> cq.Location:
    return cq.Location(cq.Vector(*vec))


def sample_motion(fixed: Sequence[Body], moving: Sequence[Body], pose_fn,
                  t0: float, t1: float, coarse: int,
                  refine_windows: Sequence[Tuple[float, float, int]] = (),
                  ) -> List[float]:
    """Deterministic sample list: a uniform sweep plus declared refinement windows.

    Refinement is DECLARED by the reference rather than discovered adaptively, so
    the sample set is reproducible and a reader can see exactly where the motion
    was examined closely and where it was not.
    """
    ts = [t0 + (t1 - t0) * i / coarse for i in range(coarse + 1)]
    for a, b, n in refine_windows:
        ts.extend(a + (b - a) * i / n for i in range(n + 1))
    return sorted(set(round(t, 9) for t in ts))


# --------------------------------------------------------------- rendering
def render_views(bodies: Sequence[Body], out_dir: str, stem: str,
                 views: Sequence[Tuple[str, Tuple[float, float, float]]],
                 colors: Optional[Dict[str, str]] = None,
                 section: Optional[Tuple[str, float]] = None,
                 alphas: Optional[Dict[str, float]] = None) -> List[str]:
    """Headless raster views via OCCT tessellation + matplotlib Agg.

    Images are review aids. They are never the evidence for a geometric claim;
    every such claim in this pilot is backed by a kernel measurement.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    os.makedirs(out_dir, exist_ok=True)
    palette = colors or {}
    opacity = alphas or {}
    default_cycle = ["#6b8fb4", "#c08a5a", "#7ba884", "#b06f8a", "#8d84b8", "#b9a04e"]
    written = []

    tess = []
    for i, b in enumerate(bodies):
        shape = b.shape
        if section:
            axis, at = section
            bb = bbox_of(compound(bodies))
            big = max(bb["dx"], bb["dy"], bb["dz"]) * 3
            cutter = cq.Solid.makeBox(big, big, big).moved(
                cq.Location(cq.Vector(-big / 2 if axis != "x" else at,
                                      -big / 2 if axis != "y" else at,
                                      -big / 2 if axis != "z" else at)))
            try:
                shape = shape.cut(cutter)
            except Exception:
                shape = b.shape
        try:
            verts, tris = shape.tessellate(0.25)
        except Exception:
            continue
        v = np.array([[p.x, p.y, p.z] for p in verts])
        f = np.array(tris)
        col = palette.get(b.id, default_cycle[i % len(default_cycle)])
        if len(f):
            # A body may be drawn translucent so bodies nested inside it stay
            # visible. matplotlib's 3D depth sorting puts a large enclosing body
            # in front of a thin one inside it, which reads as "the inner body is
            # missing" when it is merely hidden.
            tess.append((v[f], col, b.id, opacity.get(b.id, 0.94)))

    if not tess:
        return written
    allv = np.vstack([t[0].reshape(-1, 3) for t in tess])
    ctr = allv.mean(axis=0)
    span = max(allv.max(axis=0) - allv.min(axis=0)) * 0.62 or 1.0

    for label, eye in views:
        fig = plt.figure(figsize=(7.2, 5.4), dpi=130)
        ax = fig.add_subplot(111, projection="3d")
        for tri, col, _, alpha in tess:
            pc = Poly3DCollection(tri, alpha=alpha, linewidths=0.18)
            pc.set_facecolor(col)
            pc.set_edgecolor("#33383d")
            ax.add_collection3d(pc)
        ax.set_xlim(ctr[0] - span, ctr[0] + span)
        ax.set_ylim(ctr[1] - span, ctr[1] + span)
        ax.set_zlim(ctr[2] - span, ctr[2] + span)
        try:
            ax.set_box_aspect((1, 1, 1))
        except Exception:
            pass
        ax.view_init(elev=eye[0], azim=eye[1])
        ax.set_xlabel("X (mm)", fontsize=7)
        ax.set_ylabel("Y (mm)", fontsize=7)
        ax.set_zlabel("Z (mm)", fontsize=7)
        ax.tick_params(labelsize=6)
        ax.set_title(f"{stem} — {label}", fontsize=9)
        ax.grid(True, alpha=0.15)
        p = os.path.join(out_dir, f"{stem}_{label}.png")
        fig.tight_layout()
        fig.savefig(p, bbox_inches="tight")
        plt.close(fig)
        written.append(p)
    return written


ISO = [("iso", (24.0, -55.0)), ("front", (0.0, -90.0)),
       ("top", (89.9, -90.0)), ("side", (0.0, 0.0))]


def render_section(bodies, out_path: str, *, plane: str, at: float,
                   colors=None, title: str = "", annotations=(),
                   extent=None) -> str:
    """True orthographic section: the cut face only, viewed normal to the plane.

    The 3-D renderer above is a projection of whole solids and is useless for
    judging a fit. This slices every body with the plane, projects the resulting
    faces onto it, and draws them flat. Nothing behind the plane is drawn, there
    is no perspective and no inset, so what a reviewer measures on the image is
    what the model says.

    `plane` is the axis normal to the cut: "x", "y" or "z".
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    axis = {"x": 0, "y": 1, "z": 2}[plane]
    keep = [i for i in (0, 1, 2) if i != axis]
    labels = ["X (mm)", "Y (mm)", "Z (mm)"]
    palette = colors or {}
    cycle = ["#6b8fb4", "#c08a5a", "#7ba884", "#b06f8a", "#8d84b8"]

    fig, ax = plt.subplots(figsize=(9.0, 6.0), dpi=150)
    drawn = 0
    for i, b in enumerate(bodies):
        try:
            sect = b.shape.intersect(_plane_slab(b.shape, axis, at))
        except Exception:
            continue
        if sect is None:
            continue
        try:
            verts, tris = sect.tessellate(0.05)
        except Exception:
            continue
        if not tris:
            continue
        col = palette.get(b.id, cycle[i % len(cycle)])
        def coord(v, idx):
            return (v.x, v.y, v.z)[idx]

        for tri in tris:
            pts = [(coord(verts[k], keep[0]), coord(verts[k], keep[1])) for k in tri]
            ax.add_patch(MplPolygon(pts, closed=True, facecolor=col,
                                    edgecolor=col, linewidth=0.0, zorder=2))
        drawn += 1
    if not drawn:
        plt.close(fig)
        return ""

    ax.set_aspect("equal", adjustable="box")
    ax.autoscale_view()
    if extent:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
    ax.set_xlabel(labels[keep[0]], fontsize=9)
    ax.set_ylabel(labels[keep[1]], fontsize=9)
    ax.set_title("%s\nsection at %s = %.2f mm - orthographic, cut face only"
                 % (title, plane.upper(), at), fontsize=10)
    ax.grid(True, alpha=0.25, linewidth=0.4, zorder=1)
    ax.tick_params(labelsize=8)
    for a in annotations:
        ax.annotate(a["text"], xy=a["xy"], xytext=a["xytext"], fontsize=8,
                    arrowprops=dict(arrowstyle="->", linewidth=0.9, color="#c0392b"),
                    color="#c0392b", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#c0392b", lw=0.7))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _plane_slab(shape: cq.Shape, axis: int, at: float, half: float = 0.02) -> cq.Shape:
    """A thin slab at the cutting plane; intersecting with it yields the cut face."""
    bb = bbox_of(shape)
    lo = [bb["xmin"] - 10, bb["ymin"] - 10, bb["zmin"] - 10]
    size = [bb["dx"] + 20, bb["dy"] + 20, bb["dz"] + 20]
    lo[axis] = at - half
    size[axis] = 2 * half
    return cq.Solid.makeBox(size[0], size[1], size[2],
                            pnt=cq.Vector(lo[0], lo[1], lo[2]))


# ------------------------------------------------------ drawing-style sections
def section_polygons(shape: cq.Shape, axis: int, at: float, tol: float = 0.05):
    """Exact section outlines: outer boundary plus holes, per cut face.

    Tessellating a thin slab and drawing its triangles produces the diagonal
    noise that makes a review image unreadable - those diagonals are mesh edges,
    not geometry. This takes the planar faces the cut actually produces and
    walks their wires, so what is drawn is the boundary of the cut face and
    nothing else.

    Returns a list of (outer_points, [hole_points, ...]) in the two in-plane
    coordinates, ordered as (u, v) with the cut axis dropped.
    """
    keep = [i for i in (0, 1, 2) if i != axis]
    bb = bbox_of(shape)
    lo = [bb["xmin"] - 10, bb["ymin"] - 10, bb["zmin"] - 10]
    size = [bb["dx"] + 20, bb["dy"] + 20, bb["dz"] + 20]
    half = 0.01
    lo[axis] = at - half
    size[axis] = 2 * half
    slab = cq.Solid.makeBox(size[0], size[1], size[2], pnt=cq.Vector(*lo))
    try:
        sect = shape.intersect(slab)
    except Exception:
        return []
    if sect is None:
        return []

    def uv(v):
        c = (v.x, v.y, v.z)
        return (c[keep[0]], c[keep[1]])

    def wire_pts(w):
        """Walk the wire in connectivity order.

        Wire.Edges() is a bag, not a path. Concatenating each edge's samples in
        list order makes the polygon jump between disconnected ends, which draws
        as spurious wedges across the cut face - the artifact this replaces.
        """
        edges = list(w.Edges())
        if not edges:
            return []

        def ends(e):
            return e.startPoint(), e.endPoint()

        def near(a, b, eps=1e-6):
            return (abs(a.x - b.x) < eps and abs(a.y - b.y) < eps
                    and abs(a.z - b.z) < eps)

        def sample(e, rev):
            n = min(max(2, int(e.Length() / tol) + 1), 400)
            ts = [i / float(n) for i in range(n + 1)]
            if rev:
                ts.reverse()
            return [uv(e.positionAt(s)) for s in ts]

        cur = edges.pop(0)
        s0, e0 = ends(cur)
        pts = sample(cur, False)
        tail = e0
        while edges:
            for i, e in enumerate(edges):
                a, b = ends(e)
                if near(a, tail):
                    pts.extend(sample(e, False)[1:]); tail = b; edges.pop(i); break
                if near(b, tail):
                    pts.extend(sample(e, True)[1:]); tail = a; edges.pop(i); break
            else:
                break                     # open wire; draw what is connected
        return pts

    out = []
    for f in sect.Faces():
        c = f.Center()
        if abs((c.x, c.y, c.z)[axis] - at) > half * 1.5:
            continue                      # not the cut face; a slab side wall
        try:
            outer = wire_pts(f.outerWire())
            holes = [wire_pts(w) for w in f.innerWires()]
        except Exception:
            continue
        if len(outer) >= 3:
            out.append((outer, holes))
    return out


def render_review_section(bodies, out_path: str, *, plane: str, at: float,
                          colors=None, hatches=None, title: str = "",
                          label: str = "", extent=None, annotations=(),
                          section_lines=(), context_note: str = "") -> str:
    """Orthographic review section drawn as a drawing, not as a render.

    Cut faces are filled and hatched so they read as cut material. Nothing
    behind the plane is drawn. `section_lines` marks where OTHER cuts are taken,
    which is what lets a reviewer place a detail cut inside the whole product.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch

    axis = {"x": 0, "y": 1, "z": 2}[plane]
    keep = [i for i in (0, 1, 2) if i != axis]
    names = ["X (mm)", "Y (mm)", "Z (mm)"]
    palette = colors or {}
    hat = hatches or {}
    cycle = ["#6b8fb4", "#c08a5a", "#7ba884", "#b06f8a", "#8d84b8"]

    fig, ax = plt.subplots(figsize=(11.0, 6.4), dpi=150)
    drawn = 0
    for i, b in enumerate(bodies):
        polys = section_polygons(b.shape, axis, at)
        if not polys:
            continue
        col = palette.get(b.id, cycle[i % len(cycle)])
        hh = hat.get(b.id, "///")
        for outer, holes in polys:
            verts, codes = [], []
            for ring in [outer] + holes:
                verts.extend(ring + [ring[0]])
                codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(ring) - 1)
                             + [MplPath.CLOSEPOLY])
            path = MplPath(verts, codes)
            ax.add_patch(PathPatch(path, facecolor=col, edgecolor="#1b1b1b",
                                   lw=0.9, hatch=hh, alpha=0.95, zorder=3))
        drawn += 1
    if not drawn:
        plt.close(fig)
        return ""

    for sl in section_lines:
        pos, lab = sl["at"], sl["label"]
        if sl.get("along", "u") == "u":
            ax.axvline(pos, color="#c0392b", lw=1.1, ls=(0, (9, 4, 2, 4)), zorder=6)
            y = ax.get_ylim()[1]
            for dy, va in ((0, "bottom"),):
                ax.text(pos, y, " %s " % lab, color="#c0392b", fontsize=9,
                        ha="center", va=va, fontweight="bold", zorder=7,
                        bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="#c0392b", lw=0.8))
        else:
            ax.axhline(pos, color="#c0392b", lw=1.1, ls=(0, (9, 4, 2, 4)), zorder=6)
            ax.text(ax.get_xlim()[1], pos, " %s " % lab, color="#c0392b", fontsize=9,
                    ha="left", va="center", fontweight="bold", zorder=7,
                    bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="#c0392b", lw=0.8))

    ax.set_aspect("equal", adjustable="box")
    ax.autoscale_view()
    if extent:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
    ax.set_xlabel(names[keep[0]], fontsize=9)
    ax.set_ylabel(names[keep[1]], fontsize=9)
    head = title if not label else "%s   %s" % (label, title)
    ax.set_title("%s\ncut at %s = %.2f mm  -  orthographic, normal to the cut, "
                 "cut faces hatched%s"
                 % (head, plane.upper(), at, ("  -  " + context_note) if context_note else ""),
                 fontsize=10)
    ax.grid(True, alpha=0.20, lw=0.4, zorder=1)
    ax.tick_params(labelsize=8)
    for a in annotations:
        ax.annotate(a["text"], xy=a["xy"], xytext=a["xytext"], fontsize=8.5,
                    arrowprops=dict(arrowstyle="->", lw=1.0, color="#0b6b3a"),
                    color="#0b6b3a", zorder=8, ha=a.get("ha", "left"),
                    bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="#0b6b3a", lw=0.8))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ------------------------------------------------------------------- hashes
def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def write_json(path: str, obj) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, default=str)
        fh.write("\n")
    return path
