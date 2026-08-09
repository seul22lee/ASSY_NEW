"""The single design world, and the contract validation that guards it."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Optional

import yaml
from weakref import WeakKeyDictionary

from .authority import (AuthorityClass, AuthorityViolation, ReadOnlyTable,
                        ValidityStatus, copy_in, copy_out)

class _Store:
    """The authoritative storage for one DesignState.

    Held in a module-private registry rather than on the state object, so it is
    not an attribute of anything a caller can reach - not even under a mangled
    name. Obtaining one requires importing this module and looking it up here,
    which is unambiguously reflection rather than an ordinary operation on an
    object you were handed.
    """

    __slots__ = ("entities", "by_family", "applied")

    def __init__(self) -> None:
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.by_family: Dict[str, List[str]] = {}
        self.applied: List[str] = []


#: DesignState -> its storage. Module-private, and the only handle on it.
_STORAGE: "WeakKeyDictionary" = WeakKeyDictionary()

#: Contracts -> its loaded documents. Same shape of fix, same reason: holding the
#: documents in an ordinary attribute made `c._docs[...] = ...` an ordinary
#: operation that changed every authorization query afterwards. The rules that
#: decide what a mutation may do must not be editable by the code being governed.
_CONTRACT_DOCS: "WeakKeyDictionary" = WeakKeyDictionary()

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONTRACTS = os.path.abspath(os.path.join(_HERE, "..", "..", "contracts"))


class ContractError(Exception):
    """A patch that violates the contract. Never a statement about the design."""


def _load(name: str) -> Dict[str, Any]:
    with open(os.path.join(_CONTRACTS, name)) as fh:
        return yaml.safe_load(fh)


class Contracts:
    """The contract files, read once, and IMMUTABLE thereafter.

    U-2B (S-2). S-1 deferred this: the loaded contract dictionaries were plain
    and nested, so ordinary repository code could do

        state.c.families[F]["extendable_fields"]["role"] = "s04"

    and change the permissions `apply()` would consult afterwards. That is not an
    authority bypass - no authoritative value changes, and every mutation still
    validates and records provenance - but the RULES used to authorize a mutation
    must not be silently editable at runtime either.

    The backing documents are held privately and every accessor returns a
    detached copy, the same shape of fix that closed the DesignState read surface:
    what a caller receives is theirs, and changing it changes nothing.
    """

    __slots__ = ("__weakref__",)

    def __init__(self) -> None:
        ds = _load("DESIGN_STATE_CONTRACT.yaml")
        families: Dict[str, Any] = dict(ds["entity_families"])
        families.update(ds["assurance_families"])
        matrix = _load("STAGE_OWNERSHIP_MATRIX.yaml")
        _CONTRACT_DOCS[self] = {
            "families": families,
            "prohibited": ds["prohibited_content"],
            "stages": matrix["stages"],
            "universally_ownable": {
                e["family"] for e in matrix["universally_ownable"] if "family" in e},
            "authority": ds.get("authority_model", {}),
        }

    def __setattr__(self, name: str, value: Any) -> None:
        raise ContractError(
            "IMMUTABLE_CONTRACT: Contracts.%s. Loaded contract semantics decide "
            "what a mutation is allowed to do; they may not be edited at runtime. "
            "Change the contract file." % name)

    @property
    def _d(self) -> Dict[str, Any]:
        raise ContractError(
            "IMMUTABLE_CONTRACT: the loaded documents are not reachable from this "
            "object. Read them through the accessors, which return detached copies.")

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    # -- read surface: every accessor hands back a detached copy ----------
    @property
    def families(self) -> Dict[str, Any]:
        return copy_out(_CONTRACT_DOCS[self]["families"])

    @property
    def prohibited(self) -> Any:
        return copy_out(_CONTRACT_DOCS[self]["prohibited"])

    @property
    def stages(self) -> Dict[str, Any]:
        return copy_out(_CONTRACT_DOCS[self]["stages"])

    @property
    def universally_ownable(self) -> set:
        return set(_CONTRACT_DOCS[self]["universally_ownable"])

    @property
    def authority(self) -> Dict[str, Any]:
        return copy_out(_CONTRACT_DOCS[self]["authority"])

    def owner_of(self, family: str) -> Optional[Any]:
        return (_CONTRACT_DOCS[self]["families"].get(family) or {}).get("owned_by")

    def required_fields(self, family: str) -> List[str]:
        return list((_CONTRACT_DOCS[self]["families"].get(family) or {}).get("required_fields", []))

    def field_semantics(self, family: str) -> Dict[str, Any]:
        """U-2B: reference targets, spatial frames and per-field authority."""
        return copy_out((_CONTRACT_DOCS[self]["families"].get(family) or {}).get("field_semantics", {}))

    # ------------------------------------------------------------- authority
    def authority_class(self, family: str) -> AuthorityClass:
        """FA-2. Declared per family; the contract's default is the strict one."""
        fam = _CONTRACT_DOCS[self]["families"].get(family) or {}
        auth = _CONTRACT_DOCS[self]["authority"]
        declared = fam.get("authority_class")
        if declared is None:
            declared = (auth.get("class_overrides", {}) or {}).get(family)
        if declared is None:
            declared = auth.get("default_class", "AUTHORITATIVE")
        return AuthorityClass(declared)

    def is_authoritative(self, family: str) -> bool:
        return self.authority_class(family) is AuthorityClass.AUTHORITATIVE

    def extendable_fields(self, family: str) -> Dict[str, str]:
        """field -> the one stage permitted to add it.

        A family with no declaration permits no extension. Before S-1, EXTEND was
        an unguarded dict.update over any field of any entity; it was never
        exercised, so nothing depends on the permissive behaviour.
        """
        return dict((_CONTRACT_DOCS[self]["families"].get(family) or {}).get("extendable_fields", {}) or {})

    def may_create(self, stage_id: str, family: str) -> bool:
        if family in _CONTRACT_DOCS[self]["universally_ownable"]:
            return True
        owner = self.owner_of(family)
        if owner == "any":
            return True
        owns = (_CONTRACT_DOCS[self]["stages"].get(stage_id) or {}).get("owns", []) or []
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
    #: INITIALIZATION-ONLY INTERNAL ROOT - the identity, written once at
    #: construction. The authoritative storage is not an attribute at all; it
    #: lives in the module-private registry above, so there is no mangled name
    #: for ordinary code to reach and nothing on this object to replace.
    _INIT_ATTRS = frozenset(("run_id", "c"))

    #: PUBLIC READ INTERFACE - properties backed by a protected root. Assigning
    #: to one is an attempt to replace the root behind it.
    _READ_INTERFACE = frozenset(("entities", "by_family", "applied_patches"))

    #: DERIVED / EPHEMERAL - nothing here yet. When a later unit needs a cache or
    #: a memoised derivation, it is declared here and is freely replaceable,
    #: because it is not authoritative.

    def __init__(self, run_id: str, contracts: Optional[Contracts] = None) -> None:
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "c", contracts or Contracts())
        _STORAGE[self] = _Store()


    def __deepcopy__(self, memo):
        """A branch of this run: the same accumulated state, separate storage.

        Exploring one candidate must not write into the state another candidate
        is exploring, and `copy.deepcopy` is how a caller says so. The default
        deepcopy copied the attributes and stopped: authoritative storage is not
        an attribute, it lives in the module-private registry, so the copy came
        back with no table at all and every read raised. Found by the first test
        to drive the runner and the producer over the same state.

        The contracts are shared, not copied - they are immutable by
        construction, and a run's rules must not fork with its state.
        """
        import copy as _copy
        twin = DesignState(self.run_id, self.c)
        memo[id(self)] = twin
        src, dst = _STORAGE[self], _STORAGE[twin]
        dst.entities = _copy.deepcopy(src.entities, memo)
        dst.by_family = _copy.deepcopy(src.by_family, memo)
        dst.applied = list(src.applied)
        return twin

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
        """A read-only SNAPSHOT of the entity table.

        Detached from storage: the returned object contains no live reference to
        anything authoritative, so there is nothing behind it to reach. For a
        membership test or a family lookup prefer `has_entity` / `stored_family`,
        which answer without building a snapshot at all.
        """
        return ReadOnlyTable(copy_out(_STORAGE[self].entities))

    def has_entity(self, entity_id: str) -> bool:
        """Membership without materialising a snapshot."""
        return entity_id in _STORAGE[self].entities

    @property
    def by_family(self) -> Dict[str, List[str]]:
        return copy_out(_STORAGE[self].by_family)

    @property
    def applied_patches(self) -> List[str]:
        return list(_STORAGE[self].applied)

    # ------------------------------------------------------------------ hash
    def state_hash(self) -> str:
        payload = json.dumps(_STORAGE[self].entities, sort_keys=True,
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
                if eid in _STORAGE[self].entities or eid in seen:
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
                if ref not in _STORAGE[self].entities and ref not in seen:
                    problems.append("DANGLING_PREMISE: %s -> %s" % (eid, ref))
        problems.extend(self._reference_problems(patch, seen))
        return problems

    # ------------------------------------------------------- U-4 operations
    def stored_family(self, entity_id: str) -> Optional[str]:
        """The family the entity actually has. The only authority on its identity."""
        rec = _STORAGE[self].entities.get(entity_id)
        return None if rec is None else rec.get("_family")

    def _family_problem(self, op) -> Optional[str]:
        """Resolve by id, then reject a declared type that is not the stored one.

        Evaluated BEFORE any ownership, extendability or field permission, so a
        permission belonging to one family can never be evaluated against an
        entity of another.
        """
        if op.entity_id not in _STORAGE[self].entities:
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
        if eid not in _STORAGE[self].entities:
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
            elif _STORAGE[self].entities[eid].get(name) is not None:
                out.append("EXTEND_OVER_EXISTING: %s.%s already has a value; "
                           "revision requires SUPERSEDE" % (eid, name))
        return out

    def _revision_problems(self, op) -> List[str]:
        out: List[str] = []
        if op.entity_id not in _STORAGE[self].entities:
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
                if name not in _STORAGE[self].entities[op.entity_id]:
                    out.append("SUPERSEDE_ABSENT: %s.%s has no prior value"
                               % (op.entity_id, name))
        return out

    def _reference_problems(self, patch, seen: set) -> List[str]:
        """Every typed reference must resolve. A free-string subject is R-20."""
        out: List[str] = []
        known = set(_STORAGE[self].entities) | seen
        for op in patch.operations:
            for key, val in op.fields.items():
                if not key.endswith(("_id", "_ids", "_refs")) and key not in (
                        "derived_from_requirements", "addresses_obligations",
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
        # The primitives live at module level and take the private storage
        # explicitly. DesignState therefore carries no second mutating method for
        # ordinary code to call: `apply` is the only way in, and reaching the
        # primitives requires the storage, which requires reflection.
        store = _STORAGE[self]
        for op in patch.operations:
            _MUTATORS[op.kind](store.entities, store.by_family, self.c, patch, op)
        _STORAGE[self].applied.append(patch.patch_id)

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
        return [copy_out(_STORAGE[self].entities[i])
                for i in _STORAGE[self].by_family.get(name, [])]

    def standing(self, name: str) -> List[Dict[str, Any]]:
        """Only the entities that still carry unqualified authority."""
        return [e for e in self.family(name)
                if e.get("_validity", ValidityStatus.STANDING.value)
                == ValidityStatus.STANDING.value]

    def counts(self) -> Dict[str, int]:
        return {k: len(v) for k, v in sorted(_STORAGE[self].by_family.items())}


# =====================================================================
# The mutation primitives.
#
# Module-private and storage-taking, deliberately. As methods they were a second
# supported write API: ordinary code holding a DesignState could call
# `state._create(patch, op)` and place an entity with no validation and no
# provenance - the exact defect S-1 exists to prevent, through a door beside the
# one that was being guarded. Single-underscore is a naming convention, and
# ordinary method invocation is a supported operation.
#
# Here they are unreachable in practice: using one requires the private storage,
# and obtaining that requires reflection, which is outside the supported
# interface. DesignState.apply() is the only supported entry.
# =====================================================================

def _log(rec: Dict[str, Any], key: str, entry: Dict[str, Any]) -> None:
    """Append to a per-entity history list."""
    rec.setdefault(key, []).append(copy_in(entry))


def _merge_premises(rec: Dict[str, Any], op) -> None:
    if op.premise_refs:
        rec["_premises"] = sorted(set(rec.get("_premises", [])) | set(op.premise_refs))


def _propagate(entities: Dict[str, Any], changed_id: str, kind: str,
               reason: Optional[str]) -> None:
    """FA-5. A dependent commitment may not silently remain authoritative.

    Computed eagerly on write, because the premise references needed to compute
    it are recorded at write time. Which propagation strategy to use is an
    implementation decision the freeze leaves open (§9); this is the one that
    needs no additional bookkeeping.
    """
    for eid, rec in entities.items():
        if eid == changed_id or changed_id not in rec.get("_premises", []):
            continue
        if rec.get("_validity") != ValidityStatus.STANDING.value:
            continue
        rec["_validity"] = ValidityStatus.STALE.value
        _log(rec, "_stale_because",
             {"premise": changed_id, "premise_change": kind, "reason": reason})


def _create(entities, by_family, contracts, patch, op) -> None:
    rec = copy_in(dict(op.fields))
    rec["entity_id"] = op.entity_id
    rec["_family"] = op.entity_type
    rec["_created_by"] = patch.stage_id
    rec["_provenance"] = op.provenance_ref
    rec["_authority"] = contracts.authority_class(op.entity_type).value
    rec["_validity"] = ValidityStatus.STANDING.value
    if op.premise_refs:
        rec["_premises"] = list(op.premise_refs)
    entities[op.entity_id] = rec
    by_family.setdefault(op.entity_type, []).append(op.entity_id)


def _extend(entities, by_family, contracts, patch, op) -> None:
    rec = entities[op.entity_id]
    for name, value in op.fields.items():
        rec[name] = copy_in(value)
    # Provenance is per act, not per entity: the creating stage and the
    # extending stage are different authors and both must remain visible.
    _log(rec, "_extensions",
         {"stage": patch.stage_id, "fields": sorted(op.fields),
          "provenance": op.provenance_ref, "premises": list(op.premise_refs)})
    _merge_premises(rec, op)


def _supersede(entities, by_family, contracts, patch, op) -> None:
    """FA-1: both values are retained. The prior value is never overwritten out
    of existence, only displaced from being current."""
    rec = entities[op.entity_id]
    for name, value in op.fields.items():
        _log(rec, "_superseded",
             {"field": name, "prior_value": copy_in(rec.get(name)),
              "stage": patch.stage_id, "reason": op.reason,
              "provenance": op.provenance_ref})
        rec[name] = copy_in(value)
    _merge_premises(rec, op)
    _propagate(entities, op.entity_id, "SUPERSEDED", op.reason)


def _invalidate(entities, by_family, contracts, patch, op) -> None:
    """The record remains readable. What it loses is unqualified authority."""
    rec = entities[op.entity_id]
    rec["_validity"] = ValidityStatus.INVALIDATED.value
    _log(rec, "_invalidations",
         {"stage": patch.stage_id, "reason": op.reason,
          "provenance": op.provenance_ref})
    _propagate(entities, op.entity_id, "INVALIDATED", op.reason)


_MUTATORS = {"CREATE": _create, "EXTEND": _extend,
             "SUPERSEDE": _supersede, "INVALIDATE": _invalidate}
