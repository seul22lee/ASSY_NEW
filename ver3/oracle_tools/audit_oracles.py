#!/usr/bin/env python3
"""Deterministic, read-only Oracle auditor — passes 3A/3B/3C/3D/3E.

SCOPE — read this before trusting a clean report.

What this tool CAN establish:
  * structural and referential integrity of the pack files;
  * that every declared locator resolves in a frozen dossier;
  * that policy-required fields are present;
  * that the physical-design and evidence domains are not mixed;
  * that, UNDER THE AUTHOR'S OWN TAG ASSIGNMENTS, no invariant rejects a fixture
    declared admissible and no fixture declared inadmissible passes every
    invariant;
  * that every normative statement has a recorded source-entailment review and
    every admissible fixture a recorded plausibility review.

What this tool CANNOT establish, and does not claim:
  * that any statement is physically true;
  * that any fixture is geometrically realizable — tags are authored by the same
    hand that authored the invariants and are not independent evidence;
  * that a derivation is sound. `derivation_premises` are read for presence, not
    for validity;
  * that a predicate proves exactly its statement. Where that cannot be decided
    mechanically the tool demands a RECORDED SEMANTIC REVIEW instead of
    pretending to check it.

A clean report from this tool means the pack set is internally consistent and
every semantic question has been reviewed by a human-readable record. It is not
a proof of correctness. Physical validation by CAD or simulation is pending for
every fixture; see FIXTURE_PLAUSIBILITY_REVIEW.yaml.

It never writes to a pack and never runs as part of any pipeline.
"""
from __future__ import annotations
import argparse, json, random, re, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
ORACLES, DOSSIERS = ROOT / "oracles", ROOT / "oracles" / "_dossiers"
ENTAILMENT = ORACLES / "SOURCE_ENTAILMENT_REVIEW.yaml"
PLAUSIBILITY = ORACLES / "FIXTURE_PLAUSIBILITY_REVIEW.yaml"

# ------------------------------------------------------------------ vocabulary
PRODUCT_BASIS = {"DIRECT_USER_REQUIREMENT", "NECESSARY_PHYSICAL_CONSEQUENCE", "VERIFICATION_MINIMUM"}
# SF-1.3: a micro-oracle has no user. Its capability statement was project-authored
# and frozen; it grounds statements, but its authority is human-reviewable and it
# must never be presented as rank-1 user language.
CAPABILITY_BASIS = {"PROJECT_DEFINED_CAPABILITY", "NECESSARY_PHYSICAL_CONSEQUENCE", "VERIFICATION_MINIMUM"}
ALLOWED_BASIS = PRODUCT_BASIS | CAPABILITY_BASIS
REJECTED_BASIS = {"REFERENCE_REALIZATION_DETAIL", "CURRENT_TOOLING_LIMITATION", "UNSUPPORTED_INFERENCE"}

BLOCK_SCOPES = {"blocks_structural_predicate", "blocks_quantitative_acceptance",
                "blocks_PASS", "blocks_evidence_interpretation"}
UNRESOLVED_KINDS = {"quantitative", "qualitative", "interpretive", "structural_choice"}

MECHANISM_LEXICON = [
    "pin hinge", "living hinge", "hinge", "snap-fit", "snap hook", "snap", "rack", "pinion",
    "lead screw", "leadscrew", "screw thread", "worm", "cam", "ratchet", "pawl", "gear",
    "four-bar", "linkage", "magnet", "dovetail", "detent", "capstan", "bearing", "bushing",
]
REPRESENTATION_LEXICON = [
    "expressed as", "declared reaction path", "recorded as", "dependency graph",
    "is expressed", "serialized", "field", "schema", "provenance",
]
TOOLING_LEXICON = ["currently", "not yet supported", "current implementation", "our solver", "the toolchain"]
NUMERIC_LEAK = re.compile(r"\b\d+(\.\d+)?\s*(mm|cm|m|kg|g|deg|degrees|N|newton)\b", re.I)
# SF/TOOL-004: a count behind a definite article is anaphoric — "between the two
# bodies" is the arity of a relation, not a prescribed part count.
COUNT_LEAK = re.compile(
    r"(?<!the )\b(two|three|four|exactly \d+)\s+"
    r"(rails?|parts?|bodies|pieces|stops?|guides?|fasteners?|springs?|bearings?)\b", re.I)

STATUS_VALUES = {"PASS", "FAIL", "NOT_VERIFIED", "UNSUPPORTED", "INDETERMINATE",
                 "NOT_APPLICABLE", "UNRESOLVED"}
AMBIGUOUS_PACKS = {"BM-001-2": "REQ-010", "BM-002": "REQ-004"}

# Support/reaction predicates must be conditional on the load actually carried.
SUPPORT_NOUNS = re.compile(r"\b(radial|axial|transverse|thrust)\b", re.I)
UNIVERSAL_QUANT = re.compile(r"\bfor (each|every)\b|\bevery\b|\ball\b", re.I)
LOAD_QUALIFIER = re.compile(r"\b(carr(y|ies|ying)|loaded|bear(s|ing)?|it carries|actually carries|"
                            r"where|component it|components it)\b", re.I)
