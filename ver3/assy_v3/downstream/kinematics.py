"""UNIT G. Frames and the pose law, DERIVED from s04's one spatial authority.

THE AUTHORITY. s04's arrangement frame is the world. In it s04 committed the
joint frames (Joint.frame_origin, with s03's axis_direction), the body
envelopes and the functional regions, all in the ReferenceScale basis. Every
body frame COINCIDES with that frame at zero joint coordinates. s05 places a
feature RELATIVE to one of those commitments - a datum - by an offset in the
kernel length unit; s06 settles the offsets and dimensions; this module turns
datum + offset + scale into the feature's frame, and located joint frames +
joint coordinates into every body's pose. Nothing here is authored: withdraw
the datum or the scale and the frame is gone, by name.

THE SCALE. Kernel units per basis unit: an ABSOLUTE ReferenceScale's per_unit
(stated in the kernel unit), or the settled value of the one Parameter the
scale names (`ReferenceScale.scale_parameter`). Without either, nothing in the
kernel unit can be placed against the arrangement: the frame is not derivable,
the check is NOT_EVALUABLE, and no scale is invented.

THE POSE LAW. With the joint frames located in the world at zero coordinates,
the pose of a body is the composition, along the joint tree from the base, of
each joint's motion about its own located axis: a rotation about the line
through frame_origin x scale along axis_direction by q degrees (REVOLUTE), a
translation along it by q x scale (PRISMATIC), the identity (FIXED). Other
joint classes are reported, never approximated. The base is the root of the
joint tree, deterministically; a body the tree does not reach has no derivable
pose, which is a finding rather than a default.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import ir
from .findings import NOT_EVALUABLE, POSE_NOT_DERIVABLE, UNSUPPORTED_OPERATION, Finding

Vec = Tuple[float, float, float]
Mat = Tuple[Vec, Vec, Vec]

REVOLUTE = "REVOLUTE"
PRISMATIC = "PRISMATIC"
FIXED = "FIXED"
COMPLIANT = "COMPLIANT"
POSABLE = (REVOLUTE, PRISMATIC, FIXED)


def _mul(a: Mat, b: Mat) -> Mat:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))  # type: ignore
                 for i in range(3))


def _apply(a: Mat, v: Vec) -> Vec:
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))  # type: ignore


def _transpose(a: Mat) -> Mat:
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))  # type: ignore


IDENTITY: Mat = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


@dataclass(frozen=True)
class Frame:
    """A rigid transform: p_world = r . p_local + t."""

    r: Mat = IDENTITY
    t: Vec = (0.0, 0.0, 0.0)

    def compose(self, other: "Frame") -> "Frame":
        """self . other: apply `other` first, then self."""
        return Frame(_mul(self.r, other.r),
                     tuple(a + b for a, b in zip(_apply(self.r, other.t), self.t)))  # type: ignore

    def inverse(self) -> "Frame":
        rt = _transpose(self.r)
        return Frame(rt, tuple(-c for c in _apply(rt, self.t)))  # type: ignore

    def apply(self, p: Vec) -> Vec:
        return tuple(a + b for a, b in zip(_apply(self.r, p), self.t))  # type: ignore

    @staticmethod
    def from_axis(origin: Vec, axis: str) -> "Frame":
        """The feature frame at `origin` with Z along the named axis and X along
        the canonical perpendicular (`ir.frame_axes`)."""
        x, y, z = ir.frame_axes(axis)
        return Frame(((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2])),
                     tuple(float(c) for c in origin))  # type: ignore

    @staticmethod
    def rotation_about(point: Vec, direction: Vec, degrees: float) -> "Frame":
        """Rotation by `degrees` about the line through `point` along `direction`
        (a unit vector): the motion of a revolute joint located in the world."""
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        ux, uy, uz = direction
        r: Mat = ((c + ux * ux * (1 - c), ux * uy * (1 - c) - uz * s, ux * uz * (1 - c) + uy * s),
                  (uy * ux * (1 - c) + uz * s, c + uy * uy * (1 - c), uy * uz * (1 - c) - ux * s),
                  (uz * ux * (1 - c) - uy * s, uz * uy * (1 - c) + ux * s, c + uz * uz * (1 - c)))
        rp = _apply(r, point)
        return Frame(r, tuple(p - q for p, q in zip(point, rp)))  # type: ignore

    @staticmethod
    def translation(vector: Vec) -> "Frame":
        return Frame(t=tuple(float(c) for c in vector))  # type: ignore

    def as_record(self) -> Dict[str, Any]:
        return {"rotation": [[round(v, 12) for v in row] for row in self.r],
                "translation": [round(v, 12) for v in self.t]}


# ==========================================================================
# The scale authority
# ==========================================================================
SCALE_ROLE = "SCALE"


def scale_authority(scale: Optional[Dict[str, Any]], values: Dict[str, float],
                    parameters: Sequence[Any] = ()) -> Tuple[Optional[float], str]:
    """(kernel units per basis unit, how it is known) or (None, why not).

    `parameters`: the branch's ParameterDecl records (or dicts with `entity_id`
    and `role`); the one with role SCALE, settled, is the RELATIVE basis's
    authority. s04's ReferenceScale is never written for it.
    """
    if not scale:
        return None, "no ReferenceScale stands for the branch"
    if scale.get("basis") == "ABSOLUTE":
        absolute = scale.get("absolute") or {}
        per_unit = absolute.get("per_unit")
        if absolute.get("unit") != ir.KERNEL_LENGTH_UNIT:
            return None, ("the ABSOLUTE scale is stated in %r, not the kernel unit %s, and no "
                          "conversion is attempted" % (absolute.get("unit"), ir.KERNEL_LENGTH_UNIT))
        if not isinstance(per_unit, (int, float)) or isinstance(per_unit, bool) or per_unit <= 0:
            return None, "the ABSOLUTE scale states no positive per_unit"
        return float(per_unit), "ABSOLUTE ReferenceScale %s" % scale.get("entity_id")
    declared = []
    for p in parameters:
        role = getattr(p, "role", None) if not isinstance(p, dict) else p.get("role")
        pid = getattr(p, "entity_id", None) if not isinstance(p, dict) else p.get("entity_id")
        if str(role or "").upper() == SCALE_ROLE:
            declared.append(pid)
    if len(declared) > 1:
        return None, "%d parameters declare role SCALE (%s); the scale is one number" % (
            len(declared), ", ".join(sorted(declared)))
    if declared:
        pid = declared[0]
        if pid in values:
            if values[pid] <= 0:
                return None, "scale parameter %s settled to %g, which is not a scale" % (pid, values[pid])
            return float(values[pid]), "settled scale parameter %s" % pid
        return None, "the basis is RELATIVE and its scale parameter %s has no settled value" % pid
    return None, ("the basis is RELATIVE and no parameter declares role SCALE; nothing in %s can be "
                  "placed against the arrangement and no scale is invented" % ir.KERNEL_LENGTH_UNIT)


# ==========================================================================
# Feature frames from datums
# ==========================================================================
def _point(node: Any) -> Optional[Vec]:
    if isinstance(node, list) and len(node) == 3 and all(
            isinstance(c, (int, float)) and not isinstance(c, bool) for c in node):
        return (float(node[0]), float(node[1]), float(node[2]))
    return None


def datum_point(datum: str, rows: Dict[str, List[Dict[str, Any]]]
                ) -> Tuple[Optional[Vec], Optional[str], str, Optional[str]]:
    """(point in the basis, the joint's axis token if a joint, family, why-not)."""
    for fam in ("Joint", "Envelope", "FunctionalRegion"):
        for rec in rows.get(fam) or []:
            if rec.get("entity_id") != datum:
                continue
            if fam == "Joint":
                point = _point(rec.get("frame_origin"))
                axis = rec.get("axis_direction")
                if point is None:
                    return None, None, fam, ("joint %s has no located frame origin; s04 has not "
                                             "placed it" % datum)
                # a joint that points nowhere (FIXED, axis NONE) is a location only
                return point, (str(axis).strip().upper() if ir.axis_vector(axis) else None), fam, None
            container = rec.get("extent") if fam == "Envelope" else rec.get("volume")
            point = _point((container or {}).get("centre")) if isinstance(container, dict) else None
            if point is None:
                return None, None, fam, "%s %s carries no centre" % (fam, datum)
            return point, None, fam, None
    return None, None, None, "%s is no standing joint, envelope or region" % datum


def feature_frames(features: Sequence[ir.FeatureSpec], rows: Dict[str, List[Dict[str, Any]]],
                   per_unit: Optional[float], values: Dict[str, float]
                   ) -> Tuple[Dict[str, Frame], List[Finding]]:
    """Every feature's frame in the world (kernel units), from its datum, the
    scale and the settled offsets. A feature placed against another feature
    takes that feature's frame as its datum point (and its axis, unless it
    states one). Anything unresolvable is a finding, never a default."""
    from .compiler import resolve

    frames: Dict[str, Frame] = {}
    findings: List[Finding] = []
    by_id = {f.entity_id: f for f in features}
    visiting: set = set()

    def build(fid: str) -> Optional[Frame]:
        if fid in frames:
            return frames[fid]
        spec = by_id.get(fid)
        if spec is None or fid in visiting:
            return None
        visiting.add(fid)
        placement = spec.placement
        try:
            offset = tuple(resolve(e, values) for e in placement.offset)
        except ir.IRError as exc:
            findings.append(Finding(POSE_NOT_DERIVABLE, "s06", (fid,),
                                    "feature %s offset does not resolve: %s" % (fid, exc)))
            return None
        if placement.datum in by_id:
            base = build(placement.datum)
            if base is None:
                findings.append(Finding(POSE_NOT_DERIVABLE, "s05", (fid, placement.datum),
                                        "feature %s is placed against feature %s, whose frame "
                                        "is not derivable" % (fid, placement.datum)))
                return None
            axis = placement.axis or _axis_of(base)
            origin = tuple(b + o for b, o in zip(base.t, offset))
        else:
            point, joint_axis, family, why = datum_point(placement.datum, rows)
            if point is None:
                findings.append(Finding(POSE_NOT_DERIVABLE, "s04" if family else "s05",
                                        (fid, placement.datum), "feature %s: %s" % (fid, why)))
                return None
            if per_unit is None:
                findings.append(Finding(NOT_EVALUABLE, "s04", (fid, placement.datum),
                                        "feature %s is placed against %s and the arrangement has "
                                        "no scale in %s" % (fid, placement.datum, ir.KERNEL_LENGTH_UNIT),
                                        evaluable=False))
                return None
            # THE FEATURE'S OWN AXIS FIRST, wherever it states one: a datum
            # locates, and orientation is the feature's to say. A joint datum
            # supplies the joint's axis when the feature states none - a bore
            # at a hinge is on the hinge line - and an envelope or region, an
            # axis-aligned box in the arrangement frame, supplies +Z.
            axis = placement.axis or (joint_axis if family == "Joint" else "+Z")
            origin = tuple(p * per_unit + o for p, o in zip(point, offset))
        if axis is None:
            findings.append(Finding(POSE_NOT_DERIVABLE, "s05", (fid,),
                                    "feature %s names no axis and its datum carries none" % fid))
            return None
        frame = Frame.from_axis(origin, axis)
        frames[fid] = frame
        return frame

    for f in sorted(features, key=lambda x: x.entity_id):
        build(f.entity_id)
    return frames, findings


def _axis_of(frame: Frame) -> str:
    z = (frame.r[0][2], frame.r[1][2], frame.r[2][2])
    for name, vec in ir.AXIS_VECTORS.items():
        if all(abs(a - b) < 1e-9 for a, b in zip(vec, z)):
            return name
    return "+Z"


# ==========================================================================
# The pose law
# ==========================================================================
@dataclass
class PoseLaw:
    base: Optional[str] = None
    poses: Dict[str, Frame] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)
    edges: List[Tuple[str, str, str, str]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not any(f.kind in (POSE_NOT_DERIVABLE, UNSUPPORTED_OPERATION) for f in self.findings)

    def as_record(self) -> Dict[str, Any]:
        return {"base": self.base,
                "poses": {b: f.as_record() for b, f in sorted(self.poses.items())},
                "edges": [list(e) for e in self.edges],
                "findings": [f.as_record() for f in self.findings]}


def body_of_group(groups: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    return {g["entity_id"]: g.get("body") for g in groups}


def joint_edges(joints, groups):
    by_group = body_of_group(groups)
    out = []
    for j in sorted(joints, key=lambda x: x["entity_id"]):
        if str(j.get("joint_type", "")).upper() == COMPLIANT:
            continue
        out.append((j, by_group.get(j.get("parent_group")), by_group.get(j.get("child_group"))))
    return out


def base_body(edges) -> Optional[str]:
    parents = {p for _j, p, _c in edges if p}
    children = {c for _j, _p, c in edges if c}
    roots = sorted(parents - children)
    if roots:
        return roots[0]
    everything = sorted(parents | children)
    return everything[0] if everything else None


def joint_motion(joint: Dict[str, Any], q: Optional[float], per_unit: Optional[float]
                 ) -> Tuple[Optional[Frame], Optional[Finding]]:
    """M_J(q) about the joint's LOCATED axis, in the world at zero coordinates."""
    jid = joint.get("entity_id")
    kind = str(joint.get("joint_type", "")).upper()
    if kind == FIXED:
        return Frame(), None
    if kind not in POSABLE:
        return None, Finding(UNSUPPORTED_OPERATION, "s07", (jid,),
                             "joint %s is %s; the derivation poses REVOLUTE, PRISMATIC and FIXED "
                             "joints and reports every other class" % (jid, kind or "untyped"))
    direction = ir.axis_vector(joint.get("axis_direction"))
    point = _point(joint.get("frame_origin"))
    if direction is None or point is None:
        return None, Finding(POSE_NOT_DERIVABLE, "s04", (jid,),
                             "joint %s has no located frame (origin %r, axis %r); s04 has not "
                             "placed it" % (jid, joint.get("frame_origin"), joint.get("axis_direction")))
    if per_unit is None:
        return None, Finding(NOT_EVALUABLE, "s04", (jid,),
                             "joint %s is located in a basis with no scale in %s"
                             % (jid, ir.KERNEL_LENGTH_UNIT), evaluable=False)
    located = tuple(c * per_unit for c in point)
    if kind == REVOLUTE:
        return Frame.rotation_about(located, direction, float(q or 0.0)), None
    return Frame.translation(tuple(d * float(q or 0.0) for d in direction)), None


def derive_poses(joints, groups, coordinates: Dict[str, float], per_unit: Optional[float],
                 bodies: Sequence[str]) -> PoseLaw:
    """Every body's pose for one set of joint coordinates (kernel units:
    degrees for a revolute joint, kernel length for a prismatic one)."""
    law = PoseLaw()
    edges = joint_edges(joints, groups)
    law.base = base_body(edges)
    if law.base is None:
        for b in sorted(bodies):
            law.poses[b] = Frame()
        if len(bodies) > 1:
            law.findings.append(Finding(POSE_NOT_DERIVABLE, "s03", tuple(sorted(bodies)),
                                        "no joint relates these bodies; their relative pose is "
                                        "not derivable"))
        return law
    law.poses[law.base] = Frame()
    pending = list(edges)
    progressed = True
    while pending and progressed:
        progressed = False
        for edge in list(pending):
            joint, parent, child = edge
            jid = joint["entity_id"]
            if parent in law.poses and child in law.poses:
                pending.remove(edge)
                continue
            if parent not in law.poses and child not in law.poses:
                continue
            known, unknown = (parent, child) if parent in law.poses else (child, parent)
            motion, finding = joint_motion(joint, coordinates.get(jid), per_unit)
            if motion is None:
                law.findings.append(finding)
                pending.remove(edge)
                continue
            # parent/child orient the relative relation only: walking from the
            # child applies the inverse motion.
            step = motion if known == parent else motion.inverse()
            law.poses[unknown] = law.poses[known].compose(step)
            law.edges.append((jid, parent or "", child or "", str(joint.get("joint_type", ""))))
            pending.remove(edge)
            progressed = True
    for b in sorted(bodies):
        if b not in law.poses:
            law.findings.append(Finding(POSE_NOT_DERIVABLE, "s03", (b,),
                                        "body %s is reached by no joint from the base %s"
                                        % (b, law.base)))
    return law


def coordinates_in_kernel_units(joints, coordinates: Any, per_unit: Optional[float]
                                ) -> Tuple[Dict[str, float], List[Finding]]:
    """s04's joint coordinates as the kernel reads them: degrees stay degrees; a
    prismatic length in the basis becomes kernel units through the scale, or is
    NOT_EVALUABLE by name."""
    coordinates = coordinates if isinstance(coordinates, dict) else {}
    out: Dict[str, float] = {}
    findings: List[Finding] = []
    for j in joints:
        jid = j["entity_id"]
        if jid not in coordinates:
            continue
        q = coordinates[jid]
        if isinstance(q, bool) or not isinstance(q, (int, float)):
            findings.append(Finding(NOT_EVALUABLE, "s04", (jid,),
                                    "joint coordinate of %s is %r, not a number" % (jid, q),
                                    evaluable=False))
            continue
        if str(j.get("joint_type", "")).upper() == PRISMATIC:
            if per_unit is None:
                findings.append(Finding(NOT_EVALUABLE, "s04", (jid,),
                                        "prismatic coordinate of %s is a basis length and the "
                                        "arrangement has no scale in %s" % (jid, ir.KERNEL_LENGTH_UNIT),
                                        evaluable=False))
                continue
            out[jid] = float(q) * per_unit
        else:
            out[jid] = float(q)
    return out, findings


def motion_samples(from_coordinates: Dict[str, float], to_coordinates: Dict[str, float],
                   changed: Sequence[str]) -> Tuple[List[Dict[str, float]], Dict[str, Any]]:
    """The joint coordinates along a transition, sampled AS S04 SAMPLES."""
    from ..stages.s04_envelope_and_motion import SAMPLES, sample

    changed = [c for c in changed if c in from_coordinates or c in to_coordinates]
    if not changed:
        return [dict(from_coordinates)], {"kind": "UNIFORM", "adaptive": False, "samples": 1,
                                          "interior_samples": 0, "method": "NO_COORDINATE_CHANGED"}
    tracks = {c: sample(float(from_coordinates.get(c, 0.0)), float(to_coordinates.get(c, 0.0)),
                        SAMPLES) for c in changed}
    n = len(next(iter(tracks.values())))
    out = []
    for i in range(n):
        coords = dict(from_coordinates)
        for c in changed:
            coords[c] = tracks[c][i]
        out.append(coords)
    return out, {"kind": "UNIFORM", "adaptive": False, "samples": n,
                 "interior_samples": max(n - 2, 0),
                 "method": "LOCKSTEP_LINEAR_IN_JOINT_COORDINATES"}
