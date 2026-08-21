"""Every reference s03b writes is named in its prompt, with the family it points at.

The live s03b sweep was accepted 0 of 6, and all 58 canonical problems were of
two kinds: REFERENCE_FAMILY (46) and REFERENCE_NOT_AN_ID (12). Six fields carried
them:

  depends_on               named Bodies, in all six responses
  activates                named Joints, in five
  kept_open_by             named Bodies, LoadCases and Obligations, in three
  blocks                   held prose, in three
  alternatives             held prose, in two
  maintaining_interaction  named an Interface, because the name reads like one

The prompt named each of those exactly once, in the schema line, and never said
what it points at. The s03a prompt carries a REFERENCES BETWEEN ITEMS section and
its sweep was accepted 6 of 6. So the defect was not the model and not those six
fields: it was that s03b's prompt had no reference specification at all.

WHAT IS DEFENDED HERE is therefore not "those six fields are documented". It is
that the specification is DERIVED FROM THE CONTRACT and complete by construction,
so a reference field added to a family s03b authors, or one that changes target,
cardinality or conditionality, cannot be silently missing from what the model is
told. The tests below read DESIGN_STATE_CONTRACT.yaml themselves rather than
calling the generator, so agreement between the two is checked rather than
assumed.

Nothing here repairs a response. The six captured responses are negative fixtures
and stay rejected.
"""
import json
import os
import unittest

import yaml

from . import _branches, _fixtures, _paths

from ver3.assy_v3.stages.base import carry_invocation_premises
from ver3.assy_v3.stages.s03_topology_and_mobility import (
    PIPELINE_SUPPLIED_REFERENCES, RESPONSE_KEY_OF, S03B_PROMPT,
    S03BMobilityAndAssembly, reference_rules, render_reference_rules)
from ver3.assy_v3.state.design_state import Contracts, DesignState
from ver3.assy_v3.state.patch import Op, StagePatch
from ver3.assy_v3.view import InvocationContext

FIXTURE = os.path.join(_paths.REPO_ROOT, "ver3", "tests", "fixtures",
                       "s03b_live", "bm001_s03b_responses.json")
CONTRACT = os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                        "DESIGN_STATE_CONTRACT.yaml")
RESPONSIBILITY = os.path.join(_paths.REPO_ROOT, "ver3", "contracts",
                              "STAGE_RESPONSIBILITY_CONTRACT.yaml")
#: The six that failed live. Named so a regression in any ONE of them is visible
#: as itself - not to bound the rule, which is contract-wide.
FAILED_LIVE = ("depends_on", "activates", "maintaining_interaction",
               "kept_open_by", "blocks", "alternatives")


def live_responses():
    with open(FIXTURE) as fh:
        return json.load(fh)


def contract_references():
    """Every reference-valued field of every family s03b authors, read HERE.

    A second reading of the same contract, deliberately: a test that asked the
    generator what the contract says would agree with it whatever either said.
    """
    with open(CONTRACT) as fh:
        ds = yaml.safe_load(fh)
    with open(RESPONSIBILITY) as fh:
        resp = yaml.safe_load(fh)
    families = dict(ds["entity_families"])
    families.update(ds.get("assurance_families") or {})
    declared = resp["stages"]["s03b"].get("permitted_output_semantics") or []
    out = {}
    for family in declared:
        spec = families.get(family) or {}
        for field, decl in (spec.get("field_semantics") or {}).items():
            if not isinstance(decl, dict):
                continue
            if decl.get("kind") == "reference":
                out[(family, field)] = dict(decl, _conditional=False)
                continue
            # NESTED ROWS COUNT. A `{joint, dof}` row carries an id the boundary
            # resolves and a value it checks against a closed set; a model told
            # only that the field is "a list of entries" has been told neither,
            # so the completeness guarantee has to reach one level down too.
            if decl.get("kind") != "record_list":
                continue
            for name, sub in (decl.get("record_field_semantics") or {}).items():
                if not isinstance(sub, dict):
                    continue
                if sub.get("kind") == "reference" or sub.get("values"):
                    out[(family, "%s[].%s" % (field, name))] = dict(
                        sub, _conditional=False)
        for rule in (spec.get("conditional_references") or []):
            out[(family, rule.get("field"))] = dict(rule, _conditional=True)
    return out, families, declared


