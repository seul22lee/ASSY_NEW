"""DeepSeek-VL2 looks at the actual round-1 S07 renders.

The four PNGs are the compiled B-reps. The prompt carries ONLY the minimal
mechanical intent the experiment specified: which colour is which body, that it
is meant to be a housing with a moving member, that the motion is one prismatic
translation, which state is which end, and that the moving body should stay
guided. No diagnosis, no measurements, no defect list and no repair advice is
supplied by the orchestrator.
"""
import os, sys, torch
S = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("HF_HOME", os.path.join(S, "hf"))
sys.path.insert(0, S)
sys.path.insert(0, os.path.join(S, "DeepSeek-VL2"))
import dsvl2_compat
for _n in dsvl2_compat.apply():
    print("shim:", _n, flush=True)
from transformers import AutoModelForCausalLM
from deepseek_vl2.models import DeepseekVLV2ForCausalLM, DeepseekVLV2Processor
for _n in dsvl2_compat.apply_cache() + dsvl2_compat.apply_generation():
    print("shim:", _n, flush=True)
import PIL.Image

MODEL = os.environ.get("DSVL2_MODEL", "deepseek-ai/deepseek-vl2-tiny")
PILOT = os.environ.get(
    "PILOT_OUT",
    "/home/ftk3187/github/ASSY_Ver3.0/scratchpad/unitG_live/BM-001/"
    "s05_fresh_authoring_pilot")

INTENT = """You are inspecting rendered CAD of a mechanical assembly.

The only things you are told about the design intent:
- blue is the stationary body BOD-0012
- orange is the moving body BOD-0013
- it is meant to be a stationary housing with a drawer / storage body
- the relative motion is one prismatic (straight sliding) translation
- the first two images are one end state of that motion (CFG-0008)
- the last two images are the other end state (CFG-0009)
- the moving body should stay mechanically guided by the stationary body while
  it travels between those two states

The solids are drawn semi-transparently so nested parts can be seen.

Inspect this as a mechanical designer, judging ONLY what you can see:
Does it look like one coherent housing-and-moving-member mechanism? Are parts
that should be connected visibly connected? Does the moving member appear
captured and guided by the housing? Do the guide and contact features appear
mutually aligned? Does the open state look like the mechanism in another pose,
or like solids that have simply been separated? Are there floating, detached,
misplaced, wrongly oriented, blocking or nonsensical pieces? Does the closed
state look assemblable?

Do not calculate dimensions. Do not give coordinates or numbers. Do not
redesign it.

Answer in three parts:
1. the major visible mechanical problems
2. why each one makes the mechanism visually implausible
3. what physical relationship should instead be true, described qualitatively
"""


def run(images, prompt, out_path, max_new_tokens=1200):
    processor = DeepseekVLV2Processor.from_pretrained(MODEL)
    tokenizer = processor.tokenizer
    model = AutoModelForCausalLM.from_pretrained(MODEL, trust_remote_code=True)
    model = model.to(torch.bfloat16).cuda().eval()
    placeholders = "".join("<image>\n" for _ in images)
    conversation = [{"role": "<|User|>", "content": placeholders + prompt,
                     "images": list(images)},
                    {"role": "<|Assistant|>", "content": ""}]
    pil = [PIL.Image.open(p).convert("RGB") for p in images]
    inputs = processor(conversations=conversation, images=pil, force_batchify=True,
                       system_prompt="").to(model.device)
    embeds = model.prepare_inputs_embeds(**inputs)
    with torch.no_grad():
        out = model.language.generate(
            inputs_embeds=embeds, attention_mask=inputs.attention_mask,
            pad_token_id=tokenizer.eos_token_id, bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id, max_new_tokens=max_new_tokens,
            do_sample=False, use_cache=True)
    text = tokenizer.decode(out[0].cpu().tolist(), skip_special_tokens=True)
    with open(out_path, "w") as fh:
        fh.write(text)
    print("=" * 70); print(text); print("=" * 70)
    print("saved:", out_path, "| chars", len(text))
    return text


if __name__ == "__main__":
    images = [os.path.join(PILOT, n) for n in
              ("cfg0008_isometric.png", "cfg0008_side.png",
               "cfg0009_isometric.png", "cfg0009_side.png")]
    for p in images:
        assert os.path.exists(p), p
    print("model:", MODEL, "| images:", len(images), flush=True)
    run(images, INTENT, os.path.join(PILOT, "deepseek_vlm_round1_review.md"))
