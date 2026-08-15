"""WHAT THE METRICS DO NOT SAY - a reviewer's opinion, and nothing more.

S7-D. The first model call after the deterministic substrate, and the whole of
its job is the question no registered metric can answer: what would a competent
engineer looking at these already-eligible candidates want a human to know?

IT DECIDES NOTHING. Everything it writes is ASSURANCE - considered by a later
decision, never a premise of one. A deterministic function writing
`evidence_status: SUPPORTED_BY_STATE` beside a model's sentence does not make the
sentence engineering truth; the status says how well the concern is supported and
says nothing else. No stage after this one may treat an advisory's reasoning as a
fact because the record exists.

FIVE THINGS THE PRODUCER OWNS, SO THE MODEL CANNOT

    THE POPULATION. `candidates` is copied from the current CandidateComparison.
    A reviewer recommending a candidate nobody may choose has not given an
    opinion - it has given a malformed one, and the response is refused rather
    than trimmed. Trimming would silently answer a different question.

    THE ALIGNMENT. Whether the recommendation agrees with the deterministic
    frontier is computed from the comparison's own outcome, not asked of the
    model. A reviewer saying "I agree with the metrics" is a claim about the
    metrics, and the metrics already said what they said.

    THE EVIDENCE STRENGTH, downward only. A concern claiming state support with
    no valid current reference becomes PLAUSIBLE_NOT_ESTABLISHED. It is never
    raised the other way: refs happening to resolve is not the same fact as those
    refs supporting the claim, and only the reviewer can say that.

    WHAT MAY BE CITED. A reference the reviewed view did not contain is dropped
    before it can enter state. An invented id resolves to nothing and would make
    a fabricated citation look like provenance.

    THE DEPENDENCY SET. A deterministic stage knows which fields it computed
    from; a model can use anything it was shown. So the premise set is the EXACT
    provider exposure - every entity serialized into the payload this call was
    made with - and not the subset the model chose to cite. Those answer two
    different questions and only one of them is about currentness.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from ..state.patch import Op
from .base import Stage

#: Everything this pass writes is written AS `selection`. The pass is a consumer
#: responsibility - a second view of one owner, exactly as s03a/s03b are - and it
#: exists separately because the deterministic comparison is its INPUT: making
#: CandidateComparison a required premise of the `selection` view would demand
#: the entity before the pass that creates it could run.
PASS_ID = "selection_advisory"

PREFER_CANDIDATE, NO_CLEAR_PREFERENCE = "PREFER_CANDIDATE", "NO_CLEAR_PREFERENCE"
RECOMMENDATIONS = (PREFER_CANDIDATE, NO_CLEAR_PREFERENCE)

ALIGNS_WITH_FRONTIER = "ALIGNS_WITH_FRONTIER"
DEPARTS_FROM_FRONTIER = "DEPARTS_FROM_FRONTIER"
NO_DETERMINISTIC_PREFERENCE = "NO_DETERMINISTIC_PREFERENCE"

IMPORTANCE = ("HIGH", "MEDIUM", "LOW")
SUPPORTED_BY_STATE = "SUPPORTED_BY_STATE"
PLAUSIBLE_NOT_ESTABLISHED = "PLAUSIBLE_NOT_ESTABLISHED"
SPECULATIVE = "SPECULATIVE"
EVIDENCE_STATUS = (SUPPORTED_BY_STATE, PLAUSIBLE_NOT_ESTABLISHED, SPECULATIVE)

#: A CLOSED SCHEMA AT EVERY LEVEL THE MODEL OWNS, not a blacklist of names
#: somebody thought of. A key outside these sets is refused wherever it appears,
#: so a field pretending to author a verdict cannot hide one object deeper than
#: the check - which is exactly where the first version left it: the top level
#: was pinned and `recommendation` was read with `.get`, so
#: `{"kind": ..., "candidate": ..., "selected_candidate": ...}` crossed the
#: boundary with the forbidden field merely ignored.
#:
#: A blacklist would have to anticipate the name. A closed key set does not.
RESPONSE_KEYS = frozenset(("recommendation", "reasoning", "sensitivity", "concerns"))
RESPONSE_OPTIONAL = frozenset(("sensitivity",))
RECOMMENDATION_KEYS = frozenset(("kind", "candidate"))
CONCERN_KEYS = frozenset(("candidate", "issue", "importance", "evidence_status",
                          "supporting_refs"))

ADVISORY_NOT_APPLICABLE = "ADVISORY_NOT_APPLICABLE"
COMPARISON_AMBIGUOUS = "COMPARISON_AMBIGUOUS"


PROMPT = """You are an ENGINEERING REVIEWER.

