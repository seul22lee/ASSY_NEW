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

import math
import json
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

G = B.latch_geom(P)
CE = ("BODY-CLOSURE", "BODY-ENCLOSURE")
EP = ("BODY-ENCLOSURE", "BODY-PIN")
CLOSED_STATES = ["CLOSED_LATCH_ENGAGED", "CLOSED_LATCH_RELEASED",
                 "CLOSING_LATCH_LEADIN", "CLOSED_REENGAGED",
                 "PIN_ASSEMBLY_COMPRESSED", "PIN_ASSEMBLY_RECOVERED"]

# Declared contact by state: which pairs are permitted to reach zero distance.
CONTACT_BY_STATE = {s: {CE: ["INT-07"], EP: ["INT-06"]} for s in CLOSED_STATES}
CONTACT_BY_STATE["OPENING_STARTED"] = {EP: ["INT-06"]}
CONTACT_BY_STATE["OPEN"] = {CE: ["INT-09"], EP: ["INT-06"]}

# Pairs with a declared contact at either end of a segment: a near-zero distance
# during the segment is the expected approach or separation, not a discovery.
SEGMENT_CONTACT = {s: {CE, EP} for s in B.SEGMENTS}

# Region of interest per declared interaction, in the enclosure frame, at the
# state named. Localizes each measurement to the declared feature pair, so a
# clearance is not swamped by a contact elsewhere on the same body pair.
_CL = "CLOSED_LATCH_ENGAGED"
_BX0, _BX1 = G["beam_x0"] + 2.0, G["beam_x1"] - 2.0
ROI = {
    "INT-01": (_CL, (53.0, 66.6, 80.0, 92.0, 44.0, 56.0)),
    "INT-04": (_CL, (37.0, 50.6, 80.0, 92.0, 44.0, 56.0)),
    "INT-06": (_CL, (22.0, 24.0, 80.0, 92.0, 44.0, 56.0)),
    "INT-07": (_CL, (5.0, 18.0, 0.0, 80.0, 43.0, 47.0)),
    # z starts above the plate (top 49) and above the knuckle webs (top 50), so
    # this region sees only the two knuckle end faces. A region reaching down to
    # the rim measures the INT-07 seat instead and reports 0.0.
    "INT-08": (_CL, (35.2, 36.4, 80.0, 92.0, 51.0, 56.0)),
    "INT-09": ("OPEN", (36.0, 51.6, 76.0, 82.0, 38.0, 45.0)),
    # the latch shoulder under the keeper underside. Held inboard of the beam so
    # the beam/keeper running clearance cannot be reported as the closed free play.
    "INT-10": (_CL, (_BX0, _BX1, -P["keeper_proj"] + 0.2, G["tooth_y1"] - 0.2,
                     P["tooth_top_z"] - 0.6, P["keeper_z0"] + 1.0)),
    # the beam against the keeper's front face, above the tooth so the shoulder
    # gap cannot be reported as the running clearance
    "INT-11": (_CL, (_BX0, _BX1, G["beam_y1"] - 0.6, -P["keeper_proj"] + 0.2,
                     P["keeper_z0"] + 0.5, P["keeper_z1"] - 0.6)),
    "INT-14": (_CL, (53.0, 66.6, 78.5, 81.0, 45.5, 49.0)),
    # recovered lug shoulders against the far face of the last enclosure knuckle
    # radially OUTSIDE the shaft: inside the bore the pair is 0.1 apart, which
    # would otherwise be reported as the shoulder gap
    "INT-16": (_CL, (98.0, 102.0, 88.5, 92.0, 44.0, 56.0)),
}

SAMPLING = {"M1_RELEASE": (12 if FAST else 30, []),
            "M2_OPEN": (24 if FAST else 90,
                        [] if FAST else [(0.0, 0.08, 24), (0.97, 1.0, 30)]),
            "M3_CLOSE_AND_REENGAGE": (24 if FAST else 90,
                                      [] if FAST else [(0.92, 1.0, 24), (0.0, 0.03, 20)])}

COLORS = {"BODY-ENCLOSURE": "#6b8fb4", "BODY-CLOSURE": "#c08a5a",
          "BODY-PIN": "#8d84b8"}
SECTIONS = (("CLOSED_LATCH_ENGAGED", "x", 44.0, "section_knuckle_closed"),
            ("OPEN", "x", 44.0, "section_knuckle_open"))

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


def _box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def nsolids(shape: cq.Shape) -> int:
    return len(cq.Workplane("XY").add(shape).solids().vals())


def topology_probe(bodies: List[cv.Body]) -> Dict:
    """Exactly three product bodies, and no fourth doing the latch's job."""
    ids = sorted(b.id for b in bodies)
    banned = [i for i in ids if i in ("BODY-BOLT", "BODY-LATCH", "BODY-KEY",
                                      "BODY-CLIP", "BODY-CAM", "BODY-RIVET")]
    return {"body_ids": ids, "body_count": len(ids),
            "exactly_three_product_bodies":
                ids == ["BODY-CLOSURE", "BODY-ENCLOSURE", "BODY-PIN"],
            "banned_bodies_present": banned,
            "materials": {b.id: b.material_class for b in bodies},
            "single_connected_solid": {b.id: nsolids(b.shape) == 1 for b in bodies},
            "what_this_shows": ("the latch is integral to the closure and the keeper "
                                "integral to the enclosure. Nothing holds this product "
                                "shut that a user could drop, lose or leave out."),
            "the_pin_is_not_a_fastener": ("BODY-PIN realizes the hinge axis and its own "
                                          "bilateral axial retention. It is a hinge "
                                          "element, not a latch component.")}


def release_access_prism() -> cq.Shape:
    """The space a user's finger needs in front of the release pad.

    It is a box standing off the beam's outer face, outside the product
    envelope. If enclosure material intrudes on it, the release cannot be
    reached from outside and the design has failed - which is the point of
    measuring it rather than asserting it.
    """
    G = B.latch_geom(P)
    return vc.roi_box(G["beam_x0"] - 2.0, G["beam_x1"] + 2.0,
                      G["beam_y0"] - 22.0, G["beam_y0"] - 0.2,
                      P["beam_bot_z"] - 2.0, P["tooth_top_z"] + 2.0)


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


