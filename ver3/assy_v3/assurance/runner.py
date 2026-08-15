"""RUN EVERY DECLARED CHECK OVER COMMITTED STATE. Write nothing.

S-8 / U-9. The runner is deliberately dull: it evaluates each registered check,
binds the result to the exact state revision it read, and returns a snapshot.
There is no ordering to tune, no threshold to set and no aggregate to compute -
every one of those would be a place for a judgement to hide.

DETERMINISM IS THE POINT. Same state, same snapshot, byte for byte. A check that
raises is reported as NOT_EVALUABLE against its own capability rather than being
allowed to take the run down or, worse, to be read as a design finding: a crashed
check has measured nothing, which is forbidden collapse C-03.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from .model import (AssuranceSnapshot, CheckResult, Finding, NOT_EVALUABLE)
from .registry import REGISTRY


def _premise_digest(state, findings: Tuple[Finding, ...]) -> str:
    """The revisions of the entities this evaluation actually read.

    Per check, not whole-state: a result stays current for as long as what it
    READ is what the design still says. `entity_revision_digest` is the lifecycle
    API S7-F added for exactly this question and says nothing about what a record
    means.
    """
    refs = sorted({r for f in findings for r in f.refs})
    revisions = {r: state.entity_revision_digest(r) for r in refs}
    return hashlib.sha256(
        json.dumps(revisions, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def run_assurance(state, only: Optional[Tuple[str, ...]] = None) -> AssuranceSnapshot:
    """Evaluate the registry over one committed state.

    NO PROVIDER, NO WRITE, NO ORDER DEPENDENCE. Checks are evaluated in registry
    order and cannot see each other's results, so nothing here can establish a
    property because something else passed.
    """
    results: List[CheckResult] = []
    for check in REGISTRY:
        if only is not None and check.check_id not in only:
            continue
        try:
            findings = tuple(check.fn(state))
        except Exception as exc:                                    # noqa: BLE001
            # A CRASHED CHECK HAS MEASURED NOTHING (C-03). It is not a finding
            # about the design and it is not a passing check either.
            findings = (Finding("%s:evaluation" % check.check_id, NOT_EVALUABLE,
                                "the check raised %s: %s"
                                % (type(exc).__name__, exc)),)
        results.append(CheckResult(check.check_id, check.independence,
                                   check.claim_class, findings,
                                   _premise_digest(state, findings)))
    return AssuranceSnapshot(state.state_hash(), tuple(results))


def declarations() -> List[Dict[str, Any]]:
    """What every registered check declares, for a report to print verbatim."""
    return [check.declaration() for check in REGISTRY]
