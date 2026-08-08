"""S03 - topology, mobility and assembly strategy.

Engineering question: what things are there, how are they connected, what may
move, what must not, what reacts what, and in what order does it go together?

Geometry first appears here and it is SYMBOLIC: frames, axis DIRECTIONS,
sidedness. No magnitude and no axis PLACEMENT - placement depends on feature
envelopes that do not exist until s04.

THE ONE STRUCTURAL IDEA
    MobilityExpectation is a TOTAL function, not a declared set. The domain -
    every rigid group x every configuration x every rigid-body DOF - is
    enumerated HERE, mechanically, and the model only dispositions each entry.
    A declared set cannot fail by omission; a total function can, and that is
    the whole point. The contract puts the LLM role at NONE for the totality and
    HIGH for the disposition, and this module is built that way: `dof_domain`
    computes the domain from the joint graph, and the check verifies coverage
    against it rather than against anything the model said.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Set, Tuple

from ..state.patch import Op
from .base import Stage

#: The six rigid-body degrees of freedom. The domain of the totality.
DOF_NAMES = ("TX", "TY", "TZ", "RX", "RY", "RZ")

DISPOSITIONS = ("INTENDED", "BLOCKED_BY", "MAINTAINED_BY_CLASS", "IRRELEVANT_BECAUSE")

#: The compact wire codes. The disposition VOCABULARY is unchanged - only how it
#: is transmitted - so nothing downstream sees a code.
_DISPOSITION_CODE = {"I": "INTENDED", "B": "BLOCKED_BY",
                     "M": "MAINTAINED_BY_CLASS", "R": "IRRELEVANT_BECAUSE"}

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

BLOCKING_DRIVERS = ("LOAD", "KINEMATIC_NECESSITY", "DECLARED_SCENARIO")

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
5. A later step dispositions every degree of freedom of every rigid group in
   every configuration, so make the groups and configurations complete and
   final here: it can only disposition what you declare.
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
  configurations[]     id "CFG-0001", name, kind, bodies_present[]
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
  disposition         {dispositions}
  driver              {drivers}
  termination_strategy {terminations} - NONE only for a body nothing retains
  path_kind           {path_kinds}
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
  disposition         {dispositions}
  driver              {drivers}
  termination_strategy {terminations} - NONE only for a body nothing retains
  path_kind           {path_kinds}
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


def dof_domain(groups: Iterable[str], configurations: Iterable[str]) -> List[Tuple[str, str, str]]:
    """The COMPLETE domain of the mobility function.

    Computed here, from the topology, and never taken from the response. This is
    what makes omission detectable: the model can fail to disposition a line, but
    it cannot make the line not exist.
    """
    return [(g, c, d) for g in groups for c in configurations for d in DOF_NAMES]


class S03TopologyAndMobility(Stage):
    stage_id = "s03"
    purpose = "turn a candidate family into a mechanism topology with a total DOF disposition"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        projection = inputs["projection"]
        candidate = inputs.get("candidate") or {}
        grid = inputs.get("dof_grid_text") or (
            "Emit your rigid groups and configurations first; then disposition\n"
            "every (rigid group, configuration, DOF) triple over the six DOF\n"
            "%s. Every triple, exactly once." % ", ".join(DOF_NAMES))
        return PROMPT.format(
            joint_types=" | ".join(JOINT_TYPES), dofs=" | ".join(DOF_NAMES),
            axis_directions=" | ".join(AXIS_DIRECTIONS),
            interaction_kinds=" | ".join(INTERACTION_KINDS),
            dispositions=" | ".join(DISPOSITIONS),
            drivers=" | ".join(BLOCKING_DRIVERS),
            terminations=" | ".join(TERMINATION_STRATEGIES),
            path_kinds=" | ".join(PATH_KINDS),
            region_roles=" | ".join(REGION_ROLES),
            candidate=_render(candidate),
            projection=_render(projection))

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
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
            ops.append(Op("CREATE", "Configuration", c["id"], {
                "name": c["name"], "kind": c.get("kind", "OPERATIONAL"),
                "bodies_present": c.get("bodies_present", []),
                "expected_mobility": c.get("expected_mobility", [])}, prov))
        # One MobilityExpectation per configuration, carrying the dispositions
        # for that configuration. The grouping is ours, not the model's.
        by_config: Dict[str, List[Dict[str, Any]]] = {}
        for row in parsed.get("mobility", []):
            for dof, code in (row.get("dof") or {}).items():
                entry = {"rigid_group": row["rigid_group"],
                         "configuration": row["configuration"],
                         "dof": dof, "disposition": _DISPOSITION_CODE.get(code, code)}
                d = (row.get("detail") or {}).get(dof)
                if isinstance(d, dict):
                    entry.update(d)
                elif d:
                    # A detail that is not a mapping still says something; keep
                    # it verbatim rather than dropping it or crashing on it.
                    entry["detail_note"] = d
                by_config.setdefault(row["configuration"], []).append(entry)
        for d in parsed.get("dof_dispositions", []):        # long form still accepted
            by_config.setdefault(d["configuration"], []).append(d)
        for idx, (config, entries) in enumerate(sorted(by_config.items()), start=1):
            ops.append(Op("CREATE", "MobilityExpectation", "MEX-%04d" % idx, {
                "configuration": config, "dispositions": entries}, prov))
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
    import json
    try:
        return json.dumps(obj, indent=1, sort_keys=True)[:24000]
    except Exception:                                                # noqa: BLE001
        return str(obj)[:24000]


# =========================================================================
# checks
# =========================================================================
def dof_totality_check(state) -> List[str]:
    """S03-C1. Every rigid group, in every configuration, has every DOF
    dispositioned EXACTLY once.

    The domain comes from the topology, not from the response, so an omission is
    a missing entry rather than an invisible absence. This is the check the whole
    stage is shaped around.
    """
    groups = [g["entity_id"] for g in state.family("RigidGroup")]
    configs = [c["entity_id"] for c in state.family("Configuration")]
    if not groups or not configs:
        return ["DOF_DOMAIN_EMPTY: %d groups, %d configurations" % (len(groups), len(configs))]
    seen: Dict[Tuple[str, str, str], int] = {}
    for mex in state.family("MobilityExpectation"):
        for d in mex.get("dispositions", []):
            if not isinstance(d, dict):
                continue
            key = (d.get("rigid_group"), d.get("configuration"), d.get("dof"))
            seen[key] = seen.get(key, 0) + 1
    problems = []
    missing = [k for k in dof_domain(groups, configs) if k not in seen]
    for k in missing[:12]:
        problems.append("DOF_NOT_DISPOSITIONED: %s in %s: %s" % k)
    if len(missing) > 12:
        problems.append("DOF_NOT_DISPOSITIONED: and %d more" % (len(missing) - 12))
    for k, n in sorted(seen.items()):
        if n > 1:
            problems.append("DOF_DISPOSITIONED_TWICE: %s in %s: %s" % k)
        if k[0] not in groups or k[1] not in configs or k[2] not in DOF_NAMES:
            problems.append("DOF_DISPOSITION_OUT_OF_DOMAIN: %s" % (k,))
    return problems


def blocking_relation_check(state) -> List[str]:
    """S03-C2. Every BLOCKED_BY carries a direction, a blocker, a defeat
    specification and a driver.

    The defeat specification is authored here, with the relation, because a
    negative control written later from geometry defeats what the geometry
    suggests rather than what the design claims.
    """
    problems = []
    bodies = {b["entity_id"] for b in state.family("Body")}
    for mex in state.family("MobilityExpectation"):
        for d in mex.get("dispositions", []):
            if not isinstance(d, dict) or d.get("disposition") != "BLOCKED_BY":
                continue
            tag = "%s/%s/%s" % (d.get("rigid_group"), d.get("configuration"), d.get("dof"))
            # One finding per incomplete relation, not one per missing field: a
            # check that multiplies a single defect by four turns 70 problems
            # into 280 and buries everything else.
            missing = [f for f in ("blocked_direction", "blocker_body",
                                   "defeat_specification", "driver")
                       if not str(d.get(f) or "").strip()]
            if missing:
                problems.append("BLOCKING_INCOMPLETE: %s missing %s"
                                % (tag, ", ".join(missing)))
            if d.get("driver") and d["driver"] not in BLOCKING_DRIVERS:
                problems.append("BLOCKING_BAD_DRIVER: %s -> %r" % (tag, d["driver"]))
            blocker = d.get("blocker_body")
            if blocker and bodies and blocker not in bodies:
                problems.append("BLOCKER_NOT_A_BODY: %s -> %r" % (tag, blocker))
    return problems


def irrelevance_check(state) -> List[str]:
    """S03-C3. Every IRRELEVANT_BECAUSE names a scenario, and that scenario is
    one in which the DOF is genuinely unloaded.

    IRRELEVANT is the one disposition that cannot be checked against the joint
    graph, so it is checked against the LoadCases instead: a DOF called
    irrelevant in a scenario that carries a load case is not irrelevant.
    """
    scenarios = {s["entity_id"] for s in state.family("Scenario")}
    loaded = {l.get("scenario") for l in state.family("LoadCase")}
    problems = []
    for mex in state.family("MobilityExpectation"):
        for d in mex.get("dispositions", []):
            if not isinstance(d, dict) or d.get("disposition") != "IRRELEVANT_BECAUSE":
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


def assembly_acyclic_check(state) -> List[str]:
    """S03-C4. The assembly precedence relation is acyclic, and its order is a
    linear extension of it."""
    steps = {s["entity_id"]: s for s in state.family("AssemblyStep")}
    problems = []
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
S03B_PROMPT = """You are completing a mechanism that already exists as a topology.
The bodies, rigid groups, joints, interfaces and configurations are fixed and are
given below. You are adding what moves, what stops it, how loads reach the world,
and in what order it goes together.

