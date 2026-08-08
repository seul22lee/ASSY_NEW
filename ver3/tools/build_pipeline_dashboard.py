"""Build a self-contained HTML dashboard over whatever pipeline artifacts exist.

A REPORT LAYER. It reads artifacts and writes one HTML file. It imports no stage
module, runs no validator, and writes nothing except its own output, so it can
never change what it is reporting on.

Discovery is generic. The only paths it knows are the roots:

    ver3/benchmarks/<case>/            benchmark cases and their source
    ver3/assy_v3/fixtures/responses/   recorded stage responses (regression)
    ver3/assy_v3/probes/<case>/        probe cases and their recorded responses
    ver3/cad_validation/<case>/        reference artifacts
    ver3/oracles/**/<case>/            oracle packs
    ver3/contracts/stages/             stage contracts, which supply stage metadata

Everything below a root is found by pattern, so a new case or a new stage appears
without editing this file.

WHAT IT REFUSES TO DO
    Infer success from absence. Every expected artifact that is not there is
    rendered as MISSING, NOT RUN, NOT IMPLEMENTED or NOT APPLICABLE, and those
    are different statements. A stage with no output is never shown as passing.

    Present reference artifacts as stage output. The CAD references are Oracle-
    aware evaluator fixtures built by hand; no stage produced them. They appear
    in their own track, labelled, so a reader cannot mistake a render for
    evidence that S07 ran.

Usage:  python ver3/tools/build_pipeline_dashboard.py [-o OUTPUT]
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VER3 = os.path.join(REPO, "ver3")

BENCHMARKS = os.path.join(VER3, "benchmarks")
RESPONSES = os.path.join(VER3, "assy_v3", "fixtures", "responses")
LIVE_RUNS = os.path.join(VER3, "live_runs")
PROBES = os.path.join(VER3, "assy_v3", "probes")
CADVAL = os.path.join(VER3, "cad_validation")
ORACLES = os.path.join(VER3, "oracles")
STAGE_CONTRACTS = os.path.join(VER3, "contracts", "stages")
OWNERSHIP = os.path.join(VER3, "contracts", "STAGE_OWNERSHIP_MATRIX.yaml")
WINDOW_REPORT = os.path.join(HERE, "window_report.json")

STAGE_IDS = ["s%02d" % i for i in range(1, 13)]
IMG_EXT = (".png", ".jpg", ".jpeg", ".svg")
VID_EXT = (".mp4", ".webm")
ANIM_EXT = (".gif",)

# Status vocabulary. ABSENCE IS NEVER SUCCESS, and the four absence values are
# four different statements about why nothing is there.
OK, BAD, WARN, OPEN = "PASS", "FAIL", "WARNING", "UNRESOLVED"
MISSING, NOT_RUN, NOT_IMPL, NA = "MISSING", "NOT RUN", "NOT IMPLEMENTED", "NOT APPLICABLE"
# Output existing is not a verdict. A stage whose output nothing on disk has
# checked is NOT_VERIFIED, which is neither a pass nor a failure.
NOT_VER = "NOT VERIFIED"
#: Evidence declared missing by the stage itself. Deliberately its own status and
#: its own colour: incomplete engineering evidence must never look like a stage
#: that succeeded, and it is equally not a failure.
INCOMPLETE = "CONTRACT INCOMPLETE"


# ===========================================================================
# reading helpers
# ===========================================================================
def read_json(path: str) -> Optional[Any]:
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return None


def read_yaml(path: str) -> Optional[Any]:
    try:
        with open(path) as fh:
            return yaml.safe_load(fh)
    except Exception:
        return None


def read_text(path: str, limit: int = 200000) -> Optional[str]:
    try:
        with open(path, errors="replace") as fh:
            return fh.read(limit)
    except Exception:
        return None


def rel(path: str, start: str) -> str:
    return os.path.relpath(path, start).replace(os.sep, "/")


def walk_files(root: str, exts: Tuple[str, ...]) -> List[str]:
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in sorted(filenames):
            if f.lower().endswith(exts):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.0f %s" % (n, unit)
        n /= 1024.0
    return "%.1f TB" % n


# ===========================================================================
# stage metadata, taken from the contracts rather than restated here
# ===========================================================================
def load_stage_meta() -> "OrderedDict[str, Dict[str, Any]]":
    meta: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    matrix = read_yaml(OWNERSHIP) or {}
    stages = (matrix.get("stages") or {})
    for sid in STAGE_IDS:
        contract_path = os.path.join(STAGE_CONTRACTS, "%s_CONTRACT.yaml" % sid.upper())
        contract = read_yaml(contract_path) if os.path.isfile(contract_path) else None
        row = stages.get(sid, {})
        entry: Dict[str, Any] = {
            "stage_id": sid,
            "name": (contract or {}).get("name") or row.get("name") or sid,
            "contract_path": contract_path if contract else None,
            "contract": contract,
            "role": (row.get("role") or "").strip(),
            "owns": row.get("owns") or [],
            "may_not": row.get("may_not") or [],
        }
        if contract:
            # A stage may declare passes (s04 does), in which case the engineering
            # question lives inside each pass rather than at the top level.
            passes = contract.get("passes") or []
            entry["passes"] = passes
            sub = [contract.get(p) or {} for p in passes]

            def pick(key: str) -> Any:
                v = contract.get(key)
                if v:
                    return v
                found = [(p, s.get(key)) for p, s in zip(passes, sub) if s.get(key)]
                if not found:
                    return None
                if len(found) == 1:
                    return found[0][1]
                return OrderedDict(found)

            q = pick("engineering_question")
            if isinstance(q, OrderedDict):
                q = "  ".join("[%s] %s" % (k.upper(), str(v).strip()) for k, v in q.items())
            entry["question"] = (q or "").strip() if isinstance(q, str) else q
            resp = pick("engineering_responsibility")
            entry["responsibility"] = resp if isinstance(resp, str) else (
                json.dumps(resp, indent=2) if resp else "")
            entry["inputs"] = pick("required_inputs")
            entry["outputs"] = pick("structured_outputs")
            checks = pick("deterministic_exit_checks")
            if isinstance(checks, OrderedDict):
                checks = [c for group in checks.values() for c in (group or [])]
            entry["checks"] = checks or []
            entry["unresolved_allowed"] = pick("allowed_unresolved") or []
            entry["maturity"] = pick("maturity_expectations")
            entry["consumer"] = pick("next_stage_consumer_requirement")
            entry["prohibited"] = pick("prohibited_decisions") or []
            entry["gate"] = contract.get("selection_gate")
        else:
            entry["question"] = ""
            entry["responsibility"] = entry["role"]
            entry["checks"] = []
        meta[sid] = entry
    return meta


# ===========================================================================
# case discovery
# ===========================================================================
def discover_cases() -> "OrderedDict[str, Dict[str, Any]]":
    cases: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    if os.path.isdir(BENCHMARKS):
        for name in sorted(os.listdir(BENCHMARKS)):
            root = os.path.join(BENCHMARKS, name)
            if not os.path.isdir(root):
                continue
            if not os.path.isfile(os.path.join(root, "descriptor.yaml")):
                continue
            cases[name] = {
                "case_id": name, "kind": "BENCHMARK", "root": root,
                "descriptor": read_yaml(os.path.join(root, "descriptor.yaml")),
                "request_path": os.path.join(root, "source", "request.txt"),
            }

    if os.path.isdir(PROBES):
        for name in sorted(os.listdir(PROBES)):
            root = os.path.join(PROBES, name)
            if not os.path.isdir(root):
                continue
            if not os.path.isfile(os.path.join(root, "request.txt")):
                continue
            cases[name] = {
                "case_id": name, "kind": "PROBE", "root": root,
                "descriptor": None,
                "request_path": os.path.join(root, "request.txt"),
            }
    return cases


def discover_stage_responses(case_id: str) -> Dict[str, Dict[str, Any]]:
    """Recorded stage responses, wherever they live. Keyed by stage id."""
    found: Dict[str, Dict[str, Any]] = {}
    for base, provenance in ((RESPONSES, "FIXTURE_REPLAY"), (PROBES, "AGENT_AUTHORED")):
        d = os.path.join(base, case_id)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            m = re.match(r"^(s\d{2})(\..+)?\.json$", f)
            if not m:
                continue
            sid, variant = m.group(1), (m.group(2) or "").lstrip(".")
            payload = read_json(os.path.join(d, f))
            entry = {
                "path": os.path.join(d, f), "payload": payload,
                "variant": variant or None, "source_dir": base,
                "provenance": provenance,
                "bytes": os.path.getsize(os.path.join(d, f)),
            }
            meta = (payload or {}).get("_meta") if isinstance(payload, dict) else None
            if meta:
                entry["prompt_sha"] = meta.get("answers_prompt_sha256")
                entry["authored_by"] = meta.get("authored_by")
                entry["notes"] = {k: v for k, v in meta.items()
                                  if k not in ("answers_prompt_sha256", "authored_by")}
                entry["provenance"] = "LIVE_PROMPT_PAIRED"
            if variant:
                found.setdefault(sid + "::variants", {"variants": []})
                found[sid + "::variants"]["variants"].append(entry)
            else:
                found[sid] = entry
    return found


def discover_live_stage_outputs(case_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Live-provider stage outputs, found by walking the run tree.

    Generic: any ver3/live_runs/<provider>/<label>/responses/<case>/<variant>/
    s??.json is picked up, so a new stage or a new run label appears without
    editing this file.
    """
    found: Dict[str, List[Dict[str, Any]]] = {}
    if not os.path.isdir(LIVE_RUNS):
        return found
    for provider in sorted(os.listdir(LIVE_RUNS)):
        pdir = os.path.join(LIVE_RUNS, provider)
        if not os.path.isdir(pdir):
            continue
        for label in sorted(os.listdir(pdir)):
            rdir = os.path.join(pdir, label, "responses", case_id)
            if not os.path.isdir(rdir):
                continue
            for variant in sorted(os.listdir(rdir)):
                vdir = os.path.join(rdir, variant)
                if not os.path.isdir(vdir):
                    continue
                for f in sorted(os.listdir(vdir)):
                    m = re.match(r"^(s\d{2}[ab]?)\.json$", f)
                    if not m:
                        continue
                    sid = m.group(1)
                    payload = read_json(os.path.join(vdir, f))
                    found.setdefault(sid[:3], []).append({
                        "stage_id": sid, "run": "%s/%s" % (provider, label),
                        "variant": variant, "path": os.path.join(vdir, f),
                        "payload": payload,
                        "bytes": os.path.getsize(os.path.join(vdir, f))})
    return found


#: Evidence precedence, strongest first. The dashboard shows the STRONGEST
#: recorded evidence for a stage and names its source. It never converts one
#: kind into another and never invents a verdict: a fixture verdict stays a
#: fixture verdict, it is merely outranked when a live one exists.
EVIDENCE_RANK = {"live provider validation": 3,
                 "offline/recorded provider validation": 2,
                 "fixture replay": 1,
                 "no validator artifact found": 0}


#: Worst-first. A stage whose passes disagree is reported at its weakest, because
#: the weakest is the one that bounds what the stage established.
_SEVERITY = {"RAISED": 5, "RESPONSE_PARSE_FAILURE": 5, "SCHEMA_FAILURE": 5,
             "RESPONSE_TRUNCATED": 4, "CONTRACT_INCOMPLETE": 3,
             "PROVIDER_UNAVAILABLE": 2, "SUCCESS": 0}


