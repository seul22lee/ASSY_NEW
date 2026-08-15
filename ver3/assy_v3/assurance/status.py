"""FOUR QUESTIONS, FOUR ANSWERS, AND NO NUMBER THAT MIXES THEM.

S-8 / U-9. STATUS_SEMANTICS separates four constructs and the tools collapsed
them: one badge that turned any engineering finding into a downgraded execution
status, and one unweighted index that averaged contract completeness together
with engineering care.

    EXECUTION                 did the machinery run?
    CONTRACT_COMPLETENESS     is every required output present and typed?
    EVIDENCE_MATURITY         what class of evidence is behind ONE VALUE?
    ENGINEERING_ESTABLISHMENT did an independent check find ONE PROPERTY to hold?

This module projects a run into those four, side by side, and refuses to reduce
them. There is no overall status here, and the absence is the feature: a design
whose provider timed out and a design whose geometry is wrong are two different
situations, and any single symbol that can represent both will eventually be read
as the same thing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .model import (ENGINEERING_ESTABLISHED, EVIDENCE_INCOMPLETE, FAIL,
                    NOT_ESTABLISHED, NOT_VERIFIED)

EXECUTION = "EXECUTION"
CONTRACT_COMPLETENESS = "CONTRACT_COMPLETENESS"
EVIDENCE_MATURITY = "EVIDENCE_MATURITY"
ENGINEERING_ESTABLISHMENT = "ENGINEERING_ESTABLISHMENT"
CONSTRUCTS = (EXECUTION, CONTRACT_COMPLETENESS, EVIDENCE_MATURITY,
              ENGINEERING_ESTABLISHMENT)

#: Every term, and the one construct it belongs to. A term in two constructs is
#: how "PROVISIONAL" becomes an establishment status and how SUCCESS becomes a
#: statement about a design.
TERMS: Dict[str, str] = {
    "SUCCESS": EXECUTION, "PROVIDER_RATE_LIMIT": EXECUTION,
    "PROVIDER_QUOTA_EXHAUSTED": EXECUTION, "PROVIDER_UNAVAILABLE": EXECUTION,
    "PROVIDER_TIMEOUT": EXECUTION, "RESPONSE_TRUNCATED": EXECUTION,
    "RESPONSE_PARSE_FAILURE": EXECUTION, "SCHEMA_FAILURE": EXECUTION,
    "CONTRACT_INCOMPLETE": EXECUTION, "MODEL_CAPABILITY_FAILURE": EXECUTION,
    "SAFE_REJECTION": EXECUTION, "CONSUMER_CONTEXT_INSUFFICIENT": EXECUTION,
    "FALSE_ACCEPTANCE": EXECUTION,
    "COMPLETE": CONTRACT_COMPLETENESS, "INCOMPLETE": CONTRACT_COMPLETENESS,
    "SYMBOLIC": EVIDENCE_MATURITY, "PROVISIONAL": EVIDENCE_MATURITY,
    "AUTHORITATIVE": EVIDENCE_MATURITY, "FROZEN": EVIDENCE_MATURITY,
    "ENGINEERING_ESTABLISHED": ENGINEERING_ESTABLISHMENT,
    "NOT_ESTABLISHED": ENGINEERING_ESTABLISHMENT,
    "EVIDENCE_INCOMPLETE": ENGINEERING_ESTABLISHMENT,
}


def construct_of(term: str) -> Optional[str]:
    """Which construct a term belongs to, or None if it belongs to none.

    NOT_VERIFIED deliberately returns None: STATUS_SEMANTICS lists it under both
    evaluation outcomes and establishment, and a lookup that picked one would be
    this module deciding a contract question.
    """
    return TERMS.get(term)


def report(snapshot, execution: Optional[Sequence[Dict[str, Any]]] = None,
           completeness: Optional[Sequence[Dict[str, Any]]] = None,
           maturity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The four constructs, side by side, from one assurance snapshot and the
    run facts a caller already has.

    NOTHING IS COMBINED. Execution statuses are counted as they were recorded;
    an engineering finding does not touch them, and an execution failure
    contributes no engineering claim. The establishment section lists properties,
    never a fraction: "7 of 9 established" invites a percentage, and a percentage
    of establishment is a design badge with a decimal point.
    """
    execution = list(execution or [])
    findings = snapshot.findings(FAIL)
    establishment = snapshot.establishment()
    out = {
        EXECUTION: {
            "attempts": len(execution),
            "by_status": _count(str(a.get("execution_status")) for a in execution),
            "note": "the machinery, never the design; an engineering finding "
                    "does not appear here",
        },
        CONTRACT_COMPLETENESS: {
            "records": list(completeness or []),
            "note": "required outputs present and typed; says nothing about "
                    "whether a value is right",
        },
        EVIDENCE_MATURITY: {
            "values": dict(maturity or {}),
            "note": "the class of evidence behind one value; never an "
                    "establishment status",
        },
        ENGINEERING_ESTABLISHMENT: {
            "established": snapshot.established(),
            "not_established": sorted(p for p, s in establishment.items()
                                      if s == NOT_ESTABLISHED),
            "not_verified": sorted(p for p, s in establishment.items()
                                   if s == NOT_VERIFIED),
            "evidence_incomplete": sorted(p for p, s in establishment.items()
                                          if s == EVIDENCE_INCOMPLETE),
            "findings": [f.as_dict() for f in findings],
            "state_hash": snapshot.state_hash,
            "note": "one property at a time; establishment is never inherited "
                    "and is never a fraction",
        },
    }
    return out


def _count(values) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))