You are not a feasibility authority and you are not a decision maker. Whether
these candidates can work has already been established by deterministic
evaluation, and which one is committed to is a human's choice, later. Your job is
the question none of that answers:

  WHAT ENGINEERING TRADE-OFF OR DECISION-CRITICAL CONCERN IS NOT REPRESENTED BY
  THE DETERMINISTIC COMPARISON AND THE STATED PREFERENCES?

WHAT THE DESIGN ALREADY DECIDED, AND YOU MAY NOT REVISIT

1. Review ONLY the candidates named by the comparison's `candidates`. Every other
   candidate has already been excluded on established evidence, and a
   recommendation or a concern naming one is discarded in full.
2. Do not revise eligibility. Nothing you write can make a candidate eligible or
   ineligible, however serious the concern.
3. Do not recompute the metrics, and do not invent a value for one the comparison
   reports as NOT_AVAILABLE. "A has fewer parts, so prefer A" is not available to
   you when part count is not established: what you may say is that part count is
   not currently a canonical metric, and that establishing it would take evidence
   the design does not have.
4. NOT_AVAILABLE is neither good nor bad. It is a question nobody has answered.
5. Do not invent a user preference. The profile below is what the user actually
   stated; if it ranks nothing, then nothing is ranked, and saying "the user
   values compactness" would be putting words in their mouth.
6. Do not invent a measurement. No fatigue life, no load, no probability, no
   tolerance, no material property and no quantity that is not in the state you
   were given.
7. A deterministic frontier of one candidate is NOT a selection. You may prefer a
   different eligible candidate if you have an engineering reason the metrics do
   not represent - that disagreement is recorded explicitly and is exactly what a
   reviewer is for.
8. A human may disagree with you. Write for that reader.

CONCERNS, AND SAYING HONESTLY HOW WELL THEY ARE SUPPORTED

A concern is worth raising even when the design has not established it. What is
not acceptable is claiming more support than you have.

  SUPPORTED_BY_STATE          the state you were shown directly motivates this.
                              Cite the entity ids in supporting_refs. A claim
                              with no valid current reference is recorded at the
                              lower status instead.
  PLAUSIBLE_NOT_ESTABLISHED   there is a real engineering reason to care and the
                              state does not establish it. "Repeated flexure may
                              be durability-sensitive" belongs here when no
                              fatigue evidence exists.
  SPECULATIVE                 a hypothesis worth a human's attention, with little
                              or nothing behind it yet.

No concern, at any status or importance, means a candidate is infeasible,
ineligible, or in breach of a requirement. Those are decided elsewhere.
Importance says how much attention it deserves, not how much authority it has.

