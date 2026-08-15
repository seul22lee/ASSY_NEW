"""S-8 / U-9: the checker does not work for the thing it checks.

Every probe runs the real chain and then asks the independent layer what the
COMMITTED design establishes. Nothing here calls a model: an assurance check that
had to ask a provider would be an opinion about an opinion, and the whole point
of the layer is that its answer does not depend on the answer being judged.

WHAT THESE TESTS ARE GUARDING

    THE DIRECTION. producer, then committed state, then assurance. A stage that
    could reach a check could satisfy it, and a check written where its subject
    can see it stops being evidence about the subject.

    WHAT A PASS IS ENTITLED TO SAY. A count is not a conclusion; a value
    surviving transport is not a value being right; a claim tracing to a premise
    is not the claim being true. Only two independently authored premises
    agreeing about a physical property may establish one - and it establishes
    THAT property, not its siblings, not its stage and not the design.

    THE FOUR CONSTRUCTS. Execution says whether the machinery ran. An
    engineering finding does not touch it, and a provider timeout is not a
    statement about a mechanism. The single badge and the single maturity index
    that mixed them are gone rather than renamed.
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.assurance as assurance                             # noqa: E402
import ver3.assy_v3.assurance.checks as checks                         # noqa: E402
import ver3.assy_v3.assurance.model as model                           # noqa: E402
import ver3.assy_v3.assurance.status as status                         # noqa: E402
from ver3.assy_v3.assurance.registry import (NOT_ASSURANCE, REGISTRY,   # noqa: E402
                                             validate as validate_registry)
from ver3.assy_v3.assurance.runner import run_assurance                 # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from ver3.tools import quality_profile                                  # noqa: E402
from .test_s7_feasibility import HINGE_BOXES, arrangement               # noqa: E402
from .test_s7_lifecycle import _Lifecycle                               # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_STAGES = os.path.join(_REPO, "assy_v3", "stages")


def _source(*parts: str) -> str:
    with open(os.path.join(_REPO, *parts)) as fh:
        return fh.read()


class _Assurance(_Lifecycle):
    """A committed design, and the independent layer's reading of it."""

    def assured(self, state=None, **kw):
        state = state if state is not None else self.chain(**kw)
        return state, run_assurance(state)

    def result(self, snapshot, check_id):
        found = [r for r in snapshot.results if r.check_id == check_id]
        self.assertEqual(1, len(found), check_id)
        return found[0]

    def establishment(self, snapshot, prefix):
        return {p: s for p, s in snapshot.establishment().items()
                if p.startswith(prefix)}

    def reaching(self):
        """A design whose source states a reach demand and whose arrangement
        answers it. S01 authored the demand; s04a authored whether it is met."""
        state = self.seed(must_reach=["BOD-G0A"])
        self.candidates(state)
        self.hinge(state, sfx="A",
                   s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                    actor="ACT-0001"))
        return state


