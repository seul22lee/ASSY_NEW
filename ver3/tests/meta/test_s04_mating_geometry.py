"""A BOX OVERLAP IS NOT A COLLISION, AND NOW THE DESIGN CAN SAY WHAT IT IS.

The Envelope is broad-phase: no-overlap proves clearance, overlap proves nothing.
For every nested machine element - a pin in a bore, a shaft in a bearing - the
boxes DO overlap, so without a second tier the ordinary hinge was permanently
unestablished. `Interface.mating_geometry` is that tier: typed, numeric, extended
onto the intended interface by s04a, and read by ONE rule, `s04.mating_fit`,
which feasibility asks from both domains that care.

What the tier does not do: replace the Envelope, decide anything for a pair the
design did not declare, or turn a geometry it cannot read into a failure.
"""
from __future__ import annotations

import copy
import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.state.design_state import Contracts, ContractError    # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    _Feas, _group, arrangement, motion, realization, side_of, topology)

#: A lid (G0) with a pin (G1) inside its knuckle, turning about +Y. The boxes
#: overlap because the pin IS inside the lid.
PIN_IN_LID = {"BOD-G0A": ([0, 0, 0], [10, 6, 1]),
              "BOD-G1A": ([-9, 0, 0], [0.5, 6, 0.5])}


def pin_topology(kind="CLEARANCE", axis="+Y"):
    top = topology("A", 2, [(0, 1)], axis=axis)
    top["interfaces"][0]["interaction_kind"] = kind
    return top


def geometry(**over):
    g = {"interface": "IFC-0A", "inner_body": "BOD-G1A", "outer_body": "BOD-G0A",
         "inner_feature": "PIN", "outer_feature": "BORE",
         "inner_diameter": 1.0, "outer_diameter": 1.05,
         "engagement_length": 10, "axis_joint": "JNT-0A"}
    g.update(over)
    return g


def pin_arrangement(geom=None, boxes=None):
    arr = arrangement(boxes or PIN_IN_LID, steps=["ASY-0A"])
    arr["mating_geometry"] = [geom] if geom else []
    return arr


def arriving(r, along, index=0):
    """Step `index` of realization `r` arrives so its body travels `along`."""
    r["assembly_steps"][index]["access_side"] = side_of(along)
    return r


class _Mating(_Feas):

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def pin(self, geom=None, kind="CLEARANCE", axis="+Y", boxes=None,
            direction=(0, 1, 0), s03b=None):
        return self.hinge(s03a=pin_topology(kind, axis),
                          s03b=(s03b if s03b is not None
                                else arriving(realization("A"), direction)),
                          s04a=pin_arrangement(geom, boxes),
                          s04b=motion("A", "JNT-0A", _group(1, "A")))

    def inserted(self, geom=None, direction=(0, 1, 0)):
        """The lid first, then the PIN arriving into it along `direction`."""
        r = arriving(realization("A", steps=(0, 1)), direction, index=1)
        r["assembly_steps"][1]["order_index"] = 2
        arr = arrangement(PIN_IN_LID, steps=["ASY-0A", "ASY-1A"])
        arr["mating_geometry"] = [geom] if geom else []
        return self.hinge(s03a=pin_topology(), s03b=r, s04a=arr,
                          s04b=motion("A", "JNT-0A", _group(1, "A")))

    def gross(self, state):
        return self.domain(self.assess(state, apply_patch=False), "gross_interference")

    def asm(self, state):
        return self.domain(self.assess(state, apply_patch=False), "assemblability")


