"""The source-language audit catches what it missed before, and nothing else.

The previous scan matched `loosen*` and missed `work themselves loose` — the same
property spelled as a phrase. These tests pin the fix in both directions: the
phrase forms are detected, and `loose pieces` is not, because banning the word
would delete a legitimate requirement in order to catch a different one.
"""

import unittest

from . import _paths
from . import source_audit as sa


def _hits(text, category="OP-13"):
    return [f["match"] for f in sa.audit_overprescription(text) if f["category"] == category]


class TestContactDegradationDetection(unittest.TestCase):
    """OP-13 must be phrase-aware, not token-aware."""

    def test_loosen_forms_are_detected(self):
        for phrase in ("loosen", "loosens", "loosened", "loosening"):
            with self.subTest(phrase=phrase):
                self.assertTrue(_hits("the parts should not %s over time" % phrase))

    def test_come_loose_forms_are_detected(self):
        for phrase in ("come loose", "comes loose", "came loose", "coming loose"):
            with self.subTest(phrase=phrase):
                self.assertTrue(_hits("a leg should never %s in use" % phrase))

    def test_work_itself_loose_forms_are_detected(self):
        """The exact family the token scan missed."""
        for phrase in ("work itself loose", "work themselves loose",
                       "works itself loose", "works themselves loose",
                       "worked itself loose", "working themselves loose"):
            with self.subTest(phrase=phrase):
                self.assertTrue(_hits("the legs should not %s" % phrase),
                                "%r not detected" % phrase)

    def test_bare_work_loose_is_detected(self):
        self.assertTrue(_hits("the legs should not work loose"))

    def test_other_degradation_words_are_detected(self):
        for phrase in ("backlash", "slop", "wobble", "rattle", "rattling",
                       "vibration", "wear", "fatigue", "lifetime", "durability"):
            with self.subTest(phrase=phrase):
                self.assertTrue(_hits("there should be no %s" % phrase))

    def test_play_between_parts_is_detected(self):
        self.assertTrue(_hits("there should be no play between the parts"))

    # -- the other direction: legitimate uses must survive -------------------

    def test_loose_pieces_is_not_detected(self):
        """`loose pieces` is a user describing an unattached component.

        Banning the adjective would delete a real requirement in order to catch
        a different one, so this case is as important as the detections above.
        """
        self.assertEqual([], _hits("I do not want loose pieces to look after"))

    def test_loose_parts_is_not_detected(self):
        self.assertEqual([], _hits("no loose parts to keep somewhere"))

    def test_the_adjective_alone_is_not_detected(self):
        self.assertEqual([], _hits("a loose fit is not what I mean here"))

    def test_come_off_is_not_detected(self):
        """The R3 replacement must not itself trip OP-13."""
        self.assertEqual([], _hits("they should not fold back, twist aside, or come off"))

    def test_playing_and_player_are_not_detected(self):
        """`play` only matters as clearance, i.e. play IN or BETWEEN something."""
        self.assertEqual([], _hits("I play music while I work at my desk"))


class TestAuditCoversTheOtherCategories(unittest.TestCase):
    """OP-13 was added; it must not have displaced anything."""

    def test_all_thirteen_categories_are_present(self):
        ids = [c["id"] for c in sa.OVERPRESCRIPTION_CATEGORIES]
        self.assertEqual(13, len(ids))
        self.assertEqual(sorted(set(ids)), sorted(ids), "duplicate category id")

    def test_every_category_states_why_it_exists(self):
        for cat in sa.OVERPRESCRIPTION_CATEGORIES:
            with self.subTest(category=cat["id"]):
                self.assertTrue(cat["why"].strip())

    def test_each_category_still_fires_on_its_own_subject(self):
        samples = {
            "OP-01": "it must have one degree of freedom",
            "OP-02": "use a hinge at the base",
            "OP-03": "a latch holds it open",
            "OP-04": "the leg runs in a guide",
            "OP-05": "a four-bar linkage opens it",
            "OP-06": "it should be 200 mm tall",
            "OP-07": "it should have three parts",
            "OP-08": "the oracle defines this",
            "OP-09": "see REQ-001",
            "OP-10": "the acceptance criteria are these",
            "OP-11": "it must carry a load of some weight",
            "OP-12": "suitable for injection moulding",
            "OP-13": "nothing should work themselves loose",
        }
        for cid, text in samples.items():
            with self.subTest(category=cid):
                fired = {f["category"] for f in sa.audit_overprescription(text)}
                self.assertIn(cid, fired)

    def test_findings_carry_inspectable_context(self):
        """A match with no context cannot be reviewed, and an unreviewed match is not evidence."""
        for f in sa.audit_overprescription("the legs may work themselves loose in time"):
            with self.subTest(match=f["match"]):
                self.assertTrue(f["context"].strip())
                self.assertIn(f["match"], f["context"])


