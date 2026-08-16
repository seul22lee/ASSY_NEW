"""The canonical run trace: what executed, what it was shown, what it produced.

A TOOL, not production code. It names cases, and a case identifier inside
assy_v3 is FP-02.

WHY A TRACE AND NOT A UI READING THE REPOSITORY

The human review interface must not re-derive pipeline semantics from raw files.
If it did, there would be two answers to "what did s02 see" - the pipeline's and
the viewer's - and the viewer's would be the one the reviewer believed. So the
canonical execution emits ONE machine-readable trace and the HTML is a projection
of it:

    canonical pipeline -> run trace -> HTML projection -> human review record

THE TRACE IS EVIDENCE, NOT AUTHORITY

DesignState remains the only authority on what the design IS. Everything here is
a record of an execution that already happened: the view a responsibility was
given, the prompt it was sent, what came back, what the contract said, and what
changed in state as a result. Nothing downstream may treat the trace as a place
to look up design truth.

WHAT IT REFUSES TO CLAIM

A stage whose contract ACCEPTED a patch is recorded as `contract: ACCEPTED`, and
that is a statement about schema, references and authority. It is not a statement
that the engineering is sound. `human_review` is a separate field and starts at
NOT_REVIEWED for everything, because nothing in this file is entitled to fill it
in.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.pipeline import Progression, execute_stage                # noqa: E402
from ver3.assy_v3.providers import replay_integrity as ri                   # noqa: E402
from ver3.assy_v3.providers.offline import OfflineReplayProvider            # noqa: E402
from ver3.assy_v3.state import DesignState                                  # noqa: E402
from ver3.assy_v3.view import consumer_view as cv                           # noqa: E402
from ver3.assy_v3.view.boundary import responsibility_contract              # noqa: E402

VER3 = os.path.join(REPO, "ver3")
FIXTURES = os.path.join(VER3, "assy_v3", "fixtures", "responses")
BENCHMARKS = os.path.join(VER3, "benchmarks")
CAD_VALIDATION = os.path.join(VER3, "cad_validation")

TRACE_SCHEMA_VERSION = "1.0.0"

#: The human review verdicts. Deliberately three and no more: a reviewer who has
#: not looked must be distinguishable from one who looked and had a concern.
NOT_REVIEWED = "NOT_REVIEWED"
REVIEW_VERDICTS = (NOT_REVIEWED, "PASS", "FAIL", "NEEDS_REVIEW")

#: Operational status of a node in the pipeline view. What the SYSTEM says.
LIVE_MODEL = "LIVE_DEEPSEEK"
REPLAYED = "REPLAY"
DETERMINISTIC = "DETERMINISTIC"
NOT_EXERCISED = "NOT_EXERCISED"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
BLOCKED_UPSTREAM = "BLOCKED_BY_UPSTREAM"


def repo_commit() -> str:
    try:
        return subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:                                              # noqa: BLE001
        return "unknown"


def _sha(text: Optional[str]) -> Optional[str]:
    return hashlib.sha256(text.encode()).hexdigest() if text else None


def state_summary(state) -> Dict[str, Any]:
    """Counts and ids by family. Enough to diff, small enough to embed."""
    out: Dict[str, List[str]] = {}
    for eid in state.entities:
        fam = state.entities[eid].get("_family")
        out.setdefault(fam, []).append(eid)
    return {k: sorted(v) for k, v in sorted(out.items())}


def state_diff(before: Dict[str, List[str]],
               after: Dict[str, List[str]]) -> Dict[str, Any]:
    """What this execution added, per family. Never a second state authority."""
    added = {}
    for fam, ids in after.items():
        new = sorted(set(ids) - set(before.get(fam) or []))
        if new:
            added[fam] = new
    return {"added": added,
            "added_total": sum(len(v) for v in added.values())}


class _Recording:
    """Keeps the prompt and raw text per responsibility, as the campaign tool does."""

    def __init__(self, inner):
        self.inner = inner
        self.provider_id = getattr(inner, "provider_id", "unknown")
        self.response_source = getattr(inner, "response_source", "UNDECLARED")
        self.prompts: Dict[str, str] = {}
        self.raw: Dict[str, str] = {}
        self.records = getattr(inner, "records", [])

    def capabilities(self):
        return self.inner.capabilities()

    def generate(self, request, attempt_index: int = 0):
        rid = ri.producing_identity(request)
        self.prompts[rid] = request.prompt_text
        result = self.inner.generate(request, attempt_index)
        if result.response is not None:
            self.raw[rid] = result.response.raw_text
        return result


def node(responsibility: str, title: str, kind: str, status: str,
         **extra) -> Dict[str, Any]:
    """One node of the trace. `human_review` always starts NOT_REVIEWED."""
    rec = {"responsibility_id": responsibility, "title": title, "kind": kind,
           "status": status, "human_review": NOT_REVIEWED}
    rec.update(extra)
    return rec


def run_stage(stage, provider_factory, state, progression, inputs=None,
              invocation=None) -> Dict[str, Any]:
    """Execute one responsibility through the canonical boundary and record it.

    Everything recorded is read back from the execution rather than predicted:
    the prompt from the provider that saw it, the status from the StageExecution,
    the state change by diffing before against after.
    """
    rid = stage.responsibility_id()
    before = state_summary(state)
    provider = _Recording(provider_factory())

    # The view is built by `invoke` inside `execute_stage`; building it here too
    # would be a second derivation. This one is only to record occupancy and
    # readiness BEFORE the call, which is the seam S9-E turned out to hinge on.
    view = stage.consumer_view(state, invocation)
    out, execution = execute_stage(stage, provider, state, progression,
                                   inputs=inputs or {}, invocation=invocation)
    after = state_summary(state)
    raw = provider.raw.get(rid)
    prompt = provider.prompts.get(rid)

    parsed = None
    if raw:
        try:
            parsed = {k: v for k, v in json.loads(raw).items()
                      if not k.startswith("_")}
        except Exception:                                          # noqa: BLE001
            parsed = None

    accepted = bool(execution and execution.patch_applied)
    return node(
        rid, stage.purpose or rid, "MODEL",
        LIVE_MODEL if (execution and execution.response_source == "LIVE") else REPLAYED,
        stage_owner_id=stage.stage_id,
        provider_id=provider.provider_id,
        response_source=execution.response_source if execution else None,
        execution_status=execution.execution_status if execution else None,
        contract="ACCEPTED" if accepted else "REJECTED",
        contract_problems=list(out.problems) if out else [],
        declared_incompleteness=list(out.declared_incompleteness) if out else [],
        refinement_only=bool(execution and execution.refinement_only),
        consumer_view={
            "status": view.status.value,
            "counts": view.counts(),
            "namespace_occupancy": view.occupancy,
            "families": sorted(view.payload()),
            "assessment": [{"requirement": a["requirement"],
                            "verdict": a["verdict"]} for a in view.assessment],
        },
        prompt_text=prompt,
        prompt_chars=len(prompt or ""),
        prompt_pairing=ri.prompt_hash(prompt) if prompt else None,
        raw_response=raw,
        raw_response_sha256=_sha(raw),
        parsed_collections={k: len(v) for k, v in (parsed or {}).items()
                            if isinstance(v, list)},
        parsed=parsed,
        state_before=before,
        state_after=after,
        state_diff=state_diff(before, after),
        model_run_records=list(provider.records),
    )


def build_trace(case_id: str, corpus_root: str = FIXTURES) -> Dict[str, Any]:
    """A trace of the canonical chain, as far as the repository can actually run it.

    Uses the ordinary replay provider, so this costs nothing and still exercises
    the real ConsumerView, the real prompts, the real parser and the real write
    boundary. Where no recorded response exists for a responsibility, the node is
    recorded as NOT_EXERCISED with the reason - never omitted, because a missing
    node in a review UI reads as a stage that passed.
    """
    from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture
    from ver3.assy_v3.stages.s02_obligation_and_candidates import S02ObligationAndCandidates

    request_path = os.path.join(BENCHMARKS, case_id, "source", "request.txt")
    with open(request_path, "rb") as fh:
        source_bytes = fh.read()

    state = DesignState(run_id="trace-%s" % case_id)
    progression = Progression()
    factory = lambda: OfflineReplayProvider(corpus_root, case_id)   # noqa: E731

    nodes: List[Dict[str, Any]] = []
    nodes.append(run_stage(S01RequirementCapture(), factory, state, progression,
                           inputs={"request_text": source_bytes.decode("utf-8"),
                                   "design_profile": None}))
    if nodes[-1]["contract"] == "ACCEPTED":
        nodes.append(run_stage(S02ObligationAndCandidates(), factory, state,
                               progression))
    else:
        nodes.append(node("s02", "physical obligation, demand and principle",
                          "MODEL", BLOCKED_UPSTREAM,
                          reason="s01 did not produce an accepted patch"))

    # The responsibilities that exist in production but have no recorded response
    # for this corpus. Named so the reviewer sees the shape of the whole pipeline.
    for rid, title in (("s03a", "mechanism topology"),
                       ("s03b", "interaction and constraint"),
                       ("s04a", "envelope and reach"),
                       ("s04b", "placement and motion")):
        nodes.append(node(rid, title, "MODEL", NOT_EXERCISED,
                          reason="no recorded response exists for %s at %s; this "
                                 "responsibility has never had a fixture"
                                 % (rid, case_id)))

    # SPECIFIED AND UNIMPLEMENTED, and the distinction is the point.
    #
    # These three have full contracts under ver3/contracts/stages/ - engineering
    # question, llm_role, owned decisions and numbered deterministic exit checks -
    # and their families are fully typed in DESIGN_STATE_CONTRACT. What does not
    # exist is code. Recording them as nodes rather than omitting them is what
    # stops a review screen from reading as though the pipeline ended cleanly at
    # s04b by design.
    #
    # Each contract also classifies itself OPERATIONAL and says no canonical
    # responsibility exists for it, because the frozen architecture scopes the
    # canonical set to s01-s04b plus the gate. So `NOT_IMPLEMENTED` here means
    # "specified, deliberately out of frozen scope, and unbuilt" - not
    # "undefined".
    for rid, title, llm, families in (
            ("s05", "embodiment: features, parameters, construction program",
             "HIGH for feature proposal and program shape; NONE for completeness",
             ["Constraint", "ConstructionStatement", "Feature", "Parameter",
              "Realization"]),
            ("s06", "parameter resolution (deterministic solver service)",
             "NONE", []),
            ("s07", "construction compiler and CAD build", "NONE",
             ["GeometrySignature"])):
        nodes.append(node(rid, title, "DETERMINISTIC", NOT_IMPLEMENTED,
                          reason="specified by ver3/contracts/stages/%s_CONTRACT.yaml "
                                 "with deterministic exit checks, and implemented "
                                 "by no production code" % rid.upper(),
                          declared_families=families,
                          contract_path="ver3/contracts/stages/%s_CONTRACT.yaml"
                                        % rid.upper(),
                          declared_llm_role=llm))

    return {
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "run_id": state.run_id,
        "benchmark_id": case_id,
        "source_path": os.path.relpath(request_path, REPO),
        "source_sha256": ri.canonical_source_identity(source_bytes),
        "source_text": source_bytes.decode("utf-8"),
        "repo_commit": repo_commit(),
        "corpus_root": os.path.relpath(corpus_root, REPO),
        "nodes": nodes,
        "final_state": state_summary(state),
        "final_counts": state.counts(),
        "reference_cad": reference_cad(case_id),
        "notes": {
            "replay_is_not_live": "Nodes marked REPLAY are recorded responses "
                                  "replayed through the real parser and contracts. "
                                  "That is not live-model evidence.",
            "contract_is_not_mechanical": "contract=ACCEPTED means schema, "
                                          "references and authority were "
                                          "satisfied. It says nothing about "
                                          "whether the engineering is sound.",
        },
    }


def reference_cad(case_id: str) -> Dict[str, Any]:
    """The hand-authored CAD references for this benchmark, labelled as such.

    NOT pipeline output. `cad_validation/*/executable_references/*/build.py` call
    cadquery directly, import no part of assy_v3 and read no DesignState, so no
    body or feature here resolves to a canonical design entity id. Surfaced
    because it is the only real geometry that exists, and labelled because a
    reviewer must never read it as something the pipeline produced.
    """
    root = os.path.join(CAD_VALIDATION, case_id)
    out: Dict[str, Any] = {"is_pipeline_output": False, "references": []}
    exe_root = os.path.join(root, "executable_references")
    if not os.path.isdir(exe_root):
        return out
    for ref in sorted(os.listdir(exe_root)):
        d = os.path.join(exe_root, ref)
        if not os.path.isdir(d):
            continue
        steps, shots = [], []
        for dirpath, _dn, filenames in os.walk(d):
            for fn in sorted(filenames):
                rel = os.path.relpath(os.path.join(dirpath, fn), REPO)
                if fn.endswith(".step"):
                    steps.append(rel)
                elif fn.endswith(".png"):
                    shots.append(rel)
        out["references"].append({
            "reference_id": ref,
            "step_files": sorted(steps),
            "screenshots": sorted(shots),
            "traceable_to_design_entities": False,
        })
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default="BM-001")
    ap.add_argument("--out", default=os.path.join(VER3, "out", "review"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    trace = build_trace(args.case)
    path = os.path.join(args.out, "trace-%s.json" % args.case)
    with open(path, "w") as fh:
        json.dump(trace, fh, indent=1, sort_keys=True, default=str)
    print("wrote %s" % os.path.relpath(path, REPO))
    for n in trace["nodes"]:
        print("  %-6s %-22s %s" % (n["responsibility_id"], n["status"],
                                   n.get("contract", "")))
    return 0


if __name__ == "__main__":                                       # pragma: no cover
    raise SystemExit(main())
