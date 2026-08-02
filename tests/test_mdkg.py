#!/usr/bin/env python3
"""Test suite for the mdkg pipeline.

Written against ``unittest`` rather than pytest so it runs on a bare Python
install with no extra test dependency.

    python3 -m unittest discover -s tests -v
    python3 tests/test_mdkg.py                # same thing

The suite covers the six areas the project brief calls out -- page-number
preservation, evidence linkage, claim validation, unit handling, substitution
constraints and cross-book alignment -- plus a negative control that injects
deliberate defects and asserts SHACL rejects them.  A validation suite that has
never been shown to fail is not evidence of anything.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml  # noqa: E402
from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402
from rdflib.namespace import RDF, RDFS, XSD  # noqa: E402

MDCORE = Namespace("https://w3id.org/mdkg/core#")
MECH = Namespace("https://w3id.org/mdkg/mechanical-design#")
MELEM = Namespace("https://w3id.org/mdkg/machine-elements#")
EV = Namespace("https://w3id.org/mdkg/evidence#")
MDKG = Namespace("https://w3id.org/mdkg/instances#")

DATA = REPO_ROOT / "data"
BUILD = REPO_ROOT / "build"
CONFIG = yaml.safe_load((REPO_ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


class MdkgTestBase(unittest.TestCase):
    """Shared fixtures, loaded once for the whole suite."""

    spans: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]
    graph: Graph

    @classmethod
    def setUpClass(cls) -> None:
        for required in (DATA / "evidence_spans.jsonl", DATA / "claims.jsonl",
                         BUILD / "mdkg-full.ttl"):
            if not required.exists():
                raise unittest.SkipTest(f"{required} missing; run the build pipeline first")
        cls.spans = load_jsonl(DATA / "evidence_spans.jsonl")
        cls.claims = load_jsonl(DATA / "claims.jsonl")
        cls.graph = Graph()
        cls.graph.parse(BUILD / "mdkg-full.ttl", format="turtle")


# ---------------------------------------------------------------------------
# 1. Page-number preservation
# ---------------------------------------------------------------------------


class TestPageNumberPreservation(MdkgTestBase):
    """The printed page and the PDF index must never be conflated or derived."""

    def test_every_span_records_both_page_numbers(self) -> None:
        for span in self.spans:
            with self.subTest(span=span["span_id"]):
                self.assertIsInstance(span["pdf_page_index"], int)
                self.assertIsInstance(span["pdf_page_number"], int)
                self.assertEqual(span["pdf_page_number"], span["pdf_page_index"] + 1)
                self.assertIn("printed_page", span, "printed_page field must exist even when null")

    def test_printed_page_is_a_string_not_an_index(self) -> None:
        """A printed page is what is inked on the paper; it is never the index."""
        for span in self.spans:
            if span["printed_page"] is None:
                continue
            with self.subTest(span=span["span_id"]):
                self.assertIsInstance(span["printed_page"], str)
                self.assertNotEqual(
                    span["printed_page"], str(span["pdf_page_index"]),
                    "printed page equals the PDF index -- likely computed, not read",
                )

    def test_printed_page_only_when_label_is_arabic(self) -> None:
        for span in self.spans:
            with self.subTest(span=span["span_id"]):
                if span["page_label_style"] != "arabic":
                    self.assertIsNone(span["printed_page"])

    def test_front_matter_offset_is_not_assumed_constant(self) -> None:
        """The offset happens to be constant in these two files, but is never used.

        This test documents the offset and asserts that it differs between the
        two sources -- which is exactly why the code must not compute one from
        the other.
        """
        offsets: Dict[str, set] = {}
        for span in self.spans:
            if span["printed_page"] and span["printed_page"].isdigit():
                offsets.setdefault(span["doc_id"], set()).add(
                    span["pdf_page_index"] - int(span["printed_page"])
                )
        self.assertEqual(offsets["mott6"], {16})
        self.assertEqual(offsets["shigley10"], {22})
        self.assertNotEqual(
            offsets["mott6"], offsets["shigley10"],
            "the two sources have different offsets; neither may be hard-coded",
        )

    def test_rdf_keeps_the_two_numbers_on_separate_properties(self) -> None:
        pages = list(self.graph.subjects(RDF.type, EV.Page))
        self.assertGreater(len(pages), 0)
        for page in pages:
            with self.subTest(page=str(page)):
                self.assertIsNotNone(self.graph.value(page, EV.pdfPageIndex))
                self.assertIsNotNone(self.graph.value(page, EV.pdfPageNumber))
                printed = self.graph.value(page, EV.printedPage)
                if printed is not None:
                    self.assertNotEqual(EV.printedPage, EV.pdfPageIndex)
                    self.assertIsInstance(printed.toPython(), str)


# ---------------------------------------------------------------------------
# 2. Evidence linkage
# ---------------------------------------------------------------------------


class TestEvidenceLinkage(MdkgTestBase):

    def test_every_claim_cites_at_least_one_span(self) -> None:
        for claim in self.claims:
            with self.subTest(claim=claim["claim_id"]):
                self.assertTrue(claim["evidence_span_ids"], "claim has no evidence")

    def test_every_cited_span_exists(self) -> None:
        known = {s["span_id"] for s in self.spans}
        for claim in self.claims:
            for span_id in claim["evidence_span_ids"]:
                with self.subTest(claim=claim["claim_id"], span=span_id):
                    self.assertIn(span_id, known)

    def test_claim_and_its_spans_come_from_the_same_document(self) -> None:
        by_id = {s["span_id"]: s for s in self.spans}
        for claim in self.claims:
            for span_id in claim["evidence_span_ids"]:
                with self.subTest(claim=claim["claim_id"], span=span_id):
                    self.assertEqual(by_id[span_id]["doc_id"], claim["doc_id"])

    def test_claim_locations_are_resolved_not_typed(self) -> None:
        """Locations must match the spans, proving they were derived from them."""
        by_id = {s["span_id"]: s for s in self.spans}
        for claim in self.claims:
            with self.subTest(claim=claim["claim_id"]):
                self.assertTrue(claim["locations"])
                for loc in claim["locations"]:
                    span = by_id[loc["span_id"]]
                    self.assertEqual(loc["pdf_page_index"], span["pdf_page_index"])
                    self.assertEqual(loc["printed_page"], span["printed_page"])
                    self.assertEqual(loc["chapter_number"], span["chapter_number"])
                    self.assertEqual(loc["section_number"], span["section_number"])

    def test_rdf_claims_reach_a_page_through_a_span(self) -> None:
        claims = list(self.graph.subjects(RDF.type, EV.NormalizedClaim))
        self.assertGreater(len(claims), 0)
        for claim in claims:
            with self.subTest(claim=str(claim)):
                reached = [
                    p
                    for span in self.graph.objects(claim, EV.supportedByEvidence)
                    for p in self.graph.objects(span, EV.spanOnPage)
                ]
                self.assertTrue(reached, "claim does not reach any page through its evidence")

    def test_every_span_carries_a_bounding_box(self) -> None:
        for span in self.spans:
            with self.subTest(span=span["span_id"]):
                self.assertEqual(len(span["bbox"]), 4)
                x0, y0, x1, y1 = span["bbox"]
                self.assertLess(x0, x1)
                self.assertLess(y0, y1)


# ---------------------------------------------------------------------------
# 3. Claim validation and review discipline
# ---------------------------------------------------------------------------


class TestClaimValidation(MdkgTestBase):

    def test_no_claim_is_human_verified_without_a_reviewer(self) -> None:
        for claim in self.claims:
            if claim["review_status"] == "HumanVerified":
                with self.subTest(claim=claim["claim_id"]):
                    self.assertTrue(claim["reviewed_by"], "HumanVerified without a named reviewer")

    def test_automated_pipeline_did_not_self_certify(self) -> None:
        """v0.1 expects zero HumanVerified claims: nothing has been signed off yet."""
        verified = [c for c in self.claims if c["review_status"] == "HumanVerified"]
        self.assertEqual(
            verified, [],
            "automated extraction must not produce HumanVerified claims",
        )

    def test_review_status_is_from_the_controlled_ladder(self) -> None:
        allowed = set(CONFIG["confidence"]["review_states"])
        for claim in self.claims:
            with self.subTest(claim=claim["claim_id"]):
                self.assertIn(claim["review_status"], allowed)

    def test_claim_seeds_reject_a_human_verified_seed(self) -> None:
        """The builder must refuse to mint HumanVerified from a seed file."""
        import build_claims

        seed = {
            "id": "test-c-0001", "doc": "mott6", "topic": "test",
            "normalized_statement": "x", "evidence": ["mott6-es-0001"],
            "review_status": "HumanVerified",
        }
        spans = {s["span_id"]: s for s in self.spans}
        with self.assertRaises(build_claims.ClaimBuildError):
            build_claims.build_claim(seed, {}, spans)

    def test_claim_with_no_evidence_is_rejected(self) -> None:
        import build_claims

        seed = {"id": "test-c-0002", "doc": "mott6", "topic": "test",
                "normalized_statement": "x", "evidence": []}
        with self.assertRaises(build_claims.ClaimBuildError):
            build_claims.build_claim(seed, {}, {})

    def test_threshold_claims_declare_universality(self) -> None:
        for claim in self.claims:
            if claim.get("threshold"):
                with self.subTest(claim=claim["claim_id"]):
                    self.assertIn("is_universal", claim["threshold"])

    def test_no_threshold_is_claimed_universal_in_v01(self) -> None:
        """Neither book fixes a universal boundary for its qualitative terms."""
        for claim in self.claims:
            th = claim.get("threshold")
            if th:
                with self.subTest(claim=claim["claim_id"], term=th["term"]):
                    self.assertFalse(
                        th["is_universal"],
                        f"'{th['term']}' marked universal; no cited source supports that",
                    )

    def test_verification_claims_declare_all_three_flags(self) -> None:
        for claim in self.claims:
            v = claim.get("verification")
            if v:
                with self.subTest(claim=claim["claim_id"]):
                    for key in ("test_recommended", "test_procedure_specified",
                                "acceptance_criterion_specified"):
                        self.assertIn(key, v)

    def test_the_unspecified_test_case_is_recorded_as_such(self) -> None:
        """Mott recommends a test without defining one; that gap must be explicit."""
        target = next(c for c in self.claims if c["claim_id"] == "mott6-c-0051")
        v = target["verification"]
        self.assertTrue(v["test_recommended"])
        self.assertFalse(v["test_procedure_specified"])
        self.assertFalse(v["acceptance_criterion_specified"])
        self.assertTrue(v["external_authority"])


# ---------------------------------------------------------------------------
# 4. Unit handling
# ---------------------------------------------------------------------------


class TestUnitHandling(MdkgTestBase):

    def test_every_quantity_has_a_unit(self) -> None:
        for claim in self.claims:
            for qty in claim["quantities"]:
                with self.subTest(claim=claim["claim_id"], role=qty["role"]):
                    self.assertTrue(qty["unit"])

    def test_dimensionless_is_explicit_not_empty(self) -> None:
        dimensionless = [
            q for c in self.claims for q in c["quantities"] if q["unit"] == "dimensionless"
        ]
        self.assertGreater(len(dimensionless), 0, "expected some dimensionless quantities")
        for qty in dimensionless:
            self.assertNotEqual(qty["unit"], "")

    def test_units_parse_with_pint(self) -> None:
        import pint

        ureg = pint.UnitRegistry()
        for claim in self.claims:
            for qty in claim["quantities"]:
                if qty["unit"] == "dimensionless":
                    continue
                with self.subTest(claim=claim["claim_id"], unit=qty["unit"]):
                    ureg.Unit(qty["unit"])  # raises if unparseable

    def test_original_value_and_unit_are_preserved(self) -> None:
        for claim in self.claims:
            for qty in claim["quantities"]:
                with self.subTest(claim=claim["claim_id"], role=qty["role"]):
                    self.assertTrue(qty["original_value"])
                    self.assertTrue(qty["original_unit"])

    def test_derived_values_record_their_conversion_method(self) -> None:
        """10/3 evaluated to a decimal must say so; silent conversion is prohibited."""
        target = next(c for c in self.claims if c["claim_id"] == "shigley10-c-0074")
        roller = next(q for q in target["quantities"] if "roller" in q["role"])
        self.assertEqual(roller["original_value"], "10/3")
        self.assertIsNotNone(roller["conversion_method"])
        self.assertAlmostEqual(roller["value"], 10 / 3, places=6)

    def test_missing_unit_is_rejected_by_the_builder(self) -> None:
        import build_claims

        with self.assertRaises(build_claims.ClaimBuildError):
            build_claims.check_unit(None, "test-c", "role")
        with self.assertRaises(build_claims.ClaimBuildError):
            build_claims.check_unit("", "test-c", "role")
        self.assertEqual(build_claims.check_unit("dimensionless", "test-c", "role"), "dimensionless")

    def test_rdf_quantities_all_carry_a_unit_symbol(self) -> None:
        quantities = list(self.graph.subjects(RDF.type, MDCORE.QuantityValue))
        self.assertGreater(len(quantities), 0)
        for q in quantities:
            with self.subTest(quantity=str(q)):
                self.assertIsNotNone(self.graph.value(q, MDCORE.unitSymbol))
                self.assertIsNotNone(self.graph.value(q, MDCORE.valueProvenance))


# ---------------------------------------------------------------------------
# 5. Substitution constraints
# ---------------------------------------------------------------------------


class TestSubstitutionConstraints(MdkgTestBase):

    def assessments(self) -> List[URIRef]:
        return sorted(self.graph.subjects(RDF.type, MDCORE.SubstitutionAssessment), key=str)

    def test_every_assessment_has_the_four_mandatory_arguments(self) -> None:
        for a in self.assessments():
            with self.subTest(assessment=str(a)):
                self.assertIsNotNone(self.graph.value(a, MDCORE.candidateAlternative))
                self.assertIsNotNone(self.graph.value(a, MDCORE.baselineAlternative))
                self.assertIsNotNone(self.graph.value(a, MDCORE.functionBeingPreserved))
                self.assertIsNotNone(self.graph.value(a, MDCORE.assessmentConclusion))

    def test_every_assessment_names_a_context(self) -> None:
        for a in self.assessments():
            with self.subTest(assessment=str(a)):
                self.assertIsNotNone(self.graph.value(a, MDCORE.assessmentContext))

    def test_conditional_verdicts_carry_conditions_or_modifications(self) -> None:
        conditional = list(
            self.graph.subjects(MDCORE.assessmentConclusion, MDCORE.ConditionallySubstitutable)
        )
        self.assertGreater(len(conditional), 0, "expected conditional verdicts in the pilot")
        for a in conditional:
            with self.subTest(assessment=str(a)):
                conds = list(self.graph.objects(a, MDCORE.assessmentCondition))
                mods = list(self.graph.objects(a, MDCORE.requiredDesignModification))
                self.assertTrue(conds or mods)

    def test_direct_substitution_requires_identical_interface(self) -> None:
        for a in self.graph.subjects(MDCORE.assessmentConclusion, MDCORE.DirectlySubstitutable):
            with self.subTest(assessment=str(a)):
                self.assertEqual(
                    self.graph.value(a, MDCORE.interfaceCompatibility),
                    MDCORE.InterfaceIdentical,
                )
                self.assertEqual(list(self.graph.objects(a, MDCORE.requiredDesignModification)), [])

    def test_substitution_is_not_symmetric(self) -> None:
        """SA-001 and SA-006 are the same pair, same context, opposite verdicts."""
        forward = MDKG["SA-001"]
        reverse = MDKG["SA-006"]
        self.assertEqual(
            self.graph.value(forward, MDCORE.candidateAlternative),
            self.graph.value(reverse, MDCORE.baselineAlternative),
        )
        self.assertEqual(
            self.graph.value(forward, MDCORE.baselineAlternative),
            self.graph.value(reverse, MDCORE.candidateAlternative),
        )
        self.assertEqual(
            self.graph.value(forward, MDCORE.assessmentContext),
            self.graph.value(reverse, MDCORE.assessmentContext),
        )
        self.assertNotEqual(
            self.graph.value(forward, MDCORE.assessmentConclusion),
            self.graph.value(reverse, MDCORE.assessmentConclusion),
        )

    def test_no_substitution_edge_without_a_backing_assessment(self) -> None:
        assessed = {
            (self.graph.value(a, MDCORE.candidateAlternative),
             self.graph.value(a, MDCORE.baselineAlternative))
            for a in self.assessments()
        }
        for cand, base in self.graph.subject_objects(MDCORE.substitutionAssessedAs):
            with self.subTest(edge=f"{cand} -> {base}"):
                self.assertIn((cand, base), assessed)

    def test_shortcut_edges_are_not_mirrored(self) -> None:
        edges = set(self.graph.subject_objects(MDCORE.substitutionAssessedAs))
        assessed = {
            (self.graph.value(a, MDCORE.candidateAlternative),
             self.graph.value(a, MDCORE.baselineAlternative))
            for a in self.assessments()
        }
        for cand, base in edges:
            if (base, cand) in edges:
                with self.subTest(pair=f"{cand} <-> {base}"):
                    self.assertIn((base, cand), assessed,
                                  "mirrored edge exists without its own assessment")

    def test_substitution_property_is_not_declared_symmetric_or_transitive(self) -> None:
        from rdflib.namespace import OWL

        prop = MDCORE.substitutionAssessedAs
        self.assertNotIn((prop, RDF.type, OWL.SymmetricProperty), self.graph)
        self.assertNotIn((prop, RDF.type, OWL.TransitiveProperty), self.graph)

    def test_shared_function_is_symmetric_but_substitution_is_not(self) -> None:
        from rdflib.namespace import OWL

        self.assertIn((MDCORE.sharesFunctionWith, RDF.type, OWL.SymmetricProperty), self.graph)

    def test_no_transitive_closure_was_materialised(self) -> None:
        out: Dict[URIRef, set] = {}
        for s, o in self.graph.subject_objects(MDCORE.substitutionAssessedAs):
            out.setdefault(s, set()).add(o)
        assessed = {
            (self.graph.value(a, MDCORE.candidateAlternative),
             self.graph.value(a, MDCORE.baselineAlternative))
            for a in self.assessments()
        }
        for a, bs in out.items():
            for b in bs:
                for c in out.get(b, set()):
                    if c != a and c in out.get(a, set()):
                        self.assertIn((a, c), assessed,
                                      f"transitive edge {a} -> {c} not independently assessed")

    def test_preferred_verdict_names_its_requirement_set(self) -> None:
        for a in self.graph.subjects(MDCORE.assessmentConclusion, MDCORE.PreferredAlternative):
            with self.subTest(assessment=str(a)):
                self.assertTrue(list(self.graph.objects(a, MDCORE.applicableRequirement)))
                self.assertTrue(list(self.graph.objects(a, MDCORE.satisfiedRequirement)))

    def test_evaluations_declare_value_provenance(self) -> None:
        evaluations = list(self.graph.subjects(RDF.type, MDCORE.AlternativeEvaluation))
        self.assertGreater(len(evaluations), 0)
        for e in evaluations:
            with self.subTest(evaluation=str(e)):
                self.assertIsNotNone(self.graph.value(e, MDCORE.valueProvenance))
                self.assertIsNotNone(self.graph.value(e, MDCORE.applicableContext))


# ---------------------------------------------------------------------------
# 6. Cross-book alignment
# ---------------------------------------------------------------------------


class TestCrossBookAlignment(MdkgTestBase):

    def test_alignments_relate_claims_from_different_documents(self) -> None:
        by_iri = {}
        for claim in self.graph.subjects(RDF.type, EV.NormalizedClaim):
            doc = self.graph.value(claim, EV.fromSourceDocument)
            by_iri[claim] = doc
        alignments = list(self.graph.subjects(RDF.type, EV.ClaimAlignment))
        self.assertGreater(len(alignments), 0)
        for al in alignments:
            a = self.graph.value(al, EV.sourceClaimA)
            b = self.graph.value(al, EV.sourceClaimB)
            with self.subTest(alignment=str(al)):
                self.assertIsNotNone(a)
                self.assertIsNotNone(b)
                self.assertNotEqual(
                    by_iri.get(a), by_iri.get(b),
                    "a cross-book alignment must join claims from two different documents",
                )

    def test_conflicting_claims_are_both_retained(self) -> None:
        for prop in (EV.contradicts, EV.differsFrom, EV.unresolvedRelativeTo):
            for a, b in self.graph.subject_objects(prop):
                with self.subTest(relation=str(prop), a=str(a), b=str(b)):
                    self.assertIsNotNone(self.graph.value(a, EV.normalizedStatement))
                    self.assertIsNotNone(self.graph.value(b, EV.normalizedStatement))
                    self.assertNotEqual(a, b)

    def test_no_owl_sameas_between_source_claims(self) -> None:
        """Claims from two books are never merged into one node."""
        from rdflib.namespace import OWL

        for a, b in self.graph.subject_objects(OWL.sameAs):
            if (a, RDF.type, EV.NormalizedClaim) in self.graph:
                self.fail(f"claim {a} merged with {b} via owl:sameAs")

    def test_symbols_from_the_two_books_are_not_merged(self) -> None:
        """Mott's k and Shigley's a mean the same exponent but stay distinct."""
        rows = list(
            self.graph.query(
                """
                PREFIX ev: <https://w3id.org/mdkg/evidence#>
                SELECT ?symbol WHERE {
                    ?al a ev:TerminologyAlignment ;
                        ev:commonConcept ?c ;
                        ev:alignsSourceSymbol ?symbol .
                    FILTER(CONTAINS(STR(?c), "load/life exponent"))
                }
                """
            )
        )
        symbols = sorted(str(r[0]) for r in rows)
        self.assertEqual(symbols, ["mott6: k", "shigley10: a"])

    def test_the_unresolved_disagreement_is_preserved(self) -> None:
        """Mott's N=3 for keys vs Shigley's 'avoid excessive safety factors'."""
        mott = URIRef("https://w3id.org/mdkg/source/mott6#c-0063")
        shigley = URIRef("https://w3id.org/mdkg/source/shigley10#c-0024")
        self.assertIn((mott, EV.unresolvedRelativeTo, shigley), self.graph)
        self.assertIsNotNone(self.graph.value(mott, EV.normalizedStatement))
        self.assertIsNotNone(self.graph.value(shigley, EV.normalizedStatement))

    def test_terminology_csv_matches_the_graph(self) -> None:
        import csv

        path = DATA / "terminology_alignment.csv"
        self.assertTrue(path.exists())
        with path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreater(len(rows), 0)
        graph_count = len(set(self.graph.subjects(RDF.type, EV.TerminologyAlignment)))
        self.assertEqual(len(rows), graph_count)

    def test_alignment_types_come_from_the_controlled_scheme(self) -> None:
        for al in self.graph.subjects(RDF.type, EV.ClaimAlignment):
            atype = self.graph.value(al, EV.alignmentType)
            with self.subTest(alignment=str(al)):
                self.assertIsNotNone(atype)
                self.assertIn((atype, RDF.type, EV.AlignmentType), self.graph)


# ---------------------------------------------------------------------------
# 7. Negative control -- prove the validation actually fires
# ---------------------------------------------------------------------------


class TestValidationNegativeControl(MdkgTestBase):
    """Inject deliberate defects and assert SHACL rejects each one."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        shapes_path = REPO_ROOT / "shapes" / "ontology-shapes.ttl"
        if not shapes_path.exists():
            raise unittest.SkipTest("run scripts/validate_ontology.py first to bundle the shapes")
        cls.shapes = Graph()
        cls.shapes.parse(shapes_path, format="turtle")

    def _validate(self, graph: Graph) -> bool:
        from pyshacl import validate

        conforms, _, _ = validate(graph, shacl_graph=self.shapes, advanced=True, inference="none")
        return bool(conforms)

    def test_the_clean_graph_conforms(self) -> None:
        self.assertTrue(self._validate(self.graph), "the built graph should conform")

    def _mutated(self) -> Graph:
        g = Graph()
        g += self.graph
        return g

    def test_conditional_verdict_without_conditions_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#bad")
        g.add((bad, RDF.type, MDCORE.SubstitutionAssessment))
        g.add((bad, MDCORE.candidateAlternative, MELEM.ParallelKeyConnection))
        g.add((bad, MDCORE.baselineAlternative, MELEM.InvoluteSplineConnection))
        g.add((bad, MDCORE.functionBeingPreserved, MECH.TransmitTorqueShaftToHub))
        g.add((bad, MDCORE.assessmentContext, MDKG["ctx-steady-fixed-hub"]))
        g.add((bad, MDCORE.assessmentConclusion, MDCORE.ConditionallySubstitutable))
        g.add((bad, MDCORE.reviewStatus, MDCORE.NeedsReview))
        self.assertFalse(self._validate(g))

    def test_direct_substitution_with_a_modification_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#bad2")
        g.add((bad, RDF.type, MDCORE.SubstitutionAssessment))
        g.add((bad, MDCORE.candidateAlternative, MELEM.ParallelKeyConnection))
        g.add((bad, MDCORE.baselineAlternative, MELEM.InvoluteSplineConnection))
        g.add((bad, MDCORE.functionBeingPreserved, MECH.TransmitTorqueShaftToHub))
        g.add((bad, MDCORE.assessmentContext, MDKG["ctx-steady-fixed-hub"]))
        g.add((bad, MDCORE.assessmentConclusion, MDCORE.DirectlySubstitutable))
        g.add((bad, MDCORE.reviewStatus, MDCORE.NeedsReview))
        g.add((bad, MDCORE.requiredDesignModification, URIRef("http://example.org/test#mod")))
        self.assertFalse(self._validate(g))

    def test_quantity_without_a_unit_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#qty")
        g.add((bad, RDF.type, MDCORE.QuantityValue))
        g.add((bad, MDCORE.numericValue, Literal(3.0, datatype=XSD.decimal)))
        g.add((bad, MDCORE.originalValue, Literal("3")))
        self.assertFalse(self._validate(g))

    def test_claim_without_evidence_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#claim")
        g.add((bad, RDF.type, EV.NormalizedClaim))
        g.add((bad, EV.normalizedStatement, Literal("unevidenced", lang="en")))
        g.add((bad, MDCORE.reviewStatus, MDCORE.NeedsReview))
        self.assertFalse(self._validate(g))

    def test_page_without_a_pdf_index_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#page")
        g.add((bad, RDF.type, EV.Page))
        g.add((bad, EV.printedPage, Literal("42")))
        self.assertFalse(self._validate(g))

    def test_human_verified_without_a_reviewer_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#rule")
        g.add((bad, RDF.type, MDCORE.SelectionRule))
        g.add((bad, MDCORE.ruleIdentifier, Literal("TEST-001")))
        g.add((bad, MDCORE.ruleStatement, Literal("x", lang="en")))
        g.add((bad, MDCORE.contextUnspecified, Literal(True, datatype=XSD.boolean)))
        g.add((bad, MDCORE.ruleIsAnalystAuthored, Literal(True, datatype=XSD.boolean)))
        g.add((bad, MDCORE.reviewStatus, MDCORE.HumanVerified))
        self.assertFalse(self._validate(g))

    def test_rule_with_neither_claim_nor_authorship_is_rejected(self) -> None:
        g = self._mutated()
        bad = URIRef("http://example.org/test#rule2")
        g.add((bad, RDF.type, MDCORE.SelectionRule))
        g.add((bad, MDCORE.ruleIdentifier, Literal("TEST-002")))
        g.add((bad, MDCORE.ruleStatement, Literal("x", lang="en")))
        g.add((bad, MDCORE.contextUnspecified, Literal(True, datatype=XSD.boolean)))
        g.add((bad, MDCORE.reviewStatus, MDCORE.NeedsReview))
        self.assertFalse(self._validate(g))


