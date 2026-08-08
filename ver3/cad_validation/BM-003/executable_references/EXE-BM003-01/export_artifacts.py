"""EXE-BM003-01 - the exchange-artifact export pass, in the required order.

The shared engine (valcore step 3) exports and round-trips each body early,
because that is where its fixed step order puts it. That is a useful check and it
runs. But this reference's export ORDER is itself a requirement, and it is:

  1  construct the in-memory CadQuery/OCCT B-rep          (build.py)
  2  validate the native shapes                           (validate.py step 2)
  3  validate the assembly insertion paths                (validate.py step 7)
  4  validate the full motion                             (validate.py step 5)
  5  generate the geometry signature FROM THE NATIVE SHAPES(validate.py step 4)
  6  export body-level native .brep                        <- here
  7  export the assembled-state .brep                      <- here
  8  export body-level .step                               <- here
  9  export the assembled-state .step                      <- here
 10  re-import every STEP                                  <- here
 11  compare validity, volume, bounding box, body identity <- here
 12  record the round-trip results                         <- here

So this script runs AFTER validate.py and performs 6 to 12 explicitly, in that
order, and records the order it actually performed. The exports are
deterministic, so the files it writes are the ones valcore already wrote; what is
new is the ordering evidence, the assembled-state STEP round trip, and the
body-identity comparison, none of which valcore does.

STEP IS AN EXCHANGE ARTIFACT. It is not the authoritative design source. The
authoritative source is parameters.yaml + build.py + the native OCCT B-rep.

Run:  python export_artifacts.py
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, HERE)

import cadquery as cq                              # noqa: E402
import cadval as cv                                # noqa: E402
import build as B                                  # noqa: E402

OUT = os.path.join(HERE, "validation")
BBOX_TOL = 1e-6
VOL_TOL_ABS = 1e-6


def stem(bid: str) -> str:
    return bid.lower().replace("body-", "").replace("-", "_")


def bbox_delta(a: Dict[str, float], b: Dict[str, float]) -> float:
    return max(abs(a[k] - b[k]) for k in ("xmin", "xmax", "ymin", "ymax",
                                          "zmin", "zmax"))


def main() -> int:
    P = B.load_params()
    order: List[Dict] = []

    # --- 5 (precondition) the signature is taken from the NATIVE shapes -------
    bodies = B.build(P)
    native = {b.id: {"volume_mm3": cv._gprops_volume(b.shape),
                     "bbox_mm": cv.bbox_of(b.shape),
                     "valid": cv.is_valid(b.shape)} for b in bodies}
    order.append({"step": 5, "action": "geometry signature taken from the native shapes",
                  "note": "done in validate.py step 4; recorded here as the precondition"})

    # --- 6 body-level native .brep -------------------------------------------
    brep_paths = {}
    for b in bodies:
        p = os.path.join(HERE, "%s.brep" % stem(b.id))
        cv.export_brep(b.shape, p)
        brep_paths[b.id] = p
    order.append({"step": 6, "action": "export body-level native .brep",
                  "files": [os.path.relpath(brep_paths[b.id], HERE) for b in bodies]})

    # --- 7 assembled-state .brep ---------------------------------------------
    asm = cv.compound(bodies)
    asm_brep = os.path.join(HERE, "model.brep")
    cv.export_brep(asm, asm_brep)
    order.append({"step": 7, "action": "export the assembled-state .brep",
                  "files": ["model.brep"]})

    # --- 8 body-level .step --------------------------------------------------
    step_paths = {}
    for b in bodies:
        p = os.path.join(HERE, "%s.step" % stem(b.id))
        cv.export_step(b.shape, p)
        step_paths[b.id] = p
    order.append({"step": 8, "action": "export body-level .step",
                  "files": [os.path.relpath(step_paths[b.id], HERE) for b in bodies]})

    # --- 9 assembled-state .step ---------------------------------------------
    asm_step = os.path.join(HERE, "model.step")
    cv.export_step(asm, asm_step)
    order.append({"step": 9, "action": "export the assembled-state .step",
                  "files": ["model.step"]})

    # --- 10 re-import every STEP (and every BREP) ----------------------------
    rows = []
    for b in bodies:
        rs = cv.import_step(step_paths[b.id])
        rb = cv.import_brep(brep_paths[b.id])
        n = native[b.id]
        row = {
            "body_id": b.id,
            "step_file": os.path.relpath(step_paths[b.id], HERE),
            "brep_file": os.path.relpath(brep_paths[b.id], HERE),
            "step_sha256": cv.sha256_file(step_paths[b.id]),
            "brep_sha256": cv.sha256_file(brep_paths[b.id]),
            "native_volume_mm3": round(n["volume_mm3"], 9),
            "step_volume_mm3": round(cv._gprops_volume(rs), 9),
            "brep_volume_mm3": round(cv._gprops_volume(rb), 9),
            "native_valid": n["valid"],
            "step_valid": cv.is_valid(rs),
            "brep_valid": cv.is_valid(rb),
            "step_bbox_delta_mm": round(bbox_delta(n["bbox_mm"], cv.bbox_of(rs)), 12),
            "brep_bbox_delta_mm": round(bbox_delta(n["bbox_mm"], cv.bbox_of(rb)), 12),
        }
        row["step_volume_delta_mm3"] = round(abs(row["step_volume_mm3"]
                                                 - row["native_volume_mm3"]), 12)
        row["brep_volume_delta_mm3"] = round(abs(row["brep_volume_mm3"]
                                                 - row["native_volume_mm3"]), 12)
        # STEP re-fits geometry on a round trip, so it gets a relative tolerance.
        # BREP is the kernel's own format and must be exact.
        row["step_within_tolerance"] = (
            row["step_volume_delta_mm3"] <= max(VOL_TOL_ABS, 1e-9 * n["volume_mm3"])
            and row["step_bbox_delta_mm"] <= max(BBOX_TOL, 1e-9 * 200.0))
        row["brep_within_tolerance"] = (row["brep_volume_delta_mm3"] <= VOL_TOL_ABS
                                        and row["brep_bbox_delta_mm"] <= BBOX_TOL)
        row["status"] = ("PASS" if (row["step_valid"] and row["brep_valid"]
                                    and row["step_within_tolerance"]
                                    and row["brep_within_tolerance"]) else "FAIL")
        rows.append(row)
    order.append({"step": 10, "action": "re-import every STEP and every BREP"})

    # --- 11 body identity across the assembled-state round trip --------------
    asm_rs = cv.import_step(asm_step)
    asm_rb = cv.import_brep(asm_brep)
    solids = cq.Workplane("XY").add(asm_rs).solids().vals()
    matched, unmatched = [], []
    remaining = list(solids)
    for b in bodies:
        n = native[b.id]
        hit = None
        for s in remaining:
            if (abs(cv._gprops_volume(s) - n["volume_mm3"])
                    <= max(VOL_TOL_ABS, 1e-9 * n["volume_mm3"])
                    and bbox_delta(n["bbox_mm"], cv.bbox_of(s)) <= 1e-6):
                hit = s
                break
        if hit is None:
            unmatched.append(b.id)
        else:
            remaining.remove(hit)
            matched.append({"body_id": b.id,
                            "matched_on": "volume and bounding box, both within tolerance",
                            "volume_mm3": round(cv._gprops_volume(hit), 9)})
    identity = {
        "assembled_step_solid_count": len(solids),
        "expected_body_count": len(bodies),
        "matched": matched,
        "unmatched_bodies": unmatched,
        "unclaimed_solids": len(remaining),
        "assembled_step_volume_mm3": round(cv._gprops_volume(asm_rs), 9),
        "assembled_brep_volume_mm3": round(cv._gprops_volume(asm_rb), 9),
        "assembled_native_volume_mm3": round(cv._gprops_volume(asm), 9),
        "method": ("STEP AP214 as written by this exporter carries no semantic body "
                   "name, so identity is re-established geometrically: each "
                   "re-imported solid is matched to exactly one as-built body by "
                   "volume AND bounding box, and every body must be matched exactly "
                   "once. That is weaker than a carried name and is reported as such."),
        "status": ("PASS" if (len(solids) == len(bodies) and not unmatched
                              and not remaining) else "FAIL"),
    }
    order.append({"step": 11, "action": "compare validity, volume, bounding box and "
                                        "body identity"})

    # --- 12 record ------------------------------------------------------------
    bad = [r for r in rows if r["status"] != "PASS"]
    rec = {
        "reference_id": "EXE-BM003-01",
        "authoritative_source": "parameters.yaml + build.py + the native OCCT B-rep",
        "step_is": ("an exchange artifact. It is not the authoritative design source "
                    "and nothing downstream reads one."),
        "required_order": [
            "1 construct the in-memory CadQuery/OCCT B-rep",
            "2 validate the native shapes",
            "3 validate the assembly insertion paths",
            "4 validate the full motion",
            "5 generate the geometry signature from the native shapes",
            "6 export body-level native .brep",
            "7 export the assembled-state .brep",
            "8 export body-level .step",
            "9 export the assembled-state .step",
            "10 re-import every STEP",
            "11 compare validity, volume, bounding box, body identity metadata",
            "12 record the round-trip results"],
        "order_performed_here": order,
        "steps_1_to_5_performed_by": ("validate.py, which must be run first; this "
                                      "script performs 6 to 12"),
        "note_on_valcore": (
            "the shared engine also exports and round-trips each body at its own "
            "step 3, earlier than this order requires. That check runs and passes; "
            "the exports are deterministic so the files are identical. This pass is "
            "what establishes the ORDER, the assembled-state STEP round trip and the "
            "body-identity comparison, none of which the engine does."),
        "tolerances": {"brep_volume_mm3": VOL_TOL_ABS, "brep_bbox_mm": BBOX_TOL,
                       "step": "relative; a STEP round trip re-fits geometry",
                       "why_not_byte_hashes": (
                           "STEP output varies between exporter builds, so a byte "
                           "hash cannot be the reproducibility criterion. The hashes "
                           "are recorded for provenance only; reproducibility is "
                           "judged on the kernel's own mass properties.")},
        "bodies": rows,
        "assembled_identity": identity,
        "status": "PASS" if (not bad and identity["status"] == "PASS") else "FAIL",
    }
    cv.write_json(os.path.join(OUT, "export_order.json"), rec)
    print("export order pass:", rec["status"])
    print("  bodies round-tripped:", len(rows), " failures:", len(bad))
    print("  assembled STEP identity:", identity["status"],
          "(%d solids, %d bodies)" % (identity["assembled_step_solid_count"],
                                      identity["expected_body_count"]))
    return 0 if rec["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
