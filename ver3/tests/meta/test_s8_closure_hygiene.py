"""S-8 closure hygiene: the inventory is a set, not a sentence.

The S8 evidence claimed that every pre-S8 check was classified exactly once, and
its prose totals did not reconcile with its own tables - a count that says 30
above a list of 32 names is not a claim anybody can check. This module makes the
claim mechanical: the inventory below is data, the baseline it describes is
reconstructed from the commit it names, and the assertions are SET EQUALITIES
rather than arithmetic.

WHAT THIS DOES NOT DO

Nothing here changes assurance semantics, claim classes, Rule A or status
meanings. If a fact recorded here turned out to disagree with the production
code, the fix would be the record - unless the code were wrong, and then it would
be a new pass rather than a hygiene patch.

THE THREE POPULATIONS, KEPT APART

    PRE-S8 BASELINE CHECKS     41 module-level checks in `stages/*.py` at
                               237b1ba. Every one is classified exactly once.
    NEW S8 CAPABILITIES        registered capabilities with no baseline
                               predecessor. They are NOT relocations and are
                               never counted as though they were.
    SHARED PURE COMPUTATION    what the assurance layer actually imports from a
                               producer module, derived from the AST rather than
                               from a sentence about it.
"""
from __future__ import annotations

import ast
import os
import subprocess
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.assurance.model as model                           # noqa: E402
import ver3.assy_v3.assurance.status as status                         # noqa: E402
import ver3.assy_v3.stages.s01_requirement_capture as s01              # noqa: E402
import ver3.assy_v3.stages.s02_obligation_and_candidates as s02        # noqa: E402
import ver3.assy_v3.stages.s03_topology_and_mobility as s03            # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.assurance.registry import NOT_ASSURANCE, REGISTRY     # noqa: E402

#: The commit this inventory describes. S8 landed on top of it.
BASELINE_COMMIT = "237b1ba"

#: The three dispositions a pre-S8 check may have. Exactly one each.
RETAINED_PRODUCER = "RETAINED_PRODUCER_VALIDATION"
RETAINED_BOOKKEEPING = "RETAINED_BOOKKEEPING"
RELOCATED = "RELOCATED_ASSURANCE_CAPABILITY"

MODULES = {"s01": s01, "s02": s02, "s03": s03, "s04": s04}
STAGE_FILES = {
    "s01": "ver3/assy_v3/stages/s01_requirement_capture.py",
    "s02": "ver3/assy_v3/stages/s02_obligation_and_candidates.py",
    "s03": "ver3/assy_v3/stages/s03_topology_and_mobility.py",
    "s04": "ver3/assy_v3/stages/s04_envelope_and_motion.py",
}

