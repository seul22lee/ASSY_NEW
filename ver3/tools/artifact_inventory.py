"""Every artifact that can influence a replay, and exactly one disposition each.

A TOOL, not production code: it walks case directories and names cases, and a
case identifier inside assy_v3 is FP-02.

WHY AN INVENTORY AT ALL

S-9 regenerates fixtures from live output. That is only bounded if "which
artifacts are fixtures" has a mechanical answer. Before this, the answer was a
sentence in a document, and the sentence had already been wrong once: the
pre-flight counted the active corpus by looking at two directories, while 69
stored responses named by producing pass sat unreachable because replay addressed
them by owner.

DERIVED, NEVER LISTED

Nothing here hard-codes a file. The corpus is whatever the replay providers can
actually resolve, computed from the same responsibility identities the pipeline
uses, so an artifact that becomes consumable without being classified shows up as
a failure rather than as a silence.

THE DISPOSITIONS ARE NOT A RANKING

They answer different questions and do not collapse:

    CURRENT_REGENERATION_TARGET   replay resolves it now; S9-E must replace it
                                  with live-derived output
    HISTORICAL_LIVE_EVIDENCE      a real past live response; never promoted,
                                  never given fabricated provenance
    HISTORICAL_MIGRATION_EVIDENCE kept to explain how the corpus moved
    REPLAY_REGRESSION_ONLY        deterministic regression use only, never
                                  capability evidence
    RETIRE                        encodes a shape the pipeline no longer speaks
    FROZEN_SOURCE_OR_REFERENCE    source truth. Not derived, not regenerable,
                                  not S-9's to touch
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.pipeline import PRODUCING_RESPONSIBILITIES        # noqa: E402
from ver3.assy_v3.providers import replay_integrity as ri           # noqa: E402

VER3 = os.path.join(REPO, "ver3")
FIXTURES = os.path.join(VER3, "assy_v3", "fixtures", "responses")
PROBES = os.path.join(VER3, "assy_v3", "probes")
BENCHMARKS = os.path.join(VER3, "benchmarks")
LIVE_RUNS = os.path.join(VER3, "live_runs")

CURRENT_REGENERATION_TARGET = "CURRENT_REGENERATION_TARGET"
HISTORICAL_LIVE_EVIDENCE = "HISTORICAL_LIVE_EVIDENCE"
HISTORICAL_MIGRATION_EVIDENCE = "HISTORICAL_MIGRATION_EVIDENCE"
REPLAY_REGRESSION_ONLY = "REPLAY_REGRESSION_ONLY"
RETIRE = "RETIRE"
FROZEN_SOURCE_OR_REFERENCE = "FROZEN_SOURCE_OR_REFERENCE"

DISPOSITIONS = (CURRENT_REGENERATION_TARGET, HISTORICAL_LIVE_EVIDENCE,
                HISTORICAL_MIGRATION_EVIDENCE, REPLAY_REGRESSION_ONLY,
                RETIRE, FROZEN_SOURCE_OR_REFERENCE)


def _rel(path: str) -> str:
    return os.path.relpath(path, REPO)


def replay_roots() -> List[str]:
    """Where the replay providers look. Taken from the runners' own constants."""
    return [FIXTURES, PROBES]


def resolvable_responsibility(filename: str):
    """The producing responsibility a replay lookup would resolve this file for.

    `<responsibility>.json` and nothing else. `s02.pre_revision.json` resolves
    for nothing, which is exactly why it is not a current fixture.
    """
    stem = filename[:-5] if filename.endswith(".json") else None
    return stem if stem in PRODUCING_RESPONSIBILITIES else None


