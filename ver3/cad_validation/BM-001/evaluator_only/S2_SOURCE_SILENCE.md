# DOS-BM-001 S2 — source silence  (EVALUATOR ONLY)

Withheld from `../source_only_packet/`. S2 is not rank-1 material: it is an
analysis of what the source fails to say, and telling an author where the source
is silent tells them where the acceptance criteria cannot bite.

Verbatim from `ver3/oracles/_dossiers/DOS-BM-001.md`:

## S2. Missing criteria and quantities (source silence)
- No load magnitude, direction, duration or acceleration for "normal handling", "transport".
- No effort ceiling, force or torque for "easy to operate".
- No dimension, envelope or mass anywhere.
- No material; no manufacturing process; no cost model or cost target.
- No cycle count for "reusable".
- No opening angle, stroke, or open-state pose.
- No statement of which face opens, which side connects, or handedness.
- No statement that the closure remains attached when open.
- No statement that motion is bounded at the open extreme.
- No statement of rigidity or compliance.
- No statement of the side from which the user operates the latch.

## How the evaluator should use this

Each line above is a place where a demonstration author had to choose. When
assessing a demonstration:

- A choice made here is **not** a defect, whatever it is.
- A choice made here and **not recorded** is a record defect
  (`NOT_EVALUABLE / REPRESENTATION_INCOMPLETE`), not a physical one.
- An acceptance criterion that rejects a demonstration purely because of a choice
  on this list is a candidate defect **in the criterion**, and should be recorded
  as `ORACLE_COUNTEREXAMPLE_CANDIDATE` rather than charged against the design.
