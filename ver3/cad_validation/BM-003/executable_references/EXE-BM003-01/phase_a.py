#!/usr/bin/env python3
"""EXE-BM003-01 Phase A — metric assembly and kinematic proxy.

Phase A exists so that the mechanism is proved to WORK before any effort goes
into solid geometry. Every body is a set of capsules and every clearance is an
analytic segment-to-segment distance, so the whole cycle runs in a second and a
mistake costs a rerun rather than a rebuild.

The proxy is conservative: a capsule bulges where a real prism does not, so a
clearance reported here is a lower bound on the B-rep clearance. That direction
is the safe one - Phase A can reject a design Phase B would have accepted, and
cannot accept one Phase B would reject.

WHAT IT IS NOT
  Not tolerance analysis, not contact mechanics, not a stress or lifetime model.
  Every clearance is NOMINAL and measured on nominal geometry.

Fixture principle (commissioned, not chosen by this file): three hinged legs on a
central hub, held deployed by a captive annular ring whose three arms block the
leg heels from rising. Release is a deliberate lift-and-rotate. Declared
state-maintenance class: KINEMATIC_BLOCK.
"""

import hashlib
import json
import math
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "phase_a")
REFERENCE_ID = "EXE-BM003-01"
ROUND = 6


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

def load_params(path=None):
    with open(path or os.path.join(HERE, "parameters.yaml"), encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return {k: v["value"] for k, v in doc["parameters"].items()}


# ---------------------------------------------------------------------------
# Vector helpers - plain tuples, no numpy, so results are bit-stable
# ---------------------------------------------------------------------------

def add(a, b):   return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b):   return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s):   return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b):   return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def norm(a):     return math.sqrt(dot(a, a))


def rot_z(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def seg_seg_distance(p0, p1, q0, q1):
    """Closest distance between two segments. Clamped parametric solution."""
    d1, d2 = sub(p1, p0), sub(q1, q0)
    r = sub(p0, q0)
    a, e, f = dot(d1, d1), dot(d2, d2), dot(d2, r)
    EPS = 1e-12
    if a <= EPS and e <= EPS:
        return norm(r)
    if a <= EPS:
        s, t = 0.0, max(0.0, min(1.0, f / e))
    else:
        c = dot(d1, r)
        if e <= EPS:
            t, s = 0.0, max(0.0, min(1.0, -c / a))
        else:
            b = dot(d1, d2)
            denom = a * e - b * b
            s = max(0.0, min(1.0, (b * f - c * e) / denom)) if denom > EPS else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, max(0.0, min(1.0, -c / a))
            elif t > 1.0:
                t, s = 1.0, max(0.0, min(1.0, (b - c) / a))
    c1 = add(p0, mul(d1, s))
    c2 = add(q0, mul(d2, t))
    return norm(sub(c1, c2))


# A capsule is a swept SPHERE, so its ends bulge. That is harmless for a rod and
# badly wrong for a flat disc: two coaxial discs 18 mm apart on the same axis,
# each of radius 15, read as overlapping by 11.5 mm. Z-aligned cylinders
# therefore get their own exact treatment.

def point_zcyl_distance(p, cyl):
    """Exact distance from a point to a finite Z-aligned cylinder. Negative inside."""
    z0, z1 = min(cyl["a"][2], cyl["b"][2]), max(cyl["a"][2], cyl["b"][2])
    cx, cy = cyl["a"][0], cyl["a"][1]
    d_rad = math.hypot(p[0] - cx, p[1] - cy) - cyl["r"]
    d_ax = max(z0 - p[2], p[2] - z1)
    if d_rad <= 0.0 and d_ax <= 0.0:
        return max(d_rad, d_ax)                      # inside: least-negative
    return math.hypot(max(d_rad, 0.0), max(d_ax, 0.0))


def zcyl_zcyl_gap(a, b):
    """Exact for two coaxial or parallel Z-aligned cylinders."""
    az0, az1 = min(a["a"][2], a["b"][2]), max(a["a"][2], a["b"][2])
    bz0, bz1 = min(b["a"][2], b["b"][2]), max(b["a"][2], b["b"][2])
    axial = max(bz0 - az1, az0 - bz1)
    radial = math.hypot(a["a"][0] - b["a"][0], a["a"][1] - b["a"][1]) - a["r"] - b["r"]
    return max(axial, radial)          # separated if EITHER axis is clear


_SEG_SAMPLES = 48


def cap_zcyl_gap(cap, cyl):
    """Segment sampled against an exact cylinder field, minus the capsule radius."""
    a, b = cap["a"], cap["b"]
    best = float("inf")
    for k in range(_SEG_SAMPLES + 1):
        u = k / float(_SEG_SAMPLES)
        p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u,
             a[2] + (b[2] - a[2]) * u)
        d = point_zcyl_distance(p, cyl)
        if d < best:
            best = d
    return best - cap["r"]


def capsule_gap(ca, cb):
    """Surface-to-surface gap. Negative means interpenetration."""
    ka, kb = ca.get("kind", "cap"), cb.get("kind", "cap")
    if ka == "zcyl" and kb == "zcyl":
        return zcyl_zcyl_gap(ca, cb)
    if ka == "zcyl":
        return cap_zcyl_gap(cb, ca)
    if kb == "zcyl":
        return cap_zcyl_gap(ca, cb)
    return seg_seg_distance(ca["a"], ca["b"], cb["a"], cb["b"]) - ca["r"] - cb["r"]


# ---------------------------------------------------------------------------
# Body construction
# ---------------------------------------------------------------------------

BODY_IDS = [
    "BODY-HUB",
    "BODY-LEG-A", "BODY-LEG-B", "BODY-LEG-C",
    "BODY-PIN-A", "BODY-PIN-B", "BODY-PIN-C",
    "BODY-CLIP-A", "BODY-CLIP-B", "BODY-CLIP-C",
    "BODY-RING", "BODY-RINGCAPTOR", "BODY-CAPTORPIN",
    "BODY-TOPPLATE", "BODY-TOPPIN",
]
LEG_KEYS = ["A", "B", "C"]


