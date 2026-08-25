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

    A DOMAIN'S STATUS IS NOT THE CANDIDATE'S ANSWER (Unit A). Every reason code
    a domain emits is CLASSIFIED by the contract - repairable by s04, revisable
    by its upstream owner, owed downstream, unsupported by this pipeline, a
    fact the pre-selection required minimum names and the design lacks, or an
    incompatibility inherent in the architecture - and the candidate-level
    assessment is aggregated from the CLASSES, never from the statuses. A
    domain that reads FAIL because the current realization contradicts itself
    is a repair; a domain that reads NOT_ESTABLISHED because this code cannot
    sweep a composite motion is an obligation. Both stay exactly what they are
    on the domain record. INFEASIBLE needs a structured physical argument, and
    nothing here produces one yet, so it is reachable only by an evaluator that
    can state one. NOT_ESTABLISHED is reserved for the required minimum.

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
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from ..lifecycle.records import (CURRENT_MULTIPLICITY,             # noqa: F401
                                 address_operations,
                                 current_assessment,
                                 current_compliance,
                                 current_domain_assessment,
                                 multiplicity)
from ..state.design_state import Contracts
from ..state.patch import Op, StagePatch
from ..view.consumer_view import InvocationContext, ViewStatus
from . import s03_topology_and_mobility as s03
from . import s04_envelope_and_motion as s04

RESPONSIBILITY = "feasibility"

