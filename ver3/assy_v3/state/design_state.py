"""The single design world, and the contract validation that guards it."""
from __future__ import annotations

import hashlib
import json
import os
import re
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
        # STAGES AND RESPONSIBILITIES. Ownership is the question the write
        # boundary asks, and a responsibility owns families exactly as a stage
        # does - `gate` did, and had no entry here at all, which is how
        # SelectionDecision came to be listed under s04. Merged at load so
        # `may_create` asks one thing and there is no second ownership table.
        owners = dict(matrix["stages"])
        owners.update((matrix.get("responsibilities") or {}).get("entries") or {})
        _CONTRACT_DOCS[self] = {
            "families": families,
            "prohibited": ds["prohibited_content"],
            "stages": owners,
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

    def conditional_requirements(self, family: str) -> List[Dict[str, Any]]:
        """Rules that apply only to SOME records of a family.

        A family's `required_fields` are the ones every record must carry. Some
        requirements are narrower than that: a Joint needs travel and actuation
        only when it is COMPLIANT, and a ReferenceScale needs a structured
        `absolute` only when its basis is ABSOLUTE. Declaring those as required
        outright would reject every ordinary record of the family.

        They were previously written as prose beside the family. Prose is not
        consumed by the write boundary, so the rule existed and was not enforced
        - which is worse than not having it, because the contract said it held.
        """
        return copy_out((_CONTRACT_DOCS[self]["families"].get(family) or {})
                        .get("conditional_requirements", []))

    def relational_invariants(self, family: str) -> List[Dict[str, Any]]:
        """Canonical rules about a record's RELATIONS, not its own fields.

        `conditional_requirements` can say "a COMPLIANT joint must carry a
        required_travel", because that is a fact about the record in hand. It
        cannot say "the two groups it names must belong to the same body", or
        "at most one of these may stand at a time" - both need other entities.

        Declared by name and dispatched to `RELATIONAL_INVARIANTS`, the same
        shape the ConsumerView uses for applicability rules. A name with no
        implementation, or an implementation nothing declares, is a defect and
        both are checked - so an invariant cannot exist as prose alone, which is
        how the compliant-joint rule sat unenforced for as long as it did.
        """
        return copy_out((_CONTRACT_DOCS[self]["families"].get(family) or {})
                        .get("relational_invariants", []))

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

    def reference_spec(self, family: Optional[str], field: str) -> Optional[Dict[str, Any]]:
        """The declaration that makes a field a reference, or None.

        The ONE place that answers "is this a reference, and to what". Both the
        write boundary and the consumer boundary ask it, so they cannot disagree.
        """
        if not family:
            return None
        fam = (_CONTRACT_DOCS[self]["families"].get(family) or {})
        spec = ((fam.get("field_semantics") or {}).get(field))
        if isinstance(spec, dict) and spec.get("kind") == "reference":
            return copy_out(spec)
        return None

    def premise_record_spec(self, family: Optional[str],
                            field: str) -> Optional[Dict[str, Any]]:
        """The declaration that makes a field a list of premise-bearing records.

        Same role as `reference_spec` one level down: the ONE place that answers
        "do these records have to name their evidence, of what kind, and to what
        family". A premise nested inside a list used to be unreachable by any
        boundary, so a contract could require one and nothing could tell whether
        it was there.
        """
        if not family:
            return None
        fam = (_CONTRACT_DOCS[self]["families"].get(family) or {})
        spec = ((fam.get("field_semantics") or {}).get(field))
        if isinstance(spec, dict) and spec.get("kind") == "premise_record_list":
            return copy_out(spec)
        return None

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
                # A CREATE's prospective record IS its fields; the shared
                # helper is used anyway so CREATE is not a special case in the
                # architecture, only in what the record happens to be.
                problems.extend(_conditional_problems(self.c, fam, eid, op.fields))
                problems.extend(_relational_problems(self, fam, eid, op.fields,
                                                     patch, op))
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
                    mutation = self._extend_problems(patch, op)
                else:
                    mutation = self._revision_problems(patch, op)
                problems.extend(mutation)
                # AUTHORITY FIRST, then the invariant. An illegal mutation is
                # rejected for being illegal and is never re-examined for shape:
                # reporting "your unauthorised write would also be malformed"
                # invites making it well-formed rather than authorised.
                #
                # INVALIDATE is deliberately excluded. It withdraws standing
                # rather than changing engineering fields, so there is no new
                # record to hold to an invariant - and revalidating the shape of
                # something being withdrawn would make a record impossible to
                # retire once the rules around it moved.
                if not mutation and op.kind in ("EXTEND", "SUPERSEDE"):
                    record = _prospective_record(self, op)
                    stored_fam = self.stored_family(op.entity_id)
                    problems.extend(_conditional_problems(
                        self.c, stored_fam, op.entity_id, record))
                    problems.extend(_relational_problems(
                        self, stored_fam, op.entity_id, record, patch, op))
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

    def _revision_problems(self, patch, op) -> List[str]:
        """SUPERSEDE and INVALIDATE, including WHO is entitled to do it.

        THE GAP THIS CLOSES. This method used to take only `op`, so it could not
        see `patch.stage_id` even in principle - and so a supersession was checked
        for evidence (provenance, reason, a prior value) and never for authority.
        Any stage could rewrite any field of any entity: s01 could change the
        symbol of an s05-owned Parameter, and nothing objected.

        EXTEND has always been gated by exactly the same question, which is what
        makes the asymmetry a defect rather than a design. The contracts define
        SUPERSEDE's effect and its evidence requirements and never say who may
        perform one, so the rule is derived from the authority the runtime already
        enforces elsewhere:

            the family's OWNER may revise what it authored, and
            a stage granted a field through `extendable_fields` may revise THAT
            field - having been trusted to write it in the first place.

        INVALIDATE names no field. It withdraws standing rather than replacing a
        value, it is how lifecycle coordination retires an entity across
        families, and gating it on family ownership would be a different rule
        about a different operation. It is deliberately left alone here.
        """
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
            fam = self.stored_family(op.entity_id)
            owner = self.c.owner_of(fam)
            extendable = self.c.extendable_fields(fam)
            for name in op.fields:
                if name not in _STORAGE[self].entities[op.entity_id]:
                    out.append("SUPERSEDE_ABSENT: %s.%s has no prior value"
                               % (op.entity_id, name))
                    continue
                # A DELEGATED FIELD BELONGS TO ITS DELEGATE, NOT TO THE OWNER.
                # Checked before ownership on purpose: `Parameter` is owned by
                # s05, and if ownership were tested first s05 could supersede
                # `value` - the one thing S05-C10 exists to prevent. Granting a
                # field away is giving it away.
                granted = extendable.get(name)
                if granted is not None:
                    if granted != patch.stage_id:
                        out.append(
                            "SUPERSEDE_WRONG_STAGE: %s.%s is writable by %s, not "
                            "%s" % (fam, name, granted, patch.stage_id))
                    continue
                if owner != patch.stage_id:
                    out.append(
                        "SUPERSEDE_NOT_PERMITTED: %s.%s is owned by %s and is not "
                        "extendable, so %s may not revise it"
                        % (fam, name, owner, patch.stage_id))
        return out

    def _reference_problems(self, patch, seen: set) -> List[str]:
        """Every DECLARED typed reference must resolve, to the declared family.

        The contract is the authority. This used to decide what a reference was
        from the SPELLING of the field - anything ending `_id`, `_ids`, `_refs`,
        plus a hand-kept list of names that did not - and from the SHAPE of the
        value. That made two reference authorities in one system: the write
        boundary believed field names, the consumer boundary believed
        `field_semantics`, and a canonical reference the naming convention did not
        cover was enforced by neither.

        `seen` carries the ids created earlier in THIS patch, so a patch that
        creates a candidate and the obligation it addresses validates as one act.
        Same-patch closure is a write-boundary property, which is why it is
        checked here and not by any consumer.

        Two checks, and they are not the same question.

        STRUCTURE. A typed reference holds an ENTITY ID. `identity.entity_id`
        declares the format and `references.rule` is explicit: "a free-string
        subject is a SCHEMA ERROR, not a warning" (R-20). Prose in a reference
        field is invalid whatever the referent's fate - there is no entity it
        could ever denote. This is checked for every declared reference.

        EXISTENCE. Whether the named entity must already resolve is per field:
        `field_semantics_rules.reference` says "`resolvable` says whether an
        unresolved value is legal; the default is false, so a dangling reference
        is a defect rather than a style". So `resolvable: false` - the default,
        and 40 of the 46 declarations - REQUIRES resolution, and the six that say
        true tolerate an unresolved id.

        `seen` carries the ids created earlier in THIS patch, so a patch creating
        a candidate and the obligation it addresses validates as one act.
        Same-patch closure is a write-boundary property, which is why it is
        checked here and not by any consumer.
        """
        out: List[str] = []
        known = set(_STORAGE[self].entities) | seen
        for op in patch.operations:
            family = op.entity_type if op.kind == "CREATE" else self.stored_family(op.entity_id)
            for key, val in op.fields.items():
                spec = self.c.reference_spec(family, key)
                if spec is not None:
                    out += self._one_reference(patch, seen, known, spec, val,
                                               "%s.%s" % (op.entity_id, key))
                    continue
                record = self.c.premise_record_spec(family, key)
                if record is not None:
                    out += self._premise_records(patch, seen, known, record, val,
                                                 op.entity_id, key)
        return out

    def _one_reference(self, patch, seen, known, spec, val, label) -> List[str]:
        """One declared reference, wherever in the record it sits.

        Shared by the flat and the nested walk deliberately: two copies of this
        rule would be two answers to "does a reference resolve", which is the
        divergence `reference_spec` was made the single authority to end.
        """
        out: List[str] = []
        refs = val if isinstance(val, list) else [val]
        if spec.get("cardinality") == "one" and isinstance(val, list) and len(val) > 1:
            out.append("CARDINALITY: %s declares one referent and names %d"
                       % (label, len(val)))
        for ref in refs:
            if not isinstance(ref, str) or not ref:
                out.append("REFERENCE_NOT_AN_ID: %s holds %r" % (label, ref))
                continue
            if not _ENTITY_ID.match(ref):
                out.append("REFERENCE_NOT_AN_ID: %s holds %r, which is not an "
                           "entity id (R-20)" % (label, ref[:60]))
                continue
            if ref not in known:
                if not spec.get("resolvable"):
                    out.append("DANGLING_REF: %s -> %s" % (label, ref))
                continue
            target = spec.get("target")
            actual = (_created_family(patch, ref) if ref in seen
                      and ref not in _STORAGE[self].entities
                      else self.stored_family(ref))
            if target and actual and actual != target:
                out.append("REFERENCE_FAMILY: %s declares %s and names %s, a %s"
                           % (label, target, ref, actual))
        return out

    def _premise_records(self, patch, seen, known, record, val, eid, key) -> List[str]:
        """Every record in a premise-bearing list names evidence of the right kind.

        FA-4 and FA-8, made checkable at the boundary rather than trusted to the
        producer. Three separate questions, and a record has to pass all three:

        KIND. The discriminator value is one the contract declares. An
        unrecognised assertion is not a lenient case; nothing downstream knows
        what it means.

        PRESENCE. The premise field that kind requires is there. A kind mapped to
        null is an explicit statement that there is no evidence - UNDISPOSITIONED
        says exactly that - and it is the only way to hold no premise legally.

        TYPE. A record may not carry ANOTHER kind's premise field. Otherwise
        "cite a Joint" is satisfiable by citing a ConstraintRelation and the
        declaration stops being a type at all.

        Then each declared reference resolves by the ordinary rule.
        """
        out: List[str] = []
        premise_field = record.get("premise_field") or {}
        specs = record.get("record_field_semantics") or {}
        discriminator = record.get("discriminator")
        rows = val if isinstance(val, list) else [val]
        for i, row in enumerate(rows):
            label = "%s.%s[%d]" % (eid, key, i)
            if not isinstance(row, dict):
                out.append("PREMISE_RECORD_MALFORMED: %s holds %r" % (label, row))
                continue
            kind = row.get(discriminator)
            if kind not in premise_field:
                out.append("PREMISE_KIND_UNKNOWN: %s says %s is %r"
                           % (label, discriminator, kind))
                continue
            required = premise_field[kind]
            if required and not row.get(required):
                out.append("PREMISE_MISSING: %s is %s and names no %s"
                           % (label, kind, required))
            for other, field in premise_field.items():
                if field and other != kind and row.get(field):
                    out.append("PREMISE_WRONG_KIND: %s is %s and carries %s, "
                               "which is %s's premise" % (label, kind, field, other))
            for fld, spec in specs.items():
                if spec.get("kind") == "reference" and row.get(fld) is not None:
                    out += self._one_reference(patch, seen, known, spec,
                                               row[fld], "%s.%s" % (label, fld))
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

    def entity_revision_digest(self, entity_id: str) -> Optional[str]:
        """WHICH VERSION of this entity is current, as an opaque string.

        S7-F. A LIFECYCLE API, NOT AN ENGINEERING ONE. It answers one question -
        "is this the same record I evaluated last time?" - and it answers it
        without saying anything about what the record means. Engineering fields
        are still read exclusively through the ConsumerView; a reconciler that
        read values here would be a second channel, which is the thing the view
        exists to remove.

        Over the authored content and the validity, so an entity that gained a
        field, had one superseded, or stopped being current is a different
        revision under the same id. Not over the whole state: one candidate's
        envelope moving must not change another candidate's evaluation basis.
        """
        rec = _STORAGE[self].entities.get(entity_id)
        if rec is None:
            return None
        content = {k: v for k, v in rec.items()
                   if not k.startswith("_") or k == "_validity"}
        return hashlib.sha256(json.dumps(content, sort_keys=True, default=str,
                                         separators=(",", ":")).encode()).hexdigest()


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

def _authority_of(stage_id: Optional[str]) -> Optional[str]:
    """The owner a pass writes as. `s03b` is s03's; `selection_advisory` writes
    as `selection` already. The same reading `consumer_view` does, and no table
    of which pass belongs to which owner."""
    if not stage_id:
        return None
    return stage_id[:-1] if re.match(r"^s\d+[a-z]$", stage_id) else stage_id


def skip_ids(patch) -> List[str]:
    """The entities this patch creates. They are co-authored with everything
    else it does and are never staled by it."""
    return [op.entity_id for op in patch.operations if op.kind == "CREATE"]


def _log(rec: Dict[str, Any], key: str, entry: Dict[str, Any]) -> None:
    """Append to a per-entity history list."""
    rec.setdefault(key, []).append(copy_in(entry))


def _merge_premises(rec: Dict[str, Any], op) -> None:
    if op.premise_refs:
        rec["_premises"] = sorted(set(rec.get("_premises", [])) | set(op.premise_refs))


def _dependents(entities: Dict[str, Any]) -> Dict[str, List[str]]:
    """premise id -> the entities that named it. Built per propagation.

    Deterministic order, because a traversal whose shape depends on dictionary
    iteration is a traversal nobody can reproduce from the record.
    """
    out: Dict[str, List[str]] = {}
    for eid in sorted(entities):
        for premise in entities[eid].get("_premises", []) or []:
            out.setdefault(premise, []).append(eid)
    return out


def _propagate(entities: Dict[str, Any], changed_id: str, kind: str,
               reason: Optional[str], skip=()) -> None:
    """FA-5, TRANSITIVELY. A dependent commitment may not silently remain
    authoritative - and neither may a commitment that depends on one.

    S7-F. This walked ONE HOP until now, which made correctness depend on every
    producer copying the whole raw premise closure into every output: a
    comparison premised on the assessments would have stayed standing when an
    envelope the assessment read was superseded, because the assessment went
    STALE and the walk stopped there. Redundant raw premises hid the gap rather
    than closing it, and no producer can be relied on to remember forever.

    Currentness is a property of the graph, so the graph is what is walked:
    breadth-first from the changed entity, a visited set so a cycle terminates
    and a diamond is visited once, and every entity recording BOTH the premise
    that reached it and the change at the root of the walk. One transition to
    STALE per entity, however many paths arrive at it.

    `skip` is the set of entities created by the very patch making this change.
    A patch's own outputs are CO-AUTHORED with it, exactly as a co-produced
    reference is at the view boundary; staling them would have the writer
    invalidate its own work in the act of doing it.
    """
    dependents = _dependents(entities)
    seen = {changed_id}
    frontier, hops = [changed_id], 0
    while frontier:
        hops += 1
        nxt: List[str] = []
        for premise in frontier:
            for eid in dependents.get(premise, ()):
                if eid in seen or eid in skip:
                    continue
                seen.add(eid)
                rec = entities.get(eid)
                if rec is None or rec.get("_validity") != ValidityStatus.STANDING.value:
                    # Already not current. Its own dependents were reached when
                    # it stopped being current, so the walk does not continue
                    # through it and nothing is logged twice.
                    continue
                rec["_validity"] = ValidityStatus.STALE.value
                _log(rec, "_stale_because",
                     {"premise": premise, "premise_change": kind,
                      "reason": reason, "root": changed_id, "hops": hops})
                nxt.append(eid)
        frontier = nxt


#: `identity.entity_id.format`: "<type_prefix>-<zero_padded_ordinal>". Ids are
#: opaque and nothing may branch on the ordinal - this only asks whether a value
#: is an id at all, which is what R-20 makes a schema error rather than a warning.
_ENTITY_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Za-z0-9]+)+$")


