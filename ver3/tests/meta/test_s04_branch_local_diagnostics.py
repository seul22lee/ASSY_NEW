"""An S04 diagnostic answers about ONE mechanism, and reads only what it declares.

Two legacy defects, both demonstrated by the live BM-001 S04b run and both about
scope rather than about geometry:

  MIXED BRANCHES. `swept_clearance_check` and `assembly_path_check` read
  `state.family(...)` over the whole DesignState. Six candidates coexist there,
  so a body swept in one candidate was tested against bodies from the other five,
  and `order_index` - a sequence WITHIN one mechanism - was sorted across all
  six, making every branch's first body "already placed" before every other
  branch's second. The run reported 70 assembly obstructions of which none was
  about a real assembly, and swept findings against bodies from mechanisms that
  will never be built together.

  A PREMISE THE RESPONSIBILITY DOES NOT DECLARE. `S04BPlacementAndMotion.
  completeness` inherited s03's incompleteness by reading
  `MobilityExpectation.dispositions` out of its ConsumerView - a family
  `mobility_disposition` is not among s04b's required premise classes, so it is
  never in that view and the block could never fire. 277 blocked DOF carried no
  defeat specification and all six responses reported SUCCESS with nothing
  declared.

The repair for the second is REMOVAL, not widening the contract: a completeness
method reads the view it was given, and whether a candidate's evidence is good
enough to keep is judged after this pass, by feasibility.
"""
import unittest

from . import _fixtures

from ver3.assy_v3.stages import s04_envelope_and_motion as s04
from ver3.assy_v3.stages.s04_envelope_and_motion import (
    S04BPlacementAndMotion, assembly_path_check, assembly_path_findings,
    branch_payloads, swept_clearance_check, swept_clearance_findings)

#: What each diagnostic reads. Written here rather than imported: production
#: carries no standing family table, because a standing one is how a hand-kept
#: "what may this see" whitelist grows back (S3ROOT-10).
SWEPT_CLEARANCE_FAMILIES = ("Envelope", "RigidGroup", "Joint", "State",
                            "Transition", "Interface", "FunctionalRegion")
ASSEMBLY_PATH_FAMILIES = ("Envelope", "AssemblyStep")
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch


def box(centre, half=(1.0, 1.0, 1.0)):
    return {"centre": list(centre), "half_extent": list(half)}


