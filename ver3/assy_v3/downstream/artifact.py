"""UNIT G. The artifact, validated as a MECHANISM and not as a set of shapes.

"The kernel returned a shape" proves that a shape exists. This module asks what
a person opening the CAD would ask: are the parts the design named all here,
each a valid solid; does each feature's construction exist; do the bodies pose
together as the joints say; do they interfere where the design said they must
not, and touch where it said they must; does the required motion carry through
without collision; are the reserved regions respected; do the exchange files
exist and read back. Every answer is measured on the actual solids, in derived
poses, with s04's own contact policy and s04's own motion sampling - and every
question that cannot be asked is reported NOT_EVALUABLE by name, never passed.
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
    correspondence: Dict[str, List[str]] = field(default_factory=dict)   # feature -> statements
    states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    transitions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    exports: Dict[str, Any] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)
    basis: Optional[str] = None

    @property
    def workable(self) -> bool:
        """No evaluable finding contradicts the artifact. NOT a claim that every
        question was asked: `unasked` lists what could not be evaluated."""
        return not blocking(self.findings)

    @property
    def unasked(self) -> List[Finding]:
        return [f for f in self.findings if not f.evaluable]

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "basis": self.basis,
                "expected_bodies": list(self.expected_bodies),
                "built_bodies": list(self.built_bodies),
                "body_validity": dict(self.body_validity),
                "correspondence": {k: list(v) for k, v in sorted(self.correspondence.items())},
                "states": dict(self.states), "transitions": dict(self.transitions),
                "exports": dict(self.exports),
                "findings": [f.as_record() for f in self.findings],
                "workable": self.workable}


def _rows(state, branch, family):
    return [r for r in sorted(state.standing(family), key=lambda r: r["entity_id"])
            if not branch or canonical_io._in_branch(r, branch)]


def _pair_policy(interfaces) -> Dict[frozenset, Tuple[str, List[str]]]:
    """Body pair -> (TOUCHES | CLEAR | UNDECLARED, interface ids), by s04's one reader."""
    from ..stages.s04_envelope_and_motion import interface_expectation

    out: Dict[frozenset, Tuple[str, List[str]]] = {}
    for i in interfaces:
        bodies = [b for b in (i.get("bodies") or []) if isinstance(b, str)]
        if len(bodies) < 2:
            continue
        key = frozenset(bodies[:2])
        expectation = interface_expectation(i)
        prior = out.get(key)
        ids = (prior[1] if prior else []) + [i["entity_id"]]
        # An interference fit is the one contact that may share volume.
        fit = str(i.get("interaction_kind", "")).upper() == "INTERFERENCE_FIT"
        label = "FIT" if fit or (prior and prior[0] == "FIT") else expectation
        out[key] = (label, ids)
    return out


def _pairs(K, posed: Dict[str, Any], policy, where: str, findings: List[Finding],
           kind_if_blocked: str) -> Dict[str, Dict[str, float]]:
    """Every body pair's shared volume and distance, judged by the policy."""
    out: Dict[str, Dict[str, float]] = {}
    ids = sorted(posed)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            geom = compiler.pair_geometry(K, posed[a], posed[b])
            out["%s|%s" % (a, b)] = geom
            expectation, ifaces = policy.get(frozenset((a, b)), ("UNDECLARED", []))
            shared, distance = geom["shared_volume"], geom["distance"]
            if shared > compiler.INTERFERENCE_VOLUME_TOLERANCE and expectation != "FIT":
                findings.append(Finding(
                    kind_if_blocked, "s05", (a, b) + tuple(ifaces),
                    "%s: bodies %s and %s share %.6g mm3 of volume; the design declares %s "
                    "between them" % (where, a, b, shared,
                                      ("an interface of kind %s" % expectation) if ifaces
                                      else "no interaction"),
                    evidence={"shared_volume": shared, "distance": distance}))
            elif expectation == "TOUCHES" and distance > compiler.CONTACT_DISTANCE_TOLERANCE:
                findings.append(Finding(
                    MATING_NOT_REALIZED, "s05", (a, b) + tuple(ifaces),
                    "%s: bodies %s and %s are %.6g mm apart; interface %s expects them to touch"
                    % (where, a, b, distance, ", ".join(ifaces)),
                    evidence={"shared_volume": shared, "distance": distance}))
            elif expectation == "CLEAR" and distance <= compiler.CONTACT_DISTANCE_TOLERANCE:
                findings.append(Finding(
                    MATING_NOT_REALIZED, "s05", (a, b) + tuple(ifaces),
                    "%s: bodies %s and %s touch; interface %s declares a clearance"
                    % (where, a, b, ", ".join(ifaces)),
                    evidence={"shared_volume": shared, "distance": distance}))
    return out


