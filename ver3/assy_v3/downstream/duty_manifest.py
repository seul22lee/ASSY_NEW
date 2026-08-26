"""THE EMBODIMENT DUTY MANIFEST - what this branch owes s05, enumerated once.

WHY IT EXISTS

s05's completeness used to live in three places that could disagree: prose in
the prompt, a set of `check_c*` functions over the response, and
`prerequisite_findings` over standing state. A duty the prompt never raised was
a trap rather than a check, and a duty the gate asked but the prompt did not
was how a branch came to be settled while its own producing stage had declared
an interface unrealized. The manifest is the one derivation. It is computed
from the STANDING s03/s04 branch BEFORE the provider is called, and the same
object renders the prompt, validates the response, decides structural
completeness and answers the settlement gate.

WHAT IT IS NOT

It names no mechanism, no feature kind, no axis and no joint class. Every duty
below is enumeration over what s03 and s04 already declared - the bodies, the
joints, the blocking relations, the interfaces and their stated mating
geometry, the reference scale. Nothing here knows what a hinge is, and nothing
here assumes one feature per relation: a duty says WHICH SIDES must carry
material, never how much geometry does it or what it is called.

THE PROVIDER MODEL IS UPSTREAM'S AND IS PRESERVED EXACTLY. A relation whose
provider is an external `provider_reaction_site` owes material on the RETAINED
side only: the thing bearing the load is outside this design's body set, and
demanding a feature for it would force s05 to invent a body that is not the
product.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import ir

#: s03's clearance vocabulary. A CLEARANCE and an INTERFERENCE_FIT are the two
#: whose geometry is a NUMBER someone must own, so they owe a governing
#: Constraint; CONTACT and COMPLIANT_INTERACTION do not.
CLEARANCE_KINDS = ("CLEARANCE", "INTERFERENCE_FIT")

#: The role a scale parameter declares. One authority, kernel length per basis
#: unit, and only where the arrangement's basis is RELATIVE.
SCALE_ROLE = "SCALE"
RELATIVE = "RELATIVE"


@dataclass(frozen=True)
class RealizationDuty:
    """One declared relation that geometry must embody.

    `bodies` are the sides that must carry material. It is never a count of
    features and never a shape: two rails and two carriages embody one guided
    relation together, three pads on three recess walls embody guidance with no
    guide part at all, and a rod in a plain bore may leave a rotation free on
    purpose. All that is owed is material on each side.
    """

    target: str
    family: str                       # "Joint" | "ConstraintRelation"
    bodies: Tuple[str, ...]
    descriptor: str
    external_provider: Optional[str] = None
    #: The joint's declared type, or "" for a relation. Carried so a finding
    #: reads in the design's own words without re-reading the row.
    kind: str = ""
    #: What a relation blocks, or () for a joint. Same reason.
    blocked_dofs: Tuple[str, ...] = ()

    def render(self) -> str:
        tail = ("" if not self.external_provider else
                " (its provider is the external reaction site %s, so only the retained side "
                "is owed material here)" % self.external_provider)
        return ("  %-10s %-18s %s: assign the features that embody it; they must include "
                "material on EACH of %s%s"
                % (self.target, self.family, self.descriptor, ", ".join(self.bodies), tail))


@dataclass(frozen=True)
class InterfaceDuty:
    """One declared interaction whose sides geometry must realize."""

    interface: str
    bodies: Tuple[str, ...]
    interaction_kind: str
    mating: Tuple[Tuple[str, str], ...] = ()      # (body, required feature_kind)
    needs_governing_constraint: bool = False

    def required_kind(self, body: str) -> Optional[str]:
        for b, kind in self.mating:
            if b == body:
                return kind
        return None

    def render(self) -> str:
        line = ("  %-10s %-22s between %s: assign the feature(s) realizing EACH side"
                % (self.interface, self.interaction_kind, " and ".join(self.bodies)))
        if self.mating:
            line += ("; s04 stated the mating geometry, so the feature realizing %s"
                     % ", ".join("%s must be of kind %s" % (b, k) for b, k in self.mating))
        if self.needs_governing_constraint:
            line += ("; and name the Constraint that GOVERNS it - the number that keeps it "
                     "a %s is owed by this interface" % self.interaction_kind)
        return line


@dataclass(frozen=True)
class RegionDuty:
    """A FunctionalRegion whose ROLE has material meaning.

    THE SEMANTICS ARE THE CONTRACT'S, read once. `FunctionalRegion.role_policy`
    declares `excludes_occupancy` per role - a region something passes through
    or reaches into is free space, a region where the product meets what
    carries it is not - and this reads that table rather than naming a role. A
    role the contract does not declare is carried as UNKNOWN and reported, never
    silently treated as either.
    """

    region: str
    role: str
    excludes_occupancy: bool
    known_role: bool
    owning_bodies: Tuple[str, ...]
    volume: Optional[Dict[str, Any]] = None

    def render(self) -> str:
        if not self.known_role:
            return ("  %-10s role %s is not in the declared vocabulary; its material meaning "
                    "is unknown and nothing is assumed" % (self.region, self.role))
        if not self.excludes_occupancy:
            return ("  %-10s %-12s on %s: material here is expected; nothing is owed"
                    % (self.region, self.role, ", ".join(self.owning_bodies)))
        return ("  %-10s %-12s on %s: THIS VOLUME MUST BE FREE OF THE OWNING BODY'S MATERIAL. "
                "Give each owning body geometry that clears it - a feature placed ON THIS "
                "REGION whose kind REMOVES material"
                % (self.region, self.role, ", ".join(self.owning_bodies)))


@dataclass(frozen=True)
class StateRestraintDuty:
    """A relation that blocks motion IN A PARTICULAR CONFIGURATION, at the joint
    coordinates that configuration actually stands at.

    A restraint is not a property of a design, it is a property of a design AT A
    POSITION. Two limits on one joint at two different coordinates are two
    different places for material to be, and geometry that sits in one place
    cannot produce both.
    """

    relation: str
    configuration: str
    state: str
    joint_coordinates: Dict[str, Any]
    blocked_dofs: Tuple[str, ...]
    bodies: Tuple[str, ...]

    def render(self) -> str:
        coords = ", ".join("%s=%s" % (j, v) for j, v in sorted(self.joint_coordinates.items()))
        return ("  %-10s blocks %-22s in %s (state %s, %s): the geometry that embodies it must "
                "be able to touch AT THOSE COORDINATES"
                % (self.relation, ",".join(self.blocked_dofs), self.configuration, self.state,
                   coords or "no coordinate stated"))


@dataclass(frozen=True)
class ReleasedMotionDuty:
    """A motion the design REQUIRES, and the restraints released to allow it.

    The other half of a restraint duty: geometry that produces a limit in one
    configuration must not still produce it where the design says the motion
    happens.
    """

    transition: str
    from_state: str
    to_state: str
    released_constraints: Tuple[str, ...]
    required_motions: Tuple[Tuple[str, str], ...]

    def render(self) -> str:
        return ("  %-10s %s -> %s requires %s; %s is released for it and must not still be "
                "produced by material"
                % (self.transition, self.from_state, self.to_state,
                   ", ".join("%s.%s" % m for m in self.required_motions) or "motion",
                   ", ".join(self.released_constraints) or "nothing"))


@dataclass(frozen=True)
class TransitionClearanceDuty:
    """A motion s04 committed and proved against the arrangement. Material put
    into a path already shown clear turns a moving design into one that binds."""

    transition: str
    from_state: str
    to_state: str
    moving_groups: Tuple[str, ...]
    changed_coordinates: Tuple[str, ...]
    swept_volumes: Tuple[str, ...]

    def render(self) -> str:
        return ("  %-10s %s -> %s moving %s about %s: keep this path clear of product material"
                % (self.transition, self.from_state, self.to_state,
                   ", ".join(self.moving_groups) or "?",
                   ", ".join(self.changed_coordinates) or "?"))


@dataclass(frozen=True)
class AssemblyDuty:
    """A body that has to get to its place. Its insertion path is free space
    for as long as the insertion lasts."""

    step: str
    body: str
    access_side: Optional[str]
    insertion_direction: Optional[Tuple[float, float, float]]
    activates: Tuple[str, ...]
    order_index: Optional[int] = None

    def render(self) -> str:
        return ("  %-10s %s enters from %s along %s: that path is free space while it does"
                % (self.step, self.body, self.access_side or "?",
                   self.insertion_direction or "no direction stated"))


@dataclass(frozen=True)
class ScaleDuty:
    """Whether this arrangement needs a declared scale authority, and why."""

    required: bool
    basis: str
    reference_scale: Optional[str] = None

    def render(self) -> str:
        if self.required:
            return ("  the arrangement basis is %s (%s), so declare EXACTLY ONE parameter with "
                    'role "%s" in %s - kernel length units per basis unit - and close it with a '
                    "constraint like any other" % (self.basis, self.reference_scale, SCALE_ROLE,
                                                   ir.KERNEL_LENGTH_UNIT))
        return ("  the arrangement basis is %s, so declare NO %s parameter"
                % (self.basis or "unstated", SCALE_ROLE))


@dataclass(frozen=True)
class EmbodimentDutyManifest:
    """Everything this branch owes its embodiment, derived and enumerated."""

    branch: Optional[str]
    bodies: Tuple[str, ...]
    realizations: Tuple[RealizationDuty, ...]
    interfaces: Tuple[InterfaceDuty, ...]
    axisless_datums: Tuple[str, ...]
    scale: ScaleDuty
    obligations_to_discharge: Tuple[str, ...] = ()
    #: THE SPATIAL HALF. s04's commitments were visible to the prompt and owed
    #: nothing; a structurally complete embodiment could bury an aperture in
    #: material and be accepted. These make them duties.
    regions: Tuple[RegionDuty, ...] = ()
    state_restraints: Tuple[StateRestraintDuty, ...] = ()
    released_motions: Tuple[ReleasedMotionDuty, ...] = ()
    transitions: Tuple[TransitionClearanceDuty, ...] = ()
    assembly: Tuple[AssemblyDuty, ...] = ()

    # ------------------------------------------------------------ accessors
    def required_realization_targets(self) -> Tuple[str, ...]:
        return tuple(d.target for d in self.realizations)

    def realization(self, target: str) -> Optional[RealizationDuty]:
        return next((d for d in self.realizations if d.target == target), None)

    def interface(self, iid: str) -> Optional[InterfaceDuty]:
        return next((d for d in self.interfaces if d.interface == iid), None)

    def required_interfaces(self) -> Tuple[str, ...]:
        return tuple(d.interface for d in self.interfaces)

    def free_space_regions(self) -> Tuple[RegionDuty, ...]:
        """The regions whose declared role means MATERIAL MUST NOT BE HERE."""
        return tuple(d for d in self.regions if d.known_role and d.excludes_occupancy)

    def region(self, rid: str) -> Optional[RegionDuty]:
        return next((d for d in self.regions if d.region == rid), None)

    def restraints_by_joint(self) -> Dict[str, List[StateRestraintDuty]]:
        """Restraint duties gathered by the joint whose coordinate they stand
        at, so two limits on one joint can be compared."""
        out: Dict[str, List[StateRestraintDuty]] = {}
        for duty in self.state_restraints:
            for joint in sorted(duty.joint_coordinates):
                out.setdefault(joint, []).append(duty)
        return out

    def governed_interfaces(self) -> Tuple[str, ...]:
        return tuple(d.interface for d in self.interfaces if d.needs_governing_constraint)

    def joint_duties(self) -> Tuple["RealizationDuty", ...]:
        return tuple(d for d in self.realizations if d.family == "Joint")

    def restraint_duties(self) -> Tuple["RealizationDuty", ...]:
        return tuple(d for d in self.realizations if d.family == "ConstraintRelation")

    def as_record(self) -> Dict[str, Any]:
        """The manifest as evidence, so a review can read what was owed."""
        return {
            "branch": self.branch,
            "bodies": list(self.bodies),
            "realizations": [
                {"target": d.target, "family": d.family, "bodies": list(d.bodies),
                 "descriptor": d.descriptor, "external_provider": d.external_provider}
                for d in self.realizations],
            "interfaces": [
                {"interface": d.interface, "bodies": list(d.bodies),
                 "interaction_kind": d.interaction_kind,
                 "mating": {b: k for b, k in d.mating},
                 "needs_governing_constraint": d.needs_governing_constraint}
                for d in self.interfaces],
            "axisless_datums": list(self.axisless_datums),
            "scale": {"required": self.scale.required, "basis": self.scale.basis,
                      "reference_scale": self.scale.reference_scale},
            "obligations_to_discharge": list(self.obligations_to_discharge),
            "regions": [
                {"region": d.region, "role": d.role, "known_role": d.known_role,
                 "excludes_occupancy": d.excludes_occupancy,
                 "owning_bodies": list(d.owning_bodies), "volume": d.volume}
                for d in self.regions],
            "state_restraints": [
                {"relation": d.relation, "configuration": d.configuration, "state": d.state,
                 "joint_coordinates": dict(d.joint_coordinates),
                 "blocked_dofs": list(d.blocked_dofs), "bodies": list(d.bodies)}
                for d in self.state_restraints],
            "released_motions": [
                {"transition": d.transition, "from_state": d.from_state,
                 "to_state": d.to_state, "released_constraints": list(d.released_constraints),
                 "required_motions": [list(m) for m in d.required_motions]}
                for d in self.released_motions],
            "transitions": [
                {"transition": d.transition, "from_state": d.from_state,
                 "to_state": d.to_state, "moving_groups": list(d.moving_groups),
                 "changed_coordinates": list(d.changed_coordinates),
                 "swept_volumes": list(d.swept_volumes)}
                for d in self.transitions],
            "assembly": [
                {"step": d.step, "body": d.body, "access_side": d.access_side,
                 "insertion_direction": list(d.insertion_direction)
                 if d.insertion_direction else None,
                 "activates": list(d.activates), "order_index": d.order_index}
                for d in self.assembly],
        }

    # -------------------------------------------------------------- prompt
    def render(self) -> str:
        """The duties, as the enumerated list the provider is asked to satisfy."""
        out: List[str] = []
        out.append("BODIES THAT NEED MATERIAL - every one needs at least one ADDITIVE feature:")
        out.extend("  %s" % b for b in self.bodies) if self.bodies else out.append("  (none)")
        out.append("")
        out.append("RELATIONS TO EMBODY - `realization_assignments` must have EXACTLY these "
                   "keys, no more and no fewer:")
        if self.realizations:
            out.extend(d.render() for d in self.realizations)
        else:
            out.append("  (none - this branch declares no relation to embody)")
        out.append("")
        out.append("INTERFACES TO REALIZE - `interface_assignments` must have EXACTLY these "
                   "keys, and each must cover every listed body:")
        if self.interfaces:
            out.extend(d.render() for d in self.interfaces)
        else:
            out.append("  (none)")
        if self.axisless_datums:
            out.append("")
            out.append("DATUMS THAT LEND NO ORIENTATION - a feature placed against one of "
                       "these MUST state its own `axis`:")
            out.extend("  %s" % d for d in self.axisless_datums)
        out.append("")
        out.append("SPACE THAT MUST STAY FREE - a region the design promises is open cannot "
                   "be buried in its own body's material:")
        free = self.free_space_regions()
        if free:
            out.extend(d.render() for d in free)
            out.append("  For EACH of these, `region_assignments` names the feature(s) on each "
                       "owning body that clear it. AN ENVELOPE IS NOT MATERIAL: a body is not "
                       "a filled envelope, it is the material you actually give it.")
        else:
            out.append("  (none)")
        unknown = [d for d in self.regions if not d.known_role]
        if unknown:
            out.append("  NOT INTERPRETED: %s"
                       % "; ".join(d.render().strip() for d in unknown))
        if self.state_restraints:
            out.append("")
            out.append("RESTRAINTS STAND AT A POSITION - a limit is geometry at the coordinate "
                       "the design is actually at:")
            out.extend(d.render() for d in self.state_restraints)
            clash = self.restraints_by_joint()
            for joint, duties in sorted(clash.items()):
                values = sorted({str(d.joint_coordinates.get(joint)) for d in duties})
                if len(values) > 1:
                    out.append("  %s stands at %s in different configurations, so the geometry "
                               "producing a limit at one of them CANNOT be the same geometry, "
                               "in the same place, that produces the limit at another."
                               % (joint, " and ".join(values)))
        if self.released_motions:
            out.append("")
            out.append("MOTION THE DESIGN REQUIRES - it must still be possible after your "
                       "geometry exists:")
            out.extend(d.render() for d in self.released_motions)
        if self.transitions:
            out.append("")
            out.append("PATHS ALREADY PROVED CLEAR - do not put material into one:")
            out.extend(d.render() for d in self.transitions)
        if self.assembly:
            out.append("")
            out.append("ASSEMBLY - each body has to reach its place:")
            out.extend(d.render() for d in self.assembly)
        out.append("")
        out.append("SCALE AUTHORITY:")
        out.append(self.scale.render())
        out.append("")
        out.append("PARAMETER CLOSURE - every parameter you declare must be named by at least "
                   "one constraint you write; a parameter no constraint determines is a free "
                   "direction the solver reports back and nothing can be built from it.")
        if self.obligations_to_discharge:
            out.append("")
            out.append("OBLIGATIONS THIS EMBODIMENT MUST DISCHARGE - each cited by a "
                       "realization with a verification predicate:")
            out.extend("  %s" % o for o in self.obligations_to_discharge)
        return "\n".join(out)


# ==========================================================================
# Derivation. Every rule below mirrors a duty production already enforces;
# none is new and none is mechanism-specific.
# ==========================================================================
def _body_of_group(rows) -> Dict[str, str]:
    return {g.get("entity_id"): g.get("body") for g in rows.get("RigidGroup") or []}


def joint_duties(rows) -> List[RealizationDuty]:
    """Every Joint of the branch, and the bodies it relates.

    A joint whose own groups resolve to no body is skipped, exactly as the
    realization check skips it: that is s03's record to complete, and asking
    for material on a side that does not resolve would be asking for geometry
    on nothing.
    """
    groups = _body_of_group(rows)
    out: List[RealizationDuty] = []
    for j in sorted(rows.get("Joint") or [], key=lambda x: x.get("entity_id") or ""):
        sides = sorted({groups.get(j.get("parent_group")), groups.get(j.get("child_group"))}
                       - {None})
        if not sides:
            continue
        out.append(RealizationDuty(
            target=j.get("entity_id"), family="Joint", bodies=tuple(sides),
            descriptor="%s (dof %s, axis %s)"
                       % (str(j.get("joint_type", "")).upper(),
                          ",".join(j.get("dof") or []) or "none",
                          j.get("axis_direction")),
            kind=str(j.get("joint_type", "")).upper()))
    return out


def restraint_duties(rows) -> List[RealizationDuty]:
    """Every ConstraintRelation that BLOCKS something, and the sides it acts
    between - by the relation's own provider model, unchanged."""
    groups = _body_of_group(rows)
    out: List[RealizationDuty] = []
    for rel in sorted(rows.get("ConstraintRelation") or [],
                      key=lambda x: x.get("entity_id") or ""):
        if not rel.get("blocked_dofs"):
            continue
        retained = groups.get(rel.get("retained_group"))
        provider = rel.get("provider_body")
        external = bool(rel.get("provider_reaction_site")) and not provider
        sides = [b for b in (retained, provider) if b]
        if not sides:
            continue
        out.append(RealizationDuty(
            target=rel.get("entity_id"), family="ConstraintRelation",
            bodies=tuple(sides),
            descriptor="blocks %s" % ", ".join(str(d) for d in (rel.get("blocked_dofs") or [])),
            external_provider=rel.get("provider_reaction_site") if external else None,
            blocked_dofs=tuple(str(d) for d in (rel.get("blocked_dofs") or []))))
    return out


