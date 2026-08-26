"""The real standing S04/S03 design for the pilot candidate, as a designer's brief.

Nothing is invented and nothing is filtered for convenience: these are the rows
the branch actually stands on, projected into the shape a CAD designer needs.
"""
import json, os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, "/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad/s05m")
from rebuild_cnd1 import build

CID = os.environ.get("PILOT_CID", sys.argv[1] if len(sys.argv) > 1 else "CND-0004")
OUT = os.environ.get("PILOT_OUT", os.path.join(
    REPO, "scratchpad", "unitG_live", "BM-001", "s05_fresh_authoring_pilot"))
os.makedirs(OUT, exist_ok=True)

state = build()
def mine(fam):
    return [r for r in sorted(state.standing(fam), key=lambda x: x["entity_id"])
            if CID in (r.get("_premises") or [])]
def clean(r, drop=()):
    return {k: v for k, v in sorted(r.items())
            if not k.startswith("_") and k not in drop and v not in (None, [], {})}

groups = {g["entity_id"]: g.get("body") for g in mine("RigidGroup")}
scale = (mine("ReferenceScale") or [{}])[0]
brief = {
    "candidate": CID,
    "state_hash": state.state_hash(),
    "reference_scale": clean(scale),
    "bodies": [clean(b) for b in mine("Body")],
    "rigid_groups": [clean(g) for g in mine("RigidGroup")],
    "envelopes": [dict(clean(e), NOTE="BOUNDING EXTENT ONLY - this is not material")
                  for e in mine("Envelope")],
    "joints": [dict(clean(j), parent_body=groups.get(j.get("parent_group")),
                    child_body=groups.get(j.get("child_group"))) for j in mine("Joint")],
    "interfaces": [clean(i) for i in mine("Interface")],
    "physical_interactions": [clean(p) for p in mine("PhysicalInteraction")],
    "constraint_relations": [dict(clean(c), retained_body=groups.get(c.get("retained_group")))
                             for c in mine("ConstraintRelation")],
    "configurations": [clean(c) for c in mine("Configuration")],
    "states": [clean(s) for s in mine("State")],
    "transitions": [clean(t) for t in mine("Transition")],
    "transition_requirements": [clean(t) for t in mine("TransitionRequirement")],
    "swept_volumes": [clean(s) for s in mine("SweptVolume")],
    "functional_regions": [clean(r) for r in mine("FunctionalRegion")],
    "assembly_steps": [clean(a) for a in mine("AssemblyStep")],
    "candidate_record": [clean(c) for c in state.standing("Candidate")
                         if c["entity_id"] == CID],
}
with open(os.path.join(OUT, "s04_input.json"), "w") as fh:
    json.dump(brief, fh, indent=1, sort_keys=True, default=str)
print("wrote", os.path.join(OUT, "s04_input.json"))
for k, v in brief.items():
    if isinstance(v, list):
        print("  %-26s %d" % (k, len(v)))
print("scale:", brief["reference_scale"])
