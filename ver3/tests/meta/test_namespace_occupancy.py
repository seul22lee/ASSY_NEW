"""A responsibility that may CREATE into a family must see which ids are taken.

S9-E, debt D-2. THE RULE, and it names no stage and no family:

    If a producing responsibility may CREATE entities in family F, and committed
    DesignState may already contain entities in F, the responsibility must
    receive enough identity-level context to know which ids in F are occupied.

WHAT WENT WRONG WITHOUT IT

`Assumption` is `universally_ownable`, so s01 and s02 author into one namespace.
s01 commits ASM-0001 and ASM-0002. s02's consumer view carried no Assumption at
all - correctly, since a co-produced family is excluded from the SEMANTIC minimum
- and the response schema shows each family's example id at first index. Three
independent live DeepSeek attempts were rejected with the identical DUPLICATE_ID:
ASM-0001. The model was answering the question it was given; the boundary had not
given it the one fact it needed.

WHAT THIS IS NOT

It is not semantic access. s02 needs to know ASM-0001 is spent; it does not need
to know what s01 assumed. And it is not a write permission: an id being visible
says nothing about who may change the entity holding it.
"""

import ast
import inspect
import json
import unittest

from . import _paths
from . import output_semantics_audit as audit

from ver3.assy_v3.pipeline.progression import PRODUCING_RESPONSIBILITIES
from ver3.assy_v3.stages.base import render_namespace_occupancy
from ver3.assy_v3.stages.s01_requirement_capture import S01RequirementCapture
from ver3.assy_v3.stages.s02_obligation_and_candidates import S02ObligationAndCandidates
from ver3.assy_v3.state.design_state import DesignState
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.view import consumer_view as cv
from ver3.assy_v3.view.boundary import responsibility_contract

from .test_output_semantics_drift import PRODUCING_CLASSES

#: The retained S9-E paid evidence. The live s01 that produced the collision -
#: used because the agent-authored fixtures emit NO assumptions, which is exactly
#: why the defect survived until an independent model was asked.
LIVE_S01 = "ver3/live_runs/s9e/canary4/BM-001/s01.a1.raw.json"


def commit_live_s01(state):
    """Apply the retained live s01 response and return the ids it occupied."""
    import os
    path = os.path.join(_paths.REPO_ROOT, LIVE_S01)
    with open(path) as fh:
        body = json.load(fh)
    parsed = {k: v for k, v in body.items() if not k.startswith("_")}
    ops = S01RequirementCapture().to_operations(parsed, {"request_text": "x"})
    patch = StagePatch(patch_id="p1", run_id=state.run_id, stage_id="s01",
                       stage_attempt=1, parent_state_hash=state.state_hash(),
                       operations=ops, execution_status="SUCCESS",
                       provenance={"purpose": "test", "provider": "test"})
    problems = state.validate(patch)
    assert not problems, problems
    state.apply(patch)
    return parsed


