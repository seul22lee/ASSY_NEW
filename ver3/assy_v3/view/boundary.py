"""The one production boundary between accumulated state and a consuming stage.

Every consumer's engineering context comes from here. Not from a per-stage family
table, not from a projection that copies whatever state happens to hold, and not
from a second dictionary assembled beside the view.

It lives in the production package rather than in a runner because it IS the
architecture: a tool that assembles its own context is a second semantic path,
and the whole point of U-3 is that there is not one.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml

from .consumer_view import ConsumerView, InvocationContext, build_consumer_view

_CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "contracts")

#: Families whose content is source text. INV-002 and retirement row R-13: s01 is
#: the only stage that may read the request, so a later stage cannot reinterpret
#: it. This is the one genuinely non-semantic rule the retired projection carried,
#: kept here because this is now the only place a consumer's context is built.
SOURCE_TEXT_FAMILIES = ("SourceClause",)

_RESPONSIBILITY: Optional[Dict[str, Any]] = None


def responsibility_contract() -> Dict[str, Any]:
    """The stage responsibility contract, read once."""
    global _RESPONSIBILITY
    if _RESPONSIBILITY is None:
        with open(os.path.join(_CONTRACTS_DIR,
                               "STAGE_RESPONSIBILITY_CONTRACT.yaml")) as fh:
            _RESPONSIBILITY = yaml.safe_load(fh)
    return _RESPONSIBILITY


def consumer_view_for(responsibility_id: str, state,
                      budget_chars: Optional[int] = None,
                      invocation: Optional[InvocationContext] = None) -> ConsumerView:
    """What this responsibility is entitled to know, and why each item is in it.

    `budget_chars` is a SEMANTIC budget, never a character cut. Given none,
    nothing is reduced and nothing is truncated - which is the state of this
    window: no budget is configured for it, and no rendering path shortens what
    the view holds.
    """
    view = build_consumer_view(responsibility_id, state, state.c,
                               responsibility_contract(), budget_chars,
                               invocation=invocation)
    if responsibility_id != "s01":
        # BOTH CHANNELS, checked by one rule. The semantic payload is the one
        # INV-002 was written for; namespace occupancy is a second thing this
        # boundary now hands a consumer, and a rule that governs only the channel
        # it was written for is the failure S9-D closed elsewhere. Occupancy
        # carries ids and never content, so this cannot fire on today's contract -
        # only s01 may create a SourceClause, so only s01's occupancy can mention
        # one. It fires the day a contract edit changes that, which is the point:
        # the invariant should be enforced where the reach is, not where the leak
        # was first noticed.
        leaked = sorted((set(view.payload()) | set(view.occupancy))
                        & set(SOURCE_TEXT_FAMILIES))
        if leaked:
            raise AssertionError(
                "INV-002: %s would see source text %s. A stage that can reach the "
                "request can reinterpret it, which is the one thing the stage "
                "sequence exists to prevent." % (responsibility_id, leaked))
    return view