class _TwoBranches(_fixtures.StateBuilder, unittest.TestCase):
    """Two candidates whose arrangements deliberately occupy the same space.

    Same coordinates, same order indices, same shapes - so every cross-branch
    comparison a mixing diagnostic could make is available to be made, and the
    test can tell "found nothing" apart from "had nothing to find".
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def build(self, second_body_centre=(0.0, 0.0, 0.0), interfaced=False):
        s = DesignState(run_id="s04-branch")
        self.add(s, "s02", "Candidate", "CND-A", principle={"h": "f"})
        self.add(s, "s02", "Candidate", "CND-B", principle={"h": "f"})
        ops = []
        for branch, tag in (("CND-A", "A"), ("CND-B", "B")):
            bodies = ["BOD-%s1" % tag, "BOD-%s2" % tag]
            groups = ["RGP-%s1" % tag, "RGP-%s2" % tag]
            ops += [
                Op("CREATE", "Body", bodies[0],
                   {"instance_identity": "one", "role": "base",
                    "created_by_stage": "s03"}, "s03:topology", premise_refs=[branch]),
                Op("CREATE", "Body", bodies[1],
                   {"instance_identity": "one", "role": "arm",
                    "created_by_stage": "s03"}, "s03:topology", premise_refs=[branch]),
                Op("CREATE", "RigidGroup", groups[0],
                   {"body": bodies[0], "members": [bodies[0]], "is_default": True},
                   "s03:topology", premise_refs=[branch]),
                Op("CREATE", "RigidGroup", groups[1],
                   {"body": bodies[1], "members": [bodies[1]], "is_default": True},
                   "s03:topology", premise_refs=[branch]),
                Op("CREATE", "Joint", "JNT-%s1" % tag,
                   {"joint_type": "REVOLUTE", "parent_group": groups[0],
                    "child_group": groups[1], "dof": ["RZ"], "axis_direction": "+Z",
                    "frame_ids": ["FRM-%s" % tag], "frame_origin": [0.0, 0.0, 0.0]},
                   "s03:topology", premise_refs=[branch]),
                Op("CREATE", "Configuration", "CFG-%s1" % tag,
                   {"name": "open", "kind": "OPERATIONAL", "bodies_present": bodies,
                    "expected_mobility": []}, "s03:topology", premise_refs=[branch]),
                Op("CREATE", "Configuration", "CFG-%s2" % tag,
                   {"name": "shut", "kind": "OPERATIONAL", "bodies_present": bodies,
                    "expected_mobility": []}, "s03:topology", premise_refs=[branch]),
                # IDENTICAL GEOMETRY IN BOTH BRANCHES, and identical order
                # indices: everything a mixing check would collide on.
                Op("CREATE", "Envelope", "ENV-%s1" % tag,
                   {"body": bodies[0], "extent": box((0.0, 0.0, 0.0)),
                    "frame": "world", "maturity": "PROVISIONAL"},
                   "s04a:arrangement", premise_refs=[branch]),
                Op("CREATE", "Envelope", "ENV-%s2" % tag,
                   {"body": bodies[1], "extent": box(second_body_centre),
                    "frame": "world", "maturity": "PROVISIONAL"},
                   "s04a:arrangement", premise_refs=[branch]),
                Op("CREATE", "AssemblyStep", "ASY-%s1" % tag,
                   {"order_index": 1, "body": bodies[0], "access_side": "+Z",
                    "activates": [], "termination_strategy": "NONE",
                    "path_kind": "RIGID", "depends_on": [],
                    "insertion_direction": [0.0, 0.0, 1.0]},
                   "s03b:relations", premise_refs=[branch]),
                Op("CREATE", "AssemblyStep", "ASY-%s2" % tag,
                   {"order_index": 2, "body": bodies[1], "access_side": "+Z",
                    "activates": [], "termination_strategy": "NONE",
                    "path_kind": "RIGID", "depends_on": [],
                    "insertion_direction": [0.0, 0.0, 1.0]},
                   "s03b:relations", premise_refs=[branch]),
                Op("CREATE", "State", "STA-CFG-%s1" % tag,
                   {"name": "open", "configuration": "CFG-%s1" % tag,
                    "joint_coordinates": {"JNT-%s1" % tag: 0.0}},
                   "s04b:placement", premise_refs=[branch]),
                Op("CREATE", "State", "STA-CFG-%s2" % tag,
                   {"name": "shut", "configuration": "CFG-%s2" % tag,
                    "joint_coordinates": {"JNT-%s1" % tag: 90.0}},
                   "s04b:placement", premise_refs=[branch]),
                Op("CREATE", "Transition", "TRN-%s1" % tag,
                   {"from_state": "STA-CFG-%s1" % tag, "to_state": "STA-CFG-%s2" % tag,
                    "path": {"moving_groups": [groups[1]]},
                    "changed_coordinates": ["JNT-%s1" % tag]},
                   "s04b:placement", premise_refs=[branch]),
            ]
            if interfaced:
                ops.append(Op("CREATE", "Interface", "IFC-%s1" % tag,
                              {"bodies": bodies, "interaction_kind": "CONTACT",
                               "nominal": "NOMINAL", "addresses_obligations": []},
                              "s03:topology", premise_refs=[branch]))
        # TWO PATCHES, because ownership is per stage and this fixture spans two:
        # the topology families are s03's and the spatial ones are s04's. One
        # patch would be refused for a reason that has nothing to do with scope.
        s04_families = {"Envelope", "State", "Transition"}
        for stage_id, chosen in (("s03", [o for o in ops
                                          if o.entity_type not in s04_families]),
                                 ("s04", [o for o in ops
                                          if o.entity_type in s04_families])):
            patch = StagePatch(patch_id="two-branches-%s" % stage_id, run_id=s.run_id,
                               stage_id=stage_id, stage_attempt=1,
                               parent_state_hash=s.state_hash(), operations=chosen,
                               execution_status="SUCCESS",
                               provenance={"purpose": "branch scope test"})
            problems = s.validate(patch)
            self.assertEqual([], problems, problems[:4])
            s.apply(patch)
        return s

    @staticmethod
    def mentions_both(findings):
        """A finding naming entities of both branches - the defect's signature."""
        return [f for f in findings if "A" in f and "B" in f
                and any(t in f for t in ("BOD-A", "RGP-A", "ASY-A", "TRN-A"))
                and any(t in f for t in ("BOD-B", "RGP-B", "ASY-B", "TRN-B"))]


