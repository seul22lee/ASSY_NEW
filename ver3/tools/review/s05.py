"""S05 review figures: the symbolic physical embodiment.

WHAT IS DRAWN IS WHAT WAS AUTHORED, AND THE FIGURE SAYS WHOSE IT IS. An S05
proposal that the write boundary refused is drawn under `RAW_MODEL` and stamped
REJECTED; only rows that stand in canonical state are drawn under `CANONICAL`.
The two are never mixed in one panel.

NOTHING IS SIZED THAT IS NOT SETTLED. S05 declares parameters without values -
that is its contract - so no extent below is drawn to scale. Features are drawn
at the DATUM they name, with the axis they state, labelled with the symbolic
expressions they carry. Anything else would be a picture of numbers nobody has
solved.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import canvas as C

UNREALIZED = C.WARN


# --------------------------------------------------------------- expressions
def expr_text(node: Any, symbols: Optional[Dict[str, str]] = None) -> str:
    """The IR expression as readable infix. One reading, no evaluation."""
    symbols = symbols or {}
    if not isinstance(node, dict):
        return "?"
    if node.get("ref") is not None:
        ref = node["ref"]
        sym = symbols.get(ref)
        return "%s(%s)" % (sym, ref) if sym else str(ref)
    if node.get("const") is not None:
        value = node["const"]
        text = ("%g" % value) if isinstance(value, (int, float)) else str(value)
        unit = node.get("unit")
        return "%s%s" % (text, "" if unit in (None, "1") else unit)
    op = node.get("op")
    args = node.get("args") or []
    if op == "-" and len(args) == 1:
        return "-%s" % expr_text(args[0], symbols)
    return "(%s)" % ((" %s " % op).join(expr_text(a, symbols) for a in args))


def expr_refs(node: Any) -> set:
    if not isinstance(node, dict):
        return set()
    if node.get("ref") is not None:
        return {node["ref"]}
    return {r for a in (node.get("args") or []) for r in expr_refs(a)}


def constraint_text(record: Dict[str, Any], symbols) -> str:
    expr = record.get("expression") or {}
    return "%s %s %s" % (expr_text(expr.get("lhs"), symbols), expr.get("relation") or "?",
                         expr_text(expr.get("rhs"), symbols))


def step_text(step: Dict[str, Any], symbols) -> str:
    params = step.get("parameters") or {}
    shown = ", ".join("%s=%s" % (k, expr_text(v, symbols)) for k, v in sorted(params.items()))
    operands = ",".join(step.get("operands") or [])
    axis = (" axis=%s" % step.get("axis")) if step.get("axis") else ""
    return "%-4s %-9s%s%s%s" % (step.get("id"), step.get("operation"),
                                (" <- %s" % operands) if operands else "",
                                axis, (" %s" % shown) if shown else "")


def symbols_of(parameters: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    return {p.get("id") or p.get("entity_id"): p.get("symbol") for p in parameters or []}


def terminals(feature: Dict[str, Any]) -> List[str]:
    """The steps nothing consumes. Exactly one IS the feature; the count is the
    fact that decides whether the record may enter state at all."""
    steps = feature.get("construction") or []
    consumed = {o for st in steps for o in (st.get("operands") or [])}
    return [st.get("id") for st in steps if st.get("id") not in consumed]


def _fid(record):
    return record.get("id") or record.get("entity_id")


def _polarity(kind: str, table: Dict[str, str]) -> str:
    return table.get(str(kind).upper(), "?")


def _banner(accepted: bool):
    return (C.CANONICAL if accepted else C.RAW_MODEL), (not accepted)


# ==========================================================================
def embodiment_overview(response: Dict[str, Any], entities: Dict[str, List[Dict[str, Any]]],
                        polarity: Dict[str, str], path: str, branch: str = "",
                        accepted: bool = False) -> str:
    """Body-centric: every body, every feature on it, and what each feature says."""
    features = response.get("features") or []
    symbols = symbols_of(response.get("parameters"))
    bodies = [b.get("entity_id") for b in entities.get("Body") or []]
    source, rejected = _banner(accepted)

    by_body: Dict[str, List[Dict[str, Any]]] = {b: [] for b in bodies}
    for f in features:
        by_body.setdefault(f.get("body") or "(no body)", []).append(f)

    def block(f):
        return 3 + max(len(f.get("construction") or []), 1)

    total = sum(1 + sum(block(f) for f in v) + 1 for v in by_body.values()) + 2
    height = 2.6 + 0.235 * total
    fig = C.figure("S05 - embodiment overview", source,
                   "branch %s | body-centric physical embodiment | %d features on %d bodies"
                   % (branch, len(features), len([b for b in by_body if by_body[b]])),
                   figsize=(16, min(height, 26)), rejected=rejected)
    ax = fig.add_axes([0.03, 0.02, 0.95, 0.855]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    step = 1.0 / max(total, 1)
    y = 1.0

    for body in sorted(by_body):
        colour = C.colour_for(body)
        role = next((b.get("role") for b in entities.get("Body") or []
                     if b.get("entity_id") == body), "")
        groups = [g.get("entity_id") for g in entities.get("RigidGroup") or []
                  if g.get("body") == body]
        ax.text(0.0, y, "%s   %s" % (body, ",".join(groups)), fontsize=10.5,
                fontweight="bold", color=colour, family="monospace", va="top")
        ax.text(0.20, y, C.wrap(str(role or ""), 120)[0], fontsize=8, color=C.MUTED, va="top")
        y -= step
        here = sorted(by_body[body], key=lambda f: str(_fid(f)))
        if not here:
            ax.text(0.03, y, "  (no feature: nothing gives this body material)",
                    fontsize=8.5, color=UNREALIZED, family="monospace", va="top")
            y -= step * 1.4
            continue
        for index, f in enumerate(here):
            last = index == len(here) - 1
            kind = f.get("feature_kind")
            pol = _polarity(kind, polarity)
            place = f.get("placement") or {}
            term = terminals(f)
            refs = sorted({r for st in (f.get("construction") or [])
                           for e in (st.get("parameters") or {}).values()
                           for r in expr_refs(e)}
                          | {r for e in (place.get("offset") or []) for r in expr_refs(e)})
            head = "  %s %-9s %-9s %-11s" % ("└──" if last else "├──", _fid(f), kind, pol)
            ax.text(0.0, y, head, fontsize=9, color=colour, family="monospace", va="top")
            ax.text(0.235, y, C.wrap(str(f.get("geometry") or ""), 92)[0], fontsize=8,
                    color=C.INK, va="top")
            y -= step
            offset = ", ".join(expr_text(e, symbols) for e in (place.get("offset") or [])) or "-"
            iface = f.get("interface")
            meta = ("      datum=%-10s axis=%-5s offset=[%s]   interface=%s"
                    % (place.get("datum") or "(none)", place.get("axis") or "(inherited)",
                       offset, iface or "(none - realizes an obligation, not an interface)"))
            ax.text(0.0, y, meta, fontsize=7.6,
                    color=C.INK if place.get("datum") else UNREALIZED,
                    family="monospace", va="top")
            y -= step
            steps = f.get("construction") or []
            bad = len(term) != 1
            if not steps:
                ax.text(0.0, y, "      steps: (none) <-- a feature that builds nothing is "
                                "not an embodiment", fontsize=7.4, color=UNREALIZED,
                        family="monospace", va="top")
                y -= step
            for si, st in enumerate(steps):
                ax.text(0.0, y, "      %s %s" % ("steps:" if si == 0 else "       ",
                                                 step_text(st, symbols)),
                        fontsize=7.4, color=C.INK, family="monospace", va="top")
                y -= step
            tail = ("terminal = %s" % term[0] if len(term) == 1 else
                    "%d UNCONSUMED STEPS %s  <-- REFUSED AT THE WRITE BOUNDARY: exactly one "
                    "result IS the feature" % (len(term), ", ".join(term)))
            ax.text(0.0, y, "      %s   |   parameter refs: %s" % (tail, ",".join(refs) or "-"),
                    fontsize=7.4, color=UNREALIZED if bad else C.MUTED,
                    family="monospace", va="top")
            y -= step
        y -= step * 0.5

    C.note(fig, "polarity is read from the contract's feature_kind_polarity table; a body is "
                "its ADDITIVE features fused with its SUBTRACTIVE features removed. "
                "Dimensions are symbolic - S06 owns every value.")
    return C.save(fig, path)


# ==========================================================================
def feature_map(response: Dict[str, Any], entities: Dict[str, List[Dict[str, Any]]],
                polarity: Dict[str, str], path: str, branch: str = "",
                accepted: bool = False) -> str:
    """Each feature at the datum it names, with the axis it states.

    NOT CAD, AND NOT TO SCALE. Every extent an S05 feature carries is a symbolic
    expression over unsettled parameters, so no glyph below is sized from one.
    What is spatially true here is the DATUM and the AXIS; both are drawn from
    committed s04 records and the feature's own placement.
    """
    from .s04 import _extent, _by_id

    features = response.get("features") or []
    symbols = symbols_of(response.get("parameters"))
    source, rejected = _banner(accepted)
    datums: Dict[str, Tuple[List[float], str]] = {}
    for family, field in (("Joint", "frame_origin"), ("Envelope", "extent"),
                          ("FunctionalRegion", "volume")):
        for rec in entities.get(family) or []:
            eid = rec.get("entity_id")
            if family == "Joint":
                origin = rec.get(field)
                if isinstance(origin, (list, tuple)) and len(origin) == 3:
                    datums[eid] = ([float(c) for c in origin], family)
            else:
                got = C.box_of(rec)
                if got:
                    datums[eid] = ([(got[0][i] + got[1][i]) / 2.0 for i in range(3)], family)
    joint_axis = {j.get("entity_id"): str(j.get("axis_direction") or "NONE").upper()
                  for j in entities.get("Joint") or []}
    lo, hi = _extent(entities)
    span = max(hi[i] - lo[i] for i in range(3))
    arm = span * 0.11
    vectors = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0),
               "-Y": (0, -1, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}

    fig = C.figure("S05 - feature map", source,
                   "branch %s | S05 SYMBOLIC EMBODIMENT - NOT S07 CAD" % branch,
                   figsize=(16, 10.5), rejected=rejected)
    fig.text(0.988, 0.905 if rejected else 0.972,
             "S05 SYMBOLIC EMBODIMENT\nNOT S07 CAD - NOTHING IS DRAWN TO SCALE",
             fontsize=10, fontweight="bold", color="#8a5a00", ha="right", va="top",
             bbox=dict(facecolor="#fff6e0", edgecolor="#d9a441", pad=5))

    unplaced: List[str] = []
    for i in range(2):
        ax, h, v = C.plane_axes(fig, [0.05 + i * 0.34, 0.47, 0.29, 0.36], i)
        ax.set_xlim(lo[h], hi[h]); ax.set_ylim(lo[v], hi[v])
        for env in entities.get("Envelope") or []:
            got = C.box_of(env)
            if got:
                C.draw_box(ax, got[0], got[1], h, v, C.colour_for(env.get("body")),
                           "", alpha=0.05, lw=0.8, style="dotted")
        seen: Dict[Tuple[float, float], int] = {}
        for f in sorted(features, key=lambda r: str(_fid(r))):
            place = f.get("placement") or {}
            datum = place.get("datum")
            spot = datums.get(datum)
            if spot is None:
                if i == 0 and _fid(f) not in unplaced:
                    unplaced.append(_fid(f))
                continue
            point, _family = spot
            colour = C.colour_for(f.get("body"))
            pol = _polarity(f.get("feature_kind"), polarity)
            key = (round(point[h], 3), round(point[v], 3))
            rank = seen.get(key, 0); seen[key] = rank + 1
            marker = "o" if pol == "ADDITIVE" else ("x" if pol == "SUBTRACTIVE" else "s")
            ax.plot([point[h]], [point[v]], marker=marker, markersize=8,
                    markerfacecolor="none" if pol != "ADDITIVE" else colour,
                    markeredgecolor=colour, markeredgewidth=1.8, zorder=6)
            axis = place.get("axis") or joint_axis.get(datum) or ""
            direction = vectors.get(str(axis).upper())
            if direction:
                C.arrow(ax, point[h], point[v], point[h] + direction[h] * arm,
                        point[v] + direction[v] * arm, colour, lw=1.5)
            ax.annotate("%s %s" % (_fid(f), f.get("feature_kind")), (point[h], point[v]),
                        textcoords="offset points", xytext=(9, 4 + 10 * (rank % 6)),
                        fontsize=6.6, color=colour, zorder=7,
                        bbox=dict(facecolor=C.PAPER, edgecolor="none", alpha=0.75, pad=0.6))
        if i == 0:
            C.legend(ax, [("ADDITIVE feature (at its datum)", C.INK),
                          ("SUBTRACTIVE feature (at its datum)", C.MUTED),
                          ("arrow = the axis the feature states", C.INK)],
                     loc="lower left", fontsize=6.6)

    rows: List = [("FEATURE    KIND      POL          BODY      DATUM      AXIS   "
                   "SYMBOLIC DIMENSIONS (S06 owns every value)",
                   {"fontweight": "bold", "color": C.INK, "fontsize": 7.2})]
    for f in sorted(features, key=lambda r: str(_fid(r))):
        place = f.get("placement") or {}
        dims = "; ".join(
            "%s=%s" % (k, expr_text(e, symbols))
            for st in (f.get("construction") or [])
            for k, e in sorted((st.get("parameters") or {}).items()))
        rows.append(("%-10s %-9s %-12s %-9s %-10s %-6s %s"
                     % (_fid(f), f.get("feature_kind"),
                        _polarity(f.get("feature_kind"), polarity), f.get("body"),
                        place.get("datum") or "(none)", place.get("axis") or "(inherit)",
                        C.wrap(dims, 96)[0] if dims else "-"),
                     {"color": C.colour_for(f.get("body")), "fontsize": 7.0}))
    if unplaced:
        rows.append(("", {}))
        rows.append(("NOT DRAWN: %s name a datum that is no committed spatial record of this "
                     "branch." % ", ".join(unplaced), {"color": UNREALIZED, "fontsize": 7.4}))
    C.text_panel(fig, [0.05, 0.035, 0.92, 0.39], rows, fontsize=7.0, leading=0.061)
    C.note(fig, "Positions are the committed s04 datum each feature NAMES. Extents are "
                "symbolic and unsettled and are deliberately not drawn. This is a "
                "semantic, pre-CAD picture.")
    return C.save(fig, path)


# ==========================================================================
def _node(ax, x, y, w, h, text, colour, fontsize=7.4, fill=0.10, lw=1.4,
          style="solid", weight="normal"):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.004",
                                facecolor=colour, edgecolor=colour, alpha=fill,
                                linewidth=0))
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.004",
                                facecolor="none", edgecolor=colour, linewidth=lw,
                                linestyle=style))
    ax.text(x + w / 2.0, y - h / 2.0, text, fontsize=fontsize, color=colour,
            ha="center", va="center", family="monospace", fontweight=weight)
    return (x, y - h / 2.0, x + w, y - h / 2.0)


def kinematic_realizations(response: Dict[str, Any],
                           entities: Dict[str, List[Dict[str, Any]]],
                           path: str, branch: str = "", accepted: bool = False) -> str:
    """Feature(s) -> KinematicRealization -> Joint | ConstraintRelation.

    EVERY TARGET THE DESIGN DECLARED IS DRAWN, realized or not. A joint or a
    blocking relation nothing names is the finding that stops s06, and a graph
    that showed only what was claimed would hide exactly that.
    """
    claims = response.get("kinematic_realizations") or []
    features = {_fid(f): f for f in response.get("features") or []}
    source, rejected = _banner(accepted)

    joints = entities.get("Joint") or []
    relations = [r for r in entities.get("ConstraintRelation") or []
                 if r.get("blocked_dofs")]
    targets: List[Tuple[str, str, str]] = []
    for j in joints:
        targets.append((j.get("entity_id"), "Joint",
                        "%s  %s/%s" % (j.get("joint_type"), j.get("parent_group"),
                                       j.get("child_group"))))
    for r in relations:
        targets.append((r.get("entity_id"), "ConstraintRelation",
                        "blocks %s  driver=%s  retained=%s"
                        % (",".join(r.get("blocked_dofs") or []), r.get("driver"),
                           r.get("retained_group"))))
    by_target: Dict[str, List[Dict[str, Any]]] = {}
    for k in claims:
        by_target.setdefault(k.get("realizes"), []).append(k)

    lanes = []
    for tid, family, detail in targets:
        here = by_target.get(tid) or []
        lanes.append((tid, family, detail, here))
    orphan = [k for k in claims if k.get("realizes") not in {t[0] for t in targets}]

    height = 2.4 + 0.62 * sum(max(1, sum(max(1, len(k.get("participating_features") or []))
                                         for k in here) if here else 1)
                              for _t, _f, _d, here in lanes) + 0.9 * len(lanes)
    fig = C.figure("S05 - kinematic realizations", source,
                   "branch %s | what geometry embodies which declared relation" % branch,
                   figsize=(16, min(max(height, 8), 26)), rejected=rejected)
    ax = fig.add_axes([0.03, 0.02, 0.95, 0.86]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    total = sum(max(1, sum(max(1, len(k.get("participating_features") or []))
                           for k in here)) + 1 for _t, _f, _d, here in lanes) + 2
    unit = 1.0 / max(total, 1)
    y = 1.0
    ax.text(0.045, y + unit * 0.6, "PARTICIPATING FEATURES", fontsize=8.5,
            fontweight="bold", color=C.MUTED, va="bottom")
    ax.text(0.44, y + unit * 0.6, "KinematicRealization", fontsize=8.5,
            fontweight="bold", color=C.MUTED, va="bottom")
    ax.text(0.70, y + unit * 0.6, "Joint | ConstraintRelation (declared upstream)",
            fontsize=8.5, fontweight="bold", color=C.MUTED, va="bottom")

    for tid, family, detail, here in lanes:
        rowspan = max(1, sum(max(1, len(k.get("participating_features") or []))
                             for k in here)) if here else 1
        block = rowspan * unit
        tcolour = C.colour_for(tid) if here else UNREALIZED
        mid = y - block / 2.0
        _node(ax, 0.70, mid + unit * 0.36, 0.28, unit * 0.62,
              "%s  %s" % (tid, family), tcolour, fontsize=8.0, lw=1.8,
              weight="bold", style="solid" if here else "dashed")
        ax.text(0.70, mid - unit * 0.44, "   " + detail, fontsize=6.9, color=C.MUTED,
                family="monospace", va="center")
        if not here:
            _node(ax, 0.44, mid + unit * 0.35, 0.20, unit * 0.7,
                  "NO REALIZATION", UNREALIZED, fontsize=7.6, lw=1.6, style="dashed",
                  weight="bold")
            C.arrow(ax, 0.64, mid, 0.70, mid, UNREALIZED, lw=1.4, ls="--")
            ax.text(0.045, mid, "nothing embodies this relation", fontsize=7.4,
                    color=UNREALIZED, family="monospace", va="center")
            y -= block + unit
            continue
        cursor = y
        for k in here:
            parts = k.get("participating_features") or []
            span = max(1, len(parts)) * unit
            kmid = cursor - span / 2.0
            _node(ax, 0.44, kmid + unit * 0.35, 0.20, unit * 0.7, _fid(k), tcolour,
                  fontsize=7.8, lw=1.6)
            C.arrow(ax, 0.64, kmid, 0.70, kmid, tcolour, lw=1.5)
            if not parts:
                ax.text(0.045, kmid, "(no participating feature named)", fontsize=7.4,
                        color=UNREALIZED, family="monospace", va="center")
            for pi, fid in enumerate(parts):
                f = features.get(fid)
                fy = cursor - unit * (pi + 0.5)
                colour = C.colour_for(f.get("body")) if f else UNREALIZED
                text = ("%s %s on %s" % (fid, f.get("feature_kind"), f.get("body"))
                        if f else "%s  <-- names no feature of this response" % fid)
                _node(ax, 0.045, fy + unit * 0.35, 0.33, unit * 0.7, text, colour,
                      fontsize=7.2, lw=1.3,
                      style="solid" if f else "dashed")
                C.arrow(ax, 0.375, fy, 0.44, kmid, colour, lw=1.2)
            cursor -= span
        y -= block + unit

    if orphan:
        ax.text(0.045, y, "CLAIMS NAMING NO DECLARED TARGET: %s"
                % ", ".join("%s -> %s" % (_fid(k), k.get("realizes")) for k in orphan),
                fontsize=7.6, color=UNREALIZED, family="monospace", va="top")
    C.note(fig, "A KinematicRealization carries no axis and no DOF list: the joint or the "
                "relation already states those. Coverage is read from each feature's own "
                "body, and a relation drawn dashed is one the design declared and nothing "
                "embodies.")
    return C.save(fig, path)


# ==========================================================================
def interfaces(response: Dict[str, Any], entities: Dict[str, List[Dict[str, Any]]],
               path: str, branch: str = "", accepted: bool = False,
               findings: Sequence[str] = ()) -> str:
    """Interface -> the two bodies -> the feature realizing each side.

    A side with no feature is drawn as UNREALIZED, because that is the
    prerequisite finding that refuses the embodiment.

    THE VERDICT IS PRODUCTION'S, NOT THIS FIGURE'S. `findings` is the
    deterministic structural-check output; any line naming an interface is
    printed against it verbatim. A constraint that merely NAMES an interface is
    shown as naming it - whether it GOVERNS it is the check's answer, and the
    two are not the same question.
    """
    features = response.get("features") or []
    constraints = response.get("constraints") or []
    symbols = symbols_of(response.get("parameters"))
    source, rejected = _banner(accepted)
    ifaces = entities.get("Interface") or []
    interactions = entities.get("PhysicalInteraction") or []

    governing: Dict[str, List[Dict[str, Any]]] = {}
    for c in constraints:
        if c.get("governs_interface"):
            governing.setdefault(c["governs_interface"], []).append(c)
    realizing: Dict[str, List[Dict[str, Any]]] = {}
    for f in features:
        if f.get("interface"):
            realizing.setdefault(f["interface"], []).append(f)

    lanes = len(ifaces) or 1
    fig = C.figure("S05 - interfaces", source,
                   "branch %s | which feature realizes each side of each declared interface"
                   % branch, figsize=(16, 2.6 + 2.45 * lanes), rejected=rejected)
    ax = fig.add_axes([0.03, 0.02, 0.95, 0.87]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    unit = 1.0 / max(lanes, 1)
    y = 1.0
    unrealized: List[str] = []

    for iface in ifaces:
        iid = iface.get("entity_id")
        bodies = list(iface.get("bodies") or [])
        mating = iface.get("mating_geometry") or {}
        here = realizing.get(iid) or []
        sides = {b: [f for f in here if f.get("body") == b] for b in bodies}
        missing = [b for b, fs in sides.items() if not fs]
        colour = UNREALIZED if missing else C.colour_for(iid)
        if missing:
            unrealized.append("%s (%s)" % (iid, ", ".join(missing)))
        top = y - unit * 0.06
        phi = [p for p in interactions if p.get("at_interface") == iid]
        _node(ax, 0.03, top, 0.22, unit * 0.24,
              "%s\n%s" % (iid, iface.get("interaction_kind")), colour, fontsize=8.2,
              lw=1.9, weight="bold")
        detail = "nominal=%s  obligations=%s" % (iface.get("nominal"),
                                                 ",".join(iface.get("addresses_obligations") or []) or "-")
        ax.text(0.03, top - unit * 0.31, detail, fontsize=6.9, color=C.MUTED,
                family="monospace", va="top")
        if mating:
            ax.text(0.03, top - unit * 0.40,
                    "mating_geometry: " + ", ".join("%s=%s" % (k, v) for k, v in
                                                    sorted(mating.items())),
                    fontsize=6.9, color=C.INK, family="monospace", va="top")
        else:
            ax.text(0.03, top - unit * 0.40, "mating_geometry: (none declared upstream)",
                    fontsize=6.9, color=C.MUTED, family="monospace", va="top")
        for pi_, p in enumerate(phi[:2]):
            ax.text(0.03, top - unit * (0.475 + 0.055 * pi_),
                    "interaction %s: effect=%s groups=%s"
                    % (p.get("entity_id"), p.get("effect"), ",".join(p.get("groups") or [])),
                    fontsize=6.9, color=C.MUTED, family="monospace", va="top")
        for gi, c in enumerate(governing.get(iid) or []):
            ax.text(0.03, top - unit * (0.57 + 0.075 * gi),
                    "named by %s [%s] %s" % (_fid(c), c.get("kind"),
                                             constraint_text(c, symbols)),
                    fontsize=6.9, color=C.INK, family="monospace", va="top")
        mine_findings = [f for f in findings if iid in str(f)]
        base = 0.57 + 0.075 * len(governing.get(iid) or [])
        if not (governing.get(iid) or []):
            ax.text(0.03, top - unit * 0.57, "no Constraint names this interface",
                    fontsize=6.9, color=C.MUTED, family="monospace", va="top")
            base = 0.645
        for fi_, line in enumerate(mine_findings):
            ax.text(0.03, top - unit * (base + 0.075 * fi_),
                    "FINDING: " + C.wrap(str(line), 96)[0], fontsize=6.9,
                    color=UNREALIZED, family="monospace", va="top")
        for bi, body in enumerate(bodies):
            by = top - unit * (0.14 + 0.42 * bi)
            bcolour = C.colour_for(body)
            _node(ax, 0.36, by, 0.13, unit * 0.20, body, bcolour, fontsize=7.8, lw=1.5)
            C.arrow(ax, 0.25, top - unit * 0.12, 0.36, by - unit * 0.10, bcolour, lw=1.3)
            realized = sides.get(body) or []
            if not realized:
                _node(ax, 0.55, by, 0.40, unit * 0.20, "UNREALIZED - no feature on %s "
                      "names %s" % (body, iid), UNREALIZED, fontsize=7.6, lw=1.6,
                      style="dashed", weight="bold")
                C.arrow(ax, 0.49, by - unit * 0.10, 0.55, by - unit * 0.10, UNREALIZED,
                        lw=1.3, ls="--")
                continue
            for fi, f in enumerate(realized):
                place = f.get("placement") or {}
                fy = by - unit * 0.235 * fi
                _node(ax, 0.55, fy, 0.40, unit * 0.19,
                      "%s  %s  datum=%s axis=%s"
                      % (_fid(f), f.get("feature_kind"), place.get("datum"),
                         place.get("axis") or "(inherit)"), bcolour, fontsize=7.2, lw=1.3)
                C.arrow(ax, 0.49, by - unit * 0.10, 0.55, fy - unit * 0.095, bcolour, lw=1.2)
        y -= unit

    C.note(fig, "Sides are read from each feature's declared `interface` and its own `body`. "
                "%s" % ("UNREALIZED sides: " + "; ".join(unrealized) if unrealized
                        else "Every declared interface has a feature on each participating "
                             "body."),
           colour=UNREALIZED if unrealized else C.OK)
    return C.save(fig, path)


# ==========================================================================
def parameter_constraint_graph(response: Dict[str, Any], path: str, branch: str = "",
                               accepted: bool = False) -> str:
    """Parameter -> Constraint <- Parameter, and what is left undetermined."""
    parameters = response.get("parameters") or []
    constraints = response.get("constraints") or []
    features = response.get("features") or []
    symbols = symbols_of(parameters)
    source, rejected = _banner(accepted)

    used_by_geometry = {r for f in features
                        for st in (f.get("construction") or [])
                        for e in (st.get("parameters") or {}).values()
                        for r in expr_refs(e)}
    used_by_geometry |= {r for f in features
                         for e in ((f.get("placement") or {}).get("offset") or [])
                         for r in expr_refs(e)}
    determined: Dict[str, List[str]] = {}
    for c in constraints:
        expr = c.get("expression") or {}
        for ref in expr_refs(expr.get("lhs")) | expr_refs(expr.get("rhs")):
            determined.setdefault(ref, []).append(_fid(c))

    rows = max(len(parameters), len(constraints), 1)
    fig = C.figure("S05 - parameter / constraint graph", source,
                   "branch %s | %d parameters, %d constraints | S05 declares; S06 settles - "
                   "no value is authored here"
                   % (branch, len(parameters), len(constraints)),
                   figsize=(16, 3.4 + 0.92 * rows), rejected=rejected)
    ax = fig.add_axes([0.03, 0.02, 0.95, 0.79]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    punit = 1.0 / max(len(parameters), 1)
    cunit = 1.0 / max(len(constraints), 1)
    ax.text(0.02, 1.03, "Parameter (declared, no value)", fontsize=8.5,
            fontweight="bold", color=C.MUTED)
    ax.text(0.44, 1.03, "Constraint (the relation that determines it)", fontsize=8.5,
            fontweight="bold", color=C.MUTED)

    ppos: Dict[str, float] = {}
    for i, p in enumerate(parameters):
        pid = _fid(p)
        y = 1.0 - punit * (i + 0.5)
        ppos[pid] = y
        free = pid not in determined
        colour = UNREALIZED if free else C.colour_for(pid)
        role = (" role=%s" % p.get("role")) if p.get("role") else ""
        _node(ax, 0.02, y + punit * 0.34, 0.30, punit * 0.68,
              "%s  %s  [%s]%s" % (pid, p.get("symbol"), p.get("unit"), role),
              colour, fontsize=7.6, lw=1.5, style="solid" if not free else "dashed")
        tag = ("determined by %s" % ",".join(determined[pid])) if not free else \
              "NO CONSTRAINT DETERMINES IT - a free direction the solver reports back"
        ax.text(0.02, y - punit * 0.47, "   " + tag +
                ("   | read by geometry" if pid in used_by_geometry else
                 "   | not read by any feature"),
                fontsize=6.7, color=UNREALIZED if free else C.MUTED,
                family="monospace", va="center")

    for i, c in enumerate(constraints):
        cid = _fid(c)
        y = 1.0 - cunit * (i + 0.5)
        colour = C.colour_for(cid)
        text = "%s  [%s / %s]" % (cid, c.get("kind"), c.get("basis") or "(no basis)")
        _node(ax, 0.44, y + cunit * 0.34, 0.54, cunit * 0.68, text, colour,
              fontsize=7.6, lw=1.5)
        ax.text(0.44, y - cunit * 0.47,
                "   " + C.wrap(constraint_text(c, symbols), 118)[0] +
                ("   governs %s" % c["governs_interface"] if c.get("governs_interface") else ""),
                fontsize=6.8, color=C.INK, family="monospace", va="center")
        expr = c.get("expression") or {}
        for ref in sorted(expr_refs(expr.get("lhs")) | expr_refs(expr.get("rhs"))):
            if ref in ppos:
                C.arrow(ax, 0.32, ppos[ref], 0.44, y, C.colour_for(ref), lw=1.1)

    missing = sorted(used_by_geometry - set(ppos))
    free = sorted(p for p in ppos if p not in determined)
    tail = []
    if free:
        tail.append("UNDETERMINED (no constraint closes them): %s" % ", ".join(free))
    if missing:
        tail.append("REFERENCED BY GEOMETRY BUT NEVER DECLARED: %s" % ", ".join(missing))
    C.note(fig, "  |  ".join(tail) or "Every declared parameter is named by at least one "
                                      "constraint.", colour=UNREALIZED if tail else C.OK)
    return C.save(fig, path)


# ==========================================================================
def write_boundary(raw: Dict[str, Any], verdict: Dict[str, Any], standing: Dict[str, Any],
                   readiness: Dict[str, Any], path: str, branch: str = "") -> str:
    """DeepSeek proposed -> write boundary -> canonical standing -> findings -> readiness.

    THE MANDATORY DISTINCTION, IN ONE PICTURE. A proposal and a design are two
    different things, and the only place they may be compared is here, where
    the boundary between them is drawn as a boundary.
    """
    response = raw.get("response") or {}
    accepted = bool(verdict.get("accepted"))
    proposed = {k: len(v) for k, v in sorted(response.items()) if isinstance(v, list)}
    written = {k: v for k, v in sorted((standing.get("counts") or {}).items()) if v}
    problems = list(verdict.get("rejection_reasons") or [])
    structural = list(verdict.get("structural_problems_recomputed") or [])

    fig = C.figure("S05 - write boundary", C.RAW_MODEL if not accepted else C.CANONICAL,
                   "branch %s | what was proposed, what the boundary did with it, and what "
                   "stands" % branch, figsize=(16, 10.5), rejected=not accepted)
    ax = fig.add_axes([0.03, 0.03, 0.95, 0.85]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    lanes = [
        ("1. DEEPSEEK PROPOSED", C.RAW_MODEL,
         ["%-24s %d" % (k, v) for k, v in proposed.items()] or ["(nothing)"],
         C.MUTED, "solid"),
        ("2. WRITE-BOUNDARY RESULT",
         "execution_status = %s   patch_applied = %s"
         % (verdict.get("execution_status"), verdict.get("patch_applied")),
         (problems or ["(no refusal recorded)"]),
         C.OK if accepted else C.WARN, "solid" if accepted else "dashed"),
        ("3. CANONICAL STANDING S05 ENTITIES",
         "what actually entered DesignState",
         ["%-24s %d" % (k, v) for k, v in written.items()] or
         ["NONE - no S05-owned entity stands for this branch"],
         C.OK if written else C.WARN, "solid" if written else "dashed"),
        ("4. DETERMINISTIC STRUCTURAL FINDINGS",
         "downstream.embodiment.structural_problems",
         structural or ["(none)"], C.WARN if structural else C.OK, "solid"),
        ("5. SETTLEMENT READINESS",
         "canonical_io.settlement_readiness -> %s" % readiness.get("settlement_readiness"),
         list(readiness.get("why_not") or ["(ready)"]),
         C.OK if readiness.get("settlement_readiness") else C.WARN, "solid"),
    ]
    unit = 1.0 / len(lanes)
    y = 1.0
    for title, sub, body, colour, style in lanes:
        _node(ax, 0.02, y, 0.30, unit * 0.34, title, colour, fontsize=8.6, lw=1.8,
              weight="bold", style=style)
        ax.text(0.02, y - unit * 0.40, C.wrap(str(sub), 62)[0], fontsize=7.4,
                color=C.MUTED, family="monospace", va="top")
        ly = y - unit * 0.04
        for line in body[:9]:
            for part in C.wrap(str(line), 104)[:2]:
                ax.text(0.35, ly, part, fontsize=7.4, color=colour, family="monospace",
                        va="top")
                ly -= unit * 0.115
        if len(body) > 9:
            ax.text(0.35, ly, "... and %d more" % (len(body) - 9), fontsize=7.2,
                    color=C.MUTED, family="monospace", va="top")
        if y - unit > 0.02:
            C.arrow(ax, 0.17, y - unit * 0.62, 0.17, y - unit + unit * 0.02, colour, lw=1.8)
        y -= unit
    C.note(fig, "A rejected response writes NOTHING. Every count under 1 is a proposal; "
                "only the counts under 3 are the design.",
           colour=C.WARN if not accepted else C.OK)
    return C.save(fig, path)
