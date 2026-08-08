"""S02 - obligation, load and candidate formation.

Engineering question: what must physically be true, what loads exist, what
families of mechanism could satisfy both, and which of those can we evidence?

Reads ONLY the s02 projection of DesignState. The projection physically removes
SourceClause, so this stage cannot re-read the request even if its prompt asked
it to.

Its two failure modes are opposite and both fatal: collapsing the design space
by naming one mechanism, and inventing an obligation or a load the requirements
do not imply.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..knowledge import PRINCIPLE_FAMILIES, FUNCTION_CLASSES
from ..knowledge.capability_registry import EVIDENCE_ROUTES, route_for_claim
from ..state.patch import Op
from .base import Stage

import re

DIRECTION_CLASSES = ("AXIAL", "TRANSVERSE", "RADIAL", "MOMENT", "GRAVITY", "NONE")

#: Nouns that name a PART. A LoadCase is candidate-independent and must name a
#: role, never one of these. Matched on word boundaries: "gripping" is not a pin.
#: Only nouns that unambiguously name a PRODUCT part. "arm" and "lever" were
#: tried and removed: a request may name an external arm the product carries, or
#: a lever the user presses, and a role described against one of those is a role,
#: not a part.
PART_NOUNS = ("part", "shaft", "pin", "plate", "housing", "bracket")

#: Phrases only an actor-performed action produces. A load "reaches" a reaction
#: site; an actor "operates" something or finds it "reachable".
ACTOR_ACTION_PHRASES = ("reachable", "operate", "operated", "operates",
                        "by hand", "by foot", "the user", "the operator",
                        "user-operated", "performed by the user")
LOAD_KINDS = ("GRAVITY", "PAYLOAD", "ACTOR_APPLIED", "REACTION")

PROMPT = """You are deciding what must physically be true of a product, what
loads act on it, and which families of mechanism could satisfy both.

You receive TYPED REQUIREMENTS AND CONTEXT. You do not receive the original
request and you must not try to reconstruct it. Work only from what is below.

RULES
1. Derive OBLIGATIONS. EVERY requirement must be cited by at least one
   obligation - including the ones nothing here can evidence. Each obligation
   carries:
     - scope: UNIVERSAL if every candidate must satisfy it, or
       CANDIDATE_DISCRIMINATING if how it is satisfied differs by candidate;
     - evidence_route and route_available, taken from the routes listed below.
       A requirement whose route does not exist is ADDRESSED AND
       UN-EVIDENCEABLE, which is a different thing from a requirement nobody
       derived an obligation from. Make it visible.
     - involves_actors, citing the Actor ids, whenever the obligation is about
       something an actor must reach or operate.
     - derivation_premises: the physical premise that makes the requirement
       imply this obligation. A premise is a claim about the world that could
       turn out to be FALSE - "contents that cannot be reached are not stored",
       "a load that is not reacted accelerates the body". Not a restatement of
       the requirement and not a noun phrase. Without it, a later stage that
       finds this obligation unsatisfiable cannot tell whether the obligation
       was wrong or the requirement was.
     - satisfiable_at: a candidate here is a PRINCIPLE FAMILY, not a mechanism.
       There are no elements, no contacts, no dimensions and no geometry yet, so
       an obligation about any of those is NOT satisfiable at s02 and must name
       the earliest stage that could settle it. Marking such an obligation s02
       makes work look done that nobody has done.
   Across the whole set: if every obligation is UNIVERSAL then nothing here
   distinguishes one candidate from another, and the stage that has to choose
   between them will have no grounds. Obligations whose SATISFACTION DIFFERS by
   principle family are CANDIDATE_DISCRIMINATING; say so.

   THIS LIST IS WRITTEN FIRST AND CANNOT BE ADDED TO LATER. Everything after it
   can only refer back to it. So finish choosing your candidate families BEFORE
   you write this list, and include here every obligation those families bring
   with them - the supports, retentions, bounds, clearances and access each
   principle family REQUIRES in order to work at all. Those are obligations in
   exactly the same sense as the ones derived from requirements, and they are
   the ones you will list in obligations_created under rule 4. An obligation you
   only discover while writing the candidates has nowhere left to go: its id
   will point at nothing, and nobody downstream can ever check it.
