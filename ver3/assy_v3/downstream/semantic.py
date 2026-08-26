"""THE SEMANTIC S05 LAYER - mechanical meaning, with no compiler bookkeeping.

WHAT CHANGED AND WHY

s05 used to author the compiler's own representation: canonical entity ids for
records that did not exist yet, construction STEPS with their own ids, their
operand lists, their ordering and the single unconsumed result that IS the
feature, a raw expression AST, and a `parameters` list restating what the
expression already said. Every one of those is bookkeeping, and each was a
recurring class of live failure - a dangling FEA id, a step consuming a later
step, two unconsumed terminals, a unary CUT meaning "remove me from the body",
a malformed AST node, a parameter list that disagreed with its own expression.

None of those is a mechanical decision. So none of them is expressible here.

WHAT THIS LAYER SAYS

Feature kind, body, placement datum, orientation, polarity (by kind), symbolic
dimensions as parameter references, geometry intent as a RECURSIVE SOLID TREE,
which features embody which declared relation, which features realize which
side of which interface, and constraints as typed relations. Production owns
every id, every step, every ordering and every derived list.

WHAT IS DELIBERATELY INEXPRESSIBLE

  - a canonical id for a record this response is creating (local keys only)
  - a reference to a step (a tree has no references)
  - an ordering (a tree has no order; the lowerer derives one)
  - a terminal (a tree has one root)
  - a single-operand CUT (a boolean node needs two or more children)
  - the body as an operand (no node names a body)
  - two parameters multiplied or divided by each other (the typed expression
    has no parameter-by-parameter product, which is also the formulation S06
    reports as unsupported)
  - a `parameters` list on a constraint (derived from the expression)
  - a KinematicRealization id or an optional KinematicRealization row
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import ir


class SemanticError(ValueError):
    """A response that does not read as a semantic embodiment. Reported with
    the field that is wrong, never repaired."""


def _raise_side(where: str, body: str) -> bool:
    raise SemanticError("%s[%s] is not a list of feature keys" % (where, body))


def _obj(node: Any, where: str) -> Dict[str, Any]:
    if not isinstance(node, dict):
        raise SemanticError("%s is %s, not an object" % (where, type(node).__name__))
    return node


def _key(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticError("%s is not a local key" % where)
    text = value.strip()
    if _looks_canonical(text):
        raise SemanticError(
            "%s is %r, which has the shape of a canonical entity id. This response names "
            "NEW features, parameters and constraints by LOCAL KEY only; production "
            "allocates every canonical id" % (where, text))
    return text


def _looks_canonical(text: str) -> bool:
    """An id of the canonical form PREFIX-NNNN. Local keys must not look like
    one, because a key that does is a model-authored canonical id in disguise -
    the exact defect this layer removes."""
    import re
    return bool(re.match(r"^[A-Z][A-Z0-9]{1,7}-[0-9A-Za-z-]{2,}$", text))


def _no_extra(node: Dict[str, Any], allowed: Sequence[str], where: str) -> None:
    extra = sorted(set(node) - set(allowed))
    if extra:
        raise SemanticError("%s carries %s, which it does not have; the fields are %s"
                            % (where, extra, list(allowed)))


def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SemanticError("%s is %r, which is not a number" % (where, value))
    return float(value)


# ==========================================================================
# TYPED EXPRESSIONS. A restricted, linear surface over the arithmetic S06
# already solves. Every form below lowers to the existing canonical AST.
# ==========================================================================
PARAM, NUMBER, SUM, DIFFERENCE, NEGATE, SCALE_BY, DIVIDE_BY = (
    "param", "number", "sum", "difference", "negate", "scale_by", "divide_by")
EXPR_KINDS = (PARAM, NUMBER, SUM, DIFFERENCE, NEGATE, SCALE_BY, DIVIDE_BY)

#: The units a literal may declare. Lengths and angles are the kernel's; "1" is
#: the dimensionless basis number the arrangement's own coordinates are in.
LITERAL_UNITS = (ir.KERNEL_LENGTH_UNIT, ir.KERNEL_ANGLE_UNIT, "1")


@dataclass(frozen=True)
class TypedExpr:
    kind: str
    param: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    terms: Tuple["TypedExpr", ...] = ()
    left: Optional["TypedExpr"] = None
    right: Optional["TypedExpr"] = None
    of: Optional["TypedExpr"] = None
    factor: Optional[float] = None
    #: PARAM only: the declaration this reference carries.
    symbol: Optional[str] = None
    role: Optional[str] = None

    @staticmethod
    def parse(node: Any, where: str) -> "TypedExpr":
        node = _obj(node, where)
        kind = node.get("kind")
        if kind not in EXPR_KINDS:
            raise SemanticError("%s declares kind %r; an expression is one of %s"
                                % (where, kind, list(EXPR_KINDS)))
        if kind == PARAM:
            # A REFERENCE DECLARES WHAT IT NAMES. The dimension is stated where
            # it is used, so a parameter that is read but never declared is not
            # a dangling key to be caught - it is unsayable. `symbol` defaults
            # to the name and `role` is stated only where the design owes one;
            # every mention of a name must agree, which is checked once the
            # whole response is read.
            _no_extra(node, ("kind", "param", "unit", "symbol", "role"), where)
            unit = node.get("unit")
            if not isinstance(unit, str) or not unit.strip():
                raise SemanticError(
                    "%s names parameter %r with no unit; every dimension is declared where it "
                    "is used, so each reference carries the unit it is in (INV-004)"
                    % (where, node.get("param")))
            role = node.get("role")
            symbol = node.get("symbol")
            return TypedExpr(kind=PARAM, param=_key(node.get("param"), "%s param" % where),
                             unit=unit.strip(),
                             symbol=(symbol.strip() if isinstance(symbol, str) and symbol.strip()
                                     else None),
                             role=(role.strip().upper() if isinstance(role, str) and role.strip()
                                   else None))
        if kind == NUMBER:
            _no_extra(node, ("kind", "value", "unit"), where)
            unit = node.get("unit")
            if unit not in LITERAL_UNITS:
                raise SemanticError(
                    "%s declares unit %r; a literal is in %s - a length in %s, an angle in "
                    "%s, or the dimensionless basis unit \"1\". A number with no unit is the "
                    "defaulting this layer exists to prevent"
                    % (where, unit, list(LITERAL_UNITS), ir.KERNEL_LENGTH_UNIT,
                       ir.KERNEL_ANGLE_UNIT))
            return TypedExpr(kind=NUMBER, value=_number(node.get("value"), "%s value" % where),
                             unit=str(unit))
        if kind == SUM:
            _no_extra(node, ("kind", "terms"), where)
            raw = node.get("terms")
            if not isinstance(raw, list) or len(raw) < 2:
                raise SemanticError("%s sums %s terms; a sum adds two or more"
                                    % (where, len(raw) if isinstance(raw, list) else "no"))
            return TypedExpr(kind=SUM, terms=tuple(
                TypedExpr.parse(t, "%s terms[%d]" % (where, i)) for i, t in enumerate(raw)))
        if kind == DIFFERENCE:
            _no_extra(node, ("kind", "left", "right"), where)
            return TypedExpr(kind=DIFFERENCE,
                             left=TypedExpr.parse(node.get("left"), "%s left" % where),
                             right=TypedExpr.parse(node.get("right"), "%s right" % where))
        if kind == NEGATE:
            _no_extra(node, ("kind", "of"), where)
            return TypedExpr(kind=NEGATE, of=TypedExpr.parse(node.get("of"), "%s of" % where))
        if kind == SCALE_BY:
            _no_extra(node, ("kind", "of", "factor"), where)
            return TypedExpr(kind=SCALE_BY, of=TypedExpr.parse(node.get("of"), "%s of" % where),
                             factor=_number(node.get("factor"), "%s factor" % where))
        _no_extra(node, ("kind", "of", "divisor"), where)
        divisor = _number(node.get("divisor"), "%s divisor" % where)
        if divisor == 0:
            raise SemanticError("%s divides by zero" % where)
        return TypedExpr(kind=DIVIDE_BY, of=TypedExpr.parse(node.get("of"), "%s of" % where),
                         factor=divisor)

    def refs(self) -> Tuple[str, ...]:
        return tuple(node.param for node in self.walk_params())

    def walk_params(self) -> Tuple["TypedExpr", ...]:
        """Every param node beneath this one, itself included."""
        if self.kind == PARAM:
            return (self,)
        out: List["TypedExpr"] = []
        for child in list(self.terms) + [self.left, self.right, self.of]:
            if child is not None:
                out.extend(child.walk_params())
        return tuple(out)


def parameter_declarations(nodes: Sequence["TypedExpr"], where: str = "") -> Dict[str, Dict[str, Any]]:
    """key -> {unit, symbol, role}, gathered from every reference.

    THE ONE DECLARATION SET, and it is the union of the use sites. Two mentions
    of one name that disagree about its unit or its role are a contradiction
    the author has to resolve; they are never merged and never preferred by
    order of appearance.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        for ref in node.walk_params():
            declared = out.setdefault(ref.param, {"unit": ref.unit, "symbol": ref.symbol,
                                                  "role": ref.role})
            for field in ("unit", "role"):
                stated = getattr(ref, field)
                if stated is not None and declared.get(field) not in (None, stated):
                    raise SemanticError(
                        "parameter %r is declared %s %r in one place and %r in another; a "
                        "dimension has one unit and one role wherever it is named"
                        % (ref.param, field, declared.get(field), stated))
                if stated is not None:
                    declared[field] = stated
            if ref.symbol and not declared.get("symbol"):
                declared["symbol"] = ref.symbol
    for key, declared in out.items():
        declared.setdefault("symbol", None)
        if not declared.get("symbol"):
            declared["symbol"] = key
    return out


