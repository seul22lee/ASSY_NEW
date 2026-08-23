"""A NUMBER CAN ONLY DECIDE WHAT ITS AUTHORITY ALLOWS.

A 4.0 pin in a 4.0 bore, authored by s04a, eliminated a candidate before
selection. The arithmetic was right and the authority was not: S04_CONTRACT
calls every s04a dimension provisional and prohibits "any authoritative
dimension"; S05_CONTRACT leaves "every dimension, until s06 solves it";
Parameter values are set by a cited solver artifact and nothing else; and
`Interface.mating_geometry` is writable by s04 and by no one, so no later
stage could ever have promoted those numbers. A representative size was
read as a solved one because nothing on the record said which it was.

TWO QUESTIONS AT TWO MATURITIES, now:

  `mating_relation`  is the declared mating PRINCIPLE realized? The pair,
                     the feature kinds, the axis, representative sizes
                     consistent with the arrangement they sit in. s04a's,
                     and what selection is decided on.
  `mating_fit`       do AUTHORITATIVE sizes satisfy the fit? Strictly -
                     a CLEARANCE pin smaller than its bore, a press fit no
                     smaller than its hole. Asked of sizes with an authority
                     (s05 declares, s06 settles) and DEFERRED until they
                     exist: an obligation with an owner, beside an
                     established relation, never a finding either way.

And one statement of arrival, derived and re-derived: `insertion_direction`
is the motion from `access_side`, written by s04a's own derivation pass, and
a side s03 revises leaves the old vector a contradiction the evaluator
refuses and the pass repairs.
"""
from __future__ import annotations

import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.stages.s04_envelope_and_motion import S04AEnvelopeAndReach  # noqa: E402
from ver3.assy_v3.state.design_state import Contracts, ContractError    # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s04_mating_geometry import (                                 # noqa: E402
    PIN_IN_LID, arriving, geometry, pin_arrangement, pin_topology)
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, topology)


