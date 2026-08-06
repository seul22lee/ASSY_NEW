"""Source-language audits: overprescription and underdefinition.

Test infrastructure, not production code. Nothing here is Stage logic.

Two audits, with opposite failure modes:

    OVERPRESCRIPTION   the request contains its own answer, or imports a
                       property the benchmark cannot verify
    UNDERDEFINITION    the request has lost a piece of the intent it must carry

The contact-degradation category exists because the previous scan matched
``loosen*`` and missed ``work themselves loose`` — the same property, spelled as
a phrase rather than a word. A single-token scan cannot see it, which is why this
category is phrase-aware.

The hard part is that ``loose`` is not itself the problem. ``loose pieces`` is
exactly how a user describes an unattached component, and banning the word would
delete a legitimate requirement to protect against a different one. So the
patterns match the CONTEXT that turns ``loose`` into a contact-degradation claim
— something coming loose, working loose, or loosening over time — and leave the
adjective alone.

Every match must be INSPECTED. A pattern hit that nobody looked at is not
evidence, so `audit_overprescription` returns findings and the caller decides;
matches that were reviewed and accepted are recorded in ACCEPTED_MATCHES with the
reason, and `unreviewed_findings` is what a test asserts on.
"""

import re

# ---------------------------------------------------------------------------
# Overprescription categories
# ---------------------------------------------------------------------------

OVERPRESCRIPTION_CATEGORIES = [
    {
        "id": "OP-01",
        "name": "degree_of_freedom",
        "pattern": r"degrees?\s+of\s+freedom|\bdof\b",
        "why": "Analysis vocabulary. A user does not write it; a specification does.",
    },
    {
        "id": "OP-02",
        "name": "joint_named",
        "pattern": r"\b(joint|hinge|hinged|pivot|pivots|revolute|prismatic|axle|bearing|bushing|swivel)\b",
        "why": "Names a joint type, which is part of the answer.",
    },
    {
        "id": "OP-03",
        "name": "locking_realization",
        "pattern": r"\b(latch|latches|lock|locks|locking|locked|collar|toggle|detent|catch|clasp|clip|clips|pin|pins|spring|springs|magnet|magnets|screw|screws|bolt|bolts)\b",
        "why": "Names a locking realization. The widest part of this benchmark's solution space.",
    },
    {
        "id": "OP-04",
        "name": "guide_named",
        "pattern": r"\b(guide|guides|rail|rails|track|tracks|slot|slots|groove|grooves|channel|channels|slide|slider)\b",
        "why": "Names a guide feature.",
    },
    {
        "id": "OP-05",
        "name": "linkage_named",
        "pattern": r"\b(linkage|four-bar|scissor|cam|cams|rack|pinion|gear|gears|lever|levers|strut|struts|brace|braces)\b",
        "why": "Names a mechanism family.",
    },
    {
        "id": "OP-06",
        "name": "numeric_threshold",
        "pattern": r"\d",
        "why": "Any digit is a threshold the instruction did not state.",
    },
    {
        "id": "OP-07",
        "name": "body_count",
        "pattern": r"\b(one|two|three|four|five|six|seven|eight)\s+(bodies|parts|components|pieces|members|sections)\b",
        "why": "Prescribes how many bodies the product has.",
    },
    {
        "id": "OP-08",
        "name": "pipeline_vocabulary",
        "pattern": r"\b(designstate|oracle|obligation|realization|invariant|predicate|topology|rigid[- ]body|stage)\b",
        "why": "Leaks the pipeline's own structure into its input.",
    },
    {
        "id": "OP-09",
        "name": "requirement_ids",
        "pattern": r"\b(req|nrm|unr|neg|bm)-\d",
        "why": "Identifiers are assigned downstream; a source request has none.",
    },
    {
        "id": "OP-10",
        "name": "evaluation_instructions",
        "pattern": r"\b(criterion|criteria|evaluate|evaluated|verify|verified|validation|acceptance|shall)\b",
        "why": "Acceptance language belongs to an Oracle, not to a request.",
    },
    {
        "id": "OP-11",
        "name": "structural_capacity",
        "pattern": r"\b(load|loads|stress|strength|buckl\w*|payload|weight|kg|newton|newtons|force|forces)\b",
        "why": "Would require capacity evidence this benchmark's scope cannot produce.",
    },
    {
        "id": "OP-12",
        "name": "manufacturing_process",
        "pattern": r"\b(injection|mould|mold|machin\w+|tolerance|tolerances|manufactur\w+)\b",
        "why": "Process feasibility is out of scope.",
    },
    {
        "id": "OP-13",
        "name": "contact_degradation",
        # Phrase-aware, and deliberately NOT a ban on the word `loose`.
        "pattern": (
            r"\bloosen(?:s|ed|ing)?\b"
            r"|\b(?:come|comes|came|coming)\s+loose\b"
            r"|\bwork(?:s|ed|ing)?\s+(?:itself|themselves|himself|herself|its\s+way|their\s+way)\s+loose\b"
            r"|\bwork(?:s|ed|ing)?\s+loose\b"
            r"|\bbacklash\b|\bslop\b|\bwobble[sd]?\b|\brattle[sd]?\b|\brattling\b"
            r"|\bvibrat\w+\b|\bwear\b|\bfatigue\b|\blifetime\b|\bdurab\w+\b"
            r"|\bplay\s+(?:in|between)\b"
        ),
        "why": (
            "Contact degradation: clearance growth, vibration, wear, fatigue or "
            "load-history-dependent loosening. Verifying any of it needs "
            "tolerances, surface behaviour and a load history, none of which this "
            "benchmark's scope covers - so it would yield UNSUPPORTED, a correct "
            "answer that measures nothing."
        ),
        "not_banned": (
            "The adjective `loose` on its own. `loose pieces` is how a user "
            "describes an unattached component, and it is a legitimate "
            "requirement. Only the phrases that make `loose` a degradation claim "
            "are matched."
        ),
    },
]

