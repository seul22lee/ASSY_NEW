#!/usr/bin/env python3
"""Generate compact browser JSON datasets from the existing mdkg v0.1 sources.

This module reads **only** what the repository already produces — the merged
RDF graph, the verified evidence spans, the normalized claims, the curated
alignment and substitution YAML, the rule YAML, and the generated reports — and
projects them into per-view JSON files for ``outputs/visualizations/``.

It is a *projection*, not a second data model:

* No relationship is invented. Every edge corresponds to a triple, or to an
  explicit field in a curated YAML/JSONL record.
* No substitution edge is ever mirrored or composed. Direction comes straight
  from ``mdcore:baselineAlternative`` / ``mdcore:candidateAlternative``.
* Citation strings are produced by ``query_examples.assemble_citation`` — the
  project's existing logic — never re-implemented here.
* Where a source says nothing, the JSON carries an explicit
  ``"Not stated by the source"`` style marker rather than an empty value that a
  UI might render as a confident blank.

Output is deterministic: dictionaries are written with sorted keys, lists are
ordered by stable identifiers, and no timestamp is emitted.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from query_examples import assemble_citation, short as curie  # noqa: E402  (reuse existing logic)

LOG = logging.getLogger("build_visualization_data")
DEFAULT_CONFIG = REPO_ROOT / "config" / "config.yaml"

MDCORE = Namespace("https://w3id.org/mdkg/core#")
MECH = Namespace("https://w3id.org/mdkg/mechanical-design#")
MELEM = Namespace("https://w3id.org/mdkg/machine-elements#")
EV = Namespace("https://w3id.org/mdkg/evidence#")
ALIGN = Namespace("https://w3id.org/mdkg/alignment#")
MDKG = Namespace("https://w3id.org/mdkg/instances#")
MOTT6 = Namespace("https://w3id.org/mdkg/source/mott6#")
SHIGLEY10 = Namespace("https://w3id.org/mdkg/source/shigley10#")

SOURCE_NS = {"mott6": MOTT6, "shigley10": SHIGLEY10}

#: Explicit markers used instead of blanks, so the UI can never render an
#: absence as a confident empty value.
NOT_STATED = "Not stated by the source"
INSUFFICIENT = "Insufficient evidence"
NEEDS_AUTHORITY = "Requires external authority"
NEEDS_REVIEW = "Requires human review"


# ---------------------------------------------------------------------------
# Category assignment -- drives shape / colour / icon in the UI
# ---------------------------------------------------------------------------

#: Semantic categories. The UI pairs each with a distinct *shape and glyph* as
#: well as a colour, so no meaning depends on colour alone.
CATEGORY_ORDER = [
    "structure", "function", "behavior", "effect", "condition", "requirement",
    "failure", "verification", "decision", "substitution", "rule", "evidence",
    "claim", "alternative", "element", "family", "vocabulary", "source", "other",
]

_CATEGORY_BY_LOCAL: Dict[str, str] = {
    # structure
    "DesignedArtifact": "structure", "TechnicalSystem": "structure",
    "Assembly": "structure", "Component": "structure", "Interface": "structure",
    "GeometryFeature": "structure", "DesignFeature": "structure", "Material": "structure",
    "MechanicalArtifact": "structure", "MechanicalSystem": "structure",
    "MachineElement": "structure", "MechanicalInterface": "structure",
    # function / behavior
    "Function": "function", "FunctionDecomposition": "function",
    "Behavior": "behavior", "PhysicalEffect": "effect",
    # requirement / context
    "Requirement": "requirement", "Constraint": "requirement",
    "RequirementKind": "requirement", "ThresholdDefinition": "requirement",
    "QuantityValue": "requirement", "Unit": "requirement",
    "OperatingContext": "condition", "OperatingCondition": "condition",
    # failure / verification
    "FailureMode": "failure", "FailureMechanism": "failure", "FailureConsequence": "failure",
    "VerificationMethod": "verification", "AcceptanceCriterion": "verification",
    "ExternalAuthorityKind": "verification",
    # decision / substitution / rule
    "DesignProblem": "decision", "DesignAlternative": "decision", "CandidateSet": "decision",
    "EvaluationCriterion": "decision", "SelectionCriterion": "decision",
    "AlternativeEvaluation": "decision", "DesignDecision": "decision",
    "DecisionRationale": "decision", "TradeOff": "decision", "SatisfactionLevel": "vocabulary",
    "ValueProvenanceKind": "vocabulary",
    "SubstitutionAssessment": "substitution", "SubstitutionState": "substitution",
    "DesignModification": "substitution", "InterfaceCompatibilityLevel": "substitution",
    "DesignRule": "rule", "SelectionRule": "rule", "SubstitutionRule": "rule",
    "VerificationRule": "rule", "ReviewState": "vocabulary",
}

_CATEGORY_BY_ANCESTOR = [
    ("Function", "function"), ("Behavior", "behavior"), ("PhysicalEffect", "effect"),
    ("OperatingCondition", "condition"), ("OperatingContext", "condition"),
    ("Requirement", "requirement"), ("FailureMode", "failure"),
    ("FailureMechanism", "failure"), ("VerificationMethod", "verification"),
    ("DesignRule", "rule"), ("DesignAlternative", "alternative"),
    ("MachineElement", "element"), ("Interface", "structure"),
    ("GeometryFeature", "structure"), ("DesignFeature", "structure"),
    ("Material", "structure"), ("DesignedArtifact", "structure"),
]

_EVIDENCE_LOCALS = {
    "Book", "BookEdition", "SourceDocument", "Chapter", "Section", "Page",
    "Standard", "ManufacturerCatalog", "Evidence", "EvidenceSpan", "Equation",
    "Table", "Figure", "ExampleProblem", "DesignProcedure", "Variable",
    "Claim", "ExtractedClaim", "NormalizedClaim", "CandidateDesignRule",
    "ClaimAlignment", "ConceptAlignment", "TerminologyAlignment", "AlignmentType",
}


def local_name(iri: Any) -> str:
    text = str(iri)
    return text.rsplit("#", 1)[-1] if "#" in text else text.rsplit("/", 1)[-1]


def categorise(iri: URIRef, ancestors: Sequence[str]) -> str:
    """Assign a semantic category to a class or individual."""
    name = local_name(iri)
    if str(iri).startswith(str(EV)) or name in _EVIDENCE_LOCALS:
        return "evidence"
    if name in _CATEGORY_BY_LOCAL:
        return _CATEGORY_BY_LOCAL[name]
    for ancestor, cat in _CATEGORY_BY_ANCESTOR:
        if ancestor in ancestors:
            return cat
    return "other"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Sources:
    """Everything the generator reads, loaded once."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        data_dir = REPO_ROOT / config["paths"]["data_dir"]
        build_dir = REPO_ROOT / config["paths"]["build_dir"]
        out_dir = REPO_ROOT / config["paths"]["outputs_dir"]
        onto_dir = REPO_ROOT / config["paths"]["ontology_dir"]
        rules_dir = REPO_ROOT / config["paths"]["rules_dir"]

        LOG.info("loading merged graph")
        self.g = Graph()
        self.g.parse(build_dir / "mdkg-full.ttl", format="turtle")

        self.claims = load_jsonl(data_dir / "claims.jsonl")
        self.spans = load_jsonl(data_dir / "evidence_spans.jsonl")
        self.span_by_id = {s["span_id"]: s for s in self.spans}
        self.claim_by_id = {c["claim_id"]: c for c in self.claims}
        self.substitutions = load_yaml(data_dir / "substitutions.yaml")
        self.alignments_seed = load_yaml(data_dir / "alignments_seed.yaml")
        self.terminology = load_csv(data_dir / "terminology_alignment.csv")
        self.coverage = load_csv(data_dir / "coverage_matrix.csv")
        self.summary = json.loads((out_dir / "ontology_summary.json").read_text(encoding="utf-8"))
        report_path = out_dir / "validation_report.json"
        self.validation = (
            json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
        )
        self.rules: Dict[str, List[Dict[str, Any]]] = {}
        for path in sorted(rules_dir.glob("*.yaml")):
            self.rules[path.stem] = load_yaml(path).get("rules", [])

        self.doc_meta = {
            doc_id: json.loads((build_dir / f"{doc_id}.meta.json").read_text(encoding="utf-8"))
            for doc_id in config["sources"]
        }

        # IRI -> defining module file, by parsing each hand-authored module alone.
        self.module_of: Dict[str, str] = {}
        for group in ("core", "mechanical-design", "machine-elements"):
            for ttl in sorted((onto_dir / group).glob("*.ttl")):
                mg = Graph()
                mg.parse(ttl, format="turtle")
                rel = f"{group}/{ttl.name}"
                for subject in set(mg.subjects()):
                    if isinstance(subject, URIRef):
                        self.module_of.setdefault(str(subject), rel)

        self._ancestor_cache: Dict[str, List[str]] = {}

    # -- graph helpers -----------------------------------------------------

    def label(self, iri: URIRef, lang: str = "en") -> Optional[str]:
        for obj in self.g.objects(iri, RDFS.label):
            if isinstance(obj, Literal) and (obj.language == lang or obj.language is None):
                return str(obj)
        for obj in self.g.objects(iri, SKOS.prefLabel):
            if isinstance(obj, Literal) and (obj.language == lang or obj.language is None):
                return str(obj)
        return None

    def alt_label(self, iri: URIRef, lang: str = "ko") -> Optional[str]:
        for obj in self.g.objects(iri, SKOS.altLabel):
            if isinstance(obj, Literal) and obj.language == lang:
                return str(obj)
        return None

    def text_of(self, iri: URIRef, prop: URIRef) -> Optional[str]:
        for obj in self.g.objects(iri, prop):
            if isinstance(obj, Literal):
                return " ".join(str(obj).split())
        return None

    def ancestors(self, iri: URIRef) -> List[str]:
        """Transitive rdfs:subClassOf ancestors, as local names."""
        key = str(iri)
        if key in self._ancestor_cache:
            return self._ancestor_cache[key]
        seen: Set[str] = set()
        frontier = [iri]
        while frontier:
            current = frontier.pop()
            for parent in self.g.objects(current, RDFS.subClassOf):
                if isinstance(parent, URIRef) and str(parent) not in seen:
                    seen.add(str(parent))
                    frontier.append(parent)
        result = sorted(local_name(s) for s in seen)
        self._ancestor_cache[key] = result
        return result

    def span_iri(self, span_id: str) -> Optional[URIRef]:
        for doc_id, ns in SOURCE_NS.items():
            if span_id.startswith(doc_id + "-"):
                return ns[span_id[len(doc_id) + 1:]]
        return None

    def claim_iri(self, claim_id: str) -> Optional[URIRef]:
        for doc_id, ns in SOURCE_NS.items():
            if claim_id.startswith(doc_id + "-"):
                return ns[claim_id[len(doc_id) + 1:]]
        return None


