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

    APPLICABILITY IS READ FROM THE DEMAND, NEVER FROM THE REALIZATION.
    NOT_APPLICABLE means the design ASKS no question here - no actor must reach
    anything, no effect requires motion, no load is applied. A demand with no
    realization is NOT_ESTABLISHED. Reading applicability off the realization
    would let a candidate escape a domain by failing to produce the very entity
    that domain examines: no Transition, therefore no motion question, therefore
    nothing to answer. That is the loudest way absence becomes a pass.

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

#: THE EFFECTS THAT DEMAND MOTION, taken from `PhysicalEffectObligation.effect`'s
#: own vocabulary. PREVENT_MOTION is deliberately not among them: it demands that
#: motion NOT occur, which is a different question and not this one asked
#: backwards.
MOTION_EFFECTS = ("TRANSMIT_MOTION", "CONVERT_MOTION", "PERMIT_MOTION")

#: The axes a dimensional limit may be stated on. `ANY` means the largest.
#: Anything else is a word this code does not know, and it says so rather than
#: choosing one - an unrecognised axis silently becoming X answered a
#: requirement about a direction nobody named.
DIMENSION_AXES = ("ANY", "X", "Y", "Z")

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

    #: What this candidate currently says a body's extent is.
    UNIQUE, MISSING, AMBIGUOUS = "UNIQUE", "MISSING", "AMBIGUOUS"

    def _envelopes_by_body(self) -> Dict[Any, List[Dict[str, Any]]]:
        out: Dict[Any, List[Dict[str, Any]]] = {}
        for e in self.fam("Envelope"):
            out.setdefault(e.get("body"), []).append(e)
        return out

    def extent_status(self, body: str) -> str:
        """UNIQUE, MISSING or AMBIGUOUS. Three answers, not two.

        DETECTING A DUPLICATE IS NOT ENOUGH. The evaluator used to notice that a
        body carried two current extents, weaken to NOT_ESTABLISHED - and then go
        on to measure with whichever box the map happened to keep, which could
        still produce a positive FAIL. `_weaken` does not undo a FAIL, so an
        ambiguity that was recognised still decided the verdict, and which way it
        decided depended on insertion order.
        """
        found = self._envelopes_by_body().get(body) or []
        usable = [e for e in found if s04._extent_box(e)]
        if len(usable) == 1:
            return self.UNIQUE
        return self.AMBIGUOUS if len(found) > 1 else self.MISSING

    def boxes(self) -> Dict[str, Tuple[List[float], List[float]]]:
        """body -> its ONE current extent. AMBIGUOUS BODIES ARE ABSENT.

        A body the design describes twice is a body this responsibility has no
        usable geometry for, so it is left out exactly as an unplaced one is -
        and every predicate downstream, which already refuses to measure what it
        cannot see, refuses this too. That is the whole quarantine: no geometric
        answer can be built from a box nobody chose.

        s04's `_view_boxes` keeps the last envelope per body and is still what
        s04's own refinement barrier reads; it is left alone and simply not used
        for an authoritative verdict.
        """
        if len(self.basis()) > 1:
            # TWO CURRENT BASES, so two extents are not two numbers in one
            # coordinate system - and comparing them would be arithmetic across
            # a boundary nothing defines. The same quarantine: unmeasurable
            # rather than measured badly.
            return {}
        out = {}
        for body, found in self._envelopes_by_body().items():
            usable = [e for e in found if s04._extent_box(e)]
            if body and len(usable) == 1:
                out[body] = s04._extent_box(usable[0])
        return out

    def envelope_of(self) -> Dict[str, str]:
        """body -> the id of its ONE extent. Ambiguous bodies are absent here
        too: naming one of two competing envelopes as the premise of a value
        would record a dependency on a record nothing selected."""
        out = {}
        for body, found in self._envelopes_by_body().items():
            usable = [e for e in found if s04._extent_box(e)]
            if body and len(usable) == 1:
                out[body] = usable[0].get("entity_id")
        return out

    def pair_expectation(self):
        """(pair -> TOUCHES/CLEAR/UNDECLARED, pairs the design describes twice).

        Only TOUCHES exempts a pair from interference, and a pair declared BOTH
        ways exempts nothing: a dict comprehension kept whichever interface came
        last, so a CONTACT and a CLEARANCE over the same two bodies resolved by
        insertion order. Disagreement is a finding, not a tie to break.

        One reader for both domains that ask. `gross_interference` needs to know
        which pairs are exempt; `spatial_realization` needs to know which pairs
        the topology REQUIRES to touch, and a pair the design describes two ways
        requires nothing it can be held to.
        """
        stated: Dict[Any, set] = {}
        for i in self.fam("Interface"):
            bodies_of = (i.get("bodies") or [])[:2]
            if len(bodies_of) >= 2:
                stated.setdefault(frozenset(bodies_of), set()).add(
                    s04.interface_expectation(i))
        return ({p: sorted(e)[0] for p, e in stated.items() if len(e) == 1},
                {p for p, e in stated.items() if len(e) > 1})

    def envelopes_of(self, body: str) -> List[str]:
        """Every envelope id currently claiming this body. What an ambiguity is
        made of, and therefore what a finding about it rests on."""
        return sorted(e.get("entity_id")
                      for e in (self._envelopes_by_body().get(body) or [])
                      if e.get("entity_id"))

    def group_body(self) -> Dict[str, str]:
        return {g["entity_id"]: g.get("body") for g in self.fam("RigidGroup")}

    #: RETIRED. `duplicated("Envelope", "body")` reported that a body carried
    #: two extents and left the arbitrary box in play, so a recognised ambiguity
    #: could still decide a verdict. `extent_status` and `boxes` replace it by
    #: making the ambiguous body unmeasurable rather than merely noted - a
    #: detector beside a lookup that ignores it is worse than neither.
    _RETIRED_DUPLICATED = "replaced by extent_status/boxes quarantine"

    def joints_of(self, group: str) -> List[Dict[str, Any]]:
        """EVERY joint whose coordinate moves this group, not the first one.

        `driving_joint` returned `next(j for j in Joint if child_group == group)`,
        so which joint answered a question was decided by insertion order. On a
        group carrying a PRISMATIC and a REVOLUTE joint, a basis about RZ was
        answered by the slider - and answered FAIL, because two configurations
        that differ in rotation share a translation. An arbitrary choice
        producing a positive contradiction is the worst form this defect takes.
        """
        return [j for j in self.fam("Joint") if j.get("child_group") == group]

    def drivers_for(self, group: str, dof: str):
        """(joints that carry this cell, joints whose axis cannot be read).

        The address is (rigid_group, dof) and BOTH components select. Compatible
        means the joint's own class and axis leave that DOF free, asked of
        `free_dof` so the answer is s03's. An unreadable axis is separated out
        rather than passed to `free_dof`, which would answer from its Z default.
        """
        drivers, unreadable = [], []
        for j in self.joints_of(group):
            if s04.axis_index(j.get("axis_direction")) is None:
                unreadable.append(j)
            elif dof in s03.free_dof(j.get("joint_type"), j.get("axis_direction")):
                drivers.append(j)
        return drivers, unreadable

    def states_for(self, configuration: str) -> List[Dict[str, Any]]:
        """EVERY state realizing this configuration. Two is not one."""
        return [st for st in self.fam("State")
                if (st.get("configuration") or st.get("name")) == configuration]

    # -- WHAT THE DESIGN DEMANDS, as against what it has built ---------
    def reach_demands(self) -> List[Dict[str, Any]]:
        """Actors that must reach something. The demand, not its realization.

        `Actor.must_reach` is a REQUIRED field, so an actor that reaches for
        nothing states an empty list and is not a demand. A FunctionalRegion is
        how a candidate ANSWERS this; its absence is the answer missing, never
        the question missing.
        """
        return [a for a in self.fam("Actor") if a.get("must_reach")]

    def motion_demands(self) -> List[Dict[str, Any]]:
        """Effect obligations whose own declared effect requires movement."""
        return [p for p in self.fam("PhysicalEffectObligation")
                if p.get("effect") in MOTION_EFFECTS]


