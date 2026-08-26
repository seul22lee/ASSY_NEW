"""The top-level review surface: REPORT.md and index.html.

GENERIC OVER THE BUNDLE. Everything below is assembled from the JSON evidence
files in the review directory and whatever PNGs sit beside them. No benchmark
id, no mechanism family and no entity id is written here; a stage section that
has no evidence says so rather than being omitted.

THE PROGRESSION IS THE SPINE: S04 spatial/motion intent -> S05 physical
symbolic embodiment -> S06 settled dimensions -> S07 actual CAD. Each section
is extended in place when its stage produces evidence; a later stage never gets
its own disconnected report.
"""
from __future__ import annotations

import html
import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The stage sections, in pipeline order, with what each one IS.
STAGES: Tuple[Tuple[str, str, str], ...] = (
    ("s04", "S04 - spatial / motion intent",
     "The arrangement, the joint frames and the sampled motion evidence the "
     "downstream consumes."),
    ("s05", "S05 - physical symbolic embodiment",
     "The geometry that makes each declared relation real, symbolically. S05 "
     "declares parameters and never values."),
    ("s06", "S06 - settled dimensions",
     "Deterministic settlement of the declared system. Not a model result."),
    ("s07", "S07 - actual CAD",
     "Compiled solids, assemblies and geometric findings."),
    ("cad", "CAD artifacts", "Body and assembly geometry as written by the compiler."),
    ("renders", "Renders", "Rendered views of the compiled assembly."),
)

#: Figure captions by file stem. A stem with no entry still renders, untitled.
CAPTIONS = {
    "spatial_layout": "Bodies, rigid groups, envelopes, functional regions and joint "
                      "origins in the arrangement frame.",
    "joint_frames": "Every joint: type, the bodies it relates, its located origin, its "
                    "axis, and its coordinate in each state.",
    "states_and_motion": "The configurations, the transitions between them, and the "
                         "swept occupancy - one panel per transition.",
    "write_boundary": "MANDATORY DISTINCTION: what was proposed, what the boundary did "
                      "with it, what stands, what the checks found, and whether S06 may "
                      "be entered.",
    "embodiment_overview": "Body-centric: every feature, its kind, polarity, placement "
                           "datum, axis, interface, construction steps and terminal.",
    "feature_map": "Each feature at the committed datum it names, with the axis it "
                   "states. Symbolic - nothing is drawn to scale.",
    "kinematic_realizations": "Feature(s) -> KinematicRealization -> Joint | "
                              "ConstraintRelation, for every declared relation.",
    "interfaces": "Interface -> the two bodies -> the feature realizing each side, with "
                  "the deterministic finding printed against it.",
    "parameter_constraint_graph": "Parameter -> Constraint <- Parameter, with units, "
                                  "roles and what no constraint determines.",
    "constraint_graph": "The system actually formulated for the solver, or the entry "
                        "gate that stopped it.",
    "parameter_values": "Parameter | meaning | unit | bounds | settled value | status.",
}

