"""UNIT G (G5). The settled numbers, asked whether they build anything.

The solver settles values; whether the values build a solid is asked here,
deterministically and before the kernel: a primitive with a non-positive
dimension, an offset that does not resolve, a CLEARANCE constraint whose
settled margin has the wrong sign. Each is named with the feature, the step
and the number. Nothing is clamped, defaulted or re-solved.

Occupancy against s04's reserved regions is judged on the ACTUAL solids in
the arrangement frame (`downstream.artifact`), which is the one place a
feature's material is known; no second, symbolic statement of it exists.
"""
from __future__ import annotations

from typing import List, Optional

from . import canonical_io, ir


def construction_problems(state, branch: Optional[str] = None) -> List[str]:
    from .compiler import resolve

    values = canonical_io.resolved_values(state, branch)
    out: List[str] = []
    for spec in canonical_io.read_features(state, branch):
        for index, expr in enumerate(spec.placement.offset):
            try:
                resolve(expr, values)
            except ir.IRError as exc:
                out.append("CONSTRUCTION_INVALID: %s placement offset[%d]: %s"
                           % (spec.entity_id, index, exc))
        for step in spec.steps:
            kinds = ir.OPCODE_PARAMETER_KINDS.get(step.operation) or {}
            for name, expr in sorted(step.parameters.items()):
                try:
                    number = resolve(expr, values)
                except ir.IRError as exc:
                    out.append("CONSTRUCTION_INVALID: %s.%s.%s: %s"
                               % (spec.entity_id, step.step_id, name, exc))
                    continue
                if kinds.get(name) == "length" and step.operation in ("BOX", "CYLINDER", "SPHERE") \
                        and number <= 0:
                    out.append("CONSTRUCTION_INVALID: %s %s.%s.%s settles to %g; a primitive "
                               "dimension must be positive"
                               % (step.operation, spec.entity_id, step.step_id, name, number))
    return out


def clearance_problems(state, branch: Optional[str] = None) -> List[str]:
    """A CLEARANCE constraint whose settled margin has the wrong sign."""
    out: List[str] = []
    for rec in sorted(state.standing("Constraint"), key=lambda r: r["entity_id"]):
        if branch and not canonical_io._in_branch(rec, branch):
            continue
        if str(rec.get("kind", "")).upper() not in ("CLEARANCE", "INTERFERENCE_FREE"):
            continue
        margin = (rec.get("settlement") or {}).get("margin")
        if isinstance(margin, (int, float)) and not isinstance(margin, bool) and margin < 0:
            out.append("CLEARANCE_NEGATIVE: constraint %s settles with margin %g"
                       % (rec["entity_id"], margin))
    return out
