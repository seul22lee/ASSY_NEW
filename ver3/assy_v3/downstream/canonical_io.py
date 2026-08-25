"""Canonical DesignState in, authorized patch out, for s06 and s07.

NOT AN ADAPTER, AND THE NAME MATTERS

This module was called `adapters.py`, and the rebuild policy rejected that name:
rule 3 forbids a compatibility adapter without approval, and the check matches on
the name because that is how a shim announces itself. The rejection was right about
the name and would have been wrong about the module, so the module was renamed
rather than exempted - an exception list entry would have bought a permanent
"adapter" in the tree for the sake of one file's filename.

What this actually does is READ canonical state into the typed IR and WRITE
canonical patches back. It translates nothing between an old shape and a new one,
and there is no legacy form on either side of it.

WHY IT EXISTS RATHER THAN DIRECT CALLS

`solver.solve` and `compiler.compile_embodiment` take typed values and know nothing
about DesignState - which is right, and is what makes them testable. But a caller
that assembled solver input by hand would be a second reading of what the design
says, and the settlement it wrote back would be a second write path. So exactly
one function here reads state into the IR, and exactly one turns each result into
a patch whose every operation is inside declared authority.

WHAT THESE MAY WRITE, AND HOW THAT IS ENFORCED

s06 extends `Parameter.value`, `Parameter.solved_by` and `Constraint.settlement`.

s07 EXTENDS NOTHING. It creates a `GeometrySignature` and that is all, because an
extension from outside the owner withdraws standing from everything concluded over
that record - so writing a compilation fact onto a Body staled every construction
statement premised on it, in the ordinary successful flow. The per-body
measurements and the statement-to-feature mapping live on the signature, which
s07 owns outright.

The write boundary is what actually enforces this: these functions build
operations, and `DesignState.validate` refuses any that stray. The fields are
listed in DESIGN_STATE_CONTRACT under `extendable_fields`, which is the only
declaration the runtime reads.

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


def read_features(state, branch: Optional[str] = None) -> List[ir.FeatureSpec]:
    """Every standing feature of the branch, as the IR reads it. A record the
    grammar cannot read is not silently skipped: `embodiment_basis` reports it,
    and the gates refuse on it."""
    out = []
    for rec in sorted(state.standing("Feature"), key=lambda r: r["entity_id"]):
        if branch and not _in_branch(rec, branch):
            continue
        try:
            out.append(ir.FeatureSpec.parse(rec))
        except ir.IRError:
            continue
    return out


def datum_rows(state, branch: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """The s04 spatial commitments a feature may be placed against."""
    rows: Dict[str, List[Dict[str, Any]]] = {}
    for fam in ("Joint", "Envelope", "FunctionalRegion", "RigidGroup", "State", "Transition"):
        rows[fam] = [r for r in sorted(state.standing(fam), key=lambda r: r["entity_id"])
                     if not branch or _in_branch(r, branch)]
    return rows


def reference_scale(state, branch: Optional[str] = None) -> Optional[Dict[str, Any]]:
    scales = [r for r in state.standing("ReferenceScale") if not branch or _in_branch(r, branch)]
    return scales[0] if len(scales) == 1 else None


def known_for(state, branch: Optional[str] = None) -> ir.Known:
    """What a standing record may refer to (declared, not withdrawn)."""
    def declared(family):
        return [r for r in state.family(family)
                if r.get("_validity", "STANDING") != "INVALIDATED"
                and (not branch or _in_branch(r, branch))]
    datums, feature_bodies, datum_bodies, joint_axes = {}, {}, {}, {}
    for fam in ("Joint", "Envelope", "FunctionalRegion", "Feature"):
        for rec in declared(fam):
            datums[rec["entity_id"]] = fam
            if fam == "Joint":
                joint_axes[rec["entity_id"]] = rec.get("axis_direction")
            if fam == "Feature":
                feature_bodies[rec["entity_id"]] = rec.get("body")
            elif fam == "Envelope" and rec.get("body"):
                datum_bodies[rec["entity_id"]] = {rec["body"]}
            elif fam == "FunctionalRegion":
                datum_bodies[rec["entity_id"]] = {b for b in (rec.get("owning_bodies") or [])
                                                  if isinstance(b, str)}
    return ir.Known(parameters={r["entity_id"] for r in declared("Parameter")},
                    datums=datums, feature_bodies=feature_bodies, datum_bodies=datum_bodies,
                    joint_axes=joint_axes,
                    units={r["entity_id"]: r.get("unit") for r in declared("Parameter")
                           if isinstance(r.get("unit"), str) and r.get("unit")})


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
# UNIT F - the embodiment basis, and the two entry gates
# ==========================================================================
def embodiment_basis(state, branch: Optional[str] = None) -> Dict[str, Any]:
    """What of the branch's s05 embodiment currently STANDS, and whether it reads."""
    def mine(family):
        return [r for r in sorted(state.standing(family), key=lambda r: r["entity_id"])
                if not branch or _in_branch(r, branch)]
    basis: Dict[str, Any] = {"branch": branch, "problems": [],
                             "features": [r["entity_id"] for r in mine("Feature")],
                             "parameters": [r["entity_id"] for r in mine("Parameter")],
                             "constraints": [r["entity_id"] for r in mine("Constraint")]}
    known = known_for(state, branch)
    for family, kind in (("Parameter", "parameter"), ("Constraint", "constraint"),
                         ("Feature", "feature")):
        for rec in mine(family):
            basis["problems"] += ir.record_problems(kind, rec, known)
    return basis


