"""The pilot prompt. Written from zero: a CAD design task, not a bookkeeping task.

It contains no candidate id, no mechanism family and no per-duty rule. The
design considerations are questions about the finished object, which is what a
designer asks; the schema is small enough to author in one pass.
"""
import json

PROMPT = """You are a mechanical designer. You are given a SPATIAL AND KINEMATIC
DESIGN that has already been decided: which bodies exist, how they are jointed,
what they must touch, what positions they must reach, what space must stay
open, and how big the whole thing roughly is.

Your job is to DESIGN THE ACTUAL PARTS. Produce a physical embodiment that a
machinist or a moulder could make and that would work as a mechanism.

You are NOT writing a data structure for a pipeline. You are designing objects.

HOW TO THINK BEFORE YOU ANSWER

Picture the finished assembly and answer these for yourself first:

  - What material does each body actually contain? A real part is walls, ribs,
    plates, bosses and lugs - not a solid block the size of its bounding box.
  - What spaces must remain empty, and is each of them actually empty in your
    design? Something has to reach in, pass through, or move there.
  - How do the bodies physically mate? Which surface of one part meets which
    surface of the other, and with what fit?
  - What geometry actually permits the declared joint motion? A sliding pair
    needs a channel and something that runs in it; a turning pair needs a round
    feature in a round hole.
  - What geometry provides each declared restraint or contact? Something has to
    be in the way for a motion to be blocked, and it has to be in the way AT THE
    POSITION where the design says it is blocked.
  - What physically changes between the required positions? If a part is at one
    coordinate in one state and a different coordinate in another, the geometry
    that limits it at each end cannot be the same material in the same place.
  - Is the required travel physically open along its whole length? Nothing of
    the other parts may be standing in the swept path.
  - Can the parts plausibly be assembled in the stated order and direction?

Then design the parts so that the answers are yes.

THE ENVELOPES ARE BOUNDS, NOT MATERIAL. An envelope is the space a body may not
exceed. It is not a solid and you must not model a body as its envelope filled
in. Build the part you would actually manufacture inside that bound.

SIZES ARE YOURS TO CHOOSE. The arrangement below is stated in relative units.
Pick a sensible real size for the mechanism and say how many millimetres one
arrangement unit is (`scale_mm_per_unit`). After that, work in MILLIMETRES and
choose ordinary engineering values: a wall thickness, a clearance, a radius.
Give real numbers. Do not leave dimensions unknown for someone else to solve -
only write a `relation` where two dimensions genuinely have to stay tied
together (a shaft and the hole it runs in, a channel and the rib inside it).

COORDINATES. Every `at` is the CENTRE of that piece of material, in millimetres,
in the assembly frame shown below, with every joint at coordinate zero. The
frame origin and the axes are the ones the arrangement below is stated in.

WHAT YOU MAY BUILD WITH. Boxes and cylinders, added or subtracted, is the whole
vocabulary. A part is made by adding several pieces and subtracting the spaces
that are not material. Subtract to make a cavity, a slot, a channel, a bore or
an opening.

ANSWER WITH ONE JSON OBJECT, exactly this shape:

{{
  "design_summary": "<a short paragraph: what each part is and how the mechanism works>",
  "scale_mm_per_unit": <number>,

  "dimensions": [
    {{"name": "<short name>", "value": <number>, "unit": "mm",
      "why": "<why this value>"}},
    {{"name": "<short name>", "relation": "<name> + <name> * <number>", "unit": "mm",
      "why": "<why these two must stay tied>"}}
  ],

  "bodies": [
    {{"upstream_body": "<Body id from the design below>",
      "summary": "<what this part is, in a sentence>",
      "elements": [
        {{"op": "add", "shape": "box", "name": "<short name>",
          "size": [<x>, <y>, <z>], "at": [<x>, <y>, <z>]}},
        {{"op": "subtract", "shape": "box", "name": "<short name>",
          "size": [<x>, <y>, <z>], "at": [<x>, <y>, <z>],
          "clears": "<FunctionalRegion id, only if this is what opens that space>"}},
        {{"op": "add", "shape": "cylinder", "name": "<short name>",
          "radius": <r>, "height": <h>, "at": [<x>, <y>, <z>], "axis": "+X|+Y|+Z"}},
        {{"op": "subtract", "shape": "cylinder", "name": "<short name>",
          "radius": <r>, "height": <h>, "at": [<x>, <y>, <z>], "axis": "+X|+Y|+Z"}}
      ]}}
  ],

  "intended_physical_relationships": [
    {{"upstream": "<Interface / Joint / ConstraintRelation id this realizes>",
      "a": "<Body id>/<element name>",
      "b": "<Body id>/<element name>",
      "purpose": "<what this pairing does mechanically>",
      "clearance": "<a dimension name or a number in mm, where a gap or a fit is meant>"}}
  ],

  "state_expectations": [
    {{"state": "<State id>",
      "expect": "<what is engaged, what is clear, what is touching, at this position>"}}
  ]
}}

Every `size`, `at`, `radius` and `height` number may instead be the NAME of one
of your `dimensions`. Use names where a number matters in more than one place.

Name every element you refer to in `intended_physical_relationships`. Every
declared interface, joint and restraint in the design below should appear there
with the actual geometry that realizes it.

THE DECIDED SPATIAL AND KINEMATIC DESIGN
========================================
{design}
"""


def build(brief: dict) -> str:
    return PROMPT.format(design=json.dumps(brief, indent=1, sort_keys=True, default=str))
