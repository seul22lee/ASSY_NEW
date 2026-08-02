# Competency questions

The questions the ontology is built to answer. Each one records what it tests,
how it is answered today, and — where v0.1 cannot yet answer it — exactly what
is missing. The "status" column is deliberately honest: a competency question
list that claims everything works is not a specification, it is marketing.

**Status key**

| Status | Meaning |
|---|---|
| ✅ answered | A query in `scripts/query_examples.py` or a SPARQL pattern below returns a correct answer from the v0.1 graph. |
| 🟡 partial | The model supports the question; the pilot data covers only part of the domain, so answers are incomplete but not wrong. |
| ⬜ modelled, no data | The schema supports it; no v0.1 instance data exercises it yet. |
| ❌ out of scope for v0.1 | Deliberately deferred; the expansion plan says when. |

---

## A. Function-driven search
*Can a designer find a solution without knowing the name of the element?*

**CQ-01 — What alternatives can perform a required function?** ✅
`mdcore:DesignAlternative → mdcore:performsFunction`. Query 1 returns 16
alternatives for `mech:TransmitTorqueShaftToHub`. This is the entry point for a
user who can state the job but not the part name.

**CQ-02 — By what behavior does each alternative deliver that function?** ✅
`mdcore:Behavior` sits between function and structure, so a key
(`mech:ShearLoadTransfer`), a press fit (`mech:FrictionalLoadTransfer`) and a
spline (`mech:DistributedToothContact`) are distinguishable even though they
share a function. This distinction is what makes their failure modes and
verification needs differ.

**CQ-03 — What alternatives satisfy a function *in a specified operating
context*?** ✅
Query 2. Under `ctx-axial-slide-under-torque` the parallel key is
`NotAnAlternative` while the involute spline is `PreferredAlternative` — the
same function, opposite answers, decided by context.

**CQ-04 — Which alternatives rely on a given physical effect?** ✅
`mdcore:Behavior → mdcore:reliesOnEffect`. Retrieves every friction-based
connection as a family, independent of geometry — useful because they share a
sensitivity to maintained interface pressure.

**CQ-05 — What functions does one alternative deliver *besides* the obvious
one?** ✅
A parallel key also performs `mech:LocateAxially` and, by design intent,
`mech:LimitTransmittedTorque`. CQ-05 is what stops CQ-16 being answered wrongly.

---

## B. Equivalence and substitution

**CQ-06 — Are two alternatives functionally equivalent?** ✅
`mdcore:sharesFunctionWith` (symmetric). Answers "both can do this job" and
nothing more. Deliberately weak.

**CQ-07 — Can alternative A replace alternative B?** ✅
Never answered from CQ-06. Requires a `mdcore:SubstitutionAssessment` naming the
preserved function, the context, the requirements and a conclusion. Query 6.

**CQ-08 — Under what conditions is substitution possible?** ✅
`mdcore:assessmentCondition` and `mdcore:requiredDesignModification`. SHACL
refuses a `ConditionallySubstitutable` verdict that names neither.

**CQ-09 — Does substitutability hold in both directions?** ✅
No, and the graph proves it. SA-001 (spline replaces key) concludes
`PreferredAlternative`; SA-006 (key replaces spline), *same pair, same context*,
concludes `NotAnAlternative`. `substitutionAssessedAs` is neither symmetric nor
transitive, and `validate_ontology.py` fails the build if either is inferred.

**CQ-10 — What modifications are required before substitution?** ✅
`mdcore:DesignModification`, each with an effort estimate and a value
provenance so a sourced modification is distinguishable from an inferred one.

**CQ-11 — What requirements make one alternative preferable to another?** ✅
`PreferredAlternative` requires `mdcore:applicableRequirement` and
`mdcore:satisfiedRequirement`. A preference is always relative to a stated
requirement set, never a global ranking.

**CQ-12 — What are the advantages, disadvantages and trade-offs?** ✅
`mdcore:AlternativeEvaluation` (advantage / disadvantage) and `mdcore:TradeOff`.
Every one carries a context and a `mdcore:valueProvenance`. Query 5.

**CQ-13 — Which claimed advantages are from the books and which are the
analyst's?** ✅
`mdcore:valueProvenance` ∈ {SourceDerivedValue, NormalizedInterpretation,
EngineeringInference, UserDefinedWeight, ComputedResult}. SHACL requires an
evidence span on anything marked source-derived.

**CQ-14 — Which substitutions cannot be decided from these two books?** ✅
`mdcore:InsufficientEvidence`. Three such verdicts exist in v0.1, including the
one that matters most: SA-003 turns on "low torque", which neither book
quantifies.

**CQ-15 — Which alternatives are drop-in replacements?** ✅ *(answer: none)*
No `DirectlySubstitutable` verdict exists in v0.1. Every pilot pair needs at
least a change of shaft or hub feature. That is a finding, not a gap.

**CQ-16 — Does the substitution remove a function the baseline was providing?** ✅
SUB-008. Replacing a shear pin or a fusible key with a stronger connection is
not function-preserving even at equal torque capacity, because
`mech:LimitTransmittedTorque` is lost.

---

## C. Failure and verification

**CQ-17 — What failure modes are associated with an alternative?** ✅
Query 3. Two routes: asserted by a source claim, or introduced by a
substitution.

**CQ-18 — What mechanism drives a failure mode, and what aggravates it?** ✅
`mdcore:causedByFailureMechanism`, `mdcore:aggravatedByCondition`.

**CQ-19 — What calculations, inspections, simulations or tests verify an
alternative?** ✅
Query 4, via `mdcore:requiredVerification`.

