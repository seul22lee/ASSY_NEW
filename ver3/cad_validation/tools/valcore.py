"""Shared validation engine for the Ver3 CAD references.

Steps 1-7 and 9 of CAD_VALIDATION_PLAN.yaml are identical in method for every
reference: build, check the solids, round-trip them, sign them, sample the
declared motion, measure the declared interactions inside declared regions,
sweep the declared assembly, render. Only what is declared differs. That common
method lives here so it is written once and reviewed once, and so two references
cannot silently diverge in how they make the same claim.

Step 8 - what the Oracle concludes - stays in each reference's own validate.py,
because it is the part that genuinely differs.

Nothing here decides a status by assertion. Every result is a number computed
with the B-rep kernel.
"""
from __future__ import annotations

import os
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import cadquery as cq
import yaml
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common

import cadval as cv


class Ctx:
    """Everything the engine needs from a reference."""

    def __init__(self, ref_id: str, here: str, params: Dict[str, float], mod,
                 contact_by_state: Dict[str, Dict[Tuple[str, str], List[str]]],
                 segment_contact: Dict[str, set],
                 roi: Dict[str, tuple], sampling: Dict[str, tuple],
                 colors: Dict[str, str], sections: Sequence[tuple],
                 alphas: Optional[Dict[str, float]] = None):
        self.ref_id, self.HERE, self.P, self.M = ref_id, here, params, mod
        self.OUT = os.path.join(here, "validation")
        self.CONTACT_TOL = params["contact_tol"]
        self.OVERLAP_TOL = params["overlap_tol_mm3"]
        self.BODY_IDS = sorted(b.id for b in mod.build(params))
        self.PAIRS = [(a, b) for i, a in enumerate(self.BODY_IDS)
                      for b in self.BODY_IDS[i + 1:]]
        self.CONTACT_BY_STATE = contact_by_state
        self.SEGMENT_CONTACT = segment_contact
        self.ROI = roi
        self.SAMPLING = sampling
        self.COLORS = colors
        self.SECTIONS = sections
        self.ALPHAS = alphas
        self.findings: List[Dict] = []

    def finding(self, step: str, severity: str, what: str, **kw) -> None:
        rec = {"step": step, "severity": severity, "what": what}
        rec.update(kw)
        self.findings.append(rec)


def by_id(bodies: Sequence[cv.Body]) -> Dict[str, cv.Body]:
    return {b.id: b for b in bodies}


# --------------------------------------------------------------- primitives
def clip(shape: cq.Shape, roi: cq.Shape) -> Optional[cq.Shape]:
    """Intersection of a shape with a region of interest, or None if empty."""
    op = BRepAlgoAPI_Common(shape.wrapped, roi.wrapped)
    op.Build()
    if not op.IsDone():
        return None
    out = cq.Shape.cast(op.Shape())
    try:
        if cv._gprops_volume(out) <= 1e-9:
            return None
    except Exception:
        return None
    return out


def roi_box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, pnt=cq.Vector(x0, y0, z0))


def pair_measure(a: cq.Shape, b: cq.Shape) -> Tuple[float, float]:
    return cv.common_volume(a, b), cv.min_distance(a, b)


def scan(ctx: Ctx, bodies_at: List[cv.Body], allow_contact: set) -> Tuple[Dict, List[Dict]]:
    """Measure every body pair; report overlaps and undeclared approaches."""
    d = by_id(bodies_at)
    out, issues = {}, []
    for a, b in ctx.PAIRS:
        cvol, dist = pair_measure(d[a].shape, d[b].shape)
        out["%s|%s" % (a, b)] = {"common_volume_mm3": round(cvol, 9),
                                 "min_distance_mm": round(dist, 9)}
        if cvol > ctx.OVERLAP_TOL:
            issues.append({"kind": "UNDECLARED_VOLUMETRIC_OVERLAP", "pair": [a, b],
                           "common_volume_mm3": cvol})
        elif dist < ctx.CONTACT_TOL and (a, b) not in allow_contact:
            issues.append({"kind": "UNDECLARED_APPROACH", "pair": [a, b],
                           "min_distance_mm": dist})
    return out, issues


