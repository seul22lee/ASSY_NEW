"""Human-review section set for EXE-BM001-02.

Same standard as EXE-BM001-01: drawings, not renders. Orthographic, normal to
the cut, cut faces hatched, nothing behind the plane drawn, and every detail cut
located on an overview by a section line.

Four things a reviewer has to be able to see, and one view each:

    A-A  how the cover is supported and guided
    B-B  what stops it lifting off - at full open, where it matters
    C-C  the rivet and its anti-withdrawal lugs, along the slot
    D-D  the latch hook against its keeper

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

COLORS = {"BODY-ENCLOSURE": "#8fb0cc", "BODY-COVER": "#d7a878", "BODY-RIVET": "#a79ccc"}
HATCH = {"BODY-ENCLOSURE": "///", "BODY-COVER": "\\\\\\", "BODY-RIVET": "xxx"}
SHOTS = os.path.join(HERE, "screenshots")


def render_all() -> list:
    P = B.load_params()
    G = B.geom(P)
    closed = B.configuration(B.build(P), P, "S_CLOSED_LATCHED")
    opened = B.configuration(B.build(P), P, "S_OPEN")
    released = B.configuration(B.build(P), P, "S_CLOSED_RELEASED")
    rx, ry = G["rivet_closed_x"], P["rivet_y"]
    # cut through a LUG, not between the arms: they deflect in +/-Y, so a
    # plane on the axis passes down the gap and shows no lug at all
    # inside BOTH the arm beam and its lug, so the arm reads as one connected
    # piece rather than a lug floating under the ledge
    body_y = ry + (P["barb_arm_inner_r"] + P["rivet_shaft_d"] / 2.0) / 2.0
    # OUTSIDE the slot width but still inside the lug, so the ledge the lug bears
    # against is present in the cut. A plane inside the slot shows the rivet whole
    # but has no ledge in it at all, which is the wrong thing for an anti-lift view.
    bear_y = ry + (P["slot_w"] / 2.0 + P["barb_d"] / 2.0) / 2.0
    rx_open = G["rivet_open_x"]
    written = []

    def out(n):
        return os.path.join(SHOTS, n)

    # ---- OVERVIEW: plan through the cover, whole footprint, cuts located
    plan_z = P["box_z"] + P["cover_t"] / 2.0
    written.append(cv.render_review_section(
        closed, out("review_overview_section_lines.png"), plane="z", at=plan_z,
        colors=COLORS, hatches=HATCH, label="OVERVIEW  (plan, closed)",
        title="EXE-BM001-02 - whole footprint, with the detail cuts located",
        extent=(-10, 200, -8, 78),
        context_note="A-A, C-C and D-D are taken where marked; B-B is C-C's\ndirection taken at full open, just outside the slot",
        section_lines=[{"at": 135.0, "label": "A-A"},
                       {"at": P["keeper_x0"] + 1.5, "label": "D-D"},
                       {"at": ry, "label": "C-C", "along": "v"}],
        annotations=[
            {"text": "cover, sliding in X", "xy": (150.0, 35.0), "xytext": (108.0, 66.0)},
            {"text": "snap rivet in its slot", "xy": (rx, ry), "xytext": (150.0, -5.0)},
            {"text": "latch beam cut from the plate",
             "xy": (105.0, P["latch_y0"] + P["latch_w"] / 2.0), "xytext": (30.0, 66.0)},
            {"text": "solid top panel: where the cover parks",
             "xy": (50.0, 35.0), "xytext": (6.0, 5.0)},
        ]))

    # ---- A-A: support and guidance, across the product
    written.append(cv.render_review_section(
        closed, out("review_section_cover_support_and_guides.png"), plane="x", at=135.0,
        colors=COLORS, hatches=HATCH, label="SECTION A-A",
        title="cover support and lateral guidance",
        extent=(-6, 76, 26, 52),
        context_note="closed; how the cover is carried and located",
        annotations=[
            {"text": "cover rides on the ledge (INT-01).\nThe gap between the two posts is\nthe rivet slot, cut through here",
             "xy": (4.0, P["box_z"]), "xytext": (-5.0, 28.5)},
            {"text": "guide wall locates it sideways, 0.2 clearance (INT-03)",
             "xy": (3.0, 42.5), "xytext": (14.0, 49.5)},
            {"text": "nothing overhangs the cover - the rivet does the holding down",
             "xy": (35.0, 45.0), "xytext": (16.0, 27.5)},
        ]))

    # ---- B-B: the anti-lift relation, at FULL OPEN
    written.append(cv.render_review_section(
        opened, out("review_section_captive_at_full_open.png"), plane="y", at=bear_y,
        colors=COLORS, hatches=HATCH, label="SECTION B-B",
        title="what prevents removal at FULL OPEN - the rivet lugs under the ledge",
        extent=(rx_open - 26, rx_open + 26, 26, 52),
        context_note="cover at 84 mm, its open terminal bound",
        annotations=[
            {"text": "lug shoulder against the ledge underside (INT-07):\n"
                     "the cover cannot lift, here or anywhere",
             "xy": (rx_open + 2.0, G["lug_top"]), "xytext": (rx_open - 24, 29.5)},
            {"text": "ledge - present in this cut because it is taken\n"
                     "just outside the slot, where the lug actually bears",
             "xy": (rx_open + 14.0, 37.0), "xytext": (rx_open - 2.0, 48.5)},

        ]))

    # ---- C-C: the rivet along the slot
    written.append(cv.render_review_section(
        closed, out("review_section_rivet_and_slot.png"), plane="y", at=body_y,
        colors=COLORS, hatches=HATCH, label="SECTION C-C",
        title="snap rivet in its slot: travel bounds and anti-withdrawal",
        extent=(40, 200, 26, 52),
        context_note="closed; the slot spans the whole travel",
        annotations=[
            {"text": "rivet at the closed bound", "xy": (rx - 2.5, 41.0),
             "xytext": (152.0, 49.5)},
            {"text": "keeper bridge - it spans the walls out of this plane,\nwhich is why it stands free here",
             "xy": (P["keeper_x0"] + 1.5, P["keeper_z1"]), "xytext": (52.0, 48.0)},
            {"text": "the slot is exactly travel + slot width long,\n"
                     "so its ends ARE the two bounds",
             "xy": (100.0, 36.0), "xytext": (52.0, 28.0)},
            {"text": "lugs span 7.6 across a 5.4 slot once recovered",
             "xy": (rx + 2.0, G["lug_bot"] + 1.0), "xytext": (96.0, 28.5)},
        ]))

    # ---- D-D: the latch, engaged and released
    written.append(cv.render_review_section(
        closed, out("review_section_latch_engaged.png"), plane="y",
        at=P["latch_y0"] + P["latch_w"] / 2.0,
        colors=COLORS, hatches=HATCH, label="SECTION D-D",
        title="latch ENGAGED - hook behind the keeper blocks opening",
        extent=(78, 130, 32, 54),
        context_note="closed and latched",
        annotations=[
            {"text": "hook stands 1.0 clear; the cover moves 1 mm, then is blocked",
             "xy": (98.5, 46.5), "xytext": (104.0, 52.0)},
            {"text": "keeper bridge, fixed to the guide walls",
             "xy": (P["keeper_x0"] + 1.5, P["keeper_z1"]), "xytext": (79.0, 51.5)},
            {"text": "the top panel is relieved along the whole beam path,\nso the beam can be pressed at any cover position",
             "xy": (P["deck_x1"] - 0.5, 38.5), "xytext": (79.0, 33.5)},
        ]))

    written.append(cv.render_review_section(
        released, out("review_section_latch_released.png"), plane="y",
        at=P["latch_y0"] + P["latch_w"] / 2.0,
        colors=COLORS, hatches=HATCH, label="SECTION D-D (released)",
        title="latch RELEASED - beam pressed down, hook clear of the keeper",
        extent=(78, 130, 32, 54),
        context_note="the declared compliant configuration; the cover is now free to slide",
        annotations=[
            {"text": "beam deflected %.1f mm; hook now passes under the keeper"
                     % P["latch_deflection"],
             "xy": (98.5, 44.0), "xytext": (103.0, 52.0)},
            {"text": "press here - the beam's own face, reached through the aperture",
             "xy": (110.0, P["box_z"] + P["cover_t"] - P["latch_deflection"]),
             "xytext": (86.0, 33.0)},
        ]))
    return [w for w in written if w]


if __name__ == "__main__":
    for w in render_all():
        print("wrote %-58s %7d bytes" % (os.path.relpath(w, HERE), os.path.getsize(w)))
