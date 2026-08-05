"""EXE-BM002-01 - CAD-derived review media for independent human review.

Everything this file writes is rendered from the reference's own B-rep solids,
posed by the same functions the validator uses. No proxy geometry, no redrawn
mechanism, no generative image, no mesh that does not correspond to the accepted
B-rep. The accepted geometry signature is asserted before anything is drawn, so a
run against changed geometry stops rather than producing media that quietly
disagrees with the CAD.

Two rendering paths, both deliberate:

* Shaded three-dimensional views go through `cadvideo.rasterise`, a real z-buffer
  over per-FACE tessellations. Triangles carry the shading and never the line
  work, and only a face's own rim is stroked, depth-tested against the finished
  buffer. No mesh diagonal ever appears and no hidden edge shows through.
* Mechanical sections are drawn here from `cadval.section_polygons`, which walks
  the exact wires of the cut faces. Cut material is filled and hatched; nothing
  behind the plane is drawn.

Sections carry DETAIL PANELS. A running clearance of 0.2 mm on a 150 mm-wide
drawing is about one pixel, so a full-width section cannot show the fits it is
supposed to be evidence for. Every section that has a fit to show enlarges it.

A "cutaway" here means a solid is intersected with a half-space FOR DISPLAY ONLY.
It never changes the model, it is always stated on the image, and the geometry
signature is re-verified at the end of the run to prove it.

Run:  python review_views.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import cadval as cv          # noqa: E402
import cadvideo as cvd       # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B            # noqa: E402

import cadquery as cq        # noqa: E402
import matplotlib            # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.path import Path as MplPath        # noqa: E402
from matplotlib.patches import PathPatch, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots")
OUT = os.path.join(HERE, "validation")

ACCEPTED_SIGNATURE = ("6824e5102424e3db883f16b684ab54f02c14eed19bead0116c704092"
                      "156bc2ee")

P = B.load_params()
G = B.geom(P)
AY, AZ = G["axis_y"], G["axis_z"]
R, L = P["crank_radius"], P["rod_length"]

COLORS = {
    "BODY-HOUSING": "#7d9dc0",
    "BODY-REAR-PANEL": "#a8b3bd",
    "BODY-PLATFORM": "#6fa77f",
    "BODY-CRANK-SHAFT": "#c8894f",
    "BODY-CONNECTING-ROD": "#ad6a86",
    "BODY-CRANK-JOINT-PIN": "#8478bb",
    "BODY-PLATFORM-JOINT-PIN": "#c0a33e",
    "SCENARIO-PAYLOAD-1KG": "#cfd4d9",
}
HATCH = {
    "BODY-HOUSING": "///",
    "BODY-REAR-PANEL": "\\\\\\",
    "BODY-PLATFORM": "xxx",
    "BODY-CRANK-SHAFT": "...",
    "BODY-CONNECTING-ROD": "|||",
    "BODY-CRANK-JOINT-PIN": "---",
    "BODY-PLATFORM-JOINT-PIN": "+++",
    "SCENARIO-PAYLOAD-1KG": "",
}
SHORT = {
    "BODY-HOUSING": "HOUSING",
    "BODY-REAR-PANEL": "REAR PANEL",
    "BODY-PLATFORM": "PLATFORM",
    "BODY-CRANK-SHAFT": "CRANK SHAFT",
    "BODY-CONNECTING-ROD": "CONNECTING ROD",
    "BODY-CRANK-JOINT-PIN": "CRANK JOINT PIN",
    "BODY-PLATFORM-JOINT-PIN": "PLATFORM JOINT PIN",
    "SCENARIO-PAYLOAD-1KG": "PAYLOAD (SCENARIO)",
}
ALL7 = ["BODY-HOUSING", "BODY-REAR-PANEL", "BODY-PLATFORM", "BODY-CRANK-SHAFT",
        "BODY-CONNECTING-ROD", "BODY-CRANK-JOINT-PIN", "BODY-PLATFORM-JOINT-PIN"]

W, H = 1600, 900
NOT_VERIFIED = ("CAD geometry only.  Structural strength, user effort, jamming, "
                "safety and manufacture are NOT VERIFIED.")
INK = "#14181c"
DIMC = "#0b6b3a"
NOTEC = "#b03a2e"
ASMC = "#1f4e9c"


# ============================================================ fixed cameras
def cam(eye, target, scale, up=(0.0, 0.0, 1.0)) -> cvd.Camera:
    return cvd.Camera(eye=eye, target=target, up=up, scale=scale)


CENTRE = (16.0, 70.0, 112.0)
CAMERAS: Dict[str, cvd.Camera] = {
    "front_iso": cam((-360.0, -340.0, 300.0), (10.0, 70.0, 108.0), 150.0),
    "rear_iso": cam((430.0, 360.0, 300.0), (22.0, 70.0, 108.0), 150.0),
    "left": cam((-620.0, 70.0, 112.0), CENTRE, 132.0),
    "right": cam((640.0, 70.0, 112.0), CENTRE, 132.0),
    "front": cam((16.0, -620.0, 112.0), CENTRE, 132.0),
    "rear": cam((16.0, 700.0, 112.0), CENTRE, 132.0),
    "top": cam((16.0, 70.0, 720.0), CENTRE, 90.0, up=(0.0, 1.0, 0.0)),
    # looking along -X: the crank/link motion plane is face-on, +Y to the right.
    # Framed to hold the payload envelope at TOP (z up to 256) inside the frame.
    "mech": cam((760.0, 70.0, 124.0), (40.0, 70.0, 124.0), 142.0),
    # opened-front isometric: exterior handle AND internal linkage in one view
    "cutaway_iso": cam((-380.0, -320.0, 250.0), (20.0, 76.0, 112.0), 142.0),
    # crank face-on, for the grip radius
    "crank_face": cam((-520.0, 70.0, 60.0), (-30.0, 70.0, 60.0), 62.0),
    "assembly_iso": cam((-350.0, -330.0, 285.0), (20.0, 76.0, 112.0), 150.0),
}


# ============================================================== geometry help
def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


BIG = (-400.0, 500.0, -300.0, 400.0, -300.0, 500.0)


def cut_half(shape: cq.Shape, axis: str, keep: str, at: float) -> Optional[cq.Shape]:
    """Display-only half-space cut. Never applied to the exported model."""
    lo, hi = list(BIG[0::2]), list(BIG[1::2])
    i = {"x": 0, "y": 1, "z": 2}[axis]
    if keep == "above":
        hi[i] = at
    else:
        lo[i] = at
    try:
        r = shape.cut(_box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    except Exception:
        return shape
    return None if cv._gprops_volume(r) <= 1e-9 else r


class Disp:
    """A displayable object: a semantic id and a shape. Not a product body."""

    def __init__(self, bid: str, shape: cq.Shape):
        self.id, self.shape = bid, shape


def payload_solid(support_z: float) -> cq.Shape:
    return _box(G["payload_x0"], G["payload_x1"], G["payload_y0"], G["payload_y1"],
                support_z, support_z + P["payload_z"])


def support_z_at(platform_shape: cq.Shape) -> float:
    col = _box(G["payload_x0"], G["payload_x1"], G["payload_y0"], G["payload_y1"],
               0.0, 400.0)
    return cv.bbox_of(platform_shape.intersect(col))["zmax"]


def state_of(bodies, deg: float) -> Dict:
    d = {b.id: b for b in B.bodies_at(bodies, P, deg)}
    cy, cz = B.crank_pin_centre(P, deg)
    return {"bodies": d, "deg": deg, "crank_pin": (cy, cz),
            "plat_pin_z": B.platform_pin_z(P, deg),
            "support_z": support_z_at(d["BODY-PLATFORM"].shape),
            "rod_angle": B.rod_angle_deg(P, deg)}


# ------------------------------------------------- cached tessellation + poses
_PATCH_CACHE: Dict[int, Tuple[cq.Shape, List[Dict]]] = {}


def patches_of(shape: cq.Shape, bid: str, tol: float = 0.4) -> List[Dict]:
    """Tessellate once per shape, keyed on identity.

    The shape itself is kept in the cache alongside its patches. Without that the
    temporary cut solids would be collected and CPython would hand their id() to a
    later shape, which would then be drawn with somebody else's triangles.
    """
    key = id(shape)
    if key not in _PATCH_CACHE:
        ps = cvd.face_patches(shape, tol)
        for p in ps:
            p["body_id"] = bid
        _PATCH_CACHE[key] = (shape, ps)
    return _PATCH_CACHE[key][1]


def moved_patches(patches: List[Dict], loc: cq.Location) -> List[Dict]:
    """Apply a rigid pose to an already-tessellated patch set.

    Tessellating the moved solid would give the same picture at many times the
    cost; a rigid transform of the vertices is the same thing, exactly.
    """
    t = loc.wrapped.Transformation()
    M = np.array([[t.Value(r, c) for c in range(1, 4)] for r in range(1, 4)])
    v = np.array([t.Value(r, 4) for r in range(1, 4)])
    out = []
    for p in patches:
        q = dict(p)
        q["points"] = p["points"] @ M.T + v
        out.append(q)
    return out


def scene(bodies, deg: float, *, drop: Sequence[str] = (),
          cut: Optional[Tuple[str, str, float]] = None,
          cut_only: Sequence[str] = (), payload: bool = False,
          tol: float = 0.4) -> List[Dict]:
    """Tessellated, posed patch list for one configuration."""
    out: List[Dict] = []
    posed = B.bodies_at(bodies, P, deg)
    for b in posed:
        if b.id in drop:
            continue
        if cut and (not cut_only or b.id in cut_only):
            sh = cut_half(b.shape, cut[0], cut[1], cut[2])
            if sh is None:
                continue
            out += patches_of(sh, b.id, tol)
        else:
            base = next(x for x in bodies if x.id == b.id)
            out += moved_patches(patches_of(base.shape, b.id, tol),
                                 B.pose_at(P, b.id, deg))
    if payload:
        d = {b.id: b for b in posed}
        ps = cvd.face_patches(payload_solid(support_z_at(d["BODY-PLATFORM"].shape)), tol)
        for p in ps:
            p["body_id"] = "SCENARIO-PAYLOAD-1KG"
        out += ps
    return out


# ============================================================ figure plumbing
def new_fig():
    return plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)


def raster_axes(fig, rect, patches, camera: cvd.Camera, *, px=(1600, 900),
                bg="#f2f4f6", frame=None, title=None):
    img, ext = cvd.rasterise(patches, camera, COLORS, width=px[0], height=px[1],
                             bg=bg, edge_px=1.0)
    ax = fig.add_axes(rect)
    ax.imshow(img, extent=ext, origin="upper", interpolation="none", zorder=1)
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_visible(frame is not None)
        if frame:
            s.set_color(frame)
            s.set_linewidth(1.6)
    if title:
        ax.set_title(title, fontsize=10.5, color=frame or INK, weight="bold", pad=4)
    return ax


def save(fig, name: str) -> str:
    os.makedirs(SHOTS, exist_ok=True)
    p = os.path.join(SHOTS, name)
    fig.savefig(p, dpi=100, facecolor="white")
    plt.close(fig)
    print("   %s" % name)
    return p


# ------------------------------------------------------------------ overlays
def note(ax, x, y, text, *, ec=INK, fc="white", size=11.0, ha="left", va="top",
         mono=False, weight="normal"):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=size, ha=ha, va=va,
            zorder=32, color=INK, weight=weight,
            family="DejaVu Sans Mono" if mono else "DejaVu Sans",
            bbox=dict(boxstyle="round,pad=0.4", fc=fc, ec=ec, lw=1.2, alpha=0.96))


def leader(ax, camera, pt, text, xy_axes, *, color=INK, size=10.8, ha="left"):
    """Label placed in AXES fraction, leader drawn back to a model point.

    Placing labels in axes fraction and the anchor in model space keeps text in
    the margins where there is room, instead of on top of the geometry.
    """
    x, y = camera.at(pt)
    ax.annotate(text, xy=(x, y), xycoords="data",
                xytext=xy_axes, textcoords="axes fraction",
                fontsize=size, color=color, ha=ha, va="center", zorder=31,
                arrowprops=dict(arrowstyle="-", lw=1.1, color=color,
                                shrinkA=0, shrinkB=3),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1.0,
                          alpha=0.97))


def dim3(ax, camera, p0, p1, text, *, color=DIMC, size=11.5, tpos=0.5,
         toff=(0.0, 0.0)):
    a = np.array(camera.at(p0))
    b = np.array(camera.at(p1))
    ax.annotate("", xy=tuple(b), xytext=tuple(a), zorder=29,
                arrowprops=dict(arrowstyle="<|-|>,head_width=0.3,head_length=0.65",
                                lw=1.7, color=color, shrinkA=0, shrinkB=0))
    m = a + (b - a) * tpos + np.array(toff)
    ax.text(m[0], m[1], text, color=color, fontsize=size, weight="bold",
            ha="center", va="center", zorder=30,
            bbox=dict(boxstyle="round,pad=0.26", fc="white", ec=color, lw=1.1))


def triad_axes(ax, camera, *, x=0.115, y=0.16, length=0.052):
    """Orientation indicator drawn in the corner, in axes fraction, using the
    camera's own projection of the three model axes."""
    o = np.array(camera.at((0.0, 0.0, 0.0)))
    for vec, lab, col in (((60, 0, 0), "X", "#b03a2e"), ((0, 60, 0), "Y", "#0b6b3a"),
                          ((0, 0, 60), "Z", "#1f4e9c")):
        d = np.array(camera.at(tuple(vec))) - o
        n = np.linalg.norm(d)
        d = d / (n if n else 1.0) * length
        ax.annotate("", xy=(x + d[0], y + d[1]), xytext=(x, y),
                    xycoords="axes fraction", textcoords="axes fraction", zorder=32,
                    arrowprops=dict(arrowstyle="-|>,head_width=0.28,head_length=0.65",
                                    lw=2.1, color=col, shrinkA=0, shrinkB=0))
        ax.text(x + d[0] * 1.28, y + d[1] * 1.28, lab, transform=ax.transAxes,
                color=col, fontsize=11.5, weight="bold", ha="center", va="center",
                zorder=33)