2. Derive LOAD CASES. A load case says what the WORLD does to the product: which
   scenario, on which body ROLE, reacted at which ROLE, in which direction class
   (AXIAL, TRANSVERSE, RADIAL, MOMENT, GRAVITY, NONE), of which kind (GRAVITY,
   PAYLOAD, ACTOR_APPLIED, REACTION), with a magnitude ONLY if the requirements
   supply one, otherwise magnitude_or_status = "UNSUPPORTED".
   A load case must NOT name a specific part and must NOT say which element
   carries what. That depends on the mechanism, which does not exist yet.
   applied_to_role and reacted_at_role are ROLES, written as the phrase that
   says what the thing DOES - "the surface the product stands on", "the body the
   product grips", "the moving closing role". A single noun or an identifier is
   a part, not a role: `base`, `housing`, `PLATFORM`, `box_body` all name things
   that do not exist yet. Every load terminates somewhere OUTSIDE the product,
   at a site the scenario's system boundary puts outside it; a load reacted
   against the product itself has not been reacted.
   If the requirements state a magnitude with a qualifier, the qualifier travels
   with the number: "approximately 1 kg" does not become "1 kg" here.
3. Form CANDIDATES from the principle families offered below. A candidate names
   the FUNCTION CLASSES it must perform and the PRINCIPLE FAMILY it uses for
   each. Two candidates are only genuinely different if they differ in a
   principle family, not in wording.
4. For every candidate record obligations_addressed AND obligations_created. A
   candidate that needs a support has CREATED a support obligation. Omitting
   this makes an incomplete candidate look cheaper than a complete one.
   obligations_created holds the IDS of obligations you already wrote in the
   obligations list under rule 1 - it is a reference list, not a place to
   introduce something new. If you find yourself needing an id that is not
   already in that list, the omission happened back at rule 1, and the answer is
   to have put it there, not to invent an id here.
5. For every candidate record its evidence_route_verdict from the routes below:
   which route its primary function would need, and whether that route exists.
   If the route does not exist, say so - do not avoid the candidate for it.
6. NEVER select a winner. NEVER score. If several candidates remain plausible
   and nothing distinguishes them, emit an UnresolvedDecision naming the
   evidence that WOULD distinguish them. Every UnresolvedDecision must CITE, by
   id, the Ambiguity or Freedom entities that keep it open (kept_open_by) and
   must type its alternatives list (alternatives_kind: ENTITY_REFS,
   PRINCIPLE_FAMILIES or FREE_TEXT). Do not restate an ambiguity in prose that
   the input already gave you as an entity.
7. Never name a dimension or a position.

PRINCIPLE FAMILIES AVAILABLE (by function class)
{families}

EVIDENCE ROUTES AVAILABLE
{routes}

TYPED INPUT
-----------
{projection}

RESPONSE SCHEMA
Return a single JSON object with exactly these six keys, each holding a list. A
list may be empty - an empty list is a value. Every field is required unless
marked optional. Every id is a string in the format shown.

  obligations[]           id "OBL-0001", statement, derived_from_requirements[],
                          mandatory (boolean), scope, satisfiable_at,
                          evidence_route, route_available (boolean),
                          involves_actors[] (optional),
                          derivation_premises[] (optional)
  load_cases[]            id "LC-0001", scenario, applied_to_role,
                          reacted_at_role, direction_class, kind,
                          magnitude_or_status
  candidates[]            id "CND-0001", summary, family, principle,
                          obligations_addressed[], obligations_created[],
                          evidence_route_verdict {{route, available (boolean),
                          note}}, self_locking (optional)
  acceptance_contracts[]  id "ACC-0001", candidate, obligations[], predicates[]
  unresolved[]            id "UNR-0001", decision, why_open, alternatives[],
                          alternatives_kind, kept_open_by[], blocks[]
  assumptions[]           id "ASM-1001", statement, why, would_be_invalidated_by

No required field may be null. Where the answer is "there are none", use an
empty list for a list field. A null is not an answer; an empty list is.

