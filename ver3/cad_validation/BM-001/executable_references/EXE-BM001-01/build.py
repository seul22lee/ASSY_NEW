"""EXE-BM001-01 - rigid rotating closure on a realized knuckle-and-pin axis.

An Oracle-aware executable REFERENCE for BM-001. Its purpose is to establish
that at least one design satisfying the rank-1 source can be built as valid
B-rep solids and moved through its required states without undeclared
volumetric overlap. It is not a demonstration and it proves nothing about
whether the source alone leads anywhere.

Four rigid bodies:

    BODY-ENCLOSURE   fixed shell with a cavity, five knuckle segments and a
                     retention socket
    BODY-CLOSURE     plate, web, two knuckle segments, a guide boss and a stop
                     block
    BODY-PIN         headed shaft with two integral cantilever snap arms
    BODY-BOLT        headed bolt realizing retention

Nothing here depends on a body deforming or on a force being large enough. The
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

    # Retention socket boss, inside the cavity against the front wall.
    bxh = p["bolt_boss_x"] / 2.0
    boss = _box(p["bolt_x"] - bxh, p["bolt_x"] + bxh,
                p["bolt_boss_y0"], p["bolt_boss_y1"], 20.0, bz)
    shell = shell.fuse(boss)
    shell = shell.cut(_cyl_z(p["socket_z"], bz + 1.0, p["bolt_x"], p["bolt_y"],
                             p["bolt_hole_d"] / 2.0))

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
    body = _box(0, bx, 0, p["plate_rear_y"], bz, bz + pt)

    for x0, x1 in knuckle_bands(p)["closure"]:
        body = body.fuse(_cyl_x(x0, x1, ay, az, kr))
        body = body.fuse(_box(x0, x1, p["web_front_y"], ay, bz, bz + pt))
        # Stop block, drawn in the OPEN configuration and rotated back.
        stop_open = _box(x0, x1, p["stop_y0"], p["stop_y1"], p["stop_z0"], p["stop_z1"])
        body = body.fuse(stop_open.moved(open_rotation(p, -p["open_angle_deg"])))

    for x0, x1 in knuckle_bands(p)["closure"]:
        body = body.cut(_cyl_x(x0 - 0.5, x1 + 0.5, ay, az, p["bore_d"] / 2.0))

    bxh = p["bolt_boss_x"] / 2.0
    body = body.fuse(_box(p["bolt_x"] - bxh, p["bolt_x"] + bxh,
                          p["bolt_boss_y0"], p["bolt_boss_y1"],
                          bz + pt, p["lid_boss_top_z"]))
    body = body.cut(_cyl_z(bz - 1.0, p["lid_boss_top_z"] + 1.0,
                           p["bolt_x"], p["bolt_y"], p["bolt_hole_d"] / 2.0))
    return body


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


def build_bolt(p: Dict[str, float]) -> cq.Shape:
    """Built in the RETAINED state: seated on the socket floor."""
    shaft = _cyl_z(p["socket_z"], p["bolt_top_z"], p["bolt_x"], p["bolt_y"],
                   p["bolt_d"] / 2.0)
    knob = _cyl_z(p["bolt_top_z"], p["bolt_top_z"] + p["knob_h"],
                  p["bolt_x"], p["bolt_y"], p["knob_d"] / 2.0)
    return shaft.fuse(knob)


def build(p: Dict[str, float] = None) -> List[cv.Body]:
    p = p or load_params()
    return [
        cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                build_enclosure(p), role="fixed reference body; cavity, knuckle segments, retention socket"),
        cv.Body("BODY-CLOSURE", "closure", "GENERIC_RIGID_POLYMER",
                build_closure(p), role="movable closure; plate, web, knuckle segments, guide boss, stop block"),
        cv.Body("BODY-PIN", "axis pin", "GENERIC_COMPLIANT_POLYMER",
                build_pin(p),
                role=("realizes the rotation axis and its own bilateral axial retention; "
                      "kinematically rigid along FEATURE-PIN-SHAFT, compliant only in "
                      "REGION-PIN-SNAP-COMPLIANT during the declared insertion step"),
                notes=("as-built in the RELAXED configuration, which is the one used for "
                       "every operating state; the compressed configuration is assembly-only")),
        cv.Body("BODY-BOLT", "retention bolt", "GENERIC_RIGID_POLYMER",
                build_bolt(p), role="realizes retention and its release action"),
    ]


# --------------------------------------------------------------------- states
def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    """Transform applied to a body's as-built shape to reach `state`."""
    ident = cq.Location()
    lift = cv.translation((0.0, 0.0, p["release_lift"]))
    if state == "S_CLOSED_RETAINED":
        return ident
    if state == "S_CLOSED_RELEASED":
        return lift if body_id == "BODY-BOLT" else ident
    if state == "S_OPEN":
        rot = open_rotation(p, p["open_angle_deg"])
        if body_id == "BODY-CLOSURE":
            return rot
        if body_id == "BODY-BOLT":
            return rot * lift
        return ident
    raise KeyError(state)


def configuration(bodies: List[cv.Body], p: Dict[str, float], state: str) -> List[cv.Body]:
    return [b.moved(pose(p, b.id, state)) for b in bodies]


def continuous_pose(bodies: List[cv.Body], p: Dict[str, float],
                    segment: str, t: float) -> List[cv.Body]:
    """Configuration part-way through a motion segment. t runs 0 -> 1."""
    out = []
    for b in bodies:
        if segment == "M1_RELEASE":
            loc = cv.translation((0.0, 0.0, p["release_lift"] * t)) if b.id == "BODY-BOLT" else cq.Location()
        elif segment == "M2_OPEN":
            rot = open_rotation(p, p["open_angle_deg"] * t)
            lift = cv.translation((0.0, 0.0, p["release_lift"]))
            if b.id == "BODY-CLOSURE":
                loc = rot
            elif b.id == "BODY-BOLT":
                loc = rot * lift
            else:
                loc = cq.Location()
        else:
            raise KeyError(segment)
        out.append(b.moved(loc))
    return out


def probe_pose(bodies: List[cv.Body], p: Dict[str, float], deg: float) -> List[cv.Body]:
    """Configuration at an arbitrary closure angle, including beyond the terminal one.

    Used only to show that the stop block is what terminates the rotation. This
    evaluates the same admissible model outside its declared range; it exports
    nothing and creates no artifact.
    """
    out = []
    for b in bodies:
        rot = open_rotation(p, deg)
        lift = cv.translation((0.0, 0.0, p["release_lift"]))
        if b.id == "BODY-CLOSURE":
            loc = rot
        elif b.id == "BODY-BOLT":
            loc = rot * lift
        else:
            loc = cq.Location()
        out.append(b.moved(loc))
    return out


STATES = ["S_CLOSED_RETAINED", "S_CLOSED_RELEASED", "S_OPEN"]
SEGMENTS = ["M1_RELEASE", "M2_OPEN"]


if __name__ == "__main__":
    par = load_params()
    for b in build(par):
        bb = cv.bbox_of(b.shape)
        print(f"{b.id:16s} valid={cv.is_valid(b.shape)!s:5s} "
              f"vol={cv._gprops_volume(b.shape):12.3f} mm^3  "
              f"bbox=({bb['dx']:.2f} x {bb['dy']:.2f} x {bb['dz']:.2f})")
