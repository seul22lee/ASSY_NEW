"""S04 - envelope, reach and spatial proof. Two passes, and no gate between them.

The module line used to read "two passes, one selection gate", which S7-A
retired: selection follows s04 entirely, and it follows the feasibility
responsibility that reads this stage's evidence. Nothing here changes - this is
the sentence, not the behaviour.

s04a  Can any of these candidates fit, reach and be approached at all?
      Records a geometric reason where one cannot. Whether that reason makes a
      candidate ineligible is the `feasibility` responsibility's to decide, from
      the whole picture; this stage reports what it computed.
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
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..state.authority import thaw as _thaw
from ..state.patch import Op
from .base import Stage, carry_invocation_premises
#: The canonical DOF vocabulary and the one answer to what a joint frees, read
#: from the pass that owns them rather than restated - two spellings of one
#: closed set is how they drift apart.
from .s03_topology_and_mobility import DOF_NAMES, joint_free_dof

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}

#: The frozen motion-evidence vocabulary. The level records WHAT WAS COMPUTED.
MOTION_EVIDENCE = ("ENDPOINTS_ONLY", "SAMPLED", "SWEPT", "CONTINUOUS")


def axis_index(axis: Any) -> Optional[int]:
    """Which coordinate the axis names, or None.

    NONE IS AN ANSWER. Every caller used to pass through `AXIS_INDEX.get(a, 2)`
    or `axis or "+Z"`, so a joint with no axis, an unrecognised axis and a joint
    genuinely about Z were three different facts that reached the geometry as
    one. A rotation about a fabricated axis produces a swept hull, the hull
    produces a clearance verdict, and nothing in the record says the axis was
    invented. Refusing to compute is the only honest answer to a missing premise.
    """
    if not isinstance(axis, str):
        return None
    return AXIS_INDEX.get(axis.strip().upper().lstrip("+-"))


def axis_sign(axis: str) -> float:
    return -1.0 if str(axis).strip().startswith("-") else 1.0
def _region_policy() -> Dict[str, Dict[str, Any]]:
    """FunctionalRegion.role_policy, read from the canonical contract.

    Read rather than restated. This tuple used to be written here and the
    occupancy subset written twice more - once in s04b below, once in S05-C8 -
    so "which roles exclude occupancy" had three answers that happened to agree.
    """
    from ..state.design_state import Contracts
    families = Contracts().families
    return dict((families.get("FunctionalRegion") or {}).get("role_policy") or {})


#: The declared role vocabulary, in canonical order.
REGION_ROLES = tuple(sorted(_region_policy()))


def excludes_occupancy(role: Optional[str]) -> bool:
    """Is a body or feature being inside a region of this role a defect?

    THE one interpreter, used by s04b's occupancy check and by S05-C8, so the
    two stages cannot come to different conclusions about the same box. A role
    the contract does not declare returns False and is reported by the caller
    as unrecognised rather than silently treated as keep-out.
    """
    policy = _region_policy().get(str(role or "").strip().upper()) or {}
    return bool(policy.get("excludes_occupancy"))


def unknown_region_role(role: Optional[str]) -> bool:
    """A role outside the declared vocabulary. Never silently ignored."""
    return str(role or "").strip().upper() not in _region_policy()

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
    idx = axis_index(axis)
    if idx is None:
        raise ValueError("no usable axis: %r. Rotating about a fabricated axis "
                         "produces a hull, and the hull produces a verdict" % (axis,))
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

    Interior points are what make a sweep more than a pair of poses, and the ends
    are exactly where a designer has already checked - so a computation that
    evaluates only them is weak evidence. It is not FORBIDDEN evidence: the level
    records which was done, and whether it suffices belongs to the claim being
    made, not to the sampler.
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


def _branch(inputs) -> str:
    """The candidate this invocation embodies, as an id fragment.

    s04 runs once per alternative, so every id it mints must be that
    alternative's. `SCL-0001` and `ELM-0001` were module constants: the second
    candidate collided with the first and could not have a scale or an
    elimination record at all - the same defect S-5 found in `MEX-0001`, in a
    different family. The fragment is the candidate id, which is recomputable
    where a counter is not.
    """
    c = (inputs or {}).get("candidate")
    if isinstance(c, dict):
        c = c.get("entity_id")
    return c if isinstance(c, str) and c else "UNBRANCHED"


class S04AEnvelopeAndReach(Stage):
    # Both passes are s04. The contract calls them PASSES of one stage, and the
    # ownership matrix owns families at stage granularity, so a pass id here
    # would make every entity this stage creates ownerless.
    stage_id = "s04"
    pass_id = "s04a"
    purpose = "give the topology a provisional arrangement so feasibility can be computed"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        return S04A_PROMPT.format(mechanism=_render(inputs["consumer_view"]),
                                  contact_pairs=_contact_pairs_text(inputs["consumer_view"]))

    def invocation_premises(self, inputs: Dict[str, Any]) -> List[str]:
        """The candidate this arrangement embodies. s04 runs once per alternative
        and everything it authors is that alternative's (FA-5)."""
        b = _branch(inputs)
        return [b] if b != "UNBRANCHED" else []

    #: The class every s04a spatial value is committed at. COMPARABLE because
    #: that is what this pass is FOR: an arrangement alternatives are judged
    #: against. Weaker than AUTHORITATIVE, which no packaging argument earns, and
    #: stronger than PROVISIONAL, which would say nothing may rest on it.
    COMMITMENT_CLASS = "COMPARABLE"

    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        """EVERYTHING THIS PASS CONCLUDED, committed by the pass that concluded it.

        The scale, the reach results and the elimination record used to be read
        out of the raw response by `tools/run_window2._commit_s04` AFTER the
        stage returned. They are s04a's engineering conclusions, so a caller that
        did not run that second step got a DesignState without them and nothing
        saying any were missing - and a runner deciding what a response means is
        a second semantic authority for one stage's output.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s04a:arrangement"
        scale = parsed.get("scale") or {}
        premises: List[str] = []
        # THE BASIS FIRST. Every coordinate below is expressed in it, so it is
        # their premise: withdraw the basis and the numbers mean nothing, which
        # FA-5 then says about every value that cited it.
        branch = _branch(inputs)
        if scale.get("basis"):
            ops.append(Op("CREATE", "ReferenceScale", "SCL-%s" % branch, {
                "basis": scale.get("basis"), "absolute": scale.get("absolute"),
                "note": scale.get("note"),
                "commitment_class": self.COMMITMENT_CLASS}, prov))
            premises = ["SCL-%s" % branch]
        for e in parsed.get("envelopes", []):
            ops.append(Op("CREATE", "Envelope", e["id"], {
                "body": e["body"],
                "extent": {"half_extent": e["half_extent"], "centre": e["centre"]},
                "frame": "world",
                "maturity": e.get("maturity", "PROVISIONAL"),
                "commitment_class": self.COMMITMENT_CLASS,
                "scale_basis": scale.get("basis", "RELATIVE")},
                prov, premise_refs=list(premises)))
        for i, r in enumerate(parsed.get("reach_results") or [], start=1):
            ops.append(Op("CREATE", "ReachResult", "RCH-%s-%04d" % (branch, i), {
                "actor": r.get("actor"), "target": r.get("target"),
                "reachable": r.get("reachable"),
                "approach_side": r.get("approach_side"), "why": r.get("why")},
                prov, premise_refs=list(premises)))
        elim = parsed.get("elimination")
        if isinstance(elim, dict) and elim.get("eliminated") is not None:
            fields = {"eliminated": elim.get("eliminated"),
                      "reason": elim.get("reason")}
            # The candidate is a declared REFERENCE, so it is written only where
            # this invocation actually names one. "UNBRANCHED" is an id fragment
            # for minting, never an entity - putting it in a reference field
            # would be prose in a place R-20 calls a schema error.
            if branch != "UNBRANCHED":
                fields["candidate"] = branch
            ops.append(Op("CREATE", "EliminationRecord", "ELM-%s" % branch,
                          fields, prov, premise_refs=list(premises)))
        return ops

    def refinement_operations(self, parsed, inputs, state) -> List[Op]:
        """The volumes and directions this pass adds to entities s03 created.

        EXTEND, because they are properties OF an existing entity and the
        contract declares s04 as the extender of exactly these two fields. A
        target this consumer was not given is REPORTED by `completeness` and not
        written: inventing the entity would be worse, and writing onto one this
        invocation cannot see would be reaching outside its own branch.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        view = inputs.get(self.context_key) or {}
        known = {e.get("entity_id") for fam in view.values() if isinstance(fam, list)
                 for e in fam if isinstance(e, dict)}
        prov = "s04a:arrangement"
        # The basis, and only the basis. A region volume and an insertion
        # direction are COORDINATES on entities s03 owns, so withdrawing the
        # basis costs them their meaning - and nothing else s04a produced is a
        # premise of them.
        premises = (["SCL-%s" % _branch(inputs)]
                    if (parsed.get("scale") or {}).get("basis") else [])
        ops: List[Op] = []
        for r in parsed.get("region_volumes") or []:
            target = r.get("functional_region")
            if target in known and state.has_entity(target):
                ops.append(Op("EXTEND", state.stored_family(target), target,
                              {"volume": {"half_extent": r.get("half_extent"),
                                          "centre": r.get("centre")}},
                              prov, premise_refs=list(premises)))
        for a in parsed.get("assembly_directions") or []:
            target = a.get("assembly_step")
            if target in known and state.has_entity(target):
                ops.append(Op("EXTEND", state.stored_family(target), target,
                              {"insertion_direction": a.get("direction")},
                              prov, premise_refs=list(premises)))
        return ops

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        bodies = {b["entity_id"] for b in inputs["consumer_view"].get("Body", [])}
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
        for pb, cb in required_contacts(inputs["consumer_view"]):
            a, b = boxes.get(pb), boxes.get(cb)
            if not (a and b):
                continue
            gap = box_gap(a, b)
            if gap > 0:
                apart.append("%s and %s placed %.3g apart" % (pb, cb, gap))
        if apart:
            out.append("%d body pair(s) the topology connects are placed apart: %s"
                       % (len(apart), "; ".join(apart[:6])
                          + ("; ..." if len(apart) > 6 else "")))

        regions = {r["entity_id"] for r in inputs["consumer_view"].get("FunctionalRegion", [])}
        volumed = {r.get("functional_region") for r in parsed.get("region_volumes", [])}
        for missing in sorted(regions - volumed):
            out.append("functional region %s has no volume" % missing)
        # A TARGET THIS CONSUMER WAS NOT GIVEN. Not committed - inventing the
        # entity would be worse - and not silent either, which is ADR-001's own
        # property: the historical path dropped it with `if e is not None`, and
        # the drop was invisible. It was recorded by the runner that did the
        # writing; now the stage that made the claim records it.
        known = {e.get("entity_id") for fam in inputs["consumer_view"].values()
                 if isinstance(fam, list) for e in fam if isinstance(e, dict)}
        for r in parsed.get("region_volumes") or []:
            if r.get("functional_region") not in known:
                out.append("region volume names %s, which this consumer was not "
                           "given, so it was not committed"
                           % r.get("functional_region"))
        for a in parsed.get("assembly_directions") or []:
            if a.get("assembly_step") not in known:
                out.append("assembly direction names %s, which this consumer was "
                           "not given, so it was not committed"
                           % a.get("assembly_step"))
        return out


