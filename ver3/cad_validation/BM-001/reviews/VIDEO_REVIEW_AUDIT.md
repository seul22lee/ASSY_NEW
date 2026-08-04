# BM-001 — video review audit

**Status: `AUTHOR_SELF_REVIEW` — `HUMAN_REVIEW_PENDING`.**

Three review videos exist. Every one was **decoded from its own MP4 file** and
looked at — not judged from the frames that went into the encoder, and not
inferred from the manifest. This file records what was seen.

| Video | Reference | File |
|---|---|---|
| `VID-BM001-01-LID` | EXE-BM001-01 | [lid_operation.mp4](../executable_references/EXE-BM001-01/validation/simulation/lid_operation.mp4) · [.gif](../executable_references/EXE-BM001-01/validation/simulation/lid_operation.gif) |
| `VID-BM001-02-OPERATION` | EXE-BM001-02 | [cover_operation.mp4](../executable_references/EXE-BM001-02/validation/simulation/cover_operation.mp4) |
| `VID-BM001-02-ASSEMBLY` | EXE-BM001-02 | [cover_snap_assembly.mp4](../executable_references/EXE-BM001-02/validation/simulation/cover_snap_assembly.mp4) |

Full per-video records — engine and versions, source geometry signature, fps,
resolution, frame count, duration, codec, camera definition, state timeline,
trajectory hash, output SHA-256, assumptions, and what each does and does not
establish — are in
[lid_operation_video.json](../executable_references/EXE-BM001-01/validation/simulation/lid_operation_video.json)
and
[cover_videos.json](../executable_references/EXE-BM001-02/validation/simulation/cover_videos.json).

## What was verified, per video

| | LID | COVER OPERATION | COVER ASSEMBLY |
|---|---|---|---|
| declared frames | 286 | 301 | 271 |
| frames decoded back from the file | **286** | **301** | **271** |
| duration | 9.53 s | 10.03 s | 9.03 s |
| fps / resolution / codec | 30 / 1280×720 / h264 | 30 / 1280×720 / h264 | 30 / 1280×720 / h264 |
| container read-back agrees | yes | yes | yes |
| source geometry signature | `f2bc9599cdd6832d…` | `1eba7a573b5787ba…` | `1eba7a573b5787ba…` |
| camera | fixed, fitted once to the whole sweep | fixed, plus one fixed detail inset | fixed |

## The confirmations this gate requires

**Can the mechanism be understood without reading code?** **YES**, for all three.

- *Lid*: the box opens, holds and closes; the overlay names the phase and gives
  the angle and both torques at every instant. Nothing about it needs a source
  file to interpret.
- *Cover operation*: closed → press → slide → full open → slide back → snapped.
  The heavy arrows give the direction; the inset gives the latch.
- *Cover assembly*: aligned → tabs in → down past the lips → ears out → captive,
  with the span-versus-gap numbers on screen as it happens.

**Does any body appear disconnected?** **No.** Each body is one shaded solid with
its own colour and its own outline. In the lid clip the interleaved knuckles read
as alternating bands of enclosure and closure around a continuous pin, which is
what they are. In the cover clips the four tabs and the latch finger are the same
tan solid as the plate they belong to, with no seam between them.

**Is the movement direction obvious?** **Yes.** The lid sweeps through 110° in the
frame. The cover translates visibly along the rails with `SLIDE OPEN (−X)` and
`SLIDE CLOSED (+X)` arrows drawn from projected model points, so they track the
geometry rather than sitting at guessed screen positions.

**Is the latch release causally visible?** **Yes — this was checked deliberately.**
The main view alone would not have shown it: a 2.6 mm sideways shift on a 190 mm
product is about 1% of the frame. A second **fixed** camera looks straight down at
the latch. Comparing the closed and pressed frames of that inset, the tooth sits
directly behind the keeper strip when closed and is clear of it when the pad is
pushed, and the keeper strip becomes fully exposed. The release and the clearance
are one continuous solid moving together.

**Does EXE-BM001-02 remain captive at full open?** **Yes.** The full-open segment
is banner-labelled `FULL OPEN 84 mm — STILL CAPTIVE`, the 84 mm is drawn across
the aperture that is actually open, and the overlay states on every frame that
the tabs are under both rail lips. The geometric backing is the validator's own
captivity probe, not the picture.

**Do the first and final frames match the declared states?**

| Video | first frame | final frame |
|---|---|---|
| LID | t = 0.00 s, angle 0.00° — CLOSED | t = 9.50 s, angle 0.00° — CLOSED |
| COVER OPERATION | t = 0.00 s, slide 0.0 mm, latch 0.00 mm — CLOSED, LATCH ENGAGED | t = 10.00 s, slide 0.0 mm, latch 0.00 mm — SNAP RE-ENGAGED, the same pose |
| COVER ASSEMBLY | t = 0.00 s, 26.0 mm above the seat, tabs relaxed — ASSEMBLY ALIGNED | t = 9.00 s, seated, tabs relaxed, ears under the lips — CAPTIVE ASSEMBLY |

Checked by decoding the first and last frames from each file and reading the
overlay, not by trusting the generator.

## Rendering, and what was rejected on the way

The first renderer used a painter's-algorithm depth sort. It was **discarded**:
a large far wall has a nearer centroid than a small near feature, so back faces
bled through and the result read as a transparent wireframe — the exact thing
these clips are required not to be. It was replaced with a real z-buffer, and
the face rims are depth-tested against that buffer so hidden edges stay hidden.

Shading is per B-rep face: the triangles carry the shading and are drawn with no
edge stroke at all, and only each face's own rim is stroked. **No mesh diagonal
appears anywhere in any frame**, because no triangle edge is ever drawn.

No coordinate axes, no wireframe overlay, no transparency. The assembly clip is
sectioned at X = 118 mm, stated on every frame of it: a rail lip is precisely
what hides the thing it retains, so there is no un-sectioned view in which the
tab-under-lip relation can be seen at all.

## What none of these videos establish

Nothing about force. Not snap-in force, pull-out capacity, retention strength,
latch release effort, material strain, root stress, creep, fatigue, cycle life,
wear, impact resistance, tolerance robustness, moulding feasibility or cost.

The lid clip's torques are computed by MuJoCo under an **assumed density
(1200 kg/m³) and zero friction**, stated on every frame. They are a lower bound
on the effort a real hinge would need, not a measurement, and the source states
no effort ceiling for them to pass or fail against.

The two cover clips compute nothing at all. Their motion is prescribed, their
pacing is arbitrary and carries no meaning, and the compliant states in them are
`DECLARED_KINEMATIC_APPROXIMATION`s — rigid translations of a declared region
that conserve volume exactly and model no strain. The assembly clip says
`GEOMETRIC COMPLIANT-STATE REPRESENTATION / FORCE / STRAIN NOT VERIFIED` on every
frame.

A video is the weakest form of evidence in this pilot. It can show that declared
geometry reaches declared states without passing through itself; every number it
displays comes from a measurement made elsewhere, and none of the geometric
claims in either reference rests on one.
