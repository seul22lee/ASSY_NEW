"""Human-review section set for EXE-BM001-01.

These are the images a reviewer is asked to judge. They are drawings, not
renders: orthographic, normal to the cut, cut faces hatched, and nothing behind
the plane drawn. The general product views produced by the artifact contract are
deliberately not part of this set.

Every detail cut is located on the overview by a section line, so a reviewer can
see where in the product each cut is taken before reading it.

    python review_views.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))

import build as B          # noqa: E402
import cadval as cv        # noqa: E402

COLORS = {"BODY-ENCLOSURE": "#8fb0cc", "BODY-CLOSURE": "#d7a878",
          "BODY-PIN": "#a79ccc", "BODY-BOLT": "#96bfa2"}
HATCH = {"BODY-ENCLOSURE": "///", "BODY-CLOSURE": "\\\\\\",
         "BODY-PIN": "xxx", "BODY-BOLT": "..."}
SHOTS = os.path.join(HERE, "screenshots")


def render_all() -> list:
    P = B.load_params()
    raw = B.build(P)
    bodies = B.configuration(raw, P, "CLOSED_LATCH_ENGAGED")
    G = B.latch_geom(P)
    bands = B.knuckle_bands(P)
    ay, az = P["axis_y"], P["axis_z"]
    cx = sum(bands["closure"][0]) / 2.0          # first closure knuckle centre
    ex = sum(bands["enclosure"][0]) / 2.0        # head-side enclosure knuckle centre
    kx_far = bands["enclosure"][-1][1]           # last knuckle far face
    written = []

    def out(name):
        return os.path.join(SHOTS, name)

    # ---- OVERVIEW: plan through the closure plate, so the whole footprint and
    # the hinge appear together and every detail cut can be located on it
    plan_z = P["box_z"] + P["plate_t"] / 2.0
    written.append(cv.render_review_section(
        bodies, out("review_overview_latch_operation_and_sections.png"),
        plane="z", at=plan_z,
        colors=COLORS, hatches=HATCH, label="OVERVIEW  (plan, closed and latched)",
        title="EXE-BM001-01 - three bodies, how the latch works, and where the cuts are taken",
        extent=(-30, 150, -26, 126),
        context_note="A-A, B-B, C-C and E-E are taken where marked",
        section_lines=[{"at": ex, "label": "B-B"}, {"at": cx, "label": "A-A"},
                       {"at": ay, "label": "C-C", "along": "v"},
                       {"at": P["latch_x_centre"], "label": "E-E"}],
        arrows=[{"xy": (P["latch_x_centre"], -6.0), "dxy": (0.0, -13.0),
                 "text": "PULL THE PAD OUT (-Y)", "toff": (0.0, -4.0)},
                {"xy": (128.0, 86.0), "dxy": (16.0, 0.0),
                 "text": "HINGE AXIS", "toff": (0.0, 5.0), "color": "#7d3c98"}],
        annotations=[
            {"text": "closure plate covers the aperture", "xy": (74.0, 40.0),
             "xytext": (100.0, 30.0)},
            {"text": "integral latch: beam, tooth and release pad,\nall part of BODY-CLOSURE",
             "xy": (P["latch_x_centre"] + 12.0, G["beam_y0"] + 0.5),
             "xytext": (86.0, -22.0)},
            {"text": "keeper rib on the enclosure front face\n(under the plate in this view)",
             "xy": (G["keeper_x0"] - 3.0, -1.6), "xytext": (-28.0, -22.0)},
            {"text": "five interleaved knuckles on the pin", "xy": (60.0, ay),
             "xytext": (2.0, 116.0)},
            {"text": "recovered snap barb (section D-D)", "xy": (kx_far + 2.5, ay),
             "xytext": (78.0, 116.0)},
        ]))

    # ---- SECTION A-A: closure knuckle on the pin, in context
    written.append(cv.render_review_section(
        bodies, out("review_section_closure_knuckle_pin.png"), plane="x", at=cx,
        colors=COLORS, hatches=HATCH, label="SECTION A-A",
        title="closure knuckle on the pin",
        extent=(ay - 30, ay + 22, az - 34, az + 16),
        context_note="closure side of the joint",
        annotations=[
            {"text": "closure knuckle", "xy": (ay + 4.0, az + 4.5), "xytext": (ay + 9.0, az + 12.0)},
            {"text": "pin shaft, 0.1 radial running clearance",
             "xy": (ay + 2.0, az), "xytext": (ay - 28.0, az + 11.0)},
            {"text": "closure plate seats on the rim here",
             "xy": (ay - 8.0, az - 5.0), "xytext": (ay - 29.0, az - 16.0)},
        ]))

    # ---- SECTION B-B: enclosure knuckle on the pin, head-side segment
    written.append(cv.render_review_section(
        bodies, out("review_section_enclosure_knuckle_pin.png"), plane="x", at=ex,
        colors=COLORS, hatches=HATCH, label="SECTION B-B",
        title="enclosure knuckle on the pin (head-side segment)",
        extent=(ay - 30, ay + 22, az - 34, az + 16),
        context_note="enclosure side of the joint",
        annotations=[
            {"text": "enclosure knuckle and its web down to the rear wall",
             "xy": (ay + 4.0, az - 6.0), "xytext": (ay - 29.0, az - 20.0)},
            {"text": "pin in the enclosure bore", "xy": (ay + 2.0, az),
             "xytext": (ay + 8.0, az + 12.0)},
        ]))

    # ---- SECTION D-D: knuckle-side geometry in context, across the whole width
    written.append(cv.render_review_section(
        bodies, out("review_section_knuckle_side_context.png"), plane="y", at=ay,
        colors=COLORS, hatches=HATCH, label="SECTION D-D",
        title="knuckle side across the full width - five interleaved segments",
        extent=(-6, 126, az - 26, az + 16),
        context_note="cut on the hinge axis, looking along +Y",
        annotations=[
            {"text": "enclosure segments (3) alternate with closure segments (2)",
             "xy": (44.0, az + 5.0), "xytext": (4.0, az + 12.0)},
            {"text": "pin runs the full width", "xy": (60.0, az),
             "xytext": (74.0, az - 22.0)},
        ]))

    # ---- SECTION C-C: longitudinal pin, retention logic
    written.append(cv.render_review_section(
        bodies, out("review_section_pin_head_and_snap_barb.png"), plane="z", at=az,
        colors=COLORS, hatches=HATCH, label="SECTION C-C",
        title="pin retention: head, alternating knuckles, recovered snap barb",
        extent=(12, 112, ay - 12, ay + 12),
        context_note="both axial directions blocked",
        annotations=[
            {"text": "head shoulder bears on the counterbore:\n" "blocks travel toward +X",
             "xy": (23.0, ay + 3.4), "xytext": (27.0, ay + 8.2)},
            {"text": "recovered lug shoulders bear on the last\n" "knuckle face: block travel toward -X",
             "xy": (100.6, ay + 2.9), "xytext": (40.0, ay - 10.6)},
            {"text": "arms split here", "xy": (94.5, ay + 1.9), "xytext": (66.0, ay + 8.6)},
        ]))

    # ============================================================== the latch
    # E-E is a longitudinal cut on the latch centreline. The latch works in the
    # YZ plane, so this is the plane it works in; a plan would show the beam but
    # never the tooth under the keeper.
    ee = P["latch_x_centre"]
    lat_extent = (-16, 26, 22, 56)
    ky = -P["keeper_proj"]

    def latch_bodies(deg, latch):
        return B.probe_pose(raw, P, deg, latch)

    written.append(cv.render_review_section(
        latch_bodies(0.0, 0.0), out("review_section_latch_engaged.png"),
        plane="x", at=ee, colors=COLORS, hatches=HATCH, label="SECTION E-E",
        title="latch ENGAGED - the tooth is under the keeper",
        extent=lat_extent,
        context_note="closed and latched; beam, tooth and pad are one solid with the closure",
        arrows=[{"xy": (16.0, 43.0), "dxy": (0.0, 7.0), "text": "OPENING BLOCKED",
                 "toff": (0.0, 1.0)}],
        annotations=[
            {"text": "FEA-E-KEEPER - a rib on the enclosure's own front face.\n"
                     "Its UNDERSIDE is the blocking face.",
             "xy": (ky + 1.0, P["keeper_z0"] + 1.4), "xytext": (-15.0, 50.0)},
            {"text": "FEA-C-LATCH-SHOULDER, %.1f mm below the keeper:\n"
                     "the closed free play" % P["latch_gap"],
             "xy": (ky - 0.6, P["tooth_top_z"]), "xytext": (-15.0, 26.0)},
            {"text": "%.1f mm of tooth lies under the keeper" % G["engagement_mm"],
             "xy": (G["tooth_y1"] - 0.4, P["tooth_top_z"] - 1.6), "xytext": (6.0, 30.0)},
            {"text": "FEA-C-RELEASE-PAD - outside the product,\nreachable without opening the lid",
             "xy": (G["beam_y0"], P["beam_bot_z"] + 2.0), "xytext": (2.0, 23.5)},
        ]))

    written.append(cv.render_review_section(
        latch_bodies(0.0, 1.0), out("review_section_latch_released.png"),
        plane="x", at=ee, colors=COLORS, hatches=HATCH,
        label="SECTION E-E (released)",
        title="latch RELEASED - same plane, same scale, tooth clear of the keeper",
        extent=lat_extent,
        context_note="declared compliant configuration: the beam pulled %.1f mm outward"
                     % P["latch_deflect"],
        arrows=[{"xy": (G["beam_y0"] + 1.0, 26.5), "dxy": (-7.0, 0.0), "text": "PULL",
                 "toff": (0.0, 1.6)},
                {"xy": (16.0, 43.0), "dxy": (0.0, 7.0), "text": "NOW FREE TO OPEN",
                 "toff": (0.0, 1.0), "color": "#0b6b3a"}],
        annotations=[
            {"text": "the tooth is now outboard of the keeper's front face,\n"
                     "so nothing stands over it",
             "xy": (ky - 1.2, P["tooth_top_z"] - 1.0), "xytext": (-15.0, 26.0)},
            {"text": "the keeper is untouched - it is still there;\nthe tooth has moved past it",
             "xy": (ky + 1.2, P["keeper_z0"] + 1.8), "xytext": (-15.0, 50.0)},
        ]))

    # ---------------------------------------------------- operation sequence
    op_extent = (-30, 118, -6, 116)
    seq = [
        ("01_closed_latched", 0.0, 0.0, "CLOSED - LATCH ENGAGED", "#8e44ad",
         "the tooth is behind the keeper; the lid cannot be lifted"),
        ("02_release_pressed", 0.0, 1.0, "RELEASE - PAD PULLED OUT", "#b03a2e",
         "the beam is deflected %.1f mm; the tooth is clear" % P["latch_deflect"]),
        ("03_opening_started", 12.0, 0.0, "OPENING STARTED", "#b03a2e",
         "the tooth is above the keeper, so the beam has already sprung back"),
        ("04_open", P["open_angle_deg"], 0.0, "OPEN - %.0f deg" % P["open_angle_deg"],
         "#1e8449", "stop block on the rear wall; the pin still carries the hinge"),
        ("05_reclosed_latched", 0.0, 0.0, "RECLOSED - SNAP RE-ENGAGED", "#8e44ad",
         "the lead-in ramp did the work; nothing was pushed back by hand"),
    ]
    for name, deg, latch, label, col, note in seq:
        anns = [{"text": "no separate bolt, knob, boss or socket exists\n"
                         "in this product",
                 "xy": (P["latch_x_centre"], -2.0), "xytext": (-28.0, -4.0)}]
        arrows = []
        if name.startswith("01"):
            arrows = [{"xy": (60.0, 62.0), "dxy": (0.0, 12.0),
                       "text": "OPENING BLOCKED", "toff": (0.0, 1.2)}]
        elif name.startswith("02"):
            arrows = [{"xy": (P["latch_x_centre"], 6.0), "dxy": (0.0, -14.0),
                       "text": "PULL THE PAD (-Y)", "toff": (0.0, -4.0)}]
        elif name.startswith("03"):
            arrows = [{"xy": (60.0, 58.0), "dxy": (0.0, 16.0),
                       "text": "LID ROTATES OPEN", "toff": (0.0, 1.2),
                       "color": "#1e8449"}]
        elif name.startswith("05"):
            arrows = [{"xy": (60.0, 74.0), "dxy": (0.0, -14.0),
                       "text": "PUSH SHUT - THE LATCH SNAPS BACK", "toff": (0.0, -4.0),
                       "color": "#8e44ad"}]
        written.append(cv.render_review_section(
            latch_bodies(deg, latch), out("review_operation_%s.png" % name),
            plane="x", at=ee, colors=COLORS, hatches=HATCH,
            label="OPERATION %s of 5" % name[:2].lstrip("0"),
            title=label, extent=op_extent, context_note=note,
            arrows=arrows, annotations=anns))

    return [w for w in written if w]


if __name__ == "__main__":
    for w in render_all():
        print("wrote %-62s %7d bytes" % (os.path.relpath(w, HERE), os.path.getsize(w)))