def said_about(block, name):
    """The description the block gives one field.

    Parsed by the block's own shape - a field line indented two spaces, its
    description indented six - rather than by splitting on the next two-space
    run, which also matches the description's own indent and returned nothing.
    """
    lines, out, taking = block.splitlines(), [], False
    for line in lines:
        if line.strip() == name and line.startswith("  ") and not line.startswith("   "):
            taking = True
            continue
        if taking:
            if line.startswith("      "):
                out.append(line.strip())
            else:
                break
    return " ".join(out)


class _Rules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rules = reference_rules()
        cls.block = render_reference_rules()
        cls.contract, cls.families, cls.declared = contract_references()
        cls.by_key = {(r["family"], r["field"]): r for r in cls.rules}


# ======================================================================
# The enumeration is the contract's, and it is complete
# ======================================================================

class TestTheEnumerationComesFromTheContract(_Rules):

    def test_every_contract_reference_is_prompted_or_declared_pipeline_supplied(self):
        supplied = set(PIPELINE_SUPPLIED_REFERENCES)
        for (family, field) in sorted(self.contract):
            if RESPONSE_KEY_OF.get(family) is None or (family, field) in supplied:
                continue
            with self.subTest(family=family, field=field):
                self.assertIn((family, field), self.by_key,
                              "%s.%s is a reference this pass authors and the "
                              "prompt says nothing about it" % (family, field))

    def test_every_prompted_field_reaches_the_prompt_the_model_is_sent(self):
        """Through the real prompt path, not through the block in isolation: a
        specification the stage never renders is a specification nobody reads."""
        rendered = S03BMobilityAndAssembly().prompt(
            {"consumer_view": {}, "candidate": {"entity_id": "CND-X"}})
        for r in self.rules:
            name = "%s[].%s" % (RESPONSE_KEY_OF[r["family"]], r["field"])
            with self.subTest(field=name):
                self.assertIn(name, self.block)
                self.assertIn(name, rendered)
        self.assertIn("REFERENCES BETWEEN ITEMS", rendered)

    def test_the_prompt_template_carries_the_placeholder(self):
        """So the section cannot be dropped by editing prose around it."""
        self.assertIn("{references}", S03B_PROMPT)

    def test_the_prompt_names_the_family_the_contract_declares(self):
        for r in self.rules:
            name = "%s[].%s" % (RESPONSE_KEY_OF[r["family"]], r["field"])
            said = said_about(self.block, name)
            declared = self.contract[(r["family"], r["field"])]
            target = declared.get("target")
            with self.subTest(field=name):
                if declared.get("kind") == "enum" or r.get("kind") == "vocabulary":
                    for value in declared.get("values") or []:
                        self.assertIn(value, said,
                                      "%s accepts %s and the prompt does not say "
                                      "so" % (name, value))
                    continue
                if target == "ANY" or target is None:
                    self.assertIn("any entity id", said,
                                  "%s is ANY and the prompt narrows it" % name)
                else:
                    for family in ([target] if isinstance(target, str) else target):
                        self.assertIn(family, said,
                                      "%s points at %s and the prompt does not say so"
                                      % (name, family))

    def test_a_union_target_is_rendered_as_a_union(self):
        unions = [r for r in self.rules
                  if r["targets"] != "ANY" and len(r["targets"]) > 1]
        self.assertTrue(unions, "no union target left to exercise the rule")
        for r in unions:
            name = "%s[].%s" % (RESPONSE_KEY_OF[r["family"]], r["field"])
            said = said_about(self.block, name)
            with self.subTest(field=name):
                self.assertIn(" or ", said)
                for family in r["targets"]:
                    self.assertIn(family, said)

    def test_a_conditional_reference_is_rendered_as_conditional(self):
        conditional = [r for r in self.rules if r["when"]]
        self.assertTrue(conditional, "no conditional reference left to exercise")
        for r in conditional:
            name = "%s[].%s" % (RESPONSE_KEY_OF[r["family"]], r["field"])
            said = said_about(self.block, name)
            with self.subTest(field=name):
                self.assertIn("ONLY when", said)
                self.assertIn(r["when"]["field"], said)
                self.assertIn(r["when"]["equals"], said)

    def test_the_block_forbids_prose_once_and_says_where_ids_come_from(self):
        self.assertIn("ENTITY IDS", self.block)
        self.assertIn("A description is", self.block)
        self.assertIn("TYPED INPUT", self.block)
        self.assertIn("create in this", self.block)

    def test_it_carries_no_benchmark_id_and_no_worked_example(self):
        """A specification that names BOD-0001 teaches one benchmark."""
        for token in ("BOD-", "RGP-", "IFC-", "JNT-", "CFG-", "LC-", "PEO-",
                      "CND-", "BM-001"):
            self.assertNotIn(token, self.block, "the block names a concrete id")

    def test_the_six_fields_that_failed_live_are_all_specified(self):
        prompted = {r["field"] for r in self.rules}
        for field in FAILED_LIVE:
            with self.subTest(field=field):
                self.assertIn(field, prompted)

    def test_the_families_are_the_ones_the_responsibility_declares(self):
        self.assertEqual({f for f in self.declared if RESPONSE_KEY_OF.get(f)},
                         {r["family"] for r in self.rules})

    def test_every_declared_output_family_is_accounted_for(self):
        """Either it has a response key, or it is marked as one the pipeline
        derives. A family in neither state would vanish from the prompt with
        nothing said, which is the failure this section exists to end."""
        for family in self.declared:
            with self.subTest(family=family):
                self.assertIn(family, RESPONSE_KEY_OF)

    def test_an_unaccounted_output_family_raises_rather_than_disappearing(self):
        import ver3.assy_v3.stages.s03_topology_and_mobility as s03
        original = dict(s03.RESPONSE_KEY_OF)
        try:
            s03.RESPONSE_KEY_OF.pop("AssemblyStep")
            with self.assertRaises(KeyError):
                s03.reference_rules()
        finally:
            s03.RESPONSE_KEY_OF.clear()
            s03.RESPONSE_KEY_OF.update(original)

    def test_the_pipeline_derived_family_is_marked_and_not_prompted(self):
        self.assertIsNone(RESPONSE_KEY_OF.get("MobilityExpectation"))
        self.assertNotIn("MobilityExpectation",
                         {r["family"] for r in self.rules})

    def test_a_pipeline_supplied_reference_is_not_asked_for(self):
        for family, field in PIPELINE_SUPPLIED_REFERENCES:
            with self.subTest(field="%s.%s" % (family, field)):
                self.assertNotIn((family, field), self.by_key)
                self.assertNotIn("%s[].%s" % (RESPONSE_KEY_OF[family], field),
                                 self.block)