**CQ-20 — Which recommended tests do the books not actually define?** ✅
The sharpest question in the set. `mdcore:testRecommended = true` with
`testProcedureSpecified = false` and `acceptanceCriterionSpecified = false`.
Mott recommends testing a non-standardised keyless connection and defines no
procedure, no instrumentation and no pass criterion; the graph records all three
gaps and names the external authority needed to close them.

**CQ-21 — Which quantities needed for a calculation are not supplied by either
book?** ✅
`open_parameters` in `rules/verification_rules.yaml` — for example the
coefficient of friction *f* in the interference-fit torque capacity, without
which Shigley's Eq. (7–49) cannot be closed from the books alone.

**CQ-22 — Which geometry features initiate which failures?** 🟡
`mdcore:initiatesAtFeature` is modelled; the pilot links keyseats to fatigue but
does not yet cover fillets, grooves and holes systematically.

---

## D. Provenance

**CQ-23 — What textbook, edition, chapter, section, page, equation, table or
figure supports a claim?** ✅
Query 7. The citation is *assembled* from stored fields at read time; no
citation string exists anywhere in the pipeline. Example output:

> Machine Elements in Mechanical Design — 6th ed. — ch. 11 (Keys, Couplings, and
> Seals) — sec. 11-5 (Splines) — printed p. 480 — PDF page index 496 — Eq. 11-9;
> Eq. 11-10

**CQ-24 — Where exactly on the page?** ✅
`ev:boundingBox` and `ev:blockIdentifier` give PDF user-space coordinates.

**CQ-25 — Is a claim's underlying text trustworthy?** ✅
`ev:textIntegrity`. The Shigley PDF mis-maps mathematics glyphs onto ASCII, so
spans covering equations are marked `glyph-mismapped` and their text must not be
quoted. Equations resting on such spans carry
`ev:transcriptionSource = rendered-page-image`.

**CQ-26 — Which claims have been verified by a human?** ✅ *(answer: none yet)*
`mdcore:reviewStatus`. All 82 v0.1 claims sit at `NeedsReview`. SHACL blocks
`HumanVerified` without a named reviewer and date.

**CQ-27 — Which parts of the ontology have no supporting evidence?** ✅
Query 10. Returns the four alternatives and the analyst-authored rules that no
claim backs — an expansion worklist, not a defect list.

---

## E. Cross-book comparison

**CQ-28 — Do the two books agree on a topic?** ✅
Query 8. `ev:ClaimAlignment` with type `Agrees`, `ExactMatch` or `CloseMatch` —
e.g. both give the same two key failure modes, and the same load-life exponents.

**CQ-29 — Where do they differ, and how?** ✅
Query 9. Types `DiffersInScope`, `DiffersInAssumption`, `DiffersInTerminology`,
`Contradicts`, `Unresolved`, `NotComparable`, each with the differing conditions
or assumptions spelled out.

**CQ-30 — Do they use the same symbol for the same thing?** ✅
`ev:TerminologyAlignment` and `data/terminology_alignment.csv`. Mott's `k` and
Shigley's `a` are the same exponent; Mott's `P` and Shigley's `F` are the same
load. The symbols are **not merged**, because Shigley uses `P` for something
else entirely.

**CQ-31 — Which topics does only one book cover?** ✅
`docs/source_coverage_map.md`: 26 topics in both, 4 in Mott only (seals, linear
motion, motors and controls, machine frames), 2 in Shigley only (FEA, GD&T).

**CQ-32 — Where does one book's assumption invalidate the other's formula?** ✅
The most consequential cross-book finding in v0.1. Mott's bearing equations
assume a catalogue rating life of 10⁶ revolutions; Shigley states that this is
merely the most common basis and names a manufacturer rating at 90 × 10⁶
revolutions. Applying Mott's formula to such a catalogue gives a wrong answer.
Recorded as alignment `align-c-0004`, type `Refines`.

**CQ-33 — Where do the books disagree on design intent rather than fact?** ✅
`align-c-0006`, type `DiffersInAssumption`, relation `unresolvedRelativeTo`:
Mott recommends N = 3 for keys to survive accidental overload and shock; Shigley
warns against excessive safety factors because the key should be the sacrificial
member. Not formally contradictory, opposite in intent, deliberately left
unresolved.

---

## F. Decision support

**CQ-34 — Compare N alternatives against a requirement set.** 🟡
Query 5 works over the pilot evaluations. A full comparison needs an evaluation
for every (alternative × criterion) pair; v0.1 has 15 evaluations across 3
alternatives.

**CQ-35 — Which alternatives survive a constraint filter?** ⬜
`mdcore:CandidateSet` and `mdcore:exclusionRationale` are modelled and the
selection rules in `rules/selection_rules.yaml` express the filters, but the
rule *engine* that executes them is v0.2 work.

**CQ-36 — What was decided, and why?** ⬜
`mdcore:DesignDecision` and `mdcore:DecisionRationale` are modelled; no decision
instances exist in v0.1, because the pilot documents alternatives rather than a
specific design.

**CQ-37 — Rank alternatives by weighted score.** ❌
Deliberately deferred. Weighted scoring requires `UserDefinedWeight` values that
belong to a user, not to a textbook. The model supports it; v0.1 declines to
invent weights.

---

## G. Extensibility

**CQ-38 — What must be added to support a third textbook?** ✅
A namespace, a `sources` entry in `config/config.yaml`, evidence seeds and claim
seeds. No schema change. See README, "Adding another textbook".

**CQ-39 — What must be added to support a new machine-element family?** ✅
A module under `ontology/machine-elements/`, its function and behavior
individuals, and alternatives. See README, "Adding a machine-element module".

**CQ-40 — Which competency questions does the current data fail to answer?** ✅
This table. Four ⬜/❌ and three 🟡, all with a stated reason.
