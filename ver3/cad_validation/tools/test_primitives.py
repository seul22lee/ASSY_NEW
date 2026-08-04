"""Self-tests for the shared primitives both CAD references depend on.

A defect in any of these would corrupt both references at once and would not
show up as a failure - it would show up as a clean report about the wrong thing.
Each test therefore checks a primitive against a closed-form answer, not against
another run of the same code.

The regression that motivates this file: cadval.rotation once used CadQuery's
three-argument Location as if it rotated about an arbitrary line. It does not -
it rotates about an axis through the world origin and then translates. Every
motion result computed with it was meaningless, and nothing in the validation
chain could have noticed, because the geometry was still valid and still did not
interpenetrate. TEST 1 pins that behaviour permanently.

    python test_primitives.py
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadval as cv      # noqa: E402
import valcore as vc     # noqa: E402

EPS = 1e-9
_results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, bool(ok), detail))
    print("  %-58s %s%s" % (name, "ok" if ok else "FAIL",
                            ("  " + detail) if detail and not ok else ""))


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


# ------------------------------------------------------------------ TEST 1
def test_rotation_about_a_line() -> None:
    print("\n1  rotation about an arbitrary line")
    origin, axis = (0.0, 86.0, 50.0), (1.0, 0.0, 0.0)

    # a) every point ON the axis is fixed, at every angle
    worst = 0.0
    for deg in (0.0, 17.5, 90.0, 110.0, -110.0, 359.0):
        loc = cv.rotation(origin, axis, deg)
        for x in (-30.0, 0.0, 50.0, 200.0):
            p = cq.Vertex.makeVertex(x, origin[1], origin[2]).moved(loc).Center()
            worst = max(worst, abs(p.x - x), abs(p.y - origin[1]), abs(p.z - origin[2]))
    check("1a axis points are fixed", worst < 1e-9, "max deviation %.3e" % worst)

    # b) closed form: a point one unit above the axis, rotated 90 degrees about
    #    +X, must land one unit behind it. Sign convention is part of the
    #    contract - reference 1's opening sense depends on it.
    loc = cv.rotation(origin, axis, 90.0)
    p = cq.Vertex.makeVertex(10.0, origin[1], origin[2] + 1.0).moved(loc).Center()
    check("1b 90 deg maps +Z offset to -Y offset",
          close(p.x, 10.0, 1e-9) and close(p.y, origin[1] - 1.0, 1e-9)
          and close(p.z, origin[2], 1e-9),
          "got (%.6f, %.6f, %.6f)" % (p.x, p.y, p.z))

    # c) rotating by d then by -d is the identity
    a = cv.rotation(origin, axis, 37.25)
    b = cv.rotation(origin, axis, -37.25)
    p = cq.Vertex.makeVertex(12.0, 3.0, 4.0).moved(a).moved(b).Center()
    check("1c rotation composes to identity with its inverse",
          close(p.x, 12.0, 1e-9) and close(p.y, 3.0, 1e-9) and close(p.z, 4.0, 1e-9))

    # d) a rigid rotation preserves volume exactly
    box = cq.Solid.makeBox(10, 20, 30, pnt=cq.Vector(5, 70, 40))
    v0 = cv._gprops_volume(box)
    v1 = cv._gprops_volume(box.moved(cv.rotation(origin, axis, 110.0)))
    check("1d rotation preserves volume", close(v0, v1, 1e-6),
          "%.9f vs %.9f" % (v0, v1))

    # e) THE REGRESSION. The naive three-argument Location is a different rigid
    #    motion whenever the axis does not pass through the origin. If these ever
    #    agree, either CadQuery's semantics changed or cadval.rotation has been
    #    rewritten back into the bug.
    naive = cq.Location(cq.Vector(*origin), cq.Vector(*axis), 110.0)
    pn = cq.Vertex.makeVertex(0.0, origin[1], origin[2]).moved(naive).Center()
    check("1e naive Location(t, ax, deg) does NOT fix the axis",
          not (close(pn.y, origin[1], 1e-6) and close(pn.z, origin[2], 1e-6)),
          "naive put the axis point at (%.3f, %.3f, %.3f)" % (pn.x, pn.y, pn.z))


# ------------------------------------------------------------------ TEST 2
def test_common_volume() -> None:
    print("\n2  common volume - the overlap primitive")
    a = cq.Solid.makeBox(10, 10, 10)
    # a) known overlap: shifted 4 in x -> 6 x 10 x 10
    b = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(4, 0, 0))
    check("2a known interpenetration is exact",
          close(cv.common_volume(a, b), 600.0, 1e-6),
          "%.9f" % cv.common_volume(a, b))
    # b) face-to-face contact is NOT overlap
    t = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(10, 0, 0))
    check("2b touching solids have zero common volume",
          cv.common_volume(a, t) <= 1e-9, "%.3e" % cv.common_volume(a, t))
    # c) disjoint
    d = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(50, 0, 0))
    check("2c disjoint solids have zero common volume", cv.common_volume(a, d) <= 1e-9)
    # d) a penetration far below the evaluation tolerance is still measured, not
    #    rounded away - the tolerance is applied by the caller, never here
    s = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(9.999, 0, 0))
    check("2d sub-tolerance penetration is still reported",
          cv.common_volume(a, s) > 0.0, "%.6e" % cv.common_volume(a, s))


# ------------------------------------------------------------------ TEST 3
def test_min_distance() -> None:
    print("\n3  minimum distance - and why it cannot replace common volume")
    a = cq.Solid.makeBox(10, 10, 10)
    g = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(10.25, 0, 0))
    check("3a known gap is exact", close(cv.min_distance(a, g), 0.25, 1e-9),
          "%.9f" % cv.min_distance(a, g))
    t = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(10, 0, 0))
    check("3b touching solids are at distance zero", close(cv.min_distance(a, t), 0.0, 1e-9))
    o = cq.Solid.makeBox(10, 10, 10, pnt=cq.Vector(4, 0, 0))
    # This is the whole reason both primitives exist. Contact and penetration are
    # indistinguishable by distance; only volume separates them.
    check("3c overlapping solids are ALSO at distance zero",
          close(cv.min_distance(a, o), 0.0, 1e-9)
          and cv.common_volume(a, o) > 1e-6,
          "distance %.6f, common %.3f" % (cv.min_distance(a, o), cv.common_volume(a, o)))


# ------------------------------------------------------------------ TEST 4
def test_clip() -> None:
    print("\n4  region-of-interest clipping")
    body = cq.Solid.makeBox(100, 10, 10)
    roi = vc.roi_box(20.0, 30.0, -1.0, 11.0, -1.0, 11.0)
    c = vc.clip(body, roi)
    check("4a clipped volume is exact",
          c is not None and close(cv._gprops_volume(c), 10 * 10 * 10, 1e-6),
          "%.6f" % (cv._gprops_volume(c) if c else -1))
    empty = vc.clip(body, vc.roi_box(500.0, 510.0, 0.0, 1.0, 0.0, 1.0))
    check("4b a region with no material returns None", empty is None)
    # A clip that silently returned the unclipped body would make every localized
    # measurement wrong while still looking plausible.
    check("4c clipping actually restricts the body",
          c is not None and cv._gprops_volume(c) < cv._gprops_volume(body))
    # excluded cylinder, as used to separate INT-15 from INT-10
    roi2 = vc.roi_box(0.0, 10.0, 0.0, 10.0, 0.0, 10.0).cut(
        cq.Solid.makeCylinder(2.0, 12.0, pnt=cq.Vector(5, 5, -1), dir=cq.Vector(0, 0, 1)))
    c2 = vc.clip(cq.Solid.makeBox(10, 10, 10), roi2)
    want = 1000.0 - math.pi * 4.0 * 10.0
    check("4d region with an excluded cylinder is exact",
          c2 is not None and close(cv._gprops_volume(c2), want, 1e-4),
          "%.6f vs %.6f" % (cv._gprops_volume(c2) if c2 else -1, want))


# ------------------------------------------------------------------ TEST 5
def test_signature() -> None:
    print("\n5  geometry signature and rebuild comparison")
    def mk(dx=10.0):
        return [cv.Body("B-1", "one", "GENERIC_RIGID_POLYMER",
                        cq.Solid.makeBox(dx, 10, 10)),
                cv.Body("B-2", "two", "GENERIC_RIGID_METAL",
                        cq.Solid.makeBox(5, 5, 5, pnt=cq.Vector(20, 0, 0)))]
    crit = {"dx": 10.0}
    s1 = cv.geometry_signature(mk(), critical=crit, motion={}, states={})
    s2 = cv.geometry_signature(mk(), critical=crit, motion={}, states={})
    check("5a identical rebuild gives an identical hash",
          s1["signature_sha256"] == s2["signature_sha256"])
    check("5b identical rebuild is within tolerance",
          cv.compare_signatures(s1, s2)["within_tolerance"])
    s3 = cv.geometry_signature(mk(10.001), critical={"dx": 10.001}, motion={}, states={})
    cmp3 = cv.compare_signatures(s1, s3)
    check("5c a 1 micron change in one body is detected",
          not cmp3["within_tolerance"] and s1["signature_sha256"] != s3["signature_sha256"],
          str(cmp3["differences"])[:80])
    s4 = cv.geometry_signature(mk(), critical={"dx": 10.5}, motion={}, states={})
    check("5d a changed critical dimension is detected even when solids match",
          not cv.compare_signatures(s1, s4)["within_tolerance"])
    check("5e a changed motion record changes the hash",
          cv.geometry_signature(mk(), critical=crit, motion={"a": 1}, states={})
          ["signature_sha256"] != s1["signature_sha256"])


# ------------------------------------------------------------------ TEST 6
def test_roundtrip() -> None:
    print("\n6  export and re-import round trip")
    body = cq.Solid.makeBox(12, 34, 5.6, pnt=cq.Vector(1, 2, 3)).cut(
        cq.Solid.makeCylinder(2.0, 20.0, pnt=cq.Vector(6, 20, 0), dir=cq.Vector(0, 0, 1)))
    v0 = cv._gprops_volume(body)
    d = tempfile.mkdtemp()
    sp, bp = os.path.join(d, "t.step"), os.path.join(d, "t.brep")
    cv.export_step(body, sp)
    cv.export_brep(body, bp)
    vs, vb = cv._gprops_volume(cv.import_step(sp)), cv._gprops_volume(cv.import_brep(bp))
    check("6a STEP round trip preserves volume", close(v0, vs, 1e-6),
          "%.9f vs %.9f" % (v0, vs))
    check("6b BREP round trip preserves volume", close(v0, vb, 1e-9),
          "%.9f vs %.9f" % (v0, vb))
    check("6c re-imported solids are valid",
          cv.is_valid(cv.import_step(sp)) and cv.is_valid(cv.import_brep(bp)))


# ------------------------------------------------------------------ TEST 7
def test_translation_and_validity() -> None:
    print("\n7  translation, validity and body identity")
    box = cq.Solid.makeBox(10, 10, 10)
    m = box.moved(cv.translation((3.0, -4.0, 5.0)))
    # Exactness is checked on the centre of mass, which is exact. The bounding
    # box is not: see the docstring on cadval.bbox_of.
    com = cv._com(m)
    check("7a translation moves the centre of mass exactly",
          close(com[0], 8.0, 1e-9) and close(com[1], 1.0, 1e-9)
          and close(com[2], 10.0, 1e-9),
          "got %s" % (com,))
    bb = cv.bbox_of(m)
    gap = max(abs(bb["xmin"] - 3.0), abs(bb["ymin"] + 4.0), abs(bb["zmin"] - 5.0),
              abs(bb["xmax"] - 13.0), abs(bb["ymax"] - 6.0), abs(bb["zmax"] - 15.0))
    check("7a2 Bnd_Box inflation stays below the signature tolerance",
          gap < 1e-6, "inflation %.3e, compare_signatures len_tol 1e-6" % gap)
    check("7b translation preserves volume",
          close(cv._gprops_volume(box), cv._gprops_volume(m), 1e-9))
    check("7c BRepCheck_Analyzer accepts a well-formed solid", cv.is_valid(box))
    b = cv.Body("B-9", "n", "GENERIC_RIGID_POLYMER", box, role="r", installed_as="DISCRETE")
    mv = b.moved(cv.translation((1.0, 0.0, 0.0)))
    check("7d Body.moved keeps the semantic id and material class",
          mv.id == b.id and mv.material_class == b.material_class
          and mv.installed_as == b.installed_as)


def main() -> int:
    print("shared primitive self-tests  (cadval, valcore)")
    for t in (test_rotation_about_a_line, test_common_volume, test_min_distance,
              test_clip, test_signature, test_roundtrip, test_translation_and_validity):
        t()
    failed = [n for n, ok, _ in _results if not ok]
    print("\n%d/%d passed" % (len(_results) - len(failed), len(_results)))
    for n in failed:
        print("  FAILED: %s" % n)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