Do not add or rename bodies, groups, joints, interfaces or configurations. If
something is missing, say so in `unresolved` rather than inventing it.

RULES
1. DISPOSITION EVERY DEGREE OF FREEDOM, for every rigid group in every
   configuration. Each of the six gets exactly one code:
     I  INTENDED             this motion is the point
     B  BLOCKED_BY           something stops it
     M  MAINTAINED_BY_CLASS  the joint class holds it by construction
     R  IRRELEVANT_BECAUSE   name a scenario in which it is BOTH unloaded AND
                             unactuated; if you cannot name one, it is not
                             irrelevant, and a scenario that carries a load case
                             is not such a scenario
   Expand into `detail` ONLY the ones you coded B or R.
   A B needs the BODY ID that stops it, the direction, how a test would defeat
   it, and why it must be blocked (LOAD, KINEMATIC_NECESSITY, DECLARED_SCENARIO).
   Every body meant to stay where it is put has at least one blocked DOF: a
   mechanism in which nothing is blocked is a pile of loose parts.
   Leaving a line out is the failure this stage exists to prevent.
2. For every LOAD CASE, trace the ordered PATH from where the load is applied,
   through THIS mechanism, to the reaction site. Hops are body, joint or
   interface ids. A path that does not reach the reaction site is a load that is
   not reacted. Never state how much load anything carries.
