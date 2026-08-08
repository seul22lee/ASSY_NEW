"""S01 - requirement capture.

Engineering question: what did the user actually say, and what did they leave
open?

The only stage that may read raw source text (INV-002). Its failure mode is
SHARPENING - turning "approximately 300" into 300, or an absent quantity into a
plausible one - so every check below is aimed at that.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from ..state.patch import Op
from .base import Stage

QUANTITY_CLASSES = ("MAGNITUDE", "BAND", "COMPARATIVE", "NONE")

#: Nouns that name a MECHANISM rather than a function. Deliberately narrow: a
#: word that a user could plausibly write in a request is not on this list, and
#: anything present in the source is exempt regardless.
DISTINCTIVE_MECHANISM_TOKENS = (
    "revolute", "prismatic", "helical", "spherical", "flexure", "slider",
    "pinion", "follower", "linkage", "journal", "undercut", "detent",
    "bayonet", "wedge", "incline", "ratchet", "pawl", "cam", "pulley",
    "bearing", "hinge", "gear", "spring", "screw", "thread",
)
SCENARIO_KINDS = ("OPERATION", "SERVICE", "ASSEMBLY", "TRANSPORT")

PROMPT = """You are performing requirement capture on a product request.

Read the request below and convert it into typed statements. You are the only
stage that will ever see this text; every later stage reads only what you emit.

RULES
1. Never invent a requirement the text does not state.
2. Never sharpen a qualifier. "approximately 80-100 mm" stays approximate and is
   a BAND, not a magnitude.
3. Never resolve an ambiguity. Record it.
4. Never name a mechanism, a material, a part or a dimension. If the text does
   not say how, you do not say how.
5. For every requirement record its quantity_class: MAGNITUDE (a number),
   BAND (a range or an approximate value), COMPARATIVE (more/less than
   something) or NONE (no quantity at all). NONE is a fact and must be recorded
   as one.
6. Record every scenario with a kind: OPERATION, SERVICE, ASSEMBLY or TRANSPORT.
   Service is a different activity from operation and the distinction matters.
   For each scenario state its SYSTEM BOUNDARY as what is inside it and what is
   outside it. Naming the product is not a boundary. The later stage has to know
   where a load may be reacted, and it can only react a load against something
   the boundary places outside the product - a surface it stands on, a structure
   it is fixed to, a body it grips. A boundary that omits the outside leaves
   every load with nowhere to go.
7. Record every actor and what it must reach or operate.
8. Record what the text deliberately leaves free, and what is genuinely
   ambiguous.

RESPONSE SCHEMA
Return a single JSON object with exactly these seven keys, each holding a list.
A list may be empty - an empty list is a value, and means "there are none of
these", which is a different statement from omitting the key. Every field is
required unless marked optional. Every id is a string in the format shown.

  source_clauses[]  id "SRC-0001", verbatim, locator, quantity_kinds[],
                    directionality
  requirements[]    id "REQ-0001", statement_verbatim, kind, verification_kind,
                    observable_verbatim, source_locator, quantity_class
  scenarios[]       id "SCN-0001", name, kind, system_boundary, actors[],
                    environment
  actors[]          id "ACT-0001", name, must_reach[]
  freedoms[]        id "FRE-0001", decision, why_free
  ambiguities[]     id "AMB-0001", statement, conflicting_clauses[],
                    resolvable_when, block_scopes[] (optional)
  assumptions[]     id "ASM-0001", statement, why, would_be_invalidated_by

No required field may be null. Where the answer is "there are none", use an
empty list for a list field and the string "none" for a text field. A null is
not an answer; an empty list is.

REFERENCES BETWEEN ITEMS
Every field below holds ids of items YOU emit in this same response, in the
exact id format shown above. A reference to an id you did not emit, or to an
item of the wrong kind, is an error.

  requirements[].source_locator      the `locator` of one of your source_clauses
  scenarios[].actors                 actor ids, "ACT-0001"
  ambiguities[].conflicting_clauses  source clause ids, "SRC-0001" - the CLAUSES
                                     whose wording conflicts, never requirement
                                     ids; [] if the ambiguity comes from silence
                                     rather than from two clauses disagreeing

PERMITTED VALUES
Three different fields are called `kind`. They do not share a vocabulary, and a
value from one is never valid in another.
  requirement kind        FUNCTIONAL | USABILITY | PROCESS
  verification_kind       STRUCTURAL | KINEMATIC | QUANTITATIVE
  quantity_class          MAGNITUDE | BAND | COMPARATIVE | NONE
  scenario kind           OPERATION | SERVICE | ASSEMBLY | TRANSPORT
  system_boundary         a sentence naming what is inside and what is outside
  quantity_kinds          the kinds of quantity the clause mentions, such as
                          length, mass, count, force, time; [] if it states none
  directionality          the direction the clause states, such as vertical,
                          lateral, downward, bidirectional; "none" if it states
                          no direction
  source_locator          the `locator` of one of the source_clauses you emit
  statement_verbatim      wording taken from the request, not paraphrased