def rot_arrow(ax, camera, centre, radius, *, text="", color=NOTEC, a0=200.0,
              a1=340.0, size=11.0, tpos=0.5):
    """Curved rotation arrow drawn in the model's own YZ plane."""
    pts = []
    for t in np.linspace(math.radians(a0), math.radians(a1), 30):
        pts.append(camera.at((centre[0], centre[1] + radius * math.cos(t),
                              centre[2] + radius * math.sin(t))))
    pts = np.array(pts)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=2.8, zorder=29,
            solid_capstyle="round")
    ax.annotate("", xy=tuple(pts[-1]), xytext=tuple(pts[-4]), zorder=29,
                arrowprops=dict(arrowstyle="-|>,head_width=0.42,head_length=0.9",
                                lw=2.8, color=color, shrinkA=0, shrinkB=0))
    if text:
        m = pts[int((len(pts) - 1) * tpos)]
        ax.text(m[0], m[1], text, color=color, fontsize=size, weight="bold",
                ha="center", va="center", zorder=30,
                bbox=dict(boxstyle="round,pad=0.26", fc="white", ec=color, lw=1.1))


def header(ax, title: str, subtitle: str = ""):
    t = title if not subtitle else title + "\n" + subtitle
    ax.text(0.008, 0.992, t, transform=ax.transAxes, fontsize=12.5, ha="left",
            va="top", weight="bold", color=INK, zorder=33,
            bbox=dict(boxstyle="round,pad=0.38", fc="white", ec="#3a3f45", lw=1.1,
                      alpha=0.97))


def banner(ax, text: str, *, color=NOTEC, y=0.900, x=0.5):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=14.5, color="white",
            ha="center", va="center", weight="bold", zorder=34,
            bbox=dict(boxstyle="round,pad=0.4", fc=color, ec="none"))


def caveat(ax, text: str, *, y=0.012):
    ax.text(0.5, y, text, transform=ax.transAxes, fontsize=10.2, color="#4a5058",
            ha="center", va="bottom", style="italic", zorder=33,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9ced4", lw=0.9,
                      alpha=0.95))


def swatches(ax, ids: Sequence[str], *, x=0.998, y=0.997, dy=0.033):
    n = len(ids)
    ax.add_patch(Rectangle((x - 0.152, y - n * dy - 0.012), 0.152, n * dy + 0.012,
                           transform=ax.transAxes, fc="white", ec="#3a3f45", lw=1.0,
                           alpha=0.95, zorder=30))
    for k, i in enumerate(ids):
        yy = y - 0.018 - k * dy
        ax.add_patch(Rectangle((x - 0.143, yy - 0.009), 0.017, 0.019,
                               transform=ax.transAxes, fc=COLORS.get(i, "#888"),
                               ec="#2b3036", lw=0.7, zorder=31))
        ax.text(x - 0.118, yy, SHORT.get(i, i), transform=ax.transAxes,
                fontsize=9.6, ha="left", va="center", zorder=31, color=INK)


# ==================================================== section drawing engine
def draw_section(ax, disp_bodies, plane: str, at: float, extent, *,
                 lw=1.0, hatch_scale=True):
    """Fill and hatch the exact cut faces of every body on one plane."""
    axis = {"x": 0, "y": 1, "z": 2}[plane]
    for b in disp_bodies:
        polys = cv.section_polygons(b.shape, axis, at)
        if not polys:
            continue
        col = COLORS.get(b.id, "#9aa5b1")
        hh = HATCH.get(b.id, "///")
        for outer, holes in polys:
            verts, codes = [], []
            for ring in [outer] + holes:
                verts.extend(ring + [ring[0]])
                codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(ring) - 1)
                             + [MplPath.CLOSEPOLY])
            ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=col,
                                   edgecolor="#12161a", lw=lw, hatch=hh,
                                   alpha=0.97, zorder=3))
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18, lw=0.4, zorder=1)
    ax.tick_params(labelsize=8)


def sect_label(ax, xy, text, xytext, *, color=INK, size=9.8, ha="left"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=size, color=color, ha=ha,
                va="center", zorder=20,
                arrowprops=dict(arrowstyle="-", lw=1.0, color=color, shrinkA=0,
                                shrinkB=2),
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=color, lw=0.95,
                          alpha=0.97))


def sect_dim(ax, p0, p1, text, *, color=DIMC, size=9.8, toff=(0.0, 0.0),
             tha="center"):
    ax.annotate("", xy=p1, xytext=p0, zorder=21,
                arrowprops=dict(arrowstyle="<|-|>,head_width=0.26,head_length=0.6",
                                lw=1.4, color=color, shrinkA=0, shrinkB=0))
    m = ((p0[0] + p1[0]) / 2 + toff[0], (p0[1] + p1[1]) / 2 + toff[1])
    ax.text(m[0], m[1], text, color=color, fontsize=size, weight="bold", ha=tha,
            va="center", zorder=22,
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=color, lw=1.0))


def sect_arrow(ax, p0, dxy, text, *, color=NOTEC, size=10.0, tpos=0.5,
               toff=(0.0, 0.0), tha="center"):
    ax.annotate("", xy=(p0[0] + dxy[0], p0[1] + dxy[1]), xytext=p0, zorder=23,
                arrowprops=dict(arrowstyle="-|>,head_width=0.4,head_length=0.9",
                                lw=3.0, color=color, shrinkA=0, shrinkB=0))
    if text:
        ax.text(p0[0] + dxy[0] * tpos + toff[0], p0[1] + dxy[1] * tpos + toff[1],
                text, color=color, fontsize=size, weight="bold", ha=tha,
                va="center", zorder=24,
                bbox=dict(boxstyle="round,pad=0.26", fc="white", ec=color, lw=1.1))


def detail_box(ax_main, extent, label, *, color=NOTEC):
    """Mark on the main section where a detail panel is taken from."""
    ax_main.add_patch(Rectangle((extent[0], extent[2]), extent[1] - extent[0],
                                extent[3] - extent[2], fill=False, ec=color,
                                lw=1.6, ls=(0, (5, 3)), zorder=25))
    ax_main.text(extent[1], extent[3], " " + label, color=color, fontsize=10.5,
                 weight="bold", ha="left", va="bottom", zorder=26,
                 bbox=dict(boxstyle="square,pad=0.16", fc="white", ec=color, lw=1.0))


# ================================================================ image set
RENDERED: List[Dict] = []


def record(name, purpose, bodies_visible, state, plane, kind="REVIEW_EVIDENCE",
           cutaway="", details=""):
    RENDERED.append({"file": "screenshots/" + name, "purpose": purpose,
                     "bodies_visible": bodies_visible, "state": state,
                     "section_plane": plane, "display_cutaway": cutaway,
                     "detail_panels": details, "classification": kind})


