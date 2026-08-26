"""THE S05 LOWERING PASS - semantic embodiment to the executable IR.

ONE DIRECTION, ONE PLACE. Everything the provider no longer authors is decided
here, deterministically: canonical ids, construction step ids, step ordering,
the dependency order that puts a child before its consumer, the single terminal
result, the KinematicRealization rows, the Feature/interface attribution, the
canonical expression AST and the derived `Constraint.parameters` list.

IDENTICAL SEMANTIC INPUT PRODUCES IDENTICAL IR. Allocation walks the response
in its declared order and the manifest in its derived order; the solid tree is
walked post-order. Nothing here consults a clock, a hash of prose or a set
iteration order.

IT REFUSES; IT DOES NOT REPAIR. A missing entity reference, a missing
orientation, a missing geometry operand, a missing dimension, a missing
realization participant and a missing interface side are each reported and the
whole response is refused. None of them is invented, and no partial embodiment
is written for a later round to repair.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import duty_manifest, ir, semantic

#: The canonical id prefix production allocates for each family it writes.
ID_PREFIXES = {"Feature": "FEA", "Parameter": "PRM", "Constraint": "CON",
               "KinematicRealization": "KRL", "Realization": "RLZ",
               "UnresolvedDecision": "S5U"}

#: The constraint kinds that GOVERN an interface. `clearance_governance_
#: findings` counts exactly these, so a duty satisfied by any other kind would
#: be a duty not satisfied - which is how a live response named an interface
#: from a DIMENSIONAL constraint and was still refused for ungoverned clearance.
GOVERNING_KINDS = ("CLEARANCE", "INTERFERENCE_FREE")


class LoweringError(ValueError):
    """The response cannot be lowered. Carries every problem, not the first."""

    def __init__(self, problems: Sequence[str]):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


# ==========================================================================
# What the response may refer to
# ==========================================================================
@dataclass(frozen=True)
class UpstreamFacts:
    bodies: Tuple[str, ...]
    datum_family: Dict[str, str]
    datum_bodies: Dict[str, Set[str]]
    joint_axes: Dict[str, str]
    interfaces: Dict[str, Dict[str, Any]]
    polarity: Dict[str, str]
    feature_kinds: Tuple[str, ...]
    discharge: Tuple[str, ...] = ()
    preserve: Tuple[str, ...] = ()
    visible_obligations: Tuple[str, ...] = ()


def facts_from_rows(rows: Dict[str, List[Dict[str, Any]]],
                    discharge: Sequence[str] = (), preserve: Sequence[str] = (),
                    visible_obligations: Sequence[str] = ()) -> UpstreamFacts:
    from ..state.design_state import Contracts
    from .embodiment import polarity_table

    spec = (Contracts().families.get("Feature") or {}).get("field_semantics") or {}
    kinds = tuple((spec.get("feature_kind") or {}).get("values") or ())
    datum_family: Dict[str, str] = {}
    datum_bodies: Dict[str, Set[str]] = {}
    joint_axes: Dict[str, str] = {}
    for family in ("Joint", "Envelope", "FunctionalRegion"):
        for rec in rows.get(family) or []:
            eid = rec.get("entity_id")
            datum_family[eid] = family
            if family == "Joint":
                joint_axes[eid] = str(rec.get("axis_direction") or "")
            elif family == "Envelope" and rec.get("body"):
                datum_bodies[eid] = {rec["body"]}
            elif family == "FunctionalRegion":
                datum_bodies[eid] = {b for b in (rec.get("owning_bodies") or [])
                                     if isinstance(b, str)}
    return UpstreamFacts(
        bodies=tuple(sorted(b.get("entity_id") for b in (rows.get("Body") or [])
                            if b.get("entity_id"))),
        datum_family=datum_family, datum_bodies=datum_bodies, joint_axes=joint_axes,
        interfaces={i.get("entity_id"): i for i in rows.get("Interface") or []},
        polarity=polarity_table(), feature_kinds=kinds,
        discharge=tuple(sorted(discharge)), preserve=tuple(sorted(preserve)),
        visible_obligations=tuple(sorted(visible_obligations)))


# ==========================================================================
# Deterministic id allocation
# ==========================================================================
class Allocator:
    """Canonical ids, lowest unused first, from what state already holds.

    Occupancy is DesignState's whole entity table for the family - validity and
    occupancy are different questions, and an invalidated id is still spent.
    """

    WIDTH = 4

    def __init__(self, occupied: Optional[Dict[str, Iterable[str]]] = None):
        self._used: Dict[str, Set[int]] = {}
        for family, ids in (occupied or {}).items():
            prefix = ID_PREFIXES.get(family)
            if not prefix:
                continue
            for eid in ids or ():
                match = re.match(r"^%s-(\d+)$" % re.escape(prefix), str(eid))
                if match:
                    self._used.setdefault(family, set()).add(int(match.group(1)))

    def take(self, family: str) -> str:
        prefix = ID_PREFIXES[family]
        used = self._used.setdefault(family, set())
        number = 1
        while number in used:
            number += 1
        used.add(number)
        return "%s-%0*d" % (prefix, self.WIDTH, number)


# ==========================================================================
# Expression lowering
# ==========================================================================
def lower_expression(expr: semantic.TypedExpr, params: Dict[str, str]) -> Dict[str, Any]:
    """A typed expression to the canonical AST the solver and kernel read."""
    if expr.kind == semantic.PARAM:
        return {"ref": params[expr.param]}
    if expr.kind == semantic.NUMBER:
        return {"const": expr.value, "unit": expr.unit}
    if expr.kind == semantic.SUM:
        return {"op": "+", "args": [lower_expression(t, params) for t in expr.terms]}
    if expr.kind == semantic.DIFFERENCE:
        return {"op": "-", "args": [lower_expression(expr.left, params),
                                    lower_expression(expr.right, params)]}
    if expr.kind == semantic.NEGATE:
        return {"op": "-", "args": [lower_expression(expr.of, params)]}
    if expr.kind == semantic.SCALE_BY:
        return {"op": "*", "args": [lower_expression(expr.of, params),
                                    {"const": expr.factor, "unit": "1"}]}
    return {"op": "/", "args": [lower_expression(expr.of, params),
                                {"const": expr.factor, "unit": "1"}]}


# ==========================================================================
# Solid tree lowering
# ==========================================================================
def lower_solid(solid: semantic.Solid, params: Dict[str, str]) -> List[Dict[str, Any]]:
    """The feature's material as an ordered step list, post-order.

    A CHILD IS ALWAYS BUILT BEFORE THE STEP THAT CONSUMES IT, because a
    post-order walk emits it first; every step but the root is named as an
    operand by exactly one later step, so the root is the ONE unconsumed result
    and it IS the feature. There is no ordering to get wrong and no terminal to
    declare.

    AT lowers to a turn and then a move, in that order: the material is
    oriented about the feature frame's origin and the oriented material is then
    offset. Stating the order here, once, is what keeps two responses that mean
    the same placement from compiling differently.
    """
    steps: List[Dict[str, Any]] = []

    def emit(operation: str, operands=(), parameters=None, axis=None) -> str:
        step: Dict[str, Any] = {"id": "S%d" % (len(steps) + 1), "operation": operation}
        if operands:
            step["operands"] = list(operands)
        if parameters:
            step["parameters"] = parameters
        if axis:
            step["axis"] = axis
        steps.append(step)
        return step["id"]

    def walk(node: semantic.Solid) -> str:
        if node.shape in semantic.SOLID_PRIMITIVES:
            names, opcode = semantic.SOLID_PRIMITIVES[node.shape]
            return emit(opcode, parameters={
                name: lower_expression(node.lengths[name], params) for name in sorted(names)})
        if node.shape == semantic.AT:
            current = walk(node.children[0])
            if node.turn is not None:
                current = emit("ROTATE", operands=[current], axis=node.turn.axis,
                               parameters={"angle": lower_expression(node.turn.angle, params)})
            if node.offset is not None:
                current = emit("TRANSLATE", operands=[current], parameters={
                    name: lower_expression(expr, params)
                    for name, expr in zip(("dx", "dy", "dz"), node.offset)})
            return current
        operands = [walk(child) for child in node.children]
        opcode = {semantic.COMPOUND: "UNION", semantic.RELIEVED: "CUT",
                  semantic.COMMON: "INTERSECT"}[node.shape]
        return emit(opcode, operands=operands)

    walk(solid)
    return steps


# ==========================================================================
# Validation - the whole response, before any id exists
# ==========================================================================
def validate(response: semantic.SemanticResponse,
             manifest: duty_manifest.EmbodimentDutyManifest,
             facts: UpstreamFacts) -> List[str]:
    """Every duty and every reference, reported together.

    NOTHING IS INFERRED. Realization is read from the assignment the response
    states, never from a feature's name, its axis, its coincidence with a joint
    frame, or a count of features per relation. Coverage is read from each
    assigned feature's own declared body.
    """
    out: List[str] = []
    out += _reference_problems(response, facts)
    out += _realization_problems(response, manifest, facts)
    out += _interface_problems(response, manifest, facts)
    out += _material_problems(response, manifest, facts)
    out += _placement_problems(response, facts)
    out += _parameter_problems(response, manifest)
    out += _constraint_problems(response)
    out += _obligation_problems(response, facts)
    out += _region_problems(response, manifest, facts)
    out += _state_restraint_problems(response, manifest)
    return out


def _region_problems(response, manifest, facts) -> List[str]:
    """FREE SPACE IS OWED MATERIAL THAT IS NOT THERE, and the route to it is
    geometry, not a sentence.

    s04 committing an aperture and s05 filling it with a solid was a complete,
    accepted embodiment that could not work. The duty is generic: a region whose
    declared role EXCLUDES OCCUPANCY must be cleared by each body that owns it,
    and the response says which feature does the clearing. That feature has to
    be able to do it - its kind must REMOVE material and it must be placed ON
    THAT REGION - because a feature elsewhere clears nothing and a prose claim
    clears nothing at all.

    WHETHER IT ACTUALLY CLEARS IT IS SETTLED GEOMETRY'S TO SAY. This is the
    route; the evidence is s07's, against the compiled solid.
    """
    out: List[str] = []
    required = {d.region: d for d in manifest.free_space_regions()}
    stated = set(response.region_assignments)
    for rid in sorted(set(required) - stated):
        duty = required[rid]
        out.append("region_assignments omits %s (%s on %s); its role means the volume must be "
                   "FREE of the owning body's material, and this response says nothing that "
                   "clears it" % (rid, duty.role, ", ".join(duty.owning_bodies)))
    for rid in sorted(stated - set(required)):
        out.append("region_assignments names %s, which owes no free space; a region whose role "
                   "does not exclude occupancy needs no clearing" % rid)
    for rid in sorted(set(required) & stated):
        duty = required[rid]
        sides = response.region_assignments[rid]
        for body in sorted(set(duty.owning_bodies) - set(sides)):
            out.append("region_assignments[%s] says nothing for %s, which owns the region"
                       % (rid, body))
        for body in sorted(set(sides) - set(duty.owning_bodies)):
            out.append("region_assignments[%s] names %s, which does not own the region"
                       % (rid, body))
        for body in sorted(set(sides) & set(duty.owning_bodies)):
            keys = sides[body]
            if not keys:
                out.append("region_assignments[%s][%s] names no feature; nothing clears the "
                           "region" % (rid, body))
                continue
            for key in keys:
                feature = response.feature(key)
                if feature is None:
                    continue
                if feature.body != body:
                    out.append("region_assignments[%s][%s] names feature %s, which is on %s"
                               % (rid, body, key, feature.body))
                    continue
                if facts.polarity.get(feature.feature_kind) != "SUBTRACTIVE":
                    out.append("region_assignments[%s][%s] names feature %s, whose kind %s ADDS "
                               "material; clearing a region takes a feature whose kind removes "
                               "it" % (rid, body, key, feature.feature_kind))
                datum = feature.placement.datum
                if not (datum.kind == semantic.REGION_DATUM and datum.ref == rid):
                    out.append("region_assignments[%s][%s] names feature %s, which is placed on "
                               "%s %s; geometry clears a region by being AT it"
                               % (rid, body, key, datum.kind, datum.ref))
    return out


def _state_restraint_problems(response, manifest) -> List[str]:
    """A LIMIT IS GEOMETRY AT A POSITION.

    Where two restraint duties stand at DIFFERENT coordinates of the same
    joint, the geometry embodying them cannot be the same geometry in the same
    place: one piece of material cannot stop a joint at two positions. This is
    a contradiction visible in the semantic model, so it is refused here rather
    than left for the compiled solid to disprove.

    NO FEATURE NAME IS READ. A stop face, a latch, a shoulder, a pad, a cam
    surface, an end wall and a screw stop all realize this duty; what is
    compared is where the assigned material SITS.
    """
    out: List[str] = []

    def placement_of(key):
        f = response.feature(key)
        if f is None:
            return None
        datum = f.placement.datum
        return (datum.kind, datum.ref, f.placement.axis,
                tuple(_expression_shape(e) for e in f.placement.offset))

    for joint, duties in sorted(manifest.restraints_by_joint().items()):
        by_coordinate: Dict[str, List[Any]] = {}
        for duty in duties:
            by_coordinate.setdefault(str(duty.joint_coordinates.get(joint)), []).append(duty)
        if len(by_coordinate) < 2:
            continue
        signature: Dict[str, Any] = {}
        for coordinate, here in sorted(by_coordinate.items()):
            places = set()
            for duty in here:
                for _body, keys in sorted(
                        response.realization_assignments.get(duty.relation, {}).items()):
                    for key in keys:
                        spot = placement_of(key)
                        if spot is not None:
                            places.add(spot)
            signature[coordinate] = frozenset(places)
        seen: Dict[Any, str] = {}
        for coordinate, places in sorted(signature.items()):
            if not places:
                continue
            if places in seen and seen[places] != coordinate:
                out.append(
                    "the relations that restrain %s at coordinate %s and at coordinate %s are "
                    "embodied by material in exactly the same place; one piece of geometry "
                    "cannot produce a limit at two different positions of the same joint - "
                    "the two limits sit at different coordinates and their geometry has to "
                    "sit at different places too" % (joint, seen[places], coordinate))
            seen[places] = coordinate
    return out


def _expression_shape(expr) -> Any:
    """A comparable shape for an offset component, so two placements can be
    told apart without evaluating anything."""
    if expr.kind == semantic.PARAM:
        return ("param", expr.param)
    if expr.kind == semantic.NUMBER:
        return ("number", expr.value, expr.unit)
    return (expr.kind,) + tuple(
        _expression_shape(c) for c in
        (list(expr.terms) + [expr.left, expr.right, expr.of]) if c is not None)


def _reference_problems(response, facts: UpstreamFacts) -> List[str]:
    out: List[str] = []
    kinds = set(facts.feature_kinds)
    for f in response.features:
        if f.body not in facts.bodies:
            out.append("feature %s is on %s, which is no body of this branch" % (f.key, f.body))
        if kinds and f.feature_kind not in kinds:
            out.append("feature %s declares feature_kind %s, which is not in the declared "
                       "vocabulary %s" % (f.key, f.feature_kind, sorted(kinds)))
    return out


def _realization_problems(response, manifest, facts) -> List[str]:
    """EXACT COVERAGE, TARGET AND SIDE.

    The assignment key set equals the manifest's required targets - no fewer,
    so nothing the design declared goes unembodied, and no more, so nothing is
    claimed for a relation this branch does not carry. Within a target, the
    BODY key set equals the sides the relation relates: a side is now a key
    that must be present rather than a body that has to be spotted missing from
    a flat list, which is how two live responses came to embody one side of a
    restraint and read as complete.
    """
    out: List[str] = []
    required = set(manifest.required_realization_targets())
    stated = set(response.realization_assignments)
    for target in sorted(required - stated):
        duty = manifest.realization(target)
        out.append("realization_assignments omits %s (%s, %s); every declared relation must "
                   "be assigned the features that embody it on each of %s"
                   % (target, duty.family, duty.descriptor, ", ".join(duty.bodies)))
    for target in sorted(stated - required):
        out.append("realization_assignments names %s, which is no relation this branch owes "
                   "an embodiment; what is embodied is s03's to declare" % target)
    for target in sorted(required & stated):
        duty = manifest.realization(target)
        sides = response.realization_assignments[target]
        for body in sorted(set(duty.bodies) - set(sides)):
            out.append("realization_assignments[%s] states no side for %s; the relation "
                       "relates %s and each side owes material"
                       % (target, body, " and ".join(duty.bodies)))
        for body in sorted(set(sides) - set(duty.bodies)):
            out.append("realization_assignments[%s] states a side for %s, which the relation "
                       "does not relate" % (target, body))
        for body in sorted(set(sides) & set(duty.bodies)):
            keys = sides[body]
            if not keys:
                out.append("realization_assignments[%s][%s] assigns no feature; a side "
                           "embodied by no material is a label" % (target, body))
                continue
            for key in keys:
                actual = response.feature_body(key)
                if actual != body:
                    out.append("realization_assignments[%s][%s] names feature %s, which is "
                               "on %s" % (target, body, key, actual))
    return out


def _interface_problems(response, manifest, facts) -> List[str]:
    """Exact interface coverage, exact participant sides, stated mating kinds,
    and a governing Constraint of a kind that actually governs."""
    out: List[str] = []
    required = {d.interface for d in manifest.interfaces}
    stated = set(response.interface_assignments)
    for iid in sorted(required - stated):
        duty = manifest.interface(iid)
        out.append("interface_assignments omits %s (%s between %s); a feature on EACH "
                   "participant body must realize its side"
                   % (iid, duty.interaction_kind, " and ".join(duty.bodies)))
    for iid in sorted(stated - required):
        out.append("interface_assignments names %s, which the selected branch does not carry; "
                   "an interaction is s03's to declare and none may be invented here" % iid)
    seen_feature: Dict[str, List[str]] = {}
    for iid in sorted(required & stated):
        duty = manifest.interface(iid)
        assignment = response.interface_assignments[iid]
        sides = set(assignment.sides)
        for body in sorted(set(duty.bodies) - sides):
            out.append("interface_assignments[%s] realizes no side on %s, which the interface "
                       "involves" % (iid, body))
        for body in sorted(sides - set(duty.bodies)):
            out.append("interface_assignments[%s] names body %s, which the interface does not "
                       "involve" % (iid, body))
        for body in sorted(sides & set(duty.bodies)):
            keys = assignment.sides[body]
            if not keys:
                out.append("interface_assignments[%s] side %s assigns no feature" % (iid, body))
                continue
            for key in keys:
                actual = response.feature_body(key)
                if actual != body:
                    out.append("interface_assignments[%s] side %s names feature %s, which is "
                               "on %s" % (iid, body, key, actual))
                # ONE FEATURE MAY REALIZE SEVERAL INTERACTIONS, and nothing here
                # objects: a rail face carries two carriages, a pin passes
                # through two bores. `Feature.interfaces` is a multi-reference,
                # so the physical feature stays one record.
                seen_feature.setdefault(key, []).append(iid)
            required_kind = duty.required_kind(body)
            if required_kind:
                got = [response.feature(k).feature_kind for k in keys if response.feature(k)]
                if required_kind not in got:
                    out.append("interface %s states a %s on %s; the feature(s) assigned to "
                               "that side are %s"
                               % (iid, required_kind, body, ", ".join(sorted(got)) or "none"))
        governing = assignment.governing_constraint
        if duty.needs_governing_constraint:
            if governing is None:
                out.append("interface %s declares %s and declares no governing Constraint; the "
                           "number that keeps it a %s is owed by this interface"
                           % (iid, duty.interaction_kind, duty.interaction_kind))
            elif governing.kind not in GOVERNING_KINDS:
                out.append("interface %s is governed by a constraint of kind %s; a governing "
                           "constraint is one of %s - a constraint of any other kind names an "
                           "interface without governing it"
                           % (iid, governing.kind, list(GOVERNING_KINDS)))
    return out


def _material_problems(response, manifest, facts) -> List[str]:
    out: List[str] = []
    additive: Dict[str, int] = {}
    for f in response.features:
        if facts.polarity.get(f.feature_kind) == "ADDITIVE":
            additive[f.body] = additive.get(f.body, 0) + 1
    for body in manifest.bodies:
        if not additive.get(body):
            out.append("body %s has no additive feature (no STOCK, boss, rib ...); nothing "
                       "gives it material" % body)
    return out


def _placement_problems(response, facts: UpstreamFacts) -> List[str]:
    """Datums resolve IN THE FAMILY THEY DECLARE, a feature datum shares its
    body and does not cycle, and a datum that lends no orientation is met with
    a stated axis."""
    out: List[str] = []
    keys = {f.key: f for f in response.features}
    for f in response.features:
        datum = f.placement.datum
        if datum.kind == semantic.FEATURE_DATUM:
            other = keys.get(datum.ref)
            if other is None:
                out.append("feature %s is placed on feature %s, which this response does not "
                           "declare" % (f.key, datum.ref))
            elif datum.ref == f.key:
                out.append("feature %s is placed against itself" % f.key)
            elif other.body != f.body:
                out.append("feature %s on %s is placed on feature %s of body %s; a feature is "
                           "placed relative to its own body, and bodies relate through joints"
                           % (f.key, f.body, datum.ref, other.body))
            continue
        expected = semantic.DATUM_FAMILY[datum.kind]
        family = facts.datum_family.get(datum.ref)
        if family is None:
            out.append("feature %s is placed on %s %s, which is no committed %s of this branch"
                       % (f.key, datum.kind, datum.ref, expected))
            continue
        if family != expected:
            out.append("feature %s is placed on %s %s, but %s is a %s; a datum is the kind of "
                       "place it says it is" % (f.key, datum.kind, datum.ref, datum.ref, family))
            continue
        if family == "Joint":
            declared = str(facts.joint_axes.get(datum.ref) or "").strip().upper()
            if ir.axis_vector(declared) is None and f.placement.axis is None:
                out.append("feature %s is placed at joint %s, which declares no axis, and "
                           "names none of its own; a datum LOCATES and an axis ORIENTS"
                           % (f.key, datum.ref))
        bodies = facts.datum_bodies.get(datum.ref)
        if family == "Envelope" and bodies and f.body not in bodies:
            out.append("feature %s on %s is placed on envelope %s of another body"
                       % (f.key, f.body, datum.ref))
    # a chain of feature datums must terminate at a committed datum
    for f in response.features:
        seen, cursor = [f.key], f.placement.datum
        while cursor.kind == semantic.FEATURE_DATUM and cursor.ref in keys:
            if cursor.ref in seen:
                out.append("feature %s is placed on a cycle of features (%s); a chain of "
                           "placements must reach a committed datum"
                           % (f.key, " -> ".join(seen + [cursor.ref])))
                break
            seen.append(cursor.ref)
            cursor = keys[cursor.ref].placement.datum
    return out


def _parameter_problems(response, manifest) -> List[str]:
    """The scale authority, and closure: every parameter is named by some
    constraint, or it is a free direction nothing can be built from."""
    out: List[str] = []
    scale_keys = [k for k, d in sorted(response.parameters.items())
                  if d.get("role") == duty_manifest.SCALE_ROLE]
    if manifest.scale.required and len(scale_keys) != 1:
        out.append("the arrangement basis is %s, which owes EXACTLY ONE parameter with role "
                   "%s; this response declares %d"
                   % (manifest.scale.basis, duty_manifest.SCALE_ROLE, len(scale_keys)))
    if not manifest.scale.required and scale_keys:
        out.append("the arrangement basis is %s, which owes no scale parameter; this response "
                   "declares %s" % (manifest.scale.basis or "unstated", ", ".join(scale_keys)))
    for key, declared in sorted(response.parameters.items()):
        if declared.get("role") == duty_manifest.SCALE_ROLE \
                and declared.get("unit") != ir.KERNEL_LENGTH_UNIT:
            out.append("parameter %s declares role %s in %r; a scale is kernel length units "
                       "(%s) per basis unit"
                       % (key, duty_manifest.SCALE_ROLE, declared.get("unit"),
                          ir.KERNEL_LENGTH_UNIT))
    determined: Set[str] = set()
    for c in response.all_constraints():
        determined |= set(c.refs())
    for key, declared in sorted(response.parameters.items()):
        if key not in determined:
            out.append("parameter %s (%s) is named by no constraint; a parameter no "
                       "constraint determines is a free direction the solver reports back and "
                       "nothing can be built from it" % (key, declared.get("symbol")))
    return out


def _constraint_problems(response) -> List[str]:
    """ONE dimension on both sides, and no definition cycle."""
    from . import solver

    out: List[str] = []
    units = {k: d.get("unit") for k, d in response.parameters.items()}
    params = {k: k for k in response.parameters}
    for index, c in enumerate(response.all_constraints()):
        expr = {"relation": c.relation,
                "lhs": lower_expression(c.lhs, params),
                "rhs": lower_expression(c.rhs, params)}
        out += ["constraint[%d] (%s) %s" % (index, c.kind, p)
                for p in solver.dimension_problems(expr, units)]
    defines: Dict[str, Set[str]] = {}
    for c in response.all_constraints():
        if c.relation != "==":
            continue
        lhs = set(c.lhs.refs())
        if len(lhs) != 1:
            continue
        defines.setdefault(next(iter(lhs)), set()).update(c.rhs.refs())
    for start in sorted(defines):
        seen, frontier = set(), [start]
        while frontier:
            cursor = frontier.pop()
            for nxt in sorted(defines.get(cursor, ())):
                if nxt == start:
                    out.append("parameter %s participates in a definition cycle" % start)
                    frontier = []
                    break
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
    return sorted(set(out))


def _obligation_problems(response, facts: UpstreamFacts) -> List[str]:
    out: List[str] = []
    applicable = set(facts.discharge) | set(facts.preserve)
    cited: Set[str] = set()
    for index, r in enumerate(response.realizations):
        cited |= set(r.addresses_obligations)
        for oid in sorted(set(r.addresses_obligations) - applicable):
            out.append("realizations[%d] claims to discharge %s, which does not apply to the "
                       "selected candidate%s"
                       % (index, oid,
                          "" if oid in facts.visible_obligations
                          else " and is not in this view at all"))
        for oid in sorted(set(r.addresses_obligations) & set(facts.preserve)):
            out.append("realizations[%d] cites %s as discharged, but the selected branch's "
                       "upstream records already discharged it; embodiment preserves it and "
                       "may not claim it" % (index, oid))
    for oid in sorted(set(facts.discharge) - cited):
        out.append("obligation %s is embodiment's to discharge and is cited by no realization"
                   % oid)
    return out


# ==========================================================================
# Lowering
# ==========================================================================
@dataclass
class LoweredEmbodiment:
    """The canonical records production writes, and the key map that made them."""

    features: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    kinematic_realizations: List[Dict[str, Any]] = field(default_factory=list)
    realizations: List[Dict[str, Any]] = field(default_factory=list)
    unresolved: List[Dict[str, Any]] = field(default_factory=list)
    keys: Dict[str, str] = field(default_factory=dict)

    def as_rows(self) -> Dict[str, List[Dict[str, Any]]]:
        """The lowered records under their canonical family names, so the SAME
        structural checks the settlement gate runs over standing state run over
        this proposal before it is written."""
        return {"Feature": list(self.features), "Parameter": list(self.parameters),
                "Constraint": list(self.constraints),
                "KinematicRealization": list(self.kinematic_realizations),
                "Realization": list(self.realizations)}


def lower(response: semantic.SemanticResponse,
          manifest: duty_manifest.EmbodimentDutyManifest,
          facts: UpstreamFacts,
          occupied: Optional[Dict[str, Iterable[str]]] = None) -> LoweredEmbodiment:
    """Validate, then build every canonical record. Raises rather than writing
    a partial embodiment."""
    problems = validate(response, manifest, facts)
    if problems:
        raise LoweringError(problems)

    allocator = Allocator(occupied)
    out = LoweredEmbodiment()

    # PARAMETERS FIRST: every expression below resolves through them. The set
    # is the union of the declarations the references carried, in key order, so
    # allocation does not depend on where a name happened to appear.
    param_ids: Dict[str, str] = {}
    for key, declared in sorted(response.parameters.items()):
        pid = allocator.take("Parameter")
        param_ids[key] = pid
        record: Dict[str, Any] = {"entity_id": pid, "symbol": declared.get("symbol") or key,
                                  "unit": declared.get("unit"), "status": ir.DECLARED}
        if declared.get("role"):
            record["role"] = declared["role"]
        out.parameters.append(record)

    # FEATURES, in declared order. A feature datum naming another feature is
    # resolved after every id exists, so a forward reference is ordinary.
    feature_ids: Dict[str, str] = {}
    for f in response.features:
        feature_ids[f.key] = allocator.take("Feature")

    # ONE PHYSICAL FEATURE, EVERY INTERACTION IT BEARS ON. `Feature.interfaces`
    # is a multi-reference, so a rail face under two carriages is one record
    # naming two interfaces rather than two records for one face.
    interfaces_of: Dict[str, List[str]] = {}
    for iid, assignment in sorted(response.interface_assignments.items()):
        for _body, keys in sorted(assignment.sides.items()):
            for key in keys:
                named = interfaces_of.setdefault(key, [])
                if iid not in named:
                    named.append(iid)

    for f in response.features:
        datum = f.placement.datum
        placement: Dict[str, Any] = {
            "datum": (feature_ids[datum.ref] if datum.kind == semantic.FEATURE_DATUM
                      else datum.ref),
            "offset": [lower_expression(e, param_ids) for e in f.placement.offset]}
        if f.placement.axis:
            placement["axis"] = f.placement.axis
        record = {"entity_id": feature_ids[f.key], "body": f.body,
                  "feature_kind": f.feature_kind, "geometry": f.geometry,
                  "placement": placement,
                  "construction": lower_solid(f.solid, param_ids)}
        if f.key in interfaces_of:
            record["interfaces"] = list(interfaces_of[f.key])
        out.features.append(record)

    # CONSTRAINTS. `parameters` is DERIVED from the expression - one authority,
    # and the two can no longer disagree because there is no second statement.
    # A GOVERNING constraint is written from the interface assignment it was
    # declared in, so it governs exactly that interface and no other record can
    # claim to speak for a second one.
    def constraint_record(c, governs=None):
        cid = allocator.take("Constraint")
        expression = {"relation": c.relation,
                      "lhs": lower_expression(c.lhs, param_ids),
                      "rhs": lower_expression(c.rhs, param_ids)}
        record = {"entity_id": cid, "expression": expression, "kind": c.kind,
                  "parameters": sorted({param_ids[r] for r in c.refs()})}
        if c.basis:
            record["basis"] = c.basis
        if governs:
            record["governs_interface"] = governs
        return record

    for c in response.constraints:
        out.constraints.append(constraint_record(c))
    for iid, assignment in sorted(response.interface_assignments.items()):
        if assignment.governing_constraint is not None:
            out.constraints.append(
                constraint_record(assignment.governing_constraint, governs=iid))

    # KINEMATIC REALIZATIONS. Production allocates the id and writes ONE row per
    # required target, in the manifest's derived order. The model chose which
    # features embody the relation and nothing else about the record.
    for duty in manifest.realizations:
        sides = response.realization_assignments[duty.target]
        # FLATTENED IN THE MANIFEST'S SIDE ORDER, so the participant list of a
        # relation does not depend on the order the response happened to state
        # its sides in. The canonical record is unchanged: one list of features.
        participating: List[str] = []
        for body in duty.bodies:
            for key in sides.get(body, ()):
                fid = feature_ids[key]
                if fid not in participating:
                    participating.append(fid)
        out.kinematic_realizations.append({
            "entity_id": allocator.take("KinematicRealization"),
            "realizes": duty.target,
            "participating_features": participating})

    for r in response.realizations:
        out.realizations.append({
            "entity_id": allocator.take("Realization"),
            "addresses_obligations": list(r.addresses_obligations),
            "participating_features": [feature_ids[k] for k in r.participating_features],
            "verification_predicate": r.verification_predicate})

    for u in response.unresolved:
        record = {k: v for k, v in u.items() if k != "id"}
        record["entity_id"] = allocator.take("UnresolvedDecision")
        out.unresolved.append(record)

    out.keys = dict(param_ids)
    out.keys.update(feature_ids)
    return out
