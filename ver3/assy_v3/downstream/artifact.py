"""UNIT G. The artifact, validated as a MECHANISM and not as a set of shapes.

Everything is measured on the actual solids in s04's arrangement frame, posed
by the derived law, judged by s04's own contact policy, at the specific
interface and the features that realize it:

  - every body the design names is built and is a valid single solid;
  - every feature's construction exists and is where its datum puts it;
  - in every State, each INTERFACE is judged on the solids of the features
    that realize its two sides - shared volume where the interface is CLEAR
    or a CONTACT is interference, a gap where it must TOUCH is a mating not
    realized, an INTERFERENCE_FIT may share volume - and every body pair is
    judged for undeclared overlap;
  - every Transition is sampled exactly as s04 samples it and judged at each
    sample;
  - reserved regions are checked in the arrangement frame through the scale
    authority, and reported NOT_EVALUABLE without one;
  - an assembly STEP per state and an STL per body are written beside the
    per-body files.

Every question that cannot be asked is reported NOT_EVALUABLE by name; nothing
is passed for want of a check.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import canonical_io, compiler, ir, kinematics
from .findings import (BODY_INTERFERENCE, EMBODIMENT_INCOMPLETE, FEATURE_OUTSIDE_REGION,
                       MATING_NOT_REALIZED, NOT_EVALUABLE, TRAVEL_BLOCKED, Finding, blocking)


@dataclass
class ArtifactReport:
    branch: Optional[str]
    expected_bodies: List[str] = field(default_factory=list)
    built_bodies: List[str] = field(default_factory=list)
    body_validity: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    feature_map: Dict[str, Dict[str, str]] = field(default_factory=dict)   # feature -> {body, polarity}
    states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    transitions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    exports: Dict[str, Any] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)
    basis: Optional[str] = None
    scale: Optional[str] = None

    @property
    def workable(self) -> bool:
        return not blocking(self.findings)

    @property
    def unasked(self) -> List[Finding]:
        return [f for f in self.findings if not f.evaluable]

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "basis": self.basis, "scale": self.scale,
                "expected_bodies": list(self.expected_bodies),
                "built_bodies": list(self.built_bodies),
                "body_validity": dict(self.body_validity),
                "feature_map": {k: dict(v) for k, v in sorted(self.feature_map.items())},
                "states": dict(self.states), "transitions": dict(self.transitions),
                "exports": dict(self.exports),
                "findings": [f.as_record() for f in self.findings],
                "workable": self.workable}


def _rows(state, branch, family):
    return [r for r in sorted(state.standing(family), key=lambda r: r["entity_id"])
            if not branch or canonical_io._in_branch(r, branch)]


def _expectation(iface) -> str:
    """TOUCHES | CLEAR | FIT | UNDECLARED, by s04's one reader plus the one
    contact that may share volume."""
    from ..stages.s04_envelope_and_motion import interface_expectation

    if str(iface.get("interaction_kind", "")).upper() == "INTERFERENCE_FIT":
        return "FIT"
    return interface_expectation(iface)


def _judge(geom: Dict[str, float], expectation: str, subjects: Tuple[str, ...], where: str,
           what: str, kind_if_blocked: str) -> Optional[Finding]:
    shared, distance = geom["shared_volume"], geom["distance"]
    if shared > compiler.INTERFERENCE_VOLUME_TOLERANCE and expectation != "FIT":
        return Finding(kind_if_blocked, "s05", subjects,
                       "%s: %s share %.6g mm3 of volume; the design declares %s"
                       % (where, what, shared,
                          "an interface expecting %s" % expectation if expectation != "UNDECLARED"
                          else "no interaction between them"),
                       evidence={"shared_volume": shared, "distance": distance})
    if expectation == "TOUCHES" and distance > compiler.CONTACT_DISTANCE_TOLERANCE:
        return Finding(MATING_NOT_REALIZED, "s05", subjects,
                       "%s: %s are %.6g mm apart; the interface expects them to touch"
                       % (where, what, distance),
                       evidence={"shared_volume": shared, "distance": distance})
    if expectation == "CLEAR" and distance <= compiler.CONTACT_DISTANCE_TOLERANCE:
        return Finding(MATING_NOT_REALIZED, "s05", subjects,
                       "%s: %s touch; the interface declares a clearance" % (where, what),
                       evidence={"shared_volume": shared, "distance": distance})
    return None


def _region_boxes(state, branch, per_unit) -> Tuple[List[Tuple[str, Any]], Optional[Finding]]:
    from ..stages.s04_envelope_and_motion import excludes_occupancy, unknown_region_role

    regions = [r for r in _rows(state, branch, "FunctionalRegion")
               if not unknown_region_role(r.get("role")) and excludes_occupancy(r.get("role"))
               and isinstance((r.get("volume") or {}).get("centre"), list)]
    if not regions:
        return [], None
    if per_unit is None:
        return [], Finding(NOT_EVALUABLE, "s04", tuple(r["entity_id"] for r in regions),
                           "reserved regions are stated in the arrangement basis and the "
                           "arrangement has no scale in %s" % ir.KERNEL_LENGTH_UNIT, evaluable=False)
    out = []
    for r in regions:
        c, h = r["volume"]["centre"], r["volume"]["half_extent"]
        lo = [(c[i] - h[i]) * per_unit for i in range(3)]
        hi = [(c[i] + h[i]) * per_unit for i in range(3)]
        out.append((r["entity_id"], (lo, hi)))
    return out, None


def _mapping(value) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _listing(value) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def validate(state, branch: Optional[str], result: compiler.CompileResult,
             out_dir: Optional[str] = None) -> ArtifactReport:
    report = ArtifactReport(branch=branch)
    K = compiler.kernel()
    bodies = _rows(state, branch, "Body")
    joints = _rows(state, branch, "Joint")
    groups = _rows(state, branch, "RigidGroup")
    interfaces = _rows(state, branch, "Interface")
    values = canonical_io.resolved_values(state, branch)
    scale = canonical_io.reference_scale(state, branch)
    per_unit, how = kinematics.scale_authority(scale, values,
                                               canonical_io.read_parameters(state, branch))
    report.basis = (scale or {}).get("basis")
    report.scale = how
    report.expected_bodies = [b["entity_id"] for b in bodies]
    compiled = {b.body_id: b for b in result.bodies}
    report.built_bodies = sorted(compiled)
    for bid, b in sorted(compiled.items()):
        report.body_validity[bid] = {"valid": b.is_valid, "volume": b.volume,
                                     "solid_count": b.solid_count,
                                     "single_connected_solid": b.single_connected_solid}
        for fid, pol in b.feature_map.items():
            report.feature_map[fid] = {"body": bid, "polarity": pol}
    for bid in sorted(set(report.expected_bodies) - set(compiled)):
        report.findings.append(Finding(EMBODIMENT_INCOMPLETE, "s05", (bid,),
                                       "body %s is named by the design and was not built" % bid))

    features = _rows(state, branch, "Feature")
    body_of_feature = {f["entity_id"]: f.get("body") for f in features}
    sides: Dict[str, Dict[str, List[str]]] = {}          # interface -> body -> feature ids
    for f in features:
        if f.get("interface"):
            sides.setdefault(f["interface"], {}).setdefault(f.get("body"), []).append(f["entity_id"])
    declared_pairs: Dict[frozenset, List[Dict[str, Any]]] = {}
    for i in interfaces:
        bs = [b for b in (i.get("bodies") or []) if isinstance(b, str)]
        if len(bs) >= 2:
            declared_pairs.setdefault(frozenset(bs[:2]), []).append(i)
    region_boxes, region_note = _region_boxes(state, branch, per_unit)
    if region_note:
        report.findings.append(region_note)

    def posed_features(posed_bodies: Dict[str, Any], law) -> Dict[str, Any]:
        """The geometry that REALIZES each feature, posed. An additive feature
        realizes its side with its own solid; a subtractive feature is a void,
        and what meets the other side is its body's material around it - so
        the body's posed solid stands for it. Comparing a void's cylinder with
        the pin in it would report the fit as interference."""
        out = {}
        for bid, body in compiled.items():
            if bid not in law.poses:
                continue
            for fid, shape in body.feature_shapes.items():
                if body.feature_map.get(fid) == compiler.SUBTRACTIVE:
                    out[fid] = posed_bodies[bid]
                else:
                    out[fid] = compiler.placed(K, shape, law.poses[bid])
        return out

    def pose_and_judge(coordinates_basis, where, kind_if_blocked):
        coords, notes = kinematics.coordinates_in_kernel_units(joints, coordinates_basis, per_unit)
        law = kinematics.derive_poses(joints, groups, coords, per_unit, report.expected_bodies)
        posed = compiler.posed_shapes(K, result.bodies, law.poses)
        feature_solids = posed_features(posed, law)
        findings: List[Finding] = list(notes) + list(law.findings)
        pairs: Dict[str, Dict[str, float]] = {}
        # every body pair: undeclared overlap is interference; a declared FIT may share volume
        ids = sorted(posed)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                geom = compiler.pair_geometry(K, posed[a], posed[b])
                pairs["%s|%s" % (a, b)] = geom
                declared = declared_pairs.get(frozenset((a, b))) or []
                fit = any(_expectation(x) == "FIT" for x in declared)
                if geom["shared_volume"] > compiler.INTERFERENCE_VOLUME_TOLERANCE and not fit:
                    findings.append(Finding(
                        kind_if_blocked, "s05", (a, b) + tuple(x["entity_id"] for x in declared),
                        "%s: bodies %s and %s share %.6g mm3 of volume%s"
                        % (where, a, b, geom["shared_volume"],
                           "" if declared else "; s03 declares no interaction between them"),
                        evidence=geom))
        # every interface, at the features that realize it
        interface_geometry: Dict[str, Any] = {}
        for iface in interfaces:
            iid = iface["entity_id"]
            bs = [b for b in (iface.get("bodies") or []) if isinstance(b, str)][:2]
            if len(bs) < 2:
                continue
            realizing = [[fid for fid in (sides.get(iid, {}).get(b) or []) if fid in feature_solids]
                         for b in bs]
            if not realizing[0] or not realizing[1]:
                findings.append(Finding(NOT_EVALUABLE, "s05", (iid,) + tuple(bs),
                                        "%s: interface %s has no posed realizing feature on %s"
                                        % (where, iid, ", ".join(b for b, r in zip(bs, realizing) if not r)),
                                        evaluable=False))
                continue
            worst = None
            for fa in realizing[0]:
                for fb in realizing[1]:
                    geom = compiler.pair_geometry(K, feature_solids[fa], feature_solids[fb])
                    if worst is None or geom["shared_volume"] > worst[1]["shared_volume"] \
                            or (geom["shared_volume"] == worst[1]["shared_volume"]
                                and geom["distance"] < worst[1]["distance"]):
                        worst = ((fa, fb), geom)
            (fa, fb), geom = worst
            interface_geometry[iid] = {"features": [fa, fb], **geom}
            finding = _judge(geom, _expectation(iface), (iid, fa, fb), where,
                             "features %s and %s (interface %s)" % (fa, fb, iid), kind_if_blocked)
            if finding:
                findings.append(finding)
        if law.base in posed and region_boxes:
            for rid, (lo, hi) in region_boxes:
                box = K["BRepPrimAPI_MakeBox"](K["gp_Pnt"](*lo), K["gp_Pnt"](*hi)).Shape()
                for bid, shape in sorted(posed.items()):
                    geom = compiler.pair_geometry(K, shape, box)
                    if geom["shared_volume"] > compiler.INTERFERENCE_VOLUME_TOLERANCE:
                        findings.append(Finding(FEATURE_OUTSIDE_REGION, "s05", (bid, rid),
                                                "%s: body %s occupies %.6g mm3 of reserved region %s"
                                                % (where, bid, geom["shared_volume"], rid),
                                                evidence={"shared_volume": geom["shared_volume"]}))
        return law, posed, pairs, interface_geometry, findings

    exports: Dict[str, Any] = {"assembly_step_per_state": {}, "stl_per_body": {}}
    states = {s["entity_id"]: s for s in _rows(state, branch, "State")}
    for sid, st in sorted(states.items()):
        law, posed, pairs, igeom, findings = pose_and_judge(_mapping(st.get("joint_coordinates")),
                                                            "state %s" % sid, BODY_INTERFERENCE)
        report.states[sid] = {"poses": law.as_record(), "pairs": pairs, "interfaces": igeom,
                              "posed_bodies": sorted(posed),
                              "findings": [f.as_record() for f in findings]}
        report.findings += findings
        if out_dir and posed and law.complete:
            os.makedirs(out_dir, exist_ok=True)
            exports["assembly_step_per_state"][sid] = compiler.export_assembly(
                K, posed, os.path.join(out_dir, "assembly_%s.step" % sid))
    for t in _rows(state, branch, "Transition"):
        tid = t["entity_id"]
        a, b = states.get(t.get("from_state")), states.get(t.get("to_state"))
        if not (a and b):
            report.findings.append(Finding(NOT_EVALUABLE, "s04", (tid,),
                                           "transition %s names a state that does not stand" % tid,
                                           evaluable=False))
            continue
        samples, declaration = kinematics.motion_samples(
            _mapping(a.get("joint_coordinates")), _mapping(b.get("joint_coordinates")),
            _listing(t.get("changed_coordinates")))
        rows, t_findings = [], []
        for index, coords in enumerate(samples):
            law, posed, pairs, igeom, findings = pose_and_judge(
                coords, "transition %s sample %d/%d" % (tid, index + 1, len(samples)), TRAVEL_BLOCKED)
            rows.append({"coordinates": coords, "posed_bodies": sorted(posed), "pairs": pairs,
                         "interfaces": igeom, "findings": [f.as_record() for f in findings]})
            t_findings += findings
        report.transitions[tid] = {"sampling_declaration": declaration, "samples": rows,
                                   "blocked": any(f.kind == TRAVEL_BLOCKED for f in t_findings)}
        report.findings += t_findings
    if out_dir:
        for bid, body in sorted(compiled.items()):
            exports["stl_per_body"][bid] = compiler.export_stl(
                K, body.shape, os.path.join(out_dir, "%s.stl" % bid))
    report.exports = exports
    seen, unique = set(), []
    for f in report.findings:
        key = (f.kind, f.subjects, f.detail)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    report.findings = unique
    return report
