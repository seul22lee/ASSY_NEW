"""THE CAPABILITIES, EACH READING COMMITTED STATE AND NOTHING ELSE.

S-8 / U-9, §14. Every function here takes an accumulated DesignState and returns
findings. None of them writes, none of them imports a provider, and none of them
is reachable from a producing stage - the direction is producer, then committed
state, then this.

WHAT MOVED AND WHAT DID NOT

Six of these were living inside the module of the stage they judge. They are the
same computations - the plan is explicit that several current checks are good and
are preserved in substance - and what changed is where they run and what they may
claim. Two things did NOT move: DOF totality, which is BOOKKEEPING and counts
toward nothing, and the retired sampling declaration, which was never a
capability.

Geometry helpers are imported from the s04 module. That is a SHARED PURE
COMPUTATION, not a dependency of a producer on assurance: box arithmetic has no
opinion about whether a design is good, and reimplementing it here would create a
second answer to "do these boxes touch" for no gain.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..stages import s03_topology_and_mobility as _s03
from ..stages import s04_envelope_and_motion as _s04
from .model import (FAIL, FALSE_ACCEPTANCE, Finding, NOT_EVALUABLE,
                    NOT_VERIFIED, PASS, PROJECTION_FAILURE,
                    UPSTREAM_INSUFFICIENCY)


def _pass(property_id: str, detail: str, refs: Iterable[str] = ()) -> Finding:
    return Finding(property_id, PASS, detail, tuple(sorted(set(refs))))


def _fail(property_id: str, detail: str, refs: Iterable[str] = (),
          code: Optional[str] = None) -> Finding:
    return Finding(property_id, FAIL, detail, tuple(sorted(set(refs))), code)


def _unknown(property_id: str, detail: str, refs: Iterable[str] = (),
             outcome: str = NOT_VERIFIED) -> Finding:
    return Finding(property_id, outcome, detail, tuple(sorted(set(refs))))


# =====================================================================
# STRUCTURAL - the pipeline carried what it was supposed to carry
# =====================================================================
def consumer_sufficiency(state) -> List[Finding]:
    """Every declared consumer's required minimum, rebuilt from the contracts.

    BOOKKEEPING, and the reason is worth stating: a view carrying its derived
    minimum says the pipeline moved the right material, and says nothing about
    whether the material is right. What must never be merged is the taxonomy -
    upstream never established it (UPSTREAM_INSUFFICIENCY) against we failed to
    carry what exists (PROJECTION_FAILURE) - because those two blame different
    parties and only one of them is a defect in this repository.
    """
    from ..view import consumer_view_for, responsibility_contract

    out: List[Finding] = []
    for responsibility in sorted(responsibility_contract().get("stages") or {}):
        prop = "consumer_sufficiency:%s" % responsibility
        try:
            view = consumer_view_for(responsibility, state)
        except Exception as exc:                                    # noqa: BLE001
            out.append(_unknown(prop, "the view could not be built: %s" % exc,
                                outcome=NOT_EVALUABLE))
            continue
        unmet = [a for a in view.assessment if a["verdict"] != "SATISFIED"]
        projection = [a["requirement"] for a in unmet
                      if a["verdict"] == "PROJECTION_FAILURE"]
        upstream = [a["requirement"] for a in unmet
                    if a["verdict"] == "MISSING_UPSTREAM"]
        if projection:
            out.append(_fail(prop, "%s: applicable material exists and did not "
                                   "reach the view: %s"
                             % (PROJECTION_FAILURE, ", ".join(sorted(projection))),
                             code=PROJECTION_FAILURE))
        elif upstream:
            out.append(_unknown(prop, "%s: %s was never established upstream"
                                % (UPSTREAM_INSUFFICIENCY,
                                   ", ".join(sorted(upstream)))))
        else:
            out.append(_pass(prop, "the derived minimum reached the view"))
    return out


def reference_integrity(state) -> List[Finding]:
    """Every typed reference on a standing entity resolves to an entity.

    PROVENANCE_INTEGRITY: a reference that resolves is a claim that can be
    followed, which is not the same as a claim that is true. Moderate
    independence at best - the write boundary refuses unresolvable references
    with the same rule - so this is a standing audit rather than a discovery.
    """
    out: List[Finding] = []
    for eid in sorted(state.entities):
        record = state.entities[eid]
        if record.get("_validity") != "STANDING":
            continue
        family = record.get("_family")
        dangling = []
        for field, spec in (state.c.field_semantics(family) or {}).items():
            if spec.get("kind") != "reference":
                continue
            value = record.get(field)
            for ref in (value if isinstance(value, list) else [value]):
                if isinstance(ref, str) and ref and not state.has_entity(ref):
                    dangling.append("%s.%s -> %s" % (eid, field, ref))
        prop = "reference_integrity:%s" % eid
        if dangling:
            out.append(_fail(prop, "; ".join(sorted(dangling)), [eid]))
        else:
            out.append(_pass(prop, "every typed reference resolves", [eid]))
    return out


def quantitative_continuity(state) -> List[Finding]:
    """A magnitude carried out of a requirement keeps that requirement's hedge.

    FIDELITY, and never more. A value that survived transport unchanged is a
    value that was not sharpened; whether the number is right is a question no
    transport check can answer. Moved out of s02, where the stage that carried
    the number was also the one certifying it had not changed it.
    """
    hedged: List[str] = []
    for requirement in state.family("Requirement"):
        text = str(requirement.get("statement_verbatim", "")).lower()
        for qualifier in _s03.QUALIFIER_WORDS if hasattr(_s03, "QUALIFIER_WORDS") \
                else QUALIFIER_WORDS:
            if re.search(r"\b%s\b" % re.escape(qualifier), text):
                hedged.append(text)
                break
    out: List[Finding] = []
    for load in state.family("LoadCase"):
        prop = "quantitative_continuity:%s" % load["entity_id"]
        magnitude = str(load.get("magnitude_or_status", ""))
        if not magnitude or magnitude == "UNSUPPORTED":
            out.append(_unknown(prop, "no magnitude is stated, so none was "
                                      "carried", [load["entity_id"]]))
            continue
        low = magnitude.lower()
        if any(re.search(r"\b%s\b" % re.escape(q), low) for q in QUALIFIER_WORDS):
            out.append(_pass(prop, "the qualifier survived", [load["entity_id"]]))
            continue
        sharpened = [n for n in re.findall(r"\d+(?:\.\d+)?", magnitude)
                     if any(n in h for h in hedged)]
        if sharpened:
            out.append(_fail(prop, "MAGNITUDE_SHARPENED: %r drops the qualifier "
                                   "the requirement carried with %s"
                             % (magnitude, ", ".join(sharpened)),
                             [load["entity_id"]]))
        else:
            out.append(_pass(prop, "no hedged quantity was sharpened",
                             [load["entity_id"]]))
    return out


#: The qualifier vocabulary the s02 check used. Kept here because the check that
#: uses it lives here now; s01's own sharpening check keeps its own copy, which
#: is a producer validation of the source it alone may read.
QUALIFIER_WORDS = ("about", "approximately", "approx", "around", "roughly",
                   "circa", "nearly", "almost", "up to", "at least", "at most",
                   "or so", "some", "several", "typical", "typically", "order of")


# =====================================================================
# PROVENANCE INTEGRITY - the claim traces to something
# =====================================================================
def mobility_disposition_completeness(state) -> List[Finding]:
    """Every disposition traces to a resolvable premise.

    PROVENANCE_INTEGRITY, and §14 is explicit that it MAY NOT CONTRIBUTE TO
    ESTABLISHMENT: a BLOCKED_BY cell citing a relation that exists is a
    well-formed claim about blocking, not a demonstration that the DOF is
    blocked. Moved out of s03 - the stage that derived the grid was also the one
    certifying the grid cited real relations.
    """
    bodies = {b["entity_id"] for b in state.standing("Body")}
    relations = {r["entity_id"] for r in state.standing("ConstraintRelation")}
    out: List[Finding] = []
    for cell in _s03.current_mobility_cells(state):
        tag = "%s/%s/%s" % (cell.get("rigid_group"), cell.get("configuration"),
                            cell.get("dof"))
        prop = "mobility_disposition_completeness:%s" % tag
        disposition = cell.get("disposition")
        if disposition == "BLOCKED_BY":
            cited = cell.get("constraint_relation")
            if not cited or cited not in relations:
                out.append(_fail(prop, "BLOCKED_BY_UNRESOLVED_PREMISE: cites %r"
                                 % cited))
                continue
            missing = [f for f in ("blocked_direction", "defeat_specification",
                                   "driver") if not str(cell.get(f) or "").strip()]
            if not (cell.get("provider_body") or cell.get("provider_reaction_site")):
                missing.append("a provider")
            provider = cell.get("provider_body")
            if missing:
                out.append(_fail(prop, "BLOCKING_INCOMPLETE: missing %s"
                                 % ", ".join(missing), [cited]))
            elif cell.get("driver") not in _s03.CONSTRAINT_DRIVERS:
                out.append(_fail(prop, "BLOCKING_BAD_DRIVER: %r"
                                 % cell.get("driver"), [cited]))
            elif provider and bodies and provider not in bodies:
                out.append(_fail(prop, "PROVIDER_NOT_A_BODY: %r" % provider,
                                 [cited]))
            else:
                out.append(_pass(prop, "the blocking claim cites a complete "
                                       "relation", [cited]))
        elif disposition == "IRRELEVANT_BECAUSE":
            scenario = cell.get("scenario")
            if not str(scenario or "").strip():
                out.append(_fail(prop, "IRRELEVANCE_UNJUSTIFIED: names no scenario"))
            else:
                out.append(_pass(prop, "the irrelevance names a scenario",
                                 [scenario]))
    return out


# =====================================================================
# PREMISE - two producers, and whether they agree
# =====================================================================
def physical_relation_closure(state) -> List[Finding]:
    """Every required physical effect is discharged, or explicitly open.

    S02 authored the demand and S03·B authored the interaction that answers it,
    so neither could have made the other agree - which is what makes an
    undischarged obligation an ENGINEERING CONSEQUENCE rather than a
    bookkeeping gap. A mechanism that does not produce an effect its own design
    says it must produce does not work.

    Design-wide and per obligation, deliberately. The feasibility responsibility
    asks a different question - can THIS CANDIDATE work - and answers it per
    branch with an authoritative verdict; this asks whether the design has
    answered its own demand at all, and answers it with a property.
    """
    interactions = state.standing("PhysicalInteraction")
    out: List[Finding] = []
    for obligation in sorted(state.standing("PhysicalEffectObligation"),
                             key=lambda o: o["entity_id"]):
        oid = obligation["entity_id"]
        prop = "physical_relation_closure:%s" % oid
        discharging = [i for i in interactions
                       if oid in (i.get("discharges_effect") or [])
                       or i.get("discharges_effect") == oid]
        if discharging:
            effects = {str(i.get("effect")) for i in discharging}
            if str(obligation.get("effect")) not in effects:
                out.append(_fail(
                    prop, "EFFECT_MISMATCH: the obligation requires %r and the "
                          "interactions discharging it produce %s"
                    % (obligation.get("effect"), sorted(effects)),
                    [oid] + [i["entity_id"] for i in discharging]))
            else:
                out.append(_pass(prop, "discharged by %s"
                                 % ", ".join(sorted(i["entity_id"]
                                                    for i in discharging)),
                                 [oid] + [i["entity_id"] for i in discharging]))
            continue
        open_items = [u for u in state.standing("UnresolvedDecision")
                      if oid in (u.get("blocks") or [])]
        if open_items:
            out.append(_unknown(prop, "undischarged and recorded as open by %s"
                                % ", ".join(sorted(u["entity_id"]
                                                   for u in open_items)),
                                [oid] + [u["entity_id"] for u in open_items]))
        else:
            out.append(_fail(prop, "EFFECT_UNDISCHARGED_AND_UNRECORDED: the "
                                   "design requires %r and nothing produces it"
                             % obligation.get("effect"), [oid]))
    return out


def mobility_cross_premise_consistency(state) -> List[Finding]:
    """No degree of freedom is IRRELEVANT under a load that acts on it.

    S02 wrote the load cases before any disposition existed and S03 wrote the
    dispositions without being able to change the loads. A DOF called irrelevant
    in a scenario that carries a load case is a physical contradiction between
    two authors - the definition of an ENGINEERING CONSEQUENCE, and the property
    Rule A establishes for S03.
    """
    scenarios = {s["entity_id"] for s in state.standing("Scenario")}
    loaded = {}
    for load in state.standing("LoadCase"):
        loaded.setdefault(load.get("scenario"), []).append(load["entity_id"])
    out: List[Finding] = []
    for cell in _s03.current_mobility_cells(state):
        if cell.get("disposition") != "IRRELEVANT_BECAUSE":
            continue
        tag = "%s/%s/%s" % (cell.get("rigid_group"), cell.get("configuration"),
                            cell.get("dof"))
        prop = "mobility_cross_premise_consistency:%s" % tag
        scenario = cell.get("scenario")
        if not str(scenario or "").strip():
            out.append(_unknown(prop, "the disposition names no scenario, so "
                                      "there is nothing to compare it against"))
        elif scenarios and scenario not in scenarios:
            out.append(_unknown(prop, "the disposition names %s, which the "
                                      "design does not hold" % scenario))
        elif scenario in loaded:
            out.append(_fail(prop, "IRRELEVANCE_CONTRADICTED: %s carries %s"
                             % (scenario, ", ".join(sorted(loaded[scenario]))),
                             [scenario] + loaded[scenario]))
        else:
            out.append(_pass(prop, "%s carries no load case" % scenario,
                             [scenario]))
    return out


def topology_to_spatial_fidelity(state) -> List[Finding]:
    """Bodies the topology connects are placed where they meet.

    S03 declared the incidence and S04 placed the boxes; the placer authored
    neither the joint nor the interface. Bounded on purpose: this establishes
    FIDELITY TO THE DECLARED TOPOLOGY and nothing about whether that topology
    was the right one. A wrong topology faithfully realized still passes, and
    saying so is what keeps the claim honest.
    """
    boxes = _s04._boxes(state)
    mech = {f: [_s04._thaw(e) for e in state.family(f)]
            for f in ("RigidGroup", "Joint", "Interface")}
    # THE EXTENTS ARE PART OF WHAT THIS READ, so they are part of what it names.
    # A result whose premises listed only the bodies would stay "current" after
    # the placement it measured was revised, which is the currentness question
    # answered wrongly.
    envelopes: Dict[str, List[str]] = {}
    for envelope in state.standing("Envelope"):
        envelopes.setdefault(envelope.get("body"), []).append(envelope["entity_id"])
    out: List[Finding] = []
    for parent, child in sorted(_s04.required_contacts(mech)):
        prop = "topology_to_spatial_fidelity:%s|%s" % (parent, child)
        refs = [parent, child] + envelopes.get(parent, []) + envelopes.get(child, [])
        a, b = boxes.get(parent), boxes.get(child)
        if not (a and b):
            out.append(_unknown(prop, "one of the bodies has no extent, so the "
                                      "incidence cannot be measured", refs))
            continue
        gap = _s04.box_gap(a, b)
        if gap > 0:
            out.append(_fail(prop, "JOINED_BODIES_DO_NOT_MEET: placed %.3g apart"
                             % gap, refs))
        else:
            out.append(_pass(prop, "the declared incidence is realized", refs))
    return out


def required_distinctness_non_degeneracy(state) -> List[Finding]:
    """Declared distinctness survives realization.

    CONDITIONAL ON A DECLARED PREMISE, never "all joint pairs must differ".
    S03 says which configurations must differ and on what basis; S04 authors the
    coordinates. A blanket non-degeneracy rule would invent a requirement the
    design never stated, which is the same defect as ignoring one it did.
    """
    by_config = {}
    for st in state.standing("State"):
        by_config[st.get("configuration") or st.get("name")] = st
    out: List[Finding] = []
    for cfg in sorted(state.standing("Configuration"), key=lambda c: c["entity_id"]):
        basis = cfg.get("distinguishing_basis")
        if not isinstance(basis, list) or not basis:
            continue
        mine = by_config.get(cfg["entity_id"])
        for item in basis:
            if not isinstance(item, dict):
                continue
            group, dof = item.get("rigid_group"), item.get("dof")
            prop = "required_distinctness:%s|%s|%s" % (cfg["entity_id"], group, dof)
            if mine is None:
                out.append(_unknown(prop, "the configuration has no realized "
                                          "state", [cfg["entity_id"]]))
                continue
            others = [o for o in (item.get("differs_from") or []) if o in by_config] \
                or [k for k in by_config if k != cfg["entity_id"]]
            drive = _s04._driving_joint(state, group)
            if drive is None:
                out.append(_unknown(prop, "no joint drives %s, so the declared "
                                          "distinction cannot be measured"
                                    % group, [cfg["entity_id"]]))
                continue
            jid = drive["entity_id"]
            mine_q = (mine.get("joint_coordinates") or {}).get(jid)
            degenerate, unknown = [], []
            for other in others:
                theirs = (by_config[other].get("joint_coordinates") or {}).get(jid)
                if mine_q is None or theirs is None:
                    unknown.append(other)
                elif mine_q == theirs:
                    degenerate.append(other)
            if degenerate:
                out.append(_fail(prop, "DECLARED_DISTINCTNESS_NOT_REALIZED: %s "
                                       "realize %s at %r as well"
                                 % (", ".join(sorted(degenerate)), jid, mine_q),
                                 [cfg["entity_id"], jid] + degenerate))
            elif unknown:
                out.append(_unknown(prop, "%s do not state a coordinate for %s"
                                    % (", ".join(sorted(unknown)), jid),
                                    [cfg["entity_id"], jid]))
            else:
                out.append(_pass(prop, "the declared distinction is realized",
                                 [cfg["entity_id"], jid]))
    return out


def state_configuration_realization(state) -> List[Finding]:
    """Declared configurations are realized, and declared motion is the motion.

    Both directions, because both are wrong. A declared change the endpoints do
    not make is a claim about motion that does not happen; a coordinate that
    moves without being declared is motion nobody said would occur, and the
    clearance evidence was gathered for a different transition than the one the
    design describes.
    """
    states = {st["entity_id"]: st for st in state.standing("State")}
    by_config = {st.get("configuration") or st.get("name"): st
                 for st in state.standing("State")}
    out: List[Finding] = []
    for cfg in sorted(state.standing("Configuration"), key=lambda c: c["entity_id"]):
        basis = cfg.get("distinguishing_basis")
        if not isinstance(basis, list) or not basis:
            continue
        prop = "state_configuration_realization:%s" % cfg["entity_id"]
        if cfg["entity_id"] in by_config:
            out.append(_pass(prop, "the declared configuration is realized",
                             [cfg["entity_id"]]))
        else:
            out.append(_fail(prop, "CONFIGURATION_NOT_REALIZED: it declares a "
                                   "distinguishing basis and has no realized state",
                             [cfg["entity_id"]]))
    for transition in sorted(state.standing("Transition"),
                             key=lambda t: t["entity_id"]):
        prop = "state_configuration_realization:%s" % transition["entity_id"]
        a = states.get(transition.get("from_state"))
        b = states.get(transition.get("to_state"))
        if not (a and b):
            out.append(_unknown(prop, "an endpoint state is not current",
                                [transition["entity_id"]]))
            continue
        ca = a.get("joint_coordinates") or {}
        cb = b.get("joint_coordinates") or {}
        not_realized, undeclared = _s04.coordinate_change_disagreement(
            ca, cb, transition.get("changed_coordinates"))
        if not_realized or undeclared:
            detail = []
            detail += ["DECLARED_CHANGE_NOT_REALIZED: %s stays at %r"
                       % (j, ca.get(j)) for j in sorted(not_realized)]
            detail += ["UNDECLARED_COORDINATE_CHANGE: %s moves %r -> %r"
                       % (j, ca.get(j), cb.get(j)) for j in sorted(undeclared)]
            out.append(_fail(prop, "; ".join(detail), [transition["entity_id"]]))
        else:
            out.append(_pass(prop, "the declared motion is the motion realized",
                             [transition["entity_id"]]))
    return out


def reach_demand_realization(state) -> List[Finding]:
    """Every stated reach demand is answered by a realization that reaches it.

    S01 recorded what the source says an actor must reach; S04·A authored
    whether the arrangement reaches it. The demand could not be edited to match
    the placement and the placement could not narrow the demand, which is what
    makes an unreached demand an ENGINEERING CONSEQUENCE - the mechanism does not
    do what the request required - and the property Rule A establishes for S01.
    """
    results: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for reach in state.standing("ReachResult"):
        results.setdefault((reach.get("actor"), reach.get("target")), []).append(reach)
    out: List[Finding] = []
    for actor in sorted(state.standing("Actor"), key=lambda a: a["entity_id"]):
        for target in actor.get("must_reach") or []:
            prop = "reach_demand_realization:%s|%s" % (actor["entity_id"], target)
            found = results.get((actor["entity_id"], target)) or []
            if not found:
                out.append(_unknown(prop, "no reach result answers this demand",
                                    [actor["entity_id"]]))
            elif all(r.get("reachable") for r in found):
                out.append(_pass(prop, "the arrangement reaches it",
                                 [actor["entity_id"]]
                                 + [r["entity_id"] for r in found]))
            else:
                out.append(_fail(prop, "REACH_DEMAND_UNMET: the arrangement does "
                                       "not reach %s" % target,
                                 [actor["entity_id"]]
                                 + [r["entity_id"] for r in found]))
    return out


# =====================================================================
# EXTERNAL - the actor does not get to report that it acted correctly
# =====================================================================
def commitment_validity(state) -> List[Finding]:
    """A standing commitment exists only over conditions that are met NOW.

    THE GATE DOES NOT REPORT ON ITSELF. This check lived in the s04 module and
    read fields no current SelectionDecision carries, so it reported every
    commitment as evidence-less - a self-fulfilling check that had stopped
    describing the thing it judged. The preconditions are recomputed here from
    the contract's own rule over committed records: a selected candidate must be
    mechanically FEASIBLE_FOR_SELECTION and must satisfy every selection-blocking
    hard requirement, and the commitment must name the human input it came from.

    A commitment standing over violated conditions is FALSE_ACCEPTANCE - the run
    claiming something it had not earned, which is the defect class every other
    rule in this repository is shaped to prevent.
    """
    out: List[Finding] = []
    for decision in sorted(state.standing("SelectionDecision"),
                           key=lambda d: d["entity_id"]):
        did = decision["entity_id"]
        prop = "commitment_validity:%s" % did
        candidate = decision.get("selected_candidate")
        refs = [did] + ([candidate] if candidate else [])
        problems: List[str] = []

        human = [h for h in state.standing("HumanDecisionInput")
                 if h["entity_id"] == decision.get("human_decision")]
        if not human:
            problems.append("no current human decision input named %r"
                            % decision.get("human_decision"))
        elif human[0].get("action") != "SELECT":
            problems.append("the human input records %r, not a selection"
                            % human[0].get("action"))
        elif human[0].get("selected_candidate") != candidate:
            problems.append("the human selected %r and the commitment records %r"
                            % (human[0].get("selected_candidate"), candidate))

        assessments = [m for m in state.standing("MechanicalFeasibilityAssessment")
                       if m.get("candidate") == candidate]
        if len(assessments) != 1:
            problems.append("%d current feasibility assessments for %s"
                            % (len(assessments), candidate))
        elif assessments[0].get("status") != "FEASIBLE_FOR_SELECTION":
            problems.append("%s is %s" % (candidate, assessments[0].get("status")))
        else:
            refs.append(assessments[0]["entity_id"])

        for constraint in sorted(state.standing("DesignConstraint"),
                                 key=lambda c: c["entity_id"]):
            blocks = constraint.get("blocks_selection")
            if blocks is not None and not blocks:
                continue
            compliance = [h for h in state.standing("HardRequirementCompliance")
                          if h.get("candidate") == candidate
                          and h.get("constraint") == constraint["entity_id"]]
            if len(compliance) != 1:
                problems.append("%d current compliance records for %s against %s"
                                % (len(compliance), candidate,
                                   constraint["entity_id"]))
            elif compliance[0].get("status") != "SATISFIED":
                problems.append("%s is %s against %s"
                                % (candidate, compliance[0].get("status"),
                                   constraint["entity_id"]))
            else:
                refs.append(compliance[0]["entity_id"])

        if problems:
            out.append(_fail(prop, "%s: %s" % (FALSE_ACCEPTANCE,
                                               "; ".join(problems)),
                             refs, code=FALSE_ACCEPTANCE))
        else:
            out.append(_pass(prop, "the commitment stands over conditions that "
                                   "are met now", refs))
    return out
