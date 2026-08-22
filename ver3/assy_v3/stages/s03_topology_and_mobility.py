"""S03 - topology, mobility and assembly strategy.

Engineering question: what things are there, how are they connected, what may
move, what must not, what reacts what, and in what order does it go together?

Geometry first appears here and it is SYMBOLIC: frames, axis DIRECTIONS,
sidedness. No magnitude and no axis PLACEMENT - placement depends on feature
envelopes that do not exist until s04.

THE ONE STRUCTURAL IDEA
    The DOF DOMAIN and the DISPOSITION of a cell are two different facts and
    have two different authors. The domain - every rigid group x every
    configuration x every rigid-body DOF - is enumerated HERE, mechanically, and
    is BOOKKEEPING: this code guarantees it, so it can never be evidence about
    the design. What a cell MEANS comes only from a premise that is present,
    typed and referenceable - a Joint, a ConstraintRelation, an authored
    irrelevance naming a Scenario - and a cell no premise covers is
    UNDISPOSITIONED. No stage asks a model to disposition cells one by one, and
    no branch here composes a disposition out of an absence.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from ..state.patch import Op
from .base import Stage, carry_invocation_premises

def _family(name: str) -> Dict[str, Any]:
    """One entity family's contract record. READ, never restated.

    A vocabulary spelled out here as well as in the contract is two authorities
    that drift, and this module has been on the wrong side of that twice.
    """
    import yaml as _yaml
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "..", "contracts", "DESIGN_STATE_CONTRACT.yaml")
    with open(os.path.abspath(path)) as fh:
        doc = _yaml.safe_load(fh)
    # Both sections, because the split is by AUTHORITY CLASS and not by where a
    # reader should look: MobilityExpectation is declared among the assurance
    # families, and a lookup that knew only `entity_families` would report the
    # contract as silent about it.
    families = dict(doc["entity_families"])
    families.update(doc.get("assurance_families") or {})
    return families[name]


#: THE LOADED CONTRACT, once. Cached because `Contracts` is immutable by
#: construction - every accessor hands back a detached copy and assignment raises
#: - so there is nothing a later reader could change for an earlier one, and a
#: per-call YAML read inside a completeness method is a cost with no answer
#: attached to it.
_CONTRACTS_ONCE = None


def _contracts():
    global _CONTRACTS_ONCE
    if _CONTRACTS_ONCE is None:
        from ..state.design_state import Contracts
        _CONTRACTS_ONCE = Contracts()
    return _CONTRACTS_ONCE


def _branch_population() -> str:
    """The population name meaning "drawn from the branch this invocation embodies".

    Read from the consumer boundary that owns the vocabulary rather than spelled
    out again here. A second copy of a vocabulary is two authorities that drift,
    which is the failure this module has already been on the wrong side of twice.
    Imported inside the function because the view imports stages back.
    """
    from ..view.consumer_view import INVOCATION_BRANCH
    return INVOCATION_BRANCH


#: The six rigid-body degrees of freedom. The domain of the totality.
DOF_NAMES = ("TX", "TY", "TZ", "RX", "RY", "RZ")

#: The LIVE disposition vocabulary, read from the contract.
#:
#: MAINTAINED_BY_CLASS is NOT in it. S-5 stopped producing it from absence, and
#: this correction retires it: its only evidence was a `holding_class` STRING,
#: which names no entity and therefore can never be the resolvable premise U-6
#: requires. No frozen source gives it one - proposal 11.2 and 20.2 enumerate
#: exactly INTENDED, CONSTRAINED (BLOCKED_BY), IRRELEVANT and UNDISPOSITIONED -
#: and an enum kept because historical code used it is a live path to a
#: disposition nothing can back.
DISPOSITIONS = tuple(_family("MobilityExpectation")["disposition_values"])

#: disposition -> the field that must carry its premise. Read from the contract
#: so the derivation, the write boundary and the prompt cannot disagree about
#: what backs a disposition.
PREMISE_FIELD = dict(
    _family("MobilityExpectation")["field_semantics"]["dispositions"]["premise_field"])

JOINT_TYPES = ("REVOLUTE", "PRISMATIC", "HELICAL", "SPHERICAL", "PLANAR",
               "CYLINDRICAL", "FIXED", "COMPLIANT")

INTERACTION_KINDS = ("CONTACT", "CLEARANCE", "INTERFERENCE_FIT", "COMPLIANT_INTERACTION")

#: The retention trichotomy, plus NONE. A rigid part pushed straight in leaves
#: the reverse direction open, so a RETAINED body needs one of the three - but
#: the first body placed is retained by nothing and must be able to say so.
#: Second instance of this shape in one window (see AXIS_DIRECTIONS): every
#: closed value set needs a member meaning "legitimately none".
TERMINATION_STRATEGIES = ("LATER_BODY_COVER", "ROTATION", "ELASTICITY", "NONE")

#: The strategies that RETAIN. NONE is a permitted value of the field and is
#: not one of them: it says this body is not retained by a termination of its
#: own, which is a real answer for a part nothing holds and no answer at all
#: for a part the design says is held.
RETAINING_STRATEGIES = tuple(t for t in TERMINATION_STRATEGIES if t != "NONE")

PATH_KINDS = ("RIGID", "DEFORMATION_RESOLVED")

#: Why a constraint must exist. The `ConstraintRelation.driver` vocabulary.
#:
#: The legacy blocking relation is GONE from this module: its alias table, its
#: canonicaliser, its required-field list and the parser that read it back out of
#: per-DOF detail. It had no identity, so a disposition could not cite it, which
#: is exactly why it could not be the premise the contract asks for. Binding its
#: field names was the right answer while it was the only shape a model emitted;
#: keeping the machinery once nothing reads it would be a live compatibility path
#: to a fact the pipeline no longer recognises.
CONSTRAINT_DRIVERS = ("LOAD", "KINEMATIC_NECESSITY", "DECLARED_SCENARIO")


#: Which DOF each joint class leaves FREE, relative to its own axis. Ordinary
#: kinematics, product-independent, and the basis for deriving the disposition
#: grid instead of asking a model to author it cell by cell.
def free_dof(joint_type: str, axis: str) -> Set[str]:
    a = (axis or "+Z").upper().lstrip("+-")
    a = a if a in ("X", "Y", "Z") else "Z"
    others = [x for x in ("X", "Y", "Z") if x != a]
    jt = (joint_type or "").upper()
    if jt == "REVOLUTE":
        return {"R" + a}
    if jt == "PRISMATIC":
        return {"T" + a}
    if jt in ("HELICAL", "CYLINDRICAL"):
        return {"R" + a, "T" + a}
    if jt == "SPHERICAL":
        return {"RX", "RY", "RZ"}
    if jt == "PLANAR":
        return {"T" + others[0], "T" + others[1], "R" + a}
    if jt == "COMPLIANT":
        # WHAT THE AXIS RULE WOULD SAY, and it is not the authority for this
        # class. A flexure names the axis it bends ABOUT, and every compliant
        # joint in the accepted corpus declares a rotation there, so inferring a
        # translation along the axis overruled the joint's own statement. Kept
        # because `joint_dof_consistency_check` needs to be able to ask what the
        # ordinary rule would give; `joint_free_dof` is what decides.
        return {"T" + a}
    return set()                                    # FIXED, and anything unknown


#: The joint classes whose type and axis determine their free DOF completely.
#: COMPLIANT is deliberately absent: compliance couples an axis to a deflection
#: through a geometry this stage has not decided, so the class implies no unique
#: answer and the declared one is all there is.
DETERMINED_BY_TYPE_AND_AXIS = ("REVOLUTE", "PRISMATIC", "HELICAL", "CYLINDRICAL",
                               "SPHERICAL", "PLANAR", "FIXED")


def joint_free_dof(joint: Dict[str, Any]) -> Set[str]:
    """THE free DOF of a joint. One authority, and it is the joint's own field.

    `Joint.dof` is canonical, required, and written by the pass that decided the
    mechanism. The derivation used to ignore it and re-infer freedom from
    joint_type and axis_direction - which for every COMPLIANT joint in the
    accepted corpus produced a TRANSLATION along the axis while the joint
    declared a ROTATION about it. Two answers to one question, with the
    unwritten one winning.

    Whether the declared value AGREES with what an ordinary class implies is a
    different question, asked by `joint_dof_consistency_check`. Silence about
    that agreement is not a licence to overwrite the declaration.

    A joint that declares nothing at all falls back to the class rule, because a
    record with no `dof` key predates the field rather than asserting emptiness -
    and an empty list, which IS an assertion, is honoured as one.
    """
    declared = joint.get("dof")
    if declared is None:
        return free_dof(joint.get("joint_type"), joint.get("axis_direction"))
    return {d for d in declared if d in DOF_NAMES}


def joint_dof_consistency_check(state) -> List[str]:
    """S03-C10. The declared DOF and the joint class say the same thing.

    Not a second opinion about kinematics: for the ordinary classes the type and
    the axis DETERMINE the free DOF, so a REVOLUTE about +Z declaring TZ is a
    mistake, and the only way to notice is to compare the two. The canonical
    value still wins everywhere it is read - this reports the disagreement rather
    than resolving it silently.

    COMPLIANT is checked differently and for a reason stated in
    `DETERMINED_BY_TYPE_AND_AXIS`: its class implies no unique DOF, so the
    requirement is that it DECLARES one, from the canonical vocabulary. A
    compliant joint declaring nothing free is a compliant member that does not
    comply.
    """
    problems: List[str] = []
    for j in state.family("Joint"):
        jt = str(j.get("joint_type") or "").upper()
        declared = j.get("dof")
        if declared is None:
            problems.append("JOINT_DOF_ABSENT: %s declares no dof; the field is "
                            "canonical and required" % j["entity_id"])
            continue
        unknown = [d for d in declared if d not in DOF_NAMES]
        if unknown:
            problems.append("JOINT_DOF_NOT_CANONICAL: %s declares %s, which is "
                            "not %s" % (j["entity_id"], unknown, list(DOF_NAMES)))
            continue
        if jt in DETERMINED_BY_TYPE_AND_AXIS:
            implied = free_dof(jt, j.get("axis_direction"))
            if set(declared) != implied:
                problems.append(
                    "JOINT_DOF_CONTRADICTS_CLASS: %s is a %s about %s, which "
                    "leaves %s free, and declares %s"
                    % (j["entity_id"], jt, j.get("axis_direction"),
                       sorted(implied) or "nothing", sorted(declared) or "nothing"))
        elif jt == "COMPLIANT" and not declared:
            problems.append("COMPLIANT_JOINT_FREES_NOTHING: %s declares no free "
                            "DOF, so nothing about it complies" % j["entity_id"])
    return problems

REGION_ROLES = ("ACCESS", "SUPPORT", "KEEP_OUT", "APERTURE")

#: Directions are symbolic axis directions, never placements.
#: Symbolic axis directions. NONE is a VALUE, not an omission: a FIXED joint
#: genuinely has no axis, and a permitted-value set with no way to say that
#: forces the model to choose between inventing an axis and dropping a required
#: field. Live evidence: it dropped the field.
AXIS_DIRECTIONS = ("+X", "-X", "+Y", "-Y", "+Z", "-Z", "NONE")

#: Tokens that would be a metric magnitude leaking into a stage that has none.
_MAGNITUDE = re.compile(r"\b\d+(?:\.\d+)?\s*(mm|cm|m|deg|degrees|rad|kg|g|n|nm)\b",
                        re.IGNORECASE)


PROMPT = """You are defining the MECHANISM for one candidate: what bodies exist,
how they are connected, what may move, what must not, how loads reach the world,
and in what order the thing goes together.

You receive the typed design state. You do not receive the original request.

WHAT EXISTS HERE AND WHAT DOES NOT
Geometry appears at this stage, but only as TOPOLOGY and DIRECTION: which bodies
touch, which joint connects which groups, which way an axis points, which side a
part is inserted from. There are no magnitudes, no dimensions, no positions and
no axis PLACEMENTS - where an axis sits depends on feature sizes that do not
exist yet. Saying "the axis points +Z" is this stage's work. Saying "the axis is
40 mm from the base" is not, and is wrong here even if it later turns out true.

RULES
1. Name the BODIES. A body is a thing that gets made or bought. Give each a
   ROLE - what it does - not a shape. Where a body must flex to do its job, give
   it more than one RIGID GROUP and a COMPLIANT joint between them: ONE group
   and ONE compliant joint PER COMPLIANT MEMBER. Four independent tabs are four
   groups and four joints, not one region.
2. Name every JOINT: its type, the two groups it connects, its degrees of
   freedom, and its axis DIRECTION.
