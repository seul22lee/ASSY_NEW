"""Measure the ENGINEERING MATURITY of an S01/S02 output, without comparing it
to any other output's content.

WHY THIS EXISTS
    "Do the probes reach the same quality as the benchmarks?" cannot be answered
    by diffing them. Different products must produce different engineering
    content, so any metric that rewards similarity to a benchmark answer is
    measuring the wrong thing and would quietly turn the benchmarks into target
    answers (development rules 1, 2 and 4).

    So every measure here is a property of ONE output judged against ITS OWN
    source and ITS OWN internal references. No benchmark output is an input to
    any score. Two outputs become comparable only because each was scored
    against itself.

WHAT IS DELIBERATELY NOT MEASURED
    Counts as such. "Ten requirements" is not better than four; a short request
    that yields four faithful requirements is more mature than one padded to
    ten. Counts appear in the report as context, never as a score.

    Vocabulary overlap with a reference. That is similarity, not maturity.

READING A SCORE
    Every metric is a fraction in [0, 1] with an explicit denominator, or None
    when its denominator is zero — which means "this output had no opportunity
    to exhibit this property", and is different from zero.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from ver3.assy_v3.knowledge.principle_library import (                     # noqa: E402
    FUNCTION_CLASSES, PRINCIPLE_FAMILIES)
from ver3.assy_v3.stages.s01_requirement_capture import (                  # noqa: E402
    DISTINCTIVE_MECHANISM_TOKENS, QUANTITY_CLASSES, SCENARIO_KINDS)
from ver3.assy_v3.stages.s02_obligation_and_candidates import PART_NOUNS   # noqa: E402

LIBRARY_NAMES = ({f["family"] for v in PRINCIPLE_FAMILIES.values() for f in v}
                 | set(FUNCTION_CLASSES))

DIRECTION_CLASSES = ("AXIAL", "TRANSVERSE", "RADIAL", "MOMENT", "GRAVITY", "NONE")
LOAD_KINDS = ("GRAVITY", "PAYLOAD", "ACTOR_APPLIED", "REACTION")
SCOPES = ("UNIVERSAL", "CANDIDATE_DISCRIMINATING")
SATISFIABLE_AT = ("s02", "s03", "s04", "s05")
ALTERNATIVES_KINDS = ("ENTITY_REFS", "PRINCIPLE_FAMILIES", "FREE_TEXT")

#: Qualifiers whose removal turns an approximate statement into a sharp one.
#: General English hedges, not a product vocabulary.
QUALIFIERS = ("approximately", "approx", "about", "around", "roughly", "some",
              "several", "a few", "up to", "at least", "at most", "or so",
              "nominal", "typical", "circa", "near", "close to")


def frac(numerator: int, denominator: int) -> Optional[float]:
    """None when there was no opportunity to exhibit the property at all."""
    return None if not denominator else round(numerator / float(denominator), 3)


def words(text: str) -> Set[str]:
    return set(re.findall(r"[a-z]+", (text or "").lower()))


def numerals(text: str) -> Set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text or ""))


def nonempty(value: Any) -> bool:
    """An empty list is a VALUE ("there are none"); None and "" are absences."""
    return value is not None and value != ""


def as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else ([] if value is None else [value])


def id_list(value: Any) -> List[str]:
    """Only the string items. A live model may nest an object where an id was
    asked for; that is a finding for the caller, not a crash for the profiler."""
    return [v for v in as_list(value) if isinstance(v, str)]


# ===========================================================================
# S01
# ===========================================================================
def profile_s01(out: Dict[str, Any], source: str) -> Dict[str, Any]:
    clauses = [c for c in out.get("source_clauses", []) if isinstance(c, dict)]
    reqs = [r for r in out.get("requirements", []) if isinstance(r, dict)]
    scens = [s for s in out.get("scenarios", []) if isinstance(s, dict)]
    actors = [a for a in out.get("actors", []) if isinstance(a, dict)]
    freedoms = [f for f in out.get("freedoms", []) if isinstance(f, dict)]
    ambigs = [a for a in out.get("ambiguities", []) if isinstance(a, dict)]

    src_words = words(source)
    src_nums = numerals(source)
    src_lower = source.lower()

    m: Dict[str, Any] = {}
    m["_counts"] = {"clauses": len(clauses), "requirements": len(reqs),
                    "scenarios": len(scens), "actors": len(actors),
                    "freedoms": len(freedoms), "ambiguities": len(ambigs)}

    # -- semantic fidelity: is "verbatim" actually verbatim? -----------------
    exact = sum(1 for c in clauses
                if (c.get("verbatim") or "").strip().lower() in src_lower)
    m["clause_verbatim_is_verbatim"] = frac(exact, len(clauses))

    # A requirement statement should be built from the source's own words. This
    # measures drift, not wording style: a paraphrase that imports vocabulary the
    # source never used has moved away from what the user said.
    grounded = 0
    for r in reqs:
        w = words(r.get("statement_verbatim", ""))
        if w and len(w - src_words) / float(len(w)) <= 0.34:
            grounded += 1
    m["requirement_wording_grounded_in_source"] = frac(grounded, len(reqs))

    # -- no sharpening -------------------------------------------------------
    clean = 0
    for r in reqs:
        stated = numerals(r.get("statement_verbatim", ""))
        if not (stated - src_nums):
            clean += 1
    m["requirements_free_of_invented_numerals"] = frac(clean, len(reqs))

    # A qualifier present in the source must survive into the requirement that
    # carries that number. Dropping it is sharpening that no numeral check sees.
    kept = tot = 0
    for r in reqs:
        stmt = (r.get("statement_verbatim") or "").lower()
        for n in numerals(stmt):
            idx = src_lower.find(n)
            if idx < 0:
                continue
            window = src_lower[max(0, idx - 60):idx + 20]
            q = [w for w in QUALIFIERS if w in window]
            if not q:
                continue
            tot += 1
            if any(w in stmt for w in q):
                kept += 1
    m["qualifiers_preserved_with_their_number"] = frac(kept, tot)

    # -- explicitness --------------------------------------------------------
    m["requirements_with_valid_quantity_class"] = frac(
        sum(1 for r in reqs if r.get("quantity_class") in QUANTITY_CLASSES), len(reqs))
    m["scenarios_with_valid_kind"] = frac(
        sum(1 for s in scens if s.get("kind") in SCENARIO_KINDS), len(scens))
    # A quantity in the source should be typed as a quantity somewhere.
    m["quantified_source_reflected_in_a_quantity_class"] = (
        None if not src_nums else
        float(any(r.get("quantity_class") in ("MAGNITUDE", "BAND", "COMPARATIVE")
                  for r in reqs)))

    # -- provenance ----------------------------------------------------------
    locators = {c.get("locator") for c in clauses} | {c.get("id") for c in clauses}
    m["requirements_whose_locator_resolves"] = frac(
        sum(1 for r in reqs if r.get("source_locator") in locators), len(reqs))
    actor_ids = {a.get("id") for a in actors}
    ref = tot2 = 0
    for s in scens:
        for a in id_list(s.get("actors")):
            tot2 += 1
            ref += a in actor_ids
    m["scenario_actor_refs_resolve"] = frac(ref, tot2)
    clause_ids = {c.get("id") for c in clauses}
    ref = tot2 = 0
    for a in ambigs:
        for c in id_list(a.get("conflicting_clauses")):
            tot2 += 1
            ref += c in clause_ids
    m["ambiguity_clause_refs_resolve"] = frac(ref, tot2)

    # -- reasoning depth -----------------------------------------------------
    m["freedoms_saying_why_they_are_free"] = frac(
        sum(1 for f in freedoms if len(words(f.get("why_free", ""))) >= 6), len(freedoms))
    m["ambiguities_saying_what_would_resolve_them"] = frac(
        sum(1 for a in ambigs if len(words(a.get("resolvable_when", ""))) >= 4), len(ambigs))
    m["actors_declaring_what_they_must_reach"] = frac(
        sum(1 for a in actors if as_list(a.get("must_reach"))), len(actors))
    m["scenarios_declaring_a_system_boundary"] = frac(
        sum(1 for s in scens if len(words(s.get("system_boundary", ""))) >= 5), len(scens))

    # -- preservation of openness -------------------------------------------
    # Openness is expected to EXIST: a request that determines everything is not
    # a design request. Absence of any freedom is a maturity failure.
    m["produced_any_freedom"] = float(bool(freedoms))
    m["produced_any_ambiguity"] = float(bool(ambigs))

    # -- no mechanism leak ---------------------------------------------------
    leaked = set()
    blob = json.dumps(out).lower()
    for tok in DISTINCTIVE_MECHANISM_TOKENS:
        if tok in src_lower:
            continue
        if re.search(r"\b%s\b" % re.escape(tok), blob):
            leaked.add(tok)
    m["mechanism_tokens_leaked"] = sorted(leaked)
    m["free_of_mechanism_leak"] = float(not leaked)

    # -- coverage of the source ---------------------------------------------
    # Every sentence of the request should be represented by some clause.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", source) if len(s.strip()) > 15]
    covered = 0
    for s in sentences:
        sw = words(s)
        if not sw:
            continue
        if any(len(sw & words(c.get("verbatim", ""))) / float(len(sw)) >= 0.5
               for c in clauses):
            covered += 1
    m["source_sentences_represented_by_a_clause"] = frac(covered, len(sentences))
    return m


# ===========================================================================
# S02
# ===========================================================================
def profile_s02(out: Dict[str, Any], s01: Dict[str, Any]) -> Dict[str, Any]:
    obs = [o for o in out.get("obligations", []) if isinstance(o, dict)]
    lcs = [l for l in out.get("load_cases", []) if isinstance(l, dict)]
    cands = [c for c in out.get("candidates", []) if isinstance(c, dict)]
    accs = [a for a in out.get("acceptance_contracts", []) if isinstance(a, dict)]
    unres = [u for u in out.get("unresolved", []) if isinstance(u, dict)]

    req_ids = {r.get("id") for r in s01.get("requirements", []) if isinstance(r, dict)}
    amb_ids = {a.get("id") for a in s01.get("ambiguities", []) if isinstance(a, dict)}
    fre_ids = {f.get("id") for f in s01.get("freedoms", []) if isinstance(f, dict)}
    act_ids = {a.get("id") for a in s01.get("actors", []) if isinstance(a, dict)}
    scn_ids = {s.get("id") for s in s01.get("scenarios", []) if isinstance(s, dict)}
    ob_ids = {o.get("id") for o in obs}
    cand_ids = {c.get("id") for c in cands}

    m: Dict[str, Any] = {}
    m["_counts"] = {"obligations": len(obs), "load_cases": len(lcs),
                    "candidates": len(cands), "acceptance": len(accs),
                    "unresolved": len(unres)}

    # -- requirement coverage: the core downstream contract ------------------
    cited: Set[str] = set()
    for o in obs:
        cited |= {r for r in id_list(o.get("derived_from_requirements")) if r in req_ids}
    m["requirements_carried_into_an_obligation"] = frac(len(cited), len(req_ids))

    # -- obligation quality --------------------------------------------------
    m["obligations_with_valid_scope"] = frac(
        sum(1 for o in obs if o.get("scope") in SCOPES), len(obs))
    m["obligations_with_valid_satisfiable_at"] = frac(
        sum(1 for o in obs if o.get("satisfiable_at") in SATISFIABLE_AT), len(obs))
    m["obligations_declaring_an_evidence_route"] = frac(
        sum(1 for o in obs if nonempty(o.get("evidence_route"))), len(obs))
    m["obligations_showing_their_derivation"] = frac(
        sum(1 for o in obs if as_list(o.get("derivation_premises"))), len(obs))
    m["obligations_with_resolvable_requirement_refs"] = frac(
        sum(1 for o in obs
            if id_list(o.get("derived_from_requirements"))
            and all(r in req_ids for r in id_list(o.get("derived_from_requirements")))),
        sum(1 for o in obs if id_list(o.get("derived_from_requirements"))))
    # A set of obligations that are all UNIVERSAL cannot discriminate between
    # candidates, which is what s02 exists to set up.
    m["scope_is_discriminating_at_all"] = (
        None if not obs else
        float(any(o.get("scope") == "CANDIDATE_DISCRIMINATING" for o in obs)))
    # Work honestly handed to a later stage rather than claimed here.
    m["obligations_handed_to_a_later_stage"] = frac(
        sum(1 for o in obs if o.get("satisfiable_at") in ("s03", "s04", "s05")), len(obs))
    # Declaring that no route exists is a maturity signal, not a failure.
    m["declares_some_obligation_un_evidenceable"] = (
        None if not obs else
        float(any(o.get("route_available") is False for o in obs)))

    # -- load case quality ---------------------------------------------------
    m["load_cases_with_valid_direction_class"] = frac(
        sum(1 for l in lcs if l.get("direction_class") in DIRECTION_CLASSES), len(lcs))
    m["load_cases_with_valid_kind"] = frac(
        sum(1 for l in lcs if l.get("kind") in LOAD_KINDS), len(lcs))
    m["load_cases_whose_scenario_resolves"] = frac(
        sum(1 for l in lcs if l.get("scenario") in scn_ids), len(lcs))
    # A load case must describe ROLES, not parts: the mechanism does not exist yet.
    partish = 0
    for l in lcs:
        text = "%s %s" % (l.get("applied_to_role", ""), l.get("reacted_at_role", ""))
        if any(re.search(r"\b%s\b" % n, text.lower()) for n in PART_NOUNS):
            partish += 1
    m["load_cases_free_of_part_nouns"] = frac(len(lcs) - partish, len(lcs))
    # Every load must terminate somewhere.
    m["load_cases_declaring_a_reaction_site"] = frac(
        sum(1 for l in lcs if len(words(l.get("reacted_at_role", ""))) >= 2), len(lcs))

    # -- candidate quality ---------------------------------------------------
    # `principle` may legitimately arrive as a mapping of function class ->
    # family. Flatten to comparable names rather than assuming a bare string.
    def principle_names(c: Dict[str, Any]) -> List[str]:
        v = c.get("principle")
        if isinstance(v, dict):
            return [str(x) for x in v.values() if isinstance(x, str)]
        if isinstance(v, list):
            return [str(x) for x in v if isinstance(x, str)]
        return [str(v)] if nonempty(v) else []

    fams = {n for c in cands for n in principle_names(c)}
    m["distinct_principle_families"] = len(fams)
    # Diversity is about candidates being different FROM EACH OTHER, so the
    # measure is distinct principle SIGNATURES per candidate. Counting family
    # names instead lets one candidate carrying several families exceed 1.0,
    # which is not a fraction and not a meaning.
    signatures = {tuple(sorted(principle_names(c))) for c in cands
                  if principle_names(c)}
    m["candidates_differ_in_principle"] = frac(
        len(signatures), sum(1 for c in cands if principle_names(c)))
    m["candidates_from_the_offered_library"] = frac(
        sum(1 for c in cands
            if principle_names(c)
            and all(n.upper() in LIBRARY_NAMES for n in principle_names(c))),
        sum(1 for c in cands if principle_names(c)))
    m["candidates_declaring_what_they_create"] = frac(
        sum(1 for c in cands if as_list(c.get("obligations_created"))), len(cands))
    m["candidates_with_an_evidence_verdict"] = frac(
        sum(1 for c in cands if isinstance(c.get("evidence_route_verdict"), dict)), len(cands))
    m["candidate_obligation_refs_resolve"] = frac(
        sum(1 for c in cands
            for k in ("obligations_addressed", "obligations_created")
            for o in id_list(c.get(k)) if o in ob_ids),
        sum(1 for c in cands
            for k in ("obligations_addressed", "obligations_created")
            for _ in id_list(c.get(k))))

    # -- premature commitment ------------------------------------------------
    blob = json.dumps(out).lower()
    committed = [p for p in ('"selected', '"winner', '"score', '"rank',
                             '"chosen', '"recommended', '"best_')
                 if p in blob]
    m["premature_commitment_markers"] = committed
    m["free_of_premature_commitment"] = float(not committed)

    # -- openness ------------------------------------------------------------
    m["produced_any_unresolved_decision"] = float(bool(unres))
    m["unresolved_citing_what_keeps_them_open"] = frac(
        sum(1 for u in unres
            if [k for k in id_list(u.get("kept_open_by")) if k in (amb_ids | fre_ids)]),
        len(unres))
    m["unresolved_with_typed_alternatives"] = frac(
        sum(1 for u in unres if u.get("alternatives_kind") in ALTERNATIVES_KINDS), len(unres))
    m["unresolved_with_populated_alternatives"] = frac(
        sum(1 for u in unres if as_list(u.get("alternatives"))), len(unres))

    # -- hidden reconstruction ----------------------------------------------
    # s02 re-deriving in prose something s01 handed it as an entity. Detected by
    # heavy word overlap between an s02 free-text field and an s01 ambiguity
    # statement that the same item does NOT cite by id.
    recon = 0
    amb_text = {a.get("id"): words(a.get("statement", ""))
                for a in s01.get("ambiguities", []) if isinstance(a, dict)}
    for u in unres:
        prose = words(u.get("why_open", ""))
        citedk = set(id_list(u.get("kept_open_by")))
        if not prose:
            continue
        for aid, aw in amb_text.items():
            if aid in citedk or not aw:
                continue
            if len(prose & aw) / float(len(aw)) >= 0.7:
                recon += 1
                break
    m["unresolved_reconstructing_an_uncited_ambiguity"] = recon
    m["free_of_hidden_reconstruction"] = float(not recon)

    # -- downstream usefulness ----------------------------------------------
    referenced: Set[str] = set()
    for group in (obs, lcs, cands, accs, unres):
        for e in group:
            for v in e.values():
                for item in as_list(v):
                    if isinstance(item, str):
                        referenced.add(item)
    upstream = req_ids | amb_ids | fre_ids | act_ids | scn_ids
    m["upstream_entities_used_downstream"] = frac(
        len(upstream & referenced), len(upstream))
    m["acceptance_contracts_with_predicates"] = frac(
        sum(1 for a in accs if as_list(a.get("predicates"))), len(accs))
    m["acceptance_contracts_bound_to_a_candidate"] = frac(
        sum(1 for a in accs if a.get("candidate") in cand_ids), len(accs))
    return m


# ===========================================================================
# aggregate
# ===========================================================================
#: Metrics that carry the engineering meaning. Structural conformance metrics
#: are reported but excluded from the headline: a response that parses is a
#: precondition for quality, not evidence of it.
MATURITY_KEYS = (
    # s01
    "clause_verbatim_is_verbatim", "requirement_wording_grounded_in_source",
    "requirements_free_of_invented_numerals", "qualifiers_preserved_with_their_number",
    "requirements_whose_locator_resolves", "freedoms_saying_why_they_are_free",
    "ambiguities_saying_what_would_resolve_them", "actors_declaring_what_they_must_reach",
    "scenarios_declaring_a_system_boundary", "produced_any_freedom",
    "produced_any_ambiguity", "free_of_mechanism_leak",
    "source_sentences_represented_by_a_clause",
    # s02
    "requirements_carried_into_an_obligation", "obligations_showing_their_derivation",
    "obligations_with_resolvable_requirement_refs", "scope_is_discriminating_at_all",
    "obligations_handed_to_a_later_stage", "declares_some_obligation_un_evidenceable",
    "load_cases_free_of_part_nouns", "load_cases_declaring_a_reaction_site",
    "candidates_differ_in_principle", "candidates_declaring_what_they_create",
    "candidates_with_an_evidence_verdict", "free_of_premature_commitment",
    "produced_any_unresolved_decision", "unresolved_citing_what_keeps_them_open",
    "unresolved_with_typed_alternatives", "free_of_hidden_reconstruction",
    "upstream_entities_used_downstream", "acceptance_contracts_with_predicates",
)


def maturity_index(profile: Dict[str, Any]) -> Tuple[Optional[float], int]:
    """Unweighted mean of the applicable maturity metrics, and how many applied.

    Unweighted on purpose: a weighting would encode an opinion about which kind
    of engineering care matters most, and that opinion would be fitted to the
    outputs in front of me.
    """
    vals = [profile[k] for k in MATURITY_KEYS
            if k in profile and isinstance(profile.get(k), (int, float))]
    if not vals:
        return None, 0
    return round(sum(vals) / float(len(vals)), 3), len(vals)
