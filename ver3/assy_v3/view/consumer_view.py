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

    __slots__ = ("source", "key", "families", "trace")

    def __init__(self, source: Source, key: str, families: List[str], trace: Dict[str, Any]):
        self.source = source
        self.key = key
        self.families = sorted(families)
        self.trace = trace

    def as_dict(self) -> Dict[str, Any]:
        return {"source": self.source.value, "key": self.key,
                "families": list(self.families), "trace": dict(self.trace)}

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
            dep, why = None, None
            if spec.get("kind") == "reference":
                dep, why = spec.get("target"), "reference target"
            elif spec.get("kind") == "spatial":
                frame = spec.get("frame")
                if frame and frame != "SELF_DECLARING":
                    dep, why = frame.split(".")[0], "spatial frame"
            if "semantic_dependency" in spec:
                dep = str(spec["semantic_dependency"]).split(".")[0]
                why = "declared semantic dependency"
            if not dep or dep not in fams:
                continue
            out.append(Requirement(
                Source.REPRESENTATIONAL_DEPENDENCY,
                "%s.%s -> %s" % (family, fld, dep), [dep],
                {"output_semantic": semantic, "output_field": "%s.%s" % (family, fld),
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
                                ".required_reasoning_premise_classes"}))
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
    """Forward and reverse canonical references over accumulated state.

    Built from declared reference semantics only - never from a name heuristic.
    """
    fwd: Dict[str, Set[str]] = {}
    rev: Dict[str, Set[str]] = {}
    for eid in state.entities:
        rec = state.entities[eid]
        for _fld, ref in _refs_of(rec, rec.get("_family"), contracts):
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
               seen: Optional[Set[str]] = None) -> Set[str]:
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
    fwd, _rev = _reference_graph(state, contracts)
    chosen, traces = [], []
    for family in requirement.families:
        for rec in state.standing(family):
            eid = rec["entity_id"]
            owners = _branch_of(eid, fwd, state, contracts)
            if branch is not None and owners and branch not in owners:
                continue                      # another design branch
            chosen.append(rec)
            traces.append({"entity_id": eid, "family": family,
                           "source": requirement.source.value,
                           "requirement": requirement.key,
                           "branch_scope": ("common upstream" if not owners
                                            else sorted(owners)),
                           "trace": requirement.trace})
    return chosen, traces


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


def _assess(state, contracts, requirement: Requirement,
            selected: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Structural sufficiency for one requirement. No model is asked."""
    existing = {f: len(state.standing(f)) for f in requirement.families}
    any_exists = any(existing.values())
    if selected:
        verdict = Sufficiency.SATISFIED
    elif not any_exists:
        # Nothing upstream established it. Not our failure, and not permission to
        # invent it.
        verdict = Sufficiency.MISSING_UPSTREAM
    else:
        # Qualifying authoritative state exists and did not reach the view. That
        # is an infrastructure defect, and calling it upstream absence would hide
        # exactly the failure this architecture was built to expose.
        verdict = Sufficiency.PROJECTION_FAILURE
    return {"requirement": requirement.key, "source": requirement.source.value,
            "verdict": verdict.value, "families": list(requirement.families),
            "standing_instances": existing, "selected": len(selected),
            "trace": requirement.trace}


def build_consumer_view(stage_id: str, state, contracts, responsibility,
                        budget_chars: Optional[int] = None) -> ConsumerView:
    """Derive the minimum, select instances, assess, and record why."""
    required = derive_required_minimum(stage_id, contracts, responsibility)
    branch = committed_branch(state, contracts)

    selected: Dict[str, Dict[str, Any]] = {}
    traces: List[Dict[str, Any]] = []
    assessment: List[Dict[str, Any]] = []

    for req in required.requirements:
        recs, tr = select_instances(state, contracts, req, branch)
        for rec in recs:
            selected.setdefault(rec["entity_id"], rec)
        traces.extend(tr)
        assessment.append(_assess(state, contracts, req, recs))

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