3. Name every INTERFACE - every region where two bodies meet - and classify HOW
   THEY MEET: CONTACT, CLEARANCE, INTERFERENCE_FIT or COMPLIANT_INTERACTION.
   This is not a joint type: FIXED, REVOLUTE and the rest say how two groups are
   CONSTRAINED, and belong on joints. A body pair that meets and is left
   unclassified is a hole in the design. On each body and interface, list the
   obligation ids it is the reason for - the design decision has to be traceable
   to the obligation that forced it, or nothing downstream can tell a load-
   bearing choice from an arbitrary one.
4. Name the CONFIGURATIONS the product has - the distinct states its mechanism
   can be in that matter to its function.
5. Every degree of freedom of every rigid group in every configuration becomes a
   line the pipeline enumerates from what you declare here, so make the groups
   and configurations complete and final. A group you leave out has no lines at
   all, and a line that does not exist cannot be reported as unexplained.
6. A later step traces the load paths and the assembly order. Give it what it
   needs: every body a load could pass through, and every interface it could
   cross.
9. Do not select between candidates and do not score anything.

RESPONSE SCHEMA
Return a single JSON object with exactly these keys, each a list. A list may be
empty. Every field is required unless marked optional. No required field is null.

  bodies[]             id "BOD-0001", role, instance_identity,
                       addresses_obligations[] (obligation ids this body
                       is the reason for; [] if none)
  rigid_groups[]       id "RGP-0001", body, members[], is_default (boolean)
  joints[]             id "JNT-0001", joint_type, parent_group, child_group,
                       dof[], axis_direction, frame_ids[]
                       frame_ids NAMES THE FRAME the axis_direction is expressed
                       in - a symbolic name you coin here, e.g. ["FRM-JNT-0001"].
                       "+Z" relative to nothing is unanswerable, so a joint that
                       states a real direction must name one. You are naming the
                       frame, not locating it: WHERE it sits is decided later
                       from feature sizes that do not exist yet.
                       A joint whose axis_direction is NONE - a FIXED joint
                       constrains everything and points nowhere - needs no frame,
                       and [] is the right answer there.
                       For a COMPLIANT joint, and only then, add these EIGHT
                       fields DIRECTLY ON THE JOINT - not nested inside another
                       object:
                         mode, direction, required_travel, allowable_travel,
                         actuation, compliant_element, root_interface,
                         activation_window
                       actuation is always PRESCRIBED_KINEMATIC - in the real
                       mechanism a contact drives the deflection, but in this
                       model the coordinate is imposed, and the field says so
                       precisely so the structure cannot be read as evidence
                       that the mechanism deflects itself.
                       required_travel is KINEMATIC and is yours to state.
                       allowable_travel is a MATERIAL fact and you do not have
                       the material: report its status as UNSUPPORTED. Do not
                       write a number, and do not write a verdict such as
                       WITHIN_ELASTIC_LIMIT - that would assert a strain result
                       nothing here computed.
  interfaces[]         id "IFC-0001", bodies[], interaction_kind, nominal,
                       addresses_obligations[]
  configurations[]     id "CFG-0001", name, kind, bodies_present[],
                       distinguishing_basis[] {{joint, dof, differs_from[]}}
                       - what makes this configuration a DIFFERENT one: the
                       JOINT COORDINATES whose value differs from the named
                       sibling configurations. [] when nothing is required to
                       differ. A later step realizes this in coordinates and is
                       checked against it, so a name is never what distinguishes
                       two states.
                       NAME THE JOINT YOURSELF. A rigid group has no coordinate;
                       a joint does. Say WHICH joint's coordinate differs and in
                       WHICH of its degrees of freedom - nothing downstream will
                       work it out from the group, because on a chain
                       G1-[J1]-G2-[J2]-G3 the middle link touches two joints and
                       neither of them is the obvious one. The joint you name
                       must be one you emit and must declare that DOF
  functional_regions[] id "FRG-0001", role, owning_bodies[],
                       required_by_actors[] (actor ids from the input; [] for
                       SUPPORT and KEEP_OUT regions no actor uses),
                       reach_targets[] (OTHER functional region ids THIS region
                       gives reach through to - an APERTURE's targets are the
                       ACCESS regions reached through it. Region ids only, from
                       the ones you emit here; [] when this region is itself the
                       destination. It is NOT a description of what an actor
                       wants: that demand is already typed upstream on
                       Actor.must_reach and is not restated here)
  unresolved[]         id "S3U-0001", decision, why_open, alternatives[],
                       alternatives_kind, kept_open_by[], blocks[]

PERMITTED VALUES
  joint_type          {joint_types}
  dof                 {dofs}
  axis_direction      {axis_directions}
  interaction_kind    {interaction_kinds}
  functional region role {region_roles}
  alternatives_kind   ENTITY_REFS | PRINCIPLE_FAMILIES | FREE_TEXT

IDS YOU EMIT ARE NEW
Every id in your response is one you are creating now. The typed input already
contains ids of its own, and reusing one of them does not extend that entity, it
collides with it. Use exactly the prefixes shown above and never an id that
already appears in the input.

REFERENCES BETWEEN ITEMS
  rigid_groups[].body            a body id you emit
  joints[].parent_group/child_group  rigid group ids you emit
  interfaces[].bodies            body ids you emit
  configurations[].bodies_present body ids you emit
  functional_regions[].owning_bodies body ids you emit
  functional_regions[].reach_targets functional region ids you emit
  functional_regions[].required_by_actors actor ids from the input
  joints[].frame_ids             frame names you coin here
  bodies[].addresses_obligations obligation ids from the input
  interfaces[].addresses_obligations obligation ids from the input
  configurations[].distinguishing_basis[].joint        a joint id you emit, which
                                 must declare the dof named beside it
  configurations[].distinguishing_basis[].differs_from configuration ids you emit
  unresolved[].kept_open_by      Ambiguity or Freedom ids from the input, and
                                 nothing else - not a requirement, not a body
  unresolved[].alternatives      when alternatives_kind is ENTITY_REFS these are
                                 entity ids; otherwise they are not ids at all

THE CANDIDATE YOU ARE EMBODYING
{candidate}

TYPED INPUT
-----------
{projection}
"""


def derive_mobility(groups: List[str], configurations: List[str],
                    joints: List[Dict[str, Any]],
                    constraints: List[Dict[str, Any]],
                    irrelevance: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The DOF domain, and what is known about each cell. Two different facts.

    DOMAIN is deterministic and total: every rigid group x configuration x DOF
    cell exists, because the enumerator makes it exist. That totality is
    BOOKKEEPING - it is guaranteed by this function and can never be evidence
    about the design.

    DISPOSITION is what the design asserts about a cell, and it comes only from a
    premise that is present, typed and referenceable:

      covered by a ConstraintRelation       -> BLOCKED_BY, citing the relation
      free by an authored joint's OWN dof   -> INTENDED, citing the joint
      authored irrelevant in a scenario     -> IRRELEVANT_BECAUSE, citing it
      none of those                         -> UNDISPOSITIONED, naming what is
                                               missing

    Those four are tried IN THAT ORDER, and the order is stated because two
    premises can reach one cell: a relation that removes a DOF a joint's class
    leaves free is not a contradiction, it is what a constraint relation is FOR,
    and the configuration-scoped fact is the specific one. Whether two authored
    premises about one cell genuinely disagree is a CROSS-PREMISE question with
    two different authors, which the plan assigns to U-9; this function does not
    adjudicate it and does not pretend the other premise was absent.

    The last line is the change S-5 exists for. This function used to end in an
    `else` that wrote MAINTAINED_BY_CLASS with a holding class composed from the
    first joint reaching the group - or the literal "joint class of no joint"
    when there was none. That is absence used as a premise: the pipeline had no
    way to say "nothing is known here", so it said "a joint class holds it", and
    a reviewer could not tell the two apart. MAINTAINED_BY_CLASS is now retired
    outright: its evidence was a class STRING, which names no entity and so can
    never be the resolvable premise U-6 requires.

    The premise for BLOCKED_BY is a `ConstraintRelation` - the addressable
    physical truth S-4 established - not the legacy blocking relation, which had
    no identity and so could not be cited.

    APPLICABILITY IS THE WHOLE QUESTION. A premise disposes the cells it
    DECLARES and no others: the relation's own `retained_group`, its own
    `blocked_dofs`, its own `configurations`. Proposal 11.3 permits exactly
    "expansion of an authored relation over the DOFs and configurations IT
    DECLARES", and a relation that declares no configuration therefore covers
    none - reading an empty configuration set as "everywhere" turned the author's
    silence into the widest possible claim, which is the same defect in a
    different branch. s03b reports such a relation as incomplete; it does not get
    to dispose the design in the meantime.

    A Joint is different, and the difference is in the contract rather than in
    this code: a Joint declares no configuration set at all, so it is
    unconditioned by construction and its freedom holds wherever the topology
    does. Silence about a field that exists is not the same fact as a field that
    does not exist.

    WHICH DOF a joint frees is read from the joint, through `joint_free_dof`.
    This function used to re-infer it from joint_type and axis_direction, which
    for a COMPLIANT joint meant a translation ALONG the axis while every such
    joint in the accepted corpus declares a rotation ABOUT it - the grid then
    contradicted the canonical record it was derived from, and freed a DOF no
    joint had claimed. Agreement between the declaration and the class is a
    separate question with its own check.
    """
    by_child: Dict[str, List[Dict[str, Any]]] = {}
    for j in joints:
        by_child.setdefault(j.get("child_group"), []).append(j)

    blocked: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for relation in constraints:
        group = relation.get("retained_group")
        dofs = [d for d in (relation.get("blocked_dofs") or []) if isinstance(d, str)]
        configs = [c for c in (relation.get("configurations") or []) if isinstance(c, str)]
        for cfg in configs:
            for dof in dofs:
                blocked[(group, cfg, dof)] = relation

    irrelevant: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for i in irrelevance:
        for dof in (i.get("dof") or []):
            irrelevant[(i.get("rigid_group"), i.get("configuration"), dof)] = i

    out: List[Dict[str, Any]] = []
    for group in groups:
        free: Set[str] = set()
        source: Dict[str, str] = {}
        for j in by_child.get(group, []):
            for dof in joint_free_dof(j):
                free.add(dof)
                source[dof] = j.get("entity_id") or j.get("id")
        for cfg in configurations:
            for dof in DOF_NAMES:
                key = (group, cfg, dof)
                entry: Dict[str, Any] = {"rigid_group": group, "configuration": cfg,
                                         "dof": dof, "derived_by": "s03:derivation"}
                if key in blocked:
                    relation = blocked[key]
                    entry.update({"disposition": "BLOCKED_BY",
                                  "constraint_relation": relation.get("id"),
                                  "blocked_direction": relation.get("blocked_direction"),
                                  "provider_body": relation.get("provider_body"),
                                  "provider_reaction_site":
                                      relation.get("provider_reaction_site"),
                                  "defeat_specification":
                                      relation.get("defeat_specification"),
                                  "driver": relation.get("driver")})
                elif dof in free:
                    entry.update({"disposition": "INTENDED", "by_joint": source.get(dof)})
                elif key in irrelevant:
                    entry.update({"disposition": "IRRELEVANT_BECAUSE",
                                  "scenario": irrelevant[key].get("scenario")})
                else:
                    # No premise covers this cell. Say so, and say what would.
                    entry.update({
                        "disposition": "UNDISPOSITIONED",
                        "missing": "no ConstraintRelation covers this DOF in this "
                                   "configuration, no joint leaves it free, and no "
                                   "scenario declares it irrelevant"})
                out.append(entry)
    return out


def domain_premises(entries: Iterable[Dict[str, Any]], configuration: str) -> List[str]:
    """What the EXISTENCE of these cells rests on. FA-5, the domain half.

    A MobilityExpectation is about one configuration and the rigid groups whose
    cells it carries; withdraw any of them and the cells it addresses are no
    longer in the current domain. Recording only the disposition premises left
    the grid STANDING after its own topology was dropped - it went on describing
    the mobility of a group the design no longer had, and nothing said so.

    Read off the produced rows, so a MobilityExpectation depends on the groups it
    actually contains rather than on every group in the branch.
    """
    out = {configuration} if configuration else set()
    out |= {row["rigid_group"] for row in entries
            if isinstance(row.get("rigid_group"), str) and row["rigid_group"]}
    return sorted(out)


