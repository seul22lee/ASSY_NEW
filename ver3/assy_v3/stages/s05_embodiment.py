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
from ..view import Source, Sufficiency, ViewStatus
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
   Give each feature an `envelope` - {{"centre": [x,y,z], "half_extent": [x,y,z]}}
   in the same frame as the functional regions below - so its occupancy can be
   checked against the regions the design reserved. A feature with no envelope
   cannot be checked and is reported as incomplete, not as passing.
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
   A CLEARANCE or INTERFERENCE_FREE constraint must also name the interface it
   governs, as `governs_interface`. A declared clearance with no constraint
   naming it is a clearance the settlement loop was never given.
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
         ("body", "feature_kind", "geometry", "envelope"), ()),
        ("realizations", "Realization", "RLZ-",
         ("addresses_obligations", "participating_features",
          "verification_predicate"), ()),
        ("parameters", "Parameter", "PRM-",
         ("symbol", "unit"), ("status",)),
        ("constraints", "Constraint", "CON-",
         ("expression", "parameters", "kind", "governs_interface"), ()),
        ("construction_statements", "ConstructionStatement", "CST-",
         ("body", "operation", "operands", "parameters"), ()),
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

    def consumer_view(self, state, invocation=None, budget_chars=None):
        """The committed selection decides the branch. A caller may not overrule it.

        `build_consumer_view` lets a caller name an invocation branch, which is
        right for s03/s04 - they run once per alternative, before anything is
        chosen. s05 runs AFTER selection, once, on the alternative that was
        chosen. So an invocation naming a different candidate is not a scoping
        choice; it is a request to embody a design nobody selected.

        Refused by returning a view that is not READY rather than by raising:
        `invoke` already declines to call a provider on an unready view and
        records why, so the refusal arrives as evidence instead of a traceback.
        """
        view = super().consumer_view(state, invocation, budget_chars)
        asked = getattr(invocation, "branch", None)
        committed = self.selected_candidate(view.payload())
        if asked and committed and asked != committed:
            view.status = ViewStatus.UPSTREAM_INSUFFICIENCY
            detail = ("this invocation asks s05 to embody %s, but the standing "
                      "selection commits to %s; embodiment may not be routed to "
                      "a candidate nobody chose" % (asked, committed))
            # The SHAPE the rest of the system reads. `_unmet` formats an
            # assessment by its `requirement` and `coverage` keys, so an entry
            # invented with different keys would crash the very reporting path
            # that exists to explain the refusal.
            view.assessment = list(view.assessment) + [{
                "requirement": "selection_commitment",
                "source": Source.REASONING_PREMISE.value,
                "verdict": Sufficiency.MISSING_UPSTREAM.value,
                "coverage": [{"obligation": "selection_decision",
                              "verdict": Sufficiency.MISSING_UPSTREAM.value,
                              "expected_count": 1, "selected_count": 0}],
                "families": ["SelectionDecision"], "selected": 0,
                "detail": detail, "trace": {"contradiction": detail}}]
        return view

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
                      "geometry": f["geometry"]}
            premises = [f["body"]]
            if f.get("envelope") is not None:
                fields["envelope"] = f["envelope"]
                # ONLY when there is an envelope. A feature with no coordinates
                # does not rest on the frame, and premising it anyway would stale
                # geometry that a change of basis cannot affect.
                premises += scales
            ops.append(Op("CREATE", "Feature", f["id"], fields, prov,
                          premise_refs=premises))
        for r in parsed.get("realizations", []):
            obligations = list(r.get("addresses_obligations") or [])
            features = list(r.get("participating_features") or [])
            ops.append(Op("CREATE", "Realization", r["id"], {
                "addresses_obligations": obligations,
                "participating_features": features,
                "verification_predicate": r["verification_predicate"]}, prov,
                premise_refs=obligations + features))
        for p in parsed.get("parameters", []):
            ops.append(Op("CREATE", "Parameter", p["id"], {
                "symbol": p["symbol"], "unit": p["unit"],
                "status": ir.DECLARED}, prov))
        for c in parsed.get("constraints", []):
            fields = {"expression": c["expression"],
                      "parameters": c.get("parameters", []),
                      "kind": c["kind"]}
            premises = list(c.get("parameters") or [])
            if c.get("governs_interface"):
                # A typed reference AND a premise: the constraint expresses that
                # interface's clearance, so a change to the interface withdraws
                # standing from the constraint that spoke for it.
                fields["governs_interface"] = c["governs_interface"]
                premises.append(c["governs_interface"])
            ops.append(Op("CREATE", "Constraint", c["id"], fields, prov,
                          premise_refs=premises))
        for s in parsed.get("construction_statements", []):
            fields = {"body": s["body"], "operation": s["operation"],
                      "operands": s.get("operands", []),
                      "parameters": s.get("parameters", {})}
            for optional in ("axis", "feature"):
                if s.get(optional):
                    fields[optional] = s[optional]
            # THE BODY, THE RESULTS IT CONSUMES, AND THE FEATURE IT REALIZES -
            # and deliberately NOT the parameters it reads.
            #
            # A statement references a parameter SYMBOLICALLY; it does not rest
            # on that parameter's value. Recording the parameter as a premise
            # made every statement go STALE the moment s06 settled the dimension
            # it names, because an extension by a stage outside the owner stales
            # what was concluded from the record - so the program was stale
            # before the compiler ever read it, in the ordinary successful flow.
            #
            # What DOES rest on the settled values is the geometry, and the
            # GeometrySignature records them as premises for exactly that reason.
            # NOT the feature either, and the direction is why. A statement
            # REALIZES a feature; it does not rest on one. Recording the feature
            # as a premise inverted that, and s07 writing
            # `Feature.compiled_by_statement` then staled the very statement it
            # had just compiled - the compiler's record of success invalidating
            # its own input. `feature` stays as the traceability link it is.
            ops.append(Op("CREATE", "ConstructionStatement", s["id"], fields, prov,
                          premise_refs=[s["body"]] + list(s.get("operands") or [])))
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

    A previous version admitted an exception: an Interface between two bodies
    could skip a feature on one side if some COMPLIANT joint connected the same
    pair. That was wrong twice.

    It contradicted the ontology. Compliance is INTERNAL - between RigidGroups
    of one body - so a joint spanning the pair was not the thing the exception
    described; it was a malformed record, and the exception admitted it as
    justification for omitting geometry.

    And it contradicted the Joint contract's own rule, which is unconditional:
    "A joint_type label alone is inert. A realization on each side is required
    (INV-008)." Two bodies that touch need two features. If one of them is a
    flexure, the flexure is geometry on its own body and gets a feature like
    anything else.

    A malformed cross-body COMPLIANT joint is now reported rather than used, so
    the record that used to excuse a missing feature is the thing that fails.

    WHAT THIS CHECK DOES NOT PROVE: that the compliant element itself exists as
    the geometry a reduced-order beam model would consume. `compliant_element`
    is an untyped prose field naming that geometry, and nothing canonical ties
    it to a Feature id. Inferring it from the text would be reading a model's
    sentence as a structural fact. That claim is NOT automatically verified and
    is not asserted anywhere below.
    """
    by_body = _features_by_body(parsed)
    groups = _body_of_group(view)
    out = []

    for joint in _rows(view, "Joint"):
        if str(joint.get("joint_type", "")).upper() != "COMPLIANT":
            continue
        parent = groups.get(joint.get("parent_group"))
        child = groups.get(joint.get("child_group"))
        if parent and child and parent != child:
            out.append("S05-C1: joint %s is COMPLIANT but connects groups on "
                       "two different bodies (%s and %s); compliance is a "
                       "relation between rigid groups of ONE body"
                       % (joint.get("entity_id"), parent, child))

    for iface in _rows(view, "Interface"):
        bodies = [b for b in (iface.get("bodies") or []) if b]
        for body in [b for b in bodies if not by_body.get(b)]:
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


#: `Obligation.scope`, verbatim from DESIGN_STATE_CONTRACT. UNIVERSAL is an
#: obligation EVERY candidate must satisfy; CANDIDATE_DISCRIMINATING is one
#: whose satisfaction DIFFERS BY CANDIDATE, and therefore belongs to whichever
#: candidates actually took it on.
UNIVERSAL = "UNIVERSAL"
CANDIDATE_DISCRIMINATING = "CANDIDATE_DISCRIMINATING"


def applicable_obligations_for_embodiment(view: Dict[str, Any]) -> Set[str]:
    """The obligations the SELECTED candidate must discharge. One rule, one place.

    s05 sees the whole obligation set, and it should: coverage cannot be read
    from a subset, and an embodiment reasoning about its own obligations in
    ignorance of the rest is reasoning in a smaller design than the real one.
    But seeing is not owing. The design-wide set includes obligations that exist
    BECAUSE alternatives differ, and demanding that the chosen candidate
    discharge a rejected candidate's obligations is demanding it be two designs.

    The split is already in the data:

      UNIVERSAL                 every candidate must satisfy it
      CANDIDATE_DISCRIMINATING  satisfaction differs by candidate, so it applies
                                to this one exactly when this candidate's
                                AcceptanceContract took it on

    `satisfiable_at` is deliberately NOT consulted. It names the EARLIEST stage
    at which an obligation can be satisfied, so reading `satisfiable_at == s05`
    as "s05 owns it" would silently drop every obligation that became satisfiable
    at s03 or s04 and is still this candidate's to realize in geometry.

    Used by C4 and by the tests, so the view's acceptance context and the check's
    population cannot drift into two different answers.
    """
    accepted: Set[str] = set()
    for contract in _rows(view, "AcceptanceContract"):
        accepted.update(contract.get("obligations") or [])

    out: Set[str] = set()
    for row in _rows(view, "Obligation"):
        oid = row.get("entity_id")
        if not oid:
            continue
        scope = str(row.get("scope") or "").upper()
        if scope == CANDIDATE_DISCRIMINATING:
            # Only if THIS candidate took it on. The view is already scoped to
            # the committed branch, so an AcceptanceContract reaching this point
            # is the selected candidate's.
            if oid in accepted:
                out.add(oid)
            continue
        # UNIVERSAL, and anything whose scope is absent or unrecognised. Failing
        # OPEN here is deliberate: an obligation whose scope nobody stated is an
        # obligation nobody has excused, and quietly dropping it would turn a
        # missing field into a discharged duty.
        out.add(oid)
    return out


def check_c4_obligations_realized(parsed, view) -> List[str]:
    """S05-C4: every APPLICABLE Obligation is cited by a Realization with a predicate.

    INV-008. A realization that cites an obligation without a verification
    predicate discharges nothing, so an unpredicated citation does not count.

    Applicable, not every obligation in the view: see
    `applicable_obligations_for_embodiment`. Checking the design-wide set made
    the selected candidate answerable for obligations that exist only because a
    rejected alternative worked differently.
    """
    cited: Set[str] = set()
    out = []
    for r in parsed.get("realizations") or []:
        if not str(r.get("verification_predicate") or "").strip():
            out.append("S05-C4: realization %s carries no verification predicate; "
                       "it discharges nothing (INV-008)" % r.get("id"))
            continue
        cited.update(r.get("addresses_obligations") or [])
    for oid in sorted(applicable_obligations_for_embodiment(view)):
        if oid not in cited:
            out.append("S05-C4: obligation %s applies to the selected candidate "
                       "and is cited by no realization" % oid)
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

    A RE-RUN of s04b's occupancy against the new geometry, and deliberately the
    same arithmetic: `aabb` and `overlaps` are imported from the s04 module that
    already owns them rather than reimplemented, so the two stages cannot come to
    different answers about the same boxes.

    The first version of this read `intrudes_region` off the response - a key no
    contract declares and no producer emits - so it read None and passed on
    everything. A feature that cannot be evaluated is now reported as
    INCOMPLETE rather than as clean: silence about occupancy is the failure mode
    this check exists to prevent.
    """
    from .s04_envelope_and_motion import (aabb, excludes_occupancy,
                                          overlaps, unknown_region_role)

    out_unknown: List[str] = []
    regions = []
    for r in _rows(view, "FunctionalRegion"):
        if unknown_region_role(r.get("role")):
            # Not silently skipped. An undeclared role has no occupancy policy,
            # so treating it as harmless would be deciding the policy here.
            out_unknown.append(
                "S05-C8: region %s declares role %r, which is not in the "
                "declared vocabulary, so whether a feature may occupy it is "
                "undefined" % (r.get("entity_id"), r.get("role")))
            continue
        volume = r.get("volume")
        if not isinstance(volume, dict):
            continue          # a region with no volume is s04's problem, not s05's
        centre, half = volume.get("centre"), volume.get("half_extent")
        if not (isinstance(centre, list) and isinstance(half, list)):
            continue
        regions.append((r, aabb(centre, half)))
    if not regions:
        return out_unknown

    out = list(out_unknown)
    for f in parsed.get("features") or []:
        envelope = f.get("envelope")
        centre = (envelope or {}).get("centre")
        half = (envelope or {}).get("half_extent")
        if not (isinstance(centre, list) and isinstance(half, list)):
            out.append("S05-C8: feature %s declares no usable envelope, so its "
                       "occupancy against %d declared region(s) cannot be "
                       "evaluated" % (f.get("id"), len(regions)))
            continue
        box = aabb(centre, half)
        for region, region_box in regions:
            # WHICH ROLES EXCLUDE OCCUPANCY is the contract's to say, not this
            # check's. `excludes_occupancy` reads FunctionalRegion.role_policy,
            # and s04b's occupancy check reads the same function - so the two
            # stages cannot reach different answers about the same region. This
            # was previously a tuple written out here and again in s04.
            if not excludes_occupancy(region.get("role")):
                continue
            if overlaps(box, region_box):
                out.append("S05-C8: feature %s intrudes into %s region %s"
                           % (f.get("id"), region.get("role"),
                              region.get("entity_id")))
    return out