def settlement_readiness(state, branch: Optional[str] = None) -> Tuple[bool, List[str]]:
    """May s06 be asked at all? (ready, why not).

    The minimum current basis is the branch's standing construction program:
    without one there is nothing the settled numbers would build, and a solve
    over the empty system would be evidence of nothing. A program whose
    parameters and constraints are absent is a different, legitimate case -
    nothing to settle - and is left to the solver to report as feasible with
    no unknowns. Malformed records that reached state are refused here too.
    """
    basis = embodiment_basis(state, branch)
    problems = list(basis["problems"])
    if not basis["features"]:
        problems.append("no current embodiment (no standing feature) stands for %s; there is "
                        "nothing to settle for" % (branch or "the design"))
        return False, problems
    # UNIT G. AND IT MUST BE CAD-CONSTRUCTIBLE: every body built, every
    # axis-bearing joint placed on each body it relates, every placed feature
    # realized, every stated mating side of its stated kind. The same checks
    # s05 runs on its response, over what actually stands.
    problems += ["EMBODIMENT: " + f.detail for f in prerequisite_findings(state, branch)]
    return (not problems), problems


def prerequisite_findings(state, branch: Optional[str] = None):
    """The mandatory prerequisites of what STANDS, typed and owned.

    The one way from state to those findings: the gate reads it to refuse, and
    the settlement loop reads it to route the refusal to whoever owns the record
    at fault. Reading it twice by two paths is how a gate and a repair round
    come to disagree about what is missing.
    """
    from . import embodiment
    return embodiment.prerequisite_findings(embodiment.rows_from_state(state, branch))


def construction_unit_problems(state, branch: Optional[str] = None) -> List[str]:
    """Every construction parameter and every placement offset must reduce to
    the kernel's unit for its kind; nothing is converted."""
    units = {p.entity_id: p.unit for p in read_parameters(state, branch)}
    expected = {"length": _solver.dim_of_unit(ir.KERNEL_LENGTH_UNIT),
                "angle": _solver.dim_of_unit(ir.KERNEL_ANGLE_UNIT)}
    out: List[str] = []

    def check(where, expr, kind):
        try:
            dim = _solver.reduce_expr(expr, units).dim
        except ir.IRError as exc:
            out.append("%s: %s" % (where, exc))
            return
        if dim != expected[kind]:
            out.append("%s is a %s and must be in %s; it reduces to %s, and no conversion is attempted"
                       % (where, kind, ir.KERNEL_LENGTH_UNIT if kind == "length" else ir.KERNEL_ANGLE_UNIT,
                          _solver.dim_str(dim)))

    for spec in read_features(state, branch):
        for index, expr in enumerate(spec.placement.offset):
            check("%s placement offset[%d]" % (spec.entity_id, index), expr, "length")
        for step in spec.steps:
            kinds = ir.OPCODE_PARAMETER_KINDS.get(step.operation) or {}
            for name, expr in sorted(step.parameters.items()):
                if kinds.get(name):
                    check("%s.%s.%s" % (spec.entity_id, step.step_id, name), expr, kinds[name])
    return out


def scale_and_frames(state, branch: Optional[str] = None):
    """(per_unit, how, frames, findings): the scale authority and every
    feature's derived frame, with what could not be derived named."""
    from . import kinematics

    values = resolved_values(state, branch)
    per_unit, how = kinematics.scale_authority(reference_scale(state, branch), values,
                                               read_parameters(state, branch))
    frames, findings = kinematics.feature_frames(read_features(state, branch),
                                                 datum_rows(state, branch), per_unit, values)
    return per_unit, how, frames, findings