# =========================================================================
# s04b
# =========================================================================
S04B_PROMPT = """You are placing a mechanism in space and describing how it moves,
so that a later step can test whether the motion is actually clear.

You receive the mechanism, its provisional arrangement, and the state changes it
is required to be able to perform. You do not receive the original request.

WHAT YOU ARE DECIDING
1. Where each JOINT sits - its frame origin, as a position in the same
   coordinates as the arrangement you were given, and the axis it turns or slides
   about. The direction is already fixed by the topology; you are placing it.
2. For every configuration, the COORDINATE of every joint in that configuration -
   an angle in degrees for a revolute or compliant joint, a distance for a
   prismatic one, in the same relative units.
3. How each state change the mechanism is REQUIRED to perform is carried out in
   numbers: which joints move, by how much, and which groups move relative to
   each other. You are not deciding WHICH state changes are required or which
   two states each one runs between - those were decided when the mechanism was
   described, and they are in the input as transition requirements.

Do not state that anything is clear, interferes, or sweeps through anything. You
cannot see that and are not being asked: it is computed from your numbers.

RESPONSE SCHEMA
Return a single JSON object with these keys.

  joint_placements[]   joint, origin [x,y,z]
  state_coordinates[]  configuration, coordinates {{<joint id>: number}}
  transitions[]        id "TRN-0001", realizes_requirement, moving_groups[],
                       changed_coordinates[] (the joint ids whose coordinate this
                       transition changes - it is checked against your own
                       endpoint coordinates, so declare exactly the ones that
                       differ between them)
                       ONE PER TRANSITION REQUIREMENT in the input, and the
                       endpoints are NOT yours to state: the requirement already
                       says which configuration it goes from and to, and
                       restating them would be a second answer to a question that
                       has one. Name the requirement in realizes_requirement and
                       give the coordinates that carry it out.
  envelope_revisions[] envelope, half_extent [x,y,z], centre [x,y,z],
                       geometric_reason - ONLY where placing the mechanism shows
                       the arrangement you were given cannot hold. The
                       arrangement is a COMMITMENT: you extend it by default, and
                       changing one is a supersession that needs a geometric
                       reason. Both values are kept and everything resting on the
                       old one loses standing, so this is a real act and not a
                       correction. Omit it when you are extending, which is
                       almost always.
  notes                string, may be ""

WHERE EACH JOINT'S AXIS COMES FROM
The topology already fixed each joint's axis DIRECTION. You are placing the
origin on that axis, not choosing a new one. A joint whose axis the topology did
not fix cannot be given one here: say so in notes rather than picking a
direction, because a placement on an invented axis produces motion evidence for a
mechanism that does not exist.

REFERENCES
  joint_placements[].joint           a joint id from the input
  state_coordinates[].configuration  a configuration id from the input
  transitions[].realizes_requirement a transition requirement id from the input
  transitions[].moving_groups        rigid group ids from the input - the groups
                                     that move relative to each other. For each
                                     joint whose coordinate changes, name at
                                     least one of the two groups that joint
                                     connects; either side may be the one that
                                     travels, and both may.
  transitions[].changed_coordinates  joint ids from the input
  envelope_revisions[].envelope      an envelope id from the input

THE MECHANISM AND ITS ARRANGEMENT
{mechanism}
"""




def incident_joints(joints, group):
    """Every joint that relates this group to another. EITHER SIDE OF IT.

    A joint states a RELATIVE relation between two groups, and which of them is
    written as the parent is not a statement about either. Matching only on
    `child_group` asked "which joints hang off this group" and called the answer
    "which joints move it" - so the same mechanism described the other way round
    got a different verdict, and a group that is only ever a parent had no joint
    at all.
    """
    return [j for j in joints
            if group in (j.get("parent_group"), j.get("child_group"))]


def distinctness_findings(configurations, coordinates, joints):
    """(findings, read) for whether DECLARED distinctness is numerically real.

    ONE IMPLEMENTATION, TWO READERS: the pass that writes the coordinates asks it
    of the response it is about to write, and feasibility asks it of the records
    that were written. A producer that accepts numbers an evaluator then convicts
    is one question with two answers, the second arriving too late to act on.

    THE BASIS NAMES ITS OWN JOINT. It used to name a rigid group, and no rigid
    group has a coordinate - so every consumer had to decide WHICH joint
    expressed that group's named DOF, and every way of deciding was a convention
    rather than a fact. Taking the joint whose CHILD is the group read a relative
    relation as a statement about which side moves; taking any incident joint
    made the middle link of G1-[J1]-G2-[J2]-G3 ambiguous because it touches two.
    The producer names the joint, this reads it, and a name that resolves to
    nothing is reported rather than replaced by a guess.

    WHAT THIS IS NOT. `distinguishing_basis` says two named states hold different
    values of one named coordinate, and this checks that the numbers agree. It is
    NOT a statement that either state is reachable from the other - that demand is
    a TransitionRequirement and `transition_reachability` answers it - and it
    identifies no moving body, so a joint's parent and child may be written
    either way round without changing any verdict here.

    A NAMED REFERENCE IS AN ADDRESS. `differs_from` names the siblings this
    configuration must differ from; each is evaluated exactly, and one that is
    absent or has no coordinates leaves the comparison unestablished rather than
    passed by whatever else happens to be realized.

    A finding is (code, note, refs). `read` is every entity consulted INCLUDING
    on the paths that found nothing: the joint whose coordinate decided that two
    states really do differ is what a PASS was computed from, so withdrawing it
    must cost that PASS its standing.

    `coordinates` is {configuration id: {joint id: number}} - whatever the caller
    can see.
    """
    by_id = {j.get("entity_id"): j for j in (joints or []) if isinstance(j, dict)}
    out: List[Tuple[str, str, List[str]]] = []
    read: List[str] = []
    for cfg in (configurations or []):
        if not isinstance(cfg, dict):
            continue
        cid = cfg.get("entity_id") or cfg.get("id")
        for item in (cfg.get("distinguishing_basis") or []):
            if not isinstance(item, dict):
                continue
            jid, dof = item.get("joint"), item.get("dof")
            named = [o for o in (item.get("differs_from") or [])
                     if isinstance(o, str) and o]
            read.append(cid)
            if not named:
                # "different" with nothing to be different from. Comparing
                # against everything else would be inventing the sibling.
                out.append(("DISTINCTNESS_NAMES_NO_SIBLING",
                            "%s declares a basis on %s/%s and names no sibling"
                            % (cid, jid, dof), [cid]))
                continue
            joint = by_id.get(jid)
            if not isinstance(joint, dict):
                out.append(("DISTINCTNESS_JOINT_NOT_VISIBLE",
                            "%s declares a basis on %s, which is no joint of "
                            "this candidate" % (cid, jid), [cid]))
                continue
            read.append(jid)
            free = joint_free_dof(joint)
            if dof not in free:
                # A joint that does not free this degree of freedom has no
                # coordinate in it, so there is no value for the comparison to
                # read. Substituting one it DOES free would answer a different
                # question from the one the design asked.
                out.append(("DISTINCTNESS_DOF_NOT_SUPPORTED",
                            "%s declares a basis on %s/%s and that joint "
                            "declares %s"
                            % (cid, jid, dof, ", ".join(sorted(free)) or "no free DOF"),
                            [cid, jid]))
                continue
            if len(free) > 1:
                # MULTI-DOF HONESTY. `State.joint_coordinates` holds ONE scalar
                # per joint, so on a joint freeing several it cannot say which
                # of them a value is about. Reading the scalar as the named DOF
                # would manufacture evidence for exactly the degree of freedom
                # under question.
                out.append(("DISTINCTNESS_COORDINATE_NOT_RESOLVABLE",
                            "%s declares a basis on %s/%s and that joint frees "
                            "%s; one coordinate per joint cannot say which of "
                            "them a value is about"
                            % (cid, jid, dof, ", ".join(sorted(free))),
                            [cid, jid]))
                continue
            if cid not in coordinates:
                out.append(("DISTINCTNESS_NOT_REALIZED_HERE",
                            "%s declares a basis and no coordinates are stated "
                            "for it" % cid, [cid]))
                continue
            q = (coordinates.get(cid) or {}).get(jid)
            for other in named:
                read.append(other)
                if other not in coordinates:
                    out.append(("DISTINCTNESS_SIBLING_NOT_REALIZED",
                                "%s must differ from %s, for which no coordinates "
                                "are stated" % (cid, other), [cid, other, jid]))
                    continue
                p = (coordinates.get(other) or {}).get(jid)
                if q is None or p is None:
                    out.append(("DISTINCTNESS_COORDINATE_MISSING",
                                "%s and %s do not both state a coordinate for %s"
                                % (cid, other, jid), [cid, other, jid]))
                    continue
                if q == p:
                    out.append(("DECLARED_DISTINCTNESS_NOT_REALIZED",
                                "%s and %s both realize %s at %r"
                                % (cid, other, jid, q), [cid, other, jid]))
    return out, sorted({r for r in read if isinstance(r, str) and r})


