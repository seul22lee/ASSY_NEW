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

A FEATURE IS PLACED RELATIVE TO WHAT S04 COMMITTED, AND OWNS ITS CONSTRUCTION

Never an absolute position. A feature names a datum - a joint frame, its body's
envelope, a region, another feature of its body - and an offset in the kernel
unit; its construction steps are in its own frame; a body is composed from its
features by declared polarity. s07 derives every transform and every pose from
s04's frames, the scale authority and the settled numbers (Unit G).

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

from ..downstream import embodiment, ir
from ..state.patch import Op
from ..view import DISCHARGE, PRESERVE, applicable_obligation_ids, obligation_duties
from .base import Stage

def _feature_kind_vocabulary() -> Tuple[str, ...]:
    """Feature.feature_kind's declared values - read from the canonical contract.

    UNIT G. The vocabulary used to be this module's own tuple, unvalidated, and
    the mating kinds s04 states on an interface (SHAFT, PIN, BORE, GUIDE ...)
    were a second vocabulary nothing compared. One list now, declared where the
    family is declared, enforced by the write boundary, and a superset of the
    mating kinds so a realized side is checkable by the same word.
    """
    from ..state.design_state import Contracts
    spec = (Contracts().families.get("Feature") or {}).get("field_semantics") or {}
    return tuple((spec.get("feature_kind") or {}).get("values") or ())


#: The feature vocabulary. Closed, because a feature kind the compiler cannot
#: build is a proposal nothing downstream can honour.
FEATURE_KINDS = _feature_kind_vocabulary()


def _polarity() -> Dict[str, Tuple[str, ...]]:
    from ..state.design_state import Contracts
    table = (Contracts().families.get("Feature") or {}).get("feature_kind_polarity") or {}
    return {pol: tuple(kinds or ()) for pol, kinds in table.items()}


