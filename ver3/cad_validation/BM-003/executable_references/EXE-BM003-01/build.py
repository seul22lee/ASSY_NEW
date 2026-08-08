"""EXE-BM003-01 - exact B-rep construction of one folding desk stand.

This module is the authoritative design source together with parameters.yaml.
Every solid here is an exact OpenCascade B-rep built through CadQuery. There is
no second geometry representation, no proxy, and no approximate collision model
anywhere in this reference: every distance and every overlap reported by
validate.py is computed by the kernel on these solids.

WHAT THE MECHANISM IS
    A central hub carries three leg stations 120 degrees apart. Each station is a
    clevis pair; a leg blade sits between the plates on a hinge pin. Each leg
    carries a HEEL - a stub rigidly part of the leg, leaning inward from the
    hinge. Swinging the leg out lowers its heel; swinging it back raises it.

    A captive annular ring runs on the hub column. It has three arms. Lowered,
    each arm sits a small gap above one heel, so folding that leg back drives its
    heel into the arm and stops. That is the whole state-maintenance principle:
    SMC-KINEMATIC_BLOCK, realised as hard geometric interference.

    The ring cannot be turned while it is down, because three ribs on the column
    sit inside three keyways in its bore. Releasing therefore takes two motions:
    LIFT the ring clear of the ribs, then TURN it so the arms move off the heels
    and onto the rib tops. Only then can the legs fold.

    Nothing can leave. The ring is trapped between the pedestal top and the ring
    captor. The captor is trapped between a column step and a bayonet. The top
    support is trapped between the captor's lugs and a second bayonet. Each hinge
    pin is trapped between its own head on one side and a bayonet end bar on the
    other.

FRAME
    Z is the hub axis, up. z = 0 is the plane of the three hinge axes. Each leg
    station has a local frame rotated about Z by its azimuth; in it +x is radially
    outward and +y is tangential. Legs, heels and pins are built in a station
    frame and then rotated into place.

AS-BUILT POSE
    build() returns the assembly in the configuration the assembly sequence ends
    in: legs DEPLOYED, ring LOCKED. Step 7 sweeps the as-built solids, so the
    as-built pose has to be the assembled pose. FRE-BM-003-013 leaves the arrival
    configuration free, and this design has to use that freedom: the ring cannot
    be lowered onto the heels unless the legs are already out.
"""
from __future__ import annotations

import math
import os
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import cadquery as cq
import yaml

import cadval as cv

HERE = os.path.dirname(os.path.abspath(__file__))


def load_params() -> Dict[str, float]:
    with open(os.path.join(HERE, "parameters.yaml")) as fh:
        doc = yaml.safe_load(fh)
    return {p["name"]: float(p["value"]) for p in doc["parameters"]}


# --------------------------------------------------------------- primitives
def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def _cyl_z(r, z0, z1, x=0.0, y=0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(r, z1 - z0, pnt=cq.Vector(x, y, z0),
                                 dir=cq.Vector(0, 0, 1))


def _cyl_y(r, y0, y1, x=0.0, z=0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(r, y1 - y0, pnt=cq.Vector(x, y0, z),
                                 dir=cq.Vector(0, 1, 0))


def _tube(r_in, r_out, z0, z1) -> cq.Shape:
    return _cyl_z(r_out, z0, z1).cut(_cyl_z(r_in, z0 - 1.0, z1 + 1.0))


def _wedge(r_out, z0, z1, az_deg, half_deg) -> cq.Shape:
    """Solid triangular prism spanning az +/- half, big enough to contain r_out.

    Intersecting a tube with this gives an exact annular sector: two planar side
    faces and the tube's own cylindrical faces. No faceting anywhere.
    """
    if half_deg >= 89.0:
        raise ValueError("half_deg must stay below 89 for the triangle construction")
    reach = r_out / math.cos(math.radians(half_deg)) + 1.0
    a0 = math.radians(az_deg - half_deg)
    a1 = math.radians(az_deg + half_deg)
    pts = [(0.0, 0.0),
           (reach * math.cos(a0), reach * math.sin(a0)),
           (reach * math.cos(a1), reach * math.sin(a1))]
    face = cq.Face.makeFromWires(cq.Wire.makePolygon(
        [cq.Vector(x, y, z0) for x, y in pts] + [cq.Vector(pts[0][0], pts[0][1], z0)]))
    return cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))


