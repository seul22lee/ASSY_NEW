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

import re
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
class UnknownConsumer(KeyError):
    """A stage id with no responsibility declaration. Fails closed."""


class Requirement:
    """One required semantic class, and why it is required.

    The trace is part of the architecture, not a debugging aid: a required set
    with no reasons is indistinguishable from a whitelist someone wrote down.
    """

    __slots__ = ("source", "key", "families", "trace", "by_role", "selection")

    def __init__(self, source: Source, key: str, families: List[str],
                 trace: Dict[str, Any], by_role: Optional[Dict[str, List[str]]] = None,
                 selection: Optional[Dict[str, Dict[str, str]]] = None):
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
        #: Per atomic obligation: WHERE its instances are drawn from and HOW
        #: COMPLETE the selection must be. The semantic role says what qualifies;
        #: this says which of the qualifying instances this question needs. They
        #: are different questions, and collapsing them is what made a design-wide
        #: demand answerable from one branch's material.
        self.selection = dict(selection or {})

    def selection_for(self, obligation: str) -> Dict[str, str]:
        """The population/coverage/applicability rule for one atomic obligation."""
        return self.selection.get(obligation) or self.selection.get(self.key) or {
            "population": INVOCATION_BRANCH, "coverage": AT_LEAST_ONE,
            "existence": REQUIRED_NONEMPTY, "applicability": ALL_MEMBERS}

    def atoms(self) -> List[Tuple[str, List[str]]]:
        """(obligation, families that can satisfy it). One entry when atomic."""
        if self.by_role:
            return sorted(self.by_role.items())
        return [(self.key, list(self.families))]

    def as_dict(self) -> Dict[str, Any]:
        return {"source": self.source.value, "key": self.key,
                "families": list(self.families), "trace": dict(self.trace),
                "by_role": {k: list(v) for k, v in self.by_role.items()},
                "selection": {k: dict(v) for k, v in self.selection.items()}}

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


def _authority_of(responsibility_id: str) -> str:
    """The owning stage a responsibility writes as.

    `s03a` and `s03b` are two responsibilities of one owner. The split is a
    trailing pass letter on the stage id and nothing else; this reads it back
    rather than keeping a table of which pass belongs to which stage.
    """
    return responsibility_id[:-1] if re.match(r"^s\d+[a-z]$", responsibility_id) \
        else responsibility_id