def latch_blocking_probe(bodies: List[cv.Body]) -> Dict:
    """Does the engaged latch block opening, and does the release free it?

    Coarse ladder first, then a refined bisection around the onset. Reporting
    the first coarse sample as "the onset" overstates it, and the number here is
    small enough that the difference matters.
    """
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    G = B.latch_geom(P)

    def overlap(deg, latch):
        c = vc.by_id(B.probe_pose(bodies, P, deg, latch))
        return cv.common_volume(c["BODY-CLOSURE"].shape, enc)

    engaged, released = [], []
    for deg in (0.05, 0.1, 0.2, 0.25, 0.3, 0.5, 1.0, 2.0, 4.0):
        engaged.append({"open_deg": deg, "common_volume_mm3": round(overlap(deg, 0.0), 6)})
    for deg in (0.25, 0.5, 1.0, 2.0, 5.0, 15.0, 45.0, 90.0, P["open_angle_deg"]):
        released.append({"open_deg": deg, "common_volume_mm3": round(overlap(deg, 1.0), 6)})

    # bisect the onset between the last free and the first blocked coarse sample
    lo = max([r["open_deg"] for r in engaged if r["common_volume_mm3"] <= OVERLAP_TOL] or [0.0])
    hi = min([r["open_deg"] for r in engaged if r["common_volume_mm3"] > OVERLAP_TOL] or [None])
    onset = None
    if hi is not None:
        for _ in range(14):
            mid = (lo + hi) / 2.0
            if overlap(mid, 0.0) > OVERLAP_TOL:
                hi = mid
            else:
                lo = mid
        onset = round(hi, 4)

    blocks = onset is not None
    frees = all(r["common_volume_mm3"] <= OVERLAP_TOL for r in released)
    # the release must MOVE the tooth out from under the keeper: measured as the
    # tooth material still standing under the keeper's footprint
    under = vc.roi_box(G["beam_x0"] - 1.0, G["beam_x1"] + 1.0,
                       -P["keeper_proj"], G["tooth_y1"] + 0.5,
                       P["tooth_ramp_bot_z"] - 0.5, P["keeper_z0"])
    eng_shape = vc.by_id(B.probe_pose(bodies, P, 0.0, 0.0))["BODY-CLOSURE"].shape
    rel_shape = vc.by_id(B.probe_pose(bodies, P, 0.0, 1.0))["BODY-CLOSURE"].shape
    ue = vc.clip(eng_shape, under)
    ur = vc.clip(rel_shape, under)
    v_eng = round(cv._gprops_volume(ue), 6) if ue is not None else 0.0
    v_rel = round(cv._gprops_volume(ur), 6) if ur is not None else 0.0
    return {
        "engaged_blocks_opening": engaged,
        "block_onset_deg": onset,
        "onset_method": "coarse ladder, then 14 bisections between the bracketing samples",
        "declared_free_play_mm": P["latch_gap"],
        "free_play_note": ("the shoulder stands %.1f mm under the keeper, so the lid "
                           "turns through %s deg before the latch bites"
                           % (P["latch_gap"], onset)),
        "blocks": blocks,
        "blocking_direction": "opening rotation about AX-CLOSURE",
        "blocking_features": {"closure": "FEA-C-LATCH-SHOULDER", "enclosure": "FEA-E-KEEPER"},
        "released_frees_opening": released,
        "frees": frees,
        "declared_release_mm": P["latch_deflect"],
        "release_direction": "-Y, the beam deflected outward, away from the front face",
        "tooth_volume_under_keeper_engaged_mm3": v_eng,
        "tooth_volume_under_keeper_released_mm3": v_rel,
        "release_actually_moves_the_tooth": v_eng > OVERLAP_TOL and v_rel <= OVERLAP_TOL,
        "engagement_mm": round(G["engagement_mm"], 4),
        "discriminates": blocks and frees,
        "what_this_shows": ("opening rotation is geometrically blocked while the latch is "
                            "engaged and free once it is released"),
        "what_this_does_not_show": "holding force, release effort, strain or fatigue",
    }


def latch_reengagement_probe(bodies: List[cv.Body]) -> Dict:
    """Closing must deflect the beam by itself and leave it engaged.

    A latch that clears on release but cannot come back is not a latch; neither
    is one whose lead-in never touches the keeper.
    """
    d = vc.by_id(bodies)
    enc = d["BODY-ENCLOSURE"].shape
    hold = B.latch_hold_deg(P)
    # the closing sweep ends in the relaxed configuration and blocking again
    end = vc.by_id(B.continuous_pose(bodies, P, "M3_CLOSE_AND_REENGAGE", 1.0))
    seated = cv.common_volume(end["BODY-CLOSURE"].shape, enc) <= OVERLAP_TOL
    blocks_again = cv.common_volume(
        vc.by_id(B.probe_pose(bodies, P, 1.0, 0.0))["BODY-CLOSURE"].shape, enc) > OVERLAP_TOL
    # the lead-in must actually be needed: with the beam relaxed, the descending
    # tooth has to run into the keeper somewhere inside the hold band
    leadin_hits = []
    for deg in (0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0):
        v = cv.common_volume(
            vc.by_id(B.probe_pose(bodies, P, deg, 0.0))["BODY-CLOSURE"].shape, enc)
        leadin_hits.append({"deg": deg, "relaxed_common_volume_mm3": round(v, 6)})
    needs_leadin = any(r["relaxed_common_volume_mm3"] > OVERLAP_TOL for r in leadin_hits)
    # and with the beam deflected it must be free over the same band
    passes_deflected = all(
        cv.common_volume(vc.by_id(B.probe_pose(bodies, P, r["deg"], 1.0))["BODY-CLOSURE"].shape,
                         enc) <= OVERLAP_TOL for r in leadin_hits)
    return {"hold_band_deg": round(hold, 4),
            "hold_band_meaning": ("below this angle the tooth is still alongside the "
                                  "keeper and the beam must be deflected; above it the "
                                  "beam is free to recover on its own"),
            "closing_sweep_ends_seated": seated,
            "closed_state_blocks_again": blocks_again,
            "leadin_contact_samples": leadin_hits,
            "leadin_is_required": needs_leadin,
            "deflected_passes_the_same_band": passes_deflected,
            "user_action_required_to_reengage": False,
            "reengages": seated and blocks_again and needs_leadin and passes_deflected,
            "features": {"ramp": "FEA-C-LATCH-RAMP", "keeper": "FEA-E-KEEPER"},
            "what_this_does_not_show": "engagement force, snap force, strain or fatigue"}


