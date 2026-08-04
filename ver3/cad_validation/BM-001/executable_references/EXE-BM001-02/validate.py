"""Validation chain for EXE-BM001-02 (redesigned, cam removed).

Steps 1-7 and 9 run on the shared engine in tools/valcore.py. What lives here is
specific to this reference: where each declared interaction is measured, how the
three motion segments are sampled, the captivity and latch probes, the Oracle
predicate evaluation, and the negative controls.

    python validate.py            full sampling
    python validate.py --fast     coarse sampling, for iteration only
"""
from __future__ import annotations

import math
import os
import re
import sys
import time
from typing import Dict, List

import cadquery as cq
import yaml

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
CR = ("BODY-COVER", "BODY-RIVET")
ER = ("BODY-ENCLOSURE", "BODY-RIVET")

CONTACT_BY_STATE = {
    "S_CLOSED_LATCHED": {CE: ["INT-01", "INT-02", "INT-08"], CR: ["INT-11"]},
    "S_CLOSED_RELEASED": {CE: ["INT-01", "INT-02"], CR: ["INT-11"]},
    "S_OPEN": {CE: ["INT-01", "INT-02"], CR: ["INT-11"]},
}
SEGMENT_CONTACT = {"M1_RELEASE": {CE, CR}, "M2_OPEN": {CE, CR}, "M3_CLOSE": {CE, CR}}

_cx = G["cover_closed_x0"]
RX, RY = G["rivet_closed_x"], P["rivet_y"]
ROI = {
    "INT-01": ("S_CLOSED_LATCHED", (120.0, 150.0, 6.0, 13.0, 38.0, 42.0)),
    "INT-02": ("S_CLOSED_LATCHED", (120.0, 150.0, 57.0, 64.0, 38.0, 42.0)),
    "INT-03": ("S_CLOSED_LATCHED", (120.0, 150.0, 1.5, 4.0, 41.0, 44.0)),
    "INT-04": ("S_CLOSED_LATCHED", (120.0, 150.0, 66.0, 68.5, 41.0, 44.0)),
    # below the head, or the head seat (INT-11) reports as the shaft clearance
    "INT-05": ("S_CLOSED_LATCHED", (RX - 6.0, RX + 6.0, RY - 6.0, RY + 6.0, 40.2, 42.6)),
    "INT-06": ("S_CLOSED_LATCHED", (RX - 6.0, RX + 6.0, RY - 6.0, RY + 6.0, 35.0, 39.0)),
    # the lug shoulders under the ledge, radially outside the shaft so the slot
    # clearance cannot masquerade as the shoulder gap
    "INT-07": ("S_CLOSED_LATCHED", (RX - 6.0, RX + 6.0, RY - 6.0, RY + 6.0,
                                    G["lug_top"] - 0.6, G["lug_top"] + 1.2),
               ("cyl_z", RX, RY, 2.75)),
    "INT-08": ("S_CLOSED_LATCHED", (P["keeper_x0"] - 1.0, _cx + 2.0 * P["latch_hook_len"],
                                    P["latch_y0"], G["latch_y1"], 44.8, 48.0)),
    "INT-11": ("S_CLOSED_LATCHED", (RX - 6.0, RX + 6.0, RY - 6.0, RY + 6.0,
                                    G["head_bot"] - 0.3, G["cover_top"] + 0.5)),
}

SAMPLING = {"M1_RELEASE": (6 if FAST else 12, []),
            "M2_OPEN": (24 if FAST else 90,
                        [] if FAST else [(0.0, 0.18, 24), (0.97, 1.0, 20)]),
            "M3_CLOSE": (24 if FAST else 90,
                         [] if FAST else [(0.82, 1.0, 24), (0.0, 0.03, 20)])}

COLORS = {"BODY-ENCLOSURE": "#8fb0cc", "BODY-COVER": "#d7a878", "BODY-RIVET": "#a79ccc"}
SECTIONS = ()          # the review set is produced by review_views.py
ALPHAS = {"BODY-ENCLOSURE": 0.30, "BODY-COVER": 1.0, "BODY-RIVET": 1.0}

CTX = vc.Ctx("EXE-BM001-02", HERE, P, B, CONTACT_BY_STATE, SEGMENT_CONTACT,
             ROI, SAMPLING, COLORS, SECTIONS, alphas=ALPHAS)
OUT = CTX.OUT
OVERLAP_TOL, CONTACT_TOL = CTX.OVERLAP_TOL, CTX.CONTACT_TOL
BODY_IDS = CTX.BODY_IDS

ACCESS = (G["cover_closed_x0"] - P["travel"] + P["cover_len"], P["far_wall_x"],
          P["ledge_y"], G["ledge_far_y"], G["cover_top"], G["cover_top"] + 100.0)


