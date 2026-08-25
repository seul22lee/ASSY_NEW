"""UNIT G. Engineering failure as typed, owned evidence.

Workable CAD exposes failures, and a failure is only useful if it says WHAT
failed and WHOSE decision it is to change. A string in a problems list says the
first; this says both. Nothing here interprets a finding as mechanism
infeasibility: an embodiment-owned contradiction is evidence for a bounded s05
revision, an architecture-owned one is routed to s03/s04, and a capability gap
is s07's to report - never anyone's to paper over.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

#: The closed vocabulary of what can be found. Each entry names ONE kind of
#: contradiction between the artifact and what the design committed to.
CONSTRUCTION_INVALID = "CONSTRUCTION_INVALID"          # a solid did not build / is not valid
MATING_AXES_INCONSISTENT = "MATING_AXES_INCONSISTENT"  # the two sides of a joint disagree
CLEARANCE_NEGATIVE = "CLEARANCE_NEGATIVE"              # a settled clearance has the wrong sign
BODY_INTERFERENCE = "BODY_INTERFERENCE"                # two solids share volume where they may not
MATING_NOT_REALIZED = "MATING_NOT_REALIZED"            # an intended contact/clearance is not there
TRAVEL_BLOCKED = "TRAVEL_BLOCKED"                      # interference somewhere along a transition
ASSEMBLY_BLOCKED = "ASSEMBLY_BLOCKED"                  # bodies cannot be posed together
FEATURE_OUTSIDE_REGION = "FEATURE_OUTSIDE_REGION"      # settled material inside a reserved region
UNSETTLED_CRITICAL_PARAMETER = "UNSETTLED_CRITICAL_PARAMETER"
UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"        # the stack cannot evaluate this yet
EMBODIMENT_INCOMPLETE = "EMBODIMENT_INCOMPLETE"        # the embodiment does not define what CAD needs
POSE_NOT_DERIVABLE = "POSE_NOT_DERIVABLE"              # the pose law cannot place a body
NOT_EVALUABLE = "NOT_EVALUABLE"                        # a premise is missing; nothing was decided
FINDING_KINDS = (CONSTRUCTION_INVALID, MATING_AXES_INCONSISTENT, CLEARANCE_NEGATIVE,
                 BODY_INTERFERENCE, MATING_NOT_REALIZED, TRAVEL_BLOCKED, ASSEMBLY_BLOCKED, FEATURE_OUTSIDE_REGION,
                 UNSETTLED_CRITICAL_PARAMETER, UNSUPPORTED_OPERATION, EMBODIMENT_INCOMPLETE,
                 POSE_NOT_DERIVABLE, NOT_EVALUABLE)

#: Who may change what the finding contradicts. s05 owns the embodiment; s03 the
#: topology; s04 the arrangement, states and scale; s06 the settlement; s07 owns
#: only its own capability.
OWNERS = ("s03", "s04", "s05", "s06", "s07")


@dataclass(frozen=True)
class Finding:
    kind: str
    owner: str
    subjects: Tuple[str, ...]
    detail: str
    #: False when the question could not be asked (a premise was missing) - a
    #: NOT_EVALUABLE is never a pass and never a fail.
    evaluable: bool = True
    #: Numbers the finding rests on, so a reader can see the evidence, not only
    #: the verdict.
    evidence: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.kind not in FINDING_KINDS:
            raise ValueError("finding kind %r is not one of %s" % (self.kind, FINDING_KINDS))
        if self.owner not in OWNERS:
            raise ValueError("finding owner %r is not one of %s" % (self.owner, OWNERS))

    def as_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "owner": self.owner, "subjects": list(self.subjects),
                "detail": self.detail, "evaluable": self.evaluable,
                "evidence": dict(self.evidence) if self.evidence else None}

    def __str__(self) -> str:
        return "%s (%s): %s%s" % (self.kind, self.owner, self.detail,
                                  "" if self.evaluable else " [NOT EVALUABLE]")


def blocking(findings: Sequence[Finding]) -> list:
    """The findings that contradict the artifact, as opposed to those that
    report a question nobody could ask."""
    return [f for f in findings if f.evaluable and f.kind != NOT_EVALUABLE]