# ======================================================================
# Staleness cannot hide: the generator is exercised on altered declarations
# ======================================================================

class TestAStaleSpecificationIsDetected(_Rules):
    """Each case alters what the CONTRACT says and shows the block follows.

    The rules are rendered from a substituted row set rather than by editing the
    contract file, which is the same substitution the generator would see if the
    file had changed - and it keeps the test from writing to a contract.
    """

    def test_a_new_reference_field_appears_without_anyone_editing_prose(self):
        rows = list(self.rules) + [{"family": "AssemblyStep", "field": "fastened_by",
                                    "kind": "reference", "targets": ["Interface"],
                                    "cardinality": "many", "resolvable": False,
                                    "population": "INVOCATION_BRANCH", "when": None}]
        self.assertIn("assembly_steps[].fastened_by", render_reference_rules(rows))

    def test_a_field_that_becomes_a_union_is_rendered_as_one(self):
        rows = [dict(r, targets=["Body", "RigidGroup"])
                if r["field"] == "provider_body" else r for r in self.rules]
        block = render_reference_rules(rows)
        self.assertIn("Body or RigidGroup",
                      said_about(block, "constraint_relations[].provider_body"))

    def test_a_field_that_becomes_ANY_stops_naming_a_family(self):
        rows = [dict(r, targets="ANY") if r["field"] == "provider_body" else r
                for r in self.rules]
        said = said_about(render_reference_rules(rows),
                          "constraint_relations[].provider_body")
        self.assertIn("any entity id", said)
        self.assertNotIn("Body id", said)

    def test_a_field_that_becomes_conditional_says_when(self):
        rows = [dict(r, when={"field": "driver", "equals": "LOAD"})
                if r["field"] == "provider_body" else r for r in self.rules]
        said = said_about(render_reference_rules(rows),
                          "constraint_relations[].provider_body")
        self.assertIn("ONLY when driver is LOAD", said)

    def test_the_block_is_stable_when_the_contract_is(self):
        self.assertEqual(render_reference_rules(), render_reference_rules())