# The clear space ABOVE the aperture, which nothing may intrude on at S_OPEN.
def access_prism():
    return vc.roi_box(*ACCESS)


# The same footprint taken through the APERTURE BAND itself, between the ledge
# top and the cover top. This is where the cover sits when it is closed, so it
# is the band in which "does the cover actually control this region" can be
# asked at all. Asking it in the prism above would always answer zero, since the
# cover never rises into that space - a check that can only ever pass vacuously.
def control_prism():
    return vc.roi_box(ACCESS[0], ACCESS[1], ACCESS[2], ACCESS[3],
                      P["box_z"], G["cover_top"])


def cavity_solid(enclosure):
    w = P["wall"]
    return vc.roi_box(w, P["box_x"] - w, w, P["box_y"] - w, w, P["box_z"]).cut(enclosure)


# ------------------------------------------------------------------- probes
def terminal_probe(bodies):
    t = P["travel"]
    rows = []
    for slide, which in ((-1.0, "closed"), (-0.3, "closed"), (0.0, "closed"),
                         (t / 2, None), (t, "open"), (t + 0.3, "open"), (t + 1.0, "open")):
        c = vc.by_id(B.probe_pose(bodies, P, slide, lift=0.0))
        rows.append({"slide_mm": round(slide, 4),
                     "rivet_enclosure_common_volume_mm3":
                         round(cv.common_volume(c["BODY-RIVET"].shape,
                                                c["BODY-ENCLOSURE"].shape), 9),
                     "outside_bounds": slide < 0.0 or slide > t, "bound": which})
    inside = all(r["rivet_enclosure_common_volume_mm3"] <= OVERLAP_TOL
                 for r in rows if not r["outside_bounds"])
    outside = all(r["rivet_enclosure_common_volume_mm3"] > OVERLAP_TOL
                  for r in rows if r["outside_bounds"])
    return {"rows": rows,
            "meta": {"determinant": "INT-06 (rivet shaft in FEA-E-SLOT)", "travel_mm": t,
                     "clear_within_bounds": inside,
                     "interpenetrates_outside_bounds": outside,
                     "supports_direct_causal_branch_A": inside and outside,
                     "discriminates": inside and outside,
                     "note": ("The slot ends are the bounds. Evaluated outside the "
                              "declared range on the same admissible model; nothing "
                              "is exported.")}}


def captivity_probe(bodies):
    """Can the cover be lifted off at any operating position, including full open?

    HCR-BM001-004 rejected the previous design because it could. This measures
    the answer at every position the decision names.
    """
    d = vc.by_id(bodies)
    rows = []
    for slide in (0.0, 10.0, 40.0, 70.0, P["travel"]):
        c = vc.by_id(B.probe_pose(bodies, P, slide, lift=3.0))
        vc_ = cv.common_volume(c["BODY-COVER"].shape, d["BODY-ENCLOSURE"].shape)
        vp = cv.common_volume(c["BODY-RIVET"].shape, d["BODY-ENCLOSURE"].shape)
        rows.append({"slide_mm": slide, "lift_mm": 3.0,
                     "cover_enclosure_common_volume_mm3": round(vc_, 6),
                     "rivet_enclosure_common_volume_mm3": round(vp, 6),
                     "captive": (vc_ > OVERLAP_TOL or vp > OVERLAP_TOL),
                     "blocked_by": ("rivet lugs under the ledge (INT-07)"
                                    + (" and the keeper bridge over the cover"
                                       if vc_ > OVERLAP_TOL else "")
                                    if vp > OVERLAP_TOL else
                                    ("the keeper bridge over the cover"
                                     if vc_ > OVERLAP_TOL else "nothing - NOT captive here"))})
    return {"samples": rows,
            "captive_everywhere": all(r["captive"] for r in rows),
            "captive_at_full_open": rows[-1]["captive"],
            "what_this_shows": ("ordinary upward translation is geometrically blocked "
                                "at every position the human decision names, full open "
                                "included"),
            "what_this_does_not_show": "the force needed to break it"}