# =====================================================================
# the nine domains
# =====================================================================
def _physical_realization(ev: _Evidence) -> Verdict:
    """Every required effect is realized by an interaction that produces IT.

    POINTING AT AN OBLIGATION IS NOT DISCHARGING IT. `discharges_effect` says
    which demand an interaction answers; `effect` says what the interaction
    actually does, and the two are separate fields because they can disagree. An
    interaction that LOCATEs while naming an obligation to TRANSMIT_FORCE has
    answered nothing, and accepting it on the reference alone made the typed
    vocabulary decorative - any interaction could discharge any obligation.

    EXACT MATCH, because no canonical compatibility relation between effects
    exists. Inventing one here - deciding that CONVERT_MOTION covers
    TRANSMIT_MOTION - would be this file authoring physical semantics that
    belong to the contract.
    """
    demands = ev.fam("PhysicalEffectObligation")
    if not demands:
        return Verdict("physical_realization", NOT_APPLICABLE, ["NO_EFFECT_DEMANDED"])
    by_demand: Dict[Any, List[Dict[str, Any]]] = {}
    for i in ev.fam("PhysicalInteraction"):
        by_demand.setdefault(i.get("discharges_effect"), []).append(i)
    used, codes, notes = [], [], []
    status = PASS
    for demand in demands:
        eid, effect = demand.get("entity_id"), demand.get("effect")
        # THE OBLIGATION IS NAMED EITHER WAY. It is a present fact that was read,
        # and it is the reason the domain is unsatisfied; what is absent is the
        # interaction, and that has no id to name. Withdrawing the demand must
        # cost this verdict its authority.
        used.append(eid)
        claimants = by_demand.get(eid) or []
        used += [i.get("entity_id") for i in claimants]
        if not claimants:
            codes.append("EFFECT_NOT_DISCHARGED")
            notes.append("%s has no interaction" % eid)
            status = _weaken(status, NOT_ESTABLISHED)
        elif not any(i.get("effect") == effect for i in claimants):
            codes.append("EFFECT_TYPE_MISMATCH")
            notes.append("%s demands %s and the interaction(s) naming it do %s"
                         % (eid, effect,
                            ", ".join(sorted({str(i.get("effect")) for i in claimants}))))
            status = _weaken(status, NOT_ESTABLISHED)
    if status == PASS:
        codes.append("ALL_EFFECTS_DISCHARGED")
    return Verdict("physical_realization", status, codes, used, "; ".join(notes[:5]))


VALID, CONTRADICTORY, UNRESOLVED = "VALID", "CONTRADICTORY", "UNRESOLVED"


