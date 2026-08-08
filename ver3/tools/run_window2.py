"""Run Window 2 (S03, then S04) on one case and report what happened.

A TOOL, not production code: it takes case identifiers, and a case identifier
inside assy_v3 is FP-02.

EVIDENCE DISCIPLINE
    Window 1 is frozen, so S01 and S02 are REPLAYED from their recorded
    responses. That is fixture evidence and is labelled as such. S03 and S04 are
    the stages under test and are run against the live provider. Mixing the two
    labels would let a frozen stage's quality be read as evidence about a new one.

    A candidate must be chosen before S03 can embody one, and INV-007 forbids
    choosing on quality before the s04a gate. So S03 is run ONCE PER CANDIDATE
    -- embodying is not selecting, and running every candidate is what keeps the
    design space open until the gate has evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from ver3.assy_v3.providers.offline import OfflineReplayProvider            # noqa: E402
from ver3.assy_v3.providers.status import ExecutionStatus                   # noqa: E402
from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture  # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (             # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (                 # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility, assembly_acyclic_check,
    blocking_relation_check, derive_mobility, relations_of,
    compliance_check, dof_totality_check, functional_region_check,
    interface_classification_check, irrelevance_check, load_path_check,
    no_magnitude_check, no_selection_check_s03, obligation_ownership_check,
    retention_check, simulation_completeness_check)
from ver3.assy_v3.stages.s04_envelope_and_motion import (                   # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion, assembly_path_check,
    configuration_interference_check, envelope_coverage_check, joint_geometry_check,
    load_path_reaction_check, region_occupancy_check, sampling_declaration_check,
    selection_gate_check, swept_clearance_check)
from ver3.assy_v3.state import DesignState, project_for                     # noqa: E402
from ver3.live_providers import env as env_loader                           # noqa: E402
from ver3.live_providers.deepseek import DeepSeekProvider                   # noqa: E402

FIXTURES = os.path.join(REPO, "ver3", "assy_v3", "fixtures", "responses")
PROBES = os.path.join(REPO, "ver3", "assy_v3", "probes")
BENCHMARKS = os.path.join(REPO, "ver3", "benchmarks")
ENV_FILE = os.path.join(REPO, "ver3", ".env")
OUT_ROOT = os.path.join(REPO, "ver3", "live_runs", "window2")

S03_CHECKS = (
    ("dof_totality", dof_totality_check),
    ("blocking_relation", blocking_relation_check),
    ("irrelevance", irrelevance_check),
    ("assembly_acyclic", assembly_acyclic_check),
    ("load_path", load_path_check),
    ("interface_classification", interface_classification_check),
    ("retention", retention_check),
    ("no_magnitude", no_magnitude_check),
    ("obligation_ownership", obligation_ownership_check),
    ("functional_region", functional_region_check),
    ("compliance", compliance_check),
    ("simulation_completeness", simulation_completeness_check),
    ("no_selection", no_selection_check_s03),
)


#: The ONLY families s04 may see. s04's engineering question is about the
#: mechanism, and if it cannot be answered from the mechanism then that is an
#: interface failure to record - not a licence to reach back to s01 or s02.
S03_OWNED = ("Body", "RigidGroup", "Joint", "Interface", "Configuration",
             "MobilityExpectation", "LoadPath", "AssemblyStep", "FunctionalRegion")

S04_CHECKS = (
    ("envelope_coverage", envelope_coverage_check),
    ("joint_geometry", joint_geometry_check),
    ("configuration_interference", configuration_interference_check),
    ("region_occupancy", region_occupancy_check),
    ("sampling_declaration", sampling_declaration_check),
    ("swept_clearance", swept_clearance_check),
    ("assembly_path", assembly_path_check),
    ("load_path_reaction", load_path_reaction_check),
    ("selection_gate", selection_gate_check),
)


def mechanism_projection(state) -> Dict[str, Any]:
    """Exactly what s03 produced, and nothing else.

    Built by whitelist rather than by removing s01/s02: a blacklist quietly
    admits every family added later, and this boundary is the thing under test.
    """
    return {fam: [dict(e) for e in state.family(fam)] for fam in S03_OWNED}


def interface_gaps(mech: Dict[str, Any]) -> List[str]:
    """What s04 needs and s03 did not supply. Recorded, never reconstructed."""
    gaps = []
    if not mech.get("Body"):
        gaps.append("s04a needs bodies to size; s03 produced none")
    if not mech.get("Configuration"):
        gaps.append("s04b needs configurations to place; s03 produced none")
    # s04a needs actor reach. s03 now carries it on the FunctionalRegion that
    # exists BECAUSE of the actor, so the gap is checked rather than assumed: it
    # is a gap only when no region declares an actor that needs it.
    access = [r for r in mech.get("FunctionalRegion", [])
              if r.get("role") in ("ACCESS", "APERTURE")]
    if access and not any(r.get("required_by_actors") for r in access):
        gaps.append("s04a requires actor_reach_requirements: s03 declared %d "
                    "ACCESS/APERTURE region(s) and none names the actor that "
                    "needs it, so reach cannot be evaluated from s03 output alone"
                    % len(access))
    elif not access:
        gaps.append("s04a requires actor_reach_requirements: s03 declared no "
                    "ACCESS or APERTURE region, so no reach requirement reached s04")
    return gaps


def recording_root(case_id: str) -> Optional[str]:
    for root in (FIXTURES, PROBES):
        if os.path.isfile(os.path.join(root, case_id, "s01.json")):
            return root
    return None


def request_text(case_id: str) -> Optional[str]:
    for p in (os.path.join(BENCHMARKS, case_id, "source", "request.txt"),
              os.path.join(PROBES, case_id, "request.txt")):
        if os.path.isfile(p):
            with open(p) as fh:
                return fh.read()
    return None


def discover_cases() -> List[str]:
    out = []
    for root in (FIXTURES, PROBES):
        if os.path.isdir(root):
            out += [d for d in os.listdir(root)
                    if os.path.isfile(os.path.join(root, d, "s02.json"))]
    return sorted(set(out))


def seed_window1(case_id: str):
    """Replay S01 and S02. Returns (state, problems)."""
    root = recording_root(case_id)
    text = request_text(case_id)
    if root is None or text is None:
        return None, ["no recording or request for %s" % case_id]
    provider = OfflineReplayProvider(root, case_id)
    state = DesignState(run_id="w2-%s" % case_id)
    out1 = S01RequirementCapture().run(provider, {"request_text": text}, state, state.run_id)
    if out1.patch is None:
        return None, ["s01 replay failed: %s" % out1.problems]
    state.apply(out1.patch)
    proj = project_for("s02", state)
    out2 = S02ObligationAndCandidates().run(provider, {"projection": proj}, state, state.run_id)
    if out2.patch is None:
        return None, ["s02 replay failed: %s" % out2.problems]
    state.apply(out2.patch)
    return state, []


def run_s03(case_id: str, candidate: Dict[str, Any], base_state,
            provider, trial: int) -> Dict[str, Any]:
    """Embody ONE candidate. Never raises."""
    import copy
    state = copy.deepcopy(base_state)
    rec: Dict[str, Any] = {"case": case_id, "candidate": candidate.get("entity_id"),
                           "trial": trial, "failures": [], "counts": {},
                           "s03_status": None, "s03_response": None}

    def fail(kind: str, what: str, detail: Any = None) -> None:
        rec["failures"].append({"kind": kind, "stage": "s03", "what": what, "detail": detail})

    projection = project_for("s03", state)
    started = time.time()
    try:
        out = S03TopologyAndMobility().run(
            provider, {"projection": projection, "candidate": candidate},
            state, state.run_id)
    except Exception as exc:                                        # noqa: BLE001
        fail("PARSER_DEFECT", "%s: %s" % (type(exc).__name__, exc),
             traceback.format_exc(limit=6))
        rec["s03_status"] = "RAISED"
        rec["s03_seconds"] = round(time.time() - started, 2)
        return rec
    rec["s03_seconds"] = round(time.time() - started, 2)
    rec["s03_status"] = out.execution_status.value
    rec["s03_response"] = out.raw_response
    rec["s03_declared_incomplete"] = out.declared_incompleteness

    if out.execution_status in (ExecutionStatus.PROVIDER_RATE_LIMIT,
                                ExecutionStatus.PROVIDER_QUOTA_EXHAUSTED,
                                ExecutionStatus.PROVIDER_UNAVAILABLE,
                                ExecutionStatus.PROVIDER_TIMEOUT):
        fail("PROVIDER_CONDITION", out.execution_status.value, out.problems)
        return rec
    if out.execution_status in (ExecutionStatus.RESPONSE_TRUNCATED,
                                ExecutionStatus.RESPONSE_PARSE_FAILURE):
        fail("RESPONSE_CONDITION", out.execution_status.value, out.problems)
        return rec
    if out.patch is None or out.problems:
        fail("CONTRACT_CONDITION", "contract validation", out.problems)
        return rec
    if out.declared_incompleteness:
        fail("CONTRACT_CONDITION", "declared incomplete", out.declared_incompleteness)

    state.apply(out.patch)

    # Pass B: the mobility grid, load paths and assembly order, given the
    # topology pass A just fixed. Split because one response could not carry
    # both; every field survives, only the emission is halved.
    mech = {f: [dict(e) for e in state.family(f)] for f in S03_OWNED}
    demands = {"LoadCase": [dict(e) for e in state.family("LoadCase")],
               "Obligation": [dict(e) for e in state.family("Obligation")],
               "candidate": candidate.get("entity_id")}
    try:
        outb = S03BMobilityAndAssembly().run(
            provider, {"mechanism": mech, "demands": demands}, state,
            state.run_id, attempt=2)
    except Exception as exc:                                        # noqa: BLE001
        fail("PARSER_DEFECT", "s03b: %s: %s" % (type(exc).__name__, exc))
        rec["s03_status"] = "RAISED"
        rec["_state"] = state
        return rec
    rec["s03b_status"] = outb.execution_status.value
    rec["s03b_response"] = outb.raw_response
    if outb.patch is None or outb.problems:
        fail("CONTRACT_CONDITION", "s03b contract validation", outb.problems)
    else:
        if outb.declared_incompleteness:
            fail("CONTRACT_CONDITION", "s03b declared incomplete",
                 outb.declared_incompleteness)
        state.apply(outb.patch)
        # DETERMINISTIC DERIVATION. The model authored relations; the pipeline
        # expands them into the total DOF disposition. Bookkeeping the LLM used
        # to do by hand, done here where it cannot be forgotten.
        try:
            parsed = json.loads(outb.raw_response or "{}")
        except Exception:                                           # noqa: BLE001
            parsed = {}
        relations, renames = relations_of(parsed)
        rec["blocking_relations_authored"] = len(relations)
        rec["field_renames_bound"] = len(renames)
        rec["rename_examples"] = sorted(set(renames))[:6]
        groups = [g["entity_id"] for g in state.family("RigidGroup")]
        configs = [c["entity_id"] for c in state.family("Configuration")]
        joints = [dict(j) for j in state.family("Joint")]
        entries = derive_mobility(groups, configs, joints, relations,
                                  parsed.get("irrelevance") or [])
        rec["dof_entries_derived"] = len(entries)
        by_config = {}
        for e in entries:
            by_config.setdefault(e["configuration"], []).append(e)
        from ver3.assy_v3.state.patch import Op as _Op, StagePatch as _Patch
        ops = [_Op("CREATE", "MobilityExpectation", "MEX-%04d" % (i + 1),
                   {"configuration": cfg, "dispositions": rows}, "s03:derivation")
               for i, (cfg, rows) in enumerate(sorted(by_config.items()))]
        if ops:
            dpatch = _Patch(patch_id="%s-s03-derived" % state.run_id,
                            run_id=state.run_id, stage_id="s03", stage_attempt=3,
                            parent_state_hash=state.state_hash(), operations=ops,
                            execution_status="SUCCESS",
                            provenance={"purpose": "derive the total DOF disposition",
                                        "provider": "deterministic"},
                            declared_incompleteness=[])
            dproblems = state.validate(dpatch)
            if dproblems:
                fail("CONTRACT_CONDITION", "derived mobility rejected", dproblems)
            else:
                state.apply(dpatch)

    for name, fn in S03_CHECKS:
        try:
            for p in fn(state):
                fail("CHECK_FINDING", name, p)
        except Exception as exc:                                    # noqa: BLE001
            fail("PARSER_DEFECT", "check %s raised: %s" % (name, exc))
    rec["counts"] = state.counts()
    # handed to s04 so the consumer works from the producer's actual state
    rec["_state"] = state
    return rec


def run_s04(case_id: str, state, provider, trial: int) -> Dict[str, Any]:
    """s04a then s04b, from the mechanism projection ONLY. Never raises."""
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": [],
                           "s04a_status": None, "s04b_status": None,
                           "s04a_response": None, "s04b_response": None}

    def fail(kind: str, stage: str, what: str, detail: Any = None) -> None:
        rec["failures"].append({"kind": kind, "stage": stage, "what": what,
                                "detail": detail})

    mech = mechanism_projection(state)
    rec["projection_families"] = sorted(k for k, v in mech.items() if v)
    for gap in interface_gaps(mech):
        fail("INTERFACE_GAP", "s03->s04", gap)

    for attempt, (stage, key) in enumerate(
            ((S04AEnvelopeAndReach(), "s04a"), (S04BPlacementAndMotion(), "s04b")), start=1):
        started = time.time()
        try:
            out = stage.run(provider, {"mechanism": mechanism_projection(state)},
                            state, state.run_id, attempt=attempt)
        except Exception as exc:                                    # noqa: BLE001
            fail("PARSER_DEFECT", key, "%s: %s" % (type(exc).__name__, exc),
                 traceback.format_exc(limit=5))
            rec["%s_status" % key] = "RAISED"
            return rec
        rec["%s_seconds" % key] = round(time.time() - started, 2)
        rec["%s_status" % key] = out.execution_status.value
        rec["%s_response" % key] = out.raw_response
        if out.execution_status in (ExecutionStatus.RESPONSE_TRUNCATED,
                                    ExecutionStatus.RESPONSE_PARSE_FAILURE):
            fail("RESPONSE_CONDITION", key, out.execution_status.value, out.problems)
            return rec
        if out.patch is None or out.problems:
            fail("CONTRACT_CONDITION", key, "contract validation", out.problems)
            return rec
        if out.declared_incompleteness:
            fail("CONTRACT_CONDITION", key, "declared incomplete", out.declared_incompleteness)
        state.apply(out.patch)
        # Fold the pass's non-entity results onto the entities that own them, so
        # the checks read one state rather than a response.
        _absorb(state, key, out.raw_response)

    for name, fn in S04_CHECKS:
        try:
            for p in fn(state):
                fail("CHECK_FINDING", "s04", name, p)
        except Exception as exc:                                    # noqa: BLE001
            fail("PARSER_DEFECT", "s04", "check %s raised: %s" % (name, exc))
    rec["counts"] = state.counts()
    return rec


def _absorb(state, key: str, raw: Optional[str]) -> None:
    """Attach s04 results to the entities they describe.

    region volumes, assembly directions and joint origins are properties OF
    existing entities, not new families; giving each its own family would be
    inventing representation to avoid an EXTEND.
    """
    if not raw:
        return
    try:
        parsed = json.loads(raw)
    except Exception:                                                # noqa: BLE001
        return
    if key == "s04a":
        for r in parsed.get("region_volumes", []) or []:
            e = state.entities.get(r.get("functional_region"))
            if e is not None:
                e["volume"] = {"half_extent": r.get("half_extent"), "centre": r.get("centre")}
        for a in parsed.get("assembly_directions", []) or []:
            e = state.entities.get(a.get("assembly_step"))
            if e is not None:
                e["insertion_direction"] = a.get("direction")
        state.s04a_reach = parsed.get("reach_results", [])
        state.s04a_elimination = parsed.get("elimination")
        state.s04a_scale = parsed.get("scale")
    else:
        for p in parsed.get("joint_placements", []) or []:
            e = state.entities.get(p.get("joint"))
            if e is not None:
                e["frame_origin"] = p.get("origin")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="*", default=None)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--candidates", type=int, default=1,
                    help="how many of each case's candidates to embody")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--label", default=None)
    args = ap.parse_args()

    names = env_loader.load(ENV_FILE)
    if names:
        print("loaded env: %s" % env_loader.describe(names))
    cases = args.cases or discover_cases()
    label = args.label or time.strftime("%Y%m%dT%H%M%S")
    out_dir = os.path.join(OUT_ROOT, label)
    os.makedirs(os.path.join(out_dir, "responses"), exist_ok=True)

    provider = DeepSeekProvider(temperature=args.temperature)
    print("s01+s02 REPLAYED (fixture evidence) | s03 LIVE (%s, T=%.1f)"
          % (provider.capabilities().model_id, args.temperature))

    trials: List[Dict[str, Any]] = []
    for trial in range(1, args.trials + 1):
        for case_id in cases:
            base, problems = seed_window1(case_id)
            if base is None:
                print("  %-8s SEED FAILED: %s" % (case_id, problems))
                continue
            candidates = base.family("Candidate")[:args.candidates]
            for cand in candidates:
                t0 = time.time()
                rec = run_s03(case_id, cand, base, provider, trial)
                for _k in ("s03", "s03b"):
                    _raw = rec.pop("%s_response" % _k, None)
                    if _raw:
                        _d = os.path.join(out_dir, "responses", case_id,
                                          "t%d_%s" % (trial, rec["candidate"]))
                        os.makedirs(_d, exist_ok=True)
                        with open(os.path.join(_d, "%s.json" % _k), "w") as _fh:
                            _fh.write(_raw)
                raw = None
                if raw:
                    d = os.path.join(out_dir, "responses", case_id,
                                     "t%d_%s" % (trial, rec["candidate"]))
                    os.makedirs(d, exist_ok=True)
                    with open(os.path.join(d, "s03.json"), "w") as fh:
                        fh.write(raw)
                # CONTRACT_INCOMPLETE still yields an applied patch and a real
                # mechanism; refusing to consume it would hide whether s04 can
                # work from a declared-incomplete producer, which is exactly the
                # producer-consumer question this window is asking.
                _st = rec.pop("_state", None)
                if _st is not None and rec.get("s03_status") in ("SUCCESS", "CONTRACT_INCOMPLETE"):
                    s4 = run_s04(case_id, _st, provider, trial)
                    rec["s04a_status"] = s4["s04a_status"]
                    rec["s04b_status"] = s4["s04b_status"]
                    rec["failures"] += s4["failures"]
                    rec["s04_counts"] = s4.get("counts")
                    for k in ("s04a", "s04b"):
                        raw = s4.get("%s_response" % k)
                        if raw:
                            d = os.path.join(out_dir, "responses", case_id,
                                             "t%d_%s" % (trial, rec["candidate"]))
                            os.makedirs(d, exist_ok=True)
                            with open(os.path.join(d, "%s.json" % k), "w") as fh:
                                fh.write(raw)
                trials.append(rec)
                kinds: Dict[str, int] = {}
                for f in rec["failures"]:
                    kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
                print("  t%d %-8s %-9s s03=%-14s s04a=%-10s s04b=%-10s %5.1fs %s"
                      % (trial, case_id, rec["candidate"], rec["s03_status"],
                         str(rec.get("s04a_status")), str(rec.get("s04b_status")),
                         time.time() - t0,
                         ", ".join("%s:%d" % kv for kv in sorted(kinds.items())) or "CLEAN"))
                with open(os.path.join(out_dir, "trials.json"), "w") as fh:
                    json.dump(trials, fh, indent=1, sort_keys=True)
                with open(os.path.join(out_dir, "model_run_records.json"), "w") as fh:
                    json.dump(provider.records, fh, indent=1, sort_keys=True)

    by_kind: Dict[str, int] = {}
    for t in trials:
        for f in t["failures"]:
            by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    print("\nfailures by kind: %s" % (by_kind or "none"))
    print("wrote %s" % os.path.relpath(out_dir, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
