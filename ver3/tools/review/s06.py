"""S06 review figures: deterministic settlement, and its entry gate.

S06 IS NOT A MODEL. Nothing here is labelled a DeepSeek result. When the gate
refuses entry the figures say so and show the blocker; they never draw a
parameter table with invented numbers, because "s05 produced nothing" must
never read as "the empty system solved".
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import canvas as C
from .s05 import _node, constraint_text, expr_refs, symbols_of

#: Parameter states a reader must be able to tell apart.
SETTLED, FREE, UNDERDETERMINED = "SETTLED", "FREE", "UNDERDETERMINED"
CONFLICTING, UNSUPPORTED, NOT_REACHED = "CONFLICTING", "UNSUPPORTED", "NOT_REACHED"
STATUS_COLOUR = {SETTLED: C.OK, FREE: "#8a5a00", UNDERDETERMINED: "#8a5a00",
                 CONFLICTING: C.WARN, UNSUPPORTED: C.WARN, NOT_REACHED: C.MUTED}


def constraint_graph(solver_input: Dict[str, Any], path: str, branch: str = "") -> str:
    """The system that was sent to the solver - or the gate that stopped it."""
    entered = bool(solver_input.get("settlement_readiness"))
    parameters = solver_input.get("parameters") or []
    constraints = solver_input.get("constraints") or []
    why = solver_input.get("why_not") or []

    fig = C.figure("S06 - constraint graph", C.S06_DETERMINISTIC,
                   "branch %s | the system actually formulated for the solver" % branch,
                   figsize=(15, 8.6))
    ax = fig.add_axes([0.03, 0.03, 0.95, 0.84]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    if not entered:
        fig.text(0.988, 0.972, "S06 NOT ENTERED", fontsize=13, fontweight="bold",
                 color=C.WARN, ha="right", va="top",
                 bbox=dict(facecolor=C.WARN_BG, edgecolor=C.WARN, pad=6))
        _node(ax, 0.06, 0.94, 0.36, 0.15,
              "S05 embodiment\n(nothing stands for this branch)", C.WARN, fontsize=10,
              lw=2.0, style="dashed", weight="bold")
        _node(ax, 0.58, 0.94, 0.36, 0.15,
              "S06 settlement\nNEVER RUN", C.MUTED, fontsize=10, lw=2.0,
              style="dashed", weight="bold")
        C.arrow(ax, 0.42, 0.865, 0.58, 0.865, C.WARN, lw=2.0, ls="--")
        ax.text(0.50, 0.80, "ENTRY GATE\nREFUSED", fontsize=9, color=C.WARN,
                ha="center", va="top", fontweight="bold", family="monospace")
        ax.text(0.06, 0.70, "settlement_readiness == False", fontsize=12,
                fontweight="bold", color=C.WARN, family="monospace", va="top")
        ax.text(0.06, 0.63, "canonical_io.settlement_readiness(state, %r) reports:" % branch,
                fontsize=8.5, color=C.MUTED, family="monospace", va="top")
        y = 0.57
        for line in why:
            for part in C.wrap(str(line), 128):
                ax.text(0.07, y, "- " + part if part is C.wrap(str(line), 128)[0] else
                        "  " + part, fontsize=8.4, color=C.WARN, family="monospace",
                        va="top")
                y -= 0.042
        y -= 0.03
        ax.text(0.06, y, "WHAT THIS IS NOT", fontsize=10, fontweight="bold", color=C.INK,
                va="top")
        y -= 0.05
        for line in ("This is not a failed solve. No system was formulated, no equation was",
                     "reduced, and no parameter was given a value. The solver was never asked.",
                     "A branch with no standing Feature has nothing to settle for, and the gate",
                     "reports NOT_READY before any solving so that absence can never be read",
                     "as an empty system that solved."):
            ax.text(0.06, y, line, fontsize=8.6, color=C.INK, va="top")
            y -= 0.045
        C.note(fig, "No solver value appears anywhere in this section, because none exists.")
        return C.save(fig, path)

    symbols = symbols_of(parameters)
    punit = 1.0 / max(len(parameters), 1)
    cunit = 1.0 / max(len(constraints), 1)
    positions = {}
    for i, p in enumerate(parameters):
        pid = p.get("entity_id") or p.get("id")
        y = 1.0 - punit * (i + 0.5)
        positions[pid] = y
        bounds = "lower=%s upper=%s" % (p.get("lower"), p.get("upper"))
        _node(ax, 0.02, y + punit * 0.32, 0.30, punit * 0.64,
              "%s %s [%s]" % (pid, p.get("symbol"), p.get("unit")),
              C.colour_for(pid), fontsize=7.6)
        ax.text(0.02, y - punit * 0.44, "   " + bounds, fontsize=6.8, color=C.MUTED,
                family="monospace", va="center")
    for i, c in enumerate(constraints):
        cid = c.get("entity_id") or c.get("id")
        y = 1.0 - cunit * (i + 0.5)
        _node(ax, 0.44, y + cunit * 0.32, 0.54, cunit * 0.64,
              "%s [%s] %s" % (cid, c.get("kind"), constraint_text(c, symbols)),
              C.colour_for(cid), fontsize=7.4)
        expr = c.get("expression") or {}
        for ref in sorted(expr_refs(expr.get("lhs")) | expr_refs(expr.get("rhs"))):
            if ref in positions:
                C.arrow(ax, 0.32, positions[ref], 0.44, y, C.colour_for(ref), lw=1.1)
    C.note(fig, "Equalities settle a value; inequalities bound one. The formulation digest "
                "is recorded with the solver report.")
    return C.save(fig, path)


def parameter_values(solver_result: Dict[str, Any], solver_input: Dict[str, Any],
                     path: str, branch: str = "") -> str:
    """Parameter | Meaning | Unit | Lower | Upper | Settled value | Status."""
    entered = bool(solver_result.get("entered"))
    parameters = solver_input.get("parameters") or []
    values = solver_result.get("values") or {}
    statuses = solver_result.get("statuses") or {}

    fig = C.figure("S06 - parameter values", C.S06_DETERMINISTIC,
                   "branch %s | every value is the solver's, cited to its artifact" % branch,
                   figsize=(15, 3.4 + 0.42 * max(len(parameters), 6)))
    ax = fig.add_axes([0.03, 0.04, 0.95, 0.82]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    if not entered:
        fig.text(0.988, 0.972, "S06 NOT ENTERED", fontsize=13, fontweight="bold",
                 color=C.WARN, ha="right", va="top",
                 bbox=dict(facecolor=C.WARN_BG, edgecolor=C.WARN, pad=6))
        ax.text(0.02, 0.94, "PARAMETER   MEANING                UNIT   LOWER   UPPER   "
                            "SETTLED VALUE   STATUS", fontsize=9, fontweight="bold",
                color=C.INK, family="monospace", va="top")
        ax.text(0.02, 0.86, "(no row: no Parameter stands for this branch, and no solver "
                            "value exists)", fontsize=9, color=C.MUTED,
                family="monospace", va="top")
        ax.text(0.02, 0.74, "STATUS FOR EVERY PARAMETER OF THIS DESIGN: %s" % NOT_REACHED,
                fontsize=11, fontweight="bold", color=C.MUTED, family="monospace", va="top")
        ax.text(0.02, 0.66, "reason: %s" % (solver_result.get("reason") or "-"),
                fontsize=9.5, color=C.WARN, family="monospace", va="top")
        y = 0.56
        ax.text(0.02, y, "THE STATUSES THIS TABLE DISTINGUISHES", fontsize=9.5,
                fontweight="bold", color=C.INK, va="top")
        y -= 0.07
        for name, gloss in ((SETTLED, "the solver produced a value and cited its artifact"),
                            (FREE, "no constraint determines it; the solver reports it back"),
                            (UNDERDETERMINED, "the system does not pin it down"),
                            (CONFLICTING, "the constraints cannot hold together"),
                            (UNSUPPORTED, "the formulation is outside the declared IR"),
                            (NOT_REACHED, "the solver was never run for this branch")):
            ax.text(0.03, y, "%-16s %s" % (name, gloss), fontsize=8.6,
                    color=STATUS_COLOUR[name], family="monospace", va="top")
            y -= 0.055
        C.note(fig, "No number is shown because none was produced. A value here without a "
                    "cited solver artifact would be a fabricated settlement.")
        return C.save(fig, path)

    ax.text(0.02, 0.97, "%-11s %-30s %-6s %-9s %-9s %-15s %s"
            % ("PARAMETER", "MEANING", "UNIT", "LOWER", "UPPER", "SETTLED VALUE", "STATUS"),
            fontsize=8.6, fontweight="bold", color=C.INK, family="monospace", va="top")
    y = 0.90
    for p in parameters:
        pid = p.get("entity_id") or p.get("id")
        status = statuses.get(pid, NOT_REACHED)
        ax.text(0.02, y, "%-11s %-30s %-6s %-9s %-9s %-15s %s"
                % (pid, (p.get("symbol") or "")[:30], p.get("unit"),
                   p.get("lower"), p.get("upper"),
                   values.get(pid, "-"), status),
                fontsize=8.2, color=STATUS_COLOUR.get(status, C.INK),
                family="monospace", va="top")
        y -= 0.055
    C.note(fig, "Every settled value carries the solver artifact that produced it (R-23).")
    return C.save(fig, path)
