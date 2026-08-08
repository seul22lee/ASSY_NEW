"""S04 - envelope, reach and spatial proof. Two passes, one selection gate.

s04a  Can any of these candidates fit, reach and be approached at all?
      Kills candidates cheaply, each for a stated geometric reason.
s04b  Where is everything in each state, what path connects the states, and is
      that path - and every assembly path - actually clear?

WHAT IS MODEL WORK AND WHAT IS NOT
    The model proposes EXTENTS and PLACEMENTS. It does not decide whether two
    boxes overlap, and it is never asked to: interference, reach and swept
    occupancy are computed here, deterministically, from the numbers it gave.
    An LLM asked "do these interfere?" will answer, and the answer will be
    unfalsifiable. Asking it only for the inputs keeps every spatial verdict
    reproducible.

CONSERVATISM, STATED ONCE
    Every extent is an axis-aligned box. For an AABB, NO-OVERLAP IS A PROOF of
    clearance and OVERLAP IS NOT A PROOF of collision - the real bodies are
    smaller than their boxes. So a clear result is evidence and an unclear
    result is NOT_VERIFIED, never FAIL. Reporting AABB overlap as interference
    would manufacture failures the geometry does not support.

SCALE
    Extents are RELATIVE unless a requirement supplied an absolute quantity.
    Where absolute scale is free, it stays free: the numbers are a consistent
    relative system and are marked BOUNDED, never presented as dimensions.
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..state.patch import Op
from .base import Stage

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
REGION_ROLES = ("ACCESS", "SUPPORT", "KEEP_OUT", "APERTURE")

#: Results a spatial check may produce. FAIL is deliberately absent for
#: overlap-based conclusions; see the module docstring.
CLEAR, NOT_VERIFIED, OCCUPIED = "CLEAR", "NOT_VERIFIED", "OCCUPIED"


# =========================================================================
# geometry - deterministic, no model involved
# =========================================================================
def aabb(centre: Sequence[float], half: Sequence[float]) -> Tuple[List[float], List[float]]:
    lo = [centre[i] - abs(half[i]) for i in range(3)]
    hi = [centre[i] + abs(half[i]) for i in range(3)]
    return lo, hi


def overlaps(a: Tuple[List[float], List[float]], b: Tuple[List[float], List[float]],
             tol: float = 1e-9) -> bool:
    (alo, ahi), (blo, bhi) = a, b
    return all(alo[i] < bhi[i] - tol and blo[i] < ahi[i] - tol for i in range(3))


def translate(box: Tuple[List[float], List[float]],
              delta: Sequence[float]) -> Tuple[List[float], List[float]]:
    lo, hi = box
    return ([lo[i] + delta[i] for i in range(3)], [hi[i] + delta[i] for i in range(3)])


def rotate_about_axis(box: Tuple[List[float], List[float]], axis: str,
                      origin: Sequence[float], radians: float
                      ) -> Tuple[List[float], List[float]]:
    """Rotate a box and RE-BOUND it axis-aligned.

    The re-bound only ever grows the box, so it stays conservative in the
    direction that matters: a no-overlap result on the grown box is still a
    proof of clearance for the real body.
    """
    lo, hi = box
    corners = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    idx = AXIS_INDEX.get(axis.upper().lstrip("+-"), 2)
    u, v = [i for i in range(3) if i != idx]
    c, s = math.cos(radians), math.sin(radians)
    out = []
    for p in corners:
        du, dv = p[u] - origin[u], p[v] - origin[v]
        q = list(p)
        q[u] = origin[u] + du * c - dv * s
        q[v] = origin[v] + du * s + dv * c
        out.append(q)
    return ([min(p[i] for p in out) for i in range(3)],
            [max(p[i] for p in out) for i in range(3)])


def sample(a: float, b: float, n: int) -> List[float]:
    """Uniform samples INCLUDING interior points.

    Endpoint-only sampling is refused by the contract because it is the most
    effective way to make an unbuildable mechanism look correct: the ends are
    exactly where a designer has already checked.
    """
    n = max(int(n), 3)
    return [a + (b - a) * i / float(n - 1) for i in range(n)]


# =========================================================================
# s04a
# =========================================================================
S04A_PROMPT = """You are sizing a mechanism that already exists as a topology, so
that a later step can test whether it can physically fit, reach and be assembled.

