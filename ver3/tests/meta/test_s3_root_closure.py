"""One consumer-context boundary, one reference authority, one responsibility id.

Impl S-3 owns whether a consumer can reliably RECEIVE what its responsibility says
it needs, without silent omission and without a competing path. It does not own
proving that the engineering relationships between those facts are established -
that belongs to the producers and to later assurance, and the residual registry
says which step owns which.
"""
from __future__ import annotations

import ast
import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_PROD = os.path.join(_REPO, "ver3", "assy_v3")
_TOOLS = os.path.join(_REPO, "ver3", "tools")

import ver3.assy_v3.view.consumer_view as cv                           # noqa: E402
from ver3.assy_v3.stages.base import Stage                             # noqa: E402
from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly, S03TopologyAndMobility)
from ver3.assy_v3.stages.s04_envelope_and_motion import (              # noqa: E402
    S04AEnvelopeAndReach, S04BPlacementAndMotion)
from ver3.assy_v3.state.design_state import (Contracts, ContractError,  # noqa: E402
                                             DesignState)
from ver3.assy_v3.state.patch import Op, StagePatch                     # noqa: E402
from ver3.assy_v3.view import consumer_view_for                         # noqa: E402

CONSUMERS = (S02ObligationAndCandidates, S03TopologyAndMobility,
             S03BMobilityAndAssembly, S04AEnvelopeAndReach, S04BPlacementAndMotion)


def _py(root):
    for base, dirs, names in os.walk(root):
        if "__pycache__" in base:
            continue
        for n in sorted(names):
            if n.endswith(".py"):
                yield os.path.join(base, n), open(os.path.join(base, n)).read()


