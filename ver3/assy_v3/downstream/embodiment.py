"""UNIT G. CAD-constructibility of an embodiment, as structural checks over
canonical rows.

What must be embodied is DERIVED FROM UPSTREAM: every body needs material
(at least one additive feature); every axis-bearing joint is realized on each
body it relates by a feature placed AT that joint; a mating side s04 stated
is realized by a feature of the stated kind. Nothing names a mechanism class.

ONE IMPLEMENTATION, TWO SURFACES: s05 asks these of its response before it
writes (the findings carry the check's name), and s06's entry gate asks them
of what stands. The feature grammar itself - placement, construction, one
terminal - is the IR's and is refused at the write boundary; these checks
assume records that read.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import findings, ir

#: Whose decision an unmet prerequisite is, unless the record at fault is
#: another stage's: the embodiment is s05's to author.
OWNER = "s05"

AXIS_REALIZING_JOINTS = ("REVOLUTE", "PRISMATIC", "HELICAL", "CYLINDRICAL", "SPHERICAL",
                         "PLANAR")


def polarity_table() -> Dict[str, str]:
    """feature kind -> ADDITIVE | SUBTRACTIVE, from the canonical contract."""
    from ..state.design_state import Contracts
    table = (Contracts().families.get("Feature") or {}).get("feature_kind_polarity") or {}
    return {str(kind).upper(): pol for pol, kinds in table.items() for kind in (kinds or [])}


def rows_from_response(parsed: Dict[str, Any], view: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """The response as canonical rows: what the design decided (from the view)
    and what this response proposes (features and the constraints that govern
    them). Both surfaces below read exactly these keys."""
    rows = {fam: list(view.get(fam) or []) for fam in ("Body", "RigidGroup", "Joint", "Interface")}
    for family, key in (("Feature", "features"), ("Constraint", "constraints")):
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
    for fam in ("Body", "RigidGroup", "Joint", "Interface", "Feature", "Constraint"):
        rows[fam] = [r for r in sorted(state.standing(fam), key=lambda r: r["entity_id"])
                     if not branch or _in_branch(r, branch)]
    return rows


def _body_of_group(rows) -> Dict[str, str]:
    return {g.get("entity_id"): g.get("body") for g in rows.get("RigidGroup") or []}


def _finding(kind, subjects, detail, owner=OWNER):
    return findings.Finding(kind=kind, owner=owner, subjects=tuple(subjects), detail=detail)


def joint_realization_findings(rows) -> List[findings.Finding]:
    """Every axis-bearing joint is realized, on each body it relates, by at
    least one feature placed AT it AND LYING ON ITS AXIS.

    Realization is read from the placement; nothing restates it. A slide may be
    carried by rails, guides and stops - several features at one joint on one
    body are several realizations, not a contradiction.

    ON ITS AXIS is the whole of the second half. A joint datum locates a feature
    and does not orient it: a feature may be placed at the joint and state an
    axis of its own, meaning "located here, oriented otherwise" - a face whose
    normal crosses the hinge line, a keeper that retains along it. Such a
    feature is positioned by the joint and does NOT embody it, and counting it
    as a realization would let a branch satisfy this duty with geometry that
    cannot turn: the bore that makes the hinge a hinge would still be missing
    while the check reported the joint realized. A feature that states no axis
    takes the joint's, and does realize it.
    """
    out: List[findings.Finding] = []
    groups = _body_of_group(rows)
    at_joint: Dict[tuple, List[tuple]] = {}
    for f in rows.get("Feature") or []:
        placement = f.get("placement") if isinstance(f.get("placement"), dict) else {}
        datum = placement.get("datum")
        if datum:
            at_joint.setdefault((datum, f.get("body")), []).append(
                (f.get("entity_id"), placement.get("axis")))
    for j in sorted(rows.get("Joint") or [], key=lambda x: x.get("entity_id") or ""):
        kind = str(j.get("joint_type", "")).upper()
        if kind not in AXIS_REALIZING_JOINTS:
            continue
        jid = j.get("entity_id")
        axis = str(j.get("axis_direction") or "").strip().upper()
        for body in sorted({groups.get(j.get("parent_group")), groups.get(j.get("child_group"))} - {None}):
            here = at_joint.get((jid, body)) or []
            # an omitted axis IS the joint's; a stated one must be it
            on_axis = [fid for fid, stated in here
                       if stated is None or str(stated).strip().upper() == axis]
            if on_axis:
                continue
            if here:
                out.append(_finding(
                    findings.JOINT_UNREALIZED, (jid, body),
                    "joint %s (%s) is along %s and the feature(s) placed at it on %s lie on "
                    "another axis (%s); one of them must lie on the joint's axis to realize it"
                    % (jid, kind, axis, body,
                       ", ".join(sorted("%s(%s)" % (fid, stated) for fid, stated in here)))))
            else:
                out.append(_finding(
                    findings.JOINT_UNREALIZED, (jid, body),
                    "joint %s (%s) has no feature on %s placed at it (a feature whose placement "
                    "datum is %s)" % (jid, kind, body, jid)))
    return out


def body_material_findings(rows) -> List[findings.Finding]:
    """Every body of the branch has at least one additive feature; every
    feature is on a body of the branch."""
    out: List[findings.Finding] = []
    polarity = polarity_table()
    bodies = {b.get("entity_id") for b in rows.get("Body") or []}
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
    for bid in sorted(bodies):
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
    for i in sorted(rows.get("Interface") or [], key=lambda x: x.get("entity_id") or ""):
        mg = i.get("mating_geometry")
        if not isinstance(mg, dict):
            continue
        iid = i.get("entity_id")
        for side in ("inner", "outer"):
            body, kind = mg.get(side + "_body"), str(mg.get(side + "_feature") or "").upper()
            if not body or not kind:
                continue
            here = [f for f in features if f.get("interface") == iid and f.get("body") == body]
            if not here:
                continue        # interface_realization_findings reports the missing side
            if not any(str(f.get("feature_kind", "")).upper() == kind for f in here):
                out.append(_finding(
                    findings.MATING_KIND_UNREALIZED, (iid, body),
                    "interface %s states a %s %s on %s; the feature(s) realizing that side are %s"
                    % (iid, kind, side, body,
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

    interfaces = {i.get("entity_id"): i for i in rows.get("Interface") or []}
    realized: Dict[str, set] = {}
    for f in rows.get("Feature") or []:
        named = f.get("interface")
        if not named:
            continue
        iface = interfaces.get(named)
        if iface is None:
            out.append(_finding(
                findings.INTERFACE_NOT_CARRIED, (f.get("entity_id"), named),
                "feature %s names interface %s, which the selected branch does not carry; an "
                "interaction is s03's to declare and none may be invented here"
                % (f.get("entity_id"), named)))
            continue
        if f.get("body") not in (iface.get("bodies") or []):
            out.append(_finding(
                findings.INTERFACE_BODY_MISMATCH, (f.get("entity_id"), f.get("body"), named),
                "feature %s on %s names interface %s, which does not involve that body"
                % (f.get("entity_id"), f.get("body"), named)))
            continue
        realized.setdefault(named, set()).add(f.get("body"))
    for iid, iface in sorted(interfaces.items()):
        for body in [b for b in (iface.get("bodies") or []) if b and b not in realized.get(iid, set())]:
            out.append(_finding(
                findings.INTERFACE_SIDE_UNREALIZED, (iid, body),
                "interface %s involves body %s and no feature naming that interface realizes "
                "that side" % (iid, body)))
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
    for iface in sorted(rows.get("Interface") or [], key=lambda x: x.get("entity_id") or ""):
        if str(iface.get("interaction_kind", "")).upper() not in CLEARANCE_KINDS:
            continue
        if iface.get("entity_id") not in governed:
            out.append(_finding(
                findings.CLEARANCE_UNGOVERNED, (iface.get("entity_id"),),
                "interface %s declares %s and no Constraint governs it"
                % (iface.get("entity_id"), iface.get("interaction_kind"))))
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
    return (joint_realization_findings(rows) + body_material_findings(rows)
            + mating_kind_findings(rows) + interface_realization_findings(rows)
            + clearance_governance_findings(rows))


def structural_problems(rows: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """`prerequisite_findings` as the sentences a refusal is read in. The
    typed findings are the fact; this is how they are shown."""
    return ["EMBODIMENT: " + f.detail for f in prerequisite_findings(rows)]
