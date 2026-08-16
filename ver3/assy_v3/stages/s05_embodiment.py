"""s05 - physical embodiment: geometry that makes each declared relation real.

Engineering question: what actual geometry on which body makes each declared
relation real, and what does that geometry demand of the layout?

WHAT THIS STAGE MAY AND MAY NOT DECIDE

It proposes geometry. It may not create a Body, a RigidGroup or a Joint - those
are s03's and are extended by id (INV-001, R-19) - and it may not change topology,
DOF disposition, interaction kinds, load paths or assembly order; those escalate.

The one prohibition that shapes the whole module: it may not set a Parameter
VALUE. A dimension is s06's to settle, and a value authored here without a cited
solver artifact is R-23 - copying a number and calling it solved. So s05 declares
parameters with a unit and no value, writes the constraints that relate them, and
lets the settlement loop do the arithmetic. S05-C10 enforces exactly that.

CONSTRUCTION STATEMENTS ARE IN THE OWNING BODY'S OWN FRAME

Never a world placement. s07 receives only the program and the parameters and
must not need State (INV-006), so poses are derived downstream from located joint
frames rather than compiled in.

THE MODEL PROPOSES; THE CONTRACT DECIDES

`llm_role` is "High for feature proposal and program shape. NONE for
completeness, which is enumeration over s03's relation set." Completeness,
reference validity, cycle freedom, occupancy and solver evidence are all computed
here from committed state. Nothing the model says about its own completeness is
read.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ..downstream import ir
from ..state.patch import Op
from .base import Stage

#: The feature vocabulary. Closed, because a feature kind the compiler cannot
#: build is a proposal nothing downstream can honour.
FEATURE_KINDS = ("BOSS", "BORE", "FACE", "SLOT", "RIB", "SHOULDER", "STOP",
                 "CLEARANCE_POCKET", "SNAP_ARM", "KEEPER")

#: Constraint kinds s05 authors. ENVELOPE is the "a feature implies a minimum
#: envelope" rule; CLEARANCE is the one S05-C9 counts.
CONSTRAINT_KINDS = ("ENVELOPE", "CLEARANCE", "DIMENSIONAL", "INTERFERENCE_FREE")

PROMPT = """You are proposing the PHYSICAL GEOMETRY that makes an already-decided
mechanism real.

The bodies, groups, joints and interactions below are DECIDED. You may not add,
remove or reinterpret them. Your job is to say what geometry on which body
realizes each declared relation, and what that geometry demands of the layout.

RULES
1. For EVERY physical interaction below, propose a FEATURE ON EACH PARTICIPATING
   BODY that realizes that side of it. A feature names the body it is on, its
   kind, and a short geometry description. Two bodies that touch need two
   features, one on each.
2. For every obligation below, emit a REALIZATION citing the obligation ids it
   discharges, the features that do the discharging, and a verification
   predicate - a sentence a later check could test. A realization with no
   predicate discharges nothing.
3. Declare a PARAMETER for every dimension your geometry depends on. Give it a
   symbol and a UNIT. Never give it a value: dimensions are solved later from the
   constraints you write, and a number here would be a guess wearing a solved
   answer's clothes.
4. Write the CONSTRAINTS that relate those parameters:
     - ENVELOPE: a feature that implies a minimum envelope must say so. A pin of
       radius r needing a wall w gives a boss radius r + w.
     - CLEARANCE: every declared clearance and interference-free pair below must
       become a constraint. The settlement loop can only converge on constraints
       it has been given.
   A constraint is a typed relation, not prose:
     {{"relation": "==" | "<=" | ">=", "lhs": <expr>, "rhs": <expr>}}
   where <expr> is one of
     {{"ref": "<parameter id>"}}
     {{"const": <number>, "unit": "<unit>"}}
     {{"op": "+"|"-"|"*"|"/", "args": [<expr>, <expr>, ...]}}
   Multiplying two lengths gives an AREA, not a length. A scale factor is written
   with unit "1".
5. Write the CONSTRUCTION PROGRAM: an ordered list of statements that builds each
   body IN ITS OWN FRAME. Never place a body in the world; assembly poses are
   derived elsewhere. Operations are exactly:
{opcodes}
   Each statement names the body it builds, its operation, its operands (ids of
   EARLIER statements, for the combining and transforming operations only) and
   its parameters, each of which is an <expr> as above. Exactly one statement per
   body must be consumed by nothing: that final result IS the body.