def _created_family(patch, entity_id: str) -> Optional[str]:
    """The family a not-yet-applied CREATE in this patch will give an id."""
    for op in patch.operations:
        if op.kind == "CREATE" and op.entity_id == entity_id:
            return op.entity_type
    return None


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
    # S7-F. AN EXTENSION IS AN AUTHORITATIVE CHANGE, so it propagates like one -
    # but not to the owner's own passes.
    #
    # `_extend_problems` already restricts EXTEND to a field the contract
    # DECLARES extendable, by exactly the stage the contract names, and only
    # where no value exists: changing an authored value is a SUPERSEDE and
    # always was. So an extension is the OWNER'S RECORD BEING COMPLETED BY THE
    # STAGE THE CONTRACT SAID WOULD COMPLETE IT - s03 authors a Joint and s04
    # places it - and the owner's other passes were never entitled to that field.
    # Staling them would make the pipeline unable to finish one design: s03b's
    # DOF grid would be withdrawn the moment s04a placed the joint it was
    # derived from, and no deterministic step could restore it.
    #
    # What DOES lose authority is a conclusion drawn from OUTSIDE the owner. A
    # feasibility verdict about a region that has since gained its volume was
    # decided over a record that no longer says what it said.
    owner = contracts.owner_of(rec.get("_family"))
    _propagate(entities, op.entity_id, "EXTENDED",
               "%s gained %s" % (op.entity_id, ", ".join(sorted(op.fields))),
               skip=set(skip_ids(patch)) | {
                   eid for eid, other in entities.items()
                   if _authority_of(other.get("_created_by")) == owner})


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
    _propagate(entities, op.entity_id, "SUPERSEDED", op.reason,
               skip=set(skip_ids(patch)))