def _severity(status: Optional[str]) -> int:
    return _SEVERITY.get(str(status or "").upper(), 1)


def stage_evidence(case_id: str, sid: str,
                   window: Dict[str, Any],
                   live_trials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The strongest recorded validator verdict for one (case, stage).

    Reads BOTH families of artifact - window_report*.json (fixture replay) and
    live_runs/*/trials.json (live provider) - because the previous version read
    only the first, whose producer enumerates the fixtures directory and can
    therefore never contain a probe. That is what made a live-validated probe
    display as unverified beside a fixture-replayed benchmark shown as PASS.
    """
    best: Dict[str, Any] = {"status": None, "source": "no validator artifact found",
                            "detail": None, "findings": 0}
    # fixture replay
    wstat = window.get("%s_status" % sid)
    if wstat:
        best = {"status": wstat, "source": "fixture replay",
                "detail": window.get("_report_path"),
                "findings": len([f for f in (window.get("findings") or [])
                                 if isinstance(f, (list, tuple)) and f
                                 and str(f[0]).upper() == sid.upper()])}
    # live provider. Scoped PER STAGE to the most recent run that actually
    # carries a status for this stage: a Window 2 run supersedes for s03/s04 but
    # says nothing about s01/s02, whose latest evidence is an earlier run. A
    # global "newest run" filter would erase the s01/s02 evidence entirely, and
    # an unfiltered read would resurrect defects already fixed.
    def carries(t: Dict[str, Any]) -> bool:
        return any(t.get("%s_status" % k) for k in (sid, sid + "a", sid + "b"))

    relevant = [t for t in live_trials if carries(t)]
    if relevant:
        newest = max(t.get("_mtime", 0) for t in relevant)
        relevant = [t for t in relevant if t.get("_mtime", 0) >= newest - 1.0]
    for t in relevant:
        for key in (sid, sid + "a", sid + "b", sid + "b_status"):
            status = t.get("%s_status" % key) if not key.endswith("_status") else t.get(key)
            if not status:
                continue
            findings = len([f for f in (t.get("failures") or [])
                            if str(f.get("stage", "")).startswith(sid)])
            cand = {"status": status, "source": "live provider validation",
                    "detail": "%s%s" % (t.get("_run", ""),
                                        (" · " + t["candidate"]) if t.get("candidate") else ""),
                    "findings": findings}
            if EVIDENCE_RANK[cand["source"]] > EVIDENCE_RANK[best["source"]]:
                best = cand
            elif (EVIDENCE_RANK[cand["source"]] == EVIDENCE_RANK[best["source"]]
                  and _severity(cand["status"]) > _severity(best["status"])):
                # Within one evidence tier the WORST status wins. Preferring the
                # better one would let a passing pass mask an incomplete sibling,
                # which is the same masking this whole fix exists to remove.
                best = cand
    return best


def discover_live_trials(case_id: str) -> List[Dict[str, Any]]:
    """Validator findings recorded by the harness, per run."""
    out = []
    if not os.path.isdir(LIVE_RUNS):
        return out
    for provider in sorted(os.listdir(LIVE_RUNS)):
        pdir = os.path.join(LIVE_RUNS, provider)
        if not os.path.isdir(pdir):
            continue
        for label in sorted(os.listdir(pdir)):
            data = read_json(os.path.join(pdir, label, "trials.json")) or []
            for row in data:
                if isinstance(row, dict) and row.get("case") == case_id:
                    row = dict(row)
                    row["_run"] = "%s/%s" % (provider, label)
                    row["_mtime"] = os.path.getmtime(
                        os.path.join(pdir, label, "trials.json"))
                    out.append(row)
    return out


def discover_pipeline_runs(case: Dict[str, Any]) -> List[str]:
    """Real pipeline run outputs, if any exist. Placeholders do not count."""
    runs_dir = os.path.join(case["root"], "runs")
    if not os.path.isdir(runs_dir):
        return []
    return [f for f in sorted(os.listdir(runs_dir)) if not f.startswith(".")]


def discover_references(case_id: str) -> List[Dict[str, Any]]:
    """Reference artifacts. NOT stage output - built by hand as evaluator fixtures."""
    out: List[Dict[str, Any]] = []
    er = os.path.join(CADVAL, case_id, "executable_references")
    if not os.path.isdir(er):
        return out
    for ref_id in sorted(os.listdir(er)):
        root = os.path.join(er, ref_id)
        if not os.path.isdir(root):
            continue
        images = walk_files(root, IMG_EXT)
        videos = walk_files(root, VID_EXT)
        anims = walk_files(root, ANIM_EXT)
        # quarantined directories are shown but flagged, never treated as current
        def quarantined(p: str) -> bool:
            return "_interrupted" in p or "interrupted_" in p
        reports = {}
        vdir = os.path.join(root, "validation")
        for p in walk_files(vdir, (".json",)):
            reports[rel(p, vdir)] = p
        entry = {
            "ref_id": ref_id, "root": root,
            "images": [p for p in images if not quarantined(p)],
            "videos": [p for p in videos if not quarantined(p)],
            "anims": [p for p in anims if not quarantined(p)],
            "quarantined_media": [p for p in images + videos + anims if quarantined(p)],
            "reports": reports,
            "summary": read_json(os.path.join(vdir, "SUMMARY.json")),
            "status_record": read_yaml(os.path.join(root, "VALIDATION_STATUS.yaml")),
            "governance": read_yaml(os.path.join(root, "GOVERNANCE.yaml")),
            "manifest": os.path.join(root, "manifest.yaml")
            if os.path.isfile(os.path.join(root, "manifest.yaml")) else None,
            "geometry_signature": read_json(os.path.join(root, "geometry_signature.json")),
            "actual_evaluation": read_json(os.path.join(root, "actual_evaluation.json")),
            "declared_files": [f for f in sorted(os.listdir(root))
                               if f.endswith((".yaml", ".json", ".md"))],
        }
        entry["has_simulation"] = any("simulation" in p for p in reports) or \
            os.path.isdir(os.path.join(vdir, "simulation"))
        # Validation directories other than the live one - left behind by runs
        # that did not finish. Their contents are excluded from everything above,
        # so they are listed here rather than silently dropped.
        entry["other_validation_dirs"] = []
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if os.path.isdir(p) and name.startswith("validation") and name != "validation":
                entry["other_validation_dirs"].append(
                    {"name": name, "files": sum(len(f) for _, _, f in os.walk(p))})
        out.append(entry)
    return out


def discover_oracle(case_id: str) -> Optional[Dict[str, Any]]:
    """The Oracle pack for a case, including its per-stage expectations."""
    for base in (os.path.join(ORACLES, "product_cases"), os.path.join(ORACLES, "held_out"),
                 os.path.join(ORACLES, "micro_oracles")):
        d = os.path.join(base, case_id)
        if not os.path.isdir(d):
            continue
        norm = read_yaml(os.path.join(d, "normative.yaml")) or {}
        expect = read_yaml(os.path.join(d, "stage_expectations.yaml")) or {}
        stages = expect.get("stages")
        return {
            "root": d,
            "files": sorted(f for f in os.listdir(d) if f.endswith((".yaml", ".md"))),
            "invariant_count": len(norm.get("invariants") or []),
            "invariants": norm.get("invariants") or [],
            "required_unresolved": norm.get("required_unresolved") or [],
            "stage_expectations": stages if isinstance(stages, dict) else {},
            "tier": os.path.basename(base),
        }
    return None


def load_window_reports() -> Tuple[Dict[str, Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """Find every harness report under ver3/, not just the expected one.

    Returns (by_case, report_paths, conflicts). A second report file is not
    assumed to be a copy: if two files describe the same case differently, that
    is reported rather than silently resolved by preferring one.
    """
    paths: List[str] = []
    for dirpath, dirnames, filenames in os.walk(VER3):
        dirnames[:] = [d for d in dirnames if d not in (".git", "out", "__pycache__")]
        for f in filenames:
            if re.match(r"^window_report.*\.json$", f):
                paths.append(os.path.join(dirpath, f))
    paths.sort(key=lambda p: (p != WINDOW_REPORT, p))  # canonical location first

    by_case: Dict[str, Dict[str, Any]] = {}
    seen: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    conflicts: List[Dict[str, Any]] = []
    for p in paths:
        data = read_json(p) or []
        if not isinstance(data, list):
            continue
        for row in data:
            if not isinstance(row, dict) or not row.get("case"):
                continue
            case = row["case"]
            if case in seen:
                first_path, first_row = seen[case]
                differing = sorted(set(first_row) ^ set(row)) or \
                    [k for k in set(first_row) & set(row) if first_row[k] != row[k]]
                if differing:
                    conflicts.append({
                        "case": case, "kept": rel(first_path, REPO),
                        "other": rel(p, REPO), "differing_keys": differing})
                continue
            seen[case] = (p, row)
            row = dict(row)
            row["_report_path"] = rel(p, REPO)
            by_case[case] = row
    return by_case, [rel(p, REPO) for p in paths], conflicts


def find_unparseable_yaml(root: str) -> List[Tuple[str, str]]:
    """YAML under a root that does not parse. A file nothing reads can be broken
    for a long time without anything noticing, which is why this is checked."""
    bad = []
    if not os.path.isdir(root):
        return bad
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for f in filenames:
            if not f.endswith((".yaml", ".yml")):
                continue
            p = os.path.join(dirpath, f)
            try:
                with open(p) as fh:
                    yaml.safe_load(fh)
            except Exception as exc:
                bad.append((rel(p, REPO), str(exc).splitlines()[0][:200]))
    return bad


# ===========================================================================
# entity extraction from a recorded response - parsing only, no pipeline import
# ===========================================================================
ENTITY_KEYS = OrderedDict([
    ("source_clauses", "SourceClause"), ("requirements", "Requirement"),
    ("scenarios", "Scenario"), ("actors", "Actor"), ("freedoms", "Freedom"),
    ("ambiguities", "Ambiguity"), ("assumptions", "Assumption"),
    ("obligations", "Obligation"), ("load_cases", "LoadCase"),
    ("candidates", "Candidate"), ("acceptance_contracts", "AcceptanceContract"),
    ("unresolved", "UnresolvedDecision"),
])


def entity_counts(payload: Any) -> "OrderedDict[str, int]":
    counts: "OrderedDict[str, int]" = OrderedDict()
    if not isinstance(payload, dict):
        return counts
    for key, family in ENTITY_KEYS.items():
        v = payload.get(key)
        if isinstance(v, list):
            counts[family] = len(v)
    return counts


def extract_open_items(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    out = []
    for u in payload.get("unresolved") or []:
        if isinstance(u, dict):
            out.append(u)
    return out


def extract_deferred(payload: Any) -> List[Dict[str, str]]:
    """Obligations a stage hands forward, from the response itself."""
    if not isinstance(payload, dict):
        return []
    out = []
    for o in payload.get("obligations") or []:
        if not isinstance(o, dict):
            continue
        at = o.get("satisfiable_at")
        if at and at != "s02":
            out.append({"id": o.get("id"), "at": at,
                        "statement": o.get("statement", ""),
                        "route": o.get("evidence_route", ""),
                        "available": o.get("route_available")})
    return out


def extract_unavailable_routes(payload: Any) -> List[Dict[str, str]]:
    if not isinstance(payload, dict):
        return []
    out = []
    for o in payload.get("obligations") or []:
        if isinstance(o, dict) and o.get("route_available") is False:
            out.append({"id": o.get("id"), "route": o.get("evidence_route"),
                        "statement": o.get("statement", "")})
    for c in payload.get("candidates") or []:
        if isinstance(c, dict):
            v = c.get("evidence_route_verdict") or {}
            if isinstance(v, dict) and v.get("available") is False:
                out.append({"id": c.get("id"), "route": v.get("route"),
                            "statement": c.get("summary", "")})
    return out


# ===========================================================================
# HTML
# ===========================================================================
def spatial_views(s04a: Optional[Dict[str, Any]], s04b: Optional[Dict[str, Any]],
                  s03: Optional[Dict[str, Any]]) -> str:
    """Orthographic box views built from s04's own numbers.

    INSPECTION ONLY. These are axis-aligned extents the model proposed, drawn to
    scale; they are not CAD, not authoritative geometry, and nothing here is
    invented to fill a gap. A body with no extent is listed as unplaced rather
    than given one.
    """
    if not isinstance(s04a, dict) or not s04a.get("envelopes"):
        return ('<div class="note">%s No envelope data: s04a produced no extents '
                'for this case, so no spatial view can be drawn. The structured '
                'output below is the deliverable.</div>' % pill(NOT_RUN))
    boxes = []
    for e in s04a.get("envelopes", []):
        c, h = e.get("centre"), e.get("half_extent")
        if not (isinstance(c, list) and isinstance(h, list) and len(c) == 3 and len(h) == 3):
            continue
        try:
            boxes.append((e.get("body") or e.get("id"),
                          [float(x) for x in c], [abs(float(x)) for x in h]))
        except Exception:                                            # noqa: BLE001
            continue
    if not boxes:
        return ('<div class="note">%s Envelopes exist but none carries a usable '
                'centre and half-extent.</div>' % pill(MISSING))

    regions = []
    for r in (s04a.get("region_volumes") or []):
        c, h = r.get("centre"), r.get("half_extent")
        if isinstance(c, list) and isinstance(h, list) and len(c) == 3 and len(h) == 3:
            try:
                regions.append((r.get("functional_region"),
                                [float(x) for x in c], [abs(float(x)) for x in h]))
            except Exception:                                        # noqa: BLE001
                pass
    joints = []
    for j in ((s04b or {}).get("joint_placements") or []):
        o = j.get("origin")
        if isinstance(o, list) and len(o) == 3:
            try:
                joints.append((j.get("joint"), [float(x) for x in o]))
            except Exception:                                        # noqa: BLE001
                pass
    axis_of = {}
    for j in ((s03 or {}).get("joints") or []):
        axis_of[j.get("id")] = j.get("axis_direction")

    palette = ["#4f8ef7", "#2f9e63", "#c9862a", "#7d5bbe", "#d1495b",
               "#3aa8a0", "#b06fc4", "#8a9a3b"]
    svgs = []
    for plane, (ax, ay, lab) in enumerate((( 0, 2, "XZ  (front)"),
                                           (0, 1, "XY  (top)"),
                                           (1, 2, "YZ  (side)"))):
        pts = []
        for _n, c, h in boxes + regions:
            pts += [(c[ax] - h[ax], c[ay] - h[ay]), (c[ax] + h[ax], c[ay] + h[ay])]
        for _n, o in joints:
            pts.append((o[ax], o[ay]))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
        span = max(hi_x - lo_x, hi_y - lo_y) or 1.0
        pad = span * 0.12
        W = H = 320.0
        def sx(v): return (v - lo_x + pad) / (span + 2 * pad) * W
        def sy(v): return H - (v - lo_y + pad) / (span + 2 * pad) * H
        parts = ['<svg viewBox="0 0 %d %d" class="ortho">' % (W, H)]
        for i, (n, c, h) in enumerate(regions):
            x0, y0 = sx(c[ax] - h[ax]), sy(c[ay] + h[ay])
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                         'fill="none" stroke="#e8b168" stroke-dasharray="4 3"/>'
                         '<title>%s (functional region)</title>'
                         % (x0, y0, abs(sx(c[ax] + h[ax]) - x0), abs(sy(c[ay] - h[ay]) - y0),
                            esc(n)))
        for i, (n, c, h) in enumerate(boxes):
            col = palette[i % len(palette)]
            x0, y0 = sx(c[ax] - h[ax]), sy(c[ay] + h[ay])
            w, hh = abs(sx(c[ax] + h[ax]) - x0), abs(sy(c[ay] - h[ay]) - y0)
            parts.append('<g><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                         'fill="%s" fill-opacity="0.18" stroke="%s"/>'
                         '<title>%s</title></g>' % (x0, y0, w, hh, col, col, esc(n)))
            parts.append('<text x="%.1f" y="%.1f" class="olabel">%s</text>'
                         % (x0 + 3, y0 + 11, esc(str(n))[:14]))
        for n, o in joints:
            parts.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="#ff8a99"/>'
                         '<title>%s axis %s</title>'
                         % (sx(o[ax]), sy(o[ay]), esc(n), esc(axis_of.get(n, "?"))))
        parts.append('</svg>')
        svgs.append('<figure class="orthofig">%s<figcaption>%s</figcaption></figure>'
                    % ("".join(parts), esc(lab)))

    unplaced = []
    declared = {b.get("id") for b in ((s03 or {}).get("bodies") or [])}
    placed = {n for n, _c, _h in boxes}
    unplaced = sorted(x for x in declared - placed if x)
    note = ""
    if unplaced:
        note = ('<div class="note gapnote">%s %d declared bodies have no extent and '
                'are absent from these views: %s. Nothing was invented to draw them.'
                '</div>' % (pill(MISSING), len(unplaced), esc(", ".join(unplaced))))
    legend = ('<p class="muted">Solid boxes are body envelopes; dashed boxes are '
              'functional regions; dots are joint origins (hover for the axis). '
              'Axis-aligned extents proposed by s04a, drawn to scale. '
              '<b>Inspection view only</b> — not CAD, not authoritative geometry, '
              'and no dimension here has been established by anything.</p>')
    return legend + '<div class="orthorow">%s</div>%s' % ("".join(svgs), note)


def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def pill(status: str, extra: str = "") -> str:
    cls = {
        OK: "ok", BAD: "bad", WARN: "warn", OPEN: "open",
        MISSING: "gap", NOT_RUN: "gap", NOT_IMPL: "gap", NA: "na",
        NOT_VER: "unver",
        INCOMPLETE: "incomplete",
    }.get(status, "na")
    return '<span class="pill %s">%s%s</span>' % (cls, esc(status), esc(extra))


def verdict_pill(raw: Any) -> str:
    """Render a verdict recorded by some other tool, in that tool's own words.

    Anything not clearly a pass or a failure is amber rather than green:
    NOT_EVALUABLE and DEFERRED are not successes.
    """
    if raw is None:
        return pill(MISSING)
    text = str(raw)
    up = text.upper()
    if up in ("CONTRACT_INCOMPLETE", "CONTRACT INCOMPLETE"):
        # Its own class, never green and never red: the stage ran, and told you
        # what it could not support.
        cls = "incomplete"
    elif up in ("PASS", "SUCCESS", "OK", "TRUE", "COMPLETE", "BUILT"):
        cls = "ok"
    elif up in ("FAIL", "FAILED", "ERROR", "FALSE", "REJECTED"):
        cls = "bad"
    else:
        cls = "warn"
    return '<span class="pill %s">%s</span>' % (cls, esc(text))


def provenance_pill(prov: Optional[str]) -> str:
    """How a stage output came to exist. A description, not a verdict - so the
    colours distinguish the two kinds without calling either one a pass."""
    if not prov:
        return pill(MISSING)
    cls = {"LIVE_PROMPT_PAIRED": "unver", "AGENT_AUTHORED": "unver",
           "FIXTURE_REPLAY": "warn"}.get(prov, "na")
    return '<span class="pill %s">%s</span>' % (cls, esc(prov))


def details(summary: str, body: str, open_: bool = False, cls: str = "") -> str:
    return ('<details class="%s"%s><summary>%s</summary><div class="dbody">%s</div></details>'
            % (cls, " open" if open_ else "", summary, body))


def code_block(text: str, lang: str = "") -> str:
    return '<pre class="code %s">%s</pre>' % (lang, esc(text))


def json_block(obj: Any) -> str:
    try:
        return code_block(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))
    except Exception:
        return code_block(repr(obj))


def kv_table(rows: List[Tuple[str, str]]) -> str:
    body = "".join('<tr><th>%s</th><td>%s</td></tr>' % (esc(k), v) for k, v in rows)
    return '<table class="kv">%s</table>' % body


def media_gallery(paths: List[str], out_dir: str, kind: str, limit: int = 0) -> str:
    if not paths:
        return ""
    shown = paths if not limit else paths[:limit]
    cells = []
    for p in shown:
        href = rel(p, out_dir)
        name = os.path.basename(p)
        if kind == "image":
            cells.append(
                '<figure class="shot"><a href="%s" target="_blank" rel="noopener">'
                '<img loading="lazy" src="%s" alt="%s"></a>'
                '<figcaption>%s</figcaption></figure>' % (href, href, esc(name), esc(name)))
        elif kind == "video":
            cells.append(
                '<figure class="clip"><video controls preload="metadata" src="%s"></video>'
                '<figcaption><a href="%s" target="_blank" rel="noopener">%s</a> · %s</figcaption>'
                '</figure>' % (href, href, esc(name), human_bytes(os.path.getsize(p))))
        else:
            cells.append(
                '<figure class="shot"><a href="%s" target="_blank" rel="noopener">'
                '<img loading="lazy" src="%s" alt="%s"></a>'
                '<figcaption>%s (animation)</figcaption></figure>'
                % (href, href, esc(name), esc(name)))
    more = ""
    if limit and len(paths) > limit:
        more = '<p class="muted">+%d more not shown inline; all are on disk under the reference.</p>' % (
            len(paths) - limit)
    return '<div class="gallery">%s</div>%s' % ("".join(cells), more)


def grouped_gallery(paths: List[str], root: str, out_dir: str, kind: str) -> str:
    """Every file, grouped by the directory that holds it. Nothing is dropped:
    a capped gallery would silently misrepresent how much evidence exists."""
    if not paths:
        return ""
    groups: "OrderedDict[str, List[str]]" = OrderedDict()
    for p in paths:
        groups.setdefault(os.path.dirname(rel(p, root)) or ".", []).append(p)
    blocks = []
    for i, (grp, items) in enumerate(sorted(groups.items())):
        label = "%s <span class=\"muted\">— %d file%s</span>" % (
            esc(grp), len(items), "" if len(items) == 1 else "s")
        blocks.append(details(label, media_gallery(items, out_dir, kind),
                              open_=(i == 0 and len(groups) <= 3)))
    return "".join(blocks)


# ---------------------------------------------------------------- stage panel
def render_stage_panel(case: Dict[str, Any], sid: str, meta: Dict[str, Any],
                       responses: Dict[str, Any], window: Dict[str, Any],
                       oracle: Optional[Dict[str, Any]], out_dir: str,
                       live: Optional[Dict[str, List[Dict[str, Any]]]] = None,
                       live_trials: Optional[List[Dict[str, Any]]] = None
                       ) -> Tuple[str, Dict[str, Any]]:
    """Returns (html, status_record). status_record feeds the summary views."""
    anchor = "%s-%s" % (case["case_id"], sid)
    resp = responses.get(sid)
    live_rows = (live or {}).get(sid) or []
    contract = meta.get("contract")
    st: Dict[str, Any] = {"stage": sid, "case": case["case_id"]}

    # ---- window-report findings for this case/stage ------------------------
    findings = []
    for f in (window.get("findings") or []):
        if isinstance(f, (list, tuple)) and len(f) >= 2 and \
                str(f[0]).upper() == sid.upper():
            findings.append(list(f) + [""] * (3 - len(f)))
    wstat = window.get("%s_status" % sid)
    wprob = window.get("%s_problems" % sid) or []
    wincomplete = window.get("%s_incomplete" % sid) or []
    st["findings"] = len(findings)

    # ---- 1. status ---------------------------------------------------------
    # Presence of an output file is not a pass. The verdict comes from the
    # harness record; where none exists on disk, the output is NOT VERIFIED.
    ev = stage_evidence(case["case_id"], sid, window, live_trials or [])
    st["evidence_source"] = ev["source"]
    st["evidence_status"] = ev["status"]

    why = ""
    if ev["status"]:
        raw = str(ev["status"]).upper()
        if raw == "SUCCESS":
            status = OK
        elif raw == "CONTRACT_INCOMPLETE":
            status = INCOMPLETE
        elif raw in ("RESPONSE_TRUNCATED", "SCHEMA_FAILURE", "RESPONSE_PARSE_FAILURE",
                     "RAISED"):
            status = BAD
        else:
            status = WARN
        if status == OK and ev["findings"]:
            status = WARN
        why = ("Recorded validator status %s, from %s%s. This page reports that "
               "verdict; it does not compute one."
               % (ev["status"], ev["source"],
                  (" (%s)" % ev["detail"]) if ev["detail"] else ""))
    elif resp is None and live_rows:
        # Produced by a live provider rather than a recording. Its verdict comes
        # from the harness findings below, never from its mere existence.
        status, why = NOT_VER, (
            "Produced live by an independent provider. Validator findings are "
            "listed below; this panel asserts no verdict of its own.")
    elif resp is None:
        if contract is None:
            status, why = NOT_IMPL, (
                "No stage contract exists at %s and no stage module. Stage metadata below "
                "is the ownership-matrix role only."
                % rel(os.path.join(STAGE_CONTRACTS, "%s_CONTRACT.yaml" % sid.upper()), REPO))
        else:
            status, why = NOT_RUN, ("A contract exists for this stage but no recorded output "
                                    "was found for this case. The stage has not been run here.")
    elif wstat is None:
        status, why = NOT_VER, (
            "Structured output exists, but no harness report on disk records a verdict for "
            "this case. The output is shown; it is not shown as correct.")
    elif wstat != "SUCCESS":
        status = BAD
    elif findings or wprob:
        status = WARN
    else:
        status = OK
    st["status"] = status
    st["has_output"] = resp is not None or bool(live_rows)
    st["findings_recorded"] = ev["findings"]

    parts: List[str] = []

    # ---- 1. name + engineering question ------------------------------------
    q = meta.get("question") or meta.get("role") or ""
    head_rows = [("stage", "<b>%s</b> — %s" % (esc(sid.upper()), esc(meta.get("name", ""))))]
    head_rows.append(("engineering question", esc(q) if q else pill(MISSING, " no question declared")))
    if meta.get("responsibility"):
        head_rows.append(("responsibility", esc(meta["responsibility"])))
    if meta.get("passes"):
        head_rows.append(("declared passes", esc(", ".join(meta["passes"]))))
    head_rows.append(("contract", ('<code>%s</code>' % esc(rel(meta["contract_path"], REPO)))
                                  if meta.get("contract_path") else pill(NOT_IMPL)))
    head_rows.append(("owns (entity families)",
                      esc(", ".join(meta.get("owns") or [])) or pill(NA)))
    parts.append(kv_table(head_rows))

    if status in (NOT_IMPL, NOT_RUN, NOT_VER):
        parts.append('<div class="note gapnote">%s %s</div>' % (pill(status), esc(why)))

    # ---- 2. inputs ---------------------------------------------------------
    inp_rows = []
    if sid == "s01":
        rp = case.get("request_path")
        if rp and os.path.isfile(rp):
            inp_rows.append(("source request", '<code>%s</code>' % esc(rel(rp, REPO))))
            parts.append(kv_table(inp_rows))
            parts.append(details("Input content — raw source request",
                                 code_block(read_text(rp) or "")))
        else:
            parts.append(kv_table([("source request", pill(MISSING))]))
    elif contract is not None:
        ri = meta.get("inputs")  # merged across passes, where the stage declares them
        rows = [("required inputs", json_block(ri) if ri else pill(MISSING))]
        pi = contract.get("prohibited_inputs")
        if pi:
            rows.append(("prohibited inputs", json_block(pi)))
        parts.append(kv_table(rows))
        if sid == "s02":
            fam = window.get("projection_families")
            parts.append(kv_table([
                ("projection actually received",
                 esc(", ".join(fam)) if fam else pill(NOT_RUN)),
                ("source text withheld (INV-002)",
                 pill(OK, " SourceClause absent from projection")
                 if fam and "SourceClause" not in fam else pill(MISSING, " not observed"))]))
    else:
        parts.append(kv_table([("required inputs", pill(NOT_IMPL))]))

    # ---- 3./4. structured output + entities --------------------------------
    if resp is not None:
        counts = entity_counts(resp["payload"])
        st["counts"] = counts
        chips = "".join('<span class="chip"><b>%d</b> %s</span>' % (v, esc(k))
                        for k, v in counts.items())
        parts.append('<h4>Key extracted engineering entities</h4><div class="chips">%s</div>' % chips)

        # entity tables - the actual content, not a summary
        for key, family in ENTITY_KEYS.items():
            rows = (resp["payload"] or {}).get(key)
            if not isinstance(rows, list) or not rows:
                continue
            head = sorted({k for r in rows if isinstance(r, dict) for k in r})
            prefer = [c for c in ("id", "statement", "statement_verbatim", "summary",
                                  "decision", "name", "scope", "satisfiable_at",
                                  "quantity_class", "kind", "direction_class",
                                  "evidence_route", "route_available") if c in head]
            cols = prefer + [c for c in head if c not in prefer][:4]
            thead = "".join("<th>%s</th>" % esc(c) for c in cols)
            trs = []
            for r in rows:
                tds = []
                for c in cols:
                    v = r.get(c) if isinstance(r, dict) else ""
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v, sort_keys=True)
                    tds.append("<td>%s</td>" % esc(v if v is not None else ""))
                trs.append("<tr>%s</tr>" % "".join(tds))
            parts.append(details(
                "%s — %d" % (esc(family), len(rows)),
                '<table class="grid"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
                % (thead, "".join(trs))))

        parts.append(details("Complete structured output — %s (%s)"
                             % (esc(os.path.basename(resp["path"])), human_bytes(resp["bytes"])),
                             json_block(resp["payload"])))

        variants = responses.get(sid + "::variants", {}).get("variants") or []
        for v in variants:
            parts.append(details(
                'Superseded variant — %s <span class="pill na">HISTORICAL</span>'
                % esc(os.path.basename(v["path"])), json_block(v["payload"])))
    else:
        parts.append('<h4>Structured output</h4>' + '<div class="note">%s</div>'
                     % pill(status))

    open_items = extract_open_items(resp["payload"]) if resp else []
    deferred = extract_deferred(resp["payload"]) if resp else []
    unavailable = extract_unavailable_routes(resp["payload"]) if resp else []

    # ---- live-provider output ---------------------------------------------
    if live_rows:
        parts.append('<h4>Live-provider output</h4>')
        parts.append('<div class="note warnnote">Produced by an independent live '
                     'provider from the previous stage\'s structured output. '
                     'Not authored in this repository and not a fixture.</div>')
        by_run: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
        for r in live_rows:
            by_run.setdefault("%s · %s" % (r["run"], r["variant"]), []).append(r)
        for label, rows in by_run.items():
            body = []
            payloads = {r["stage_id"]: r["payload"] for r in rows}
            for r in sorted(rows, key=lambda r: r["stage_id"]):
                p = r["payload"] or {}
                chips = "".join('<span class="chip"><b>%d</b> %s</span>'
                                % (len(v), esc(k))
                                for k, v in sorted(p.items()) if isinstance(v, list))
                body.append('<h5>%s <span class="muted">%s</span></h5>%s'
                            % (esc(r["stage_id"].upper()), esc(human_bytes(r["bytes"])),
                               '<div class="chips">%s</div>' % chips if chips else ""))
                for key, rows2 in sorted(p.items()):
                    if isinstance(rows2, list) and rows2 and isinstance(rows2[0], dict):
                        head = sorted({k for x in rows2 if isinstance(x, dict) for k in x})
                        cols = [c for c in ("id", "role", "body", "joint_type",
                                            "parent_group", "child_group", "axis_direction",
                                            "interaction_kind", "name", "kind",
                                            "order_index", "access_side",
                                            "termination_strategy", "path_kind",
                                            "load_case", "rigid_group", "configuration",
                                            "actor", "reachable", "half_extent", "centre")
                                if c in head]
                        cols += [c for c in head if c not in cols][:5]
                        thead = "".join("<th>%s</th>" % esc(c) for c in cols)
                        trs = []
                        for x in rows2:
                            tds = []
                            for c in cols:
                                v = x.get(c) if isinstance(x, dict) else ""
                                if isinstance(v, (dict, list)):
                                    v = json.dumps(v, sort_keys=True)
                                tds.append("<td>%s</td>" % esc("" if v is None else v))
                            trs.append("<tr>%s</tr>" % "".join(tds))
                        body.append(details(
                            "%s — %d" % (esc(key), len(rows2)),
                            '<table class="grid"><thead><tr>%s</tr></thead>'
                            '<tbody>%s</tbody></table>' % (thead, "".join(trs))))
                body.append(details("Complete structured output — %s" % esc(r["stage_id"]),
                                    json_block(p)))
            if sid == "s04":
                body.append("<h5>Spatial inspection views</h5>")
                s03p = None
                for lr in ((live or {}).get("s03") or []):
                    if lr["variant"] == rows[0]["variant"] and lr["stage_id"] == "s03":
                        s03p = lr["payload"]
                body.append(spatial_views(payloads.get("s04a"), payloads.get("s04b"), s03p))
            parts.append(details("<b>%s</b>" % esc(label), "".join(body), open_=True))

    # ---- harness findings, verbatim ---------------------------------------
    rows_for_stage = []
    for t in (live_trials or []):
        for f in (t.get("failures") or []):
            if str(f.get("stage", "")).startswith(sid) or (
                    sid == "s03" and f.get("stage") == "s03->s04"):
                rows_for_stage.append((t.get("_run"), t.get("candidate"), f))
    if rows_for_stage:
        trs = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                      % (esc(run), esc(cand),
                         pill(WARN if f["kind"] == "CHECK_FINDING" else BAD, " " + f["kind"]),
                         esc("%s — %s" % (f.get("what"), f.get("detail")))[:400])
                      for run, cand, f in rows_for_stage[:400])
        parts.append('<h4>Validator findings recorded by the harness '
                     '<span class="pill warn">%d</span></h4>'
                     '<div class="note">Reproduced exactly as the harness recorded '
                     'them. This page computes no verdict of its own.</div>'
                     '<table class="grid"><thead><tr><th>run</th><th>candidate</th>'
                     '<th>kind</th><th>finding</th></tr></thead><tbody>%s</tbody>'
                     '</table>' % (len(rows_for_stage), trs))
    elif live_rows:
        parts.append('<h4>Validator findings recorded by the harness</h4>'
                     '<div class="note">%s none recorded for this stage</div>' % pill(OK))

    # ---- 5. validator / acceptance ----------------------------------------
    vrows: List[Tuple[str, str]] = []
    if wstat:
        vrows.append(("harness execution status", verdict_pill(wstat)))
    elif resp is not None:
        vrows.append(("harness execution status",
                      pill(NOT_RUN, " no window_report entry for this case")))
    if wprob:
        vrows.append(("contract problems", code_block("\n".join(map(str, wprob)))))
    if wincomplete:
        vrows.append(("declared incompleteness", code_block("\n".join(map(str, wincomplete)))))
    if findings:
        vrows.append(("check findings", code_block(
            "\n".join("[%s] %s" % (f[1], f[2]) for f in findings))))
    elif resp is not None and wstat:
        vrows.append(("check findings", pill(OK, " none reported")))
    checks = meta.get("checks") or []
    if checks:
        ids = ", ".join(c.get("id", "?") for c in checks if isinstance(c, dict))
        vrows.append(("contract exit checks declared", esc(ids)))
    parts.append("<h4>Validator / acceptance</h4>" +
                 (kv_table(vrows) if vrows else '<div class="note">%s</div>' % pill(NOT_RUN)))

    # ---- 5b. what the Oracle expects of this stage for this case -----------
    # The Oracle pack states this independently of the implementation, so it is
    # the one place a stage's output can be checked against something it did not
    # author. Nothing here is computed as a verdict: comparison is shown, and
    # where the stage did not run there is nothing to compare.
    expect = ((oracle or {}).get("stage_expectations") or {}).get(sid)
    if expect:
        erows: List[Tuple[str, str]] = []
        must = expect.get("must_exist") or []
        if must:
            erows.append(("must exist", esc(", ".join(map(str, must)))))
        forbid = expect.get("must_not_be_decided") or []
        if forbid:
            erows.append(("must NOT be decided here", esc(", ".join(map(str, forbid)))))
        may_open = expect.get("may_remain_unresolved") or []
        if may_open:
            if resp is None:
                cmp_txt = pill(status)
            else:
                cmp_txt = esc("%d unresolved recorded; the Oracle permits %d named ones. "
                              "IDs are namespaced differently, so this is not an "
                              "automatic match." % (len(open_items), len(may_open)))
            erows.append(("may remain unresolved (%d)" % len(may_open),
                          esc(", ".join(map(str, may_open))[:400])))
            erows.append(("against recorded output", cmp_txt))
        for k in ("provenance_required", "must_be_decided", "must_report",
                  "must_preserve", "must_defer", "conditional"):
            if expect.get(k):
                erows.append((k.replace("_", " "), json_block(expect[k])
                              if not isinstance(expect[k], list)
                              else esc(", ".join(map(str, expect[k])))))
        parts.append("<h4>Oracle expectation for this stage</h4>"
                     '<div class="note">Authored independently of the implementation, in '
                     '<code>%s</code>. Shown for comparison; no verdict is computed here.</div>'
                     % esc(rel(os.path.join(oracle["root"], "stage_expectations.yaml"), REPO))
                     + kv_table(erows) + details("Raw expectation block", json_block(expect)))
    elif oracle:
        parts.append("<h4>Oracle expectation for this stage</h4>"
                     '<div class="note gapnote">%s The Oracle pack for this case declares no '
                     'expectation block for %s.</div>' % (pill(MISSING), esc(sid.upper())))
    else:
        parts.append("<h4>Oracle expectation for this stage</h4>"
                     '<div class="note">%s No Oracle pack exists for this case.</div>'
                     % pill(NA))

    # ---- 6. open problems --------------------------------------------------
    st["unresolved"] = len(open_items)
    st["deferred"] = len(deferred)
    obody = []
    if open_items:
        trs = []
        for u in open_items:
            trs.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(u.get("id")), esc(u.get("decision")),
                esc(", ".join(u.get("kept_open_by") or []) or "—"),
                esc(u.get("alternatives_kind") or "—")))
        obody.append('<h5>Unresolved decisions <span class="pill open">%d</span></h5>'
                     '<table class="grid"><thead><tr><th>id</th><th>decision</th>'
                     '<th>kept open by</th><th>alternatives</th></tr></thead>'
                     '<tbody>%s</tbody></table>' % (len(open_items), "".join(trs)))
        obody.append(details("why each is open", json_block(open_items)))
    if deferred:
        trs = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                      % (esc(d["id"]), esc(d["at"]), esc(d["statement"])) for d in deferred)
        obody.append('<h5>Deferred obligations — handed to a later stage '
                     '<span class="pill warn">%d</span></h5>'
                     '<table class="grid"><thead><tr><th>id</th><th>satisfiable at</th>'
                     '<th>statement</th></tr></thead><tbody>%s</tbody></table>'
                     % (len(deferred), trs))
    if unavailable:
        trs = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                      % (esc(u["id"]), esc(u["route"]), esc(u["statement"])) for u in unavailable)
        obody.append('<h5>Declared un-evidenceable — no available route '
                     '<span class="pill warn">%d</span></h5>'
                     '<table class="grid"><thead><tr><th>entity</th><th>route</th>'
                     '<th>what it is</th></tr></thead><tbody>%s</tbody></table>'
                     % (len(unavailable), trs))
    if not obody:
        obody.append('<div class="note">%s</div>' %
                     (pill(NA) if resp is None else pill(OK, " none recorded")))
    parts.append("<h4>Open problems, unresolved decisions, deferred obligations</h4>"
                 + "".join(obody))

    # ---- 7. provenance and maturity ---------------------------------------
    prows = []
    if resp is not None:
        prov = resp["provenance"]
        prows.append(("execution provenance", provenance_pill(prov)))
        if prov == "FIXTURE_REPLAY":
            prows.append(("what that means",
                          "A recorded response replayed for regression. It is NOT evidence "
                          "that the reasoning works: these recordings were authored with the "
                          "validators in view."))
        if resp.get("prompt_sha"):
            prows.append(("answers prompt sha256", "<code>%s</code>" % esc(resp["prompt_sha"])))
            prows.append(("prompt pairing",
                          "The provider refuses this recording if the stage builds a "
                          "different prompt, so a stale answer cannot be replayed."))
        if resp.get("authored_by"):
            prows.append(("authored by", esc(resp["authored_by"])))
        for k, v in (resp.get("notes") or {}).items():
            prows.append((esc(k), esc(v)))
        prows.append(("artifact", "<code>%s</code>" % esc(rel(resp["path"], REPO))))
    if meta.get("maturity"):
        prows.append(("declared geometry maturity", json_block(meta["maturity"])))
    parts.append("<h4>Provenance and maturity</h4>" +
                 (kv_table(prows) if prows else '<div class="note">%s</div>' % pill(status)))

    # ---- 8. consumer handoff ----------------------------------------------
    crows = []
    if meta.get("consumer"):
        crows.append(("declared consumer requirement", json_block(meta["consumer"])))
    if resp is not None and deferred:
        crows.append(("actually handed forward",
                      esc("%d obligations marked satisfiable at a later stage" % len(deferred))))
    if sid == "s01":
        unused = window.get("unused_s01_families") or []
        crows.append(("consumed by the next stage",
                      code_block("\n".join(unused)) if unused
                      else (pill(OK, " everything referenced") if window else pill(NOT_RUN))))
        if unused:
            crows.append(("reading",
                          "Unreferenced here means the consumer is a LATER stage "
                          "(dimensional freedoms at s03+, quantitative ambiguities at s11). "
                          "It is recorded, not silently dropped."))
    parts.append("<h4>Consumer handoff</h4>" +
                 (kv_table(crows) if crows else '<div class="note">%s</div>' % pill(status)))

    # ---- 9. visual output --------------------------------------------------
    vis = []
    if contract is not None:
        gm = contract.get("maturity_expectations") or {}
        geometry = gm.get("geometry") if isinstance(gm, dict) else None
        spatial = bool(geometry) and str(geometry) not in ("NONE", "['NONE']")
    else:
        spatial = False
    if spatial and status in (NOT_RUN, NOT_IMPL):
        vis.append('<div class="note gapnote">%s This stage would produce spatial output '
                   '(declared maturity: %s) but it has not run for this case, so there is '
                   'nothing to visualise. Reference artifacts below were built by hand and '
                   'are <b>not</b> this stage\'s output.</div>'
                   % (pill(NOT_RUN), esc(json.dumps(geometry))))
    elif not spatial:
        vis.append('<div class="note">%s This stage has no spatial or numerical content to '
                   'visualise; its structured output above is the deliverable.</div>' % pill(NA))
    parts.append("<h4>Visualisation</h4>" + "".join(vis))

    # ---- 10. runtime -------------------------------------------------------
    rrows = []
    if resp is not None:
        rrows.append(("recording size", human_bytes(resp["bytes"])))
        rrows.append(("provider", "offline replay" if resp["provenance"] == "FIXTURE_REPLAY"
                      else "agent-authored, prompt-paired"))
    rrows.append(("runtime measured", pill(NA, " the report layer does not execute stages")))
    parts.append("<h4>Runtime / provider</h4>" + kv_table(rrows))

    provenance = ('<span class="prov">source: %s%s</span>'
                  % (esc(ev["source"]),
                     esc(" · %d finding(s)" % ev["findings"]) if ev["findings"] else ""))
    panel = ('<section class="stage" id="%s"><header class="stagehead">'
             '<h3>%s <span class="sname">%s</span></h3>%s%s</header>%s</section>'
             % (anchor, esc(sid.upper()), esc(meta.get("name", "")),
                pill(status), provenance, "".join(parts)))
    return panel, st


# ---------------------------------------------------- reference artifact track
def render_reference_track(refs: List[Dict[str, Any]], case_id: str,
                          oracle: Optional[Dict[str, Any]], out_dir: str) -> str:
    if not refs:
        return ('<section class="refs"><h3>Reference artifacts</h3>'
                '<div class="note">%s No executable reference exists for this case.</div>'
                '</section>' % pill(NA))
    blocks = []
    for r in refs:
        rows = []
        summary = r.get("summary")
        status_record = r.get("status_record")
        if status_record:
            cert = status_record.get("final_positive_reference_certification")
            rows.append(("final positive-reference certification", verdict_pill(cert)))
            for k in ("development_fast_validation", "full_sampling_reference_validation",
                      "reason", "engineering_failure_observed_before_interruption"):
                if k in status_record:
                    rows.append((k.replace("_", " "), esc(status_record[k])))
        if summary:
            overall = summary.get("overall")
            rows.append(("validator SUMMARY.json overall", verdict_pill(overall)))
            rows.append(("fast mode", verdict_pill(summary.get("fast_mode"))
                         + ('' if not summary.get("fast_mode") else
                            ' <span class="muted">reduced sampling — not a full-sampling '
                            'reference validation</span>')))
            rows.append(("run seconds", esc(summary.get("run_seconds"))))
            rows.append(("geometry signature",
                         "<code>%s</code>" % esc(summary.get("geometry_signature_sha256", ""))[:32]))
            rows.append(("what this means", esc(summary.get("what_this_means", ""))))
            rows.append(("human review", verdict_pill(summary.get("human_review"))))
        elif status_record:
            rows.append(("validator SUMMARY.json",
                         pill(MISSING, " no complete run summary on disk")))
        else:
            rows.append(("validator SUMMARY.json", pill(MISSING)))
        rows.append(("manifest", ("<code>%s</code>" % esc(rel(r["manifest"], REPO)))
                     if r["manifest"] else pill(MISSING, " not generated")))
        gov = r.get("governance") or {}
        if gov:
            rows.append(("reference class", esc(gov.get("reference_class", ""))))
            rows.append(("completion claim", verdict_pill(gov.get("completion_claim"))))

        body = [kv_table(rows)]

        # step results
        if summary and isinstance(summary.get("steps"), dict):
            trs = "".join('<tr><td>%s</td><td>%s</td></tr>'
                          % (esc(k), verdict_pill(v))
                          for k, v in summary["steps"].items())
            body.append('<h5>Validator steps</h5><table class="grid">'
                        '<thead><tr><th>step</th><th>result</th></tr></thead>'
                        '<tbody>%s</tbody></table>' % trs)
            if summary.get("findings"):
                body.append(details("Findings (%d)" % len(summary["findings"]),
                                    json_block(summary["findings"])))

        # Oracle evaluation. The evaluation records only an id and a verdict, so
        # the statement each verdict is ABOUT is joined in from the Oracle pack.
        # Without that join a reader sees a column of PASS and no requirement.
        ae = r.get("actual_evaluation")
        if isinstance(ae, dict) and ae.get("invariants"):
            by_id = {i.get("id"): i for i in ((oracle or {}).get("invariants") or [])
                     if isinstance(i, dict)}
            trs, unjoined = [], 0
            for inv in ae["invariants"]:
                iid = inv.get("invariant_id") or inv.get("invariant") or inv.get("id")
                src = by_id.get(iid)
                if src is None:
                    unjoined += 1
                stat = str(inv.get("status"))
                blocked = inv.get("blocked_on")
                trs.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                    esc(iid),
                    verdict_pill(stat),
                    esc((src or {}).get("statement", "")).strip()
                    or pill(MISSING, " not found in the Oracle pack"),
                    esc(blocked) if blocked else
                    esc(", ".join((src or {}).get("source_locators") or []) or "—")))
            note = ""
            if unjoined:
                note = ('<div class="note gapnote">%s %d of %d evaluated invariants have no '
                        'matching id in the Oracle pack for this case, so their statements '
                        'cannot be shown.</div>' % (pill(WARN), unjoined, len(ae["invariants"])))
            elif not by_id:
                note = ('<div class="note gapnote">%s No Oracle pack was located for this case, '
                        'so only ids and verdicts are available — what each verdict is about '
                        'cannot be shown here.</div>' % pill(MISSING))
            body.append('<h5>Oracle evaluation — each verdict against the invariant it is '
                        'about</h5>' + note +
                        '<table class="grid"><thead><tr><th>invariant</th><th>verdict</th>'
                        '<th>what it requires (from the Oracle pack)</th>'
                        '<th>blocked on / source</th></tr></thead>'
                        '<tbody>%s</tbody></table>' % "".join(trs))
            for key, title in (("maximum_claim", "Maximum claim this evidence supports"),
                               ("scope_warning", "Scope warning"),
                               ("summary", "Evaluation summary")):
                if ae.get(key):
                    v = ae[key]
                    body.append('<div class="note gapnote"><b>%s.</b> %s</div>'
                                % (esc(title), esc(v) if isinstance(v, str)
                                   else esc(json.dumps(v))))
            for key, title in (("requirement_readings", "Requirement readings"),
                               ("phase_b_dynamics_cross_reference", "Dynamics cross-reference"),
                               ("unsupported_and_not_verified", "Explicitly not established")):
                if ae.get(key):
                    body.append(details("%s (%s)" % (esc(title),
                                                     len(ae[key]) if isinstance(ae[key], list)
                                                     else "detail"), json_block(ae[key])))

        # media
        if r["images"]:
            body.append('<h5>Rendered views <span class="muted">(%d — every file, grouped by '
                        'directory; click any image for full size)</span></h5>'
                        % len(r["images"])
                        + grouped_gallery(r["images"], r["root"], out_dir, "image"))
        else:
            body.append('<h5>Rendered views</h5><div class="note">%s</div>' % pill(MISSING))

        if r["videos"] or r["anims"]:
            body.append("<h5>Animations</h5>" +
                        grouped_gallery(r["videos"], r["root"], out_dir, "video") +
                        grouped_gallery(r["anims"], r["root"], out_dir, "anim"))
        elif r["quarantined_media"]:
            body.append('<h5>Animations</h5><div class="note gapnote">%s Every animation for '
                        'this reference is quarantined — see below. None is shown as current '
                        'evidence.</div>' % pill(WARN))
        else:
            body.append('<h5>Animations</h5><div class="note">%s</div>' % pill(MISSING))

        if r["quarantined_media"]:
            qdirs: "OrderedDict[str, int]" = OrderedDict()
            for p in r["quarantined_media"]:
                qdirs[os.path.dirname(rel(p, r["root"]))] = \
                    qdirs.get(os.path.dirname(rel(p, r["root"])), 0) + 1
            listing = "; ".join("%s (%d)" % (d, n) for d, n in qdirs.items())
            body.append('<div class="note gapnote">%s %d media file(s) come from an '
                        '<b>interrupted</b> run and are withheld from the galleries above, '
                        'because a directory left behind by a killed validator is not an '
                        'authoritative artifact source: %s</div>'
                        % (pill(WARN), len(r["quarantined_media"]), esc(listing)))
            body.append(details('Show quarantined media anyway <span class="pill warn">'
                                'NOT AUTHORITATIVE</span>',
                                grouped_gallery(
                                    [p for p in r["quarantined_media"]
                                     if p.lower().endswith(IMG_EXT)], r["root"], out_dir, "image")
                                + grouped_gallery(
                                    [p for p in r["quarantined_media"]
                                     if p.lower().endswith(VID_EXT)], r["root"], out_dir, "video")
                                + grouped_gallery(
                                    [p for p in r["quarantined_media"]
                                     if p.lower().endswith(ANIM_EXT)], r["root"], out_dir, "anim")))

        # simulation
        if r["has_simulation"]:
            simdir = os.path.join(r["root"], "validation", "simulation")
            plots = walk_files(simdir, IMG_EXT)
            body.append("<h5>Simulation</h5>")
            if plots:
                body.append(media_gallery(plots, out_dir, "image"))
            simjson = {k: v for k, v in r["reports"].items() if k.startswith("simulation")}
            if simjson:
                body.append(details("Simulation reports (%d)" % len(simjson),
                                    code_block("\n".join(sorted(simjson)))))
        else:
            body.append('<h5>Simulation</h5><div class="note">%s No dynamics artifacts '
                        'for this reference.</div>' % pill(NA))

        # every validation report, collapsible
        if r["reports"]:
            items = []
            for name in sorted(r["reports"]):
                data = read_json(r["reports"][name])
                stat = (data or {}).get("status") if isinstance(data, dict) else None
                label = "%s %s" % (esc(name), verdict_pill(stat) if stat else "")
                items.append(details(label, json_block(data) if data is not None
                                     else '<div class="note">%s</div>' % pill(MISSING)))
            body.append(details("All validation reports (%d)" % len(r["reports"]),
                                "".join(items)))
        if r.get("other_validation_dirs"):
            listing = "; ".join("<code>%s</code> (%d files)" % (esc(d["name"]), d["files"])
                                for d in r["other_validation_dirs"])
            body.append('<div class="note gapnote">%s This reference also holds %d validation '
                        'director%s left behind by runs that did not finish: %s. Nothing from '
                        'them is included above — an interrupted run is not an authoritative '
                        'artifact source — but they exist on disk and are named here so the '
                        'omission is visible.</div>'
                        % (pill(WARN), len(r["other_validation_dirs"]),
                           "y" if len(r["other_validation_dirs"]) == 1 else "ies", listing))
        blocks.append('<article class="ref"><h4>%s</h4>%s</article>'
                      % (esc(r["ref_id"]), "".join(body)))

    banner = ('<div class="note warnnote"><b>Not stage output.</b> These are '
              'Oracle-aware executable evaluator fixtures, built by hand to validate the '
              'evaluator. No pipeline stage produced them, and their existence is not '
              'evidence that S03–S07 ran.</div>')
    return ('<section class="refs" id="%s-refs"><h3>Reference artifacts</h3>%s%s</section>'
            % (esc(case_id), banner, "".join(blocks)))


# ===========================================================================
# assembly
# ===========================================================================
def build(out_path: str) -> Dict[str, Any]:
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)

    stage_meta = load_stage_meta()
    cases = discover_cases()
    window_reports, report_paths, report_conflicts = load_window_reports()

    inventory: Dict[str, Any] = {
        "cases": {}, "missing": [], "visual_stages": set(),
        "structured_only_stages": set(), "inconsistencies": [],
    }
    issues: List[Dict[str, str]] = inventory["inconsistencies"]

    def flag(severity: str, where: str, what: str) -> None:
        issues.append({"severity": severity, "where": where, "what": what})

    if len(report_paths) > 1:
        flag(WARN, ", ".join(report_paths),
             "%d harness report files exist. Only %s is written by the current harness; "
             "the others are stale copies from before it moved, and a reader cannot tell "
             "which is current from the filesystem alone."
             % (len(report_paths), rel(WINDOW_REPORT, REPO)))
    for c in report_conflicts:
        flag(BAD, c["other"],
             "describes case %s differently from %s (keys: %s)"
             % (c["case"], c["kept"], ", ".join(map(str, c["differing_keys"]))[:200]))

    case_sections: List[str] = []
    summary_rows: List[str] = []
    stage_status: Dict[str, Dict[str, Dict[str, Any]]] = {s: {} for s in STAGE_IDS}

    for case_id, case in cases.items():
        responses = discover_stage_responses(case_id)
        live_outputs = discover_live_stage_outputs(case_id)
        live_trials = discover_live_trials(case_id)
        refs = discover_references(case_id)
        oracle = discover_oracle(case_id)
        window = window_reports.get(case_id, {})
        runs = discover_pipeline_runs(case) if case["kind"] == "BENCHMARK" else []

        # ---- generic consistency checks over this case ---------------------
        if responses and not window:
            flag(WARN, case_id,
                 "has recorded stage output but appears in no harness report. Its execution "
                 "result exists only inside a pytest run, so nothing on disk records it.")
        if case["kind"] == "BENCHMARK" and responses and not runs:
            flag(WARN, "%s/runs/" % case_id,
                 "holds no run directory while stage responses exist. The recordings are "
                 "stage responses, not evidence of a pipeline execution.")
        for r in refs:
            if not r["manifest"]:
                flag(WARN, "%s/%s" % (case_id, r["ref_id"]),
                     "has %d images and %d validation reports but no manifest.yaml, so its "
                     "artifact set is not declared anywhere machine-readable."
                     % (len(r["images"]), len(r["reports"])))
            if r["summary"] is None:
                flag(WARN, "%s/%s" % (case_id, r["ref_id"]),
                     "has no validation/SUMMARY.json; there is no completed validator verdict "
                     "for this reference.")
            elif r["summary"].get("fast_mode"):
                flag(WARN, "%s/%s" % (case_id, r["ref_id"]),
                     "its only SUMMARY.json records fast_mode: true — reduced sampling, not a "
                     "full-sampling reference validation.")
            if r.get("other_validation_dirs"):
                flag(WARN, "%s/%s" % (case_id, r["ref_id"]),
                     "holds %d unfinished validation director%s (%s) whose contents are "
                     "excluded from this report: %s"
                     % (len(r["other_validation_dirs"]),
                        "y" if len(r["other_validation_dirs"]) == 1 else "ies",
                        "%d files" % sum(d["files"] for d in r["other_validation_dirs"]),
                        ", ".join(d["name"] for d in r["other_validation_dirs"])))
            for path, err in find_unparseable_yaml(r["root"]):
                flag(BAD, path, "does not parse as YAML (%s). Nothing reads it, which is why "
                                "this has gone unnoticed." % err)
        if oracle:
            for path, err in find_unparseable_yaml(oracle["root"]):
                flag(BAD, path, "does not parse as YAML (%s)." % err)

        provs = {v["provenance"] for k, v in responses.items() if "::" not in k}
        if len(provs) > 1:
            flag(WARN, case_id, "mixes execution provenance across stages: %s"
                 % ", ".join(sorted(provs)))

        inv = {"stages_with_output": [], "references": len(refs),
               "live_stages": sorted(live_outputs),
               "images": sum(len(r["images"]) for r in refs),
               "videos": sum(len(r["videos"]) + len(r["anims"]) for r in refs),
               "reports": sum(len(r["reports"]) for r in refs),
               "oracle": bool(oracle), "runs": runs}

        panels, rail = [], []
        for sid in STAGE_IDS:
            panel, st = render_stage_panel(case, sid, stage_meta[sid], responses,
                                           window, oracle, out_dir,
                                           live_outputs, live_trials)
            panels.append(panel)
            stage_status[sid][case_id] = st
            if st.get("has_output"):
                inv["stages_with_output"].append(sid)
                inventory["structured_only_stages"].add(sid)
            else:
                inventory["missing"].append("%s/%s: %s" % (case_id, sid, st["status"]))
            cls = {OK: "ok", BAD: "bad", WARN: "warn", NOT_VER: "unver",
                   NOT_RUN: "gap", NOT_IMPL: "gap"}.get(st["status"], "na")
            rail.append('<a class="railchip %s" href="#%s-%s">%s<span>%s</span></a>'
                        % (cls, esc(case_id), sid, esc(sid.upper()),
                           esc("verified" if st["status"] == OK else st["status"])))

        # ---- case header ---------------------------------------------------
        req = read_text(case["request_path"]) if case.get("request_path") else None
        # A classification, not a verdict - so it gets a neutral chip.
        hdr_rows = [("kind", '<span class="chip"><b>%s</b></span>' % esc(case["kind"]))]
        if case["kind"] == "PROBE":
            hdr_rows.append(("purpose", "An unseen micro-probe. Live reasoning evidence: "
                                        "the validators were never fitted to it."))
        hdr_rows.append(("pipeline run outputs",
                         esc(", ".join(runs)) if runs else pill(NOT_RUN,
                             " runs/ holds no run; the recordings below are stage responses, "
                             "not a pipeline execution record")))
        hdr_rows.append(("oracle pack",
                         ('<code>%s</code> — %d invariants (%s)'
                          % (esc(rel(oracle["root"], REPO)), oracle["invariant_count"],
                             esc(oracle["tier"]))) if oracle else pill(NA)))
        hdr_rows.append(("reference artifacts",
                         esc("%d reference(s), %d images, %d clips, %d reports"
                             % (len(refs), inv["images"], inv["videos"], inv["reports"]))
                         if refs else pill(NA)))

        case_sections.append(
            '<section class="case" id="case-%s" data-case="%s">'
            '<h2>%s <span class="muted">%s</span></h2>%s%s%s<div class="rail">%s</div>%s%s</section>'
            % (esc(case_id), esc(case_id), esc(case_id), esc(case["kind"]),
               kv_table(hdr_rows),
               details("Source request", code_block(req or "")) if req
               else '<div class="note">%s source request</div>' % pill(MISSING),
               "", "".join(rail), "".join(panels),
               render_reference_track(refs, case_id, oracle, out_dir)))

        # ---- summary row ---------------------------------------------------
        done = len(inv["stages_with_output"])
        s1 = responses.get("s01")
        s2 = responses.get("s02")
        prov = (s1 or {}).get("provenance") if s1 else None
        counts2 = entity_counts((s2 or {}).get("payload")) if s2 else {}
        counts1 = entity_counts((s1 or {}).get("payload")) if s1 else {}
        unresolved = len(extract_open_items((s2 or {}).get("payload"))) if s2 else 0
        # Every reference gets its own verdict in the cell. Collapsing two
        # references to one status would hide a failure behind a pass.
        if not refs:
            cad_cell = pill(NA)
        else:
            bits = []
            for r in refs:
                sr = r.get("status_record") or {}
                sm = r.get("summary")
                cert = sr.get("final_positive_reference_certification")
                if cert:
                    v = verdict_pill(cert)
                elif sm:
                    v = verdict_pill(sm.get("overall"))
                else:
                    v = pill(MISSING, " no verdict")
                bits.append('<div class="muted" style="white-space:nowrap">%s %s</div>'
                            % (esc(r["ref_id"].replace("EXE-", "")), v))
            cad_cell = "".join(bits)
        summary_rows.append(
            "<tr><td><a href='#case-%s'><b>%s</b></a><div class='muted'>%s</div></td>"
            "<td>%s <span class='muted'>%d/12</span></td>"
            "<td>%s</td><td>%s</td><td class='num'>%s</td><td class='num'>%s</td>"
            "<td class='num'>%s</td><td class='num'>%s</td><td>%s</td><td>%s</td></tr>"
            % (esc(case_id), esc(case_id), esc(case["kind"]),
               '<div class="bar"><span style="width:%d%%"></span></div>' % int(done / 12.0 * 100),
               done,
               verdict_pill(window.get("s01_status")) if window.get("s01_status")
               else pill(MISSING, " no report on disk"),
               provenance_pill(prov),
               counts1.get("Requirement", "—"), counts2.get("Obligation", "—"),
               counts2.get("Candidate", "—"),
               ('<span class="pill open">%d</span>' % unresolved) if unresolved else "0",
               cad_cell,
               # artifacts existing is not a verdict, so this says PRESENT, not PASS
               ('<span class="pill ok">PRESENT</span>'
                if any(r["has_simulation"] for r in refs) else pill(NA))))

        inventory["cases"][case_id] = inv

    # ---- cross-stage comparison -------------------------------------------
    cross = []
    for sid in STAGE_IDS:
        meta = stage_meta[sid]
        cards = []
        for case_id in cases:
            st = stage_status[sid][case_id]
            counts = st.get("counts") or {}
            peek = ", ".join("%s %d" % (k, v) for k, v in list(counts.items())[:4]) or "—"
            cards.append(
                '<a class="xcard %s" href="#%s-%s"><b>%s</b>%s'
                '<div class="muted">%s</div></a>'
                % ({OK: "ok", BAD: "bad", WARN: "warn", NOT_VER: "unver",
                    NOT_RUN: "gap", NOT_IMPL: "gap"}.get(st["status"], "na"),
                   esc(case_id), sid, esc(case_id), pill(st["status"]), esc(peek)))
        cross.append('<div class="xrow"><h3>%s <span class="sname">%s</span></h3>'
                     '<p class="muted">%s</p><div class="xcards">%s</div></div>'
                     % (esc(sid.upper()), esc(meta.get("name", "")),
                        esc(meta.get("question") or meta.get("role") or ""),
                        "".join(cards)))

    tabs = ['<button class="tab active" data-target="view-summary">Summary</button>',
            '<button class="tab" data-target="view-cross">Cross-stage</button>']
    for case_id in cases:
        tabs.append('<button class="tab" data-target="view-%s">%s</button>'
                    % (esc(case_id), esc(case_id)))

    summary_table = (
        '<table class="grid summary"><thead><tr>'
        '<th>case</th><th>stage completion</th><th>S01 harness</th><th>execution provenance</th>'
        '<th>reqs</th><th>obligations</th><th>candidates</th><th>unresolved</th>'
        '<th>CAD</th><th>simulation</th></tr></thead><tbody>%s</tbody></table>'
        % "".join(summary_rows))

    # ---- inconsistencies, computed rather than asserted --------------------
    if issues:
        trs = "".join('<tr><td>%s</td><td><code>%s</code></td><td>%s</td></tr>'
                      % (pill(i["severity"]), esc(i["where"]), esc(i["what"]))
                      for i in sorted(issues, key=lambda i: (i["severity"] != BAD, i["where"])))
        issues_html = ('<table class="grid"><thead><tr><th>severity</th><th>where</th>'
                       '<th>what the artifacts say</th></tr></thead><tbody>%s</tbody></table>'
                       % trs)
    else:
        issues_html = '<div class="note">%s Nothing detected by these checks.</div>' % pill(OK)
    inconsistency_section = (
        '<h3>Inconsistencies detected in the artifacts <span class="pill %s">%d</span></h3>'
        '<p class="muted">Found by comparing artifacts against each other while building this '
        'page — stale duplicate reports, undeclared artifact sets, unparseable files, and '
        'evidence that exists only inside a test run. These are observations about the files '
        'on disk, not judgements about the designs.</p>%s'
        % ("warn" if issues else "ok", len(issues), issues_html))

    views = ['<div class="view active" id="view-summary">'
             '<h2>Summary</h2>'
             '<div class="note warnnote"><b>Absence is never success.</b> No pipeline run '
             'output exists for any case: <code>ver3/benchmarks/*/runs/</code> holds only '
             'placeholders. S01 and S02 rows below are <i>recorded stage responses</i>. '
             'S03–S12 are NOT IMPLEMENTED or NOT RUN and are shown as such. CAD artifacts '
             'are hand-built evaluator fixtures, not stage output.</div>'
             + summary_table + inconsistency_section +
             '<h3>Legend</h3><div class="legend">%s %s %s %s %s %s %s %s %s</div>'
             '<p class="muted">MISSING — expected and absent. NOT RUN — the machinery exists '
             'but was not executed here. NOT IMPLEMENTED — the machinery does not exist yet. '
             'NOT APPLICABLE — nothing of this kind is expected here. NOT VERIFIED — output '
             'exists and nothing on disk checked it. CONTRACT INCOMPLETE — the stage ran '
             'and declared, itemised, what evidence it could not supply; neither a '
             'pass nor a failure.</p></div>'
             % (pill(OK), pill(BAD), pill(WARN), pill(OPEN), pill(NOT_VER),
                pill(INCOMPLETE), pill(MISSING), pill(NOT_RUN), pill(NOT_IMPL))]
    views.append('<div class="view" id="view-cross"><h2>Cross-stage comparison</h2>'
                 '<p class="muted">Same stage, every case side by side. Identical counts and '
                 'identical wording across cases would indicate boilerplate rather than '
                 'product-specific reasoning.</p>%s</div>' % "".join(cross))
    for case_id, section in zip(cases, case_sections):
        views.append('<div class="view" id="view-%s">%s</div>' % (esc(case_id), section))

    generated_note = (
        "Generated by ver3/tools/build_pipeline_dashboard.py — a read-only report layer. "
        "Rebuild at any time; it imports no stage module and runs no validator.")

    doc = HTML_SHELL % {
        "tabs": "".join(tabs),
        "views": "".join(views),
        "note": esc(generated_note),
        "css": CSS, "js": JS,
    }
    with open(out_path, "w") as fh:
        fh.write(doc)

    inventory["visual_stages"] = sorted(inventory["visual_stages"])
    inventory["structured_only_stages"] = sorted(inventory["structured_only_stages"])
    return inventory