#: The nine domains, in the order the contract declares them.
#:
#: `transition_reachability` replaced `mobility_disposition`, in place and not
#: beside it. The domain it replaced asked whether the six-DOF grid dispositioned
#: as free every cell some other fact implied had to move, and it derived those
#: cells from a configuration's `distinguishing_basis`, from a joint's
#: `child_group`, and from a rule that the coordinate be free in BOTH endpoints -
#: three inferences the representation does not support. Two states differing is
#: not a demand that either be reachable; which side of a joint is its child is
#: not a statement about what travels; and a mechanism blocked in its stable
#: states and released during the change is an ordinary mechanism, not a
#: contradiction. What is asked now is the narrower question the typed evidence
#: can answer: whether the state change something ACTUALLY DEMANDED is supported
#: by the topology, by the release semantics, and by a realization.
DOMAINS = ("physical_realization", "load_reaction_closure", "transition_reachability",
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

#: THE FINDING CLASSES, in the contract's words. What a reason code MEANS for
#: the candidate before selection. Read back from the contract at load so the
#: two cannot drift; named here so an evaluator can say which it is emitting.
ESTABLISHED = "ESTABLISHED"
REPAIRABLE_S04 = "REPAIRABLE_S04"
OWNER_REVISION = "OWNER_REVISION"
DEFERRED_DOWNSTREAM = "DEFERRED_DOWNSTREAM"
UNSUPPORTED = "UNSUPPORTED"
REQUIRED_MINIMUM_ABSENT = "REQUIRED_MINIMUM_ABSENT"
ARCHITECTURE_INCOMPATIBILITY = "ARCHITECTURE_INCOMPATIBILITY"
#: The classes that are obligations - carried on the record, never decisive.
OBLIGATION_CLASSES = (REPAIRABLE_S04, OWNER_REVISION, DEFERRED_DOWNSTREAM,
                      UNSUPPORTED)

#: The one occupancy this method cannot compute: a moving group two or more of
#: the transition's changed joints touch. Its pose is the COMPOSITION of those
#: motions, and `sweep_hull` rotates one box about one joint. Said as a
#: capability limit, by name, so it is never read as evidence about the group.
OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION = "OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION"

#: What an INFEASIBLE rests on. The same keys the contract's conditional
#: requirement demands of `MechanicalFeasibilityAssessment.physical_argument`;
#: an argument missing any of them is refused before it can decide anything.
ARGUMENT_KEYS = ("contradiction", "premises", "architectural_commitments")

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

    __slots__ = ("domain", "status", "reason_codes", "premises", "summary",
                 "arguments")

    def __init__(self, domain: str, status: str,
                 reason_codes: Optional[Sequence[str]] = None,
                 premises: Optional[Sequence[str]] = None,
                 summary: str = "",
                 arguments: Optional[Sequence[Dict[str, Any]]] = None):
        self.domain = domain
        self.status = status
        self.reason_codes = sorted(set(reason_codes or ()))
        self.premises = sorted({p for p in (premises or ()) if isinstance(p, str) and p})
        self.summary = summary
        #: THE ARGUMENTS BEHIND AN ARCHITECTURE_INCOMPATIBILITY, one record
        #: each: the contradiction, the premises it rests on, the architectural
        #: commitments it follows from. Empty for every other finding, and
        #: empty today for every evaluator above: no domain can yet prove that
        #: a mechanism cannot satisfy a demand under ANY admissible realization
        #: of its commitments, and saying so without the proof is what INV-011
        #: forbids. An evaluator that can prove it states the code and carries
        #: the argument; the aggregation refuses the code without one.
        self.arguments = [dict(a) for a in (arguments or ()) if isinstance(a, dict)]


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
        carries it: propagation walked one hop when this was written, so
        superseding the scale staled the envelope and stopped, leaving a verdict
        standing on an extent that had just lost its authority. S7-F made the
        walk transitive and the direct premise stays, because what a verdict was
        decided from is provenance rather than a mechanism.
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
        # KEYED BY FEATURE, NOT BY PAIR ALONE. Two interfaces on one body pair
        # are two FEATURES when each names what it is - a rotating journal and a
        # snap retainer on one hinge pair are how a real hinge is built, and one
        # runs clear while the other is an interference fit. Collapsing them to
        # the pair read the design as contradicting itself. Feature identity is
        # the interface's own `feature`, the field s03 owns for exactly this;
        # an interface that names none is one feature described as many times
        # as the pair has unnamed rows - and if those disagree, that is the
        # conflict this reader exists to find. It USED TO read `nominal` as a
        # name when that was a string: a status field no producer authors as
        # a name, so no design could ever make two features on a pair distinct.
        features: Dict[Any, Dict[Any, set]] = {}
        for i in self.fam("Interface"):
            bodies_of = (i.get("bodies") or [])[:2]
            if len(bodies_of) < 2:
                continue
            named = i.get("feature")
            feature = named.strip() if isinstance(named, str) and named.strip() else None
            features.setdefault(frozenset(bodies_of), {}).setdefault(
                feature, set()).add(s04.interface_expectation(i))
        expectation, conflicted = {}, set()
        for pair, by_feature in features.items():
            # A feature described two incompatible ways is a conflict.
            if any(len(e) > 1 for e in by_feature.values()):
                conflicted.add(pair)
                continue
            kinds = {sorted(e)[0] for e in by_feature.values()}
            # DISTINCT FEATURES MAY DIFFER. What the pair as a whole is held
            # to: if any feature on it is meant to touch, the pair is declared
            # to meet - a journal that runs clear does not make the bodies
            # strangers when a retainer on the same pair grips. CLEAR only when
            # every feature is clear; UNDECLARED only when every feature is.
            expectation[pair] = (s04.TOUCHES if s04.TOUCHES in kinds
                                 else s04.CLEAR if kinds == {s04.CLEAR}
                                 else sorted(kinds)[0])
        return expectation, conflicted

    def mating_for(self, pair):
        """The interface on this pair that carries mating geometry, if any.

        At most one: two interfaces on one pair each carrying a geometry is two
        narrow-phase statements about one fit, and is reported as such rather
        than resolved by order.
        """
        found = [i for i in self.fam("Interface")
                 if set((i.get("bodies") or [])[:2]) == set(pair)
                 and isinstance(i.get("mating_geometry"), dict)]
        return found

    def fit_settlement(self, interface):
        """(status, code, note, refs) - what the embodiment block has settled
        about this interface's fit, or None where nothing has.

        THE TYPED ANSWER TO QUESTION TWO. S05-C9 makes every declared clearance
        a Constraint that `governs_interface`; s06 extends that Constraint
        with a `settlement` naming the solver status and the margin. Nothing
        is written for a system that did not settle, so a settlement that IS
        here is a FEASIBLE one - the fit realized by solved sizes - and a
        constraint with none is the fit still owed. Read here so an evaluator
        asked after the block has run does not call settled what it can see.
        """
        iid = interface.get("entity_id")
        governing = [c for c in self.fam("Constraint")
                     if c.get("governs_interface") == iid
                     and str(c.get("kind", "")).upper() in ("CLEARANCE",
                                                            "INTERFERENCE_FREE")]
        settled = [c for c in governing if isinstance(c.get("settlement"), dict)]
        if not settled:
            return None
        refs = [c["entity_id"] for c in settled]
        bad = [c for c in settled
               if str(c["settlement"].get("solver_status", "")).lower() != "feasible"
               or (isinstance(c["settlement"].get("margin"), (int, float))
                   and c["settlement"]["margin"] < 0)]
        if bad:
            return (s04.FIT_CONTRADICTED, "REQUIRED_CLEARANCE_NOT_REALIZED",
                    "%s: the constraint governing its fit settled %s"
                    % (iid, ", ".join("%s as %s" % (c["entity_id"],
                                                   c["settlement"].get("solver_status"))
                                      for c in bad)), refs)
        return (s04.FIT_ESTABLISHED, "ANALYTICAL_FIT_ESTABLISHED",
                "%s: the constraint governing its fit is settled" % iid, refs)

    def narrow_phase(self, pair, boxes):
        """(status, code, note, refs) for an overlapping pair, by the one rule.

        Asked only where the broad phase is inconclusive. A pair with no
        geometry is what it always was - unestablished - and a pair with two
        geometries is a question the design has answered twice.

        TWO MATURITIES, ONE READER. The relation is s04's and decides
        selection; the fit is the embodiment block's. Where that block has
        settled the fit, its settlement is the answer; where it has not, the
        fit is DEFERRED - an obligation with an owner, beside an established
        relation - and never decided from representative sizes.
        """
        carrying = self.mating_for(pair)
        if not carrying:
            return (s04.FIT_NOT_ESTABLISHED, None, None, [])
        if len(carrying) > 1:
            return (s04.FIT_NOT_ESTABLISHED, "MATING_GEOMETRY_STATED_TWICE",
                    "%s carry mating geometry for one pair"
                    % ", ".join(sorted(i["entity_id"] for i in carrying)),
                    [i["entity_id"] for i in carrying])
        interface = carrying[0]
        joints = {j["entity_id"]: j for j in self.fam("Joint")}
        status, code, note, refs = s04.mating_fit(
            interface, interface["mating_geometry"], joints, boxes)
        if status != s04.FIT_DEFERRED:
            return status, code, note, refs
        settled = self.fit_settlement(interface)
        if settled is None:
            return status, code, note, refs
        return settled[0], settled[1], settled[2], refs + settled[3]

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


#: HOW MUCH A REALIZATION FINDING COSTS THE REACHABILITY QUESTION.
#:
#: The rules that produce these codes live once, in the pass that writes a
#: realization, so a producer and an evaluator cannot disagree about whether a
#: demand was carried out. What a finding MEANS for eligibility is this table and
#: nothing else, and the split it encodes is between a design that has said
#: something contradictory and one that has not said enough:
#:
#:   FAIL             a positive contradiction. The numbers, or the topology, or
#:                    the realization's own claim, say the demanded change did
#:                    not happen - not that nobody has shown that it did.
#:
#:   NOT_ESTABLISHED  a fact the evidence does not carry. Absence never becomes
#:                    impossibility here: a missing coordinate, a missing
#:                    realization, a joint whose freedoms one scalar cannot tell
#:                    apart, and a claim about what moves that was never made are
#:                    all questions left open.
_REALIZATION_COST = {
    "JOINT_ABSENT": NOT_ESTABLISHED,
    "DOF_NOT_SUPPORTED": FAIL,
    "NO_REALIZATION": NOT_ESTABLISHED,
    "REALIZED_MORE_THAN_ONCE": NOT_ESTABLISHED,
    "ENDPOINT_STATE_ABSENT": NOT_ESTABLISHED,
    "ENDPOINT_MISMATCH": FAIL,
    "ENDPOINT_COORDINATES_ABSENT": NOT_ESTABLISHED,
    "REQUIRED_COORDINATE_ABSENT": NOT_ESTABLISHED,
    "REQUIRED_COORDINATE_NOT_A_NUMBER": NOT_ESTABLISHED,
    "REQUIRED_MOTION_NOT_REALIZED": FAIL,
    "REQUIRED_MOTION_NOT_DECLARED": NOT_ESTABLISHED,
    "MOVING_SIDE_ABSENT": NOT_ESTABLISHED,
    "MOVING_SIDE_UNRELATED": FAIL,
    "REQUIRED_DOF_NOT_RESOLVABLE": NOT_ESTABLISHED,
    "DECLARED_CHANGE_NOT_REALIZED": FAIL,
}

#: The names the domain reports for the two of those the unit vocabulary renames.
#: A code is read by code and by a person, and these two say what happened in the
#: reachability question's own words rather than the producer's.
_REACHABILITY_CODE = {
    "NO_REALIZATION": "REQUIRED_TRANSITION_NOT_REALIZED",
    "REALIZED_MORE_THAN_ONCE": "TRANSITION_REQUIREMENT_REALIZED_MULTIPLE_TIMES",
    "REQUIRED_MOTION_NOT_REALIZED": "REQUIRED_RELATIVE_MOTION_NOT_REALIZED",
}


def _relative_motions(entries) -> Set[Tuple[Any, Any]]:
    """The (joint, dof) pairs a record explicitly states. Nothing derived."""
    return {(e.get("joint"), e.get("dof")) for e in (entries or [])
            if isinstance(e, dict) and e.get("joint") and e.get("dof")}


def _active_at(relation, configuration) -> bool:
    """Whether a restraint holds in one configuration, BY ITS OWN LIST.

    An empty list is a statement that it holds NOWHERE - it is not shorthand for
    everywhere, and reading it as one would make every relation a blocker of
    every transition.
    """
    return configuration in {c for c in (relation.get("configurations") or [])
                             if isinstance(c, str)}


def _release_findings(ev: _Evidence, req, required):
    """(status, code, note, premises) for what the source restraints do to a demand.

    EXPLICIT MATCHES ONLY. A restraint blocks a required relative motion when its
    own `blocked_relative_motions` names the same (joint, dof), and never because
    its `retained_group` happens to be a side of that joint, because its
    `blocked_dofs` happens to contain the letters, or because of what anything is
    called. The unreleased explicit blocker is the ONE fact that makes a demanded
    motion contradicted; everything else about a release declaration is a
    question the evidence leaves open.

    THE DESTINATION IS NOT ASKED. Blocked at the source, released during the
    change, blocked again on arrival is an ordinary mechanism - a latch is one -
    so nothing here requires the demanded freedom to survive into the state the
    transition ends in.
    """
    out = []
    source = req.get("from_configuration")
    released = [r for r in (req.get("released_constraints") or [])
                if isinstance(r, str)]
    # KEYED ON ENTITY ID, which the write boundary makes unique, so naming a
    # relation resolves to that relation or to nothing. Searching the family for
    # the first match would be picking among same-family entities.
    relations = {r.get("entity_id"): r for r in ev.fam("ConstraintRelation")}
    for name, relation in sorted(relations.items()):
        blocking = _relative_motions(relation.get("blocked_relative_motions")) & required
        if not source or not _active_at(relation, source):
            continue
        if not blocking:
            continue
        if name not in released:
            # G. THE CONTRADICTION. The demand says this relative motion has to
            # happen where this restraint says it does not, and nothing claims
            # to defeat the restraint.
            out.append((FAIL, "UNRELEASED_REQUIRED_MOTION",
                        "%s requires %s in %s and %s restrains it there without "
                        "being released"
                        % (req.get("entity_id"),
                           ", ".join("%s/%s" % m for m in sorted(blocking)),
                           source, name),
                        [name]))
            continue
        # H. RELEASED. Being blocked in the stable source state is then legal and
        # costs nothing; what remains open is how the release is achieved.
        if not str(relation.get("defeat_specification") or "").strip():
            out.append((NOT_ESTABLISHED, "RELEASE_EVIDENCE_NOT_ESTABLISHED",
                        "%s releases %s, which states no defeat specification, "
                        "so how the release is achieved is not established"
                        % (req.get("entity_id"), name),
                        [name]))
        else:
            out.append((PASS, None, None, [name]))
    # J. A RELEASE DECLARATION THAT ANSWERS NOTHING. Naming a relation that is
    # not active at the source, or that states no blocked relative motion, or
    # whose blocked motions are disjoint from what is required, leaves the
    # reachability question open - it does not prove the motion impossible, and
    # manufacturing a FAIL from an irrelevant link would be inventing physics
    # from a bookkeeping mistake. s03b's own checker calls out the authored
    # inconsistency; this domain answers only the narrower eligibility question.
    for name in released:
        relation = relations.get(name)
        if relation is None:
            continue
        if not _active_at(relation, source):
            out.append((NOT_ESTABLISHED, "RELEASE_NOT_ACTIVE_AT_SOURCE",
                        "%s releases %s, which holds in %s and not in %s"
                        % (req.get("entity_id"), name,
                           ", ".join(sorted(c for c in
                                            (relation.get("configurations") or [])
                                            if isinstance(c, str)))
                           or "no configuration", source),
                        [name]))
            continue
        restrained = _relative_motions(relation.get("blocked_relative_motions"))
        if not restrained:
            out.append((NOT_ESTABLISHED, "RELEASE_RELATIVE_MOTION_NOT_ESTABLISHED",
                        "%s releases %s, and that relation does not say which "
                        "relative joint motion it restrains"
                        % (req.get("entity_id"), name), [name]))
        elif not (restrained & required):
            out.append((NOT_ESTABLISHED, "RELEASE_RELATION_NOT_APPLICABLE",
                        "%s releases %s, which restrains %s and the transition "
                        "requires %s"
                        % (req.get("entity_id"), name,
                           ", ".join("%s/%s" % m for m in sorted(restrained)),
                           ", ".join("%s/%s" % m for m in sorted(required))),
                        [name]))
    return out


def _realizations_of(ev: _Evidence, req) -> List[Dict[str, Any]]:
    """The written Transitions that claim to realize one demand, AS WRITTEN.

    Endpoint configurations are read from the endpoint States rather than from
    the requirement, because whether the realization runs between the two states
    that were demanded is exactly what the caller has to be able to ask.
    """
    states = {st.get("entity_id"): st for st in ev.fam("State")}
    out = []
    for t in ev.fam("Transition"):
        if t.get("realizes_requirement") != req.get("entity_id"):
            continue
        a = states.get(t.get("from_state")) or {}
        b = states.get(t.get("to_state")) or {}
        out.append({"id": t.get("entity_id"),
                    "from_configuration": a.get("configuration"),
                    "to_configuration": b.get("configuration"),
                    "moving_groups": (t.get("path") or {}).get("moving_groups"),
                    "changed_coordinates": t.get("changed_coordinates"),
                    "_states": [st for st in (a, b) if st]})
    # SORTED BY ID, so which record answers a demand realized more than once is
    # not decided by the order the family happens to come back in. That it was
    # realized more than once is itself the finding; picking deterministically
    # is what makes the finding reproducible rather than a lottery.
    return sorted(out, key=lambda t: str(t["id"]))


def _transition_reachability(ev: _Evidence) -> Verdict:
    """Is the state change this design DEMANDS actually supported?

    THE DEMAND IS A TYPED RECORD. A TransitionRequirement says which two states,
    which joints have to move relative to each other and in which degree of
    freedom, and which restraints the change defeats. Nothing else creates the
    question: two configurations declared to differ are two states that differ,
    and `required_configurations` verifies exactly that - it is not a statement
    that either is reachable from the other, and the domain this replaced read it
    as one.

    Three facts have to hold, and they fail in different ways. The TOPOLOGY has
    to have the freedom (a joint that cannot turn about the axis the demand names
    is a contradiction). A REALIZATION has to exist, connect the demanded pair,
    and move the demanded coordinate (numbers that do not move are a
    contradiction; numbers nobody wrote are a question). And the RESTRAINTS
    active where the change begins have to be released, explicitly, by this
    demand (an active explicit blocker nobody released is a contradiction; a
    release nobody explained is a question).
    """
    requirements = ev.fam("TransitionRequirement")
    demanded = ev.motion_demands()
    if not requirements:
        if demanded:
            # THE DEMAND IS THE APPLICABILITY TEST. An effect obligation that
            # requires movement is a motion question whether or not anything has
            # been authored to answer it, and NOT_APPLICABLE would excuse the
            # candidate for having produced nothing to judge.
            return Verdict("transition_reachability", NOT_ESTABLISHED,
                           ["MOTION_DEMANDED_WITHOUT_TRANSITION_REQUIREMENT"],
                           [p.get("entity_id") for p in demanded],
                           "%d effect obligation(s) require movement and no "
                           "transition requirement states which state change"
                           % len(demanded))
        return Verdict("transition_reachability", NOT_APPLICABLE,
                       ["NO_REQUIRED_MOTION"])

    joints = {j.get("entity_id"): j for j in ev.fam("Joint")}
    codes, notes, used = [], [], []
    status = PASS
    for req in requirements:
        used.append(req.get("entity_id"))
        required = _relative_motions(req.get("required_relative_motions"))
        realizations = _realizations_of(ev, req)
        # EXACTLY THE ENDPOINT STATES THE REALIZATION USED, and not every state
        # that happens to realize the same configuration: what this verdict was
        # computed from is the coordinates the transition's own endpoints hold.
        # Whether a configuration is realized twice is a different question, and
        # `required_configurations` is the domain that asks it.
        # THE COORDINATES OF THE REALIZATION BEING JUDGED, and of no other. When
        # two records claim one demand the shared rules judge the first and
        # report the duplication; merging every claimant's endpoints into one map
        # would check one record's declaration against another record's numbers
        # and could manufacture a contradiction out of the ambiguity.
        coordinates = {}
        for t in realizations:
            states = t.pop("_states")
            used += [st.get("entity_id") for st in states]
            used.append(t["id"])
            if t is not realizations[0]:
                continue
            for st in states:
                coordinates[st.get("configuration")] = st.get("joint_coordinates") or {}
        for code, note in s04.realization_findings(
                req, realizations, coordinates, joints):
            codes.append(_REACHABILITY_CODE.get(code, code))
            notes.append(note)
            status = (FAIL if _REALIZATION_COST[code] == FAIL
                      else _weaken(status, NOT_ESTABLISHED))
        for verdict, code, note, premises in _release_findings(ev, req, required):
            used += premises
            if code is None:
                continue
            codes.append(code)
            notes.append(note)
            status = FAIL if verdict == FAIL else _weaken(status, NOT_ESTABLISHED)
    used += [j for j in joints
             if any(j == m[0] for req in requirements
                    for m in _relative_motions(req.get("required_relative_motions")))]
    if status == PASS:
        codes.append("EVERY_DEMANDED_CHANGE_REACHABLE")
    return Verdict("transition_reachability", status, codes,
                   [u for u in used if u], "; ".join(notes[:5]))


def _required_configurations(ev: _Evidence) -> Verdict:
    """Each configuration is realized, and declared distinctness is real.

    THE FIRST HALF IS THIS DOMAIN'S OWN: a configuration with no state is not
    realized, and one realized twice has two answers to what it is set to.

    THE SECOND HALF IS THE SHARED RULE. Whether the numbers make declared
    distinctness real is `s04.distinctness_findings`, asked here and by the pass
    that writes the coordinates. What a finding COSTS is decided here.
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
    # DECLARED DISTINCTNESS, BY THE SHARED RULE. The formula lived here and the
    # pass that writes the coordinates had none, so a response stating two
    # configurations at one coordinate was accepted by the producer and
    # convicted by the evaluator - one question with two answers, the second
    # arriving too late to be acted on. `s04.distinctness_findings` is the one
    # implementation; what a finding COSTS is decided here and nowhere else.
    #
    # WHAT IT IS NOT. Two states differing is not a statement that either is
    # reachable from the other. That demand is a TransitionRequirement and
    # `transition_reachability` answers it; nothing below is read there, and
    # nothing there is read here.
    coordinates = {cid: (st.get("joint_coordinates") or {})
                   for cid, st in realized.items()}
    findings, consulted = s04.distinctness_findings(
        configs, coordinates, ev.fam("Joint"))
    # EVERYTHING THE COMPARISON READ, whether or not it complained. The driver
    # joint decides which coordinate is compared, so it is a premise of a PASS
    # exactly as it is of a FAIL.
    for ref in consulted:
        used.append(ref)
        if ref in realized:
            used.append(realized[ref].get("entity_id"))
    for code, note, refs in findings:
        codes.append(code)
        notes.append(note)
        # A CONFIGURATION NAMED IS ALSO THE STATE THAT REALIZES IT: the numbers
        # compared came off the state, so withdrawing either costs this verdict
        # its standing.
        for ref in refs:
            used.append(ref)
            if ref in realized:
                used.append(realized[ref].get("entity_id"))
        status = (FAIL if code == "DECLARED_DISTINCTNESS_NOT_REALIZED"
                  else _weaken(status, NOT_ESTABLISHED))
    # The coordinates compared above are spatial values, so the basis they are
    # expressed in is a premise of the comparison exactly as it is of them.
    if used:
        used += ev.basis()
    if status == PASS:
        codes.append("EVERY_CONFIGURATION_REALIZED")
    return Verdict("required_configurations", status, codes, used, "; ".join(notes[:5]))


def _motion_and_transitions(ev: _Evidence) -> Verdict:
    """A transition moves exactly the coordinates it says it moves.

    REALIZATION INTEGRITY, AND NOT STABLE-STATE MOBILITY. Whether the demanded
    change is SUPPORTED - by the topology, by the restraints active where it
    starts, by a realization that carries it out - is
    `transition_reachability`'s question. Whether the records that were written
    are coherent with themselves and with each other is this one's, and the two
    are kept apart so a single defect is not counted twice under two names.

    THE DEMAND IS A TransitionRequirement. It used to be a configuration's
    `distinguishing_basis` as well: two states declared to differ made a
    transition required, which read a statement that they are not the same state
    as a statement that one is reachable from the other. That difference is
    verified where it belongs - `required_configurations` checks that named
    stable states really do differ numerically - and it demands no motion.
    """
    transitions = ev.fam("Transition")
    required = ev.fam("TransitionRequirement")
    demanded = ev.motion_demands()
    if not transitions:
        # A STATE CHANGE IS REQUIRED AND NOTHING DESCRIBES IT. Absent, not
        # inapplicable - that difference is the whole point of the domain, and
        # the demand may come from either direction: a requirement stating the
        # change, or an effect obligation that cannot be discharged without
        # movement.
        if required or demanded:
            return Verdict(
                "motion_and_transitions", NOT_ESTABLISHED,
                ["REQUIRED_TRANSITION_MISSING"],
                [e.get("entity_id") for e in list(required) + demanded],
                "%d motion demand(s) and no transition realizes any of them"
                % len(list(required) + demanded))
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
    joints = ev.fam("Joint")
    # WHICH JOINTS MOVE A MOVING GROUP, asked of the transition that moves it.
    #
    # INCIDENCE IS PARENT OR CHILD. This read `child_group` alone, so a group
    # named on the PARENT side of the only joint it touches had no joint at all,
    # and the same mechanism described the other way round got a different
    # verdict. A joint states a RELATIVE relation; which side travels in the
    # world is not what its parent/child ordering says.
    #
    # AND THE TRANSITION SAYS WHICH ONES CARRY IT. `changed_coordinates` names
    # the joints whose coordinate this path moves, and it is complete: every
    # incident joint among them moves this group. ONE IS NOT THE ONLY RIGHT
    # NUMBER. The middle link of a serial chain G1-[J1]-G2-[J2]-G3 is moved by
    # both joints whenever both turn - that is what a chain is - and asking
    # "which single joint drives it" was a question with no answer, reported as
    # ambiguity about a motion the design had fully attributed. What is asked of
    # each carrying joint is that it be usable: a readable axis and a placed
    # origin. A group none of the changed joints touches is still unestablished
    # - the transition says it moves and says nothing that moves it.
    for t in sorted(ev.fam("Transition"), key=lambda x: str(x.get("entity_id"))):
        changed = {c for c in (t.get("changed_coordinates") or [])
                   if isinstance(c, str)}
        for group in sorted((t.get("path") or {}).get("moving_groups") or []):
            incident = s04.incident_joints(joints, group)
            if not incident:
                codes.append("MOVING_GROUP_HAS_NO_JOINT")
                notes.append("%s is moved by %s and no joint relates it to "
                             "anything" % (group, t.get("entity_id")))
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            drivers = [j for j in incident if j.get("entity_id") in changed]
            if not drivers:
                codes.append("MOVING_GROUP_HAS_NO_JOINT")
                notes.append("%s is moved by %s and none of the coordinates it "
                             "changes is a joint of that group"
                             % (group, t.get("entity_id")))
                status = _weaken(status, NOT_ESTABLISHED)
                continue
            for joint in drivers:
                if s04.axis_index(joint.get("axis_direction")) is None:
                    codes.append("JOINT_AXIS_UNUSABLE")
                    notes.append("%s declares axis %r"
                                 % (joint["entity_id"],
                                    joint.get("axis_direction")))
                    status = _weaken(status, NOT_ESTABLISHED)
                    continue
                origin = joint.get("frame_origin")
                if not (isinstance(origin, list) and len(origin) == 3):
                    codes.append("JOINT_NOT_PLACED")
                    status = _weaken(status, NOT_ESTABLISHED)
                    continue
                used.append(joint["entity_id"])
    # OCCUPANCY IS ACCOUNTED FOR PER REQUIRED (TRANSITION, MOVING GROUP). A
    # transition that moves three groups and carries one SweptVolume used to
    # read as evidenced, so two bodies' motion was never swept and nothing said
    # so - partial geometry read as complete, one domain over from where that
    # defect was already named. Every group a transition says it moves either
    # has a current occupancy or has a finding that says why not, and WHY is
    # read from the same typed facts the producer read: a group two or more of
    # the changed joints touch is a composition this method cannot sweep - a
    # capability limit, named as one - and anything else is a computation the
    # producer did not deliver.
    swept = {(v.get("transition"), v.get("rigid_group"))
             for v in ev.fam("SweptVolume")}
    for t in sorted(ev.fam("Transition"), key=lambda x: str(x.get("entity_id"))):
        changed = {c for c in (t.get("changed_coordinates") or [])
                   if isinstance(c, str)}
        for group in sorted((t.get("path") or {}).get("moving_groups") or []):
            if (t.get("entity_id"), group) in swept:
                continue
            carrying = [j for j in s04.incident_joints(joints, group)
                        if j.get("entity_id") in changed]
            if len(carrying) > 1:
                codes.append(OCCUPANCY_UNSUPPORTED_COMPOSITE_MOTION)
                notes.append("%s is moved by %s through %s at once; this "
                             "method sweeps one box about one joint and cannot "
                             "compose them"
                             % (group, t.get("entity_id"),
                                ", ".join(sorted(j["entity_id"] for j in carrying))))
            else:
                codes.append("OCCUPANCY_NOT_COMPUTED")
                notes.append("%s is moved by %s and no occupancy was computed "
                             "for it" % (group, t.get("entity_id")))
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
    """Whether each actor can reach what it must, ON THE EVIDENCE THIS STAGE HAS.

    THE PRE-SELECTION REACH BASIS. s04a's contract is an arrangement "sufficient
    to decide fit, reach and assemblability", and a ReachResult is that
    decision: the contract calls it "an engineering conclusion of s04a",
    AUTHORITATIVE, authored from the arrangement it produced. This domain used to
    discard it - every reach demand came back NOT_ESTABLISHED because "no
    deterministic reach basis exists" - and nothing anywhere was contracted to
    produce one, so the domain could not PASS on any input. A domain no candidate
    can satisfy is not a standard; it is a refusal to look.

    What establishes reach here, and what does not:

      An actor's demand is answered by an ACCESS or APERTURE region the design
      declares that actor requires, AND a branch-local ReachResult for that
      actor that concludes it is reachable. Both, for every demanding actor.

      A negative conclusion is a positive finding and FAILS: s04a looked at its
      own arrangement and said the actor cannot get there.

      A demand with no region, or a region with no conclusion, or a target the
      conclusion does not name, is NOT_ESTABLISHED - the question is asked and
      nothing answers it.

    THE EVIDENCE LEVEL IS RECORDED, NOT HIDDEN. MODEL_LOCAL_POSITIVE stays on
    the verdict beside the PASS so a reader knows this reach rests on s04a's
    conclusion about boxes and sides, not on a hand envelope swept through a
    solid. That is the contracted evidence level before selection; a later
    stage that computes more says so in its own record.
    """
    demands = ev.reach_demands()
    regions = [r for r in ev.fam("FunctionalRegion")
               if r.get("role") in ("ACCESS", "APERTURE")
               and (r.get("required_by_actors") or r.get("reach_targets"))]
    if not demands and not regions:
        return Verdict("reach", NOT_APPLICABLE, ["NO_REACH_REQUIREMENT"])
    codes, notes, used = [], [], [a.get("entity_id") for a in demands]
    status = PASS
    if demands and not regions:
        return Verdict("reach", NOT_ESTABLISHED, ["REACH_REALIZATION_ABSENT"], used,
                       "%d actor(s) must reach something and this candidate "
                       "declares no access or aperture region that answers it"
                       % len(demands))
    results = ev.fam("ReachResult")
    region_ids = {r.get("entity_id") for r in regions}
    for actor in demands:
        aid = actor.get("entity_id")
        # THE REGION THIS ACTOR IS DECLARED TO NEED. A region nobody required
        # answers nobody; reach for an actor is established through a region
        # the design says is that actor's.
        mine = [r for r in regions if aid in (r.get("required_by_actors") or [])]
        if not mine:
            codes.append("REACH_REGION_NOT_DECLARED_FOR_ACTOR")
            notes.append("%s must reach something and no access or aperture "
                         "region is declared as required by it" % aid)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        used += [r.get("entity_id") for r in mine]
        # THE CONCLUSION ABOUT THIS ACTOR, about a target that is one of its
        # regions or one of the things it must reach. A conclusion about
        # something else is not a conclusion about this demand.
        targets = set(actor.get("must_reach") or []) | {
            r.get("entity_id") for r in mine}
        about = [x for x in results if x.get("actor") == aid
                 and x.get("target") in targets]
        if not about:
            codes.append("REACH_CONCLUSION_ABSENT")
            notes.append("%s has a declared region and s04a recorded no reach "
                         "conclusion about it" % aid)
            status = _weaken(status, NOT_ESTABLISHED)
            continue
        used += [x.get("entity_id") for x in about]
        negative = [x for x in about if not x.get("reachable")]
        if negative:
            # s04a LOOKED AND SAID NO. A negative conclusion about the
            # arrangement it authored is positive evidence, not an absence.
            codes.append("REACH_CONCLUDED_UNREACHABLE")
            notes.append("%s cannot reach %s on s04a's own arrangement"
                         % (aid, ", ".join(sorted(str(x.get("target"))
                                                  for x in negative))))
            status = FAIL
    if results:
        codes.append(MODEL_LOCAL_POSITIVE if all(r.get("reachable") for r in results)
                     else MODEL_LOCAL_NEGATIVE)
    if status == PASS:
        codes.append("EVERY_ACTOR_REACHES_ITS_REGION")
    used += ev.basis() if used else []
    return Verdict("reach", status, codes, used, "; ".join(notes[:5]))


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
    # THE PAIRS THE DESIGN DECLARES TO MEET. An arriving part's conservative
    # corridor passes through the box of the part it is going to sit against,
    # nest inside or snap onto - that is what arriving at a mating position IS -
    # so a pair declared TOUCHES is not an obstruction on the way there. The same
    # reader `gross_interference` uses, so the two domains cannot disagree about
    # which pairs the topology says meet. A pair declared CLEAR, UNDECLARED, or
    # described two ways is exempt from nothing: the corridor through it is
    # exactly what the design has not shown to be clear.
    expectation, _conflicted = ev.pair_expectation()
    meets = {p for p, e in expectation.items() if e == s04.TOUCHES}
    placed: List[str] = []
    for step in ordered:
        sid, body = step["entity_id"], step.get("body")
        used.append(sid)
        if str(step.get("path_kind")) == "DEFORMATION_RESOLVED":
            # A PATH THE PART DEFLECTS THROUGH. Rigid boxes cannot see the
            # deflection, so the corridor test below is the wrong instrument -
            # but that is not the same as the design having said nothing. The
            # QUALITATIVE principle of a snap-fit is stated by the step itself:
            # retention by ELASTICITY, into an activated interface that is an
            # INTERFERENCE_FIT or COMPLIANT_INTERACTION. That is what there is
            # to establish before selection. Whether the flexure survives the
            # deflection - its stress, its force, its limit to produce - is
            # embodiment: s05 declares `limit_to_produce` as its own premise
            # class, and requiring it here would pull sizing in front of the
            # choice of principle.
            #
            # A label with no principle behind it is still unestablished: a
            # step that says DEFORMATION_RESOLVED and names no elastic retention
            # and no fit has described a path nothing holds.
            fits = [i for i in ev.fam("Interface")
                    if i.get("entity_id") in (step.get("activates") or [])
                    and i.get("interaction_kind") in ("INTERFERENCE_FIT",
                                                      "COMPLIANT_INTERACTION")]
            if step.get("termination_strategy") == "ELASTICITY" and fits:
                codes.append("DEFORMATION_RESOLVED_BY_ELASTIC_FIT")
                codes.append("SIZING_DEFERRED_TO_EMBODIMENT")
                notes.append("%s snaps %s into %s; deflection and limit to "
                             "produce are an embodiment obligation"
                             % (sid, body, ", ".join(sorted(
                                 i["entity_id"] for i in fits))))
                used += [i["entity_id"] for i in fits]
            else:
                codes.append("DEFORMATION_RESOLVED_PATH_UNSUPPORTED")
                notes.append("%s declares a deformation-resolved path for %s and "
                             "states no elastic retention into a fit"
                             % (sid, body))
                status = _weaken(status, NOT_ESTABLISHED)
            placed.append(body)
            continue
        direction, code, note = s04.approach_direction(step)
        if direction is None:
            # Missing, unreadable or self-contradicting: nothing this domain
            # can build a corridor from, and the code names which.
            codes.append(code)
            notes.append(note)
            status = _weaken(status, NOT_ESTABLISHED)
            placed.append(body)
            continue
        if body not in boxes:
            codes.append("INSERTION_GEOMETRY_MISSING")
            status = _weaken(status, NOT_ESTABLISHED)
            placed.append(body)
            continue
        hull = s04.insertion_hull(boxes, body, direction)
        # The hull is built from every box in the arrangement - the span comes
        # from the largest of them - so the clearance answer rests on all of
        # them and on the basis they are measured in.
        used += [e for e in (envelope_of.get(b) for b in boxes) if e] + ev.basis()
        for prior in placed:
            if prior not in boxes or not s04.overlaps(hull, boxes[prior]):
                continue
            pair = frozenset((body, prior))
            if pair in meets:
                # Arriving where it is declared to meet this body. The
                # interface that declares it is what the corridor rests on.
                used += [i.get("entity_id") for i in ev.fam("Interface")
                         if set((i.get("bodies") or [])[:2]) == {body, prior}]
                continue
            if expectation.get(pair) == s04.CLEAR:
                # A CLEARANCE PAIR ON THE PATH IS NOT EXEMPT - it is the case
                # the narrow phase exists for. A pin arriving in its bore
                # enters the bore's box along the whole corridor, and whether
                # that is the intended insertion or an obstruction is decided
                # by the mating geometry: the cross-section fits, and the step
                # drives the pin along the mating axis. Without the geometry
                # the corridor is what it always was, unestablished.
                carrying = ev.mating_for(pair)
                if len(carrying) > 1:
                    # TWO GEOMETRIES FOR ONE PAIR is the same ambiguity here as
                    # in `gross_interference`, and it has the same name: the
                    # design answered one question twice, which establishes
                    # nothing and contradicts nothing. It used to fall through
                    # to the generic corridor finding, so one defect had two
                    # meanings depending on which domain read it.
                    codes.append("MATING_GEOMETRY_STATED_TWICE")
                    notes.append("%s carry mating geometry for one pair"
                                 % ", ".join(sorted(i["entity_id"] for i in carrying)))
                    used += [i["entity_id"] for i in carrying]
                    status = _weaken(status, NOT_ESTABLISHED)
                    continue
                if len(carrying) == 1:
                    joints = {j["entity_id"]: j for j in ev.fam("Joint")}
                    fit, code, note, refs = s04.insertion_fit(
                        carrying[0], carrying[0]["mating_geometry"], joints,
                        boxes, direction)
                    used += refs
                    if fit == s04.FIT_DEFERRED:
                        # The same two maturities `gross_interference` reads:
                        # the relation and the approach are s04's and stand;
                        # the fit is settled by the constraint that governs
                        # the interface, where the block has run.
                        settled = ev.fit_settlement(carrying[0])
                        if settled is not None:
                            fit, code, note = settled[0], settled[1], settled[2]
                            used += settled[3]
                        else:
                            codes.append("MATING_RELATION_ESTABLISHED")
                            codes.append(code)
                            continue
                    if fit == s04.FIT_ESTABLISHED:
                        codes.append(code)
                        continue
                    if fit == s04.FIT_CONTRADICTED:
                        codes.append(code)
                        notes.append(note)
                        status = FAIL
                        continue
                    codes.append(code)
                    notes.append(note)
                    status = _weaken(status, NOT_ESTABLISHED)
                    continue
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

    THE BOXES HAVE NO FAIL PATH, and that is a statement about the evidence
    rather than about the mechanisms. An axis-aligned box overlap is not a
    collision: the real bodies are smaller than their boxes, so no-overlap proves
    clearance and overlap proves nothing. Inventing a FAIL from a box to balance
    the vocabulary would manufacture failures the geometry does not support.

    THE NARROW PHASE HAS ONE, AT THE RIGHT MATURITY. Where an intended mating
    interface carries `mating_geometry`, `s04.mating_relation` reads the
    principle - the pair, the feature kinds, the axis, representative sizes
    consistent with the arrangement - and that is what selection rests on.
    The FIT - a CLEARANCE pin strictly smaller than its bore, a press fit no
    smaller than its hole - is read by `s04.mating_fit` from sizes that have
    an authority, and before embodiment none do: s04a is prohibited "any
    authoritative dimension", and its representative numbers can neither
    establish nor contradict the fit. Until the Constraint that governs the
    interface (S05-C9) is settled by s06, the fit is SIZING_DEFERRED_TO_
    EMBODIMENT beside MATING_RELATION_ESTABLISHED - an obligation with an
    owner, costing the domain nothing now, exactly as a snap-fit's limit to
    produce is. A settlement that is here is read; one that says the fit is
    not realized is the one FAIL this domain produces, and it rests on solved
    values, never on a box and never on a representative.

    It USED TO FAIL on the representative numbers themselves: a 4.0 pin in a
    4.0 bore, authored by a pass whose contract calls every dimension
    provisional, eliminated a candidate before anything had sized it.
    """
    boxes = ev.boxes()
    # THE REGIONS NOTHING MAY ENTER. KEEP_OUT by role, and NOT the contract's
    # `excludes_occupancy` policy, which is a different question: that policy
    # says which regions a body may not SIT in at rest - an ACCESS region with
    # a body parked in it is an access the design does not have - and a moving
    # part passing THROUGH an access region is not that. Only KEEP_OUT says "a
    # body entering it is the promise being broken", and a sweep is an entering.
    #
    # A region is a property OF a body - the one whose surface bounds it - and
    # one that names no owner is a claim with no subject: the producer's own
    # check (S03-C12) calls it REGION_WITHOUT_OWNER, and reading its box as an
    # obstacle anyway would let an unattributed volume the model pictured
    # decide a candidate. It is reported below as evidence this domain cannot
    # use, not swept against.
    keepouts, ownerless = [], []
    for r in ev.fam("FunctionalRegion"):
        if r.get("role") != "KEEP_OUT":
            continue
        if not [b for b in (r.get("owning_bodies") or []) if isinstance(b, str)]:
            ownerless.append(r["entity_id"])
            continue
        vol = r.get("volume")
        if isinstance(vol, dict) and isinstance(vol.get("centre"), list) \
                and isinstance(vol.get("half_extent"), list):
            keepouts.append((r["entity_id"], s04.aabb(vol["centre"], vol["half_extent"])))
    moving = {g for t in ev.fam("Transition")
              for g in ((t.get("path") or {}).get("moving_groups") or [])}
    bodies = [b.get("entity_id") for b in ev.fam("Body")]
    # APPLICABILITY IS ASKED OF THE BODIES, NOT OF THE BOXES. Two bodies coexist
    # whether or not anything has placed them, so geometry that is missing makes
    # the question unanswerable rather than absent - reading applicability off
    # the envelopes would have let an unplaced mechanism report that nothing
    # could interfere.
    if len(bodies) < 2 and not moving and not keepouts and not ownerless:
        return Verdict("gross_interference", NOT_APPLICABLE, ["NOTHING_COEXISTS"])
    expectation, conflicted = ev.pair_expectation()
    exempt = {p for p, e in expectation.items() if e == s04.TOUCHES}
    envelope_of = ev.envelope_of()
    codes, notes, used = [], [], []
    status = PASS
    for rid in ownerless:
        codes.append("REGION_WITHOUT_OWNER")
        notes.append("%s excludes occupancy and names no owning body, so it has no "
                     "position relative to any part" % rid)
        used.append(rid)
        status = _weaken(status, NOT_ESTABLISHED)
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
    names = sorted(boxes)
    # THE PAIRS THE NARROW PHASE ESTABLISHED. A sweep that enters one of them
    # is the pin turning in its bore, which is what the geometry says happens.
    analytically_clear = set()
    # A DECLARED MATING THAT CARRIES GEOMETRY IS MEASURED WHATEVER ITS KIND.
    # TOUCHES exempts a pair from the BOX test - two bodies meant to meet are
    # supposed to overlap as boxes - and that exemption stands. It does not
    # exempt the pair from its own numbers: a press fit whose pin is smaller
    # than its hole is a contradiction the design authored, and the exemption
    # used to hide it, because the narrow phase was only ever asked about
    # CLEARANCE. A TOUCHES pair with no geometry is what it always was - exempt,
    # and not suddenly held to a metric requirement nobody stated.
    for pair in sorted(exempt, key=sorted):
        if any(b not in boxes for b in pair):
            continue
        fit, code, note, refs = ev.narrow_phase(pair, boxes)
        if code is None:
            continue
        used += refs
        if fit == s04.FIT_DEFERRED:
            # The relation is established at this maturity and the fit is
            # the embodiment block's to settle: an obligation, recorded by
            # name, that costs the domain nothing now (the same principle as
            # a snap-fit's limit to produce).
            codes.append("MATING_RELATION_ESTABLISHED")
            codes.append(code)
            continue
        codes.append(code)
        if fit == s04.FIT_CONTRADICTED:
            notes.append(note)
            status = FAIL
        elif fit != s04.FIT_ESTABLISHED:
            notes.append(note)
            status = _weaken(status, NOT_ESTABLISHED)
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            pair = frozenset((names[x], names[y]))
            if pair in exempt or not s04.overlaps(boxes[names[x]], boxes[names[y]]):
                continue
            used += [envelope_of.get(names[x]), envelope_of.get(names[y])]
            if expectation.get(pair) == s04.CLEAR:
                # BROAD PHASE INCONCLUSIVE, NARROW PHASE ASKED. Two boxes of a
                # CLEARANCE pair overlap - which for a pin in a bore they
                # always do. The mating geometry, where the design realized
                # one, says whether the pin clears; where it did not, the
                # overlap is what it always was, the promise unverified.
                fit, code, note, refs = ev.narrow_phase(pair, boxes)
                used += refs
                if fit == s04.FIT_ESTABLISHED:
                    codes.append(code)
                    analytically_clear.add(pair)
                    continue
                if fit == s04.FIT_DEFERRED:
                    # The pin IS in its bore by the established relation;
                    # the boxes overlapping is that, and the fit is owed to
                    # embodiment, not to the broad phase.
                    codes.append("MATING_RELATION_ESTABLISHED")
                    codes.append(code)
                    analytically_clear.add(pair)
                    continue
                if fit == s04.FIT_CONTRADICTED:
                    codes.append(code)
                    notes.append(note)
                    status = FAIL
                    continue
                codes.append(code or "CLEARANCE_PAIR_OVERLAPS")
                notes.append(note or "%s and %s are declared CLEARANCE and their "
                                     "boxes overlap" % (names[x], names[y]))
            else:
                codes.append("UNDECLARED_PAIR_OVERLAPS")
                notes.append("%s and %s overlap and no interface declares the pair"
                             % (names[x], names[y]))
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
            if other == body or pair in exempt or pair in analytically_clear:
                continue
            if s04.overlaps(hull, obox):
                codes.append("SWEEP_MEETS_CLEARANCE_PAIR"
                             if expectation.get(pair) == s04.CLEAR
                             else "SWEEP_MEETS_UNDECLARED_BODY")
                notes.append("%s sweeps into %s" % (body, other))
                status = _weaken(status, NOT_ESTABLISHED)
                used.append(envelope_of.get(other))
    if status == PASS:
        codes.append("NO_CONSERVATIVE_OVERLAP")
    return Verdict("gross_interference", status, codes, used, "; ".join(notes[:5]))


#: The one dispatch table. A domain is added by adding an evaluator here and a
#: value to the contract's vocabulary; nothing else enumerates them.
DOMAIN_EVALUATORS: Dict[str, Callable[[_Evidence], Verdict]] = {
    "physical_realization": _physical_realization,
    "load_reaction_closure": _load_reaction_closure,
    "transition_reachability": _transition_reachability,
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


# =====================================================================
# classification - what a finding means for the candidate, and whose it is
# =====================================================================
_CLASSIFICATION: Optional[Dict[str, Any]] = None


def classification() -> Dict[str, Any]:
    """The contract's finding classes, code table and required minimum.

    READ FROM THE CONTRACT, ONCE. `FeasibilityDomainAssessment.
    finding_classification` says what each reason code means for the candidate
    and which pass answers it; `MechanicalFeasibilityAssessment.
    pre_selection_required_minimum` says which facts a candidate must have
    shown to be comparable. Nothing here keeps a second table: a class decided
    in code beside the contract would be two answers to one question, and the
    first time a code was added to one and not the other nobody would know.
    """
    global _CLASSIFICATION
    if _CLASSIFICATION is None:
        fams = Contracts().families
        fda = fams.get("FeasibilityDomainAssessment") or {}
        mfa = fams.get("MechanicalFeasibilityAssessment") or {}
        _CLASSIFICATION = {
            "classes": dict(fda.get("finding_classes") or {}),
            "codes": {k: dict(v) for k, v in
                      (fda.get("finding_classification") or {}).items()},
            "minimum": dict(mfa.get("pre_selection_required_minimum") or {}),
        }
    return _CLASSIFICATION


def _argument_problems(domain: str, argument: Any) -> List[str]:
    """Why an argument is not one. Structural, and fails closed."""
    if not isinstance(argument, dict):
        return ["%s: an architecture incompatibility carries a mapping argument, "
                "not %r" % (domain, type(argument).__name__)]
    out = []
    for key in ARGUMENT_KEYS:
        if key not in argument:
            out.append("%s: the physical argument states no %r" % (domain, key))
    if not (isinstance(argument.get("contradiction"), str)
            and argument["contradiction"].strip()):
        out.append("%s: the physical argument's contradiction is not a statement"
                   % domain)
    for key in ("premises", "architectural_commitments"):
        value = argument.get(key)
        if not (isinstance(value, list) and value
                and all(isinstance(x, str) and x for x in value)):
            out.append("%s: the physical argument's %s must name at least one "
                       "entity" % (domain, key))
    return out


def classify(verdict: Verdict):
    """(obligations, problems) for ONE domain's verdict, from the contract.

    An obligation row is {domain, code, class, owner} plus `negates` where the
    finding leaves a required-minimum fact unestablished. Establishments and
    non-questions produce no row. TOTAL, OR REFUSED: a code the contract does
    not classify is a finding this responsibility cannot explain, and a FAIL
    or NOT_ESTABLISHED domain that explains itself with nothing but
    establishments is a domain that did not say why - both are problems, so
    the evaluator writes no assessment over them rather than an aggregate
    nobody can read back.
    """
    table = classification()
    rows, problems = [], []
    for code in verdict.reason_codes:
        spec = table["codes"].get(code)
        if spec is None:
            problems.append("%s: reason code %s has no classification in the "
                            "contract" % (verdict.domain, code))
            continue
        cls = spec.get("class")
        if cls not in table["classes"]:
            problems.append("%s: reason code %s classifies to %r, which is no "
                            "finding class" % (verdict.domain, code, cls))
            continue
        if cls in (ESTABLISHED, NOT_APPLICABLE):
            continue
        row = {"domain": verdict.domain, "code": code, "class": cls,
               "owner": spec.get("owner")}
        fact = spec.get("negates")
        if fact:
            if fact not in table["minimum"]:
                problems.append("%s: reason code %s negates %r, which is no "
                                "required-minimum fact" % (verdict.domain, code, fact))
                continue
            row["negates"] = fact
        if cls == ARCHITECTURE_INCOMPATIBILITY:
            # THE CLASS NO TABLE MAY GRANT. The code is admissible only beside
            # an argument the verdict itself carries; the row then carries it.
            if not verdict.arguments:
                problems.append("%s: %s is stated with no physical argument; "
                                "INFEASIBLE is reserved for an impossibility "
                                "supported by one (INV-011)"
                                % (verdict.domain, code))
                continue
            for argument in verdict.arguments:
                problems += _argument_problems(verdict.domain, argument)
            row["arguments"] = [dict(a) for a in verdict.arguments]
        rows.append(row)
    if verdict.status in (FAIL, NOT_ESTABLISHED) and not rows and not problems:
        problems.append("%s is %s and every reason code it carries is an "
                        "establishment; the domain has not said why"
                        % (verdict.domain, verdict.status))
    if verdict.arguments and not any(r["class"] == ARCHITECTURE_INCOMPATIBILITY
                                     for r in rows) and not problems:
        problems.append("%s carries a physical argument and states no "
                        "architecture incompatibility" % verdict.domain)
    return rows, problems


class Aggregation:
    """The candidate-level answer, and exactly what decided it."""

    __slots__ = ("status", "blocking", "obligations", "physical_argument",
                 "problems")

    def __init__(self, status, blocking, obligations, physical_argument, problems):
        self.status = status
        self.blocking = list(blocking)
        self.obligations = list(obligations)
        self.physical_argument = physical_argument
        self.problems = list(problems)


def aggregate(verdicts: Sequence[Verdict]) -> Aggregation:
    """The whole of the candidate-level rule, from the CLASSES of the findings.

    INFEASIBLE iff some domain states an ARCHITECTURE_INCOMPATIBILITY and
    carries the argument for it - the one thing the contract will not let a
    table grant. Else NOT_ESTABLISHED iff some finding negates a fact of the
    pre-selection required minimum: the design has not shown what a candidate
    must show to be compared, whether the fact is absent, ambiguous, or
    contradicted by a realization its owner can still repair. Else
    FEASIBLE_FOR_SELECTION, with every remaining finding - repairable,
    owner-revisable, deferred, unsupported - carried as an open obligation.

    NO DOMAIN STATUS IS READ. A FAIL whose contradiction its owner may revise
    without changing the principle is a repair; a NOT_ESTABLISHED outside the
    minimum is an obligation; a NOT_APPLICABLE is nothing. Nothing about
    complexity enters, because nothing about complexity is an input.
    """
    blocking, obligations, arguments, problems = [], [], [], []
    for v in verdicts:
        rows, rows_problems = classify(v)
        problems += rows_problems
        for row in rows:
            if row["class"] == ARCHITECTURE_INCOMPATIBILITY:
                arguments.append(row)
            elif row.get("negates"):
                blocking.append(row)
            else:
                obligations.append(row)
    if problems:
        return Aggregation(None, blocking, obligations, None, problems)
    if arguments:
        first = arguments[0]
        argument = dict(first["arguments"][0])
        argument.setdefault("domain", first["domain"])
        return Aggregation(INFEASIBLE, blocking + arguments, obligations,
                           argument, [])
    if blocking:
        return Aggregation(MFA_NOT_ESTABLISHED, blocking, obligations, None, [])
    return Aggregation(FEASIBLE, [], obligations, None, [])


# =====================================================================
# hard requirements
# =====================================================================
SATISFIED, VIOLATED, NOT_YET_EVALUABLE = "SATISFIED", "VIOLATED", "NOT_YET_EVALUABLE"

#: WHEN a hard requirement can be answered, in the contract's words (Unit D).
#: PRE_SELECTION: the evidence exists before mechanism selection, so an
#: unanswered record is required evidence absent. DOWNSTREAM: only a later
#: responsibility produces it, so an unanswered record is honest, and owed.
PRE_SELECTION, DOWNSTREAM = "PRE_SELECTION", "DOWNSTREAM"

_EVALUATION_POLICY: Optional[Dict[str, Dict[str, Any]]] = None


def evaluation_policy() -> Dict[str, Dict[str, Any]]:
    """kind -> {point, evidence_owner}, READ FROM THE CONTRACT, ONCE.

    `DesignConstraint.kinds.<kind>.evaluation` is the one table that says when
    a hard requirement of that kind can be answered and who owes the evidence
    while it cannot. Nothing keeps a second copy: selection, the decision
    screen and the assurance check read the stamp this responsibility puts on
    each compliance record, never a table of their own - the same discipline
    `classification` keeps for the finding codes.
    """
    global _EVALUATION_POLICY
    if _EVALUATION_POLICY is None:
        kinds = (Contracts().families.get("DesignConstraint") or {}).get("kinds") or {}
        _EVALUATION_POLICY = {
            kind: dict(spec.get("evaluation") or {})
            for kind, spec in kinds.items() if isinstance(spec, dict)}
    return _EVALUATION_POLICY


def evaluation_timing(kind: Any) -> Dict[str, Any]:
    """{point, evidence_owner} for one kind. FAILS CLOSED.

    A kind the table does not know, one that declares no point, and a
    DOWNSTREAM point that names no owner are all PRE_SELECTION: a policy
    nobody declared widens nothing, and a deferral to nobody is not a
    deferral anyone can discharge. Read by the evaluator when it writes the
    record, and by nothing that reads the record.
    """
    spec = evaluation_policy().get(kind) or {}
    owner = spec.get("evidence_owner")
    owner = owner if isinstance(owner, str) and owner else None
    if spec.get("point") == DOWNSTREAM and owner:
        return {"point": DOWNSTREAM, "evidence_owner": owner}
    return {"point": PRE_SELECTION, "evidence_owner": owner}


def compliance_deferred(record: Dict[str, Any]) -> bool:
    """A record honestly unanswered at a DOWNSTREAM point, naming who owes it.

    Explicit on every count - the status, the stamped point, a non-empty
    owner - or it is not deferred. Nothing is inferred from the `why`.
    """
    owner = record.get("evidence_owner")
    return (record.get("status") == NOT_YET_EVALUABLE
            and record.get("evaluation_point") == DOWNSTREAM
            and isinstance(owner, str) and bool(owner))


def compliance_blocks(record: Dict[str, Any]) -> Optional[str]:
    """Why ONE compliance record stops a candidate being chosen, or None.

    THE ONE READING OF A STAMPED RECORD, and the only one: selection reads
    eligibility through it, the assurance check re-derives a commitment's
    preconditions through it, and no consumer keeps a rule of its own. Typed
    fields only - the status and the stamped point - never the reason, the
    `why`, or whose candidate it is.

        SATISFIED                        -> does not block
        VIOLATED                         -> blocks, at any point; a deferral
                                            never hides an established violation
        NOT_YET_EVALUABLE, DOWNSTREAM    -> does not block: deferred debt, owed
        NOT_YET_EVALUABLE, otherwise     -> blocks: required evidence absent
        anything else, or no stamp       -> blocks, closed
    """
    constraint = record.get("constraint")
    status = record.get("status")
    if status == SATISFIED:
        return None
    if status == VIOLATED:
        return "%s is violated" % constraint
    if compliance_deferred(record):
        return None
    if status == NOT_YET_EVALUABLE:
        owner = record.get("evidence_owner")
        return ("%s is NOT_YET_EVALUABLE and its evidence is required before "
                "selection%s" % (constraint, " (owed by %s)" % owner if owner else ""))
    return "%s is %r, which is no compliance status" % (constraint, status)


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
    agg = aggregate(verdicts)
    if agg.problems:
        # A FINDING THIS RESPONSIBILITY CANNOT CLASSIFY, or an infeasibility
        # stated without its argument. No assessment is written over either:
        # an aggregate nobody can read back is worse than none.
        return FeasibilityOutcome(candidate_id, None, verdicts, compliance, None,
                                  ["%s: %s" % (RESPONSIBILITY, p)
                                   for p in agg.problems], view.as_dict())
    status = agg.status

    conflicting = multiplicity(state, candidate_id)
    if conflicting:
        # A CANDIDATE WITH TWO CURRENT ANSWERS is a lifecycle defect, and
        # evaluating again over an address nobody can read would bury it.
        return FeasibilityOutcome(candidate_id, CURRENT_MULTIPLICITY, verdicts,
                                  compliance, None, conflicting, view.as_dict())

    prov = "feasibility:deterministic"
    ops: List[Op] = []
    domain_ids, raw_union = [], set()
    for v in verdicts:
        rows, _problems = classify(v)
        made, eid = address_operations(
            state, "FeasibilityDomainAssessment",
            "FDA-%s-%s" % (candidate_id, _TOKEN[v.domain]),
            {"candidate": candidate_id, "domain": v.domain, "status": v.status,
             "reason_codes": v.reason_codes, "summary": v.summary,
             # THE STRUCTURED READING OF THE CODES: what each means for the
             # candidate and whose it is. The status above is untouched.
             "obligations": [{k: r[k] for k in r if k != "domain"} for r in rows]},
            sorted({candidate_id} | set(v.premises)), prov,
            current_domain_assessment(state, candidate_id, v.domain))
        ops += made
        domain_ids.append(eid)
        raw_union |= set(v.premises)
    # THE RAW UNION IS CARRIED AS WELL AS THE DOMAIN RECORDS. S7-F made
    # propagation transitive, so naming the domain records is enough on its own
    # now; the raw premises stay because they are true, they cost nothing, and
    # deleting correct provenance to demonstrate a mechanism is not a test of it.
    fields = {"candidate": candidate_id, "status": status,
              "domain_assessments": domain_ids, "evaluated_domains": list(DOMAINS),
              "findings": [_finding(v) for v in verdicts
                           if v.status in (FAIL, NOT_ESTABLISHED)],
              # WHY IT IS NOT FEASIBLE_FOR_SELECTION, structured: the
              # required-minimum facts the design has not shown. Empty on a
              # FEASIBLE answer.
              "blocking_findings": [dict(r) for r in agg.blocking],
              # WHAT THE CANDIDATE CARRIES INTO SELECTION, structured: every
              # finding outside the minimum, with its class and its owner. A
              # FEASIBLE answer with rows here is a candidate that may be
              # chosen with its debts on the record, not one with none.
              "open_obligations": [dict(r) for r in agg.obligations]}
    if agg.physical_argument is not None:
        fields["physical_argument"] = dict(agg.physical_argument)
    made, _mfa = address_operations(
        state, "MechanicalFeasibilityAssessment", "MFA-%s" % candidate_id,
        fields,
        sorted({candidate_id} | set(domain_ids) | raw_union), prov,
        current_assessment(state, candidate_id),
        basis_over=sorted({candidate_id} | raw_union))
    ops += made
    for constraint, hstatus, codes, used, why in compliance:
        cid = constraint.get("entity_id")
        # WHEN THIS CAN BE ANSWERED, AND BY WHOM - stamped from the one table
        # (Unit D), so every reader downstream reads the record and none reads
        # the table. The status above is what the evidence established; the
        # stamp is what the design declared about the kind. A policy revised
        # in the contract reaches the record on the next reconcile, as a
        # revision of it, and everything premised on it goes stale.
        timing = evaluation_timing(constraint.get("kind"))
        fields = {"candidate": candidate_id, "constraint": cid, "status": hstatus,
                  "why": why or "; ".join(codes),
                  "evaluation_point": timing["point"]}
        if timing["evidence_owner"]:
            fields["evidence_owner"] = timing["evidence_owner"]
        made, _hrc = address_operations(
            state, "HardRequirementCompliance",
            "HRC-%s-%s" % (candidate_id, cid), fields,
            sorted({candidate_id, cid} | {u for u in used if u}), prov,
            current_compliance(state, candidate_id, cid))
        ops += made
    if not ops:
        # NOTHING TO SAY THAT IS NOT ALREADY SAID. Reconciling a design nobody
        # changed writes nothing at all, or every reconcile would be a revision
        # and the history would fill with copies of one answer.
        return FeasibilityOutcome(candidate_id, status, verdicts, compliance,
                                  None, [], view.as_dict())

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
