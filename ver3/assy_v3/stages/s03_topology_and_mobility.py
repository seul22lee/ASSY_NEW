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
from typing import Any, Dict, Iterable, List, Set, Tuple

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
        return {"T" + a}
    return set()                                    # FIXED, and anything unknown

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
                       dof[], axis_direction,
                       compliance {{mode, direction, required_travel,
                       allowable_travel_status, actuation, compliant_element,
                       root_interface, activation_window}} (only for COMPLIANT;
                       actuation is always PRESCRIBED_KINEMATIC - in the real
                       mechanism a contact drives the deflection, but in this
                       model the coordinate is imposed, and the field says so
                       precisely so the structure cannot be read as evidence
                       that the mechanism deflects itself)
  interfaces[]         id "IFC-0001", bodies[], interaction_kind, nominal_status,
                       addresses_obligations[]
  configurations[]     id "CFG-0001", name, kind, bodies_present[],
                       distinguishing_basis[] {{rigid_group, dof, differs_from[]}}
                       - what makes this configuration a DIFFERENT one: the
                       (rigid group, DOF) pairs whose value differs from the
                       named sibling configurations. [] when nothing is required
                       to differ. A later step realizes this in coordinates and
                       is checked against it, so a name is never what
                       distinguishes two states
  functional_regions[] id "FRG-0001", role, owning_bodies[],
                       required_by_actors[] (actor ids from the input; [] for
                       SUPPORT and KEEP_OUT regions no actor uses),
                       reach_targets[] (what those actors must reach through it)
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
  unresolved[].kept_open_by      Ambiguity or Freedom ids from the input

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
      free by an authored joint's class     -> INTENDED, citing the joint
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
            for dof in free_dof(j.get("joint_type"), j.get("axis_direction")):
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
            fields = {"joint_type": j["joint_type"], "parent_group": j["parent_group"],
                      "child_group": j["child_group"], "dof": j.get("dof", []),
                      "axis_direction": j["axis_direction"],
                      "frame_ids": j.get("frame_ids", [])}
            if j.get("compliance"):
                fields["compliance"] = j["compliance"]
            ops.append(Op("CREATE", "Joint", j["id"], fields, prov))
        for i in parsed.get("interfaces", []):
            ops.append(Op("CREATE", "Interface", i["id"], {
                "bodies": i.get("bodies", []),
                "interaction_kind": i["interaction_kind"],
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
        for p in parsed.get("load_paths", []):
            ops.append(Op("CREATE", "LoadPath", p["id"], {
                "load_case": p["load_case"], "candidate": p["candidate"],
                "ordered_hops": p.get("ordered_hops", []),
                "maturity": "HYPOTHESIS"}, prov))
        for a in parsed.get("assembly_steps", []):
            ops.append(Op("CREATE", "AssemblyStep", a["id"], {
                "order_index": a["order_index"], "body": a["body"],
                "access_side": a["access_side"], "activates": a.get("activates", []),
                "termination_strategy": a.get("termination_strategy"),
                "path_kind": a["path_kind"], "depends_on": a.get("depends_on", [])}, prov))
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


def constraint_disposition_check(state) -> List[str]:
    """S03-C2. Every BLOCKED_BY cell cites a ConstraintRelation that exists, and
    that relation carries a direction, a provider, a defeat specification and a
    driver.

    It reads the CANONICAL fields. It used to read `blocker_body`, a legacy
    blocking-relation name the derivation stopped emitting at S-5 - so after that
    migration this check reported every correctly-derived cell as incomplete,
    which is a validator describing a producer that no longer exists.

    The defeat specification is authored with the relation, because a negative
    control written later from geometry defeats what the geometry suggests rather
    than what the design claims.
    """
    problems = []
    # STANDING throughout: this asks whether the mobility the design CURRENTLY
    # claims rests on relations it CURRENTLY has. A withdrawn grid citing a
    # withdrawn relation is consistent history, not a present defect.
    bodies = {b["entity_id"] for b in state.standing("Body")}
    relations = {r["entity_id"]: r for r in state.standing("ConstraintRelation")}
    for d in current_mobility_cells(state):
        if d.get("disposition") != "BLOCKED_BY":
            continue
        tag = "%s/%s/%s" % (d.get("rigid_group"), d.get("configuration"), d.get("dof"))
        cited = d.get("constraint_relation")
        if not cited or cited not in relations:
            problems.append("BLOCKED_BY_UNRESOLVED_PREMISE: %s cites %r"
                            % (tag, cited))
            continue
        # One finding per incomplete relation, not one per missing field: a
        # check that multiplies a single defect by four turns 70 problems into
        # 280 and buries everything else.
        missing = [f for f in ("blocked_direction", "defeat_specification",
                               "driver") if not str(d.get(f) or "").strip()]
        if not (d.get("provider_body") or d.get("provider_reaction_site")):
            missing.append("a provider")
        if missing:
            problems.append("BLOCKING_INCOMPLETE: %s missing %s"
                            % (tag, ", ".join(missing)))
        if d.get("driver") and d["driver"] not in CONSTRAINT_DRIVERS:
            problems.append("BLOCKING_BAD_DRIVER: %s -> %r" % (tag, d["driver"]))
        provider = d.get("provider_body")
        if provider and bodies and provider not in bodies:
            problems.append("PROVIDER_NOT_A_BODY: %s -> %r" % (tag, provider))
    return problems


def irrelevance_check(state) -> List[str]:
    """S03-C3. Every IRRELEVANT_BECAUSE names a scenario, and that scenario is
    one in which the DOF is genuinely unloaded.

    IRRELEVANT is the one disposition that cannot be checked against the joint
    graph, so it is checked against the LoadCases instead: a DOF called
    irrelevant in a scenario that carries a load case is not irrelevant.
    """
    scenarios = {s["entity_id"] for s in state.standing("Scenario")}
    loaded = {l.get("scenario") for l in state.standing("LoadCase")}
    problems = []
    for d in current_mobility_cells(state):
        if d.get("disposition") != "IRRELEVANT_BECAUSE":
            continue
        tag = "%s/%s/%s" % (d.get("rigid_group"), d.get("configuration"), d.get("dof"))
        scenario = d.get("scenario")
        if not str(scenario or "").strip():
            problems.append("IRRELEVANCE_UNJUSTIFIED: %s names no scenario" % tag)
            continue
        if scenarios and scenario in scenarios and scenario in loaded:
            problems.append(
                "IRRELEVANCE_CONTRADICTED: %s cites %s, which carries a load case"
                % (tag, scenario))
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
    for g in retained:
        body = group_body.get(g)
        if body and body in declared and not declared[body]:
            problems.append("RETAINED_BODY_WITHOUT_TERMINATION: %s" % body)
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
    required = ("mode", "direction", "required_travel", "allowable_travel_status",
                "actuation", "compliant_element", "root_interface", "activation_window")
    problems = []
    for j in state.family("Joint"):
        if j.get("joint_type") != "COMPLIANT":
            continue
        c = j.get("compliance")
        if not isinstance(c, dict):
            problems.append("COMPLIANT_JOINT_WITHOUT_COMPLIANCE_BLOCK: %s" % j["entity_id"])
            continue
        for field in required:
            if not str(c.get(field) or "").strip():
                problems.append("COMPLIANCE_INCOMPLETE: %s missing %s" % (j["entity_id"], field))
        if c.get("actuation") and c["actuation"] != "PRESCRIBED_KINEMATIC":
            problems.append("COMPLIANCE_ACTUATION_NOT_DECLARED_PRESCRIBED: %s -> %r"
                            % (j["entity_id"], c["actuation"]))
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
   ROTATION or ELASTICITY.

RESPONSE SCHEMA
Return one JSON object. Emit every key. Use exactly these key names.

  irrelevance[]         rigid_group, configuration, dof[], scenario
  physical_interactions[]
                        id "PHI-0001", groups[], effect, discharges_effect,
                        at_interface (optional), configurations[] (optional)
  constraint_relations[]
                        id "CRL-0001", retained_group, blocked_dofs[],
                        configurations[], driver, blocked_direction (optional),
                        provider_body (optional),
                        provider_reaction_site (optional),
                        provider_site (optional),
                        maintaining_interaction (optional),
                        defeat_specification (optional)
                        AT LEAST ONE of provider_body / provider_reaction_site
                        must identify what provides the constraint.
                        provider_site is where it acts and does not answer that.
  load_paths[]          id "LDP-0001", load_case, candidate, ordered_hops[],
                        terminates_at (optional)
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

Every reference above is an ID. A description is not an id, and an interaction
you describe instead of emitting does not exist.

Ids you emit are new. Never reuse an id from the input.

THE CANDIDATE YOU ARE EMBODYING
{candidate}

TYPED INPUT
-----------
{mechanism}
"""


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
        discharged = {i.get("discharges_effect")
                      for i in parsed.get("physical_interactions") or []}
        for demand in view.get("PhysicalEffectObligation") or []:
            eid = demand.get("entity_id")
            if eid not in discharged and eid not in open_items:
                out.append("U5-1 %s is neither discharged by an interaction nor "
                           "recorded open" % eid)

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
        """
        out: List[str] = []
        for relation in parsed.get("constraint_relations") or []:
            configs = [c for c in (relation.get("configurations") or [])
                       if isinstance(c, str) and c.strip()]
            if not configs:
                out.append("%s names no configuration, so it removes a DOF "
                           "nowhere; a relation holds where it says it holds"
                           % relation.get("id"))
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
            for optional in ("blocked_direction", "provider_body",
                             "provider_reaction_site", "provider_site",
                             "maintaining_interaction", "defeat_specification",
                             "release_transition"):
                if r.get(optional):
                    fields[optional] = r[optional]
            ops.append(Op("CREATE", "ConstraintRelation", r["id"], fields, prov))
        for p in parsed.get("load_paths", []):
            fields = {"load_case": p["load_case"], "candidate": p["candidate"],
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
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u["kept_open_by"],
                "blocks": u.get("blocks", [])}, prov))
        return ops

    def completeness(self, parsed, inputs):
        # S-4 canonical physical truth first, then the legacy mobility checks.
        # The two are different questions and are kept apart deliberately.
        out = self._s4_physical_problems(parsed, inputs)
        out.extend(self._s5_mobility_problems(parsed, inputs))
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