def realization_findings(requirement, realizations, coordinates, joints):
    """(code, note) for ONE demanded state change and what claims to realize it.

    ONE IMPLEMENTATION, TWO READERS. The pass that writes a realization asks this
    of the response it is about to write; feasibility asks it of the records that
    were written. Two rules about one question is how a producer comes to accept
    what an evaluator then rejects for a reason the producer could have given, so
    the matching lives here once and each caller decides only what a finding
    COSTS - incompleteness on one side, a domain status on the other.

    WHAT IS NOT READ. Not `distinguishing_basis`: two states differing is not a
    demand that either be reachable. Not which side of a joint is its child: a
    joint states a RELATIVE relation, so either incident group moving establishes
    the motion and reversing parent and child changes no finding. Not names, not
    ordering, not counts - only the fields the demand and the realization state.

    `realizations` are dicts of id, from_configuration, to_configuration (None
    where the endpoint record is absent), moving_groups and changed_coordinates.
    `coordinates` is {configuration: {joint id: number}} and `joints` is
    {joint id: joint}, both as the caller can see them.
    """
    rid = requirement.get("entity_id") or requirement.get("id")
    frm = requirement.get("from_configuration")
    to = requirement.get("to_configuration")
    required = [m for m in (requirement.get("required_relative_motions") or [])
                if isinstance(m, dict)]
    out: List[Tuple[str, str]] = []

    # A. THE TOPOLOGY HAS TO HAVE THE FREEDOM THE DEMAND NEEDS. Asked of the
    # joint's own declared DOF through the one reader of that field, so this
    # agrees with every other consumer of it by construction.
    for motion in required:
        jid, dof = motion.get("joint"), motion.get("dof")
        joint = joints.get(jid)
        if not isinstance(joint, dict):
            out.append(("JOINT_ABSENT",
                        "%s requires %s to move and no such joint is visible"
                        % (rid, jid)))
            continue
        free = joint_free_dof(joint)
        if dof not in free:
            out.append(("DOF_NOT_SUPPORTED",
                        "%s requires %s/%s and that joint declares %s"
                        % (rid, jid, dof, ", ".join(sorted(free)) or "no free DOF")))

    # B. exactly one realization
    if not realizations:
        out.append(("NO_REALIZATION",
                    "%s demands a change from %s to %s and nothing realizes it"
                    % (rid, frm, to)))
        return out
    if len(realizations) > 1:
        out.append(("REALIZED_MORE_THAN_ONCE",
                    "%s is realized %d times (%s); a demand realized more than "
                    "once has no single answer"
                    % (rid, len(realizations),
                       ", ".join(sorted(str(r.get("id")) for r in realizations)))))
    t = realizations[0]
    tid = t.get("id")

    # C. and it has to run between the two states the demand names
    if t.get("from_configuration") is None or t.get("to_configuration") is None:
        out.append(("ENDPOINT_STATE_ABSENT",
                    "%s has an endpoint that resolves to no state, so what it "
                    "connects is not established" % tid))
        return out
    if (t.get("from_configuration"), t.get("to_configuration")) != (frm, to):
        out.append(("ENDPOINT_MISMATCH",
                    "%s demands %s -> %s and %s connects %s -> %s"
                    % (rid, frm, to, tid, t.get("from_configuration"),
                       t.get("to_configuration"))))
        return out
    for cfg in (frm, to):
        if cfg not in coordinates:
            out.append(("ENDPOINT_COORDINATES_ABSENT",
                        "%s ends at configuration %s and no coordinates are "
                        "stated for it" % (rid, cfg)))
    if frm not in coordinates or to not in coordinates:
        return out

    changed = [c for c in (t.get("changed_coordinates") or []) if isinstance(c, str)]
    moving = [g for g in (t.get("moving_groups") or []) if isinstance(g, str)]
    for motion in required:
        jid, dof = motion.get("joint"), motion.get("dof")
        joint = joints.get(jid) or {}
        a, b = coordinates[frm].get(jid), coordinates[to].get(jid)
        if a is None or b is None:
            out.append(("REQUIRED_COORDINATE_ABSENT",
                        "%s requires %s to move and %s has no coordinate for it "
                        "in %s" % (rid, jid, tid, frm if a is None else to)))
            continue
        try:
            unchanged = float(a) == float(b)
        except (TypeError, ValueError):
            out.append(("REQUIRED_COORDINATE_NOT_A_NUMBER",
                        "%s requires %s to move and its endpoint coordinates are "
                        "not numbers" % (rid, jid)))
            continue
        if unchanged:
            out.append(("REQUIRED_MOTION_NOT_REALIZED",
                        "%s requires %s to move and its coordinate is %s at both "
                        "ends" % (rid, jid, a)))
        if jid not in changed:
            out.append(("REQUIRED_MOTION_NOT_DECLARED",
                        "%s requires %s to move and %s does not list it among "
                        "the coordinates it changes" % (rid, jid, tid)))
        # E. EITHER INCIDENT GROUP. The joint relates two groups and says nothing
        # about which of them travels; requiring the child would be reading a
        # relative orientation as an absolute one. Naming nothing and naming
        # something unrelated are different answers: one has not said what moves,
        # the other has said something that does not answer the demand.
        incident = {joint.get("parent_group"), joint.get("child_group")}
        incident.discard(None)
        if not moving:
            out.append(("MOVING_SIDE_ABSENT",
                        "%s requires %s to move and %s names nothing that moves"
                        % (rid, jid, tid)))
        elif incident and not (incident & set(moving)):
            out.append(("MOVING_SIDE_UNRELATED",
                        "%s requires %s to move and %s names no group of that "
                        "joint among what moves (%s)"
                        % (rid, jid, tid, ", ".join(sorted(moving)))))
        # MULTI-DOF HONESTY. One scalar per joint cannot say WHICH degree of
        # freedom of a multi-DOF joint it moved, and guessing would manufacture
        # evidence for the required one.
        free = sorted(d for d in joint_free_dof(joint) if d in DOF_NAMES)
        if len(free) > 1:
            out.append(("REQUIRED_DOF_NOT_RESOLVABLE",
                        "%s requires %s/%s and that joint declares %s; one "
                        "coordinate per joint cannot say which of them moved, so "
                        "the required motion is not established by these numbers"
                        % (rid, jid, dof, ", ".join(free))))
    # THE OTHER DIRECTION. A coordinate claimed to change whose endpoints are
    # equal is a positive contradiction of the realization's own claim, and is
    # checked here so neither a silent omission nor a silent addition passes.
    for jid in changed:
        a, b = coordinates[frm].get(jid), coordinates[to].get(jid)
        if a is None or b is None:
            continue
        try:
            if float(a) == float(b):
                out.append(("DECLARED_CHANGE_NOT_REALIZED",
                            "%s lists %s among the coordinates it changes and "
                            "its endpoints are both %s" % (tid, jid, a)))
        except (TypeError, ValueError):
            pass
    return out