# ------------------------------------------------------------ overall views
def overall_views(bodies):
    print("-- overall and exterior")
    specs = [
        ("review_overall_front_iso.png", "front_iso", 0.0,
         "Overall product, front-left isometric",
         "external handle at -X, open payload top, front and left faces"),
        ("review_overall_rear_iso.png", "rear_iso", 0.0,
         "Overall product, rear-right isometric",
         "BODY-REAR-PANEL closing the +X side"),
        ("review_overall_left.png", "left", 0.0,
         "Left elevation, looking +X", "the external crank, face-on"),
        ("review_overall_right.png", "right", 0.0,
         "Right elevation, looking -X", "the rear panel, face-on"),
        ("review_overall_front.png", "front", 0.0,
         "Front elevation, looking +Y", "handle projection and overall height"),
        ("review_overall_rear.png", "rear", 0.0,
         "Rear elevation, looking -Y", "back face"),
        ("review_overall_top.png", "top", 180.0,
         "Top view, platform at TOP", "the payload aperture and the platform below it"),
    ]
    for name, camname, deg, title, sub in specs:
        c = CAMERAS[camname]
        fig = new_fig()
        ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0], scene(bodies, deg), c)
        header(ax, "EXE-BM002-01   " + title, sub)
        caveat(ax, NOT_VERIFIED)
        triad_axes(ax, c)
        if camname == "front_iso":
            dim3(ax, c, (-46.0, -14.0, 0.0), (79.0, -14.0, 0.0), "125 overall X")
            dim3(ax, c, (79.0, 0.0, -12.0), (79.0, 140.0, -12.0), "140 overall Y")
            dim3(ax, c, (-56.0, 0.0, 0.0), (-56.0, 0.0, 224.0), "224 overall Z")
            rot_arrow(ax, c, (-46.0, AY, AZ), 40.0, text="CRANK ROTATION",
                      a0=-40.0, a1=200.0)
            leader(ax, c, (16.0, 70.0, 224.0),
                   "TOP PAYLOAD OPENING\nhousing rim z = 224", (0.62, 0.90))
            leader(ax, c, (-40.0, AY, AZ - 26.0),
                   "EXTERNAL HANDLE GRIP\nFEATURE-SHAFT-GRIP\non BODY-CRANK-SHAFT",
                   (0.055, 0.40))
            leader(ax, c, (35.0, 70.0, 126.0),
                   "PLATFORM support surface\nat BOTTOM, z = 126", (0.63, 0.33))
        if camname == "left":
            rot_arrow(ax, c, (-46.0, AY, AZ), 26.0, text="grip sweep r = 26",
                      a0=-90.0, a1=200.0)
            leader(ax, c, (-46.0, AY, AZ - 26.0),
                   "FEATURE-SHAFT-GRIP  O12\n26 mm from the shaft axis", (0.10, 0.30))
            leader(ax, c, (-18.0, AY + 30.0, AZ + 18.0),
                   "FEATURE-SHAFT-HUB  O70\nalso the journal diameter", (0.145, 0.86))
            dim3(ax, c, (-46.0, 0.0, 10.0), (-46.0, 140.0, 10.0), "140 overall Y")
        if camname == "rear_iso":
            leader(ax, c, (79.0, 100.0, 140.0),
                   "BODY-REAR-PANEL closes the +X side", (0.70, 0.62))
            leader(ax, c, (40.0, 70.0, 224.0), "open payload top", (0.70, 0.86))
        if camname == "right":
            leader(ax, c, (79.0, 70.0, 170.0),
                   "BODY-REAR-PANEL\ncloses the +X side and carries\nboth pin-retention lands.\n"
                   "Its inner face is shown in the inset of\n"
                   "review_internal_mechanism_rear_panel_removed.png",
                   (0.055, 0.30))
        if camname == "front":
            dim3(ax, c, (-46.0, 0.0, -14.0), (79.0, 0.0, -14.0), "125")
            dim3(ax, c, (91.0, 0.0, 0.0), (91.0, 0.0, 224.0), "224")
            a = np.array(c.at((70.0, 0.0, 126.0)))
            b = np.array(c.at((70.0, 0.0, 216.0)))
            cvd.arrow(ax, tuple(a), tuple(b - a), text="platform travel 90",
                      color=DIMC, lw=3.2, size=12)
        if camname == "top":
            leader(ax, c, (35.0, 70.0, 216.0),
                   "PLATFORM support surface at TOP\nz = 216, i.e. 8 mm below the rim",
                   (0.70, 0.24))
            leader(ax, c, (16.0, 6.0, 224.0), "housing rim z = 224", (0.16, 0.80))
            dim3(ax, c, (11.0, 14.4, 224.0), (63.0, 14.4, 224.0), "52")
            dim3(ax, c, (63.0, 14.4, 224.0), (63.0, 125.6, 224.0), "111")
        swatches(ax, ALL7 if camname not in ("top",) else
                 ["BODY-HOUSING", "BODY-REAR-PANEL", "BODY-PLATFORM"])
        save(fig, name)
        record(name, title + " - " + sub, ALL7,
               "CRANK_180_TOP" if deg == 180 else "CRANK_0_BOTTOM", None)


def body_identification(bodies):
    print("-- body identification")
    c = CAMERAS["cutaway_iso"]
    deg = 240.0
    st = state_of(bodies, deg)
    fig = new_fig()
    pats = scene(bodies, deg, cut=("y", "above", 74.0),
                 cut_only=("BODY-HOUSING",), drop=("BODY-REAR-PANEL",), payload=True)
    panel = cut_half({b.id: b for b in bodies}["BODY-REAR-PANEL"].shape.moved(
        cv.translation((88.0, 0.0, 0.0))), "y", "above", 74.0)
    pats = pats + patches_of(panel, "BODY-REAR-PANEL", 0.4)
    ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0], pats, c)
    header(ax, "EXE-BM002-01   Product body identification",
           "seven product bodies; housing cut at y = 74 and the rear panel lifted "
           "88 mm off along +X, BOTH FOR DISPLAY ONLY")
    banner(ax, "DISPLAY CUTAWAY - THE MODEL IS UNCHANGED")
    cy, cz = st["crank_pin"]
    sz, pz = st["support_z"], st["plat_pin_z"]
    leader(ax, c, (40.0, 120.0, 60.0), "1   BODY-HOUSING", (0.045, 0.22))
    leader(ax, c, (167.0, 110.0, 150.0),
           "2   BODY-REAR-PANEL\n     lifted off for identification", (0.72, 0.90))
    leader(ax, c, (24.0, 40.0, sz), "3   BODY-PLATFORM", (0.045, 0.55))
    leader(ax, c, (-40.0, AY, AZ - 26.0), "4   BODY-CRANK-SHAFT", (0.045, 0.35))
    leader(ax, c, (48.0, AY, (cz + pz) / 2.0), "5   BODY-CONNECTING-ROD", (0.83, 0.47))
    leader(ax, c, (62.0, cy, cz), "6   BODY-CRANK-JOINT-PIN", (0.83, 0.36))
    leader(ax, c, (63.0, AY, pz), "7   BODY-PLATFORM-JOINT-PIN", (0.83, 0.57))
    leader(ax, c, (35.0, 70.0, sz + P["payload_z"]),
           "SCENARIO-PAYLOAD-1KG\nSCENARIO OBJECT - NOT A PRODUCT BODY",
           (0.60, 0.80), color=NOTEC)
    swatches(ax, ALL7 + ["SCENARIO-PAYLOAD-1KG"])
    caveat(ax, NOT_VERIFIED)
    save(fig, "review_body_identification.png")
    record("review_body_identification.png",
           "identifies all seven product bodies and the scenario payload",
           ALL7 + ["SCENARIO-PAYLOAD-1KG"],
           "crank 240 deg, chosen so that every body is visible", None,
           cutaway="housing cut at y = 74; rear panel lifted 88 mm along +X; display only")


def crank_interface(bodies):
    print("-- external crank user interface")
    deg = 300.0
    st = state_of(bodies, deg)
    cy, cz = st["crank_pin"]
    gy = AY + P["grip_offset"] * math.sin(math.radians(deg))
    gz = AZ - P["grip_offset"] * math.cos(math.radians(deg))
    fig = new_fig()

    # left panel: the crank face-on, where the 26 mm grip radius is a true circle
    cL = CAMERAS["crank_face"]
    axL = raster_axes(fig, [0.015, 0.30, 0.45, 0.60],
                      scene(bodies, deg), cL, px=(760, 620), frame="#3a3f45",
                      title="EXTERNAL: the crank face-on, looking +X")
    rot_arrow(axL, cL, (-46.0, AY, AZ), P["grip_offset"], text="grip sweep",
              a0=-70.0, a1=210.0)
    dim3(axL, cL, (-46.0, AY, AZ), (-46.0, gy, gz), "26", size=13)
    leader(axL, cL, (-40.0, gy, gz), "FEATURE-SHAFT-GRIP  O12\nthe part the hand turns",
           (0.04, 0.13))
    leader(axL, cL, (-18.0, AY + 24.0, AZ + 24.0), "FEATURE-SHAFT-HUB  O70",
           (0.60, 0.93))
    leader(axL, cL, (0.0, AY + 35.0, AZ), "housing -X wall\n(boundary crossing behind the hub)",
           (0.58, 0.06))

    # right panel: the same body's internal crank arm, where 45 mm lives
    cR = cvd.Camera(eye=(760.0, 70.0, 60.0), target=(36.0, 70.0, 60.0),
                    up=(0.0, 0.0, 1.0), scale=64.0)
    axR = raster_axes(fig, [0.50, 0.30, 0.45, 0.60],
                      scene(bodies, deg, drop=("BODY-REAR-PANEL",)), cR,
                      px=(760, 620), frame="#3a3f45",
                      title="INTERNAL: the same shaft's crank arm, looking -X")
    dim3(axR, cR, (36.0, AY, AZ), (36.0, cy, cz), "45", size=13)
    leader(axR, cR, (36.0, cy, cz), "FEATURE-SHAFT-CRANK-ARM\ncrank pin at radius 45",
           (0.60, 0.10))
    leader(axR, cR, (36.0, AY, AZ), "same crank-shaft axis\ny = 70, z = 60", (0.05, 0.90))

    axT = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    axT.set_axis_off()
    axT.set_xlim(0, 1); axT.set_ylim(0, 1)
    header(axT, "EXE-BM002-01   External crank - user interface",
           "the two radii below are DIFFERENT things on the SAME body; "
           "left panel is outside the housing, right panel is inside it")
    note(axT, 0.015, 0.27,
         "EXTERNAL HAND-GRIP RADIUS = 26 mm   (left panel)\n"
         "    the radius the user's hand actually turns on.\n\n"
         "INTERNAL CRANK RADIUS = 45 mm   (right panel)\n"
         "    the crank arm inside the housing. It sets the platform travel:\n"
         "    travel = 2 x 45 = 90 mm.\n\n"
         "Both are features of BODY-CRANK-SHAFT. They are NOT related by any\n"
         "gear ratio - this mechanism has no gearing at all. The hand moves on a\n"
         "26 mm radius; the crank pin moves on a 45 mm radius.",
         ec=NOTEC, fc="#fffdf5", size=11.5)
    note(axT, 0.985, 0.27,
         "HUMAN REVIEW QUESTIONS - not automatic PASS criteria\n"
         "  - Is the external grip visually and physically reachable?\n"
         "  - Is 26 mm a credible hand-crank radius for this product?\n"
         "  - Does the sweep look likely to foul the supporting surface\n"
         "    or nearby objects?  The grip reaches z = 34 at its lowest,\n"
         "    34 mm above the surface the housing stands on.\n"
         "  - Would a different handle radius or grip form be preferable?\n\n"
         "ERGONOMIC ADEQUACY AND USER EFFORT ARE NOT CLAIMED.",
         ec=ASMC, size=11.0, ha="right")
    caveat(axT, NOT_VERIFIED)
    save(fig, "review_external_crank_user_interface.png")
    record("review_external_crank_user_interface.png",
           "external grip, hub, boundary crossing, and the 26 vs 45 mm distinction "
           "shown side by side on the same body",
           ["BODY-CRANK-SHAFT", "BODY-HOUSING", "BODY-CONNECTING-ROD"],
           "crank 300 deg", None, details="two panels: exterior face-on, interior along -X")


