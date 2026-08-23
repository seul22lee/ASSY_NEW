"""THE CANONICAL BM-001 STATE, rebuilt deterministically from tracked evidence.

Every step is a replay of a recorded patch or a recorded response through the
CURRENT producer, at the current write boundary. ZERO provider calls. This is
the state every pre-selection qualification of the benchmark is asked of, and
it is rebuilt rather than stored because a stored state cannot say whether the
boundary would still accept what it holds.

PARTIAL, AND SAYS SO. s01 is 28 of its 33 records: the five SourceClause
records survive nowhere with their fields (only ids, and prose in a review
page), nothing downstream references them, and no record here is
hand-authored - each is the entity as the pipeline itself projected it into a
committed consumer view, provenance included. The hash of this state therefore
equals no earlier canonical hash, and no claim of byte-exact historical replay
is made.

Lived in session scratch through three units; persisted here so the
reconciliation tool and anyone after it rebuild the same state from the same
evidence.
"""
import copy
import glob
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)
from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.stages.s03_topology_and_mobility import joint_free_dof
from ver3.assy_v3.stages.s04_envelope_and_motion import S04BPlacementAndMotion
from ver3.assy_v3.providers.interfaces import (GenerationResponse, GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.stages.base import ExecutionStatus
from ver3.assy_v3.view import InvocationContext
import time

E = os.path.join("scratchpad", "evidence")
#: The retained candidates of BM-001, in id order. Evidence for diagnosis and
#: for the replay's iteration; nothing in production reads this.
ORDER = ["CND-%04d" % n for n in range(1, 7)]


class Canned:
    def __init__(self, raw): self.raw, self.records = raw, []
    def capabilities(self):
        return ProviderCapabilities(provider_id="replay", model_id="none",
                                    context_window_tokens=None, max_output_tokens=None,
                                    supports_structured_output=True, supports_seed=True,
                                    requests_per_minute=None, tokens_per_minute=None,
                                    daily_quota_requests=None, notes="recorded response")
    def generate(self, request, attempt_index=0):
        return GenerationResult(execution_status=ExecutionStatus.SUCCESS,
                                response=GenerationResponse(raw_text=self.raw, finish_reason="stop",
                                                            truncated=False, input_tokens=None,
                                                            output_tokens=None, served_model_id="none"),
                                attempt_index=attempt_index, started_at=time.time(),
                                ended_at=time.time(), from_cache=True)


def commit(state, ops, stage_id, purpose, log):
    p = StagePatch(patch_id="%s-%d" % (stage_id, len(state.applied_patches)), run_id=state.run_id,
                   stage_id=stage_id, stage_attempt=1, parent_state_hash=state.state_hash(),
                   operations=ops, execution_status="SUCCESS",
                   provenance={"purpose": purpose, "provider": "saved evidence"})
    problems = state.validate(p)
    log.append({"purpose": purpose, "operations": len(ops), "accepted": not problems, "problems": problems[:6]})
    if problems:
        raise SystemExit("%s REJECTED: %s" % (purpose, problems[:4]))
    state.apply(p)


def ops_from(path, prov, key="authored_operations"):
    d = json.load(open(path)); rows = d.get(key) if isinstance(d, dict) and key in d else d
    if isinstance(d, dict) and "operations" in d and key not in d: rows = d["operations"]
    return [Op(o.get("kind", "CREATE"), o["family"], o["entity_id"], dict(o["fields"]), prov,
               premise_refs=list(o.get("premise_refs") or [])) for o in rows]


def replay_dir(state, d, stage_id, aprov, dprov, purpose, log):
    val = os.path.join(d, "08_canonical_validation.json")
    if not os.path.exists(val) or not json.load(open(val))["accepted"]:
        return False
    ops = ops_from(os.path.join(d, "07_authored_patch.json"), aprov)
    ops += ops_from(os.path.join(d, "09_derived_operations.json"), dprov, key="operations")
    commit(state, ops, stage_id, purpose, log)
    return True


def s03a_saved(cid):
    cap = json.load(open(os.path.join(E, "BM-001_S03a_rerun", cid, "03_parse_patch_validation.json")))
    return cap["patch"]["operations"]


def migrated_basis(cid):
    """The canonical {joint,dof,differs_from} basis: forced where unique, else the
    targeted authoring the basis unit recorded."""
    authored = os.path.join(E, "BM-001_basis_targeted", cid, "basis", "07_authored_basis.json")
    if os.path.exists(authored):
        return json.load(open(authored))["after"]
    ops = s03a_saved(cid)
    joints = [dict(o["fields"], entity_id=o["entity_id"]) for o in ops if o["family"] == "Joint"]
    out = {}
    for o in ops:
        if o["family"] != "Configuration": continue
        rows = []
        for r in (o["fields"].get("distinguishing_basis") or []):
            g, dof = r.get("rigid_group"), r.get("dof")
            compat = [j["entity_id"] for j in joints if g in (j.get("parent_group"), j.get("child_group")) and dof in joint_free_dof(j)]
            assert len(compat) == 1, (cid, o["entity_id"], compat)
            rows.append({"joint": compat[0], "dof": dof, "differs_from": list(r.get("differs_from") or [])})
        out[o["entity_id"]] = rows
    return out


S01_RECOVERABLE = {"Actor": 1, "Ambiguity": 7, "Freedom": 7, "Requirement": 10, "Scenario": 3}
S01_UNRECOVERABLE = {"SourceClause": 5}


def s01_from_views():
    """THE 28 S01 RECORDS THAT SURVIVE WHOLE, assembled from committed consumer
    views. The captured S01 patch lived in session scratch that is gone; the
    five SourceClause records survive nowhere with their fields (only ids, and
    prose in a review page), and nothing downstream references them. This is
    a PARTIAL replay and says so: its hash cannot equal any prior canonical
    state's, and no record here is hand-authored - each is the entity as the
    pipeline itself projected it, provenance included."""
    found = {}
    for p in sorted(glob.glob(os.path.join(E, "**", "02_consumer_view.json"), recursive=True)):
        for fam in S01_RECOVERABLE:
            for r in (json.load(open(p)).get("payload") or {}).get(fam) or []:
                found.setdefault(fam, {}).setdefault(r["entity_id"], r)
    assert {f: len(found[f]) for f in S01_RECOVERABLE} == S01_RECOVERABLE
    ops = []
    for fam in sorted(found):
        for eid, r in sorted(found[fam].items()):
            fields = {k: v for k, v in r.items() if not k.startswith("_") and k != "entity_id"}
            ops.append(Op("CREATE", fam, eid, fields, r.get("_provenance") or "s01:extraction"))
    return ops


def build():
    state = DesignState(run_id="bm001-closure-partial"); log = []
    commit(state, s01_from_views(), "s01", "replay s01 (28 of 33 records; SourceClause unrecoverable)", log)
    path = os.path.join(E, "BM-001_S02", "03_parse_patch_validation.json")
    ops = [Op("CREATE", o["family"], o["entity_id"], dict(o["fields"]), "s02:derivation", premise_refs=list(o.get("premise_refs") or []))
           for o in json.load(open(path))["patch"]["operations"]]
    commit(state, ops, "s02", "replay s02", log)
    for cid in ORDER:
        basis = migrated_basis(cid)
        ops = []
        for o in s03a_saved(cid):
            f = dict(o["fields"])
            if o["family"] == "Configuration" and "distinguishing_basis" in f:
                f["distinguishing_basis"] = copy.deepcopy(basis.get(o["entity_id"]) or [])
            ops.append(Op(o["kind"], o["family"], o["entity_id"], f, "s03:topology", premise_refs=list(o.get("premise_refs") or [])))
        commit(state, ops, "s03", "replay s03a %s" % cid, log)
    # s03b: Unit-2 for five, the Unit345 fresh one for CND-0006
    for cid in ORDER:
        d = os.path.join(E, "BM-001_Unit345", cid, "s03b") if cid == "CND-0006" else os.path.join(E, "BM-001_S03b_unit2", cid)
        assert replay_dir(state, d, "s03", "s03b:relations", "s03:derivation", "replay s03b %s" % cid, log), cid
    # release completions from the convergence unit
    for cid in ("CND-0001", "CND-0003", "CND-0004"):
        done = json.load(open(os.path.join(E, "BM-001_converge", cid, "release", "07_completion.json")))
        ops = []
        for row in done["parsed"]["completions"]:
            cur = state.entities[row["relation"]]; fields = {}
            m = row.get("blocked_relative_motions") or []
            if m and m != (cur.get("blocked_relative_motions") or []): fields["blocked_relative_motions"] = m
            if row["defeat_specification"] != cur.get("defeat_specification"): fields["defeat_specification"] = row["defeat_specification"]
            if fields:
                ops.append(Op("SUPERSEDE", "ConstraintRelation", row["relation"], fields, "s03b:relations", reason="release principle completed"))
        commit(state, ops, "s03", "release completion %s" % cid, log)
    # s04a: Unit345 rerun where present, else the original
    for cid in ORDER:
        for d in (os.path.join(E, "BM-001_Unit345", cid, "s04a"), os.path.join(E, "BM-001_S04a", cid)):
            if replay_dir(state, d, "s04", "s04a:arrangement", "s04a:derivation", "replay s04a %s" % cid, log):
                break
        else:
            raise SystemExit("no s04a for %s" % cid)
    # s04b: every candidate's recorded response through the CURRENT producer
    for cid in ORDER:
        src = os.path.join(E, "BM-001_converge", "CND-0005", "s04b") if cid == "CND-0005" else os.path.join(E, "BM-001_Unit345", cid, "s04b")
        raw = open(os.path.join(src, "05_raw_response.txt")).read()
        cand = next(c for c in state.family("Candidate") if c["entity_id"] == cid)
        out = S04BPlacementAndMotion().invoke(Canned(raw), state, state.run_id, {"candidate": cand}, attempt=3, invocation=InvocationContext(branch=cid))
        assert not state.validate(out.patch), (cid, out.problems)
        state.apply(out.patch)
        log.append({"purpose": "s04b %s re-judged" % cid, "status": out.execution_status.value})
    return state, log


def mine(state, cid, fam):
    """The records of `fam` that embody candidate `cid` (by premise)."""
    return [e for e in state.family(fam) if cid in (e.get("_premises") or [])]


def with_preserved_mating(state):
    """The one s04a mating EXTEND recorded by the analytical-mating unit
    (CND-0001 IFC-0002, PIN 4.0 in BORE 4.0 over 60), replayed as it was
    committed. Preserved evidence: never re-authored and never rewritten."""
    from ver3.assy_v3.stages.base import carry_invocation_premises
    from ver3.assy_v3.stages.s04_envelope_and_motion import S04AEnvelopeAndReach
    from ver3.assy_v3.state.patch import StagePatch
    path = os.path.join(E, "BM-001_mating", "CND-0001", "mating", "07_authored.json")
    parsed = json.load(open(path))["parsed"]
    # THROUGH THE PRODUCER. The stage's own builder makes the record - fields,
    # maturity and lineage - from the recorded response and the branch's view,
    # exactly as the live pass would; nothing here decides what it carries.
    stage = S04AEnvelopeAndReach()
    view = stage.consumer_view(state, InvocationContext(branch="CND-0001")).payload()
    scale = [e["entity_id"] for e in mine(state, "CND-0001", "ReferenceScale")]
    ops = carry_invocation_premises(
        stage.mating_operations(parsed["mating_geometry"], view, scale), ["CND-0001"])
    p = StagePatch(patch_id="mating-replay", run_id=state.run_id, stage_id="s04",
                   stage_attempt=1, parent_state_hash=state.state_hash(),
                   operations=ops, execution_status="SUCCESS",
                   provenance={"provider": "saved evidence"})
    problems = state.validate(p)
    assert not problems, problems
    state.apply(p)
    return state


if __name__ == "__main__":
    st, log = build()
    print("hash:", st.state_hash())
    print("counts:", st.counts())