def _classify_path(ev, load, path, interfaces, boxes, envelope_of):
    """ONE load path, classified on its own: (verdict, codes, notes, premises).

    Nothing here looks at any other path. Aggregation is the caller's, and
    keeping the two apart is what makes the answer independent of which path was
    written down first.
    """
    codes, notes, used = [], [], [path.get("entity_id")]
    verdict = VALID
    terminus, expected = path.get("terminates_at"), load.get("reacted_at_site")
    if not terminus:
        codes.append("LOAD_PATH_OPEN")
        verdict = UNRESOLVED
    elif expected and terminus != expected:
        codes.append("TERMINUS_NOT_THE_DECLARED_SITE")
        notes.append("%s closes at %s and %s is reacted at %s"
                     % (path.get("entity_id"), terminus, load.get("entity_id"),
                        expected))
        verdict = CONTRADICTORY
        used += [terminus, expected]
    else:
        site = ev.by_id.get(terminus)
        used.append(terminus)
        if site is None:
            codes.append("TERMINAL_SITE_NOT_GIVEN")
            verdict = UNRESOLVED
        elif site.get("boundary_side") != "EXTERNAL":
            codes.append("TERMINAL_SITE_INTERNAL")
            notes.append("%s closes inside the product" % path.get("entity_id"))
            verdict = CONTRADICTORY
    hops = [h for h in (path.get("ordered_hops") or []) if isinstance(h, str)]
    if len(hops) < 1:
        codes.append("LOAD_PATH_TOO_SHORT")
        verdict = _worse(verdict, UNRESOLVED)
    for h in hops:
        iface = interfaces.get(h)
        if iface is None:
            codes.append("HOP_NOT_AN_INTERFACE")
            verdict = _worse(verdict, UNRESOLVED)
            continue
        used.append(h)
        pair = [b for b in (iface.get("bodies") or []) if b in boxes]
        if len(pair) < 2:
            # WHICH bodies, and WHY each is unmeasurable. An ambiguous extent
            # and an absent one are both reasons this hop cannot be checked, and
            # they are not the same fact.
            for b in (iface.get("bodies") or []):
                if b in boxes:
                    continue
                code, note, premises = _extent_finding(ev, b, "HOP_GEOMETRY_MISSING")
                codes.append(code)
                notes.append(note)
                used += premises
            verdict = _worse(verdict, UNRESOLVED)
            continue
        # THE EXTENTS ARE NAMED WHATEVER THE ANSWER, and so is the basis they
        # are expressed in. A gap that is not there today is a gap either body
        # could acquire by being moved, so "these two touch" rests on both
        # extents exactly as much as "these two are apart" does.
        used += [e for e in (envelope_of.get(pair[0]),
                             envelope_of.get(pair[1])) if e] + ev.basis()
        if s04.box_gap(boxes[pair[0]], boxes[pair[1]]) > 0:
            codes.append("HOP_BODIES_APART")
            notes.append("%s carries %s -> %s and they are apart"
                         % (h, pair[0], pair[1]))
            verdict = CONTRADICTORY
    for x, y in zip(hops, hops[1:]):
        ia, ib = interfaces.get(x), interfaces.get(y)
        if ia and ib and not (set(ia.get("bodies") or [])
                              & set(ib.get("bodies") or [])):
            codes.append("HOPS_NOT_CONNECTED")
            notes.append("%s and %s share no body" % (x, y))
            verdict = CONTRADICTORY
    return verdict, codes, notes, used


def _worse(current: str, candidate: str) -> str:
    """CONTRADICTORY absorbs; UNRESOLVED beats VALID."""
    if CONTRADICTORY in (current, candidate):
        return CONTRADICTORY
    if UNRESOLVED in (current, candidate):
        return UNRESOLVED
    return VALID


def _load_reaction_closure(ev: _Evidence) -> Verdict:
    """Every load reaches the site its own load case names, outside the product.

    EVERY PATH IS EVALUATED, NOT ONE OF THEM. The index used to be
    `{path.load_case: path}`, which keeps whichever path was written last, so a
    load with two declared routes got a verdict decided by insertion order - a
    valid route and a route closing inside the product gave PASS or FAIL
    depending on nothing at all.

    The policy is stated once and applied to all of them: a route the design
    currently asserts and that contradicts itself is a contradiction whether or
    not some other route works, because the design is asserting both. An
    unresolved route beside a valid one leaves the closure unestablished for the
    same reason - the design declared a route it has not shown.
    """
    loads = ev.fam("LoadCase")
    if not loads:
        return Verdict("load_reaction_closure", NOT_APPLICABLE, ["NO_LOAD_CASE"])
    by_case: Dict[Any, List[Dict[str, Any]]] = {}
    for p in ev.fam("LoadPath"):
        by_case.setdefault(p.get("load_case"), []).append(p)
    interfaces = {i["entity_id"]: i for i in ev.fam("Interface")}
    boxes = ev.boxes()
    envelope_of = ev.envelope_of()
    used, codes, notes = [], [], []
    status = PASS
    for load in loads:
        lid = load.get("entity_id")
        # The load case is named whether or not a path answers it: the demand is
        # present, and withdrawing it withdraws the question.
        used.append(lid)
        routes = by_case.get(lid) or []
        if not routes:
            codes.append("LOAD_PATH_MISSING")
            notes.append("%s has no path" % lid)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        verdicts = []
        for path in sorted(routes, key=lambda p: p.get("entity_id") or ""):
            verdict, path_codes, path_notes, path_used = _classify_path(
                ev, load, path, interfaces, boxes, envelope_of)
            verdicts.append(verdict)
            codes += path_codes
            notes += path_notes
            used += path_used
        if CONTRADICTORY in verdicts:
            codes.append("DECLARED_ROUTE_CONTRADICTS_ITSELF"
                         if VALID in verdicts else "LOAD_ROUTE_CONTRADICTED")
            status = FAIL
        elif UNRESOLVED in verdicts:
            status = _weaken(status, NOT_ESTABLISHED)
        elif len(verdicts) > 1:
            codes.append("EVERY_DECLARED_ROUTE_CLOSES")
    if status == PASS:
        codes.append("EVERY_LOAD_CLOSES_EXTERNALLY")
    return Verdict("load_reaction_closure", status, codes, used, "; ".join(notes[:5]))


