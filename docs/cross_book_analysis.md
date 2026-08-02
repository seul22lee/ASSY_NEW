# Cross-book analysis

Where Mott 6e and Shigley 10e agree, complement one another, differ, and where
they cannot be compared at all. Every statement below is backed by a claim in
the graph with page-level provenance; the citations are assembled by
`scripts/query_examples.py --query 8` and `--query 9`.

**Governing rule: nothing is merged.** Where the books differ, both claims stay
in the graph and an `ev:ClaimAlignment` records the difference and its reason. A
reader can always recover what each book actually said.

Coverage in v0.1: **15 claim alignments**, **12 terminology alignments**, over 82
claims (40 Mott, 42 Shigley).

---

## 1. Alignment types used

| Type | Claim alignments (15) | Terminology alignments (12) | Meaning |
|---|---|---|---|
| `Agrees` | 4 | — | Same statement, same scope, no material difference |
| `Complements` | 5 | — | Non-overlapping content on a shared concept; each fills the other's gap |
| `Refines` | 1 | 1 | One narrows, bounds or formalises the other |
| `CloseMatch` | 1 | 4 | Equivalent but differently expressed |
| `ExactMatch` | — | 3 | Same concept; only the notation differs |
| `DiffersInScope` | 2 | — | Same subject, different criteria foregrounded |
| `DiffersInTerminology` | 1 | 3 | Same concept, incompatible naming |
| `DiffersInAssumption` | 1 | — | Opposite design intent, deliberately unresolved |
| `RelatedNotEquivalent` | — | 1 | Adjacent concepts that must not be substituted for one another |
| `Contradicts` | 0 | 0 | No outright factual contradiction found in the pilot |

That `Contradicts` is zero is a finding about the pilot topics, not a claim
about the books as a whole. The interesting disagreements in v0.1 are about
*intent* and *scope*, not about facts.

---

## 2. Terminology alignment

Full table: `data/terminology_alignment.csv`. The consequential entries:

### 2.1 Design factor — same idea, incompatible naming

| | Mott 6e | Shigley 10e |
|---|---|---|
| Term | design factor | design factor / factor of safety |
| Symbol | `N` | `n_d` (chosen) and `n` (achieved) |
| Cite | ch. 5 sec. 5-9, printed p. 189 | ch. 1 sec. 1-11, printed p. 18 |

Shigley separates the factor chosen before design (`n_d`) from the one actually
achieved after choices such as rounding up to a standard size (`n`), and states
the two "generally differ numerically." Mott uses a single `N` for both roles.

**Consequence:** a reader combining formulas across the books must check which
role each symbol plays. Recorded as `align-t-0002`, type `DiffersInTerminology`.

### 2.2 Bearing load/life exponent — same exponent, different symbol

| | Mott 6e | Shigley 10e |
|---|---|---|
| Symbol | `k` | `a` |
| Ball bearings | 3.00 | 3 |
| Roller bearings | 3.33 | 10/3 (exact fraction) |
| Form | `L₂/L₁ = (P₁/P₂)^k`, Eq. (14–1) | `F·L^(1/a) = constant`, Eq. (11–1) |
| Cite | printed p. 571 | printed p. 566 |

Algebraically the same power law. The values agree exactly for ball bearings and
to Mott's rounding for roller bearings; Shigley additionally states that the
roller value applies to cylindrical **and** tapered roller bearings, which Mott
does not qualify.

The symbols are **not merged** in the graph. `align-t-0003` links them as
`ExactMatch` in concept while keeping both `ev:Variable` records, and a test
asserts they remain distinct. Merging by symbol would be actively unsafe here:
Shigley uses `P` for force, pressure *and* diametral pitch, while Mott uses `P`
for bearing load — where Shigley uses `F`.

### 2.3 Other terminology entries

| Concept | Mott | Shigley | Type |
|---|---|---|---|
| Bearing load | `P` | `F` | `DiffersInTerminology` |
| Yield strength | `s_y` (lower case) | `S_y` (upper case) | `ExactMatch`, notation differs |
| Rating life | rated life / L10 | rating life, also minimum life, L10, B10 (ABMA) | `Refines` |
| Basic dynamic load rating | `C` | `C10` / Basic Dynamic Load Rating | `CloseMatch` |
| Key groove | keyseat; notes "keyway" is the common name for the hub groove | keyseat; "keyway depth" | `DiffersInTerminology` |
| Spline | "a series of axial keys machined into a shaft" | "essentially stubby gear teeth" | `CloseMatch` |
| Key failure modes | shear across the interface; bearing compression | direct shear; bearing stress | `ExactMatch` |

