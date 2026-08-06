#!/usr/bin/env python3
"""Deterministic, read-only auditor for the BM-003 HELD_OUT_BENCHMARK_ORACLE.

A separate tool from audit_oracles.py because BM-003's authority differs. The
product_cases packs derive from frozen dossiers with rank-1 locators; BM-003
derives from a frozen benchmark SOURCE. Same discipline, different provenance
model, so a different set of joins to check.

WHAT THIS TOOL CAN ESTABLISH
  * every source clause is represented, and every normative statement cites one;
  * no numeric threshold was introduced that the source does not contain;
  * no realization family is preferred;
  * no invariant contradicts a declared freedom;
  * every negative case maps to a real acceptance predicate;
  * no evidence class is cited for a claim its own scope excludes;
  * stage expectations do not name a mechanism;
  * all IDs are unique and all references resolve;
  * every file parses;
  * the source hash matches the frozen source.

WHAT IT CANNOT
  * that any invariant is physically true;
  * that the admissible families are actually buildable - their tags are authored
    by the same hand that authored the invariants, so a clean fixture result
    means the author was self-consistent, not that the world agrees;
  * that the Oracle is not overfitted in some way nobody thought to check.

A clean report means the pack is internally coherent. It is not a substitute for
the human review recorded in GOVERNANCE.yaml.

Exit code 0 when no finding is BLOCKING.
"""

import argparse
import hashlib
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # ver3/
REPO = os.path.dirname(ROOT)
PACK = os.path.join(ROOT, "oracles", "held_out", "BM-003")
SOURCE = os.path.join(ROOT, "benchmarks", "BM-003", "source", "request.txt")

FILES = {
    "ledger": "source_clause_ledger.yaml",
    "normative": "normative.yaml",
    "configurations": "configurations.yaml",
    "expectations": "assembly_and_mobility_expectations.yaml",
    "freedoms": "freedoms.yaml",
    "ambiguities": "ambiguities.yaml",
    "evidence": "evidence_scope.yaml",
    "realizations": "realizations.yaml",
    "negatives": "negative_cases.yaml",
    "stages": "stage_expectations.yaml",
    "governance": "GOVERNANCE.yaml",
}

#: Mechanism words no normative statement, stage expectation or predicate may
#: REQUIRE. They may appear as admitted examples in freedoms.yaml and
#: realizations.yaml, which is the whole point of those files.
MECHANISM_WORDS = [
    "latch", "detent", "collar", "toggle", "spring", "magnet", "screw", "bolt",
    "pin", "clip", "clasp", "ring", "hinge", "revolute", "prismatic", "bearing",
    "over-centre", "over-center", "cam", "linkage", "strut", "brace",
]

#: Files where mechanism vocabulary is legitimate.
MECHANISM_PERMITTED_FILES = {"freedoms", "realizations", "negatives", "ledger", "governance"}

VALID_STATUSES = {"PASS", "FAIL", "NOT_VERIFIED", "UNSUPPORTED", "INDETERMINATE",
                  "NOT_EVALUABLE"}


class Finding(object):
    def __init__(self, check, severity, code, detail):
        self.check = check
        self.severity = severity
        self.code = code
        self.detail = detail

    def as_dict(self):
        return {"check": self.check, "severity": self.severity,
                "code": self.code, "detail": self.detail}


def load(pack_dir):
    docs = {}
    for key, name in FILES.items():
        path = os.path.join(pack_dir, name)
        with open(path, "r", encoding="utf-8") as fh:
            docs[key] = yaml.safe_load(fh)
    return docs


