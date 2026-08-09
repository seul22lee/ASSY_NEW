"""DEFENCE IN DEPTH for the authority boundary. NOT proof of authority safety.

**The runtime guard in assy_v3/state/authority.py is the enforcement.** Guarded
containers refuse every mutating method at every depth, and the write capability
is held in a module-private registry rather than on the state object. This scan
exists only to catch common accidental bypasses at review time, before anyone
runs the code that would trip the guard.

What it can do: flag the shapes the audit actually found, plus direct use of the
write capability outside the state module.

What it cannot do, and does not claim: complete Python alias analysis. A write
reaching state through an alias created in another function is invisible here and
is caught at runtime instead. Treating this scan as the authority model would be
the same category error as treating a convention as a boundary.
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

VER3 = os.path.join(REPO, "ver3")

#: The controlled mutation boundary itself. It is the one place permitted to
#: write, and it is guarded from within by the gate rather than by this scan.
BOUNDARY = {os.path.join(VER3, "assy_v3", "state", "design_state.py"),
            os.path.join(VER3, "assy_v3", "state", "authority.py")}

SCANNED = [os.path.join(VER3, "assy_v3"), os.path.join(VER3, "tools"),
           os.path.join(VER3, "live_providers")]

#: Attributes DesignState legitimately carries. Anything else assigned onto a
#: state object is a side-channel engineering fact - the second half of the
#: audited defect (`state.s04a_reach = ...`). The write capability is not among
#: them: it is held off the instance entirely.
STATE_ATTRS = {"run_id", "c", "entities", "by_family", "applied_patches"}

#: Names that grant or hold write authority. Outside the state package there is
#: no legitimate reason to touch any of them.
CAPABILITY_NAMES = {"granted", "unlocked", "_cap", "_gate", "WriteCapability",
                    "_CAPABILITIES", "_is_granted"}


def _python_files():
    for root in SCANNED:
        for dirpath, _dirs, names in os.walk(root):
            for n in sorted(names):
                if n.endswith(".py"):
                    path = os.path.join(dirpath, n)
                    if path not in BOUNDARY:
                        yield path


def _is_state_ish(node) -> bool:
    """`state`, `self.state`, `design_state`, ... conservatively matched by name."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return isinstance(node, ast.Name) and (
        node.id == "state" or node.id.endswith("_state"))


def _violations(path):
    with open(path) as fh:
        src = fh.read()
    tree = ast.parse(src, filename=path)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for tgt in targets:
            # shape 1:  state.entities[...] = ...   /   e["field"] = ... via entities
            if isinstance(tgt, ast.Subscript):
                base = tgt.value
                if (isinstance(base, ast.Attribute) and base.attr in ("entities", "by_family")
                        and _is_state_ish(base.value)):
                    out.append((node.lineno, "direct write into %s" % base.attr))
            # shape 2:  state.<anything not an allowed attribute> = ...
            if isinstance(tgt, ast.Attribute) and _is_state_ish(tgt.value):
                if isinstance(tgt.value, ast.Name) and tgt.attr not in STATE_ATTRS:
                    out.append((node.lineno,
                                "side-channel attribute %r on state" % tgt.attr))

    # shape 3: reaching for write authority at all, outside the state package
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in CAPABILITY_NAMES:
            out.append((node.lineno,
                        "use of write-capability name %r" % node.attr))
        elif isinstance(node, ast.Name) and node.id in CAPABILITY_NAMES:
            out.append((node.lineno,
                        "use of write-capability name %r" % node.id))
        # shape 4: object.__setattr__(x, ...) is the documented introspection
        # bypass; it has no legitimate use outside the state package.
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "__setattr__"):
            out.append((node.lineno, "object.__setattr__ bypass"))
    return out


class TestNoUncontrolledAuthoritativeWrites(unittest.TestCase):

    def test_no_direct_authoritative_writes_outside_the_boundary(self):
        found = []
        for path in _python_files():
            for lineno, why in _violations(path):
                found.append("%s:%d %s" % (os.path.relpath(path, REPO), lineno, why))
        assert not found, (
            "Class-A state may change only through CREATE / EXTEND / SUPERSEDE / "
            "INVALIDATE carried by a StagePatch (FA-3). Found:\n  " + "\n  ".join(found))


    def test_the_scan_rejects_external_use_of_the_write_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            specimen = os.path.join(tmp, "sneaky.py")
            with open(specimen, "w") as fh:
                fh.write("def sneak(state, rec):\n"
                         "    with state._cap.granted():\n"
                         "        rec['x'] = 1\n"
                         "    object.__setattr__(rec, '_cap', None)\n")
            found = _violations(specimen)
        kinds = {why for _ln, why in found}
        self.assertIn("use of write-capability name '_cap'", kinds)
        self.assertIn("use of write-capability name 'granted'", kinds)
        self.assertIn("object.__setattr__ bypass", kinds)

    def test_the_scan_would_actually_catch_the_historical_defect(self):
        """A guard nobody has seen fail is not evidence. Feed it the old code."""
        with tempfile.TemporaryDirectory() as tmp:
            specimen = os.path.join(tmp, "old_absorb.py")
            with open(specimen, "w") as fh:
                fh.write("def _absorb(state, key, raw):\n"
                         "    e = state.entities.get('FRG-0001')\n"
                         "    state.entities['X'] = {}\n"
                         "    state.s04a_reach = []\n")
            found = _violations(specimen)
        kinds = {why for _ln, why in found}
        assert "direct write into entities" in kinds
        assert "side-channel attribute 's04a_reach' on state" in kinds


if __name__ == "__main__":
    unittest.main()