# ---------------------------------------------------------------------------
# 8. Text-integrity discipline
# ---------------------------------------------------------------------------


class TestTextIntegrity(MdkgTestBase):

    def test_every_span_declares_a_text_integrity_verdict(self) -> None:
        allowed = {"reliable", "partial-glyph-loss", "glyph-mismapped", "unverified"}
        for span in self.spans:
            with self.subTest(span=span["span_id"]):
                self.assertIn(span["text_integrity"], allowed)

    def test_shigley_math_spans_are_flagged_not_trusted(self) -> None:
        """The Shigley PDF mis-maps math glyphs; such spans must be flagged."""
        flagged = [
            s for s in self.spans
            if s["doc_id"] == "shigley10" and s["text_integrity"] == "glyph-mismapped"
        ]
        self.assertGreater(len(flagged), 0, "expected at least one flagged math span")
        for span in flagged:
            with self.subTest(span=span["span_id"]):
                self.assertGreater(span["math_font_char_ratio"], 0.005)

    def test_equations_from_flagged_spans_were_transcribed_visually(self) -> None:
        """Any equation claim resting on unreliable text must say where it came from."""
        for claim in self.claims:
            if claim["text_integrity"] == "glyph-mismapped" and claim.get("equations"):
                with self.subTest(claim=claim["claim_id"]):
                    self.assertIsNotNone(
                        claim.get("equation_transcription"),
                        "equation claim on mis-mapped text without a transcription source",
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