def cited_premises(entries: Iterable[Dict[str, Any]]) -> List[str]:
    """The entities these cells were ACTUALLY DERIVED FROM. FA-4, FA-5.

    A citation inside a disposition record and a DEPENDENCY are two different
    facts and were, until this function, only the first. The typed citation makes
    `constraint_relation: CRL-2` checkable - right family, referent exists - and
    tells a reader where the claim came from. It does not put CRL-2 into
    `Op.premise_refs`, so `_propagate` never saw it, and a MobilityExpectation
    asserting "TX is BLOCKED_BY CRL-2" stayed STANDING after CRL-2 was
    invalidated. Reference integrity was intact; the design just went on claiming
    a DOF was held by something it had withdrawn.

    Collected MECHANICALLY from the rows that were produced, through the
    contract's own disposition -> premise-field map. Three consequences follow
    from that and none of them is a special case:

      - a cell's premise enters because the derivation USED it. Something merely
        visible in the consumer view does not - availability is not dependency,
        and a view is not a claim;
      - UNDISPOSITIONED maps to no field, so it contributes nothing. An honest
        statement that nothing is known cannot depend on anything;
      - the same premise cited by many cells appears once. The dependency is a
        SET: FA-5 asks whether this value rests on that one, not how often.
    """
    out = set()
    for row in entries:
        field = PREMISE_FIELD.get(row.get("disposition"))
        if field and isinstance(row.get(field), str) and row[field]:
            out.add(row[field])
    return sorted(out)


def disposition_completeness(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """How much of the domain rests on evidence, and which cells do not.

    The quantity the audited pipeline could not express. Domain totality was
    trivially true and told a reviewer nothing; this says what fraction of the
    cells a premise actually covers, and names the ones it does not.

    A low number is not a failure. It is a measurement, and an honest one is worth
    more than a total that was guaranteed by construction.
    """
    rows = list(entries)
    undispositioned = [r for r in rows if r.get("disposition") == "UNDISPOSITIONED"]
    evidenced = len(rows) - len(undispositioned)
    return {
        "domain_cells": len(rows),
        "dispositioned_by_evidence": evidenced,
        "undispositioned": len(undispositioned),
        "fraction": (evidenced / len(rows)) if rows else 0.0,
        "cells_without_evidence": [
            "%s/%s/%s" % (r.get("rigid_group"), r.get("configuration"), r.get("dof"))
            for r in undispositioned],
        "reported_as": "ENGINEERING QUANTITY, unlike domain totality which is "
                       "BOOKKEEPING",
    }


def dof_domain(groups: Iterable[str], configurations: Iterable[str]) -> List[Tuple[str, str, str]]:
    """THE enumerator. One branch's groups x one branch's configurations x DOF.

    Computed from the topology and never taken from a response or read back out
    of anything stored. This is what makes omission detectable: no premise has to
    exist for the line to exist, so an uncovered cell is visible as
    UNDISPOSITIONED rather than absent.

    Every answer to "which mobility cells exist" comes through here. The producer
    applies it to the branch its invocation is for; `current_dof_domain` applies
    it to each standing branch and unions the results. One rule, two projections
    of it, and no second formula in a checker.
    """
    return [(g, c, d) for g in groups for c in configurations for d in DOF_NAMES]


def current_dof_domain(state) -> List[Tuple[str, str, str]]:
    """WHICH MOBILITY CELLS CURRENTLY EXIST. The one executable answer.

    Class B, in the operational sense and not only the declared one: it is
    RECOMPUTED from standing topology on every call and is stored nowhere. No
    MobilityExpectation, and no other record, is consulted about whether a cell
    exists - which is what stops a stored structure from becoming a second
    authority for domain existence. A disposition's rigid_group / configuration /
    dof identify WHICH derived cell the disposition is about; they do not assert
    that the cell is there.

    CURRENT means STANDING. Superseded, invalidated and stale topology stays
    readable as history (FA-1) and defines nothing: withdrawing a rigid group
    took it out of the ConsumerView the producer works from, so a domain that
    still contained it was a second currentness rule inside one pipeline, and the
    checker went on demanding cells for a group the design had dropped.

    THE UNION OF THE BRANCHES', never the Cartesian product of everything in
    state. Two alternatives with two groups and two configurations each have 24
    cells apiece and 48 between them; the product of all four groups with all
    four configurations is 96, and the extra 48 are pairs like "candidate A's
    group in candidate B's configuration", which no mechanism contains and no
    producer could ever disposition.

    A cell exists when its group and its configuration belong to a COMMON BRANCH,
    or when neither belongs to any - the second case being a design that has not
    branched, where the whole state is the one mechanism. Branch membership comes
    from `branch_membership`, the same relation the ConsumerView uses to scope a
    branch, so the producer and every reader answer "which mechanism is this
    group in" the same way.
    """
    from ..view.consumer_view import branch_membership

    groups = sorted(g["entity_id"] for g in state.standing("RigidGroup"))
    configs = sorted(c["entity_id"] for c in state.standing("Configuration"))
    owner = branch_membership(state, state.c, set(groups) | set(configs))
    out: List[Tuple[str, str, str]] = []
    for g in groups:
        for c in configs:
            if (owner.get(g) or set()) & (owner.get(c) or set()) or not (
                    owner.get(g) or owner.get(c)):
                out.extend(dof_domain([g], [c]))
    return out


def current_mobility_cells(state) -> List[Dict[str, Any]]:
    """The disposition rows that are CURRENTLY in force.

    From STANDING MobilityExpectations only. A grid whose topology was withdrawn
    is retained and readable, and it is not current coverage: letting it answer
    "is this cell dispositioned" would mean a design could drop a rigid group and
    keep being credited for the mobility of the group it dropped.
    """
    return [d for mex in state.standing("MobilityExpectation")
            for d in mex.get("dispositions", []) if isinstance(d, dict)]


#: The effect vocabulary, read from the contract rather than restated.
_EFFECT_KINDS = tuple(_family("PhysicalEffectObligation")["effect"])


#: The COMPLIANT variant, exactly as DESIGN_STATE_CONTRACT declares it - flat,
#: and `allowable_travel` rather than `allowable_travel_status`. Read from the
#: contract at import so the prompt, the producer and the write boundary cannot
#: drift into three spellings of one variant again.
def _compliant_fields() -> Tuple[str, ...]:
    from ..state.design_state import Contracts
    for rule in Contracts().conditional_requirements("Joint"):
        if rule.get("name") == "compliant_joint_variant":
            return tuple(rule.get("additional_required_fields") or ())
    return ()


COMPLIANT_FIELDS = _compliant_fields()


def _candidate_premise(candidate) -> List[str]:
    """The candidate id an s03 invocation was given, however it was handed over.

    Pass A receives the candidate record; pass B receives its id inside the
    demands. One reader, so the two passes cannot drift into disagreeing about
    what they are embodying.
    """
    if isinstance(candidate, dict):
        candidate = candidate.get("entity_id")
    return [candidate] if isinstance(candidate, str) and candidate else []


class S03TopologyAndMobility(Stage):
    stage_id = "s03"
    pass_id = "s03a"
    #: TOPOLOGY, and not one word about what a DOF means. This pass used to
    #: declare itself the author of "a total DOF disposition" while its response
    #: schema exposed no such field - a responsibility statement describing the
    #: producer it had already stopped being.
    purpose = "turn a candidate family into a mechanism topology"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        projection = inputs["consumer_view"]
        candidate = inputs.get("candidate") or {}
        return PROMPT.format(
            joint_types=" | ".join(JOINT_TYPES), dofs=" | ".join(DOF_NAMES),
            axis_directions=" | ".join(AXIS_DIRECTIONS),
            interaction_kinds=" | ".join(INTERACTION_KINDS),
            region_roles=" | ".join(REGION_ROLES),
            candidate=_render(candidate),
            projection=_render(projection))

    def invocation_premises(self, inputs: Dict[str, Any]) -> List[str]:
        """The candidate this pass was invoked to embody.

        s03 is run once per candidate: the topology it authors exists BECAUSE
        that alternative was chosen to be worked out. Withdraw the candidate and
        the topology must lose unqualified standing, which is what declaring it a
        premise means (FA-5).

        Read from this stage's own declared input, so the fact survives whichever
        runner made the call.
        """
        return _candidate_premise(inputs.get("candidate"))

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s03:topology"
        for b in parsed.get("bodies", []):
            ops.append(Op("CREATE", "Body", b["id"], {
                "instance_identity": b["instance_identity"], "role": b["role"],
                "created_by_stage": "s03",
                "addresses_obligations": b.get("addresses_obligations", [])}, prov))
        for g in parsed.get("rigid_groups", []):
            ops.append(Op("CREATE", "RigidGroup", g["id"], {
                "body": g["body"], "members": g.get("members", []),
                "is_default": g.get("is_default", True)}, prov))
        for j in parsed.get("joints", []):
            # `frame_ids` is REQUIRED and no longer defaulted. It used to fall
            # back to [], which produced a joint whose axis_direction was
            # declared spatial "in frame Joint.frame_ids" while naming no frame -
            # a unit vector expressed in nothing. An omitted frame now fails at
            # the write boundary instead of being synthesised here.
            fields = {"joint_type": j["joint_type"], "parent_group": j["parent_group"],
                      "child_group": j["child_group"], "dof": j.get("dof", []),
                      "axis_direction": j["axis_direction"],
                      "frame_ids": j.get("frame_ids")}
            # THE COMPLIANT VARIANT IS FLAT, because that is what the contract
            # declares. The prompt asked for a nested `compliance {...}` object
            # and this passed it straight through, so every COMPLIANT joint the
            # model produced was rejected for eight missing fields that were
            # present all along, one level down. `allowable_travel_status` was
            # the second half of the same divergence: the contract's field is
            # `allowable_travel`, and it holds a STATUS - the contract says it
            # "is a material fact whose status is UNSUPPORTED until a compliance
            # route exists", so the honest value is that status, never a number
            # invented to look settled.
            for name in COMPLIANT_FIELDS:
                if j.get(name) is not None:
                    fields[name] = j[name]
            ops.append(Op("CREATE", "Joint", j["id"], fields, prov))
        for i in parsed.get("interfaces", []):
            ops.append(Op("CREATE", "Interface", i["id"], {
                "bodies": i.get("bodies", []),
                "interaction_kind": i["interaction_kind"],
                # The canonical field is `nominal`; the prompt now spells it the
                # same way, and `nominal_status` is still read so the recorded
                # corpus keeps replaying.
                #
                # THE DEFAULT IS DELIBERATELY LEFT IN PLACE. It is a genuine
                # hidden default - a parser asserting the interface is at nominal
                # condition whenever the model says nothing - and removing it was
                # tried here: it invalidated every recorded s03a response in the
                # corpus, none of which carries the field, and those recordings
                # are historical evidence rather than something to be rewritten
                # to suit a new rule. It caused none of the live failures this
                # seam closure was opened for, so it is REPORTED and not changed.
                "nominal": i.get("nominal_status", i.get("nominal", "NOMINAL")),
                "addresses_obligations": i.get("addresses_obligations", [])}, prov))
        for c in parsed.get("configurations", []):
            fields = {"name": c["name"], "kind": c.get("kind", "OPERATIONAL"),
                      "bodies_present": c.get("bodies_present", []),
                      "expected_mobility": c.get("expected_mobility", [])}
            # S-6 / U-7 premise. Written only when stated: an empty basis and an
            # absent one are the same claim - nothing is required to differ - and
            # the check that realizes it is conditional on the declaration.
            if c.get("distinguishing_basis"):
                fields["distinguishing_basis"] = c["distinguishing_basis"]
            ops.append(Op("CREATE", "Configuration", c["id"], fields, prov))
        # NO MobilityExpectation. s03a authors TOPOLOGY; the DOF disposition is
        # derived by s03b from the relations it authors, and that is the only
        # live route into this family.
        #
        # Two branches used to stand here - `mobility` in a compact per-DOF form
        # and `dof_dispositions` in a long one - and both took a disposition
        # STRAIGHT FROM THE RESPONSE, premise unexamined. They outlived the
        # prompt that asked for them, so nothing documented them and a stale
        # recording replayed through this pass still created MAINTAINED_BY_CLASS
        # cells: the exact value S-5 exists to remove, arriving by a path S-5 had
        # not looked at. A second producer for one family is not a compatibility
        # convenience, it is a second answer to "what does the design claim about
        # this DOF" - and the older shape could not cite a premise at all.
        # Recordings in that shape are corpus debt (Impl S-9), not a reason to
        # keep a parser alive.
        #
        # NO LoadPath and NO AssemblyStep either, for the same reason and found
        # the same way. S-9's output-semantics scan compared what this class can
        # CREATE against what s03a declares, and these two were produced and
        # undeclared - the identical shape the paragraph above describes, left
        # behind when that clean-up removed only the families it had gone looking
        # for. `load_paths` and `assembly_steps` appear nowhere in this pass's
        # PROMPT: only S03B_PROMPT asks for them, so no live response can carry
        # the keys and no recording in the corpus does. They are declared outputs
        # of s03b, which authors them from the interactions and constraints it
        # has just written - a premise s03a does not have, since it has decided
        # no interaction yet. Parsing them here was a second producer for two
        # more families, silently reachable by a stale recording.
        for f in parsed.get("functional_regions", []):
            ops.append(Op("CREATE", "FunctionalRegion", f["id"], {
                "role": f["role"], "owning_bodies": f.get("owning_bodies", []),
                "required_by_actors": f.get("required_by_actors", []),
                "reach_targets": f.get("reach_targets", [])}, prov))
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u["kept_open_by"],
                "blocks": u.get("blocks", [])}, prov))
        return ops

    # ---------------------------------------------------------- completeness
    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        if not parsed.get("bodies"):
            out.append("no bodies named")
        if not parsed.get("joints"):
            out.append("no joints named")
        if not parsed.get("configurations"):
            out.append("no configurations named")
        for j in parsed.get("joints", []):
            if j.get("joint_type") not in JOINT_TYPES:
                out.append("joint %s has an unknown type %r" % (j.get("id"), j.get("joint_type")))
        for i in parsed.get("interfaces", []):
            if i.get("interaction_kind") not in INTERACTION_KINDS:
                out.append("interface %s is unclassified" % i.get("id"))
        return out


