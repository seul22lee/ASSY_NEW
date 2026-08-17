"""Can the downstream REPRESENT the benchmarks it will be asked to run?

The prior review left this question open, and an open capability question is the
kind that gets answered by a run failing at the kernel months later. This file
answers the part of it that needs no kernel: the opcode vocabulary, the solver
formulations, and the limits of both. It is stdlib-only and runs on every push.

EVIDENCE IS CLASSIFIED, because the three kinds are not interchangeable:

  SOURCE-REQUIRED   a capability the benchmark request actually states. BM-002
                    says "rotate an external hand crank to raise and lower an
                    internal platform" and "approximately 80-100 mm", so
                    rotation-to-translation with a bounded travel IS required.

  CANDIDATE-ARCHETYPE  one supported mechanical formulation that could satisfy a
                    source-required capability. A lead screw satisfies BM-002's
                    travel; so does a rack and pinion, and so does a scissor
                    lift. The source names none of them. An earlier version of
                    this file wrote "BM-002 travel = lead x turns" as though the
                    benchmark demanded a lead screw - which would have made the
                    pipeline answerable for reproducing one archetype rather
                    than for solving the stated problem.

  UNSUPPORTED       a claim the system intentionally cannot make. Recorded as a
                    test so the boundary is discovered by reading the suite.

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

class TestBoundedTravelFromRotation_SourceRequired(unittest.TestCase):
    """SOURCE-REQUIRED. BM-002 states both halves of this in its request text:
    an external hand crank the user rotates, and a platform travel of
    approximately 80-100 mm.

    So what must be representable is a chain from a rotational input to a bounded
    translational output, with the bound CHECKED rather than assumed. The
    coefficient below is deliberately just a number - which archetype produces it
    is the design's business, not the requirement's.
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


class TestCoupledDimensions_SourceRequired(unittest.TestCase):
    """SOURCE-REQUIRED, in the weak and honest sense.

    BM-001 asks for a box with "a reusable latch" that opens and closes
    repeatedly "without accidental opening". It does not say snap latch, and it
    does not say cantilever. What any answer needs is the ability to dimension
    two mating parts against a shared constraint, because a latch and the thing
    it catches on must fit each other whatever archetype is chosen.

    Two unknowns tied by two equations, neither of which defines one directly.
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


class TestFixedAngleFormulation_CandidateArchetype(unittest.TestCase):
    """CANDIDATE-ARCHETYPE, not source-required.

    BM-003 asks that three legs "end up spread apart in different directions so
    they give the stand a usable footprint". It states no angle, and 120 degrees
    is one arrangement among many - an earlier version of this file implied the
    benchmark required it.

    What this shows is that IF a design commits to a fixed angle, the resulting
    footprint relation is linear and settles, because a fixed angle's sine is a
    constant coefficient. There is no `sin` in the IR, so what is NOT reachable
    is solving for the angle itself as an unknown of a trigonometric relation.
    `TestRecordedLimits` states that boundary.
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
        """A THREAD is not expressible.

        This bounds one CANDIDATE ARCHETYPE, not the benchmark: a design that
        answers BM-002 with a lead screw can represent the shaft as a cylinder,
        which is enough for envelope, interference and travel reasoning and is
        what S05-C8 compares. It is NOT enough to verify thread engagement or
        self-locking. A run that chose that archetype must not be read as having
        checked either. A design answering the same requirement with a rack and
        pinion is not affected by this limit at all.
        """
        for absent in ("HELIX", "SWEEP", "REVOLVE", "LOFT", "THREAD"):
            with self.subTest(opcode=absent):
                self.assertNotIn(absent, ir.OPCODES)

    def test_there_is_no_fillet_or_chamfer(self):
        """Angled lead-ins are reachable by a rotated CUT (proved in the kernel
        suite); a true radius is not.

        Again an archetype bound rather than a benchmark one: IF a design answers
        BM-001 with a cantilever snap, root stress concentration is outside what
        the run can speak to. The benchmark asks for a reusable latch and names
        no archetype."""
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


