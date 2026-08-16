"""Canonical DesignState in, authorized patch out, for s06 and s07.

WHY ADAPTERS AND NOT DIRECT CALLS

`solver.solve` and `compiler.compile_program` take typed values and know nothing
about DesignState - which is right, and is what makes them testable. But a caller
that assembled solver input by hand would be a second reading of what the design
says, and the settlement it wrote back would be a second write path. So exactly
one function here reads state into the IR, and exactly one turns each result into
a patch whose every operation is inside declared authority.

WHAT THESE MAY WRITE, AND HOW THAT IS ENFORCED

s06 extends `Parameter.value`, `Parameter.solved_by` and `Constraint.settlement`.
s07 creates `GeometrySignature` and extends `Body.compiled` and
`Feature.compiled_by_statement`. Nothing else - and the write boundary is what
actually enforces it: these functions build operations, and `DesignState.validate`
refuses any that stray. The fields are listed in DESIGN_STATE_CONTRACT under
`extendable_fields`, which is the only declaration the runtime reads.

NO MODEL PROVENANCE

Neither stage contacts a provider, so neither may carry a requested or served
model, and a provider id of "none" would be a lie in a field meant for a name.
Both are recorded through `DeterministicExecution`, which has no room for one.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..state.patch import Op
from . import compiler as _compiler
from . import ir
from . import solver as _solver

#: Provenance strings. Distinct per stage so a record says which deterministic
#: service wrote it without anyone parsing the field it landed in.
S06_PROVENANCE = "s06:settlement"
S07_PROVENANCE = "s07:compilation"


# ==========================================================================
# DesignState -> typed IR
# ==========================================================================
def read_parameters(state, branch: Optional[str] = None) -> List[ir.ParameterDecl]:
    """Every declared Parameter, as the solver's typed declaration.

    Ordered by entity id, because the solver's determinism guarantee is only as
    good as the order it is handed.
    """
    out = []
    for rec in sorted(state.standing("Parameter"), key=lambda r: r["entity_id"]):
        if branch and not _in_branch(rec, branch):
            continue
        out.append(ir.ParameterDecl.parse(rec))
    return out


def read_constraints(state, branch: Optional[str] = None) -> List[ir.TypedConstraint]:
    out = []
    for rec in sorted(state.standing("Constraint"), key=lambda r: r["entity_id"]):
        if branch and not _in_branch(rec, branch):
            continue
        out.append(ir.TypedConstraint.parse(rec))
    return out


def read_program(state, branch: Optional[str] = None) -> ir.ConstructionProgram:
    """The construction statements, read in committed order.

    A READING of state, not a second authority. There is no ConstructionProgram
    family and there does not need to be: the statements already carry the body
    they build and the operands they consume, and ordering is theirs.
    """
    rows = [r for r in sorted(state.standing("ConstructionStatement"),
                              key=lambda r: r["entity_id"])
            if not branch or _in_branch(r, branch)]
    return ir.ConstructionProgram.parse(rows)


def _in_branch(record: Dict[str, Any], branch: str) -> bool:
    """Does this entity belong to the candidate being worked on?

    Branch membership is the premise closure the architecture already records -
    an entity authored to embody a candidate carries it in `_premises`. Reading
    that rather than inventing a branch field is what keeps two alternatives from
    contaminating each other: s05 may author features for candidate A and B into
    one DesignState, and settling A's constraints against B's parameters would
    produce a design neither of them describes.
    """
    return branch in (record.get("_premises") or [])


# ==========================================================================
# s06 - settlement
# ==========================================================================
def solve_from_state(state, branch: Optional[str] = None
                     ) -> Tuple[_solver.SolverReport, List[ir.ParameterDecl]]:
    """Read the branch's system and settle it. No writes."""
    params = read_parameters(state, branch)
    cons = read_constraints(state, branch)
    return _solver.solve(params, cons), params


