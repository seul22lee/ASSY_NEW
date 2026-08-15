"""WHAT CAN THE DESIGN COMPARE, among the candidates it may still choose from?

NAMED FOR THE RESPONSIBILITY, as `feasibility` is. Pipeline stage numbers mean
other things and S7-A settled that these two are non-numbered.

S7-C. The second producer that calls no provider. `feasibility` answered "can
this candidate work" one candidate at a time; this asks a question no single
branch can answer - how the retained alternatives compare - and it asks it of one
accumulated DesignState.

IT DOES NOT CHOOSE. Every outcome below is a statement about the evidence:
SOLE_ELIGIBLE says one candidate is currently eligible, DOMINANT_UNDER_PROFILE
says the stated preferences discriminate, TRADEOFF_UNRESOLVED says they do not,
NOT_COMPARABLE says a metric the tier needs does not exist. A frontier of one is
not a winner - it is the comparison running out of ways to tell candidates apart,
and the commitment is a human's.

FOUR RULES DECIDE ALMOST EVERYTHING BELOW

    A PREFERENCE NEVER TOUCHES ELIGIBILITY. Eligibility is upstream truth, read
    and never recomputed: the feasibility verdict, and every blocking hard
    requirement satisfied. What somebody wants cannot make a broken mechanism
    choosable, and the two questions are answered by different code reading
    different families.

    THE POPULATION IS COMPLETE OR THERE IS NO COMPARISON. A candidate whose
    eligibility cannot be established from current evidence is not quietly
    dropped - it makes the whole population unestablished. `known ineligible` and
    `eligibility unknown` are different facts, and comparing the subset that
    happened to be knowable would publish a conclusion about a design nobody has.

    NO SURROGATE, AND NO SENTINEL. A criterion with no canonical metric is
    NOT_AVAILABLE and stays that way; Body count is not part count. Unavailable
    is neither good nor bad, so it is never infinity, zero or "worst" - it stops
    the tier instead.

    A HIGHER TIER'S TRADEOFF STAYS A TRADEOFF. MEDIUM is reached only when HIGH
    was an EXACT TIE. Letting the lower tier pick between candidates that
    disagree at the higher one would answer the important question with the
    unimportant one.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..state.patch import Op, StagePatch
from ..view.consumer_view import ViewStatus, branch_membership
from . import s04_envelope_and_motion as s04
from .feasibility import FEASIBLE

RESPONSIBILITY = "selection"

#: The tiers, in the order they are evaluated. Not weights: a lower one is
#: reached only when the one above it did not discriminate at all.
PRIORITIES = ("HIGH", "MEDIUM", "LOW")
OBJECTIVES = ("MINIMIZE", "MAXIMIZE")

SATISFIED, VIOLATED, NOT_YET_EVALUABLE = "SATISFIED", "VIOLATED", "NOT_YET_EVALUABLE"

#: What the deterministic comparison was able to say.
SOLE_ELIGIBLE = "SOLE_ELIGIBLE"
DOMINANT_UNDER_PROFILE = "DOMINANT_UNDER_PROFILE"
TRADEOFF_UNRESOLVED = "TRADEOFF_UNRESOLVED"
NOT_COMPARABLE = "NOT_COMPARABLE"

AVAILABLE, NOT_AVAILABLE = "AVAILABLE", "NOT_AVAILABLE"

#: Ephemeral results. These are execution facts, not state: nothing is written
#: when the design cannot support a comparison, because a record saying "no
#: answer" is still a record somebody would premise on.
NO_SELECTION_PREFERENCES = "NO_SELECTION_PREFERENCES"
PROFILE_INVALID = "PROFILE_INVALID"
PROFILE_AMBIGUOUS = "PROFILE_AMBIGUOUS"
ELIGIBILITY_NOT_ESTABLISHED = "ELIGIBILITY_NOT_ESTABLISHED"
NO_ELIGIBLE_CANDIDATES = "NO_ELIGIBLE_CANDIDATES"
PROFILE_MISSING = "PROFILE_MISSING"
CONTEXT_NOT_READY = "CONTEXT_NOT_READY"
COMPARISON_WRITTEN = "COMPARISON_WRITTEN"
PROFILE_WRITTEN = "PROFILE_WRITTEN"
PROFILE_UNCHANGED = "PROFILE_UNCHANGED"


# =====================================================================
# outcomes
# =====================================================================
class SelectionProfileOutcome:
    """What materialising the preferences produced, and whether it could."""

    __slots__ = ("status", "profile_id", "source_hash", "criteria", "patch",
                 "problems")

    def __init__(self, status, profile_id=None, source_hash=None, criteria=None,
                 patch=None, problems=None):
        self.status = status
        self.profile_id = profile_id
        self.source_hash = source_hash
        self.criteria = dict(criteria or {})
        self.patch = patch
        self.problems = list(problems or [])

    @property
    def ok(self) -> bool:
        return self.status in (PROFILE_WRITTEN, PROFILE_UNCHANGED)


class SelectionComparisonOutcome:
    """What comparing produced. `status` is the EXECUTION fact; `outcome` is the
    engineering one, and exists only when a comparison was written."""

    __slots__ = ("status", "outcome", "frontier", "eligible", "population",
                 "metrics", "stopping_priority", "patch", "problems",
                 "consumer_view")

    def __init__(self, status, outcome=None, frontier=(), eligible=(),
                 population=None, metrics=None, stopping_priority=None,
                 patch=None, problems=None, consumer_view=None):
        self.status = status
        self.outcome = outcome
        self.frontier = list(frontier)
        self.eligible = list(eligible)
        self.population = dict(population or {})
        self.metrics = dict(metrics or {})
        self.stopping_priority = stopping_priority
        self.patch = patch
        self.problems = list(problems or [])
        self.consumer_view = consumer_view

    @property
    def ok(self) -> bool:
        return self.patch is not None and not self.problems


# =====================================================================
# the preference snapshot
# =====================================================================
def canonical_preferences(preferences: Any) -> str:
    """The preference mapping as one canonical string. KEY ORDER IS NOT MEANING.

    Hashes THIS and nothing else. Folding the request text, the hard
    requirements or any engineering fact into the hash would make an unchanged
    preference set look changed every time the design moved - and a profile that
    reversions on unrelated evidence stales every comparison for no reason.
    """
    return json.dumps(preferences, sort_keys=True, separators=(",", ":"))


def profile_identity(preferences: Any) -> Tuple[str, str]:
    """(source_hash, entity id) for a preference snapshot.

    Derived from the content, so the same preferences always produce the same
    identity and calling twice cannot make a second profile. No counter exists.
    """
    digest = hashlib.sha256(canonical_preferences(preferences).encode()).hexdigest()
    return digest, "SPF-%s" % digest[:12].upper()


def validate_preferences(preferences: Any) -> List[str]:
    """What is wrong with the stated preferences, if anything.

    AN UNKNOWN CRITERION NAME IS NOT WRONG. The user may want something this
    pipeline cannot yet measure, and forgetting the request would be a worse
    answer than saying the metric does not exist. What is wrong is an objective
    or a priority outside the declared vocabulary - a preference nothing can act
    on, and one that cannot be silently dropped either, because the remaining
    criteria are not what the user said.
    """
    if not isinstance(preferences, dict):
        return ["selection_preferences is %s, not a mapping of criterion to "
                "{objective, priority}" % type(preferences).__name__]
    problems = []
    for criterion, spec in sorted(preferences.items()):
        if not isinstance(spec, dict):
            problems.append("%s: %r is not {objective, priority}" % (criterion, spec))
            continue
        if spec.get("objective") not in OBJECTIVES:
            problems.append("%s: objective %r; the vocabulary is %s"
                            % (criterion, spec.get("objective"), list(OBJECTIVES)))
        if spec.get("priority") not in PRIORITIES:
            problems.append("%s: priority %r; the vocabulary is %s"
                            % (criterion, spec.get("priority"), list(PRIORITIES)))
    return problems


def materialize_selection_profile(state, selection_preferences: Any,
                                  run_id: Optional[str] = None,
                                  attempt: int = 1) -> SelectionProfileOutcome:
    """Turn the user's stated preferences into the one authoritative snapshot.

    THE FIRST AND ONLY PLACE A PREFERENCE ENTERS STATE. s01 reads the same
    profile document for its hard requirements and never looks at this section;
    nothing between here and there declares the role, so no earlier consumer view
    can contain one.

    `None` means no preference source was supplied, which is different from a
    source that supplies an empty mapping. The first produces no profile at all -
    inventing one would be inventing the user's answer. The second is a real
    snapshot saying "no ranked preference stated", and a comparison under it
    honestly reports that the evidence does not discriminate.
    """
    if selection_preferences is None:
        return SelectionProfileOutcome(NO_SELECTION_PREFERENCES)
    problems = validate_preferences(selection_preferences)
    if problems:
        # NOT PARTIALLY MATERIALISED. Keeping the well-formed criteria would
        # record a preference set the user never stated.
        return SelectionProfileOutcome(PROFILE_INVALID, problems=problems)

    source_hash, eid = profile_identity(selection_preferences)
    standing = state.standing("SelectionProfile")
    if len(standing) > 1:
        return SelectionProfileOutcome(
            PROFILE_AMBIGUOUS,
            problems=["%d current selection profiles: %s. Which preferences are "
                      "in force is the design's to say, and picking one would be "
                      "this code deciding it"
                      % (len(standing),
                         ", ".join(sorted(p["entity_id"] for p in standing)))])
    if standing and standing[0]["entity_id"] == eid:
        # IDEMPOTENT. The same preferences are the same snapshot; a second
        # invocation must not produce a second profile or a new version.
        return SelectionProfileOutcome(PROFILE_UNCHANGED, eid, source_hash,
                                       selection_preferences)

    ops: List[Op] = []
    if standing:
        # SUPERSEDED, NOT OVERWRITTEN. The old snapshot stays readable, and the
        # comparison built on it goes STALE by ordinary propagation - which is
        # how changing what you want reopens the choice without touching one
        # engineering fact.
        ops.append(Op("INVALIDATE", "SelectionProfile", standing[0]["entity_id"], {},
                      "selection:profile",
                      reason="the stated preferences changed; this snapshot is "
                             "no longer what the user asked for"))
    ops.append(Op("CREATE", "SelectionProfile", eid, {
        "profile_version": source_hash[:12],
        "source_hash": source_hash,
        "criteria": {k: dict(v) for k, v in sorted(selection_preferences.items())}},
        "selection:profile"))
    patch = StagePatch(
        patch_id="%s-selection-profile-%s" % (run_id or state.run_id,
                                              source_hash[:8]),
        run_id=run_id or state.run_id, stage_id=RESPONSIBILITY,
        stage_attempt=attempt, parent_state_hash=state.state_hash(),
        operations=ops, execution_status="SUCCESS",
        provenance={"purpose": "materialise the stated selection preferences",
                    "provider": "deterministic"})
    problems = state.validate(patch)
    return SelectionProfileOutcome(
        PROFILE_WRITTEN if not problems else PROFILE_INVALID, eid, source_hash,
        selection_preferences, None if problems else patch, problems)


# =====================================================================
# reading the accumulated design
# =====================================================================
class _Evidence:
    """The retained design, indexed. THE ONLY ENGINEERING CHANNEL.

    Design-wide rather than branch-scoped, because that is the question:
    comparison cannot be done from inside one alternative. Which entity belongs
    to which branch is answered by `branch_membership`, the canonical helper, and
    applied only to ids this view already admitted - a second branch ontology
    would be a second answer to "whose evidence is this".
    """

    def __init__(self, view: Dict[str, Any], membership: Dict[str, set]):
        self.view = view
        self.by_family = {fam: [e for e in rows if isinstance(e, dict)]
                          for fam, rows in view.items() if isinstance(rows, list)}
        self.by_id = {e["entity_id"]: e for rows in self.by_family.values()
                      for e in rows if e.get("entity_id")}
        self.membership = membership

    def fam(self, name: str) -> List[Dict[str, Any]]:
        return list(self.by_family.get(name, []))

    def ids(self, *families: str) -> List[str]:
        return sorted(e["entity_id"] for f in families for e in self.fam(f)
                      if e.get("entity_id"))

    def of_candidate(self, family: str, candidate: str) -> List[Dict[str, Any]]:
        """Entities of this family that the canonical scope says belong to this
        candidate's branch. Never inferred from an id's spelling, its position or
        the order it was created in."""
        return [e for e in self.fam(family)
                if candidate in self.membership.get(e.get("entity_id"), set())]


def evidence_of(state, payload: Dict[str, Any]) -> "_Evidence":
    """The indexed engineering evidence behind one consumer payload.

    ONE CONSTRUCTION, so `eligibility` cannot be asked the same question two ways.
    S7-E re-establishes the eligible population at submit time and must reach that
    answer through exactly this path: a writer that rebuilt the index itself would
    be a second opinion about which entity belongs to which branch, and the two
    would agree until the day they did not.
    """
    admitted = sorted(e["entity_id"] for rows in payload.values() for e in rows
                      if isinstance(e, dict) and e.get("entity_id"))
    return _Evidence(payload, branch_membership(state, state.c, admitted))


def _blocks_selection(constraint: Dict[str, Any]) -> bool:
    """ABSENT MEANS TRUE, which is the contract's declared default. Reading the
    absence as false would let a requirement nobody marked stop blocking."""
    stated = constraint.get("blocks_selection")
    return True if stated is None else bool(stated)


ELIGIBLE, INELIGIBLE, UNRESOLVED = "ELIGIBLE", "INELIGIBLE", "UNRESOLVED"


def eligibility(ev: _Evidence):
    """candidate -> (verdict, why, the exact facts read). Preference-blind.

    Reads only what feasibility established. Nothing here recomputes a domain, a
    compliance status or a maturity: `NOT_YET_EVALUABLE` is feasibility's verdict
    about the evidence and this responsibility may act on it, never restate it.
    """
    constraints = ev.fam("DesignConstraint")
    blocking = sorted(c["entity_id"] for c in constraints if _blocks_selection(c))
    out: Dict[str, Tuple[str, str, List[str]]] = {}
    for candidate in sorted(c["entity_id"] for c in ev.fam("Candidate")):
        # EVERY constraint is read, because whether it blocks is the fact being
        # used - a requirement that turns out not to block was still consulted.
        used = [candidate] + sorted(c["entity_id"] for c in constraints)
        assessments = [m for m in ev.fam("MechanicalFeasibilityAssessment")
                       if m.get("candidate") == candidate]
        if not assessments:
            out[candidate] = (UNRESOLVED, "no current feasibility assessment", used)
            continue
        if len(assessments) > 1:
            out[candidate] = (
                UNRESOLVED, "%d current feasibility assessments (%s)"
                % (len(assessments),
                   ", ".join(sorted(m["entity_id"] for m in assessments))),
                used + sorted(m["entity_id"] for m in assessments))
            continue
        mfa = assessments[0]
        used.append(mfa["entity_id"])
        if mfa.get("status") != FEASIBLE:
            # THE MECHANICAL PREREQUISITE ALREADY FAILED. A missing compliance
            # record for a candidate that cannot work does not leave anything
            # unresolved: nothing a hard requirement could say would make it
            # choosable.
            out[candidate] = (INELIGIBLE, "feasibility is %s" % mfa.get("status"), used)
            continue
        verdict, why = ELIGIBLE, "feasible, and every blocking requirement satisfied"
        for constraint in blocking:
            records = [h for h in ev.fam("HardRequirementCompliance")
                       if h.get("candidate") == candidate
                       and h.get("constraint") == constraint]
            if len(records) != 1:
                verdict = UNRESOLVED
                why = ("%d current compliance records for %s"
                       % (len(records), constraint))
                used += sorted(h["entity_id"] for h in records)
                break
            used.append(records[0]["entity_id"])
            status = records[0].get("status")
            if status == VIOLATED:
                verdict, why = INELIGIBLE, "%s is violated" % constraint
                break
            if status != SATISFIED:
                verdict = INELIGIBLE
                why = "%s is %s at the current maturity" % (constraint, status)
                break
        out[candidate] = (verdict, why, sorted(set(used)))
    return out


# =====================================================================
# the metric registry
# =====================================================================
class Metric:
    """One candidate's value for one criterion, and what it was read from."""

    __slots__ = ("availability", "value", "unit", "reason_code", "source_refs")

    def __init__(self, availability, value=None, unit=None, reason_code="OK",
                 source_refs=()):
        self.availability = availability
        self.value = value
        self.unit = unit
        self.reason_code = reason_code
        self.source_refs = sorted({r for r in source_refs if r})

    def as_dict(self) -> Dict[str, Any]:
        return {"availability": self.availability, "value": self.value,
                "unit": self.unit, "reason_code": self.reason_code,
                "source_refs": list(self.source_refs)}