def active_replay_artifacts() -> List[Dict[str, Any]]:
    """What a replay provider can actually serve today, derived by resolution."""
    out: List[Dict[str, Any]] = []
    for root in replay_roots():
        if not os.path.isdir(root):
            continue
        for case in sorted(os.listdir(root)):
            case_dir = os.path.join(root, case)
            if not os.path.isdir(case_dir):
                continue
            for name in sorted(os.listdir(case_dir)):
                if not name.endswith(".json"):
                    continue
                responsibility = resolvable_responsibility(name)
                path = os.path.join(case_dir, name)
                with open(path) as fh:
                    body = fh.read()
                identities = ri.fixture_identities(body)
                missing = [k for k, v in identities.items() if not v]
                out.append({
                    "path": _rel(path),
                    "case": case,
                    "responsibility": responsibility,
                    "resolvable": responsibility is not None,
                    "consumer": "OfflineReplayProvider/AgentAuthoredProvider"
                                if responsibility else "none",
                    "declares_pairing": bool(ri.declared_pairing(body)),
                    "missing_identities": missing,
                    "migration_bridge": ri.MIGRATION_BRIDGE_KEY in body,
                    "disposition": (CURRENT_REGENERATION_TARGET if responsibility
                                    else HISTORICAL_MIGRATION_EVIDENCE),
                })
    return out


def historical_live_artifacts() -> List[Dict[str, Any]]:
    """`live_runs` in full. Every one is historical evidence and stays that way."""
    out: List[Dict[str, Any]] = []
    for dirpath, _dirs, files in os.walk(LIVE_RUNS):
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            stem = name[:-5] if name.endswith(".json") else name
            out.append({
                "path": _rel(path),
                "kind": ("stage_response" if stem in PRODUCING_RESPONSIBILITIES
                         or re.match(r"^s0\d[a-b]?$", stem) else stem),
                "responsibility": stem if stem in PRODUCING_RESPONSIBILITIES else None,
                # ADDRESSABLE ONLY BY THE PASS THAT PRODUCED IT. The old lookup
                # keyed on the owner, so anything named for a second pass could
                # never be requested at all.
                "old_addressing_reachable": stem in ("s01", "s02", "s03", "s04"),
                "disposition": HISTORICAL_LIVE_EVIDENCE,
            })
    return out


def frozen_sources() -> List[Dict[str, Any]]:
    """Source truth: requests, manifests, oracle and reference material."""
    out: List[Dict[str, Any]] = []
    for base, pattern in ((BENCHMARKS, ("request.txt", "source_manifest.yaml")),
                          (PROBES, ("request.txt",))):
        for dirpath, _dirs, files in os.walk(base):
            for name in sorted(files):
                if name in pattern:
                    out.append({"path": _rel(os.path.join(dirpath, name)),
                                "disposition": FROZEN_SOURCE_OR_REFERENCE})
    return out


def inventory() -> Dict[str, Any]:
    active = active_replay_artifacts()
    historical = historical_live_artifacts()
    frozen = frozen_sources()
    everything = active + historical + frozen

    by_disposition: Dict[str, List[str]] = {d: [] for d in DISPOSITIONS}
    for item in everything:
        by_disposition[item["disposition"]].append(item["path"])

    return {
        "active": active,
        "historical_live": historical,
        "frozen": frozen,
        "by_disposition": by_disposition,
        "counts": {d: len(paths) for d, paths in by_disposition.items()},
        "regeneration_targets": sorted(
            i["path"] for i in active
            if i["disposition"] == CURRENT_REGENERATION_TARGET),
        "old_addressing_unreachable": sorted(
            i["path"] for i in historical
            if i["responsibility"] and not i["old_addressing_reachable"]),
    }


def main() -> int:
    inv = inventory()
    print("ACTIVE REPLAY CORPUS      %d" % len(inv["active"]))
    print("HISTORICAL LIVE ARTIFACTS %d" % len(inv["historical_live"]))
    print("FROZEN SOURCES/REFERENCES %d" % len(inv["frozen"]))
    print()
    for disposition, paths in sorted(inv["counts"].items()):
        print("  %-32s %d" % (disposition, paths))
    print()
    print("REGENERATION TARGETS (%d):" % len(inv["regeneration_targets"]))
    for path in inv["regeneration_targets"]:
        print("   ", path)
    print()
    print("historical responses unreachable under old owner-keyed replay: %d"
          % len(inv["old_addressing_unreachable"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