#: Fields whose dimensional meaning the FIELD ITSELF fixes. A placement offset
#: is a length by construction; a turn is an angle by construction. Where the
#: context is unambiguous a bare number is read as that quantity and
#: canonicalised to the typed literal - the ceremony was not preventing a
#: mistake, it was only a way to fail. Nowhere else: a constraint relates
#: quantities whose dimension is exactly what is under discussion, so a bare
#: number there would be the silent guessing this layer exists to prevent.
def contextual(node: Any, unit: str, where: str) -> "TypedExpr":
    """A typed expression, or a bare number read in the unit this field is in."""
    if isinstance(node, bool):
        raise SemanticError("%s is a boolean, not a quantity" % where)
    if isinstance(node, (int, float)):
        return TypedExpr(kind=NUMBER, value=float(node), unit=unit)
    return TypedExpr.parse(node, where)


def length(node: Any, where: str) -> "TypedExpr":
    return contextual(node, ir.KERNEL_LENGTH_UNIT, where)


def angle(node: Any, where: str) -> "TypedExpr":
    return contextual(node, ir.KERNEL_ANGLE_UNIT, where)


def zero_length() -> TypedExpr:
    """The typed zero of the kernel length unit - a coordinate definition, not
    a dimension anyone left undecided."""
    return TypedExpr(kind=NUMBER, value=0.0, unit=ir.KERNEL_LENGTH_UNIT)


