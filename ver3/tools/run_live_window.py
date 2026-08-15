"""Run the frozen S01 -> S02 window against a live provider, repeatedly.

A TOOL, not production code. It lives outside assy_v3 because it takes case
identifiers as arguments, and a case identifier inside the production package is
FP-02 (benchmark-ID branching, retirement row R-14).

WHAT IT IS FOR
    The window has only ever been exercised by responses this repository's own
    agent authored. That is debt D-2. This harness runs the SAME prompts, the
    SAME parser and the SAME fourteen checks against an independent model, many
    times, at a non-zero temperature, and records everything needed to tell
    whether the implementation holds or whether it only held because the author
    of the validators also wrote the answers.

HOW IT TREATS FAILURE
    It collects. A live model will emit responses the parser was never shown,
    and a traceback in trial 3 would destroy the evidence from trials 4..N. So
    every stage execution is wrapped, every failure is classified into one of a
    small set of kinds, and the run continues. Nothing is fixed while the
    evidence is still being gathered.

    The classification distinguishes a PROVIDER condition (a rate limit says
    nothing about the design), a RESPONSE condition (unparseable or truncated),
    a PARSER condition (our code raised on a response shape it did not expect --
    a defect in us, not in the model), a CONTRACT condition (well-formed but
    under-covered) and a CHECK finding (the response is valid and a validator
    objects to its content). Only the last is evidence about reasoning quality.

Usage:
    python ver3/tools/run_live_window.py --trials 3 --temperature 1.0
    python ver3/tools/run_live_window.py --cases BM-001 PRB-02 --trials 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

import yaml                                                                # noqa: E402
from ver3.assy_v3.stages.s01_requirement_capture import (                  # noqa: E402
    sharpening_check, locator_check, mechanism_leakage_check)
from ver3.assy_v3.stages.s02_obligation_and_candidates import (            # noqa: E402
    S02ObligationAndCandidates, no_selection_check, load_case_check,
    candidate_distinctness_check, known_principle_check, evidence_route_check,
    created_obligations_check, requirement_coverage_check, obligation_scope_check,
    candidate_coverage_check, openness_citation_check, actor_citation_check)
from ver3.assy_v3.pipeline import (CHECK_FINDING, PARSER_DEFECT,           # noqa: E402
                                   PROVIDER_CONDITION, Progression,
                                   full_live_qualification,
                                   response_source_of, window1)
from ver3.assy_v3.providers.offline import OfflineReplayProvider           # noqa: E402
from ver3.assy_v3.assurance import problems as assurance_problems
from ver3.assy_v3.state import DesignState                    # noqa: E402
from ver3.live_providers import env as env_loader                          # noqa: E402
from ver3.live_providers.deepseek import DeepSeekProvider                  # noqa: E402

BENCHMARKS = os.path.join(REPO, "ver3", "benchmarks")
FIXTURES = os.path.join(REPO, "ver3", "assy_v3", "fixtures", "responses")
PROBES = os.path.join(REPO, "ver3", "assy_v3", "probes")
ENV_FILE = os.path.join(REPO, "ver3", ".env")
OUT_ROOT = os.path.join(REPO, "ver3", "live_runs", "deepseek")

# FAILURE KINDS COME FROM THE PIPELINE. They were defined here and again in
# run_window2 with slightly different membership, which is how one condition came
# to have two names. Imported above; only CHECK_FINDING and the contract kinds are
# evidence about reasoning, the rest are about the wire, the format or our code.


def discover_cases() -> "Dict[str, str]":
    """case_id -> path of its request text. Directories, not a hard-coded list."""
    cases: Dict[str, str] = {}
    for root, sub in ((BENCHMARKS, os.path.join("source", "request.txt")),
                      (PROBES, "request.txt")):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name, sub)
            if os.path.isfile(path):
                cases[name] = path
    return cases


def read(path: str) -> str:
    with open(path) as fh:
        return fh.read()


S01_CHECKS = ("sharpening", "locator", "mechanism_leak")
S02_CHECKS = ("no_selection", "load_case", "distinctness", "known_principle",
              "evidence_route", "created_obligations", "requirement_coverage",
              "obligation_scope", "candidate_coverage", "openness_citation",
              "actor_citation")


def recording_root(case_id: str) -> Optional[str]:
    """Where this case's recorded stage responses live, if any."""
    for root in (FIXTURES, PROBES):
        if os.path.isfile(os.path.join(root, case_id, "s01.json")):
            return root
    return None


def design_profile(case_id: str) -> Optional[Dict[str, Any]]:
    """The user's structured profile, beside the request it accompanies.

    Read here as well as in Window 2 because the SEEDING path used to ingest it
    and the live path did not, so the same source produced different committed
    state depending on which runner ran it. Same locations, same verbatim read.
    """
    for name in ("design_profile.json", "design_profile.yaml"):
        for base in (os.path.join(BENCHMARKS, case_id, "source"),
                     os.path.join(PROBES, case_id)):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                with open(path) as fh:
                    return yaml.safe_load(fh)
    return None


