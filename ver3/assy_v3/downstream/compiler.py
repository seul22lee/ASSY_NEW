"""s07 - compile faithfully, report validity, export, and fail loudly.

llm_role NONE. Engineering authority NONE. S07_CONTRACT is explicit that this
stage "owns NO engineering decision. It owns only facts about what compiled."

WHAT IT REFUSES TO DO, AND WHY THAT IS THE FEATURE

A CAD kernel always wants a number. When a dimension is missing the tempting
thing is to supply a default, and R-24 records what that cost: a compiler that
chooses a form, a placement, an axis or a missing dimension is making the
engineering decision nobody recorded, invisibly, inside a solid. So a missing
value here is a compile failure citing the originating ConstructionStatement and
its dependency cone (S07-C6), and no geometry is emitted at all.

INPUT EXCLUSIVITY (INV-006)

Only the construction program and the resolved parameters. Not the pose law -
world placement is derivable downstream from located joint frames and joint
coordinates, so it is not an input to compilation. Bodies compile in their own
frames; nothing here places a body in an assembly.

THE AUTHORITATIVE ARTIFACT

The signature is taken from the NATIVE shapes before any export. Native B-rep is
authoritative; STEP is an exchange artifact that is round-trip checked and never
the source of truth. A visualization mesh, if one is ever produced, is a
derivative of a derivative and is authoritative for nothing.

The kernel is OpenCascade through OCP, imported lazily so that a machine without
it can still import this module, read the contracts and run everything that does
not build geometry.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .ir import AXIS_VECTORS, Expr, FeatureSpec, IRError, Step
from .kinematics import Frame

#: S07-C3. Absolute, in mm3, and declared by the contract rather than tuned.
BREP_VOLUME_TOLERANCE = 1e-6
#: S07-C4. Relative, because STEP is a text exchange format and its round-trip
#: error scales with the magnitude of the shape.
STEP_RELATIVE_TOLERANCE = 1e-9


class KernelUnavailable(RuntimeError):
    """The CAD kernel is not installed. Never silently degraded into a skip."""


def kernel():
    """The OpenCascade entry points, imported on first use.

    Lazy so that `import ver3.assy_v3.downstream.compiler` works in an
    environment with no kernel - which is what lets the contract, IR and solver
    tests run anywhere while the compile tests require the real thing.
    """
    try:
        from OCP.BRep import BRep_Builder
        from OCP.BRepAlgoAPI import (BRepAlgoAPI_Common, BRepAlgoAPI_Cut,
                                     BRepAlgoAPI_Fuse)
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.BRepCheck import BRepCheck_Analyzer
        from OCP.BRepGProp import BRepGProp
        from OCP.BRepPrimAPI import (BRepPrimAPI_MakeBox,
                                     BRepPrimAPI_MakeCylinder,
                                     BRepPrimAPI_MakeSphere)
        from OCP.BRepTools import BRepTools
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.StlAPI import StlAPI_Writer
        from OCP.TopoDS import TopoDS_Compound
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import BRepBndLib
        from OCP.GProp import GProp_GProps
        from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec
        from OCP.STEPControl import (STEPControl_AsIs, STEPControl_Reader,
                                     STEPControl_Writer)
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS_Shape
    except Exception as exc:                                       # noqa: BLE001
        raise KernelUnavailable(
            "the OpenCascade kernel (OCP) is not importable: %s. s07 cannot "
            "compile without it, and this is reported rather than skipped." % exc)
    return locals()


@dataclass
class CompiledBody:
    body_id: str
    volume: float
    is_valid: bool
    solid_count: int
    single_connected_solid: bool
    bbox: Tuple[float, float, float, float, float, float]
    #: UNIT G. feature id -> polarity, for every feature composed into this body,
    #: and each feature's own solid, so an interface can be judged at the feature
    #: that realizes it rather than at the whole body.
    feature_map: Dict[str, str] = field(default_factory=dict)
    feature_shapes: Dict[str, Any] = field(default_factory=dict)
    shape: Any = None

    def as_record(self) -> Dict[str, Any]:
        return {"body_id": self.body_id, "volume": self.volume,
                "is_valid": self.is_valid, "solid_count": self.solid_count,
                "single_connected_solid": self.single_connected_solid,
                "bbox": list(self.bbox),
                "feature_map": dict(sorted(self.feature_map.items()))}


@dataclass
class CompileResult:
    ok: bool
    bodies: List[CompiledBody] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    #: UNIT G. On failure: the feature and its step that did not build.
    failed_feature: Optional[str] = None
    failed_step: Optional[str] = None
    signature: Optional[Dict[str, Any]] = None
    exports: Dict[str, Any] = field(default_factory=dict)
    roundtrip: Dict[str, Any] = field(default_factory=dict)
    #: UNIT G. What the artifact validator concluded about the assembled,
    #: posed, moved solids - filled by `downstream.artifact`, never here.
    artifact: Optional[Dict[str, Any]] = None

    def as_record(self) -> Dict[str, Any]:
        return {"ok": self.ok,
                "bodies": [b.as_record() for b in self.bodies],
                "problems": list(self.problems),
                "failed_feature": self.failed_feature, "failed_step": self.failed_step,
                "signature": self.signature, "exports": dict(self.exports),
                "roundtrip": dict(self.roundtrip), "artifact": self.artifact}


def resolve(expr: Expr, values: Dict[str, float]) -> float:
    """A statement parameter to a number, or a failure naming what is missing.

    This is the exact point R-24 warns about. There is no default branch.
    """
    if expr.ref is not None:
        if expr.ref not in values:
            raise IRError("parameter %s has no resolved value; s06 did not "
                          "settle it and s07 does not choose one" % expr.ref)
        return float(values[expr.ref])
    if expr.const is not None:
        return float(expr.const)
    args = [resolve(a, values) for a in expr.args]
    if expr.op == "+":
        return sum(args)
    if expr.op == "-":
        if len(args) == 1:
            return -args[0]                      # unary minus: negation (Unit G)
        out = args[0]
        for a in args[1:]:
            out -= a
        return out
    if expr.op == "*":
        out = args[0]
        for a in args[1:]:
            out *= a
        return out
    if expr.op == "/":
        out = args[0]
        for a in args[1:]:
            if a == 0.0:
                raise IRError("division by zero while resolving a parameter")
            out /= a
        return out
    raise IRError("unknown operator %r" % expr.op)


def trsf_of(K, frame: Frame):
    """A derived Frame as the kernel's rigid transform. Nothing is re-decided."""
    trsf = K["gp_Trsf"]()
    r, t = frame.r, frame.t
    trsf.SetValues(r[0][0], r[0][1], r[0][2], t[0],
                   r[1][0], r[1][1], r[1][2], t[1],
                   r[2][0], r[2][1], r[2][2], t[2])
    return trsf