def build_roi(ctx: Ctx, spec) -> Tuple[str, cq.Shape, tuple, Optional[list]]:
    state, box = spec[0], spec[1]
    roi = roi_box(*box)
    cut = spec[2] if len(spec) > 2 else None
    if cut:
        _, cx, cy, cr = cut
        roi = roi.cut(cq.Solid.makeCylinder(
            cr, box[5] - box[4] + 2.0, pnt=cq.Vector(cx, cy, box[4] - 1.0),
            dir=cq.Vector(0, 0, 1)))
    return state, roi, box, (list(cut) if cut else None)


# ------------------------------------------------------------- steps 1 and 2
def step1_build(ctx: Ctx) -> Tuple[List[cv.Body], Dict]:
    t0 = time.time()
    bodies = ctx.M.build(ctx.P)
    rec = {"step": 1, "name": "build", "reference_id": ctx.ref_id,
           "parameters": ctx.P, "build_seconds": round(time.time() - t0, 3),
           "bodies": [{"body_id": b.id, "name": b.name, "material_class": b.material_class,
                       "role": b.role, "installed_as": b.installed_as, "notes": b.notes,
                       "volume_mm3": round(cv._gprops_volume(b.shape), 6),
                       "bbox_mm": {k: round(v, 6) for k, v in cv.bbox_of(b.shape).items()}}
                      for b in bodies]}
    cv.write_json(os.path.join(ctx.OUT, "build_report.json"), rec)
    return bodies, rec


def step2_validity(ctx: Ctx, bodies: List[cv.Body]) -> Dict:
    rows = []
    for b in bodies:
        vol = cv._gprops_volume(b.shape)
        ok = cv.is_valid(b.shape)
        solids = len(cq.Workplane("XY").add(b.shape).solids().vals())
        rows.append({"body_id": b.id, "brepcheck_analyzer_valid": ok,
                     "volume_mm3": round(vol, 6), "volume_positive": vol > 0.0,
                     "solid_count": solids, "single_connected_solid": solids == 1})
        if not ok:
            ctx.finding("2", "FAIL", "invalid solid", body=b.id)
        if vol <= 0:
            ctx.finding("2", "FAIL", "non-positive volume", body=b.id)
        if solids != 1:
            ctx.finding("2", "FAIL", "body is not a single connected solid",
                        body=b.id, solid_count=solids)
    rec = {"step": 2, "name": "solid validity",
           "method": "OCCT BRepCheck_Analyzer; BRepGProp volume; solid count",
           "status": "PASS" if all(r["brepcheck_analyzer_valid"] and r["volume_positive"]
                                   and r["single_connected_solid"] for r in rows) else "FAIL",
           "bodies": rows}
    cv.write_json(os.path.join(ctx.OUT, "solid_validity.json"), rec)
    return rec


