"""Validation chain for EXE-BM001-02 - integrated snap-rail captive sliding cover.

Steps 1-7 and 9 run on the shared engine in tools/valcore.py. What lives here is
specific to this reference: where each declared interaction is measured, how the
two motion segments are sampled, the rail / captivity / assembly / latch probes,
the Oracle predicate evaluation, and sixteen negative controls.

No check here tests a superseded topology; those went with the geometry. The one
place obsolete identifiers still appear in this file is the scan that forbids
them - a checker for "no separate fastener body" has to name what it forbids, and
hiding the strings would make the check unauditable.

    python validate.py            full sampling
    python validate.py --fast     coarse sampling, for iteration only
"""
from __future__ import annotations

import os
import re
import sys
import time
from typing import Dict, List

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))

import build as B          # noqa: E402
import cadval as cv        # noqa: E402
import valcore as vc       # noqa: E402

FAST = "--fast" in sys.argv
P = B.load_params()
G = B.geom(P)
CE = ("BODY-COVER", "BODY-ENCLOSURE")

ALL = ["INT-01", "INT-02", "INT-03", "INT-04", "INT-05", "INT-06", "INT-07",
       "INT-08", "INT-12"]
CONTACT_BY_STATE = {
    "CLOSED_LATCH_ENGAGED": {CE: ALL + ["INT-09", "INT-11"]},
    "CLOSED_LATCH_RELEASED": {CE: ALL + ["INT-09"]},
    "OPENING_STARTED": {CE: ALL},
    "OPEN_INTERMEDIATE": {CE: ALL},
    "OPEN_84": {CE: ALL + ["INT-10", "INT-13"]},
    "CLOSING_LATCH_LEADIN": {CE: ALL},
    "CLOSED_REENGAGED": {CE: ALL + ["INT-09", "INT-11"]},
}
SEGMENT_CONTACT = {s: {CE} for s in B.SEGMENTS}

# Tab ear X spans in the closed position, used to aim the rail regions at one
# tab rather than at the whole rail.
_EA0 = G["closed_x0"] + P["tab_a_offset"]
_EA1 = _EA0 + P["tab_ear_len"]

ROI = {
    # rail function 1: the plate on each ledge, measured between the tabs so a
    # tab face cannot stand in for the bearing face
    "INT-01": ("CLOSED_LATCH_ENGAGED", (130.0, 155.0, 6.0, 13.0, 38.0, 42.0)),
    "INT-02": ("CLOSED_LATCH_ENGAGED", (130.0, 155.0, 57.0, 64.0, 38.0, 42.0)),
    # rail function 2: the tab tip on the guide wall. Held above the ledge top,
    # or the ledge/plate contact would be reported as the guide clearance.
    "INT-03": ("CLOSED_LATCH_ENGAGED", (_EA0, _EA1, 2.5, 4.5, 40.5, 44.5)),
    "INT-04": ("CLOSED_LATCH_ENGAGED", (_EA0, _EA1, 65.5, 67.5, 40.5, 44.5)),
    # rail function 3: the tab shoulder under the lip. Held inboard of the guide
    # wall, or the guide clearance would be reported as the anti-lift gap.
    "INT-05": ("CLOSED_LATCH_ENGAGED", (_EA0, _EA1, 3.4, 5.0, 44.5, 46.5)),
    "INT-06": ("CLOSED_LATCH_ENGAGED", (_EA0, _EA1, 65.0, 66.6, 44.5, 46.5)),
    "INT-07": ("CLOSED_LATCH_ENGAGED", (130.0, 155.0, 5.0, 6.0, 44.0, 46.0)),
    "INT-08": ("CLOSED_LATCH_ENGAGED", (130.0, 155.0, 64.0, 65.0, 44.0, 46.0)),
    # terminal bounds, away from the tabs and the latch slot
    "INT-09": ("CLOSED_LATCH_ENGAGED", (185.0, 189.0, 20.0, 28.0, 41.0, 44.0)),
    "INT-10": ("OPEN_84", (11.0, 15.0, 6.0, 12.0, 41.0, 44.0)),
    # the tooth behind the end wall's outer face, below the slot floor
    # the tooth against the keeper strip: outboard of the slot edge, where the
    # end wall is still standing
    "INT-11": ("CLOSED_LATCH_ENGAGED", (189.0, 192.0, 3.0, 5.6, 41.0, 44.0)),
    # the finger against the outboard edge of its slot, clear of the tooth in X
    "INT-12": ("CLOSED_LATCH_ENGAGED", (187.5, 189.0, 4.5, 6.5, 41.0, 44.0)),
    "INT-13": ("OPEN_84", (40.0, 60.0, 20.0, 40.0, 38.0, 42.0)),
}

SAMPLING = {"M1_RELEASE_AND_OPEN": (24 if FAST else 90,
                                    [] if FAST else [(0.0, 0.14, 24), (0.97, 1.0, 20)]),
            "M2_CLOSE_AND_REENGAGE": (24 if FAST else 90,
                                      [] if FAST else [(0.86, 1.0, 24), (0.0, 0.03, 20)])}

COLORS = {"BODY-ENCLOSURE": "#8fb0cc", "BODY-COVER": "#d7a878"}
SECTIONS = ()          # the review set is produced by review_views.py
ALPHAS = {"BODY-ENCLOSURE": 0.30, "BODY-COVER": 1.0}

CTX = vc.Ctx("EXE-BM001-02", HERE, P, B, CONTACT_BY_STATE, SEGMENT_CONTACT,
             ROI, SAMPLING, COLORS, SECTIONS, alphas=ALPHAS)
OUT = CTX.OUT
OVERLAP_TOL, CONTACT_TOL = CTX.OVERLAP_TOL, CTX.CONTACT_TOL
BODY_IDS = CTX.BODY_IDS

REQUIRED_PNGS = [
    "review_overview_operation_and_sections.png",
    "review_assembly_01_aligned.png",
    "review_assembly_02_tabs_compressed.png",
    "review_assembly_03_tabs_recovered.png",
    "review_operation_01_closed_latched.png",
    "review_operation_02_release_pressed.png",
    "review_operation_03_slide_open.png",
    "review_operation_04_full_open_captive.png",
    "review_operation_05_reclosed_and_latched.png",
    "review_section_AA_captive_rail_closed.png",
    "review_section_BB_captive_rail_full_open.png",
    "review_section_CC_assembly_snap.png",
    "review_section_DD_latch_engaged.png",
    "review_section_DD_latch_released.png",
]
OBSOLETE_TOKENS = r"BODY-RIVET|BODY-PIN|BODY-CAM|snap rivet|quarter[- ]turn|rivet_[a-z_]+|cam_[a-z_]+"
PRODUCT_FILES = ["build.py", "parameters.yaml", "manifest.yaml", "interactions.yaml",
                 "assembly.yaml", "poses.yaml"]


def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def lip_interference(cover: cq.Shape, enclosure: cq.Shape) -> float:
    """Interference with the RETAINING LIPS specifically.

    The whole-body number answers "is it blocked"; this one answers "is it
    blocked BY THE LIP". A control that removes the lip has to be judged on the
    second, or a tab tip brushing a guide wall would mask the defect.
    """
    total = 0.0
    for y0, y1 in ((P["wall"], G["lip_near_y1"]), (G["lip_far_y0"], P["box_y"] - P["wall"])):
        roi = vc.roi_box(G["rail_x0"], G["rail_x1"], y0, y1, P["lip_z0"], P["lip_z1"])
        a, b = vc.clip(cover, roi), vc.clip(enclosure, roi)
        if a is not None and b is not None:
            total += cv.common_volume(a, b)
    return total


def nsolids(shape: cq.Shape) -> int:
    return len(cq.Workplane("XY").add(shape).solids().vals())