You receive ONLY the mechanism: bodies, rigid groups, joints, configurations,
assembly steps, functional regions, and the actors that must reach things. You do
not receive the original request and you must not try to reconstruct it.

WHAT YOU ARE DECIDING
For every body, a provisional EXTENT: a box, given as a half-extent in x, y, z,
and a centre position, in ONE consistent relative coordinate system. You are not
choosing dimensions - no feature exists yet. You are proposing the smallest
consistent set of relative sizes and positions in which this topology could
physically exist, so that boxes which cannot possibly coexist can be detected.

SCALE
Work in RELATIVE units unless the input states an absolute quantity. Pick any
convenient scale and keep it consistent. If the input does state a quantity, use
it and say so. Never invent an absolute size for something the input left free.

RULES
1. Every body gets an extent and a centre.
2. THESE BODY PAIRS MUST TOUCH. Each pair is connected by a joint or declared as
   a CONTACT interface, so their boxes must overlap or share a face. A pair in
   this list placed apart describes a mechanism whose parts are not connected,
   which contradicts the topology you were given rather than expressing it:
{contact_pairs}
3. Every functional region gets a volume - a box - positioned where the design
   promises it: an ACCESS region where a hand or an item goes in, a SUPPORT
   region where the product meets what carries it, a KEEP_OUT region nothing may
   enter, an APERTURE where something passes through.
4. For every actor and everything it must reach, say whether the reach is
   possible in this arrangement, and from which side.
5. For every assembly step, say which direction the body arrives from, as a
   vector in the same coordinates.
6. If this topology CANNOT be given a consistent arrangement at all, say so and
   name the geometric reason. That is a real and useful result: it eliminates a
   candidate cheaply, which is what this pass is for.

Do not state that anything interferes or is clear. You are not being asked to
judge overlaps and you cannot see them: that is computed from your numbers.

RESPONSE SCHEMA
Return a single JSON object with these keys, each a list unless marked.

  scale                 object {{basis, absolute, note}} - basis is "RELATIVE" or
                        "ABSOLUTE"; absolute is the quantity you were given, or
                        null
  envelopes[]           id "ENV-0001", body, half_extent [x,y,z],
                        centre [x,y,z], maturity "PROVISIONAL"
  region_volumes[]      functional_region, half_extent [x,y,z], centre [x,y,z]
  reach_results[]       actor, target, reachable (boolean), approach_side,
                        why
  assembly_directions[] assembly_step, direction [x,y,z]
  elimination           object {{eliminated (boolean), reason}} - reason is a
                        GEOMETRIC statement, or null when not eliminated

REFERENCES
  envelopes[].body                a body id from the input
  region_volumes[].functional_region  a functional region id from the input
  reach_results[].actor           an actor id from the input
  assembly_directions[].assembly_step an assembly step id from the input