def station_frame(P, i):
    """Radial and tangential unit vectors, and the hinge point, for station i."""
    phi = P["station_angles"][i]
    rhat = (math.cos(math.radians(phi)), math.sin(math.radians(phi)), 0.0)
    that = (-math.sin(math.radians(phi)), math.cos(math.radians(phi)), 0.0)
    hinge = add(mul(rhat, P["hinge_r"]), (0.0, 0.0, P["hinge_z"]))
    return phi, rhat, that, hinge


def hub_primitives(P, mutation=None):
    prims = [
        {"kind": "zcyl", "tag": "hub_column", "a": (0, 0, P["shoulder_top_z"]),
         "b": (0, 0, P["col_top_z"]), "r": P["col_r"]},
        {"kind": "zcyl", "tag": "hub_spigot", "a": (0, 0, P["col_top_z"]),
         "b": (0, 0, P["spigot_top_z"]), "r": P["spigot_r"]},
        {"kind": "zcyl", "tag": "hub_shoulder", "a": (0, 0, P["shoulder_bot_z"]),
         "b": (0, 0, P["shoulder_top_z"]), "r": P["shoulder_r"]},
    ]
    for i in range(int(P["station_count"])):
        _phi, rhat, _that, _h = station_frame(P, i)
        prims.append({"tag": "hub_boss",
                      "a": add(mul(rhat, P["col_r"]), (0, 0, P["hinge_z"])),
                      "b": add(mul(rhat, P["boss_r_outer"]), (0, 0, P["hinge_z"])),
                      "r": P["boss_half_h"]})
    return prims


def leg_primitives(P, i, theta_deg, mutation=None):
    """Leg shaft plus the blocker heel, at leg angle theta (deg from -Z)."""
    _phi, rhat, _that, hinge = station_frame(P, i)
    th = math.radians(theta_deg)
    d_leg = add(mul((0, 0, 1.0), -math.cos(th)), mul(rhat, math.sin(th)))
    beta = math.radians(P["heel_beta"])
    d_heel = add(mul((0, 0, 1.0), math.cos(th + beta)), mul(rhat, math.sin(th + beta)))
    heel_len = P["heel_len"]
    if mutation == "SHORT_HEEL":
        heel_len = 6.0
    return [
        {"tag": "leg_shaft", "a": hinge, "b": add(hinge, mul(d_leg, P["leg_len"])),
         "r": P["leg_r"]},
        {"tag": "leg_heel", "a": hinge, "b": add(hinge, mul(d_heel, heel_len)),
         "r": P["heel_r"]},
    ]


def pin_primitives(P, i):
    _phi, _rhat, that, hinge = station_frame(P, i)
    half = P["hinge_pin_len"] / 2.0
    return [{"tag": "pin", "a": sub(hinge, mul(that, half)),
             "b": add(hinge, mul(that, half)), "r": P["hinge_pin_r"]}]


def clip_primitives(P, i):
    _phi, _rhat, that, hinge = station_frame(P, i)
    off = P["hinge_pin_len"] / 2.0 - P["clip_t"]
    return [{"tag": "clip", "a": add(hinge, mul(that, off)),
             "b": add(hinge, mul(that, off + P["clip_t"])), "r": P["clip_r"]}]


def ring_primitives(P, z_bot, rot_deg, mutation=None):
    """Annular hub plus three radial blocking arms.

    The arms are the blockers. Their BOTTOM face is what the heel cannot rise
    past, so the arm is modelled as a capsule whose axis lies at the arm's
    mid-height and whose radius is half the ring height.
    """
    z_mid = z_bot + P["ring_h"] / 2.0
    hr = P["ring_h"] / 2.0
    prims = [{"kind": "zcyl", "tag": "ring_hub", "a": (0, 0, z_bot),
              "b": (0, 0, z_bot + P["ring_h"]), "r": P["ring_hub_or"]}]
    n_arms = int(P["station_count"])
    if mutation == "TWO_ARMS":
        n_arms = 2
    for i in range(n_arms):
        phi = P["station_angles"][i] + rot_deg
        rh = (math.cos(math.radians(phi)), math.sin(math.radians(phi)), 0.0)
        r_out = P["ring_arm_r_out"]
        if mutation == "SHORT_ARM" and i == 0:
            r_out = P["ring_arm_r_in"] + 4.0
        prims.append({"tag": "ring_arm",
                      "a": add(mul(rh, P["ring_arm_r_in"]), (0, 0, z_mid)),
                      "b": add(mul(rh, r_out), (0, 0, z_mid)),
                      "r": hr, "arm_index": i})
    return prims


def captor_primitives(P, present=True):
    if not present:
        return []
    return [{"kind": "zcyl", "tag": "captor", "a": (0, 0, P["captor_z_bot"]),
             "b": (0, 0, P["captor_z_bot"] + P["captor_h"]), "r": P["captor_r"]}]


def captor_pin_primitives(P):
    half = P["captor_pin_len"] / 2.0
    z = P["captor_z_bot"] + P["captor_h"] / 2.0
    return [{"tag": "captor_pin", "a": (-half, 0, z), "b": (half, 0, z),
             "r": P["captor_pin_r"]}]


def topplate_primitives(P):
    return [{"kind": "zcyl", "tag": "topplate", "a": (0, 0, P["col_top_z"]),
             "b": (0, 0, P["col_top_z"] + P["plate_t"]), "r": P["plate_r"]}]


def toppin_primitives(P):
    half = P["top_pin_len"] / 2.0
    z = P["col_top_z"] + P["plate_t"] / 2.0
    return [{"tag": "top_pin", "a": (-half, 0, z), "b": (half, 0, z),
             "r": P["top_pin_r"]}]