def internal_views(bodies):
    print("-- internal mechanism")
    deg = 235.0
    st = state_of(bodies, deg)
    cy, cz = st["crank_pin"]
    pz, sz = st["plat_pin_z"], st["support_z"]

    # (a) rear panel removed, looking along -X, with an inset of what was removed
    c = CAMERAS["mech"]
    fig = new_fig()
    ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0],
                     scene(bodies, deg, drop=("BODY-REAR-PANEL",)), c)
    header(ax, "EXE-BM002-01   Internal mechanism, BODY-REAR-PANEL REMOVED FOR REVIEW",
           "looking along -X, so the crank/link motion plane is face-on; +Y to the right")
    banner(ax, "REAR PANEL REMOVED FOR REVIEW - IT IS PART OF THE PRODUCT")
    leader(ax, c, (36.0, AY, AZ), "crank-shaft axis\ny = 70, z = 60", (0.045, 0.30))
    leader(ax, c, (36.0, cy, cz), "crank joint pin", (0.045, 0.45))
    leader(ax, c, (35.0, AY - 20.0, AZ), "FEATURE-SHAFT-CRANK-ARM\nbehind the O70 hub",
           (0.045, 0.60))
    leader(ax, c, (48.0, AY, (cz + pz) / 2.0), "connecting rod", (0.045, 0.70))
    leader(ax, c, (48.0, AY, pz), "platform joint pin\nin the platform clevis", (0.665, 0.64))
    leader(ax, c, (36.0, 11.0, sz - 10.0), "front guide channel", (0.045, 0.80))
    leader(ax, c, (36.0, 129.0, sz - 10.0), "back guide channel", (0.665, 0.78))
    dim3(ax, c, (36.0, AY, AZ), (36.0, cy, cz), "R 45")
    dim3(ax, c, (48.0, cy, cz), (48.0, AY, pz), "85")
    _panel_inset(fig, bodies)
    swatches(ax, [i for i in ALL7 if i != "BODY-REAR-PANEL"])
    caveat(ax, NOT_VERIFIED)
    save(fig, "review_internal_mechanism_rear_panel_removed.png")
    record("review_internal_mechanism_rear_panel_removed.png",
           "whole linkage with the rear panel taken off; inset shows what the panel carries",
           [i for i in ALL7 if i != "BODY-REAR-PANEL"], "crank 235 deg", None,
           cutaway="BODY-REAR-PANEL removed for review",
           details="inset: the removed rear panel and its two retention lands")

    # (b) cutaway isometric: exterior handle and interior linkage together
    c = CAMERAS["cutaway_iso"]
    fig = new_fig()
    ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0],
                     scene(bodies, deg, cut=("y", "above", 74.0),
                           cut_only=("BODY-HOUSING", "BODY-REAR-PANEL")), c)
    header(ax, "EXE-BM002-01   Internal mechanism, cutaway isometric",
           "housing and rear panel cut at y = 74 FOR DISPLAY ONLY; "
           "the exterior handle and the interior linkage are in one view")
    banner(ax, "DISPLAY CUTAWAY - THE MODEL IS UNCHANGED")
    triad_axes(ax, c)
    leader(ax, c, (-40.0, AY, AZ - 26.0), "external grip, outside the housing",
           (0.045, 0.34))
    leader(ax, c, (16.0, AY - 34.0, AZ), "shaft running in the two housing\njournal lands",
           (0.045, 0.50))
    leader(ax, c, (35.0, cy, cz), "crank arm and crank joint pin", (0.80, 0.36))
    leader(ax, c, (48.0, AY, pz), "connecting rod up to the\nplatform clevis", (0.80, 0.50))
    leader(ax, c, (30.0, 129.0, sz - 8.0), "back guide channel", (0.80, 0.66))
    leader(ax, c, (30.0, AY, sz), "platform support surface", (0.045, 0.66))
    swatches(ax, ALL7)
    caveat(ax, NOT_VERIFIED)
    save(fig, "review_internal_mechanism_cutaway_iso.png")
    record("review_internal_mechanism_cutaway_iso.png",
           "cutaway isometric showing the exterior handle and the internal linkage together",
           ALL7, "crank 235 deg", None,
           cutaway="housing and rear panel cut at y = 74, display only")

    # (c) annotated chain with feature ids
    deg = 90.0
    st = state_of(bodies, deg)
    cy, cz = st["crank_pin"]
    pz, sz = st["plat_pin_z"], st["support_z"]
    c = CAMERAS["mech"]
    fig = new_fig()
    ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0],
                     scene(bodies, deg, drop=("BODY-REAR-PANEL",)), c)
    header(ax, "EXE-BM002-01   Kinematic chain, annotated with feature IDs",
           "CRANK_90_RISING; rear panel removed; looking along -X")
    chain = [
        ((-40.0, AY, AZ - 26.0), "1  FEATURE-SHAFT-GRIP\n     outside the housing", (0.045, 0.20)),
        ((4.0, AY + 34.0, AZ), "2  FEATURE-HOUSING-JOURNAL-1\n     also the boundary crossing", (0.045, 0.33)),
        ((20.0, AY - 34.0, AZ), "3  FEATURE-HOUSING-JOURNAL-2", (0.045, 0.44)),
        ((35.0, AY - 22.0, AZ - 22.0), "4  FEATURE-SHAFT-CRANK-ARM   R 45", (0.045, 0.55)),
        ((36.0, cy, cz), "5  BODY-CRANK-JOINT-PIN\n     in FEATURE-SHAFT-CRANK-PIN-BORE\n     and FEATURE-ROD-CRANK-BORE", (0.045, 0.68)),
        ((48.0, (cy + AY) / 2.0, (cz + pz) / 2.0), "6  BODY-CONNECTING-ROD\n     85 mm between bore centres", (0.72, 0.46)),
        ((48.0, AY, pz), "7  BODY-PLATFORM-JOINT-PIN\n     in FEATURE-ROD-PLATFORM-BORE\n     and both clevis lugs", (0.72, 0.60)),
        ((30.0, AY, sz), "8  FEATURE-PLATFORM-SUPPORT-SURFACE", (0.72, 0.73)),
        ((30.0, 11.0, sz - 12.0), "9  FEATURE-HOUSING-GUIDE-FRONT\n     + FEATURE-PLATFORM-FOLLOWER-FRONT", (0.045, 0.82)),
        ((30.0, 129.0, sz - 12.0), "10 FEATURE-HOUSING-GUIDE-BACK\n     + FEATURE-PLATFORM-FOLLOWER-BACK", (0.72, 0.86)),
    ]
    for pt, txt, xy in chain:
        leader(ax, c, pt, txt, xy, size=10.2)
    note(ax, 0.5, 0.075,
         "CHAIN:  grip -> shaft -> journal land 1 -> journal land 2 -> crank arm -> "
         "crank joint pin ->\nconnecting rod -> platform joint pin -> platform clevis "
         "-> platform -> guide followers -> guide channels -> housing",
         ec=DIMC, size=11.0, ha="center", va="bottom")
    note(ax, 0.045, 0.155,
         "Items 1 to 4 lie BEHIND the O70 hub and inside the housing wall,\n"
         "so this view can only point at where they are. They are drawn in\n"
         "SECTION A-A (shaft, both journal lands, overhung arm) and the\n"
         "crank arm is exposed in SECTION B-B.", ec=NOTEC, size=10.5, va="bottom")
    save(fig, "review_kinematic_chain_annotated.png")
    record("review_kinematic_chain_annotated.png",
           "the complete crank-to-platform chain with feature IDs",
           [i for i in ALL7 if i != "BODY-REAR-PANEL"], "CRANK_90_RISING", None,
           cutaway="BODY-REAR-PANEL removed for review")


def _panel_inset(fig, bodies):
    c = cvd.Camera(eye=(-460.0, -320.0, 250.0), target=(70.0, 70.0, 112.0),
                   up=(0.0, 0.0, 1.0), scale=132.0)
    d = {b.id: b for b in bodies}
    ax2 = raster_axes(fig, [0.700, 0.045, 0.255, 0.40],
                      patches_of(d["BODY-REAR-PANEL"].shape, "BODY-REAR-PANEL", 0.4),
                      c, px=(430, 680), bg="#ffffff", frame=NOTEC,
                      title="REMOVED: BODY-REAR-PANEL, inner face.\n"
                            "It carries BOTH pin-retention lands.")
    leader(ax2, c, (67.0, AY + 45.0, AZ + 6.0),
           "CRANK-PIN-LAND\nannulus r 36-54", (0.50, 0.13), size=8.4, ha="center")
    leader(ax2, c, (67.0, AY, 160.0),
           "PLATFORM-PIN-LAND\ny 61-79, z 94-200", (0.50, 0.90), size=8.4, ha="center")