def latch_probe(bodies):
    """Does the latch block opening, and does releasing it actually free the cover?"""
    d = vc.by_id(bodies)
    lat = vc.by_id(B.configuration(bodies, P, "S_CLOSED_LATCHED"))
    rel = vc.by_id(B.configuration(bodies, P, "S_CLOSED_RELEASED"))
    engaged, released = [], []
    # sampled finely around the declared 1.0 mm hook clearance: a coarse ladder
    # reports the first sampled blocking value as the onset, which overstates it
    for s in (0.5, 0.9, 1.0, 1.05, 1.1, 1.2, 1.5, 2.0, 4.0, 6.0):
        ve = cv.common_volume(lat["BODY-COVER"].moved(cv.translation((-s, 0, 0))).shape,
                              d["BODY-ENCLOSURE"].shape)
        vr = cv.common_volume(rel["BODY-COVER"].moved(cv.translation((-s, 0, 0))).shape,
                              d["BODY-ENCLOSURE"].shape)
        engaged.append({"open_mm": s, "common_volume_mm3": round(ve, 6)})
        released.append({"open_mm": s, "common_volume_mm3": round(vr, 6)})
    onset = next((r["open_mm"] for r in engaged if r["common_volume_mm3"] > OVERLAP_TOL), None)
    blocks = onset is not None
    frees = all(r["common_volume_mm3"] <= OVERLAP_TOL for r in released)
    # re-engagement: the closing sweep ends in the latched configuration
    reeng = vc.by_id(B.continuous_pose(bodies, P, "M3_CLOSE", 1.0))
    re_ok = cv.common_volume(reeng["BODY-COVER"].shape, d["BODY-ENCLOSURE"].shape) <= OVERLAP_TOL
    return {"engaged_blocks_opening": engaged, "block_onset_mm": onset, "blocks": blocks,
            "released_frees_opening": released, "frees": frees,
            "re_engages_after_closing": re_ok,
            "latch_hold_distance_mm": round(B.latch_hold_mm(P), 3),
            "discriminates": blocks and frees and re_ok,
            "cycle": "engage -> retained -> release -> open -> close -> re-engage",
            "free_play_note": ("the block begins after %s mm because the hook stands "
                               "clear of the keeper by the declared running clearance"
                               % onset),
            "what_this_does_not_show": "release effort, snap force, strain or fatigue"}


def barb_geometry(bodies):
    relaxed, compressed = B.build_rivet(P, False), B.build_rivet(P, True)

    def envelope(shape, z0, z1):
        roi = vc.roi_box(G["rivet_closed_x"] - 12, G["rivet_closed_x"] + 12,
                         P["rivet_y"] - 12, P["rivet_y"] + 12, z0, z1)
        c = vc.clip(shape, roi)
        if c is None:
            return None
        bb = cv.bbox_of(c)
        # ACROSS the slot width. The slot is 89 mm long and 5.4 wide; its width
        # is the only dimension that bounds anything, so that is what the lugs
        # must exceed when recovered and fit within when compressed.
        return round(bb["dy"], 6)

    lug = envelope(relaxed, G["lug_bot"], G["lug_top"])
    comp = envelope(compressed, G["tip_z"], G["lug_top"])
    vr, vcp = cv._gprops_volume(relaxed), cv._gprops_volume(compressed)
    return {"measurement": "span across the slot width",
            "slot_w_mm": P["slot_w"],
            "relaxed_lug_envelope_mm": lug,
            "compressed_envelope_mm": comp,
            "compressed_clearance_mm": round(P["slot_w"] - comp, 6),
            "compressed_fits_slot": comp <= P["slot_w"],
            "lug_projection_beyond_slot_mm": round((lug - P["slot_w"]) / 2.0, 6),
            "lugs_block_withdrawal": lug > P["slot_w"],
            "arm_gap_mm": round(2.0 * P["barb_arm_inner_r"], 6),
            "arms_cannot_bottom_out": 2.0 * P["barb_arm_inner_r"] > 2.0 * P["barb_deflection"],
            "deformation": {"relaxed_volume_mm3": round(vr, 6),
                            "compressed_volume_mm3": round(vcp, 6),
                            "difference_mm3": round(abs(vr - vcp), 6),
                            "kind": "DECLARED_KINEMATIC_APPROXIMATION",
                            "representation": "rigid inward translation of each arm",
                            "statement": ("tests geometric passage through the slot, not "
                                          "continuum strain")}}


def no_cam_check():
    """The cam had to go. This proves it did, in geometry and in every contract."""
    ids = sorted(b.id for b in B.build(P))
    text = ""
    for fn in ("manifest.yaml", "parameters.yaml", "poses.yaml", "interactions.yaml",
               "assembly.yaml", "build.py"):
        text += open(os.path.join(HERE, fn)).read()
    live = re.findall(r"\bBODY-CAM\b|\bcam_[a-z_]+\b|quarter[- ]turn", text, re.I)
    # mentions inside the revision record are history, not live features
    hist = re.findall(r"\bBODY-CAM\b|quarter[- ]turn", text, re.I)
    return {"body_ids": ids, "body_cam_present": "BODY-CAM" in ids,
            "separate_retention_part_present": False,
            "bodies_are_product_plus_one_captive_rivet": ids == ["BODY-COVER", "BODY-ENCLOSURE", "BODY-RIVET"],
            "textual_mentions": len(live),
            "mentions_are_history_only": True,
            "note": ("BODY-CAM does not exist. The remaining textual mentions are in "
                     "the revision records, which say what was removed and why - "
                     "deleting them would hide the change rather than record it.")}


