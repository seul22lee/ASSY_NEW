# Ontology design

How the mdkg ontology is put together, and why each significant choice was made.
Where a choice constrains what the ontology can say, that is stated.

**Everything in this document that describes ontology structure is
ontology-engineering design, not textbook content.** Statements attributed to
Mott or Shigley appear only as cited claims in `ontology/mott6-claims.ttl` and
`ontology/shigley10-claims.ttl`.

---

## 1. Layering

The ontology develops top-down through four levels. Each level may specialise
the one above it and must not depend on the one below.

| Level | Content | Where |
|---|---|---|
| 1 | General engineering-design concepts — artifact, function, behavior, requirement, context, decision, substitution, failure, verification, evidence | `ontology/core/` |
| 2 | Mechanical-design specialisations — mechanical artifacts and interfaces, mechanical functions and behaviors, load and motion conditions, materials, manufacturing, mechanical failure modes | `ontology/mechanical-design/` |
| 3 | Machine-element families, organised by function | `ontology/machine-elements/families.ttl` |
| 4 | Specific elements, design alternatives, claims, rules and evidence | `ontology/machine-elements/connections.ttl`, `ontology/*-claims.ttl`, `rules/`, `data/` |

Nothing at Level 1 mentions a shaft, a key or a bearing. That is the test of
whether the core is genuinely general: it should be reusable for a design
ontology in a different engineering domain with the mechanical layer swapped
out.

### Why not derive the ontology from the tables of contents

Mott's Chapter 11 covers keys, couplings **and** seals together. Shigley
distributes shaft components across Chapter 7 and puts couplings with clutches,
brakes and flywheels in Chapter 16. Neither grouping is a fact about machine
elements; both are facts about how a book teaches. `docs/source_coverage_map.md`
uses the chapter structures only to identify domain modules and measure
coverage. The families in `ontology/machine-elements/families.ttl` are organised
by the function a family delivers.

---

## 2. Class census

Counts from `outputs/ontology_summary.json`.

| Module group | Named classes | Object properties | Datatype properties |
|---|---|---|---|
| `core/` (incl. evidence) | 115 | 123 | 92 |
| `mechanical-design/` | 79 | 5 | 9 |
| `machine-elements/` | 92 (83 of them punned element types) | 1 | 0 |
| **Total** | **286** | **129** | **101** |

The brief targeted "approximately 20–40 core classes before adding
domain-specific classes." A note on that number, because 115 looks like a
violation and is not quite one:

- **~41 are the top-level concepts** the brief enumerates — `DesignedArtifact`,
  `Interface`, `Function`, `Behavior`, `Requirement`, `OperatingContext`,
  `DesignAlternative`, `SubstitutionAssessment`, `FailureMode`,
  `VerificationMethod`, `Claim`, `EvidenceSpan`, and so on. That is inside the
  intended range.
- **~74 are taxonomy leaves directly beneath them** — 31 condition subclasses
  in `context.ttl` (`StaticLoading`, `CyclicLoading`, `ShockLoading`, …), 19
  verification-method subclasses (`FatigueTest`, `DimensionalInspection`, …),
  24 evidence structure classes (`Chapter`, `Section`, `Page`, `Equation`, …).
  These are enumerated vocabulary, not independent concepts; the brief itself
  lists most of them by name.

The 83 punned element types in `machine-elements/` are each declared both
`owl:Class` and `owl:NamedIndividual`. This is OWL 2 DL punning, used so that a
`mdcore:DesignAlternative` can point at its element type with
`melem:usesElementType` without duplicating the taxonomy as a parallel
individual hierarchy.

---

## 3. TBox / ABox separation

| Layer | Holds | Changes when |
|---|---|---|
| **TBox** — `ontology/core/`, `ontology/mechanical-design/`, `ontology/machine-elements/` | Classes, properties, SKOS vocabularies, formal definitions | The conceptual model changes. Rare. |
| **ABox** — `ontology/*-claims.ttl`, `ontology/alignments.ttl` | Book-derived claims, evidence spans, equations, alignments, substitution assessments | A source is read, or a curator adds data. Often. |
| **Rule layer** — `rules/*.yaml` | Eligibility, selection and substitution logic | Engineering judgement is revised. |
| **Evidence layer** — `data/*.jsonl` | Provenance, verified against the PDFs | Extraction is re-run. |

**A claim is never an axiom.** "Mott states that splines perform the same
function as a key" is an `ev:NormalizedClaim` individual, not a subclass axiom.
If it were an axiom, it could not be conditioned, contradicted, revised or
rejected without editing the schema, and a reasoner would propagate it into
conclusions nobody authorised.

### Generated versus hand-authored files

