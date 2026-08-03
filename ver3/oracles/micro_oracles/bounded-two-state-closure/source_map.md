# bounded-two-state-closure — source map (micro-oracle)

> **Pack status: `PRE_CAD_SEMANTIC_REVIEWED`** — semantic review clean; not lock-ready, not
> CAD-validated. Every admissible fixture is `NEEDS_GEOMETRY_VALIDATION`.


**Capability (rank 1 for this pack):** a closure that reaches two defined states
by a bounded motion, where the bound at each extreme is physically produced.
Source: `ver3/oracles/_dossiers/DOS-bounded-two-state-closure.md` S1.

A micro-oracle has no user request. Its rank-1 source is the declared capability
statement; product cases and legacy fixtures rank below it and never define it.

## The name

"bounded-two-state-closure" is the capability's identifier, not its content. Nothing in the
statements requires a hinge or a stop feature. `normative.naming_note`,
`FRE-HS-002` and `FRE-HS-004` say so, and `ADM-HS-C` (a sliding cover) and
`ADM-HS-D` (bounded by slot run-out, with no added feature) are admitted to prove
it.

## Statements

| Statement | basis_type | Grounded in |
|---|---|---|
| NRM-HS-001 | DIRECT_USER_REQUIREMENT | S1, "reaches two defined states" |
| NRM-HS-002 | DIRECT_USER_REQUIREMENT | S1, "by a bounded motion" |
| NRM-HS-003 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (a bounded motion has a limiting constraint) |
| NRM-HS-004 | DIRECT_USER_REQUIREMENT | S1, "where the bound at each extreme is physically produced" |
| NRM-HS-005 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived (two configurations, two conditions) |
| NRM-HS-006 | NECESSARY_PHYSICAL_CONSEQUENCE | S1 → derived |
| NRM-HS-007 | VERIFICATION_MINIMUM | S5 + S3 (the matched pair does not discriminate) |

## Boundaries with neighbouring capabilities

| Question | Owner | Why not here |
|---|---|---|
| What holds the closure at a state? | latch-retention | A bound says where motion ends, not that the closure stays. UNR-HS-002, NEG-HS-011. |
| What guides the motion along its path? | guided-slider | NRM-HS-003 requires the constraint to persist; it does not specify guidance. |
| What drives the motion? | rotary-to-linear-engagement, among others | Not owned here. |

## Legacy material and its rank

| Item | Rank | Disposition |
|---|---|---|
| Pin hinge with ring-meshed knuckles (S6) | 4 | FRE-HS-002, FRE-HS-003. |
| Discrete stop flange (S6) | 4 | FRE-HS-004, FRE-HS-007, NEG-HS-009. |
| 90 degree target and the `theta >= 90` threshold (S4, S6) | 4 | The m0 fixture's own. UNR-HS-001, NEG-HS-010. |
| Bore 2.150 / pin 2.000, min wall 2.192, 16 wedges, friction_mu 0.3, solref [0.001, 1.0] (S3, S6) | 4 | Realization and solver values. FRE-HS-006. |
| Matched-pair criteria and verdicts (S3) | 4 | EV-HS-001/002/003, with the discrimination finding stated. |
| Motion bounded only by a discrete stop across the corpus (S7) | 6 | A library state. FRE-HS-004. |

## The finding this pack is organised around

The m0 matched pair is the best evidence the legacy corpus produced: genuine V-B
contact, one feature varied, a control included. And every seed-0 criterion
passes in **both** members — including the angle criterion, where the unbounded
control reaches 219.65 degrees and still clears the 90 degree threshold. The
verdicts differ only at 5/5 against 1/5 seeds.

So the pair supports "removing the limit produced seed-level instability across a
five-seed sweep", and supports no single-run criterion for the presence of a
bound. `NRM-HS-007` requires any such criterion to be shown discriminating;
`UNR-HS-004` records that the corpus has not supplied one; `NEG-HS-008` and
`NEG-HS-014` enforce both. Nothing here weakens the evidence — it states what the
evidence shows and declines to claim the rest.

---

## Corrections at the independent semantic review

The findings below were raised by human review of the first clean audit and are
recorded finding-by-finding in `../../INDEPENDENT_SEMANTIC_REVIEW_REPORT.md`.
Statement text, basis types and unresolved scopes in this map reflect the
corrected pack, not the reviewed one.

| Finding | What changed |
|---|---|
| SF-1.3 | `PROJECT_DEFINED_CAPABILITY` replaces `DIRECT_USER_REQUIREMENT`. |
| SF-10.1 | `NRM-HS-003` requires CONTINUOUS CONSTRAINT COVERAGE, not one persistent constraint. The constraint mode may change and the path may use several features in succession. `ADM-HS-E` — a flexure handing off to a moulded rib — falsifies the retired reading. |
| SF-10.2 | `NRM-HS-005` requires each extreme to be independently EVALUATED at its own configuration, not to have a distinct determining feature. One continuous slot (`ADM-HS-D`) or one magnetic field (`ADM-HS-F`) may produce both bounds. What is forbidden is copying one evaluation result to both. |
| SF-10.3 | Bounding remains separate from holding. `UNR-HS-002` keeps the holding question out; holding is owned by `latch-retention`. |
| SF-10.4 | Criterion discrimination moved to `evidence_cases.yaml`. Whether a test distinguishes a bounded from an unbounded control is a property of the test, not of the closure. |
| SF-11.1 | The pack declares `source_declares_terminal_states` with a verbatim fragment the auditor verifies against the frozen dossier. Bounds are definitional HERE; the terminal-bound check still fires for BM-002 and C4-drawer, whose sources declare no travel limit. |

The mechanism-neutral name is kept and `historical_aliases: [hinge-and-stop]`
records the former identifier without making it authoritative.

## Capability authority after amendment AMD-HS-001

`AMD-HS-001`, approved by **HSD-003**, supersedes the frozen S1 for the
constraint-persistence and bound-distinctness clauses only. The
"bound at each extreme is physically produced" clause is **unchanged** and remains
the grounding for `source_declares_terminal_states`.

HSD-003 also records a scope limit that no earlier file stated: **not every
product closure instantiates this micro-oracle.** A detachable or freely-positioned
product closure may satisfy its product source without belonging to this
capability at all. Two endpoint bounds with an unconstrained free-flight region
between them do not instantiate it.
