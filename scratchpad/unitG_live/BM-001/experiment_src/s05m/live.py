"""THE LIVE MATRIX. One fresh DeepSeek S05 authoring call per S04-valid
candidate, through the new boundary, then the deterministic S06 and S07.

No old response, no seeded S05 state, no synthetic successful output, no
candidate-specific retry. One call, one attempt, per candidate.
"""
import json, os, sys, time
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ver3.live_providers import env as env_loader
names = env_loader.load(os.path.join(REPO, "ver3", ".env"))
print("env variable NAMES loaded:", sorted(names), flush=True)
from ver3.live_providers.deepseek import DeepSeekProvider
import harness
from rebuild import build
from ver3.tools import bm001_replay as B

OUT = os.path.join(REPO, "scratchpad", "unitG_live", "BM-001", "s05_all_candidates")
os.makedirs(OUT, exist_ok=True)


def s04_valid(state):
    """Standing S03/S04 branch, and no AUTHORITATIVE S04 elimination."""
    eliminated = {e.get("candidate") for e in state.standing("EliminationRecord")
                  if e.get("eliminated")}
    out = []
    for cand in sorted(state.standing("Candidate"), key=lambda r: r["entity_id"]):
        cid = cand["entity_id"]
        if cid in eliminated:
            continue
        mine = lambda f: [e for e in state.standing(f) if cid in (e.get("_premises") or [])]
        if mine("Body") and mine("Joint") is not None and mine("Envelope") and mine("State"):
            out.append(cid)
    return out


probe = build()
CANDIDATES = s04_valid(probe)
print("S04-valid candidates (%d):" % len(CANDIDATES), CANDIDATES, flush=True)
print("upstream state hash:", probe.state_hash(), flush=True)
del probe

rows = []
for cid in CANDIDATES:
    print("=" * 78, flush=True)
    print("CANDIDATE", cid, flush=True)
    provider = DeepSeekProvider(temperature=1.0)
    t0 = time.time()
    row, _state = harness.run_candidate(cid, provider, OUT)
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    try:
        records = json.loads(env_loader.mask(json.dumps(provider.records, default=str), key))
    except Exception:
        records = []
    harness.dump(os.path.join(OUT, cid, "provider_run_record.json"), records)
    rows.append(row)
    s05 = row.get("s05") or {}
    print("  s05:", s05.get("status"), "| applied", s05.get("patch_applied"),
          "| structural", s05.get("structural_problems"),
          "| duties", s05.get("outstanding_duties"),
          "| ready", s05.get("settlement_readiness"), flush=True)
    print("  s06:", (row.get("s06") or {}).get("solver_status")
          or (row.get("s06") or {}).get("reason"), flush=True)
    s07 = row.get("s07") or {}
    print("  s07:", "compiled" if s07.get("compiled") else s07.get("reason"),
          "| evidence", "PASS" if s07.get("workable") else "FAIL",
          "| blocking", len(s07.get("blocking_findings") or []),
          s07.get("findings_by_owner") or "", flush=True)
    for f in (s07.get("blocking_findings") or [])[:4]:
        print("     finding:", f.get("kind"), f.get("owner"), str(f.get("detail"))[:160],
              flush=True)
    if s05.get("problems"):
        for p in s05["problems"][:4]:
            print("     refusal:", str(p)[:400], flush=True)
    print("  elapsed:", round(time.time() - t0, 1), "s", flush=True)
    harness.dump(os.path.join(OUT, "matrix.json"), rows)

harness.dump(os.path.join(OUT, "matrix.json"), rows)
print("=" * 78, flush=True)
print("MATRIX WRITTEN:", os.path.join(OUT, "matrix.json"), flush=True)
