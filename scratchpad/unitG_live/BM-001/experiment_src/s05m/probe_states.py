import os, sys
sys.path.insert(0, "/home/ftk3187/github/ASSY_Ver3.0"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebuild_cnd1 import build
st = build()
print("corrections:", build.note)
for fam in ("Joint", "State", "Transition", "SweptVolume", "MobilityExpectation"):
    rows = [r for r in st.family(fam) if "CND-0001" in (r.get("_premises") or [])]
    print("%-20s" % fam, [(r["entity_id"], r.get("_validity")) for r in rows])
