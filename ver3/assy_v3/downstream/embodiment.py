"""UNIT G. CAD-constructibility of an embodiment, as structural checks over
canonical rows.

S05 "complete" used to mean "some Feature and ConstructionStatement records
exist". A body with no program, a joint whose axis no feature places, a placed
feature no statement builds and a mating side of the wrong kind all passed -
and then s07 had nothing it could build, or built something unrelated to the
mechanism. These checks derive what must be embodied FROM UPSTREAM SEMANTICS
(joints, groups, interfaces and their mating geometry) and ask whether the
embodiment defines it. No mechanism class is named anywhere here.

ONE IMPLEMENTATION, TWO SURFACES. The rows may come from a model response
(s05 asks before it writes, so the findings carry the check's name in the
declared incompleteness) or from standing state (s06's entry gate asks the same
question of what actually stands). `rows_from_response` and `rows_from_state`
build the same shape; nothing below knows which it was given.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set

from . import ir

#: Joint classes that relate two bodies and need an axis realized on each.
#: FIXED joints attach bodies rigidly and need no axis; COMPLIANT joints are
#: internal to one body (the ontology's rule) and are realized as features of
#: that body, which S05-C1 already demands.
AXIS_REALIZING_JOINTS = ("REVOLUTE", "PRISMATIC", "HELICAL", "CYLINDRICAL", "SPHERICAL",
                         "PLANAR")


def rows_from_response(parsed: Dict[str, Any], view: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """The design as it would stand if the response were committed."""
    def records(items, extra=None):
        out = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            rec = dict(item)
            rec["entity_id"] = rec.get("entity_id") or rec.get("id")
            out.append(rec)
        return out
    rows = {fam: list(view.get(fam) or []) for fam in ("Body", "RigidGroup", "Joint", "Interface")}
    rows["Feature"] = records(parsed.get("features"))
    rows["ConstructionStatement"] = records(parsed.get("construction_statements"))
    return rows


def rows_from_state(state, branch: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    """The design as it stands, on one branch."""
    from .canonical_io import _in_branch

    rows: Dict[str, List[Dict[str, Any]]] = {}
    for fam in ("Body", "RigidGroup", "Joint", "Interface", "Feature", "ConstructionStatement"):
        rows[fam] = [r for r in sorted(state.standing(fam), key=lambda r: r["entity_id"])
                     if not branch or _in_branch(r, branch)]
    return rows


def _body_of_group(rows) -> Dict[str, str]:
    return {g.get("entity_id"): g.get("body") for g in rows.get("RigidGroup") or []}


def joint_realization_problems(rows) -> List[str]:
    """Every axis-bearing joint has, on each body it relates, ONE placed
    feature naming it, whose placement axis is the joint's declared axis."""
    out: List[str] = []
    groups = _body_of_group(rows)
    by_key: Dict[tuple, List[Dict[str, Any]]] = {}
    for f in rows.get("Feature") or []:
        if f.get("joint"):
            by_key.setdefault((f["joint"], f.get("body")), []).append(f)
    joint_ids = {j.get("entity_id") for j in rows.get("Joint") or []}
    for f in rows.get("Feature") or []:
        if f.get("joint") and f["joint"] not in joint_ids:
            out.append("EMBODIMENT: feature %s realizes joint %s, which the branch does not carry"
                       % (f.get("entity_id"), f["joint"]))
    for j in sorted(rows.get("Joint") or [], key=lambda x: x.get("entity_id") or ""):
        kind = str(j.get("joint_type", "")).upper()
        if kind not in AXIS_REALIZING_JOINTS:
            continue
        jid = j.get("entity_id")
        declared = str(j.get("axis_direction", "")).strip().upper()
        for body in sorted({groups.get(j.get("parent_group")), groups.get(j.get("child_group"))} - {None}):
            here = by_key.get((jid, body)) or []
            if not here:
                out.append("EMBODIMENT: joint %s (%s) has no feature on %s that realizes its "
                           "axis (a feature naming `joint` %s with a `placement`)"
                           % (jid, kind, body, jid))
                continue
            if len(here) > 1:
                out.append("EMBODIMENT: joint %s is realized by %d features on %s (%s); one "
                           "feature places a joint in a body"
                           % (jid, len(here), body, ", ".join(sorted(f["entity_id"] for f in here))))
            for f in here:
                node = f.get("placement")
                if node is None:
                    out.append("EMBODIMENT: feature %s realizes joint %s on %s and has no "
                               "placement; an axis nobody located cannot be built"
                               % (f["entity_id"], jid, body))
                    continue
                try:
                    placement = ir.Placement.parse(node, "feature %s placement" % f["entity_id"])
                except ir.IRError:
                    continue                    # the grammar refuses it by name elsewhere
                if declared and placement.axis != declared:
                    out.append("EMBODIMENT: feature %s realizes joint %s along %s; the joint's "
                               "declared axis is %s" % (f["entity_id"], jid, placement.axis, declared))
    return out


