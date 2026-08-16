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

from .ir import (ConstructionProgram, Expr, IRError, Statement,
                 dependency_cone)

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
    statement_map: Dict[str, str] = field(default_factory=dict)
    shape: Any = None

    def as_record(self) -> Dict[str, Any]:
        return {"body_id": self.body_id, "volume": self.volume,
                "is_valid": self.is_valid, "solid_count": self.solid_count,
                "single_connected_solid": self.single_connected_solid,
                "bbox": list(self.bbox),
                "statement_map": dict(sorted(self.statement_map.items()))}


@dataclass
class CompileResult:
    ok: bool
    bodies: List[CompiledBody] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    failed_statement: Optional[str] = None
    dependency_cone: List[str] = field(default_factory=list)
    signature: Optional[Dict[str, Any]] = None
    exports: Dict[str, Any] = field(default_factory=dict)
    roundtrip: Dict[str, Any] = field(default_factory=dict)

    def as_record(self) -> Dict[str, Any]:
        return {"ok": self.ok,
                "bodies": [b.as_record() for b in self.bodies],
                "problems": list(self.problems),
                "failed_statement": self.failed_statement,
                "dependency_cone": list(self.dependency_cone),
                "signature": self.signature, "exports": dict(self.exports),
                "roundtrip": dict(self.roundtrip)}


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


def _build_statement(K, stmt: Statement, values: Dict[str, float],
                     built: Dict[str, Any]):
    """One opcode to one shape. No opcode consults anything but its own inputs."""
    p = {k: resolve(v, values) for k, v in stmt.parameters.items()}
    op = stmt.operation
    if op == "BOX":
        if min(p["dx"], p["dy"], p["dz"]) <= 0:
            raise IRError("BOX %s has a non-positive dimension" % stmt.entity_id)
        return K["BRepPrimAPI_MakeBox"](
            K["gp_Pnt"](0, 0, 0), p["dx"], p["dy"], p["dz"]).Shape()
    if op == "CYLINDER":
        if p["radius"] <= 0 or p["height"] <= 0:
            raise IRError("CYLINDER %s has a non-positive dimension" % stmt.entity_id)
        return K["BRepPrimAPI_MakeCylinder"](p["radius"], p["height"]).Shape()
    if op == "SPHERE":
        if p["radius"] <= 0:
            raise IRError("SPHERE %s has a non-positive radius" % stmt.entity_id)
        return K["BRepPrimAPI_MakeSphere"](p["radius"]).Shape()
    if op == "TRANSLATE":
        trsf = K["gp_Trsf"]()
        trsf.SetTranslation(K["gp_Vec"](p["dx"], p["dy"], p["dz"]))
        return K["BRepBuilderAPI_Transform"](built[stmt.operands[0]], trsf, True).Shape()
    if op == "ROTATE":
        import math
        d = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[stmt.axis]
        trsf = K["gp_Trsf"]()
        trsf.SetRotation(K["gp_Ax1"](K["gp_Pnt"](0, 0, 0), K["gp_Dir"](*d)),
                         math.radians(p["angle"]))
        return K["BRepBuilderAPI_Transform"](built[stmt.operands[0]], trsf, True).Shape()
    shape = built[stmt.operands[0]]
    for operand in stmt.operands[1:]:
        other = built[operand]
        if op == "UNION":
            algo = K["BRepAlgoAPI_Fuse"](shape, other)
        elif op == "CUT":
            algo = K["BRepAlgoAPI_Cut"](shape, other)
        else:
            algo = K["BRepAlgoAPI_Common"](shape, other)
        if not algo.IsDone():
            raise IRError("%s %s: the kernel did not complete the boolean"
                          % (op, stmt.entity_id))
        shape = algo.Shape()
    return shape


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


def compile_program(program: ConstructionProgram, values: Dict[str, float],
                    out_dir: Optional[str] = None) -> CompileResult:
    """Build every body, measure it, export it, and check the round trips.

    On the first statement that cannot be compiled this returns immediately with
    the statement and its dependency cone, and with NO geometry emitted - which
    is S07-C6 stated as control flow rather than as a promise.
    """
    ordering = program.ordering_problems()
    if ordering:
        return CompileResult(ok=False, problems=ordering,
                             failed_statement=ordering[0].split()[0],
                             dependency_cone=[])
    try:
        K = kernel()
    except KernelUnavailable as exc:
        return CompileResult(ok=False, problems=[str(exc)])

    result = CompileResult(ok=True)
    built: Dict[str, Any] = {}
    for body in program.bodies():
        stmts = program.for_body(body)
        terminal = program.terminal_of(body)
        if terminal is None:
            result.ok = False
            result.problems.append(
                "body %s has no single terminal statement; the program does not "
                "say which result IS the body" % body)
            return result
        smap: Dict[str, str] = {}
        for stmt in stmts:
            try:
                shape = _build_statement(K, stmt, values, built)
            except (IRError, KeyError, RuntimeError) as exc:
                result.ok = False
                result.failed_statement = stmt.entity_id
                result.dependency_cone = dependency_cone(program, stmt.entity_id)
                result.problems.append("%s: %s" % (stmt.entity_id, exc))
                result.bodies = []          # no geometry is emitted on failure
                return result
            built[stmt.entity_id] = shape
            if stmt.feature:
                smap[stmt.entity_id] = stmt.feature
        volume, count, valid, bbox = _measure(K, built[terminal])
        result.bodies.append(CompiledBody(
            body_id=body, volume=volume, is_valid=valid, solid_count=count,
            single_connected_solid=(count == 1), bbox=bbox,
            statement_map=smap, shape=built[terminal]))

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


def independent_rebuild_matches(program: ConstructionProgram,
                                values: Dict[str, float]) -> Tuple[bool, str, str]:
    """S07-C5. Compile twice and compare signatures taken from native shapes."""
    a = compile_program(program, values)
    b = compile_program(program, values)
    sa = (a.signature or {}).get("signature_sha256", "")
    sb = (b.signature or {}).get("signature_sha256", "")
    return (bool(sa) and sa == sb), sa, sb
