"""EXE-BM003-01 - CAD-state animations for human review.

Two clips, both drawn frame by frame from this reference's own B-rep solids and
posed by the same functions the validator uses:

  bm003_cad_cycle      the complete operational cycle: unfold, lock, release, fold
  bm003_cad_assembly   the fifteen-step assembly sequence

Both are PRESCRIBED CAD KINEMATIC ANIMATIONS. Every body position in every frame
comes from build.py's pose law or from an assembly offset declared in
assembly.yaml. Nothing here integrates an equation of motion, resolves a contact,
applies a force or computes a strain, and the overlay says so in every frame.
There is no MuJoCo in this reference and no dynamics of any kind.

Each clip writes a manifest recording engine and versions, fps, resolution, frame
count, duration, the fixed camera, the state timeline, a trajectory hash over the
exact pose samples the frames were drawn from, and the output's own SHA-256.

Run:  python make_videos.py [cycle|assembly]
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List, Sequence, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)

import cadval as cv                                # noqa: E402
import cadvideo as cvd                             # noqa: E402
import build as B                                  # noqa: E402
import review_views as RV                          # noqa: E402

import yaml                                        # noqa: E402
import matplotlib                                  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                    # noqa: E402

OUTDIR = os.path.join(HERE, "validation", "review")
P, G = RV.P, RV.G
FPS = 24
WV, HV = 1280, 720
TOL = 0.7

CAM = cvd.Camera(eye=(430.0, -520.0, 330.0), target=(0.0, 0.0, -10.0),
                 up=(0.0, 0.0, 1.0), scale=185.0)

CAVEAT = ("PRESCRIBED CAD KINEMATIC ANIMATION - poses come from the declared "
          "transforms. No dynamics, no contact resolution, no force.")


def _sig() -> str:
    import json
    p = os.path.join(HERE, "geometry_signature.json")
    return json.load(open(p))["signature_sha256"] if os.path.exists(p) else "UNKNOWN"


def _frame(bodies, title: str, sub: str, banner: str = "") -> np.ndarray:
    pats = []
    for b in bodies:
        for pa in cvd.face_patches(b.shape, tol=TOL):
            pa["body_id"] = b.id
            pats.append(pa)
    img, extent = cvd.rasterise(pats, CAM, RV.COLORS, width=WV, height=HV)
    fig = plt.figure(figsize=(WV / 100.0, HV / 100.0), dpi=100)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=extent, origin="upper", interpolation="none")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_xticks([])
    ax.set_yticks([])
    cvd.title_block(ax, [title, sub])
    if banner:
        cvd.state_banner(ax, banner)
    cvd.caveat(ax, CAVEAT)
    out = cvd.frame_rgb(fig)
    plt.close(fig)
    return out


def clip_cycle(bodies) -> Dict:
    kf = B._keyframes(P, G)
    plan = [(seg, 34) for seg in B.SEGMENTS]
    frames, samples, timeline = [], [], []
    labels = {
        "M1_UNFOLD": ("M1  UNFOLD", "swing each leg out by hand"),
        "M2_RING_TURN_TO_LOCK": ("M2  TURN THE RING BACK", "keyways line up with the ribs"),
        "M3_RING_LOWER_TO_LOCK": ("M3  LOWER THE RING", "arms come down over the heels"),
        "M4_RING_LIFT_TO_RELEASE": ("M4  LIFT THE RING", "first half of the deliberate release"),
        "M5_RING_TURN_TO_RELEASE": ("M5  TURN THE RING", "second half; arms move off the heels"),
        "M6_FOLD": ("M6  FOLD", "the legs are free only now"),
    }
    for seg, n in plan:
        a, b = (kf[s] for s in B.SEGMENT_ENDS[seg])
        timeline.append({"segment": seg, "first_frame": len(frames), "frames": n + 1})
        for i in range(n + 1):
            t = i / float(n)
            vals = [a[j] + (b[j] - a[j]) * t for j in range(3)]
            samples.append(list(vals))
            conf = B.bodies_at(bodies, P, *vals)
            ttl, sub = labels[seg]
            locked = seg in ("M3_RING_LOWER_TO_LOCK",) and t > 0.98
            frames.append(_frame(conf, ttl, sub,
                                 "LOCKED" if locked else ""))
    path = os.path.join(OUTDIR, "bm003_cad_cycle.mp4")
    os.makedirs(OUTDIR, exist_ok=True)
    cvd.write_mp4(frames, path, fps=FPS)
    return cvd.manifest(
        video_id="bm003_cad_cycle", reference_id="EXE-BM003-01", path=path, here=HERE,
        geometry_signature=_sig(), fps=FPS, width=WV, height=HV,
        frame_count=len(frames), camera=CAM, timeline=timeline,
        traj_hash=cvd.trajectory_hash(samples),
        assumptions={"kind": "PRESCRIBED_CAD_KINEMATIC_ANIMATION",
                     "poses": "the declared transforms in build.py; nothing is integrated",
                     "dynamics": "none - DYNAMICS_NOT_REQUIRED_FOR_THIS_REFERENCE"},
        establishes=["the declared cycle is STORED -> deploy -> lock -> release -> fold -> STORED",
                     "M4 and M5 together are the deliberate release",
                     "what a reviewer sees corresponds to the accepted B-rep"],
        does_not_establish=["any force, torque, speed or dynamic behaviour",
                            "non-interference - that is the kernel measurement in "
                            "validation/motion_report.json, not this animation"])


def clip_assembly(bodies) -> Dict:
    decl = yaml.safe_load(open(os.path.join(HERE, "assembly.yaml")))["steps"]
    conf = {b.id: b for b in B.configuration(bodies, P, "DEPLOYED_LOCKED")}
    frames, samples, timeline = [], [], []
    placed: List[str] = []
    for st in decl:
        bid, kind = st["place"], st.get("kind", "insertion")
        n = 6 if kind in ("base", "operation") else 20
        timeline.append({"step": st["id"], "body": bid, "kind": kind,
                         "first_frame": len(frames), "frames": n + 1})
        direc = st.get("direction", [0.0, 0.0, 0.0])
        dist = float(st.get("approach_distance", 0.0))
        for i in range(n + 1):
            s = dist * (1.0 - i / float(n))
            samples.append([s] + list(direc))
            shown = [conf[x] for x in placed if x != bid]
            body = conf[bid].moved(cv.translation(
                (-direc[0] * s, -direc[1] * s, -direc[2] * s)))
            frames.append(_frame(shown + [body],
                                 "%s  %s" % (st["id"], bid.replace("BODY-", "")),
                                 "quarter turn" if kind == "operation" else
                                 ("fixed reference body" if kind == "base"
                                  else "straight-line insertion"),
                                 "BAYONET TURN" if kind == "operation" else ""))
        if bid not in placed:
            placed.append(bid)
    path = os.path.join(OUTDIR, "bm003_cad_assembly.mp4")
    os.makedirs(OUTDIR, exist_ok=True)
    cvd.write_mp4(frames, path, fps=FPS)
    return cvd.manifest(
        video_id="bm003_cad_assembly", reference_id="EXE-BM003-01", path=path, here=HERE,
        geometry_signature=_sig(), fps=FPS, width=WV, height=HV,
        frame_count=len(frames), camera=CAM, timeline=timeline,
        traj_hash=cvd.trajectory_hash(samples),
        assumptions={"kind": "PRESCRIBED_CAD_KINEMATIC_ANIMATION",
                     "paths": "the straight-line offsets declared in assembly.yaml",
                     "dynamics": "none"},
        establishes=["the declared installation order and each body's approach direction"],
        does_not_establish=["that any path is clear - that is the sweep in "
                            "validation/assembly_report.json",
                            "insertion force, ease of assembly or process suitability",
                            "the five bayonet turns, which are held frames here and are "
                            "swept in validation/bayonet_turns.json"])


def main(which: str = "all") -> int:
    bodies = B.build(P)
    os.makedirs(OUTDIR, exist_ok=True)
    made = []
    if which in ("all", "cycle"):
        made.append(clip_cycle(bodies))
    if which in ("all", "assembly"):
        made.append(clip_assembly(bodies))
    cv.write_json(os.path.join(HERE, "validation", "videos.json"),
                  {"reference_id": "EXE-BM003-01", "clips": made,
                   "count": len(made),
                   "role": ("review aids. No geometric claim in this reference rests "
                            "on a video."),
                   "dynamics": "DYNAMICS_NOT_REQUIRED_FOR_THIS_REFERENCE",
                   "human_review": "HUMAN_REVIEW_PENDING"})
    for m in made:
        print("wrote", m["file"], "%d frames" % m["frame_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