def body_program_problems(rows) -> List[str]:
    """Every body of the branch has a construction program with one terminal."""
    out: List[str] = []
    statements = [s for s in rows.get("ConstructionStatement") or []]
    parsed: List[ir.Statement] = []
    for s in statements:
        try:
            parsed.append(ir.Statement.parse(s))
        except ir.IRError:
            continue                            # refused by name at the boundary
    program = ir.ConstructionProgram(parsed)
    built = set(program.bodies())
    for b in sorted(rows.get("Body") or [], key=lambda x: x.get("entity_id") or ""):
        bid = b.get("entity_id")
        if bid not in built:
            out.append("EMBODIMENT: body %s has no construction statement; a body with no "
                       "program cannot be built" % bid)
        elif program.terminal_of(bid) is None:
            out.append("EMBODIMENT: body %s has no single terminal statement; the program does "
                       "not say which result IS the body" % bid)
    bodies = {b.get("entity_id") for b in rows.get("Body") or []}
    for bid in sorted(built - bodies):
        out.append("EMBODIMENT: statements build %s, which is no body of the branch" % bid)
    return out


def placed_feature_problems(rows) -> List[str]:
    """A placed feature is realized by at least one statement naming it - a
    frame nothing is built in places nothing."""
    out: List[str] = []
    realized = {s.get("feature") for s in rows.get("ConstructionStatement") or [] if s.get("feature")}
    for f in sorted(rows.get("Feature") or [], key=lambda x: x.get("entity_id") or ""):
        if f.get("placement") is not None and f["entity_id"] not in realized:
            out.append("EMBODIMENT: feature %s is placed and no construction statement names it; "
                       "nothing is built in its frame" % f["entity_id"])
    for s in rows.get("ConstructionStatement") or []:
        feat = s.get("feature")
        if feat and feat not in {f.get("entity_id") for f in rows.get("Feature") or []}:
            out.append("EMBODIMENT: statement %s realizes %s, which is no feature"
                       % (s.get("entity_id"), feat))
    return out


def mating_kind_problems(rows) -> List[str]:
    """Where s04 stated a mating pair (inner/outer feature kinds and bodies),
    the features realizing that interface are of those kinds, on those bodies."""
    out: List[str] = []
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
                continue                        # S05-C1 reports the missing side
            if not any(str(f.get("feature_kind", "")).upper() == kind for f in here):
                out.append("EMBODIMENT: interface %s states a %s %s on %s; the feature(s) "
                           "realizing that side are %s"
                           % (iid, kind, side, body,
                              ", ".join(sorted("%s(%s)" % (f["entity_id"], f.get("feature_kind"))
                                               for f in here))))
    return out


def structural_problems(rows: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """Everything CAD needs the embodiment to define, in one list."""
    return (joint_realization_problems(rows) + body_program_problems(rows)
            + placed_feature_problems(rows) + mating_kind_problems(rows))