class _Base(_fixtures.StateBuilder, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def patch(self, s, stage, ops):
        return StagePatch(patch_id="p%d" % len(s.applied_patches), run_id=s.run_id,
                          stage_id=stage, stage_attempt=1,
                          parent_state_hash=s.state_hash(), operations=ops,
                          execution_status="SUCCESS", provenance={"provider": "t"})


# =====================================================================
# Source-A availability timing
# =====================================================================
class TestSourceAvailabilityTiming(_Base):
    """A stage's own output referring to its own output is not a pre-stage input.

    s02 emits a candidate that addresses an obligation s02 emitted in the same
    patch. Reading that reference as "the obligation must be in the view before
    s02 runs" asks s02 to have already done its own work, and reported its
    upstream absent while it was about to create it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(os.path.join(_REPO, "ver3", "contracts",
                               "STAGE_RESPONSIBILITY_CONTRACT.yaml")) as fh:
            cls.resp = yaml.safe_load(fh)

    def keys(self, stage_id):
        return {r.key for r in cv.derive_source_a(stage_id, self.c, self.resp)}

    def test_SA_TIME_01_a_pre_existing_referent_is_still_required(self):
        keys = self.keys("s02")
        self.assertTrue(
            any("-> Requirement" in k for k in keys),
            "s02 does not author requirements, so its obligations still need them")

    def test_SA_TIME_02_a_co_produced_referent_is_not_required_beforehand(self):
        keys = self.keys("s02")
        for co in ("-> Obligation", "-> Candidate", "-> LoadCase"):
            self.assertFalse(any(k.endswith(co) for k in keys),
                             "s02 demands %s before running, and s02 creates it" % co)

    def test_SA_TIME_03_same_patch_cross_reference_validates(self):
        s = DesignState(run_id="copro")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        obl = self._fields_for(s, self.c, "s02", "Obligation",
                               {"derived_from_requirements": ["REQ-1"]})
        cand = self._fields_for(s, self.c, "s02", "Candidate",
                                {"principle": {"h": "f"},
                                 "addresses_obligations": ["OBL-1"],
                                 "obligations_created": []})
        s.apply(self.patch(s, "s02", [
            Op("CREATE", "Obligation", "OBL-1", obl, "p"),
            Op("CREATE", "Candidate", "CND-1", cand, "p")]))
        self.assertEqual(["OBL-1"], s.entities["CND-1"]["addresses_obligations"])

    def test_SA_TIME_03b_order_within_the_patch_does_not_matter(self):
        s = DesignState(run_id="order")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        obl = self._fields_for(s, self.c, "s02", "Obligation",
                               {"derived_from_requirements": ["REQ-1"]})
        cand = self._fields_for(s, self.c, "s02", "Candidate",
                                {"principle": {"h": "f"},
                                 "addresses_obligations": ["OBL-1"],
                                 "obligations_created": []})
        s.apply(self.patch(s, "s02", [
            Op("CREATE", "Candidate", "CND-1", cand, "p"),
            Op("CREATE", "Obligation", "OBL-1", obl, "p")]))
        self.assertTrue(s.has_entity("CND-1"))

    def test_SA_TIME_04_a_referent_in_neither_place_fails(self):
        s = DesignState(run_id="dangle")
        self.assertFalse(self.c.reference_spec("RigidGroup", "body")["resolvable"],
                         "the field under test must be one that MUST resolve")
        fields = self._fields_for(s, self.c, "s03", "RigidGroup",
                                  {"body": "BOD-NOWHERE"})
        with self.assertRaises(ContractError) as caught:
            s.apply(self.patch(s, "s03", [
                Op("CREATE", "RigidGroup", "RGP-1", fields, "p")]))
        self.assertIn("DANGLING_REF", str(caught.exception))

    def test_SA_TIME_05_the_distinction_names_no_stage_and_no_family(self):
        import inspect
        src = inspect.getsource(cv.derive_source_a)
        named = [f for f in self.c.families if re.search(r"['\"]%s['\"]" % f, src)]
        self.assertEqual([], named, "Source A names families: %s" % named)
        self.assertIsNone(re.search(r"['\"]s0\d", src), "Source A names a stage")

    def test_SA_TIME_06_a_future_co_producing_pair_needs_no_resolver_change(self):
        """A stage that authors two mutually-referencing families, invented here."""
        import copy
        resp = copy.deepcopy(self.resp)
        resp["stages"]["s03a"]["permitted_output_semantics"] = ["Joint", "RigidGroup"]
        keys = {r.key for r in cv.derive_source_a("s03a", self.c, resp)}
        self.assertFalse(any(k.endswith("-> RigidGroup") for k in keys),
                         "a co-produced pair is still demanded up front")


# =====================================================================
# One canonical reference authority
# =====================================================================
class TestCanonicalReferenceAuthority(_Base):

    def test_REF_CANON_01_a_reference_not_named_like_one_is_enforced(self):
        """`body`, `parent_group`, `at_interface` end in no suffix and were in no
        allowlist, so the old name-shape rule saw none of them."""
        for family, field in (("RigidGroup", "body"), ("Joint", "parent_group"),
                              ("PhysicalInteraction", "at_interface")):
            spec = self.c.reference_spec(family, field)
            self.assertIsNotNone(spec, "%s.%s" % (family, field))
            self.assertFalse(field.endswith(("_id", "_ids", "_refs")))
        s = DesignState(run_id="canon")
        fields = self._fields_for(s, self.c, "s03", "Joint",
                                  {"parent_group": "RGP-ABSENT",
                                   "child_group": "RGP-ABSENT"})
        with self.assertRaises(ContractError) as caught:
            s.apply(self.patch(s, "s03", [
                Op("CREATE", "Joint", "JNT-1", fields, "p")]))
        self.assertIn("DANGLING_REF", str(caught.exception))

    def test_REF_CANON_02_a_referent_of_the_wrong_family_fails(self):
        s = DesignState(run_id="fam")
        self.add(s, "s03", "Body", "BOD-1")
        fields = self._fields_for(s, self.c, "s03", "PhysicalInteraction",
                                  {"at_interface": "BOD-1"})
        with self.assertRaises(ContractError) as caught:
            s.apply(self.patch(s, "s03", [
                Op("CREATE", "PhysicalInteraction", "PI-1", fields, "p")]))
        self.assertIn("REFERENCE_FAMILY", str(caught.exception))

    def test_REF_CANON_03_cardinality_one_rejects_a_list_of_referents(self):
        s = DesignState(run_id="card")
        self.add(s, "s03", "Body", "BOD-1")
        self.add(s, "s03", "Interface", "IF-1", bodies=["BOD-1"])
        self.add(s, "s03", "Interface", "IF-2", bodies=["BOD-1"])
        fields = self._fields_for(s, self.c, "s03", "PhysicalInteraction",
                                  {"at_interface": ["IF-1", "IF-2"]})
        with self.assertRaises(ContractError) as caught:
            s.apply(self.patch(s, "s03", [
                Op("CREATE", "PhysicalInteraction", "PI-1", fields, "p")]))
        self.assertIn("CARDINALITY", str(caught.exception))

    def test_REF_CANON_04_a_reference_shaped_name_gains_no_authority(self):
        """Spelling is not a declaration. A field the contract does not declare a
        reference must not become one because it ends in `_id`."""
        self.assertIsNone(self.c.reference_spec("Requirement", "statement_id"))
        s = DesignState(run_id="spell")
        fields = self._fields_for(s, self.c, "s01", "Requirement",
                                  {"quantity_class": "BAND"})
        fields["note_id"] = "NOT-AN-ENTITY"
        s.apply(self.patch(s, "s01", [
            Op("CREATE", "Requirement", "REQ-1", fields, "p")]))
        self.assertTrue(s.has_entity("REQ-1"))

    def test_REF_CANON_05_both_boundaries_ask_the_same_question(self):
        """The write boundary and the consumer graph read one declaration."""
        write = os.path.join(_PROD, "state", "design_state.py")
        src = open(write).read()
        self.assertIn("reference_spec", src)
        self.assertNotIn('endswith(("_id", "_ids", "_refs"))', src,
                         "the name-shape authority is back")
        graph = __import__("inspect").getsource(cv._refs_of)
        self.assertIn("field_semantics", graph + src)

    def test_REF_CANON_06_resolvable_is_read_the_way_the_contract_defines_it(self):
        """`field_semantics_rules.reference`: "`resolvable` says whether an
        UNRESOLVED VALUE IS LEGAL; the default is false, so a dangling reference is
        a defect rather than a style." So false REQUIRES resolution.

        Asserted as RUNTIME BEHAVIOUR in both directions, not by counting which
        values the corpus happens to use. After the S-4 exit audit no field
        declares `true` at all - every reference a producer authors names
        something that exists, or is created beside it in the same patch - so the
        `true` branch is exercised against a synthetic declaration rather than
        being left untested.
        """
        import copy
        s = DesignState(run_id="soft")
        # false: the declared default. A named referent must exist.
        self.assertFalse(self.c.reference_spec("RigidGroup", "body")["resolvable"])
        fields = self._fields_for(s, self.c, "s03", "RigidGroup",
                                  {"body": "BOD-LATER"})
        with self.assertRaises(ContractError) as caught:
            s.apply(self.patch(s, "s03", [
                Op("CREATE", "RigidGroup", "RGP-1", fields, "p")]))
        self.assertIn("DANGLING_REF", str(caught.exception))

        # true: tolerated, and only because the declaration says so.
        class _Permissive:
            def __init__(self, base):
                self._b = base

            def __getattr__(self, name):
                return getattr(self._b, name)

            def reference_spec(self, family, field):
                spec = self._b.reference_spec(family, field)
                if spec and family == "RigidGroup" and field == "body":
                    spec = dict(spec, resolvable=True)
                return spec

        s2 = DesignState(run_id="permissive", contracts=_Permissive(self.c))
        s2.apply(self.patch(s2, "s03", [
            Op("CREATE", "RigidGroup", "RGP-1",
               self._fields_for(s2, self.c, "s03", "RigidGroup",
                                {"body": "BOD-LATER"}), "p")]))
        self.assertTrue(s2.has_entity("RGP-1"))

        # Structure is never optional, whatever the declaration says.
        bad = self._fields_for(s, self.c, "s03", "PhysicalInteraction",
                               {"at_interface": "the interface between the parts"})
        with self.assertRaises(ContractError) as caught:
            s.apply(self.patch(s, "s03", [
                Op("CREATE", "PhysicalInteraction", "PI-2", bad, "p")]))
        self.assertIn("REFERENCE_NOT_AN_ID", str(caught.exception))


# =====================================================================
# One consumer boundary
# =====================================================================
class TestOneConsumerBoundary(_Base):

    def test_S3ROOT_01_02_03_05_every_consumer_reads_the_view(self):
        for stage in CONSUMERS:
            src = __import__("inspect").getsource(stage.prompt)
            self.assertTrue(
                'inputs["consumer_view"]' in src or 'inputs["mechanism"]' in src,
                "%s builds its prompt from something else" % stage.__name__)

    def test_S3ROOT_04_11_no_runner_assembles_engineering_context(self):
        """A raw family read whose result reaches a stage's inputs is a second
        semantic channel. Control identity is not: an id is not a fact."""
        offences = []
        for path, src in _py(_TOOLS):
            for node in ast.walk(ast.parse(src)):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                if not (isinstance(fn, ast.Attribute)
                        and fn.attr in ("family", "standing", "entities")):
                    continue
                # Legitimate: control, bookkeeping, deterministic derivation.
                offences.append((os.path.basename(path), node.lineno, fn.attr))
        prompts = [o for o in offences if o[0] == "run_window2.py"
                   and o[2] in ("family", "standing")]
        # Whatever remains must not flow into a stage's inputs: assert the two
        # keys a stage reads are never built from a raw read in the same call.
        src = open(os.path.join(_TOOLS, "run_window2.py")).read()
        for key in ('"consumer_view":', '"mechanism":'):
            for line in [l for l in src.splitlines() if key in l]:
                self.assertNotIn("state.family", line, line)
                self.assertNotIn("state.standing", line, line)
        self.assertNotIn('"demands"', src, "the raw demands channel is back")
        self.assertTrue(prompts is not None)

    def test_S3ROOT_06_candidate_identity_is_explicit_and_structural(self):
        self.assertEqual(["CND-1"],
                         S03TopologyAndMobility().invocation_premises(
                             {"candidate": {"entity_id": "CND-1"}}))
        self.assertEqual(["CND-1"],
                         S03BMobilityAndAssembly().invocation_premises(
                             {"candidate": "CND-1"}))
        ctx = cv.InvocationContext(branch="CND-1")
        self.assertEqual("CND-1", ctx.branch)
        self.assertEqual({}, ctx.anchors, "identity, not an engineering payload")

    def test_S3ROOT_09_no_production_projection_path_remains(self):
        self.assertFalse(os.path.exists(
            os.path.join(_PROD, "state", "projection.py")))
        for path, src in list(_py(_PROD)) + list(_py(_TOOLS)):
            self.assertNotIn("project_for", src, path)

    def test_S3ROOT_10_no_replacement_context_whitelist_appears(self):
        pattern = re.compile(
            r"^([A-Z_]*(?:CONTEXT|NEEDS|OWNED|FAMILIES)[A-Z_]*) *= *[\[({]", re.M)
        #: INV-002 is not a context table. It names the families that carry the
        #: REQUEST TEXT, so a stage after s01 cannot reinterpret the source - a
        #: prohibition, not a selection, and the boundary asserts it rather than
        #: selecting by it.
        allowed = {"SOURCE_TEXT_FAMILIES"}
        for path, src in list(_py(_PROD)) + list(_py(_TOOLS)):
            hits = [h for h in pattern.findall(src) if h not in allowed]
            self.assertEqual([], hits, "%s declares a context family table" % path)

    def test_S3ROOT_12_no_positional_context_truncation_remains(self):
        for path, src in _py(_PROD):
            for m in re.finditer(r"\[:\s*(\d{3,})\s*\]", src):
                self.fail("%s slices context at %s" % (path, m.group(1)))

    def test_S3ROOT_18_unknown_responsibility_fails_closed(self):
        s = DesignState(run_id="unknown")
        for bad in ("s03", "s04", "s99"):
            with self.assertRaises(cv.UnknownConsumer):
                consumer_view_for(bad, s)

    def test_S3ROOT_18b_authority_and_responsibility_are_distinct(self):
        self.assertEqual(("s02", "s02"),
                         (S02ObligationAndCandidates.stage_id,
                          S02ObligationAndCandidates.responsibility_id()))
        self.assertEqual(("s03", "s03a"),
                         (S03TopologyAndMobility.stage_id,
                          S03TopologyAndMobility.responsibility_id()))
        self.assertEqual(("s03", "s03b"),
                         (S03BMobilityAndAssembly.stage_id,
                          S03BMobilityAndAssembly.responsibility_id()))
        self.assertEqual(("s04", "s04a"),
                         (S04AEnvelopeAndReach.stage_id,
                          S04AEnvelopeAndReach.responsibility_id()))
        self.assertEqual(("s04", "s04b"),
                         (S04BPlacementAndMotion.stage_id,
                          S04BPlacementAndMotion.responsibility_id()))
        self.assertEqual("sXX", Stage.responsibility_id())

    def test_S3ROOT_18c_no_runner_keeps_its_own_pass_to_contract_map(self):
        src = open(os.path.join(_TOOLS, "run_window2.py")).read()
        for literal in ('"s03a"', '"s03b"', "'s03a'", "'s03b'"):
            self.assertNotIn("consumer_view(%s" % literal, src)
        self.assertIn("consumer_view(state", src)

    def test_S3ROOT_21_22_no_benchmark_or_model_logic_in_the_boundary(self):
        for path, src in _py(os.path.join(_PROD, "view")):
            self.assertIsNone(re.search(r"BM-\d|PRB-\d|deepseek|gpt-|claude", src,
                                        re.I), path)

    def test_S3ROOT_23_the_view_is_deterministic(self):
        s = DesignState(run_id="det")
        self.add(s, "s01", "Requirement", "REQ-1", quantity_class="BAND")
        a = cv.render(consumer_view_for("s02", s))
        b = cv.render(consumer_view_for("s02", s))
        self.assertEqual(a, b)


# =====================================================================
# Truncation, budget, and the taxonomy
# =====================================================================
class TestTruncationAndBudget(_Base):

    def big_view(self, n=400):
        s = DesignState(run_id="big")
        for i in range(n):
            self.add(s, "s01", "Requirement", "REQ-%04d" % i, quantity_class="BAND")
        # Sorts last: exactly what a positional cut removes.
        self.add(s, "s01", "Scenario", "SCN-LAST")
        return s, consumer_view_for("s02", s)

    def test_S3ROOT_13_the_24000_class_defect_is_behaviourally_resolved(self):
        s, view = self.big_view()
        rendered = cv.render(view)
        self.assertGreater(len(rendered), 24000,
                           "the fixture is not large enough to reproduce the cut")
        old = rendered[:24000]
        self.assertNotIn("SCN-LAST", old,
                         "the old renderer would not have lost it, so this proves "
                         "nothing")
        self.assertIn("SCN-LAST", rendered)
        self.assertIn("SCN-LAST", {e["entity_id"] for e in view.entities})

    def test_S3ROOT_14_required_overflow_is_explicit_not_silent(self):
        s, _v = self.big_view()
        squeezed = consumer_view_for("s02", s, budget_chars=2000)
        self.assertEqual(cv.ViewStatus.BUDGET_INSUFFICIENT, squeezed.status)
        self.assertTrue(any(o.get("rule", "").startswith("required minimum")
                            for o in squeezed.omitted))

    def test_S3ROOT_14b_contributory_context_goes_before_required(self):
        s, view = self.big_view(n=40)
        required = {t["entity_id"] for t in view.traces
                    if t["source"] != cv.Source.CONTRIBUTORY_CONTEXT.value}
        roomy = consumer_view_for("s02", s, budget_chars=len(cv.render(view)))
        self.assertTrue(required <= {e["entity_id"] for e in roomy.entities})

    def test_S3ROOT_15_missing_upstream_and_projection_failure_stay_apart(self):
        empty = DesignState(run_id="empty")
        v = consumer_view_for("s02", empty)
        verdicts = {a["verdict"] for a in v.assessment}
        self.assertIn(cv.Sufficiency.MISSING_UPSTREAM.value, verdicts)
        self.assertNotIn(cv.Sufficiency.PROJECTION_FAILURE.value, verdicts,
                         "nothing existed to lose")

    def test_S3ROOT_16_17_design_wide_survives_and_branch_local_is_isolated(self):
        s = DesignState(run_id="mixed")
        self.add(s, "s01", "Requirement", "REQ-A", quantity_class="BAND")
        self.add(s, "s01", "Requirement", "REQ-LOOSE", quantity_class="BAND")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-A"])
        self.add(s, "s02", "Candidate", "CND-A", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        self.add(s, "s02", "Candidate", "CND-B", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        self.add(s, "s03", "Body", "BOD-A", prem=["CND-A"])
        self.add(s, "s03", "Body", "BOD-B", prem=["CND-B"])
        # Design-wide: s02 declares the FULL requirement set, so the requirement
        # no candidate addresses is still there. It has no branch lineage at all.
        wide = {e["entity_id"] for e in consumer_view_for("s02", s).entities}
        self.assertIn("REQ-A", wide)
        self.assertIn("REQ-LOOSE", wide, "an unaddressed requirement was dropped")
        self.assertEqual([], s.entities["REQ-LOOSE"].get("_premises", []),
                         "it is visible and still unaddressed")
        # Branch-local: the other alternative's topology is positively excluded.
        v = consumer_view_for("s03b", s,
                              invocation=cv.InvocationContext(branch="CND-A"))
        got = {e["entity_id"] for e in v.entities}
        self.assertIn("BOD-A", got)
        self.assertNotIn("BOD-B", got, "another branch's topology reached the view")
        # Nothing is dropped in silence: every unmet obligation says what it
        # expected, what arrived, and which of the two findings it is.
        for a in v.assessment:
            for atom in a["coverage"]:
                if atom["verdict"] != cv.Sufficiency.SATISFIED.value:
                    self.assertTrue(atom["why"] and "expected" in atom, atom)


if __name__ == "__main__":
    unittest.main()


class TestS3OwnedADRReplays(_Base):
    """The two registry entries Impl S-3 owns, driven rather than argued."""

    def test_ADR_002_a_required_premise_is_not_omitted_from_the_view(self):
        """Original: a quantity constraining extent was authoritative in state and
        absent from the s04 view, because the boundary was one hand-written family
        tuple. The tuple is gone; the minimum is derived."""
        s = DesignState(run_id="adr002")
        self.add(s, "s01", "Requirement", "REQ-Q", quantity_class="BAND")
        self.add(s, "s01", "Actor", "ACT-1")
        self.add(s, "s02", "Obligation", "OBL-1", scope="UNIVERSAL",
                 satisfiable_at="s03", derived_from_requirements=["REQ-Q"])
        self.add(s, "s02", "Candidate", "CND-1", principle={"h": "f"},
                 addresses_obligations=["OBL-1"], obligations_created=[])
        self.add(s, "s03", "Body", "BOD-1", prem=["CND-1"])

        v = consumer_view_for("s04a", s, invocation=cv.InvocationContext(branch="CND-1"))
        quantity = [a for a in v.assessment if a["requirement"] == "extent_bounding_quantity"]
        self.assertTrue(quantity, "the premise is not even derived")
        got = {e["entity_id"] for e in v.entities}
        self.assertIn("REQ-Q", got, "the authoritative quantity was omitted again")

        # Forbidden post-fix condition: present in state, absent from the view,
        # with no finding. Every unmet obligation states expected and selected.
        for a in v.assessment:
            for atom in a["coverage"]:
                if atom["verdict"] != cv.Sufficiency.SATISFIED.value:
                    self.assertIn("expected_count", atom)
                    self.assertTrue(atom["why"])

    def test_ADR_002b_the_hand_written_family_tuple_is_gone(self):
        """The NAME may survive as a tombstone; the TABLE may not."""
        for path, src in list(_py(_PROD)) + list(_py(_TOOLS)):
            for node in ast.walk(ast.parse(src)):
                if not isinstance(node, ast.Assign):
                    continue
                names = [t2.id for t2 in node.targets if isinstance(t2, ast.Name)]
                if not any("OWNED" in n or "CONTEXT" in n for n in names):
                    continue
                self.assertNotIsInstance(
                    node.value, (ast.List, ast.Tuple, ast.Set, ast.Dict),
                    "%s: %s is a context table again" % (path, names))

    def test_ADR_004_no_serialized_view_is_positionally_sliced(self):
        """Original: `json.dumps(...)[:26000]`, and `RigidGroup` sorts last."""
        import ver3.assy_v3.stages.s03_topology_and_mobility as s03
        import ver3.assy_v3.stages.s04_envelope_and_motion as s04
        import inspect
        for fn in (s03._render, s04._render, cv.render):
            self.assertIsNone(re.search(r"\[:\s*\d+\s*\]", inspect.getsource(fn)),
                              fn.__module__)
        payload = {"AAA": [{"id": "A"} for _ in range(4000)], "ZZZ": [{"id": "LAST"}]}
        for fn in (s03._render, s04._render):
            out = fn(payload)
            self.assertGreater(len(out), 26000)
            self.assertNotIn("LAST", out[:26000], "the fixture does not reproduce it")
            self.assertIn("LAST", out)
