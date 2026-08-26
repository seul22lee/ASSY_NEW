"""Shared drawing surface for the ASSY review report.

EVERY FIGURE STATES ITS EVIDENCE SOURCE. `figure()` will not produce an axes
without one, because a picture of a design that does not say where the design
came from is the one thing this report may not contain: a rejected proposal
drawn like an accepted state.

NOTHING HERE KNOWS A MECHANISM. The helpers take canonical rows and read
declared fields - `extent`/`volume`/`occupancy` shaped as {centre, half_extent}
or an AABB pair, `entity_id`, `body` - and draw what is there. No feature kind,
joint class or benchmark id appears below.
"""
from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

#: The declared evidence sources. A figure names exactly one.
RAW_MODEL = "raw DeepSeek response - PROPOSED ONLY, not DesignState"
CANONICAL = "accepted canonical DesignState"
S04_DETERMINISTIC = "deterministic S04 calculation"
S06_DETERMINISTIC = "deterministic S06 solver"
SOURCES = (RAW_MODEL, CANONICAL, S04_DETERMINISTIC, S06_DETERMINISTIC)

INK = "#1b1f24"
MUTED = "#6b7580"
RULE = "#c9d1d9"
WARN = "#b3261e"
WARN_BG = "#fdecea"
OK = "#1a7f4b"
PAPER = "#ffffff"

#: A stable colour per id, so the same body is the same colour in every figure
#: of the report without anyone keeping a table.
_WHEEL = ("#2f6fb2", "#c9761a", "#3e8e5a", "#8a4fa0", "#b0413e",
          "#1d7c86", "#8a6d3b", "#5c6bc0")


def colour_for(key: str) -> str:
    if not key:
        return MUTED
    digest = hashlib.sha256(str(key).encode()).digest()
    return _WHEEL[digest[0] % len(_WHEEL)]


def colour_by_index(index: int) -> str:
    """A distinct colour per position, for a small ordered set (joints of a
    branch, transitions) where hashing can collide and legibility matters."""
    return _WHEEL[index % len(_WHEEL)]


def figure(title: str, source: str, subtitle: str = "", figsize=(14, 9),
           rejected: bool = False):
    """A titled figure carrying its evidence source. `source` is mandatory."""
    if source not in SOURCES:
        raise ValueError("figure %r declares source %r, which is not one of %s"
                         % (title, source, list(SOURCES)))
    fig = plt.figure(figsize=figsize, facecolor=PAPER)
    fig.text(0.012, 0.975, title, fontsize=17, fontweight="bold", color=INK, va="top")
    y = 0.945
    if subtitle:
        fig.text(0.012, y, subtitle, fontsize=9.5, color=MUTED, va="top")
        y -= 0.022
    fig.text(0.012, y, "SOURCE: %s" % source, fontsize=9, color=INK, va="top",
             family="monospace",
             bbox=dict(facecolor="#eef2f6", edgecolor=RULE, pad=3.5))
    if rejected:
        fig.text(0.988, 0.975, "REJECTED - NOT DESIGNSTATE", fontsize=12,
                 fontweight="bold", color=WARN, ha="right", va="top",
                 bbox=dict(facecolor=WARN_BG, edgecolor=WARN, pad=5))
    return fig


def note(fig, text: str, colour: str = MUTED) -> None:
    """A footnote every reader sees, for what the figure cannot show."""
    fig.text(0.012, 0.012, text, fontsize=8.5, color=colour, va="bottom", wrap=True)