def build_state(P, legs_theta, ring_z, ring_rot, *, present=None, mutation=None):
    """All bodies as {body_id: [primitives]} for one configuration."""
    present = present or set(BODY_IDS)
    out = {}
    if "BODY-HUB" in present:
        out["BODY-HUB"] = hub_primitives(P, mutation)
    for i, k in enumerate(LEG_KEYS):
        if "BODY-LEG-%s" % k in present:
            m = mutation if (mutation == "SHORT_HEEL" and k == "A") else None
            out["BODY-LEG-%s" % k] = leg_primitives(P, i, legs_theta[i], m)
        if "BODY-PIN-%s" % k in present:
            out["BODY-PIN-%s" % k] = pin_primitives(P, i)
        if "BODY-CLIP-%s" % k in present:
            out["BODY-CLIP-%s" % k] = clip_primitives(P, i)
    if "BODY-RING" in present:
        out["BODY-RING"] = ring_primitives(P, ring_z, ring_rot, mutation)
    if "BODY-RINGCAPTOR" in present:
        out["BODY-RINGCAPTOR"] = captor_primitives(P)
    if "BODY-CAPTORPIN" in present:
        out["BODY-CAPTORPIN"] = captor_pin_primitives(P)
    if "BODY-TOPPLATE" in present:
        out["BODY-TOPPLATE"] = topplate_primitives(P)
    if "BODY-TOPPIN" in present:
        out["BODY-TOPPIN"] = toppin_primitives(P)
    return out


# ---------------------------------------------------------------------------
# Interaction policy
#
# A designed sliding or joint fit is NOT a collision. Excluding those pairs is
# what makes the remaining overlap check meaningful: without it every bearing
# reads as interference and the real leg-leg case drowns.
# ---------------------------------------------------------------------------

DECLARED_FIT_TAGS = {
    frozenset({"ring_hub", "hub_column"}),      # ring slides on the column
    frozenset({"ring_hub", "hub_shoulder"}),    # ring seats on the shoulder (lower stop)
    frozenset({"ring_hub", "captor"}),          # ring meets its upper travel stop
    frozenset({"captor", "hub_column"}),
    frozenset({"captor", "captor_pin"}),
    frozenset({"captor_pin", "hub_column"}),
    frozenset({"topplate", "hub_spigot"}),
    frozenset({"topplate", "hub_column"}),
    frozenset({"topplate", "top_pin"}),
    frozenset({"top_pin", "hub_spigot"}),
    frozenset({"pin", "hub_boss"}),             # hinge pin in its clevis
    frozenset({"pin", "leg_shaft"}),            # hinge pin through the leg eye
    frozenset({"pin", "leg_heel"}),
    frozenset({"clip", "pin"}),
    frozenset({"clip", "hub_boss"}),
    frozenset({"leg_shaft", "hub_boss"}),       # leg root in the clevis
    frozenset({"leg_heel", "hub_boss"}),
    frozenset({"leg_shaft", "leg_heel"}),       # same body, shared root
}


def pair_is_declared_fit(ta, tb):
    return frozenset({ta, tb}) in DECLARED_FIT_TAGS


def interference_scan(bodies, *, ignore_pairs=()):
    """Worst gap over every non-fit primitive pair. Negative means overlap."""
    ignore = {frozenset(p) for p in ignore_pairs}
    worst = {"gap": float("inf"), "a": None, "b": None}
    overlaps = []
    ids = sorted(bodies)
    for i, ba in enumerate(ids):
        for bb in ids[i + 1:]:
            if frozenset({ba, bb}) in ignore:
                continue
            for pa in bodies[ba]:
                for pb in bodies[bb]:
                    if pair_is_declared_fit(pa["tag"], pb["tag"]):
                        continue
                    g = capsule_gap(pa, pb)
                    if g < worst["gap"]:
                        worst = {"gap": g, "a": "%s/%s" % (ba, pa["tag"]),
                                 "b": "%s/%s" % (bb, pb["tag"])}
                    if g < 0.0:
                        overlaps.append({"a": "%s/%s" % (ba, pa["tag"]),
                                         "b": "%s/%s" % (bb, pb["tag"]),
                                         "gap_mm": round(g, ROUND)})
    return {"min_gap_mm": round(worst["gap"], ROUND),
            "closest_pair": [worst["a"], worst["b"]],
            "overlap_count": len(overlaps), "overlaps": overlaps[:12]}


def heel_arm_gap(P, i, theta, ring_z, ring_rot, mutation=None):
    """Gap between one leg's heel and the nearest ring arm. Negative = blocked."""
    heel = leg_primitives(P, i, theta, mutation)[1]
    arms = [p for p in ring_primitives(P, ring_z, ring_rot, mutation)
            if p["tag"] == "ring_arm"]
    if not arms:
        return float("inf")
    return min(capsule_gap(heel, a) for a in arms)


def fold_arrest_angle(P, i, ring_z, ring_rot, *, theta_from=None, mutation=None):
    """How far the leg can fold back before the ring arm stops it.

    Returns the angle at which the heel first touches an arm, or None if the
    whole range is clear. This is the measurement that decides whether the
    deployed state is geometrically blocked, and it is why a single deployed
    pose is not evidence: the arrest is a property of the SWEEP.
    """
    theta_from = P["theta_deployed"] if theta_from is None else theta_from
    n = int(P["samples_coarse"]) + int(P["samples_refine"])
    prev = None
    for k in range(n + 1):
        th = theta_from - (theta_from - P["theta_stored"]) * k / float(n)
        g = heel_arm_gap(P, i, th, ring_z, ring_rot, mutation)
        if g < 0.0:
            return {"arrested": True, "arrest_theta_deg": round(th, 4),
                    "free_travel_deg": round(theta_from - th, 4),
                    "gap_at_deployed_mm": round(prev if prev is not None else g, ROUND)}
        prev = g
    return {"arrested": False, "arrest_theta_deg": None,
            "free_travel_deg": round(theta_from - P["theta_stored"], 4),
            "min_gap_mm": round(prev, ROUND)}


# ---------------------------------------------------------------------------
# Configurations and trajectories
# ---------------------------------------------------------------------------

def configurations(P):
    td, ts = P["theta_deployed"], P["theta_stored"]
    zl, zr, rot = P["ring_z_locked"], P["ring_z_released"], P["ring_release_rot"]
    return {
        "STORED":             {"legs": [ts, ts, ts], "ring_z": zl, "ring_rot": rot},
        "DEPLOYMENT_ENABLED": {"legs": [ts, ts, ts], "ring_z": zl, "ring_rot": rot},
        "DEPLOYING":          {"legs": [td / 2] * 3, "ring_z": zl, "ring_rot": rot},
        "DEPLOYED_UNLOCKED":  {"legs": [td, td, td], "ring_z": zl, "ring_rot": rot},
        "DEPLOYED_LOCKED":    {"legs": [td, td, td], "ring_z": zl, "ring_rot": 0.0},
        "DELIBERATE_RELEASE": {"legs": [td, td, td], "ring_z": zr, "ring_rot": rot},
        "FOLDING":            {"legs": [td / 2] * 3, "ring_z": zl, "ring_rot": rot},
        "RETURNED_STORED":    {"legs": [ts, ts, ts], "ring_z": zl, "ring_rot": rot},
    }