# ======================================================================
# The slicing itself
# ======================================================================

class TestBranchPayloads(_TwoBranches):

    def test_one_payload_per_candidate(self):
        state = self.build()
        payloads = branch_payloads(state, SWEPT_CLEARANCE_FAMILIES)
        self.assertEqual(2, len(payloads))
        for payload in payloads:
            bodies = {e.get("body") for e in payload["Envelope"]}
            self.assertTrue(bodies <= {"BOD-A1", "BOD-A2"}
                            or bodies <= {"BOD-B1", "BOD-B2"},
                            "a payload carries both branches: %s" % bodies)

    def test_a_state_with_no_candidate_premise_is_one_branch(self):
        """Every single-mechanism fixture is this, and nothing about it changes."""
        s = DesignState(run_id="unbranched")
        self.add(s, "s03", "Body", "BOD-1")
        payloads = branch_payloads(s, ("Body",))
        self.assertEqual(1, len(payloads))
        self.assertEqual(["BOD-1"], [b["entity_id"] for b in payloads[0]["Body"]])

    def test_it_carries_only_the_families_it_was_asked_for(self):
        state = self.build()
        for payload in branch_payloads(state, ASSEMBLY_PATH_FAMILIES):
            self.assertEqual(set(ASSEMBLY_PATH_FAMILIES), set(payload))

    def test_it_builds_no_consumer_view_and_names_no_downstream_consumer(self):
        """A diagnostic that needed a downstream consumer's VIEW to know what it
        was looking at would be answerable only after the stage it informs.

        Importing the canonical branch RESOLVER is a different thing and is
        required: `branch_membership` is a pure function of state and contracts,
        not a view built for some consumer. What must be absent is view
        CONSTRUCTION and any downstream responsibility.

        THE CODE, not the prose: a docstring explaining what is not consulted has
        to name it, and a scan that read prose would find its own explanation.
        """
        from .test_s3_interface_readiness import _code_only
        code = _code_only(branch_payloads, swept_clearance_findings,
                          assembly_path_findings)
        for token in ("consumer_view_for", "build_consumer_view", "ConsumerView",
                      "feasibility", "selection", "ViewStatus", ".payload("):
            self.assertNotIn(token, code)

    def test_it_delegates_branch_ownership_and_traverses_nothing_itself(self):
        """The repository owns branch semantics once. A second traversal here
        would be a second branch ontology - and the narrower one it replaced
        answered "which branch" from a DIRECT premise, which is not the canonical
        definition: ownership is transitive over the depends-on graph."""
        from .test_s3_interface_readiness import _code_only
        code = _code_only(branch_payloads)
        self.assertIn("branch_membership", code)
        for token in ("_closure", "_reference_graph", "branches_built_on",
                      "_premises", "while "):
            self.assertNotIn(token, code,
                             "branch_payloads traverses or re-derives ownership "
                             "instead of asking the resolver")


