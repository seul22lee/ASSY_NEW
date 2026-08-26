"""DeepSeek-VL2 compares round-1 and round-2 compiled CAD. Observation only."""
import os, sys
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import vlm_review as V

PILOT = V.PILOT
PROMPT = """These images show two versions of the SAME mechanical assembly, rendered
from solid geometry.

- blue is the stationary body, orange is the moving body
- it is meant to be a stationary housing with a drawer / storage body
- the motion is one prismatic (straight sliding) translation
- the FIRST FOUR images are VERSION 1: its closed state then its open state
- the LAST FOUR images are VERSION 2: the same two states after a redesign

Compare these two versions as mechanical assemblies.

Did version 2 materially improve:
- body coherence;
- connection of previously detached or floating geometry;
- guide and mating alignment;
- mechanical capture and support of the moving body;
- plausibility of the closed state;
- plausibility of the open state;
- visual continuity of the mechanism across the motion?

What major visible mechanical defects remain?

Do not calculate dimensions. Do not propose another redesign.
"""

if __name__ == "__main__":
    names = ["cfg0008_isometric.png", "cfg0008_side.png",
             "cfg0009_isometric.png", "cfg0009_side.png",
             "round2_CFG-0008_isometric.png", "round2_CFG-0008_side.png",
             "round2_CFG-0009_isometric.png", "round2_CFG-0009_side.png"]
    images = [os.path.join(PILOT, n) for n in names]
    for p in images:
        assert os.path.exists(p), p
    print("model:", V.MODEL, "| images:", len(images), flush=True)
    V.run(images, PROMPT, os.path.join(PILOT, "vlm_round2_comparison.md"))
