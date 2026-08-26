"""THE CANDIDATE MATRIX - one comparison over every S04-valid branch.

WHY A MATRIX AND NOT A REPORT PER CANDIDATE

The question this answers is not "did the boundary work for this design" but
"does the boundary work". One candidate passing proves that a mechanism was
embodied; the matrix is what shows the authoring contract is general. So the
candidates sit in ONE table, with the same columns, and the row that failed is
next to the row that did not.

THE ACCEPTANCE RULE IS THE PAGE'S RULE. A response the write boundary refused
is stamped REJECTED - NOT DESIGNSTATE and is NEVER drawn as the design: only a
branch whose S05 patch was applied gets an embodiment visualization, and that
visualization is rendered from the CANONICAL STANDING ROWS, not from the
response.
"""
from __future__ import annotations

import html
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from . import canvas as C, report as R, s05 as F5, s06 as F6

#: The proof each candidate is judged against, in order. A row is CLOSED only
#: when every one of these holds.
CRITERIA = (
    ("s05_accepted", "S05 write ACCEPTED"),
    ("structural_clear", "structural_problems == []"),
    ("duties_clear", "outstanding S05 duties == 0"),
    ("settlement_ready", "settlement_readiness == True"),
    ("s06_settled", "S06 settled"),
    ("s07_built", "S07 built real B-reps"),
    ("evidence_clear", "carried spatial/geometric evidence passes"),
)


def verdict(row: Dict[str, Any]) -> Dict[str, Any]:
    """The six criteria, read from the recorded run and from nothing else."""
    s05 = row.get("s05") or {}
    s06 = row.get("s06") or {}
    s07 = row.get("s07") or {}
    accepted = bool(s05.get("accepted"))
    out = {
        "s05_accepted": accepted,
        "structural_clear": accepted and s05.get("structural_problems") == [],
        "duties_clear": accepted and s05.get("outstanding_duties") == [],
        "settlement_ready": accepted and bool(s05.get("settlement_readiness")),
        "s06_settled": s06.get("solver_status") == "feasible",
        "s07_built": bool(s07.get("compiled")) and bool(s07.get("bodies")),
        # "STEP FILES WERE WRITTEN" IS NOT SUCCESS. The compiled solids must
        # also BE the design: no blocking geometric finding against the spatial
        # duties the same manifest carried into s07.
        "evidence_clear": bool(s07.get("compiled")) and bool(s07.get("workable"))
        and not (s07.get("blocking_findings") or []),
    }
    out["all"] = all(out[key] for key, _label in CRITERIA)
    return out


def _response_from_rows(accepted: Dict[str, Any]) -> Dict[str, Any]:
    """Canonical standing rows in the shape the embodiment renderers read."""
    return {"features": accepted.get("Feature") or [],
            "parameters": accepted.get("Parameter") or [],
            "constraints": accepted.get("Constraint") or [],
            "kinematic_realizations": accepted.get("KinematicRealization") or [],
            "realizations": accepted.get("Realization") or []}


