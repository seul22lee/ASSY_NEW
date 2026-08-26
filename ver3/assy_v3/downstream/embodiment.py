"""UNIT G. CAD-constructibility of an embodiment, as structural checks over
canonical rows.

What must be embodied is DERIVED FROM UPSTREAM: every body needs material
(at least one additive feature); every kinematic relation s03 declared - a
Joint, and a ConstraintRelation that blocks something - is embodied by a
KinematicRealization whose features cover the sides it relates; a mating side
s04 stated is realized by a feature of the stated kind. Nothing names a
mechanism class, a feature kind or a joint class.

REALIZATION IS DECLARED, NOT INFERRED. Three inferences stood here and all
three were coincidences a design could satisfy without embodying anything: a
feature PLACED AT a joint, then one also ORIENTED ALONG it, and for a restraint
a body merely carrying a feature whose KIND was spelled STOP, SHOULDER or
KEEPER. A keeper on a hinge axis permits no rotation; a feature named STOP
restrains nothing by being named. What embodies a relation is now said, once,
by a record whose only content is the target and the material.

ONE IMPLEMENTATION, TWO SURFACES: s05 asks these of its response before it
writes (the findings carry the check's name), and s06's entry gate asks them
of what stands. The feature grammar itself - placement, construction, one
terminal - is the IR's and is refused at the write boundary; these checks
assume records that read.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import duty_manifest, findings, ir

#: Whose decision an unmet prerequisite is, unless the record at fault is
#: another stage's: the embodiment is s05's to author.
OWNER = "s05"

#: Family names, so the two surfaces read the same rows by the same keys.
REALIZATION = "KinematicRealization"


def polarity_table() -> Dict[str, str]:
    """feature kind -> ADDITIVE | SUBTRACTIVE, from the canonical contract."""
    from ..state.design_state import Contracts
    table = (Contracts().families.get("Feature") or {}).get("feature_kind_polarity") or {}
    return {str(kind).upper(): pol for pol, kinds in table.items() for kind in (kinds or [])}


#: The s04 families the SPATIAL duties are derived from. Carried by every row
#: reader, so a manifest built from state and one built from the recorded view
#: see the same commitments.
SPATIAL_FAMILIES = ("FunctionalRegion", "State", "Configuration", "Transition",
                    "TransitionRequirement", "SweptVolume", "AssemblyStep",
                    "ReferenceScale", "Envelope")


def rows_from_response(parsed: Dict[str, Any], view: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """The response as canonical rows: what the design decided (from the view)
    and what this response proposes (features and the constraints that govern
    them). Both surfaces below read exactly these keys."""
    rows = {fam: list(view.get(fam) or []) for fam in
            ("Body", "RigidGroup", "Joint", "Interface", "ConstraintRelation")
            + SPATIAL_FAMILIES}
    for family, key in (("Feature", "features"), ("Constraint", "constraints"),
                        (REALIZATION, "kinematic_realizations")):
        rows[family] = []
        for item in parsed.get(key) or []:
            if isinstance(item, dict):
                rec = dict(item)
                rec["entity_id"] = rec.get("entity_id") or rec.get("id")
                rows[family].append(rec)
    return rows


def rows_from_state(state, branch: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    from .canonical_io import _in_branch

    rows: Dict[str, List[Dict[str, Any]]] = {}
    for fam in ("Body", "RigidGroup", "Joint", "Interface", "Feature", "Constraint",
                "ConstraintRelation", REALIZATION) + SPATIAL_FAMILIES:
        rows[fam] = [r for r in sorted(state.standing(fam), key=lambda r: r["entity_id"])
                     if not branch or _in_branch(r, branch)]
    return rows


def _body_of_group(rows) -> Dict[str, str]:
    return {g.get("entity_id"): g.get("body") for g in rows.get("RigidGroup") or []}


def _finding(kind, subjects, detail, owner=OWNER):
    return findings.Finding(kind=kind, owner=owner, subjects=tuple(subjects), detail=detail)


def _realized_by(rows) -> Dict[str, List[Dict[str, Any]]]:
    """target id -> the KinematicRealizations naming it. One reading of the
    claims, shared by every duty below."""
    out: Dict[str, List[Dict[str, Any]]] = {}
    for rec in rows.get(REALIZATION) or []:
        target = rec.get("realizes")
        if target:
            out.setdefault(target, []).append(rec)
    return out


def _covered_by(realization, features: Dict[str, str]) -> set:
    """The bodies ONE realization's participating features are on. Coverage is
    READ from the features' own `body`; a realization never restates it."""
    return {features.get(fid) for fid in (realization.get("participating_features") or [])
            if features.get(fid)}