# =====================================================================
# 1-5 - the direction, and what a check must declare
# =====================================================================
class TestIndependence(_Assurance):

    def test_S8_01_no_stage_module_reaches_assurance(self):
        """The invariant in one assertion. A producing module that could import
        a check could also satisfy it, and every check in this repository used to
        live in the module of the stage it judged."""
        for name in sorted(os.listdir(_STAGES)):
            if not name.endswith(".py"):
                continue
            source = _source("assy_v3", "stages", name)
            tree = ast.parse(source)
            # THE CODE, not the prose. A module explaining that it may not reach
            # assurance says the word; what matters is that nothing in it does.
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    self.assertNotIn("assurance", node.attr, name)
                if isinstance(node, ast.Name):
                    self.assertNotIn("assurance", node.id, name)
                if isinstance(node, ast.Call):
                    called = getattr(node.func, "id", "") or getattr(
                        node.func, "attr", "")
                    self.assertNotIn("assurance", called, name)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn("assurance", node.module or "", name)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn("assurance", alias.name, name)

    def test_S8_02_a_producer_validator_is_not_registered_as_assurance(self):
        """The runner still runs producer validations - they refuse malformed
        writes and that is their job. What they may not be is counted as
        independent assurance, and the two sets are disjoint by name."""
        from ver3.tools import run_window2
        producer = {name for name, _fn in
                    tuple(run_window2.S03_CHECKS) + tuple(run_window2.S04_CHECKS)}
        registered = {c.check_id for c in REGISTRY}
        self.assertEqual(set(), producer & registered)
        for relocated in ("constraint_disposition", "irrelevance",
                          "joint_geometry", "configuration_realization",
                          "transition_realization", "selection_gate"):
            self.assertNotIn(relocated, producer,
                             "%s is still run as a stage check" % relocated)

    def test_S8_03_assurance_authors_nothing(self):
        """Structural and behavioural. No operation is constructed anywhere in
        the layer, and running the whole registry leaves the state hash where it
        was - the act of assessing does not change the thing assessed."""
        for name in sorted(os.listdir(os.path.join(_REPO, "assy_v3", "assurance"))):
            if not name.endswith(".py"):
                continue
            source = _source("assy_v3", "assurance", name)
            for writing in ('Op("', "StagePatch(", ".apply(",
                            '["_validity"] =', "_validity ="):
                self.assertNotIn(writing, source, "%s writes state" % name)
        state = self.chain()
        before = state.state_hash()
        run_assurance(state)
        run_assurance(state)
        self.assertEqual(before, state.state_hash())
        self.assertEqual([], state.family("AssuranceResult"))

    def test_S8_04_no_provider_is_reachable_from_assurance(self):
        for name in sorted(os.listdir(os.path.join(_REPO, "assy_v3", "assurance"))):
            if not name.endswith(".py"):
                continue
            source = _source("assy_v3", "assurance", name)
            for provider in ("deepseek", "DeepSeek", "gemini", "Gemini",
                             "anthropic", "openai", "providers", "requests",
                             "urllib", "socket", "generate("):
                self.assertNotIn(provider, source,
                                 "%s reaches %s" % (name, provider))

    def test_S8_05_every_registered_check_declares_its_metadata(self):
        validate_registry()
        for check in REGISTRY:
            self.assertIn(check.independence, model.INDEPENDENCE_DEGREES)
            self.assertIn(check.claim_class, model.CLAIM_CLASSES)
            self.assertTrue(check.property_scope.strip())
            self.assertTrue(check.inputs)
            self.assertTrue(check.authors)
        for missing in (model.Check("x", "NOWHERE", model.BOOKKEEPING, "p",
                                    ("i",), ("a",), fn=lambda s: []),
                        model.Check("x", model.STRUCTURAL, "GUESS", "p",
                                    ("i",), ("a",), fn=lambda s: []),
                        model.Check("x", model.STRUCTURAL, model.BOOKKEEPING, "",
                                    ("i",), ("a",), fn=lambda s: []),
                        model.Check("x", model.STRUCTURAL, model.BOOKKEEPING, "p",
                                    ("i",), ("a",), fn=None)):
            with self.assertRaises(model.RegistryError):
                missing.validate()

    def test_S8_05b_an_engineering_consequence_needs_two_authors(self):
        """One author checking itself can only find what it already knew."""
        with self.assertRaises(model.RegistryError):
            model.Check("x", model.PREMISE, model.ENGINEERING_CONSEQUENCE, "p",
                        ("i",), ("s03",), fn=lambda s: []).validate()
        for check in REGISTRY:
            if check.claim_class == model.ENGINEERING_CONSEQUENCE:
                self.assertTrue(len(set(check.authors)) >= 2
                                or check.independence == model.EXTERNAL,
                                check.check_id)


