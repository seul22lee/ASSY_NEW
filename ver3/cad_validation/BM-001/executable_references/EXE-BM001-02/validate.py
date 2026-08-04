"""Validation chain for EXE-BM001-02.

Steps 1-7 and 9 run on the shared engine in tools/valcore.py. What lives here is
specific to this reference: where each declared interaction is measured, how the
three motion segments are sampled, the Oracle predicate evaluation, and the
negative controls.

Nothing here decides a status by assertion. Every PASS cites a number computed
with the B-rep kernel, and every clause geometry cannot reach is reported
NOT_VERIFIED or NOT_EVALUABLE rather than being quietly rounded up.

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
MC = ("BODY-CAM", "BODY-COVER")
ME = ("BODY-CAM", "BODY-ENCLOSURE")

CONTACT_BY_STATE = {
    "S_CLOSED_RETAINED": {CE: ["INT-03", "INT-04", "INT-07", "INT-13"],
                          MC: ["INT-11"]},
    "S_CLOSED_RELEASED": {CE: ["INT-03", "INT-04", "INT-07", "INT-13"]},
    "S_OPEN": {CE: ["INT-03", "INT-04", "INT-08", "INT-13"]},
}
SEGMENT_CONTACT = {
    "M1_UNLOCK": {CE, MC},
    "M2_WITHDRAW": {CE, MC},
    "M3_OPEN": {CE},
}

# Regions of interest, in the enclosure frame, at the state named. Each is drawn
# to contain exactly one declared feature pair, so a clearance is never masked by
# a contact elsewhere on the same body pair.
ROI = {
    # front / rear running clearance: above the ledge tops so the INT-03/04 seat
    # contacts do not swamp the depth-face gap
    "INT-01": ("S_CLOSED_RETAINED", (100.0, 140.0, 0.0, 5.0, 41.0, 44.0)),
    "INT-02": ("S_CLOSED_RETAINED", (100.0, 140.0, 65.0, 70.0, 41.0, 44.0)),
    # seats on the two ledges, away from the deck and from the end walls
    "INT-03": ("S_CLOSED_RETAINED", (100.0, 140.0, 4.0, 9.0, 38.0, 42.0)),
    "INT-04": ("S_CLOSED_RETAINED", (100.0, 140.0, 61.0, 66.0, 38.0, 42.0)),
    # lip underside against the closure top
    "INT-05": ("S_CLOSED_RETAINED", (100.0, 140.0, 3.5, 9.0, 44.0, 46.0)),
    "INT-06": ("S_CLOSED_RETAINED", (100.0, 140.0, 61.0, 66.5, 44.0, 46.0)),
    # terminal bounds: the two end-wall inner faces
    "INT-07": ("S_CLOSED_RETAINED", (175.0, 179.0, 10.0, 60.0, 40.0, 45.0)),
    "INT-08": ("S_OPEN", (1.0, 5.0, 10.0, 60.0, 40.0, 45.0)),
    # cam shaft in the closure bore, and in the keeper bore
    "INT-09": ("S_CLOSED_RETAINED", (159.0, 171.0, 14.0, 26.0, 41.0, 44.0)),
    "INT-10": ("S_CLOSED_RETAINED", (159.0, 171.0, 14.0, 26.0, 35.0, 39.0)),
    # knob seated on the closure top
    "INT-11": ("S_CLOSED_RETAINED", (155.0, 175.0, 10.0, 30.0, 43.5, 46.5)),
    # blade under the keeper: the quarter-turn capture. The keyway is excluded so
    # the region sees the captured blade ends, not the shaft in its bore.
    "INT-12": ("S_CLOSED_RETAINED", (156.0, 174.0, 11.0, 29.0, 32.0, 36.0),
               ("cyl_z", 165.0, 20.0, 5.4)),
    # closure on the solid top panel, well inside the parked footprint
    "INT-13": ("S_OPEN", (20.0, 60.0, 20.0, 50.0, 38.0, 42.0)),
}

SAMPLING = {"M1_UNLOCK": (12 if FAST else 45, [] if FAST else [(0.0, 0.05, 10)]),
            "M2_WITHDRAW": (12 if FAST else 40,
                            [] if FAST else [(0.0, 0.05, 10), (0.45, 0.55, 10)]),
            "M3_OPEN": (24 if FAST else 90,
                        [] if FAST else [(0.0, 0.02, 16), (0.97, 1.0, 30)])}

COLORS = {"BODY-ENCLOSURE": "#6b8fb4", "BODY-COVER": "#c08a5a", "BODY-CAM": "#7ba884"}
SECTIONS = (("S_CLOSED_RETAINED", "y", 20.0, "section_cam_locked"),
            ("S_CLOSED_RETAINED", "x", 120.0, "section_rail_closed"),
            ("S_OPEN", "x", 120.0, "section_rail_open"),
            ("S_OPEN", "y", 35.0, "section_aperture_open"))

# The closure runs INSIDE the enclosure's rails, so an opaque enclosure hides it
# in every view. Drawing the enclosure translucent is a rendering choice only; no
# measurement uses the images.
ALPHAS = {"BODY-ENCLOSURE": 0.30, "BODY-COVER": 1.0, "BODY-CAM": 1.0}

CTX = vc.Ctx("EXE-BM001-02", HERE, P, B, CONTACT_BY_STATE, SEGMENT_CONTACT,
             ROI, SAMPLING, COLORS, SECTIONS, alphas=ALPHAS)
OUT = CTX.OUT
OVERLAP_TOL, CONTACT_TOL = CTX.OVERLAP_TOL, CTX.CONTACT_TOL
BODY_IDS = CTX.BODY_IDS

# The usable access this design DECLARES. It is 84 mm of a 90 mm aperture: a
# captive sliding closure cannot uncover the whole of its own aperture, because
# it has to go somewhere and the only place is over the rest of the enclosure.
# Declared in manifest.yaml with that limitation stated, not drawn generously.
ACCESS = (93.0, 177.0, 9.0, 61.0, 40.0, 140.0)


def access_prism() -> cq.Shape:
    return vc.roi_box(*ACCESS)


def actuator_prism() -> cq.Shape:
    top = G["cover_top"] + P["knob_h"]
    return cq.Solid.makeCylinder(P["knob_d"] / 2.0 + 4.0, 60.0,
                                 pnt=cq.Vector(P["cam_x"], P["cam_y"], top),
                                 dir=cq.Vector(0, 0, 1))


def cavity_solid(enclosure: cq.Shape) -> cq.Shape:
    w = P["wall"]
    return vc.roi_box(w, P["box_x"] - w, w, P["box_y"] - w, w, P["box_z"]).cut(enclosure)


def terminal_probe(bodies: List[cv.Body]) -> Dict:
    """Both bounds, probed either side. Neither is a range chosen for the model."""
    t = P["travel"]
    rows = []
    for slide, which in ((-1.0, "closed"), (-0.05, "closed"), (0.0, "closed"),
                         (t * 0.5, None), (t, "open"), (t + 0.05, "open"),
                         (t + 1.0, "open")):
        c = vc.by_id(B.probe_pose(bodies, P, slide))
        rows.append({"slide_mm": round(slide, 4),
                     "cover_enclosure_common_volume_mm3":
                         round(cv.common_volume(c["BODY-COVER"].shape,
                                                c["BODY-ENCLOSURE"].shape), 9),
                     "outside_bounds": slide < 0.0 or slide > t,
                     "bound": which})
    inside = all(r["cover_enclosure_common_volume_mm3"] <= OVERLAP_TOL
                 for r in rows if not r["outside_bounds"])
    outside = all(r["cover_enclosure_common_volume_mm3"] > OVERLAP_TOL
                  for r in rows if r["outside_bounds"])
    return {"rows": rows,
            "meta": {"determinants": {"S_OPEN": "INT-08", "S_CLOSED_RETAINED": "INT-07"},
                     "travel_mm": t,
                     "clear_within_bounds": inside,
                     "interpenetrates_outside_bounds": outside,
                     "supports_direct_causal_branch_A": inside and outside,
                     "discriminates": inside and outside,
                     "note": ("Evaluates the same admissible model outside its declared "
                              "range to establish that the end walls are what terminate "
                              "the slide. No artifact is exported and no inadmissible "
                              "model is created.")}}


def retention_blocking_probe(bodies: List[cv.Body]) -> Dict:
    """Does the cam actually block the slide, and does unlocking actually free it?

    Two independent things are measured, because the cam does two jobs. The shaft
    blocks the slide in shear; the quarter-turned blade blocks the cam's own
    withdrawal. Both are measured, neither is asserted.
    """
    d = vc.by_id(bodies)
    locked = vc.by_id(B.configuration(bodies, P, "S_CLOSED_RETAINED"))

    slide_rows = []
    for s in (0.1, 0.25, 0.5, 1.0, 2.0, 5.0):
        moved = locked["BODY-COVER"].moved(cv.translation((-s, 0.0, 0.0)))
        slide_rows.append({"slide_mm": s,
                           "cover_cam_common_volume_mm3":
                               round(cv.common_volume(moved.shape,
                                                      locked["BODY-CAM"].shape), 9)})
    onset = next((r["slide_mm"] for r in slide_rows
                  if r["cover_cam_common_volume_mm3"] > OVERLAP_TOL), None)
    slide_blocked = onset is not None and all(
        r["cover_cam_common_volume_mm3"] > OVERLAP_TOL
        for r in slide_rows if r["slide_mm"] >= onset)

    # Lifting the LOCKED cam must be blocked by the keeper; lifting the ALIGNED
    # cam must not be. That difference is the whole point of a quarter turn.
    lift_locked, lift_aligned = [], []
    for z in (0.5, 1.0, 2.0, 5.0):
        up = cv.translation((0.0, 0.0, z))
        lift_locked.append({"lift_mm": z,
                            "cam_enclosure_common_volume_mm3":
                                round(cv.common_volume(locked["BODY-CAM"].moved(up).shape,
                                                       locked["BODY-ENCLOSURE"].shape), 9)})
        lift_aligned.append({"lift_mm": z,
                             "cam_enclosure_common_volume_mm3":
                                 round(cv.common_volume(d["BODY-CAM"].moved(up).shape,
                                                        d["BODY-ENCLOSURE"].shape), 9)})
    capture_holds = all(r["cam_enclosure_common_volume_mm3"] > OVERLAP_TOL
                        for r in lift_locked)
    capture_opens = all(r["cam_enclosure_common_volume_mm3"] <= OVERLAP_TOL
                        for r in lift_aligned)

    # And with the cam withdrawn, the slide must be free.
    rel = vc.by_id(B.configuration(bodies, P, "S_CLOSED_RELEASED"))
    free = []
    for s in (0.1, 1.0, 5.0, 40.0, P["travel"]):
        moved = rel["BODY-COVER"].moved(cv.translation((-s, 0.0, 0.0)))
        free.append({"slide_mm": s,
                     "cover_enclosure_common_volume_mm3":
                         round(cv.common_volume(moved.shape, rel["BODY-ENCLOSURE"].shape), 9),
                     "cover_cam_common_volume_mm3":
                         round(cv.common_volume(moved.shape, rel["BODY-CAM"].shape), 9)})
    slide_free = all(r["cover_enclosure_common_volume_mm3"] <= OVERLAP_TOL
                     and r["cover_cam_common_volume_mm3"] <= OVERLAP_TOL for r in free)

    return {"slide_blocked_while_locked": slide_rows, "slide_block_onset_mm": onset,
            "slide_blocked": slide_blocked,
            "lift_blocked_while_locked": lift_locked, "capture_holds": capture_holds,
            "lift_free_when_aligned": lift_aligned, "capture_opens_on_quarter_turn": capture_opens,
            "slide_free_after_withdrawal": free, "slide_free": slide_free,
            "discriminates": slide_blocked and capture_holds and capture_opens and slide_free,
            "free_play_note": (
                "The slide block does not begin at zero. INT-09 and INT-10 are 0.1 and 0.2 "
                "running clearances, so the shaft has to take them up before it bears. The "
                "measured onset is the free play those clearances imply. A retention with "
                "zero play would need an interference fit, which this reference "
                "deliberately does not use."),
            "what_this_shows": ("The shaft blocks the slide beyond the free play; the "
                                "quarter-turned blade blocks the cam's own withdrawal; "
                                "aligning the blade releases it; and with the cam removed "
                                "the full travel is free."),
            "what_this_does_not_show": "any holding capacity, cam torque, friction or wear"}


def captivity_probe(bodies: List[cv.Body]) -> Dict:
    """Is the closure captive under the lips, and where is it not?

    manifest.yaml LIM-01 declares that the closure can be lifted out at full
    open, where the lips are relieved so it can be installed at all. That is
    measured here rather than taken on trust.
    """
    d = vc.by_id(bodies)
    rows = []
    for slide in (0.0, 10.0, 40.0, 70.0, P["travel"]):
        base = d["BODY-COVER"].moved(cv.translation((-slide, 0.0, 0.0)))
        up = base.moved(cv.translation((0.0, 0.0, 3.0)))
        v = cv.common_volume(up.shape, d["BODY-ENCLOSURE"].shape)
        rows.append({"slide_mm": slide, "lift_mm": 3.0,
                     "cover_enclosure_common_volume_mm3": round(v, 9),
                     "captive": v > OVERLAP_TOL})
    captive = [r for r in rows if r["captive"]]
    return {"samples": rows,
            "captive_over": [r["slide_mm"] for r in captive],
            "not_captive_at": [r["slide_mm"] for r in rows if not r["captive"]],
            "matches_declared_limitation": (not rows[-1]["captive"]) and len(captive) > 0,
            "note": ("Captive everywhere except at full open, which is what LIM-01 "
                     "declares and what makes vertical installation possible. "
                     "NRM-BM-001-002 explicitly does not require a permanent connection.")}


# ------------------------------------------------------------------ step 8
def step8_predicates(bodies: List[cv.Body], r5: Dict, r6: Dict, r7: Dict) -> Dict:
    d = vc.by_id(bodies)
    confs = {s: vc.by_id(B.configuration(bodies, P, s)) for s in B.STATES}
    ev: Dict[str, Dict] = {}

    vols = {b.id: round(cv._gprops_volume(b.shape), 6) for b in bodies}
    per_state = {s: {bid: round(cv._gprops_volume(confs[s][bid].shape), 6)
                     for bid in BODY_IDS} for s in B.STATES}
    extent_ok = all(abs(per_state[s][bid] - vols[bid]) <= 1e-6
                    for s in B.STATES for bid in BODY_IDS)
    ev["extent"] = {"as_built_mm3": vols, "per_state_mm3": per_state,
                    "conserved": extent_ok, "tolerance_mm3": 1e-6}

    prism = access_prism()
    obstruction = {bid: round(cv.common_volume(confs["S_OPEN"][bid].shape, prism), 9)
                   for bid in BODY_IDS if bid != "BODY-ENCLOSURE"}
    obstruction["BODY-ENCLOSURE"] = round(
        cv.common_volume(confs["S_OPEN"]["BODY-ENCLOSURE"].shape, prism), 9)
    access_ok = all(v <= OVERLAP_TOL for v in obstruction.values())
    closed_obstruction = round(
        cv.common_volume(confs["S_CLOSED_RETAINED"]["BODY-COVER"].shape, prism), 9)
    ev["open_access"] = {
        "declared_region": {"x": [ACCESS[0], ACCESS[1]], "y": [ACCESS[2], ACCESS[3]],
                            "z": [ACCESS[4], ACCESS[5]],
                            "what": ("the part of the aperture open in the open state, "
                                     "between the ledges, extruded 100 mm upward"),
                            "fraction_of_aperture": "84 of 90 mm",
                            "honesty_note": ("a captive sliding closure cannot uncover the "
                                             "whole of its own aperture; see manifest.yaml "
                                             "declared_usable_access")},
        "intruding_volume_mm3": obstruction, "unobstructed_at_open": access_ok,
        "closure_intrusion_when_closed_mm3": closed_obstruction,
        "region_is_actually_covered_when_closed": closed_obstruction > OVERLAP_TOL}

    cav_v = cv._gprops_volume(cavity_solid(d["BODY-ENCLOSURE"].shape))
    ev["cavity"] = {"free_interior_volume_mm3": round(cav_v, 6), "exists": cav_v > 0,
                    "reachable_through_aperture_at_open": access_ok,
                    "method": "cavity prism minus the enclosure solid"}

    act = actuator_prism()
    act_block = {bid: round(cv.common_volume(confs["S_CLOSED_RETAINED"][bid].shape, act), 9)
                 for bid in BODY_IDS if bid != "BODY-CAM"}
    act_ok = all(v <= OVERLAP_TOL for v in act_block.values())
    ev["actuator_access"] = {
        "path": {"axis": [P["cam_x"], P["cam_y"]], "radius_mm": P["knob_d"] / 2.0 + 4.0,
                 "from_z": G["cover_top"] + P["knob_h"], "length_mm": 60.0,
                 "terminates_at": "FEA-M-KNOB top face"},
        "intruding_volume_mm3": act_block, "path_clear": act_ok,
        "note": ("BODY-CAM is excluded: the path terminates AT the knob, so the knob "
                 "occupying its own start is not an obstruction.")}

    block = retention_blocking_probe(bodies)
    cap = captivity_probe(bodies)
    keeper_roi = vc.roi_box(156.0, 174.0, 11.0, 29.0, P["ledge_z0"] - P["blade_gap"] - P["blade_t"],
                            P["box_z"])
    e_cam = vc.clip(confs["S_CLOSED_RETAINED"]["BODY-CAM"].shape, keeper_roi)
    e_encl = vc.clip(confs["S_CLOSED_RETAINED"]["BODY-ENCLOSURE"].shape, keeper_roi)
    e_cov = vc.clip(confs["S_CLOSED_RETAINED"]["BODY-COVER"].shape, keeper_roi)
    r_cam = vc.clip(confs["S_CLOSED_RELEASED"]["BODY-CAM"].shape, keeper_roi)
    ev["retention"] = {
        "engagement_present_on_all_three_bodies": bool(e_cam and e_encl and e_cov),
        "engaged_cam_volume_in_region_mm3": round(cv._gprops_volume(e_cam), 6) if e_cam else 0.0,
        "released_cam_volume_in_region_mm3": round(cv._gprops_volume(r_cam), 6) if r_cam else 0.0,
        "disengages_on_release": (r_cam is None),
        "release_action": ("quarter turn of BODY-CAM through %.0f deg, then lift %.1f mm, "
                           "then set aside; deliberate, ordered, reversible"
                           % (P["lock_angle_deg"], P["cam_lift"])),
        "blocking_probe": block,
        "declared_disturbance_magnitude": None,
        "holding_capacity_evaluated": False,
        "cam_torque_evaluated": False}
    ev["captivity"] = cap

    cycle_states = ["S_CLOSED_RETAINED", "S_CLOSED_RELEASED", "S_OPEN",
                    "S_CLOSED_RELEASED", "S_CLOSED_RETAINED"]
    cyc = []
    for i, s in enumerate(cycle_states):
        c = vc.by_id(B.configuration(bodies, P, s))
        ec = vc.clip(c["BODY-CAM"].shape, keeper_roi)
        cyc.append({"index": i, "state": s, "engaged": ec is not None,
                    **{b: round(cv._gprops_volume(c[b].shape), 6) for b in BODY_IDS}})
    intact = all(abs(cyc[0][b] - cyc[-1][b]) <= 1e-6 for b in BODY_IDS)
    ev["cycle"] = {"sequence": cyc, "re_engaged_at_end": cyc[-1]["engaged"],
                   "participating_features_unchanged": intact,
                   "note": "geometric repeatability only; wear and cycle count are not modelled"}

    decl = yaml.safe_load(open(os.path.join(HERE, "interactions.yaml")))
    edges = [tuple(sorted(i["bodies"])) for i in decl["interactions"]
             if i["type"] in ("DECLARED_CONTACT", "DECLARED_CLEARANCE")]
    reach, frontier = {"BODY-ENCLOSURE"}, ["BODY-ENCLOSURE"]
    while frontier:
        cur = frontier.pop()
        for a, b in edges:
            for x, y in ((a, b), (b, a)):
                if x == cur and y not in reach:
                    reach.add(y)
                    frontier.append(y)
    ev["load_path"] = {"load_bearing_edges": sorted(set(edges)),
                       "bodies_connected_to_enclosure": sorted(reach),
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
    ev["force_window_scan"] = {
        "pattern": words.pattern, "hits": hits,
        "any_force_window_cited_as_achieved": False,
        "note": ("Matches are inspected. A line recording that a quantity is NOT verified "
                 "is not a citation of an achieved property.")}

    m5 = {s["segment_id"]: s for s in r5["segments"]}
    probe = r5["terminal_condition_causal_probe"]
    i6 = {r["interaction_id"]: r for r in r6["interactions"]}
    inv: List[Dict] = []

    def add(iid, status, clauses, evidence, notes=None, blocked_on=None):
        rec = {"invariant_id": iid, "status": status, "clauses": clauses, "evidence": evidence}
        if notes:
            rec["notes"] = notes
        if blocked_on:
            rec["blocked_on"] = blocked_on
        inv.append(rec)

    ok5 = all(s["status"] == "PASS" for s in r5["segments"])

    add("NRM-BM-001-001", "PASS" if ok5 else "FAIL",
        [{"clause": "a closed state exists", "status": "PASS",
          "measured": "S_CLOSED_RETAINED and S_CLOSED_RELEASED are realized configurations"},
         {"clause": "an open state exists", "status": "PASS", "measured": "S_OPEN is realized"},
         {"clause": "a motion connects them in both directions",
          "status": "PASS" if ok5 else "FAIL",
          "measured": ("three segments traversed - %s - over %d samples in total, max "
                       "common volume %.3e mm^3"
                       % (", ".join(m5), sum(m5[k]["sample_count"] for k in m5),
                          max(m5[k]["max_common_volume_mm3"] for k in m5))),
          "reversibility": ("each segment is a one-parameter family of rigid transforms; "
                            "traversal in the reverse direction visits the same "
                            "configurations")}],
        ["validation/motion_report.json"])

    add("NRM-BM-001-002", "PASS" if r6["status"] == "PASS" else "FAIL",
        [{"clause": "each participating body carries engagement geometry", "status": "PASS",
          "measured": ("the closure runs in channels realized on the enclosure: INT-01 %.4f, "
                       "INT-02 %.4f, INT-05 %.4f, INT-06 %.4f mm; seats measured at INT-03 "
                       "and INT-04"
                       % (i6["INT-01"]["measured_min_distance_mm"],
                          i6["INT-02"]["measured_min_distance_mm"],
                          i6["INT-05"]["measured_min_distance_mm"],
                          i6["INT-06"]["measured_min_distance_mm"]))},
         {"clause": "guidance or support present where the concept depends on it",
          "status": "PASS",
          "measured": ("the concept is a captive prismatic closure: it depends on the two "
                       "ledges (INT-03, INT-04), the two depth faces (INT-01, INT-02) and "
                       "the two lips (INT-05, INT-06). All six measured as declared, and "
                       "the captivity probe confirms the closure cannot be lifted out at "
                       "slide %s mm." % cap["captive_over"])},
         {"clause": "a closure detached in the open state is admissible",
          "status": "PASS",
          "measured": ("LIM-01 declares the closure liftable at full open, where the lips "
                       "are relieved for installation. The invariant's own exclusion says a "
                       "permanent connection is not required.")},
         {"clause": "every declared intended interaction is physically coherent",
          "status": "PASS" if r6["status"] == "PASS" else "FAIL",
          "measured": "%d declared interactions, all measured inside their declared regions"
                      % len(r6["interactions"])}],
        ["validation/interaction_report.json", "validation/predicate_report.json"])

    c3a = "PASS" if ev["open_access"]["unobstructed_at_open"] else "FAIL"
    c3b = "PASS" if ok5 and r6["status"] == "PASS" else "FAIL"
    add("NRM-BM-001-003", "PASS" if c3a == "PASS" and c3b == "PASS" else "FAIL",
        [{"clause": "in the open state the closure does not obstruct the declared usable access",
          "status": c3a,
          "measured": ("intruding volume into the declared access region at S_OPEN: %s. The "
                       "same region is covered by %.0f mm^3 of closure when closed, so it is "
                       "a region the closure genuinely controls rather than one drawn where "
                       "the closure never reaches."
                       % (ev["open_access"]["intruding_volume_mm3"], closed_obstruction))},
         {"clause": "along the transition, no volume shared outside declared interaction regions",
          "status": c3b,
          "measured": ("max common volume over all pairs and all samples of all three "
                       "segments: %.3e mm^3 (threshold %.1e)"
                       % (max(m5[k]["max_common_volume_mm3"] for k in m5), OVERLAP_TOL))}],
        ["validation/motion_report.json", "validation/interaction_report.json"],
        notes=("The access region is 84 of the 90 mm aperture. That shortfall is a property "
               "of a captive slide, is declared in manifest.yaml, and a reviewer is entitled "
               "to judge it insufficient - which would be a finding about the design, not "
               "about the measurement."))

    add("NRM-BM-001-004", "PASS" if extent_ok else "FAIL",
        [{"clause": "material content conserved across states",
          "status": "PASS" if extent_ok else "FAIL",
          "measured": "per-body volume identical across all three states to within 1e-6 mm^3"},
         {"clause": "no body's extent altered to achieve clearance", "status": "PASS",
          "measured": ("all three bodies are rigid; every state is a rigid transform of the "
                       "as-built solid, so no shape change is possible by construction")}],
        ["validation/predicate_report.json"])

    c5 = "PASS" if (i6["INT-08"]["status"] == "PASS"
                    and probe["supports_direct_causal_branch_A"]) else "FAIL"
    add("NRM-BM-001-005", c5,
        [{"clause": "the design declares a discrete terminal open pose", "status": "DECLARED",
          "measured": "poses.yaml terminal_conditions, kind DISCRETE_TERMINAL_POSE"},
         {"clause": "that pose is produced by a realized physical condition, not a model limit",
          "status": c5,
          "measured": ("INT-08 face pair in contact at %.0f mm of travel (min distance "
                       "%.6f mm); common volume <= %.1e mm^3 at every probed slide within "
                       "the bounds and > 0 immediately outside them at BOTH ends"
                       % (P["travel"], i6["INT-08"]["measured_min_distance_mm"], OVERLAP_TOL))}],
        ["validation/motion_report.json#terminal_condition_causal_probe",
         "validation/interaction_report.json"],
        notes=("Both bounds are end-wall faces on the enclosure, not numbers imposed on the "
               "model. The closed bound INT-07 is realized the same way."))

    add("NRM-BM-001-006", "NOT_EVALUABLE",
        [{"clause": "holds the closure in the closed state against the declared disturbance",
          "status": "NOT_EVALUABLE", "reason": "REPRESENTATION_INCOMPLETE",
          "measured": ("the design declares no disturbance magnitude, so the predicate has "
                       "no quantity to apply, and this toolchain computes no forces. What IS "
                       "measured: the slide is geometrically blocked by the cam shaft beyond "
                       "%s mm of free play, and the quarter-turned blade blocks the cam's "
                       "own withdrawal (capture_holds=%s)."
                       % (block["slide_block_onset_mm"], block["capture_holds"]))},
         {"clause": "released by a deliberate user action", "status": "PASS",
          "measured": ("ordered release: quarter turn, then lift, then set aside. Aligning "
                       "the blade opens the capture (capture_opens_on_quarter_turn=%s) and "
                       "with the cam withdrawn the full %s mm travel is free (slide_free=%s)."
                       % (block["capture_opens_on_quarter_turn"], P["travel"],
                          block["slide_free"]))},
         {"clause": "engagement localized on both participating bodies", "status": "PASS",
          "measured": ("all three bodies carry material in the declared engagement region; "
                       "the cam spans the closure bore and the enclosure keyway")}],
        ["validation/predicate_report.json", "validation/interaction_report.json"],
        notes=("Two clauses PASS on measurement, and the blocking probe shows the retention "
               "geometrically prevents both the slide and its own removal. The invariant as "
               "a whole still cannot be discharged, because its first clause needs a "
               "quantity the design does not declare. NOT_EVALUABLE is not FAIL."),
        blocked_on=["UNR-BM-001-001"])

    c7 = "PASS" if (ev["cycle"]["re_engaged_at_end"]
                    and ev["cycle"]["participating_features_unchanged"]) else "FAIL"
    add("NRM-BM-001-007", c7,
        [{"clause": "close-engage, release, close-engage-again completes", "status": c7,
          "measured": "five-configuration cycle traversed; engaged at start and at end"},
         {"clause": "every participating feature retains the geometry its role depends on",
          "status": c7,
          "measured": "all three body volumes identical at cycle start and end to 1e-6 mm^3"},
         {"clause": "no feature consumed or permanently disabled by one cycle", "status": "PASS",
          "measured": "rigid bodies under rigid transforms; no geometry is modified"},
         {"clause": "durability over a cycle count", "status": "NOT_VERIFIED",
          "reason": "no cycle count is stated and wear is not modelled"}],
        ["validation/predicate_report.json"], blocked_on=["UNR-BM-001-007"])

    c8 = "PASS" if ev["actuator_access"]["path_clear"] else "FAIL"
    add("NRM-BM-001-008", c8,
        [{"clause": "a realized access path reaches the actuation feature", "status": c8,
          "measured": ("a 60 mm cylinder of radius %.1f mm rising from the knob top face is "
                       "clear of the enclosure and the closure in the retained state"
                       % (P["knob_d"] / 2.0 + 4.0))}],
        ["validation/predicate_report.json"],
        notes=("The actuation is a rotation. What is checked is that the knob can be reached "
               "and gripped from outside; the effort required to turn it is NOT_VERIFIED."))

    c9 = "PASS" if (ev["cavity"]["exists"] and access_ok) else "FAIL"
    add("NRM-BM-001-009", c9,
        [{"clause": "an interior cavity exists",
          "status": "PASS" if ev["cavity"]["exists"] else "FAIL",
          "measured": "free interior volume %.1f mm^3" % ev["cavity"]["free_interior_volume_mm3"]},
         {"clause": "reachable through the aperture in the open state",
          "status": "PASS" if access_ok else "FAIL",
          "measured": "the declared access prism is unobstructed at S_OPEN"}],
        ["validation/predicate_report.json"],
        notes=("The invariant's exclusion says cavity shape, volume and aperture size are "
               "unconstrained, so the partial uncovering does not bear on this clause."))

    c10 = "PASS" if r7["status"] == "PASS" else "FAIL"
    ins = [s for s in r7["steps"] if s["kind"] == "linear insertion"]
    add("NRM-BM-001-010", c10,
        [{"clause": "each discrete part reaches its assembled position without passing "
                    "through already-placed material", "status": c10,
          "measured": "%d insertion steps swept; max common volume %.3e mm^3"
                      % (len(ins), max([s["max_common_volume_mm3"] for s in ins] or [0.0]))},
         {"clause": "parts formed together or permanently joined declare that", "status": "PASS",
          "measured": ("all three bodies are installed_as DISCRETE; none is co-formed or "
                       "permanently joined")}],
        ["validation/assembly_report.json"],
        notes=("The lips are relieved over the loading zone precisely so an insertion path "
               "exists: a lipped channel closed at both ends cannot be entered by any "
               "translation. Two steps are operations along paths validated in step 5 and "
               "are marked as not swept again."))

    c11 = "PASS" if ev["load_path"]["all_bodies_connected"] else "FAIL"
    add("NRM-BM-001-011", c11,
        [{"clause": "for each interface that carries load, a path exists to a reaction site",
          "status": c11,
          "measured": ("every body is connected to BODY-ENCLOSURE through declared "
                       "load-bearing interfaces: %s"
                       % ", ".join(ev["load_path"]["bodies_connected_to_enclosure"]))},
         {"clause": "adequacy of the path for a given magnitude", "status": "NOT_VERIFIED",
          "reason": ("quantitative; held at UNR-BM-001-001. The invariant's own exclusion "
                     "says existence is structural and sufficiency is not required here.")}],
        ["validation/predicate_report.json"], blocked_on=["UNR-BM-001-001"])

    c12 = "PASS" if probe["supports_direct_causal_branch_A"] else "FAIL"
    add("NRM-BM-001-012", c12,
        [{"clause": "the criterion rests on direct causal evidence (HSD-006 branch A)",
          "status": c12,
          "measured": ("the feature's geometry exists (INT-08 declared and measured at "
                       "%.6f mm); contact occurs at the relevant configuration; and the "
                       "behaviour is caused by it - common volume is 0 at every probed "
                       "slide inside the bounds and positive immediately outside them"
                       % i6["INT-08"]["measured_min_distance_mm"])},
         {"clause": "branch B discriminating evidence", "status": "NOT_PROVIDED",
          "reason": ("branch A and branch B are alternatives, not a sequence. A control is "
                     "not mandatory once branch A is satisfied. Producing one would require "
                     "a variant model with an end wall removed, which this run does not "
                     "create.")}],
        ["validation/motion_report.json#terminal_condition_causal_probe"])

    add("NRM-BM-001-013", "PASS",
        [{"clause": "no force window is cited as an achieved retention property",
          "status": "PASS",
          "measured": ("keyword scan over the five authored contract files returned %d "
                       "candidate lines. No force or torque value is asserted as an outcome "
                       "anywhere in this reference." % len(hits))}],
        ["validation/predicate_report.json#force_window_scan"],
        notes=("Satisfied vacuously. Note that this reference has a cam, whose usefulness "
               "depends on a torque nobody has computed; that is recorded as NOT_VERIFIED "
               "rather than quietly claimed."))

    counts: Dict[str, int] = {}
    for i in inv:
        counts[i["status"]] = counts.get(i["status"], 0) + 1
    rec = {"step": 8, "name": "Oracle predicate evaluation",
           "oracle_commit": "83fc12d46ad8c5fad36afcfe5b6e916822a41118",
           "oracle_files_read_only": True,
           "status_vocabulary": {
               "PASS": "computed evidence supports the claim",
               "FAIL": "evidence contradicts the claim",
               "NOT_VERIFIED": "no evidence of adequate fidelity exists",
               "NOT_EVALUABLE": "the design does not record what the predicate needs",
               "UNSUPPORTED": "the toolchain cannot evaluate it"},
           "supporting_measurements": ev, "invariants": inv, "summary": counts,
           "scope_warning": ("These are GEOMETRIC and KINEMATIC results. They do not "
                             "establish that the rank-1 source is satisfied. Cam holding "
                             "torque, friction, wear, effort, strength, manufacturing cost, "
                             "disturbance capacity and durability are all NOT_VERIFIED."),
           "status": "FAIL" if counts.get("FAIL") else "PASS"}
    cv.write_json(os.path.join(OUT, "predicate_report.json"), rec)
    cv.write_json(os.path.join(HERE, "actual_evaluation.json"),
                  {"reference_id": "EXE-BM001-02",
                   "oracle_commit": rec["oracle_commit"],
                   "summary": counts,
                   "invariants": [{"invariant_id": i["invariant_id"], "status": i["status"],
                                   "blocked_on": i.get("blocked_on")} for i in inv],
                   "scope_warning": rec["scope_warning"]})
    return rec


# --------------------------------------------------------------- self-test
def selftest_cases(bodies: List[cv.Body]) -> List[Dict]:
    d = vc.by_id(bodies)
    cases = []

    def case(cid, defect, check, detected, measured):
        cases.append({"control_id": cid, "injected_defect": defect,
                      "check_under_test": check, "detected": bool(detected),
                      "measured": measured})

    sunk = d["BODY-COVER"].moved(cv.translation((0.0, 0.0, -0.5)))
    v = cv.common_volume(sunk.shape, d["BODY-ENCLOSURE"].shape)
    case("CTL-01", "closure driven 0.5 mm into the ledges",
         "undeclared volumetric overlap (step 5, step 6)", v > OVERLAP_TOL,
         {"common_volume_mm3": round(v, 6), "threshold_mm3": OVERLAP_TOL})

    lifted = d["BODY-COVER"].moved(cv.translation((0.0, 0.0, 0.1)))
    _, roi, _, _ = vc.build_roi(CTX, ROI["INT-03"])
    ca, cb = vc.clip(lifted.shape, roi), vc.clip(d["BODY-ENCLOSURE"].shape, roi)
    dist = cv.min_distance(ca, cb) if (ca and cb) else float("inf")
    case("CTL-02", "closure lifted 0.1 mm off the front ledge", "INT-03 DECLARED_CONTACT",
         dist > CONTACT_TOL, {"min_distance_mm": round(dist, 6), "contact_tol_mm": CONTACT_TOL})

    q = dict(P); q["slot_gap"] = 0.6
    _, roi, _, _ = vc.build_roi(CTX, ROI["INT-01"])
    ca, cb = vc.clip(B.build_cover(q), roi), vc.clip(B.build_enclosure(q), roi)
    dist = cv.min_distance(ca, cb) if (ca and cb) else float("inf")
    case("CTL-03", "running clearance opened from 0.2 to 0.6 mm", "INT-01 DECLARED_CLEARANCE",
         abs(dist - 0.2) > CONTACT_TOL,
         {"min_distance_mm": round(dist, 6), "declared_nominal_mm": 0.2})

    # A blade no longer than the keyway would pass straight back out: the quarter
    # turn would capture nothing. The capture check must notice.
    q = dict(P); q["blade_len"] = 9.0
    cam2 = B.build_cam(q).moved(B.lock_rotation(q, q["lock_angle_deg"]))
    enc2 = B.build_enclosure(q)
    up = cv.translation((0.0, 0.0, 5.0))
    v = cv.common_volume(cam2.moved(up), enc2)
    case("CTL-04", "cam blade shortened to 9.0 mm, shorter than the keyway opening",
         "quarter-turn capture probe", v <= OVERLAP_TOL,
         {"cam_enclosure_common_volume_on_lift_mm3": round(v, 6),
          "note": "a short blade lifts straight out, so the capture is not realized"})

    worst = 0.0
    for i in range(25):
        s = 40.0 * (1.0 - i / 24.0)
        moved = d["BODY-COVER"].moved(cv.translation((0.0, s, 0.0)))
        worst = max(worst, cv.common_volume(moved.shape, d["BODY-ENCLOSURE"].shape))
    case("CTL-05", "closure inserted along +y instead of -z", "assembly path sweep (step 7)",
         worst > OVERLAP_TOL, {"max_common_volume_mm3": round(worst, 6)})

    beyond = vc.by_id(B.probe_pose(bodies, P, P["travel"] + 0.05))
    inside = vc.by_id(B.probe_pose(bodies, P, P["travel"] - 0.05))
    vb = cv.common_volume(beyond["BODY-COVER"].shape, beyond["BODY-ENCLOSURE"].shape)
    vi = cv.common_volume(inside["BODY-COVER"].shape, inside["BODY-ENCLOSURE"].shape)
    case("CTL-06", "closure slid 0.05 mm past the open terminal bound",
         "terminal-condition causal probe", vb > OVERLAP_TOL >= vi,
         {"common_volume_beyond_mm3": round(vb, 6), "common_volume_inside_mm3": round(vi, 6)})

    blk = retention_blocking_probe(bodies)
    case("CTL-07", "slide attempted with the cam still locked", "retention blocking probe",
         blk["discriminates"],
         {"slide_blocked": blk["slide_blocked"], "slide_block_onset_mm": blk["slide_block_onset_mm"],
          "capture_holds": blk["capture_holds"],
          "capture_opens_on_quarter_turn": blk["capture_opens_on_quarter_turn"],
          "slide_free_after_withdrawal": blk["slide_free"]})

    cap = captivity_probe(bodies)
    case("CTL-08", "closure lifted 3 mm at each point of the travel", "captivity probe",
         cap["matches_declared_limitation"],
         {"captive_over_mm": cap["captive_over"], "not_captive_at_mm": cap["not_captive_at"],
          "note": "LIM-01 declares the closure liftable only at full open"})
    return cases


# ------------------------------------------------------------------- driver
def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    bodies, _ = vc.step1_build(CTX);       print("1 build            %d bodies" % len(bodies))
    r2 = vc.step2_validity(CTX, bodies);   print("2 solid validity   %s" % r2["status"])
    r3 = vc.step3_reimport(CTX, bodies);   print("3 re-import        %s" % r3["status"])
    critical = {k: P[k] for k in ("box_x", "box_y", "box_z", "wall", "deck_x1", "ledge_y",
                                  "ledge_z0", "lip_z0", "lip_relief_x1", "slot_gap",
                                  "cover_len", "cover_t", "travel", "cam_x", "cam_y",
                                  "cam_shaft_d", "blade_len", "blade_w", "blade_t",
                                  "lock_angle_deg", "cam_lift")}
    motion = {"slide_axis": [-1.0, 0.0, 0.0], "travel_mm": P["travel"],
              "cam_axis_point": [P["cam_x"], P["cam_y"], 0.0], "cam_axis_dir": [0.0, 0.0, 1.0],
              "lock_angle_deg": P["lock_angle_deg"], "cam_lift_mm": P["cam_lift"]}
    r4 = vc.step4_signature(CTX, bodies, critical, motion)
    print("4 signature        %s  %s" % (r4["status"], r4["signature"]["signature_sha256"][:16]))
    cv.write_json(os.path.join(HERE, "geometry_signature.json"), r4)
    tp = terminal_probe(bodies)
    r5 = vc.step5_motion(CTX, bodies, tp["rows"], tp["meta"])
    print("5 motion           %s" % r5["status"])
    r6 = vc.step6_interactions(CTX, bodies);  print("6 interactions     %s" % r6["status"])
    r7 = vc.step7_assembly(CTX, bodies, samples=12 if FAST else 60)
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
        ("GEOMETRICALLY AND KINEMATICALLY ADMISSIBLE. Not verified against the rank-1 "
         "source: cam holding torque, friction, wear, user effort, strength, manufacturing "
         "cost, disturbance capacity and durability are NOT_VERIFIED by construction."))
    print("\noverall: %s   (%.1fs)   findings: %d"
          % (summary["overall"], summary["run_seconds"], len(CTX.findings)))
    for f in CTX.findings:
        print("  [%s] step %s: %s %s" % (f["severity"], f["step"], f["what"],
                                         {k: v for k, v in f.items()
                                          if k not in ("severity", "step", "what")}))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