def _single_claim(target: str, claims) -> Optional[Dict[str, Any]]:
    """THE realization of a target, or None when there is none or several.

    A KinematicRealization is a COMPLETE realization record, not a fragment: one
    per target in one committed branch, listing every participating feature. Two
    records each carrying one side of a relation are not a realization between
    them - each states an embodiment that does not embody, and reading them as a
    union means nothing in state ever has to be true on its own. Several rows
    are reported by `realization_claim_findings` and coverage is not judged for
    that target until it is one record again.
    """
    here = claims.get(target) or []
    return here[0] if len(here) == 1 else None


def _named_interfaces(feature: Dict[str, Any]) -> List[str]:
    """The interactions a feature says it realizes a side of.

    ONE READING, and it is a list. `Feature.interfaces` is a multi-reference
    because one physical feature can bear on several declared interactions;
    every reader goes through here so none of them re-decides that.
    """
    named = feature.get("interfaces")
    if isinstance(named, list):
        return [i for i in named if isinstance(i, str) and i]
    return [named] if isinstance(named, str) and named else []


def _feature_bodies(rows) -> Dict[str, str]:
    return {f.get("entity_id"): f.get("body") for f in rows.get("Feature") or []}


def joint_realization_findings(rows) -> List[findings.Finding]:
    """Every Joint is embodied by a KinematicRealization naming it, whose
    features cover each body the joint relates.

    WHAT IS ASKED IS COVERAGE, NOT SHAPE. No feature's axis is compared with the
    joint's and no joint class is named here: the geometry that embodies a
    relation need not be aligned with it. Three transverse pads on three recess
    walls guide a slide; two rails and two carriages embody one guided relation
    between them; a rod in a plain bore may leave axial rotation deliberately
    free. Every one of those is refused by an axis rule and is ordinary
    mechanical design.

    Several realizations of one joint are not a contradiction - they are how a
    relation carried by several elements is stated.
    """
    out: List[findings.Finding] = []
    features = _feature_bodies(rows)
    claims = _realized_by(rows)
    for duty in duty_manifest.from_rows(rows).joint_duties():
        jid, kind, sides = duty.target, duty.kind, list(duty.bodies)
        here = claims.get(jid) or []
        if not here:
            out.append(_finding(
                findings.JOINT_UNREALIZED, (jid,),
                "joint %s (%s) relates %s and no KinematicRealization names it; a joint_type "
                "label alone is inert and no placement stands in for the claim"
                % (jid, kind, ", ".join(sides))))
            continue
        claim = _single_claim(jid, claims)
        if claim is None:
            continue                    # fragmented; reported as its own defect
        covered = _covered_by(claim, features)
        missing = [side for side in sides if side not in covered]
        if missing:
            out.append(_finding(
                findings.REALIZATION_UNCOVERED, tuple([jid] + missing),
                "joint %s (%s) is claimed by %s, whose participating features are on %s and "
                "none on %s; ONE realization carries every side the relation relates"
                % (jid, kind, claim.get("entity_id"),
                   ", ".join(sorted(b for b in covered)) or "no body of the branch",
                   ", ".join(missing))))
    return out


def restraint_realization_findings(rows) -> List[findings.Finding]:
    """Every ConstraintRelation that blocks something is embodied by a
    KinematicRealization naming it, covering the sides it acts between.

    `blocked_dofs` is what makes a relation a block; one that blocks nothing is
    a recorded relationship, not something geometry has to produce. WHICH DOFs
    are blocked, in which configurations, and how a test would defeat it stay
    the relation's own - this asks only that the material exists.

    WHICH SIDES, BY THE RELATION'S OWN PROVIDER MODEL:

      the RETAINED side always. The product material that is held is this
      design's, whatever holds it, so the body owning `retained_group` must be
      represented.

      the PROVIDER BODY when there is one - a body of this design provides the
      restraint, and material on it is what does the providing.

      NOTHING for an external provider. `provider_reaction_site` names a
      ReactionSiteRequirement: the thing bearing the load is outside this
      design's body set, and demanding a Feature for it would force s05 to
      invent a body that is not the product. That relation is upstream's and
      stays authoritative for its side.

    NO FEATURE KIND IS CONSULTED. The predecessor of this check asked whether a
    side carried a feature whose kind was spelled STOP, SHOULDER or KEEPER,
    which is a claim about a word: a face named STOP restrains nothing by being
    named, and a restraint realized by a rib, a wall or a pocket floor was
    refused for being spelled otherwise. A MobilityExpectation already names the
    authoritative relation; this is its embodiment.
    """
    out: List[findings.Finding] = []
    features = _feature_bodies(rows)
    claims = _realized_by(rows)
    for duty in duty_manifest.from_rows(rows).restraint_duties():
        rid, sides = duty.target, list(duty.bodies)
        here = claims.get(rid) or []
        if not here:
            out.append(_finding(
                findings.RESTRAINT_UNREALIZED, (rid,),
                "constraint relation %s blocks %s and no KinematicRealization names it; the "
                "restraint is stated and nothing embodies it%s"
                % (rid, ", ".join(duty.blocked_dofs),
                   " (its provider is the external reaction site %s, so only the retained side "
                   "is owed material here)" % duty.external_provider
                   if duty.external_provider else "")))
            continue
        claim = _single_claim(rid, claims)
        if claim is None:
            continue                    # fragmented; reported as its own defect
        covered = _covered_by(claim, features)
        missing = [side for side in sides if side not in covered]
        if missing:
            out.append(_finding(
                findings.REALIZATION_UNCOVERED, tuple([rid] + missing),
                "constraint relation %s is claimed by %s, whose participating features are on "
                "%s and none on %s; a surface blocks nothing it is not touching"
                % (rid, claim.get("entity_id"),
                   ", ".join(sorted(b for b in covered)) or "no body of the branch",
                   ", ".join(missing))))
    return out


