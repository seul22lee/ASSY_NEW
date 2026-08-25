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
            solved_by=record.get("solved_by"))


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
    "TRANSLATE": "the operand moved by (dx, dy, dz) in the body frame",
    "ROTATE": "the operand rotated by angle (degrees) about the named body axis "
              "through the frame origin",
    "UNION": "the operands fused",
    "CUT": "the first operand with every later operand removed",
    "INTERSECT": "the common volume of the operands",
}
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


# ==========================================================================
# UNIT G. PLACEMENT - a feature's own frame, stated in its body's frame.
#
# THE ONE PLACEMENT REPRESENTATION. A feature that realizes a joint side, an
# interface side or any located geometry says WHERE it is and WHICH WAY it
# points: `origin` - three expressions in the body frame, in the kernel length
# unit - and `axis`, the feature's own axis (a bore's, a pin's, a slide's, a
# stop face's normal) as a signed body axis. Nothing here is a number invented
# in a world frame, and nothing is a pose: poses are DERIVED from placements
# and s04's joint coordinates by `downstream.kinematics`, exactly as the
# contracts say the pose law is derived and never authored.
#
# THE FRAME CONVENTION, stated once and consumed by s05's prompt, s06's checks
# and s07's kernel calls alike:
#   - every body frame is PARALLEL to the arrangement (world) frame in the pose
#     where every joint coordinate is zero - s04's arrangement itself - so a
#     body axis token and the joint axis token s03 declared name the same
#     direction, and the two are comparable by name;
#   - a feature frame has Z along `axis`, origin at `origin`, and X along the
#     CANONICAL PERPENDICULAR of the axis (`frame_axes`): a rule, so that no
#     second orientation choice is asked of anyone;
#   - s07 builds a primitive that realizes a placed feature IN THAT FRAME;
#     TRANSLATE and ROTATE remain moves within the body frame.
# ==========================================================================
def frame_axes(axis: str) -> Tuple[Tuple[float, float, float], Tuple[float, float, float],
                                   Tuple[float, float, float]]:
    """(x, y, z) unit vectors of the frame whose Z is the named axis.

    X is the canonical perpendicular - the next body axis in cyclic order
    (Z->X, X->Y, Y->Z), positive - and Y completes a right-handed frame. One
    rule, so the orientation of a placed primitive is never a decision.
    """
    z = axis_vector(axis)
    if z is None:
        raise IRError("axis %r is not one of %s" % (axis, list(SIGNED_AXES)))
    letter = axis.strip().upper()[-1]
    x = AXIS_VECTORS["+" + {"Z": "X", "X": "Y", "Y": "Z"}[letter]]
    y = (z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0])
    return x, y, z


@dataclass(frozen=True)
class Placement:
    origin: Tuple[Expr, Expr, Expr]
    axis: str

    @staticmethod
    def parse(node: Any, where: str = "placement") -> "Placement":
        if not isinstance(node, dict):
            raise IRError("%s is not an object" % where)
        origin = node.get("origin")
        if not isinstance(origin, list) or len(origin) != 3:
            raise IRError("%s origin is not three expressions" % where)
        exprs = []
        for index, component in enumerate(origin):
            if isinstance(component, bool) or isinstance(component, (int, float)):
                raise IRError("%s origin[%d] is a bare number (%r); a coordinate is a "
                              "declared parameter or a unit-bearing constant"
                              % (where, index, component))
            exprs.append(Expr.parse(component))
        axis = node.get("axis")
        if axis_vector(axis) is None:
            raise IRError("%s axis %r is not one of %s" % (where, axis, list(SIGNED_AXES)))
        unknown = sorted(set(node) - {"origin", "axis"})
        if unknown:
            raise IRError("%s carries %s, which a placement does not have" % (where, unknown))
        return Placement(origin=(exprs[0], exprs[1], exprs[2]), axis=axis.strip().upper())

    def refs(self) -> Set[str]:
        return {r for e in self.origin for r in e.refs()}


def placement_problems(where: str, node: Any, known_parameters: Set[str]) -> List[str]:
    try:
        placement = Placement.parse(node, where)
    except IRError as exc:
        return ["IR: %s" % exc]
    return ["IR: %s references %s, which no standing Parameter declares" % (where, ref)
            for ref in sorted(placement.refs()) if ref not in known_parameters]