class S04BPlacementAndMotion(Stage):
    stage_id = "s04"
    pass_id = "s04b"
    purpose = "place the mechanism and describe its motion so clearance can be computed"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        return S04B_PROMPT.format(mechanism=_render(inputs["consumer_view"]))

    def invocation_premises(self, inputs: Dict[str, Any]) -> List[str]:
        b = _branch(inputs)
        return [b] if b != "UNBRANCHED" else []

    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        """The states and transitions. NO sampling declaration.

        `sampling_declaration` used to be written here, from the module constant,
        before any sweep had run - so the record of how the motion was evidenced
        existed before the motion was computed, and the sweep then read its own
        density back out of it. The declaration is written by
        `derived_operations` from what the computation actually evaluated, and a
        transition whose motion could not be computed carries none.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s04b:placement"
        view = (inputs or {}).get(self.context_key) or {}
        # NO REALIZATION IS WRITTEN FROM NUMBERS THAT CONTRADICT THE DESIGN.
        #
        # EVERY state, not the contradicted pair. The coordinates are ONE answer:
        # the model chose them together to realize a mechanism, and keeping the
        # subset that happens not to collide would commit a realization nobody
        # produced. Withholding them cascades correctly - a transition whose
        # endpoint states were not written is skipped below, and the sweep that
        # would have been computed from them is skipped in `derived_operations`.
        #
        # The joint PLACEMENTS still commit. Where a joint sits is a separate
        # fact that these coordinates do not contradict, and this is the shape
        # the refinement barrier already uses: commit what stands, withhold the
        # realization, and let the caller ask again.
        refused = self._contradicted_distinctness(parsed, inputs)
        for st in ([] if refused else parsed.get("state_coordinates", [])):
            coords = st.get("coordinates", {})
            ops.append(Op("CREATE", "State", "STA-%s" % st["configuration"], {
                "name": st["configuration"],
                "configuration": st["configuration"],
                "joint_coordinates": coords},
                prov, premise_refs=self._state_premises(
                    view, st["configuration"], coords)))
        # THE ENDPOINTS COME FROM THE REQUIREMENT, and from nowhere else. The
        # model used to state them, which made s03b and s04b two authors of the
        # same fact with nothing comparing them; a transition that named the
        # wrong pair was a realization of nothing, indistinguishable from one
        # that named the right pair. Resolving them here gives the topology one
        # owner. A requirement this consumer was not given resolves to nothing
        # and is REPORTED by `completeness` - the operation is not written,
        # because inventing the endpoints is the defect being removed.
        demanded = {r.get("entity_id"): r
                    for r in (view.get("TransitionRequirement") or [])
                    if isinstance(r, dict)}
        realized = {st.get("configuration") for st in
                    ([] if refused else parsed.get("state_coordinates", []))}
        for t in ([] if refused else parsed.get("transitions", [])):
            required = demanded.get(t.get("realizes_requirement"))
            if required is None:
                continue
            # AND THE ENDPOINT STATES HAVE TO EXIST. A demand can name a
            # configuration this response stated no coordinates for; the
            # endpoint is then a state nothing wrote, and a path to it would be
            # a reference to a record that does not exist. `completeness`
            # reports the missing coordinates - the path is simply not written.
            if not {required.get("from_configuration"),
                    required.get("to_configuration")} <= realized:
                continue
            ops.append(Op("CREATE", "Transition", t["id"], {
                "from_state": "STA-%s" % required.get("from_configuration"),
                "to_state": "STA-%s" % required.get("to_configuration"),
                "realizes_requirement": t["realizes_requirement"],
                "path": {"moving_groups": t.get("moving_groups", [])},
                "changed_coordinates": t.get("changed_coordinates", [])},
                prov, premise_refs=self._transition_premises(view, t)))
        return ops

    # ------------------------------------------------------ dependency graph
    #
    # A PREMISE IS REQUIRED IFF CHANGING IT CAN CHANGE THIS PRODUCED VALUE. When
    # this was written propagation stopped after one hop, so every derived value
    # had to name every fact it was actually made from or a chain of
    # individually-correct links carried no staleness along itself. S7-F made the
    # walk transitive; the lists below are unchanged, because naming what a value
    # was made from is what provenance IS - the walk decides currentness, not
    # what the record is allowed to say about itself.
    #
    # This replaces one list - every envelope in the view, on every s04b output -
    # which was wrong in both directions at once. TOO MUCH: a state's coordinates
    # are angles and distances computed from no extent at all, and a sweep reads
    # exactly one body's box, so resizing an unrelated body staled realizations it
    # cannot affect, which teaches a reader to ignore STALE. TOO LITTLE: none of
    # them named the Configuration, the endpoint States, the Transition or the
    # moving RigidGroup, so changing an endpoint coordinate left the swept
    # occupancy STANDING with a hull computed from the coordinate just replaced.

    def _scale_premise(self, view) -> List[str]:
        """The basis the numbers are in. A premise of every s04 spatial value,
        which is the contract's own words: "a coordinate has no meaning without
        the basis it is expressed in"."""
        return sorted({r["entity_id"] for r in (view.get("ReferenceScale") or [])
                       if isinstance(r, dict) and r.get("entity_id")})

    def _state_premises(self, view, configuration, coordinates) -> List[str]:
        """What a realized configuration rests on.

        The Configuration it realizes - withdraw it and these coordinates realize
        nothing - and the Joints they are coordinates OF. NOT the envelopes: a
        joint angle is not computed from a body's extent, and saying it was makes
        an unrelated resize look like it invalidated the kinematics.
        """
        out = {configuration} if configuration else set()
        out |= {j for j in (coordinates or {}) if isinstance(j, str)}
        return sorted(out | set(self._scale_premise(view)))

    @staticmethod
    def _endpoints(view, t) -> Tuple[Optional[str], Optional[str]]:
        """The configurations a transition connects, READ FROM ITS REQUIREMENT.

        One owner for endpoint topology. Everything in this pass that needs to
        know where a transition starts and ends asks here, so the premise list,
        the swept motion and the written operation cannot disagree about it -
        which they could when each read a field the model restated.
        """
        for r in (view.get("TransitionRequirement") or []):
            if isinstance(r, dict) and r.get("entity_id") == t.get("realizes_requirement"):
                return r.get("from_configuration"), r.get("to_configuration")
        return None, None

    def _transition_premises(self, view, t) -> List[str]:
        """Its requirement, its endpoints, what moves, and what it says changes.

        THE REQUIREMENT IS A PREMISE. It decides the endpoints and the motion
        this realization has to carry out, so withdrawing or revising it costs
        the realization its standing - which is what a premise means, and what
        the transitive walk then applies to everything computed from it.
        """
        frm, to = self._endpoints(view, t)
        out = {"STA-%s" % frm if frm else None,
               "STA-%s" % to if to else None,
               t.get("realizes_requirement")}
        out |= {g for g in (t.get("moving_groups") or []) if isinstance(g, str)}
        out |= {j for j in (t.get("changed_coordinates") or []) if isinstance(j, str)}
        return sorted({x for x in out if isinstance(x, str) and x}
                      | set(self._scale_premise(view)))

    def _sweep_premises(self, view, t, group, joint_id, envelope_id) -> List[str]:
        """Exactly what `sweep_hull` read to produce this occupancy.

        The transition and the moving group it is about, both endpoint states
        whose coordinates it swept between, the driving joint - whose type, axis
        and frame origin decide the geometry - and the ONE envelope whose box was
        swept. Change any of them and this hull is wrong; change any other
        envelope and it is not.
        """
        frm, to = self._endpoints(view, t)
        out = {t.get("id"), group, joint_id, envelope_id,
               "STA-%s" % frm if frm else None,
               "STA-%s" % to if to else None}
        return sorted({x for x in out if isinstance(x, str) and x}
                      | set(self._scale_premise(view)))

    def _coordinate_premises(self, view) -> List[str]:
        """What a coordinate added to somebody else's entity rests on.

        THE BASIS, AND NOT THE EXTENTS. Premises recorded on an EXTEND land on
        the ENTITY - `_merge_premises` has no field granularity - so whatever is
        named here decides the standing of the whole Joint. The basis belongs:
        withdraw it and `frame_origin` is a triple of numbers meaning nothing,
        which is the contract's own words and the property ADR-001 pins. The
        other bodies' extents do not: resizing one would then say the TOPOLOGY
        had lost authority because a body got bigger.

        What depends on the placement geometrically is the swept occupancy, and
        it names the Joint and the one swept envelope directly.
        """
        return self._scale_premise(view)

    def refinement_operations(self, parsed, inputs, state) -> List[Op]:
        """Joint placement, and any supersession of the s04a arrangement.

        TWO KINDS OF REFINEMENT, and the difference is the whole of U-7. Placing
        a joint EXTENDS what s04a left open - s04a sized bodies and said nothing
        about where axes sit - and needs no reason because it contradicts
        nothing. Changing an envelope SUPERSEDES a standing commitment, so it
        carries a geometric reason and both values are retained; a revision
        without one is refused rather than applied, because a silent
        contradiction of a binding commitment is the defect this step exists to
        make impossible.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        view = inputs.get(self.context_key) or {}
        known = {e.get("entity_id") for fam in view.values() if isinstance(fam, list)
                 for e in fam if isinstance(e, dict)}
        prov = "s04b:placement"
        premises = self._coordinate_premises(view)
        ops: List[Op] = []
        for p in parsed.get("joint_placements") or []:
            target = p.get("joint")
            if target in known and state.has_entity(target):
                ops.append(Op("EXTEND", state.stored_family(target), target,
                              {"frame_origin": p.get("origin")},
                              prov, premise_refs=list(premises)))
        return ops + self._revision_ops(parsed, inputs, state)

    def _revision_ops(self, parsed, inputs, state) -> List[Op]:
        """The justified supersessions of the arrangement, and only those.

        ONE reader, because the barrier and the commit must agree about what
        counts as a revision. If the barrier fired on a revision this refused, an
        invocation would withhold its realization and commit nothing - a stall
        with no cause a reader could see.

        A revision is applicable when it names an envelope this consumer was
        given, states a geometric reason, and actually carries a new extent.
        Anything else is not applied: `completeness` reports a revision with no
        reason, and a commitment contradicted without one is the defect the
        commitment class exists to prevent.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        view = inputs.get(self.context_key) or {}
        known = {e.get("entity_id") for fam in view.values() if isinstance(fam, list)
                 for e in fam if isinstance(e, dict)}
        ops: List[Op] = []
        for r in parsed.get("envelope_revisions") or []:
            target = r.get("envelope")
            why = str(r.get("geometric_reason") or "").strip()
            if target not in known or not state.has_entity(target) or not why:
                continue
            if not (isinstance(r.get("half_extent"), list)
                    and isinstance(r.get("centre"), list)):
                continue
            ops.append(Op("SUPERSEDE", state.stored_family(target), target,
                          {"extent": {"half_extent": r["half_extent"],
                                      "centre": r["centre"]}},
                          "s04b:placement", reason=why))
        return ops

    def refinement_barrier(self, parsed, inputs, state):
        """A revised arrangement is committed alone, then reasoned from.

        Everything else this response proposes - the joint origins, the state
        coordinates, the transitions - was decided against the extents in the
        view, and the revision replaces them. Committing both in one patch put a
        swept occupancy computed from the OLD extent into state as current
        evidence for the NEW one, and it did not even go stale: it is created
        after the supersession, so it was never a dependent of it.

        The realization is not discarded. It is withheld until the premises it
        rests on are the ones the design now holds.
        """
        ops = self._revision_ops(parsed, inputs, state)
        if not ops:
            return None
        return (ops,
                "%d arrangement commitment(s) superseded with a geometric reason; "
                "the realization is withheld until it can be reasoned from the "
                "revised arrangement: %s"
                % (len(ops), ", ".join(sorted(o.entity_id for o in ops))))

    def derived_operations(self, parsed, inputs, state) -> List[Op]:
        """The swept occupancy, and the evidence level OF ITS OWN COMPUTATION.

        Class B: recomputable from the placement, the joint's own axis and the
        endpoint coordinates, and produced only where those premises are present.
        A transition whose sweep is not computable gets no SweptVolume and no
        declaration - the absence is the honest record, and `motion_evidence_check`
        reports it rather than this code filling it in.
        """
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        # NOTHING IS COMPUTED FROM A REALIZATION THAT WAS NOT WRITTEN. The same
        # gate `to_operations` applies: an occupancy swept between endpoint
        # states no patch created would reference records that do not exist, and
        # a hull computed from numbers the design contradicts is evidence for a
        # mechanism nobody realized.
        if self._contradicted_distinctness(parsed, inputs):
            return carry_invocation_premises([], self.invocation_premises(inputs))
        view = inputs.get(self.context_key) or {}
        boxes, gb = _view_boxes(view), {g["entity_id"]: g.get("body")
                                        for g in (view.get("RigidGroup") or [])}
        envelope_of = {e.get("body"): e.get("entity_id")
                       for e in (view.get("Envelope") or []) if isinstance(e, dict)}
        joints = {j["entity_id"]: j for j in (view.get("Joint") or [])}
        origins = {p.get("joint"): p.get("origin")
                   for p in (parsed.get("joint_placements") or [])}
        coords = {st.get("configuration"): (st.get("coordinates") or {})
                  for st in (parsed.get("state_coordinates") or [])}
        ops: List[Op] = []
        for t in parsed.get("transitions") or []:
            frm, to = self._endpoints(view, t)
            # NO SWEEP FOR A TRANSITION THAT WAS NOT WRITTEN. `to_operations`
            # skips a transition whose requirement this consumer was not given,
            # or whose endpoint states this response stated no coordinates for -
            # inventing either is the defect being removed - and a hull computed
            # for it would reference records no patch creates. The two skips are
            # the same condition read from the same two places, so the sweep can
            # never outlive the path it is the occupancy of.
            if frm is None or to is None or frm not in coords or to not in coords:
                continue
            ca = coords.get(frm) or {}
            cb = coords.get(to) or {}
            changed = {c for c in (t.get("changed_coordinates") or [])
                       if isinstance(c, str)}
            for group in (t.get("moving_groups") or []):
                body = gb.get(group)
                # WHICH JOINT MOVES THIS GROUP - the same question the evaluator
                # asks, answered the same way. This matched `child_group` alone
                # and took the first hit, so a group named on the PARENT side of
                # the joint that moves it got no hull at all, and the mechanism
                # described the other way round produced different evidence.
                # Incidence is either side; which of the incident joints carries
                # THIS motion is what the transition already says it changes.
                carrying = [j for j in incident_joints(joints.values(), group)
                            if j.get("entity_id") in changed]
                if body not in boxes or len(carrying) != 1:
                    # More than one is a motion the design does not attribute,
                    # and picking would be the arbitrary choice being removed.
                    # `spatial_realization` reports both the ambiguity and the
                    # occupancy this did not compute.
                    continue
                drive = carrying[0]
                jid = drive["entity_id"]
                swept = sweep_hull(boxes[body], drive, origins.get(jid),
                                   float(ca.get(jid, 0) or 0),
                                   float(cb.get(jid, 0) or 0))
                if not swept["computable"]:
                    continue
                ops.append(Op("CREATE", "SweptVolume",
                              "SWV-%s-%s" % (t["id"], group),
                              {"rigid_group": group, "transition": t["id"],
                               "sampling_declaration": swept["sampling_declaration"],
                               "occupancy": {"aabb": swept["hull"]},
                               "fidelity": swept["motion_evidence_level"]},
                              "s04b:computation",
                              premise_refs=self._sweep_premises(
                                  view, t, group, jid, envelope_of.get(body))))
        # THE EVIDENCE LIVES IN ONE PLACE, on the SweptVolume the computation
        # produced. Copying it onto the Transition as well would put the same
        # claim in two records that can disagree - and the Transition is where
        # the constant used to live, which is exactly the shape being removed. A
        # transition with no SweptVolume was not evidenced, and that is readable
        # without a field saying so.
        #
        # The invocation premise last, as everywhere else: this occupancy was
        # computed to evidence ONE candidate's motion, so withdrawing that
        # candidate costs it standing. `run` passes only `to_operations` through
        # this, so a derived value has to say it itself.
        return carry_invocation_premises(ops, self.invocation_premises(inputs))

    def _contradicted_distinctness(self, parsed, inputs) -> List[str]:
        """The declared distinctions THESE NUMBERS POSITIVELY CONTRADICT.

        Realizing `Configuration.distinguishing_basis` numerically is this pass's
        responsibility, not a preference. A response giving two configurations
        the design says are different states one coordinate has not realized
        them, and admitting it would turn an invalid realization into evidence
        about the MECHANISM - the candidate convicted, a stage later, of a
        contradiction its author introduced.

        ONLY THE CONTRADICTION GATES. A driver the topology does not resolve, a
        sibling with no coordinates, a basis naming nobody are questions the
        evidence leaves open; they are reported and they do not withhold
        anything. What is refused is the positive statement that two distinct
        states are one.
        """
        findings, _read = distinctness_findings(
            (inputs.get(self.context_key) or {}).get("Configuration") or [],
            {st.get("configuration"): (st.get("coordinates") or {})
             for st in (parsed.get("state_coordinates") or [])},
            (inputs.get(self.context_key) or {}).get("Joint") or [])
        return [note for code, note, _refs in findings
                if code == "DECLARED_DISTINCTNESS_NOT_REALIZED"]

    def _realization_problems(self, parsed, inputs) -> List[str]:
        """Whether every demanded state change was actually carried out here.

        THE REQUIREMENT IS THE SUBJECT. s04b does not decide which transitions a
        mechanism needs - s03b already did, directed and symbolic - so this asks
        only whether each demand got exactly one realization and whether the
        numbers in that realization do what the demand asked for.

        THE RULES ARE `realization_findings`, and the two things this adds are
        the two only a producer can say: a transition that named no requirement
        at all, and one that named a requirement this consumer was not given.
        Both are refusals to write the record rather than judgements about a
        record, which is why they are here and the rest is shared.
        """
        view = inputs.get(self.context_key) or {}
        required = [r for r in (view.get("TransitionRequirement") or [])
                    if isinstance(r, dict)]
        joints = {j["entity_id"]: j for j in (view.get("Joint") or [])}
        coordinates = {st.get("configuration"): (st.get("coordinates") or {})
                       for st in (parsed.get("state_coordinates") or [])}
        out: List[str] = []

        known = {r.get("entity_id") for r in required}
        by_requirement: Dict[str, List[Dict[str, Any]]] = {}
        for t in (parsed.get("transitions") or []):
            if not isinstance(t, dict):
                continue
            name = t.get("realizes_requirement")
            if not isinstance(name, str) or not name:
                out.append("transition %s realizes no requirement; a transition "
                           "this pass writes is the realization of a demanded "
                           "state change and says which" % t.get("id"))
                continue
            if name not in known:
                out.append("transition %s realizes %s, which this consumer was "
                           "not given; the endpoints of a transition come from "
                           "its requirement, so nothing was written for it"
                           % (t.get("id"), name))
                continue
            by_requirement.setdefault(name, []).append(t)

        for demand in required:
            rid = demand.get("entity_id")
            # THE ENDPOINTS ARE THE DEMAND'S. This pass resolves them from the
            # requirement when it writes the record, so a realization here
            # cannot connect a different pair - the mismatch the shared rules
            # look for is a question about written records, and it is asked of
            # them by the evaluator that reads them.
            realizations = [
                {"id": t.get("id"),
                 "from_configuration": demand.get("from_configuration"),
                 "to_configuration": demand.get("to_configuration"),
                 "moving_groups": t.get("moving_groups"),
                 "changed_coordinates": t.get("changed_coordinates")}
                for t in (by_requirement.get(rid) or [])]
            out += [note for _code, note in realization_findings(
                demand, realizations, coordinates, joints)]
        return out

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        joints = {j["entity_id"] for j in inputs["consumer_view"].get("Joint", [])}
        placed = {p.get("joint") for p in parsed.get("joint_placements", [])}
        for missing in sorted(joints - placed):
            out.append("joint %s has no placement" % missing)
        configs = {c["entity_id"] for c in inputs["consumer_view"].get("Configuration", [])}
        stated = {s.get("configuration") for s in parsed.get("state_coordinates", [])}
        for missing in sorted(configs - stated):
            out.append("configuration %s has no joint coordinates" % missing)
        out.extend(self._realization_problems(parsed, inputs))
        # DECLARED DISTINCTNESS, CHECKED BEFORE THESE COORDINATES ARE ACCEPTED.
        # Two configurations the design says are not the same state, given one
        # coordinate, are numbers that contradict the mechanism they claim to
        # realize. This pass used to have no rule about it at all: the formula
        # lived only in feasibility, so the contradiction was authored here,
        # committed, and convicted a stage later - by which time the response
        # that could have been asked again was already state.
        #
        # THE SAME RULE, not a second one. `distinctness_findings` is shared
        # with the evaluator so a response this pass accepts cannot be one the
        # evaluator rejects for a reason this pass could have given.
        distinct, _read = distinctness_findings(
            inputs["consumer_view"].get("Configuration") or [],
            {st.get("configuration"): (st.get("coordinates") or {})
             for st in (parsed.get("state_coordinates") or [])},
            inputs["consumer_view"].get("Joint") or [])
        out.extend(note for _code, note, _refs in distinct)
        # An axis this pass cannot use is not this pass's to invent. Reported
        # where the placement is claimed, so the run records that the motion was
        # never computable rather than that it was computed.
        by_id = {j["entity_id"]: j for j in inputs["consumer_view"].get("Joint", [])}
        for p in parsed.get("joint_placements") or []:
            j = by_id.get(p.get("joint")) or {}
            if str(j.get("joint_type", "")).upper() == "FIXED":
                continue
            if axis_index(j.get("axis_direction")) is None:
                out.append("joint %s is placed and its axis %r names no coordinate, "
                           "so no motion can be computed from it"
                           % (p.get("joint"), j.get("axis_direction")))
        for t in parsed.get("transitions") or []:
            if not (t.get("changed_coordinates") or []):
                out.append("transition %s declares no changed coordinate, so "
                           "nothing says what moves" % t.get("id"))
        for r in parsed.get("envelope_revisions") or []:
            if not str(r.get("geometric_reason") or "").strip():
                out.append("a revision of envelope %s states no geometric reason; "
                           "a commitment is superseded with a reason or extended"
                           % r.get("envelope"))

        # NO PROPAGATION FROM MobilityExpectation. A block here used to inherit
        # s03's incompleteness by reading `MobilityExpectation.dispositions` for
        # BLOCKED_BY cells carrying no defeat specification - and it could never
        # fire, because `mobility_disposition` is not among this responsibility's
        # required premise classes, so the family is never in this view. A live
        # run showed it: hundreds of blocked DOF carried no defeat specification
        # and every response reported SUCCESS with nothing declared.
        #
        # The right repair is removal, not adding the family to the contract. A
        # completeness method reads THE VIEW IT WAS GIVEN; reaching for a premise
        # class the responsibility does not declare is a second input channel,
        # and widening the contract to feed a check would give s04b a premise it
        # has no engineering question for. Whether a candidate's evidence is good
        # enough to keep is judged AFTER this pass, by feasibility, which does
        # declare the classes it needs.
        return out