def _walk_strings(node, path="$"):
    """Every string in a nested structure, with a rough path for reporting."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            for p, s in _walk_strings(v, "%s.%s" % (path, k)):
                yield p, s
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for p, s in _walk_strings(v, "%s[%d]" % (path, i)):
                yield p, s


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_source_hash(docs, findings, source_path=SOURCE):
    """A-1. The Oracle must be bound to the exact source it was written against."""
    declared = docs["ledger"]["source_sha256"]
    if not os.path.isfile(source_path):
        findings.append(Finding("A-1", "BLOCKING", "SOURCE_MISSING", source_path))
        return
    with open(source_path, "rb") as fh:
        actual = hashlib.sha256(fh.read()).hexdigest()
    if actual != declared:
        findings.append(Finding("A-1", "BLOCKING", "SOURCE_HASH_MISMATCH",
                                "declared %s, actual %s" % (declared, actual)))
    for key in ("normative", "governance"):
        d = docs[key]
        got = d.get("source_sha256") or d.get("authoring", {}).get("source_sha256")
        if got and got != actual:
            findings.append(Finding("A-1", "BLOCKING", "SOURCE_HASH_INCONSISTENT",
                                    "%s declares %s" % (FILES[key], got)))


def check_clause_coverage(docs, findings, source_path=SOURCE):
    """A-2. Every source sentence is in the ledger, and every clause is used."""
    clauses = docs["ledger"]["clauses"]

    with open(source_path, encoding="utf-8") as fh:
        text = " ".join(fh.read().split())
    sentences = [s.strip() for s in re.split(r"(?<=\.)\s+", text) if s.strip()]
    ledger_text = " ".join(" ".join(c["verbatim"].split()) for c in clauses)
    for sent in sentences:
        if sent.rstrip(".") not in ledger_text:
            findings.append(Finding("A-2", "BLOCKING", "SOURCE_CLAUSE_UNMAPPED",
                                    "source sentence absent from ledger: %r" % sent[:70]))

    referenced = set()
    for key in ("normative", "freedoms", "ambiguities"):
        for _p, s in _walk_strings(docs[key]):
            referenced.update(re.findall(r"SRC-BM003-\d+", s))
    for c in clauses:
        if c["id"] not in referenced:
            findings.append(Finding("A-2", "BLOCKING", "CLAUSE_NEVER_USED",
                                    "%s is mapped but nothing cites it" % c["id"]))


def check_normative_provenance(docs, findings):
    """A-3. Every invariant cites a clause or declares its derivation."""
    clause_ids = {c["id"] for c in docs["ledger"]["clauses"]}
    for inv in docs["normative"]["invariants"]:
        cites = inv.get("source_clauses", [])
        if not cites and inv.get("basis_type") != "VERIFICATION_MINIMUM":
            findings.append(Finding("A-3", "BLOCKING", "INVARIANT_WITHOUT_SOURCE", inv["id"]))
        for c in cites:
            if c not in clause_ids:
                findings.append(Finding("A-3", "BLOCKING", "DANGLING_CLAUSE_REF",
                                        "%s cites unknown %s" % (inv["id"], c)))
        # A VERIFICATION_MINIMUM is justified by what it ENABLES, not by a
        # physical derivation, so it is exempt from the premises requirement and
        # carries enables_claim + requires_evidence_tags instead.
        if (inv.get("support_type") == "derived"
                and inv.get("basis_type") != "VERIFICATION_MINIMUM"
                and not inv.get("derivation_premises")):
            findings.append(Finding("A-3", "BLOCKING", "DERIVED_WITHOUT_PREMISES", inv["id"]))
        if inv.get("basis_type") == "VERIFICATION_MINIMUM":
            if not inv.get("enables_claim") or not inv.get("requires_evidence_tags"):
                findings.append(Finding("A-3", "BLOCKING", "VERIFICATION_MINIMUM_INCOMPLETE", inv["id"]))
        if not inv.get("verification_predicate"):
            findings.append(Finding("A-3", "BLOCKING", "NO_VERIFICATION_PREDICATE", inv["id"]))


#: Bookkeeping fields whose digits are metadata, not requirements.
METADATA_KEYS = {
    "schema_version", "source_sha256", "source_revision", "benchmark_id",
    "oracle_name", "authored_on", "frozen_on", "decision_date", "timestamp",
    "count", "total", "minimum_required", "quantitative", "interpretive",
}


def _semantic_text(text):
    """Strip identifiers and hashes, leaving prose a threshold could hide in."""
    text = re.sub(r"\b[0-9a-f]{16,}\b", "", text)                       # hashes
    text = re.sub(r"\b(?:NRM|SRC|AMB|FRE|NEG|ADM|INADM|CFG|TRN|ASM|MOB|EVC)-[A-Z0-9-]+", "", text)
    text = re.sub(r"\bBM-?00\d\b", "", text)                            # benchmark ids
    text = re.sub(r"\bs\d\d\b", "", text)                               # stage ids
    text = re.sub(r"\bV-[AB]\b", "", text)                               # fidelity labels
    text = re.sub(r"\b\d+\.\d+\.\d+\b", "", text)                      # semantic versions
    text = re.sub(r"\bVer[12]\b", "", text)                              # legacy version names
    return text


def check_no_unstated_numeric_threshold(docs, findings, source_path=SOURCE):
    """A-4. The source contains no digit, so no requirement may introduce one.

    This is the check that catches an invented threshold - an impact energy for
    "knocked it", a footprint dimension, a mass for "small object". Metadata
    fields and identifiers are stripped first, because their digits are
    bookkeeping and flagging them would bury the finding that matters.
    """
    with open(source_path, encoding="utf-8") as fh:
        source_digits = set(re.findall(r"\d", fh.read()))
    scanned = ("normative", "configurations", "expectations", "stages")
    for key in scanned:
        for path, s in _walk_strings(docs[key]):
            if path.split(".")[-1].split("[")[0] in METADATA_KEYS:
                continue
            for n in re.findall(r"\d+(?:\.\d+)?", _semantic_text(s)):
                if not source_digits:
                    findings.append(Finding(
                        "A-4", "BLOCKING", "UNSTATED_NUMERIC_THRESHOLD",
                        "%s in %s introduces %r: %r" % (path, FILES[key], n, s[:80])))


def check_no_preferred_realization(docs, findings):
    """A-5. No realization family may be preferred, recommended or required."""
    fams = docs["realizations"]["admissible_realizations"]
    if len(fams) < 4:
        findings.append(Finding("A-5", "BLOCKING", "TOO_FEW_ADMISSIBLE_FAMILIES",
                                "%d declared, at least 4 required" % len(fams)))
    principles = set()
    for f in fams:
        if not f.get("not_preferred"):
            findings.append(Finding("A-5", "BLOCKING", "FAMILY_NOT_MARKED_UNPREFERRED", f["id"]))
        principles.add(f["family"])
    if len(principles) != len(fams):
        findings.append(Finding("A-5", "BLOCKING", "FAMILIES_NOT_DISTINCT",
                                "family labels repeat"))
    for path, s in _walk_strings(docs["normative"]):
        if re.search(r"\b(preferred|recommended|should use|must use)\b", s, re.I):
            findings.append(Finding("A-5", "BLOCKING", "PREFERENCE_IN_NORMATIVE",
                                    "%s: %r" % (path, s[:90])))


def check_freedoms_not_contradicted(docs, findings):
    """A-6. No invariant, expectation or stage projection may require a free choice."""
    for key in ("normative", "configurations", "expectations", "stages"):
        if key in MECHANISM_PERMITTED_FILES:
            continue
        for path, s in _walk_strings(docs[key]):
            low = s.lower()
            for word in MECHANISM_WORDS:
                if not re.search(r"\b%s\b" % re.escape(word), low):
                    continue
                # A negated or admitting mention is not a requirement.
                if re.search(r"\b(no|not|never|any|neither|without|nor|admits|example)\b", low):
                    continue
                findings.append(Finding(
                    "A-6", "BLOCKING", "FREEDOM_CONTRADICTED",
                    "%s in %s requires mechanism %r: %r" % (path, FILES[key], word, s[:90])))

    free_ids = {f["id"] for f in docs["freedoms"]["freedoms"]}
    for path, s in _walk_strings(docs["normative"]):
        for fid in re.findall(r"FRE-BM-003-\d+", s):
            if fid not in free_ids:
                findings.append(Finding("A-6", "BLOCKING", "DANGLING_FREEDOM_REF", fid))


def check_negative_cases(docs, findings):
    """A-7. Every negative case names a mutation, a predicate, a stage and a reason."""
    required = ("mutation", "why_wrong", "expected_detection_predicate",
                "expected_owning_stage", "must_not_be_reported_as",
                "why_a_model_might_do_this")
    stages = set(docs["stages"]["stages"])
    seen = set()
    for neg in docs["negatives"]["negative_cases"]:
        for field in required:
            if not neg.get(field):
                findings.append(Finding("A-7", "BLOCKING", "NEGATIVE_CASE_INCOMPLETE",
                                        "%s missing %s" % (neg["id"], field)))
        if neg["id"] in seen:
            findings.append(Finding("A-7", "BLOCKING", "DUPLICATE_ID", neg["id"]))
        seen.add(neg["id"])
        st = neg.get("expected_owning_stage")
        if st and st not in stages:
            findings.append(Finding("A-7", "BLOCKING", "NEGATIVE_CASE_UNKNOWN_STAGE",
                                    "%s names %s" % (neg["id"], st)))
        for status in neg.get("must_not_be_reported_as", []):
            if status not in VALID_STATUSES and status != "INFEASIBLE":
                findings.append(Finding("A-7", "BLOCKING", "UNKNOWN_STATUS",
                                        "%s: %s" % (neg["id"], status)))
    if len(docs["negatives"]["negative_cases"]) < 15:
        findings.append(Finding("A-7", "BLOCKING", "TOO_FEW_NEGATIVE_CASES",
                                str(len(docs["negatives"]["negative_cases"]))))


def check_negative_cases_map_to_predicates(docs, findings):
    """A-8. A negative case whose predicate names nothing real detects nothing."""
    known = set()
    for inv in docs["normative"]["invariants"]:
        known.add(inv["id"])
    for group in ("assembly_expectations", "mobility_expectations"):
        for e in docs["expectations"][group]:
            known.add(e["id"])
    known.update(a["id"] for a in docs["ambiguities"]["ambiguities"])
    for neg in docs["negatives"]["negative_cases"]:
        pred = neg.get("expected_detection_predicate", "")
        refs = re.findall(r"(?:NRM|ASM|MOB|AMB)-BM-003-\d+", pred)
        named_rule = re.search(r"[a-z_]{6,}", pred) is not None
        if not refs and not named_rule:
            findings.append(Finding("A-8", "BLOCKING", "NEGATIVE_CASE_UNANCHORED",
                                    "%s predicate names no rule" % neg["id"]))
        for r in refs:
            if r not in known:
                findings.append(Finding("A-8", "BLOCKING", "DANGLING_PREDICATE_REF",
                                        "%s -> %s" % (neg["id"], r)))


def check_evidence_scope(docs, findings):
    """A-9. No claim may cite an evidence class whose own scope excludes it."""
    classes = docs["evidence"]["evidence_classes"]
    for c in classes:
        if c.get("availability") == "NOT_AVAILABLE_IN_THIS_BENCHMARK":
            continue
        for field in ("in_scope", "out_of_scope"):
            if not c.get(field):
                findings.append(Finding("A-9", "BLOCKING", "EVIDENCE_SCOPE_INCOMPLETE",
                                        "%s missing %s" % (c["id"], field)))
        if "structural_artifacts" not in c:
            findings.append(Finding("A-9", "BLOCKING", "NO_STRUCTURAL_ARTIFACTS", c["id"]))

    by_name = {c["name"]: c for c in classes}
    prohibited = {p.lower() for p in docs["evidence"]["prohibited_inferences"]["items"]}
    sim = by_name.get("continuous_kinematic_simulation", {})
    sim_out = {o.lower() for o in sim.get("out_of_scope", [])}
    for p in prohibited:
        if not any(p in o or o in p for o in sim_out):
            findings.append(Finding("A-9", "BLOCKING", "PROHIBITED_INFERENCE_NOT_SCOPED",
                                    "%r is prohibited but not in the simulation out_of_scope list" % p))

    for group in ("assembly_expectations", "mobility_expectations"):
        for e in docs["expectations"][group]:
            for name in e.get("satisfied_by", []):
                if name not in by_name:
                    findings.append(Finding("A-9", "BLOCKING", "UNKNOWN_EVIDENCE_CLASS",
                                            "%s -> %s" % (e["id"], name)))

    for entry in docs["evidence"]["required_statuses"]["mapping"]:
        if entry["status"] not in VALID_STATUSES:
            findings.append(Finding("A-9", "BLOCKING", "UNKNOWN_REQUIRED_STATUS",
                                    "%s -> %s" % (entry["property"], entry["status"])))


def check_no_structural_pass(docs, findings):
    """A-10. Capacity must not be passable from the evidence this benchmark has."""
    rules = docs["stages"]["stages"]["s11"].get("outcome_rules", {})
    cap = rules.get("structural_capacity")
    if not cap:
        findings.append(Finding("A-10", "BLOCKING", "NO_CAPACITY_OUTCOME_RULE",
                                "s11 declares no structural_capacity rule"))
        return
    if cap.get("if_capability_absent") != "UNSUPPORTED" or cap.get("otherwise") != "UNSUPPORTED":
        findings.append(Finding("A-10", "BLOCKING", "CAPACITY_NOT_UNSUPPORTED",
                                json.dumps(cap)))
    forbidden = docs["stages"]["stages"]["s11"].get("must_not_decide", [])
    if not any("capacity" in f.lower() or "strength" in f.lower() for f in forbidden):
        findings.append(Finding("A-10", "BLOCKING", "CAPACITY_PASS_NOT_FORBIDDEN",
                                "s11 must_not_decide does not forbid a capacity PASS"))


def check_release_requirement_present(docs, findings):
    """A-11. The deliberate release is the benchmark's distinguishing requirement."""
    texts = " ".join(s for _p, s in _walk_strings(docs["normative"]))
    if "deliberate" not in texts.lower():
        findings.append(Finding("A-11", "BLOCKING", "DELIBERATE_RELEASE_MISSING",
                                "no invariant requires a deliberate action before folding"))
    cfg_ids = {c["id"] for c in docs["configurations"]["configurations"]}
    if "CFG-BM-003-RELEASED" not in cfg_ids:
        findings.append(Finding("A-11", "BLOCKING", "RELEASED_CONFIGURATION_MISSING",
                                "no configuration distinguishes released from deployed"))


