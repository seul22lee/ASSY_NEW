"""DesignState and StagePatch.

One design world per run. A stage proposes a patch; the patch is validated
against DESIGN_STATE_CONTRACT and STAGE_OWNERSHIP_MATRIX and only then applied.

The stage projection is gone. It copied whatever state held into whichever stage
asked, which made it a second answer to "what may this consumer see" beside the
ConsumerView - and the two did not agree. Its one non-semantic rule, INV-002
(only s01 may read source text), moved to the consumer boundary, which is now the
only place a consumer's context is built.
"""
from .design_state import DesignState, ContractError               # noqa: F401
from .patch import StagePatch, Op, CREATE, RECORD_UNRESOLVED       # noqa: F401
