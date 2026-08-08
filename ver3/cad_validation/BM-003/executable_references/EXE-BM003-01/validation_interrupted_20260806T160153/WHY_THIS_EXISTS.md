# Interrupted validation output, preserved for diagnosis

This directory is a copy of `validation/` taken after two validation runs were
INTERRUPTED, not after they failed.

- A full-sampling run on 2026-08-06 reached step 7 and wrote
  `motion_report.json` (15:47), `interaction_report.json` (15:48) and
  `assembly_report.json` (15:49) before it was interrupted during finalisation.
  It never wrote a new `SUMMARY.json`.
- A second, detached relaunch was stopped deliberately before completion.

Nothing in here is evidence of a defect in the reference. It is kept separate so
that a clean run's artifacts cannot be mixed with a partial run's, which is
exactly the failure mode `manifest_util` was written after.

The authoritative results are in `../validation/`, produced by a single
foreground run whose exit code was observed, and are cross-checked for run
identity before `manifest.yaml` is written.