def _sector(r_in, r_out, z0, z1, az_deg, half_deg) -> cq.Shape:
    return _tube(r_in, r_out, z0, z1).intersect(_wedge(r_out, z0 - 1.0, z1 + 1.0,
                                                       az_deg, half_deg))


def _rot_z(shape: cq.Shape, deg: float) -> cq.Shape:
    return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), deg)


def _rot_y(shape: cq.Shape, deg: float, at=(0.0, 0.0, 0.0)) -> cq.Shape:
    return shape.rotate(cq.Vector(at[0], at[1], at[2]),
                        cq.Vector(at[0], at[1] + 1.0, at[2]), deg)


def _one_solid(shape: cq.Shape) -> cq.Shape:
    """Reduce a fused compound to the single solid it should be."""
    solids = cq.Workplane("XY").add(shape).solids().vals()
    if len(solids) == 1:
        return solids[0]
    return shape


def _fuse(*shapes: cq.Shape) -> cq.Shape:
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return _one_solid(out.clean())


# ---------------------------------------------------------- derived geometry
def geom(p: Dict[str, float]) -> Dict[str, float]:
    """Values computed from parameters.yaml. These are the design's real stops.

    The ring seat is DERIVED from where the heel actually is when the leg is
    deployed, not chosen independently, so the blocking gap is a stated design
    quantity rather than an accident of two independent numbers.
    """
    beta = math.radians(p["heel_beta"])
    # The four corners of the heel prism in the leg's stored frame, relative to
    # the hinge. The prism is built along +z and tipped inward by beta.
    def corner(sx, sz):
        x = sx * math.cos(beta) - sz * math.sin(beta)
        z = sx * math.sin(beta) + sz * math.cos(beta)
        return math.hypot(x, z), math.degrees(math.atan2(z, x))

    hh, hl = p["heel_half_x"], p["heel_len"]
    c_top = corner(hh, hl)            # topmost corner: what the ring arm blocks
    c_far = corner(-hh, hl)           # far end of the heel's underside
    c_near = corner(-hh, 0.0)         # near end of the heel's underside
    radius, psi0 = c_top

    def heel_top(theta_deg: float) -> float:
        return radius * math.sin(math.radians(psi0 + theta_deg))

    def at(c, theta_deg):
        a = math.radians(c[1] + theta_deg)
        return p["hinge_r"] + c[0] * math.cos(a), c[0] * math.sin(a)

    # Height of the heel's underside above the outward stop pad's outer edge, at
    # the deployed angle. The pad top is placed the declared clearance below it,
    # which is what limits how far a leg can splay past deployed.
    f_r, f_z = at(c_far, p["theta_deployed"])
    n_r, n_z = at(c_near, p["theta_deployed"])
    frac = (p["stop_pad_x1"] - f_r) / (n_r - f_r)
    stop_pad_z1 = f_z + frac * (n_z - f_z) - p["outward_stop_clearance"]

    heel_top_deployed = heel_top(p["theta_deployed"])
    seat_z = heel_top_deployed + p["blocker_clearance"]
    rib_z1 = seat_z + p["rib_h"]
    ring_z_released = rib_z1 + p["ring_rib_clearance"]
    captor_z0 = ring_z_released + p["ring_h"]
    captor_z1 = captor_z0 + p["captor_h"]
    captor_lug_z0 = captor_z1 + p["captor_play"]
    captor_lug_z1 = captor_lug_z0 + p["lug_h"]

    # Angle at which fold-back is stopped: the heel corner reaches the arm.
    sin_stop = min(1.0, seat_z / radius)
    psi_stop = 180.0 - math.degrees(math.asin(sin_stop))
    theta_block = psi_stop - psi0
    # Angle reached if the ring is lifted but NOT turned.
    sin_lift = min(1.0, ring_z_released / radius)
    theta_lift_only = 180.0 - math.degrees(math.asin(sin_lift)) - psi0

    return {
        "heel_corner_radius": radius,
        "heel_corner_psi0_deg": psi0,
        "stop_pad_z1": stop_pad_z1,
        "heel_underside_z_at_pad_edge": stop_pad_z1 + p["outward_stop_clearance"],
        "heel_top_stored": heel_top(p["theta_stored"]),
        "heel_top_deployed": heel_top_deployed,
        "seat_z": seat_z,
        "ring_z_locked": seat_z,
        "rib_z0": seat_z,
        "rib_z1": rib_z1,
        "ring_z_released": ring_z_released,
        "captor_z0": captor_z0,
        "captor_z1": captor_z1,
        "captor_lug_z0": captor_lug_z0,
        "captor_lug_z1": captor_lug_z1,
        "sleeve_z0": captor_lug_z1,
        "plate_groove_z0": p["top_lug_z0"] - p["top_lift_play"],
        "plate_groove_z1": p["top_lug_z1"] + p["top_lift_play"],
        "column_top_z": p["top_lug_z1"],
        "ear_y1": -(p["clevis_y1"] + p["ear_gap"]),
        "ear_y0": -(p["clevis_y1"] + p["ear_gap"] + p["ear_t"]),
        "theta_block_deg": theta_block,
        "theta_lift_only_deg": theta_lift_only,
    }


