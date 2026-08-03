#!/usr/bin/env python3
"""Deterministic, read-only Oracle auditor — Passes 3A/3B/3C/3D.

Audit tooling, not pipeline code. It reads `ver3/oracles/` and the frozen
dossiers and emits exception findings only. It never writes to a pack.

The anti-self-confirmation mechanism is 3B/3C: every product pack declares
`admissible_realizations` (materially different designs that MUST all be
accepted) and `inadmissible_realizations` (designs that MUST be rejected).
Invariants declare `requires_tags`. The auditor mechanically evaluates every
invariant against every fixture, so an over-tight or over-loose Oracle is caught
by construction rather than by the author's opinion.
"""
from __future__ import annotations
import argparse, json, random, re, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
ORACLES, DOSSIERS = ROOT / "oracles", ROOT / "oracles" / "_dossiers"

ALLOWED_BASIS = {"DIRECT_USER_REQUIREMENT", "NECESSARY_PHYSICAL_CONSEQUENCE", "VERIFICATION_MINIMUM"}
REJECTED_BASIS = {"REFERENCE_REALIZATION_DETAIL", "CURRENT_TOOLING_LIMITATION", "UNSUPPORTED_INFERENCE"}

# Mechanism nouns that must not appear in product normative statements.
MECHANISM_LEXICON = [
    "pin hinge", "living hinge", "hinge", "snap-fit", "snap hook", "snap", "rack", "pinion",
    "lead screw", "leadscrew", "screw thread", "worm", "cam", "ratchet", "pawl", "gear",
    "four-bar", "linkage", "magnet", "dovetail", "detent", "capstan", "bearing", "bushing",
]
# Representation verbs that indicate a pipeline requirement, not a product one.
REPRESENTATION_LEXICON = [
    "expressed as", "declared reaction path", "recorded as", "dependency graph",
    "is expressed", "serialized", "field", "schema", "provenance",
]
TOOLING_LEXICON = ["currently", "not yet supported", "current implementation", "our solver", "the toolchain"]
# Dimensional / count leakage
NUMERIC_LEAK = re.compile(r"\b\d+(\.\d+)?\s*(mm|cm|m|kg|g|deg|degrees|N|newton)\b", re.I)
# A count is a defect when it PRESCRIBES how many elements a design has. A count
# preceded by a definite article is anaphoric — "between the two bodies" refers to
# the participants the statement just named, and is the arity of a relation rather
# than a realization decision. TOOL-004.
COUNT_LEAK = re.compile(
    r"(?<!the )\b(two|three|four|exactly \d+)\s+"
    r"(rails?|parts?|bodies|pieces|stops?|guides?|fasteners?|springs?|bearings?)\b", re.I)

STATUS_VALUES = {"PASS", "FAIL", "NOT_VERIFIED", "UNSUPPORTED", "INDETERMINATE", "NOT_APPLICABLE", "UNRESOLVED"}


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


def load_packs():
    packs = {}
    for tier in ("product_cases", "micro_oracles"):
        for d in sorted((ORACLES / tier).iterdir()) if (ORACLES / tier).exists() else []:
            if not d.is_dir():
                continue
            p = {"_tier": tier, "_dir": d, "_id": d.name}
            for f in ("normative", "freedoms", "stage_expectations", "negative_cases",
                      "evidence_scope", "realizations"):
                fp = d / f"{f}.yaml"
                p[f] = yaml.safe_load(fp.read_text()) if fp.exists() else None
            packs[d.name] = p
    return packs


def dossier_sections(case):
    """Section ids (S1, S2, ...) present in a frozen dossier. TOOL-003.

    Two of the three source shapes in this corpus are not REQ-numbered: a product
    case whose whole rank-1 source is one free-text command, and a micro-oracle
    whose rank-1 source is its declared capability statement. Requiring a
    `REQ-nnn` locator would report those as ungrounded while they are in fact
    grounded in a frozen section.
    """
    fp = DOSSIERS / f"DOS-{case}.md"
    if not fp.exists():
        return set()
    return set(re.findall(r"^##\s*(S\d+)\b", fp.read_text(), re.M))


def dossier_reqs(case):
    """Extract REQ ids + verbatim statements from a frozen dossier's tables."""
    fp = DOSSIERS / f"DOS-{case}.md"
    if not fp.exists():
        return {}
    out = {}
    for line in fp.read_text().splitlines():
        m = re.match(r"\|\s*(REQ-\d+)\s*\|\s*([^|]*)\|\s*([^|]*)\|", line)
        if m:
            out[m.group(1)] = m.group(3).strip()
    return out


# --------------------------------------------------------------- Pass 3A
REQUIRED_FILES = ["normative", "freedoms", "stage_expectations", "negative_cases",
                  "evidence_scope", "realizations"]