RESPONSE SCHEMA
Return a single JSON object. EVERY object below - this one, the recommendation
and each concern - carries exactly the keys listed for it and no others. An
extra key anywhere, at any depth, discards the whole response; so does a missing
one, and so does a value of the wrong type. Nothing is written when that happens,
so a review worth having is a review that answers in this shape.

  recommendation   object {{kind, candidate}} - both keys always present
                   kind is "PREFER_CANDIDATE" or "NO_CLEAR_PREFERENCE".
                   PREFER_CANDIDATE names a candidate from the comparison's
                   population; NO_CLEAR_PREFERENCE sets candidate to null, and
                   only null - not "", not 0, not [].
  reasoning        your engineering review, in prose. A non-empty string.
  sensitivity      optional STRING: under what change of stated priority the
                   answer would flip. OMIT THE KEY if none applies - a null is
                   not the way to say nothing.
  concerns[]       a LIST, always present, [] when you have none. Never null and
                   never the word "none". Each entry is an object with exactly
                   candidate, issue, importance, evidence_status,
                   supporting_refs.

  importance       HIGH | MEDIUM | LOW
  evidence_status  SUPPORTED_BY_STATE | PLAUSIBLE_NOT_ESTABLISHED | SPECULATIVE
  supporting_refs  a LIST of entity ids from the state below, [] where you have
                   none. A LIST EVEN FOR ONE ID: "JNT-0A" is not a reference,
                   ["JNT-0A"] is.

Do not emit a selected candidate, a score, a weighted score, an eligibility
verdict, a feasibility verdict or a hard-requirement status - not at the top
level, not inside the recommendation, and not inside a concern. Those are not
yours, and a response containing one is discarded entirely.

THE PROFILE THE USER STATED
---------------------------
{profile}

THE DETERMINISTIC COMPARISON
----------------------------
{comparison}

