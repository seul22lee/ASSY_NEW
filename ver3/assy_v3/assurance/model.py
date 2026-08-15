"""WHAT A CHECK IS ALLOWED TO CLAIM, and the vocabulary it claims it in.

S-8 / U-9. Two declarations decide everything about a result:

    HOW FAR THE CHECKER STANDS FROM THE WRITER   independence degree
    WHAT A PASS IS ENTITLED TO ASSERT            claim class

Both are closed sets. A check that declares a value outside them is a registry
error rather than a default, because the whole failure this unit removes is a
check quietly claiming more than its position entitles it to.

THE ONE RULE EVERYTHING ELSE PROTECTS

    Only an ENGINEERING_CONSEQUENCE result, from a check that compared premises
    two different producers authored, may raise a property to
    ENGINEERING_ESTABLISHED - and it raises exactly the property it names.

A count is not a conclusion. A value surviving transport is not a value being
right. Every claim tracing to a resolvable premise is not the claim being true.
Those three are BOOKKEEPING, FIDELITY and PROVENANCE_INTEGRITY, and none of them
establishes anything, however many of them pass.

ESTABLISHMENT IS PROPERTY-LOCAL. It belongs to one named property of one named
entity, and it is never inherited from a sibling property, another candidate, a
stage, a patch, a run, a badge, execution success, contract completeness or
evidence maturity. There is no "stage established" and no "design established",
because there is nothing those phrases could mean that is not a collapse.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# =====================================================================
# A1 - the two declared vocabularies
# =====================================================================
#: How far the checker stands from the writer.
STRUCTURAL = "STRUCTURAL"
PREMISE = "PREMISE"
EXTERNAL = "EXTERNAL"
INDEPENDENCE_DEGREES = (STRUCTURAL, PREMISE, EXTERNAL)

#: What a passing result is entitled to assert.
BOOKKEEPING = "BOOKKEEPING"
FIDELITY = "FIDELITY"
PROVENANCE_INTEGRITY = "PROVENANCE_INTEGRITY"
ENGINEERING_CONSEQUENCE = "ENGINEERING_CONSEQUENCE"
CLAIM_CLASSES = (BOOKKEEPING, FIDELITY, PROVENANCE_INTEGRITY,
                 ENGINEERING_CONSEQUENCE)

#: STATUS_SEMANTICS.evaluation_outcomes. Not re-invented here: a second spelling
#: of PASS would be a second vocabulary, which is the collapse this file exists
#: to prevent.
PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT_VERIFIED"
NOT_EVALUABLE = "NOT_EVALUABLE"
UNSUPPORTED = "UNSUPPORTED"
INDETERMINATE = "INDETERMINATE"
OUTCOMES = (PASS, FAIL, NOT_VERIFIED, NOT_EVALUABLE, UNSUPPORTED, INDETERMINATE)

#: STATUS_SEMANTICS.status_constructs.ENGINEERING_ESTABLISHMENT.
ENGINEERING_ESTABLISHED = "ENGINEERING_ESTABLISHED"
NOT_ESTABLISHED = "NOT_ESTABLISHED"
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
ESTABLISHMENT = (ENGINEERING_ESTABLISHED, NOT_ESTABLISHED, NOT_VERIFIED,
                 EVIDENCE_INCOMPLETE)

#: The two findings M-9 records as having no emitter. FALSE_ACCEPTANCE is the
#: most serious defect class in this repository - a run claiming something it had
#: not earned - and until now nothing could report one.
FALSE_ACCEPTANCE = "FALSE_ACCEPTANCE"
SAFE_REJECTION = "SAFE_REJECTION"

#: The distinction that may never be merged (§14, and the taxonomy U-3 exists
#: for): upstream never established it, versus we failed to carry it.
UPSTREAM_INSUFFICIENCY = "UPSTREAM_INSUFFICIENCY"
PROJECTION_FAILURE = "PROJECTION_FAILURE"


class RegistryError(ValueError):
    """A check that declares something outside the closed vocabularies."""


# =====================================================================
# what a check says
# =====================================================================
@dataclass(frozen=True)
class Finding:
    """One property, one outcome, and the entities it was read from.

    `property_id` names the PROPERTY, not the check and not the stage: a
    capability that examines nine joints produces nine properties, and one of
    them failing says nothing about the other eight.
    """

    property_id: str
    outcome: str
    detail: str
    refs: Tuple[str, ...] = ()
    code: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        out = {"property_id": self.property_id, "outcome": self.outcome,
               "detail": self.detail, "refs": list(self.refs)}
        if self.code:
            out["code"] = self.code
        return out


@dataclass(frozen=True)
class Check:
    """A declaration. The function is only how the declaration is evaluated."""

    check_id: str
    independence: str
    claim_class: str
    #: What the properties this check produces are ABOUT, in one line.
    property_scope: str
    #: The families whose committed content it reads, and who authored each.
    inputs: Tuple[str, ...]
    #: The producing stages whose premises it compares. Two different ones is
    #: what PREMISE independence MEANS, and the registry test asserts it.
    authors: Tuple[str, ...]
    fn: Callable[[Any], List[Finding]] = field(repr=False, default=None)

    def declaration(self) -> Dict[str, Any]:
        return {"check_id": self.check_id, "independence": self.independence,
                "claim_class": self.claim_class,
                "property_scope": self.property_scope,
                "inputs": list(self.inputs), "authors": list(self.authors)}

    def validate(self) -> None:
        if self.independence not in INDEPENDENCE_DEGREES:
            raise RegistryError("%s declares independence %r; the vocabulary is %s"
                                % (self.check_id, self.independence,
                                   list(INDEPENDENCE_DEGREES)))
        if self.claim_class not in CLAIM_CLASSES:
            raise RegistryError("%s declares claim class %r; the vocabulary is %s"
                                % (self.check_id, self.claim_class,
                                   list(CLAIM_CLASSES)))
        for what in ("property_scope", "inputs", "authors"):
            if not getattr(self, what):
                raise RegistryError("%s declares no %s" % (self.check_id, what))
        if self.claim_class == ENGINEERING_CONSEQUENCE and len(set(self.authors)) < 2 \
                and self.independence != EXTERNAL:
            # AN ENGINEERING CONSEQUENCE IS A DISAGREEMENT BETWEEN TWO AUTHORS.
            # One author checking itself can only find what it already knew, and
            # a check like that establishing a property is the self-fulfilling
            # result R-6 warns about. EXTERNAL is the one exception, and it earns
            # it differently: the precondition is recomputed by a reader that is
            # not the actor being judged.
            raise RegistryError(
                "%s claims ENGINEERING_CONSEQUENCE from one author (%s)"
                % (self.check_id, list(self.authors)))
        if self.fn is None:
            raise RegistryError("%s declares no evaluation" % self.check_id)


@dataclass(frozen=True)
class CheckResult:
    """What one check found, and what its findings are entitled to establish."""

    check_id: str
    independence: str
    claim_class: str
    findings: Tuple[Finding, ...]
    #: The revisions of the entities this evaluation actually read. Currentness
    #: is answered per check rather than by whole-state equality: a result is
    #: current for as long as what it READ is what the design still says.
    premise_digest: str

    @property
    def outcome(self) -> str:
        """Worst-first over the findings. NOT an aggregate across constructs -
        every finding here belongs to one check and one claim class."""
        for worst in (FAIL, INDETERMINATE, NOT_EVALUABLE, UNSUPPORTED,
                      NOT_VERIFIED):
            if any(f.outcome == worst for f in self.findings):
                return worst
        return PASS

    def establishment(self) -> Dict[str, str]:
        """property id -> establishment status. THE ONE PLACE IT IS DECIDED.

        A property is ENGINEERING_ESTABLISHED only when its own finding passed,
        in a check that compared two independently authored premises and declared
        ENGINEERING_CONSEQUENCE. Everything else is NOT_ESTABLISHED, which is a
        legitimate permanent state and not a failure - and a FAIL is
        NOT_ESTABLISHED too, because establishment says a property HOLDS, never
        that it was looked at.
        """
        out: Dict[str, str] = {}
        for finding in self.findings:
            if self.claim_class != ENGINEERING_CONSEQUENCE:
                out[finding.property_id] = NOT_ESTABLISHED
            elif finding.outcome == PASS:
                out[finding.property_id] = ENGINEERING_ESTABLISHED
            elif finding.outcome in (NOT_VERIFIED, NOT_EVALUABLE, UNSUPPORTED):
                out[finding.property_id] = NOT_VERIFIED
            elif finding.outcome == INDETERMINATE:
                out[finding.property_id] = EVIDENCE_INCOMPLETE
            else:
                out[finding.property_id] = NOT_ESTABLISHED
        return out

    def as_dict(self) -> Dict[str, Any]:
        return {"check_id": self.check_id, "independence": self.independence,
                "claim_class": self.claim_class, "outcome": self.outcome,
                "premise_digest": self.premise_digest,
                "findings": [f.as_dict() for f in self.findings],
                "establishment": self.establishment()}


@dataclass(frozen=True)
class AssuranceSnapshot:
    """AN IMMUTABLE REPORT BOUND TO THE STATE IT READ. Never stored in it.

    A2. Writing results into DesignState would make the act of assessing the
    design change the design being assessed: `state_hash` would move, a second
    run would see something the first did not, and every "reconciling an
    unchanged design writes nothing" property in S7-F would become false. The
    package contract already requires that re-projecting an unchanged state give
    a byte-identical result, which is what this is.
    """

    state_hash: str
    results: Tuple[CheckResult, ...]

    def establishment(self) -> Dict[str, str]:
        """Every property this snapshot judged, and what it is entitled to say.

        Flat and per-property on purpose. There is no per-stage roll-up and no
        design-wide badge, because establishment is not a quantity and a summary
        of it would be exactly the collapse S8-I9 forbids.
        """
        out: Dict[str, str] = {}
        for result in self.results:
            out.update(result.establishment())
        return dict(sorted(out.items()))

    def established(self) -> List[str]:
        return sorted(p for p, s in self.establishment().items()
                      if s == ENGINEERING_ESTABLISHED)

    def findings(self, outcome: Optional[str] = None) -> List[Finding]:
        return [f for r in self.results for f in r.findings
                if outcome is None or f.outcome == outcome]

    def is_current(self, state) -> bool:
        """Whether this snapshot still describes the design in front of it."""
        return self.state_hash == state.state_hash()

    def as_dict(self) -> Dict[str, Any]:
        return {"state_hash": self.state_hash,
                "results": [r.as_dict() for r in self.results],
                "establishment": self.establishment()}

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"),
                       default=str).encode()).hexdigest()