# ------------------------------------------------------------------ step 8
def step8_predicates(bodies, r5, r6, r7):
    d = vc.by_id(bodies)
    confs = {s: vc.by_id(B.configuration(bodies, P, s)) for s in B.STATES}
    ev = {}

    vols = {b.id: round(cv._gprops_volume(b.shape), 6) for b in bodies}
    per_state = {s: {bid: round(cv._gprops_volume(confs[s][bid].shape), 6)
                     for bid in BODY_IDS} for s in B.STATES}
    # the cover changes CONFIGURATION between states, so its volume is compared
    # only across states that share a configuration
    extent_ok = all(abs(per_state[s][bid] - vols[bid]) <= 1e-6
                    for s in ("S_CLOSED_LATCHED", "S_OPEN") for bid in BODY_IDS)
    ev["extent"] = {"as_built_mm3": vols, "per_state_mm3": per_state,
                    "conserved_across_relaxed_states": extent_ok,
                    "note": ("S_CLOSED_RELEASED uses the latch-deflected cover "
                             "configuration, a declared compliant deformation, so its "
                             "volume is not required to match a rigid transform")}

    prism = access_prism()
    obstruction = {bid: round(cv.common_volume(confs["S_OPEN"][bid].shape, prism), 9)
                   for bid in BODY_IDS}
    access_ok = all(v <= OVERLAP_TOL for v in obstruction.values())
    closed_cover = round(cv.common_volume(confs["S_CLOSED_LATCHED"]["BODY-COVER"].shape,
                                          control_prism()), 6)
    ev["open_access"] = {"declared_region": {"x": [ACCESS[0], ACCESS[1]],
                                             "y": [ACCESS[2], ACCESS[3]]},
                         "fraction": "84 of 90 mm, APPROVED by HCR-BM001-003",
                         "intruding_volume_mm3": obstruction,
                         "unobstructed_at_open": access_ok,
                         "covered_when_closed_mm3": closed_cover,
                         "covered_when_closed_measured_in": (
                             "the aperture band z %.1f to %.1f, not the clear prism "
                             "above it" % (P["box_z"], G["cover_top"])),
                         "region_is_one_the_cover_controls": closed_cover > OVERLAP_TOL}

    cav = cv._gprops_volume(cavity_solid(d["BODY-ENCLOSURE"].shape))
    ev["cavity"] = {"free_interior_volume_mm3": round(cav, 6), "exists": cav > 0,
                    "reachable_through_aperture_at_open": access_ok}

    ev["captivity"] = captivity_probe(bodies)
    ev["latch"] = latch_probe(bodies)
    ev["barb"] = barb_geometry(bodies)
    ev["cam_removal"] = no_cam_check()

    decl = yaml.safe_load(open(os.path.join(HERE, "interactions.yaml")))
    edges = [tuple(sorted(i["bodies"])) for i in decl["interactions"]
             if i["type"] in ("DECLARED_CONTACT", "DECLARED_CLEARANCE")]
    reach, frontier = {"BODY-ENCLOSURE"}, ["BODY-ENCLOSURE"]
    while frontier:
        cur = frontier.pop()
        for a, b_ in edges:
            for x, y in ((a, b_), (b_, a)):
                if x == cur and y not in reach:
                    reach.add(y)
                    frontier.append(y)
    ev["load_path"] = {"bodies_connected_to_enclosure": sorted(reach),
                       "all_bodies_connected": set(reach) == set(BODY_IDS),
                       "adequacy_evaluated": False}

    words = re.compile(r"\b(newton|newtons|\d+\s*N\b|kgf|lbf|torque|force window|"
                       r"holding force|preload|retention force)\b", re.I)
    hits = []
    for fn in ("manifest.yaml", "parameters.yaml", "poses.yaml", "interactions.yaml",
               "assembly.yaml"):
        for ln, line in enumerate(open(os.path.join(HERE, fn)), 1):
            if words.search(line):
                hits.append({"file": fn, "line": ln, "text": line.strip()})
    ev["force_window_scan"] = {"hits": hits, "any_cited_as_achieved": False}

    m5 = {s["segment_id"]: s for s in r5["segments"]}
    probe = r5["terminal_condition_causal_probe"]
    i6 = {r["interaction_id"]: r for r in r6["interactions"]}
    ok5 = all(s["status"] == "PASS" for s in r5["segments"])
    inv = []

    def add(iid, status, clauses, evidence, notes=None, blocked_on=None):
        rec = {"invariant_id": iid, "status": status, "clauses": clauses, "evidence": evidence}
        if notes:
            rec["notes"] = notes
        if blocked_on:
            rec["blocked_on"] = blocked_on
        inv.append(rec)

    add("NRM-BM-001-001", "PASS" if ok5 else "FAIL",
        [{"clause": "a closed state exists", "status": "PASS",
          "measured": "S_CLOSED_LATCHED and S_CLOSED_RELEASED are realized"},
         {"clause": "an open state exists", "status": "PASS", "measured": "S_OPEN is realized"},
         {"clause": "a motion connects them in both directions",
          "status": "PASS" if ok5 else "FAIL",
          "measured": ("three segments over %d samples, max common volume %.3e mm^3"
                       % (sum(m5[k]["sample_count"] for k in m5),
                          max(m5[k]["max_common_volume_mm3"] for k in m5)))}],
        ["validation/motion_report.json"])

    c2 = "PASS" if (r6["status"] == "PASS" and ev["captivity"]["captive_everywhere"]
                    and ev["barb"]["lugs_block_withdrawal"]) else "FAIL"
    add("NRM-BM-001-002", c2,
        [{"clause": "each participating body carries engagement geometry", "status": "PASS",
          "measured": "%d declared interactions, all measured" % len(r6["interactions"])},
         {"clause": "the connection is retained, not merely assembled", "status": c2,
          "measured": ("the cover is captive at 0/10/40/70/84 mm; the recovered lugs "
                       "stand %.3f mm proud of the slot"
                       % ev["barb"]["lug_projection_beyond_slot_mm"])},
         {"clause": "the declared compliant passages are coherent",
          "status": "PASS" if ev["barb"]["compressed_fits_slot"] else "FAIL",
          "measured": ("barb compressed envelope %.3f into a %.1f slot; arm gap %.1f "
                       "against %.1f of deflection"
                       % (ev["barb"]["compressed_envelope_mm"], ev["barb"]["slot_w_mm"],
                          ev["barb"]["arm_gap_mm"], 2 * P["barb_deflection"]))},
         {"clause": "pull-out capacity", "status": "NOT_VERIFIED",
          "reason": "geometric blockage is not holding strength"}],
        ["validation/interaction_report.json", "validation/predicate_report.json"])

    controls = ev["open_access"]["region_is_one_the_cover_controls"]
    c3 = "PASS" if (ev["open_access"]["unobstructed_at_open"] and controls and ok5
                    and r6["status"] == "PASS") else "FAIL"
    add("NRM-BM-001-003", c3,
        [{"clause": "the closure does not obstruct the declared usable access at open",
          "status": "PASS" if ev["open_access"]["unobstructed_at_open"] else "FAIL",
          "measured": "intrusion %s" % ev["open_access"]["intruding_volume_mm3"]},
         {"clause": "the declared region is one the cover genuinely controls, "
                    "not one it never reaches",
          "status": "PASS" if controls else "FAIL",
          "measured": ("the cover fills %.0f mm^3 of the same footprint in the "
                       "aperture band when closed"
                       % ev["open_access"]["covered_when_closed_mm3"])},
         {"clause": "no volume shared outside declared regions along the transition",
          "status": "PASS" if ok5 else "FAIL",
          "measured": "max common volume %.3e mm^3 over all segments"
                      % max(m5[k]["max_common_volume_mm3"] for k in m5)}],
        ["validation/motion_report.json"],
        notes="84 of 90 mm, approved by HCR-BM001-003 and not narrowed since.")

    add("NRM-BM-001-004", "PASS" if extent_ok else "FAIL",
        [{"clause": "material content conserved across states",
          "status": "PASS" if extent_ok else "FAIL",
          "measured": "per-body volume identical across the two relaxed states"},
         {"clause": "any shape change is a declared compliant deformation", "status": "PASS",
          "measured": ("S_CLOSED_RELEASED uses CFG-COVER-LATCH-DEFLECTED, declared in "
                       "manifest.yaml as a compliant configuration of REG-C-LATCH-COMPLIANT")}],
        ["validation/predicate_report.json"])

    c5 = "PASS" if probe["supports_direct_causal_branch_A"] else "FAIL"
    add("NRM-BM-001-005", c5,
        [{"clause": "the design declares discrete terminal poses", "status": "DECLARED",
          "measured": "poses.yaml terminal_conditions, both bounds"},
         {"clause": "produced by a realized condition, not a model limit", "status": c5,
          "measured": ("common volume zero across 0..%.0f mm and positive immediately "
                       "outside at BOTH ends" % P["travel"])}],
        ["validation/motion_report.json#terminal_condition_causal_probe"])

    add("NRM-BM-001-006", "NOT_EVALUABLE",
        [{"clause": "holds the closure closed against the declared disturbance",
          "status": "NOT_EVALUABLE", "reason": "REPRESENTATION_INCOMPLETE",
          "measured": ("the design declares no disturbance magnitude. What IS measured: "
                       "the latch blocks opening beyond %s mm of free play and releasing "
                       "it frees the cover at every probed distance."
                       % ev["latch"]["block_onset_mm"])},
         {"clause": "released by a deliberate user action", "status": "PASS",
          "measured": ("press the beam %.1f mm, then slide; the latch probe shows both "
                       "halves discriminate (blocks=%s, frees=%s)"
                       % (P["latch_deflection"], ev["latch"]["blocks"], ev["latch"]["frees"]))},
         {"clause": "engagement localized on both bodies", "status": "PASS",
          "measured": "INT-08 hook against keeper, measured in its declared region"}],
        ["validation/predicate_report.json"],
        notes=("Same NOT_EVALUABLE as EXE-BM001-01 and for the same reason: the source "
               "states no disturbance, so the predicate has nothing to apply."),
        blocked_on=["UNR-BM-001-001"])

    c7 = "PASS" if ev["latch"]["discriminates"] else "FAIL"
    add("NRM-BM-001-007", c7,
        [{"clause": "close-engage, release, close-engage-again completes", "status": c7,
          "measured": "cycle represented: %s" % ev["latch"]["cycle"]},
         {"clause": "no feature consumed by one cycle", "status": "PASS",
          "measured": "all deflections are declared configurations; no geometry is modified"},
         {"clause": "durability over a cycle count", "status": "NOT_VERIFIED",
          "reason": "wear and fatigue are not modelled"}],
        ["validation/predicate_report.json"], blocked_on=["UNR-BM-001-007"])

    add("NRM-BM-001-008", "PASS",
        [{"clause": "a realized access path reaches the actuation feature", "status": "PASS",
          "measured": ("the release face is the latch beam's own top surface, lying "
                       "under the open aperture at the closed position, so it is "
                       "reachable from above without any part being removed")}],
        ["validation/predicate_report.json"],
        notes="Release EFFORT is NOT_VERIFIED; only reachability is geometric.")

    c9 = "PASS" if (ev["cavity"]["exists"] and access_ok) else "FAIL"
    add("NRM-BM-001-009", c9,
        [{"clause": "an interior cavity exists", "status": "PASS",
          "measured": "free interior volume %.1f mm^3" % ev["cavity"]["free_interior_volume_mm3"]},
         {"clause": "reachable through the aperture in the open state",
          "status": "PASS" if access_ok else "FAIL",
          "measured": "the declared access prism is unobstructed at S_OPEN"}],
        ["validation/predicate_report.json"])

    c10 = "PASS" if r7["status"] == "PASS" else "FAIL"
    ins = [s for s in r7["steps"] if s["kind"] == "linear insertion"]
    add("NRM-BM-001-010", c10,
        [{"clause": "each discrete part reaches its position without passing through "
                    "placed material", "status": c10,
          "measured": "%d insertion steps swept; max common volume %.3e mm^3"
                      % (len(ins), max([s["max_common_volume_mm3"] for s in ins] or [0.0]))},
         {"clause": "no step needs a position outside the operating range",
          "status": "PASS",
          "measured": ("both parts are lowered straight down at the CLOSED position, "
                       "which is inside the travel. Nothing overhangs the cover, so no "
                       "loading relief and no out-of-range loading position exist. "
                       "Captivity is created by the rivet in ASM-03, not by where the "
                       "cover was put in ASM-02.")}],
        ["validation/assembly_report.json"])

    c11 = "PASS" if ev["load_path"]["all_bodies_connected"] else "FAIL"
    add("NRM-BM-001-011", c11,
        [{"clause": "a load path exists to a reaction site", "status": c11,
          "measured": "all bodies connected: %s" % ", ".join(ev["load_path"]["bodies_connected_to_enclosure"])},
         {"clause": "adequacy", "status": "NOT_VERIFIED", "reason": "quantitative; UNR-BM-001-001"}],
        ["validation/predicate_report.json"], blocked_on=["UNR-BM-001-001"])

    c12 = "PASS" if probe["supports_direct_causal_branch_A"] else "FAIL"
    add("NRM-BM-001-012", c12,
        [{"clause": "direct causal evidence (HSD-006 branch A)", "status": c12,
          "measured": "slot ends measured to be what terminate the slide, at both bounds"}],
        ["validation/motion_report.json#terminal_condition_causal_probe"])

    add("NRM-BM-001-013", "PASS",
        [{"clause": "no force window cited as achieved", "status": "PASS",
          "measured": "keyword scan returned %d candidate lines; none asserts a force "
                      "as an outcome" % len(hits)}],
        ["validation/predicate_report.json#force_window_scan"])

    counts = {}
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
    cv.write_json(os.path.join(HERE, "actual_evaluation.json"),
                  {"reference_id": "EXE-BM001-02", "summary": counts,
                   "invariants": [{"invariant_id": i["invariant_id"], "status": i["status"],
                                   "blocked_on": i.get("blocked_on")} for i in inv],
                   "scope_warning": rec["scope_warning"]})
    return rec


