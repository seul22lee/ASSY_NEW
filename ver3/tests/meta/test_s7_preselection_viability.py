"""EVERY PRE-SELECTION BLOCKER HAS AN OWNER, AND ONE MEANING.

A benchmark of six candidates reached selection with one viable, and the
other five were stopped by findings that traced, one by one, not to the
designs but to three seams where a fact had no owner or had two meanings:

  arrival     s03 owns the side a part arrives from (`access_side`) - a
              required field with no vocabulary and no reader. s04a asked
              the model for the same fact a second time as a vector, and
              its prompt said "arrives from" while both corridor evaluators
              read the vector as the part's MOTION - the opposite sign. The
              model answered in both senses; nothing compared the two
              statements; an obstruction was reported for a clip on the +X
              face of a box because "arrives from +X" was swept as "moves
              towards +X", through the box and out the far side.

  corridor    the corridor reached twice the largest extent of ANY body,
              whatever the arriving body's own size, so a 1-unit clip was
              swept 20 units through the whole arrangement.

  keep-out    S03-C12 ("every region has at least one owning body") existed
              as a state check nobody wired into the producer, so a KEEP_OUT
              with no owner was committed, given a volume wherever the model
              pictured it, and read by the sweep rule as a wall in the air.

None of this exempts anything by identity. The tests here hold the generic
invariants: one owner per fact, one meaning per field, a corridor that is the
path a part takes, and a region that is a property of a body.
"""
from __future__ import annotations

import unittest

from . import _fixtures, _paths                                        # noqa: F401

import ver3.assy_v3.stages.feasibility as s07                          # noqa: E402
import ver3.assy_v3.stages.s04_envelope_and_motion as s04              # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (            # noqa: E402
    AXIS_DIRECTIONS, S03BMobilityAndAssembly, S03TopologyAndMobility,
    retention_check)
from ver3.assy_v3.state.design_state import Contracts                   # noqa: E402
from ver3.assy_v3.state.patch import Op                                 # noqa: E402
from .test_s7_feasibility import (                                      # noqa: E402
    HINGE_BOXES, _Feas, _group, arrangement, motion, realization, side_of,
    topology)


def step(sid="ASY-0A", side="+Z", direction=None, body="BOD-G0A"):
    out = {"entity_id": sid, "order_index": 1, "body": body, "access_side": side,
           "activates": [], "termination_strategy": "NONE", "path_kind": "RIGID",
           "depends_on": []}
    if direction is not None:
        out["insertion_direction"] = direction
    return out