# ==================================================== orthographic sections
def section_AA(bodies):
    disp = list(B.bodies_at(bodies, P, 0.0))
    fig = new_fig()
    axM = fig.add_axes([0.05, 0.09, 0.60, 0.76])
    draw_section(axM, disp, "y", 70.0, (-52.0, 92.0, -6.0, 132.0))
    axM.set_xlabel("X (mm)", fontsize=9.5)
    axM.set_ylabel("Z (mm)", fontsize=9.5)
    axM.set_title("SECTION A-A    cut on the plane y = 70, through the crank-shaft axis\n"
                  "orthographic, cut faces hatched, CRANK_0_BOTTOM", fontsize=11.5,
                  weight="bold", pad=6)
    for x, lab in ((0.0, "housing outer face x=0"), (71.0, "panel seat x=71")):
        axM.axvline(x, color=NOTEC, lw=1.1, ls=(0, (7, 4)), zorder=6)
        axM.text(x, -5.0, " " + lab, color=NOTEC, fontsize=8.4, rotation=90,
                 ha="right", va="bottom", zorder=7)
    sect_label(axM, (-32.0, 34.0), "FEATURE-SHAFT-GRIP  O12 at radius 26\n"
                                   "entirely outside the housing", (-46.0, 118.0))
    sect_label(axM, (-10.0, 60.0), "FEATURE-SHAFT-HUB  O70\ncrosses the wall AND is the\n"
                                   "journal surface for both lands", (-44.0, 92.0))
    sect_label(axM, (20.0, 40.0), "OVERHUNG CRANK ARM  x 30-40\n"
                                  "both journal lands are on its -X side", (-42.0, 12.0))
    sect_label(axM, (75.0, 60.0), "BODY-REAR-PANEL  x 71-79\ncarries NO shaft journal",
               (58.0, 122.0))
    sect_label(axM, (48.0, 60.0), "BODY-CONNECTING-ROD\nx 42-54", (60.0, 100.0))
    sect_arrow(axM, (-26.0, 72.0), (44.0, 0.0), "crank shaft inserted -X",
               color=ASMC, tpos=0.5, toff=(0.0, 7.0))
    det = (-2.0, 32.0, 88.0, 106.0)
    detail_box(axM, det, "DETAIL 1")
    det2 = (24.0, 34.0, 92.0, 104.0)

    axD = fig.add_axes([0.685, 0.47, 0.30, 0.40])
    draw_section(axD, disp, "y", 70.0, det, lw=1.2)
    axD.set_title("DETAIL 1  -  the two journal lands and the relief between them\n"
                  "(enlarged; a 0.2 mm running clearance is one pixel at full size)",
                  fontsize=9.6, weight="bold", color=NOTEC, pad=4)
    axD.set_xlabel("X (mm)", fontsize=8.5)
    hub_top = AZ + G["hub_r"]
    sect_dim(axD, (4.0, hub_top), (4.0, hub_top + P["journal_clearance"]),
             "0.2", toff=(3.4, 0.0), size=9.0)
    sect_dim(axD, (11.0, hub_top), (11.0, hub_top + P["journal_clearance"]
                                    + P["relief_extra_r"]), "3.2", toff=(3.4, 0.0),
             size=9.0)
    sect_dim(axD, (20.0, hub_top), (20.0, hub_top + P["journal_clearance"]),
             "0.2", toff=(3.4, 0.0), size=9.0)
    sect_label(axD, (4.0, hub_top + 3.0), "LAND 1\nx 0-8", (1.0, 103.0), size=8.6)
    sect_label(axD, (11.0, hub_top + 4.0), "RELIEF\nx 8-14", (10.0, 90.5), size=8.6)
    sect_label(axD, (20.0, hub_top + 3.0), "LAND 2\nx 14-26", (22.0, 103.0), size=8.6)

    axE = fig.add_axes([0.685, 0.09, 0.30, 0.29])
    draw_section(axE, disp, "y", 70.0, det2, lw=1.2)
    axE.set_title("DETAIL 2  -  the shaft's thrust collar against the journal boss",
                  fontsize=9.6, weight="bold", color=NOTEC, pad=4)
    axE.set_xlabel("X (mm)", fontsize=8.5)
    sect_dim(axE, (26.0, 99.0), (27.0, 99.0), "1.0", toff=(0.0, 1.6), size=9.0)
    sect_label(axE, (28.5, 96.0), "thrust collar O80\n(pull-out stop)", (30.0, 101.0),
               size=8.6)
    axT = fig.add_axes([0, 0, 1, 1]); axT.set_axis_off()
    note(axT, 0.05, 0.075,
         "BOTH journal lands belong to BODY-HOUSING.  The rear panel is not a shaft "
         "journal:\nthe connecting rod occupies the crank axis, so the shaft cannot "
         "reach the panel.", ec=DIMC, size=10.5, va="top")
    caveat(axT, NOT_VERIFIED)
    save(fig, "review_section_AA_shaft_and_dual_journals.png")
    record("review_section_AA_shaft_and_dual_journals.png",
           "shaft, boundary crossing, both housing journal lands, relief, thrust "
           "collar and the overhung arm", ALL7, "CRANK_0_BOTTOM", "y = 70 (normal Y)",
           details="DETAIL 1 journal lands and relief; DETAIL 2 thrust collar")


def section_BB(bodies):
    c = CAMERAS["mech"]
    for tag, deg, fn in (("BOTTOM", 0.0, "bottom"), ("MID-STROKE", 90.0, "mid"),
                         ("TOP", 180.0, "top")):
        st = state_of(bodies, deg)
        cy, cz = st["crank_pin"]
        pz, sz, ra = st["plat_pin_z"], st["support_z"], st["rod_angle"]
        fig = new_fig()
        ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0],
                         scene(bodies, deg, drop=("BODY-REAR-PANEL",),
                               cut=("x", "above", 30.0),
                               cut_only=("BODY-HOUSING", "BODY-CRANK-SHAFT")), c)
        header(ax, "EXE-BM002-01   SECTION B-B   crank / link / platform chain - %s" % tag,
               "view normal to the motion plane (along -X); housing and crank shaft cut at "
               "x = 30 so the CRANK ARM is exposed instead of the hub;\n"
               "identical camera and scale in all three")
        banner(ax, "B-B   %s   crank %.0f deg" % (tag, deg))
        dim3(ax, c, (36.0, AY, AZ), (36.0, cy, cz), "CRANK RADIUS 45")
        dim3(ax, c, (48.0, cy, cz), (48.0, AY, pz), "ROD CENTRES 85")
        leader(ax, c, (35.0, AY, AZ), "crank axis  y 70, z 60", (0.045, 0.30))
        leader(ax, c, (35.0, cy, cz), "crank joint", (0.045, 0.44))
        leader(ax, c, (35.0, AY + (cy - AY) * 0.5, AZ + (cz - AZ) * 0.5),
               "FEATURE-SHAFT-CRANK-ARM\n(the O70 hub is cut away here)", (0.045, 0.58))
        leader(ax, c, (48.0, AY, pz), "platform joint  z = %.1f" % pz, (0.72, 0.52))
        leader(ax, c, (30.0, AY, sz), "SUPPORT SURFACE  z = %.1f" % sz, (0.72, 0.66))
        leader(ax, c, (30.0, 129.0, sz - 14.0),
               "guide channel: travel\ndirection is vertical", (0.70, 0.29))
        note(ax, 0.045, 0.10,
             "crank angle            %6.1f deg\n"
             "connecting-rod angle   %6.2f deg from vertical\n"
             "platform pin  z        %6.1f mm\n"
             "support surface z      %6.1f mm" % (deg, ra, pz, sz),
             ec=ASMC, mono=True, size=11.5, va="bottom")
        if tag in ("BOTTOM", "TOP"):
            caveat(ax, "KINEMATIC EXTREMUM - NOT A VERIFIED PHYSICAL HARD STOP.   " + NOT_VERIFIED)
        else:
            caveat(ax, NOT_VERIFIED)
        swatches(ax, [i for i in ALL7 if i != "BODY-REAR-PANEL"])
        save(fig, "review_section_BB_crank_link_platform_%s.png" % fn)
        record("review_section_BB_crank_link_platform_%s.png" % fn,
               "crank/link/platform chain at %s, same plane camera and scale" % tag,
               [i for i in ALL7 if i != "BODY-REAR-PANEL"], "crank %.0f deg" % deg,
               "view normal to the motion plane (along -X)",
               cutaway="housing and crank shaft cut at x = 30; rear panel removed")