REFERENCES BETWEEN ITEMS
Each field below holds ids of the kind named. Ids beginning REQ-, SCN-, ACT-,
FRE- and AMB- come from the TYPED INPUT you were given; ids beginning OBL-,
CND- and LC- are ones you emit here. A reference to an id that appears in
neither place is an error.

  obligations[].derived_from_requirements  requirement ids from the input
  obligations[].involves_actors            actor ids from the input
  load_cases[].scenario                    a scenario id from the input
  candidates[].obligations_addressed       obligation ids you emit here
  candidates[].obligations_created         obligation ids you emit here
  acceptance_contracts[].candidate         a candidate id you emit here
  acceptance_contracts[].obligations       obligation ids you emit here
  unresolved[].kept_open_by                ambiguity and freedom ids from the
                                           input - never a restatement in prose
  unresolved[].blocks                      obligation ids you emit here
  unresolved[].alternatives                typed by alternatives_kind: candidate
                                           ids for ENTITY_REFS, family names for
                                           PRINCIPLE_FAMILIES, prose for FREE_TEXT

PERMITTED VALUES
  scope             UNIVERSAL | CANDIDATE_DISCRIMINATING
  satisfiable_at    s02 | s03 | s04 | s05 - the EARLIEST stage at which this
                    obligation can be addressed at all. A candidate here is a
                    principle family and not yet a mechanism, so an obligation
                    about elements, contacts or dimensions is not satisfiable
                    at s02 and must say so rather than appear unaddressed.
  direction_class   AXIAL | TRANSVERSE | RADIAL | MOMENT | GRAVITY | NONE
  load case kind    GRAVITY | PAYLOAD | ACTOR_APPLIED | REACTION
  alternatives_kind ENTITY_REFS | PRINCIPLE_FAMILIES | FREE_TEXT
  family            one of the FUNCTION CLASSES listed above
  principle         one of the PRINCIPLE FAMILIES listed above
  evidence_route    one of the EVIDENCE ROUTES listed above
  scenario          the id of a Scenario given to you in the typed input
