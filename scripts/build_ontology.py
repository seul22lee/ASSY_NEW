#!/usr/bin/env python3
"""Assemble the RDF/OWL outputs from hand-authored TBox modules and curated data.

Inputs
------
``ontology/core/*.ttl``, ``ontology/mechanical-design/*.ttl``,
``ontology/machine-elements/*.ttl``
    Hand-authored TBox.  Never modified by this script.
``data/evidence_spans.jsonl``, ``data/claims.jsonl``
    Verified provenance and claims.
``data/alignments_seed.yaml``, ``data/substitutions.yaml``, ``rules/*.yaml``
    Curated ABox.

Outputs (all regenerated, all carrying a GENERATED banner)
----------------------------------------------------------
``ontology/core.ttl``, ``ontology/evidence.ttl``,
``ontology/mechanical-design.ttl``, ``ontology/machine-elements.ttl``
    Single-file bundles of the corresponding module directories, for tools that
    want one file.
``ontology/mott6-claims.ttl``, ``ontology/shigley10-claims.ttl``
    Per-source claims with their bibliographic structure and evidence spans.
``ontology/alignments.ttl``
    Cross-source concept and claim alignments, plus substitution assessments
    and the rule-layer stubs.
``data/terminology_alignment.csv``
    Flat view of the concept alignments.
``build/mdkg-full.ttl``
    Everything merged, for validation and querying.
``outputs/ontology_summary.json``
    Machine-readable class/property/instance census.

Design note
-----------
Citation strings are never stored.  Chapter, section, printed page and PDF page
travel as separate typed properties on ev:Page and ev:EvidenceSpan, and
``scripts/query_examples.py`` assembles a human-readable citation from them at
read time.  Nothing in this pipeline can emit a page number that was not proven
by ``build_evidence_spans.py``.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

LOG = logging.getLogger("build_ontology")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

MDCORE = Namespace("https://w3id.org/mdkg/core#")
MECH = Namespace("https://w3id.org/mdkg/mechanical-design#")
MELEM = Namespace("https://w3id.org/mdkg/machine-elements#")
EV = Namespace("https://w3id.org/mdkg/evidence#")
ALIGN = Namespace("https://w3id.org/mdkg/alignment#")
MDKG = Namespace("https://w3id.org/mdkg/instances#")
MOTT6 = Namespace("https://w3id.org/mdkg/source/mott6#")
SHIGLEY10 = Namespace("https://w3id.org/mdkg/source/shigley10#")

PREFIXES: Dict[str, Namespace] = {
    "mdcore": MDCORE, "mech": MECH, "melem": MELEM, "ev": EV, "evidence": EV,
    "align": ALIGN, "mdkg": MDKG, "mott6": MOTT6, "shigley10": SHIGLEY10,
    "skos": SKOS, "owl": OWL, "rdfs": RDFS,
}

SOURCE_NS: Dict[str, Namespace] = {"mott6": MOTT6, "shigley10": SHIGLEY10}

BANNER = """# ###########################################################################
# GENERATED FILE -- DO NOT EDIT BY HAND
#
# Produced by scripts/build_ontology.py from:
#   {sources}
#
# Edit the inputs and re-run:  python3 scripts/build_ontology.py
# ###########################################################################
"""

_LOCAL_SAFE = re.compile(r"[^0-9A-Za-z_.\-]")


class BuildError(RuntimeError):
    """Raised when curated data cannot be turned into a consistent graph."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def safe_local(text: str) -> str:
    """Sanitise a string into a legal Turtle local name."""
    cleaned = _LOCAL_SAFE.sub("_", str(text)).strip("_")
    if cleaned and cleaned[0].isdigit():
        cleaned = "n" + cleaned
    return cleaned or "unnamed"


def expand(curie: str) -> URIRef:
    """Expand a ``prefix:local`` CURIE against the project's prefix map."""
    if curie.startswith("http://") or curie.startswith("https://"):
        return URIRef(curie)
    if ":" not in curie:
        raise BuildError(f"not a CURIE and not an IRI: {curie!r}")
    prefix, local = curie.split(":", 1)
    if prefix not in PREFIXES:
        raise BuildError(f"unknown prefix {prefix!r} in {curie!r}")
    return PREFIXES[prefix][local]