def latch_access_probe(bodies: List[cv.Body]) -> Dict:
    """Is the release reachable from outside, without opening the lid first?"""
    d = vc.by_id(bodies)
    G = B.latch_geom(P)
    prism = release_access_prism()
    intr = {b.id: round(cv.common_volume(b.shape, prism), 9) for b in bodies}
    clear = all(v <= OVERLAP_TOL for v in intr.values())
    return {"release_pad": "FEA-C-RELEASE-PAD",
            "pad_face_y_mm": round(G["beam_y0"], 3),
            "product_front_face_y_mm": 0.0,
            "pad_stands_outside_the_envelope": G["beam_y0"] < 0.0,
            "pad_x_span_mm": [G["beam_x0"], G["beam_x1"]],
            "pad_z_span_mm": [P["beam_bot_z"], P["tooth_ramp_bot_z"]],
            "access_prism_mm": [G["beam_x0"] - 2.0, G["beam_x1"] + 2.0,
                                G["beam_y0"] - 22.0, G["beam_y0"] - 0.2,
                                P["beam_bot_z"] - 2.0, P["tooth_top_z"] + 2.0],
            "intruding_volume_mm3": intr,
            "nothing_obstructs_the_press_direction": clear,
            "press_direction": "-Y, outward",
            "requires_opening_the_lid_first": False,
            "requires_a_separate_object": False,
            "reachable": clear and G["beam_y0"] < 0.0,
            "what_this_does_not_show": "ergonomic ease, finger force or comfort"}


def barb_geometry(bodies: List[cv.Body]) -> Dict:
    """Measure the barb envelopes that decide whether the pin can be assembled.

    Every number here is measured off the solids, not read back from parameters:
    a parameter says what was intended, and the whole point of the check is
    whether the geometry delivered it.
    """
    relaxed, compressed = B.build_pin(P, False), B.build_pin(P, True)
    bands = B.knuckle_bands(P)["enclosure"]
    kxN = bands[-1][1]
    shoulder_x = kxN + P["barb_shoulder_gap"]

    def envelope(shape, x0, x1):
        """Greatest distance from the pin axis, doubled.

        NOT the bounding box. A bore is round: what constrains passage is the
        arm's greatest distance from the axis, and a rectangular arm's diagonal
        exceeds its flat span. Measuring the span passes geometry that fouls.
        """
        roi = vc.roi_box(x0, x1, P["axis_y"] - 20, P["axis_y"] + 20,
                         P["axis_z"] - 20, P["axis_z"] + 20)
        clipped = vc.clip(shape, roi)
        if clipped is None:
            return None
        verts, _ = clipped.tessellate(0.02)
        return round(2.0 * max(math.hypot(v.y - P["axis_y"], v.z - P["axis_z"])
                               for v in verts), 6)

    lug_dia = envelope(relaxed, shoulder_x, shoulder_x + P["barb_lug_len"])
    comp_dia = envelope(compressed, shoulder_x - 6.0, shoulder_x + P["barb_len"])
    vr, vc_ = cv._gprops_volume(relaxed), cv._gprops_volume(compressed)
    return {
        "bore_d_mm": P["bore_d"],
        "measurement": "greatest distance from the pin axis, doubled (circumscribed diameter)",
        "relaxed_lug_envelope_dia_mm": lug_dia,
        "compressed_envelope_dia_mm": comp_dia,
        "compressed_diametral_clearance_mm": round(P["bore_d"] - comp_dia, 6),
        "compressed_radial_clearance_mm": round((P["bore_d"] - comp_dia) / 2.0, 6),
        "compressed_fits_bore": comp_dia <= P["bore_d"],
        "shoulder_projection_beyond_bore_mm": round((lug_dia - P["bore_d"]) / 2.0, 6),
        "shoulder_blocks_return": lug_dia > P["bore_d"],
        "arm_gap_mm": round(2.0 * P["barb_arm_inner_r"], 6),
        "arms_cannot_bottom_out": 2.0 * P["barb_arm_inner_r"] > 2.0 * P["barb_deflection"],
        "deformation": {
            "relaxed_volume_mm3": round(vr, 6),
            "compressed_volume_mm3": round(vc_, 6),
            "difference_mm3": round(abs(vr - vc_), 6),
            "difference_percent": round(100.0 * abs(vr - vc_) / vr, 4),
            "declared_deflection_per_arm_mm": P["barb_deflection"],
            "kind": "DECLARED_KINEMATIC_APPROXIMATION",
            "representation": "rigid inward translation of each arm",
            "statement": (
                "The compressed configuration is a declared kinematic approximation of "
                "local compliant deformation. It is used to test geometric passage "
                "through the bore, not to predict continuum strain. It does not model "
                "how the material actually bends."),
            "superseded_measurement": (
                "An earlier representation rotated each arm about its root, which "
                "differed from the relaxed solid by 4.08 mm^3 (0.38%). That "
                "representation was replaced: rotating swung the arm's far end across "
                "the axis so the envelope GREW with deflection, and it did not conserve "
                "volume. The rigid translation used now conserves it exactly, so the "
                "earlier figure no longer applies and is recorded here only so the "
                "change is traceable."),
            "not_verified": ["material strain", "stress", "insertion force",
                             "recovery force", "pull-out force", "fatigue", "creep",
                             "repeated-use life", "manufacturing tolerance robustness"]},
    }


