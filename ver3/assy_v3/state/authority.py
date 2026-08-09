"""The authority model: which values may change, and by what path.

Frozen architecture FA-2 and FA-3 (S01_S04_ARCHITECTURE_FREEZE.md §3, §5).

Four authority classes, and every value belongs to exactly one:

  A  AUTHORITATIVE  engineering state the design asserts. Controlled mutation
                    only, provenance required.
  B  DERIVED        strict consequences of class-A premises. Recomputable.
                    Carries its premise set. Never authored-looking.
  C  EPHEMERAL      views, serializations, caches, provider payloads. Plain
                    mutable structures. Everything a reader receives is class C.
  D  ASSURANCE      check results and findings. Append-only consumers of
                    class A, never producers of it.

ENFORCEMENT MODEL - ENCAPSULATION, NOT GUARDED SUBCLASSES
    Authoritative storage is owned exclusively by DesignState and NEVER LEAVES
    IT. Internally it is plain dicts and lists; externally, every read returns a
    defensive plain copy, and the entity table is exposed only through a
    read-only mapping.

    The previous design subclassed dict and list and guarded their mutators. That
    cannot satisfy the invariant, and the reason is structural rather than an
    oversight: for any `dict` subclass, ``dict.__setitem__(obj, k, v)`` is an
    ordinary Python call that does not dispatch through the override. The same
    holds for every base-class mutator on both types. A representation whose
    authoritative storage IS a builtin mutable container therefore always exposes
    a supported bypass, no matter how completely its methods are overridden.

    Encapsulation removes the question. There is no capability object to
    discover, because nothing outside DesignState.apply() ever needs one; and
    there is no authoritative container to call a base-class mutator on, because
    no authoritative container is ever handed out.

WHAT A READER GETS
    A plain dict or list it owns. Mutating it is legal, ordinary, and has no
    effect on state - the same semantics as `dict.copy()`, which is the idiom
    every Python reader already understands. Mutation is not rejected; it is
    INEFFECTIVE, which is the property that matters: authoritative state cannot
    be changed through a reference obtained by reading.

SUPPORTED-INTERFACE GUARANTEE, AND ITS LIMIT
    Guaranteed for ordinary repository operations - attribute assignment,
    attribute lookup, method invocation on returned objects, and base-class
    mutation APIs: none of them can change authoritative state outside
    DesignState.apply().

    Not guaranteed against deliberately implementation-breaking reflection:
    reading a name-mangled private attribute, `object.__setattr__` against
    internals, `ctypes`, or monkey-patching. Those are excluded because they are
    not operations a normal module would reasonably perform on an object it was
    handed - not because they are hard. This is repository-level architectural
    enforcement, not a security sandbox.
"""
from __future__ import annotations

try:                                                  # pragma: no cover
    from collections.abc import Mapping
except ImportError:                                   # pragma: no cover
    from collections import Mapping                   # type: ignore
from enum import Enum
from typing import Any, Dict, Iterator


class AuthorityClass(str, Enum):
    """FA-2. Declared per family in DESIGN_STATE_CONTRACT.authority_model."""

    AUTHORITATIVE = "AUTHORITATIVE"
    DERIVED = "DERIVED"
    EPHEMERAL = "EPHEMERAL"
    ASSURANCE = "ASSURANCE"


class ValidityStatus(str, Enum):
    """FA-5. What a premise change does to a dependent commitment.

    Nothing is deleted (FA-1). A superseded or invalidated fact stays readable;
    what it loses is unqualified authority.
    """

    STANDING = "STANDING"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"
    STALE = "STALE"


NOT_UNQUALIFIED = (ValidityStatus.SUPERSEDED, ValidityStatus.INVALIDATED,
                   ValidityStatus.STALE)


class AuthorityViolation(Exception):
    """An attempt to change class-A state outside the controlled boundary.

    Never a statement about the design. It says a write took the wrong path.
    """


def copy_out(value: Any) -> Any:
    """A plain, owned copy of an authoritative value. Class C.

    Recursive, so no level of the returned structure is shared with state.
    """
    if isinstance(value, dict):
        return {k: copy_out(v) for k, v in value.items()}
    if isinstance(value, list):
        return [copy_out(v) for v in value]
    if isinstance(value, tuple):
        return tuple(copy_out(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return set(value)
    return value                            # scalars, str, bytes, None


def copy_in(value: Any) -> Any:
    """A plain copy for storage, detached from whatever the caller still holds.

    This is what closes input aliasing: the object an operation was given is
    never the object state keeps.
    """
    if isinstance(value, dict):
        return {k: copy_in(v) for k, v in value.items()}
    if isinstance(value, list):
        return [copy_in(v) for v in value]
    if isinstance(value, tuple):
        return tuple(copy_in(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return set(value)
    return value


#: Retained under its historical name: `thaw` was what callers used to turn an
#: authoritative structure into a plain one. Everything is plain on the way out
#: now, so it is the identity-preserving copy.
thaw = copy_out


class ReadOnlyTable(Mapping):
    """The entity table as a reader sees it: lookups only.

    Derives from Mapping, not from dict, so there is no inherited mutator and no
    base-class call that could reach the underlying storage - the bypass that
    made the previous representation unsalvageable.

    Every value it yields is a defensive copy, so a reader cannot reach stored
    state through a record either.
    """

    __slots__ = ("_backing",)

    def __init__(self, backing: Dict[str, Dict[str, Any]]) -> None:
        object.__setattr__(self, "_backing", backing)

    # -- reads ------------------------------------------------------------
    def __getitem__(self, key: str) -> Dict[str, Any]:
        return copy_out(self._backing[key])

    def __iter__(self) -> Iterator[str]:
        return iter(self._backing)

    def __len__(self) -> int:
        return len(self._backing)

    def __contains__(self, key: object) -> bool:
        return key in self._backing

    def __repr__(self) -> str:
        return "ReadOnlyTable(%d entities)" % len(self._backing)

    # -- writes, refused with the reason rather than a bare TypeError ------
    def _refuse(self, op: str, *args: Any) -> None:
        raise AuthorityViolation(
            "UNCONTROLLED_WRITE: %s on the entity table. Authoritative state "
            "changes only through CREATE / EXTEND / SUPERSEDE / INVALIDATE "
            "carried by a StagePatch and applied by DesignState.apply() (FA-3)."
            % op)

    def __setitem__(self, *a: Any) -> None:
        self._refuse("__setitem__")

    def __delitem__(self, *a: Any) -> None:
        self._refuse("__delitem__")

    def update(self, *a: Any, **kw: Any) -> None:
        self._refuse("update")

    def setdefault(self, *a: Any) -> None:
        self._refuse("setdefault")

    def pop(self, *a: Any) -> None:
        self._refuse("pop")

    def popitem(self, *a: Any) -> None:
        self._refuse("popitem")

    def clear(self, *a: Any) -> None:
        self._refuse("clear")
