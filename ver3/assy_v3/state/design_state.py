"""The single design world, and the contract validation that guards it."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Optional

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONTRACTS = os.path.abspath(os.path.join(_HERE, "..", "..", "contracts"))


class ContractError(Exception):
    """A patch that violates the contract. Never a statement about the design."""


def _load(name: str) -> Dict[str, Any]:
    with open(os.path.join(_CONTRACTS, name)) as fh:
        return yaml.safe_load(fh)


class Contracts:
    """The contract files, read once. The validator has no rules of its own."""

    def __init__(self) -> None:
        ds = _load("DESIGN_STATE_CONTRACT.yaml")
        self.families: Dict[str, Any] = dict(ds["entity_families"])
        self.families.update(ds["assurance_families"])
        self.prohibited = ds["prohibited_content"]
        matrix = _load("STAGE_OWNERSHIP_MATRIX.yaml")
        self.stages = matrix["stages"]
        self.universally_ownable = {
            e["family"] for e in matrix["universally_ownable"] if "family" in e}

    def owner_of(self, family: str) -> Optional[Any]:
        return self.families.get(family, {}).get("owned_by")

    def required_fields(self, family: str) -> List[str]:
        return list(self.families.get(family, {}).get("required_fields", []))

    def may_create(self, stage_id: str, family: str) -> bool:
        if family in self.universally_ownable:
            return True
        owner = self.owner_of(family)
        if owner == "any":
            return True
        owns = self.stages.get(stage_id, {}).get("owns", []) or []
        return family in owns


class DesignState:
    """Exactly one per run. Entities are addressed by stable opaque ID."""

    def __init__(self, run_id: str, contracts: Optional[Contracts] = None) -> None:
        self.run_id = run_id
        self.c = contracts or Contracts()
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.by_family: Dict[str, List[str]] = {}
        self.applied_patches: List[str] = []

    # ------------------------------------------------------------------ hash
    def state_hash(self) -> str:
        payload = json.dumps(self.entities, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()

    # ------------------------------------------------------------ validation
    def validate(self, patch) -> List[str]:
        """Every reason this patch may not be applied. Empty means it may."""
        problems: List[str] = []
        if patch.parent_state_hash != self.state_hash():
            problems.append(
                "STALE_PATCH: computed against %s, current state is %s"
                % (patch.parent_state_hash[:12], self.state_hash()[:12]))
        seen: set = set()
        for op in patch.operations:
            fam, eid = op.entity_type, op.entity_id
            if fam not in self.c.families:
                problems.append("UNKNOWN_FAMILY: %s (%s)" % (fam, eid))
                continue
            if op.kind == "CREATE":
                if not self.c.may_create(patch.stage_id, fam):
                    problems.append(
                        "OWNERSHIP: %s may not create %s (%s)" % (patch.stage_id, fam, eid))
                if eid in self.entities or eid in seen:
                    problems.append("DUPLICATE_ID: %s" % eid)
                # An empty list is a VALUE - "this clause carries no quantities",
                # "no actor participates". Only absence and empty string are missing.
                missing = [f for f in self.c.required_fields(fam)
                           if f != "entity_id"
                           and (f not in op.fields or op.fields[f] is None
                                or op.fields[f] == "")]
                if missing:
                    problems.append("MISSING_REQUIRED: %s %s -> %s" % (fam, eid, missing))
                if not op.provenance_ref:
                    problems.append("NO_PROVENANCE: %s" % eid)
                seen.add(eid)
            elif op.kind == "EXTEND":
                if eid not in self.entities:
                    problems.append("EXTEND_UNKNOWN: %s" % eid)
        problems.extend(self._reference_problems(patch, seen))
        return problems

    def _reference_problems(self, patch, seen: set) -> List[str]:
        """Every typed reference must resolve. A free-string subject is R-20."""
        out: List[str] = []
        known = set(self.entities) | seen
        for op in patch.operations:
            for key, val in op.fields.items():
                if not key.endswith(("_id", "_ids", "_refs")) and key not in (
                        "derived_from_requirements", "obligations_addressed",
                        "obligations_created", "conflicting_clauses", "blocks"):
                    continue
                for ref in (val if isinstance(val, list) else [val]):
                    if isinstance(ref, str) and ref[:4].isupper() and "-" in ref:
                        if ref not in known:
                            out.append("DANGLING_REF: %s.%s -> %s" % (op.entity_id, key, ref))
        return out

    # ----------------------------------------------------------------- apply
    def apply(self, patch) -> None:
        problems = self.validate(patch)
        if problems:
            raise ContractError("; ".join(problems))
        for op in patch.operations:
            if op.kind == "CREATE":
                rec = dict(op.fields)
                rec["entity_id"] = op.entity_id
                rec["_family"] = op.entity_type
                rec["_created_by"] = patch.stage_id
                rec["_provenance"] = op.provenance_ref
                self.entities[op.entity_id] = rec
                self.by_family.setdefault(op.entity_type, []).append(op.entity_id)
            elif op.kind == "EXTEND":
                self.entities[op.entity_id].update(op.fields)
        self.applied_patches.append(patch.patch_id)

    # ------------------------------------------------------------------ read
    def family(self, name: str) -> List[Dict[str, Any]]:
        return [self.entities[i] for i in self.by_family.get(name, [])]

    def counts(self) -> Dict[str, int]:
        return {k: len(v) for k, v in sorted(self.by_family.items())}
