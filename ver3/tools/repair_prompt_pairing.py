"""Re-pair recorded stage responses with a changed prompt -- but only when they
still answer it.

WHY THIS EXISTS
    AgentAuthoredProvider refuses a recording whose `_meta.answers_prompt_sha256`
    does not match the prompt the stage now builds. That is the pairing doing its
    job: a response to a question no longer being asked is stale.

    When a prompt changes in a way that alters WHAT IS ASKED, the recordings are
    genuinely dead and must be re-authored. When it changes only how the answer's
    FORMAT is specified, and a recording already conforms to that format, the
    recording does still answer the new prompt and re-stamping it is honest.

    Deciding which case applies is not something a hash can do, so this tool does
    not decide it either. It VERIFIES: it pushes each recording through the real
    parser, the real contract validation and the real completeness check, and
    re-stamps only those that pass. Anything that fails is left stale and
    reported, because a recording that no longer works is evidence, not a chore.

This tool never edits response CONTENT. It writes one field: _meta.answers_prompt_sha256.

Usage:
    python ver3/tools/repair_prompt_pairing.py            # report only
    python ver3/tools/repair_prompt_pairing.py --write    # re-stamp what passes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from ver3.assy_v3.providers.agent_authored import prompt_hash               # noqa: E402
from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture  # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (             # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.state import DesignState, project_for                     # noqa: E402

FIXTURES = os.path.join(REPO, "ver3", "assy_v3", "fixtures", "responses")
PROBES = os.path.join(REPO, "ver3", "assy_v3", "probes")
BENCHMARKS = os.path.join(REPO, "ver3", "benchmarks")


def request_text(case_id: str) -> Optional[str]:
    for path in (os.path.join(BENCHMARKS, case_id, "source", "request.txt"),
                 os.path.join(PROBES, case_id, "request.txt")):
        if os.path.isfile(path):
            with open(path) as fh:
                return fh.read()
    return None


def cases_under(root: str) -> List[str]:
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if os.path.isfile(os.path.join(root, d, "s01.json")))


def check_case(root: str, case_id: str) -> List[Dict[str, Any]]:
    """Rebuild each prompt and verify the recording still satisfies the stage.

    Returns one row per stage: the new hash, whether the recording is already
    paired, and whether it still parses and validates.
    """
    rows: List[Dict[str, Any]] = []
    text = request_text(case_id)
    if text is None:
        return [{"case": case_id, "stage": "s01", "verified": False,
                 "problems": ["no request text found for this case"]}]

    state = DesignState(run_id="repair-%s" % case_id)

    for stage_id, stage, inputs in (
            ("s01", S01RequirementCapture(), {"request_text": text}),
            ("s02", S02ObligationAndCandidates(), None)):
        path = os.path.join(root, case_id, "%s.json" % stage_id)
        if not os.path.isfile(path):
            continue
        if inputs is None:
            inputs = {"projection": project_for("s02", state)}

        with open(path) as fh:
            payload = json.load(fh)

        new_hash = prompt_hash(stage.prompt(inputs))
        declared = (payload.get("_meta") or {}).get("answers_prompt_sha256")

        problems: List[str] = []
        try:
            ops = stage.to_operations({k: v for k, v in payload.items()
                                       if not k.startswith("_")})
            missing = stage.completeness(payload, inputs)
        except Exception as exc:                                    # noqa: BLE001
            rows.append({"case": case_id, "stage": stage_id, "path": path,
                         "new_hash": new_hash, "already_paired": declared == new_hash,
                         "verified": False,
                         "problems": ["response shape: %s: %s"
                                      % (type(exc).__name__, exc)]})
            break

        from ver3.assy_v3.state.patch import StagePatch
        patch = StagePatch(
            patch_id="repair-%s-%s" % (case_id, stage_id), run_id=state.run_id,
            stage_id=stage_id, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=ops,
            execution_status="SUCCESS", provenance={"purpose": stage.purpose,
                                                    "provider": "verification"},
            declared_incompleteness=missing)
        problems = state.validate(patch)
        verified = not problems and not missing
        rows.append({"case": case_id, "stage": stage_id, "path": path,
                     "new_hash": new_hash, "already_paired": declared == new_hash,
                     "verified": verified,
                     "problems": problems + (["declared incomplete: %s" % missing]
                                             if missing else [])})
        if not verified:
            break
        state.apply(patch)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="re-stamp the pairing hash on verified recordings")
    args = ap.parse_args()

    rows: List[Dict[str, Any]] = []
    for root in (FIXTURES, PROBES):
        for case_id in cases_under(root):
            rows.extend(check_case(root, case_id))

    stale = [r for r in rows if not r.get("already_paired")]
    broken = [r for r in rows if not r.get("verified")]

    for r in rows:
        state = ("paired" if r.get("already_paired")
                 else ("re-pairable" if r["verified"] else "STALE AND BROKEN"))
        print("  %-8s %-4s %-16s %s" % (r["case"], r["stage"], state,
                                        "; ".join(map(str, r["problems"]))[:110]))
    print("\n%d recording(s); %d not paired with the current prompt; "
          "%d do not satisfy the stage" % (len(rows), len(stale), len(broken)))

    if broken:
        print("\nNOT re-stamping anything: a recording that no longer satisfies the "
              "stage does not answer the new prompt, and stamping it would make the "
              "pairing lie. Re-author these, or revert the prompt change.")
        return 1

    if not args.write:
        print("\nreport only; pass --write to re-stamp the %d verified recording(s)"
              % len(stale))
        return 0

    written = 0
    for r in stale:
        with open(r["path"]) as fh:
            payload = json.load(fh)
        meta = payload.setdefault("_meta", {})
        meta["answers_prompt_sha256"] = r["new_hash"]
        note = ("re-paired after the response-schema section was added to the "
                "prompt; content unchanged and re-verified against the parser, "
                "contract validation and completeness check")
        history = meta.setdefault("pairing_history", [])
        if note not in history:
            history.append(note)
        with open(r["path"], "w") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.write("\n")
        written += 1
    print("\nre-stamped %d recording(s). Content was not modified." % written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