#: The density the sweep uses when a caller names none. It is a parameter OF THE
#: COMPUTATION, not a declaration about it: nothing records an evidence level
#: from this number, and changing it changes what is computed and therefore what
#: is recorded. Non-adaptive and per-run, because a density chosen per case is a
#: density chosen after seeing the answer.
SAMPLES = 9


def sweep_hull(box, joint: Dict[str, Any], origin: Sequence[float],
               q0: float, q1: float, samples: int = SAMPLES) -> Dict[str, Any]:
    """Sweep one body between two joint coordinates and RECORD WHAT WAS DONE.

    Returns the hull together with the evidence of its own construction: how many
    poses were evaluated, how many of them were interior, the method, and the
    resulting motion evidence level.

    THE LEVEL IS AN OUTPUT, NOT AN INPUT. Before S-6 a parser wrote
    `sampling_declaration = {samples: 9}` from a module constant when the patch
    was built - before any sweep existed - a check then validated the property
    that constant guaranteed, and the sweep read its density back out of the
    declaration. The claim decided the computation. Here the computation decides
    the claim, and a caller that changes `samples` changes the recorded level.

    It never returns SWEPT or CONTINUOUS. This method unions the axis-aligned
    bounds of discrete poses; claiming a continuous sweep would be claiming a
    computation that did not happen, and the vocabulary having the word in it is
    not permission to use it.

    `computable` is False, with a reason and no hull, when a premise is missing.
    Nothing is defaulted so the arithmetic can proceed.
    """
    axis = joint.get("axis_direction")
    idx = axis_index(axis)
    if idx is None:
        return {"computable": False,
                "why": "joint %s declares axis %r, which names no coordinate"
                       % (joint.get("entity_id"), axis)}
    prismatic = str(joint.get("joint_type", "")).upper() == "PRISMATIC"
    if not prismatic and not (isinstance(origin, (list, tuple)) and len(origin) == 3):
        return {"computable": False,
                "why": "joint %s has no placed frame origin to rotate about"
                       % joint.get("entity_id")}
    n = max(int(samples), 2)
    poses = ([q0, q1] if n == 2 else sample(q0, q1, n))
    hull = None
    for q in poses:
        if prismatic:
            delta = [0.0, 0.0, 0.0]
            delta[idx] = q * axis_sign(axis)
            box_q = translate(box, delta)
        else:
            box_q = rotate_about_axis(box, axis, origin, math.radians(q))
        hull = box_q if hull is None else (
            [min(hull[0][i], box_q[0][i]) for i in range(3)],
            [max(hull[1][i], box_q[1][i]) for i in range(3)])
    interior = max(len(poses) - 2, 0)
    return {
        "computable": True, "hull": hull,
        "sampling_declaration": {
            "kind": "UNIFORM", "adaptive": False,
            "samples": len(poses), "interior_samples": interior,
            "method": "AABB_UNION_OF_DISCRETE_POSES"},
        # The one place the level is decided, and it reads only what was done.
        "motion_evidence_level": "SAMPLED" if interior else "ENDPOINTS_ONLY",
    }