def derive_source_a(stage_id: str, contracts, responsibility) -> List[Requirement]:
    """SOURCE A. What must exist for this stage's outputs to have traceable meaning.

    Reads only structured field semantics. Free-form `rules:` prose is never
    consulted - it carries historical and audit rationale including case
    identifiers, and a derivation that read it would not be benchmark-independent.
    """
    fams = _families(contracts)
    stage = responsibility["stages"].get(stage_id) or {}
    #: Families this stage authors ITSELF. A reference from one of its outputs to
    #: another is CO-PRODUCED, not a pre-stage input: s02 emits a candidate that
    #: addresses an obligation s02 emitted in the same patch, and demanding the
    #: obligation beforehand asks s02 to have already done its own work. Whether
    #: the co-produced referent actually resolves is real, and it is checked where
    #: it belongs - at the write boundary, over the patch that contains both.
    #:
    #: Derived from the stage's own declared outputs, so a future stage that
    #: co-produces a mutually-referencing pair needs no change here and no pair is
    #: named anywhere.
    co_produced = {_resolve_output(s)[0]
                   for s in stage.get("permitted_output_semantics", [])}
    authority = (stage.get("authority_stage")
                 or (responsibility.get("stages", {}).get(stage_id) or {}).get("owner")
                 or _authority_of(stage_id))
    out: List[Requirement] = []
    for semantic in stage.get("permitted_output_semantics", []):
        family, field = _resolve_output(semantic)
        spec_all = (fams.get(family) or {}).get("field_semantics") or {}
        extendable = (fams.get(family) or {}).get("extendable_fields") or {}
        if field:
            fields = [field]
        else:
            # A field the contract says ANOTHER stage extends is that stage's to
            # author, and its dependencies are that stage's to have. Charging the
            # creating responsibility for them asks s03 to hold what s04 will
            # write. Derived from `extendable_fields`; no stage is named here and
            # no field is listed.
            fields = [f for f in spec_all
                      if extendable.get(f) in (None, authority)]
        # A premise carried inside a list of records is still a representational
        # dependency of this output: a disposition citing a Scenario cannot be
        # authored, let alone read, unless the Scenario is there. Flattened to
        # `field.subfield` so one rule below serves both depths - the nested
        # declaration brings its own cardinality and population, which is the
        # point of declaring it in the same vocabulary.
        pairs: List[Tuple[str, Dict[str, Any]]] = []
        for fld in fields:
            spec = spec_all.get(fld)
            if not spec:
                continue
            if spec.get("kind") == "premise_record_list":
                for sub, subspec in (spec.get("record_field_semantics") or {}).items():
                    pairs.append(("%s.%s" % (fld, sub), subspec))
            else:
                pairs.append((fld, spec))
        for fld, spec in pairs:
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
            required_fields = (fams.get(family) or {}).get("required_fields") or []
            # WHETHER A REFERENT MUST EXIST FOLLOWS THE FIELD'S OWN DECLARATION.
            #
            # An OPTIONAL field may simply not be authored, so nothing has to
            # exist for it to point at. A MANY field is satisfied by the empty
            # list, which this contract states elsewhere is a VALUE - "this step
            # activates nothing" is an answer. Only a required single-valued
            # reference cannot be authored without a referent.
            #
            # Treating all three alike demanded upstream material for relations
            # the stage was free not to author at all.
            single_required = (fld in required_fields
                               and spec.get("cardinality") != "many")
            # A CONDITIONAL OUTPUT IS ONE PRODUCED PER INSTANCE OF SOMETHING.
            # Where the stage declares that, the referent may legitimately not
            # exist: no instances, no records, and a complete answer. Without it
            # a stage was blocked on the referent of an output it need not
            # produce at all - a compliance record needs a constraint to be
            # about, but a design that states no constraint produces none.
            # The record's own requirement is untouched; this is about READINESS.
            if family in (stage.get("conditional_outputs") or {}):
                single_required = False
            existence = REQUIRED_NONEMPTY if single_required else MAY_BE_EMPTY
            population = spec.get("referent_population") or INVOCATION_BRANCH
            if population not in _POPULATIONS:
                raise ValueError(
                    "%s.%s declares referent_population %r; the vocabulary is %s"
                    % (family, fld, population, sorted(_POPULATIONS)))
            # WHICH of the population may be referenced, on the same principle
            # as WHERE it comes from: the field says so.
            #
            # A family reached by two requirements is selected by their UNION, so
            # narrowing a premise alone narrows nothing while any other path
            # still admits the wider set. `obligation_to_discharge` was narrowed
            # to the committed candidate's duties and the obligations arrived
            # anyway, through `Realization.addresses_obligations` - the field a
            # realization uses to cite them.
            referent_applicability = (spec.get("referent_applicability")
                                      or ALL_MEMBERS)
            if referent_applicability not in APPLICABILITY_RULES:
                raise ValueError(
                    "%s.%s declares referent_applicability %r; the declared "
                    "rules are %s" % (family, fld, referent_applicability,
                                      sorted(APPLICABILITY_RULES)))
            for dep, why in deps:
                if dep not in fams or dep in co_produced:
                    continue
                out.append(Requirement(
                    Source.REPRESENTATIONAL_DEPENDENCY,
                    "%s.%s -[%s]-> %s" % (family, fld, why.split()[0], dep), [dep],
                    {"output_semantic": semantic,
                     "output_field": "%s.%s" % (family, fld),
                     "declaration": why, "requires": dep,
                     "source_contract": "DESIGN_STATE_CONTRACT.field_semantics"},
                    selection={"%s.%s -[%s]-> %s" % (family, fld, why.split()[0], dep): {
                        # WHERE the referent may come from is the FIELD's to say.
                        # A blanket INVOCATION_BRANCH asked a load case to be
                        # branch-scoped before s03b ran, when authoring
                        # `LoadPath.load_case` is precisely what makes it branch
                        # material - a circle the stage could never enter.
                        #
                        # Making every dependency DESIGN_WIDE instead was tried
                        # and FALSIFIED: it admitted another branch's topology and
                        # broke the isolation SELECT-09/10/23 and S3ROOT-16/17
                        # pin. So neither answer is universal, and the contract
                        # declares it per field. Undeclared stays branch-local:
                        # an unclassified reference must not widen what a consumer
                        # sees by default.
                        "population": population, "coverage": AT_LEAST_ONE,
                        "existence": existence,
                        "applicability": referent_applicability}}))
    return out


def _selection_of(premise: Dict[str, Any], roles: List[str]) -> Dict[str, Dict[str, str]]:
    """The premise's declared instance-selection rule, per atomic obligation.

    A premise usually needs one population for everything it asks for. One does
    not: s04a needs the actors, which are a demand on the design, together with
    the regions the branch it is working on authored. Where the roles differ the
    contract says so per role; where they do not, one declaration covers them.
    """
    decl = premise.get("instance_selection")
    if not decl:
        raise KeyError(
            "premise %r declares no instance_selection. A premise that says WHAT "
            "it needs without saying WHICH instances is not resolvable: the "
            "resolver would have to guess a population, and guessing is what the "
            "declaration exists to prevent." % premise.get("class"))
    if decl.get("by_role"):
        out = {}
        for row in decl["by_role"]:
            out[row["role"]] = {"population": row["population"],
                                "coverage": row["coverage"],
                                "existence": row["existence"],
                                "applicability": row.get("applicability") or ALL_MEMBERS}
        missing = [r for r in roles if r not in out]
        if missing:
            raise KeyError("premise %r declares populations per role and omits %s"
                           % (premise.get("class"), missing))
        return out
    rule = {"population": decl["population"], "coverage": decl["coverage"],
            "existence": decl["existence"],
            "applicability": decl.get("applicability") or ALL_MEMBERS}
    return {role: dict(rule) for role in roles} or {premise["class"]: rule}


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
        selection = _selection_of(premise, roles)
        out.append(Requirement(
            Source.REASONING_PREMISE, premise["class"], sorted(qualifying),
            {"engineering_question": premise.get("justified_by_question"),
             "why": premise.get("why"), "requires_semantics": roles,
             "qualifying_by_role": by_role,
             "instance_selection": {k: dict(v) for k, v in selection.items()},
             "source_contract": "STAGE_RESPONSIBILITY_CONTRACT"
                                ".required_reasoning_premise_classes"},
            by_role=by_role, selection=selection))
    return out


