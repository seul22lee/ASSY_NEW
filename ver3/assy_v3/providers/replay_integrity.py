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
from typing import Any, Dict, Optional

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
