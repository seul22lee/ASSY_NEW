"""The CND-0001 branch with ONE confirmed S04 defect corrected.

THE DEFECT. s03 recorded the hinge chain pointing lid -> pin -> base, so
`base_body()` takes the LID as the pose-tree root and the OPEN state swings the
BASE about the hinge instead of the lid. s04's own Transition record disagrees
with it: `moving_groups` lists the pin and lid groups, not the base.

THE CORRECTION, AND WHERE IT IS APPLIED. The two joint records are re-oriented
so pose propagation runs base -> pin -> lid. This is done AT CONSTRUCTION, on
the replayed s03 operations, before anything downstream exists - because
revising a joint after the fact correctly stales every state, transition and
swept volume resting on it, and only a re-derivation by the owning stage can
lift that. Correcting the input avoids inventing a re-derivation.

Joint identities, types, the hinge axis, the located frame origin, the joint
coordinates and the mechanism principle are all preserved. Nothing is moved and
no geometry is touched. The tracked evidence file is not modified: the swap is
made on the operations in memory during this scratch rebuild.
"""
import os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ver3.tools import bm001_replay as B
from ver3.assy_v3.state.patch import Op, StagePatch

CID = "CND-0001"
#: joint -> (parent_group, child_group) the physical hinge tree requires.
HINGE_TREE = {"JNT-0001": ("RGP-0001", "RGP-0002"),    # base -> pin  (FIXED)
              "JNT-0002": ("RGP-0002", "RGP-0003")}    # pin  -> lid  (REVOLUTE)
#: the groups that actually travel: the lid's own, not the base or its pin.
MOVING_GROUPS = ["RGP-0003", "RGP-0004"]
NOTE = []

_original_s03a = B.s03a_saved


def _corrected_s03a(cid):
    ops = _original_s03a(cid)
    if cid != CID:
        return ops
    out = []
    for op in ops:
        if op.get("family") == "Joint" and op.get("entity_id") in HINGE_TREE:
            parent, child = HINGE_TREE[op["entity_id"]]
            fields = dict(op["fields"])
            if (fields.get("parent_group"), fields.get("child_group")) != (parent, child):
                NOTE.append("%s: %s->%s becomes %s->%s (identity, type, axis %s and located "
                            "origin %s unchanged)"
                            % (op["entity_id"], fields.get("parent_group"),
                               fields.get("child_group"), parent, child,
                               fields.get("axis_direction"), fields.get("frame_origin")))
                fields["parent_group"], fields["child_group"] = parent, child
            op = dict(op, fields=fields)
        out.append(op)
    return out


def _corrected_s04b(cls):
    """The transitions say what the corrected tree means: the base and its fixed
    pin stand, the lid and its compliant subgroup travel.

    Corrected on the producer's OWN operations, in memory, before they are
    committed - for the same reason the joints are: revising a transition
    afterwards stales the feasibility assessment that rests on it, and a stale
    assessment makes the candidate ineligible for selection. The recorded s04b
    response is not touched.
    """
    original = cls.invoke

    def invoke(self, provider, state, run_id, inputs=None, **kw):
        out = original(self, provider, state, run_id, inputs, **kw)
        branch = (inputs or {}).get("candidate")
        branch = branch.get("entity_id") if isinstance(branch, dict) else branch
        if branch != CID or out.patch is None:
            return out
        for op in out.patch.operations:
            if op.entity_type != "Transition":
                continue
            path = op.fields.get("path")
            if not isinstance(path, dict) or path.get("moving_groups") == MOVING_GROUPS:
                continue
            NOTE.append("%s: moving_groups %s becomes %s"
                        % (op.entity_id, path.get("moving_groups"), MOVING_GROUPS))
            path["moving_groups"] = list(MOVING_GROUPS)
        return out

    cls.invoke = invoke
    return original


def build():
    del NOTE[:]
    from ver3.assy_v3.stages.s04_envelope_and_motion import S04BPlacementAndMotion
    B.s03a_saved = _corrected_s03a
    restore = _corrected_s04b(S04BPlacementAndMotion)
    try:
        state, _log = B.build()
        B.with_preserved_mating(state)
        _finish(state)
    finally:
        S04BPlacementAndMotion.invoke = restore
    build.note = list(NOTE)
    return state


def _finish(state):
    """The rest of the canonical rebuild, exactly as the pilot has always done."""
    import shutil, tempfile
    from ver3.tools import reconcile_preselection as R
    tmp = tempfile.mkdtemp(prefix="assy-cnd1-")
    PA = os.path.join(tmp, "pa")
    shutil.copytree(os.path.join(REPO, "scratchpad", "evidence",
                                 "BM-001_parameter_authority"), PA)
    R.derive_arrival(state, B.ORDER, PA)
    prov = R._LazyProvider(None)
    for cid in B.ORDER:
        R.complete_topology(state, cid, prov, PA)
        R.complete_release(state, cid, prov, PA)
    R.qualify(state, B.ORDER, PA)
    shutil.rmtree(tmp, ignore_errors=True)
    assert prov._real is None and not prov.records, "a provider was called during replay"


def _moving_groups(state):
    """Say what the corrected tree means physically: the base and its fixed pin
    stand; the lid and its compliant subgroup travel."""
    ops = []
    for t in sorted(state.standing("Transition"), key=lambda r: r["entity_id"]):
        if CID not in (t.get("_premises") or []):
            continue
        path = dict(t.get("path") or {})
        if path.get("moving_groups") == MOVING_GROUPS:
            continue
        NOTE.append("%s: moving_groups %s becomes %s"
                    % (t["entity_id"], path.get("moving_groups"), MOVING_GROUPS))
        path["moving_groups"] = list(MOVING_GROUPS)
        ops.append(Op("SUPERSEDE", "Transition", t["entity_id"], {"path": path},
                      "s04b:placement",
                      reason="the base and its fixed pin stand; the lid travels"))
    if not ops:
        return
    patch = StagePatch(patch_id="cnd1-moving-groups", run_id=state.run_id, stage_id="s04",
                       stage_attempt=1, parent_state_hash=state.state_hash(),
                       operations=ops, execution_status="SUCCESS",
                       provenance={"purpose": "moving groups follow the hinge tree",
                                   "provider": None})
    problems = state.validate(patch)
    assert not problems, problems
    state.apply(patch)


if __name__ == "__main__":
    st = build()
    for n in build.note:
        print("  corrected:", n)
    for fam in ("Joint", "State", "Transition", "SweptVolume"):
        rows = [r for r in st.family(fam) if CID in (r.get("_premises") or [])]
        print("%-14s" % fam, [(r["entity_id"], r.get("_validity")) for r in rows])
    print("state hash:", st.state_hash())