def derive_required_minimum(stage_id: str, contracts, responsibility) -> RequiredMinimum:
    """The union of the two independent sources. Derived BEFORE the stage runs.

    The consuming stage contributes nothing to this. It may not narrow it, and
    there is no parameter through which it could.

    An unknown stage is a configuration error, not an empty minimum. `s03` looks
    like a stage and is not one - the contract declares `s03a` and `s03b` - and
    asking for it used to yield a view that required nothing, selected nothing,
    and reported VIEW_READY. Absence of a responsibility declaration cannot mean
    "nothing is required"; a consumer must never be handed nothing and told it has
    everything.
    """
    declared = set((responsibility or {}).get("stages") or {})
    if stage_id not in declared:
        raise UnknownConsumer(
            "no consumer stage %r in the responsibility contract; it declares %s"
            % (stage_id, sorted(declared)))
    return RequiredMinimum(stage_id,
                           derive_source_a(stage_id, contracts, responsibility)
                           + derive_source_b(stage_id, contracts, responsibility))


# =====================================================================
# Namespace occupancy
#
# A SECOND KIND OF SUFFICIENCY, and deliberately not a third source of the
# required minimum above. That minimum answers "what must this consumer KNOW to
# reason". This answers "what must it know to AUTHOR without colliding", and the
# two are different questions with different privileges.
#
# THE RULE, stated generally:
#
#   If a responsibility may CREATE entities in family F, and committed
#   DesignState may already contain entities in F, the responsibility must
#   receive enough identity-level context to know which ids in F are occupied.
#
# S9-E found the consequence of not having it. `Assumption` is universally
# ownable, so s01 and s02 both author into one namespace. s01 commits ASM-0001
# and ASM-0002; s02's view carried no Assumption at all, because a co-produced
# family is correctly excluded from the SEMANTIC minimum; and the response schema
# shows every family's example id at first index. Three independent live attempts
# were rejected with the identical DUPLICATE_ID: ASM-0001. The model was asked to
# author into a namespace it could not see, and the defect is here rather than in
# its reasoning.
#
# WHY IT IS NOT SEMANTIC VISIBILITY
#
# Least privilege is the point. s02 needs to know ASM-0001 is taken. It does not
# need to know what s01 assumed, and granting it the family's semantic content to
# solve an id collision would widen the view for a reason that has nothing to do
# with reasoning. So this carries IDS ONLY - no statement, no why, no fields.
# =====================================================================
def creatable_families(responsibility_id: str, responsibility) -> Set[str]:
    """Families this responsibility may bring into existence.

    Read from `permitted_output_semantics`, FAMILY-level entries only. A dotted
    entry like `Joint.frame_origin` is a field this responsibility may author
    onto a Joint somebody else created - an EXTEND, which occupies no new id and
    can collide with nothing.
    """
    stage = (responsibility.get("stages") or {}).get(responsibility_id) or {}
    return {s.split(".", 1)[0]
            for s in stage.get("permitted_output_semantics", []) if "." not in s}


def derive_namespace_occupancy(responsibility_id: str, state,
                               responsibility) -> Dict[str, List[str]]:
    """Which ids are already taken in each family this responsibility may create.

    DERIVED FROM COMMITTED DESIGNSTATE and from nothing else. Not from the
    prompt's examples, not from a fixture, not from `pairing_history`, not from a
    counter and not from a prefix range - every one of those is a claim about
    what was written somewhere rather than about what state actually holds, and
    the write boundary rejects a duplicate on what state holds.

    `family()` and not `standing()`: validity and occupancy are different
    questions. `DesignState.validate` reports DUPLICATE_ID against the whole
    entity table, so an invalidated or superseded id is still spent. Offering it
    back as available would produce a collision that reads as the model's fault.

    Families with nothing in them are omitted rather than carried as empty lists:
    "no id is taken here" is what an absent family already says, and rendering a
    page of empty families would bury the ones that matter.
    """
    out: Dict[str, List[str]] = {}
    for family in sorted(creatable_families(responsibility_id, responsibility)):
        ids = sorted(e["entity_id"] for e in state.family(family))
        if ids:
            out[family] = ids
    return out


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


