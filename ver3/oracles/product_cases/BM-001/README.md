# BM-001 — Latching storage box

## Problem intent

A compact desktop storage box with a reusable latch that opens and closes
repeatedly, stays shut during normal handling and transport, is easy to operate,
and is cheap to make.

Source: `V2/tests/fixtures/BM-001_requirementspec.json` (8 requirements) and
`V2/BM-001_LATCHING_STORAGE_BOX.md`.

## Fixed requirements

Twelve normative invariants (`normative.yaml`). In summary: two enclosure states
with a continuous connecting motion; a *realized* connection supporting the
closure; the open state genuinely clears the aperture and the swept path clears
the enclosure; the closure is rigid; a *realized* travel limit at the open
extreme; reusable retention with localized engagement, holding and release
predicates; a user access path terminating at the actuator; payload access to
the cavity; collision-free assembly with an acyclic dependency graph; declared
load reaction paths; units on every predicate input.

## Freedoms

Ten, all explicit refusals (`freedoms.yaml`): closure mechanism family;
retention mechanism family; which face opens and which side connects; motion
type; part count and decomposition; **enclosure cross-section**; all dimensions;
material and process; whether the travel limit is a separate part or an integral
face; number of engagement sites.

## Known ambiguities

Five required-unresolved decisions (`normative.yaml → required_unresolved`).
The two that matter most: there is **no load case** for "normal handling and
transport", and **no effort ceiling** for "easy to operate". Consequently
REQ-002, REQ-003 and REQ-004 are expected to terminate at `NOT_VERIFIED`, and
REQ-005 at `UNSUPPORTED`. A run that reports PASS for any of them has
fabricated an acceptance limit.

## Why this case is included

It is the parent of the three-case BM-001 family and the smallest problem that
still exercises the whole chain: state, motion, clearance, retention, access,
assembly and reaction — without needing a transmission.

## Pipeline capabilities stressed

- Two-state kinematics with a swept-volume clearance predicate (not endpoint-only).
- Realization-versus-label discrimination (`NEG-002`, `NEG-006`).
- Distinguishing a *design* travel limit from an *analysis-model* one (`NEG-001`).
- Access paths that terminate at a feature, not at a boundary (`NEG-007`).
- Honest non-pass reporting where the request under-specifies (`NV-001..004`).
- Refusing to select between candidates of unequal completeness (`NEG-009`).

## What would constitute overfitting here

Concretely, for this case:

1. **Assuming a rectangular prismatic enclosure.** Nothing in BM-001 requires
   one; `FRE-BM-001-006` refuses it explicitly. The family variants add
   curvature, so a box assumption in the parent would poison all three packs.
2. **Assuming a pin hinge.** `FRE-BM-001-001`.
3. **Assuming a cantilever snap latch.** `FRE-BM-001-002` — the most likely
   import from Ver1, whose `snap_hook` card makes it the path of least
   resistance.
4. Asserting a hinge side, an opening face, a part count, a dimension, a
   material or a process.
5. Requiring a *separate* stop part rather than a realized terminal contact
   (`FRE-BM-001-009`).
6. Comparing any produced artifact to `V2/BM-001_GOLDEN_STAGE_OUTPUTS.md`.