# =====================================================================
# Gate C - the fit rule
# =====================================================================
class TestAnalyticalFit(_Mating):

    def test_F1_a_pin_smaller_than_its_bore_clears(self):
        """Overlapping boxes, CLEARANCE declared, and the geometry says the pin
        is 1.0 in a 1.05 bore. Broad phase inconclusive, narrow phase decides."""
        v = self.gross(self.pin(geometry()))
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("ANALYTICAL_FIT_ESTABLISHED", v.reason_codes)
        self.assertNotIn("CLEARANCE_PAIR_OVERLAPS", v.reason_codes)
        for p in ("IFC-0A", "JNT-0A", "BOD-G0A", "BOD-G1A", "ENV-G0A", "ENV-G1A",
                  "SCL-CND-A"):
            self.assertIn(p, v.premises, p)

    def test_F2_a_pin_too_large_for_its_bore_fails(self):
        """THE ONE POSITIVE CONTRADICTION THIS TIER CAN MAKE. The design said
        clearance and wrote a pin no smaller than its bore."""
        for d in (1.05, 1.2):
            out = self.assess(self.pin(geometry(inner_diameter=d)), apply_patch=False)
            v = self.domain(out, "gross_interference")
            self.assertEqual(s07.FAIL, v.status, v.summary)
            self.assertIn("REQUIRED_CLEARANCE_NOT_REALIZED", v.reason_codes)
            self.assertEqual(s07.INFEASIBLE, out.status)

    def test_F2b_a_press_fit_smaller_than_its_hole_fails_end_to_end(self):
        """INTERFERENCE_FIT declared, and the authored pin is SMALLER than the
        hole: a press fit that cannot press. Asked of the candidate, through
        the real evaluator - not of `mating_fit` directly - because the TOUCHES
        box exemption used to stop the geometry ever being read, and the bad
        fit came out FEASIBLE_FOR_SELECTION."""
        out = self.assess(self.pin(geometry(inner_diameter=0.9),
                                   kind="INTERFERENCE_FIT"), apply_patch=False)
        v = self.domain(out, "gross_interference")
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("REQUIRED_CONTACT_NOT_REALIZED", v.reason_codes)
        self.assertEqual(s07.INFEASIBLE, out.status)
        self.assertIn("IFC-0A", v.premises)

    def test_F2c_a_real_press_fit_passes_and_the_box_overlap_is_still_exempt(self):
        """The exemption is from the BOX test, not from the numbers. A pin no
        smaller than its hole under INTERFERENCE_FIT is what was declared."""
        for d in (1.05, 1.2):
            v = self.gross(self.pin(geometry(inner_diameter=d), kind="INTERFERENCE_FIT"))
            self.assertEqual(s07.PASS, v.status, v.summary)
            self.assertIn("ANALYTICAL_FIT_ESTABLISHED", v.reason_codes)
            self.assertNotIn("UNDECLARED_PAIR_OVERLAPS", v.reason_codes)

    def test_F2d_a_touches_pair_with_no_geometry_stays_exempt(self):
        """No new universal metric requirement on every legacy CONTACT pair."""
        v = self.gross(self.pin(None, kind="INTERFERENCE_FIT"))
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertNotIn("REQUIRED_CONTACT_NOT_REALIZED", v.reason_codes)

    def test_F3_overlapping_boxes_with_no_geometry_stay_unestablished(self):
        """What it always was. Never FAIL from a box overlap alone."""
        out = self.assess(self.pin(None), apply_patch=False)
        v = self.domain(out, "gross_interference")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("CLEARANCE_PAIR_OVERLAPS", v.reason_codes)
        self.assertNotEqual(s07.INFEASIBLE, out.status)

    def test_F6_an_unreadable_axis_is_not_established(self):
        """The joint's axis names no coordinate. The geometry cannot say which
        way the pin runs, so nothing is measured - and nothing fails."""
        top = pin_topology(axis="DIAGONAL")
        state = self.hinge(s03a=top, s04a=pin_arrangement(geometry()),
                           s04b=motion("A", "JNT-0A", _group(1, "A")))
        v = self.gross(state)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("MATING_AXIS_NOT_ESTABLISHED", v.reason_codes)

    def test_F6b_an_axis_stated_twice_is_two_authors_of_one_fact(self):
        v = self.gross(self.pin(geometry(axis_direction="+Y")))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("MATING_AXIS_NOT_ESTABLISHED", v.reason_codes)
        self.assertIn("AXIS_STATED_TWICE", v.summary)

    def test_F6c_a_fixed_dowel_states_its_own_axis(self):
        """No joint relates a dowel to its hole. The record says the axis, in
        the joint's own vocabulary, and that is the one source."""
        top = pin_topology()
        top["joints"][0]["joint_type"] = "FIXED"
        top["joints"][0]["dof"] = []
        top["joints"][0]["axis_direction"] = "NONE"
        g = geometry(inner_feature="DOWEL", outer_feature="HOLE",
                     axis_direction="+Y")
        del g["axis_joint"]
        state = self.hinge(s03a=top, s03b=realization("A", demand=None),
                           s04a=pin_arrangement(g),
                           s04b=motion("A", "JNT-0A", _group(1, "A"), transition=False,
                                       coords=(0, 0)))
        v = self.gross(state)
        self.assertIn("ANALYTICAL_FIT_ESTABLISHED", v.reason_codes, v.summary)

    def test_F10_an_unsupported_feature_pair_is_never_guessed(self):
        """A thread in a bore is not a pin in a bore. The reader does not know
        what a thread clears by, and says so rather than measuring it as one."""
        state = self.pin(geometry(inner_feature="SHAFT", outer_feature="HOLE"))
        v = self.gross(state)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("UNSUPPORTED_MATING_GEOMETRY", v.reason_codes)

    def test_F10b_an_unlisted_kind_is_refused_at_the_boundary(self):
        with self.assertRaises(ContractError) as raised:
            self.pin(geometry(inner_feature="THREAD"))
        self.assertIn("RECORD_VALUE", str(raised.exception))

    def test_F11_a_pair_whose_boxes_do_not_overlap_needs_no_geometry(self):
        """The broad phase still proves clearance on its own."""
        apart = {"BOD-G0A": ([0, 0, 0], [1, 1, 1]), "BOD-G1A": ([9, 0, 0], [1, 1, 1])}
        state = self.hinge(s03a=pin_topology(),
                           s04a=pin_arrangement(None, apart),
                           # a small turn, so the sweep does not reach the lid
                           s04b=motion("A", "JNT-0A", _group(1, "A"), coords=(0, 5)))
        v = self.gross(state)
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertNotIn("ANALYTICAL_FIT_ESTABLISHED", v.reason_codes)

    def test_F12_engagement_longer_than_the_pin_is_a_contradiction(self):
        v = self.gross(self.pin(geometry(engagement_length=30)))
        self.assertEqual(s07.FAIL, v.status)
        self.assertIn("REQUIRED_ENGAGEMENT_NOT_REALIZED", v.reason_codes)

    def test_F13_a_geometry_about_another_pair_refines_nothing(self):
        """The interface is G0-G1; the geometry names G1 twice."""
        v = self.gross(self.pin(geometry(outer_body="BOD-G1A")))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("MATING_GEOMETRY_NOT_ESTABLISHED", v.reason_codes)