class TestCanonicalOwnershipIsTransitiveAndScoped(_TwoBranches):
    """The two facts the direct-premise reading got wrong, in both directions."""

    def extra(self, state, ops):
        s04_families = {"Envelope", "State", "Transition"}
        for stage_id, chosen in (("s03", [o for o in ops
                                          if o.entity_type not in s04_families]),
                                 ("s04", [o for o in ops
                                          if o.entity_type in s04_families])):
            if not chosen:
                continue
            patch = StagePatch(patch_id="extra-%s-%d" % (stage_id,
                                                         len(state.applied_patches)),
                               run_id=state.run_id, stage_id=stage_id,
                               stage_attempt=1, parent_state_hash=state.state_hash(),
                               operations=chosen, execution_status="SUCCESS",
                               provenance={"purpose": "ownership test"})
            problems = state.validate(patch)
            self.assertEqual([], problems, problems[:4])
            state.apply(patch)

    def bodies_in(self, payload):
        return {e.get("body") for e in payload["Envelope"]}

    def test_an_entity_with_no_candidate_premise_belongs_to_the_branch_it_rests_on(self):
        """`ENV-A3` premises nothing and names a body that was authored from
        CND-A. Ownership is transitive over the depends-on graph, so it is
        CND-A's - which the direct-premise reading put in no branch at all."""
        state = self.build()
        self.extra(state, [
            Op("CREATE", "Body", "BOD-A3",
               {"instance_identity": "one", "role": "shim",
                "created_by_stage": "s03"}, "s03:topology", premise_refs=["CND-A"]),
            Op("CREATE", "Envelope", "ENV-A3",
               {"body": "BOD-A3", "extent": box((0.0, 0.0, 0.0)), "frame": "world",
                "maturity": "PROVISIONAL"}, "s04a:arrangement")])
        payloads = branch_payloads(state, SWEPT_CLEARANCE_FAMILIES)
        owning = [p for p in payloads if "BOD-A3" in self.bodies_in(p)]
        self.assertEqual(1, len(owning), "the transitively owned envelope is in %d "
                                         "payloads" % len(owning))
        self.assertTrue(self.bodies_in(owning[0]) <= {"BOD-A1", "BOD-A2", "BOD-A3"},
                        "it landed in the wrong branch: %s"
                        % self.bodies_in(owning[0]))

    def test_a_genuinely_unscoped_record_is_in_no_branch(self):
        """No candidate reaches it, so it belongs to no mechanism. Putting it in
        every branch would let one orphan obstruct every assembly at once."""
        state = self.build()
        self.extra(state, [
            Op("CREATE", "Body", "BOD-ORPHAN",
               {"instance_identity": "one", "role": "stray",
                "created_by_stage": "s03"}, "s03:topology"),
            Op("CREATE", "Envelope", "ENV-ORPHAN",
               {"body": "BOD-ORPHAN", "extent": box((0.0, 0.0, 0.0)),
                "frame": "world", "maturity": "PROVISIONAL"}, "s04a:arrangement")])
        for payload in branch_payloads(state, SWEPT_CLEARANCE_FAMILIES):
            self.assertNotIn("BOD-ORPHAN", self.bodies_in(payload))

    def test_an_orphan_obstructs_no_assembly_and_is_swept_into_by_nothing(self):
        state = self.build()
        self.extra(state, [
            Op("CREATE", "Body", "BOD-ORPHAN",
               {"instance_identity": "one", "role": "stray",
                "created_by_stage": "s03"}, "s03:topology"),
            Op("CREATE", "Envelope", "ENV-ORPHAN",
               {"body": "BOD-ORPHAN", "extent": box((0.0, 0.0, 0.0)),
                "frame": "world", "maturity": "PROVISIONAL"}, "s04a:arrangement")])
        for finding in swept_clearance_check(state) + assembly_path_check(state):
            self.assertNotIn("BOD-ORPHAN", finding)

    def test_the_transitively_owned_body_still_participates_in_its_own_branch(self):
        """Scoping correctly is not scoping away: placed on top of CND-A's parts,
        it must be found obstructing them."""
        state = self.build()
        self.extra(state, [
            Op("CREATE", "Body", "BOD-A3",
               {"instance_identity": "one", "role": "shim",
                "created_by_stage": "s03"}, "s03:topology", premise_refs=["CND-A"]),
            Op("CREATE", "Envelope", "ENV-A3",
               {"body": "BOD-A3", "extent": box((0.0, 0.0, 0.0)), "frame": "world",
                "maturity": "PROVISIONAL"}, "s04a:arrangement"),
            Op("CREATE", "AssemblyStep", "ASY-A3",
               {"order_index": 3, "body": "BOD-A3", "access_side": "+Z",
                "activates": [], "termination_strategy": "NONE",
                "path_kind": "RIGID", "depends_on": [],
                "insertion_direction": [0.0, 0.0, 1.0]},
               "s03b:relations", premise_refs=["CND-A"])])
        found = [f for f in assembly_path_check(state) if "BOD-A3" in f]
        self.assertTrue(found, "the transitively owned body obstructed nothing")
        for f in found:
            self.assertNotIn("BOD-B", f, "it was tested against the other branch")


