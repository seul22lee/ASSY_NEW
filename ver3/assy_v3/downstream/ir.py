"""The typed representations s05 authors and s06/s07 consume.

WHY A TYPED IR AT ALL

`Constraint.expression` and `ConstructionStatement.operation`/`operands` are
required fields in DESIGN_STATE_CONTRACT, and the contract does not say what may
go in them. Left as free text they would be interpreted twice - once by whoever
wrote them and once by whoever reads them - and S06's contract forbids exactly
that outcome: it may not "defer a symbolic expression to CAD" (R-22) and may not
report `unsupported_formulation` by accident because a string parsed differently
than intended.

So the shapes below are the smallest typed forms that make deterministic
interpretation possible. They are JSON-representable because they live inside
DesignState entities, and they are validated on the way in rather than trusted.

WHAT IS DELIBERATELY NOT HERE

No symbolic algebra language. No solver of general nonlinear systems. The
repository's constraint population is envelope and clearance arithmetic over
declared layout parameters - "a pin of radius r needing a wall w gives a boss
radius r+w" - and the IR covers that exactly. A formulation outside it is
reported `unsupported_formulation`, which is a contract status, not a failure to
be worked around.

EVERY QUANTITY CARRIES A UNIT

INV-004 and R-21: a null unit is a schema error and s06 may not default one. The
unit therefore lives on the declaration and on every literal, and unit agreement
is checked structurally rather than assumed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

# ==========================================================================
# Solver IR
# ==========================================================================

#: The relations a constraint may assert. Equality settles a value; the
#: inequalities bound one. Nothing else is admitted, because nothing else
#: appears in the declared constraint population.
RELATIONS = ("==", "<=", ">=")

#: The arithmetic a constraint expression may use. Deliberately four operators:
#: envelope and clearance constraints are sums, differences and scalings of
#: declared lengths, and an operator nobody needs is an operator whose semantics
#: nobody has agreed.
ARITHMETIC = ("+", "-", "*", "/")

#: What s06 may report. Frozen by S06_CONTRACT.structured_outputs.solver_status.
FEASIBLE = "feasible"
INFEASIBLE = "infeasible"
UNDERDETERMINED = "underdetermined"
UNSUPPORTED_FORMULATION = "unsupported_formulation"
SOLVER_FAILURE = "solver_failure"
#: UNIT F. The settlement was asked of a branch with no current embodiment
#: program to settle for. Distinct from a system that has no unknowns - which
#: is FEASIBLE with `unknown_count` 0 - and reported before any solving, so an
#: absent s05 output can never be read as an empty problem that solved.
NOT_READY = "not_ready"
SOLVER_STATUSES = (FEASIBLE, INFEASIBLE, UNDERDETERMINED,
                   UNSUPPORTED_FORMULATION, SOLVER_FAILURE, NOT_READY)

#: Parameter value states. DECLARED is what s05 may author; SOLVED is what s06
#: may write and only with a cited solver artifact (S05-C10).
DECLARED = "DECLARED"
SOLVED = "SOLVED"
FREE = "FREE"
PARAMETER_STATUSES = (DECLARED, SOLVED, FREE)


class IRError(ValueError):
    """A malformed IR value. Reported, never repaired."""


@dataclass(frozen=True)
class Expr:
    """One node of a constraint expression.

    Exactly one of `ref`, `const` or `op` is set. A node that sets none or more
    than one is not an ambiguous expression to be resolved by precedence - it is
    a malformed one, and it is rejected here rather than interpreted downstream.
    """

    ref: Optional[str] = None
    const: Optional[float] = None
    unit: Optional[str] = None
    op: Optional[str] = None
    args: Tuple["Expr", ...] = ()

    @staticmethod
    def parse(node: Any) -> "Expr":
        if not isinstance(node, dict):
            raise IRError("expression node is %s, not an object" % type(node).__name__)
        kinds = [k for k in ("ref", "const", "op") if node.get(k) is not None]
        if len(kinds) != 1:
            raise IRError("expression node must set exactly one of ref/const/op; "
                          "it sets %s" % (kinds or "none"))
        kind = kinds[0]
        if kind == "ref":
            if not isinstance(node["ref"], str):
                raise IRError("ref must be a parameter id")
            return Expr(ref=node["ref"])
        if kind == "const":
            unit = node.get("unit")
            if not unit:
                # INV-004 at the leaf. A literal without a unit is the defaulting
                # this whole layer exists to prevent, one level below where R-21
                # noticed it.
                raise IRError("literal %r declares no unit" % node["const"])
            try:
                return Expr(const=float(node["const"]), unit=str(unit))
            except (TypeError, ValueError):
                raise IRError("literal %r is not a number" % node["const"])
        if node["op"] not in ARITHMETIC:
            raise IRError("operator %r is not one of %s"
                          % (node["op"], list(ARITHMETIC)))
        args = node.get("args")
        # UNIT G. `-` with ONE argument is negation - a placement below the
        # frame origin, an offset the other way. A language of placements that
        # cannot say "minus this" makes the model spell it as 0 - x or -1 * x,
        # and a live response wrote the natural form instead. Every other
        # operator, and `-` as subtraction, still needs two.
        minimum = 1 if node["op"] == "-" else 2
        if not isinstance(args, list) or len(args) < minimum:
            raise IRError("operator %r needs at least %s argument%s"
                          % (node["op"], "one" if minimum == 1 else "two",
                             "" if minimum == 1 else "s"))
        return Expr(op=node["op"], args=tuple(Expr.parse(a) for a in args))

    def refs(self) -> Set[str]:
        if self.ref is not None:
            return {self.ref}
        return {r for a in self.args for r in a.refs()}

    def as_dict(self) -> Dict[str, Any]:
        if self.ref is not None:
            return {"ref": self.ref}
        if self.const is not None:
            return {"const": self.const, "unit": self.unit}
        return {"op": self.op, "args": [a.as_dict() for a in self.args]}


@dataclass(frozen=True)
class ParameterDecl:
    """A declared layout quantity. `unit` is mandatory and never defaulted."""

    entity_id: str
    symbol: str
    unit: str
    status: str
    value: Optional[float] = None
    lower: Optional[float] = None
    upper: Optional[float] = None
    #: UNIT G. What the parameter IS for the arrangement: "SCALE" - kernel
    #: length units per basis unit - is the one role, and the one scale
    #: authority s05 may declare for a RELATIVE basis.
    role: Optional[str] = None
    solved_by: Optional[str] = None

    @staticmethod
    def parse(record: Dict[str, Any]) -> "ParameterDecl":
        unit = record.get("unit")
        if not unit:
            raise IRError("Parameter %s declares no unit (INV-004)"
                          % record.get("entity_id"))
        status = record.get("status")
        if status not in PARAMETER_STATUSES:
            raise IRError("Parameter %s status %r is not one of %s"
                          % (record.get("entity_id"), status,
                             list(PARAMETER_STATUSES)))
        return ParameterDecl(
            entity_id=record["entity_id"], symbol=record.get("symbol") or "",
            unit=str(unit), status=status, value=record.get("value"),
            lower=record.get("lower"), upper=record.get("upper"),
            solved_by=record.get("solved_by"),
            role=(str(record.get("role")).upper() if record.get("role") else None))


@dataclass(frozen=True)
class TypedConstraint:
    """One relation over declared parameters."""

    entity_id: str
    relation: str
    lhs: Expr
    rhs: Expr
    kind: str = ""

    @staticmethod
    def parse(record: Dict[str, Any]) -> "TypedConstraint":
        expr = record.get("expression")
        if not isinstance(expr, dict):
            raise IRError("Constraint %s expression is not an object"
                          % record.get("entity_id"))
        relation = expr.get("relation")
        if relation not in RELATIONS:
            raise IRError("Constraint %s relation %r is not one of %s"
                          % (record.get("entity_id"), relation, list(RELATIONS)))
        return TypedConstraint(
            entity_id=record["entity_id"], relation=relation,
            lhs=Expr.parse(expr.get("lhs")), rhs=Expr.parse(expr.get("rhs")),
            kind=record.get("kind") or "")

    def refs(self) -> Set[str]:
        return self.lhs.refs() | self.rhs.refs()


# ==========================================================================
# Construction IR
# ==========================================================================

#: THE OPCODE VOCABULARY, and it is closed.
#:
#: Every entry is a shape-producing or shape-combining operation that a kernel
#: performs without deciding anything. There is no opcode that places a body in
#: the world: S05_CONTRACT's construction_frame_rule requires every statement to
#: be expressed in the OWNING BODY'S OWN FRAME, and INV-006 keeps the pose law
#: out of s07 entirely. TRANSLATE and ROTATE therefore position FEATURES within
#: a body, never bodies within an assembly.
OPCODES = {
    "BOX": ("dx", "dy", "dz"),
    "CYLINDER": ("radius", "height"),
    "SPHERE": ("radius",),
    "TRANSLATE": ("dx", "dy", "dz"),
    "ROTATE": ("angle",),
    "UNION": (),
    "CUT": (),
    "INTERSECT": (),
}

#: Opcodes that consume prior results rather than producing a primitive.
COMBINING = ("UNION", "CUT", "INTERSECT")
TRANSFORMING = ("TRANSLATE", "ROTATE")

#: UNIT F. THE EXECUTION SEMANTICS OF EVERY OPCODE, stated once. s07 executes
#: exactly these; a statement whose author meant something else did not say
#: so. Every primitive is placed against the OWNING BODY'S OWN FRAME, whose
#: origin is a coordinate definition and not a dimension - which is why a
#: coordinate at the origin is written as the typed zero of the frame's unit,
#: `{"const": 0, "unit": "mm"}`, and never as a bare number.
KERNEL_LENGTH_UNIT = "mm"
KERNEL_ANGLE_UNIT = "deg"
#: A PRIMITIVE IS BUILT IN THE FRAME OF THE FEATURE IT REALIZES (Unit G): the
#: frame's Z is the feature's placement axis, its X the reference, its origin
#: the placement origin. A primitive naming no placed feature is built in the
#: body frame itself. Either way "the frame origin" below means that frame's.
OPCODE_SEMANTICS = {
    "BOX": "the solid [0,dx] x [0,dy] x [0,dz] from the frame origin",
    "CYLINDER": "the solid of radius r, axis +Z of the frame from z=0 to z=height, "
                "centred on the frame origin in X and Y",
    "SPHERE": "the solid of radius r centred on the frame origin",
    "TRANSLATE": "the operand moved by (dx, dy, dz) in the feature frame; an omitted "
                 "component is zero",
    "ROTATE": "the operand rotated by angle (degrees) about the named body axis "
              "through the frame origin",
    "UNION": "the operands fused - all of them steps of THIS feature",
    "CUT": "the first operand with every later operand removed - all of them steps of THIS "
           "feature; never the body, which no step names",
    "INTERSECT": "the common volume of the operands",
}

#: UNIT G. WHAT A FEATURE'S CONSTRUCTION IS, and what it is NOT.
#:
#: THE ONE STATEMENT OF IT. `compiler.build_feature` executes the steps and
#: `compile_embodiment` composes bodies by polarity; s05 is shown this text and
#: the contracts point at it, so the language the model writes in, the boundary
#: enforces, and the kernel executes are one language.
#:
#: The distinction it draws is the one a subtractive feature gets wrong: a bore
#: is A CYLINDER, positively constructed, and it is its KIND that removes it
#: from the body. Writing CUT inside it to mean "take this out of the body" asks
#: a feature-local operation to reach the body, which no step can do - the body
#: is not an operand and is never in scope. Such a step is malformed however it
#: is written, and a single-operand CUT is refused on arity before its intent
#: can even be read.
CONSTRUCTION_SEMANTICS = (
    "A FEATURE'S CONSTRUCTION BUILDS ITS OWN SOLID, and that solid is ALWAYS POSITIVE "
    "material - the shape of the thing itself. A bore is the cylinder that will be removed, "
    "constructed as a cylinder; a boss is the cylinder that will be added, constructed the "
    "same way. WHETHER IT IS ADDED OR REMOVED IS ITS KIND, not a step: the body is the union "
    "of its ADDITIVE features with its SUBTRACTIVE features removed, and that composition "
    "happens at the BODY, after every feature is built. "
    "CUT, UNION and INTERSECT are FEATURE-LOCAL CSG: they shape this feature's own solid out "
    "of two or more of ITS OWN earlier steps - a bore with a relief, a boss with a flat. Each "
    "needs at least two operands, because that is what combining two solids means. A "
    "SUBTRACTIVE feature must NOT write CUT to mean \"remove this from the body\": the body "
    "is not an operand, no step may name it, and its kind has already said so.")
#: What each opcode parameter IS, so a value in the wrong unit is refused
#: rather than fed to a kernel that assumes millimetres and degrees.
OPCODE_PARAMETER_KINDS = {
    "BOX": {"dx": "length", "dy": "length", "dz": "length"},
    "CYLINDER": {"radius": "length", "height": "length"},
    "SPHERE": {"radius": "length"},
    "TRANSLATE": {"dx": "length", "dy": "length", "dz": "length"},
    "ROTATE": {"angle": "angle"},
    "UNION": {}, "CUT": {}, "INTERSECT": {},
}

#: UNIT G. THE ONE TABLE OF NAMED AXES. s03 declares a joint's axis as one of
#: these, s04 rotates about it, an Interface's mating geometry names it, a
#: feature's placement is stated in it, and s07 maps a primitive onto it. It
#: used to be written four times (s03.AXIS_DIRECTIONS, s04.AXIS_INDEX +
#: AXIS_VECTORS, the mating-geometry enum, and the unsigned list below); the
#: stage modules now re-export this one.
AXIS_VECTORS = {"+X": (1.0, 0.0, 0.0), "-X": (-1.0, 0.0, 0.0),
                "+Y": (0.0, 1.0, 0.0), "-Y": (0.0, -1.0, 0.0),
                "+Z": (0.0, 0.0, 1.0), "-Z": (0.0, 0.0, -1.0)}
SIGNED_AXES = tuple(AXIS_VECTORS)
AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
#: ROTATE needs an axis; it is the one transform with a direction, and naming it
#: in the statement rather than inferring it is what keeps s07 from choosing one.
#: Unsigned: the sign of a rotation is the sign of its angle.
AXES = tuple(AXIS_INDEX)


def axis_vector(axis: Any) -> Optional[Tuple[float, float, float]]:
    """The unit vector a signed axis name denotes, or None. None is an answer:
    a missing or unrecognised axis is never read as Z."""
    if not isinstance(axis, str):
        return None
    return AXIS_VECTORS.get(axis.strip().upper())


def frame_axes(axis: str) -> Tuple[Tuple[float, float, float], Tuple[float, float, float],
                                   Tuple[float, float, float]]:
    """(x, y, z) unit vectors of the frame whose Z is the named axis.

    X is the canonical perpendicular - the next arrangement axis in cyclic
    order (Z->X, X->Y, Y->Z), positive - and Y completes a right-handed frame.
    One rule, so the orientation of a placed primitive is never a decision.
    """
    z = axis_vector(axis)
    if z is None:
        raise IRError("axis %r is not one of %s" % (axis, list(SIGNED_AXES)))
    letter = axis.strip().upper()[-1]
    x = AXIS_VECTORS["+" + {"Z": "X", "X": "Y", "Y": "Z"}[letter]]
    y = (z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0])
    return x, y, z


# ==========================================================================
# UNIT G. PLACEMENT - where a feature is, RELATIVE TO WHAT S04 COMMITTED.
#
# THE ONE SPATIAL AUTHORITY is s04's arrangement frame: joint frames
# (frame_origin + axis_direction), body envelopes, functional regions, all in
# the ReferenceScale basis. Every body frame COINCIDES with that frame at zero
# joint coordinates. A feature is placed by naming a DATUM in that authority -
# a Joint, the body's Envelope, a FunctionalRegion, or another feature of the
# same body - plus an `offset` (three expressions in the kernel length unit,
# along the arrangement axes) and its own `axis`. A joint datum's axis IS the
# joint's declared axis_direction: stating it is redundant and must agree;
# stating a different one is a second truth and is refused. An envelope or a
# region is an axis-aligned box in the arrangement frame, so its frame IS the
# arrangement frame: a feature placed against one that names no axis takes
# the arrangement's +Z. A feature placed against another feature inherits
# that feature's axis unless it names its own.
#
# The feature frame: origin = datum point x scale + offset; Z along the axis;
# X along the canonical perpendicular (`frame_axes`). The scale - kernel units
# per basis unit - is the ReferenceScale's authority (ABSOLUTE per_unit, or a
# settled scale parameter), resolved by downstream.kinematics; nothing here
# reads a number that was not committed or settled.
# ==========================================================================
DATUM_FAMILIES = ("Joint", "Envelope", "FunctionalRegion", "Feature")


@dataclass(frozen=True)
class Placement:
    datum: str
    offset: Tuple[Expr, Expr, Expr]
    axis: Optional[str] = None            # None: taken from the joint datum

    @staticmethod
    def parse(node: Any, where: str = "placement") -> "Placement":
        if not isinstance(node, dict):
            raise IRError("%s is not an object" % where)
        datum = node.get("datum")
        if not isinstance(datum, str) or not datum.strip():
            raise IRError("%s names no datum; a feature is placed relative to a joint, "
                          "its body's envelope, a region or another feature" % where)
        raw = node.get("offset")
        if raw is None:
            raw = [{"const": 0.0, "unit": KERNEL_LENGTH_UNIT}] * 3
        if not isinstance(raw, list) or len(raw) != 3:
            raise IRError("%s offset is not three expressions" % where)
        exprs = []
        for index, component in enumerate(raw):
            if isinstance(component, bool) or isinstance(component, (int, float)):
                raise IRError("%s offset[%d] is a bare number (%r); a coordinate is a "
                              "declared parameter or a unit-bearing constant"
                              % (where, index, component))
            exprs.append(Expr.parse(component))
        axis = node.get("axis")
        if axis is not None and axis_vector(axis) is None:
            raise IRError("%s axis %r is not one of %s" % (where, axis, list(SIGNED_AXES)))
        unknown = sorted(set(node) - {"datum", "offset", "axis"})
        if unknown:
            raise IRError("%s carries %s, which a placement does not have" % (where, unknown))
        return Placement(datum=datum.strip(), offset=(exprs[0], exprs[1], exprs[2]),
                         axis=axis.strip().upper() if isinstance(axis, str) else None)

    def refs(self) -> Set[str]:
        return {r for e in self.offset for r in e.refs()}


# ==========================================================================
# UNIT G. CONSTRUCTION IS THE FEATURE'S. A feature carries the ordered steps
# that build its solid, in its own frame; the one step nothing consumes IS the
# feature. A body is composed from its features by kind polarity (declared in
# the contract): additive features fused, subtractive features removed. There
# is no construction a feature does not own, so placement, role, dimensions
# and construction trace to one record.
# ==========================================================================
@dataclass(frozen=True)
class Step:
    """One construction step of a feature, in the feature's frame."""

    step_id: str
    operation: str
    operands: Tuple[str, ...]
    parameters: Dict[str, Expr]
    axis: Optional[str] = None

    @staticmethod
    def parse(record: Dict[str, Any], where: str = "step") -> "Step":
        if not isinstance(record, dict):
            raise IRError("%s is not an object" % where)
        sid = record.get("id")
        if not isinstance(sid, str) or not sid.strip():
            raise IRError("%s has no id" % where)
        op = record.get("operation")
        if op not in OPCODES:
            raise IRError("%s %s operation %r is not in the opcode vocabulary %s"
                          % (where, sid, op, sorted(OPCODES)))
        operands = tuple(record.get("operands") or ())
        if any(not isinstance(o, str) for o in operands):
            raise IRError("%s %s operands must be step ids" % (where, sid))
        if op in COMBINING and len(operands) < 2:
            raise IRError("%s %s: %s combines %d operands; it needs at least two"
                          % (where, sid, op, len(operands)))
        if op in TRANSFORMING and len(operands) != 1:
            raise IRError("%s %s: %s transforms %d operands; it needs exactly one"
                          % (where, sid, op, len(operands)))
        if op not in COMBINING and op not in TRANSFORMING and operands:
            raise IRError("%s %s: %s is a primitive and takes no operands" % (where, sid, op))
        raw = record.get("parameters")
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise IRError("%s %s parameters is not an object of named expressions"
                          % (where, sid))
        params = {k: Expr.parse(v) for k, v in raw.items()}
        if op == "TRANSLATE":
            # A move along one axis is written with that component alone: an
            # omitted translation component is the identity along its axis -
            # the typed zero - not a dimension anyone left undecided.
            for k in OPCODES[op]:
                params.setdefault(k, Expr(const=0.0, unit=KERNEL_LENGTH_UNIT))
        missing = [k for k in OPCODES[op] if k not in params]
        if missing:
            raise IRError("%s %s: %s omits required parameter(s) %s" % (where, sid, op, missing))
        extra = sorted(set(params) - set(OPCODES[op]))
        if extra:
            raise IRError("%s %s: %s takes no parameter %s" % (where, sid, op, extra))
        axis = record.get("axis")
        if op == "ROTATE" and axis not in AXES:
            raise IRError("%s %s: ROTATE declares axis %r; it must be one of %s"
                          % (where, sid, axis, list(AXES)))
        return Step(step_id=sid.strip(), operation=op, operands=operands, parameters=params,
                    axis=axis)

    def refs(self) -> Set[str]:
        return {r for e in self.parameters.values() for r in e.refs()}


