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

#: THE MANDATORY PREREQUISITES OF AN EMBODIMENT, one kind per duty. These are
#: STRUCTURAL: something the design committed to has no geometry at all, so no
#: number could express it and the solver is not run. They are found before
#: settlement by `downstream.embodiment.prerequisite_findings` and are answered
#: by a structural revision - which is a different repair from an infeasible or
#: underdetermined system, where the geometry exists and the numbers are wrong.
INTERFACE_SIDE_UNREALIZED = "INTERFACE_SIDE_UNREALIZED"    # a participant body has no feature for it
INTERFACE_NOT_CARRIED = "INTERFACE_NOT_CARRIED"            # a feature names an interface not in the branch
INTERFACE_BODY_MISMATCH = "INTERFACE_BODY_MISMATCH"        # ... one that does not involve its body
MATING_KIND_UNREALIZED = "MATING_KIND_UNREALIZED"          # the side is realized, not by the stated kind
JOINT_UNREALIZED = "JOINT_UNREALIZED"                      # an axis-bearing joint carries no feature
BODY_WITHOUT_MATERIAL = "BODY_WITHOUT_MATERIAL"            # nothing gives the body material
FEATURE_OFF_BRANCH = "FEATURE_OFF_BRANCH"                  # a feature is on no body of the branch
CLEARANCE_UNGOVERNED = "CLEARANCE_UNGOVERNED"              # a declared clearance no Constraint owns
COMPLIANT_JOINT_MALFORMED = "COMPLIANT_JOINT_MALFORMED"    # compliance stated between two bodies
RESTRAINT_UNREALIZED = "RESTRAINT_UNREALIZED"              # a blocking relation nothing embodies
REALIZATION_UNCOVERED = "REALIZATION_UNCOVERED"            # a realization missing a side's material
REALIZATION_FRAGMENTED = "REALIZATION_FRAGMENTED"          # one relation claimed by several records
PREREQUISITE_KINDS = (INTERFACE_SIDE_UNREALIZED, INTERFACE_NOT_CARRIED, INTERFACE_BODY_MISMATCH,
                      MATING_KIND_UNREALIZED, JOINT_UNREALIZED, BODY_WITHOUT_MATERIAL,
                      FEATURE_OFF_BRANCH, CLEARANCE_UNGOVERNED, COMPLIANT_JOINT_MALFORMED,
                      RESTRAINT_UNREALIZED, REALIZATION_UNCOVERED, REALIZATION_FRAGMENTED)

FINDING_KINDS = (CONSTRUCTION_INVALID, CLEARANCE_NEGATIVE,
                 BODY_INTERFERENCE, MATING_NOT_REALIZED, TRAVEL_BLOCKED, ASSEMBLY_BLOCKED, FEATURE_OUTSIDE_REGION,
                 UNSETTLED_CRITICAL_PARAMETER, UNSUPPORTED_OPERATION, EMBODIMENT_INCOMPLETE,
                 POSE_NOT_DERIVABLE, NOT_EVALUABLE) + PREREQUISITE_KINDS

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