def run_trial(case_id: str, request_path: str, provider: DeepSeekProvider,
              trial: int, seed_s01: bool = False) -> Dict[str, Any]:
    """One full S01 -> S02 pass. Returns a trial record; never raises.

    seed_s01 is a DIAGNOSTIC, not a pipeline mode. It replays the recorded S01
    response so that S02 can be exercised live even while S01 cannot complete.
    A trial run this way is evidence about S02 ONLY: its S01 half is a fixture,
    and it is labelled as such in the record so the two can never be conflated.
    """
    text = read(request_path)
    state = DesignState(run_id="live-%s-t%d" % (case_id, trial))
    progression = Progression()
    rec: Dict[str, Any] = {
        "case": case_id, "trial": trial, "failures": [], "counts": {},
        "s01_status": None, "s02_status": None,
        "s01_response": None, "s02_response": None,
    }

    def fail(kind: str, stage: str, what: str, detail: Any = None) -> None:
        rec["failures"].append({"kind": kind, "stage": stage, "what": what,
                                "detail": detail})

    s01_provider = provider
    if seed_s01:
        root = recording_root(case_id)
        if root is None:
            fail(PROVIDER_CONDITION, "s01", "no recording to seed from")
            return rec
        s01_provider = OfflineReplayProvider(root, case_id)
    # Read from what the providers DECLARE, so the record cannot say "live"
    # because of the script that happened to start the run.
    rec["s01_provider"] = response_source_of(s01_provider)
    rec["s02_provider"] = response_source_of(provider)

    # ------------------------------------------------------- s01 and s02
    # THE CANONICAL PROGRESSION. This runner used to call S01's inner driver
    # directly, which skipped the ConsumerView, the readiness gate and the view
    # record - the one path in the repository that did. It now goes where every
    # other caller goes, and differs from the replay runner in its provider only.
    started = time.time()
    _out1, out2 = window1(provider, state, text, progression,
                          design_profile=design_profile(case_id),
                          s01_provider=s01_provider)
    rec["s01_seconds"] = round(time.time() - started, 2)
    e1 = progression.by_responsibility("s01")
    rec["s01_status"] = e1.execution_status if e1 else None
    rec["s01_view_status"] = e1.view_status if e1 else None
    rec["s01_response"] = _out1.raw_response if _out1 else _last_raw(provider)
    rec["s01_declared_incomplete"] = _out1.declared_incompleteness if _out1 else None
    if e1 is None or not e1.patch_applied:
        rec["failures"] = progression.failures
        return rec

    for name, fn in (("sharpening", lambda: sharpening_check(state, text)),
                     ("locator", lambda: locator_check(state)),
                     ("mechanism_leak", lambda: mechanism_leakage_check(state, text))):
        try:
            for p in fn():
                fail(CHECK_FINDING, "s01", name, p)
        except Exception as exc:                                    # noqa: BLE001
            fail(PARSER_DEFECT, "s01", "check %s raised: %s" % (name, exc))

    # ------------------------------------------------------ interface / s02
    # S02 already ran inside the canonical progression above, against the same
    # provider and through the same boundary. What is left here is reporting.
    rec["projection_families"] = sorted(
        S02ObligationAndCandidates().consumer_view(state).payload())
    e2 = progression.by_responsibility("s02")
    rec["s02_status"] = e2.execution_status if e2 else None
    rec["s02_view_status"] = e2.view_status if e2 else None
    rec["s02_response"] = out2.raw_response if out2 else _last_raw(provider)
    rec["s02_declared_incomplete"] = out2.declared_incompleteness if out2 else None
    if e2 is None or not e2.patch_applied:
        rec["counts"] = state.counts()
        rec["failures"] = progression.failures + rec["failures"]
        return rec

    for name, fn in (("no_selection", lambda: no_selection_check(state)),
                     ("load_case", lambda: load_case_check(state)),
                     # QUANTITATIVE CONTINUITY MOVED (S-8 / U-9). The stage that
                     # carried the number no longer certifies that it did not
                     # sharpen it; the independent layer reads the committed
                     # Requirement and LoadCase and answers that.
                     ("quantitative_continuity",
                      lambda: assurance_problems(state, "quantitative_continuity")),
                     ("distinctness", lambda: candidate_distinctness_check(state)),
                     ("known_principle", lambda: known_principle_check(state)),
                     ("evidence_route", lambda: evidence_route_check(state)),
                     ("created_obligations", lambda: created_obligations_check(state)),
                     ("requirement_coverage", lambda: requirement_coverage_check(state)),
                     ("obligation_scope", lambda: obligation_scope_check(state)),
                     ("candidate_coverage", lambda: candidate_coverage_check(state)),
                     ("openness_citation", lambda: openness_citation_check(state)),
                     ("actor_citation", lambda: actor_citation_check(state))):
        try:
            for p in fn():
                fail(CHECK_FINDING, "s02", name, p)
        except Exception as exc:                                    # noqa: BLE001
            fail(PARSER_DEFECT, "s02", "check %s raised: %s" % (name, exc))

    rec["counts"] = state.counts()
    rec["unused_s01_families"] = _unused(state)
    rec["progression"] = progression.as_record()
    # S01->S02 is not the full chain, so this can only ever be False here. It is
    # recorded anyway, with its reasons, so a window-1 trial can never be read as
    # end-to-end evidence by a later reader who did not know which tool ran it.
    qualified, reasons = full_live_qualification(progression)
    rec["full_live"] = {"qualified": qualified, "reasons": reasons}
    return rec


