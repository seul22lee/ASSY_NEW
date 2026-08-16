"""s06 - solve, or report precisely why not.

llm_role is NONE and stays NONE. S06_CONTRACT lists "any LLM involvement" among
its prohibited decisions with the rationale that a model here re-introduces R-23,
copying existing values and calling them solved.

WHAT THIS SOLVER WILL AND WILL NOT DO

It settles linear relations over declared parameters - which is what the declared
constraint population is: envelope arithmetic ("a boss radius is r+w") and
clearance arithmetic ("this gap is at least 0.5 mm"). Equalities settle values;
inequalities bound them and are checked.

It does NOT choose. If several values satisfy every constraint, that is an
UNDERDETERMINED system and the free directions are reported as such. Picking the
midpoint, the lower bound, or "the one that looks right" would be selection
authority, and selection does not live here. S06_CONTRACT names this directly:
it may not "silently pick one member of a solution family".

It does NOT approximate. A formulation it cannot interpret exactly is
`unsupported_formulation`, never a best effort - "Never approximate a report of
success."

DETERMINISM IS A CHECKED PROPERTY (S06-C6)

Ordering is by entity id throughout, elimination is exact rational-free floating
arithmetic on a fixed pivot order, and no dictionary iteration order can reach a
result. `solve` called twice on the same input returns equal reports.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .ir import (DECLARED, Expr, FEASIBLE, INFEASIBLE, IRError, ParameterDecl,
                 SOLVED, SOLVER_FAILURE, TypedConstraint, UNDERDETERMINED,
                 UNSUPPORTED_FORMULATION)

#: Below this a residual is zero. Absolute, in the declared unit, and declared
#: here rather than passed in so a caller cannot widen it to obtain a feasible
#: report (S06-C2).
RESIDUAL_TOLERANCE = 1e-9


class Linear:
    """A linear form over parameter ids: sum(coef * id) + constant.

    The one representation the solver works in. Anything that cannot be reduced
    to it is unsupported, and saying so is a contract status rather than a
    failure - which is why reduction raises `IRError` instead of guessing.
    """

    #: `units` is a SET, and that is the correction that made the unit check
    #: work at all. Carrying a single `unit` and combining with `a or b` meant
    #: the first unit always won, so adding a millimetre to a degree produced a
    #: millimetre and the mismatch this class exists to catch was erased before
    #: anything looked at it. Every unit that entered a form stays visible.
    __slots__ = ("terms", "const", "units")

    def __init__(self, terms: Optional[Dict[str, float]] = None,
                 const: float = 0.0, unit: Optional[str] = None,
                 units: Optional[Set[str]] = None):
        self.terms = {k: v for k, v in (terms or {}).items() if v != 0.0}
        self.const = const
        self.units: Set[str] = set(units or ())
        if unit:
            self.units.add(unit)

    def __add__(self, other: "Linear") -> "Linear":
        terms = dict(self.terms)
        for k, v in other.terms.items():
            terms[k] = terms.get(k, 0.0) + v
        return Linear(terms, self.const + other.const,
                      units=self.units | other.units)

    def __sub__(self, other: "Linear") -> "Linear":
        return self + other.scaled(-1.0)

    def scaled(self, k: float) -> "Linear":
        return Linear({t: c * k for t, c in self.terms.items()},
                      self.const * k, units=self.units)

    def is_constant(self) -> bool:
        return not self.terms


def reduce_expr(expr: Expr, units: Dict[str, str]) -> Linear:
    """Expression -> linear form, or IRError if it is not linear.

    Multiplication is admitted only when one side is constant, and division only
    by a constant. A product of two unknowns is a nonlinear system this solver
    does not claim to handle, and claiming it would be the approximation the
    contract forbids.
    """
    if expr.ref is not None:
        if expr.ref not in units:
            raise IRError("expression references undeclared parameter %s" % expr.ref)
        return Linear({expr.ref: 1.0}, 0.0, units[expr.ref])
    if expr.const is not None:
        return Linear({}, expr.const, expr.unit)
    parts = [reduce_expr(a, units) for a in expr.args]
    if expr.op == "+":
        out = parts[0]
        for p in parts[1:]:
            out = out + p
        return out
    if expr.op == "-":
        out = parts[0]
        for p in parts[1:]:
            out = out - p
        return out
    if expr.op == "*":
        out = parts[0]
        for p in parts[1:]:
            if p.is_constant():
                out = out.scaled(p.const)
            elif out.is_constant():
                out = p.scaled(out.const)
            else:
                raise IRError("product of two non-constant expressions is not "
                              "linear; this solver does not support it")
        return out
    if expr.op == "/":
        out = parts[0]
        for p in parts[1:]:
            if not p.is_constant():
                raise IRError("division by a non-constant expression is not "
                              "linear; this solver does not support it")
            if p.const == 0.0:
                raise IRError("division by zero")
            out = out.scaled(1.0 / p.const)
        return out
    raise IRError("unknown operator %r" % expr.op)


def unit_problems(form: Linear, units: Dict[str, str], where: str) -> List[str]:
    """Every quantity combined in one relation must share a unit.

    Structural, not defaulted: S06 may not default a missing unit (R-21), and it
    must not silently add a millimetre to a degree either.
    """
    seen = {units[t] for t in form.terms if t in units} | set(form.units)
    return ([] if len(seen) <= 1 else
            ["%s mixes units %s" % (where, sorted(seen))])


@dataclass
class SolverReport:
    """What s06 says about one settlement attempt. The evidence for S05-C10."""

    solver_status: str
    settled: Dict[str, float] = field(default_factory=dict)
    residuals: Dict[str, float] = field(default_factory=dict)
    active_set: List[str] = field(default_factory=list)
    margins: Dict[str, float] = field(default_factory=dict)
    free_parameters: List[str] = field(default_factory=list)
    conflicting: List[str] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    formulation_sha256: str = ""
    solver_id: str = "assy.downstream.solver/1"

    def as_record(self) -> Dict[str, Any]:
        return {"solver_id": self.solver_id,
                "solver_status": self.solver_status,
                "formulation_sha256": self.formulation_sha256,
                "settled": dict(sorted(self.settled.items())),
                "residuals": dict(sorted(self.residuals.items())),
                "active_set": list(self.active_set),
                "margins": dict(sorted(self.margins.items())),
                "free_parameters": list(self.free_parameters),
                "conflicting": list(self.conflicting),
                "problems": list(self.problems)}


def formulation_hash(params: Sequence[ParameterDecl],
                     constraints: Sequence[TypedConstraint]) -> str:
    """Identity of the exact system solved. Sorted, so it is order-independent."""
    payload = {
        "parameters": sorted([p.entity_id, p.unit, p.status,
                              p.lower, p.upper] for p in params),
        "constraints": sorted([c.entity_id, c.relation,
                               json.dumps(c.lhs.as_dict(), sort_keys=True),
                               json.dumps(c.rhs.as_dict(), sort_keys=True)]
                              for c in constraints),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def solve(parameters: Sequence[ParameterDecl],
          constraints: Sequence[TypedConstraint]) -> SolverReport:
    """Settle what the equalities determine; check what the inequalities bound.

    Ordering is by entity id at every step, and the elimination pivots on the
    lowest-id remaining unknown, so the result cannot depend on input order or on
    dictionary iteration (S06-C6).
    """
    params = sorted(parameters, key=lambda p: p.entity_id)
    cons = sorted(constraints, key=lambda c: c.entity_id)
    units = {p.entity_id: p.unit for p in params}
    report = SolverReport(solver_status=SOLVER_FAILURE,
                          formulation_sha256=formulation_hash(params, cons))

    # ---- reduce every relation, or declare the formulation unsupported ----
    equalities: List[Tuple[str, Linear]] = []
    inequalities: List[Tuple[str, str, Linear]] = []
    for c in cons:
        try:
            form = reduce_expr(c.lhs, units) - reduce_expr(c.rhs, units)
        except IRError as exc:
            report.solver_status = UNSUPPORTED_FORMULATION
            report.problems.append("%s: %s" % (c.entity_id, exc))
            return report
        problems = unit_problems(form, units, c.entity_id)
        if problems:
            report.solver_status = UNSUPPORTED_FORMULATION
            report.problems.extend(problems)
            return report
        if c.relation == "==":
            equalities.append((c.entity_id, form))
        else:
            inequalities.append((c.entity_id, c.relation, form))

    # ---- values already fixed are constants, not unknowns ----
    known: Dict[str, float] = {p.entity_id: p.value for p in params
                               if p.value is not None and p.status == SOLVED}

    def substitute(form: Linear) -> Linear:
        out = Linear({}, form.const, units=form.units)
        for t, coef in sorted(form.terms.items()):
            if t in known:
                out = out + Linear({}, coef * known[t], units=form.units)
            else:
                out = out + Linear({t: coef}, 0.0, units=form.units)
        return out

    # ---- Gaussian elimination on the equality block, lowest id pivots ----
    rows = [(cid, substitute(f)) for cid, f in equalities]
    used: List[str] = []
    changed = True
    while changed:
        changed = False
        for i, (cid, form) in enumerate(rows):
            form = substitute(form)
            rows[i] = (cid, form)
            unknowns = sorted(form.terms)
            if len(unknowns) == 1:
                pivot = unknowns[0]
                coef = form.terms[pivot]
                if coef == 0.0:
                    continue
                known[pivot] = -form.const / coef
                used.append(cid)
                changed = True
            elif not unknowns and abs(form.const) > RESIDUAL_TOLERANCE:
                # No unknown left and the relation does not hold: the equalities
                # contradict each other. Reported as the conflict it is.
                report.solver_status = INFEASIBLE
                report.conflicting.append(cid)
                report.residuals[cid] = form.const
                report.problems.append(
                    "%s cannot be satisfied: residual %g" % (cid, form.const))
                return report

    # ---- residuals of every equality against the settled values ----
    for cid, form in rows:
        resid = substitute(form)
        if resid.terms:
            continue
        report.residuals[cid] = resid.const
        if abs(resid.const) > RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(cid)
            report.problems.append(
                "%s residual %g exceeds %g" % (cid, resid.const, RESIDUAL_TOLERANCE))
            return report

    # ---- inequalities: check the settled ones, keep the rest as bounds ----
    for cid, rel, form in inequalities:
        resid = substitute(form)
        if resid.terms:
            report.active_set.append(cid)
            continue
        margin = -resid.const if rel == "<=" else resid.const
        report.margins[cid] = margin
        report.active_set.append(cid)
        if margin < -RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(cid)
            report.problems.append(
                "%s violated by %g" % (cid, -margin))
            return report

    # ---- declared bounds are constraints too ----
    for p in params:
        if p.entity_id not in known:
            continue
        v = known[p.entity_id]
        if p.lower is not None and v < p.lower - RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(p.entity_id)
            report.problems.append("%s settled %g below its lower bound %g"
                                   % (p.entity_id, v, p.lower))
            return report
        if p.upper is not None and v > p.upper + RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(p.entity_id)
            report.problems.append("%s settled %g above its upper bound %g"
                                   % (p.entity_id, v, p.upper))
            return report

    report.settled = {k: v for k, v in known.items()
                      if not any(p.entity_id == k and p.status == SOLVED
                                 and p.value == v for p in params)}
    report.settled = dict(known)

    # ---- anything the equalities did not determine stays free ----
    free = [p.entity_id for p in params if p.entity_id not in known]
    if free:
        # NOT a value chosen from the admissible domain. The free directions are
        # reported so an authorized producer can decide, which is exactly what
        # "may not silently pick one member of a solution family" requires.
        report.free_parameters = free
        report.solver_status = UNDERDETERMINED
        report.problems.append(
            "%d parameter(s) are not determined by the constraint system: %s"
            % (len(free), ", ".join(free)))
        return report

    report.solver_status = FEASIBLE
    return report
