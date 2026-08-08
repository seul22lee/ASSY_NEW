"""The only way DesignState changes."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

CREATE = "CREATE"
EXTEND = "EXTEND"
RELATE = "RELATE"
RECORD_UNRESOLVED = "RECORD_UNRESOLVED"
RECORD_REJECTED = "RECORD_REJECTED"

OP_KINDS = (CREATE, EXTEND, RELATE, RECORD_UNRESOLVED, RECORD_REJECTED)


@dataclass(frozen=True)
class Op:
    kind: str
    entity_type: str
    entity_id: str
    fields: Dict[str, Any] = field(default_factory=dict)
    provenance_ref: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind not in OP_KINDS:
            raise ValueError("unknown operation kind %r" % self.kind)


@dataclass
class StagePatch:
    """A stage's proposal. Carries the status of the work that produced it."""

    patch_id: str
    run_id: str
    stage_id: str
    stage_attempt: int
    parent_state_hash: str
    operations: List[Op]
    execution_status: str
    provenance: Dict[str, Any]
    declared_incompleteness: List[str] = field(default_factory=list)
    #: For each changed entity, what depends on it. Computed when the change is
    #: made, not when a consequence surfaces. Empty for a creating stage.
    invalidation_cone: Dict[str, List[str]] = field(default_factory=dict)

    def digest(self) -> str:
        payload = json.dumps(
            {"stage": self.stage_id, "attempt": self.stage_attempt,
             "ops": [[o.kind, o.entity_type, o.entity_id] for o in self.operations]},
            sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()