STATION_KEYS = ("A", "B", "C")


def stations(p: Dict[str, float]) -> Dict[str, float]:
    return {"A": p["station_azimuth_a"], "B": p["station_azimuth_b"],
            "C": p["station_azimuth_c"]}


# ------------------------------------------------------------------ the hub
def build_hub(p: Dict[str, float], g: Dict[str, float],
              defeat: FrozenSet[str] = frozenset()) -> cq.Shape:
    az = stations(p)
    parts = [
        _cyl_z(p["hub_base_r"], p["hub_base_z0"], p["hub_base_z1"]),
        _cyl_z(p["pedestal_r"], p["hub_base_z1"], g["seat_z"]),
        _cyl_z(p["journal_r"], g["seat_z"], g["captor_z0"]),
        _cyl_z(p["column_r"], g["captor_z0"], g["column_top_z"]),
    ]
    if "NC_BASE_GROWN" in defeat:
        # taller base flange: reaches into the heel sweep part way through the fold
        parts[0] = _cyl_z(p["hub_base_r"], p["hub_base_z0"], p["hub_base_z1"] + 6.0)

    # three anti-rotation ribs, midway between the legs
    if "NC_RIBS_REMOVED" not in defeat:
        for k in STATION_KEYS:
            parts.append(_sector(p["journal_r"] - 0.5, p["rib_r"],
                                 g["rib_z0"], g["rib_z1"],
                                 az[k] + p["rib_azimuth_offset"], p["rib_half_deg"]))

    # two bayonet lugs for the ring captor, two more for the top support
    for base in (p["bayonet_azimuth"], p["bayonet_azimuth"] + 180.0):
        if "NC_CAPTOR_LUGS_REMOVED" not in defeat:
            parts.append(_sector(p["column_r"] - 0.5, p["lug_r"],
                                 g["captor_lug_z0"], g["captor_lug_z1"],
                                 base, p["lug_half_deg"]))
        parts.append(_sector(p["column_r"] - 0.5, p["lug_r"],
                             p["top_lug_z0"], p["top_lug_z1"],
                             base, p["lug_half_deg"]))

    # NEGATIVE CONTROL ONLY: a boss placed in the band the heel sweeps through
    # strictly between the two endpoints, so both endpoints stay interference free
    if "NC_HUB_BOSS" in defeat:
        for k in STATION_KEYS:
            parts.append(_rot_z(_box(23.0, 24.5, -p["clevis_y1"], p["clevis_y1"],
                                     9.9, 10.5), az[k]))

    # three outward stop pads: the heel's underside comes down on these, which is
    # what bounds the leg's swing on the far side of the deployed angle
    if "NC_STOP_PAD_REMOVED" not in defeat:
        for k in STATION_KEYS:
            parts.append(_rot_z(_box(p["stop_pad_x0"], p["stop_pad_x1"],
                                     -p["stop_pad_half_y"], p["stop_pad_half_y"],
                                     p["hub_base_z0"], g["stop_pad_z1"]), az[k]))

    # three clevis pairs
    for k in STATION_KEYS:
        for sign in (1.0, -1.0):
            plate = _box(p["clevis_x0"], p["clevis_x1"],
                         min(sign * p["clevis_y0"], sign * p["clevis_y1"]),
                         max(sign * p["clevis_y0"], sign * p["clevis_y1"]),
                         p["clevis_z0"], p["clevis_z1"])
            parts.append(_rot_z(plate, az[k]))

    hub = _fuse(*parts)

    # hinge bores and the bayonet relief that lets each pin's end bar through
    for k in STATION_KEYS:
        bore = _cyl_y(p["pin_bore_r"], -p["clevis_y1"] - 1.0, p["clevis_y1"] + 1.0,
                      x=p["hinge_r"], z=p["hinge_z"])
        cut = bore
        if "NC_PIN_RELIEF_BLOCKED" not in defeat:
            cut = cut.fuse(_box(p["hinge_r"] - p["pin_slot_half_x"],
                                p["hinge_r"] + p["pin_slot_half_x"],
                                -p["clevis_y1"] - 1.0, p["clevis_y1"] + 1.0,
                                p["hinge_z"] - p["pin_slot_half_z"],
                                p["hinge_z"] + p["pin_slot_half_z"]))
        hub = hub.cut(_rot_z(cut, az[k]))

    return _one_solid(hub.clean())


