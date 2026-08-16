"""One integrity mechanism for every replayed response.

WHAT S9-A FOUND

Two replay providers with different guarantees, split by corpus rather than by
principle. `AgentAuthoredProvider` refused a recording whose declared prompt hash
did not match the prompt the stage had just built - real integrity, applied to the
probes. `OfflineReplayProvider` returned whatever was on disk, and it is what all
three runners used, so the benchmark fixtures were bound to nothing at all.

The mechanism was never the problem. Its reach was.

WHAT A PAIRING PROVES, AND WHAT IT DOES NOT

`answers_prompt_sha256` binds a recorded response to the PROMPT it answers. Since
the prompt is derived from the source text and the committed upstream state, a
response that pairs is a response to the question this run is actually asking.

It does not prove the response was ever produced by a model, nor that it is
correct. Provenance of ORIGIN is S9-E's job (S9-I2) and is deliberately not
conflated with this: a fixture can be perfectly paired and still be hand-written,
which is exactly the state of the current corpus.

WHY THIS DOES NOT SIMPLY REJECT THE CURRENT CORPUS

The rule is stated here in full, and the current agent-authored fixtures largely do
not meet it. Enforcement is the caller's policy, so the legacy corpus can keep
running as legacy while every replay records what it is. Weakening the rule to keep
those fixtures passing would delete the only signal S9-E needs.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

#: Response-source labels. Defined here rather than in the pipeline package so a
#: provider can declare its source without importing the orchestration it serves.
LIVE = "LIVE"
REPLAY = "REPLAY"

#: The recording declares a prompt hash and it matches what the stage just built.
PAIRED = "PAIRED"
#: It declares one and it does not match. The response answers a question that is
#: no longer being asked.
STALE = "STALE"
#: It declares none. Not a mismatch - an absence, and a weaker position than
#: either, because nothing about the recording can be checked at all.
UNDECLARED = "UNDECLARED"
#: The file is not a JSON object, so it carries no metadata to check.
UNREADABLE = "UNREADABLE"

#: The metadata key holding the pairing. Truncated to 16 hex characters by
#: history rather than by design; kept as-is so existing recordings remain
#: readable, and long enough that an accidental collision is not the concern.
PAIRING_KEY = "answers_prompt_sha256"

#: A MIGRATION BRIDGE, and recorded as one. `pairing_history` is free text left by
#: the re-stamping tool when a prompt's FORMAT changed but its question did not.
#: It is readable here so migration can interpret old artifacts; nothing in the
#: target path may consult it, and `pairing_status` deliberately does not.
MIGRATION_BRIDGE_KEY = "pairing_history"


def prompt_hash(text: str) -> str:
    """The pairing hash of a prompt. One definition, previously two."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def declared_pairing(raw_text: str) -> Optional[str]:
    """The hash a recording claims to answer, if it claims one."""
    try:
        parsed = json.loads(raw_text)
    except Exception:                                              # noqa: BLE001
        return None
    if not isinstance(parsed, dict):
        return None
    return (parsed.get("_meta") or {}).get(PAIRING_KEY)


def pairing_status(raw_text: str, prompt_text: str) -> str:
    """Is this recording bound to the prompt this run is asking?

    Deliberately does NOT consult `pairing_history`: a note explaining why a
    recording was re-stamped is migration evidence, and letting it influence the
    answer would turn the bridge into the authority.
    """
    try:
        parsed = json.loads(raw_text)
        if not isinstance(parsed, dict):
            return UNREADABLE
    except Exception:                                              # noqa: BLE001
        return UNREADABLE
    declared = (parsed.get("_meta") or {}).get(PAIRING_KEY)
    if not declared:
        return UNDECLARED
    return PAIRED if declared == prompt_hash(prompt_text) else STALE


def integrity_report(raw_text: str, prompt_text: str) -> Dict[str, Any]:
    """The whole integrity picture for one replayed response.

    `migration_bridge_present` is reported so the bridge stays visible and
    countable while S-9 retires it - not so anything may act on it.
    """
    try:
        parsed = json.loads(raw_text)
        meta = (parsed.get("_meta") or {}) if isinstance(parsed, dict) else {}
    except Exception:                                              # noqa: BLE001
        meta = {}
    return {
        "status": pairing_status(raw_text, prompt_text),
        "declared": meta.get(PAIRING_KEY),
        "actual": prompt_hash(prompt_text),
        "migration_bridge_present": MIGRATION_BRIDGE_KEY in meta,
        # Present on the probes and absent on the benchmark fixtures, which is
        # itself the asymmetry S9-E has to remove.
        "authored_by": meta.get("authored_by"),
    }