CSS = """
:root{--ink:#1b1f24;--muted:#6b7580;--rule:#d7dde4;--paper:#fff;--warn:#b3261e;
--warnbg:#fdecea;--ok:#1a7f4b;--okbg:#eaf6ef;--code:#f5f7f9;--accent:#2f6fb2}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
color:var(--ink);background:var(--paper)}
.wrap{max-width:1180px;margin:0 auto;padding:2.2rem 1.4rem 5rem}
h1{font-size:1.9rem;margin:0 0 .3rem;letter-spacing:-.01em}
h2{font-size:1.35rem;margin:2.8rem 0 .5rem;padding-top:1.1rem;border-top:2px solid var(--rule)}
h3{font-size:1.02rem;margin:1.8rem 0 .35rem}
p{margin:.5rem 0}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
code{background:var(--code);padding:.1rem .3rem;border-radius:3px;font-size:.86em}
pre{background:var(--code);border:1px solid var(--rule);border-radius:6px;padding:.8rem 1rem;
overflow-x:auto;font-size:.8rem;line-height:1.5}
table{border-collapse:collapse;width:100%;margin:.8rem 0;font-size:.86rem}
th,td{border:1px solid var(--rule);padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:#f2f5f8;font-weight:600}
figure{margin:1.2rem 0 1.8rem}
figure img{width:100%;height:auto;border:1px solid var(--rule);border-radius:6px;
background:#fff}
figcaption{font-size:.83rem;color:var(--muted);margin-top:.45rem}
.src{display:inline-block;font-family:ui-monospace,monospace;font-size:.76rem;
background:#eef2f6;border:1px solid var(--rule);border-radius:4px;padding:.15rem .45rem;
margin:.3rem .3rem .3rem 0}
.badge{display:inline-block;font-weight:700;font-size:.78rem;border-radius:4px;
padding:.2rem .55rem;margin-right:.4rem}
.rejected{background:var(--warnbg);color:var(--warn);border:1px solid var(--warn)}
.accepted{background:var(--okbg);color:var(--ok);border:1px solid var(--ok)}
.neutral{background:#eef2f6;color:var(--muted);border:1px solid var(--rule)}
.callout{border-left:4px solid var(--warn);background:var(--warnbg);padding:.7rem 1rem;
margin:1rem 0;border-radius:0 6px 6px 0}
.callout.ok{border-left-color:var(--ok);background:var(--okbg)}
.callout.info{border-left-color:var(--accent);background:#eef4fb}
.chain{font-family:ui-monospace,monospace;font-size:.84rem;background:var(--code);
border:1px solid var(--rule);border-radius:6px;padding:1rem;white-space:pre;overflow-x:auto}
.muted{color:var(--muted)}
.nav{position:sticky;top:0;background:rgba(255,255,255,.96);border-bottom:1px solid var(--rule);
padding:.6rem 0;margin-bottom:1.2rem;font-size:.85rem;z-index:9}
.nav a{color:var(--accent);text-decoration:none;margin-right:1rem}
.nav a:hover{text-decoration:underline}
ul{margin:.4rem 0 .4rem 1.2rem;padding:0}
li{margin:.2rem 0}
@media(prefers-color-scheme:dark){
:root{--ink:#e6edf3;--muted:#9aa7b2;--rule:#30363d;--paper:#0d1117;--code:#161b22;
--warnbg:#3a1d1a;--okbg:#132a1e}
figure img{background:#fff}
th{background:#161b22}
.nav{background:rgba(13,17,23,.96)}
}
"""


