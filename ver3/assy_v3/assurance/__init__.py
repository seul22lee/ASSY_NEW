"""Independent assurance. READS COMMITTED STATE, WRITES NOTHING.

S-8 / U-9. The layer exists because the pipeline was grading itself: every check
lived in the module of the stage it judged, two of them tested properties that
module guaranteed by construction, and the result was reported on one axis that
mixed four different questions.

    producing responsibility -> committed DesignState -> assurance

The arrow only points that way. No module under `stages/` may import anything
here; nothing here may author class-A state, and no provider is reachable from
it - a check that had to ask a model would be an opinion about an opinion.
"""
from .model import (AssuranceSnapshot, BOOKKEEPING, Check, CheckResult,
                    ENGINEERING_CONSEQUENCE, ENGINEERING_ESTABLISHED, EXTERNAL,
                    FIDELITY, Finding, NOT_ESTABLISHED, PREMISE,
                    PROVENANCE_INTEGRITY, STRUCTURAL)
from .registry import NOT_ASSURANCE, REGISTRY
from .runner import declarations, run_assurance


def problems(state, check_id: str):
    """The FAIL findings of one capability, as text. A REPORTING PROJECTION.

    The capabilities return typed findings; a caller that only wants to print
    what went wrong gets the same list of sentences the relocated checks used to
    return. It is not a compatibility path back to the old location - there is no
    way to reach a check from a stage module through it, which is the property
    the move exists to create.
    """
    snapshot = run_assurance(state, only=(check_id,))
    return [f.detail for r in snapshot.results for f in r.findings
            if f.outcome == "FAIL"]

__all__ = ["AssuranceSnapshot", "BOOKKEEPING", "Check", "CheckResult",
           "ENGINEERING_CONSEQUENCE", "ENGINEERING_ESTABLISHED", "EXTERNAL",
           "FIDELITY", "Finding", "NOT_ASSURANCE", "NOT_ESTABLISHED", "PREMISE",
           "PROVENANCE_INTEGRITY", "REGISTRY", "STRUCTURAL", "declarations",
           "problems", "run_assurance"]