class TestOccupancyIsDerivedFromAuthoritativeState(unittest.TestCase):
    """Occupancy comes from committed DesignState and from nothing else."""

    def setUp(self):
        self.state = DesignState(run_id="occupancy")
        self.parsed = commit_live_s01(self.state)
        self.occupied = sorted(e["entity_id"]
                               for e in self.state.family("Assumption"))

    def test_the_upstream_state_actually_occupies_the_family(self):
        """The premise of every test below. Without it they prove nothing."""
        self.assertEqual(["ASM-0001", "ASM-0002"], self.occupied)

    def test_the_consumer_view_carries_the_occupied_ids(self):
        """POSITIVE CASE. s02 may create Assumption; the view says which are taken."""
        view = S02ObligationAndCandidates().consumer_view(self.state)
        self.assertEqual(self.occupied, view.occupancy.get("Assumption"))

    def test_occupancy_matches_state_for_every_creatable_family(self):
        """Derived, not sampled. Every family s02 may create, compared to state."""
        view = S02ObligationAndCandidates().consumer_view(self.state)
        families = cv.creatable_families("s02", responsibility_contract())
        for family in sorted(families):
            with self.subTest(family=family):
                in_state = sorted(e["entity_id"] for e in self.state.family(family))
                self.assertEqual(in_state, view.occupancy.get(family, []))

    def test_an_invalidated_id_is_still_occupied(self):
        """Validity and occupancy are different questions.

        `DesignState.validate` reports DUPLICATE_ID against the whole entity
        table, so withdrawing an assumption does not hand its id back. Offering
        it as available would manufacture a collision and blame the model.
        """
        patch = StagePatch(
            patch_id="inv", run_id=self.state.run_id, stage_id="s01",
            stage_attempt=2, parent_state_hash=self.state.state_hash(),
            operations=[Op("INVALIDATE", "Assumption", "ASM-0001", {},
                           "s01:test", reason="withdrawn by the test")],
            execution_status="SUCCESS",
            provenance={"purpose": "t", "provider": "t"})
        self.assertEqual([], self.state.validate(patch))
        self.state.apply(patch)
        self.assertEqual([], [e for e in self.state.standing("Assumption")
                              if e["entity_id"] == "ASM-0001"])
        view = S02ObligationAndCandidates().consumer_view(self.state)
        self.assertIn("ASM-0001", view.occupancy["Assumption"])

    def test_occupancy_is_recorded_on_the_view(self):
        """A reviewer must be able to read back what the stage was told."""
        view = S02ObligationAndCandidates().consumer_view(self.state)
        self.assertEqual({"Assumption": ["ASM-0001", "ASM-0002"]},
                         view.as_dict()["namespace_occupancy"])

    def test_a_family_with_nothing_in_it_is_absent_rather_than_empty(self):
        view = S02ObligationAndCandidates().consumer_view(self.state)
        self.assertNotIn("Obligation", view.occupancy)