class TestRevisedBM003Request(unittest.TestCase):
    """The frozen source, after amendment R3."""

    @classmethod
    def setUpClass(cls):
        with open(_paths.request_path("BM-003"), encoding="utf-8") as fh:
            cls.text = fh.read()

    def test_request_passes_the_overprescription_audit(self):
        findings = sa.unreviewed_findings(self.text)
        self.assertEqual([], findings,
                         "unreviewed matches: %s" % [(f["category"], f["match"]) for f in findings])

    def test_request_passes_the_contact_degradation_category(self):
        self.assertEqual([], _hits(self.text))

    def test_request_still_contains_loose_pieces(self):
        """The legitimate use survived the amendment.

        Compared against whitespace-normalized text: the request is hard-wrapped,
        and this phrase happens to straddle a line break.
        """
        self.assertIn("loose pieces", " ".join(self.text.split()))

    def test_request_carries_the_r3_wording(self):
        self.assertIn("fold back, twist aside, or come off", " ".join(self.text.split()))
        self.assertNotIn("work themselves loose", self.text)

    def test_request_passes_the_underdefinition_audit(self):
        missing = sa.audit_underdefinition(self.text)
        self.assertEqual([], missing, "intent elements missing: %s" % missing)

    def test_all_three_frozen_requests_pass_the_audit(self):
        """BM-001 and BM-002 are extracted, so a hit would be a finding about the
        SOURCE rather than about our drafting — but it would still need to be seen."""
        for bm in _paths.BENCHMARK_IDS:
            with self.subTest(benchmark=bm):
                with open(_paths.request_path(bm), encoding="utf-8") as fh:
                    text = fh.read()
                self.assertEqual([], _hits(text))


class TestReviewRegister(unittest.TestCase):
    """A scan result is not evidence unless the match was inspected."""

    def test_accepted_matches_are_fully_justified(self):
        for entry in sa.ACCEPTED_MATCHES:
            with self.subTest(match=entry.get("match")):
                for field in ("match", "category", "where", "verdict", "action"):
                    self.assertIn(field, entry)

    def test_reviewed_matches_record_a_verdict_and_an_action(self):
        self.assertTrue(sa.REVIEWED_AND_FIXED, "no review history recorded")
        for entry in sa.REVIEWED_AND_FIXED:
            with self.subTest(match=entry["match"]):
                self.assertTrue(entry["where"].strip())
                self.assertTrue(entry["action"].strip())
                self.assertIn(entry["verdict"], (
                    "FALSE_POSITIVE", "REAL_MATCH", "REAL_MATCH_BENIGN_MEANING",
                    "REAL_MATCH_MISSED_BY_TOKEN_SCAN"))

    def test_the_missed_phrase_is_on_the_record(self):
        matches = {e["match"] for e in sa.REVIEWED_AND_FIXED}
        self.assertIn("work themselves loose", matches)

    def test_reviewed_categories_exist(self):
        ids = {c["id"] for c in sa.OVERPRESCRIPTION_CATEGORIES}
        for entry in sa.REVIEWED_AND_FIXED:
            with self.subTest(match=entry["match"]):
                self.assertIn(entry["category"], ids)


if __name__ == "__main__":
    unittest.main()
