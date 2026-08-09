"""The single design world, and the contract validation that guards it."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Optional

import yaml

from .authority import (AuthorityClass, AuthorityViolation, ReadOnlyTable,
                        ValidityStatus, copy_in, copy_out)

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
        # U-2A (S-1). The authority model is declared in the contract, not here.
        self.authority = ds.get("authority_model", {})

    def owner_of(self, family: str) -> Optional[Any]:
        return self.families.get(family, {}).get("owned_by")

    def required_fields(self, family: str) -> List[str]:
        return list(self.families.get(family, {}).get("required_fields", []))

    # ------------------------------------------------------------- authority
    def authority_class(self, family: str) -> AuthorityClass:
        """FA-2. Declared per family; the contract's default is the strict one."""
        declared = (self.families.get(family, {}) or {}).get("authority_class")
        if declared is None:
            declared = (self.authority.get("class_overrides", {}) or {}).get(family)
        if declared is None:
            declared = self.authority.get("default_class", "AUTHORITATIVE")
        return AuthorityClass(declared)

    def is_authoritative(self, family: str) -> bool:
        return self.authority_class(family) is AuthorityClass.AUTHORITATIVE

    def extendable_fields(self, family: str) -> Dict[str, str]:
        """field -> the one stage permitted to add it.

        A family with no declaration permits no extension. Before S-1, EXTEND was
        an unguarded dict.update over any field of any entity; it was never
        exercised, so nothing depends on the permissive behaviour.
        """
        return dict((self.families.get(family, {}) or {}).get("extendable_fields", {}) or {})

    def may_create(self, stage_id: str, family: str) -> bool:
        if family in self.universally_ownable:
            return True
        owner = self.owner_of(family)
        if owner == "any":
            return True
        owns = self.stages.get(stage_id, {}).get("owns", []) or []
        return family in owns