def _lerp(a, b, u):
    return a + (b - a) * u


def _samples(P, critical_us):
    """Deterministic base sampling with refinement around critical fractions."""
    n = int(P["samples_coarse"])
    us = [k / float(n) for k in range(n + 1)]
    m = int(P["samples_refine"])
    for cu in critical_us:
        for k in range(m + 1):
            u = cu + (k / float(m) - 0.5) * 0.12
            if 0.0 <= u <= 1.0:
                us.append(u)
    return sorted(set(round(u, 9) for u in us))


def trajectories(P):
    """Sampled transitions. Endpoint-only witnesses are never produced here."""
    cfg = configurations(P)
    td, ts = P["theta_deployed"], P["theta_stored"]
    zl, zr, rot = P["ring_z_locked"], P["ring_z_released"], P["ring_release_rot"]
    trs = {}

    # STORED -> DEPLOYMENT_ENABLED: ring already clear; nothing moves.
    trs["T1_STORED_TO_DEPLOYMENT_ENABLED"] = [
        {"u": u, "legs": [ts] * 3, "ring_z": zl, "ring_rot": rot}
        for u in _samples(P, [0.5])]

    # DEPLOYMENT_ENABLED -> DEPLOYED_UNLOCKED: the legs swing out.
    trs["T2_DEPLOY"] = [
        {"u": u, "legs": [_lerp(ts, td, u)] * 3, "ring_z": zl, "ring_rot": rot}
        for u in _samples(P, [0.0, 0.5, 1.0])]

    # DEPLOYED_UNLOCKED -> DEPLOYED_LOCKED: ring rotates back onto the heels.
    trs["T3_LOCK"] = [
        {"u": u, "legs": [td] * 3, "ring_z": zl, "ring_rot": _lerp(rot, 0.0, u)}
        for u in _samples(P, [0.8, 1.0])]

    # DEPLOYED_LOCKED -> DELIBERATE_RELEASE: lift, then rotate. Two-part action.
    lift = [{"u": 0.5 * u, "legs": [td] * 3, "ring_z": _lerp(zl, zr, u),
             "ring_rot": 0.0} for u in _samples(P, [0.0, 1.0])]
    turn = [{"u": 0.5 + 0.5 * u, "legs": [td] * 3, "ring_z": zr,
             "ring_rot": _lerp(0.0, rot, u)} for u in _samples(P, [0.0, 1.0])]
    trs["T4_DELIBERATE_RELEASE"] = lift + turn

    # DELIBERATE_RELEASE -> RETURNED_STORED: ring lowers, then legs fold.
    drop = [{"u": 0.25 * u, "legs": [td] * 3,
             "ring_z": _lerp(zr, zl, u), "ring_rot": rot} for u in _samples(P, [1.0])]
    fold = [{"u": 0.25 + 0.75 * u, "legs": [_lerp(td, ts, u)] * 3,
             "ring_z": zl, "ring_rot": rot} for u in _samples(P, [0.0, 0.5, 1.0])]
    trs["T5_FOLD_TO_STORED"] = drop + fold
    return trs


def envelope(bodies):
    """Axis-aligned extent of the whole assembly, capsule radii included."""
    lo = [float("inf")] * 3
    hi = [-float("inf")] * 3
    for prims in bodies.values():
        for p in prims:
            for pt in (p["a"], p["b"]):
                for ax in range(3):
                    lo[ax] = min(lo[ax], pt[ax] - p["r"])
                    hi[ax] = max(hi[ax], pt[ax] + p["r"])
    return {"x_mm": round(hi[0] - lo[0], ROUND), "y_mm": round(hi[1] - lo[1], ROUND),
            "z_mm": round(hi[2] - lo[2], ROUND),
            "radial_mm": round(max(hi[0] - lo[0], hi[1] - lo[1]), ROUND)}


def foot_points(P, theta):
    pts = []
    for i in range(int(P["station_count"])):
        _phi, rhat, _that, hinge = station_frame(P, i)
        th = math.radians(theta)
        d = add(mul((0, 0, 1.0), -math.cos(th)), mul(rhat, math.sin(th)))
        pts.append(add(hinge, mul(d, P["leg_len"])))
    return pts