def check_stage_expectations(docs, findings):
    """A-12. Every stage covered; none may leak a preferred solution."""
    stages = docs["stages"]["stages"]
    expected = ["s%02d" % n for n in range(1, 13)]
    missing = [s for s in expected if s not in stages]
    if missing:
        findings.append(Finding("A-12", "BLOCKING", "STAGE_COVERAGE_INCOMPLETE", str(missing)))
    amb_ids = {a["id"] for a in docs["ambiguities"]["ambiguities"]}
    for sid, spec in stages.items():
        for field in ("must_make_available", "must_not_decide", "downstream_needs"):
            if not spec.get(field):
                findings.append(Finding("A-12", "BLOCKING", "STAGE_FIELD_MISSING",
                                        "%s missing %s" % (sid, field)))
        for a in spec.get("must_leave_unresolved", []):
            if a not in amb_ids:
                findings.append(Finding("A-12", "BLOCKING", "DANGLING_AMBIGUITY_REF",
                                        "%s -> %s" % (sid, a)))


def check_ambiguities(docs, findings):
    """A-13. Required unresolved items must all be present as ambiguities."""
    amb = docs["ambiguities"]["ambiguities"]
    if len(amb) < 9:
        findings.append(Finding("A-13", "BLOCKING", "TOO_FEW_AMBIGUITIES", str(len(amb))))
    for a in amb:
        for field in ("question", "source_says", "why_unresolved", "block_scopes"):
            if not a.get(field):
                findings.append(Finding("A-13", "BLOCKING", "AMBIGUITY_INCOMPLETE",
                                        "%s missing %s" % (a["id"], field)))
        if a.get("kind") == "quantitative" and "blocks_structural_predicate" in a.get("block_scopes", []):
            findings.append(Finding("A-13", "BLOCKING", "QUANTITATIVE_BLOCKS_STRUCTURAL",
                                    "%s: a missing number does not undefine a geometric predicate" % a["id"]))


