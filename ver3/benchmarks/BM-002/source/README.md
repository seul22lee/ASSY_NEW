# source/

`request.txt` holds the raw source request, verbatim. It is the only raw text a
run consumes, and only Stage 01 consumes it (INV-002, rebuild policy rule 5).
Every later stage reads DesignState.

**Present.** Provenance, extraction method, hashes, the witness comparison, the
human-review status and the contamination declarations are in
[`../source_manifest.yaml`](../source_manifest.yaml).

Extracted verbatim from the original benchmark fixture, **not** from an Oracle
dossier. The dossier's analytical sections were never read for this file, which
is what keeps answer-key material out of the one tree production code may read.
Ver2's derived interpretation of this same text — its clauses, requirements,
assumptions, unknowns and freedoms — was deliberately excluded: it is an
already-performed Stage 01, and including it would make the stage untestable.

**Status: HUMAN_REVIEW_REQUIRED.** Two witnesses to the source exist and are not
byte-identical. The copy is exact against the declared primary witness; what
needs confirming is which rendering is canonical. See the manifest's questions.