# ---------------------------------------------------------------------------
# Node / edge construction helpers
# ---------------------------------------------------------------------------


def node(nid: str, label: str, cat: str, **extra: Any) -> Dict[str, Any]:
    data = {"id": nid, "label": label, "cat": cat}
    data.update({k: v for k, v in extra.items() if v not in (None, [], {})})
    return {"data": data}


def edge(source: str, target: str, label: str, kind: str, **extra: Any) -> Dict[str, Any]:
    eid = f"{source}~{kind}~{target}~{label}"
    data = {"id": eid, "source": source, "target": target, "label": label, "kind": kind}
    data.update({k: v for k, v in extra.items() if v not in (None, [], {})})
    return {"data": data}


def graph_doc(
    gid: str, title: str, description: str,
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]],
    legend: List[Dict[str, str]], notes: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble a graph dataset, dropping edges whose endpoints do not exist."""
    known = {n["data"]["id"] for n in nodes}
    kept, dropped = [], []
    seen_edge_ids: Set[str] = set()
    for e in edges:
        d = e["data"]
        if d["source"] not in known or d["target"] not in known:
            dropped.append(d["id"])
            continue
        if d["id"] in seen_edge_ids:
            continue
        seen_edge_ids.add(d["id"])
        kept.append(e)
    if dropped:
        LOG.warning("[%s] dropped %d dangling edge(s)", gid, len(dropped))

    degree: Counter = Counter()
    for e in kept:
        degree[e["data"]["source"]] += 1
        degree[e["data"]["target"]] += 1
    isolated = sorted(nid for nid in known if degree[nid] == 0)

    doc = {
        "meta": {
            "id": gid, "title": title, "description": description,
            "node_count": len(nodes), "edge_count": len(kept),
            "isolated_node_count": len(isolated), "isolated_nodes": isolated[:60],
            "dropped_dangling_edges": len(dropped),
            "categories": sorted({n["data"]["cat"] for n in nodes}),
            "edge_kinds": sorted({e["data"]["kind"] for e in kept}),
            "legend": legend, "notes": notes or [],
        },
        "nodes": sorted(nodes, key=lambda n: n["data"]["id"]),
        "edges": sorted(kept, key=lambda e: e["data"]["id"]),
    }
    if extra:
        doc.update(extra)
    return doc


# ---------------------------------------------------------------------------
# View A -- overview
# ---------------------------------------------------------------------------


def build_overview(src: Sources) -> Dict[str, Any]:
    s = src.summary
    tbox, abox, dist = s["tbox"], s["abox"], s["distributions"]
    mott_claims = sum(1 for c in src.claims if c["doc_id"] == "mott6")
    shig_claims = sum(1 for c in src.claims if c["doc_id"] == "shigley10")
    human_verified = sum(1 for c in src.claims if c["review_status"] == "HumanVerified")

    rule_counts = {name: len(rules) for name, rules in sorted(src.rules.items())}
    verdicts = dict(dist.get("substitution_conclusions", {}))

    validation = None
    if src.validation:
        v = src.validation
        validation = {
            "shacl_conforms": v["summary"]["shacl_conforms"],
            "custom_checks_run": v["summary"]["custom_checks_run"],
            "custom_checks_failed": v["summary"]["custom_checks_failed"],
            "failed_check_names": v["summary"]["failed_check_names"],
            "overall_pass": v["summary"]["overall_pass"],
            "checks": [
                {"check": c["check"], "passed": c["passed"],
                 "items_checked": c["items_checked"], "violations": c["violation_count"],
                 "notes": c.get("notes", [])}
                for c in v["custom_checks"]
            ],
        }

    cards = [
        {"key": "version", "label": "Ontology version", "value": src.config["project"]["version"], "group": "Project"},
        {"key": "triples", "label": "Total triples", "value": s["total_triples"], "group": "Project"},
        {"key": "classes", "label": "Classes", "value": tbox["classes"], "group": "TBox"},
        {"key": "object_properties", "label": "Object properties", "value": tbox["object_properties"], "group": "TBox"},
        {"key": "datatype_properties", "label": "Datatype properties", "value": tbox["datatype_properties"], "group": "TBox"},
        {"key": "skos_schemes", "label": "SKOS concept schemes", "value": tbox["skos_concept_schemes"], "group": "TBox"},
        {"key": "evidence_spans", "label": "Evidence spans (verified)", "value": abox["evidence_spans"], "group": "Evidence"},
        {"key": "claims", "label": "Normalized claims", "value": abox["claims"], "group": "Evidence"},
        {"key": "mott_claims", "label": "Mott 6e claims", "value": mott_claims, "group": "Evidence"},
        {"key": "shigley_claims", "label": "Shigley 10e claims", "value": shig_claims, "group": "Evidence"},
        {"key": "pages", "label": "Cited pages", "value": abox["pages"], "group": "Evidence"},
        {"key": "alternatives", "label": "Design alternatives", "value": abox["design_alternatives"], "group": "Design"},
        {"key": "substitutions", "label": "Substitution assessments", "value": len(src.substitutions["assessments"]), "group": "Design"},
        {"key": "claim_alignments", "label": "Claim alignments", "value": abox["claim_alignments"], "group": "Cross-book"},
        {"key": "terminology_alignments", "label": "Terminology alignments", "value": abox["terminology_alignments"], "group": "Cross-book"},
        {"key": "rules_total", "label": "Rules (all categories)", "value": sum(rule_counts.values()), "group": "Rules"},
        {"key": "human_verified", "label": "HumanVerified claims", "value": human_verified,
         "group": "Trust", "emphasis": "warn" if human_verified == 0 else "ok",
         "note": "Zero by design — nothing has been signed off by a human engineer."},
    ]

    return {
        "project": {
            "name": src.config["project"]["name"],
            "version": src.config["project"]["version"],
            "language": src.config["project"]["ontology_language"],
            "secondary_language": src.config["project"]["secondary_language"],
        },
        "warning": (
            "mdkg v0.1 is a pilot knowledge graph. All claims remain NeedsReview and "
            "must not be treated as validated design facts."
        ),
        "cards": cards,
        "rule_counts": rule_counts,
        "substitution_verdicts": verdicts,
        "review_states": dict(dist.get("review_states", {})),
        "text_integrity": dict(dist.get("text_integrity", {})),
        "tbox_modules": tbox.get("modules", {}),
        "validation": validation,
        "sources": [
            {
                "doc_id": doc_id,
                "title": cfg["title"],
                "authors": cfg["authors"],
                "edition": cfg["edition"],
                "publisher": cfg["publisher"],
                "year": cfg["year"],
                "file": cfg["file"],
                "sha256": src.doc_meta[doc_id]["sha256"],
                "page_count": src.doc_meta[doc_id]["page_count"],
                "math_text_reliability": cfg["math_text_reliability"],
                "claims": sum(1 for c in src.claims if c["doc_id"] == doc_id),
                "spans": sum(1 for sp in src.spans if sp["doc_id"] == doc_id),
            }
            for doc_id, cfg in src.config["sources"].items()
        ],
        "no_directly_substitutable": verdicts.get("DirectlySubstitutable", 0) == 0,
    }


# ---------------------------------------------------------------------------
# View B -- core ontology
# ---------------------------------------------------------------------------


ONTOLOGY_LEGEND = [
    {"cat": "structure", "label": "Artifact / structure", "shape": "round-rectangle", "glyph": "▭"},
    {"cat": "function", "label": "Function", "shape": "diamond", "glyph": "◆"},
    {"cat": "behavior", "label": "Behavior", "shape": "hexagon", "glyph": "⬡"},
    {"cat": "effect", "label": "Physical effect", "shape": "octagon", "glyph": "⬢"},
    {"cat": "condition", "label": "Context / condition", "shape": "rectangle", "glyph": "▬"},
    {"cat": "requirement", "label": "Requirement / quantity", "shape": "tag", "glyph": "⚑"},
    {"cat": "failure", "label": "Failure", "shape": "triangle", "glyph": "▲"},
    {"cat": "verification", "label": "Verification", "shape": "vee", "glyph": "⌄"},
    {"cat": "decision", "label": "Decision / evaluation", "shape": "pentagon", "glyph": "⬟"},
    {"cat": "substitution", "label": "Substitution", "shape": "barrel", "glyph": "⬓"},
    {"cat": "rule", "label": "Rule", "shape": "rhomboid", "glyph": "▰"},
    {"cat": "evidence", "label": "Evidence / provenance", "shape": "ellipse", "glyph": "●"},
    {"cat": "vocabulary", "label": "Controlled vocabulary", "shape": "concave-hexagon", "glyph": "◇"},
    {"cat": "other", "label": "Other", "shape": "ellipse", "glyph": "○"},
]


def _class_record(src: Sources, iri: URIRef) -> Dict[str, Any]:
    ancestors = src.ancestors(iri)
    supers = sorted(
        curie(p) for p in src.g.objects(iri, RDFS.subClassOf) if isinstance(p, URIRef)
    )
    return {
        "uri": str(iri),
        "curie": curie(iri),
        "label": src.label(iri) or local_name(iri),
        "ko": src.alt_label(iri),
        "definition": src.text_of(iri, SKOS.definition),
        "scope_note": src.text_of(iri, SKOS.scopeNote),
        "comment": src.text_of(iri, RDFS.comment),
        "module": src.module_of.get(str(iri)),
        "superclasses": supers,
        "ancestors": ancestors,
        "cat": categorise(iri, ancestors),
    }


def _property_records(src: Sources, in_scope: Set[str]) -> List[Dict[str, Any]]:
    """Object and datatype properties, with domain/range where declared."""
    out: List[Dict[str, Any]] = []
    for ptype, kind in ((OWL.ObjectProperty, "object"), (OWL.DatatypeProperty, "datatype")):
        for prop in sorted(set(src.g.subjects(RDF.type, ptype)), key=str):
            if not isinstance(prop, URIRef):
                continue
            domains = sorted(curie(d) for d in src.g.objects(prop, RDFS.domain) if isinstance(d, URIRef))
            ranges = sorted(curie(r) for r in src.g.objects(prop, RDFS.range) if isinstance(r, URIRef))
            characteristics = []
            if (prop, RDF.type, OWL.SymmetricProperty) in src.g:
                characteristics.append("Symmetric")
            if (prop, RDF.type, OWL.TransitiveProperty) in src.g:
                characteristics.append("Transitive")
            inverse = [curie(i) for i in src.g.objects(prop, OWL.inverseOf) if isinstance(i, URIRef)]
            out.append({
                "uri": str(prop), "curie": curie(prop),
                "label": src.label(prop) or local_name(prop),
                "ko": src.alt_label(prop),
                "kind": kind,
                "definition": src.text_of(prop, SKOS.definition),
                "scope_note": src.text_of(prop, SKOS.scopeNote),
                "module": src.module_of.get(str(prop)),
                "domains": domains, "ranges": ranges,
                "characteristics": characteristics,
                "inverse_of": inverse,
                "in_scope": bool({*domains, *ranges} & in_scope),
            })
    return out


def build_ontology_graph(src: Sources) -> Dict[str, Any]:
    """Level-1 core plus the evidence module: classes, subclass edges, property edges."""
    core_iris = sorted(
        {
            iri for iri in set(src.g.subjects(RDF.type, OWL.Class))
            if isinstance(iri, URIRef)
            and src.module_of.get(str(iri), "").startswith("core/")
        },
        key=str,
    )
    records = {curie(iri): _class_record(src, iri) for iri in core_iris}
    in_scope = set(records)

    nodes = [
        node(rec["curie"], rec["label"], rec["cat"],
             uri=rec["uri"], ko=rec["ko"], definition=rec["definition"],
             scopeNote=rec["scope_note"], comment=rec["comment"], module=rec["module"],
             superclasses=rec["superclasses"], nodeType="class")
        for rec in records.values()
    ]

    # Superclasses declared outside the core modules (notably skos:Concept) are
    # added as bridge nodes so the controlled-vocabulary classes are not stranded.
    # Each still corresponds to a real rdfs:subClassOf triple.
    bridges = {
        parent for rec in records.values() for parent in rec["superclasses"]
        if parent not in in_scope
    }
    for parent in sorted(bridges):
        nodes.append(node(parent, parent.split(":")[-1], "vocabulary",
                          nodeType="class", bridge=True,
                          definition="Declared outside the core modules; shown so that its "
                                     "subclasses are not stranded."))
    visible = in_scope | bridges

    edges: List[Dict[str, Any]] = []
    for rec in records.values():
        for parent in rec["superclasses"]:
            if parent in visible:
                edges.append(edge(rec["curie"], parent, "subClassOf", "taxonomy"))

    properties = _property_records(src, in_scope)
    for prop in properties:
        if prop["kind"] != "object":
            continue
        for d in prop["domains"]:
            for r in prop["ranges"]:
                if d in in_scope and r in in_scope:
                    edges.append(edge(
                        d, r, prop["label"], "property",
                        prop=prop["curie"], propUri=prop["uri"],
                        definition=prop["definition"], scopeNote=prop["scope_note"],
                        characteristics=prop["characteristics"],
                    ))

    # Per-class relation inventory for the detail panel.
    outgoing: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    incoming: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for prop in properties:
        for d in prop["domains"]:
            for r in prop["ranges"]:
                if d in in_scope:
                    outgoing[d].append({"property": prop["curie"], "label": prop["label"], "target": r})
                if r in in_scope:
                    incoming[r].append({"property": prop["curie"], "label": prop["label"], "source": d})
    for n in nodes:
        nid = n["data"]["id"]
        if outgoing.get(nid):
            n["data"]["outgoing"] = sorted(outgoing[nid], key=lambda x: (x["property"], x["target"]))
        if incoming.get(nid):
            n["data"]["incoming"] = sorted(incoming[nid], key=lambda x: (x["property"], x["source"]))

    return graph_doc(
        "ontology_graph",
        "Core ontology (Level 1)",
        "General engineering-design concepts and the evidence model. Nothing here "
        "mentions a shaft, a key or a bearing — that is the test of whether the core "
        "is genuinely reusable.",
        nodes, edges, ONTOLOGY_LEGEND,
        notes=[
            "Solid edges are rdfs:subClassOf. Dashed edges are object properties, drawn "
            "from declared domain to declared range; select one to see its definition.",
            "Every class here is ontology engineering, not source-derived content.",
        ],
        extra={"properties": sorted(properties, key=lambda p: p["curie"]),
               "modules": sorted({r["module"] for r in records.values() if r["module"]})},
    )


# ---------------------------------------------------------------------------
# View C -- mechanical design
# ---------------------------------------------------------------------------


def build_function_behavior_graph(src: Sources) -> Dict[str, Any]:
    """Mechanical extension with the Function–Behavior–Structure wiring made explicit."""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def add(iri: URIRef, cat_override: Optional[str] = None, node_type: str = "class") -> str:
        cid = curie(iri)
        if cid in seen:
            return cid
        seen.add(cid)
        rec = _class_record(src, iri)
        nodes.append(node(
            cid, rec["label"], cat_override or rec["cat"],
            uri=rec["uri"], ko=rec["ko"], definition=rec["definition"],
            scopeNote=rec["scope_note"], comment=rec["comment"], module=rec["module"],
            superclasses=rec["superclasses"], nodeType=node_type,
        ))
        return cid

    # Mechanical + machine-element classes.
    for iri in sorted(set(src.g.subjects(RDF.type, OWL.Class)), key=str):
        if not isinstance(iri, URIRef):
            continue
        module = src.module_of.get(str(iri), "")
        if module.startswith("mechanical-design/"):
            add(iri)
    for iri in sorted({MECH.MachineElement, MECH.MechanicalArtifact, MECH.MechanicalSystem}, key=str):
        add(iri)

    # Individuals: functions, behaviors, effects, failure modes, verification methods.
    individual_types = [
        (MDCORE.Function, "function"), (MDCORE.Behavior, "behavior"),
        (MDCORE.PhysicalEffect, "effect"), (MDCORE.FailureMode, "failure"),
        (MDCORE.FailureMechanism, "failure"), (MDCORE.EngineeringCalculation, "verification"),
        (MDCORE.DimensionalInspection, "verification"), (MDCORE.TorqueTest, "verification"),
    ]
    for cls, cat in individual_types:
        for iri in sorted(set(src.g.subjects(RDF.type, cls)), key=str):
            if isinstance(iri, URIRef):
                add(iri, cat_override=cat, node_type="individual")

    # Design alternatives so structure closes the FBS loop.
    for iri in sorted(set(src.g.subjects(RDF.type, MDCORE.DesignAlternative)), key=str):
        add(iri, cat_override="alternative", node_type="individual")

    # Element classes that carry a direct mdcore:hasFunction triple. Including them
    # closes the Function -> Structure side of FBS for families such as seals and
    # springs, whose functions would otherwise appear unattached.
    for iri in sorted(set(src.g.subjects(MDCORE.hasFunction, None)), key=str):
        if isinstance(iri, URIRef) and str(iri).startswith(str(MELEM)):
            add(iri, cat_override="element")

    # Level-1 superclasses of the mechanical classes are pulled in as bridge nodes,
    # so the Level-1 -> Level-2 specialisation is visible rather than the mechanical
    # subclasses appearing stranded. Each is a real rdfs:subClassOf triple.
    bridge_parents = {
        parent for n in list(nodes)
        for parent in n["data"].get("superclasses", []) if parent not in seen
    }
    for parent in sorted(bridge_parents):
        prefix, _, localp = parent.partition(":")
        ns = {"mdcore": MDCORE, "mech": MECH, "melem": MELEM, "ev": EV}.get(prefix)
        iri = ns[localp] if ns is not None else None
        seen.add(parent)
        rec = _class_record(src, iri) if iri is not None else None
        nodes.append(node(
            parent, (rec["label"] if rec else localp), (rec["cat"] if rec else "other"),
            uri=(rec["uri"] if rec else None), definition=(rec["definition"] if rec else None),
            scopeNote=(rec["scope_note"] if rec else None), nodeType="class", bridge=True,
            module=(rec["module"] if rec else None),
        ))

    # Taxonomy edges within the visible set.
    for n in list(nodes):
        for parent in n["data"].get("superclasses", []):
            if parent in seen:
                edges.append(edge(n["data"]["id"], parent, "subClassOf", "taxonomy"))

    # SKOS broader chains link the function vocabulary (transmit torque between
    # shaft and hub -> transmit torque -> transmit power).
    for s, o in src.g.subject_objects(SKOS.broader):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            a, b = curie(s), curie(o)
            if a in seen and b in seen:
                edges.append(edge(a, b, "broader", "taxonomy"))

    # FBS + failure + verification wiring, straight from the triples.
    relations = [
        (MDCORE.realizesFunction, "realizes function", "fbs"),
        (MDCORE.realizedBy, "realized by", "fbs"),
        (MDCORE.enabledBy, "enabled by", "fbs"),
        (MDCORE.enablesBehavior, "enables behavior", "fbs"),
        (MDCORE.performsFunction, "performs function", "fbs"),
        (MDCORE.hasFunction, "has function", "fbs"),
        (MDCORE.reliesOnEffect, "relies on effect", "effect"),
        (MDCORE.behaviorRequiresCondition, "requires condition", "condition"),
        (MDCORE.causedByFailureMechanism, "caused by", "failure"),
        (MDCORE.aggravatedByCondition, "aggravated by", "failure"),
        (MDCORE.addressesFailureMode, "addresses failure mode", "verification"),
    ]
    for prop, label, kind in relations:
        for s, o in src.g.subject_objects(prop):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                a, b = curie(s), curie(o)
                if a in seen and b in seen:
                    edges.append(edge(a, b, label, kind))

    # --- View E payload: function -> alternatives, fully resolved -----------
    claims_by_target: Dict[str, List[str]] = defaultdict(list)
    for claim in src.claims:
        for target in claim.get("about", []):
            claims_by_target[target].append(claim["claim_id"])

    functions: List[Dict[str, Any]] = []
    for firi in sorted(set(src.g.subjects(RDF.type, MDCORE.Function)), key=str):
        if not isinstance(firi, URIRef):
            continue
        fid = curie(firi)
        alternatives = []
        for alt in sorted(src.g.subjects(MDCORE.performsFunction, firi), key=str):
            aid = curie(alt)
            behaviors = sorted(curie(b) for b in src.g.objects(alt, MDCORE.enablesBehavior))
            elem_types = sorted(curie(e) for e in src.g.objects(alt, MELEM.usesElementType))
            alt_claims = sorted(claims_by_target.get(aid, []))
            span_ids = sorted({
                sid for cid in alt_claims for sid in src.claim_by_id[cid]["evidence_span_ids"]
            })
            docs = sorted({src.claim_by_id[cid]["doc_id"] for cid in alt_claims})
            failures, verifications, limitations = [], [], []
            for sa in src.substitutions["assessments"]:
                if sa["candidate"] != aid:
                    continue
                failures += [f["failure_mode"] for f in sa.get("introduced_failure_modes") or []]
                verifications += [v["method"] for v in sa.get("required_verification") or []]
                limitations += [
                    {"statement": d["statement"], "criterion": d["criterion"],
                     "provenance": d.get("provenance", "EngineeringInference"),
                     "assessment": sa["id"]}
                    for d in sa.get("disadvantages") or []
                ]
            alternatives.append({
                "id": aid,
                "label": src.label(alt) or local_name(alt),
                "behaviors": behaviors,
                "element_types": elem_types,
                "failure_modes": sorted(set(failures)),
                "verification": sorted(set(verifications)),
                "limitations": limitations,
                "claim_ids": alt_claims,
                "span_ids": span_ids,
                "source_books": docs,
                "claim_count": len(alt_claims),
                "span_count": len(span_ids),
            })
        functions.append({
            "id": fid,
            "label": src.label(firi) or local_name(firi),
            "pref_label": src.text_of(firi, SKOS.prefLabel),
            "ko": src.alt_label(firi),
            "definition": src.text_of(firi, SKOS.definition),
            "scope_note": src.text_of(firi, SKOS.scopeNote),
            "broader": sorted(curie(b) for b in src.g.objects(firi, SKOS.broader)),
            "alternative_count": len(alternatives),
            "alternatives": sorted(alternatives, key=lambda a: a["label"]),
        })

    return graph_doc(
        "function_behavior_graph",
        "Mechanical design — Function · Behavior · Structure",
        "The Level-2 mechanical extension. Four alternatives all perform "
        "'transmit torque between shaft and hub', but through different behaviors — "
        "and it is the behavior that decides the failure modes and the verification.",
        nodes, edges, ONTOLOGY_LEGEND,
        notes=[
            "Shared function does not imply direct substitutability.",
            "Edge kinds: taxonomy (subClassOf), fbs (function↔behavior↔structure), "
            "effect, condition, failure, verification.",
        ],
        extra={"functions": sorted(functions, key=lambda f: f["label"])},
    )


# ---------------------------------------------------------------------------
# View D -- machine element taxonomy
# ---------------------------------------------------------------------------

#: Families expanded by default; everything else starts collapsed.
DEFAULT_EXPANDED = {"melem:ConnectionElement", "melem:SupportElement"}


def build_machine_elements_graph(src: Sources) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    claims_by_target: Dict[str, List[str]] = defaultdict(list)
    for claim in src.claims:
        for target in claim.get("about", []):
            claims_by_target[target].append(claim["claim_id"])

    element_iris = sorted(
        {
            iri for iri in set(src.g.subjects(RDF.type, OWL.Class))
            if isinstance(iri, URIRef) and str(iri).startswith(str(MELEM))
        },
        key=str,
    )
    root = curie(MECH.MachineElement)
    rec_root = _class_record(src, MECH.MachineElement)
    nodes.append(node(root, rec_root["label"], "structure", uri=rec_root["uri"],
                      definition=rec_root["definition"], nodeType="class", family=root,
                      isRoot=True))

    families: Set[str] = set()
    for iri in element_iris:
        rec = _class_record(src, iri)
        cid = rec["curie"]
        is_family = "MachineElement" in [local_name(s) for s in
                                         src.g.objects(iri, RDFS.subClassOf)]
        cat = "family" if is_family else "element"
        if is_family:
            families.add(cid)
        claim_ids = sorted(claims_by_target.get(cid, []))
        span_ids = sorted({sid for c in claim_ids for sid in src.claim_by_id[c]["evidence_span_ids"]})
        nodes.append(node(
            cid, rec["label"], cat, uri=rec["uri"], ko=rec["ko"],
            definition=rec["definition"], scopeNote=rec["scope_note"],
            comment=rec["comment"], module=rec["module"],
            superclasses=rec["superclasses"], nodeType="class",
            claimIds=claim_ids, spanIds=span_ids,
            claimCount=len(claim_ids), spanCount=len(span_ids),
        ))
        for parent in rec["superclasses"]:
            edges.append(edge(cid, parent, "subClassOf", "taxonomy"))

    # Design alternatives, kept visually distinct from element classes.
    for alt in sorted(set(src.g.subjects(RDF.type, MDCORE.DesignAlternative)), key=str):
        aid = curie(alt)
        claim_ids = sorted(claims_by_target.get(aid, []))
        span_ids = sorted({sid for c in claim_ids for sid in src.claim_by_id[c]["evidence_span_ids"]})
        elem_types = sorted(curie(e) for e in src.g.objects(alt, MELEM.usesElementType))
        funcs = sorted(curie(f) for f in src.g.objects(alt, MDCORE.performsFunction))
        behs = sorted(curie(b) for b in src.g.objects(alt, MDCORE.enablesBehavior))
        failures, verifications = set(), set()
        for sa in src.substitutions["assessments"]:
            if sa["candidate"] == aid or sa["baseline"] == aid:
                failures |= {f["failure_mode"] for f in sa.get("introduced_failure_modes") or []}
                verifications |= {v["method"] for v in sa.get("required_verification") or []}
        nodes.append(node(
            aid, src.label(alt) or local_name(alt), "alternative",
            uri=str(alt), nodeType="individual", elementTypes=elem_types,
            functions=funcs, behaviors=behs,
            failureModes=sorted(failures), verification=sorted(verifications),
            claimIds=claim_ids, spanIds=span_ids,
            claimCount=len(claim_ids), spanCount=len(span_ids),
        ))
        for et in elem_types:
            edges.append(edge(aid, et, "uses element type", "realisation"))

    # Resolve each node's family by walking the subclass chain transitively.
    # Direct superclasses are not enough: melem:BallBearing -> RollingContactBearing
    # -> Bearing -> SupportElement needs three hops to reach its family.
    parent_of: Dict[str, List[str]] = {
        n["data"]["id"]: list(n["data"].get("superclasses", [])) for n in nodes
    }

    def family_of(nid: str, seen: Optional[Set[str]] = None) -> Optional[str]:
        if nid in families:
            return nid
        seen = seen or set()
        if nid in seen:
            return None
        seen.add(nid)
        for parent in parent_of.get(nid, []):
            found = family_of(parent, seen)
            if found:
                return found
        return None

    for n in nodes:
        nid = n["data"]["id"]
        if n["data"].get("isRoot"):
            continue
        fam = family_of(nid)
        # A design alternative has no superclass; it belongs to the family of the
        # element type it uses, so that collapsing a family hides it too.
        if fam is None:
            for element_type in n["data"].get("elementTypes", []):
                fam = family_of(element_type)
                if fam:
                    break
        if fam:
            n["data"]["family"] = fam

    return graph_doc(
        "machine_elements_graph",
        "Machine-element taxonomy (Level 3)",
        "Families are organised by the function they deliver, not by the chapter that "
        "describes them. Shaft/hub connections and bearings are expanded; other "
        "families start collapsed.",
        nodes, edges,
        [
            {"cat": "family", "label": "Element family (OWL class)", "shape": "round-rectangle", "glyph": "▭"},
            {"cat": "element", "label": "Element type (OWL class)", "shape": "rectangle", "glyph": "▬"},
            {"cat": "alternative", "label": "Design alternative (individual)", "shape": "pentagon", "glyph": "⬟"},
            {"cat": "structure", "label": "Taxonomy root", "shape": "round-rectangle", "glyph": "▭"},
        ],
        notes=[
            "Element types are OWL classes; design alternatives are individuals. "
            "Substitution operates on alternatives, never on element classes.",
            "Families are deliberately NOT disjoint: a setscrew both connects and fastens.",
        ],
        extra={
            "families": sorted(families),
            "default_expanded": sorted(DEFAULT_EXPANDED),
        },
    )


# ---------------------------------------------------------------------------
# Views G / K -- claims and evidence
# ---------------------------------------------------------------------------


def _citation_for(src: Sources, span_id: str) -> Dict[str, Any]:
    """Assemble a citation using the project's existing logic — never by hand."""
    iri = src.span_iri(span_id)
    if iri is None:
        return {"citation": NOT_STATED, "span_id": span_id}
    return assemble_citation(src.g, iri)


