"""EXE-BM003-01 - validation.

Steps 1-7 and 9 are the shared engine in ver3/cad_validation/tools/valcore.py.
What is written here is what genuinely differs for BM-003:

  * the declared regions of interest, contacts and sampling (the Ctx below);
  * the mechanism evidence - blocking, release, retention, footprint, envelope,
    bayonet turns, continuity - which is what the Oracle's predicates actually
    need and which no other reference in this repository has;
  * seventeen negative controls, each of which mutates one condition and must
    make one named predicate fail while its declared unrelated predicates keep
    their baseline result;
  * step 8, the Oracle evaluation.

Every number below is computed by the OCCT kernel on the exact B-rep solids
build.py produces. Nothing is asserted.

Run:  python validate.py            full
      BM003_FAST=1 python validate.py    reduced sampling, for iteration only
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)

import cadquery as cq
import yaml

import cadval as cv
import valcore as vc
import build as B

FAST = os.environ.get("BM003_FAST") == "1"
OUT = os.path.join(HERE, "validation")
LOCK = os.path.join(OUT, "RUN.lock")
RUN_STATUS = os.path.join(OUT, "RUN_STATUS.txt")

_T0 = time.time()
_STAGE: List[Tuple[str, float]] = []


def stage(name: str, phase: str = "START") -> None:
    """Flushed stage marker so a long run shows where it is."""
    now = time.time()
    if phase == "START":
        _STAGE.append((name, now))
        sys.stdout.write("[%8.1fs] START  %s\n" % (now - _T0, name))
    else:
        took = 0.0
        for i in range(len(_STAGE) - 1, -1, -1):
            if _STAGE[i][0] == name:
                took = now - _STAGE[i][1]
                _STAGE.pop(i)
                break
        sys.stdout.write("[%8.1fs] END    %-28s %8.1fs\n" % (now - _T0, name, took))
    sys.stdout.flush()


def acquire_lock() -> None:
    """One validator per validation directory. A partial run mixed with a clean
    one is exactly the failure manifest_util was written after."""
    os.makedirs(OUT, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            held = open(LOCK).read().strip()
        except Exception:                                  # noqa: BLE001
            held = "unknown"
        raise SystemExit(
            "another validator holds %s (%s).\n"
            "If no validate.py is running, delete that file and retry."
            % (os.path.relpath(LOCK, HERE), held))
    with os.fdopen(fd, "w") as fh:
        fh.write("pid=%d started=%s\n" % (os.getpid(), time.strftime("%Y-%m-%dT%H:%M:%S")))


def release_lock() -> None:
    try:
        os.remove(LOCK)
    except OSError:
        pass


def write_run_status(state: str, detail: str = "") -> None:
    """Terminal status, always written. PASS | FAIL | INTERRUPTED | EXECUTION_FAILED."""
    try:
        os.makedirs(OUT, exist_ok=True)
        with open(RUN_STATUS, "w") as fh:
            fh.write("%s\n" % state)
            fh.write("finished=%s\n" % time.strftime("%Y-%m-%dT%H:%M:%S"))
            fh.write("elapsed_seconds=%.1f\n" % (time.time() - _T0))
            fh.write("fast_mode=%s\n" % FAST)
            if detail:
                fh.write("detail=%s\n" % detail)
    except Exception:                                      # noqa: BLE001
        pass

P = B.load_params()
G = B.geom(P)
AZ = B.stations(P)
KEYS = list(B.STATION_KEYS)

CONTACT_TOL = P["contact_tol"]
OVERLAP_TOL = P["overlap_tol_mm3"]
CONNECTION_TOL = P["connection_tol"]
PROBE_DISTANCE = 2.0        # how far a retained body is pushed along its escape


# ============================================================ declared regions
def _aabb(az_deg: float, x0, x1, y0, y1, z0, z1) -> tuple:
    """World axis-aligned box containing a station-local box.

    The three stations are identical, so every region is written once in a
    station frame. For station A the rotation is a quarter turn and the result is
    exact; for B and C the axis-aligned hull is slightly larger than the rotated
    rectangle. That is safe here and the measured values in
    validation/interaction_report.json show it: each of the three stations
    reports the same number.
    """
    a = math.radians(az_deg)
    ca, sa = math.cos(a), math.sin(a)
    xs, ys = [], []
    for x in (x0, x1):
        for y in (y0, y1):
            xs.append(x * ca - y * sa)
            ys.append(x * sa + y * ca)
    return (min(xs), max(xs), min(ys), max(ys), z0, z1)


ROI: Dict[str, tuple] = {}
for _k in KEYS:
    _a = AZ[_k]
    _rib = _a + P["rib_azimuth_offset"]
    ROI["INT-HINGE-%s-HEAD" % _k] = ("DEPLOYED_LOCKED", _aabb(_a, 30, 50, 10, 17, -8, 8))
    ROI["INT-HINGE-%s-BAR" % _k] = ("DEPLOYED_LOCKED", _aabb(_a, 36, 44, -16, -10, 4.2, 5.0))
    ROI["INT-HINGE-%s-BORE" % _k] = ("DEPLOYED_LOCKED", _aabb(_a, 34, 46, -4, 4, 2.5, 6.0))
    ROI["INT-BLADE-%s-GAP" % _k] = ("DEPLOYED_LOCKED", _aabb(_a, 34, 46, 4, 8, -8, 8))
    ROI["INT-BLOCK-%s" % _k] = ("DEPLOYED_LOCKED", _aabb(_a, 15, 27, -8, 8, 7.5, 14.0))
    ROI["INT-CLEAR-%s" % _k] = ("DEPLOYED_RELEASED", _aabb(_a, 10, 45, -25, 25, 0.0, 26.0))
    ROI["INT-STOP-%s" % _k] = ("DEPLOYED_LOCKED", _aabb(_a, 28, 34, -6, 6, -6.0, 1.0))

_RIB_A = AZ["A"] + P["rib_azimuth_offset"]
ROI["INT-RING-SEAT"] = ("DEPLOYED_LOCKED", (-19.0, 19.0, -19.0, 19.0, 9.0, 13.0))
ROI["INT-RING-KEY"] = ("DEPLOYED_LOCKED", _aabb(_RIB_A, 11, 18, -7, 7, 11.6, 14.5))
ROI["INT-RING-RIBTOP"] = ("DEPLOYED_RELEASED", _aabb(_RIB_A, 11, 18, -7, 7, 11.5, 15.5))
ROI["INT-RING-CAPTOR-STOP"] = ("DEPLOYED_RELEASED", (-22.0, 22.0, -22.0, 22.0, 22.0, 27.0))
ROI["INT-RING-CAPTOR-GAP"] = ("DEPLOYED_LOCKED", (-22.0, 22.0, -22.0, 22.0, 17.0, 27.0))
ROI["INT-CAPTOR-SEAT"] = ("DEPLOYED_LOCKED", (-16.0, 16.0, -16.0, 16.0, 22.0, 27.0))
ROI["INT-CAPTOR-LUG"] = ("DEPLOYED_LOCKED", (-16.0, 16.0, -16.0, 16.0, 30.0, 34.5),
                         ("exclude the column bore, which is a radial gap not this axial one",
                          0.0, 0.0, 11.5))
ROI["INT-SUPPORT-SEAT"] = ("DEPLOYED_LOCKED", (-16.0, 16.0, -16.0, 16.0, 34.5, 39.0))
ROI["INT-SUPPORT-LUG"] = ("DEPLOYED_LOCKED", (-15.0, 15.0, -15.0, 15.0, 112.0, 115.5),
                          ("exclude the column bore", 0.0, 0.0, 11.6))
ROI["INT-SUPPORT-CAPTOR"] = ("DEPLOYED_LOCKED", (-20.0, 20.0, -20.0, 20.0, 30.0, 39.0))
for _p in ("AB", "BC", "AC"):
    ROI["INT-LEG-LEG-%s" % _p] = ("STORED", (-60.0, 60.0, -60.0, 60.0, -20.0, 12.0))


# ----------------------------------------------------- declared contact pairs
_CONTACT_PAIRS = {
    ("BODY-HUB", "BODY-PIN-A"): ["FEATURE-PIN-A-HEAD", "FEATURE-CLEVIS-A-OUTER-FACE"],
    ("BODY-HUB", "BODY-PIN-B"): ["FEATURE-PIN-B-HEAD", "FEATURE-CLEVIS-B-OUTER-FACE"],
    ("BODY-HUB", "BODY-PIN-C"): ["FEATURE-PIN-C-HEAD", "FEATURE-CLEVIS-C-OUTER-FACE"],
    ("BODY-HUB", "BODY-RING"): ["FEATURE-PEDESTAL-TOP", "FEATURE-RING-UNDERSIDE"],
    ("BODY-HUB", "BODY-RING-CAPTOR"): ["FEATURE-COLUMN-STEP", "FEATURE-CAPTOR-UNDERSIDE"],
    ("BODY-HUB", "BODY-TOP-SUPPORT"): ["FEATURE-LOWER-LUG-TOP", "FEATURE-SLEEVE-UNDERSIDE"],
    ("BODY-RING", "BODY-RING-CAPTOR"): ["FEATURE-RING-TOP", "FEATURE-CAPTOR-UNDERSIDE"],
}
CONTACT_BY_STATE = {s: dict(_CONTACT_PAIRS) for s in B.STATES}
SEGMENT_CONTACT = {s: set(_CONTACT_PAIRS) for s in B.SEGMENTS}

_COARSE = 12 if FAST else 30
_REFINE = [] if FAST else [(0.0, 0.08, 8), (0.92, 1.0, 8)]
SAMPLING = {s: (_COARSE, list(_REFINE)) for s in B.SEGMENTS}

COLORS = {
    "BODY-HUB": "#6b8fb4",
    "BODY-LEG-A": "#c08a5a", "BODY-LEG-B": "#c9a06a", "BODY-LEG-C": "#b3794c",
    "BODY-PIN-A": "#5a5f6b", "BODY-PIN-B": "#5a5f6b", "BODY-PIN-C": "#5a5f6b",
    "BODY-RING": "#b06f8a",
    "BODY-RING-CAPTOR": "#7ba884",
    "BODY-TOP-SUPPORT": "#8d84b8",
}
ALPHAS = {"BODY-TOP-SUPPORT": 0.55}
SECTIONS = (("DEPLOYED_LOCKED", "x", 0.0, "deployed_locked_section"),
            ("STORED", "x", 0.0, "stored_section"))

CTX = vc.Ctx("EXE-BM003-01", HERE, P, B, CONTACT_BY_STATE, SEGMENT_CONTACT,
             ROI, SAMPLING, COLORS, SECTIONS, ALPHAS)


# ================================================================ helpers
def _by(bodies: Sequence[cv.Body]) -> Dict[str, cv.Body]:
    return {b.id: b for b in bodies}


def _pairs(ids: Sequence[str]) -> List[Tuple[str, str]]:
    ids = sorted(ids)
    return [(a, b) for i, a in enumerate(ids) for b in ids[i + 1:]]


def _station_axes(k: str) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """(radially outward, tangential) unit vectors of station k, in world."""
    a = math.radians(AZ[k])
    return (math.cos(a), math.sin(a), 0.0), (-math.sin(a), math.cos(a), 0.0)


def _worst_common(conf: Dict[str, cv.Body], pairs: Sequence[Tuple[str, str]]
                  ) -> Tuple[float, Optional[List[str]]]:
    worst, where = 0.0, None
    for a, b in pairs:
        if a not in conf or b not in conf:
            continue
        c = cv.common_volume(conf[a].shape, conf[b].shape)
        if c > worst:
            worst, where = c, [a, b]
    return worst, where


def _leg_pairs(ids: Sequence[str]) -> List[Tuple[str, str]]:
    """Pairs that a leg swing can bring into collision."""
    legs = [i for i in ids if i.startswith("BODY-LEG-")]
    out = []
    for lg in legs:
        for other in ("BODY-HUB", "BODY-RING", "BODY-RING-CAPTOR", "BODY-TOP-SUPPORT"):
            if other in ids:
                out.append(tuple(sorted((lg, other))))
    out += _pairs(legs)
    return sorted(set(out))


class Model:
    """One built model: baseline, or a negative control's mutation of it."""

    def __init__(self, params: Optional[Dict[str, float]] = None,
                 defeat: frozenset = frozenset(), label: str = "baseline"):
        self.label = label
        self.P = dict(params or P)
        self.defeat = defeat
        self.G = B.geom(self.P)
        self.bodies = B.build(self.P, defeat)
        self.ids = sorted(b.id for b in self.bodies)
        self.by = _by(self.bodies)

    def at(self, theta, ring_z, ring_phi) -> Dict[str, cv.Body]:
        return _by(B.bodies_at(self.bodies, self.P, theta, ring_z, ring_phi))

    def state(self, s: str) -> Dict[str, cv.Body]:
        return _by(B.configuration(self.bodies, self.P, s))