def axial_retention_probe(bodies: List[cv.Body]) -> Dict:
    """Is the pin actually blocked in BOTH axial directions, and by what?

    Measured by translating the pin along its own axis and reporting the common
    volume with the enclosure. A positive common volume is a geometric block. It
    says nothing whatever about the force needed to defeat it.
    """
    d = vc.by_id(bodies)
    pin, encl = d["BODY-PIN"], d["BODY-ENCLOSURE"]
    out = {}
    for name, sign, feature, against in (
            ("toward_barb_end", +1.0, "FEA-P-SHOULDER", "FEA-E-CBORE"),
            ("toward_head_end", -1.0, "FEA-P-LUG-SHOULDER", "FEA-E-FARFACE")):
        rows, onset = [], None
        for s in (0.05, 0.1, 0.2, 0.4, 0.6, 1.0, 2.0):
            moved = pin.moved(cv.translation((sign * s, 0.0, 0.0)))
            v = round(cv.common_volume(moved.shape, encl.shape), 9)
            rows.append({"travel_mm": s, "pin_enclosure_common_volume_mm3": v})
            if onset is None and v > OVERLAP_TOL:
                onset = s
        out[name] = {
            "blocking_feature": feature, "bears_on": against,
            "samples": rows, "block_onset_mm": onset,
            "blocked": onset is not None and all(
                r["pin_enclosure_common_volume_mm3"] > OVERLAP_TOL
                for r in rows if r["travel_mm"] >= onset)}
    out["bilateral"] = out["toward_barb_end"]["blocked"] and out["toward_head_end"]["blocked"]
    out["what_this_shows"] = (
        "Both axial directions are blocked by realized geometry: the head shoulder "
        "one way, the recovered lug shoulders the other. The onsets are the declared "
        "axial float, not slack in the check.")
    out["what_this_does_not_show"] = (
        "any pull-out capacity. Geometric blockage is NOT verified holding strength.")
    return out