THE MECHANISM
{mechanism}
"""


class S04AEnvelopeAndReach(Stage):
    # Both passes are s04. The contract calls them PASSES of one stage, and the
    # ownership matrix owns families at stage granularity, so a pass id here
    # would make every entity this stage creates ownerless.
    stage_id = "s04"
    pass_id = "s04a"
    purpose = "give the topology a provisional arrangement so feasibility can be computed"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        return S04A_PROMPT.format(mechanism=_render(inputs["mechanism"]),
                                  contact_pairs=_contact_pairs_text(inputs["mechanism"]))

    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s04a:arrangement"
        scale = parsed.get("scale") or {}
        for e in parsed.get("envelopes", []):
            ops.append(Op("CREATE", "Envelope", e["id"], {
                "body": e["body"],
                "extent": {"half_extent": e["half_extent"], "centre": e["centre"]},
                "frame": "world",
                "maturity": e.get("maturity", "PROVISIONAL"),
                "scale_basis": scale.get("basis", "RELATIVE")}, prov))
        return ops

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        bodies = {b["entity_id"] for b in inputs["mechanism"].get("Body", [])}
        placed = {e.get("body") for e in parsed.get("envelopes", [])}
        for missing in sorted(bodies - placed):
            out.append("body %s has no extent" % missing)
        for e in parsed.get("envelopes", []):
            for field in ("half_extent", "centre"):
                v = e.get(field)
                if not (isinstance(v, list) and len(v) == 3
                        and all(isinstance(x, (int, float)) for x in v)):
                    out.append("envelope %s has a malformed %s" % (e.get("id"), field))
        # A pair the topology connects, placed apart, is an arrangement that
        # contradicts its own producer. s04a has not supplied the evidence its
        # output claims, so this is incompleteness rather than a finding beside
        # a SUCCESS. Gaps observed live were 1.0-1.5 in a system whose bodies
        # are a few units across, so this is reasoning, not tolerance.
        boxes = {}
        for e in parsed.get("envelopes", []):
            c, h = e.get("centre"), e.get("half_extent")
            if isinstance(c, list) and isinstance(h, list) and len(c) == 3 and len(h) == 3:
                try:
                    boxes[e.get("body")] = aabb([float(x) for x in c],
                                                [float(x) for x in h])
                except Exception:                                    # noqa: BLE001
                    pass
        apart = []
        for pb, cb in required_contacts(inputs["mechanism"]):
            a, b = boxes.get(pb), boxes.get(cb)
            if not (a and b):
                continue
            gap = max(max(a[0][i] - b[1][i], b[0][i] - a[1][i]) for i in range(3))
            if gap > 0:
                apart.append("%s and %s placed %.3g apart" % (pb, cb, gap))
        if apart:
            out.append("%d body pair(s) the topology connects are placed apart: %s"
                       % (len(apart), "; ".join(apart[:6])
                          + ("; ..." if len(apart) > 6 else "")))

        regions = {r["entity_id"] for r in inputs["mechanism"].get("FunctionalRegion", [])}
        volumed = {r.get("functional_region") for r in parsed.get("region_volumes", [])}
        for missing in sorted(regions - volumed):
            out.append("functional region %s has no volume" % missing)
        return out


# =========================================================================
# s04b
# =========================================================================
S04B_PROMPT = """You are placing a mechanism in space and describing how it moves,
so that a later step can test whether the motion is actually clear.

You receive the mechanism and its provisional arrangement. You do not receive the
original request.

WHAT YOU ARE DECIDING
1. Where each JOINT sits - its frame origin, as a position in the same
   coordinates as the arrangement you were given, and the axis it turns or slides
   about. The direction is already fixed by the topology; you are placing it.
2. For every configuration, the COORDINATE of every joint in that configuration -
   an angle in degrees for a revolute or compliant joint, a distance for a
   prismatic one, in the same relative units.
3. Which configuration each transition goes from and to.

Do not state that anything is clear, interferes, or sweeps through anything. You
cannot see that and are not being asked: it is computed from your numbers.

RESPONSE SCHEMA
Return a single JSON object with these keys.

  joint_placements[]   joint, origin [x,y,z]
  state_coordinates[]  configuration, coordinates {{<joint id>: number}}
  transitions[]        id "TRN-0001", from_configuration, to_configuration,
                       moving_groups[]
  notes                string, may be ""

REFERENCES
  joint_placements[].joint           a joint id from the input
  state_coordinates[].configuration  a configuration id from the input
  transitions[].from_configuration / to_configuration  configuration ids
  transitions[].moving_groups        rigid group ids from the input