TERMINAL_TAG = re.compile(r"terminal|extreme|_bound|bound_|ends_physically", re.I)


class Finding:
    _n = 0

    def __init__(self, pas, pack, sid, sev, defect, evidence, correction, dependants=None):
        Finding._n += 1
        self.id = f"F-{pas}-{Finding._n:03d}"
        self.pas, self.pack, self.sid, self.sev = pas, pack, sid, sev
        self.defect, self.evidence, self.correction = defect, evidence, correction
        self.dependants = dependants or []

    def d(self):
        return {"finding_id": self.id, "pass": self.pas, "pack": self.pack, "statement_id": self.sid,
                "severity": self.sev, "defect_type": self.defect, "source_evidence": self.evidence,
                "minimal_correction": self.correction, "affected_dependants": self.dependants}


REQUIRED_FILES = ["normative", "freedoms", "stage_expectations", "negative_cases",
                  "evidence_scope", "realizations", "evidence_cases"]


def load_packs():
    packs = {}
    for tier in ("product_cases", "micro_oracles"):
        d0 = ORACLES / tier
        for d in sorted(d0.iterdir()) if d0.exists() else []:
            if not d.is_dir():
                continue
            p = {"_tier": tier, "_dir": d, "_id": d.name}
            for f in REQUIRED_FILES:
                fp = d / f"{f}.yaml"
                p[f] = yaml.safe_load(fp.read_text()) if fp.exists() else None
            packs[d.name] = p
    return packs


def load_review(path, key):
    if not path.exists():
        return None
    doc = yaml.safe_load(path.read_text()) or {}
    return {r[key]: r for r in (doc.get("reviews") or []) if isinstance(r, dict) and key in r}


def dossier_sections(case):
    """Section ids (S1, S2, ...) present in a frozen dossier."""
    fp = DOSSIERS / f"DOS-{case}.md"
    if not fp.exists():
        return set()
    return set(re.findall(r"^##\s*(S\d+)\b", fp.read_text(), re.M))


def dossier_reqs(case):
    """REQ ids + verbatim statements from a frozen dossier's tables."""
    fp = DOSSIERS / f"DOS-{case}.md"
    if not fp.exists():
        return {}
    out = {}
    for line in fp.read_text().splitlines():
        m = re.match(r"\|\s*(REQ-\d+)\s*\|\s*([^|]*)\|\s*([^|]*)\|", line)
        if m:
            out[m.group(1)] = m.group(3).strip()
    return out


def phys_vocab(p):
    r = p.get("realizations") or {}
    return set((r.get("physical_tag_vocabulary") or {}).keys())


def evid_vocab(p):
    e = p.get("evidence_cases") or {}
    return set((e.get("evidence_tag_vocabulary") or {}).keys())


def all_unresolved_ids(packs, name):
    """Own ids plus every ancestor's — fixes the former unreachable check."""
    ids, seen, cur = set(), set(), name
    while cur and cur in packs and cur not in seen:
        seen.add(cur)
        n = packs[cur].get("normative") or {}
        ids |= {u["id"] for u in (n.get("required_unresolved") or []) if "id" in u}
        cur = n.get("inherits")
    return ids


