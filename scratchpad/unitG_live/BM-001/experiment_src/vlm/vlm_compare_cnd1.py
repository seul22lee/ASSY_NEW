"""DeepSeek-VL2 compares CND-0001 round-1 and round-2 compiled CAD."""
import os, sys
S = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, S)
import vlm_review as V
PROMPT = """These images show two versions of the SAME mechanical assembly, rendered
from solid geometry.

- blue is the stationary base, orange is the moving lid, green is a hinge pin
- it is meant to be one coherent hinged closure with a latch
- the lid turns about the hinge between two required states
- the FIRST FOUR images are VERSION 1: lid closed, then lid open
- the LAST FOUR images are VERSION 2: the same two states after a redesign

Compare these two versions visually:
- body coherence
- hinge continuity
- physical connection between base, lid and pin
- plausible rotation between the states
- latch and retention coherence
- detached or floating geometry
- whether version 2 looks more like one manufacturable mechanical assembly

Do not give dimensions or coordinates. Do not redesign anything.
"""
if __name__ == "__main__":
    names = ["round1_CFG-0001_isometric.png", "round1_CFG-0001_side.png",
             "round1_CFG-0002_isometric.png", "round1_CFG-0002_side.png",
             "round2_CFG-0001_isometric.png", "round2_CFG-0001_side.png",
             "round2_CFG-0002_isometric.png", "round2_CFG-0002_side.png"]
    images = [os.path.join(V.PILOT, n) for n in names]
    for p in images: assert os.path.exists(p), p
    print("model:", V.MODEL, "| images:", len(images), flush=True)
    V.run(images, PROMPT, os.path.join(V.PILOT, "deepseek_vlm_round2_comparison.md"))
