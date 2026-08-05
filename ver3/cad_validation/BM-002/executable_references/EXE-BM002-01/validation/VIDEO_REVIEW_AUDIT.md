# EXE-BM002-01 — video review audit

Two clips. Both were **decoded back from disk** for this audit, not merely
written: every frame was read through `imageio` / ffmpeg, the container metadata
was compared with what the writer intended, and representative frames were
extracted and looked at.

Both are **PRESCRIBED CAD KINEMATIC ANIMATIONS**. Every body position in every
frame comes from `build.py`'s pose law or from an assembly offset declared in
`assembly.yaml`. Nothing integrates an equation of motion, resolves a contact,
applies a force or computes a strain. **No MuJoCo was run and none exists in this
phase.**

---

## Engine and provenance — both clips

| | |
|---|---|
| engine | cadquery-ocp tessellation + matplotlib painter + ffmpeg (libx264) |
| cadquery | 2.4.0 |
| matplotlib | 3.7.5 |
| numpy | 1.24.4 |
| imageio_ffmpeg | 0.5.1 |
| ffmpeg | 4.2.2-static |
| source geometry signature | `6824e5102424e3db883f16b684ab54f02c14eed19bead0116c704092156bc2ee` |
| geometry source | the reference's own B-rep solids, posed by the same functions the validator uses. No proxy geometry, no remodelling, no generative imagery. |
| hidden-surface handling | true z-buffer per pixel. Face rims are drawn only where they win the depth test, so hidden edges stay hidden. |
| mesh artifacts | none. Triangles carry shading and are never stroked; only a face's own boundary is drawn. Confirmed by eye on the extracted frames. |

---

## 1. `validation/review/lift_cad_operation.mp4`

### Decoded from disk

| property | intended | **read back** |
|---|---|---|
| codec | H.264 (libx264), yuv420p | **h264** |
| resolution | 1280 × 720 | **1280 × 720** |
| fps | 30 | **30.0** |
| frame count | 300 | **300** |
| duration | 10.0 s | **10.0 s** |
| bytes | — | **1 931 801** |

* output SHA-256 `8f662627b15fd7d4fcb79070402bed98cfe4189a4c92776d2b09b7e0789c7b3c`
* trajectory SHA-256 `89b83806d33223f63096fdd5cf15c2c1cde9a0df3814277494a6fd4f9494b312`
  — taken over the exact pose samples the frames were drawn from
  (t, crank angle, support-surface z, rod angle, platform-pin z, crank-pin y and z),
  rounded to 1e-6 before hashing.
* GIF companion `validation/review/lift_cad_operation.gif`,
  SHA-256 `129485aa00ebd1d9a430dc53f8c27207…`

### Cameras — fixed for the whole clip, and recorded

**Main** — orthographic, eye (−380, −320, 250), target (14, 74, 124), up (0,0,1),
half-height 150 mm. Chosen because it is the only single view in which the
**exterior handle** and the **interior linkage** are both visible, which is what a
reviewer needs in order to see that turning the handle is what moves the platform.
Housing and rear panel are intersected with y ≤ 74 **for display only**.

**Fixed inset** — orthographic, eye (760, 70, 128), target (40, 70, 128),
half-height 146 mm: the crank/link motion plane face-on with the rear panel
removed. Present in every frame, same position, same scale.

### State timeline, as recorded and as seen

| t (s) | frame | state | crank | support-surface z |
|---|---|---|---|---|
| 0.000 | 0 | **BOTTOM** | 0.0° | 126.000 |
| 0.033 | 1 | **RISING** | 1.2° | 126.008 |
| 5.000 | 150 | **TOP** | 180.0° | 216.003 |
| 5.033 | 151 | **LOWERING** | 181.2° | 215.988 |
| 9.967 | 299 | **BOTTOM RETURN** | 358.8° | 126.008 |

Required sequence BOTTOM → RISING → TOP → LOWERING → BOTTOM RETURN: **present, in
that order.**