def triangle_area(pts):
    (x1, y1, _), (x2, y2, _), (x3, y3, _) = pts
    return abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2.0


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def assembly_steps(P, *, mutation=None):
    """Ordered installation. Each step names what it establishes and needs."""
    steps = [
        dict(id="AS-01", installs="BODY-HUB", predecessors=[],
             direction=None, path="datum body, placed",
             establishes=[], deformation=False),
        dict(id="AS-02", installs="BODY-RING", predecessors=["AS-01"],
             direction="-Z along the column, from above",
             path="ring bore over the plain column down to the shoulder",
             establishes=["REL-RING-SLIDE"], deformation=False),
        dict(id="AS-03", installs="BODY-RINGCAPTOR", predecessors=["AS-02"],
             direction="-Z along the column, from above",
             path="captor bore over the column to its seat",
             establishes=["REL-RING-CAPTIVE"], deformation=False),
        dict(id="AS-04", installs="BODY-CAPTORPIN", predecessors=["AS-03"],
             direction="+X through the cross hole",
             path="pin through the captor and column",
             establishes=["REL-CAPTOR-RETAINED"], deformation=False),
    ]
    for i, k in enumerate(LEG_KEYS):
        n = 5 + i * 3
        steps += [
            dict(id="AS-%02d" % n, installs="BODY-LEG-%s" % k,
                 predecessors=["AS-01"],
                 direction="radially inward into the clevis",
                 path="leg eye between the clevis arms",
                 establishes=[], deformation=False),
            dict(id="AS-%02d" % (n + 1), installs="BODY-PIN-%s" % k,
                 predecessors=["AS-%02d" % n],
                 direction="tangential along the hinge axis",
                 path="through clevis arm, leg eye, clevis arm",
                 establishes=["REL-HINGE-%s" % k], deformation=False),
            dict(id="AS-%02d" % (n + 2), installs="BODY-CLIP-%s" % k,
                 predecessors=["AS-%02d" % (n + 1)],
                 direction="tangential onto the pin groove",
                 path="clip onto the exposed pin end",
                 establishes=["REL-PIN-RETAINED-%s" % k], deformation=False),
        ]
    steps += [
        dict(id="AS-14", installs="BODY-TOPPLATE", predecessors=["AS-01"],
             direction="-Z over the spigot, from above",
             path="plate bore over the spigot onto the column step",
             establishes=["REL-PLATE-SEATED"], deformation=False),
        dict(id="AS-15", installs="BODY-TOPPIN", predecessors=["AS-14"],
             direction="+X through the cross hole",
             path="pin through the plate and spigot",
             establishes=["REL-PLATE-RETAINED"], deformation=False),
    ]
    if mutation == "CYCLE":
        for s in steps:
            if s["id"] == "AS-01":
                s["predecessors"] = ["AS-15"]
    if mutation == "RING_AFTER_CAPTOR":
        for s in steps:
            if s["id"] == "AS-02":
                s["predecessors"] = ["AS-03"]
            if s["id"] == "AS-03":
                s["predecessors"] = ["AS-01"]
    return steps


def acyclic(steps):
    ids = {s["id"] for s in steps}
    dangling = [(s["id"], p) for s in steps for p in s["predecessors"] if p not in ids]
    order, seen, stack = [], set(), set()
    graph = {s["id"]: list(s["predecessors"]) for s in steps}

    def visit(n):
        if n in stack:
            return False
        if n in seen:
            return True
        stack.add(n)
        for m in graph.get(n, []):
            if m in graph and not visit(m):
                return False
        stack.discard(n)
        seen.add(n)
        order.append(n)
        return True

    ok = all(visit(n) for n in sorted(graph))
    return {"acyclic": ok and not dangling, "dangling_predecessors": dangling,
            "topological_order": order if ok else []}


#: Bodies that slide over the hub along their insertion axis. A bore smaller than
#: the shaft it must pass is a blocked path no swept-collision check would see -
#: the body simply never reaches the scene, so nothing collides.
BORED_BODIES = {
    "BODY-RING":       ("ring_bore_r", ["spigot_r", "col_r"]),
    "BODY-RINGCAPTOR": (None,          ["spigot_r", "col_r"]),   # bore = col_r + slip
    "BODY-TOPPLATE":   ("plate_bore_r", ["spigot_r"]),
}


def bore_feasible(P, body):
    """Can this body physically pass over the features on its insertion axis?"""
    if body not in BORED_BODIES:
        return {"applicable": False, "pass": True}
    bore_key, over = BORED_BODIES[body]
    bore = P[bore_key] if bore_key else P["col_r"] + P["ring_slip"]
    worst = max(P[k] for k in over)
    return {"applicable": True, "bore_r": round(bore, ROUND),
            "must_pass_over_r": round(worst, ROUND),
            "margin_mm": round(bore - worst, ROUND),
            "pass": bore >= worst}


def insertion_path_clear(P, step, *, mutation=None):
    """Sweep the installed body along its insertion direction against what is
    already there. A path checked against an EMPTY frame proves nothing, so the
    scene is always the configuration the preceding steps produced."""
    body = step["installs"]
    bore = bore_feasible(P, body)
    if not bore["pass"]:
        return {"step": step["id"], "body": body, "samples": 0, "min_gap_mm": None,
                "clear": False, "reason": "BORE_TOO_SMALL", "bore": bore}
    installed = {s["installs"] for s in assembly_steps(P, mutation=mutation)
                 if _precedes(s["id"], step["id"])}
    if not installed:
        return {"step": step["id"], "body": body, "samples": 0,
                "min_gap_mm": None, "clear": True, "note": "datum body", "bore": bore}

    td = P["theta_deployed"]
    # Legs are installed in their deployed pose; the ring is installed at the
    # released angular position, which is the orientation its arms fit through.
    scene = build_state(P, [td] * 3, P["ring_z_locked"], P["ring_release_rot"],
                        present=installed, mutation=mutation)
    n = int(P["samples_coarse"])
    worst = float("inf")
    for k in range(n + 1):
        u = k / float(n)
        prims = _approach_primitives(P, body, u, mutation)
        if prims is None:
            continue
        scene_plus = dict(scene)
        scene_plus[body] = prims
        res = interference_scan(scene_plus)
        worst = min(worst, res["min_gap_mm"])
    return {"step": step["id"], "body": body, "samples": n + 1,
            "min_gap_mm": round(worst, ROUND),
            "clear": worst >= 0.0, "bore": bore,
            "checked_against": sorted(installed)}


def _precedes(a, b):
    return a != b and a < b          # ids are zero-padded and monotonic