def save(fig, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=140, facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    return path


# ----------------------------------------------------------------- geometry
def aabb(value: Any) -> Optional[Tuple[List[float], List[float]]]:
    """(lo, hi) from any canonical box, or None. Two declared shapes are read -
    {centre, half_extent} and {aabb: [[lo],[hi]]} - and nothing is inferred from
    a field that carries neither."""
    if not isinstance(value, dict):
        return None
    if "aabb" in value:
        box = value.get("aabb")
        if (isinstance(box, (list, tuple)) and len(box) == 2
                and all(isinstance(p, (list, tuple)) and len(p) == 3 for p in box)):
            return [float(c) for c in box[0]], [float(c) for c in box[1]]
        return None
    centre, half = value.get("centre"), value.get("half_extent")
    if not (isinstance(centre, (list, tuple)) and isinstance(half, (list, tuple))):
        return None
    if len(centre) != 3 or len(half) != 3:
        return None
    lo = [float(centre[i]) - abs(float(half[i])) for i in range(3)]
    hi = [float(centre[i]) + abs(float(half[i])) for i in range(3)]
    return lo, hi


def box_of(record: Dict[str, Any]) -> Optional[Tuple[List[float], List[float]]]:
    """The box a canonical record declares, whichever declared field holds it."""
    for field in ("extent", "volume", "occupancy", "aabb"):
        got = aabb(record.get(field))
        if got:
            return got
    return None


#: The two-axis views a 3D arrangement is drawn in. (name, horizontal, vertical)
PLANES = (("XZ (front)", 0, 2), ("XY (top)", 0, 1), ("YZ (side)", 1, 2))
AXIS_NAME = ("X", "Y", "Z")


def draw_box(ax, lo, hi, h: int, v: int, colour: str, label: str = "",
             style: str = "solid", alpha: float = 0.13, lw: float = 1.4,
             fontsize: float = 7.5) -> None:
    ax.add_patch(Rectangle((lo[h], lo[v]), hi[h] - lo[h], hi[v] - lo[v],
                           facecolor=colour, edgecolor=colour, alpha=alpha,
                           linewidth=0))
    ax.add_patch(Rectangle((lo[h], lo[v]), hi[h] - lo[h], hi[v] - lo[v],
                           facecolor="none", edgecolor=colour, linewidth=lw,
                           linestyle=style))
    if label:
        ax.text((lo[h] + hi[h]) / 2.0, (lo[v] + hi[v]) / 2.0, label, fontsize=fontsize,
                color=colour, ha="center", va="center", fontweight="bold",
                bbox=dict(facecolor=PAPER, edgecolor="none", alpha=0.72, pad=1.0))


def plane_axes(fig, rect, plane_index: int, title: str = ""):
    name, h, v = PLANES[plane_index]
    ax = fig.add_axes(rect)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel(AXIS_NAME[h], fontsize=8, color=MUTED)
    ax.set_ylabel(AXIS_NAME[v], fontsize=8, color=MUTED)
    ax.set_title(title or name, fontsize=10, color=INK, loc="left")
    ax.tick_params(labelsize=7, colors=MUTED)
    for spine in ax.spines.values():
        spine.set_color(RULE)
    ax.grid(True, color="#eef1f4", linewidth=0.7)
    ax.axhline(0, color="#dfe4e9", linewidth=0.9, zorder=0)
    ax.axvline(0, color="#dfe4e9", linewidth=0.9, zorder=0)
    return ax, h, v


def arrow(ax, x0, y0, x1, y1, colour, lw=1.6, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                                 mutation_scale=11, color=colour, linewidth=lw,
                                 linestyle=ls, shrinkA=0, shrinkB=0, zorder=5))


def legend(ax, entries: Sequence[Tuple[str, str]], loc="upper right", fontsize=7.5):
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=c, linewidth=2.6, label=t) for t, c in entries]
    if handles:
        lg = ax.legend(handles=handles, loc=loc, fontsize=fontsize, frameon=True,
                       framealpha=0.94, borderpad=0.5)
        lg.get_frame().set_edgecolor(RULE)


# ------------------------------------------------------------- text panels
def text_panel(fig, rect, lines: Sequence[Tuple[str, Dict[str, Any]]], title: str = "",
               fontsize: float = 8.0, leading: float = 0.036):
    """A plain block of labelled lines. Each line is (text, kwargs)."""
    ax = fig.add_axes(rect)
    ax.axis("off")
    y = 1.0
    if title:
        ax.text(0, y, title, fontsize=10, fontweight="bold", color=INK, va="top")
        y -= leading * 1.25
    for text, kw in lines:
        style = {"fontsize": fontsize, "color": INK, "family": "monospace"}
        style.update(kw or {})
        ax.text(style.pop("x", 0), y, text, va="top", **style)
        y -= leading
    return ax


def wrap(text: str, width: int) -> List[str]:
    import textwrap
    out: List[str] = []
    for para in str(text).split("\n"):
        out.extend(textwrap.wrap(para, width) or [""])
    return out
