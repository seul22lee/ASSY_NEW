"""EXE-BM001-01 - rigid rotating closure on a realized knuckle-and-pin axis.

An Oracle-aware executable REFERENCE for BM-001. Its purpose is to establish
that at least one design satisfying the rank-1 source can be built as valid
B-rep solids and moved through its required states without undeclared
volumetric overlap. It is not a demonstration and it proves nothing about
whether the source alone leads anywhere.

Three product bodies and no others:

    BODY-ENCLOSURE   fixed shell with a cavity, five knuckle segments and the
                     latch keeper rib on its front face
    BODY-CLOSURE     plate, front lip, web, two knuckle segments, a stop block,
                     and the integral exterior snap latch
    BODY-PIN         headed shaft with two integral cantilever snap arms

An earlier realization held the lid shut with a separate lift-bolt - a fourth
body with a knob, a shaft, a closure guide boss and an enclosure socket, four
features and an extra part to do one thing. It also read as a key, which it
never was: it gave no keying, no authorization and no security. It is gone. The
closure now carries its own latch and the enclosure carries the keeper.

Two features deform, each only in its own declared region and only during its
own declared action: the pin's snap arms during insertion, and the latch beam
during release and the closing lead-in. Both are rigid translations of a
declared region - DECLARED_KINEMATIC_APPROXIMATIONs that conserve volume
exactly and model no strain. No force is computed anywhere here. The
terminal open condition is *constructed*: the stop face is drawn in the open
configuration and rotated back into the closed configuration, so the open angle
is a consequence of the geometry rather than a number asserted about it.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List

import cadquery as cq
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import cadval as cv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_params() -> Dict[str, float]:
    with open(os.path.join(HERE, "parameters.yaml")) as fh:
        doc = yaml.safe_load(fh)
    return {p["name"]: float(p["value"]) for p in doc["parameters"]}


def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0,
                            pnt=cq.Vector(x0, y0, z0))


def _cyl_x(x0, x1, y, z, r) -> cq.Shape:
    """Cylinder with its axis along +X."""
    return cq.Solid.makeCylinder(r, x1 - x0, pnt=cq.Vector(x0, y, z),
                                 dir=cq.Vector(1, 0, 0))


def _cyl_z(z0, z1, x, y, r) -> cq.Shape:
    return cq.Solid.makeCylinder(r, z1 - z0, pnt=cq.Vector(x, y, z0),
                                 dir=cq.Vector(0, 0, 1))


def knuckle_bands(p: Dict[str, float]) -> Dict[str, List[tuple]]:
    """Five interleaved segments: enclosure, closure, enclosure, closure, enclosure.

    The outermost two segments belong to the enclosure so that the closure is
    axially captured between them.
    """
    seg, gap, x0 = p["knuckle_seg"], p["knuckle_gap"], p["knuckle_x0"]
    bands, x = [], x0
    for _ in range(5):
        bands.append((x, x + seg))
        x += seg + gap
    return {"enclosure": [bands[0], bands[2], bands[4]],
            "closure": [bands[1], bands[3]]}


def open_rotation(p: Dict[str, float], deg: float) -> cq.Location:
    """Rotation of the closure about the axis by `deg` in the opening sense.

    Opening lifts the front of the closure, which is a NEGATIVE rotation about
    +X in this frame.
    """
    return cv.rotation((0.0, p["axis_y"], p["axis_z"]), (1.0, 0.0, 0.0), -deg)


# --------------------------------------------------------------------- bodies
def build_enclosure(p: Dict[str, float]) -> cq.Shape:
    w, bx, by, bz = p["wall"], p["box_x"], p["box_y"], p["box_z"]
    ay, az, kr = p["axis_y"], p["axis_z"], p["knuckle_r"]

    shell = _box(0, bx, 0, by, 0, bz).cut(_box(w, bx - w, w, by - w, w, bz))

    # Latch keeper: a rib standing proud of the front face. Its UNDERSIDE is the
    # blocking face - the closure's latch shoulder bears on it when the lid is
    # pulled. It is fused to the wall, so it is enclosure material and not a
    # bridge, a bracket or anything that could float.
    kxh = p["keeper_w"] / 2.0
    shell = shell.fuse(_box(p["latch_x_centre"] - kxh, p["latch_x_centre"] + kxh,
                            -p["keeper_proj"], w, p["keeper_z0"], p["keeper_z1"]))

    # Knuckle segments and the webs tying them to the rear wall.
    for x0, x1 in knuckle_bands(p)["enclosure"]:
        shell = shell.fuse(_cyl_x(x0, x1, ay, az, kr))
        shell = shell.fuse(_box(x0, x1, by - p["web_gap"], ay, 20.0, az))

    # Bores, and the counterbore that seats the pin head.
    for x0, x1 in knuckle_bands(p)["enclosure"]:
        shell = shell.cut(_cyl_x(x0 - 0.5, x1 + 0.5, ay, az, p["bore_d"] / 2.0))
    kx0 = knuckle_bands(p)["enclosure"][0][0]
    shell = shell.cut(_cyl_x(kx0 - 0.5, kx0 + p["pin_cbore_depth"], ay, az,
                             p["pin_cbore_d"] / 2.0))
    return shell


def build_closure(p: Dict[str, float]) -> cq.Shape:
    """Built in the CLOSED configuration."""
    bx, bz, ay, az, kr = p["box_x"], p["box_z"], p["axis_y"], p["axis_z"], p["knuckle_r"]
    pt = p["plate_t"]

    # The plate needs no relief: the axis stands knuckle_r behind the rear outer
    # face, so the enclosure knuckle envelope never reaches forward of y = box_y
    # and the plate's rear edge stops short of it by web_gap.
    # The plate overhangs the front face by front_lip. That overhang is what the
    # latch beam hangs from, which is what puts the release on the outside.
    body = _box(0, bx, -p["front_lip"], p["plate_rear_y"], bz, bz + pt)

    for x0, x1 in knuckle_bands(p)["closure"]:
        body = body.fuse(_cyl_x(x0, x1, ay, az, kr))
        body = body.fuse(_box(x0, x1, p["web_front_y"], ay, bz, bz + pt))
        # Stop block, drawn in the OPEN configuration and rotated back.
        stop_open = _box(x0, x1, p["stop_y0"], p["stop_y1"], p["stop_z0"], p["stop_z1"])
        body = body.fuse(stop_open.moved(open_rotation(p, -p["open_angle_deg"])))

    for x0, x1 in knuckle_bands(p)["closure"]:
        body = body.cut(_cyl_x(x0 - 0.5, x1 + 0.5, ay, az, p["bore_d"] / 2.0))

    return body


def latch_geom(p: Dict[str, float]) -> Dict[str, float]:
    """Where the latch features are. Derived once so the builder, the validator
    and the drawings cannot disagree about them."""
    g = {}
    g["beam_x0"] = p["latch_x_centre"] - p["beam_w"] / 2.0
    g["beam_x1"] = p["latch_x_centre"] + p["beam_w"] / 2.0
    g["keeper_x0"] = p["latch_x_centre"] - p["keeper_w"] / 2.0
    g["keeper_x1"] = p["latch_x_centre"] + p["keeper_w"] / 2.0
    # beam sits latch_gap outboard of the keeper's front face
    g["beam_y1"] = -p["keeper_proj"] - p["latch_gap"]
    g["beam_y0"] = g["beam_y1"] - p["beam_t"]
    g["tooth_y1"] = g["beam_y1"] + p["tooth_proj"]      # inboard tip
    g["lip_y"] = -p["front_lip"]
    # How much of the tooth actually lies under the keeper: the tooth's inboard
    # tip against the keeper's front face. It is the tooth's projection less the
    # beam's running clearance - NOT keeper_proj less that clearance, which is a
    # different pair of numbers that happens to land nearby.
    g["engagement_mm"] = g["tooth_y1"] - (-p["keeper_proj"])
    return g


def build_latch(p: Dict[str, float], deflect: float = 0.0) -> cq.Shape:
    """The closure's integral snap latch: beam, tooth, lead-in ramp, shoulder.

    `deflect` is the outward (-Y) displacement of the declared compliant region
    REG-CLOSURE-LATCH-COMPLIANT. It is a rigid translation of that region: a
    DECLARED_KINEMATIC_APPROXIMATION that conserves volume exactly and models no
    strain. Nothing here computes a force.
    """
    g = latch_geom(p)
    # The beam runs up to the plate underside only. Its root is plate material and
    # never moves; translating the free length keeps the two solids face-to-face
    # at z = box_z, so the closure stays one connected solid and the deflected
    # configuration conserves volume exactly.
    beam = _box(g["beam_x0"], g["beam_x1"], g["beam_y0"], g["beam_y1"],
                p["beam_bot_z"], p["box_z"])
    # tooth section in the YZ plane, extruded through X. The bottom face slopes
    # up as it goes inboard: that slope is the lead-in, and closing the lid drives
    # the keeper's top corner along it and cams the beam out on its own.
    pts = [(g["beam_y1"], p["tooth_ramp_bot_z"]),
           (g["tooth_y1"], p["tooth_ramp_top_z"]),
           (g["tooth_y1"], p["tooth_top_z"]),
           (g["beam_y1"], p["tooth_top_z"])]
    wp = cq.Workplane("YZ", origin=(g["beam_x0"], 0, 0)).polyline(pts).close()
    tooth = wp.extrude(g["beam_x1"] - g["beam_x0"]).val()
    latch = beam.fuse(tooth)
    if deflect:
        latch = latch.moved(cv.translation((0.0, -deflect, 0.0)))
    return latch


def _cone_x(x0, x1, y, z, r0, r1) -> cq.Shape:
    """Truncated cone with its axis along +X."""
    return cq.Solid.makeCone(r0, r1, x1 - x0, pnt=cq.Vector(x0, y, z), dir=cq.Vector(1, 0, 0))


def build_pin(p: Dict[str, float], compressed: bool = False) -> cq.Shape:
    """Headed hinge pin with two integral cantilever snap arms.

    Axial retention is bilateral and both directions are geometric:

      * toward the barb end - FEA-P-SHOULDER bears on the counterbore floor
      * toward the head end - FEA-P-BARB-SHOULDER bears on the far face of the
                              last enclosure knuckle

    The arms are CANTILEVER BEAMS, not a split cone. A cone split by one slot
    compresses only across the slot: its extent perpendicular to the slot is
    unchanged, so it still cannot enter a round bore. Two beams carrying lugs
    do fit, because each beam is narrow in the direction it does not move.

    `compressed=True` returns the declared compliant configuration used for the
    insertion check - the same two arms, deflected inward about their roots. It
    is a configuration of this pin, never a separate part, and never exported.
    """
    ay, az = p["axis_y"], p["axis_z"]
    bands = knuckle_bands(p)["enclosure"]
    kx0, kxN = bands[0][0], bands[-1][1]
    head_x0 = kx0 + p["pin_cbore_depth"] - p["pin_head_len"]
    shaft_x0 = kx0 + p["pin_cbore_depth"]
    root = p["barb_slot_root_x"]
    shoulder_x = kxN + p["barb_shoulder_gap"]
    tip_x = shoulder_x + p["barb_len"]
    r_in = p["barb_arm_inner_r"]                            # arm inner radius
    r_beam = p["pin_d"] / 2.0                               # arm outer radius, flush with the shaft
    r_lug = p["barb_d"] / 2.0
    hw = p["barb_beam_w"] / 2.0                            # beam half-width in z
    defl = p["barb_deflection"]

    head = _cyl_x(head_x0, shaft_x0, ay, az, p["pin_head_d"] / 2.0)
    shaft = _cyl_x(shaft_x0, root, ay, az, p["pin_d"] / 2.0)
    core = head.fuse(shaft)

    arms = []
    for sign in (+1.0, -1.0):
        def yspan(a, b):
            lo, hi = sorted((ay + sign * a, ay + sign * b))
            return lo, hi
        y0, y1 = yspan(r_in, r_beam)
        beam = _box(root, tip_x, y0, y1, az - hw, az + hw)
        ly0, ly1 = yspan(r_in, r_lug)
        lug = _box(shoulder_x, shoulder_x + p["barb_lug_len"], ly0, ly1, az - hw, az + hw)
        # lead-in: taper the lug back to the beam line over the remaining length
        ramp = cq.Solid.makeWedge(
            p["barb_lug_len"], abs(ly1 - ly0), 2 * hw, 0.0, 0.0,
            p["barb_lug_len"], abs(ly1 - ly0)) if False else None
        arm = beam.fuse(lug)
        # chamfer the leading face of the lug into a lead-in ramp
        cut = _box(shoulder_x + p["barb_lug_len"] - p["barb_leadin_len"], tip_x + 1.0,
                   *yspan(r_beam, r_lug + 1.0), az - hw - 1.0, az + hw + 1.0)
        wedge_keep = cq.Solid.makeBox(1, 1, 1)  # placeholder, replaced by rotation cut below
        arm = arm.cut(cut)
        lead = _box(shoulder_x + p["barb_lug_len"] - p["barb_leadin_len"],
                    shoulder_x + p["barb_lug_len"], *yspan(r_beam, r_lug),
                    az - hw, az + hw)
        ang = math.degrees(math.atan2(r_lug - r_beam, p["barb_leadin_len"]))
        lead = lead.cut(_box(shoulder_x + p["barb_lug_len"] - p["barb_leadin_len"] - 20.0,
                             shoulder_x + p["barb_lug_len"] - p["barb_leadin_len"],
                             *yspan(r_beam - 1.0, r_lug + 1.0), az - hw - 1, az + hw + 1))
        arm = arm.fuse(_ramp(shoulder_x + p["barb_lug_len"] - p["barb_leadin_len"],
                             shoulder_x + p["barb_lug_len"], ay, az, sign,
                             r_lug, r_beam, hw))
        # Round the arm's outer surface to the lug radius. A rectangular arm has a
        # DIAGONAL larger than its flat span, and a round bore is constrained by
        # the diagonal, not the span - flat corners foul the bore even when the
        # measured width fits.
        # Stepped clip: the beam is rounded to the SHAFT radius so it runs inside
        # the bore, and only the lug is allowed out to the retaining radius. A
        # single clip at the lug radius leaves the beam's corners at
        # sqrt(r_beam^2 + hw^2), which is larger than the bore radius and fouls it.
        clip = _cyl_x(root - 1.0, shoulder_x, ay, az, r_beam).fuse(
            _cyl_x(shoulder_x, tip_x + 1.0, ay, az, r_lug))
        arm = arm.intersect(clip)
        if compressed:
            # Rigid inward translation, not a rotation about the root. Rotating
            # swings the arm's far end across the axis and OUT the other side, so
            # the envelope grows with deflection instead of shrinking. Translation
            # also conserves volume exactly, which a root rotation does not.
            arm = arm.moved(cv.translation((0.0, -sign * defl, 0.0)))
        arms.append(arm)
    out = core
    for a in arms:
        out = out.fuse(a)
    return out


def _ramp(x0, x1, ay, az, sign, r_out, r_in, hw) -> cq.Shape:
    """Triangular lead-in prism: r_out at x0 falling to r_in at x1."""
    pts = [(x0, ay + sign * r_in), (x0, ay + sign * r_out), (x1, ay + sign * r_in)]
    wp = cq.Workplane("XY", origin=(0, 0, az - hw)).polyline(pts).close()
    return wp.extrude(2 * hw).val()


def build_closure_with_latch(p: Dict[str, float], deflect: float = 0.0) -> cq.Shape:
    return build_closure(p).fuse(build_latch(p, deflect))


def build(p: Dict[str, float] = None) -> List[cv.Body]:
    p = p or load_params()
    return [
        cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                build_enclosure(p),
                role=("fixed reference body; cavity, knuckle segments, and the latch "
                      "keeper rib on the front face")),
        cv.Body("BODY-CLOSURE", "closure", "GENERIC_COMPLIANT_POLYMER",
                build_closure_with_latch(p),
                role=("movable closure; plate, front lip, web, knuckle segments, stop "
                      "block, and the integral exterior snap latch"),
                notes=("kinematically rigid everywhere except "
                       "REG-CLOSURE-LATCH-COMPLIANT, which is the beam and its tooth "
                       "and deflects only during release and the closing lead-in")),
        cv.Body("BODY-PIN", "axis pin", "GENERIC_COMPLIANT_POLYMER",
                build_pin(p),
                role=("realizes the rotation axis and its own bilateral axial retention; "
                      "kinematically rigid along FEATURE-PIN-SHAFT, compliant only in "
                      "REGION-PIN-SNAP-COMPLIANT during the declared insertion step"),
                notes=("as-built in the RELAXED configuration, which is the one used for "
                       "every operating state; the compressed configuration is assembly-only")),
    ]


# --------------------------------------------------------------------- states
# The lid angle and the latch deflection each declared state stands for. The
# latch deflection is a PRESCRIBED GEOMETRIC STATE of a declared compliant
# region - never a simulated deformation, and never a force.
STATE_TABLE = {
    "CLOSED_LATCH_ENGAGED":   {"deg": 0.0,  "latch": 0.0, "pin": "relaxed"},
    "CLOSED_LATCH_RELEASED":  {"deg": 0.0,  "latch": 1.0, "pin": "relaxed"},
    "OPENING_STARTED":        {"deg": 6.0,  "latch": 0.0, "pin": "relaxed"},
    "OPEN":                   {"deg": None, "latch": 0.0, "pin": "relaxed"},
    "CLOSING_LATCH_LEADIN":   {"deg": 0.0,  "latch": 1.0, "pin": "relaxed"},
    "CLOSED_REENGAGED":       {"deg": 0.0,  "latch": 0.0, "pin": "relaxed"},
    "PIN_ASSEMBLY_COMPRESSED": {"deg": 0.0, "latch": 0.0, "pin": "compressed"},
    "PIN_ASSEMBLY_RECOVERED": {"deg": 0.0,  "latch": 0.0, "pin": "relaxed"},
}
STATES = list(STATE_TABLE)
SEGMENTS = ["M1_RELEASE", "M2_OPEN", "M3_CLOSE_AND_REENGAGE"]

# How far the lid must swing before the latch tooth is clear of the keeper in Z.
# Below it the beam has to stay deflected; above it the beam is free to recover.
def latch_hold_deg(p: Dict[str, float]) -> float:
    g = latch_geom(p)
    r = math.hypot(g["tooth_y1"] - p["axis_y"], p["tooth_top_z"] - p["axis_z"])
    rise = p["keeper_z1"] - p["tooth_ramp_bot_z"] + 1.0
    return math.degrees(min(rise / r, 0.6))


def state_bodies(bodies: List[cv.Body], p: Dict[str, float], deg: float,
                 latch: float, pin: str = "relaxed") -> List[cv.Body]:
    """Bodies at an arbitrary lid angle and latch deflection.

    Every state and every motion sample goes through here, so a state cannot
    drift from the geometry a segment sweeps through it.
    """
    rot = open_rotation(p, deg)
    out = []
    for b in bodies:
        if b.id == "BODY-CLOSURE":
            shape = (build_closure_with_latch(p, latch * p["latch_deflect"])
                     if latch else b.shape)
            nb = cv.Body(b.id, b.name, b.material_class, shape,
                         installed_as=b.installed_as, role=b.role, notes=b.notes)
            out.append(nb.moved(rot))
        elif b.id == "BODY-PIN" and pin == "compressed":
            nb = cv.Body(b.id, b.name, b.material_class, build_pin(p, compressed=True),
                         installed_as=b.installed_as, role=b.role, notes=b.notes)
            out.append(nb)
        else:
            out.append(b)
    return out


def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    """Rigid placement of a body in a state, for the signature record.

    Configuration changes - a deflected latch beam, a compressed pin barb - are
    not poses and do not appear here. They are recorded separately as declared
    compliant configurations.
    """
    st = STATE_TABLE[state]
    deg = p["open_angle_deg"] if st["deg"] is None else st["deg"]
    if body_id == "BODY-CLOSURE":
        return open_rotation(p, deg)
    return cq.Location()


def configuration(bodies: List[cv.Body], p: Dict[str, float], state: str) -> List[cv.Body]:
    st = STATE_TABLE[state]
    deg = p["open_angle_deg"] if st["deg"] is None else st["deg"]
    return state_bodies(bodies, p, deg, st["latch"], st["pin"])


def continuous_pose(bodies: List[cv.Body], p: Dict[str, float],
                    segment: str, t: float) -> List[cv.Body]:
    """Configuration part-way through a motion segment. t runs 0 -> 1."""
    hold = latch_hold_deg(p)
    if segment == "M1_RELEASE":
        # the beam is deflected outward in place; the lid has not moved yet
        return state_bodies(bodies, p, 0.0, t)
    if segment == "M2_OPEN":
        deg = p["open_angle_deg"] * t
        # the user holds the beam out only until the tooth is above the keeper
        return state_bodies(bodies, p, deg, 1.0 if deg <= hold else 0.0)
    if segment == "M3_CLOSE_AND_REENGAGE":
        deg = p["open_angle_deg"] * (1.0 - t)
        # coming down, the lead-in ramp deflects the beam over the same band and
        # it recovers on its own once the tooth is past
        return state_bodies(bodies, p, deg, 1.0 if 1e-9 < deg <= hold else 0.0)
    raise KeyError(segment)


def probe_pose(bodies: List[cv.Body], p: Dict[str, float], deg: float,
               latch: float = 0.0) -> List[cv.Body]:
    """Configuration at an arbitrary lid angle, including beyond the terminal one.

    Used to show that the stop block is what terminates the rotation, and that
    the latch is what blocks it near closed. This evaluates the same admissible
    model outside its declared range; it exports nothing.
    """
    return state_bodies(bodies, p, deg, latch)


if __name__ == "__main__":
    par = load_params()
    for b in build(par):
        bb = cv.bbox_of(b.shape)
        print(f"{b.id:16s} valid={cv.is_valid(b.shape)!s:5s} "
              f"vol={cv._gprops_volume(b.shape):12.3f} mm^3  "
              f"bbox=({bb['dx']:.2f} x {bb['dy']:.2f} x {bb['dz']:.2f})")
