"""The S-1 supported-interface invariant, and the matrix that defines it.

Repository code using ordinary interfaces must not be able to (1) replace an
authoritative storage root, (2) acquire or replace write authority, (3) mutate
state through a reference a read returned, (4) bypass through an ordinary
container interface, or (5) otherwise change authoritative state except through
DesignState.apply(StagePatch).

SUPPORTED INTERFACE - the definition this file tests against
    Ordinary Python operations a normal module could reasonably perform on an
    object DesignState handed it: attribute lookup, attribute assignment, method
    invocation, and BASE-CLASS Python-callable mutation APIs such as
    ``dict.__setitem__(obj, k, v)``. Base-class calls are inside the contract
    because they are ordinary, documented Python that any module may write - the
    previous design excluded them by omission rather than by argument, and that
    is exactly what left the hole.

    Excluded: reading a name-mangled private attribute of another object,
    ``object.__setattr__`` against internals, ctypes, and monkey-patching. These
    are excluded because they are deliberately implementation-breaking, not
    because they are difficult. That boundary is itself tested below.

History: written against 65ebe1a, where five of the matrix rows below were OPEN
using ordinary operations only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.state.authority import (AuthorityViolation, ReadOnlyTable,  # noqa: E402
                                          copy_in, copy_out, thaw)
from ver3.assy_v3.state.design_state import ContractError, DesignState        # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                           # noqa: E402


def _reflect(state):
    """The excluded region, in one place: reach the private storage registry.

    Every use of this helper marks a test that deliberately steps outside the
    supported interface, so the boundary stays visible instead of scattered.
    """
    from ver3.assy_v3.state import design_state as _ds
    return _ds._STORAGE[state]


def _patch(state, stage, ops, pid="p1"):
    return StagePatch(
        patch_id=pid, run_id=state.run_id, stage_id=stage, stage_attempt=1,
        parent_state_hash=state.state_hash(), operations=ops,
        execution_status="SUCCESS", provenance={"provider": "test"})


def _seeded():
    s = DesignState("harden")
    s.apply(_patch(s, "s03", [
        Op("CREATE", "Body", "BOD-0001",
           {"instance_identity": "b", "role": "STRUCTURE", "created_by_stage": "s03",
            "addresses_obligations": []}, "prov:s03"),
        Op("CREATE", "RigidGroup", "RGP-0001",
           {"body": "BOD-0001", "members": ["BOD-0001"], "is_default": True}, "prov:s03"),
        Op("CREATE", "RigidGroup", "RGP-0002",
           {"body": "BOD-0001", "members": ["BOD-0001"], "is_default": False}, "prov:s03"),
        Op("CREATE", "FunctionalRegion", "FRG-0001",
           {"role": "ACCESS", "owning_bodies": ["BOD-0001"]}, "prov:s03")], pid="p0"))
    s.apply(_patch(s, "s04", [
        Op("EXTEND", "FunctionalRegion", "FRG-0001",
           {"volume": {"half_extent": [1.0, 1.0, 1.0], "centre": [0.0, 0.0, 0.0]}},
           "prov:s04a")], pid="p1"))
    return s


def _joint(state):
    state.apply(_patch(state, "s03", [
        Op("CREATE", "Body", "BOD-0001",
           {"instance_identity": "b", "role": "STRUCTURE", "created_by_stage": "s03",
            "addresses_obligations": []}, "prov:s03"),
        Op("CREATE", "RigidGroup", "RGP-0001",
           {"body": "BOD-0001", "members": ["BOD-0001"], "is_default": True}, "prov:s03"),
        Op("CREATE", "RigidGroup", "RGP-0002",
           {"body": "BOD-0001", "members": ["BOD-0001"], "is_default": False}, "prov:s03"),
        Op("CREATE", "Joint", "JNT-0001",
           {"joint_type": "REVOLUTE", "parent_group": "RGP-0001",
            "child_group": "RGP-0002", "dof": ["RZ"],
            "axis_direction": [0, 0, 1], "frame_ids": []}, "prov:s03")], pid="pj"))
    return state


class _Base(unittest.TestCase):

    def assertStateUnchanged(self, state, before):
        self.assertEqual(before, state.state_hash())


# =====================================================================
# ROOT-01/02 - authoritative storage roots are not replaceable
# =====================================================================
class TestStorageRoots(_Base):

    def test_ROOT_01_entity_root_cannot_be_replaced(self):
        s = _seeded()
        with self.assertRaisesRegex(AuthorityViolation, "PROTECTED_ROOT"):
            s.entities = {}
        self.assertIn("FRG-0001", s.entities)

    def test_ROOT_02_index_and_history_roots_cannot_be_replaced(self):
        s = _seeded()
        for name, value in (("by_family", {}), ("applied_patches", [])):
            with self.subTest(root=name):
                with self.assertRaisesRegex(AuthorityViolation, "PROTECTED_ROOT"):
                    setattr(s, name, value)
        self.assertEqual(["FRG-0001"], s.by_family["FunctionalRegion"])

    def test_ROOT_identity_attributes_are_write_once(self):
        s = _seeded()
        for name in ("run_id", "c"):
            with self.subTest(attr=name):
                with self.assertRaisesRegex(AuthorityViolation, "PROTECTED_ROOT"):
                    setattr(s, name, None)

    def test_ROOT_roots_cannot_be_deleted(self):
        s = _seeded()
        with self.assertRaisesRegex(AuthorityViolation, "PROTECTED_ROOT"):
            del s.entities

    def test_ROOT_side_channel_attributes_still_refused(self):
        s = _seeded()
        for name in ("s04a_reach", "s04a_elimination", "s04a_scale", "anything"):
            with self.subTest(attr=name):
                with self.assertRaisesRegex(AuthorityViolation, "SIDE_CHANNEL_WRITE"):
                    setattr(s, name, ["x"])

    def test_ROOT_mutating_a_returned_index_copy_does_not_change_state(self):
        s = _seeded()
        before = s.state_hash()
        s.by_family["FunctionalRegion"].append("GHOST")
        s.by_family["Invented"] = ["X"]
        s.applied_patches.append("ghost-patch")
        self.assertEqual(["FRG-0001"], s.by_family["FunctionalRegion"])
        self.assertNotIn("Invented", s.by_family)
        self.assertNotIn("ghost-patch", s.applied_patches)
        self.assertStateUnchanged(s, before)


# =====================================================================
# CAP-01..04 - write authority is not part of the object surface
# =====================================================================
class TestCapabilityEncapsulation(_Base):
    """There is no capability object to find. Encapsulation removed the question
    rather than hiding the answer."""

    #: Token-bounded, so `_propagate` and `str.capitalize` are not false hits.
    HINT = re.compile(r"(?:^|_)(cap|gate|grant|granted|unlock|unlocked|token|"
                      r"capability|authorize|authorise)(?:$|_)", re.I)

    def _capability_names(self, obj):
        return [n for n in dir(obj) if self.HINT.search(n)]

    def _assert_no_capability_surface(self, obj, label):
        hits = self._capability_names(obj)
        self.assertEqual([], hits,
                         "%s exposes capability-shaped names %s" % (label, hits))

    def test_CAP_01_design_state_exposes_no_capability(self):
        self._assert_no_capability_surface(_seeded(), "DesignState")

    def test_CAP_02_a_record_from_the_read_api_exposes_no_capability(self):
        s = _seeded()
        for rec in (s.entities["FRG-0001"], s.family("FunctionalRegion")[0],
                    s.standing("FunctionalRegion")[0]):
            self._assert_no_capability_surface(rec, "record")
            self.assertIs(dict, type(rec))

    def test_CAP_03_a_nested_value_exposes_no_capability(self):
        s = _seeded()
        rec = s.entities["FRG-0001"]
        self._assert_no_capability_surface(rec["volume"], "nested dict")
        self._assert_no_capability_surface(rec["volume"]["centre"], "nested list")
        self.assertIs(dict, type(rec["volume"]))
        self.assertIs(list, type(rec["volume"]["centre"]))

    def test_CAP_04_no_reachable_object_carries_write_authority(self):
        """Traverse everything a reader can reach and find nothing that grants."""
        s = _seeded()
        seen, found = set(), []
        queue = [s, s.entities, s.by_family, s.applied_patches,
                 s.entities["FRG-0001"], s.family("FunctionalRegion")[0]]
        while queue:
            obj = queue.pop()
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            found.extend("%s.%s" % (type(obj).__name__, n)
                         for n in self._capability_names(obj))
            if isinstance(obj, dict):
                queue.extend(list(obj.values())[:50])
            elif isinstance(obj, (list, tuple)):
                queue.extend(list(obj)[:50])
        self.assertEqual([], found)


# =====================================================================
# MUT-01..06 - no ordinary container interface reaches storage
# =====================================================================
class TestContainerInterfaces(_Base):

    def test_MUT_01_top_level_table_mutators_are_refused(self):
        s = _seeded()
        before = s.state_hash()
        calls = {"__setitem__": ("X", {}), "__delitem__": ("FRG-0001",),
                 "update": ({"X": {}},), "setdefault": ("X", {}),
                 "pop": ("FRG-0001",), "popitem": (), "clear": ()}
        for name, args in calls.items():
            with self.subTest(mutator=name):
                with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
                    getattr(s.entities, name)(*args)
        self.assertStateUnchanged(s, before)

    def test_MUT_02_nested_mutation_on_a_read_record_cannot_change_state(self):
        s = _seeded()
        before = s.state_hash()
        rec = s.entities["FRG-0001"]
        rec["volume"]["centre"][0] = 999          # legal on the copy the caller owns
        rec["volume"]["centre"].append(4)
        rec["owning_bodies"].append("BOD-9999")
        rec["role"] = "REWRITTEN"
        self.assertEqual([0.0, 0.0, 0.0], s.entities["FRG-0001"]["volume"]["centre"])
        self.assertEqual(["BOD-0001"], s.entities["FRG-0001"]["owning_bodies"])
        self.assertEqual("ACCESS", s.entities["FRG-0001"]["role"])
        self.assertStateUnchanged(s, before)

    def test_MUT_03_input_aliases_cannot_reach_back_into_state(self):
        s = DesignState("alias")
        deep = {"a": [{"b": [1, 2, 3]}]}
        bodies = ["BOD-0001"]
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-0001",
               {"basis": "RELATIVE", "note": deep}, "p")]))
        s.apply(_patch(s, "s03", [
            Op("CREATE", "Body", "BOD-0001",
           {"instance_identity": "b", "role": "STRUCTURE",
            "created_by_stage": "s03", "addresses_obligations": []}, "p"),
            Op("CREATE", "FunctionalRegion", "FRG-0001",
               {"role": "ACCESS", "owning_bodies": bodies}, "p")], pid="p1"))
        deep["a"][0]["b"][0] = 999
        deep["a"].append("extra")
        bodies.append("BOD-9999")
        self.assertEqual(1, s.entities["SCL-0001"]["note"]["a"][0]["b"][0])
        self.assertEqual(1, len(s.entities["SCL-0001"]["note"]["a"]))
        self.assertEqual(["BOD-0001"], s.entities["FRG-0001"]["owning_bodies"])

    def test_MUT_04_dict_base_class_calls_cannot_reach_storage(self):
        """The bypass that made builtin subclassing unsalvageable.

        `dict.__setitem__(obj, k, v)` does not dispatch through an override, so a
        dict-subclass representation can always be mutated this way. It is closed
        here because nothing a reader holds IS the storage: the table is not a
        dict at all, and a record is a copy."""
        s = _seeded()
        before = s.state_hash()
        self.assertNotIsInstance(s.entities, dict)
        for call, args in ((dict.__setitem__, ("X", {})), (dict.pop, ("FRG-0001",)),
                           (dict.update, ({"X": {}},)), (dict.clear, ())):
            with self.subTest(call=call.__name__):
                with self.assertRaises(TypeError):
                    call(s.entities, *args)
        rec = s.entities["FRG-0001"]
        dict.__setitem__(rec, "role", "BASE_CLASS")        # legal on the copy
        dict.pop(rec, "owning_bodies")
        self.assertEqual("ACCESS", s.entities["FRG-0001"]["role"])
        self.assertIn("owning_bodies", s.entities["FRG-0001"])
        self.assertStateUnchanged(s, before)

    def test_MUT_05_list_base_class_calls_cannot_reach_storage(self):
        s = _seeded()
        before = s.state_hash()
        centre = s.entities["FRG-0001"]["volume"]["centre"]
        list.__setitem__(centre, 0, 999)
        list.append(centre, 4)
        list.clear(s.entities["FRG-0001"]["owning_bodies"])
        self.assertEqual([0.0, 0.0, 0.0], s.entities["FRG-0001"]["volume"]["centre"])
        self.assertEqual(["BOD-0001"], s.entities["FRG-0001"]["owning_bodies"])
        self.assertStateUnchanged(s, before)

    def test_MUT_06_entity_deletion_and_replacement_are_refused(self):
        s = _seeded()
        before = s.state_hash()
        with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
            del s.entities["FRG-0001"]
        with self.assertRaisesRegex(AuthorityViolation, "UNCONTROLLED_WRITE"):
            s.entities["FRG-0001"] = {}
        self.assertStateUnchanged(s, before)
        self.assertIn("FRG-0001", s.entities)


# =====================================================================
# READ-01 - the read API is not a write API
# =====================================================================
class TestReadApi(_Base):

    def test_READ_01_no_read_result_confers_write_authority(self):
        s = _seeded()
        before = s.state_hash()
        results = [s.entities["FRG-0001"], s.family("FunctionalRegion")[0],
                   s.standing("FunctionalRegion")[0], s.by_family,
                   s.applied_patches, s.counts()]
        for i, obj in enumerate(results):
            with self.subTest(result=i):
                if isinstance(obj, dict):
                    obj["INJECTED"] = "x"
                elif isinstance(obj, list):
                    obj.append("INJECTED")
        self.assertStateUnchanged(s, before)
        self.assertNotIn("INJECTED", s.entities["FRG-0001"])
        self.assertNotIn("INJECTED", s.by_family)

    def test_READ_reads_remain_ordinary_and_usable(self):
        s = _seeded()
        rec = s.entities["FRG-0001"]
        self.assertIs(dict, type(rec))
        self.assertEqual("ACCESS", rec.get("role"))
        self.assertIn("volume", rec)
        self.assertEqual([0.0, 0.0, 0.0], rec["volume"]["centre"])   # equality vs list
        self.assertEqual(3, len(rec["volume"]["centre"]))
        self.assertEqual(0.0, min(rec["volume"]["centre"]))
        self.assertTrue(json.dumps(rec))                              # serializable
        self.assertTrue(json.dumps(s.family("FunctionalRegion")))
        # The seed now also carries the Body and RigidGroups its own references
        # name - a typed reference must denote an entity - so the counts are of
        # the whole seed rather than of the one region under test.
        self.assertIn("FRG-0001", s.entities)
        self.assertEqual(1, s.counts()["FunctionalRegion"])
        self.assertEqual(len(s.entities), sum(s.counts().values()))

    def test_READ_two_reads_are_independent_copies(self):
        s = _seeded()
        a, b = s.entities["FRG-0001"], s.entities["FRG-0001"]
        self.assertIsNot(a, b)
        a["volume"]["centre"][0] = 5
        self.assertEqual([0.0, 0.0, 0.0], b["volume"]["centre"])


# =====================================================================
# AUTH-01..03 - controlled mutation still correct
# =====================================================================
class TestControlledMutationStillCorrect(_Base):

    def test_AUTH_01_family_spoofing_is_refused(self):
        s = _joint(DesignState("spoof"))
        self.assertEqual("Joint", s.stored_family("JNT-0001"))
        for kind, fields, extra in (("EXTEND", {"volume": {}}, {}),
                                    ("SUPERSEDE", {"volume": {}}, {"reason": "r"}),
                                    ("INVALIDATE", {}, {"reason": "r"})):
            with self.subTest(op=kind):
                with self.assertRaisesRegex(ContractError, "FAMILY_MISMATCH"):
                    s.apply(_patch(s, "s04", [
                        Op(kind, "FunctionalRegion", "JNT-0001", fields, "p",
                           **extra)], pid="p-%s" % kind))
        self.assertNotIn("volume", s.entities["JNT-0001"])

    def test_AUTH_02_legitimate_mutation_works_and_records_history(self):
        s = _seeded()
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [1, 1, 1]}}, "prov:sup", reason="refined")],
            pid="p2"))
        rec = s.entities["FRG-0001"]
        self.assertEqual([1, 1, 1], rec["volume"]["centre"])
        self.assertEqual("refined", rec["_superseded"][0]["reason"])
        self.assertEqual([0.0, 0.0, 0.0], rec["_superseded"][0]["prior_value"]["centre"])
        self.assertEqual("prov:s03", rec["_provenance"])
        self.assertEqual("prov:s04a", rec["_extensions"][0]["provenance"])

    def test_AUTH_03_premise_change_still_propagates(self):
        s = DesignState("prop")
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-0001", {"basis": "RELATIVE"}, "p")]))
        s.apply(_patch(s, "s03", [
            Op("CREATE", "Body", "BOD-0001",
           {"instance_identity": "b", "role": "STRUCTURE",
            "created_by_stage": "s03", "addresses_obligations": []}, "p"),
            Op("CREATE", "FunctionalRegion", "FRG-0001",
               {"role": "ACCESS", "owning_bodies": ["BOD-0001"]}, "p")], pid="p1"))
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [0, 0, 0]}}, "p",
               premise_refs=["SCL-0001"])], pid="p2"))
        self.assertEqual("STANDING", s.entities["FRG-0001"]["_validity"])
        s.apply(_patch(s, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-0001", {}, "p",
               reason="withdrawn")], pid="p3"))
        dep = s.entities["FRG-0001"]
        self.assertEqual("STALE", dep["_validity"])
        self.assertEqual("SCL-0001", dep["_stale_because"][0]["premise"])
        self.assertEqual([0, 0, 0], dep["volume"]["centre"])       # value untouched
        self.assertEqual([], s.standing("FunctionalRegion"))

    def test_AUTH_a_rejected_patch_changes_nothing(self):
        s = _seeded()
        before = s.state_hash()
        with self.assertRaises(ContractError):
            s.apply(_patch(s, "s04", [
                Op("CREATE", "ReferenceScale", "SCL-0001", {"basis": "R"}, None)],
                pid="p9"))
        self.assertStateUnchanged(s, before)


# =====================================================================
# The excluded region - stated, and tested, so it stays honest
# =====================================================================
class TestSupportedInterfaceBoundary(_Base):

    def test_the_excluded_region_is_reflection_and_is_real(self):
        """Reaching the module-private storage registry is outside the contract.

        It is excluded because it is deliberately implementation-breaking - you
        must import the state module and index its private registry - not because
        it is hard. The exclusion is executable rather than asserted in prose."""
        s = _seeded()
        backing = _reflect(s).entities                     # reflection, by definition
        backing["FRG-0001"]["role"] = "REFLECTED"
        self.assertEqual("REFLECTED", s.entities["FRG-0001"]["role"])

    def test_ordinary_operations_never_yield_the_backing_store(self):
        """The complement: nothing a reader obtains ordinarily IS the storage."""
        s = _seeded()
        backing = _reflect(s).entities
        for obj in (s.entities, s.by_family, s.applied_patches,
                    s.entities["FRG-0001"], s.family("FunctionalRegion")[0],
                    s.counts()):
            self.assertIsNot(obj, backing)
            self.assertIsNot(obj, backing.get("FRG-0001"))
        self.assertIsInstance(s.entities, ReadOnlyTable)

    def test_copy_helpers_are_recursive_in_both_directions(self):
        original = {"a": [{"b": [1, 2]}], "t": (1, [2])}
        for made in (copy_out(original), copy_in(original)):
            self.assertEqual(original, made)
            self.assertIsNot(original["a"], made["a"])
            self.assertIsNot(original["a"][0]["b"], made["a"][0]["b"])
        self.assertIs(thaw, copy_out)


# =====================================================================
# LEAK-A / LEAK-B - the two supported paths that survived 14bed10
# =====================================================================
class TestReadWrapperDoesNotHoldLiveStorage(_Base):
    """A read-only wrapper around a LIVE mutable object is not encapsulation.

    At 14bed10 `state.entities._backing` was the live store, reachable by
    ordinary attribute lookup, and writing through it changed authoritative
    state with no operation, provenance or validation.
    """

    def test_LEAK_A_no_public_read_object_holds_live_storage(self):
        s = _seeded()
        backing = _reflect(s).entities                       # reflection, for the test only
        table = s.entities
        for name in dir(table):
            if name.startswith("__"):
                continue
            value = getattr(table, name, None)
            self.assertIsNot(value, backing,
                             "ReadOnlyTable.%s is the live authoritative store" % name)

    def test_LEAK_A_writing_through_any_wrapper_attribute_cannot_change_state(self):
        s = _seeded()
        before = s.state_hash()
        table = s.entities
        for name in dir(table):
            if name.startswith("__"):
                continue
            value = getattr(table, name, None)
            if isinstance(value, dict) and "FRG-0001" in value:
                value["FRG-0001"]["role"] = "BYPASS_A"
        self.assertEqual("ACCESS", s.entities["FRG-0001"]["role"])
        self.assertStateUnchanged(s, before)

    def test_LEAK_A_the_snapshot_is_detached_and_stable(self):
        s = _seeded()
        table = s.entities
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001",
               {"role": "KEEPOUT"}, "p", reason="r")], pid="pS"))
        self.assertEqual("ACCESS", table["FRG-0001"]["role"])      # a snapshot
        self.assertEqual("KEEPOUT", s.entities["FRG-0001"]["role"])  # a fresh read


class TestNoSecondMutationEntryPoint(_Base):
    """At 14bed10 `state._create(patch, op)` placed an entity with no validation
    and no provenance. Single-underscore is a convention; ordinary method
    invocation is a supported operation."""

    #: Every primitive that writes authoritative storage.
    PRIMITIVES = ("_create", "_extend", "_supersede", "_invalidate",
                  "_propagate", "_merge_premises", "_log")

    def test_LEAK_B_no_mutation_primitive_is_reachable_on_the_state(self):
        s = _seeded()
        for name in self.PRIMITIVES:
            with self.subTest(primitive=name):
                self.assertFalse(hasattr(s, name),
                                 "DesignState.%s is a second write API" % name)

    def test_LEAK_B_apply_is_the_only_public_mutating_callable(self):
        """Inventory the whole public surface and prove exactly one entry mutates."""
        s = _seeded()
        mutating = []
        for name in dir(s):
            if name.startswith("__"):
                continue
            attr = getattr(s, name, None)
            if not callable(attr):
                continue
            probe = _seeded()
            before = probe.state_hash()
            try:
                attr_probe = getattr(probe, name)
                attr_probe()                       # no-arg call; most reads accept it
            except Exception:
                pass
            if probe.state_hash() != before:
                mutating.append(name)
        self.assertEqual([], mutating,
                         "callables that mutate without a patch: %s" % mutating)
        # And the one that does mutate, does so only with a patch.
        before = s.state_hash()
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-0001", {"basis": "RELATIVE"}, "p")],
            pid="pA"))
        self.assertNotEqual(before, s.state_hash())

    def test_LEAK_B_the_primitives_still_require_storage_reflection_to_use(self):
        """They exist at module level, and using one needs the private store."""
        from ver3.assy_v3.state import design_state as ds
        self.assertTrue(callable(ds._create))
        s = _seeded()
        with self.assertRaises(TypeError):
            ds._create(s)                          # cannot be driven from the state alone


class TestPublicObjectGraph(_Base):
    """One general invariant over the whole supported read surface."""

    MUTATOR_NAMES = {"_create", "_extend", "_supersede", "_invalidate",
                     "_propagate", "_merge_premises", "_log", "apply"}

    def test_no_supported_path_yields_live_storage_or_a_writer(self):
        s = _seeded()
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-0001", {"basis": "RELATIVE"}, "p")],
            pid="pG"))
        store = _reflect(s)
        live = {id(store.entities), id(store.by_family), id(store.applied)}
        for rec in store.entities.values():
            live.add(id(rec))

        roots = [s, s.entities, s.by_family, s.applied_patches, s.counts(),
                 s.family("FunctionalRegion"), s.standing("FunctionalRegion"),
                 s.entities["FRG-0001"]]
        seen, queue, problems = set(), list(roots), []
        while queue:
            obj = queue.pop()
            if id(obj) in seen or isinstance(obj, (str, bytes, int, float, bool, type(None))):
                continue
            seen.add(id(obj))
            if id(obj) in live:
                problems.append("live authoritative storage reachable: %r" % type(obj))
                continue
            if isinstance(obj, dict):
                queue.extend(list(obj.values())[:100])
            elif isinstance(obj, (list, tuple, set)):
                queue.extend(list(obj)[:100])
            else:
                for name in dir(obj):
                    if name.startswith("__"):
                        continue
                    try:
                        value = getattr(obj, name)
                    except Exception:
                        continue
                    if callable(value) and name in self.MUTATOR_NAMES and name != "apply":
                        problems.append("mutating callable reachable: %s.%s"
                                        % (type(obj).__name__, name))
                    if id(value) in live:
                        problems.append("live storage via %s.%s"
                                        % (type(obj).__name__, name))
                    if not callable(value):
                        queue.append(value)
        self.assertEqual([], problems)