# =====================================================================
# Gate D - insertion
# =====================================================================
class TestInsertion(_Mating):

    def test_F4_a_pin_arriving_along_its_bore_is_not_obstructed_by_it(self):
        """The pin's corridor enters the lid's box along the whole way - it is
        going INTO the lid. The geometry fits and the step drives it along
        the mating axis, so that pair passes the narrow-phase predicate."""
        v = self.asm(self.inserted(geometry(), direction=(0, 1, 0)))
        self.assertEqual(s07.PASS, v.status, v.summary)
        self.assertIn("ANALYTICAL_INSERTION_ESTABLISHED", v.reason_codes)
        self.assertNotIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes)

    def test_F4b_driven_in_sideways_is_a_contradiction(self):
        v = self.asm(self.inserted(geometry(), direction=(1, 0, 0)))
        self.assertEqual(s07.FAIL, v.status, v.summary)
        self.assertIn("INSERTION_NOT_ALONG_MATING_AXIS", v.reason_codes)

    def test_F4c_a_clearance_pair_with_no_geometry_is_not_exempt(self):
        """Declared CLEARANCE is not declared to meet. Without the geometry the
        corridor into the bore is what it always was."""
        v = self.asm(self.inserted(None, direction=(0, 1, 0)))
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes)

    def test_F4d_a_missing_insertion_direction_is_an_absence(self):
        """Valid geometry, a corridor that needs the narrow phase, and no
        direction stated for the step. Nothing can be measured along an axis
        nobody named - and nothing is contradicted.

        s04a derives the direction for every step it is shown, so "no
        direction" is a step s04a has not spoken for: here one s03 adds after
        the arrangement was written."""
        arr = arrangement(PIN_IN_LID, steps=["ASY-0A"])
        arr["mating_geometry"] = [geometry()]
        state = self.hinge(s03a=pin_topology(), s03b=realization("A"), s04a=arr,
                           s04b=motion("A", "JNT-0A", _group(1, "A")))
        late = dict(realization("A", steps=(0, 1))["assembly_steps"][1],
                    order_index=2, access_side="-Y")
        self.revise(state, Op("CREATE", "AssemblyStep", late.pop("id"), late,
                              "s03b:relations", premise_refs=["CND-A"]), stage="s03")
        v = self.asm(state)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("INSERTION_DIRECTION_MISSING", v.reason_codes)
        self.assertNotIn("INSERTION_NOT_ALONG_MATING_AXIS", v.reason_codes)

    def test_F14_two_geometries_for_one_pair_mean_the_same_in_both_domains(self):
        """The design answered one question twice. That is an ambiguity, not
        a collision, and it has ONE name wherever it is read: assemblability
        used to fall through to the generic corridor finding."""
        state = self.inserted(geometry(), direction=(0, 1, 0))
        self.revise(state, Op("CREATE", "Interface", "IFC-DUP",
                              {"bodies": ["BOD-G0A", "BOD-G1A"],
                               "interaction_kind": "CLEARANCE", "nominal": "SECOND",
                               "addresses_obligations": []}, "t",
                              premise_refs=["CND-A"]), stage="s03")
        g = dict(geometry()); g.pop("interface")
        self.revise(state, Op("EXTEND", "Interface", "IFC-DUP",
                              {"mating_geometry": g}, "t",
                              premise_refs=["CND-A"]), stage="s04")
        out = self.assess(state, apply_patch=False)
        for d in ("gross_interference", "assemblability"):
            v = self.domain(out, d)
            self.assertEqual(s07.NOT_ESTABLISHED, v.status, (d, v.summary))
            self.assertIn("MATING_GEOMETRY_STATED_TWICE", v.reason_codes, d)
            self.assertNotIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes, d)
        self.assertNotEqual(s07.INFEASIBLE, out.status)

    def test_F5_an_unrelated_body_in_the_corridor_still_obstructs(self):
        """Three bodies: the pin mates with G0 and its corridor also crosses
        G2, which nothing declares. G2 is still an obstacle."""
        top = topology("A", 3, [(0, 1)], axis="+Y")
        top["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        boxes = dict(PIN_IN_LID, **{"BOD-G2A": ([-9, 20, 0], [1, 1, 1])})
        r = realization("A", steps=(2, 0, 1))
        for n, s in enumerate(r["assembly_steps"]):
            s["order_index"] = n + 1
            s["access_side"] = side_of([0, -1, 0])
        arr = arrangement(boxes, steps=["ASY-2A", "ASY-0A", "ASY-1A"])
        arr["mating_geometry"] = [geometry()]
        state = self.hinge(s03a=top, s03b=r, s04a=arr,
                           s04b=motion("A", "JNT-0A", _group(1, "A")))
        v = self.asm(state)
        self.assertIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes, v.summary)
        self.assertIn("BOD-G1A entering meets BOD-G2A", v.summary)
        self.assertIn("ANALYTICAL_INSERTION_ESTABLISHED", v.reason_codes,
                      "the mating pair was still established")