# =====================================================================
# 6-9 - only an engineering consequence establishes, and only its property
# =====================================================================
class TestEstablishment(_Assurance):

    def test_S8_06_a_relabelled_fidelity_result_would_establish(self):
        """THE MUTATION, run in the open. The same passing findings establish
        nothing as FIDELITY and everything as ENGINEERING_CONSEQUENCE, which is
        why the claim class is declared in a registry rather than chosen by
        whoever writes the check."""
        state, snapshot = self.assured()
        fidelity = self.result(snapshot, "quantitative_continuity")
        self.assertEqual(model.FIDELITY, fidelity.claim_class)
        for value in fidelity.establishment().values():
            self.assertNotEqual(model.ENGINEERING_ESTABLISHED, value)
        relabelled = model.CheckResult(
            fidelity.check_id, fidelity.independence,
            model.ENGINEERING_CONSEQUENCE, fidelity.findings,
            fidelity.premise_digest)
        self.assertEqual(
            set(),
            {v for v in relabelled.establishment().values()
             if v == model.ENGINEERING_ESTABLISHED}
            if not any(f.outcome == model.PASS for f in fidelity.findings)
            else set() ^ {model.ENGINEERING_ESTABLISHED})

    def test_S8_07_a_structural_pass_establishes_nothing(self):
        state, snapshot = self.assured()
        for check_id in ("consumer_sufficiency", "reference_integrity",
                         "mobility_disposition_completeness",
                         "quantitative_continuity"):
            result = self.result(snapshot, check_id)
            self.assertNotEqual(model.ENGINEERING_CONSEQUENCE, result.claim_class)
            self.assertNotIn(model.ENGINEERING_ESTABLISHED,
                             set(result.establishment().values()),
                             "%s established something" % check_id)
        self.assertTrue(any(f.outcome == model.PASS
                            for f in self.result(snapshot,
                                                 "reference_integrity").findings))

    def test_S8_08_a_valid_engineering_consequence_establishes_its_property(self):
        state, snapshot = self.assured()
        result = self.result(snapshot, "topology_to_spatial_fidelity")
        self.assertEqual(model.ENGINEERING_CONSEQUENCE, result.claim_class)
        self.assertEqual(model.PREMISE, result.independence)
        passed = [f for f in result.findings if f.outcome == model.PASS]
        self.assertTrue(passed)
        established = result.establishment()
        for finding in passed:
            self.assertEqual(model.ENGINEERING_ESTABLISHED,
                             established[finding.property_id])

    def test_S8_09_establishment_does_not_leak(self):
        """One property, one entity. Not the sibling body pair, not the stage,
        not the design - and there is no design-wide term for it to leak into,
        which is the structural half of the same statement."""
        state = self.chain()
        # one incidence broken, the others untouched
        self.supersede(state, "ENV-G1A",
                       {"extent": {"centre": [0, 0, 40],
                                   "half_extent": [1, 1, 1]}},
                       why="moved far away")
        snapshot = run_assurance(state)
        established = self.establishment(snapshot, "topology_to_spatial_fidelity")
        broken = [p for p, s in established.items()
                  if s != model.ENGINEERING_ESTABLISHED]
        intact = [p for p, s in established.items()
                  if s == model.ENGINEERING_ESTABLISHED]
        self.assertTrue(broken and intact,
                        "the probe did not separate one property from the rest")
        for prop in intact:
            self.assertNotIn("BOD-G1A", prop)
        report = snapshot.as_dict()
        for forbidden in ("stage_established", "design_established", "overall",
                          "score", "index"):
            self.assertNotIn(forbidden, json.dumps(report))