# --------------------------------------------------------------- Pass 3A
def pass_3a(packs):
    f = []
    for name, p in packs.items():
        for req in REQUIRED_FILES:
            if p.get(req) is None:
                f.append(Finding("3A", name, "-", "BLOCKING", "PACK_FILE_MISSING",
                                 f"{req}.yaml absent", f"author {req}.yaml"))
        n = p.get("normative")
        if not n:
            continue
        if not (n.get("invariants") or []):
            f.append(Finding("3A", name, "-", "BLOCKING", "PACK_HAS_NO_INVARIANTS",
                             "normative.yaml declares no invariants", "author the invariants"))
        reqs = dossier_reqs(name)
        parent = n.get("inherits")
        if parent:
            reqs = {**dossier_reqs(parent), **reqs}
        for inv in n.get("invariants", []) or []:
            sid = inv.get("id", "?")
            locs = inv.get("source_locators") or []
            sections = dossier_sections(name) | (dossier_sections(parent) if parent else set())
            grounded = []
            for l in locs:
                st_l = str(l)
                mreq = re.search(r"REQ-\d+", st_l)
                if mreq:
                    if reqs and mreq.group(0) not in reqs:
                        f.append(Finding("3A", name, sid, "BLOCKING", "LOCATOR_DOES_NOT_RESOLVE",
                                         f"cites {mreq.group(0)}, absent from frozen dossier DOS-{name}.md",
                                         "cite a requirement present in the dossier, or reclassify"))
                    else:
                        grounded.append(st_l)
                    continue
                msec = re.search(r"\bS\d+\b", st_l)
                if msec and "DOS-" in st_l:
                    if sections and msec.group(0) not in sections:
                        f.append(Finding("3A", name, sid, "BLOCKING", "LOCATOR_DOES_NOT_RESOLVE",
                                         f"cites section {msec.group(0)}, absent from the frozen dossier",
                                         "cite a section present in the dossier, or reclassify"))
                    else:
                        grounded.append(st_l)
            b = inv.get("basis_type")
            if b in ("DIRECT_USER_REQUIREMENT", "PROJECT_DEFINED_CAPABILITY"):
                if not grounded:
                    f.append(Finding("3A", name, sid, "BLOCKING", "DIRECT_WITHOUT_RANK1_LOCATOR",
                                     f"basis_type={b}, source_locators={locs}",
                                     "supply a locator that resolves in the frozen dossier, or change basis_type"))
                if any(re.search(r"\bS[67]\b", str(l)) for l in locs):
                    f.append(Finding("3A", name, sid, "BLOCKING", "DIRECT_FROM_LEGACY_SECTION",
                                     f"{b} cites S6/S7: {locs}",
                                     "S6 is realization detail and S7 is legacy behaviour; reclassify"))
            if b == "PROJECT_DEFINED_CAPABILITY" and not any("S1" in str(l) for l in grounded):
                f.append(Finding("3A", name, sid, "BLOCKING", "CAPABILITY_NOT_FROM_CAPABILITY_STATEMENT",
                                 f"PROJECT_DEFINED_CAPABILITY not grounded in S1: {locs}",
                                 "ground it in the capability statement, or reclassify as derived"))
            if inv.get("support_type") == "derived" and not inv.get("derivation_premises"):
                f.append(Finding("3A", name, sid, "BLOCKING", "DERIVED_WITHOUT_PREMISES",
                                 "support_type=derived with no derivation_premises",
                                 "state the premises, or mark support_type: direct"))
            st = str(inv.get("statement", ""))
            if re.search(r"\b(every|all|always|never|only)\b", st, re.I) \
               and inv.get("support_type") == "derived" and not inv.get("exclusions"):
                f.append(Finding("3A", name, sid, "MAJOR", "POSSIBLY_STRONGER_THAN_SOURCE",
                                 f"universal quantifier in a derived statement, no exclusions declared: '{st[:90]}'",
                                 "declare exclusions or weaken the quantifier"))
            amb = inv.get("acknowledges_ambiguity")
            if name in AMBIGUOUS_PACKS and AMBIGUOUS_PACKS[name] in str(locs) and not amb:
                f.append(Finding("3A", name, sid, "BLOCKING", "AMBIGUITY_SILENTLY_RECONCILED",
                                 f"touches ambiguous source {AMBIGUOUS_PACKS[name]} without acknowledges_ambiguity",
                                 "add acknowledges_ambiguity"))
    return f


# --------------------------------------------------------------- Pass 3B / 3C
def evaluate(inv, fixture, domain):
    """Does a fixture satisfy an invariant? Pure tag algebra, per domain."""
    key = "requires_evidence_tags" if domain == "evidence" else "requires_tags"
    need = set(inv.get(key) or [])
    forbid = set(inv.get("forbids_tags") or [])
    have = set(fixture.get("tags") or [])
    return need <= have and not (forbid & have)


def split_invariants(n):
    phys, evid = [], []
    for inv in n.get("invariants", []) or []:
        (evid if inv.get("basis_type") == "VERIFICATION_MINIMUM" else phys).append(inv)
    return phys, evid


