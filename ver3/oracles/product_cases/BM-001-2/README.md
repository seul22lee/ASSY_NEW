# BM-001-2 — Latching storage box, panel-mounted, no projecting corners

## Problem intent

BM-001 plus one environmental requirement and one safety requirement: the
enclosure seats flat against a mounting panel, the exposed side presents no
projecting corners, and the latch cannot be released from the exposed side.

## Relationship to BM-001

A **documented single-requirement delta**. The spec says so in its own metadata:
*"Everything else is identical, so any difference in the result traces to that
requirement and nothing else."* This pack therefore `inherits: BM-001` and
states only what changes. Two added invariants, three added freedoms, two added
unresolved decisions, three added negative cases.

## Fixed requirements (delta)

`NRM-BM-001-2-001` — one flat mounting region, no projecting exposed edges.
`NRM-BM-001-2-002` — the actuator is unreachable from the exposed side.

## Freedoms (delta)

The exposed profile that achieves non-projection; which face mounts; how
unreachability is achieved. **`FRE-BM-001-006` is narrowed, not removed**: a
sharp-arrised prism is now excluded, but the curved form is still entirely free.

## Known ambiguities

The word *cylindrical* appears in the task brief but **not in the spec**, whose
observable is "the exposed side rounded". Recorded in `source_map.md`; the pack
requires non-projection, not a cylinder.

## Why this case is included

It is the cleanest available test of whether a *single added requirement
propagates into geometry*. Because the spec guarantees everything else is
identical, a run that produces the BM-001 box unchanged has demonstrably failed
to act on REQ-009 — and `NEG-BM-001-2-001` catches exactly that, even when the
requirement trace is complete.

## Pipeline capabilities stressed

- Requirement→geometry propagation, with a control (the parent case).
- Metric surface reasoning rather than qualitative curvature labels (`NEG-002`).
- Negative access constraints — proving a path does *not* exist (`NRM-2-002`).
- Delta inheritance without re-deriving the parent.

## What would constitute overfitting here

1. Encoding **"cylinder"** as normative. The evidence says "rounded".
2. Fixing the mounting face, the rounding radius, or the actuator side.
3. Asserting the Ver2 realization's inside-the-wall beam-and-nose catch as
   required — it is one solution to REQ-010, cited only as context.
4. Any comparison against `V2/out/BM-001-2/run-*`.

## Corrected at the independent semantic review

**SF-3.1** — `NRM-BM-001-2-001` asserted that the exposed boundary is *opposite*
the seating region. REQ-009 says "flush against a mounting panel on one side" and
"no projecting corners on the exposed side"; it never relates the two sides
geometrically. `ADM-BM-001-2-D`, an L-shaped body seated on one narrow face whose
exposed boundary wraps three adjoining faces, is in the set to keep the addition
out.

**AMB-001-2-01 is preserved.** The three readings of "worked from inside the
enclosure" remain unresolved and the exact wording is unchanged. This pack carries
the only `blocks_structural_predicate` scope in the whole set, with a
justification: the predicate's *domain* is undefined, not merely a threshold
missing. Until "inside the enclosure" is fixed there is no set of poses the
predicate ranges over, so it cannot separate compliant from non-compliant designs
at any fidelity.

That is why BM-001-2 alone remains **BLOCKED_BY_SOURCE_AMBIGUITY** and is not
lock-ready.