@dataclass(frozen=True)
class FeatureSpec:
    """A Feature record as the deterministic downstream reads it: role,
    placement and construction, one record, one grammar."""

    entity_id: str
    body: str
    kind: str
    placement: Placement
    steps: Tuple[Step, ...]
    interface: Optional[str] = None

    @staticmethod
    def parse(record: Dict[str, Any]) -> "FeatureSpec":
        eid = record.get("entity_id") or record.get("id")
        where = "feature %s" % eid
        body = record.get("body")
        if not isinstance(body, str) or not body:
            raise IRError("%s names no body" % where)
        kind = record.get("feature_kind")
        if not isinstance(kind, str) or not kind:
            raise IRError("%s names no feature_kind" % where)
        placement = Placement.parse(record.get("placement"), "%s placement" % where)
        raw_steps = record.get("construction")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise IRError("%s has no construction; a feature that builds nothing is not "
                          "an embodiment" % where)
        steps = []
        seen: Set[str] = set()
        for index, raw in enumerate(raw_steps):
            step = Step.parse(raw, "%s step[%d]" % (where, index))
            if step.step_id in seen:
                raise IRError("%s repeats step id %s" % (where, step.step_id))
            for operand in step.operands:
                if operand not in seen:
                    raise IRError("%s step %s consumes %s, which is not an earlier step of "
                                  "this feature" % (where, step.step_id, operand))
            seen.add(step.step_id)
            steps.append(step)
        consumed = {o for st in steps for o in st.operands}
        finals = [st.step_id for st in steps if st.step_id not in consumed]
        if len(finals) != 1:
            raise IRError("%s has %d unconsumed steps (%s); exactly one result IS the feature"
                          % (where, len(finals), ", ".join(finals)))
        return FeatureSpec(entity_id=str(eid), body=body, kind=kind.strip().upper(),
                           placement=placement, steps=tuple(steps),
                           interface=record.get("interface") or None)

    @property
    def terminal(self) -> str:
        consumed = {o for st in self.steps for o in st.operands}
        return next(st.step_id for st in self.steps if st.step_id not in consumed)

    def refs(self) -> Set[str]:
        out = set(self.placement.refs())
        for st in self.steps:
            out |= st.refs()
        return out


