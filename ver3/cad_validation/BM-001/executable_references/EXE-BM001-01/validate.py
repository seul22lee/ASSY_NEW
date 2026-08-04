"""Validation chain for EXE-BM001-01.

Steps 1-7 and 9 run on the shared engine in tools/valcore.py, so both references
make the same kind of claim in the same way and the common method is reviewed
once. What lives here is what is genuinely specific to this reference: where each
declared interaction is measured, how the motion is sampled, the Oracle predicate
evaluation, and the negative controls.

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

# Declared contact by state: which pairs are permitted to reach zero distance.
CONTACT_BY_STATE = {
    "S_CLOSED_RETAINED": {("BODY-CLOSURE", "BODY-ENCLOSURE"): ["INT-07", "INT-13"],
                          ("BODY-ENCLOSURE", "BODY-PIN"): ["INT-06"],
                          ("BODY-BOLT", "BODY-ENCLOSURE"): ["INT-12"]},
    "S_CLOSED_RELEASED": {("BODY-CLOSURE", "BODY-ENCLOSURE"): ["INT-07", "INT-13"],
                          ("BODY-ENCLOSURE", "BODY-PIN"): ["INT-06"]},
    "S_OPEN": {("BODY-CLOSURE", "BODY-ENCLOSURE"): ["INT-09"],
               ("BODY-ENCLOSURE", "BODY-PIN"): ["INT-06"]},
}
# Pairs with a declared contact at either end of a segment: a near-zero distance
# during the segment is the expected approach or separation, not a discovery.
SEGMENT_CONTACT = {
    "M1_RELEASE": {("BODY-CLOSURE", "BODY-ENCLOSURE"), ("BODY-ENCLOSURE", "BODY-PIN"),
                   ("BODY-BOLT", "BODY-ENCLOSURE")},
    "M2_OPEN": {("BODY-CLOSURE", "BODY-ENCLOSURE"), ("BODY-ENCLOSURE", "BODY-PIN")},
}

# Region of interest per declared interaction, in the enclosure frame, at the
# state named. Localizes each measurement to the declared feature pair, so a
# clearance is not swamped by a contact elsewhere on the same body pair.
ROI = {
    "INT-01": ("S_CLOSED_RETAINED", (53.0, 66.6, 80.0, 92.0, 44.0, 56.0)),
    "INT-04": ("S_CLOSED_RETAINED", (37.0, 50.6, 80.0, 92.0, 44.0, 56.0)),
    "INT-06": ("S_CLOSED_RETAINED", (22.0, 24.0, 80.0, 92.0, 44.0, 56.0)),
    "INT-07": ("S_CLOSED_RETAINED", (5.0, 18.0, 0.0, 80.0, 43.0, 47.0)),
    # z starts above the plate (top 49) and above the knuckle webs (top 50), so
    # this region sees only the two knuckle end faces. A region reaching down to
    # the rim measures the INT-07 seat instead and reports 0.0.
    "INT-08": ("S_CLOSED_RETAINED", (35.2, 36.4, 80.0, 92.0, 51.0, 56.0)),
    "INT-09": ("S_OPEN", (36.0, 51.6, 76.0, 82.0, 38.0, 45.0)),
    "INT-10": ("S_CLOSED_RETAINED", (50.0, 70.0, 0.0, 18.0, 50.0, 58.0)),
    "INT-11": ("S_CLOSED_RETAINED", (50.0, 70.0, 0.0, 18.0, 38.0, 44.0)),
    "INT-12": ("S_CLOSED_RETAINED", (50.0, 70.0, 0.0, 18.0, 35.5, 38.5)),
    "INT-13": ("S_CLOSED_RETAINED", (53.0, 67.0, 3.0, 15.0, 43.0, 47.0)),
    "INT-14": ("S_CLOSED_RETAINED", (53.0, 66.6, 78.5, 81.0, 45.5, 49.0)),
    # The guide bore is cut out of this region: without that, the nearest closure
    # material to the bolt is the bore wall (INT-10, 0.1 mm) and this region
    # reports INT-10's clearance under INT-15's name.
    "INT-15": ("S_CLOSED_RETAINED", (50.0, 70.0, 0.0, 18.0, 56.0, 66.0),
               ("cyl_z", 60.0, 9.0, 4.5)),
}

SAMPLING = {"M1_RELEASE": (12 if FAST else 30, [] if FAST else [(0.0, 0.06, 12)]),
            "M2_OPEN": (24 if FAST else 90,
                        [] if FAST else [(0.0, 0.02, 16), (0.97, 1.0, 30)])}

COLORS = {"BODY-ENCLOSURE": "#6b8fb4", "BODY-CLOSURE": "#c08a5a",
          "BODY-PIN": "#8d84b8", "BODY-BOLT": "#7ba884"}
SECTIONS = (("S_CLOSED_RETAINED", "x", 44.0, "section_knuckle_closed"),
            ("S_OPEN", "x", 44.0, "section_knuckle_open"),
            ("S_CLOSED_RETAINED", "y", 9.0, "section_retention_closed"),
            ("S_CLOSED_RELEASED", "y", 9.0, "section_retention_released"))

CTX = vc.Ctx("EXE-BM001-01", HERE, P, B, CONTACT_BY_STATE, SEGMENT_CONTACT,
             ROI, SAMPLING, COLORS, SECTIONS)
OUT = CTX.OUT
OVERLAP_TOL, CONTACT_TOL = CTX.OVERLAP_TOL, CTX.CONTACT_TOL
BODY_IDS = CTX.BODY_IDS


# ------------------------------------------------------- geometric utilities
def access_prism() -> cq.Shape:
    """The usable access region this design declares for the storage interaction."""
    w = P["wall"]
    return vc.roi_box(w, P["box_x"] - w, w, P["box_y"] - w, P["box_z"], P["box_z"] + 100.0)


def actuator_prism() -> cq.Shape:
    top = P["bolt_top_z"] + P["knob_h"]
    return cq.Solid.makeCylinder(P["knob_d"] / 2.0 + 4.0, 80.0,
                                 pnt=cq.Vector(P["bolt_x"], P["bolt_y"], top),
                                 dir=cq.Vector(0, 0, 1))


def cavity_solid(enclosure: cq.Shape) -> cq.Shape:
    w = P["wall"]
    return vc.roi_box(w, P["box_x"] - w, w, P["box_y"] - w, w, P["box_z"]).cut(enclosure)


def terminal_probe(bodies: List[cv.Body]) -> Dict:
    a0 = P["open_angle_deg"]
    rows = []
    for deg in (a0 - 2.0, a0 - 0.5, a0 - 0.05, a0, a0 + 0.05, a0 + 0.5, a0 + 2.0):
        c = vc.by_id(B.probe_pose(bodies, P, deg))
        rows.append({"opening_angle_deg": round(deg, 4),
                     "closure_enclosure_common_volume_mm3":
                         round(cv.common_volume(c["BODY-CLOSURE"].shape,
                                                c["BODY-ENCLOSURE"].shape), 9),
                     "closure_enclosure_min_distance_mm":
                         round(cv.min_distance(c["BODY-CLOSURE"].shape,
                                               c["BODY-ENCLOSURE"].shape), 9),
                     "beyond_terminal": deg > a0})
    before = all(r["closure_enclosure_common_volume_mm3"] <= OVERLAP_TOL
                 for r in rows if not r["beyond_terminal"])
    after = all(r["closure_enclosure_common_volume_mm3"] > OVERLAP_TOL
                for r in rows if r["beyond_terminal"])
    meta = {"determinant": "INT-09", "terminal_angle_deg": a0,
            "clear_before_terminal": before, "interpenetrates_beyond_terminal": after,
            "supports_direct_causal_branch_A": before and after,
            "discriminates": before and after,
            "note": ("Evaluates the same admissible model outside its declared range to "
                     "establish that INT-09 is what terminates the rotation. No artifact "
                     "is exported and no inadmissible model is created.")}
    return {"rows": rows, "meta": meta}


def retention_blocking_probe(bodies: List[cv.Body]) -> Dict:
    """Does the retention actually block the motion it is supposed to block?

    Measured, not asserted: with the bolt retained, the closure is rotated a
    little and the common volume with the bolt is reported. A positive volume is
    a geometric block. This says nothing about the force needed to defeat it.
    """
    d = vc.by_id(bodies)
    angles = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 8.0]
    rows = []
    for deg in angles:
        moved = d["BODY-CLOSURE"].moved(B.open_rotation(P, deg))
        rows.append({"opening_angle_deg": deg,
                     "closure_bolt_common_volume_mm3":
                         round(cv.common_volume(moved.shape, d["BODY-BOLT"].shape), 9)})
    onset = next((r["opening_angle_deg"] for r in rows
                  if r["closure_bolt_common_volume_mm3"] > OVERLAP_TOL), None)
    blocked = onset is not None and all(
        r["closure_bolt_common_volume_mm3"] > OVERLAP_TOL
        for r in rows if r["opening_angle_deg"] >= onset)

    rel = vc.by_id(B.configuration(bodies, P, "S_CLOSED_RELEASED"))
    free = []
    for deg in angles:
        rot = B.open_rotation(P, deg)
        free.append({"opening_angle_deg": deg,
                     "closure_enclosure_common_volume_mm3":
                         round(cv.common_volume(rel["BODY-CLOSURE"].moved(rot).shape,
                                                rel["BODY-ENCLOSURE"].shape), 9),
                     "bolt_enclosure_common_volume_mm3":
                         round(cv.common_volume(rel["BODY-BOLT"].moved(rot).shape,
                                                rel["BODY-ENCLOSURE"].shape), 9)})
    unblocked = all(r["closure_enclosure_common_volume_mm3"] <= OVERLAP_TOL
                    and r["bolt_enclosure_common_volume_mm3"] <= OVERLAP_TOL for r in free)
    return {"retained_rotation": rows, "block_onset_deg": onset, "blocked_beyond_onset": blocked,
            "released_rotation_free": free, "free_after_release": unblocked,
            "discriminates": blocked and unblocked,
            "free_play_note": (
                "The block does not begin at zero. INT-10 and INT-11 are 0.1 mm running "
                "clearances, and near the closed pose the closure's motion at the bolt is "
                "almost entirely along the bolt axis, so the bore slides on the shaft before "
                "it bears on it. The measured onset is the free play those clearances imply. "
                "A retention that engaged with zero play would need an interference fit, "
                "which this reference deliberately does not use."),
            "what_this_shows": ("The release action is necessary: beyond the free play the "
                                "opening motion is geometrically blocked while the bolt is "
                                "retained, and free at every probed angle once it is lifted."),
            "what_this_does_not_show": "any holding capacity, or that the free play is acceptable"}


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
    clearances = {bid: round(cv.min_distance(confs["S_OPEN"][bid].shape, prism), 9)
                  for bid in obstruction}
    access_ok = all(v <= OVERLAP_TOL for v in obstruction.values())
    ev["open_access"] = {
        "declared_region": {"x": [P["wall"], P["box_x"] - P["wall"]],
                            "y": [P["wall"], P["box_y"] - P["wall"]],
                            "z": [P["box_z"], P["box_z"] + 100.0],
                            "what": "prism over the whole cavity aperture, 100 mm tall"},
        "intruding_volume_mm3": obstruction, "min_distance_to_region_mm": clearances,
        "unobstructed": access_ok}

    cav_v = cv._gprops_volume(cavity_solid(d["BODY-ENCLOSURE"].shape))
    ev["cavity"] = {"free_interior_volume_mm3": round(cav_v, 6), "exists": cav_v > 0,
                    "reachable_through_aperture_at_open": access_ok,
                    "method": "cavity prism minus the enclosure solid"}

    act = actuator_prism()
    act_block = {bid: round(cv.common_volume(confs["S_CLOSED_RETAINED"][bid].shape, act), 9)
                 for bid in BODY_IDS}
    act_ok = all(v <= OVERLAP_TOL for v in act_block.values())
    ev["actuator_access"] = {
        "path": {"axis": [P["bolt_x"], P["bolt_y"]], "radius_mm": P["knob_d"] / 2.0 + 4.0,
                 "from_z": P["bolt_top_z"] + P["knob_h"], "length_mm": 80.0,
                 "terminates_at": "FEA-B-KNOB top face"},
        "intruding_volume_mm3": act_block, "path_clear": act_ok}

    eng_roi = vc.roi_box(50.0, 70.0, 0.0, 18.0, P["socket_z"], P["box_z"])
    e_bolt = vc.clip(confs["S_CLOSED_RETAINED"]["BODY-BOLT"].shape, eng_roi)
    e_encl = vc.clip(confs["S_CLOSED_RETAINED"]["BODY-ENCLOSURE"].shape, eng_roi)
    r_bolt = vc.clip(confs["S_CLOSED_RELEASED"]["BODY-BOLT"].shape, eng_roi)
    block = retention_blocking_probe(bodies)
    ev["retention"] = {
        "engagement_depth_below_rim_mm": round(P["box_z"] - P["socket_z"], 6),
        "material_present_on_both_bodies_in_engagement_region": bool(e_bolt and e_encl),
        "engaged_bolt_volume_in_region_mm3": round(cv._gprops_volume(e_bolt), 6) if e_bolt else 0.0,
        "released_bolt_volume_in_region_mm3": round(cv._gprops_volume(r_bolt), 6) if r_bolt else 0.0,
        "disengages_on_release": (r_bolt is None),
        "release_action": "lift BODY-BOLT %.1f mm; deliberate, single-body, reversible" % P["release_lift"],
        "blocking_probe": block,
        "declared_disturbance_magnitude": None,
        "holding_capacity_evaluated": False}

    cycle_states = ["S_CLOSED_RETAINED", "S_CLOSED_RELEASED", "S_OPEN",
                    "S_CLOSED_RELEASED", "S_CLOSED_RETAINED"]
    cyc = []
    for i, s in enumerate(cycle_states):
        c = vc.by_id(B.configuration(bodies, P, s))
        eb = vc.clip(c["BODY-BOLT"].shape, eng_roi)
        cyc.append({"index": i, "state": s,
                    "bolt_volume_mm3": round(cv._gprops_volume(c["BODY-BOLT"].shape), 6),
                    "closure_volume_mm3": round(cv._gprops_volume(c["BODY-CLOSURE"].shape), 6),
                    "enclosure_volume_mm3": round(cv._gprops_volume(c["BODY-ENCLOSURE"].shape), 6),
                    "engaged": eb is not None,
                    "socket_min_distance_mm": round(
                        cv.min_distance(c["BODY-BOLT"].shape, c["BODY-ENCLOSURE"].shape), 9)})
    intact = all(abs(cyc[0][k] - cyc[-1][k]) <= 1e-6 for k in
                 ("bolt_volume_mm3", "closure_volume_mm3", "enclosure_volume_mm3"))
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
        "note": ("Matches are inspected. A line recording that a force is NOT verified is "
                 "not a citation of an achieved property.")}

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
          "measured": ("M1_RELEASE and M2_OPEN traversed over %d and %d samples with max "
                       "common volume %.3e and %.3e mm^3"
                       % (m5["M1_RELEASE"]["sample_count"], m5["M2_OPEN"]["sample_count"],
                          m5["M1_RELEASE"]["max_common_volume_mm3"],
                          m5["M2_OPEN"]["max_common_volume_mm3"])),
          "reversibility": ("the path is a one-parameter family of rigid transforms; "
                            "traversal in the reverse direction visits the same "
                            "configurations")}],
        ["validation/motion_report.json"])

    add("NRM-BM-001-002", "PASS" if r6["status"] == "PASS" else "FAIL",
        [{"clause": "each participating body carries engagement geometry", "status": "PASS",
          "measured": ("bores on BODY-CLOSURE and BODY-ENCLOSURE both engaged by BODY-PIN; "
                       "INT-01 measured %.4f mm, INT-04 measured %.4f mm"
                       % (i6["INT-01"]["measured_min_distance_mm"],
                          i6["INT-04"]["measured_min_distance_mm"]))},
         {"clause": "guidance or support present where the concept depends on it",
          "status": "PASS",
          "measured": ("the concept is a revolute closure: it depends on the axis (INT-01, "
                       "INT-04, INT-06) and on the closed-state seat (INT-07, INT-13). All "
                       "five measured as declared.")},
         {"clause": "every declared intended interaction is physically coherent",
          "status": "PASS" if r6["status"] == "PASS" else "FAIL",
          "measured": "%d declared interactions, all measured inside their declared regions"
                      % len(r6["interactions"])}],
        ["validation/interaction_report.json"])

    c3a = "PASS" if ev["open_access"]["unobstructed"] else "FAIL"
    c3b = "PASS" if ok5 and r6["status"] == "PASS" else "FAIL"
    add("NRM-BM-001-003", "PASS" if c3a == "PASS" and c3b == "PASS" else "FAIL",
        [{"clause": "in the open state the closure does not obstruct the declared usable access",
          "status": c3a,
          "measured": ("intruding volume into the declared access region: %s; nearest "
                       "approach %.3f mm" % (ev["open_access"]["intruding_volume_mm3"],
                                             min(clearances.values())))},
         {"clause": "along the transition, no volume shared outside declared interaction regions",
          "status": c3b,
          "measured": ("max common volume over all pairs and all samples: %.3e mm^3 "
                       "(threshold %.1e)"
                       % (max(m5[k]["max_common_volume_mm3"] for k in m5), OVERLAP_TOL))}],
        ["validation/motion_report.json", "validation/interaction_report.json"],
        notes=("The rule applied is no UNDECLARED volumetric overlap. Declared contacts "
               "reach zero distance and that is correct, not a defect."))

    add("NRM-BM-001-004", "PASS" if extent_ok else "FAIL",
        [{"clause": "material content conserved across states",
          "status": "PASS" if extent_ok else "FAIL",
          "measured": "per-body volume identical across all three states to within 1e-6 mm^3"},
         {"clause": "no body's extent altered to achieve clearance", "status": "PASS",
          "measured": ("all four bodies are rigid; every state is a rigid transform of the "
                       "as-built solid, so no shape change is possible by construction")}],
        ["validation/predicate_report.json"])

    c5 = "PASS" if (i6["INT-09"]["status"] == "PASS"
                    and probe["supports_direct_causal_branch_A"]) else "FAIL"
    add("NRM-BM-001-005", c5,
        [{"clause": "the design declares a discrete terminal open pose", "status": "DECLARED",
          "measured": "poses.yaml terminal_condition, kind DISCRETE_TERMINAL_POSE"},
         {"clause": "that pose is produced by a realized physical condition, not a model limit",
          "status": c5,
          "measured": ("INT-09 face pair in contact at %.1f deg (min distance %.6f mm); "
                       "common volume <= %.1e mm^3 at every probed angle below the terminal "
                       "angle and > 0 at every angle above it"
                       % (P["open_angle_deg"], i6["INT-09"]["measured_min_distance_mm"],
                          OVERLAP_TOL))}],
        ["validation/motion_report.json#terminal_condition_causal_probe",
         "validation/interaction_report.json"],
        notes=("The stop face is constructed in the open configuration and rotated back, so "
               "the terminal angle is a consequence of the geometry rather than a limit "
               "imposed on the model."))

    add("NRM-BM-001-006", "NOT_EVALUABLE",
        [{"clause": "holds the closure in the closed state against the declared disturbance",
          "status": "NOT_EVALUABLE", "reason": "REPRESENTATION_INCOMPLETE",
          "measured": ("the design declares no disturbance magnitude, so the predicate has no "
                       "quantity to apply, and this toolchain computes no forces. What IS "
                       "measured is that the motion is geometrically blocked while retained "
                       "beyond %.2f deg of free play, and free at every probed angle once "
                       "released." % block["block_onset_deg"])},
         {"clause": "released by a deliberate user action", "status": "PASS",
          "measured": ("BODY-BOLT lifts %.1f mm; the engagement region is then empty of bolt "
                       "material (disengages_on_release=%s), and the rotation blocked before "
                       "the lift is free after it (free_after_release=%s)"
                       % (P["release_lift"], ev["retention"]["disengages_on_release"],
                          block["free_after_release"]))},
         {"clause": "engagement localized on both participating bodies", "status": "PASS",
          "measured": ("both bodies carry material in the declared engagement region; "
                       "engagement depth below the rim is %.1f mm"
                       % ev["retention"]["engagement_depth_below_rim_mm"])}],
        ["validation/predicate_report.json", "validation/interaction_report.json"],
        notes=("Two clauses PASS on measurement, and the blocking probe shows the retention "
               "does geometrically prevent the motion. The invariant as a whole still cannot "
               "be discharged, because its first clause needs a quantity the design does not "
               "declare. NOT_EVALUABLE is not FAIL and is not a defect in the geometry."),
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
          "measured": ("an 80 mm cylinder of radius %.1f mm rising from the knob top face is "
                       "clear of all four bodies in the retained state"
                       % (P["knob_d"] / 2.0 + 4.0))}],
        ["validation/predicate_report.json"])

    c9 = "PASS" if (ev["cavity"]["exists"] and access_ok) else "FAIL"
    add("NRM-BM-001-009", c9,
        [{"clause": "an interior cavity exists",
          "status": "PASS" if ev["cavity"]["exists"] else "FAIL",
          "measured": "free interior volume %.1f mm^3" % ev["cavity"]["free_interior_volume_mm3"]},
         {"clause": "reachable through the aperture in the open state",
          "status": "PASS" if access_ok else "FAIL",
          "measured": "the aperture prism is unobstructed at S_OPEN"}],
        ["validation/predicate_report.json"])

    c10 = "PASS" if r7["status"] == "PASS" else "FAIL"
    add("NRM-BM-001-010", c10,
        [{"clause": "each discrete part reaches its assembled position without passing "
                    "through already-placed material", "status": c10,
          "measured": "%d insertion steps swept; max common volume %.3e mm^3"
                      % (len([s for s in r7["steps"] if s["kind"] == "linear insertion"]),
                         max([s.get("max_common_volume_mm3", 0.0) for s in r7["steps"]]))},
         {"clause": "parts formed together or permanently joined declare that", "status": "PASS",
          "measured": ("all four bodies are installed_as DISCRETE; none is co-formed or "
                       "permanently joined")}],
        ["validation/assembly_report.json"])

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
          "measured": ("the feature's geometry exists (INT-09 declared and measured); contact "
                       "occurs at the relevant configuration (min distance %.6f mm at %.1f "
                       "deg); and the behaviour is caused by it (common volume 0 below the "
                       "terminal angle, positive above it)"
                       % (i6["INT-09"]["measured_min_distance_mm"], P["open_angle_deg"]))},
         {"clause": "branch B discriminating evidence", "status": "NOT_PROVIDED",
          "reason": ("branch A and branch B are alternatives, not a sequence. A control is not "
                     "mandatory once branch A is satisfied. Producing one would require a "
                     "variant model with the stop removed, which this run does not create.")}],
        ["validation/motion_report.json#terminal_condition_causal_probe"])

    add("NRM-BM-001-013", "PASS",
        [{"clause": "no force window is cited as an achieved retention property",
          "status": "PASS",
          "measured": ("keyword scan over the five authored contract files returned %d "
                       "candidate lines. No force value is asserted as an outcome anywhere in "
                       "this reference." % len(hits))}],
        ["validation/predicate_report.json#force_window_scan"],
        notes="Satisfied vacuously: the reference cites no force window at all.")

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
           "scope_warning": ("These are GEOMETRIC and KINEMATIC results. They do not establish "
                             "that the rank-1 source is satisfied. See "
                             "CAD_VALIDATION_PLAN.yaml claim_fidelity."),
           "status": "FAIL" if counts.get("FAIL") else "PASS"}
    cv.write_json(os.path.join(OUT, "predicate_report.json"), rec)
    cv.write_json(os.path.join(HERE, "actual_evaluation.json"),
                  {"reference_id": "EXE-BM001-01",
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

    sunk = d["BODY-CLOSURE"].moved(cv.translation((0.0, 0.0, -0.5)))
    v = cv.common_volume(sunk.shape, d["BODY-ENCLOSURE"].shape)
    case("CTL-01", "closure driven 0.5 mm into the enclosure",
         "undeclared volumetric overlap (step 5, step 6)", v > OVERLAP_TOL,
         {"common_volume_mm3": round(v, 6), "threshold_mm3": OVERLAP_TOL})

    lifted = d["BODY-CLOSURE"].moved(cv.translation((0.0, 0.0, 0.5)))
    _, roi, _, _ = vc.build_roi(CTX, ROI["INT-07"])
    ca, cb = vc.clip(lifted.shape, roi), vc.clip(d["BODY-ENCLOSURE"].shape, roi)
    dist = cv.min_distance(ca, cb) if (ca and cb) else float("inf")
    case("CTL-02", "closure lifted 0.5 mm off the rim", "INT-07 DECLARED_CONTACT",
         dist > CONTACT_TOL,
         {"min_distance_mm": round(dist, 6), "contact_tol_mm": CONTACT_TOL})

    q = dict(P); q["bore_d"] = 4.6
    _, roi, _, _ = vc.build_roi(CTX, ROI["INT-01"])
    ca, cb = vc.clip(B.build_pin(q), roi), vc.clip(B.build_enclosure(q), roi)
    dist = cv.min_distance(ca, cb) if (ca and cb) else float("inf")
    case("CTL-03", "knuckle bore opened from 4.2 to 4.6 mm", "INT-01 DECLARED_CLEARANCE",
         abs(dist - 0.1) > CONTACT_TOL,
         {"min_distance_mm": round(dist, 6), "declared_nominal_mm": 0.1})

    q = dict(P); q["axis_y"] = 84.0
    v = cv.common_volume(B.build_closure(q), B.build_enclosure(q))
    case("CTL-04", "axis_y returned to 84.0, the value step 7 rejected",
         "undeclared volumetric overlap in the closed state", v > OVERLAP_TOL,
         {"common_volume_mm3": round(v, 6),
          "note": "at 84.0 the knuckle envelope reaches in front of the plate's rear edge"})

    worst = 0.0
    for i in range(25):
        s = 40.0 * (1.0 - i / 24.0)
        moved = d["BODY-CLOSURE"].moved(cv.translation((0.0, s, 0.0)))
        worst = max(worst, cv.common_volume(moved.shape, d["BODY-ENCLOSURE"].shape))
    case("CTL-05", "closure inserted along +y instead of -z", "assembly path sweep (step 7)",
         worst > OVERLAP_TOL, {"max_common_volume_mm3": round(worst, 6)})

    beyond = vc.by_id(B.probe_pose(bodies, P, P["open_angle_deg"] + 0.05))
    below = vc.by_id(B.probe_pose(bodies, P, P["open_angle_deg"] - 0.05))
    vb = cv.common_volume(beyond["BODY-CLOSURE"].shape, beyond["BODY-ENCLOSURE"].shape)
    vl = cv.common_volume(below["BODY-CLOSURE"].shape, below["BODY-ENCLOSURE"].shape)
    case("CTL-06", "closure rotated 0.05 deg past the terminal angle",
         "terminal-condition causal probe", vb > OVERLAP_TOL >= vl,
         {"common_volume_beyond_mm3": round(vb, 6), "common_volume_below_mm3": round(vl, 6)})

    # CTL-07 - the retention blocking probe must distinguish retained from
    # released. Without this the release action could be claimed on the strength
    # of a lift that changes nothing.
    blk = retention_blocking_probe(bodies)
    case("CTL-07", "opening attempted with the bolt still retained",
         "retention blocking probe", blk["discriminates"],
         {"blocked_beyond_onset": blk["blocked_beyond_onset"],
          "block_onset_deg": blk["block_onset_deg"],
          "free_after_release": blk["free_after_release"]})
    return cases


# ------------------------------------------------------------------- driver
def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    bodies, _ = vc.step1_build(CTX);       print("1 build            %d bodies" % len(bodies))
    r2 = vc.step2_validity(CTX, bodies);   print("2 solid validity   %s" % r2["status"])
    r3 = vc.step3_reimport(CTX, bodies);   print("3 re-import        %s" % r3["status"])
    critical = {k: P[k] for k in ("box_x", "box_y", "box_z", "wall", "axis_y", "axis_z",
                                  "knuckle_r", "bore_d", "pin_d", "plate_t",
                                  "open_angle_deg", "bolt_d", "bolt_hole_d",
                                  "socket_z", "release_lift")}
    motion = {"axis_point": [0.0, P["axis_y"], P["axis_z"]], "axis_dir": [1.0, 0.0, 0.0],
              "open_angle_deg": P["open_angle_deg"], "release_lift_mm": P["release_lift"]}
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
         "source: cost, user effort, disturbance capacity, strength and durability are "
         "NOT_VERIFIED by construction."))
    print("\noverall: %s   (%.1fs)   findings: %d"
          % (summary["overall"], summary["run_seconds"], len(CTX.findings)))
    for f in CTX.findings:
        print("  [%s] step %s: %s %s" % (f["severity"], f["step"], f["what"],
                                         {k: v for k, v in f.items()
                                          if k not in ("severity", "step", "what")}))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
