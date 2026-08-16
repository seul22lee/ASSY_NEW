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
SOLVER_STATUSES = (FEASIBLE, INFEASIBLE, UNDERDETERMINED,
                   UNSUPPORTED_FORMULATION, SOLVER_FAILURE)

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
        if not isinstance(args, list) or len(args) < 2:
            raise IRError("operator %r needs at least two arguments" % node["op"])
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

#: ROTATE needs an axis; it is the one transform with a direction, and naming it
#: in the statement rather than inferring it is what keeps s07 from choosing one.
AXES = ("X", "Y", "Z")


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
