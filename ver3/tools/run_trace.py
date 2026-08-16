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



#: The embodiment producer is MODEL-owned, and the trace must say so. It was
#: previously rendered with kind DETERMINISTIC beside a declared llm_role of
#: HIGH, which is a classification a reviewer would reasonably believe.
MODEL_OWNED = "MODEL"
DETERMINISTIC_SERVICE = "DETERMINISTIC"


def validity_of(state, entity_id):
    if entity_id is None or entity_id not in state.entities:
        return None
    return state.entities[entity_id].get("_validity", "STANDING")


def downstream_nodes(state, progression):
    """Real nodes for s05, s06 and s07 from what actually executed.

    A responsibility that did not run is still a node, with its reason - a stage
    missing from a review screen reads as a stage that passed.
    """
    out = []

    # ---- s05: a producing responsibility, model-owned ----------------
    produced = {fam: sorted(e["entity_id"] for e in state.family(fam))
                for fam in ("Feature", "Realization", "Parameter", "Constraint",
                            "ConstructionStatement")}
    if any(produced.values()):
        out.append(node("s05", "physical embodiment", MODEL_OWNED, REPLAYED,
                        stage_owner_id="s05",
                        declared_llm_role="HIGH for feature proposal and program "
                                          "shape; NONE for completeness",
                        produced=produced,
                        realization_graph=[
                            {"realization": r["entity_id"],
                             "addresses_obligations": r.get("addresses_obligations") or [],
                             "participating_features": r.get("participating_features") or [],
                             "verification_predicate": r.get("verification_predicate"),
                             "validity": validity_of(state, r["entity_id"])}
                            for r in sorted(state.family("Realization"),
                                            key=lambda x: x["entity_id"])],
                        feature_graph=[
                            {"feature": f["entity_id"], "body": f.get("body"),
                             "feature_kind": f.get("feature_kind"),
                             "validity": validity_of(state, f["entity_id"])}
                            for f in sorted(state.family("Feature"),
                                            key=lambda x: x["entity_id"])],
                        construction_program=[
                            {"statement": c["entity_id"], "body": c.get("body"),
                             "operation": c.get("operation"),
                             "operands": c.get("operands") or [],
                             "feature": c.get("feature"),
                             "validity": validity_of(state, c["entity_id"])}
                            for c in sorted(state.family("ConstructionStatement"),
                                            key=lambda x: x["entity_id"])]))
    else:
        out.append(node("s05", "physical embodiment", MODEL_OWNED, NOT_EXERCISED,
                        reason="no embodiment has been authored for this case"))

    # ---- s06 and s07: deterministic services -------------------------
    for rid, title in (("s06", "parameter settlement (deterministic solver)"),
                       ("s07", "construction compilation (deterministic CAD)")):
        runs = progression.deterministic_by_responsibility(rid)
        if not runs:
            out.append(node(rid, title, DETERMINISTIC_SERVICE, NOT_EXERCISED,
                            reason="no deterministic execution was recorded",
                            declared_llm_role="NONE"))
            continue
        last = runs[-1]
        record = dict(last.as_record())
        record["validity_of_evidence"] = validity_of(state, last.evidence_id)
        extra = {}
        if rid == "s06":
            extra["settled"] = {
                p["entity_id"]: {"symbol": p.get("symbol"), "unit": p.get("unit"),
                                 "value": p.get("value"),
                                 "solved_by": p.get("solved_by"),
                                 "validity": validity_of(state, p["entity_id"])}
                for p in sorted(state.family("Parameter"), key=lambda x: x["entity_id"])}
            extra["constraint_settlement"] = {
                c["entity_id"]: c.get("settlement")
                for c in sorted(state.family("Constraint"), key=lambda x: x["entity_id"])
                if c.get("settlement")}
        else:
            signatures = sorted(state.family("GeometrySignature"),
                                key=lambda x: x["entity_id"])
            extra["signatures"] = [
                {"entity_id": g["entity_id"],
                 "signature_sha256": g.get("signature_sha256"),
                 "per_body": g.get("per_body"),
                 "feature_map": g.get("feature_map"),
                 "compiled_bodies": g.get("compiled_bodies"),
                 "validity": validity_of(state, g["entity_id"])}
                for g in signatures]
        out.append(node(rid, title, DETERMINISTIC_SERVICE,
                        "EXECUTED" if last.patch_applied else "EXECUTED_NO_WRITE",
                        stage_owner_id=rid, declared_llm_role="NONE",
                        deterministic_runs=[r.as_record() for r in runs],
                        execution=record, **extra))
    return out


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
    # s05, s06 and s07 now EXIST, so the trace projects their real executions
    # rather than a placeholder. `deterministic_nodes` builds the last two from
    # DeterministicExecution records, which is why they carry no response source
    # and no provider: they contacted none.
    nodes.extend(downstream_nodes(state, progression))

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