# =====================================================================
# A - one statement of arrival
# =====================================================================
class TestArrivalHasOneOwner(unittest.TestCase):

    def test_the_vocabulary_is_one_vocabulary(self):
        """The contract's `access_side` values, s03's axis words and s04's
        axis vectors are the same set: a side s03 may state is a side s04 can
        build an approach from, and nothing else."""
        contract = Contracts().families["AssemblyStep"]["access_side"]
        self.assertEqual(sorted(contract), sorted(s04.AXIS_VECTORS))
        self.assertEqual(sorted(contract),
                         sorted(a for a in AXIS_DIRECTIONS if a != "NONE"))

    def test_the_vector_is_the_motion_from_the_side(self):
        """Arriving from +Z is moving along -Z. A part comes from outside."""
        self.assertEqual([-0.0, -0.0, -1.0], s04.motion_from_side("+Z"))
        self.assertEqual([1.0, -0.0, -0.0], s04.motion_from_side("-X"))
        self.assertIsNone(s04.motion_from_side("NONE"))
        self.assertIsNone(s04.motion_from_side(None))
        self.assertIsNone(s04.motion_from_side("up"))

    def test_one_reading_for_both_evaluators(self):
        """`approach_direction` is the only reader. Agreement yields the unit
        motion; a vector in the prompt's old "arrives from" sense, or any
        other, is the record contradicting itself - not resolved by
        preferring either half."""
        d, code, _ = s04.approach_direction(step(side="+Z", direction=[0, 0, -2]))
        self.assertEqual(([0.0, 0.0, -1.0], None), (d, code))
        d, code, note = s04.approach_direction(step(side="+Z", direction=[0, 0, 1]))
        self.assertIsNone(d)
        self.assertEqual("INSERTION_DIRECTION_CONTRADICTS_ACCESS_SIDE", code)
        self.assertIn("+Z", note)
        d, code, _ = s04.approach_direction(step(side="+Z", direction=[1, 0, 0]))
        self.assertEqual("INSERTION_DIRECTION_CONTRADICTS_ACCESS_SIDE", code)
        d, code, _ = s04.approach_direction(step(side="+Z"))
        self.assertEqual((None, "INSERTION_DIRECTION_MISSING"), (d, code))
        d, code, _ = s04.approach_direction(step(side="+Z", direction=[0, 0, 0]))
        self.assertEqual((None, "INSERTION_DIRECTION_MISSING"), (d, code))
        d, code, _ = s04.approach_direction(step(side="NONE", direction=[0, 0, -1]))
        self.assertEqual((None, "ACCESS_SIDE_UNREADABLE"), (d, code))

    def test_s04a_no_longer_asks_for_the_vector(self):
        """The question whose answer was fixed by s03's statement is gone from
        the prompt, and the response shape no longer carries a field for it."""
        prompt = s04.S04A_PROMPT
        self.assertNotIn("assembly_directions", prompt)
        self.assertNotIn("arrives from, as a", prompt)
        self.assertIn("access_side", prompt)

    def test_the_path_check_names_the_contradiction_not_an_obstruction(self):
        """A step whose stored vector contradicts its side: the corridor is
        not built from either half, and the finding says which seam."""
        payload = {"Envelope": [
            {"entity_id": "ENV-1", "body": "BOD-1",
             "extent": {"centre": [0, 0, 0], "half_extent": [1, 1, 1]}},
            {"entity_id": "ENV-2", "body": "BOD-2",
             "extent": {"centre": [0, 0, 3], "half_extent": [1, 1, 1]}}],
            "AssemblyStep": [
                step("ASY-1", "+Z", [0, 0, -1], "BOD-1"),
                dict(step("ASY-2", "+Z", [0, 0, 1], "BOD-2"), order_index=2)]}
        found = s04.assembly_path_findings(payload)
        self.assertEqual(1, len(found), found)
        self.assertTrue(found[0].startswith(
            "ASSEMBLY_DIRECTION_CONTRADICTS_ACCESS_SIDE"), found)
        # The same arrangement, stated coherently: from above, nothing in the way.
        payload["AssemblyStep"][1]["insertion_direction"] = [0, 0, -1]
        self.assertEqual([], s04.assembly_path_findings(payload))
        # And from below, coherently: through BOD-1, reported as a path finding.
        payload["AssemblyStep"][1].update(access_side="-Z",
                                          insertion_direction=[0, 0, 1])
        found = s04.assembly_path_findings(payload)
        self.assertTrue(found and found[0].startswith("ASSEMBLY_PATH_OBSTRUCTED"), found)

    def test_s03b_refuses_a_side_that_names_no_side(self):
        """The producer gate: a required field with no vocabulary accepted
        anything, and the approach built from it could be nothing."""
        stage = S03BMobilityAndAssembly()
        parsed = realization("A")
        parsed["assembly_steps"][0]["access_side"] = "from the top"
        problems = stage.completeness(parsed, {"consumer_view": {}})
        self.assertTrue(any("ASY-0A" in p and "names no side" in p for p in problems),
                        problems)
        parsed["assembly_steps"][0]["access_side"] = "NONE"
        problems = stage.completeness(parsed, {"consumer_view": {}})
        self.assertTrue(any("ASY-0A" in p and "names no side" in p for p in problems),
                        problems)
        parsed["assembly_steps"][0]["access_side"] = "+Y"
        problems = stage.completeness(parsed, {"consumer_view": {}})
        self.assertEqual([], [p for p in problems if "names no side" in p])