# ----------------------------------------------------------------- the legs
def build_leg(p: Dict[str, float], g: Dict[str, float], key: str,
              defeat: FrozenSet[str] = frozenset()) -> cq.Shape:
    """One leg, built in its station frame at theta_stored, then deployed."""
    hx, hz = p["hinge_r"], p["hinge_z"]
    half_y = p["blade_half_y"]
    if "NC_LEG_WIDE" in defeat and key == "A":
        half_y = 34.0            # wide enough to reach its neighbours mid-fold

    shaft = _box(hx - p["shaft_half_x"], hx + p["shaft_half_x"],
                 -half_y, half_y, hz - p["leg_len"], hz)
    eye = _cyl_y(p["eye_r"], -half_y, half_y, x=hx, z=hz)

    parts = [shaft, eye]

    if not ("NC_HEEL_REMOVED" in defeat and key == "A"):
        heel = _box(-p["heel_half_x"], p["heel_half_x"], -half_y, half_y,
                    0.0, p["heel_len"])
        heel = _rot_y(heel, -p["heel_beta"])
        parts.append(heel.translate(cq.Vector(hx, 0.0, hz)))
        if "NC_LEG_LOBE" in defeat:
            # NEGATIVE CONTROL ONLY: a wide tangential lobe on the heel tip, so the
            # three legs reach each other
            lobe = _box(-p["heel_half_x"], p["heel_half_x"], -17.0, 17.0,
                        16.0, p["heel_len"])
            lobe = _rot_y(lobe, -p["heel_beta"])
            parts.append(lobe.translate(cq.Vector(hx, 0.0, hz)))

    pad = _box(-p["pad_half_x"], p["pad_half_x"], -half_y, half_y,
               p["pad_z0"], p["pad_z1"])
    pad = _rot_y(pad, p["theta_deployed"])
    parts.append(pad.translate(cq.Vector(hx, 0.0, hz + p["pad_centre_z"])))

    leg = _fuse(*parts)

    # swing to the as-built (deployed) pose, then cut the hinge bore and the pin
    # relief in world coordinates so the relief is horizontal during assembly
    leg = _rot_y(leg, -p["theta_deployed"], at=(hx, 0.0, hz))
    bore = _cyl_y(p["pin_bore_r"], -half_y - 1.0, half_y + 1.0, x=hx, z=hz)
    relief = _box(hx - p["pin_slot_half_x"], hx + p["pin_slot_half_x"],
                  -half_y - 1.0, half_y + 1.0,
                  hz - p["pin_slot_half_z"], hz + p["pin_slot_half_z"])
    leg = leg.cut(bore.fuse(relief))

    return _one_solid(_rot_z(leg, stations(p)[key]).clean())