def build_evidence_graph(src: Sources) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    span_records: List[Dict[str, Any]] = []
    used_by_claims: Set[str] = {sid for c in src.claims for sid in c["evidence_span_ids"]}

    for doc_id, cfg in src.config["sources"].items():
        did = f"doc:{doc_id}"
        seen.add(did)
        meta = src.doc_meta[doc_id]
        nodes.append(node(
            did, cfg["title"], "source", nodeType="document", docId=doc_id,
            edition=cfg["edition"], authors=cfg["authors"], sha256=meta["sha256"],
            pageCount=meta["page_count"], file=cfg["file"],
            mathTextReliability=cfg["math_text_reliability"],
        ))

    for span in src.spans:
        sid = span["span_id"]
        doc_id = span["doc_id"]
        chap = span.get("chapter_number")
        sec = span.get("section_number")
        page_key = f"page:{doc_id}:{span['pdf_page_index']}"
        chap_key = f"chap:{doc_id}:{chap}" if chap else None
        sec_key = f"sec:{doc_id}:{sec}" if sec else None

        if chap_key and chap_key not in seen:
            seen.add(chap_key)
            nodes.append(node(chap_key, f"ch. {chap} — {span.get('chapter_title') or ''}".strip(" —"),
                              "evidence", nodeType="chapter", docId=doc_id,
                              chapterNumber=chap, chapterTitle=span.get("chapter_title")))
            edges.append(edge(f"doc:{doc_id}", chap_key, "has chapter", "structure"))
        if sec_key and sec_key not in seen:
            seen.add(sec_key)
            nodes.append(node(sec_key, f"sec. {sec} — {span.get('section_title') or ''}".strip(" —"),
                              "evidence", nodeType="section", docId=doc_id,
                              sectionNumber=sec, sectionTitle=span.get("section_title")))
            if chap_key:
                edges.append(edge(chap_key, sec_key, "has section", "structure"))
        if page_key not in seen:
            seen.add(page_key)
            printed = span.get("printed_page")
            nodes.append(node(
                page_key,
                f"p. {printed}" if printed else f"pdf idx {span['pdf_page_index']}",
                "evidence", nodeType="page", docId=doc_id,
                printedPage=printed, pdfPageIndex=span["pdf_page_index"],
                pdfPageNumber=span["pdf_page_number"], pageLabel=span.get("page_label"),
                pageLabelStyle=span.get("page_label_style"),
            ))
            edges.append(edge(sec_key or chap_key or f"doc:{doc_id}", page_key, "has page", "structure"))

        span_key = f"span:{sid}"
        seen.add(span_key)
        citation = _citation_for(src, sid)
        artifacts = [
            f"{a.get('kind', '?')} {a.get('number', '?')}" for a in span.get("artifact_refs") or []
        ]
        nodes.append(node(
            span_key, sid, "evidence", nodeType="span", docId=doc_id, spanId=sid,
            textIntegrity=span["text_integrity"], usedByClaims=sid in used_by_claims,
        ))
        edges.append(edge(page_key, span_key, "has span", "structure"))

        span_records.append({
            "span_id": sid,
            "doc_id": doc_id,
            "book_title": span["book_title"],
            "authors": span["authors"],
            "edition": span["edition"],
            "chapter_number": span.get("chapter_number") or NOT_STATED,
            "chapter_title": span.get("chapter_title") or NOT_STATED,
            "section_number": span.get("section_number") or NOT_STATED,
            "section_title": span.get("section_title") or NOT_STATED,
            "printed_page": span.get("printed_page") or NOT_STATED,
            "page_label": span.get("page_label"),
            "page_label_style": span.get("page_label_style"),
            "pdf_page_index": span["pdf_page_index"],
            "pdf_page_number": span["pdf_page_number"],
            "block_id": span["block_id"],
            "bbox": span["bbox"],
            "extracted_text": span["extracted_text"],
            "excerpt_truncated": span["excerpt_truncated"],
            "anchor": span["anchor"],
            "match_mode": span["match_mode"],
            "text_integrity": span["text_integrity"],
            "math_font_char_ratio": span["math_font_char_ratio"],
            "extraction_method": span["extraction_method"],
            "extraction_confidence": span["extraction_confidence"],
            "artifact_refs": span.get("artifact_refs") or [],
            "artifact_labels": artifacts,
            "note": span.get("note"),
            "topic": span["topic"],
            "citation": citation.get("citation"),
            "citation_fields": citation,
            "used_by_claims": sorted(
                c["claim_id"] for c in src.claims if sid in c["evidence_span_ids"]
            ),
        })

    integrity_counts = Counter(s["text_integrity"] for s in src.spans)
    return graph_doc(
        "evidence_graph",
        "Evidence and provenance",
        "Document → chapter → section → page → evidence span. Every span was verified "
        "against the PDF at build time.",
        nodes, edges,
        [
            {"cat": "source", "label": "Source document", "shape": "round-rectangle", "glyph": "▭"},
            {"cat": "evidence", "label": "Chapter / section / page / span", "shape": "ellipse", "glyph": "●"},
        ],
        notes=[
            "PDF page index and printed page are separate fields and neither is derived "
            "from the other.",
            "Spans marked glyph-mismapped carry text that decodes to unrelated ASCII; "
            "their extracted text must not be quoted.",
        ],
        extra={
            "spans": sorted(span_records, key=lambda s: s["span_id"]),
            "integrity_counts": dict(sorted(integrity_counts.items())),
            "unused_spans": sorted(set(src.span_by_id) - used_by_claims),
        },
    )