#: WHAT AN INTERFACE SAYS ABOUT ITS PAIR SHARING SPACE. Three answers, and they
#: are not interchangeable: a kind whose meaning REQUIRES the pair to meet
#: exempts that pair from generic interference, and CLEARANCE is the opposite
#: statement - the design promising they stay apart - so it can exempt nothing.
#:
#: EXTRACTED at the S7-B correction. The set lived inline in `required_contacts`
#: and the CLEARANCE case lived inline in `configuration_interference_check`,
#: which is how a consumer came to read "an interface exists" as "these two are
#: allowed to overlap" - the one reading neither of those two places supports.
TOUCHES, CLEAR, UNDECLARED = "TOUCHES", "CLEAR", "UNDECLARED"
INTENDED_CONTACT_KINDS = ("CONTACT", "INTERFERENCE_FIT", "COMPLIANT_INTERACTION")


def interface_expectation(iface: Optional[Dict[str, Any]]) -> str:
    """TOUCHES, CLEAR or UNDECLARED for one interface. One reader, one answer."""
    kind = (iface or {}).get("interaction_kind")
    if kind in INTENDED_CONTACT_KINDS:
        return TOUCHES
    if kind == "CLEARANCE":
        return CLEAR
    return UNDECLARED


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
        if len(bodies) >= 2 and interface_expectation(i) == TOUCHES:
            pairs.add(tuple(sorted(bodies[:2])))
    return sorted(pairs)