def interface_duties(rows) -> List[InterfaceDuty]:
    """Every Interface of the branch: each participant body owes a feature, a
    stated mating side owes that feature_kind, and a clearance owes a
    governing Constraint."""
    out: List[InterfaceDuty] = []
    for iface in sorted(rows.get("Interface") or [], key=lambda x: x.get("entity_id") or ""):
        bodies = tuple(b for b in (iface.get("bodies") or []) if b)
        if not bodies:
            continue
        kind = str(iface.get("interaction_kind") or "").upper()
        mating: List[Tuple[str, str]] = []
        mg = iface.get("mating_geometry")
        if isinstance(mg, dict):
            for side in ("inner", "outer"):
                body = mg.get(side + "_body")
                feature = str(mg.get(side + "_feature") or "").upper()
                if body and feature:
                    mating.append((body, feature))
        out.append(InterfaceDuty(
            interface=iface.get("entity_id"), bodies=bodies, interaction_kind=kind,
            mating=tuple(sorted(set(mating))),
            needs_governing_constraint=kind in CLEARANCE_KINDS))
    return out


def axisless_datums(rows) -> List[str]:
    """Committed datums that LOCATE without ORIENTING - a joint declaring no
    axis. A feature placed against one carries its own axis or the write
    boundary refuses it."""
    out = []
    for j in sorted(rows.get("Joint") or [], key=lambda x: x.get("entity_id") or ""):
        axis = str(j.get("axis_direction") or "").strip().upper()
        if ir.axis_vector(axis) is None:
            out.append("%s (%s, axis_direction %s)"
                       % (j.get("entity_id"), j.get("joint_type"), j.get("axis_direction")))
    return out