def pass_3b(packs):
    f = []
    for name, p in packs.items():
        n, r, e = p.get("normative"), p.get("realizations"), p.get("evidence_cases")
        if not n:
            continue
        phys, evid = split_invariants(n)
        if not r:
            f.append(Finding("3B", name, "-", "BLOCKING", "NO_REALIZATION_FIXTURES",
                             "realizations.yaml absent", "declare admissible and inadmissible realizations"))
            continue
        adm = r.get("admissible_realizations") or []
        inadm = r.get("inadmissible_realizations") or []
        if len(adm) < 2:
            f.append(Finding("3B", name, "-", "BLOCKING", "FEWER_THAN_TWO_ADMISSIBLE",
                             f"{len(adm)} admissible realization(s)",
                             "declare at least two materially different admissible realizations"))
        for inv in phys:
            sid = inv.get("id", "?")
            for a in adm:
                if not evaluate(inv, a, "physical"):
                    dt = ("NECESSITY_COUNTEREXAMPLE"
                          if inv.get("basis_type") == "NECESSARY_PHYSICAL_CONSEQUENCE"
                          else "REJECTS_ADMISSIBLE_REALIZATION")
                    f.append(Finding("3B", name, sid, "BLOCKING", dt,
                                     f"admissible '{a['id']}' ({a.get('summary', '')[:80]}) fails; "
                                     f"requires_tags={inv.get('requires_tags')} vs tags={a.get('tags')}",
                                     "generalize the invariant so this realization is admitted",
                                     [a["id"]]))
        for bad in inadm:
            if phys and all(evaluate(inv, bad, "physical") for inv in phys):
                f.append(Finding("3B", name, "-", "BLOCKING", "ADMITS_INADMISSIBLE_REALIZATION",
                                 f"inadmissible '{bad['id']}' ({bad.get('summary', '')[:80]}) satisfies every physical invariant",
                                 "strengthen an invariant, or add one, so this design is rejected",
                                 [bad["id"]]))
        # evidence domain, evaluated separately — never against physical fixtures
        if evid:
            eadm = (e or {}).get("admissible_evidence_cases") or []
            einadm = (e or {}).get("inadmissible_evidence_cases") or []
            if len(eadm) < 2:
                f.append(Finding("3B", name, "-", "BLOCKING", "FEWER_THAN_TWO_ADMISSIBLE_EVIDENCE_CASES",
                                 f"{len(eadm)} admissible evidence case(s) for {len(evid)} VERIFICATION_MINIMUM statement(s)",
                                 "declare at least two materially different admissible evidence cases"))
            for inv in evid:
                for a in eadm:
                    if not evaluate(inv, a, "evidence"):
                        f.append(Finding("3B", name, inv.get("id", "?"), "BLOCKING",
                                         "REJECTS_ADMISSIBLE_EVIDENCE_CASE",
                                         f"admissible evidence '{a['id']}' fails; "
                                         f"requires_evidence_tags={inv.get('requires_evidence_tags')} vs {a.get('tags')}",
                                         "generalize the verification minimum", [a["id"]]))
            for bad in einadm:
                if all(evaluate(inv, bad, "evidence") for inv in evid):
                    f.append(Finding("3B", name, "-", "BLOCKING", "ADMITS_INADMISSIBLE_EVIDENCE_CASE",
                                     f"inadmissible evidence '{bad['id']}' satisfies every verification minimum",
                                     "strengthen a verification minimum", [bad["id"]]))
    return f


def pass_3c(packs):
    f = []
    for name, p in packs.items():
        n, fr = p.get("normative"), p.get("freedoms")
        if not n:
            continue
        free_terms = [(x["id"], str(x.get("decision", "")).lower())
                      for x in (fr or {}).get("freedoms", []) or []]
        allowed = CAPABILITY_BASIS if p["_tier"] == "micro_oracles" else PRODUCT_BASIS
        for inv in n.get("invariants", []) or []:
            sid, st = inv.get("id", "?"), str(inv.get("statement", ""))
            low = st.lower()
            b = inv.get("basis_type")
            if b in REJECTED_BASIS:
                f.append(Finding("3C", name, sid, "BLOCKING", "REJECTED_BASIS_TYPE",
                                 f"basis_type={b}", "remove or reclassify"))
            elif b not in ALLOWED_BASIS:
                f.append(Finding("3C", name, sid, "BLOCKING", "UNKNOWN_BASIS_TYPE",
                                 f"basis_type={b}", f"use one of {sorted(ALLOWED_BASIS)}"))
            elif b not in allowed:
                dt = ("MICRO_ORACLE_CLAIMS_USER_REQUIREMENT" if p["_tier"] == "micro_oracles"
                      else "PRODUCT_CASE_CLAIMS_PROJECT_CAPABILITY")
                f.append(Finding("3C", name, sid, "BLOCKING", dt,
                                 f"basis_type={b} in tier {p['_tier']}",
                                 "a micro-oracle has no user; a product case has a user. Use the tier's basis set"))
            for term in MECHANISM_LEXICON:
                if re.search(rf"\b{re.escape(term)}\b", low):
                    f.append(Finding("3C", name, sid, "BLOCKING", "MECHANISM_NAME_IN_NORMATIVE",
                                     f"'{term}' in: '{st[:110]}'",
                                     "restate capability-neutrally; move the mechanism to a reference realization"))
                    break
            for term in REPRESENTATION_LEXICON:
                if term in low:
                    f.append(Finding("3C", name, sid, "BLOCKING", "REPRESENTATION_REQUIREMENT_IN_NORMATIVE",
                                     f"'{term}' in: '{st[:110]}'", "move to stage_expectations"))
                    break
            for term in TOOLING_LEXICON:
                if term in low:
                    f.append(Finding("3C", name, sid, "BLOCKING", "TOOLING_LIMITATION_IN_NORMATIVE",
                                     f"'{term}' in: '{st[:110]}'", "move to evidence_scope"))
                    break
            if NUMERIC_LEAK.search(st) and not inv.get("quantity_is_user_stated"):
                f.append(Finding("3C", name, sid, "BLOCKING", "DIMENSION_LEAK_IN_NORMATIVE",
                                 f"numeric quantity in: '{st[:110]}'",
                                 "remove, or set quantity_is_user_stated with a rank-1 locator"))
            if COUNT_LEAK.search(st):
                f.append(Finding("3C", name, sid, "BLOCKING", "PART_COUNT_IN_NORMATIVE",
                                 f"count in: '{st[:110]}'", "remove the count"))
            excl = " ".join(str(x) for x in (inv.get("exclusions") or [])).lower()
            for fid, dec in free_terms:
                key = [w for w in re.findall(r"[a-z]{5,}", dec) if w not in
                       ("which", "whether", "realizing", "family", "decision", "achieves", "between")]
                seen = set()
                key = [w for w in key
                       if not (w.rstrip("s") in seen or seen.add(w.rstrip("s")))]
                if key and all(w in excl for w in key[:3]):
                    continue
                if fid in (inv.get("related_freedoms") or []) and excl:
                    continue
                if key and sum(1 for w in key[:3] if w in low) == len(key[:3]) and len(key) >= 2:
                    f.append(Finding("3C", name, sid, "MAJOR", "NORMATIVE_CONSTRAINS_DECLARED_FREEDOM",
                                     f"statement overlaps freedom {fid} ('{dec[:60]}')",
                                     "narrow the invariant or withdraw the freedom", [fid]))
        if p["_tier"] == "micro_oracles":
            if any(re.search(rf"\b{re.escape(t)}\b", name.lower()) for t in MECHANISM_LEXICON):
                f.append(Finding("3C", name, "-", "BLOCKING", "MICRO_ORACLE_NAMED_FOR_MECHANISM",
                                 f"pack id '{name}'", "rename to a capability"))
    return f