def _required_motion_cells(ev: _Evidence):
    """(group, configuration, dof) cells the design REQUIRES to move.

    THE ADDRESS IS ALL THREE COMPONENTS, because that is what a mobility cell is.
    Dropping the configuration and matching on (group, dof) asked "is this DOF
    ever blocked anywhere", which is a different question with a different
    answer: a latch free when open and held when closed is a correct mechanism,
    and the collapsed lookup read its closed cell as a contradiction of a motion
    only its open cell is required to perform.

    From declared motion requirements only - a distinguishing basis, or a
    transition whose changed joint has exactly one free DOF. NOT the 6-DOF
    bookkeeping grid: totality is what the enumerator guarantees, and reading a
    feasibility verdict off it would be reading it off this code.

    A distinguishing basis is a statement about the configuration that CARRIES
    it - "what makes this one a different one" - so it requires that
    configuration's cell alone. A transition happens BETWEEN two configurations,
    so it requires the cell in each endpoint: a coordinate that changes from one
    to the other must be free at both ends of the change.
    """
    cells, ambiguous, used = [], [], []
    for cfg in ev.fam("Configuration"):
        for item in (cfg.get("distinguishing_basis") or []):
            if not isinstance(item, dict):
                continue
            group, dof = item.get("rigid_group"), item.get("dof")
            if group and dof:
                cells.append((group, cfg.get("entity_id"), dof))
                used.append(cfg.get("entity_id"))
    states = {st.get("entity_id"): st for st in ev.fam("State")}
    for t in ev.fam("Transition"):
        tid = t.get("entity_id")
        endpoints = [states.get(t.get(f)) for f in ("from_state", "to_state")]
        configs = [(st or {}).get("configuration") for st in endpoints]
        for jid in (t.get("changed_coordinates") or []):
            joint = ev.by_id.get(jid)
            # THE REFERENT MUST BE A VISIBLE JOINT. A changed coordinate that
            # resolves to no joint in the view - or to an entity of some other
            # family - produced no requirement at all under the old `continue`:
            # the motion the transition declared simply vanished instead of being
            # questioned, which is the demand-hidden-by-absence defect one level
            # down.
            if not isinstance(joint, dict) or joint.get("_family") != "Joint":
                ambiguous.append((
                    "CHANGED_COORDINATE_NOT_A_JOINT",
                    "%s declares %s changes and it names no visible joint"
                    % (tid, jid)))
                used += [tid, jid]
                continue
            # `free_dof` DEFAULTS AN UNREADABLE AXIS TO Z. That default is S-5's
            # and stays so, but a feasibility verdict must not rest on it: an
            # axis this pipeline cannot read is a cell nobody actually declared,
            # so the requirement is unresolvable rather than silently assumed to
            # be about Z. `spatial_realization` already refuses the same axis;
            # this refuses it for the cell address it would otherwise fabricate.
            if s04.axis_index(joint.get("axis_direction")) is None:
                ambiguous.append((
                    "REQUIRED_MOTION_AXIS_UNREADABLE",
                    "%s changes %s whose axis %r names no coordinate"
                    % (tid, jid, joint.get("axis_direction"))))
                used += [tid, jid]
                continue
            free = s03.free_dof(joint.get("joint_type"), joint.get("axis_direction"))
            group = joint.get("child_group")
            if len(free) == 1 and group:
                for cfg in [c for c in configs if c]:
                    cells.append((group, cfg, sorted(free)[0]))
                used += [tid, jid] + [
                    st.get("entity_id") for st in endpoints if st]
            elif group:
                # A multi-DOF class: the representation does not say WHICH
                # coordinate this transition moves, and guessing would invent the
                # requirement the verdict is about.
                ambiguous.append((
                    "MULTI_DOF_JOINT_NOT_RESOLVABLE",
                    "%s leaves more than one DOF free at %s and the "
                    "representation does not say which one moves" % (jid, group)))
                used += [tid, jid]
    return sorted(set(cells)), ambiguous, used


def _disposition_support(ev: _Evidence, d, group: str, dof: str):
    """Whether the joint an INTENDED cell cites really leaves that cell free.

    Reads `free_dof`, so the question "does this joint class free this DOF" has
    the one answer s03's derivation used to author the claim.
    """
    joint = ev.by_id.get(d.get("by_joint"))
    if not isinstance(joint, dict) or joint.get("_family") != "Joint":
        return [("DISPOSITION_PREMISE_NOT_A_JOINT",
                 "%s/%s cites %s, which is no joint of this candidate"
                 % (group, dof, d.get("by_joint")))]
    if joint.get("child_group") != group:
        return [("DISPOSITION_JOINT_DRIVES_ANOTHER_GROUP",
                 "%s/%s cites %s, whose child is %s"
                 % (group, dof, joint["entity_id"], joint.get("child_group")))]
    if s04.axis_index(joint.get("axis_direction")) is None:
        # `free_dof` would answer from its Z default here, and an answer from a
        # default cannot confirm or refute anything.
        return [("DISPOSITION_JOINT_AXIS_UNREADABLE",
                 "%s/%s cites %s, whose axis %r names no coordinate"
                 % (group, dof, joint["entity_id"], joint.get("axis_direction")))]
    if dof not in s03.free_dof(joint.get("joint_type"), joint.get("axis_direction")):
        return [("DISPOSITION_JOINT_DOES_NOT_FREE_IT",
                 "%s/%s cites %s, a %s about %s, which leaves %s free"
                 % (group, dof, joint["entity_id"], joint.get("joint_type"),
                    joint.get("axis_direction"),
                    ", ".join(sorted(s03.free_dof(joint.get("joint_type"),
                                                  joint.get("axis_direction"))))
                    or "nothing"))]
    return []