def placed(K, shape, frame: Optional[Frame]):
    if frame is None:
        return shape
    return K["BRepBuilderAPI_Transform"](shape, trsf_of(K, frame), True).Shape()


def trsf_of(K, frame: Frame):
    """A derived Frame as the kernel's rigid transform. Nothing is re-decided."""
    trsf = K["gp_Trsf"]()
    r, t = frame.r, frame.t
    trsf.SetValues(r[0][0], r[0][1], r[0][2], t[0],
                   r[1][0], r[1][1], r[1][2], t[1],
                   r[2][0], r[2][1], r[2][2], t[2])
    return trsf


def placed(K, shape, frame: Optional[Frame]):
    if frame is None:
        return shape
    return K["BRepBuilderAPI_Transform"](shape, trsf_of(K, frame), True).Shape()


def _build_step(K, step: Step, values: Dict[str, float], built: Dict[str, Any]):
    """One opcode to one shape, in the feature's own frame. No opcode consults
    anything but its own inputs."""
    p = {k: resolve(v, values) for k, v in step.parameters.items()}
    op = step.operation
    if op == "BOX":
        if min(p["dx"], p["dy"], p["dz"]) <= 0:
            raise IRError("BOX %s has a non-positive dimension" % step.step_id)
        return K["BRepPrimAPI_MakeBox"](K["gp_Pnt"](0, 0, 0), p["dx"], p["dy"], p["dz"]).Shape()
    if op == "CYLINDER":
        if p["radius"] <= 0 or p["height"] <= 0:
            raise IRError("CYLINDER %s has a non-positive dimension" % step.step_id)
        return K["BRepPrimAPI_MakeCylinder"](p["radius"], p["height"]).Shape()
    if op == "SPHERE":
        if p["radius"] <= 0:
            raise IRError("SPHERE %s has a non-positive radius" % step.step_id)
        return K["BRepPrimAPI_MakeSphere"](p["radius"]).Shape()
    if op == "TRANSLATE":
        trsf = K["gp_Trsf"]()
        trsf.SetTranslation(K["gp_Vec"](p["dx"], p["dy"], p["dz"]))
        return K["BRepBuilderAPI_Transform"](built[step.operands[0]], trsf, True).Shape()
    if op == "ROTATE":
        import math
        d = AXIS_VECTORS["+" + step.axis]
        trsf = K["gp_Trsf"]()
        trsf.SetRotation(K["gp_Ax1"](K["gp_Pnt"](0, 0, 0), K["gp_Dir"](*d)),
                         math.radians(p["angle"]))
        return K["BRepBuilderAPI_Transform"](built[step.operands[0]], trsf, True).Shape()
    shape = built[step.operands[0]]
    for operand in step.operands[1:]:
        other = built[operand]
        if op == "UNION":
            algo = K["BRepAlgoAPI_Fuse"](shape, other)
        elif op == "CUT":
            algo = K["BRepAlgoAPI_Cut"](shape, other)
        else:
            algo = K["BRepAlgoAPI_Common"](shape, other)
        if not algo.IsDone():
            raise IRError("%s %s: the kernel did not complete the boolean" % (op, step.step_id))
        shape = algo.Shape()
    return shape