def region_duties(rows) -> List[RegionDuty]:
    """Every FunctionalRegion, with the material meaning its ROLE declares."""
    from ..stages.s04_envelope_and_motion import excludes_occupancy, unknown_region_role

    out: List[RegionDuty] = []
    for r in sorted(rows.get("FunctionalRegion") or [], key=lambda x: x.get("entity_id") or ""):
        role = str(r.get("role") or "").strip().upper()
        owning = tuple(b for b in (r.get("owning_bodies") or []) if isinstance(b, str))
        if not owning:
            continue                    # ownerless; s03's record to complete
        out.append(RegionDuty(
            region=r.get("entity_id"), role=role,
            known_role=not unknown_region_role(role),
            excludes_occupancy=excludes_occupancy(role),
            owning_bodies=owning,
            volume=r.get("volume") if isinstance(r.get("volume"), dict) else None))
    return out


def state_restraint_duties(rows) -> List[StateRestraintDuty]:
    """Every blocking relation, at every configuration it is active in, with
    the joint coordinates that configuration actually stands at.

    A relation naming no configuration is active throughout and gets no
    coordinate-specific duty here: there is no particular position to hold it
    at, and inventing one would be inventing a design decision.
    """
    groups = _body_of_group(rows)
    states_by_configuration: Dict[str, List[Dict[str, Any]]] = {}
    for st in sorted(rows.get("State") or [], key=lambda x: x.get("entity_id") or ""):
        if st.get("configuration"):
            states_by_configuration.setdefault(st["configuration"], []).append(st)
    out: List[StateRestraintDuty] = []
    for rel in sorted(rows.get("ConstraintRelation") or [],
                      key=lambda x: x.get("entity_id") or ""):
        blocked = tuple(str(d) for d in (rel.get("blocked_dofs") or []))
        if not blocked:
            continue
        retained = groups.get(rel.get("retained_group"))
        sides = tuple(b for b in (retained, rel.get("provider_body")) if b)
        if not sides:
            continue
        for configuration in sorted(rel.get("configurations") or []):
            for st in states_by_configuration.get(configuration) or []:
                coordinates = st.get("joint_coordinates")
                out.append(StateRestraintDuty(
                    relation=rel.get("entity_id"), configuration=configuration,
                    state=st.get("entity_id"),
                    joint_coordinates=dict(coordinates) if isinstance(coordinates, dict) else {},
                    blocked_dofs=blocked, bodies=sides))
    return out