def _mobility_disposition(ev: _Evidence) -> Verdict:
    """Every DOF the design requires to move is dispositioned as free."""
    cells, ambiguous, used = _required_motion_cells(ev)
    demanded = ev.motion_demands()
    if not cells and not ambiguous:
        if demanded:
            # THE DEMAND IS THE APPLICABILITY TEST. An effect obligation that
            # requires movement is a motion question whether or not anything has
            # been built to answer it, and reporting NOT_APPLICABLE here would
            # excuse the candidate for having produced nothing to judge.
            return Verdict("mobility_disposition", NOT_ESTABLISHED,
                           ["MOTION_DEMANDED_WITHOUT_REALIZATION"],
                           [p.get("entity_id") for p in demanded],
                           "%d effect obligation(s) require movement and no "
                           "configuration or transition declares which DOF moves"
                           % len(demanded))
        return Verdict("mobility_disposition", NOT_APPLICABLE, ["NO_REQUIRED_MOTION"])
    # EVERY DISPOSITION OF A CELL, not the last one indexed. Two records
    # dispositioning one cell is two answers to what is known about it, and
    # assignment kept whichever came last - so which MobilityExpectation a
    # verdict rested on, and whether that verdict was INTENDED or BLOCKED_BY,
    # could turn on insertion order.
    disposed: Dict[Any, List[Tuple[str, Dict[str, Any]]]] = {}
    for mex in ev.fam("MobilityExpectation"):
        for d in (mex.get("dispositions") or []):
            if isinstance(d, dict):
                disposed.setdefault((d.get("rigid_group"), d.get("configuration"),
                                     d.get("dof")), []).append(
                                         (mex.get("entity_id"), d))
    codes, notes = [], []
    status = PASS
    for code, note in ambiguous:
        # EACH UNRESOLVABLE REQUIREMENT REPORTS ITS OWN REASON. A multi-DOF
        # class, an unreadable axis and a coordinate that names no joint are
        # three different ways the design has not said which cell must move, and
        # one code standing for all three would describe two of them wrongly.
        codes.append(code)
        notes.append(note)
        status = _weaken(status, NOT_ESTABLISHED)
    for cell in cells:
        group, configuration, dof = cell
        rows = disposed.get(cell) or []
        if not rows:
            codes.append("REQUIRED_CELL_NOT_DISPOSITIONED")
            notes.append("%s/%s/%s has no disposition" % cell)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        if len(rows) > 1:
            codes.append("CELL_DISPOSITIONED_TWICE")
            notes.append("%s/%s/%s is dispositioned by %s" % (
                cell + (", ".join(sorted(m for m, _d in rows)),)))
            status = _weaken(status, NOT_ESTABLISHED)
            used += sorted(m for m, _d in rows)
            continue
        mid, d = rows[0]
        verdict = d.get("disposition")
        if verdict == "INTENDED" and d.get("by_joint"):
            used += [mid, d["by_joint"]]
            # THE CITED JOINT MUST ACTUALLY FREE THIS CELL. `by_joint` is a
            # reference, and the write boundary checks that it resolves to a
            # Joint - not that the joint's own class and axis leave this DOF of
            # this group free. Taking the citation on trust let a disposition
            # assert mobility its own evidence does not provide, which is the
            # typed-relation-accepted-by-id defect the effect discharge had.
            #
            # NOT_ESTABLISHED rather than FAIL: a miscited premise fails to
            # support the motion, where a FAIL would claim the design has shown
            # the motion cannot happen.
            for code, note in _disposition_support(ev, d, group, dof):
                codes.append(code)
                notes.append(note)
                status = _weaken(status, NOT_ESTABLISHED)
        elif verdict in ("BLOCKED_BY", "IRRELEVANT_BECAUSE"):
            codes.append("REQUIRED_MOTION_CONTRADICTED")
            notes.append("%s must move in %s and is %s"
                         % (group + "/" + dof, configuration, verdict))
            status = FAIL
            used += [mid] + [d[f] for f in ("constraint_relation", "scenario")
                             if d.get(f)]
        else:
            codes.append("REQUIRED_CELL_UNDISPOSITIONED")
            notes.append("%s/%s/%s is %s" % (group, configuration, dof, verdict))
            status = _weaken(status, NOT_ESTABLISHED)
            used.append(mid)
    if status == PASS:
        codes.append("EVERY_REQUIRED_CELL_INTENDED")
    return Verdict("mobility_disposition", status, codes, used, "; ".join(notes[:5]))


def _resolve_driver(ev: _Evidence, group: str, dof: str):
    """(joint, code, note, premises) for the joint that carries (group, dof).

    ONE COMPATIBLE JOINT OR NO ANSWER. Zero is a requirement the topology does
    not support; more than one is a requirement the topology does not resolve.
    Neither is a licence to pick, and picking is what made a slider answer for a
    hinge. When ambiguity is the finding, the competing joints ARE the positive
    facts that establish it, so they are the premises.
    """
    drivers, unreadable = ev.drivers_for(group, dof)
    if len(drivers) == 1:
        return drivers[0], None, None, [drivers[0]["entity_id"]]
    if len(drivers) > 1:
        names = sorted(j["entity_id"] for j in drivers)
        return (None, "DISTINCTNESS_DRIVER_AMBIGUOUS",
                "%s/%s could be carried by %s and the design does not say which"
                % (group, dof, " or ".join(names)), names)
    if unreadable:
        names = sorted(j["entity_id"] for j in unreadable)
        return (None, "DISTINCTNESS_DRIVER_AXIS_UNREADABLE",
                "%s/%s: %s declare axes that name no coordinate"
                % (group, dof, ", ".join(names)), names)
    return (None, "DISTINCTNESS_DRIVER_UNKNOWN",
            "no joint of this candidate leaves %s free at %s" % (dof, group), [])


