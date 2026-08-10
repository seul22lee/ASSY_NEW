# IMPL S-5 — CANONICAL MOBILITY MIGRATION AND DOF DISPOSITION

Baseline `6e8bd59`. S-4 is frozen at that commit and this document does not revise
its evidence.

---

## 1. S-4 is frozen, and `CONTRACT_INCOMPLETE` was its input, not its failure

At `6e8bd59` the synthetic chain reported `_s4_physical_problems == []` while overall
S03B was `CONTRACT_INCOMPLETE` for `'no blocking relation…'`. That is not an S-4
failure — it is the mobility debt S-4 deliberately deferred, and it is the problem
S-5 exists to remove. No S-4 semantics were reopened; `_s4_physical_problems` is
unchanged, asserted by `S5-S4-05`.

## 2. Authoritative requirement, read before editing

The freeze (§11.2) and the plan (§11, U-6) define this completely:

| act | owner |
|---|---|
| enumerate the complete domain: group × configuration × DOF | **deterministic**, and BOOKKEEPING |
| `INTENDED` because a joint's class leaves the DOF free | deterministic consequence, premise is the joint |
| `BLOCKED_BY` because a `ConstraintRelation` covers it | deterministic consequence, **and the cell references it** |
| `IRRELEVANT_BECAUSE` unloaded and unactuated in a scenario | authored, cross-checked |
| a DOF with none of the above | **`UNDISPOSITIONED`** |

Contract: `MobilityExpectation.authorship_split` gives domain `DERIVED`/deterministic
with totality *"BOOKKEEPING … may never be counted as engineering assurance"*, and
disposition `AUTHORITATIVE` with `premise_required: true`, `premise_target:
ConstraintRelation`. `disposition_values` already contained `UNDISPOSITIONED` —
*"vocabulary at S-2; the behaviour is S-5."*

## 3. Pre-flight truth table

| # | issue | current production behaviour | requirement | root cause | correction |
|---|---|---|---|---|---|
| A | `blocking_relations` | model authored it; `relations_of` → `derive_mobility` consumed it | not a canonical input | S-4 left it as compatibility | **retired from the live surface** |
| B | `ConstraintRelation` | authored, and read by nothing | the premise for `BLOCKED_BY` | derivation predated it | **now the sole constraint premise** |
| C/D/E | `MobilityExpectation` | domain and disposition in one function | two facts | never split | **split** |
| F | `UNDISPOSITIONED` | in the vocabulary, produced nowhere | first-class outcome | no way to say "nothing is known" | **produced** |
| G | `MAINTAINED_BY_CLASS` | the `else` branch, from absence | valid only when justified | absence used as premise | **branch deleted** |
| H | prompt/schema/parser | asked for both channels | one truth | — | **legacy removed** |
| I | deterministic derivation | mixed the two | domain derived, disposition premised | — | **rewritten** |
| J | overall S03B | `CONTRACT_INCOMPLETE` incl. mobility | mobility reason gone | — | **gone** |
| K | active migration row | `MobilityExpectation domain and disposition split`, S-5 / U-6 | zero at closure | — | **superseded** |
| L | fixtures authoring the legacy shape | several | may retain historically | — | classified |
| M | S-4 boundary | `_s4_physical_problems` | untouched | — | untouched |

Answers: (1) `ConstraintRelation`. (2) `relations_of` parsed `blocking_relations[]`
and `derive_mobility` keyed `BLOCKED_BY` on it, citing a `BLK-` id — which
contradicts the contract rule that `BLOCKED_BY` *"must cite an addressable
ConstraintRelation by id"*. (3) Yes, both. (4) `derive_mobility`, the blocking-relation
completeness check, and a run-record counter. (5) Both, mixed. (6) The `else` branch.
(7) Yes, from absence. (8) No. (9) Yes — `retained_group`, `blocked_dofs`,
`configurations` carry everything; no spatial information needed. (10) Yes.

**GO — S-5 canonical mobility migration is coherent and bounded.**

## 4. Domain is not disposition

The enumerator makes every `group × configuration × DOF` cell exist. That totality is
guaranteed by the code that produces it, so it is bookkeeping — `dof_totality_check`
now says so in its own docstring, and `disposition_completeness()` reports the
quantity that actually means something: how much of the domain rests on evidence, and
which cells do not.

A disposition now comes only from a premise that is present and referenceable.
`BLOCKED_BY` cites the `ConstraintRelation`; `INTENDED` cites the joint;
`IRRELEVANT_BECAUSE` names the scenario.

## 5. `UNDISPOSITIONED`, and the branch that is gone

