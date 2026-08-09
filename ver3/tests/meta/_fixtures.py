"""Building STRUCTURALLY VALID state for tests.

Fixtures used to fill every required field with a placeholder, including declared
reference fields, so a `LoadPath.load_case` held the string "x". Nothing objected:
the write boundary decided what a reference was from the field's SPELLING, and
"x" did not look like an id. Now that the contract is the authority, a declared
reference must name a real entity - so the fixtures have to build one.

This is the fixture doing what a producer does, not the test being made lenient.
"""
from typing import Any, Dict, Optional

from ver3.assy_v3.state.patch import Op, StagePatch


class StateBuilder:
    """Mixin: `add(state, stage, family, id, **fields)` with referents supplied."""

    def _fields_for(self, s, contracts, stage, fam, over):
        out: Dict[str, Any] = {}
        for f in contracts.required_fields(fam):
            if f == "entity_id" or f in over:
                continue
            spec = contracts.reference_spec(fam, f)
            if spec is None:
                out[f] = "x"
            elif spec.get("cardinality") == "many":
                # An empty list is a VALUE: this entity names no referent.
                out[f] = []
            else:
                out[f] = self._referent(s, contracts, stage, spec.get("target"), fam)
        out.update(over)
        return out

    def _referent(self, s, contracts, stage, target: Optional[str], origin: str) -> Any:
        """A minimal standing entity of the target family, made once and reused.

        Built under the family's declared owner, because ownership is checked at
        the same boundary. A reference cycle between two families cannot be
        satisfied one entity at a time - that needs a single patch creating both,
        which is a producer's job, not a fixture's - so the chain stops and the
        test that hit it must supply the referent itself.
        """
        if not target or target == origin:
            return "x"
        existing = s.family(target)
        if existing:
            return existing[0]["entity_id"]
        building = getattr(self, "_building", None)
        if building is None:
            building = set()
            self._building = building
        if target in building:
            raise AssertionError(
                "fixture: %s and %s reference each other, so neither can be built "
                "alone; the test must create them in one patch" % (origin, target))
        building.add(target)
        try:
            owner = contracts.owner_of(target)
            at = owner if isinstance(owner, str) and owner != "any" else stage
            self.add(s, at, target, "%s-AUTO" % target[:3].upper())
        finally:
            building.discard(target)
        return "%s-AUTO" % target[:3].upper()

    def add(self, s, stage, fam, eid, prem=None, **over):
        fields = self._fields_for(s, self.c, stage, fam, over)
        s.apply(StagePatch(
            patch_id="p-%s-%d" % (eid, len(s.applied_patches)), run_id=s.run_id,
            stage_id=stage, stage_attempt=1, parent_state_hash=s.state_hash(),
            operations=[Op("CREATE", fam, eid, fields, "p",
                           premise_refs=list(prem or []))],
            execution_status="SUCCESS", provenance={"provider": "t"}))
        return eid