# --------------------------------------------------------------- Pass 3D
def pass_3d(packs):
    f = []
    for name, p in packs.items():
        n = p.get("normative")
        if not n:
            continue
        parent = n.get("inherits")
        if parent:
            if parent not in packs:
                f.append(Finding("3D", name, "-", "BLOCKING", "PARENT_NOT_FOUND", f"inherits {parent}", "fix"))
            else:
                pn = packs[parent]["normative"]
                pids = {i["id"] for i in (pn.get("invariants") or [])}
                pstat = {str(i.get("statement", "")).strip().lower() for i in (pn.get("invariants") or [])}
                for inv in n.get("invariants", []) or []:
                    if str(inv.get("statement", "")).strip().lower() in pstat:
                        f.append(Finding("3D", name, inv["id"], "MAJOR", "PARENT_REQUIREMENT_DUPLICATED",
                                         "statement identical to a parent invariant", "remove; inheritance covers it"))
                for ov in n.get("overrides", []) or []:
                    tgt, rel = ov.get("overrides"), ov.get("relation")
                    if tgt not in pids:
                        f.append(Finding("3D", name, tgt or "?", "BLOCKING", "OVERRIDE_TARGET_MISSING",
                                         f"overrides {tgt}, not in {parent}", "fix the target id"))
                    if rel not in ("narrows", "replaces", "contradicts"):
                        f.append(Finding("3D", name, tgt or "?", "BLOCKING", "OVERRIDE_RELATION_INVALID",
                                         f"relation={rel}", "use narrows | replaces | contradicts"))
                    if not ov.get("rank1_support"):
                        f.append(Finding("3D", name, tgt or "?", "BLOCKING", "OVERRIDE_WITHOUT_RANK1_SUPPORT",
                                         "no rank1_support", "cite the rank-1 delta source"))
        blob = json.dumps({k: v for k, v in p.items() if k not in ("_dir",)}, default=str).lower()
        for pat in ("differ from the bm-001 result", "differs from the bm-001",
                    "compared to the parent design", "the bm-001 result"):
            if pat in blob:
                f.append(Finding("3D", name, "-", "BLOCKING", "GENERATED_PARENT_COMPARISON",
                                 f"'{pat}' present", "test the delta requirement directly on the child design"))
        # unresolved references — resolved across the inheritance chain (dead
        # `and False` branch removed)
        known = all_unresolved_ids(packs, name)
        for inv in n.get("invariants", []) or []:
            for u in inv.get("related_unresolved") or []:
                if u not in known:
                    f.append(Finding("3D", name, inv["id"], "BLOCKING", "UNRESOLVED_REF_NOT_FOUND",
                                     f"related_unresolved {u} is defined neither here nor in any ancestor",
                                     "define it or drop the reference"))
        se = p.get("stage_expectations") or {}
        for sid, blk in (se.get("stages") or {}).items():
            if not isinstance(blk, dict):
                continue
            if "expected_outcomes" in blk:
                f.append(Finding("3D", name, sid, "BLOCKING", "FIXED_STAGE11_OUTCOME",
                                 f"expected_outcomes present at {sid}", "replace with conditional outcome_rules"))
            for rid, rule in (blk.get("outcome_rules") or {}).items():
                if not isinstance(rule, dict) or "pass_requires" not in rule:
                    f.append(Finding("3D", name, f"{sid}:{rid}", "BLOCKING", "OUTCOME_RULE_NOT_CONDITIONAL",
                                     f"{rule}", "give pass_requires + otherwise"))
                else:
                    for k, v in rule.items():
                        if k.startswith("if_") or k == "otherwise":
                            if isinstance(v, str) and v.isupper() and v not in STATUS_VALUES:
                                f.append(Finding("3D", name, f"{sid}:{rid}", "MAJOR", "INVALID_STATUS_VALUE",
                                                 f"{k}={v}", f"use one of {sorted(STATUS_VALUES)}"))
    return f