### Verified by looking at the decoded frames

* **frame 0** — crank pin at bottom dead centre, rod vertical, platform at
  z = 126.0, travel bar empty, payload seated on the plate, "KINEMATIC EXTREMUM"
  banner shown.
* **frame 75 (90°, 2.50 s)** — crank pin at +Y, rod at its maximum 31.97° from
  vertical, platform at 158.1, travel bar about one third full, platform arrow
  pointing up.
* **frame 150 (180°, 5.00 s)** — rod vertical again, platform at 216.0, travel bar
  full, payload standing proud of the rim, "KINEMATIC EXTREMUM" banner shown.
* **frame 225 (270°)** — crank pin at −Y, rod at −31.97°, platform descending.
* **frame 299 (358.8°)** — platform back at 126.0, travel bar empty. **The cycle
  closes.**
* **crank direction** — the external grip and the internal crank pin both advance
  in the same sense throughout; the platform rises for 0–180° and falls for
  180–360°, which is what the slider-crank requires. No reversal, no jump.
* **platform displacement** — 126.0 → 216.0 → 126.0, i.e. 90 mm, matching the
  measured Phase A travel.
* **linkage continuity** — the rod stays attached at both pins in every frame
  inspected; no body is drawn passing through another.
* **rear panel** — absent from the inset (stated in the inset title), present in
  the main view, which is cut at y = 74 with that stated in the title block.
* **overlay** — legible at 1280 × 720: title block, state banner, a monospaced
  data block (time, crank angle, support-surface z, rod angle, state, payload
  1.0 kg), a travel bar annotated 126 BOTTOM / 216 TOP / 90 mm travel, and the
  standing caveat *CAD KINEMATIC ANIMATION — NOT DYNAMICS. STRUCTURAL STRENGTH /
  USER EFFORT / JAMMING NOT VERIFIED.*
* **scenario payload** — drawn in its own grey, moving rigidly with the platform,
  and named in the data block as a scenario at 1.0 kg. It is never counted as a
  product body.
* **artifacts** — no mesh diagonals, no z-fighting, no back faces bleeding
  through, no popping between frames.

### Claims

**Established.** The declared bodies pass through a complete 0–360° crank cycle;
the external handle rotates and the platform rises and then lowers in response;
the rod changes orientation, reaching 31.97°; the support surface moves between
126.0 and 216.0; no body is drawn passing through another at any inspected frame.

**Not established.** Any force, torque, pressure, stress, strain or deflection;
that a human can turn the crank or with what effort; that the mechanism does not
jam (contact-level, NOT_VERIFIED); that the platform holds position when the crank
is released; that the platform carries 1 kg (UNSUPPORTED); safety,
manufacturability, wear or life.

---

## 2. `validation/review/lift_cad_assembly.mp4`

### Decoded from disk

| property | intended | **read back** |
|---|---|---|
| codec | H.264 (libx264), yuv420p | **h264** |
| resolution | 1280 × 720 | **1280 × 720** |
| fps | 30 | **30.0** |
| frame count | 375 | **375** |
| duration | 12.5 s | **12.5 s** |
| bytes | — | **861 837** |

* output SHA-256 `10efdf10ae35950920ec7567d8a82380832c5bae7487e720afb79fe3a8ef8e78`
* trajectory SHA-256 `7fd9d3b23b2a2bbc8fba49eafd7f0ff6af5ea70def1d812ee6659b31f1ca5320`
  — over (t, step index, insertion offset, crank angle) for every frame.

### Camera

Orthographic, eye (−350, −330, 285), target (20, 76, 112), half-height 158 mm,
**fixed for the whole clip**. Housing and rear panel intersected with y ≤ 74 for
display only.

### State timeline, as recorded and as seen