THE CURRENT ENGINEERING STATE
-----------------------------
{state}
"""


# =====================================================================
# reading the reviewed context
# =====================================================================
def _one_comparison(payload: Dict[str, Any]):
    """The single current CandidateComparison, or why there is not one.

    Never first-wins. Which comparison is in force is the design's to say, and
    two of them is a question rather than a tie to break.
    """
    found = [c for c in (payload.get("CandidateComparison") or [])
             if isinstance(c, dict)]
    if len(found) == 1:
        return found[0], None
    return None, ("no current deterministic comparison" if not found else
                  "%d current deterministic comparisons: %s"
                  % (len(found), ", ".join(sorted(c.get("entity_id", "?")
                                                  for c in found))))


def visible_ids(payload: Dict[str, Any]) -> List[str]:
    """Every canonical entity id the provider payload actually contains.

    THE EXPOSURE, not the citation. A deterministic stage knows which fields it
    computed from; a model can use anything it was shown, so what the advisory
    depends on is everything that reached the prompt - and an entity removed from
    the payload is not exposure and must not be counted as any.
    """
    out = set()
    for rows in payload.values():
        if not isinstance(rows, list):
            continue
        for e in rows:
            if isinstance(e, dict) and e.get("entity_id"):
                out.add(e["entity_id"])
    return sorted(out)


def comparison_alignment(comparison: Dict[str, Any], recommended) -> str:
    """Whether the reviewer agrees with what the metrics discriminated.

    Computed here rather than asked of the model, and computed from the
    comparison's OWN record: a frontier of more than one candidate means the
    deterministic evidence expressed no preference, so there is nothing for an
    advisory to align with or depart from however firm its opinion is.
    """
    frontier = [c for c in (comparison.get("frontier") or []) if isinstance(c, str)]
    if recommended is None or len(frontier) != 1:
        return NO_DETERMINISTIC_PREFERENCE
    return (ALIGNS_WITH_FRONTIER if frontier[0] == recommended
            else DEPARTS_FROM_FRONTIER)


# =====================================================================
# identity
# =====================================================================
def _digest(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def normalized(response: Dict[str, Any]) -> Dict[str, Any]:
    """The response with its concern list put in a canonical order.

    THE SAME CONCERNS IN A DIFFERENT ORDER ARE THE SAME REVIEW. Hashing the raw
    response made a reordering produce a new advisory id and, through it, new
    concern ids - a reordering looking like new engineering.

    Only ever a VALIDATED response, so it reads its keys directly. Tolerating a
    missing or mistyped one here would be a second, laxer opinion about what a
    response is, in the one place a strict boundary was supposed to settle.
    """
    out = dict(response)
    out["concerns"] = sorted(
        response["concerns"],
        key=lambda c: json.dumps(c, sort_keys=True, default=str))
    return out


def advisory_identity(comparison_id: str, response: Dict[str, Any]) -> str:
    """Content-derived, so the same review of the same comparison is one record.

    No counter. A review is an assurance artifact and there may legitimately be
    several of them over one comparison - what must not happen is two ids for one
    review, or one id for two.
    """
    return "ADV-%s" % _digest(comparison_id, normalized(response))[:12].upper()


def concern_identity(advisory_id: str, concern: Dict[str, Any]) -> str:
    """From the concern's own content, never its position in the list.

    The same set of concerns written in a different order is the same set. Using
    the index would have made a reordering look like new engineering.
    """
    return "CNC-%s" % _digest(advisory_id, concern["candidate"],
                              concern["issue"],
                              concern["evidence_status"])[:12].upper()


# =====================================================================
# the stage
# =====================================================================
class SelectionEngineeringReview(Stage):
    """The reviewer pass. One owner, a second consumer view."""

    stage_id = "selection"
    pass_id = PASS_ID
    purpose = "review what the deterministic comparison does not represent"

    # -- the prompt ----------------------------------------------------
    def prompt(self, inputs: Dict[str, Any]) -> str:
        payload = inputs[self.context_key]
        comparison, _why = _one_comparison(payload)
        profiles = payload.get("SelectionProfile") or []
        return PROMPT.format(
            profile=_render(profiles[0] if len(profiles) == 1 else profiles),
            comparison=_render(comparison),
            state=_render({fam: rows for fam, rows in sorted(payload.items())
                           if fam not in ("CandidateComparison", "SelectionProfile")}))

    # -- what this invocation rests on ---------------------------------
    def invocation_premises(self, inputs: Dict[str, Any]) -> List[str]:
        """THE EXACT PROVIDER EXPOSURE. Deliberately broader than what the model
        cited, because the model saw all of it and any of it could have shaped
        the sentence. Narrower would be a currentness claim the reviewer never
        made: a fact it read changing must cost the review its standing."""
        return visible_ids(inputs[self.context_key])

    # -- the write -----------------------------------------------------
    def to_operations(self, parsed: Dict[str, Any], inputs=None) -> List[Op]:
        payload = (inputs or {})[self.context_key]
        comparison, why = _one_comparison(payload)
        if comparison is None:
            # Unreachable through `invoke` - the view is REQUIRED_NONEMPTY on the
            # comparison, so an unready context never calls the provider. Stated
            # anyway, because a direct caller is a caller.
            raise ValueError(why)
        population = [c for c in (comparison.get("candidates") or [])
                      if isinstance(c, str)]
        # STRUCTURE FIRST, EVIDENCE SECOND, and never the two in one pass. If the
        # response is not the shape that was asked for, nothing is written at all
        # - so a malformed field can never arrive downstream disguised as a weak
        # claim.
        response = validate_response(parsed, population)
        recommendation = response["recommendation"]
        recommended = response["candidate"]
        concerns = calibrate(response["concerns"], set(visible_ids(payload)))

        # FROM THE VALIDATED RESPONSE, not the raw parse. Nothing unvalidated
        # reaches the hash, so there is no second reader of the model's JSON with
        # its own idea of what the keys are. Pre-calibration deliberately: two
        # reviews that differ only in how much support they CLAIMED are two
        # reviews, and downgrading one of them must not merge them.
        advisory_id = advisory_identity(comparison["entity_id"], response)
        # THE PRODUCER'S FIELDS. The population is the comparison's, the
        # alignment is computed from it, and neither was asked of the model.
        fields = {
            "candidates": list(population),
            "comparison": comparison["entity_id"],
            "recommendation": recommendation,
            "comparison_alignment": comparison_alignment(comparison, recommended),
            "reasoning": response["reasoning"]}
        if recommended is not None:
            # OMITTED RATHER THAN NULL. A declared reference holding None is not
            # an absent field, it is a reference to nothing - and NO_CLEAR_
            # PREFERENCE means the reviewer named nobody, not that it named
            # nothing.
            fields["recommended_candidate"] = recommended
        if response.get("sensitivity"):
            # Typed above; what is decided here is only whether an empty
            # statement is worth a field, and it is not.
            fields["sensitivity"] = response["sensitivity"]
        ops = [Op("CREATE", "SelectionAdvisory", advisory_id, fields,
                  "selection_advisory:review")]
        for concern in concerns:
            ops.append(Op("CREATE", "SelectionConcern",
                          concern_identity(advisory_id, concern),
                          dict(concern, advisory=advisory_id),
                          "selection_advisory:review",
                          premise_refs=[advisory_id]))
        return ops

    def completeness(self, parsed: Dict[str, Any], inputs: Dict[str, Any]) -> List[str]:
        return []


def _render(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=1, sort_keys=True, default=str)
    except Exception:                                               # noqa: BLE001
        return str(obj)


def _object(value: Any, allowed, what: str, optional=frozenset()) -> Dict[str, Any]:
    """A model-owned object with EXACTLY the keys it is allowed, and no others.

    Both directions. A missing required key is a response that does not say what
    it means; an extra one is a model reaching for a field somebody else owns,
    and the fact that the producer would have ignored it is not a defence - the
    next reader might not.
    """
    if not isinstance(value, dict):
        raise ValueError("%s must be an object, not %s"
                         % (what, type(value).__name__))
    extra = sorted(set(value) - allowed)
    if extra:
        raise ValueError("%s carries keys it may not author: %s"
                         % (what, ", ".join(extra)))
    missing = sorted(allowed - optional - set(value))
    if missing:
        raise ValueError("%s omits %s" % (what, ", ".join(missing)))
    return value


def _string(value: Any, what: str) -> str:
    """A string, and nothing that merely looks like one.

    No coercion: 123 is not "123" and [] is not "". A model that sent the wrong
    type sent the wrong answer, and turning it into text here would be this code
    deciding what it meant. `bool` is excluded explicitly because it is an `int`
    subclass and would otherwise pass a numeric check somewhere later.
    """
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValueError("%s must be a string, not %s"
                         % (what, type(value).__name__))
    if not value.strip():
        raise ValueError("%s is empty" % what)
    return value


def _member(value: Any, vocabulary, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValueError("%s must be a string, not %s"
                         % (what, type(value).__name__))
    if value not in vocabulary:
        raise ValueError("%s is %r; the vocabulary is %s"
                         % (what, value, list(vocabulary)))
    return value


def _ref_list(value: Any, what: str) -> List[str]:
    """A list of non-empty strings. A BARE STRING IS NOT ONE.

    Python would iterate `"JNT-0A"` character by character, so a malformed field
    became six references that resolve to nothing - and the concern was then
    DOWNGRADED for lacking support it had in fact supplied in the wrong shape.
    A schema failure laundered into an evidence finding is the worst of both:
    the model is told nothing and the record says something false about why.
    """
    if isinstance(value, str):
        raise ValueError("%s is a string; a list of ids was required, and a "
                         "string would be read one character at a time" % what)
    if not isinstance(value, list):
        raise ValueError("%s must be a list of ids, not %s"
                         % (what, type(value).__name__))
    return [_string(ref, "%s[%d]" % (what, n)) for n, ref in enumerate(value)]


def validate_response(parsed: Any, population) -> Dict[str, Any]:
    """THE ONE BOUNDARY between a model's JSON and this design's state.

    Everything structural happens here and nothing structural happens anywhere
    else, so "what can cross" is answerable by reading one function. It runs
    entirely BEFORE the evidence validator, because the two are different
    questions and conflating them is what let a malformed field arrive disguised
    as a weak claim:

        BAD SCHEMA      the response is not the shape that was asked for.
                        Nothing is written, at all.
        BAD EVIDENCE    the response is well-formed and claims more support than
                        it has. The concern is kept and its status corrected.
    """
    _object(parsed, RESPONSE_KEYS, "the response", RESPONSE_OPTIONAL)
    block = _object(parsed["recommendation"], RECOMMENDATION_KEYS,
                    "the recommendation")
    kind = _member(block["kind"], RECOMMENDATIONS, "recommendation kind")
    candidate = block["candidate"]
    if kind == NO_CLEAR_PREFERENCE:
        # EXACTLY None. `if candidate:` accepted "", 0, False, [] and {} as "no
        # candidate" - five malformed values masquerading as the one legitimate
        # way to say nothing was preferred.
        if candidate is not None:
            raise ValueError("NO_CLEAR_PREFERENCE names %r; only null means "
                             "no candidate was preferred" % (candidate,))
    else:
        _string(candidate, "the recommended candidate")
        if candidate not in population:
            raise ValueError("%s is not one of the candidates this comparison "
                             "holds (%s)" % (candidate, ", ".join(sorted(population))))
    out = {"recommendation": kind, "candidate": candidate,
           "reasoning": _string(parsed["reasoning"], "reasoning")}
    if "sensitivity" in parsed:
        # TYPE FIRST, then meaning. An absent key is "no sensitivity statement";
        # a present one of the wrong type is a malformed response, and deciding
        # which by truthiness would have accepted 0 and [] as both.
        out["sensitivity"] = _string(parsed["sensitivity"], "sensitivity")
    concerns = parsed["concerns"]
    if not isinstance(concerns, list):
        raise ValueError("concerns must be a list, not %s"
                         % type(concerns).__name__)
    out["concerns"] = [_validated_concern(c, population, n)
                       for n, c in enumerate(concerns)]
    return out


def _validated_concern(raw: Any, population, index: int) -> Dict[str, Any]:
    """One concern, structurally. ONE MALFORMED CONCERN FAILS THE RESPONSE.

    Writing the valid ones and dropping the rest would publish a review the model
    did not give - and the reader would have no way to know a concern had been
    silently removed.
    """
    what = "concern %d" % (index + 1)
    concern = _object(raw, CONCERN_KEYS, what)
    candidate = _string(concern["candidate"], "%s candidate" % what)
    if candidate not in population:
        raise ValueError("%s names %s, which this comparison does not hold"
                         % (what, candidate))
    return {"candidate": candidate,
            "issue": _string(concern["issue"], "%s issue" % what),
            "importance": _member(concern["importance"], IMPORTANCE,
                                  "%s importance" % what),
            "evidence_status": _member(concern["evidence_status"], EVIDENCE_STATUS,
                                       "%s evidence_status" % what),
            "supporting_refs": _ref_list(concern["supporting_refs"],
                                         "%s supporting_refs" % what)}


def calibrate(concerns, visible) -> List[Dict[str, Any]]:
    """The EVIDENCE half, over already-structurally-valid concerns.

    Preserve or downgrade, never upgrade. Sorted by content so that the same set
    of concerns in a different order produces the same records - a reordering is
    not new engineering.
    """
    out = []
    for concern in concerns:
        # ONLY WHAT THE REVIEWER ACTUALLY SAW. An id that was not in the payload
        # resolves to nothing, and storing it would make a fabricated citation
        # look like provenance.
        refs = sorted({r for r in concern["supporting_refs"] if r in visible})
        status, note = concern["evidence_status"], None
        if status == SUPPORTED_BY_STATE and not refs:
            # DOWNGRADED, NEVER FAILED. Overclaiming how well a concern is
            # supported is not a reason to lose the concern - the reviewer may be
            # right that it matters. It is a reason to record what it actually
            # rests on, which is judgement rather than state.
            status = PLAUSIBLE_NOT_ESTABLISHED
            note = ("the review claimed state support and supplied no reference "
                    "that is current in the state it was shown")
        record = dict(concern, evidence_status=status, supporting_refs=refs)
        if note:
            record["evidence_note"] = note
        out.append(record)
    return sorted(out, key=lambda c: (c["candidate"], c["issue"],
                                      c["evidence_status"]))