FEATURE_KIND_POLARITY = _polarity()

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
   BODY that realizes that side of it, and name in `interface` the Interface it
   realizes - the interaction's `at_interface`, an Interface id from the input.
   Two bodies that touch need two features, one on each, both naming that same
   interface. A feature that realizes an obligation rather than an interface
   names none. Never name an interface that is not in the input: interactions
   are decided upstream and you may not add, remove or reinterpret one.
   A feature names the body it is on, its kind, and a short geometry
   description.
   PLACEMENT. Every feature carries a `placement` RELATIVE TO SOMETHING THE
   DESIGN HAS ALREADY COMMITTED (see GRAMMAR): a `datum` that is a Joint id
   (the feature sits on that joint's located axis), the body's own Envelope id
   (the feature sits at the body's centre), a FunctionalRegion id, or an
   earlier feature of the SAME body; an optional `offset` of three <expr>s in
   mm along the arrangement axes; and the feature's own `axis` where it has
   one (a stock block at its envelope has none: the arrangement's +Z). Never
   state a position of your own.
   STOCK. Every body needs material: give each body one STOCK feature (its
   plate, block or shell), placed at the body's Envelope, and place the
   body's other features against that STOCK or against a joint.
   JOINTS. Every joint listed under JOINTS TO REALIZE relates two bodies
   about an axis. On EACH of those two bodies, the feature(s) that carry
   that joint - the bore and the pin, the rail and the guide - are placed
   with that joint as their `datum`; that placement IS the realization.
   Poses are derived from the joint frames and the joint coordinates; you
   never state a pose.
   MATING. Where an interface below carries `mating_geometry`, the feature
   on its `inner_body` is of the `inner_feature` kind and the feature on its
   `outer_body` of the `outer_feature` kind.
2. THE OBLIGATIONS BELOW ARE SPLIT INTO TWO DUTIES. For every obligation under
   DISCHARGE emit a REALIZATION citing the obligation ids it discharges, the
   features that do the discharging, and a verification predicate - a sentence a
   later check could test. A realization with no predicate discharges nothing.
   Every obligation under PRESERVE was already discharged by the selected
   mechanism's own upstream records - its interactions, routes and motions -
   and your geometry realizes those records; do NOT cite a preserved obligation
   as discharged, and do not cite an obligation that is not listed at all.
   Obligations belonging to an alternative that was not selected are not shown
   and are not yours.
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
   A CLEARANCE or INTERFERENCE_FREE constraint must also name the interface it
   governs, as `governs_interface`. A declared clearance with no constraint
   naming it is a clearance the settlement loop was never given.
   A constraint is a typed relation, not prose (GRAMMAR below). Multiplying two
   lengths gives an AREA, not a length. A scale factor is written with unit "1".
   Every number anywhere in your response - a constraint, an offset, a step
   parameter - is a unit-bearing constant or a parameter reference, and
   NEVER a bare number.
5. Where a degree of freedom below is dispositioned BLOCKED_BY a constraint
   relation, the geometry must PRODUCE that limit: a pair of features that
   actually stops the motion, one on each side of the relation. A clearance
   pocket on both sides satisfies "two features touch" and stops nothing.
6. Do not remove what the design has already established. Where states,
   motions, swept volumes or load routes appear below, they were proven against
   the arrangement you are embodying: a feature placed into a path already shown
   clear turns a moving design into one that binds, and material cut from a
   member on a load route removes what carries the load. If your geometry cannot
   respect one of them, say so in `unresolved` rather than quietly overriding it.
   The envelopes, regions, scale and mating sizes below are the PROVISIONAL
   arrangement s04 committed, in s04's own basis: respect where things sit
   relative to each other, and never copy a provisional extent, representative
   size or region into a constant and present it as a dimension. A constant in
   a constraint is either a bound the design actually states (`basis`
   STATED_BOUND - a hard requirement, a rule you can name) or a design choice
   you make and mark as one (`basis` DESIGN_CHOICE); every other size is a
   parameter related to others (`basis` GEOMETRIC_RELATION).
7. Give every feature its CONSTRUCTION: an ordered list of steps, in the
   feature's own frame (origin at the placement, Z along its axis), each with
   a short local `id`, an `operation` from the GRAMMAR, `operands` (ids of
   EARLIER steps of the same feature, for combining and transforming
   operations only) and `parameters`, an OBJECT of named <expr>s. Exactly one
   step must be consumed by nothing: that result IS the feature's solid. A
   body is its ADDITIVE features fused with its SUBTRACTIVE features removed
   (the kinds are listed under PERMITTED VALUES); a BORE is the cylinder that
   is removed, a BOSS the cylinder that is added.
8. CLOSE THE SYSTEM. The settlement is a solve, not a guess: every parameter
   an offset or a construction step reads must be determined by the
   constraints you write - each by a GEOMETRIC_RELATION to other parameters,
   a STATED_BOUND, or a DESIGN_CHOICE (`==` a unit-bearing constant, marked
   `basis` DESIGN_CHOICE). Choices are yours to make - a wall thickness, a pin
   diameter, a clearance - and they must be visible as choices, never
   presented as facts; a parameter no constraint determines is a free
   direction the solver reports back, and nothing can be built from it. Do
   not give a parameter a value directly (rule 3); close it with a constraint.
9. SCALE. The arrangement below is stated in a basis (the ReferenceScale). If
   that basis is RELATIVE, the design has no absolute size until something
   states one: declare ONE parameter in mm with `role` "SCALE", meaning "mm
   per basis unit", and close it like any other parameter - from a stated
   bound where one exists (`basis` STATED_BOUND), otherwise by a design
   choice marked as such (`basis` DESIGN_CHOICE), consistent with the mm
   dimensions you choose for the features. Every feature is placed against
   the arrangement THROUGH this scale, so an unclosed scale leaves nothing
   placeable. If the basis is ABSOLUTE, declare no SCALE parameter.
10. HARD REQUIREMENTS. Every requirement listed under HONOUR applies to this
   design and your geometry must be compatible with it. Every compliance record
   listed under OWED is a hard requirement THIS embodiment stage owes evidence
   for and cannot yet establish: it stays NOT_YET_EVALUABLE until that evidence
   exists. Do not assert or imply that any of them is satisfied, and do not cite
   one as an obligation. Where your geometry turns on something such a
   requirement bears on, declare the parameter it turns on and record what is
   still open in `unresolved`.

OBLIGATION DUTIES OF THIS EMBODIMENT
------------------------------------
{duties}

JOINTS TO REALIZE
-----------------
{joint_duties}

SETTLEMENT FEEDBACK
-------------------
{settlement_feedback}

HARD REQUIREMENTS
-----------------
{hard_requirements}

GRAMMAR
-------
{grammar}

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
    ADDITIVE     {additive_kinds}
    SUBTRACTIVE  {subtractive_kinds}
  constraint kind {constraint_kinds}
  operation      {opcode_names}
  placement axis {signed_axes}
  ROTATE axis    {rotate_axes}   (required by ROTATE, and by nothing else)
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
         ("body", "feature_kind", "geometry", "interface", "placement",
          "construction"), ()),
        ("realizations", "Realization", "RLZ-",
         ("addresses_obligations", "participating_features",
          "verification_predicate"), ()),
        ("parameters", "Parameter", "PRM-",
         ("symbol", "unit", "role"), ("status",)),
        ("constraints", "Constraint", "CON-",
         ("expression", "parameters", "kind", "basis", "governs_interface"), ()),
        ("unresolved", "UnresolvedDecision", "S5U-",
         ("decision", "why_open", "alternatives", "alternatives_kind",
          "kept_open_by", "blocks"), ()),
    )

    ID_EXAMPLE_DIGITS = "NNNN"

    # ------------------------------------------------------------------
    # THE SELECTION THIS INVOCATION EMBODIES
    # ------------------------------------------------------------------
    def selected_candidate(self, view: Dict[str, Any]) -> Optional[str]:
        """The committed candidate, read from the view s05 was actually given.

        From the VIEW rather than from DesignState or from a caller argument.
        The view is what was recorded and what a reviewer reads back, and a
        second path to the same fact would be a second answer to which design
        this geometry is for. `SelectionDecision.selected_candidate` is the one
        authority; nothing here keeps a parallel `selected_branch`.
        """
        for row in _rows(view, "SelectionDecision"):
            value = row.get("selected_candidate")
            if isinstance(value, str) and value:
                return value
        return None

    def selection_decision(self, view: Dict[str, Any]) -> Optional[str]:
        for row in _rows(view, "SelectionDecision"):
            if row.get("entity_id"):
                return row["entity_id"]
        return None

    def invocation_premises(self, inputs: Dict[str, Any]) -> List[str]:
        """Everything this invocation authors rests on the commitment that chose it.

        Two entities, and they are different facts. The Candidate is the
        mechanism being embodied - withdraw it and the geometry describes
        nothing. The SelectionDecision is the COMMITMENT to that mechanism -
        withdraw it and the geometry describes something real that the design is
        no longer pursuing. Recording only the candidate would leave embodiment
        standing through a reopened selection, which is exactly the state a
        reviewer must be able to see is stale.

        Local premises are not replaced. `carry_invocation_premises` unions and
        dedups, so a Constraint still rests on its parameters and its governed
        interface as well as on the selection.
        """
        view = (inputs or {}).get(self.context_key) or {}
        return [e for e in (self.selected_candidate(view),
                            self.selection_decision(view)) if e]

    # THE BRANCH IS THE SELECTION'S, NOT A CALLER'S. This class used to carry
    # its own override refusing an invocation that named a candidate other than
    # the committed one. That rule is now the generic builder's, declared by
    # `branch_authority: SELECTION_DECISION` on the s05 responsibility (Unit E):
    # the view is built on the committed branch whatever a caller passes, and a
    # contradicting invocation is recorded and leaves the view UPSTREAM_
    # INSUFFICIENT, which `invoke` refuses to call a provider on. Nothing here
    # keeps a second copy of that rule.

    @classmethod
    def render_response_schema(cls) -> str:
        import textwrap
        from ..state.design_state import Contracts
        contracts = Contracts()
        lines = []
        for collection, family, prefix, fields, _supplied in cls.RESPONSE_ENVELOPE:
            spec = contracts.families[family]
            required = set(spec.get("required_fields") or [])
            semantics = spec.get("field_semantics") or {}
            shown = ['id "%s%s"' % (prefix, cls.ID_EXAMPLE_DIGITS)] if prefix else []
            for field in fields:
                mark = "" if field in required or prefix is None else " (optional)"
                spec_f = semantics.get(field) or {}
                nested = spec_f.get("record_field_semantics")
                if nested:
                    inner = ", ".join("%s%s" % (n, "" if sub.get("required") else "?")
                                      for n, sub in nested.items())
                    shape = "[{%s}]" if spec_f.get("kind") == "record_list" else "{%s}"
                    shown.append("%s%s %s" % (field, mark, shape % inner))
                elif spec_f.get("kind") == "enum" and spec_f.get("values"):
                    # A CLOSED VOCABULARY, from the contract: shown beside the
                    # field, so a role or a kind is never guessed from the name.
                    shown.append("%s%s in {%s}" % (field, mark, " | ".join(str(v) for v in spec_f["values"])))
                elif spec_f.get("kind") == "reference":
                    # WHAT A REFERENCE MAY NAME, from the contract (Unit G). A
                    # field typed as a reference to declared families is shown
                    # with those families, so "which ids go here" is never left
                    # to be guessed from the field's name.
                    target = spec_f.get("target")
                    targets = target if isinstance(target, list) else [target]
                    many = spec_f.get("cardinality") == "many"
                    shown.append("%s%s -> %s id%s" % (field, mark, " | ".join(str(t) for t in targets),
                                                      "s" if many else ""))
                else:
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
    @staticmethod
    def render_grammar() -> str:
        """The embodiment language, RENDERED FROM THE IR (Unit G).

        Expression forms, relations, arithmetic, units, the typed zero, the
        signed axes, the placement grammar and its frame convention, and every
        opcode with its semantics - each read from `downstream.ir`, so the
        language the model is shown is the language the boundary enforces and
        the kernel executes. Nothing here is a second copy.
        """
        zero = '{"const": 0, "unit": "%s"}' % ir.KERNEL_LENGTH_UNIT
        parameter_prefix = next(prefix for _c, family, prefix, _f, _s in S05Embodiment.RESPONSE_ENVELOPE
                                if family == "Parameter")
        lines = [
            "<expr> is exactly one of",
            '  {"ref": "<parameter id>"}   - the id "%s%s" of a parameter you declare, '
            'never its symbol' % (parameter_prefix, S05Embodiment.ID_EXAMPLE_DIGITS),
            '  {"const": <number>, "unit": "<unit>"}',
            '  {"op": %s, "args": [<expr>, <expr>, ...]}'
            % " | ".join('"%s"' % o for o in ir.ARITHMETIC),
            '  {"op": "-", "args": [<expr>]}   - negation',
            "A constraint expression is",
            '  {"relation": %s, "lhs": <expr>, "rhs": <expr>}'
            % " | ".join('"%s"' % r for r in ir.RELATIONS),
            "Units: lengths in %s, angles in %s - every constant in those units, never "
            "another; a dimensionless factor has unit \"1\"." % (ir.KERNEL_LENGTH_UNIT,
                                                                 ir.KERNEL_ANGLE_UNIT),
            "A coordinate at a frame origin is the typed zero %s - a coordinate "
            "definition, not a dimension." % zero,
            "",
            "FRAMES. The arrangement frame the envelopes, regions and joint origins "
            "below are stated in is THE frame; every body frame coincides with it at "
            "zero joint coordinates. A feature is placed RELATIVE to a committed datum:",
            '  {"datum": "<Joint | Envelope | FunctionalRegion | Feature id>", '
            '"offset": [<expr>, <expr>, <expr>], "axis": %s}'
            % " | ".join('"%s"' % a for a in ir.SIGNED_AXES),
            "  datum: WHERE the feature sits - a Joint (its located frame), the body's own "
            "Envelope (its centre), a FunctionalRegion (its centre), or an earlier feature of "
            "the same body (its frame). A datum locates; it does not orient;",
            "  offset: optional, three <expr>s in %s along the arrangement axes, default "
            "zero;" % ir.KERNEL_LENGTH_UNIT,
            "  axis: HOW the feature is oriented - its own axis (a bore's, a pin's, a "
            "slide's, a face's normal) as a signed arrangement axis. Omitted at a joint it "
            "is the joint's, which is what a bore, a pin or a bearing wants; omitted against "
            "an envelope or a region it is the arrangement's +Z; omitted against a feature "
            "it is that feature's. YOU MAY STATE A DIFFERENT AXIS AT A JOINT, and it means "
            "\"located by this joint, oriented otherwise\" - a face whose normal crosses the "
            "hinge line, a snap arm projecting across it. But a joint is REALIZED only by a "
            "feature at it that LIES ON ITS AXIS: the bore or pin that makes the joint what "
            "it is must be on the joint's own axis, and a feature oriented otherwise is "
            "positioned by the joint without embodying it.",
            "BASIS NUMBERS. The arrangement's own numbers - envelope extents and centres, "
            "joint origins, region volumes - are in the ReferenceScale basis and are "
            "DIMENSIONLESS: written as constants they carry unit \"1\", never \"%s\". A "
            "length in %s that follows from one is scale x basis number: e.g. "
            '{"op": "*", "args": [{"ref": "<SCALE parameter>"}, {"const": 100, "unit": "1"}]}.'
            % (ir.KERNEL_LENGTH_UNIT, ir.KERNEL_LENGTH_UNIT),
            "The feature frame has Z along its axis, origin at datum + offset, and X along "
            "the canonical perpendicular (Z->X, X->Y, Y->Z, positive); the feature's "
            "construction is built in it.",
            "",
            "Operations (parameters are an object of named <expr>s; operands are ids of "
            "EARLIER steps of the same feature):",
        ]
        for op, params in sorted(ir.OPCODES.items()):
            if op in ir.COMBINING:
                shape = "operands: two or more; parameters: none"
            elif op in ir.TRANSFORMING:
                shape = "operands: exactly one; takes " + ", ".join(params)
            else:
                shape = "operands: none; takes " + ", ".join(params)
            lines.append("  %-10s %-44s %s" % (op, shape, ir.OPCODE_SEMANTICS.get(op, "")))
        lines.append("  ROTATE also names `axis`, one of %s." % " | ".join(ir.AXES))
        lines.append("  A combining operation has no parameters of its own: what it combines is "
                     "an earlier step OF THE SAME FEATURE, named as an operand.")
        lines.append("  A feature never names another feature, or another feature's step, as an "
                     "operand.")
        lines.append("")
        # THE ONE STATEMENT, from the IR that enforces it and the compiler that
        # executes it. A subtractive feature that writes CUT to mean "remove me
        # from the body" is the error this paragraph exists to prevent.
        lines.append("POLARITY, NOT A STEP.")
        for sentence in ir.CONSTRUCTION_SEMANTICS.split(". "):
            sentence = sentence.strip()
            if sentence:
                lines.append("  " + sentence + ("" if sentence.endswith(".") else "."))
        return "\n".join(lines)

    def prompt(self, inputs: Dict[str, Any]) -> str:
        proj = inputs["consumer_view"]
        return PROMPT.format(
            projection=_render(proj),
            duties=render_duties(proj),
            hard_requirements=render_hard_requirements(proj),
            grammar=self.render_grammar(),
            joint_duties=render_joint_duties(proj),
            settlement_feedback=render_settlement_feedback(inputs),
            opcode_names=" | ".join(sorted(ir.OPCODES)),
            feature_kinds=" | ".join(FEATURE_KINDS),
            additive_kinds=" | ".join(FEATURE_KIND_POLARITY.get("ADDITIVE", ())),
            subtractive_kinds=" | ".join(FEATURE_KIND_POLARITY.get("SUBTRACTIVE", ())),
            constraint_kinds=" | ".join(CONSTRAINT_KINDS),
            signed_axes=" | ".join(ir.SIGNED_AXES),
            rotate_axes=" | ".join(ir.AXES),
            collections=len(self.RESPONSE_ENVELOPE),
            response_schema=self.render_response_schema())

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        """Every output carries the premises it was derived FROM.

        This is what puts s05 into the currentness graph rather than beside it.
        `_propagate` walks `_premises`, so an entity that records none is an
        entity no upstream change can ever stale - it would sit in state looking
        authoritative after the decision it rests on had been withdrawn.

        The premises are not invented: a Realization rests on the obligations it
        discharges and the features that do the discharging, a Feature rests on
        the body it is on, a statement rests on the body it builds, the results
        it consumes and the parameters it reads. Each is already a declared
        reference; recording it as a premise is saying that the dependency is
        real in the direction currentness walks.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s05:embodiment"
        # The basis every envelope coordinate is expressed in. Taken from the
        # view rather than rebuilt from an id convention, because the scale is a
        # committed entity and guessing its name in a second place is how two
        # spellings of one id start. s04 states the rule this follows: withdraw
        # the basis and the numbers mean nothing.
        scales = sorted(_ids(inputs.get(self.context_key) or {}, "ReferenceScale")) \
            if inputs else []
        for f in parsed.get("features", []):
            fields = {"body": f["body"], "feature_kind": f["feature_kind"],
                      "geometry": f["geometry"], "placement": f.get("placement"),
                      "construction": f.get("construction")}
            premises = [f["body"]]
            if f.get("interface"):
                # THE TYPED TRACE (Unit E): which s03 interface this feature
                # realizes a side of. A reference the boundary resolves, and a
                # premise, so a revised interface stales the geometry that
                # realized it. Never inferred from prose or from the body.
                fields["interface"] = f["interface"]
                premises.append(f["interface"])
            # THE DATUM AND THE PARAMETERS (Unit G). The feature rests on the s04
            # commitment it is placed against - move the joint frame and the
            # feature is stale - on the scale every datum coordinate is stated
            # in, and on every parameter its offset or construction reads. The
            # grammar is the IR's; the boundary refuses a malformed record by
            # name, so only references are read here.
            placement = f.get("placement") if isinstance(f.get("placement"), dict) else {}
            if placement.get("datum"):
                premises.append(placement["datum"])
                premises += scales
            refs: Set[str] = set()
            for component in placement.get("offset") or []:
                refs |= _expr_refs(component)
            for step in f.get("construction") or []:
                params = step.get("parameters") if isinstance(step, dict) else None
                for expr in (params.values() if isinstance(params, dict) else []):
                    refs |= _expr_refs(expr)
            premises += sorted(refs)
            ops.append(Op("CREATE", "Feature", f["id"], fields, prov, premise_refs=premises))
        for r in parsed.get("realizations", []):
            obligations = list(r.get("addresses_obligations") or [])
            features = list(r.get("participating_features") or [])
            ops.append(Op("CREATE", "Realization", r["id"], {
                "addresses_obligations": obligations,
                "participating_features": features,
                "verification_predicate": r["verification_predicate"]}, prov,
                premise_refs=obligations + features))
        for p in parsed.get("parameters", []):
            fields = {"symbol": p["symbol"], "unit": p["unit"], "status": ir.DECLARED}
            if p.get("role"):
                # UNIT G. A declared ROLE - SCALE: kernel units per basis unit,
                # the one scale authority s05 may declare for a RELATIVE basis.
                # s04's ReferenceScale is not written for it.
                fields["role"] = p["role"]
            ops.append(Op("CREATE", "Parameter", p["id"], fields, prov))
        for c in parsed.get("constraints", []):
            fields = {"expression": c["expression"],
                      "parameters": c.get("parameters", []),
                      "kind": c["kind"]}
            if c.get("basis"):
                # WHAT THE CONSTRAINT RESTS ON (Unit G): a relation, a stated
                # bound, or a design choice - the choice is this stage's and
                # stays visible as one.
                fields["basis"] = c["basis"]
            premises = list(c.get("parameters") or [])
            if c.get("governs_interface"):
                # A typed reference AND a premise: the constraint expresses that
                # interface's clearance, so a change to the interface withdraws
                # standing from the constraint that spoke for it.
                fields["governs_interface"] = c["governs_interface"]
                premises.append(c["governs_interface"])
            ops.append(Op("CREATE", "Constraint", c["id"], fields, prov,
                          premise_refs=premises))
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u.get("kept_open_by", []),
                "blocks": u.get("blocks", [])}, prov))
        return ops

    # ------------------------------------------------------------ repair
    def repair_operations(self, ops: List[Op], inputs: Dict[str, Any], state,
                          parsed: Optional[Dict[str, Any]] = None) -> List[Op]:
        """A settlement-feedback round REVISES the embodiment that stands (Unit G).

        The boundary's own vocabulary, through the shared helper: a restated
        standing id becomes a SUPERSEDE of the fields that differ, under this
        round's reason; a stale one is invalidated and re-created; nothing is
        re-minted beside itself and nothing is deleted.
        """
        from .base import REPAIR_KEY, revise_standing_operations
        parsed = parsed or {}
        repair = (inputs or {}).get(REPAIR_KEY) or {}
        codes = sorted({r.get("code") for r in (repair.get("findings") or [])
                        if isinstance(r, dict) and r.get("code")})
        reason = "s05 embodiment revision after settlement round %s: %s" % (
            repair.get("round"), ", ".join(codes) or "feedback")
        withdrawals = self._declared_withdrawals(parsed, ops, inputs, state)
        retracted = [Op("INVALIDATE", family, eid, {}, self.PROVENANCE,
                        reason="%s | withdrawn answering %s: %s" % (reason, cause, why))
                     for family, eid, why, cause in withdrawals]
        return retracted + revise_standing_operations(state, ops, reason)

    #: This stage's provenance, and the mark of a record it authored.
    PROVENANCE = "s05:embodiment"

    @classmethod
    def embodiment_families(cls) -> Tuple[str, ...]:
        """THE EMBODIMENT, by family, derived from the contract rather than
        listed here: everything `owned_by: s05`, plus the universally ownable
        families this stage also authors into. A hand-kept list is how a family
        comes to be revised by one rule and snapshotted by another - Realization
        and UnresolvedDecision were authored by `to_operations` and absent from
        both, so a revision could neither restate nor withdraw them and the
        branch kept a mix of two embodiments.
        """
        from ..state.design_state import Contracts
        contracts = Contracts()
        families = contracts.families
        owned = [f for f in families if contracts.owner_of(f) == cls.stage_id]
        return tuple(sorted(owned) + sorted(contracts.universally_ownable & set(families)))

    def embodiment_snapshot(self, state, branch: Optional[str]) -> Dict[str, List[str]]:
        """What of this branch's embodiment stands, by family and id.

        ONE DEFINITION, THREE USES: it is what the repair prompt shows the model,
        what a revision withdraws by omission, and what the loop's repeated-state
        identity is taken over. Two of those disagreeing is a revision that
        withdraws what the model was never shown.

        THIS BRANCH WHERE THERE IS ONE: `_premises` is the membership the
        architecture already records, and reading by family alone would take in
        a sibling candidate's embodiment. Where no branch is named - a design
        that has not branched, or a diagnostic reading the whole state - it is
        every record this stage authored. Returning NOTHING there was wrong in a
        way that mattered: the loop takes its repeated-state identity over this
        snapshot, and a constant identity made every second round read as a
        cycle no matter how much the embodiment had changed. The branch-only
        safety belongs to withdrawal, which refuses outright without one, not to
        the question "what stands".

        A universally ownable family is included only where THIS stage authored
        the record, because s05 may not speak for an Assumption another
        responsibility wrote.
        """
        from ..state.design_state import Contracts
        shared = Contracts().universally_ownable
        out: Dict[str, List[str]] = {}
        for family in self.embodiment_families():
            rows = [rec["entity_id"]
                    for rec in sorted(state.standing(family), key=lambda r: r["entity_id"])
                    if (not branch or branch in (rec.get("_premises") or []))
                    and not (family in shared and rec.get("_provenance") != self.PROVENANCE)]
            if rows:
                out[family] = rows
        return out

    def _repair_scope(self, repair: Dict[str, Any], state, snapshot_ids) -> set:
        """WHAT THIS ROUND IS AUTHORIZED TO REMOVE.

        The report named the trouble: the constraints in conflict, the
        parameters left free, the subjects of each prerequisite finding. Those
        ids, and the records of this branch's embodiment that REST on one of
        them, are what a revision may retract - a constraint that cannot hold
        goes, and so may the parameter that existed only to state it. Nothing
        else. A round asked to settle a bore diameter has no authority over a
        feature the report never mentioned, and would need none to answer.
        """
        named: set = set()
        for row in repair.get("findings") or []:
            if not isinstance(row, dict):
                continue
            named |= {row.get("constraint"), row.get("parameter")} - {None}
            named |= {s for s in (row.get("subjects") or []) if isinstance(s, str)}
        scope = set(named)
        for eid in snapshot_ids:
            rec = state.entities.get(eid) or {}
            if named & set(rec.get("_premises") or []):
                scope.add(eid)
        return scope

    def _declared_withdrawals(self, parsed: Dict[str, Any], ops: List[Op],
                              inputs: Dict[str, Any], state):
        """WITHDRAWAL IS AN ACT, AND IT IS STATED (Unit G).

        An earlier version read omission as withdrawal: whatever the revised
        response did not restate stopped standing. That made an engineering
        decision out of a model's silence - a response that simply did not
        mention a feature retired it, and a truncated or forgetful answer could
        quietly demolish the parts of the embodiment nobody was asking about.
        Withdrawal is now DECLARED and TYPED: the entity, why, and which of this
        round's findings it answers. What the response omits keeps standing
        exactly as it was.

        Each one is checked before it is an operation: the entity must be part
        of THIS branch's standing embodiment in a family this stage authors, the
        stated family must be the one it actually has, the cause must be a
        finding of this round, the report must have named it (or something it
        rests on), and the same response may not both restate and withdraw it.
        A withdrawal that fails any of these refuses the response rather than
        being dropped - a repair that reaches outside its mandate is not a
        repair to accept in part.
        """
        from .base import REPAIR_KEY, StageError

        declared = parsed.get("withdrawals") or []
        if not declared:
            return ()
        branch = (inputs or {}).get("candidate")
        if not branch:
            # A withdrawal retires part of ONE branch's embodiment. Without a
            # named candidate there is nothing to confine it to, and retiring
            # by family alone would reach into every other candidate.
            raise StageError("this invocation names no candidate, so nothing can be withdrawn: "
                             "a withdrawal retires part of one branch's embodiment")
        repair = (inputs or {}).get(REPAIR_KEY) or {}
        snapshot = self.embodiment_snapshot(state, branch)
        family_of = {eid: family for family, ids in snapshot.items() for eid in ids}
        scope = self._repair_scope(repair, state, family_of)
        causes = {row.get("code") for row in repair.get("findings") or []
                  if isinstance(row, dict)}
        restated = {op.entity_id for op in ops}
        out = []
        for item in declared:
            if not isinstance(item, dict):
                raise StageError("a withdrawal is a record stating entity, cause and reason; "
                                 "%r is not" % (item,))
            eid = item.get("entity")
            reason = str(item.get("reason") or "").strip()
            cause = item.get("cause")
            family = family_of.get(eid)
            if not eid or not reason:
                raise StageError("withdrawal %r states no entity or no reason; a record is "
                                 "never withdrawn without saying which and why" % (item,))
            if family is None:
                raise StageError("withdrawal names %s, which is not part of this branch's "
                                 "standing embodiment; only what this stage authored for this "
                                 "selection may be withdrawn here" % eid)
            if item.get("family") and item["family"] != family:
                raise StageError("withdrawal calls %s a %s; it is a %s"
                                 % (eid, item["family"], family))
            if cause not in causes:
                raise StageError("withdrawal of %s cites %r, which is not a finding of this "
                                 "round (%s)" % (eid, cause, ", ".join(sorted(c for c in causes if c))))
            if eid not in scope:
                raise StageError("withdrawal of %s is outside this round's repair scope: the "
                                 "report named neither it nor anything it rests on" % eid)
            if eid in restated:
                raise StageError("%s is both restated and withdrawn in one response; a record is "
                                 "revised or retracted, not both" % eid)
            out.append((family, eid, reason, cause))
        return tuple(out)

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
        out.extend(check_c5_program_totality(parsed, view))
        out.extend(check_c6_units(parsed))
        out.extend(check_c7_no_parameter_cycle(parsed))
        out.extend(check_c9_clearance_constraints(parsed, view))
        out.extend(check_c10_no_unsolved_values(parsed))
        out.extend(check_c11_joints_realized(parsed, view))
        out.extend(check_c12_bodies_built(parsed, view))
        out.extend(check_c14_mating_kinds(parsed, view))
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


def embodiment_duties(view: Dict[str, Any]) -> Dict[str, Set[str]]:
    """{DISCHARGE, PRESERVE} for the selected candidate, from the one rule.

    DELEGATES to `obligation_duties` exactly as `applicable_obligations_for_
    embodiment` delegates to `applicable_obligation_ids`: the prompt lists the
    two duties from the recorded payload and S05-C4 judges against the same
    payload by the same function, so the stage cannot be asked one thing and
    marked against another (Unit E).
    """
    return obligation_duties(_rows(view, "Obligation"),
                             _rows(view, "AcceptanceContract"), "s05")


def owed_hard_requirements(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The compliance records in the view. THE VIEW ALREADY NARROWED THEM: the
    `hard_requirement_debt_to_carry` premise admits only records that are
    NOT_YET_EVALUABLE at a DOWNSTREAM point and name s05 as evidence owner, so
    what is here is exactly the debt this embodiment owes and nothing is
    re-decided from a status or a kind."""
    return sorted(_rows(view, "HardRequirementCompliance"),
                  key=lambda r: str(r.get("entity_id")))


def render_duties(view: Dict[str, Any]) -> str:
    duties = embodiment_duties(view)
    statements = {r.get("entity_id"): r for r in _rows(view, "Obligation")}

    def block(title, ids):
        lines = [title]
        if not ids:
            lines.append("  (none)")
        for oid in sorted(ids):
            rec = statements.get(oid) or {}
            lines.append("  - %s (satisfiable at %s): %s"
                         % (oid, rec.get("satisfiable_at"), rec.get("statement")))
        return lines
    return "\n".join(
        block("DISCHARGE - cite each of these in a realization with a predicate:",
              duties[DISCHARGE])
        + block("PRESERVE - already discharged by the selected mechanism's upstream "
                "records; realize those records, never cite these as discharged:",
                duties[PRESERVE]))


def render_joint_duties(view: Dict[str, Any]) -> str:
    """The joints this embodiment must realize, DERIVED from the view (Unit G).

    The same shape as the obligation duties: enumeration over s03's joint set,
    resolved through s03's groups to the bodies each joint relates, with the
    axis s03 declared and whether s04 located the frame. What must be
    embodied is read from the topology, never from a mechanism class, and it
    is rendered as a list rather than left as a rule to be applied.
    """
    from ..downstream.embodiment import AXIS_REALIZING_JOINTS
    groups = _body_of_group(view)
    lines = []
    for joint in sorted(_rows(view, "Joint"), key=lambda j: j.get("entity_id") or ""):
        kind = str(joint.get("joint_type", "")).upper()
        if kind not in AXIS_REALIZING_JOINTS:
            continue
        bodies = sorted({groups.get(joint.get("parent_group")), groups.get(joint.get("child_group"))}
                        - {None})
        located = isinstance(joint.get("frame_origin"), list)
        lines.append("  %s  %s about %s  %s: on EACH of %s, the feature(s) carrying this joint "
                     "are placed with datum %s" % (
                         joint.get("entity_id"), kind, joint.get("axis_direction"),
                         "(frame located by s04)" if located else "(frame NOT located by s04)",
                         ", ".join(bodies) or "no resolvable body", joint.get("entity_id")))
    return "\n".join(lines) if lines else "  none - no axis-bearing joint is in this branch"


#: The solver's own report, on an embodiment the gate admitted. A STRUCTURAL
#: cause is not one of these: it arrives as a typed prerequisite finding from
#: `downstream.embodiment`, keeps its own kind, and asks for different work.
SETTLEMENT_INFEASIBLE = "SETTLEMENT_INFEASIBLE"
SETTLEMENT_UNDERDETERMINED = "SETTLEMENT_UNDERDETERMINED"
SETTLEMENT_UNSUPPORTED = "SETTLEMENT_UNSUPPORTED"


def render_settlement_feedback(inputs: Optional[Dict[str, Any]]) -> str:
    """What s06 found when it tried to settle the embodiment that stands, and
    what this invocation is therefore asked to do (Unit G).

    A REPAIR invocation carries the solver's report as findings: for an
    infeasible system, the constraints that conflict and by how much; for an
    underdetermined one, the parameters no constraint determines. The model is
    told what stands (ids and constraints), so it revises by restating the
    same ids - a restated id revises, a new id creates - and changes only the
    choices or relations that the report names. Nothing here decides which.
    """
    from .base import REPAIR_KEY
    repair = (inputs or {}).get(REPAIR_KEY)
    if not isinstance(repair, dict) or not repair.get("findings"):
        return "  none - this is the first embodiment of this selection."
    from .base import CAUSE_PREREQUISITES

    rows = [r for r in repair.get("findings") or [] if isinstance(r, dict)]
    if repair.get("cause") == CAUSE_PREREQUISITES:
        # STRUCTURAL, AND THE SOLVER NEVER RAN. Nothing here is a number to
        # adjust: the design commits to something this embodiment does not
        # contain, and until it does there is nothing to settle.
        lines = ["  Your previous embodiment STANDS (round %s) and CANNOT BE BUILT. It is missing "
                 "geometry the design commits to, so no settlement was attempted:"
                 % repair.get("round")]
        for row in rows:
            lines.append("  - %s: %s%s" % (row.get("code"), row.get("detail"),
                                           " [%s]" % ", ".join(row.get("subjects") or ())
                                           if row.get("subjects") else ""))
        lines.append("  Supply the MISSING GEOMETRY - a feature that realizes the named side of "
                     "that interface, a feature placed at that joint, material for that body, a "
                     "Constraint that governs that clearance. Keep everything that already "
                     "stands. Changing a dimension answers none of these.")
        lines += _standing_block(repair)
        lines.append(_SNAPSHOT_RULE)
        return "\n".join(lines)
    lines = ["  Your previous embodiment STANDS (round %s). The solver settled it and found:"
             % repair.get("round")]
    for row in rows:
        code = row.get("code")
        if code == SETTLEMENT_INFEASIBLE:
            lines.append("  - INFEASIBLE: constraint %s (%s) cannot hold with the others: %s"
                         % (row.get("constraint"), row.get("expression"), row.get("detail")))
        elif code == SETTLEMENT_UNDERDETERMINED:
            lines.append("  - UNDERDETERMINED: parameter %s (%s) is determined by no constraint"
                         % (row.get("parameter"), row.get("symbol")))
        elif code == SETTLEMENT_UNSUPPORTED:
            lines.append("  - UNSUPPORTED: constraint %s (%s) cannot be solved: %s. Rewrite it as "
                         "a LINEAR relation over the parameters - a basis number is a constant "
                         "with unit \"1\", never a parameter, and two parameters are never "
                         "multiplied or divided by each other"
                         % (row.get("constraint"), row.get("expression"), row.get("detail")))
        else:
            lines.append("  - %s: %s" % (code, row.get("detail")))
    settled = repair.get("settled") or {}
    if settled:
        lines.append("  Values the constraints settled before the conflict: %s"
                     % ", ".join("%s=%s" % (k, v) for k, v in sorted(settled.items())))
    lines += _standing_block(repair)
    lines.append("  Revise the choices or relations the report names - a different design "
                 "choice, a relation you had wrong, a parameter you must close - keep the "
                 "rest, and never answer a conflict by dropping a required constraint.")
    lines.append(_SNAPSHOT_RULE)
    return "\n".join(lines)


#: THE ONE REVISION RULE, in the words the boundary enforces it in.
_SNAPSHOT_RULE = (
    "  HOW TO REVISE. Restate an id to change it - the fields that differ are revised, and a "
    "new id creates. WHAT YOU DO NOT MENTION KEEPS STANDING UNCHANGED, so you may answer with "
    "only the part you are changing. To RETRACT something - a relation that cannot hold, a "
    "parameter that existed only to state it - say so explicitly:\n"
    "    \"withdrawals\": [{\"entity\": \"<id>\", \"cause\": \"<one of the finding codes "
    "above>\", \"reason\": \"<why this must go>\"}]\n"
    "  A withdrawal is refused unless the report above named that entity (or something it "
    "rests on), so it is the answer to a finding and never a general clean-up. The same id is "
    "never both restated and withdrawn.")


def _standing_block(repair: Dict[str, Any]) -> List[str]:
    """What stands, by family and id - every family this stage authors, because
    the answer is a snapshot of all of them and omission withdraws."""
    current = repair.get("current") or {}
    if not current:
        return []
    out = ["  What stands, by id (restate an id to revise it; what you do not mention is left exactly as it is):"]
    for family in sorted(current):
        rows = current.get(family) or []
        if rows:
            out.append("    %s: %s" % (family, "; ".join(rows)))
    return out


def render_hard_requirements(view: Dict[str, Any]) -> str:
    constraints = {r.get("entity_id"): r for r in _rows(view, "DesignConstraint")}
    lines = ["HONOUR - every hard requirement the design states:"]
    if not constraints:
        lines.append("  (none stated)")
    for cid, rec in sorted(constraints.items()):
        lines.append("  - %s [%s]: %s%s"
                     % (cid, rec.get("kind"), rec.get("statement"),
                        " parameters=%s" % _render(rec.get("parameters"))
                        .replace("\n", " ") if rec.get("parameters") else ""))
    lines.append("OWED - compliance records this embodiment stage owes evidence for; "
                 "each stays NOT_YET_EVALUABLE here and none may be asserted satisfied:")
    owed = owed_hard_requirements(view)
    if not owed:
        lines.append("  (none)")
    for rec in owed:
        cid = rec.get("constraint")
        lines.append("  - %s owes %s [%s]: %s"
                     % (rec.get("entity_id"), cid,
                        (constraints.get(cid) or {}).get("kind"),
                        (constraints.get(cid) or {}).get("statement")))
    return "\n".join(lines)


#: Required of every Joint by DESIGN_STATE_CONTRACT. A record missing one of
#: these is not a joint the contract recognises, whatever its label says.
JOINT_REQUIRED = ("joint_type", "parent_group", "child_group", "dof",
                  "axis_direction", "frame_ids")


def internal_compliant_joints(view) -> Dict[str, List[Dict[str, Any]]]:
    """Well-formed COMPLIANT joints, keyed by the ONE body they are internal to.

    Keyed by body, not by body pair, and that is the correction. Compliance is
    declared by DESIGN_STATE_CONTRACT as "a joint_type of Joint between
    RigidGroups of one body (proposal D-2)" - an internal relation, where part
    of a body flexes relative to the rest of it. Keying by pair presupposed
    cross-body compliance, which the ontology does not model.

    Well-formed is doing real work: the Joint contract says "a joint_type label
    alone is inert", so a record calling itself COMPLIANT while omitting an axis
    or a frame is an incomplete joint wearing a label. The write boundary now
    also enforces the compliant variant fields, so a record reaching here has
    them - this stays as the reading-side half of the same rule.
    """
    groups = _body_of_group(view)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for joint in _rows(view, "Joint"):
        if str(joint.get("joint_type", "")).upper() != "COMPLIANT":
            continue
        if any(not joint.get(field) for field in JOINT_REQUIRED):
            continue
        parent = groups.get(joint.get("parent_group"))
        child = groups.get(joint.get("child_group"))
        if parent and child and parent == child:
            out.setdefault(parent, []).append(joint)
    return out


def check_c1_interface_features(parsed, view) -> List[str]:
    """S05-C1: every Interface has a Feature on EACH participant. No exception.

    THE CHECK ITSELF IS `embodiment.interface_realization_findings` and lives
    with the other mandatory prerequisites, because s06's entry gate asks the
    identical question of what stands. It was here alone once, and a branch
    whose interface had no realizing feature was settled anyway: s05 declared
    the incompleteness, the patch was applied as contract failures are, and the
    downstream gate - which knew nothing of C1 - found the branch ready and
    settled numbers for geometry that did not exist. One implementation, asked
    at both surfaces, is what makes that impossible rather than unlikely.
    """
    return ["S05-C1: " + f.detail for f in embodiment.interface_realization_findings(
        embodiment.rows_from_response(parsed, view))]


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


def applicable_obligations_for_embodiment(view: Dict[str, Any]) -> Set[str]:
    """The obligations the SELECTED candidate must discharge.

    DELEGATES to `applicable_obligation_ids`, which is the one place the rule
    lives. The ConsumerView applies the same function to standing state to
    decide what s05 is SHOWN; this applies it to the recorded payload to decide
    what s05 is JUDGED on. Two implementations would let the stage be asked to
    realize one set and marked against another, which is the contradiction this
    replaced - the prompt said "for every obligation below" while the view
    carried the whole design's obligations and the validator wanted a subset.
    """
    return applicable_obligation_ids(_rows(view, "Obligation"),
                                     _rows(view, "AcceptanceContract"))


def check_c4_obligations_realized(parsed, view) -> List[str]:
    """S05-C4: every APPLICABLE Obligation is cited by a Realization with a predicate.

    INV-008. A realization that cites an obligation without a verification
    predicate discharges nothing, so an unpredicated citation does not count.

    Applicable, not every obligation in the view: see
    `applicable_obligations_for_embodiment`. Checking the design-wide set made
    the selected candidate answerable for obligations that exist only because a
    rejected alternative worked differently.
    """
    duties = embodiment_duties(view)
    applicable = duties[DISCHARGE] | duties[PRESERVE]
    visible = _ids(view, "Obligation")
    dated = {r.get("entity_id"): r.get("satisfiable_at") for r in _rows(view, "Obligation")}

    cited: Set[str] = set()
    out = []
    for r in parsed.get("realizations") or []:
        if not str(r.get("verification_predicate") or "").strip():
            out.append("S05-C4: realization %s carries no verification predicate; "
                       "it discharges nothing (INV-008)" % r.get("id"))
            continue
        claimed = list(r.get("addresses_obligations") or [])
        cited.update(claimed)
        # THE REVERSE ERROR. Coverage alone accepts a realization that discharges
        # everything required AND something else - and that something else is a
        # claim about a mechanism nobody selected, written into state as though
        # the chosen design had satisfied it.
        for oid in sorted(set(claimed) - applicable):
            out.append(
                "S05-C4: realization %s claims to discharge %s, which does not "
                "apply to the selected candidate%s"
                % (r.get("id"), oid,
                   "" if oid in visible else " and is not in this view at all"))
        # A VISIBLE OBLIGATION IS NOT A DUTY TO DISCHARGE (Unit E). One the
        # selected branch's upstream records already discharged is preserved by
        # realizing those records; citing it as this geometry's discharge is a
        # claim over work another stage established.
        for oid in sorted(set(claimed) & duties[PRESERVE]):
            out.append(
                "S05-C4: realization %s cites %s as discharged, but the selected "
                "branch's upstream records already discharged it (satisfiable at "
                "%s); embodiment preserves it and may not claim it"
                % (r.get("id"), oid, dated.get(oid)))
    for oid in sorted(duties[DISCHARGE]):
        if oid not in cited:
            out.append("S05-C4: obligation %s applies to the selected candidate, "
                       "is embodiment's to discharge (satisfiable at %s), and is "
                       "cited by no realization" % (oid, dated.get(oid)))
    return out


def _as_record(item: Dict[str, Any]) -> Dict[str, Any]:
    rec = dict(item)
    rec["entity_id"] = rec.get("entity_id") or rec.get("id")
    return rec


def _as_record(item: Dict[str, Any]) -> Dict[str, Any]:
    rec = dict(item)
    rec["entity_id"] = rec.get("entity_id") or rec.get("id")
    return rec


def _expr_refs(expr: Any) -> Set[str]:
    if not isinstance(expr, dict):
        return set()
    if expr.get("ref"):
        return {expr["ref"]}
    return {r for a in (expr.get("args") or []) for r in _expr_refs(a)}


def check_c5_program_totality(parsed, view=None) -> List[str]:
    """S05-C5: every feature reads as the IR reads it - placement against a
    committed datum, construction with one terminal, every symbol declared.

    THE IR'S OWN VALIDATOR, not a second walk over the grammar. The boundary
    refuses what this reports; this reports it under the check's name before
    the write, beside every other finding.
    """
    from ..downstream import embodiment
    view = view or {}
    declared = {p.get("id") for p in parsed.get("parameters") or [] if isinstance(p, dict)}
    rows = embodiment.rows_from_response(parsed, view)
    datums, feature_bodies, datum_bodies, joint_axes = {}, {}, {}, {}
    for fam in ("Joint", "Envelope", "FunctionalRegion"):
        for rec in _rows(view, fam):
            datums[rec.get("entity_id")] = fam
            if fam == "Joint":
                joint_axes[rec.get("entity_id")] = rec.get("axis_direction")
            if fam == "Envelope" and rec.get("body"):
                datum_bodies[rec["entity_id"]] = {rec["body"]}
            elif fam == "FunctionalRegion":
                datum_bodies[rec["entity_id"]] = {b for b in (rec.get("owning_bodies") or [])
                                                  if isinstance(b, str)}
    for rec in rows["Feature"]:
        datums[rec["entity_id"]] = "Feature"
        feature_bodies[rec["entity_id"]] = rec.get("body")
    known = ir.Known(parameters=declared, datums=datums, feature_bodies=feature_bodies,
                     datum_bodies=datum_bodies, joint_axes=joint_axes)
    out = []
    for rec in rows["Feature"]:
        for problem in ir.feature_record_problems(rec, known):
            out.append("S05-C5: " + problem[len("IR: "):] if problem.startswith("IR: ") else problem)
    return out


def check_c11_joints_realized(parsed, view) -> List[str]:
    """S05-C11: every axis-bearing joint is realized by ONE placed feature on
    each body it relates, along the joint's declared axis (Unit G)."""
    from ..downstream import embodiment
    return ["S05-C11: " + f.detail for f in embodiment.joint_realization_findings(
        embodiment.rows_from_response(parsed, view))]


def check_c12_bodies_built(parsed, view) -> List[str]:
    """S05-C12: every body of the branch has material - at least one ADDITIVE
    feature - and every feature is on a body of the branch (Unit G)."""
    from ..downstream import embodiment
    return ["S05-C12: " + f.detail for f in embodiment.body_material_findings(
        embodiment.rows_from_response(parsed, view))]


def check_c14_mating_kinds(parsed, view) -> List[str]:
    """S05-C14: a stated mating side is realized by a feature of the stated
    kind on the stated body (Unit G)."""
    from ..downstream import embodiment
    return ["S05-C14: " + f.detail for f in embodiment.mating_kind_findings(
        embodiment.rows_from_response(parsed, view))]


def _parameter_problems(parsed, created: bool) -> List[str]:
    """The IR's parameter validator over the response's declarations (Unit G:
    one implementation for C6, C10 and the boundary)."""
    out = []
    for p in parsed.get("parameters") or []:
        if not isinstance(p, dict):
            continue
        rec = _as_record(p)
        rec.setdefault("status", ir.DECLARED)
        out += ir.parameter_record_problems(rec, created=created)
    return out


def check_c6_units(parsed) -> List[str]:
    """S05-C6: no Parameter has a null unit (INV-004 / R-21), and every
    constraint relates quantities of ONE dimension - the solver's own
    dimensional reduction, asked before the write (Unit G)."""
    from ..downstream import solver
    out = ["S05-C6: " + p[len("IR: "):] for p in _parameter_problems(parsed, created=False)
           if "declares no unit" in p]
    units = {p.get("id"): p.get("unit") for p in parsed.get("parameters") or []
             if isinstance(p, dict) and isinstance(p.get("unit"), str) and p.get("unit")}
    for c in parsed.get("constraints") or []:
        expr = c.get("expression") if isinstance(c, dict) else None
        if not isinstance(expr, dict):
            continue
        refs = _expr_refs(expr.get("lhs")) | _expr_refs(expr.get("rhs"))
        if all(r in units for r in refs):
            out += ["S05-C6: constraint %s %s" % (c.get("id"), p)
                    for p in solver.dimension_problems(expr, units)]
    return out


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


#: s03's clearance vocabulary, re-exported from where the check lives.
CLEARANCE_KINDS = embodiment.CLEARANCE_KINDS


def check_c9_clearance_constraints(parsed, view) -> List[str]:
    """S05-C9: every declared clearance pair has a Constraint that names it.

    THE CHECK ITSELF is `embodiment.clearance_governance_findings`, shared with
    s06's entry gate for the same reason S05-C1 is: a clearance nobody owns is a
    number the settlement loop is never asked to hold, and settling a branch
    without it produces dimensions that satisfy every constraint that exists and
    interfere anyway.
    """
    return ["S05-C9: " + f.detail for f in embodiment.clearance_governance_findings(
        embodiment.rows_from_response(parsed, view))]


def check_c10_no_unsolved_values(parsed) -> List[str]:
    """S05-C10: no Parameter value is set without a cited solver artifact.

    R-23, and the reason the s05/s06 loop is safe without a sequential barrier.
    s05 authors declarations; a number here would be a guess wearing a solved
    answer's clothes.
    """
    return ["S05-C10: " + p[len("IR: "):] for p in _parameter_problems(parsed, created=True)
            if "solver artifact" in p]