# ==========================================================================
# CONDITIONAL CONTRACT REQUIREMENTS
# ==========================================================================
#
# Deliberately a SMALL vocabulary, not a schema language. Each checker below
# exists because a canonical rule needed it, and a rule that needs a construct
# not listed here should get one added with the same justification - not be
# expressed by making this general enough to say anything.
#
#   applies_when             {field, equals}      which records the rule governs
#   additional_required_fields                    fields those records must carry
#   required_shape           per field:
#       mapping                                   must be a mapping
#       required_keys                             keys it must contain
#       non_empty_string                          keys whose value is real text
#       positive_finite_number                    keys whose value is a usable
#                                                 number - not a string, not a
#                                                 range, not zero, not infinite

def _is_number(value) -> bool:
    # bool is an int in Python, and True is not a scale factor.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _shape_problems(rule_name, family, eid, field, value, shape) -> List[str]:
    out: List[str] = []
    where = "%s %s.%s" % (family, eid, field)
    if shape.get("mapping") and not isinstance(value, dict):
        return ["CONDITIONAL_SHAPE (%s): %s must be a mapping, got %r"
                % (rule_name, where, type(value).__name__)]
    if not isinstance(value, dict):
        return out
    for key in shape.get("required_keys") or []:
        if key not in value:
            out.append("CONDITIONAL_SHAPE (%s): %s is missing %r"
                       % (rule_name, where, key))
    for key in shape.get("non_empty_string") or []:
        got = value.get(key)
        if key in value and not (isinstance(got, str) and got.strip()):
            out.append("CONDITIONAL_SHAPE (%s): %s.%s must be a non-empty "
                       "string, got %r" % (rule_name, where, key, got))
    for key in shape.get("positive_finite_number") or []:
        got = value.get(key)
        if key not in value:
            continue
        if not _is_number(got):
            out.append("CONDITIONAL_SHAPE (%s): %s.%s must be a number, got %r"
                       % (rule_name, where, key, got))
        elif got != got or got in (float("inf"), float("-inf")):
            out.append("CONDITIONAL_SHAPE (%s): %s.%s must be finite, got %r"
                       % (rule_name, where, key, got))
        elif got <= 0:
            out.append("CONDITIONAL_SHAPE (%s): %s.%s must be positive, got %r"
                       % (rule_name, where, key, got))
    return out