# ==========================================================================
# THE SOLID OF A FEATURE. Physical shape, not CSG bookkeeping.
#
# WHAT THIS REPLACED AND WHY
#
# The first version of this layer exposed the compiler's own booleans - UNION,
# CUT, INTERSECT over a list of operands. A live response wrote CUT with ONE
# operand, which can only have meant "cut this feature out of its body", and
# that is not something a feature's own geometry can say: the body is composed
# from its features afterwards, BY POLARITY. Refusing the unary form caught the
# mistake but kept inviting it, because an operator called CUT taking a list of
# operands reads as the body-level operation it is not.
#
# So the shapes below are named for what they ARE. There is no operator whose
# first operand could be misread as the body:
#
#   BLOCK, CYLINDER, SPHERE   the material itself
#   AT                        the same material, placed within the feature frame
#   COMPOUND                  several parts of ONE feature, fused
#   RELIEVED                  a base with reliefs taken out of IT
#   COMMON                    the material two parts share
#
# RELIEVED is the only difference, it names its `base` explicitly, and it needs
# at least one relief - so a lone solid cannot be written as a subtraction of
# anything. A bore with a counterbore, a boss with a flat: those are reliefs of
# the feature's own base. Whether the finished solid is ADDED to the body or
# REMOVED from it is the feature's KIND and is stated nowhere here.
# ==========================================================================
BLOCK, CYLINDER, SPHERE = "BLOCK", "CYLINDER", "SPHERE"
AT, COMPOUND, RELIEVED, COMMON = "AT", "COMPOUND", "RELIEVED", "COMMON"

#: shape -> the named lengths it takes, and the IR opcode it lowers to.
SOLID_PRIMITIVES = {BLOCK: (("dx", "dy", "dz"), "BOX"),
                    CYLINDER: (("radius", "height"), "CYLINDER"),
                    SPHERE: (("radius",), "SPHERE")}
SOLID_SHAPES = (BLOCK, CYLINDER, SPHERE, AT, COMPOUND, RELIEVED, COMMON)


@dataclass(frozen=True)
class Turn:
    """A rotation of a feature's own material about its frame origin."""

    axis: str
    angle: TypedExpr

    @staticmethod
    def parse(node: Any, where: str) -> "Turn":
        node = _obj(node, where)
        _no_extra(node, ("axis", "angle"), where)
        axis = node.get("axis")
        if axis not in ir.AXES:
            raise SemanticError("%s turns about %r; the axes are %s"
                                % (where, axis, list(ir.AXES)))
        if node.get("angle") is None:
            raise SemanticError("%s states no angle" % where)
        return Turn(axis=axis, angle=angle(node["angle"], "%s angle" % where))


