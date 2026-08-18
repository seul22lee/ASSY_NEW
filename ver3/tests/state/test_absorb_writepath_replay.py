"""ADR-001 — exact replay of the historical uncontrolled authoritative-write path.

LEVEL 1 evidence: the historical failure path, driven with the historical payload,
must no longer produce the historical defect. LEVEL 2 (the general invariant that
no class-A fact may enter by any other path) is test_authority_model.py and
test_no_uncontrolled_authoritative_writes.py.

REPLAY TYPE: STRUCTURAL. No model call. The defect was in state mutation, so the
replay drives state mutation. Introducing model variability into a test of a
mutation path would only make the evidence weaker.

NOT AN ANSWER TEMPLATE. Nothing here asserts that a historical coordinate,
direction or verdict is correct. Every assertion is about the PATH a value takes
into authoritative state, and would hold identically for an unseen problem.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.state.authority import AuthorityViolation                  # noqa: E402
from ver3.assy_v3.state.design_state import DesignState                      # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                          # noqa: E402

ARTIFACT = os.path.join(
    REPO, "docs", "implementation", "evidence", "replays",
    "ADR-001_absorb_writepath.json")


def _substrate():
    with open(ARTIFACT) as fh:
        return json.load(fh)


def _seed(substrate):
    """The upstream entities the s04 payload refers to. s03 owns all three."""
    state = DesignState("adr-001-replay")
    # The bodies and rigid groups the seed's own references name. A typed
    # reference must denote an entity; the seed used to name three that were
    # never created, and the boundary could not see it.
    ops = [Op("CREATE", "Body", "BOD-0001",
              {"instance_identity": "b", "role": "STRUCTURE",
               "created_by_stage": "s03", "addresses_obligations": []}, "replay:s03"),
           Op("CREATE", "RigidGroup", "RGP-0001",
              {"body": "BOD-0001", "members": ["BOD-0001"], "is_default": True},
              "replay:s03"),
           Op("CREATE", "RigidGroup", "RGP-0002",
              {"body": "BOD-0001", "members": ["BOD-0001"], "is_default": False},
              "replay:s03")]
    for rid in substrate["entities_referenced"]["FunctionalRegion"]:
        ops.append(Op("CREATE", "FunctionalRegion", rid,
                      {"role": "ACCESS", "owning_bodies": ["BOD-0001"]}, "replay:s03"))
    for sid in substrate["entities_referenced"]["AssemblyStep"]:
        ops.append(Op("CREATE", "AssemblyStep", sid,
                      {"order_index": 1, "body": "BOD-0001", "access_side": "+Z",
                       "activates": [], "termination_strategy": "ROTATION",
                       "path_kind": "RIGID", "depends_on": []}, "replay:s03"))
    for jid in substrate["entities_referenced"]["Joint"]:
        ops.append(Op("CREATE", "Joint", jid,
                      {"joint_type": "REVOLUTE", "parent_group": "RGP-0001",
                       "child_group": "RGP-0002", "dof": ["RZ"],
                       "axis_direction": [0, 0, 1],
                       # NAMES the frame the axis is expressed in; [] was a
                       # unit vector in no frame, which the contract refuses.
                       "frame_ids": ["FRM-JNT-0001"]}, "replay:s03"))
    # The actor the s04a reach results name. s01 owns it, so it arrives in its
    # owner's patch - a typed reference must denote an entity, and ownership is
    # checked at the same boundary.
    state.apply(StagePatch(
        patch_id="seed-s01", run_id=state.run_id, stage_id="s01", stage_attempt=1,
        parent_state_hash=state.state_hash(),
        operations=[Op("CREATE", "Actor", "ACT-0001",
                       {"name": "operator", "must_reach": [], "role": "OPERATOR"}, "replay:s01")],
        execution_status="SUCCESS", provenance={"provider": "replay"}))
    state.apply(StagePatch(
        patch_id="seed", run_id=state.run_id, stage_id="s03", stage_attempt=1,
        parent_state_hash=state.state_hash(), operations=ops,
        execution_status="SUCCESS", provenance={"provider": "replay"}))
    return state


def _stage_ops(state, key, payload, view):
    """Every operation the CURRENT stage makes from this payload."""
    from ver3.assy_v3.stages.s04_envelope_and_motion import (
        S04AEnvelopeAndReach, S04BPlacementAndMotion)
    stage = (S04AEnvelopeAndReach if key == "s04a" else S04BPlacementAndMotion)()
    inputs = {"consumer_view": view, "candidate": None}
    ops = stage.to_operations(payload, inputs)
    ops += stage.refinement_operations(payload, inputs, state)
    ops += stage.derived_operations(payload, inputs, state)
    return stage, inputs, ops


def _view_of(state):
    """What the stages are given: every standing entity, by family.

    The replay is about the WRITE PATH, so the view is supplied directly rather
    than derived - deriving it would make this a test of Consumer Sufficiency,
    which has its own suite.
    """
    view = {}
    for eid, rec in state.entities.items():
        entry = {k: v for k, v in rec.items() if not k.startswith("_")}
        entry["entity_id"] = eid
        view.setdefault(rec["_family"], []).append(entry)
    return view


def _run_commit(state, substrate):
    """Drive the CURRENT code over the HISTORICAL payload.

    S-6 / U-7 retired `tools/run_window2._commit_s04`, which is what this replay
    used to drive: the runner read the raw s04 response and wrote the engineering
    facts the stages did not. The facts have not moved - they are authored by the
    stage that concluded them, in the stage's own patch - so the replay drives
    the stage. The ADR-001 property is unchanged and is now checked one layer
    closer to the producer.
    """
    rec = {}
    for key in ("s04a", "s04b"):
        payload = json.loads(json.dumps(substrate[key]))
        stage, inputs, ops = _stage_ops(state, key, payload, _view_of(state))
        rec["%s_uncommitted" % key] = [
            p for p in stage.completeness(payload, inputs)
            if "was not given" in p]
        if not ops:
            continue
        patch = StagePatch(
            patch_id="replay-%s" % key, run_id=state.run_id, stage_id="s04",
            stage_attempt=1, parent_state_hash=state.state_hash(),
            operations=ops, execution_status="SUCCESS",
            provenance={"provider": "replay"})
        problems = state.validate(patch)
        if problems:
            rec["%s_rejected" % key] = problems
            continue
        state.apply(patch)
    return rec


class TestAbsorbWritePathReplay(unittest.TestCase):

    def setUp(self):
        self.substrate = _substrate()

    # ------------------------------------------------------------------ BEFORE
    def test_the_historical_direct_write_cannot_reach_state(self):
        """The old path was `state.entities[id][field] = value`. Replay it verbatim.

        Two shapes, two outcomes, and both close the path: writing into the entity
        TABLE is refused outright, and writing into a record obtained from it
        touches only the copy the caller was handed."""
        state = _seed(self.substrate)
        target = self.substrate["entities_referenced"]["FunctionalRegion"][0]
        r = (self.substrate["s04a"]["region_volumes"] or [])[0]
        value = {"half_extent": r["half_extent"], "centre": r["centre"]}

        with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
            state.entities[target] = value

        before = state.state_hash()
        state.entities[target]["volume"] = value
        self.assertNotIn("volume", state.entities[target])
        self.assertEqual(before, state.state_hash())


    def test_the_historical_side_channel_is_now_structurally_impossible(self):
        """The old path also did `state.s04a_reach = parsed[...]`."""
        state = _seed(self.substrate)
        with self.assertRaisesRegex(AuthorityViolation, "SIDE_CHANNEL_WRITE"):
            state.s04a_reach = self.substrate["s04a"]["reach_results"]
        with self.assertRaisesRegex(AuthorityViolation, "SIDE_CHANNEL_WRITE"):
            state.s04a_elimination = self.substrate["s04a"]["elimination"]
        with self.assertRaisesRegex(AuthorityViolation, "SIDE_CHANNEL_WRITE"):
            state.s04a_scale = self.substrate["s04a"]["scale"]


    def test_the_old_helper_no_longer_exists(self):
        import ver3.tools.run_window2 as rw2
        assert not hasattr(rw2, "_absorb"), "the bypass must be gone, not renamed"
        # S-6 / U-7: the runner's own writer is gone too. It was a second
        # semantic authority for one stage's output, and the facts it wrote are
        # authored by the stage now - `_run_commit` above drives that path.
        assert not hasattr(rw2, "_commit_s04"), \
            "the runner writes s04 engineering meaning again"


    # ------------------------------------------------------------------- AFTER
    def test_the_same_facts_still_reach_authoritative_state(self):
        """The externally visible operation must still happen. A boundary that
        silently drops the engineering fact would be a regression, not a fix."""
        state = _seed(self.substrate)
        _run_commit(state, self.substrate)

        regions = {e["entity_id"]: e for e in state.family("FunctionalRegion")}
        for r in self.substrate["s04a"]["region_volumes"]:
            assert regions[r["functional_region"]]["volume"]["centre"] == r["centre"]

        steps = {e["entity_id"]: e for e in state.family("AssemblyStep")}
        for a in self.substrate["s04a"]["assembly_directions"]:
            assert steps[a["assembly_step"]]["insertion_direction"] == a["direction"]

        joints = {e["entity_id"]: e for e in state.family("Joint")}
        for p in self.substrate["s04b"]["joint_placements"]:
            assert joints[p["joint"]]["frame_origin"] == p["origin"]


    def test_the_facts_arrive_through_controlled_operations_with_provenance(self):
        state = _seed(self.substrate)
        _run_commit(state, self.substrate)
        for fam, fld in (("FunctionalRegion", "volume"),
                         ("AssemblyStep", "insertion_direction"),
                         ("Joint", "frame_origin")):
            for rec in state.family(fam):
                if fld not in rec:
                    continue
                ext = [e for e in rec.get("_extensions", []) if fld in e["fields"]]
                assert ext, "%s.%s arrived without a recorded EXTEND" % (fam, fld)
                assert ext[0]["stage"] == "s04"
                assert ext[0]["provenance"], "an authoritative write with no provenance"


    def test_the_side_channel_conclusions_are_now_addressable_entities(self):
        """Reach, elimination and scale had no identity, no owner and no provenance,
        and nothing could read them. They are engineering conclusions."""
        state = _seed(self.substrate)
        _run_commit(state, self.substrate)

        reach = state.family("ReachResult")
        assert len(reach) == len(self.substrate["s04a"]["reach_results"])
        for rec in reach:
            assert rec["entity_id"] and rec["_created_by"] == "s04" and rec["_provenance"]

        elim = state.family("EliminationRecord")
        assert len(elim) == 1 and elim[0]["_provenance"]

        scale = state.family("ReferenceScale")
        assert len(scale) == 1 and scale[0]["basis"] == self.substrate["s04a"]["scale"]["basis"]
        # An honest RELATIVE basis with no absolute value stays honest. FA-8: it must
        # not be defaulted into a number.
        assert scale[0]["absolute"] == self.substrate["s04a"]["scale"]["absolute"]


    def test_the_spatial_commitments_bind_to_the_scale_they_are_expressed_in(self):
        """M-5A / FA-5. A coordinate has no meaning without its basis, so withdrawing
        the basis must cost every coordinate its unqualified authority."""
        state = _seed(self.substrate)
        _run_commit(state, self.substrate)
        scale_id = state.family("ReferenceScale")[0]["entity_id"]

        placed = [e for e in state.family("Joint") if "frame_origin" in e]
        assert placed and all(e["_validity"] == "STANDING" for e in placed)

        state.apply(StagePatch(
            patch_id="withdraw", run_id=state.run_id, stage_id="s04", stage_attempt=2,
            parent_state_hash=state.state_hash(),
            operations=[Op("INVALIDATE", "ReferenceScale", scale_id, {}, "replay:test",
                           reason="the declared basis was withdrawn")],
            execution_status="SUCCESS", provenance={"provider": "replay"}))

        after = [e for e in state.family("Joint") if "frame_origin" in e]
        assert all(e["_validity"] == "STALE" for e in after)
        # FA-1: the value itself is untouched. It lost authority, not existence.
        for before, now in zip(placed, after):
            assert now["frame_origin"] == before["frame_origin"]
        assert all("frame_origin" not in e for e in state.standing("Joint"))


    def test_a_payload_referring_to_an_unknown_entity_is_recorded_not_silent(self):
        """Before S-1 an unresolvable target was skipped with `if e is not None`.
        It is still not committed -- inventing the entity would be worse -- but the
        drop is no longer invisible."""
        state = _seed(self.substrate)
        payload = json.loads(json.dumps(self.substrate["s04a"]))
        payload["region_volumes"].append(
            {"functional_region": "FRG-DOES-NOT-EXIST", "half_extent": [1, 1, 1],
             "centre": [0, 0, 0]})
        stage, inputs, _ops = _stage_ops(state, "s04a", payload, _view_of(state))
        reported = stage.completeness(payload, inputs)
        assert any("FRG-DOES-NOT-EXIST" in u for u in reported), reported
        assert "FRG-DOES-NOT-EXIST" not in state.entities


if __name__ == "__main__":
    unittest.main()