def _approach_primitives(P, body, u, mutation=None):
    """The installed body backed off along its insertion direction by (1-u)."""
    back = (1.0 - u)
    if body == "BODY-RING":
        return ring_primitives(P, P["ring_z_locked"] + back * 70.0,
                               P["ring_release_rot"], mutation)
    if body == "BODY-RINGCAPTOR":
        return [{"kind": "zcyl", "tag": "captor",
                 "a": (0, 0, P["captor_z_bot"] + back * 60.0),
                 "b": (0, 0, P["captor_z_bot"] + P["captor_h"] + back * 60.0),
                 "r": P["captor_r"]}]
    if body == "BODY-TOPPLATE":
        return [{"kind": "zcyl", "tag": "topplate",
                 "a": (0, 0, P["col_top_z"] + back * 40.0),
                 "b": (0, 0, P["col_top_z"] + P["plate_t"] + back * 40.0),
                 "r": P["plate_r"]}]
    if body in ("BODY-CAPTORPIN", "BODY-TOPPIN"):
        base = (captor_pin_primitives(P) if body == "BODY-CAPTORPIN"
                else toppin_primitives(P))[0]
        shift = back * 46.0
        return [{"tag": base["tag"], "a": add(base["a"], (shift, 0, 0)),
                 "b": add(base["b"], (shift, 0, 0)), "r": base["r"]}]
    for i, k in enumerate(LEG_KEYS):
        if body == "BODY-LEG-%s" % k:
            _phi, rhat, _that, _h = station_frame(P, i)
            prims = leg_primitives(P, i, P["theta_deployed"], mutation)
            off = mul(rhat, back * 55.0)
            return [{"tag": p["tag"], "a": add(p["a"], off), "b": add(p["b"], off),
                     "r": p["r"]} for p in prims]
        if body == "BODY-PIN-%s" % k:
            _phi, _rhat, that, _h = station_frame(P, i)
            p = pin_primitives(P, i)[0]
            off = mul(that, back * 48.0)
            return [{"tag": p["tag"], "a": add(p["a"], off), "b": add(p["b"], off),
                     "r": p["r"]}]
        if body == "BODY-CLIP-%s" % k:
            _phi, _rhat, that, _h = station_frame(P, i)
            p = clip_primitives(P, i)[0]
            off = mul(that, back * 40.0)
            return [{"tag": p["tag"], "a": add(p["a"], off), "b": add(p["b"], off),
                     "r": p["r"]}]
    return None


# ---------------------------------------------------------------------------
# Phase A checks
# ---------------------------------------------------------------------------

def run_checks(P, *, mutation=None, present=None, drop_trajectory=False,
               teleport=False, assembly_mutation=None):
    """Every Phase A acceptance check. Returns {check_id: {...}}."""
    R = {}
    cfg = configurations(P)
    present = present or set(BODY_IDS)
    td = P["theta_deployed"]

    legs_present = [k for k in LEG_KEYS if "BODY-LEG-%s" % k in present]
    R["PA-01_three_legs"] = {"count": len(legs_present), "expected": 3,
                             "pass": len(legs_present) == 3}

    feet = foot_points(P, td)
    area = triangle_area(feet)
    dirs = []
    for i in range(int(P["station_count"])):
        _phi, rhat, _t, _h = station_frame(P, i)
        dirs.append([round(c, 4) for c in rhat])
    R["PA-02_distinct_directions"] = {"directions": dirs,
                                      "distinct": len({tuple(d) for d in dirs}) == 3,
                                      "pass": len({tuple(d) for d in dirs}) == 3}
    R["PA-03_feet_non_collinear"] = {"footprint_area_mm2": round(area, ROUND),
                                     "pass": area > 1.0}

    steps = assembly_steps(P, mutation=assembly_mutation)
    ac = acyclic(steps)
    R["PA-04_assembly_acyclic"] = dict(ac, pass_=ac["acyclic"], step_count=len(steps))
    R["PA-04_assembly_acyclic"]["pass"] = ac["acyclic"]

    paths = [insertion_path_clear(P, s, mutation=mutation) for s in steps
             if s["installs"] in present]
    bad = [p for p in paths if not p["clear"]]
    R["PA-05_insertion_paths"] = {"checked": len(paths), "blocked": len(bad),
                                  "blocked_steps": [p["step"] for p in bad],
                                  "min_gap_mm": min([p["min_gap_mm"] for p in paths
                                                     if p["min_gap_mm"] is not None] or [None]),
                                  "pass": not bad}
    final = [p for p in paths if p["body"] in ("BODY-TOPPLATE", "BODY-RINGCAPTOR")]
    R["PA-06_final_retainer_installable"] = {
        "checked": [p["body"] for p in final],
        "pass": all(p["clear"] for p in final) and len(final) == 2}

    # captivity: the ring cannot leave along +Z past the captor, nor -Z past the
    # shoulder. Both are geometric facts about radii, not assertions.
    ring_captive = (P["captor_r"] > P["ring_bore_r"] and
                    P["shoulder_r"] > P["ring_bore_r"] and
                    "BODY-RINGCAPTOR" in present)
    R["PA-07_ring_captive"] = {
        "captor_r": P["captor_r"], "shoulder_r": P["shoulder_r"],
        "ring_bore_r": P["ring_bore_r"],
        "upper_stop": P["captor_r"] > P["ring_bore_r"] and "BODY-RINGCAPTOR" in present,
        "lower_stop": P["shoulder_r"] > P["ring_bore_r"],
        "travel_mm": round(P["ring_z_released"] - P["ring_z_locked"], ROUND),
        "pass": ring_captive}

    hinge_ok = all("BODY-PIN-%s" % k in present and "BODY-CLIP-%s" % k in present
                   for k in legs_present) and len(legs_present) == 3
    R["PA-08_hinge_retention"] = {
        "legs": legs_present,
        "pins": [k for k in LEG_KEYS if "BODY-PIN-%s" % k in present],
        "clips": [k for k in LEG_KEYS if "BODY-CLIP-%s" % k in present],
        "clip_exceeds_pin": P["clip_r"] > P["hinge_pin_r"],
        "pass": hinge_ok and P["clip_r"] > P["hinge_pin_r"]}

    # blocking, per leg, measured by sweeping the fold-back
    locked = cfg["DEPLOYED_LOCKED"]
    arrests = {}
    for i, k in enumerate(LEG_KEYS):
        if "BODY-LEG-%s" % k not in present:
            continue
        arrests[k] = fold_arrest_angle(P, i, locked["ring_z"], locked["ring_rot"],
                                       mutation=mutation)
    R["PA-09_locked_blocks_all_three"] = {
        "per_leg": arrests,
        "blocked": [k for k, v in arrests.items() if v["arrested"]],
        "not_blocked": [k for k, v in arrests.items() if not v["arrested"]],
        "pass": len(arrests) == 3 and all(v["arrested"] for v in arrests.values())}

    rel = cfg["DELIBERATE_RELEASE"]
    clears = {}
    for i, k in enumerate(LEG_KEYS):
        if "BODY-LEG-%s" % k not in present:
            continue
        # after release the ring returns to its seat at the released angle
        clears[k] = fold_arrest_angle(P, i, P["ring_z_locked"], rel["ring_rot"],
                                      mutation=mutation)
    R["PA-10_release_clears_all_three"] = {
        "per_leg": clears,
        "still_blocked": [k for k, v in clears.items() if v["arrested"]],
        "pass": len(clears) == 3 and all(not v["arrested"] for v in clears.values())}

    # continuous paths, interior sampled, no teleport, no forbidden overlap
    trs = trajectories(P)
    if drop_trajectory:
        trs = {k: [v[0], v[-1]] for k, v in trs.items()}
    traj_report, worst_gap, jumps = {}, float("inf"), []
    for name, samples in trs.items():
        prev = None
        gmin = float("inf")
        for si, s in enumerate(samples):
            legs = list(s["legs"])
            if teleport and name == "T2_DEPLOY" and si == len(samples) // 2:
                legs[0] = legs[0] + 17.0
            bodies = build_state(P, legs, s["ring_z"], s["ring_rot"],
                                 present=present, mutation=mutation)
            res = interference_scan(bodies)
            gmin = min(gmin, res["min_gap_mm"])
            key = (tuple(round(x, 6) for x in legs),
                   round(s["ring_z"], 6), round(s["ring_rot"], 6))
            if prev is not None:
                d = max(abs(key[0][j] - prev[0][j]) for j in range(3))
                dz = abs(key[1] - prev[1])
                dr = abs(key[2] - prev[2])
                if d > 6.0 or dz > 6.0 or dr > 12.0:
                    jumps.append({"transition": name, "sample": si,
                                  "d_theta_deg": round(d, 4), "d_z_mm": round(dz, 4),
                                  "d_rot_deg": round(dr, 4)})
            prev = key
        worst_gap = min(worst_gap, gmin)
        traj_report[name] = {"samples": len(samples), "min_gap_mm": round(gmin, ROUND),
                             "endpoint_only": len(samples) <= 2}
    R["PA-11_trajectories"] = {
        "per_transition": traj_report,
        "total_samples": sum(v["samples"] for v in traj_report.values()),
        "any_endpoint_only": any(v["endpoint_only"] for v in traj_report.values()),
        "pass": not any(v["endpoint_only"] for v in traj_report.values())}
    R["PA-12_no_forbidden_overlap"] = {
        "min_gap_over_cycle_mm": round(worst_gap, ROUND),
        "target_mm": P["min_clearance_target"],
        "designed_contacts_excluded": [
            "ring seating on the hub shoulder (lower travel stop)",
            "ring meeting the captor (upper travel stop, nominal 0.0 mm)",
            "hinge pin in clevis and leg eye",
            "leg root inside the clevis boss",
        ],
        "note": "NOMINAL geometry. Not a tolerance result and not a contact claim.",
        "pass": worst_gap >= 0.0}
    R["PA-13_no_teleportation"] = {"jumps": jumps, "pass": not jumps}

    st = build_state(P, cfg["STORED"]["legs"], cfg["STORED"]["ring_z"],
                     cfg["STORED"]["ring_rot"], present=present, mutation=mutation)
    dp = build_state(P, cfg["DEPLOYED_LOCKED"]["legs"], cfg["DEPLOYED_LOCKED"]["ring_z"],
                     cfg["DEPLOYED_LOCKED"]["ring_rot"], present=present, mutation=mutation)
    es, ed = envelope(st), envelope(dp)
    smaller = [ax for ax in ("x_mm", "y_mm", "radial_mm") if es[ax] < ed[ax] - 1e-9]
    R["PA-14_stored_more_compact"] = {
        "stored": es, "deployed": ed, "smaller_extents": smaller,
        "radial_reduction_mm": round(ed["radial_mm"] - es["radial_mm"], ROUND),
        "pass": bool(smaller)}

    ids = set(BODY_IDS)
    refs = {s["installs"] for s in steps} | {p for s in steps for p in s["predecessors"]}
    step_ids = {s["id"] for s in steps}
    R["PA-15_ids_resolve"] = {
        "bodies": len(ids),
        "unresolved_bodies": sorted({s["installs"] for s in steps} - ids),
        "unresolved_predecessors": sorted(refs - ids - step_ids),
        "pass": not ({s["installs"] for s in steps} - ids) and not (refs - ids - step_ids)}

    R["PA-16_no_component_detaches"] = {
        "operational_bodies": len(present),
        "expected": len(BODY_IDS),
        "pass": len(present) == len(BODY_IDS)}
    return R


