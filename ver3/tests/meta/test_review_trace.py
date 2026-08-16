"""The run trace is evidence, and the review UI is a projection of it.

Two properties this file exists to hold.

FIRST: a stage missing from a review screen reads as a stage that passed. So the
trace must carry a node for every responsibility in the canonical chain, INCLUDING
the ones that did not run and the ones that do not exist, each with its reason.
Silence is the one thing a review interface may not do.

SECOND: contract acceptance is not mechanical correctness. The trace records the
two separately and the UI renders them as two badges, and nothing in either may
compute a mechanical verdict. Human review starts NOT_REVIEWED and is only ever
set by a person.
"""

import json
import os
import re
import unittest

from . import _paths

from ver3.assy_v3.pipeline.progression import PRODUCING_RESPONSIBILITIES
from ver3.tools import build_review_ui as ui
from ver3.tools import run_trace as rt


class _Built(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.trace = rt.build_trace("BM-001")
        cls.by_id = {n["responsibility_id"]: n for n in cls.trace["nodes"]}


class TestTraceIsComplete(_Built):

    def test_every_producing_responsibility_has_a_node(self):
        """Including the four with no fixture. Absence would read as success."""
        for rid in PRODUCING_RESPONSIBILITIES:
            with self.subTest(responsibility=rid):
                self.assertIn(rid, self.by_id)

    def test_an_unexercised_node_says_why(self):
        for node in self.trace["nodes"]:
            if node["status"] in (rt.NOT_EXERCISED, rt.NOT_IMPLEMENTED,
                                  rt.BLOCKED_UPSTREAM):
                with self.subTest(node=node["responsibility_id"]):
                    self.assertTrue(node.get("reason"),
                                    "a node that did not run must say why")

    def test_the_embodiment_layer_is_a_real_node_now(self):
        """s05 exists. What it must never be is absent, or mis-typed.

        It was previously NOT_IMPLEMENTED and, worse, rendered with kind
        DETERMINISTIC beside a declared llm_role of HIGH - a classification a
        reviewer would reasonably believe. It is model-owned and says so.
        """
        s05 = self.by_id["s05"]
        self.assertEqual("MODEL", s05["kind"])
        # BM-001 has no embodiment authored, so it is NOT_EXERCISED - which is a
        # statement about this run, not about the implementation.
        self.assertEqual(rt.NOT_EXERCISED, s05["status"])
        self.assertTrue(s05.get("reason"))

    def test_the_deterministic_services_are_not_typed_as_model_stages(self):
        for rid in ("s06", "s07"):
            with self.subTest(node=rid):
                self.assertEqual("DETERMINISTIC", self.by_id[rid]["kind"])

    def test_identity_and_hashes_are_recorded(self):
        for key in ("run_id", "benchmark_id", "source_sha256", "repo_commit",
                    "trace_schema_version"):
            with self.subTest(key=key):
                self.assertTrue(self.trace.get(key))


class TestExecutedNodesResolve(_Built):

    def _executed(self):
        return [n for n in self.trace["nodes"]
                if n["status"] in (rt.LIVE_MODEL, rt.REPLAYED)]

    def test_at_least_one_node_actually_executed(self):
        """Otherwise every assertion below is vacuous."""
        self.assertTrue(self._executed())

    def test_stage_owner_and_responsibility_are_both_recorded(self):
        """The S9-C distinction, carried into the evidence a human reads."""
        for n in self._executed():
            with self.subTest(node=n["responsibility_id"]):
                self.assertTrue(n["stage_owner_id"])
                self.assertTrue(n["responsibility_id"])

    def test_consumer_view_provenance_resolves(self):
        for n in self._executed():
            with self.subTest(node=n["responsibility_id"]):
                self.assertIn("status", n["consumer_view"])
                self.assertIn("namespace_occupancy", n["consumer_view"])

    def test_state_before_and_after_resolve_to_the_diff(self):
        """The diff is derived, so it must agree with the two states it came from."""
        for n in self._executed():
            with self.subTest(node=n["responsibility_id"]):
                for fam, ids in (n["state_diff"]["added"] or {}).items():
                    after = set(n["state_after"].get(fam) or [])
                    before = set(n["state_before"].get(fam) or [])
                    self.assertTrue(set(ids) <= after - before)

    def test_a_rejected_node_applied_nothing(self):
        for n in self._executed():
            if n["contract"] == "REJECTED":
                with self.subTest(node=n["responsibility_id"]):
                    self.assertEqual(0, n["state_diff"]["added_total"])

    def test_prompt_and_response_are_carried_with_their_hashes(self):
        for n in self._executed():
            with self.subTest(node=n["responsibility_id"]):
                if n.get("prompt_text"):
                    self.assertTrue(n["prompt_pairing"])
                if n.get("raw_response"):
                    self.assertTrue(n["raw_response_sha256"])


class TestTheTraceNeverJudgesTheEngineering(_Built):

    def test_every_node_starts_not_reviewed(self):
        for n in self.trace["nodes"]:
            with self.subTest(node=n["responsibility_id"]):
                self.assertEqual(rt.NOT_REVIEWED, n["human_review"])

    def test_no_node_carries_a_mechanical_score(self):
        """No automated quality number anywhere. There is no such measurement."""
        blob = json.dumps(self.trace).lower()
        for banned in ("mechanical_score", "design_score", "quality_score"):
            with self.subTest(term=banned):
                self.assertNotIn(banned, blob)

    def test_the_trace_says_contract_is_not_mechanical(self):
        self.assertIn("contract_is_not_mechanical", self.trace["notes"])

    def test_replay_is_labelled_as_not_live(self):
        self.assertIn("replay_is_not_live", self.trace["notes"])
        for n in self.trace["nodes"]:
            if n["status"] == rt.REPLAYED:
                with self.subTest(node=n["responsibility_id"]):
                    self.assertNotEqual("LIVE", n.get("response_source"))


class TestReferenceCadIsLabelled(_Built):

    def test_there_are_references_to_label(self):
        """Both loops below iterate the reference list. With no references they
        pass while checking nothing, and 'reference CAD is correctly labelled'
        would be true of a trace carrying no reference CAD at all."""
        self.assertTrue(self.trace["reference_cad"]["references"])

    def test_reference_cad_is_not_claimed_as_pipeline_output(self):
        self.assertFalse(self.trace["reference_cad"]["is_pipeline_output"])

    def test_no_reference_claims_traceability_it_does_not_have(self):
        for ref in self.trace["reference_cad"]["references"]:
            with self.subTest(ref=ref["reference_id"]):
                self.assertFalse(ref["traceable_to_design_entities"])

    def test_referenced_artifact_paths_exist(self):
        """A review UI that links a missing file degrades silently."""
        for ref in self.trace["reference_cad"]["references"]:
            for rel in (ref["step_files"] + ref["screenshots"])[:12]:
                with self.subTest(path=rel):
                    self.assertTrue(os.path.isfile(os.path.join(_paths.REPO_ROOT, rel)))


class TestTheUiIsAProjectionOfTheTrace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.trace = rt.build_trace("BM-001")
        cls.dir = tempfile.mkdtemp(prefix="assy-ui-")
        cls.path = ui.build(cls.trace, cls.dir)
        with open(cls.path) as fh:
            cls.html = fh.read()

    def test_it_writes_an_index_entry_point(self):
        self.assertTrue(self.path.endswith("index.html"))
        self.assertTrue(os.path.isfile(self.path))

    def test_the_page_is_self_contained(self):
        """No CDN. It has to work over a forwarded port with no internet."""
        for remote in ("http://", "https://"):
            with self.subTest(scheme=remote):
                self.assertNotIn('src="%s' % remote, self.html)
                self.assertNotIn('href="%s' % remote, self.html)

    def test_the_trace_is_embedded_rather_than_refetched(self):
        self.assertIn("const TRACE =", self.html)

    def test_the_ui_derives_nothing_the_trace_does_not_carry(self):
        """It must not open DesignState, a fixture or a contract itself."""
        source = open(ui.__file__).read()
        for banned in ("DesignState(", "yaml.safe_load", "fixtures/responses"):
            with self.subTest(term=banned):
                self.assertNotIn(banned, source)

    def test_it_renders_both_status_kinds_separately(self):
        self.assertIn("human review", self.html.lower())
        self.assertIn("contract", self.html.lower())

    def test_it_warns_that_contract_is_not_mechanical_correctness(self):
        self.assertIn("not a claim that the mechanism", self.html)

    def test_every_renderable_status_has_a_legend_entry(self):
        """A badge the page cannot explain is a badge the reviewer cannot weigh.

        The legend was keyed on the NAMES of the status constants rather than
        their VALUES - `REPLAYED` for a status whose value is `REPLAY`, and
        `LIVE_MODEL` for `LIVE_DEEPSEEK`. Those entries matched nothing, so a
        page showing two REPLAY nodes explained neither while the legend itself
        looked complete. Derived from STATUS_CLASS, which is the UI's own list
        of statuses it will render, so renaming one fails here.
        """
        source = open(ui.__file__).read()
        meaning = re.search(r"const PROVENANCE_MEANING = \{(.*?)\n\};",
                            source, re.S)
        self.assertTrue(meaning, "the legend table is gone or was renamed")
        explained = set(re.findall(r"^\s*([A-Z_]+):", meaning.group(1), re.M))
        self.assertTrue(explained, "the legend parsed to nothing")
        for status in ui.STATUS_CLASS:
            with self.subTest(status=status):
                self.assertIn(status, explained,
                              "%s renders as a badge but the legend never "
                              "explains it" % status)

    def test_section_numbers_are_not_hardcoded_per_template(self):
        """Numbers that skip read as sections that failed to load.

        They were written for the fullest node, so a deterministic node - which
        has no prompt and no raw response - rendered 1,2,3,4 and then 11. A
        shared counter numbers them in emission order instead.
        """
        source = open(ui.__file__).read()
        literals = re.findall(r"section\('(\d+) \u00b7 ", source)
        self.assertTrue(literals, "no numbered sections found to check")
        self.assertIn("++SEC", source,
                      "section numbers are literal again; a node that skips a "
                      "section will show a gap")
        self.assertNotIn("<h2>11 \u00b7", source,
                         "the review header bypasses the counter")

    def test_the_legend_explains_the_statuses_actually_on_this_page(self):
        """The end-to-end form: what a reviewer of THIS page can actually read."""
        for status in {n["status"] for n in self.trace["nodes"]}:
            with self.subTest(status=status):
                self.assertIn(status, self.html)

    def test_every_node_reaches_the_page(self):
        for n in self.trace["nodes"]:
            with self.subTest(node=n["responsibility_id"]):
                self.assertIn(n["responsibility_id"], self.html)

    def test_human_review_is_stored_separately_from_the_trace(self):
        """The UI writes to browser storage and exports a separate artifact; it
        never edits DesignState and never rewrites the trace."""
        source = open(ui.__file__).read()
        self.assertIn("localStorage", source)
        self.assertIn("human_review-", source)
        self.assertNotIn("state.apply", source)


class TestTheUnimplementedStagesAreSpecifiedNotUndefined(_Built):
    """`NOT_IMPLEMENTED` must mean unbuilt, never unspecified.

    A draft of the gap specification claimed `ConstructionStatement` had no
    required fields. It has four. The claim came from an audit that looked only
    in `entity_families`, found nothing, and treated the miss as an empty
    definition - so a family that IS fully typed was reported as a hole in the
    contract. This resolves every declared family across BOTH sections and fails
    on absence rather than defaulting.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        state = _paths.contract("DESIGN_STATE_CONTRACT.yaml")
        cls.fams = dict(state["entity_families"])
        cls.fams.update(state["assurance_families"])

    def test_every_declared_family_resolves_and_is_typed(self):
        # No node declares families now that all three are implemented; the
        # check stays because a future NOT_IMPLEMENTED node must still resolve.
        for n in self.trace["nodes"]:
            for family in (n.get("declared_families") or []):
                with self.subTest(node=n["responsibility_id"], family=family):
                    self.assertIn(family, self.fams,
                                  "declared family missing from BOTH contract "
                                  "sections; a one-section lookup would have "
                                  "reported this as undefined")
                    required = self.fams[family].get("required_fields")
                    self.assertTrue(required,
                                    "%s resolves but declares no required "
                                    "fields" % family)

    def test_construction_statement_is_fully_typed(self):
        """The specific claim that was wrong, pinned so it cannot recur."""
        cs = self.fams["ConstructionStatement"]
        self.assertEqual(["entity_id", "operation", "operands", "parameters"],
                         cs["required_fields"])

    def test_the_solver_and_compiler_declare_no_model_role(self):
        """s06 and s07 are deterministic by contract. A paid call there is waste."""
        for rid in ("s06", "s07"):
            with self.subTest(node=rid):
                self.assertEqual("NONE", self.by_id[rid]["declared_llm_role"])


class TestS02SchemaExampleHardening(unittest.TestCase):
    """S9-E: the prompt showed ASM-0001 as the example while declaring it taken."""

    def test_no_schema_example_is_an_instantiable_id(self):
        from ver3.assy_v3.stages.s02_obligation_and_candidates import (
            S02ObligationAndCandidates)
        schema = S02ObligationAndCandidates.render_response_schema()
        self.assertEqual([], re.findall(r'id "[A-Z][A-Z0-9]*-\d+"', schema))

    def test_the_format_is_still_taught(self):
        from ver3.assy_v3.stages.s02_obligation_and_candidates import (
            S02ObligationAndCandidates)
        self.assertIn('id "ASM-NNNN"',
                      S02ObligationAndCandidates.render_response_schema())


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
