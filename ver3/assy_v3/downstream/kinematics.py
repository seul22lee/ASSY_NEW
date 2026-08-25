"""UNIT G. The pose law, DERIVED - never authored.

S04's contract: "with located joint frames and joint coordinates, every pose is
DERIVABLE"; the design-state contract lists the pose law under
`derived_not_stored`. Nothing in the repository derived it, so bodies compiled
in frames nobody could relate, and no assembly, interference or motion question
could be asked of a solid. This module is that derivation and only that.

WHAT IT READS. s03's Joint (type, parent/child group, axis token), s03's
RigidGroup (group -> body), s05's Feature.placement on the features that
realize each joint on each body (`Feature.joint`), s06's settled values (to
resolve the placement expressions), and s04's State.joint_coordinates.

THE FRAME CONVENTION (stated in downstream/ir with the placement grammar):
every body frame is parallel to the arrangement frame at zero joint
coordinates; a joint's realization frame in a body has Z along the placement
axis and origin at the placement origin. The relative pose of a child body
across a joint is then

    T_child = T_parent . F_parent(J) . M_J(q) . F_child(J)^-1

with M_J a rotation about Z by q degrees (revolute), a translation along Z by q
in the kernel length unit (prismatic), or the identity (FIXED). Other joint
classes are reported unsupported; nothing is approximated. The base body is
the root of the joint tree - the body that is a parent and never a child -
chosen deterministically, and it sits at the identity. A body the tree does not
reach is a body with no derivable pose, which is a finding, not a default.

A prismatic coordinate is stated in s04's basis. It becomes a length only
through an ABSOLUTE ReferenceScale in the kernel unit; a RELATIVE basis leaves
the motion NOT_EVALUABLE, and no scale is invented.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import ir
from .findings import (ASSEMBLY_BLOCKED, MATING_AXES_INCONSISTENT, NOT_EVALUABLE,
                       POSE_NOT_DERIVABLE, UNSUPPORTED_OPERATION, Finding)

Vec = Tuple[float, float, float]
Mat = Tuple[Vec, Vec, Vec]

#: Joint classes the derivation can pose. Everything else is reported.
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


@dataclass(frozen=True)
class Frame:
    """A rigid transform: p_world = r . p_local + t."""

    r: Mat = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
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
        """The feature frame of a placement: columns are the canonical (x, y, z)."""
        x, y, z = ir.frame_axes(axis)
        return Frame(((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2])),
                     tuple(float(c) for c in origin))  # type: ignore

    @staticmethod
    def rotation_z(degrees: float) -> "Frame":
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        return Frame(((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)))

    @staticmethod
    def translation_z(length: float) -> "Frame":
        return Frame(t=(0.0, 0.0, float(length)))

    def as_record(self) -> Dict[str, Any]:
        return {"rotation": [[round(v, 12) for v in row] for row in self.r],
                "translation": [round(v, 12) for v in self.t]}


@dataclass(frozen=True)
class Realization:
    """One joint's frame in one body, as the placed feature states it."""

    joint: str
    body: str
    feature: str
    axis: str
    frame: Frame