# --------------------------------------------------------------- Pass 3E
def pass_3e(packs):
    """Policy compliance, domain separation, source coverage, review coverage."""
    f = []
    ent = load_review(ENTAILMENT, "statement_id")
    plaus = load_review(PLAUSIBILITY, "fixture_id")
    if ent is None:
        f.append(Finding("3E", "-", "-", "BLOCKING", "SOURCE_ENTAILMENT_REVIEW_REQUIRED",
                         f"{ENTAILMENT.name} absent", "create the source-entailment review record"))
    if plaus is None:
        f.append(Finding("3E", "-", "-", "BLOCKING", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
                         f"{PLAUSIBILITY.name} absent", "create the fixture plausibility review record"))

    for name, p in packs.items():
        n = p.get("normative")
        if not n:
            continue
        pv, ev = phys_vocab(p), evid_vocab(p)

        # Does the frozen source itself declare terminal states? Verified by
        # locating the declared verbatim fragment in the dossier.
        sdt = n.get("source_declares_terminal_states") or {}
        source_bounds_ok = False
        if sdt.get("value"):
            # Dossiers are hard-wrapped, so a quoted fragment legitimately spans a
            # line break. Compare on whitespace-normalized text.
            norm = lambda t: re.sub(r"\s+", " ", t).strip().lower()
            frag = norm(str(sdt.get("verbatim_fragment") or ""))
            dfp = DOSSIERS / f"DOS-{name}.md"
            if frag and dfp.exists() and frag in norm(dfp.read_text()):
                source_bounds_ok = True
            else:
                f.append(Finding("3E", name, "-", "BLOCKING", "UNCONDITIONAL_TERMINAL_BOUND",
                                 "source_declares_terminal_states asserted but its verbatim_fragment "
                                 "is not present in the frozen dossier",
                                 "quote a fragment that actually appears in the dossier, or withdraw the claim"))

        for inv in n.get("invariants", []) or []:
            sid = inv.get("id", "?")
            b = inv.get("basis_type")

            # 1.2 policy fields on every VERIFICATION_MINIMUM
            if b == "VERIFICATION_MINIMUM":
                if not inv.get("enables_claim"):
                    f.append(Finding("3E", name, sid, "BLOCKING", "POLICY_FIELD_MISSING",
                                     "VERIFICATION_MINIMUM without enables_claim",
                                     "state exactly which claim becomes admissible when the minimum is satisfied"))
                if not inv.get("requires_evidence_tags"):
                    f.append(Finding("3E", name, sid, "BLOCKING", "POLICY_FIELD_MISSING",
                                     "VERIFICATION_MINIMUM without requires_evidence_tags",
                                     "declare the evidence tags this minimum requires"))
                if inv.get("requires_tags"):
                    f.append(Finding("3E", name, sid, "BLOCKING", "DESIGN_EVIDENCE_TAG_MIXED",
                                     f"VERIFICATION_MINIMUM carries physical requires_tags={inv.get('requires_tags')}",
                                     "a verification minimum constrains evidence, not physical designs"))
            else:
                if inv.get("requires_evidence_tags"):
                    f.append(Finding("3E", name, sid, "BLOCKING", "DESIGN_EVIDENCE_TAG_MIXED",
                                     f"physical invariant carries requires_evidence_tags={inv.get('requires_evidence_tags')}",
                                     "a physical design must not be inadmissible for want of a test"))
                stray = set(inv.get("requires_tags") or []) - pv
                if stray:
                    f.append(Finding("3E", name, sid, "BLOCKING", "DESIGN_EVIDENCE_TAG_MIXED",
                                     f"requires_tags {sorted(stray)} not in the physical tag vocabulary",
                                     "declare the tag in physical_tag_vocabulary or move the invariant to the evidence domain"))
            stray_e = set(inv.get("requires_evidence_tags") or []) - ev
            if stray_e:
                f.append(Finding("3E", name, sid, "BLOCKING", "DESIGN_EVIDENCE_TAG_MIXED",
                                 f"requires_evidence_tags {sorted(stray_e)} not in the evidence tag vocabulary",
                                 "declare the tag in evidence_tag_vocabulary"))

            # 11: support/reaction predicates must be load-conditional
            pred = str(inv.get("verification_predicate", ""))
            if SUPPORT_NOUNS.search(pred) and UNIVERSAL_QUANT.search(pred) \
               and not LOAD_QUALIFIER.search(pred) and not inv.get("applies_when"):
                f.append(Finding("3E", name, sid, "BLOCKING", "CONDITIONAL_LOAD_DOMAIN_VIOLATION",
                                 f"support/reaction predicate quantifies universally with no load qualifier: '{pred[:120]}'",
                                 "restrict the domain to elements that carry the relevant load, or declare applies_when"))

            # 11: terminal-bound obligations must be conditional UNLESS the frozen
            # source itself declares terminal states. The exemption is verified
            # against the dossier text, not taken on the pack's word.
            if any(TERMINAL_TAG.search(t or "") for t in (inv.get("requires_tags") or [])) \
               and not inv.get("applies_when") and not source_bounds_ok:
                f.append(Finding("3E", name, sid, "BLOCKING", "UNCONDITIONAL_TERMINAL_BOUND",
                                 f"terminal-bound tag {inv.get('requires_tags')} with no applies_when, "
                                 f"and the frozen source declares no terminal state",
                                 "apply only where the design declares a terminal state as a physical end "
                                 "of travel, or ground a source_declares_terminal_states fragment in the dossier"))

            # 11: predicate stronger than statement — mechanical hint, human record
            stq = bool(UNIVERSAL_QUANT.search(str(inv.get("statement", ""))))
            pq = bool(UNIVERSAL_QUANT.search(pred))
            rec = (ent or {}).get(sid)
            if pq and not stq and not (rec and rec.get("predicate_scope_reviewed")):
                f.append(Finding("3E", name, sid, "MAJOR", "PREDICATE_STRONGER_THAN_STATEMENT",
                                 "predicate carries a universal quantifier the statement does not, "
                                 "and no recorded review confirms the scopes match",
                                 "record predicate_scope_reviewed in SOURCE_ENTAILMENT_REVIEW.yaml, or narrow the predicate"))

            # 1.5 every statement needs a recorded entailment review
            if ent is not None:
                if sid not in ent:
                    f.append(Finding("3E", name, sid, "BLOCKING", "SOURCE_ENTAILMENT_REVIEW_REQUIRED",
                                     "no entry in SOURCE_ENTAILMENT_REVIEW.yaml",
                                     "review the statement against its source and record the result"))
                elif not ent[sid].get("review_result"):
                    f.append(Finding("3E", name, sid, "BLOCKING", "SOURCE_ENTAILMENT_REVIEW_REQUIRED",
                                     "entailment record has no review_result",
                                     "record directly_entailed | physically_necessary | conditional | unsupported"))
                elif ent[sid].get("review_result") == "unsupported":
                    f.append(Finding("3E", name, sid, "BLOCKING", "STATEMENT_REVIEWED_UNSUPPORTED",
                                     "entailment review concluded the statement is unsupported by its source",
                                     "remove, weaken or condition the statement"))

        # 1.4 unresolved block scopes
        for u in n.get("required_unresolved") or []:
            uid = u.get("id", "?")
            kind = u.get("kind")
            if kind not in UNRESOLVED_KINDS:
                f.append(Finding("3E", name, uid, "BLOCKING", "UNRESOLVED_BLOCK_SCOPE_INVALID",
                                 f"kind={kind}", f"use one of {sorted(UNRESOLVED_KINDS)}"))
            if "blocks" in u:
                f.append(Finding("3E", name, uid, "BLOCKING", "UNRESOLVED_BLOCK_SCOPE_INVALID",
                                 "legacy coarse `blocks:` relation still present",
                                 "replace with explicit block_scopes"))
            scopes = set(u.get("block_scopes") or [])
            bad = scopes - BLOCK_SCOPES
            if bad:
                f.append(Finding("3E", name, uid, "BLOCKING", "UNRESOLVED_BLOCK_SCOPE_INVALID",
                                 f"unknown block scope(s) {sorted(bad)}", f"use {sorted(BLOCK_SCOPES)}"))
            if "blocks_structural_predicate" in scopes and kind == "quantitative":
                f.append(Finding("3E", name, uid, "BLOCKING", "UNRESOLVED_BLOCK_SCOPE_INVALID",
                                 "a quantitative unknown blocks an independent structural predicate",
                                 "a missing quantity may withhold PASS or make an acceptance INDETERMINATE; "
                                 "it may not make a structural predicate underivable"))
            if "blocks_structural_predicate" in scopes and not u.get("structural_block_justification"):
                f.append(Finding("3E", name, uid, "BLOCKING", "UNRESOLVED_BLOCK_SCOPE_INVALID",
                                 "blocks_structural_predicate without structural_block_justification",
                                 "justify why the predicate's DOMAIN, not merely its threshold, is undefined"))

        # 11: rank-1 requirement coverage.
        # Coverage means a STRUCTURED citation - an invariant locator, an
        # unresolved-decision locator, a stage-11 evaluation rule, or an explicit
        # not-verified entry. A passing mention in a derivation premise or an
        # exclusion is not coverage, and an earlier version of this check counted
        # one, which let the BM-002 travel omission hide behind prose.
        reqs = dossier_reqs(name)
        if reqs:
            covered = set()
            def _harvest(x):
                for m in re.finditer(r"REQ-\d+", json.dumps(x, default=str)):
                    covered.add(m.group(0))
            for inv in n.get("invariants", []) or []:
                _harvest(inv.get("source_locators"))
            for u in n.get("required_unresolved") or []:
                _harvest(u.get("source_locators"))
            s11 = ((p.get("stage_expectations") or {}).get("stages") or {}).get("s11") or {}
            _harvest(s11.get("outcome_rules"))
            es = p.get("evidence_scope") or {}
            _harvest(es.get("not_verified"))
            for rid in reqs:
                if rid not in covered:
                    f.append(Finding("3E", name, rid, "BLOCKING", "DIRECT_REQUIREMENT_COVERAGE_GAP",
                                     f"rank-1 {rid} ('{reqs[rid][:60]}') is cited by no invariant locator, "
                                     f"no unresolved-decision locator, no stage-11 evaluation rule and no "
                                     f"not-verified entry",
                                     "carry it as an invariant, as an unresolved decision, or as an explicit not-verified item"))

        # 11: fixed candidate plurality
        se_blob = json.dumps(p.get("stage_expectations") or {}, default=str).lower()
        if "must survive" in se_blob:
            f.append(Finding("3E", name, "-", "BLOCKING", "FIXED_CANDIDATE_PLURALITY",
                             "stage expectations require a fixed number of candidates to survive",
                             "replace with the open-search rule: the space was not closed by library "
                             "availability, each rejection is reasoned, and an absent realizer yields UNSUPPORTED"))

        # 1.6 fixture plausibility review coverage
        if plaus is not None:
            for a in (p.get("realizations") or {}).get("admissible_realizations") or []:
                fid = a.get("id", "?")
                rec = plaus.get(fid)
                if not rec:
                    f.append(Finding("3E", name, fid, "BLOCKING", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
                                     "admissible fixture has no plausibility review record",
                                     "record its physical operation, assumptions, counterexample and status"))
                    continue
                if not rec.get("assumptions"):
                    f.append(Finding("3E", name, fid, "BLOCKING", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
                                     "plausibility record states no explicit assumptions",
                                     "state the geometric and physical assumptions the fixture depends on"))
                if rec.get("status") not in ("PHYSICALLY_PLAUSIBLE", "NEEDS_GEOMETRY_VALIDATION", "REJECTED"):
                    f.append(Finding("3E", name, fid, "BLOCKING", "FIXTURE_PHYSICAL_PLAUSIBILITY_UNVERIFIED",
                                     f"status={rec.get('status')}",
                                     "use PHYSICALLY_PLAUSIBLE | NEEDS_GEOMETRY_VALIDATION | REJECTED"))
                if rec.get("status") == "REJECTED":
                    f.append(Finding("3E", name, fid, "BLOCKING", "REJECTED_FIXTURE_STILL_ADMISSIBLE",
                                     "fixture reviewed as physically REJECTED but still listed as admissible",
                                     "remove or revise the fixture"))
    return f


