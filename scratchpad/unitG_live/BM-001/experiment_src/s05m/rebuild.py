"""Rebuild the canonical BM-001 upstream deterministically. Zero provider calls."""
import os, shutil, sys, tempfile, json
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
from ver3.tools import bm001_replay as B, reconcile_preselection as R

PA_TRACKED = os.path.join(REPO, "scratchpad", "evidence", "BM-001_parameter_authority")


def build():
    tmp = tempfile.mkdtemp(prefix="assy-s05m-")
    PA = os.path.join(tmp, "pa"); shutil.copytree(PA_TRACKED, PA)
    state, _ = B.build(); B.with_preserved_mating(state)
    R.derive_arrival(state, B.ORDER, PA)
    prov = R._LazyProvider(None)
    for cid in B.ORDER:
        R.complete_topology(state, cid, prov, PA)
        R.complete_release(state, cid, prov, PA)
    R.qualify(state, B.ORDER, PA)
    shutil.rmtree(tmp, ignore_errors=True)
    assert prov._real is None and not prov.records, "a provider was called during replay"
    return state


if __name__ == "__main__":
    st = build()
    print("hash:", st.state_hash())
    for cid in B.ORDER:
        mine = lambda f: [e for e in st.standing(f) if cid in (e.get("_premises") or [])]
        elim = [e for e in st.standing("EliminationRecord") if cid in (e.get("_premises") or [])
                or e.get("candidate") == cid]
        mfa = [e for e in st.standing("MechanicalFeasibilityAssessment")
               if e.get("candidate") == cid or cid in (e.get("_premises") or [])]
        print("=" * 70)
        print(cid, "| bodies", len(mine("Body")), "joints", len(mine("Joint")),
              "envelopes", len(mine("Envelope")), "states", len(mine("State")),
              "interfaces", len(mine("Interface")), "relations", len(mine("ConstraintRelation")))
        for e in elim:
            print("   ELIMINATION:", json.dumps({k: v for k, v in e.items()
                                                 if not k.startswith("_")}, default=str)[:400])
        for e in mfa:
            print("   MFA:", e.get("entity_id"), e.get("status"), str(e.get("summary"))[:120])