CSS = """
:root{--bg:#0f1115;--panel:#161a21;--panel2:#1b2029;--line:#262d38;--tx:#e6e9ef;
--mut:#9aa4b2;--ok:#2f9e63;--bad:#d1495b;--warn:#c9862a;--open:#7d5bbe;--na:#4b5563;--acc:#4f8ef7}
*{box-sizing:border-box}
a{color:#7fb0ff}
a:visited{color:#a48ff0}
.summary a,.xcard,.railchip{color:var(--tx)}
.summary a{font-size:14px}
body{margin:0;background:var(--bg);color:var(--tx);
font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header.top{position:sticky;top:0;z-index:20;background:#0c0e12;border-bottom:1px solid var(--line);
padding:10px 16px}
h1{font-size:16px;margin:0 0 8px}
.tabs{display:flex;gap:6px;flex-wrap:wrap}
.tab{background:var(--panel);color:var(--mut);border:1px solid var(--line);border-radius:6px;
padding:5px 11px;font-size:13px;cursor:pointer}
.tab:hover{color:var(--tx)}
.tab.active{background:var(--acc);border-color:var(--acc);color:#fff}
main{padding:18px;max-width:1500px;margin:0 auto}
.view{display:none}.view.active{display:block}
h2{font-size:20px;margin:14px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:16px;margin:18px 0 8px}
h4{font-size:13px;margin:16px 0 6px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
h5{font-size:13px;margin:12px 0 6px}
.muted{color:var(--mut);font-size:12px}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:600;
border:1px solid transparent;white-space:nowrap}
.pill.ok{background:rgba(47,158,99,.16);color:#61d69a;border-color:rgba(47,158,99,.4)}
.pill.bad{background:rgba(209,73,91,.16);color:#ff8a99;border-color:rgba(209,73,91,.45)}
.pill.warn{background:rgba(201,134,42,.16);color:#e8b168;border-color:rgba(201,134,42,.45)}
.pill.open{background:rgba(125,91,190,.18);color:#b79cf0;border-color:rgba(125,91,190,.45)}
.pill.gap{background:rgba(75,85,99,.25);color:#c2cad6;border-color:#3b4455}
.pill.na{background:rgba(75,85,99,.18);color:var(--mut);border-color:#333c4a}
table{border-collapse:collapse;width:100%;margin:6px 0}
table.kv th{text-align:left;color:var(--mut);font-weight:500;width:230px;vertical-align:top;
padding:5px 10px 5px 0;border-bottom:1px solid var(--line);font-size:12px}
table.kv td{padding:5px 0;border-bottom:1px solid var(--line);vertical-align:top}
table.grid{font-size:12.5px;background:var(--panel);border:1px solid var(--line);border-radius:6px;
overflow:hidden}
table.grid th{background:var(--panel2);text-align:left;padding:7px 9px;color:var(--mut);
font-weight:600;border-bottom:1px solid var(--line)}
table.grid td{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}
table.grid tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.summary td{vertical-align:middle}
.bar{background:var(--panel2);border-radius:4px;height:8px;width:110px;display:inline-block;
overflow:hidden;vertical-align:middle;margin-right:6px}
.bar span{display:block;height:100%;background:var(--ok)}
pre.code{background:#0b0d11;border:1px solid var(--line);border-radius:6px;padding:10px;
overflow:auto;max-height:460px;font-size:12px;line-height:1.45;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;word-break:break-word}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:#a8c7fa}
details{border:1px solid var(--line);border-radius:6px;margin:6px 0;background:var(--panel)}
details>summary{cursor:pointer;padding:7px 10px;font-size:12.5px;color:var(--tx);
list-style:none;user-select:none}
details>summary::-webkit-details-marker{display:none}
details>summary:before{content:"\\25B8";margin-right:7px;color:var(--mut);display:inline-block}
details[open]>summary:before{transform:rotate(90deg)}
.dbody{padding:0 10px 10px}
section.stage{border:1px solid var(--line);border-radius:8px;background:var(--panel);
padding:12px 14px;margin:12px 0}
.stagehead{display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--line);
padding-bottom:8px;margin-bottom:4px}
.stagehead h3{margin:0;font-size:15px}
.sname{color:var(--mut);font-weight:400;font-size:13px}
.prov{color:var(--mut);font-size:11px;font-style:italic}
section.case>h2{font-size:22px}
.rail{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}
.railchip{display:flex;flex-direction:column;align-items:center;gap:2px;text-decoration:none;
background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:6px 10px;
min-width:78px;color:var(--tx);font-size:12px;font-weight:600}
.railchip span{font-size:9.5px;color:var(--mut);font-weight:500;text-transform:uppercase}
.railchip.ok{border-color:rgba(47,158,99,.5)}
.railchip.gap{opacity:.62}
.railchip:hover{border-color:var(--acc)}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:3px 8px;
font-size:12px;color:var(--mut)}
.chip b{color:var(--tx)}
.note{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--na);
border-radius:5px;padding:8px 11px;margin:6px 0;font-size:12.5px}
.gapnote{border-left-color:var(--warn)}
.warnnote{border-left-color:var(--acc)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:8px 0}
figure{margin:0;background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:6px}
figure img,figure video{width:100%;display:block;border-radius:4px;background:#fff}
figure video{background:#000}
figcaption{font-size:10.5px;color:var(--mut);margin-top:5px;word-break:break-all}
.clip{grid-column:span 2}
section.refs{border:1px dashed var(--line);border-radius:8px;padding:12px 14px;margin:18px 0;
background:rgba(79,142,247,.03)}
article.ref{border-top:1px solid var(--line);padding-top:10px;margin-top:12px}
.xrow{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:10px 14px;
margin:10px 0}
.xcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}
.xcard{display:block;text-decoration:none;color:var(--tx);background:var(--panel2);
border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:12px}
.xcard.ok{border-color:rgba(47,158,99,.45)}
.xcard.unver{border-color:rgba(79,142,247,.45)}
.railchip.unver{border-color:rgba(79,142,247,.5)}
.pill.unver{background:rgba(79,142,247,.14);color:#8fb6fb;border-color:rgba(79,142,247,.45)}
.pill.incomplete{background:rgba(201,134,42,.22);color:#f0c07a;border-color:#c9862a;
border-style:dashed}
.xcard.incomplete{border-color:#c9862a;border-style:dashed}
.railchip.incomplete{border-color:#c9862a;border-style:dashed}
.xcard.gap{opacity:.6}
.xcard:hover{border-color:var(--acc)}
.xcard b{display:block;margin-bottom:3px}
.orthorow{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0}
.orthofig{margin:0;background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:6px}
svg.ortho{width:320px;height:320px;background:#0b0d11;border-radius:4px}
text.olabel{fill:#9aa4b2;font-size:9px;font-family:ui-monospace,monospace}
.legend{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 20px}
footer{color:var(--mut);font-size:11.5px;padding:20px 18px;border-top:1px solid var(--line);
margin-top:24px}
"""