# ==========================================================================
# UNIT F/G. RECORD VALIDATORS - the grammar as a write-boundary check.
#
# `Expr.parse`, `TypedConstraint.parse` and `FeatureSpec.parse` RAISE, which is
# right for a reader that has been handed a record and cannot go on. A boundary
# that decides whether a record may enter standing state needs the same grammar
# as a list of problems, so these wrap the parsers and add what a parser cannot
# know: whether a reference names a Parameter that exists, whether a datum is a
# committed spatial record, whether a listed parameter is one the expression
# uses. ONE grammar, two surfaces; nothing below re-decides what a node means.
# ==========================================================================
IR_VALIDATION_KINDS = ("parameter", "constraint", "feature")


def parameter_record_problems(record: Dict[str, Any], created: bool = False) -> List[str]:
    """`created`: the record is being AUTHORED by this patch. A value on an
    authored declaration is a number the declaring stage invented (S05-C10 /
    "no fabricated s06 value"); a value arriving by extension is the settler's,
    and whether it carries its artifact is R-23's question, asked where the
    value is read (`canonical_io.resolved_values`)."""
    eid = record.get("entity_id")
    out: List[str] = []
    unit = record.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        out.append("IR: Parameter %s declares no unit (INV-004)" % eid)
    if record.get("status") not in PARAMETER_STATUSES:
        out.append("IR: Parameter %s status %r is not one of %s"
                   % (eid, record.get("status"), list(PARAMETER_STATUSES)))
    if not isinstance(record.get("symbol"), str) or not record.get("symbol", "").strip():
        out.append("IR: Parameter %s declares no symbol" % eid)
    value = record.get("value")
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            out.append("IR: Parameter %s value %r is not a number" % (eid, value))
        if created and not record.get("solved_by"):
            out.append("IR: Parameter %s is declared with a value and no solver "
                       "artifact; a declaration does not carry the number it is "
                       "declared to be settled to (S05-C10)" % eid)
    for bound in ("lower", "upper"):
        b = record.get(bound)
        if b is not None and (isinstance(b, bool) or not isinstance(b, (int, float))):
            out.append("IR: Parameter %s %s %r is not a number" % (eid, bound, b))
    role = record.get("role")
    if role is not None and str(role).upper() == "SCALE" and unit != KERNEL_LENGTH_UNIT:
        out.append("IR: Parameter %s declares role SCALE in %r; a scale is kernel length units "
                   "(%s) per basis unit" % (eid, unit, KERNEL_LENGTH_UNIT))
    return out