def _solver_files(s06: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    params = s06.get("parameters") or {}
    entered = bool(s06.get("entered"))
    rows = [{"entity_id": pid, "symbol": rec.get("symbol"), "unit": rec.get("unit"),
             "lower": rec.get("lower"), "upper": rec.get("upper")}
            for pid, rec in sorted(params.items())]
    status_of = {}
    values = {}
    for pid, rec in sorted(params.items()):
        values[pid] = rec.get("value")
        if rec.get("status") == "SOLVED" and rec.get("value") is not None:
            status_of[pid] = F6.SETTLED
        elif rec.get("status") == "FREE":
            status_of[pid] = F6.FREE
        elif s06.get("solver_status") == "underdetermined":
            status_of[pid] = F6.UNDERDETERMINED
        elif s06.get("solver_status") == "infeasible":
            status_of[pid] = F6.CONFLICTING
        elif s06.get("solver_status") == "unsupported_formulation":
            status_of[pid] = F6.UNSUPPORTED
        else:
            status_of[pid] = F6.NOT_REACHED
    return ({"settlement_readiness": entered, "why_not": s06.get("why_not") or [],
             "parameters": rows, "constraints": []},
            {"entered": entered, "solver_status": s06.get("solver_status"),
             "reason": s06.get("reason"), "why_not": s06.get("why_not") or [],
             "values": values, "statuses": status_of})


def render_candidate(root: str, row: Dict[str, Any]) -> List[str]:
    """Figures for one candidate. An accepted branch only."""
    cid = row["candidate"]
    directory = os.path.join(root, cid)
    made: List[str] = []
    if not os.path.isdir(directory):
        return made
    s04 = R.read(os.path.join(directory, "s04_state.json")) or {}
    entities = s04.get("entities") or {}
    s05 = row.get("s05") or {}
    if s05.get("accepted"):
        accepted = R.read(os.path.join(directory, "accepted_s05_state.json")) or {}
        response = _response_from_rows(accepted)
        from ...assy_v3.downstream import embodiment as EMB
        polarity = EMB.polarity_table()
        findings = s05.get("structural_problems") or []
        made.append(F5.embodiment_overview(
            response, entities, polarity,
            os.path.join(directory, "embodiment_overview.png"), cid, accepted=True))
        made.append(F5.feature_map(
            response, entities, polarity,
            os.path.join(directory, "feature_map.png"), cid, accepted=True))
        made.append(F5.kinematic_realizations(
            response, entities, os.path.join(directory, "kinematic_realizations.png"),
            cid, accepted=True))
        made.append(F5.interfaces(
            response, entities, os.path.join(directory, "interfaces.png"), cid,
            accepted=True, findings=findings))
        made.append(F5.parameter_constraint_graph(
            response, os.path.join(directory, "parameter_constraint_graph.png"),
            cid, accepted=True))
    s06 = row.get("s06") or {}
    solver_input, solver_result = _solver_files(s06)
    made.append(F6.parameter_values(solver_result, solver_input,
                                    os.path.join(directory, "parameter_values.png"), cid))
    return made


# ------------------------------------------------------------------ report
def _cell(value: bool) -> str:
    return "PASS" if value else "FAIL"


def build_markdown(root: str, rows: List[Dict[str, Any]], title: str,
                   subtitle: str) -> str:
    out = ["# %s" % title, "", subtitle, ""]
    out += ["> **Evidence rule.** Every figure states its SOURCE. A response the write",
            "> boundary refused is stamped `REJECTED - NOT DESIGNSTATE` and is never drawn",
            "> as the design. Only a branch whose S05 patch was APPLIED is visualized, and",
            "> from its canonical standing rows.", ""]
    verdicts = {r["candidate"]: verdict(r) for r in rows}
    closed = [c for c, v in verdicts.items() if v["all"]]
    out += ["## Verdict", "",
            "**%d of %d S04-valid candidates completed S05 -> S06 -> S07.**"
            % (len(closed), len(rows)), "",
            "S05 is **%s**." % ("CLOSED" if len(closed) == len(rows) and rows
                                else "NOT CLOSED"), ""]
    header = ["Candidate"] + [label for _key, label in CRITERIA]
    out += ["## Matrix", "", "| " + " | ".join(header) + " |",
            "|" + "---|" * len(header)]
    for r in rows:
        v = verdicts[r["candidate"]]
        out.append("| %s | %s |" % (r["candidate"],
                                    " | ".join(_cell(v[k]) for k, _l in CRITERIA)))
    out += ["", "## Per candidate", ""]
    for r in rows:
        cid = r["candidate"]
        s05, s06, s07 = r.get("s05") or {}, r.get("s06") or {}, r.get("s07") or {}
        v = verdicts[cid]
        out += ["### %s" % cid, "",
                "- **S04**: `%s` standing on branch; state hash `%s`"
                % (", ".join("%s %d" % (f, n) for f, n in
                             sorted(((R.read(os.path.join(root, cid, "s04_state.json"))
                                      or {}).get("counts") or {}).items())),
                   r.get("upstream_state_hash")),
                "- **Selection**: synthetic scratch commitment `%s` (NOT BM-001's decision)"
                % (r.get("selection") or {}).get("decision"),
                "- **DeepSeek S05**: `%s`, %s chars, %ss"
                % (s05.get("status"), s05.get("raw_chars"), s05.get("elapsed_s")),
                "- **Write boundary**: %s"
                % ("**ACCEPTED**" if s05.get("accepted")
                   else "**REJECTED - NOT DESIGNSTATE**"), ""]
        if s05.get("problems"):
            out += ["  Refusal:", "", "```", "\n".join(str(p) for p in s05["problems"])[:4000],
                    "```", ""]
        if s05.get("accepted"):
            out += ["- **Canonical standing**: %s"
                    % ", ".join("%s %d" % (f, n) for f, n in
                                sorted((s05.get("entities_written") or {}).items())),
                    "- **structural_problems**: %s"
                    % (s05.get("structural_problems") or "[]"),
                    "- **outstanding duties**: %s" % (s05.get("outstanding_duties") or "[]"),
                    "- **settlement_readiness**: `%s`" % s05.get("settlement_readiness"), ""]
            for stem in ("embodiment_overview", "kinematic_realizations", "interfaces",
                         "parameter_constraint_graph", "feature_map"):
                path = os.path.join(root, cid, stem + ".png")
                if os.path.exists(path):
                    out += ["![%s](%s/%s.png)" % (stem, cid, stem), ""]
        out += ["- **S06**: %s" % ("`%s`" % s06.get("solver_status") if s06.get("entered")
                                   else "NOT ENTERED - %s" % s06.get("reason")), ""]
        if s06.get("entered") and s06.get("problems"):
            out += ["```", "\n".join(str(p) for p in s06["problems"])[:2000], "```", ""]
        out += ["- **S07**: %s" % ("compiled %s" % ", ".join(s07.get("bodies") or [])
                                   if s07.get("compiled")
                                   else "NOT ENTERED - %s" % s07.get("reason")),
                "- **Geometric evidence**: %s"
                % ("PASS" if v["evidence_clear"] else
                   "FAIL - %d blocking finding(s) %s"
                   % (len(s07.get("blocking_findings") or []),
                      s07.get("findings_by_owner") or "")), ""]
        for f in (s07.get("blocking_findings") or [])[:12]:
            out.append("  - `%s` (owner **%s**): %s" % (f.get("kind"), f.get("owner"),
                                                        f.get("detail")))
        if s07.get("blocking_findings"):
            out.append("")
        if s07.get("artifacts"):
            out += ["  CAD artifacts: %s"
                    % ", ".join("`%s/cad/%s`" % (cid, a) for a in s07["artifacts"]), ""]
        if s07.get("problems"):
            out += ["```", "\n".join(str(p) for p in s07["problems"])[:2000], "```", ""]
    return "\n".join(out).rstrip() + "\n"


def build_html(root: str, rows: List[Dict[str, Any]], title: str, subtitle: str) -> str:
    e = html.escape
    verdicts = {r["candidate"]: verdict(r) for r in rows}
    closed = [c for c, v in verdicts.items() if v["all"]]
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             "<title>%s</title><style>%s%s</style></head><body><div class='wrap'>"
             % (e(title), R.CSS,
                ".pass{color:var(--ok);font-weight:700}.fail{color:var(--warn);font-weight:700}"
                "td.k{white-space:nowrap}")]
    parts.append("<h1>%s</h1><p class='muted'>%s</p>" % (e(title), e(subtitle)))
    parts.append("<div class='callout info'><strong>Evidence rule.</strong> Every figure "
                 "states its SOURCE. A response the write boundary refused is stamped "
                 "<span class='badge rejected'>REJECTED - NOT DESIGNSTATE</span> and is never "
                 "drawn as the design. Only a branch whose S05 patch was APPLIED is "
                 "visualized, and from its canonical standing rows.</div>")
    parts.append("<div class='callout %s'><strong>%d of %d</strong> S04-valid candidates "
                 "completed S05 &rarr; S06 &rarr; S07. S05 is <strong>%s</strong>.</div>"
                 % ("ok" if rows and len(closed) == len(rows) else "",
                    len(closed), len(rows),
                    "CLOSED" if rows and len(closed) == len(rows) else "NOT CLOSED"))
    parts.append("<h2>Matrix</h2><table><tr><th>Candidate</th>" +
                 "".join("<th>%s</th>" % e(label) for _k, label in CRITERIA) + "</tr>")
    for r in rows:
        v = verdicts[r["candidate"]]
        parts.append("<tr><td class='k'><a href='#%s'><strong>%s</strong></a></td>%s</tr>"
                     % (e(r["candidate"]), e(r["candidate"]),
                        "".join("<td class='%s'>%s</td>"
                                % ("pass" if v[k] else "fail", _cell(v[k]))
                                for k, _l in CRITERIA)))
    parts.append("</table>")

    for r in rows:
        cid = r["candidate"]
        s05, s06, s07 = r.get("s05") or {}, r.get("s06") or {}, r.get("s07") or {}
        counts = (R.read(os.path.join(root, cid, "s04_state.json")) or {}).get("counts") or {}
        parts.append("<h2 id='%s'>%s</h2>" % (e(cid), e(cid)))
        parts.append("<span class='badge %s'>%s</span>"
                     % ("accepted" if s05.get("accepted") else "rejected",
                        "S05 ACCEPTED" if s05.get("accepted")
                        else "REJECTED - NOT DESIGNSTATE"))
        parts.append("<table>"
                     "<tr><th>S04 (accepted canonical DesignState)</th><td>%s</td></tr>"
                     "<tr><th>Selection</th><td>synthetic scratch commitment "
                     "<code>%s</code> &mdash; NOT BM-001's decision</td></tr>"
                     "<tr><th>DeepSeek S05</th><td><code>%s</code>, %s chars, %ss</td></tr>"
                     "<tr><th>Canonical standing S05</th><td>%s</td></tr>"
                     "<tr><th>structural_problems</th><td>%s</td></tr>"
                     "<tr><th>outstanding duties</th><td>%s</td></tr>"
                     "<tr><th>settlement_readiness</th><td><code>%s</code></td></tr>"
                     "<tr><th>S06</th><td>%s</td></tr>"
                     "<tr><th>S07</th><td>%s</td></tr></table>"
                     % (e(", ".join("%s %d" % kv for kv in sorted(counts.items()))),
                        e(str((r.get("selection") or {}).get("decision"))),
                        e(str(s05.get("status"))), e(str(s05.get("raw_chars"))),
                        e(str(s05.get("elapsed_s"))),
                        e(", ".join("%s %d" % kv for kv in
                                    sorted((s05.get("entities_written") or {}).items()))
                          or "NOTHING"),
                        e(str(s05.get("structural_problems", "-"))),
                        e(str(s05.get("outstanding_duties", "-"))),
                        e(str(s05.get("settlement_readiness"))),
                        e("%s" % s06.get("solver_status") if s06.get("entered")
                          else "NOT ENTERED &mdash; %s" % s06.get("reason")),
                        e("compiled %s" % ", ".join(s07.get("bodies") or [])
                          if s07.get("compiled")
                          else "NOT ENTERED &mdash; %s" % s07.get("reason"))))
        parts.append("<div class='callout%s'><strong>Geometric evidence:</strong> %s</div>"
                     % ("" if not verdicts[cid]["evidence_clear"] else " ok",
                        "PASS &mdash; the compiled solids satisfy every carried spatial duty"
                        if verdicts[cid]["evidence_clear"] else
                        e("FAIL &mdash; %d blocking finding(s) %s"
                          % (len(s07.get("blocking_findings") or []),
                             s07.get("findings_by_owner") or ""))))
        if s07.get("blocking_findings"):
            parts.append("<table><tr><th>Finding</th><th>Owner</th><th>Detail</th></tr>"
                         + "".join("<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>"
                                   % (e(str(f.get("kind"))), e(str(f.get("owner"))),
                                      e(str(f.get("detail"))))
                                   for f in s07["blocking_findings"][:20]) + "</table>")
        if s05.get("problems"):
            parts.append("<h3>Write-boundary refusal</h3><pre>%s</pre>"
                         % e("\n".join(str(p) for p in s05["problems"])[:6000]))
        if s06.get("entered") and s06.get("problems"):
            parts.append("<h3>S06 report</h3><pre>%s</pre>"
                         % e("\n".join(str(p) for p in s06["problems"])[:3000]))
        if s07.get("problems"):
            parts.append("<h3>S07 compile problems</h3><pre>%s</pre>"
                         % e("\n".join(str(p) for p in s07["problems"])[:3000]))
        if s07.get("artifacts"):
            parts.append("<p class='muted'>CAD artifacts: " + " ".join(
                "<a class='src' href='%s/cad/%s'>%s</a>" % (e(cid), e(a), e(a))
                for a in s07["artifacts"]) + "</p>")
        for stem in ("embodiment_overview", "kinematic_realizations", "interfaces",
                     "parameter_constraint_graph", "feature_map", "parameter_values"):
            path = os.path.join(root, cid, stem + ".png")
            if os.path.exists(path):
                parts.append("<figure><a href='%s/%s.png'><img src='%s/%s.png' alt='%s'>"
                             "</a><figcaption><strong>%s</strong> - %s</figcaption></figure>"
                             % (e(cid), e(stem), e(cid), e(stem), e(stem),
                                e(stem.replace("_", " ")), e(R.CAPTIONS.get(stem, ""))))
        files = []
        for name in ("duty_manifest.json", "carried_spatial_duties.json", "prompt.txt",
                     "raw_model_response.txt", "accepted_s05_state.json",
                     "s06_settlement.json", "s07_artifact_report.json", "s04_state.json"):
            if os.path.exists(os.path.join(root, cid, name)):
                files.append(name)
        if files:
            parts.append("<p class='muted'>Evidence: " + " ".join(
                "<a class='src' href='%s/%s'>%s</a>" % (e(cid), e(f), e(f))
                for f in files) + "</p>")
    parts.append("</div></body></html>")
    return "\n".join(parts)


def write(root: str, rows: List[Dict[str, Any]], title: str, subtitle: str):
    with open(os.path.join(root, "REPORT.md"), "w") as fh:
        fh.write(build_markdown(root, rows, title, subtitle))
    with open(os.path.join(root, "index.html"), "w") as fh:
        fh.write(build_html(root, rows, title, subtitle))
    return (os.path.join(root, "REPORT.md"), os.path.join(root, "index.html"))