def _render(obj: Any) -> str:
    """Deterministic serialization of a ConsumerView payload.

    The fixed positional slice is GONE. It was semantic selection disguised as
    formatting: `sort_keys=True` fixes the order, so what fell off the end was
    whatever the alphabet put last, and it went without a word. Budget pressure is
    handled semantically by ConsumerView before anything is rendered, and a budget
    that cannot hold the required minimum is a recorded condition, not a cut.
    """
    import json
    try:
        return json.dumps(obj, indent=1, sort_keys=True)
    except Exception:                                                # noqa: BLE001
        return str(obj)


# =========================================================================
# checks
# =========================================================================
def dof_totality_check(state) -> List[str]:
    """BOOKKEEPING. Every rigid group, in every configuration, has every DOF
    dispositioned exactly once.

    This tests what the enumerator guarantees, so it can never be evidence about
    the design - it is reported as bookkeeping and contributes to no establishment
    claim. Making it branch-safe does not change that: it still asks whether the
    cells the producer was supposed to make exist, which is a question about this
    code. The engineering quantity is DISPOSITION COMPLETENESS: how much of the
    domain rests on evidence, and which cells do not. `disposition_completeness`
    below reports that.

    BOTH SIDES ARE CURRENT, and that is the point. The domain is
    `current_dof_domain` - standing topology, branch union - and the coverage is
    `current_mobility_cells` - standing grids only. Mixing the two currentness
    rules is how this check kept being wrong in a new way each time: history
    could enlarge the domain, or a withdrawn grid could satisfy it, and either
    one makes the report describe a design that is not the one in front of you.

    It still catches a REAL omission: a standing group with no cells in its own
    branch's standing configurations is missing them, and that is exactly what
    the current domain asks about.
    """
    domain = current_dof_domain(state)
    if not domain:
        return ["DOF_DOMAIN_EMPTY: %d standing groups, %d standing configurations"
                % (len(state.standing("RigidGroup")),
                   len(state.standing("Configuration")))]
    in_domain = set(domain)
    seen: Dict[Tuple[str, str, str], int] = {}
    for d in current_mobility_cells(state):
        key = (d.get("rigid_group"), d.get("configuration"), d.get("dof"))
        seen[key] = seen.get(key, 0) + 1
    problems = []
    missing = [k for k in domain if k not in seen]
    for k in missing[:12]:
        problems.append("DOF_NOT_DISPOSITIONED: %s in %s: %s" % k)
    if len(missing) > 12:
        problems.append("DOF_NOT_DISPOSITIONED: and %d more" % (len(missing) - 12))
    for k, n in sorted(seen.items()):
        if n > 1:
            problems.append("DOF_DISPOSITIONED_TWICE: %s in %s: %s" % k)
        if k not in in_domain:
            problems.append("DOF_DISPOSITION_OUT_OF_DOMAIN: %s" % (k,))
    return problems


def assembly_order_problems(steps: Dict[str, Dict[str, Any]]) -> List[str]:
    """Cycles, unknown dependencies, and an order that contradicts one.

    EXTRACTED at S7-B from `assembly_acyclic_check`, which keeps its exact
    findings and its exact strings. The structural question - can this be built
    in the order it claims - is asked by the check over accumulated state and by
    the feasibility evaluator over one candidate's view, and two walks of the
    same graph would be two answers.
    """
    problems: List[str] = []
    colour: Dict[str, int] = {}

    def visit(node: str, trail: List[str]) -> None:
        if colour.get(node) == 2:
            return
        if colour.get(node) == 1:
            problems.append("ASSEMBLY_CYCLE: %s" % " -> ".join(trail + [node]))
            return
        colour[node] = 1
        for dep in steps.get(node, {}).get("depends_on", []) or []:
            if dep in steps:
                visit(dep, trail + [node])
        colour[node] = 2

    for sid in steps:
        visit(sid, [])
    for sid, step in steps.items():
        for dep in step.get("depends_on", []) or []:
            if dep not in steps:
                problems.append("ASSEMBLY_DEP_UNKNOWN: %s -> %s" % (sid, dep))
            elif steps[dep].get("order_index") is not None and step.get("order_index") is not None:
                if steps[dep]["order_index"] >= step["order_index"]:
                    problems.append("ASSEMBLY_ORDER_CONTRADICTS_DEPENDENCY: %s before %s"
                                    % (sid, dep))
    return problems


def assembly_acyclic_check(state) -> List[str]:
    """S03-C4. The assembly precedence relation is acyclic, and its order is a
    linear extension of it."""
    return assembly_order_problems(
        {s["entity_id"]: s for s in state.family("AssemblyStep")})


def load_path_check(state) -> List[str]:
    """S03-C5. Every LoadCase has a path that reaches its declared reaction site,
    and every hop is a real entity."""
    # An Interface is a legitimate hop: a load crosses an interface on its way
    # from one body to the next, and excluding it produced 31 findings that were
    # all describing correct paths.
    known = ({b["entity_id"] for b in state.family("Body")}
             | {j["entity_id"] for j in state.family("Joint")}
             | {g["entity_id"] for g in state.family("RigidGroup")}
             | {i["entity_id"] for i in state.family("Interface")})
    paths = state.family("LoadPath")
    problems = []
    served = {p.get("load_case") for p in paths}
    for l in state.family("LoadCase"):
        if l["entity_id"] not in served:
            problems.append("LOADCASE_WITHOUT_PATH: %s" % l["entity_id"])
    for p in paths:
        hops = p.get("ordered_hops") or []
        if len(hops) < 2:
            problems.append("LOADPATH_TOO_SHORT: %s has %d hop(s); a path needs an "
                            "application point and a reaction" % (p["entity_id"], len(hops)))
        for h in hops:
            if isinstance(h, str) and known and h not in known:
                problems.append("LOADPATH_HOP_UNKNOWN: %s -> %s" % (p["entity_id"], h))
    return problems


def interface_classification_check(state) -> List[str]:
    """S03-C6. Every interface is classified, and every body pair that a joint
    connects has an interface. A meeting region left unclassified is a hole."""
    problems = []
    for i in state.family("Interface"):
        if i.get("interaction_kind") not in INTERACTION_KINDS:
            problems.append("INTERFACE_UNCLASSIFIED: %s -> %r"
                            % (i["entity_id"], i.get("interaction_kind")))
    group_body = {g["entity_id"]: g.get("body") for g in state.family("RigidGroup")}
    pairs: Set[frozenset] = set()
    for i in state.family("Interface"):
        b = [x for x in (i.get("bodies") or []) if isinstance(x, str)]
        if len(b) >= 2:
            pairs.add(frozenset(b[:2]))
    for j in state.family("Joint"):
        pb, cb = group_body.get(j.get("parent_group")), group_body.get(j.get("child_group"))
        if pb and cb and pb != cb and frozenset((pb, cb)) not in pairs:
            problems.append("JOINED_BODIES_WITHOUT_INTERFACE: %s connects %s and %s"
                            % (j["entity_id"], pb, cb))
    return problems


def retention_check(state) -> List[str]:
    """S03-C8. Every body that must stay put declares one of exactly three
    retention terminations.

    A rigid part installed by one straight translation always leaves the reverse
    direction open, so retention is never free: it is covered by a later body,
    or reached by rotation, or held elastically.

    NONE IS THE FOURTH VALUE AND IT IS NOT A STRATEGY. It is the honest answer
    for a body nothing holds - a part that is meant to come back out, or one
    whose retention no configuration depends on - and the permitted-value set
    needs it, because the alternative is a model choosing between inventing a
    strategy and dropping a required field. What it may not do is answer THIS
    question. This check used to test the field for truthiness, so "NONE" - a
    non-empty string - satisfied the very check that exists to ask how a retained
    body is held, and a design could declare that nothing retains a part it also
    declares is retained.
    """
    problems = []
    for s in state.family("AssemblyStep"):
        if s.get("path_kind") not in PATH_KINDS:
            problems.append("ASSEMBLY_BAD_PATH_KIND: %s -> %r"
                            % (s["entity_id"], s.get("path_kind")))
        strategy = s.get("termination_strategy")
        if strategy and strategy not in TERMINATION_STRATEGIES:
            problems.append("RETENTION_UNKNOWN_STRATEGY: %s -> %r" % (s["entity_id"], strategy))
    # A body whose removal is blocked somewhere must say how it is retained.
    retained: Set[str] = set()
    for mex in state.family("MobilityExpectation"):
        for d in mex.get("dispositions", []):
            if isinstance(d, dict) and d.get("disposition") == "BLOCKED_BY":
                retained.add(d.get("rigid_group"))
    group_body = {g["entity_id"]: g.get("body") for g in state.family("RigidGroup")}
    declared = {s.get("body"): s.get("termination_strategy") for s in state.family("AssemblyStep")}
    for g in sorted(retained):
        body = group_body.get(g)
        if not body:
            continue
        if body not in declared:
            problems.append(
                "RETAINED_BODY_WITHOUT_ASSEMBLY_STEP: %s is held in place by a "
                "constraint relation and no assembly step installs it, so the "
                "design never says how it is retained" % body)
            continue
        if str(declared[body] or "").strip().upper() in ("", "NONE"):
            problems.append(
                "RETAINED_BODY_WITHOUT_TERMINATION: %s is held in place by a "
                "constraint relation and declares termination_strategy=%r; NONE "
                "and absence are the same answer here, and neither says what "
                "holds it" % (body, declared[body]))
    return problems


def no_magnitude_check(state) -> List[str]:
    """No metric magnitude and no axis placement exists at s03.

    The failure this prevents is a number that looks authoritative arriving one
    stage before anything could have established it.
    """
    import json
    problems = []
    for family in ("Body", "RigidGroup", "Joint", "Interface", "Configuration",
                   "LoadPath", "AssemblyStep", "FunctionalRegion"):
        for e in state.family(family):
            blob = json.dumps(e)
            for m in _MAGNITUDE.finditer(blob):
                problems.append("MAGNITUDE_AT_S03: %s -> %r" % (e["entity_id"], m.group(0)))
                break
    return problems


def obligation_ownership_check(state) -> List[str]:
    """S03-C7. Every obligation satisfiable at s03 is claimed by something in the
    mechanism.

    Rewritten in Window 2. The previous version searched a JSON blob for the
    obligation id, which no response could ever satisfy because the response
    schema had no field in which to cite one: 48 findings, 0 true positives. A
    check that cannot be passed measures nothing. Bodies, interfaces and joints
    now carry `addresses_obligations`, so the property is expressible, and this
    check reads that field.
    """
    claimed: Set[str] = set()
    for family in ("Body", "Interface", "Joint", "FunctionalRegion", "AssemblyStep"):
        for e in state.family(family):
            for o in (e.get("addresses_obligations") or []):
                if isinstance(o, str):
                    claimed.add(o)
    problems = []
    for o in state.family("Obligation"):
        if o.get("satisfiable_at") != "s03":
            continue
        if o["entity_id"] not in claimed:
            problems.append("OBLIGATION_UNCLAIMED_AT_S03: %s (%s)"
                            % (o["entity_id"], str(o.get("statement", ""))[:70]))
    return problems