#: name -> (pre-S8 owner, disposition, capability it became or None).
#:
#: A check that became TWO capabilities lists both: `irrelevance_check` asked one
#: provenance question and one cross-author question, and S8 split it because
#: only the second compares two producers. Recording the split is the point - a
#: relocation table that pretended it was one capability would hide the reason
#: the move was worth making.
BASELINE_INVENTORY = {
    # ---- s01 ---------------------------------------------------------
    "sharpening_check": ("s01", RETAINED_PRODUCER, None),
    "locator_check": ("s01", RETAINED_PRODUCER, None),
    "mechanism_leakage_check": ("s01", RETAINED_PRODUCER, None),
    # ---- s02 ---------------------------------------------------------
    "no_selection_check": ("s02", RETAINED_PRODUCER, None),
    "load_case_check": ("s02", RETAINED_PRODUCER, None),
    "candidate_distinctness_check": ("s02", RETAINED_PRODUCER, None),
    "known_principle_check": ("s02", RETAINED_PRODUCER, None),
    "evidence_route_check": ("s02", RETAINED_PRODUCER, None),
    "created_obligations_check": ("s02", RETAINED_PRODUCER, None),
    "requirement_coverage_check": ("s02", RETAINED_PRODUCER, None),
    "obligation_scope_check": ("s02", RETAINED_PRODUCER, None),
    "candidate_coverage_check": ("s02", RETAINED_PRODUCER, None),
    "openness_citation_check": ("s02", RETAINED_PRODUCER, None),
    "actor_citation_check": ("s02", RETAINED_PRODUCER, None),
    "magnitude_fidelity_check": ("s02", RELOCATED, ("quantitative_continuity",)),
    # ---- s03 ---------------------------------------------------------
    "assembly_acyclic_check": ("s03", RETAINED_PRODUCER, None),
    "load_path_check": ("s03", RETAINED_PRODUCER, None),
    "interface_classification_check": ("s03", RETAINED_PRODUCER, None),
    "retention_check": ("s03", RETAINED_PRODUCER, None),
    "no_magnitude_check": ("s03", RETAINED_PRODUCER, None),
    "obligation_ownership_check": ("s03", RETAINED_PRODUCER, None),
    "functional_region_check": ("s03", RETAINED_PRODUCER, None),
    "compliance_check": ("s03", RETAINED_PRODUCER, None),
    "simulation_completeness_check": ("s03", RETAINED_PRODUCER, None),
    "no_selection_check_s03": ("s03", RETAINED_PRODUCER, None),
    "dof_totality_check": ("s03", RETAINED_BOOKKEEPING, None),
    "constraint_disposition_check": ("s03", RELOCATED,
                                     ("mobility_disposition_completeness",)),
    "irrelevance_check": ("s03", RELOCATED,
                          ("mobility_disposition_completeness",
                           "mobility_cross_premise_consistency")),
    # ---- s04 ---------------------------------------------------------
    "envelope_coverage_check": ("s04", RETAINED_PRODUCER, None),
    "configuration_interference_check": ("s04", RETAINED_PRODUCER, None),
    "region_occupancy_check": ("s04", RETAINED_PRODUCER, None),
    "spatial_commitment_check": ("s04", RETAINED_PRODUCER, None),
    "joint_frame_check": ("s04", RETAINED_PRODUCER, None),
    "swept_clearance_check": ("s04", RETAINED_PRODUCER, None),
    "assembly_path_check": ("s04", RETAINED_PRODUCER, None),
    "load_path_reaction_check": ("s04", RETAINED_PRODUCER, None),
    "motion_evidence_check": ("s04", RETAINED_BOOKKEEPING, None),
    "joint_geometry_check": ("s04", RELOCATED, ("topology_to_spatial_fidelity",)),
    "configuration_realization_check": ("s04", RELOCATED,
                                        ("required_distinctness_non_degeneracy",
                                         "state_configuration_realization")),
    "transition_realization_check": ("s04", RELOCATED,
                                     ("state_configuration_realization",)),
    "selection_gate_check": ("s04", RELOCATED, ("commitment_validity",)),
}

#: Capabilities S8 introduced that no baseline check became. Kept apart from the
#: relocation table so a new capability can never be counted as a move.
NEW_CAPABILITIES = ("consumer_sufficiency", "reference_integrity",
                    "physical_relation_closure", "reach_demand_realization")

#: What the assurance layer actually imports from a producing module, as class-D
#: shared pure computation. Two of these are constants and seven are callables;
#: the test derives the set from the AST and compares, so the record cannot drift
#: from the import.
#:
#: `_s04._driving_joint` LEFT with the rigid-group basis. It answered "which
#: joint moves this group" with the first joint whose CHILD was the group, and
#: the one caller asked it in order to measure a declared distinction - a
#: question that names its own joint now, so there is nothing to drive and no
#: convention left to apply.
SHARED_PURE_COMPUTATION = (
    "_s03.CONSTRAINT_DRIVERS", "_s03.QUALIFIER_WORDS",
    "_s03.current_mobility_cells", "_s04._boxes",
    "_s04._thaw", "_s04.box_gap", "_s04.coordinate_change_disagreement",
    "_s04.distinctness_findings", "_s04.required_contacts",
)

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_ROOT = os.path.dirname(_REPO)