# ------------------------------------------------------------ the hinge pins
def build_pin(p: Dict[str, float], g: Dict[str, float], key: str,
              locked: bool = True,
              defeat: FrozenSet[str] = frozenset()) -> cq.Shape:
    """One hinge pin. `locked` gives the bayonet end bar its turned orientation."""
    hx, hz = p["hinge_r"], p["hinge_z"]
    shaft = _cyl_y(p["pin_r"], g["ear_y1"], p["clevis_y1"], x=hx, z=hz)
    head = _cyl_y(p["pin_head_r"], p["clevis_y1"],
                  p["clevis_y1"] + p["pin_head_t"], x=hx, z=hz)
    parts = [shaft, head]
    if not ("NC_PIN_CAPTOR_REMOVED" in defeat and key == "A"):
        bar = _box(hx - p["ear_half_x"], hx + p["ear_half_x"],
                   g["ear_y0"], g["ear_y1"],
                   hz - p["ear_half_z"], hz + p["ear_half_z"])
        if locked:
            bar = bar.rotate(cq.Vector(hx, 0.0, hz), cq.Vector(hx, 1.0, hz), 90.0)
        parts.append(bar)
    pin = _fuse(*parts)
    return _one_solid(_rot_z(pin, stations(p)[key]).clean())


# ---------------------------------------------------------- the locking ring
def build_ring(p: Dict[str, float], g: Dict[str, float],
               defeat: FrozenSet[str] = frozenset()) -> cq.Shape:
    """The captive ring, built at its locked height and locked azimuth."""
    z0 = g["ring_z_locked"]
    z1 = z0 + p["ring_h"]
    az = stations(p)
    ring = _tube(p["ring_bore_r"], p["ring_collar_r"], z0, z1)

    arms = list(STATION_KEYS)
    if "NC_ONE_ARM_REMOVED" in defeat:
        arms = ["B", "C"]
    for k in arms:
        ring = ring.fuse(_sector(p["ring_collar_r"] - 0.5, p["ring_arm_r"], z0, z1,
                                 az[k], p["ring_arm_half_deg"]))
    ring = _one_solid(ring.clean())

    # three keyways that ride over the anti-rotation ribs
    for k in STATION_KEYS:
        ring = ring.cut(_sector(p["ring_bore_r"] - 1.0, p["ring_key_r"],
                                z0 - 1.0, z1 + 1.0,
                                az[k] + p["rib_azimuth_offset"],
                                p["ring_key_half_deg"]))
    return _one_solid(ring.clean())