# ==========================================================================
# The integrated canonical development chain
#
# A DEVELOPMENT / CONTRACT FIXTURE. Not live, not a benchmark result, and not an
# S9-E promotion. It exists because the benchmark corpus cannot currently feed
# s05 without paid regeneration, and a downstream that only ever runs from
# hand-built solver input is a downstream nobody has seen work.
#
# It enters through the SAME public interfaces production uses: canonical
# DesignState, the s05 stage's own `to_operations`, and the deterministic
# execution path. Nothing here calls a solver or a compiler core directly.
# ==========================================================================

DEVELOPMENT_FIXTURE = "DEVELOPMENT/CONTRACT FIXTURE - not live, not a benchmark result"


def _mm(v):
    return {"const": v, "unit": "mm"}


def _ref(i):
    return {"ref": i}


def development_embodiment():
    """One body, one bore, one obligation discharged. Canonical shapes only.

    Deliberately small and deliberately generic: no benchmark dimension, no
    reference geometry, nothing that names a case. What it exercises is the
    SEAM - obligation to realization to feature to statement to solid.
    """
    return {
        "features": [{"id": "FEA-0001", "body": "BOD-0001",
                      "feature_kind": "BORE", "geometry": "axial bore"}],
        "realizations": [{"id": "RLZ-0001",
                          "addresses_obligations": ["OBL-0001"],
                          "participating_features": ["FEA-0001"],
                          "verification_predicate":
                              "the bore admits the retained member"}],
        "parameters": [{"id": "PRM-0001", "symbol": "pin_r", "unit": "mm"},
                       {"id": "PRM-0002", "symbol": "wall", "unit": "mm"},
                       {"id": "PRM-0003", "symbol": "boss_r", "unit": "mm"}],
        "constraints": [
            {"id": "CON-0001", "kind": "DIMENSIONAL", "parameters": ["PRM-0001"],
             "expression": {"relation": "==", "lhs": _ref("PRM-0001"), "rhs": _mm(4)}},
            {"id": "CON-0002", "kind": "DIMENSIONAL", "parameters": ["PRM-0002"],
             "expression": {"relation": "==", "lhs": _ref("PRM-0002"), "rhs": _mm(2)}},
            # The envelope rule from S05_CONTRACT, as a coupled relation: a pin
            # of radius r needing a wall w gives a boss radius r + w.
            {"id": "CON-0003", "kind": "ENVELOPE",
             "parameters": ["PRM-0001", "PRM-0002", "PRM-0003"],
             "expression": {"relation": "==", "lhs": _ref("PRM-0003"),
                            "rhs": {"op": "+", "args": [_ref("PRM-0001"),
                                                        _ref("PRM-0002")]}}}],
        "construction_statements": [
            {"id": "CST-0001", "body": "BOD-0001", "operation": "BOX", "operands": [],
             "parameters": {"dx": _mm(40), "dy": _mm(30), "dz": _mm(20)}},
            {"id": "CST-0002", "body": "BOD-0001", "operation": "CYLINDER",
             "operands": [], "feature": "FEA-0001",
             "parameters": {"radius": _ref("PRM-0003"), "height": _mm(30)}},
            {"id": "CST-0003", "body": "BOD-0001", "operation": "TRANSLATE",
             "operands": ["CST-0002"],
             "parameters": {"dx": _mm(20), "dy": _mm(15), "dz": _mm(-5)}},
            {"id": "CST-0004", "body": "BOD-0001", "operation": "CUT",
             "operands": ["CST-0001", "CST-0003"], "parameters": {}}],
    }