# =====================================================================
# Gate E - isolation and currentness
# =====================================================================
class TestLifecycle(_Mating):

    def test_F7_another_candidates_geometry_cannot_satisfy_this_pair(self):
        """Two branches, the same shape. B carries the geometry; A does not.
        A's pair is as unestablished as if B did not exist."""
        state = self.seed()
        self.candidates(state)
        self.hinge(state=state, s03a=pin_topology(),            # A: no geometry
                   s04a=pin_arrangement(None),
                   s04b=motion("A", "JNT-0A", _group(1, "A")))
        top_b = topology("B", 2, [(0, 1)], axis="+Y")
        top_b["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        g = geometry(interface="IFC-0B", inner_body="BOD-G1B", outer_body="BOD-G0B",
                     axis_joint="JNT-0B")
        boxes_b = {k.replace("A", "B"): v for k, v in PIN_IN_LID.items()}
        arr_b = arrangement(boxes_b, steps=["ASY-0B"])
        arr_b["mating_geometry"] = [g]
        self.branch(state, "B", top_b, realization("B"), arr_b,
                    motion("B", "JNT-0B", _group(1, "B")))
        a = self.domain(self.assess(state, "CND-A", apply_patch=False),
                        "gross_interference")
        b = self.domain(self.assess(state, "CND-B", apply_patch=False),
                        "gross_interference")
        self.assertEqual(s07.NOT_ESTABLISHED, a.status)
        self.assertIn("CLEARANCE_PAIR_OVERLAPS", a.reason_codes)
        self.assertEqual(s07.PASS, b.status, b.summary)
        self.assertNotIn("IFC-0B", a.premises)

    def test_F8_superseding_the_geometry_stales_the_verdict(self):
        """The fit rested on the diameters. Change one and the PASS that was
        computed from it has no standing."""
        state = self.pin(geometry())
        out = self.assess(state)
        fda = next(o.entity_id for o in out.patch.operations
                   if o.entity_type == "FeasibilityDomainAssessment"
                   and o.fields.get("domain") == "gross_interference")
        self.assertEqual("STANDING", self.val(state, fda))
        self.revise(state, Op("SUPERSEDE", "Interface", "IFC-0A",
                              {"mating_geometry": dict(geometry(inner_diameter=1.2),
                                                       interface=None)}, "t",
                              reason="the pin was resized"), stage="s04")
        self.assertEqual("STALE", self.val(state, fda))

    def test_F8b_superseding_the_axis_joint_stales_it_too(self):
        state = self.pin(geometry())
        out = self.assess(state)
        fda = next(o.entity_id for o in out.patch.operations
                   if o.entity_type == "FeasibilityDomainAssessment"
                   and o.fields.get("domain") == "gross_interference")
        self.revise(state, Op("SUPERSEDE", "Joint", "JNT-0A",
                              {"axis_direction": "+Z"}, "t",
                              reason="the hinge axis was redrawn"), stage="s03")
        self.assertEqual("STALE", self.val(state, fda))

    def test_F9_reversing_parent_and_child_changes_nothing(self):
        def run(reverse):
            top = pin_topology()
            if reverse:
                j = top["joints"][0]
                j["parent_group"], j["child_group"] = j["child_group"], j["parent_group"]
            state = self.hinge(s03a=top, s04a=pin_arrangement(geometry()),
                               s04b=motion("A", "JNT-0A", _group(1, "A")))
            out = self.assess(state, apply_patch=False)
            return {d: (self.domain(out, d).status,
                        tuple(self.domain(out, d).reason_codes))
                    for d in ("gross_interference", "assemblability")}
        self.assertEqual(run(False), run(True))