# ----------------------------------------------------------- the ring captor
def build_captor(p: Dict[str, float], g: Dict[str, float], locked: bool = True,
                 defeat: FrozenSet[str] = frozenset()) -> cq.Shape:
    r_out = p["captor_r"]
    if "NC_CAPTOR_UNDERSIZED" in defeat:
        r_out = p["ring_bore_r"] - 0.6      # no longer overhangs the ring bore
    captor = _tube(p["captor_bore_r"], r_out, g["captor_z0"], g["captor_z1"])
    turn = 90.0 if locked else 0.0
    keyways = () if "NC_CAPTOR_UNDERSIZED" in defeat else (
        p["bayonet_azimuth"], p["bayonet_azimuth"] + 180.0)
    for base in keyways:
        captor = captor.cut(_sector(p["captor_bore_r"] - 1.0, p["captor_key_r"],
                                    g["captor_z0"] - 1.0, g["captor_z1"] + 1.0,
                                    base + turn, p["captor_key_half_deg"]))
    return _one_solid(captor.clean())


# ---------------------------------------------------------- the top support
def build_top_support(p: Dict[str, float], g: Dict[str, float],
                      locked: bool = True,
                      defeat: FrozenSet[str] = frozenset()) -> cq.Shape:
    sleeve = _cyl_z(p["sleeve_r"], g["sleeve_z0"], p["plate_z0"])
    plate = _cyl_z(p["plate_r"], p["plate_z0"], p["plate_z1"])
    body = _fuse(sleeve, plate)
    # bore, then the circumferential bayonet groove in the platform
    body = body.cut(_cyl_z(p["sleeve_bore_r"], g["sleeve_z0"] - 1.0,
                           g["plate_groove_z0"]))
    body = body.cut(_tube(0.0, p["plate_groove_r"],
                          g["plate_groove_z0"], g["plate_groove_z1"]))
    turn = 90.0 if locked else 0.0
    for base in (p["bayonet_azimuth"], p["bayonet_azimuth"] + 180.0):
        body = body.cut(_sector(p["sleeve_bore_r"] - 1.0, p["captor_key_r"],
                                g["sleeve_z0"] - 1.0, g["plate_groove_z0"],
                                base + turn, p["captor_key_half_deg"]))
    return _one_solid(body.clean())


# ------------------------------------------------------------- the assembly
def build(p: Optional[Dict[str, float]] = None,
          defeat: FrozenSet[str] = frozenset()) -> List[cv.Body]:
    p = p or load_params()
    g = geom(p)
    bodies = [cv.Body("BODY-HUB", "central hub", "RIGID", build_hub(p, g, defeat),
                      role="fixed reference body; carries three clevis pairs, the "
                           "ring journal, the anti-rotation ribs and both bayonets",
                      installed_as="DISCRETE")]
    for k in STATION_KEYS:
        if "NC_LEG_OMITTED" in defeat and k == "C":
            continue
        bodies.append(cv.Body("BODY-LEG-%s" % k, "support leg %s" % k, "RIGID",
                              build_leg(p, g, k, defeat),
                              role="swings about its hinge; its heel is what the "
                                   "ring arm blocks",
                              installed_as="DISCRETE"))
        bodies.append(cv.Body("BODY-PIN-%s" % k, "hinge pin %s" % k, "RIGID",
                              build_pin(p, g, k, True, defeat),
                              role="revolute joint; retained by its head one side "
                                   "and its bayonet end bar the other",
                              installed_as="DISCRETE"))
    bodies.append(cv.Body("BODY-RING", "locking ring", "RIGID",
                          build_ring(p, g, defeat),
                          role="captive slider-turner; its three arms block "
                               "fold-back when lowered",
                          installed_as="DISCRETE"))
    bodies.append(cv.Body("BODY-RING-CAPTOR", "ring captor", "RIGID",
                          build_captor(p, g, True, defeat),
                          role="final captor: overhangs the ring bore so the ring "
                               "cannot leave the column",
                          installed_as="DISCRETE"))
    bodies.append(cv.Body("BODY-TOP-SUPPORT", "top support", "RIGID",
                          build_top_support(p, g, True, defeat),
                          role="the platform offered to hold an object; bayoneted "
                               "to the column top",
                          installed_as="DISCRETE"))
    return bodies