3. Give the ASSEMBLY ORDER: which body, from which access side, what it depends
   on, and which retention termination holds it once placed -
   LATER_BODY_COVER, ROTATION, ELASTICITY, or NONE if nothing retains it. A
   rigid part pushed straight in leaves the reverse direction open, so a body
   that must stay put needs one of the first three. Mark a step
   DEFORMATION_RESOLVED if it only goes together because something flexes,
   otherwise RIGID.

RESPONSE SCHEMA
Return a single JSON object with exactly these keys.

  mobility[]           one row per (rigid_group, configuration) pair:
                       rigid_group, configuration,
                       dof {{TX,TY,TZ,RX,RY,RZ}} each holding one code I/B/M/R,
                       detail {{<DOF>: {{...}}}} for the B and R codes only
  load_paths[]         id "LDP-0001", load_case, candidate, ordered_hops[]
  assembly_steps[]     id "ASY-0001", order_index (integer), body, access_side,
                       activates[], termination_strategy, path_kind, depends_on[]
  unresolved[]         id "S3U-1001", decision, why_open, alternatives[],
                       alternatives_kind, kept_open_by[], blocks[]

PERMITTED VALUES
  driver               {drivers}
  termination_strategy {terminations} - NONE only for a body nothing retains
  path_kind            {path_kinds}
  alternatives_kind    ENTITY_REFS | PRINCIPLE_FAMILIES | FREE_TEXT