def build_claims_graph(src: Sources) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    claim_records: List[Dict[str, Any]] = []
    for claim in src.claims:
        cid = claim["claim_id"]
        key = f"claim:{cid}"
        seen.add(key)
        nodes.append(node(
            key, cid, "claim", nodeType="claim", docId=claim["doc_id"],
            topic=claim["topic"], reviewStatus=claim["review_status"],
            textIntegrity=claim["text_integrity"],
        ))
        for sid in claim["evidence_span_ids"]:
            skey = f"span:{sid}"
            if skey not in seen:
                seen.add(skey)
                span = src.span_by_id[sid]
                nodes.append(node(skey, sid, "evidence", nodeType="span",
                                  docId=span["doc_id"], textIntegrity=span["text_integrity"]))
            edges.append(edge(key, skey, "supported by", "evidence"))
        for target in claim.get("about", []):
            tkey = f"concept:{target}"
            if tkey not in seen:
                seen.add(tkey)
                iri = None
                for prefix, ns in (("mdcore", MDCORE), ("mech", MECH), ("melem", MELEM), ("ev", EV)):
                    if target.startswith(prefix + ":"):
                        iri = ns[target.split(":", 1)[1]]
                label = (src.label(iri) if iri is not None else None) or target
                cat = categorise(iri, src.ancestors(iri)) if iri is not None else "other"
                nodes.append(node(tkey, label, cat, nodeType="concept", curieRef=target,
                                  uri=str(iri) if iri is not None else None))
            edges.append(edge(key, tkey, "is about", "aboutness"))

        citations = [_citation_for(src, sid) for sid in claim["evidence_span_ids"]]
        claim_records.append({
            "claim_id": cid,
            "doc_id": claim["doc_id"],
            "book_title": claim["book_title"],
            "edition": claim["edition"],
            "topic": claim["topic"],
            "claim_type": claim["claim_type"],
            "normalized_statement": claim["normalized_statement"],
            "subject": claim.get("subject") or NOT_STATED,
            "predicate": claim.get("predicate") or NOT_STATED,
            "object": claim.get("object") or NOT_STATED,
            "conditions": claim.get("conditions") or [],
            "assumptions": claim.get("assumptions") or [],
            "exceptions": claim.get("exceptions") or [],
            "quantities": claim.get("quantities") or [],
            "threshold": claim.get("threshold"),
            "verification": claim.get("verification"),
            "external_authority": claim.get("external_authority") or [],
            "about": claim.get("about") or [],
            "equations": claim.get("equations") or [],
            "tables": claim.get("tables") or [],
            "figures": claim.get("figures") or [],
            "examples": claim.get("examples") or [],
            "procedures": claim.get("procedures") or [],
            "standards": claim.get("standards") or [],
            "equation_transcription": claim.get("equation_transcription"),
            "analyst_note": claim.get("analyst_note"),
            "review_status": claim["review_status"],
            "reviewed_by": claim.get("reviewed_by"),
            "extraction_confidence": claim["extraction_confidence"],
            "extraction_method": claim["extraction_method"],
            "text_integrity": claim["text_integrity"],
            "evidence_span_ids": claim["evidence_span_ids"],
            "citations": [c.get("citation") for c in citations],
            "printed_pages": claim.get("printed_pages") or [],
            "pdf_page_indices": claim.get("pdf_page_indices") or [],
            "has_quantities": bool(claim.get("quantities")),
            "has_artifacts": bool(
                claim.get("equations") or claim.get("tables")
                or claim.get("figures") or claim.get("examples")
            ),
            "requires_external_authority": bool(claim.get("external_authority")),
        })

    topics = sorted({c["topic"] for c in src.claims})
    return graph_doc(
        "claims_graph",
        "Claims and evidence",
        "Every claim is attributed to exactly one source and reaches a page through at "
        "least one verified evidence span.",
        nodes, edges,
        [
            {"cat": "claim", "label": "Normalized claim", "shape": "round-rectangle", "glyph": "▭"},
            {"cat": "evidence", "label": "Evidence span", "shape": "ellipse", "glyph": "●"},
            {"cat": "other", "label": "Referenced ontology concept", "shape": "diamond", "glyph": "◆"},
        ],
        notes=[
            "A claim is ABox data, never an OWL axiom.",
            "All claims are at NeedsReview; none has been signed off by a human engineer.",
        ],
        extra={
            "claims": sorted(claim_records, key=lambda c: c["claim_id"]),
            "topics": topics,
            "review_states": dict(sorted(Counter(c["review_status"] for c in src.claims).items())),
            "by_document": dict(sorted(Counter(c["doc_id"] for c in src.claims).items())),
            "claims_without_evidence": sorted(
                c["claim_id"] for c in src.claims if not c["evidence_span_ids"]
            ),
        },
    )