# ---------------------------------------------------------------- kinematics
STATES = ["STORED", "DEPLOYED_LOCKED", "DEPLOYED_RELEASED"]

SEGMENTS = ["M1_UNFOLD", "M2_RING_TURN_TO_LOCK", "M3_RING_LOWER_TO_LOCK",
            "M4_RING_LIFT_TO_RELEASE", "M5_RING_TURN_TO_RELEASE", "M6_FOLD"]


def _keyframes(p: Dict[str, float], g: Dict[str, float]) -> Dict[str, Tuple[float, float, float]]:
    """(leg angle, ring height, ring azimuth) at each named configuration."""
    return {
        "STORED": (p["theta_stored"], g["ring_z_released"], p["ring_release_rot"]),
        "DEPLOYED_RELEASED": (p["theta_deployed"], g["ring_z_released"],
                              p["ring_release_rot"]),
        "LIFTED_ALIGNED": (p["theta_deployed"], g["ring_z_released"], 0.0),
        "DEPLOYED_LOCKED": (p["theta_deployed"], g["ring_z_locked"], 0.0),
    }


SEGMENT_ENDS = {
    "M1_UNFOLD": ("STORED", "DEPLOYED_RELEASED"),
    "M2_RING_TURN_TO_LOCK": ("DEPLOYED_RELEASED", "LIFTED_ALIGNED"),
    "M3_RING_LOWER_TO_LOCK": ("LIFTED_ALIGNED", "DEPLOYED_LOCKED"),
    "M4_RING_LIFT_TO_RELEASE": ("DEPLOYED_LOCKED", "LIFTED_ALIGNED"),
    "M5_RING_TURN_TO_RELEASE": ("LIFTED_ALIGNED", "DEPLOYED_RELEASED"),
    "M6_FOLD": ("DEPLOYED_RELEASED", "STORED"),
}


def pose_at(p: Dict[str, float], body_id: str,
            theta: float, ring_z: float, ring_phi: float) -> cq.Location:
    """Rigid transform from the as-built pose to the given configuration."""
    g = geom(p)
    if body_id.startswith("BODY-LEG-"):
        k = body_id[-1]
        a = math.radians(stations(p)[k])
        origin = (p["hinge_r"] * math.cos(a), p["hinge_r"] * math.sin(a), p["hinge_z"])
        axis = (-math.sin(a), math.cos(a), 0.0)
        return cv.rotation(origin, axis, p["theta_deployed"] - theta)
    if body_id == "BODY-RING":
        return (cv.translation((0.0, 0.0, ring_z - g["ring_z_locked"]))
                * cv.rotation((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), ring_phi))
    return cq.Location()


def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    theta, ring_z, ring_phi = _keyframes(p, geom(p))[state]
    return pose_at(p, body_id, theta, ring_z, ring_phi)


def configuration(bodies: Sequence[cv.Body], p: Dict[str, float],
                  state: str) -> List[cv.Body]:
    return [b.moved(pose(p, b.id, state)) for b in bodies]


def bodies_at(bodies: Sequence[cv.Body], p: Dict[str, float],
              theta: float, ring_z: float, ring_phi: float) -> List[cv.Body]:
    return [b.moved(pose_at(p, b.id, theta, ring_z, ring_phi)) for b in bodies]


def continuous_pose(bodies: Sequence[cv.Body], p: Dict[str, float],
                    seg: str, t: float,
                    defeat: FrozenSet[str] = frozenset()) -> List[cv.Body]:
    k = _keyframes(p, geom(p))
    a, b = (k[s] for s in SEGMENT_ENDS[seg])
    u = t
    if "NC_TRANSFORM_JUMP" in defeat and seg == "M6_FOLD":
        # a discontinuous interpolant: the same endpoints, a jump in between
        u = 0.0 if t < 0.5 else 1.0
    vals = tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
    return bodies_at(bodies, p, *vals)