def section_CC(bodies):
    for tag, deg, fn in (("BOTTOM", 0.0, "bottom"), ("MID-STROKE", 90.0, "mid"),
                         ("TOP", 180.0, "top")):
        st = state_of(bodies, deg)
        sz = st["support_z"]
        disp = list(B.bodies_at(bodies, P, deg))
        plate_mid = sz - P["plate_t"] / 2.0
        fig = new_fig()
        axM = fig.add_axes([0.05, 0.09, 0.50, 0.78])
        draw_section(axM, disp, "x", 33.0, (-6.0, 146.0, 80.0, 236.0))
        axM.set_xlabel("Y (mm)", fontsize=9.5)
        axM.set_ylabel("Z (mm)", fontsize=9.5)
        axM.set_title("SECTION C-C  %s    cut on the plane x = 33\n"
                      "orthographic, cut faces hatched, crank %.0f deg"
                      % (tag, deg), fontsize=11.5, weight="bold", pad=6)
        sect_label(axM, (70.0, sz), "FEATURE-PLATFORM-SUPPORT-SURFACE\nz = %.1f" % sz,
                   (70.0, 228.0))
        det_f = (4.0, 21.0, sz - 17.0, sz + 6.0)
        det_b = (119.0, 136.0, sz - 17.0, sz + 6.0)
        detail_box(axM, det_f, "DETAIL F")
        detail_box(axM, det_b, "DETAIL B")
        sect_arrow(axM, (70.0, sz - 34.0), (0.0, 24.0), "platform travel",
                   color=DIMC, tpos=0.55, toff=(0.0, -3.0))

        axF = fig.add_axes([0.585, 0.53, 0.185, 0.34])
        draw_section(axF, disp, "x", 33.0, det_f, lw=1.2)
        axF.set_title("DETAIL F - front guide", fontsize=9.4, weight="bold",
                      color=NOTEC, pad=4)
        sect_dim(axF, (G["groove_f_y0"], sz - 16.0), (G["foll_f_y0"], sz - 16.0),
                 "0.4", toff=(0.0, -1.8), size=8.6)
        sect_dim(axF, (G["boss_f_y1"], sz - 4.0), (G["plate_y0"], sz - 4.0),
                 "0.4", toff=(2.6, 2.2), size=8.6)
        sect_label(axF, (11.0, sz - 12.0), "follower\n26 x 5.6 x 16", (16.5, sz - 17.0),
                   size=8.4)
        sect_label(axF, (8.6, sz - 6.0), "channel\nfloor y=8", (5.2, sz + 4.0), size=8.4)

        axB = fig.add_axes([0.795, 0.53, 0.185, 0.34])
        draw_section(axB, disp, "x", 33.0, det_b, lw=1.2)
        axB.set_title("DETAIL B - back guide", fontsize=9.4, weight="bold",
                      color=NOTEC, pad=4)
        sect_dim(axB, (G["foll_b_y1"], sz - 16.0), (G["groove_b_y1"], sz - 16.0),
                 "0.4", toff=(0.0, -1.8), size=8.6)
        sect_dim(axB, (G["plate_y1"], sz - 4.0), (G["boss_b_y0"], sz - 4.0),
                 "0.4", toff=(-2.6, 2.2), size=8.6)
        sect_label(axB, (129.0, sz - 12.0), "follower", (121.0, sz - 17.0), size=8.4)

        # plan cut through the plate: this is where the 0.2 side clearance lives
        axP = fig.add_axes([0.585, 0.09, 0.395, 0.34])
        draw_section(axP, disp, "z", plate_mid, (12.0, 58.0, 2.0, 22.0), lw=1.2)
        axP.set_title("DETAIL S  -  plan cut at z = %.1f, through the plate.\n"
                      "This is the plane the 0.2 mm SIDE clearance is visible in."
                      % plate_mid, fontsize=9.4, weight="bold", color=NOTEC, pad=4)
        axP.set_xlabel("X (mm)", fontsize=8.5)
        axP.set_ylabel("Y (mm)", fontsize=8.5)
        sect_dim(axP, (G["groove_x0"], 10.0), (P["follower_x0"], 10.0), "0.2",
                 toff=(-2.0, 2.4), size=8.6)
        sect_dim(axP, (P["follower_x1"], 10.0), (G["groove_x1"], 10.0), "0.2",
                 toff=(2.0, 2.4), size=8.6)
        sect_label(axP, (35.0, 11.0), "front follower in its channel, x 22-48 in a "
                                      "21.8-48.2 slot", (35.0, 18.0), size=8.4)

        axT = fig.add_axes([0, 0, 1, 1]); axT.set_axis_off()
        note(axT, 0.05, 0.072,
             "Both guides engaged.  Side clearance 0.2 each side, tip clearance 0.4, "
             "plate-edge gap 0.4 - all measured, see validation/interaction_report.json "
             "INT-14 and INT-15.", ec=DIMC, size=10.2, va="bottom")
        caveat(axT, NOT_VERIFIED)
        save(fig, "review_section_CC_platform_guides_%s.png" % fn)
        record("review_section_CC_platform_guides_%s.png" % fn,
               "both guide channels and followers at %s, with the three clearances "
               "enlarged" % tag, ALL7, "crank %.0f deg" % deg,
               "x = 33 (normal X) main; z = %.1f (normal Z) for the side clearance"
               % plate_mid,
               details="DETAIL F front guide, DETAIL B back guide, DETAIL S plan cut")


def section_DD(bodies):
    disp = list(B.bodies_at(bodies, P, 0.0))
    fig = new_fig()
    axM = fig.add_axes([0.055, 0.10, 0.55, 0.76])
    draw_section(axM, disp, "y", 70.0, (24.0, 86.0, -2.0, 40.0))
    axM.set_xlabel("X (mm)", fontsize=9.5)
    axM.set_ylabel("Z (mm)", fontsize=9.5)
    axM.set_title("SECTION D-D    crank joint pin and its two axial stops\n"
                  "cut on the plane y = 70 (the A-A plane), CRANK_0_BOTTOM",
                  fontsize=11.5, weight="bold", pad=6)
    z = G["crank_pin_z_bottom"]
    sect_label(axM, (35.0, z + 9.0), "FEATURE-SHAFT-CRANK-ARM\nbore O10.2, x 30-40",
               (27.0, 36.0))
    sect_label(axM, (48.0, z + 9.5), "FEATURE-ROD-CRANK-BORE\nO10.2, x 42-54",
               (43.0, 36.0))
    sect_label(axM, (58.0, z + 8.5), "-X STOP: the pin head seats on the\n"
                                     "rod's +X face.  Measured free travel 0.000",
               (52.0, 1.0))
    sect_label(axM, (69.0, z + 4.0), "+X STOP: FEATURE-PANEL-CRANK-PIN-LAND,\n"
                                     "integral to BODY-REAR-PANEL.\n"
                                     "Annulus r 36-54, so it faces the pin head\n"
                                     "at EVERY crank angle.", (57.0, 30.0))
    sect_dim(axM, (65.0, z), (67.0, z), "2.0", toff=(0.0, -3.4))
    sect_arrow(axM, (84.0, 38.0), (-18.0, 0.0), "pin inserted -X", color=ASMC,
               tpos=0.5, toff=(0.0, 2.2))
    det = (29.0, 43.0, z - 8.0, z + 8.0)
    detail_box(axM, det, "DETAIL P")

    axD = fig.add_axes([0.645, 0.34, 0.33, 0.52])
    draw_section(axD, disp, "y", 70.0, det, lw=1.3)
    axD.set_title("DETAIL P  -  the pin in the crank arm bore\n"
                  "0.1 mm radial running clearance, enlarged", fontsize=9.6,
                  weight="bold", color=NOTEC, pad=4)
    axD.set_xlabel("X (mm)", fontsize=8.5)
    sect_dim(axD, (35.0, z + G["pin_r"]), (35.0, z + G["pin_bore_r"]), "0.1",
             toff=(2.6, 0.6), size=9.2)
    sect_label(axD, (36.0, z - G["pin_r"]), "BODY-CRANK-JOINT-PIN  O10",
               (34.0, z - 6.0), size=8.8, ha="center")
    axT = fig.add_axes([0, 0, 1, 1]); axT.set_axis_off()
    note(axT, 0.645, 0.30,
         "The rear-panel land is INTEGRAL to the panel.\n"
         "It is not a separate retainer: there is no circlip,\n"
         "washer or screw anywhere in this product.\n\n"
         "Measured: -X travel 0.000 mm blocked by the rod,\n"
         "+X travel 2.000 mm blocked by the rear panel.",
         ec=DIMC, size=10.2, va="top")
    caveat(axT, NOT_VERIFIED)
    save(fig, "review_section_DD_crank_joint_retention.png")
    record("review_section_DD_crank_joint_retention.png",
           "crank joint pin, both bores, and both axial stops including the panel land",
           ALL7, "CRANK_0_BOTTOM", "y = 70 (normal Y)",
           details="DETAIL P: 0.1 mm bore clearance enlarged")


def section_EE(bodies):
    disp = list(B.bodies_at(bodies, P, 0.0))
    z = G["plat_pin_z_bottom"]
    fig = new_fig()
    axM = fig.add_axes([0.055, 0.10, 0.55, 0.76])
    draw_section(axM, disp, "y", 70.0, (26.0, 86.0, 82.0, 132.0))
    axM.set_xlabel("X (mm)", fontsize=9.5)
    axM.set_ylabel("Z (mm)", fontsize=9.5)
    axM.set_title("SECTION E-E    platform joint pin and its two axial stops\n"
                  "cut on the plane y = 70 (the A-A plane), CRANK_0_BOTTOM",
                  fontsize=11.5, weight="bold", pad=6)
    sect_label(axM, (38.0, z - 8.0), "FEATURE-PLATFORM-CLEVIS-LUG-A\nx 35-41",
               (29.0, 86.0))
    sect_label(axM, (48.0, z + 8.0), "FEATURE-ROD-PLATFORM-BORE\nx 42-54",
               (38.0, 128.0))
    sect_label(axM, (58.0, z - 8.0), "FEATURE-PLATFORM-CLEVIS-LUG-B  x 55-61\n"
                                     "two lugs straddle the rod, so the joint\n"
                                     "is not a cantilever", (50.0, 86.0))
    sect_label(axM, (63.0, z + 6.0), "-X STOP: pin head on lug B's +X face\n"
                                     "measured free travel 0.000", (52.0, 128.0))
    sect_label(axM, (69.0, z + 2.0), "+X STOP: FEATURE-PANEL-PLATFORM-PIN-LAND,\n"
                                     "integral to BODY-REAR-PANEL.\nSpans z 94-200, "
                                     "the pin's whole travel.", (64.0, 120.0))
    sect_dim(axM, (65.0, z), (67.0, z), "2.0", toff=(0.0, -3.6))
    sect_arrow(axM, (83.0, 88.0), (-18.0, 0.0), "pin inserted -X", color=ASMC,
               tpos=0.5, toff=(0.0, 2.4))
    det = (33.0, 45.0, z - 8.0, z + 8.0)
    detail_box(axM, det, "DETAIL Q")

    axD = fig.add_axes([0.645, 0.34, 0.33, 0.52])
    draw_section(axD, disp, "y", 70.0, det, lw=1.3)
    axD.set_title("DETAIL Q  -  the pin in clevis lug A\n"
                  "0.1 mm radial running clearance, enlarged", fontsize=9.6,
                  weight="bold", color=NOTEC, pad=4)
    axD.set_xlabel("X (mm)", fontsize=8.5)
    sect_dim(axD, (38.0, z + G["pin_r"]), (38.0, z + G["pin_bore_r"]), "0.1",
             toff=(2.6, 0.6), size=9.2)
    sect_label(axD, (39.0, z - G["pin_r"]), "BODY-PLATFORM-JOINT-PIN  O10",
               (38.0, z - 6.0), size=8.8, ha="center")
    axT = fig.add_axes([0, 0, 1, 1]); axT.set_axis_off()
    note(axT, 0.645, 0.30,
         "Measured: -X travel 0.000 mm blocked by the platform,\n"
         "+X travel 2.000 mm blocked by the rear panel.\n\n"
         "Both lands arrive in the SAME -X motion that seats the\n"
         "panel, so the pins are captured the moment the product\n"
         "is closed and not before.", ec=DIMC, size=10.2, va="top")
    caveat(axT, NOT_VERIFIED)
    save(fig, "review_section_EE_platform_joint_retention.png")
    record("review_section_EE_platform_joint_retention.png",
           "platform joint pin, clevis lugs, rod bore and both axial stops",
           ALL7, "CRANK_0_BOTTOM", "y = 70 (normal Y)",
           details="DETAIL Q: 0.1 mm bore clearance enlarged")