# ---------------------------------------------------------------------------
# View H -- cross-book alignments
# ---------------------------------------------------------------------------

FEATURED_ALIGNMENTS = [
    {"key": "design-factor-terminology", "title": "Design factor terminology",
     "concept_ids": ["align-t-0001", "align-t-0002"], "claim_ids": ["align-c-0010"],
     "summary": "Shigley separates n_d (chosen) from n (achieved); Mott uses a single N "
                "for both roles. Symbols are not interchangeable across the books."},
    {"key": "bearing-load-life-exponent", "title": "Bearing load/life exponent",
     "concept_ids": ["align-t-0003", "align-t-0005"], "claim_ids": ["align-c-0002", "align-c-0003"],
     "summary": "Mott's k and Shigley's a are the same exponent: 3 for ball bearings, "
                "3.33 / 10-over-3 for roller. The symbols are deliberately not merged."},
    {"key": "spline-versus-key", "title": "Spline versus key emphasis",
     "concept_ids": ["align-t-0009"], "claim_ids": ["align-c-0005"],
     "summary": "Mott: 'the advantages of splines over keys are many'. Shigley: splines are "
                "'much more expensive… usually not necessary for simple torque transmission'. "
                "Different criteria, not a contradiction."},
    {"key": "key-design-intent", "title": "Mott N = 3 versus Shigley's sacrificial key",
     "concept_ids": [], "claim_ids": ["align-c-0006"],
     "summary": "Mott recommends N = 3 to survive accidental overload and shock; Shigley "
                "warns against excessive safety factors because the key should fail first. "
                "Opposite design intent, deliberately left unresolved."},
    {"key": "rating-life-basis", "title": "Bearing catalogue rating-life basis",
     "concept_ids": ["align-t-0006", "align-t-0007"], "claim_ids": ["align-c-0004"],
     "summary": "Mott's equations assume a 10^6-revolution catalogue basis. Shigley notes a "
                "manufacturer rating at 90 x 10^6. Misapplying the formula errs by about 4.5x "
                "in required capacity."},
]


