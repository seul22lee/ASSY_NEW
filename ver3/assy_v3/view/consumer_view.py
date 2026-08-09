"""Consumer Sufficiency: the required minimum, the view, and whether it is enough.

U-3 / M-3. Frozen architecture §4 (freeze FA-6, FA-7).

    REQUIRED MINIMUM = REPRESENTATIONAL DEPENDENCIES
                     ∪ ENGINEERING REASONING PREMISES
                     ∪ justified contributory context

The two required sources are independent and are derived from two different
contracts, neither of which the consuming stage owns:

    SOURCE A  what the stage's permitted OUTPUTS need in order to MEAN something
              -> DESIGN_STATE_CONTRACT field semantics
                 (reference target / spatial frame / explicit dependency)

    SOURCE B  what the stage's assigned DECISIONS need in order to be made
              -> STAGE_RESPONSIBILITY_CONTRACT premise classes
                 -> requires_semantics -> families declaring those semantic roles

WHAT THIS REPLACES
    A hand-written tuple of family names decided what later stages could see. It
    could not express "the arrangement of the selected candidate", and it could
    not notice that a needed class was absent - which is how quantities and the
    S04A arrangement were lost. Nothing here names a family or a stage.

ELIGIBILITY IS NOT RELEVANCE
    Resolving a premise to families answers "which TYPES may satisfy this". It
    does not answer "which accumulated INSTANCES belong in this view". Including
    every instance of an eligible family would turn semantic roles into a context
    dump and would mix design branches. Instance relevance is decided separately,
    by structured canonical relationships only.

DETERMINISTIC
    No model call, no embedding, no similarity. Same contracts + same state +
    same stage + same branch => same view.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class Source(str, Enum):
    REPRESENTATIONAL_DEPENDENCY = "REPRESENTATIONAL_DEPENDENCY"
    REASONING_PREMISE = "REASONING_PREMISE"
    CONTRIBUTORY_CONTEXT = "CONTRIBUTORY_CONTEXT"


class Sufficiency(str, Enum):
    """Per requirement. The distinction between the middle two is the whole point."""

    SATISFIED = "SATISFIED"
    #: The contract requires it and no qualifying authoritative entity exists.
    #: Upstream never established it. Not a model failure and not permission to
    #: invent the premise.
    MISSING_UPSTREAM = "MISSING_UPSTREAM"
    #: The substrate exists but the engineering conclusion is legitimately not
    #: established yet. Distinct from absence.
    UNRESOLVED = "UNRESOLVED"
    #: Qualifying authoritative state EXISTS and view construction failed to carry
    #: it. An infrastructure defect, never an upstream one.
    PROJECTION_FAILURE = "PROJECTION_FAILURE"


class ViewStatus(str, Enum):
    VIEW_READY = "VIEW_READY"
    UPSTREAM_INSUFFICIENCY = "UPSTREAM_INSUFFICIENCY"
    PROJECTION_FAILURE = "PROJECTION_FAILURE"
    BUDGET_INSUFFICIENT = "BUDGET_INSUFFICIENT"


# =====================================================================
# Required minimum
# =====================================================================
class Requirement:
    """One required semantic class, and why it is required.

    The trace is part of the architecture, not a debugging aid: a required set
    with no reasons is indistinguishable from a whitelist someone wrote down.
    """

    __slots__ = ("source", "key", "families", "trace", "by_role")

    def __init__(self, source: Source, key: str, families: List[str],
                 trace: Dict[str, Any], by_role: Optional[Dict[str, List[str]]] = None):
        self.source = source
        self.key = key
        self.families = sorted(families)
        self.trace = trace
        #: The ATOMIC obligations this requirement is made of.
        #:
        #: A premise naming three semantic roles is THREE obligations, not one.
        #: Flattening them into a family union let one satisfied role mark the
        #: whole premise satisfied - the union was non-empty, so the question
        #: "did we select anything?" answered yes while two thirds of the premise
        #: was missing.
        #:
        #: `requires_semantics` means ALL of them. No contract vocabulary
        #: expresses alternatives, and inferring OR from prose would be a guess.
        self.by_role = dict(by_role or {})

    def atoms(self) -> List[Tuple[str, List[str]]]:
        """(obligation, families that can satisfy it). One entry when atomic."""
        if self.by_role:
            return sorted(self.by_role.items())
        return [(self.key, list(self.families))]

    def as_dict(self) -> Dict[str, Any]:
        return {"source": self.source.value, "key": self.key,
                "families": list(self.families), "trace": dict(self.trace),
                "by_role": {k: list(v) for k, v in self.by_role.items()}}

    def __repr__(self) -> str:                                   # pragma: no cover
        return "Requirement(%s, %s, %s)" % (self.source.value, self.key, self.families)


class RequiredMinimum:
    """What a consumer must be given, derived before it runs."""

    __slots__ = ("stage_id", "requirements")

    def __init__(self, stage_id: str, requirements: List[Requirement]):
        self.stage_id = stage_id
        self.requirements = list(requirements)

    def of(self, source: Source) -> List[Requirement]:
        return [r for r in self.requirements if r.source is source]

    def families(self) -> Set[str]:
        return {f for r in self.requirements for f in r.families}

    def as_dict(self) -> Dict[str, Any]:
        return {"stage_id": self.stage_id,
                "requirements": [r.as_dict() for r in self.requirements]}


def _families(contracts) -> Dict[str, Any]:
    return contracts.families


def _resolve_output(semantic: str) -> Tuple[str, Optional[str]]:
    if "." in semantic:
        fam, fld = semantic.split(".", 1)
        return fam, fld
    return semantic, None


def derive_source_a(stage_id: str, contracts, responsibility) -> List[Requirement]:
    """SOURCE A. What must exist for this stage's outputs to have traceable meaning.

    Reads only structured field semantics. Free-form `rules:` prose is never
    consulted - it carries historical and audit rationale including case
    identifiers, and a derivation that read it would not be benchmark-independent.
    """
    fams = _families(contracts)
    stage = responsibility["stages"].get(stage_id) or {}
    out: List[Requirement] = []
    for semantic in stage.get("permitted_output_semantics", []):
        family, field = _resolve_output(semantic)
        spec_all = (fams.get(family) or {}).get("field_semantics") or {}
        fields = [field] if field else list(spec_all)
        for fld in fields:
            spec = spec_all.get(fld)
            if not spec:
                continue
            # A field may carry SEVERAL representational dependencies, and they
            # compose as a UNION. Accumulating them into one variable made a
            # later declaration overwrite an earlier one, so a field declaring
            # both a reference target and an explicit semantic dependency
            # silently lost the reference.
            deps: List[Tuple[str, str]] = []
            if spec.get("kind") == "reference" and spec.get("target"):
                deps.append((spec["target"], "reference target"))
            elif spec.get("kind") == "spatial":
                frame = spec.get("frame")
                if frame and frame != "SELF_DECLARING":
                    deps.append((frame.split(".")[0], "spatial frame"))
            if "semantic_dependency" in spec:
                deps.append((str(spec["semantic_dependency"]).split(".")[0],
                             "declared semantic dependency"))
            for dep, why in deps:
                if dep not in fams:
                    continue
                out.append(Requirement(
                    Source.REPRESENTATIONAL_DEPENDENCY,
                    "%s.%s -[%s]-> %s" % (family, fld, why.split()[0], dep), [dep],
                    {"output_semantic": semantic,
                     "output_field": "%s.%s" % (family, fld),
                     "declaration": why, "requires": dep,
                     "source_contract": "DESIGN_STATE_CONTRACT.field_semantics"}))
    return out


def derive_source_b(stage_id: str, contracts, responsibility) -> List[Requirement]:
    """SOURCE B. What upstream engineering evidence this stage's decisions need.

    Premise -> required semantic roles -> families whose OWN declaration carries
    them. No family is named by a stage contract and none is named here.
    """
    fams = _families(contracts)
    stage = responsibility["stages"].get(stage_id) or {}
    out: List[Requirement] = []
    for premise in stage.get("required_reasoning_premise_classes", []):
        roles = list(premise.get("requires_semantics") or [])
        qualifying: Set[str] = set()
        by_role: Dict[str, List[str]] = {}
        for role in roles:
            match = sorted(f for f, v in fams.items()
                           if role in ((v or {}).get("semantic_roles") or []))
            by_role[role] = match
            qualifying |= set(match)
        out.append(Requirement(
            Source.REASONING_PREMISE, premise["class"], sorted(qualifying),
            {"engineering_question": premise.get("justified_by_question"),
             "why": premise.get("why"), "requires_semantics": roles,
             "qualifying_by_role": by_role,
             "source_contract": "STAGE_RESPONSIBILITY_CONTRACT"
                                ".required_reasoning_premise_classes"},
            by_role=by_role))
    return out


def derive_required_minimum(stage_id: str, contracts, responsibility) -> RequiredMinimum:
    """The union of the two independent sources. Derived BEFORE the stage runs.

    The consuming stage contributes nothing to this. It may not narrow it, and
    there is no parameter through which it could.
    """
    return RequiredMinimum(stage_id,
                           derive_source_a(stage_id, contracts, responsibility)
                           + derive_source_b(stage_id, contracts, responsibility))


# =====================================================================
# Relevant instance selection
# =====================================================================
STANDING = "STANDING"


def _refs_of(entity: Dict[str, Any], family: str, contracts) -> List[Tuple[str, str]]:
    """(field, referenced id) for every declared reference this entity carries."""
    out = []
    for fld, spec in (contracts.field_semantics(family) or {}).items():
        if spec.get("kind") != "reference":
            continue
        val = entity.get(fld)
        for ref in (val if isinstance(val, list) else [val]):
            if isinstance(ref, str) and ref:
                out.append((fld, ref))
    return out


def _reference_graph(state, contracts) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """The DEPENDS-ON graph: X -> Y means "X depends on Y".

    Two edge kinds, both declared and both meaning the same direction:

      typed reference   the value of X names Y, so X needs Y to mean anything
      recorded premise  X was authored FROM Y (S-1 `_premises`), so X depends on
                        it and loses standing when it is withdrawn

    Direction is what makes scope derivable, and the two roles must not be
    confused. Following the arrow from an entity reaches what it was BUILT ON -
    including the candidate it embodies. Following it from a Candidate reaches
    what the candidate itself RESTS ON - the shared upstream material.

    Built from declared semantics only; never from a name heuristic.
    """
    fwd: Dict[str, Set[str]] = {}
    rev: Dict[str, Set[str]] = {}
    for eid in state.entities:
        rec = state.entities[eid]
        edges = {ref for _fld, ref in _refs_of(rec, rec.get("_family"), contracts)}
        edges |= {p for p in (rec.get("_premises") or []) if isinstance(p, str)}
        for ref in edges:
            fwd.setdefault(eid, set()).add(ref)
            rev.setdefault(ref, set()).add(eid)
    return fwd, rev


def committed_branch(state, contracts) -> Optional[str]:
    """The candidate the design has committed to, if it has.

    Read from canonical commitment state, not from a case convention: a standing
    SelectionDecision naming a candidate. Before selection there is no branch and
    alternatives are legitimately all in scope.
    """
    for rec in state.standing("SelectionDecision"):
        for fld, spec in (contracts.field_semantics("SelectionDecision") or {}).items():
            if spec.get("kind") == "reference" and spec.get("target") == "Candidate":
                val = rec.get(fld)
                if isinstance(val, str) and val:
                    return val
    return None


def _branch_of(eid: str, fwd: Dict[str, Set[str]], state, contracts,
               seen: Optional[Set[str]] = None) -> Set[str]:   # retained for callers
    """Which candidates an entity belongs to, by following canonical references.

    An entity that reaches no candidate belongs to none - it is common upstream
    premise material and is in scope for every branch. That is a structural fact
    about the reference graph, not a rule about any family.
    """
    seen = seen or set()
    if eid in seen:
        return set()
    seen.add(eid)
    rec = state.entities.get(eid) if eid in state.entities else None
    if rec is None:
        return set()
    if rec.get("_family") == "Candidate":
        return {eid}
    out: Set[str] = set()
    for ref in fwd.get(eid, ()):
        out |= _branch_of(ref, fwd, state, contracts, seen)
    return out


#: Relevance outcomes. Only the first two enter a view.
ACTIVE_BRANCH = "ACTIVE_BRANCH"
COMMON_UPSTREAM = "COMMON_UPSTREAM"
OTHER_BRANCH = "OTHER_BRANCH"
UNSCOPED = "UNSCOPED"
IN_VIEW = (ACTIVE_BRANCH, COMMON_UPSTREAM)


def _closure(starts, g, limit=64):
    """Everything reachable from `starts` in `g`, including `starts`.

    Bounded and cycle-safe: a visited set plus a hard cap, so a reference cycle
    terminates and a pathological graph cannot run away.
    """
    seen, frontier, steps = set(starts), list(starts), 0
    while frontier and steps < limit:
        nxt = []
        for eid in frontier:
            for ref in g.get(eid, ()):
                if ref not in seen:
                    seen.add(ref)
                    nxt.append(ref)
        frontier = nxt
        steps += 1
    return seen


def _reachable(start, fwd, stop_at, limit=64):
    """Which members of `stop_at` lie strictly downstream of `start`."""
    return _closure(fwd.get(start, ()), fwd, limit) & set(stop_at)


def _branch_rests_on(candidate, fwd, rev):
    """Everything the candidate and the work built on it depend on.

    `rev` from the candidate gives the branch: the candidate plus every entity
    built on it. `fwd` from that whole set gives what the branch rests on.
    """
    return _closure(_closure({candidate}, rev), fwd)


def scope_of(eid, fwd, rev, state, contracts, branch, candidates=None) -> Tuple[str, str]:
    """Why an entity is, or is not, relevant to this consumer. POSITIVE only.

    Two directions on the depends-on graph, and they mean different things:

      eid  ->* Candidate   the entity was BUILT ON that candidate. It belongs to
                           that branch.
      Candidate ->* eid    the candidate, or the work built on it, RESTS ON the
                           entity. It is upstream material, and it is common
                           exactly to the candidates whose branches reach it.

    The upstream direction starts from the whole branch, not from the candidate
    alone. A frame that only the branch's topology names is still material that
    branch rests on, and a stage that must reason about the topology cannot do it
    without the frame.

    An entity in neither direction is UNSCOPED. The rule this replaces inferred
    "unreachable from every candidate => common to every candidate", which is not
    an inference: an orphan and a shared premise both have no branch edge, so it
    put unconnected state into every view.
    """
    if candidates is None:
        candidates = {e["entity_id"] for e in state.standing("Candidate")}
    if eid in candidates:
        if branch is None or eid == branch:
            return ACTIVE_BRANCH, "the candidate under consideration"
        return OTHER_BRANCH, "a different candidate"

    owners = _reachable(eid, fwd, candidates)
    if owners:
        if branch is None:
            return ACTIVE_BRANCH, "pre-selection: built on %s" % sorted(owners)
        if branch in owners:
            return ACTIVE_BRANCH, "built on the committed candidate %s" % branch
        return OTHER_BRANCH, "built only on %s" % sorted(owners)

    relevant = {branch} if branch else candidates
    resting = sorted(c for c in relevant if eid in _branch_rests_on(c, fwd, rev))
    if resting:
        return COMMON_UPSTREAM, "material the %s branch rests on" % (
            resting[0] if len(resting) == 1 else "candidates %s" % resting)

    return UNSCOPED, ("no candidate was built on it and no relevant candidate "
                      "rests on it")


def select_instances(state, contracts, requirement: Requirement,
                     branch: Optional[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Which accumulated instances satisfy this requirement, and why each is here.

    Eligibility by family is necessary and not sufficient. An instance is included
    when it is in scope for the branch under consideration - either because it
    reaches that candidate through canonical references, or because it reaches no
    candidate at all and is therefore common upstream premise material.

    A qualifying instance belonging to a DIFFERENT candidate is excluded: a stage
    working on one committed branch must not silently receive another branch's
    topology because the family matched.
    """
    fwd, rev = _reference_graph(state, contracts)
    cands = {e["entity_id"] for e in state.standing("Candidate")}
    chosen, traces = [], []
    for family in requirement.families:
        for rec in state.standing(family):
            eid = rec["entity_id"]
            scope, why = scope_of(eid, fwd, rev, state, contracts, branch, cands)
            if scope not in IN_VIEW:
                continue
            chosen.append(rec)
            traces.append({"entity_id": eid, "family": family,
                           "source": requirement.source.value,
                           "requirement": requirement.key,
                           "branch_scope": scope, "why_relevant": why,
                           "trace": requirement.trace})
    return chosen, traces