def _region_boxes(state, branch, scale) -> Tuple[List[Tuple[str, Any]], Optional[Finding]]:
    """Occupancy-excluding regions as kernel-unit boxes, or why not."""
    from ..stages.s04_envelope_and_motion import excludes_occupancy, unknown_region_role

    regions = [r for r in _rows(state, branch, "FunctionalRegion")
               if not unknown_region_role(r.get("role")) and excludes_occupancy(r.get("role"))
               and isinstance((r.get("volume") or {}).get("centre"), list)]
    if not regions:
        return [], None
    absolute = (scale or {}).get("absolute") or {}
    per_unit = absolute.get("per_unit")
    if (scale or {}).get("basis") != "ABSOLUTE" or absolute.get("unit") != ir.KERNEL_LENGTH_UNIT \
            or not isinstance(per_unit, (int, float)) or isinstance(per_unit, bool):
        return [], Finding(NOT_EVALUABLE, "s04", tuple(r["entity_id"] for r in regions),
                           "reserved regions are stated in a %s basis; occupancy in %s needs "
                           "an ABSOLUTE scale in that unit, and none is invented"
                           % ((scale or {}).get("basis") or "missing", ir.KERNEL_LENGTH_UNIT),
                           evaluable=False)
    out = []
    for r in regions:
        c, h = r["volume"]["centre"], r["volume"]["half_extent"]
        lo = [(c[i] - h[i]) * per_unit for i in range(3)]
        hi = [(c[i] + h[i]) * per_unit for i in range(3)]
        out.append((r["entity_id"], (lo, hi)))
    return out, None


def _region_findings(K, posed, boxes, anchor, where, findings, base_bbox_centre):
    """Posed bodies against reserved regions, anchored at the base body's
    arrangement envelope centre (the one world datum s04 committed for it)."""
    if not boxes or anchor is None:
        return
    shift = [anchor[i] - base_bbox_centre[i] for i in range(3)]
    for rid, (lo, hi) in boxes:
        box = K["BRepPrimAPI_MakeBox"](
            K["gp_Pnt"](lo[0] - shift[0], lo[1] - shift[1], lo[2] - shift[2]),
            K["gp_Pnt"](hi[0] - shift[0], hi[1] - shift[1], hi[2] - shift[2])).Shape()
        for bid, shape in sorted(posed.items()):
            geom = compiler.pair_geometry(K, shape, box)
            if geom["shared_volume"] > compiler.INTERFERENCE_VOLUME_TOLERANCE:
                findings.append(Finding(
                    FEATURE_OUTSIDE_REGION, "s05", (bid, rid),
                    "%s: body %s occupies %.6g mm3 of reserved region %s"
                    % (where, bid, geom["shared_volume"], rid),
                    evidence={"shared_volume": geom["shared_volume"]}))


def _mapping(value) -> Dict[str, Any]:
    """A record field that must be a mapping, read as one or as nothing stated."""
    return dict(value) if isinstance(value, dict) else {}