JS = """
(function(){
  function show(id){
    document.querySelectorAll('.view').forEach(function(v){v.classList.toggle('active',v.id===id)});
    document.querySelectorAll('.tab').forEach(function(t){
      t.classList.toggle('active', t.dataset.target===id)});
  }
  document.querySelectorAll('.tab').forEach(function(t){
    t.addEventListener('click',function(){ show(t.dataset.target);
      history.replaceState(null,'','#'+t.dataset.target); });
  });
  // deep links: #BM-001-s03 opens the right view and scrolls to the stage
  function openHash(){
    var h=decodeURIComponent(location.hash.replace('#',''));
    if(!h) return;
    if(document.getElementById(h) && h.indexOf('view-')===0){ show(h); return; }
    var el=document.getElementById(h);
    if(!el) return;
    var view=el.closest('.view');
    if(view){ show(view.id); }
    setTimeout(function(){ el.scrollIntoView({block:'start'});
      el.style.outline='2px solid var(--acc)';
      setTimeout(function(){el.style.outline='';},1600); },40);
  }
  window.addEventListener('hashchange',openHash);
  openHash();
  // expand / collapse all within a view
  document.addEventListener('keydown',function(e){
    if(e.key==='e'&&e.altKey){document.querySelectorAll('.view.active details')
      .forEach(function(d){d.open=true});}
    if(e.key==='c'&&e.altKey){document.querySelectorAll('.view.active details')
      .forEach(function(d){d.open=false});}
  });
})();
"""

