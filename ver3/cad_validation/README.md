# ver3/cad_validation

Phase **CAD-1 — positive CAD realizability validation**.

This tree holds CAD work that tests the Ver3 Oracle against real geometry. It
contains no Oracle files and changes none; the Oracle is read at commit
`83fc12d46ad8c5fad36afcfe5b6e916822a41118`.

## Two kinds of CAD, kept apart

| Kind | Author knows | Purpose | Built here? |
|---|---|---|---|
| **A. Demonstration** | the rank-1 source **only** | can someone reading only the source produce something the Oracle accepts? | **no** — a fresh session owns it |
| **B. Executable reference** | the source **and** the Oracle | does an admissible design survive real geometry, motion, contact and assembly? | **yes**, two of them |

Keeping them apart is the whole point. A Demonstration authored by someone who
has seen the Oracle's admissible fixtures proves nothing about whether the source
alone is sufficient. `BM-001/source_only_packet/` is the sealed input for that
future session, and `BM-001/demonstrations/` stays empty until it runs.

## Layout

```
CAD_VALIDATION_PLAN.yaml     what this phase can and cannot establish
TOOLCHAIN_LOCK.yaml          exact versions, verified capabilities, probe evidence
schemas/                     artifact schemas
tools/                       shared build + validation library
BM-001/
  source_only_packet/        sealed rank-1 input for a future fresh session
  demonstrations/            EMPTY in this run, by design
  executable_references/     EXE-BM001-01, EXE-BM001-02
  reviews/                   selection record, pilot report
```

## What a PASS here means

Geometry and kinematics only. Every strength, fatigue, wear, friction, holding
force, tolerance-capability and durability question is `NOT_VERIFIED`, because
this toolchain has no physics solver and no test data. Motion evidence is
**sampled**, not proved.

Two admissible designs passing does not show the Oracle is right — an
over-permissive Oracle would also admit them. That is what the Demonstration
session and later adversarial CAD are for.