THE MECHANISM AND ITS ARRANGEMENT
{mechanism}
"""


class S04BPlacementAndMotion(Stage):
    stage_id = "s04"
    pass_id = "s04b"
    purpose = "place the mechanism and describe its motion so clearance can be computed"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        return S04B_PROMPT.format(mechanism=_render(inputs["mechanism"]))

    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s04b:placement"
        for s in parsed.get("state_coordinates", []):
            ops.append(Op("CREATE", "State", "STA-%s" % s["configuration"], {
                "name": s["configuration"],
                "joint_coordinates": s.get("coordinates", {})}, prov))
        for t in parsed.get("transitions", []):
            ops.append(Op("CREATE", "Transition", t["id"], {
                "from_state": "STA-%s" % t["from_configuration"],
                "to_state": "STA-%s" % t["to_configuration"],
                "path": {"moving_groups": t.get("moving_groups", [])},
                "sampling_declaration": {"kind": "UNIFORM", "samples": SAMPLES,
                                         "adaptive": False,
                                         "interior_samples": SAMPLES - 2}}, prov))
        return ops

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        joints = {j["entity_id"] for j in inputs["mechanism"].get("Joint", [])}
        placed = {p.get("joint") for p in parsed.get("joint_placements", [])}
        for missing in sorted(joints - placed):
            out.append("joint %s has no placement" % missing)
        configs = {c["entity_id"] for c in inputs["mechanism"].get("Configuration", [])}
        stated = {s.get("configuration") for s in parsed.get("state_coordinates", [])}
        for missing in sorted(configs - stated):
            out.append("configuration %s has no joint coordinates" % missing)
        if len(configs) > 1 and not parsed.get("transitions"):
            out.append("more than one configuration and no transition between them")

        # PROPAGATION. s04b proves motion clear against the blocking relations
        # s03 declared. Where those relations carry no defeat specification, the
        # clearance result rests on a claim nobody specified, and s04b may not
        # report SUCCESS on it. Upstream incompleteness is inherited, not reset.
        unspecified = []
        for mex in inputs["mechanism"].get("MobilityExpectation", []):
            for d in (mex.get("dispositions") or []):
                if not isinstance(d, dict) or d.get("disposition") != "BLOCKED_BY":
                    continue
                if not str(d.get("defeat_specification") or "").strip():
                    unspecified.append("%s/%s/%s" % (d.get("rigid_group"),
                                                     d.get("configuration"), d.get("dof")))
        if unspecified:
            out.append("inherited from s03: %d blocked DOF have no defeat "
                       "specification, so the motion results below rest on "
                       "constraints nobody specified (%s%s)"
                       % (len(unspecified), ", ".join(unspecified[:5]),
                          ", ..." if len(unspecified) > 5 else ""))
        return out


#: Declared once, non-adaptive, with interior samples. Not a tuning knob: a
#: sampling density chosen per case is a density chosen after seeing the answer.
SAMPLES = 9


def required_contacts(mech: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Body pairs the topology says are connected.

    Derived from s03's own joint graph and CONTACT interfaces, so the constraint
    handed to s04a is the producer's statement rather than a rule about products.
    """
    gb = {g["entity_id"]: g.get("body") for g in mech.get("RigidGroup", [])}
    pairs: Set[Tuple[str, str]] = set()
    for j in mech.get("Joint", []):
        a, b = gb.get(j.get("parent_group")), gb.get(j.get("child_group"))
        if a and b and a != b:
            pairs.add(tuple(sorted((a, b))))
    for i in mech.get("Interface", []):
        bodies = [x for x in (i.get("bodies") or []) if isinstance(x, str)]
        if len(bodies) >= 2 and i.get("interaction_kind") in ("CONTACT", "INTERFERENCE_FIT",
                                                              "COMPLIANT_INTERACTION"):
            pairs.add(tuple(sorted(bodies[:2])))
    return sorted(pairs)


def _contact_pairs_text(mech: Dict[str, Any]) -> str:
    pairs = required_contacts(mech)
    if not pairs:
        return "   (the topology declares no connected body pair)"
    return "\n".join("   %s and %s must touch" % p for p in pairs)


def _render(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=1, sort_keys=True)[:26000]
    except Exception:                                                # noqa: BLE001
        return str(obj)[:26000]


# =========================================================================
# the spatial computation and the checks
# =========================================================================
def _boxes(state) -> Dict[str, Tuple[List[float], List[float]]]:
    out = {}
    for e in state.family("Envelope"):
        ext = e.get("extent") or {}
        c, h = ext.get("centre"), ext.get("half_extent")
        if isinstance(c, list) and isinstance(h, list) and len(c) == 3 and len(h) == 3:
            out[e.get("body")] = aabb(c, h)
    return out


def _group_body(state) -> Dict[str, str]:
    return {g["entity_id"]: g.get("body") for g in state.family("RigidGroup")}