def read(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def figures(directory: str) -> List[str]:
    if not os.path.isdir(directory):
        return []
    stems = list(CAPTIONS)
    found = sorted(f for f in os.listdir(directory) if f.lower().endswith(".png"))
    def rank(name):
        stem = os.path.splitext(name)[0]
        return (stems.index(stem) if stem in stems else len(stems), name)
    return sorted(found, key=rank)


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    return "-" if value is None else str(value)


# ------------------------------------------------------------------ dashboard
def dashboard_rows(root: str) -> List[Dict[str, str]]:
    """One row per stage, read from that stage's own evidence."""
    s04 = read(os.path.join(root, "s04", "state_summary.json")) or {}
    raw = read(os.path.join(root, "s05", "raw_model_response.json")) or {}
    verdict = read(os.path.join(root, "s05", "boundary_verdict.json")) or {}
    standing = read(os.path.join(root, "s05", "accepted_state_summary.json")) or {}
    si = read(os.path.join(root, "s06", "solver_input.json")) or {}
    sr = read(os.path.join(root, "s06", "solver_result.json")) or {}

    rows = []
    counts = s04.get("counts") or {}
    rows.append({
        "stage": "S04", "source": "deterministic replay of accepted canonical DesignState",
        "status": "ACCEPTED" if counts else "NO EVIDENCE",
        "exists": ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())) or "-",
        "blocker": "-" if counts else "no S04 evidence in this review directory"})

    proposed = {k: len(v) for k, v in (raw.get("response") or {}).items()
                if isinstance(v, list) and v}
    written = {k: v for k, v in (standing.get("counts") or {}).items() if v}
    accepted = bool(verdict.get("accepted"))
    rows.append({
        "stage": "S05", "source": "DeepSeek + canonical write boundary",
        "status": ("ACCEPTED" if accepted else
                   "REJECTED - NOT DESIGNSTATE" if raw else "NO EVIDENCE"),
        "exists": ("standing: " + (", ".join("%s %d" % (k, v) for k, v in sorted(written.items()))
                                   if written else "NOTHING") +
                   " | proposed: " + (", ".join("%s %d" % (k, v)
                                                for k, v in sorted(proposed.items())) or "-")),
        "blocker": "; ".join(verdict.get("rejection_reasons") or []) or "-"})

    entered = bool(sr.get("entered"))
    rows.append({
        "stage": "S06", "source": "deterministic settlement (no model)",
        "status": "ENTERED" if entered else "NOT ENTERED",
        "exists": ("solver_status %s" % sr.get("solver_status")) if entered else
                  "no system formulated; no value produced",
        "blocker": ("-" if entered else
                    "settlement_readiness == %s: %s"
                    % (_fmt(si.get("settlement_readiness")),
                       "; ".join(si.get("why_not") or [])))})

    s07 = read(os.path.join(root, "s07", "compilation.json")) or {}
    rows.append({
        "stage": "S07", "source": "deterministic CAD compilation",
        "status": s07.get("status") or "NOT ENTERED",
        "exists": s07.get("artifacts") and ", ".join(s07["artifacts"]) or "no CAD artifact",
        "blocker": s07.get("blocker") or "S06 has not settled a system"})
    return rows


# ------------------------------------------------------------------ markdown
def build_markdown(root: str, title: str, subtitle: str) -> str:
    out: List[str] = ["# %s" % title, "", subtitle, ""]
    out += ["> **Evidence rule.** Every figure states its SOURCE. A model response that the",
            "> write boundary refused is never shown as the accepted design; it is labelled",
            "> `REJECTED - NOT DESIGNSTATE` and its refusal reasons are printed beside it.",
            "> No number in this report was invented for it.", ""]
    out += ["## Dashboard", "",
            "| Stage | Source | Status | What exists | Main blocker |",
            "|---|---|---|---|---|"]
    for r in dashboard_rows(root):
        out.append("| %s | %s | **%s** | %s | %s |"
                   % (r["stage"], r["source"], r["status"],
                      r["exists"].replace("|", "\\|"), r["blocker"].replace("|", "\\|")))
    out += ["", "## Progression", "", "```",
            "S04  spatial / motion intent",
            "       |",
            "S05  physical symbolic embodiment",
            "       |",
            "S06  settled dimensions",
            "       |",
            "S07  actual CAD", "```", ""]
    for key, heading, gloss in STAGES:
        directory = os.path.join(root, key)
        pngs = figures(directory)
        payloads = sorted(f for f in os.listdir(directory)
                          if f.endswith(".json")) if os.path.isdir(directory) else []
        if not pngs and not payloads:
            continue
        out += ["## %s" % heading, "", gloss, ""]
        out += section_markdown(root, key)
        for name in pngs:
            stem = os.path.splitext(name)[0]
            out += ["### %s" % stem.replace("_", " "), "",
                    "![%s](%s/%s)" % (stem, key, name), "",
                    CAPTIONS.get(stem, ""), ""]
        if payloads:
            out += ["**Evidence files:** " +
                    ", ".join("`%s/%s`" % (key, f) for f in payloads), ""]
    return "\n".join(out).rstrip() + "\n"