# =====================================================================
# 10-14 - four constructs, and no scalar across them
# =====================================================================
class TestStatusConstructs(_Assurance):

    def test_S8_10_an_engineering_finding_does_not_downgrade_execution(self):
        state = self.chain()
        self.supersede(state, "ENV-G1A",
                       {"extent": {"centre": [0, 0, 40],
                                   "half_extent": [1, 1, 1]}},
                       why="moved far away")
        snapshot = run_assurance(state)
        self.assertTrue(snapshot.findings(model.FAIL))
        report = status.report(snapshot,
                               execution=[{"execution_status": "SUCCESS"},
                                          {"execution_status": "SUCCESS"}])
        self.assertEqual({"SUCCESS": 2}, report[status.EXECUTION]["by_status"])
        self.assertTrue(report[status.ENGINEERING_ESTABLISHMENT]["findings"])
        source = _source("tools", "build_pipeline_dashboard.py")
        self.assertNotIn('if status == OK and ev["findings"]:', source)

    def test_S8_11_an_execution_failure_is_not_an_engineering_claim(self):
        state, snapshot = self.assured()
        report = status.report(snapshot,
                               execution=[{"execution_status": "PROVIDER_TIMEOUT"}])
        self.assertEqual({"PROVIDER_TIMEOUT": 1},
                         report[status.EXECUTION]["by_status"])
        engineering = report[status.ENGINEERING_ESTABLISHMENT]
        self.assertEqual([], [f for f in engineering["findings"]
                              if "TIMEOUT" in json.dumps(f)])
        for term in ("PROVIDER_TIMEOUT", "SUCCESS"):
            self.assertEqual(status.EXECUTION, status.construct_of(term))

    def test_S8_12_evidence_maturity_is_not_an_establishment_status(self):
        self.assertEqual(status.EVIDENCE_MATURITY,
                         status.construct_of("PROVISIONAL"))
        self.assertNotIn("PROVISIONAL", model.ESTABLISHMENT)
        state, snapshot = self.assured()
        self.assertNotIn("PROVISIONAL", set(snapshot.establishment().values()))
        # and no term belongs to two constructs
        self.assertEqual(len(status.TERMS), len(set(status.TERMS)))
        for term, construct in status.TERMS.items():
            self.assertIn(construct, status.CONSTRUCTS)

    def test_S8_13_no_report_scalar_mixes_constructs(self):
        state, snapshot = self.assured()
        report = status.report(snapshot, execution=[{"execution_status": "SUCCESS"}])
        self.assertEqual(set(status.CONSTRUCTS), set(report))
        for construct, section in report.items():
            for key, value in section.items():
                if isinstance(value, (int, float)) and key != "attempts":
                    self.fail("%s carries the scalar %s" % (construct, key))
        self.assertNotIn("overall", json.dumps(report))

    def test_S8_14_the_maturity_index_is_retired_not_renamed(self):
        self.assertFalse(hasattr(quality_profile, "maturity_index"))
        source = _source("tools", "quality_profile.py")
        for successor in ("def quality_index", "def readiness_index",
                          "def confidence_index", "def maturity_index"):
            self.assertNotIn(successor, source)
        profile = {k: 1.0 for k in quality_profile.MATURITY_KEYS}
        grouped = quality_profile.construct_profile(profile)
        self.assertEqual({"CONTRACT_COMPLETENESS", "FIDELITY", "note"},
                         set(grouped))
        self.assertEqual(set(), set(quality_profile.FIDELITY_KEYS)
                         & set(quality_profile.COMPLETENESS_KEYS))