def envelope_coverage_check(state) -> List[str]:
    """S04A-C1. Every body has an extent, and every extent belongs to a body.

    The producer-consumer property in its simplest form: s04b cannot place what
    s04a did not size.
    """
    bodies = {b["entity_id"] for b in state.family("Body")}
    placed = {e.get("body") for e in state.family("Envelope")}
    problems = ["BODY_WITHOUT_ENVELOPE: %s" % b for b in sorted(bodies - placed)]
    problems += ["ENVELOPE_FOR_UNKNOWN_BODY: %s" % b
                 for b in sorted(x for x in placed - bodies if x)]
    return problems


def joint_geometry_check(state) -> List[str]:
    """Bodies a joint connects must actually meet.

    Computed, not asserted: two boxes joined by a joint whose envelopes are
    disjoint describe a mechanism whose parts do not touch. This is the check
    that catches an arrangement produced without regard to the topology.
    """
    boxes = _boxes(state)
    mech = {f: [dict(e) for e in state.family(f)]
            for f in ("RigidGroup", "Joint", "Interface")}
    problems = []
    for pb, cb in required_contacts(mech):
        a, b = boxes.get(pb), boxes.get(cb)
        if not (a and b):
            continue
        gap = max(max(a[0][i] - b[1][i], b[0][i] - a[1][i]) for i in range(3))
        if gap > 0:
            problems.append("JOINED_BODIES_DO_NOT_MEET: the topology connects %s "
                            "and %s, but they are placed %.3g apart" % (pb, cb, gap))
    return problems


def configuration_interference_check(state) -> List[str]:
    """S04A-C4. AABB interference per configuration, reported CONSERVATIVELY.

    Overlap of two axis-aligned boxes is NOT proof that the bodies collide, so
    it is never reported as a failure. It is reported as NOT_VERIFIED against
    the interface that declares the pair: if s03 called the pair CLEARANCE and
    the boxes overlap, the clearance is unproven, which is a fact worth having.
    """
    boxes = _boxes(state)
    declared = {}
    for i in state.family("Interface"):
        b = [x for x in (i.get("bodies") or []) if isinstance(x, str)]
        if len(b) >= 2:
            declared[frozenset(b[:2])] = i
    problems = []
    for cfg in state.family("Configuration"):
        present = [b for b in (cfg.get("bodies_present") or []) if b in boxes]
        for x in range(len(present)):
            for y in range(x + 1, len(present)):
                pair = frozenset((present[x], present[y]))
                if not overlaps(boxes[present[x]], boxes[present[y]]):
                    continue
                iface = declared.get(pair)
                kind = (iface or {}).get("interaction_kind")
                if kind == "CLEARANCE":
                    problems.append(
                        "CLEARANCE_NOT_VERIFIED: %s and %s overlap as boxes in %s; "
                        "s03 declared CLEARANCE. Boxes overlapping is not proof of "
                        "collision, so this is NOT_VERIFIED, not a failure"
                        % (present[x], present[y], cfg["entity_id"]))
                elif iface is None:
                    problems.append(
                        "UNDECLARED_PAIR_OVERLAPS: %s and %s overlap as boxes in %s "
                        "and s03 declared no interface between them"
                        % (present[x], present[y], cfg["entity_id"]))
    return problems


def region_occupancy_check(state) -> List[str]:
    """S04B-C3. A declared functional region is not occupied by the bodies that
    promised it.

    An ACCESS region a body sits in is an access the design does not have; a
    KEEP_OUT region a body enters is the promise being broken by the promiser.
    """
    boxes = _boxes(state)
    problems = []
    for r in state.family("FunctionalRegion"):
        vol = r.get("volume")
        if not isinstance(vol, dict):
            problems.append("REGION_WITHOUT_VOLUME: %s" % r["entity_id"])
            continue
        c, h = vol.get("centre"), vol.get("half_extent")
        if not (isinstance(c, list) and isinstance(h, list)):
            problems.append("REGION_VOLUME_MALFORMED: %s" % r["entity_id"])
            continue
        box = aabb(c, h)
        for body in (r.get("owning_bodies") or []):
            if body in boxes and r.get("role") in ("ACCESS", "APERTURE", "KEEP_OUT") \
                    and overlaps(box, boxes[body]):
                problems.append(
                    "REGION_OCCUPIED_BY_ITS_OWNER: %s (%s) overlaps %s"
                    % (r["entity_id"], r.get("role"), body))
    return problems