def _unavailable(reason: str, refs=()) -> Metric:
    """NO FABRICATED NUMBER. `value` and `unit` are null, and the refs are the
    positive facts that were read - never an id invented to stand for a missing
    one."""
    return Metric(NOT_AVAILABLE, None, None, reason, refs)


def _rigid_body_count(ev: _Evidence, candidate: str) -> Metric:
    """How many BODIES this candidate has. NOT how many parts it is made of.

    A Body is a rigid element of the representation; whether two of them are
    manufactured separately, or one of them is bought as an assembly, is a fact
    no contract here establishes. Answering `part_count` with this number would
    answer a question the design has not answered.
    """
    bodies = sorted(b["entity_id"] for b in ev.of_candidate("Body", candidate))
    if not bodies:
        return _unavailable("NO_CANDIDATE_BODY")
    return Metric(AVAILABLE, len(bodies), "count", "OK", bodies)


def _joint_count(ev: _Evidence, candidate: str) -> Metric:
    """How many JOINTS this candidate has. NOT how many actuators it needs.

    A joint is a kinematic relation; how many of them are driven, and by what, is
    not recorded anywhere. `actuation_complexity` is a different question.
    """
    joints = sorted(j["entity_id"] for j in ev.of_candidate("Joint", candidate))
    return Metric(AVAILABLE, len(joints), "count", "OK", joints)