def _contact_pairs_text(mech: Dict[str, Any]) -> str:
    pairs = required_contacts(mech)
    if not pairs:
        return "   (the topology declares no connected body pair)"
    return "\n".join("   %s and %s must touch" % p for p in pairs)


def _render(obj: Any) -> str:
    """Deterministic serialization of a ConsumerView payload.

    U-3: the fixed positional character slice is GONE. It was a semantic-selection
    mechanism disguised as formatting - `sort_keys=True` put RigidGroup last, so
    the topology was what fell off the end. Budget pressure is now handled
    semantically before rendering, by ConsumerView, and an unsatisfiable budget is
    a recorded condition rather than a silent cut.
    """
    try:
        return json.dumps(obj, indent=1, sort_keys=True)
    except Exception:                                                # noqa: BLE001
        return str(obj)


# =========================================================================
# the spatial computation and the checks
# =========================================================================
def box_gap(a: Tuple[List[float], List[float]],
            b: Tuple[List[float], List[float]]) -> float:
    """Largest separation between two boxes on any axis. Positive means apart.

    EXTRACTED at S7-B, unchanged: this expression stood in three places, and a
    feasibility evaluator needed a fourth. One formula, so a reader asking "are
    these two apart" gets one answer.
    """
    return max(max(a[0][i] - b[1][i], b[0][i] - a[1][i]) for i in range(3))


def coordinate_change_disagreement(from_coords, to_coords, declared):
    """(declared-but-not-realized, realized-but-not-declared) joint ids.

    EXTRACTED at S7-B from `transition_realization_check`, which keeps its exact
    findings and its exact strings. Both directions are wrong in different ways:
    a declared change the endpoints do not make is a claim about motion that does
    not happen, and a coordinate that changes undeclared is motion nobody said
    would occur.
    """
    ca, cb = from_coords or {}, to_coords or {}
    actual = {j for j in set(ca) | set(cb) if ca.get(j) != cb.get(j)}
    said = {j for j in (declared or []) if isinstance(j, str)}
    return sorted(said - actual), sorted(actual - said)


def _extent_box(e) -> Optional[Tuple[List[float], List[float]]]:
    ext = e.get("extent") or {}
    c, h = ext.get("centre"), ext.get("half_extent")
    if isinstance(c, list) and isinstance(h, list) and len(c) == 3 and len(h) == 3:
        return aabb(c, h)
    return None


def _view_boxes(view) -> Dict[str, Tuple[List[float], List[float]]]:
    """body -> box, from a CONSUMER VIEW. Branch-scoped by construction."""
    out = {}
    for e in (view.get("Envelope") or []):
        box = _extent_box(e) if isinstance(e, dict) else None
        if box:
            out[e.get("body")] = box
    return out


#: A record still carrying unqualified authority, decided the way DesignState
#: decides it. The payload helpers below are pure, so they cannot ask the state.
_STANDING = "STANDING"


def _standing_rows(rows) -> List[Dict[str, Any]]:
    return [r for r in (rows or [])
            if isinstance(r, dict) and r.get("_validity", _STANDING) == _STANDING]


def _payload_boxes(payload) -> Dict[str, Tuple[List[float], List[float]]]:
    """body -> box, from a family->records payload. Same rule as `_boxes`."""
    out = {}
    for e in _standing_rows(payload.get("Envelope")):
        ext = e.get("extent") or {}
        c, h = ext.get("centre"), ext.get("half_extent")
        if isinstance(c, list) and isinstance(h, list) and len(c) == 3 and len(h) == 3:
            out[e.get("body")] = aabb(c, h)
    return out


def branch_payloads(state, families: Sequence[str]) -> List[Dict[str, List[Dict[str, Any]]]]:
    """One payload per candidate branch, using the CANONICAL branch resolver.

    A GEOMETRIC DIAGNOSTIC THAT MIXES BRANCHES ANSWERS ABOUT NO MECHANISM.
    Candidates coexist in one DesignState, so `state.family("Envelope")` is every
    alternative's arrangement at once, and a diagnostic reading it produces a body
    sweeping into another CANDIDATE's body and an assembly step obstructed by a
    part from a mechanism it will never be built with. Neither finding is about
    any design that exists.

    WHICH BRANCH AN ENTITY BELONGS TO IS NOT THIS MODULE'S QUESTION TO ANSWER.
    `branch_membership` already owns it, over the declared depends-on graph -
    typed references and recorded premises alike - so membership is TRANSITIVE:
    an envelope naming a body that was authored from a candidate belongs to that
    candidate's branch without premising it directly. An earlier version of this
    function read `_premises` for a Candidate id, which is a second branch
    ontology and a strictly narrower one: it put every indirectly-owned entity in
    no branch and every genuinely unscoped one in ALL of them.

    Two absences that are not the same fact, and only the FIRST licenses running
    over everything:

      NOTHING HAS BRANCHED. No Candidate stands at all. "Before the work
      branches, this branch is the design" - `branch_membership`'s own words - so
      the diagnostic runs once over everything, which is what every
      single-mechanism fixture is.

      NOTHING IS OWNED. Candidates stand and no branch reaches these records.
      They are UNSCOPED, they belong to no mechanism, and there is nothing to
      check: returning them as one implicit mechanism would assemble a machine
      out of parts the design says belong to none, and report its collisions as
      if they were somebody's. An unscoped record appears in no payload, whether
      it is one of many or all there is.

    The RESOLVER is asked, never a ConsumerView. `branch_membership` is a pure
    function of state and contracts; a view is built for a particular consumer,
    and a diagnostic that needed one would be answerable only after the stage it
    exists to inform.
    """
    from ..view.consumer_view import branch_membership

    records = [(family, record) for family in families
               for record in state.family(family)]
    if not state.standing("Candidate"):
        return [{f: list(state.family(f)) for f in families}]
    membership = branch_membership(state, state.c,
                                   [r["entity_id"] for _f, r in records])
    branches = sorted({b for owned in membership.values() for b in owned})
    out: List[Dict[str, List[Dict[str, Any]]]] = []
    for branch in branches:
        payload: Dict[str, List[Dict[str, Any]]] = {f: [] for f in families}
        for family, record in records:
            if branch in membership.get(record["entity_id"], ()):
                payload[family].append(record)
        out.append(payload)
    return out


def _boxes(state) -> Dict[str, Tuple[List[float], List[float]]]:
    out = {}
    for e in state.standing("Envelope"):
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
                if interface_expectation(iface) == CLEAR:
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
            if body in boxes and excludes_occupancy(r.get("role")) \
                    and overlaps(box, boxes[body]):
                problems.append(
                    "REGION_OCCUPIED_BY_ITS_OWNER: %s (%s) overlaps %s"
                    % (r["entity_id"], r.get("role"), body))
    return problems


def motion_evidence_check(state) -> List[str]:
    """S04B-C1/C2. The recorded evidence level is the one the record supports.

    SUPERSEDES `sampling_declaration_check`, which tested the property a module
    constant guaranteed: the parser wrote `samples: SAMPLES` and the check
    confirmed `SAMPLES - 2 >= 1`. It could not fail, and it said nothing about
    the motion.

    This recomputes the level from the sampling record and requires the recorded
    level to agree - so a level cannot be raised by declaring it - and refuses
    any level this method cannot produce. Unioning the bounds of discrete poses
    is not a swept or continuous computation, and the vocabulary containing those
    words is not permission to claim them.

    A transition with no declaration at all is REPORTED as not computed, not
    silently accepted: absent evidence is a state, and a missing record where a
    computation should have run is a finding.
    """
    problems = []
    evidenced = set()
    for v in state.standing("SweptVolume"):
        evidenced.add(v.get("transition"))
        d = v.get("sampling_declaration")
        level = v.get("fidelity")
        if not isinstance(d, dict):
            problems.append("MOTION_NOT_COMPUTED: %s carries no sampling record, "
                            "so nothing says how it was evidenced" % v["entity_id"])
            continue
        if d.get("adaptive"):
            problems.append("SAMPLING_ADAPTIVE: %s" % v["entity_id"])
        interior = int(d.get("interior_samples") or 0)
        implied = "SAMPLED" if interior else "ENDPOINTS_ONLY"
        if level not in MOTION_EVIDENCE:
            problems.append("MOTION_EVIDENCE_UNDECLARED: %s -> %r"
                            % (v["entity_id"], level))
        elif level != implied:
            problems.append(
                "MOTION_EVIDENCE_OVERSTATED: %s claims %s; %d interior sample(s) "
                "support %s. The level follows the computation, never the reverse"
                % (v["entity_id"], level, interior, implied))
        # ENDPOINTS_ONLY is NOT reported as a defect. It is a level, and the
        # record says which one: whether it is SUFFICIENT for a claim is an
        # assurance question about that claim, and answering it here would be
        # this check deciding how much evidence an unseen argument needs. What
        # this check owes is that the level matches the computation, which is the
        # comparison above.
    for t in state.standing("Transition"):
        if not ((t.get("path") or {}).get("moving_groups") or []):
            continue
        if t["entity_id"] not in evidenced:
            problems.append("MOTION_NOT_COMPUTED: %s moves something and no swept "
                            "occupancy was computed for it" % t["entity_id"])
    return problems