def sampling_declaration_check(state) -> List[str]:
    """S04B-C1/C2. Sampling is declared, non-adaptive, and has interior samples.

    Endpoint-only evidence is the most effective way to make an unbuildable
    mechanism look correct, because the endpoints are where a designer has
    already looked.
    """
    problems = []
    for t in state.family("Transition"):
        d = t.get("sampling_declaration")
        if not isinstance(d, dict):
            problems.append("SAMPLING_NOT_DECLARED: %s" % t["entity_id"])
            continue
        if d.get("adaptive"):
            problems.append("SAMPLING_ADAPTIVE: %s" % t["entity_id"])
        if int(d.get("interior_samples") or 0) < 1:
            problems.append("SAMPLING_ENDPOINT_ONLY: %s" % t["entity_id"])
    return problems


def swept_clearance_check(state) -> List[str]:
    """S04B. Sweep every moving group along every transition and test occupancy.

    The sweep is computed from the joint placement, the joint's own axis
    direction, and the state coordinates - never from anything the model
    asserted about clearance. A group that sweeps into a KEEP_OUT region or into
    a body it has no declared interface with is reported.
    """
    boxes, gb = _boxes(state), _group_body(state)
    joints = {j["entity_id"]: j for j in state.family("Joint")}
    states = {s["entity_id"]: s for s in state.family("State")}
    placements = {}
    for j in state.family("Joint"):
        o = j.get("frame_origin")
        if isinstance(o, list) and len(o) == 3:
            placements[j["entity_id"]] = o
    declared = set()
    for i in state.family("Interface"):
        b = [x for x in (i.get("bodies") or []) if isinstance(x, str)]
        if len(b) >= 2:
            declared.add(frozenset(b[:2]))
    keepouts = []
    for r in state.family("FunctionalRegion"):
        v = r.get("volume")
        if r.get("role") == "KEEP_OUT" and isinstance(v, dict) \
                and isinstance(v.get("centre"), list):
            keepouts.append((r["entity_id"], aabb(v["centre"], v["half_extent"])))

    problems: List[str] = []
    for t in state.family("Transition"):
        a, b = states.get(t.get("from_state")), states.get(t.get("to_state"))
        if not (a and b):
            problems.append("TRANSITION_ENDPOINT_MISSING: %s" % t["entity_id"])
            continue
        ca = a.get("joint_coordinates") or {}
        cb = b.get("joint_coordinates") or {}
        moving = (t.get("path") or {}).get("moving_groups") or []
        n = int((t.get("sampling_declaration") or {}).get("samples") or SAMPLES)
        for group in moving:
            body = gb.get(group)
            if body not in boxes:
                continue
            # The joint driving this group: the one whose child it is.
            drive = next((j for j in joints.values() if j.get("child_group") == group), None)
            if drive is None or drive["entity_id"] not in placements:
                problems.append("SWEEP_NOT_COMPUTABLE: %s in %s has no placed driving joint"
                                % (group, t["entity_id"]))
                continue
            jid = drive["entity_id"]
            origin = placements[jid]
            axis = str(drive.get("axis_direction") or "+Z")
            q0, q1 = float(ca.get(jid, 0) or 0), float(cb.get(jid, 0) or 0)
            prismatic = str(drive.get("joint_type", "")).upper() == "PRISMATIC"
            hull = None
            for q in sample(q0, q1, n):
                if prismatic:
                    idx = AXIS_INDEX.get(axis.upper().lstrip("+-"), 2)
                    delta = [0.0, 0.0, 0.0]
                    delta[idx] = q * (-1.0 if axis.startswith("-") else 1.0)
                    box = translate(boxes[body], delta)
                else:
                    box = rotate_about_axis(boxes[body], axis, origin, math.radians(q))
                hull = box if hull is None else (
                    [min(hull[0][i], box[0][i]) for i in range(3)],
                    [max(hull[1][i], box[1][i]) for i in range(3)])
            if hull is None:
                continue
            for rid, kbox in keepouts:
                if overlaps(hull, kbox):
                    problems.append("SWEEP_ENTERS_KEEP_OUT: %s sweeps into %s during %s"
                                    % (body, rid, t["entity_id"]))
            for other, obox in boxes.items():
                if other == body or frozenset((body, other)) in declared:
                    continue
                if overlaps(hull, obox):
                    problems.append(
                        "SWEEP_MEETS_UNDECLARED_BODY: %s sweeps into %s during %s; "
                        "s03 declared no interface between them (NOT_VERIFIED: box "
                        "overlap is not proof of collision)"
                        % (body, other, t["entity_id"]))
    return problems