def functional_region_check(state) -> List[str]:
    """S03-C12. Every functional region has a role and at least one owning body."""
    bodies = {b["entity_id"] for b in state.family("Body")}
    problems = []
    for f in state.family("FunctionalRegion"):
        if f.get("role") not in REGION_ROLES:
            problems.append("REGION_BAD_ROLE: %s -> %r" % (f["entity_id"], f.get("role")))
        owners = [b for b in (f.get("owning_bodies") or []) if isinstance(b, str)]
        if not owners:
            problems.append("REGION_WITHOUT_OWNER: %s" % f["entity_id"])
        for b in owners:
            if bodies and b not in bodies:
                problems.append("REGION_OWNER_UNKNOWN: %s -> %s" % (f["entity_id"], b))
    return problems


def compliance_check(state) -> List[str]:
    """S03-C9. Every compliant joint declares the eight fields, and never
    collapses required_travel and allowable_travel into one number.

    required_travel is kinematic and follows from the mechanism. allowable_travel
    is a material fact this pipeline has no route to establish, so it carries a
    status instead of a value. One number for both would assert the material fact.
    """
    # THE FIELD SET COMES FROM THE CONTRACT, not from a list kept here. This
    # checker held its own copy and went stale: it read a nested `compliance`
    # object and `allowable_travel_status`, both of which the seam retired, so
    # it would have reported COMPLIANT_JOINT_WITHOUT_COMPLIANCE_BLOCK for every
    # correctly-authored joint - a check failing on exactly the shape it exists
    # to require. A third hand-written spelling of one variant is what the
    # producer stopped keeping, and this stops keeping it too.
    problems = []
    for j in state.family("Joint"):
        if j.get("joint_type") != "COMPLIANT":
            continue
        if j.get("compliance") is not None:
            problems.append(
                "COMPLIANCE_NESTED_BLOCK: %s carries a `compliance` object; the "
                "canonical variant is flat fields on the joint" % j["entity_id"])
        for field in COMPLIANT_FIELDS:
            if not str(j.get(field) or "").strip():
                problems.append("COMPLIANCE_INCOMPLETE: %s missing %s"
                                % (j["entity_id"], field))
        if j.get("actuation") and j["actuation"] != "PRESCRIBED_KINEMATIC":
            problems.append("COMPLIANCE_ACTUATION_NOT_DECLARED_PRESCRIBED: %s -> %r"
                            % (j["entity_id"], j["actuation"]))
    return problems


def simulation_completeness_check(state) -> List[str]:
    """S03-C10. The joint graph can be projected into a multibody model without
    re-derivation: every joint resolves to two existing groups, every group to a
    body, and the graph is connected."""
    groups = {g["entity_id"] for g in state.family("RigidGroup")}
    bodies = {b["entity_id"] for b in state.family("Body")}
    problems = []
    for g in state.family("RigidGroup"):
        if g.get("body") not in bodies:
            problems.append("GROUP_WITHOUT_BODY: %s -> %r" % (g["entity_id"], g.get("body")))
    adjacency: Dict[str, Set[str]] = {g: set() for g in groups}
    for j in state.family("Joint"):
        p, c = j.get("parent_group"), j.get("child_group")
        for endpoint in (p, c):
            if endpoint not in groups:
                problems.append("JOINT_ENDPOINT_UNKNOWN: %s -> %r" % (j["entity_id"], endpoint))
        if j.get("axis_direction") not in AXIS_DIRECTIONS:
            problems.append("JOINT_BAD_AXIS_DIRECTION: %s -> %r"
                            % (j["entity_id"], j.get("axis_direction")))
        if p in adjacency and c in adjacency:
            adjacency[p].add(c)
            adjacency[c].add(p)
    if groups:
        seen, stack = set(), [sorted(groups)[0]]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(adjacency.get(n, ()))
        stranded = sorted(groups - seen)
        if stranded:
            problems.append("JOINT_GRAPH_DISCONNECTED: %s not reachable"
                            % ", ".join(stranded[:6]))
    return problems


def no_selection_check_s03(state) -> List[str]:
    """INV-007 still holds here: s03 embodies a candidate, it does not choose one."""
    import json
    blob = json.dumps([e for f in ("Body", "Joint", "Configuration", "LoadPath")
                       for e in state.family(f)]).lower()
    return ["SELECTION_AT_S03: %r" % p for p in
            ('"selected', '"winner', '"score', '"rank', '"best_') if p in blob]


# =========================================================================
# s03 pass B
# =========================================================================

S03B_PROMPT = """The mechanism below is fixed. Add what holds it together, how
loads reach the world, and in what order it goes together.

Do not add or rename bodies, groups, joints, interfaces or configurations. If
something is missing, say so in unresolved.

1. WHAT HOLDS EACH BODY. For each body that must stay where it is put, state
   what stops it, as a constraint_relation below. ONE relation per (retained
   group, blocked direction) - not one per degree of freedom: the pipeline
   expands each relation over the DOFs and the CONFIGURATIONS THE RELATION
   ITSELF NAMES, and over no others. A relation that names no configuration
   therefore holds nowhere, so name them. A mechanism in which nothing is blocked
   is a pile of loose parts.
2. IRRELEVANCE. Only for a DOF that is BOTH unloaded AND unactuated, naming the
   scenario in which that holds. The scenario is an ID from the input, not a
   description; a scenario carrying a load case is not one. Most mechanisms need
   none.
3. LOAD PATHS. Per load case, the ordered hops from where the load is applied,
   through this mechanism, to the reaction site. A HOP IS AN INTERFACE ID - the
   interface that carries the load across that step. Not a body, not a joint: a
   body is what the load passes through, an interface is what carries it from
   one body to the next. Terminate at the reaction site the load case names, and
   if this mechanism does not reach it, leave terminates_at out and say so.
   Never say how much load anything carries.
4. ASSEMBLY ORDER. Which body, from which access side, what it depends on, and
   what retains it once placed. A rigid part pushed straight in leaves the
   reverse direction open, so a body that must stay put needs LATER_BODY_COVER,
   ROTATION or ELASTICITY. NONE is the fourth value and it is not a strategy: it
   says nothing retains this body, which is the right answer for a part that is
   meant to come back out or that no constraint relation holds, and is not an
   answer for a body you have just declared a constraint_relation retains. Every
   body whose group appears as a `retained_group` above needs one of the three.

RESPONSE SCHEMA
Return one JSON object. Emit every key. Use exactly these key names.

  irrelevance[]         rigid_group, configuration, dof[], scenario
  physical_interactions[]
                        id "PHI-0001", groups[], effect, discharges_effect,
                        at_interface (optional), configurations[] (optional)
  transition_requirements[]
                        id "TRQ-0001", from_configuration, to_configuration,
                        required_relative_motions[] {{joint, dof}},
                        released_constraints[]
                        WHAT STATE CHANGE MUST BE POSSIBLE. See THE STATE MACHINE
                        below. [] is a real answer for a mechanism with one
                        configuration and nowhere to go.
  constraint_relations[]
                        id "CRL-0001", retained_group, blocked_dofs[],
                        configurations[], driver, blocked_direction (optional),
                        blocked_relative_motions[] {{joint, dof}} (optional),
                        provider_body (optional),
                        provider_reaction_site (optional),
                        provider_site (optional),
                        maintaining_interaction (optional),
                        defeat_specification (optional)
                        AT LEAST ONE of provider_body / provider_reaction_site
                        must identify what provides the constraint.
                        provider_site is where it acts and does not answer that.
  load_paths[]          id "LDP-0001", load_case, ordered_hops[],
                        terminates_at (optional)
                        The candidate is NOT yours to state: this pass is run
                        once per candidate and the one you are embodying is
                        named above, so the path is written against it.
  assembly_steps[]      id "ASY-0001", order_index, body, access_side,
                        activates[], termination_strategy, path_kind, depends_on[]
  unresolved[]          id "S3U-1001", decision, why_open, alternatives[],
                        alternatives_kind, kept_open_by[], blocks[]

  blocked_direction     {axis_directions}
  provider_body         a body id, not a description
  configurations        configuration ids where the relation holds
  blocked_dofs          which of {dofs} the relation removes
  driver                {drivers}
  defeat_specification  how a test would defeat this constraint
  termination_strategy  {terminations}
  path_kind             {path_kinds}
  alternatives_kind     ENTITY_REFS | PRINCIPLE_FAMILIES | FREE_TEXT

PHYSICAL REALIZATION
This candidate must physically do what the input's PHYSICAL EFFECT OBLIGATIONS
require. Those obligations are candidate-independent: they say WHAT effect must
occur, between which roles. You say HOW THIS CANDIDATE does it.

  For every effect obligation this candidate realizes, emit a
  physical_interaction naming the rigid groups between which the effect passes,
  the effect ({effects}), and the obligation id it discharges. An interaction
  TRANSMITS; a joint CONSTRAINS. They are not the same fact and a joint is not a
  substitute for one.

  For every constraint this candidate relies on, emit a constraint_relation: the
  retained group, which DOFs it removes, in which configurations, and what
  DRIVES it ({drivers}). Name what PROVIDES it - a body of this mechanism in
  provider_body, or, where the reaction is taken outside the product, the
  declared reaction site in provider_reaction_site. Those are the two kinds of
  provider there are; the world is not a body. provider_site is a different
  fact: the interface of this mechanism at which the constraint acts. Do not
  leave a constraint standing on nothing, and do not report one you have not
  decided.

  For every load case, emit a load_path: the ordered interfaces the load passes
  through, and where it terminates. If the load reaches a declared EXTERNAL
  reaction site, name it in terminates_at. If it does not, leave terminates_at
  out - an open path is a real answer and saying so is better than closing it
  with something you did not establish.

THE STATE MACHINE
A mechanism whose configurations are each well held and none reachable from any
other is a solid object. Say which changes of state the design must be CAPABLE
of, and what each one needs.

  DIRECTED. A -> B is not B -> A. A lid that closes and cannot be reopened
  satisfies one and fails the other, so write each direction you require and do
  not add the reverse because you wrote the forward.

  NOT A COMPLETE GRAPH. Write the transitions the design actually requires.
  Every pair of configurations connected in both directions is a claim about the
  product that nothing asked for.

  ADJACENCY IS NOT IN distinguishing_basis. That field says two configurations
  DIFFER in some named joint coordinate. It does not say either can be reached
  from the other, and it does not say that DOF is free in either of them - a
  latched lid and an open one differ in a hinge coordinate that is restrained in
  both, which is what makes them states rather than positions.

  RELATIVE MOTION. `required_relative_motions` names a JOINT and one of its
  degrees of freedom: the two sides of that joint move relative to each other.
  It does not say which body travels in the world, and nothing here should be
  read as naming a moving part.

  A LOCKED SOURCE IS NORMAL. A configuration whose DOF are BLOCKED_BY is a stable
  state, and leaving it is what a latch, a detent or a catch is for. If leaving
  the source requires defeating a restraint, name that relation in
  `released_constraints` - that is the whole point of the field, not an admission
  of contradiction.

  THE DESTINATION MAY RE-LOCK. Arriving in a state that re-establishes a
  restraint is normal and is not a contradiction with the transition you just
  wrote.

  A relation you name in `released_constraints` must say WHICH relative motion it
  restrains, through its own `blocked_relative_motions`. Otherwise nothing
  downstream can tell why releasing it matters.

WHEN A RESTRAINT NAMES THE MOTION IT REMOVES
`constraint_relations[].blocked_relative_motions` is optional and is a
STATEMENT, not a derivation. Write an entry only where the relation explicitly
restrains that joint-relative DOF. Do not produce one by matching
`retained_group` against a joint's parent or child group, by parent/child
ordering, or from body or configuration names: which side of a joint a held
group happens to be is not what the relation says.

IT ADDS TO `blocked_dofs`; IT DOES NOT REPLACE IT. The two answer different
questions and a relation that restrains anything needs both:

  blocked_dofs                 which DOF of the RETAINED GROUP this relation
                               removes, in the configurations it names. This is
                               what the mobility of each configuration is
                               expanded from, so a relation that leaves it empty
                               removes nothing anywhere and disposes no cell.
  blocked_relative_motions     which relative JOINT motion that same restraint
                               corresponds to, where you know the correspondence.
                               Additional information about the same relation,
                               and never a substitute for the line above.

Fill in `blocked_dofs` for every relation that restrains group mobility, exactly
as before. Add `blocked_relative_motions` on top of it when you can say which
joint-relative motion it is. Neither is computed from the other, by you or by
anything downstream.

`configurations` is the complete list of where a relation holds. An empty list
means it holds NOWHERE - it is not shorthand for "everywhere" - so a relation you
mean to be active must name the configurations it is active in.

{references}

An interaction you describe instead of emitting does not exist.

Ids you emit are new. Never reuse an id from the input.

THE CANDIDATE YOU ARE EMBODYING
{candidate}

TYPED INPUT
-----------
{mechanism}
"""