def _package_volume(ev: _Evidence, candidate: str) -> Metric:
    """The volume of the box enclosing the WHOLE candidate.

    Not the sum of its bodies' boxes and not its largest body: those are
    different quantities, and the one a user comparing package volume means is
    the space the assembled thing occupies.

    THE SAME GEOMETRY DISCIPLINE FEASIBILITY USES, through the same helpers. A
    body with no extent, a body with two, or a basis stated twice all make the
    measurement unavailable rather than approximate - an overall dimension read
    off the bodies that happened to be placed is a smaller product answering for
    the real one.
    """
    bodies = sorted(b["entity_id"] for b in ev.of_candidate("Body", candidate))
    if not bodies:
        return _unavailable("NO_CANDIDATE_BODY")
    scales = ev.of_candidate("ReferenceScale", candidate)
    if not scales:
        return _unavailable("NO_REFERENCE_SCALE", bodies)
    if len(scales) > 1:
        return _unavailable("SCALE_AMBIGUOUS",
                            bodies + [s["entity_id"] for s in scales])
    scale = scales[0]
    refs = bodies + [scale["entity_id"]]
    if scale.get("basis") != "ABSOLUTE" or not isinstance(scale.get("absolute"), dict):
        # A RELATIVE basis is a legitimate, honest value and it is not a size.
        # Comparing two candidates' relative volumes would compare two numbers
        # that mean nothing to each other.
        return _unavailable("SCALE_NOT_ABSOLUTE", refs)
    unit = scale["absolute"].get("unit")
    per_unit = scale["absolute"].get("per_unit")
    if not unit or not isinstance(per_unit, (int, float)) or isinstance(per_unit, bool):
        return _unavailable("SCALE_FACTOR_MISSING", refs)

    by_body: Dict[Any, List[Dict[str, Any]]] = {}
    for e in ev.of_candidate("Envelope", candidate):
        by_body.setdefault(e.get("body"), []).append(e)
    boxes, used = [], list(refs)
    for body in bodies:
        found = [e for e in (by_body.get(body) or []) if s04._extent_box(e)]
        if len(found) != 1:
            return _unavailable(
                "GEOMETRY_AMBIGUOUS" if len(found) > 1 else "GEOMETRY_INCOMPLETE",
                used + [e["entity_id"] for e in (by_body.get(body) or [])])
        boxes.append(s04._extent_box(found[0]))
        used.append(found[0]["entity_id"])
    lo = [min(b[0][i] for b in boxes) for i in range(3)]
    hi = [max(b[1][i] for b in boxes) for i in range(3)]
    spans = [(hi[i] - lo[i]) * per_unit for i in range(3)]
    return Metric(AVAILABLE, spans[0] * spans[1] * spans[2], "%s^3" % unit,
                  "OK", used)