def check_ids_unique_and_resolve(docs, findings):
    """A-14. IDs unique across the pack; every cross reference resolves."""
    defined = set()
    def _collect(items, key="id"):
        for it in items:
            i = it[key]
            if i in defined:
                findings.append(Finding("A-14", "BLOCKING", "DUPLICATE_ID", i))
            defined.add(i)
    _collect(docs["ledger"]["clauses"])
    _collect(docs["normative"]["invariants"])
    _collect(docs["configurations"]["configurations"])
    _collect(docs["configurations"]["transitions"])
    _collect(docs["expectations"]["assembly_expectations"])
    _collect(docs["expectations"]["mobility_expectations"])
    _collect(docs["freedoms"]["freedoms"])
    _collect(docs["ambiguities"]["ambiguities"])
    _collect(docs["evidence"]["evidence_classes"])
    _collect(docs["realizations"]["admissible_realizations"])
    _collect(docs["realizations"]["inadmissible_realizations"])
    _collect(docs["negatives"]["negative_cases"])

    pattern = re.compile(r"\b(?:SRC-BM003|NRM-BM-003|CFG-BM-003|TRN-BM-003|ASM-BM-003|"
                         r"MOB-BM-003|FRE-BM-003|AMB-BM-003|EVC-BM-003|ADM-BM-003|"
                         r"INADM-BM-003|NEG-BM-003)-[A-Z0-9_]+")
    for key in docs:
        for path, s in _walk_strings(docs[key]):
            for ref in pattern.findall(s):
                if ref not in defined:
                    findings.append(Finding("A-14", "BLOCKING", "DANGLING_REFERENCE",
                                            "%s in %s -> %s" % (path, FILES[key], ref)))


