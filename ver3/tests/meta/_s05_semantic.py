"""A MECHANISM-BLIND semantic S05 response builder, for the boundary tests.

WHY IT IS BUILT AND NOT WRITTEN OUT

A fixture response hand-written for a hinge proves that the boundary accepts a
hinge. This one is DERIVED from the duty manifest of whatever topology it is
handed - it reads the bodies, the relations, the interfaces, the stated mating
kinds, the governed clearances and the scale basis, and emits a response that
discharges exactly those duties. The same builder therefore has to work for a
multi-rail carriage, three pads in a recess, a rod in a plain bore, a compliant
retainer, a screw and nut, and a crank-link-slider, and the cross-mechanism
tests are the same call over different upstreams.

It is deliberately dumb about geometry: a box on each side, one design choice
per parameter. What is under test is the AUTHORING BOUNDARY, not the taste of
the geometry.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ver3.assy_v3.downstream import duty_manifest, embodiment

#: The families the manifest and the lowerer read out of a branch.
UPSTREAM_FAMILIES = ("Body", "RigidGroup", "Joint", "Interface", "ConstraintRelation",
                     "Envelope", "FunctionalRegion", "ReferenceScale", "Obligation",
                     "AcceptanceContract", "SelectionDecision")


def view_of(state, branch: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """The s03/s04 rows a consumer view would carry."""
    out = {}
    for family in UPSTREAM_FAMILIES:
        rows = [r for r in state.standing(family)
                if not branch or branch in (r.get("_premises") or [])]
        if rows:
            out[family] = sorted(rows, key=lambda r: r["entity_id"])
    return out


def _envelope_of(view, body: str) -> Optional[str]:
    for env in view.get("Envelope") or []:
        if env.get("body") == body:
            return env.get("entity_id")
    return None


def _additive_kind(polarity: Dict[str, str], preferred=("FACE", "STOCK", "RIB")) -> str:
    for kind in preferred:
        if polarity.get(kind) == "ADDITIVE":
            return kind
    return next(k for k, p in sorted(polarity.items()) if p == "ADDITIVE")


def _num(value, unit="mm"):
    return {"kind": "number", "value": value, "unit": unit}


def _param(name, unit="mm", role=None):
    """A reference that DECLARES what it names - the only way to name one."""
    node = {"kind": "param", "param": name, "unit": unit}
    if role:
        node["role"] = role
    return node


def minimal_response(view: Dict[str, List[Dict[str, Any]]],
                     obligations_to_discharge=()) -> Dict[str, Any]:
    """A response that discharges every duty the manifest derives from `view`.

    Nothing here names a mechanism. Each duty is answered by the same rule: a
    body gets material, a relation gets a feature on each side it relates, an
    interface gets a feature per participant side of the kind s04 stated where
    it stated one, and a governed clearance gets a CLEARANCE constraint.
    """
    manifest = duty_manifest.from_rows(view, obligations_to_discharge=obligations_to_discharge)
    polarity = embodiment.polarity_table()
    neutral = _additive_kind(polarity)

    constraints: List[Dict[str, Any]] = []
    features: List[Dict[str, Any]] = []

    if manifest.scale.required:
        constraints.append({"kind": "DIMENSIONAL", "basis": "DESIGN_CHOICE", "relation": "==",
                            "lhs": _param("scale", role="SCALE"), "rhs": _num(1.0)})
    constraints.append({"kind": "DIMENSIONAL", "basis": "DESIGN_CHOICE",
                        "relation": "==", "lhs": _param("thick"), "rhs": _num(2.0)})

    def solid():
        return {"shape": "BLOCK", "dx": _param("thick"), "dy": _param("thick"),
                "dz": _param("thick")}

    def place(body):
        """On the body's own envelope, with a stated axis.

        An envelope LOCATES and lends the arrangement's +Z; stating the axis
        anyway is what a feature does when it means a particular orientation,
        and it keeps this builder independent of whether any joint declares one.
        """
        return {"datum": {"kind": "ENVELOPE", "ref": _envelope_of(view, body)},
                "axis": "+Z"}

    # 1. material for every body
    for body in manifest.bodies:
        features.append({"key": "stock_%s" % body, "body": body, "feature_kind": "STOCK",
                         "geometry": "stock for %s" % body, "placement": place(body),
                         "solid": solid()})

    # 2. a feature per interface side, of the stated mating kind where stated
    interface_assignments: Dict[str, Any] = {}
    for duty in manifest.interfaces:
        sides: Dict[str, List[str]] = {}
        for body in duty.bodies:
            kind = duty.required_kind(body) or neutral
            key = "if_%s_%s" % (duty.interface, body)
            features.append({"key": key, "body": body, "feature_kind": kind,
                             "geometry": "%s side of %s on %s"
                                         % (kind, duty.interface, body),
                             "placement": place(body), "solid": solid()})
            sides[body] = [key]
        assignment: Dict[str, Any] = {"sides": sides}
        if duty.needs_governing_constraint:
            # DECLARED IN PLACE. One constraint per governed interface, because
            # a canonical Constraint carries one `governs_interface`.
            assignment["governing_constraint"] = {
                "kind": "CLEARANCE", "basis": "DESIGN_CHOICE", "relation": "==",
                "lhs": _param("gap_%s" % duty.interface), "rhs": _num(0.2)}
        interface_assignments[duty.interface] = assignment

    # 2b. geometry that clears every region whose role means free space. A
    #     feature that REMOVES material, placed ON the region: the route the
    #     boundary asks for, and the only one it can check before there is a
    #     solid.
    region_assignments: Dict[str, Dict[str, List[str]]] = {}
    subtractive = next(k for k, p in sorted(polarity.items()) if p == "SUBTRACTIVE")
    for duty in manifest.free_space_regions():
        sides: Dict[str, List[str]] = {}
        for body in duty.owning_bodies:
            key = "clear_%s_%s" % (duty.region, body)
            features.append({"key": key, "body": body, "feature_kind": subtractive,
                             "geometry": "free space for %s in %s" % (duty.region, body),
                             "placement": {"datum": {"kind": "FUNCTIONAL_REGION",
                                                     "ref": duty.region}, "axis": "+Z"},
                             "solid": solid()})
            sides[body] = [key]
        region_assignments[duty.region] = sides

    # 3. material on each side of every relation the design declared, keyed by
    #    the side it is on - the manifest names the sides and the response
    #    mirrors them, so a side cannot be left out by writing a shorter list.
    #
    #    A RESTRAINT STANDS WHERE ITS CONFIGURATION STANDS. Where a relation is
    #    active at particular joint coordinates, the material embodying it is
    #    offset by them, so two limits on one joint at two coordinates are two
    #    places. The offset is a deterministic function of the coordinates and
    #    of nothing else - no mechanism, no feature name, no axis rule.
    coordinates_of: Dict[str, float] = {}
    for restraint in manifest.state_restraints:
        total = sum(float(v) for v in restraint.joint_coordinates.values()
                    if isinstance(v, (int, float)))
        coordinates_of[restraint.relation] = total

    realization_assignments: Dict[str, Dict[str, List[str]]] = {}
    for duty in manifest.realizations:
        sides: Dict[str, List[str]] = {}
        at = coordinates_of.get(duty.target)
        for body in duty.bodies:
            key = "rz_%s_%s" % (duty.target, body)
            placement = place(body)
            if at:
                placement = dict(placement, offset=[at, 0, 0])
            features.append({"key": key, "body": body, "feature_kind": neutral,
                             "geometry": "material embodying %s on %s" % (duty.target, body),
                             "placement": placement, "solid": solid()})
            sides[body] = [key]
        realization_assignments[duty.target] = sides

    realizations = []
    if manifest.obligations_to_discharge:
        realizations.append({
            "addresses_obligations": list(manifest.obligations_to_discharge),
            "participating_features": [f["key"] for f in features[:1]],
            "verification_predicate": "the built assembly carries the named geometry"})

    return {"features": features, "constraints": constraints,
            "realization_assignments": realization_assignments,
            "interface_assignments": interface_assignments,
            "region_assignments": region_assignments,
            "realizations": realizations, "unresolved": []}