@dataclass(frozen=True)
class Solid:
    """One node of a feature's material. Children are built before it, always."""

    shape: str
    lengths: Dict[str, TypedExpr] = field(default_factory=dict)
    children: Tuple["Solid", ...] = ()
    offset: Optional[Tuple[TypedExpr, TypedExpr, TypedExpr]] = None
    turn: Optional[Turn] = None

    @staticmethod
    def parse(node: Any, where: str = "solid") -> "Solid":
        node = _obj(node, where)
        shape = node.get("shape")
        if shape not in SOLID_SHAPES:
            if node.get("op"):
                raise SemanticError(
                    "%s names the operation %r; a feature's material is described by its "
                    "SHAPE, not by a compiler operation. The shapes are %s"
                    % (where, node.get("op"), list(SOLID_SHAPES)))
            raise SemanticError("%s declares shape %r; the shapes are %s"
                                % (where, shape, list(SOLID_SHAPES)))
        if shape in SOLID_PRIMITIVES:
            names, _opcode = SOLID_PRIMITIVES[shape]
            _no_extra(node, ("shape",) + names, where)
            lengths = {}
            for name in names:
                if name not in node:
                    raise SemanticError("%s: %s omits required dimension %r"
                                        % (where, shape, name))
                lengths[name] = length(node[name], "%s %s" % (where, name))
            return Solid(shape=shape, lengths=lengths)
        if shape == AT:
            _no_extra(node, ("shape", "of", "offset", "turn"), where)
            if node.get("of") is None:
                raise SemanticError("%s places nothing; AT takes one `of`" % where)
            if isinstance(node.get("of"), list):
                raise SemanticError("%s places exactly one solid, not a list" % where)
            raw = node.get("offset")
            offset = None
            if raw is not None:
                if not isinstance(raw, list) or len(raw) != 3:
                    raise SemanticError("%s offset is not three lengths" % where)
                offset = tuple(length(c, "%s offset[%d]" % (where, i))
                               for i, c in enumerate(raw))
            turn = Turn.parse(node["turn"], "%s turn" % where) if node.get("turn") else None
            if offset is None and turn is None:
                raise SemanticError("%s states neither an offset nor a turn; it places "
                                    "nothing" % where)
            return Solid(shape=AT, children=(Solid.parse(node["of"], "%s of" % where),),
                         offset=offset, turn=turn)
        if shape == RELIEVED:
            _no_extra(node, ("shape", "base", "relief"), where)
            if node.get("base") is None:
                raise SemanticError(
                    "%s states no `base`; RELIEVED is a base of THIS feature's own material "
                    "with reliefs taken out of IT. It is not how a feature is removed from "
                    "its body - that is the feature's KIND, and the body is named nowhere in "
                    "a feature's geometry" % where)
            raw = node.get("relief")
            if not isinstance(raw, list) or not raw:
                raise SemanticError(
                    "%s relieves nothing; RELIEVED takes one or more reliefs - a counterbore "
                    "in a bore, a flat on a boss. A shape with nothing taken out of it is "
                    "just that shape" % where)
            return Solid(shape=RELIEVED,
                         children=(Solid.parse(node["base"], "%s base" % where),)
                         + tuple(Solid.parse(r, "%s relief[%d]" % (where, i))
                                 for i, r in enumerate(raw)))
        _no_extra(node, ("shape", "parts"), where)
        raw = node.get("parts")
        if not isinstance(raw, list) or len(raw) < 2:
            raise SemanticError(
                "%s: %s combines %s part(s); it takes TWO OR MORE parts of THIS feature's own "
                "material" % (where, shape, len(raw) if isinstance(raw, list) else "no"))
        return Solid(shape=shape, children=tuple(
            Solid.parse(c, "%s parts[%d]" % (where, i)) for i, c in enumerate(raw)))

    def refs(self) -> Tuple[str, ...]:
        return tuple(node.param for node in self.walk_params())

    def walk_params(self) -> Tuple[TypedExpr, ...]:
        out: List[TypedExpr] = []
        for expr in self.exprs():
            out.extend(expr.walk_params())
        return tuple(out)

    def exprs(self) -> Tuple[TypedExpr, ...]:
        out: List[TypedExpr] = list(self.lengths.values())
        if self.offset:
            out.extend(self.offset)
        if self.turn:
            out.append(self.turn.angle)
        for child in self.children:
            out.extend(child.exprs())
        return tuple(out)

    def node_count(self) -> int:
        return 1 + sum(c.node_count() for c in self.children)


