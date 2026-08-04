"""EXE-BM001-02 - guided captive sliding cover with integral snap features.

Redesigned under human decisions HCR-BM001-004..007. The quarter-turn cam is
gone, and with it every part the user had to remove and put somewhere.

Three bodies:

    BODY-ENCLOSURE   shell, cavity, solid top panel, two ledges, two lipped
                     rails, the pin slot, and the latch keeper
    BODY-COVER       plate, the ear that carries the pin, and an integral
                     compliant latch beam with hook and release pad
    BODY-PIN         headed pin with two cantilever snap arms; fixed to the
                     cover, running in the enclosure slot

HOW THE COVER IS CAPTIVE, AND WHY IT IS STILL ASSEMBLABLE

    Those two requirements fight each other. A cover that cannot come out at
    full open cannot have gone in at full open either, so something has to give.

    Here the loading position is OUTSIDE the operating range. The lips carry a
    relief at load_relief_x0..x1; the cover's pin ear can pass down through it,
    but only when the cover is pushed well beyond its open bound. The pin is
    fitted afterwards, and from then on the slot ends limit travel to
    0..travel - which never brings the ear back under the relief.

    So the cover is captive at every operating position, including full open,
    and it still got in.
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
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def _cyl_z(z0, z1, x, y, r) -> cq.Shape:
    return cq.Solid.makeCylinder(r, z1 - z0, pnt=cq.Vector(x, y, z0), dir=cq.Vector(0, 0, 1))


def geom(p: Dict[str, float]) -> Dict[str, float]:
    g = {}
    g["cover_top"] = p["box_z"] + p["cover_t"]
    g["cover_closed_x0"] = p["far_wall_x"] - p["cover_len"]
    g["ledge_far_y"] = p["box_y"] - p["ledge_y"]
    g["lip_far_y"] = p["box_y"] - p["lip_inner_y"]
    # The plate must pass BETWEEN the lips to be loaded at all, so it is narrower
    # than the lip gap and is not overlapped by them. Anti-lift comes from the pin
    # lugs under the ledge; the lips guide laterally and cap the ear.
    g["plate_y0"] = p["lip_inner_y"] + p["slot_gap"] * 2.0
    g["plate_y1"] = g["lip_far_y"] - p["slot_gap"] * 2.0
    g["pin_closed_x"] = g["cover_closed_x0"] + p["pin_offset_x"]
    g["pin_open_x"] = g["pin_closed_x"] - p["travel"]
    g["slot_x0"] = g["pin_open_x"] - p["slot_w"] / 2.0
    g["slot_x1"] = g["pin_closed_x"] + p["slot_w"] / 2.0
    g["ear_y0"] = p["wall"] + p["slot_gap"]      # stays inside the running channel
    g["ear_y1"] = g["plate_y0"]
    # The pin is fitted from BELOW, through the cavity. Nothing of it ever rises
    # into the lip zone, which is what made a top-down pin impossible: its head
    # had to pass through the lips the cover is already under.
    g["head_top"] = p["ledge_z0"] - p["barb_gap"]          # head under the ledge
    g["head_bot"] = g["head_top"] - p["pin_head_h"]
    g["barb_bot"] = g["cover_top"] - p["pin_head_h"] - p["barb_lug_len"]
    g["barb_top"] = g["barb_bot"] + p["barb_lug_len"]      # lugs inside the cover counterbore
    g["latch_y1"] = p["latch_y0"] + p["latch_w"]
    g["latch_tip_x"] = g["cover_closed_x0"]             # free tip at the trailing edge
    g["latch_root_x"] = g["cover_closed_x0"] + p["latch_len"]
    g["hook_z1"] = g["cover_top"] + p["latch_hook_h"]
    return g


# --------------------------------------------------------------------- bodies
def build_enclosure(p: Dict[str, float]) -> cq.Shape:
    g = geom(p)
    w, bx, by, bz = p["wall"], p["box_x"], p["box_y"], p["box_z"]

    shell = _box(0, bx, 0, by, 0, bz).cut(_box(w, bx - w, w, by - w, w, bz))
    # solid top panel over the front of the interior
    shell = shell.fuse(_box(w, p["deck_x1"], w, by - w, p["deck_z0"], bz))
    # the two ledges the cover runs on
    shell = shell.fuse(_box(w, bx - w, w, p["ledge_y"], p["ledge_z0"], bz))
    shell = shell.fuse(_box(w, bx - w, g["ledge_far_y"], by - w, p["ledge_z0"], bz))
    # far end wall: the closed terminal bound. The near end stays open so the
    # cover can be loaded past its open bound.
    shell = shell.fuse(_box(p["far_wall_x"], bx, 0, by, bz, p["rail_top_z"]))

    # lipped rails, then the running channel cut out of each
    # The channel is cut to the LEDGE edge, not the lip edge. Cutting only to the
    # lip leaves rail material beside the plate at cover height, which the plate
    # then runs into - the lip must overhang the channel, not bound it.
    for y0, y1, cy0, cy1 in ((0.0, p["ledge_y"], p["wall"] - p["slot_gap"], p["ledge_y"]),
                             (g["ledge_far_y"], by, g["ledge_far_y"],
                              by - p["wall"] + p["slot_gap"])):
        shell = shell.fuse(_box(0, bx, y0, y1, bz, p["rail_top_z"]))
        shell = shell.cut(_box(0, p["far_wall_x"], cy0, cy1, bz, p["lip_z0"]))
    # loading relief: the only place the pin ear can pass down through a lip
    shell = shell.cut(_box(p["load_relief_x0"], p["load_relief_x1"],
                           p["wall"] - p["slot_gap"], p["lip_inner_y"],
                           p["lip_z0"], p["rail_top_z"] + 1.0))

    # slot the captive pin runs in, through the front ledge
    shell = shell.cut(_box(g["slot_x0"], g["slot_x1"],
                           p["pin_y"] - p["slot_w"] / 2.0, p["pin_y"] + p["slot_w"] / 2.0,
                           p["ledge_z0"] - 1.0, bz + 1.0))

    # Relief in the top panel under the latch path. Without it the deflected
    # beam meets the panel as soon as the cover starts to open, because the
    # latch works right at the panel edge.
    shell = shell.cut(_box(p["keeper_x0"] - p["latch_len"], p["deck_x1"],
                           p["latch_y0"] - p["latch_slot_w"] - 1.0,
                           g["latch_y1"] + p["latch_slot_w"] + 1.0,
                           p["box_z"] - p["latch_deflection"] - 0.4, p["box_z"] + 1.0))

    # Latch keeper: a bridge across the aperture at keeper_x0. It sits over the
    # cover at every operating position - at full open the cover still reaches
    # x = cover_len + (near bound), so the bridge never stands in the opening.
    shell = shell.fuse(_box(p["keeper_x0"], p["keeper_x0"] + p["keeper_len"],
                            p["lip_inner_y"], g["lip_far_y"],
                            p["lip_z0"], p["keeper_z1"]))
    return shell


def build_cover(p: Dict[str, float], latch_deflected: bool = False) -> cq.Shape:
    """Built in the CLOSED position.

    `latch_deflected` returns the declared released configuration: the beam,
    hook and pad translated down by latch_deflection while the plate stays
    where it is. Deflecting the WHOLE cover instead would drive the plate
    into the ledges and report an interference that the product does not have.
    """
    g = geom(p)
    x0, x1 = g["cover_closed_x0"], p["far_wall_x"]
    body = _box(x0, x1, g["plate_y0"], g["plate_y1"], p["box_z"], g["cover_top"])

    # ear carrying the pin, reaching out over the front ledge
    ear_x0 = g["pin_closed_x"] - p["pin_head_d"] / 2.0 - 3.0
    ear_x1 = g["pin_closed_x"] + p["pin_head_d"] / 2.0 + 3.0
    body = body.fuse(_box(ear_x0, ear_x1, g["ear_y0"], g["ear_y1"],
                          p["box_z"], g["cover_top"]))
    # bore for the pin, counterbored so the head sits flush
    body = body.cut(_cyl_z(p["box_z"] - 1.0, g["cover_top"] + 1.0,
                           g["pin_closed_x"], p["pin_y"], p["pin_bore_d"] / 2.0))
    # counterbore from BELOW the top face, housing the recovered lugs
    body = body.cut(_cyl_z(g["barb_bot"] - 0.2, g["cover_top"] + 1.0,
                           g["pin_closed_x"], p["pin_y"], p["barb_d"] / 2.0 + 0.2))

    # Integral compliant latch. The beam is cut FROM the plate, so it lies in the
    # plate's own plane and can deflect down into the aperture. A beam sitting on
    # top of the cover would have to live in the 0.2 mm gap under the lips, which
    # is why the first attempt fouled them.
    ly0, ly1 = p["latch_y0"], g["latch_y1"]
    sw = p["latch_slot_w"]
    for a, b_ in ((ly0 - sw, ly0), (ly1, ly1 + sw)):
        body = body.cut(_box(g["latch_tip_x"] - 1.0, g["latch_root_x"], a, b_,
                             p["box_z"] - 1.0, g["cover_top"] + 1.0))
    hook = _box(g["latch_tip_x"], g["latch_tip_x"] + p["latch_hook_len"], ly0, ly1,
                g["cover_top"], g["hook_z1"])
    # lead-in on the hook's trailing face, so closing deflects the beam
    ramp = _ramp_x(g["latch_tip_x"] + p["latch_hook_len"],
                   g["latch_tip_x"] + p["latch_hook_len"] + p["latch_hook_len"],
                   ly0, ly1, g["cover_top"], g["hook_z1"])
    # No raised release pad. One was tried and it struck the keeper bridge as the
    # cover slid under it. The beam's own top face is the release surface: at the
    # closed position the beam lies under the open aperture, so a finger reaches
    # it directly.
    latch = hook.fuse(ramp)
    if latch_deflected:
        latch = latch.moved(cv.translation((0.0, 0.0, -p["latch_deflection"])))
        # the beam itself bends; represent it by removing the plate strip the
        # beam occupies and re-adding it at the deflected height
        strip = _box(g["latch_tip_x"], g["latch_root_x"], ly0, ly1,
                     p["box_z"], g["cover_top"])
        moved_strip = strip.moved(cv.translation((0.0, 0.0, -p["latch_deflection"])))
        body = body.cut(strip).fuse(moved_strip)
    body = body.fuse(latch)
    return body


def _ramp_x(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    """Wedge: full height z1 at x0, falling to z0 at x1."""
    pts = [(x0, z0), (x1, z0), (x0, z1)]
    wp = cq.Workplane("XZ", origin=(0, y0, 0)).polyline(pts).close()
    return wp.extrude(-(y1 - y0)).val()


def build_pin(p: Dict[str, float], compressed: bool = False) -> cq.Shape:
    """Snap rivet fitted from below, through the cavity.

    Head under the ledge, shaft up through the slot and the cover bore, snap
    lugs recovering in a counterbore INSIDE the cover. The cover is then trapped
    between the head and the lugs, and nothing on the pin ever enters the lip
    zone - which a top-down pin could not avoid.
    """
    g = geom(p)
    px, py = g["pin_closed_x"], p["pin_y"]
    r_in, r_beam = p["barb_arm_inner_r"], p["pin_shaft_d"] / 2.0
    r_lug, hw = p["barb_d"] / 2.0, p["barb_beam_w"] / 2.0
    root_z = g["barb_bot"] - 4.0                       # arms split below the lugs
    head = _cyl_z(g["head_bot"], g["head_top"], px, py, p["pin_head_d"] / 2.0)
    shaft = _cyl_z(g["head_top"], root_z, px, py, r_beam)
    core = head.fuse(shaft)

    arms = []
    for sign in (+1.0, -1.0):
        def xspan(a, b):
            lo, hi = sorted((px + sign * a, px + sign * b))
            return lo, hi
        bx0, bx1 = xspan(r_in, r_beam)
        beam = _box(bx0, bx1, py - hw, py + hw, root_z, g["barb_top"] + p["barb_leadin_len"])
        lx0, lx1 = xspan(r_in, r_lug)
        lug = _box(lx0, lx1, py - hw, py + hw, g["barb_bot"], g["barb_top"])
        lead = _ramp_z(g["barb_top"], g["barb_top"] + p["barb_leadin_len"],
                       px, py, sign, r_lug, r_beam, hw)
        arm = beam.fuse(lug).fuse(lead)
        clip = _cyl_z(root_z - 1.0, g["barb_bot"], px, py, r_beam).fuse(
            _cyl_z(g["barb_bot"], g["barb_top"] + p["barb_leadin_len"] + 1.0, px, py, r_lug))
        arm = arm.intersect(clip)
        if compressed:
            arm = arm.moved(cv.translation((-sign * p["barb_deflection"], 0.0, 0.0)))
        arms.append(arm)
    out = core
    for a in arms:
        out = out.fuse(a)
    return out


def _ramp_z(z0, z1, px, py, sign, r_out, r_in, hw) -> cq.Shape:
    """Lead-in prism: r_out at z0 tapering to r_in at z1."""
    pts = [(px + sign * r_out, z0), (px + sign * r_in, z1), (px + sign * r_in, z0)]
    wp = cq.Workplane("XZ", origin=(0, py - hw, 0)).polyline(pts).close()
    return wp.extrude(-2 * hw).val()


def build(p: Dict[str, float] = None) -> List[cv.Body]:
    p = p or load_params()
    return [
        cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                build_enclosure(p),
                role="fixed body; cavity, top panel, ledges, lipped rails, pin slot, latch keeper"),
        cv.Body("BODY-COVER", "sliding cover", "GENERIC_COMPLIANT_POLYMER",
                build_cover(p),
                role=("movable cover; plate, pin ear, and an integral compliant latch "
                      "beam with hook and release pad"),
                notes="compliant only in REG-C-LATCH-COMPLIANT; the plate is a rigid slider"),
        cv.Body("BODY-PIN", "captive retention pin", "GENERIC_COMPLIANT_POLYMER",
                build_pin(p),
                role=("fixed in the cover ear, running in the enclosure slot; its snap "
                      "arms make the cover captive and its slot ends bound the travel"),
                notes="compliant only in REG-P-SNAP-COMPLIANT, and only during ASM-03"),
    ]


# --------------------------------------------------------------------- states
def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    ident = cq.Location()
    slide = cv.translation((-p["travel"], 0.0, 0.0))
    if state in ("S_CLOSED_LATCHED", "S_CLOSED_RELEASED"):
        return ident            # released differs by COVER CONFIGURATION, not pose
    if state == "S_OPEN":
        return slide if body_id in ("BODY-COVER", "BODY-PIN") else ident
    raise KeyError(state)


def latch_hold_mm(p: Dict[str, float]) -> float:
    """How far the cover moves before the hook is clear of the keeper.

    Beyond this the beam has recovered and the latch plays no further part in
    the motion.
    """
    g = geom(p)
    # measured to the far end of the RAMP, not the hook: the ramp is the tallest
    # part of the latch and is what last clears the keeper bridge
    return (g["latch_tip_x"] + 2.0 * p["latch_hook_len"]) - p["keeper_x0"] + 0.5


def cover_configuration(state: str) -> bool:
    """True when the state uses the latch-deflected cover configuration."""
    return state == "S_CLOSED_RELEASED"


def configuration(bodies, p, state):
    out = []
    for b in bodies:
        if b.id == "BODY-COVER" and cover_configuration(state):
            b = cv.Body(b.id, b.name, b.material_class,
                        build_cover(p, latch_deflected=True), b.role, b.installed_as, b.notes)
        out.append(b.moved(pose(p, b.id, state)))
    return out


def continuous_pose(bodies, p, segment, t):
    out = []
    for b in bodies:
        loc = cq.Location()
        moves = b.id in ("BODY-COVER", "BODY-PIN")
        if segment == "M1_RELEASE":
            if b.id == "BODY-COVER":
                b = cv.Body(b.id, b.name, b.material_class,
                            build_cover(p, latch_deflected=t > 0.5), b.role,
                            b.installed_as, b.notes)
        elif segment in ("M2_OPEN", "M3_CLOSE"):
            frac = t if segment == "M2_OPEN" else (1.0 - t)
            slide = p["travel"] * frac
            # The beam is held down only while the hook is still alongside the
            # keeper. Past that it recovers - holding it down for the whole slide
            # would drag the deflected strip over the solid top panel.
            if b.id == "BODY-COVER":
                b = cv.Body(b.id, b.name, b.material_class,
                            build_cover(p, latch_deflected=slide <= latch_hold_mm(p)),
                            b.role, b.installed_as, b.notes)
            if moves:
                loc = cv.translation((-slide, 0.0, 0.0))
        else:
            raise KeyError(segment)
        out.append(b.moved(loc))
    return out


def probe_pose(bodies, p, slide, lift=0.0, latch_down=None):
    """Arbitrary slide, with optional upward lift - used by the captivity probe."""
    if latch_down is None:
        latch_down = p["latch_deflection"]
    out = []
    for b in bodies:
        loc = cq.Location()
        if b.id in ("BODY-COVER", "BODY-PIN"):
            loc = cv.translation((-slide, 0.0, lift - latch_down))
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