class BuildFailure(IRError):
    """A step of a feature did not build. Carries WHICH step, so the failure
    cites the feature and the step rather than a guess from a message."""

    def __init__(self, feature: str, step: str, cause: Exception):
        super().__init__("%s.%s: %s" % (feature, step, cause))
        self.feature, self.step, self.cause = feature, step, cause


def build_feature(K, spec: FeatureSpec, values: Dict[str, float], frame: Frame):
    """The feature's solid, in the world: its steps in its own frame, then the
    one derived transform."""
    built: Dict[str, Any] = {}
    for step in spec.steps:
        try:
            built[step.step_id] = _build_step(K, step, values, built)
        except (IRError, KeyError, RuntimeError) as exc:
            raise BuildFailure(spec.entity_id, step.step_id, exc)
    return placed(K, built[spec.terminal], frame)


ADDITIVE = "ADDITIVE"
SUBTRACTIVE = "SUBTRACTIVE"


def compile_embodiment(features: Sequence[FeatureSpec], values: Dict[str, float],
                       frames: Dict[str, Frame], polarity: Dict[str, str],
                       out_dir: Optional[str] = None) -> CompileResult:
    """Build every feature in its derived frame, compose every body from its
    features by declared polarity, measure, export, and check the round trips.

    UNIT G. A body is the union of its ADDITIVE features with its SUBTRACTIVE
    features removed, in id order within each polarity. On the first feature
    that cannot be built this returns with the feature and its step and with
    NO geometry emitted (S07-C6 as control flow). A feature with no derived
    frame is not built at the origin: it is the failure it is.
    """
    try:
        K = kernel()
    except KernelUnavailable as exc:
        return CompileResult(ok=False, problems=[str(exc)])
    if not features:
        # The hash of nothing is not evidence (Unit F); an embodiment with no
        # feature has nothing to compile and says so.
        return CompileResult(ok=False, problems=["no feature to compile; nothing gives any body "
                                                 "material"])
    result = CompileResult(ok=True)
    by_body: Dict[str, List[FeatureSpec]] = {}
    for f in sorted(features, key=lambda x: x.entity_id):
        by_body.setdefault(f.body, []).append(f)
    for body, specs in sorted(by_body.items()):
        shapes: Dict[str, Any] = {}
        fmap: Dict[str, str] = {}
        for spec in specs:
            pol = polarity.get(spec.kind)
            if pol not in (ADDITIVE, SUBTRACTIVE):
                return _fail(result, spec.entity_id, None,
                             "feature kind %s of %s has no declared polarity" % (spec.kind, spec.entity_id))
            frame = frames.get(spec.entity_id)
            if frame is None:
                return _fail(result, spec.entity_id, None,
                             "feature %s has no derived frame; nothing is built at the origin instead"
                             % spec.entity_id)
            try:
                shapes[spec.entity_id] = build_feature(K, spec, values, frame)
            except BuildFailure as exc:
                return _fail(result, exc.feature, exc.step, str(exc))
            fmap[spec.entity_id] = pol
        additive = [fid for fid in sorted(fmap) if fmap[fid] == ADDITIVE]
        subtractive = [fid for fid in sorted(fmap) if fmap[fid] == SUBTRACTIVE]
        if not additive:
            return _fail(result, None, None,
                         "body %s has no additive feature; nothing gives it material" % body)
        shape = shapes[additive[0]]
        for fid in additive[1:]:
            algo = K["BRepAlgoAPI_Fuse"](shape, shapes[fid])
            if not algo.IsDone():
                return _fail(result, fid, None, "UNION of %s into %s did not complete" % (fid, body))
            shape = algo.Shape()
        for fid in subtractive:
            algo = K["BRepAlgoAPI_Cut"](shape, shapes[fid])
            if not algo.IsDone():
                return _fail(result, fid, None, "CUT of %s from %s did not complete" % (fid, body))
            shape = algo.Shape()
        volume, count, valid, bbox = _measure(K, shape)
        result.bodies.append(CompiledBody(
            body_id=body, volume=volume, is_valid=valid, solid_count=count,
            single_connected_solid=(count == 1), bbox=bbox, feature_map=fmap,
            feature_shapes=shapes, shape=shape))

    # ---- S07-C1 / C2 -------------------------------------------------
    for b in result.bodies:
        if not b.is_valid or b.volume <= 0:
            result.ok = False
            result.problems.append(
                "S07-C1: body %s is not a valid solid with positive volume "
                "(valid=%s volume=%g)" % (b.body_id, b.is_valid, b.volume))
        if not b.single_connected_solid:
            result.ok = False
            result.problems.append(
                "S07-C2: body %s compiled to %d solids; a body must be a single "
                "connected solid" % (b.body_id, b.solid_count))
    result.signature = geometry_signature(result.bodies)
    if out_dir and result.ok:
        _export_and_check(K, result, out_dir)
    return result