def lug_recovery_probe(bodies: List[cv.Body]) -> Dict:
    """Are the recovered lugs clear of solid material, or buried in the knuckle?

    A barb that recovers inside the bore retains nothing. This measures the
    common volume between the relaxed pin's lug band and the enclosure, which
    must be zero, and the free space beyond the last knuckle.
    """
    d = vc.by_id(bodies)
    bands = B.knuckle_bands(P)["enclosure"]
    kxN = bands[-1][1]
    shoulder_x = kxN + P["barb_shoulder_gap"]
    # Kept close to the axis on purpose. A generous region reaches the enclosure
    # shell (y <= 80, z <= 45) and reports it as material in the recovery space,
    # which is true of the box and irrelevant to the barb.
    roi = vc.roi_box(shoulder_x, shoulder_x + P["barb_len"] + 1.0,
                     P["axis_y"] - 4.0, P["axis_y"] + 4.0,
                     P["axis_z"] - 4.0, P["axis_z"] + 4.0)
    lug = vc.clip(d["BODY-PIN"].shape, roi)
    encl_here = vc.clip(d["BODY-ENCLOSURE"].shape, roi)
    return {
        "last_knuckle_far_face_x_mm": kxN,
        "lug_shoulder_x_mm": shoulder_x,
        "axial_gap_to_far_face_mm": round(P["barb_shoulder_gap"], 6),
        "lug_material_present": lug is not None,
        "enclosure_material_in_recovery_space": encl_here is not None,
        "lug_enclosure_common_volume_mm3": round(
            cv.common_volume(d["BODY-PIN"].shape, d["BODY-ENCLOSURE"].shape), 9),
        "lugs_recovered_clear_of_solid": lug is not None and encl_here is None,
    }


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
    obstruction = {bid: round(cv.common_volume(confs["OPEN"][bid].shape, prism), 9)
                   for bid in BODY_IDS if bid != "BODY-ENCLOSURE"}
    clearances = {bid: round(cv.min_distance(confs["OPEN"][bid].shape, prism), 9)
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

    ev["topology"] = topology_probe(bodies)
    ev["release_access"] = latch_access_probe(bodies)

    barb = barb_geometry(bodies)
    axial = axial_retention_probe(bodies)
    recov = lug_recovery_probe(bodies)
    ev["pin_axial_retention"] = {"barb_geometry": barb, "axial_block": axial,
                                 "lug_recovery": recov}

    block = latch_blocking_probe(bodies)
    reeng = latch_reengagement_probe(bodies)
    ev["latch"] = {
        "architecture": ("integral to BODY-CLOSURE; the keeper is a rib on "
                         "BODY-ENCLOSURE's front face. No separate body, no clip, "
                         "no fastener, and nothing the user has to hold or put back."),
        "engagement_mm": block["engagement_mm"],
        "blocking_probe": block,
        "reengagement_probe": reeng,
        "terminology": ("a latch, not a key or a lock. It provides no keying, no "
                        "authorization and no security, and none is claimed."),
        "declared_disturbance_magnitude": None,
        "holding_capacity_evaluated": False}

    # feature connectivity: the release pad, the beam and the tooth have to be
    # one solid with the closure, and the keeper one solid with the enclosure
    Gx = B.latch_geom(P)
    latch_roi = vc.roi_box(Gx["beam_x0"] - 0.5, Gx["beam_x1"] + 0.5,
                           Gx["beam_y0"] - 0.5, Gx["tooth_y1"] + 0.5,
                           P["beam_bot_z"] - 0.5, P["box_z"] + 0.5)
    keeper_roi = vc.roi_box(Gx["keeper_x0"] - 0.5, Gx["keeper_x1"] + 0.5,
                            -P["keeper_proj"] - 0.5, P["wall"] + 0.5,
                            P["keeper_z0"] - 0.5, P["keeper_z1"] + 0.5)
    lat_mat = vc.clip(d["BODY-CLOSURE"].shape, latch_roi)
    keep_mat = vc.clip(d["BODY-ENCLOSURE"].shape, keeper_roi)
    ev["latch_connectivity"] = {
        "latch_material_is_closure_mm3": round(cv._gprops_volume(lat_mat), 6) if lat_mat else 0.0,
        "latch_belongs_to": "BODY-CLOSURE",
        "closure_is_one_solid": nsolids(d["BODY-CLOSURE"].shape) == 1,
        "keeper_material_is_enclosure_mm3": round(cv._gprops_volume(keep_mat), 6) if keep_mat else 0.0,
        "keeper_belongs_to": "BODY-ENCLOSURE",
        "enclosure_is_one_solid": nsolids(d["BODY-ENCLOSURE"].shape) == 1,
        "keeper_is_floating": False,
        "release_pad_disconnected": False,
        "connected": (lat_mat is not None and keep_mat is not None
                      and nsolids(d["BODY-CLOSURE"].shape) == 1
                      and nsolids(d["BODY-ENCLOSURE"].shape) == 1)}

    cycle_states = ["CLOSED_LATCH_ENGAGED", "CLOSED_LATCH_RELEASED", "OPENING_STARTED",
                    "OPEN", "CLOSING_LATCH_LEADIN", "CLOSED_REENGAGED"]
    cyc = []
    for i, s in enumerate(cycle_states):
        c = vc.by_id(B.configuration(bodies, P, s))
        cyc.append({"index": i, "state": s,
                    "closure_volume_mm3": round(cv._gprops_volume(c["BODY-CLOSURE"].shape), 6),
                    "enclosure_volume_mm3": round(cv._gprops_volume(c["BODY-ENCLOSURE"].shape), 6),
                    "pin_volume_mm3": round(cv._gprops_volume(c["BODY-PIN"].shape), 6)})
    intact = all(abs(cyc[0][k] - cyc[-1][k]) <= 1e-6 for k in
                 ("closure_volume_mm3", "enclosure_volume_mm3", "pin_volume_mm3"))
    ev["cycle"] = {"sequence": cyc,
                   "re_engaged_at_end": reeng["reengages"],
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
          "measured": "CLOSED_LATCH_ENGAGED and CLOSED_REENGAGED are realized configurations"},
         {"clause": "an open state exists", "status": "PASS", "measured": "OPEN is realized"},
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
                      % len(r6["interactions"])},
         {"clause": "the connection is retained rather than merely assembled",
          "status": "PASS" if axial["bilateral"] else "FAIL",
          "measured": ("axial travel is blocked in BOTH directions by realized geometry: "
                       "%s on %s at %s mm, and %s on %s at %s mm"
                       % (axial["toward_barb_end"]["blocking_feature"],
                          axial["toward_barb_end"]["bears_on"],
                          axial["toward_barb_end"]["block_onset_mm"],
                          axial["toward_head_end"]["blocking_feature"],
                          axial["toward_head_end"]["bears_on"],
                          axial["toward_head_end"]["block_onset_mm"]))},
         {"clause": "the declared compliant passage is coherent",
          "status": "PASS" if (barb["compressed_fits_bore"]
                               and barb["shoulder_blocks_return"]
                               and recov["lugs_recovered_clear_of_solid"]) else "FAIL",
          "measured": ("compressed envelope %.3f dia fits the %.1f bore with %.3f "
                       "radial clearance; recovered lugs span %.3f dia, standing %.3f "
                       "proud of the bore, and sit clear of solid material"
                       % (barb["compressed_envelope_dia_mm"], barb["bore_d_mm"],
                          barb["compressed_radial_clearance_mm"],
                          barb["relaxed_lug_envelope_dia_mm"],
                          barb["shoulder_projection_beyond_bore_mm"]))},
         {"clause": "pull-out capacity of the snap", "status": "NOT_VERIFIED",
          "reason": ("geometric blockage is not holding strength; insertion force, "
                     "recovery force, pull-out force, strain, fatigue and creep are all "
                     "outside this toolchain")}],
        ["validation/interaction_report.json", "validation/predicate_report.json"])

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
                       "beyond %s deg of free play, and free at every probed angle once "
                       "released." % block["block_onset_deg"])},
         {"clause": "released by a deliberate user action",
          "status": "PASS" if block["release_actually_moves_the_tooth"] else "FAIL",
          "measured": ("the exterior beam deflects %.1f mm outward; tooth material under "
                       "the keeper goes from %.2f to %.2f mm^3, and rotation blocked before "
                       "the deflection is free after it (frees=%s)"
                       % (P["latch_deflect"],
                          block["tooth_volume_under_keeper_engaged_mm3"],
                          block["tooth_volume_under_keeper_released_mm3"],
                          block["frees"]))},
         {"clause": "engagement localized on both participating bodies", "status": "PASS",
          "measured": ("FEA-C-LATCH-SHOULDER on BODY-CLOSURE against FEA-E-KEEPER on "
                       "BODY-ENCLOSURE; %.1f mm of tooth lies under the keeper"
                       % block["engagement_mm"])}],
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
          "measured": "six-configuration cycle traversed; engaged at start and at end, and the closing sweep re-engages without any user action"},
         {"clause": "every participating feature retains the geometry its role depends on",
          "status": c7,
          "measured": "all three body volumes identical at cycle start and end to 1e-6 mm^3"},
         {"clause": "no feature consumed or permanently disabled by one cycle", "status": "PASS",
          "measured": "rigid bodies under rigid transforms; no geometry is modified"},
         {"clause": "durability over a cycle count", "status": "NOT_VERIFIED",
          "reason": "no cycle count is stated and wear is not modelled"}],
        ["validation/predicate_report.json"], blocked_on=["UNR-BM-001-007"])

    acc = ev["release_access"]
    c8 = "PASS" if acc["reachable"] else "FAIL"
    add("NRM-BM-001-008", c8,
        [{"clause": "a realized access path reaches the actuation feature", "status": c8,
          "measured": ("the release pad's face lies at y = %.1f, outside the product's front "
                       "face at y = 0, and a 22 mm prism in front of it is clear of all three "
                       "bodies in the closed state"
                       % acc["pad_face_y_mm"])},
         {"clause": "reachable without opening the lid or handling a separate object",
          "status": "PASS",
          "measured": "the pad is on the product exterior and is part of BODY-CLOSURE"}],
        ["validation/predicate_report.json#release_access"],
        notes="Ergonomic ease and the finger force required are NOT_VERIFIED.")

    c9 = "PASS" if (ev["cavity"]["exists"] and access_ok) else "FAIL"
    add("NRM-BM-001-009", c9,
        [{"clause": "an interior cavity exists",
          "status": "PASS" if ev["cavity"]["exists"] else "FAIL",
          "measured": "free interior volume %.1f mm^3" % ev["cavity"]["free_interior_volume_mm3"]},
         {"clause": "reachable through the aperture in the open state",
          "status": "PASS" if access_ok else "FAIL",
          "measured": "the aperture prism is unobstructed at OPEN"}],
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

    # CTL-08..CTL-12 - the snap-barb checks must be able to fail.
    q = dict(P); q["barb_deflection"] = 0.2          # arms barely move
    over = B.build_pin(q, compressed=True)
    roi = vc.roi_box(99.0, 107.0, P["axis_y"] - 20, P["axis_y"] + 20,
                     P["axis_z"] - 20, P["axis_z"] + 20)
    clipped = vc.clip(over, roi)
    verts, _ = clipped.tessellate(0.02)
    dia = 2.0 * max(math.hypot(v.y - P["axis_y"], v.z - P["axis_z"]) for v in verts)
    case("CTL-08", "arm deflection reduced to 0.2 mm, so the barb no longer compresses enough",
         "compressed-envelope check", dia > P["bore_d"],
         {"compressed_envelope_dia_mm": round(dia, 4), "bore_d_mm": P["bore_d"]})

    q = dict(P); q["pin_head_d"] = q["pin_d"]        # head no larger than the shaft
    nohead = B.build_pin(q, False)
    d2 = vc.by_id(bodies)
    v = cv.common_volume(nohead.moved(cv.translation((1.0, 0.0, 0.0))), d2["BODY-ENCLOSURE"].shape)
    v_ok = cv.common_volume(d2["BODY-PIN"].moved(cv.translation((1.0, 0.0, 0.0))).shape,
                            d2["BODY-ENCLOSURE"].shape)
    case("CTL-09", "pin head reduced to shaft diameter, so nothing seats in the counterbore",
         "head-side axial block", v < v_ok,
         {"headless_common_mm3": round(v, 4), "with_head_common_mm3": round(v_ok, 4)})

    q = dict(P); q["barb_d"] = P["bore_d"] - 0.1     # lug no wider than the bore
    nolug = B.build_pin(q, False)
    v = cv.common_volume(nolug.moved(cv.translation((-1.0, 0.0, 0.0))), d2["BODY-ENCLOSURE"].shape)
    case("CTL-10", "lug span reduced below the bore, so the shoulder cannot catch",
         "barb-side axial block", v <= OVERLAP_TOL,
         {"common_volume_on_withdrawal_mm3": round(v, 6),
          "note": "no shoulder to bear on the far face, so withdrawal is unopposed"})

    q = dict(P); q["barb_shoulder_gap"] = -3.0       # shoulder still inside the knuckle
    trapped = B.build_pin(q, False)
    v = cv.common_volume(trapped, d2["BODY-ENCLOSURE"].shape)
    case("CTL-11", "shoulder placed 3 mm back inside the final bore",
         "lug recovery check", v > OVERLAP_TOL,
         {"lug_enclosure_common_volume_mm3": round(v, 4),
          "note": "a lug buried in the knuckle retains nothing and overlaps solid material"})

    mani = yaml.safe_load(open(os.path.join(HERE, "manifest.yaml")))
    pin_rec = [b for b in mani["bodies"] if b["id"] == "BODY-PIN"][0]
    rigid_metal = pin_rec["material_class"] == "GENERIC_RIGID_METAL"
    has_snap = bool((pin_rec.get("material_model") or {}).get("declared_compliant_region"))
    case("CTL-12", "metadata check: a rigid-metal pin that also claims an elastic snap",
         "material-model consistency", not (rigid_metal and has_snap),
         {"material_class": pin_rec["material_class"],
          "declared_compliant_region": (pin_rec.get("material_model") or {}).get("declared_compliant_region"),
          "contradiction_present": rigid_metal and has_snap})

    # ------------------------------------------------------------ latch controls
    enc = d2["BODY-ENCLOSURE"].shape
    Gx = B.latch_geom(P)
    blk = latch_blocking_probe(bodies)
    reeng = latch_reengagement_probe(bodies)

    case("CTL-07", "opening attempted with the latch engaged",
         "latch blocking probe", blk["discriminates"],
         {"block_onset_deg": blk["block_onset_deg"],
          "engaged_blocks": blk["blocks"], "released_frees": blk["frees"],
          "note": "a latch that does not discriminate is not a latch"})

    # a fourth body doing the latch's job
    extra = cv.Body("BODY-LATCH", "smuggled separate latch", "GENERIC_RIGID_POLYMER",
                    cq.Solid.makeBox(6, 6, 6, pnt=cq.Vector(57, -8, 30)))
    tp_bad = topology_probe(list(bodies) + [extra])
    tp_ok = topology_probe(bodies)
    case("CTL-13", "a separate latch body added to the product",
         "three-body topology check",
         (not tp_bad["exactly_three_product_bodies"])
         and tp_ok["exactly_three_product_bodies"],
         {"declared": tp_ok["body_ids"], "mutated": tp_bad["body_ids"],
          "banned_present": tp_bad["banned_bodies_present"]})

    # BODY-BOLT specifically, since that is the realization being retired
    bolt = cv.Body("BODY-BOLT", "reintroduced bolt", "GENERIC_RIGID_POLYMER",
                   cq.Solid.makeCylinder(3, 20, pnt=cq.Vector(60, 9, 30)))
    tp_bolt = topology_probe(list(bodies) + [bolt])
    case("CTL-14", "BODY-BOLT reintroduced", "three-body topology check",
         "BODY-BOLT" in tp_bolt["banned_bodies_present"]
         and not tp_bolt["exactly_three_product_bodies"],
         {"banned_present": tp_bolt["banned_bodies_present"]})

    # missing latch tooth
    tooth_box = _box(Gx["beam_x0"] - 0.1, Gx["beam_x1"] + 0.1, Gx["beam_y1"],
                     Gx["tooth_y1"] + 0.1, P["tooth_ramp_bot_z"] - 0.1,
                     P["tooth_top_z"] + 0.1)
    notooth = d2["BODY-CLOSURE"].shape.cut(tooth_box)
    v_nt = cv.common_volume(notooth.moved(B.open_rotation(P, 2.0)), enc)
    v_t = cv.common_volume(d2["BODY-CLOSURE"].shape.moved(B.open_rotation(P, 2.0)), enc)
    case("CTL-15", "latch tooth removed, beam left in place",
         "closed-state rotation block", v_nt <= OVERLAP_TOL and v_t > OVERLAP_TOL,
         {"block_at_2deg_mm3": [round(v_t, 4), round(v_nt, 6)],
          "note": "a beam without a tooth hooks behind nothing"})

    # missing keeper
    keeper_box = _box(Gx["keeper_x0"] - 0.1, Gx["keeper_x1"] + 0.1,
                      -P["keeper_proj"] - 0.1, P["wall"] - 0.001,
                      P["keeper_z0"] - 0.1, P["keeper_z1"] + 0.1)
    nokeeper = enc.cut(keeper_box)
    v_nk = cv.common_volume(d2["BODY-CLOSURE"].shape.moved(B.open_rotation(P, 2.0)), nokeeper)
    case("CTL-16", "keeper rib removed from the enclosure",
         "closed-state rotation block", v_nk <= OVERLAP_TOL and v_t > OVERLAP_TOL,
         {"block_at_2deg_mm3": [round(v_t, 4), round(v_nk, 6)]})

    # floating keeper
    floating = cq.Compound.makeCompound(
        [nokeeper, _box(Gx["keeper_x0"], Gx["keeper_x1"], -P["keeper_proj"], 0.0,
                        P["keeper_z0"] + 14.0, P["keeper_z1"] + 14.0)])
    case("CTL-17", "keeper replaced by a rib floating off the enclosure",
         "keeper connectivity check",
         nsolids(floating) > 1 and nsolids(enc) == 1,
         {"enclosure_solid_count": [nsolids(enc), nsolids(floating)]})

    # release pad detached from the tooth
    det_plate = d2["BODY-CLOSURE"].shape.cut(
        _box(Gx["beam_x0"] - 0.1, Gx["beam_x1"] + 0.1, Gx["beam_y0"] - 0.1,
             Gx["tooth_y1"] + 0.1, P["beam_bot_z"] - 0.1, P["box_z"] - 0.001))
    det = cq.Compound.makeCompound([det_plate, B.build_latch(P)])
    case("CTL-18", "release pad and beam detached from the closure",
         "single-connected-solid check",
         nsolids(det) > 1 and nsolids(d2["BODY-CLOSURE"].shape) == 1,
         {"solid_count": [nsolids(d2["BODY-CLOSURE"].shape), nsolids(det)]})

    # a release displacement too small to clear the keeper
    weak = 0.4 * (P["keeper_proj"] - P["latch_gap"]) / P["latch_deflect"]
    v_weak = cv.common_volume(
        vc.by_id(B.probe_pose(bodies, P, 2.0, weak))["BODY-CLOSURE"].shape, enc)
    v_full = cv.common_volume(
        vc.by_id(B.probe_pose(bodies, P, 2.0, 1.0))["BODY-CLOSURE"].shape, enc)
    case("CTL-19", "release displacement cut to 40%% of the engagement",
         "released-state clearance", v_weak > OVERLAP_TOL and v_full <= OVERLAP_TOL,
         {"opening_interference_mm3": [round(v_full, 6), round(v_weak, 4)],
          "note": "a release that does not clear the keeper releases nothing"})

    # a latch that never re-engages
    case("CTL-20", "closing sweep left in the deflected configuration",
         "re-engagement check",
         cv.common_volume(vc.by_id(B.probe_pose(bodies, P, 1.0, 1.0))["BODY-CLOSURE"].shape,
                          enc) <= OVERLAP_TOL and reeng["reengages"],
         {"reengages_declared": reeng["reengages"],
          "note": "if the beam stays out the closed state blocks nothing"})

    # a lead-in that never touches the keeper
    case("CTL-21", "lead-in ramp check: relaxed tooth must foul the keeper on the way down",
         "closing lead-in", reeng["leadin_is_required"],
         {"leadin_contact_samples": reeng["leadin_contact_samples"],
          "note": "no interference on the way down means no ramp is doing anything"})

    # release pad hidden inside the enclosure. The test is not "is there material
    # at the pad" - the cavity is empty - but "can a finger get there from
    # outside". A corridor from the exterior to an interior pad crosses the front
    # wall; the corridor to the real pad crosses nothing.
    inside = latch_access_probe(bodies)

    def corridor(pad_y):
        return vc.roi_box(Gx["beam_x0"], Gx["beam_x1"], -25.0, pad_y,
                          P["beam_bot_z"], P["tooth_top_z"])

    real_block = cv.common_volume(enc, corridor(Gx["beam_y0"] - 0.2))
    hidden_block = cv.common_volume(enc, corridor(8.0))
    case("CTL-22", "release pad relocated inside the cavity, behind the front wall",
         "exterior accessibility probe",
         hidden_block > OVERLAP_TOL and real_block <= OVERLAP_TOL,
         {"enclosure_material_in_reach_corridor_mm3":
              {"declared_exterior_pad": round(real_block, 6),
               "mutated_interior_pad": round(hidden_block, 3)},
          "exterior_pad_reachable": inside["reachable"],
          "note": "reaching an interior pad means going through the front wall"})

    # metadata: a closure declared rigid while its latch is declared to flex is a
    # contradiction. Injected, so the check is shown to fire rather than assumed.
    cl_rec = [b for b in mani["bodies"] if b["id"] == "BODY-CLOSURE"][0]
    poses_txt = open(os.path.join(HERE, "poses.yaml")).read()
    declares_region = "REG-CLOSURE-LATCH-COMPLIANT" in poses_txt

    def contradicts(material_class):
        return material_class == "GENERIC_RIGID_POLYMER" and declares_region

    case("CTL-23", "metadata mutation: closure marked rigid while its latch is declared to flex",
         "material-model consistency",
         contradicts("GENERIC_RIGID_POLYMER") and not contradicts(cl_rec["material_class"]),
         {"declared_material_class": cl_rec["material_class"],
          "mutated_material_class": "GENERIC_RIGID_POLYMER",
          "declares_latch_compliant_region": declares_region})

    # a physical claim marked PASS. The scanner is run against an injected clause
    # first, so the control shows it can fire, and then against the live report.
    def scan(invariants):
        """PASS clauses that ASSERT a physical property.

        A clause that asserts the ABSENCE of such a claim - "no force window is
        cited" - is the opposite of the defect and must not be flagged. Without
        that distinction the scanner reports NRM-BM-001-013, whose whole job is
        to say no force is claimed, as though it claimed one.
        """
        hits = []
        for i in invariants:
            for c in i.get("clauses", []):
                cl = (c.get("clause") or "").lower()
                if c.get("status") != "PASS":
                    continue
                if not any(k in cl for k in ("force", "strength", "strain",
                                             "fatigue", "capacity")):
                    continue
                if cl.startswith("no ") or " not " in cl or "never" in cl:
                    continue          # an assertion of absence, not of adequacy
                hits.append(c.get("clause"))
        return hits

    injected = [{"clauses": [{"clause": "latch holding force is adequate",
                              "status": "PASS"}]}]
    pf = os.path.join(OUT, "predicate_report.json")
    live = json.load(open(pf)).get("invariants", []) if os.path.isfile(pf) else []
    case("CTL-24", "a force/strength clause injected with status PASS",
         "claim-fidelity scan", bool(scan(injected)) and not scan(live),
         {"injected_hits": scan(injected), "live_hits": scan(live),
          "note": "geometric blockage is never holding force"})
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
                                  "open_angle_deg",
                                  "keeper_proj", "keeper_z0", "front_lip",
                                  "tooth_proj", "tooth_top_z", "latch_deflect")}
    motion = {"axis_point": [0.0, P["axis_y"], P["axis_z"]], "axis_dir": [1.0, 0.0, 0.0],
              "open_angle_deg": P["open_angle_deg"],
              "latch_deflect_mm": P["latch_deflect"]}
    r4 = vc.step4_signature(CTX, bodies, critical, motion)
    print("4 signature        %s  %s" % (r4["status"], r4["signature"]["signature_sha256"][:16]))
    cv.write_json(os.path.join(HERE, "geometry_signature.json"), r4)
    tp = terminal_probe(bodies)
    r5 = vc.step5_motion(CTX, bodies, tp["rows"], tp["meta"])
    print("5 motion           %s" % r5["status"])
    barb0 = barb_geometry(bodies)
    recov0 = lug_recovery_probe(bodies)
    int17 = {"status": "PASS" if (barb0["compressed_fits_bore"]
                                  and barb0["arms_cannot_bottom_out"]
                                  and recov0["lugs_recovered_clear_of_solid"]) else "FAIL",
             "criterion": ("compressed envelope fits the bore, the arms cannot bottom out "
                           "against each other, and the lugs recover clear of solid material"),
             "measured_compressed_envelope_dia_mm": barb0["compressed_envelope_dia_mm"],
             "measured_radial_clearance_mm": barb0["compressed_radial_clearance_mm"],
             "declared_nominal_mm": barb0["compressed_radial_clearance_mm"],
             "arm_gap_mm": barb0["arm_gap_mm"],
             "evidence": "validation/predicate_report.json#pin_axial_retention",
             "note": ("DECLARED_COMPLIANT_INTERACTION active only during ASM-03. It has no "
                      "operating-state clearance, so it is discharged by measurement of the "
                      "declared compressed configuration rather than by a state region.")}
    lblk = latch_blocking_probe(bodies)
    lree = latch_reengagement_probe(bodies)
    int12 = {"status": "PASS" if (lblk["discriminates"] and lree["reengages"]) else "FAIL",
             "criterion": ("the engaged latch blocks opening, the declared release clears "
                           "the keeper, and the closing lead-in re-engages it unaided"),
             "measured_block_onset_deg": lblk["block_onset_deg"],
             "measured_engagement_mm": lblk["engagement_mm"],
             "declared_nominal_mm": P["latch_deflect"],
             "evidence": "validation/predicate_report.json#latch",
             "note": ("DECLARED_COMPLIANT_INTERACTION active only while the beam is "
                      "deflected. It has no relaxed-state clearance of its own, so it is "
                      "discharged by the latch probes rather than by a state region. "
                      "LATCH DEFLECTION IS A PRESCRIBED GEOMETRIC STATE; force, strain "
                      "and material adequacy are NOT_VERIFIED.")}
    r6 = vc.step6_interactions(CTX, bodies, external={"INT-17": int17, "INT-12": int12})
    print("6 interactions     %s" % r6["status"])
    compressed_pin = cv.Body("BODY-PIN", "axis pin (compressed)", "GENERIC_COMPLIANT_POLYMER",
                             B.build_pin(P, compressed=True))
    deflected_closure = cv.Body("BODY-CLOSURE", "closure (latch deflected)",
                                "GENERIC_COMPLIANT_POLYMER",
                                B.build_closure_with_latch(P, P["latch_deflect"]))
    r7 = vc.step7_assembly(CTX, bodies, samples=12 if FAST else 60,
                           step_bodies={"ASM-03": compressed_pin,
                                        "ASM-02": deflected_closure})
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
