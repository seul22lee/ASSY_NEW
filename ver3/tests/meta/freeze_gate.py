"""The Stage freeze gate, as a pure function over source-manifest envelopes.

Test infrastructure, not production code. It lives in ver3/tests/meta/ and not in
ver3/assy_v3/ because it is part of how the repository is checked, not part of
the pipeline. Nothing here is Stage logic.

STAGE_PROGRESSION_CONTRACT step 8 will not let a stage contract freeze until all
three benchmarks demonstrate downstream sufficiency from source-only runs. A
source-only run is only meaningful against a settled source, so the gate also
requires every benchmark source to be reviewed and frozen.

Three envelope fields block INDEPENDENTLY:

    human_review_complete   did a human actually look?
    frozen                  are the bytes settled?
    authority_status        what IS this artifact?

They are not redundant. They fail in different ways and at different times: a
source can be reviewed but not yet frozen, or marked frozen by mistake without
ever being reviewed, or be a superseded revision that is still technically frozen.
Any one of the three catches a case the others miss, which is why the gate takes
all three rather than collapsing them into one "ready" flag — a single flag is a
single edit away from making an unreviewed source look ready.

The function returns the blockers rather than a boolean, because "the gate is
closed" is not useful to anyone; "the gate is closed because BM-003 has not been
reviewed" is.
"""

from . import _paths

#: The only authority_status the gate accepts.
REQUIRED_AUTHORITY_STATUS = "FROZEN"


def source_blockers(benchmark_id, manifest=None):
    """Reasons this benchmark's source blocks the freeze gate. Empty means clear.

    `manifest` may be supplied to evaluate a hypothetical envelope; when omitted
    the on-disk manifest is read. Tests use the override to prove each field
    blocks on its own, without editing a real source.
    """
    man = manifest if manifest is not None else _paths.source_manifest(benchmark_id)
    blockers = []

    if not man.get("human_review_complete", False):
        blockers.append({
            "benchmark_id": benchmark_id,
            "field": "human_review_complete",
            "value": man.get("human_review_complete"),
            "reason": "no human has completed review of this source",
        })

    if not man.get("frozen", False):
        blockers.append({
            "benchmark_id": benchmark_id,
            "field": "frozen",
            "value": man.get("frozen"),
            "reason": "the source bytes are not settled",
        })

    status = man.get("authority_status")
    if status != REQUIRED_AUTHORITY_STATUS:
        blockers.append({
            "benchmark_id": benchmark_id,
            "field": "authority_status",
            "value": status,
            "reason": "authority_status is %r, not %r" % (status, REQUIRED_AUTHORITY_STATUS),
        })

    return blockers


def all_source_blockers(benchmark_ids=None, manifests=None):
    """Blockers across every benchmark. Empty means every source is settled."""
    ids = benchmark_ids if benchmark_ids is not None else _paths.BENCHMARK_IDS
    out = []
    for bm in ids:
        man = (manifests or {}).get(bm)
        out.extend(source_blockers(bm, manifest=man))
    return out


def stage_freeze_permitted(benchmark_ids=None, manifests=None):
    """True only when NO source blocks.

    Deliberately the last thing defined here, and deliberately derived from the
    blocker list rather than computed separately: a boolean that can disagree
    with the reasons behind it is worse than no boolean.
    """
    return not all_source_blockers(benchmark_ids, manifests)


def settled_envelope(**overrides):
    """A fully settled envelope, for tests that need to vary one field.

    Starting from a settled envelope and breaking ONE field is what makes the
    independence claim testable: if the gate still closes, that field alone
    closed it.
    """
    env = {
        "human_review_complete": True,
        "frozen": True,
        "authority_status": REQUIRED_AUTHORITY_STATUS,
    }
    env.update(overrides)
    return env