"""


def _render_families() -> str:
    lines = []
    for fc in FUNCTION_CLASSES:
        names = ", ".join(f["family"] for f in PRINCIPLE_FAMILIES[fc])
        lines.append("  %s: %s" % (fc, names))
    return "\n".join(lines)


def _render_routes() -> str:
    return "\n".join(
        "  %s: %s (available: %s)" % (r, ", ".join(v["establishes"]), v["available"])
        for r, v in sorted(EVIDENCE_ROUTES.items()))


def _render_projection(proj: Dict[str, List[Dict]]) -> str:
    import json
    slim: Dict[str, Any] = {}
    for fam, rows in sorted(proj.items()):
        slim[fam] = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    return json.dumps(slim, indent=1, sort_keys=True)


class S02ObligationAndCandidates(Stage):
    stage_id = "s02"
    purpose = "derive obligations and load cases, and form candidate principle families"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        proj = inputs["projection"]
        if "SourceClause" in proj:
            raise AssertionError(
                "s02 was handed SourceClause; the projection is not enforcing INV-002")
        return PROMPT.format(families=_render_families(), routes=_render_routes(),
                             projection=_render_projection(proj))

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s02:derivation"
        for o in parsed.get("obligations", []):
            ops.append(Op("CREATE", "Obligation", o["id"], {
                "statement": o["statement"],
                "derived_from_requirements": o.get("derived_from_requirements", []),
                "mandatory": o.get("mandatory", True),
                "scope": o["scope"], "satisfiable_at": o["satisfiable_at"],
                "evidence_route": o["evidence_route"],
                "route_available": o["route_available"],
                "involves_actors": o.get("involves_actors", []),
                "derivation_premises": o.get("derivation_premises", [])}, prov))
        for l in parsed.get("load_cases", []):
            ops.append(Op("CREATE", "LoadCase", l["id"], {
                "scenario": l["scenario"], "applied_to_role": l["applied_to_role"],
                "reacted_at_role": l["reacted_at_role"],
                "direction_class": l["direction_class"], "kind": l["kind"],
                "magnitude_or_status": l["magnitude_or_status"]}, prov))
        for c in parsed.get("candidates", []):
            ops.append(Op("CREATE", "Candidate", c["id"], {
                "summary": c["summary"], "family": c["family"],
                "principle": c["principle"],
                "obligations_addressed": c.get("obligations_addressed", []),
                "obligations_created": c.get("obligations_created", []),
                "evidence_route_verdict": c["evidence_route_verdict"],
                "self_locking": c.get("self_locking")}, prov))
        for a in parsed.get("acceptance_contracts", []):
            ops.append(Op("CREATE", "AcceptanceContract", a["id"], {
                "candidate": a["candidate"], "obligations": a.get("obligations", []),
                "predicates": a.get("predicates", [])}, prov))
        for u in parsed.get("unresolved", []):
            ops.append(Op("CREATE", "UnresolvedDecision", u["id"], {
                "decision": u["decision"], "why_open": u["why_open"],
                "alternatives": u.get("alternatives", []),
                "alternatives_kind": u["alternatives_kind"],
                "kept_open_by": u["kept_open_by"],
                "blocks": u.get("blocks", [])}, prov))
        for a in parsed.get("assumptions", []):
            ops.append(Op("CREATE", "Assumption", a["id"], {
                "statement": a["statement"], "inferred_by_stage": "s02",
                "why": a["why"],
                "would_be_invalidated_by": a["would_be_invalidated_by"]}, prov))
        return ops

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        if not parsed.get("obligations"):
            out.append("no obligations derived")
        if not parsed.get("candidates"):
            out.append("no candidates formed")
        return out


# ------------------------------------------------------------- s02 checks
def no_selection_check(state) -> List[str]:
    """INV-007 / R-15. No selected candidate, no score, no rank."""
    banned = ("selected", "chosen", "winner", "rank", "score", "best", "preferred")
    out = []
    for c in state.family("Candidate"):
        for k, v in c.items():
            if any(b in str(k).lower() for b in banned):
                out.append("SELECTION_FIELD: %s.%s" % (c["entity_id"], k))
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append("NUMERIC_RANK: %s.%s = %r" % (c["entity_id"], k, v))
    return out


#: Hedges whose removal turns an approximate quantity into a sharp one. Ordinary
#: English, not a product or benchmark vocabulary.
QUALIFIER_WORDS = ("approximately", "approx", "about", "around", "roughly",
                   "up to", "at least", "at most", "or so", "nominal",
                   "typical", "near", "close to", "some", "several")


def _reads_as_a_role(text: str) -> bool:
    """A role is a phrase describing a function; a part is a token naming a thing.

    Deliberately shape-based, so it carries no vocabulary to maintain and no
    product knowledge: three or more words, not an identifier, not a constant.
    """
    t = (text or "").strip()
    if not t or "_" in t:
        return False
    if t.isupper():
        return False
    return len(re.findall(r"[A-Za-z]+", t)) >= 3


def magnitude_fidelity_check(state) -> List[str]:
    """S02. A magnitude carried from a requirement keeps that requirement's hedge.

    s01 is protected against sharpening by `sharpening_check`; nothing protected
    s02, and a live run duly turned "approximately 1 kg" into "1 kg" one call in
    eighteen. The stage cannot re-read the source (INV-002), so the comparison is
    against the Requirement entities it was given, which is where the quantity
    legitimately reaches it.
    """
    hedged: List[str] = []
    for r in state.family("Requirement"):
        text = str(r.get("statement_verbatim", "")).lower()
        for q in QUALIFIER_WORDS:
            if re.search(r"\b%s\b" % re.escape(q), text):
                hedged.append(text)
                break
    problems = []
    for l in state.family("LoadCase"):
        magnitude = str(l.get("magnitude_or_status", ""))
        if not magnitude or magnitude == "UNSUPPORTED":
            continue
        low = magnitude.lower()
        if any(re.search(r"\b%s\b" % re.escape(q), low) for q in QUALIFIER_WORDS):
            continue
        for number in re.findall(r"\d+(?:\.\d+)?", magnitude):
            if any(number in h for h in hedged):
                problems.append(
                    "MAGNITUDE_SHARPENED: %s -> %r drops the qualifier the "
                    "requirement carried with %s" % (l["entity_id"], magnitude, number))
                break
    return problems


def load_case_check(state) -> List[str]:
    """S02-C4/C5/C6. Load cases are candidate-independent and complete."""
    out = []
    scenarios = {s["entity_id"]: s for s in state.family("Scenario")}
    for l in state.family("LoadCase"):
        if l.get("direction_class") not in DIRECTION_CLASSES:
            out.append("BAD_DIRECTION_CLASS: %s -> %r" % (l["entity_id"], l.get("direction_class")))
        if l.get("kind") not in LOAD_KINDS:
            out.append("BAD_LOAD_KIND: %s -> %r" % (l["entity_id"], l.get("kind")))
        if l.get("scenario") not in scenarios:
            out.append("UNRESOLVED_SCENARIO: %s -> %r" % (l["entity_id"], l.get("scenario")))
        # A role is a phrase saying what something DOES; a part is a token
        # naming a thing. The structural test replaces the noun list that used
        # to sit here: a curated vocabulary could not tell that `PLATFORM`,
        # `box_body` and `base` name parts, and could not stop `gripping` from
        # matching `pin` either. Shape generalises where vocabulary does not.
        for field in ("applied_to_role", "reacted_at_role"):
            role = str(l.get(field, ""))
            if not _reads_as_a_role(role):
                out.append("LOADCASE_ROLE_READS_AS_A_PART: %s.%s -> %r"
                           % (l["entity_id"], field, role))
        role = str(l.get("applied_to_role", "")).lower()
        if any(re.search(r"\b%s\b" % b, role) for b in PART_NOUNS):
            out.append("LOADCASE_NAMES_A_PART: %s -> %r" % (l["entity_id"], role))
    for s in state.family("Scenario"):
        if s.get("kind") != "OPERATION":
            continue
        if not any(l.get("scenario") == s["entity_id"] for l in state.family("LoadCase")):
            out.append("OPERATION_SCENARIO_WITHOUT_LOADCASE: %s" % s["entity_id"])
    return out


def candidate_distinctness_check(state) -> List[str]:
    """Two candidates are different only if a principle family differs."""
    seen: Dict[str, str] = {}
    out = []
    for c in state.family("Candidate"):
        principle = c.get("principle")
        key = str(sorted(principle.items())) if isinstance(principle, dict) else str(principle)
        if key in seen:
            out.append("CANDIDATES_NOT_DISTINCT: %s duplicates %s" % (c["entity_id"], seen[key]))
        seen[key] = c["entity_id"]
    return out


def known_principle_check(state) -> List[str]:
    """Every principle family must come from the knowledge layer, not prose."""
    known = {f["family"] for fams in PRINCIPLE_FAMILIES.values() for f in fams}
    out = []
    for c in state.family("Candidate"):
        p = c.get("principle")
        used = list(p.values()) if isinstance(p, dict) else [p]
        for u in used:
            for token in (u if isinstance(u, list) else [u]):
                if token not in known:
                    out.append("UNKNOWN_PRINCIPLE: %s uses %r" % (c["entity_id"], token))
    return out


def evidence_route_check(state) -> List[str]:
    """Every candidate declares a route, and unavailable routes are declared."""
    out = []
    for c in state.family("Candidate"):
        v = c.get("evidence_route_verdict") or {}
        if not isinstance(v, dict) or "route" not in v or "available" not in v:
            out.append("NO_ROUTE_VERDICT: %s" % c["entity_id"])
            continue
        if v["route"] not in EVIDENCE_ROUTES:
            out.append("UNKNOWN_ROUTE: %s -> %r" % (c["entity_id"], v["route"]))
        elif EVIDENCE_ROUTES[v["route"]]["available"] != bool(v["available"]):
            out.append("ROUTE_AVAILABILITY_MISSTATED: %s -> %r" % (c["entity_id"], v["route"]))
    return out


def created_obligations_check(state) -> List[str]:
    """R-16. A candidate that creates obligations must say so, or incompleteness wins."""
    return ["NO_CREATED_OBLIGATIONS: %s" % c["entity_id"]
            for c in state.family("Candidate")
            if c.get("obligations_created") is None]


OBLIGATION_SCOPES = ("UNIVERSAL", "CANDIDATE_DISCRIMINATING")


def requirement_coverage_check(state) -> List[str]:
    """Every requirement is cited by an obligation, or nothing addresses it.

    Added after the first evaluation: two to three requirements per case were
    silently un-obligated, and silence read identically to a deliberate decision
    that no route exists.
    """
    cited = set()
    for o in state.family("Obligation"):
        cited.update(o.get("derived_from_requirements") or [])
    return ["REQUIREMENT_WITHOUT_OBLIGATION: %s" % r["entity_id"]
            for r in state.family("Requirement") if r["entity_id"] not in cited]


def obligation_scope_check(state) -> List[str]:
    """Scope is declared, and route availability agrees with the registry."""
    out = []
    for o in state.family("Obligation"):
        if o.get("scope") not in OBLIGATION_SCOPES:
            out.append("BAD_OBLIGATION_SCOPE: %s -> %r" % (o["entity_id"], o.get("scope")))
        route = o.get("evidence_route")
        if route not in EVIDENCE_ROUTES:
            out.append("UNKNOWN_OBLIGATION_ROUTE: %s -> %r" % (o["entity_id"], route))
        elif EVIDENCE_ROUTES[route]["available"] != bool(o.get("route_available")):
            out.append("ROUTE_AVAILABILITY_MISSTATED: %s -> %r" % (o["entity_id"], route))
    return out


def candidate_coverage_check(state) -> List[str]:
    """Every CANDIDATE_DISCRIMINATING obligation is addressed by some candidate.

    Universal obligations are exempt by construction: every candidate must
    satisfy them, so listing them on each would be noise. So are obligations
    that cannot be satisfied until a later stage: a principle family cannot
    discharge something that needs a topology.
    """
    addressed = set()
    for c in state.family("Candidate"):
        addressed.update(c.get("obligations_addressed") or [])
    return ["DISCRIMINATING_OBLIGATION_UNADDRESSED: %s" % o["entity_id"]
            for o in state.family("Obligation")
            if o.get("scope") == "CANDIDATE_DISCRIMINATING"
            and o.get("satisfiable_at") == "s02"
            and o.get("mandatory") and o["entity_id"] not in addressed]


def openness_citation_check(state) -> List[str]:
    """An UnresolvedDecision cites the ambiguity or freedom that keeps it open."""
    known = {e["entity_id"] for e in state.family("Ambiguity")}
    known |= {e["entity_id"] for e in state.family("Freedom")}
    out = []
    for u in state.family("UnresolvedDecision"):
        refs = u.get("kept_open_by") or []
        if not refs:
            out.append("OPENNESS_NOT_CITED: %s" % u["entity_id"])
        for r in refs:
            if r not in known:
                out.append("OPENNESS_CITES_UNKNOWN: %s -> %s" % (u["entity_id"], r))
        if u.get("alternatives_kind") not in ("ENTITY_REFS", "PRINCIPLE_FAMILIES", "FREE_TEXT"):
            out.append("ALTERNATIVES_UNTYPED: %s" % u["entity_id"])
    return out


def actor_citation_check(state) -> List[str]:
    """Reachability obligations cite an actor, so reach is checkable at s04a.

    Corrected after live reasoning on unseen inputs produced four findings and no
    true positives. The old rule matched substrings, so "the load REACHes a
    reaction site" tripped on "reach" and "returns with no USER action" tripped
    on "user" - an obligation whose whole content is that NO actor is involved.
    The rule is now a curated set of phrases that only an actor-performed action
    produces, matched on word boundaries.
    """
    if not state.family("Actor"):
        return []
    out = []
    for o in state.family("Obligation"):
        text = o.get("statement", "").lower()
        if any(re.search(r"\b%s\b" % re.escape(ph), text) for ph in ACTOR_ACTION_PHRASES):
            if not (o.get("involves_actors") or []):
                out.append("REACHABILITY_OBLIGATION_WITHOUT_ACTOR: %s" % o["entity_id"])
    return out


def deferred_obligation_report(state) -> List[str]:
    """What s02 hands to s03 unsatisfied, on purpose. Information, not a fault."""
    return ["DEFERRED_TO_%s: %s" % (o.get("satisfiable_at", "?").upper(), o["entity_id"])
            for o in state.family("Obligation")
            if o.get("satisfiable_at") not in (None, "s02")]
