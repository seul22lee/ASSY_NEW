"""S05-C4 asks the selected candidate for ITS obligations, not for every one.

The design-wide obligation set contains three different kinds of thing as far as
one candidate is concerned:

  UNIVERSAL                          it must satisfy this, whatever it is
  CANDIDATE_DISCRIMINATING, taken on  it must satisfy this because it took it on
  CANDIDATE_DISCRIMINATING, not taken  this exists because a DIFFERENT candidate
                                       works differently

C4 used to demand a realization for all three. That is not a strict check; it is
a wrong one. It made the chosen design answerable for obligations that exist
only because a rejected alternative had them, so an embodiment could be complete
and still be reported as failing - and the only way to pass would be to author
realizations for a mechanism nobody selected.

The tests below fix the population and then prove the check can still FAIL. A
narrowed check that cannot fail would be worse than the wrong one it replaced.
"""

import unittest

from ver3.assy_v3.stages import s05_embodiment as s05


def obligation(oid, scope):
    return {"entity_id": oid, "statement": "something must hold",
            "scope": scope, "mandatory": True, "satisfiable_at": "s05",
            "evidence_route": "MOBILITY_ANALYSIS", "route_available": True,
            "derived_from_requirements": []}


def acceptance(cid, candidate, obligations):
    return {"entity_id": cid, "candidate": candidate,
            "obligations": list(obligations), "predicates": []}


def realization(rid, obligations, predicate="the gap stays positive"):
    return {"id": rid, "addresses_obligations": list(obligations),
            "participating_features": ["FEA-1"],
            "verification_predicate": predicate}


class _Population(unittest.TestCase):
    """A design where the two candidates owe different things."""

    def view(self, *, accepted=("OBL-A",)):
        return {
            "Obligation": [
                obligation("OBL-U", "UNIVERSAL"),
                obligation("OBL-A", "CANDIDATE_DISCRIMINATING"),
                obligation("OBL-B", "CANDIDATE_DISCRIMINATING"),
            ],
            "AcceptanceContract": [acceptance("ACC-A", "CND-A", accepted)],
        }


class TestApplicability(_Population):

    def test_the_fixture_offers_something_to_exclude(self):
        """Otherwise 'B is excluded' would be true of an empty set."""
        ids = {o["entity_id"] for o in self.view()["Obligation"]}
        self.assertEqual({"OBL-U", "OBL-A", "OBL-B"}, ids)

    def test_a_universal_obligation_applies(self):
        self.assertIn("OBL-U",
                      s05.applicable_obligations_for_embodiment(self.view()))

    def test_a_discriminating_obligation_this_candidate_took_on_applies(self):
        self.assertIn("OBL-A",
                      s05.applicable_obligations_for_embodiment(self.view()))

    def test_another_candidates_discriminating_obligation_does_not(self):
        self.assertNotIn("OBL-B",
                         s05.applicable_obligations_for_embodiment(self.view()))

    def test_reversing_the_acceptance_reverses_the_applicability(self):
        """So nothing above passes because of the order they are declared in."""
        applicable = s05.applicable_obligations_for_embodiment(
            self.view(accepted=("OBL-B",)))
        self.assertIn("OBL-B", applicable)
        self.assertNotIn("OBL-A", applicable)

    def test_an_obligation_with_no_stated_scope_still_applies(self):
        """Fail OPEN. A missing field is not an excused duty, and silently
        dropping it would let a contract omission discharge an obligation."""
        view = {"Obligation": [obligation("OBL-X", None)], "AcceptanceContract": []}
        self.assertIn("OBL-X", s05.applicable_obligations_for_embodiment(view))

    def test_satisfiable_at_is_not_read_as_ownership(self):
        """`satisfiable_at` is the EARLIEST stage, not the owning one. An
        obligation that became satisfiable at s03 is still this candidate's to
        realize in geometry."""
        view = {"Obligation": [dict(obligation("OBL-E", "UNIVERSAL"),
                                    satisfiable_at="s03")],
                "AcceptanceContract": []}
        self.assertIn("OBL-E", s05.applicable_obligations_for_embodiment(view))