| t (s) | frame | step | state | bodies placed |
|---|---|---|---|---|
| 0.0 | 0 | 1 | empty housing | 1 |
| 0.9 | 27 | 2 | crank shaft inserted −X | 2 |
| 2.6 | 78 | 3 | connecting rod lowered −Z | 3 |
| 4.0 | 120 | 4 | crank joint pin inserted −X | 4 |
| 5.2 | 156 | 5 | platform lowered into both guides −Z | 5 |
| 6.7 | 201 | 6 | platform joint pin inserted −X | 6 |
| 7.9 | 237 | 7 | open-side cycle check | 6 |
| 9.7 | 291 | 8 | rear panel installed −X | 7 |
| 11.3 | 339 | 9 | completed lift | 7 |

All eleven required beats are present: empty housing; crank shaft from the open
+X side; rod positioned; crank joint pin installed; platform lowered into **both**
guides; platform joint aligned and pinned; open-side cycle check; panel
approaching; **its retention features approaching the pin ends**; panel installed;
completed product.

### Verified by looking at the decoded frames

* **frame 0** — housing alone, +X side and top open.
* **frame 60** — crank shaft translating −X, grip emerging outside the −X wall.
* **frame 140** — crank joint pin travelling −X toward the rod.
* **frame 200** — platform descending, clevis passing either side of the rod.
* **frame 260** — crank turning with the +X side still open (step 7), all six
  internal bodies present and moving together.
* **frame 300 / 320** — rear panel offset along +X with **both retention lands
  clearly visible on its inner face**, the annular land around the crank axis and
  the vertical land above it, with the "insert −X" arrow.
* **frame 374** — panel seated, +X side closed, product complete.
* **overlay** — title block naming the step, a blue **GEOMETRIC ASSEMBLY
  SEQUENCE** banner, a data block (time, step n of 9, bodies placed n of 7, crank
  angle), a standing panel reading *ASSEMBLY FORCE AND MANUFACTURING PROCESS NOT
  VERIFIED — no contact and no force is simulated — this is a prescribed sequence
  of CAD states, not an insertion study*, and the same statement again along the
  bottom.
* **artifacts** — none; same renderer as the operation clip.

### Claims

**Established.** An ordering exists in which each body reaches its seated
position; the crank shaft enters from the open +X side and its grip emerges
outside; the rod and the platform enter vertically through the open top; both
followers enter the two channels before the panel is installed; both joint pins
are installed before the panel closes the side; the panel's two lands arrive
behind the two pin heads in the same motion that seats it.

**Not established.** Insertion force, ease of assembly, tooling or fixturing;
manufacturability; that this sequence is the only possible one; any contact,
friction or deformation — none is modelled.

---

## The two required questions

> **Can a reviewer understand how the crank raises and lowers the platform without
> reading source code?**

**Yes.** The main view carries the exterior handle and the interior linkage
together, so the causal path is visible rather than asserted: at frame 75 the
handle has turned a quarter turn, the crank pin has swung to +Y, the rod leans
31.97°, and the platform has risen to 158.1 — all four readable in one image. By
frame 150 the handle has made half a turn and the platform is at its highest,
216.0. By frame 299 the handle has completed the turn and the platform is back at
126.0. The travel bar makes the position within the 90 mm stroke legible at a
glance, and the fixed inset shows the same mechanism face-on so the geometry of
the linkage is never ambiguous. Nothing in that account requires the source.

> **Can a reviewer understand how the seven product bodies are assembled without
> reading source code?**

**Yes.** Each step names the body being installed, arrows its actual direction,
and shows the count rise from 1 of 7 to 7 of 7. The two things a reader would
otherwise have to take on trust are shown directly: at frame 200 the platform's
followers descend into the channels from their open upper ends, and at frames
300–320 the rear panel's two retention lands are visible on its inner face,
approaching the two pin heads they will capture. The reason the panel is last is
therefore apparent from the pictures alone.

---

## Conclusion

Both clips decode as written, match their manifests exactly, and show what they
claim to show. Both are review evidence for **geometry and prescribed kinematics
only**.

**Human review status: HUMAN_REVIEW_PENDING.**