def _expression_problems(where: str, node: Any, known: Set[str]) -> List[str]:
    try:
        expr = Expr.parse(node)
    except IRError as exc:
        return ["IR: %s: %s" % (where, exc)]
    return ["IR: %s references %s, which no standing Parameter declares" % (where, ref)
            for ref in sorted(expr.refs()) if ref not in known]


def constraint_record_problems(record: Dict[str, Any], known_parameters: Set[str],
                               units: Optional[Dict[str, str]] = None) -> List[str]:
    """Grammar, references, and - when the declared units are known - ONE
    dimension on both sides. A constraint adding a length to a pure number is
    not a relation the solver can read; it was found at settlement, after the
    record stood. The dimensional reduction is the solver's own (Unit G)."""
    eid = record.get("entity_id")
    expr = record.get("expression")
    if not isinstance(expr, dict):
        return ["IR: Constraint %s expression is not an object" % eid]
    out: List[str] = []
    if expr.get("relation") not in RELATIONS:
        out.append("IR: Constraint %s relation %r is not one of %s"
                   % (eid, expr.get("relation"), list(RELATIONS)))
    for side in ("lhs", "rhs"):
        out += _expression_problems("Constraint %s %s" % (eid, side), expr.get(side),
                                    known_parameters)
    listed = record.get("parameters")
    if not isinstance(listed, list):
        out.append("IR: Constraint %s parameters is not a list" % eid)
        return out
    for pid in listed:
        if pid not in known_parameters:
            out.append("IR: Constraint %s lists %s, which no standing Parameter declares"
                       % (eid, pid))
    if not out:
        used = TypedConstraint.parse(record).refs()
        for ref in sorted(used - set(listed)):
            out.append("IR: Constraint %s uses %s in its expression and does not list "
                       "it in `parameters`" % (eid, ref))
    if not out and units is not None and all(ref in units for ref in used):
        from . import solver                     # lazy: solver imports this module
        out += ["IR: Constraint %s %s" % (eid, p) for p in solver.dimension_problems(expr, units)]
    return out