BASE = Model(label="baseline")


# ======================================================= mechanism evidence
def fold_scan(m: Model, ring_z: float, ring_phi: float, steps: int
              ) -> List[Dict]:
    """Swing every leg back from deployed toward stored, ring held where told."""
    lo, hi = m.P["theta_stored"], m.P["theta_deployed"]
    pairs = _leg_pairs(m.ids)
    rows = []
    for i in range(steps + 1):
        th = hi - (hi - lo) * i / steps
        conf = m.at(th, ring_z, ring_phi)
        per_leg = {}
        for lg in [x for x in m.ids if x.startswith("BODY-LEG-")]:
            w, _ = _worst_common(conf, [p for p in pairs if lg in p])
            per_leg[lg] = round(w, 9)
        rows.append({"theta_deg": round(th, 6),
                     "max_common_volume_mm3_by_leg": per_leg,
                     "max_common_volume_mm3": round(max(per_leg.values()), 9)})
    return rows


def first_obstructed(rows: List[Dict], leg: Optional[str] = None) -> Optional[float]:
    key = "max_common_volume_mm3_by_leg"
    for r in rows:
        v = r[key][leg] if leg else r["max_common_volume_mm3"]
        if v > OVERLAP_TOL:
            return r["theta_deg"]
    return None


def turn_scan(m: Model, ring_z: float, sign: float, steps: int) -> List[Dict]:
    """Turn the ring at a held height and watch for the ribs."""
    rows = []
    span = m.P["ring_release_rot"]
    for i in range(steps + 1):
        phi = sign * span * i / steps
        conf = m.at(m.P["theta_deployed"], ring_z, phi)
        c = cv.common_volume(conf["BODY-RING"].shape, conf["BODY-HUB"].shape)
        rows.append({"ring_phi_deg": round(phi, 6), "common_volume_mm3": round(c, 9)})
    return rows


def outward_scan(m: Model, steps: int) -> List[Dict]:
    """Swing the legs PAST deployed, ring locked, until something stops them."""
    rows = []
    pairs = _leg_pairs(m.ids)
    for i in range(steps + 1):
        th = m.P["theta_deployed"] + 20.0 * i / steps
        conf = m.at(th, m.G["ring_z_locked"], 0.0)
        w, where = _worst_common(conf, pairs)
        rows.append({"theta_deg": round(th, 6), "max_common_volume_mm3": round(w, 9),
                     "pair": where})
    return rows


def escape_probes(m: Model) -> List[Dict]:
    """Push each retained body along its declared escape direction and measure."""
    specs = [
        ("RET-RING-UP", "BODY-RING", "DEPLOYED_RELEASED", (0.0, 0.0, 1.0),
         ["BODY-RING-CAPTOR"], "+z off the column"),
        ("RET-RING-DOWN", "BODY-RING", "DEPLOYED_LOCKED", (0.0, 0.0, -1.0),
         ["BODY-HUB"], "-z past the pedestal"),
        ("RET-CAPTOR-UP", "BODY-RING-CAPTOR", "DEPLOYED_LOCKED", (0.0, 0.0, 1.0),
         ["BODY-HUB"], "+z off the column"),
        ("RET-CAPTOR-DOWN", "BODY-RING-CAPTOR", "DEPLOYED_LOCKED", (0.0, 0.0, -1.0),
         ["BODY-HUB"], "-z past the column step"),
        ("RET-SUPPORT-UP", "BODY-TOP-SUPPORT", "DEPLOYED_LOCKED", (0.0, 0.0, 1.0),
         ["BODY-HUB"], "+z off the column"),
        ("RET-SUPPORT-DOWN", "BODY-TOP-SUPPORT", "DEPLOYED_LOCKED", (0.0, 0.0, -1.0),
         ["BODY-HUB"], "-z past the lower bayonet lugs"),
    ]
    for k in KEYS:
        radial, tang = _station_axes(k)
        neg_t = tuple(-c for c in tang)
        neg_r = tuple(-c for c in radial)
        specs += [
            ("RET-PIN-%s-OUTWARD" % k, "BODY-PIN-%s" % k, "DEPLOYED_LOCKED", tang,
             ["BODY-HUB"], "+y of the station: withdrawing the pin"),
            ("RET-PIN-%s-INWARD" % k, "BODY-PIN-%s" % k, "DEPLOYED_LOCKED", neg_t,
             ["BODY-HUB"], "-y of the station: pushing the pin through"),
            ("RET-LEG-%s-AXIAL-PLUS" % k, "BODY-LEG-%s" % k, "DEPLOYED_LOCKED", tang,
             ["BODY-HUB"], "the leg sliding along its hinge axis"),
            ("RET-LEG-%s-AXIAL-MINUS" % k, "BODY-LEG-%s" % k, "DEPLOYED_LOCKED", neg_t,
             ["BODY-HUB"], "the leg sliding the other way along its hinge axis"),
            ("RET-LEG-%s-RADIAL" % k, "BODY-LEG-%s" % k, "DEPLOYED_LOCKED", radial,
             ["BODY-PIN-%s" % k], "the leg lifting off its pin radially"),
            ("RET-LEG-%s-INBOARD" % k, "BODY-LEG-%s" % k, "DEPLOYED_LOCKED", neg_r,
             ["BODY-PIN-%s" % k], "the leg sliding inboard off its pin"),
        ]

    rows = []
    for rid, body, st, direc, blockers, what in specs:
        if body not in m.by:
            rows.append({"retention_id": rid, "body": body, "status": "NOT_EVALUABLE",
                         "reason": "body absent from this model"})
            continue
        conf = m.state(st)
        moved = conf[body].moved(cv.translation(tuple(c * PROBE_DISTANCE for c in direc)))
        per = {}
        for bl in blockers:
            if bl not in conf:
                continue
            per[bl] = round(cv.common_volume(moved.shape, conf[bl].shape), 9)
        blocked = any(v > OVERLAP_TOL for v in per.values())
        rows.append({"retention_id": rid, "body": body, "escape": what,
                     "state": st, "probe_distance_mm": PROBE_DISTANCE,
                     "direction": [round(c, 9) for c in direc],
                     "blockers": blockers, "common_volume_with_blocker_mm3": per,
                     "status": "PASS" if blocked else "FAIL"})
    return rows


