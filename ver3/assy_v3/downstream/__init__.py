"""The deterministic downstream: settlement (s06) and compilation (s07).

s05 is a producing RESPONSIBILITY and lives with the other stages. s06 and s07
are not: they are deterministic services with no model involvement and no
engineering authority, and putting them beside the stages would invite exactly
the confusion their contracts spend most of their length preventing.

    ir        the typed representations s05 authors and s06/s07 consume
    solver    s06 - solve, or say precisely why not
    compiler  s07 - compile faithfully, export, and fail loudly rather than repair
"""
from .ir import (ConstructionProgram, Expr, ParameterDecl, TypedConstraint,
                 OPCODES, SOLVER_STATUSES)

__all__ = ["ConstructionProgram", "Expr", "ParameterDecl", "TypedConstraint",
           "OPCODES", "SOLVER_STATUSES"]