def relevant_ids(state, contracts, branch) -> Dict[str, str]:
    """Every standing entity that is in scope for this consumer, and why.

    Computed from the reference graph ALONE, independently of what any
    requirement selected. Assessment needs this: deciding PROJECTION_FAILURE from
    the view's own contents would let a selection error conclude upstream
    absence, which is the one misdiagnosis the taxonomy exists to prevent.
    """
    fwd, rev = _reference_graph(state, contracts)
    cands = {e["entity_id"] for e in state.standing("Candidate")}
    out = {}
    for eid in state.entities:
        rec = state.entities[eid]
        if rec.get("_validity", STANDING) != STANDING:
            continue
        scope, _why = scope_of(eid, fwd, rev, state, contracts, branch, cands)
        if scope in IN_VIEW:
            out[eid] = rec.get("_family")
    return out


def close_references(state, contracts, selected: Dict[str, Dict[str, Any]],
                     max_depth: int = 3) -> List[Dict[str, Any]]:
    """Bounded representational closure over already-selected entities.

    A selected value whose referent is absent has no traceable meaning, so the
    referent comes too. Bounded by depth and by a visited set, so a cycle
    terminates and one dependency does not flood the graph.
    """
    added = []
    frontier = list(selected)
    depth = 0
    while frontier and depth < max_depth:
        nxt = []
        for eid in frontier:
            rec = selected.get(eid) or (state.entities[eid] if eid in state.entities else None)
            if rec is None:
                continue
            for fld, ref in _refs_of(rec, rec.get("_family"), contracts):
                if ref in selected or ref not in state.entities:
                    continue
                target = state.entities[ref]
                if target.get("_validity", STANDING) != STANDING:
                    continue
                selected[ref] = target
                added.append({"entity_id": ref, "family": target.get("_family"),
                              "source": Source.REPRESENTATIONAL_DEPENDENCY.value,
                              "requirement": "closure",
                              "branch_scope": "REPRESENTATIONAL_CLOSURE",
                              "why_relevant": ("required to give %s.%s a traceable "
                                               "meaning" % (eid, fld)),
                              "trace": {"required_by": eid, "via_field": fld,
                                        "declaration": "reference target",
                                        "depth": depth + 1}})
                nxt.append(ref)
        frontier = nxt
        depth += 1
    return added


