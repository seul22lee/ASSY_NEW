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
    bodies = B.configuration(B.build(P), P, "S_CLOSED_RETAINED")
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
        bodies, out("review_overview_section_lines.png"), plane="z", at=plan_z,
        colors=COLORS, hatches=HATCH, label="OVERVIEW  (plan)",
        title="EXE-BM001-01 - whole footprint, with the detail cuts located",
        extent=(-10, 130, -10, 108),
        context_note="A-A, B-B and D-D are taken where marked",
        section_lines=[{"at": ex, "label": "B-B"}, {"at": cx, "label": "A-A"},
                       {"at": ay, "label": "D-D", "along": "v"}],
        annotations=[
            {"text": "closure plate covers the aperture", "xy": (60.0, 40.0),
             "xytext": (6.0, 18.0)},
            {"text": "retention bolt through the closure", "xy": (60.0, 9.0),
             "xytext": (72.0, -6.0)},
            {"text": "five interleaved knuckles on the pin", "xy": (60.0, ay),
             "xytext": (10.0, 100.0)},
            {"text": "recovered snap barb (section C-C)", "xy": (kx_far + 2.5, ay),
             "xytext": (74.0, 100.0)},
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
    return [w for w in written if w]


if __name__ == "__main__":
    for w in render_all():
        print("wrote %-62s %7d bytes" % (os.path.relpath(w, HERE), os.path.getsize(w)))
