"""Can the closed opcode set actually BUILD what the benchmarks need?

The compiling half of the capability review. BM-001 (hinged cover with a snap
latch), BM-002 (enclosed hand-cranked platform lift) and BM-003 (folding
three-leg stand) are decomposed into geometric capability classes, and each one
is put through a real OpenCascade compile.

The non-compiling half - the opcode vocabulary, the solver formulation, and the
recorded limits - lives in `ver3/tests/meta/test_downstream_capability.py` and
runs on every push without a kernel. This file is separated from it by
DEPENDENCY: see this package's docstring for why that is a placement decision
rather than a skip.

No reference geometry. Rebuild policy rule 4 forbids the executable references
from being a production input, and a capability test that copied their
dimensions would be checking reproduction rather than capability. Every shape
below is a generic archetype with invented numbers - a shelled box, a
cantilever, a rotated cut. What is asserted is that the CLASS compiles, never
that the result resembles anyone's answer.
"""

import unittest

from ver3.assy_v3.downstream import compiler, ir


def const(value, unit="mm"):
    return {"const": float(value), "unit": unit}


def stmt(eid, operation, operands=(), body="BOD-1", axis=None, **params):
    """One construction step. Unit G: steps are a FEATURE'S; the whole
    sequence here is one STOCK feature of one body, built at the identity."""
    record = {"id": eid, "operation": operation,
              "operands": list(operands), "parameters": dict(params)}
    if axis:
        record["axis"] = axis
    return record


def compile_body(records, values=None, body="BOD-1"):
    from ver3.assy_v3.downstream.embodiment import polarity_table
    from ver3.assy_v3.downstream.kinematics import Frame
    spec = ir.FeatureSpec(entity_id="FEA-1", body=body, kind="STOCK",
                          placement=ir.Placement.parse({"datum": "ENV-1", "axis": "+Z"}),
                          steps=tuple(ir.Step.parse(r) for r in records))
    return compiler.compile_embodiment([spec], dict(values or {}), {"FEA-1": Frame()},
                                       polarity_table())


class TestTheKernelIsReallyHere(unittest.TestCase):
    """Asserted in the suite as well as in the workflow step.

    The workflow checks the kernel before running these, which is what makes a
    failure below a real failure. This says the same thing from inside the
    suite, so running it by hand in an environment without OpenCascade reports
    the missing kernel rather than eight confusing geometry failures.
    """

    def test_opencascade_is_importable(self):
        compiler.kernel()          # raises KernelUnavailable if it is not


class TestEnclosureClass(unittest.TestCase):
    """A shelled housing with a through-bore.

    BM-001 needs a box that opens (shell plus a hinge bore); BM-002 needs a
    housing the mechanism stays inside. Both are the same capability class: a
    solid hollowed by a CUT, then bored by a rotated CYLINDER.
    """

    def _shelled_box_with_bore(self):
        return [
            stmt("A", "BOX", dx=const(100), dy=const(60), dz=const(40)),
            stmt("B", "BOX", dx=const(94), dy=const(54), dz=const(36)),
            stmt("C", "TRANSLATE", ["B"], dx=const(3), dy=const(3), dz=const(3)),
            stmt("D", "CUT", ["A", "C"]),
            stmt("E", "CYLINDER", radius=const(2), height=const(60)),
            stmt("F", "ROTATE", ["E"], axis="X", angle=const(-90, "deg")),
            stmt("G", "TRANSLATE", ["F"], dx=const(50), dy=const(60), dz=const(38)),
            stmt("H", "CUT", ["D", "G"]),
        ]

    def test_a_shelled_enclosure_with_a_bore_compiles(self):
        result = compile_body(self._shelled_box_with_bore())
        self.assertTrue(result.ok, result.problems)
        self.assertTrue(result.bodies, "compiled without producing a body")

    def test_the_shell_is_hollow_rather_than_solid(self):
        """Otherwise 'it compiled' would be true of a solid block."""
        result = compile_body(self._shelled_box_with_bore())
        solid = compile_body([stmt("A", "BOX", dx=const(100), dy=const(60),
                                   dz=const(40))])
        self.assertTrue(solid.ok, solid.problems)
        self.assertLess(result.bodies[0].volume, solid.bodies[0].volume,
                        "the CUT removed nothing; this is a solid block that "
                        "happens to compile")