HTML_SHELL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASSY pipeline dashboard</title>
<style>%(css)s</style></head><body>
<header class="top">
  <h1>ASSY pipeline dashboard <span class="muted">— benchmark → stage → output → validation</span></h1>
  <div class="tabs">%(tabs)s</div>
</header>
<main>%(views)s</main>
<footer>%(note)s<br>Alt+E expands every collapsed block in the active view, Alt+C collapses them.</footer>
<script>%(js)s</script>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output",
                    default=os.path.join(VER3, "out", "pipeline_dashboard.html"))
    args = ap.parse_args()
    inv = build(args.output)

    print("wrote %s" % rel(os.path.abspath(args.output), REPO))
    print("\nARTIFACTS DISCOVERED")
    for case_id, c in inv["cases"].items():
        print("  %-8s stages with output: %-14s refs:%d images:%d clips:%d reports:%d oracle:%s"
              % (case_id, ",".join(c["stages_with_output"]) or "none",
                 c["references"], c["images"], c["videos"], c["reports"], c["oracle"]))
    print("\nMISSING / NOT RUN / NOT IMPLEMENTED  (%d stage slots)" % len(inv["missing"]))
    by_status: Dict[str, List[str]] = {}
    for m in inv["missing"]:
        slot, status = m.rsplit(": ", 1)
        by_status.setdefault(status, []).append(slot)
    for status, slots in sorted(by_status.items()):
        print("  %-16s %d  e.g. %s" % (status, len(slots), ", ".join(slots[:4])))
    print("\nINCONSISTENCIES (%d)" % len(inv["inconsistencies"]))
    for i in inv["inconsistencies"]:
        print("  [%s] %s\n        %s" % (i["severity"], i["where"], i["what"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
