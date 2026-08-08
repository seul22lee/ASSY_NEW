"""DesignState, StagePatch and the stage projections.

One design world per run. A stage proposes a patch; the patch is validated
against DESIGN_STATE_CONTRACT and STAGE_OWNERSHIP_MATRIX and only then applied.
"""
from .design_state import DesignState, ContractError               # noqa: F401
from .patch import StagePatch, Op, CREATE, RECORD_UNRESOLVED       # noqa: F401
from .projection import project_for                                # noqa: F401