def settlement_operations(report: _solver.SolverReport,
                          parameters: Sequence[ir.ParameterDecl],
                          evidence_id: str) -> List[Op]:
    """The settlement, as operations the write boundary will accept.

    EXTEND and nothing else. A parameter that already has a value is not extended
    over - the boundary reports EXTEND_OVER_EXISTING and the caller must decide
    whether a revision is justified, which is a decision and not a mechanical
    consequence of solving again.

    Every settled value carries `solved_by`. That is what makes S05-C10
    checkable: a value with no cited solver artifact is a number nobody solved.
    """
    if report.solver_status != ir.FEASIBLE:
        # Nothing is written for a system that did not settle. An infeasible or
        # underdetermined report is evidence, and evidence does not become a
        # value.
        return []
    already = {p.entity_id for p in parameters if p.value is not None}
    ops: List[Op] = []
    for pid in sorted(report.settled):
        if pid in already:
            continue
        ops.append(Op("EXTEND", "Parameter", pid,
                      {"value": report.settled[pid], "solved_by": evidence_id},
                      S06_PROVENANCE))
    for cid in sorted(set(report.active_set) | set(report.residuals)):
        ops.append(Op("EXTEND", "Constraint", cid,
                      {"settlement": {"solver_status": report.solver_status,
                                      "residual": report.residuals.get(cid),
                                      "margin": report.margins.get(cid),
                                      "solved_by": evidence_id}},
                      S06_PROVENANCE))
    return ops


def evidence_identity(report: _solver.SolverReport) -> str:
    """A stable id for one settlement, derived from what was solved.

    Not a counter and not a timestamp: the same system solved twice is the same
    evidence, which is what makes S06-C6's determinism visible in state rather
    than only in a return value.
    """
    return "SLV-%s" % report.formulation_sha256[:16]


# ==========================================================================
# s07 - compilation
# ==========================================================================
def resolved_values(state, branch: Optional[str] = None) -> Dict[str, float]:
    """Parameter values that s06 actually settled.

    A value with no `solved_by` is not offered to the compiler. s07 compiles only
    explicit decisions, and a number nobody solved is not one - this is where
    R-23 would otherwise reach the geometry.
    """
    out: Dict[str, float] = {}
    for rec in state.standing("Parameter"):
        if branch and not _in_branch(rec, branch):
            continue
        if rec.get("value") is not None and rec.get("solved_by"):
            out[rec["entity_id"]] = float(rec["value"])
    return out


def compile_from_state(state, out_dir: Optional[str] = None,
                       branch: Optional[str] = None) -> _compiler.CompileResult:
    """Read the program and the settled values, and compile. No writes."""
    return _compiler.compile_program(read_program(state, branch),
                                     resolved_values(state, branch),
                                     out_dir=out_dir)


def compilation_operations(result: _compiler.CompileResult,
                           signature_id: str) -> List[Op]:
    """What compiling recorded, as operations inside s07's declared authority.

    s07 creates a GeometrySignature and extends compilation facts onto the bodies
    and features it built. It writes no engineering decision, because it made
    none: every field here is a statement about what compiled.

    A failed compile writes NOTHING. There is no partial signature and no
    half-registered artifact, because an artifact that exists is read as current.
    """
    if not result.ok or not result.signature:
        return []
    ops: List[Op] = [
        Op("CREATE", "GeometrySignature", signature_id, {
            "signature_sha256": result.signature["signature_sha256"],
            "per_body": result.signature["per_body"],
            "critical_dimensions": result.signature["critical_dimensions"]},
           S07_PROVENANCE)]
    for body in sorted(result.bodies, key=lambda b: b.body_id):
        ops.append(Op("EXTEND", "Body", body.body_id, {
            "compiled": {"volume": body.volume, "is_valid": body.is_valid,
                         "solid_count": body.solid_count,
                         "single_connected_solid": body.single_connected_solid,
                         "signature": signature_id}}, S07_PROVENANCE))
        for statement, feature in sorted(body.statement_map.items()):
            ops.append(Op("EXTEND", "Feature", feature,
                          {"compiled_by_statement": statement}, S07_PROVENANCE))
    return ops


def signature_identity(result: _compiler.CompileResult) -> str:
    """Derived from the geometry, so an identical rebuild registers identically."""
    digest = (result.signature or {}).get("signature_sha256", "")
    return "GSG-%s" % digest[:16]
