"""Render the candidate-matrix review from the recorded run."""
import json, os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
from ver3.tools.review import matrix

ROOT = os.path.join(REPO, "scratchpad", "unitG_live", "BM-001", "s05_all_candidates")
rows = json.load(open(os.path.join(ROOT, "matrix.json")))
for row in rows:
    for path in matrix.render_candidate(ROOT, row):
        print("figure:", os.path.relpath(path, ROOT))
md, page = matrix.write(
    ROOT, rows,
    "ASSY Ver3.0 - S05 authoring boundary: every S04-valid candidate",
    "BM-001 upstream rebuilt deterministically (zero provider calls) | one fresh DeepSeek "
    "S05 call per candidate through the new semantic boundary | S06 and S07 are "
    "deterministic and consume the accepted S05 result")
print("REPORT.md:", md)
print("index.html:", page)
for row in rows:
    v = matrix.verdict(row)
    print(row["candidate"], "->", "CLOSED" if v["all"] else "NOT CLOSED",
          {k: v[k] for k, _l in matrix.CRITERIA})