def section_FF(bodies):
    for tag, deg, fn, gap in (("BOTTOM", 0.0, "bottom", 98.0),
                              ("TOP", 180.0, "top", 8.0)):
        st = state_of(bodies, deg)
        sz = st["support_z"]
        disp = list(B.bodies_at(bodies, P, deg)) + [
            Disp("SCENARIO-PAYLOAD-1KG", payload_solid(sz))]
        fig = new_fig()
        axM = fig.add_axes([0.07, 0.09, 0.56, 0.79])
        draw_section(axM, disp, "x", 33.0, (-6.0, 146.0, 86.0, 292.0))
        axM.set_xlabel("Y (mm)", fontsize=9.5)
        axM.set_ylabel("Z (mm)", fontsize=9.5)
        axM.set_title("SECTION F-F  %s    payload access, cut on the plane x = 33\n"
                      "orthographic, cut faces hatched, crank %.0f deg" % (tag, deg),
                      fontsize=11.5, weight="bold", pad=6)
        axM.axhline(224.0, color=NOTEC, lw=1.2, ls=(0, (7, 4)), zorder=6)
        sect_label(axM, (10.0, 224.0), "HOUSING RIM  z = 224\n"
                                       "this is the APERTURE, not the endpoint",
                   (22.0, 268.0))
        sect_label(axM, (100.0, sz + 20.0),
                   "SCENARIO-PAYLOAD-1KG  36 x 60 x 40\n"
                   "SCENARIO OBJECT - NOT A PRODUCT BODY\n"
                   "1 KG SCENARIO DECLARED\n"
                   "STRUCTURAL CAPACITY NOT VERIFIED", (88.0, 250.0))
        sect_label(axM, (56.0, sz),
                   "FEATURE-PLATFORM-SUPPORT-SURFACE  z = %.1f\n"
                   "the access path ENDS on this face" % sz, (16.0, sz - 22.0))
        sect_dim(axM, (140.0, sz), (140.0, 224.0), "%.0f" % gap, toff=(-9.0, 0.0))
        sect_arrow(axM, (70.0, 262.0), (0.0, -(262.0 - sz - 1.0)),
                   "payload placed through the top,\ndown onto the PLATFORM",
                   tpos=0.34, toff=(-34.0, 0.0))
        axT = fig.add_axes([0, 0, 1, 1]); axT.set_axis_off()
        note(axT, 0.985, 0.86,
             "MEASURED, at this state:\n"
             "   support surface            z = %.1f mm\n"
             "   housing rim                z = 224.0 mm\n"
             "   rim to support surface       %.0f mm\n"
             "   overlap during descent       0.000000 mm3\n"
             "   seated distance to platform  0.000000 mm\n\n"
             "The endpoint is the PLATFORM SURFACE.  Accepting the rim\n"
             "as the endpoint is the defect NEG-BM-002-007 describes,\n"
             "and negative control NC-14 tests for it.\n\n"
             "1 KG SCENARIO DECLARED.\n"
             "STRUCTURAL CAPACITY NOT VERIFIED - no strength evidence\n"
             "exists at any fidelity (DOS-BM-002 S5)."
             % (sz, gap), ec=NOTEC, size=10.8, ha="right", va="top")
        note(axT, 0.985, 0.34,
             "HUMAN REVIEW QUESTIONS\n"
             "  - Is payload access adequate at BOTTOM and at TOP?\n"
             "  - Is the 8 mm top recess acceptable, or should the\n"
             "    platform come further up or the rim come down?\n"
             "  - Is an open-top arrangement acceptable for this product?",
             ec=ASMC, size=10.5, ha="right", va="top")
        caveat(axT, NOT_VERIFIED)
        save(fig, "review_section_FF_payload_access_%s.png" % fn)
        record("review_section_FF_payload_access_%s.png" % fn,
               "payload access path terminating on the platform support surface at %s" % tag,
               ALL7 + ["SCENARIO-PAYLOAD-1KG"], "crank %.0f deg" % deg,
               "x = 33 (normal X)")


def sections_overview(bodies):
    deg = 90.0
    st = state_of(bodies, deg)
    c = CAMERAS["mech"]
    fig = new_fig()
    ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0],
                     scene(bodies, deg, drop=("BODY-REAR-PANEL",)), c)
    header(ax, "EXE-BM002-01   Operation overview, with the locations of sections A-A to F-F",
           "CRANK_90_RISING; rear panel removed; looking along -X")
    p0, p1 = c.at((36.0, 70.0, -10.0)), c.at((36.0, 70.0, 244.0))
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=NOTEC, lw=1.6,
            ls=(0, (9, 4, 2, 4)), zorder=28)
    for pt, lab in ((p1, "A-A / D-D / E-E"), (p0, "cut y = 70")):
        ax.text(pt[0], pt[1], lab, color=NOTEC, fontsize=10.5, weight="bold",
                ha="center", va="center", zorder=29,
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec=NOTEC, lw=1.0))
    note(ax, 0.045, 0.09,
         "A-A   cut y = 70   shaft, boundary crossing, BOTH housing journal lands, overhung arm\n"
         "B-B   view along -X  crank / link / platform chain, at BOTTOM, MID-STROKE and TOP\n"
         "C-C   cut x = 33   both guide channels and followers, at BOTTOM, MID-STROKE and TOP\n"
         "D-D   cut y = 70   crank joint pin and its two axial stops (detail on the A-A plane)\n"
         "E-E   cut y = 70   platform joint pin and its two axial stops (detail on the A-A plane)\n"
         "F-F   cut x = 33   payload access, from the rim down to the support surface",
         ec=NOTEC, size=11.0, va="bottom", mono=False)
    note(ax, 0.955, 0.30,
         "C-C and F-F are cut at x = 33,\nnormal to this view - i.e. on a\n"
         "plane parallel to the page.", ec=ASMC, size=10.5, ha="right", va="top")
    caveat(ax, NOT_VERIFIED)
    save(fig, "review_overview_operation_and_sections.png")
    record("review_overview_operation_and_sections.png",
           "locates sections A-A to F-F on the mechanism", ALL7, "CRANK_90_RISING",
           None, cutaway="BODY-REAR-PANEL removed for review")


# ================================================================ storyboards
OP_FRAMES = [
    ("01_bottom", 0.0, "BOTTOM"),
    ("02_rising_45", 45.0, "RISING"),
    ("03_rising_90", 90.0, "RISING"),
    ("04_rising_135", 135.0, "RISING"),
    ("05_top", 180.0, "TOP"),
    ("06_lowering_225", 225.0, "LOWERING"),
    ("07_lowering_270", 270.0, "LOWERING"),
    ("08_lowering_315", 315.0, "LOWERING"),
    ("09_bottom_return", 360.0, "BOTTOM RETURN"),
]


def operation_storyboard(bodies):
    print("-- operation storyboard")
    c = CAMERAS["mech"]
    for fn, deg, state in OP_FRAMES:
        st = state_of(bodies, deg)
        cy, cz = st["crank_pin"]
        pz, sz, ra = st["plat_pin_z"], st["support_z"], st["rod_angle"]
        fig = new_fig()
        ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0],
                         scene(bodies, deg, drop=("BODY-REAR-PANEL",), payload=True), c)
        header(ax, "EXE-BM002-01   Operation storyboard %s of 9" % fn.split("_")[0],
               "rear panel removed; identical camera and scale in all nine frames")
        banner(ax, "%s    crank %.0f deg" % (state, deg))
        note(ax, 0.045, 0.10,
             "crank angle            %6.1f deg\n"
             "support-surface z      %6.1f mm\n"
             "connecting-rod angle   %6.2f deg from vertical\n"
             "state                  %s" % (deg, sz, ra, state),
             ec=ASMC, mono=True, size=12.0, va="bottom")
        # The crank pin sits at plane-angle (deg - 90) in the (y right, z up) frame
        # this camera shows, and theta increases with the storyboard, so the arc must
        # sweep to INCREASING angle and put its head ahead of the pin. Drawing it the
        # other way round said the platform was being lowered while it rose.
        rot_arrow(ax, c, (36.0, AY, AZ), 58.0, text="crank turns this way",
                  a0=deg - 150.0, a1=deg - 50.0, size=10.5, tpos=0.06)
        if state in ("RISING", "LOWERING"):
            up = state == "RISING"
            z0 = sz + 14.0 if up else sz + 44.0
            z1 = sz + 44.0 if up else sz + 14.0
            a = np.array(c.at((30.0, 24.0, z0)))
            b = np.array(c.at((30.0, 24.0, z1)))
            cvd.arrow(ax, tuple(a), tuple(b - a),
                      text="platform %s" % state, color=DIMC, lw=3.4, size=12)
        leader(ax, c, (30.0, AY, sz), "support surface  z = %.1f" % sz, (0.72, 0.60))
        leader(ax, c, (36.0, cy, cz), "crank pin", (0.045, 0.44))
        leader(ax, c, (35.0, 70.0, sz + P["payload_z"] / 2.0),
               "SCENARIO-PAYLOAD-1KG\nscenario object, moves with the platform\n"
               "for visualisation only", (0.70, 0.76), color=NOTEC)
        swatches(ax, [i for i in ALL7 if i != "BODY-REAR-PANEL"]
                 + ["SCENARIO-PAYLOAD-1KG"])
        if state in ("BOTTOM", "TOP", "BOTTOM RETURN"):
            caveat(ax, "KINEMATIC EXTREMUM - NOT A VERIFIED PHYSICAL HARD STOP.   "
                       "Turning the crank further carries the platform back the other way.")
        else:
            caveat(ax, NOT_VERIFIED)
        name = "review_operation_%s.png" % fn
        save(fig, name)
        record(name, "operation frame: %s at crank %.0f deg" % (state, deg),
               [i for i in ALL7 if i != "BODY-REAR-PANEL"] + ["SCENARIO-PAYLOAD-1KG"],
               "crank %.0f deg (%s)" % (deg, state), None,
               cutaway="BODY-REAR-PANEL removed for review")