# ---------------------------------------------------------------------------
# False-positive review register
#
# A pattern hit that nobody inspected is not evidence. Every match must either
# fail the audit or appear here with a reason. The register is deliberately
# empty: every match found so far was a real hit that was fixed in the source
# rather than excused here.
# ---------------------------------------------------------------------------

ACCEPTED_MATCHES = []

#: Matches inspected and REJECTED as false positives, then fixed at the source.
#: Kept as the record of what the audit caught and what was done about it.
REVIEWED_AND_FIXED = [
    {
        "match": "rack",
        "category": "OP-05",
        "where": "inside the word `track`, in `keep track of`",
        "verdict": "FALSE_POSITIVE",
        "action": "Scan given word boundaries. The phrase was later removed for OP-04.",
    },
    {
        "match": "track",
        "category": "OP-04",
        "where": "`loose pieces to keep track of`",
        "verdict": "REAL_MATCH_BENIGN_MEANING",
        "action": (
            "Rewritten to `look after`. An idiom, not a guide feature - but "
            "`track` is a guide synonym and a reviewer scanning for guide "
            "language would stop on it exactly as the audit did."
        ),
    },
    {
        "match": "clamp",
        "category": "OP-03",
        "where": "`anything to clamp it to`, rendering `external fixture`",
        "verdict": "REAL_MATCH_BENIGN_MEANING",
        "action": (
            "Rewritten to `any other equipment to do it`. It appeared only in the "
            "negative and referred to something outside the product, so it "
            "prescribed nothing - but it is a mechanism noun a few lines from the "
            "release requirement."
        ),
    },
    {
        "match": "rattle",
        "category": "OP-13",
        "where": "`Nothing should rattle, turn on its own, ...`",
        "verdict": "REAL_MATCH",
        "action": "Replaced with `shift out of place` at revision R2.",
    },
    {
        "match": "loosening",
        "category": "OP-13",
        "where": "`without anything loosening, coming apart, ...`",
        "verdict": "REAL_MATCH",
        "action": "Replaced with `all normal parts remaining attached` at revision R2.",
    },
    {
        "match": "work themselves loose",
        "category": "OP-13",
        "where": "`fold back, twist aside, or work themselves loose`",
        "verdict": "REAL_MATCH_MISSED_BY_TOKEN_SCAN",
        "action": (
            "Replaced with `come off` at amendment R3. The token scan matched "
            "`loosen*` and missed this phrase, which is why OP-13 is phrase-aware."
        ),
    },
]


def audit_overprescription(text):
    """Every overprescription match in `text`, with enough context to inspect it."""
    low = " ".join(text.lower().split())
    findings = []
    for cat in OVERPRESCRIPTION_CATEGORIES:
        for m in re.finditer(cat["pattern"], low):
            findings.append({
                "category": cat["id"],
                "name": cat["name"],
                "match": m.group(0),
                "start": m.start(),
                "context": low[max(0, m.start() - 40):m.end() + 40],
            })
    return findings


def unreviewed_findings(text):
    """Findings not covered by the accepted-match register.

    This is what a test asserts on. Splitting it from `audit_overprescription`
    keeps 'what the scan saw' separate from 'what was allowed', so an accepted
    match stays visible rather than disappearing from the scan entirely.
    """
    accepted = {(a["category"], a["match"]) for a in ACCEPTED_MATCHES}
    return [f for f in audit_overprescription(text)
            if (f["category"], f["match"]) not in accepted]


# ---------------------------------------------------------------------------
# Underdefinition: the intent elements the BM-003 request must carry
# ---------------------------------------------------------------------------

BM003_INTENT_ELEMENTS = [
    ("three_legs", r"three legs"),
    ("fold_close_to_body", r"fold in close to the body"),
    ("compact_stored_form", r"narrow and compact"),
    ("stays_attached_when_folded", r"everything should stay attached"),
    ("no_loose_parts_to_manage", r"loose pieces"),
    ("manual_unfolding", r"open it by hand"),
    ("comprehensible_sequence", r"sequence that makes sense"),
    ("legs_spread_apart", r"spread apart in different"),
    ("usable_footprint", r"usable footprint"),
    ("stays_connected_while_opening", r"come apart or fall off"),
    ("no_tools_motor_fixture", r"not need tools, a motor, or any other equipment"),
    ("stays_deployed_unaided", r"stay open on its own"),
    ("no_holding_required", r"not have to hold the legs"),
    ("named_unintended_motions", r"fold back, twist aside, or come off"),
    ("general_unintended_motion", r"turn on its own, shift out of place, or move in some other direction"),
    ("deliberate_release", r"something deliberate"),
    ("returns_to_stored_form", r"fold back down to the same compact shape"),
    ("repeatable_cycle", r"opening and folding sequence should be repeatable"),
    ("parts_remain_attached", r"all normal parts remaining attached"),
    ("no_removal_to_cycle", r"without anything needing to be removed and put back on"),
    ("assemblable_as_product", r"built as a product"),
    ("sensible_assembly_order", r"sensible order"),
    ("stays_together_in_use", r"stay together through normal opening and folding"),
    ("desktop_object_purpose", r"hold a small object on my desk"),
]


def audit_underdefinition(text, elements=None):
    """Intent elements NOT found in `text`. Empty means complete."""
    low = " ".join(text.lower().split())
    return [name for name, rx in (elements or BM003_INTENT_ELEMENTS)
            if not re.search(rx, low)]