class DesignState:
    """Exactly one per run. Entities are addressed by stable opaque ID.

    Authoritative storage is owned here and never leaves. Internally it is plain
    dicts and lists; every read hands back a defensive copy, and the entity table
    is exposed only through a read-only mapping.

    There is no capability object and no guarded container, because there is
    nothing outside `apply()` that needs one. A representation that hands out a
    mutable builtin as authoritative storage can always be mutated through a
    base-class call such as ``dict.__setitem__(rec, k, v)``; encapsulation
    removes the question rather than trying to police it.
    """

    #: Attributes settable through ordinary assignment AFTER construction.
    #: Deliberately empty. The storage roots were previously settable, so
    #: ``state.entities = {}`` replaced the whole authoritative table; and an
    #: engineering fact could be parked on the object as ``state.s04a_reach``.
    _SETTABLE_AFTER_INIT: frozenset = frozenset()

    #: §4 attribute taxonomy.
    #:
    #: INITIALIZATION-ONLY INTERNAL ROOT - the authoritative storage itself, and
    #: the identity written once at construction. Replacing one would discard
    #: state with no operation, provenance or history.
    _INIT_ATTRS = frozenset(("run_id", "c", "_DesignState__entities",
                             "_DesignState__by_family", "_DesignState__applied",
                             "_DesignState__ready"))

    #: PUBLIC READ INTERFACE - properties backed by a protected root. Assigning
    #: to one is an attempt to replace the root behind it.
    _READ_INTERFACE = frozenset(("entities", "by_family", "applied_patches"))

    #: DERIVED / EPHEMERAL - nothing here yet. When a later unit needs a cache or
    #: a memoised derivation, it is declared here and is freely replaceable,
    #: because it is not authoritative.

    def __init__(self, run_id: str, contracts: Optional[Contracts] = None) -> None:
        set_ = object.__setattr__
        set_(self, "_DesignState__ready", False)
        set_(self, "run_id", run_id)
        set_(self, "c", contracts or Contracts())
        set_(self, "_DesignState__entities", {})
        set_(self, "_DesignState__by_family", {})
        set_(self, "_DesignState__applied", [])
        set_(self, "_DesignState__ready", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._SETTABLE_AFTER_INIT:
            object.__setattr__(self, name, value)
            return
        if name in self._INIT_ATTRS or name in self._READ_INTERFACE:
            raise AuthorityViolation(
                "PROTECTED_ROOT: DesignState.%s is written once at construction "
                "and is not replaceable. Replacing an authoritative storage root "
                "would discard state without any operation, provenance or "
                "history (FA-1, FA-3)." % name)
        raise AuthorityViolation(
            "SIDE_CHANNEL_WRITE: DesignState.%s. An engineering fact needs an "
            "entity with an identity, an owner and provenance - not an attribute "
            "on the state object (FA-2, FA-3)." % name)

    def __delattr__(self, name: str) -> None:
        raise AuthorityViolation("PROTECTED_ROOT: DesignState.%s is not deletable." % name)

    # ------------------------------------------------------- read surface
    @property
    def entities(self):
        """Lookups only. Each record comes back as a plain copy the caller owns."""
        return ReadOnlyTable(self.__entities)

    @property
    def by_family(self) -> Dict[str, List[str]]:
        return copy_out(self.__by_family)

    @property
    def applied_patches(self) -> List[str]:
        return list(self.__applied)

    # ------------------------------------------------------------------ hash
    def state_hash(self) -> str:
        payload = json.dumps(self.__entities, sort_keys=True,
                             separators=(",", ":")).encode()
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
                if eid in self.__entities or eid in seen:
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
            elif op.kind in ("EXTEND", "SUPERSEDE", "INVALIDATE"):
                # The entity already exists, so its STORED family is the
                # authority. A caller-supplied entity_type may not be the source
                # of truth, or one family's permissions could be borrowed for
                # another's entity.
                mismatch = self._family_problem(op)
                if mismatch:
                    problems.append(mismatch)
                    continue
                if op.kind == "EXTEND":
                    problems.extend(self._extend_problems(patch, op))
                else:
                    problems.extend(self._revision_problems(op))
            # U-4. A declared premise must resolve, or the dependency it claims
            # to record is fiction and FA-5 cannot be computed from it.
            for ref in op.premise_refs:
                if ref not in self.__entities and ref not in seen:
                    problems.append("DANGLING_PREMISE: %s -> %s" % (eid, ref))
        problems.extend(self._reference_problems(patch, seen))
        return problems

    # ------------------------------------------------------- U-4 operations
    def stored_family(self, entity_id: str) -> Optional[str]:
        """The family the entity actually has. The only authority on its identity."""
        rec = self.__entities.get(entity_id)
        return None if rec is None else rec.get("_family")

    def _family_problem(self, op) -> Optional[str]:
        """Resolve by id, then reject a declared type that is not the stored one.

        Evaluated BEFORE any ownership, extendability or field permission, so a
        permission belonging to one family can never be evaluated against an
        entity of another.
        """
        if op.entity_id not in self.__entities:
            return None                     # the operation's own check reports this
        actual = self.stored_family(op.entity_id)
        if actual != op.entity_type:
            return ("FAMILY_MISMATCH: %s is a %s, not a %s; permissions of the "
                    "declared family may not be borrowed"
                    % (op.entity_id, actual, op.entity_type))
        return None

    def _extend_problems(self, patch, op) -> List[str]:
        """EXTEND is a permission, not a dict.update.

        The contract decides which stage may add which field. Adding over an
        existing value is not an extension - it is a revision, and revision has
        its own operation so that the prior value survives.
        """
        out: List[str] = []
        eid = op.entity_id
        if eid not in self.__entities:
            out.append("EXTEND_UNKNOWN: %s" % eid)
            return out
        # The STORED family, never the declared one (see _family_problem).
        fam = self.stored_family(eid)
        if not op.provenance_ref:
            out.append("NO_PROVENANCE: %s" % eid)
        permitted = self.c.extendable_fields(fam)
        for name in op.fields:
            if name not in permitted:
                out.append("EXTEND_NOT_PERMITTED: %s.%s is not an extendable field"
                           % (fam, name))
            elif permitted[name] != patch.stage_id:
                out.append("EXTEND_WRONG_STAGE: %s.%s is extendable by %s, not %s"
                           % (fam, name, permitted[name], patch.stage_id))
            elif self.__entities[eid].get(name) is not None:
                out.append("EXTEND_OVER_EXISTING: %s.%s already has a value; "
                           "revision requires SUPERSEDE" % (eid, name))
        return out

    def _revision_problems(self, op) -> List[str]:
        out: List[str] = []
        if op.entity_id not in self.__entities:
            out.append("%s_UNKNOWN: %s" % (op.kind, op.entity_id))
            return out
        if not op.provenance_ref:
            out.append("NO_PROVENANCE: %s" % op.entity_id)
        if not op.reason:
            out.append("NO_REASON: %s may not be silent (%s)" % (op.kind, op.entity_id))
        if op.kind == "SUPERSEDE":
            if not op.fields:
                out.append("SUPERSEDE_EMPTY: %s names no field" % op.entity_id)
            for name in op.fields:
                if name not in self.__entities[op.entity_id]:
                    out.append("SUPERSEDE_ABSENT: %s.%s has no prior value"
                               % (op.entity_id, name))
        return out

    def _reference_problems(self, patch, seen: set) -> List[str]:
        """Every typed reference must resolve. A free-string subject is R-20."""
        out: List[str] = []
        known = set(self.__entities) | seen
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
        """The controlled mutation boundary. The only way class-A state changes.

        Every value that enters is copied in, so state never holds an object a
        caller still has a reference to; every value that leaves is copied out,
        so no reader ever holds an object that state uses.
        """
        problems = self.validate(patch)
        if problems:
            raise ContractError("; ".join(problems))
        for op in patch.operations:
            if op.kind == "CREATE":
                self._create(patch, op)
            elif op.kind == "EXTEND":
                self._extend(patch, op)
            elif op.kind == "SUPERSEDE":
                self._supersede(patch, op)
            elif op.kind == "INVALIDATE":
                self._invalidate(patch, op)
        self.__applied.append(patch.patch_id)

    def _log(self, rec, key: str, entry: Dict[str, Any]) -> None:
        """Append to a per-entity history list."""
        rec.setdefault(key, []).append(copy_in(entry))

    def _create(self, patch, op) -> None:
        rec = copy_in(dict(op.fields))
        rec["entity_id"] = op.entity_id
        rec["_family"] = op.entity_type
        rec["_created_by"] = patch.stage_id
        rec["_provenance"] = op.provenance_ref
        rec["_authority"] = self.c.authority_class(op.entity_type).value
        rec["_validity"] = ValidityStatus.STANDING.value
        if op.premise_refs:
            rec["_premises"] = list(op.premise_refs)
        self.__entities[op.entity_id] = rec
        self.__by_family.setdefault(op.entity_type, []).append(op.entity_id)

    def _extend(self, patch, op) -> None:
        rec = self.__entities[op.entity_id]
        for name, value in op.fields.items():
            rec[name] = copy_in(value)
        # Provenance is per act, not per entity: the creating stage and the
        # extending stage are different authors and both must remain visible.
        self._log(rec, "_extensions",
                  {"stage": patch.stage_id, "fields": sorted(op.fields),
                   "provenance": op.provenance_ref,
                   "premises": list(op.premise_refs)})
        self._merge_premises(rec, op)

    def _supersede(self, patch, op) -> None:
        """FA-1: both values are retained. The prior value is never overwritten
        out of existence, only displaced from being current."""
        rec = self.__entities[op.entity_id]
        for name, value in op.fields.items():
            # The prior value is already wrapped, so the retained history is as
            # alias-safe as the current value.
            self._log(rec, "_superseded",
                      {"field": name, "prior_value": rec.get(name),
                       "stage": patch.stage_id, "reason": op.reason,
                       "provenance": op.provenance_ref})
            rec[name] = copy_in(value)
        self._merge_premises(rec, op)
        self._propagate(op.entity_id, "SUPERSEDED", op.reason)

    def _invalidate(self, patch, op) -> None:
        """The record remains readable. What it loses is unqualified authority."""
        rec = self.__entities[op.entity_id]
        rec["_validity"] = ValidityStatus.INVALIDATED.value
        self._log(rec, "_invalidations",
                  {"stage": patch.stage_id, "reason": op.reason,
                   "provenance": op.provenance_ref})
        self._propagate(op.entity_id, "INVALIDATED", op.reason)

    def _merge_premises(self, rec, op) -> None:
        if op.premise_refs:
            rec["_premises"] = sorted(
                set(rec.get("_premises", [])) | set(op.premise_refs))

    # ------------------------------------------------------- M-5A propagation
    def _propagate(self, changed_id: str, kind: str, reason: Optional[str]) -> None:
        """FA-5. A dependent commitment may not silently remain authoritative.

        Computed eagerly on write, because the premise references needed to
        compute it are recorded at write time. Which propagation strategy to use
        is an implementation decision the freeze leaves open (§9); this is the
        one that needs no additional bookkeeping.
        """
        for eid, rec in self.__entities.items():
            if eid == changed_id or changed_id not in rec.get("_premises", []):
                continue
            if rec.get("_validity") != ValidityStatus.STANDING.value:
                continue
            rec["_validity"] = ValidityStatus.STALE.value
            self._log(rec, "_stale_because",
                      {"premise": changed_id, "premise_change": kind,
                       "reason": reason})

    # ------------------------------------------------------------------ read
    def family(self, name: str) -> List[Dict[str, Any]]:
        """Every entity of the family, whatever its validity.

        Nothing is hidden (FA-1). A caller that needs only currently
        authoritative values asks for them; a caller that needs the whole record,
        including what was superseded, gets it.

        Each record is a plain copy the caller owns. Mutating it is ordinary and
        has no effect on state - the same semantics as ``dict.copy()``. The read
        API is not a write API.
        """
        return [copy_out(self.__entities[i])
                for i in self.__by_family.get(name, [])]

    def standing(self, name: str) -> List[Dict[str, Any]]:
        """Only the entities that still carry unqualified authority."""
        return [e for e in self.family(name)
                if e.get("_validity", ValidityStatus.STANDING.value)
                == ValidityStatus.STANDING.value]

    def counts(self) -> Dict[str, int]:
        return {k: len(v) for k, v in sorted(self.__by_family.items())}