@dataclass(frozen=True)
class Statement:
    """One construction step, in its owning body's frame."""

    entity_id: str
    body: str
    operation: str
    operands: Tuple[str, ...]
    parameters: Dict[str, Expr]
    axis: Optional[str] = None
    feature: Optional[str] = None

    @staticmethod
    def parse(record: Dict[str, Any]) -> "Statement":
        op = record.get("operation")
        if op not in OPCODES:
            raise IRError("ConstructionStatement %s operation %r is not in the "
                          "opcode vocabulary %s"
                          % (record.get("entity_id"), op, sorted(OPCODES)))
        operands = tuple(record.get("operands") or ())
        if op in COMBINING and len(operands) < 2:
            raise IRError("%s %s combines %d operands; it needs at least two"
                          % (op, record.get("entity_id"), len(operands)))
        if op in TRANSFORMING and len(operands) != 1:
            raise IRError("%s %s transforms %d operands; it needs exactly one"
                          % (op, record.get("entity_id"), len(operands)))
        if op not in COMBINING and op not in TRANSFORMING and operands:
            raise IRError("%s %s is a primitive and takes no operands"
                          % (op, record.get("entity_id")))
        raw = record.get("parameters") or {}
        if not isinstance(raw, dict):
            raise IRError("ConstructionStatement %s parameters is not an object"
                          % record.get("entity_id"))
        params = {k: Expr.parse(v) for k, v in raw.items()}
        missing = [k for k in OPCODES[op] if k not in params]
        if missing:
            raise IRError("%s %s omits required parameter(s) %s"
                          % (op, record.get("entity_id"), missing))
        axis = record.get("axis")
        if op == "ROTATE" and axis not in AXES:
            raise IRError("ROTATE %s declares axis %r; it must be one of %s"
                          % (record.get("entity_id"), axis, list(AXES)))
        body = record.get("body")
        if not body:
            raise IRError("ConstructionStatement %s names no owning body"
                          % record.get("entity_id"))
        return Statement(entity_id=record["entity_id"], body=body, operation=op,
                         operands=operands, parameters=params, axis=axis,
                         feature=record.get("feature"))

    def refs(self) -> Set[str]:
        return {r for e in self.parameters.values() for r in e.refs()}


@dataclass
class ConstructionProgram:
    """The ordered statements for one design, grouped by the body they build.

    NOT a new DesignState family. It is the READING of the ConstructionStatement
    records that already exist, ordered by their declared dependencies - so there
    is one authority for what the program is, and it is the state.
    """

    statements: List[Statement] = field(default_factory=list)

    @staticmethod
    def parse(records: Sequence[Dict[str, Any]]) -> "ConstructionProgram":
        return ConstructionProgram([Statement.parse(r) for r in records])

    def bodies(self) -> List[str]:
        seen: List[str] = []
        for s in self.statements:
            if s.body not in seen:
                seen.append(s.body)
        return seen

    def for_body(self, body: str) -> List[Statement]:
        return [s for s in self.statements if s.body == body]

    def parameter_refs(self) -> Set[str]:
        return {r for s in self.statements for r in s.refs()}

    def ordering_problems(self) -> List[str]:
        """Statements whose operands are not already built, and cycles.

        A compiler that tolerated a forward reference would be choosing an
        evaluation order, which is a decision s07 does not own.
        """
        problems: List[str] = []
        for body in self.bodies():
            built: Set[str] = set()
            for s in self.for_body(body):
                for operand in s.operands:
                    if operand not in built:
                        problems.append(
                            "%s references %s before it is built" % (s.entity_id, operand))
                built.add(s.entity_id)
        return problems

    def terminal_of(self, body: str) -> Optional[str]:
        """The statement whose result IS the body: the one nothing consumes."""
        stmts = self.for_body(body)
        consumed = {o for s in stmts for o in s.operands}
        finals = [s.entity_id for s in stmts if s.entity_id not in consumed]
        return finals[-1] if len(finals) == 1 else None


def dependency_cone(program: ConstructionProgram, entity_id: str) -> List[str]:
    """Everything the named statement rests on, transitively.

    S07-C6 requires a compile failure to cite the originating statement AND its
    dependency cone, because a statement that fails is rarely the statement that
    is wrong.
    """
    by_id = {s.entity_id: s for s in program.statements}
    seen: List[str] = []
    frontier = [entity_id]
    while frontier:
        cur = frontier.pop()
        if cur in seen or cur not in by_id:
            continue
        seen.append(cur)
        frontier.extend(by_id[cur].operands)
    return seen