def released_motion_duties(rows) -> List[ReleasedMotionDuty]:
    """Every motion the design requires, with the restraints released for it."""
    requirements = {r.get("entity_id"): r for r in rows.get("TransitionRequirement") or []}
    out: List[ReleasedMotionDuty] = []
    for t in sorted(rows.get("Transition") or [], key=lambda x: x.get("entity_id") or ""):
        req = requirements.get(t.get("realizes_requirement")) or {}
        motions = tuple(
            (str(m.get("joint")), str(m.get("dof")))
            for m in (req.get("required_relative_motions") or []) if isinstance(m, dict))
        released = tuple(c for c in (req.get("released_constraints") or [])
                         if isinstance(c, str))
        if not motions and not released:
            continue
        out.append(ReleasedMotionDuty(
            transition=t.get("entity_id"), from_state=t.get("from_state"),
            to_state=t.get("to_state"), released_constraints=released,
            required_motions=motions))
    return out


def transition_duties(rows) -> List[TransitionClearanceDuty]:
    """Every committed motion, with the occupancy s04 proved it against."""
    swept: Dict[str, List[str]] = {}
    for sv in sorted(rows.get("SweptVolume") or [], key=lambda x: x.get("entity_id") or ""):
        if sv.get("transition"):
            swept.setdefault(sv["transition"], []).append(sv.get("entity_id"))
    out: List[TransitionClearanceDuty] = []
    for t in sorted(rows.get("Transition") or [], key=lambda x: x.get("entity_id") or ""):
        tid = t.get("entity_id")
        out.append(TransitionClearanceDuty(
            transition=tid, from_state=t.get("from_state"), to_state=t.get("to_state"),
            moving_groups=tuple((t.get("path") or {}).get("moving_groups") or ()),
            changed_coordinates=tuple(t.get("changed_coordinates") or ()),
            swept_volumes=tuple(swept.get(tid) or ())))
    return out


