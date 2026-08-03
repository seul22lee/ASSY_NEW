# demonstrations/

This directory holds **source-only Demonstration CAD**: a model authored by a
session that has read `../source_only_packet/` and nothing else from this
repository.

**It is empty on purpose.** No demonstration was created in the CAD-1 pilot.

The pilot author had read the acceptance criteria before modelling, so nothing
they produced could serve as a demonstration however carefully it were labelled —
you cannot un-see an answer key. The directory therefore stays empty until a
session that has not read them owns it.

When such a session runs, its output belongs in `DEM-BM001-<n>/`.

Contamination check before it starts: it must have read `../source_only_packet/`
only. If it has read anything else under `ver3/`, the run is contaminated and must
say so in its report rather than being silently accepted.