# ------------------------------------------------------------------ step 3
def step3_reimport(ctx: Ctx, bodies: List[cv.Body]) -> Dict:
    rows = []
    for b in bodies:
        # BODY-REAR-PANEL -> rear_panel. Single-word ids are unaffected, so this
        # leaves every existing reference's export filenames unchanged.
        stem = b.id.lower().replace("body-", "").replace("-", "_")
        sp = os.path.join(ctx.HERE, "%s.step" % stem)
        bp = os.path.join(ctx.HERE, "%s.brep" % stem)
        n_step, n_brep = cv.export_step(b.shape, sp), cv.export_brep(b.shape, bp)
        v0 = cv._gprops_volume(b.shape)
        rs, rb = cv.import_step(sp), cv.import_brep(bp)
        vs, vb = cv._gprops_volume(rs), cv._gprops_volume(rb)
        row = {"body_id": b.id,
               "step_file": os.path.relpath(sp, ctx.HERE), "step_bytes": n_step,
               "step_sha256": cv.sha256_file(sp),
               "brep_file": os.path.relpath(bp, ctx.HERE), "brep_bytes": n_brep,
               "brep_sha256": cv.sha256_file(bp),
               "volume_as_built_mm3": round(v0, 6),
               "volume_step_roundtrip_mm3": round(vs, 6),
               "volume_brep_roundtrip_mm3": round(vb, 6),
               "step_delta_mm3": round(abs(vs - v0), 9),
               "brep_delta_mm3": round(abs(vb - v0), 9),
               "step_reimport_valid": cv.is_valid(rs),
               "brep_reimport_valid": cv.is_valid(rb)}
        # A STEP round trip re-fits geometry, so it is held to a relative
        # tolerance; BREP is the kernel's own format and must be exact.
        row["step_within_tolerance"] = row["step_delta_mm3"] <= max(1e-6, 1e-9 * v0)
        row["brep_within_tolerance"] = row["brep_delta_mm3"] <= 1e-6
        for k in ("step_reimport_valid", "brep_reimport_valid",
                  "step_within_tolerance", "brep_within_tolerance"):
            if not row[k]:
                ctx.finding("3", "FAIL", "re-import check failed: %s" % k, body=b.id)
        rows.append(row)

    asm = cv.compound(bodies)
    ap, abp = os.path.join(ctx.HERE, "model.step"), os.path.join(ctx.HERE, "model.brep")
    cv.export_step(asm, ap)
    cv.export_brep(asm, abp)
    ra = cv.import_brep(abp)
    rec = {"step": 3, "name": "STEP and BREP export with independent re-import",
           "note": ("Volume is compared, not file bytes. STEP output varies between "
                    "exporter builds, so a byte hash cannot be the reproducibility "
                    "criterion; the hashes are recorded for provenance only."),
           "bodies": rows,
           "assembly": {"step_file": "model.step", "step_bytes": os.path.getsize(ap),
                        "step_sha256": cv.sha256_file(ap),
                        "brep_file": "model.brep", "brep_bytes": os.path.getsize(abp),
                        "brep_sha256": cv.sha256_file(abp),
                        "brep_roundtrip_volume_mm3": round(cv._gprops_volume(ra), 6),
                        "as_built_volume_mm3": round(cv._gprops_volume(asm), 6)},
           "status": "PASS" if all(r["step_within_tolerance"] and r["brep_within_tolerance"]
                                   and r["step_reimport_valid"] and r["brep_reimport_valid"]
                                   for r in rows) else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "reimport_report.json"), rec)
    return rec


# ------------------------------------------------------------------ step 4
def step4_signature(ctx: Ctx, bodies: List[cv.Body], critical: Dict[str, float],
                    motion: Dict) -> Dict:
    def trsf_rows(loc: cq.Location) -> List[List[float]]:
        t = loc.wrapped.Transformation()
        return [[round(t.Value(r, c), 9) for c in range(1, 5)] for r in range(1, 4)]

    states = {s: {b.id: trsf_rows(ctx.M.pose(ctx.P, b.id, s)) for b in bodies}
              for s in ctx.M.STATES}
    sig = cv.geometry_signature(bodies, critical=critical, motion=motion, states=states)
    rebuilt = ctx.M.build(ctx.M.load_params())
    sig2 = cv.geometry_signature(rebuilt, critical=critical, motion=motion, states=states)
    cmp_ = cv.compare_signatures(sig, sig2)
    if not cmp_["within_tolerance"]:
        ctx.finding("4", "FAIL", "rebuild is not deterministic",
                    differences=cmp_["differences"])
    rec = {"step": 4, "name": "geometry signature and rebuild determinism",
           "signature": sig, "rebuild_comparison": cmp_,
           "criterion": ("Reproducibility is judged on the kernel's own mass properties, "
                         "not on exported bytes."),
           "status": "PASS" if cmp_["within_tolerance"] else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "geometry_signature.json"), rec)
    return rec


