"""EXE-BM002-01 - enclosed hand-cranked platform lift, in-line slider-crank.

An Oracle-aware executable REFERENCE for BM-002. Its purpose is to establish that
at least one design satisfying the rank-1 source can be built as valid B-rep
solids and driven through a complete 0-360 degree crank cycle without undeclared
volumetric overlap, delivering a MEASURED 90 mm of platform travel. It is not a
demonstration and it proves nothing about whether the source alone leads anywhere.

Seven product bodies and no others:

    BODY-HOUSING            base, walls, mechanism cavity, open top for payload
                            access, first and second crank-shaft journal lands,
                            two integral vertical platform guide channels
    BODY-REAR-PANEL         closes the +X side after internal assembly, and
                            carries the integral lands that stop both joint pins
                            escaping axially
    BODY-PLATFORM           payload support plate, two guide followers, and the
                            clevis that receives the platform joint pin
    BODY-CRANK-SHAFT        exterior handle grip, large-diameter hub that both
                            crosses the housing boundary and runs in the two
                            journal lands, thrust collar, internal crank arm
    BODY-CONNECTING-ROD     fixed-length link, 85 mm between bore centres
    BODY-CRANK-JOINT-PIN    revolute joint between crank arm and rod
    BODY-PLATFORM-JOINT-PIN revolute joint between rod and platform clevis

SCENARIO-PAYLOAD-1KG is a scenario object, not a product body. It is never built
here and never appears in the body list.

Two things about this geometry are worth stating before reading it.

The crank is OVERHUNG - one arm, both journal lands on the -X side of the
connecting rod. That is forced, not chosen. A two-web crankshaft would have to
join its webs across the crank axis, and in the crank's own rotating frame the
connecting rod sweeps a full turn about the crank pin, so it sweeps THROUGH the
axis. Any material joining two webs there is struck by the rod. The consequence is
that the second journal land could not be put on the rear panel: the shaft cannot
extend past the rod. It is a second land inside the housing instead, separated
from the first by a relief bore so the two are physically distinct. See
DESIGN_AND_OPERATION_RATIONALE.md, change CHG-02.

Nothing here deforms. Every joint is a clearance fit retained by a pin head on one
side and a rear-panel land on the other, so this reference declares no compliant
region, no snap fit and no interference fit, and therefore claims nothing about
insertion force or strain.
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


# --------------------------------------------------------------- primitives
def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def _cyl_x(x0, x1, y, z, r) -> cq.Shape:
    """Cylinder with its axis along +X, centred on (y, z)."""
    return cq.Solid.makeCylinder(r, x1 - x0, pnt=cq.Vector(x0, y, z),
                                 dir=cq.Vector(1, 0, 0))


def _one_solid(shape: cq.Shape) -> cq.Shape:
    """Collapse a boolean result to a single cleaned solid.

    Fusing touching primitives can leave coincident faces behind, which makes
    BRepCheck_Analyzer's answer depend on the order the primitives were fused
    rather than on the shape. clean() removes them, so validity is a property of
    the body.
    """
    return cq.Workplane("XY").add(shape).clean().val()


# ------------------------------------------------------- derived dimensions
def geom(p: Dict[str, float]) -> Dict[str, float]:
    """Every dimension that follows from the parameters, in one place.

    Nothing downstream may re-derive one of these locally; a second derivation is
    how a model acquires two versions of the same number.
    """
    ay, az = p["crank_axis_y"], p["crank_axis_z"]
    R, L = p["crank_radius"], p["rod_length"]

    g: Dict[str, float] = {}
    g["axis_y"], g["axis_z"] = ay, az
    g["crank_pin_z_bottom"] = az - R                       # BDC
    g["crank_pin_z_top"] = az + R                          # TDC
    g["plat_pin_z_bottom"] = az - R + L
    g["plat_pin_z_top"] = az + R + L
    g["travel"] = 2.0 * R
    g["max_rod_angle_deg"] = math.degrees(math.asin(R / L))

    # platform, at the BOTTOM state (the as-built configuration)
    g["plate_z0"] = g["plat_pin_z_bottom"] + p["clevis_offset"]
    g["plate_z1"] = g["plate_z0"] + p["plate_t"]
    g["support_z_bottom"] = g["plate_z1"]
    g["support_z_top"] = g["plate_z1"] + g["travel"]
    g["rim_z"] = g["support_z_top"] + p["top_clearance"]

    # guide channels
    g["guide_z0"] = g["plate_z0"] - p["guide_z_below"]
    g["follower_z0"] = g["plate_z0"] - p["follower_over"]
    g["follower_z1"] = g["plate_z1"] + p["follower_over"]
    g["boss_f_y1"] = p["wall_y"] + p["guide_boss_t"]                 # front boss inner face
    g["groove_f_y0"] = g["boss_f_y1"] - p["guide_groove_depth"]      # front channel floor
    g["boss_b_y0"] = p["housing_y"] - p["wall_y"] - p["guide_boss_t"]
    g["groove_b_y1"] = g["boss_b_y0"] + p["guide_groove_depth"]
    g["groove_x0"] = p["follower_x0"] - p["guide_side_clearance"]
    g["groove_x1"] = p["follower_x1"] + p["guide_side_clearance"]
    g["plate_y0"] = g["boss_f_y1"] + p["plate_edge_gap"]
    g["plate_y1"] = g["boss_b_y0"] - p["plate_edge_gap"]
    g["foll_f_y0"] = g["groove_f_y0"] + p["guide_depth_clearance"]
    g["foll_b_y1"] = g["groove_b_y1"] - p["guide_depth_clearance"]

    # journals and bores
    g["hub_r"] = p["hub_d"] / 2.0
    g["journal_bore_r"] = g["hub_r"] + p["journal_clearance"]
    g["relief_bore_r"] = g["journal_bore_r"] + p["relief_extra_r"]
    g["j2_boss_r"] = p["j2_boss_d"] / 2.0
    g["pin_r"] = p["pin_d"] / 2.0
    g["pin_bore_r"] = g["pin_r"] + p["pin_bore_clearance"]
    g["pin_head_r"] = p["pin_head_d"] / 2.0
    g["collar_r"] = p["collar_d"] / 2.0
    g["arm_outer_r"] = R + p["arm_pin_boss_r"]

    # rear panel
    g["panel_x0"] = p["housing_x1"]
    g["panel_x1"] = p["housing_x1"] + p["panel_t"]
    g["land_x0"] = p["housing_x1"] - p["land_t"]
    g["crank_land_gap"] = g["land_x0"] - p["crank_pin_head_x1"]
    g["plat_land_gap"] = g["land_x0"] - p["plat_pin_head_x1"]
    g["plat_land_z0"] = g["plat_pin_z_bottom"] - p["plat_land_z_below"]
    g["plat_land_z1"] = g["plat_pin_z_top"] + p["plat_land_z_above"]

    # axial location of the crank shaft
    g["shaft_pull_out_gap"] = p["collar_x0"] - p["j2_x1"]      # -X free travel
    g["shaft_push_in_gap"] = p["rod_x0"] - p["arm_x1"]         # +X free travel, first stage

    # payload
    g["payload_x0"] = (p["plate_x0"] + p["plate_x1"] - p["payload_x"]) / 2.0
    g["payload_x1"] = g["payload_x0"] + p["payload_x"]
    g["payload_y0"] = ay - p["payload_y"] / 2.0
    g["payload_y1"] = ay + p["payload_y"] / 2.0
    return g


# ------------------------------------------------------------------ bodies
def build_housing(p: Dict[str, float], *, guides: str = "both",
                  j2: bool = True) -> cq.Shape:
    """Base, walls, cavity, two journal lands and two vertical guide channels.

    `guides` selects which guide channels exist and `j2` whether the second journal
    land is bored to size or opened out to the relief diameter. Neither is a product
    option: the reduced variants exist only so a negative control can remove a
    feature in memory and show that the corresponding check reports it.
    """
    g = geom(p)
    s = _box(0.0, p["housing_x1"], 0.0, p["housing_y"], 0.0, g["rim_z"])
    # cavity: open at +X (closed later by the rear panel) and open at the top
    s = s.cut(_box(p["wall_x"], p["housing_x1"] + 10.0,
                   p["wall_y"], p["housing_y"] - p["wall_y"],
                   p["floor_z"], g["rim_z"] + 10.0))

    # internal journal boss carrying the second journal land
    s = s.fuse(_cyl_x(p["wall_x"], p["j2_x1"], g["axis_y"], g["axis_z"], g["j2_boss_r"]))

    # guide bosses standing off the front and back inner walls
    if guides in ("both", "front"):
        s = s.fuse(_box(p["guide_x0"], p["guide_x1"], p["wall_y"], g["boss_f_y1"],
                        g["guide_z0"], g["rim_z"]))
    if guides in ("both", "back"):
        s = s.fuse(_box(p["guide_x0"], p["guide_x1"], g["boss_b_y0"],
                        p["housing_y"] - p["wall_y"], g["guide_z0"], g["rim_z"]))
    s = _one_solid(s)

    # the channels themselves
    if guides in ("both", "front"):
        s = s.cut(_box(g["groove_x0"], g["groove_x1"], g["groove_f_y0"], g["boss_f_y1"],
                       g["guide_z0"], g["rim_z"] + 10.0))
    if guides in ("both", "back"):
        s = s.cut(_box(g["groove_x0"], g["groove_x1"], g["boss_b_y0"], g["groove_b_y1"],
                       g["guide_z0"], g["rim_z"] + 10.0))

    # journal land 1 (through the -X wall, this is the boundary crossing),
    # a relief that makes the two lands physically distinct, then land 2
    s = s.cut(_cyl_x(-1.0, p["wall_x"], g["axis_y"], g["axis_z"], g["journal_bore_r"]))
    s = s.cut(_cyl_x(p["wall_x"], p["relief_x1"], g["axis_y"], g["axis_z"],
                     g["relief_bore_r"]))
    s = s.cut(_cyl_x(p["relief_x1"], p["j2_x1"], g["axis_y"], g["axis_z"],
                     g["journal_bore_r"] if j2 else g["relief_bore_r"]))
    return _one_solid(s)


def build_rear_panel(p: Dict[str, float], *,
                     crank_land: bool = True, plat_land: bool = True) -> cq.Shape:
    """Closes the +X side and carries the two integral pin-retention lands.

    The land flags exist only for negative controls.
    """
    g = geom(p)
    s = _box(g["panel_x0"], g["panel_x1"], 0.0, p["housing_y"], 0.0, g["rim_z"])
    if crank_land:
        ring = _cyl_x(g["land_x0"], g["panel_x0"], g["axis_y"], g["axis_z"],
                      p["crank_land_r1"])
        ring = ring.cut(_cyl_x(g["land_x0"] - 1.0, g["panel_x0"] + 1.0,
                               g["axis_y"], g["axis_z"], p["crank_land_r0"]))
        s = s.fuse(ring)
    if plat_land:
        s = s.fuse(_box(g["land_x0"], g["panel_x0"],
                        g["axis_y"] - p["plat_land_hw"], g["axis_y"] + p["plat_land_hw"],
                        g["plat_land_z0"], g["plat_land_z1"]))
    return _one_solid(s)


def build_platform(p: Dict[str, float], *, followers: str = "both",
                   clevis: bool = True, plate_inset: float = 0.0) -> cq.Shape:
    """Support plate, two guide followers, and the clevis under the plate.

    Built in the BOTTOM configuration; every other state is a rigid translation of
    it. The follower, clevis and plate_inset flags exist only for negative
    controls: `followers` removes a follower, and `plate_inset` pulls the plate
    edges away from the guide bosses so that a platform with no followers has no
    guide engagement of any kind left.
    """
    g = geom(p)
    ay = g["axis_y"]
    s = _box(p["plate_x0"], p["plate_x1"], g["plate_y0"] + plate_inset,
             g["plate_y1"] - plate_inset, g["plate_z0"], g["plate_z1"])
    if followers in ("both", "front"):
        s = s.fuse(_box(p["follower_x0"], p["follower_x1"], g["foll_f_y0"], g["plate_y0"],
                        g["follower_z0"], g["follower_z1"]))
    if followers in ("both", "back"):
        s = s.fuse(_box(p["follower_x0"], p["follower_x1"], g["plate_y1"], g["foll_b_y1"],
                        g["follower_z0"], g["follower_z1"]))
    if clevis:
        zc = g["plat_pin_z_bottom"]
        for x0, x1 in ((p["lug_a_x0"], p["lug_a_x1"]), (p["lug_b_x0"], p["lug_b_x1"])):
            lug = _cyl_x(x0, x1, ay, zc, p["lug_r"])
            lug = lug.fuse(_box(x0, x1, ay - p["lug_r"], ay + p["lug_r"],
                                zc, g["plate_z0"]))
            s = s.fuse(lug)
        s = _one_solid(s)
        s = s.cut(_cyl_x(p["lug_a_x0"] - 1.0, p["lug_b_x1"] + 1.0, ay, zc, g["pin_bore_r"]))
    return _one_solid(s)


def build_crank_shaft(p: Dict[str, float], *, handle: bool = True,
                      crossing: bool = True, arm: bool = True,
                      hub_interference: float = 0.0) -> cq.Shape:
    """Handle grip, hub, thrust collar and crank arm, as one solid.

    Built at BOTTOM dead centre: the crank pin and the handle grip both point
    straight down. Every other angle is a rigid rotation about the shaft axis.

    The flags exist only for negative controls: `handle` removes the exterior
    input, `crossing` pulls the whole shaft inboard so nothing crosses the housing
    wall, `arm` removes the crank arm, and `hub_interference` grows the hub past
    its journal bore.
    """
    g = geom(p)
    ay, az = g["axis_y"], g["axis_z"]
    zp = g["crank_pin_z_bottom"]

    hub_x0 = p["hub_x0"] if crossing else p["wall_x"] + 2.0
    s = _cyl_x(hub_x0, p["hub_x1"], ay, az, g["hub_r"] + hub_interference)
    if handle and crossing:
        s = s.fuse(_cyl_x(p["grip_x0"], p["hub_x0"], ay, az - p["grip_offset"],
                          p["grip_d"] / 2.0))
    s = s.fuse(_cyl_x(p["collar_x0"], p["collar_x1"], ay, az, g["collar_r"]))
    if arm:
        a = _cyl_x(p["arm_x0"], p["arm_x1"], ay, az, p["arm_hub_r"])
        a = a.fuse(_cyl_x(p["arm_x0"], p["arm_x1"], ay, zp, p["arm_pin_boss_r"]))
        a = a.fuse(_box(p["arm_x0"], p["arm_x1"],
                        ay - p["arm_pin_boss_r"], ay + p["arm_pin_boss_r"], zp, az))
        s = s.fuse(a)
        s = _one_solid(s)
        s = s.cut(_cyl_x(p["arm_x0"] - 1.0, p["arm_x1"] + 1.0, ay, zp, g["pin_bore_r"]))
    return _one_solid(s)


def build_connecting_rod(p: Dict[str, float], *, length_error: float = 0.0) -> cq.Shape:
    """Fixed-length link. Built at BOTTOM, where it stands vertical.

    `length_error` exists only for the negative control that changes the centre
    distance.
    """
    g = geom(p)
    ay = g["axis_y"]
    z0 = g["crank_pin_z_bottom"]
    z1 = g["plat_pin_z_bottom"] + length_error
    s = _cyl_x(p["rod_x0"], p["rod_x1"], ay, z0, p["rod_eye_r"])
    s = s.fuse(_cyl_x(p["rod_x0"], p["rod_x1"], ay, z1, p["rod_eye_r"]))
    s = s.fuse(_box(p["rod_x0"], p["rod_x1"], ay - p["rod_eye_r"], ay + p["rod_eye_r"],
                    z0, z1))
    s = _one_solid(s)
    s = s.cut(_cyl_x(p["rod_x0"] - 1.0, p["rod_x1"] + 1.0, ay, z0, g["pin_bore_r"]))
    s = s.cut(_cyl_x(p["rod_x0"] - 1.0, p["rod_x1"] + 1.0, ay, z1, g["pin_bore_r"]))
    return _one_solid(s)


def _pin(p: Dict[str, float], x0: float, x1: float, head_x1: float,
         y: float, z: float, *, head: bool = True) -> cq.Shape:
    g = geom(p)
    s = _cyl_x(x0, x1, y, z, g["pin_r"])
    if head:
        s = s.fuse(_cyl_x(x1, head_x1, y, z, g["pin_head_r"]))
    return _one_solid(s)


def build_crank_joint_pin(p: Dict[str, float], *, head: bool = True) -> cq.Shape:
    g = geom(p)
    return _pin(p, p["arm_x0"], p["rod_x1"], p["crank_pin_head_x1"],
                g["axis_y"], g["crank_pin_z_bottom"], head=head)


def build_platform_joint_pin(p: Dict[str, float], *, head: bool = True) -> cq.Shape:
    g = geom(p)
    return _pin(p, p["lug_a_x0"], p["lug_b_x1"], p["plat_pin_head_x1"],
                g["axis_y"], g["plat_pin_z_bottom"], head=head)


def build(p: Dict[str, float] = None) -> List[cv.Body]:
    p = p or load_params()
    return [
        cv.Body("BODY-HOUSING", "housing", "GENERIC_RIGID_POLYMER",
                build_housing(p),
                role=("fixed reference body; base and enclosure walls, mechanism "
                      "cavity, open top for payload access, first and second "
                      "crank-shaft journal lands, two integral vertical platform "
                      "guide channels, and the support-surface reaction at z = 0")),
        cv.Body("BODY-REAR-PANEL", "rear panel", "GENERIC_RIGID_POLYMER",
                build_rear_panel(p),
                role=("closes the +X side after internal assembly; carries the "
                      "annular land that stops the crank joint pin escaping in +X "
                      "and the vertical land that stops the platform joint pin "
                      "escaping in +X")),
        cv.Body("BODY-PLATFORM", "platform", "GENERIC_RIGID_POLYMER",
                build_platform(p),
                role=("payload support plate, two guide followers, and the clevis "
                      "that carries the platform joint pin"),
                notes="as-built in the BOTTOM state; every state is a rigid translation of it"),
        cv.Body("BODY-CRANK-SHAFT", "crank shaft", "GENERIC_RIGID_POLYMER",
                build_crank_shaft(p),
                role=("exterior handle grip outside the housing, large-diameter hub "
                      "that both crosses the housing boundary and runs in both "
                      "journal lands, thrust collar, and the internal crank arm"),
                notes="as-built at bottom dead centre; every state is a rigid rotation about the shaft axis"),
        cv.Body("BODY-CONNECTING-ROD", "connecting rod", "GENERIC_RIGID_POLYMER",
                build_connecting_rod(p),
                role="fixed-length link between the crank joint and the platform joint",
                notes="as-built at bottom dead centre, where it stands vertical"),
        cv.Body("BODY-CRANK-JOINT-PIN", "crank joint pin", "GENERIC_RIGID_POLYMER",
                build_crank_joint_pin(p),
                role=("realizes the revolute joint between the crank arm and the "
                      "connecting rod; its head is the -X axial stop")),
        cv.Body("BODY-PLATFORM-JOINT-PIN", "platform joint pin", "GENERIC_RIGID_POLYMER",
                build_platform_joint_pin(p),
                role=("realizes the revolute joint between the connecting rod and "
                      "the platform clevis; its head is the -X axial stop")),
    ]


# ---------------------------------------------------------------- kinematics
# theta is the crank angle in degrees, 0 at bottom dead centre, increasing so that
# the crank pin moves toward +Y first. The relation below is used to POSE the
# bodies. It is not evidence that the physical chain exists; that is established
# by the geometry above and measured by validate.py.
STATE_TABLE = {
    "CRANK_0_BOTTOM":    0.0,
    "CRANK_45_RISING":   45.0,
    "CRANK_90_RISING":   90.0,
    "CRANK_135_RISING":  135.0,
    "CRANK_180_TOP":     180.0,
    "CRANK_225_LOWERING": 225.0,
    "CRANK_270_LOWERING": 270.0,
    "CRANK_315_LOWERING": 315.0,
    "CRANK_360_BOTTOM":  360.0,
}
STATES = list(STATE_TABLE)
SEGMENTS = ["M1_000_090", "M2_090_180", "M3_180_270", "M4_270_360"]
SEGMENT_RANGE = {"M1_000_090": (0.0, 90.0), "M2_090_180": (90.0, 180.0),
                 "M3_180_270": (180.0, 270.0), "M4_270_360": (270.0, 360.0)}


def crank_pin_centre(p: Dict[str, float], deg: float):
    g = geom(p)
    t = math.radians(deg)
    return (g["axis_y"] + p["crank_radius"] * math.sin(t),
            g["axis_z"] - p["crank_radius"] * math.cos(t))


def platform_pin_z(p: Dict[str, float], deg: float) -> float:
    t = math.radians(deg)
    R, L = p["crank_radius"], p["rod_length"]
    _, zc = crank_pin_centre(p, deg)
    return zc + math.sqrt(L * L - (R * math.sin(t)) ** 2)


def rod_angle_deg(p: Dict[str, float], deg: float) -> float:
    """Connecting-rod angle from vertical, signed, in degrees."""
    R, L = p["crank_radius"], p["rod_length"]
    return math.degrees(math.asin(R * math.sin(math.radians(deg)) / L))


def pose_at(p: Dict[str, float], body_id: str, deg: float) -> cq.Location:
    g = geom(p)
    ay, az = g["axis_y"], g["axis_z"]
    if body_id in ("BODY-HOUSING", "BODY-REAR-PANEL"):
        return cq.Location()
    if body_id in ("BODY-CRANK-SHAFT", "BODY-CRANK-JOINT-PIN"):
        return cv.rotation((0.0, ay, az), (1.0, 0.0, 0.0), deg)
    if body_id == "BODY-CONNECTING-ROD":
        yc, zc = crank_pin_centre(p, deg)
        return (cv.translation((0.0, yc - ay, zc - g["crank_pin_z_bottom"]))
                * cv.rotation((0.0, ay, g["crank_pin_z_bottom"]), (1.0, 0.0, 0.0),
                              rod_angle_deg(p, deg)))
    if body_id in ("BODY-PLATFORM", "BODY-PLATFORM-JOINT-PIN"):
        return cv.translation((0.0, 0.0, platform_pin_z(p, deg) - g["plat_pin_z_bottom"]))
    raise KeyError(body_id)


def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    return pose_at(p, body_id, STATE_TABLE[state])


def bodies_at(bodies: List[cv.Body], p: Dict[str, float], deg: float) -> List[cv.Body]:
    """Every state and every motion sample goes through here, so a state cannot
    drift from the geometry a segment sweeps through it."""
    return [b.moved(pose_at(p, b.id, deg)) for b in bodies]


def configuration(bodies: List[cv.Body], p: Dict[str, float], state: str) -> List[cv.Body]:
    return bodies_at(bodies, p, STATE_TABLE[state])


def continuous_pose(bodies: List[cv.Body], p: Dict[str, float],
                    segment: str, t: float) -> List[cv.Body]:
    a, b = SEGMENT_RANGE[segment]
    return bodies_at(bodies, p, a + (b - a) * t)


if __name__ == "__main__":
    par = load_params()
    gg = geom(par)
    for b in build(par):
        bb = cv.bbox_of(b.shape)
        print("%-24s valid=%-5s vol=%12.3f mm^3  bbox=(%.2f x %.2f x %.2f)"
              % (b.id, cv.is_valid(b.shape), cv._gprops_volume(b.shape),
                 bb["dx"], bb["dy"], bb["dz"]))
    print("---")
    for k in ("crank_pin_z_bottom", "crank_pin_z_top", "plat_pin_z_bottom",
              "plat_pin_z_top", "support_z_bottom", "support_z_top", "travel",
              "rim_z", "max_rod_angle_deg", "arm_outer_r", "shaft_pull_out_gap",
              "crank_land_gap", "plat_land_gap"):
        print("%-22s %10.4f" % (k, gg[k]))