class AmbiguousSelection(RuntimeError):
    """More than one SelectionDecision stands. There is no committed branch.

    The write boundary refuses to create a second standing decision, so reaching
    this means state arrived by some path that invariant did not cover. Raised
    rather than resolved: picking one of two contradictory commitments is a
    selection, and selection is a human authority that no resolver may exercise
    on the design's behalf.
    """


def committed_branch(state, contracts) -> Optional[str]:
    """The candidate the design has committed to, if it has.

    Read from canonical commitment state, not from a case convention: a standing
    SelectionDecision naming a candidate. Before selection there is no branch and
    alternatives are legitimately all in scope.

    THREE outcomes, and the third used to be missing. This iterated the standing
    decisions and returned the first one carrying a candidate reference - so two
    contradictory commitments produced one silent answer, and s05, s06 and s07
    all followed it while nothing recorded that another decision existed. The
    invariant `one_standing_selection` now prevents that state; this fails
    closed in case it is ever reached anyway, because a wrong branch here is not
    an error anyone would see - it is a complete, plausible design for the wrong
    alternative.
    """
    standing = list(state.standing("SelectionDecision"))
    if len(standing) > 1:
        raise AmbiguousSelection(
            "%d SelectionDecisions stand (%s); exactly one may speak for the "
            "design, and choosing between them is not a resolver's to make"
            % (len(standing),
               ", ".join(sorted(r.get("entity_id", "?") for r in standing))))
    for rec in standing:
        for fld, spec in (contracts.field_semantics("SelectionDecision") or {}).items():
            if spec.get("kind") == "reference" and spec.get("target") == "Candidate":
                val = rec.get(fld)
                if isinstance(val, str) and val:
                    return val
    return None


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


def branches_built_on(eid, fwd, candidates):
    """The candidates this entity was BUILT ON - its branch membership.

    The ONE answer to "which branch is this". `scope_of` turns it into a
    relevance verdict for one consumer; a caller that has to reason about the
    accumulated design rather than about one invocation needs the membership
    itself, and computing it a second way would be a second branch ontology.
    """
    return _reachable(eid, fwd, candidates)


def branch_membership(state, contracts, ids) -> Dict[str, Set[str]]:
    """entity id -> the branches it was built on, over accumulated state.

    Empty for an entity no candidate reaches, and empty for EVERY entity while no
    candidate stands - which is the same rule `_population_members` applies to
    INVOCATION_BRANCH: before the work branches, "this branch" is the design.
    """
    candidates = {e["entity_id"] for e in state.standing("Candidate")}
    if not candidates:
        return {eid: set() for eid in ids}
    fwd, _rev = _reference_graph(state, contracts)
    return {eid: branches_built_on(eid, fwd, candidates) for eid in ids}


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

    owners = branches_built_on(eid, fwd, candidates)
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


# =====================================================================
# Instance selection: WHERE the instances come from, and HOW MANY
# =====================================================================
#: Populations. Defined once in STAGE_RESPONSIBILITY_CONTRACT
#: .instance_selection_vocabulary; the names below are that vocabulary, and the
#: resolver below is the only thing that turns them into instances.
DESIGN_WIDE = "DESIGN_WIDE"
INVOCATION_BRANCH = "INVOCATION_BRANCH"
COMMITTED_BRANCH = "COMMITTED_BRANCH"
ALL_RETAINED_BRANCHES = "ALL_RETAINED_BRANCHES"

#: Coverage.
ALL_APPLICABLE = "ALL_APPLICABLE"
AT_LEAST_ONE = "AT_LEAST_ONE"

#: Existence. Whether the applicable population is allowed to be empty. This is a
#: different question from coverage: "every recorded ambiguity" is satisfied by a
#: design that recorded none, "the full requirement set" is not, and one term
#: cannot carry both.
MAY_BE_EMPTY = "MAY_BE_EMPTY"
REQUIRED_NONEMPTY = "REQUIRED_NONEMPTY"

#: Applicability rules. The registry is the seam.
ALL_MEMBERS = "ALL_MEMBERS"
MATCHES_INVOCATION_ANCHORS = "MATCHES_INVOCATION_ANCHORS"


class InvocationContext:
    """What THIS reasoning invocation is about. Identity, never facts.

    An anchor is a canonical entity id: the scenario being reasoned about, the
    configuration, the branch. It GUIDES selection and is not itself engineering
    content - the moment it carried facts it would be a second context channel
    beside the view, which is the thing U-3 exists to remove.

    Anchors are typed by the family of the entity they name, read from state
    rather than declared here, so no family is enumerated and a new anchor kind
    needs no code.
    """

    __slots__ = ("branch", "anchors")

    def __init__(self, branch: Optional[str] = None,
                 anchors: Optional[Dict[str, str]] = None):
        self.branch = branch
        self.anchors = dict(anchors or {})

    @classmethod
    def of(cls, state, branch: Optional[str] = None, *anchor_ids: str):
        """Anchors given by id alone; their family is read from standing state.

        An id that names nothing fails here rather than silently selecting
        nothing later.
        """
        anchors = {}
        for eid in anchor_ids:
            if not state.has_entity(eid):
                raise ValueError("invocation anchor %r is not in state" % eid)
            anchors[state.stored_family(eid)] = eid
        return cls(branch, anchors)

    def as_dict(self) -> Dict[str, Any]:
        return {"branch": self.branch, "anchors": dict(self.anchors)}

    def __repr__(self) -> str:                                   # pragma: no cover
        return "InvocationContext(%r, %r)" % (self.branch, self.anchors)