def build_development_trace(out_dir):
    """Run the canonical chain end to end and return its trace."""
    from ver3.assy_v3.downstream import execution as dex
    from ver3.assy_v3.stages.s05_embodiment import S05Embodiment
    from ver3.assy_v3.state.patch import Op, StagePatch

    state = DesignState(run_id="dev-integrated")
    progression = Progression()

    def commit(stage, ops):
        patch = StagePatch(
            patch_id="%s-%d" % (stage, len(state.applied_patches)),
            run_id=state.run_id, stage_id=stage, stage_attempt=1,
            parent_state_hash=state.state_hash(), operations=list(ops),
            execution_status="SUCCESS",
            provenance={"purpose": "development fixture", "provider": None})
        problems = state.validate(patch)
        if problems:
            raise AssertionError("development fixture rejected: %s" % problems)
        state.apply(patch)

    commit("s03", [Op("CREATE", "Body", "BOD-0001",
                      {"instance_identity": "enclosure", "role": "shell",
                       "created_by_stage": "s03"}, "s03:topology")])
    commit("s02", [Op("CREATE", "Obligation", "OBL-0001",
                      {"statement": "the retained member is located",
                       "derived_from_requirements": [], "mandatory": True,
                       "scope": "UNIVERSAL", "satisfiable_at": "s05",
                       "evidence_route": "MOBILITY_ANALYSIS",
                       "route_available": True}, "s02:derivation")])

    embodiment = development_embodiment()
    stage = S05Embodiment()
    before = state_summary(state)
    commit("s05", stage.to_operations(embodiment))
    after = state_summary(state)

    dex.execute_settlement(state, progression)
    result, compile_execution = dex.execute_compilation(
        state, progression, out_dir=out_dir)

    # `downstream_nodes` builds all three from committed state; the s05 node is
    # then enriched with what only this caller knows - the response it authored
    # and the state either side of it - rather than being added a second time.
    nodes = downstream_nodes(state, progression)
    for n in nodes:
        if n["responsibility_id"] == "s05":
            n.update({"contract": "ACCEPTED", "state_before": before,
                      "state_after": after,
                      "state_diff": state_diff(before, after),
                      "parsed": embodiment,
                      "provenance": DEVELOPMENT_FIXTURE})
    return {
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "run_id": state.run_id,
        "benchmark_id": "DEV-INTEGRATED",
        "provenance": DEVELOPMENT_FIXTURE,
        "is_live": False,
        "is_benchmark_result": False,
        "repo_commit": repo_commit(),
        "source_text": "A development fixture exercising the canonical downstream "
                       "seam. It is not a design request and answers no benchmark.",
        "nodes": nodes,
        "final_state": state_summary(state),
        "final_counts": state.counts(),
        "compile_ok": result.ok,
        "exports": result.exports,
        "roundtrip": result.roundtrip,
        "progression": progression.as_record(),
        "reference_cad": {"is_pipeline_output": False, "references": []},
        "notes": {
            "replay_is_not_live": "This fixture is not a live run and claims no "
                                  "model provenance.",
            "contract_is_not_mechanical": "Compilation success is a geometric "
                                          "fact, not a mechanical judgement.",
        },
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default="BM-001")
    ap.add_argument("--out", default=os.path.join(VER3, "out", "review"))
    ap.add_argument("--development", action="store_true",
                    help="run the integrated canonical development chain")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.development:
        cad = os.path.join(VER3, "out", "cad", "DEV-INTEGRATED")
        trace = build_development_trace(cad)
        args.case = "DEV-INTEGRATED"
    else:
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