def _prospective_record(state, op) -> Dict[str, Any]:
    """The record this operation would LEAVE BEHIND, not the operation's fields.

    A canonical invariant is a property of the design's state, not of the event
    that produced it. Validating `op.fields` alone answered "is this write
    well-formed on its own", which for a mutation is the wrong question: an
    EXTEND carrying one field is always well-formed on its own, and can still
    leave a record that violates a rule about the whole of it.

    Stored fields first, the operation's on top. Private bookkeeping keys are
    left out - they are not engineering fields and no contract rule speaks about
    them.
    """
    stored = _STORAGE[state].entities.get(op.entity_id) or {}
    record = {k: v for k, v in stored.items() if not k.startswith("_")}
    record.update(op.fields or {})
    return record


# ==========================================================================
# RELATIONAL INVARIANTS
# ==========================================================================
#
# Declared per family by NAME and dispatched here, the same shape the
# ConsumerView uses for applicability rules. Deliberately a registry rather than
# a rule language: each of these needs to read other entities, and a expression
# syntax general enough to express "resolve two references and compare a field
# of each" would be a query language nobody asked for.
#
# The meta guard in the test suite asserts the declaration and the registry
# agree in both directions, so an invariant cannot exist as prose alone and an
# implementation cannot sit unreferenced.

