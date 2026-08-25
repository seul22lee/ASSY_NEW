"""s06 - solve, or report precisely why not.

llm_role is NONE and stays NONE. S06_CONTRACT lists "any LLM involvement" among
its prohibited decisions with the rationale that a model here re-introduces R-23,
copying existing values and calling them solved.

WHAT THIS SOLVER SOLVES

Simultaneous linear systems over declared parameters, by Gaussian elimination
with rank detection. That is what the declared constraint population is: envelope
arithmetic ("a boss radius is r + w") and clearance arithmetic ("this gap is at
least 0.5 mm"), which couple - a boss radius constrains an arm radius which
constrains an axis height. Equalities settle values; inequalities bound them and
report margins.

An earlier version settled only rows that already reduced to a single unknown. It
was not a linear solver, and it reported a coupled 2x2 system as UNDERDETERMINED
when the system had a unique solution. Rank is now computed rather than inferred
from how convenient a row happened to look.

DIMENSIONS, NOT UNIT STRINGS

Quantities carry an exponent vector over base units. `mm` is length; `mm * mm` is
an area; a scale factor is dimensionless. Comparing a length with an area is a
dimension error rather than a value, which is the defect a string-valued `unit`
could not see: `0.5 mm * 10 mm` reduced to `5 mm` and compared happily against a
length.

WHAT IT WILL NOT DO

It does not choose. If the system leaves free directions, that is UNDERDETERMINED
and the free parameters are named; picking a member of a solution family is
selection authority and selection does not live here. It does not approximate: a
formulation it cannot interpret exactly is `unsupported_formulation`, never a best
effort - "Never approximate a report of success."

DETERMINISM IS A CHECKED PROPERTY (S06-C6)

Variables are ordered by entity id, rows by constraint id, and the pivot is the
lowest remaining variable with the largest-magnitude coefficient among remaining
rows, ties broken by row order. No dictionary iteration order can reach a result.
"""
from __future__ import annotations

import hashlib
import re
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .ir import (DECLARED, Expr, FEASIBLE, INFEASIBLE, IRError, ParameterDecl,
                 SOLVED, SOLVER_FAILURE, TypedConstraint, UNDERDETERMINED,
                 UNSUPPORTED_FORMULATION)

#: Below this a residual is zero. Absolute, and declared here rather than passed
#: in so a caller cannot widen it to obtain a feasible report (S06-C2).
RESIDUAL_TOLERANCE = 1e-9
#: Below this a pivot is no pivot. Separate from the residual tolerance because
#: it answers a different question - rank, not satisfaction.
PIVOT_TOLERANCE = 1e-12

Dim = Tuple[Tuple[str, int], ...]

#: A DIMENSION is an exponent vector over base units, canonicalised as a sorted
#: tuple: `mm` is (("mm",1),), an area is (("mm",2),), a pure number is ().
DIMENSIONLESS: Dim = ()

#: Spellings that mean "a pure number". A dimensionless literal is how a scale
#: factor is written, and scaling is the multiplication the constraint population
#: actually uses.
SCALAR_UNITS = ("1", "", "dimensionless", "scalar", "ratio")


class DimensionError(IRError):
    """Two quantities that cannot be combined. Reported, never coerced."""


def dim_of_unit(unit: Optional[str]) -> Dim:
    """A declared unit string to an exponent vector.

    A trailing exponent is read, so `mm2` and `mm^2` are both the area that
    `mm * mm` produces. Without this a parameter declared in mm2 could never be
    equated to a product of two lengths - the multiplication would be right and
    the comparison would fail - and areas and volumes are exactly what envelope
    reasoning multiplies its way into.

    Anything else is one base unit with exponent 1. No unit is invented and none
    is converted: `cm` is not `mm`, and saying so is the point.
    """
    if unit is None or str(unit) in SCALAR_UNITS:
        return DIMENSIONLESS
    text = str(unit).strip()
    match = re.match(r"^([A-Za-z_]+)\s*(?:\^)?\s*(-?\d+)$", text)
    if match:
        base, exp = match.group(1), int(match.group(2))
        return DIMENSIONLESS if exp == 0 else ((base, exp),)
    return ((text, 1),)


def dim_mul(a: Dim, b: Dim) -> Dim:
    exps: Dict[str, int] = {}
    for u, e in tuple(a) + tuple(b):
        exps[u] = exps.get(u, 0) + e
    return tuple(sorted((u, e) for u, e in exps.items() if e != 0))


def dim_inv(a: Dim) -> Dim:
    return tuple(sorted((u, -e) for u, e in a))


def dim_str(d: Dim) -> str:
    return ("dimensionless" if not d else
            "*".join(u if e == 1 else "%s^%d" % (u, e) for u, e in d))