def compilation_readiness(state, branch: Optional[str] = None) -> Tuple[bool, List[str]]:
    """May s07 be entered? (ready, why not).

    A current embodiment that reads; every parameter a feature references
    settled; every standing constraint feasibly settled; every dimension and
    offset in the kernel's unit; every settled number one that builds; a scale
    authority; and every feature's frame derivable from its datum. Anything
    less is refused BEFORE the kernel is asked, and nothing is written.
    """
    from . import settled_geometry

    ready, problems = settlement_readiness(state, branch)
    if not ready:
        return False, problems
    values = resolved_values(state, branch)
    features = read_features(state, branch)
    for ref in sorted({r for f in features for r in f.refs()}):
        if ref not in values:
            problems.append("parameter %s is referenced by the embodiment and has no standing "
                            "settled value; s06 did not settle it and s07 does not choose one" % ref)
    for rec in sorted(state.standing("Constraint"), key=lambda r: r["entity_id"]):
        if branch and not _in_branch(rec, branch):
            continue
        settlement = rec.get("settlement") or {}
        if settlement.get("solver_status") != ir.FEASIBLE:
            problems.append("constraint %s carries no feasible settlement (%s); the system was "
                            "not settled feasible" % (rec["entity_id"],
                                                      settlement.get("solver_status") or "none"))
    problems += construction_unit_problems(state, branch)
    problems += settled_geometry.construction_problems(state, branch)
    problems += settled_geometry.clearance_problems(state, branch)
    per_unit, how, _frames, findings = scale_and_frames(state, branch)
    if per_unit is None:
        problems.append("no scale authority: %s" % how)
    problems += [str(f) for f in findings if f.kind != "NOT_EVALUABLE" or per_unit is not None]
    return (not problems), problems


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
    # THE CONSTRAINTS THE SETTLEMENT RESTED ON. Recorded as premises so a later
    # change to any of them stales the value it produced: `_propagate` walks
    # `_premises`, and a settled value that recorded none could never go stale,
    # which is precisely how an old dimension survives the constraint that
    # justified it.
    system = sorted(set(report.active_set) | set(report.residuals))
    ops: List[Op] = []
    for pid in sorted(report.settled):
        if pid in already:
            continue
        ops.append(Op("EXTEND", "Parameter", pid,
                      {"value": report.settled[pid], "solved_by": evidence_id},
                      S06_PROVENANCE, premise_refs=list(system)))
    for cid in system:
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
    """Read the features, the settled values, the derived frames and the
    declared polarity, and compile. No writes."""
    from . import embodiment

    per_unit, how, frames, findings = scale_and_frames(state, branch)
    blocking = [str(f) for f in findings if f.evaluable]
    if per_unit is None or blocking:
        return _compiler.CompileResult(ok=False, problems=(["no scale authority: %s" % how]
                                                          if per_unit is None else []) + blocking)
    return _compiler.compile_embodiment(read_features(state, branch), resolved_values(state, branch),
                                        frames, embodiment.polarity_table(), out_dir=out_dir)


def compilation_operations(result: _compiler.CompileResult,
                           signature_id: str,
                           values_used: Optional[Sequence[str]] = None) -> List[Op]:
    """What compiling recorded, as one CREATE inside s07's declared authority.

    s07 creates a GeometrySignature and extends NOTHING. It writes no engineering
    decision because it made none, and it writes nothing onto upstream entities
    because doing so staled them: an extension from outside the owner withdraws
    standing from everything concluded over that record, so recording a
    compilation fact on a Body invalidated every construction statement premised
    on it. The facts live on the signature, which s07 owns outright.

    A failed compile writes NOTHING. There is no partial signature and no
    half-registered artifact, because an artifact that exists in state is read as
    current.
    """
    if not result.ok or not result.signature:
        return []
    # The settled parameters and statements the geometry was compiled FROM.
    # These are the premises that make a re-solve or a program change stale the
    # geometry rather than leaving an old solid looking authoritative.
    # UNIT G. EVERY feature composed into a body, the bodies, and every settled
    # value the geometry was compiled from are premises: a revised feature, a
    # re-solved value or a changed body stales the signature by the ordinary
    # rule.
    compiled_from = sorted({fid for b in result.bodies for fid in b.feature_map}
                           | {b.body_id for b in result.bodies}
                           | set(values_used or ()))
    feature_map = {fid: b.body_id for b in result.bodies for fid in b.feature_map}
    return [Op("CREATE", "GeometrySignature", signature_id, {
        "signature_sha256": result.signature["signature_sha256"],
        "per_body": result.signature["per_body"],
        "critical_dimensions": result.signature["critical_dimensions"],
        "feature_map": feature_map,
        "compiled_bodies": [b.as_record() for b in
                            sorted(result.bodies, key=lambda x: x.body_id)]},
        S07_PROVENANCE, premise_refs=compiled_from)]


def signature_identity(result: _compiler.CompileResult) -> str:
    """Derived from the geometry, so an identical rebuild registers identically."""
    digest = (result.signature or {}).get("signature_sha256", "")
    return "GSG-%s" % digest[:16]