def _by(disposition):
    return {n for n, (_s, d, _t) in BASELINE_INVENTORY.items() if d == disposition}


def _source(path: str) -> str:
    with open(os.path.join(_ROOT, path)) as fh:
        return fh.read()


def _checks_in(source: str):
    """Module-level functions whose name contains `check`.

    Module-level on purpose: a nested helper is not a check the runner could
    call, and counting one would inflate the inventory with something no
    consumer can reach.
    """
    return {node.name for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef) and "check" in node.name}


# =====================================================================
# The inventory is the baseline, exactly
# =====================================================================
class TestBaselineInventory(unittest.TestCase):

    def recovered_baseline(self):
        """(stage, check) for every check in `stages/*.py` at the baseline commit.

        STAGE-QUALIFIED, because the name alone proves the wrong thing. A set of
        bare names shows that the inventory lists the right checks and says
        nothing about whether `magnitude_fidelity_check` was s02's or
        `selection_gate_check` was s04's - and the disposition of each one turns
        on which producer owned it. Recovering the pair makes the ownership
        column falsifiable against the commit instead of asserted beside it.
        """
        recovered = set()
        for stage, path in sorted(STAGE_FILES.items()):
            shown = subprocess.run(
                ["git", "-C", _ROOT, "show", "%s:%s" % (BASELINE_COMMIT, path)],
                capture_output=True, text=True)
            if shown.returncode != 0:
                self.skipTest("the %s baseline is not reachable from this tree"
                              % BASELINE_COMMIT)
            recovered |= {(stage, name) for name in _checks_in(shown.stdout)}
        return recovered

    def test_S8H_01_the_record_is_the_actual_pre_s8_baseline(self):
        """Reconstructed from the commit the record names, not remembered.

        Skipped rather than guessed where git is unavailable: an inventory test
        that silently passed on a missing baseline would be the same defect it
        exists to remove.
        """
        recovered = self.recovered_baseline()
        declared = {(stage, name) for name, (stage, _d, _t)
                    in BASELINE_INVENTORY.items()}
        self.assertEqual(recovered, declared,
                         "the recorded inventory is not the baseline, in name "
                         "or in who owned it")
        self.assertEqual(41, len(recovered))

    def test_S8H_01b_the_per_stage_distribution_is_the_commit_s(self):
        """Counted from the recovered pairs, so the distribution is a
        consequence of the baseline rather than a second thing to maintain."""
        recovered = self.recovered_baseline()
        by_stage = {}
        for stage, _name in recovered:
            by_stage[stage] = by_stage.get(stage, 0) + 1
        self.assertEqual({"s01": 3, "s02": 12, "s03": 13, "s04": 13}, by_stage)
        self.assertEqual(41, sum(by_stage.values()))
        # and the inventory's own ownership column agrees, stage by stage
        for stage, count in sorted(by_stage.items()):
            self.assertEqual(count, sum(1 for _n, (s, _d, _t)
                                        in BASELINE_INVENTORY.items()
                                        if s == stage), stage)

    def test_S8H_02_every_baseline_check_is_classified_exactly_once(self):
        producer, bookkeeping, relocated = (_by(RETAINED_PRODUCER),
                                            _by(RETAINED_BOOKKEEPING),
                                            _by(RELOCATED))
        self.assertEqual(set(), producer & bookkeeping)
        self.assertEqual(set(), producer & relocated)
        self.assertEqual(set(), bookkeeping & relocated)
        self.assertEqual(set(BASELINE_INVENTORY),
                         producer | bookkeeping | relocated)
        self.assertEqual((32, 2, 7),
                         (len(producer), len(bookkeeping), len(relocated)))
        for name, (stage, disposition, target) in BASELINE_INVENTORY.items():
            self.assertIn(stage, MODULES, name)
            self.assertIn(disposition,
                          (RETAINED_PRODUCER, RETAINED_BOOKKEEPING, RELOCATED))
            self.assertEqual(disposition == RELOCATED, target is not None, name)

    def test_S8H_03_relocated_checks_are_gone_from_their_producer(self):
        """Absent from the module AND from its source, because a function that
        survives under a comment is still reachable from the stage."""
        for name in sorted(_by(RELOCATED)):
            stage = BASELINE_INVENTORY[name][0]
            self.assertFalse(hasattr(MODULES[stage], name),
                             "%s is still in %s" % (name, stage))
            self.assertNotIn("def %s(" % name, _source(STAGE_FILES[stage]))

    def test_S8H_04_retained_checks_are_still_where_they_were(self):
        """The other half. A hygiene patch that quietly deleted a producer
        validation would be a semantic change wearing a tidy name."""
        for name in sorted(_by(RETAINED_PRODUCER) | _by(RETAINED_BOOKKEEPING)):
            stage = BASELINE_INVENTORY[name][0]
            self.assertTrue(hasattr(MODULES[stage], name),
                            "%s vanished from %s" % (name, stage))

    def test_S8H_05_every_relocation_resolves_to_a_registered_capability(self):
        registered = {c.check_id for c in REGISTRY}
        claimed = {t for _n, (_s, _d, targets) in BASELINE_INVENTORY.items()
                   if targets for t in targets}
        self.assertTrue(claimed)
        self.assertEqual(set(), claimed - registered,
                         "a relocation names a capability that does not exist")
        self.assertEqual(7, len(claimed))

    def test_S8H_06_bookkeeping_resolves_to_something_that_cannot_establish(self):
        registered = {c.check_id for c in REGISTRY}
        for name in sorted(_by(RETAINED_BOOKKEEPING)):
            stem = name[:-len("_check")]
            self.assertNotIn(stem, registered, "%s is registered" % name)
            self.assertNotIn(name, registered)
        self.assertIn("dof_totality", NOT_ASSURANCE)
        self.assertIn("sampling_declaration", NOT_ASSURANCE)
        # `motion_evidence` is bookkeeping by being absent from the registry -
        # it records the computation performed, and only a registered capability
        # can establish anything at all.
        self.assertNotIn("motion_evidence", registered)

    def test_S8H_07_new_capabilities_are_not_relocations(self):
        registered = {c.check_id for c in REGISTRY}
        relocated_targets = {t for _n, (_s, _d, targets)
                             in BASELINE_INVENTORY.items() if targets
                             for t in targets}
        self.assertEqual(set(), set(NEW_CAPABILITIES) & relocated_targets)
        self.assertEqual(registered, relocated_targets | set(NEW_CAPABILITIES),
                         "the registry is not exactly relocations plus new work")
        self.assertEqual((11, 7, 4), (len(registered), len(relocated_targets),
                                      len(NEW_CAPABILITIES)))

    def test_S8H_08_shared_pure_computation_is_what_the_code_shares(self):
        """Derived from the AST. The evidence said three and listed four, which
        is how a number stops being a fact - this one cannot say either unless
        the imports say it."""
        tree = ast.parse(_source("ver3/assy_v3/assurance/checks.py"))
        shared = {"%s.%s" % (node.value.id, node.attr)
                  for node in ast.walk(tree)
                  if isinstance(node, ast.Attribute)
                  and isinstance(node.value, ast.Name)
                  and node.value.id in ("_s03", "_s04")}
        self.assertEqual(set(SHARED_PURE_COMPUTATION), shared)
        self.assertEqual(9, len(shared))

    def test_S8H_09_the_evidence_document_states_the_checked_numbers(self):
        """The document is part of the closure, so it is asserted like one."""
        # Whitespace-normalised: a claim that wraps across a line is the same
        # claim, and a test that could be broken by a reflow would be measuring
        # the margin.
        evidence = " ".join(_source("docs/implementation/evidence/"
                                    "S08_IMPLEMENTATION_EVIDENCE.md").split())
        for claim in ("**A — producer / write-boundary validation (32).**",
                      "**B — bookkeeping / report-only (2).**",
                      "**C — independent assurance (11 capabilities, seven of "
                      "them carrying relocated code).**",
                      "**D — shared pure computation (9 references",
                      "41 module-level checks",
                      "FOUR capabilities are new work with no baseline "
                      "predecessor"):
            self.assertIn(" ".join(claim.split()), evidence, claim)