def _listing(value) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _bbox_centre(K, shape):
    box = K["Bnd_Box"]()
    K["BRepBndLib"].Add_s(shape, box)
    x0, y0, z0, x1, y1, z1 = box.Get()
    return [(x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0]


def validate(state, branch: Optional[str], result: compiler.CompileResult,
             out_dir: Optional[str] = None) -> ArtifactReport:
    """Everything the artifact can be asked, on the actual solids."""
    report = ArtifactReport(branch=branch)
    K = compiler.kernel()
    bodies = _rows(state, branch, "Body")
    joints = _rows(state, branch, "Joint")
    groups = _rows(state, branch, "RigidGroup")
    interfaces = _rows(state, branch, "Interface")
    scales = _rows(state, branch, "ReferenceScale")
    scale = scales[0] if len(scales) == 1 else None
    report.basis = (scale or {}).get("basis")
    report.expected_bodies = [b["entity_id"] for b in bodies]
    compiled = {b.body_id: b for b in result.bodies}
    report.built_bodies = sorted(compiled)
    for bid, b in sorted(compiled.items()):
        report.body_validity[bid] = {"valid": b.is_valid, "volume": b.volume,
                                     "solid_count": b.solid_count,
                                     "single_connected_solid": b.single_connected_solid}
    for bid in sorted(set(report.expected_bodies) - set(compiled)):
        report.findings.append(Finding(EMBODIMENT_INCOMPLETE, "s05", (bid,),
                                       "body %s is named by the design and was not built" % bid))
    program = canonical_io.read_program(state, branch)
    for stmt in program.statements:
        if stmt.feature:
            report.correspondence.setdefault(stmt.feature, []).append(stmt.entity_id)

    values = canonical_io.resolved_values(state, branch)
    features = _rows(state, branch, "Feature")
    frames, realization_findings = kinematics.realizations(features, values)
    report.findings += realization_findings
    policy = _pair_policy(interfaces)
    region_boxes, region_note = _region_boxes(state, branch, scale)
    if region_note:
        report.findings.append(region_note)
    envelopes = {e.get("body"): e for e in _rows(state, branch, "Envelope")}
    per_unit = ((scale or {}).get("absolute") or {}).get("per_unit")

    def anchor_for(base):
        env = envelopes.get(base)
        if not (region_boxes and isinstance(env, dict) and isinstance(per_unit, (int, float))):
            return None
        extent = env.get("extent")
        centre = extent.get("centre") if isinstance(extent, dict) else None
        if not (isinstance(centre, list) and len(centre) == 3
                and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in centre)):
            return None
        return [c * per_unit for c in centre]

    def pose_and_judge(coordinates_basis, where, kind_if_blocked):
        coords, notes = kinematics.coordinates_in_kernel_units(joints, coordinates_basis, scale)
        law = kinematics.derive_poses(joints, groups, frames, coords, report.expected_bodies)
        posed = compiler.posed_shapes(K, result.bodies, law.poses)
        findings = list(notes) + list(law.findings)
        pairs = _pairs(K, posed, policy, where, findings, kind_if_blocked)
        if law.base in posed:
            _region_findings(K, posed, region_boxes, anchor_for(law.base), where, findings,
                             _bbox_centre(K, posed[law.base]))
        return law, posed, pairs, findings

    exports: Dict[str, Any] = {"assembly_step_per_state": {}, "stl_per_body": {}}
    for st in _rows(state, branch, "State"):
        sid = st["entity_id"]
        law, posed, pairs, findings = pose_and_judge(_mapping(st.get("joint_coordinates")),
                                                     "state %s" % sid, BODY_INTERFERENCE)
        report.states[sid] = {"poses": law.as_record(), "pairs": pairs,
                              "posed_bodies": sorted(posed),
                              "findings": [f.as_record() for f in findings]}
        report.findings += findings
        if out_dir and posed and law.complete:
            os.makedirs(out_dir, exist_ok=True)
            exports["assembly_step_per_state"][sid] = compiler.export_assembly(
                K, posed, os.path.join(out_dir, "assembly_%s.step" % sid))
    states = {s["entity_id"]: s for s in _rows(state, branch, "State")}
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
        rows = []
        t_findings: List[Finding] = []
        for index, coords in enumerate(samples):
            law, posed, pairs, findings = pose_and_judge(
                coords, "transition %s sample %d/%d" % (tid, index + 1, len(samples)),
                TRAVEL_BLOCKED)
            rows.append({"coordinates": coords, "posed_bodies": sorted(posed), "pairs": pairs,
                         "findings": [f.as_record() for f in findings]})
            t_findings += findings
        report.transitions[tid] = {"sampling_declaration": declaration, "samples": rows,
                                   "blocked": any(f.kind == TRAVEL_BLOCKED for f in t_findings)}
        report.findings += t_findings
    if out_dir:
        for bid, body in sorted(compiled.items()):
            exports["stl_per_body"][bid] = compiler.export_stl(
                K, body.shape, os.path.join(out_dir, "%s.stl" % bid))
    report.exports = exports
    # one finding per distinct (kind, subjects, detail) - a pair that interferes in
    # nine samples is one contradiction with nine pieces of evidence
    seen, unique = set(), []
    for f in report.findings:
        key = (f.kind, f.subjects, f.detail)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    report.findings = unique
    return report