def section_markdown(root: str, key: str) -> List[str]:
    """The stage-specific prose that must appear, from that stage's evidence."""
    if key == "s05":
        raw = read(os.path.join(root, "s05", "raw_model_response.json")) or {}
        verdict = read(os.path.join(root, "s05", "boundary_verdict.json")) or {}
        standing = read(os.path.join(root, "s05", "accepted_state_summary.json")) or {}
        si = read(os.path.join(root, "s06", "solver_input.json")) or {}
        if not raw:
            return ["_No S05 response evidence in this review directory._", ""]
        accepted = bool(verdict.get("accepted"))
        proposed = {k: len(v) for k, v in (raw.get("response") or {}).items()
                    if isinstance(v, list)}
        written = {k: v for k, v in (standing.get("counts") or {}).items() if v}
        lines = ["### DeepSeek proposed -> write boundary -> canonical standing", ""]
        lines += ["**%s**" % ("ACCEPTED - THIS IS THE DESIGN" if accepted
                              else "REJECTED - NOT DESIGNSTATE"), ""]
        lines += ["| Step | Result |", "|---|---|"]
        lines.append("| 1. DeepSeek proposed | %s |"
                     % (", ".join("%s %d" % (k, v) for k, v in sorted(proposed.items()))
                        or "nothing"))
        lines.append("| 2. Write-boundary result | `execution_status = %s`, "
                     "`patch_applied = %s` |" % (verdict.get("execution_status"),
                                                 _fmt(verdict.get("patch_applied"))))
        lines.append("| 3. Canonical standing S05 entities | %s |"
                     % (", ".join("%s %d" % (k, v) for k, v in sorted(written.items()))
                        or "**NONE** - no S05-owned entity stands for this branch"))
        lines.append("| 4. Structural findings | %d |"
                     % len(verdict.get("structural_problems_recomputed") or []))
        lines.append("| 5. Settlement readiness | `%s` |"
                     % _fmt(si.get("settlement_readiness")))
        lines.append("")
        reasons = verdict.get("rejection_reasons") or []
        if reasons:
            lines += ["**Exact rejection reasons (write boundary):**", ""]
            lines += ["- `%s`" % r for r in reasons] + [""]
        structural = verdict.get("structural_problems_recomputed") or []
        if structural:
            lines += ["**Deterministic structural findings "
                      "(`downstream.embodiment.structural_problems`):**", ""]
            lines += ["- %s" % s for s in structural] + [""]
        other = standing.get("standing_but_authored_by_other_stages") or {}
        if other:
            lines += ["_Standing on this branch but authored by other stages "
                      "(not S05 output): %s._"
                      % ", ".join("%s %d" % (f, d.get("count")) for f, d in sorted(other.items())),
                      ""]
        return lines
    if key == "s06":
        si = read(os.path.join(root, "s06", "solver_input.json")) or {}
        sr = read(os.path.join(root, "s06", "solver_result.json")) or {}
        if not si:
            return []
        if sr.get("entered"):
            return ["`solver_status` = **%s**" % sr.get("solver_status"), ""]
        return ["**S06 NOT ENTERED**", "",
                "reason: `settlement_readiness == %s`" % _fmt(si.get("settlement_readiness")),
                ""] + ["- %s" % w for w in (si.get("why_not") or [])] + \
               ["", "_No solver value exists and none is shown. This is not a failed solve: "
                "the solver was never run._", ""]
    if key == "s04":
        s04 = read(os.path.join(root, "s04", "state_summary.json")) or {}
        if not s04:
            return []
        lines = ["`state_hash` = `%s` | provider calls during rebuild: **%s**"
                 % (s04.get("state_hash"), s04.get("provider_calls")), "",
                 "Rebuilt by:", ""]
        lines += ["- `%s`" % step for step in (s04.get("rebuilt_by") or [])]
        lines.append("")
        lines += joint_table(s04) + transition_table(s04)
        return lines
    return []