# =====================================================================
# 15-21 - the capability matrix, in substance
# =====================================================================
class TestCapabilities(_Assurance):

    def test_S8_15_S8_16_two_capabilities_are_declared_not_assurance(self):
        registered = {c.check_id for c in REGISTRY}
        self.assertNotIn("dof_totality", registered)
        self.assertNotIn("sampling_declaration", registered)
        self.assertEqual({"dof_totality", "sampling_declaration"},
                         set(NOT_ASSURANCE))
        source = _source("assy_v3", "assurance", "checks.py")
        self.assertNotIn("dof_totality", source)
        self.assertNotIn("SAMPLE", source)

    def test_S8_17_undeclared_distinctness_is_not_penalised(self):
        """Conditional on a declared premise, never "all joints must differ"."""
        state, snapshot = self.assured()
        declared = [c for c in state.standing("Configuration")
                    if c.get("distinguishing_basis")]
        result = self.result(snapshot, "required_distinctness_non_degeneracy")
        if not declared:
            self.assertEqual((), result.findings)
        for finding in result.findings:
            self.assertTrue(any(c["entity_id"] in finding.property_id
                                for c in declared), finding.property_id)

    def test_S8_18_a_loaded_dof_may_not_be_irrelevant(self):
        """THE S03 RULE-A PROPERTY. s02 wrote the load case and s03 wrote the
        disposition; neither could make the other agree."""
        from .test_s5_generality import TestIrrelevancePremise as _Irr
        _Irr.setUpClass()
        probe = _Irr("test_GEN_IRR_02_the_same_claim_fails_when_the_load_fact_changes")
        quiet = run_assurance(probe._state_with("SCN-IDLE"))
        loud = run_assurance(probe._state_with("SCN-LOAD"))
        established = self.establishment(quiet,
                                         "mobility_cross_premise_consistency")
        self.assertTrue(established)
        self.assertEqual({model.ENGINEERING_ESTABLISHED}, set(established.values()))
        failures = [f for f in loud.findings(model.FAIL)
                    if f.property_id.startswith("mobility_cross_premise")]
        self.assertTrue(failures)
        self.assertIn("IRRELEVANCE_CONTRADICTED", failures[0].detail)
        for prop in self.establishment(loud, "mobility_cross_premise_consistency"):
            self.assertNotEqual(model.ENGINEERING_ESTABLISHED,
                                loud.establishment()[prop])

    def test_S8_19_a_topology_spatial_mismatch_is_a_finding(self):
        state = self.chain()
        self.supersede(state, "ENV-G1A",
                       {"extent": {"centre": [0, 0, 40],
                                   "half_extent": [1, 1, 1]}},
                       why="moved far away")
        snapshot = run_assurance(state)
        failures = [f for f in snapshot.findings(model.FAIL)
                    if f.property_id.startswith("topology_to_spatial_fidelity")]
        self.assertTrue(failures)
        self.assertIn("JOINED_BODIES_DO_NOT_MEET", failures[0].detail)

    def test_S8_20_a_declared_distinction_with_no_realization_is_a_finding(self):
        state = self.chain()
        configurations = state.standing("Configuration")
        self.assertTrue(configurations)
        template = {k: v for k, v in configurations[0].items()
                    if not k.startswith("_") and k != "entity_id"}
        self.revise(state, Op("CREATE", "Configuration", "CFG-UNREALIZED",
                              dict(template, name="an unrealized state",
                                   distinguishing_basis=[
                                       {"rigid_group": "RGP-G0A", "dof": "RZ"}]),
                              "t"), stage="s03")
        snapshot = run_assurance(state)
        failures = [f for f in snapshot.findings(model.FAIL)
                    if "CFG-UNREALIZED" in f.property_id]
        self.assertTrue(failures)
        self.assertIn("CONFIGURATION_NOT_REALIZED", failures[0].detail)

    def test_S8_21_the_gate_does_not_report_on_itself(self):
        """EXTERNAL. The preconditions are recomputed from committed records by
        a reader that is not the committing code, and a commitment standing over
        violated conditions is FALSE_ACCEPTANCE - the emitter M-9 records as
        missing."""
        state, decision = self.committed()
        snapshot = run_assurance(state)
        self.assertEqual(model.ENGINEERING_ESTABLISHED,
                         snapshot.establishment()["commitment_validity:%s" % decision])
        source = inspect.getsource(checks.commitment_validity)
        for producer in ("selection_decision", "commit_human_selection",
                         "equal_coverage_confirmed"):
            self.assertNotIn(producer, source)
        # A NEW BLOCKING REQUIREMENT, which supersedes nothing. The commitment
        # stays STANDING - no premise edge leads from a requirement that did not
        # exist when it was made - and it now stands over a condition nobody has
        # satisfied. That is the shape a self-reporting gate can never see.
        self.constraint(state, eid="DSC-S821", blocks=True)
        self.assertEqual("STANDING", self.validity(state, decision))
        again = run_assurance(state)
        failures = [f for f in again.findings(model.FAIL)
                    if f.property_id.startswith("commitment_validity")]
        self.assertTrue(failures)
        self.assertEqual(model.FALSE_ACCEPTANCE, failures[0].code)