def _last_raw(provider) -> Optional[str]:
    """The response text of the most recent call, so a trial that died inside
    the parser still records what the model actually said."""
    for record in reversed(provider.records):
        raw = (record.get("response") or {}).get("raw_text")
        if raw:
            return raw
    return None


def _unused(state) -> List[str]:
    referenced = set()
    for fam in ("Obligation", "LoadCase", "Candidate", "AcceptanceContract",
                "UnresolvedDecision"):
        for e in state.family(fam):
            for v in e.values():
                for item in (v if isinstance(v, list) else [v]):
                    if isinstance(item, str):
                        referenced.add(item)
    out = []
    for fam in ("Requirement", "Scenario", "Actor", "Freedom", "Ambiguity"):
        ids = [e["entity_id"] for e in state.family(fam)]
        dead = [i for i in ids if i not in referenced]
        if dead:
            out.append("%s: %d/%d unreferenced" % (fam, len(dead), len(ids)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="*", default=None)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--model", default=None)
    ap.add_argument("--label", default=None, help="output directory name")
    ap.add_argument("--seed-s01", action="store_true",
                    help="DIAGNOSTIC: replay the recorded S01 response so S02 can be "
                         "exercised live. Such a trial is evidence about S02 only.")
    ap.add_argument("--no-json-mode", action="store_true",
                    help="do not use the provider's json_object response format")
    args = ap.parse_args()

    names = env_loader.load(ENV_FILE)
    if names:
        print("loaded %s: %s" % (os.path.relpath(ENV_FILE, REPO),
                                 env_loader.describe(names)))

    all_cases = discover_cases()
    case_ids = args.cases or sorted(all_cases)
    unknown = [c for c in case_ids if c not in all_cases]
    if unknown:
        print("unknown cases: %s (known: %s)" % (unknown, sorted(all_cases)))
        return 2

    label = args.label or time.strftime("%Y%m%dT%H%M%S")
    out_dir = os.path.join(OUT_ROOT, label)
    os.makedirs(os.path.join(out_dir, "responses"), exist_ok=True)

    provider = DeepSeekProvider(model=args.model, temperature=args.temperature,
                                json_object_mode=not args.no_json_mode)
    caps = provider.capabilities()
    print("provider %s | model requested %s | temperature %.2f | json mode %s"
          % (caps.provider_id, caps.model_id, args.temperature,
             not args.no_json_mode))
    print("%d case(s) x %d trial(s) = %d window runs, 2 model calls each"
          % (len(case_ids), args.trials, len(case_ids) * args.trials))

    trials: List[Dict[str, Any]] = []
    for trial in range(1, args.trials + 1):
        for case_id in case_ids:
            t0 = time.time()
            rec = run_trial(case_id, all_cases[case_id], provider, trial,
                            seed_s01=args.seed_s01)
            # Structured answers are kept as files; nothing else from the call is.
            for stage in ("s01", "s02"):
                raw = rec.pop("%s_response" % stage)
                if raw:
                    d = os.path.join(out_dir, "responses", case_id, "t%d" % trial)
                    os.makedirs(d, exist_ok=True)
                    with open(os.path.join(d, "%s.json" % stage), "w") as fh:
                        fh.write(raw)
            trials.append(rec)
            kinds = {}
            for f in rec["failures"]:
                kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
            print("  t%d %-8s s01=%-20s s02=%-20s %5.1fs  %s"
                  % (trial, case_id, rec["s01_status"], rec["s02_status"],
                     time.time() - t0,
                     ", ".join("%s:%d" % kv for kv in sorted(kinds.items())) or "clean"))
            with open(os.path.join(out_dir, "trials.json"), "w") as fh:
                json.dump(trials, fh, indent=1, sort_keys=True)
            with open(os.path.join(out_dir, "model_run_records.json"), "w") as fh:
                json.dump(provider.records, fh, indent=1, sort_keys=True)

    # ------------------------------------------------------------- summary
    by_kind: Dict[str, int] = {}
    for t in trials:
        for f in t["failures"]:
            by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    print("\nfailures by kind: %s" % (by_kind or "none"))
    print("wrote %s" % os.path.relpath(out_dir, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
