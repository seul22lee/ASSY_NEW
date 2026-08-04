"""EXE-BM001-02 - integrated snap-rail captive sliding cover.

TWO product bodies and no others:

    BODY-ENCLOSURE   rigid; carries the two captive rails and the latch keeper
    BODY-COVER       compliant only in three declared regions; everything that
                     retains it or latches it is part of this body

The whole mechanism is the rail cross-section. Each rail is a C-channel:

        z
        |   +-------+   <- retaining lip, overhangs the channel inboard
        |   |#######|      from the guide wall (lip_z0..lip_z1)
        |   |###+---+ - - - - - - - - - - lip inner edge
        |   |###|
        |   |###|  <- guide wall (inner face at y = wall): lateral location
        |   |###|
        |   +---+-----------+  <- ledge top face at z = box_z: vertical support
        |       |###########|
        +-------+-----------+------ y

The cover's plate is narrow enough to pass BETWEEN the two lips. Local
compliant retention tabs project outward from its edges, under the lips. To
assemble, the tabs are deflected inward until they too fit between the lips,
the cover is pressed straight down onto the ledges, and the tabs recover
outward beneath the lips. After that the cover cannot be lifted off anywhere,
because the lips run the full operating length.

That is the entire retention story: three functions - support, guidance and
anti-lift - carried by one rail, and no separate part anywhere in it.

The closed state is held by a second integral snap: a cantilever finger at the
cover's exposed +X end, reaching out through a slot in the end wall, with a
tooth hanging down behind the wall's OUTER face. Lift the finger, the tooth
clears the wall, slide the cover open. Closing drives the tooth's ramp against
the slot floor, lifts the finger automatically, and the tooth drops back.

Compliance is modelled as a rigid translation of a declared region. That is a
DECLARED_KINEMATIC_APPROXIMATION: it tests geometric passage and engagement and
conserves volume exactly. It predicts nothing about strain, and no force is
computed anywhere in this reference.

    python build.py            # rebuild and export
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List

import cadquery as cq
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))

import cadval as cv          # noqa: E402

STATES = ["CLOSED_LATCH_ENGAGED", "CLOSED_LATCH_RELEASED", "OPENING_STARTED",
          "OPEN_INTERMEDIATE", "OPEN_84", "CLOSING_LATCH_LEADIN", "CLOSED_REENGAGED"]
SEGMENTS = ["M1_RELEASE_AND_OPEN", "M2_CLOSE_AND_REENGAGE"]


def load_params(path: str = None) -> Dict[str, float]:
    doc = yaml.safe_load(open(path or os.path.join(HERE, "parameters.yaml")))
    return {p["name"]: float(p["value"]) for p in doc["parameters"]}


def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def _prism_xy(pts, z0, z1) -> cq.Shape:
    """A polygon in the XY plane, extruded through Z. Used for the latch tooth,
    whose lead-in ramp is a real sloped face rather than a stepped stack."""
    wp = cq.Workplane("XY").polyline([(x, y) for x, y in pts]).close()
    return wp.extrude(z1 - z0).val().moved(cv.translation((0.0, 0.0, z0)))


# --------------------------------------------------------------------- geometry
def geom(p: Dict[str, float]) -> Dict[str, float]:
    g: Dict[str, float] = {}
    w = p["wall"]
    g["guide_near_y"] = w                      # inner face of the near guide wall
    g["guide_far_y"] = p["box_y"] - w          # inner face of the far guide wall
    g["ledge_near_y1"] = p["ledge_y"]          # inboard edge of the near ledge
    g["ledge_far_y0"] = p["box_y"] - p["ledge_y"]
    g["ledge_top"] = p["box_z"]
    g["lip_near_y1"] = w + p["lip_overhang"]   # inner edge of the near lip
    g["lip_far_y0"] = p["box_y"] - w - p["lip_overhang"]

    # The cover plate must pass BETWEEN the lips, so its edges sit just inboard
    # of the lip inner edges.
    g["cover_y0"] = g["lip_near_y1"] + p["plate_gap"]
    g["cover_y1"] = g["lip_far_y0"] - p["plate_gap"]
    g["cover_top"] = p["box_z"] + p["cover_t"]

    # Tab tips run against the guide walls; that is the lateral location.
    g["tab_near_tip_y"] = w + p["guide_gap"]
    g["tab_far_tip_y"] = p["box_y"] - w - p["guide_gap"]

    g["rail_x0"] = p["rail_x0"]                # rails start here; -X of it is solid
    g["rail_x1"] = p["far_wall_x"]
    g["closed_x0"] = p["far_wall_x"] - p["cover_len"]
    g["closed_x1"] = p["far_wall_x"]
    g["open_x0"] = g["closed_x0"] - p["travel"]

    # The latch lives over the NEAR RAIL, not over the aperture. A finger on the
    # centreline would retract into the opening at full open and stand in the
    # way of the 84 mm the design promises; out here it retracts over the ledge.
    g["finger_y0"] = p["latch_y0"]
    g["finger_y1"] = p["latch_y0"] + p["latch_w"]
    g["lug_y0"] = p["latch_y0"] - p["latch_lug_w"]      # projects OUTBOARD
    g["lug_y1"] = p["latch_y0"]
    g["slot_y0"] = p["latch_y0"] - p["latch_slot_gap"]  # outboard edge of the slot
    g["slot_y1"] = g["finger_y1"] + p["latch_shift"] + p["latch_slot_gap"]
    g["keeper_y0"] = g["lug_y0"]                        # wall left outboard of the slot
    g["keeper_y1"] = g["slot_y0"]
    g["tooth_x0"] = p["box_x"] + p["latch_free_play"]
    g["tooth_x1"] = g["tooth_x0"] + p["latch_tooth_len"]
    g["finger_x1"] = g["tooth_x1"] + p["latch_pad_len"]
    g["latch_engage_mm"] = p["latch_lug_w"] - p["latch_slot_gap"]
    return g


# ---------------------------------------------------------------- enclosure
def build_enclosure(p: Dict[str, float]) -> cq.Shape:
    g = geom(p)
    w, bx, by, bz = p["wall"], p["box_x"], p["box_y"], p["box_z"]

    # open-topped box
    s = _box(0, bx, 0, by, 0, bz).cut(_box(w, bx - w, w, by - w, w, bz))

    # solid top panel: the surface the cover parks over when open. Its top face
    # is held below the ledge tops so the ledges alone carry the cover.
    s = s.fuse(_box(w, p["deck_x1"], w, by - w, p["deck_z0"], bz - p["deck_gap"]))

    # ---- the two captive rails ------------------------------------------------
    # ledge: vertical support, top face at z = box_z
    s = s.fuse(_box(w, bx - w, w, p["ledge_y"], p["ledge_z0"], bz))
    s = s.fuse(_box(w, bx - w, g["ledge_far_y0"], by - w, p["ledge_z0"], bz))
    # guide walls carried up to the lip: lateral location
    s = s.fuse(_box(0, bx, 0, w, bz, p["lip_z1"]))
    s = s.fuse(_box(0, bx, by - w, by, bz, p["lip_z1"]))
    # retaining lips: real overhanging solid, running the full rail length, so a
    # tab under one at the closed bound is still under one at the open bound
    s = s.fuse(_box(g["rail_x0"], g["rail_x1"], w, g["lip_near_y1"],
                    p["lip_z0"], p["lip_z1"]))
    s = s.fuse(_box(g["rail_x0"], g["rail_x1"], g["lip_far_y0"], by - w,
                    p["lip_z0"], p["lip_z1"]))
    # -X of rail_x0 the rail band is filled solid: that face is the open bound
    s = s.fuse(_box(0, g["rail_x0"], 0, p["ledge_y"], p["ledge_z0"], p["lip_z1"]))
    s = s.fuse(_box(0, g["rail_x0"], g["ledge_far_y0"], by, p["ledge_z0"], p["lip_z1"]))
    # end walls carried to the lip height so the closed bound is a full face
    s = s.fuse(_box(0, w, 0, by, bz, p["lip_z1"]))
    s = s.fuse(_box(p["far_wall_x"], bx, 0, by, bz, p["lip_z1"]))

    # ---- latch slot: the finger reaches through the end wall to the outside.
    # Open-topped, so the cover can still be pressed straight down at assembly.
    # The wall OUTBOARD of it, y lug_y0 to slot_y0, is left standing: that is the keeper.
    s = s.cut(_box(p["far_wall_x"] - 1.0, bx + 1.0, g["slot_y0"], g["slot_y1"],
                   bz, p["lip_z1"] + 1.0))
    return s


# -------------------------------------------------------------------- cover
def _tab_solid(p: Dict[str, float], g: Dict[str, float],
               x0: float, near: bool, compressed) -> cq.Shape:
    """One retention tab: a cantilever beam rooted at its +X end, carrying an
    ear that projects outward under the rail lip."""
    if near:
        beam_y0, beam_y1 = g["cover_y0"], g["cover_y0"] + p["tab_beam_w"]
        ear_y0, ear_y1 = g["tab_near_tip_y"], g["cover_y0"]
        sign = +1.0                       # compressed means inboard, i.e. +Y
    else:
        beam_y0, beam_y1 = g["cover_y1"] - p["tab_beam_w"], g["cover_y1"]
        ear_y0, ear_y1 = g["cover_y1"], g["tab_far_tip_y"]
        sign = -1.0
    beam = _box(x0, x0 + p["tab_len"], beam_y0, beam_y1, p["box_z"], g["cover_top"])
    ear = _box(x0, x0 + p["tab_ear_len"], ear_y0, ear_y1, p["box_z"], g["cover_top"])
    tab = beam.fuse(ear)
    # `compressed` may be a bool or a fraction in 0..1. The fraction exists so a
    # video can show the tab part-way in; True is exactly 1.0, so the geometry the
    # validator sees is unchanged by its existence.
    frac = 1.0 if compressed is True else (0.0 if compressed is False else float(compressed))
    if frac:
        tab = tab.moved(cv.translation((0.0, sign * frac * p["tab_deflection"], 0.0)))
    return tab


def _tab_void(p: Dict[str, float], g: Dict[str, float],
              x0: float, near: bool) -> cq.Shape:
    """What the plate gives up so the beam can flex: the beam's own footprint
    plus the slot that frees it inboard and at its -X end."""
    sw = p["tab_slot_w"]
    if near:
        y0, y1 = g["cover_y0"], g["cover_y0"] + p["tab_beam_w"] + sw
    else:
        y0, y1 = g["cover_y1"] - p["tab_beam_w"] - sw, g["cover_y1"]
    return _box(x0 - sw, x0 + p["tab_len"], y0, y1, p["box_z"], g["cover_top"])


def build_cover(p: Dict[str, float], *, tabs_compressed=False,
                latch_released=False) -> cq.Shape:
    """Built in the CLOSED position.

    `tabs_compressed` is the declared assembly configuration: the four retention
    tabs translated inward as rigid bodies. `latch_released` is the declared
    release configuration: the latch finger and its tooth translated up.
    """
    g = geom(p)
    x0, x1 = g["closed_x0"], g["closed_x1"]
    plate = _box(x0, x1, g["cover_y0"], g["cover_y1"], p["box_z"], g["cover_top"])

    tabs = [(x0 + p["tab_a_offset"], True), (x0 + p["tab_b_offset"], True),
            (x0 + p["tab_a_offset"], False), (x0 + p["tab_b_offset"], False)]
    for tx, near in tabs:
        plate = plate.cut(_tab_void(p, g, tx, near))
    for tx, near in tabs:
        plate = plate.fuse(_tab_solid(p, g, tx, near, tabs_compressed))

    # ---- integral latch: finger, tooth, ramp -------------------------------
    # The finger runs out through the end wall over the near rail. Its tooth is a
    # lug projecting OUTBOARD, standing behind the strip of end wall left beside
    # the slot. Push the pad inboard and the lug clears that strip.
    finger = _box(x1, g["finger_x1"], g["finger_y0"], g["finger_y1"],
                  p["box_z"], g["cover_top"])
    # tooth section in XY: the blocking face is at tooth_x0, and the lead-in ramp
    # runs from the outboard corner to the inboard one, so closing pushes the
    # finger aside without the user doing anything
    tooth = _prism_xy([(g["tooth_x0"], g["lug_y0"]), (g["tooth_x0"] + p["latch_ramp_run"],
                       g["lug_y0"]), (g["tooth_x1"], g["lug_y1"]),
                       (g["tooth_x0"], g["lug_y1"])], p["box_z"], g["cover_top"])
    latch = finger.fuse(tooth)
    lf = (1.0 if latch_released is True else
          (0.0 if latch_released is False else float(latch_released)))
    if lf:
        latch = latch.moved(cv.translation((0.0, lf * p["latch_shift"], 0.0)))
    return plate.fuse(latch)


# --------------------------------------------------------------------- bodies
def build(p: Dict[str, float]) -> List[cv.Body]:
    return [
        cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                build_enclosure(p), installed_as="DISCRETE",
                role=("Fixed body. Cavity, solid top panel, and two captive rails "
                      "whose ledge, guide wall and retaining lip together support, "
                      "locate and hold down the cover. Its far end wall carries the "
                      "latch slot and the keeper face."),
                notes="rigid throughout; no compliant region declared"),
        cv.Body("BODY-COVER", "sliding cover", "GENERIC_COMPLIANT_POLYMER",
                build_cover(p), installed_as="DISCRETE_SNAP_IN",
                role=("Movable cover. Four integral retention tabs run under the "
                      "rail lips; an integral latch finger reaches through the end "
                      "wall and hooks behind its outer face."),
                notes=("kinematically rigid except REG-COVER-RETAIN-LEFT-COMPLIANT, "
                       "REG-COVER-RETAIN-RIGHT-COMPLIANT and REG-COVER-LATCH-COMPLIANT")),
    ]


# ---------------------------------------------------------------------- poses
def slide_of(p: Dict[str, float], state: str) -> float:
    # OPENING_STARTED and CLOSING_LATCH_LEADIN sit INSIDE the window where the
    # tooth is alongside the end wall, so the lifted configuration is doing real
    # work in them rather than being merely declared.
    mid = (p["latch_free_play"] + p["latch_hold_travel"]) / 2.0
    return {"CLOSED_LATCH_ENGAGED": 0.0, "CLOSED_LATCH_RELEASED": 0.0,
            "OPENING_STARTED": mid,
            "OPEN_INTERMEDIATE": p["travel"] / 2.0,
            "OPEN_84": p["travel"],
            "CLOSING_LATCH_LEADIN": mid,
            "CLOSED_REENGAGED": 0.0}[state]


def pose(p: Dict[str, float], body_id: str, state: str) -> cq.Location:
    """The rigid placement of one body in one state, for the signature record.

    Configuration changes - a deflected tab, a lifted finger - are not poses and
    do not appear here; they are recorded separately as declared compliant
    configurations.
    """
    if body_id != "BODY-COVER":
        return cq.Location()
    return cv.translation((-slide_of(p, state), 0.0, 0.0))


def _cover_variant(p, *, compressed=False, released=False) -> cq.Shape:
    return build_cover(p, tabs_compressed=compressed, latch_released=released)


def configuration(bodies: List[cv.Body], p: Dict[str, float], state: str) -> List[cv.Body]:
    """The bodies as they stand in one declared state."""
    released = state in ("CLOSED_LATCH_RELEASED", "OPENING_STARTED",
                         "CLOSING_LATCH_LEADIN")
    out = []
    for b in bodies:
        if b.id != "BODY-COVER":
            out.append(b)
            continue
        shape = _cover_variant(p, released=released) if released else b.shape
        moved = cv.Body(b.id, b.name, b.material_class, shape,
                        installed_as=b.installed_as, role=b.role, notes=b.notes)
        out.append(moved.moved(cv.translation((-slide_of(p, state), 0.0, 0.0))))
    return out


def continuous_pose(bodies: List[cv.Body], p: Dict[str, float],
                    segment: str, t: float) -> List[cv.Body]:
    """A point on a motion segment. t runs 0 to 1.

    M1: the finger is lifted, the cover runs 0 -> 84 mm. The finger stays lifted
        only while the tooth is still alongside the end wall.
    M2: the reverse. The lead-in ramp does the lifting on the way in.
    """
    hold, play = p["latch_hold_travel"], p["latch_free_play"]
    if segment == "M1_RELEASE_AND_OPEN":
        s = t * p["travel"]
        # opening: the user lifts the finger before moving at all and holds it
        # until the tooth is past the end wall
        released = s <= hold + 1e-9
    else:
        s = (1.0 - t) * p["travel"]
        # closing: the ramp lifts the finger only while the tooth is actually
        # alongside the wall. Once the tooth is clear of the outer face it drops
        # back on its own - which is the snap, and why the segment has to END in
        # the recovered configuration rather than the lifted one.
        released = play - 1e-9 <= s <= hold + 1e-9
    out = []
    for b in bodies:
        if b.id != "BODY-COVER":
            out.append(b)
            continue
        shape = _cover_variant(p, released=released) if released else b.shape
        moved = cv.Body(b.id, b.name, b.material_class, shape,
                        installed_as=b.installed_as, role=b.role, notes=b.notes)
        out.append(moved.moved(cv.translation((-s, 0.0, 0.0))))
    return out


def probe_pose(bodies: List[cv.Body], p: Dict[str, float], slide: float,
               *, lift: float = 0.0, pitch_deg: float = 0.0,
               roll_deg: float = 0.0) -> List[cv.Body]:
    """The cover displaced by an ordinary removal attempt: lift it, or tilt it.

    A tilt matters because two tabs a side could in principle let the cover
    rock out diagonally even when a straight lift is blocked.
    """
    g = geom(p)
    cx = g["closed_x0"] - slide + p["cover_len"] / 2.0
    cy = (g["cover_y0"] + g["cover_y1"]) / 2.0
    cz = p["box_z"] + p["cover_t"] / 2.0
    loc = cv.translation((-slide, 0.0, lift))
    if pitch_deg:
        loc = cv.rotation((cx, cy, cz), (0, 1, 0), pitch_deg) * loc
    if roll_deg:
        loc = cv.rotation((cx, cy, cz), (1, 0, 0), roll_deg) * loc
    return [b if b.id != "BODY-COVER" else b.moved(loc) for b in bodies]


def usable_opening(p: Dict[str, float]) -> Dict[str, float]:
    g = geom(p)
    return {"aperture_x0": p["deck_x1"], "aperture_x1": p["far_wall_x"],
            "nominal_mm": p["far_wall_x"] - p["deck_x1"],
            "usable_x0": g["closed_x0"] - p["travel"] + p["cover_len"],
            "usable_x1": p["far_wall_x"],
            "usable_mm": p["travel"]}


# --------------------------------------------------------------------- export
def export(p: Dict[str, float] = None, out_dir: str = None) -> Dict[str, int]:
    p = p or load_params()
    out_dir = out_dir or HERE
    bodies = build(p)
    written = {}
    for b in bodies:
        stem = b.id.lower().replace("body-", "")
        written["%s.step" % stem] = cv.export_step(b.shape, os.path.join(out_dir, "%s.step" % stem))
        written["%s.brep" % stem] = cv.export_brep(b.shape, os.path.join(out_dir, "%s.brep" % stem))
    comp = cv.compound(bodies)
    written["model.step"] = cv.export_step(comp, os.path.join(out_dir, "model.step"))
    written["model.brep"] = cv.export_brep(comp, os.path.join(out_dir, "model.brep"))
    return written


if __name__ == "__main__":
    P = load_params()
    for b in build(P):
        bb = cv.bbox_of(b.shape)
        print("%-16s vol %12.3f mm^3   bbox %.1f x %.1f x %.1f  valid=%s"
              % (b.id, cv._gprops_volume(b.shape), bb["dx"], bb["dy"], bb["dz"],
                 cv.is_valid(b.shape)))
    for k, v in sorted(export(P).items()):
        print("wrote %-18s %8d bytes" % (k, v))
