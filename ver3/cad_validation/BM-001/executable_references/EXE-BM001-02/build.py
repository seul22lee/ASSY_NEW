"""EXE-BM001-02 - rigid captive sliding closure on realized rails.

The second Oracle-aware executable REFERENCE for BM-001. It matches no listed
semantic fixture, and that is deliberate: an Oracle that only ever sees designs
drawn from its own fixture list is being tested against itself.

Three rigid bodies:

    BODY-ENCLOSURE   shell with a cavity, a solid top panel over the front half,
                     two ledges and two lipped rails, two raised end walls, and
                     a keeper for the retention cam
    BODY-COVER       flat closure running in the rails, with a keyway bore
    BODY-CAM         quarter-turn retention cam: blade, shaft, knob

Both terminal bounds are realized the same way: an end face of the closure meets
the inner face of an end wall. Neither is a limit imposed on the model.

The honest limitation of this topology is stated up front. A captive sliding
closure cannot uncover the whole of its own aperture - it has to go somewhere,
and the only place is over the rest of the enclosure. This design therefore
declares its usable access as the part of the aperture that is open in the open
state, which is what NRM-BM-001-003 asks for: the access the design declares.
"""
from __future__ import annotations

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
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def _cyl_z(z0, z1, x, y, r) -> cq.Shape:
    return cq.Solid.makeCylinder(r, z1 - z0, pnt=cq.Vector(x, y, z0),
                                 dir=cq.Vector(0, 0, 1))


def geom(p: Dict[str, float]) -> Dict[str, float]:
    """Derived positions, named once so nothing is recomputed inconsistently."""
    g = {}
    g["x_near"] = p["end_wall_x"]                       # inner face of the near end wall
    g["x_far"] = p["box_x"] - p["end_wall_x"]           # inner face of the far end wall
    g["cover_closed_x0"] = g["x_far"] - p["cover_len"]
    g["cover_top"] = p["box_z"] + p["cover_t"]
    g["ledge_far_y"] = p["box_y"] - p["ledge_y"]        # inboard edge of the rear ledge
    g["slot_out_front"] = p["wall"] - p["slot_gap"]     # outboard face of the front channel
    g["slot_out_rear"] = p["box_y"] - p["wall"] + p["slot_gap"]
    g["keeper_x0"] = p["cam_x"] - 12.0
    g["keeper_y1"] = p["cam_y"] + 10.0
    g["blade_top"] = p["ledge_z0"] - p["blade_gap"]
    g["blade_bot"] = g["blade_top"] - p["blade_t"]
    return g


def keyway(p: Dict[str, float], hole_d: float, z0: float, z1: float) -> cq.Shape:
    """Circular bore plus the two radial extensions the blade passes through."""
    k = p["keyway_clear"]
    bore = _cyl_z(z0, z1, p["cam_x"], p["cam_y"], hole_d / 2.0)
    slot = _box(p["cam_x"] - (p["blade_len"] + k) / 2.0, p["cam_x"] + (p["blade_len"] + k) / 2.0,
                p["cam_y"] - (p["blade_w"] + k) / 2.0, p["cam_y"] + (p["blade_w"] + k) / 2.0,
                z0, z1)
    return bore.fuse(slot)


def lock_rotation(p: Dict[str, float], deg: float) -> cq.Location:
    return cv.rotation((p["cam_x"], p["cam_y"], 0.0), (0.0, 0.0, 1.0), deg)


# --------------------------------------------------------------------- bodies
def build_enclosure(p: Dict[str, float]) -> cq.Shape:
    g = geom(p)
    w, bx, by, bz = p["wall"], p["box_x"], p["box_y"], p["box_z"]

    shell = _box(0, bx, 0, by, 0, bz).cut(_box(w, bx - w, w, by - w, w, bz))
    # Solid top panel over the front of the interior. The aperture is what is
    # left of the top, and the panel is what the closure parks over when open.
    shell = shell.fuse(_box(w, p["deck_x1"], w, by - w, p["deck_z0"], bz))
    # Ledges the closure runs on.
    shell = shell.fuse(_box(w, bx - w, w, p["ledge_y"], p["ledge_z0"], bz))
    shell = shell.fuse(_box(w, bx - w, g["ledge_far_y"], by - w, p["ledge_z0"], bz))
    # Keeper for the retention cam.
    shell = shell.fuse(_box(g["keeper_x0"], bx - w, w, g["keeper_y1"],
                            p["ledge_z0"], bz))
    # Raised end walls: their inner faces are the two terminal bounds.
    shell = shell.fuse(_box(0, g["x_near"], 0, by, bz, p["rail_top_z"]))
    shell = shell.fuse(_box(g["x_far"], bx, 0, by, bz, p["rail_top_z"]))

    # Rails: a full-height block along each side, then the running channel cut
    # out of it, then the lips relieved over the loading zone.
    for y0, y1, s0, s1 in ((0.0, p["ledge_y"], g["slot_out_front"], p["ledge_y"] + p["slot_gap"]),
                           (g["ledge_far_y"], by, g["ledge_far_y"] - p["slot_gap"], g["slot_out_rear"])):
        shell = shell.fuse(_box(0, bx, y0, y1, bz, p["rail_top_z"]))
        shell = shell.cut(_box(g["x_near"], g["x_far"], s0, s1, bz, p["lip_z0"]))
        shell = shell.cut(_box(g["x_near"], p["lip_relief_x1"], s0, s1,
                               p["lip_z0"], p["rail_top_z"] + 1.0))

    shell = shell.cut(keyway(p, p["keeper_hole_d"], p["ledge_z0"] - 1.0, bz + 1.0))
    return shell