# =====================================================================
# 22-23 - a snapshot is bound to what it read
# =====================================================================
class TestSnapshot(_Assurance):

    def test_S8_22_the_same_state_gives_the_same_answer(self):
        state = self.chain()
        first, second = run_assurance(state), run_assurance(state)
        self.assertEqual(first.digest(), second.digest())
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(state.state_hash(), first.state_hash)

    def test_S8_23_a_snapshot_stops_being_current_when_the_state_moves(self):
        state = self.chain()
        snapshot = run_assurance(state)
        self.assertTrue(snapshot.is_current(state))
        before = self.result(snapshot, "topology_to_spatial_fidelity")
        self.supersede(state, "ENV-G1A",
                       {"extent": {"centre": [0, 0, 40],
                                   "half_extent": [1, 1, 1]}},
                       why="moved far away")
        self.assertFalse(snapshot.is_current(state),
                         "a historical snapshot reported itself as current")
        after = self.result(run_assurance(state), "topology_to_spatial_fidelity")
        self.assertNotEqual(before.premise_digest, after.premise_digest)

    def test_S8_23b_an_unrelated_change_leaves_a_check_s_premises_alone(self):
        """Per check, not whole-state: a snapshot is current FOR A CHECK when
        what that check read is what the design still says."""
        state = self.chain()
        before = self.result(run_assurance(state), "topology_to_spatial_fidelity")
        self.unrelated(state, "AMB-S8")
        after = self.result(run_assurance(state), "topology_to_spatial_fidelity")
        self.assertEqual(before.premise_digest, after.premise_digest)


# =====================================================================
# Rule A - one established engineering property per producing stage
# =====================================================================
class TestRuleA(_Assurance):

    def test_S8_RULE_A_s01_a_stated_reach_demand_is_answered(self):
        state = self.reaching()
        snapshot = run_assurance(state)
        established = self.establishment(snapshot, "reach_demand_realization")
        self.assertTrue(established, "the demand produced no property at all")
        self.assertEqual({model.ENGINEERING_ESTABLISHED},
                         set(established.values()))
        check = [c for c in REGISTRY if c.check_id == "reach_demand_realization"][0]
        self.assertEqual(("s01", "s04"), check.authors)

    def test_S8_RULE_A_s02_a_required_effect_is_discharged(self):
        state, snapshot = self.assured()
        established = self.establishment(snapshot, "physical_relation_closure")
        self.assertTrue(established)
        self.assertIn(model.ENGINEERING_ESTABLISHED, set(established.values()))
        check = [c for c in REGISTRY if c.check_id == "physical_relation_closure"][0]
        self.assertEqual(("s02", "s03"), check.authors)

    def test_S8_RULE_A_s03_a_loaded_dof_is_not_irrelevant(self):
        from .test_s5_generality import TestIrrelevancePremise as _Irr
        _Irr.setUpClass()
        probe = _Irr("test_GEN_IRR_02_the_same_claim_fails_when_the_load_fact_changes")
        snapshot = run_assurance(probe._state_with("SCN-IDLE"))
        established = self.establishment(snapshot,
                                         "mobility_cross_premise_consistency")
        self.assertEqual({model.ENGINEERING_ESTABLISHED}, set(established.values()))

    def test_S8_RULE_A_s04_the_declared_incidence_is_realized(self):
        state, snapshot = self.assured()
        established = self.establishment(snapshot, "topology_to_spatial_fidelity")
        self.assertTrue(established)
        self.assertIn(model.ENGINEERING_ESTABLISHED, set(established.values()))
        check = [c for c in REGISTRY
                 if c.check_id == "topology_to_spatial_fidelity"][0]
        self.assertEqual(("s03", "s04"), check.authors)

    def test_S8_RULE_A_nothing_was_relabelled_to_reach_the_floor(self):
        """The floor is met by four capabilities that compare two authors. The
        ones that could have been promoted to make it easier were not."""
        by_class = {}
        for check in REGISTRY:
            by_class.setdefault(check.claim_class, []).append(check.check_id)
        self.assertIn("consumer_sufficiency", by_class[model.BOOKKEEPING])
        self.assertIn("quantitative_continuity", by_class[model.FIDELITY])
        self.assertIn("mobility_disposition_completeness",
                      by_class[model.PROVENANCE_INTEGRITY])
        self.assertIn("reference_integrity", by_class[model.PROVENANCE_INTEGRITY])


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
