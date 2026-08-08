"""What each stage is allowed to read.

INV-002 and retirement row R-13: s01 is the only stage that may see source text.
The projection ENFORCES that rather than asking stages to be well behaved -
a stage that cannot reach the request cannot re-interpret it.
"""
from __future__ import annotations

from typing import Any, Dict, List

#: Families whose content is source text. Never projected at or after s02.
SOURCE_TEXT_FAMILIES = ("SourceClause",)


def project_for(stage_id: str, state) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for family, ids in state.by_family.items():
        if stage_id != "s01" and family in SOURCE_TEXT_FAMILIES:
            continue
        out[family] = [dict(state.entities[i]) for i in ids]
    return out