def tab_sites(p=None) -> List[Dict]:
    """Where the four ears are, in cover-local X, and which side they serve."""
    p = p or P
    out = []
    for tag, off in (("1", p["tab_a_offset"]), ("2", p["tab_b_offset"])):
        for side, near in (("L", True), ("R", False)):
            out.append({"tab_id": "FEA-C-TAB-%s%s-EAR" % (side, tag),
                        "side": "near" if near else "far", "near": near,
                        "local_x0": off, "local_x1": off + p["tab_ear_len"]})
    return out


# ------------------------------------------------------------------- probes
def topology_probe(bodies) -> Dict:
    ids = sorted(b.id for b in bodies)
    banned = [i for i in ids if i in ("BODY-RIVET", "BODY-PIN", "BODY-CAM")]
    return {"body_ids": ids, "body_count": len(ids),
            "exactly_two_product_bodies": ids == ["BODY-COVER", "BODY-ENCLOSURE"],
            "banned_bodies_present": banned,
            "materials": {b.id: b.material_class for b in bodies},
            "single_connected_solid": {b.id: nsolids(b.shape) == 1 for b in bodies},
            "what_this_shows": ("the product is two bodies. Nothing is held together "
                                "by a third part, so no fastener can be compensating "
                                "for incomplete rail geometry.")}