#: Reference-valued fields the PIPELINE fills in, so the model is not asked for
#: them. `LoadPath.candidate` is the invocation's own candidate: this pass runs
#: once per candidate, so a model restating it can only agree or be wrong.
#: Listed rather than inferred, because "the producer supplies this" is a fact
#: about the producer, and the standing test requires every contract-declared
#: reference to be either PROMPTED or named here.
PIPELINE_SUPPLIED_REFERENCES = (("LoadPath", "candidate"),)


#: Which response key carries which family, for every family this responsibility
#: is permitted to output. The prompt speaks in response keys and the contract
#: speaks in families, so one of the two has to say how they correspond.
#:
#: `None` means THE MODEL IS NOT ASKED: MobilityExpectation is a declared s03b
#: output that `derived_operations` computes from the relations the model writes,
#: so asking about its references would be asking for a value the model does not
#: supply. It is listed rather than omitted because a declared output family that
#: appears nowhere here raises instead of being silently dropped from the prompt,
#: which is the failure the whole section exists to end.
RESPONSE_KEY_OF = {"PhysicalInteraction": "physical_interactions",
                   "ConstraintRelation": "constraint_relations",
                   "LoadPath": "load_paths", "AssemblyStep": "assembly_steps",
                   "UnresolvedDecision": "unresolved",
                   "TransitionRequirement": "transition_requirements",
                   "MobilityExpectation": None}


def _output_families(responsibility_id: str = "s03b") -> Tuple[str, ...]:
    """The families this responsibility may author, read from the contract."""
    import yaml as _yaml
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "..", "contracts",
                        "STAGE_RESPONSIBILITY_CONTRACT.yaml")
    with open(os.path.abspath(path)) as fh:
        doc = _yaml.safe_load(fh)
    declared = (doc["stages"][responsibility_id].get("permitted_output_semantics")
                or [])
    missing = [f for f in declared if f not in RESPONSE_KEY_OF]
    if missing:
        raise KeyError(
            "%s declares output families %s and RESPONSE_KEY_OF does not say "
            "which response key carries them, or that the pipeline authors them"
            % (responsibility_id, missing))
    return tuple(f for f in declared if RESPONSE_KEY_OF[f])


def reference_rules(responsibility_id: str = "s03b") -> List[Dict[str, Any]]:
    """Every reference-valued field of every family this pass authors.

    THE ONE ENUMERATION. Read from the contract, so a field added there appears
    here without anyone remembering; a field that changes target, cardinality or
    conditionality changes here for the same reason.

    Three kinds of declaration are carried, because the contract has three and
    the difference is what a model needs to be told:

      reference    `field_semantics` says the field IS a reference and to what.
                   `target` may be one family, a list of families, or ANY - and
                   ANY is not "anything", it is "any entity this design has",
                   which still forbids prose.
      conditional  `conditional_references` says the field is a reference only
                   when a sibling field says so - `alternatives` holds ids when
                   `alternatives_kind` is ENTITY_REFS and holds no ids otherwise.
                   A model told the field is "a list" writes prose into it, which
                   is exactly what the live sweep recorded.
      supplied     the pipeline fills it, so it is not asked for at all.

    Sorted, so the rendered block is stable and a diff means a contract change.
    """
    contracts = _contracts()
    families = _output_families(responsibility_id)
    supplied = set(PIPELINE_SUPPLIED_REFERENCES)
    rows: List[Dict[str, Any]] = []
    for family in families:
        spec = contracts.families.get(family) or {}
        for field, decl in sorted((spec.get("field_semantics") or {}).items()):
            if not isinstance(decl, dict) or decl.get("kind") != "reference":
                continue
            if (family, field) in supplied:
                continue
            target = decl.get("target")
            rows.append({
                "family": family, "field": field, "kind": "reference",
                "targets": ("ANY" if target == "ANY" else
                            list(target) if isinstance(target, list) else [target]),
                "cardinality": decl.get("cardinality", "one"),
                "resolvable": bool(decl.get("resolvable", False)),
                "population": decl.get("referent_population") or _branch_population(),
                "when": None})
        # NESTED REFERENCES ARE REFERENCES. A row of `{joint, dof}` inside a
        # record list carries an id the write boundary resolves and a value it
        # checks against a closed set, and a model told only that the field is
        # "a list of entries" has been told neither. Same descent the canonical
        # graph makes, for the same reason.
        for field, decl in sorted((spec.get("field_semantics") or {}).items()):
            if not isinstance(decl, dict) or decl.get("kind") != "record_list":
                continue
            if (family, field) in supplied:
                continue
            for name, sub in sorted((decl.get("record_field_semantics") or {}).items()):
                if not isinstance(sub, dict):
                    continue
                if sub.get("kind") == "reference":
                    target = sub.get("target")
                    rows.append({
                        "family": family, "field": "%s[].%s" % (field, name),
                        "kind": "reference",
                        "targets": ("ANY" if target == "ANY" else
                                    list(target) if isinstance(target, list)
                                    else [target]),
                        "cardinality": sub.get("cardinality", "one"),
                        "resolvable": bool(sub.get("resolvable", False)),
                        "population": (sub.get("referent_population")
                                       or _branch_population()),
                        "when": None})
                elif sub.get("values"):
                    rows.append({
                        "family": family, "field": "%s[].%s" % (field, name),
                        "kind": "vocabulary", "targets": [],
                        "values": list(sub["values"]), "cardinality": "one",
                        "resolvable": False,
                        "population": _branch_population(), "when": None})
        for rule in contracts.conditional_references(family):
            field = rule.get("field")
            if (family, field) in supplied:
                continue
            target = rule.get("target")
            rows.append({
                "family": family, "field": field, "kind": "conditional",
                "targets": ("ANY" if target in (None, "ANY") else
                            list(target) if isinstance(target, list) else [target]),
                "cardinality": rule.get("cardinality", "many"),
                "resolvable": bool(rule.get("resolvable", False)),
                "population": rule.get("referent_population") or _branch_population(),
                "when": dict(rule.get("applies_when") or {})})
    return sorted(rows, key=lambda r: (r["family"], r["field"]))


def render_reference_rules(rows: Optional[List[Dict[str, Any]]] = None) -> str:
    """The prompt's reference section, generated from `reference_rules`.

    WRITTEN BY THE CONTRACT, not by hand. The live s03b sweep failed 6/6 on
    reference typing alone: `depends_on` named bodies, `activates` named joints,
    `maintaining_interaction` named an interface because the name reads like one,
    and `kept_open_by`, `blocks` and `alternatives` held prose. The prompt named
    each of those fields exactly once, in the schema line, and never said what it
    points at - so nothing the model could read told it. s03a carries the same
    section and its sweep was accepted 6/6.

    Generated rather than written so a field added to the contract cannot be
    silently missing from it, which is the failure this section exists to end.
    """
    rows = reference_rules() if rows is None else rows
    out = ["REFERENCES BETWEEN ITEMS",
           "Every field below holds ENTITY IDS and nothing else. A description is",
           "not an id: prose in one of these fields names no entity and is refused.",
           "An id is either one from the TYPED INPUT below or one you create in this",
           "same response, and it must be of the family named here - a body id where",
           "a step is required denotes the wrong thing, however sensible it reads.",
           ""]
    import textwrap as _tw
    for r in rows:
        key = RESPONSE_KEY_OF.get(r["family"], r["family"])
        name = "%s[].%s" % (key, r["field"])
        if r.get("kind") == "vocabulary":
            what = ("exactly one of %s, and nothing else"
                    % " | ".join(r.get("values") or []))
        elif r["targets"] == "ANY":
            what = ("any entity id this design has - the field is deliberately "
                    "not restricted to one family, and prose is still refused")
        else:
            plural = "s" if r["cardinality"] == "many" else ""
            what = "%s id%s" % (" or ".join(r["targets"]), plural)
            if len(r["targets"]) > 1:
                what += " - either family, and nothing else"
        if (r.get("kind") != "vocabulary" and r["cardinality"] == "many"
                and r["targets"] != "ANY"):
            what += "; [] when there are none"
        if r["when"]:
            when = r["when"]
            what = ("ONLY when %s is %s: %s. Otherwise this field holds no ids at "
                    "all and nothing here applies to it"
                    % (when.get("field"), when.get("equals"), what))
        # THE FIELD ON ITS OWN LINE. A two-column layout with names this long
        # leaves a 25-character description column, and ragged text is the part
        # a reader skips.
        out.append("  " + name)
        out.extend("      " + line for line in _tw.wrap(what, width=74) or [""])
    return "\n".join(out)


def _motions(entries) -> Set[Tuple[str, str]]:
    """(joint, dof) pairs from a typed motion list. The ONE matching key.

    Every rule below compares a required motion against a restrained one through
    these pairs, and through nothing else. Matching by `retained_group` against a
    joint's parent or child would read a relative orientation as an absolute one:
    which side of a joint the held group happens to be says nothing about which
    relative motion the relation removes, so reversing a joint's parent and child
    must not change any answer here.
    """
    out: Set[Tuple[str, str]] = set()
    for row in (entries or []):
        if not isinstance(row, dict):
            continue
        joint, dof = row.get("joint"), row.get("dof")
        if isinstance(joint, str) and joint and dof in DOF_NAMES:
            out.add((joint, dof))
    return out


def _configurations(relation) -> Set[str]:
    return {c for c in (relation.get("configurations") or []) if isinstance(c, str)}


def _active_in(relation, configuration: str) -> bool:
    """Whether a restraint holds in ONE configuration. The contract's own rule.

    A relation "holds where it says it holds": `configurations` is the complete
    list, so an EMPTY list means it holds NOWHERE - the same reading `s03b`
    already reports as evidence that disposes nothing, and the same one
    `derive_mobility` applies when it expands a relation over the configurations
    it declares. Treating empty as "everywhere" would turn an author's silence
    into the widest possible claim, which is the defect that reading exists to
    prevent, and it would make a relation that restrains nothing block every
    transition in the design.
    """
    return configuration in _configurations(relation)


def transition_consistency(requirements, relations, joints) -> List[str]:
    """What the authored state machine says about itself, and where it disagrees.

    TYPED ENTITIES ONLY. Requirements, relations and joints as they were written;
    no group naming, no parent/child ordering, no configuration names, and no
    inference from `distinguishing_basis`.

    THE FINDINGS ARE NOT ONE KIND. A required motion the joint does not have, and
    a required motion an active restraint removes that nothing releases, are
    CONTRADICTIONS: the design says two things that cannot both hold. A release
    whose relation states no defeat specification is INCOMPLETENESS: the design
    may well be right and has not said how the release is achieved. Reported
    separately because deciding what they cost a candidate is feasibility's
    question, not this pass's - which is also why nothing here deletes or
    rewrites a requirement that produces one.
    """
    by_joint = {j.get("entity_id"): j for j in (joints or [])
                if isinstance(j, dict)}
    by_relation = {r.get("id") or r.get("entity_id"): r for r in (relations or [])
                   if isinstance(r, dict)}
    out: List[str] = []
    for req in (requirements or []):
        if not isinstance(req, dict):
            continue
        rid = req.get("id") or req.get("entity_id")
        source = req.get("from_configuration")
        required = _motions(req.get("required_relative_motions"))
        released = [r for r in (req.get("released_constraints") or [])
                    if isinstance(r, str)]

        # A. the joint has to have the freedom the transition needs
        for joint, dof in sorted(required):
            declared = by_joint.get(joint)
            if declared is None:
                continue                      # a reference the boundary refuses
            if dof not in set(declared.get("dof") or []):
                out.append("TRANSITION_DOF_NOT_SUPPORTED: %s requires %s/%s and "
                           "that joint declares %s"
                           % (rid, joint, dof,
                              sorted(declared.get("dof") or []) or "no free DOF"))

        for name in released:
            relation = by_relation.get(name)
            if relation is None:
                continue
            # B. a release only means something where the restraint is active
            if source and not _active_in(relation, source):
                out.append("RELEASE_NOT_ACTIVE_AT_SOURCE: %s releases %s, which "
                           "holds in %s and not in %s"
                           % (rid, name,
                              ", ".join(sorted(_configurations(relation)))
                              or "no configuration", source))
            # C. and only where it restrains something the transition needs.
            #    ABSENT AND DISJOINT ARE DIFFERENT ANSWERS. A relation that has
            #    not said which relative motion it removes has not said why
            #    releasing it matters - which is incompleteness, and reading it
            #    as "restrains nothing relevant" would be inventing the answer.
            #    One that HAS said, and named something else, is a mismatch
            #    between two statements that were both made.
            restrained = _motions(relation.get("blocked_relative_motions"))
            if not restrained:
                out.append("RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED: %s releases "
                           "%s, and that relation does not say which relative "
                           "joint motion it restrains, so why the release "
                           "matters is not established" % (rid, name))
            elif not (restrained & required):
                out.append("RELEASE_RELATION_NOT_APPLICABLE: %s releases %s, "
                           "which restrains %s and the transition requires %s"
                           % (rid, name,
                              ", ".join("%s/%s" % m for m in sorted(restrained)),
                              ", ".join("%s/%s" % m for m in sorted(required))))
            # E. released, and nothing says how the release is achieved
            if not str(relation.get("defeat_specification") or "").strip():
                out.append("RELEASE_EVIDENCE_NOT_ESTABLISHED: %s releases %s, "
                           "which states no defeat specification, so how the "
                           "release is achieved is not established" % (rid, name))

        # D. an active restraint on a required motion that nothing releases
        for name, relation in sorted(by_relation.items()):
            if name in released:
                continue
            if source and not _active_in(relation, source):
                continue
            blocking = _motions(relation.get("blocked_relative_motions")) & required
            if blocking:
                out.append("UNRELEASED_REQUIRED_MOTION: %s requires %s in %s and "
                           "%s restrains it there without being released"
                           % (rid, ", ".join("%s/%s" % m for m in sorted(blocking)),
                              source, name))
    return out


