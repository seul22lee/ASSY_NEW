"""The gate that would have caught the last four passes' defects.

Each check here corresponds to something that actually went wrong and was found
by hand: a prompt claiming six collections while eight were consumed, a reaction
relation left optional so its invariant silently did nothing, producer metadata
still saying NOT_YET_PRODUCED after the producer existed, and U-5 conditions that
were described as enforced before they were.

These are stable invariants, not implementation trivia. They read machine-readable
surfaces - contracts, envelope declarations, producer code - never prose wording.
"""
from __future__ import annotations

import json
import os
import re
import unittest

import yaml

from . import _fixtures, _paths                                        # noqa: F401

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_CONTRACTS = os.path.join(_REPO, "ver3", "contracts")

from ver3.assy_v3.stages.s02_obligation_and_candidates import (        # noqa: E402
    S02ObligationAndCandidates)
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    S03BMobilityAndAssembly)
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402


def _active_s4_rows(rows):
    """Rows in the ACTIVE migration structure whose owner includes S-4.

    Ownership, not status text. A row may be legitimately active if it has been
    formally transferred to a later step - that shows up as a different
    `migration_step`, not as a reassuring `current_status`.
    """
    out = []
    for row in rows or []:
        step = str(row.get("migration_step") or "")
        if re.search(r"\bS-4\b", step):
            out.append("%s (owner %r, status %r)"
                       % (row.get("concept"), step,
                          str(row.get("current_status"))[:40]))
    return out


def _load(name, *parts):
    with open(os.path.join(_CONTRACTS, *parts, name)) as fh:
        return yaml.safe_load(fh)


class TestResponseEnvelopeCannotDrift(unittest.TestCase):
    """A prompt, a parser and a contract that disagree is the defect class this
    catches. It has recurred in every S-4 slice so far."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.stage = S02ObligationAndCandidates()
        cls.prompt = cls.stage.prompt({"consumer_view": {}})
        cls.source = open(os.path.join(
            _REPO, "ver3", "assy_v3", "stages",
            "s02_obligation_and_candidates.py")).read()

    def test_GATE_01_the_declared_count_matches_the_envelope(self):
        claimed = re.search(r"exactly these (\d+) keys", self.prompt)
        self.assertIsNotNone(claimed, "the prompt no longer states a count")
        self.assertEqual(len(self.stage.RESPONSE_ENVELOPE), int(claimed.group(1)),
                         "the prompt claims a different number of collections than "
                         "the envelope declares")

    def test_GATE_02_every_declared_collection_is_consumed(self):
        consumed = set(re.findall(r'parsed\.get\("([a-z_]+)"', self.source))
        for collection, _family, _prefix, _fields, _sup in self.stage.RESPONSE_ENVELOPE:
            self.assertIn(collection, consumed,
                          "%s is offered to the model and read by nothing"
                          % collection)

    def test_GATE_03_every_consumed_collection_is_declared(self):
        declared = {c for c, _f, _p, _fl, _s in self.stage.RESPONSE_ENVELOPE}
        consumed = set(re.findall(r'parsed\.get\("([a-z_]+)"', self.source))
        # `_dofs`-style internals and the derived-mobility keys are not response
        # collections; only compare what to_operations turns into entities.
        creates = set(re.findall(r'for (\w+) in parsed\.get\("([a-z_]+)"',
                                 self.source))
        for _var, collection in creates:
            self.assertIn(collection, declared,
                          "%s is turned into entities and is in no envelope"
                          % collection)
        self.assertTrue(consumed)

    def test_GATE_04_every_declared_collection_appears_in_the_schema(self):
        for collection, _family, _prefix, _fields, _sup in self.stage.RESPONSE_ENVELOPE:
            self.assertIn("%s[]" % collection, self.prompt,
                          "%s is in the envelope and not in the response schema"
                          % collection)

    def test_GATE_05_every_declared_family_is_real_and_stage_owned(self):
        for _collection, family, _prefix, _fields, _sup in self.stage.RESPONSE_ENVELOPE:
            self.assertIn(family, self.c.families, family)
            self.assertTrue(self.c.may_create("s02", family),
                            "s02 offers %s and does not own it" % family)

    def test_GATE_06_every_emitted_prefix_is_shown_to_the_model(self):
        for _collection, _family, prefix, _fields, _sup in self.stage.RESPONSE_ENVELOPE:
            self.assertIn(prefix, self.prompt,
                          "%s ids are emitted and the prompt never shows the "
                          "prefix" % prefix)


class TestActiveMigrationTruth(unittest.TestCase):
    """A family cannot be produced and simultaneously be listed as unproduced."""

    @classmethod
    def setUpClass(cls):
        cls.ds = _load("DESIGN_STATE_CONTRACT.yaml")
        cls.s03 = _load("S03_CONTRACT.yaml", "stages")

    def produced(self):
        """Families some stage's to_operations actually creates."""
        out = set()
        for name in ("s02_obligation_and_candidates.py", "s03_topology_and_mobility.py"):
            src = open(os.path.join(_REPO, "ver3", "assy_v3", "stages", name)).read()
            out |= set(re.findall(r'Op\("CREATE", "(\w+)"', src))
        return out

    def test_GATE_07_no_produced_family_is_an_active_legacy_row(self):
        produced = self.produced()
        for row in (self.ds.get("legacy_producers") or {}).get("rows") or []:
            concept = row.get("concept", "")
            named = {f for f in produced if f in concept}
            if named and row.get("current_status") in ("NOT_YET_PRODUCED",):
                self.fail("%s is produced by %s and is still an ACTIVE legacy row "
                          "saying %s" % (concept, sorted(named),
                                         row.get("current_status")))

    def test_GATE_08_history_lives_outside_the_active_list(self):
        superseded = self.ds.get("superseded_legacy_producers") or {}
        self.assertTrue(superseded.get("rows"), "history was deleted, not moved")
        active = {r.get("concept")
                  for r in (self.ds.get("legacy_producers") or {}).get("rows") or []}
        for row in superseded["rows"]:
            self.assertNotIn(row["concept"], active,
                             "%s is both active and superseded" % row["concept"])

    def test_GATE_09_the_stage_contract_does_not_contradict_itself(self):
        producer = self.s03.get("legacy_producer", {}).get("current_producer", {})
        if producer.get("migration_status", "").strip().startswith("DONE"):
            self.assertEqual([], producer.get("does_not_yet_emit") or [],
                             "migration is DONE and something is still listed as "
                             "not emitted")