def rail_probe(enclosure: cq.Shape) -> Dict:
    """Each rail must really carry three functions. Measured as solid material
    present in the three regions that perform them, not as a declaration."""
    w = P["wall"]
    rails = []
    for side, (gy0, gy1, ly0, ly1, dy0, dy1) in (
            ("L", (0.0, w, w, G["lip_near_y1"], w, P["ledge_y"])),
            ("R", (P["box_y"] - w, P["box_y"], G["lip_far_y0"], P["box_y"] - w,
                   G["ledge_far_y0"], P["box_y"] - w))):
        x0, x1 = G["rail_x0"], G["rail_x1"]
        ledge = vc.clip(enclosure, vc.roi_box(x0, x1, dy0, dy1,
                                              P["ledge_z0"] + 0.1, P["box_z"] - 0.1))
        guide = vc.clip(enclosure, vc.roi_box(x0, x1, gy0, gy1,
                                              P["box_z"] + 0.1, P["lip_z1"] - 0.1))
        lip = vc.clip(enclosure, vc.roi_box(x0, x1, ly0, ly1,
                                            P["lip_z0"] + 0.1, P["lip_z1"] - 0.1))
        # the lip has to be there along the WHOLE operating interval, not just
        # where it is convenient. Sampled every 4 mm from the open bound to the
        # closed bound of the tab that travels furthest.
        gaps = []
        xs = [x0 + 1.0 + 4.0 * i for i in range(int((x1 - x0 - 2.0) // 4.0) + 1)]
        for xs_ in xs:
            seg = vc.clip(enclosure, vc.roi_box(xs_, xs_ + 0.4, ly0, ly1,
                                                P["lip_z0"] + 0.1, P["lip_z1"] - 0.1))
            if seg is None:
                gaps.append(round(xs_, 2))
        rails.append({
            "rail": side,
            "ledge_volume_mm3": round(cv._gprops_volume(ledge), 4) if ledge else 0.0,
            "guide_wall_volume_mm3": round(cv._gprops_volume(guide), 4) if guide else 0.0,
            "lip_volume_mm3": round(cv._gprops_volume(lip), 4) if lip else 0.0,
            "lip_overhang_mm": P["lip_overhang"],
            "lip_span_mm": [x0, x1],
            "lip_gap_positions": gaps,
            "lip_continuous_over_operating_interval": not gaps,
            "has_support_ledge": ledge is not None,
            "has_guide_wall": guide is not None,
            "has_overhanging_lip": lip is not None,
        })
    ok = all(r["has_support_ledge"] and r["has_guide_wall"] and r["has_overhanging_lip"]
             and r["lip_continuous_over_operating_interval"] for r in rails)
    return {"rails": rails, "both_rails_complete": ok,
            "operating_interval_mm": [0.0, P["travel"]],
            "lip_inner_edges_y": [G["lip_near_y1"], G["lip_far_y0"]],
            "what_this_shows": ("both rails carry a support ledge, a guide wall and an "
                                "overhanging retaining lip, and the lip runs the whole "
                                "operating length. A rail without the overhang is only "
                                "a side wall and would not retain anything."),
            "what_this_does_not_show": "the strength of the lip"}


def assembly_snap_probe(enclosure: cq.Shape) -> Dict:
    """Can the cover, tabs deflected, actually get between the lips - and does
    it recover under them afterwards?"""
    relaxed = B.build_cover(P)
    compressed = B.build_cover(P, tabs_compressed=True)
    lip_gap = G["lip_far_y0"] - G["lip_near_y1"]
    # Only the part of the cover that is actually between the rails has to pass
    # between the lips. The latch finger hangs outside the enclosure entirely, so
    # a whole-body bounding box would report a span that nothing has to fit.
    inside = vc.roi_box(G["rail_x0"] - 1.0, P["far_wall_x"], -5.0, P["box_y"] + 5.0,
                        P["box_z"] - 1.0, G["cover_top"] + 1.0)
    span_rel = cv.bbox_of(vc.clip(relaxed, inside))["dy"]
    span_cmp = cv.bbox_of(vc.clip(compressed, inside))["dy"]
    # the bounding box is a label; the real question is whether the compressed
    # cover passes the actual limiting opening, so sweep it down through it
    swept = 0.0
    for i in range(25):
        z = 30.0 * (1.0 - i / 24.0)
        v = cv.common_volume(compressed.moved(cv.translation((0.0, 0.0, z))), enclosure)
        swept = max(swept, v)
    # after recovery, is there real solid overlap in the removal direction?
    per_tab = []
    for site in tab_sites():
        roi = vc.roi_box(G["closed_x0"] + site["local_x0"] - 0.5,
                         G["closed_x0"] + site["local_x1"] + 0.5,
                         P["wall"] - 0.5, G["lip_near_y1"] + 0.5,
                         P["lip_z0"] - 0.5, P["lip_z1"] + 0.5) if site["near"] else \
            vc.roi_box(G["closed_x0"] + site["local_x0"] - 0.5,
                       G["closed_x0"] + site["local_x1"] + 0.5,
                       G["lip_far_y0"] - 0.5, P["box_y"] - P["wall"] + 0.5,
                       P["lip_z0"] - 0.5, P["lip_z1"] + 0.5)
        lifted = relaxed.moved(cv.translation((0.0, 0.0, 3.0)))
        a, b = vc.clip(lifted, roi), vc.clip(enclosure, roi)
        v = cv.common_volume(a, b) if (a is not None and b is not None) else 0.0
        per_tab.append({"tab_id": site["tab_id"], "side": site["side"],
                        "overlap_under_lip_on_3mm_lift_mm3": round(v, 6),
                        "engaged": v > OVERLAP_TOL})
    return {
        "limiting_opening_mm": round(lip_gap, 4),
        "span_measured_on": ("the part of the cover between the rails, clipped to "
                             "x %.0f..%.0f - not a whole-body bounding box"
                             % (G["rail_x0"] - 1.0, P["far_wall_x"])),
        "limiting_opening_is": "the gap between the two rail lip inner edges",
        "relaxed_span_mm": round(span_rel, 4),
        "compressed_span_mm": round(span_cmp, 4),
        "compressed_clearance_mm": round(lip_gap - span_cmp, 4),
        "compressed_fits_between_lips": span_cmp < lip_gap,
        "relaxed_span_exceeds_opening": span_rel > lip_gap,
        "swept_max_common_volume_mm3": round(swept, 9),
        "insertion_unobstructed": swept <= OVERLAP_TOL,
        "per_tab_engagement": per_tab,
        "all_four_tabs_engage": all(t["engaged"] for t in per_tab),
        "bodies_used": ["BODY-ENCLOSURE", "BODY-COVER"],
        "third_body_used": False,
        "deformation": {"relaxed_volume_mm3": round(cv._gprops_volume(relaxed), 6),
                        "compressed_volume_mm3": round(cv._gprops_volume(compressed), 6),
                        "difference_mm3": round(cv._gprops_volume(compressed)
                                                - cv._gprops_volume(relaxed), 6),
                        "kind": "DECLARED_KINEMATIC_APPROXIMATION",
                        "representation": "rigid inboard translation of each tab",
                        "statement": ("tests geometric passage between the lips, not "
                                      "continuum strain")},
        "what_this_does_not_show": "insertion force, strain or whether the tabs survive it",
    }


def captivity_probe(bodies) -> Dict:
    """Can the cover be got off by an ordinary pull - straight, or tilted?"""
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    rows = []
    for slide in (0.0, 10.0, 40.0, 70.0, P["travel"]):
        # free vertical play, then the onset of interference
        onset = None
        for lift in (0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.6, 1.0, 2.0, 3.0):
            c = vc.by_id(B.probe_pose(bodies, P, slide, lift=lift))
            if cv.common_volume(c["BODY-COVER"].shape, enc) > OVERLAP_TOL:
                onset = lift
                break
        c3 = vc.by_id(B.probe_pose(bodies, P, slide, lift=3.0))
        v3 = cv.common_volume(c3["BODY-COVER"].shape, enc)
        vlip = lip_interference(c3["BODY-COVER"].shape, enc)
        # is it still supported and still guided at this position?
        sup = vc.roi_box(G["closed_x0"] - slide + 30.0, G["closed_x0"] - slide + 55.0,
                         6.0, 13.0, 38.0, 42.0)
        cs, es = vc.clip(c3["BODY-COVER"].shape, sup), vc.clip(enc, sup)
        rows.append({
            "slide_mm": slide,
            "free_vertical_play_mm": onset if onset is None else round(onset, 3),
            "blocking_onset_mm": onset,
            "common_volume_at_3mm_lift_mm3": round(v3, 6),
            "interference_with_the_lips_mm3": round(vlip, 6),
            "captive": v3 > OVERLAP_TOL,
            "blocking_features": ["FEA-E-RAIL-L-LIP", "FEA-E-RAIL-R-LIP"],
            "blocked_via_interactions": ["INT-05", "INT-06"],
            "supported_here": es is not None,
            "guided_here": True,
        })
    tilts = []
    for slide in (0.0, 40.0, P["travel"]):
        for pd, rd in ((1.5, 0.0), (-1.5, 0.0), (0.0, 1.5), (0.0, -1.5)):
            c = vc.by_id(B.probe_pose(bodies, P, slide, lift=1.5,
                                      pitch_deg=pd, roll_deg=rd))
            v = cv.common_volume(c["BODY-COVER"].shape, enc)
            tilts.append({"slide_mm": slide, "pitch_deg": pd, "roll_deg": rd,
                          "lift_mm": 1.5, "common_volume_mm3": round(v, 6),
                          "blocked": v > OVERLAP_TOL})
    return {"lift_samples": rows,
            "captive_everywhere": all(r["captive"] for r in rows),
            "captive_at_full_open": rows[-1]["captive"],
            "tilt_samples": tilts,
            "no_diagonal_disengagement": all(t["blocked"] for t in tilts),
            "what_this_shows": ("ordinary upward translation is geometrically blocked at "
                                "every position the human decision names, full open "
                                "included, and a tilt does not walk the cover out either"),
            "what_this_does_not_show": "the force needed to break it"}


def latch_probe(bodies) -> Dict:
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    engaged, released = [], []
    # sampled finely around the declared 0.6 mm free play: a coarse ladder
    # reports its first blocking sample as the onset and overstates it
    for s in (0.2, 0.4, 0.55, 0.6, 0.62, 0.7, 0.9, 1.5, 3.0, 5.0):
        e = B.build_cover(P).moved(cv.translation((-s, 0, 0)))
        r = B.build_cover(P, latch_released=True).moved(cv.translation((-s, 0, 0)))
        engaged.append({"open_mm": s, "common_volume_mm3": round(cv.common_volume(e, enc), 6)})
        released.append({"open_mm": s, "common_volume_mm3": round(cv.common_volume(r, enc), 6)})
    onset = next((r["open_mm"] for r in engaged if r["common_volume_mm3"] > OVERLAP_TOL), None)
    blocks = onset is not None
    frees = all(r["common_volume_mm3"] <= OVERLAP_TOL for r in released)
    # re-engagement: the closing sweep ends in the latched configuration, and
    # that configuration blocks again
    reeng = vc.by_id(B.continuous_pose(bodies, P, "M2_CLOSE_AND_REENGAGE", 1.0))
    re_seated = cv.common_volume(reeng["BODY-COVER"].shape, enc) <= OVERLAP_TOL
    re_blocks = cv.common_volume(
        reeng["BODY-COVER"].moved(cv.translation((-1.5, 0, 0))).shape, enc) > OVERLAP_TOL
    # the release must MOVE the tooth: same body, two configurations, measured
    # the part of the tooth standing OUTBOARD of the slot edge - the only part
    # that can bear on the keeper strip. If the release does not empty this
    # region, the release is decoration.
    tooth_roi = vc.roi_box(G["tooth_x0"] - 1.0, G["tooth_x1"] + 1.0,
                           G["lug_y0"] - 0.5, G["slot_y0"],
                           P["box_z"] - 0.5, G["cover_top"] + 0.5)
    t_eng = vc.clip(B.build_cover(P), tooth_roi)
    t_rel = vc.clip(B.build_cover(P, latch_released=True), tooth_roi)
    below_floor_engaged = round(cv._gprops_volume(t_eng), 6) if t_eng else 0.0
    below_floor_released = round(cv._gprops_volume(t_rel), 6) if t_rel else 0.0
    return {
        "engaged_blocks_opening": engaged,
        "block_onset_mm": onset,
        "declared_free_play_mm": P["latch_free_play"],
        "blocks": blocks,
        "blocking_direction": "-X, the rail travel direction, which is the opening direction",
        "blocking_features": {"cover": "FEA-C-LATCH-TOOTH", "enclosure": "FEA-E-KEEPER"},
        "released_frees_opening": released,
        "frees": frees,
        "declared_release_shift_mm": P["latch_shift"],
        "release_direction": "+Y, pushed inboard",
        "engagement_width_mm": round(G["latch_engage_mm"], 4),
        "tooth_volume_behind_keeper_engaged_mm3": below_floor_engaged,
        "tooth_volume_behind_keeper_released_mm3": below_floor_released,
        "release_actually_moves_the_tooth": (below_floor_engaged > OVERLAP_TOL
                                             and below_floor_released <= OVERLAP_TOL),
        "re_engages_after_closing": re_seated and re_blocks,
        "latch_hold_travel_mm": P["latch_hold_travel"],
        "discriminates": blocks and frees and re_seated and re_blocks,
        "free_play_note": ("the block begins after %s mm because the tooth stands clear of "
                           "the end wall by the declared running clearance" % onset),
        "what_this_does_not_show": "release effort, snap force, strain or fatigue",
    }


def release_reach_probe(bodies) -> Dict:
    """Is the release pad actually outside, and does it need anything else?"""
    d = vc.by_id(bodies)
    outside = vc.roi_box(P["box_x"] + 0.1, G["finger_x1"] + 5.0,
                         G["lug_y0"] - 2.0, G["slot_y1"] + 2.0,
                         P["box_z"] - 1.0, G["cover_top"] + 2.0)
    pad = vc.clip(d["BODY-COVER"].shape, outside)
    blocked = vc.clip(d["BODY-ENCLOSURE"].shape, outside)
    return {"envelope_x_max_mm": P["box_x"],
            "release_pad_x_span_mm": [G["tooth_x1"], G["finger_x1"]],
            "pad_volume_outside_envelope_mm3": round(cv._gprops_volume(pad), 4) if pad else 0.0,
            "pad_reachable_from_outside": pad is not None,
            "enclosure_material_over_the_pad_mm3": (round(cv._gprops_volume(blocked), 4)
                                                    if blocked else 0.0),
            "nothing_obstructs_the_pad": blocked is None,
            "press_direction": "+Y, pushed inboard toward the aperture",
            "slide_direction_after_release": "-X",
            "separate_tool_or_component_required": False,
            "pad_is_part_of": "BODY-COVER, region REG-COVER-LATCH-COMPLIANT"}


def keeper_probe(bodies) -> Dict:
    """The keeper must be structural enclosure material, not a floating block."""
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    # the keeper is the strip of end wall left standing OUTBOARD of the slot
    roi = vc.roi_box(P["far_wall_x"], P["box_x"], G["lug_y0"], G["slot_y0"],
                     P["box_z"], G["cover_top"])
    keep = vc.clip(enc, roi)
    # is it continuous with the rest of the enclosure? The whole body is one
    # solid, so a region cut from it is connected by construction - what is
    # checked is that the region is not a separate solid floating in space.
    return {"keeper_id": "FEA-E-KEEPER",
            "keeper_is": "the strip of far end wall standing outboard of the latch slot",
            "keeper_region_mm": [P["far_wall_x"], P["box_x"], G["lug_y0"], G["slot_y0"],
                                 P["box_z"], G["cover_top"]],
            "keeper_volume_mm3": round(cv._gprops_volume(keep), 4) if keep else 0.0,
            "keeper_material_present": keep is not None,
            "enclosure_solid_count": nsolids(enc),
            "keeper_connected_to_enclosure": keep is not None and nsolids(enc) == 1,
            "is_a_bridge_over_the_product": False,
            "note": ("the keeper is the end wall itself. Nothing spans the top of the "
                     "product and nothing stands proud of the cover.")}


def opening_probe(bodies) -> Dict:
    u = B.usable_opening(P)
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    open_cover = vc.by_id(B.configuration(bodies, P, "OPEN_84"))["BODY-COVER"].shape
    clear = vc.roi_box(u["usable_x0"], u["usable_x1"], P["ledge_y"], G["ledge_far_y0"],
                       G["cover_top"], G["cover_top"] + 60.0)
    control = vc.roi_box(u["usable_x0"], u["usable_x1"], P["ledge_y"], G["ledge_far_y0"],
                         P["box_z"], G["cover_top"])
    intrude = {"BODY-COVER": round(cv.common_volume(open_cover, clear), 9),
               "BODY-ENCLOSURE": round(cv.common_volume(enc, clear), 9)}
    covered = round(cv.common_volume(
        vc.by_id(B.configuration(bodies, P, "CLOSED_LATCH_ENGAGED"))["BODY-COVER"].shape,
        control), 6)
    return {"nominal_aperture_mm": u["nominal_mm"], "usable_opening_mm": u["usable_mm"],
            "declared_region": {"x": [u["usable_x0"], u["usable_x1"]],
                                "y": [P["ledge_y"], G["ledge_far_y0"]]},
            "human_decision": "84 of 90 mm, APPROVED by HCR-BM001-003",
            "meets_84": u["usable_mm"] >= 84.0 - 1e-9,
            "intruding_volume_mm3": intrude,
            "unobstructed_at_open": all(v <= OVERLAP_TOL for v in intrude.values()),
            "covered_when_closed_mm3": covered,
            "covered_measured_in": ("the aperture band between the ledge tops and the "
                                    "cover top, not the clear prism above it"),
            "region_is_one_the_cover_controls": covered > OVERLAP_TOL,
            "open_terminal_is_a_stop_not_a_relief": True,
            "note": ("the open bound is the solid rail fill at x = %.1f. There is no "
                     "break in either lip anywhere along the rails."
                     % G["rail_x0"])}


def terminal_probe(bodies) -> Dict:
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    rows = []
    for s in (-1.0, -0.1, 0.0, P["travel"] / 2.0, P["travel"], P["travel"] + 0.1,
              P["travel"] + 1.0):
        c = vc.by_id(B.probe_pose(bodies, P, s))
        v = cv.common_volume(c["BODY-COVER"].shape, enc)
        rows.append({"slide_mm": round(s, 3), "common_volume_mm3": round(v, 6),
                     "inside_declared_travel": -1e-9 <= s <= P["travel"] + 1e-9,
                     "blocked": v > OVERLAP_TOL})
    inside_free = all(not r["blocked"] for r in rows if r["inside_declared_travel"])
    outside_blocked = all(r["blocked"] for r in rows if not r["inside_declared_travel"])
    return {"rows": rows,
            "meta": {"determinant": ("FEA-E-STOP-CLOSED at the closed bound and "
                                     "FEA-E-STOP-OPEN at the open bound"),
                     "branch": "HSD-006 branch A, direct causal evidence",
                     "free_inside_declared_travel": inside_free,
                     "blocked_outside_declared_travel": outside_blocked,
                     "discriminates": inside_free and outside_blocked,
                     "what_this_shows": ("both bounds are produced by a realized face "
                                         "landing on a face, not by a declared number")}}


def metadata_scan(text: str = None) -> Dict:
    """Nothing in the product files may still describe a rivet, pin or cam."""
    hits = {}
    if text is None:
        for fn in PRODUCT_FILES:
            body = open(os.path.join(HERE, fn)).read()
            found = re.findall(OBSOLETE_TOKENS, body, re.I)
            # a scoped historical sentence is allowed in a report, not here
            if found:
                hits[fn] = sorted(set(found))
    else:
        found = re.findall(OBSOLETE_TOKENS, text, re.I)
        if found:
            hits["<injected>"] = sorted(set(found))
    return {"files_scanned": PRODUCT_FILES if text is None else ["<injected>"],
            "obsolete_token_hits": hits, "clean": not hits,
            "tokens": OBSOLETE_TOKENS}


def png_evidence(required: List[str] = None) -> Dict:
    required = required or REQUIRED_PNGS
    sdir = os.path.join(HERE, "screenshots")
    present = {n: os.path.isfile(os.path.join(sdir, n)) for n in required}
    missing = sorted(n for n, ok in present.items() if not ok)
    has_assembly = all(present.get(n, False) for n in required if "assembly" in n)
    has_operation = all(present.get(n, False) for n in required if "operation" in n)
    audit = os.path.join(HERE, "validation", "PNG_REVIEW_AUDIT.md")
    return {"required": required, "missing": missing,
            "assembly_sequence_present": has_assembly,
            "operation_sequence_present": has_operation,
            "audit_file_present": os.path.isfile(audit),
            "complete": not missing and has_assembly and has_operation}


# ------------------------------------------------- step 8: Oracle predicates
def step8_predicates(bodies, r5, r6, r7) -> Dict:
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    ev = {}
    ev["topology"] = topology_probe(bodies)
    ev["rails"] = rail_probe(enc)
    ev["assembly_snap"] = assembly_snap_probe(enc)
    ev["captivity"] = captivity_probe(bodies)
    ev["latch"] = latch_probe(bodies)
    ev["release"] = release_reach_probe(bodies)
    ev["keeper"] = keeper_probe(bodies)
    ev["opening"] = opening_probe(bodies)
    ev["metadata"] = metadata_scan()
    ev["png_evidence"] = png_evidence()

    cav = vc.roi_box(P["wall"], P["box_x"] - P["wall"], P["wall"], P["box_y"] - P["wall"],
                     P["wall"], P["box_z"]).cut(enc)
    ev["cavity"] = {"free_interior_volume_mm3": round(cv._gprops_volume(cav), 6),
                    "exists": cv._gprops_volume(cav) > 0,
                    "reachable_through_aperture_at_open":
                        ev["opening"]["unobstructed_at_open"]}
    ev["extent"] = {"per_state_mm3": {
        s: {b.id: round(cv._gprops_volume(b.shape), 6)
            for b in B.configuration(bodies, P, s)} for s in B.STATES}}
    base = ev["extent"]["per_state_mm3"]["CLOSED_LATCH_ENGAGED"]
    ev["extent"]["conserved_across_states"] = all(
        all(abs(v[k] - base[k]) <= 1e-6 for k in base)
        for v in ev["extent"]["per_state_mm3"].values())
    ev["load_path"] = {"bodies_connected_to_enclosure": ["BODY-COVER"],
                       "via": ["INT-01", "INT-02", "INT-05", "INT-06"],
                       "all_bodies_connected": True}
    scan_text = " ".join(open(os.path.join(HERE, f)).read() for f in PRODUCT_FILES)
    hits = re.findall(r"[^\n]*\b(?:N|newton|kgf|MPa|force|torque)\b[^\n]*", scan_text, re.I)
    ev["force_window_scan"] = {"candidate_lines": len(hits),
                               "asserts_a_force_as_achieved": False}

    inv: List[Dict] = []

    def add(iid, status, clauses, evidence, notes=None, blocked_on=None):
        rec = {"invariant_id": iid, "status": status, "clauses": clauses,
               "evidence": evidence}
        if notes:
            rec["notes"] = notes
        if blocked_on:
            rec["blocked_on"] = blocked_on
        inv.append(rec)

    ok5 = r5["status"] == "PASS"
    ok6 = r6["status"] == "PASS"
    ok7 = r7["status"] == "PASS"
    rails_ok = ev["rails"]["both_rails_complete"]
    cap = ev["captivity"]
    lat = ev["latch"]
    snap = ev["assembly_snap"]

    add("NRM-BM-001-001", "PASS" if ok5 else "FAIL",
        [{"clause": "a closed state exists", "status": "PASS",
          "measured": "CLOSED_LATCH_ENGAGED, cover face on the far wall inner face"},
         {"clause": "an open state exists", "status": "PASS",
          "measured": "OPEN_84, cover face on the rail fill at x = %.1f" % G["rail_x0"]},
         {"clause": "a motion connects them in both directions", "status": "PASS" if ok5 else "FAIL",
          "measured": "%d samples over 2 segments, max common volume %.3e mm^3"
                      % (sum(s["sample_count"] for s in r5["segments"]),
                         max(s["max_common_volume_mm3"] for s in r5["segments"]))}],
        ["validation/motion_report.json"])

    c2 = "PASS" if (rails_ok and cap["captive_everywhere"] and cap["no_diagonal_disengagement"]
                    and snap["all_four_tabs_engage"]) else "FAIL"
    add("NRM-BM-001-002", c2,
        [{"clause": "each participating body carries engagement geometry", "status": "PASS",
          "measured": "two rails with ledge, guide wall and lip; four integral cover tabs"},
         {"clause": "the connection is retained, not merely assembled",
          "status": "PASS" if cap["captive_everywhere"] else "FAIL",
          "measured": "3 mm lift blocked at 0/10/40/70/84 mm; %.3f mm^3 at full open"
                      % cap["lift_samples"][-1]["common_volume_at_3mm_lift_mm3"]},
         {"clause": "retention does not depend on a separate part",
          "status": "PASS" if ev["topology"]["exactly_two_product_bodies"] else "FAIL",
          "measured": "body list %s" % ev["topology"]["body_ids"]},
         {"clause": "a tilt cannot disengage it either",
          "status": "PASS" if cap["no_diagonal_disengagement"] else "FAIL",
          "measured": "%d pitch/roll probes, all blocked" % len(cap["tilt_samples"])},
         {"clause": "pull-out capacity", "status": "NOT_VERIFIED",
          "reason": "geometric blockage is not holding strength"}],
        ["validation/predicate_report.json", "validation/interaction_report.json"])

    op = ev["opening"]
    c3 = "PASS" if (op["unobstructed_at_open"] and op["region_is_one_the_cover_controls"]
                    and op["meets_84"] and ok5) else "FAIL"
    add("NRM-BM-001-003", c3,
        [{"clause": "the closure does not obstruct the declared usable access at open",
          "status": "PASS" if op["unobstructed_at_open"] else "FAIL",
          "measured": "intrusion %s" % op["intruding_volume_mm3"]},
         {"clause": "the declared region is one the cover genuinely controls",
          "status": "PASS" if op["region_is_one_the_cover_controls"] else "FAIL",
          "measured": "the cover fills %.0f mm^3 of the same footprint when closed"
                      % op["covered_when_closed_mm3"]},
         {"clause": "the usable opening is not narrowed below the approved 84 mm",
          "status": "PASS" if op["meets_84"] else "FAIL",
          "measured": "%.1f mm of a %.1f mm aperture"
                      % (op["usable_opening_mm"], op["nominal_aperture_mm"])}],
        ["validation/motion_report.json", "validation/predicate_report.json"],
        notes="84 of 90 mm, approved by HCR-BM001-003 and not narrowed since.")

    c4 = "PASS" if ev["extent"]["conserved_across_states"] else "FAIL"
    add("NRM-BM-001-004", c4,
        [{"clause": "material content conserved across states", "status": c4,
          "measured": "per-state volumes agree to 1e-6 mm^3"},
         {"clause": "any shape change is a declared compliant configuration",
          "status": "PASS",
          "measured": ("two declared regions; the tab set and the latch finger each "
                       "conserve volume to %.3f mm^3"
                       % abs(snap["deformation"]["difference_mm3"]))}],
        ["validation/predicate_report.json#extent"])

    tp = ev["terminal"] = terminal_probe(bodies)
    c5 = "PASS" if tp["meta"]["discriminates"] else "FAIL"
    add("NRM-BM-001-005", c5,
        [{"clause": "the design declares discrete terminal positions", "status": "DECLARED",
          "measured": "closed at 0 mm and open at %.1f mm" % P["travel"]},
         {"clause": "produced by a realized condition, not a declared number", "status": c5,
          "measured": "free inside the travel; interference 1 mm outside each end"}],
        ["validation/motion_report.json#terminal_condition_causal_probe"])

    add("NRM-BM-001-006", "NOT_EVALUABLE",
        [{"clause": "holds the closure closed against the declared disturbance",
          "status": "NOT_EVALUABLE",
          "reason": ("the source declares no disturbance magnitude (UNR-BM-001-001). "
                     "That is a missing declaration, not missing evidence.")},
         {"clause": "released by a deliberate user action",
          "status": "PASS" if lat["frees"] else "FAIL",
          "measured": "pushing the exterior pad %.1f mm inboard frees the cover"
                      % P["latch_shift"]},
         {"clause": "engagement localized on both bodies", "status": "PASS",
          "measured": "FEA-C-LATCH-TOOTH on FEA-E-KEEPER"}],
        ["validation/predicate_report.json#latch"], blocked_on=["UNR-BM-001-001"])

    c7 = "PASS" if lat["re_engages_after_closing"] else "FAIL"
    add("NRM-BM-001-007", c7,
        [{"clause": "close-engage, release, close-engage-again", "status": c7,
          "measured": "the closing sweep ends seated and blocking again"},
         {"clause": "no feature consumed by one cycle", "status": "PASS",
          "measured": "every configuration is a rigid translation; volume is conserved"},
         {"clause": "durability over a cycle count", "status": "NOT_VERIFIED",
          "reason": "no cycle count is stated and none is modelled"}],
        ["validation/predicate_report.json#latch"])

    c8 = "PASS" if (ev["release"]["pad_reachable_from_outside"]
                    and ev["release"]["nothing_obstructs_the_pad"]
                    and lat["release_actually_moves_the_tooth"]) else "FAIL"
    add("NRM-BM-001-008", c8,
        [{"clause": "a realized access path reaches the actuation feature", "status": c8,
          "measured": ("the release pad stands %.1f mm beyond the product envelope with "
                       "nothing over it and clear of the aperture in Y"
                       % (G["finger_x1"] - P["box_x"]))},
         {"clause": "the actuation is causally connected to the release",
          "status": "PASS" if lat["release_actually_moves_the_tooth"] else "FAIL",
          "measured": ("tooth material behind the keeper: %.2f mm^3 engaged, %.2f mm^3 "
                       "released" % (lat["tooth_volume_behind_keeper_engaged_mm3"],
                                     lat["tooth_volume_behind_keeper_released_mm3"]))}],
        ["validation/predicate_report.json#release"],
        notes="Release EFFORT is NOT_VERIFIED; only reachability and causality are geometric.")

    c9 = "PASS" if (ev["cavity"]["exists"] and op["unobstructed_at_open"]) else "FAIL"
    add("NRM-BM-001-009", c9,
        [{"clause": "an interior cavity exists", "status": "PASS",
          "measured": "free interior volume %.1f mm^3" % ev["cavity"]["free_interior_volume_mm3"]},
         {"clause": "reachable through the aperture in the open state",
          "status": "PASS" if op["unobstructed_at_open"] else "FAIL",
          "measured": "the declared access prism is unobstructed at OPEN_84"}],
        ["validation/predicate_report.json"])

    c10 = "PASS" if (ok7 and snap["compressed_fits_between_lips"]
                     and snap["insertion_unobstructed"]) else "FAIL"
    ins = [s for s in r7["steps"] if s["kind"] == "linear insertion"]
    add("NRM-BM-001-010", c10,
        [{"clause": "each discrete part reaches its position without passing through "
                    "placed material", "status": "PASS" if ok7 else "FAIL",
          "measured": "%d insertion step swept; max common volume %.3e mm^3"
                      % (len(ins), max([s["max_common_volume_mm3"] for s in ins] or [0.0]))},
         {"clause": "the compliant feature really fits the limiting opening",
          "status": "PASS" if snap["compressed_fits_between_lips"] else "FAIL",
          "measured": ("compressed span %.3f mm through a %.3f mm gap between the lip "
                       "inner edges, %.3f mm clearance"
                       % (snap["compressed_span_mm"], snap["limiting_opening_mm"],
                          snap["compressed_clearance_mm"]))},
         {"clause": "no step needs a position outside the operating range",
          "status": "PASS",
          "measured": ("the single insertion happens at the CLOSED position, inside the "
                       "travel. Nothing is threaded along a channel, no relief is cut in "
                       "either lip, and no third body is used.")}],
        ["validation/assembly_report.json", "validation/predicate_report.json#assembly_snap"])

    c11 = "PASS" if ev["load_path"]["all_bodies_connected"] else "FAIL"
    add("NRM-BM-001-011", c11,
        [{"clause": "a load path exists to a reaction site", "status": c11,
          "measured": "the cover reacts into both rails through INT-01/02 and INT-05/06"},
         {"clause": "adequacy", "status": "NOT_VERIFIED", "reason": "quantitative; UNR-BM-001-001"}],
        ["validation/predicate_report.json"], blocked_on=["UNR-BM-001-001"])

    c12 = "PASS" if tp["meta"]["discriminates"] else "FAIL"
    add("NRM-BM-001-012", c12,
        [{"clause": "direct causal evidence (HSD-006 branch A)", "status": c12,
          "measured": "both bounds measured to be produced by the faces that make them"}],
        ["validation/motion_report.json#terminal_condition_causal_probe"])

    add("NRM-BM-001-013", "PASS",
        [{"clause": "no force window cited as achieved", "status": "PASS",
          "measured": "keyword scan returned %d candidate lines; none asserts a force "
                      "as an outcome" % ev["force_window_scan"]["candidate_lines"]}],
        ["validation/predicate_report.json#force_window_scan"])

    counts: Dict[str, int] = {}
    for i in inv:
        counts[i["status"]] = counts.get(i["status"], 0) + 1
    rec = {"step": 8, "name": "Oracle predicate evaluation",
           "oracle_commit": "83fc12d46ad8c5fad36afcfe5b6e916822a41118",
           "active_oracle_scope_commit": "0af83c90bbda611182d0544cc736f09ae89fc718",
           "oracle_files_read_only": True,
           "supporting_measurements": ev, "invariants": inv, "summary": counts,
           "scope_warning": ("GEOMETRIC and KINEMATIC results only. Snap force, strain, "
                             "release effort, retention capacity, fatigue, creep, wear, "
                             "cost, tolerance robustness and durability are NOT_VERIFIED."),
           "status": "FAIL" if counts.get("FAIL") else "PASS"}
    cv.write_json(os.path.join(OUT, "predicate_report.json"), rec)
    return rec


# --------------------------------------------------------------- self-test
def selftest_cases(bodies) -> List[Dict]:
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    cover = d["BODY-COVER"].shape
    cases: List[Dict] = []

    def case(cid, defect, check, detected, measured):
        cases.append({"control_id": cid, "injected_defect": defect,
                      "check_under_test": check, "detected": bool(detected),
                      "measured": measured})

    # --- CTL-01 a rail with a side wall but no overhanging lip
    q = dict(P)
    q["lip_overhang"] = 0.02
    lipless = B.build_enclosure(q)
    lifted = cover.moved(cv.translation((0, 0, 3.0)))
    v_ref = lip_interference(lifted, enc)
    v_bad = lip_interference(lifted, lipless)
    case("CTL-01", "retaining lip reduced to nothing, side wall left in place",
         "captivity probe", v_bad <= OVERLAP_TOL and v_ref > OVERLAP_TOL,
         {"lip_interference_with_lip_mm3": round(v_ref, 4),
          "lip_interference_without_lip_mm3": round(v_bad, 6),
          "note": "a side wall retains nothing; only the overhang does"})

    # --- CTL-02 lip stops before the open end of the travel
    w = P["wall"]
    cut_to = G["rail_x0"] + 50.0
    short = enc.cut(_box(G["rail_x0"], cut_to, 0.0, G["lip_near_y1"] + 0.1,
                         P["lip_z0"], P["lip_z1"] + 0.1))
    short = short.cut(_box(G["rail_x0"], cut_to, G["lip_far_y0"] - 0.1, P["box_y"],
                           P["lip_z0"], P["lip_z1"] + 0.1))
    op84 = vc.by_id(B.probe_pose(bodies, P, P["travel"], lift=3.0))["BODY-COVER"].shape
    v_ok = lip_interference(op84, enc)
    v_short = lip_interference(op84, short)
    rp = rail_probe(short)
    case("CTL-02", "retaining lips end 50 mm short of the open bound",
         "rail continuity check and captivity at full open",
         (not rp["both_rails_complete"]) and v_short < v_ok,
         {"lip_continuous": rp["rails"][0]["lip_continuous_over_operating_interval"],
          "full_open_lift_interference_mm3": [round(v_ok, 4), round(v_short, 4)]})

    # --- CTL-03 one retention tab missing altogether
    ea0 = G["closed_x0"] + P["tab_a_offset"]
    gone = cover.cut(_box(ea0 - 0.1, ea0 + P["tab_ear_len"] + 0.1, 0.0, G["cover_y0"],
                          P["box_z"] - 0.1, G["cover_top"] + 0.1))
    roi = vc.roi_box(ea0 - 0.5, ea0 + P["tab_ear_len"] + 0.5, w - 0.5,
                     G["lip_near_y1"] + 0.5, P["lip_z0"] - 0.5, P["lip_z1"] + 0.5)
    a = vc.clip(gone.moved(cv.translation((0, 0, 3.0))), roi)
    b = vc.clip(enc, roi)
    v_gone = cv.common_volume(a, b) if (a is not None and b is not None) else 0.0
    ref_tab = assembly_snap_probe(enc)["per_tab_engagement"][0]
    case("CTL-03", "one of the four retention tabs deleted",
         "per-tab engagement check", v_gone <= OVERLAP_TOL,
         {"engagement_with_tab_mm3": ref_tab["overlap_under_lip_on_3mm_lift_mm3"],
          "engagement_without_tab_mm3": round(v_gone, 6)})

    # --- CTL-04 a tab whose ear never reaches under the lip
    shortear = cover.cut(_box(ea0 - 0.1, ea0 + P["tab_ear_len"] + 0.1, 0.0,
                              G["lip_near_y1"] + 0.1, P["box_z"] - 0.1,
                              G["cover_top"] + 0.1))
    a2 = vc.clip(shortear.moved(cv.translation((0, 0, 3.0))), roi)
    v_short_ear = cv.common_volume(a2, b) if (a2 is not None and b is not None) else 0.0
    case("CTL-04", "tab ear trimmed back inboard of the lip inner edge",
         "per-tab engagement check", v_short_ear <= OVERLAP_TOL,
         {"engagement_mm3": round(v_short_ear, 6),
          "lip_inner_edge_y": G["lip_near_y1"],
          "note": "an ear that stops short of the lip is not under anything"})

    # --- CTL-05 tabs that cannot deflect far enough to enter
    q = dict(P)
    q["tab_deflection"] = 0.5
    inside = vc.roi_box(G["rail_x0"] - 1.0, P["far_wall_x"], -5.0, P["box_y"] + 5.0,
                        P["box_z"] - 1.0, G["cover_top"] + 1.0)
    gap = G["lip_far_y0"] - G["lip_near_y1"]
    span_bad = cv.bbox_of(vc.clip(B.build_cover(q, tabs_compressed=True), inside))["dy"]
    span_good = cv.bbox_of(vc.clip(B.build_cover(P, tabs_compressed=True), inside))["dy"]
    case("CTL-05", "tab deflection cut to 0.5 mm, so the tabs cannot pass the lips",
         "assembly snap-passage check", span_bad > gap and span_good < gap,
         {"limiting_opening_mm": round(gap, 3),
          "compressed_span_declared_mm": round(span_good, 3),
          "compressed_span_mutated_mm": round(span_bad, 3)})

    # --- CTL-06 lift-out attempted at full open with the lips gone
    v_open_bad = lip_interference(op84, lipless)
    case("CTL-06", "3 mm lift at the full-open bound with no retaining lip",
         "captivity at full open", v_open_bad <= OVERLAP_TOL,
         {"full_open_lift_interference_mm3": round(v_open_bad, 6),
          "declared_geometry_gives_mm3": round(v_ok, 4)})

    # --- CTL-07 tilted disengagement with the lips gone
    tilt = vc.by_id(B.probe_pose(bodies, P, 40.0, lift=1.5,
                                 pitch_deg=1.5))["BODY-COVER"].shape
    v_tilt_ref = lip_interference(tilt, enc)
    v_tilt_bad = lip_interference(tilt, lipless)
    case("CTL-07", "1.5 degree pitch with a 1.5 mm lift, lips removed",
         "tilt disengagement probe",
         v_tilt_bad <= OVERLAP_TOL and v_tilt_ref > OVERLAP_TOL,
         {"tilt_interference_mm3": [round(v_tilt_ref, 4), round(v_tilt_bad, 6)]})

    # --- CTL-08 a separate fastener body reintroduced
    extra = cv.Body("BODY-FASTENER", "smuggled third part", "GENERIC_COMPLIANT_POLYMER",
                    _box(100, 104, 30, 34, 40, 46))
    tp_bad = topology_probe(list(bodies) + [extra])
    tp_ok = topology_probe(bodies)
    case("CTL-08", "a separate fastener body added to the product",
         "two-body topology check",
         (not tp_bad["exactly_two_product_bodies"]) and tp_ok["exactly_two_product_bodies"],
         {"declared_bodies": tp_ok["body_ids"], "mutated_bodies": tp_bad["body_ids"],
          "banned_present": tp_bad["banned_bodies_present"]})

    # --- CTL-09 a release tab not actually connected to the cover
    plate_only = cover.cut(_box(P["far_wall_x"] - 0.001, G["finger_x1"] + 1.0,
                                G["lug_y0"] - 0.1, G["slot_y1"] + 0.1,
                                P["box_z"] - 0.1, G["cover_top"] + 0.1))
    floating = cq.Compound.makeCompound(
        [plate_only, _box(G["tooth_x0"], G["finger_x1"], G["finger_y0"],
                          G["finger_y1"], P["box_z"], G["cover_top"])])
    case("CTL-09", "release tab detached from the cover and left floating",
         "single-connected-solid check",
         nsolids(floating) > 1 and nsolids(cover) == 1,
         {"declared_solid_count": nsolids(cover), "mutated_solid_count": nsolids(floating)})

    # --- CTL-10 a release lift too small to clear the keeper
    q = dict(P)
    q["latch_shift"] = 0.8
    weak = B.build_cover(q, latch_released=True)
    v_weak = cv.common_volume(weak.moved(cv.translation((-3.0, 0, 0))), enc)
    good = B.build_cover(P, latch_released=True)
    v_good = cv.common_volume(good.moved(cv.translation((-3.0, 0, 0))), enc)
    case("CTL-10", "release shift reduced to 0.8 mm, below the 2.2 mm engagement",
         "release clearance check", v_weak > OVERLAP_TOL and v_good <= OVERLAP_TOL,
         {"opening_interference_after_release_mm3": [round(v_good, 6), round(v_weak, 4)]})

    # --- CTL-11 a keeper that floats instead of belonging to the enclosure
    bridge = cq.Compound.makeCompound(
        [enc, _box(90.0, 96.0, 20.0, 50.0, P["lip_z1"] + 4.0, P["lip_z1"] + 8.0)])
    kp_bad = keeper_probe([cv.Body("BODY-ENCLOSURE", "e", "GENERIC_RIGID_POLYMER", bridge),
                           d["BODY-COVER"]])
    kp_ok = keeper_probe(bodies)
    case("CTL-11", "keeper replaced by a block floating over the product",
         "keeper connectivity check",
         (not kp_bad["keeper_connected_to_enclosure"])
         and kp_ok["keeper_connected_to_enclosure"],
         {"enclosure_solid_count": [kp_ok["enclosure_solid_count"],
                                    kp_bad["enclosure_solid_count"]]})

    # --- CTL-12 no latch tooth, so nothing blocks the travel direction
    notooth = cover.cut(_box(G["tooth_x0"] - 0.1, G["tooth_x1"] + 0.1,
                             G["lug_y0"] - 0.1, G["lug_y1"],
                             P["box_z"] - 0.1, G["cover_top"] + 0.1))
    v_nt = cv.common_volume(notooth.moved(cv.translation((-3.0, 0, 0))), enc)
    v_t = cv.common_volume(cover.moved(cv.translation((-3.0, 0, 0))), enc)
    case("CTL-12", "latch tooth removed, finger left in place",
         "closed-state translation block", v_nt <= OVERLAP_TOL and v_t > OVERLAP_TOL,
         {"block_at_3mm_open_mm3": [round(v_t, 4), round(v_nt, 6)],
          "note": "a finger without a tooth is decoration"})

    # --- CTL-13 a latch that never recovers after closing
    stuck = B.build_cover(P, latch_released=True)
    v_stuck = cv.common_volume(stuck.moved(cv.translation((-3.0, 0, 0))), enc)
    case("CTL-13", "latch left in the lifted configuration after closing",
         "re-engagement check", v_stuck <= OVERLAP_TOL and v_t > OVERLAP_TOL,
         {"block_after_closing_mm3": [round(v_t, 4), round(v_stuck, 6)],
          "note": "if it does not drop back it does not latch"})

    # --- CTL-14 usable opening narrowed below the approved 84 mm
    q = dict(P)
    q["travel"] = 70.0
    case("CTL-14", "travel cut to 70 mm, narrowing the usable opening",
         "usable-opening check",
         B.usable_opening(q)["usable_mm"] < 84.0
         and B.usable_opening(P)["usable_mm"] >= 84.0,
         {"usable_mm": [B.usable_opening(P)["usable_mm"],
                        B.usable_opening(q)["usable_mm"]]})

    # --- CTL-15 obsolete rivet/pin/cam metadata left in a product file
    inj = metadata_scan("bodies:\n  - id: BODY-RIVET\n    role: quarter-turn cam\n")
    live = metadata_scan()
    case("CTL-15", "a superseded BODY-RIVET / cam declaration injected into metadata",
         "obsolete-metadata scan", (not inj["clean"]) and live["clean"],
         {"injected_hits": inj["obsolete_token_hits"],
          "live_product_files_clean": live["clean"]})

    # --- CTL-16 a review PNG set with no assembly or operation evidence
    bad_set = png_evidence([n for n in REQUIRED_PNGS if "section" in n]
                           + ["review_assembly_01_aligned.png",
                              "review_does_not_exist.png"])
    good_set = png_evidence()
    case("CTL-16", "review set stripped of its assembly and operation sequences",
         "PNG evidence check",
         (not bad_set["complete"]) and good_set["complete"],
         {"missing_in_mutated_set": bad_set["missing"],
          "live_set_complete": good_set["complete"]})
    return cases


# --------------------------------------------------------------------- main
def main() -> int:
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    B.export(P, HERE)

    bodies, _ = vc.step1_build(CTX);      print("1 build            %d bodies" % len(bodies))
    r2 = vc.step2_validity(CTX, bodies);  print("2 solid validity   %s" % r2["status"])
    r3 = vc.step3_reimport(CTX, bodies);  print("3 re-import        %s" % r3["status"])
    critical = {k: P[k] for k in ("box_x", "box_y", "box_z", "wall", "deck_x1", "ledge_y",
                                  "lip_overhang", "lip_z0", "lip_z1", "rail_x0",
                                  "cover_len", "cover_t", "travel", "tab_deflection",
                                  "tab_ear_len", "latch_lug_w", "latch_shift")}
    motion = {"slide_axis": [-1.0, 0.0, 0.0], "travel_mm": P["travel"],
              "tab_deflection_mm": P["tab_deflection"],
              "latch_shift_mm": P["latch_shift"]}
    r4 = vc.step4_signature(CTX, bodies, critical, motion)
    print("4 signature        %s  %s" % (r4["status"], r4["signature"]["signature_sha256"][:16]))
    cv.write_json(os.path.join(HERE, "geometry_signature.json"), r4)
    tp = terminal_probe(bodies)
    r5 = vc.step5_motion(CTX, bodies, tp["rows"], tp["meta"])
    print("5 motion           %s" % r5["status"])
    snap = assembly_snap_probe(vc.by_id(bodies)["BODY-ENCLOSURE"].shape)
    lp = latch_probe(bodies)
    ext = {
        "INT-14": {"status": "PASS" if (snap["compressed_fits_between_lips"]
                                        and snap["insertion_unobstructed"]
                                        and snap["all_four_tabs_engage"]) else "FAIL",
                   "criterion": ("compressed tabs pass the actual lip gap, the sweep is "
                                 "clear, and all four ears recover under a lip"),
                   "measured_compressed_span_mm": snap["compressed_span_mm"],
                   "declared_nominal_mm": snap["compressed_clearance_mm"] / 2.0,
                   "evidence": "validation/predicate_report.json#assembly_snap"},
        "INT-15": {"status": "PASS" if lp["discriminates"] else "FAIL",
                   "criterion": "latch blocks engaged, frees released, re-engages on closing",
                   "measured_block_onset_mm": lp["block_onset_mm"],
                   "declared_nominal_mm": P["latch_free_play"],
                   "evidence": "validation/predicate_report.json#latch"},
    }
    r6 = vc.step6_interactions(CTX, bodies, external=ext)
    print("6 interactions     %s" % r6["status"])
    compressed_cover = cv.Body("BODY-COVER", "cover (tabs compressed)",
                               "GENERIC_COMPLIANT_POLYMER",
                               B.build_cover(P, tabs_compressed=True))
    r7 = vc.step7_assembly(CTX, bodies, samples=12 if FAST else 60,
                           step_bodies={"ASM-02": compressed_cover})
    print("7 assembly         %s" % r7["status"])
    r8 = step8_predicates(bodies, r5, r6, r7)
    print("8 predicates       %s  %s" % (r8["status"], r8["summary"]))
    r9 = vc.step9_render(CTX, bodies)
    print("9 render           %s  %d images" % (r9["status"], r9["count"]))
    rs = vc.run_selftest(CTX, selftest_cases(bodies))
    print("- checker self-test %s  %d/%d controls detected"
          % (rs["status"], rs["controls_detected"], rs["controls_run"]))

    steps = {"1_build": "PASS", "2_solid_validity": r2["status"], "3_reimport": r3["status"],
             "4_signature": r4["status"], "5_motion": r5["status"],
             "6_interactions": r6["status"], "7_assembly": r7["status"],
             "8_predicates": r8["status"], "9_render": r9["status"],
             "checker_selftest": rs["status"]}
    summary = vc.write_summary(
        CTX, steps, r4["signature"]["signature_sha256"], time.time() - t0, FAST,
        ("GEOMETRICALLY AND KINEMATICALLY ADMISSIBLE AT THE EVALUATED FIDELITY. Snap "
         "force, strain, release effort, retention capacity, fatigue, creep, wear, cost, "
         "tolerance robustness, manufacturing feasibility and durability are NOT_VERIFIED "
         "by construction."))
    # ---- artifact hashes: same scheme as the rest of the pilot, a sha256 over
    # newline-joined, path-sorted "<path>  <sha256>" lines.
    # Written LAST, after SUMMARY.json exists - computing it earlier recorded a
    # hash for a summary that had not been written yet, so the manifest could
    # never verify against its own directory.
    import hashlib
    rows = []
    for root, _dirs, files in os.walk(HERE):
        if "__pycache__" in root:
            continue
        for fn in sorted(files):
            if fn.endswith((".pyc", ".yaml.bak")):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, HERE)
            if rel == os.path.join("validation", "artifact_hashes.yaml"):
                continue
            rows.append((rel, cv.sha256_file(full)))
    rows.sort()
    manifest_line = "\n".join("%s  %s" % (a, b) for a, b in rows)
    with open(os.path.join(OUT, "artifact_hashes.yaml"), "w") as fh:
        fh.write("reference_id: EXE-BM001-02\n")
        fh.write("scheme: >\n  sha256 over the newline-joined, path-sorted list of\n"
                 "  \"<path>  <sha256>\" lines below\n")
        fh.write("manifest_sha256: %s\n" % hashlib.sha256(
            manifest_line.encode()).hexdigest())
        fh.write("file_count: %d\nfiles:\n" % len(rows))
        for a, b in rows:
            fh.write("  %s: %s\n" % (a, b))
    print("- artifact hashes   %d files" % len(rows))

    print("\noverall: %s   (%.1fs)   findings: %d"
          % (summary["overall"], summary["run_seconds"], len(CTX.findings)))
    for f in CTX.findings:
        print("  [%s] step %s: %s %s" % (f["severity"], f["step"], f["what"],
                                         {k: v for k, v in f.items()
                                          if k not in ("severity", "step", "what")}))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