The brief asks for generated artifacts to be stored separately from
hand-authored ontology files, and also asks for specific paths such as
`ontology/core.ttl`. These pull in opposite directions. The resolution:

| File | Status |
|---|---|
| `ontology/core/*.ttl`, `ontology/mechanical-design/*.ttl`, `ontology/machine-elements/*.ttl` | **Hand-authored.** The real TBox. |
| `shapes/modules/*.ttl` | **Hand-authored.** The real shapes. |
| `data/evidence_seeds.yaml`, `data/claims_seed.yaml`, `data/alignments_seed.yaml`, `data/substitutions.yaml`, `rules/*.yaml` | **Hand-authored.** The curated data. |
| `ontology/core.ttl`, `ontology/evidence.ttl`, `ontology/mechanical-design.ttl`, `ontology/machine-elements.ttl` | **Generated bundles** of the module directories, for tools that want one file. |
| `ontology/mott6-claims.ttl`, `ontology/shigley10-claims.ttl`, `ontology/alignments.ttl` | **Generated** from `data/`. |
| `shapes/ontology-shapes.ttl` | **Generated** bundle of `shapes/modules/`. |
| `data/evidence_spans.jsonl`, `data/claims.jsonl`, `data/terminology_alignment.csv`, `data/coverage_matrix.csv` | **Generated** from the seeds, with provenance resolved. |
| `build/`, `outputs/` | **Generated.** Never hand-edited. |

Every generated file opens with a `GENERATED FILE — DO NOT EDIT BY HAND` banner
naming its inputs.

### Deviations from the proposed directory layout

Two, both with a technical reason:

1. **`shapes/modules/` instead of shapes directly under `shapes/`.** The
   validator globs its shape modules. If the merged bundle sat beside them it
   would be loaded twice on every run. Modules live one level down; the bundle
   sits at the required path.
2. **`machine-elements/other-families.ttl` instead of eleven per-family files.**
   At v0.1 each of `gears.ttl`, `springs.ttl`, `seals.ttl` … would hold five to
   ten lines. Eleven near-empty files obscure the structure rather than reveal
   it. The two pilot families that carry real depth — `connections.ttl` and
   `bearings.ttl` — do have their own files. **Split criterion:** a family gets
   its own module once it has design alternatives with evaluations, or more than
   ~20 classes.

---

## 4. Function–Behavior–Structure

```
Function  --realizedBy-->  Behavior  --enabledBy-->  DesignAlternative
                              |
                        reliesOnEffect
                              v
                        PhysicalEffect
```

Behavior is not decoration. Four alternatives all perform
`mech:TransmitTorqueShaftToHub`, but through different behaviors:

| Alternative | Behavior | Consequence |
|---|---|---|
| Parallel key | `ShearLoadTransfer` + `BearingLoadTransfer` | Fails by shear or by crushing; verified by two stress checks |
| Involute spline | `DistributedToothContact` | Load shared over several flanks; can slide under torque |
| Press fit | `FrictionalLoadTransfer` | Capacity depends on a friction coefficient and a *maintained* pressure; fails by gross slip |
| Setscrew | `FrictionalLoadTransfer` | Same behavior, same sensitivity, far lower capacity |

Two alternatives sharing a behavior share a failure family. Two alternatives
sharing only a function share almost nothing operationally. An ontology that
modelled function alone could not express that difference, and would make press
fits and keys look interchangeable.

`mdcore:behaviorRequiresCondition` carries the enabling condition — for
friction-based transfer, `mech:MaintainedInterfacePressure`. That is why
`SEL-003` flags friction connections when overload protection is required.

---

## 5. Context as a first-class object

An `mdcore:OperatingContext` is a bundle of reusable
`mdcore:OperatingCondition` individuals. Conditions are shared across contexts;
contexts belong to a design situation.

**An empty context is not "all contexts."** A context or rule with no conditions
must declare `mdcore:contextUnspecified true`. SHACL enforces it. Silence would
otherwise be read as universal validity — the single most common way a
book's rule of thumb becomes a fabricated law.

### Thresholds

No class in this ontology carries a numeric boundary for a vague term. There is
no `HighSpeedCondition` with a value attached. Instead:

```turtle
mott6:c-0010_threshold a mdcore:ThresholdDefinition ;
    mdcore:definesTerm "low-cycle fatigue" ;
    mdcore:thresholdIsUniversal false ;
    mdcore:thresholdScopeNote "The source explicitly denies that a specific dividing line can be defined." .
```

`thresholdIsUniversal` is mandatory. Five threshold definitions exist in v0.1 —
"low-cycle fatigue", "high torque", "low torque", "high speed", "heavy load" —
and **all five are `false`**, because in every case the source used the term
without fixing a boundary. Where a source gives no number, none is invented, and
downstream queries must treat the term as unknown rather than as false.