def _required_configurations(ev: _Evidence) -> Verdict:
    """Each configuration is realized, and declared distinctness is real.

    A NAMED REFERENCE IS AN ADDRESS, NOT A SUGGESTION. `differs_from` names the
    siblings this configuration must differ from; each is evaluated exactly, and
    one that is absent or unrealized makes the comparison unestablished. The
    fallback that compared against "some other realized configuration" turned a
    reference to an entity the design does not have into a PASS earned by an
    entity nobody named.
    """
    configs = ev.fam("Configuration")
    if not configs:
        return Verdict("required_configurations", NOT_APPLICABLE, ["NO_CONFIGURATION"])
    codes, notes, used = [], [], []
    status = PASS
    realized = {}
    for cfg in configs:
        cid = cfg.get("entity_id")
        states = ev.states_for(cid)
        if not states:
            codes.append("CONFIGURATION_NOT_REALIZED")
            notes.append("%s has no state" % cid)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        if len(states) > 1:
            # Two states for one configuration is two answers to "what is it set
            # to". Indexing by configuration used to keep whichever came first.
            codes.append("CONFIGURATION_REALIZED_TWICE")
            notes.append("%s is realized by %s" % (cid, ", ".join(
                sorted(st.get("entity_id") for st in states))))
            status = _weaken(status, NOT_ESTABLISHED)
            used += [cid] + sorted(st.get("entity_id") for st in states)
            continue
        realized[cid] = states[0]
        used += [cid, states[0].get("entity_id")]
    for cfg in configs:
        cid = cfg.get("entity_id")
        mine = realized.get(cid)
        for item in (cfg.get("distinguishing_basis") or []):
            if not isinstance(item, dict):
                continue
            group, dof = item.get("rigid_group"), item.get("dof")
            named = [o for o in (item.get("differs_from") or [])
                     if isinstance(o, str) and o]
            used.append(cid)
            if not named:
                # "different" with nothing to be different from. Comparing
                # against everything else was this code inventing the sibling.
                codes.append("DISTINCTNESS_NAMES_NO_SIBLING")
                notes.append("%s declares a basis on %s/%s and names no sibling"
                             % (cid, group, dof))
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            if mine is None:
                codes.append("DISTINCTNESS_NOT_REALIZED_HERE")
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            joint, code, note, premises = _resolve_driver(ev, group, dof)
            used += premises
            if joint is None:
                codes.append(code)
                notes.append(note)
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            jid = joint["entity_id"]
            q = (mine.get("joint_coordinates") or {}).get(jid)
            for other in named:
                sibling = realized.get(other)
                if sibling is None:
                    codes.append("DISTINCTNESS_SIBLING_NOT_REALIZED")
                    notes.append("%s must differ from %s, which this candidate "
                                 "does not realize" % (cid, other))
                    status = _weaken(status, NOT_ESTABLISHED)
                    continue
                p = (sibling.get("joint_coordinates") or {}).get(jid)
                used.append(sibling.get("entity_id"))
                if q is None or p is None:
                    codes.append("DISTINCTNESS_COORDINATE_MISSING")
                    notes.append("%s and %s do not both state a coordinate for %s"
                                 % (cid, other, jid))
                    status = _weaken(status, NOT_ESTABLISHED)
                elif q == p:
                    codes.append("DECLARED_DISTINCTNESS_NOT_REALIZED")
                    notes.append("%s and %s both realize %s at %r"
                                 % (cid, other, jid, q))
                    status = FAIL
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
    declaring = [cfg for cfg in ev.fam("Configuration")
                 if cfg.get("distinguishing_basis")]
    demanded = ev.motion_demands()
    if not transitions:
        # A STATE CHANGE IS REQUIRED AND NOTHING DESCRIBES IT. Absent, not
        # inapplicable - that difference is the whole point of the domain, and
        # the demand may come from either direction: a configuration declaring
        # what makes it different, or an effect obligation that cannot be
        # discharged without movement.
        if declaring or demanded:
            return Verdict(
                "motion_and_transitions", NOT_ESTABLISHED,
                ["REQUIRED_TRANSITION_MISSING"],
                [e.get("entity_id") for e in declaring + demanded],
                "%d motion demand(s) and no transition realizes any of them"
                % len(declaring + demanded))
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
            code, note, premises = _extent_finding(ev, bid, "BODY_WITHOUT_ENVELOPE")
            codes.append(code)
            notes.append(note)
            used += premises
            status = _weaken(status, NOT_ESTABLISHED)
        else:
            used.append(envelope_of.get(bid))
    # WHICH PAIRS MUST TOUCH IS THE TOPOLOGY'S STATEMENT, read off every group,
    # joint and interface this candidate has - so all of them are facts this
    # verdict used. An interface restated over a different pair changes the
    # requirement, not only the answer to it.
    mech = {f: ev.fam(f) for f in ("RigidGroup", "Joint", "Interface")}
    used += ev.ids("RigidGroup", "Joint", "Interface", "Body") + ev.basis()
    _expectation, conflicted = ev.pair_expectation()
    for pb, cb in s04.required_contacts(mech):
        a, b = boxes.get(pb), boxes.get(cb)
        if not (a and b):
            continue
        if frozenset((pb, cb)) in conflicted:
            # THE PAIR IS DESCRIBED TWO WAYS - required to meet and required to
            # stay clear. Whether they are apart cannot decide anything: it
            # contradicts one declaration and satisfies the other, so a FAIL here
            # would report a broken mechanism where the description is what is
            # broken. `gross_interference` already calls this out; the finding
            # must not leak past it into a positive contradiction.
            codes.append("INTERFACE_EXPECTATION_CONFLICT")
            notes.append("%s and %s are declared both to meet and to stay clear"
                         % (pb, cb))
            status = _weaken(status, NOT_ESTABLISHED)
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
        drivers = ev.joints_of(group)
        if not drivers:
            codes.append("MOVING_GROUP_HAS_NO_JOINT")
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        if len(drivers) > 1:
            # EVERY joint on the group must be usable, because which one carries
            # the motion is not stated. Checking the first left the others
            # unexamined and let insertion order decide what was inspected.
            codes.append("MOVING_GROUP_DRIVER_AMBIGUOUS")
            notes.append("%s is moved and %s could carry it" % (group, ", ".join(
                sorted(j["entity_id"] for j in drivers))))
            status = _weaken(status, NOT_ESTABLISHED)
        for joint in drivers:
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
    # THE DEMAND IS THE ACTOR'S, and it exists before any candidate answers it.
    # Reading applicability off the FunctionalRegion asked the candidate whether
    # it wished to be examined: declare no access region and the reach question
    # disappeared, which is exactly how a design that ignores an actor came out
    # indistinguishable from one that has no actor.
    demands = ev.reach_demands()
    regions = [r for r in ev.fam("FunctionalRegion")
               if r.get("role") in ("ACCESS", "APERTURE")
               and (r.get("required_by_actors") or r.get("reach_targets"))]
    if not demands and not regions:
        return Verdict("reach", NOT_APPLICABLE, ["NO_REACH_REQUIREMENT"])
    codes, used = [], [a.get("entity_id") for a in demands]
    if demands and not regions:
        codes.append("REACH_REALIZATION_ABSENT")
        why = ("%d actor(s) must reach something and this candidate declares no "
               "access or aperture region that answers it" % len(demands))
    else:
        codes.append("REACH_BASIS_NOT_ESTABLISHED")
        why = ("%d reach requirement(s); no deterministic reach basis exists, so "
               "a ReachResult is recorded as a model-local finding and decides "
               "nothing" % max(len(demands), len(regions)))
    results = ev.fam("ReachResult")
    if results:
        codes.append(MODEL_LOCAL_POSITIVE if all(r.get("reachable") for r in results)
                     else MODEL_LOCAL_NEGATIVE)
    return Verdict("reach", NOT_ESTABLISHED, codes, used, why)


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
    # A CORRIDOR IS ONLY CLEAR OF WHAT CAN BE SEEN. A previously-installed body
    # with no extent used to be skipped in silence, so the fewer bodies an
    # arrangement had placed the more freely every insertion passed - the same
    # partial-geometry-read-as-complete defect the dimensional evaluator had, one
    # domain over. The insertion answer is unestablished while any body is
    # unplaced, whether or not it is one this step must pass.
    unplaced = sorted(b["entity_id"] for b in bodies if b["entity_id"] not in boxes)
    for bid in unplaced:
        code, note, premises = _extent_finding(ev, bid,
                                               "INSERTION_GEOMETRY_INCOMPLETE")
        codes.append(code)
        notes.append(note)
        used += premises
        status = _weaken(status, NOT_ESTABLISHED)
    if unplaced:
        used += [b["entity_id"] for b in bodies]
    # ORDER_INDEX ALONE IS NOT A TOTAL ORDER, and dict order was breaking the
    # tie - so two steps sharing an index were installed in whichever sequence
    # the view happened to hold them, and the corridor each was tested against
    # depended on that. The id breaks the tie deterministically, and a shared
    # index is reported rather than resolved.
    shared = sorted(i for i in {s.get("order_index") for s in steps.values()}
                    if [s for s in steps.values() if s.get("order_index") == i][1:])
    if shared:
        codes.append("ASSEMBLY_ORDER_NOT_TOTAL")
        notes.append("more than one step claims order index %s"
                     % ", ".join(str(i) for i in shared))
        status = _weaken(status, NOT_ESTABLISHED)
        used += sorted(steps)
    ordered = sorted(steps.values(),
                     key=lambda s: (s.get("order_index") or 0, s["entity_id"]))
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

    AN INTERFACE IS NOT A PERMISSION SLIP. Only a kind whose meaning REQUIRES the
    pair to meet exempts that pair: two bodies declared to touch are supposed to
    overlap as boxes, and reporting it would be reporting the design. CLEARANCE
    is the opposite declaration - the design promising these two stay apart - so
    an overlapping CLEARANCE pair is the promise unverified, and exempting it
    because "an interface exists" turned the strongest statement about a pair
    into the weakest. `interface_expectation` is s04's, so the classification has
    one reader.

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
    expectation, conflicted = ev.pair_expectation()
    exempt = {p for p, e in expectation.items() if e == s04.TOUCHES}
    envelope_of = ev.envelope_of()
    codes, notes, used = [], [], []
    status = PASS
    for pair in sorted(conflicted, key=sorted):
        codes.append("INTERFACE_EXPECTATION_CONFLICT")
        notes.append("%s are declared both to meet and to stay clear"
                     % " and ".join(sorted(pair)))
        status = _weaken(status, NOT_ESTABLISHED)
    # EVERY BOX, EVERY INTERFACE AND THE BASIS. "Nothing overlaps that was not
    # declared" is a statement about the whole arrangement: any extent moving,
    # any pair being declared or undeclared, or the basis being withdrawn makes
    # it a different statement.
    used += (ev.ids("Interface", "Body")
             + [e for e in (envelope_of.get(b) for b in boxes) if e] + ev.basis())
    for bid in sorted(b for b in bodies if b not in boxes):
        code, note, premises = _extent_finding(ev, bid,
                                               "INTERFERENCE_GEOMETRY_MISSING")
        codes.append(code)
        notes.append(note)
        used += premises
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
            pair = frozenset((body, other))
            if other == body or pair in exempt:
                continue
            if s04.overlaps(hull, obox):
                codes.append("SWEEP_MEETS_CLEARANCE_PAIR"
                             if expectation.get(pair) == s04.CLEAR
                             else "SWEEP_MEETS_UNDECLARED_BODY")
                notes.append("%s sweeps into %s" % (body, other))
                status = _weaken(status, NOT_ESTABLISHED)
                used.append(envelope_of.get(other))
    names = sorted(boxes)
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            pair = frozenset((names[x], names[y]))
            if pair in exempt or not s04.overlaps(boxes[names[x]], boxes[names[y]]):
                continue
            if expectation.get(pair) == s04.CLEAR:
                codes.append("CLEARANCE_PAIR_OVERLAPS")
                notes.append("%s and %s are declared CLEARANCE and their boxes "
                             "overlap" % (names[x], names[y]))
            else:
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