# =====================================================================
# The s04 check reads the same rule; the boundary refuses another branch
# =====================================================================
class TestOtherReaders(_Mating):

    def test_C1_the_configuration_interference_check_reads_the_same_rule(self):
        """S04A-C4 reports an overlapping CLEARANCE pair as NOT_VERIFIED. With
        an established fit it reports nothing for that pair; with a
        contradicted one it reports the contradiction, in the fit rule's own
        words - not "unverified" of a pin the evaluator has convicted."""
        clean = self.pin(geometry())
        self.assertEqual([], [p for p in s04.configuration_interference_check(clean)
                              if "BOD-G0A" in p and "BOD-G1A" in p])
        none = self.pin(None)
        self.assertTrue(any("CLEARANCE_NOT_VERIFIED" in p
                            for p in s04.configuration_interference_check(none)))
        bad = self.pin(geometry(inner_diameter=1.2))
        found = [p for p in s04.configuration_interference_check(bad)
                 if "REQUIRED_CLEARANCE_NOT_REALIZED" in p]
        self.assertTrue(found, s04.configuration_interference_check(bad))

    def test_E1_a_nested_reference_into_another_branch_is_refused_at_the_write(self):
        """`mating_geometry.axis_joint` declares INVOCATION_BRANCH, exactly as
        a top-level reference would. The branch-authority walk used to stop at
        the top level, so another candidate's joint - which RESOLVES - was
        accepted one level down."""
        from ver3.assy_v3.state.patch import StagePatch
        state = self.seed()
        self.candidates(state)
        self.hinge(state=state, s03a=pin_topology(), s04a=pin_arrangement(None),
                   s04b=motion("A", "JNT-0A", _group(1, "A")))
        top_b = topology("B", 2, [(0, 1)], axis="+Y")
        top_b["interfaces"][0]["interaction_kind"] = "CLEARANCE"
        self.branch(state, "B", top_b, realization("B"),
                    arrangement({k.replace("A", "B"): v for k, v in PIN_IN_LID.items()},
                                steps=["ASY-0B"]),
                    motion("B", "JNT-0B", _group(1, "B")))
        base = dict(geometry()); base.pop("interface")

        def trial(geom):
            patch = StagePatch(
                patch_id="probe", run_id=state.run_id, stage_id="s04", stage_attempt=9,
                parent_state_hash=state.state_hash(),
                operations=[Op("EXTEND", "Interface", "IFC-0A",
                               {"mating_geometry": geom}, "s04a:arrangement",
                               premise_refs=["CND-A"])],
                execution_status="SUCCESS", provenance={"provider": "probe"})
            return state.validate(patch)
        self.assertEqual([], trial(base))
        for field, foreign in (("axis_joint", "JNT-0B"), ("outer_body", "BOD-G0B")):
            problems = trial(dict(base, **{field: foreign}))
            self.assertTrue(any("FOREIGN_BRANCH" in p
                                and "mating_geometry[0].%s" % field in p
                                for p in problems), (field, problems))


