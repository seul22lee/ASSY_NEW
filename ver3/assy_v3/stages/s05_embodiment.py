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
lets the settlement loop do the arithmetic.

THE AUTHORING BOUNDARY: SEMANTIC IN, EXECUTABLE OUT

The provider authors MECHANICAL MEANING and nothing else - feature kind, body,
placement datum, orientation, symbolic dimensions, a recursive solid tree,
which features embody which declared relation, which features realize which
side of which interface, and constraints as typed relations. Production owns
every piece of compiler bookkeeping: canonical ids, construction step ids,
step ordering, the dependency order, the single terminal result, the
KinematicRealization rows, the canonical expression AST and the derived
`Constraint.parameters` list.

The recurring live failures this replaced were all bookkeeping: a dangling
feature id for a record that did not exist yet, a step consuming a later step,
two unconsumed terminals, a unary CUT meaning "remove me from the body", a
malformed expression node, a `parameters` list disagreeing with its own
expression, and a KinematicRealization the model chose not to write. None of
them was a mechanical decision, and none of them is expressible now. See
`downstream.semantic` for what may be said and `downstream.lowering` for what
production derives from it.

WHAT MUST BE EMBODIED IS ENUMERATED, ONCE

`downstream.duty_manifest` derives every duty from the standing s03/s04 branch
BEFORE the call: the bodies that need material, every joint and every blocking
relation that must be embodied and the sides each relates, every interface and
its participant sides, s04's stated mating geometry, the clearances that owe a
governing constraint, the datums that lend no orientation, and the scale
authority. The same manifest renders the prompt, validates the response,
decides structural completeness and answers the settlement gate. A duty the
prompt never raises cannot be a check, and a check the prompt never raises
cannot be a trap.

THE MODEL PROPOSES; THE CONTRACT DECIDES

`llm_role` is "High for feature proposal and program shape. NONE for
completeness, which is enumeration over s03's relation set." Completeness,
reference validity, cycle freedom, occupancy and solver evidence are all
computed here from committed state. Nothing the model says about its own
completeness is read.

WHOLE OR NOT AT ALL

The boundary runs in one sequence - parse, resolve local keys, validate
upstream references, exact duty coverage, body material, interface sides and
mating kinds and governing constraints, placement and orientation, solid-tree
validity, typed constraint validity, deterministic lowering, executable-IR
validation - and only then are operations built. A response that fails any of
it is refused whole. No partial embodiment is written for a later round to
repair.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ..downstream import duty_manifest, embodiment, ir, lowering, semantic
from ..state.patch import Op
from ..view import DISCHARGE, PRESERVE, applicable_obligation_ids, obligation_duties
from .base import Stage, StageError

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
#: envelope" rule; CLEARANCE and INTERFERENCE_FREE are the two that GOVERN an
#: interface - `lowering.GOVERNING_KINDS` is the same fact where it is enforced.
CONSTRAINT_KINDS = ("ENVELOPE", "CLEARANCE", "DIMENSIONAL", "INTERFERENCE_FREE")