def realization_findings(rows) -> List[findings.Finding]:
    """Both kinematic duties, and the claims' own coherence."""
    return (realization_claim_findings(rows) + joint_realization_findings(rows)
            + restraint_realization_findings(rows))


def realization_claim_findings(rows) -> List[findings.Finding]:
    """A claim names a relation this branch carries and material that exists."""
    out: List[findings.Finding] = []
    targets = {r.get("entity_id") for r in (rows.get("Joint") or [])}
    targets |= {r.get("entity_id") for r in (rows.get("ConstraintRelation") or [])}
    features = _feature_bodies(rows)
    claims = _realized_by(rows)
    for rec in sorted(rows.get(REALIZATION) or [], key=lambda x: x.get("entity_id") or ""):
        rid = rec.get("entity_id")
        target = rec.get("realizes")
        if target not in targets:
            out.append(_finding(
                findings.JOINT_UNREALIZED, (rid, str(target)),
                "realization %s names %s, which is no Joint or ConstraintRelation of this "
                "branch; what is embodied is s03's to declare" % (rid, target)))
        participating = rec.get("participating_features") or []
        if not participating:
            out.append(_finding(
                findings.REALIZATION_UNCOVERED, (rid,),
                "realization %s names no participating feature; a relation embodied by no "
                "material is a label" % rid))
        for fid in participating:
            if fid not in features:
                out.append(_finding(
                    findings.FEATURE_OFF_BRANCH, (rid, str(fid)),
                    "realization %s names feature %s, which is no feature of this branch"
                    % (rid, fid)))
    for target, here in sorted(claims.items()):
        if len(here) > 1:
            out.append(_finding(
                findings.REALIZATION_FRAGMENTED, tuple([target] + sorted(
                    str(r.get("entity_id")) for r in here)),
                "%s is claimed by %s; a KinematicRealization is a COMPLETE realization record, "
                "not a fragment - one per relation in a branch, listing every participating "
                "feature. Two records each carrying one side embody nothing on their own, and "
                "reading them as a union means no record in state has to be true by itself"
                % (target, ", ".join(sorted(str(r.get("entity_id")) for r in here)))))
    return out


def body_material_findings(rows) -> List[findings.Finding]:
    """Every body of the branch has at least one additive feature; every
    feature is on a body of the branch."""
    out: List[findings.Finding] = []
    polarity = polarity_table()
    manifest = duty_manifest.from_rows(rows)
    bodies = set(manifest.bodies)
    additive: Dict[str, int] = {}
    for f in rows.get("Feature") or []:
        body = f.get("body")
        if body not in bodies:
            out.append(_finding(
                findings.FEATURE_OFF_BRANCH, (f.get("entity_id"), body),
                "feature %s is on %s, which is no body of the branch" % (f.get("entity_id"), body)))
            continue
        if polarity.get(str(f.get("feature_kind", "")).upper()) == "ADDITIVE":
            additive[body] = additive.get(body, 0) + 1
    for bid in manifest.bodies:
        if not additive.get(bid):
            out.append(_finding(
                findings.BODY_WITHOUT_MATERIAL, (bid,),
                "body %s has no additive feature (no STOCK, boss, rib ...); nothing gives it "
                "material" % bid))
    return out