# =====================================================================
# Gate B - the producer
# =====================================================================
class TestProducer(_Mating):

    def test_B1_s04a_extends_the_interface_it_refines(self):
        state = self.pin(geometry())
        i = state.entities["IFC-0A"]
        self.assertEqual("PIN", i["mating_geometry"]["inner_feature"])
        self.assertEqual([("s04", ["mating_geometry"])],
                         [(x["stage"], x["fields"]) for x in i["_extensions"]])
        for p in ("BOD-G0A", "BOD-G1A", "JNT-0A", "SCL-CND-A"):
            self.assertIn(p, i["_premises"], p)

    def test_B2_a_geometry_that_establishes_nothing_is_declared_incomplete(self):
        state = self.pin(geometry(inner_feature="SHAFT", outer_feature="HOLE"))
        self.assertTrue(any("establishes nothing" in p
                            for p in self.last_s04a.declared_incompleteness),
                        self.last_s04a.declared_incompleteness)

    def test_B3_the_prompt_asks_for_the_geometry_and_forbids_the_verdict(self):
        prompt = s04.S04A_PROMPT
        self.assertIn("mating_geometry[]", prompt)
        self.assertIn("OVERLAP ON PURPOSE", prompt)
        self.assertIn("not stated by you", prompt)
        self.assertIn("Do not state that anything interferes or is clear", prompt)

    def test_B4_nothing_invents_an_interface_from_an_overlap(self):
        """A geometry naming an interface the candidate does not have is
        dropped by the producer, not created. s03a says which pairs are
        intended; s04a realizes them."""
        state = self.pin(geometry(interface="IFC-NOPE"))
        self.assertEqual(1, len([i for i in state.family("Interface")
                                 if "CND-A" in i["_premises"]]))
        self.assertTrue(any("no interface of this candidate" in p
                            for p in self.last_s04a.declared_incompleteness))


if __name__ == "__main__":
    unittest.main()
