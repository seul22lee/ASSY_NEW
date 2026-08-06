# source/

`request.txt` holds the raw source request. It is the only raw text a run
consumes, and only Stage 01 consumes it (INV-002, rebuild policy rule 5).

**Present, but AUTHORED rather than extracted, and UNFROZEN.**

BM-001 and BM-002 have requests copied verbatim from an original fixture, so
their faithfulness is checkable by comparing bytes against a witness. BM-003 had
no prior source, so this one was written from a fixed product intent. There is
nothing to compare it against, which is why it stays unfrozen until a human has
reviewed it.

- [`source_manifest.yaml`](source_manifest.yaml) — provenance, authoring method,
  hash, prohibited-content scan, contamination declarations
- [`../BM003_SOURCE_AUTHORING_RECORD.md`](../BM003_SOURCE_AUTHORING_RECORD.md) —
  intent-to-sentence mapping and the judgement calls
- [`../BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md`](../BM003_SOURCE_HUMAN_REVIEW_CHECKLIST.md) —
  the review to run before freezing

**Status: HUMAN_REVIEW_REQUIRED.** No Oracle exists for BM-003 and none was
authored. Until the source is reviewed and frozen, and an Oracle is authored
independently and frozen *before* the first run, BM-003 remains a placeholder and
no stage contract may freeze.