# =====================================================================
# The Python vocabulary is the contract's, or the test fails
# =====================================================================
class TestStatusSemanticsSync(unittest.TestCase):
    """The S8 model says it reuses STATUS_SEMANTICS rather than inventing a
    second status system. This is that claim, checked.

    EXACT SET EQUALITY, not membership. A spot check passes while a term is
    quietly added on one side, and a vocabulary that can grow on one side only is
    two vocabularies with one name.
    """

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_ROOT, "ver3", "contracts",
                               "STATUS_SEMANTICS.yaml")) as fh:
            cls.contract = yaml.safe_load(fh)

    def test_S8H_10_evaluation_outcomes_match_exactly(self):
        self.assertEqual(set(self.contract["evaluation_outcomes"]),
                         set(model.OUTCOMES))

    def test_S8H_11_establishment_vocabulary_matches_exactly(self):
        declared = self.contract["status_constructs"]["ENGINEERING_ESTABLISHMENT"]
        self.assertEqual(set(declared["vocabulary"]), set(model.ESTABLISHMENT))
        # And the term the contract deliberately does NOT repeat here.
        self.assertNotIn("PROVISIONAL", set(model.ESTABLISHMENT))
        self.assertIn("PROVISIONAL",
                      self.contract["status_constructs"]["EVIDENCE_MATURITY"]
                      ["vocabulary"])

    def test_S8H_12_the_assurance_declarations_match_exactly(self):
        declarations = self.contract["assurance_declarations"]
        self.assertEqual(set(declarations["independence_degree"]),
                         set(model.INDEPENDENCE_DEGREES))
        self.assertEqual(set(declarations["claim_class"]),
                         set(model.CLAIM_CLASSES))

    def test_S8H_13_the_construct_map_matches_the_contract(self):
        """Every term the status projection maps is the contract's term for that
        construct, and every contract term is mapped."""
        constructs = self.contract["status_constructs"]
        expected = {}
        for term in self.contract["execution_statuses"]:
            expected[term] = status.EXECUTION
        for construct, key in ((status.CONTRACT_COMPLETENESS,
                                "CONTRACT_COMPLETENESS"),
                               (status.EVIDENCE_MATURITY, "EVIDENCE_MATURITY")):
            for term in constructs[key]["vocabulary"]:
                expected[term] = construct
        for term in constructs["ENGINEERING_ESTABLISHMENT"]["vocabulary"]:
            if term != "NOT_VERIFIED":
                # Deliberately unmapped: the contract lists it under two
                # constructs, and picking one here would be this module settling
                # a contract question.
                expected[term] = status.ENGINEERING_ESTABLISHMENT
        self.assertEqual(expected, status.TERMS)

    def test_S8H_14_the_python_side_loads_no_contract_at_runtime(self):
        """Drift detection belongs in a test. Reading the YAML in production to
        make this pass would turn a checked constant into a runtime dependency,
        which is a bigger change than the drift it prevents."""
        for name in ("model.py", "status.py", "registry.py", "runner.py",
                     "checks.py"):
            tree = ast.parse(_source(os.path.join("ver3", "assy_v3",
                                                  "assurance", name)))
            # The code, not the prose: these modules name the contract they
            # follow, and saying which contract a constant comes from is the
            # opposite of a hidden dependency on it.
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual("yaml", alias.name, name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn("yaml", node.module or "", name)
                if isinstance(node, ast.Call) and getattr(
                        node.func, "id", "") == "open":
                    self.fail("%s reads a file at runtime" % name)
                if isinstance(node, ast.Str):
                    self.assertNotIn(".yaml", node.s, name)


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