def pass_3a(packs):
    f = []
    for name, p in packs.items():
        # An unauthored pack must never pass silently.
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
            # 3A.3 every locator must resolve, whatever shape it has.
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
            if inv.get("basis_type") == "DIRECT_USER_REQUIREMENT":
                if not grounded:
                    f.append(Finding("3A", name, sid, "BLOCKING", "DIRECT_WITHOUT_RANK1_LOCATOR",
                                     f"basis_type=DIRECT_USER_REQUIREMENT, source_locators={locs}",
                                     "supply a locator that resolves in the frozen dossier, or change basis_type"))
                # A direct statement may not be grounded in a realization or a
                # legacy-behaviour section. Those are rank 4-6 by construction.
                if any(re.search(r"\bS[67]\b", str(l)) for l in locs):
                    f.append(Finding("3A", name, sid, "BLOCKING", "DIRECT_FROM_LEGACY_SECTION",
                                     f"basis_type=DIRECT_USER_REQUIREMENT cites S6/S7: {locs}",
                                     "S6 is realization detail and S7 is legacy behaviour; reclassify"))
                # A micro-oracle's only rank-1 source is its capability statement.
                if p["_tier"] == "micro_oracles" and not any("S1" in str(l) for l in grounded):
                    f.append(Finding("3A", name, sid, "BLOCKING", "MICRO_DIRECT_NOT_FROM_CAPABILITY",
                                     f"micro-oracle DIRECT statement not grounded in S1: {locs}",
                                     "ground it in the capability statement, or reclassify as derived"))
            # 3A.4 derived statement must show premises
            if inv.get("support_type") == "derived" and not inv.get("derivation_premises"):
                f.append(Finding("3A", name, sid, "BLOCKING", "DERIVED_WITHOUT_PREMISES",
                                 "support_type=derived with no derivation_premises",
                                 "state the premises, or mark support_type: direct"))
            # 3A.1 stronger than source: universal quantifier with no premise
            st = str(inv.get("statement", ""))
            if re.search(r"\b(every|all|always|never|only)\b", st, re.I) \
               and inv.get("support_type") == "derived" and not inv.get("exclusions"):
                f.append(Finding("3A", name, sid, "MAJOR", "POSSIBLY_STRONGER_THAN_SOURCE",
                                 f"universal quantifier in a derived statement, no exclusions declared: '{st[:90]}'",
                                 "declare exclusions or weaken the quantifier"))
            # 3A.5 silently reconciled conflict
            amb = inv.get("acknowledges_ambiguity")
            if name in AMBIGUOUS_PACKS and AMBIGUOUS_PACKS[name] in str(locs) + str(inv.get("sources", "")) and not amb:
                f.append(Finding("3A", name, sid, "BLOCKING", "AMBIGUITY_SILENTLY_RECONCILED",
                                 f"touches ambiguous source {AMBIGUOUS_PACKS[name]} without acknowledges_ambiguity",
                                 "add acknowledges_ambiguity"))
    return f


AMBIGUOUS_PACKS = {"BM-001-2": "REQ-010", "BM-002": "REQ-004", "C4-drawer": "gear"}


# --------------------------------------------------------------- Pass 3B / 3C
def evaluate(inv, fixture):
    """Does a fixture satisfy an invariant? Pure tag algebra — deterministic."""
    need = set(inv.get("requires_tags") or [])
    forbid = set(inv.get("forbids_tags") or [])
    have = set(fixture.get("tags") or [])
    return need <= have and not (forbid & have)


def pass_3b(packs):
    f = []
    for name, p in packs.items():
        n, r = p.get("normative"), p.get("realizations")
        if not n:
            continue
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
        for inv in n.get("invariants", []) or []:
            sid = inv.get("id", "?")
            # Necessity: an admissible design that violates the invariant disproves necessity.
            for a in adm:
                if not evaluate(inv, a):
                    sev = "BLOCKING"
                    dt = ("NECESSITY_COUNTEREXAMPLE" if inv.get("basis_type") == "NECESSARY_PHYSICAL_CONSEQUENCE"
                          else "REJECTS_ADMISSIBLE_REALIZATION")
                    f.append(Finding("3B", name, sid, sev, dt,
                                     f"admissible '{a['id']}' ({a.get('summary','')}) fails; "
                                     f"requires_tags={inv.get('requires_tags')} vs tags={a.get('tags')}",
                                     "generalize the invariant so this realization is admitted",
                                     [a["id"]]))
        # Weakness: an inadmissible design that passes every invariant.
        for bad in inadm:
            if all(evaluate(inv, bad) for inv in (n.get("invariants") or [])):
                f.append(Finding("3B", name, "-", "BLOCKING", "ADMITS_INADMISSIBLE_REALIZATION",
                                 f"inadmissible '{bad['id']}' ({bad.get('summary','')}) satisfies every invariant",
                                 "strengthen an invariant, or add one, so this design is rejected",
                                 [bad["id"]]))
    return f