_ANCHORS = (DESIGN_WIDE, INVOCATION_BRANCH, COMMITTED_BRANCH, ALL_RETAINED_BRANCHES)
_POPULATIONS = frozenset(_ANCHORS)


def _population_members(population: str, state, contracts, branch,
                        scopes: "_Scopes") -> Optional[Set[str]]:
    """The entity ids in that population, or None when it is everything.

    Each population is a different RELEVANCE MODEL, chosen by the premise rather
    than applied globally, and each resolves against its OWN branch anchor. The
    invocation's branch and the committed branch are different questions, and a
    single scope map computed once for the view could only answer one of them.
    """
    if population == DESIGN_WIDE:
        return None
    if population == INVOCATION_BRANCH:
        if not state.standing("Candidate"):
            # POSITIVE and observable: no alternative has been proposed, so the
            # work has not branched and "the branch this invocation is working on"
            # IS the design. Without this a consumer that runs before candidate
            # generation reported its upstream absent while it was standing in
            # front of it.
            return None
        return scopes.in_view(branch)
    if population == COMMITTED_BRANCH:
        committed = committed_branch(state, contracts)
        if committed is None:
            # No selection has been recorded, so there is no committed branch.
            # Saying "everything" here would let a stage that must realize THE
            # chosen alternative read another one's state.
            return set()
        return scopes.in_view(committed)
    if population == ALL_RETAINED_BRANCHES:
        # Anchored at no single candidate: every branch still standing, and what
        # they share. Comparison cannot be done from inside one alternative.
        return scopes.not_unscoped(None)
    raise ValueError("unknown population %r; the vocabulary is %s"
                     % (population, sorted(_ANCHORS)))


def _applicable(ids, rule: str, context: Dict[str, Any]):
    """Which members of the population apply to this invocation.

    ONE dispatch point. A premise that later applies conditionally declares a
    named rule in the contract and it is resolved here - which is why a
    scenario-specific or configuration-specific requirement needs no change to
    selection, assessment, or the view. Rules must read canonical structured
    relations. Never text in a field, never a stage id, never a model's opinion.
    """
    fn = APPLICABILITY_RULES.get(rule)
    if fn is None:
        raise ValueError("unknown applicability rule %r; declared rules are %s"
                         % (rule, sorted(APPLICABILITY_RULES)))
    return fn(ids, context)


def _matches_invocation_anchors(ids, ctx):
    """Instances scoped to something this invocation is not about are dropped.

    Generic by construction: it compares an instance's DECLARED references
    against the invocation's DECLARED anchors. It never names a family, a
    scenario, a configuration or an id - the anchor supplies which, the contract
    supplies where to look, and the same rule serves every anchor kind that ever
    exists.

    An instance that declares no reference to an anchored family, or leaves it
    unset, applies EVERYWHERE. It was not scoped to one context, so no anchor can
    exclude it.
    """
    invocation = ctx.get("invocation")
    if not invocation or not invocation.anchors:
        return ids
    state, contracts = ctx["state"], ctx["contracts"]
    keep = set()
    for eid in ids:
        rec = state.entities.get(eid) if state.has_entity(eid) else None
        if rec is None:
            continue
        scoped_out = False
        for field, referent in _refs_of(rec, rec.get("_family"), contracts):
            target = state.stored_family(referent) if state.has_entity(referent) else None
            anchor = invocation.anchors.get(target)
            if anchor is not None and referent != anchor:
                scoped_out = True
                break
        if not scoped_out:
            keep.add(eid)
    return keep


#: `Obligation.scope`, verbatim from DESIGN_STATE_CONTRACT.
UNIVERSAL_SCOPE = "UNIVERSAL"
CANDIDATE_DISCRIMINATING_SCOPE = "CANDIDATE_DISCRIMINATING"