PROMPT = """You are proposing the PHYSICAL GEOMETRY that makes an already-decided
mechanism real.

The bodies, groups, joints and interactions below are DECIDED. You may not add,
remove or reinterpret them. Your job is to say what geometry on which body
realizes each declared relation, and what that geometry demands of the layout.

YOU AUTHOR MECHANICAL MEANING. YOU DO NOT AUTHOR BOOKKEEPING.
You name new features, parameters and constraints by a short LOCAL KEY of your
own choosing - "base_stock", "hinge_bore", "r_pin". Production allocates every
canonical id. You never write an id for something you are creating, you never
write construction steps or their order, and you never write a realization
record: you say WHICH FEATURES embody each relation and production writes it.

RULES
1. FEATURES. For every body below, and for every relation and interface listed
   under DUTIES, propose the features that make it real. A feature names its
   `key`, the `body` it is on, its `feature_kind`, a short `geometry`
   description, its `placement`, and its `solid`.
   MATERIAL. Every body needs material - at least one ADDITIVE feature. AN
   ENVELOPE IS NOT MATERIAL: it is the bounding extent s04 committed, the space
   the body may not exceed, and NOT a solid to be filled. A housing, frame,
   bracket, shell, drawer or carriage occupies only part of its envelope. Build
   the body you would actually manufacture, from as many additive features as
   its shape needs and subtractive features for what is removed. A single block
   the size of the envelope is almost never the part.
   POLARITY IS THE KIND, NOT A STEP. A body is its ADDITIVE features fused with
   its SUBTRACTIVE features removed. A BORE is the cylinder that WILL BE
   REMOVED, and you build it as a positive cylinder; its kind removes it at body
   composition. Never try to subtract a feature from its body - the body is not
   something your geometry can name.
2. PLACEMENT. Every feature carries a `placement` RELATIVE TO SOMETHING THE
   DESIGN HAS ALREADY COMMITTED: a `datum` that is a Joint id (the feature sits
   on that joint's located frame), the body's own Envelope id (the body's
   centre), a FunctionalRegion id, or the KEY of an earlier feature of the SAME
   body; an optional `offset` of three expressions in {length_unit} along the
   arrangement axes; and the feature's own `axis` where it has one. A DATUM
   LOCATES; AN AXIS ORIENTS. At a joint the axis defaults to the joint's, which
   is what a bore, a pin or a bearing wants, and you may state a different one,
   meaning "located here, oriented otherwise". Against an envelope or a region
   the default is the arrangement's +Z; against a feature it is that feature's.
   A DATUM THAT DECLARES NO AXIS LENDS NONE - see DUTIES - so a feature placed
   against one MUST state its own. Never state a position of your own; poses are
   derived downstream from the joint frames and the joint coordinates.
3. SOLID. Every feature carries a `solid`: the MATERIAL THE FEATURE IS, built
   in the feature's own frame (origin at the placement, Z along its axis). It
   is described by SHAPE, never by a compiler operation - see GRAMMAR. Where a
   compound feature genuinely needs it, RELIEVED takes a `base` and one or more
   `relief` shapes taken out of THAT BASE - a bore with a counterbore, a boss
   with a flat. There is no way to say "remove this feature from its body",
   because that is not geometry you write: it is the feature's KIND, and the
   body is composed from its features afterwards. The tree has no ids, no
   ordering and no result to declare: children are built before their parent,
   the root IS the feature's solid, and production derives the whole program.
4. PARAMETERS ARE DECLARED WHERE THEY ARE USED. There is no parameter list.
   Every dimension is an expression, and a symbolic one names its parameter AND
   its unit right there: {{"kind": "param", "param": "r_pin", "unit": "mm"}}.
   Use the same name again wherever the same dimension appears, with the same
   unit; production collects the declarations and makes one Parameter from
   them. NEVER give a parameter a value: dimensions are solved later from the
   constraints you write, and a number here would be a guess wearing a solved
   answer's clothes. Every number is a unit-bearing constant, never bare.
5. CONSTRAINTS. Write the typed relations that relate those parameters, each
   with a `kind`, a `basis`, a `relation` and the two sides `lhs` and `rhs`. A
   constraint carries no key: nothing refers to one.
     - ENVELOPE: a feature that implies a minimum envelope must say so. A pin of
       radius r needing a wall w gives a boss radius r + w.
     - CLEARANCE / INTERFERENCE_FREE: the constraint you write inside an
       interface's assignment must be one of THESE kinds. A constraint of any
       other kind names an interface without governing it.
   A constant is either a bound the design actually states (`basis`
   STATED_BOUND - a hard requirement, a rule you can name) or a design choice
   you make and mark as one (`basis` DESIGN_CHOICE); every other size is a
   parameter related to others (`basis` GEOMETRIC_RELATION).
   CLOSE THE SYSTEM. Every parameter you use must be named by at least one
   constraint - by a GEOMETRIC_RELATION to other parameters, a STATED_BOUND, or
   a DESIGN_CHOICE (`==` a number, marked as a choice). Choices are yours to
   make - a wall thickness, a pin diameter, a clearance - and they must be
   visible as choices, never presented as facts.
6. REALIZATION ASSIGNMENTS. `realization_assignments` maps EVERY relation listed
   under DUTIES to ITS SIDES: for each body the relation relates, the feature
   keys ON THAT BODY that embody it. The relation keys must be EXACTLY the
   relations listed, and the body keys under each must be EXACTLY the sides
   DUTIES names for it - a side is a key you must fill in, not a list you can
   make shorter. List EVERY feature that does the job, on EVERY side: two rails and two carriages embody
   one guided relation together, three pads bearing on three recess walls embody
   guidance with no guide part at all, and a rod in a plain bore may leave a
   rotation free on purpose. What embodies a relation is what you say embodies
   it - never a name, never an axis that happens to match, never one feature per
   relation.
7. INTERFACE ASSIGNMENTS. `interface_assignments` maps EVERY interface listed
   under DUTIES to its `sides`: for each participating body, the feature keys on
   that body that realize that side. Two bodies that touch need two features, one
   on each. A feature realizes ONE interface: if the same physical region serves
   two interfaces, declare a feature for each. Where DUTIES says an interface
   owes a governing constraint, also name it as `governing_constraint`.
8. SPACE THAT MUST STAY FREE. DUTIES lists the regions whose role means the
   design promises that volume is open - something reaches into it or passes
   through it. For EVERY one, `region_assignments` names, per owning body, the
   feature(s) that clear it. Such a feature must be of a kind that REMOVES
   material and must be placed ON THAT REGION: geometry clears a region by
   being at it, and a claim in words clears nothing. Whether it actually clears
   it is judged later against the built solid.
9. A LIMIT IS GEOMETRY AT A POSITION. Where DUTIES shows a joint standing at
   different coordinates in different configurations, the material producing a
   limit at one coordinate cannot be the same material in the same place as the
   material producing a limit at another - one solid cannot stop a joint at two
   positions. Place them where they actually are.
10. MOTION AND PATHS. DUTIES lists the motions the design requires and the
   paths s04 already proved clear. Do not put material into one. Where a
   restraint is released for a required motion, your geometry must not still
   produce it.
11. OBLIGATIONS. For every obligation under DISCHARGE emit a `realizations` entry
   citing the obligation ids it discharges, the feature keys that do the
   discharging, and a verification predicate - a sentence a later check could
   test. A realization with no predicate discharges nothing. Every obligation
   under PRESERVE was already discharged by the selected mechanism's own upstream
   records; do NOT cite one as discharged.
12. Where a degree of freedom below is dispositioned BLOCKED_BY a constraint
   relation, the geometry must PRODUCE that limit: features that actually stop
   the motion, on each side of the relation. A clearance pocket on both sides
   assigns two features and stops nothing.
13. Do not remove what the design has already established. Where states,
   motions, swept volumes or load routes appear below, they were proven against
   the arrangement you are embodying: a feature placed into a path already shown
   clear turns a moving design into one that binds, and material cut from a
   member on a load route removes what carries the load. If your geometry cannot
   respect one of them, say so in `unresolved` rather than quietly overriding it.
   The envelopes, regions, scale and mating sizes below are the PROVISIONAL
   arrangement s04 committed, in s04's own basis: respect where things sit
   relative to each other, and never copy a provisional extent, representative
   size or region into a constant and present it as a dimension.
14. HARD REQUIREMENTS. Every requirement listed under HONOUR applies to this
   design and your geometry must be compatible with it. Every compliance record
   listed under OWED is a hard requirement THIS embodiment stage owes evidence
   for and cannot yet establish: it stays NOT_YET_EVALUABLE until that evidence
   exists. Do not assert or imply that any of them is satisfied, and do not cite
   one as an obligation. Where your geometry turns on something such a
   requirement bears on, declare the parameter it turns on and record what is
   still open in `unresolved`.

DUTIES OF THIS EMBODIMENT - derived from the committed design, and complete
--------------------------------------------------------------------------
{duties}

OBLIGATION DUTIES
-----------------
{obligation_duties}

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
Return a single JSON object with exactly these keys. A list may be empty - an
empty list is a value. The only keys are FEATURE keys - short
local names you choose, unique, and NOT of the canonical PREFIX-0001 form. A
parameter name is declared wherever it is used and needs no list; a constraint
has no name at all.
Canonical ids appear only where you name something the design has ALREADY
committed - a body, a joint, a constraint relation, an interface, an envelope,
a region, an obligation.

{response_schema}

PERMITTED VALUES
  feature_kind   {feature_kinds}
    ADDITIVE     {additive_kinds}
    SUBTRACTIVE  {subtractive_kinds}
  constraint kind {constraint_kinds}
  constraint basis {basis_values}
  relation       {relations}
  solid shape    {solid_shapes}
  datum kind     {datum_kinds}
  placement axis {signed_axes}
  turn axis      {rotate_axes}
  literal unit   {literal_units}
"""