The spline framings are worth noting: Mott frames a spline as a *multiplied
key*, Shigley as a *shortened gear*. The framings foreshadow their differing
emphases in §4.1.

---

## 3. Agreements

### 3.1 Key failure modes — the cleanest agreement

Both books identify the same two failure modes, in the same order, and treat
them as checks to be made together.

> **Mott**, ch. 11 sec. 11-4, printed p. 476: "There are two basic modes of
> potential failure for keys transmitting power: (1) shear across the shaft/hub
> interface and (2) compression failure due to the bearing action…"

> **Shigley**, ch. 7 sec. 7-7, printed p. 383: "Failure of the key can be by
> direct shear, or by bearing stress."

`align-c-0001`, type `Agrees`. Both books' equations for the resulting checks are
recorded, so a designer can use either.

### 3.2 Bearing load/life exponents

`align-c-0002`, type `Agrees`, with the rounding difference recorded in
`ev:differingConditions` rather than normalised away.

### 3.3 The design factor is a strength-to-stress ratio

`align-c-0009`. Both derive a design (allowable) stress by dividing a strength
by the factor.

### 3.4 Manufacturer data are mandatory for real bearing selection

> **Mott**, printed p. 571: "It is essential that published data from specific
> manufacturers be used in any real application."

> **Shigley**, printed p. 566: "Each bearing manufacturer will choose a specific
> rating life for which load ratings of its bearings are reported."

`align-c-0013`, type `Agrees`. Both present their own tables as illustrative.

---

## 4. Differences

### 4.1 Splines versus keys — opposite emphases, not a contradiction

The most instructive difference in the pilot.

> **Mott**, ch. 11 sec. 11-5, printed p. 479: "The advantages of splines over
> keys are many." — asserted on load sharing (four or more splines versus one or
> two keys), integral construction, controlled fit, wear resistance and
> indexing.

> **Shigley**, ch. 7 sec. 7-3, printed p. 357: "Splines are generally much more
> expensive to manufacture than keys, and are usually not necessary for simple
> torque transmission."

`align-c-0005`, type `DiffersInScope`. **Not a contradiction.** Mott evaluates
against mechanical performance; Shigley against manufacturing cost, for the
specific case of simple torque transmission. Both are true and they answer
different questions.

Merging these into a single verdict on splines would destroy exactly the
information a designer needs. Both are retained, and substitution assessment
SA-001 cites **both** — Mott's advantages as the reason to prefer a spline when
axial motion is required, Shigley's cost as the reason not to when it is not.

### 4.2 How conservative should a key be? — an unresolved disagreement of intent

The sharpest tension found.

> **Mott**, design procedure for parallel keys, printed p. 477, step 3: "Specify
> a suitable design factor, N. In typical industrial applications, N = 3 is
> adequate to accommodate accidental overloads and shock."

> **Shigley**, printed p. 383: "Excessive safety factors should be avoided in
> key design, since it is desirable in an overload situation for the key to
> fail, rather than more costly components."

`align-c-0006`, type `DiffersInAssumption`, relation `unresolvedRelativeTo`.

The two are not formally contradictory — Mott gives a number, Shigley gives a
direction, and N = 3 is not necessarily "excessive." But they express **opposite
design intents**:

| | Mott's intent | Shigley's intent |
|---|---|---|
| The key should | survive the accidental overload | fail before costlier components do |
| So the design factor should be | comfortable (N = 3) | as small as is safe |
| The key is | a load-carrying member | a sacrificial fuse |

Which applies depends on something neither book states in the cited passages:
whether *this* key is intended to be sacrificial.

**This is left explicitly unresolved.** It is not averaged, and neither is
declared correct. It has a direct consequence in the ontology: rule `SUB-008`
treats removal of `mech:LimitTransmittedTorque` as a loss of function, so
replacing a fusible key with a stronger connection is not function-preserving
even at equal torque capacity — but only when overload protection is a stated
requirement.

### 4.3 Spline torque capacity — not comparable

> **Mott**, printed p. 480: torque capacity for SAE straight-sided splines,
> based on a 1000 psi allowable bearing stress, `T = 1000·N·R·h` per inch of
> spline length, in inch units.

> **Shigley**, printed p. 357: splines "are typically used to transfer high
> torques." No capacity equation in the cited section.

`align-c-0014`, type `DiffersInScope`. One is quantitative and narrow, the other
qualitative and broad. **Only Mott's claim can support a calculation**, and only
within its stated unit system — a constraint captured as verification rule
`VER-007`, because applying that formula in SI, or forgetting the per-inch
basis, is a plausible and consequential error.

