"""WHICH ANSWER IS CURRENT, AND WHAT MAKES A NEW ONE.

S7-F. Lifecycle only: nothing here knows what a feasibility domain is, what a
metric means or why a candidate is eligible. It answers two questions for any
deterministic responsibility that has to be able to answer again -

    WHICH record is the current answer at this logical address?
    IS the answer that stands still an answer to what the design now says?

- and it answers them the same way for every caller, so a comparison and a
feasibility assessment cannot end up with two different ideas of what
"unchanged" means.

AN ADDRESS IS NOT AN ID. The address is what the question is about - this
candidate's mobility, this candidate against that requirement, the comparison
under this profile. The id says which ANSWER to it is being read. Before S7-F
they were the same string, which was sufficient exactly once: a re-evaluation
over revised evidence had nowhere to go, because the only id its answer could
have was taken by the answer it replaces.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from ..state.patch import Op

CURRENT_MULTIPLICITY = "CURRENT_MULTIPLICITY"


def _current(state, family: str, **address) -> List[Dict[str, Any]]:
    """Every CURRENT record at one logical address. Never ordered, never picked.

    `records[-1]`, `max(id)` and "the latest hash" are all the same mistake:
    they answer "which one was written last", and the question is "which one is
    true now". Standing is the only thing that decides, and two standing answers
    to one question is a lifecycle defect rather than a tie to break.
    """
    return [r for r in state.standing(family)
            if all(r.get(k) == v for k, v in address.items())]


def current_domain_assessment(state, candidate: str, domain: str):
    found = _current(state, "FeasibilityDomainAssessment", candidate=candidate,
                     domain=domain)
    return found[0] if len(found) == 1 else None


def current_assessment(state, candidate: str):
    """The one current mechanical feasibility answer for this candidate."""
    found = _current(state, "MechanicalFeasibilityAssessment", candidate=candidate)
    return found[0] if len(found) == 1 else None


def current_compliance(state, candidate: str, constraint: str):
    found = _current(state, "HardRequirementCompliance", candidate=candidate,
                     constraint=constraint)
    return found[0] if len(found) == 1 else None


def _grouped(state, family: str, candidate: str, by: str) -> Dict[Any, int]:
    counts: Dict[Any, int] = {}
    for record in state.standing(family):
        if record.get("candidate") == candidate:
            counts[record.get(by)] = counts.get(record.get(by), 0) + 1
    return counts


def multiplicity(state, candidate: str) -> List[str]:
    """Addresses this candidate currently has more than one answer at.

    Counted from the records themselves rather than from a list of what the
    addresses are: a domain nobody thought to enumerate is still an address, and
    a check that only looks where it expects trouble finds only the trouble it
    expected.
    """
    out = ["%d current assessments of %s for %s"
           % (n, domain, candidate)
           for domain, n in sorted(_grouped(
               state, "FeasibilityDomainAssessment", candidate, "domain").items())
           if n > 1]
    standing = [r for r in state.standing("MechanicalFeasibilityAssessment")
                if r.get("candidate") == candidate]
    if len(standing) > 1:
        out.append("%d current feasibility assessments for %s: %s"
                   % (len(standing), candidate,
                      ", ".join(sorted(r["entity_id"] for r in standing))))
    out += ["%d current compliance records for %s against %s"
            % (n, candidate, constraint)
            for constraint, n in sorted(_grouped(
                state, "HardRequirementCompliance", candidate, "constraint").items())
            if n > 1]
    return out


def evaluation_basis(state, premises) -> str:
    """WHICH VERSION OF THE EVIDENCE this answer was reached over.

    Not the verdict. Two PASS verdicts over two different arrangements are two
    evaluations, and only one of them is about the geometry the design currently
    has - so "the answer did not change" is never on its own a reason to leave
    yesterday's evaluation standing.

    Built from the lifecycle digest of each premise, which says whether the
    record is the same revision and nothing about what it means. One candidate's
    envelope moving cannot change another candidate's basis, which a whole-state
    hash could not have avoided.
    """
    revisions = {p: state.entity_revision_digest(p) for p in sorted(set(premises))}
    return hashlib.sha256(
        json.dumps(revisions, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _engineering(record: Dict[str, Any]) -> Dict[str, Any]:
    """The authored content of a record, without its id or its bookkeeping."""
    return {k: v for k, v in record.items()
            if not k.startswith("_") and k not in ("entity_id", "evaluation_basis")}


def revision_id(address_id: str, basis: str, fields: Dict[str, Any],
                replaced: Optional[str]) -> str:
    """A new id for a re-evaluation at an address that already has an answer.

    Derived from the address, the evidence revision, the answer and the record
    it replaces - so the same transition is always the same id, and a design
    that moves away from a state and back to it does not collide with its own
    history. No counter, no clock, no ordinal.
    """
    payload = json.dumps([address_id, basis, fields, replaced or ""],
                         sort_keys=True, separators=(",", ":"), default=str)
    return "%s-R%s" % (address_id,
                       hashlib.sha256(payload.encode()).hexdigest()[:8].upper())


DEFAULT_REPLACED_REASON = ("re-evaluated over the current evidence; this answer "
                           "was reached over a revision the design no longer has")


def address_operations(state, family: str, address_id: str,
                       fields: Dict[str, Any], premises, prov: str, current,
                       basis_over=None,
                       replaced_reason: str = DEFAULT_REPLACED_REASON):
    """The operations one logical address needs, which is usually none.

    SHARED WITH `selection`, deliberately. A comparison and a feasibility
    assessment are different engineering questions and their lifecycle is the
    same question: is the current answer still an answer to what the design now
    says? One implementation of that means one behaviour, and no second opinion
    about what "unchanged" means.

    THREE CASES, AND THE FIRST IS THE COMMON ONE:

        the current answer was reached over exactly this evidence and says the
        same thing            -> nothing is written, so reconciling twice is
                                 reconciling once

        a current answer exists over different evidence, or says something else
                              -> it is INVALIDATED with a reason and a new
                                 current answer is written beside it. Nothing is
                                 deleted and no validity is assigned by hand

        no current answer exists - there never was one, or the one there was has
        already lost authority
                              -> the new answer is written, and the old record
                                 keeps its id and its history
    """
    # THE EVIDENCE, NOT THE SIBLING ANSWERS. `basis_over` exists because the
    # feasibility assessment names the domain records this same act is writing:
    # they do not exist yet when the basis is computed and they do a moment
    # later, so including them would make an unchanged design produce a new
    # revision on every reconcile. What the answer was reached OVER is the
    # upstream evidence; the sibling records are what it was reached WITH.
    basis = evaluation_basis(state, premises if basis_over is None else basis_over)
    stored = dict(fields, evaluation_basis=basis)
    if current is not None:
        if (current.get("evaluation_basis") == basis
                and _engineering(current) == _engineering(stored)):
            return [], current["entity_id"]
        eid = revision_id(address_id, basis, fields, current["entity_id"])
        return ([Op("INVALIDATE", family, current["entity_id"], {}, prov,
                    reason=replaced_reason),
                 Op("CREATE", family, eid, stored, prov,
                    premise_refs=sorted(set(premises)))], eid)
    eid = address_id
    if state.has_entity(eid):
        eid = revision_id(address_id, basis, fields, None)
    return [Op("CREATE", family, eid, stored, prov,
               premise_refs=sorted(set(premises)))], eid