def meets_current_fixture_rule(raw_text: str, prompt_text: str) -> bool:
    """THE TARGET RULE for a regenerated fixture: paired, and nothing weaker.

    UNDECLARED fails. A fixture that says nothing about what it answers cannot be
    replayed as though it answered this - and most of the current corpus fails
    here, which is the debt S9-E clears rather than a rule to be softened.
    """
    return pairing_status(raw_text, prompt_text) == PAIRED


# ==========================================================================
# S9-D: the identities a CURRENT fixture must carry
#
# The pairing hash above binds a response to the PROMPT it answered, which is
# necessary and nowhere near sufficient. A prompt is derived from the source and
# from committed upstream state, so a pairing proves the question matched - not
# which source the question was about, not which of two passes of one stage
# asked it, and not that any model ever produced the answer.
#
# These four identities are what a promoted fixture must carry, and each exists
# because a specific substitution went undetected without it.
# ==========================================================================

#: sha256 of the source request bytes. ONE rule for every corpus: the benchmark
#: manifests already publish `request_sha256` over the same bytes, and the probes
#: have no manifest, so computing it is what lets both be checked identically
#: without inventing a probe-specific scheme or fabricating a probe manifest.
SOURCE_KEY = "source_sha256"
#: WHICH PRODUCING PASS. s03a and s03b share an owner; without this a fixture for
#: one is indistinguishable from a fixture for the other.
RESPONSIBILITY_KEY = "responsibility_id"
#: sha256 of the RAW accepted model response, before any packaging.
RESPONSE_KEY = "raw_response_sha256"
#: Which run and attempt promoted it - the S9-B model-run identity, reused rather
#: than re-invented.
PROMOTION_KEY = "model_run_id"
#: sha256 of the response content in CANONICAL form, with `_meta` removed.
#:
#: `raw_response_sha256` above hashes the original raw text, which cannot be
#: reproduced from a stored fixture - JSON re-serialization is not byte-stable -
#: so it can only ever be compared ledger-to-fixture. Both sides then agree while
#: the artifact's actual content has been edited, which is precisely what a
#: post-promotion hand-enrichment does. This hash is RECOMPUTABLE from the
#: fixture, so the content it describes is the content actually present.
CONTENT_KEY = "canonical_content_sha256"

#: Every identity a current fixture must carry. Absence of any one is a failure,
#: not a warning: a fixture that cannot say which source it answers is not usable
#: as evidence about that source.
REQUIRED_FIXTURE_IDENTITIES = (SOURCE_KEY, RESPONSIBILITY_KEY, RESPONSE_KEY,
                               PROMOTION_KEY, CONTENT_KEY)


def canonical_content_hash(body: Any) -> str:
    """The hash of a response's CONTENT, independent of how it was formatted.

    `_meta` is removed first, because provenance is packaging: adding it must not
    change the identity of the answer it describes. Sorted keys and fixed
    separators make the serialization canonical, so the same content hashes the
    same however it was written to disk.
    """
    if isinstance(body, str):
        body = json.loads(body)
    content = {k: v for k, v in body.items() if k != "_meta"} \
        if isinstance(body, dict) else body
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def producing_identity(request) -> str:
    """WHICH PASS a request is for - the identity replay and fixtures key on.

    Lives here rather than on `GenerationRequest` because that module is
    definitions only; a property with a body there would be an implementation
    inside the interface it defines.

    Falls back to the owner when no responsibility is stated, which is correct
    for s01 and s02 - their owner and their responsibility are the same string -
    and keeps every caller predating the field working unchanged.
    """
    return getattr(request, "responsibility_id", None) or request.stage_id