ASM = [
    ("01_empty_housing", ["BODY-HOUSING"], None, "Empty primary housing",
     "the +X side and the whole top are open"),
    ("02_crank_shaft_inserted", ["BODY-HOUSING", "BODY-CRANK-SHAFT"],
     ("BODY-CRANK-SHAFT", "-X"),
     "Crank shaft inserted from the open +X side",
     "the hub passes through journal land 2, the relief and journal land 1; "
     "the grip emerges outside the -X wall"),
    ("03_connecting_rod_and_crank_pin",
     ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD", "BODY-CRANK-JOINT-PIN"],
     ("BODY-CRANK-JOINT-PIN", "-X"),
     "Connecting rod lowered in, then the crank joint pin pushed in along -X",
     "the rod comes down through the open top into the 2 mm gap beside the crank arm"),
    ("04_platform_entering_guides",
     ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD", "BODY-CRANK-JOINT-PIN",
      "BODY-PLATFORM"], ("BODY-PLATFORM", "-Z"),
     "Platform lowered into BOTH guide channels",
     "the followers enter the channels from their open upper ends; the clevis comes "
     "down either side of the rod"),
    ("05_platform_joint_pin",
     ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD", "BODY-CRANK-JOINT-PIN",
      "BODY-PLATFORM", "BODY-PLATFORM-JOINT-PIN"], ("BODY-PLATFORM-JOINT-PIN", "-X"),
     "Platform joint pin pushed in along -X",
     "through clevis lug B, the rod's platform bore and clevis lug A"),
    ("06_open_side_cycle_check",
     ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD", "BODY-CRANK-JOINT-PIN",
      "BODY-PLATFORM", "BODY-PLATFORM-JOINT-PIN"], None,
     "Cycle check with the +X side still open",
     "the mechanism is complete and can be turned before it is closed up"),
    ("07_rear_panel_approach", ALL7, ("BODY-REAR-PANEL", "-X"),
     "Rear panel approaching along -X",
     "its two retention lands come up behind the two joint-pin heads"),
    ("08_rear_panel_installed", ALL7, None, "Rear panel installed",
     "the +X side is closed and both joint pins are captured"),
    ("09_completed_lift", ALL7, None, "Completed lift",
     "all seven product bodies in place"),
]
ASM_DEG = {"04_platform_entering_guides": 0.0, "06_open_side_cycle_check": 120.0}
OFFSET = {"BODY-CRANK-SHAFT": (105.0, 0.0, 0.0), "BODY-CRANK-JOINT-PIN": (78.0, 0.0, 0.0),
          "BODY-PLATFORM": (0.0, 0.0, 104.0), "BODY-PLATFORM-JOINT-PIN": (78.0, 0.0, 0.0),
          "BODY-REAR-PANEL": (74.0, 0.0, 0.0)}


def assembly_storyboard(bodies):
    print("-- assembly storyboard")
    c = CAMERAS["assembly_iso"]
    d0 = {b.id: b for b in bodies}
    for fn, present, moving, title, sub in ASM:
        deg = ASM_DEG.get(fn, 0.0)
        pats: List[Dict] = []
        for bid in present:
            sh = B.bodies_at(bodies, P, deg)
            sh = {b.id: b for b in sh}[bid].shape
            if moving and bid == moving[0]:
                sh = sh.moved(cv.translation(OFFSET[bid]))
            if bid in ("BODY-HOUSING", "BODY-REAR-PANEL"):
                cutsh = cut_half(sh, "y", "above", 74.0)
                if cutsh is not None:
                    pats += patches_of(cutsh, bid, 0.4)
                continue
            pats += patches_of(sh, bid, 0.4)
        fig = new_fig()
        ax = raster_axes(fig, [0.0, 0.0, 1.0, 1.0], pats, c)
        header(ax, "EXE-BM002-01   Assembly step %s  -  %s" % (fn.split("_")[0], title),
               sub + "\nhousing and rear panel cut at y = 74 FOR DISPLAY ONLY")
        banner(ax, "GEOMETRIC ASSEMBLY-SEQUENCE REPRESENTATION")
        triad_axes(ax, c)
        if moving:
            bid, d = moving
            bb = cv.bbox_of(d0[bid].shape)
            ctr = (bb["xmin"] + bb["dx"] / 2, bb["ymin"] + bb["dy"] / 2,
                   bb["zmin"] + bb["dz"] / 2)
            off = OFFSET[bid]
            start = (ctr[0] + off[0], ctr[1] + off[1], ctr[2] + off[2])
            end = (ctr[0] + off[0] * 0.18, ctr[1], ctr[2] + off[2] * 0.18)
            a = np.array(c.at(start)); b = np.array(c.at(end))
            cvd.arrow(ax, tuple(a), tuple(b - a), text="insert %s" % d,
                      color=NOTEC, lw=3.6, size=12.5)
        if fn.startswith("04"):
            leader(ax, c, (35.0, 129.0, 150.0),
                   "BACK guide channel\nthe follower enters from its open upper end",
                   (0.76, 0.66))
            note(ax, 0.045, 0.60,
                 "The FRONT guide channel is symmetric with the back one and\n"
                 "sits in the wall this display cutaway removes. Both channels\n"
                 "are shown together in SECTION C-C.", ec=ASMC, size=10.5)
        if fn.startswith("07"):
            leader(ax, c, (67.0, AY + 45.0, AZ),
                   "FEATURE-PANEL-CRANK-PIN-LAND\napproaching the crank pin head",
                   (0.76, 0.34))
            leader(ax, c, (67.0, AY, 150.0),
                   "FEATURE-PANEL-PLATFORM-PIN-LAND\napproaching the platform pin head",
                   (0.76, 0.52))
        if fn.startswith("06"):
            note(ax, 0.045, 0.12,
                 "the crank has been turned to 120 deg here:\n"
                 "the mechanism runs with the +X side still open",
                 ec=ASMC, size=11.0, va="bottom")
        swatches(ax, present)
        caveat(ax, "GEOMETRIC ASSEMBLY-SEQUENCE REPRESENTATION.   INSERTION FORCE NOT "
                   "VERIFIED.   No contact and no force is simulated.")
        name = "review_assembly_%s.png" % fn
        save(fig, name)
        record(name, "assembly step: %s" % title, present,
               "assembly step %s, crank %.0f deg" % (fn.split("_")[0], deg), None,
               cutaway="housing and rear panel cut at y = 74, display only")


# ==================================================================== main
def verify_signature() -> bool:
    """Sign a FRESHLY BUILT model, never one this process has rendered.

    cadval.bbox_of asks OCCT for a Bnd_Box, and Bnd_Box uses a shape's cached
    triangulation when the shape has one. Rendering leaves a 0.4 mm-deflection
    mesh on every face, after which the reported box is the MESH's extent - about
    0.013 mm larger per side here - and the signature moves even though the solid
    has not changed at all. Volume and centre of mass are unaffected, which is how
    you can tell the difference between this and a real geometry change.

    So the check rebuilds. That is also what the signature means: the result of
    reconstructing the model from parameters.yaml. The Phase A validator signs
    before it renders anything, so its recorded signature is unaffected.
    """
    prev = json.load(open(os.path.join(HERE, "geometry_signature.json")))
    sig = cv.geometry_signature(
        B.build(P), critical=prev["signature"]["critical_dimensions_mm"],
        motion=prev["signature"]["motion"],
        states=prev["signature"]["state_transforms"])
    ok = sig["signature_sha256"] == ACCEPTED_SIGNATURE
    if not ok:
        print("REFUSING TO RENDER: geometry signature is %s, expected %s"
              % (sig["signature_sha256"], ACCEPTED_SIGNATURE))
    return ok


def main() -> int:
    bodies = B.build(P)
    if not verify_signature():
        return 2
    print("geometry signature verified: %s" % ACCEPTED_SIGNATURE)
    os.makedirs(SHOTS, exist_ok=True)

    overall_views(bodies)
    body_identification(bodies)
    crank_interface(bodies)
    internal_views(bodies)
    print("-- orthographic sections")
    sections_overview(bodies)
    section_AA(bodies)
    section_BB(bodies)
    section_CC(bodies)
    section_DD(bodies)
    section_EE(bodies)
    section_FF(bodies)
    operation_storyboard(bodies)
    assembly_storyboard(bodies)

    if not verify_signature():
        return 2
    rec = {
        "step": 9, "name": "CAD-derived review media",
        "reference_id": "EXE-BM002-01",
        "source_geometry_signature_sha256": ACCEPTED_SIGNATURE,
        "signature_verified_before_and_after_render": True,
        "signature_check_method": (
            "the check REBUILDS the model from parameters.yaml and signs that. It "
            "must not sign a model this process has rendered: cadval.bbox_of asks "
            "OCCT for a Bnd_Box, Bnd_Box uses a shape's cached triangulation when it "
            "has one, and rendering leaves a 0.4 mm mesh on every face. The reported "
            "box then grows by about 0.013 mm per side and the signature moves while "
            "the solid is untouched. Volume and centre of mass stay bit-identical, "
            "which is how a reader tells this apart from a real geometry change. "
            "The Phase A validator signs before it renders, so its recorded "
            "signature is unaffected."),
        "geometry_source": ("the reference's own B-rep solids, posed by build.py - the "
                            "same functions the validator uses"),
        "renderer_3d": ("cadvideo.rasterise: a true z-buffer over per-face "
                        "tessellations. Triangles carry shading only; only a face's "
                        "own rim is stroked, depth-tested against the finished "
                        "buffer. No mesh diagonals, no hidden edges showing through."),
        "renderer_sections": ("cadval.section_polygons walked into filled, hatched "
                              "patches. Orthographic, cut faces only, nothing behind "
                              "the plane drawn."),
        "tessellation_deflection_mm": 0.4,
        "resolution_px": [W, H],
        "cameras": {k: v.as_dict() for k, v in CAMERAS.items()},
        "display_cutaways_note": ("A cutaway intersects a solid with a half-space FOR "
                                  "DISPLAY ONLY. The model is never modified, and the "
                                  "geometry signature is re-verified after the run."),
        "detail_panels_note": ("A 0.2 mm clearance on a 150 mm-wide drawing is about "
                               "one pixel. Every section with a fit to show carries an "
                               "enlarged detail panel of that fit."),
        "no_generative_imagery": True,
        "no_proxy_or_redrawn_geometry": True,
        "images": RENDERED,
        "count": len(RENDERED),
        "role": ("review aids for a human CAD reviewer. No geometric claim in this "
                 "reference rests on an image; every such claim is backed by a kernel "
                 "measurement in validation/."),
        "human_review": "HUMAN_REVIEW_PENDING",
        "status": "PASS" if RENDERED else "FAIL",
    }
    cv.write_json(os.path.join(OUT, "render_report.json"), rec)
    print("\n%d review images written to screenshots/" % len(RENDERED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
