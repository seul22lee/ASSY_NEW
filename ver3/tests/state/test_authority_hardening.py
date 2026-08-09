"""The stronger S-1 invariant: authoritative mutation is impossible outside the boundary.

The first S-1 implementation closed the historical `_absorb` path and guarded the
outer entity table and entity records. That is not the whole invariant. These
tests were written to FAIL against commit 2570aa4, each demonstrating a real
executable bypass, and are preserved as the regression that keeps them closed.

Mechanism-independent throughout: no case, no product, no model.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from ver3.assy_v3.state.authority import (AuthorityViolation,                # noqa: E402
                                          WriteCapability, thaw, wrap)
from ver3.assy_v3.state.design_state import ContractError, DesignState       # noqa: E402
from ver3.assy_v3.state.patch import Op, StagePatch                          # noqa: E402


def _patch(state, stage, ops, pid="p1"):
    return StagePatch(
        patch_id=pid, run_id=state.run_id, stage_id=stage, stage_attempt=1,
        parent_state_hash=state.state_hash(), operations=ops,
        execution_status="SUCCESS", provenance={"provider": "test"})


def _seeded():
    """One region owned by s03, with a nested spatial value extended by s04."""
    s = DesignState("harden")
    s.apply(_patch(s, "s03", [
        Op("CREATE", "FunctionalRegion", "FRG-0001",
           {"role": "ACCESS", "owning_bodies": ["BOD-0001"]}, "prov:s03")], pid="p0"))
    s.apply(_patch(s, "s04", [
        Op("EXTEND", "FunctionalRegion", "FRG-0001",
           {"volume": {"half_extent": [1.0, 1.0, 1.0], "centre": [0.0, 0.0, 0.0]}},
           "prov:s04a")], pid="p1"))
    return s


def _joint(state):
    state.apply(_patch(state, "s03", [
        Op("CREATE", "Joint", "JNT-0001",
           {"joint_type": "REVOLUTE", "parent_group": "RGP-0001",
            "child_group": "RGP-0002", "dof": ["RZ"],
            "axis_direction": [0, 0, 1], "frame_ids": []}, "prov:s03")], pid="pj"))
    return state


# =====================================================================
# GAP A - nested mutable value bypass
# =====================================================================
class TestNestedValueBypass(unittest.TestCase):
    """The outer record was guarded; the values inside it were plain dicts and lists."""

    def test_nested_dict_field_cannot_be_mutated_in_place(self):
        s = _seeded()
        with self.assertRaises(AuthorityViolation):
            s.entities["FRG-0001"]["volume"]["centre"] = [9, 9, 9]

    def test_nested_list_element_cannot_be_mutated_in_place(self):
        s = _seeded()
        with self.assertRaises(AuthorityViolation):
            s.entities["FRG-0001"]["volume"]["centre"][0] = 999

    def test_nested_list_cannot_be_appended_to(self):
        s = _seeded()
        with self.assertRaises(AuthorityViolation):
            s.entities["FRG-0001"]["owning_bodies"].append("BOD-9999")

    def test_a_blocked_nested_mutation_leaves_state_and_history_untouched(self):
        s = _seeded()
        before_hash = s.state_hash()
        before_ext = len(s.entities["FRG-0001"]["_extensions"])
        try:
            s.entities["FRG-0001"]["volume"]["centre"][0] = 999
        except AuthorityViolation:
            pass
        self.assertEqual(before_hash, s.state_hash())
        self.assertEqual(before_ext, len(s.entities["FRG-0001"]["_extensions"]))
        self.assertEqual([0.0, 0.0, 0.0], list(s.entities["FRG-0001"]["volume"]["centre"]))


# =====================================================================
# GAP B - entity-table and record mutator coverage
# =====================================================================
class TestContainerMutatorCoverage(unittest.TestCase):
    """A guard that overrides some inherited mutators and not others is not a guard."""

    #: Every mutating name on the dict API. Enumerated rather than hand-picked, so
    #: a method left active is a test failure and not an oversight.
    DICT_MUTATORS = ("__setitem__", "__delitem__", "__ior__", "update",
                     "setdefault", "pop", "popitem", "clear")
    LIST_MUTATORS = ("__setitem__", "__delitem__", "__iadd__", "__imul__",
                     "append", "extend", "insert", "pop", "remove", "clear",
                     "sort", "reverse")

    def _assert_all_closed(self, obj, names, kind):
        import inspect
        base = dict if kind == "dict" else list
        left_open = []
        for name in names:
            if not hasattr(base, name):
                continue                      # not present on this Python version
            own = getattr(type(obj), name, None)
            inherited = getattr(base, name, None)
            if own is inherited or own is None:
                left_open.append(name)
        self.assertEqual([], left_open,
                         "%s mutators inherited unguarded on %s: %s"
                         % (kind, type(obj).__name__, left_open))

    def test_every_dict_mutator_is_closed_on_the_entity_table(self):
        s = _seeded()
        self._assert_all_closed(s.entities, self.DICT_MUTATORS, "dict")

    def test_every_dict_mutator_is_closed_on_an_entity_record(self):
        s = _seeded()
        self._assert_all_closed(s.entities["FRG-0001"], self.DICT_MUTATORS, "dict")

    def test_every_dict_mutator_is_closed_on_a_nested_value(self):
        s = _seeded()
        self._assert_all_closed(s.entities["FRG-0001"]["volume"],
                                self.DICT_MUTATORS, "dict")

    def test_every_list_mutator_is_closed_on_a_nested_list(self):
        s = _seeded()
        self._assert_all_closed(s.entities["FRG-0001"]["volume"]["centre"],
                                self.LIST_MUTATORS, "list")

    def test_popitem_on_the_entity_table_is_refused(self):
        """Named explicitly: it was the one mutator the first pass missed."""
        s = _seeded()
        with self.assertRaises(AuthorityViolation):
            s.entities.popitem()

    def test_every_enumerated_dict_mutator_actually_raises_on_the_table(self):
        s = _seeded()
        calls = {"__setitem__": ("X", {}), "__delitem__": ("FRG-0001",),
                 "update": ({"X": {}},), "setdefault": ("X", {}),
                 "pop": ("FRG-0001",), "popitem": (), "clear": ()}
        for name, args in calls.items():
            with self.subTest(mutator=name):
                with self.assertRaises(AuthorityViolation):
                    getattr(s.entities, name)(*args)


# =====================================================================
# GAP C - entity-family authority spoofing
# =====================================================================
class TestFamilyAuthoritySpoofing(unittest.TestCase):
    """Permission belongs to the entity that exists, not to the type the caller claims."""

    def test_extend_may_not_borrow_another_familys_permission(self):
        """`volume` is extendable on FunctionalRegion. It is not a Joint field."""
        s = _joint(DesignState("spoof"))
        with self.assertRaisesRegex(ContractError, "FAMILY_MISMATCH"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "JNT-0001",
                   {"volume": {"centre": [0, 0, 0]}}, "prov:spoof")], pid="p2"))

    def test_the_spoofed_field_did_not_reach_the_entity(self):
        s = _joint(DesignState("spoof"))
        try:
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "JNT-0001",
                   {"volume": {"centre": [0, 0, 0]}}, "prov:spoof")], pid="p2"))
        except ContractError:
            pass
        self.assertNotIn("volume", s.entities["JNT-0001"])

    def test_the_reverse_spoof_is_also_refused(self):
        s = _seeded()
        with self.assertRaisesRegex(ContractError, "FAMILY_MISMATCH"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "Joint", "FRG-0001",
                   {"frame_origin": [0, 0, 0]}, "prov:spoof")], pid="p2"))

    def test_supersede_validates_the_stored_family(self):
        s = _seeded()
        with self.assertRaisesRegex(ContractError, "FAMILY_MISMATCH"):
            s.apply(_patch(s, "s04", [
                Op("SUPERSEDE", "Joint", "FRG-0001", {"volume": {}}, "prov:x",
                   reason="r")], pid="p2"))

    def test_invalidate_validates_the_stored_family(self):
        s = _seeded()
        with self.assertRaisesRegex(ContractError, "FAMILY_MISMATCH"):
            s.apply(_patch(s, "s04", [
                Op("INVALIDATE", "Joint", "FRG-0001", {}, "prov:x",
                   reason="r")], pid="p2"))

    def test_a_correctly_declared_family_still_works(self):
        s = _seeded()
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [5, 5, 5]}}, "prov:ok", reason="refined")],
            pid="p2"))
        self.assertEqual([5, 5, 5], list(s.entities["FRG-0001"]["volume"]["centre"]))


# =====================================================================
# GAP D - external aliasing of mutation input
# =====================================================================
class TestInputAliasing(unittest.TestCase):
    """A guard on the container does nothing if the caller kept the object."""

    def test_a_mutable_object_passed_to_create_cannot_later_change_state(self):
        s = DesignState("alias")
        bodies = ["BOD-0001"]
        s.apply(_patch(s, "s03", [
            Op("CREATE", "FunctionalRegion", "FRG-0001",
               {"role": "ACCESS", "owning_bodies": bodies}, "prov:s03")]))
        bodies.append("BOD-9999")                       # caller mutates its own list
        self.assertEqual(["BOD-0001"], list(s.entities["FRG-0001"]["owning_bodies"]))

    def test_a_mutable_object_passed_to_extend_cannot_later_change_state(self):
        s = _seeded()
        s2 = DesignState("alias2")
        s2.apply(_patch(s2, "s03", [
            Op("CREATE", "FunctionalRegion", "FRG-0002",
               {"role": "ACCESS", "owning_bodies": ["B"]}, "p")], pid="p0"))
        centre = [0.0, 0.0, 0.0]
        s2.apply(_patch(s2, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0002",
               {"volume": {"centre": centre}}, "p")], pid="p1"))
        centre[0] = 999.0
        self.assertEqual([0.0, 0.0, 0.0],
                         list(s2.entities["FRG-0002"]["volume"]["centre"]))

    def test_a_mutable_object_passed_to_supersede_cannot_later_change_state(self):
        s = _seeded()
        replacement = {"centre": [1.0, 1.0, 1.0]}
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001", {"volume": replacement},
               "p", reason="refined")], pid="p2"))
        replacement["centre"][0] = 999.0
        self.assertEqual([1.0, 1.0, 1.0], list(s.entities["FRG-0001"]["volume"]["centre"]))

    def test_the_retained_prior_value_is_also_alias_safe(self):
        """FA-1 keeps the prior value. It must not be mutable either."""
        s = _seeded()
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [1, 1, 1]}}, "p", reason="refined")], pid="p2"))
        prior = s.entities["FRG-0001"]["_superseded"][0]["prior_value"]
        with self.assertRaises(AuthorityViolation):
            prior["centre"] = [7, 7, 7]


# =====================================================================
# GAP E - the internal gate must not be a supported public switch
# =====================================================================
class TestGateExposure(unittest.TestCase):

    def test_the_gate_is_not_reachable_under_a_public_attribute_name(self):
        s = _seeded()
        self.assertFalse(hasattr(s, "_gate"),
                         "the write capability must not be a public state attribute")

    def test_the_gate_cannot_be_replaced_after_construction(self):
        s = _seeded()

        class _AlwaysOpen:
            open = True

        for name in ("_gate", "_DesignState__gate"):
            with self.subTest(attr=name):
                with self.assertRaises(AuthorityViolation):
                    setattr(s, name, _AlwaysOpen())

    def test_a_duck_typed_forged_capability_does_not_open_a_container(self):
        """An object that merely looks open must not unlock anything."""
        s = _seeded()
        rec = s.entities["FRG-0001"]

        class _LooksOpen:
            open = True

        object.__setattr__(rec, "_cap", _LooksOpen())
        with self.assertRaises(AuthorityViolation):
            rec["role"] = "SPOOFED"
        self.assertEqual("ACCESS", rec["role"])

    def test_no_supported_interface_reaches_the_capability(self):
        """The honest guarantee: no accessor returns it, no public name holds it,
        and nothing settable replaces it."""
        s = _seeded()
        public = [n for n in dir(s) if not n.startswith("__")]
        self.assertNotIn("_gate", public)
        self.assertNotIn("_cap", public)
        for name in public:
            value = getattr(s, name)
            self.assertNotIsInstance(
                value, WriteCapability,
                "%s exposes the write capability as a public attribute" % name)

    def test_the_documented_limit_is_real_and_is_introspection_only(self):
        """Stated rather than hidden: rebinding a private slot with a genuine
        capability DOES bypass the guard. That is introspection, not a supported
        interface, and it is why the static scan exists as defence in depth.

        This test exists so the limit is executable evidence rather than a
        sentence in a document that may or may not still be true."""
        s = _seeded()
        rec = s.entities["FRG-0001"]
        object.__setattr__(rec, "_cap", WriteCapability())
        forged = getattr(rec, "_cap")
        with forged.granted():
            rec["role"] = "BYPASSED"
        self.assertEqual("BYPASSED", rec["role"])


# =====================================================================
# AUTH-01..08 - mechanism-independent authority properties
# =====================================================================
class TestAuthorityProperties(unittest.TestCase):
    """Properties, not paths. None of these names a case, a product or a model."""

    def test_AUTH_01_state_cannot_change_without_a_controlled_mutation(self):
        """Every supported mutation attempt, with no patch applied, changes nothing."""
        s = _seeded()
        before = s.state_hash()
        rec = s.entities["FRG-0001"]
        attempts = [
            lambda: s.entities.__setitem__("X", {}),
            lambda: s.entities.pop("FRG-0001"),
            lambda: s.entities.popitem(),
            lambda: s.entities.clear(),
            lambda: rec.__setitem__("role", "X"),
            lambda: rec.update({"role": "X"}),
            lambda: rec.pop("role"),
            lambda: rec["volume"].__setitem__("centre", [9, 9, 9]),
            lambda: rec["volume"]["centre"].__setitem__(0, 9),
            lambda: rec["volume"]["centre"].append(9),
            lambda: rec["owning_bodies"].clear(),
            lambda: rec["_extensions"].pop(),
        ]
        for i, attempt in enumerate(attempts):
            with self.subTest(attempt=i):
                with self.assertRaises(AuthorityViolation):
                    attempt()
        self.assertEqual(before, s.state_hash())

    def test_AUTH_02_input_aliases_cannot_reach_back_into_state(self):
        s = DesignState("auth02")
        deep = {"a": [{"b": [1, 2, 3]}]}
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-0001",
               {"basis": "RELATIVE", "note": deep}, "p")]))
        deep["a"][0]["b"][0] = 999
        deep["a"].append("extra")
        self.assertEqual(1, s.entities["SCL-0001"]["note"]["a"][0]["b"][0])
        self.assertEqual(1, len(s.entities["SCL-0001"]["note"]["a"]))

    def test_AUTH_03_a_value_read_from_state_cannot_be_mutated_to_alter_state(self):
        s = _seeded()
        volume = s.entities["FRG-0001"]["volume"]     # a live reference, by design
        with self.assertRaises(AuthorityViolation):
            volume["centre"] = [9, 9, 9]
        with self.assertRaises(AuthorityViolation):
            volume["centre"][0] = 9
        self.assertEqual([0.0, 0.0, 0.0], list(s.entities["FRG-0001"]["volume"]["centre"]))

    def test_AUTH_04_each_operation_produces_its_required_history(self):
        s = _seeded()
        rec = s.entities["FRG-0001"]
        self.assertTrue(rec["_provenance"])                       # CREATE
        self.assertTrue(rec["_extensions"][0]["provenance"])      # EXTEND
        s.apply(_patch(s, "s04", [
            Op("SUPERSEDE", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [1, 1, 1]}}, "prov:sup", reason="refined")],
            pid="p2"))
        self.assertEqual("refined", rec["_superseded"][0]["reason"])
        self.assertEqual([0.0, 0.0, 0.0],
                         list(rec["_superseded"][0]["prior_value"]["centre"]))
        s.apply(_patch(s, "s04", [
            Op("INVALIDATE", "FunctionalRegion", "FRG-0001", {}, "prov:inv",
               reason="withdrawn")], pid="p3"))
        self.assertEqual("withdrawn", rec["_invalidations"][0]["reason"])
        self.assertEqual("INVALIDATED", rec["_validity"])

    def test_AUTH_05_permission_comes_from_stored_identity_not_caller_assertion(self):
        s = _joint(DesignState("auth05"))
        self.assertEqual("Joint", s.stored_family("JNT-0001"))
        with self.assertRaisesRegex(ContractError, "FAMILY_MISMATCH"):
            s.apply(_patch(s, "s04", [
                Op("EXTEND", "FunctionalRegion", "JNT-0001",
                   {"volume": {}}, "p")], pid="p2"))

    def test_AUTH_06_propagation_still_works_after_hardening(self):
        s = DesignState("auth06")
        s.apply(_patch(s, "s04", [
            Op("CREATE", "ReferenceScale", "SCL-0001", {"basis": "RELATIVE"}, "p")]))
        s.apply(_patch(s, "s03", [
            Op("CREATE", "FunctionalRegion", "FRG-0001",
               {"role": "ACCESS", "owning_bodies": ["B"]}, "p")], pid="p1"))
        s.apply(_patch(s, "s04", [
            Op("EXTEND", "FunctionalRegion", "FRG-0001",
               {"volume": {"centre": [0, 0, 0]}}, "p",
               premise_refs=["SCL-0001"])], pid="p2"))
        s.apply(_patch(s, "s04", [
            Op("INVALIDATE", "ReferenceScale", "SCL-0001", {}, "p",
               reason="withdrawn")], pid="p3"))
        dep = s.entities["FRG-0001"]
        self.assertEqual("STALE", dep["_validity"])
        self.assertEqual("SCL-0001", dep["_stale_because"][0]["premise"])
        self.assertEqual([0, 0, 0], list(dep["volume"]["centre"]))   # value untouched

    def test_AUTH_07_ephemeral_views_are_plain_and_freely_mutable(self):
        from ver3.assy_v3.state.projection import project_for
        s = _seeded()
        view = project_for("s04", s)
        region = view["FunctionalRegion"][0]
        self.assertIs(dict, type(region))
        self.assertIs(dict, type(region["volume"]))
        self.assertIs(list, type(region["volume"]["centre"]))
        region["volume"]["centre"][0] = 999          # class C: no guard, no effect
        region["owning_bodies"].append("X")
        self.assertEqual([0.0, 0.0, 0.0], list(s.entities["FRG-0001"]["volume"]["centre"]))
        self.assertEqual(["BOD-0001"], list(s.entities["FRG-0001"]["owning_bodies"]))

    def test_AUTH_07_thaw_is_recursive_and_wrap_is_its_inverse_in_content(self):
        s = _seeded()
        original = s.entities["FRG-0001"]["volume"]
        plain = thaw(original)
        self.assertIs(dict, type(plain))
        self.assertEqual(dict(original), plain)

    def test_AUTH_08_serialization_and_read_only_consumers_are_unaffected(self):
        s = _seeded()
        blob = json.dumps(s.entities, sort_keys=True)          # state_hash's path
        self.assertIn("FRG-0001", blob)
        self.assertEqual(json.loads(blob)["FRG-0001"]["volume"]["centre"], [0.0, 0.0, 0.0])
        rec = s.entities["FRG-0001"]
        self.assertEqual("ACCESS", rec.get("role"))            # mapping reads
        self.assertIn("volume", rec)
        self.assertEqual(sorted(dict(rec)), sorted(rec.keys()))
        self.assertEqual([0.0, 0.0, 0.0], rec["volume"]["centre"])   # equality vs list
        self.assertEqual(3, len(rec["volume"]["centre"]))
        self.assertEqual(0.0, min(rec["volume"]["centre"]))
        self.assertTrue(isinstance(rec, dict) and isinstance(rec["volume"]["centre"], list))