def build_alignments_graph(src: Sources) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def claim_node(cid: str) -> Optional[str]:
        claim = src.claim_by_id.get(cid)
        if claim is None:
            return None
        key = f"claim:{cid}"
        if key not in seen:
            seen.add(key)
            nodes.append(node(
                key, cid, "claim", nodeType="claim", docId=claim["doc_id"],
                side="left" if claim["doc_id"] == "mott6" else "right",
                topic=claim["topic"], statement=claim["normalized_statement"],
            ))
        return key

    alignment_records: List[Dict[str, Any]] = []
    for al in src.alignments_seed.get("claim_alignments", []):
        a_key = claim_node(al["claim_a"])
        b_key = claim_node(al["claim_b"])
        if not a_key or not b_key:
            LOG.warning("alignment %s references an unknown claim", al["id"])
            continue
        akey = f"align:{al['id']}"
        seen.add(akey)
        nodes.append(node(akey, al["id"], "vocabulary", nodeType="alignment",
                          alignmentType=al["alignment_type"]))
        edges.append(edge(a_key, akey, al["alignment_type"], "alignment"))
        edges.append(edge(akey, b_key, al["alignment_type"], "alignment"))

        ca, cb = src.claim_by_id[al["claim_a"]], src.claim_by_id[al["claim_b"]]
        alignment_records.append({
            "id": al["id"],
            "alignment_type": al["alignment_type"],
            "relation": al.get("relation"),
            "common_concept": al.get("common_concept") or NOT_STATED,
            "differing_conditions": " ".join((al.get("differing_conditions") or "").split()) or None,
            "differing_assumptions": " ".join((al.get("differing_assumptions") or "").split()) or None,
            "analyst_note": " ".join((al.get("analyst_note") or "").split()) or None,
            "review_status": al.get("review_status",
                                    src.alignments_seed.get("defaults", {}).get("review_status", "NeedsReview")),
            "claim_a": {
                "claim_id": ca["claim_id"], "doc_id": ca["doc_id"], "topic": ca["topic"],
                "statement": ca["normalized_statement"],
                "citations": [_citation_for(src, s).get("citation") for s in ca["evidence_span_ids"]],
                "span_ids": ca["evidence_span_ids"],
            },
            "claim_b": {
                "claim_id": cb["claim_id"], "doc_id": cb["doc_id"], "topic": cb["topic"],
                "statement": cb["normalized_statement"],
                "citations": [_citation_for(src, s).get("citation") for s in cb["evidence_span_ids"]],
                "span_ids": cb["evidence_span_ids"],
            },
            "topics": sorted({ca["topic"], cb["topic"]}),
        })

    terminology_records = []
    for row in src.terminology:
        terminology_records.append({
            "id": row["alignment_id"],
            "common_concept": row["common_concept"],
            "core_concept": row["core_concept"] or NOT_STATED,
            "mott6_term": row["mott6_term"] or NOT_STATED,
            "mott6_symbol": row["mott6_symbol"] or "—",
            "shigley10_term": row["shigley10_term"] or NOT_STATED,
            "shigley10_symbol": row["shigley10_symbol"] or "—",
            "alignment_type": row["alignment_type"],
            "review_status": row["review_status"],
            "analyst_note": row["analyst_note"] or None,
            "evidence_span_ids": [s for s in (row["evidence_span_ids"] or "").split(";") if s],
        })

    type_counts = Counter(a["alignment_type"] for a in alignment_records)
    return graph_doc(
        "alignments_graph",
        "Cross-book alignments",
        "Mott claims on the left, Shigley claims on the right, joined by a reified "
        "alignment. Nothing is merged: both claims survive in every case.",
        nodes, edges,
        [
            {"cat": "claim", "label": "Source claim", "shape": "round-rectangle", "glyph": "▭"},
            {"cat": "vocabulary", "label": "Alignment record", "shape": "concave-hexagon", "glyph": "◇"},
        ],
        notes=[
            "Conflicting or differently scoped claims are never merged into one statement.",
            "No Contradicts alignment exists in the pilot; the interesting disagreements are "
            "about scope and intent, not fact.",
        ],
        extra={
            "alignments": sorted(alignment_records, key=lambda a: a["id"]),
            "terminology": sorted(terminology_records, key=lambda t: t["id"]),
            "alignment_type_counts": dict(sorted(type_counts.items())),
            "terminology_type_counts": dict(sorted(Counter(
                t["alignment_type"] for t in terminology_records).items())),
            "featured": FEATURED_ALIGNMENTS,
            "all_types": ["Agrees", "Complements", "Refines", "CloseMatch", "ExactMatch",
                          "DiffersInScope", "DiffersInAssumption", "DiffersInTerminology",
                          "RelatedNotEquivalent", "ConflictingUsage", "Contradicts",
                          "NotComparable", "Unresolved"],
        },
    )


# ---------------------------------------------------------------------------
# View F -- substitution assessments
# ---------------------------------------------------------------------------

VERDICT_ORDER = ["PreferredAlternative", "DirectlySubstitutable", "ConditionallySubstitutable",
                 "FunctionalAlternative", "NotAnAlternative", "InsufficientEvidence"]


