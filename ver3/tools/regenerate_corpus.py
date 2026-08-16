"""S9-E: replace the agent-authored corpus with live-derived fixtures.

A TOOL, not production code: it names cases, and a case identifier inside
assy_v3 is FP-02.

WHAT REGENERATION MEANS HERE

    frozen source
    -> canonical stage invocation (the same one live and replay both use)
    -> DeepSeek
    -> the raw response, retained
    -> the ordinary parser
    -> the ordinary contracts
    -> the ordinary write boundary
    -> an accepted patch
    -> FIRST_CONFORMING promotion
    -> a fixture bound to source, responsibility, content and run evidence
    -> strict CURRENT replay through the ordinary pipeline

Nothing here parses a response itself, fixes one, or decides whether an answer is
good. If a response will not parse, that is a recorded failed attempt; if it
parses and fails a contract, that is a different recorded failed attempt. Both are
evidence, and neither is repaired.

TEMPERATURE IS AN EXPERIMENT DECISION, DECLARED BEFORE THE ANSWERS ARE SEEN.

The first regeneration attempt used the stage's requested 0.0, on the reasoning
that a fixture should be the answer the pipeline asks for rather than a sample.
Greedy decoding degenerated: S02 emitted 206 near-duplicate obligations and ran to
the token cap without closing the object, twice, at two different caps.

The repository's own live protocol already answers this - both live runners default
to `--temperature 1.0`, and `run_live_window` exists to run "many times, at a
non-zero temperature". So regeneration uses the established live setting, declared
here as an experiment override and recorded per attempt by S9-B. That is a choice
about the experiment, made before seeing any answer; it is not resampling until an
answer is liked, and the promotion rule remains FIRST_CONFORMING.
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
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.pipeline import Progression, window1                 # noqa: E402
from ver3.assy_v3.pipeline import promotion as pr                      # noqa: E402
from ver3.assy_v3.providers import replay_integrity as ri              # noqa: E402
from ver3.assy_v3.providers.offline import OfflineReplayProvider       # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus              # noqa: E402
from ver3.assy_v3.state import DesignState                             # noqa: E402
from ver3.live_providers import env as env_loader                      # noqa: E402
from ver3.live_providers.deepseek import DeepSeekProvider              # noqa: E402

VER3 = os.path.join(REPO, "ver3")
FIXTURES = os.path.join(VER3, "assy_v3", "fixtures", "responses")
PROBES = os.path.join(VER3, "assy_v3", "probes")
BENCHMARKS = os.path.join(VER3, "benchmarks")
ENV_FILE = os.path.join(VER3, ".env")
OUT_ROOT = os.path.join(VER3, "live_runs", "s9e")

#: Window 1 is what the active corpus holds. S03/S04 have never had fixtures,
#: and inventing them is not regeneration - it is new corpus, which S9-E does not
#: create.
WINDOW1 = ("s01", "s02")


def case_source(case_id: str):
    """(request path, corpus root) for a case, or (None, None)."""
    bm = os.path.join(BENCHMARKS, case_id, "source", "request.txt")
    if os.path.isfile(bm):
        return bm, FIXTURES
    prb = os.path.join(PROBES, case_id, "request.txt")
    if os.path.isfile(prb):
        return prb, PROBES
    return None, None


class _Recording:
    """Wraps the live provider to keep the prompt and raw text per responsibility.

    The prompt is needed to compute the pairing, and only the provider sees it -
    the stage builds it inside `invoke`. Reading it here rather than rebuilding it
    later is what keeps the pairing a fact about the call that happened.
    """

    def __init__(self, inner):
        self.inner = inner
        self.provider_id = inner.provider_id
        self.response_source = inner.response_source
        self.prompts: Dict[str, str] = {}
        self.raw: Dict[str, str] = {}
        self.records: List[Dict[str, Any]] = inner.records

    def capabilities(self):
        return self.inner.capabilities()

    def generate(self, request, attempt_index: int = 0):
        responsibility = ri.producing_identity(request)
        self.prompts[responsibility] = request.prompt_text
        result = self.inner.generate(request, attempt_index)
        if result.response is not None:
            self.raw[responsibility] = result.response.raw_text
        return result


def _rung(execution, outcome) -> str:
    """Which rung of the promotion ladder this attempt reached."""
    if outcome is None:
        return pr.PARSER_FAILED
    status = outcome.execution_status
    if status in (ExecutionStatus.PROVIDER_RATE_LIMIT,
                  ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED,
                  ExecutionStatus.PROVIDER_UNAVAILABLE,
                  ExecutionStatus.PROVIDER_TIMEOUT):
        return pr.PROVIDER_FAILED
    if status is ExecutionStatus.RESPONSE_TRUNCATED:
        return pr.RESPONSE_UNUSABLE
    if status is ExecutionStatus.RESPONSE_PARSE_FAILURE:
        return pr.PARSER_FAILED
    if status is ExecutionStatus.SCHEMA_FAILURE:
        return pr.CONTRACT_FAILED
    if execution is None or not execution.patch_applied:
        return pr.NOT_ACCEPTED
    return pr.ACCEPTED


def _attempt_from(responsibility, source_sha, execution, outcome, raw,
                  records, index) -> pr.AttemptOutcome:
    model_run_id = None
    for record in reversed(records):
        if record.get("responsibility") == responsibility or True:
            model_run_id = record.get("model_run_id")
            break
    return pr.AttemptOutcome(
        responsibility_id=responsibility, source_sha256=source_sha,
        model_run_id=model_run_id or "", attempt_index=index,
        stage=_rung(execution, outcome), raw_response=raw,
        problems=tuple(outcome.problems) if outcome else ())


def regenerate_case(case_id: str, provider_factory, out_dir: str,
                    max_attempts: int = 3) -> Dict[str, Any]:
    """Live window-1, with bounded retries for a non-conforming responsibility.

    S02 IS RETRIED AGAINST THE COMMITTED S01 IT ANSWERED. Its prompt is derived
    from that state, and the pairing binds the response to that prompt - so a
    corpus that took S01 from one pass and S02 from another would hold two halves
    that never met. The retry re-invokes S02 alone against the state the promoted
    S01 produced.

    Bounded and declared: `max_attempts` per responsibility, and FIRST_CONFORMING
    decides among whatever they produce. A non-conforming attempt is retained.
    """
    request_path, corpus_root = case_source(case_id)
    if request_path is None:
        return {"case": case_id, "error": "no source"}
    with open(request_path, "rb") as fh:
        source_bytes = fh.read()
    source_sha = ri.canonical_source_identity(source_bytes)
    request_text = source_bytes.decode("utf-8")

    run_id = "s9e-%s" % case_id
    attempts: List[pr.AttemptOutcome] = []
    prompts: Dict[str, str] = {}
    per_responsibility: Dict[str, Any] = {"s01": [], "s02": []}
    all_records: List[Dict[str, Any]] = []
    state = None
    started = time.time()

    # ---- S01, and the state S02 must answer against ----------------------
    for index in range(1, max_attempts + 1):
        state = DesignState(run_id=run_id)
        progression = Progression()
        provider = _Recording(provider_factory())
        from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture
        from ver3.assy_v3.pipeline import execute_stage
        out, execution = execute_stage(S01RequirementCapture(), provider, state,
                                       progression,
                                       inputs={"request_text": request_text,
                                               "design_profile": None})
        all_records.extend(provider.records)
        prompts.setdefault("s01", provider.prompts.get("s01", ""))
        attempt = _attempt_from("s01", source_sha, execution, out,
                                provider.raw.get("s01"), provider.records, index)
        attempts.append(attempt)
        per_responsibility["s01"].append(
            {"attempt": index, "rung": attempt.stage,
             "problems": list(out.problems) if out else [],
             "raw_chars": len(provider.raw.get("s01") or "")})
        if attempt.stage == pr.ACCEPTED:
            prompts["s01"] = provider.prompts.get("s01", "")
            break

    s01_ok = any(a.responsibility_id == "s01" and a.stage == pr.ACCEPTED
                 for a in attempts)

    # ---- S02 against THAT state ------------------------------------------
    if s01_ok:
        from ver3.assy_v3.stages.s02_obligation_and_candidates import (
            S02ObligationAndCandidates)
        from ver3.assy_v3.pipeline import execute_stage
        for index in range(1, max_attempts + 1):
            import copy
            trial_state = copy.deepcopy(state)
            progression = Progression()
            provider = _Recording(provider_factory())
            out, execution = execute_stage(S02ObligationAndCandidates(), provider,
                                           trial_state, progression)
            all_records.extend(provider.records)
            prompts.setdefault("s02", provider.prompts.get("s02", ""))
            attempt = _attempt_from("s02", source_sha, execution, out,
                                    provider.raw.get("s02"), provider.records,
                                    index)
            attempts.append(attempt)
            per_responsibility["s02"].append(
                {"attempt": index, "rung": attempt.stage,
                 "problems": list(out.problems)[:2] if out else [],
                 "raw_chars": len(provider.raw.get("s02") or "")})
            if attempt.stage == pr.ACCEPTED:
                prompts["s02"] = provider.prompts.get("s02", "")
                state = trial_state
                break

    elapsed = round(time.time() - started, 1)
    os.makedirs(os.path.join(out_dir, case_id), exist_ok=True)
    for attempt in attempts:
        if attempt.raw_response:
            name = "%s.a%d.raw.json" % (attempt.responsibility_id,
                                        attempt.attempt_index)
            with open(os.path.join(out_dir, case_id, name), "w") as fh:
                fh.write(attempt.raw_response)
    with open(os.path.join(out_dir, case_id, "model_run_records.json"), "w") as fh:
        json.dump(all_records, fh, indent=1, sort_keys=True)

    return {"case": case_id, "corpus_root": corpus_root,
            "source_sha256": source_sha, "run_id": run_id,
            "seconds": elapsed, "attempts": attempts, "prompts": prompts,
            "per_responsibility": per_responsibility,
            "counts": state.counts() if state else {}}


def promote_case(result: Dict[str, Any], ledger_entries: Dict[str, Any],
                 write: bool) -> Dict[str, Any]:
    """FIRST_CONFORMING, per responsibility. Nothing is chosen by content."""
    promoted = {}
    for responsibility in WINDOW1:
        candidates = [a for a in result["attempts"]
                      if a.responsibility_id == responsibility]
        decision = pr.select_for_promotion(candidates)
        chosen = decision["chosen"]
        entry = {"rule": decision["rule"],
                 "eligible": decision["eligible_count"],
                 "promoted": False,
                 "problems": [p for c in decision["considered"]
                              for p in c["problems"]]}
        if chosen is not None:
            prompt = result["prompts"].get(responsibility, "")
            body = pr.fixture_body(chosen, prompt)
            fidelity = ri.promotion_fidelity_problems(body, chosen.raw_response)
            entry["fidelity_problems"] = fidelity
            if not fidelity:
                path = os.path.join(result["corpus_root"], result["case"],
                                    "%s.json" % responsibility)
                if write:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as fh:
                        fh.write(body)
                ledger_entries[chosen.model_run_id] = pr.ledger_entry(chosen)
                entry.update({"promoted": True, "path": path,
                              "model_run_id": chosen.model_run_id})
        promoted[responsibility] = entry
    return promoted


def verify_current_replay(case_id: str, corpus_root: str, source_sha: str,
                          prompts: Dict[str, str],
                          ledger: Dict[str, Any]) -> Dict[str, Any]:
    """Strict CURRENT replay of what was just written, ordinary path only."""
    from ver3.assy_v3.providers.interfaces import GenerationRequest
    out = {}
    for responsibility in WINDOW1:
        provider = OfflineReplayProvider(
            corpus_root, case_id, trust=ri.CURRENT_REPLAY,
            source_sha256=source_sha, ledger=ledger)
        request = GenerationRequest(
            purpose="verify", stage_id=responsibility[:3],
            prompt_text=prompts.get(responsibility, ""),
            max_output_tokens=1, deadline_s=1.0,
            responsibility_id=responsibility)
        result = provider.generate(request)
        out[responsibility] = {
            "status": result.execution_status.value,
            "integrity": provider.last_integrity.get(
                "current_fixture_integrity"),
            "problems": provider.last_integrity.get("problems"),
            "error": result.error_detail,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="*", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="experiment override; the repository's live protocol "
                         "default. Recorded in every model-run record.")
    ap.add_argument("--attempts", type=int, default=3,
                    help="bounded attempts per responsibility, declared before "
                         "the run. FIRST_CONFORMING decides among them.")
    ap.add_argument("--write", action="store_true",
                    help="promote conforming responses into the corpus")
    args = ap.parse_args()

    names = env_loader.load(ENV_FILE)
    if names:
        print("loaded %s" % env_loader.describe(names))

    cases = args.cases or ["BM-001", "BM-002", "BM-003",
                           "PRB-01", "PRB-02", "PRB-03"]
    label = args.label or time.strftime("%Y%m%dT%H%M%S")
    out_dir = os.path.join(OUT_ROOT, label)
    os.makedirs(out_dir, exist_ok=True)

    ledgers: Dict[str, Dict[str, Any]] = {}
    summary = []
    for case_id in cases:
        print("\n=== %s ===" % case_id)
        result = regenerate_case(
            case_id, lambda: DeepSeekProvider(temperature=args.temperature),
            out_dir, max_attempts=args.attempts)
        if result.get("error"):
            print("  %s" % result["error"])
            continue
        root = result["corpus_root"]
        ledgers.setdefault(root, pr.read_ledger(root) or
                           {"entries": {}, "selection_rule": pr.SELECTION_RULE})
        for responsibility in WINDOW1:
            for info in result["per_responsibility"][responsibility]:
                print("  %-4s a%d %-18s raw=%-7d %s"
                      % (responsibility, info["attempt"], info["rung"],
                         info["raw_chars"],
                         ("%s" % info["problems"][:1]) if info["problems"] else ""))
        promoted = promote_case(result, ledgers[root]["entries"], args.write)
        for responsibility, entry in promoted.items():
            print("  %-4s promote=%s %s" % (responsibility, entry["promoted"],
                                            entry.get("problems") or ""))
        if args.write:
            pr.write_ledger(root, ledgers[root])
            verified = verify_current_replay(case_id, root,
                                             result["source_sha256"],
                                             result["prompts"], ledgers[root])
            for responsibility, v in verified.items():
                print("  %-4s CURRENT replay: %s %s"
                      % (responsibility, v["status"], v["integrity"]))
            result["current_replay"] = verified
        summary.append({k: v for k, v in result.items()
                        if k not in ("attempts", "prompts")})
        with open(os.path.join(out_dir, "summary.json"), "w") as fh:
            json.dump(summary, fh, indent=1, sort_keys=True, default=str)
    print("\nwrote %s" % os.path.relpath(out_dir, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