# ==========================================================================
# THE RECORDS. Local keys everywhere a NEW s05 object is named; canonical ids
# only where a STANDING upstream entity is named.
# ==========================================================================
#: The families a feature may be placed against. A DATUM IS A PLACE. An
#: Interface is an interaction between bodies, not a location, and it is absent
#: here on purpose: a live response placed two features against one, which is
#: not a mistake to be caught afterwards but a sentence that should not parse.
JOINT_DATUM, ENVELOPE_DATUM = "JOINT", "ENVELOPE"
REGION_DATUM, FEATURE_DATUM = "FUNCTIONAL_REGION", "FEATURE"
DATUM_KINDS = (JOINT_DATUM, ENVELOPE_DATUM, REGION_DATUM, FEATURE_DATUM)

#: datum kind -> the canonical family its `ref` must name. FEATURE is absent
#: because a feature datum names a LOCAL KEY of this same response.
DATUM_FAMILY = {JOINT_DATUM: "Joint", ENVELOPE_DATUM: "Envelope",
                REGION_DATUM: "FunctionalRegion"}


@dataclass(frozen=True)
class SemanticDatum:
    """WHERE a feature sits, typed by the kind of thing it sits on."""

    kind: str
    ref: str

    @staticmethod
    def parse(node: Any, where: str) -> "SemanticDatum":
        if isinstance(node, str):
            raise SemanticError(
                "%s is the bare name %r; a datum states WHAT KIND of place it is - "
                '{"kind": %s, "ref": "..."} - so a thing that is not a place cannot be '
                "named as one" % (where, node, " | ".join(DATUM_KINDS)))
        node = _obj(node, where)
        _no_extra(node, ("kind", "ref"), where)
        kind = node.get("kind")
        if kind not in DATUM_KINDS:
            raise SemanticError(
                "%s declares kind %r; a feature is placed on a %s. An Interface is an "
                "interaction between bodies and is not a place"
                % (where, kind, " | ".join(DATUM_KINDS)))
        ref = node.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            raise SemanticError("%s names nothing" % where)
        ref = ref.strip()
        if kind == FEATURE_DATUM:
            ref = _key(ref, "%s ref" % where)
        return SemanticDatum(kind=kind, ref=ref)


@dataclass(frozen=True)
class SemanticPlacement:
    datum: SemanticDatum
    offset: Tuple[TypedExpr, TypedExpr, TypedExpr]
    axis: Optional[str] = None

    @staticmethod
    def parse(node: Any, where: str) -> "SemanticPlacement":
        node = _obj(node, where)
        _no_extra(node, ("datum", "offset", "axis"), where)
        if node.get("datum") is None:
            raise SemanticError(
                "%s names no datum; a feature is placed relative to a committed joint, its "
                "body's envelope, a functional region or another feature" % where)
        raw = node.get("offset")
        if raw is None:
            offset = (zero_length(), zero_length(), zero_length())
        else:
            if not isinstance(raw, list) or len(raw) != 3:
                raise SemanticError("%s offset is not three lengths" % where)
            # A PLACEMENT OFFSET IS A LENGTH BY CONSTRUCTION, so a plain number
            # is read in the kernel length unit rather than refused.
            offset = tuple(length(c, "%s offset[%d]" % (where, i))
                           for i, c in enumerate(raw))
        axis = node.get("axis")
        if axis is not None and ir.axis_vector(axis) is None:
            raise SemanticError("%s axis %r is not one of %s"
                                % (where, axis, list(ir.SIGNED_AXES)))
        return SemanticPlacement(
            datum=SemanticDatum.parse(node["datum"], "%s datum" % where), offset=offset,
            axis=axis.strip().upper() if isinstance(axis, str) else None)

    def refs(self) -> Tuple[str, ...]:
        return tuple(r for e in self.offset for r in e.refs())

    def exprs(self) -> Tuple[TypedExpr, ...]:
        return tuple(self.offset)


