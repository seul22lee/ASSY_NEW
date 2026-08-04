"""Review videos for EXE-BM001-02, from the final CAD.

Two clips, both evidence rather than illustration:

    cover_operation.mp4       closed -> release -> open -> close -> re-engage
    cover_snap_assembly.mp4   aligned -> tabs in -> past the lips -> recovered

Every frame is the reference's own two B-rep solids, posed and configured by
build.py - the same functions the validator calls. There is no proxy geometry,
no third body, and nothing from a superseded topology.

The assembly clip is a PRESCRIBED GEOMETRIC-STATE ANIMATION. It shows where the
compliant regions are declared to be at each moment; it is not FEA and it
computes no force. Every frame says so on its face.

    python make_videos.py
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))

import build as B          # noqa: E402
import cadval as cv        # noqa: E402
import cadvideo as vid     # noqa: E402
import cadquery as cq      # noqa: E402

P = B.load_params()
G = B.geom(P)
OUT = os.path.join(HERE, "validation", "simulation")
FPS = 30
W, H = 1280, 720
COLORS = {"BODY-ENCLOSURE": "#7f97ad", "BODY-COVER": "#d89b56"}

NOT_ESTABLISHED = [
    "snap insertion force, pull-out capacity or retention strength",
    "latch release effort or snap force",
    "material strain, root stress, creep, fatigue or repeated-cycle life",
    "wear, impact resistance or tolerance robustness",
    "moulding feasibility or cost",
    "that any motion shown occurs at any particular speed, or under any load",
]


def sig() -> str:
    return json.load(open(os.path.join(HERE, "geometry_signature.json"))) \
        ["signature"]["signature_sha256"]


def bodies_at(slide=0.0, lift=0.0, *, tabs=0.0, latch=0.0):
    """The two product bodies, placed and configured. Nothing else exists."""
    cover = B.build_cover(P, tabs_compressed=tabs, latch_released=latch)
    enc = cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                  B.build_enclosure(P))
    cb = cv.Body("BODY-COVER", "sliding cover", "GENERIC_COMPLIANT_POLYMER", cover)
    return [enc, cb.moved(cv.translation((-slide, 0.0, lift)))]


def clipped(bodies, x_max):
    """Section the scene so the rail channel can be seen into.

    Declared on every frame that uses it. A rail is a C-channel; from outside,
    the lip is exactly what hides the thing it retains, so a section is the only
    way to show the tab going under it.
    """
    keep = cq.Solid.makeBox(400, 300, 300, pnt=cq.Vector(-100, -100, -100))
    keep = keep.cut(cq.Solid.makeBox(400, 300, 300, pnt=cq.Vector(x_max, -100, -100)))
    return [cv.Body(b.id, b.name, b.material_class, b.shape.intersect(keep),
                    installed_as=b.installed_as, role=b.role, notes=b.notes)
            for b in bodies]


def smooth(s):
    """Minimum-jerk easing, so nothing in the clip starts or stops abruptly."""
    s = min(max(s, 0.0), 1.0)
    return 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5


# ============================================================ operating video
def operation_timeline():
    """(duration_s, label, banner colour, pose function of local fraction)."""
    hold, travel = P["latch_hold_travel"], P["travel"]

    def closed(_u):
        return dict(slide=0.0, tabs=0.0, latch=0.0)

    def press(u):
        return dict(slide=0.0, tabs=0.0, latch=smooth(u))

    def open_run(u):
        s = smooth(u) * travel
        return dict(slide=s, tabs=0.0, latch=1.0 if s <= hold else 0.0)

    def full_open(_u):
        return dict(slide=travel, tabs=0.0, latch=0.0)

    def close_run(u):
        s = (1.0 - smooth(u)) * travel
        lat = 1.0 if P["latch_free_play"] <= s <= hold else 0.0
        return dict(slide=s, tabs=0.0, latch=lat)

    def reengaged(_u):
        return dict(slide=0.0, tabs=0.0, latch=0.0)

    return [
        (1.1, "CLOSED - LATCH ENGAGED", "#8e44ad", closed),
        (1.3, "PRESS THE RELEASE PAD", "#b03a2e", press),
        (2.4, "SLIDE OPEN", "#b03a2e", open_run),
        (1.4, "FULL OPEN 84 mm - STILL CAPTIVE", "#1e8449", full_open),
        (2.4, "SLIDE CLOSED", "#b03a2e", close_run),
        (1.4, "SNAP RE-ENGAGED", "#8e44ad", reengaged),
    ]


MAIN_CAM = vid.Camera(eye=(-150.0, -250.0, 200.0), target=(95.0, 35.0, 42.0), scale=74.0)
# The latch works in the horizontal plane, so its inset looks straight down at it.
# A three-quarter inset shows the finger but hides the 2.6 mm sideways motion that
# is the whole point of the release.
DETAIL_CAM = vid.Camera(eye=(193.5, 7.0, 240.0), target=(193.5, 7.0, 42.0),
                        up=(0.0, 1.0, 0.0), scale=9.5)


def _seg_arrow(ax, a_model, b_model, text, color, toff=(0.0, 0.0), tha="center"):
    """Draw an arrow between two MODEL points, projected by the main camera."""
    ax0, ay0 = MAIN_CAM.at(a_model)
    bx0, by0 = MAIN_CAM.at(b_model)
    vid.arrow(ax, (ax0, ay0), (bx0 - ax0, by0 - ay0), text, color=color,
              toff=toff, tha=tha)


def _annotate_operation(ax, seg, pose, t):
    """Arrows anchored to real model points, so they follow the geometry."""
    top = G["cover_top"]
    if seg == 1:
        # the release is a sideways push on the pad, out at the end wall
        _seg_arrow(ax, (198.0, -22.0, top + 3.0), (198.0, 2.0, top + 3.0),
                   "PRESS", "#b03a2e", toff=(-14.0, -6.0))
    elif seg == 2:
        _seg_arrow(ax, (150.0, 35.0, top + 26.0), (96.0, 35.0, top + 26.0),
                   "SLIDE OPEN", "#b03a2e", toff=(0.0, 7.0))
    elif seg == 3:
        _seg_arrow(ax, (103.0, 35.0, top + 24.0), (187.0, 35.0, top + 24.0),
                   "FULL OPEN 84 mm - CAPTIVE", "#1e8449", toff=(0.0, 7.0))
    elif seg == 4:
        _seg_arrow(ax, (96.0, 35.0, top + 26.0), (150.0, 35.0, top + 26.0),
                   "SLIDE CLOSED", "#b03a2e", toff=(0.0, 7.0))
    elif seg == 5:
        _seg_arrow(ax, (198.0, 2.0, top + 3.0), (198.0, -22.0, top + 3.0),
                   "SNAP RE-ENGAGED", "#8e44ad", toff=(-28.0, -6.0))


def render_operation():
    segs = operation_timeline()
    total = sum(s[0] for s in segs)
    n = int(round(total * FPS))
    frames, samples, timeline = [], [], []
    acc = 0.0
    for dur, label, col, _fn in segs:
        timeline.append({"state": label, "t_start_s": round(acc, 3),
                         "t_end_s": round(acc + dur, 3)})
        acc += dur

    for k in range(n + 1):
        t = k / float(FPS)
        u, seg = t, 0
        for i, (dur, _l, _c, _f) in enumerate(segs):
            if u <= dur or i == len(segs) - 1:
                seg = i
                break
            u -= dur
        dur, label, col, fn = segs[seg]
        pose = fn(min(u / dur, 1.0))
        samples.append([t, pose["slide"], pose["latch"], pose["tabs"]])

        bods = bodies_at(slide=pose["slide"], latch=pose["latch"])
        img, ext = vid.rasterise(vid.body_patches(bods), MAIN_CAM, COLORS, W, H)
        det, _dext = vid.rasterise(vid.body_patches(bods), DETAIL_CAM, COLORS, 380, 300)
        fig, ax = vid.new_canvas(img, ext, W, H)

        # detail inset: a second FIXED camera on the latch, declared in the manifest
        ax2 = fig.add_axes([0.773, 0.575, 0.213, 0.290])
        ax2.imshow(det, origin="upper", interpolation="none")
        ax2.set_xticks([]); ax2.set_yticks([])
        for s in ax2.spines.values():
            s.set_edgecolor("#3a3f45"); s.set_linewidth(1.4)
        ax2.set_title("LATCH DETAIL  (fixed inset camera)", fontsize=9.5,
                      color="#1b1f24", pad=3)

        vid.state_banner(ax, label, color=col)
        vid.title_block(ax, [
            "EXE-BM001-02   snap-rail captive cover",
            "BODY-ENCLOSURE (blue) + BODY-COVER (tan)",
            "two bodies - no fastener anywhere",
            "",
            "t              %5.2f s" % t,
            "slide          %5.1f mm  of %.0f mm" % (pose["slide"], P["travel"]),
            "latch finger   %5.2f mm inboard  (declared max %.1f)"
            % (pose["latch"] * P["latch_shift"], P["latch_shift"]),
            "tabs           under both rail lips at every position",
        ], size=10.0)
        _annotate_operation(ax, seg, pose, t)
        vid.caveat(ax, "Geometric and kinematic states from the validated CAD. "
                       "No force, strain, effort or life is computed or claimed.")
        frames.append(vid.frame_rgb(fig))
        import matplotlib.pyplot as plt
        plt.close(fig)

    path = os.path.join(OUT, "cover_operation.mp4")
    vid.write_mp4(frames, path, FPS)
    man = vid.manifest(
        video_id="VID-BM001-02-OPERATION", reference_id="EXE-BM001-02", path=path,
        here=HERE, geometry_signature=sig(), fps=FPS, width=W, height=H,
        frame_count=len(frames), camera=MAIN_CAM, timeline=timeline,
        traj_hash=vid.trajectory_hash(samples),
        assumptions={
            "kinematics": "prescribed, minimum-jerk easing between declared states",
            "speed": ("arbitrary and carries no meaning. The clip is paced for "
                      "review, not derived from any dynamics."),
            "compliance": ("the latch finger is shown as a rigid translation of "
                           "REG-COVER-LATCH-COMPLIANT, a "
                           "DECLARED_KINEMATIC_APPROXIMATION that conserves volume "
                           "exactly and models no strain"),
            "friction": "none modelled anywhere",
        },
        establishes=[
            "the closed state, the release, the full 84 mm travel and the return "
            "are reachable by the declared geometry",
            "the latch tooth is behind the keeper when closed and clear of it when "
            "the release pad is pushed - the release is causally connected",
            "the cover stays under both rail lips at every frame, full open included",
            "only two bodies exist at any point in the clip",
        ],
        does_not_establish=NOT_ESTABLISHED,
        extra={"detail_inset_camera": DETAIL_CAM.as_dict(),
               "sample_columns": ["t_s", "slide_mm", "latch_fraction", "tab_fraction"]})
    return path, man, frames


# ============================================================ assembly video
# Nearly end-on to the section plane, so both rails and the cover between them
# read as a cross-section rather than as a corner.
ASM_CAM = vid.Camera(eye=(272.0, 6.0, 84.0), target=(118.0, 35.0, 46.0), scale=40.0)
ASM_CLIP_X = 118.0


def assembly_timeline():
    lift0 = 26.0

    def aligned(u):
        return dict(lift=lift0, tabs=smooth(u))

    def descend(u):
        return dict(lift=lift0 * (1.0 - smooth(u)), tabs=1.0)

    def recover(u):
        return dict(lift=0.0, tabs=1.0 - smooth(u))

    def captive(_u):
        return dict(lift=0.0, tabs=0.0)

    return [
        (1.4, "ASSEMBLY ALIGNED", "#2c3e50", lambda u: dict(lift=lift0, tabs=0.0)),
        (1.6, "INTEGRAL TABS COMPRESSED", "#7d3c98", aligned),
        (2.6, "TABS PASS RAIL LIPS", "#b03a2e", descend),
        (1.6, "TABS RECOVERED UNDER LIPS", "#1e8449", recover),
        (1.8, "CAPTIVE ASSEMBLY", "#1e8449", captive),
    ]


def render_assembly():
    segs = assembly_timeline()
    total = sum(s[0] for s in segs)
    n = int(round(total * FPS))
    frames, samples, timeline = [], [], []
    acc = 0.0
    for dur, label, col, _fn in segs:
        timeline.append({"state": label, "t_start_s": round(acc, 3),
                         "t_end_s": round(acc + dur, 3)})
        acc += dur

    lip_gap = G["lip_far_y0"] - G["lip_near_y1"]
    for k in range(n + 1):
        t = k / float(FPS)
        u, seg = t, 0
        for i, (dur, _l, _c, _f) in enumerate(segs):
            if u <= dur or i == len(segs) - 1:
                seg = i
                break
            u -= dur
        dur, label, col, fn = segs[seg]
        pose = fn(min(u / dur, 1.0))
        samples.append([t, pose["lift"], pose["tabs"]])

        bods = clipped(bodies_at(lift=pose["lift"], tabs=pose["tabs"]), ASM_CLIP_X)
        img, ext = vid.rasterise(vid.body_patches(bods), ASM_CAM, COLORS, W, H)
        fig, ax = vid.new_canvas(img, ext, W, H)

        span = 63.6 - 2.0 * pose["tabs"] * P["tab_deflection"]
        vid.state_banner(ax, label, color=col)
        vid.title_block(ax, [
            "EXE-BM001-02   snap-in assembly",
            "BODY-ENCLOSURE + BODY-COVER only",
            "sectioned at X = %.0f mm to see" % ASM_CLIP_X,
            "into the rail channels",
            "",
            "t                 %5.2f s" % t,
            "height above seat %5.1f mm" % pose["lift"],
            "tab deflection    %5.2f mm each side  (declared %.1f)"
            % (pose["tabs"] * P["tab_deflection"], P["tab_deflection"]),
            "cover span        %5.1f mm" % span,
            "lip gap           %5.1f mm" % lip_gap,
            "relation          %s"
            % ("inside the gap - free to pass" if span < lip_gap
               else "wider than the gap - held by the lips"),
        ], size=10.0)
        vid.title_block(ax, [
            "GEOMETRIC COMPLIANT-STATE REPRESENTATION",
            "FORCE / STRAIN NOT VERIFIED",
        ], x=0.986, y=0.985, size=12.0, ha="right", weight="bold", color="#7d3c98")
        z = P["box_z"] + pose["lift"] + P["cover_t"] / 2.0

        def am(a, b, text, color, toff=(0.0, 0.0)):
            ax0, ay0 = ASM_CAM.at(a)
            bx0, by0 = ASM_CAM.at(b)
            vid.arrow(ax, (ax0, ay0), (bx0 - ax0, by0 - ay0), text, color=color,
                      toff=toff, lw=3.0, size=12)

        if seg == 1:
            am((110.0, -4.0, z), (110.0, 6.0, z), None, "#7d3c98")
            am((110.0, 74.0, z), (110.0, 64.0, z), "TABS DEFLECT IN", "#7d3c98",
               toff=(0.0, 6.0))
        elif seg == 2:
            am((110.0, 35.0, P["box_z"] + pose["lift"] + 26.0),
               (110.0, 35.0, P["box_z"] + pose["lift"] + 8.0), "PRESS DOWN",
               "#b03a2e", toff=(14.0, 6.0))
        elif seg == 3:
            am((110.0, 8.0, z), (110.0, 1.0, z), None, "#1e8449")
            am((110.0, 62.0, z), (110.0, 69.0, z), "EARS SPRING OUT UNDER THE LIPS",
               "#1e8449", toff=(0.0, 7.0))
        elif seg == 4:
            am((110.0, 35.0, G["cover_top"] + 2.0),
               (110.0, 35.0, G["cover_top"] + 16.0), "CANNOT LIFT OUT", "#1e8449",
               toff=(20.0, 0.0))
        vid.caveat(ax, "A prescribed geometric-state animation of a declared "
                       "compliant region, not a deformation simulation. Volume is "
                       "conserved exactly; no strain is modelled and none is claimed.")
        frames.append(vid.frame_rgb(fig))
        import matplotlib.pyplot as plt
        plt.close(fig)

    path = os.path.join(OUT, "cover_snap_assembly.mp4")
    vid.write_mp4(frames, path, FPS)
    man = vid.manifest(
        video_id="VID-BM001-02-ASSEMBLY", reference_id="EXE-BM001-02", path=path,
        here=HERE, geometry_signature=sig(), fps=FPS, width=W, height=H,
        frame_count=len(frames), camera=ASM_CAM, timeline=timeline,
        traj_hash=vid.trajectory_hash(samples),
        assumptions={
            "kind": ("PRESCRIBED GEOMETRIC-STATE ANIMATION. Each frame is a "
                     "declared configuration of REG-COVER-RETAIN-LEFT/RIGHT-"
                     "COMPLIANT, produced as a rigid translation of the tab "
                     "region. It is not FEA."),
            "volume": "conserved to 0.000 mm^3 across every configuration shown",
            "section": ("the scene is cut at X = %.0f mm so the rail channels are "
                        "visible. The lip is what hides the thing it retains, so "
                        "there is no un-sectioned view that shows this." % ASM_CLIP_X),
            "speed": "arbitrary; paced for review and derived from no dynamics",
        },
        establishes=[
            "the compressed cover span fits between the actual rail lip inner "
            "edges, so a straight downward press is geometrically possible",
            "the ears finish underneath the lips, which is what makes the cover captive",
            "the whole sequence uses two bodies and no fastener",
        ],
        does_not_establish=NOT_ESTABLISHED + [
            "that the tabs survive the deflection, or the force needed to hold them in",
        ],
        extra={"section_plane_x_mm": ASM_CLIP_X,
               "sample_columns": ["t_s", "lift_mm", "tab_fraction"]})
    return path, man, frames


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for name, fn in (("operation", render_operation), ("assembly", render_assembly)):
        path, man, frames = fn()
        out[name] = man
        print("%-10s %s  %d frames  %.2fs  %.1f MB"
              % (name, os.path.basename(path), man["frame_count"],
                 man["duration_s"], man["output_bytes"] / 1e6))
        # a representative frame from each declared state, for the visual gate
        import imageio
        for tl in man["state_timeline"]:
            k = min(int((tl["t_start_s"] + tl["t_end_s"]) / 2.0 * FPS), len(frames) - 1)
            slug = tl["state"].lower().replace(" ", "_").replace("-", "").replace(",", "")
            slug = "".join(c for c in slug if c.isalnum() or c == "_")
            imageio.imwrite(os.path.join(OUT, "frame_%s_%s.png" % (name, slug)),
                            frames[k])
        imageio.imwrite(os.path.join(OUT, "frame_%s_first.png" % name), frames[0])
        imageio.imwrite(os.path.join(OUT, "frame_%s_last.png" % name), frames[-1])
    cv.write_json(os.path.join(OUT, "cover_videos.json"),
                  {"reference_id": "EXE-BM001-02",
                   "geometry_signature_sha256": sig(),
                   "videos": out,
                   "human_review": "HUMAN_REVIEW_PENDING"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