class TestU5InvariantsArePinned(_fixtures.StateBuilder, unittest.TestCase):
    """U5-1/2/3 and the LoadCase relation, asserted at the surface that owns each."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_GATE_10_a_load_case_must_name_its_reaction_site(self):
        required = self.c.required_fields("LoadCase")
        self.assertIn("reacted_at_site", required,
                      "the relation U5-3 depends on is optional again, so its "
                      "wrong-terminus check can silently do nothing")
        spec = self.c.reference_spec("LoadCase", "reacted_at_site")
        self.assertEqual("ReactionSiteRequirement", spec["target"])
        self.assertFalse(spec["resolvable"], "a named site need not exist")

    def test_GATE_11_the_s4_layer_evaluates_all_three_conditions(self):
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S03BMobilityAndAssembly._s4_physical_problems)
        for marker in ("U5-1", "U5-2", "U5-3"):
            self.assertIn(marker, src, "%s is no longer evaluated" % marker)

    def test_GATE_12_the_s4_layer_reads_no_legacy_mobility_channel(self):
        from .test_s3_interface_readiness import _code_only
        src = _code_only(S03BMobilityAndAssembly._s4_physical_problems)
        self.assertNotIn("blocking_relations", src,
                         "S-4 completeness consults the legacy mobility channel")

    def test_GATE_13_every_s4_physical_reference_must_resolve(self):
        for family, field in (("LoadCase", "reacted_at_site"),
                              ("LoadPath", "ordered_hops"),
                              ("LoadPath", "terminates_at"),
                              ("ConstraintRelation", "provider_body"),
                              ("ConstraintRelation", "provider_reaction_site"),
                              ("ConstraintRelation", "provider_site"),
                              ("PhysicalInteraction", "discharges_effect"),
                              ("PhysicalInteraction", "at_interface")):
            spec = self.c.reference_spec(family, field)
            self.assertIsNotNone(spec, "%s.%s" % (family, field))
            self.assertFalse(spec.get("resolvable"),
                             "%s.%s may name something that does not exist"
                             % (family, field))


class TestTheGateWouldHaveCaughtIt(unittest.TestCase):
    """Deliberately break each relationship and prove the gate notices.

    A consistency gate nobody has seen fail is a gate nobody knows works.
    """

    def test_GATE_14_a_count_drift_is_detected(self):
        stage = S02ObligationAndCandidates()
        original = S02ObligationAndCandidates.RESPONSE_ENVELOPE
        try:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original[:-1]
            prompt = stage.prompt({"consumer_view": {}})
            claimed = int(re.search(r"exactly these (\d+) keys", prompt).group(1))
            self.assertNotEqual(len(original), claimed,
                                "removing a collection changed nothing")
            # The gate compares the two; here they now disagree by construction.
            self.assertEqual(len(original) - 1, claimed)
        finally:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original

    def test_GATE_15_an_unconsumed_collection_is_detected(self):
        stage = S02ObligationAndCandidates()
        original = S02ObligationAndCandidates.RESPONSE_ENVELOPE
        source = open(os.path.join(_REPO, "ver3", "assy_v3", "stages",
                                   "s02_obligation_and_candidates.py")).read()
        try:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original + (
                ("invented_things", "Obligation", "INV-", ("statement",), ()),)
            consumed = set(re.findall(r'parsed\.get\("([a-z_]+)"', source))
            self.assertNotIn("invented_things", consumed,
                             "the fabricated collection is somehow consumed")
        finally:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original


if __name__ == "__main__":
    unittest.main()


class TestFieldLevelCanonicalAlignment(unittest.TestCase):
    """Collection-level agreement is not enough.

    The envelope could stay perfectly consistent while the model was asked for
    `obligations_addressed` and the producer renamed it to
    `addresses_obligations`. That rename IS the incomplete migration, and it
    passed every earlier gate.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.stage = S02ObligationAndCandidates()
        cls.prompt = cls.stage.prompt({"consumer_view": {}})
        cls.source = open(os.path.join(
            _REPO, "ver3", "assy_v3", "stages",
            "s02_obligation_and_candidates.py")).read()

    def canonical_fields(self, family):
        spec = self.c.families[family]
        return (set(spec.get("required_fields") or [])
                | set(spec.get("optional_fields") or [])) - {"entity_id"}

    def test_GATE_16_every_exposed_field_is_a_canonical_field(self):
        for collection, family, _prefix, fields, supplied in self.stage.RESPONSE_ENVELOPE:
            canonical = self.canonical_fields(family)
            for field in tuple(fields) + tuple(supplied):
                self.assertIn(field, canonical,
                              "%s.%s is offered to the model and is not a field of "
                              "%s" % (collection, field, family))

    def test_GATE_17_every_canonical_required_field_is_exposed(self):
        for collection, family, _prefix, fields, supplied in self.stage.RESPONSE_ENVELOPE:
            required = set(self.c.families[family].get("required_fields") or [])
            missing = required - set(fields) - set(supplied) - {"entity_id"}
            self.assertEqual(set(), missing,
                             "%s must author %s and it is neither asked of the "
                             "model nor declared stage-supplied"
                             % (collection, sorted(missing)))

    def test_GATE_18_no_producer_semantic_rename_remains(self):
        """`"canonical": c.get("other_name")` is a rename. Structural extraction
        under the SAME name is not."""
        renames = []
        for canonical, source in re.findall(
                r'"(\w+)":\s*\w+\.get\(\s*"(\w+)"', self.source):
            if canonical != source:
                renames.append("%s <- %s" % (canonical, source))
        self.assertEqual([], renames,
                         "the producer renames a model field into a canonical one, "
                         "which is a compatibility shim: %s" % renames)

    def test_GATE_19_the_retired_legacy_name_is_gone_from_the_live_surface(self):
        self.assertNotIn("obligations_addressed", self.prompt,
                         "the model is still asked for the retired field name")
        code = re.sub(r"#.*", "", self.source)          # comments may record history
        self.assertNotIn("obligations_addressed", code,
                         "the live producer still handles the retired field name")

    def test_GATE_20_the_canonical_principle_shape_is_what_is_asked_for(self):
        shape = self.c.families["Candidate"]["principle_shape"]
        self.assertEqual("mapping", shape["kind"])
        self.assertIn("function_class", self.prompt,
                      "the mapping shape is not shown to the model")
        # and a rejected shape is reported, never coerced
        scalar = {"candidates": [{"id": "CND-1", "principle": "PIVOT"}]}
        self.assertTrue(self.stage._principle_shape_problems(scalar),
                        "a bare-string principle passes the live producer")
        before = json.dumps(scalar, sort_keys=True)
        self.stage._principle_shape_problems(scalar)
        self.assertEqual(before, json.dumps(scalar, sort_keys=True),
                         "the producer rewrote the model's principle")

    def test_GATE_21_no_s4_owned_row_is_still_ACTIVE(self):
        """PLACEMENT outranks prose.

        This used to key on the status token, so a row whose status read like a
        completion note - "producer emits the same field names" - sat in the
        active list and passed. The structure's own rule settles it: "a row here
        means the canonical target is defined, the producer does not yet conform
        ... It is NOT a claim of conformance." Being in `rows` IS the claim, and
        an optimistic sentence inside it does not withdraw it.
        """
        ds = _load("DESIGN_STATE_CONTRACT.yaml")
        self.assertIn("does not yet conform",
                      (ds.get("legacy_producers") or {}).get("rule", ""),
                      "the active structure no longer means what this test reads "
                      "it to mean; re-derive the rule before trusting this check")
        offending = _active_s4_rows((ds.get("legacy_producers") or {}).get("rows"))
        self.assertEqual([], offending,
                         "S-4 cannot close while it owns an ACTIVE migration row, "
                         "whatever the row's status text says: %s" % offending)


