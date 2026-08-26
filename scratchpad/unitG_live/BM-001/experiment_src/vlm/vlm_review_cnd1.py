"""DeepSeek-VL2 looks at the actual CND-0001 round-1 S07 renders.

The intent below is derived only from the real standing S04/S03 state of this
candidate. No numerical diagnostics, no defect list, no repair advice, and
nothing from any other candidate's experiment.
"""
import os, sys
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import vlm_review as V

PILOT = V.PILOT
INTENT = """You are inspecting rendered CAD of a mechanical assembly.

The only things you are told about the design intent:
- blue is BOD-0001, the stationary base
- orange is BOD-0002, the moving lid
- green is BOD-0003, a hinge pin
- it is meant to be ONE coherent hinged closure: a box base, a lid that turns on
  the pin, and a latch that holds the lid shut
- the lid's motion is a rotation about the hinge
- the first two images are one required state (lid closed)
- the last two images are the other required state (lid open)
- the bodies must stay mechanically connected and guided through that rotation

The solids are drawn semi-transparently so nested parts can be seen.

Judging ONLY what you can see, report visually observable problems:
- pieces that are floating or detached from the body they belong to
- a hinge connection that does not look physical
- a lid that does not appear to turn about a coherent hinge
- pin, knuckle, lid and base geometry that look misaligned with each other
- latch geometry that looks unrelated to what it should engage
- the closed and open pictures not looking like the same mechanism
- anything obviously blocking or nonsensical

Do not give dimensions, coordinates or numbers. Do not redesign it.

Answer in three parts:
1. the major visible mechanical problems
2. why each one makes the mechanism visually implausible
3. what physical relationship should instead be true, described qualitatively
"""

if __name__ == "__main__":
    names = ["round1_CFG-0001_isometric.png", "round1_CFG-0001_side.png",
             "round1_CFG-0002_isometric.png", "round1_CFG-0002_side.png"]
    images = [os.path.join(PILOT, n) for n in names]
    for p in images:
        assert os.path.exists(p), p
    print("model:", V.MODEL, "| images:", len(images), flush=True)
    V.run(images, INTENT, os.path.join(PILOT, "deepseek_vlm_round1_review.md"))