class TestTheActualPromptCarriesIt(unittest.TestCase):
    """The information has to survive to the text the model reads.

    State -> ConsumerView -> prompt renderer -> the prompt actually sent. A view
    that holds the ids and a prompt that does not is the same defect one layer
    further down.
    """

    def setUp(self):
        self.state = DesignState(run_id="prompt")
        self.parsed = commit_live_s01(self.state)
        self.stage = S02ObligationAndCandidates()
        self.view = self.stage.consumer_view(self.state)
        self.prompt = self.stage.build_prompt({
            "consumer_view": self.view.payload(),
            "namespace_occupancy": self.view.occupancy})

    def test_every_occupied_id_appears_in_the_prompt(self):
        for eid in sorted(e["entity_id"] for e in self.state.family("Assumption")):
            with self.subTest(entity_id=eid):
                self.assertIn(eid, self.prompt)

    def test_the_prompt_says_they_are_taken_rather_than_available(self):
        self.assertIn("IDS ALREADY IN USE", self.prompt)

    def test_the_schema_example_is_marked_as_a_format_and_not_an_offer(self):
        """S9-E secondary finding. `id "ASM-0001"` is a format example, and the
        first index is commonly the id already spent. Wording alone was never the
        fix - the occupancy list above is - but leaving the example unqualified
        beside it would still read as an offer."""
        self.assertIn("FORMAT of an id", self.prompt)

    def test_the_schema_example_is_not_an_instantiable_id(self):
        """S9-E, observed live: two cues about ASM-0001 in one prompt.

        The occupancy section said it was taken; the schema example showed it as
        the id to write. The model emitted it. The occupancy list is the real
        mechanism and is untouched - this asserts the competing cue is gone.
        """
        schema = S02ObligationAndCandidates.render_response_schema()
        for occupied in ("ASM-0001", "ASM-0002"):
            with self.subTest(id=occupied):
                self.assertNotIn(occupied, schema)

    def test_no_schema_example_is_a_concrete_ordinal(self):
        """The property, not the one family that collided.

        Which families are occupied depends on committed state, and the schema
        renderer has none - so a per-family exception would be the same
        anchoring waiting for a different responsibility.
        """
        import re
        schema = S02ObligationAndCandidates.render_response_schema()
        concrete = re.findall(r'id "([A-Z][A-Z0-9]*-\d+)"', schema)
        self.assertEqual([], concrete)

    def test_the_id_format_is_still_communicated(self):
        """Removing the example must not remove the shape it taught."""
        stage = S02ObligationAndCandidates()
        schema = stage.render_response_schema()
        self.assertIn('id "ASM-NNNN"', schema)
        self.assertIn('id "OBL-NNNN"', schema)
        state = DesignState(run_id="fmt")
        commit_live_s01(state)
        view = stage.consumer_view(state)
        prompt = stage.build_prompt({"consumer_view": view.payload(),
                                     "namespace_occupancy": view.occupancy})
        # The prompt must SAY that NNNN is a placeholder, or the format it shows
        # is ambiguous in a new way.
        self.assertIn("NNNN stands for", prompt)

    def test_the_occupied_ids_are_still_the_only_concrete_asm_ids_shown(self):
        """After the change, a concrete ASM id in the prompt means 'taken'."""
        import re
        state = DesignState(run_id="only")
        commit_live_s01(state)
        stage = S02ObligationAndCandidates()
        view = stage.consumer_view(state)
        prompt = stage.build_prompt({"consumer_view": view.payload(),
                                     "namespace_occupancy": view.occupancy})
        self.assertEqual({"ASM-0001", "ASM-0002"}, set(re.findall(r"ASM-\d+", prompt)))

    def test_a_stage_with_no_occupancy_gets_the_prompt_it_always_got(self):
        """s01 runs against empty state, so nothing is appended to its prompt."""
        empty = DesignState(run_id="empty")
        view = S01RequirementCapture().consumer_view(empty)
        self.assertEqual({}, view.occupancy)
        self.assertEqual("", render_namespace_occupancy(view.occupancy))


class TestLeastPrivilege(unittest.TestCase):
    """Identity is not semantics. Seeing an id must not deliver the entity."""

    def setUp(self):
        self.state = DesignState(run_id="privilege")
        self.parsed = commit_live_s01(self.state)
        self.stage = S02ObligationAndCandidates()
        self.view = self.stage.consumer_view(self.state)
        self.prompt = self.stage.build_prompt({
            "consumer_view": self.view.payload(),
            "namespace_occupancy": self.view.occupancy})

    def test_the_semantic_payload_still_carries_no_assumption(self):
        self.assertNotIn("Assumption", self.view.payload())

    def test_no_assumption_field_content_reaches_the_prompt(self):
        """The ids arrive; what the assumptions SAY does not."""
        for a in self.parsed.get("assumptions") or []:
            for field in ("statement", "why", "would_be_invalidated_by"):
                value = a.get(field)
                if isinstance(value, str) and len(value) > 20:
                    with self.subTest(id=a["id"], field=field):
                        self.assertNotIn(value, self.prompt)

    def test_occupancy_holds_ids_and_nothing_else(self):
        for family, ids in self.view.occupancy.items():
            with self.subTest(family=family):
                self.assertTrue(all(isinstance(i, str) for i in ids))


