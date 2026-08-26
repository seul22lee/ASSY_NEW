import os, sys
sys.path.insert(0,"/home/ftk3187/github/ASSY_Ver3.0"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebuild_cnd1 import build
st = build()
print("corrections:", len(build.note))
for e in sorted(st.family("MechanicalFeasibilityAssessment"), key=lambda r: r["entity_id"]):
    print("  %-14s %-10s %s" % (e["entity_id"], e.get("_validity"), e.get("status")))
bad=[e for e in st.family("FeasibilityDomainAssessment")
     if e.get("candidate")=="CND-0001" and e.get("status")!="ESTABLISHED"]
print("CND-0001 non-established domains:")
for e in bad[:8]:
    print("   %-42s %-18s %s" % (e["entity_id"], e.get("status"), (e.get("reason_codes") or [])[:3]))