def _same_body_rigid_groups(state, family, eid, record, patch, op, rule):
    """A COMPLIANT Joint relates two RigidGroups of ONE Body.

    DESIGN_STATE_CONTRACT states it directly: "Compliance is a joint_type of
    Joint between RigidGroups of one body (proposal D-2)." It was prose, so a
    cross-body joint wearing the label became standing state and was only
    noticed - if at all - when S05-C1 read it much later and treated it as
    grounds for omitting geometry.

    Resolved through the declared typed references, never by comparing names.
    """
    trigger = rule.get("applies_when") or {}
    actual = record.get(trigger.get("field"))
    expected = trigger.get("equals")
    if not (isinstance(actual, str) and isinstance(expected, str)
            and actual.strip().upper() == expected.strip().upper()):
        return []

    entities = _STORAGE[state].entities
    bodies, unresolved = {}, []
    for field in rule.get("reference_fields") or []:
        ref = record.get(field)
        target = entities.get(ref) if isinstance(ref, str) else None
        if target is None:
            unresolved.append("%s=%r" % (field, ref))
            continue
        bodies[field] = target.get(rule.get("compare_field"))
    if unresolved:
        # Not this invariant's failure to report: an unresolvable reference is
        # already a reference problem, and saying it twice helps nobody.
        return []
    distinct = {b for b in bodies.values() if b is not None}
    if len(distinct) > 1:
        return ["RELATIONAL (%s): %s %s declares %s=%s and relates groups on "
                "different bodies (%s); this relation holds between groups of "
                "ONE body"
                % (rule.get("name"), family, eid, trigger.get("field"), actual,
                   ", ".join("%s->%s" % (k, v) for k, v in sorted(bodies.items())))]
    return []


