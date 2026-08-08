"""Run the S01 -> S02 window on one case and report what happened.

A TOOL, not production code: it lives outside assy_v3 because it takes case
identifiers as arguments, and a case identifier inside the production package is
FP-02 (benchmark-ID branching, retirement row R-14).

Not a test. An evaluation harness: it runs the window, applies every check, and
prints findings without deciding whether they are acceptable.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from ver3.assy_v3.providers.offline import OfflineReplayProvider          # noqa: E402
from ver3.assy_v3.stages.s01_requirement_capture import (                 # noqa: E402
    S01RequirementCapture, sharpening_check, locator_check, mechanism_leakage_check)
from ver3.assy_v3.stages.s02_obligation_and_candidates import (           # noqa: E402
    S02ObligationAndCandidates, no_selection_check, load_case_check,
    candidate_distinctness_check, known_principle_check, evidence_route_check,
    magnitude_fidelity_check,
    created_obligations_check, requirement_coverage_check, obligation_scope_check,
    candidate_coverage_check, openness_citation_check, actor_citation_check)
from ver3.assy_v3.state import DesignState, project_for                   # noqa: E402

FIXTURES = os.path.join(REPO, "ver3", "assy_v3", "fixtures", "responses")
BENCHMARKS = os.path.join(REPO, "ver3", "benchmarks")


def request_text(case_id: str) -> str:
    with open(os.path.join(BENCHMARKS, case_id, "source", "request.txt")) as fh:
        return fh.read()


def run_case(case_id: str) -> Dict[str, Any]:
    provider = OfflineReplayProvider(FIXTURES, case_id)
    state = DesignState(run_id="win-%s" % case_id)
    report: Dict[str, Any] = {"case": case_id, "findings": []}

    # ---- s01: the only stage that sees the request -----------------------
    text = request_text(case_id)
    out1 = S01RequirementCapture().run(provider, {"request_text": text}, state, state.run_id)
    report["s01_status"] = out1.execution_status.value
    report["s01_problems"] = out1.problems
    report["s01_incomplete"] = out1.declared_incompleteness
    if out1.patch is None:
        report["findings"].append(("S01", "NO_PATCH", out1.problems))
        return report
    state.apply(out1.patch)

    for name, fn in (("sharpening", lambda: sharpening_check(state, text)),
                     ("locator", lambda: locator_check(state)),
                     ("mechanism_leak", lambda: mechanism_leakage_check(state, text))):
        for p in fn():
            report["findings"].append(("S01", name, p))

    # ---- interface: what s02 is allowed to see ---------------------------
    proj = project_for("s02", state)
    report["projection_families"] = sorted(proj)
    if "SourceClause" in proj:
        report["findings"].append(("IFACE", "source_text_leaked_to_s02", "SourceClause present"))

    # ---- s02: consumes the projection only -------------------------------
    out2 = S02ObligationAndCandidates().run(provider, {"projection": proj}, state, state.run_id)
    report["s02_status"] = out2.execution_status.value
    report["s02_problems"] = out2.problems
    report["s02_incomplete"] = out2.declared_incompleteness
    if out2.patch is None:
        report["findings"].append(("S02", "NO_PATCH", out2.problems))
        return report
    if out2.problems:
        for p in out2.problems:
            report["findings"].append(("S02", "contract", p))
        return report
    state.apply(out2.patch)

    for name, fn in (("no_selection", lambda: no_selection_check(state)),
                     ("load_case", lambda: load_case_check(state)),
                     ("magnitude_fidelity", lambda: magnitude_fidelity_check(state)),
                     ("distinctness", lambda: candidate_distinctness_check(state)),
                     ("known_principle", lambda: known_principle_check(state)),
                     ("evidence_route", lambda: evidence_route_check(state)),
                     ("created_obligations", lambda: created_obligations_check(state)),
                     ("requirement_coverage", lambda: requirement_coverage_check(state)),
                     ("obligation_scope", lambda: obligation_scope_check(state)),
                     ("candidate_coverage", lambda: candidate_coverage_check(state)),
                     ("openness_citation", lambda: openness_citation_check(state)),
                     ("actor_citation", lambda: actor_citation_check(state))):
        for p in fn():
            report["findings"].append(("S02", name, p))

    # ---- interface: unused and reconstructed -----------------------------
    report["counts"] = state.counts()
    report["unused_s01_families"] = _unused(state, proj)
    return report


def _unused(state, proj) -> List[str]:
    """S01 output that no S02 entity references. Dead information."""
    referenced = set()
    for fam in ("Obligation", "LoadCase", "Candidate", "AcceptanceContract",
                "UnresolvedDecision"):
        for e in state.family(fam):
            for v in e.values():
                for item in (v if isinstance(v, list) else [v]):
                    if isinstance(item, str):
                        referenced.add(item)
    unused = []
    for fam in ("Requirement", "Scenario", "Actor", "Freedom", "Ambiguity"):
        ids = [e["entity_id"] for e in state.family(fam)]
        dead = [i for i in ids if i not in referenced]
        if dead:
            unused.append("%s: %d/%d unreferenced %s" % (fam, len(dead), len(ids), dead))
    return unused


if __name__ == "__main__":
    cases = sys.argv[1:]
    if not cases:
        cases = sorted(d for d in os.listdir(FIXTURES)
                       if os.path.isdir(os.path.join(FIXTURES, d)))
    all_reports = []
    for c in cases:
        r = run_case(c)
        all_reports.append(r)
        print("=" * 72)
        print(c, "| s01:", r.get("s01_status"), "| s02:", r.get("s02_status"))
        if r.get("counts"):
            print("   counts:", r["counts"])
        for f in r["findings"]:
            print("   [%s/%s] %s" % f)
        for u in r.get("unused_s01_families", []):
            print("   [IFACE/unused] %s" % u)
        if r.get("s01_incomplete"):
            print("   s01 declared incomplete:", r["s01_incomplete"])
        if r.get("s02_incomplete"):
            print("   s02 declared incomplete:", r["s02_incomplete"])
    with open(os.path.join(HERE, "window_report.json"), "w") as fh:
        json.dump(all_reports, fh, indent=1, sort_keys=True)
    print("\nwrote window_report.json")
