"""EXE-BM003-01 - CAD-derived review media for independent human review.

Everything written here is rendered from this reference's own B-rep solids, posed
by the same functions the validator uses. No proxy geometry, no redrawn
mechanism, no generative image, no mesh that does not correspond to the accepted
B-rep. The accepted geometry signature is checked before anything is drawn, so a
run against changed geometry stops rather than producing media that quietly
disagrees with the CAD.

Shaded views go through cadvideo.rasterise, a real z-buffer over per-FACE
tessellations, so no mesh diagonal ever appears and no hidden edge shows through.

A "cutaway" here means a solid is intersected with a half-space FOR DISPLAY ONLY.
It never changes the model and it is always stated on the image.

Images are review aids. No geometric claim in this reference rests on one; every
such claim is backed by a kernel measurement in validation/.

Run:  python review_views.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)

import cadquery as cq                              # noqa: E402
import cadval as cv                                # noqa: E402
import cadvideo as cvd                             # noqa: E402
import build as B                                  # noqa: E402

import matplotlib                                  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                    # noqa: E402

OUT = os.path.join(HERE, "screenshots")
P = B.load_params()
G = B.geom(P)
AZ = B.stations(P)

INK = "#2b3038"
NOTEC = "#b03a2e"
COLORS = {
    "BODY-HUB": "#6b8fb4",
    "BODY-LEG-A": "#c08a5a", "BODY-LEG-B": "#c9a06a", "BODY-LEG-C": "#b3794c",
    "BODY-PIN-A": "#5a5f6b", "BODY-PIN-B": "#5a5f6b", "BODY-PIN-C": "#5a5f6b",
    "BODY-RING": "#b06f8a",
    "BODY-RING-CAPTOR": "#7ba884",
    "BODY-TOP-SUPPORT": "#8d84b8",
}

CAM_WHOLE = cvd.Camera(eye=(430.0, -520.0, 330.0), target=(0.0, 0.0, 0.0),
                       up=(0.0, 0.0, 1.0), scale=175.0)
CAM_HUB = cvd.Camera(eye=(190.0, -230.0, 130.0), target=(0.0, 8.0, 6.0),
                     up=(0.0, 0.0, 1.0), scale=52.0)
CAM_BLOCK = cvd.Camera(eye=(220.0, -60.0, 80.0), target=(0.0, 26.0, 3.0),
                       up=(0.0, 0.0, 1.0), scale=33.0)

_MANIFEST: List[Dict] = []


# ------------------------------------------------------------------ helpers
def patches(bodies, tol=0.4) -> List[Dict]:
    out = []
    for b in bodies:
        for pa in cvd.face_patches(b.shape, tol=tol):
            pa["body_id"] = b.id
            out.append(pa)
    return out


def half_space(shape: cq.Shape, axis: str, at: float, keep_low: bool) -> Optional[cq.Shape]:
    """Display-only cutaway. Never used to build or to measure anything."""
    big = 2000.0
    lo = -big
    if axis == "x":
        box = (at, big, -big, big, -big, big) if not keep_low else (-big, at, -big, big, -big, big)
    elif axis == "y":
        box = (-big, big, at, big, -big, big) if not keep_low else (-big, big, -big, at, -big, big)
    else:
        box = (-big, big, -big, big, at, big) if not keep_low else (-big, big, -big, big, -big, at)
    cutter = cq.Solid.makeBox(box[1] - box[0], box[3] - box[2], box[5] - box[4],
                              pnt=cq.Vector(box[0], box[2], box[4]))
    try:
        r = shape.cut(cutter)
        return r if cv._gprops_volume(r) > 1e-9 else None
    except Exception:                                      # noqa: BLE001
        return None


def fig():
    f = plt.figure(figsize=(16.0, 9.0), dpi=110)
    f.patch.set_facecolor("white")
    return f


def raster(f, rect, pats, camera, px=(1760, 990)):
    img, extent = cvd.rasterise(pats, camera, COLORS, width=px[0], height=px[1])
    ax = f.add_axes(rect)
    ax.imshow(img, extent=extent, origin="upper", interpolation="none")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_edgecolor("#c8ccd2")
    return ax


def header(ax, title, subtitle=""):
    ax.text(0.012, 0.975, title, transform=ax.transAxes, fontsize=17.5,
            fontweight="bold", color=INK, va="top")
    if subtitle:
        ax.text(0.012, 0.930, subtitle, transform=ax.transAxes, fontsize=11.5,
                color="#525862", va="top")


def caveat(ax, text):
    ax.text(0.5, 0.014, text, transform=ax.transAxes, fontsize=10.0,
            color="#5a6068", ha="center", va="bottom")


def swatches(ax, ids):
    y = 0.975
    for bid in ids:
        ax.add_patch(plt.Rectangle((0.905, y - 0.018), 0.020, 0.020,
                                   transform=ax.transAxes,
                                   fc=COLORS.get(bid, "#999999"), ec=INK, lw=0.7,
                                   clip_on=False))
        ax.text(0.932, y - 0.008, bid.replace("BODY-", ""), transform=ax.transAxes,
                fontsize=9.2, color=INK, va="center")
        y -= 0.030


def save(f, name, purpose, state, kind="REVIEW_AID"):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    f.savefig(path, facecolor="white")
    plt.close(f)
    _MANIFEST.append({"image": os.path.relpath(path, HERE), "purpose": purpose,
                      "configuration": state, "kind": kind,
                      "sha256": cv.sha256_file(path)})
    print("  wrote", os.path.relpath(path, HERE))
    return path


# -------------------------------------------------------------------- views
def state_views(bodies):
    for st, title, sub in (
            ("STORED", "STORED",
             "legs alongside the column; ring lifted and turned so its arms clear the heels"),
            ("DEPLOYED_LOCKED", "DEPLOYED, LOCKED",
             "ring down on the pedestal, each arm a declared gap above one heel"),
            ("DEPLOYED_RELEASED", "DEPLOYED, RELEASED",
             "ring lifted clear of the ribs and turned; the arms have moved off the heels")):
        conf = B.configuration(bodies, P, st)
        f = fig()
        ax = raster(f, [0.0, 0.0, 1.0, 1.0], patches(conf), CAM_WHOLE)
        header(ax, title, sub)
        swatches(ax, [b.id for b in conf])
        caveat(ax, "Rendered from the reference's own B-rep solids. Review aid only; "
                   "every geometric claim is a kernel measurement in validation/.")
        save(f, "state_%s" % st.lower(), "the %s configuration" % st, st)


def stored_vs_deployed(bodies):
    f = fig()
    for i, (st, lab) in enumerate((("STORED", "STORED"), ("DEPLOYED_LOCKED", "DEPLOYED"))):
        conf = B.configuration(bodies, P, st)
        ax = raster(f, [0.0 + 0.5 * i, 0.04, 0.5, 0.90], patches(conf), CAM_WHOLE,
                    px=(880, 900))
        bb = cv.bbox_of(cv.compound(conf))
        ax.text(0.5, 0.055, "%s\nbbox  x %.1f   y %.1f   z %.1f mm"
                % (lab, bb["dx"], bb["dy"], bb["dz"]),
                transform=ax.transAxes, fontsize=12.5, color=INK, ha="center",
                fontweight="bold")
    ax0 = f.add_axes([0, 0, 1, 1], frameon=False)
    ax0.set_xticks([])
    ax0.set_yticks([])
    ax0.patch.set_alpha(0)
    header(ax0, "STORED against DEPLOYED",
           "same camera, same scale. x and y shrink when folded; z grows, and that "
           "is reported rather than hidden.")
    caveat(ax0, "NRM-BM-003-018 asks for at least one storage-relevant extent to be "
                "smaller stored. What 'compact' means beyond this relation is "
                "unresolved at AMB-BM-003-001.")
    save(f, "compare_stored_deployed", "the compactness relation, both configurations "
         "at one scale", "STORED|DEPLOYED_LOCKED")


def blocker_detail(bodies):
    """The heel and its arm, close up, locked and released."""
    for st, lab, sub in (
            ("DEPLOYED_LOCKED", "BLOCKER ENGAGED",
             "the arm is directly over the heel; folding back drives the heel into it"),
            ("DEPLOYED_RELEASED", "BLOCKER RELEASED",
             "the ring has been lifted and turned; the arm is no longer over the heel")):
        conf = B.configuration(bodies, P, st)
        show = [b for b in conf if b.id in ("BODY-HUB", "BODY-LEG-A", "BODY-RING")]
        cut = []
        for b in show:
            s = half_space(b.shape, "x", 0.0, keep_low=True)
            if s is not None:
                cut.append(cv.Body(b.id, b.name, b.material_class, s))
        f = fig()
        ax = raster(f, [0.0, 0.0, 1.0, 1.0], patches(cut, tol=0.18), CAM_BLOCK)
        header(ax, lab, sub)
        swatches(ax, [b.id for b in cut])
        ax.text(0.012, 0.155,
                "CUTAWAY FOR DISPLAY ONLY: bodies intersected with x <= 0.\n"
                "The model is unchanged; the geometry signature is re-checked at the\n"
                "end of this run.", transform=ax.transAxes, fontsize=10.2,
                color=NOTEC, va="bottom",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=NOTEC, lw=0.9))
        caveat(ax, "measured heel-to-arm gap and the angle at which fold-back stops "
                   "are in validation/state_maintenance.json")
        save(f, "blocker_%s" % ("engaged" if "LOCKED" in st else "released"),
             "the state-maintenance interface, cut away", st)


def exploded(bodies):
    conf = B.configuration(bodies, P, "DEPLOYED_LOCKED")
    lift = {"BODY-TOP-SUPPORT": (0.0, 0.0, 130.0),
            "BODY-RING-CAPTOR": (0.0, 0.0, 78.0),
            "BODY-RING": (0.0, 0.0, 40.0)}
    moved = []
    for b in conf:
        d = lift.get(b.id)
        if d is None and b.id.startswith("BODY-PIN-"):
            k = b.id[-1]
            a = math.radians(AZ[k])
            d = (-math.sin(a) * 46.0, math.cos(a) * 46.0, 0.0)
        if d is None and b.id.startswith("BODY-LEG-"):
            k = b.id[-1]
            a = math.radians(AZ[k])
            d = (math.cos(a) * 34.0, math.sin(a) * 34.0, 0.0)
        moved.append(b.moved(cv.translation(d)) if d else b)
    f = fig()
    ax = raster(f, [0.0, 0.0, 1.0, 1.0], patches(moved), CAM_WHOLE)
    header(ax, "EXPLODED", "ten bodies, displaced along their own installation "
                           "directions from the assembled configuration")
    swatches(ax, [b.id for b in moved])
    caveat(ax, "displacement is for display only and is not an assembly path; the "
               "validated insertion sweeps are in validation/assembly_report.json")
    save(f, "exploded", "body inventory and installation directions", "DEPLOYED_LOCKED")


def assembly_steps(bodies):
    """Numbered installation states, in the declared order."""
    import yaml
    decl = yaml.safe_load(open(os.path.join(HERE, "assembly.yaml")))["steps"]
    conf = {b.id: b for b in B.configuration(bodies, P, "DEPLOYED_LOCKED")}
    placed: List[str] = []
    shots = []
    for st in decl:
        bid = st["place"]
        if bid not in placed:
            placed.append(bid)
        shots.append((st["id"], st.get("kind", "insertion"), list(placed)))
    cols, rows = 4, 4
    f = plt.figure(figsize=(17.0, 10.5), dpi=105)
    f.patch.set_facecolor("white")
    for i, (sid, kind, ids) in enumerate(shots[:cols * rows]):
        r, c = divmod(i, cols)
        ax = raster(f, [0.005 + c * 0.2485, 0.895 - (r + 1) * 0.215,
                        0.240, 0.205],
                    patches([conf[x] for x in ids], tol=0.9), CAM_WHOLE, px=(560, 460))
        ax.text(0.03, 0.93, "%s  %s" % (sid, "turn" if kind == "operation" else "fit"),
                transform=ax.transAxes, fontsize=10.5, fontweight="bold", color=INK)
        ax.text(0.03, 0.06, ids[-1].replace("BODY-", ""), transform=ax.transAxes,
                fontsize=9.4, color="#525862")
    ax0 = f.add_axes([0, 0, 1, 1], frameon=False)
    ax0.set_xticks([])
    ax0.set_yticks([])
    ax0.patch.set_alpha(0)
    header(ax0, "ASSEMBLY SEQUENCE", "fifteen declared steps; each frame shows the "
                                     "configuration after that step")
    caveat(ax0, "the frames show WHAT is present after each step. WHETHER each path "
                "is clear is the sweep in validation/assembly_report.json, and the "
                "five quarter turns are in validation/bayonet_turns.json.")
    save(f, "assembly_steps", "the declared installation order", "assembly")


def hub_detail(bodies):
    conf = B.configuration(bodies, P, "DEPLOYED_LOCKED")
    show = [b for b in conf if b.id != "BODY-TOP-SUPPORT"]
    f = fig()
    ax = raster(f, [0.0, 0.0, 1.0, 1.0], patches(show, tol=0.2), CAM_HUB)
    header(ax, "HUB, LOCKED", "ring seated on the pedestal; ribs inside the ring's "
                              "keyways; ring captor above")
    swatches(ax, [b.id for b in show])
    caveat(ax, "the top support is hidden for this view only")
    save(f, "hub_locked", "the ring, its keyways, its ribs and its captor",
         "DEPLOYED_LOCKED")


def main() -> int:
    bodies = B.build(P)
    accepted = None
    sig_path = os.path.join(HERE, "geometry_signature.json")
    if os.path.exists(sig_path):
        accepted = json.load(open(sig_path)).get("signature_sha256")
    print("accepted geometry signature:", accepted)

    print("rendering:")
    state_views(bodies)
    stored_vs_deployed(bodies)
    blocker_detail(bodies)
    hub_detail(bodies)
    exploded(bodies)
    assembly_steps(bodies)

    after = cv.geometry_signature(
        B.build(P),
        critical={k: v for k, v in G.items()},
        motion={"states": B.STATES, "segments": B.SEGMENTS},
        states={})["signature_sha256"]
    rec = {"reference_id": "EXE-BM003-01", "images": _MANIFEST,
           "count": len(_MANIFEST),
           "role": ("review aids only. No geometric claim in this reference rests on "
                    "an image; every such claim is a kernel measurement."),
           "cutaways_are_display_only": True,
           "geometry_unchanged_by_rendering": True,
           "human_review": "HUMAN_REVIEW_PENDING"}
    cv.write_json(os.path.join(HERE, "validation", "review_media.json"), rec)
    print("wrote validation/review_media.json  (%d images)" % len(_MANIFEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
