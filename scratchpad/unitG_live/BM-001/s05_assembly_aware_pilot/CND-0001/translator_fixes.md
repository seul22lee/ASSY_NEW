# Scratch translator fixes recorded for this experiment

Neither fix alters a number, a position, a shape or any design decision. Both
only let the translator represent what the design already states.

## 1. A generic `wedge` primitive (added before round 1)

The prompt asks for lead-in and hooking faces, which boxes and cylinders cannot
express. A `wedge` — a general right triangular prism — was added to the pilot
geometry language. It is lowered with the **existing** IR opcodes only
(`BOX`, `ROTATE`, `TRANSLATE`, `CUT`); no new compiler capability, no new IR
opcode, and no mechanism-specific primitive. The round-1 design used it once,
for `snap_hook`.

## 2. Vector-valued dimensions read as triples (added during round 1)

The pilot language says a dimension carries one number. The round-1 design also
declared `lid_plate_size` with the value `[100, 60, 6]` and then used that NAME
where a size triple was expected (`"size": ["lid_plate_size"]`).

The translator crashed on it. It now expands a name that resolves to a
three-number dimension into its three components, in place. The meaning is
unambiguous and nothing is changed by reading it that way; such a dimension is
not turned into a Parameter, because it is three numbers rather than one
quantity.

**This is a design-language liberty the model took, not a defect the translator
was fixing in the geometry.**

The same design also **indexes** that dimension inside expressions
(`base_height + lid_plate_size[2]/2`). Indexing is part of the same construct,
so the expression parser now reads `name[i]` as the i-th number the design
already wrote. Nothing is computed, chosen or altered.

## 3. Not a translator fix: a disclosed reference repair

The design declares the dimension `wall_thickness` and refers to it as `wall` in
six geometry expressions. That is a **DeepSeek authoring inconsistency**, not a
translator limitation, and it was repaired in the design text under disclosure —
identifier spelling only, in geometry-expression positions, with prose left
untouched. Every site is listed in `round1_reference_repair.json`, and the
pre-repair design is kept as `round1_design_plan.pre_reference_repair.json`.