#: criterion -> evaluator. THE ONLY WAY A CRITERION CAN INFLUENCE ANYTHING. A
#: name absent from this table is NOT_AVAILABLE, whatever it resembles - the
#: registry is what stops "assembly_complexity" quietly becoming a step count.
METRIC_REGISTRY = {
    "rigid_body_count": _rigid_body_count,
    "joint_count": _joint_count,
    "package_volume": _package_volume,
}


def evaluate_metric(ev: _Evidence, criterion: str, candidate: str) -> Metric:
    evaluator = METRIC_REGISTRY.get(criterion)
    if evaluator is None:
        return _unavailable("NO_CANONICAL_METRIC_SOURCE")
    return evaluator(ev, candidate)


# =====================================================================
# the tiered comparison
# =====================================================================
def _better(objective: str, a: float, b: float) -> bool:
    return a < b if objective == "MINIMIZE" else a > b


def _dominates(objectives, va, vb) -> bool:
    """A dominates B: no worse everywhere, strictly better somewhere.

    Per criterion, on its own objective. No weight, no normalization, no order
    among the criteria of one tier - each is compared to itself.
    """
    if any(_better(objectives[c], vb[c], va[c]) for c in objectives):
        return False
    return any(_better(objectives[c], va[c], vb[c]) for c in objectives)