THE MECHANISM YOU ARE COMPLETING
{mechanism}

THE LOAD CASES AND OBLIGATIONS
{demands}
"""


class S03BMobilityAndAssembly(Stage):
    """The second half of s03. Split from the first because one response could
    not carry the whole mechanism AND its complete mobility grid: the largest
    topologies truncated, and a truncated total function is not a total
    function. The split preserves every field; it only stops asking for them at
    once."""

    stage_id = "s03"
    pass_id = "s03b"
    purpose = "disposition every degree of freedom and give the load paths and assembly order"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        return S03B_PROMPT.format(
            drivers=" | ".join(BLOCKING_DRIVERS),
            terminations=" | ".join(TERMINATION_STRATEGIES),
            path_kinds=" | ".join(PATH_KINDS),
            mechanism=_render(inputs["mechanism"]),
            demands=_render(inputs.get("demands") or {}))

    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s03b:mobility"
        by_config: Dict[str, List[Dict[str, Any]]] = {}
        for row in parsed.get("mobility", []):
            for dof, code in (row.get("dof") or {}).items():
                entry = {"rigid_group": row["rigid_group"],
                         "configuration": row["configuration"],
                         "dof": dof, "disposition": _DISPOSITION_CODE.get(code, code)}
                d = (row.get("detail") or {}).get(dof)
                if isinstance(d, dict):
                    entry.update(d)
                elif d:
                    # A detail that is not a mapping still says something; keep
                    # it verbatim rather than dropping it or crashing on it.
                    entry["detail_note"] = d
                by_config.setdefault(row["configuration"], []).append(entry)
        for idx, (config, entries) in enumerate(sorted(by_config.items()), start=1):
            ops.append(Op("CREATE", "MobilityExpectation", "MEX-%04d" % idx, {
                "configuration": config, "dispositions": entries}, prov))
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
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u["kept_open_by"],
                "blocks": u.get("blocks", [])}, prov))
        return ops

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        if not parsed.get("mobility"):
            out.append("no DOF dispositions")
        for row in parsed.get("mobility", []):
            for dof, code in (row.get("dof") or {}).items():
                if _DISPOSITION_CODE.get(code, code) not in DISPOSITIONS:
                    out.append("disposition %r is not one of the four" % code)
                    break
        # A BLOCKED_BY without its defeat specification is a CLAIM WITHOUT ITS
        # EVIDENCE. It was previously reported by a check that ran after the
        # stage had already returned SUCCESS, so the stage passed while the
        # support for its central claim was missing. Mandatory evidence belongs
        # here, where its absence makes the stage CONTRACT_INCOMPLETE.
        blocked_missing, irrelevant_missing = [], []
        for row in parsed.get("mobility", []):
            detail = row.get("detail") or {}
            for dof, code in (row.get("dof") or {}).items():
                disposition = _DISPOSITION_CODE.get(code, code)
                d = detail.get(dof) if isinstance(detail, dict) else None
                d = d if isinstance(d, dict) else {}
                tag = "%s/%s/%s" % (row.get("rigid_group"), row.get("configuration"), dof)
                if disposition == "BLOCKED_BY":
                    absent = [f for f in ("blocked_direction", "blocker_body",
                                          "defeat_specification", "driver")
                              if not str(d.get(f) or "").strip()]
                    if absent:
                        blocked_missing.append("%s missing %s" % (tag, ", ".join(absent)))
                elif disposition == "IRRELEVANT_BECAUSE":
                    if not str(d.get("scenario") or "").strip():
                        irrelevant_missing.append("%s names no scenario" % tag)
        if blocked_missing:
            out.append("%d blocked DOF carry no defeat specification: %s"
                       % (len(blocked_missing), "; ".join(blocked_missing[:6])
                          + ("; ..." if len(blocked_missing) > 6 else "")))
        if irrelevant_missing:
            out.append("%d DOF called irrelevant name no scenario: %s"
                       % (len(irrelevant_missing), "; ".join(irrelevant_missing[:6])
                          + ("; ..." if len(irrelevant_missing) > 6 else "")))
        if not parsed.get("assembly_steps"):
            out.append("no assembly order")
        return out