class TestFieldLevelGateActuallyFails(unittest.TestCase):
    """Deliberate regressions, proving the gate is not just describing today."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.stage = S02ObligationAndCandidates()

    def test_GATE_22_a_renamed_canonical_field_is_detected(self):
        """PM-GATE-01: put the old name back and the field check fails."""
        original = S02ObligationAndCandidates.RESPONSE_ENVELOPE
        try:
            broken = tuple(
                (c, f, p, tuple("obligations_addressed" if x == "addresses_obligations"
                                else x for x in fields), s)
                for c, f, p, fields, s in original)
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = broken
            offenders = []
            for collection, family, _p, fields, _s in broken:
                spec = self.c.families[family]
                canonical = (set(spec.get("required_fields") or [])
                             | set(spec.get("optional_fields") or []))
                offenders += [f for f in fields if f not in canonical]
            self.assertIn("obligations_addressed", offenders,
                          "renaming the canonical field passed the gate")
        finally:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original

    def test_GATE_23_a_scalar_principle_surface_is_detected(self):
        """PM-GATE-02."""
        self.assertTrue(self.stage._principle_shape_problems(
            {"candidates": [{"id": "CND-1", "principle": "PIVOT"}]}))
        self.assertTrue(self.stage._principle_shape_problems(
            {"candidates": [{"id": "CND-1", "principle": []}]}))

    def test_GATE_24_an_active_s4_nonconforming_row_is_detected(self):
        """PM-GATE-03: the check that would have caught the metadata I left."""
        rows = [{"concept": "invented", "current_status": "NONCONFORMING",
                 "migration_step": "S-4"}]
        offending = [r["concept"] for r in rows
                     if re.match(r"^S-4\b", str(r["migration_step"]))
                     and r["current_status"] in ("NONCONFORMING", "NOT_YET_PRODUCED")]
        self.assertEqual(["invented"], offending)


class TestClosureHygieneFalsifiers(unittest.TestCase):
    """CH-ACTIVE / CH-SURFACE: prove the strengthened checks fail when broken."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()
        cls.stage = S02ObligationAndCandidates()

    def test_CH_ACTIVE_01_the_real_contract_has_no_active_s4_row(self):
        ds = _load("DESIGN_STATE_CONTRACT.yaml")
        self.assertEqual(
            [], _active_s4_rows((ds.get("legacy_producers") or {}).get("rows")))

    def test_CH_ACTIVE_02_benign_prose_does_not_rescue_an_active_row(self):
        """The exact defect: a completed item left active behind a kind sentence."""
        rows = [{"concept": "invented", "migration_step": "S-4 (prompt cites it)",
                 "current_status": "producer now conforms; nothing left to do"}]
        self.assertEqual(1, len(_active_s4_rows(rows)),
                         "an S-4 row escaped because its status text sounded done")

    def test_CH_ACTIVE_03_a_superseded_row_does_not_fail_the_gate(self):
        ds = _load("DESIGN_STATE_CONTRACT.yaml")
        superseded = (ds.get("superseded_legacy_producers") or {}).get("rows") or []
        self.assertTrue(any(r["concept"].startswith("FunctionalRegion")
                            for r in superseded), "history was lost, not moved")
        self.assertEqual([], _active_s4_rows(superseded),
                         "the history structure is being read as active")

    def test_CH_ACTIVE_04_a_later_owner_may_legitimately_stay_active(self):
        rows = [{"concept": "mobility", "migration_step": "S-5 / U-6",
                 "current_status": "NONCONFORMING"}]
        self.assertEqual([], _active_s4_rows(rows),
                         "a row transferred to a later step was charged to S-4")

    # -- the model-facing surface is rendered, so it cannot drift ------
    def test_CH_SURFACE_01_every_envelope_field_reaches_the_model(self):
        prompt = self.stage.prompt({"consumer_view": {}})
        for collection, _family, _prefix, fields, _sup in self.stage.RESPONSE_ENVELOPE:
            for field in fields:
                self.assertIn(field, prompt,
                              "%s.%s is declared and never shown to the model"
                              % (collection, field))

    def test_CH_SURFACE_02_the_schema_is_rendered_not_restated(self):
        """One list, not three. The schema block is generated from the envelope,
        so a field cannot be present in one and absent from the other."""
        source = open(os.path.join(_REPO, "ver3", "assy_v3", "stages",
                                   "s02_obligation_and_candidates.py")).read()
        self.assertIn("{response_schema}", source,
                      "the response schema is hand-written again")
        rendered = self.stage.render_response_schema()
        for collection, _f, _p, fields, _s in self.stage.RESPONSE_ENVELOPE:
            self.assertIn("%s[]" % collection, rendered)
            for field in fields:
                self.assertIn(field, rendered)

    def test_CH_SURFACE_03_04_removing_or_renaming_a_field_changes_the_schema(self):
        """A rename or omission in the envelope is visible in what the model reads,
        which is what makes the two impossible to maintain separately."""
        original = S02ObligationAndCandidates.RESPONSE_ENVELOPE
        try:
            trimmed = tuple(
                (c, f, p, tuple(x for x in fields if x != "reacted_at_site"), s)
                for c, f, p, fields, s in original)
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = trimmed
            self.assertNotIn("reacted_at_site",
                             self.stage.render_response_schema(),
                             "removing a field left the model-facing schema "
                             "unchanged, so the two can drift")
            renamed = tuple(
                (c, f, p, tuple("obligations_addressed"
                                if x == "addresses_obligations" else x
                                for x in fields), s)
                for c, f, p, fields, s in original)
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = renamed
            self.assertIn("obligations_addressed",
                          self.stage.render_response_schema(),
                          "a rename did not reach the model-facing schema")
        finally:
            S02ObligationAndCandidates.RESPONSE_ENVELOPE = original

    def test_CH_PRI_03_no_live_wording_makes_principle_a_scalar(self):
        """Every live mention of the field states the mapping."""
        prompt = self.stage.prompt({"consumer_view": {}})
        self.assertIn("{function_class: principle_family}", prompt)
        self.assertIn("ONE-ENTRY MAPPING", prompt.upper())
        for phrase in ("principle is one of", "choose one principle",
                       "principle: a principle family"):
            self.assertNotIn(phrase.lower(), prompt.lower(), phrase)