def spatial_commitment_check(state) -> List[str]:
    """Every s04a spatial commitment carries the class it was committed at.

    Read from `spatial_commitments` in the canonical contract, so the check and
    the declaration cannot drift and a family added there is checked without
    editing this. ENTITY-LEVEL commitments carry a class on the entity; FIELD-
    LEVEL ones cannot - runtime has no per-field authority, and a field invented
    to hold one would declare an enforcement that does not exist - so what is
    checked for them is that the field is s04's to author and nobody else's,
    which the boundary already enforces.
    """
    import yaml as _yaml
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "..", "contracts", "DESIGN_STATE_CONTRACT.yaml")
    with open(os.path.abspath(path)) as fh:
        doc = _yaml.safe_load(fh)
    fams = dict(doc["entity_families"])
    fams.update(doc.get("assurance_families") or {})
    decl = doc.get("spatial_commitments") or {}
    problems = []
    for d in decl.get("entity_level") or []:
        field = d["class_field"]
        vocab = fams[d["family"]].get(field) or []
        for e in state.standing(d["family"]):
            if e.get(field) not in vocab:
                problems.append(
                    "SPATIAL_COMMITMENT_UNCLASSIFIED: %s carries %s=%r, which is "
                    "not a commitment class; a value nothing may silently "
                    "contradict has to say what it is"
                    % (e["entity_id"], field, e.get(field)))
    for d in decl.get("field_level") or []:
        owner = (fams[d["family"]].get("extendable_fields") or {}).get(d["field"])
        if owner != "s04":
            problems.append(
                "SPATIAL_COMMITMENT_NOT_ENFORCEABLE: %s.%s is declared an s04a "
                "commitment and is extendable by %r; the only enforcement a "
                "field-level commitment has is who may author it"
                % (d["family"], d["field"], owner))
    return problems


def joint_frame_check(state) -> List[str]:
    """A located joint carries enough to compute motion, or it carries nothing.

    An origin with no usable axis supports no incidence and no motion claim. It
    used to support both, because every consumer defaulted a missing axis to Z -
    so a joint the topology never gave an axis produced a swept hull, and the
    hull produced a clearance verdict, with nothing in the record saying the axis
    was invented.

    A FIXED joint legitimately has no axis and drives nothing; it is not asked
    for one.
    """
    problems = []
    for j in state.standing("Joint"):
        if str(j.get("joint_type", "")).upper() == "FIXED":
            continue
        origin = j.get("frame_origin")
        placed = isinstance(origin, list) and len(origin) == 3
        usable = axis_index(j.get("axis_direction")) is not None
        if placed and not usable:
            problems.append(
                "JOINT_FRAME_INCOMPLETE: %s is placed at %s and declares axis %r, "
                "which names no coordinate; an origin without an axis supports no "
                "motion claim" % (j["entity_id"], origin, j.get("axis_direction")))
        if not placed and usable:
            problems.append("JOINT_NOT_PLACED: %s has an axis and no frame origin"
                            % j["entity_id"])
    return problems


def swept_clearance_check(state) -> List[str]:
    """S04B. Sweep every moving group along every transition and test occupancy.

    The sweep is computed from the joint placement, the joint's own axis
    direction, and the state coordinates - never from anything the model
    asserted about clearance. A group that sweeps into a KEEP_OUT region or into
    a body it has no declared interface with is reported.

    ONE BRANCH AT A TIME. The state holds every candidate's arrangement, and a
    sweep tested against another candidate's bodies is a collision between two
    mechanisms that will never exist together.
    """
    # The families this computation reads, written where it is called rather
    # than as a module constant: a standing table of families is how a hand-kept
    # "what may this see" whitelist grows back, and the list belongs beside the
    # call it scopes, where a reader checks it against the function below.
    return [p for payload in branch_payloads(
                state, ("Envelope", "RigidGroup", "Joint", "State", "Transition",
                        "Interface", "FunctionalRegion"))
            for p in swept_clearance_findings(payload)]


def swept_clearance_findings(payload) -> List[str]:
    """The same computation over ONE branch's payload. Pure, and the only copy.

    Taking a payload rather than the state is what makes the scope decidable:
    the caller says which mechanism this is about, and nothing in here can widen
    it. `swept_clearance_check` is the state-level entry point and does exactly
    that partitioning.
    """
    boxes = _payload_boxes(payload)
    gb = {g["entity_id"]: g.get("body") for g in (payload.get("RigidGroup") or [])}
    joints = {j["entity_id"]: j for j in (payload.get("Joint") or [])}
    states = {s["entity_id"]: s for s in (payload.get("State") or [])}
    placements = {}
    for j in (payload.get("Joint") or []):
        o = j.get("frame_origin")
        if isinstance(o, list) and len(o) == 3:
            placements[j["entity_id"]] = o
    declared = set()
    for i in (payload.get("Interface") or []):
        b = [x for x in (i.get("bodies") or []) if isinstance(x, str)]
        if len(b) >= 2:
            declared.add(frozenset(b[:2]))
    keepouts = []
    for r in (payload.get("FunctionalRegion") or []):
        v = r.get("volume")
        if r.get("role") == "KEEP_OUT" and isinstance(v, dict) \
                and isinstance(v.get("centre"), list):
            keepouts.append((r["entity_id"], aabb(v["centre"], v["half_extent"])))

    problems: List[str] = []
    for t in _standing_rows(payload.get("Transition")):
        a, b = states.get(t.get("from_state")), states.get(t.get("to_state"))
        if not (a and b):
            problems.append("TRANSITION_ENDPOINT_MISSING: %s" % t["entity_id"])
            continue
        ca = a.get("joint_coordinates") or {}
        cb = b.get("joint_coordinates") or {}
        moving = (t.get("path") or {}).get("moving_groups") or []
        for group in moving:
            body = gb.get(group)
            if body not in boxes:
                continue
            # The joint driving this group: the one whose child it is.
            drive = next((j for j in joints.values() if j.get("child_group") == group), None)
            if drive is None:
                problems.append("SWEEP_NOT_COMPUTABLE: %s in %s has no driving joint"
                                % (group, t["entity_id"]))
                continue
            jid = drive["entity_id"]
            # ONE sweep implementation, shared with the producer. A second copy
            # here would be a second answer to "where does this body go".
            swept = sweep_hull(boxes[body], drive, placements.get(jid),
                               float(ca.get(jid, 0) or 0), float(cb.get(jid, 0) or 0))
            if not swept["computable"]:
                problems.append("SWEEP_NOT_COMPUTABLE: %s in %s: %s"
                                % (group, t["entity_id"], swept["why"]))
                continue
            hull = swept["hull"]
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

    ONE BRANCH AT A TIME, because `order_index` is a sequence within ONE
    mechanism and means nothing across two.
    """
    return [p for payload in branch_payloads(state, ("Envelope", "AssemblyStep"))
            for p in assembly_path_findings(payload)]


def assembly_path_findings(payload) -> List[str]:
    """The same computation over ONE branch's payload. Pure, and the only copy.

    Order index is a sequence WITHIN a mechanism. Sorting every candidate's steps
    together makes each branch's first body "already placed" before every other
    branch's second, and every obstruction that follows is between parts of two
    designs that are alternatives to each other.
    """
    boxes = _payload_boxes(payload)
    steps = sorted((payload.get("AssemblyStep") or []),
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

    A HOP IS AN INTERFACE, which is what S-4 made `ordered_hops` mean: a body is
    what a load passes through, an interface is what carries it from one body to
    the next. This check read hops as BODY ids and filtered by membership in the
    envelope map, so after S-4 every hop was discarded and the check returned
    nothing on every path - vacuously green while reporting a spatial conclusion.
    The identical geometry expressed with body hops produced a finding, which is
    how the silence was found.

    Two things must hold, and each is a different failure. An interface whose own
    bodies are apart carries nothing across. Consecutive interfaces that share no
    body are two crossings with no route between them.
    """
    boxes = _boxes(state)
    interfaces = {i["entity_id"]: i for i in state.standing("Interface")}
    problems = []
    for p in state.standing("LoadPath"):
        hops = [h for h in (p.get("ordered_hops") or []) if isinstance(h, str)]
        for h in hops:
            iface = interfaces.get(h)
            if iface is None:
                problems.append("LOADPATH_HOP_NOT_AN_INTERFACE: %s in %s names %s, "
                                "which is no interface of this mechanism"
                                % (h, p["entity_id"], h))
                continue
            pair = [b for b in (iface.get("bodies") or []) if b in boxes]
            if len(pair) < 2:
                continue
            a, b = pair[0], pair[1]
            gap = box_gap(boxes[a], boxes[b])
            if gap > 0:
                problems.append("LOADPATH_HOP_DISJOINT: %s carries %s -> %s in %s, "
                                "and they are placed %.3g apart; the load cannot "
                                "cross" % (h, a, b, p["entity_id"], gap))
        for x, y in zip(hops, hops[1:]):
            ia, ib = interfaces.get(x), interfaces.get(y)
            if not (ia and ib):
                continue
            if not set(ia.get("bodies") or []) & set(ib.get("bodies") or []):
                problems.append("LOADPATH_HOPS_NOT_CONNECTED: %s and %s in %s share "
                                "no body, so the load has no route from one to the "
                                "other" % (x, y, p["entity_id"]))
    return problems
