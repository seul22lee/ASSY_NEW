"""S04 review figures: the spatial and kinematic state consumed downstream.

WHAT S04 OWNS IS WHAT IS DRAWN. Envelopes, functional regions, joint frames,
states, transitions and swept occupancy - each an axis-aligned box, a point or
an axis the arrangement actually committed. No detailed physical feature is
reconstructed here, because s04 does not own one.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import canvas as C


def _by_id(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {r.get("entity_id"): r for r in rows or []}


def _extent(entities: Dict[str, List[Dict[str, Any]]]):
    """The drawing extent, from every box the state declares."""
    los, his = [], []
    for family in ("Envelope", "FunctionalRegion", "SweptVolume"):
        for rec in entities.get(family) or []:
            got = C.box_of(rec)
            if got:
                los.append(got[0]); his.append(got[1])
    for rec in entities.get("Joint") or []:
        origin = rec.get("frame_origin")
        if isinstance(origin, (list, tuple)) and len(origin) == 3:
            los.append([float(c) for c in origin]); his.append([float(c) for c in origin])
    if not los:
        return [-1, -1, -1], [1, 1, 1]
    lo = [min(p[i] for p in los) for i in range(3)]
    hi = [max(p[i] for p in his) for i in range(3)]
    pad = [max(1.0, (hi[i] - lo[i]) * 0.12) for i in range(3)]
    return [lo[i] - pad[i] for i in range(3)], [hi[i] + pad[i] for i in range(3)]


def _body_of(entities, envelope_or_region: Dict[str, Any]) -> str:
    body = envelope_or_region.get("body")
    if body:
        return body
    owners = envelope_or_region.get("owning_bodies") or []
    return owners[0] if owners else ""


def _basis_note(entities) -> str:
    scales = entities.get("ReferenceScale") or []
    if not scales:
        return "no ReferenceScale stands: the numbers below carry no declared basis"
    s = scales[0]
    return ("ReferenceScale %s: basis %s%s - every coordinate below is in that basis and is "
            "DIMENSIONLESS, not millimetres" % (s.get("entity_id"), s.get("basis"),
             "" if s.get("basis") != "ABSOLUTE" else " (%s)" % s.get("absolute")))


# ==========================================================================
def spatial_layout(entities: Dict[str, List[Dict[str, Any]]], path: str,
                   branch: str = "") -> str:
    """Bodies, envelopes, functional regions, joint origins, arrangement axes."""
    envelopes = entities.get("Envelope") or []
    regions = entities.get("FunctionalRegion") or []
    joints = entities.get("Joint") or []
    groups = entities.get("RigidGroup") or []
    bodies = entities.get("Body") or []
    lo, hi = _extent(entities)

    fig = C.figure("S04 - spatial layout", C.CANONICAL,
                   "branch %s | %s" % (branch, _basis_note(entities)),
                   figsize=(15.5, 10.6))
    for i in range(3):
        ax, h, v = C.plane_axes(fig, [0.045 + i * 0.315, 0.455, 0.26, 0.44], i)
        ax.set_xlim(lo[h], hi[h]); ax.set_ylim(lo[v], hi[v])
        for env in envelopes:
            got = C.box_of(env)
            if not got:
                continue
            body = _body_of(entities, env)
            C.draw_box(ax, got[0], got[1], h, v, C.colour_for(body),
                       "%s\n%s" % (env.get("entity_id"), body), alpha=0.10)
        for reg in regions:
            got = C.box_of(reg)
            if not got:
                continue
            C.draw_box(ax, got[0], got[1], h, v, "#8a4fa0", reg.get("entity_id"),
                       style="dashed", alpha=0.07, lw=1.1, fontsize=6.5)
        for index, jnt in enumerate(joints):
            origin = jnt.get("frame_origin")
            if not (isinstance(origin, (list, tuple)) and len(origin) == 3):
                continue
            ax.plot([origin[h]], [origin[v]], marker="D", markersize=6.5,
                    color=C.WARN, zorder=6)
            ax.annotate(str(jnt.get("entity_id")), (origin[h], origin[v]),
                        textcoords="offset points", xytext=(7, 5 + 9 * (index % 3)),
                        fontsize=6.8, color=C.WARN, zorder=7,
                        bbox=dict(facecolor=C.PAPER, edgecolor="none", alpha=0.7, pad=0.6))
        if i == 0:
            C.legend(ax, [("Envelope (body)", C.colour_for(bodies[0].get("entity_id")) if bodies else C.INK),
                          ("FunctionalRegion", "#8a4fa0"),
                          ("Joint frame_origin", C.WARN)], loc="lower left")

    rows: List = []
    rows.append(("BODIES AND RIGID GROUPS", {"fontweight": "bold", "color": C.INK}))
    for b in bodies:
        bid = b.get("entity_id")
        members = [g.get("entity_id") for g in groups if g.get("body") == bid]
        rows.append(("  %-9s %s" % (bid, ", ".join(members) or "(no group)"),
                     {"color": C.colour_for(bid)}))
        for line in C.wrap(str(b.get("role") or ""), 96)[:2]:
            rows.append(("      " + line, {"color": C.MUTED, "fontsize": 7.2}))
    rows.append(("", {}))
    rows.append(("ENVELOPES  (id / body / maturity / centre / half_extent)",
                 {"fontweight": "bold", "color": C.INK}))
    for env in envelopes:
        ext = env.get("extent") or {}
        rows.append(("  %-9s %-9s %-12s c=%-18s h=%s"
                     % (env.get("entity_id"), _body_of(entities, env),
                        env.get("maturity") or "-", ext.get("centre"), ext.get("half_extent")),
                     {"color": C.colour_for(_body_of(entities, env)), "fontsize": 7.4}))
    rows.append(("", {}))
    rows.append(("FUNCTIONAL REGIONS  (id / role / owning bodies / centre / half_extent)",
                 {"fontweight": "bold", "color": C.INK}))
    for reg in regions:
        vol = reg.get("volume") or {}
        rows.append(("  %-9s %-10s %-20s c=%-16s h=%s"
                     % (reg.get("entity_id"), reg.get("role") or "-",
                        ",".join(reg.get("owning_bodies") or []) or "(ownerless)",
                        vol.get("centre"), vol.get("half_extent")),
                     {"color": "#8a4fa0", "fontsize": 7.4}))
    C.text_panel(fig, [0.045, 0.04, 0.93, 0.355], rows, fontsize=7.4, leading=0.050)
    C.note(fig, "Envelopes and regions are the PROVISIONAL arrangement s04 committed, drawn "
                "as the axis-aligned boxes the state declares. Nothing here is CAD.")
    return C.save(fig, path)


# ==========================================================================
def joint_frames(entities: Dict[str, List[Dict[str, Any]]], path: str,
                 branch: str = "") -> str:
    """Every Joint: id, type, the bodies it relates, its located origin, its axis.

    A joint that declares no axis is drawn as a location only and SAID to be
    one. Nothing is drawn along an axis the state does not state.
    """
    joints = entities.get("Joint") or []
    groups = _by_id(entities.get("RigidGroup") or [])
    envelopes = entities.get("Envelope") or []
    states = entities.get("State") or []
    lo, hi = _extent(entities)
    span = max(hi[i] - lo[i] for i in range(3))
    arm = span * 0.16

    def body_of_group(gid):
        return (groups.get(gid) or {}).get("body") or "?"

    fig = C.figure("S04 - joint frames", C.CANONICAL,
                   "branch %s | a datum LOCATES; an axis ORIENTS. A joint with "
                   "axis_direction NONE has no orientation to lend." % branch,
                   figsize=(15.5, 8.6))
    for i in range(2):
        ax, h, v = C.plane_axes(fig, [0.05 + i * 0.34, 0.50, 0.29, 0.36], i)
        ax.set_xlim(lo[h], hi[h]); ax.set_ylim(lo[v], hi[v])
        for env in envelopes:
            got = C.box_of(env)
            if got:
                C.draw_box(ax, got[0], got[1], h, v, C.colour_for(_body_of(entities, env)),
                           "", alpha=0.055, lw=0.8, style="dotted")
        for index, jnt in enumerate(joints):
            origin = jnt.get("frame_origin")
            if not (isinstance(origin, (list, tuple)) and len(origin) == 3):
                continue
            colour = C.colour_by_index(index)
            ax.plot([origin[h]], [origin[v]], marker="D", markersize=7,
                    color=colour, zorder=6)
            axis = str(jnt.get("axis_direction") or "").strip().upper()
            direction = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0),
                         "-Y": (0, -1, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}.get(axis)
            if direction:
                C.arrow(ax, origin[h] - direction[h] * arm, origin[v] - direction[v] * arm,
                        origin[h] + direction[h] * arm, origin[v] + direction[v] * arm,
                        colour, lw=2.0)
            ax.annotate("%s %s" % (jnt.get("entity_id"), jnt.get("joint_type")),
                        (origin[h], origin[v]), textcoords="offset points",
                        xytext=(8, 6 + 11 * (index % 3)), fontsize=7.2, color=colour,
                        fontweight="bold", zorder=7,
                        bbox=dict(facecolor=C.PAPER, edgecolor="none", alpha=0.78, pad=0.8))
    coord_names = [s.get("entity_id") for s in states]
    rows: List = [("JOINT      TYPE       PARENT GROUP/BODY   CHILD GROUP/BODY    ORIGIN"
                   "               AXIS   FREE DOF        %s"
                   % "  ".join("%-13s" % n for n in coord_names),
                   {"fontweight": "bold", "color": C.INK, "fontsize": 7.0})]
    for jnt in joints:
        jid = jnt.get("entity_id")
        axis = str(jnt.get("axis_direction") or "NONE")
        coords = []
        for st in states:
            value = (st.get("joint_coordinates") or {}).get(jid)
            coords.append("%-13s" % ("-" if value is None else value))
        rows.append(("%-10s %-10s %-8s %-9s %-8s %-9s %-20s %-6s %-15s %s"
                     % (jid, jnt.get("joint_type"),
                        jnt.get("parent_group"), body_of_group(jnt.get("parent_group")),
                        jnt.get("child_group"), body_of_group(jnt.get("child_group")),
                        jnt.get("frame_origin"), axis,
                        ",".join(jnt.get("dof") or []) or "(none)",
                        "  ".join(coords)),
                     {"color": C.colour_by_index(joints.index(jnt)), "fontsize": 7.0}))
    rows.append(("", {}))
    rows.append(("STATE COORDINATE COLUMNS: %s"
                 % "; ".join("%s = %s" % (s.get("entity_id"), s.get("name")) for s in states),
                 {"color": C.MUTED, "fontsize": 7.2}))
    noaxis = [j.get("entity_id") for j in joints
              if str(j.get("axis_direction") or "NONE").upper() in ("NONE", "")]
    if noaxis:
        rows.append(("", {}))
        rows.append(("NO AXIS TO LEND: %s declare axis_direction NONE. Every S05 feature "
                     "placed at one of these MUST state its own axis."
                     % ", ".join(noaxis), {"color": C.WARN, "fontsize": 7.4}))
    C.text_panel(fig, [0.05, 0.055, 0.92, 0.375], rows, fontsize=7.0, leading=0.095)
    C.note(fig, "Joint frame_origin is s04's committed placement, in the ReferenceScale "
                "basis. Arrows are drawn only where the joint declares an axis_direction.")
    return C.save(fig, path)


# ==========================================================================
def states_and_motion(entities: Dict[str, List[Dict[str, Any]]], path: str,
                      branch: str = "") -> str:
    """The configurations, the transitions between them, and the swept occupancy.

    LABELLED FOR WHAT IT IS. The occupancy s04 owns is an AABB union over
    sampled poses; it is drawn as that and never as a shape.
    """
    configs = _by_id(entities.get("Configuration") or [])
    states = entities.get("State") or []
    transitions = entities.get("Transition") or []
    swept = entities.get("SweptVolume") or []
    reqs = _by_id(entities.get("TransitionRequirement") or [])
    envelopes = entities.get("Envelope") or []
    lo, hi = _extent(entities)

    order = {t.get("entity_id"): i for i, t in enumerate(transitions)}

    def tcolour(tid):
        return C.colour_by_index(order.get(tid, 0))

    fig = C.figure("S04 - states and motion", C.CANONICAL,
                   "branch %s | COARSE / SAMPLED SPATIAL EVIDENCE - NOT FINAL CAD"
                   % branch, figsize=(15.5, 10.2))
    fig.text(0.988, 0.972, "COARSE / SAMPLED SPATIAL EVIDENCE\nNOT FINAL CAD", fontsize=10,
             fontweight="bold", color="#8a5a00", ha="right", va="top",
             bbox=dict(facecolor="#fff6e0", edgecolor="#d9a441", pad=5))

    # ONE PANEL PER TRANSITION. Two transitions between the same pair of states
    # sweep the same box; drawn together one hides the other and the picture
    # would say a sweep is missing when it is not.
    shown = transitions or [None]
    width = 0.90 / max(len(shown), 1)
    for index, tr in enumerate(shown):
        tid = (tr or {}).get("entity_id")
        rect = [0.055 + index * width, 0.475, width - 0.055, 0.34]
        ax, h, v = C.plane_axes(fig, rect, 0, title=" ")
        ax.set_xlim(lo[h], hi[h]); ax.set_ylim(lo[v], hi[v])
        for env in envelopes:
            got = C.box_of(env)
            if got:
                C.draw_box(ax, got[0], got[1], h, v,
                           C.colour_for(_body_of(entities, env)), "", alpha=0.05,
                           lw=0.8, style="dotted")
        colour = tcolour(tid)
        for sv in swept:
            if sv.get("transition") != tid:
                continue
            got = C.box_of(sv)
            if got:
                C.draw_box(ax, got[0], got[1], h, v, colour, sv.get("rigid_group"),
                           style="dashdot", alpha=0.13, lw=1.5, fontsize=6.6)
        if tr is not None:
            req = reqs.get(tr.get("realizes_requirement")) or {}
            head = "%s   %s -> %s" % (tid, tr.get("from_state"), tr.get("to_state"))
            sub = "moving: %s   released: %s" % (
                ",".join((tr.get("path") or {}).get("moving_groups") or []) or "-",
                ",".join(req.get("released_constraints") or []) or "(none)")
            ax.set_title("%s\n%s" % (head, sub), fontsize=8.2, color=colour,
                         loc="left", fontweight="bold")
    C.legend(ax, [("swept occupancy (AABB of sampled poses)", C.MUTED),
                  ("Envelope (static)", C.RULE)], loc="lower left", fontsize=6.8)

    rows: List = [("CONFIGURATIONS AND STATES", {"fontweight": "bold", "color": C.INK})]
    for st in states:
        cfg = configs.get(st.get("configuration")) or {}
        rows.append(("  %-14s %-10s %-9s joint_coordinates=%s"
                     % (st.get("entity_id"), cfg.get("name") or st.get("name"),
                        cfg.get("kind") or "-", st.get("joint_coordinates")),
                     {"color": C.INK, "fontsize": 7.2}))
    rows.append(("", {}))
    rows.append(("TRANSITIONS  (transition / moving groups / start -> end / released / "
                 "required motions)", {"fontweight": "bold", "color": C.INK}))
    for tr in transitions:
        req = reqs.get(tr.get("realizes_requirement")) or {}
        motions = ", ".join("%s.%s" % (m.get("joint"), m.get("dof"))
                            for m in (req.get("required_relative_motions") or []))
        rows.append(("  %-10s %-28s %-14s -> %-14s released=%s"
                     % (tr.get("entity_id"),
                        ",".join((tr.get("path") or {}).get("moving_groups") or []),
                        tr.get("from_state"), tr.get("to_state"),
                        ",".join(req.get("released_constraints") or []) or "(none)"),
                     {"color": tcolour(tr.get("entity_id")), "fontsize": 7.2}))
        rows.append(("      required relative motions: %s" % (motions or "(none stated)"),
                     {"color": C.MUTED, "fontsize": 7.0}))
    rows.append(("", {}))
    rows.append(("SWEEP EVIDENCE  (swept volume / transition / group / fidelity / method / "
                 "samples)", {"fontweight": "bold", "color": C.INK}))
    for sv in swept:
        decl = sv.get("sampling_declaration") or {}
        rows.append(("  %-26s %-10s %-9s %-9s %-30s samples=%s interior=%s"
                     % (sv.get("entity_id"), sv.get("transition"), sv.get("rigid_group"),
                        sv.get("fidelity"), decl.get("method"), decl.get("samples"),
                        decl.get("interior_samples")),
                     {"color": tcolour(sv.get("transition")), "fontsize": 6.9}))
    C.text_panel(fig, [0.055, 0.045, 0.92, 0.375], rows, fontsize=7.2, leading=0.062)
    C.note(fig, "Occupancy is an AABB union over discrete sampled poses - s04's own "
                "declaration, shown verbatim. It is coarse spatial evidence, not a swept "
                "solid, and no detailed feature is reconstructed from it.")
    return C.save(fig, path)