def legacy_shapes_in_recording(parsed) -> Dict[str, int]:
    """What a RECORDING contains of the shapes this pipeline no longer speaks.

    S-9 corpus information and nothing else: it feeds no derivation, no check and
    no state, and every caller of it writes into a run record. It replaced a
    canonicaliser, an alias table and a per-DOF relation reconstructor that
    existed to make those shapes usable - machinery that is a live compatibility
    path the moment anything downstream reads what it returns. Counting is not a
    path, which is the whole difference.
    """
    return {
        "legacy_blocking_relations": len(parsed.get("blocking_relations") or []),
        "legacy_mobility_rows": len(parsed.get("mobility") or []),
        "legacy_dof_dispositions": len(parsed.get("dof_dispositions") or []),
    }


class S03BMobilityAndAssembly(Stage):
    """The second half of s03: what holds the mechanism, how loads leave it, and
    how it is built. It authors ENGINEERING RELATIONS; the exhaustive DOF grid is
    derived from them by `derive_mobility`, which is the contract's own division
    of labour (LLM role NONE for totality)."""

    stage_id = "s03"
    pass_id = "s03b"
    purpose = "author the blocking relations, load paths and assembly order"

    def prompt(self, inputs):
        return S03B_PROMPT.format(
            axis_directions=" | ".join(AXIS_DIRECTIONS),
            drivers=" | ".join(CONSTRAINT_DRIVERS), dofs=" ".join(DOF_NAMES),
            effects=" | ".join(_EFFECT_KINDS),
            terminations=" | ".join(TERMINATION_STRATEGIES),
            path_kinds=" | ".join(PATH_KINDS),
            # THE CONTRACT'S OWN ANSWER about every reference this pass writes,
            # rendered at prompt time so a contract change reaches the model
            # without anyone editing prose.
            references=render_reference_rules(),
            candidate=_render(inputs.get("candidate") or {}),
            mechanism=_render(inputs["consumer_view"]))

    def invocation_premises(self, inputs):
        """The same candidate, carried on this pass's demands.

        Pass B works out what holds the topology pass A fixed for one candidate.
        Its load paths, assembly order and open decisions are that candidate's,
        for the same reason and with the same consequence under FA-5.
        """
        return _candidate_premise(inputs.get("candidate"))

    def _s4_physical_problems(self, parsed, inputs) -> List[str]:
        """The three U-5 conditions, and only those.

        U5-1  every physical effect obligation is discharged by an authored
              interaction, or explicitly recorded open;
        U5-2  every constraint relation names what PROVIDES it - a body of this
              mechanism or a declared external reaction site. `provider_site` is
              where it acts and does not answer that question;
        U5-3  every load path terminates at the EXTERNAL reaction site its own
              load case names, or is explicitly recorded open.

        It INVENTS NOTHING. An obligation this candidate cannot discharge, a
        constraint it has not decided, a path that reaches nowhere - each is a
        real answer when it is SAID, through `unresolved`. What is not an answer
        is silence.

        Deliberately separate from the mobility layer, which asks a different
        question about the same relations: this one asks whether the physical
        demand was realized, and S-5's asks what the relations dispose. Canonical
        physical truth is ConstraintRelation; the legacy blocking relation was not
        a second version of it and is gone.
        """
        view = inputs.get(self.context_key) or {}
        by_id = {e.get("entity_id"): e
                 for family in view.values() if isinstance(family, list)
                 for e in family if isinstance(e, dict)}
        open_items = {ref for u in parsed.get("unresolved") or []
                      for ref in (u.get("blocks") or [])}
        out: List[str] = []

        # -- U5-1 -----------------------------------------------------
        # DISCHARGE IS A CLAIM ABOUT THE EFFECT, not about the citation. This
        # collected the cited ids and asked nothing else, so an interaction
        # claiming TRANSMIT_FORCE discharged an obligation requiring PERMIT_MOTION
        # by naming it - and the mismatch was found a layer later, by
        # `physical_relation_closure`, which has compared the two all along. The
        # producer now asks the same question the assurance property asks, in the
        # same vocabulary, so the two cannot disagree about what discharge means.
        effects: Dict[str, Set[str]] = {}
        for i in parsed.get("physical_interactions") or []:
            if not isinstance(i, dict):
                continue
            effect, target = i.get("effect"), i.get("discharges_effect")
            if effect not in _EFFECT_KINDS:
                out.append("U5-1 %s produces %r, which is not an effect this "
                           "pipeline has (%s)"
                           % (i.get("id"), effect, ", ".join(_EFFECT_KINDS)))
            if isinstance(target, str):
                effects.setdefault(target, set()).add(effect)
        for demand in view.get("PhysicalEffectObligation") or []:
            eid = demand.get("entity_id")
            if eid in open_items:
                continue
            produced = effects.get(eid)
            if not produced:
                out.append("U5-1 %s is neither discharged by an interaction nor "
                           "recorded open" % eid)
            elif demand.get("effect") not in produced:
                out.append("U5-1 %s requires %r and the interaction(s) citing it "
                           "produce %s; citing an obligation is not discharging "
                           "it" % (eid, demand.get("effect"), sorted(produced)))
        given = {d.get("entity_id") for d in view.get("PhysicalEffectObligation") or []}
        for target in sorted(effects):
            if target not in given:
                out.append("U5-1 an interaction discharges %s, which is no effect "
                           "obligation this consumer was given" % target)

        # -- U5-2 -----------------------------------------------------
        for relation in parsed.get("constraint_relations") or []:
            rid = relation.get("id")
            body = relation.get("provider_body")
            site = relation.get("provider_reaction_site")
            if not body and not site:
                out.append("U5-2 %s names no provider; provider_site says where a "
                           "constraint acts, not what provides it" % rid)
                continue
            if site:
                declared = by_id.get(site)
                if declared is None:
                    out.append("U5-2 %s is provided by %s, which this consumer was "
                               "not given" % (rid, site))
                elif declared.get("boundary_side") != "EXTERNAL":
                    out.append("U5-2 %s takes its reaction at %s, which the scenario "
                               "boundary puts INSIDE the product; an internal site "
                               "provides nothing to react against" % (rid, site))

        # -- U5-3 -----------------------------------------------------
        served = {p.get("load_case") for p in parsed.get("load_paths") or []}
        for load in view.get("LoadCase") or []:
            eid = load.get("entity_id")
            if eid not in served and eid not in open_items:
                out.append("U5-3 %s has neither a load path nor a recorded reason "
                           "it has none" % eid)
        for path in parsed.get("load_paths") or []:
            pid = path.get("id")
            if pid in open_items:
                continue
            terminus = path.get("terminates_at")
            load = by_id.get(path.get("load_case")) or {}
            expected = load.get("reacted_at_site")
            if not terminus:
                out.append("U5-3 %s reaches no reaction site and is not recorded "
                           "open; a path that does not close is an OPEN path, "
                           "which is a finding and not a silence" % pid)
                continue
            declared = by_id.get(terminus)
            if declared is None:
                out.append("U5-3 %s terminates at %s, which this consumer was not "
                           "given" % (pid, terminus))
            elif declared.get("boundary_side") != "EXTERNAL":
                out.append("U5-3 %s terminates at %s, which is INTERNAL; the load "
                           "has not left the product" % (pid, terminus))
            elif expected and terminus != expected:
                out.append("U5-3 %s terminates at %s, but %s is reacted at %s; a "
                           "path that closes somewhere else has not closed this "
                           "load" % (pid, terminus, path.get("load_case"), expected))
        return out

    def _s5_mobility_problems(self, parsed, inputs) -> List[str]:
        """PREMISE MATERIAL that would dispose nothing, and only that.

        Separate from `_s4_physical_problems` because they are different
        questions: S-4 asks whether the physical demand was realized, S-5 asks
        whether what this response offers as mobility evidence can actually reach
        a cell.

        DOMAIN TOTALITY is not checked here. It is guaranteed by the enumerator,
        which makes it bookkeeping - checking what your own code just built is not
        assurance, and the plan says to report it as such rather than count it.

        NOR IS "every disposition cites a resolvable premise" checked here. That
        moved to the write boundary, where `MobilityExpectation.dispositions`
        declares which field carries which disposition's premise and which family
        it must resolve to. A rule enforced in a stage's completeness method binds
        one producer; the same rule at the write boundary binds every producer
        there will ever be, including one written after this file - and an earlier
        version of this method recomputed the grid to check it, which put a second
        derivation of the same fact in the same class as the defect it was
        checking for.

        An UNDISPOSITIONED cell is not an error to be repaired; it is the honest
        state, and reporting how many there are is what `disposition_completeness`
        is for. What IS an error is evidence that silently reaches no cell: a
        relation naming no configuration, an irrelevance claim naming no scenario
        or no DOF. Those look like engineering and dispose nothing.

        REACHING A CELL IS DECIDABLE WITHOUT DERIVING THE GRID, because the grid's
        domain is groups x configurations x DOF and all three are known from the
        view. So this asks membership directly rather than expanding the grid and
        looking - which is the same reason the premise rule moved to the write
        boundary: a check that re-derives what it is checking is in the same class
        as the defect it looks for. The cases it now catches were each silent: a
        relation blocking a DOF this pipeline does not have, a relation holding in
        another candidate's configuration, an irrelevance claim about a group that
        does not exist. Every one of them looked complete and disposed nothing.
        """
        view = inputs.get(self.context_key) or {}
        groups = {g.get("entity_id") for g in view.get("RigidGroup") or []}
        configs = {c.get("entity_id") for c in view.get("Configuration") or []}
        scenarios = {s.get("entity_id") for s in view.get("Scenario") or []}
        out: List[str] = []
        for relation in parsed.get("constraint_relations") or []:
            rid = relation.get("id")
            named = [c for c in (relation.get("configurations") or [])
                     if isinstance(c, str) and c.strip()]
            if not named:
                out.append("%s names no configuration, so it removes a DOF "
                           "nowhere; a relation holds where it says it holds"
                           % rid)
            # THE DOMAIN IS THE VIEW'S. Membership is decided against the groups
            # and configurations this invocation was given, which is what makes
            # the answer branch-local without a second notion of a branch: a
            # configuration of another candidate resolves as an id and addresses
            # no cell of this grid.
            elsewhere = [c for c in named if c not in configs]
            if elsewhere:
                out.append("%s holds in %s, which is no configuration of this "
                           "mechanism; it removes a DOF nowhere here"
                           % (rid, ", ".join(sorted(elsewhere))))
            group = relation.get("retained_group")
            if group and group not in groups:
                out.append("%s retains %s, which is no rigid group of this "
                           "mechanism" % (rid, group))
            unknown = [d for d in (relation.get("blocked_dofs") or [])
                       if d not in DOF_NAMES]
            if unknown:
                out.append("%s blocks %s, which is not a degree of freedom this "
                           "pipeline has (%s); it removes nothing"
                           % (rid, ", ".join(str(u) for u in unknown),
                              ", ".join(DOF_NAMES)))
        for i, claim in enumerate(parsed.get("irrelevance") or []):
            if not isinstance(claim, dict):
                out.append("irrelevance claim %d is not a record" % i)
                continue
            absent = [f for f in ("rigid_group", "configuration", "scenario")
                      if not str(claim.get(f) or "").strip()]
            if not [d for d in (claim.get("dof") or []) if d in DOF_NAMES]:
                absent.append("dof")
            if absent:
                out.append("an irrelevance claim names no %s, so it makes no DOF "
                           "irrelevant anywhere" % ", ".join(absent))
                continue
            # NAMING SOMETHING IS NOT REACHING IT. An irrelevance claim is not
            # canonical state - it exists only to dispose a cell - so a claim
            # about a group, configuration or scenario that is not in this view
            # is not caught by any reference rule and disposes nothing at all.
            for field, universe, what in (("rigid_group", groups, "rigid group"),
                                          ("configuration", configs, "configuration"),
                                          ("scenario", scenarios, "scenario")):
                value = claim.get(field)
                if value not in universe:
                    out.append("an irrelevance claim names %s %s, which is no %s "
                               "this consumer was given; it makes no DOF "
                               "irrelevant anywhere" % (field, value, what))
            bad = [d for d in (claim.get("dof") or []) if d not in DOF_NAMES]
            if bad:
                out.append("an irrelevance claim names %s, which is not a degree "
                           "of freedom this pipeline has" % ", ".join(str(b) for b in bad))
        return out

    def derived_operations(self, parsed, inputs, state):
        """The TOTAL DOF disposition, derived from the relations just authored.

        The contract splits the labour: the model authors relations, the pipeline
        expands them (LLM role NONE for totality). The expansion is still s03
        output embodying one candidate, so it carries the same premise.

        IT BELONGS TO THE INVOCATION. This used to be called by
        `tools/run_window2.py` after `invoke` returned, as a separate patch - so
        the answer to "does this DesignState have a DOF disposition in it"
        depended on which caller ran, and a second canonical caller of `invoke`
        got a state with none. Deriving it here puts it in the stage's own patch,
        validated at the same write boundary as the relations it derives from,
        and reachable by every caller for the same reason.

        The topology comes from THIS INVOCATION'S CONSUMER VIEW, which is the
        only branch-scoped answer to "which topology is this". Reading it from
        state gave the second candidate a domain built from every group and
        configuration in the design, including the first candidate's - the two
        derivations then collided on an id, which is how the scope error
        announced itself, but the wrong answer was the domain and not the id. A
        runner passing the topology in as arguments had the same defect and no
        way to notice it.
        """
        view = inputs.get(self.context_key) or {}
        entries = derive_mobility(
            [g["entity_id"] for g in view.get("RigidGroup") or []],
            [c["entity_id"] for c in view.get("Configuration") or []],
            list(view.get("Joint") or []),
            parsed.get("constraint_relations") or [],
            parsed.get("irrelevance") or [])
        by_config: Dict[str, List[Dict[str, Any]]] = {}
        for e in entries:
            by_config.setdefault(e["configuration"], []).append(e)
        # KEYED ON THE CONFIGURATION, which is this entity's natural key: there is
        # one mobility expectation per configuration and configurations are
        # candidate-local. A running MEX-0001 counter numbered from one per
        # invocation, so the second candidate's derivation collided with the
        # first's - two candidates could not both have mobility, and the failure
        # was invisible while a runner derived only what it was pointed at. A
        # derived id must also be RECOMPUTABLE (FA-4); a counter is a function of
        # call order, and this is a function of the premises.
        # BOTH HALVES OF THE DEPENDENCY. What makes these cells EXIST - the
        # configuration and the rigid groups they address - and what the
        # dispositions were derived FROM. Withdraw the topology and the grid
        # loses standing along with the cells it describes; withdraw a cited
        # relation and the conclusion loses standing while the cells remain.
        # Those are different consequences of one rule and both are FA-5.
        ops = [Op("CREATE", "MobilityExpectation", "MEX-%s" % cfg,
                  {"configuration": cfg, "dispositions": rows}, "s03:derivation",
                  premise_refs=sorted(set(domain_premises(rows, cfg))
                                      | set(cited_premises(rows))))
               for cfg, rows in sorted(by_config.items())]
        return carry_invocation_premises(ops, self.invocation_premises(inputs))

    def to_operations(self, parsed, inputs=None):
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops, prov = [], "s03b:relations"
        # S-4. `PhysicalInteraction` and `ConstraintRelation` have been declared
        # s03b outputs since S-2 with nothing authoring them. These are the two
        # branches that did not exist.
        #
        # An interaction TRANSMITS and a joint CONSTRAINS - the freeze separates
        # them deliberately, and this is where the transmission finally has a
        # home. The model states which groups interact, which effect passes, and
        # which candidate-independent obligation that discharges; nothing here
        # infers an interaction from a joint class or from anything's absence.
        for i in parsed.get("physical_interactions", []):
            fields = {"groups": i.get("groups", []), "effect": i["effect"],
                      "discharges_effect": i["discharges_effect"]}
            for optional in ("at_interface", "configurations"):
                if i.get(optional):
                    fields[optional] = i[optional]
            ops.append(Op("CREATE", "PhysicalInteraction", i["id"], fields, prov))
        for r in parsed.get("constraint_relations", []):
            fields = {"retained_group": r["retained_group"],
                      "blocked_dofs": r.get("blocked_dofs", []),
                      "configurations": r.get("configurations", []),
                      "driver": r["driver"]}
            # `release_transition` is NOT forwarded, and the field audit is why:
            # no line of S03B_PROMPT asks for it, no consumer reads it, and the
            # contract types it as nothing - so the only way it could arrive is a
            # response nobody asked for, and it would enter canonical state
            # untyped, where prose and a dangling id are equally acceptable. It
            # stays DECLARED for an author who has a premise for it; what is
            # removed is a producer forwarding a field that no question produced.
            for optional in ("blocked_direction", "provider_body",
                             "provider_reaction_site", "provider_site",
                             "maintaining_interaction", "defeat_specification",
                             # FORWARDED UNCHANGED. Which relative motion a
                             # restraint removes is the model's statement; this
                             # pass neither derives it nor repairs it.
                             "blocked_relative_motions"):
                if r.get(optional):
                    fields[optional] = r[optional]
            ops.append(Op("CREATE", "ConstraintRelation", r["id"], fields, prov))
        # WHOSE LOAD PATH THIS IS, from the invocation. The candidate was taken
        # from the RESPONSE, though the invocation already determines it: the
        # pass is run once per candidate and its premise is that candidate. A
        # model restating it can only agree or be wrong, and being wrong wrote a
        # path into another branch's design. Disagreement is reported by
        # `completeness` rather than silently overwritten - what is not written
        # here is a value this invocation did not determine.
        branch = (self.invocation_premises(inputs or {}) or [None])[0]
        for p in parsed.get("load_paths", []):
            fields = {"load_case": p["load_case"],
                      "candidate": branch or p.get("candidate"),
                      "ordered_hops": p.get("ordered_hops", []),
                      "maturity": "HYPOTHESIS"}
            # Where the path closes. Written only when the model says so: an
            # unclosed path is a legitimate recorded state (R-12), and filling it
            # in would be this code deciding the engineering.
            if p.get("terminates_at"):
                fields["terminates_at"] = p["terminates_at"]
            ops.append(Op("CREATE", "LoadPath", p["id"], fields, prov))
        for a in parsed.get("assembly_steps", []):
            ops.append(Op("CREATE", "AssemblyStep", a["id"], {
                "order_index": a["order_index"], "body": a["body"],
                "access_side": a["access_side"], "activates": a.get("activates", []),
                "termination_strategy": a.get("termination_strategy"),
                "path_kind": a["path_kind"], "depends_on": a.get("depends_on", [])}, prov))
        # WHAT STATE CHANGE MUST BE POSSIBLE, forwarded exactly as authored. A
        # requirement that exposes a contradiction is evidence: a producer that
        # dropped or repaired it would be answering an eligibility question that
        # belongs to feasibility, and answering it invisibly.
        for t in parsed.get("transition_requirements", []):
            ops.append(Op("CREATE", "TransitionRequirement", t["id"], {
                "from_configuration": t["from_configuration"],
                "to_configuration": t["to_configuration"],
                "required_relative_motions": t.get("required_relative_motions", []),
                "released_constraints": t.get("released_constraints", [])}, prov))
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u["kept_open_by"],
                "blocks": u.get("blocks", [])}, prov))
        return ops

    def _branch_local_problems(self, parsed, inputs) -> List[str]:
        """No output of this invocation may point into another candidate.

        Every candidate's topology lives in ONE DesignState, so `IFC-0009` of
        another branch RESOLVES - right format, right family, present - and the
        write boundary has no reason to refuse it. Reference integrity was intact
        and the design was still wrong: a load path routed through an interface
        that belongs to a mechanism this candidate does not have.

        WHICH REFERENCES ARE BRANCH-LOCAL IS THE CONTRACT'S ANSWER, not a list
        kept here. `referent_population` already says it per field. So LoadCase,
        the effect obligations and the reaction sites stay design-wide because
        they declare themselves so, and nothing had to be narrowed to make this
        work.

        The CONSUMER default applies here - a field declaring no population is
        branch-local - because the universe this checks against is the VIEW, and
        what a consumer may see is exactly the question that default answers. The
        write boundary governs only fields that declare the population EXPLICITLY,
        which is a different reach for a different reason: defaulting a write rule
        would silently bind every reference in the contract. So this reports a
        wider set than canonical validation refuses, and both are deliberate.

        The universe is the VIEW, which is precisely this invocation's branch
        plus the design-wide material it was given - so "in the branch" needs no
        second definition and no graph walk. Ids minted by this same response
        count: a step that depends on a step in the same patch is not foreign.

        Reads the operations rather than the response keys, because the operations
        are where the family and the field name are known. That runs the
        translator a second time, which is deliberate: one translator read twice
        cannot disagree with itself, and a table here mapping response keys to
        families would be a second producer definition.
        """
        view = inputs.get(self.context_key) or {}
        visible = {rec.get("entity_id") for rows in view.values()
                   if isinstance(rows, list) for rec in rows
                   if isinstance(rec, dict)}
        ops = self.to_operations(parsed, inputs)
        minted = {op.entity_id for op in ops}
        contracts = _contracts()
        out: List[str] = []
        for op in ops:
            for field, value in sorted((op.fields or {}).items()):
                spec = contracts.reference_spec(op.entity_type, field)
                if spec is None:
                    continue
                branch_local = _branch_population()
                population = spec.get("referent_population") or branch_local
                if population != branch_local:
                    continue
                named = value if isinstance(value, list) else [value]
                for ref in named:
                    if not isinstance(ref, str) or not ref.strip():
                        continue
                    if ref in visible or ref in minted:
                        continue
                    out.append(
                        "%s.%s names %s, which is not in this invocation's "
                        "mechanism; %s is drawn from the %s and an id that "
                        "merely exists somewhere in the design is another "
                        "candidate's" % (op.entity_id, field, ref,
                                         "%s.%s" % (op.entity_type, field),
                                         population))
        stated = {p.get("candidate") for p in parsed.get("load_paths") or []
                  if isinstance(p, dict) and p.get("candidate")}
        branch = (self.invocation_premises(inputs or {}) or [None])[0]
        for other in sorted(x for x in stated if branch and x != branch):
            out.append("a load path states candidate %s; this invocation embodies "
                       "%s, which is what was written" % (other, branch))
        return out

    def completeness(self, parsed, inputs):
        # S-4 canonical physical truth first, then the legacy mobility checks.
        # The two are different questions and are kept apart deliberately.
        out = self._s4_physical_problems(parsed, inputs)
        out.extend(self._s5_mobility_problems(parsed, inputs))
        out.extend(self._branch_local_problems(parsed, inputs))
        # THE STATE MACHINE, checked against itself. Reported, never repaired:
        # the findings are engineering facts about what this candidate says, and
        # what they cost it is decided downstream.
        out.extend(transition_consistency(
            parsed.get("transition_requirements") or [],
            parsed.get("constraint_relations") or [],
            (inputs.get(self.context_key) or {}).get("Joint") or []))
        relations = parsed.get("constraint_relations") or []
        if not relations:
            out.append("nothing in this mechanism is held: no constraint relation")
        incomplete = []
        for r in relations:
            absent = [f for f in ("retained_group", "driver")
                      if not str(r.get(f) or "").strip()]
            if not r.get("blocked_dofs"):
                absent.append("blocked_dofs")
            if not (r.get("provider_body") or r.get("provider_reaction_site")):
                absent.append("a provider")
            if absent:
                incomplete.append("%s missing %s" % (r.get("id"), ", ".join(absent)))
        if incomplete:
            out.append("%d constraint relation(s) incomplete: %s"
                       % (len(incomplete), "; ".join(incomplete[:5])
                          + ("; ..." if len(incomplete) > 5 else "")))
        for i in parsed.get("irrelevance", []):
            if isinstance(i, dict) and not str(i.get("scenario") or "").strip():
                out.append("an irrelevance claim names no scenario")
                break
        if not parsed.get("assembly_steps"):
            out.append("no assembly order")
        return out