# ------------------------------------------------------------------ step 5
def step5_motion(ctx: Ctx, bodies: List[cv.Body], probes: List[Dict],
                 probe_meta: Dict) -> Dict:
    segs = []
    for seg in ctx.M.SEGMENTS:
        coarse, refine = ctx.SAMPLING[seg]
        ts = cv.sample_motion([], [], None, 0.0, 1.0, coarse, refine)
        allow = ctx.SEGMENT_CONTACT[seg]
        worst, worst_at = 0.0, None
        mins: Dict[str, Tuple[float, float]] = {}
        issues, samples = [], []
        t0 = time.time()
        for t in ts:
            conf = ctx.M.continuous_pose(bodies, ctx.P, seg, t)
            meas, iss = scan(ctx, conf, allow)
            for k, v in meas.items():
                if k not in mins or v["min_distance_mm"] < mins[k][0]:
                    mins[k] = (v["min_distance_mm"], t)
                if v["common_volume_mm3"] > worst:
                    worst, worst_at = v["common_volume_mm3"], (k, t)
            for i in iss:
                i["t"] = t
                issues.append(i)
            samples.append({"t": t, "pairs": meas})
        hard = [i for i in issues if i["kind"] == "UNDECLARED_VOLUMETRIC_OVERLAP"]
        for i in hard:
            ctx.finding("5", "FAIL", "undeclared volumetric overlap during motion",
                        segment=seg, pair=i["pair"],
                        common_volume_mm3=i["common_volume_mm3"], at_t=i["t"])
        segs.append({"segment_id": seg, "sample_count": len(ts),
                     "sampling": {"uniform": coarse, "refinement_windows": refine,
                                  "declared_not_adaptive": True},
                     "elapsed_seconds": round(time.time() - t0, 2),
                     "max_common_volume_mm3": round(worst, 9),
                     "max_common_volume_at": worst_at,
                     "min_distance_by_pair": {k: {"min_distance_mm": round(v[0], 9),
                                                  "at_t": v[1]}
                                              for k, v in sorted(mins.items())},
                     "undeclared_overlaps": hard,
                     "approaches_within_contact_tol":
                         [i for i in issues if i["kind"] == "UNDECLARED_APPROACH"],
                     "status": "PASS" if not hard else "FAIL",
                     "samples": samples})

    probe_meta = dict(probe_meta)
    probe_meta["samples"] = probes
    ok_probe = probe_meta.get("discriminates", True)
    if not ok_probe:
        ctx.finding("5", "FAIL", "terminal condition is not produced by its declared determinant")
    rec = {"step": 5, "name": "motion sampling",
           "method": ("Rigid transforms of as-built solids. At every sample all body pairs "
                      "are measured with BRepAlgoAPI_Common (volume) and "
                      "BRepExtrema_DistShapeShape (distance). Overlap is the volume, never "
                      "inferred from distance."),
           "evidence_is_sampled": ("This is dense sampling, not a proof of non-interference "
                                   "over the continuum. Reported as such."),
           "overlap_tol_mm3": ctx.OVERLAP_TOL, "contact_tol_mm": ctx.CONTACT_TOL,
           "segments": segs, "terminal_condition_causal_probe": probe_meta,
           "status": "PASS" if all(s["status"] == "PASS" for s in segs) and ok_probe else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "motion_report.json"), rec)
    return rec