# ==========================================================================
# UNIT F. RECORD VALIDATORS - the grammar as a write-boundary check.
#
# `Expr.parse`, `TypedConstraint.parse` and `Statement.parse` RAISE, which is
# right for a reader that has been handed a record and cannot go on. A boundary
# that decides whether a record may enter standing state needs the same grammar
# as a list of problems, so these wrap the parsers and add what a parser cannot
# know: whether a reference names a Parameter that exists, whether an operand
# names a statement that exists, whether a listed parameter is one the
# expression uses. ONE grammar, two surfaces; nothing below re-decides what a
# node means.
# ==========================================================================
IR_VALIDATION_KINDS = ("parameter", "constraint", "statement", "feature")


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
    return out


def _expression_problems(where: str, node: Any, known: Set[str]) -> List[str]:
    try:
        expr = Expr.parse(node)
    except IRError as exc:
        return ["IR: %s: %s" % (where, exc)]
    return ["IR: %s references %s, which no standing Parameter declares" % (where, ref)
            for ref in sorted(expr.refs()) if ref not in known]


def constraint_record_problems(record: Dict[str, Any], known_parameters: Set[str]
                               ) -> List[str]:
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
    return out


def statement_record_problems(record: Dict[str, Any], known_parameters: Set[str],
                              known_statements: Set[str]) -> List[str]:
    eid = record.get("entity_id")
    try:
        stmt = Statement.parse(record)
    except IRError as exc:
        return ["IR: %s" % exc]
    out: List[str] = []
    for ref in sorted(stmt.refs()):
        if ref not in known_parameters:
            out.append("IR: ConstructionStatement %s references %s, which no standing "
                       "Parameter declares" % (eid, ref))
    for operand in stmt.operands:
        if operand not in known_statements:
            out.append("IR: ConstructionStatement %s consumes %s, which is no standing "
                       "ConstructionStatement" % (eid, operand))
    return out


def envelope_problems(feature_id: Any, envelope: Any, known_parameters: Set[str]
                      ) -> Tuple[Optional[Dict[str, List[Expr]]], List[str]]:
    """Parse a symbolic feature envelope: (expressions by axis list, problems).

    The constraint grammar at the leaves of a spatial claim: `{ref}` naming a
    declared Parameter, `{const, unit}`, or arithmetic over them. A bare number
    is a solved dimension demanded of the stage that is told never to invent
    one, and is refused by name; a coordinate at the frame origin is the typed
    zero of the frame's unit.
    """
    if not isinstance(envelope, dict):
        return None, ["IR: feature %s declares an envelope that is not an object"
                      % feature_id]
    out: Dict[str, List[Expr]] = {}
    problems: List[str] = []
    for axis_list in ("centre", "half_extent"):
        components = envelope.get(axis_list)
        if not isinstance(components, list) or len(components) != 3:
            problems.append("IR: feature %s envelope %s is not three components"
                            % (feature_id, axis_list))
            continue
        parsed: List[Expr] = []
        for index, node in enumerate(components):
            if isinstance(node, bool) or isinstance(node, (int, float)):
                problems.append(
                    "IR: feature %s envelope %s[%d] is a bare number (%r); a "
                    "dimension is a declared parameter or a unit-bearing constant, "
                    "never a value invented here" % (feature_id, axis_list, index, node))
                continue
            try:
                expr = Expr.parse(node)
            except IRError as exc:
                problems.append("IR: feature %s envelope %s[%d]: %s"
                                % (feature_id, axis_list, index, exc))
                continue
            for ref in sorted(expr.refs()):
                if ref not in known_parameters:
                    problems.append("IR: feature %s envelope references %s, which no "
                                    "standing Parameter declares" % (feature_id, ref))
            parsed.append(expr)
        if len(parsed) == 3:
            out[axis_list] = parsed
    if problems or len(out) != 2:
        return None, problems
    return out, []


def record_problems(kind: str, record: Dict[str, Any], known_parameters: Set[str],
                    known_statements: Set[str], created: bool = False) -> List[str]:
    """THE ONE ENTRY the write boundary calls, by the kind a family declares."""
    if kind == "parameter":
        return parameter_record_problems(record, created=created)
    if kind == "constraint":
        return constraint_record_problems(record, known_parameters)
    if kind == "statement":
        return statement_record_problems(record, known_parameters, known_statements)
    if kind == "feature":
        problems: List[str] = []
        if record.get("envelope") is not None:
            _exprs, envelope = envelope_problems(record.get("entity_id"),
                                                 record.get("envelope"), known_parameters)
            problems += envelope
        if record.get("placement") is not None:
            problems += placement_problems("feature %s placement" % record.get("entity_id"),
                                           record.get("placement"), known_parameters)
        return problems
    raise IRError("unknown ir_validation kind %r; the vocabulary is %s"
                  % (kind, list(IR_VALIDATION_KINDS)))