def joint_table(s04: Dict[str, Any]) -> List[str]:
    entities = s04.get("entities") or {}
    joints = entities.get("Joint") or []
    if not joints:
        return []
    groups = {g.get("entity_id"): g.get("body") for g in entities.get("RigidGroup") or []}
    states = entities.get("State") or []
    head = ["Joint", "Type", "Bodies", "Origin", "Axis"] + \
           [str(s.get("entity_id")) for s in states]
    out = ["#### Joints", "", "| " + " | ".join(head) + " |",
           "|" + "---|" * len(head)]
    for j in joints:
        jid = j.get("entity_id")
        bodies = "%s -> %s" % (groups.get(j.get("parent_group"), "?"),
                               groups.get(j.get("child_group"), "?"))
        coords = [_fmt((s.get("joint_coordinates") or {}).get(jid)) for s in states]
        out.append("| " + " | ".join([str(jid), str(j.get("joint_type")), bodies,
                                      "`%s`" % (j.get("frame_origin"),),
                                      str(j.get("axis_direction"))] + coords) + " |")
    return out + [""]


def transition_table(s04: Dict[str, Any]) -> List[str]:
    entities = s04.get("entities") or {}
    transitions = entities.get("Transition") or []
    if not transitions:
        return []
    swept = entities.get("SweptVolume") or []
    out = ["#### Transitions", "",
           "| Transition | Moving group | Start | End | Sweep evidence |",
           "|---|---|---|---|---|"]
    for t in transitions:
        tid = t.get("entity_id")
        here = [s for s in swept if s.get("transition") == tid]
        evidence = ", ".join("%s (%s, %s samples)"
                             % (s.get("entity_id"), s.get("fidelity"),
                                (s.get("sampling_declaration") or {}).get("samples"))
                             for s in here) or "none"
        out.append("| %s | %s | %s | %s | %s |"
                   % (tid, ",".join((t.get("path") or {}).get("moving_groups") or []),
                      t.get("from_state"), t.get("to_state"), evidence))
    return out + [""]