class TestArrivalIsDerived(_Feas):
    """Through the real stages: s03b states the side, s04a writes the vector."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def test_every_step_gets_the_motion_from_its_side(self):
        r = realization("A", steps=(0, 1))
        r["assembly_steps"][1]["order_index"] = 2
        r["assembly_steps"][0]["access_side"] = "+Z"
        r["assembly_steps"][1]["access_side"] = "-X"
        state = self.hinge(s03a=topology("A", 2, [(0, 1)]), s03b=r,
                           s04a=arrangement(HINGE_BOXES, steps=["ASY-0A", "ASY-1A"]))
        steps = {s["entity_id"]: s for s in state.family("AssemblyStep")}
        self.assertEqual([0.0, 0.0, -1.0], steps["ASY-0A"]["insertion_direction"])
        self.assertEqual([1.0, 0.0, 0.0], steps["ASY-1A"]["insertion_direction"])
        for s in steps.values():
            self.assertIsNone(s04.approach_direction(s)[1], s)

    def test_a_vector_the_model_volunteers_is_not_transcribed(self):
        """A response still carrying the retired `assembly_directions` key
        cannot put a second statement of arrival into the state."""
        r = realization("A")
        r["assembly_steps"][0]["access_side"] = "+Z"
        arr = arrangement(HINGE_BOXES, steps=["ASY-0A"])
        arr["assembly_directions"] = [{"assembly_step": "ASY-0A", "direction": [1, 0, 0]}]
        state = self.hinge(s03a=topology("A", 2, [(0, 1)]), s03b=r, s04a=arr)
        (s,) = [x for x in state.family("AssemblyStep") if x["entity_id"] == "ASY-0A"]
        self.assertEqual([0.0, 0.0, -1.0], s["insertion_direction"])

    def test_feasibility_names_the_contradiction_and_builds_no_corridor(self):
        """A state authored before the field had a meaning: the step's two
        statements disagree. Assemblability is unestablished for THAT reason,
        and no obstruction is invented from either half."""
        r = realization("A", steps=(0, 1))
        r["assembly_steps"][1]["order_index"] = 2
        r["assembly_steps"][1]["access_side"] = "+X"
        state = self.hinge(s03a=topology("A", 2, [(0, 1)]), s03b=r,
                           s04a=arrangement(HINGE_BOXES, steps=["ASY-0A", "ASY-1A"]))
        self.revise(state, Op("SUPERSEDE", "AssemblyStep", "ASY-1A",
                              {"insertion_direction": [1, 0, 0]}, "s04a:arrangement",
                              premise_refs=["CND-A"],
                              reason="authored under the old prompt"), stage="s04")
        v = self.domain(self.assess(state, apply_patch=False), "assemblability")
        self.assertEqual(s07.NOT_ESTABLISHED, v.status, v.summary)
        self.assertIn("INSERTION_DIRECTION_CONTRADICTS_ACCESS_SIDE", v.reason_codes)
        self.assertNotIn("INSERTION_PATH_NOT_CLEAR", v.reason_codes)
        self.assertIn("ASY-1A", v.premises)

    def test_the_written_state_check_reads_the_side_too(self):
        state = self.hinge()
        (s,) = [x for x in state.family("AssemblyStep") if x["entity_id"] == "ASY-0A"]
        self.assertEqual([], [p for p in retention_check(state)
                              if "ACCESS_SIDE_UNREADABLE" in p])
        self.revise(state, Op("SUPERSEDE", "AssemblyStep", "ASY-0A",
                              {"access_side": "NONE"}, "s03b:relations",
                              premise_refs=["CND-A"], reason="test"), stage="s03")
        self.assertTrue([p for p in retention_check(state)
                         if "ASSEMBLY_ACCESS_SIDE_UNREADABLE" in p and "ASY-0A" in p])


# =====================================================================
# B - the corridor is the path the part takes
# =====================================================================
class TestCorridorIsBounded(unittest.TestCase):

    BOX = {"BOD-BOX": ([-10, -10, -10], [10, 10, 10]),
           "BOD-CLIP": ([10, -0.5, -0.5], [11, 0.5, 0.5]),
           "BOD-FAR": ([-20, -0.5, -0.5], [-19, 0.5, 0.5])}

    def test_a_clip_on_one_face_is_not_swept_through_the_box(self):
        """The clip sits on the +X face and arrives from +X. Its corridor runs
        from the clip to the arrangement's +X bound and no further: it never
        reaches the box's interior, let alone the far side."""
        hull = s04.insertion_hull(self.BOX, "BOD-CLIP", s04.motion_from_side("+X"))
        self.assertGreaterEqual(hull[0][0], 10.0 - 1e-9, hull)
        self.assertFalse(s04.overlaps(hull, self.BOX["BOD-BOX"]))
        self.assertFalse(s04.overlaps(hull, self.BOX["BOD-FAR"]))

    def test_a_genuine_obstruction_still_reaches_the_bound(self):
        """The same clip arriving from -X would come through the box and
        past the far part: the bound is the arrangement's face, so both are
        met. Bounding the corridor weakened nothing real."""
        hull = s04.insertion_hull(self.BOX, "BOD-CLIP", s04.motion_from_side("-X"))
        self.assertLessEqual(hull[0][0], -20.0 + 1e-9, hull)
        self.assertTrue(s04.overlaps(hull, self.BOX["BOD-BOX"]))
        self.assertTrue(s04.overlaps(hull, self.BOX["BOD-FAR"]))

    def test_the_corridor_does_not_depend_on_another_bodys_size(self):
        """Twice the largest extent of ANY body was the old span: here that is
        40 units for a 1-unit clip. The span is now the distance to the
        bound on the approach side, whatever the other bodies measure."""
        boxes = dict(self.BOX, **{"BOD-HUGE": ([100, 100, 100], [200, 200, 200])})
        hull = s04.insertion_hull(boxes, "BOD-CLIP", s04.motion_from_side("+X"))
        self.assertFalse(s04.overlaps(hull, boxes["BOD-BOX"]))
        self.assertLessEqual(hull[1][0], 200.0 + 1e-9)

    def test_one_construction_for_both_readers(self):
        """feasibility has no private hull: it reads s04's."""
        self.assertFalse(hasattr(s07, "_insertion_hull"))