def _fail(result: CompileResult, feature: Optional[str], step: Optional[str], problem: str
          ) -> CompileResult:
    result.ok = False
    result.failed_feature = feature
    result.failed_step = step
    result.problems.append(problem)
    result.bodies = []                       # no geometry is emitted on failure
    return result


def _measure(K, shape) -> Tuple[float, int, bool, Tuple[float, ...]]:
    props = K["GProp_GProps"]()
    K["BRepGProp"].VolumeProperties_s(shape, props)
    exp = K["TopExp_Explorer"](shape, K["TopAbs_SOLID"])
    n = 0
    while exp.More():
        n += 1
        exp.Next()
    valid = K["BRepCheck_Analyzer"](shape).IsValid()
    box = K["Bnd_Box"]()
    K["BRepBndLib"].Add_s(shape, box)
    return props.Mass(), n, bool(valid), tuple(box.Get())


def geometry_signature(bodies: Sequence[CompiledBody]) -> Dict[str, Any]:
    """Taken from the NATIVE shapes, before any export.

    Mass properties and bounds rather than a topology hash: OCCT face indices are
    not a persistent identity and the contract forbids treating them as one.
    """
    per_body = {}
    for b in sorted(bodies, key=lambda x: x.body_id):
        per_body[b.body_id] = {
            "volume": round(b.volume, 9),
            "bbox": [round(v, 9) for v in b.bbox],
            "solid_count": b.solid_count,
        }
    payload = json.dumps(per_body, sort_keys=True, separators=(",", ":"))
    return {"signature_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "per_body": per_body,
            "critical_dimensions": {b: v["bbox"] for b, v in per_body.items()}}


def _export_and_check(K, result: CompileResult, out_dir: str) -> None:
    """native brep -> step -> reimport -> compare, in the contract's order."""
    os.makedirs(out_dir, exist_ok=True)
    exports: Dict[str, Any] = {"native_brep_per_body": {}, "step_per_body": {}}
    rt: Dict[str, Any] = {"brep": {}, "step": {}}
    for b in result.bodies:
        brep_path = os.path.join(out_dir, "%s.brep" % b.body_id)
        step_path = os.path.join(out_dir, "%s.step" % b.body_id)
        K["BRepTools"].Write_s(b.shape, brep_path)
        exports["native_brep_per_body"][b.body_id] = brep_path

        shape2 = K["TopoDS_Shape"]()
        K["BRepTools"].Read_s(shape2, brep_path, K["BRep_Builder"]())
        v2, _c, _v, _bb = _measure(K, shape2)
        delta = abs(v2 - b.volume)
        rt["brep"][b.body_id] = delta
        if delta > BREP_VOLUME_TOLERANCE:
            result.ok = False
            result.problems.append(
                "S07-C3: %s BREP round-trip volume delta %g exceeds %g"
                % (b.body_id, delta, BREP_VOLUME_TOLERANCE))

        writer = K["STEPControl_Writer"]()
        writer.Transfer(b.shape, K["STEPControl_AsIs"])
        writer.Write(step_path)
        exports["step_per_body"][b.body_id] = step_path
        reader = K["STEPControl_Reader"]()
        reader.ReadFile(step_path)
        reader.TransferRoots()
        v3, _c3, valid3, _bb3 = _measure(K, reader.OneShape())
        rel = abs(v3 - b.volume) / b.volume if b.volume else abs(v3 - b.volume)
        rt["step"][b.body_id] = rel
        if rel > STEP_RELATIVE_TOLERANCE or not valid3:
            result.ok = False
            result.problems.append(
                "S07-C4: %s STEP round-trip relative delta %g (valid=%s)"
                % (b.body_id, rel, valid3))
    result.exports = exports
    result.roundtrip = rt