# ------------------------------------------------------------------ step 6
def step6_interactions(ctx: Ctx, bodies: List[cv.Body],
                       external: Optional[Dict[str, Dict]] = None) -> Dict:
    decl = yaml.safe_load(open(os.path.join(ctx.HERE, "interactions.yaml")))
    confs = {s: by_id(ctx.M.configuration(bodies, ctx.P, s)) for s in ctx.M.STATES}
    external = external or {}
    rows = []
    for it in decl["interactions"]:
        iid, (a, b), typ = it["id"], it["bodies"], it["type"]
        # An interaction that exists only during an assembly step has no operating
        # state to measure it in. It is discharged by a cited probe instead, and
        # only if that probe actually reports a result.
        if iid in external:
            ext = dict(external[iid])
            ext.update({"interaction_id": iid, "bodies": [a, b], "type": typ,
                        "evaluated_in_state": "ASSEMBLY_ONLY"})
            if ext.get("status") != "PASS":
                ctx.finding("6", "FAIL", "assembly-only interaction not discharged",
                            interaction=iid)
            rows.append(ext)
            continue
        state, roi, box, cut = build_roi(ctx, ctx.ROI[iid])
        ca, cb = clip(confs[state][a].shape, roi), clip(confs[state][b].shape, roi)
        row = {"interaction_id": iid, "bodies": [a, b], "type": typ,
               "evaluated_in_state": state, "roi_box_mm": list(box),
               "roi_excludes": cut, "declared_nominal_mm": it.get("nominal_clearance_mm")}
        if ca is None or cb is None:
            row.update(status="NOT_EVALUABLE",
                       reason="one or both bodies have no material in the declared region")
            ctx.finding("6", "FAIL", "declared interaction region contains no geometry",
                        interaction=iid)
            rows.append(row)
            continue
        cvol, dist = pair_measure(ca, cb)
        row["measured_min_distance_mm"] = round(dist, 9)
        row["measured_common_volume_mm3"] = round(cvol, 9)
        nom = it.get("nominal_clearance_mm")
        if cvol > ctx.OVERLAP_TOL:
            row["status"] = "FAIL"
            row["reason"] = "volumetric overlap inside a declared region"
            ctx.finding("6", "FAIL", "overlap inside declared region", interaction=iid,
                        common_volume_mm3=cvol)
        elif typ == "DECLARED_CONTACT":
            ok = dist <= ctx.CONTACT_TOL
            row["status"] = "PASS" if ok else "FAIL"
            row["criterion"] = ("min distance <= contact_tol (%.3f) and no overlap"
                                % ctx.CONTACT_TOL)
            if not ok:
                ctx.finding("6", "FAIL", "declared contact is not in contact",
                            interaction=iid, min_distance_mm=dist)
        elif typ == "DECLARED_CLEARANCE":
            ok = abs(dist - nom) <= ctx.CONTACT_TOL if nom is not None else dist > 0
            row["status"] = "PASS" if ok else "FAIL"
            row["criterion"] = "|min distance - nominal| <= contact_tol, and no overlap"
            if not ok:
                ctx.finding("6", "FAIL", "declared clearance does not match nominal",
                            interaction=iid, measured=dist, nominal=nom)
        elif typ == "NOT_INTENDED_TO_INTERACT":
            ok = dist > ctx.CONTACT_TOL
            if nom is not None:
                ok = ok and abs(dist - nom) <= ctx.CONTACT_TOL
            row["status"] = "PASS" if ok else "FAIL"
            row["criterion"] = ("min distance > contact_tol, and where a nominal gap is "
                                "declared, |min distance - nominal| <= contact_tol")
            if not ok:
                ctx.finding("6", "FAIL", "declared non-interacting gap does not match nominal",
                            interaction=iid, measured=dist, nominal=nom)
        else:
            row["status"] = "UNSUPPORTED"
            row["reason"] = "no evaluator for interaction type %s" % typ
        rows.append(row)

    state_rows = []
    for s in ctx.M.STATES:
        meas, iss = scan(ctx, ctx.M.configuration(bodies, ctx.P, s),
                         set(ctx.CONTACT_BY_STATE[s]))
        for i in iss:
            sev = "FAIL" if i["kind"] == "UNDECLARED_VOLUMETRIC_OVERLAP" else "REVIEW"
            ctx.finding("6", sev, i["kind"], state=s, pair=i["pair"])
        state_rows.append({"state": s, "pairs": meas, "issues": iss,
                           "declared_contacts": {"|".join(k): v
                                                 for k, v in ctx.CONTACT_BY_STATE[s].items()}})

    bad = [r for r in rows if r["status"] != "PASS"]
    rec = {"step": 6, "name": "interaction classification and tolerance check",
           "evaluation_tolerance": {"contact_tol_mm": ctx.CONTACT_TOL,
                                    "overlap_tol_mm3": ctx.OVERLAP_TOL,
                                    "note": "evaluation tolerance, never a material allowance"},
           "method": ("Each declared interaction is measured inside a declared region of "
                      "interest, so a clearance is not masked by a contact elsewhere on the "
                      "same body pair. Whole-body pairs are then scanned per state."),
           "interactions": rows, "per_state_pair_scan": state_rows,
           "status": "PASS" if not bad and not any(r["issues"] for r in state_rows) else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "interaction_report.json"), rec)
    return rec