def applicable_obligation_ids(obligations, acceptances) -> Set[str]:
    """Which obligations THIS candidate owes. THE single semantic authority.

    Record-based and pure, so the same rule can be applied to the two shapes
    that need it: the ConsumerView narrows the population by reading standing
    state, and S05-C4 validates against the recorded view payload. Those are
    different data, and if each computed applicability its own way the stage
    would be asked to realize one set and judged against another - which is
    exactly the contradiction this replaced.

    The split is already in the contract:

      UNIVERSAL                 every candidate must satisfy it
      CANDIDATE_DISCRIMINATING  satisfaction differs by candidate, so it applies
                                to this one exactly when this candidate's
                                AcceptanceContract took it on

    `satisfiable_at` is deliberately not consulted: it names the EARLIEST stage
    at which an obligation can be satisfied, so reading it as ownership would
    drop every obligation that became satisfiable upstream and is still this
    candidate's to realize in geometry.

    Fails OPEN on an unstated scope. An obligation nobody classified is an
    obligation nobody excused, and dropping it would turn a missing field into a
    discharged duty.
    """
    accepted: Set[str] = set()
    for contract in acceptances or ():
        accepted.update(contract.get("obligations") or ())

    out: Set[str] = set()
    for record in obligations or ():
        oid = record.get("entity_id")
        if not oid:
            continue
        scope = str(record.get("scope") or "").strip().upper()
        if scope == CANDIDATE_DISCRIMINATING_SCOPE and oid not in accepted:
            continue
        out.add(oid)
    return out


def _applicable_to_committed_candidate(ids, ctx):
    """Narrow an obligation population to what the committed candidate owes.

    Narrowing the VIEW rather than showing everything and asking the consumer to
    ignore most of it. A stage shown a design-wide obligation set and told to
    realize it will realize it - including obligations that exist only because a
    rejected alternative worked differently - and the resulting claims about a
    mechanism nobody chose would be accepted into state.

    The acceptance contracts are read from the committed branch, which is the
    same anchor `candidate_acceptance` populates from, so the view cannot narrow
    against one candidate while presenting another's acceptance.
    """
    state, contracts = ctx["state"], ctx["contracts"]
    obligations = [r for r in state.standing("Obligation")
                   if r.get("entity_id") in ids]
    if len(obligations) != len(ids):
        # Some member is not an Obligation. This rule speaks only about
        # obligations, so anything else passes through untouched rather than
        # being silently dropped by a rule that does not understand it.
        other = {i for i in ids if i not in {r.get("entity_id") for r in obligations}}
    else:
        other = set()
    branch = ctx.get("branch") or committed_branch(state, contracts)
    acceptances = [r for r in state.standing("AcceptanceContract")
                   if not branch or r.get("candidate") == branch]
    return applicable_obligation_ids(obligations, acceptances) | other


APPLICABLE_TO_COMMITTED_CANDIDATE = "APPLICABLE_TO_COMMITTED_CANDIDATE"

APPLICABILITY_RULES: Dict[str, Any] = {
    ALL_MEMBERS: lambda ids, _ctx: ids,
    MATCHES_INVOCATION_ANCHORS: _matches_invocation_anchors,
    APPLICABLE_TO_COMMITTED_CANDIDATE: _applicable_to_committed_candidate,
}


def expected_instances(state, contracts, families: List[str], rule: Dict[str, str],
                       branch, scopes: Optional["_Scopes"] = None,
                       invocation: Optional[InvocationContext] = None) -> Set[str]:
    """Which standing instances SHOULD satisfy one atomic obligation.

    Computed from the contracts, the authoritative state and the premise's own
    declaration - never from what the view happens to contain. Sufficiency that
    read its own expectation off the selection could only ever agree with itself.
    """
    if scopes is None:
        scopes = _Scopes(state, contracts)
    members = _population_members(rule.get("population", INVOCATION_BRANCH),
                                  state, contracts, branch, scopes)
    ids = {rec["entity_id"] for family in families
           for rec in state.standing(family)
           if members is None or rec["entity_id"] in members}
    return set(_applicable(ids, rule.get("applicability") or ALL_MEMBERS,
                           {"state": state, "contracts": contracts,
                            "families": list(families), "branch": branch,
                            "invocation": invocation}))


class _Scopes:
    """Branch scope for every standing entity, per anchor, computed on demand.

    One view can hold several populations anchored at different branches, so the
    scope map is keyed by anchor rather than fixed when the view is built.
    """

    __slots__ = ("state", "contracts", "_fwd", "_rev", "_cands", "_by_anchor")

    def __init__(self, state, contracts):
        self.state, self.contracts = state, contracts
        self._fwd, self._rev = _reference_graph(state, contracts)
        self._cands = {e["entity_id"] for e in state.standing("Candidate")}
        self._by_anchor: Dict[Optional[str], Dict[str, str]] = {}

    def for_branch(self, anchor: Optional[str]) -> Dict[str, str]:
        if anchor not in self._by_anchor:
            out = {}
            for eid in self.state.entities:
                if self.state.entities[eid].get("_validity") != STANDING:
                    continue
                out[eid] = scope_of(eid, self._fwd, self._rev, self.state,
                                    self.contracts, anchor, self._cands)[0]
            self._by_anchor[anchor] = out
        return self._by_anchor[anchor]

    def in_view(self, anchor: Optional[str]) -> Set[str]:
        return {e for e, s in self.for_branch(anchor).items() if s in IN_VIEW}

    def not_unscoped(self, anchor: Optional[str]) -> Set[str]:
        return {e for e, s in self.for_branch(anchor).items() if s != UNSCOPED}