#: The interaction kind that IS a declared clearance. From s03's own vocabulary:
#: CONTACT, CLEARANCE, INTERFERENCE_FIT, COMPLIANT_INTERACTION.
CLEARANCE_KINDS = ("CLEARANCE", "INTERFERENCE_FIT")


def check_c9_clearance_constraints(parsed, view) -> List[str]:
    """S05-C9: every declared clearance pair has a Constraint that names it.

    Per interface and by TYPED REFERENCE. `Constraint.governs_interface` is a
    declared reference to the Interface whose clearance the constraint expresses,
    so the link is something production emits and DesignState validates rather
    than something a test injects - the first version looked for `interface` and
    `realizes` keys that no contract declares, which made the link set
    permanently empty.

    The recorded history is the argument for per-interface rather than in
    aggregate: a clearance that was never given to the settlement loop produced a
    BUILD FAILURE patched by hand instead of an INFEASIBILITY that triggered a
    re-solve, and a regression rode along undetected for three revisions. One
    constraint cannot speak for five clearances.
    """
    governed = {c.get("governs_interface")
                for c in parsed.get("constraints") or []
                if str(c.get("kind", "")).upper() in
                ("CLEARANCE", "INTERFERENCE_FREE") and c.get("governs_interface")}
    out = []
    for iface in _rows(view, "Interface"):
        if str(iface.get("interaction_kind", "")).upper() not in CLEARANCE_KINDS:
            continue
        if iface.get("entity_id") not in governed:
            out.append("S05-C9: interface %s declares %s and no Constraint "
                       "governs it" % (iface.get("entity_id"),
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