# =====================================================================
# The view
# =====================================================================
class ConsumerView:
    """Semantic infrastructure, not a prompt string.

    Inspectable on its own: what was required, what was selected, why each item is
    here, what is missing, and whether the absence is upstream or ours.
    """

    __slots__ = ("stage_id", "run_id", "required", "entities", "traces",
                 "assessment", "status", "omitted", "branch")

    def __init__(self, stage_id, run_id, required, entities, traces, assessment,
                 status, omitted, branch):
        self.stage_id = stage_id
        self.run_id = run_id
        self.required = required
        self.entities = entities
        self.traces = traces
        self.assessment = assessment
        self.status = status
        self.omitted = omitted
        self.branch = branch

    # -- questions a reviewer asks -------------------------------------
    def why(self, entity_id: str) -> List[Dict[str, Any]]:
        return [t for t in self.traces if t["entity_id"] == entity_id]

    def why_missing(self, requirement_key: str) -> Optional[Dict[str, Any]]:
        for a in self.assessment:
            if a["requirement"] == requirement_key:
                return a
        return None

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for rec in self.entities:
            out[rec.get("_family")] = out.get(rec.get("_family"), 0) + 1
        return dict(sorted(out.items()))

    def as_dict(self) -> Dict[str, Any]:
        return {"stage_id": self.stage_id, "run_id": self.run_id,
                "branch": self.branch, "status": self.status.value,
                "required_minimum": self.required.as_dict(),
                "assessment": list(self.assessment),
                "counts": self.counts(), "omitted": list(self.omitted),
                "entities": list(self.entities), "traces": list(self.traces)}

    def payload(self) -> Dict[str, List[Dict[str, Any]]]:
        """The plain by-family structure a renderer consumes. Class C."""
        out: Dict[str, List[Dict[str, Any]]] = {}
        for rec in self.entities:
            out.setdefault(rec.get("_family"), []).append(rec)
        return out


