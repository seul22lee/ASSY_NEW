# EXE-BM003-01 — bounded self-audit

Twelve questions, answered against what is actually in this directory rather than
against what was intended. Where the answer is unflattering it is written that
way.

---

### 1. Is there any geometry representation here other than exact CadQuery/OCCT B-rep?

No. `build.py` builds ten solids out of `cq.Solid.makeBox`, `makeCylinder` and
boolean operations, and every distance and volume in `validation/` comes from
`cadval.min_distance` (BRepExtrema_DistShapeShape) and `cadval.common_volume`
(BRepAlgoAPI_Common) applied to those solids. There is no capsule model, no
finite-cylinder collision routine, no proxy, and no second engine. Tessellation
appears only inside `review_views.py` and `make_videos.py`, for pixels, and no
geometric claim rests on either.

### 2. Is any claim in this reference supported by something other than a kernel measurement?

Three, and each is labelled:

- **NRM-BM-003-008** (no tool, motor or fixture) is discharged by reading the
  declared segments and confirming that no participant outside the ten bodies
  appears in any of them. That is a check on a declaration, not on geometry, and
  the evaluation record says so.
- **NRM-BM-003-004** (a comprehensible sequence exists) rests on the declared
  segment list plus the measurement that each is interference free. Whether a
  user would find it comprehensible is not measurable and is not claimed.
- The **five bayonet turns** establish that no rigid-body translation along the
  insertion axis remains after the turn. That the turn itself will not be undone
  by handling is *not* established and is recorded as NOT_VERIFIED.

Everything else is a number the kernel produced.

### 3. Did any Oracle predicate have to be weakened, reinterpreted or worked around?

No. Two things were *fixed on this side* rather than on the Oracle's:

- The first exact model had no outward stop, so a leg could swing past deployed.
  NRM-BM-003-010 requires forbidden mobility to be addressed, so the mechanism
  gained the stop pads (R2). The invariant was not softened.
- The connectivity check first treated `BODY-RING`/`BODY-RING-CAPTOR` as a pair
  that must stay engaged, and it reported the ring as detaching every time it was
  lowered. That was the *checker* being wrong about what a limit stop is, not the
  Oracle. It was corrected to distinguish running pairs from limit stops, and the
  ring's captivity is now established by an escape probe.

None of the three Oracle reopening conditions was met.

### 4. Does any measurement pass only because of a tolerance choice?

Two are close enough to say so plainly:

- `INT-STOP-x` declares a 0.15 mm nominal and measures 0.1427 mm. The difference
  is real and it is geometric, not numerical: `outward_stop_clearance` is applied
  as a *vertical* offset, and `min_distance` returns the *perpendicular* distance
  to a heel underside that is tilted about 18° from horizontal. It passes because
  0.0073 < `contact_tol` = 0.05. If `contact_tol` were 0.005 it would fail, and
  the correct fix would be to declare the perpendicular nominal, not to widen the
  tolerance.
- The blocking gap `INT-BLOCK-x` is 0.4 mm by construction and measures 0.4 mm.
  Nothing is riding on the tolerance there.

No other declared nominal is within a factor of two of `contact_tol`.

### 5. Could the negative controls pass for the wrong reason?

The harness rejects three ways of passing wrongly:

- a control that makes the checker **raise** rather than measure is recorded as
  NOT detected, with the exception type;
- a control that flips its target predicate but also flips a predicate it
  declared unrelated is recorded as NOT detected;
- every control's baseline is the fully passing model, so a control cannot
  "detect" a defect that was already there.

What the harness does **not** rule out: a control could flip its target for a
reason other than the intended one. NC-11's record therefore states explicitly
that both endpoints stay interference free and only the interior fails, which is
the property being tested. NC-10's record states the opposite — that its
interference also exists at an endpoint — because in this mechanism leg-to-leg
separation is monotone in the leg angle and an interior-only leg-to-leg collision
cannot be constructed. That limitation is a property of the mechanism and it is
written down rather than papered over.

### 6. Is any dimension in `parameters.yaml` traceable to the frozen source?

None. The BM-003 source contains no digit. Every value is a fixture design choice
under FRE-BM-003-011 and `parameters.yaml` says so at the top. The risk this
creates — that a reader treats one of them as a requirement — is addressed only
by that declaration, which is a weak control. A stronger one would be a mechanical
check that no Oracle artifact cites a number from this file; none exists, because
this reference does not modify the Oracle.