def build_cover(p: Dict[str, float]) -> cq.Shape:
    """Built in the CLOSED position."""
    g = geom(p)
    body = _box(g["cover_closed_x0"], g["x_far"], p["wall"], p["box_y"] - p["wall"],
                p["box_z"], g["cover_top"])
    return body.cut(keyway(p, p["cover_hole_d"], p["box_z"] - 1.0, g["cover_top"] + 1.0))


def build_cam(p: Dict[str, float]) -> cq.Shape:
    """Built in the INSERTION orientation: blade aligned with the keyway.

    The locked state is a quarter turn from here, so 'locked' is a pose rather
    than a shape, and the same solid is demonstrably able to pass through the
    keyway it later cannot pass through.
    """
    g = geom(p)
    blade = _box(p["cam_x"] - p["blade_len"] / 2.0, p["cam_x"] + p["blade_len"] / 2.0,
                 p["cam_y"] - p["blade_w"] / 2.0, p["cam_y"] + p["blade_w"] / 2.0,
                 g["blade_bot"], g["blade_top"])
    shaft = _cyl_z(g["blade_top"], g["cover_top"], p["cam_x"], p["cam_y"],
                   p["cam_shaft_d"] / 2.0)
    knob = _cyl_z(g["cover_top"], g["cover_top"] + p["knob_h"], p["cam_x"], p["cam_y"],
                  p["knob_d"] / 2.0)
    return blade.fuse(shaft).fuse(knob)


def build(p: Dict[str, float] = None) -> List[cv.Body]:
    p = p or load_params()
    return [
        cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                build_enclosure(p),
                role="fixed reference body; cavity, top panel, ledges, lipped rails, end walls, cam keeper"),
        cv.Body("BODY-COVER", "sliding closure", "GENERIC_RIGID_POLYMER",
                build_cover(p), role="movable closure running in the rails"),
        cv.Body("BODY-CAM", "quarter-turn retention cam", "GENERIC_RIGID_POLYMER",
                build_cam(p), role="realizes retention and its release action",
                notes="as-built in the insertion orientation; the locked state is a quarter turn from it"),
    ]


# --------------------------------------------------------------------- states
def _park(p: Dict[str, float]) -> cq.Location:
    return cv.translation((0.0, -p["cam_park_y"], p["cam_lift"]))


def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    ident = cq.Location()
    if state == "S_CLOSED_RETAINED":
        return lock_rotation(p, p["lock_angle_deg"]) if body_id == "BODY-CAM" else ident
    if state == "S_CLOSED_RELEASED":
        return _park(p) if body_id == "BODY-CAM" else ident
    if state == "S_OPEN":
        if body_id == "BODY-CAM":
            return _park(p)
        if body_id == "BODY-COVER":
            return cv.translation((-p["travel"], 0.0, 0.0))
        return ident
    raise KeyError(state)


def configuration(bodies: List[cv.Body], p: Dict[str, float], state: str) -> List[cv.Body]:
    return [b.moved(pose(p, b.id, state)) for b in bodies]


def continuous_pose(bodies: List[cv.Body], p: Dict[str, float],
                    segment: str, t: float) -> List[cv.Body]:
    out = []
    for b in bodies:
        loc = cq.Location()
        if segment == "M1_UNLOCK":
            if b.id == "BODY-CAM":
                loc = lock_rotation(p, p["lock_angle_deg"] * (1.0 - t))
        elif segment == "M2_WITHDRAW":
            if b.id == "BODY-CAM":
                if t <= 0.5:
                    loc = cv.translation((0.0, 0.0, p["cam_lift"] * (t / 0.5)))
                else:
                    loc = cv.translation((0.0, -p["cam_park_y"] * ((t - 0.5) / 0.5),
                                          p["cam_lift"]))
        elif segment == "M3_OPEN":
            if b.id == "BODY-COVER":
                loc = cv.translation((-p["travel"] * t, 0.0, 0.0))
            elif b.id == "BODY-CAM":
                loc = _park(p)
        else:
            raise KeyError(segment)
        out.append(b.moved(loc))
    return out


def probe_pose(bodies: List[cv.Body], p: Dict[str, float], slide: float) -> List[cv.Body]:
    """Configuration at an arbitrary slide distance, including beyond the bounds.

    Used only to show that the end walls are what terminate the slide. Evaluates
    the same admissible model outside its declared range; exports nothing.
    """
    out = []
    for b in bodies:
        loc = cq.Location()
        if b.id == "BODY-COVER":
            loc = cv.translation((-slide, 0.0, 0.0))
        elif b.id == "BODY-CAM":
            loc = _park(p)
        out.append(b.moved(loc))
    return out


STATES = ["S_CLOSED_RETAINED", "S_CLOSED_RELEASED", "S_OPEN"]
SEGMENTS = ["M1_UNLOCK", "M2_WITHDRAW", "M3_OPEN"]


if __name__ == "__main__":
    par = load_params()
    for b in build(par):
        bb = cv.bbox_of(b.shape)
        print("%-16s valid=%-5s vol=%11.3f  bbox=(%.2f x %.2f x %.2f)  z[%.1f,%.1f]"
              % (b.id, cv.is_valid(b.shape), cv._gprops_volume(b.shape),
                 bb["dx"], bb["dy"], bb["dz"], bb["zmin"], bb["zmax"]))