def independent_rebuild_matches(features: Sequence[FeatureSpec], values: Dict[str, float],
                                frames: Dict[str, Frame], polarity: Dict[str, str]
                                ) -> Tuple[bool, str, str]:
    """S07-C5. Compile twice and compare signatures taken from native shapes."""
    a = compile_embodiment(features, values, frames, polarity)
    b = compile_embodiment(features, values, frames, polarity)
    sa = (a.signature or {}).get("signature_sha256", "")
    sb = (b.signature or {}).get("signature_sha256", "")
    return (bool(sa) and sa == sb), sa, sb


# ==========================================================================
# UNIT G. THE ARTIFACT AS AN ASSEMBLY: posed solids, their interference, and
# the exchange files of the whole. These are kernel operations on DERIVED
# poses; nothing here chooses where a body goes.
# ==========================================================================
#: Two solids sharing more than this volume (mm3) interfere. Absolute, like
#: BREP_VOLUME_TOLERANCE, and declared rather than tuned.
INTERFERENCE_VOLUME_TOLERANCE = 1e-6
#: Two solids closer than this (mm) touch.
CONTACT_DISTANCE_TOLERANCE = 1e-6


def posed_shapes(K, bodies: Sequence[CompiledBody], poses: Dict[str, Frame]) -> Dict[str, Any]:
    """Each compiled body moved into its derived pose. Bodies with no pose are
    left out - a body nobody could place is not drawn at the origin."""
    out = {}
    for b in bodies:
        if b.body_id in poses:
            out[b.body_id] = placed(K, b.shape, poses[b.body_id])
    return out


def translated(K, shape, vector: Tuple[float, float, float]):
    """A posed solid moved along a vector, for a path check. Nothing about the
    design changes: this is the same solid asked where it would be."""
    trsf = K["gp_Trsf"]()
    trsf.SetTranslation(K["gp_Vec"](float(vector[0]), float(vector[1]), float(vector[2])))
    return K["BRepBuilderAPI_Transform"](shape, trsf, True).Shape()


def bbox_extent(K, shape) -> Tuple[float, float, float]:
    """The solid's bounding extent, used only to scale how far a path check
    walks. It decides nothing about the geometry."""
    box = K["Bnd_Box"]()
    K["BRepBndLib"].Add_s(shape, box)
    xa, ya, za, xb, yb, zb = box.Get()
    return (abs(xb - xa), abs(yb - ya), abs(zb - za))


def pair_geometry(K, a, b) -> Dict[str, float]:
    """The shared volume and the minimum distance of two posed solids."""
    common = K["BRepAlgoAPI_Common"](a, b)
    shared = 0.0
    if common.IsDone():
        props = K["GProp_GProps"]()
        K["BRepGProp"].VolumeProperties_s(common.Shape(), props)
        shared = max(props.Mass(), 0.0)
    dist = K["BRepExtrema_DistShapeShape"](a, b)
    distance = dist.Value() if dist.IsDone() else float("nan")
    return {"shared_volume": shared, "distance": distance}


def export_assembly(K, posed: Dict[str, Any], path: str) -> str:
    """One STEP file of every posed body, as a compound."""
    compound = K["TopoDS_Compound"]()
    builder = K["BRep_Builder"]()
    builder.MakeCompound(compound)
    for _bid, shape in sorted(posed.items()):
        builder.Add(compound, shape)
    writer = K["STEPControl_Writer"]()
    writer.Transfer(compound, K["STEPControl_AsIs"])
    writer.Write(path)
    return path


def export_stl(K, shape, path: str, deflection: float = 0.05) -> str:
    """A triangulated derivative for viewing; authoritative for nothing."""
    K["BRepMesh_IncrementalMesh"](shape, deflection, False, 0.5, True)
    writer = K["StlAPI_Writer"]()
    writer.Write(shape, path)
    return path