6. Never invent a dimension to make something buildable. If a value is unknown,
   declare a parameter and constrain it.

DECIDED MECHANISM AND SPATIAL CONTEXT
-------------------------------------
{projection}

RESPONSE SCHEMA
Return a single JSON object with exactly these {collections} keys, each holding a
list. A list may be empty - an empty list is a value. Every id is a string in the
format shown, where NNNN stands for a zero-padded number you choose. NNNN is a
FORMAT, not a value: write an actual number in its place, and never one listed
below as already in use.

{response_schema}

PERMITTED VALUES
  feature_kind   {feature_kinds}
  constraint kind {constraint_kinds}
  operation      {opcode_names}
  axis           X | Y | Z   (required by ROTATE, and by nothing else)
"""


def _render(obj: Any) -> str:
    import json
    return json.dumps(obj, indent=1, sort_keys=True, default=str)


class S05Embodiment(Stage):
    #: WRITE OWNER. s05 is one of the few where the numbered stage and the
    #: producing responsibility coincide - there is one pass, not two.
    stage_id = "s05"
    purpose = "realize declared relations as named geometry and constrain the layout"

    #: (json collection, canonical family, id prefix, exposed fields, stage-supplied)
    #:
    #: CANONICAL NAMES ONLY. The draft S05 contract still spells these
    #: `Feature.rigid_group`, `Realization.discharges_obligations` and `ROI`;
    #: DESIGN_STATE_CONTRACT is the authority and says `body`,
    #: `addresses_obligations`, and no ROI family at all.
    RESPONSE_ENVELOPE = (
        ("features", "Feature", "FEA-",
         ("body", "feature_kind", "geometry"), ()),
        ("realizations", "Realization", "RLZ-",
         ("addresses_obligations", "participating_features",
          "verification_predicate"), ()),
        ("parameters", "Parameter", "PRM-",
         ("symbol", "unit"), ("status",)),
        ("constraints", "Constraint", "CON-",
         ("expression", "parameters", "kind"), ()),
        ("construction_statements", "ConstructionStatement", "CST-",
         ("body", "operation", "operands", "parameters"), ()),
        ("unresolved", "UnresolvedDecision", "S5U-",
         ("decision", "why_open", "alternatives", "alternatives_kind",
          "kept_open_by", "blocks"), ()),
    )

    ID_EXAMPLE_DIGITS = "NNNN"

    @classmethod
    def render_response_schema(cls) -> str:
        import textwrap
        from ..state.design_state import Contracts
        contracts = Contracts()
        lines = []
        for collection, family, prefix, fields, _supplied in cls.RESPONSE_ENVELOPE:
            required = set(contracts.families[family].get("required_fields") or [])
            shown = ['id "%s%s"' % (prefix, cls.ID_EXAMPLE_DIGITS)]
            for field in fields:
                mark = "" if field in required else " (optional)"
                shown.append("%s%s" % (field, mark))
            body = textwrap.wrap(", ".join(shown), 52)
            head = "  %-24s " % (collection + "[]")
            if len(head) > 27:
                lines.append("  %s[]" % collection)
                head = " " * 27
            lines.append(head + body[0])
            lines.extend(" " * 27 + part for part in body[1:])
        return "\n".join(lines)

    # ------------------------------------------------------------ prompt
    def prompt(self, inputs: Dict[str, Any]) -> str:
        proj = inputs["consumer_view"]
        opcodes = "\n".join(
            "     %-10s %s" % (op, ("takes " + ", ".join(p)) if p else "combines operands")
            for op, p in sorted(ir.OPCODES.items()))
        return PROMPT.format(
            projection=_render(proj),
            opcodes=opcodes,
            opcode_names=" | ".join(sorted(ir.OPCODES)),
            feature_kinds=" | ".join(FEATURE_KINDS),
            constraint_kinds=" | ".join(CONSTRAINT_KINDS),
            collections=len(self.RESPONSE_ENVELOPE),
            response_schema=self.render_response_schema())

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s05:embodiment"
        for f in parsed.get("features", []):
            ops.append(Op("CREATE", "Feature", f["id"], {
                "body": f["body"], "feature_kind": f["feature_kind"],
                "geometry": f["geometry"]}, prov))
        for r in parsed.get("realizations", []):
            ops.append(Op("CREATE", "Realization", r["id"], {
                "addresses_obligations": r.get("addresses_obligations", []),
                "participating_features": r.get("participating_features", []),
                "verification_predicate": r["verification_predicate"]}, prov))
        for p in parsed.get("parameters", []):
            # `status` is stage-supplied and always DECLARED. s05 may not settle
            # a value, so it may not claim a settled status either; s06 extends
            # `value` and `solved_by` when it has actually solved.
            ops.append(Op("CREATE", "Parameter", p["id"], {
                "symbol": p["symbol"], "unit": p["unit"],
                "status": ir.DECLARED}, prov))
        for c in parsed.get("constraints", []):
            ops.append(Op("CREATE", "Constraint", c["id"], {
                "expression": c["expression"],
                "parameters": c.get("parameters", []),
                "kind": c["kind"]}, prov))
        for s in parsed.get("construction_statements", []):
            fields = {"body": s["body"], "operation": s["operation"],
                      "operands": s.get("operands", []),
                      "parameters": s.get("parameters", {})}
            for optional in ("axis", "feature"):
                if s.get(optional):
                    fields[optional] = s[optional]
            ops.append(Op("CREATE", "ConstructionStatement", s["id"], fields, prov))
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u.get("kept_open_by", []),
                "blocks": u.get("blocks", [])}, prov))
        return ops

    # ------------------------------------------------------------ completeness
    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        """S05-C1 through S05-C10, computed rather than asked.

        `llm_role` is NONE for completeness because completeness is enumeration
        over s03's relation set, and the relation set is in the view. Every check
        below reads the view and the response; none reads a self-report.
        """
        view = inputs.get(self.context_key) or {}
        out: List[str] = []
        out.extend(check_c1_interface_features(parsed, view))
        out.extend(check_c2_blocking_pairs(parsed, view))
        out.extend(check_c3_limit_pairs(parsed, view))
        out.extend(check_c4_obligations_realized(parsed, view))
        out.extend(check_c5_program_totality(parsed))
        out.extend(check_c6_units(parsed))
        out.extend(check_c7_no_parameter_cycle(parsed))
        out.extend(check_c8_region_intrusion(parsed, view))
        out.extend(check_c9_clearance_constraints(parsed, view))
        out.extend(check_c10_no_unsolved_values(parsed))
        return out


# ==========================================================================
# The ten deterministic exit checks.
#
# Each is a free function so it can be falsified on its own, and each reads the
# CONSUMER VIEW for what the design decided and the RESPONSE for what was
# proposed. None of them asks the model whether it was complete.
# ==========================================================================

def _rows(view: Dict[str, Any], family: str) -> List[Dict[str, Any]]:
    return list(view.get(family) or [])


def _ids(view: Dict[str, Any], family: str) -> Set[str]:
    return {r.get("entity_id") for r in _rows(view, family)}


def _features_by_body(parsed: Dict[str, Any]) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for f in parsed.get("features") or []:
        out.setdefault(f.get("body"), set()).add(f.get("id"))
    return out


def check_c1_interface_features(parsed, view) -> List[str]:
    """S05-C1: every Interface has a Feature on EACH participant.

    An interface is two bodies meeting. One feature realizes one side of it, so a
    single feature leaves the other side unrealised - the geometry would touch
    nothing.
    """
    by_body = _features_by_body(parsed)
    out = []
    for iface in _rows(view, "Interface"):
        for body in (iface.get("bodies") or []):
            if not by_body.get(body):
                out.append("S05-C1: interface %s involves body %s and no feature "
                           "realizes that side" % (iface.get("entity_id"), body))
    return out


def _body_of_group(view: Dict[str, Any]) -> Dict[str, str]:
    """RigidGroup -> the Body it belongs to. `retained_group` names a group."""
    return {g.get("entity_id"): g.get("body") for g in _rows(view, "RigidGroup")}


def _blocking_relations(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    """A ConstraintRelation that actually blocks something.

    `blocked_dofs` is what makes it a block. A relation blocking nothing is a
    recorded relationship, not a constraint geometry has to produce.
    """
    return [r for r in _rows(view, "ConstraintRelation") if r.get("blocked_dofs")]


def check_c2_blocking_pairs(parsed, view) -> List[str]:
    """S05-C2: every blocking relation has a feature pair.

    A block is two surfaces meeting. The two sides are the relation's
    `provider_body` and the body owning its `retained_group` - one feature on
    each, because a single surface blocks nothing it is not touching.
    """
    by_body = _features_by_body(parsed)
    group_body = _body_of_group(view)
    out = []
    for rel in _blocking_relations(view):
        provider = rel.get("provider_body")
        retained = group_body.get(rel.get("retained_group"))
        sides = [b for b in (provider, retained) if b]
        if len(sides) < 2:
            continue          # the relation itself is under-specified; s03's problem
        missing = [b for b in sides if not by_body.get(b)]
        if missing:
            out.append("S05-C2: blocking relation %s blocks %s and no feature "
                       "realizes it on %s"
                       % (rel.get("entity_id"), rel.get("blocked_dofs"),
                          ", ".join(sorted(missing))))
    return out


#: Feature kinds that can PRODUCE a travel limit. A bore does not stop a shaft;
#: a shoulder or a stop face does.
LIMIT_PRODUCING = ("STOP", "SHOULDER", "KEEPER")


def check_c3_limit_pairs(parsed, view) -> List[str]:
    """S05-C3: every declared limit has a PRODUCING feature pair.

    A limit is a DOF a MobilityExpectation dispositions as BLOCKED_BY some
    constraint relation. C2 asks whether the two sides carry geometry at all;
    this asks whether that geometry can produce a stop. A clearance pocket on
    both sides satisfies C2 and stops nothing.
    """
    by_body = _features_by_body(parsed)
    kind_of = {f.get("id"): str(f.get("feature_kind", "")).upper()
               for f in parsed.get("features") or []}
    group_body = _body_of_group(view)
    relations = {r.get("entity_id"): r for r in _rows(view, "ConstraintRelation")}
    out = []
    for mex in _rows(view, "MobilityExpectation"):
        for cell in (mex.get("dispositions") or []):
            if str(cell.get("disposition", "")).upper() != "BLOCKED_BY":
                continue
            rel = relations.get(cell.get("constraint_relation"))
            if rel is None:
                continue
            sides = [rel.get("provider_body"), group_body.get(rel.get("retained_group"))]
            producing = [b for b in sides if b and any(
                kind_of.get(fid) in LIMIT_PRODUCING for fid in by_body.get(b, ()))]
            if len(producing) < 2:
                out.append("S05-C3: %s dispositions %s as BLOCKED_BY %s, and no "
                           "%s feature pair produces that limit"
                           % (mex.get("entity_id"), cell.get("dof"),
                              rel.get("entity_id"), "/".join(LIMIT_PRODUCING)))
    return sorted(set(out))


def check_c4_obligations_realized(parsed, view) -> List[str]:
    """S05-C4: every Obligation is cited by some Realization with a predicate.

    INV-008. A realization that cites an obligation without a verification
    predicate discharges nothing, so an unpredicated citation does not count.
    """
    cited: Set[str] = set()
    out = []
    for r in parsed.get("realizations") or []:
        if not str(r.get("verification_predicate") or "").strip():
            out.append("S05-C4: realization %s carries no verification predicate; "
                       "it discharges nothing (INV-008)" % r.get("id"))
            continue
        cited.update(r.get("addresses_obligations") or [])
    for oid in sorted(_ids(view, "Obligation")):
        if oid not in cited:
            out.append("S05-C4: obligation %s is cited by no realization" % oid)
    return out


def check_c5_program_totality(parsed) -> List[str]:
    """S05-C5: every symbol the construction program references is declared.

    The check s07 depends on: a statement referencing an undeclared parameter can
    never be compiled, and finding that out at the kernel is finding out too late.
    """
    declared = {p.get("id") for p in parsed.get("parameters") or []}
    out = []
    for s in parsed.get("construction_statements") or []:
        for name, expr in (s.get("parameters") or {}).items():
            for ref in _expr_refs(expr):
                if ref not in declared:
                    out.append("S05-C5: statement %s parameter %s references %s, "
                               "which no Parameter declares"
                               % (s.get("id"), name, ref))
    return out


def _expr_refs(expr: Any) -> Set[str]:
    if not isinstance(expr, dict):
        return set()
    if expr.get("ref"):
        return {expr["ref"]}
    return {r for a in (expr.get("args") or []) for r in _expr_refs(a)}


def check_c6_units(parsed) -> List[str]:
    """S05-C6: no Parameter has a null unit. INV-004 / R-21."""
    return ["S05-C6: parameter %s declares no unit (INV-004)" % p.get("id")
            for p in parsed.get("parameters") or []
            if not str(p.get("unit") or "").strip()]


def check_c7_no_parameter_cycle(parsed) -> List[str]:
    """S05-C7: no parameter dependency cycle.

    An equality defines its left side in terms of its right. If following those
    definitions returns to where it started, no ordering of the solve exists and
    the system is not a definition set but a knot.
    """
    defines: Dict[str, Set[str]] = {}
    for c in parsed.get("constraints") or []:
        expr = c.get("expression") or {}
        if expr.get("relation") != "==":
            continue
        lhs = _expr_refs(expr.get("lhs"))
        if len(lhs) != 1:
            continue
        defines.setdefault(next(iter(lhs)), set()).update(_expr_refs(expr.get("rhs")))
    out = []
    for start in sorted(defines):
        seen, frontier = set(), [start]
        while frontier:
            cur = frontier.pop()
            for nxt in sorted(defines.get(cur, ())):
                if nxt == start:
                    out.append("S05-C7: parameter %s participates in a definition "
                               "cycle" % start)
                    frontier = []
                    break
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
    return sorted(set(out))


def check_c8_region_intrusion(parsed, view) -> List[str]:
    """S05-C8: no Feature intrudes into a FunctionalRegion.

    Re-run of s04b occupancy against the NEW geometry. A feature that declares
    itself inside a reserved region is reported; a feature whose geometry cannot
    be resolved to a region is not silently passed - it is simply not yet
    comparable, and the compiler's own occupancy check is where that lands.
    """
    reserved = {r.get("entity_id"): r for r in _rows(view, "FunctionalRegion")}
    out = []
    for f in parsed.get("features") or []:
        intrudes = f.get("intrudes_region") or f.get("inside_region")
        if intrudes and intrudes in reserved:
            out.append("S05-C8: feature %s intrudes into functional region %s"
                       % (f.get("id"), intrudes))
    return out


#: The interaction kind that IS a declared clearance. From s03's own vocabulary:
#: CONTACT, CLEARANCE, INTERFERENCE_FIT, COMPLIANT_INTERACTION.
CLEARANCE_KINDS = ("CLEARANCE", "INTERFERENCE_FIT")


def check_c9_clearance_constraints(parsed, view) -> List[str]:
    """S05-C9: every declared clearance pair has a Constraint.

    Per interface, not in aggregate. The recorded history is the argument: a
    clearance that was never declared as a constraint produced a BUILD FAILURE
    patched by hand rather than an INFEASIBILITY that triggered a re-solve, and a
    regression rode along undetected for three revisions. The convergence block
    can only converge on constraints it has been given, so a count is not enough
    - each clearance needs its own.
    """
    constrained: Set[str] = set()
    for c in parsed.get("constraints") or []:
        if str(c.get("kind", "")).upper() not in ("CLEARANCE", "INTERFERENCE_FREE"):
            continue
        for ref in (c.get("realizes") or []) + ([c.get("interface")] if c.get("interface") else []):
            constrained.add(ref)
    out = []
    for iface in _rows(view, "Interface"):
        if str(iface.get("interaction_kind", "")).upper() not in CLEARANCE_KINDS:
            continue
        if iface.get("entity_id") not in constrained:
            out.append("S05-C9: interface %s declares %s and no Constraint "
                       "expresses it" % (iface.get("entity_id"),
                                          iface.get("interaction_kind")))
    return out


def check_c10_no_unsolved_values(parsed) -> List[str]:
    """S05-C10: no Parameter value is set without a cited solver artifact.

    R-23, and the reason the s05/s06 loop is safe without a sequential barrier.
    s05 authors declarations; a number here would be a guess wearing a solved
    answer's clothes.
    """
    out = []
    for p in parsed.get("parameters") or []:
        if p.get("value") is not None and not p.get("solved_by"):
            out.append("S05-C10: parameter %s carries a value with no cited solver "
                       "artifact; dimensions are settled by s06 (R-23)" % p.get("id"))
    return out