def bind_all(graph: Graph) -> Graph:
    """Bind the project's prefixes so serialisations stay readable."""
    for prefix, ns in (
        ("mdcore", MDCORE), ("mech", MECH), ("melem", MELEM), ("ev", EV),
        ("align", ALIGN), ("mdkg", MDKG), ("mott6", MOTT6), ("shigley10", SHIGLEY10),
        ("skos", SKOS), ("owl", OWL), ("dcterms", DCTERMS), ("xsd", XSD),
    ):
        graph.bind(prefix, ns)
    return graph


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def serialize(graph: Graph, path: Path, sources: Sequence[str]) -> int:
    """Serialise *graph* to Turtle with a GENERATED banner. Returns triple count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = graph.serialize(format="turtle")
    banner = BANNER.format(sources="\n#   ".join(sources))
    path.write_text(banner + "\n" + body, encoding="utf-8")
    return len(graph)


# ---------------------------------------------------------------------------
# TBox bundling
# ---------------------------------------------------------------------------


def bundle_modules(module_dir: Path, exclude: Sequence[str] = ()) -> Tuple[Graph, List[str]]:
    """Merge every .ttl in *module_dir* into one graph."""
    graph = bind_all(Graph())
    used: List[str] = []
    for ttl in sorted(module_dir.glob("*.ttl")):
        if ttl.name in exclude:
            continue
        graph.parse(ttl, format="turtle")
        used.append(str(ttl.relative_to(REPO_ROOT)))
    return graph, used


# ---------------------------------------------------------------------------
# Evidence + claims
# ---------------------------------------------------------------------------


class SourceGraphBuilder:
    """Build the claims/evidence graph for one source document."""

    def __init__(self, doc_id: str, source_cfg: Dict[str, Any], meta: Dict[str, Any]) -> None:
        self.doc_id = doc_id
        self.cfg = source_cfg
        self.meta = meta
        self.ns = SOURCE_NS[doc_id]
        self.g = bind_all(Graph())
        self._pages: Set[int] = set()
        self._chapters: Set[str] = set()
        self._sections: Set[str] = set()
        self._artifacts: Set[Tuple[str, str]] = set()

    # -- IRIs --------------------------------------------------------------
    def doc_iri(self) -> URIRef:
        return self.ns["document"]

    def edition_iri(self) -> URIRef:
        return self.ns["edition"]

    def book_iri(self) -> URIRef:
        return self.ns["book"]

    def page_iri(self, idx: int) -> URIRef:
        return self.ns[f"page_idx{idx}"]

    def chapter_iri(self, num: str) -> URIRef:
        return self.ns[f"ch_{safe_local(num)}"]

    def section_iri(self, num: str) -> URIRef:
        return self.ns[f"sec_{safe_local(num)}"]

    def span_iri(self, span_id: str) -> URIRef:
        return self.ns[safe_local(span_id.replace(f"{self.doc_id}-", ""))]

    def claim_iri(self, claim_id: str) -> URIRef:
        return self.ns[safe_local(claim_id.replace(f"{self.doc_id}-", ""))]

    def artifact_iri(self, kind: str, number: str) -> URIRef:
        return self.ns[f"{kind}_{safe_local(number)}"]

    # -- bibliographic scaffolding ----------------------------------------
    def emit_bibliography(self) -> None:
        g, ns = self.g, self.ns
        book, edition, doc = self.book_iri(), self.edition_iri(), self.doc_iri()

        g.add((book, RDF.type, EV.Book))
        g.add((book, EV.bookTitle, Literal(self.cfg["title"], lang="en")))
        g.add((book, RDFS.label, Literal(self.cfg["title"], lang="en")))
        for author in self.cfg.get("authors", []):
            g.add((book, EV.author, Literal(author)))
        g.add((book, EV.hasEdition, edition))

        g.add((edition, RDF.type, EV.BookEdition))
        g.add((edition, RDFS.label,
               Literal(f"{self.cfg['title']}, {self.cfg['edition']} edition", lang="en")))
        g.add((edition, EV.editionLabel, Literal(self.cfg["edition"])))
        g.add((edition, EV.editionOrdinal, Literal(int(self.cfg["edition_ordinal"]), datatype=XSD.integer)))
        g.add((edition, EV.publisher, Literal(self.cfg["publisher"])))
        g.add((edition, EV.publicationYear, Literal(str(self.cfg["year"]), datatype=XSD.gYear)))
        g.add((edition, EV.hasDocument, doc))

        g.add((doc, RDF.type, EV.SourceDocument))
        g.add((doc, RDFS.label, Literal(self.cfg["file"])))
        g.add((doc, EV.sourceFileName, Literal(self.cfg["file"])))
        g.add((doc, EV.sha256, Literal(self.meta["sha256"])))
        g.add((doc, EV.pageCount, Literal(int(self.meta["page_count"]), datatype=XSD.integer)))
        # Text-layer reliability is a property of THIS file, not of the edition.
        g.add((doc, EV.textIntegrity, Literal(self.cfg.get("math_text_reliability", "unverified"))))

    # -- structural entities ----------------------------------------------
    def ensure_page(self, span: Dict[str, Any]) -> URIRef:
        idx = int(span["pdf_page_index"])
        page = self.page_iri(idx)
        if idx in self._pages:
            return page
        self._pages.add(idx)
        g = self.g
        g.add((page, RDF.type, EV.Page))
        g.add((page, EV.pageOfDocument, self.doc_iri()))
        # The two page numbers, kept as separate properties. Never derived.
        g.add((page, EV.pdfPageIndex, Literal(idx, datatype=XSD.integer)))
        g.add((page, EV.pdfPageNumber, Literal(int(span["pdf_page_number"]), datatype=XSD.integer)))
        if span.get("printed_page"):
            g.add((page, EV.printedPage, Literal(str(span["printed_page"]))))
        if span.get("page_label"):
            g.add((page, EV.pageLabel, Literal(str(span["page_label"]))))
        g.add((page, EV.pageLabelStyle, Literal(str(span["page_label_style"]))))
        label = span.get("printed_page") or span.get("page_label") or f"index {idx}"
        g.add((page, RDFS.label, Literal(f"{self.doc_id} p. {label} (pdf index {idx})", lang="en")))
        return page

    def ensure_chapter(self, number: Optional[str], title: Optional[str]) -> Optional[URIRef]:
        if not number:
            return None
        ch = self.chapter_iri(number)
        if number not in self._chapters:
            self._chapters.add(number)
            self.g.add((ch, RDF.type, EV.Chapter))
            self.g.add((ch, EV.chapterNumber, Literal(str(number))))
            if title:
                self.g.add((ch, EV.chapterTitle, Literal(title, lang="en")))
                self.g.add((ch, RDFS.label, Literal(f"{self.doc_id} ch. {number}: {title}", lang="en")))
            self.g.add((self.edition_iri(), EV.hasChapter, ch))
        return ch

    def ensure_section(
        self, number: Optional[str], title: Optional[str], chapter: Optional[URIRef]
    ) -> Optional[URIRef]:
        if not number:
            return None
        sec = self.section_iri(number)
        if number not in self._sections:
            self._sections.add(number)
            self.g.add((sec, RDF.type, EV.Section))
            self.g.add((sec, EV.sectionNumber, Literal(str(number))))
            if title:
                self.g.add((sec, EV.sectionTitle, Literal(title, lang="en")))
                self.g.add((sec, RDFS.label, Literal(f"{self.doc_id} sec. {number}: {title}", lang="en")))
            if chapter is not None:
                self.g.add((chapter, EV.hasSection, sec))
        return sec

    ARTIFACT_CLASSES = {
        "equation": (EV.Equation, EV.equationNumber, "eq"),
        "table": (EV.Table, EV.tableNumber, "tab"),
        "figure": (EV.Figure, EV.figureNumber, "fig"),
        "example": (EV.ExampleProblem, EV.exampleNumber, "ex"),
        "procedure": (EV.DesignProcedure, None, "proc"),
        "section": (None, None, None),
    }

    def ensure_artifact(self, kind: str, number: str) -> Optional[URIRef]:
        spec = self.ARTIFACT_CLASSES.get(kind)
        if not spec or spec[0] is None:
            return None
        cls, num_prop, tag = spec
        iri = self.artifact_iri(tag, number)
        if (kind, number) not in self._artifacts:
            self._artifacts.add((kind, number))
            self.g.add((iri, RDF.type, cls))
            if num_prop is not None:
                self.g.add((iri, num_prop, Literal(str(number))))
            self.g.add((iri, RDFS.label, Literal(f"{self.doc_id} {kind} {number}", lang="en")))
        return iri

    # -- spans -------------------------------------------------------------
    def emit_span(self, span: Dict[str, Any]) -> URIRef:
        g = self.g
        iri = self.span_iri(span["span_id"])
        page = self.ensure_page(span)
        chapter = self.ensure_chapter(span.get("chapter_number"), span.get("chapter_title"))
        section = self.ensure_section(span.get("section_number"), span.get("section_title"), chapter)

        g.add((iri, RDF.type, EV.EvidenceSpan))
        g.add((iri, RDFS.label, Literal(span["span_id"])))
        g.add((iri, EV.spanOfDocument, self.doc_iri()))
        g.add((iri, EV.spanOnPage, page))
        if chapter is not None:
            g.add((iri, EV.inChapter, chapter))
        if section is not None:
            g.add((iri, EV.inSection, section))
        g.add((iri, EV.blockIdentifier, Literal(span["block_id"])))
        g.add((iri, EV.boundingBox, Literal(",".join(str(v) for v in span["bbox"]))))
        g.add((iri, EV.extractedText, Literal(span["extracted_text"], lang="en")))
        g.add((iri, EV.extractionMethod, Literal(span["extraction_method"])))
        g.add((iri, EV.extractionConfidence,
               Literal(float(span["extraction_confidence"]), datatype=XSD.decimal)))
        g.add((iri, EV.textIntegrity, Literal(span["text_integrity"])))
        g.add((iri, EV.mathFontCharRatio,
               Literal(float(span["math_font_char_ratio"]), datatype=XSD.decimal)))
        if span.get("note"):
            g.add((iri, MDCORE.analystNote, Literal(span["note"], lang="en")))

        for ref in span.get("artifact_refs", []):
            art = self.ensure_artifact(ref.get("kind", ""), ref.get("number", ""))
            if art is not None:
                # The item is tied to the running text that explains it, so it is
                # never cited stripped of its own paragraph's conditions.
                g.add((art, EV.explainedBySpan, iri))
        return iri

    # -- claims ------------------------------------------------------------
    def emit_claim(self, claim: Dict[str, Any]) -> URIRef:
        g = self.g
        iri = self.claim_iri(claim["claim_id"])
        g.add((iri, RDF.type, EV.NormalizedClaim))
        g.add((iri, RDFS.label, Literal(claim["claim_id"])))
        g.add((iri, EV.claimIdentifier, Literal(claim["claim_id"])))
        g.add((iri, EV.normalizedStatement, Literal(claim["normalized_statement"], lang="en")))
        g.add((iri, EV.fromSourceDocument, self.doc_iri()))
        g.add((iri, EV.claimTopic, Literal(claim["topic"])))
        g.add((iri, EV.textIntegrity, Literal(claim["text_integrity"])))

        for key, prop in (
            ("subject", EV.claimSubject), ("predicate", EV.claimPredicate), ("object", EV.claimObject),
        ):
            if claim.get(key):
                g.add((iri, prop, Literal(claim[key], lang="en")))
        for key, prop in (
            ("conditions", EV.claimCondition), ("exceptions", EV.claimException),
            ("assumptions", EV.claimAssumption),
        ):
            for value in claim.get(key) or []:
                g.add((iri, prop, Literal(value, lang="en")))
        if claim.get("analyst_note"):
            g.add((iri, MDCORE.analystNote, Literal(claim["analyst_note"], lang="en")))

        g.add((iri, EV.extractionMethod, Literal(claim["extraction_method"])))
        g.add((iri, EV.extractionConfidence,
               Literal(float(claim["extraction_confidence"]), datatype=XSD.decimal)))
        g.add((iri, MDCORE.reviewStatus, MDCORE[claim["review_status"]]))

        for span_id in claim["evidence_span_ids"]:
            g.add((iri, EV.supportedByEvidence, self.span_iri(span_id)))

        for kind, prop in (
            ("equations", EV.concernsEquation), ("tables", EV.concernsTable),
            ("figures", EV.concernsFigure),
        ):
            singular = {"equations": "equation", "tables": "table", "figures": "figure"}[kind]
            for number in claim.get(kind) or []:
                art = self.ensure_artifact(singular, number)
                if art is not None:
                    g.add((iri, prop, art))
        for number in claim.get("examples") or []:
            art = self.ensure_artifact("example", number)
            if art is not None:
                g.add((iri, EV.claimAbout, art))
        for number in claim.get("procedures") or []:
            art = self.ensure_artifact("procedure", number)
            if art is not None:
                g.add((iri, EV.claimAbout, art))

        for standard in claim.get("standards") or []:
            std = self.ns[f"std_{safe_local(standard)[:60]}"]
            g.add((std, RDF.type, EV.Standard))
            g.add((std, RDFS.label, Literal(standard, lang="en")))
            g.add((iri, EV.claimAbout, std))

        for curie in claim.get("about") or []:
            g.add((iri, EV.claimAbout, expand(curie)))
        for curie in claim.get("external_authority") or []:
            g.add((iri, MDCORE.requiresExternalAuthority, expand(curie)))

        for i, qty in enumerate(claim.get("quantities") or []):
            self._emit_quantity(iri, claim["claim_id"], i, qty)

        if claim.get("threshold"):
            self._emit_threshold(iri, claim)
        if claim.get("verification"):
            self._emit_verification(iri, claim)
        if claim.get("equation_transcription"):
            tr = claim["equation_transcription"]
            for number in claim.get("equations") or []:
                art = self.ensure_artifact("equation", number)
                if art is not None:
                    g.add((art, EV.transcriptionSource, Literal(tr.get("source", "unspecified"))))
                    if tr.get("note"):
                        g.add((art, MDCORE.analystNote, Literal(tr["note"], lang="en")))
        return iri

    def _emit_quantity(self, claim_iri: URIRef, claim_id: str, index: int, qty: Dict[str, Any]) -> None:
        g = self.g
        q = self.ns[f"{safe_local(claim_id)}_q{index}"]
        g.add((q, RDF.type, MDCORE.QuantityValue))
        g.add((q, RDFS.label, Literal(qty["role"], lang="en")))
        # A unit is mandatory; 'dimensionless' is a unit, not its absence.
        g.add((q, MDCORE.unitSymbol, Literal(qty["unit"])))
        if qty.get("value") is not None:
            g.add((q, MDCORE.numericValue, Literal(float(qty["value"]), datatype=XSD.decimal)))
        if qty.get("is_range"):
            g.add((q, MDCORE.valueIsRange, Literal(True, datatype=XSD.boolean)))
            g.add((q, MDCORE.rangeMinimum, Literal(float(qty["range_min"]), datatype=XSD.decimal)))
            g.add((q, MDCORE.rangeMaximum, Literal(float(qty["range_max"]), datatype=XSD.decimal)))
        g.add((q, MDCORE.originalValue, Literal(str(qty["original_value"]))))
        g.add((q, MDCORE.originalUnit, Literal(str(qty["original_unit"]))))
        if qty.get("conversion_method"):
            g.add((q, MDCORE.conversionMethod, Literal(qty["conversion_method"], lang="en")))
        g.add((q, MDCORE.valueProvenance, MDCORE[qty.get("value_provenance", "SourceDerivedValue")]))
        g.add((claim_iri, EV.claimQuantity, q))

    def _emit_threshold(self, claim_iri: URIRef, claim: Dict[str, Any]) -> None:
        g = self.g
        th = claim["threshold"]
        iri = self.ns[f"{safe_local(claim['claim_id'])}_threshold"]
        g.add((iri, RDF.type, MDCORE.ThresholdDefinition))
        g.add((iri, RDFS.label, Literal(f"threshold for '{th['term']}'", lang="en")))
        g.add((iri, MDCORE.definesTerm, Literal(th["term"])))
        g.add((iri, MDCORE.thresholdIsUniversal,
               Literal(bool(th["is_universal"]), datatype=XSD.boolean)))
        if th.get("scope_note"):
            g.add((iri, MDCORE.thresholdScopeNote, Literal(th["scope_note"], lang="en")))
        g.add((claim_iri, EV.claimAbout, iri))

    def _emit_verification(self, claim_iri: URIRef, claim: Dict[str, Any]) -> None:
        g = self.g
        v = claim["verification"]
        iri = self.ns[f"{safe_local(claim['claim_id'])}_verification"]
        kind = v.get("method_kind", "VerificationMethod")
        g.add((iri, RDF.type, MDCORE[kind]))
        g.add((iri, RDFS.label, Literal(f"verification recommended by {claim['claim_id']}", lang="en")))
        # The three booleans are always all present: an unstated procedure is a
        # recorded gap, never an omitted field.
        g.add((iri, MDCORE.testRecommended,
               Literal(bool(v["test_recommended"]), datatype=XSD.boolean)))
        g.add((iri, MDCORE.testProcedureSpecified,
               Literal(bool(v["test_procedure_specified"]), datatype=XSD.boolean)))
        g.add((iri, MDCORE.acceptanceCriterionSpecified,
               Literal(bool(v["acceptance_criterion_specified"]), datatype=XSD.boolean)))
        for curie in v.get("external_authority") or []:
            g.add((iri, MDCORE.requiresExternalAuthority, expand(curie)))
        g.add((claim_iri, EV.claimAbout, iri))


def build_source_graphs(
    config: Dict[str, Any], spans: List[Dict[str, Any]], claims: List[Dict[str, Any]]
) -> Dict[str, Graph]:
    """Build one graph per source document."""
    build_dir = REPO_ROOT / config["paths"]["build_dir"]
    graphs: Dict[str, Graph] = {}
    for doc_id, source_cfg in config["sources"].items():
        meta = json.loads((build_dir / f"{doc_id}.meta.json").read_text(encoding="utf-8"))
        builder = SourceGraphBuilder(doc_id, source_cfg, meta)
        builder.emit_bibliography()
        for span in spans:
            if span["doc_id"] == doc_id:
                builder.emit_span(span)
        for claim in claims:
            if claim["doc_id"] == doc_id:
                builder.emit_claim(claim)
        graphs[doc_id] = builder.g
        LOG.info("[%s] claims graph: %d triples", doc_id, len(builder.g))
    return graphs


# ---------------------------------------------------------------------------
# Alignments
# ---------------------------------------------------------------------------


def claim_iri_for(claim_id: str) -> URIRef:
    """Resolve a claim id such as 'mott6-c-0001' to its source-namespaced IRI."""
    for doc_id, ns in SOURCE_NS.items():
        if claim_id.startswith(doc_id + "-"):
            return ns[safe_local(claim_id[len(doc_id) + 1:])]
    raise BuildError(f"claim id {claim_id!r} does not start with a known source prefix")


def span_iri_for(span_id: str) -> URIRef:
    for doc_id, ns in SOURCE_NS.items():
        if span_id.startswith(doc_id + "-"):
            return ns[safe_local(span_id[len(doc_id) + 1:])]
    raise BuildError(f"span id {span_id!r} does not start with a known source prefix")


CLAIM_RELATIONS = {
    "supports": EV.supports, "agreesWith": EV.agreesWith, "complements": EV.complements,
    "refines": EV.refines, "broaderThan": EV.broaderThanClaim, "narrowerThan": EV.narrowerThanClaim,
    "differsFrom": EV.differsFrom, "contradicts": EV.contradicts,
    "unresolvedRelativeTo": EV.unresolvedRelativeTo,
}


def build_alignment_graph(data: Dict[str, Any], known_claims: Set[str]) -> Tuple[Graph, List[Dict[str, str]]]:
    """Build the cross-source alignment graph and the flat terminology table."""
    g = bind_all(Graph())
    rows: List[Dict[str, str]] = []
    defaults = data.get("defaults", {})

    for ca in data.get("concept_alignments", []):
        iri = ALIGN[safe_local(ca["id"])]
        g.add((iri, RDF.type, EV.TerminologyAlignment))
        g.add((iri, RDFS.label, Literal(ca["common_concept"], lang="en")))
        g.add((iri, EV.commonConcept, Literal(ca["common_concept"], lang="en")))
        g.add((iri, EV.alignmentType, EV[ca["alignment_type"]]))
        if ca.get("core_concept"):
            g.add((iri, EV.alignsToConcept, expand(ca["core_concept"])))
        for doc_id in ("mott6", "shigley10"):
            term = ca.get(f"{doc_id}_term")
            symbol = ca.get(f"{doc_id}_symbol")
            if term:
                g.add((iri, EV.alignsSourceTerm, Literal(f"{doc_id}: {term}", lang="en")))
            if symbol:
                g.add((iri, EV.alignsSourceSymbol, Literal(f"{doc_id}: {symbol}")))
        if ca.get("analyst_note"):
            g.add((iri, MDCORE.analystNote, Literal(" ".join(ca["analyst_note"].split()), lang="en")))
        g.add((iri, MDCORE.reviewStatus, MDCORE[ca.get("review_status", defaults.get("review_status", "NeedsReview"))]))
        for span_id in ca.get("evidence", []):
            g.add((iri, EV.supportedByEvidence, span_iri_for(span_id)))

        rows.append({
            "alignment_id": ca["id"],
            "common_concept": ca["common_concept"],
            "core_concept": ca.get("core_concept", ""),
            "mott6_term": ca.get("mott6_term", ""),
            "mott6_symbol": ca.get("mott6_symbol", ""),
            "shigley10_term": ca.get("shigley10_term", ""),
            "shigley10_symbol": ca.get("shigley10_symbol", ""),
            "alignment_type": ca["alignment_type"],
            "review_status": ca.get("review_status", defaults.get("review_status", "NeedsReview")),
            "evidence_span_ids": ";".join(ca.get("evidence", [])),
            "analyst_note": " ".join(ca.get("analyst_note", "").split()),
        })

    for cl in data.get("claim_alignments", []):
        for key in ("claim_a", "claim_b"):
            if cl[key] not in known_claims:
                raise BuildError(f"{cl['id']}: references unknown claim {cl[key]!r}")
        iri = ALIGN[safe_local(cl["id"])]
        a, b = claim_iri_for(cl["claim_a"]), claim_iri_for(cl["claim_b"])
        g.add((iri, RDF.type, EV.ClaimAlignment))
        g.add((iri, RDFS.label, Literal(f"{cl['claim_a']} vs {cl['claim_b']}", lang="en")))
        g.add((iri, EV.sourceClaimA, a))
        g.add((iri, EV.sourceClaimB, b))
        g.add((iri, EV.alignmentType, EV[cl["alignment_type"]]))
        if cl.get("common_concept"):
            g.add((iri, EV.commonConcept, Literal(cl["common_concept"], lang="en")))
        if cl.get("differing_conditions"):
            g.add((iri, EV.differingConditions,
                   Literal(" ".join(cl["differing_conditions"].split()), lang="en")))
        if cl.get("differing_assumptions"):
            g.add((iri, EV.differingAssumptions,
                   Literal(" ".join(cl["differing_assumptions"].split()), lang="en")))
        if cl.get("analyst_note"):
            g.add((iri, MDCORE.analystNote, Literal(" ".join(cl["analyst_note"].split()), lang="en")))
        g.add((iri, MDCORE.reviewStatus,
               MDCORE[cl.get("review_status", defaults.get("review_status", "NeedsReview"))]))
        # The direct claim-to-claim edge, so a query can traverse without the
        # reification. The alignment individual keeps the nuance.
        relation = CLAIM_RELATIONS.get(cl.get("relation", ""))
        if relation is not None:
            g.add((a, relation, b))
    return g, rows


# ---------------------------------------------------------------------------
# Substitution assessments, contexts, requirements, rules
# ---------------------------------------------------------------------------


def build_substitution_graph(data: Dict[str, Any]) -> Graph:
    """Build contexts, requirements and reified substitution assessments."""
    g = bind_all(Graph())

    for ctx in data.get("contexts", []):
        iri = MDKG[safe_local(ctx["id"])]
        g.add((iri, RDF.type, MDCORE.OperatingContext))
        g.add((iri, RDFS.label, Literal(ctx["label"], lang="en")))
        for cond in ctx.get("conditions", []):
            g.add((iri, MDCORE.hasCondition, expand(cond)))
        if not ctx.get("conditions"):
            g.add((iri, MDCORE.contextUnspecified, Literal(True, datatype=XSD.boolean)))
        if ctx.get("note"):
            g.add((iri, MDCORE.analystNote, Literal(" ".join(ctx["note"].split()), lang="en")))

    for req in data.get("requirements", []):
        iri = MDKG[safe_local(req["id"])]
        g.add((iri, RDF.type, MDCORE.Requirement))
        g.add((iri, RDFS.label, Literal(req["label"], lang="en")))
        g.add((iri, MDCORE.hasRequirementKind, expand(req["kind"])))
        g.add((iri, MDCORE.requirementStatement, Literal(req["statement"], lang="en")))

    for sa in data.get("assessments", []):
        _emit_assessment(g, sa)
    return g


def _emit_assessment(g: Graph, sa: Dict[str, Any]) -> None:
    """Emit one reified SubstitutionAssessment with all its arguments."""
    iri = MDKG[safe_local(sa["id"])]
    candidate = expand(sa["candidate"])
    baseline = expand(sa["baseline"])

    g.add((iri, RDF.type, MDCORE.SubstitutionAssessment))
    g.add((iri, RDFS.label, Literal(sa["label"], lang="en")))
    g.add((iri, MDCORE.candidateAlternative, candidate))
    g.add((iri, MDCORE.baselineAlternative, baseline))
    g.add((iri, MDCORE.functionBeingPreserved, expand(sa["function_preserved"])))
    g.add((iri, MDCORE.assessmentContext, MDKG[safe_local(sa["context"])]))
    g.add((iri, MDCORE.assessmentConclusion, MDCORE[sa["conclusion"]]))
    g.add((iri, MDCORE.interfaceCompatibility, MDCORE[sa["interface_compatibility"]]))
    g.add((iri, MDCORE.confidence, Literal(float(sa.get("confidence", 0.5)), datatype=XSD.decimal)))
    g.add((iri, MDCORE.reviewStatus, MDCORE[sa.get("review_status", "NeedsReview")]))
    if sa.get("analyst_note"):
        g.add((iri, MDCORE.analystNote, Literal(" ".join(sa["analyst_note"].split()), lang="en")))

    for key, prop in (
        ("applicable_requirements", MDCORE.applicableRequirement),
        ("satisfied_requirements", MDCORE.satisfiedRequirement),
        ("violated_requirements", MDCORE.violatedRequirement),
    ):
        for rid in sa.get(key) or []:
            g.add((iri, prop, MDKG[safe_local(rid)]))

    for i, cond in enumerate(sa.get("conditions") or []):
        cond_iri = MDKG[f"{safe_local(sa['id'])}_cond{i}"]
        g.add((cond_iri, RDF.type, expand(cond["condition"])))
        g.add((cond_iri, RDFS.label, Literal(cond["statement"][:90], lang="en")))
        g.add((cond_iri, MDCORE.conditionStatement, Literal(cond["statement"], lang="en")))
        g.add((cond_iri, MDCORE.valueProvenance, MDCORE[cond.get("provenance", "EngineeringInference")]))
        for span_id in cond.get("evidence") or []:
            g.add((cond_iri, EV.supportedByEvidence, span_iri_for(span_id)))
        g.add((iri, MDCORE.assessmentCondition, cond_iri))

    for i, mod in enumerate(sa.get("modifications") or []):
        mod_iri = MDKG[f"{safe_local(sa['id'])}_mod{i}"]
        g.add((mod_iri, RDF.type, MDCORE.DesignModification))
        g.add((mod_iri, RDFS.label, Literal(mod["statement"][:90], lang="en")))
        g.add((mod_iri, MDCORE.modificationStatement, Literal(mod["statement"], lang="en")))
        if mod.get("effort"):
            g.add((mod_iri, MDCORE.modificationEffort, Literal(mod["effort"])))
        g.add((mod_iri, MDCORE.valueProvenance, MDCORE[mod.get("provenance", "EngineeringInference")]))
        for span_id in mod.get("evidence") or []:
            g.add((mod_iri, EV.supportedByEvidence, span_iri_for(span_id)))
        g.add((iri, MDCORE.requiredDesignModification, mod_iri))

    for key, prop, tag in (
        ("advantages", MDCORE.assessmentAdvantage, "adv"),
        ("disadvantages", MDCORE.assessmentDisadvantage, "dis"),
    ):
        for i, item in enumerate(sa.get(key) or []):
            ev_iri = MDKG[f"{safe_local(sa['id'])}_{tag}{i}"]
            g.add((ev_iri, RDF.type, MDCORE.AlternativeEvaluation))
            g.add((ev_iri, RDFS.label, Literal(item["statement"][:90], lang="en")))
            g.add((ev_iri, MDCORE.evaluatesAlternative, candidate))
            g.add((ev_iri, MDCORE.againstCriterion, expand(item["criterion"])))
            g.add((ev_iri, MDCORE.evaluationLevel, MDCORE[item["level"]]))
            g.add((ev_iri, MDCORE.evaluationScale, Literal("mdkg qualitative satisfaction scale v1")))
            g.add((ev_iri, MDCORE.applicableContext, MDKG[safe_local(sa["context"])]))
            g.add((ev_iri, MDCORE.valueProvenance,
                   MDCORE[item.get("provenance", "EngineeringInference")]))
            g.add((ev_iri, MDCORE.analystNote, Literal(item["statement"], lang="en")))
            for span_id in item.get("evidence") or []:
                g.add((ev_iri, EV.supportedByEvidence, span_iri_for(span_id)))
            g.add((iri, prop, ev_iri))
            g.add((candidate, MDCORE.hasAdvantage if tag == "adv" else MDCORE.hasDisadvantage, ev_iri))

    for i, to in enumerate(sa.get("trade_offs") or []):
        to_iri = MDKG[f"{safe_local(sa['id'])}_to{i}"]
        g.add((to_iri, RDF.type, MDCORE.TradeOff))
        g.add((to_iri, RDFS.label, Literal(to["statement"][:90], lang="en")))
        g.add((to_iri, MDCORE.tradeOffGains, expand(to["gains"])))
        g.add((to_iri, MDCORE.tradeOffCosts, expand(to["costs"])))
        g.add((to_iri, MDCORE.tradeOffStatement, Literal(to["statement"], lang="en")))
        g.add((to_iri, MDCORE.valueProvenance, MDCORE[to.get("provenance", "EngineeringInference")]))
        for span_id in to.get("evidence") or []:
            g.add((to_iri, EV.supportedByEvidence, span_iri_for(span_id)))
        g.add((iri, MDCORE.assessmentTradeOff, to_iri))

    for key, prop in (
        ("introduced_failure_modes", MDCORE.introducedFailureMode),
        ("mitigated_failure_modes", MDCORE.mitigatedFailureMode),
    ):
        for item in sa.get(key) or []:
            g.add((iri, prop, expand(item["failure_mode"])))

    for i, ver in enumerate(sa.get("required_verification") or []):
        method = expand(ver["method"])
        g.add((iri, MDCORE.requiredVerification, method))
        note_iri = MDKG[f"{safe_local(sa['id'])}_ver{i}"]
        g.add((note_iri, RDF.type, MDCORE.AcceptanceCriterion))
        g.add((note_iri, RDFS.label, Literal(ver["statement"][:90], lang="en")))
        g.add((note_iri, MDCORE.acceptanceStatement, Literal(ver["statement"], lang="en")))
        g.add((method, MDCORE.hasAcceptanceCriterion, note_iri))
        for span_id in ver.get("evidence") or []:
            g.add((note_iri, EV.supportedByEvidence, span_iri_for(span_id)))
        # Where a test is named, its three specification booleans travel with it.
        if "test_recommended" in ver:
            g.add((method, MDCORE.testRecommended,
                   Literal(bool(ver["test_recommended"]), datatype=XSD.boolean)))
            g.add((method, MDCORE.testProcedureSpecified,
                   Literal(bool(ver.get("test_procedure_specified", False)), datatype=XSD.boolean)))
            g.add((method, MDCORE.acceptanceCriterionSpecified,
                   Literal(bool(ver.get("acceptance_criterion_specified", False)), datatype=XSD.boolean)))
        for curie in ver.get("external_authority") or []:
            g.add((method, MDCORE.requiresExternalAuthority, expand(curie)))

    for i, un in enumerate(sa.get("unresolved") or []):
        un_iri = MDKG[f"{safe_local(sa['id'])}_open{i}"]
        g.add((un_iri, RDF.type, MDCORE.SubstitutionAssessment))
        g.add((un_iri, RDFS.label, Literal(f"open question in {sa['id']}", lang="en")))
        g.add((un_iri, MDCORE.candidateAlternative, candidate))
        g.add((un_iri, MDCORE.baselineAlternative, baseline))
        g.add((un_iri, MDCORE.functionBeingPreserved, expand(sa["function_preserved"])))
        g.add((un_iri, MDCORE.assessmentContext, MDKG[safe_local(sa["context"])]))
        g.add((un_iri, MDCORE.assessmentConclusion, MDCORE[un.get("state", "InsufficientEvidence")]))
        g.add((un_iri, MDCORE.analystNote, Literal(un["statement"], lang="en")))
        g.add((un_iri, MDCORE.reviewStatus, MDCORE.NeedsReview))
        for span_id in un.get("evidence") or []:
            g.add((un_iri, EV.supportedByEvidence, span_iri_for(span_id)))

    for claim_id in sa.get("supporting_claims") or []:
        g.add((iri, EV.supportedByEvidence, claim_iri_for(claim_id)))

    # The shortcut edge is MATERIALISED here, from an existing assessment, and
    # only in the direction the assessment states. It is never asserted by hand
    # and never mirrored.
    if sa["conclusion"] in ("ConditionallySubstitutable", "DirectlySubstitutable", "PreferredAlternative"):
        g.add((candidate, MDCORE.substitutionAssessedAs, baseline))


def build_rule_graph(rules_dir: Path) -> Graph:
    """Emit citable stubs for the YAML rule layer."""
    g = bind_all(Graph())
    kind_map = {
        "SelectionRule": MDCORE.SelectionRule,
        "SubstitutionRule": MDCORE.SubstitutionRule,
        "VerificationRule": MDCORE.VerificationRule,
    }
    for yaml_path in sorted(rules_dir.glob("*.yaml")):
        data = load_yaml(yaml_path)
        for rule in data.get("rules", []):
            iri = MDKG[safe_local(rule["id"])]
            g.add((iri, RDF.type, kind_map.get(rule.get("kind", ""), MDCORE.DesignRule)))
            g.add((iri, RDFS.label, Literal(rule["title"], lang="en")))
            g.add((iri, MDCORE.ruleIdentifier, Literal(rule["id"])))
            g.add((iri, MDCORE.ruleStatement,
                   Literal(" ".join(str(rule["statement"]).split()), lang="en")))
            g.add((iri, MDCORE.ruleIsAnalystAuthored,
                   Literal(bool(rule.get("analyst_authored", False)), datatype=XSD.boolean)))
            g.add((iri, MDCORE.reviewStatus, MDCORE[rule.get("review_status", "NeedsReview")]))
            g.add((iri, MDCORE.confidence,
                   Literal(float(rule.get("confidence", 0.5)), datatype=XSD.decimal)))
            g.add((iri, DCTERMS.source, Literal(str(yaml_path.relative_to(REPO_ROOT)))))

            applies = rule.get("applies_when") or {}
            conditions = list(applies.get("context_conditions") or [])
            for cond in conditions:
                g.add((iri, MDCORE.ruleAppliesInContext, expand(cond)))
            # An empty context is recorded explicitly, never left to inference.
            if not conditions:
                g.add((iri, MDCORE.contextUnspecified, Literal(True, datatype=XSD.boolean)))
            if applies.get("function"):
                g.add((iri, MDCORE.ruleConcernsFunction, expand(applies["function"])))

            for target_key in ("effect", "applies_to"):
                block = rule.get(target_key) or {}
                for curie in block.get("alternatives") or []:
                    g.add((iri, MDCORE.ruleConcernsAlternative, expand(curie)))
                for curie in block.get("over") or []:
                    g.add((iri, MDCORE.ruleConcernsAlternative, expand(curie)))

            for claim_id in rule.get("derived_from") or []:
                g.add((iri, MDCORE.ruleDerivedFromClaim, claim_iri_for(claim_id)))
            for curie in rule.get("requires_external_authority") or []:
                g.add((iri, MDCORE.requiresExternalAuthority, expand(curie)))
            if rule.get("notes"):
                g.add((iri, MDCORE.analystNote, Literal(" ".join(rule["notes"].split()), lang="en")))
    return g


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize(full: Graph, tbox_graphs: Dict[str, Graph]) -> Dict[str, Any]:
    """Produce a machine-readable census of the built ontology."""
    def count_of(g: Graph, cls: URIRef) -> int:
        return len(set(g.subjects(RDF.type, cls)))

    classes = sorted({str(s) for g in tbox_graphs.values() for s in g.subjects(RDF.type, OWL.Class)})
    obj_props = sorted({str(s) for g in tbox_graphs.values() for s in g.subjects(RDF.type, OWL.ObjectProperty)})
    dat_props = sorted({str(s) for g in tbox_graphs.values() for s in g.subjects(RDF.type, OWL.DatatypeProperty)})
    schemes = sorted({str(s) for g in tbox_graphs.values() for s in g.subjects(RDF.type, SKOS.ConceptScheme)})

    conclusions: Dict[str, int] = defaultdict(int)
    for _, concl in full.subject_objects(MDCORE.assessmentConclusion):
        conclusions[str(concl).rsplit("#", 1)[-1]] += 1
    review: Dict[str, int] = defaultdict(int)
    for _, state in full.subject_objects(MDCORE.reviewStatus):
        review[str(state).rsplit("#", 1)[-1]] += 1
    integrity: Dict[str, int] = defaultdict(int)
    for _, val in full.subject_objects(EV.textIntegrity):
        integrity[str(val)] += 1

    return {
        "tbox": {
            "classes": len(classes),
            "object_properties": len(obj_props),
            "datatype_properties": len(dat_props),
            "skos_concept_schemes": len(schemes),
            "class_iris": classes,
            "object_property_iris": obj_props,
            "datatype_property_iris": dat_props,
            "modules": {name: len(g) for name, g in sorted(tbox_graphs.items())},
        },
        "abox": {
            "claims": count_of(full, EV.NormalizedClaim),
            "evidence_spans": count_of(full, EV.EvidenceSpan),
            "pages": count_of(full, EV.Page),
            "chapters": count_of(full, EV.Chapter),
            "sections": count_of(full, EV.Section),
            "equations": count_of(full, EV.Equation),
            "tables": count_of(full, EV.Table),
            "figures": count_of(full, EV.Figure),
            "example_problems": count_of(full, EV.ExampleProblem),
            "design_procedures": count_of(full, EV.DesignProcedure),
            "standards_referenced": count_of(full, EV.Standard),
            "design_alternatives": count_of(full, MDCORE.DesignAlternative),
            "substitution_assessments": count_of(full, MDCORE.SubstitutionAssessment),
            "alternative_evaluations": count_of(full, MDCORE.AlternativeEvaluation),
            "trade_offs": count_of(full, MDCORE.TradeOff),
            "design_modifications": count_of(full, MDCORE.DesignModification),
            "operating_contexts": count_of(full, MDCORE.OperatingContext),
            "requirements": count_of(full, MDCORE.Requirement),
            "quantity_values": count_of(full, MDCORE.QuantityValue),
            "threshold_definitions": count_of(full, MDCORE.ThresholdDefinition),
            "claim_alignments": count_of(full, EV.ClaimAlignment),
            "terminology_alignments": count_of(full, EV.TerminologyAlignment),
            "selection_rules": count_of(full, MDCORE.SelectionRule),
            "substitution_rules": count_of(full, MDCORE.SubstitutionRule),
            "verification_rules": count_of(full, MDCORE.VerificationRule),
        },
        "distributions": {
            "substitution_conclusions": dict(sorted(conclusions.items())),
            "review_states": dict(sorted(review.items())),
            "text_integrity": dict(sorted(integrity.items())),
        },
        "total_triples": len(full),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(config: Dict[str, Any]) -> Dict[str, Any]:
    ont_dir = REPO_ROOT / config["paths"]["ontology_dir"]
    data_dir = REPO_ROOT / config["paths"]["data_dir"]
    build_dir = REPO_ROOT / config["paths"]["build_dir"]
    out_dir = REPO_ROOT / config["paths"]["outputs_dir"]
    rules_dir = REPO_ROOT / config["paths"]["rules_dir"]

    written: Dict[str, int] = {}

    # --- TBox bundles ----------------------------------------------------
    core_graph, core_src = bundle_modules(ont_dir / "core", exclude=["evidence.ttl"])
    written["ontology/core.ttl"] = serialize(core_graph, ont_dir / "core.ttl", core_src)

    ev_graph, ev_src = bundle_modules(ont_dir / "core")
    ev_only = bind_all(Graph())
    ev_only.parse(ont_dir / "core" / "evidence.ttl", format="turtle")
    written["ontology/evidence.ttl"] = serialize(
        ev_only, ont_dir / "evidence.ttl", ["ontology/core/evidence.ttl"]
    )

    mech_graph, mech_src = bundle_modules(ont_dir / "mechanical-design")
    written["ontology/mechanical-design.ttl"] = serialize(
        mech_graph, ont_dir / "mechanical-design.ttl", mech_src
    )

    melem_graph, melem_src = bundle_modules(ont_dir / "machine-elements")
    written["ontology/machine-elements.ttl"] = serialize(
        melem_graph, ont_dir / "machine-elements.ttl", melem_src
    )

    # --- ABox -------------------------------------------------------------
    spans = load_jsonl(data_dir / "evidence_spans.jsonl")
    claims = load_jsonl(data_dir / "claims.jsonl")
    LOG.info("loaded %d spans, %d claims", len(spans), len(claims))

    source_graphs = build_source_graphs(config, spans, claims)
    for doc_id, graph in source_graphs.items():
        path = ont_dir / f"{doc_id}-claims.ttl"
        written[str(path.relative_to(REPO_ROOT))] = serialize(
            graph, path, ["data/evidence_spans.jsonl", "data/claims.jsonl", f"build/{doc_id}.meta.json"]
        )

    known_claims = {c["claim_id"] for c in claims}
    align_data = load_yaml(data_dir / "alignments_seed.yaml")
    align_graph, term_rows = build_alignment_graph(align_data, known_claims)

    sub_graph = build_substitution_graph(load_yaml(data_dir / "substitutions.yaml"))
    rule_graph = build_rule_graph(rules_dir)

    combined_align = bind_all(Graph())
    for g in (align_graph, sub_graph, rule_graph):
        combined_align += g
    written["ontology/alignments.ttl"] = serialize(
        combined_align, ont_dir / "alignments.ttl",
        ["data/alignments_seed.yaml", "data/substitutions.yaml", "rules/*.yaml"],
    )

    # --- terminology table ------------------------------------------------
    csv_path = data_dir / "terminology_alignment.csv"
    fieldnames = list(term_rows[0].keys()) if term_rows else ["alignment_id"]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(term_rows)
    LOG.info("wrote %d terminology alignments -> %s", len(term_rows), csv_path)

    # --- merged graph -----------------------------------------------------
    full = bind_all(Graph())
    for g in (core_graph, ev_only, mech_graph, melem_graph, combined_align, *source_graphs.values()):
        full += g
    written["build/mdkg-full.ttl"] = serialize(
        full, build_dir / "mdkg-full.ttl", ["all ontology modules and all curated data"]
    )

    summary = summarize(
        full,
        {
            "core": core_graph, "evidence": ev_only,
            "mechanical-design": mech_graph, "machine-elements": melem_graph,
        },
    )
    summary["files_written"] = written
    summary["terminology_alignment_rows"] = len(term_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ontology_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    config = load_yaml(args.config)
    summary = run(config)
    printable = {k: v for k, v in summary.items() if k != "tbox"}
    printable["tbox"] = {k: v for k, v in summary["tbox"].items() if not k.endswith("_iris")}
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