# ---------------------------------------------------------------------- html
def build_html(root: str, title: str, subtitle: str) -> str:
    e = html.escape
    rows = dashboard_rows(root)
    parts: List[str] = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
                        '<meta name="viewport" content="width=device-width,initial-scale=1">',
                        "<title>%s</title><style>%s</style></head><body><div class='wrap'>"
                        % (e(title), CSS)]
    present = [(k, h) for k, h, _g in STAGES
               if os.path.isdir(os.path.join(root, k))
               and (figures(os.path.join(root, k))
                    or any(f.endswith(".json") for f in os.listdir(os.path.join(root, k))))]
    parts.append("<div class='nav'>" + "".join(
        "<a href='#%s'>%s</a>" % (k, e(h.split(" - ")[0])) for k, h in present) + "</div>")
    parts.append("<h1>%s</h1><p class='muted'>%s</p>" % (e(title), e(subtitle)))
    parts.append("<div class='callout info'><strong>Evidence rule.</strong> Every figure "
                 "states its SOURCE. A model response the write boundary refused is never "
                 "shown as the accepted design: it is stamped "
                 "<span class='badge rejected'>REJECTED - NOT DESIGNSTATE</span> and its "
                 "refusal reasons are printed beside it. No number here was invented for "
                 "this report.</div>")

    parts.append("<h2>Dashboard</h2><table><tr><th>Stage</th><th>Source</th><th>Status</th>"
                 "<th>What exists</th><th>Main blocker</th></tr>")
    for r in rows:
        cls = ("accepted" if r["status"] in ("ACCEPTED", "ENTERED") else
               "rejected" if "REJECT" in r["status"] or "NOT ENTERED" in r["status"]
               else "neutral")
        parts.append("<tr><td><strong>%s</strong></td><td>%s</td>"
                     "<td><span class='badge %s'>%s</span></td><td>%s</td><td>%s</td></tr>"
                     % (e(r["stage"]), e(r["source"]), cls, e(r["status"]),
                        e(r["exists"]), e(r["blocker"])))
    parts.append("</table>")

    parts.append("<h2>Progression</h2><div class='chain'>"
                 "S04  spatial / motion intent\n"
                 "       |\n"
                 "S05  physical symbolic embodiment\n"
                 "       |\n"
                 "S06  settled dimensions\n"
                 "       |\n"
                 "S07  actual CAD</div>")

    for key, heading, gloss in STAGES:
        directory = os.path.join(root, key)
        if not os.path.isdir(directory):
            continue
        pngs = figures(directory)
        payloads = sorted(f for f in os.listdir(directory) if f.endswith(".json"))
        extras = sorted(f for f in os.listdir(directory)
                        if not f.endswith((".json", ".png")))
        if not pngs and not payloads and not extras:
            continue
        parts.append("<h2 id='%s'>%s</h2><p class='muted'>%s</p>"
                     % (e(key), e(heading), e(gloss)))
        parts.append(section_html(root, key))
        for name in pngs:
            stem = os.path.splitext(name)[0]
            parts.append("<figure><a href='%s/%s'><img src='%s/%s' alt='%s'></a>"
                         "<figcaption><strong>%s</strong> - %s</figcaption></figure>"
                         % (e(key), e(name), e(key), e(name), e(stem),
                            e(stem.replace("_", " ")), e(CAPTIONS.get(stem, ""))))
        links = payloads + extras
        if links:
            parts.append("<p class='muted'>Evidence files: " + " ".join(
                "<a class='src' href='%s/%s'>%s</a>" % (e(key), e(f), e(f))
                for f in links) + "</p>")
    parts.append("</div></body></html>")
    return "\n".join(parts)


