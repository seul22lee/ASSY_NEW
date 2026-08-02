#!/usr/bin/env python3
"""Answer the ten required competency queries against the built graph.

Every citation printed here is ASSEMBLED from stored provenance fields --
book, edition, chapter, section, printed page, PDF page index, and any
equation, table or figure number.  No citation string is stored anywhere in
the pipeline, and none is ever composed by a language model.  If a field is
absent, the citation says so rather than filling the gap.

Run ``python3 scripts/query_examples.py`` for all queries, or
``--query 6`` for one.  ``--format json`` emits machine-readable results.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import yaml
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDFS

LOG = logging.getLogger("query_examples")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

PREFIX_BLOCK = """
PREFIX mdcore: <https://w3id.org/mdkg/core#>
PREFIX mech:   <https://w3id.org/mdkg/mechanical-design#>
PREFIX melem:  <https://w3id.org/mdkg/machine-elements#>
PREFIX ev:     <https://w3id.org/mdkg/evidence#>
PREFIX mdkg:   <https://w3id.org/mdkg/instances#>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos:   <http://www.w3.org/2004/02/skos/core#>
"""

MDCORE = Namespace("https://w3id.org/mdkg/core#")
EV = Namespace("https://w3id.org/mdkg/evidence#")


def short(term: Any) -> str:
    """Render an IRI as a compact prefixed name for display."""
    text = str(term)
    for ns, prefix in (
        ("https://w3id.org/mdkg/core#", "mdcore:"),
        ("https://w3id.org/mdkg/mechanical-design#", "mech:"),
        ("https://w3id.org/mdkg/machine-elements#", "melem:"),
        ("https://w3id.org/mdkg/evidence#", "ev:"),
        ("https://w3id.org/mdkg/instances#", "mdkg:"),
        ("https://w3id.org/mdkg/source/mott6#", "mott6:"),
        ("https://w3id.org/mdkg/source/shigley10#", "shigley10:"),
    ):
        if text.startswith(ns):
            return prefix + text[len(ns):]
    return text


# ---------------------------------------------------------------------------
# Citation assembly -- the only place a citation string is ever produced
# ---------------------------------------------------------------------------


def assemble_citation(graph: Graph, span: URIRef) -> Dict[str, Any]:
    """Build a citation from stored fields only.

    Any field the graph does not hold is reported as ``None`` and rendered as
    'not recorded'.  Nothing is inferred, and in particular the printed page is
    never computed from the PDF page index.
    """
    doc = graph.value(span, EV.spanOfDocument)
    page = graph.value(span, EV.spanOnPage)
    chapter = graph.value(span, EV.inChapter)
    section = graph.value(span, EV.inSection)

    # Walk document -> edition -> book so the title and edition are the ones
    # recorded for this file, not assumed.
    edition = next(graph.subjects(EV.hasDocument, doc), None) if doc else None
    book = next(graph.subjects(EV.hasEdition, edition), None) if edition else None

    fields: Dict[str, Any] = {
        "book_title": str(graph.value(book, EV.bookTitle)) if book else None,
        "authors": sorted(str(a) for a in graph.objects(book, EV.author)) if book else [],
        "edition": str(graph.value(edition, EV.editionLabel)) if edition else None,
        "source_file": str(graph.value(doc, EV.sourceFileName)) if doc else None,
        "chapter_number": str(graph.value(chapter, EV.chapterNumber)) if chapter else None,
        "chapter_title": str(graph.value(chapter, EV.chapterTitle)) if chapter else None,
        "section_number": str(graph.value(section, EV.sectionNumber)) if section else None,
        "section_title": str(graph.value(section, EV.sectionTitle)) if section else None,
        "printed_page": str(graph.value(page, EV.printedPage)) if page and graph.value(page, EV.printedPage) else None,
        "pdf_page_index": int(graph.value(page, EV.pdfPageIndex)) if page and graph.value(page, EV.pdfPageIndex) is not None else None,
        "pdf_page_number": int(graph.value(page, EV.pdfPageNumber)) if page and graph.value(page, EV.pdfPageNumber) is not None else None,
        "text_integrity": str(graph.value(span, EV.textIntegrity)) if graph.value(span, EV.textIntegrity) else None,
        "bounding_box": str(graph.value(span, EV.boundingBox)) if graph.value(span, EV.boundingBox) else None,
        "span_id": str(graph.value(span, RDFS.label)) if graph.value(span, RDFS.label) else short(span),
    }

    artifacts: List[str] = []
    for art in graph.subjects(EV.explainedBySpan, span):
        for prop, tag in ((EV.equationNumber, "Eq."), (EV.tableNumber, "Table"),
                          (EV.figureNumber, "Fig."), (EV.exampleNumber, "Example")):
            value = graph.value(art, prop)
            if value is not None:
                artifacts.append(f"{tag} {value}")
    fields["artifacts"] = sorted(set(artifacts))

    parts: List[str] = []
    if fields["book_title"]:
        parts.append(fields["book_title"])
    if fields["edition"]:
        parts.append(f"{fields['edition']} ed.")
    if fields["chapter_number"]:
        chap = f"ch. {fields['chapter_number']}"
        if fields["chapter_title"]:
            chap += f" ({fields['chapter_title']})"
        parts.append(chap)
    if fields["section_number"]:
        sec = f"sec. {fields['section_number']}"
        if fields["section_title"]:
            sec += f" ({fields['section_title']})"
        parts.append(sec)
    parts.append(
        f"printed p. {fields['printed_page']}" if fields["printed_page"]
        else "printed page not recorded"
    )
    parts.append(
        f"PDF page index {fields['pdf_page_index']}" if fields["pdf_page_index"] is not None
        else "PDF page index not recorded"
    )
    if fields["artifacts"]:
        parts.append("; ".join(fields["artifacts"]))
    fields["citation"] = " — ".join(parts)
    return fields


def claim_citations(graph: Graph, claim: URIRef) -> List[Dict[str, Any]]:
    """Assemble every citation supporting one claim."""
    return [
        assemble_citation(graph, span)
        for span in sorted(graph.objects(claim, EV.supportedByEvidence), key=str)
        if (span, EV.spanOnPage, None) in graph
    ]


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


@dataclass
class QueryResult:
    number: int
    title: str
    sparql: Optional[str]
    rows: List[Dict[str, Any]]
    note: str = ""


def q1(g: Graph) -> QueryResult:
    """All alternatives that can realise a specified function."""
    sparql = PREFIX_BLOCK + """
    SELECT ?alternative ?label ?behavior WHERE {
        ?alternative a mdcore:DesignAlternative ;
                     rdfs:label ?label ;
                     mdcore:performsFunction mech:TransmitTorqueShaftToHub .
        OPTIONAL { ?alternative mdcore:enablesBehavior ?behavior }
    } ORDER BY ?label
    """
    rows: Dict[str, Dict[str, Any]] = {}
    for r in g.query(sparql):
        key = short(r.alternative)
        rows.setdefault(key, {"alternative": key, "label": str(r.label), "behaviors": []})
        if r.behavior is not None:
            rows[key]["behaviors"].append(short(r.behavior))
    return QueryResult(
        1, "Alternatives that can realise mech:TransmitTorqueShaftToHub", sparql,
        sorted(rows.values(), key=lambda x: x["label"]),
        "Entry point for a designer who knows the required function but not the element name.",
    )


def q2(g: Graph) -> QueryResult:
    """Alternatives that satisfy a function under a specified operating context."""
    sparql = PREFIX_BLOCK + """
    SELECT ?alternative ?label ?conclusion ?assessment WHERE {
        ?assessment a mdcore:SubstitutionAssessment ;
                    mdcore:functionBeingPreserved mech:TransmitTorqueShaftToHub ;
                    mdcore:assessmentContext mdkg:ctx-axial-slide-under-torque ;
                    mdcore:candidateAlternative ?alternative ;
                    mdcore:assessmentConclusion ?conclusion .
        ?alternative rdfs:label ?label .
    } ORDER BY ?label
    """
    rows = [
        {
            "alternative": short(r.alternative), "label": str(r.label),
            "verdict_in_this_context": short(r.conclusion), "assessment": short(r.assessment),
        }
        for r in g.query(sparql)
    ]
    return QueryResult(
        2, "Alternatives assessed for torque transmission WHERE THE HUB MUST SLIDE UNDER TORQUE",
        sparql, rows,
        "Same function as query 1, but the context filters the answer: co-function is not enough.",
    )


def q3(g: Graph) -> QueryResult:
    """All failure modes associated with an alternative."""
    sparql = PREFIX_BLOCK + """
    SELECT DISTINCT ?failureMode ?fmLabel ?via WHERE {
        {
            ?assessment mdcore:candidateAlternative melem:PressFitConnectionAlternative ;
                        mdcore:introducedFailureMode ?failureMode .
            BIND("introduced by substituting in" AS ?via)
        } UNION {
            ?claim ev:claimAbout melem:PressFitConnectionAlternative ;
                   ev:claimAbout ?failureMode .
            ?failureMode a mdcore:FailureMode .
            BIND("asserted by a source claim" AS ?via)
        }
        OPTIONAL { ?failureMode rdfs:label ?fmLabel }
    }
    """
    rows = [
        {"failure_mode": short(r.failureMode), "label": str(r.fmLabel) if r.fmLabel else None,
         "route": str(r.via)}
        for r in g.query(sparql)
    ]
    return QueryResult(
        3, "Failure modes associated with melem:PressFitConnectionAlternative", sparql, rows,
        "Failure modes reach an alternative by two routes: source claims and substitution assessments.",
    )


def q4(g: Graph) -> QueryResult:
    """Calculations, inspections or tests required to verify an alternative."""
    sparql = PREFIX_BLOCK + """
    SELECT DISTINCT ?method ?methodLabel ?recommended ?procSpecified ?critSpecified ?authority WHERE {
        ?assessment mdcore:candidateAlternative melem:PressFitConnectionAlternative ;
                    mdcore:requiredVerification ?method .
        OPTIONAL { ?method rdfs:label ?methodLabel }
        OPTIONAL { ?method mdcore:testRecommended ?recommended }
        OPTIONAL { ?method mdcore:testProcedureSpecified ?procSpecified }
        OPTIONAL { ?method mdcore:acceptanceCriterionSpecified ?critSpecified }
        OPTIONAL { ?method mdcore:requiresExternalAuthority ?authority }
    } ORDER BY ?method
    """
    rows: Dict[str, Dict[str, Any]] = {}
    for r in g.query(sparql):
        key = short(r.method)
        row = rows.setdefault(key, {
            "method": key,
            "label": str(r.methodLabel) if r.methodLabel else None,
            "test_recommended": bool(r.recommended) if r.recommended is not None else None,
            "procedure_specified": bool(r.procSpecified) if r.procSpecified is not None else None,
            "acceptance_criterion_specified": bool(r.critSpecified) if r.critSpecified is not None else None,
            "external_authority_required": [],
        })
        if r.authority is not None:
            row["external_authority_required"].append(short(r.authority))
    for row in rows.values():
        row["external_authority_required"] = sorted(set(row["external_authority_required"]))
    return QueryResult(
        4, "Verification required before adopting melem:PressFitConnectionAlternative", sparql,
        sorted(rows.values(), key=lambda x: x["method"]),
        "Note the explicit false values: a recommended test whose procedure the books never defined.",
    )


def q5(g: Graph) -> QueryResult:
    """Compare two alternatives against a set of requirements."""
    sparql = PREFIX_BLOCK + """
    SELECT ?alternative ?altLabel ?criterion ?level ?provenance ?statement WHERE {
        VALUES ?alternative { melem:InvoluteSplineConnection melem:PressFitConnectionAlternative
                              melem:SetscrewConnection }
        ?evaluation mdcore:evaluatesAlternative ?alternative ;
                    mdcore:againstCriterion ?criterion ;
                    mdcore:evaluationLevel ?level ;
                    mdcore:valueProvenance ?provenance .
        OPTIONAL { ?evaluation mdcore:analystNote ?statement }
        ?alternative rdfs:label ?altLabel .
    } ORDER BY ?altLabel ?criterion
    """
    rows = [
        {
            "alternative": str(r.altLabel), "criterion": short(r.criterion),
            "level": short(r.level), "value_provenance": short(r.provenance),
            "statement": textwrap.shorten(str(r.statement), 150) if r.statement else None,
        }
        for r in g.query(sparql)
    ]
    return QueryResult(
        5, "Three alternatives compared against the requirements they were evaluated on", sparql, rows,
        "Every level carries its value provenance, so a book's wording is never confused with an inference.",
    )


def q6(g: Graph) -> QueryResult:
    """Determine the substitution state of a candidate against a baseline."""
    sparql = PREFIX_BLOCK + """
    SELECT ?assessment ?candLabel ?baseLabel ?contextLabel ?conclusion ?confidence ?review WHERE {
        ?assessment a mdcore:SubstitutionAssessment ;
                    mdcore:candidateAlternative ?cand ;
                    mdcore:baselineAlternative ?base ;
                    mdcore:assessmentContext ?context ;
                    mdcore:assessmentConclusion ?conclusion .
        OPTIONAL { ?assessment mdcore:confidence ?confidence }
        OPTIONAL { ?assessment mdcore:reviewStatus ?review }
        ?cand rdfs:label ?candLabel . ?base rdfs:label ?baseLabel .
        ?context rdfs:label ?contextLabel .
    } ORDER BY ?assessment
    """
    rows = [
        {
            "assessment": short(r.assessment),
            "candidate": str(r.candLabel), "baseline": str(r.baseLabel),
            "context": str(r.contextLabel), "conclusion": short(r.conclusion),
            "confidence": float(r.confidence) if r.confidence is not None else None,
            "review_status": short(r.review) if r.review is not None else None,
        }
        for r in g.query(sparql)
    ]
    return QueryResult(
        6, "Every substitution verdict, with its context", sparql, rows,
        "SA-001 and SA-006 are the same pair in the same context, assessed both ways, and disagree. "
        "That asymmetry is the model working as intended.",
    )


def q7(g: Graph) -> QueryResult:
    """Return the exact evidence for a design recommendation."""
    target = URIRef("https://w3id.org/mdkg/source/mott6#c-0044")
    rows: List[Dict[str, Any]] = []
    statement = g.value(target, EV.normalizedStatement)
    rows.append({
        "claim": short(target),
        "normalized_statement": str(statement) if statement else None,
        "review_status": short(g.value(target, MDCORE.reviewStatus)),
        "citations": claim_citations(g, target),
    })
    for claim in g.subjects(EV.claimAbout, URIRef("https://w3id.org/mdkg/machine-elements#StraightSidedSplineConnection")):
        if g.value(claim, EV.normalizedStatement) is None:
            continue
        rows.append({
            "claim": short(claim),
            "normalized_statement": textwrap.shorten(str(g.value(claim, EV.normalizedStatement)), 200),
            "review_status": short(g.value(claim, MDCORE.reviewStatus)),
            "citations": claim_citations(g, claim),
        })
    return QueryResult(
        7, "Exact evidence behind a recommendation, assembled from stored fields", None, rows,
        "Book, edition, chapter, section, printed page, PDF page index and any equation/table/figure. "
        "Assembled programmatically; never composed by a model.",
    )


def q8(g: Graph) -> QueryResult:
    """Claims that appear in both books."""
    sparql = PREFIX_BLOCK + """
    SELECT ?alignment ?type ?concept ?claimA ?claimB WHERE {
        ?alignment a ev:ClaimAlignment ;
                   ev:alignmentType ?type ;
                   ev:sourceClaimA ?claimA ;
                   ev:sourceClaimB ?claimB .
        OPTIONAL { ?alignment ev:commonConcept ?concept }
        FILTER (?type IN (ev:Agrees, ev:ExactMatch, ev:CloseMatch))
    } ORDER BY ?alignment
    """
    rows = [
        {
            "alignment": short(r.alignment), "type": short(r.type),
            "common_concept": str(r.concept) if r.concept else None,
            "mott6_claim": short(r.claimA), "shigley10_claim": short(r.claimB),
        }
        for r in g.query(sparql)
    ]
    return QueryResult(
        8, "Topics on which the two books agree", sparql, rows,
        "Agreement is asserted by an alignment individual; the two claims stay separate.",
    )


def q9(g: Graph) -> QueryResult:
    """Claims where the books differ in terminology, assumptions, scope or conclusion."""
    sparql = PREFIX_BLOCK + """
    SELECT ?alignment ?type ?concept ?claimA ?claimB ?conditions ?assumptions ?note WHERE {
        ?alignment a ev:ClaimAlignment ;
                   ev:alignmentType ?type ;
                   ev:sourceClaimA ?claimA ;
                   ev:sourceClaimB ?claimB .
        OPTIONAL { ?alignment ev:commonConcept ?concept }
        OPTIONAL { ?alignment ev:differingConditions ?conditions }
        OPTIONAL { ?alignment ev:differingAssumptions ?assumptions }
        OPTIONAL { ?alignment mdcore:analystNote ?note }
        FILTER (?type IN (ev:DiffersInScope, ev:DiffersInAssumption, ev:DiffersInTerminology,
                          ev:ConflictingUsage, ev:Contradicts, ev:Unresolved, ev:NotComparable))
    } ORDER BY ?alignment
    """
    rows = [
        {
            "alignment": short(r.alignment), "type": short(r.type),
            "common_concept": str(r.concept) if r.concept else None,
            "mott6_claim": short(r.claimA), "shigley10_claim": short(r.claimB),
            "differing_conditions": textwrap.shorten(str(r.conditions), 200) if r.conditions else None,
            "differing_assumptions": textwrap.shorten(str(r.assumptions), 200) if r.assumptions else None,
            "analyst_note": textwrap.shorten(str(r.note), 220) if r.note else None,
        }
        for r in g.query(sparql)
    ]
    return QueryResult(
        9, "Where the books differ, and how", sparql, rows,
        "Differences are preserved with their reasons. Nothing here has been reconciled.",
    )


def q10(g: Graph) -> QueryResult:
    """Ontology classes and rules that lack supporting evidence."""
    sparql = PREFIX_BLOCK + """
    SELECT ?alternative ?label WHERE {
        ?alternative a mdcore:DesignAlternative ; rdfs:label ?label .
        FILTER NOT EXISTS { ?claim ev:claimAbout ?alternative }
        FILTER NOT EXISTS { ?a mdcore:candidateAlternative ?alternative }
        FILTER NOT EXISTS { ?a2 mdcore:baselineAlternative ?alternative }
    } ORDER BY ?label
    """
    unsupported_alts = [
        {"kind": "DesignAlternative", "iri": short(r.alternative), "label": str(r.label),
         "status": "no claim and no assessment references it"}
        for r in g.query(sparql)
    ]
    rule_sparql = PREFIX_BLOCK + """
    SELECT ?rule ?label ?analystAuthored WHERE {
        ?rule a ?cls ; rdfs:label ?label ; mdcore:ruleIsAnalystAuthored ?analystAuthored .
        VALUES ?cls { mdcore:SelectionRule mdcore:SubstitutionRule mdcore:VerificationRule }
        FILTER NOT EXISTS { ?rule mdcore:ruleDerivedFromClaim ?c }
    } ORDER BY ?rule
    """
    unsupported_rules = [
        {"kind": "DesignRule", "iri": short(r.rule), "label": str(r.label),
         "status": ("declared analyst-authored (permitted)" if bool(r.analystAuthored)
                    else "NO claim and NOT declared analyst-authored (invalid)")}
        for r in g.query(rule_sparql)
    ]
    return QueryResult(
        10, "Concepts and rules with no supporting evidence", sparql,
        unsupported_alts + unsupported_rules,
        "An expansion worklist. Rules with no cited claim are legitimate only when they "
        "declare themselves analyst-authored.",
    )


QUERIES: Dict[int, Callable[[Graph], QueryResult]] = {
    1: q1, 2: q2, 3: q3, 4: q4, 5: q5, 6: q6, 7: q7, 8: q8, 9: q9, 10: q10,
}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render(result: QueryResult) -> str:
    lines = [
        "",
        "=" * 92,
        f"QUERY {result.number}: {result.title}",
        "=" * 92,
    ]
    if result.note:
        lines.append(textwrap.fill(result.note, 92, initial_indent="  ", subsequent_indent="  "))
        lines.append("")
    if not result.rows:
        lines.append("  (no results)")
        return "\n".join(lines)

    for i, row in enumerate(result.rows, 1):
        lines.append(f"  [{i}]")
        for key, value in row.items():
            if key == "citations":
                for c in value:
                    lines.append(f"      CITATION: {c['citation']}")
                    lines.append(f"                text integrity: {c['text_integrity']}; "
                                 f"bbox: {c['bounding_box']}; span: {c['span_id']}")
                continue
            if value in (None, [], ""):
                rendered = "—"
            elif isinstance(value, list):
                rendered = ", ".join(str(v) for v in value)
            else:
                rendered = str(value)
            lines.append(f"      {key:32s} {textwrap.shorten(rendered, 220)}")
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--query", type=int, choices=sorted(QUERIES), help="run one query only")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--show-sparql", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s: %(message)s")

    with args.config.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    full = REPO_ROOT / config["paths"]["build_dir"] / "mdkg-full.ttl"
    if not full.exists():
        raise SystemExit(f"{full} missing; run scripts/build_ontology.py first")
    graph = Graph()
    graph.parse(full, format="turtle")

    selected = [args.query] if args.query else sorted(QUERIES)
    results = [QUERIES[n](graph) for n in selected]

    if args.format == "json":
        print(json.dumps(
            [{"number": r.number, "title": r.title, "note": r.note, "rows": r.rows}
             for r in results],
            indent=2, ensure_ascii=False, default=str,
        ))
        return 0

    for result in results:
        print(render(result))
        if args.show_sparql and result.sparql:
            print("  SPARQL:")
            print(textwrap.indent(result.sparql.strip(), "    "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