class Linear:
    """A linear form over parameter ids: sum(coef * id) + constant, with a dimension."""

    __slots__ = ("terms", "const", "dim")

    def __init__(self, terms: Optional[Dict[str, float]] = None,
                 const: float = 0.0, dim: Dim = DIMENSIONLESS):
        self.terms = {k: v for k, v in (terms or {}).items() if v != 0.0}
        self.const = const
        self.dim = tuple(dim)

    def _neutral(self) -> bool:
        """A bare zero combines with anything; it asserts no dimension."""
        return not self.terms and self.const == 0.0 and not self.dim

    def require_same(self, other: "Linear", what: str) -> None:
        if self._neutral() or other._neutral():
            return
        if self.dim != other.dim:
            raise DimensionError("%s combines %s with %s"
                                 % (what, dim_str(self.dim), dim_str(other.dim)))

    def __add__(self, other: "Linear") -> "Linear":
        self.require_same(other, "addition")
        terms = dict(self.terms)
        for k, v in other.terms.items():
            terms[k] = terms.get(k, 0.0) + v
        return Linear(terms, self.const + other.const, self.dim or other.dim)

    def __sub__(self, other: "Linear") -> "Linear":
        self.require_same(other, "subtraction")
        return Linear(
            {k: v for k, v in
             ({**{t: c for t, c in self.terms.items()},
               **{t: self.terms.get(t, 0.0) - c
                  for t, c in other.terms.items()}}).items()},
            self.const - other.const, self.dim or other.dim)

    def scaled(self, k: float, dim: Dim = DIMENSIONLESS) -> "Linear":
        return Linear({t: c * k for t, c in self.terms.items()},
                      self.const * k, dim_mul(self.dim, dim))

    def is_constant(self) -> bool:
        return not self.terms