def _at_most_one_standing(state, family, eid, record, patch, op, rule):
    """At most one record of this family may stand at a time.

    For SelectionDecision this is what makes selection an AUTHORITY rather than
    an opinion. Two standing decisions were reachable through ordinary writes,
    and `committed_branch` then returned whichever the iteration reached first -
    so the whole downstream silently followed one of two contradictory choices,
    with nothing recording that the other existed.

    Rejected at the boundary rather than resolved by consumers. Changing a
    decision has a canonical path that keeps the history: SUPERSEDE the standing
    one, or INVALIDATE it and record a new one. What is refused is a second
    decision standing BESIDE the first.
    """
    if op.kind != "CREATE":
        return []                     # revising the standing one is the path
    others = [r["entity_id"] for r in state.standing(family)
              if r["entity_id"] != eid]
    if others:
        return ["RELATIONAL (%s): %s %s would stand beside %s; at most one %s "
                "may stand at a time. Supersede or invalidate the standing one "
                "first - a second record does not replace it, it contradicts it"
                % (rule.get("name"), family, eid, ", ".join(sorted(others)),
                   family)]
    return []


RELATIONAL_INVARIANTS: Dict[str, Any] = {
    "same_body_rigid_groups": _same_body_rigid_groups,
    "at_most_one_standing": _at_most_one_standing,
}