def assembly_duties(rows) -> List[AssemblyDuty]:
    """Every body that has to reach its place, and along what."""
    out: List[AssemblyDuty] = []
    for step in sorted(rows.get("AssemblyStep") or [],
                       key=lambda x: (x.get("order_index") if isinstance(x.get("order_index"), int)
                                      else 0, x.get("entity_id") or "")):
        direction = step.get("insertion_direction")
        vector = (tuple(float(c) for c in direction)
                  if isinstance(direction, (list, tuple)) and len(direction) == 3 else None)
        if not step.get("body"):
            continue
        out.append(AssemblyDuty(
            step=step.get("entity_id"), body=step.get("body"),
            access_side=step.get("access_side"), insertion_direction=vector,
            activates=tuple(a for a in (step.get("activates") or []) if isinstance(a, str)),
            order_index=step.get("order_index")))
    return out


def scale_duty(rows) -> ScaleDuty:
    """Whether a SCALE parameter is owed, from the committed ReferenceScale."""
    scales = sorted(rows.get("ReferenceScale") or [], key=lambda x: x.get("entity_id") or "")
    if not scales:
        return ScaleDuty(required=False, basis="", reference_scale=None)
    scale = scales[0]
    basis = str(scale.get("basis") or "").strip().upper()
    return ScaleDuty(required=(basis == RELATIVE), basis=basis,
                     reference_scale=scale.get("entity_id"))


def from_rows(rows: Dict[str, List[Dict[str, Any]]], branch: Optional[str] = None,
              obligations_to_discharge: Sequence[str] = ()) -> EmbodimentDutyManifest:
    """THE ONE DERIVATION. `rows` are the standing s03/s04 rows of the branch -
    from state (`embodiment.rows_from_state`) or from the recorded consumer
    view. Both are the same rows; neither is a second rule."""
    bodies = tuple(sorted(b.get("entity_id") for b in (rows.get("Body") or [])
                          if b.get("entity_id")))
    realizations = tuple(joint_duties(rows) + restraint_duties(rows))
    return EmbodimentDutyManifest(
        branch=branch, bodies=bodies, realizations=realizations,
        interfaces=tuple(interface_duties(rows)),
        axisless_datums=tuple(axisless_datums(rows)),
        scale=scale_duty(rows),
        obligations_to_discharge=tuple(sorted(obligations_to_discharge)),
        regions=tuple(region_duties(rows)),
        state_restraints=tuple(state_restraint_duties(rows)),
        released_motions=tuple(released_motion_duties(rows)),
        transitions=tuple(transition_duties(rows)),
        assembly=tuple(assembly_duties(rows)))
