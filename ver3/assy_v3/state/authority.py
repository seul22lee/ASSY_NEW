"""The authority model: which values may change, and by what path.

Frozen architecture FA-2 and FA-3 (S01_S04_ARCHITECTURE_FREEZE.md §3, §5).

Four authority classes, and every value belongs to exactly one:

  A  AUTHORITATIVE  engineering state the design asserts. Controlled mutation
                    only, provenance required.
  B  DERIVED        strict consequences of class-A premises. Recomputable.
                    Carries its premise set. Never authored-looking.
  C  EPHEMERAL      views, serializations, caches, provider payloads. Freely
                    regenerated. Never stored in DesignState at all - a
                    projection returns plain dicts outside the state, which is
                    what makes class C structurally distinguishable here.
  D  ASSURANCE      check results and findings. Append-only consumers of
                    class A, never producers of it.

The guard classes below exist because the audited defect was not a stage
misbehaving. It was a runner helper assigning into an entity dict directly, with
no operation, no ownership check and no provenance - and nothing in the system
could have detected it. A convention would not have caught that. A locked
container does.
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

    #: Current, and no premise it depends on has changed.
    STANDING = "STANDING"
    #: A replacement value was recorded. Both are retained.
    SUPERSEDED = "SUPERSEDED"
    #: Explicitly withdrawn with a reason. The record remains.
    INVALIDATED = "INVALIDATED"
    #: A premise this value depends on was superseded or invalidated. The value
    #: itself was not touched; it has lost unqualified authority.
    STALE = "STALE"


#: Statuses that do NOT carry unqualified authority.
NOT_UNQUALIFIED = (ValidityStatus.SUPERSEDED, ValidityStatus.INVALIDATED,
                   ValidityStatus.STALE)


class AuthorityViolation(Exception):
    """An attempt to change class-A state outside the controlled boundary.

    Never a statement about the design. It says a write took the wrong path.
    """


class _MutationGate:
    """Open only inside the controlled mutation boundary."""

    __slots__ = ("open",)

    def __init__(self) -> None:
        self.open = False

    @contextmanager
    def unlocked(self) -> Iterator[None]:
        previous = self.open
        self.open = True
        try:
            yield
        finally:
            self.open = previous


def _refuse(what: str, key: Any) -> None:
    raise AuthorityViolation(
        "UNCONTROLLED_WRITE: %s[%r] outside the controlled mutation boundary. "
        "Class-A state changes only through CREATE / EXTEND / SUPERSEDE / "
        "INVALIDATE carried by a StagePatch (FA-3)." % (what, key))


class GuardedRecord(dict):
    """One authoritative entity. Readable everywhere, writable only by the boundary."""

    __slots__ = ("_gate",)

    def __init__(self, gate: _MutationGate, data: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(data or {})
        self._gate = gate

    # -- writes -----------------------------------------------------------
    def __setitem__(self, key: Any, value: Any) -> None:
        if not self._gate.open:
            _refuse("entity", key)
        super().__setitem__(key, value)

    def __delitem__(self, key: Any) -> None:
        if not self._gate.open:
            _refuse("entity", key)
        super().__delitem__(key)

    def update(self, *args: Any, **kw: Any) -> None:            # type: ignore[override]
        if not self._gate.open:
            _refuse("entity", "update")
        super().update(*args, **kw)

    def setdefault(self, key: Any, default: Any = None) -> Any:  # type: ignore[override]
        if key not in self and not self._gate.open:
            _refuse("entity", key)
        return super().setdefault(key, default)

    def pop(self, *args: Any) -> Any:                            # type: ignore[override]
        if not self._gate.open:
            _refuse("entity", args[0] if args else "pop")
        return super().pop(*args)

    def popitem(self) -> Any:
        if not self._gate.open:
            _refuse("entity", "popitem")
        return super().popitem()

    def clear(self) -> None:
        if not self._gate.open:
            _refuse("entity", "clear")
        super().clear()


class GuardedEntities(dict):
    """The entity table. Adding or replacing an entity is a controlled act."""

    __slots__ = ("_gate",)

    def __init__(self, gate: _MutationGate) -> None:
        super().__init__()
        self._gate = gate

    def __setitem__(self, key: Any, value: Any) -> None:
        if not self._gate.open:
            _refuse("entities", key)
        super().__setitem__(key, value)

    def __delitem__(self, key: Any) -> None:
        if not self._gate.open:
            _refuse("entities", key)
        super().__delitem__(key)

    def update(self, *args: Any, **kw: Any) -> None:            # type: ignore[override]
        if not self._gate.open:
            _refuse("entities", "update")
        super().update(*args, **kw)

    def setdefault(self, key: Any, default: Any = None) -> Any:  # type: ignore[override]
        if key not in self and not self._gate.open:
            _refuse("entities", key)
        return super().setdefault(key, default)

    def pop(self, *args: Any) -> Any:                            # type: ignore[override]
        if not self._gate.open:
            _refuse("entities", args[0] if args else "pop")
        return super().pop(*args)

    def clear(self) -> None:
        if not self._gate.open:
            _refuse("entities", "clear")
        super().clear()