# ======================================================================
# Cross-branch findings disappear; same-branch findings remain
# ======================================================================

class TestSweptClearanceIsBranchLocal(_TwoBranches):

    def test_no_finding_names_two_branches(self):
        state = self.build()
        findings = swept_clearance_check(state)
        self.assertEqual([], self.mentions_both(findings),
                         "a sweep was tested against another candidate's body")

    def test_a_within_branch_sweep_conflict_is_still_reported(self):
        """The same overlap, inside one mechanism, must still be found - otherwise
        this is scope removal rather than scope correction."""
        state = self.build()
        findings = swept_clearance_check(state)
        undeclared = [f for f in findings if f.startswith("SWEEP_MEETS_UNDECLARED_BODY")]
        self.assertTrue(undeclared, findings)
        for f in undeclared:
            tag = "A" if "BOD-A" in f else "B"
            self.assertNotIn("BOD-%s" % ("B" if tag == "A" else "A"), f)

    def test_declaring_the_interface_silences_it_within_the_branch(self):
        state = self.build(interfaced=True)
        findings = swept_clearance_check(state)
        self.assertEqual([], [f for f in findings
                              if f.startswith("SWEEP_MEETS_UNDECLARED_BODY")], findings)

    def test_the_pure_core_answers_about_the_payload_it_is_given(self):
        state = self.build()
        payloads = branch_payloads(state, SWEPT_CLEARANCE_FAMILIES)
        each = [swept_clearance_findings(p) for p in payloads]
        self.assertEqual(sorted(f for group in each for f in group),
                         sorted(swept_clearance_check(state)))

    def test_a_keep_out_of_another_branch_is_not_entered(self):
        state = self.build()
        patch = StagePatch(
            patch_id="keepout", run_id=state.run_id, stage_id="s03", stage_attempt=1,
            parent_state_hash=state.state_hash(),
            operations=[Op("CREATE", "FunctionalRegion", "FRG-B9",
                           {"role": "KEEP_OUT", "owning_bodies": ["BOD-B1"],
                            "required_by_actors": [], "reach_targets": [],
                            "volume": box((0.0, 0.0, 0.0), (4.0, 4.0, 4.0))},
                           "s03:topology", premise_refs=["CND-B"])],
            execution_status="SUCCESS", provenance={"purpose": "keep-out"})
        self.assertEqual([], state.validate(patch))
        state.apply(patch)
        entered = [f for f in swept_clearance_check(state)
                   if f.startswith("SWEEP_ENTERS_KEEP_OUT")]
        self.assertTrue(entered, "the keep-out was not entered by anything at all")
        for f in entered:
            self.assertNotIn("BOD-A", f,
                             "a body swept into ANOTHER candidate's keep-out")


