"""What this toolchain can actually establish.

Consulted by s02 so that the evidence route is a RECORDED DECISION rather than a
silent selection pressure. Three benchmarks chose mechanisms partly for what
could be evidenced; each was recorded in prose and none had an owner.

This is a statement about the PIPELINE, not about any design, which is why it is
a registry and not DesignState.
"""
from __future__ import annotations

from typing import Dict, List, Optional

#: route_id -> what it can establish, and whether it exists here.
EVIDENCE_ROUTES: Dict[str, Dict] = {
    "RIGID_KINEMATIC_GEOMETRY": {
        "establishes": ["configuration existence", "pose", "reachability"],
        "available": True,
    },
    "SWEPT_INTERFERENCE": {
        "establishes": ["path clearance", "swept occupancy", "assembly insertion",
                        "kinematic blocking"],
        "available": True,
    },
    "MOBILITY_ANALYSIS": {
        "establishes": ["degree-of-freedom availability", "absence of a motion path"],
        "available": True,
    },
    "RIGID_BODY_DYNAMICS": {
        "establishes": ["ideal-joint torque", "back-drive under ideal joints",
                        "quasi-static balance"],
        "available": True,
        "caveat": "ideal joints, no contact resolution, declared density assumptions",
    },
    "CONTACT_RESOLVING_ANALYSIS": {
        "establishes": ["friction retention", "jamming", "binding", "engagement force"],
        "available": False,
    },
    "COMPLIANCE_REDUCED_ORDER": {
        "establishes": ["deflection force", "allowable travel", "snap insertion force"],
        "available": False,
    },
    "MATERIAL_PROPERTY_ANALYSIS": {
        "establishes": ["strength", "stiffness", "wear", "fatigue", "lifetime"],
        "available": False,
    },
    "MANUFACTURING_PROCESS_ANALYSIS": {
        "establishes": ["mouldability", "process suitability", "cost"],
        "available": False,
    },
    "TOLERANCE_ANALYSIS": {
        "establishes": ["fit under variation", "stack-up"],
        "available": False,
    },
}

#: claim class -> the route that would establish it.
_CLAIM_ROUTE = {
    "configuration_exists": "RIGID_KINEMATIC_GEOMETRY",
    "path_is_clear": "SWEPT_INTERFERENCE",
    "motion_is_available": "MOBILITY_ANALYSIS",
    "motion_is_unavailable": "MOBILITY_ANALYSIS",
    "assembly_is_possible": "SWEPT_INTERFERENCE",
    "effort_or_torque": "RIGID_BODY_DYNAMICS",
    "back_drive": "RIGID_BODY_DYNAMICS",
    "friction_retention": "CONTACT_RESOLVING_ANALYSIS",
    "jamming_or_binding": "CONTACT_RESOLVING_ANALYSIS",
    "deflection_force": "COMPLIANCE_REDUCED_ORDER",
    "allowable_deflection": "COMPLIANCE_REDUCED_ORDER",
    "load_capacity": "MATERIAL_PROPERTY_ANALYSIS",
    "durability": "MATERIAL_PROPERTY_ANALYSIS",
    "manufacturability": "MANUFACTURING_PROCESS_ANALYSIS",
    "fit_under_variation": "TOLERANCE_ANALYSIS",
}


def route_for_claim(claim_class: str) -> Optional[Dict]:
    """The route a claim class needs, with its availability. None if unmapped."""
    rid = _CLAIM_ROUTE.get(claim_class)
    if rid is None:
        return None
    out = dict(EVIDENCE_ROUTES[rid])
    out["route_id"] = rid
    return out


def unavailable_routes() -> List[str]:
    return sorted(r for r, v in EVIDENCE_ROUTES.items() if not v["available"])