def check_fixture_permissiveness(docs, findings):
    """A-15. Every physical invariant must admit every admissible family."""
    vocab = set(docs["realizations"]["physical_tag_vocabulary"])
    required = {}
    for inv in docs["normative"]["invariants"]:
        if inv.get("basis_type") == "VERIFICATION_MINIMUM":
            for t in inv.get("requires_evidence_tags", []):
                if t in vocab:
                    findings.append(Finding("A-15", "BLOCKING", "DESIGN_EVIDENCE_TAG_MIXED",
                                            "%s uses physical tag %r as evidence tag" % (inv["id"], t)))
            continue
        for t in inv.get("requires_tags", []):
            if t not in vocab:
                findings.append(Finding("A-15", "BLOCKING", "UNKNOWN_PHYSICAL_TAG",
                                        "%s -> %s" % (inv["id"], t)))
            required.setdefault(inv["id"], set()).add(t)

    for fam in docs["realizations"]["admissible_realizations"]:
        tags = set(fam.get("satisfies_tags", []))
        for inv_id, needed in required.items():
            missing = needed - tags
            if missing:
                findings.append(Finding("A-15", "BLOCKING", "ADMISSIBLE_FAMILY_REJECTED",
                                        "%s fails %s (missing %s)" % (fam["id"], inv_id, sorted(missing))))

    inv_ids = {i["id"] for i in docs["normative"]["invariants"]}
    for bad in docs["realizations"]["inadmissible_realizations"]:
        rejectors = bad.get("rejected_by", [])
        if not rejectors:
            findings.append(Finding("A-15", "BLOCKING", "INADMISSIBLE_NOT_REJECTED", bad["id"]))
        for r in rejectors:
            if r not in inv_ids:
                findings.append(Finding("A-15", "BLOCKING", "DANGLING_REJECTOR",
                                        "%s -> %s" % (bad["id"], r)))