@dataclass(frozen=True)
class Known:
    """What a record may refer to: the state a patch would leave, by family."""

    parameters: Set[str]
    #: datum id -> family, for every declared Joint / Envelope / FunctionalRegion / Feature
    datums: Dict[str, str]
    #: feature id -> body, for every declared Feature (a feature datum must share the body)
    feature_bodies: Dict[str, str]
    #: envelope id -> body, region id -> owning bodies (a datum of the wrong body is refused)
    datum_bodies: Dict[str, Set[str]]
    #: joint id -> its declared axis_direction, so a restated axis is checked against it
    joint_axes: Optional[Dict[str, str]] = None
    #: parameter id -> declared unit, so a constraint's two sides can be checked
    #: for ONE dimension before it stands (INV-004 at the relation, not only at
    #: the leaf)
    units: Optional[Dict[str, str]] = None


def feature_record_problems(record: Dict[str, Any], known: Known) -> List[str]:
    """The whole feature, read once: placement, construction, references."""
    eid = record.get("entity_id") or record.get("id")
    try:
        spec = FeatureSpec.parse(record)
    except IRError as exc:
        return ["IR: %s" % exc]
    out: List[str] = []
    for ref in sorted(spec.refs()):
        if ref not in known.parameters:
            out.append("IR: feature %s references %s, which no standing Parameter declares"
                       % (eid, ref))
    datum = spec.placement.datum
    family = known.datums.get(datum)
    if family is None:
        out.append("IR: feature %s is placed against %s, which is no standing joint, "
                   "envelope, region or feature" % (eid, datum))
        return out
    if family == "Joint":
        # A DATUM LOCATES; AN AXIS ORIENTS. They are two facts, and a joint
        # datum settles only the first: the feature's origin is the joint's
        # located frame. Its axis DEFAULTS to the joint's - which is what a
        # bore, a pin or a bearing wants, and what most features at a joint
        # mean - and a feature may state its own instead, which says "located
        # by this joint, oriented otherwise": a face whose normal is not the
        # hinge line, a snap arm that projects across it, a keeper that
        # retains along it. Refusing that was an over-constraint, and it cost a
        # live repair round: a stage told to realize a mating side could not
        # place a FACE at the joint it belongs to without claiming the face
        # points along the hinge axis.
        #
        # WHAT REALIZES THE JOINT IS THEREFORE NOT "ANY FEATURE PLACED AT IT" -
        # it is one placed at it ON ITS AXIS, which
        # `downstream.embodiment.joint_realization_findings` is what asks.
        declared = str((known.joint_axes or {}).get(datum) or "").strip().upper()
        if axis_vector(declared) is None and spec.placement.axis is None:
            # a joint that points nowhere (FIXED, axis NONE) is a location only:
            # the feature placed at it carries its own axis or has none at all
            out.append("IR: feature %s is placed at joint %s, which declares no axis, and "
                       "names none of its own" % (eid, datum))
    if family == "Feature":
        if datum == eid:
            out.append("IR: feature %s is placed against itself" % eid)
        elif known.feature_bodies.get(datum) not in (None, spec.body):
            out.append("IR: feature %s on %s is placed against feature %s of body %s; a "
                       "feature is placed relative to its own body, and bodies relate "
                       "through joints" % (eid, spec.body, datum, known.feature_bodies.get(datum)))
    bodies = known.datum_bodies.get(datum)
    if family in ("Envelope",) and bodies and spec.body not in bodies:
        out.append("IR: feature %s on %s is placed against envelope %s of another body"
                   % (eid, spec.body, datum))
    return out


def record_problems(kind: str, record: Dict[str, Any], known: Known,
                    created: bool = False) -> List[str]:
    """THE ONE ENTRY the write boundary calls, by the kind a family declares."""
    if kind == "parameter":
        return parameter_record_problems(record, created=created)
    if kind == "constraint":
        return constraint_record_problems(record, known.parameters, known.units)
    if kind == "feature":
        return feature_record_problems(record, known)
    raise IRError("unknown ir_validation kind %r; the vocabulary is %s"
                  % (kind, list(IR_VALIDATION_KINDS)))