class TestAssemblyPathIsBranchLocal(_TwoBranches):

    def test_no_obstruction_names_two_branches(self):
        state = self.build()
        findings = assembly_path_check(state)
        self.assertEqual([], self.mentions_both(findings),
                         "a step was obstructed by another candidate's body")

    def test_order_index_is_a_sequence_within_one_mechanism(self):
        """Both branches use order 1 and 2. Mixed, each branch's first body is
        'already placed' before the other's second."""
        state = self.build()
        for f in assembly_path_check(state):
            tag = "A" if "BOD-A" in f else "B"
            self.assertNotIn("BOD-%s" % ("B" if tag == "A" else "A"), f)

    def test_a_within_branch_obstruction_is_still_reported(self):
        state = self.build()
        findings = [f for f in assembly_path_check(state)
                    if f.startswith("ASSEMBLY_PATH_OBSTRUCTED")]
        self.assertTrue(findings, "the overlapping arrangement obstructed nothing")

    def test_moving_the_second_body_clear_removes_it(self):
        state = self.build(second_body_centre=(0.0, 0.0, 40.0))
        self.assertEqual([], [f for f in assembly_path_check(state)
                              if f.startswith("ASSEMBLY_PATH_OBSTRUCTED")])

    def test_the_pure_core_answers_about_the_payload_it_is_given(self):
        state = self.build()
        payloads = branch_payloads(state, ASSEMBLY_PATH_FAMILIES)
        each = [assembly_path_findings(p) for p in payloads]
        self.assertEqual(sorted(f for group in each for f in group),
                         sorted(assembly_path_check(state)))


# ======================================================================
# Completeness reads only what the responsibility declares
# ======================================================================

class TestS04bCompletenessReadsOnlyDeclaredPremises(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import yaml
        import os
        from . import _paths
        with open(os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                               "STAGE_RESPONSIBILITY_CONTRACT.yaml")) as fh:
            cls.responsibility = yaml.safe_load(fh)["stages"]["s04b"]
        cls.roles = {r for c in cls.responsibility["required_reasoning_premise_classes"]
                     for r in (c.get("requires_semantics") or [])}

    def declared_families(self):
        from ver3.assy_v3.state.design_state import Contracts
        families = Contracts().families
        return {name for name, spec in families.items()
                if set(spec.get("semantic_roles") or []) & self.roles}

    def test_the_responsibility_does_not_declare_mobility_disposition(self):
        """The premise the removed block read. Stated here so the test explains
        WHY the block had to go rather than merely that it is gone."""
        self.assertNotIn("mobility_disposition", self.roles)

    def test_completeness_reads_no_undeclared_premise_family(self):
        import inspect
        from ver3.assy_v3.state.design_state import Contracts
        source = inspect.getsource(S04BPlacementAndMotion.completeness)
        code = "\n".join(line for line in source.splitlines()
                         if not line.strip().startswith("#"))
        declared = self.declared_families()
        for family in Contracts().families:
            if family in declared:
                continue
            self.assertNotIn('"%s"' % family, code,
                             "s04b completeness reads %s, which its responsibility "
                             "does not declare" % family)

    def test_it_still_reads_the_families_it_does_declare(self):
        """The rule is 'read what you declared', not 'read nothing'."""
        import inspect
        source = inspect.getsource(S04BPlacementAndMotion.completeness)
        for family in ("Joint", "Configuration"):
            self.assertIn('"%s"' % family, source)

    def test_no_defeat_specification_rule_survives_in_this_stage(self):
        import inspect
        code = "\n".join(
            line for line in inspect.getsource(
                S04BPlacementAndMotion.completeness).splitlines()
            if not line.strip().startswith("#"))
        self.assertNotIn("defeat_specification", code)


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