#: Worst-wins ordering when aggregating atomic obligations.
_SEVERITY = {Sufficiency.SATISFIED.value: 0, Sufficiency.UNRESOLVED.value: 1,
             Sufficiency.MISSING_UPSTREAM.value: 2,
             Sufficiency.PROJECTION_FAILURE.value: 3}


def _assess_atom(state, obligation: str, families: List[str], selected_ids: Set[str],
                 relevant: Dict[str, str]) -> Dict[str, Any]:
    """One atomic obligation, judged against accumulated state.

    Three absences that must not be confused:

      nothing exists                     -> MISSING_UPSTREAM
      it exists but none is in scope     -> MISSING_UPSTREAM, with the reason
                                            said out loud. We lost nothing, so
                                            blaming projection would be false.
      a RELEVANT instance exists and did
      not reach the view                 -> PROJECTION_FAILURE, ours
    """
    standing = {f: len(state.standing(f)) for f in families}
    covered = any(fam in families for eid, fam in relevant.items() if eid in selected_ids)
    reachable = any(fam in families for fam in relevant.values())
    if covered:
        verdict, why = Sufficiency.SATISFIED, "a relevant instance was selected"
    elif not any(standing.values()):
        verdict, why = Sufficiency.MISSING_UPSTREAM, "nothing upstream established it"
    elif not reachable:
        verdict, why = (Sufficiency.MISSING_UPSTREAM,
                        "qualifying entities exist but none is in scope for this "
                        "consumer; their relevance is not established")
    else:
        verdict, why = (Sufficiency.PROJECTION_FAILURE,
                        "a relevant qualifying instance exists and did not reach "
                        "the view")
    return {"obligation": obligation, "families": list(families),
            "standing_instances": standing, "verdict": verdict.value, "why": why}


