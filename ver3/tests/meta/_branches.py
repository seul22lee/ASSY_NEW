"""The six accepted BM-001 branches, rebuilt through the real producers.

An s03b invocation reasons against ONE candidate's topology inside a DesignState
that holds every candidate's. That is the situation this module reconstructs,
and it reconstructs it rather than describing it: the S01 and S02 patches and the
six S03a responses are the live ones, replayed through `to_operations` and the
canonical write boundary, so a fixture cannot drift into a shape the producer
would not emit.

Zero network. The responses are saved evidence from the 2026-08-18 re-run sweep,
in which all six were accepted by canonical validation.
"""
import json
import os

from . import _paths

from ver3.assy_v3.stages.base import carry_invocation_premises
from ver3.assy_v3.stages.s03_topology_and_mobility import S03TopologyAndMobility
from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op, StagePatch

FIXTURE = os.path.join(_paths.REPO_ROOT, "ver3", "tests", "fixtures",
                       "s03b_seam", "bm001_accepted_branches.json")


def fixture():
    with open(FIXTURE) as fh:
        return json.load(fh)


def _commit(state, ops, stage_id, purpose):
    patch = StagePatch(
        patch_id="%s-%d" % (stage_id, len(state.applied_patches)),
        run_id=state.run_id, stage_id=stage_id, stage_attempt=1,
        parent_state_hash=state.state_hash(), operations=list(ops),
        execution_status="SUCCESS",
        provenance={"purpose": purpose, "provider": "saved evidence"})
    problems = state.validate(patch)
    if problems:
        raise AssertionError("the fixture no longer commits: %s" % problems[:4])
    state.apply(patch)
    return patch


def six_branch_state(run_id="bm001-s03b"):
    """S01 + S02 + all six S03a branches in one DesignState."""
    data = fixture()
    state = DesignState(run_id=run_id)
    for key, stage_id, prov in (("s01_operations", "s01", "s01:extraction"),
                                ("s02_operations", "s02", "s02:derivation")):
        _commit(state, [Op("CREATE", o["family"], o["entity_id"], dict(o["fields"]),
                           prov, premise_refs=list(o["premise_refs"]))
                        for o in data[key]], stage_id, "replay of the live %s patch" % stage_id)
    stage = S03TopologyAndMobility()
    for cid, response in sorted(data["s03a_responses"].items()):
        inputs = {"candidate": candidate(state, cid)}
        _commit(state, carry_invocation_premises(stage.to_operations(response, inputs),
                                                 stage.invocation_premises(inputs)),
                "s03", "replay of the accepted s03a response for %s" % cid)
    return state


def candidate(state, cid):
    for rec in state.family("Candidate"):
        if rec["entity_id"] == cid:
            return rec
    raise AssertionError("%s is not in this state" % cid)