def pass_3c(packs):
    f = []
    for name, p in packs.items():
        n, fr = p.get("normative"), p.get("freedoms")
        if not n:
            continue
        free_terms = []
        for x in (fr or {}).get("freedoms", []) or []:
            free_terms.append((x["id"], str(x.get("decision", "")).lower()))
        for inv in n.get("invariants", []) or []:
            sid, st = inv.get("id", "?"), str(inv.get("statement", ""))
            low = st.lower()
            b = inv.get("basis_type")
            if b in REJECTED_BASIS:
                f.append(Finding("3C", name, sid, "BLOCKING", "REJECTED_BASIS_TYPE",
                                 f"basis_type={b}", "remove or reclassify"))
            if b not in ALLOWED_BASIS:
                f.append(Finding("3C", name, sid, "BLOCKING", "UNKNOWN_BASIS_TYPE",
                                 f"basis_type={b}", f"use one of {sorted(ALLOWED_BASIS)}"))
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
            # An invariant that explicitly EXCLUDES a freedom's domain does not
            # constrain it. Without this, an invariant requiring a motion to
            # exist is falsely flagged against a freedom over the motion's type.
            excl = " ".join(str(x) for x in (inv.get("exclusions") or [])).lower()
            for fid, dec in free_terms:
                key = [w for w in re.findall(r"[a-z]{5,}", dec) if w not in
                       ("which", "whether", "realizing", "family", "decision", "achieves", "between")]
                # 'states' and 'state' are one concept. A key set made of stem
                # variants co-occurs trivially and is not evidence of overlap.
                seen = set()
                key = [w for w in key
                       if not (w.rstrip("s") in seen or seen.add(w.rstrip("s")))]
                if key and all(w in excl for w in key[:3]):
                    continue          # domain explicitly excluded by the invariant
                if fid in (inv.get("related_freedoms") or []) and excl:
                    continue          # author declared the relation and stated exclusions
                if key and sum(1 for w in key[:3] if w in low) == len(key[:3]) and len(key) >= 2:
                    f.append(Finding("3C", name, sid, "MAJOR", "NORMATIVE_CONSTRAINS_DECLARED_FREEDOM",
                                     f"statement overlaps freedom {fid} ('{dec[:60]}')",
                                     "narrow the invariant or withdraw the freedom", [fid]))
        # micro-oracle must stay mechanism-neutral in its own identity
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
        # delta must not compare against a generated parent design
        blob = json.dumps({k: v for k, v in p.items() if k not in ("_dir",)}, default=str).lower()
        for pat in ("differ from the bm-001 result", "differs from the bm-001", "compared to the parent design",
                    "the bm-001 result"):
            if pat in blob:
                f.append(Finding("3D", name, "-", "BLOCKING", "GENERATED_PARENT_COMPARISON",
                                 f"'{pat}' present", "test the delta requirement directly on the child design"))
        # freedom vs invariant, invariant vs unresolved
        unres = {u["id"]: u for u in (n.get("required_unresolved") or [])}
        for inv in n.get("invariants", []) or []:
            for u in inv.get("related_unresolved") or []:
                if u not in unres and not any(u in packs[q]["normative"].get("required_unresolved", []) and False
                                              for q in packs):
                    if u not in unres:
                        f.append(Finding("3D", name, inv["id"], "MAJOR", "UNRESOLVED_REF_NOT_FOUND",
                                         f"related_unresolved {u} undefined here", "define it or drop the reference"))
        # status semantics
        se = p.get("stage_expectations") or {}
        for sid, blk in (se.get("stages") or {}).items():
            if "expected_outcomes" in blk:
                f.append(Finding("3D", name, sid, "BLOCKING", "FIXED_STAGE11_OUTCOME",
                                 f"expected_outcomes present at {sid}", "replace with conditional outcome_rules"))
            for rid, rule in (blk.get("outcome_rules") or {}).items():
                if not isinstance(rule, dict) or "pass_requires" not in rule:
                    f.append(Finding("3D", name, f"{sid}:{rid}", "BLOCKING", "OUTCOME_RULE_NOT_CONDITIONAL",
                                     f"{rule}", "give pass_requires + otherwise"))
                else:
                    for k in ("otherwise", "if_capability_absent"):
                        v = rule.get(k)
                        if v and v not in STATUS_VALUES:
                            f.append(Finding("3D", name, f"{sid}:{rid}", "MAJOR", "INVALID_STATUS_VALUE",
                                             f"{k}={v}", f"use one of {sorted(STATUS_VALUES)}"))
    return f


PASSES = {"3A": pass_3a, "3B": pass_3b, "3C": pass_3c, "3D": pass_3d}


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
           "shuffle_seed": a.shuffle_seed,
           "counts": {"total": len(findings), "BLOCKING": len(blocking),
                      "MAJOR": sum(1 for x in findings if x.sev == "MAJOR")},
           "findings": [x.d() for x in findings]}
    if a.json_out:
        a.json_out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("packs_audited", "passes_run", "shuffle_seed", "counts")}, indent=2))
    for x in findings:
        print(f"  [{x.sev:8s}] {x.id} {x.pack}/{x.sid} {x.defect}")
        print(f"             evidence : {x.evidence[:150]}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