# ------------------------------------------------------------------ step 7
def step7_assembly(ctx: Ctx, bodies: List[cv.Body], samples: int = 60,
                   step_bodies: Optional[Dict[str, cv.Body]] = None) -> Dict:
    decl = yaml.safe_load(open(os.path.join(ctx.HERE, "assembly.yaml")))
    d = by_id(bodies)
    # A step may declare that the part is in a different CONFIGURATION while it is
    # being inserted - a snap feature deflected, for instance. The swept solid is
    # then that configuration, and the placed solid afterwards is the normal one.
    step_bodies = step_bodies or {}
    at: Dict[str, cq.Location] = {}
    placed: List[str] = []
    steps = []
    for st in decl["steps"]:
        bid, kind = st["place"], st.get("kind", "insertion")
        if kind == "base":
            at[bid] = cq.Location()
            placed.append(bid)
            steps.append({"step_id": st["id"], "body": bid, "kind": "base",
                          "status": "PASS", "note": "fixed reference body; nothing inserted"})
            continue
        if kind == "operation":
            # Already-installed body moved along a path step 5 validated. Not
            # swept again; the citation is recorded so the omission is visible.
            at[bid] = cq.Location()
            steps.append({"step_id": st["id"], "body": bid, "kind": "operation",
                          "validated_by": st.get("validated_by"),
                          "swept_here": False, "status": "PASS",
                          "note": "moves an installed body along a path validated in step 5"})
            continue
        off = st.get("at_offset") or [0.0, 0.0, 0.0]
        seat = cv.translation(tuple(off))
        direc, dist = st["direction"], float(st["approach_distance"])
        worst, worst_s, contacts = 0.0, None, {}
        others = [o for o in placed if o != bid]
        swept = step_bodies.get(st["id"], d[bid])
        for i in range(samples + 1):
            s = dist * (1.0 - i / float(samples))
            loc = cv.translation((-direc[0] * s, -direc[1] * s, -direc[2] * s)) * seat
            moving = swept.moved(loc) if i < samples else d[bid].moved(loc)
            for other in others:
                cvol = cv.common_volume(moving.shape, d[other].moved(at[other]).shape)
                if cvol > worst:
                    worst, worst_s = cvol, s
                if i == samples:
                    contacts[other] = round(cv.min_distance(
                        moving.shape, d[other].moved(at[other]).shape), 9)
        ok = worst <= ctx.OVERLAP_TOL
        if not ok:
            ctx.finding("7", "FAIL", "insertion path passes through placed material",
                        assembly_step=st["id"], body=bid,
                        common_volume_mm3=worst, at_offset_mm=worst_s)
        at[bid] = seat
        if bid not in placed:
            placed.append(bid)
        steps.append({"step_id": st["id"], "body": bid, "kind": "linear insertion",
                      "swept_configuration": ("declared alternate configuration"
                                              if st["id"] in step_bodies else "as-built"),
                      "seated_configuration": "as-built",
                      "direction": direc, "approach_distance_mm": dist,
                      "seated_at_offset_mm": off, "samples": samples + 1,
                      "placed_before": others,
                      "max_common_volume_mm3": round(worst, 9),
                      "max_common_volume_at_offset_mm": worst_s,
                      "seated_min_distance_to_mm": contacts,
                      "status": "PASS" if ok else "FAIL"})

    rec = {"step": 7, "name": "assembly process check",
           "method": ("Each discrete part is swept along its declared straight-line "
                      "insertion direction, from its approach distance to its seated "
                      "offset, and the boolean common with every already-placed body is "
                      "measured at each sample."),
           "steps": steps,
           "establishes": "an unobstructed insertion ordering exists",
           "does_not_establish": ("insertion force, ease of assembly or process "
                                  "suitability; those remain NOT_VERIFIED"),
           "status": "PASS" if all(s["status"] == "PASS" for s in steps) else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "assembly_report.json"), rec)
    return rec