CONSTRAINT_BASES = ("STATED_BOUND", "DESIGN_CHOICE", "GEOMETRIC_RELATION")


def _render(obj: Any) -> str:
    import json
    return json.dumps(obj, indent=1, sort_keys=True, default=str)


class S05Embodiment(Stage):
    #: WRITE OWNER. s05 is one of the few where the numbered stage and the
    #: producing responsibility coincide - there is one pass, not two.
    stage_id = "s05"
    purpose = "realize declared relations as named geometry and constrain the layout"

    #: THE FAMILIES THIS STAGE WRITES, and the prefix production allocates for
    #: each. The response names none of these ids: the prefixes live here so a
    #: reader can see what this stage brings into existence, and in
    #: `lowering.ID_PREFIXES` because that is where they are allocated.
    RESPONSE_ENVELOPE = (
        ("features", "Feature", lowering.ID_PREFIXES["Feature"]),
        ("realizations", "Realization", lowering.ID_PREFIXES["Realization"]),
        ("realization_assignments", "KinematicRealization",
         lowering.ID_PREFIXES["KinematicRealization"]),
        ("parameters", "Parameter", lowering.ID_PREFIXES["Parameter"]),
        ("constraints", "Constraint", lowering.ID_PREFIXES["Constraint"]),
        ("unresolved", "UnresolvedDecision", lowering.ID_PREFIXES["UnresolvedDecision"]),
    )

    #: Kept so a reader of an older contract finds the same name. Nothing in the
    #: schema shows a canonical id any more, so there is no example to collide.
    ID_EXAMPLE_DIGITS = "NNNN"

    #: This stage's provenance, and the mark of a record it authored.
    PROVENANCE = "s05:embodiment"

    # ------------------------------------------------------------------
    # THE SELECTION THIS INVOCATION EMBODIES
    # ------------------------------------------------------------------
    def selected_candidate(self, view: Dict[str, Any]) -> Optional[str]:
        """The committed candidate, read from the view s05 was actually given."""
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
        no longer pursuing.
        """
        view = (inputs or {}).get(self.context_key) or {}
        return [e for e in (self.selected_candidate(view),
                            self.selection_decision(view)) if e]

    # ------------------------------------------------------------------
    # THE DUTY MANIFEST - one derivation, four uses
    # ------------------------------------------------------------------
    def duty_manifest(self, inputs: Dict[str, Any]) -> duty_manifest.EmbodimentDutyManifest:
        """What this branch owes its embodiment, from the view it was given.

        THE VIEW AND THE STATE ARE THE SAME ROWS. `manifest_from_rows` is handed
        the s03/s04 families of the committed branch; the settlement gate hands
        it the same families out of standing state. Neither is a second rule.
        """
        view = (inputs or {}).get(self.context_key) or {}
        rows = {fam: _rows(view, fam) for fam in
                ("Body", "RigidGroup", "Joint", "Interface", "ConstraintRelation")
                + embodiment.SPATIAL_FAMILIES}
        duties = embodiment_duties(view)
        return duty_manifest.from_rows(rows, branch=self.selected_candidate(view),
                                       obligations_to_discharge=duties[DISCHARGE])

    def upstream_facts(self, inputs: Dict[str, Any]) -> lowering.UpstreamFacts:
        view = (inputs or {}).get(self.context_key) or {}
        rows = {fam: _rows(view, fam) for fam in
                ("Body", "RigidGroup", "Joint", "Interface", "ConstraintRelation",
                 "Envelope", "FunctionalRegion", "ReferenceScale")}
        duties = embodiment_duties(view)
        return lowering.facts_from_rows(
            rows, discharge=duties[DISCHARGE], preserve=duties[PRESERVE],
            visible_obligations=_ids(view, "Obligation"))

    # ------------------------------------------------------------ prompt
    @classmethod
    def render_response_schema(cls) -> str:
        """The semantic shape, written where the shape is enforced.

        It is no longer derived from the canonical family declarations, because
        the response is no longer canonical records: it is mechanical meaning,
        and production makes the records. `downstream.semantic` is the one
        authority for what may be said, and this renders exactly that.
        """
        return """{
  "features": [
    {"key": "<local key>", "body": "<Body id>", "feature_kind": "<kind>",
     "geometry": "<short description of what this geometry is>",
     "placement": {"datum": {"kind": "JOINT | ENVELOPE | FUNCTIONAL_REGION |
                                      FEATURE",
                             "ref": "<committed id, or a feature key>"},
                   "axis": "<signed axis>",      // omit to inherit the datum's
                   "offset": [<len>, <len>, <len>]},      // optional
     "solid": <solid>}
  ],
  "constraints": [
    {"kind": "<constraint kind>", "basis": "<basis>",
     "relation": "<relation>", "lhs": <expr>, "rhs": <expr>}
  ],
  "realization_assignments": {
    "<Joint or ConstraintRelation id>": {
      "<Body id, one key per side DUTIES names>": ["<feature key>", ...]
    }
  },
  "interface_assignments": {
    "<Interface id>": {"sides": {"<Body id>": ["<feature key>", ...]},
                       "governing_constraint": {"kind": "CLEARANCE",
                                                "basis": "<basis>",
                                                "relation": "<relation>",
                                                "lhs": <expr>, "rhs": <expr>}}
  },
  "region_assignments": {
    "<FunctionalRegion id owing free space>": {
      "<owning Body id>": ["<feature key that removes material AT that region>"]
    }
  },
  "realizations": [
    {"addresses_obligations": ["<Obligation id>", ...],
     "participating_features": ["<feature key>", ...],
     "verification_predicate": "<a sentence a later check could test>"}
  ],
  "unresolved": [
    {"decision": "...", "why_open": "...", "alternatives": [...],
     "alternatives_kind": "...", "kept_open_by": [...], "blocks": [...]}
  ]
}"""

    @staticmethod
    def render_grammar() -> str:
        """The embodiment language, RENDERED FROM THE LAYER THAT ENFORCES IT.

        Expression forms, the solid tree, the units, the typed zero, the signed
        axes and the placement frame convention - each read from
        `downstream.semantic` and `downstream.ir`, so the language the model is
        shown is the language the boundary enforces and the kernel executes.
        Nothing here is a second copy.
        """
        zero = '{"kind": "number", "value": 0, "unit": "%s"}' % ir.KERNEL_LENGTH_UNIT
        lines = [
            "<expr> is a TYPED EXPRESSION - exactly one of",
            '  {"kind": "param", "param": "<name>", "unit": "<unit>", "symbol": "<symbol>"}'
            "   - names AND declares the dimension; `symbol` is optional and",
            "     defaults to the name; add \"role\": \"SCALE\" only where DUTIES asks",
            "     for a scale. Use the same name and unit everywhere it recurs.",
            '  {"kind": "number", "value": <number>, "unit": %s}'
            % " | ".join('"%s"' % u for u in semantic.LITERAL_UNITS),
            '  {"kind": "sum", "terms": [<expr>, <expr>, ...]}          - two or more',
            '  {"kind": "difference", "left": <expr>, "right": <expr>}',
            '  {"kind": "negate", "of": <expr>}',
            '  {"kind": "scale_by", "of": <expr>, "factor": <number>}   - times a plain number',
            '  {"kind": "divide_by", "of": <expr>, "divisor": <number>} - over a plain number',
            "There is no product or quotient of two parameters: the settlement is linear in "
            "the parameters, and a relation outside that is one the solver cannot read.",
            "Units: lengths in %s, angles in %s; a dimensionless factor has unit \"1\"."
            % (ir.KERNEL_LENGTH_UNIT, ir.KERNEL_ANGLE_UNIT),
            "A coordinate at a frame origin is the typed zero %s - a coordinate definition, "
            "not a dimension." % zero,
            "BASIS NUMBERS. The arrangement's own numbers - envelope extents and centres, "
            "joint origins, region volumes - are in the ReferenceScale basis and are "
            "DIMENSIONLESS. A length in %s that follows from one is the scale parameter "
            "scaled by that number: "
            '{"kind": "scale_by", "of": {"kind": "param", "param": "<scale name>", '
            '"unit": "mm", "role": "SCALE"}, "factor": 100}.' % ir.KERNEL_LENGTH_UNIT,
            "",
            "A LENGTH is <expr>, or a plain number read in %s. An ANGLE is <expr>, or a "
            "plain number read in %s. Only where the field itself fixes the dimension - "
            "never in a constraint." % (ir.KERNEL_LENGTH_UNIT, ir.KERNEL_ANGLE_UNIT),
            "",
            "<solid> is THE MATERIAL A FEATURE IS - exactly one of",
            '  {"shape": "BLOCK", "dx": <len>, "dy": <len>, "dz": <len>}',
            "        " + ir.OPCODE_SEMANTICS["BOX"],
            '  {"shape": "CYLINDER", "radius": <len>, "height": <len>}',
            "        " + ir.OPCODE_SEMANTICS["CYLINDER"],
            '  {"shape": "SPHERE", "radius": <len>}',
            "        " + ir.OPCODE_SEMANTICS["SPHERE"],
            '  {"shape": "AT", "of": <solid>, "offset": [<len>, <len>, <len>], '
            '"turn": {"axis": "X"|"Y"|"Z", "angle": <ang>}}',
            "        the same material, turned about the feature frame origin and then "
            "offset in it; state either or both",
            '  {"shape": "COMPOUND", "parts": [<solid>, <solid>, ...]}',
            "        two or more parts of THIS feature, fused into one",
            '  {"shape": "RELIEVED", "base": <solid>, "relief": [<solid>, ...]}',
            "        the base with the reliefs taken out of IT - a bore with a counterbore, "
            "a boss with a flat",
            '  {"shape": "COMMON", "parts": [<solid>, <solid>, ...]}',
            "        the material two or more parts share",
            "",
            "  RELIEVED is the only difference and it names its base, so there is no way to "
            "write \"take this feature out of the body\": the body is named nowhere in a "
            "feature's geometry, and whether the finished solid is added or removed is the "
            "feature's KIND.",
            "  The tree carries no ids, no order and no terminal. Children are built first "
            "and the root is the feature's solid; production derives the program from it.",
            "",
            "FRAMES. The arrangement frame the envelopes, regions and joint origins below are "
            "stated in is THE frame; every body frame coincides with it at zero joint "
            "coordinates. The feature frame has Z along the feature's axis, origin at datum + "
            "offset, and X along the canonical perpendicular (Z->X, X->Y, Y->Z, positive); the "
            "feature's solid is built in it.",
            "",
        ]
        # THE ONE STATEMENT of what a feature's construction is, from the IR
        # that enforces it and the compiler that executes it.
        lines.append("POLARITY, NOT A NODE OF YOUR TREE.")
        for sentence in ir.POLARITY_SEMANTICS.split(". "):
            sentence = sentence.strip()
            if sentence:
                lines.append("  " + sentence + ("" if sentence.endswith(".") else "."))
        lines += [
            "",
            "WHAT EMBODIES WHAT IS DECLARED, NOT INFERRED. Neither the datum nor the axis says "
            "that a feature EMBODIES anything: a keeper sitting on a hinge axis permits no "
            "rotation, and a face named STOP restrains nothing by being named. "
            "`realization_assignments` is where you say it, and it is the only place it is "
            "read. It carries no axis, no coordinate and no list of degrees of freedom - the "
            "joint or the relation already states those and stays the authority.",
        ]
        return "\n".join(lines)

    def prompt(self, inputs: Dict[str, Any]) -> str:
        proj = inputs["consumer_view"]
        manifest = self.duty_manifest(inputs)
        return PROMPT.format(
            projection=_render(proj),
            duties=manifest.render(),
            obligation_duties=render_duties(proj),
            hard_requirements=render_hard_requirements(proj),
            grammar=self.render_grammar(),
            settlement_feedback=render_settlement_feedback(inputs),
            solid_shapes=" | ".join(semantic.SOLID_SHAPES),
            datum_kinds=" | ".join(semantic.DATUM_KINDS),
            feature_kinds=" | ".join(FEATURE_KINDS),
            additive_kinds=" | ".join(FEATURE_KIND_POLARITY.get("ADDITIVE", ())),
            subtractive_kinds=" | ".join(FEATURE_KIND_POLARITY.get("SUBTRACTIVE", ())),
            constraint_kinds=" | ".join(CONSTRAINT_KINDS),
            basis_values=" | ".join(CONSTRAINT_BASES),
            relations=" | ".join(ir.RELATIONS),
            signed_axes=" | ".join(ir.SIGNED_AXES),
            rotate_axes=" | ".join(ir.AXES),
            length_unit=ir.KERNEL_LENGTH_UNIT,
            literal_units=" | ".join('"%s"' % u for u in semantic.LITERAL_UNITS),
            response_schema=self.render_response_schema())

    # ------------------------------------------------------------ boundary
    def lowered(self, parsed: Dict[str, Any], inputs: Dict[str, Any]):
        """THE WHOLE PRE-WRITE BOUNDARY, in one sequence.

        parse semantic -> resolve local keys -> validate upstream references ->
        exact duty coverage -> body material -> interface sides, mating kinds
        and governing constraints -> placement and orientation -> solid-tree
        validity -> typed constraint validity -> deterministic lowering ->
        executable-IR validation.

        It returns the canonical records or it raises. There is no third
        outcome, and in particular there is no partial one.
        """
        try:
            response = semantic.SemanticResponse.parse(parsed)
        except semantic.SemanticError as exc:
            raise StageError("s05 response is not a semantic embodiment: %s" % exc)
        manifest = self.duty_manifest(inputs)
        facts = self.upstream_facts(inputs)
        try:
            out = lowering.lower(response, manifest, facts,
                                 occupied=(inputs or {}).get(self.occupancy_key))
        except lowering.LoweringError as exc:
            raise StageError(
                "s05 response does not discharge this branch's embodiment duties (%d):\n  - %s"
                % (len(exc.problems), "\n  - ".join(exc.problems)))
        problems = self.executable_ir_problems(out, inputs)
        if problems:
            raise StageError(
                "s05 lowered program does not read as the executable IR (%d):\n  - %s"
                % (len(problems), "\n  - ".join(problems)))
        return response, manifest, out

    def executable_ir_problems(self, out: "lowering.LoweredEmbodiment",
                               inputs: Dict[str, Any]) -> List[str]:
        """The EXISTING executable-IR validator, over what was just lowered.

        The lowerer is deterministic and the tree makes a malformed program
        unsayable, so this should never fire. It runs anyway, because "should
        never" is not a property anything downstream can rely on, and because
        the IR - not the lowerer - is the authority on what the compiler reads.
        """
        view = (inputs or {}).get(self.context_key) or {}
        declared = {p["entity_id"] for p in out.parameters}
        datums, feature_bodies, datum_bodies, joint_axes = {}, {}, {}, {}
        for fam in ("Joint", "Envelope", "FunctionalRegion"):
            for rec in _rows(view, fam):
                datums[rec.get("entity_id")] = fam
                if fam == "Joint":
                    joint_axes[rec.get("entity_id")] = rec.get("axis_direction")
                elif fam == "Envelope" and rec.get("body"):
                    datum_bodies[rec["entity_id"]] = {rec["body"]}
                elif fam == "FunctionalRegion":
                    datum_bodies[rec["entity_id"]] = {b for b in (rec.get("owning_bodies") or [])
                                                      if isinstance(b, str)}
        for rec in out.features:
            datums[rec["entity_id"]] = "Feature"
            feature_bodies[rec["entity_id"]] = rec.get("body")
        units = {p["entity_id"]: p.get("unit") for p in out.parameters}
        known = ir.Known(parameters=declared, datums=datums, feature_bodies=feature_bodies,
                         datum_bodies=datum_bodies, joint_axes=joint_axes, units=units)
        problems: List[str] = []
        for rec in out.parameters:
            problems += ir.parameter_record_problems(rec, created=True)
        for rec in out.constraints:
            problems += ir.constraint_record_problems(rec, declared, units)
        for rec in out.features:
            problems += ir.feature_record_problems(rec, known)
        return problems

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        """Every output carries the premises it was derived FROM.

        This is what puts s05 into the currentness graph rather than beside it.
        `_propagate` walks `_premises`, so an entity that records none is an
        entity no upstream change can ever stale.

        The premises are not invented: a Feature rests on the body it is on, the
        datum it is placed against, the scale that datum's coordinates are in
        and every parameter it reads; a Constraint on its parameters and the
        interface it governs; a KinematicRealization on the relation it embodies
        and on nothing else.
        """
        inputs = inputs or {}
        _response, manifest, out = self.lowered(parsed, inputs)
        ops: List[Op] = []
        prov = self.PROVENANCE
        view = inputs.get(self.context_key) or {}
        # The basis every envelope coordinate is expressed in. Taken from the
        # view rather than rebuilt from an id convention, because the scale is a
        # committed entity and guessing its name in a second place is how two
        # spellings of one id start.
        scales = sorted(_ids(view, "ReferenceScale"))

        for rec in out.parameters:
            ops.append(Op("CREATE", "Parameter", rec["entity_id"],
                          {k: v for k, v in rec.items() if k != "entity_id"}, prov))
        for rec in out.features:
            fields = {k: v for k, v in rec.items() if k != "entity_id"}
            premises = [rec["body"]]
            # THE TYPED TRACE: which s03 interactions this feature realizes a
            # side of. Each is a premise, so a revised interface stales the
            # geometry that realized it. Never inferred from prose or the body.
            premises += list(rec.get("interfaces") or [])
            datum = (rec.get("placement") or {}).get("datum")
            if datum:
                premises.append(datum)
                premises += scales
            premises += sorted(_record_refs(rec))
            ops.append(Op("CREATE", "Feature", rec["entity_id"], fields, prov,
                          premise_refs=premises))
        for rec in out.constraints:
            fields = {k: v for k, v in rec.items() if k != "entity_id"}
            premises = list(fields.get("parameters") or [])
            if fields.get("governs_interface"):
                premises.append(fields["governs_interface"])
            ops.append(Op("CREATE", "Constraint", rec["entity_id"], fields, prov,
                          premise_refs=premises))
        for rec in out.kinematic_realizations:
            # WHAT EMBODIES WHAT. The TARGET is the premise: the claim exists
            # because that joint or that constraint relation does, and a revised
            # or withdrawn relation is a claim that must be re-examined.
            #
            # THE PARTICIPATING FEATURES ARE NAMED, NOT RESTED ON, and the live
            # pipeline is what settled that. They were premises first, and every
            # KinematicRealization in a run ended STALE: a premise change stales
            # its dependents, so revising any feature's DIMENSION staled the
            # claim that merely NAMED it, the joint read unrealized again, the
            # structural loop oscillated and s06 never once ran.
            ops.append(Op("CREATE", "KinematicRealization", rec["entity_id"],
                          {"realizes": rec["realizes"],
                           "participating_features": list(rec["participating_features"])},
                          prov, premise_refs=[rec["realizes"]]))
        for rec in out.realizations:
            fields = {k: v for k, v in rec.items() if k != "entity_id"}
            ops.append(Op("CREATE", "Realization", rec["entity_id"], fields, prov,
                          premise_refs=list(fields["addresses_obligations"])
                          + list(fields["participating_features"])))
        for rec in out.unresolved:
            ops.append(Op("CREATE", "UnresolvedDecision", rec["entity_id"],
                          {k: v for k, v in rec.items() if k != "entity_id"}, prov))
        return ops

    # ------------------------------------------------------------ repair
    def repair_operations(self, ops: List[Op], inputs: Dict[str, Any], state,
                          parsed: Optional[Dict[str, Any]] = None) -> List[Op]:
        """A settlement-feedback round RE-AUTHORS the embodiment, whole.

        THERE IS NOTHING TO RESTATE ANY MORE. The response names no canonical
        id, so a revision cannot be a restatement of one; and it must not be,
        because a partial re-authoring is exactly the committed fragment this
        boundary exists to prevent. A repair round therefore retires this
        stage's standing embodiment for this branch and writes the new one in
        the same patch - one atomic replacement, with this round's reason on
        every retirement.
        """
        from .base import REPAIR_KEY
        repair = (inputs or {}).get(REPAIR_KEY) or {}
        branch = (inputs or {}).get("candidate") or \
            self.selected_candidate((inputs or {}).get(self.context_key) or {})
        if not branch:
            raise StageError("this invocation names no candidate, so the embodiment it would "
                             "replace cannot be identified")
        codes = sorted({r.get("code") for r in (repair.get("findings") or [])
                        if isinstance(r, dict) and r.get("code")})
        reason = "s05 embodiment re-authored after settlement round %s: %s" % (
            repair.get("round"), ", ".join(codes) or "feedback")
        retired = [Op("INVALIDATE", family, eid, {}, self.PROVENANCE, reason=reason)
                   for family, ids in sorted(self.embodiment_snapshot(state, branch).items())
                   for eid in ids]
        return retired + ops

    @classmethod
    def embodiment_families(cls) -> Tuple[str, ...]:
        """THE EMBODIMENT, by family, derived from the contract rather than
        listed here: everything `owned_by: s05`, plus the universally ownable
        families this stage also authors into."""
        from ..state.design_state import Contracts
        contracts = Contracts()
        families = contracts.families
        owned = [f for f in families if contracts.owner_of(f) == cls.stage_id]
        return tuple(sorted(owned) + sorted(contracts.universally_ownable & set(families)))

    def embodiment_snapshot(self, state, branch: Optional[str]) -> Dict[str, List[str]]:
        """What of this branch's embodiment stands, by family and id.

        THIS BRANCH WHERE THERE IS ONE: `_premises` is the membership the
        architecture already records, and reading by family alone would take in
        a sibling candidate's embodiment. A universally ownable family is
        included only where THIS stage authored the record, because s05 may not
        speak for an Assumption another responsibility wrote.
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

    # ------------------------------------------------------------ completeness
    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        """The structural checks, over the LOWERED records.

        `to_operations` has already refused anything incomplete, so this is
        expected to be empty; it runs because the settlement gate asks the same
        questions of what stands and the two must not be able to disagree. If it
        ever reports, the response is refused rather than written incomplete -
        which is why it is computed here and raised, not returned as a
        declaration to be applied around.
        """
        _response, manifest, out = self.lowered(parsed, inputs)
        view = inputs.get(self.context_key) or {}
        rows = dict(embodiment.rows_from_response(lowered_as_parsed(out), view))
        problems = embodiment.structural_problems(rows)
        outstanding = outstanding_duties(manifest, rows)
        if problems or outstanding:
            raise StageError(
                "s05 lowered embodiment leaves duties outstanding (%d):\n  - %s"
                % (len(problems) + len(outstanding),
                   "\n  - ".join(list(problems) + list(outstanding))))
        return []