def build_substitutions_graph(src: Sources) -> Dict[str, Any]:
    data = src.substitutions
    contexts = {c["id"]: c for c in data.get("contexts", [])}
    requirements = {r["id"]: r for r in data.get("requirements", [])}

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def alt_node(curie_ref: str) -> str:
        key = f"alt:{curie_ref}"
        if key not in seen:
            seen.add(key)
            iri = MELEM[curie_ref.split(":", 1)[1]] if curie_ref.startswith("melem:") else None
            nodes.append(node(key, (src.label(iri) if iri is not None else None) or curie_ref,
                              "alternative", nodeType="individual", curieRef=curie_ref,
                              uri=str(iri) if iri is not None else None))
        return key

    def label_of(curie_ref: str) -> str:
        for prefix, ns in (("melem", MELEM), ("mech", MECH), ("mdcore", MDCORE)):
            if curie_ref.startswith(prefix + ":"):
                iri = ns[curie_ref.split(":", 1)[1]]
                return src.label(iri) or curie_ref
        return curie_ref

    def decorate(items: Sequence[Dict[str, Any]], text_key: str) -> List[Dict[str, Any]]:
        """Attach provenance badge and resolved citations to a curated list item."""
        out = []
        for item in items or []:
            spans = item.get("evidence") or []
            out.append({
                **{k: v for k, v in item.items() if k != "evidence"},
                "text": item.get(text_key) or NOT_STATED,
                "provenance": item.get("provenance", "EngineeringInference"),
                "span_ids": spans,
                "citations": [_citation_for(src, s).get("citation") for s in spans],
                "criterion_label": label_of(item["criterion"]) if item.get("criterion") else None,
                "failure_label": label_of(item["failure_mode"]) if item.get("failure_mode") else None,
                "method_label": label_of(item["method"]) if item.get("method") else None,
                "condition_label": label_of(item["condition"]) if item.get("condition") else None,
            })
        return out

    records: List[Dict[str, Any]] = []
    for sa in data["assessments"]:
        cand_key = alt_node(sa["candidate"])
        base_key = alt_node(sa["baseline"])
        akey = f"sa:{sa['id']}"
        seen.add(akey)
        nodes.append(node(akey, sa["id"], "substitution", nodeType="assessment",
                          verdict=sa["conclusion"], confidence=sa.get("confidence")))
        # Direction is exactly as curated: baseline -> assessment -> candidate.
        # No reverse edge is ever emitted.
        edges.append(edge(base_key, akey, "baseline", "substitution", verdict=sa["conclusion"]))
        edges.append(edge(akey, cand_key, "candidate", "substitution", verdict=sa["conclusion"]))

        ctx = contexts.get(sa["context"], {})
        records.append({
            "id": sa["id"],
            "label": sa["label"],
            "baseline": {"curie": sa["baseline"], "label": label_of(sa["baseline"])},
            "candidate": {"curie": sa["candidate"], "label": label_of(sa["candidate"])},
            "direction": f"{label_of(sa['candidate'])} replaces {label_of(sa['baseline'])}",
            "function_preserved": {"curie": sa["function_preserved"],
                                   "label": label_of(sa["function_preserved"])},
            "context": {
                "id": sa["context"],
                "label": ctx.get("label", NOT_STATED),
                "conditions": [{"curie": c, "label": label_of(c)} for c in ctx.get("conditions", [])],
                "note": " ".join((ctx.get("note") or "").split()) or None,
            },
            "verdict": sa["conclusion"],
            "confidence": sa.get("confidence"),
            "interface_compatibility": sa.get("interface_compatibility", NOT_STATED),
            "review_status": sa.get("review_status", "NeedsReview"),
            "applicable_requirements": [
                {"id": r, "label": requirements.get(r, {}).get("label", r),
                 "kind": requirements.get(r, {}).get("kind"),
                 "statement": requirements.get(r, {}).get("statement")}
                for r in sa.get("applicable_requirements") or []
            ],
            "satisfied_requirements": [
                {"id": r, "label": requirements.get(r, {}).get("label", r)}
                for r in sa.get("satisfied_requirements") or []
            ],
            "violated_requirements": [
                {"id": r, "label": requirements.get(r, {}).get("label", r)}
                for r in sa.get("violated_requirements") or []
            ],
            "conditions": decorate(sa.get("conditions"), "statement"),
            "modifications": decorate(sa.get("modifications"), "statement"),
            "advantages": decorate(sa.get("advantages"), "statement"),
            "disadvantages": decorate(sa.get("disadvantages"), "statement"),
            "trade_offs": decorate(sa.get("trade_offs"), "statement"),
            "introduced_failure_modes": decorate(sa.get("introduced_failure_modes"), "statement"),
            "mitigated_failure_modes": decorate(sa.get("mitigated_failure_modes"), "statement"),
            "required_verification": decorate(sa.get("required_verification"), "statement"),
            "unresolved": decorate(sa.get("unresolved"), "statement"),
            "analyst_note": " ".join((sa.get("analyst_note") or "").split()) or None,
            "supporting_claims": [
                {
                    "claim_id": cid,
                    "doc_id": src.claim_by_id[cid]["doc_id"],
                    "statement": src.claim_by_id[cid]["normalized_statement"],
                    "citations": [
                        _citation_for(src, s).get("citation")
                        for s in src.claim_by_id[cid]["evidence_span_ids"]
                    ],
                }
                for cid in sa.get("supporting_claims") or [] if cid in src.claim_by_id
            ],
            "span_ids": sorted({
                s for cid in sa.get("supporting_claims") or []
                if cid in src.claim_by_id
                for s in src.claim_by_id[cid]["evidence_span_ids"]
            }),
        })

    verdict_counts = Counter(r["verdict"] for r in records)
    for r in records:
        for u in r["unresolved"]:
            verdict_counts[u.get("state", "InsufficientEvidence")] += 1

    return graph_doc(
        "substitutions_graph",
        "Substitution assessments",
        "Each assessment is a reified judgement with a preserved function, an operating "
        "context and a requirement set. Direction runs baseline → candidate and is never "
        "mirrored.",
        nodes, edges,
        [
            {"cat": "alternative", "label": "Design alternative", "shape": "pentagon", "glyph": "⬟"},
            {"cat": "substitution", "label": "Substitution assessment", "shape": "barrel", "glyph": "⬓"},
        ],
        notes=[
            "SA-001 and SA-006 assess the same pair in the same context in opposite "
            "directions and reach opposite verdicts.",
            "No reverse edge is generated automatically, and no transitive edge is composed.",
        ],
        extra={
            "assessments": sorted(records, key=lambda r: r["id"]),
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "verdict_order": VERDICT_ORDER,
            "contexts": sorted(
                [
                    {"id": c["id"], "label": c["label"],
                     "conditions": [{"curie": x, "label": label_of(x)} for x in c.get("conditions", [])],
                     "note": " ".join((c.get("note") or "").split()) or None}
                    for c in data.get("contexts", [])
                ], key=lambda c: c["id"]
            ),
            "requirements": sorted(
                [
                    {"id": r["id"], "label": r["label"], "kind": r["kind"],
                     "statement": r["statement"]}
                    for r in data.get("requirements", [])
                ], key=lambda r: r["id"]
            ),
            "no_directly_substitutable": verdict_counts.get("DirectlySubstitutable", 0) == 0,
            "primary_pair": ["SA-001", "SA-006"],
        },
    )


# ---------------------------------------------------------------------------
# View I -- rules
# ---------------------------------------------------------------------------

AUTHORITY_LABELS = {
    "mdcore:RequiresExternalStandard": "External standard required",
    "mdcore:RequiresManufacturerData": "Manufacturer data required",
    "mdcore:RequiresCompanySpecification": "Company specification required",
    "mdcore:RequiresExperimentalProtocol": "Experimental protocol required",
    "mdcore:RequiresEngineeringReview": "Engineering review required",
}


def build_rules(src: Sources) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    for group, rules in sorted(src.rules.items()):
        for rule in rules:
            applies = rule.get("applies_when") or {}
            applies_to = rule.get("applies_to") or {}
            effect = rule.get("effect") or {}
            requires = rule.get("requires_verification") or []
            authorities = set(rule.get("requires_external_authority") or [])
            for block in (rule.get("acceptance") or {}, *(requires if isinstance(requires, list) else [])):
                if isinstance(block, dict):
                    authorities |= set(block.get("requires_external_authority") or [])

            entities = sorted({
                *(applies_to.get("alternatives") or []),
                *(effect.get("alternatives") or []),
                *(effect.get("over") or []),
                *([applies["function"]] if applies.get("function") else []),
                *(applies.get("context_conditions") or []),
                *(applies_to.get("context_conditions") or []),
                *(applies.get("behaviors") or []),
                *(applies.get("requirement_kinds") or []),
            })

            executable = rule.get("executable")
            records.append({
                "id": rule["id"],
                "group": group,
                "kind": rule.get("kind", "DesignRule"),
                "title": rule["title"],
                "statement": " ".join(str(rule["statement"]).split()),
                "applies_when": applies or None,
                "applies_to": applies_to or None,
                "effect": effect or None,
                "guard": rule.get("guard"),
                "prohibitions": rule.get("prohibitions") or [],
                "acceptance": rule.get("acceptance"),
                "requires_verification": requires,
                "preconditions": rule.get("preconditions") or [],
                "open_parameters": rule.get("open_parameters") or [],
                "unit_constraints": rule.get("unit_constraints") or [],
                "derived_from": rule.get("derived_from") or [],
                "derived_from_details": [
                    {"claim_id": cid, "doc_id": src.claim_by_id[cid]["doc_id"],
                     "statement": src.claim_by_id[cid]["normalized_statement"]}
                    for cid in rule.get("derived_from") or [] if cid in src.claim_by_id
                ],
                "analyst_authored": bool(rule.get("analyst_authored", False)),
                "confidence": rule.get("confidence"),
                "review_status": rule.get("review_status", "NeedsReview"),
                "executable": executable,
                "not_executable_because": " ".join(
                    (rule.get("not_executable_because") or "").split()) or None,
                "external_authorities": sorted(authorities),
                "external_authority_labels": [
                    AUTHORITY_LABELS.get(a, a) for a in sorted(authorities)
                ],
                "referenced_entities": entities,
                "notes": " ".join((rule.get("notes") or "").split()) or None,
                "both_sources_agree": rule.get("both_sources_agree", False),
                "evidence_requirement": (
                    "Derived from cited claims" if rule.get("derived_from")
                    else "Analyst-authored (no cited claim)"
                ),
            })

    declarative_only = [r["id"] for r in records if r.get("executable") is False]
    return {
        "rules": sorted(records, key=lambda r: r["id"]),
        "counts_by_group": dict(sorted(Counter(r["group"] for r in records).items())),
        "counts_by_kind": dict(sorted(Counter(r["kind"] for r in records).items())),
        "declarative_only": declarative_only,
        "authority_labels": AUTHORITY_LABELS,
        "notice": (
            "The rule layer is declarative. Rules are validated and machine-readable, but "
            "no engine evaluates them against a design problem in v0.1."
        ),
    }


# ---------------------------------------------------------------------------
# View J -- coverage
# ---------------------------------------------------------------------------


