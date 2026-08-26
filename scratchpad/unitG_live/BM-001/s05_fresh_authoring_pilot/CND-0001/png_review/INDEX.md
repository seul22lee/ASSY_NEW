# Round-1 CAD review renders — CND-0001

PNGs rendered **directly from the existing CAD files** in `../cad_round1/`.
Each STEP was read, tessellated as-is and drawn. No geometry was healed,
modified or redesigned, and no design data was regenerated. Transparency is a
drawing property only, so nested parts are visible.

View convention: `isometric` elev 22° / azim −60°; `front` looks along −Y (X–Z);
`side` looks along −X (Y–Z); `top` looks along −Z (X–Y).

In the assembly views the compound's solids are drawn in the order the file
stores them, which is the exporter's sorted body order — blue `BOD-0001` (base),
orange `BOD-0002` (lid), green `BOD-0003` (pin).

## Assembly states

| Source CAD file | PNGs created |
|---|---|
| `../cad_round1/assembly_STA-CFG-0001.step` | `round1_CFG-0001_isometric.png`<br>`round1_CFG-0001_front.png`<br>`round1_CFG-0001_side.png`<br>`round1_CFG-0001_top.png` |
| `../cad_round1/assembly_STA-CFG-0002.step` | `round1_CFG-0002_isometric.png`<br>`round1_CFG-0002_front.png`<br>`round1_CFG-0002_side.png`<br>`round1_CFG-0002_top.png` |

## Individual bodies

| Source CAD file | PNG created |
|---|---|
| `../cad_round1/BOD-0001.step` | `round1_BOD-0001_isometric.png` |
| `../cad_round1/BOD-0002.step` | `round1_BOD-0002_isometric.png` |
| `../cad_round1/BOD-0003.step` | `round1_BOD-0003_isometric.png` |

## Source files present but not rendered from

These hold the same geometry as the STEP files above and were left unused:

- `../cad_round1/BOD-0001.brep`, `BOD-0002.brep`, `BOD-0003.brep`
- `../cad_round1/BOD-0001.stl`, `BOD-0002.stl`, `BOD-0003.stl`

**11 PNGs created from 5 source STEP files.**