@dataclass(frozen=True)
class SemanticFeature:
    key: str
    body: str
    feature_kind: str
    geometry: str
    placement: SemanticPlacement
    solid: Solid

    @staticmethod
    def parse(node: Any, index: int) -> "SemanticFeature":
        where = "features[%d]" % index
        node = _obj(node, where)
        _no_extra(node, ("key", "body", "feature_kind", "geometry", "placement", "solid"),
                  where)
        key = _key(node.get("key"), "%s key" % where)
        where = "feature %s" % key
        body = node.get("body")
        if not isinstance(body, str) or not body.strip():
            raise SemanticError("%s names no body" % where)
        kind = node.get("feature_kind")
        if not isinstance(kind, str) or not kind.strip():
            raise SemanticError("%s names no feature_kind" % where)
        geometry = node.get("geometry")
        if not isinstance(geometry, str) or not geometry.strip():
            raise SemanticError("%s carries no geometry description" % where)
        if node.get("solid") is None:
            raise SemanticError("%s has no solid; a feature that builds nothing is not an "
                                "embodiment" % where)
        return SemanticFeature(
            key=key, body=body.strip(), feature_kind=kind.strip().upper(),
            geometry=geometry.strip(),
            placement=SemanticPlacement.parse(node.get("placement"), "%s placement" % where),
            solid=Solid.parse(node["solid"], "%s solid" % where))

    def refs(self) -> Tuple[str, ...]:
        return self.placement.refs() + self.solid.refs()

    def exprs(self) -> Tuple[TypedExpr, ...]:
        return tuple(self.placement.offset) + self.solid.exprs()


# A `SemanticParameter` record used to live here. It is gone: a parameter is
# DECLARED WHERE IT IS USED, so `parameter_declarations` gathers the set from
# the references and there is no second list to fall out of step with them.


@dataclass(frozen=True)
class SemanticConstraint:
    """One typed relation. It carries NO key, because nothing references it:
    the constraint that governs an interface is declared inside that
    interface's assignment, and every other constraint is named by nobody."""

    kind: str
    relation: str
    lhs: TypedExpr
    rhs: TypedExpr
    basis: Optional[str] = None

    @staticmethod
    def parse(node: Any, where: str) -> "SemanticConstraint":
        node = _obj(node, where)
        if "parameters" in node:
            raise SemanticError(
                "%s states a `parameters` list; the expression already names every parameter "
                "it uses and production derives the list from it" % where)
        if "key" in node:
            raise SemanticError(
                "%s carries a `key`; a constraint is referenced by nothing - the one that "
                "governs an interface is declared inside that interface's assignment" % where)
        _no_extra(node, ("kind", "relation", "lhs", "rhs", "basis"), where)
        kind = node.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            raise SemanticError("%s names no kind" % where)
        relation = node.get("relation")
        if relation not in ir.RELATIONS:
            raise SemanticError("%s declares relation %r; it is one of %s"
                                % (where, relation, list(ir.RELATIONS)))
        basis = node.get("basis")
        return SemanticConstraint(
            kind=kind.strip().upper(), relation=relation,
            lhs=TypedExpr.parse(node.get("lhs"), "%s lhs" % where),
            rhs=TypedExpr.parse(node.get("rhs"), "%s rhs" % where),
            basis=basis.strip().upper() if isinstance(basis, str) and basis.strip() else None)

    def refs(self) -> Tuple[str, ...]:
        return self.lhs.refs() + self.rhs.refs()

    def exprs(self) -> Tuple[TypedExpr, ...]:
        return (self.lhs, self.rhs)


@dataclass(frozen=True)
class SemanticRealization:
    """An obligation discharge. Separate from a KinematicRealization and it
    stays separate: one says a duty is met, the other says what embodies a
    declared relation."""

    addresses_obligations: Tuple[str, ...]
    participating_features: Tuple[str, ...]
    verification_predicate: str

    @staticmethod
    def parse(node: Any, index: int) -> "SemanticRealization":
        where = "realizations[%d]" % index
        node = _obj(node, where)
        _no_extra(node, ("addresses_obligations", "participating_features",
                         "verification_predicate"), where)
        predicate = node.get("verification_predicate")
        if not isinstance(predicate, str) or not predicate.strip():
            raise SemanticError("%s carries no verification predicate; it discharges nothing"
                                % where)
        obligations = node.get("addresses_obligations") or []
        if not isinstance(obligations, list) or not all(isinstance(o, str) for o in obligations):
            raise SemanticError("%s addresses_obligations is not a list of obligation ids"
                                % where)
        raw = node.get("participating_features") or []
        if not isinstance(raw, list):
            raise SemanticError("%s participating_features is not a list" % where)
        return SemanticRealization(
            addresses_obligations=tuple(obligations),
            participating_features=tuple(_key(k, "%s participating_features[%d]" % (where, i))
                                         for i, k in enumerate(raw)),
            verification_predicate=predicate.strip())