def select_instances(state, contracts, requirement: Requirement,
                     branch: Optional[str],
                     scopes: Optional[Dict[str, str]] = None,
                     invocation: Optional[InvocationContext] = None):
    """Which accumulated instances satisfy this requirement, and why each is here.

    Eligibility by family is necessary and not sufficient - and the sufficient
    part is not one rule. Each atomic obligation carries its own population, so a
    demand on the whole design and a commitment made on one branch are answered by
    different relevance models in the same view. Branch lineage is one of those
    models, not the gate on all of them.
    """
    if scopes is None:
        scopes = _Scopes(state, contracts)
    chosen, traces = [], []
    seen: Set[str] = set()
    for obligation, families in requirement.atoms():
        rule = requirement.selection_for(obligation)
        wanted = expected_instances(state, contracts, families, rule, branch, scopes,
                                    invocation)
        for family in families:
            for rec in state.standing(family):
                eid = rec["entity_id"]
                if eid not in wanted or eid in seen:
                    continue
                seen.add(eid)
                chosen.append(rec)
                traces.append({"entity_id": eid, "family": family,
                               "source": requirement.source.value,
                               "requirement": requirement.key,
                               "obligation": obligation,
                               "population": rule.get("population"),
                               "coverage": rule.get("coverage"),
                               "existence": rule.get("existence"),
                               "applicability": rule.get("applicability"),
                               "branch_scope": scopes.for_branch(branch).get(eid, UNSCOPED),
                               "why_relevant": _why_population(
                                   rule, scopes.for_branch(branch).get(eid)),
                               "trace": requirement.trace})
    return chosen, traces


def _why_population(rule: Dict[str, str], scope: Optional[str]) -> str:
    population = rule.get("population")
    if population == DESIGN_WIDE:
        return ("a demand on the design as a whole; it applies whatever "
                "alternative is being worked on")
    return "%s material (%s)" % (population.lower().replace("_", " "),
                                 scope or UNSCOPED)


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
                 "assessment", "status", "omitted", "branch", "occupancy")

    def __init__(self, stage_id, run_id, required, entities, traces, assessment,
                 status, omitted, branch, occupancy=None):
        self.stage_id = stage_id
        self.run_id = run_id
        self.required = required
        self.entities = entities
        self.traces = traces
        self.assessment = assessment
        self.status = status
        self.omitted = omitted
        self.branch = branch
        #: IDENTITY-LEVEL OCCUPANCY, family -> occupied ids. Carried on the view
        #: rather than fetched by whoever renders the prompt, so it travels the
        #: same recorded, provenanced path as everything else the consumer is
        #: given. Defaults to empty so a view built by a test or a tool that does
        #: not supply it is still a valid view - an honest "nothing declared",
        #: never a silent claim that no id is taken.
        self.occupancy = dict(occupancy or {})

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
                # Recorded on the view's own record, so what a stage was told was
                # taken can be read back from the run afterwards rather than
                # rebuilt from state that has since moved.
                "namespace_occupancy": {k: list(v)
                                        for k, v in sorted(self.occupancy.items())},
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


def _assess_atom(state, contracts, obligation: str, families: List[str],
                 rule: Dict[str, str], selected_ids: Set[str], branch,
                 scopes: "_Scopes",
                 invocation: Optional[InvocationContext] = None) -> Dict[str, Any]:
    """One atomic obligation, judged by comparing EXPECTED against SELECTED.

    Expected is derived independently - contracts, authoritative state, and the
    premise's own declaration. Three absences that must not be confused:

      nothing applicable exists          -> MISSING_UPSTREAM
      applicable instances exist and the
      view carries none                  -> PROJECTION_FAILURE, ours
      the view carries some but the
      premise means all of them          -> PROJECTION_FAILURE, ours

    The last one is the case a "did we select anything?" test could never see:
    nineteen requirements exist, nine arrive, and the coverage the question needs
    is not there.
    """
    standing = {f: len(state.standing(f)) for f in families}
    expected = expected_instances(state, contracts, families, rule, branch, scopes,
                                  invocation)
    got = expected & set(selected_ids)
    coverage = rule.get("coverage") or AT_LEAST_ONE
    existence = rule.get("existence") or REQUIRED_NONEMPTY
    enough = bool(got) if coverage == AT_LEAST_ONE else got == expected

    if not expected and existence == REQUIRED_NONEMPTY:
        # This premise cannot proceed without established material. Reported
        # before coverage is considered at all: nothing was lost, so calling it a
        # projection failure would blame the wrong party.
        verdict, why = (Sufficiency.MISSING_UPSTREAM,
                        "no applicable instance exists in the %s population, and "
                        "this premise requires at least one" % rule.get("population"))
    elif not expected:
        # Empty is a valid design state here. "Every recorded X" is satisfied by
        # a design that recorded none; selecting all of nothing IS all of it.
        verdict, why = (Sufficiency.SATISFIED,
                        "no applicable instance exists, which this premise permits")
    elif enough:
        verdict, why = Sufficiency.SATISFIED, "%d of %d applicable instances selected" % (
            len(got), len(expected))
    elif not got:
        verdict, why = (Sufficiency.PROJECTION_FAILURE,
                        "%d applicable instances exist and none reached the view"
                        % len(expected))
    else:
        verdict, why = (Sufficiency.PROJECTION_FAILURE,
                        "the premise requires every applicable instance; %d of %d "
                        "reached the view" % (len(got), len(expected)))
    return {"obligation": obligation, "families": list(families),
            "standing_instances": standing, "verdict": verdict.value, "why": why,
            "population": rule.get("population"), "coverage": coverage,
            "existence": existence, "applicability": rule.get("applicability"),
            "expected": sorted(expected), "expected_count": len(expected),
            "selected": sorted(got), "selected_count": len(got)}