def incomparable_criteria(criteria, metrics, population: Sequence[str]):
    """Criteria whose AVAILABLE values are stated in more than one unit.

    Reported beside the outcome so a NOT_COMPARABLE record says which of the two
    reasons it had - a criterion nobody could measure, or one measured in units
    that do not meet.
    """
    return sorted(c for c in criteria
                  if len({metrics[c][k].unit for k in population
                          if metrics[c][k].availability == AVAILABLE}) > 1)


def compare(criteria: Dict[str, Dict[str, str]], metrics, population: Sequence[str]):
    """(outcome, frontier, stopping_priority). No candidate id is ever consulted.

    `population` is already the eligible set. Sorting below is for a stable
    RECORD, never for a decision: two candidates the evidence does not
    distinguish both stay in the frontier.
    """
    frontier = sorted(population)
    if len(frontier) == 1:
        return SOLE_ELIGIBLE, frontier, None
    for priority in PRIORITIES:
        tier = {c: spec["objective"] for c, spec in criteria.items()
                if spec.get("priority") == priority}
        if not tier:
            continue
        # STEP 1 - every criterion of this tier, for every candidate still in the
        # frontier. An unavailable one stops the comparison here: the available
        # subset is a different question, and a lower tier is not a fallback for
        # a higher one nobody could evaluate.
        missing = sorted(c for c in tier for k in frontier
                         if metrics[c][k].availability != AVAILABLE)
        # AND THEY MUST BE THE SAME QUANTITY. Two established values are not two
        # comparable numbers: 2 cm3 is not less than 1000 mm3, and `<` says it
        # is. This is a property of the PAIR, not of either record - both metrics
        # are perfectly AVAILABLE - so it belongs here and not in the evaluator
        # that computed them.
        #
        # No conversion is attempted. Nothing in this repository is an authority
        # on what one unit is worth in another, and inventing a table here would
        # make this file that authority.
        incomparable = sorted(c for c in tier
                              if len({metrics[c][k].unit for k in frontier}) > 1)
        if missing or incomparable:
            return NOT_COMPARABLE, frontier, priority
        values = {k: {c: metrics[c][k].value for c in tier} for k in frontier}
        # STEP 2 - Pareto dominance within the tier.
        surviving = [k for k in frontier
                     if not any(_dominates(tier, values[o], values[k])
                                for o in frontier if o != k)]
        if len(surviving) == 1:
            return DOMINANT_UNDER_PROFILE, surviving, priority
        frontier = sorted(surviving)
        # STEP 3 - a lower tier may only break an EXACT TIE. Candidates that
        # trade off against one another inside this tier disagree about
        # something the user called this important, and MEDIUM does not get to
        # settle what HIGH could not.
        first = values[frontier[0]]
        if any(values[k] != first for k in frontier[1:]):
            return TRADEOFF_UNRESOLVED, frontier, priority
    return TRADEOFF_UNRESOLVED, frontier, None


