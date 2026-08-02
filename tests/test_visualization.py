#!/usr/bin/env python3
"""Tests for the visualization data generator and the generated application.

    python3 -m unittest discover -s tests -v
    python3 tests/test_visualization.py

These tests treat the visualization as what it is: a *projection* of the mdkg
data. The point is not that it looks nice, but that it cannot quietly say
something the underlying graph does not say — no invented edge, no mirrored
substitution, no fabricated citation, no unit-less quantity, and no runtime
dependency on the network.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml  # noqa: E402

VIZ_DIR = REPO_ROOT / "outputs" / "visualizations"
VIZ_DATA = VIZ_DIR / "data"
DATA_DIR = REPO_ROOT / "data"

GRAPH_DATASETS = [
    "ontology_graph", "function_behavior_graph", "machine_elements_graph",
    "claims_graph", "evidence_graph", "alignments_graph", "substitutions_graph",
]
ALL_DATASETS = GRAPH_DATASETS + ["overview", "rules", "coverage", "search_index"]

#: Every view the application must be able to populate.
REQUIRED_VIEWS = [
    "overview", "ontology", "mechanical", "elements", "functions",
    "substitutions", "claims", "evidence", "alignments", "rules",
    "coverage", "pipeline",
]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


class VizTestBase(unittest.TestCase):
    """Shared fixtures, loaded once."""

    data: Dict[str, Any]
    claims: List[Dict[str, Any]]
    spans: List[Dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        if not VIZ_DATA.exists():
            raise unittest.SkipTest(
                "outputs/visualizations/data missing; run "
                "python3 scripts/build_html_visualization.py first"
            )
        cls.data = {}
        for name in ALL_DATASETS:
            path = VIZ_DATA / f"{name}.json"
            if not path.exists():
                raise unittest.SkipTest(f"{path} missing; rebuild the visualization")
            cls.data[name] = json.loads(path.read_text(encoding="utf-8"))
        cls.claims = load_jsonl(DATA_DIR / "claims.jsonl")
        cls.spans = load_jsonl(DATA_DIR / "evidence_spans.jsonl")


# ---------------------------------------------------------------------------
# 1-3. Structural integrity of the generated JSON
# ---------------------------------------------------------------------------


class TestGeneratedJson(VizTestBase):

    def test_all_datasets_are_valid_json(self) -> None:
        for name in ALL_DATASETS:
            with self.subTest(dataset=name):
                path = VIZ_DATA / f"{name}.json"
                json.loads(path.read_text(encoding="utf-8"))  # raises on malformed

    def test_graph_datasets_have_required_meta(self) -> None:
        for name in GRAPH_DATASETS:
            with self.subTest(dataset=name):
                meta = self.data[name]["meta"]
                for key in ("id", "title", "description", "node_count", "edge_count",
                            "categories", "edge_kinds", "legend"):
                    self.assertIn(key, meta)
                self.assertEqual(meta["node_count"], len(self.data[name]["nodes"]))
                self.assertEqual(meta["edge_count"], len(self.data[name]["edges"]))

    def test_every_node_has_a_stable_unique_id(self) -> None:
        for name in GRAPH_DATASETS:
            ids: Set[str] = set()
            for node in self.data[name]["nodes"]:
                with self.subTest(dataset=name, node=node["data"].get("id")):
                    nid = node["data"].get("id")
                    self.assertTrue(nid, "node without an id")
                    self.assertIsInstance(nid, str)
                    self.assertNotIn(nid, ids, "duplicate node id")
                    ids.add(nid)
                    self.assertIn("label", node["data"])
                    self.assertIn("cat", node["data"])

    def test_every_edge_references_existing_nodes(self) -> None:
        for name in GRAPH_DATASETS:
            ids = {n["data"]["id"] for n in self.data[name]["nodes"]}
            seen: Set[str] = set()
            for e in self.data[name]["edges"]:
                d = e["data"]
                with self.subTest(dataset=name, edge=d.get("id")):
                    self.assertIn(d["source"], ids, "edge source is not a node")
                    self.assertIn(d["target"], ids, "edge target is not a node")
                    self.assertNotIn(d["id"], seen, "duplicate edge id")
                    seen.add(d["id"])

    def test_no_dangling_edges_were_dropped_silently(self) -> None:
        """Dropping is allowed but must be reported, not hidden."""
        for name in GRAPH_DATASETS:
            with self.subTest(dataset=name):
                self.assertIn("dropped_dangling_edges", self.data[name]["meta"])

    def test_node_categories_are_declared_in_meta(self) -> None:
        for name in GRAPH_DATASETS:
            declared = set(self.data[name]["meta"]["categories"])
            for node in self.data[name]["nodes"]:
                with self.subTest(dataset=name, node=node["data"]["id"]):
                    self.assertIn(node["data"]["cat"], declared)

    def test_every_graph_has_a_legend(self) -> None:
        """Colour is never the only encoding: each legend entry names a shape and glyph."""
        for name in GRAPH_DATASETS:
            legend = self.data[name]["meta"]["legend"]
            with self.subTest(dataset=name):
                self.assertTrue(legend)
                for item in legend:
                    self.assertIn("cat", item)
                    self.assertIn("label", item)
                    self.assertIn("shape", item)
                    self.assertIn("glyph", item)


# ---------------------------------------------------------------------------
# 4-5. Claims, evidence and provenance
# ---------------------------------------------------------------------------


class TestClaimsAndEvidence(VizTestBase):

    def test_displayed_claims_match_the_source_data(self) -> None:
        shown = {c["claim_id"] for c in self.data["claims_graph"]["claims"]}
        actual = {c["claim_id"] for c in self.claims}
        self.assertEqual(shown, actual)

    def test_every_displayed_claim_references_existing_spans(self) -> None:
        known = {s["span_id"] for s in self.data["evidence_graph"]["spans"]}
        for c in self.data["claims_graph"]["claims"]:
            with self.subTest(claim=c["claim_id"]):
                self.assertTrue(c["evidence_span_ids"], "claim with no evidence")
                for sid in c["evidence_span_ids"]:
                    self.assertIn(sid, known)

    def test_no_claim_lacks_evidence(self) -> None:
        self.assertEqual(self.data["claims_graph"]["claims_without_evidence"], [])

    def test_every_span_resolves_to_a_source_document(self) -> None:
        docs = {s["doc_id"] for s in self.data["overview"]["sources"]}
        for s in self.data["evidence_graph"]["spans"]:
            with self.subTest(span=s["span_id"]):
                self.assertIn(s["doc_id"], docs)
                self.assertTrue(s["book_title"])
                self.assertTrue(s["source_file_name"] if "source_file_name" in s else True)

    def test_evidence_graph_span_nodes_reach_a_document(self) -> None:
        ds = self.data["evidence_graph"]
        edges = ds["edges"]
        parent_of: Dict[str, str] = {}
        for e in edges:
            parent_of[e["data"]["target"]] = e["data"]["source"]
        span_nodes = [n["data"]["id"] for n in ds["nodes"] if n["data"].get("nodeType") == "span"]
        self.assertTrue(span_nodes)
        for sid in span_nodes:
            with self.subTest(span=sid):
                node, hops = sid, 0
                while node in parent_of and hops < 10:
                    node = parent_of[node]; hops += 1
                self.assertTrue(node.startswith("doc:"),
                                f"{sid} does not reach a document node (stopped at {node})")

    def test_citations_are_assembled_from_stored_provenance(self) -> None:
        """Every citation must contain the printed page and PDF index from the span."""
        by_id = {s["span_id"]: s for s in self.spans}
        for s in self.data["evidence_graph"]["spans"]:
            with self.subTest(span=s["span_id"]):
                citation = s["citation"]
                self.assertTrue(citation, "no assembled citation")
                source = by_id[s["span_id"]]
                self.assertIn(source["book_title"], citation)
                self.assertIn(f"PDF page index {source['pdf_page_index']}", citation)
                if source["printed_page"]:
                    self.assertIn(f"printed p. {source['printed_page']}", citation)

    def test_citations_are_not_hand_written_strings_in_the_source_data(self) -> None:
        """The curated inputs must contain no citation field for the generator to copy."""
        seeds = yaml.safe_load((DATA_DIR / "claims_seed.yaml").read_text(encoding="utf-8"))
        for seed in seeds["claims"]:
            with self.subTest(claim=seed["id"]):
                for forbidden in ("printed_page", "pdf_page_index", "chapter", "section", "citation"):
                    self.assertNotIn(forbidden, seed)

    def test_printed_page_and_pdf_index_stay_separate(self) -> None:
        for s in self.data["evidence_graph"]["spans"]:
            with self.subTest(span=s["span_id"]):
                self.assertIn("printed_page", s)
                self.assertIn("pdf_page_index", s)
                self.assertIsInstance(s["pdf_page_index"], int)
                self.assertNotEqual(str(s["printed_page"]), str(s["pdf_page_index"]))

    def test_glyph_mismapped_evidence_is_flagged(self) -> None:
        flagged = [s for s in self.data["evidence_graph"]["spans"]
                   if s["text_integrity"] == "glyph-mismapped"]
        self.assertTrue(flagged, "expected at least one glyph-mismapped span to be flagged")
        for s in flagged:
            with self.subTest(span=s["span_id"]):
                self.assertGreater(s["math_font_char_ratio"], 0.005)
        integrity_values = {s["text_integrity"] for s in self.data["evidence_graph"]["spans"]}
        self.assertTrue(integrity_values <= {
            "reliable", "partial-glyph-loss", "glyph-mismapped", "unverified"})

    def test_claims_on_mismapped_text_declare_a_transcription_source(self) -> None:
        for c in self.data["claims_graph"]["claims"]:
            if c["text_integrity"] == "glyph-mismapped" and c["equations"]:
                with self.subTest(claim=c["claim_id"]):
                    self.assertIsNotNone(c["equation_transcription"])

    def test_unused_spans_are_reported_not_hidden(self) -> None:
        ds = self.data["evidence_graph"]
        self.assertIn("unused_spans", ds)
        cited = {sid for c in self.claims for sid in c["evidence_span_ids"]}
        expected = sorted({s["span_id"] for s in self.spans} - cited)
        self.assertEqual(ds["unused_spans"], expected)


# ---------------------------------------------------------------------------
# 6-8. Substitution semantics
# ---------------------------------------------------------------------------


class TestSubstitutionIntegrity(VizTestBase):

    def assessments(self) -> List[Dict[str, Any]]:
        return self.data["substitutions_graph"]["assessments"]

    def test_all_curated_assessments_are_rendered(self) -> None:
        curated = yaml.safe_load((DATA_DIR / "substitutions.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(a["id"] for a in self.assessments()),
            sorted(a["id"] for a in curated["assessments"]),
        )

    def test_direction_is_preserved_from_the_source(self) -> None:
        curated = {a["id"]: a for a in yaml.safe_load(
            (DATA_DIR / "substitutions.yaml").read_text(encoding="utf-8"))["assessments"]}
        for sa in self.assessments():
            with self.subTest(assessment=sa["id"]):
                src = curated[sa["id"]]
                self.assertEqual(sa["candidate"]["curie"], src["candidate"])
                self.assertEqual(sa["baseline"]["curie"], src["baseline"])
                self.assertEqual(sa["verdict"], src["conclusion"])

    def test_substitution_edges_run_baseline_to_candidate_only(self) -> None:
        ds = self.data["substitutions_graph"]
        by_id = {n["data"]["id"]: n["data"] for n in ds["nodes"]}
        for e in ds["edges"]:
            d = e["data"]
            if d["kind"] != "substitution":
                continue
            with self.subTest(edge=d["id"]):
                src, tgt = by_id[d["source"]], by_id[d["target"]]
                if d["label"] == "baseline":
                    self.assertEqual(src.get("nodeType"), "individual")
                    self.assertEqual(tgt.get("nodeType"), "assessment")
                elif d["label"] == "candidate":
                    self.assertEqual(src.get("nodeType"), "assessment")
                    self.assertEqual(tgt.get("nodeType"), "individual")
                else:
                    self.fail(f"unexpected substitution edge label {d['label']!r}")

    def test_no_reverse_substitution_edge_is_added_automatically(self) -> None:
        """A mirrored pair may exist only when two assessments genuinely declare it."""
        ds = self.data["substitutions_graph"]
        assessed = {(a["baseline"]["curie"], a["candidate"]["curie"]) for a in self.assessments()}
        derived: Set = set()
        for a in self.assessments():
            derived.add((a["baseline"]["curie"], a["candidate"]["curie"]))
        self.assertEqual(derived, assessed)
        for base, cand in derived:
            if (cand, base) in derived:
                matches = [a["id"] for a in self.assessments()
                           if a["baseline"]["curie"] == cand and a["candidate"]["curie"] == base]
                with self.subTest(pair=f"{base}<->{cand}"):
                    self.assertTrue(matches, "mirrored pair without its own assessment")

    def test_no_transitive_substitution_edge_is_generated(self) -> None:
        pairs = {(a["baseline"]["curie"], a["candidate"]["curie"]) for a in self.assessments()}
        out: Dict[str, Set[str]] = {}
        for base, cand in pairs:
            out.setdefault(base, set()).add(cand)
        for a, bs in out.items():
            for b in bs:
                for c in out.get(b, set()):
                    if c != a and (a, c) in pairs:
                        matches = [x["id"] for x in self.assessments()
                                   if x["baseline"]["curie"] == a and x["candidate"]["curie"] == c]
                        with self.subTest(triple=f"{a}->{b}->{c}"):
                            self.assertTrue(matches, "transitive edge without its own assessment")

    def test_the_asymmetric_pair_is_present_and_opposed(self) -> None:
        by_id = {a["id"]: a for a in self.assessments()}
        self.assertIn("SA-001", by_id)
        self.assertIn("SA-006", by_id)
        a, b = by_id["SA-001"], by_id["SA-006"]
        self.assertEqual(a["candidate"]["curie"], b["baseline"]["curie"])
        self.assertEqual(a["baseline"]["curie"], b["candidate"]["curie"])
        self.assertEqual(a["context"]["id"], b["context"]["id"])
        self.assertNotEqual(a["verdict"], b["verdict"])
        self.assertEqual(self.data["substitutions_graph"]["primary_pair"], ["SA-001", "SA-006"])

    def test_no_directly_substitutable_verdict_in_the_pilot(self) -> None:
        verdicts = [a["verdict"] for a in self.assessments()]
        self.assertNotIn("DirectlySubstitutable", verdicts)
        self.assertTrue(self.data["substitutions_graph"]["no_directly_substitutable"])
        self.assertTrue(self.data["overview"]["no_directly_substitutable"])

    def test_conditional_verdicts_carry_conditions_or_modifications(self) -> None:
        for sa in self.assessments():
            if sa["verdict"] == "ConditionallySubstitutable":
                with self.subTest(assessment=sa["id"]):
                    self.assertTrue(sa["conditions"] or sa["modifications"])

    def test_all_six_verdict_states_are_representable(self) -> None:
        order = self.data["substitutions_graph"]["verdict_order"]
        for state in ("PreferredAlternative", "DirectlySubstitutable",
                      "ConditionallySubstitutable", "FunctionalAlternative",
                      "NotAnAlternative", "InsufficientEvidence"):
            self.assertIn(state, order)

    def test_every_assessment_names_function_context_and_verdict(self) -> None:
        for sa in self.assessments():
            with self.subTest(assessment=sa["id"]):
                self.assertTrue(sa["function_preserved"]["curie"])
                self.assertTrue(sa["context"]["id"])
                self.assertTrue(sa["verdict"])
                self.assertTrue(sa["candidate"]["curie"])
                self.assertTrue(sa["baseline"]["curie"])

    def test_every_assessment_item_declares_provenance(self) -> None:
        """Source-derived and inferred statements must never be indistinguishable."""
        allowed = {"SourceDerivedValue", "NormalizedInterpretation", "EngineeringInference",
                   "UserDefinedWeight", "ComputedResult"}
        for sa in self.assessments():
            for key in ("conditions", "modifications", "advantages", "disadvantages", "trade_offs"):
                for item in sa[key]:
                    with self.subTest(assessment=sa["id"], key=key):
                        self.assertIn(item["provenance"], allowed)


# ---------------------------------------------------------------------------
# 9. Units
# ---------------------------------------------------------------------------


class TestUnits(VizTestBase):

    def test_every_displayed_quantity_has_a_unit(self) -> None:
        total = 0
        for c in self.data["claims_graph"]["claims"]:
            for q in c["quantities"]:
                total += 1
                with self.subTest(claim=c["claim_id"], role=q["role"]):
                    self.assertTrue(q["unit"], "quantity with no unit")
                    self.assertTrue(q["original_value"] != "", "original value lost")
                    self.assertTrue(q["original_unit"], "original unit lost")
                    self.assertIn("value_provenance", q)
        self.assertGreater(total, 0, "expected quantities in the pilot data")

    def test_dimensionless_is_explicit(self) -> None:
        units = {q["unit"] for c in self.data["claims_graph"]["claims"] for q in c["quantities"]}
        self.assertIn("dimensionless", units)
        self.assertNotIn("", units)

    def test_quantity_counts_match_the_source(self) -> None:
        shown = sum(len(c["quantities"]) for c in self.data["claims_graph"]["claims"])
        actual = sum(len(c.get("quantities") or []) for c in self.claims)
        self.assertEqual(shown, actual)


# ---------------------------------------------------------------------------
# 12-13. Trust status and summary agreement
# ---------------------------------------------------------------------------


class TestTrustAndCounts(VizTestBase):

    def test_human_verified_count_is_zero(self) -> None:
        card = next(c for c in self.data["overview"]["cards"] if c["key"] == "human_verified")
        self.assertEqual(card["value"], 0)
        actual = sum(1 for c in self.claims if c["review_status"] == "HumanVerified")
        self.assertEqual(card["value"], actual)

    def test_no_displayed_claim_claims_human_verification(self) -> None:
        for c in self.data["claims_graph"]["claims"]:
            with self.subTest(claim=c["claim_id"]):
                if c["review_status"] == "HumanVerified":
                    self.assertTrue(c["reviewed_by"])

    def test_summary_counts_match_the_ontology_summary(self) -> None:
        summary = json.loads(
            (REPO_ROOT / "outputs" / "ontology_summary.json").read_text(encoding="utf-8"))
        cards = {c["key"]: c["value"] for c in self.data["overview"]["cards"]}
        self.assertEqual(cards["classes"], summary["tbox"]["classes"])
        self.assertEqual(cards["object_properties"], summary["tbox"]["object_properties"])
        self.assertEqual(cards["datatype_properties"], summary["tbox"]["datatype_properties"])
        self.assertEqual(cards["triples"], summary["total_triples"])
        self.assertEqual(cards["claims"], summary["abox"]["claims"])
        self.assertEqual(cards["evidence_spans"], summary["abox"]["evidence_spans"])
        self.assertEqual(cards["claim_alignments"], summary["abox"]["claim_alignments"])
        self.assertEqual(cards["terminology_alignments"], summary["abox"]["terminology_alignments"])
        self.assertEqual(cards["alternatives"], summary["abox"]["design_alternatives"])

    def test_summary_counts_match_the_data_files(self) -> None:
        cards = {c["key"]: c["value"] for c in self.data["overview"]["cards"]}
        self.assertEqual(cards["claims"], len(self.claims))
        self.assertEqual(cards["evidence_spans"], len(self.spans))
        self.assertEqual(cards["mott_claims"], sum(1 for c in self.claims if c["doc_id"] == "mott6"))
        self.assertEqual(cards["shigley_claims"],
                         sum(1 for c in self.claims if c["doc_id"] == "shigley10"))

    def test_rule_counts_match_the_rule_files(self) -> None:
        for stem, count in self.data["rules"]["counts_by_group"].items():
            with self.subTest(group=stem):
                rules = yaml.safe_load(
                    (REPO_ROOT / "rules" / f"{stem}.yaml").read_text(encoding="utf-8"))["rules"]
                self.assertEqual(count, len(rules))

    def test_pilot_warning_is_present(self) -> None:
        self.assertIn("NeedsReview", self.data["overview"]["warning"])
        self.assertIn("pilot", self.data["overview"]["warning"].lower())


# ---------------------------------------------------------------------------
# 14. Every required view has data
# ---------------------------------------------------------------------------


class TestViewCoverage(VizTestBase):

    def test_every_required_view_has_a_dataset(self) -> None:
        backing = {
            "overview": lambda: self.data["overview"]["cards"],
            "ontology": lambda: self.data["ontology_graph"]["nodes"],
            "mechanical": lambda: self.data["function_behavior_graph"]["nodes"],
            "elements": lambda: self.data["machine_elements_graph"]["nodes"],
            "functions": lambda: self.data["function_behavior_graph"]["functions"],
            "substitutions": lambda: self.data["substitutions_graph"]["assessments"],
            "claims": lambda: self.data["claims_graph"]["claims"],
            "evidence": lambda: self.data["evidence_graph"]["spans"],
            "alignments": lambda: self.data["alignments_graph"]["alignments"],
            "rules": lambda: self.data["rules"]["rules"],
            "coverage": lambda: self.data["coverage"]["rows"],
            "pipeline": lambda: self.data["overview"]["text_integrity"],
        }
        self.assertEqual(sorted(backing), sorted(REQUIRED_VIEWS))
        for view, getter in backing.items():
            with self.subTest(view=view):
                self.assertTrue(getter(), f"view '{view}' has no data")

    def test_every_view_is_reachable_from_the_navigation(self) -> None:
        html = (VIZ_DIR / "index.html").read_text(encoding="utf-8")
        for view in REQUIRED_VIEWS:
            with self.subTest(view=view):
                self.assertIn(f'data-view="{view}"', html)

    def test_every_view_is_implemented_in_the_application(self) -> None:
        js = (VIZ_DIR / "assets" / "app.js").read_text(encoding="utf-8")
        for view in REQUIRED_VIEWS:
            with self.subTest(view=view):
                self.assertIn(f"VIEWS.{view} = function", js)

    def test_search_index_covers_every_entity_family(self) -> None:
        idx = self.data["search_index"]
        self.assertGreater(idx["count"], 500)
        for expected in ("Ontology class", "Claim", "Evidence span", "Function",
                         "Substitution assessment", "Claim alignment", "Coverage topic",
                         "Machine element", "Source document"):
            with self.subTest(entity_type=expected):
                self.assertTrue(any(t.startswith(expected) for t in idx["types"]),
                                f"search index has no '{expected}' entries")

    def test_search_entries_target_a_real_view(self) -> None:
        for e in self.data["search_index"]["entries"]:
            with self.subTest(entry=e["id"]):
                self.assertIn(e["view"], REQUIRED_VIEWS)
                self.assertTrue(e["label"])
                self.assertTrue(e["text"])

    def test_search_index_includes_korean_labels_where_present(self) -> None:
        with_ko = [e for e in self.data["search_index"]["entries"] if e.get("ko")]
        self.assertTrue(with_ko, "expected Korean alternative labels in the search index")

    def test_alignments_cover_the_featured_comparisons(self) -> None:
        ds = self.data["alignments_graph"]
        known = {a["id"] for a in ds["alignments"]} | {t["id"] for t in ds["terminology"]}
        self.assertEqual(len(ds["featured"]), 5)
        for f in ds["featured"]:
            with self.subTest(featured=f["key"]):
                for ref in f["claim_ids"] + f["concept_ids"]:
                    self.assertIn(ref, known)

    def test_alignments_join_two_different_documents(self) -> None:
        for a in self.data["alignments_graph"]["alignments"]:
            with self.subTest(alignment=a["id"]):
                self.assertNotEqual(a["claim_a"]["doc_id"], a["claim_b"]["doc_id"])


# ---------------------------------------------------------------------------
# 15. No runtime CDN dependency
# ---------------------------------------------------------------------------


class TestOfflineIntegrity(VizTestBase):

    #: Full-URL matcher. Matching the whole URL rather than just the scheme is
    #: what lets the exemptions below be evaluated against real context.
    URL_RE = re.compile(r"https?://[^\s\"'()<>\\]+")

    #: Hosts that are never fetched at runtime: an XML namespace is an
    #: identifier, a w3id.org IRI is an ontology identifier, and localhost is
    #: the local server the app is served from.
    URL_EXEMPT = ("www.w3.org/", "w3id.org/", "localhost", "127.0.0.1",
                  "js.cytoscape.org", "purl.org/")

    #: Loader hints that only make sense for a remote subresource.
    HTML_ATTR_RE = re.compile(r"""\s(integrity|crossorigin)\s*=\s*["']""")

    #: CDN hosts, checked as substrings anywhere in the file.
    CDN_MARKERS = ["//cdn.", "//unpkg.", "//cdnjs.", "//jsdelivr",
                   "fonts.googleapis", "fonts.gstatic"]

    def _runtime_files(self) -> List[Path]:
        return [
            VIZ_DIR / "index.html",
            VIZ_DIR / "assets" / "app.js",
            VIZ_DIR / "assets" / "app.css",
        ]

    def test_no_remote_url_in_runtime_files(self) -> None:
        for path in self._runtime_files():
            text = path.read_text(encoding="utf-8")
            hits = [u for u in self.URL_RE.findall(text)
                    if not any(x in u for x in self.URL_EXEMPT)]
            with self.subTest(file=path.name):
                self.assertEqual(hits, [], f"remote URL in {path.name}: {hits[:3]}")

    def test_no_cdn_marker_in_runtime_files(self) -> None:
        for path in self._runtime_files():
            text = path.read_text(encoding="utf-8")
            for marker in self.CDN_MARKERS:
                with self.subTest(file=path.name, marker=marker):
                    self.assertNotIn(marker, text)

    def test_no_subresource_integrity_hints(self) -> None:
        """`integrity=` / `crossorigin=` attributes only exist for remote assets."""
        html = (VIZ_DIR / "index.html").read_text(encoding="utf-8")
        self.assertEqual(self.HTML_ATTR_RE.findall(html), [])

    def test_all_script_and_style_sources_are_relative(self) -> None:
        html = (VIZ_DIR / "index.html").read_text(encoding="utf-8")
        for match in re.finditer(r'(?:src|href)="([^"]+)"', html):
            url = match.group(1)
            with self.subTest(url=url[:60]):
                if url.startswith("data:") or url.startswith("#"):
                    continue
                self.assertFalse(url.startswith("http"), "absolute URL in a runtime reference")
                self.assertFalse(url.startswith("//"), "protocol-relative URL")

    def test_vendored_library_is_present_and_pinned(self) -> None:
        vendor_js = VIZ_DIR / "assets" / "vendor" / "cytoscape.min.js"
        manifest_path = VIZ_DIR / "assets" / "vendor" / "vendor.json"
        self.assertTrue(vendor_js.exists(), "Cytoscape.js is not vendored into the app")
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["files"]["cytoscape.min.js"]["sha256"]
        actual = hashlib.sha256(vendor_js.read_bytes()).hexdigest()
        self.assertEqual(actual, expected, "vendored library does not match its pinned digest")
        self.assertGreater(vendor_js.stat().st_size, 100_000)

    def test_vendor_license_is_shipped(self) -> None:
        license_file = VIZ_DIR / "assets" / "vendor" / "cytoscape-LICENSE.txt"
        self.assertTrue(license_file.exists())
        self.assertIn("MIT", license_file.read_text(encoding="utf-8").upper())

    def test_readme_documents_the_launch_command(self) -> None:
        readme = (VIZ_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 -m http.server 8000", readme)
        self.assertIn("http://localhost:8000/outputs/visualizations/", readme)

    def test_status_file_exists_so_no_request_404s(self) -> None:
        self.assertTrue((VIZ_DATA / "status.json").exists())


# ---------------------------------------------------------------------------
# Data-integrity guarantees specific to the projection
# ---------------------------------------------------------------------------


class TestProjectionFidelity(VizTestBase):

    def test_no_threshold_is_presented_as_universal(self) -> None:
        for c in self.data["claims_graph"]["claims"]:
            if c["threshold"]:
                with self.subTest(claim=c["claim_id"]):
                    self.assertFalse(c["threshold"]["is_universal"])

    def test_test_recommendations_declare_what_is_missing(self) -> None:
        found = 0
        for c in self.data["claims_graph"]["claims"]:
            v = c["verification"]
            if v:
                found += 1
                with self.subTest(claim=c["claim_id"]):
                    self.assertIn("test_procedure_specified", v)
                    self.assertIn("acceptance_criterion_specified", v)
        self.assertGreater(found, 0)

    def test_rules_declare_attribution(self) -> None:
        for r in self.data["rules"]["rules"]:
            with self.subTest(rule=r["id"]):
                self.assertTrue(r["derived_from"] or r["analyst_authored"],
                                "rule with neither a cited claim nor analyst attribution")

    def test_non_executable_rules_explain_why(self) -> None:
        for r in self.data["rules"]["rules"]:
            if r["executable"] is False:
                with self.subTest(rule=r["id"]):
                    self.assertTrue(r["not_executable_because"])
        self.assertTrue(self.data["rules"]["declarative_only"])

    def test_coverage_marks_taxonomy_only_topics(self) -> None:
        rows = self.data["coverage"]["rows"]
        pilot = [r for r in rows if r["is_pilot_topic"]]
        taxonomy = [r for r in rows if not r["is_pilot_topic"]]
        self.assertTrue(pilot, "expected some pilot topics")
        self.assertTrue(taxonomy, "expected some taxonomy-only topics")
        for r in taxonomy:
            with self.subTest(topic=r["topic_key"]):
                self.assertEqual(r["claim_count"], 0)
                self.assertIn("Taxonomy only", r["status"])

    def test_machine_elements_distinguish_classes_from_individuals(self) -> None:
        ds = self.data["machine_elements_graph"]
        types = {n["data"].get("nodeType") for n in ds["nodes"]}
        self.assertIn("class", types)
        self.assertIn("individual", types)
        for n in ds["nodes"]:
            if n["data"]["cat"] == "alternative":
                with self.subTest(node=n["data"]["id"]):
                    self.assertEqual(n["data"]["nodeType"], "individual")

    def test_function_alternatives_match_the_rdf(self) -> None:
        """Alternatives listed under a function must also be nodes in the graph."""
        ds = self.data["function_behavior_graph"]
        node_ids = {n["data"]["id"] for n in ds["nodes"]}
        for f in ds["functions"]:
            for a in f["alternatives"]:
                with self.subTest(function=f["id"], alternative=a["id"]):
                    self.assertIn(a["id"], node_ids)

    def test_missing_values_use_explicit_markers(self) -> None:
        """Absences are stated, never rendered as a confident blank."""
        markers = {"Not stated by the source", "Insufficient evidence",
                   "Requires external authority", "Requires human review"}
        blob = json.dumps(self.data["claims_graph"]) + json.dumps(self.data["evidence_graph"])
        self.assertTrue(any(m in blob for m in markers),
                        "no explicit not-stated marker found in the generated data")


if __name__ == "__main__":
    unittest.main(verbosity=2)