class TestWriteAuthorityIsUnchanged(unittest.TestCase):
    """Visibility is not authority. This is the freeze the repair must not touch."""

    def setUp(self):
        self.state = DesignState(run_id="authority")
        commit_live_s01(self.state)

    def _s02_patch(self, op):
        return StagePatch(patch_id="a", run_id=self.state.run_id, stage_id="s02",
                          stage_attempt=1,
                          parent_state_hash=self.state.state_hash(),
                          operations=[op], execution_status="SUCCESS",
                          provenance={"purpose": "t", "provider": "t"})

    def test_seeing_the_id_does_not_let_s02_reuse_it(self):
        """The boundary that caught the live collision still catches it."""
        problems = self.state.validate(self._s02_patch(
            Op("CREATE", "Assumption", "ASM-0001",
               {"statement": "x", "inferred_by_stage": "s02", "why": "y",
                "would_be_invalidated_by": "z"}, "s02:derivation")))
        self.assertTrue(any("DUPLICATE_ID" in p for p in problems), problems)

    def test_seeing_the_id_does_not_grant_update_authority(self):
        problems = self.state.validate(self._s02_patch(
            Op("EXTEND", "Assumption", "ASM-0001", {"why": "rewritten by s02"},
               "s02:derivation")))
        self.assertTrue(problems, "s02 extended an entity it does not own")

    def test_a_genuinely_new_id_in_the_shared_family_is_still_accepted(self):
        """Least privilege must not become no privilege: s02 may still assume."""
        problems = self.state.validate(self._s02_patch(
            Op("CREATE", "Assumption", "ASM-0003",
               {"statement": "x", "inferred_by_stage": "s02", "why": "y",
                "would_be_invalidated_by": "z"}, "s02:derivation")))
        self.assertEqual([], problems)


class TestMutation(unittest.TestCase):
    """Omit one occupied id from the derived view and require a failure."""

    def setUp(self):
        self.state = DesignState(run_id="mutation")
        commit_live_s01(self.state)
        self.view = S02ObligationAndCandidates().consumer_view(self.state)

    def _completeness_problems(self, occupancy):
        """Does this occupancy account for every id state actually holds?

        The check the mutation has to trip. Compared against DesignState, which
        is the only authority on what is spent.
        """
        problems = []
        for family in sorted(cv.creatable_families("s02", responsibility_contract())):
            in_state = {e["entity_id"] for e in self.state.family(family)}
            declared = set(occupancy.get(family) or [])
            for missing in sorted(in_state - declared):
                problems.append("%s occupies %s and the view does not say so"
                                % (family, missing))
        return problems

    def test_the_derived_view_is_complete(self):
        self.assertEqual([], self._completeness_problems(self.view.occupancy))

    def test_dropping_one_occupied_id_is_detected(self):
        mutated = {k: list(v) for k, v in self.view.occupancy.items()}
        mutated["Assumption"].remove("ASM-0001")
        problems = self._completeness_problems(mutated)
        self.assertTrue(any("ASM-0001" in p for p in problems), problems)

    def test_dropping_the_whole_family_is_detected(self):
        mutated = {k: list(v) for k, v in self.view.occupancy.items()}
        del mutated["Assumption"]
        self.assertEqual(2, len(self._completeness_problems(mutated)))

    def test_the_omission_has_a_real_cost(self):
        """Why the mutation matters: the omitted id is one the boundary refuses.

        This is the whole S9-E blocker in one test - the prompt never says the id
        is taken, the model chooses it, the patch is rejected, and the rejection
        reads as the model's failure.

        ASSERTED ON THE OCCUPANCY BLOCK, not on the whole prompt, and the reason
        is the finding itself: `ASM-0001` appears in the prompt either way,
        because it is the response schema's format example for the family. That
        is precisely what the model followed into the collision. So "is the id in
        the prompt" is the wrong question and always was; the question is whether
        anything TELLS the model the id is spent.
        """
        mutated = {"Assumption": ["ASM-0002"]}
        block = render_namespace_occupancy(mutated)
        self.assertIn("ASM-0002", block)
        self.assertNotIn("ASM-0001", block)
        self.assertIn("ASM-0001", render_namespace_occupancy(self.view.occupancy))
        problems = self.state.validate(StagePatch(
            patch_id="a", run_id=self.state.run_id, stage_id="s02",
            stage_attempt=1, parent_state_hash=self.state.state_hash(),
            operations=[Op("CREATE", "Assumption", "ASM-0001",
                           {"statement": "x", "inferred_by_stage": "s02",
                            "why": "y", "would_be_invalidated_by": "z"},
                           "s02:derivation")],
            execution_status="SUCCESS",
            provenance={"purpose": "t", "provider": "t"}))
        self.assertTrue(any("DUPLICATE_ID" in p for p in problems), problems)