# =====================================================================
# the invocation
# =====================================================================
def evaluate_candidate_comparison(state, run_id: Optional[str] = None,
                                  attempt: int = 1) -> SelectionComparisonOutcome:
    """What the design can deterministically say about its retained alternatives.

    NO PROVIDER, and no branch: the invocation is design-wide because the
    question is. The profile must already be in state - building the view first
    and special-casing its absence would make the preference a side channel
    rather than the authoritative snapshot it is.
    """
    from ..view import consumer_view_for

    if len(state.standing("SelectionProfile")) > 1:
        return SelectionComparisonOutcome(
            PROFILE_AMBIGUOUS,
            problems=["more than one current selection profile; which "
                      "preferences are in force is not this code's to decide"])
    view = consumer_view_for(RESPONSIBILITY, state)
    if view.status is not ViewStatus.VIEW_READY:
        unmet = [a["requirement"] for a in view.assessment
                 if a["verdict"] != "SATISFIED"]
        status = (PROFILE_MISSING
                  if any("selection_preference" in u for u in unmet)
                  else CONTEXT_NOT_READY)
        return SelectionComparisonOutcome(
            status, problems=["%s: consumer context is %s"
                              % (RESPONSIBILITY, view.status.value)] + unmet,
            consumer_view=view.as_dict())

    payload = view.payload()
    ev = evidence_of(state, payload)

    profiles = ev.fam("SelectionProfile")
    if len(profiles) != 1:
        return SelectionComparisonOutcome(
            PROFILE_AMBIGUOUS if profiles else PROFILE_MISSING,
            problems=["%d selection profiles in the view" % len(profiles)],
            consumer_view=view.as_dict())
    profile = profiles[0]
    criteria = {k: v for k, v in (profile.get("criteria") or {}).items()
                if isinstance(v, dict)}

    population = eligibility(ev)
    unresolved = sorted(k for k, (v, _w, _u) in population.items() if v == UNRESOLVED)
    if unresolved:
        # THE POPULATION, NOT THE SUBSET. A candidate whose eligibility cannot be
        # established is not excluded - it is unknown, and comparing the others
        # would publish a conclusion about a design nobody has.
        return SelectionComparisonOutcome(
            ELIGIBILITY_NOT_ESTABLISHED, population=population,
            problems=["%s: %s" % (k, population[k][1]) for k in unresolved],
            consumer_view=view.as_dict())
    eligible = sorted(k for k, (v, _w, _u) in population.items() if v == ELIGIBLE)
    if not eligible:
        return SelectionComparisonOutcome(
            NO_ELIGIBLE_CANDIDATES, population=population,
            consumer_view=view.as_dict())

    # METRICS FOR EVERY STATED CRITERION, for every eligible candidate - so the
    # record says what could not be measured as well as what could.
    metrics = {c: {k: evaluate_metric(ev, c, k) for k in eligible} for c in criteria}
    outcome, frontier, stopping = compare(criteria, metrics, eligible)

    # THE RAW FACTS, DIRECTLY. `_propagate` is one hop, so premising the profile
    # and the assessments would leave this standing when an envelope a volume was
    # measured from is superseded: the assessment is not what changed.
    premises = {profile["entity_id"]}
    for _candidate, (_verdict, _why, used) in sorted(population.items()):
        premises |= set(used)
    for criterion in sorted(metrics):
        for candidate in sorted(metrics[criterion]):
            premises |= set(metrics[criterion][candidate].source_refs)

    eid = "CCP-%s" % profile["source_hash"][:12].upper()
    ops = [Op("CREATE", "CandidateComparison", eid, {
        "candidates": list(eligible),
        "profile": profile["entity_id"],
        "metrics": {c: {k: m.as_dict() for k, m in sorted(per.items())}
                    for c, per in sorted(metrics.items())},
        "outcome": outcome,
        "frontier": list(frontier),
        "stopping_priority": stopping,
        "unavailable_criteria": sorted(
            c for c in metrics
            if any(m.availability != AVAILABLE for m in metrics[c].values())),
        "incomparable_criteria": incomparable_criteria(criteria, metrics,
                                                       eligible)},
        "selection:comparison", premise_refs=sorted(premises))]
    patch = StagePatch(
        patch_id="%s-selection-comparison-%s" % (run_id or state.run_id, eid),
        run_id=run_id or state.run_id, stage_id=RESPONSIBILITY,
        stage_attempt=attempt, parent_state_hash=state.state_hash(),
        operations=ops, execution_status="SUCCESS",
        provenance={"purpose": "compare the eligible candidates deterministically",
                    "provider": "deterministic"})
    problems = state.validate(patch)
    return SelectionComparisonOutcome(
        COMPARISON_WRITTEN, outcome, frontier, eligible, population,
        {c: {k: m.as_dict() for k, m in per.items()} for c, per in metrics.items()},
        stopping, None if problems else patch, problems, view.as_dict())