# ------------------------------------------------------------------ step 9
def step9_render(ctx: Ctx, bodies: List[cv.Body]) -> Dict:
    sdir = os.path.join(ctx.HERE, "screenshots")
    written = []
    for s in ctx.M.STATES:
        conf = ctx.M.configuration(bodies, ctx.P, s)
        written += cv.render_views(conf, sdir, s.lower(), cv.ISO, colors=ctx.COLORS,
                                   alphas=ctx.ALPHAS)
    for s, axis, at_, label in ctx.SECTIONS:
        conf = ctx.M.configuration(bodies, ctx.P, s)
        written += cv.render_views(conf, sdir, label, cv.ISO[:2], colors=ctx.COLORS,
                                   section=(axis, at_), alphas=ctx.ALPHAS)
    rec = {"step": 9, "name": "render",
           "images": [os.path.relpath(w, ctx.HERE) for w in written],
           "count": len(written),
           "role": ("review aids only. No geometric claim in this pilot rests on an image; "
                    "every such claim is backed by a kernel measurement."),
           "human_review": "HUMAN_REVIEW_PENDING",
           "status": "PASS" if written else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "render_report.json"), rec)
    return rec


# ----------------------------------------------------------------- self-test
def run_selftest(ctx: Ctx, cases: List[Dict]) -> Dict:
    missed = [c["control_id"] for c in cases if not c["detected"]]
    for cid in missed:
        ctx.finding("selftest", "FAIL", "a negative control was not detected", control=cid)
    rec = {"name": "checker self-test",
           "purpose": ("Establishes that the checks in this chain can fail. Each control "
                       "injects a defect in memory and passes only if the check reports it. "
                       "No perturbed model is exported."),
           "controls": cases, "controls_run": len(cases),
           "controls_detected": len(cases) - len(missed), "undetected": missed,
           "status": "PASS" if not missed else "FAIL"}
    cv.write_json(os.path.join(ctx.OUT, "checker_selftest.json"), rec)
    return rec


def write_summary(ctx: Ctx, steps: Dict[str, str], sig_sha: str, seconds: float,
                  fast: bool, meaning: str) -> Dict:
    summary = {"reference_id": ctx.ref_id, "run_seconds": round(seconds, 1),
               "fast_mode": fast, "geometry_signature_sha256": sig_sha,
               "steps": steps, "findings": ctx.findings,
               "overall": "FAIL" if any(v == "FAIL" for v in steps.values()) else "PASS",
               "what_this_means": meaning, "human_review": "HUMAN_REVIEW_PENDING"}
    cv.write_json(os.path.join(ctx.OUT, "SUMMARY.json"), summary)
    return summary
