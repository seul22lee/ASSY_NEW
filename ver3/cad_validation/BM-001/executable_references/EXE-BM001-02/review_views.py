"""Human-review drawing set for EXE-BM001-02.

Drawings, not renders. Orthographic, normal to the cut, cut faces hatched,
nothing behind the plane drawn, every detail cut located on the overview.

The set has to answer nine questions without anyone opening build.py:

    where are the snap-fit features        overview, A-A, C-C, D-D
    how is the cover assembled             assembly 01-03, C-C
    what retains it under the rails        A-A, B-B
    why can it not lift out at full open   B-B, operation 04
    what keeps it closed                   D-D engaged, operation 01
    where does the user press              overview, operation 02
    in which direction                     overview, operation 02 (arrows)
    which way does the cover slide         overview, operation 03 (arrows)
    how does the latch re-engage           D-D released, operation 05

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

COLORS = {"BODY-ENCLOSURE": "#8fb0cc", "BODY-COVER": "#d7a878"}
HATCH = {"BODY-ENCLOSURE": "///", "BODY-COVER": "\\\\\\"}
SHOTS = os.path.join(HERE, "screenshots")

P = B.load_params()
G = B.geom(P)

# where the detail cuts are taken
AA_X = G["closed_x0"] + P["tab_b_offset"] + P["tab_ear_len"] / 2.0     # through an ear
CC_X = G["closed_x0"] + P["tab_a_offset"] + P["tab_ear_len"] / 2.0
BB_X = AA_X - P["travel"]                                             # same ear, open
DD_Y = P["latch_y0"] + P["latch_w"] / 2.0            # latch finger centreline
RAIL_Y = (G["tab_near_tip_y"] + G["lip_near_y1"]) / 2.0               # inside ear AND lip

ASM_NOTE = ("geometric state illustration of a declared compliant configuration "
            "- not a deformation simulation")


def out(n):
    return os.path.join(SHOTS, n)


def cover_at(slide=0.0, lift=0.0, *, compressed=False, released=False):
    """The enclosure, plus one cover body placed and configured."""
    shape = B.build_cover(P, tabs_compressed=compressed, latch_released=released)
    body = cv.Body("BODY-COVER", "sliding cover", "GENERIC_COMPLIANT_POLYMER", shape)
    enc = cv.Body("BODY-ENCLOSURE", "enclosure", "GENERIC_RIGID_POLYMER",
                  B.build_enclosure(P))
    return [enc, body.moved(cv.translation((-slide, 0.0, lift)))]


def render_all() -> list:
    w = []
    lip_gap = G["lip_far_y0"] - G["lip_near_y1"]
    cmp_span = cv.bbox_of(B.build_cover(P, tabs_compressed=True))["dy"]
    rel_span = cv.bbox_of(B.build_cover(P))["dy"]
    engage = P["lip_overhang"] - P["guide_gap"]

    # =============================================================== overview
    w.append(cv.render_review_section(
        cover_at(), out("review_overview_operation_and_sections.png"),
        plane="z", at=P["box_z"] + P["cover_t"] / 2.0,
        colors=COLORS, hatches=HATCH, label="OVERVIEW  (plan, closed and latched)",
        title="EXE-BM001-02 - two bodies, how it works, and where the cuts are taken",
        extent=(-16, 218, -26, 98),
        context_note="BODY-ENCLOSURE hatched /// , BODY-COVER hatched \\\\\\",
        section_lines=[{"at": AA_X, "label": "A-A"}, {"at": CC_X, "label": "C-C"},
                       {"at": DD_Y, "label": "D-D", "along": "v"}],
        arrows=[
            {"xy": (124.0, 80.0), "dxy": (-44.0, 0.0), "text": "COVER SLIDES OPEN",
             "toff": (0.0, 1.5)},
            {"xy": (207.0, -12.0), "dxy": (0.0, 14.0),
             "text": "PUSH HERE (+Y)", "tha": "left", "toff": (3.0, -7.0)},
        ],
        annotations=[
            {"text": "BODY-COVER: plate, four retention tabs, one latch finger.\n"
                     "Everything that retains or latches it belongs to it.",
             "xy": (150.0, 30.0), "xytext": (66.0, 92.0)},
            {"text": "BODY-ENCLOSURE: cavity, top panel, two captive rails",
             "xy": (40.0, 35.0), "xytext": (-14.0, 92.0)},
            {"text": "near guide wall. The retaining lip is above this\nplane - see A-A and B-B",
             "xy": (150.0, 1.5), "xytext": (-14.0, -24.0)},
            {"text": "retention tab: cantilever beam + ear under the lip (x4)",
             "xy": (CC_X + 2.0, 4.4), "xytext": (10.0, 22.0)},
            {"text": "latch finger and tooth, out through the end wall.\n"
                     "Over the rail, not over the aperture - so at full open\n"
                     "it retracts over the ledge and not into the opening.",
             "xy": (196.0, 9.0), "xytext": (96.0, -24.0)},
        ]))

    # ====================================================== assembly sequence
    w.append(cv.render_review_section(
        cover_at(lift=24.0, compressed=True), out("review_assembly_01_aligned.png"),
        plane="x", at=AA_X, colors=COLORS, hatches=HATCH,
        label="ASSEMBLY 1 of 3", title="cover aligned above the rails, tabs already held in",
        extent=(-6, 76, 28, 84), context_note=ASM_NOTE,
        arrows=[{"xy": (35.0, 62.0), "dxy": (0.0, -10.0), "text": "PRESS STRAIGHT DOWN",
                 "toff": (0.0, 1.5)},
                {"xy": (2.5, 67.5), "dxy": (2.2, 0.0), "color": "#7d3c98"},
                {"xy": (67.5, 67.5), "dxy": (-2.2, 0.0), "color": "#7d3c98",
                 "text": "tabs held in 2.2 mm each side", "toff": (-33.0, 4.0)}],
        annotations=[
            {"text": "retaining lip (BODY-ENCLOSURE) - what the ear\nhas to get past, and then under",
             "xy": (4.1, 46.9), "xytext": (13.0, 40.0)},
            {"text": "retention ear, deflected inboard", "xy": (7.2, 65.5),
             "xytext": (16.0, 55.0)},
            {"text": "the gap between the lip inner edges is %.1f mm and the cover\n"
                     "with its tabs held in spans %.1f mm, so it comes straight down"
                     % (lip_gap, cmp_span),
             "xy": (35.0, 68.0), "xytext": (-4.0, 79.0)},
        ]))

    w.append(cv.render_review_section(
        cover_at(compressed=True), out("review_assembly_02_tabs_compressed.png"),
        plane="x", at=AA_X, colors=COLORS, hatches=HATCH,
        label="ASSEMBLY 2 of 3",
        title="tabs passing the lips - the actual limiting opening, at the moment of passage",
        extent=(-6, 76, 28, 58), context_note=ASM_NOTE,
        annotations=[
            {"text": "limiting opening %.1f mm: the real gap between the lip\n"
                     "inner edges, not an axis-aligned bounding box" % lip_gap,
             "xy": (G["lip_near_y1"], 46.5), "xytext": (7.0, 53.0)},
            {"text": "ear passing 0.2 mm clear of the lip", "xy": (5.6, 43.5),
             "xytext": (12.0, 29.5)},
            {"text": "two bodies only - nothing is inserted here",
             "xy": (35.0, 42.0), "xytext": (40.0, 29.5)},
        ]))

    w.append(cv.render_review_section(
        cover_at(), out("review_assembly_03_tabs_recovered.png"),
        plane="x", at=AA_X, colors=COLORS, hatches=HATCH,
        label="ASSEMBLY 3 of 3",
        title="tabs recovered under the lips - the cover is now captive",
        extent=(-6, 76, 28, 58),
        context_note="relaxed configuration; this is the as-built and as-operated state",
        arrows=[{"xy": (9.0, 54.5), "dxy": (-4.4, 0.0), "color": "#7d3c98"},
                {"xy": (61.0, 54.5), "dxy": (4.4, 0.0), "color": "#7d3c98",
                 "text": "ears spring outward", "toff": (-26.0, 1.0)}],
        annotations=[
            {"text": "%.1f mm of ear now under the lip. Relaxed span %.1f mm against\n"
                     "a %.1f mm opening: it cannot go back out the way it came."
                     % (engage, rel_span, lip_gap),
             "xy": (4.4, 45.2), "xytext": (11.0, 51.5)},
            {"text": "plate seated on both ledges", "xy": (35.0, 40.0),
             "xytext": (24.0, 31.0)},
        ]))

    # ===================================================== operating sequence
    # The latch works in the horizontal plane, so its views are PLANS. A
    # longitudinal cut would show the finger but never the tooth, which projects
    # sideways - exactly the half-of-the-relationship mistake to avoid.
    PLAN_Z = P["box_z"] + P["cover_t"] / 2.0
    lat_extent = (140, 214, -8, 30)

    w.append(cv.render_review_section(
        cover_at(), out("review_operation_01_closed_latched.png"),
        plane="z", at=PLAN_Z, colors=COLORS, hatches=HATCH,
        label="OPERATION 1 of 5",
        title="CLOSED and LATCHED - the tooth stands behind the end wall",
        extent=lat_extent, context_note="plan at mid-cover; opening is blocked by solid material",
        arrows=[{"xy": (176.0, -4.0), "dxy": (-16.0, 0.0), "text": "OPENING BLOCKED",
                 "toff": (0.0, 1.0)}],
        annotations=[
            {"text": "latch tooth: projects %.1f mm outboard from the finger"
                     % P["latch_lug_w"], "xy": (192.0, 4.4), "xytext": (196.0, -6.5)},
            {"text": "KEEPER - the strip of end wall left standing beside the slot.\n"
                     "%.1f mm of it is behind the tooth." % G["latch_engage_mm"],
             "xy": (188.5, 4.5), "xytext": (142.0, 22.0)},
            {"text": "%.1f mm free play, then solid wall" % P["latch_free_play"],
             "xy": (190.3, 5.5), "xytext": (158.0, 14.0)},
            {"text": "the release pad is out here, clear of the aperture in Y",
             "xy": (198.0, 9.0), "xytext": (150.0, 27.0)},
        ]))

    w.append(cv.render_review_section(
        cover_at(released=True), out("review_operation_02_release_pressed.png"),
        plane="z", at=PLAN_Z, colors=COLORS, hatches=HATCH,
        label="OPERATION 2 of 5",
        title="RELEASE - push the exterior pad inboard and the tooth clears the keeper",
        extent=lat_extent,
        context_note="declared compliant configuration: finger pushed %.1f mm inboard"
                     % P["latch_shift"],
        arrows=[{"xy": (199.0, -5.0), "dxy": (0.0, 6.0), "text": "PUSH  (+Y, inboard)",
                 "toff": (2.0, -3.0), "tha": "left"},
                {"xy": (176.0, -4.0), "dxy": (-16.0, 0.0), "text": "NOW FREE",
                 "toff": (0.0, 1.0), "color": "#0b6b3a"}],
        annotations=[
            {"text": "the tooth has moved inboard of the slot edge, so it can pass\n"
                     "straight through the slot with the rest of the finger",
             "xy": (192.0, 7.0), "xytext": (144.0, 22.0)},
            {"text": "%.0f mm of pad standing outside the product envelope.\n"
                     "No tool and no separate part." % (G["finger_x1"] - P["box_x"]),
             "xy": (198.0, 11.0), "xytext": (152.0, 27.0)},
        ]))

    w.append(cv.render_review_section(
        cover_at(slide=P["travel"] / 2.0), out("review_operation_03_slide_open.png"),
        plane="z", at=PLAN_Z, colors=COLORS, hatches=HATCH,
        label="OPERATION 3 of 5", title="SLIDING - the cover runs on the rails, still captive",
        extent=(-16, 218, -18, 88),
        context_note="mid travel, %.0f mm of %.0f mm" % (P["travel"] / 2.0, P["travel"]),
        arrows=[{"xy": (122.0, 80.0), "dxy": (-40.0, 0.0), "text": "SLIDE OPEN  (-X)",
                 "toff": (0.0, 1.5)}],
        annotations=[
            {"text": "the finger has sprung back: it is only deflected while the tooth\n"
                     "is alongside the end wall, the first %.0f mm of travel"
                     % P["latch_hold_travel"],
             "xy": (150.0, 9.0), "xytext": (108.0, -16.0)},
            {"text": "all four tabs still in the rails (see A-A and B-B)",
             "xy": (CC_X - P["travel"] / 2.0, 5.0), "xytext": (18.0, 20.0)},
            {"text": "cover parks over the solid top panel", "xy": (60.0, 40.0),
             "xytext": (-14.0, 84.0)},
        ]))

    # A longitudinal cut through the rail shows the lip and the ears but has no
    # aperture in it at all - the aperture is inboard of the rails. So the
    # full-open view is a PLAN, where the 84 mm actually exists to be measured,
    # and the lip relation at this position is carried by section B-B.
    w.append(cv.render_review_section(
        cover_at(slide=P["travel"]), out("review_operation_04_full_open_captive.png"),
        plane="z", at=P["box_z"] + P["cover_t"] / 2.0, colors=COLORS, hatches=HATCH,
        label="OPERATION 4 of 5",
        title="FULL OPEN - %.0f mm of the %.0f mm aperture is clear, and the cover is still captive"
              % (P["travel"], P["far_wall_x"] - P["deck_x1"]),
        extent=(-16, 218, -18, 88),
        context_note="plan at mid-cover; B-B is the same position seen across the rail",
        section_lines=[{"at": BB_X, "label": "B-B"}],
        arrows=[{"xy": (103.0, 80.0), "dxy": (84.0, 0.0),
                 "text": "%.0f mm USABLE OPENING" % P["travel"], "toff": (0.0, 1.5)},
                {"xy": (60.0, -10.0), "dxy": (-30.0, 0.0), "text": "cover came this way",
                 "toff": (0.0, 1.5), "color": "#7d3c98"}],
        annotations=[
            {"text": "open bound: the cover's end face on solid material at x = %.0f.\n"
                     "A stop, not a relief - there is no gap in the rails to lift through."
                     % G["rail_x0"], "xy": (13.5, 45.0), "xytext": (16.0, -16.0)},
            {"text": "aperture, now uncovered from x = 103 to x = 187",
             "xy": (150.0, 35.0), "xytext": (112.0, 60.0)},
            {"text": "all four retention tabs are still inside the rails,\n"
                     "under lips that run the whole length (see B-B)",
             "xy": (BB_X, 5.0), "xytext": (24.0, 20.0)},
            {"text": "the cover has not left the rails and cannot",
             "xy": (60.0, 45.0), "xytext": (-14.0, 84.0)},
        ]))

    w.append(cv.render_review_section(
        cover_at(), out("review_operation_05_reclosed_and_latched.png"),
        plane="z", at=PLAN_Z, colors=COLORS, hatches=HATCH,
        label="OPERATION 5 of 5",
        title="RECLOSED - the ramp pushed the finger aside, then the tooth sprang back",
        extent=lat_extent,
        context_note="the same state as OPERATION 1: the cycle returns what it started with",
        arrows=[{"xy": (170.0, -4.0), "dxy": (16.0, 0.0), "text": "SLIDE CLOSED  (+X)",
                 "toff": (0.0, 1.0)}],
        annotations=[
            {"text": "the sloped face is the lead-in: pushing the cover shut drives it\n"
                     "against the keeper corner, which deflects the finger on its own",
             "xy": (193.0, 5.0), "xytext": (142.0, 22.0)},
            {"text": "past the keeper the tooth springs back and blocks opening again",
             "xy": (190.7, 4.0), "xytext": (146.0, 27.0)},
        ]))

    # ============================================================== sections
    rail_extent = (-6, 76, 26, 58)
    w.append(cv.render_review_section(
        cover_at(), out("review_section_AA_captive_rail_closed.png"),
        plane="x", at=AA_X, colors=COLORS, hatches=HATCH,
        label="SECTION A-A", title="the captive rail, closed - all three rail functions at once",
        extent=rail_extent, context_note="cut through a retention ear, closed position",
        annotations=[
            {"text": "1. LEDGE - carries the cover (INT-01/02)",
             "xy": (11.0, 40.0), "xytext": (16.0, 35.5)},
            {"text": "2. GUIDE WALL - locates it sideways,\n"
                     "0.2 mm on the tab tip (INT-03/04)",
             "xy": (3.0, 42.5), "xytext": (-5.0, 51.5)},
            {"text": "3. RETAINING LIP - overhangs the ear\nand blocks lift (INT-05/06)",
             "xy": (4.6, 46.9), "xytext": (17.0, 52.5)},
            {"text": "the plate passes between the lips - which is how it got in,\n"
                     "and why no relief is cut anywhere in the rails",
             "xy": (35.0, 45.0), "xytext": (30.0, 29.0)},
        ]))

    w.append(cv.render_review_section(
        cover_at(slide=P["travel"]), out("review_section_BB_captive_rail_full_open.png"),
        plane="x", at=BB_X, colors=COLORS, hatches=HATCH,
        label="SECTION B-B",
        title="the same capture at FULL OPEN - nothing about it has changed",
        extent=rail_extent,
        context_note="cut through the same ear, now at the %.0f mm bound" % P["travel"],
        arrows=[{"xy": (35.0, 46.0), "dxy": (0.0, 8.0),
                 "text": "ORDINARY REMOVAL DIRECTION", "toff": (0.0, 0.8)}],
        annotations=[
            {"text": "the ear is under the lip here exactly as it is when closed.\n"
                     "A 3 mm lift meets 124.8 mm^3 of solid at 0, 10, 40, 70 and 84 mm.",
             "xy": (4.4, 45.2), "xytext": (6.0, 27.5)},
            {"text": "no opening, no relief, no removal position",
             "xy": (66.0, 46.9), "xytext": (36.0, 54.0)},
        ]))

    w.append(cv.render_review_section(
        cover_at(compressed=True), out("review_section_CC_assembly_snap.png"),
        plane="x", at=CC_X, colors=COLORS, hatches=HATCH,
        label="SECTION C-C",
        title="the assembly snap - compressed tab against the limiting gap",
        extent=(-6, 76, 28, 58), context_note=ASM_NOTE,
        arrows=[{"xy": (10.0, 55.0), "dxy": (-4.4, 0.0), "color": "#7d3c98"},
                {"xy": (60.0, 55.0), "dxy": (4.4, 0.0), "color": "#7d3c98",
                 "text": "recovery on release", "toff": (-25.0, 1.0)}],
        annotations=[
            {"text": "COMPRESSED: ear tip at y = %.1f, inboard of the lip inner edge\n"
                     "at y = %.1f. Span %.1f mm through a %.1f mm gap, %.1f mm clear."
                     % (G["tab_near_tip_y"] + P["tab_deflection"], G["lip_near_y1"],
                        cmp_span, lip_gap, lip_gap - cmp_span),
             "xy": (5.6, 43.5), "xytext": (13.0, 52.0)},
            {"text": "RECOVERED (see A-A): the tip returns to y = %.1f and %.1f mm\n"
                     "of ear sits under the lip" % (G["tab_near_tip_y"], engage),
             "xy": (4.4, 45.6), "xytext": (8.0, 31.5)},
            {"text": "the beam deflects into a %.1f mm slot cut in the plate"
                     % P["tab_slot_w"], "xy": (10.4, 41.0), "xytext": (42.0, 33.0)},
        ]))

    dd_extent = (180, 208, -6, 20)
    w.append(cv.render_review_section(
        cover_at(), out("review_section_DD_latch_engaged.png"),
        plane="z", at=PLAN_Z, colors=COLORS, hatches=HATCH,
        label="SECTION D-D", title="latch ENGAGED - one connected feature, from pad to tooth",
        extent=dd_extent,
        context_note="detail of the plan cut, at the end wall; finger, ramp and tooth are one solid",
        arrows=[{"xy": (188.0, -3.0), "dxy": (-6.0, 0.0), "text": "BLOCKED", "toff": (0.0, 0.8)}],
        annotations=[
            {"text": "release pad (FEA-C-RELEASE-PAD)", "xy": (198.0, 11.5),
             "xytext": (186.0, 17.0)},
            {"text": "tooth, %.1f mm outboard of the finger" % P["latch_lug_w"],
             "xy": (192.5, 4.2), "xytext": (194.0, -5.0)},
            {"text": "keeper: the end wall standing beside the slot,\n"
                     "%.1f mm of it behind the tooth" % G["latch_engage_mm"],
             "xy": (187.5, 4.0), "xytext": (180.5, 8.5)},
            {"text": "slot edge at y = %.1f; the finger runs through inboard of it"
                     % G["slot_y0"], "xy": (189.5, 5.7), "xytext": (183.0, 17.5)},
        ]))

    w.append(cv.render_review_section(
        cover_at(released=True), out("review_section_DD_latch_released.png"),
        plane="z", at=PLAN_Z, colors=COLORS, hatches=HATCH,
        label="SECTION D-D (released)",
        title="latch RELEASED - same plane, same scale, tooth clear of the keeper",
        extent=dd_extent,
        context_note="declared compliant configuration: finger and tooth pushed %.1f mm inboard"
                     % P["latch_shift"],
        arrows=[{"xy": (199.0, -3.0), "dxy": (0.0, 6.0), "text": "PUSH", "toff": (1.5, -3.0),
                 "tha": "left"},
                {"xy": (188.0, -3.0), "dxy": (-6.0, 0.0), "text": "NOW FREE TO SLIDE",
                 "toff": (0.0, 0.8), "color": "#0b6b3a"}],
        annotations=[
            {"text": "the tooth is now inboard of y = %.1f, the slot edge, so the whole\n"
                     "assembly passes out through the slot" % G["slot_y0"],
             "xy": (192.5, 7.0), "xytext": (180.5, 16.5)},
            {"text": "the keeper strip is untouched. It is still there;\n"
                     "the tooth has simply moved past it.",
             "xy": (188.5, 4.5), "xytext": (180.5, -5.0)},
        ]))
    return [x for x in w if x]


if __name__ == "__main__":
    for x in render_all():
        print("wrote %-56s %7d bytes" % (os.path.relpath(x, HERE), os.path.getsize(x)))