def mating_kind_findings(rows) -> List[findings.Finding]:
    """A mating side s04 stated is realized by a feature of the stated kind."""
    out: List[findings.Finding] = []
    features = rows.get("Feature") or []
    for duty in duty_manifest.from_rows(rows).interfaces:
        iid = duty.interface
        for body, kind in duty.mating:
            here = [f for f in features
                    if iid in _named_interfaces(f) and f.get("body") == body]
            if not here:
                continue        # interface_realization_findings reports the missing side
            if not any(str(f.get("feature_kind", "")).upper() == kind for f in here):
                out.append(_finding(
                    findings.MATING_KIND_UNREALIZED, (iid, body),
                    "interface %s states a %s side on %s; the feature(s) realizing that side "
                    "are %s"
                    % (iid, kind, body,
                       ", ".join(sorted("%s(%s)" % (f["entity_id"], f.get("feature_kind"))
                                        for f in here)))))
    return out


#: s03's clearance vocabulary: CONTACT, CLEARANCE, INTERFERENCE_FIT,
#: COMPLIANT_INTERACTION. A clearance and an interference fit are the two whose
#: geometry is a NUMBER someone must own.
CLEARANCE_KINDS = ("CLEARANCE", "INTERFERENCE_FIT")


def interface_realization_findings(rows) -> List[findings.Finding]:
    """Every Interface has a Feature on EACH participant body. No exception.

    A previous version admitted one: an Interface between two bodies could skip
    a feature on one side if some COMPLIANT joint connected the same pair. That
    was wrong twice. It contradicted the ontology - compliance is INTERNAL,
    between RigidGroups of ONE body, so a joint spanning the pair was not the
    thing the exception described but a malformed record, and the exception
    admitted it as justification for omitting geometry. And it contradicted the
    Joint contract's own unconditional rule: "A joint_type label alone is inert.
    A realization on each side is required (INV-008)." Two bodies that touch
    need two features; a flexure is geometry on its own body and gets a feature
    like anything else. The malformed cross-body COMPLIANT joint is reported -
    as s03's, since the Joint record is s03's to correct - so the record that
    used to excuse a missing feature is now the thing that fails.

    THE TRACE IS TYPED. A feature says which interface it realizes a side of; a
    body merely having SOME feature proves nothing about an interface. An
    interface the branch does not carry may not be named - an interaction is
    s03's to declare - and a body the interface does not involve cannot realize
    a side of it.

    WHAT THIS DOES NOT PROVE: that a compliant element exists as the geometry a
    reduced-order beam model would consume. `compliant_element` is untyped prose
    and nothing canonical ties it to a Feature id; inferring it from the text
    would be reading a model's sentence as a structural fact.
    """
    out: List[findings.Finding] = []
    groups = _body_of_group(rows)
    for joint in sorted(rows.get("Joint") or [], key=lambda x: x.get("entity_id") or ""):
        if str(joint.get("joint_type", "")).upper() != "COMPLIANT":
            continue
        parent, child = groups.get(joint.get("parent_group")), groups.get(joint.get("child_group"))
        if parent and child and parent != child:
            out.append(_finding(
                findings.COMPLIANT_JOINT_MALFORMED, (joint.get("entity_id"), parent, child),
                "joint %s is COMPLIANT but connects groups on two different bodies (%s and %s); "
                "compliance is a relation between rigid groups of ONE body"
                % (joint.get("entity_id"), parent, child),
                owner="s03"))

    manifest = duty_manifest.from_rows(rows)
    interfaces = {i.get("entity_id"): i for i in rows.get("Interface") or []}
    realized: Dict[str, set] = {}
    for f in rows.get("Feature") or []:
        for named in _named_interfaces(f):
            iface = interfaces.get(named)
            if iface is None:
                out.append(_finding(
                    findings.INTERFACE_NOT_CARRIED, (f.get("entity_id"), named),
                    "feature %s names interface %s, which the selected branch does not carry; "
                    "an interaction is s03's to declare and none may be invented here"
                    % (f.get("entity_id"), named)))
                continue
            if f.get("body") not in (iface.get("bodies") or []):
                out.append(_finding(
                    findings.INTERFACE_BODY_MISMATCH, (f.get("entity_id"), f.get("body"), named),
                    "feature %s on %s names interface %s, which does not involve that body"
                    % (f.get("entity_id"), f.get("body"), named)))
                continue
            realized.setdefault(named, set()).add(f.get("body"))
    for duty in manifest.interfaces:
        for body in [b for b in duty.bodies if b not in realized.get(duty.interface, set())]:
            out.append(_finding(
                findings.INTERFACE_SIDE_UNREALIZED, (duty.interface, body),
                "interface %s involves body %s and no feature naming that interface realizes "
                "that side" % (duty.interface, body)))
    return out