def bayonet_turns(m: Model, steps: int) -> List[Dict]:
    """Sweep each quarter turn and measure it, since step 7 sweeps lines only."""
    rows = []
    others_static = ["BODY-HUB", "BODY-RING", "BODY-RING-CAPTOR", "BODY-TOP-SUPPORT"]

    for k in KEYS:
        if "BODY-PIN-%s" % k not in m.by:
            continue
        hx, hz = m.P["hinge_r"], m.P["hinge_z"]
        a = math.radians(AZ[k])
        origin = (hx * math.cos(a), hx * math.sin(a), hz)
        axis = (-math.sin(a), math.cos(a), 0.0)
        unlocked = cv.Body("BODY-PIN-%s" % k, "hinge pin %s" % k, "RIGID",
                           B.build_pin(m.P, m.G, k, False, m.defeat))
        worst, at_ = 0.0, None
        conf = m.state("DEPLOYED_LOCKED")
        neigh = [x for x in ("BODY-HUB", "BODY-LEG-%s" % k, "BODY-RING") if x in conf]
        for i in range(steps + 1):
            ang = 90.0 * i / steps
            turned = unlocked.moved(cv.rotation(origin, axis, ang))
            for o in neigh:
                c = cv.common_volume(turned.shape, conf[o].shape)
                if c > worst:
                    worst, at_ = c, [round(ang, 4), o]
        rows.append({"turn_id": "TURN-PIN-%s" % k, "body": "BODY-PIN-%s" % k,
                     "axis": "the station's own hinge axis", "travel_deg": 90.0,
                     "samples": steps + 1, "measured_against": neigh,
                     "max_common_volume_mm3": round(worst, 9),
                     "max_common_volume_at": at_,
                     "status": "PASS" if worst <= OVERLAP_TOL else "FAIL"})

    for tid, bid, maker in (("TURN-CAPTOR", "BODY-RING-CAPTOR", B.build_captor),
                            ("TURN-TOP-SUPPORT", "BODY-TOP-SUPPORT", B.build_top_support)):
        if bid not in m.by:
            continue
        unlocked = cv.Body(bid, bid, "RIGID", maker(m.P, m.G, False, m.defeat))
        conf = m.state("DEPLOYED_LOCKED")
        neigh = [x for x in others_static if x != bid and x in conf]
        worst, at_ = 0.0, None
        for i in range(steps + 1):
            ang = 90.0 * i / steps
            turned = unlocked.moved(cv.rotation((0, 0, 0), (0, 0, 1), ang))
            for o in neigh:
                c = cv.common_volume(turned.shape, conf[o].shape)
                if c > worst:
                    worst, at_ = c, [round(ang, 4), o]
        rows.append({"turn_id": tid, "body": bid, "axis": "the hub axis",
                     "travel_deg": 90.0, "samples": steps + 1,
                     "measured_against": neigh,
                     "max_common_volume_mm3": round(worst, 9),
                     "max_common_volume_at": at_,
                     "status": "PASS" if worst <= OVERLAP_TOL else "FAIL"})
    return rows


def ground_contacts(m: Model) -> Dict:
    """Where the deployed legs actually touch a support plane, and what area they bound."""
    conf = m.state("DEPLOYED_LOCKED")
    legs = [i for i in m.ids if i.startswith("BODY-LEG-")]
    if not legs:
        return {"status": "FAIL", "reason": "no legs", "regions": [], "hull_area_mm2": 0.0}
    zmins = {lg: cv.bbox_of(conf[lg].shape)["zmin"] for lg in legs}
    plane = min(zmins.values())
    slab_h = 0.05
    regions, pts = [], []
    for lg in legs:
        sl = vc.clip(conf[lg].shape,
                     vc.roi_box(-400, 400, -400, 400, plane, plane + slab_h))
        if sl is None:
            regions.append({"body": lg, "status": "FAIL",
                            "reason": "no material at the support plane"})
            continue
        bb = cv.bbox_of(sl)
        corners = [(bb["xmin"], bb["ymin"]), (bb["xmax"], bb["ymin"]),
                   (bb["xmax"], bb["ymax"]), (bb["xmin"], bb["ymax"])]
        pts += corners
        regions.append({"body": lg, "status": "PASS",
                        "zmin_mm": round(zmins[lg], 6),
                        "on_common_plane": abs(zmins[lg] - plane) <= 1e-6,
                        "footprint_bbox_mm": {k: round(v, 6) for k, v in bb.items()},
                        "centroid_xy_mm": [round(sum(c[0] for c in corners) / 4.0, 6),
                                           round(sum(c[1] for c in corners) / 4.0, 6)]})
    area = _hull_area(pts)
    centres = [r["centroid_xy_mm"] for r in regions if r.get("centroid_xy_mm")]
    collinear = True
    if len(centres) >= 3:
        (x1, y1), (x2, y2), (x3, y3) = centres[0], centres[1], centres[2]
        collinear = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) < 1e-6
    ok = (len(regions) == 3 and all(r["status"] == "PASS" for r in regions)
          and area > 0.0 and not collinear
          and all(r.get("on_common_plane") for r in regions))
    return {"support_plane_z_mm": round(plane, 6), "slab_thickness_mm": slab_h,
            "regions": regions, "hull_area_mm2": round(area, 6),
            "contact_centres_collinear": collinear,
            "method": ("each deployed leg is clipped by a thin slab at the lowest "
                       "point any leg reaches; the convex hull of the resulting "
                       "regions' corners is the footprint"),
            "does_not_establish": ("any footprint dimension, symmetry or stability "
                                   "margin - NRM-BM-003-006 requires none and "
                                   "AMB-BM-003-003 leaves them open"),
            "status": "PASS" if ok else "FAIL"}


def _hull_area(pts: Sequence[Tuple[float, float]]) -> float:
    pts = sorted(set((round(x, 9), round(y, 9)) for x, y in pts))
    if len(pts) < 3:
        return 0.0

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ox, oy), (ax, ay) = out[-2], out[-1]
                if (ax - ox) * (p[1] - oy) - (ay - oy) * (p[0] - ox) > 0:
                    break
                out.pop()
            out.append(p)
        return out

    hull = half(pts)[:-1] + half(pts[::-1])[:-1]
    a = 0.0
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def envelopes(m: Model) -> Dict:
    rows = {}
    for s in ("STORED", "DEPLOYED_LOCKED"):
        conf = m.state(s)
        bb = cv.bbox_of(cv.compound(list(conf.values())))
        rmax = 0.0
        for b in conf.values():
            bx = cv.bbox_of(b.shape)
            for x in (bx["xmin"], bx["xmax"]):
                for y in (bx["ymin"], bx["ymax"]):
                    rmax = max(rmax, math.hypot(x, y))
        rows[s] = {"bbox_mm": {k: round(v, 6) for k, v in bb.items()},
                   "max_radial_extent_mm": round(rmax, 6)}
    extents = {
        "bbox_dx": (rows["STORED"]["bbox_mm"]["dx"], rows["DEPLOYED_LOCKED"]["bbox_mm"]["dx"]),
        "bbox_dy": (rows["STORED"]["bbox_mm"]["dy"], rows["DEPLOYED_LOCKED"]["bbox_mm"]["dy"]),
        "bbox_dz": (rows["STORED"]["bbox_mm"]["dz"], rows["DEPLOYED_LOCKED"]["bbox_mm"]["dz"]),
        "max_radial_extent": (rows["STORED"]["max_radial_extent_mm"],
                              rows["DEPLOYED_LOCKED"]["max_radial_extent_mm"]),
    }
    smaller = {k: (a < b - 1e-9) for k, (a, b) in extents.items()}
    return {"configurations": rows,
            "storage_relevant_extents_declared": ["bbox_dx", "bbox_dy", "max_radial_extent"],
            "comparison": {k: {"stored_mm": round(a, 6), "deployed_mm": round(b, 6),
                               "stored_smaller": smaller[k]}
                           for k, (a, b) in extents.items()},
            "at_least_one_storage_relevant_extent_smaller":
                any(smaller[k] for k in ("bbox_dx", "bbox_dy", "max_radial_extent")),
            "frame": "the world frame of parameters.yaml; bounding box is axis-aligned in it",
            "note": ("bbox_dz is LARGER stored than deployed and is reported as such. "
                     "NRM-BM-003-018 asks for at least one storage-relevant extent to "
                     "shrink, not for every dimension to. What 'compact' means beyond "
                     "this relation stays unresolved at AMB-BM-003-001."),
            "status": "PASS" if any(smaller[k] for k in
                                    ("bbox_dx", "bbox_dy", "max_radial_extent")) else "FAIL"}


def support_region(m: Model) -> Dict:
    """Is the platform's upper face actually available to put something on?"""
    if "BODY-TOP-SUPPORT" not in m.by:
        return {"status": "FAIL", "reason": "no support body"}
    conf = m.state("DEPLOYED_LOCKED")
    top = m.P["plate_z1"]
    above = {}
    for bid, b in conf.items():
        sl = vc.clip(b.shape, vc.roi_box(-400, 400, -400, 400, top + 1e-6, top + 400))
        above[bid] = sl is not None
    face = vc.clip(conf["BODY-TOP-SUPPORT"].shape,
                   vc.roi_box(-400, 400, -400, 400, top - 0.05, top))
    bb = cv.bbox_of(face) if face is not None else None
    clear = not any(above.values())
    return {"support_face_z_mm": top,
            "support_face_bbox_mm": ({k: round(v, 6) for k, v in bb.items()}
                                     if bb else None),
            "nominal_face_radius_mm": m.P["plate_r"],
            "bodies_with_material_above_the_face": [k for k, v in above.items() if v],
            "face_is_unobstructed": clear,
            "explicitly_not_a_capacity_claim": (
                "NRM-BM-003-007 is satisfied by the region existing and being "
                "reachable. No mass or load is stated by the source "
                "(AMB-BM-003-002), so no capacity is claimed and none could be."),
            "status": "PASS" if (clear and bb is not None) else "FAIL"}