class TestGenerality(unittest.TestCase):
    """The mechanism must not be about s02, Assumption, or the prefix ASM-."""

    def test_assumption_is_not_the_only_shared_create_namespace(self):
        """AUDIT of every family more than one responsibility may create.

        `UnresolvedDecision` is the second: s02 authors one, and s03a and s03b
        may then author into a family already holding UNR- ids. A mechanism built
        for Assumption alone would have left that collision live.
        """
        creates = audit.responsibility_creates(PRODUCING_CLASSES)
        producers = {}
        for rid in PRODUCING_RESPONSIBILITIES:
            for family in creates[rid]:
                producers.setdefault(family, []).append(rid)
        shared = {f: rs for f, rs in producers.items() if len(rs) > 1}
        self.assertIn("Assumption", shared)
        self.assertIn("UnresolvedDecision", shared)

    def test_every_shared_namespace_is_covered_without_being_named(self):
        """Every later producer of a shared family gets that family's occupancy.

        Derived from the contract, so a family that becomes shared tomorrow is
        covered the day its declaration says so.
        """
        creates = audit.responsibility_creates(PRODUCING_CLASSES)
        producers = {}
        for rid in PRODUCING_RESPONSIBILITIES:
            for family in creates[rid]:
                producers.setdefault(family, []).append(rid)
        contract = responsibility_contract()
        for family, rids in sorted(producers.items()):
            if len(rids) < 2:
                continue
            for rid in rids:
                with self.subTest(family=family, responsibility=rid):
                    self.assertIn(family, cv.creatable_families(rid, contract))

    def test_a_synthetic_family_and_responsibility_work_unchanged(self):
        """No production string is required for the mechanism to apply.

        The contract is the only input that decides which families are watched,
        so a responsibility declaring a family this repository has never had gets
        occupancy for it with no code change.
        """
        state = DesignState(run_id="synthetic")
        commit_live_s01(state)
        synthetic = {"stages": {"sZZ": {
            "permitted_output_semantics": ["Requirement", "Joint.frame_origin"]}}}
        occupancy = cv.derive_namespace_occupancy("sZZ", state, synthetic)
        self.assertEqual(sorted(e["entity_id"] for e in state.family("Requirement")),
                         occupancy["Requirement"])
        # The dotted entry is a FIELD on somebody else's entity. It creates no id
        # and must not be read as a family to watch.
        self.assertNotIn("Joint", occupancy)

    def test_the_mechanism_names_no_family_and_no_stage_in_its_code(self):
        """Source check. Comments may explain the history; code may not encode it.

        Docstrings and comments are prose - the rationale above deliberately says
        `Assumption` and `ASM-0001`, because a rule whose reason cannot be written
        down is a rule nobody can review. What must not appear is a STRING LITERAL
        or an IDENTIFIER carrying the family, which is what would make the
        mechanism about one case.
        """
        for fn in (cv.derive_namespace_occupancy, cv.creatable_families,
                   render_namespace_occupancy):
            with self.subTest(function=fn.__name__):
                tree = ast.parse(inspect.getsource(fn).lstrip())
                doc = _paths.docstring_nodes(tree)
                names = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                            and id(node) not in doc:
                        names.append(node.value)
                    elif isinstance(node, ast.Name):
                        names.append(node.id)
                    elif isinstance(node, ast.Attribute):
                        names.append(node.attr)
                for banned in ("Assumption", "ASM", "s02", "UnresolvedDecision"):
                    self.assertFalse(
                        any(banned in n for n in names),
                        "%s mentions %r in code: %s"
                        % (fn.__name__, banned, [n for n in names if banned in n]))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