class TestC4UsesThatPopulation(_Population):

    def test_realizing_every_applicable_obligation_passes(self):
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A"])]},
            self.view())
        self.assertEqual([], problems)

    def test_omitting_another_candidates_obligation_is_not_a_failure(self):
        """The defect this repair exists for."""
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A"])]},
            self.view())
        self.assertNotIn("OBL-B", " ".join(problems))

    def test_omitting_an_applicable_universal_obligation_FAILS(self):
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-A"])]}, self.view())
        self.assertTrue(problems, "C4 accepted an undischarged universal obligation")
        self.assertIn("OBL-U", " ".join(problems))

    def test_omitting_this_candidates_own_discriminating_obligation_FAILS(self):
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U"])]}, self.view())
        self.assertTrue(problems)
        self.assertIn("OBL-A", " ".join(problems))

    def test_an_unpredicated_citation_discharges_nothing(self):
        """Unchanged by this repair, and re-proved so narrowing the population
        did not quietly narrow the check as well."""
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A"],
                                          predicate="  ")]},
            self.view())
        self.assertTrue(problems)
        self.assertIn("RLZ-1", " ".join(problems))

    def test_with_no_acceptance_context_only_universals_are_demanded(self):
        """A design whose obligations are all universal authors no acceptance
        contract, and must not thereby fail every discriminating obligation."""
        view = dict(self.view(), AcceptanceContract=[])
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U"])]}, view)
        self.assertEqual([], problems)



class TestANonApplicableClaimIsRejected(_Population):
    """§3.4. Coverage alone is not enough.

    A realization that discharges everything required AND something else looked
    correct: every applicable obligation was cited, so C4 passed. But that
    something else is a claim about a mechanism nobody selected, and accepting
    it writes into state that the chosen design satisfied an obligation belonging
    to a rejected alternative.
    """

    def test_citing_only_applicable_obligations_passes(self):
        self.assertEqual([], s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A"])]},
            self.view()))

    def test_citing_another_candidates_obligation_FAILS(self):
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A", "OBL-B"])]},
            self.view())
        self.assertTrue(problems, "a claim about an unselected mechanism was "
                                  "accepted because coverage was complete")
        self.assertIn("OBL-B", " ".join(problems))

    def test_the_failure_names_the_exact_obligation(self):
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A", "OBL-B"])]},
            self.view())
        offending = [p for p in problems if "OBL-B" in p]
        self.assertEqual(1, len(offending), problems)
        self.assertIn("RLZ-1", offending[0])
        self.assertNotIn("OBL-A", offending[0])

    def test_citing_only_the_non_applicable_one_fails_twice_over(self):
        """Once for the claim, once for each duty left undischarged."""
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-B"])]}, self.view())
        joined = " ".join(problems)
        self.assertIn("OBL-B", joined)
        self.assertIn("OBL-U", joined)
        self.assertIn("OBL-A", joined)

    def test_an_obligation_outside_the_view_entirely_is_reported_as_such(self):
        """A model naming an id it was never shown is a different mistake from
        naming one it was shown but does not owe, and the message says which."""
        problems = s05.check_c4_obligations_realized(
            {"realizations": [realization("RLZ-1", ["OBL-U", "OBL-A", "OBL-ZZ"])]},
            self.view())
        offending = [p for p in problems if "OBL-ZZ" in p]
        self.assertTrue(offending)
        self.assertIn("not in this view at all", offending[0])


class TestOneAuthorityForApplicability(unittest.TestCase):
    """§3.2. The view and the validator must not be able to disagree."""

    def test_the_stage_delegates_rather_than_reimplementing(self):
        import inspect
        from ver3.assy_v3.view import applicable_obligation_ids
        source = inspect.getsource(s05.applicable_obligations_for_embodiment)
        self.assertIn("applicable_obligation_ids", source,
                      "s05 computes applicability itself; a second "
                      "implementation can drift from the one that decides what "
                      "the stage is shown")
        self.assertNotIn("CANDIDATE_DISCRIMINATING", source,
                         "the scope vocabulary is being interpreted in a second "
                         "place")
        self.assertTrue(callable(applicable_obligation_ids))

    def test_the_view_rule_and_the_checker_agree_on_the_same_records(self):
        from ver3.assy_v3.view import applicable_obligation_ids
        view = {"Obligation": [obligation("OBL-U", "UNIVERSAL"),
                               obligation("OBL-A", "CANDIDATE_DISCRIMINATING"),
                               obligation("OBL-B", "CANDIDATE_DISCRIMINATING")],
                "AcceptanceContract": [acceptance("ACC-A", "CND-A", ["OBL-A"])]}
        self.assertEqual(
            applicable_obligation_ids(view["Obligation"],
                                      view["AcceptanceContract"]),
            s05.applicable_obligations_for_embodiment(view))


if __name__ == "__main__":                                       # pragma: no cover
    unittest.main()
