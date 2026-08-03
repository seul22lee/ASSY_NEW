# Micro-oracle — rotary-to-linear-engagement

**Status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; **not** lock-ready,
**not** CAD-validated, **not** production authority. Every admissible fixture is
`NEEDS_GEOMETRY_VALIDATION`. Next authorized phase: adversarial CAD validation.

**Tier:** micro_oracle.
**Frozen dossier:** `../../_dossiers/DOS-rotary-to-linear-engagement.md`.

## Capability

> Conversion of rotary input motion into linear output motion through an
> uninterrupted chain of realized localized interactions, with the reaction of
> the loads those interactions produce.

The name is deliberate. This pack replaces a mechanism-named predecessor, and it
names what is achieved rather than how. Rack-and-pinion appears here only as a
cited reference realization and an evidence source — one member of the family,
never the family.

## The failure this pack is built around

The legacy pipeline held exactly one conversion realizer. Asked for a
hand-cranked lift without it, the pipeline answered **INFEASIBLE** — while a
second conversion, a lead screw, existed in the same repository, and a third
topology existed beside it.

A hand-cranked lift without that one mechanism is entirely realizable. The
verdict was a library gap reported as physics. That single confusion —
**UNSUPPORTED mistaken for INFEASIBLE** — is what this micro-oracle exists to
make impossible:

- `FRE-RL-001` declares the conversion family free, and lists eight realizations.
- `NEG-RL-008` makes the INFEASIBLE verdict a defect with a required outcome.
- `stage_expectations.s02.open_search_note` requires that the solution space was not
  closed by library availability, that each rejection names a reason, and that
  reduction-to-one-because-only-one-is-implemented is reported as a capability gap.
  It does NOT require a fixed number of candidates to survive (SF-8.3).
- `stage_expectations.s12.capability_gap_rule` requires the revision record to name
  the missing realizer rather than the missing physics.

`ADM-RL-C` (a band on a drum) and `ADM-RL-D` (a crank pin in a slot, whose
input/output relation is not even linear) are admitted as fixtures. If any
invariant rejected them, the pack would have quietly encoded the one card.

## The second finding, corpus-wide

DOS S5 records verbatim that the conversion card "passes V-A 5/5" and that "V-B
is NAMED-DEFERRED, not silently dropped".

**No contact-level evidence exists for any rotary-to-linear conversion anywhere
in the legacy corpus.** Under declared pairs the ratio is exact by construction,
so agreement between commanded input and observed output reports the declaration
rather than the artifact. `NRM-RL-007` is the invariant form of this; the
`corpus_level_finding` in `evidence_scope.yaml` states its reach. Engagement,
backlash, friction, efficiency and jamming are NOT_VERIFIED for every
realization — which is not INFEASIBLE either.

## Files

| File | Role |
|---|---|
| `normative.yaml` | 7 invariants + 3 required unresolved decisions + scope exclusions + naming note |
| `freedoms.yaml` | 8 decisions no test may assert |
| `realizations.yaml` | 4 admissible + 7 inadmissible fixtures |
| `negative_cases.yaml` | 7 design + 6 process cases |
| `evidence_scope.yaml` | Corpus-level fidelity finding; 4 not-verified criteria |
| `stage_expectations.yaml` | Representation obligations; conditional s11 outcome rules |
| `source_map.md` | Every statement traced; every legacy value ranked |

## Boundary with guidance

`NRM-RL-004` requires only the restraint without which the output would rotate
instead of translating. It does **not** supply general guidance, and a guidance
realization may not be credited to it unless it demonstrably removes rotation
about the input axis. Guidance is owned by `guided-slider`. `NEG-RL-012` and the
`double_discharge_rule` in `stage_expectations.s05` keep one realization from
discharging two obligations.

## Corrected at the independent semantic review

The capability statement above is the SF-8.1 rewrite. The reviewed version said
"through a localized engagement", which was read as requiring direct engagement
between the rotating input body and the translating output body — and therefore
rejected every multi-stage conversion, including the crank-link-slider, which is
the most common rotary-to-linear mechanism in engineering. `ADM-RL-E` and
`ADM-RL-F` are in the fixture set precisely to keep that reading out.

Two further corrections: the requirement that the input/output relation be
*declared* was a DesignState obligation and moved to `stage_expectations`
(SF-8.2), and the fixed-plurality rule was withdrawn (SF-8.3).

Basis types are `PROJECT_DEFINED_CAPABILITY`, not `DIRECT_USER_REQUIREMENT`: a
micro-oracle has no user, and this capability statement was written by the
project and then frozen (SF-1.3).

## Capability authority after amendment AMD-RL-001

Normative authority for the **capability statement** rests with `AMD-RL-001`,
approved by **HSD-002**. The frozen S1 text is preserved verbatim in the amendment
record; S2–S7 retain full authority.

Stage expectations were carrying the retired wording after the normative file had
been corrected. Fixed in this pass:

| Retired stage wording | Now |
|---|---|
| `engagement_site` (singular) at s04 | `interaction_sites` (a list), with a chain note |
| `radial_support_realization` required at s05 | `reaction_realizations_for_carried_loads` |
| `output_rotation_restraint` unconditional at s05 | required only where the chain applies the moment |
| `RL-C2_relation_declared` — a physical FAIL for a missing declaration | `RL-C2_rotation_causes_translation` — physical causation; the declaration is a representation obligation at s04 |
| `RL-C5` requiring radial support on the rotating body | reaction for load components actually carried |