def lowered_as_parsed(out: "lowering.LoweredEmbodiment") -> Dict[str, Any]:
    """The lowered records in the shape the shared row reader takes.

    `id` and `entity_id` both, because `rows_from_response` reads either and the
    older per-check messages name `id`. One record, two spellings of the same
    identity - never two identities.
    """
    def rows(records):
        return [dict(r, id=r["entity_id"]) for r in records]
    return {"features": rows(out.features), "parameters": rows(out.parameters),
            "constraints": rows(out.constraints),
            "kinematic_realizations": rows(out.kinematic_realizations),
            "realizations": rows(out.realizations)}


def outstanding_duties(manifest: duty_manifest.EmbodimentDutyManifest,
                       rows: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """Duties of the manifest that the canonical rows do not discharge.

    The count a reviewer reads as "outstanding S05 duties". It is derived from
    the same manifest the prompt rendered, over the same rows the settlement
    gate reads, so the three cannot disagree.
    """
    out: List[str] = []
    claims = {r.get("realizes") for r in rows.get("KinematicRealization") or []}
    for duty in manifest.realizations:
        if duty.target not in claims:
            out.append("duty: %s (%s) is embodied by no KinematicRealization"
                       % (duty.target, duty.family))
    realized: Dict[str, Set[str]] = {}
    for f in rows.get("Feature") or []:
        for named in embodiment._named_interfaces(f):
            realized.setdefault(named, set()).add(f.get("body"))
    for duty in manifest.interfaces:
        for body in duty.bodies:
            if body not in realized.get(duty.interface, set()):
                out.append("duty: interface %s has no feature realizing its %s side"
                           % (duty.interface, body))
    additive = {f.get("body") for f in rows.get("Feature") or []
                if embodiment.polarity_table().get(
                    str(f.get("feature_kind", "")).upper()) == "ADDITIVE"}
    for body in manifest.bodies:
        if body not in additive:
            out.append("duty: body %s has no additive feature" % body)
    governed = {c.get("governs_interface") for c in rows.get("Constraint") or []
                if str(c.get("kind", "")).upper() in lowering.GOVERNING_KINDS
                and c.get("governs_interface")}
    for iid in manifest.governed_interfaces():
        if iid not in governed:
            out.append("duty: interface %s owes a governing Constraint and has none" % iid)
    # THE SPATIAL HALF, over the SAME standing rows. A region whose role means
    # free space is cleared by material that removes material AND sits at the
    # region; anything else is an aperture the body has buried.
    polarity = embodiment.polarity_table()
    for duty in manifest.free_space_regions():
        for body in duty.owning_bodies:
            clearing = [f for f in rows.get("Feature") or []
                        if f.get("body") == body
                        and (f.get("placement") or {}).get("datum") == duty.region
                        and polarity.get(str(f.get("feature_kind", "")).upper()) == "SUBTRACTIVE"]
            if not clearing:
                out.append("duty: region %s (%s) must be free of %s's material and no feature "
                           "of that body removes material at it"
                           % (duty.region, duty.role, body))
    return out


def carried_spatial_duties(manifest: duty_manifest.EmbodimentDutyManifest) -> Dict[str, Any]:
    """The duties whose evidence is SETTLED GEOMETRY'S, carried to whoever can
    answer them.

    s05 authors the route and refuses what its own model contradicts; it cannot
    prove a solid does not collide before there is a solid. These travel with
    the design so s07 evaluates the compiled B-reps against the same duties
    rather than against a second list someone wrote for it.
    """
    return {"free_space_regions": [d.region for d in manifest.free_space_regions()],
            "transitions": [d.transition for d in manifest.transitions],
            "released_motions": [{"transition": d.transition,
                                  "released": list(d.released_constraints),
                                  "motions": [list(m) for m in d.required_motions]}
                                 for d in manifest.released_motions],
            "state_restraints": [{"relation": d.relation, "state": d.state,
                                  "coordinates": dict(d.joint_coordinates)}
                                 for d in manifest.state_restraints],
            "assembly": [{"step": d.step, "body": d.body,
                          "insertion_direction": list(d.insertion_direction)
                          if d.insertion_direction else None}
                         for d in manifest.assembly]}


def _record_refs(record: Any) -> Set[str]:
    """Every parameter id a canonical record's expressions read."""
    out: Set[str] = set()
    if isinstance(record, dict):
        if isinstance(record.get("ref"), str):
            out.add(record["ref"])
        for value in record.values():
            out |= _record_refs(value)
    elif isinstance(record, list):
        for item in record:
            out |= _record_refs(item)
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


# THE DUTY LIST IS THE MANIFEST'S. `render_joint_duties` used to walk the view
# and write the same enumeration in prose, beside the checks that enforced it -
# two derivations of one fact, and the pair could disagree about what was owed.
# `duty_manifest.EmbodimentDutyManifest.render` is now the only one, and the
# same object validates the response and answers the settlement gate.


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
    from .base import CAUSE_PREREQUISITES, CAUSE_REFUSED

    rows = [r for r in repair.get("findings") or [] if isinstance(r, dict)]
    if repair.get("cause") == CAUSE_REFUSED:
        # NOTHING WAS WRITTEN. The answer was well-formed enough to read and the
        # write boundary refused it whole, because a patch is all or nothing.
        lines = ["  Your previous answer was REFUSED AT THE WRITE BOUNDARY (round %s) and NOTHING "
                 "was written. What stands is what stood before it. The reasons:"
                 % repair.get("round")]
        for row in rows:
            lines.append("  - %s" % row.get("detail"))
        lines.append("  Fix exactly these and restate the embodiment. Everything else in your "
                     "previous answer was acceptable - a patch is written whole or not at all, "
                     "so one malformed field discarded all of it.")
        lines += _standing_block(repair)
        lines.append(_SNAPSHOT_RULE)
        return "\n".join(lines)
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
    "  HOW TO REVISE. Answer with the COMPLETE embodiment, exactly as you would author it "
    "for the first time: every feature, every parameter, every constraint, every "
    "assignment. You name no canonical id and you restate none - production replaces this "
    "branch's whole embodiment with what you return, in one write. Keep everything that was "
    "right, change what the report names, and never answer a conflict by dropping a "
    "required constraint or leaving a duty unassigned.")


