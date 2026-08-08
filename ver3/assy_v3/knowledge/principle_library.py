"""Mechanical principle families, indexed by the FUNCTION they perform.

Product-independent by construction. The index key is a physical function class -
"convert a rotary input to a linear output", "maintain a configuration without
continuous input" - and the value is the set of principle families that can
perform it. Nothing here knows what a box, a lift or a stand is.

The anti-pattern this exists to prevent: a stage prompt that says "a box has a
hinge", "a shaft needs a bearing", "a lift uses a lead screw". Those map a
PRODUCT NOUN to a MECHANISM, which is retirement row R-10 at product scale. Here
a stage supplies a function class it derived from obligations, and receives every
family that performs it - including the ones it would not have thought of.
"""
from __future__ import annotations

from typing import Dict, List

#: Function classes a mechanism may be required to perform.
FUNCTION_CLASSES = (
    "PERMIT_RELATIVE_MOTION",
    "CONVERT_MOTION",
    "MAINTAIN_CONFIGURATION",
    "BOUND_MOTION",
    "RETAIN_BODY",
    "GUIDE_MOTION",
    "TRANSMIT_LOAD",
    "PERMIT_ASSEMBLY",
    "ACTUATE",
    "METER_DISCRETE_QUANTITY",
)

#: function class -> principle families. Each family names its physical basis,
#: the obligations it CREATES, and the claim classes it depends on.
PRINCIPLE_FAMILIES: Dict[str, List[Dict]] = {
    "PERMIT_RELATIVE_MOTION": [
        {"family": "REVOLUTE_PAIR", "basis": "one rotational freedom about a fixed axis",
         "creates": ["axial retention", "radial support"], "depends_on_claims": []},
        {"family": "PRISMATIC_PAIR", "basis": "one translational freedom along a fixed direction",
         "creates": ["lateral guidance", "travel bounds"], "depends_on_claims": []},
        {"family": "HELICAL_PAIR", "basis": "coupled rotation and translation",
         "creates": ["axial retention", "anti-rotation of the driven body"],
         "depends_on_claims": ["friction_retention"]},
        {"family": "PLANAR_PAIR", "basis": "two translations and one rotation in a plane",
         "creates": ["out-of-plane retention"], "depends_on_claims": []},
        {"family": "SPHERICAL_PAIR", "basis": "three rotations about a point",
         "creates": ["radial retention"], "depends_on_claims": []},
        {"family": "COMPLIANT_FLEXURE", "basis": "elastic deformation of a continuous member",
         "creates": ["deflection bound", "recovery"],
         "depends_on_claims": ["allowable_deflection", "durability"]},
    ],
    "CONVERT_MOTION": [
        {"family": "CRANK_SLIDER", "basis": "a rotating crank driving a slider through a link",
         "creates": ["slider guidance", "two revolute joints"], "self_locking": False,
         "depends_on_claims": []},
        {"family": "SCREW_AND_NUT", "basis": "a helical pair converting rotation to translation",
         "creates": ["anti-rotation of the nut", "axial support of the screw"],
         "self_locking": True, "depends_on_claims": ["friction_retention"]},
        {"family": "RACK_AND_PINION", "basis": "a toothed wheel engaging a toothed bar",
         "creates": ["rack guidance", "tooth engagement"], "self_locking": False,
         "depends_on_claims": []},
        {"family": "CAM_AND_FOLLOWER", "basis": "a profiled surface displacing a follower",
         "creates": ["follower return", "follower guidance"], "self_locking": False,
         "depends_on_claims": ["jamming_or_binding"]},
        {"family": "LEVER_LINKAGE", "basis": "rigid links pivoting to change displacement ratio",
         "creates": ["pivot supports"], "self_locking": False, "depends_on_claims": []},
        {"family": "FLEXIBLE_ELEMENT_DRIVE", "basis": "a belt, cable or chain around pulleys",
         "creates": ["tensioning", "pulley supports"], "self_locking": False,
         "depends_on_claims": ["friction_retention"]},
        {"family": "WEDGE_OR_INCLINE", "basis": "a sliding inclined surface",
         "creates": ["normal reaction", "guidance"], "self_locking": True,
         "depends_on_claims": ["friction_retention"]},
    ],
    "MAINTAIN_CONFIGURATION": [
        {"family": "KINEMATIC_BLOCK", "basis": "the motion is geometrically unavailable",
         "creates": ["a blocking body pair", "a release action"],
         "depends_on_claims": ["motion_is_unavailable"]},
        {"family": "OVER_CENTRE", "basis": "the configuration sits past a toggle point",
         "creates": ["a travel bound", "a release action"],
         "depends_on_claims": ["effort_or_torque"]},
        {"family": "DETENT_OR_SNAP", "basis": "a compliant member seated in a recess",
         "creates": ["deflection bound", "recovery", "a release action"],
         "depends_on_claims": ["deflection_force", "allowable_deflection"]},
        {"family": "FRICTION_HOLD", "basis": "a friction interface resisting motion",
         "creates": ["a normal load", "a release action"],
         "depends_on_claims": ["friction_retention"]},
        {"family": "GRAVITY_SEATED", "basis": "a stable equilibrium under the declared orientation",
         "creates": ["an orientation assumption"],
         "depends_on_claims": ["effort_or_torque"]},
        {"family": "SEPARATE_RETAINING_MEMBER", "basis": "a distinct body displaced to release",
         "creates": ["retention of the retainer", "a release action"],
         "depends_on_claims": ["motion_is_unavailable"]},
    ],
    "BOUND_MOTION": [
        {"family": "HARD_STOP", "basis": "two surfaces meeting at the limit",
         "creates": ["a producing feature pair"], "depends_on_claims": ["motion_is_unavailable"]},
        {"family": "JOINT_LIMIT_BY_GEOMETRY", "basis": "the pair runs out of engagement",
         "creates": ["engagement length"], "depends_on_claims": ["motion_is_unavailable"]},
    ],
    "RETAIN_BODY": [
        {"family": "LATER_BODY_COVER", "basis": "a body installed afterwards closes the escape",
         "creates": ["an assembly ordering constraint"], "depends_on_claims": []},
        {"family": "ROTATION_LOCK", "basis": "a bayonet or twist misaligns the escape path",
         "creates": ["a turn operation", "angular retention"], "depends_on_claims": []},
        {"family": "ELASTIC_CAPTURE", "basis": "a compliant member deflects then recovers",
         "creates": ["deflection bound", "recovery"],
         "depends_on_claims": ["allowable_deflection"]},
        {"family": "GEOMETRIC_UNDERCUT", "basis": "a profile that cannot pass its opening",
         "creates": ["an insertion path that is not a straight translation"],
         "depends_on_claims": []},
    ],
    "GUIDE_MOTION": [
        {"family": "PRISMATIC_GUIDE", "basis": "mating surfaces constraining all but one translation",
         "creates": ["clearance", "anti-rotation"], "depends_on_claims": []},
        {"family": "JOURNAL_SUPPORT", "basis": "a cylindrical surface constraining radial motion",
         "creates": ["axial location"], "depends_on_claims": []},
        {"family": "MULTI_POINT_CONSTRAINT", "basis": "two or more separated contacts removing rotation",
         "creates": ["separation distance"], "depends_on_claims": []},
    ],
    "TRANSMIT_LOAD": [
        {"family": "DIRECT_BEARING", "basis": "surfaces in compression",
         "creates": ["a reaction site"], "depends_on_claims": ["load_capacity"]},
        {"family": "SHEAR_MEMBER", "basis": "a member loaded transversely",
         "creates": ["a reaction site"], "depends_on_claims": ["load_capacity"]},
        {"family": "TENSION_MEMBER", "basis": "a member loaded along its length",
         "creates": ["anchorages"], "depends_on_claims": ["load_capacity"]},
    ],
    "PERMIT_ASSEMBLY": [
        {"family": "STRAIGHT_INSERTION", "basis": "one straight translation into place",
         "creates": ["retention of the reverse direction"], "depends_on_claims": []},
        {"family": "INSERT_AND_TURN", "basis": "a translation followed by a rotation",
         "creates": ["angular retention"], "depends_on_claims": []},
        {"family": "ELASTIC_INSERTION", "basis": "a member deflects to pass and recovers",
         "creates": ["deflection bound", "recovery"],
         "depends_on_claims": ["deflection_force", "allowable_deflection"]},
    ],
    "METER_DISCRETE_QUANTITY": [
        {"family": "ESCAPEMENT", "basis": "two gates alternately opened so that one item passes per cycle",
         "creates": ["a cycling input", "a gate travel bound", "a return to the rest gate state"],
         "depends_on_claims": ["motion_is_unavailable"]},
        {"family": "SINGLE_ITEM_POCKET", "basis": "a recess sized for one item, carried past a barrier",
         "creates": ["a pocket sized to the item", "a barrier the item cannot pass otherwise",
                     "a return of the carrier"],
         "depends_on_claims": ["jamming_or_binding"]},
        {"family": "INDEXING_ROTOR", "basis": "a rotor advanced by a fixed angle per actuation",
         "creates": ["angular positioning", "a stop per index position", "a return or ratchet"],
         "depends_on_claims": ["motion_is_unavailable"]},
        {"family": "GATED_PAIR", "basis": "an upstream and a downstream closure never open together",
         "creates": ["a linkage between the two closures", "a volume between them holding one item"],
         "depends_on_claims": ["motion_is_unavailable"]},
        {"family": "METERED_APERTURE", "basis": "an opening admitting at most one item at a time by size",
         "creates": ["an aperture sized to the item", "a means of clearing a stalled item"],
         "depends_on_claims": ["jamming_or_binding"]},
    ],
    "ACTUATE": [
        {"family": "DIRECT_MANUAL", "basis": "a user surface moved by hand",
         "creates": ["reachability", "an access path"], "depends_on_claims": []},
        {"family": "STORED_ENERGY", "basis": "a spring or equivalent releasing stored work",
         "creates": ["energy storage", "a retaining catch"],
         "depends_on_claims": ["effort_or_torque", "durability"]},
        {"family": "EXTERNAL_POWER", "basis": "a supplied energy source",
         "creates": ["a power interface", "control"], "depends_on_claims": ["effort_or_torque"]},
    ],
}

#: Added after live reasoning on an unseen input: every other function class
#: describes relative motion of the PRODUCT'S OWN bodies. None described
#: controlling the passage of external items THROUGH the product, so a request
#: for "release exactly one each time" was servable by no offered family. The
#: reasoning correctly recorded the gap rather than inventing a family; this
#: entry closes it.

#: The retention trichotomy, stated once. A rigid part installed by a single
#: straight translation always leaves the reverse direction open.
RETENTION_TERMINATION = ("LATER_BODY_COVER", "ROTATION_LOCK", "ELASTIC_CAPTURE")


def families_for_function(function_class: str) -> List[Dict]:
    if function_class not in PRINCIPLE_FAMILIES:
        raise KeyError("unknown function class %r" % function_class)
    return [dict(f) for f in PRINCIPLE_FAMILIES[function_class]]
