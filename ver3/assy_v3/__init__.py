"""assy_v3 — the Ver3 pipeline package.

THIS PACKAGE IS INTENTIONALLY EMPTY OF PIPELINE LOGIC.

The rebuild task that created it defines contracts and boundaries only. No Stage
is implemented, and none may be added without following the eight steps in
ver3/contracts/STAGE_PROGRESSION_CONTRACT.yaml.

What this package may never reach
---------------------------------
Everything listed in ver3/FORBIDDEN_LEGACY_DEPENDENCIES.yaml, which is data
consumed by ver3/tests/meta/test_no_legacy_imports.py rather than documentation.
The two entries most easily rationalised away are the important ones:

  ver3/oracles/         An Oracle states what must be true of a run. A stage that
                        reads one is reading its own answer key.
  ver3/cad_validation/  Positive executable CAD references. They are evaluation
                        and development fixtures, never production inputs, never
                        retrieval sources, never templates, never golden geometry.

Both are BLOCKING. Neither has an approved exception, and the approved-exception
list being empty is the expected steady state rather than a gap.

Naming
------
The runtime artifact this pipeline builds is the GENERATED_DESIGN_ASSURANCE_PACKAGE
(equivalently the RUNTIME_ASSURANCE_RECORD). It is never called an Oracle inside
this package. The word appearing here as an identifier would mean the hidden
answer key had leaked into the system being judged, so the naming rule is
enforced by test rather than left to review.

Layout once implementation begins
---------------------------------
    assy_v3/
        state/       DesignState types      <- DESIGN_STATE_CONTRACT.yaml
        patch/       StagePatch types       <- STAGE_PATCH_CONTRACT.yaml
        provenance/  provenance records     <- PROVENANCE_CONTRACT.yaml
        status/      status vocabularies    <- STATUS_SEMANTICS.yaml
        assurance/   package projection     <- GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml
        providers/   provider boundary      <- MODEL_RUN_RECORD_CONTRACT.yaml  (present)
        stages/      s01..s12               <- STAGE_OWNERSHIP_MATRIX.yaml     (absent by design)

`stages/` does not exist. Creating it is the act that starts stage implementation,
and ver3/tests/meta/test_no_stage_implementation.py fails the moment it appears
without the contracts that must precede it.
"""

__all__ = []

# Deliberately no version constant, no configuration, no imports.
# An empty boundary that imports nothing cannot violate anything, and that is the
# state this package is checked into the repository in.