# =====================================================================
# C - a region is a property of a body
# =====================================================================
class TestRegionsHaveOwners(unittest.TestCase):

    def test_s03a_refuses_a_region_no_body_owns(self):
        """S03-C12 at the producer. An ungrounded KEEP_OUT is not a statement
        about the design; it is refused before it can be given a volume."""
        parsed = dict(topology("A", 2, [(0, 1)]),
                      functional_regions=[{"id": "FRG-A", "role": "KEEP_OUT",
                                           "owning_bodies": [],
                                           "required_by_actors": []}])
        problems = S03TopologyAndMobility().completeness(parsed, {"consumer_view": {}})
        self.assertTrue(any("FRG-A" in p and "no owning body" in p for p in problems),
                        problems)
        parsed["functional_regions"][0]["owning_bodies"] = ["BOD-NOPE"]
        problems = S03TopologyAndMobility().completeness(parsed, {"consumer_view": {}})
        self.assertTrue(any("FRG-A" in p and "BOD-NOPE" in p for p in problems), problems)
        parsed["functional_regions"][0]["owning_bodies"] = ["BOD-G0A"]
        problems = S03TopologyAndMobility().completeness(parsed, {"consumer_view": {}})
        self.assertEqual([], [p for p in problems if "FRG-A" in p])
        parsed["functional_regions"][0]["role"] = "FORBIDDEN"
        problems = S03TopologyAndMobility().completeness(parsed, {"consumer_view": {}})
        self.assertTrue(any("FRG-A" in p and "unknown role" in p for p in problems),
                        problems)

    def test_the_occupancy_check_does_not_pass_a_region_by_having_nobody_to_fail(self):
        class State:
            def __init__(self, regions):
                self.regions = regions

            def family(self, name):
                return self.regions if name == "FunctionalRegion" else []

            standing = family

        region = {"entity_id": "FRG-A", "role": "KEEP_OUT", "owning_bodies": [],
                  "volume": {"centre": [0, 0, 0], "half_extent": [1, 1, 1]}}
        found = s04.region_occupancy_check(State([region]))
        self.assertTrue(any(f.startswith("REGION_WITHOUT_OWNER: FRG-A") for f in found),
                        found)


