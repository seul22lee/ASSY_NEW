"""The ONE boundary this correction is judged on.

CLOSED: base, pin and lid all identity.
OPEN:   base and pin identity; the lid rotates about the existing hinge frame.

Nothing else about s04 is asserted here.
"""
import os, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebuild_cnd1 import build
from ver3.assy_v3.downstream import kinematics

CID, PER_UNIT = "CND-0001", 5.0
BASE, PIN, LID = "BOD-0001", "BOD-0003", "BOD-0002"
IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
failures = []


def close(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def identity(frame):
    return close(frame.t, (0, 0, 0)) and \
        all(close(r, i) for r, i in zip(frame.r, IDENTITY))


state = build()
mine = lambda f: [r for r in state.standing(f) if CID in (r.get("_premises") or [])]
joints, groups = mine("Joint"), mine("RigidGroup")
bodies = [b["entity_id"] for b in mine("Body")]
states = {s["entity_id"]: s for s in mine("State")}

edges = kinematics.joint_edges(joints, groups)
root = kinematics.base_body(edges)
print("pose-tree root:", root)
if root != BASE:
    failures.append("root is %s, expected the stationary base %s" % (root, BASE))

for sid, expect_lid_moves in (("STA-CFG-0001", False), ("STA-CFG-0002", True)):
    st = states[sid]
    coords, _n = kinematics.coordinates_in_kernel_units(
        joints, st.get("joint_coordinates") or {}, PER_UNIT)
    law = kinematics.derive_poses(joints, groups, coords, PER_UNIT, bodies)
    print("\n%s coords=%s" % (sid, st.get("joint_coordinates")))
    for b in (BASE, PIN, LID):
        f = law.poses.get(b)
        print("   %-10s t=%-26s R=%s" % (b, [round(v, 3) for v in f.t],
                                         [[round(v, 3) for v in r] for r in f.r]))
    for b in (BASE, PIN):
        if not identity(law.poses[b]):
            failures.append("%s: %s is not identity" % (sid, b))
    lid_moved = not identity(law.poses[LID])
    if lid_moved != expect_lid_moves:
        failures.append("%s: lid moved=%s, expected %s" % (sid, lid_moved, expect_lid_moves))
    if expect_lid_moves and lid_moved:
        # it must be a rotation about the EXISTING located hinge frame
        hinge = next(j for j in joints if j["entity_id"] == "JNT-0002")
        p = tuple(c * PER_UNIT for c in hinge["frame_origin"])
        f = law.poses[LID]
        moved_point = tuple(sum(f.r[i][k] * p[k] for k in range(3)) + f.t[i] for i in range(3))
        if not close(moved_point, p, 1e-6):
            failures.append("%s: the hinge point %s does not stay put (goes to %s)"
                            % (sid, [round(v, 3) for v in p],
                               [round(v, 3) for v in moved_point]))
        else:
            print("   hinge point %s is fixed under the lid's motion -> rotation is about "
                  "the existing hinge frame" % ([round(v, 1) for v in p],))

print("\n" + ("REGRESSION PASS" if not failures else "REGRESSION FAIL"))
for f in failures:
    print("  -", f)
sys.exit(1 if failures else 0)