def reduce_expr(expr: Expr, units: Dict[str, str]) -> Linear:
    """Expression -> linear form, or IRError if it is not linear.

    A constant factor MAY carry a dimension - `2 mm * x` is linear in x - and the
    dimension of the result follows. A product of two unknowns is nonlinear and
    is refused rather than approximated.
    """
    if expr.ref is not None:
        if expr.ref not in units:
            raise IRError("expression references undeclared parameter %s" % expr.ref)
        return Linear({expr.ref: 1.0}, 0.0, dim_of_unit(units[expr.ref]))
    if expr.const is not None:
        return Linear({}, expr.const, dim_of_unit(expr.unit))
    parts = [reduce_expr(a, units) for a in expr.args]
    if expr.op == "+":
        out = parts[0]
        for p in parts[1:]:
            out = out + p
        return out
    if expr.op == "-":
        if len(parts) == 1:
            return parts[0].scaled(-1.0, ())          # unary minus: negation (Unit G)
        out = parts[0]
        for p in parts[1:]:
            out = out - p
        return out
    if expr.op == "*":
        out = parts[0]
        for p in parts[1:]:
            if p.is_constant():
                out = out.scaled(p.const, p.dim)
            elif out.is_constant():
                out = p.scaled(out.const, out.dim)
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
            out = out.scaled(1.0 / p.const, dim_inv(p.dim))
        return out
    raise IRError("unknown operator %r" % expr.op)


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
    rank: int = 0
    unknown_count: int = 0
    formulation_sha256: str = ""
    solver_id: str = "assy.downstream.solver/2"

    def as_record(self) -> Dict[str, Any]:
        return {"solver_id": self.solver_id,
                "solver_status": self.solver_status,
                "formulation_sha256": self.formulation_sha256,
                "rank": self.rank, "unknown_count": self.unknown_count,
                "settled": {k: round(v, 12) for k, v in sorted(self.settled.items())},
                "residuals": {k: round(v, 12) for k, v in sorted(self.residuals.items())},
                "active_set": list(self.active_set),
                "margins": {k: round(v, 12) for k, v in sorted(self.margins.items())},
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
    """Settle what the equalities determine; check what the inequalities bound."""
    params = sorted(parameters, key=lambda p: p.entity_id)
    cons = sorted(constraints, key=lambda c: c.entity_id)
    units = {p.entity_id: p.unit for p in params}
    report = SolverReport(solver_status=SOLVER_FAILURE,
                          formulation_sha256=formulation_hash(params, cons))

    # ---- reduce, or declare the formulation unsupported --------------
    equalities: List[Tuple[str, Linear]] = []
    inequalities: List[Tuple[str, str, Linear]] = []
    for c in cons:
        try:
            lhs = reduce_expr(c.lhs, units)
            rhs = reduce_expr(c.rhs, units)
            lhs.require_same(rhs, "%s relation" % c.entity_id)
            form = lhs - rhs
        except IRError as exc:
            report.solver_status = UNSUPPORTED_FORMULATION
            report.problems.append("%s: %s" % (c.entity_id, exc))
            return report
        (equalities if c.relation == "==" else inequalities).append(
            (c.entity_id, form) if c.relation == "==" else
            (c.entity_id, c.relation, form))

    # ---- values already settled are constants, not unknowns ----------
    known: Dict[str, float] = {p.entity_id: p.value for p in params
                               if p.value is not None and p.status == SOLVED}
    unknowns = [p.entity_id for p in params if p.entity_id not in known]
    report.unknown_count = len(unknowns)
    index = {v: i for i, v in enumerate(unknowns)}

    # ---- build the augmented matrix, rows ordered by constraint id ---
    rows: List[Tuple[str, List[float], float]] = []
    for cid, form in equalities:
        coefs = [0.0] * len(unknowns)
        const = form.const
        for t, c in sorted(form.terms.items()):
            if t in known:
                const += c * known[t]
            else:
                coefs[index[t]] += c
        rows.append((cid, coefs, const))

    # ---- Gaussian elimination with explicit rank ---------------------
    pivot_row_of: Dict[int, int] = {}
    r = 0
    for col in range(len(unknowns)):
        best, best_mag = -1, PIVOT_TOLERANCE
        for i in range(r, len(rows)):
            mag = abs(rows[i][1][col])
            if mag > best_mag:
                best, best_mag = i, mag
        if best < 0:
            continue
        rows[r], rows[best] = rows[best], rows[r]
        cid, coefs, const = rows[r]
        pivot = coefs[col]
        coefs = [v / pivot for v in coefs]
        const = const / pivot
        rows[r] = (cid, coefs, const)
        for i in range(len(rows)):
            if i == r or abs(rows[i][1][col]) <= PIVOT_TOLERANCE:
                continue
            cid_i, coefs_i, const_i = rows[i]
            factor = coefs_i[col]
            rows[i] = (cid_i,
                       [a - factor * b for a, b in zip(coefs_i, coefs)],
                       const_i - factor * const)
        pivot_row_of[col] = r
        r += 1
    report.rank = r

    # ---- an all-zero row with a non-zero constant is a contradiction --
    for cid, coefs, const in rows:
        if all(abs(v) <= PIVOT_TOLERANCE for v in coefs) and abs(const) > RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(cid)
            report.residuals[cid] = const
            report.problems.append(
                "%s cannot be satisfied: the equality system is inconsistent "
                "(residual %g)" % (cid, const))
            return report

    # ---- read off the settled values ---------------------------------
    for col, row_i in sorted(pivot_row_of.items()):
        _cid, coefs, const = rows[row_i]
        # A pivot row that still couples other unknowns determines nothing on its
        # own; that variable is part of a free family, not settled.
        if any(abs(coefs[j]) > PIVOT_TOLERANCE for j in range(len(unknowns))
               if j != col):
            continue
        # The pivot row was normalised to a leading 1 during elimination, so the
        # row reads `x + const = 0` and the value is simply -const. Dividing by
        # the coefficient again would be arithmetic on a known 1.0.
        known[unknowns[col]] = -const
    report.settled = dict(known)

    def value_of(form: Linear) -> Optional[float]:
        total = form.const
        for t, c in sorted(form.terms.items()):
            if t not in known:
                return None
            total += c * known[t]
        return total

    for cid, form in equalities:
        v = value_of(form)
        if v is None:
            continue
        report.residuals[cid] = v
        if abs(v) > RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(cid)
            report.problems.append("%s residual %g exceeds %g"
                                   % (cid, v, RESIDUAL_TOLERANCE))
            return report

    # ---- inequalities ------------------------------------------------
    for cid, rel, form in inequalities:
        report.active_set.append(cid)
        v = value_of(form)
        if v is None:
            continue
        margin = -v if rel == "<=" else v
        report.margins[cid] = margin
        if margin < -RESIDUAL_TOLERANCE:
            report.solver_status = INFEASIBLE
            report.conflicting.append(cid)
            report.problems.append("%s violated by %g" % (cid, -margin))
            return report

    # ---- declared bounds are constraints too -------------------------
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

    free = [u for u in unknowns if u not in known]
    if free:
        # NOT a value chosen from the admissible domain. The free directions are
        # reported so an authorized producer can decide, which is what "may not
        # silently pick one member of a solution family" requires.
        report.free_parameters = free
        report.solver_status = UNDERDETERMINED
        report.problems.append(
            "rank %d over %d unknown(s); %d direction(s) remain free: %s"
            % (report.rank, len(unknowns), len(free), ", ".join(free)))
        return report

    report.solver_status = FEASIBLE
    return report


def dimension_problems(expression: Dict[str, Any], units: Dict[str, str]) -> List[str]:
    """UNIT G. Do the two sides of a relation reduce to ONE dimension?

    The one reading of a dimension is this module's linear reduction, so the
    write boundary asks it here rather than keeping a second unit algebra. A
    formulation this solver cannot reduce for another reason (a product of
    unknowns, a division by an unknown) is not a dimensional defect and is
    reported at settlement, not here.
    """
    try:
        lhs = reduce_expr(Expr.parse(expression.get("lhs")), units)
        rhs = reduce_expr(Expr.parse(expression.get("rhs")), units)
    except DimensionError as exc:
        return ["combines dimensions it cannot: %s" % exc]
    except IRError:
        return []
    if lhs.dim != rhs.dim and not (lhs.is_constant() and lhs.const == 0.0) \
            and not (rhs.is_constant() and rhs.const == 0.0):
        return ["relates %s to %s; a relation holds between quantities of one dimension"
                % (dim_str(lhs.dim), dim_str(rhs.dim))]
    return []