class TestUngroundedExclusionBlocksNothing(_Feas):
    """A KEEP_OUT nothing owns, already in the state, is reported as evidence
    gross interference cannot use - not swept against. The SAME geometry with
    an owner is swept against, so nothing real was weakened."""

    @classmethod
    def setUpClass(cls):
        cls.c = Contracts()

    def swept(self, owners):
        top = dict(topology("A", 2, [(0, 1)]),
                   functional_regions=[{"id": "FRG-A", "role": "KEEP_OUT",
                                        "owning_bodies": owners,
                                        "required_by_actors": []}])
        arr = arrangement(HINGE_BOXES, steps=["ASY-0A"], region="FRG-A")
        # On top of the moving bar, where its sweep certainly is.
        arr["region_volumes"][0]["centre"] = list(HINGE_BOXES["BOD-G1A"][0])
        state = self.hinge(s03a=top, s04a=arr,
                           s04b=motion("A", "JNT-0A", _group(1, "A")))
        return self.domain(self.assess(state, apply_patch=False), "gross_interference")

    def test_an_owned_keep_out_is_still_an_obstacle(self):
        v = self.swept(["BOD-G0A"])
        self.assertIn("SWEEP_MEETS_KEEP_OUT", v.reason_codes, v.summary)
        self.assertNotIn("REGION_WITHOUT_OWNER", v.reason_codes)

    def test_an_ownerless_keep_out_is_unusable_evidence_not_a_wall(self):
        # s03a's gate refuses this now; the state is written past it, as the
        # historical states were, to hold the consumer to its own rule.
        top = dict(topology("A", 2, [(0, 1)]))
        state = self.hinge(s03a=top, s04a=arrangement(HINGE_BOXES, steps=["ASY-0A"]),
                           s04b=motion("A", "JNT-0A", _group(1, "A")))
        self.revise(state, Op("CREATE", "FunctionalRegion", "FRG-A",
                              {"role": "KEEP_OUT", "owning_bodies": [],
                               "required_by_actors": [], "reach_targets": []},
                              "s03:topology", premise_refs=["CND-A"]), stage="s03")
        self.revise(state, Op("EXTEND", "FunctionalRegion", "FRG-A",
                              {"volume": {"centre": list(HINGE_BOXES["BOD-G1A"][0]),
                                          "half_extent": [1, 1, 1]}},
                              "s04a:arrangement", premise_refs=["CND-A"]), stage="s04")
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertIn("REGION_WITHOUT_OWNER", v.reason_codes, v.summary)
        self.assertNotIn("SWEEP_MEETS_KEEP_OUT", v.reason_codes, v.summary)
        self.assertEqual(s07.NOT_ESTABLISHED, v.status)
        self.assertIn("FRG-A", v.premises)

    def test_a_sweep_through_an_access_region_is_not_a_keep_out(self):
        """`excludes_occupancy` is about sitting, KEEP_OUT about entering. A
        lid swinging through the hand's access region is not the promise
        broken - CND-0004's lesson, held generically."""
        top = dict(topology("A", 2, [(0, 1)]),
                   functional_regions=[{"id": "FRG-A", "role": "ACCESS",
                                        "owning_bodies": ["BOD-G0A"],
                                        "required_by_actors": []}])
        arr = arrangement(HINGE_BOXES, steps=["ASY-0A"], region="FRG-A")
        arr["region_volumes"][0]["centre"] = list(HINGE_BOXES["BOD-G1A"][0])
        state = self.hinge(s03a=top, s04a=arr,
                           s04b=motion("A", "JNT-0A", _group(1, "A")))
        v = self.domain(self.assess(state, apply_patch=False), "gross_interference")
        self.assertNotIn("SWEEP_MEETS_KEEP_OUT", v.reason_codes, v.summary)
        self.assertNotIn("REGION_WITHOUT_OWNER", v.reason_codes, v.summary)


if __name__ == "__main__":
    unittest.main()