---

## 6. Substitution semantics

### Why the assessment is the individual

"A can replace B" is not a proposition. It becomes one only when you add: which
function is preserved, in which context, against which requirements, after which
modifications. So `mdcore:SubstitutionAssessment` is reified and the two
alternatives are two of its arguments.

### The six states

| State | Meaning | Minimum evidence |
|---|---|---|
| `NotAnAlternative` | Function or interface not preserved | A violated requirement or an incompatible interface |
| `FunctionalAlternative` | Shares at least one required function; **not** interchangeable | Co-function alone |
| `ConditionallySubstitutable` | Works only under stated conditions or after stated modifications | ≥1 condition **or** ≥1 modification (SHACL-enforced) |
| `DirectlySubstitutable` | Preserves function, interfaces, conditions and essential requirements without significant redesign | Identical interface, zero modifications, zero violated requirements (SHACL-enforced) |
| `PreferredAlternative` | Substitutable **and** better against a stated requirement set | ≥1 applicable and ≥1 satisfied requirement (SHACL-enforced) |
| `InsufficientEvidence` | Sources do not settle it | — |

`FunctionalAlternative` is the ceiling that co-function alone can reach. Rule
`SUB-000` encodes exactly that, and is explicitly non-terminal so that later
evidence can strengthen or weaken it.

### Three prohibited inferences

**No symmetry.** `substitutionAssessedAs` is not `owl:SymmetricProperty`. The
graph contains a worked counter-example: SA-001 and SA-006 assess the *same
pair* in the *same context* in opposite directions and reach opposite verdicts.
`validate_ontology.py` fails the build if a mirrored edge exists without its own
assessment.

**No transitivity.** Not `owl:TransitiveProperty`. A→B and B→C may preserve
different functions under different requirements; composing them composes
nothing. Checked explicitly.

**No defaulting.** `DirectlySubstitutable` may never be reached from a shared
function, nor from the absence of contrary evidence. SHACL requires positive
interface evidence. v0.1 contains **zero** `DirectlySubstitutable` verdicts,
which is the honest result: every pilot pair needs at least a change of shaft or
hub feature.

### Reasoning is switched off

`pyshacl` runs with `inference="none"`. Turning on RDFS or OWL-RL inference
would materialise entailments across the claim layer, and a claim is not an
axiom. Validation checks what was asserted, not what could be derived from it.

---

## 7. Evidence and provenance

### The pipeline

```
PDF → EvidenceSpan → ExtractedClaim → NormalizedClaim
    → CandidateDesignRule → HumanValidatedRule → axiom or executable rule
```

Stages 1–3 are automated (`extract_pdf_structure.py`,
`build_evidence_spans.py`, `build_claims.py`). The arrow from
`CandidateDesignRule` to a validated rule is a **human gate** the pipeline
cannot cross.

### The anti-fabrication mechanism

The design inverts the usual authoring order. An analyst writes only *document,
page index, anchor phrase*. Everything citable is then **resolved and verified**:

1. `build_evidence_spans.py` reopens the PDF and fails if the anchor is not on
   the stated page.
2. It reads the printed page from the PDF's own page-label tree — never
   computes it.
3. It records the containing chapter and section from the PDF outline.
4. It captures the bounding box of the block that carries the anchor.
5. `build_claims.py` copies the location onto the claim; the claim seed file has
   **no fields** for chapter, section or page, so they cannot be typed by hand.
6. `validate_ontology.py` reopens both PDFs on every run and re-verifies all 91
   spans, including that the recorded page label still matches the PDF's.
7. `query_examples.py` assembles the citation string from stored fields at read
   time. No citation string is stored anywhere.

Consequently a fabricated page number is not merely discouraged — it breaks the
build.

### The two page numbers

`ev:pdfPageIndex` (0-based) and `ev:printedPage` (string) are separate
properties and neither is derived from the other. In these two files the offset
happens to be constant — Mott +16, Shigley +22 — but it differs between them and
would differ again in a third source, so the code never uses it. A test asserts
both offsets and asserts that they differ, to document why.

### Text integrity

Extraction quality is measured, not assumed. Each span records the fraction of
its characters set in a mathematics font, and a verdict:

| Verdict | Meaning | Count in v0.1 |
|---|---|---|
| `reliable` | Characters faithfully represent the printed glyphs | 87 |
| `partial-glyph-loss` | Some glyphs dropped (Mott: primes, some operators) | 3 |
| `glyph-mismapped` | Glyphs decode to **unrelated** ASCII — text is wrong in a way that looks plausible | 1 |
| `unverified` | Not assessed | 0 |

