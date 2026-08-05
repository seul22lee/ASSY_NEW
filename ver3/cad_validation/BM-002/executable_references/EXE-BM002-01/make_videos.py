"""EXE-BM002-01 - CAD-state videos for human review.

Two clips, both drawn frame by frame from the reference's own B-rep solids and
posed by the same functions the validator uses:

  lift_cad_operation   one complete 0-360 degree crank revolution
  lift_cad_assembly    the nine-step assembly sequence

Both are PRESCRIBED CAD KINEMATIC ANIMATIONS. Every body position in every frame
comes from build.py's pose law or from an assembly offset declared in
assembly.yaml. Nothing here integrates an equation of motion, resolves a contact,
applies a force or computes a strain, and the overlay says so in every frame. No
MuJoCo is involved.

Each clip writes a manifest recording engine and versions, the source geometry
signature, fps, resolution, frame count, duration, the fixed camera definitions,
the state timeline, a trajectory hash over the exact pose samples the frames were
drawn from, and the output file's own SHA-256.

Run:  python make_videos.py [operation|assembly]
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import cadval as cv          # noqa: E402
import cadvideo as cvd       # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B            # noqa: E402
import review_views as RV    # noqa: E402

import cadquery as cq        # noqa: E402
import matplotlib            # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

HERE = RV.HERE
OUTDIR = os.path.join(HERE, "validation", "review")
P, G = RV.P, RV.G
AY, AZ = RV.AY, RV.AZ

FPS = 30
WV, HV = 1280, 720
TOL = 0.55                      # tessellation deflection for video frames, mm

# Main camera: an opened-front isometric. It is the only view in which the
# EXTERIOR handle and the INTERIOR linkage are both visible at once, which is what
# a reviewer needs in order to see that turning the handle is what moves the
# platform. Fixed for the whole clip.
CAM_MAIN = cvd.Camera(eye=(-380.0, -320.0, 250.0), target=(14.0, 74.0, 124.0),
                      up=(0.0, 0.0, 1.0), scale=150.0)
# Fixed inset: the crank/link motion plane face-on, rear panel removed.
CAM_INSET = cvd.Camera(eye=(760.0, 70.0, 128.0), target=(40.0, 70.0, 128.0),
                       up=(0.0, 0.0, 1.0), scale=146.0)
CAM_ASM = cvd.Camera(eye=(-350.0, -330.0, 285.0), target=(20.0, 76.0, 112.0),
                     up=(0.0, 0.0, 1.0), scale=158.0)

NOT_DYN = ("CAD KINEMATIC ANIMATION - NOT DYNAMICS.   "
           "STRUCTURAL STRENGTH / USER EFFORT / JAMMING NOT VERIFIED.")


# ------------------------------------------------------------------ helpers
def state_name(deg: float) -> str:
    d = deg % 360.0
    if d < 1e-9 or abs(d - 360.0) < 1e-9:
        return "BOTTOM"
    if abs(d - 180.0) < 1e-9:
        return "TOP"
    return "RISING" if d < 180.0 else "LOWERING"


def raster(patches, camera, w, h, bg="#eef1f4"):
    return cvd.rasterise(patches, camera, RV.COLORS, width=w, height=h, bg=bg,
                         edge_px=1.0)


def compose(main_img, main_ext, inset_img, inset_ext):
    fig = plt.figure(figsize=(WV / 100.0, HV / 100.0), dpi=100)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.imshow(main_img, extent=main_ext, origin="upper", interpolation="none",
              zorder=1)
    ax.set_xlim(main_ext[0], main_ext[1])
    ax.set_ylim(main_ext[2], main_ext[3])
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_visible(False)
    axi = None
    if inset_img is not None:
        axi = fig.add_axes([0.735, 0.055, 0.25, 0.60])
        axi.imshow(inset_img, extent=inset_ext, origin="upper",
                   interpolation="none", zorder=1)
        axi.set_xlim(inset_ext[0], inset_ext[1])
        axi.set_ylim(inset_ext[2], inset_ext[3])
        axi.set_xticks([]); axi.set_yticks([]); axi.set_aspect("equal")
        for s in axi.spines.values():
            s.set_color("#3a3f45"); s.set_linewidth(1.4)
        axi.set_title("FIXED CUTAWAY INSET\nmotion plane face-on, rear panel removed",
                      fontsize=8.6, weight="bold", color="#3a3f45", pad=3)
    return fig, ax, axi


def to_rgb(fig) -> np.ndarray:
    out = cvd.frame_rgb(fig)
    plt.close(fig)
    return out


# ================================================================ operation
def operation(bodies) -> Dict:
    n = 300                                  # 10.0 s at 30 fps
    frames: List[np.ndarray] = []
    samples: List[List[float]] = []
    timeline: List[Dict] = []
    seen = set()
    t0 = time.time()
    for i in range(n):
        deg = 360.0 * i / float(n)
        st = RV.state_of(bodies, deg)
        sz, ra, pz = st["support_z"], st["rod_angle"], st["plat_pin_z"]
        cyc, czc = st["crank_pin"]
        nm = state_name(deg)
        samples.append([i / float(FPS), deg, sz, ra, pz, cyc, czc])
        if nm not in seen:
            seen.add(nm)
            timeline.append({"t_s": round(i / float(FPS), 3), "frame": i,
                             "state": nm, "crank_angle_deg": round(deg, 3),
                             "support_surface_z_mm": round(sz, 4)})

        main = RV.scene(bodies, deg, cut=("y", "above", 74.0),
                        cut_only=("BODY-HOUSING", "BODY-REAR-PANEL"),
                        payload=True, tol=TOL)
        mimg, mext = raster(main, CAM_MAIN, WV, HV)
        ins = RV.scene(bodies, deg, drop=("BODY-REAR-PANEL",), payload=True, tol=TOL)
        iimg, iext = raster(ins, CAM_INSET, 320, 460, bg="#ffffff")
        fig, ax, axi = compose(mimg, mext, iimg, iext)

        cvd.title_block(ax, [
            "EXE-BM002-01   enclosed hand-cranked platform lift",
            "one complete crank revolution, 0 to 360 degrees",
            "housing and rear panel cut at y = 74 FOR DISPLAY ONLY",
        ], x=0.012, y=0.985, size=11.0, weight="bold")
        cvd.state_banner(ax, "%s    crank %5.1f deg" % (nm, deg), x=0.78, y=0.995)
        ax.text(0.012, 0.30,
                "time                  %5.2f s\n"
                "crank angle          %6.1f deg\n"
                "support-surface z    %6.1f mm\n"
                "connecting-rod angle %6.2f deg\n"
                "state                %s\n"
                "payload scenario      1.0 kg" % (i / float(FPS), deg, sz, ra, nm),
                transform=ax.transAxes, fontsize=11.5, va="top", ha="left",
                family="DejaVu Sans Mono", zorder=22,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#1f4e9c", lw=1.2))
        # travel bar: where the platform is inside its 90 mm stroke
        frac = (sz - 126.0) / 90.0
        ax.add_patch(matplotlib.patches.Rectangle(
            (0.022, 0.36), 0.026, 0.30, transform=ax.transAxes, fc="white",
            ec="#3a3f45", lw=1.1, zorder=21))
        ax.add_patch(matplotlib.patches.Rectangle(
            (0.022, 0.36), 0.026, 0.30 * frac, transform=ax.transAxes,
            fc="#6fa77f", ec="none", zorder=22))
        ax.text(0.056, 0.665, "216 TOP", transform=ax.transAxes, fontsize=8.6,
                va="center", zorder=23)
        ax.text(0.056, 0.36, "126 BOTTOM", transform=ax.transAxes, fontsize=8.6,
                va="center", zorder=23)
        ax.text(0.056, 0.512, "90 mm\ntravel", transform=ax.transAxes, fontsize=8.6,
                va="center", zorder=23)
        if nm in ("TOP", "BOTTOM"):
            ax.text(0.5, 0.085, "KINEMATIC EXTREMUM - NOT A VERIFIED PHYSICAL HARD STOP",
                    transform=ax.transAxes, fontsize=11.5, color="white",
                    ha="center", va="center", weight="bold", zorder=24,
                    bbox=dict(boxstyle="round,pad=0.35", fc="#b03a2e", ec="none"))
        cvd.caveat(ax, NOT_DYN, y=0.014)
        frames.append(to_rgb(fig))
        if i % 30 == 0:
            print("   operation frame %3d/%d  (%.0fs)" % (i, n, time.time() - t0))

    path = os.path.join(OUTDIR, "lift_cad_operation.mp4")
    cvd.write_mp4(frames, path, fps=FPS)
    gif = os.path.join(OUTDIR, "lift_cad_operation.gif")
    cvd.write_gif(frames, gif, fps=15, every=2, scale=0.5)
    timeline.append({"t_s": round((n - 1) / float(FPS), 3), "frame": n - 1,
                     "state": "BOTTOM RETURN",
                     "crank_angle_deg": round(360.0 * (n - 1) / n, 3),
                     "support_surface_z_mm": round(
                         RV.state_of(bodies, 360.0 * (n - 1) / n)["support_z"], 4)})
    rec = cvd.manifest(
        video_id="lift_cad_operation", reference_id="EXE-BM002-01", path=path,
        here=HERE, geometry_signature=RV.ACCEPTED_SIGNATURE, fps=FPS,
        width=WV, height=HV, frame_count=len(frames), camera=CAM_MAIN,
        timeline=timeline, traj_hash=cvd.trajectory_hash(samples),
        assumptions={
            "kind": "PRESCRIBED CAD KINEMATIC ANIMATION",
            "not_a_dynamics_simulation": True,
            "not_a_contact_simulation": True,
            "engine_is_not_mujoco": True,
            "pose_law": ("build.py pose_at(): the crank shaft and crank joint pin "
                         "rotate about the shaft axis; the connecting rod rotates "
                         "about the crank-pin axis by asin(R sin theta / L) and "
                         "translates onto the crank pin; the platform and platform "
                         "joint pin translate vertically."),
            "payload": ("SCENARIO-PAYLOAD-1KG is a declared envelope, not a product "
                        "body. It is drawn moving rigidly with the platform for "
                        "visualisation. It has no mass distribution, no stiffness "
                        "and no friction here."),
            "display_cutaway": ("housing and rear panel intersected with y <= 74 for "
                                "display; the model is unchanged"),
            "inset_camera": CAM_INSET.as_dict(),
        },
        establishes=[
            "the declared bodies pass through a complete 0-360 degree crank cycle",
            "the external handle rotates and the platform rises and then lowers in response",
            "the connecting rod changes orientation through the cycle, reaching 31.97 degrees",
            "the platform support surface moves between z = 126.0 and z = 216.0",
            "no body is drawn passing through another at any sampled frame",
        ],
        does_not_establish=[
            "any force, torque, pressure, stress, strain or deflection",
            "that a human can turn the crank, or with what effort",
            "that the mechanism does not jam - jamming is contact-level and NOT_VERIFIED",
            "that the platform holds position when the crank is released",
            "that the platform carries 1 kg - capacity is UNSUPPORTED",
            "safety, manufacturability, wear or life",
        ],
        extra={"gif": os.path.relpath(gif, HERE),
               "gif_sha256": cv.sha256_file(gif),
               "sequence": "BOTTOM -> RISING -> TOP -> LOWERING -> BOTTOM RETURN"})
    cv.write_json(os.path.join(OUTDIR, "lift_cad_operation_video.json"), rec)
    print("   wrote %s (%d frames, %.1f s)" % (path, len(frames), len(frames) / FPS))
    return rec


# ================================================================= assembly
# (label, seconds, moving body, axis, from_offset, to_offset, crank angle)
ASM_TIMELINE = [
    ("empty housing", 0.9, None, None, 0.0, 0.0, 0.0),
    ("crank shaft inserted -X", 1.7, "BODY-CRANK-SHAFT", "x", 118.0, 0.0, 0.0),
    ("connecting rod lowered -Z", 1.4, "BODY-CONNECTING-ROD", "z", 128.0, 0.0, 0.0),
    ("crank joint pin inserted -X", 1.2, "BODY-CRANK-JOINT-PIN", "x", 86.0, 0.0, 0.0),
    ("platform lowered into both guides -Z", 1.5, "BODY-PLATFORM", "z", 112.0, 0.0, 0.0),
    ("platform joint pin inserted -X", 1.2, "BODY-PLATFORM-JOINT-PIN", "x", 86.0, 0.0, 0.0),
    ("open-side cycle check", 1.8, "CRANK", None, 0.0, 200.0, 0.0),
    ("rear panel installed -X", 1.6, "BODY-REAR-PANEL", "x", 86.0, 0.0, 200.0),
    ("completed lift", 1.2, None, None, 0.0, 0.0, 200.0),
]
PRESENT = {
    0: ["BODY-HOUSING"],
    1: ["BODY-HOUSING", "BODY-CRANK-SHAFT"],
    2: ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD"],
    3: ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD",
        "BODY-CRANK-JOINT-PIN"],
    4: ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD",
        "BODY-CRANK-JOINT-PIN", "BODY-PLATFORM"],
    5: ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD",
        "BODY-CRANK-JOINT-PIN", "BODY-PLATFORM", "BODY-PLATFORM-JOINT-PIN"],
    6: ["BODY-HOUSING", "BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD",
        "BODY-CRANK-JOINT-PIN", "BODY-PLATFORM", "BODY-PLATFORM-JOINT-PIN"],
    7: RV.ALL7,
    8: RV.ALL7,
}
STEP_NOTE = {
    0: "the +X side and the whole top are open",
    1: "the hub passes through journal land 2, the relief and journal land 1;\n"
       "the grip emerges outside the -X wall",
    2: "down through the open top into the 2 mm gap beside the crank arm",
    3: "through the rod's crank bore into the crank arm bore; the head seats on the rod",
    4: "both followers enter their channels; the clevis comes down either side of the rod",
    5: "through clevis lug B, the rod's platform bore and clevis lug A",
    6: "the mechanism is complete and runs with the +X side still open",
    7: "the panel closes the side AND brings both retention lands up behind the pin heads",
    8: "all seven product bodies in place",
}


def assembly(bodies) -> Dict:
    d0 = {b.id: b for b in bodies}
    plan: List[Tuple] = []
    for k, (lab, secs, mover, axis, o0, o1, deg) in enumerate(ASM_TIMELINE):
        nf = int(round(secs * FPS))
        for j in range(nf):
            u = j / float(max(nf - 1, 1))
            plan.append((k, lab, mover, axis, o0 + (o1 - o0) * u, deg, u))
    frames: List[np.ndarray] = []
    samples: List[List[float]] = []
    timeline: List[Dict] = []
    last = None
    t0 = time.time()
    for i, (k, lab, mover, axis, off, deg, u) in enumerate(plan):
        crank = off if mover == "CRANK" else deg
        pats: List[Dict] = []
        posed = {b.id: b for b in B.bodies_at(bodies, P, crank)}
        for bid in PRESENT[k]:
            sh = posed[bid].shape
            if mover == bid and axis:
                v = {"x": (off, 0.0, 0.0), "z": (0.0, 0.0, off)}[axis]
                sh = sh.moved(cv.translation(v))
            if bid in ("BODY-HOUSING", "BODY-REAR-PANEL"):
                c = RV.cut_half(sh, "y", "above", 74.0)
                if c is None:
                    continue
                pats += RV.patches_of(c, bid, TOL)
                continue
            pats += RV.patches_of(sh, bid, TOL)
        img, ext = raster(pats, CAM_ASM, WV, HV)
        fig, ax, _ = compose(img, ext, None, None)
        cvd.title_block(ax, [
            "EXE-BM002-01   assembly sequence, step %d of 9" % (k + 1),
            lab,
            STEP_NOTE[k],
        ], x=0.012, y=0.985, size=11.0, weight="bold")
        cvd.state_banner(ax, "GEOMETRIC ASSEMBLY SEQUENCE", x=0.80, y=0.995,
                         color="#1f4e9c")
        ax.text(0.012, 0.30,
                "time            %5.2f s\n"
                "step            %d of 9\n"
                "bodies placed   %d of 7\n"
                "crank angle    %6.1f deg" % (i / float(FPS), k + 1,
                                              len(PRESENT[k]), crank),
                transform=ax.transAxes, fontsize=11.5, va="top", ha="left",
                family="DejaVu Sans Mono", zorder=22,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#1f4e9c", lw=1.2))
        if mover and mover != "CRANK" and off > 1e-6:
            bb = cv.bbox_of(d0[mover].shape)
            ctr = np.array([bb["xmin"] + bb["dx"] / 2, bb["ymin"] + bb["dy"] / 2,
                            bb["zmin"] + bb["dz"] / 2])
            v = np.array({"x": (1.0, 0, 0), "z": (0, 0, 1.0)}[axis])
            a = np.array(CAM_ASM.at(tuple(ctr + v * off)))
            b = np.array(CAM_ASM.at(tuple(ctr + v * off * 0.25)))
            cvd.arrow(ax, tuple(a), tuple(b - a), text="insert -%s" % axis.upper(),
                      color="#b03a2e", lw=3.4, size=12)
        ax.text(0.985, 0.30,
                "ASSEMBLY FORCE AND MANUFACTURING\nPROCESS NOT VERIFIED.\n"
                "No contact and no force is simulated.\n"
                "This is a prescribed sequence of CAD\nstates, not an insertion study.",
                transform=ax.transAxes, fontsize=10.5, va="top", ha="right",
                zorder=22,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#b03a2e", lw=1.2))
        cvd.caveat(ax, "GEOMETRIC ASSEMBLY SEQUENCE - NOT A CONTACT-FORCE SIMULATION.  "
                       "ASSEMBLY FORCE AND MANUFACTURING PROCESS NOT VERIFIED.", y=0.014)
        frames.append(to_rgb(fig))
        samples.append([i / float(FPS), float(k), off, crank])
        if lab != last:
            timeline.append({"t_s": round(i / float(FPS), 3), "frame": i,
                             "step": k + 1, "state": lab,
                             "bodies_placed": len(PRESENT[k])})
            last = lab
        if i % 30 == 0:
            print("   assembly frame %3d/%d  (%.0fs)" % (i, len(plan), time.time() - t0))

    path = os.path.join(OUTDIR, "lift_cad_assembly.mp4")
    cvd.write_mp4(frames, path, fps=FPS)
    rec = cvd.manifest(
        video_id="lift_cad_assembly", reference_id="EXE-BM002-01", path=path,
        here=HERE, geometry_signature=RV.ACCEPTED_SIGNATURE, fps=FPS,
        width=WV, height=HV, frame_count=len(frames), camera=CAM_ASM,
        timeline=timeline, traj_hash=cvd.trajectory_hash(samples),
        assumptions={
            "kind": "GEOMETRIC ASSEMBLY SEQUENCE",
            "not_a_contact_or_force_simulation": True,
            "engine_is_not_mujoco": True,
            "motion_law": ("each body translates along the straight-line insertion "
                           "direction declared for it in assembly.yaml. The offsets "
                           "are display approach distances; the SEATED positions are "
                           "the as-built ones the validator swept in step 7."),
            "display_cutaway": ("housing and rear panel intersected with y <= 74 for "
                                "display; the model is unchanged"),
        },
        establishes=[
            "an ordering exists in which each body reaches its seated position",
            "the crank shaft enters from the open +X side and its grip emerges outside",
            "the connecting rod and the platform enter vertically through the open top",
            "both followers enter the two guide channels before the panel is installed",
            "both joint pins are installed before the rear panel closes the +X side",
            "the rear panel's two retention lands arrive behind the two pin heads in "
            "the same motion that seats the panel",
        ],
        does_not_establish=[
            "insertion force, ease of assembly, tooling or fixturing",
            "manufacturability of any body",
            "that the sequence is the only possible one",
            "any contact, friction or deformation - none is modelled",
        ],
        extra={"steps": 9, "note": "step 7 turns the crank with the +X side open"})
    cv.write_json(os.path.join(OUTDIR, "lift_cad_assembly_video.json"), rec)
    print("   wrote %s (%d frames, %.1f s)" % (path, len(frames), len(frames) / FPS))
    return rec


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    bodies = B.build(P)
    if not RV.verify_signature():
        return 2
    print("geometry signature verified: %s" % RV.ACCEPTED_SIGNATURE)
    os.makedirs(OUTDIR, exist_ok=True)
    if which in ("operation", "both"):
        operation(bodies)
    if which in ("assembly", "both"):
        assembly(bodies)
    return 0


if __name__ == "__main__":
    sys.exit(main())