def _assess(state, contracts, requirement: Requirement,
            selected: List[Dict[str, Any]],
            relevant: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Structural sufficiency: per atomic obligation, then aggregated.

    A compound premise cannot be SATISFIED while a required role is not. No model
    is asked, and the view's own contents never decide the verdict.
    """
    if relevant is None:
        relevant = relevant_ids(state, contracts, committed_branch(state, contracts))
    selected_ids = {r["entity_id"] for r in selected}
    coverage = [_assess_atom(state, name, fams, selected_ids, relevant)
                for name, fams in requirement.atoms()]
    worst = (max(coverage, key=lambda c: _SEVERITY[c["verdict"]])["verdict"]
             if coverage else Sufficiency.SATISFIED.value)
    return {"requirement": requirement.key, "source": requirement.source.value,
            "verdict": worst, "coverage": coverage,
            "families": list(requirement.families),
            "selected": len(selected), "trace": requirement.trace}


def build_consumer_view(stage_id: str, state, contracts, responsibility,
                        budget_chars: Optional[int] = None) -> ConsumerView:
    """Derive the minimum, select instances, assess, and record why."""
    required = derive_required_minimum(stage_id, contracts, responsibility)
    branch = committed_branch(state, contracts)

    selected: Dict[str, Dict[str, Any]] = {}
    traces: List[Dict[str, Any]] = []
    assessment: List[Dict[str, Any]] = []

    relevant = relevant_ids(state, contracts, branch)
    for req in required.requirements:
        recs, tr = select_instances(state, contracts, req, branch)
        for rec in recs:
            selected.setdefault(rec["entity_id"], rec)
        traces.extend(tr)
        assessment.append(_assess(state, contracts, req, recs, relevant))

    traces.extend(close_references(state, contracts, selected))

    omitted: List[Dict[str, Any]] = []
    status = ViewStatus.VIEW_READY
    if any(a["verdict"] == Sufficiency.PROJECTION_FAILURE.value for a in assessment):
        status = ViewStatus.PROJECTION_FAILURE
    elif any(a["verdict"] == Sufficiency.MISSING_UPSTREAM.value for a in assessment):
        status = ViewStatus.UPSTREAM_INSUFFICIENCY

    view = ConsumerView(stage_id, getattr(state, "run_id", None), required,
                        list(selected.values()), traces, assessment, status,
                        omitted, branch)

    if budget_chars is not None:
        view = _apply_budget(view, budget_chars)
    return view


# =====================================================================
# Budget
# =====================================================================
def render(view: ConsumerView) -> str:
    """Deterministic serialization of the view. Never of raw state."""
    import json
    return json.dumps(view.payload(), indent=1, sort_keys=True)


def _apply_budget(view: ConsumerView, budget_chars: int) -> ConsumerView:
    """Semantic reduction, never a positional slice.

    Contributory context goes first. The required minimum is never silently
    dropped: if it alone will not fit, that is a recorded condition, because
    budget pressure must not be able to change the engineering contract.
    """
    if len(render(view)) <= budget_chars:
        return view

    required_ids = {t["entity_id"] for t in view.traces
                    if t["source"] != Source.CONTRIBUTORY_CONTEXT.value}
    dropped = [rec for rec in view.entities if rec["entity_id"] not in required_ids]
    kept = [rec for rec in view.entities if rec["entity_id"] in required_ids]
    omitted = list(view.omitted) + [
        {"entity_id": r["entity_id"], "family": r.get("_family"),
         "rule": "contributory context reduced first", "reason": "budget"}
        for r in dropped]

    reduced = ConsumerView(view.stage_id, view.run_id, view.required, kept,
                           view.traces, view.assessment, view.status, omitted,
                           view.branch)
    if len(render(reduced)) <= budget_chars:
        return reduced

    reduced.status = ViewStatus.BUDGET_INSUFFICIENT
    reduced.omitted.append(
        {"rule": "required minimum exceeds budget",
         "reason": "recorded rather than truncated",
         "required_chars": len(render(reduced)), "budget_chars": budget_chars})
    return reduced