def section_html(root: str, key: str) -> str:
    e = html.escape
    if key == "s05":
        raw = read(os.path.join(root, "s05", "raw_model_response.json")) or {}
        verdict = read(os.path.join(root, "s05", "boundary_verdict.json")) or {}
        standing = read(os.path.join(root, "s05", "accepted_state_summary.json")) or {}
        si = read(os.path.join(root, "s06", "solver_input.json")) or {}
        if not raw:
            return "<p class='muted'>No S05 response evidence in this review directory.</p>"
        accepted = bool(verdict.get("accepted"))
        proposed = {k: len(v) for k, v in (raw.get("response") or {}).items()
                    if isinstance(v, list)}
        written = {k: v for k, v in (standing.get("counts") or {}).items() if v}
        out = ["<div class='callout%s'><span class='badge %s'>%s</span>%s</div>"
               % ("" if not accepted else " ok",
                  "rejected" if not accepted else "accepted",
                  "REJECTED - NOT DESIGNSTATE" if not accepted
                  else "ACCEPTED - THIS IS THE DESIGN",
                  "" if accepted else
                  " The response below is a <strong>proposal</strong>. It never entered "
                  "DesignState.")]
        out.append("<h3>DeepSeek proposed &rarr; write boundary &rarr; canonical standing "
                   "&rarr; findings &rarr; settlement readiness</h3>")
        out.append("<table><tr><th>Step</th><th>Result</th></tr>")
        out.append("<tr><td>1. DeepSeek proposed</td><td>%s</td></tr>"
                   % e(", ".join("%s %d" % (k, v) for k, v in sorted(proposed.items()))
                       or "nothing"))
        out.append("<tr><td>2. Write-boundary result</td><td><code>execution_status = %s</code>"
                   " &middot; <code>patch_applied = %s</code></td></tr>"
                   % (e(str(verdict.get("execution_status"))),
                      e(_fmt(verdict.get("patch_applied")))))
        out.append("<tr><td>3. Canonical standing S05 entities</td><td>%s</td></tr>"
                   % (e(", ".join("%s %d" % (k, v) for k, v in sorted(written.items())))
                      if written else
                      "<strong>NONE</strong> &mdash; no S05-owned entity stands for this branch"))
        out.append("<tr><td>4. Structural findings</td><td>%d</td></tr>"
                   % len(verdict.get("structural_problems_recomputed") or []))
        out.append("<tr><td>5. Settlement readiness</td><td><code>%s</code></td></tr>"
                   % e(_fmt(si.get("settlement_readiness"))))
        out.append("</table>")
        reasons = verdict.get("rejection_reasons") or []
        if reasons:
            out.append("<h3>Exact rejection reasons (write boundary)</h3><pre>%s</pre>"
                       % e("\n".join(reasons)))
        structural = verdict.get("structural_problems_recomputed") or []
        if structural:
            out.append("<h3>Deterministic structural findings</h3><pre>%s</pre>"
                       % e("\n".join(structural)))
        other = standing.get("standing_but_authored_by_other_stages") or {}
        if other:
            out.append("<p class='muted'>Standing on this branch but authored by other "
                       "stages (not S05 output): %s.</p>"
                       % e(", ".join("%s %d" % (f, d.get("count"))
                                     for f, d in sorted(other.items()))))
        return "".join(out)
    if key == "s06":
        si = read(os.path.join(root, "s06", "solver_input.json")) or {}
        sr = read(os.path.join(root, "s06", "solver_result.json")) or {}
        if not si:
            return ""
        if sr.get("entered"):
            return "<p><code>solver_status</code> = <strong>%s</strong></p>" \
                   % e(str(sr.get("solver_status")))
        return ("<div class='callout'><span class='badge rejected'>S06 NOT ENTERED</span>"
                "reason: <code>settlement_readiness == %s</code><pre>%s</pre>"
                "<p>No solver value exists and none is shown. This is not a failed solve: "
                "the solver was never run.</p></div>"
                % (e(_fmt(si.get("settlement_readiness"))),
                   e("\n".join(si.get("why_not") or []))))
    if key == "s04":
        s04 = read(os.path.join(root, "s04", "state_summary.json")) or {}
        if not s04:
            return ""
        md = joint_table(s04) + transition_table(s04)
        return ("<p><code>state_hash</code> = <code>%s</code> &middot; provider calls during "
                "rebuild: <strong>%s</strong></p>%s"
                % (e(str(s04.get("state_hash"))), e(str(s04.get("provider_calls"))),
                   _md_tables_to_html(md)))
    return ""


def _md_tables_to_html(lines: Sequence[str]) -> str:
    """The small markdown tables above, rendered for the HTML page. One writer,
    two surfaces - the report and the page never disagree about a number."""
    e = html.escape
    out, in_table = [], False
    for line in lines:
        if line.startswith("#### "):
            out.append("<h3>%s</h3>" % e(line[5:]))
            continue
        if line.startswith("|") and set(line.replace("|", "").strip()) <= set("-: "):
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not in_table:
                out.append("<table>"); in_table = True
                out.append("<tr>" + "".join("<th>%s</th>" % e(c) for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(
                    "<td>%s</td>" % (("<code>%s</code>" % e(c.strip("`")))
                                     if c.startswith("`") else e(c)) for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>"); in_table = False
        if line.strip():
            out.append("<p>%s</p>" % e(line))
    if in_table:
        out.append("</table>")
    return "".join(out)


def write(root: str, title: str, subtitle: str) -> Tuple[str, str]:
    md_path = os.path.join(root, "REPORT.md")
    html_path = os.path.join(root, "index.html")
    with open(md_path, "w") as fh:
        fh.write(build_markdown(root, title, subtitle))
    with open(html_path, "w") as fh:
        fh.write(build_html(root, title, subtitle))
    return md_path, html_path