### 7. Is the STEP output treated as authoritative anywhere?

No. `validation/reimport_report.json` exports each body to `.brep` and `.step`,
re-imports both independently, and compares validity and volume. BREP is held to
1e-6 mm³ absolute; STEP to a relative tolerance, because a STEP round trip re-fits
geometry. The authoritative source is stated in `GOVERNANCE.yaml` as
parameters + build code + the native OCCT B-rep. No downstream check reads a STEP
file.

### 8. Does the evidence support the completion claim, no more and no less?

The claim is `ONE_POSITIVE_EXECUTABLE_REFERENCE_VALIDATED`. The evidence is one
mechanism, one state-maintenance class, one realization class. It says nothing
about the other three classes or the other admitted families, and
`GOVERNANCE.yaml` sets `cross_principle_permissiveness_validated: false` for that
reason.

The one place the claim could be read as larger than the evidence is
NRM-BM-003-009. What is shown is that a *path is absent* in the exact rigid
model. What is not shown, and cannot be from rigid geometry, is that the block
survives any real load. AMB-BM-003-005 blocks the question anyway, but the
asymmetry is worth stating: "geometrically impossible" here means impossible for
rigid bodies at nominal dimensions, not impossible for a physical object.

### 9. Is anything here reachable from production?

No. Nothing outside this directory was created or modified. `validate.py` imports
`cadval` and `valcore` read-only and neither was changed. No stage contract, no
provider, no benchmark source, no Oracle file, and no `assy_v3` module references
this reference or is referenced by it.

### 10. Was the design changed to make a check pass, rather than to be right?

R2 (the outward stop) is the case to examine, because it was added *after* a
check would have caught its absence. But no check caught it — the first exact
model passed every predicate that existed at the time, and the gap was found by
reading NRM-BM-003-010's list of forbidden freedoms against what the mechanism
actually constrained. The stop pad was added because the mechanism was wrong, and
the predicate `P_OUTWARD` and control NC-17 were added at the same time so the
absence would be caught in future.

R4 is the opposite case and is worth being blunt about: `rib_h` was reduced from
4.0 to 2.0 *because* `P_LIFT_ONLY` failed. That is changing a dimension to make a
check pass. It is defensible only because the check was testing a property the
mechanism was supposed to have and had silently lost in R1 — the turn being
functionally necessary — so the failure was a true report of a real regression,
not a threshold problem. Had the fix been to delete the predicate instead, that
would have been the illegitimate move.

### 11. What would most likely be wrong if this reference is wrong?

In order of how much would be affected:

1. **The declared regions of interest.** For stations B and C an ROI is the
   axis-aligned hull of a rotated rectangle, so it is larger than intended. If it
   swallowed unintended geometry, an interaction could be measured against the
   wrong feature and still report a plausible number. The mitigation is weak but
   real: all three stations report the same value, and a wrong ROI at one station
   would almost certainly not.
2. **The sampling density.** Every path claim is sampling, not a proof. A thin
   interference between samples would be missed. NC-11 shows the sampling is dense
   enough to catch a 0.6 mm-tall interior feature; it does not show what the
   smallest catchable feature is.
3. **The interpretation of NRM-BM-003-010's "gross" freedom.** The legs retain
   about 1.2° of fold-back play and about 1.4° of outward play between their two
   stops. Calling that "not gross" is a judgement. The numbers are reported so a
   reader can disagree.

### 12. Is anything in this directory unused, unreferenced or dead?

`validation/videos.json` and `validation/review_media.json` exist only if
`make_videos.py` and `review_views.py` have been run; they are review media and
nothing in `validate.py` depends on them. `build.py` carries eight `defeat` flags
that are used only by the negative controls in `validate.py` and by nothing else —
that is deliberate, and each is commented as control-only. `cadvideo`'s
`section_polygons` and `render_review_section` are not used by this reference; it
has no drawn sections, only cutaway renders.

---

**Overall self-assessment:** the mechanism and its evidence hold up. The two
weakest points are the ROI hulls at stations B and C (question 11.1) and the
R4 dimension change made in response to a failing check (question 10), both of
which are recorded here rather than smoothed over.