# ======================================================================
# The captured responses, as negative fixtures
# ======================================================================

class TestTheCapturedResponsesAreStillRejected(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.state = _branches.six_branch_state(run_id="s03b-refs")
        cls.stage = S03BMobilityAndAssembly()
        cls.views = {c["entity_id"]: cls.stage.consumer_view(
            cls.state, InvocationContext(branch=c["entity_id"]))
            for c in cls.state.family("Candidate")}

    def author(self, cid, response):
        cand = _branches.candidate(self.state, cid)
        inputs = {"candidate": cand,
                  self.stage.context_key: self.views[cid].payload()}
        ops = carry_invocation_premises(self.stage.to_operations(response, inputs),
                                        self.stage.invocation_premises(inputs))
        patch = StagePatch(patch_id="refs-%s" % cid, run_id=self.state.run_id,
                           stage_id="s03", stage_attempt=1,
                           parent_state_hash=self.state.state_hash(),
                           operations=ops, execution_status="SUCCESS",
                           provenance={"purpose": "reference seam test",
                                       "provider": "saved evidence"})
        return self.state.validate(patch), patch

    def test_the_fixture_holds_all_six_responses(self):
        r = live_responses()["responses"]
        self.assertEqual(6, len(r))
        self.assertTrue(all(v.get("assembly_steps") for v in r.values()))

    def test_every_captured_response_is_still_refused(self):
        for cid, response in sorted(live_responses()["responses"].items()):
            with self.subTest(candidate=cid):
                problems, _ = self.author(cid, response)
                self.assertTrue(problems, "%s became acceptable; the reference "
                                          "layer was weakened to admit it" % cid)

    def test_the_refusals_are_the_ones_the_live_run_recorded(self):
        """Same responses, same reference problems - so this is the seam the
        sweep hit, not a different one that happens to reject the same input."""
        recorded = live_responses()["recorded_problems"]
        for cid, response in sorted(live_responses()["responses"].items()):
            with self.subTest(candidate=cid):
                problems, _ = self.author(cid, response)
                reference_now = {p for p in problems
                                 if p.startswith(("REFERENCE_FAMILY",
                                                  "REFERENCE_NOT_AN_ID"))}
                reference_then = {p for p in recorded[cid]
                                  if p.startswith(("REFERENCE_FAMILY",
                                                   "REFERENCE_NOT_AN_ID"))}
                self.assertEqual(reference_then, reference_now)

    def test_each_field_that_failed_live_is_refused_somewhere_in_the_corpus(self):
        seen = set()
        for cid, response in sorted(live_responses()["responses"].items()):
            problems, _ = self.author(cid, response)
            for p in problems:
                for field in FAILED_LIVE:
                    if ".%s " % field in p:
                        seen.add(field)
        self.assertEqual(set(FAILED_LIVE), seen,
                         "a field the live sweep failed on is no longer exercised")


# ======================================================================
# A response written to the specification passes the reference layer
# ======================================================================

class TestASpecCompliantResponsePasses(TestTheCapturedResponsesAreStillRejected):
    """Synthetic, and composed FROM THE VIEW by the canonical semantics - not the
    captured response with its references corrected, which would be a repair."""

    def compliant(self, cid):
        p = self.views[cid].payload()
        groups = [g["entity_id"] for g in p.get("RigidGroup") or []]
        bodies = [b["entity_id"] for b in p.get("Body") or []]
        ifaces = [i["entity_id"] for i in p.get("Interface") or []]
        configs = [c["entity_id"] for c in p.get("Configuration") or []]
        peos = p.get("PhysicalEffectObligation") or []
        loads = p.get("LoadCase") or []
        free = [f["entity_id"] for f in (p.get("Freedom") or [])][:1]
        return {
            "irrelevance": [],
            "physical_interactions": [
                {"id": "PHI-9%03d" % (n + 1), "groups": groups[:2],
                 "effect": q.get("effect"), "discharges_effect": q["entity_id"],
                 "at_interface": ifaces[0], "configurations": configs[:1]}
                for n, q in enumerate(peos)],
            "constraint_relations": [
                {"id": "CRL-9001", "retained_group": groups[-1],
                 "blocked_dofs": ["TX", "TY", "TZ"], "configurations": configs,
                 "driver": "KINEMATIC_NECESSITY", "blocked_direction": "+Z",
                 "provider_body": bodies[0], "provider_site": ifaces[0],
                 "maintaining_interaction": "PHI-9001",
                 "defeat_specification": "a pull that separates the two bodies"}],
            "load_paths": [
                {"id": "LDP-9%03d" % (n + 1), "load_case": l["entity_id"],
                 "ordered_hops": ifaces[:2], "terminates_at": l.get("reacted_at_site")}
                for n, l in enumerate(loads)],
            "assembly_steps": [
                {"id": "ASY-9%03d" % (n + 1), "order_index": n + 1, "body": b,
                 "access_side": "+Z", "activates": ifaces[:1],
                 "termination_strategy": "LATER_BODY_COVER", "path_kind": "RIGID",
                 "depends_on": (["ASY-9%03d" % n] if n else [])}
                for n, b in enumerate(bodies)],
            "unresolved": [
                {"id": "S3U-9001", "decision": "the retaining feature",
                 "why_open": "no material has been chosen",
                 "alternatives": [bodies[0], ifaces[0]],
                 "alternatives_kind": "ENTITY_REFS", "kept_open_by": free,
                 "blocks": [peos[0]["entity_id"]] if peos else []}],
        }

    def test_a_specification_compliant_response_raises_no_reference_problem(self):
        for cid in sorted(self.views):
            with self.subTest(candidate=cid):
                problems, _ = self.author(cid, self.compliant(cid))
                references = [p for p in problems
                              if p.startswith(("REFERENCE_FAMILY", "REFERENCE_NOT_AN_ID",
                                               "REFERENCE_UNRESOLVED", "FOREIGN_BRANCH"))]
                self.assertEqual([], references)

    def test_the_conditional_field_is_typed_only_under_ENTITY_REFS(self):
        """FREE_TEXT alternatives are not ids and are not checked as ids - which
        is what makes the conditional line in the prompt true rather than a rule
        that happens to hold."""
        cid = sorted(self.views)[0]
        prose = self.compliant(cid)
        prose["unresolved"][0]["alternatives_kind"] = "FREE_TEXT"
        prose["unresolved"][0]["alternatives"] = ["a moulded catch", "a metal clip"]
        problems, _ = self.author(cid, prose)
        self.assertEqual([], [p for p in problems if ".alternatives " in p])

    def test_entity_refs_alternatives_holding_prose_is_still_refused(self):
        cid = sorted(self.views)[0]
        bad = self.compliant(cid)
        bad["unresolved"][0]["alternatives"] = ["a moulded catch"]
        problems, _ = self.author(cid, bad)
        self.assertTrue([p for p in problems if ".alternatives " in p], problems)

    def test_a_wrong_family_is_still_refused_field_by_field(self):
        """The specification tells the model the family; the boundary enforces it.
        One test per field the live sweep failed on, each pointed at a family the
        contract does not allow there."""
        cid = sorted(self.views)[0]
        p = self.views[cid].payload()
        body = (p.get("Body") or [{}])[0].get("entity_id")
        joint = (p.get("Joint") or [{}])[0].get("entity_id")
        iface = (p.get("Interface") or [{}])[0].get("entity_id")
        for field, wrong, where in (("depends_on", [body], "assembly_steps"),
                                    ("activates", [joint], "assembly_steps"),
                                    ("maintaining_interaction", iface,
                                     "constraint_relations"),
                                    ("kept_open_by", [body], "unresolved")):
            with self.subTest(field=field):
                response = self.compliant(cid)
                response[where][0][field] = wrong
                problems, _ = self.author(cid, response)
                self.assertTrue([x for x in problems if ".%s " % field in x],
                                "%s accepted a %s" % (field, wrong))


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