def assembly_path_check(state) -> List[str]:
    """S04B-C4. Each assembly step has a clear insertion path IN THE
    CONFIGURATION PRODUCED BY THE PRECEDING STEPS.

    Against the preceding configuration, not the finished product: a part that
    fits into the empty shell and not into the half-built one is the failure
    this catches, and checking against the final assembly would miss it.
    """
    boxes = _boxes(state)
    steps = sorted(state.family("AssemblyStep"),
                   key=lambda s: s.get("order_index") or 0)
    directions = {}
    for s in steps:
        d = s.get("insertion_direction")
        if isinstance(d, list) and len(d) == 3:
            directions[s["entity_id"]] = d
    problems, placed = [], []
    for s in steps:
        body = s.get("body")
        if body not in boxes:
            placed.append(body)
            continue
        d = directions.get(s["entity_id"])
        if d is None:
            problems.append("ASSEMBLY_DIRECTION_MISSING: %s" % s["entity_id"])
            placed.append(body)
            continue
        norm = math.sqrt(sum(x * x for x in d)) or 1.0
        unit = [x / norm for x in d]
        span = max(max(boxes[b][1][i] - boxes[b][0][i] for i in range(3))
                   for b in boxes) * 2.0
        hull = boxes[body]
        for k in sample(0.0, span, SAMPLES):
            hull = (
                [min(hull[0][i], boxes[body][0][i] - unit[i] * k) for i in range(3)],
                [max(hull[1][i], boxes[body][1][i] - unit[i] * k) for i in range(3)])
        for prior in placed:
            if prior in boxes and overlaps(hull, boxes[prior]):
                problems.append(
                    "ASSEMBLY_PATH_OBSTRUCTED: %s entering along %s meets %s, which "
                    "is already placed (NOT_VERIFIED: box overlap is not proof)"
                    % (body, d, prior))
        placed.append(body)
    return problems


def load_path_reaction_check(state) -> List[str]:
    """S04B-C5. Every provisional load path is confirmed or refuted spatially.

    A path is confirmed when consecutive hops are bodies whose envelopes touch,
    so the load has somewhere to cross. It is refuted when they are disjoint:
    a load cannot pass between bodies that do not meet.
    """
    boxes = _boxes(state)
    problems = []
    for p in state.family("LoadPath"):
        hops = [h for h in (p.get("ordered_hops") or []) if isinstance(h, str)]
        bodies = [h for h in hops if h in boxes]
        for a, b in zip(bodies, bodies[1:]):
            gap = max(max(boxes[a][0][i] - boxes[b][1][i],
                          boxes[b][0][i] - boxes[a][1][i]) for i in range(3))
            if gap > 0:
                problems.append("LOADPATH_HOP_DISJOINT: %s -> %s in %s are "
                                "separated by %.3g; the load cannot cross"
                                % (a, b, p["entity_id"], gap))
    return problems


def selection_gate_check(state) -> List[str]:
    """INV-007. A SelectionDecision may exist only with equal-coverage evidence,
    and a tie is an UnresolvedDecision, never a pick."""
    problems = []
    for d in state.family("SelectionDecision"):
        if not d.get("equal_coverage_confirmed"):
            problems.append("SELECTION_WITHOUT_EQUAL_COVERAGE: %s" % d["entity_id"])
        if not (d.get("evidence") or []):
            problems.append("SELECTION_WITHOUT_EVIDENCE: %s" % d["entity_id"])
    blob = json.dumps([e for e in state.family("SelectionDecision")]).lower()
    for token in ('"score', '"rank', '"best_'):
        if token in blob:
            problems.append("SELECTION_BY_SCORE: %s" % token)
    return problems
