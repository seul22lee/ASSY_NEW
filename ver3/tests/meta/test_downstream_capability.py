"""Can the downstream REPRESENT the benchmarks it will be asked to run?

The prior review left this question open, and an open capability question is the
kind that gets answered by a run failing at the kernel months later. This file
answers the part of it that needs no kernel: the opcode vocabulary, the solver
formulations that BM-001, BM-002 and BM-003 actually require, and the limits of
both. It is stdlib-only and runs on every push.

The COMPILING half - putting each geometric archetype through a real
OpenCascade build - is `ver3/tests/kernel/test_capability_geometry.py`, run by
the downstream CI job. The split is by dependency: this file was briefly one
suite, and the boundaries job, which installs nothing but PyYAML, discovered the
geometry tests and failed for an environment reason that had nothing to do with
any boundary. Moving them is the fix; skip-guarding them would have left a suite
that reports success by not running.

Two rules this file holds itself to.

FIRST, no reference geometry. Rebuild policy rule 4 forbids the executable
references from being a production input, and a capability test that copied
their dimensions would be checking reproduction rather than capability.

SECOND, the limits are recorded as tests too. A capability suite that only
demonstrates successes is a brochure. Where the vocabulary cannot express
something - a helical thread, a trigonometric relation, a nonlinear equation -
that is asserted as an explicit boundary, so the day someone adds the opcode the
test tells them the limit moved rather than staying quietly green.
"""

import unittest

from ver3.assy_v3.downstream import ir, solver


def const(value, unit="mm"):
    return {"const": float(value), "unit": unit}


def ref(name):
    return {"ref": name}


def op(name, *args):
    return {"op": name, "args": list(args)}


def declare(eid, symbol, unit):
    return ir.ParameterDecl.parse({"entity_id": eid, "symbol": symbol,
                                   "unit": unit, "status": "DECLARED"})


def relate(eid, relation, lhs, rhs, kind="DIMENSIONAL"):
    return ir.TypedConstraint.parse({
        "entity_id": eid, "kind": kind, "parameters": [],
        "expression": {"relation": relation, "lhs": lhs, "rhs": rhs}})


class TestPoseIsNotAnOpcodeQuestion(unittest.TestCase):
    """The half of the orientation argument that needs no kernel.

    Deliberately OUTSIDE the kernel-guarded classes above, so the frame rule is
    still checked in the stdlib boundary job. It reads the opcode table, and an
    opcode table is not geometry.
    """

    def test_no_opcode_places_a_body_in_the_world(self):
        """The rule that makes the pose question s04's rather than s07's."""
        for opcode in ir.OPCODES:
            with self.subTest(opcode=opcode):
                self.assertNotIn("PLACE", opcode)
                self.assertNotIn("POSE", opcode)
                self.assertNotIn("ASSEMBLE", opcode)


# ======================================================================
# PARAMETRICS - what the typed IR can settle
# ======================================================================

class TestTravelChainClass(unittest.TestCase):
    """BM-002 states a quantity the design must hit: 80-100 mm of platform travel.

    The capability is a linear chain from an input the user turns to an output
    the requirement bounds, with the bound checked rather than assumed.
    """

    def _travel(self, lead, turns):
        return solver.solve(
            [declare("PRM-T", "travel", "mm"), declare("PRM-N", "turns", "1")],
            [relate("C1", "==", ref("PRM-N"), const(turns, "1")),
             relate("C2", "==", ref("PRM-T"), op("*", const(lead), ref("PRM-N"))),
             relate("C3", ">=", ref("PRM-T"), const(80)),
             relate("C4", "<=", ref("PRM-T"), const(100))])

    def test_a_linear_drive_chain_settles_inside_the_declared_window(self):
        report = self._travel(lead=2.0, turns=45)
        self.assertEqual(solver.FEASIBLE, report.solver_status, report.problems)
        self.assertAlmostEqual(90.0, report.settled["PRM-T"], places=6)

    def test_a_chain_that_misses_the_window_is_reported_infeasible(self):
        """The value that matters. A solver that settles 60 mm and calls the
        design feasible has answered a different question than the one asked."""
        report = self._travel(lead=2.0, turns=30)
        self.assertEqual(solver.INFEASIBLE, report.solver_status)
        self.assertIn("C3", report.conflicting,
                      "infeasible without naming the bound it violated leaves "
                      "nobody able to act on it")

    def test_an_unset_input_is_underdetermined_not_defaulted(self):
        report = solver.solve(
            [declare("PRM-T", "travel", "mm"), declare("PRM-N", "turns", "1")],
            [relate("C2", "==", ref("PRM-T"), op("*", const(2.0), ref("PRM-N")))])
        self.assertEqual(solver.UNDERDETERMINED, report.solver_status)
        self.assertEqual({}, report.settled,
                         "a value was settled from an underdetermined system, "
                         "which means something was chosen rather than derived")


class TestCoupledGeometryClass(unittest.TestCase):
    """BM-001's latch and its catch are dimensioned against the same wall.

    Two unknowns tied by two equations neither of which defines one directly.
    Substitution cannot start here; this is why the solver is an elimination
    rather than a chain of definitions.
    """

    def test_a_two_by_two_coupled_system_settles(self):
        report = solver.solve(
            [declare("PRM-C", "catch", "mm"), declare("PRM-G", "gap", "mm")],
            [relate("C1", "==", op("+", ref("PRM-C"), ref("PRM-G")), const(3.0)),
             relate("C2", "==", op("-", ref("PRM-C"), ref("PRM-G")), const(1.0))])
        self.assertEqual(solver.FEASIBLE, report.solver_status, report.problems)
        self.assertAlmostEqual(2.0, report.settled["PRM-C"], places=9)
        self.assertAlmostEqual(1.0, report.settled["PRM-G"], places=9)