def clearance_governance_findings(rows) -> List[findings.Finding]:
    """Every declared clearance or interference fit has a Constraint naming it.

    Per interface and by TYPED REFERENCE. `Constraint.governs_interface` is a
    declared reference to the Interface whose clearance the constraint expresses,
    so the link is something production emits and DesignState validates rather
    than something a test injects - an earlier version looked for `interface` and
    `realizes` keys that no contract declares, which made the link set
    permanently empty.

    The recorded history is the argument for per-interface rather than in
    aggregate: a clearance never given to the settlement loop produced a BUILD
    FAILURE patched by hand instead of an INFEASIBILITY that triggered a
    re-solve, and a regression rode along undetected for three revisions. One
    constraint cannot speak for five clearances.
    """
    governed = {c.get("governs_interface") for c in rows.get("Constraint") or []
                if str(c.get("kind", "")).upper() in ("CLEARANCE", "INTERFERENCE_FREE")
                and c.get("governs_interface")}
    out: List[findings.Finding] = []
    for duty in duty_manifest.from_rows(rows).interfaces:
        if not duty.needs_governing_constraint:
            continue
        if duty.interface not in governed:
            out.append(_finding(
                findings.CLEARANCE_UNGOVERNED, (duty.interface,),
                "interface %s declares %s and no Constraint governs it"
                % (duty.interface, duty.interaction_kind)))
    return out


def prerequisite_findings(rows: Dict[str, List[Dict[str, Any]]]) -> List[findings.Finding]:
    """THE MANDATORY PREREQUISITES OF AN EMBODIMENT, in one place and typed.

    These are the questions s05 asks of its response before it writes and s06's
    entry gate asks of what stands - the same functions over the same rows, so a
    duty cannot be enforced at one surface and absent at the other. That split
    is exactly how a branch came to be settled while its own producing stage had
    declared an interface unrealized: the duty was computed over the response
    and never over the state, and the numbers were settled for geometry that did
    not exist.

    EACH ONE IS A TYPED FINDING WITH AN OWNER, because it is routed, not only
    reported: what s05 owns goes back to s05 as a STRUCTURAL revision - geometry
    the design committed to and the embodiment does not contain - and what
    another stage owns (a malformed Joint is s03's record) escalates instead.
    Neither is an infeasibility: nothing here is a number to adjust.

    NOTHING HERE IS DEFERRABLE TODAY. A prerequisite may be waived only by a
    contract that says so in writing (S06_CONTRACT `settlement_entry.deferral`),
    and no deferral is declared. Numeric closure is NOT among these: an
    infeasible or underdetermined system is what the s06 -> s05 settlement loop
    exists to repair, and refusing entry for it would deny the loop the report
    it repairs from.
    """
    return (realization_findings(rows) + body_material_findings(rows)
            + mating_kind_findings(rows) + interface_realization_findings(rows)
            + clearance_governance_findings(rows) + free_space_findings(rows))


def free_space_findings(rows) -> List[findings.Finding]:
    """A region whose declared role means FREE SPACE is cleared by material
    that removes material, at that region.

    THE STRUCTURAL HALF of the spatial duty, asked of what stands - the same
    question s05 asks of its response. Whether the volume is ACTUALLY clear is
    settled geometry's to answer (`FEATURE_OUTSIDE_REGION`, over the compiled
    solid); this asks only whether the embodiment contains a route to it, which
    is the difference between a design that might work and one that cannot.

    NO ROLE IS NAMED HERE. `excludes_occupancy` is the contract's own table.
    """
    out: List[findings.Finding] = []
    polarity = polarity_table()
    for duty in duty_manifest.from_rows(rows).free_space_regions():
        for body in duty.owning_bodies:
            clearing = [f for f in rows.get("Feature") or []
                        if f.get("body") == body
                        and (f.get("placement") or {}).get("datum") == duty.region
                        and polarity.get(str(f.get("feature_kind", "")).upper()) == "SUBTRACTIVE"]
            if not clearing:
                out.append(_finding(
                    findings.EMBODIMENT_INCOMPLETE, (duty.region, body),
                    "region %s is a %s of %s, so that volume must be FREE of its material, and "
                    "no feature of %s removes material at it; an envelope is a bounding extent "
                    "and a region inside it is not cleared by being unmentioned"
                    % (duty.region, duty.role, body, body)))
    return out


def structural_problems(rows: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """`prerequisite_findings` as the sentences a refusal is read in. The
    typed findings are the fact; this is how they are shown."""
    return ["EMBODIMENT: " + f.detail for f in prerequisite_findings(rows)]