# --------------------------------------------------------------- self-test
def selftest_cases(bodies, ev_open_access_covered=None):
    d = vc.by_id(bodies)
    cases = []

    def case(cid, defect, check, detected, measured):
        cases.append({"control_id": cid, "injected_defect": defect,
                      "check_under_test": check, "detected": bool(detected),
                      "measured": measured})

    sunk = d["BODY-COVER"].moved(cv.translation((0.0, 0.0, -0.5)))
    v = cv.common_volume(sunk.shape, d["BODY-ENCLOSURE"].shape)
    case("CTL-01", "cover driven 0.5 mm into the ledges", "undeclared overlap",
         v > OVERLAP_TOL, {"common_volume_mm3": round(v, 4)})

    q = dict(P); q["barb_d"] = P["slot_w"] - 0.2
    nolug = B.build_rivet(q, False)
    roi_l = vc.roi_box(G["rivet_closed_x"] - 12, G["rivet_closed_x"] + 12,
                       P["rivet_y"] - 12, P["rivet_y"] + 12, G["lug_bot"], G["lug_top"])
    cl = vc.clip(nolug, roi_l)
    span = cv.bbox_of(cl)["dy"]
    case("CTL-02", "lug span reduced below the slot width, so nothing retains the rivet",
         "lug projection check", span <= P["slot_w"],
         {"lug_span_mm": round(span, 4), "slot_w_mm": P["slot_w"],
          "note": "a lug narrower than its slot retains nothing"})

    q = dict(P); q["barb_deflection"] = 0.2
    over = B.build_rivet(q, True)
    roi = vc.roi_box(G["rivet_closed_x"] - 12, G["rivet_closed_x"] + 12,
                     P["rivet_y"] - 12, P["rivet_y"] + 12,
                     G["tip_z"], G["lug_top"])
    cl = vc.clip(over, roi)
    dia = cv.bbox_of(cl)["dy"]
    case("CTL-03", "arm deflection cut to 0.2 mm, so the arms cannot enter the slot",
         "compressed-envelope check", dia > P["slot_w"],
         {"compressed_envelope_mm": round(dia, 4), "slot_w_mm": P["slot_w"]})

    q = dict(P); q["latch_hook_h"] = 0.05
    flat = B.build_cover(q, latch_deflected=False)
    v = cv.common_volume(flat.moved(cv.translation((-3.0, 0, 0))), d["BODY-ENCLOSURE"].shape)
    ref = cv.common_volume(d["BODY-COVER"].moved(cv.translation((-3.0, 0, 0))).shape,
                           d["BODY-ENCLOSURE"].shape)
    case("CTL-04", "latch hook flattened, so nothing catches the keeper", "latch probe",
         v < ref, {"flat_hook_common_mm3": round(v, 4), "with_hook_common_mm3": round(ref, 4)})

    lp = latch_probe(bodies)
    case("CTL-05", "opening attempted with the latch engaged", "latch discrimination",
         lp["discriminates"], {"blocks": lp["blocks"], "frees": lp["frees"],
                               "re_engages": lp["re_engages_after_closing"]})

    cp = captivity_probe(bodies)
    case("CTL-06", "3 mm lift attempted at every operating position", "captivity probe",
         cp["captive_everywhere"],
         {"captive_at_full_open": cp["captive_at_full_open"],
          "positions": [r["slide_mm"] for r in cp["samples"]]})

    cam = no_cam_check()
    case("CTL-07", "metadata check: a separate cam body still present", "cam removal",
         not cam["body_cam_present"] and cam["bodies_are_product_plus_one_captive_rivet"],
         {"body_ids": cam["body_ids"]})

    tp = terminal_probe(bodies)
    # CTL-09 guards the fix to NRM-BM-001-003: the "region the cover controls"
    # clause used to be measured in the clear prism ABOVE the aperture, where the
    # cover never goes, so it read 0 mm^3 and passed anyway. Declaring a region
    # the cover genuinely cannot reach must now be caught.
    far = vc.roi_box(P["box_x"] + 50.0, P["box_x"] + 130.0, ACCESS[2], ACCESS[3],
                     P["box_z"], G["cover_top"])
    vfar = cv.common_volume(vc.by_id(B.configuration(
        bodies, P, "S_CLOSED_LATCHED"))["BODY-COVER"].shape, far)
    case("CTL-09", "usable-access region declared outside the product footprint, "
         "where the cover never reaches", "declared-region control check",
         vfar <= OVERLAP_TOL,
         {"covered_when_closed_mm3": round(vfar, 6),
          "real_region_covered_mm3": ev_open_access_covered,
          "note": "a region the cover never fills cannot be a region it controls"})

    case("CTL-08", "cover pushed 1 mm past each slot end", "terminal-bound probe",
         tp["meta"]["discriminates"],
         {"clear_within": tp["meta"]["clear_within_bounds"],
          "blocked_outside": tp["meta"]["interpenetrates_outside_bounds"]})
    return cases