def all_pass(results):
    return all(v.get("pass", False) for v in results.values())


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

NEGATIVE_CONTROLS = [
    ("NC-A01", "remove one hinge retainer", "PA-08_hinge_retention",
     dict(present=set(BODY_IDS) - {"BODY-CLIP-A"})),
    ("NC-A02", "omit one leg", "PA-01_three_legs",
     dict(present=set(BODY_IDS) - {"BODY-LEG-C", "BODY-PIN-C", "BODY-CLIP-C"})),
    ("NC-A03", "one leg unlocked (heel too short to reach the arm)",
     "PA-09_locked_blocks_all_three", dict(mutation="SHORT_HEEL")),
    ("NC-A04", "blocker engages only two legs", "PA-09_locked_blocks_all_three",
     dict(mutation="TWO_ARMS")),
    ("NC-A05", "locking ring not captive", "PA-07_ring_captive",
     dict(present=set(BODY_IDS) - {"BODY-RINGCAPTOR"})),
    ("NC-A06", "final retainer has no installation path", "PA-06_final_retainer_installable",
     dict(param_override={"plate_bore_r": 4.0, "plate_r": 6.0})),
    ("NC-A07", "hinge-pin access closed before the pin is installed",
     "PA-05_insertion_paths", dict(param_override={"ring_z_locked": 0.0, "ring_h": 26.0})),
    ("NC-A08", "assembly dependency cycle", "PA-04_assembly_acyclic",
     dict(assembly_mutation="CYCLE")),
    ("NC-A09", "endpoint poses kept, continuous trajectory deleted", "PA-11_trajectories",
     dict(drop_trajectory=True)),
    ("NC-A10", "intermediate leg-leg collision", "PA-12_no_forbidden_overlap",
     dict(param_override={"theta_deployed": 30.0, "hinge_r": 4.0, "leg_r": 14.0})),
    ("NC-A11", "intermediate leg-hub collision", "PA-12_no_forbidden_overlap",
     dict(param_override={"col_r": 30.0, "shoulder_top_z": -60.0})),
    ("NC-A12", "blocker still engaged after deliberate release",
     "PA-10_release_clears_all_three", dict(param_override={"ring_release_rot": 0.0})),
    ("NC-A13", "reverse folding still possible when locked", "PA-09_locked_blocks_all_three",
     dict(param_override={"ring_arm_r_out": 17.0})),
    ("NC-A14", "stored envelope not reduced in any extent", "PA-14_stored_more_compact",
     dict(param_override={"theta_deployed": 0.0})),
    ("NC-A15", "a body transform jumps between samples", "PA-13_no_teleportation",
     dict(teleport=True)),
]