class _Authority(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def pin(self, geom=None, kind="CLEARANCE", direction=(0, 1, 0)):
        """The lid first, then the pin arriving into it along `direction`:
        both domains that read the mating have something to read."""
        r = arriving(realization("A", steps=(0, 1)), direction, index=1)
        r["assembly_steps"][1]["order_index"] = 2
        arr = arrangement(PIN_IN_LID, steps=["ASY-0A", "ASY-1A"])
        arr["mating_geometry"] = [geom] if geom else []
        return self.hinge(s03a=pin_topology(kind, "+Y"), s03b=r, s04a=arr,
                          s04b=motion("A", "JNT-0A", _group(1, "A")))

    def fda(self, out, domain):
        return next(o.entity_id for o in out.patch.operations
                    if o.entity_type == "FeasibilityDomainAssessment"
                    and o.fields.get("domain") == domain)

    def val(self, state, eid):
        return state.entities[eid].get("_validity")

    def iface(self, state, iid="IFC-0A"):
        return next(i for i in state.family("Interface") if i["entity_id"] == iid)

    def boxes(self, state):
        return {e["body"]: s04.aabb(e["extent"]["centre"], e["extent"]["half_extent"])
                for e in state.family("Envelope")}


# =====================================================================
# A / B - authority decides what a number may do
# =====================================================================
class TestProvisionalSizesDecideNoFit(_Authority):

    def test_A_a_provisional_size_cannot_contradict_the_fit(self):
        """The CND-0001 shape, generically: CLEARANCE declared, the pin
        written exactly the size of its bore, by the pass whose contract
        calls that number provisional. The relation stands, the fit is owed,
        the candidate is not eliminated."""
        out = self.assess(self.pin(geometry(inner_diameter=1.0, outer_diameter=1.0)),
                          apply_patch=False)
        for domain in ("gross_interference", "assemblability"):
            v = self.domain(out, domain)
            self.assertNotEqual(s07.FAIL, v.status, (domain, v.summary))
            self.assertNotIn("REQUIRED_CLEARANCE_NOT_REALIZED", v.reason_codes, domain)
            self.assertIn("SIZING_DEFERRED_TO_EMBODIMENT", v.reason_codes, domain)
            self.assertIn("MATING_RELATION_ESTABLISHED", v.reason_codes, domain)
        self.assertEqual(s07.FEASIBLE, out.status, out.status)

    def test_A2_the_record_says_what_its_sizes_are(self):
        """Typed on the record, by the producer, validated by the boundary:
        the only maturity the field's only writer may state."""
        state = self.pin(geometry())
        self.assertEqual("PROVISIONAL", self.iface(state)["mating_geometry"]["maturity"])
        with self.assertRaises(ContractError) as raised:
            self.revise(state, Op("SUPERSEDE", "Interface", "IFC-0A",
                                  {"mating_geometry": dict(
                                      self.iface(state)["mating_geometry"],
                                      maturity="AUTHORITATIVE")},
                                  "t", reason="a promotion nobody may write"),
                        stage="s04")
        self.assertIn("RECORD_VALUE", str(raised.exception))

    def test_A3_a_record_written_before_the_field_reads_as_provisional(self):
        """The legacy shape: no `maturity` key. Deterministic - the field's
        only writer could state nothing else - and the same verdict."""
        state = self.pin(geometry())
        geom = {k: v for k, v in self.iface(state)["mating_geometry"].items()
                if k != "maturity"}
        joints = {j["entity_id"]: j for j in state.family("Joint")}
        fit, code, _n, _r = s04.mating_fit(self.iface(state), geom, joints,
                                           self.boxes(state))
        self.assertEqual((s04.FIT_DEFERRED, "SIZING_DEFERRED_TO_EMBODIMENT"), (fit, code))
        fit, code, _n, _r = s04.mating_relation(self.iface(state), geom, joints,
                                                self.boxes(state))
        self.assertEqual((s04.FIT_ESTABLISHED, "MATING_RELATION_ESTABLISHED"), (fit, code))

    def test_B_an_authoritative_incompatible_fit_does_contradict(self):
        """The numerical truth, where it belongs. Sizes with an authority,
        equal or inverted, are the positive contradiction; a solved margin
        is the fit established."""
        state = self.pin(geometry())
        iface, geom = self.iface(state), self.iface(state)["mating_geometry"]
        joints = {j["entity_id"]: j for j in state.family("Joint")}
        boxes = self.boxes(state)
        for d_in, d_out in ((1.0, 1.0), (1.01, 1.0)):
            fit, code, _n, _r = s04.mating_fit(iface, geom, joints, boxes,
                                               sizes={"inner_diameter": d_in,
                                                      "outer_diameter": d_out})
            self.assertEqual((s04.FIT_CONTRADICTED, "REQUIRED_CLEARANCE_NOT_REALIZED"),
                             (fit, code), (d_in, d_out))
        fit, code, _n, _r = s04.mating_fit(iface, geom, joints, boxes,
                                           sizes={"inner_diameter": 0.99,
                                                  "outer_diameter": 1.0})
        self.assertEqual((s04.FIT_ESTABLISHED, "ANALYTICAL_FIT_ESTABLISHED"), (fit, code))

    def test_B2_a_settlement_in_state_is_the_fit_answered(self):
        """End to end through the typed seam: s05's Constraint governs the
        interface, s06's settlement is written against it, and the evaluator
        reads the fit as established - or, for a settlement that says the
        fit is not realized, as the one FAIL this domain produces."""
        state = self.pin(geometry())
        self.revise(state, Op("CREATE", "Parameter", "PRM-DIN",
                              {"symbol": "d_in", "unit": "mm", "status": "DECLARED"},
                              "s05:embodiment", premise_refs=["CND-A"]), stage="s05")
        self.revise(state, Op("CREATE", "Constraint", "CON-FIT",
                              {"expression": "d_in <= d_out", "parameters": ["PRM-DIN"],
                               "kind": "CLEARANCE", "governs_interface": "IFC-0A"},
                              "s05:embodiment",
                              premise_refs=["CND-A", "IFC-0A", "PRM-DIN"]),
                    stage="s05")
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertIn("SIZING_DEFERRED_TO_EMBODIMENT", v.reason_codes, "owed until settled")
        self.revise(state, Op("EXTEND", "Constraint", "CON-FIT",
                              {"settlement": {"solver_status": "feasible", "residual": 0.0,
                                              "margin": 0.02, "solved_by": "SLV-x"}},
                              "s06:settlement"), stage="s06")
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("ANALYTICAL_FIT_ESTABLISHED", v.reason_codes)
        self.assertNotIn("SIZING_DEFERRED_TO_EMBODIMENT", v.reason_codes)
        self.assertIn("CON-FIT", v.premises)
        self.revise(state, Op("SUPERSEDE", "Constraint", "CON-FIT",
                              {"settlement": {"solver_status": "infeasible", "residual": 0.01,
                                              "margin": -0.01, "solved_by": "SLV-y"}},
                              "s06:settlement", reason="re-solved"), stage="s06")
        out = self.assess(state, apply_patch=False)
        v = self.domain(out, "gross_interference")
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("REQUIRED_CLEARANCE_NOT_REALIZED", v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)


# =====================================================================
# C / D - deferral is earned by the relation, never by the label
# =====================================================================
class TestDeferralIsEarned(_Authority):

    def test_C_a_valid_relation_with_sizing_deferred_establishes_the_domain(self):
        """The obligation is contractually downstream (S05-C9 + s06), so the
        pre-selection domains PASS with the obligation recorded by name and
        the relation's premises carried."""
        out = self.assess(self.pin(geometry()), apply_patch=False)
        for domain in ("gross_interference", "assemblability"):
            v = self.domain(out, domain)
            self.assertEqual(s07.PASS, v.status, (domain, v.summary))
            self.assertIn("SIZING_DEFERRED_TO_EMBODIMENT", v.reason_codes)
            for p in ("IFC-0A", "JNT-0A", "BOD-G0A", "BOD-G1A"):
                self.assertIn(p, v.premises, (domain, p))

    def test_D_a_malformed_relation_gets_no_deferred_pass(self):
        """Every defect the relation rule names stays what it was: nothing
        is deferred for a pair it cannot read."""
        cases = [
            (geometry(inner_body="BOD-G1A", outer_body="BOD-G1A"), "MATING_GEOMETRY_NOT_ESTABLISHED"),
            (geometry(inner_feature="SHAFT", outer_feature="HOLE"), "UNSUPPORTED_MATING_GEOMETRY"),
            (geometry(axis_direction="+Y"), "MATING_AXIS_NOT_ESTABLISHED"),
            (geometry(inner_diameter=-1.0), "MATING_GEOMETRY_NOT_ESTABLISHED"),
            (geometry(inner_diameter=5.0), "MATING_SIZE_EXCEEDS_ARRANGEMENT"),
            (geometry(engagement_length=99), "MATING_SIZE_EXCEEDS_ARRANGEMENT"),
        ]
        for geom, code in cases:
            v = self.domain(self.assess(self.pin(geom), apply_patch=False),
                            "gross_interference")
            self.assertEqual(s07.NOT_ESTABLISHED, v.status, (code, v.summary))
            self.assertIn(code, v.reason_codes, v.summary)
            self.assertNotIn("SIZING_DEFERRED_TO_EMBODIMENT", v.reason_codes, code)
            self.assertNotIn("MATING_RELATION_ESTABLISHED", v.reason_codes, code)
        v = self.domain(self.assess(self.pin(geometry(engagement_length=0)),
                                    apply_patch=False), "gross_interference")
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("REQUIRED_ENGAGEMENT_NOT_REALIZED", v.reason_codes)

    def test_D2_driven_in_sideways_is_still_a_contradiction(self):
        """The approach is s04's own fact: a relation-level contradiction at
        s04's maturity, whatever the sizes will be."""
        state = self.pin(geometry(), direction=(1, 0, 0))
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("INSERTION_NOT_ALONG_MATING_AXIS", v.reason_codes)

    def test_D3_the_producer_declares_a_size_its_own_boxes_cannot_hold(self):
        stage = S04AEnvelopeAndReach()
        arr = pin_arrangement(geometry(inner_diameter=5.0))
        top = pin_topology()
        view = {"Body": [{"entity_id": b} for b in PIN_IN_LID],
                "Interface": [dict(i, entity_id=i["id"]) for i in top["interfaces"]],
                "Joint": [dict(j, entity_id=j["id"]) for j in top["joints"]],
                "FunctionalRegion": [], "AssemblyStep": []}
        problems = stage.completeness(arr, {"consumer_view": view})
        self.assertTrue(any("IFC-0A" in p and "does not fit across" in p for p in problems),
                        problems)


# =====================================================================
# E / F - one maturity rule for both domains, and the boxes
# =====================================================================
class TestOneRuleForBothDomains(_Authority):

    def test_E_assemblability_and_gross_interference_agree(self):
        """Same state, same relation, same deferral, same premises on the
        interface - in both domains, from the one function."""
        out = self.assess(self.pin(geometry()), apply_patch=False)
        g = self.domain(out, "gross_interference")
        a = self.domain(out, "assemblability")
        for code in ("MATING_RELATION_ESTABLISHED", "SIZING_DEFERRED_TO_EMBODIMENT"):
            self.assertIn(code, g.reason_codes)
            self.assertIn(code, a.reason_codes)
        self.assertEqual(g.status, a.status)
        self.assertIn("IFC-0A", g.premises)
        self.assertIn("IFC-0A", a.premises)

    def test_F_a_box_overlap_for_an_established_nesting_is_not_a_collision(self):
        """The pin IS in its bore; its box is inside the lid's; the lid's
        sweep enters the pin's box. None of that is a finding against an
        established relation - and all of it still is for a pair with none."""
        v = self.domain(self.assess(self.pin(geometry()), apply_patch=False),
                        "gross_interference")
        self.assertEqual(s07.PASS, v.status, v.summary)
        for code in ("CLEARANCE_PAIR_OVERLAPS", "SWEEP_MEETS_CLEARANCE_PAIR",
                     "UNDECLARED_PAIR_OVERLAPS"):
            self.assertNotIn(code, v.reason_codes, v.summary)
        v = self.domain(self.assess(self.pin(None), apply_patch=False),
                        "gross_interference")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("CLEARANCE_PAIR_OVERLAPS", v.reason_codes)


# =====================================================================
# G / H - one statement of arrival, derived and re-derived
# =====================================================================
class TestArrivalIsDerivedAndReDerived(_Authority):

    def test_G_the_vector_is_the_motion_from_the_side(self):
        r = realization("A", steps=(0, 1))
        r["assembly_steps"][1]["order_index"] = 2
        r["assembly_steps"][0]["access_side"] = "-Y"
        r["assembly_steps"][1]["access_side"] = "+X"
        state = self.hinge(s03a=topology("A", 2, [(0, 1)]), s03b=r,
                           s04a=arrangement(HINGE_BOXES, steps=["ASY-0A", "ASY-1A"]))
        steps = {s["entity_id"]: s for s in state.family("AssemblyStep")}
        self.assertEqual(s04.motion_from_side("-Y"), steps["ASY-0A"]["insertion_direction"])
        self.assertEqual(s04.motion_from_side("+X"), steps["ASY-1A"]["insertion_direction"])

    def test_H_superseding_the_side_stales_the_assessment_and_forces_re_derivation(self):
        """s03 revises the side. The assessment that rested on the step goes
        STALE by ordinary propagation; the evaluator refuses the old vector as
        a contradiction of the new side; the derivation pass supersedes the
        vector - authority s04, reason on the record, no model - and the
        fresh assessment rests on the one statement again."""
        state = self.pin(geometry())
        out = self.assess(state)
        fda = self.fda(out, "assemblability")
        self.assertEqual("STANDING", self.val(state, fda))
        old = next(s for s in state.family("AssemblyStep")
                   if s["entity_id"] == "ASY-0A")["insertion_direction"]
        self.revise(state, Op("SUPERSEDE", "AssemblyStep", "ASY-0A",
                              {"access_side": "+X"}, "s03b:relations",
                              reason="the part is now loaded from the side"),
                    stage="s03")
        self.assertEqual("STALE", self.val(state, fda),
                         "the assessment kept standing over a revised premise")
        step = next(s for s in state.family("AssemblyStep") if s["entity_id"] == "ASY-0A")
        d, code, _ = s04.approach_direction(step)
        self.assertEqual((None, "INSERTION_DIRECTION_CONTRADICTS_ACCESS_SIDE"), (d, code))
        patch = S04AEnvelopeAndReach().derive_arrival(state, "CND-A")
        self.assertEqual([], state.validate(patch), patch.operations)
        (op,) = patch.operations
        self.assertEqual(("SUPERSEDE", "ASY-0A"), (op.kind, op.entity_id))
        self.assertEqual(s04.motion_from_side("+X"), op.fields["insertion_direction"])
        self.assertTrue(op.reason and "+X" in op.reason, op.reason)
        self.assertIn("CND-A", op.premise_refs)
        state.apply(patch)
        step = next(s for s in state.family("AssemblyStep") if s["entity_id"] == "ASY-0A")
        self.assertEqual(s04.motion_from_side("+X"), step["insertion_direction"])
        self.assertEqual(old, [h["prior_value"] for h in step["_superseded"]
                               if h["field"] == "insertion_direction"][-1],
                         "the prior vector is retained in the record's history")
        self.assertEqual("s04", [h["stage"] for h in step["_superseded"]][-1])
        out = self.assess(state, apply_patch=False)
        v = self.domain(out, "assemblability")
        self.assertNotIn("INSERTION_DIRECTION_CONTRADICTS_ACCESS_SIDE", v.reason_codes)

    def test_H2_the_derivation_pass_writes_nothing_where_nothing_disagrees(self):
        state = self.pin(geometry())
        patch = S04AEnvelopeAndReach().derive_arrival(state, "CND-A")
        self.assertEqual([], patch.operations)
        self.assertEqual([], state.validate(patch))

    def test_H3_the_derivation_pass_cannot_be_run_under_another_authority(self):
        """A SUPERSEDE of `insertion_direction` is s04's - the stage granted
        the field - and the patch says so; the boundary refuses it from any
        other stage."""
        state = self.pin(geometry())
        self.revise(state, Op("SUPERSEDE", "AssemblyStep", "ASY-0A",
                              {"access_side": "+X"}, "s03b:relations", reason="t"),
                    stage="s03")
        patch = S04AEnvelopeAndReach().derive_arrival(state, "CND-A")
        self.assertEqual("s04", patch.stage_id)
        patch.stage_id = "s03"
        problems = state.validate(patch)
        self.assertTrue(any("SUPERSEDE_WRONG_STAGE" in p for p in problems), problems)


# =====================================================================
# K - the ordinary mechanism, by invariant and not by id
# =====================================================================
class TestOrdinaryMechanismStaysFeasible(_Authority):

    def test_K_an_ordinary_hinge_is_feasible_for_selection(self):
        """Two bars, one revolute joint, a CONTACT interface, two states,
        arrival from above: the mechanism the fixtures are built on. It
        passes every domain on facts pre-selection owns and nothing else."""
        out = self.assess(self.hinge(), apply_patch=False)
        self.assertEqual(s07.FEASIBLE, out.status,
                         [(v.domain, v.status, v.reason_codes) for v in out.verdicts
                          if v.status not in (s07.PASS, s07.NOT_APPLICABLE)])

    def test_K2_a_nested_pin_hinge_with_representative_sizes_is_feasible(self):
        """The same hinge with its pin stated analytically, sizes
        representative: feasible, with the fit recorded as owed."""
        out = self.assess(self.pin(geometry()), apply_patch=False)
        self.assertEqual(s07.FEASIBLE, out.status,
                         [(v.domain, v.status, v.reason_codes) for v in out.verdicts
                          if v.status not in (s07.PASS, s07.NOT_APPLICABLE)])


if __name__ == "__main__":
    unittest.main()


# =====================================================================
# the reconciliation tool's own pieces, without evidence or a provider
# =====================================================================
class TestReconciliationPieces(_Authority):

    def test_gap_detection_asks_exactly_what_the_gates_declare(self):
        from ver3.tools import reconcile_preselection as rp
        top = dict(topology("A", 2, [(0, 1)]),
                   functional_regions=[{"id": "FRG-A", "role": "KEEP_OUT",
                                        "owning_bodies": ["BOD-G0A"],
                                        "required_by_actors": []}])
        state = self.hinge(s03a=top, s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"],
                                                      region="FRG-A"))
        gaps = rp.topology_gaps(state, "CND-A")
        self.assertEqual(([], []), (gaps["regions"], gaps["interfaces"]))
        self.revise(state, Op("SUPERSEDE", "FunctionalRegion", "FRG-A",
                              {"owning_bodies": []}, "s03:topology", reason="t"),
                    stage="s03")
        gaps = rp.topology_gaps(state, "CND-A")
        self.assertEqual(["FRG-A"], [r["entity_id"] for r in gaps["regions"]])
        self.assertEqual([], rp.release_gaps(state, "CND-A"))

    def test_a_recorded_answer_replays_by_prompt_hash_and_nothing_else(self):
        import os
        import tempfile
        from ver3.tools import reconcile_preselection as rp

        class NoProvider:
            model, provider_id, records = "none", "none", []

            def generate(self, request, attempt_index=0):
                raise AssertionError("a recorded answer was re-asked")

        with tempfile.TemporaryDirectory() as tmp:
            rp._dump(os.path.join(tmp, "04_provider_record.json"),
                     {"prompt_sha256": rp._sha("the question")})
            rp._dump(os.path.join(tmp, "06_parsed_response.json"),
                     {"json_parse": "OK", "parsed": {"answer": 1}})
            self.assertEqual({"answer": 1},
                             rp._call(NoProvider(), "the question", "p", "s03", "r", tmp))
            with self.assertRaises(AssertionError):
                rp._call(NoProvider(), "a different question", "p", "s03", "r", tmp)