class TestCantileverWithAngledLeadInClass(unittest.TestCase):
    """BM-001's snap latch: an arm, a barb, and a ramp that lets it deflect in.

    There is no CHAMFER opcode, so the question is whether the FUNCTION - an
    angled lead-in face - is reachable at all. It is: a rotated BOX cut against
    the barb produces the ramp. A true filleted radius is not reachable, and the
    recorded limits in the meta suite say so rather than this test implying
    otherwise.
    """

    def _arm(self):
        return [
            stmt("A", "BOX", dx=const(20), dy=const(3), dz=const(2)),
            stmt("B", "BOX", dx=const(3), dy=const(3), dz=const(3)),
            stmt("C", "TRANSLATE", ["B"], dx=const(18), dy=const(0), dz=const(1)),
            stmt("D", "UNION", ["A", "C"]),
        ]

    def _ramp(self):
        return [
            stmt("E", "BOX", dx=const(6), dy=const(6), dz=const(6)),
            stmt("F", "ROTATE", ["E"], axis="Y", angle=const(35, "deg")),
            stmt("G", "TRANSLATE", ["F"], dx=const(21), dy=const(0), dz=const(3)),
            stmt("H", "CUT", ["D", "G"]),
        ]

    def test_a_cantilever_with_a_rotated_lead_in_cut_compiles(self):
        result = compile_body(self._arm() + self._ramp())
        self.assertTrue(result.ok, result.problems)

    def test_the_angled_cut_actually_removed_material(self):
        base = compile_body(self._arm())
        cut = compile_body(self._arm() + self._ramp())
        self.assertTrue(base.ok, base.problems)
        self.assertTrue(cut.ok, cut.problems)
        self.assertLess(cut.bodies[0].volume, base.bodies[0].volume,
                        "the ramp cut nothing away, so this proves no lead-in")


class TestArbitraryOrientationIsReachable(unittest.TestCase):
    """ROTATE names one of X/Y/Z. That is not a limit on reachable orientation.

    BM-003's legs point in three different directions, which reads at first like
    a demand for arbitrary-axis rotation. Two answers, and the second is the one
    that matters.

    Within a body, composed principal rotations reach any orientation - that is
    what Euler angles are - and the test below shows a composition behaving as a
    rigid motion.

    Between bodies the question does not arise, and THAT half needs no kernel:
    the construction_frame_rule keeps world placement out of the program
    entirely, so where a leg points is a pose applied downstream from located
    joint frames. `TestPoseIsNotAnOpcodeQuestion` in the meta suite holds it, so
    the frame rule is still checked on every push.
    """

    def test_composed_principal_rotations_are_a_rigid_motion(self):
        flat = compile_body([stmt("A", "BOX", dx=const(60), dy=const(10),
                                  dz=const(4))])
        turned = compile_body([
            stmt("A", "BOX", dx=const(60), dy=const(10), dz=const(4)),
            stmt("B", "ROTATE", ["A"], axis="X", angle=const(30, "deg")),
            stmt("C", "ROTATE", ["B"], axis="Z", angle=const(40, "deg"))])
        self.assertTrue(flat.ok, flat.problems)
        self.assertTrue(turned.ok, turned.problems)
        self.assertAlmostEqual(flat.bodies[0].volume, turned.bodies[0].volume,
                               delta=1e-6,
                               msg="a rotation changed the volume, so this is "
                                   "not a rigid motion and the composition is "
                                   "not doing what the test claims")


class TestNoReferenceGeometryReachedThisSuite(unittest.TestCase):
    """Rule 4, checked against this file rather than promised in its docstring.

    It matters most here: this is the file that holds actual geometry, so it is
    the one where reading a reference STEP would be easiest and worst.
    """

    OFF_LIMITS = ("cad_validation", "oracles", "executable_references",
                  "benchmarks")

    def _literals_outside_this_check(self):
        """Every string literal in the module except this class's own.

        Checked against the AST rather than the raw text, because a plain
        substring scan finds the banned list itself and fails on the guard
        instead of on a violation.
        """
        import ast
        tree = ast.parse(open(__file__).read())
        mine = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
                and n.name == "TestNoReferenceGeometryReachedThisSuite"]
        skip = {id(n) for cls in mine for n in ast.walk(cls)}
        return [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in skip]

    def test_the_scan_found_the_suite(self):
        """A scan that found no literals would pass while reading nothing."""
        self.assertGreater(len(self._literals_outside_this_check()), 30)

    def test_no_path_into_reference_or_oracle_geometry(self):
        """A PATH into those directories, not a mention of them.

        The first version flagged any literal containing a banned word and a
        slash anywhere, so this file's own docstring - which names the
        benchmarks it reasons about, and cites a sibling file by path - tripped
        it. Requiring the separator to be ADJACENT to the directory name is what
        makes it a path test rather than a word filter.
        """
        for text in self._literals_outside_this_check():
            for banned in self.OFF_LIMITS:
                if banned + "/" in text or "/" + banned in text:
                    self.fail("a literal names a path into %s: %r"
                              % (banned, text[:80]))

    def test_the_suite_opens_no_file_but_its_own_source(self):
        import ast
        for node in ast.walk(ast.parse(open(__file__).read())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "open":
                arg = node.args[0] if node.args else None
                self.assertTrue(
                    isinstance(arg, ast.Name) and arg.id == "__file__",
                    "this suite opens a file other than its own source; every "
                    "shape here must be an invented archetype, never geometry "
                    "read from a reference")


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