def _assess(state, contracts, requirement: Requirement,
            selected: List[Dict[str, Any]], branch=None,
            scopes: Optional["_Scopes"] = None,
            invocation: Optional[InvocationContext] = None) -> Dict[str, Any]:
    """Structural sufficiency: per atomic obligation, then aggregated.

    A compound premise cannot be SATISFIED while a required role is not. No model
    is asked, and the view's own contents never decide the verdict.
    """
    if scopes is None:
        scopes = _Scopes(state, contracts)
    selected_ids = {r["entity_id"] for r in selected}
    coverage = [_assess_atom(state, contracts, name, fams,
                             requirement.selection_for(name), selected_ids,
                             branch, scopes, invocation)
                for name, fams in requirement.atoms()]
    worst = (max(coverage, key=lambda c: _SEVERITY[c["verdict"]])["verdict"]
             if coverage else Sufficiency.SATISFIED.value)
    return {"requirement": requirement.key, "source": requirement.source.value,
            "verdict": worst, "coverage": coverage,
            "families": list(requirement.families),
            "selected": len(selected), "trace": requirement.trace}


def build_consumer_view(stage_id: str, state, contracts, responsibility,
                        budget_chars: Optional[int] = None,
                        invocation_branch: Optional[str] = None,
                        invocation: Optional[InvocationContext] = None) -> ConsumerView:
    """Derive the minimum, select instances, assess, and record why.

    `invocation_branch` is the explicit control input: the candidate this call is
    working on. It is what INVOCATION_BRANCH populations resolve against. When it
    is not given the committed branch is used, which is right for a stage that
    runs once after selection and wrong to assume for one that runs per candidate
    - so the caller says which it is rather than the view guessing.
    """
    required = derive_required_minimum(stage_id, contracts, responsibility)
    branch = (invocation_branch or (invocation.branch if invocation else None)
              or committed_branch(state, contracts))

    selected: Dict[str, Dict[str, Any]] = {}
    traces: List[Dict[str, Any]] = []
    assessment: List[Dict[str, Any]] = []

    scopes = _Scopes(state, contracts)
    for req in required.requirements:
        recs, tr = select_instances(state, contracts, req, branch, scopes, invocation)
        for rec in recs:
            selected.setdefault(rec["entity_id"], rec)
        traces.extend(tr)
        assessment.append(_assess(state, contracts, req, recs, branch, scopes,
                                  invocation))

    traces.extend(close_references(state, contracts, selected))

    omitted: List[Dict[str, Any]] = []
    status = ViewStatus.VIEW_READY
    if any(a["verdict"] == Sufficiency.PROJECTION_FAILURE.value for a in assessment):
        status = ViewStatus.PROJECTION_FAILURE
    elif any(a["verdict"] == Sufficiency.MISSING_UPSTREAM.value for a in assessment):
        status = ViewStatus.UPSTREAM_INSUFFICIENCY

    view = ConsumerView(stage_id, getattr(state, "run_id", None), required,
                        list(selected.values()), traces, assessment, status,
                        omitted, branch,
                        derive_namespace_occupancy(stage_id, state, responsibility))

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

    # OCCUPANCY SURVIVES REDUCTION. Budget pressure may drop context; it may not
    # make a taken id look available. Dropping a semantic record costs the model
    # information it can declare missing, whereas dropping an id costs it a
    # collision it cannot see coming and would be blamed for. It is also the
    # cheapest thing in the view - a list of short strings - so there is no
    # tension here to resolve.
    reduced = ConsumerView(view.stage_id, view.run_id, view.required, kept,
                           view.traces, view.assessment, view.status, omitted,
                           view.branch, view.occupancy)
    if len(render(reduced)) <= budget_chars:
        return reduced

    reduced.status = ViewStatus.BUDGET_INSUFFICIENT
    reduced.omitted.append(
        {"rule": "required minimum exceeds budget",
         "reason": "recorded rather than truncated",
         "required_chars": len(render(reduced)), "budget_chars": budget_chars})
    return reduced
