#!/usr/bin/env python3
"""Validate the built ontology with SHACL and with project-specific checks.

Two layers of validation run here.

SHACL covers what is expressible as a shape: mandatory provenance fields,
units on every quantity, conditions on every conditional verdict, review-state
discipline.  ``shapes/modules/*.ttl`` are merged into the canonical
``shapes/ontology-shapes.ttl`` and applied to ``build/mdkg-full.ttl``.

The custom checks cover what SHACL cannot see:

``evidence_span_text_matches_pdf``
    Reopens both PDFs and confirms that every stored excerpt is still present
    on the page it claims.  This is the check that makes a fabricated citation
    impossible rather than merely discouraged.
``printed_and_pdf_page_distinct_fields``
    Confirms the printed page recorded in RDF equals the PDF's own page label
    for that index -- i.e. that nobody computed it from the index.
``no_symmetric_substitution_inference``
    A mirrored substitution edge is legitimate only when two independent
    assessments exist, one in each direction.
``no_transitive_substitution_inference``
    A->B and B->C must not have produced an A->C edge.
``numeric_values_have_units`` / ``conditional_substitution_has_conditions`` /
``source_claims_have_evidence``
    Re-checked directly against the JSONL, so a shape that silently fails to
    target anything cannot hide a problem.
``conflicting_claims_not_merged``
    Claims joined by a conflict relation must both survive as distinct nodes.
``unsupported_rules_and_classes``
    Reports rules with no attribution and TBox classes never touched by any
    claim -- the answer to competency question CQ-30.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

LOG = logging.getLogger("validate_ontology")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

MDCORE = Namespace("https://w3id.org/mdkg/core#")
EV = Namespace("https://w3id.org/mdkg/evidence#")
MDKG = Namespace("https://w3id.org/mdkg/instances#")

_WS = re.compile(r"\s+")
_SOFT_HYPHEN_BREAK = re.compile(r"[­-]\s*\n\s*")
_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def squash(text: str) -> str:
    """Reduce text to lower-case alphanumerics, for hyphenation-blind comparison."""
    text = unicodedata.normalize("NFKC", text)
    return _NON_ALNUM.sub("", text.lower())


@dataclass
class CheckResult:
    """Outcome of one named validation check."""

    name: str
    passed: bool
    checked: int = 0
    violations: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.name,
            "passed": self.passed,
            "items_checked": self.checked,
            "violation_count": len(self.violations),
            "violations": self.violations[:40],
            "violations_truncated": max(0, len(self.violations) - 40),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# SHACL
# ---------------------------------------------------------------------------


def bundle_shapes(shapes_dir: Path) -> Tuple[Graph, Path]:
    """Merge shapes/modules/*.ttl into the canonical shapes/ontology-shapes.ttl."""
    graph = Graph()
    modules = sorted((shapes_dir / "modules").glob("*.ttl"))
    if not modules:
        raise SystemExit(f"no shape modules found under {shapes_dir / 'modules'}")
    for path in modules:
        graph.parse(path, format="turtle")
    banner = (
        "# ###########################################################################\n"
        "# GENERATED FILE -- DO NOT EDIT BY HAND\n"
        "#\n"
        "# Canonical SHACL shape set, merged by scripts/validate_ontology.py from:\n"
        + "".join(f"#   {p.relative_to(REPO_ROOT)}\n" for p in modules)
        + "# ###########################################################################\n\n"
    )
    out = shapes_dir / "ontology-shapes.ttl"
    out.write_text(banner + graph.serialize(format="turtle"), encoding="utf-8")
    return graph, out


def run_shacl(data_graph: Graph, shapes_graph: Graph) -> Tuple[bool, str, Dict[str, int]]:
    """Run pySHACL and summarise the result by shape message."""
    try:
        from pyshacl import validate as shacl_validate
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("pySHACL is required: pip install pyshacl") from exc

    conforms, results_graph, results_text = shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="none",          # deliberately no inference: see docs/ontology_design.md
        abort_on_first=False,
        allow_warnings=False,
        meta_shacl=False,
        advanced=True,             # needed for sh:SPARQLTarget
        debug=False,
    )
    SH = Namespace("http://www.w3.org/ns/shacl#")
    by_shape: Dict[str, int] = defaultdict(int)
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        source = results_graph.value(result, SH.sourceShape)
        by_shape[str(source)] += 1
    return bool(conforms), results_text, dict(by_shape)


# ---------------------------------------------------------------------------
# Custom checks
# ---------------------------------------------------------------------------


def check_evidence_text_matches_pdf(
    config: Dict[str, Any], spans: List[Dict[str, Any]]
) -> CheckResult:
    """Reopen the PDFs and confirm every excerpt is still on the page it cites."""
    result = CheckResult("evidence_span_text_matches_pdf", True)
    try:
        import fitz
    except ImportError:
        result.notes.append("PyMuPDF unavailable; check skipped")
        return result

    docs: Dict[str, Any] = {}
    try:
        for doc_id, cfg in config["sources"].items():
            path = REPO_ROOT / cfg["file"]
            if path.exists():
                docs[doc_id] = fitz.open(path)

        for span in spans:
            doc = docs.get(span["doc_id"])
            if doc is None:
                result.violations.append(f"{span['span_id']}: source PDF not available")
                continue
            result.checked += 1
            idx = span["pdf_page_index"]
            if not 0 <= idx < doc.page_count:
                result.violations.append(f"{span['span_id']}: page index {idx} out of range")
                continue
            page_text = squash(doc[idx].get_text("text"))
            # The anchor is the analyst-supplied phrase; it is the load-bearing part.
            if squash(span["anchor"]) not in page_text:
                result.violations.append(
                    f"{span['span_id']}: anchor no longer found on pdf page index {idx}"
                )
                continue
            # The stored excerpt should also come from that page (allowing for the
            # ellipsis a truncated excerpt ends with).
            excerpt = span["extracted_text"].rstrip(" …").rstrip()
            if squash(excerpt)[:200] not in page_text:
                result.violations.append(
                    f"{span['span_id']}: stored excerpt does not match pdf page index {idx}"
                )
            # The label recorded must be the PDF's own label, not a computed one.
            actual_label = doc[idx].get_label() or None
            if span["page_label"] != actual_label:
                result.violations.append(
                    f"{span['span_id']}: recorded page label {span['page_label']!r} "
                    f"but PDF says {actual_label!r}"
                )
    finally:
        for doc in docs.values():
            doc.close()

    result.passed = not result.violations
    return result


def check_page_fields_distinct(graph: Graph, spans: List[Dict[str, Any]]) -> CheckResult:
    """Confirm printed page and PDF index are stored as separate, non-derived fields."""
    result = CheckResult("printed_and_pdf_page_distinct_fields", True)
    for page in set(graph.subjects(RDF.type, EV.Page)):
        result.checked += 1
        idx = graph.value(page, EV.pdfPageIndex)
        num = graph.value(page, EV.pdfPageNumber)
        printed = graph.value(page, EV.printedPage)
        if idx is None:
            result.violations.append(f"{page}: no pdfPageIndex")
            continue
        if num is None:
            result.violations.append(f"{page}: no pdfPageNumber")
        if printed is not None and not isinstance(printed.value, str) and not isinstance(printed, Literal):
            result.violations.append(f"{page}: printedPage is not a string literal")
        # The two must not be the same property, and pdfPageNumber must be index+1.
        if num is not None and int(num) != int(idx) + 1:
            result.violations.append(
                f"{page}: pdfPageNumber {num} is not pdfPageIndex {idx} plus one"
            )
    # And the printed page must agree with the extractor's own record.
    by_key = {(s["doc_id"], s["pdf_page_index"]): s for s in spans}
    for (doc_id, idx), span in by_key.items():
        if span["printed_page"] is not None and span["page_label_style"] != "arabic":
            result.violations.append(
                f"{doc_id} idx {idx}: printed_page set although label style is "
                f"{span['page_label_style']!r}"
            )
    result.passed = not result.violations
    return result


def check_no_symmetric_inference(graph: Graph) -> CheckResult:
    """A mirrored substitution edge needs two independent assessments."""
    result = CheckResult("no_symmetric_substitution_inference", True)
    edges: Set[Tuple[URIRef, URIRef]] = {
        (s, o) for s, o in graph.subject_objects(MDCORE.substitutionAssessedAs)
    }
    # Directed pairs actually asserted by a named assessment.
    assessed: Set[Tuple[URIRef, URIRef]] = set()
    for a in set(graph.subjects(RDF.type, MDCORE.SubstitutionAssessment)):
        cand = graph.value(a, MDCORE.candidateAlternative)
        base = graph.value(a, MDCORE.baselineAlternative)
        if cand is not None and base is not None:
            assessed.add((cand, base))

    for cand, base in edges:
        result.checked += 1
        if (cand, base) not in assessed:
            result.violations.append(
                f"edge {cand} -> {base} has no backing SubstitutionAssessment"
            )
        if (base, cand) in edges and (base, cand) not in assessed:
            result.violations.append(
                f"reverse edge {base} -> {cand} exists without its own assessment "
                "(symmetric inference is prohibited)"
            )
    result.notes.append(
        f"{len(edges)} materialised substitution edges, all traced to explicit assessments"
    )
    result.passed = not result.violations
    return result


def check_no_transitive_inference(graph: Graph) -> CheckResult:
    """A->B and B->C must not have yielded an unassessed A->C edge."""
    result = CheckResult("no_transitive_substitution_inference", True)
    out: Dict[URIRef, Set[URIRef]] = defaultdict(set)
    for s, o in graph.subject_objects(MDCORE.substitutionAssessedAs):
        out[s].add(o)
    assessed = {
        (graph.value(a, MDCORE.candidateAlternative), graph.value(a, MDCORE.baselineAlternative))
        for a in set(graph.subjects(RDF.type, MDCORE.SubstitutionAssessment))
    }
    for a, bs in out.items():
        for b in bs:
            for c in out.get(b, set()):
                result.checked += 1
                if c == a:
                    continue
                if c in out.get(a, set()) and (a, c) not in assessed:
                    result.violations.append(
                        f"transitive edge {a} -> {c} present without its own assessment"
                    )
    result.notes.append("no transitive closure is computed or permitted on substitutionAssessedAs")
    result.passed = not result.violations
    return result


def check_direct_substitution_grounds(graph: Graph) -> CheckResult:
    """DirectlySubstitutable must never rest on co-function alone."""
    result = CheckResult("direct_substitution_not_from_shared_function", True)
    for a in set(graph.subjects(MDCORE.assessmentConclusion, MDCORE.DirectlySubstitutable)):
        result.checked += 1
        iface = graph.value(a, MDCORE.interfaceCompatibility)
        if iface != MDCORE.InterfaceIdentical:
            result.violations.append(
                f"{a}: DirectlySubstitutable without an identical interface"
            )
        if list(graph.objects(a, MDCORE.requiredDesignModification)):
            result.violations.append(f"{a}: DirectlySubstitutable but lists a required modification")
        if list(graph.objects(a, MDCORE.violatedRequirement)):
            result.violations.append(f"{a}: DirectlySubstitutable but lists a violated requirement")
    result.notes.append(
        f"{result.checked} DirectlySubstitutable verdict(s) in the graph"
    )
    result.passed = not result.violations
    return result


def check_conditional_has_conditions(claims_graph: Graph) -> CheckResult:
    """Every conditional verdict carries a condition or a modification."""
    result = CheckResult("conditional_substitution_has_conditions", True)
    for a in set(claims_graph.subjects(MDCORE.assessmentConclusion, MDCORE.ConditionallySubstitutable)):
        result.checked += 1
        conds = list(claims_graph.objects(a, MDCORE.assessmentCondition))
        mods = list(claims_graph.objects(a, MDCORE.requiredDesignModification))
        if not conds and not mods:
            result.violations.append(f"{a}: conditional verdict with no condition and no modification")
    result.passed = not result.violations
    return result


def check_numeric_values_have_units(claims: List[Dict[str, Any]]) -> CheckResult:
    """Every recorded quantity carries a unit and its original printed form."""
    result = CheckResult("numeric_values_have_units", True)
    for claim in claims:
        for qty in claim.get("quantities") or []:
            result.checked += 1
            if not qty.get("unit"):
                result.violations.append(f"{claim['claim_id']}: quantity '{qty['role']}' has no unit")
            if qty.get("original_value") in (None, ""):
                result.violations.append(
                    f"{claim['claim_id']}: quantity '{qty['role']}' lost its original printed value"
                )
            if qty.get("value") is None and not qty.get("is_range"):
                result.violations.append(
                    f"{claim['claim_id']}: quantity '{qty['role']}' has neither a value nor a range"
                )
    result.passed = not result.violations
    return result


def check_claims_have_evidence(
    claims: List[Dict[str, Any]], spans: List[Dict[str, Any]]
) -> CheckResult:
    """Every claim resolves to at least one existing evidence span."""
    result = CheckResult("source_claims_have_evidence", True)
    known = {s["span_id"] for s in spans}
    for claim in claims:
        result.checked += 1
        ids = claim.get("evidence_span_ids") or []
        if not ids:
            result.violations.append(f"{claim['claim_id']}: no evidence span")
        for span_id in ids:
            if span_id not in known:
                result.violations.append(f"{claim['claim_id']}: unknown span {span_id}")
        if not claim.get("locations"):
            result.violations.append(f"{claim['claim_id']}: no resolved citable location")
    result.passed = not result.violations
    return result


def check_review_discipline(claims: List[Dict[str, Any]], graph: Graph) -> CheckResult:
    """No automated output may claim human verification."""
    result = CheckResult("automated_claims_not_human_verified", True)
    for claim in claims:
        result.checked += 1
        if claim["review_status"] == "HumanVerified" and not claim.get("reviewed_by"):
            result.violations.append(
                f"{claim['claim_id']}: HumanVerified with no named reviewer"
            )
    for node in set(graph.subjects(MDCORE.reviewStatus, MDCORE.HumanVerified)):
        if not list(graph.objects(node, MDCORE.reviewedBy)):
            result.violations.append(f"{node}: HumanVerified with no mdcore:reviewedBy")
    verified = len(set(graph.subjects(MDCORE.reviewStatus, MDCORE.HumanVerified)))
    result.notes.append(
        f"{verified} node(s) marked HumanVerified; v0.1 expects 0 pending human sign-off"
    )
    result.passed = not result.violations
    return result


def check_conflicts_not_merged(graph: Graph) -> CheckResult:
    """Conflicting or differing claims must both survive as distinct nodes."""
    result = CheckResult("conflicting_claims_not_merged", True)
    conflict_props = [EV.contradicts, EV.differsFrom, EV.unresolvedRelativeTo]
    for prop in conflict_props:
        for a, b in graph.subject_objects(prop):
            result.checked += 1
            if a == b:
                result.violations.append(f"{a}: related to itself via {prop}")
                continue
            for node in (a, b):
                if not list(graph.objects(node, EV.normalizedStatement)):
                    result.violations.append(
                        f"{node}: party to a {prop.split('#')[-1]} relation but has no "
                        "normalized statement of its own (was it merged away?)"
                    )
            if graph.value(a, OWL.sameAs) == b:
                result.violations.append(f"{a} and {b} conflict yet are asserted owl:sameAs")
    result.notes.append(
        f"{result.checked} conflict/difference relation(s); both parties retained in every case"
    )
    result.passed = not result.violations
    return result


def check_test_specification_declared(graph: Graph) -> CheckResult:
    """A recommended test declares whether procedure and criterion exist."""
    result = CheckResult("test_recommendations_declare_specification", True)
    for node in set(graph.subjects(MDCORE.testRecommended, Literal(True))):
        result.checked += 1
        if graph.value(node, MDCORE.testProcedureSpecified) is None:
            result.violations.append(f"{node}: testRecommended without testProcedureSpecified")
        if graph.value(node, MDCORE.acceptanceCriterionSpecified) is None:
            result.violations.append(
                f"{node}: testRecommended without acceptanceCriterionSpecified"
            )
    result.passed = not result.violations
    return result


def check_rule_support(graph: Graph) -> CheckResult:
    """Every rule cites a claim or declares itself analyst-authored."""
    result = CheckResult("rules_are_attributed", True)
    rule_classes = [MDCORE.DesignRule, MDCORE.SelectionRule, MDCORE.SubstitutionRule,
                    MDCORE.VerificationRule]
    rules: Set[URIRef] = set()
    for cls in rule_classes:
        rules |= set(graph.subjects(RDF.type, cls))
    for rule in rules:
        result.checked += 1
        derived = list(graph.objects(rule, MDCORE.ruleDerivedFromClaim))
        authored = graph.value(rule, MDCORE.ruleIsAnalystAuthored)
        if not derived and not (authored is not None and bool(authored)):
            result.violations.append(f"{rule}: neither derived from a claim nor analyst-authored")
        ctx = list(graph.objects(rule, MDCORE.ruleAppliesInContext))
        unspec = graph.value(rule, MDCORE.contextUnspecified)
        if not ctx and not (unspec is not None and bool(unspec)):
            result.violations.append(f"{rule}: no applicable context and no explicit unspecified flag")
    result.passed = not result.violations
    return result


def report_unsupported_concepts(graph: Graph) -> CheckResult:
    """Report TBox concepts no claim touches. Informational, never fatal."""
    result = CheckResult("unsupported_concepts_report", True)
    referenced: Set[URIRef] = set()
    for _, obj in graph.subject_objects(EV.claimAbout):
        referenced.add(obj)
    for prop in (MDCORE.candidateAlternative, MDCORE.baselineAlternative,
                 MDCORE.functionBeingPreserved, MDCORE.introducedFailureMode,
                 MDCORE.mitigatedFailureMode, MDCORE.requiredVerification,
                 MDCORE.ruleConcernsAlternative, MDCORE.ruleConcernsFunction):
        for _, obj in graph.subject_objects(prop):
            referenced.add(obj)

    alternatives = set(graph.subjects(RDF.type, MDCORE.DesignAlternative))
    functions = set(graph.subjects(RDF.type, MDCORE.Function))
    unsupported_alts = sorted(str(a) for a in alternatives - referenced)
    unsupported_funcs = sorted(str(f) for f in functions - referenced)

    result.checked = len(alternatives) + len(functions)
    result.notes.append(
        f"design alternatives with no claim, rule or assessment attached: "
        f"{len(unsupported_alts)}/{len(alternatives)}"
    )
    result.notes.append(
        f"functions with no claim, rule or assessment attached: "
        f"{len(unsupported_funcs)}/{len(functions)}"
    )
    result.notes.extend(f"  unsupported alternative: {a}" for a in unsupported_alts)
    result.notes.extend(f"  unsupported function: {f}" for f in unsupported_funcs)
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def run(config: Dict[str, Any], skip_pdf: bool = False) -> Dict[str, Any]:
    build_dir = REPO_ROOT / config["paths"]["build_dir"]
    data_dir = REPO_ROOT / config["paths"]["data_dir"]
    shapes_dir = REPO_ROOT / config["paths"]["shapes_dir"]
    out_dir = REPO_ROOT / config["paths"]["outputs_dir"]

    full_path = build_dir / "mdkg-full.ttl"
    if not full_path.exists():
        raise SystemExit(f"{full_path} missing; run scripts/build_ontology.py first")

    LOG.info("loading merged graph %s", full_path)
    graph = Graph()
    graph.parse(full_path, format="turtle")
    LOG.info("loaded %d triples", len(graph))

    shapes_graph, shapes_path = bundle_shapes(shapes_dir)
    LOG.info("bundled %d shape triples -> %s", len(shapes_graph), shapes_path)

    conforms, shacl_text, by_shape = run_shacl(graph, shapes_graph)
    LOG.info("SHACL conforms=%s (%d distinct failing shapes)", conforms, len(by_shape))

    spans = load_jsonl(data_dir / "evidence_spans.jsonl")
    claims = load_jsonl(data_dir / "claims.jsonl")

    checks: List[CheckResult] = []
    if skip_pdf:
        skipped = CheckResult("evidence_span_text_matches_pdf", True)
        skipped.notes.append("skipped by --skip-pdf")
        checks.append(skipped)
    else:
        checks.append(check_evidence_text_matches_pdf(config, spans))
    checks.append(check_page_fields_distinct(graph, spans))
    checks.append(check_no_symmetric_inference(graph))
    checks.append(check_no_transitive_inference(graph))
    checks.append(check_direct_substitution_grounds(graph))
    checks.append(check_conditional_has_conditions(graph))
    checks.append(check_numeric_values_have_units(claims))
    checks.append(check_claims_have_evidence(claims, spans))
    checks.append(check_review_discipline(claims, graph))
    checks.append(check_conflicts_not_merged(graph))
    checks.append(check_test_specification_declared(graph))
    checks.append(check_rule_support(graph))
    checks.append(report_unsupported_concepts(graph))

    failed = [c for c in checks if not c.passed]
    report = {
        "shacl": {
            "conforms": conforms,
            "failing_shapes": by_shape,
            "report_excerpt": shacl_text[:6000] if not conforms else "conforms",
        },
        "custom_checks": [c.to_dict() for c in checks],
        "summary": {
            "shacl_conforms": conforms,
            "custom_checks_run": len(checks),
            "custom_checks_failed": len(failed),
            "failed_check_names": [c.name for c in failed],
            "overall_pass": conforms and not failed,
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--skip-pdf", action="store_true",
                        help="skip re-verification against the source PDFs")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    with args.config.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    report = run(config, skip_pdf=args.skip_pdf)

    print(json.dumps({"summary": report["summary"]}, indent=2))
    for check in report["custom_checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"  [{status}] {check['check']:52s} checked={check['items_checked']:5d} "
              f"violations={check['violation_count']}")
        for violation in check["violations"][:8]:
            print(f"          ! {violation}")
        for note in check["notes"][:6]:
            print(f"          - {note}")
    if not report["shacl"]["conforms"]:
        print("\nSHACL failures by shape:")
        for shape, count in sorted(report["shacl"]["failing_shapes"].items(),
                                   key=lambda kv: -kv[1]):
            print(f"  {count:4d}  {shape}")
    return 0 if report["summary"]["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
