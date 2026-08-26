"""The assembly-aware pilot prompt.

It asks for a mechanism that can be MADE and ASSEMBLED, not a set of solids
that happen to correspond to features. It names no mechanism family, carries no
template and contains no candidate-specific geometry or dimension: every
requirement below is a property any assembled mechanism must have.
"""
import json

PROMPT = """You are a mechanical designer. You are given a SPATIAL AND KINEMATIC
DESIGN that has already been decided: which bodies exist, how they are jointed,
what they must touch, what positions they must reach, what space must stay open,
in what order they are put together, and how big the whole thing roughly is.

Design the ACTUAL PARTS: a physically manufacturable AND assemblable mechanism
whose real geometry realizes that design.

This is not "make a box or a cylinder for each feature". A mechanism is only
real if the parts can be made, brought together, and then move as declared.

WHAT YOU MUST WORK OUT BEFORE YOU ANSWER

Picture the finished object, then picture someone assembling it.

  MANUFACTURABLE PARTS
  - Every body must come out as ONE connected part. Material you add must touch
    the rest of its own body - nothing floating alongside it. Material you
    remove must not accidentally cut a body into two pieces.
  - An envelope is a bound, not a solid. Build the part you would actually make
    inside that bound: walls, floors, ribs, bosses - not a filled block.

  PARTS THAT ACTUALLY MEET
  - Where the design says two bodies touch in a state, their surfaces must
    really meet there - seated on each other, not floating apart and not
    overlapping.
  - No required relationship may be satisfied by a NAME or by a sentence. If
    two things are meant to engage, the geometry has to put them in the same
    place, at the same size, facing each other.

  JOINTS THAT ARE REALLY BUILT
  - A rotating joint is not built by separately naming a barrel, a bore and a
    pin. The whole joint has to exist: material on EACH body that carries the
    joint, bores through them that are genuinely COAXIAL - same axis line, same
    diameter class - and a shaft or pin long enough to actually pass through
    the parts it joins, with running clearance so it can still turn afterwards.
  - Whatever you build must leave the declared motion possible over its whole
    range, not only at the two ends.

  A THING THAT CAN BE PUT TOGETHER
  - Decide the real order of assembly: what goes on what, from which direction,
    through which opening.
  - If a part has to be inserted, there must be a clear path for it to travel
    along and room for a hand or a tool to reach it. A pin cannot be inserted
    through solid material, and it cannot appear inside a closed cavity.
  - Say what stops an inserted part from simply falling back out.
  - Interleaving parts (for instance alternating projections that must pass
    each other) only works if the gaps and the projections actually match.

  A LATCH OR RETAINER THAT REALLY LATCHES
  - Where the design calls for something to be held or released, the geometry
    must do the holding. A flexible catch needs: a root that is CONNECTED to
    its own body, a member slender enough to bend, a real projection that
    hooks, a matching recess or ledge on the other body for it to hook into, a
    sloped or rounded lead-in so it can be pushed into engagement, EMPTY SPACE
    behind or beside it for it to deflect into, and a way to release it.
  - It must be engaged in the state where the design says it holds, and clear
    of its catch in the state where the design says the parts move.

  TWO STATES, ONE MECHANISM
  - The required states are two poses of ONE assembled thing. Everything that is
    joined stays joined in both. If a part is only plausible in one of them,
    the design is wrong.

  SPACE THAT MUST STAY EMPTY
  - Where the design reserves a volume to be reached into or passed through,
    your material must genuinely not be there.

Then design the parts so that all of that is true, and say so in the answer.

SIZES ARE YOURS. The arrangement is in relative units: choose a real size and
say how many millimetres one unit is (`scale_mm_per_unit`). Then work in
MILLIMETRES with ordinary engineering values. Give real numbers. Use a
`relation` only where two dimensions genuinely have to stay tied together - a
shaft and the bore it turns in, a projection and the recess it enters.

COORDINATES. Every `at` is the CENTRE of that piece of material, in millimetres,
in the assembly frame below, with every joint at coordinate zero.

WHAT YOU MAY BUILD WITH. Boxes, cylinders and wedges, added or subtracted. A
wedge is a right triangular prism - use it for a lead-in ramp or a hooking
face. A part is made by adding several pieces and subtracting the spaces that
are not material.

ANSWER WITH ONE JSON OBJECT, exactly this shape:

{{
  "design_summary": "<what each part is, how it is assembled, and how it works>",
  "scale_mm_per_unit": <number>,

  "dimensions": [
    {{"name": "<short name>", "value": <number>, "unit": "mm", "why": "<why>"}},
    {{"name": "<short name>", "relation": "<name> + <number>", "unit": "mm",
      "why": "<why these must stay tied>"}}
  ],

  "bodies": [
    {{"upstream_body": "<Body id>",
      "summary": "<what this part is>",
      "elements": [
        {{"op": "add", "shape": "box", "name": "<name>",
          "size": [<x>, <y>, <z>], "at": [<x>, <y>, <z>]}},
        {{"op": "subtract", "shape": "cylinder", "name": "<name>",
          "radius": <r>, "height": <h>, "at": [<x>, <y>, <z>], "axis": "+X|+Y|+Z",
          "clears": "<FunctionalRegion id, only if this opens that space>"}},
        {{"op": "add", "shape": "wedge", "name": "<name>",
          "size": [<x>, <y>, <z>], "at": [<x>, <y>, <z>],
          "slope": "+X|-X|+Y|-Y|+Z|-Z"}}
      ]}}
  ],

  "mating_sets": [
    {{"name": "<what this joint or engagement is>",
      "upstream_relationships": ["<Interface / Joint / ConstraintRelation ids>"],
      "participants": [{{"body": "<Body id>", "element": "<element name>",
                        "role": "<what this piece does in this set>"}}],
      "purpose": "<what the set achieves mechanically>",
      "fit": "<the intended fit or clearance, as a dimension name or mm value>",
      "motion_after_assembly": "<what may still move once assembled, and how far>"}}
  ],

  "assembly_sequence": [
    {{"step": <n>,
      "component": "<Body id>",
      "action": "<what is done>",
      "insertion_direction": [<x>, <y>, <z>],
      "access": "<the opening or face it goes in through>",
      "final_retention": "<what holds it once it is there>"}}
  ],

  "state_expectations": [
    {{"state": "<State id>",
      "touching": "<what is in contact>",
      "engaged": "<what is holding what>",
      "free": "<what is clear, and what can still move>",
      "still_assembled": "<what remains joined in this state>"}}
  ]
}}

Every `size`, `at`, `radius`, `height` may instead be the NAME of one of your
`dimensions`.

A MATING SET IS THE WHOLE ENGAGEMENT. Put every participant of one joint in ONE
mating set - both sides' material and the part that joins them - not as separate
unrelated entries. Do the same for a catch: the flexible member, its hook, the
recess it enters and the lead-in belong to one set.

THE DECIDED SPATIAL AND KINEMATIC DESIGN
========================================
{design}
"""


def build(brief: dict) -> str:
    return PROMPT.format(design=json.dumps(brief, indent=1, sort_keys=True, default=str))