class TestTheClassificationMatchesTheSourceText(unittest.TestCase):
    """A SOURCE-REQUIRED claim must be traceable to words in the request.

    This is the guard against the failure the reclassification fixed: naming an
    archetype and treating it as a requirement. It reads the benchmark request
    text and checks that the archetype vocabulary does NOT appear in it - so if
    someone later writes "BM-002 requires a lead screw", the source itself
    contradicts them here.

    Reading the request text is not reading reference geometry. The request is
    the problem statement; rule 4 is about the executable answers.
    """

    #: Mechanism archetypes. None of these is named by any benchmark request,
    #: and each is one way among several to answer what IS named.
    ARCHETYPES = ("lead screw", "leadscrew", "rack and pinion", "snap latch",
                  "snap-fit", "scissor", "cantilever", "lead x turns")

    @classmethod
    def setUpClass(cls):
        import os
        from . import _paths
        cls.requests = {}
        for bm in ("BM-001", "BM-002", "BM-003"):
            path = os.path.join(_paths.REPO_ROOT, "ver3", "benchmarks", bm,
                                "source", "request.txt")
            with open(path) as handle:
                cls.requests[bm] = handle.read().lower()

    def test_the_requests_were_actually_read(self):
        """Otherwise every assertion below is about an empty string."""
        for bm, text in self.requests.items():
            with self.subTest(benchmark=bm):
                self.assertGreater(len(text), 200)

    def test_no_benchmark_request_names_a_mechanism_archetype(self):
        for bm, text in self.requests.items():
            for archetype in self.ARCHETYPES:
                with self.subTest(benchmark=bm, archetype=archetype):
                    self.assertNotIn(
                        archetype, text,
                        "%s names %r, so the classification in this file is "
                        "wrong and it may be genuinely source-required"
                        % (bm, archetype))

    def test_the_source_required_capabilities_really_are_in_the_text(self):
        """The other direction. A capability class labelled SOURCE-REQUIRED has
        to be findable in the request, or the label is as unfounded as the
        archetype claims it replaced."""
        self.assertIn("crank", self.requests["BM-002"])
        self.assertIn("80-100 mm", self.requests["BM-002"])
        self.assertIn("latch", self.requests["BM-001"])
        self.assertIn("three legs", self.requests["BM-003"])

    def test_bm003_states_no_angle(self):
        """The specific overreach that was corrected."""
        for token in ("120", "degree", "angle"):
            with self.subTest(token=token):
                self.assertNotIn(token, self.requests["BM-003"])

    def test_production_contains_no_benchmark_identity(self):
        """The classification would be worthless if production branched on a
        benchmark id regardless."""
        import os
        from . import _paths
        root = os.path.join(_paths.REPO_ROOT, "ver3", "assy_v3")
        offenders = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(base, name)
                with open(path) as handle:
                    body = handle.read()
                for token in ("BM-001", "BM-002", "BM-003"):
                    if token in body:
                        offenders.append("%s names %s" % (path, token))
        self.assertEqual([], offenders)


class TestNoReferenceGeometryReachedThisSuite(unittest.TestCase):
    """Rule 4, checked against this file rather than promised in its docstring.

    The distinction this guard has to make: a benchmark's REQUEST is the problem
    statement, and reading it is how the classification above is kept honest -
    a SOURCE-REQUIRED claim has to be checkable against the words that make it
    required. A benchmark's executable reference is an ANSWER, and reading that
    would be reproduction rather than capability.

    So `benchmarks/<id>/source/` is permitted and the geometry directories are
    not. Written as a rule rather than an exception list of one, because the
    next legitimate source read should not have to amend this class.
    """

    #: Directories holding reference and oracle GEOMETRY - answers, not problems.
    OFF_LIMITS = ("cad_validation", "oracles", "executable_references")

    #: The problem statements. Reading a request is reading what was asked.
    PERMITTED_READS = ("benchmarks",)

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

    def test_the_suite_reads_no_geometry_artifact(self):
        """Every path this file builds must be a problem statement or itself.

        Checked on path ADJACENCY, and excluding this class's own literals - a
        bare substring scan finds the banned list itself and the docstrings that
        explain the rule, and fails on the explanation instead of on a
        violation.
        """
        for text in self._literals_outside_this_check():
            for banned in self.OFF_LIMITS:
                if banned + "/" in text or "/" + banned in text:
                    self.fail("this suite names a path into %s: %r"
                              % (banned, text[:80]))

    def test_the_only_benchmark_path_is_a_request(self):
        """A permitted read of the benchmark tree must be of the SOURCE request,
        not of a run, an evaluation or anything else under it."""
        literals = self._literals_outside_this_check()
        self.assertIn("request.txt", literals,
                      "the classification guard no longer reads any request; "
                      "SOURCE-REQUIRED claims are then unchecked")
        for text in literals:
            if "benchmarks/" in text or "/benchmarks" in text:
                self.fail("a composed path into the benchmark tree: %r" % text)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