@dataclass(frozen=True)
class InterfaceAssignment:
    """Which features realize each side, and - where the interface owes one -
    the Constraint that governs it, DECLARED HERE.

    Declared here and not referenced by key for two reasons, and both were live
    failures. A key can dangle. And a key can be reused: one constraint named
    as governing three clearances is one canonical record, which carries ONE
    `governs_interface`, so two of the three would silently read ungoverned.
    A constraint declared inside the assignment governs exactly the interface
    it sits in, and cannot be shared.
    """

    interface: str
    sides: Dict[str, Tuple[str, ...]]
    governing_constraint: Optional[SemanticConstraint] = None

    @staticmethod
    def parse(iid: str, node: Any) -> "InterfaceAssignment":
        where = "interface_assignments[%s]" % iid
        node = _obj(node, where)
        _no_extra(node, ("sides", "governing_constraint"), where)
        raw = _obj(node.get("sides"), "%s sides" % where)
        sides: Dict[str, Tuple[str, ...]] = {}
        for body, keys in sorted(raw.items()):
            if not isinstance(keys, list):
                raise SemanticError("%s sides[%s] is not a list of feature keys"
                                    % (where, body))
            sides[body] = tuple(_key(k, "%s sides[%s][%d]" % (where, body, i))
                                for i, k in enumerate(keys))
        governing = node.get("governing_constraint")
        if isinstance(governing, str):
            raise SemanticError(
                "%s governing_constraint is the name %r; the governing Constraint is DECLARED "
                "here as a record, because one constraint carries one governed interface and "
                "a shared name would leave the others ungoverned" % (where, governing))
        return InterfaceAssignment(
            interface=iid, sides=sides,
            governing_constraint=(SemanticConstraint.parse(
                governing, "%s governing_constraint" % where)
                if governing is not None else None))

    def exprs(self) -> Tuple[TypedExpr, ...]:
        return self.governing_constraint.exprs() if self.governing_constraint else ()