def _extent_finding(ev: _Evidence, body: str, missing_code: str):
    """(code, note, premises) for ONE body whose extent cannot be measured.

    Reported where the body is actually read, not as a blanket prefix on the
    domain: a body nothing in this domain measures is not a reason this domain
    cannot answer, and staling a load closure because some unrelated body was
    described twice is STALE that fires for no reason.

    An ambiguity names EVERY envelope claiming the body - those are the current
    positive facts that establish it - where a plain absence names none.
    """
    if len(ev.basis()) > 1:
        return ("SCALE_AMBIGUOUS",
                "%d reference scales are current, so no two extents are stated "
                "in one basis" % len(ev.basis()), ev.basis())
    if ev.extent_status(body) == ev.AMBIGUOUS:
        return ("BODY_ENVELOPED_TWICE",
                "%s carries more than one current extent (%s), so no measurement "
                "over it is established" % (body, ", ".join(ev.envelopes_of(body))),
                ev.envelopes_of(body))
    return missing_code, "%s has no extent" % body, []


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
    """The size of the WHOLE candidate, or no answer at all.

    "Overall" is not a property of the bodies that happen to have been placed.
    Measuring the enveloped subset and calling the result SATISFIED answered a
    question about a smaller product than the one being designed - and the more
    incomplete the arrangement, the more comfortably it passed. Every body this
    candidate has must have an extent, or the overall dimension is not yet a
    number.

    The units must meet too. An extent in a RELATIVE basis and a limit in
    millimetres are not comparable, and a conversion invented here would be this
    code choosing the scale the design deliberately left free. The condition is
    the ReferenceScale rule: basis ABSOLUTE and `absolute` stating
    {unit, per_unit}. s04 is told never to invent an absolute size for something
    the input left free, so on a design that states no size this is
    NOT_YET_EVALUABLE - which is what that design knows.
    """
    params = constraint.get("parameters") or {}
    limit, unit = params.get("limit"), params.get("unit")
    if not isinstance(limit, (int, float)):
        return NOT_YET_EVALUABLE, ["CONSTRAINT_LIMIT_MISSING"], [], ""
    # NO DEFAULT AXIS. `params.get("axis", "ANY")` answered a limit that named no
    # direction by measuring the largest span - a different requirement, and a
    # more permissive one on every arrangement whose longest axis is not the one
    # the user meant. An unstated axis is a limit the design has not finished
    # stating.
    axis = params.get("axis")
    if axis not in DIMENSION_AXES:
        # NO FALLBACK. `AXIS_INDEX.get(axis, 0)` answered a requirement about a
        # direction nobody named by silently measuring X.
        return (NOT_YET_EVALUABLE, ["AXIS_NOT_RECOGNIZED"], [],
                "the limit is stated on axis %r; this code knows %s"
                % (axis, ", ".join(DIMENSION_AXES)))
    scales = ev.fam("ReferenceScale")
    if not scales:
        return NOT_YET_EVALUABLE, ["NO_REFERENCE_SCALE"], [], ""
    if len(scales) > 1:
        # Two bases and no rule saying which the extents are in. Picking the
        # first would be choosing an answer.
        return (NOT_YET_EVALUABLE, ["SCALE_AMBIGUOUS"],
                [s.get("entity_id") for s in scales],
                "%d reference scales are current and nothing says which basis "
                "these extents are expressed in" % len(scales))
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
    boxes, bodies = ev.boxes(), ev.ids("Body")
    if not bodies:
        return NOT_YET_EVALUABLE, ["NO_BODY"], [], ""
    twice = sorted(b for b in bodies if ev.extent_status(b) == ev.AMBIGUOUS)
    if twice:
        return (NOT_YET_EVALUABLE, ["BODY_ENVELOPED_TWICE"],
                sorted(bodies) + [e for b in twice for e in ev.envelopes_of(b)],
                "%s carry more than one current extent, so there is no one "
                "arrangement to measure" % ", ".join(twice[:5]))
    unplaced = sorted(b for b in bodies if b not in boxes)
    if unplaced:
        return (NOT_YET_EVALUABLE, ["EXTENT_INCOMPLETE"], sorted(bodies),
                "%d of %d bodies have no extent (%s), so there is no overall "
                "dimension to compare" % (len(unplaced), len(bodies),
                                          ", ".join(unplaced[:5])))
    envelope_of = ev.envelope_of()
    lo = [min(b[0][i] for b in boxes.values()) for i in range(3)]
    hi = [max(b[1][i] for b in boxes.values()) for i in range(3)]
    spans = [(hi[i] - lo[i]) * per_unit for i in range(3)]
    measured = max(spans) if axis == "ANY" else spans[s04.AXIS_INDEX[axis]]
    used = ([scale.get("entity_id")] + sorted(bodies)
            + [envelope_of[b] for b in sorted(boxes)])
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
