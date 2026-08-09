"""The authority model: which values may change, and by what path.

Frozen architecture FA-2 and FA-3 (S01_S04_ARCHITECTURE_FREEZE.md §3, §5).

Four authority classes, and every value belongs to exactly one:

  A  AUTHORITATIVE  engineering state the design asserts. Controlled mutation
                    only, provenance required.
  B  DERIVED        strict consequences of class-A premises. Recomputable.
                    Carries its premise set. Never authored-looking.
  C  EPHEMERAL      views, serializations, caches, provider payloads. Freely
                    regenerated. Plain mutable structures, produced by `thaw`.
  D  ASSURANCE      check results and findings. Append-only consumers of
                    class A, never producers of it.

ENFORCEMENT MODEL
    Authoritative values are stored in guarded containers, RECURSIVELY. A dict
    becomes a GuardedDict, a list a GuardedList, at every depth. Every mutating
    method of the underlying type is closed; with the write capability closed,
    each raises AuthorityViolation.

    Wrapping happens on WRITE, and it CONSTRUCTS NEW CONTAINERS from the input's
    contents. That is what closes input aliasing: the object a caller passed into
    an operation is never the object the state holds, so the caller cannot reach
    back into state through the reference it kept.

    Reads are free and cost nothing: GuardedDict IS a dict and GuardedList IS a
    list, so indexing, `.get`, iteration, equality and json serialization all
    behave identically for every existing reader.

    A consumer that needs a mutable structure - a projection, a prompt payload, a
    cache - calls `thaw()` and gets plain dicts and lists. That is class C, and it
    is deliberately outside the authority model.

WHAT THIS GUARANTEES, AND WHAT IT DOES NOT
    Guaranteed: no supported interface in this repository can change authoritative
    state outside the controlled mutation boundary. Every mutating method of every
    authoritative container refuses, at every depth, and the write capability is
    not reachable under any public name.

    NOT guaranteed: immunity to introspection. `object.__setattr__` on a private
    slot, `gc` traversal, or importing this module and constructing a capability
    directly can still reach the stored objects. This is repository-level
    architectural enforcement, not a security sandbox, and the distinction is
    stated rather than blurred.
"""
from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from typing import Any, Dict, Iterator, Optional


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


class WriteCapability:
    """The authority to mutate. Held privately by one DesignState.

    Not a public switch: it is stored name-mangled on the state, refused for
    reassignment, and never returned by any accessor. Opening it is the act of
    entering the controlled mutation boundary.
    """

    __slots__ = ("_open",)

    def __init__(self) -> None:
        self._open = False

    @property
    def open(self) -> bool:
        return self._open

    @contextmanager
    def granted(self) -> Iterator[None]:
        previous = self._open
        self._open = True
        try:
            yield
        finally:
            self._open = previous


def _refuse(container: str, key: Any, op: str) -> None:
    raise AuthorityViolation(
        "UNCONTROLLED_WRITE: %s.%s(%r) outside the controlled mutation boundary. "
        "Class-A state changes only through CREATE / EXTEND / SUPERSEDE / "
        "INVALIDATE carried by a StagePatch (FA-3). To change a nested value, "
        "submit an operation describing the change." % (container, op, key))


def _is_granted(cap: Any) -> bool:
    """True only for a real, open capability.

    The type check matters: without it any object exposing ``open = True`` would
    unlock a container, so a forged capability would be a one-line bypass. With
    it, forgery requires importing this module and rebinding a private slot
    through ``object.__setattr__`` - introspection, not a supported interface.
    """
    return type(cap) is WriteCapability and cap.open


def _guard_methods(cls, base, names, label):
    """Close every mutating method the base type provides.

    Generated rather than hand-written, so a method cannot be left active by
    oversight - which is exactly how `popitem` survived the first pass.
    """
    for name in names:
        original = getattr(base, name, None)
        if original is None:
            continue                       # not present on this Python version

        def make(name=name, original=original):
            def guarded(self, *args, **kw):
                if not _is_granted(self._cap):
                    _refuse(label, args[0] if args else None, name)
                return original(self, *args, **kw)
            guarded.__name__ = name
            guarded.__qualname__ = "%s.%s" % (cls.__name__, name)
            return guarded

        setattr(cls, name, make())


#: Every mutating name on the mapping API, including 3.9+ in-place union.
_DICT_MUTATORS = ("__setitem__", "__delitem__", "__ior__", "update",
                  "setdefault", "pop", "popitem", "clear")

#: Every mutating name on the sequence API, including in-place operators.
_LIST_MUTATORS = ("__setitem__", "__delitem__", "__iadd__", "__imul__",
                  "append", "extend", "insert", "pop", "remove", "clear",
                  "sort", "reverse")


class GuardedDict(dict):
    """An authoritative mapping at any depth. Readable everywhere, writable only
    inside the controlled mutation boundary."""

    __slots__ = ("_cap",)

    def __init__(self, cap: WriteCapability,
                 data: Optional[Dict[Any, Any]] = None) -> None:
        # dict.__init__ does not route through __setitem__, so construction is
        # not a guarded write and needs no capability.
        super().__init__(data or {})
        object.__setattr__(self, "_cap", cap)

    def __reduce__(self):                                  # copy/pickle -> plain
        return (dict, (dict(self),))


class GuardedList(list):
    """An authoritative sequence at any depth."""

    __slots__ = ("_cap",)

    def __init__(self, cap: WriteCapability, data=None) -> None:
        super().__init__(data or [])
        object.__setattr__(self, "_cap", cap)

    def __reduce__(self):
        return (list, (list(self),))


_guard_methods(GuardedDict, dict, _DICT_MUTATORS, "entity")
_guard_methods(GuardedList, list, _LIST_MUTATORS, "value")

#: The entity table and an entity record are both authoritative mappings. They
#: are named separately because their error messages and their roles differ, but
#: the enforcement is identical.
GuardedEntities = GuardedDict
GuardedRecord = GuardedDict


def wrap(value: Any, cap: WriteCapability) -> Any:
    """Recursively place a value under authority.

    New containers are constructed at every level, so the caller's objects are
    never the objects state holds. This is what makes input aliasing impossible
    rather than merely discouraged.
    """
    if isinstance(value, dict):
        return GuardedDict(cap, {k: wrap(v, cap) for k, v in value.items()})
    if isinstance(value, list):
        return GuardedList(cap, [wrap(v, cap) for v in value])
    if isinstance(value, tuple):
        return tuple(wrap(v, cap) for v in value)
    if isinstance(value, set):
        return frozenset(value)
    return value                            # scalars, str, bytes, None: immutable


def thaw(value: Any) -> Any:
    """A plain mutable copy: class C. Nothing thawed can affect class-A state."""
    if isinstance(value, dict):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        out = [thaw(v) for v in value]
        return tuple(out) if isinstance(value, tuple) else out
    if isinstance(value, frozenset):
        return set(value)
    return value