```python
else:
    entry.update({"disposition": "UNDISPOSITIONED",
                  "missing": "no ConstraintRelation covers this DOF in this "
                             "configuration, no joint leaves it free, and no "
                             "scenario declares it irrelevant"})
```

What it replaced composed a holding class from the first joint reaching the group, or
wrote the literal `"joint class of no joint"` when there was none. **That is absence
used as a premise.** The pipeline had no way to say "nothing is known here", so it
said "a joint class holds it", and a reviewer could not tell the two apart.

`MAINTAINED_BY_CLASS` is **not** retired — the contract keeps it, and it remains
valid when something justifies it. What is deleted is its use as the default when
nothing does. `S5-DISP-03` proves absence never produces it, with a joint present and
with no joint at all; `S5-DISP-03b` proves the branch was deleted rather than
reworded, scanning the code and not the docstring that explains it.

## 6. Legacy retirement

`blocking_relations` is gone from the live model-facing schema, the prompt, and every
derivation. Remaining occurrences, classified:

| where | classification |
|---|---|
| `relations_of` + one run-record counter | **S-9 corpus information** — records what a pre-migration recording contained, feeds no derivation |
| tests | proving retirement |
| recorded fixtures | historical |

`S5-CR-02` proves the point that matters: a legacy blocking relation, on its own,
now disposes **nothing** — it never had an identity, so `BLOCKED_BY` could never
have cited it.

## 7. S-4 freeze verified

`_s4_physical_problems == []` on the chain after every S-5 edit; `PEO-0001` still
discharged; `LDP-A` still closes at `RSR-0001`, which is still what `LC-0001` names.
`S5-S4-05` asserts the S-4 layer does not reason about disposition at all.

## 8. The chain

```
ConsumerView        VIEW_READY
provider called     1
patch valid         True
_s4_physical        []
_s5_mobility        []
domain cells        6   (2 by evidence, 4 UNDISPOSITIONED)
execution_status    CONTRACT_INCOMPLETE
declared_incomplete ['no assembly order']
```

**The mobility reason is gone.** The one remaining item is classified, not assumed:
`AssemblyStep` is a declared s03b output *with* a producer, and s03b's own engineering
question is *"In what order does it assemble, and what retains each part?"* — so a
response authoring none is genuinely incomplete and the stage correctly says so.
That is **probe incompleteness**: the minimal synthetic response emits
`assembly_steps: []`. Not S-5, not S-4, and not erased by changing production
behaviour to obtain a nicer status.

Second variant, with the constraint removed: the domain stays at 6 cells, the
uncovered ones are `UNDISPOSITIONED`, nothing is repaired, and completeness reports a
fraction below 1.

## 9. Two candidates

A's mobility domain contains only A's rigid group; B's topology cannot enter it, and a
relation naming a group the topology does not have adds no cell. Configuration-scoped
constraints do not leak between configurations.

## 10. Migration metadata

`legacy_producers.rows` is now `[]`, with a note saying an empty list is the claim
*"no producer is known to be nonconforming"* — different from the list having been
deleted. Six entries in `superseded_legacy_producers`, the mobility one recording its
residual: recorded fixtures still contain the pre-split shape, which is **S-9** corpus
debt.

## 11. Test-evidence matrix, for the load-bearing claims

| claim | production path | falsifier |
|---|---|---|
| domain is total and topology-derived | `derive_mobility` | a constraint naming an absent group adds no cell |
| `BLOCKED_BY` cites a resolvable relation | `derive_mobility` | citing an unauthored id is reported |
| absence → `UNDISPOSITIONED` | `derive_mobility` else-branch | with and without a joint; `"joint class"` absent from output |
| legacy channel is dead | prompt, `derived_operations` | a legacy relation disposes nothing |
| S-4 unchanged | `_s4_physical_problems` on the real chain | marker check that it never reasons about disposition |

## 12. Defer map

**S-6** frames, axes, `ReferenceScale`, metric reaction location, S04A→S04B
continuity · **S-7** retained/selected/committed/reopen · **S-8** cross-premise
mobility assurance (a DOF marked irrelevant that a load case loads is U-9's, per plan
§11.6) · **S-9** corpus refresh, live-chain validation, historical replay retirement.

## 13. CURRENT STATUS

**S-5 COMPLETE — CANONICAL MOBILITY MIGRATION AND DOF DISPOSITION CLOSED.**

Domain and disposition are separate facts; every disposition cites a premise; a cell
no premise covers says so; the class-from-absence branch is deleted; the legacy
channel is retired from every live path; disposition completeness is reported as a
quantity and totality as bookkeeping; zero active S-5 migration rows.

**Impl S-6 has NOT begun.**
