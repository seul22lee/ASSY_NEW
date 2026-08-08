"""Score every available S01/S02 output for engineering maturity and lay the
benchmarks beside the probes.

The comparison this prints is between MATURITY PROFILES, never between answers.
Each output is scored against its own source and its own internal references, so
a probe is never penalised for being about a different product -- which is the
whole point, and the thing a diff against a benchmark answer would get wrong.

Sources of output, discovered rather than named:
    recorded   ver3/assy_v3/fixtures/responses/<case>/  and  probes/<case>/
    live       ver3/live_runs/<provider>/<label>/responses/<case>/t<N>/

Usage:
    python ver3/tools/compare_maturity.py
    python ver3/tools/compare_maturity.py --live-label regression_final
    python ver3/tools/compare_maturity.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from ver3.tools.quality_profile import (                                    # noqa: E402
    MATURITY_KEYS, maturity_index, profile_s01, profile_s02)

FIXTURES = os.path.join(REPO, "ver3", "assy_v3", "fixtures", "responses")
PROBES = os.path.join(REPO, "ver3", "assy_v3", "probes")
BENCHMARKS = os.path.join(REPO, "ver3", "benchmarks")
LIVE_ROOT = os.path.join(REPO, "ver3", "live_runs")


def source_for(case_id: str) -> Optional[str]:
    for path in (os.path.join(BENCHMARKS, case_id, "source", "request.txt"),
                 os.path.join(PROBES, case_id, "request.txt")):
        if os.path.isfile(path):
            with open(path) as fh:
                return fh.read()
    return None


def load(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except Exception:                                                # noqa: BLE001
        return None


def kind_of(case_id: str) -> str:
    """Whether a case is a quality REFERENCE or an EVALUATION probe, decided by
    where it lives rather than by its name."""
    return "benchmark" if os.path.isdir(os.path.join(BENCHMARKS, case_id)) else "probe"


def collect() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(case_id: str, origin: str, trial: str,
            s01: Optional[Dict[str, Any]], s02: Optional[Dict[str, Any]]) -> None:
        source = source_for(case_id)
        if source is None or s01 is None:
            return
        p1 = profile_s01(s01, source)
        p2 = profile_s02(s02, s01) if s02 else None
        combined = dict(p1)
        if p2:
            combined.update({k: v for k, v in p2.items() if k != "_counts"})
        index, applied = maturity_index(combined)
        rows.append({"case": case_id, "kind": kind_of(case_id), "origin": origin,
                     "trial": trial, "s01": p1, "s02": p2,
                     "maturity": index, "metrics_applied": applied,
                     "has_s02": p2 is not None})

    for root in (FIXTURES, PROBES):
        if not os.path.isdir(root):
            continue
        for case_id in sorted(os.listdir(root)):
            d = os.path.join(root, case_id)
            if not os.path.isdir(d):
                continue
            add(case_id, "recorded", "-",
                load(os.path.join(d, "s01.json")), load(os.path.join(d, "s02.json")))

    if os.path.isdir(LIVE_ROOT):
        for provider in sorted(os.listdir(LIVE_ROOT)):
            for label in sorted(os.listdir(os.path.join(LIVE_ROOT, provider))):
                rdir = os.path.join(LIVE_ROOT, provider, label, "responses")
                if not os.path.isdir(rdir):
                    continue
                for case_id in sorted(os.listdir(rdir)):
                    for trial in sorted(os.listdir(os.path.join(rdir, case_id))):
                        t = os.path.join(rdir, case_id, trial)
                        add(case_id, "live:%s/%s" % (provider, label), trial,
                            load(os.path.join(t, "s01.json")),
                            load(os.path.join(t, "s02.json")))
    return rows


def summarise(rows: List[Dict[str, Any]], title: str) -> None:
    if not rows:
        return
    print("\n%s" % title)
    for r in sorted(rows, key=lambda r: (r["kind"], r["case"], r["trial"])):
        idx = "  n/a" if r["maturity"] is None else "%5.3f" % r["maturity"]
        print("   %-10s %-9s %-3s  maturity %s over %2d metrics   s02:%s"
              % (r["case"], r["kind"], r["trial"], idx, r["metrics_applied"],
                 "yes" if r["has_s02"] else "NO"))


def gap_table(reference: List[Dict[str, Any]], evaluated: List[Dict[str, Any]],
              left: str = "bench", right: str = "probe") -> None:
    """Per-metric medians. A gap is a QUALITY difference; a metric that is
    None on one side had no opportunity to appear and is skipped, not scored 0."""
    print("\n%-52s %8s %8s %7s" % ("metric", left, right, "gap"))
    print("-" * 79)
    gaps = []
    for key in MATURITY_KEYS:
        def vals(rows):
            out = []
            for r in rows:
                for part in (r["s01"], r["s02"]):
                    if part and isinstance(part.get(key), (int, float)):
                        out.append(part[key])
            return out
        b, p = vals(reference), vals(evaluated)
        if not b or not p:
            continue
        mb, mp = statistics.median(b), statistics.median(p)
        gaps.append((mp - mb, key, mb, mp))
    for d, key, mb, mp in sorted(gaps):
        flag = "  <-- gap" if d <= -0.15 else ("  (%s ahead)" % right if d >= 0.15 else "")
        print("%-52s %8.3f %8.3f %+7.3f%s" % (key[:52], mb, mp, d, flag))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live-label", default=None,
                    help="restrict live rows to this run label")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    rows = collect()
    if args.live_label:
        rows = [r for r in rows
                if r["origin"] == "recorded" or r["origin"].endswith("/" + args.live_label)]

    recorded = [r for r in rows if r["origin"] == "recorded"]
    live = [r for r in rows if r["origin"] != "recorded"]

    summarise(recorded, "RECORDED (agent-authored) — the current quality bar")
    summarise(live, "LIVE (independent provider) — what is being stabilised")

    def med(rows, pred):
        v = [r["maturity"] for r in rows if pred(r) and r["maturity"] is not None]
        return statistics.median(v) if v else None

    print("\nMEDIAN MATURITY INDEX")
    for label, rs in (("recorded", recorded), ("live", live)):
        b = med(rs, lambda r: r["kind"] == "benchmark")
        p = med(rs, lambda r: r["kind"] == "probe")
        print("   %-9s benchmarks %s   probes %s   %s"
              % (label,
                 "  n/a" if b is None else "%5.3f" % b,
                 "  n/a" if p is None else "%5.3f" % p,
                 "" if (b is None or p is None) else
                 "probe-vs-benchmark gap %+.3f" % (p - b)))

    if live:
        print("\nPER-METRIC, LIVE ONLY — benchmarks as the reference, probes as the evaluation set")
        gap_table([r for r in live if r["kind"] == "benchmark"],
                  [r for r in live if r["kind"] == "probe"])

    print("\nRECORDED reference profile (the maturity the window has demonstrated)")
    gap_table([r for r in recorded if r["kind"] == "benchmark"],
              [r for r in recorded if r["kind"] == "probe"])

    if live:
        print("\nTHE ACTUAL TARGET — recorded (the demonstrated bar) vs live reasoning,"
              "\nover ALL cases, because the deficit turns out not to be probe-specific")
        gap_table(recorded, live, left="recorded", right="live")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(rows, fh, indent=1, sort_keys=True)
        print("\nwrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