def _relational_problems(state, family, eid, record, patch, op) -> List[str]:
    """Every declared relational invariant this record must satisfy."""
    out: List[str] = []
    for rule in state.c.relational_invariants(family):
        name = rule.get("rule")
        fn = RELATIONAL_INVARIANTS.get(name)
        if fn is None:
            # Fails CLOSED. A declared invariant with no implementation is a
            # rule the contract asserts and the runtime cannot keep, which is
            # the exact drift this mechanism exists to prevent.
            out.append("RELATIONAL_UNIMPLEMENTED: %s declares invariant %r and "
                       "no implementation is registered" % (family, name))
            continue
        out.extend(fn(state, family, eid, record, patch, op, rule))
    return out


def _conditional_problems(contracts, family, eid, fields) -> List[str]:
    """Every declared conditional rule this record triggers, and what it broke."""
    out: List[str] = []
    for rule in contracts.conditional_requirements(family):
        name = rule.get("name") or "unnamed"
        when = rule.get("applies_when") or {}
        field, expected = when.get("field"), when.get("equals")
        if field is None:
            continue
        actual = fields.get(field)
        if not (isinstance(actual, str) and isinstance(expected, str)
                and actual.strip().upper() == expected.strip().upper()):
            continue                     # the rule does not govern this record
        for required in rule.get("additional_required_fields") or []:
            value = fields.get(required)
            if required not in fields or value is None or value == "":
                out.append("CONDITIONAL_REQUIRED (%s): %s %s declares %s=%s and "
                           "must carry %r"
                           % (name, family, eid, field, actual, required))
        for shaped, shape in (rule.get("required_shape") or {}).items():
            if shaped in fields and fields[shaped] is not None:
                out.extend(_shape_problems(name, family, eid, shaped,
                                           fields[shaped], shape))
    return out


def _invalidate(entities, by_family, contracts, patch, op) -> None:
    """The record remains readable. What it loses is unqualified authority."""
    rec = entities[op.entity_id]
    rec["_validity"] = ValidityStatus.INVALIDATED.value
    _log(rec, "_invalidations",
         {"stage": patch.stage_id, "reason": op.reason,
          "provenance": op.provenance_ref})
    _propagate(entities, op.entity_id, "INVALIDATED", op.reason,
               skip=set(skip_ids(patch)))


_MUTATORS = {"CREATE": _create, "EXTEND": _extend,
             "SUPERSEDE": _supersede, "INVALIDATE": _invalidate}