class TestFixedAngleGeometryClass(unittest.TestCase):
    """BM-003's legs spread at a fixed angle, and the footprint follows from it.

    There is no `sin` in the IR. With the angle FIXED - which is what "spread
    apart in three directions" means - its sine is a constant coefficient and
    the relation is linear, so the footprint settles. What is NOT reachable is
    solving for the angle itself; `TestRecordedLimits` states that boundary.
    """

    def test_a_fixed_angle_coefficient_settles_the_footprint(self):
        report = solver.solve(
            [declare("PRM-F", "footprint", "mm"), declare("PRM-L", "leg", "mm")],
            [relate("C1", "==", ref("PRM-L"), const(120.0)),
             relate("C2", "==", ref("PRM-F"),
                    op("*", const(0.866, "1"), ref("PRM-L")))])
        self.assertEqual(solver.FEASIBLE, report.solver_status, report.problems)
        self.assertAlmostEqual(103.92, report.settled["PRM-F"], places=2)


# ======================================================================
# THE LIMITS, stated as tests
# ======================================================================

class TestRecordedLimits(unittest.TestCase):
    """What this downstream CANNOT represent, asserted so the boundary is known.

    Each of these is a real constraint on what a benchmark run can conclude. None
    of them is a defect: refusing to answer is the correct behaviour for a
    formulation the solver cannot honestly reduce. They are here so the limits
    are discovered by reading the suite rather than by a run behaving oddly.
    """

    def test_there_is_no_swept_or_helical_geometry(self):
        """A lead screw's THREAD is not expressible.

        BM-002's screw is representable as a cylindrical shaft, which is enough
        for envelope, interference and travel reasoning - and is what S05-C8
        compares. It is NOT enough to verify thread engagement or self-locking,
        so a BM-002 run must not be read as having checked those.
        """
        for absent in ("HELIX", "SWEEP", "REVOLVE", "LOFT", "THREAD"):
            with self.subTest(opcode=absent):
                self.assertNotIn(absent, ir.OPCODES)

    def test_there_is_no_fillet_or_chamfer(self):
        """Angled lead-ins are reachable by a rotated CUT (proved above); a true
        radius is not. Stress concentration at a snap-latch root is therefore
        outside what any BM-001 run can speak to."""
        for absent in ("FILLET", "CHAMFER", "DRAFT", "SHELL"):
            with self.subTest(opcode=absent):
                self.assertNotIn(absent, ir.OPCODES)

    def test_the_opcode_set_is_closed_at_eight(self):
        """Pinned so an addition is a decision someone makes deliberately."""
        self.assertEqual(
            ["BOX", "CUT", "CYLINDER", "INTERSECT", "ROTATE", "SPHERE",
             "TRANSLATE", "UNION"], sorted(ir.OPCODES))

    def test_a_nonlinear_relation_is_refused_rather_than_approximated(self):
        """Beam deflection, thread torque and crank-slider kinematics are all
        nonlinear. The solver must say so; a linearised guess would be a number
        nobody decided, which is exactly what R-24 forbids."""
        report = solver.solve(
            [declare("PRM-D", "defl", "mm"), declare("PRM-L", "len", "mm")],
            [relate("C1", "==", ref("PRM-D"), op("*", ref("PRM-L"), ref("PRM-L")))])
        self.assertEqual(solver.UNSUPPORTED_FORMULATION, report.solver_status)
        self.assertEqual({}, report.settled)

    def test_there_are_no_transcendental_functions_in_the_expression_grammar(self):
        """So an angle can never be a solved unknown of a trigonometric relation;
        it has to arrive fixed, with its sine as a coefficient."""
        for absent in ("sin", "cos", "tan", "sqrt", "exp", "log", "**", "^"):
            with self.subTest(operator=absent):
                self.assertNotIn(absent, ir.ARITHMETIC)

    def test_a_dimensional_violation_is_refused(self):
        """Not a limit so much as the guard that makes the rest trustworthy."""
        report = solver.solve(
            [declare("PRM-A", "a", "mm")],
            [relate("C1", "==", ref("PRM-A"), const(5.0, "mm^2"))])
        self.assertEqual(solver.UNSUPPORTED_FORMULATION, report.solver_status)


class TestNoReferenceGeometryReachedThisSuite(unittest.TestCase):
    """Rule 4, checked against this file rather than promised in its docstring."""

    #: Directories holding reference and oracle geometry. A production or test
    #: path into any of them is the rule-4 violation this guards.
    OFF_LIMITS = ("cad_validation", "oracles", "executable_references",
                  "benchmarks")

    def _literals_outside_this_check(self):
        """Every string literal in the module except this class's own.

        Checked against the AST rather than the raw text, because a plain
        substring scan finds the banned list itself and fails on the guard
        instead of on a violation - which is a test that cannot pass rather
        than a test that catches something.
        """
        import ast
        tree = ast.parse(open(__file__).read())
        mine = {n for n in ast.walk(tree)
                if isinstance(n, ast.ClassDef)
                and n.name == "TestNoReferenceGeometryReachedThisSuite"}
        skip = {id(n) for cls in mine for n in ast.walk(cls)}
        return [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in skip]

    def test_the_scan_found_the_suite(self):
        """A scan that found no literals would pass while reading nothing."""
        self.assertGreater(len(self._literals_outside_this_check()), 50)

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
        tree = ast.parse(open(__file__).read())
        for node in ast.walk(tree):
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