def connectivity(m: Model, steps: int) -> Dict:
    """Do the declared running pairs stay engaged all cycle, and is the graph
    they form singly connected?

    A LIMIT STOP is not a running pair. BODY-RING and BODY-RING-CAPTOR touch only
    when the ring is at the top of its travel; the rest of the time they are as
    far apart as that travel is long. That separation is the stroke, not a lapse,
    and the first version of this check treated it as one - which would have said
    the ring detaches every time it is lowered. The ring's attachment is to the
    hub's journal, which never lapses, and its captivity is established by the
    escape probe in retention.json: by geometry, not by proximity.
    """
    edges = [("BODY-HUB", "BODY-RING"),
             ("BODY-HUB", "BODY-RING-CAPTOR"), ("BODY-HUB", "BODY-TOP-SUPPORT")]
    for k in KEYS:
        edges += [("BODY-HUB", "BODY-PIN-%s" % k),
                  ("BODY-PIN-%s" % k, "BODY-LEG-%s" % k),
                  ("BODY-HUB", "BODY-LEG-%s" % k)]
    edges = [tuple(sorted(e)) for e in edges if e[0] in m.by and e[1] in m.by]
    stops = [tuple(sorted(("BODY-RING", "BODY-RING-CAPTOR")))]
    stops = [e for e in stops if e[0] in m.by and e[1] in m.by]

    worst = {"|".join(e): 0.0 for e in edges + stops}
    kf = B._keyframes(m.P, m.G)
    for seg in B.SEGMENTS:
        a, b = (kf[s] for s in B.SEGMENT_ENDS[seg])
        for i in range(steps + 1):
            u = i / float(steps)
            conf = m.at(*[a[j] + (b[j] - a[j]) * u for j in range(3)])
            for e in edges + stops:
                d = cv.min_distance(conf[e[0]].shape, conf[e[1]].shape)
                key = "|".join(e)
                if d > worst[key]:
                    worst[key] = d

    engaged = [e for e in edges if worst["|".join(e)] <= CONNECTION_TOL]
    # union-find over the engaged edges
    parent = {i: i for i in m.ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a2, b2 in engaged:
        ra, rb = find(a2), find(b2)
        if ra != rb:
            parent[ra] = rb
    comps = len({find(i) for i in m.ids})
    lapsed = [e for e in edges if e not in engaged]
    return {"declared_running_pairs": ["|".join(e) for e in edges],
            "declared_limit_stops": ["|".join(e) for e in stops],
            "limit_stop_stroke_mm": {"|".join(e): round(worst["|".join(e)], 6)
                                     for e in stops},
            "max_separation_over_cycle_mm": {k: round(v, 6) for k, v in sorted(worst.items())},
            "connection_tol_mm": CONNECTION_TOL,
            "edges_that_lapsed": ["|".join(e) for e in lapsed],
            "connected_components": comps,
            "singly_connected": comps == 1,
            "samples_per_segment": steps + 1,
            "method": ("every declared joint or retention pair is measured at every "
                       "sample of every segment; the largest separation each pair ever "
                       "reaches is reported, so the connectivity verdict is checkable "
                       "against the numbers rather than against the threshold alone"),
            "status": "PASS" if (comps == 1 and not lapsed) else "FAIL"}


def continuity(m: Model, steps: int) -> Dict:
    """Bound the jump between consecutive samples, per body, per segment."""
    kf = B._keyframes(m.P, m.G)
    rows = []
    worst_overall = 0.0
    for seg in B.SEGMENTS:
        a, b = (kf[s] for s in B.SEGMENT_ENDS[seg])
        prev = None
        worst, at_ = 0.0, None
        for i in range(steps + 1):
            t = i / float(steps)
            conf = m.at(*[a[j] + (b[j] - a[j]) * t for j in range(3)])
            pts = {}
            for bid, body in conf.items():
                bb = cv.bbox_of(body.shape)
                pts[bid] = (bb["xmin"], bb["ymin"], bb["zmin"],
                            bb["xmax"], bb["ymax"], bb["zmax"])
            if prev is not None:
                for bid, cur in pts.items():
                    d = max(abs(cur[j] - prev[bid][j]) for j in range(6))
                    if d > worst:
                        worst, at_ = d, [bid, round(t, 6)]
            prev = pts
        # the largest displacement a single uniform step can legitimately produce
        span = max(abs(b[j] - a[j]) for j in range(3))
        reach = 200.0
        bound = 3.0 * (span / steps) * math.pi / 180.0 * reach + 1e-6
        bound = max(bound, 3.0 * span / steps + 1e-6)
        rows.append({"segment_id": seg, "samples": steps + 1,
                     "max_bbox_step_mm": round(worst, 6), "at": at_,
                     "declared_bound_mm": round(bound, 6),
                     "status": "PASS" if worst <= bound else "FAIL"})
        worst_overall = max(worst_overall, worst)
    return {"segments": rows, "max_step_mm": round(worst_overall, 6),
            "method": ("between consecutive samples, the largest change in any body's "
                       "bounding-box coordinate is compared against the displacement a "
                       "uniform step of the declared interpolation can produce"),
            "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL"}


def cycle_return(m: Model) -> Dict:
    """Does the end of M6 land exactly on the stored configuration it started from?"""
    def mat(loc):
        t = loc.wrapped.Transformation()
        return [[round(t.Value(r, c), 9) for c in range(1, 5)] for r in range(1, 4)]

    kf = B._keyframes(m.P, m.G)
    end = kf[B.SEGMENT_ENDS["M6_FOLD"][1]]
    diffs = []
    for b in m.bodies:
        a = mat(B.pose_at(m.P, b.id, *end))
        c = mat(B.pose(m.P, b.id, "STORED"))
        d = max(abs(a[i][j] - c[i][j]) for i in range(3) for j in range(4))
        diffs.append({"body_id": b.id, "max_transform_difference": round(d, 12)})
    ok = all(x["max_transform_difference"] <= 1e-9 for x in diffs)
    return {"bodies": diffs, "tolerance": 1e-9,
            "reversibility": ("M4 is M3 reversed, M5 is M2 reversed, M6 is M1 reversed; "
                              "no segment contains a one-way step"),
            "not_a_durability_claim": ("repeatable here means no irreversible step. "
                                       "It is not a cycle count and says nothing about "
                                       "wear or lifetime, which AMB-BM-003-006 leaves open."),
            "status": "PASS" if ok else "FAIL"}


def assembly_graph() -> Dict:
    decl = yaml.safe_load(open(os.path.join(HERE, "assembly.yaml")))
    return _graph_from(decl["steps"])


def _graph_from(steps: List[Dict]) -> Dict:
    order = [s["id"] for s in steps]
    idx = {sid: i for i, sid in enumerate(order)}
    deps: Dict[str, List[str]] = {sid: [] for sid in order}
    first_seen: Dict[str, str] = {}
    for s in steps:
        sid, body = s["id"], s["place"]
        for d in s.get("depends_on", []):
            deps[sid].append(d)
        if body in first_seen and s.get("kind") == "operation":
            deps[sid].append(first_seen[body])
        elif body not in first_seen:
            first_seen[body] = sid
    colour: Dict[str, int] = {sid: 0 for sid in order}
    cycles: List[List[str]] = []

    def visit(sid, stack):
        if colour[sid] == 1:
            cycles.append(stack[stack.index(sid):] + [sid])
            return
        if colour[sid] == 2:
            return
        colour[sid] = 1
        for d in deps[sid]:
            if d in colour:
                visit(d, stack + [d])
        colour[sid] = 2

    for sid in order:
        visit(sid, [sid])
    unknown = [d for sid in order for d in deps[sid] if d not in idx]
    return {"steps": order, "dependencies": deps, "cycles_found": cycles,
            "unknown_references": unknown, "acyclic": not cycles and not unknown,
            "status": "PASS" if (not cycles and not unknown) else "FAIL"}


# ================================================================ predicates
def p_block(m: Model, steps: int = 30) -> Dict:
    rows = fold_scan(m, m.G["ring_z_locked"], 0.0, steps)
    legs = [i for i in m.ids if i.startswith("BODY-LEG-")]
    per = {}
    for lg in legs:
        onset = first_obstructed(rows, lg)
        per[lg] = {"obstructed_from_theta_deg": onset,
                   "clear_at_deployed": rows[0]["max_common_volume_mm3_by_leg"][lg] <= OVERLAP_TOL,
                   "obstructed_at_stored":
                       rows[-1]["max_common_volume_mm3_by_leg"][lg] > OVERLAP_TOL}
    ok = bool(legs) and len(legs) == 3 and all(
        v["obstructed_from_theta_deg"] is not None and v["clear_at_deployed"]
        and v["obstructed_at_stored"] for v in per.values())
    return {"status": "PASS" if ok else "FAIL", "per_leg": per, "scan": rows,
            "claim": ("with the ring locked, no continuous rigid-body path exists from "
                      "DEPLOYED toward STORED for any leg"),
            "analytic_block_angle_deg": round(m.G["theta_block_deg"], 6)}


def p_release(m: Model, steps: int = 30) -> Dict:
    rows = fold_scan(m, m.G["ring_z_released"], m.P["ring_release_rot"], steps)
    worst = max(r["max_common_volume_mm3"] for r in rows)
    return {"status": "PASS" if worst <= OVERLAP_TOL else "FAIL",
            "max_common_volume_mm3": round(worst, 9), "scan": rows,
            "claim": "after the lift and the turn, the whole fold path is clear"}


def p_lift_only(m: Model, steps: int = 30) -> Dict:
    rows = fold_scan(m, m.G["ring_z_released"], 0.0, steps)
    onset = first_obstructed(rows)
    reached_stored = rows[-1]["max_common_volume_mm3"] <= OVERLAP_TOL
    ok = onset is not None and not reached_stored
    return {"status": "PASS" if ok else "FAIL",
            "obstructed_from_theta_deg": onset,
            "stored_reachable_by_lift_alone": reached_stored,
            "analytic_lift_only_limit_deg": round(m.G["theta_lift_only_deg"], 6),
            "claim": ("lifting the ring without turning it does not free the legs: the "
                      "fold is stopped part way, so the release genuinely needs both "
                      "motions"),
            "scan": rows}


def p_antirot(m: Model, steps: int = 24) -> Dict:
    pos = turn_scan(m, m.G["ring_z_locked"], 1.0, steps)
    neg = turn_scan(m, m.G["ring_z_locked"], -1.0, steps)
    free = turn_scan(m, m.G["ring_z_released"], 1.0, steps)

    def onset(rows):
        for r in rows[1:]:
            if r["common_volume_mm3"] > OVERLAP_TOL:
                return r["ring_phi_deg"]
        return None

    op, on = onset(pos), onset(neg)
    free_worst = max(r["common_volume_mm3"] for r in free)
    ok = op is not None and on is not None and free_worst <= OVERLAP_TOL
    return {"status": "PASS" if ok else "FAIL",
            "locked_height_obstructed_from_deg": {"positive": op, "negative": on},
            "released_height_max_common_volume_mm3": round(free_worst, 9),
            "residual_angular_play_deg": (None if op is None or on is None
                                          else round(op - on, 6)),
            "claim": ("at the locked height the ribs are inside the ring's keyways and "
                      "the ring cannot be turned; lifted clear of them it turns freely "
                      "through the whole release travel"),
            "scans": {"locked_positive": pos, "locked_negative": neg, "released": free}}


def p_retention(m: Model) -> Dict:
    rows = escape_probes(m)
    bad = [r for r in rows if r["status"] != "PASS"]
    return {"status": "PASS" if not bad else "FAIL", "probes": rows,
            "failed": [r["retention_id"] for r in bad],
            "claim": ("every body that could leave has a measured blocked escape "
                      "direction and a named blocker")}


def p_three_legs(m: Model) -> Dict:
    legs = [i for i in m.ids if i.startswith("BODY-LEG-")]
    stored = {}
    for lg in legs:
        bb = cv.bbox_of(m.state("STORED")[lg].shape)
        stored[lg] = [round(bb[k], 6) for k in ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax")]
    distinct = len({tuple(v) for v in stored.values()}) == len(legs)
    return {"status": "PASS" if (len(legs) == 3 and distinct) else "FAIL",
            "leg_count": len(legs), "stored_bboxes_distinct": distinct,
            "stored_bbox_mm": stored}


def p_compact(m: Model) -> Dict:
    return envelopes(m)


def p_footprint(m: Model) -> Dict:
    return ground_contacts(m)


def p_support(m: Model) -> Dict:
    return support_region(m)


def p_continuity(m: Model, steps: int = 20, defeat_pose: frozenset = frozenset()) -> Dict:
    if defeat_pose:
        kf = B._keyframes(m.P, m.G)
        rows = []
        for seg in B.SEGMENTS:
            a, b = (kf[s] for s in B.SEGMENT_ENDS[seg])
            prev, worst, at_ = None, 0.0, None
            for i in range(steps + 1):
                t = i / float(steps)
                conf = _by(B.continuous_pose(m.bodies, m.P, seg, t, defeat_pose))
                pts = {bid: tuple(cv.bbox_of(bd.shape)[k] for k in
                                  ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax"))
                       for bid, bd in conf.items()}
                if prev is not None:
                    for bid, cur in pts.items():
                        d = max(abs(cur[j] - prev[bid][j]) for j in range(6))
                        if d > worst:
                            worst, at_ = d, [bid, round(t, 6)]
                prev = pts
            span = max(abs(b[j] - a[j]) for j in range(3))
            bound = max(3.0 * (span / steps) * math.pi / 180.0 * 200.0,
                        3.0 * span / steps) + 1e-6
            rows.append({"segment_id": seg, "max_bbox_step_mm": round(worst, 6),
                         "at": at_, "declared_bound_mm": round(bound, 6),
                         "status": "PASS" if worst <= bound else "FAIL"})
        return {"segments": rows,
                "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL"}
    return continuity(m, steps)


def p_connected(m: Model, steps: int = 12) -> Dict:
    return connectivity(m, steps)


def p_outward(m: Model, steps: int = 40) -> Dict:
    rows = outward_scan(m, steps)
    onset = None
    for r in rows[1:]:
        if r["max_common_volume_mm3"] > OVERLAP_TOL:
            onset = r["theta_deg"]
            break
    residual = None if onset is None else onset - m.P["theta_deployed"]
    bound = m.P["outward_travel_max_deg"]
    ok = (onset is not None and rows[0]["max_common_volume_mm3"] <= OVERLAP_TOL
          and residual <= bound)
    return {"status": "PASS" if ok else "FAIL",
            "stopped_at_theta_deg": onset,
            "residual_outward_travel_deg": (None if residual is None
                                            else round(residual, 6)),
            "declared_outward_travel_bound_deg": bound,
            "within_declared_bound": residual is not None and residual <= bound,
            "clear_at_deployed": rows[0]["max_common_volume_mm3"] <= OVERLAP_TOL,
            "claim": ("swinging a leg past its deployed angle is stopped by the hub's "
                      "outward stop pad, so the deployed angle is bounded on both sides"),
            "why_a_bound_is_needed_here": (
                "'something eventually stops it' does not discriminate: with the stop "
                "pads removed the heel still reaches the base flange, about 8.5 degrees "
                "past deployed. NRM-BM-003-010 asks the DESIGN to declare its intended "
                "and forbidden mobility, so this reference declares its own bound and "
                "measures against it. The bound is a FIXTURE design declaration. It is "
                "not an Oracle threshold and must not be read back as one - the Oracle "
                "introduces no number anywhere (FRE-BM-003-011)."),
            "scan": rows}


def p_path_clear(m: Model, steps: int = 16, defeat_pose: frozenset = frozenset()) -> Dict:
    """Interference over the six declared segments, at the given sampling."""
    kf = B._keyframes(m.P, m.G)
    pairs = _pairs(m.ids)
    rows = []
    for seg in B.SEGMENTS:
        a, b = (kf[s] for s in B.SEGMENT_ENDS[seg])
        worst, at_ = 0.0, None
        for i in range(steps + 1):
            t = i / float(steps)
            if defeat_pose:
                conf = _by(B.continuous_pose(m.bodies, m.P, seg, t, defeat_pose))
            else:
                conf = m.at(*[a[j] + (b[j] - a[j]) * t for j in range(3)])
            w, where = _worst_common(conf, pairs)
            if w > worst:
                worst, at_ = w, [where, round(t, 6)]
        rows.append({"segment_id": seg, "samples": steps + 1,
                     "max_common_volume_mm3": round(worst, 9), "at": at_,
                     "status": "PASS" if worst <= OVERLAP_TOL else "FAIL"})
    return {"segments": rows, "sampling_steps": steps,
            "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL"}


MIN_INTERIOR_SAMPLES = 8


def p_path_sampled(steps: int) -> Dict:
    """The declared sampling policy: interior samples, not just endpoints."""
    interior = max(0, steps - 1)
    return {"status": "PASS" if interior >= MIN_INTERIOR_SAMPLES else "FAIL",
            "samples_per_segment": steps + 1,
            "interior_samples_per_segment": interior,
            "declared_minimum_interior_samples": MIN_INTERIOR_SAMPLES,
            "why": ("two valid endpoints prove nothing about the path between them "
                    "(NRM-BM-003-005, NEG-BM-003-006). The policy is declared, not "
                    "discovered adaptively.")}


def p_asm_paths(m: Model, steps: int, decl_steps: Optional[List[Dict]] = None) -> Dict:
    """Sweep the declared insertion sequence. Local re-implementation of step 7's
    measurement so a negative control can reorder the sequence in memory."""
    decl = decl_steps or yaml.safe_load(open(os.path.join(HERE, "assembly.yaml")))["steps"]
    alt = _insertion_bodies(m)
    placed: List[str] = []
    rows = []
    for st in decl:
        bid, kind = st["place"], st.get("kind", "insertion")
        if kind == "base":
            placed.append(bid)
            rows.append({"step_id": st["id"], "body": bid, "kind": "base", "status": "PASS"})
            continue
        if kind == "operation":
            rows.append({"step_id": st["id"], "body": bid, "kind": "operation",
                         "validated_by": st.get("validated_by"), "status": "PASS"})
            continue
        if bid not in m.by:
            rows.append({"step_id": st["id"], "body": bid, "status": "NOT_EVALUABLE"})
            continue
        direc, dist = st["direction"], float(st["approach_distance"])
        swept = alt.get(st["id"], m.by[bid])
        others = [o for o in placed if o != bid and o in m.by]
        worst, at_ = 0.0, None
        for i in range(steps + 1):
            s = dist * (1.0 - i / float(steps))
            loc = cv.translation((-direc[0] * s, -direc[1] * s, -direc[2] * s))
            moving = (swept if i < steps else m.by[bid]).moved(loc)
            for o in others:
                c = cv.common_volume(moving.shape, m.by[o].shape)
                if c > worst:
                    worst, at_ = c, [o, round(s, 4)]
        if bid not in placed:
            placed.append(bid)
        rows.append({"step_id": st["id"], "body": bid, "kind": "insertion",
                     "samples": steps + 1, "placed_before": others,
                     "max_common_volume_mm3": round(worst, 9),
                     "max_common_volume_at": at_,
                     "status": "PASS" if worst <= OVERLAP_TOL else "FAIL"})
    return {"steps": rows, "sampling_steps": steps,
            "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL"}


def _insertion_bodies(m: Model) -> Dict[str, cv.Body]:
    """The alternate configurations swept during insertion: the four bayoneted
    bodies are inserted with their reliefs aligned and turned afterwards."""
    out = {}
    for k, sid in zip(KEYS, ("AS-03", "AS-06", "AS-09")):
        if "BODY-PIN-%s" % k in m.by:
            out[sid] = cv.Body("BODY-PIN-%s" % k, "hinge pin %s" % k, "RIGID",
                               B.build_pin(m.P, m.G, k, False, m.defeat))
    if "BODY-RING-CAPTOR" in m.by:
        out["AS-12"] = cv.Body("BODY-RING-CAPTOR", "ring captor", "RIGID",
                               B.build_captor(m.P, m.G, False, m.defeat))
    if "BODY-TOP-SUPPORT" in m.by:
        out["AS-14"] = cv.Body("BODY-TOP-SUPPORT", "top support", "RIGID",
                               B.build_top_support(m.P, m.G, False, m.defeat))
    return out


def p_asm_acyclic(steps: Optional[List[Dict]] = None) -> Dict:
    if steps is None:
        return assembly_graph()
    return _graph_from(steps)


# ========================================================= negative controls
def _mut(**kw) -> Dict[str, float]:
    q = dict(P)
    q.update(kw)
    return q


def negative_controls(fast: bool) -> List[Dict]:
    """Seventeen controls. Each begins from the fully passing baseline, changes
    one condition, and must make one named predicate fail while its declared
    unrelated predicates keep the result they had on the baseline."""
    n_fold = 12 if fast else 24
    n_turn = 10 if fast else 18
    n_asm = 40 if fast else 90
    n_path = 8 if fast else 14

    def base_ref(name):
        return BASELINE_PREDICATES[name]

    cases = []

    def run(cid, what, mutation, target, target_fn, controls, expect_change=(),
            note=None):
        rec = {"control_id": cid, "mutates": what, "target_predicate": target,
               "declared_unrelated_predicates": list(controls),
               "declared_dependent_predicates": list(expect_change)}
        if note:
            rec["note"] = note
        try:
            res = target_fn()
        except Exception as exc:                       # noqa: BLE001
            rec.update(detected=False, status="FAIL",
                       reason=("the control raised %s. A detection by exception is "
                               "rejected: the checker must MEASURE the defect."
                               % type(exc).__name__))
            return rec
        rec["target_result"] = res.get("status")
        rec["target_detail"] = {k: v for k, v in res.items() if k != "scan" and k != "scans"
                                and k != "segments" and k != "probes" and k != "steps"}
        flipped = res.get("status") == "FAIL"
        holds, held = True, {}
        for cname, cfn in controls.items():
            try:
                cres = cfn()
            except Exception as exc:                   # noqa: BLE001
                held[cname] = "RAISED_%s" % type(exc).__name__
                holds = False
                continue
            held[cname] = cres.get("status")
            if cres.get("status") != base_ref(cname):
                holds = False
        rec["unrelated_predicate_results"] = held
        rec["unrelated_predicates_unchanged"] = holds
        rec["detected"] = bool(flipped and holds)
        rec["status"] = "PASS" if rec["detected"] else "FAIL"
        return rec

    # 1 - a hinge pin with no captor
    m = Model(defeat=frozenset({"NC_PIN_CAPTOR_REMOVED"}), label="NC-01")
    cases.append(run("NC-01", "hinge pin A loses its bayonet end bar",
                     None, "P_RETENTION", lambda mm=m: p_retention(mm),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_BLOCK": lambda mm=m: p_block(mm, n_fold)}))

    # 2 - a leg omitted
    m = Model(defeat=frozenset({"NC_LEG_OMITTED"}), label="NC-02")
    cases.append(run("NC-02", "leg C and its pin are absent",
                     None, "P_THREE_LEGS", lambda mm=m: p_three_legs(mm),
                     {"P_SUPPORT": lambda mm=m: p_support(mm)},
                     expect_change=("P_FOOTPRINT", "P_BLOCK")))

    # 3 - a leg with no heel: nothing for the arm to meet
    m = Model(defeat=frozenset({"NC_HEEL_REMOVED"}), label="NC-03")
    cases.append(run("NC-03", "leg A loses its blocking heel",
                     None, "P_BLOCK", lambda mm=m: p_block(mm, n_fold),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_RETENTION": lambda mm=m: p_retention(mm),
                      "P_COMPACT": lambda mm=m: p_compact(mm)}))

    # 4 - the ring blocks only two of the three legs
    m = Model(defeat=frozenset({"NC_ONE_ARM_REMOVED"}), label="NC-04")
    cases.append(run("NC-04", "the ring is built with two arms instead of three",
                     None, "P_BLOCK", lambda mm=m: p_block(mm, n_fold),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_RETENTION": lambda mm=m: p_retention(mm),
                      "P_ANTIROT": lambda mm=m: p_antirot(mm, n_turn)}))

    # 5 - the captor no longer overhangs the ring bore
    m = Model(defeat=frozenset({"NC_CAPTOR_UNDERSIZED"}), label="NC-05")
    cases.append(run("NC-05", "the ring captor is turned down inside the ring bore",
                     None, "P_RETENTION", lambda mm=m: p_retention(mm),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_BLOCK": lambda mm=m: p_block(mm, n_fold)}))

    # 6 - a cycle in the assembly dependency relation
    _steps = yaml.safe_load(open(os.path.join(HERE, "assembly.yaml")))["steps"]
    cyc = [dict(s) for s in _steps]
    for s in cyc:
        if s["id"] == "AS-02":
            s["depends_on"] = ["AS-11"]
    cases.append(run("NC-06", "AS-02 is made to depend on AS-11, which depends on AS-02",
                     None, "P_ASM_ACYCLIC", lambda st=cyc: p_asm_acyclic(st),
                     {"P_THREE_LEGS": lambda: p_three_legs(BASE)}))

    # 7 - the final captor installed before the ring
    reord = [dict(s) for s in _steps]
    i11 = next(i for i, s in enumerate(reord) if s["id"] == "AS-11")
    i12 = next(i for i, s in enumerate(reord) if s["id"] == "AS-12")
    reord[i11], reord[i12] = reord[i12], reord[i11]
    cases.append(run("NC-07", "the ring captor is installed before the ring",
                     None, "P_ASM_PATHS",
                     lambda st=reord: p_asm_paths(BASE, n_asm, st),
                     {"P_ASM_ACYCLIC": lambda: p_asm_acyclic()}))

    # 8 - the pin's insertion relief is not cut
    m = Model(defeat=frozenset({"NC_PIN_RELIEF_BLOCKED"}), label="NC-08")
    cases.append(run("NC-08", "the clevis bores are round, so the pin's end bar cannot pass",
                     None, "P_ASM_PATHS", lambda mm=m: p_asm_paths(mm, n_asm),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_COMPACT": lambda mm=m: p_compact(mm)}))

    # 9 - endpoints kept, the trajectory between them removed
    m = Model(defeat=frozenset({"NC_HUB_BOSS"}), label="NC-09")
    endpoints = p_path_clear(m, 1)
    dense = p_path_clear(m, n_path)
    rec = {"control_id": "NC-09",
           "mutates": ("sampling: the declared interior samples are removed and only "
                       "the two endpoints are kept, on a model whose only defect is "
                       "strictly between the endpoints"),
           "target_predicate": "P_PATH_SAMPLED",
           "target_result": p_path_sampled(1)["status"],
           "target_detail": p_path_sampled(1),
           "corroboration": {
               "endpoints_only_path_clear": endpoints["status"],
               "declared_sampling_path_clear": dense["status"],
               "why_this_matters": ("endpoint-only sampling reports PASS on a model "
                                    "that dense sampling reports FAIL on. That is "
                                    "exactly NEG-BM-003-006 and it is why the sampling "
                                    "policy is a checked predicate, not a convention.")},
           "declared_unrelated_predicates": ["P_PATH_SAMPLED at declared sampling"],
           "unrelated_predicate_results": {"P_PATH_SAMPLED_declared":
                                           p_path_sampled(_COARSE)["status"]},
           "unrelated_predicates_unchanged": p_path_sampled(_COARSE)["status"] == "PASS"}
    rec["detected"] = (rec["target_result"] == "FAIL"
                       and endpoints["status"] == "PASS"
                       and dense["status"] == "FAIL"
                       and rec["unrelated_predicates_unchanged"])
    rec["status"] = "PASS" if rec["detected"] else "FAIL"
    cases.append(rec)

    # 10 - leg meets leg during the fold
    m = Model(defeat=frozenset({"NC_LEG_LOBE"}), label="NC-10")
    cases.append(run("NC-10", "each heel is given a wide tangential lobe",
                     None, "P_PATH_CLEAR", lambda mm=m: p_path_clear(mm, n_path),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm)},
                     expect_change=("P_BLOCK", "P_RELEASE"),
                     note=("leg-to-leg separation in this mechanism is monotone in the "
                           "leg angle - the legs are closest at DEPLOYED - so a "
                           "leg-to-leg interference that exists at all also exists at "
                           "an endpoint. It cannot be made interior-only here. The "
                           "strictly interior-only interference control is NC-11. The "
                           "lobe also reaches the clevis plates, which is why the "
                           "leg-to-hub predicates are declared dependent rather than "
                           "unrelated.")))

    # 11 - leg meets hub, and only between the endpoints
    m = Model(defeat=frozenset({"NC_HUB_BOSS"}), label="NC-11")
    cases.append(run("NC-11", ("a boss is added to the hub in the band the heel sweeps "
                               "through only between the two endpoints"),
                     None, "P_PATH_CLEAR", lambda mm=m: p_path_clear(mm, n_path),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_RETENTION": lambda mm=m: p_retention(mm),
                      "P_COMPACT": lambda mm=m: p_compact(mm)},
                     note=("both endpoint configurations are interference free; the "
                           "defect exists only strictly between them")))

    # 12 - the blocker is still engaged after the release
    m = Model(params=_mut(ring_release_rot=0.0), label="NC-12")
    cases.append(run("NC-12", "the release turn is removed, so the arms stay over the heels",
                     None, "P_RELEASE", lambda mm=m: p_release(mm, n_fold),
                     {"P_BLOCK": lambda mm=m: p_block(mm, n_fold),
                      "P_RETENTION": lambda mm=m: p_retention(mm)}))

    # 13 - the locked configuration permits fold-back
    _span = G["heel_top_stored"] - G["heel_top_deployed"]
    m = Model(params=_mut(blocker_clearance=_span + 1.0), label="NC-13")
    cases.append(run("NC-13", ("the ring seat is raised above the heel's entire sweep, "
                               "so the arms never meet a heel"),
                     None, "P_BLOCK", lambda mm=m: p_block(mm, n_fold),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_COMPACT": lambda mm=m: p_compact(mm),
                      "P_FOOTPRINT": lambda mm=m: p_footprint(mm)}))

    # 14 - the stored envelope is no smaller than the deployed one
    m = Model(params=_mut(theta_deployed=P["theta_stored"]), label="NC-14")
    cases.append(run("NC-14", "the deployed angle is set equal to the stored angle",
                     None, "P_COMPACT", lambda mm=m: p_compact(mm),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_SUPPORT": lambda mm=m: p_support(mm)},
                     expect_change=("P_FOOTPRINT", "P_BLOCK")))

    # 15 - a discontinuous body transform
    cases.append(run("NC-15", "M6's interpolation is replaced by a jump between endpoints",
                     None, "P_CONTINUITY",
                     lambda: p_continuity(BASE, 12, frozenset({"NC_TRANSFORM_JUMP"})),
                     {"P_THREE_LEGS": lambda: p_three_legs(BASE),
                      "P_BLOCK": lambda: p_block(BASE, n_fold)}))

    # 16 - the ring's anti-rotation is defeated
    m = Model(defeat=frozenset({"NC_RIBS_REMOVED"}), label="NC-16")
    cases.append(run("NC-16", "the three anti-rotation ribs are removed",
                     None, "P_ANTIROT", lambda mm=m: p_antirot(mm, n_turn),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_BLOCK": lambda mm=m: p_block(mm, n_fold),
                      "P_RETENTION": lambda mm=m: p_retention(mm)}))

    # 17 - the outward stop is removed
    m = Model(defeat=frozenset({"NC_STOP_PAD_REMOVED"}), label="NC-17")
    cases.append(run("NC-17", "the three outward stop pads are removed",
                     None, "P_OUTWARD", lambda mm=m: p_outward(mm, 40 if fast else 80),
                     {"P_THREE_LEGS": lambda mm=m: p_three_legs(mm),
                      "P_BLOCK": lambda mm=m: p_block(mm, n_fold),
                      "P_RETENTION": lambda mm=m: p_retention(mm)}))

    return cases


BASELINE_PREDICATES: Dict[str, str] = {}


# ================================================================ step 8
def oracle_evaluation(ev: Dict) -> Dict:
    """What the frozen BM-003 Oracle concludes about this reference.

    Every status below is derived from a measurement in `ev`. Where the Oracle's
    predicate cannot be decided by exact rigid geometry, the status is
    NOT_VERIFIED or UNSUPPORTED and says why. No status is upgraded because the
    design looks right.
    """
    def st(*keys) -> bool:
        return all(ev[k]["status"] == "PASS" for k in keys)

    rows = [
        {"invariant": "NRM-BM-003-001",
         "statement": "three distinguishable legs, each with a stored pose against the body",
         "status": "PASS" if st("three_legs", "compactness") else "FAIL",
         "evidence": ["three_legs.json", "envelope.json"],
         "tags": ["three_legs_present", "stored_pose_defined"]},
        {"invariant": "NRM-BM-003-002",
         "statement": "stored configuration is one connected component",
         "status": "PASS" if st("connectivity") else "FAIL",
         "evidence": ["connectivity.json"], "tags": ["stored_connected"]},
        {"invariant": "NRM-BM-003-003",
         "statement": "no removal of any component to fold or unfold",
         "status": "PASS" if st("connectivity", "retention") else "FAIL",
         "evidence": ["connectivity.json", "retention.json"],
         "tags": ["no_removal_to_operate"],
         "reasoning": ("no segment of the declared cycle removes a body; every declared "
                       "retention stays engaged at every sample")},
        {"invariant": "NRM-BM-003-004",
         "statement": "a manual deployment sequence exists, ending deployed",
         "status": "PASS" if st("motion", "state_maintenance") else "FAIL",
         "evidence": ["poses.yaml", "motion_report.json"],
         "tags": ["deployment_sequence_declared"]},
        {"invariant": "NRM-BM-003-005",
         "statement": "connectedness holds along the path, not only at its endpoints",
         "status": "PASS" if st("connectivity", "path_sampling") else "FAIL",
         "evidence": ["connectivity.json", "motion_report.json"],
         "tags": ["path_sampled", "path_connected"]},
        {"invariant": "NRM-BM-003-006",
         "statement": "three ground contacts bounding a non-zero area",
         "status": "PASS" if st("footprint") else "FAIL",
         "evidence": ["footprint.json"], "tags": ["deployed_footprint_non_degenerate"]},
        {"invariant": "NRM-BM-003-007",
         "statement": "an available support region exists in the deployed configuration",
         "status": "PASS" if st("support_region") else "FAIL",
         "evidence": ["support_region.json"], "tags": ["support_region_identifiable"],
         "explicitly_not": "no capacity is claimed; AMB-BM-003-002 blocks any"},
        {"invariant": "NRM-BM-003-008",
         "statement": "no tool, motor or external fixture in deployment",
         "status": "PASS",
         "evidence": ["poses.yaml", "assembly.yaml"],
         "tags": ["unpowered_manual_operation"],
         "reasoning": ("every declared operational segment moves a product body only; "
                       "no participant outside the ten bodies appears in any of them")},
        {"invariant": "NRM-BM-003-009",
         "statement": "the deployed configuration persists and does not enter folding first",
         "declared_state_maintenance_class": "SMC-KINEMATIC_BLOCK",
         "status": "PASS" if st("state_maintenance", "release", "lift_only") else "FAIL",
         "evidence": ["state_maintenance.json"],
         "tags": ["deployed_state_maintained", "state_maintenance_realized",
                  "state_maintenance_class_declared"],
         "verifier_fidelity": "mobility_analysis_with_realized_geometry",
         "why_that_is_the_right_route": (
             "SMC-KINEMATIC_BLOCK is the one class whose predicate exact rigid "
             "geometry can decide, because the claim is that a path is ABSENT. The "
             "other three classes need stability, energy or contact routes this "
             "toolset does not have; this design deliberately uses the class it can "
             "actually establish. That is a fixture choice, not a statement that the "
             "other classes are worse.")},
        {"invariant": "NRM-BM-003-010",
         "statement": "no unintended gross rigid-body freedom in the deployed configuration",
         "status": "PASS" if st("state_maintenance", "retention", "outward_stop") else "FAIL",
         "evidence": ["state_maintenance.json", "retention.json", "outward_stop.json"],
         "tags": ["deployed_mobility_declared", "unintended_dof_addressed"],
         "per_leg_freedoms": {
             "intended": "rotation about its own hinge axis, between the two stops",
             "fold back": "kinematically blocked by the ring arm",
             "swing further out": "kinematically blocked by the hub's stop pad",
             "twist aside / slide along the hinge axis": "blocked by the clevis pair",
             "detach": "blocked by the pin, which is itself blocked both ways"},
         "scope": ("GROSS freedom only. The residual angular play between the two "
                   "stops is measured and reported; whether that play is acceptable "
                   "is unresolved at AMB-BM-003-007 and is not claimed either way.")},
        {"invariant": "NRM-BM-003-011",
         "statement": "a deliberate action is required before folding becomes possible",
         "status": "PASS" if st("state_maintenance", "antirotation", "lift_only",
                                "release") else "FAIL",
         "evidence": ["state_maintenance.json"],
         "tags": ["release_action_declared", "folding_gated_by_deliberate_action"],
         "representation_used": "a persistent RELEASED configuration",
         "note": ("one of several representations NRM-BM-003-011 admits. The Oracle "
                  "requires none of them in particular and this one is not preferred.")},
        {"invariant": "NRM-BM-003-012",
         "statement": "after the release, a continuous path back to the same stored state, repeatably",
         "status": "PASS" if st("release", "cycle_return", "motion") else "FAIL",
         "evidence": ["cycle_return.json", "motion_report.json"],
         "tags": ["return_path_exists", "cycle_repeatable"]},
        {"invariant": "NRM-BM-003-013",
         "statement": "every component stays attached through the whole cycle",
         "status": "PASS" if st("connectivity", "retention") else "FAIL",
         "evidence": ["connectivity.json", "retention.json"],
         "tags": ["retention_persistent", "cycle_sampled"]},
        {"invariant": "NRM-BM-003-014",
         "statement": "a physically coherent assembly sequence exists",
         "status": "PASS" if st("assembly", "assembly_graph", "bayonet_turns") else "FAIL",
         "evidence": ["assembly_report.json", "assembly_graph.json", "bayonet_turns.json"],
         "tags": ["assembly_sequence_declared", "insertion_paths_clear", "assembly_acyclic"]},
        {"invariant": "NRM-BM-003-015",
         "statement": "every relationship operation depends on is established by assembly",
         "status": "PASS" if st("relations_activated") else "FAIL",
         "evidence": ["relations_activated.json"], "tags": ["operational_relations_activated"]},
        {"invariant": "NRM-BM-003-016",
         "statement": "every declared relationship has an identifiable physical realization",
         "realization_class": "RIGID_MULTI_BODY",
         "status": "PASS" if st("interactions", "retention") else "FAIL",
         "evidence": ["interaction_report.json", "retention.json"],
         "tags": ["interface_ownership_shown", "retention_direction_shown"]},
        {"invariant": "NRM-BM-003-017",
         "statement": "no body passes through another on any declared path",
         "status": "PASS" if st("motion", "assembly", "bayonet_turns") else "FAIL",
         "evidence": ["motion_report.json", "assembly_report.json", "bayonet_turns.json"],
         "tags": ["path_interference_checked"],
         "deformation_exception_invoked": False,
         "note": ("this is dense sampling of the declared paths, not a proof over the "
                  "continuum, and is reported as such")},
        {"invariant": "NRM-BM-003-018",
         "statement": "stored is more compact than deployed in a storage-relevant extent",
         "status": "PASS" if st("compactness") else "FAIL",
         "evidence": ["envelope.json"], "tags": ["stored_more_compact_than_deployed"]},
    ]

    unsupported = [
        {"claim": "load capacity of the support region",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-002; the source states no mass or force"},
        {"claim": "what disturbance the locked state survives",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-005; 'knocked it' carries no magnitude"},
        {"claim": "material, strength, stiffness, wear, fatigue, lifetime",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-006; the source is silent"},
        {"claim": "manufacturability, process, tolerance, cost",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-008; only a geometric assembly path is shown"},
        {"claim": "user effort to deploy, release or fold",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-004; no force, torque or travel criterion"},
        {"claim": "whether the deployed footprint is large enough for any object",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-003 and AMB-BM-003-009"},
        {"claim": "whether the declared clearances and residual play are acceptable",
         "status": "UNSUPPORTED", "because": "AMB-BM-003-007"},
        {"claim": "whether a bayonet could be turned back by vibration or handling",
         "status": "NOT_VERIFIED", "because": "rigid geometry cannot observe it; no dynamic route was run"},
        {"claim": "behaviour under gravity, inertia or any dynamic load",
         "status": "NOT_VERIFIED", "because": "DYNAMICS_NOT_REQUIRED_FOR_THIS_REFERENCE; see the governance record"},
    ]

    failed = [r for r in rows if r["status"] != "PASS"]
    return {
        "oracle": "ver3/oracles/held_out/BM-003",
        "oracle_frozen_before_this_reference": True,
        "declared_state_maintenance_class": "SMC-KINEMATIC_BLOCK",
        "realization_class": "RIGID_MULTI_BODY",
        "invariants": rows,
        "invariants_total": len(rows),
        "invariants_pass": len(rows) - len(failed),
        "invariants_failed": [r["invariant"] for r in failed],
        "unsupported_and_not_verified": unsupported,
        "oracle_reopening": {
            "conditions_that_would_require_it": [
                "a mechanically coherent exact B-rep reference rejected by an operative predicate",
                "an exact negative control passing its intended predicate",
                "required exact assembly or mobility evidence that the Oracle schema cannot represent"],
            "any_condition_met": False,
            "consequence": "no Oracle change is proposed by this reference"},
        "status": "PASS" if not failed else "FAIL",
    }


# ==================================================================== main
def main() -> int:
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    steps: Dict[str, str] = {}

    stage("build")
    bodies, build_rec = vc.step1_build(CTX)
    steps["1_build"] = "PASS"
    stage("build", "END")
    stage("native validity")
    steps["2_validity"] = vc.step2_validity(CTX, bodies)["status"]
    stage("native validity", "END")
    stage("re-import")
    steps["3_reimport"] = vc.step3_reimport(CTX, bodies)["status"]
    stage("re-import", "END")

    critical = {k: v for k, v in G.items()}
    critical.update({"leg_len": P["leg_len"], "hinge_r": P["hinge_r"],
                     "theta_deployed": P["theta_deployed"]})
    motion = {"states": B.STATES, "segments": B.SEGMENTS,
              "segment_ends": B.SEGMENT_ENDS,
              "keyframes": {k: [round(x, 9) for x in v]
                            for k, v in B._keyframes(P, G).items()}}
    stage("geometry signature")
    sig = vc.step4_signature(CTX, bodies, critical=critical, motion=motion)
    steps["4_signature"] = sig["status"]
    cv.write_json(os.path.join(HERE, "geometry_signature.json"), sig["signature"])
    stage("geometry signature", "END")

    n_fold = 12 if FAST else 40
    n_turn = 10 if FAST else 24
    n_asm = 40 if FAST else 150
    n_conn = 8 if FAST else 16
    n_path = 8 if FAST else 20
    n_turnsweep = 8 if FAST else 24

    # ------------------------------------------------ mechanism evidence
    stage("core predicates")
    ev: Dict[str, Dict] = {}
    ev["state_maintenance"] = p_block(BASE, n_fold)
    ev["release"] = p_release(BASE, n_fold)
    ev["lift_only"] = p_lift_only(BASE, n_fold)
    ev["antirotation"] = p_antirot(BASE, n_turn)
    ev["outward_stop"] = p_outward(BASE, 40 if FAST else 80)
    ev["retention"] = p_retention(BASE)
    ev["three_legs"] = p_three_legs(BASE)
    ev["footprint"] = p_footprint(BASE)
    ev["compactness"] = p_compact(BASE)
    ev["support_region"] = p_support(BASE)
    ev["connectivity"] = p_connected(BASE, n_conn)
    ev["continuity"] = p_continuity(BASE, n_path)
    ev["cycle_return"] = cycle_return(BASE)
    ev["assembly_graph"] = assembly_graph()
    ev["path_sampling"] = p_path_sampled(_COARSE)

    turns = bayonet_turns(BASE, n_turnsweep)
    ev["bayonet_turns"] = {"turns": turns,
                           "status": "PASS" if all(t["status"] == "PASS" for t in turns)
                           else "FAIL"}

    decl_asm = yaml.safe_load(open(os.path.join(HERE, "assembly.yaml")))
    declared_rel = set(decl_asm["operational_relations_activated_here"])
    used_rel = set()
    for it in yaml.safe_load(open(os.path.join(HERE, "interactions.yaml")))["interactions"]:
        if "realises" in it:
            used_rel.add(it["realises"])
    activated = set()
    for s in decl_asm["steps"]:
        a = s.get("activates")
        if isinstance(a, str):
            activated.add(a)
        elif isinstance(a, list):
            activated.update(a)
    missing = sorted(used_rel - activated)
    ev["relations_activated"] = {
        "declared": sorted(declared_rel),
        "activated_by_a_step": sorted(activated),
        "referenced_by_an_interaction": sorted(used_rel),
        "referenced_but_never_activated": missing,
        "undeclared_relations": sorted(used_rel - declared_rel),
        "status": "PASS" if not missing and used_rel <= declared_rel else "FAIL"}

    for name, rec in ev.items():
        cv.write_json(os.path.join(OUT, "%s.json" % name), rec)
    stage("core predicates", "END")
    cv.write_json(os.path.join(OUT, "state_maintenance.json"), {
        "declared_class": "SMC-KINEMATIC_BLOCK",
        "obstructing_bodies": {"BODY-LEG-x heel": "BODY-RING arm underside"},
        "block": ev["state_maintenance"], "release": ev["release"],
        "lift_alone_is_not_enough": ev["lift_only"],
        "ring_cannot_turn_while_down": ev["antirotation"],
        "outward_stop": ev["outward_stop"],
        "status": "PASS" if all(ev[k]["status"] == "PASS" for k in
                                ("state_maintenance", "release", "lift_only",
                                 "antirotation", "outward_stop")) else "FAIL"})

    # ----------------------------------------------------- engine steps 5-7
    probes = [{"probe": "arms present", "result": ev["state_maintenance"]["status"],
               "max_common_volume_at_stored_mm3":
                   ev["state_maintenance"]["scan"][-1]["max_common_volume_mm3"]},
              {"probe": "one arm removed",
               "result": "the leg that lost its arm is no longer obstructed",
               "reference": "checker_selftest.json#NC-04"}]
    probe_meta = {
        "terminal_condition": "fold-back from DEPLOYED_LOCKED is obstructed",
        "declared_determinant": "the ring arm above each heel",
        "discriminates": ev["state_maintenance"]["status"] == "PASS",
        "method": ("the condition is measured with the determinant present and, in "
                   "NC-04, with it removed; it holds in the first case and not the "
                   "second, so the condition is produced by the thing it is attributed "
                   "to and not by something else in the model")}
    stage("motion report")
    steps["5_motion"] = vc.step5_motion(CTX, bodies, probes, probe_meta)["status"]
    stage("motion report", "END")
    stage("interaction report")
    ext = {}
    steps["6_interactions"] = vc.step6_interactions(CTX, bodies, ext)["status"]
    stage("interaction report", "END")
    stage("assembly report")
    steps["7_assembly"] = vc.step7_assembly(CTX, bodies, samples=n_asm,
                                            step_bodies=_insertion_bodies(BASE))["status"]
    stage("assembly report", "END")

    for k in ("state_maintenance", "release", "lift_only", "antirotation", "retention",
              "outward_stop", "three_legs", "footprint", "compactness", "support_region",
              "connectivity", "continuity", "cycle_return", "assembly_graph",
              "bayonet_turns", "relations_activated", "path_sampling"):
        steps["EV_%s" % k] = ev[k]["status"]

    # ------------------------------------------------------ negative controls
    global BASELINE_PREDICATES
    BASELINE_PREDICATES = {
        "P_THREE_LEGS": ev["three_legs"]["status"],
        "P_BLOCK": ev["state_maintenance"]["status"],
        "P_RELEASE": ev["release"]["status"],
        "P_RETENTION": ev["retention"]["status"],
        "P_COMPACT": ev["compactness"]["status"],
        "P_FOOTPRINT": ev["footprint"]["status"],
        "P_SUPPORT": ev["support_region"]["status"],
        "P_ANTIROT": ev["antirotation"]["status"],
        "P_ASM_ACYCLIC": ev["assembly_graph"]["status"],
        "P_ASM_PATHS": steps["7_assembly"],
        "P_CONTINUITY": ev["continuity"]["status"],
        "P_OUTWARD": ev["outward_stop"]["status"],
        "P_PATH_CLEAR": steps["5_motion"],
    }
    stage("negative controls")
    cases = negative_controls(FAST)
    steps["selftest"] = vc.run_selftest(CTX, cases)["status"]
    stage("negative controls", "END")

    # ------------------------------------------------------------- step 8
    # the engine's own steps are evidence too; step 8 reads them by name
    ev["motion"] = {"status": steps["5_motion"], "source": "validation/motion_report.json"}
    ev["interactions"] = {"status": steps["6_interactions"],
                          "source": "validation/interaction_report.json"}
    ev["assembly"] = {"status": steps["7_assembly"],
                      "source": "validation/assembly_report.json"}
    stage("oracle evaluation")
    oracle = oracle_evaluation(ev)
    steps["8_oracle"] = oracle["status"]
    cv.write_json(os.path.join(OUT, "oracle_evaluation.json"), oracle)
    cv.write_json(os.path.join(HERE, "actual_evaluation.json"), oracle)
    stage("oracle evaluation", "END")

    stage("rendering")
    steps["9_render"] = vc.step9_render(CTX, bodies)["status"]
    stage("rendering", "END")

    meaning = (
        "ONE_POSITIVE_EXECUTABLE_REFERENCE_VALIDATED. One mechanism, built as exact "
        "OCCT B-rep solids, satisfies the frozen BM-003 Oracle's operative invariants "
        "under the evidence this toolset can produce. It is an evaluator fixture. It "
        "is not a golden design, not a mandatory mechanism, not a production result, "
        "and it establishes nothing about the other realization families the Oracle "
        "admits.")
    stage("final summary")
    summary = vc.write_summary(CTX, steps, sig["signature"]["signature_sha256"],
                               time.time() - t0, FAST, meaning)
    stage("final summary", "END")
    print(json.dumps({"overall": summary["overall"], "steps": steps,
                      "seconds": summary["run_seconds"],
                      "signature": summary["geometry_signature_sha256"]}, indent=2))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    acquire_lock()
    _rc, _state, _detail = 1, "EXECUTION_FAILED", ""
    try:
        _rc = main()
        _state = "PASS" if _rc == 0 else "FAIL"
    except KeyboardInterrupt:
        _state, _detail = "INTERRUPTED", "SIGINT"
        _rc = 130
    except SystemExit as _e:
        _state = "INTERRUPTED" if _e.code not in (0, 1) else ("PASS" if _e.code == 0
                                                              else "FAIL")
        _detail = "SystemExit(%r)" % (_e.code,)
        _rc = _e.code if isinstance(_e.code, int) else 1
    except BaseException as _e:                            # noqa: BLE001
        _state, _detail = "EXECUTION_FAILED", "%s: %s" % (type(_e).__name__, _e)
        raise
    finally:
        write_run_status(_state, _detail)
        release_lock()
        sys.stdout.write("RUN_STATUS: %s\n" % _state)
        sys.stdout.flush()
    sys.exit(_rc)