@dataclass(frozen=True)
class SemanticResponse:
    """What a provider may say. Features carry keys because several records
    name them; NOTHING ELSE does, so nothing else can dangle."""

    features: Tuple[SemanticFeature, ...]
    constraints: Tuple[SemanticConstraint, ...]
    realization_assignments: Dict[str, Dict[str, Tuple[str, ...]]]
    interface_assignments: Dict[str, InterfaceAssignment]
    realizations: Tuple[SemanticRealization, ...] = ()
    unresolved: Tuple[Dict[str, Any], ...] = ()
    #: region -> body -> the feature keys on that body that clear the region.
    region_assignments: Dict[str, Dict[str, Tuple[str, ...]]] = field(default_factory=dict)
    #: key -> {unit, symbol, role}, gathered from every place the name is used.
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    COLLECTIONS = ("features", "constraints", "realization_assignments",
                   "interface_assignments", "region_assignments", "realizations",
                   "unresolved")

    @staticmethod
    def parse(payload: Any) -> "SemanticResponse":
        payload = _obj(payload, "the response")
        payload = {k: v for k, v in payload.items() if not str(k).startswith("_")}
        # THE RETIRED FIELDS ARE NAMED FIRST. A response still written in an
        # older format must be told what it no longer authors, not that it
        # carries an unknown key.
        for banned, why in (
                ("kinematic_realizations",
                 "production allocates every KinematicRealization id and writes the rows from "
                 "`realization_assignments`"),
                ("construction", "a feature carries a `solid` tree; production lowers it"),
                ("parameters",
                 "a parameter is declared WHERE IT IS USED - every `param` reference carries "
                 "its unit - so there is no separate declaration list to fall out of step "
                 "with the references"),
                ("withdrawals", "this boundary writes an embodiment whole or not at all")):
            if banned in payload:
                raise SemanticError("the response carries `%s`, which it no longer authors: %s"
                                    % (banned, why))
        _no_extra(payload, SemanticResponse.COLLECTIONS, "the response")

        features = tuple(SemanticFeature.parse(f, i)
                         for i, f in enumerate(payload.get("features") or []))
        constraints = tuple(SemanticConstraint.parse(c, "constraints[%d]" % i)
                            for i, c in enumerate(payload.get("constraints") or []))
        realizations = tuple(SemanticRealization.parse(r, i)
                             for i, r in enumerate(payload.get("realizations") or []))

        raw_assign = payload.get("realization_assignments")
        if raw_assign is None:
            raise SemanticError(
                "the response states no `realization_assignments`; every declared relation "
                "this branch carries must be assigned the features that embody it")
        raw_assign = _obj(raw_assign, "realization_assignments")
        assignments: Dict[str, Dict[str, Tuple[str, ...]]] = {}
        for target, sides in sorted(raw_assign.items()):
            where = "realization_assignments[%s]" % target
            if isinstance(sides, list):
                raise SemanticError(
                    "%s is a flat list of features; a relation is embodied SIDE BY SIDE - "
                    "state the features on EACH body the relation relates, keyed by that "
                    "body, so a side cannot be left out by writing a shorter list" % where)
            sides = _obj(sides, where)
            assignments[target] = {
                body: tuple(_key(k, "%s[%s][%d]" % (where, body, i))
                            for i, k in enumerate(keys))
                for body, keys in sorted(sides.items())
                if isinstance(keys, list) or _raise_side(where, body)}

        raw_iface = payload.get("interface_assignments")
        if raw_iface is None:
            raise SemanticError(
                "the response states no `interface_assignments`; every declared interface "
                "this branch carries must have its sides assigned")
        raw_iface = _obj(raw_iface, "interface_assignments")
        interfaces = {iid: InterfaceAssignment.parse(iid, node)
                      for iid, node in sorted(raw_iface.items())}

        raw_regions = payload.get("region_assignments") or {}
        raw_regions = _obj(raw_regions, "region_assignments")
        regions: Dict[str, Dict[str, Tuple[str, ...]]] = {}
        for rid, sides in sorted(raw_regions.items()):
            where = "region_assignments[%s]" % rid
            sides = _obj(sides, where)
            regions[rid] = {
                body: tuple(_key(k, "%s[%s][%d]" % (where, body, i))
                            for i, k in enumerate(keys))
                for body, keys in sorted(sides.items())
                if isinstance(keys, list) or _raise_side(where, body)}

        unresolved = tuple(u for u in (payload.get("unresolved") or []) if isinstance(u, dict))

        exprs: List[TypedExpr] = []
        for f in features:
            exprs.extend(f.exprs())
        for c in constraints:
            exprs.extend(c.exprs())
        for a in interfaces.values():
            exprs.extend(a.exprs())
        parameters = parameter_declarations(exprs)

        response = SemanticResponse(
            features=features, constraints=constraints,
            realization_assignments=assignments, interface_assignments=interfaces,
            realizations=realizations, unresolved=unresolved, parameters=parameters,
            region_assignments=regions)
        response.check_local_keys()
        return response

    # -------------------------------------------------------------- keys
    def feature_keys(self) -> Tuple[str, ...]:
        return tuple(f.key for f in self.features)

    def parameter_keys(self) -> Tuple[str, ...]:
        return tuple(sorted(self.parameters))

    def all_constraints(self) -> Tuple[SemanticConstraint, ...]:
        """Every constraint the response states, governing ones included."""
        governing = tuple(a.governing_constraint
                          for _iid, a in sorted(self.interface_assignments.items())
                          if a.governing_constraint is not None)
        return tuple(self.constraints) + governing

    def check_local_keys(self) -> None:
        """Feature keys are unique, and every feature key named elsewhere is one
        that exists. There is no other local reference left to check: a
        parameter is declared where it is used and a constraint is named by
        nobody."""
        seen: set = set()
        for key in self.feature_keys():
            if key in seen:
                raise SemanticError("feature key %r is used twice; a local key names one "
                                    "record" % key)
            seen.add(key)
        for target, sides in sorted(self.realization_assignments.items()):
            for body, keys in sorted(sides.items()):
                for key in keys:
                    if key not in seen:
                        raise SemanticError(
                            "realization_assignments[%s][%s] names feature %r, which this "
                            "response does not declare" % (target, body, key))
        for iid, assignment in sorted(self.interface_assignments.items()):
            for body, keys in sorted(assignment.sides.items()):
                for key in keys:
                    if key not in seen:
                        raise SemanticError(
                            "interface_assignments[%s] side %s names feature %r, which this "
                            "response does not declare" % (iid, body, key))
        for rid, sides in sorted(self.region_assignments.items()):
            for body, keys in sorted(sides.items()):
                for key in keys:
                    if key not in seen:
                        raise SemanticError(
                            "region_assignments[%s][%s] names feature %r, which this response "
                            "does not declare" % (rid, body, key))
        for index, r in enumerate(self.realizations):
            for key in r.participating_features:
                if key not in seen:
                    raise SemanticError(
                        "realizations[%d] names feature %r, which this response does not "
                        "declare" % (index, key))

    def feature(self, key: str) -> Optional[SemanticFeature]:
        return next((f for f in self.features if f.key == key), None)

    def feature_body(self, key: str) -> Optional[str]:
        f = self.feature(key)
        return f.body if f else None