PASSES = {"3A": pass_3a, "3B": pass_3b, "3C": pass_3c, "3D": pass_3d, "3E": pass_3e}

SCOPE_NOTE = ("This auditor checks structural, referential, policy and tag-algebra "
              "consistency, and that every semantic question carries a recorded human "
              "review. It does NOT establish physical truth: fixture tags are authored "
              "by the same hand as the invariants and are not independent evidence. "
              "CAD/physics validation is pending for every fixture.")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="p", choices=list(PASSES) + ["all"], default="all")
    ap.add_argument("--shuffle-seed", type=int, default=None)
    ap.add_argument("--json-out", type=Path)
    a = ap.parse_args(argv)

    packs = load_packs()
    if a.shuffle_seed is not None:
        rnd = random.Random(a.shuffle_seed)
        items = list(packs.items()); rnd.shuffle(items); packs = dict(items)
        for p in packs.values():
            n = p.get("normative")
            if n and n.get("invariants"):
                rnd.shuffle(n["invariants"])

    names = list(PASSES) if a.p == "all" else [a.p]
    findings = [x for nm in names for x in PASSES[nm](packs)]
    blocking = [x for x in findings if x.sev == "BLOCKING"]
    out = {"packs_audited": sorted(packs), "passes_run": names,
           "shuffle_seed": a.shuffle_seed, "auditor_scope": SCOPE_NOTE,
           "counts": {"total": len(findings), "BLOCKING": len(blocking),
                      "MAJOR": sum(1 for x in findings if x.sev == "MAJOR")},
           "findings": [x.d() for x in findings]}
    if a.json_out:
        a.json_out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("packs_audited", "passes_run", "shuffle_seed", "counts")}, indent=2))
    for x in findings:
        print(f"  [{x.sev:8s}] {x.id} {x.pack}/{x.sid} {x.defect}")
        print(f"             evidence : {x.evidence[:160]}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