def _standing_block(repair: Dict[str, Any]) -> List[str]:
    """What stands and is about to be replaced, by family and id.

    Shown so the report's subjects can be located, not so an id can be
    restated: the response names no canonical id, and the whole embodiment is
    replaced by what it returns.
    """
    current = repair.get("current") or {}
    if not current:
        return []
    out = ["  What stands for this branch today (it is REPLACED by what you return, whole):"]
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
    """S05-C2: every blocking relation is embodied by a KinematicRealization.

    THE CHECK ITSELF is `embodiment.restraint_realization_findings`, shared with
    s06's entry gate. It asks that the claim exists and that its material covers
    both sides the relation acts between; which DOFs are blocked, in which
    configurations, stays the relation's own.

    IT ASKED SOMETHING WEAKER BEFORE: whether each side carried ANY feature. A
    clearance pocket on both sides satisfied that and blocks nothing. S05-C3 was
    added to close the gap by asking whether a feature was named STOP, SHOULDER
    or KEEPER - a claim about a WORD, which refused a restraint realized by a
    rib, a wall or a pocket floor and accepted one realized by a label. Both are
    retired: what restrains is declared, and the declaration is what is checked.
    A MobilityExpectation already names the authoritative relation; this is its
    embodiment.
    """
    return ["S05-C2: " + f.detail for f in embodiment.restraint_realization_findings(
        embodiment.rows_from_response(parsed, view))]


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
    """S05-C11: every Joint is embodied by a KinematicRealization naming it,
    whose features cover each body the joint relates.

    THE CHECK ITSELF is `embodiment.realization_findings`, shared with s06's
    entry gate, which also asks that every claim names a relation this branch
    carries and material that exists. NO AXIS IS COMPARED and no joint class is
    named: the geometry that embodies a relation need not be aligned with it,
    and a rule requiring alignment refuses transverse pads guiding a slide, a
    rod in a bore with rotation deliberately free, and every realization carried
    by several elements at once.
    """
    return ["S05-C11: " + f.detail for f in embodiment.realization_findings(
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