def run_negative_controls(P):
    out = []
    for cid, desc, target, kw in NEGATIVE_CONTROLS:
        params = dict(P)
        params.update(kw.pop("param_override", {}))
        try:
            res = run_checks(params, **kw)
            target_failed = not res.get(target, {}).get("pass", False)
            other_failed = sorted(k for k, v in res.items()
                                  if not v.get("pass", False) and k != target)
            detail = res.get(target, {})
        except Exception as exc:                      # noqa: BLE001
            target_failed, other_failed = False, ["EXECUTION_ERROR: %s" % str(exc)[:120]]
            detail = {}
        out.append({
            "control_id": cid, "description": desc,
            "intended_failed_check": target,
            "detected": bool(target_failed),
            "also_failed": other_failed,
            "target_detail": {k: v for k, v in detail.items() if k != "per_leg"},
        })
    return out


# ---------------------------------------------------------------------------
# Signatures and reporting
# ---------------------------------------------------------------------------

def _sig(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def topology_signature(P):
    steps = assembly_steps(P)
    return _sig({
        "bodies": sorted(BODY_IDS),
        "steps": [{"id": s["id"], "installs": s["installs"],
                   "predecessors": sorted(s["predecessors"]),
                   "establishes": sorted(s["establishes"])} for s in steps],
        "configurations": {k: v for k, v in sorted(configurations(P).items())},
    })


def phase_a_geometry_signature(P):
    cfg = configurations(P)
    payload = {}
    for name in sorted(cfg):
        c = cfg[name]
        bodies = build_state(P, c["legs"], c["ring_z"], c["ring_rot"])
        payload[name] = {
            "envelope": envelope(bodies),
            "primitive_count": sum(len(v) for v in bodies.values()),
            "min_gap_mm": interference_scan(bodies)["min_gap_mm"],
        }
    payload["parameters"] = {k: P[k] for k in sorted(P)}
    return _sig(payload)


def evidence_signature(results, controls):
    return _sig({
        "checks": {k: v.get("pass") for k, v in sorted(results.items())},
        "controls": {c["control_id"]: c["detected"] for c in controls},
    })


def main():
    os.makedirs(OUT, exist_ok=True)
    P = load_params()
    print("EXE-BM003-01 Phase A - metric assembly and kinematic proxy")

    steps = assembly_steps(P)
    results = run_checks(P)
    for k in sorted(results):
        print("  %-34s %s" % (k, "PASS" if results[k].get("pass") else "FAIL"))
    controls = run_negative_controls(P)
    detected = sum(1 for c in controls if c["detected"])
    print("  negative controls: %d/%d detected" % (detected, len(controls)))

    sigs = {
        "phase_a_geometry_signature_sha256": phase_a_geometry_signature(P),
        "topology_signature_sha256": topology_signature(P),
        "evidence_signature_sha256": evidence_signature(results, controls),
    }

    cfg = configurations(P)
    bodies_manifest = []
    for bid in BODY_IDS:
        bodies_manifest.append({
            "body_id": bid,
            "role": ("datum" if bid == "BODY-HUB" else
                     "support leg" if "LEG" in bid else
                     "hinge pin" if "PIN-" in bid else
                     "hinge pin retainer" if "CLIP" in bid else
                     "captive locking ring" if bid == "BODY-RING" else
                     "ring captor" if bid == "BODY-RINGCAPTOR" else
                     "captor retainer" if bid == "BODY-CAPTORPIN" else
                     "support plate" if bid == "BODY-TOPPLATE" else "plate retainer"),
            "installed_as": "DISCRETE",
        })

    report = {
        "reference_id": REFERENCE_ID, "benchmark_id": "BM-003",
        "phase": "PHASE_A_METRIC_PROXY",
        "fidelity": "capsule proxy, analytic segment distances, NOMINAL geometry",
        "declared_state_maintenance_class": "KINEMATIC_BLOCK",
        "body_count": len(BODY_IDS),
        "bodies": bodies_manifest,
        "assembly_step_count": len(steps),
        "assembly_steps": steps,
        "configurations": cfg,
        "checks": results,
        "negative_controls": controls,
        "negative_controls_detected": detected,
        "signatures": sigs,
        "overall": "PASS" if (all_pass(results) and detected == len(controls)) else "FAIL",
        "not_established": [
            "load capacity, stress, stiffness, buckling",
            "fatigue, wear, lifetime",
            "tolerance-induced looseness; every clearance here is NOMINAL",
            "contact pressure, friction behaviour",
            "impact resistance",
            "manufacturing-process feasibility",
        ],
    }
    with open(os.path.join(OUT, "phase_a_report.json"), "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    with open(os.path.join(OUT, "phase_a_signatures.json"), "w") as fh:
        json.dump(sigs, fh, indent=2, sort_keys=True)
    trs = trajectories(P)
    with open(os.path.join(OUT, "phase_a_trajectories.json"), "w") as fh:
        json.dump({k: v for k, v in sorted(trs.items())}, fh, indent=2, sort_keys=True)

    print("  signatures: geometry %s" % sigs["phase_a_geometry_signature_sha256"][:16])
    print("              topology %s" % sigs["topology_signature_sha256"][:16])
    print("              evidence %s" % sigs["evidence_signature_sha256"][:16])
    print("OVERALL: %s" % report["overall"])
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