def build_coverage(src: Sources) -> Dict[str, Any]:
    claim_topics = Counter(c["topic"] for c in src.claims)
    #: Analyst mapping from claim topic tag to the coverage-matrix topic keys it exercises.
    TOPIC_LINK = {
        "design-factor": ["uncertainty-safety"],
        "fatigue": ["fatigue"],
        "shaft-hub-connection": ["shaft-hub"],
        "substitution": ["shaft-hub", "tolerances-fits"],
        "verification": ["shaft-hub", "tolerances-fits", "rolling-bearings"],
        "bearing-life": ["rolling-bearings"],
    }
    topic_claim_counts: Counter = Counter()
    for topic, count in claim_topics.items():
        for key in TOPIC_LINK.get(topic, []):
            topic_claim_counts[key] += count

    sa_topics = {"shaft-hub", "rolling-bearings", "tolerances-fits"}

    rows = []
    for row in src.coverage:
        key = row["topic_key"]
        rows.append({
            "topic_key": key,
            "topic": row["topic"],
            "group": row["group"],
            "coverage": row["coverage"],
            "depth_note": row["depth_note"],
            "mott6": {
                "covered": row["mott6_covered"] == "yes",
                "chapters": [c for c in row["mott6_chapters"].split(";") if c],
                "chapter_titles": row["mott6_chapter_titles"],
                "pages": int(row["mott6_pages"] or 0),
                "sections": int(row["mott6_sections"] or 0),
                "printed_pages": [p for p in row["mott6_printed_pages"].split(";") if p],
            },
            "shigley10": {
                "covered": row["shigley10_covered"] == "yes",
                "chapters": [c for c in row["shigley10_chapters"].split(";") if c],
                "chapter_titles": row["shigley10_chapter_titles"],
                "pages": int(row["shigley10_pages"] or 0),
                "sections": int(row["shigley10_sections"] or 0),
                "printed_pages": [p for p in row["shigley10_printed_pages"].split(";") if p],
            },
            "claim_count": topic_claim_counts.get(key, 0),
            "is_pilot_topic": topic_claim_counts.get(key, 0) > 0,
            "has_substitution_assessment": key in sa_topics,
            "status": (
                "Pilot topic — semantic claims extracted"
                if topic_claim_counts.get(key, 0) > 0
                else "Taxonomy only — page structure extracted, no claims yet"
            ),
        })

    return {
        "rows": sorted(rows, key=lambda r: (r["group"], r["topic"])),
        "coverage_counts": dict(sorted(Counter(r["coverage"] for r in rows).items())),
        "claim_topics": dict(sorted(claim_topics.items())),
        "documents": [
            {"doc_id": d, "title": src.config["sources"][d]["title"],
             "page_count": src.doc_meta[d]["page_count"],
             "toc_entries": src.doc_meta[d]["toc_entry_count"]}
            for d in src.config["sources"]
        ],
        "notice": (
            "Page structure was extracted for both complete books (1,978 pages, 799 outline "
            "entries). Semantic claim extraction in v0.1 is a pilot confined to the topics "
            "marked below."
        ),
    }


# ---------------------------------------------------------------------------
# Global search index
# ---------------------------------------------------------------------------


def build_search_index(src: Sources, datasets: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []

    def add(eid: str, etype: str, view: str, label: str,
            sub: str = "", text: str = "", ko: str = "", target: Optional[str] = None) -> None:
        entries.append({
            "id": eid, "type": etype, "view": view, "label": label,
            "sub": sub, "ko": ko, "target": target or eid,
            "text": " ".join(f"{label} {ko} {sub} {text}".split()).lower()[:1400],
        })

    for n in datasets["ontology_graph"]["nodes"]:
        d = n["data"]
        add(d["id"], "Ontology class", "ontology", d["label"], d["id"],
            f"{d.get('definition', '')} {d.get('scopeNote', '')} {d.get('comment', '')}",
            d.get("ko", ""))
    for p in datasets["ontology_graph"]["properties"]:
        add(p["curie"], f"Ontology property ({p['kind']})", "ontology", p["label"], p["curie"],
            f"{p.get('definition', '')} {p.get('scope_note', '')}", p.get("ko") or "")

    for n in datasets["function_behavior_graph"]["nodes"]:
        d = n["data"]
        if d["cat"] in ("function", "behavior", "effect", "condition", "failure", "verification"):
            add(d["id"], f"Mechanical {d['cat']}", "mechanical", d["label"], d["id"],
                f"{d.get('definition', '')} {d.get('scopeNote', '')}", d.get("ko", ""))
    for f in datasets["function_behavior_graph"]["functions"]:
        add(f["id"], "Function", "functions", f["label"], f.get("pref_label") or "",
            f"{f.get('definition', '')} {f.get('scope_note', '')} "
            f"{' '.join(a['label'] for a in f['alternatives'])}", f.get("ko") or "")

    for n in datasets["machine_elements_graph"]["nodes"]:
        d = n["data"]
        kind = "Design alternative" if d["cat"] == "alternative" else "Machine element"
        add(d["id"], kind, "elements", d["label"], d["id"],
            f"{d.get('definition', '')} {d.get('scopeNote', '')}", d.get("ko", ""))

    for c in datasets["claims_graph"]["claims"]:
        add(c["claim_id"], "Claim", "claims", c["claim_id"],
            f"{c['book_title']} — {c['topic']}",
            f"{c['normalized_statement']} {c['subject']} {c['predicate']} {c['object']}")

    for s in datasets["evidence_graph"]["spans"]:
        add(s["span_id"], "Evidence span", "evidence", s["span_id"],
            f"{s['book_title']} p. {s['printed_page']}",
            f"{s['extracted_text']} {s['chapter_title']} {s['section_title']} {s['anchor']}")

    for a in datasets["alignments_graph"]["alignments"]:
        add(a["id"], "Claim alignment", "alignments", a["id"], a["alignment_type"],
            f"{a['common_concept']} {a.get('analyst_note') or ''} "
            f"{a['claim_a']['statement']} {a['claim_b']['statement']}")
    for t in datasets["alignments_graph"]["terminology"]:
        add(t["id"], "Terminology alignment", "alignments", t["common_concept"], t["alignment_type"],
            f"{t['mott6_term']} {t['mott6_symbol']} {t['shigley10_term']} "
            f"{t['shigley10_symbol']} {t.get('analyst_note') or ''}")

    for sa in datasets["substitutions_graph"]["assessments"]:
        add(sa["id"], "Substitution assessment", "substitutions", sa["id"],
            f"{sa['verdict']} — {sa['direction']}",
            f"{sa['label']} {sa['context']['label']} {sa.get('analyst_note') or ''}")

    for r in datasets["rules"]["rules"]:
        add(r["id"], f"Rule ({r['kind']})", "rules", r["id"], r["title"],
            f"{r['statement']} {r.get('notes') or ''}")

    for doc in datasets["overview"]["sources"]:
        add(f"doc:{doc['doc_id']}", "Source document", "evidence", doc["title"],
            f"{doc['edition']} ed. — {', '.join(doc['authors'])}", doc["file"])

    for row in datasets["coverage"]["rows"]:
        add(f"topic:{row['topic_key']}", "Coverage topic", "coverage", row["topic"],
            row["coverage"], f"{row['group']} {row['depth_note']}")

    seen_ids: Set[str] = set()
    unique: List[Dict[str, Any]] = []
    for e in sorted(entries, key=lambda x: (x["type"], x["id"])):
        key = f"{e['type']}|{e['id']}"
        if key in seen_ids:
            continue
        seen_ids.add(key)
        unique.append(e)

    return {
        "entries": unique,
        "count": len(unique),
        "types": sorted({e["type"] for e in unique}),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

DATASET_FILES = [
    "overview", "ontology_graph", "function_behavior_graph", "machine_elements_graph",
    "claims_graph", "evidence_graph", "alignments_graph", "substitutions_graph",
    "rules", "coverage", "search_index",
]


def build_all(config: Dict[str, Any]) -> Dict[str, Any]:
    """Build every dataset and return them keyed by file stem."""
    src = Sources(config)
    datasets: Dict[str, Any] = {}
    datasets["overview"] = build_overview(src)
    datasets["ontology_graph"] = build_ontology_graph(src)
    datasets["function_behavior_graph"] = build_function_behavior_graph(src)
    datasets["machine_elements_graph"] = build_machine_elements_graph(src)
    datasets["claims_graph"] = build_claims_graph(src)
    datasets["evidence_graph"] = build_evidence_graph(src)
    datasets["alignments_graph"] = build_alignments_graph(src)
    datasets["substitutions_graph"] = build_substitutions_graph(src)
    datasets["rules"] = build_rules(src)
    datasets["coverage"] = build_coverage(src)
    datasets["search_index"] = build_search_index(src, datasets)
    return datasets


def write_datasets(datasets: Dict[str, Any], out_dir: Path) -> Dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, int] = {}
    for name in DATASET_FILES:
        path = out_dir / f"{name}.json"
        payload = json.dumps(datasets[name], ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")) + "\n"
        path.write_text(payload, encoding="utf-8")
        written[f"{name}.json"] = len(payload.encode("utf-8"))
        LOG.info("wrote %-34s %8d bytes", path.name, written[f"{name}.json"])
    return written


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "outputs" / "visualizations" / "data")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    with args.config.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    datasets = build_all(config)
    written = write_datasets(datasets, args.out)
    summary = {
        "files": written,
        "graphs": {
            name: {"nodes": datasets[name]["meta"]["node_count"],
                   "edges": datasets[name]["meta"]["edge_count"],
                   "isolated": datasets[name]["meta"]["isolated_node_count"]}
            for name in DATASET_FILES if "meta" in datasets[name]
        },
        "search_entities": datasets["search_index"]["count"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