REQUEST
-------
{request}
"""


class S01RequirementCapture(Stage):
    stage_id = "s01"
    purpose = "convert a raw product request into typed requirements and context"

    def prompt(self, inputs: Dict[str, Any]) -> str:
        return PROMPT.format(request=inputs["request_text"])

    # ------------------------------------------------------------ operations
    def to_operations(self, parsed: Dict[str, Any]) -> List[Op]:
        parsed = {k: v for k, v in parsed.items() if not k.startswith("_")}
        ops: List[Op] = []
        prov = "s01:extraction"
        for c in parsed.get("source_clauses", []):
            ops.append(Op("CREATE", "SourceClause", c["id"], {
                "verbatim": c["verbatim"], "locator": c["locator"],
                "quantity_kinds": c.get("quantity_kinds", []),
                "directionality": c.get("directionality", "none")}, prov))
        for a in parsed.get("actors", []):
            ops.append(Op("CREATE", "Actor", a["id"], {
                "name": a["name"], "must_reach": a.get("must_reach", [])}, prov))
        for s in parsed.get("scenarios", []):
            ops.append(Op("CREATE", "Scenario", s["id"], {
                "name": s["name"], "kind": s["kind"],
                "system_boundary": s["system_boundary"],
                "actors": s.get("actors", []), "environment": s.get("environment", "")}, prov))
        for r in parsed.get("requirements", []):
            ops.append(Op("CREATE", "Requirement", r["id"], {
                "statement_verbatim": r["statement_verbatim"], "kind": r["kind"],
                "verification_kind": r["verification_kind"],
                "observable_verbatim": r["observable_verbatim"],
                "source_locator": r["source_locator"],
                "quantity_class": r["quantity_class"]}, prov))
        for f in parsed.get("freedoms", []):
            ops.append(Op("CREATE", "Freedom", f["id"], {
                "decision": f["decision"], "why_free": f["why_free"]}, prov))
        for a in parsed.get("ambiguities", []):
            ops.append(Op("CREATE", "Ambiguity", a["id"], {
                "statement": a["statement"],
                "conflicting_clauses": a.get("conflicting_clauses", []),
                "resolvable_when": a["resolvable_when"],
                "block_scopes": a.get("block_scopes", [])}, prov))
        for a in parsed.get("assumptions", []):
            ops.append(Op("CREATE", "Assumption", a["id"], {
                "statement": a["statement"], "inferred_by_stage": "s01",
                "why": a["why"],
                "would_be_invalidated_by": a["would_be_invalidated_by"]}, prov))
        return ops

    # ---------------------------------------------------------- completeness
    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        if not parsed.get("requirements"):
            out.append("no requirements captured")
        if not parsed.get("scenarios"):
            out.append("no scenarios captured")
        for r in parsed.get("requirements", []):
            if r.get("quantity_class") not in QUANTITY_CLASSES:
                out.append("requirement %s has no valid quantity_class" % r.get("id"))
        for s in parsed.get("scenarios", []):
            if s.get("kind") not in SCENARIO_KINDS:
                out.append("scenario %s has no valid kind" % s.get("id"))
        return out


# ------------------------------------------------------------- s01 checks
def sharpening_check(state, request_text: str) -> List[str]:
    """S01-C2. No numeral in a requirement that is absent from the source.

    The one S01 failure mode that a machine can catch, so it is caught here and
    not left to review.
    """
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?", request_text))
    problems = []
    for r in state.family("Requirement"):
        for n in re.findall(r"\d+(?:\.\d+)?", r.get("statement_verbatim", "")):
            if n not in source_numbers:
                problems.append("SHARPENING: %s introduces %s" % (r["entity_id"], n))
    return problems


def locator_check(state) -> List[str]:
    """S01-C1. Every requirement resolves to a captured clause."""
    known = {c["entity_id"] for c in state.family("SourceClause")}
    known |= {c.get("locator") for c in state.family("SourceClause")}
    return ["UNRESOLVED_LOCATOR: %s -> %s" % (r["entity_id"], r.get("source_locator"))
            for r in state.family("Requirement")
            if r.get("source_locator") not in known]


def mechanism_leakage_check(state, request_text: str) -> List[str]:
    """S01 must name no mechanism THAT THE SOURCE DID NOT NAME.

    Two corrections from the first evaluation of this window:

    * Source vocabulary is not leakage. A request that itself names a mechanism -
      "a hand crank", "a lever" - makes a requirement carrying that word faithful
      rather than inventive. Any token present in the source is exempt.
    * Decomposing family names into words made the check flag ordinary function
      vocabulary - support, hold, turn, energy, retaining - and it flagged three
      cases that were all correct. Only DISTINCTIVE mechanism nouns count.
    """
    source = request_text.lower()
    problems = []
    for r in state.family("Requirement"):
        text = (r.get("statement_verbatim", "") + " " +
                r.get("observable_verbatim", "")).lower()
        for token in DISTINCTIVE_MECHANISM_TOKENS:
            if re.search(r"\b%s\b" % re.escape(token), text) and token not in source:
                problems.append("MECHANISM_LEAK: %s mentions %r, absent from the source"
                                % (r["entity_id"], token))
    return problems