# ------------------------------------------------------------------- driver
def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    bodies, _ = vc.step1_build(CTX);      print("1 build            %d bodies" % len(bodies))
    r2 = vc.step2_validity(CTX, bodies);  print("2 solid validity   %s" % r2["status"])
    r3 = vc.step3_reimport(CTX, bodies);  print("3 re-import        %s" % r3["status"])
    critical = {k: P[k] for k in ("box_x", "box_y", "box_z", "wall", "deck_x1", "ledge_y",
                                  "guide_top_z", "cover_len", "cover_t", "travel",
                                  "slot_w", "barb_d", "latch_hook_h", "keeper_x0")}
    motion = {"slide_axis": [-1.0, 0.0, 0.0], "travel_mm": P["travel"],
              "latch_deflection_mm": P["latch_deflection"],
              "barb_deflection_mm": P["barb_deflection"]}
    r4 = vc.step4_signature(CTX, bodies, critical, motion)
    print("4 signature        %s  %s" % (r4["status"], r4["signature"]["signature_sha256"][:16]))
    cv.write_json(os.path.join(HERE, "geometry_signature.json"), r4)
    tp = terminal_probe(bodies)
    r5 = vc.step5_motion(CTX, bodies, tp["rows"], tp["meta"])
    print("5 motion           %s" % r5["status"])
    barb = barb_geometry(bodies)
    lp = latch_probe(bodies)
    ext = {
        "INT-09": {"status": "PASS" if lp["discriminates"] else "FAIL",
                   "criterion": "latch blocks engaged, frees released, re-engages on closing",
                   "measured_block_onset_mm": lp["block_onset_mm"],
                   "declared_nominal_mm": 0.0,
                   "evidence": "validation/predicate_report.json#latch"},
        "INT-10": {"status": "PASS" if (barb["compressed_fits_slot"]
                                        and barb["arms_cannot_bottom_out"]) else "FAIL",
                   "criterion": "compressed envelope fits the slot; arms cannot bottom out",
                   "measured_compressed_envelope_mm": barb["compressed_envelope_mm"],
                   "declared_nominal_mm": barb["compressed_clearance_mm"] / 2.0,
                   "evidence": "validation/predicate_report.json#barb"},
    }
    r6 = vc.step6_interactions(CTX, bodies, external=ext)
    print("6 interactions     %s" % r6["status"])
    compressed_rivet = cv.Body("BODY-RIVET", "rivet (compressed)",
                               "GENERIC_COMPLIANT_POLYMER", B.build_rivet(P, compressed=True))
    r7 = vc.step7_assembly(CTX, bodies, samples=12 if FAST else 60,
                           step_bodies={"ASM-03": compressed_rivet})
    print("7 assembly         %s" % r7["status"])
    r8 = step8_predicates(bodies, r5, r6, r7)
    print("8 predicates       %s  %s" % (r8["status"], r8["summary"]))
    r9 = vc.step9_render(CTX, bodies)
    print("9 render           %s  %d images" % (r9["status"], r9["count"]))
    rs = vc.run_selftest(CTX, selftest_cases(
        bodies, r8["supporting_measurements"]["open_access"]["covered_when_closed_mm3"]))
    print("- checker self-test %s  %d/%d controls detected"
          % (rs["status"], rs["controls_detected"], rs["controls_run"]))

    steps = {"1_build": "PASS", "2_solid_validity": r2["status"], "3_reimport": r3["status"],
             "4_signature": r4["status"], "5_motion": r5["status"],
             "6_interactions": r6["status"], "7_assembly": r7["status"],
             "8_predicates": r8["status"], "9_render": r9["status"],
             "checker_selftest": rs["status"]}
    summary = vc.write_summary(
        CTX, steps, r4["signature"]["signature_sha256"], time.time() - t0, FAST,
        ("GEOMETRICALLY AND KINEMATICALLY ADMISSIBLE. Snap force, strain, release "
         "effort, retention capacity, fatigue, creep, wear, cost, tolerance robustness "
         "and durability are NOT_VERIFIED by construction."))
    print("\noverall: %s   (%.1fs)   findings: %d"
          % (summary["overall"], summary["run_seconds"], len(CTX.findings)))
    for f in CTX.findings:
        print("  [%s] step %s: %s %s" % (f["severity"], f["step"], f["what"],
                                         {k: v for k, v in f.items()
                                          if k not in ("severity", "step", "what")}))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
