# source/

`request.txt` goes here: the raw source request, verbatim, and nothing else.

It is the only raw text a run consumes, and only Stage 01 consumes it (INV-002,
rebuild policy rule 5). Every later stage reads DesignState.

**Not yet present.** The frozen rank-1 source for this benchmark currently lives
inside `ver3/oracles/_dossiers/`, a BLOCKING forbidden path root. It must be
extracted here before the first source-only run.

The extraction is a scoped task with a human check, not a copy. A dossier
contains rank-1 user source *and* Oracle-authored semantic material in a single
document; separating them carelessly would move answer-key content into the one
tree production code may read.
