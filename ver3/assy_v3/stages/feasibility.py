"""CAN THIS CANDIDATE WORK? - deterministically, locally, and blind to taste.

NAMED FOR THE RESPONSIBILITY, NOT FOR A STAGE NUMBER. The brief called this file
`s07_mechanical_feasibility.py`, and `s07` is already taken: pipeline stage s07 is
geometry compilation, with its own `S07_CONTRACT.yaml`. Migration step S-7 is not
pipeline stage s07, and S7-A refused this exact collision once already - "they are
responsibilities, as `gate` already was: non-numbered". Under the brief's name the
progression gate would also have passed for the wrong reason: it looks for
`S07_CONTRACT.yaml` and would have found the compiler's.

S7-B. The `feasibility` responsibility, and the first producer in the pipeline
that calls no provider at all. It reads what s01-s04 established about ONE
candidate and says whether the established evidence contains anything that stops
that candidate working. It never compares candidates, never sees a preference,
and never prefers a simpler mechanism: a four-bar that works is not less feasible
than a hinge that works, and nothing here can express the difference.

THREE RULES DECIDE ALMOST EVERYTHING BELOW

    APPLICABILITY BEFORE STATUS. NOT_APPLICABLE means the design poses no
    question in this domain - no load case, no required motion. It is not a
    weaker PASS and it never blocks.

    ABSENCE IS NOT_ESTABLISHED. Never PASS, and never FAIL either. A missing
    envelope, an unchecked path, a conservative box overlap are all things the
    design has not established, and turning any of them into a verdict would be
    this code deciding the engineering.

    FAIL NEEDS A POSITIVE CONTRADICTION. A current typed fact that contradicts a
    requirement: a path that closes at the wrong site, two configurations
    declared to differ that realize the same coordinate, a DOF required to move
    that a relation blocks. Not an absence, and not a model's opinion.

WHY DOMAIN-LEVEL RECORDS

    A motion verdict and a load verdict rest on different facts. One record for
    all nine could carry only their union, so an envelope changing would stale
    the load closure it cannot affect - and a reader who sees that learns to
    ignore STALE. Each domain names exactly what it read.

NO SECOND FORMULA

    Every geometric and kinematic computation here is the one s03/s04 already
    perform: `free_dof`, `sweep_hull`, `box_gap`, `overlaps`, `required_contacts`,
    `coordinate_change_disagreement`, `assembly_order_problems`. Two formulas for
    one question is two answers.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..state.patch import Op, StagePatch
from ..view.consumer_view import InvocationContext, ViewStatus
from . import s03_topology_and_mobility as s03
from . import s04_envelope_and_motion as s04

RESPONSIBILITY = "feasibility"

#: The nine domains, in the order the contract declares them.
DOMAINS = ("physical_realization", "load_reaction_closure", "mobility_disposition",
           "required_configurations", "motion_and_transitions",
           "spatial_realization", "reach", "assemblability", "gross_interference")

PASS, FAIL, NOT_ESTABLISHED, NOT_APPLICABLE = (
    "PASS", "FAIL", "NOT_ESTABLISHED", "NOT_APPLICABLE")

FEASIBLE, INFEASIBLE, MFA_NOT_ESTABLISHED = (
    "FEASIBLE_FOR_SELECTION", "INFEASIBLE", "NOT_ESTABLISHED")

#: Short, stable tokens. A reason code is read by code and by a person; a
#: sentence is read only by a person, and `summary` is where sentences go.
MODEL_LOCAL_NEGATIVE = "MODEL_LOCAL_NEGATIVE"
MODEL_LOCAL_POSITIVE = "MODEL_LOCAL_POSITIVE"

#: DERIVED FROM THE DOMAIN NAME, never a table beside it - an abbreviation list
#: is a second vocabulary, and the two drift the first time a domain is added.
#: Hyphenated because an entity id's segments are alphanumeric and `_` is not.
_TOKEN = {d: d.upper().replace("_", "-") for d in DOMAINS}


class Verdict:
    """One domain's answer, and exactly what it was read from.

    `premises` are the CURRENT POSITIVE FACTS this verdict used - not everything
    the view held. An absence contributes a reason code and no premise: there is
    no entity to name, and inventing one to look thorough would make a missing
    fact look like a present one.
    """

    __slots__ = ("domain", "status", "reason_codes", "premises", "summary")

    def __init__(self, domain: str, status: str,
                 reason_codes: Optional[Sequence[str]] = None,
                 premises: Optional[Sequence[str]] = None,
                 summary: str = ""):
        self.domain = domain
        self.status = status
        self.reason_codes = sorted(set(reason_codes or ()))
        self.premises = sorted({p for p in (premises or ()) if isinstance(p, str) and p})
        self.summary = summary


class FeasibilityOutcome:
    """What one evaluation produced, and whether it could run at all."""

    __slots__ = ("candidate", "status", "verdicts", "compliance", "patch",
                 "problems", "consumer_view")

    def __init__(self, candidate, status, verdicts, compliance, patch,
                 problems, consumer_view):
        self.candidate = candidate
        self.status = status
        self.verdicts = list(verdicts)
        self.compliance = list(compliance)
        self.patch = patch
        self.problems = list(problems)
        self.consumer_view = consumer_view

    @property
    def ok(self) -> bool:
        return self.patch is not None and not self.problems


# =====================================================================
# reading one candidate's view
# =====================================================================
class _Evidence:
    """The candidate's evidence, indexed. THE ONLY ENGINEERING CHANNEL.

    Everything below reads this. Raw DesignState is used for patch mechanics and
    for nothing else: a second context channel beside the view is exactly what
    U-3 removed, and a feasibility verdict built from unscoped state would read
    another candidate's evidence without saying so.
    """

    def __init__(self, view: Dict[str, Any], candidate: str):
        self.candidate = candidate
        self.view = view
        self.by_family = {fam: list(rows) for fam, rows in view.items()
                          if isinstance(rows, list)}
        self.by_id = {e["entity_id"]: e for rows in self.by_family.values()
                      for e in rows if isinstance(e, dict) and e.get("entity_id")}

    def fam(self, name: str) -> List[Dict[str, Any]]:
        return [e for e in self.by_family.get(name, []) if isinstance(e, dict)]

    def ids(self, *families: str) -> List[str]:
        """Every id of these families. What a verdict names when it read the
        WHOLE set - "no undeclared pair overlaps" is a statement about all the
        interfaces, and any of them changing changes it."""
        return [e["entity_id"] for f in families for e in self.fam(f)
                if e.get("entity_id")]

    def basis(self) -> List[str]:
        """THE BASIS EVERY COORDINATE IS EXPRESSED IN.

        A premise of any verdict that read a spatial value, for the reason S-6
        gave about the values themselves: withdraw the basis and the numbers mean
        nothing. It has to be named HERE and not left to the envelope that
        carries it - `_propagate` is one hop, so superseding the scale stales the
        envelope and stops, leaving a verdict standing on an extent that has just
        lost its authority.
        """
        return self.ids("ReferenceScale")

    def boxes(self) -> Dict[str, Tuple[List[float], List[float]]]:
        return s04._view_boxes(self.view)

    def envelope_of(self) -> Dict[str, str]:
        return {e.get("body"): e.get("entity_id") for e in self.fam("Envelope")}

    def group_body(self) -> Dict[str, str]:
        return {g["entity_id"]: g.get("body") for g in self.fam("RigidGroup")}

    def state_for(self, configuration: str) -> Optional[Dict[str, Any]]:
        # `configuration or name`, exactly as `configuration_realization_check`
        # indexes it. Two different keyings would disagree about which state
        # realizes a configuration on precisely the records where it matters.
        for st in self.fam("State"):
            if (st.get("configuration") or st.get("name")) == configuration:
                return st
        return None

    def driving_joint(self, group: str) -> Optional[Dict[str, Any]]:
        for j in self.fam("Joint"):
            if j.get("child_group") == group:
                return j
        return None


# =====================================================================
# the nine domains
# =====================================================================
def _physical_realization(ev: _Evidence) -> Verdict:
    """Every required effect is realized by an interaction this candidate has."""
    demands = ev.fam("PhysicalEffectObligation")
    if not demands:
        return Verdict("physical_realization", NOT_APPLICABLE, ["NO_EFFECT_DEMANDED"])
    discharged = {i.get("discharges_effect"): i for i in ev.fam("PhysicalInteraction")}
    used, missing = [], []
    for demand in demands:
        eid = demand.get("entity_id")
        interaction = discharged.get(eid)
        # THE OBLIGATION IS NAMED EITHER WAY. It is a present fact that was read,
        # and it is the reason the domain is unsatisfied; what is absent is the
        # interaction, and that has no id to name. Withdrawing the demand must
        # cost this verdict its authority.
        used.append(eid)
        if interaction is None:
            missing.append(eid)
        else:
            used.append(interaction.get("entity_id"))
    if missing:
        return Verdict("physical_realization", NOT_ESTABLISHED,
                       ["EFFECT_NOT_DISCHARGED"], used,
                       "%d effect obligation(s) have no interaction: %s"
                       % (len(missing), ", ".join(sorted(missing)[:5])))
    return Verdict("physical_realization", PASS, ["ALL_EFFECTS_DISCHARGED"], used)


def _load_reaction_closure(ev: _Evidence) -> Verdict:
    """Every load reaches the site its own load case names, outside the product."""
    loads = ev.fam("LoadCase")
    if not loads:
        return Verdict("load_reaction_closure", NOT_APPLICABLE, ["NO_LOAD_CASE"])
    paths = {p.get("load_case"): p for p in ev.fam("LoadPath")}
    interfaces = {i["entity_id"]: i for i in ev.fam("Interface")}
    boxes = ev.boxes()
    envelope_of = ev.envelope_of()
    used, codes, notes = [], [], []
    status = PASS
    for load in loads:
        lid = load.get("entity_id")
        path = paths.get(lid)
        # The load case is named whether or not a path answers it: the demand is
        # present, and withdrawing it withdraws the question.
        used.append(lid)
        if path is None:
            codes.append("LOAD_PATH_MISSING")
            notes.append("%s has no path" % lid)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        used.append(path.get("entity_id"))
        terminus, expected = path.get("terminates_at"), load.get("reacted_at_site")
        if not terminus:
            codes.append("LOAD_PATH_OPEN")
            status = _weaken(status, NOT_ESTABLISHED)
        elif expected and terminus != expected:
            codes.append("TERMINUS_NOT_THE_DECLARED_SITE")
            notes.append("%s closes at %s and %s is reacted at %s"
                         % (path.get("entity_id"), terminus, lid, expected))
            status = FAIL
            used += [terminus, expected]
        else:
            site = ev.by_id.get(terminus)
            used.append(terminus)
            if site is None:
                codes.append("TERMINAL_SITE_NOT_GIVEN")
                status = _weaken(status, NOT_ESTABLISHED)
            elif site.get("boundary_side") != "EXTERNAL":
                codes.append("TERMINAL_SITE_INTERNAL")
                notes.append("%s closes inside the product" % path.get("entity_id"))
                status = FAIL
        hops = [h for h in (path.get("ordered_hops") or []) if isinstance(h, str)]
        if len(hops) < 1:
            codes.append("LOAD_PATH_TOO_SHORT")
            status = _weaken(status, NOT_ESTABLISHED)
        for h in hops:
            iface = interfaces.get(h)
            if iface is None:
                codes.append("HOP_NOT_AN_INTERFACE")
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            used.append(h)
            pair = [b for b in (iface.get("bodies") or []) if b in boxes]
            if len(pair) < 2:
                codes.append("HOP_GEOMETRY_MISSING")
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            # THE EXTENTS ARE NAMED WHATEVER THE ANSWER, and so is the basis they
            # are expressed in. A gap that is not there today is a gap either
            # body could acquire by being moved, so "these two touch" rests on
            # both extents exactly as much as "these two are apart" does.
            used += [e for e in (envelope_of.get(pair[0]),
                                 envelope_of.get(pair[1])) if e] + ev.basis()
            if s04.box_gap(boxes[pair[0]], boxes[pair[1]]) > 0:
                codes.append("HOP_BODIES_APART")
                notes.append("%s carries %s -> %s and they are apart"
                             % (h, pair[0], pair[1]))
                status = FAIL
        for x, y in zip(hops, hops[1:]):
            ia, ib = interfaces.get(x), interfaces.get(y)
            if ia and ib and not (set(ia.get("bodies") or [])
                                  & set(ib.get("bodies") or [])):
                codes.append("HOPS_NOT_CONNECTED")
                notes.append("%s and %s share no body" % (x, y))
                status = FAIL
    if status == PASS:
        codes.append("EVERY_LOAD_CLOSES_EXTERNALLY")
    return Verdict("load_reaction_closure", status, codes, used, "; ".join(notes[:5]))


def _required_motion_cells(ev: _Evidence):
    """(group, dof, why) triples the design REQUIRES to move, and what is ambiguous.

    From declared motion requirements only - a distinguishing basis, or a
    transition whose changed joint has exactly one free DOF. NOT the 6-DOF
    bookkeeping grid: totality is what the enumerator guarantees, and reading a
    feasibility verdict off it would be reading it off this code.
    """
    cells, ambiguous, used = [], [], []
    for cfg in ev.fam("Configuration"):
        for item in (cfg.get("distinguishing_basis") or []):
            if not isinstance(item, dict):
                continue
            group, dof = item.get("rigid_group"), item.get("dof")
            if group and dof:
                cells.append((group, dof, cfg.get("entity_id")))
                used.append(cfg.get("entity_id"))
    for t in ev.fam("Transition"):
        for jid in (t.get("changed_coordinates") or []):
            joint = ev.by_id.get(jid)
            if not isinstance(joint, dict):
                continue
            free = s03.free_dof(joint.get("joint_type"), joint.get("axis_direction"))
            group = joint.get("child_group")
            if len(free) == 1 and group:
                cells.append((group, sorted(free)[0], t.get("entity_id")))
                used += [t.get("entity_id"), jid]
            elif group:
                # A multi-DOF class: the representation does not say WHICH
                # coordinate this transition moves, and guessing would invent the
                # requirement the verdict is about.
                ambiguous.append((group, joint.get("joint_type"), jid))
    return cells, ambiguous, used


def _mobility_disposition(ev: _Evidence) -> Verdict:
    """Every DOF the design requires to move is dispositioned as free."""
    cells, ambiguous, used = _required_motion_cells(ev)
    if not cells and not ambiguous:
        return Verdict("mobility_disposition", NOT_APPLICABLE, ["NO_REQUIRED_MOTION"])
    disposed = {}
    for mex in ev.fam("MobilityExpectation"):
        for d in (mex.get("dispositions") or []):
            if isinstance(d, dict):
                disposed[(d.get("rigid_group"), d.get("configuration"),
                          d.get("dof"))] = (mex.get("entity_id"), d)
    codes, notes = [], []
    status = PASS
    if ambiguous:
        codes.append("MULTI_DOF_JOINT_NOT_RESOLVABLE")
        notes.append("%s leaves more than one DOF free and the representation "
                     "does not say which one moves" % ambiguous[0][2])
        status = _weaken(status, NOT_ESTABLISHED)
    for group, dof, _why in cells:
        rows = [(mid, d) for (g, _c, x), (mid, d) in disposed.items()
                if g == group and x == dof]
        if not rows:
            codes.append("REQUIRED_CELL_NOT_DISPOSITIONED")
            notes.append("%s/%s has no disposition" % (group, dof))
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        for mid, d in rows:
            verdict = d.get("disposition")
            if verdict == "INTENDED" and d.get("by_joint"):
                used += [mid, d["by_joint"]]
            elif verdict in ("BLOCKED_BY", "IRRELEVANT_BECAUSE"):
                codes.append("REQUIRED_MOTION_CONTRADICTED")
                notes.append("%s/%s must move and is %s" % (group, dof, verdict))
                status = FAIL
                used += [mid] + [d[f] for f in ("constraint_relation", "scenario")
                                 if d.get(f)]
            else:
                codes.append("REQUIRED_CELL_UNDISPOSITIONED")
                notes.append("%s/%s is %s" % (group, dof, verdict))
                status = _weaken(status, NOT_ESTABLISHED)
                used.append(mid)
    if status == PASS:
        codes.append("EVERY_REQUIRED_CELL_INTENDED")
    return Verdict("mobility_disposition", status, codes, used, "; ".join(notes[:5]))


def _required_configurations(ev: _Evidence) -> Verdict:
    """Each configuration is realized, and declared distinctness is real."""
    configs = ev.fam("Configuration")
    if not configs:
        return Verdict("required_configurations", NOT_APPLICABLE, ["NO_CONFIGURATION"])
    codes, notes, used = [], [], []
    status = PASS
    realized = {}
    for cfg in configs:
        cid = cfg.get("entity_id")
        st = ev.state_for(cid)
        if st is None:
            codes.append("CONFIGURATION_NOT_REALIZED")
            notes.append("%s has no state" % cid)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        realized[cid] = st
        used += [cid, st.get("entity_id")]
    for cfg in configs:
        cid = cfg.get("entity_id")
        mine = realized.get(cid)
        if mine is None:
            continue
        for item in (cfg.get("distinguishing_basis") or []):
            if not isinstance(item, dict):
                continue
            group = item.get("rigid_group")
            joint = ev.driving_joint(group)
            if joint is None:
                codes.append("DISTINCTNESS_DRIVER_UNKNOWN")
                notes.append("no joint drives %s" % group)
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            jid = joint["entity_id"]
            others = [o for o in (item.get("differs_from") or []) if o in realized] \
                or [k for k in realized if k != cid]
            q = (mine.get("joint_coordinates") or {}).get(jid)
            for other in others:
                p = (realized[other].get("joint_coordinates") or {}).get(jid)
                if q is None or p is None:
                    codes.append("DISTINCTNESS_COORDINATE_MISSING")
                    status = _weaken(status, NOT_ESTABLISHED)
                elif q == p:
                    codes.append("DECLARED_DISTINCTNESS_NOT_REALIZED")
                    notes.append("%s and %s both realize %s at %r"
                                 % (cid, other, jid, q))
                    status = FAIL
                    used += [jid, realized[other].get("entity_id")]
                else:
                    used.append(jid)
    # The coordinates compared above are spatial values, so the basis they are
    # expressed in is a premise of the comparison exactly as it is of them.
    if used:
        used += ev.basis()
    if status == PASS:
        codes.append("EVERY_CONFIGURATION_REALIZED")
    return Verdict("required_configurations", status, codes, used, "; ".join(notes[:5]))


def _motion_and_transitions(ev: _Evidence) -> Verdict:
    """A transition moves exactly the coordinates it says it moves."""
    transitions = ev.fam("Transition")
    required_change = any(cfg.get("distinguishing_basis")
                          for cfg in ev.fam("Configuration"))
    if not transitions:
        if required_change:
            # A state change IS required and no transition describes it. Absent,
            # not inapplicable - that difference is the whole point of the domain.
            return Verdict("motion_and_transitions", NOT_ESTABLISHED,
                           ["REQUIRED_TRANSITION_MISSING"], [],
                           "a configuration declares a distinguishing basis and "
                           "no transition realizes the change")
        return Verdict("motion_and_transitions", NOT_APPLICABLE, ["NO_REQUIRED_MOTION"])
    codes, notes, used = [], [], []
    status = PASS
    states = {st.get("entity_id"): st for st in ev.fam("State")}
    for t in transitions:
        a, b = states.get(t.get("from_state")), states.get(t.get("to_state"))
        if not (a and b):
            codes.append("TRANSITION_ENDPOINT_MISSING")
            notes.append("%s has an endpoint this candidate does not hold"
                         % t.get("entity_id"))
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        used += [t.get("entity_id"), a.get("entity_id"), b.get("entity_id")]
        not_realized, undeclared = s04.coordinate_change_disagreement(
            a.get("joint_coordinates"), b.get("joint_coordinates"),
            t.get("changed_coordinates"))
        if not_realized:
            codes.append("DECLARED_CHANGE_NOT_REALIZED")
            notes.append("%s says %s changes and its endpoints hold it"
                         % (t.get("entity_id"), ", ".join(not_realized)))
            status = FAIL
        if undeclared:
            codes.append("UNDECLARED_COORDINATE_CHANGE")
            notes.append("%s moves %s and does not declare it"
                         % (t.get("entity_id"), ", ".join(undeclared)))
            status = FAIL
        used += [j for j in (not_realized + undeclared) if j in ev.by_id]
    if used:
        used += ev.basis()
    if status == PASS:
        codes.append("EVERY_TRANSITION_MOVES_WHAT_IT_DECLARES")
    return Verdict("motion_and_transitions", status, codes, used, "; ".join(notes[:5]))


def _spatial_realization(ev: _Evidence) -> Verdict:
    """The mechanism has an arrangement, its joints can move, and it holds together."""
    bodies = ev.fam("Body")
    if not bodies:
        return Verdict("spatial_realization", NOT_APPLICABLE, ["NO_BODY"])
    boxes, envelope_of = ev.boxes(), ev.envelope_of()
    codes, notes, used = [], [], []
    status = PASS
    for body in bodies:
        bid = body.get("entity_id")
        if bid not in boxes:
            codes.append("BODY_WITHOUT_ENVELOPE")
            notes.append("%s has no extent" % bid)
            status = _weaken(status, NOT_ESTABLISHED)
        else:
            used.append(envelope_of.get(bid))
    # WHICH PAIRS MUST TOUCH IS THE TOPOLOGY'S STATEMENT, read off every group,
    # joint and interface this candidate has - so all of them are facts this
    # verdict used. An interface restated over a different pair changes the
    # requirement, not only the answer to it.
    mech = {f: ev.fam(f) for f in ("RigidGroup", "Joint", "Interface")}
    used += ev.ids("RigidGroup", "Joint", "Interface", "Body") + ev.basis()
    for pb, cb in s04.required_contacts(mech):
        a, b = boxes.get(pb), boxes.get(cb)
        if not (a and b):
            continue
        if s04.box_gap(a, b) > 0:
            codes.append("CONNECTED_BODIES_APART")
            notes.append("the topology connects %s and %s and they are apart"
                         % (pb, cb))
            status = FAIL
            used += [envelope_of.get(pb), envelope_of.get(cb)]
    moving = {g for t in ev.fam("Transition")
              for g in ((t.get("path") or {}).get("moving_groups") or [])}
    for group in sorted(moving):
        joint = ev.driving_joint(group)
        if joint is None:
            codes.append("MOVING_GROUP_HAS_NO_JOINT")
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        if s04.axis_index(joint.get("axis_direction")) is None:
            codes.append("JOINT_AXIS_UNUSABLE")
            notes.append("%s declares axis %r" % (joint["entity_id"],
                                                  joint.get("axis_direction")))
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        origin = joint.get("frame_origin")
        if not (isinstance(origin, list) and len(origin) == 3):
            codes.append("JOINT_NOT_PLACED")
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        used.append(joint["entity_id"])
    swept = {v.get("transition") for v in ev.fam("SweptVolume")}
    for t in ev.fam("Transition"):
        if ((t.get("path") or {}).get("moving_groups") or []) \
                and t.get("entity_id") not in swept:
            codes.append("OCCUPANCY_NOT_COMPUTED")
            status = _weaken(status, NOT_ESTABLISHED)
    used += [v.get("entity_id") for v in ev.fam("SweptVolume")]
    # s04a's OWN CONCLUSION THAT THIS ARRANGEMENT CANNOT EXIST. It is a
    # geometric finding by a model, so it is recorded and it weakens - it never
    # decides. An elimination with no positive contradiction beside it means the
    # arrangement is unestablished, not that the mechanism is broken: a
    # deterministic wrapper that turned it into INFEASIBLE would be publishing
    # the model's verdict under this responsibility's name.
    if any(e.get("eliminated") for e in ev.fam("EliminationRecord")):
        codes.append(MODEL_LOCAL_NEGATIVE)
        status = _weaken(status, NOT_ESTABLISHED)
        notes.append("s04a records this arrangement as eliminated; that is a "
                     "finding to weigh, not a contradiction to act on")
    if status == PASS:
        codes.append("ARRANGEMENT_COMPLETE_AND_CONNECTED")
    return Verdict("spatial_realization", status, codes, used, "; ".join(notes[:5]))


def _reach(ev: _Evidence) -> Verdict:
    """Whether an actor can get to what it must - which nothing here can decide.

    A ReachResult is s04a's conclusion ABOUT its own arrangement, not a
    deterministic computation over one. Until a reach basis exists - a hand
    envelope, an access trajectory, a clearance corridor - a reach requirement is
    NOT_ESTABLISHED, and the ReachResult contributes a reason code saying which
    way the model leaned. Reporting the model's answer as this pipeline's would
    make a deterministic wrapper the author of an unfalsifiable claim.
    """
    regions = [r for r in ev.fam("FunctionalRegion")
               if r.get("role") in ("ACCESS", "APERTURE")
               and (r.get("required_by_actors") or r.get("reach_targets"))]
    if not regions:
        return Verdict("reach", NOT_APPLICABLE, ["NO_REACH_REQUIREMENT"])
    codes = ["REACH_BASIS_NOT_ESTABLISHED"]
    results = ev.fam("ReachResult")
    if results:
        codes.append(MODEL_LOCAL_POSITIVE if all(r.get("reachable") for r in results)
                     else MODEL_LOCAL_NEGATIVE)
    return Verdict(
        "reach", NOT_ESTABLISHED, codes, [],
        "%d reach requirement(s); no deterministic reach basis exists, so a "
        "ReachResult is recorded as a model-local finding and decides nothing"
        % len(regions))


def _assemblability(ev: _Evidence) -> Verdict:
    """It can be put together in the order it claims, and each part can get in."""
    steps = {s["entity_id"]: s for s in ev.fam("AssemblyStep")}
    bodies = ev.fam("Body")
    if not steps and len(bodies) < 2:
        return Verdict("assemblability", NOT_APPLICABLE, ["NOTHING_TO_ASSEMBLE"])
    codes, notes, used = [], [], []
    status = PASS
    # A CYCLE AND A CONTRADICTED ORDER ARE POSITIVE CONTRADICTIONS: the order the
    # design states cannot be performed. A dependency naming a step this
    # candidate does not have is an ABSENCE - `depends_on` is not a resolvable
    # reference, so a dangling one is a fact the design has not supplied, and
    # reading it as a broken mechanism would make missing evidence into failure.
    for problem in s03.assembly_order_problems(steps):
        if problem.startswith("ASSEMBLY_DEP_UNKNOWN"):
            codes.append("ASSEMBLY_DEPENDENCY_UNKNOWN")
            status = _weaken(status, NOT_ESTABLISHED)
        else:
            codes.append("ASSEMBLY_ORDER_CONTRADICTED")
            status = FAIL
        notes.append(problem)
        used += sorted(steps)
    if not steps:
        return Verdict("assemblability", NOT_ESTABLISHED, ["ASSEMBLY_ORDER_MISSING"],
                       [], "%d bodies and no assembly step" % len(bodies))
    boxes, envelope_of = ev.boxes(), ev.envelope_of()
    ordered = sorted(steps.values(), key=lambda s: s.get("order_index") or 0)
    placed: List[str] = []
    for step in ordered:
        sid, body = step["entity_id"], step.get("body")
        used.append(sid)
        if str(step.get("path_kind")) == "DEFORMATION_RESOLVED":
            codes.append("DEFORMATION_RESOLVED_PATH")
            status = _weaken(status, NOT_ESTABLISHED)
            placed.append(body)
            continue
        direction = step.get("insertion_direction")
        if not (isinstance(direction, list) and len(direction) == 3):
            codes.append("INSERTION_DIRECTION_MISSING")
            status = _weaken(status, NOT_ESTABLISHED)
            placed.append(body)
            continue
        if body not in boxes:
            codes.append("INSERTION_GEOMETRY_MISSING")
            status = _weaken(status, NOT_ESTABLISHED)
            placed.append(body)
            continue
        hull = _insertion_hull(boxes, body, direction)
        # The hull is built from every box in the arrangement - the span comes
        # from the largest of them - so the clearance answer rests on all of
        # them and on the basis they are measured in.
        used += [e for e in (envelope_of.get(b) for b in boxes) if e] + ev.basis()
        for prior in placed:
            if prior in boxes and s04.overlaps(hull, boxes[prior]):
                # A box overlap is not a collision - the real bodies are smaller
                # than their boxes - so it is what the design has not shown to be
                # clear, never a proof that it is not.
                codes.append("INSERTION_PATH_NOT_CLEAR")
                notes.append("%s entering meets %s" % (body, prior))
                status = _weaken(status, NOT_ESTABLISHED)
        placed.append(body)
    if status == PASS:
        codes.append("ORDER_CONSISTENT_AND_PATHS_CLEAR")
    return Verdict("assemblability", status, codes, used, "; ".join(notes[:5]))


def _insertion_hull(boxes, body, direction):
    """The volume a body sweeps arriving along its declared direction.

    The same construction `assembly_path_check` performs; the span and the
    sampling come from there so the two cannot describe different insertions.
    """
    norm = math.sqrt(sum(x * x for x in direction)) or 1.0
    unit = [x / norm for x in direction]
    span = max(max(boxes[b][1][i] - boxes[b][0][i] for i in range(3))
               for b in boxes) * 2.0
    hull = boxes[body]
    for k in s04.sample(0.0, span, s04.SAMPLES):
        hull = ([min(hull[0][i], boxes[body][0][i] - unit[i] * k) for i in range(3)],
                [max(hull[1][i], boxes[body][1][i] - unit[i] * k) for i in range(3)])
    return hull


def _gross_interference(ev: _Evidence) -> Verdict:
    """Nothing sweeps or sits where it must not - as far as boxes can show.

    NO FAIL PATH, and that is a statement about the evidence rather than about
    the mechanisms. An axis-aligned box overlap is not a collision: the real
    bodies are smaller than their boxes, so no-overlap proves clearance and
    overlap proves nothing. Until the representation holds exact geometry there
    is nothing here that could positively contradict a requirement, and inventing
    a FAIL to balance the vocabulary would manufacture failures the geometry does
    not support.
    """
    boxes = ev.boxes()
    keepouts = [(r["entity_id"], s04.aabb(r["volume"]["centre"],
                                          r["volume"]["half_extent"]))
                for r in ev.fam("FunctionalRegion")
                if r.get("role") == "KEEP_OUT" and isinstance(r.get("volume"), dict)
                and isinstance((r.get("volume") or {}).get("centre"), list)]
    moving = {g for t in ev.fam("Transition")
              for g in ((t.get("path") or {}).get("moving_groups") or [])}
    bodies = [b.get("entity_id") for b in ev.fam("Body")]
    # APPLICABILITY IS ASKED OF THE BODIES, NOT OF THE BOXES. Two bodies coexist
    # whether or not anything has placed them, so geometry that is missing makes
    # the question unanswerable rather than absent - reading applicability off
    # the envelopes would have let an unplaced mechanism report that nothing
    # could interfere.
    if len(bodies) < 2 and not moving and not keepouts:
        return Verdict("gross_interference", NOT_APPLICABLE, ["NOTHING_COEXISTS"])
    declared = {frozenset((i.get("bodies") or [])[:2])
                for i in ev.fam("Interface") if len(i.get("bodies") or []) >= 2}
    envelope_of, codes, notes, used = ev.envelope_of(), [], [], []
    status = PASS
    # EVERY BOX, EVERY INTERFACE AND THE BASIS. "Nothing overlaps that was not
    # declared" is a statement about the whole arrangement: any extent moving,
    # any pair being declared or undeclared, or the basis being withdrawn makes
    # it a different statement.
    used += (ev.ids("Interface", "Body")
             + [e for e in (envelope_of.get(b) for b in boxes) if e] + ev.basis())
    if [b for b in bodies if b not in boxes]:
        codes.append("INTERFERENCE_GEOMETRY_MISSING")
        status = _weaken(status, NOT_ESTABLISHED)
    for volume in ev.fam("SweptVolume"):
        occupancy = (volume.get("occupancy") or {}).get("aabb")
        if not occupancy:
            continue
        hull = (list(occupancy[0]), list(occupancy[1]))
        body = ev.group_body().get(volume.get("rigid_group"))
        used.append(volume.get("entity_id"))
        for rid, kbox in keepouts:
            if s04.overlaps(hull, kbox):
                codes.append("SWEEP_MEETS_KEEP_OUT")
                notes.append("%s sweeps into %s" % (body, rid))
                status = _weaken(status, NOT_ESTABLISHED)
                used.append(rid)
        for other, obox in boxes.items():
            if other == body or frozenset((body, other)) in declared:
                continue
            if s04.overlaps(hull, obox):
                codes.append("SWEEP_MEETS_UNDECLARED_BODY")
                notes.append("%s sweeps into %s" % (body, other))
                status = _weaken(status, NOT_ESTABLISHED)
                used.append(envelope_of.get(other))
    names = sorted(boxes)
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            pair = frozenset((names[x], names[y]))
            if pair in declared or not s04.overlaps(boxes[names[x]], boxes[names[y]]):
                continue
            codes.append("UNDECLARED_PAIR_OVERLAPS")
            notes.append("%s and %s overlap and no interface declares the pair"
                         % (names[x], names[y]))
            status = _weaken(status, NOT_ESTABLISHED)
            used += [envelope_of.get(names[x]), envelope_of.get(names[y])]
    if status == PASS:
        codes.append("NO_CONSERVATIVE_OVERLAP")
    return Verdict("gross_interference", status, codes, used, "; ".join(notes[:5]))


#: The one dispatch table. A domain is added by adding an evaluator here and a
#: value to the contract's vocabulary; nothing else enumerates them.
DOMAIN_EVALUATORS: Dict[str, Callable[[_Evidence], Verdict]] = {
    "physical_realization": _physical_realization,
    "load_reaction_closure": _load_reaction_closure,
    "mobility_disposition": _mobility_disposition,
    "required_configurations": _required_configurations,
    "motion_and_transitions": _motion_and_transitions,
    "spatial_realization": _spatial_realization,
    "reach": _reach,
    "assemblability": _assemblability,
    "gross_interference": _gross_interference,
}


def _weaken(current: str, candidate: str) -> str:
    """FAIL is absorbing; NOT_ESTABLISHED beats PASS. Never the other way."""
    if current == FAIL or candidate == FAIL:
        return FAIL
    if NOT_ESTABLISHED in (current, candidate):
        return NOT_ESTABLISHED
    return current


def aggregate(verdicts: Sequence[Verdict]) -> str:
    """The whole of the eligibility rule.

    Applicable FAIL beats everything; applicable NOT_ESTABLISHED beats PASS;
    NOT_APPLICABLE never blocks. Nothing about complexity enters, because nothing
    about complexity is an input.
    """
    applicable = [v.status for v in verdicts if v.status != NOT_APPLICABLE]
    if FAIL in applicable:
        return INFEASIBLE
    if NOT_ESTABLISHED in applicable:
        return MFA_NOT_ESTABLISHED
    return FEASIBLE


# =====================================================================
# hard requirements
# =====================================================================
SATISFIED, VIOLATED, NOT_YET_EVALUABLE = "SATISFIED", "VIOLATED", "NOT_YET_EVALUABLE"


def _material_class_only(constraint, ev):
    """No canonical material assignment exists anywhere in the representation.

    So the answer is NOT_YET_EVALUABLE, and it stays that way until one does.
    Reading a material off a candidate's prose would be inferring the fact the
    constraint is about, and answering SATISFIED because nothing contradicts it
    would be absence becoming compliance.
    """
    return NOT_YET_EVALUABLE, ["NO_MATERIAL_AUTHORITY"], [], (
        "no canonical material assignment exists; a candidate's description is "
        "not one")


def _prohibited_energy_source(constraint, ev):
    """Same shape: no canonical energy or actuation authority exists yet."""
    return NOT_YET_EVALUABLE, ["NO_ENERGY_AUTHORITY"], [], (
        "no canonical energy or actuation assignment exists")


def _max_overall_dimension(constraint, ev):
    """Evaluable only when the numbers and the limit are in the same units.

    An extent expressed in a RELATIVE basis and a limit in millimetres are not
    comparable, and a conversion rule invented here would be this code choosing
    the scale the design deliberately left free. The condition is the
    ReferenceScale rule, not a shape assumed here: basis ABSOLUTE and `absolute`
    stating {unit, per_unit}. s04 is told never to invent an absolute size for
    something the input left free, so on a design that states no size this is
    NOT_YET_EVALUABLE - which is what that design knows.
    """
    params = constraint.get("parameters") or {}
    limit, unit = params.get("limit"), params.get("unit")
    if not isinstance(limit, (int, float)):
        return NOT_YET_EVALUABLE, ["CONSTRAINT_LIMIT_MISSING"], [], ""
    scales = ev.fam("ReferenceScale")
    if not scales:
        return NOT_YET_EVALUABLE, ["NO_REFERENCE_SCALE"], [], ""
    scale = scales[0]
    if scale.get("basis") != "ABSOLUTE" or not scale.get("absolute"):
        return (NOT_YET_EVALUABLE, ["SCALE_NOT_ABSOLUTE"], [scale.get("entity_id")],
                "extents are expressed in a %r basis; the limit is %s %s and the "
                "two are not comparable" % (scale.get("basis"), limit, unit))
    absolute = scale.get("absolute")
    if not isinstance(absolute, dict) or absolute.get("unit") != unit:
        return (NOT_YET_EVALUABLE, ["UNIT_AMBIGUOUS"], [scale.get("entity_id")],
                "the scale and the limit do not state the same unit")
    per_unit = absolute.get("per_unit")
    if not isinstance(per_unit, (int, float)):
        # NOT DEFAULTED TO 1. What one coordinate is worth is the whole content
        # of an absolute basis, and assuming it would answer the requirement from
        # a number nobody supplied.
        return (NOT_YET_EVALUABLE, ["SCALE_FACTOR_MISSING"], [scale.get("entity_id")],
                "the scale states a unit and not what one coordinate is worth in it")
    boxes = ev.boxes()
    if not boxes:
        return NOT_YET_EVALUABLE, ["NO_EXTENT"], [], ""
    envelope_of = ev.envelope_of()
    lo = [min(b[0][i] for b in boxes.values()) for i in range(3)]
    hi = [max(b[1][i] for b in boxes.values()) for i in range(3)]
    spans = [(hi[i] - lo[i]) * per_unit for i in range(3)]
    axis = params.get("axis", "ANY")
    measured = max(spans) if axis == "ANY" else spans[s04.AXIS_INDEX.get(axis, 0)]
    used = [scale.get("entity_id")] + [envelope_of[b] for b in sorted(boxes)]
    if measured > limit:
        return (VIOLATED, ["OVERALL_DIMENSION_EXCEEDED"], used,
                "%.4g %s exceeds the %s %s limit" % (measured, unit, limit, unit))
    return (SATISFIED, ["WITHIN_OVERALL_DIMENSION"], used,
            "%.4g %s is within the %s %s limit" % (measured, unit, limit, unit))


#: kind -> evaluator. A kind with no entry is NOT_YET_EVALUABLE, which is the
#: honest answer: nothing here knows how to decide it yet.
CONSTRAINT_EVALUATORS: Dict[str, Callable[..., Tuple[str, List[str], List[str], str]]] = {
    "MATERIAL_CLASS_ONLY": _material_class_only,
    "PROHIBITED_ENERGY_SOURCE": _prohibited_energy_source,
    "MAX_OVERALL_DIMENSION": _max_overall_dimension,
}


def evaluate_hard_requirements(ev: _Evidence):
    """One compliance record per current hard requirement. None means none."""
    out = []
    for constraint in ev.fam("DesignConstraint"):
        evaluator = CONSTRAINT_EVALUATORS.get(constraint.get("kind"))
        if evaluator is None:
            status, codes, used, why = (
                NOT_YET_EVALUABLE, ["NO_EVALUATOR_FOR_KIND"], [],
                "nothing here knows how to decide %r" % constraint.get("kind"))
        else:
            status, codes, used, why = evaluator(constraint, ev)
        out.append((constraint, status, codes, used, why))
    return out


# =====================================================================
# the invocation
# =====================================================================
def evaluate_candidate_feasibility(state, candidate_id: str,
                                   run_id: Optional[str] = None,
                                   attempt: int = 1) -> FeasibilityOutcome:
    """Is this candidate mechanically eligible to be chosen from?

    NO PROVIDER. Nothing here calls a model, and there is no prompt to call one
    with: a model may not declare a mechanism feasible, so the responsibility is
    a deterministic reading of what s01-s04 established.

    The ConsumerView is the only engineering channel. `state` is used to build
    it, to validate the patch and for nothing else - reading unscoped state would
    let one candidate's verdict rest on another's evidence with nothing saying so.
    """
    from ..view import consumer_view_for

    invocation = InvocationContext(branch=candidate_id)
    view = consumer_view_for(RESPONSIBILITY, state, invocation=invocation)
    if view.status is not ViewStatus.VIEW_READY:
        return FeasibilityOutcome(
            candidate_id, None, [], [], None,
            ["%s: consumer context is %s; no assessment was produced"
             % (RESPONSIBILITY, view.status.value)]
            + ["%s -> %s" % (a["requirement"], a["verdict"])
               for a in view.assessment if a["verdict"] != "SATISFIED"],
            view.as_dict())

    ev = _Evidence(view.payload(), candidate_id)
    verdicts = [DOMAIN_EVALUATORS[d](ev) for d in DOMAINS]
    compliance = evaluate_hard_requirements(ev)
    status = aggregate(verdicts)

    prov = "feasibility:deterministic"
    ops: List[Op] = []
    domain_ids, raw_union = [], set()
    for v in verdicts:
        eid = "FDA-%s-%s" % (candidate_id, _TOKEN[v.domain])
        domain_ids.append(eid)
        raw_union |= set(v.premises)
        ops.append(Op("CREATE", "FeasibilityDomainAssessment", eid,
                      {"candidate": candidate_id, "domain": v.domain,
                       "status": v.status, "reason_codes": v.reason_codes,
                       "summary": v.summary},
                      prov, premise_refs=sorted({candidate_id} | set(v.premises))))
    # THE RAW UNION IS CARRIED DIRECTLY. `_propagate` is one hop, so naming the
    # domain records would leave this standing when an envelope the spatial
    # verdict read is superseded: the domain record goes STALE and stops there.
    ops.append(Op("CREATE", "MechanicalFeasibilityAssessment",
                  "MFA-%s" % candidate_id,
                  {"candidate": candidate_id, "status": status,
                   "domain_assessments": domain_ids,
                   "evaluated_domains": list(DOMAINS),
                   "findings": [_finding(v) for v in verdicts
                                if v.status in (FAIL, NOT_ESTABLISHED)]},
                  prov,
                  premise_refs=sorted({candidate_id} | set(domain_ids) | raw_union)))
    for constraint, hstatus, codes, used, why in compliance:
        cid = constraint.get("entity_id")
        ops.append(Op("CREATE", "HardRequirementCompliance",
                      "HRC-%s-%s" % (candidate_id, cid),
                      {"candidate": candidate_id, "constraint": cid,
                       "status": hstatus, "why": why or "; ".join(codes)},
                      prov,
                      premise_refs=sorted({candidate_id, cid}
                                          | {u for u in used if u})))

    patch = StagePatch(
        patch_id="%s-%s-feasibility" % (run_id or state.run_id, candidate_id),
        run_id=run_id or state.run_id, stage_id=RESPONSIBILITY,
        stage_attempt=attempt, parent_state_hash=state.state_hash(),
        operations=ops, execution_status="SUCCESS",
        provenance={"purpose": "decide mechanical eligibility",
                    "provider": "deterministic"},
        # DELIBERATELY EMPTY. `declared_incompleteness` is a stage saying it
        # could not finish its own work; a NOT_ESTABLISHED domain is this stage
        # finishing it and reporting what the design has not established. Putting
        # the verdicts here would make a complete answer look like a failed
        # invocation, and a runner would refuse the patch that contains the
        # finding.
        declared_incompleteness=[])
    problems = state.validate(patch)
    return FeasibilityOutcome(candidate_id, status, verdicts, compliance,
                              None if problems else patch, problems, view.as_dict())


def _finding(v: Verdict) -> str:
    return "%s: %s (%s)%s" % (v.domain, v.status, ", ".join(v.reason_codes),
                              " - " + v.summary if v.summary else "")