def check_governance(docs, findings):
    """A-16. Production visibility false; isolation recorded."""
    g = docs["governance"]
    if g["production_visibility"]["visible_to_production"] is not False:
        findings.append(Finding("A-16", "BLOCKING", "ORACLE_VISIBLE_TO_PRODUCTION", ""))
    if g["authority"]["authority_status"] != "FROZEN":
        findings.append(Finding("A-16", "BLOCKING", "ORACLE_NOT_FROZEN",
                                g["authority"]["authority_status"]))
    if not g.get("files_explicitly_not_read"):
        findings.append(Finding("A-16", "BLOCKING", "ISOLATION_NOT_RECORDED", ""))
    if not g["authoring"].get("source_hash_verified_before_authoring"):
        findings.append(Finding("A-16", "BLOCKING", "SOURCE_HASH_NOT_VERIFIED", ""))


CHECKS = [
    check_source_hash, check_clause_coverage, check_normative_provenance,
    check_no_unstated_numeric_threshold, check_no_preferred_realization,
    check_freedoms_not_contradicted, check_negative_cases,
    check_negative_cases_map_to_predicates, check_evidence_scope,
    check_no_structural_pass, check_release_requirement_present,
    check_stage_expectations, check_ambiguities, check_ids_unique_and_resolve,
    check_fixture_permissiveness, check_governance,
]


def audit(pack_dir=PACK, source_path=SOURCE):
    findings = []
    try:
        docs = load(pack_dir)
    except Exception as exc:                      # noqa: BLE001 - reported, not raised
        return [Finding("A-0", "BLOCKING", "PACK_PARSE_FAILURE", str(exc)[:200])]
    for fn in CHECKS:
        try:
            if fn in (check_source_hash, check_clause_coverage,
                      check_no_unstated_numeric_threshold):
                fn(docs, findings, source_path)
            else:
                fn(docs, findings)
        except Exception as exc:                  # noqa: BLE001
            findings.append(Finding(fn.__name__, "BLOCKING", "CHECK_ERROR", str(exc)[:200]))
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pack", default=PACK)
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    findings = audit(args.pack, args.source)
    blocking = [f for f in findings if f.severity == "BLOCKING"]
    report = {
        "oracle": "HELD_OUT_BENCHMARK_ORACLE",
        "benchmark_id": "BM-003",
        "checks_run": len(CHECKS),
        "findings": [f.as_dict() for f in findings],
        "counts": {"total": len(findings), "BLOCKING": len(blocking)},
        "result": "PASS" if not blocking else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not blocking else 1


if __name__ == "__main__":
    sys.exit(main())