---

## 5. Complementary coverage

Cases where neither book is complete alone.

### 5.1 Axial motion under torque — the pair that makes SA-001 possible

> **Mott**, printed p. 479: "Sliding motion between a standard parallel key and
> the mating element should not be permitted."

> **Shigley**, printed p. 357: a spline "can be made with a reasonably loose slip
> fit to allow for large axial motion between the shaft and component while still
> transmitting torque."

`align-c-0007`, type `Complements`. Mott rules the key **out**; Shigley rules the
spline **in**. Neither book states the substitution; together, from two
independent sources, they establish it. This pair is the evidential basis of
substitution assessment SA-001.

### 5.2 Multiple keys

Mott (p. 477) offers "two keys or a spline" when a single key would exceed the
hub length. Shigley (p. 383) adds the arrangement Mott omits: "typically
oriented at 90° from one another." `align-c-0008`.

### 5.3 When to use a Woodruff key

Entirely non-overlapping rationales for the same element:

| Mott, p. 473 | Shigley, p. 384 |
|---|---|
| light loading | better concentricity after assembly |
| easy assembly and disassembly | especially important at high speeds |
| | keyslot need not be cut into the shoulder stress-concentration region |
| | deeper penetration prevents key rolling in smaller shafts |

`align-c-0011`. Together they give a fuller applicability profile than either
book alone.

### 5.4 Stress concentration of competing connections

Mott (p. 483): "the presence of any of the pin-type connections produces stress
concentrations in the shaft." Shigley (p. 357): the press/shrink fit
stress-concentration factor "is usually quite small."

`align-c-0012`, type `Complements`. Read together these support a comparative
ranking that **neither book states outright**. The ranking is therefore recorded
as an analyst inference (`mdcore:EngineeringInference`) wherever it is used —
never as textbook content.

### 5.5 Why bearings have a finite life

Mott gives the physical reason (fatigue under high contact stress); Shigley gives
the statistical definition of the quoted life (the 10th percentile of the
revolutions-to-failure distribution). `align-c-0015`.

---

## 6. The most consequential finding: a hidden assumption

`align-c-0004`, type `Refines`.

Mott's working equations for bearing selection —

> `L_d = (C/P_d)^k · 10⁶` and `C = P_d·(L_d/10⁶)^(1/k)`, printed p. 575

— assume the manufacturer's catalogue data are rated at **10⁶ revolutions**.
Mott states this as a conditional ("If the reported load data in the
manufacturer's literature is for 10⁶ revolutions…") but then proceeds
throughout on that basis.

Shigley bounds it explicitly:

> printed p. 566: "The most commonly used rating life is 10⁶ revolutions. The
> Timken Company is a well-known exception, rating its bearings at 3 000 hours at
> 500 rev/min, which is 90(10⁶) revolutions."

**Consequence:** applying Mott's formula to a catalogue rated on the other basis
gives an answer wrong by a factor of 90^(1/k) ≈ 4.5 in required capacity. A
knowledge graph that merged the two books' bearing sections into one "bearing
life" concept would lose precisely the caveat that prevents this error.

The alignment preserves both claims and records the differing assumption.
Verification rule `VER-005` makes it a **precondition**: "The catalogue
rating-life basis must be established before the load-life equation is applied."

---

## 7. Where comparison is impossible

From `docs/source_coverage_map.md`: 26 of 32 topics are covered by both books.

**Mott only** (4): seals; linear motion elements; electric motors and controls;
machine frames and structural members.

**Shigley only** (2): finite-element analysis; geometric dimensioning and
tolerancing.

For these topics the ontology can hold claims but no `ev:ClaimAlignment`. A query
asking whether the books agree correctly returns **nothing** rather than a
fabricated consensus.

Depth differences within shared topics are recorded in the coverage matrix — for
example Shigley devotes a 65-page chapter to deflection and stiffness while Mott
distributes the same material across sections of chapters 3 and 12.

---

## 8. Review status

All 15 claim alignments and all 12 terminology alignments are at
`mdcore:NeedsReview`. They were authored by an analyst reading the cited pages
and mechanically verified against the PDFs, which is stronger than automatic
extraction but is **not** human sign-off.

`align-c-0006` — the design-intent disagreement — most needs a human engineer's
judgement, and is flagged accordingly. The ontology's position is that it should
stay unresolved until someone with authority decides whether the key in a given
design is meant to be sacrificial.
