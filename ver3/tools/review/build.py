"""Build the review surface from the evidence already in a review directory.

    python -m ver3.tools.review.build <review-dir> [--title T] [--subtitle S]

Reads the JSON evidence each stage directory holds, renders the figures it can,
and writes REPORT.md and index.html. Rendering a stage is skipped - not faked -
when its evidence is absent, so the same command extends the SAME report as
later stages produce output.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional


def _read(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def render(root: str) -> Dict[str, list]:
    from . import report, s04, s05, s06
    made: Dict[str, list] = {"s04": [], "s05": [], "s06": []}

    state = _read(os.path.join(root, "s04", "state_summary.json"))
    entities = (state or {}).get("entities") or {}
    branch = (state or {}).get("branch") or ""
    if entities:
        for fn, name in ((s04.spatial_layout, "spatial_layout"),
                         (s04.joint_frames, "joint_frames"),
                         (s04.states_and_motion, "states_and_motion")):
            made["s04"].append(fn(entities, os.path.join(root, "s04", name + ".png"), branch))

    raw = _read(os.path.join(root, "s05", "raw_model_response.json"))
    verdict = _read(os.path.join(root, "s05", "boundary_verdict.json")) or {}
    standing = _read(os.path.join(root, "s05", "accepted_state_summary.json")) or {}
    readiness = _read(os.path.join(root, "s06", "solver_input.json")) or {}
    if raw and raw.get("response"):
        from ...assy_v3.downstream import embodiment as EMB
        accepted = bool(verdict.get("accepted"))
        # WHICH ROWS ARE DRAWN. Accepted -> the canonical standing rows are the
        # design. Rejected -> the proposal is drawn, stamped, and never mixed in.
        rows = ({"features": standing.get("entities", {}).get("Feature") or [],
                 "parameters": standing.get("entities", {}).get("Parameter") or [],
                 "constraints": standing.get("entities", {}).get("Constraint") or [],
                 "kinematic_realizations":
                     standing.get("entities", {}).get("KinematicRealization") or []}
                if accepted else raw["response"])
        polarity = EMB.polarity_table()
        findings = verdict.get("structural_problems_recomputed") or []
        made["s05"].append(s05.write_boundary(
            raw, verdict, standing, readiness,
            os.path.join(root, "s05", "write_boundary.png"), branch))
        made["s05"].append(s05.embodiment_overview(
            rows, entities, polarity,
            os.path.join(root, "s05", "embodiment_overview.png"), branch, accepted))
        made["s05"].append(s05.feature_map(
            rows, entities, polarity,
            os.path.join(root, "s05", "feature_map.png"), branch, accepted))
        made["s05"].append(s05.kinematic_realizations(
            rows, entities, os.path.join(root, "s05", "kinematic_realizations.png"),
            branch, accepted))
        made["s05"].append(s05.interfaces(
            rows, entities, os.path.join(root, "s05", "interfaces.png"), branch,
            accepted, findings))
        made["s05"].append(s05.parameter_constraint_graph(
            rows, os.path.join(root, "s05", "parameter_constraint_graph.png"),
            branch, accepted))

    si = _read(os.path.join(root, "s06", "solver_input.json"))
    sr = _read(os.path.join(root, "s06", "solver_result.json"))
    if si is not None and sr is not None:
        made["s06"].append(s06.constraint_graph(
            si, os.path.join(root, "s06", "constraint_graph.png"), branch))
        made["s06"].append(s06.parameter_values(
            sr, si, os.path.join(root, "s06", "parameter_values.png"), branch))
    return made


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root")
    ap.add_argument("--title", default=None)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    from . import report
    if not args.no_figures:
        made = render(root)
        for stage, paths in made.items():
            for p in paths:
                print("figure:", os.path.relpath(p, root))
    state = _read(os.path.join(root, "s04", "state_summary.json")) or {}
    title = args.title or ("ASSY Ver3.0 - design review: %s"
                           % (state.get("design") or os.path.basename(root)))
    md, page = report.write(root, title, args.subtitle)
    print("REPORT.md:", md)
    print("index.html:", page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