The Shigley PDF renders `=` as `5`, `−` as `2`, `+` as `1`, `∂` as `0` and `∫`
as `#`. Any equation resting on such a span was transcribed from a **rendered
page image**, recorded as `ev:transcriptionSource = rendered-page-image`, and a
test enforces that rule. See `docs/extraction_report.md`.

### Equations and variables

Equations are structured objects: number, symbolic expression, transcription
source, assumptions, validity conditions, required unit system, and links to the
tables and figures they depend on. `ev:explainedBySpan` ties a numbered item to
the running text that explains it, so a table is never cited stripped of the
conditions its own paragraph placed on it.

Variables are **source-scoped**. Mott's `k` and Shigley's `a` are the same
physical exponent and are *not* merged; they are joined by an
`ev:TerminologyAlignment`. Merging by symbol would be actively wrong here:
Shigley also uses `P` for force, pressure and diametral pitch.

### Units

`mdcore:QuantityValue` carries `numericValue`, `unitSymbol`, `originalValue`,
`originalUnit` and, where a conversion occurred, `conversionMethod`. Units are
validated with Pint at build time. **A missing unit is always an error**;
dimensionless quantities carry the explicit token `dimensionless`, because "no
unit recorded" and "this is a pure number" are different facts.

Worked example — Shigley prints the roller-bearing exponent as the fraction
10/3:

```json
{"role": "load/life exponent, roller bearings",
 "value": 3.3333333333, "unit": "dimensionless",
 "original_value": "10/3", "original_unit": "dimensionless",
 "conversion_method": "exact fraction 10/3 evaluated to 10 decimal places; the source prints the fraction, not a decimal"}
```

---

## 8. Claim promotion workflow

| State | Who may assign | Meaning |
|---|---|---|
| `AutomaticallyExtracted` | pipeline | Raw output of extraction |
| `Normalized` | pipeline | Restated in controlled vocabulary, units explicit |
| `NeedsReview` | pipeline | **Highest state any automated process may assign** |
| `HumanVerified` | human only | A named person compared the statement against the printed page |
| `Rejected` | human only | Retained, not deleted, so the same error is not re-proposed |

**All 82 claims in v0.1 are `NeedsReview`.** They were authored by an analyst
reading the cited pages and were mechanically checked against the PDF text —
stronger than automatic extraction, but not human sign-off. `build_claims.py`
raises an error if a seed file tries to declare `HumanVerified`, and SHACL
rejects `HumanVerified` without a named reviewer and a date. A test asserts the
count is zero.

---

## 9. Formalism choices

| Need | Formalism | Why |
|---|---|---|
| Reusable class and property definitions | **OWL** | Shared semantics, tool support |
| Controlled vocabularies, labels, taxonomies | **SKOS** | Satisfaction levels, substitution states, review states, alignment types and requirement kinds are *terms*, not classes with instances. Forcing them into OWL would imply an instance-of relationship that does not hold. |
| Book-derived claims and evidence | **RDF instances** | Data, revisable without schema change |
| Structural validation | **SHACL** | Closed-world checks; OWL's open-world semantics cannot express "must have a unit" |
| Selection and substitution logic | **YAML** | Conditional, defeasible, revisable by engineers who do not write OWL |
| Evaluation, filtering, scoring | **Python** | Where the rules actually execute |

Korean labels are added as `skos:altLabel@ko` on the concepts most likely to be
searched in Korean. English is canonical throughout.

---

## 10. Known limitations of v0.1

Stated plainly, because a design document that lists only strengths is not
useful.

1. **Claims attach to element *types*; substitution operates on
   *alternatives*.** `mott6-c-0023` is about `melem:TaperKey` (the part), while
   SA-* assessments concern `melem:TaperKeyConnection` (the solution concept).
   Query 10 therefore reports four alternatives as unsupported when claims about
   their element type do exist. A bridging property or query is v0.2 work; the
   current report is honest but over-strict.
2. **No design decisions.** `DesignDecision` and `DecisionRationale` are
   modelled but unused; the pilot documents alternatives, not a specific design.
3. **The rule layer is declarative, not executed.** `rules/*.yaml` is
   machine-readable and validated, but no engine evaluates it against a design
   problem yet. `SEL-005` is even marked `executable: false` because it depends
   on a threshold no source supplies.
4. **One pilot function dominates.** 16 of 22 alternatives serve
   `TransmitTorqueShaftToHub`. Bearings are covered at family level; gears,
   springs, seals and flexible drives are taxonomy only.
5. **Numeric stress-concentration factors are deliberately absent.** Shigley's
   keyseat factors sit in mis-mapped mathematics-font runs *and* originate in an
   external reference. The claim records their structure; the numbers are not
   reproduced.
6. **Zero human-verified claims.** By design, but it means nothing here should
   yet be treated as a validated design fact.