@dataclass
class PoseLaw:
    """What the derivation concluded for one set of joint coordinates."""

    base: Optional[str] = None
    poses: Dict[str, Frame] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)
    #: (joint, parent body, child body, joint_type) in the order they were walked.
    edges: List[Tuple[str, str, str, str]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not any(f.kind in (POSE_NOT_DERIVABLE, ASSEMBLY_BLOCKED, UNSUPPORTED_OPERATION,
                                  MATING_AXES_INCONSISTENT) for f in self.findings)

    def as_record(self) -> Dict[str, Any]:
        return {"base": self.base,
                "poses": {b: f.as_record() for b, f in sorted(self.poses.items())},
                "edges": [list(e) for e in self.edges],
                "findings": [f.as_record() for f in self.findings]}


def body_of_group(groups: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    return {g["entity_id"]: g.get("body") for g in groups}


def joint_edges(joints: Sequence[Dict[str, Any]], groups: Sequence[Dict[str, Any]]
                ) -> List[Tuple[Dict[str, Any], Optional[str], Optional[str]]]:
    """(joint, parent body, child body) for every joint relating two bodies.

    COMPLIANT joints are internal to one body (the ontology's rule) and pose
    nothing; they are left out here and never reported as unsupported.
    """
    by_group = body_of_group(groups)
    out = []
    for j in sorted(joints, key=lambda x: x["entity_id"]):
        if str(j.get("joint_type", "")).upper() == COMPLIANT:
            continue
        out.append((j, by_group.get(j.get("parent_group")), by_group.get(j.get("child_group"))))
    return out


def base_body(edges) -> Optional[str]:
    """The root of the joint tree: a parent that is never a child, first by id.

    Deterministic and derived; the base is a presentation choice for the
    assembly (every relative pose is the same whichever body sits still) and is
    never an engineering decision.
    """
    parents = {p for _j, p, _c in edges if p}
    children = {c for _j, _p, c in edges if c}
    roots = sorted(parents - children)
    if roots:
        return roots[0]
    everything = sorted(parents | children)
    return everything[0] if everything else None


def realizations(features: Sequence[Dict[str, Any]], values: Dict[str, float]
                 ) -> Tuple[Dict[Tuple[str, str], Realization], List[Finding]]:
    """The joint frames s05 placed, resolved with s06's values.

    A placement whose origin cannot be resolved is not a frame: the joint it
    realizes has no derivable pose, and that is reported with the parameter
    that is missing rather than filled with a number.
    """
    from .compiler import resolve

    out: Dict[Tuple[str, str], Realization] = {}
    findings: List[Finding] = []
    for f in sorted(features, key=lambda x: x["entity_id"]):
        joint, node = f.get("joint"), f.get("placement")
        if not joint or node is None:
            continue
        try:
            placement = ir.Placement.parse(node, "feature %s placement" % f["entity_id"])
            origin = tuple(resolve(e, values) for e in placement.origin)
        except ir.IRError as exc:
            findings.append(Finding(POSE_NOT_DERIVABLE, "s05", (f["entity_id"], joint),
                                    "feature %s realizes %s and its placement does not "
                                    "resolve: %s" % (f["entity_id"], joint, exc)))
            continue
        key = (joint, f.get("body"))
        if key in out:
            findings.append(Finding(MATING_AXES_INCONSISTENT, "s05",
                                    (out[key].feature, f["entity_id"], joint),
                                    "two features (%s, %s) both realize joint %s on body %s"
                                    % (out[key].feature, f["entity_id"], joint, f.get("body"))))
            continue
        out[key] = Realization(joint=joint, body=f.get("body"), feature=f["entity_id"],
                               axis=placement.axis, frame=Frame.from_axis(origin, placement.axis))
    return out, findings


def joint_motion(joint: Dict[str, Any], q: Optional[float]) -> Tuple[Optional[Frame], Optional[str]]:
    """M_J(q), or (None, why) when the class is unsupported."""
    kind = str(joint.get("joint_type", "")).upper()
    if kind == FIXED:
        return Frame(), None
    if kind == REVOLUTE:
        return Frame.rotation_z(float(q or 0.0)), None
    if kind == PRISMATIC:
        return Frame.translation_z(float(q or 0.0)), None
    return None, ("joint %s is %s; the derivation poses REVOLUTE, PRISMATIC and FIXED "
                  "joints and reports every other class" % (joint.get("entity_id"), kind or "untyped"))


def derive_poses(joints: Sequence[Dict[str, Any]], groups: Sequence[Dict[str, Any]],
                 frames: Dict[Tuple[str, str], Realization],
                 coordinates: Dict[str, float], bodies: Sequence[str]) -> PoseLaw:
    """Every body's pose for one set of joint coordinates (kernel units).

    `coordinates` are already in kernel units: degrees for a revolute joint,
    millimetres for a prismatic one. Converting s04's basis to those is the
    caller's question (`coordinates_in_kernel_units`), because it needs the
    ReferenceScale and can fail closed.
    """
    law = PoseLaw()
    edges = joint_edges(joints, groups)
    law.base = base_body(edges)
    if law.base is None:
        for b in sorted(bodies):
            law.poses[b] = Frame()
        if len(bodies) > 1:
            law.findings.append(Finding(POSE_NOT_DERIVABLE, "s03", tuple(sorted(bodies)),
                                        "no joint relates these bodies; their relative pose "
                                        "is not derivable"))
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
            # Walk in whichever direction reaches the placed body: parent/child
            # orient the RELATIVE relation only (the Joint contract's own rule).
            known, unknown = (parent, child) if parent in law.poses else (child, parent)
            f_known = frames.get((jid, known))
            f_unknown = frames.get((jid, unknown))
            missing = [b for b, fr in ((known, f_known), (unknown, f_unknown)) if fr is None]
            if missing:
                law.findings.append(Finding(
                    POSE_NOT_DERIVABLE, "s05", (jid,) + tuple(missing),
                    "joint %s has no placed feature realizing its axis on %s; the pose of "
                    "%s cannot be derived" % (jid, ", ".join(missing), unknown)))
                pending.remove(edge)
                continue
            declared = str(joint.get("axis_direction", "")).strip().upper()
            for realization in (f_known, f_unknown):
                if realization.axis != declared:
                    law.findings.append(Finding(
                        MATING_AXES_INCONSISTENT, "s05", (jid, realization.feature),
                        "feature %s realizes joint %s along %s; the joint's declared axis is %s"
                        % (realization.feature, jid, realization.axis, declared or "none")))
            motion, why = joint_motion(joint, coordinates.get(jid))
            if motion is None:
                law.findings.append(Finding(UNSUPPORTED_OPERATION, "s07", (jid,), why))
                pending.remove(edge)
                continue
            if known == parent:
                relative = f_known.frame.compose(motion).compose(f_unknown.frame.inverse())
            else:
                relative = f_known.frame.compose(motion.inverse()).compose(f_unknown.frame.inverse())
            law.poses[unknown] = law.poses[known].compose(relative)
            law.edges.append((jid, parent or "", child or "", str(joint.get("joint_type", ""))))
            pending.remove(edge)
            progressed = True
    for b in sorted(bodies):
        if b not in law.poses:
            law.findings.append(Finding(POSE_NOT_DERIVABLE, "s03", (b,),
                                        "body %s is reached by no joint from the base %s"
                                        % (b, law.base)))
    return law


def coordinates_in_kernel_units(joints: Sequence[Dict[str, Any]],
                                coordinates: Dict[str, Any],
                                scale: Optional[Dict[str, Any]]
                                ) -> Tuple[Dict[str, float], List[Finding]]:
    """s04's joint coordinates as the kernel reads them.

    A revolute coordinate is already degrees (s04's own convention). A prismatic
    one is a length in s04's basis and becomes millimetres only through an
    ABSOLUTE scale stated in the kernel unit; otherwise the joint's motion is
    NOT_EVALUABLE and left out, by name.
    """
    out: Dict[str, float] = {}
    findings: List[Finding] = []
    coordinates = coordinates if isinstance(coordinates, dict) else {}
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
            absolute = (scale or {}).get("absolute") or {}
            per_unit = absolute.get("per_unit")
            if (scale or {}).get("basis") != "ABSOLUTE" or absolute.get("unit") != ir.KERNEL_LENGTH_UNIT \
                    or not isinstance(per_unit, (int, float)) or isinstance(per_unit, bool):
                findings.append(Finding(
                    NOT_EVALUABLE, "s04", (jid,),
                    "prismatic coordinate of %s is stated in a %s basis; a length in %s needs "
                    "an ABSOLUTE scale in that unit, and none is invented"
                    % (jid, (scale or {}).get("basis") or "missing", ir.KERNEL_LENGTH_UNIT),
                    evaluable=False))
                continue
            out[jid] = float(q) * float(per_unit)
        else:
            out[jid] = float(q)
    return out, findings


def motion_samples(from_coordinates: Dict[str, float], to_coordinates: Dict[str, float],
                   changed: Sequence[str]) -> Tuple[List[Dict[str, float]], Dict[str, Any]]:
    """The joint coordinates along a transition, sampled AS S04 SAMPLES.

    s04's `sample`/`SAMPLES` are the one non-adaptive sampling rule in the
    design; reusing them keeps the solid-level evidence on the same poses the
    box-level evidence was computed on. The declaration says what was done.
    """
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