def canonical_source_identity(request_bytes: bytes) -> str:
    """THE source/request identity. One function, every corpus.

    Benchmarks additionally publish this in `source_manifest.request_sha256`;
    probes publish nothing. Both are checked with this, so the asymmetry in what
    a corpus DECLARES never becomes an asymmetry in what is CHECKED.
    """
    return hashlib.sha256(request_bytes).hexdigest()


def canonical_source_identity_of_file(path: str) -> str:
    with open(path, "rb") as fh:
        return canonical_source_identity(fh.read())


def fixture_identities(raw_text: str) -> Dict[str, Any]:
    """The identities a fixture declares, with None for each it does not."""
    try:
        parsed = json.loads(raw_text)
        meta = (parsed.get("_meta") or {}) if isinstance(parsed, dict) else {}
    except Exception:                                              # noqa: BLE001
        meta = {}
    return {key: meta.get(key) for key in REQUIRED_FIXTURE_IDENTITIES}


def verify_current_fixture(raw_text: str, *, prompt_text: str, source_sha256: str,
                           responsibility_id: str) -> List[str]:
    """Everything wrong with replaying this artifact here, as reasons.

    Reasons rather than a bool, because "which binding failed" is the whole
    diagnostic value - a source mismatch and a responsibility mismatch are
    different defects with different remedies, and collapsing them to False
    would make a substituted pass look like a stale prompt.

    DELIBERATELY DOES NOT CONSULT `pairing_history`. A migration note may explain
    an old artifact; it may not make a current one valid.
    """
    problems: List[str] = []
    declared = fixture_identities(raw_text)

    for key in REQUIRED_FIXTURE_IDENTITIES:
        if not declared.get(key):
            problems.append("fixture declares no %s" % key)

    if declared.get(SOURCE_KEY) and declared[SOURCE_KEY] != source_sha256:
        problems.append("fixture answers source %s but this run is source %s"
                        % (declared[SOURCE_KEY][:16], source_sha256[:16]))

    if declared.get(RESPONSIBILITY_KEY) and \
            declared[RESPONSIBILITY_KEY] != responsibility_id:
        problems.append("fixture is %s's response, requested as %s"
                        % (declared[RESPONSIBILITY_KEY], responsibility_id))

    # THE CONTENT MUST BE THE CONTENT IT CLAIMS. Recomputed from the artifact
    # rather than compared between two stored copies of the same claim, so an
    # edit made after promotion cannot leave every declared identity agreeing.
    if declared.get(CONTENT_KEY):
        try:
            actual_content = canonical_content_hash(raw_text)
        except Exception as exc:                                   # noqa: BLE001
            problems.append("fixture content is not readable: %s" % exc)
        else:
            if actual_content != declared[CONTENT_KEY]:
                problems.append(
                    "fixture content hashes %s but declares %s; it was altered "
                    "after promotion" % (actual_content[:16],
                                         declared[CONTENT_KEY][:16]))

    status = pairing_status(raw_text, prompt_text)
    if status != PAIRED:
        problems.append("prompt pairing is %s" % status)
    return problems


def promotion_fidelity_problems(fixture_body: str, accepted_raw: str) -> List[str]:
    """Does the promoted artifact still say exactly what the model said?

    Packaging may add `_meta` AROUND a response. It may not touch the answer.
    Compared as parsed content with `_meta` removed, because re-serializing JSON
    is not byte-stable and a byte comparison would fail on formatting while
    passing nothing useful. Semantic equality catches what matters: a field added,
    removed or changed between what was accepted and what was stored.
    """
    problems: List[str] = []
    try:
        promoted = json.loads(fixture_body)
    except Exception as exc:                                       # noqa: BLE001
        return ["promoted fixture is not readable JSON: %s" % exc]
    try:
        accepted = json.loads(accepted_raw)
    except Exception as exc:                                       # noqa: BLE001
        return ["accepted response is not readable JSON: %s" % exc]

    meta = promoted.pop("_meta", None) if isinstance(promoted, dict) else None
    if meta is None:
        problems.append("promoted fixture carries no _meta provenance")

    if isinstance(accepted, dict):
        accepted.pop("_meta", None)

    if promoted != accepted:
        added = sorted(set(promoted) - set(accepted)) if isinstance(promoted, dict) else []
        lost = sorted(set(accepted) - set(promoted)) if isinstance(accepted, dict) else []
        detail = []
        if added:
            detail.append("added %s" % added)
        if lost:
            detail.append("lost %s" % lost)
        if not detail:
            detail.append("a retained field's value changed")
        problems.append("promoted fixture differs from the accepted response: %s"
                        % "; ".join(detail))
    # A declared response hash must be the hash of the response actually accepted.
    declared = fixture_identities(fixture_body).get(RESPONSE_KEY)
    actual = hashlib.sha256(accepted_raw.encode("utf-8")).hexdigest()
    if declared and declared != actual:
        problems.append("declared %s does not hash the accepted response"
                        % RESPONSE_KEY)
    return problems


