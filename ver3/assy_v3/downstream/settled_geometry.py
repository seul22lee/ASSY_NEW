"""UNIT F. Post-settlement geometry: the deferred s04 questions, asked once the
numbers exist.

s04 committed an ARRANGEMENT - extents, reserved regions, sweeps - in its own
basis, provisionally. s05 stated where each feature's material may be as an
expression over the parameters it declares. s06 settled those parameters.
Only now can "does the embodiment respect what s04 reserved" be asked without
guessing, and it is asked in s04's own arithmetic: `aabb`, `overlaps` and
`excludes_occupancy` are imported from the s04 module, so this and s04b cannot
reach different answers about the same boxes.

WHAT IS NOT INVENTED. A RELATIVE basis is not read as millimetres; a unit the
basis does not state is not converted; a parameter with no settled value gives
no number. Each of those leaves the feature NOT_ESTABLISHED, reported by name,
and never a pass. Nothing here is a claim of clearance: an evaluable envelope
that overlaps nothing excluded is simply a feature for which no finding stands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import canonical_io, ir

RESOLVED = "RESOLVED"
UNRESOLVED = "UNRESOLVED"              # a referenced parameter has no settled value
NOT_COMPARABLE = "NOT_COMPARABLE"      # the basis cannot place the constant
INTRUDES = "INTRUDES"


@dataclass
class SettledGeometryReport:
    """Per feature: how far the occupancy question could be taken, and what it found."""

    branch: Optional[str]
    features: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    basis: Optional[str] = None

    def as_record(self) -> Dict[str, Any]:
        return {"branch": self.branch, "basis": self.basis,
                "features": {k: dict(v) for k, v in sorted(self.features.items())},
                "findings": list(self.findings)}


def _coordinate(value: float, unit: str, scale: Optional[Dict[str, Any]]) -> Optional[float]:
    """A settled physical constant as a coordinate in the s04 basis, or None.

    S05's `_constant_in_basis` is THE reading of the ReferenceScale - the same
    one the S05-C8 occupancy check uses - so this report and that check cannot
    disagree about whether a constant is comparable with an s04 extent.
    """
    from ..stages.s05_embodiment import _constant_in_basis

    return _constant_in_basis(ir.Expr.parse({"const": float(value), "unit": unit}), scale)


def _resolve_component(expr: ir.Expr, values: Dict[str, float], units: Dict[str, str]
                       ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """(number, unit, why_not) for one envelope component with the settled values."""
    from . import solver as _solver

    try:
        form = _solver.reduce_expr(expr, units)
    except ir.IRError as exc:
        return None, None, str(exc)
    total = form.const
    for pid, coef in sorted(form.terms.items()):
        if pid not in values:
            return None, None, "parameter %s has no settled value" % pid
        total += coef * values[pid]
    unit = _solver.dim_str(form.dim)
    return total, unit, None


def construction_problems(state, branch: Optional[str] = None) -> List[str]:
    """UNIT G (G5). The settled numbers, asked whether they build anything.

    A primitive with a non-positive dimension, a settlement that leaves a
    construction-critical parameter without a value, a placement origin that
    does not resolve: each is a finding here, before the kernel is asked,
    naming the statement and the number. Nothing is clamped or substituted.
    """
    from .compiler import resolve

    values = canonical_io.resolved_values(state, branch)
    out: List[str] = []
    for stmt in canonical_io.read_program(state, branch).statements:
        kinds = ir.OPCODE_PARAMETER_KINDS.get(stmt.operation) or {}
        for name, expr in sorted(stmt.parameters.items()):
            try:
                number = resolve(expr, values)
            except ir.IRError as exc:
                out.append("CONSTRUCTION_INVALID: %s.%s: %s" % (stmt.entity_id, name, exc))
                continue
            if kinds.get(name) == "length" and stmt.operation in ("BOX", "CYLINDER", "SPHERE") \
                    and number <= 0:
                out.append("CONSTRUCTION_INVALID: %s %s.%s settles to %g; a primitive "
                           "dimension must be positive" % (stmt.operation, stmt.entity_id,
                                                           name, number))
    for fid, node in sorted(canonical_io.read_placements(state, branch).items()):
        try:
            placement = ir.Placement.parse(node, "feature %s placement" % fid)
            for e in placement.origin:
                resolve(e, values)
        except ir.IRError as exc:
            out.append("CONSTRUCTION_INVALID: feature %s placement: %s" % (fid, exc))
    return out


def clearance_problems(state, branch: Optional[str] = None) -> List[str]:
    """UNIT G (G5). A CLEARANCE constraint whose settled margin has the wrong
    sign: the solver reports margins on inequalities; a feasible system with a
    negative clearance margin is a clearance stated as `<=`/`>=` the wrong way
    round, and a fit that will not go together."""
    out: List[str] = []
    for rec in sorted(state.standing("Constraint"), key=lambda r: r["entity_id"]):
        if branch and not canonical_io._in_branch(rec, branch):
            continue
        if str(rec.get("kind", "")).upper() not in ("CLEARANCE", "INTERFERENCE_FREE"):
            continue
        settlement = rec.get("settlement") or {}
        margin = settlement.get("margin")
        if isinstance(margin, (int, float)) and not isinstance(margin, bool) and margin < 0:
            out.append("CLEARANCE_NEGATIVE: constraint %s settles with margin %g"
                       % (rec["entity_id"], margin))
    return out


def evaluate(state, branch: Optional[str] = None) -> SettledGeometryReport:
    """Every standing feature of the branch against every excluding region."""
    from ..stages.s04_envelope_and_motion import (aabb, excludes_occupancy,
                                                  overlaps, unknown_region_role)

    report = SettledGeometryReport(branch=branch)
    scales = [r for r in state.standing("ReferenceScale")
              if not branch or canonical_io._in_branch(r, branch)]
    scale = scales[0] if len(scales) == 1 else None
    report.basis = (scale or {}).get("basis")
    values = canonical_io.resolved_values(state, branch)
    units = {p.entity_id: p.unit for p in canonical_io.read_parameters(state, branch)}
    known = set(units)

    regions = []
    for r in state.standing("FunctionalRegion"):
        if branch and not canonical_io._in_branch(r, branch):
            continue
        if unknown_region_role(r.get("role")) or not excludes_occupancy(r.get("role")):
            continue
        volume = r.get("volume") or {}
        centre, half = volume.get("centre"), volume.get("half_extent")
        if isinstance(centre, list) and isinstance(half, list):
            regions.append((r["entity_id"], aabb(centre, half)))

    for feature in sorted(state.standing("Feature"), key=lambda f: f["entity_id"]):
        if branch and not canonical_io._in_branch(feature, branch):
            continue
        fid = feature["entity_id"]
        if feature.get("envelope") is None:
            report.features[fid] = {"status": UNRESOLVED, "why": "no envelope"}
            continue
        exprs, problems = ir.envelope_problems(fid, feature["envelope"], known)
        if exprs is None:
            report.features[fid] = {"status": UNRESOLVED, "why": "; ".join(problems)}
            continue
        coords: Dict[str, List[float]] = {}
        entry: Dict[str, Any] = {"status": RESOLVED}
        for axis_list in ("centre", "half_extent"):
            numbers = []
            for expr in exprs[axis_list]:
                number, unit, why = _resolve_component(expr, values, units)
                if why:
                    entry = {"status": UNRESOLVED, "why": why}
                    break
                coordinate = _coordinate(number, unit, scale)
                if coordinate is None:
                    entry = {"status": NOT_COMPARABLE,
                             "why": "a %s constant cannot be placed in a %s basis"
                                    % (unit, report.basis or "missing")}
                    break
                numbers.append(coordinate)
            if entry["status"] != RESOLVED:
                break
            coords[axis_list] = numbers
        if entry["status"] != RESOLVED:
            report.features[fid] = entry
            continue
        box = aabb(coords["centre"], coords["half_extent"])
        entry["box"] = [list(box[0]), list(box[1])]
        intruded = [rid for rid, region_box in regions if overlaps(box, region_box)]
        if intruded:
            entry["status"] = INTRUDES
            entry["regions"] = intruded
            for rid in intruded:
                report.findings.append("feature %s intrudes into region %s with its "
                                       "settled envelope" % (fid, rid))
        report.features[fid] = entry
    return report
