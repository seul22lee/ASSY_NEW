"""EXE-BM001-02 - snap-riveted captive sliding cover.

Three bodies:

    BODY-ENCLOSURE   shell, cavity, solid top panel, two ledges, two guide walls,
                     the rivet slot, the latch keeper bridge
    BODY-COVER       plate with an integral compliant latch beam cut from it
    BODY-RIVET       snap rivet: head, shaft, two cantilever arms with lugs

THE ARCHITECTURE, AND WHAT IT IS NOT

    Every part has one job. The ledges carry the cover, the guide walls locate it
    sideways, the rivet holds it down, the slot ends bound the travel, the latch
    holds it shut.

    There are no retaining lips. Two earlier versions had them - inherited from
    the quarter-turn cam design - and they cost more than they gave: a lipped
    channel closed at both ends cannot be entered by any translation, so the
    cover needed a relief cut in the lips and a loading position beyond its own
    open bound just to get in. Once the rivet is doing the retaining, the lips
    have no remaining job, so they are gone and the assembly is two straight
    presses.

ASSEMBLY, IN FULL

    1. drop the cover between the guide walls onto the ledges - nothing
       obstructs it, because nothing overhangs it
    2. press the rivet down through the cover bore and the slot; its arms deflect
       inward on the lead-in and recover under the ledge

    After step 2 the cover is captive at every position of its travel, full open
    included, and the rivet cannot withdraw because its recovered lugs are wider
    than the slot they came through.
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
    return cq.Solid.makeCylinder(r, z1 - z0, pnt=cq.Vector(x, y, z0), dir=cq.Vector(0, 0, 1))


def geom(p: Dict[str, float]) -> Dict[str, float]:
    g = {}
    g["cover_top"] = p["box_z"] + p["cover_t"]
    g["cover_closed_x0"] = p["far_wall_x"] - p["cover_len"]
    g["cover_open_x0"] = g["cover_closed_x0"] - p["travel"]
    g["ledge_far_y"] = p["box_y"] - p["ledge_y"]
    g["plate_y0"] = p["wall"] + p["guide_gap"]
    g["plate_y1"] = p["box_y"] - p["wall"] - p["guide_gap"]
    g["rivet_closed_x"] = g["cover_closed_x0"] + p["rivet_offset_x"]
    g["rivet_open_x"] = g["rivet_closed_x"] - p["travel"]
    g["slot_x0"] = g["rivet_open_x"] - p["slot_w"] / 2.0
    g["slot_x1"] = g["rivet_closed_x"] + p["slot_w"] / 2.0
    g["head_top"] = g["cover_top"]
    g["head_bot"] = g["cover_top"] - p["rivet_head_h"]
    g["lug_top"] = p["ledge_z0"] - p["barb_gap"]
    g["lug_bot"] = g["lug_top"] - p["barb_lug_len"]
    g["tip_z"] = g["lug_bot"] - p["barb_leadin_len"]
    g["latch_y1"] = p["latch_y0"] + p["latch_w"]
    g["latch_tip_x"] = g["cover_closed_x0"]
    g["latch_root_x"] = g["cover_closed_x0"] + p["latch_len"]
    g["hook_z1"] = g["cover_top"] + p["latch_hook_h"]
    return g


# --------------------------------------------------------------------- bodies
def build_enclosure(p: Dict[str, float]) -> cq.Shape:
    g = geom(p)
    w, bx, by, bz = p["wall"], p["box_x"], p["box_y"], p["box_z"]

    shell = _box(0, bx, 0, by, 0, bz).cut(_box(w, bx - w, w, by - w, w, bz))
    # solid top panel: the surface the cover parks over when open
    shell = shell.fuse(_box(w, p["deck_x1"], w, by - w, p["deck_z0"], bz))
    # the two ledges the cover runs on
    shell = shell.fuse(_box(w, bx - w, w, p["ledge_y"], p["ledge_z0"], bz))
    shell = shell.fuse(_box(w, bx - w, g["ledge_far_y"], by - w, p["ledge_z0"], bz))
    # guide walls: side location only, nothing overhangs the cover
    shell = shell.fuse(_box(0, bx, 0, w, bz, p["guide_top_z"]))
    shell = shell.fuse(_box(0, bx, by - w, by, bz, p["guide_top_z"]))
    shell = shell.fuse(_box(0, w, 0, by, bz, p["guide_top_z"]))
    shell = shell.fuse(_box(p["far_wall_x"], bx, 0, by, bz, p["guide_top_z"]))

    # the slot the rivet runs in; its ends are the terminal bounds
    shell = shell.cut(_box(g["slot_x0"], g["slot_x1"],
                           p["rivet_y"] - p["slot_w"] / 2.0,
                           p["rivet_y"] + p["slot_w"] / 2.0,
                           p["ledge_z0"] - 1.0, bz + 1.0))

    # relief under the latch beam where it passes over the solid panel
    shell = shell.cut(_box(p["keeper_x0"] - p["latch_len"], p["deck_x1"],
                           p["latch_y0"] - p["latch_slot_w"] - 1.0,
                           g["latch_y1"] + p["latch_slot_w"] + 1.0,
                           bz - p["latch_deflection"] - 0.4, bz + 1.0))

    # keeper bridge, spanning the guide walls where the cover always is
    shell = shell.fuse(_box(p["keeper_x0"], p["keeper_x0"] + p["keeper_len"],
                            w, by - w, p["keeper_z0"], p["keeper_z1"]))
    return shell


def build_cover(p: Dict[str, float], latch_deflected: bool = False) -> cq.Shape:
    """Built in the CLOSED position.

    `latch_deflected` returns the declared released configuration: the beam and
    its hook translated down while the plate stays put. Deflecting the whole
    cover instead would drive the plate into the ledges and report an
    interference the product does not have.
    """
    g = geom(p)
    body = _box(g["cover_closed_x0"], p["far_wall_x"], g["plate_y0"], g["plate_y1"],
                p["box_z"], g["cover_top"])

    body = body.cut(_cyl_z(p["box_z"] - 1.0, g["cover_top"] + 1.0,
                           g["rivet_closed_x"], p["rivet_y"], p["cover_bore_d"] / 2.0))
    body = body.cut(_cyl_z(g["head_bot"], g["cover_top"] + 1.0,
                           g["rivet_closed_x"], p["rivet_y"], p["rivet_head_d"] / 2.0 + 0.1))

    ly0, ly1 = p["latch_y0"], g["latch_y1"]
    sw = p["latch_slot_w"]
    for a, b in ((ly0 - sw, ly0), (ly1, ly1 + sw)):
        body = body.cut(_box(g["latch_tip_x"] - 1.0, g["latch_root_x"], a, b,
                             p["box_z"] - 1.0, g["cover_top"] + 1.0))

    hook = _box(g["latch_tip_x"], g["latch_tip_x"] + p["latch_hook_len"], ly0, ly1,
                g["cover_top"], g["hook_z1"])
    ramp = _ramp_x(g["latch_tip_x"] + p["latch_hook_len"],
                   g["latch_tip_x"] + 2.0 * p["latch_hook_len"],
                   ly0, ly1, g["cover_top"], g["hook_z1"])
    latch = hook.fuse(ramp)

    if latch_deflected:
        drop = cv.translation((0.0, 0.0, -p["latch_deflection"]))
        strip = _box(g["latch_tip_x"], g["latch_root_x"], ly0, ly1,
                     p["box_z"], g["cover_top"])
        body = body.cut(strip).fuse(strip.moved(drop))
        latch = latch.moved(drop)
    return body.fuse(latch)


def _ramp_x(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    """Wedge: full height z1 at x0, falling to z0 at x1."""
    pts = [(x0, z0), (x1, z0), (x0, z1)]
    wp = cq.Workplane("XZ", origin=(0, y0, 0)).polyline(pts).close()
    return wp.extrude(-(y1 - y0)).val()


def _ramp_z(z0, z1, px, py, sign, r_out, r_in, hw) -> cq.Shape:
    """Lead-in prism across the slot width: r_in at the tip z0, r_out at z1."""
    pts = [(py + sign * r_in, z0), (py + sign * r_out, z1), (py + sign * r_in, z1)]
    wp = cq.Workplane("YZ", origin=(px - hw, 0, 0)).polyline(pts).close()
    return wp.extrude(2 * hw).val()


def build_rivet(p: Dict[str, float], compressed: bool = False) -> cq.Shape:
    """Snap rivet: head sunk in the cover, lugs recovered under the ledge.

    Pressed straight down. The lead-in deflects the arms, they pass through the
    cover bore and the slot, and they recover under the ledge. Recovered they
    span barb_d, wider than the slot they came through, so the rivet cannot come
    back out - that is the anti-withdrawal feature.

    `compressed=True` is the declared configuration used for the insertion
    check: a configuration of this same rivet, never a separate part, and never
    exported.
    """
    g = geom(p)
    px, py = g["rivet_closed_x"], p["rivet_y"]
    r_in, r_shaft = p["barb_arm_inner_r"], p["rivet_shaft_d"] / 2.0
    r_lug, hw = p["barb_d"] / 2.0, p["barb_beam_w"] / 2.0
    split_z = g["lug_top"] + 6.0

    head = _cyl_z(g["head_bot"], g["head_top"], px, py, p["rivet_head_d"] / 2.0)
    shaft = _cyl_z(split_z, g["head_bot"], px, py, r_shaft)
    core = head.fuse(shaft)

    arms = []
    for sign in (+1.0, -1.0):
        # The arms deflect across the slot's WIDTH (Y), not along its length.
        # A lug that reaches along the slot passes straight back up it, because
        # the slot is 89 mm long and only 5.4 wide - the width is the only
        # dimension that bounds anything.
        def yspan(a, b):
            lo, hi = sorted((py + sign * a, py + sign * b))
            return lo, hi
        by0, by1 = yspan(r_in, r_shaft)
        beam = _box(px - hw, px + hw, by0, by1, g["tip_z"], split_z)
        ly0_, ly1_ = yspan(r_in, r_lug)
        lug = _box(px - hw, px + hw, ly0_, ly1_, g["lug_bot"], g["lug_top"])
        lead = _ramp_z(g["tip_z"], g["lug_bot"], px, py, sign, r_lug, r_in, hw)
        arm = beam.fuse(lug).fuse(lead)
        # stepped clip: the shank stays inside the slot envelope and only the lug
        # reaches the retaining span. One clip at the lug radius would leave the
        # shank's corners outside the slot.
        clip = _cyl_z(g["tip_z"] - 1.0, g["lug_top"], px, py, r_lug).fuse(
            _cyl_z(g["lug_top"], split_z + 1.0, px, py, r_shaft))
        arm = arm.intersect(clip)
        if compressed:
            arm = arm.moved(cv.translation((0.0, -sign * p["barb_deflection"], 0.0)))
        arms.append(arm)
    out = core
    for a in arms:
        out = out.fuse(a)
    return out


def build(p: Dict[str, float] = None) -> List[cv.Body]:
    p = p or load_params()
    return [
        cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                build_enclosure(p),
                role=("fixed body; cavity, top panel, ledges, guide walls, rivet slot, "
                      "keeper bridge")),
        cv.Body("BODY-COVER", "sliding cover", "GENERIC_COMPLIANT_POLYMER",
                build_cover(p),
                role="movable cover with an integral compliant latch beam cut from the plate",
                notes="compliant only in REG-C-LATCH-COMPLIANT; the plate is a rigid slider"),
        cv.Body("BODY-RIVET", "snap rivet", "GENERIC_COMPLIANT_POLYMER",
                build_rivet(p),
                role="holds the cover down at every position; its slot ends bound the travel",
                notes="compliant only in REG-R-SNAP-COMPLIANT, and only during ASM-03"),
    ]


# --------------------------------------------------------------------- states
MOVING = ("BODY-COVER", "BODY-RIVET")


def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    ident = cq.Location()
    if state in ("S_CLOSED_LATCHED", "S_CLOSED_RELEASED"):
        return ident              # these differ by COVER CONFIGURATION, not by pose
    if state == "S_OPEN":
        return cv.translation((-p["travel"], 0.0, 0.0)) if body_id in MOVING else ident
    raise KeyError(state)


def cover_configuration(state: str) -> bool:
    return state == "S_CLOSED_RELEASED"


def latch_hold_mm(p: Dict[str, float]) -> float:
    """How far the cover moves before the latch is clear of the keeper.

    Measured to the far end of the RAMP, not the hook: the ramp is the tallest
    part of the latch and is what last clears the bridge.
    """
    g = geom(p)
    return (g["latch_tip_x"] + 2.0 * p["latch_hook_len"]) - p["keeper_x0"] + 0.5


def _cover(bodies, p, deflected):
    out = []
    for b in bodies:
        if b.id == "BODY-COVER":
            b = cv.Body(b.id, b.name, b.material_class,
                        build_cover(p, latch_deflected=deflected),
                        b.role, b.installed_as, b.notes)
        out.append(b)
    return out


def configuration(bodies, p, state):
    return [b.moved(pose(p, b.id, state))
            for b in _cover(bodies, p, cover_configuration(state))]


def continuous_pose(bodies, p, segment, t):
    if segment == "M1_RELEASE":
        return [b.moved(cq.Location()) for b in _cover(bodies, p, t > 0.5)]
    if segment in ("M2_OPEN", "M3_CLOSE"):
        frac = t if segment == "M2_OPEN" else (1.0 - t)
        slide = p["travel"] * frac
        held = slide <= latch_hold_mm(p)
        out = []
        for b in _cover(bodies, p, held):
            loc = cv.translation((-slide, 0.0, 0.0)) if b.id in MOVING else cq.Location()
            out.append(b.moved(loc))
        return out
    raise KeyError(segment)


def probe_pose(bodies, p, slide, lift=0.0, latch_down=False):
    """Arbitrary slide, with an optional lift - used by the captivity probe."""
    out = []
    for b in _cover(bodies, p, latch_down):
        loc = cv.translation((-slide, 0.0, lift)) if b.id in MOVING else cq.Location()
        out.append(b.moved(loc))
    return out


STATES = ["S_CLOSED_LATCHED", "S_CLOSED_RELEASED", "S_OPEN"]
SEGMENTS = ["M1_RELEASE", "M2_OPEN", "M3_CLOSE"]


if __name__ == "__main__":
    par = load_params()
    for b in build(par):
        bb = cv.bbox_of(b.shape)
        print("%-16s valid=%-5s vol=%11.3f  bbox=(%.2f x %.2f x %.2f)  %s"
              % (b.id, cv.is_valid(b.shape), cv._gprops_volume(b.shape),
                 bb["dx"], bb["dy"], bb["dz"], b.material_class))