# ==========================================================================
# S9-D CLOSURE HARDENING: a rule that governs the path it was written for
#
# `verify_current_fixture` above existed from the first S9-D commit and was
# called by promotion, by the dry run and by audits - and by no replay. Ordinary
# replay read the artifact, recorded a pairing status beside it and returned
# SUCCESS whatever that status said. A rule enforced only where it is convenient
# is a rule the target path does not have.
#
# Two trust classes, because the corpus is mid-migration and pretending
# otherwise would force exactly the metadata forgery S9-E exists to avoid.
# ==========================================================================

#: Bounded regression on artifacts that predate S9-E. Consumable, and never
#: current: it cannot support a current-fixture claim, a generalization claim or
#: any part of full-live qualification.
LEGACY_REPLAY = "LEGACY"
#: The target class. Every current identity is checked BEFORE a response is
#: returned, and a failure is a failure rather than a warning.
CURRENT_REPLAY = "CURRENT"

REPLAY_TRUST_CLASSES = (LEGACY_REPLAY, CURRENT_REPLAY)

#: What a replay says about itself afterwards. NOT_ESTABLISHED is the honest
#: state of every artifact in the corpus until S9-E replaces it - not a defect,
#: and not something a stamp can change.
INTEGRITY_ESTABLISHED = "ESTABLISHED"
INTEGRITY_NOT_ESTABLISHED = "NOT_ESTABLISHED"


def anchor_problems(raw_text: str, ledger: Optional[Dict[str, Any]]) -> List[str]:
    """Does this fixture's promotion identity resolve to retained evidence?

    A `model_run_id` that is merely NON-EMPTY proves nothing: a fixture can carry
    an invented one and look complete. What makes it evidence is that it resolves
    to a retained promotion record whose responsibility, source and accepted
    raw-response hash are the same facts the fixture states.

    The ledger is the trusted side. Without one, a current claim cannot be made
    at all - which is why this returns a problem rather than passing by default.
    """
    identities = fixture_identities(raw_text)
    model_run_id = identities.get(PROMOTION_KEY)
    if ledger is None:
        return ["no promotion ledger, so %s resolves to nothing" % PROMOTION_KEY]
    if not model_run_id:
        return ["fixture declares no %s to resolve" % PROMOTION_KEY]

    entry = (ledger.get("entries") or {}).get(model_run_id)
    if entry is None:
        return ["%s %r is in no retained promotion record"
                % (PROMOTION_KEY, model_run_id)]

    problems: List[str] = []
    for key in (RESPONSIBILITY_KEY, SOURCE_KEY, RESPONSE_KEY, CONTENT_KEY):
        if identities.get(key) != entry.get(key):
            problems.append(
                "fixture %s=%r disagrees with the promotion record's %r"
                % (key, identities.get(key), entry.get(key)))
    return problems


def current_replay_problems(raw_text: str, *, prompt_text: str,
                            source_sha256: Optional[str],
                            responsibility_id: str,
                            ledger: Optional[Dict[str, Any]] = None) -> List[str]:
    """Everything that stops this artifact being replayed as a CURRENT fixture.

    The full rule in one call, so the replay boundary cannot enforce a subset of
    it by accident. Source identity is required: replaying "for whatever request
    this is" is how a fixture for one benchmark answers another.
    """
    if not source_sha256:
        return ["no canonical source identity was supplied, so the fixture "
                "cannot be checked against the request being replayed"]
    problems = verify_current_fixture(raw_text, prompt_text=prompt_text,
                                      source_sha256=source_sha256,
                                      responsibility_id=responsibility_id)
    problems.extend(anchor_problems(raw_text, ledger))
    return problems
