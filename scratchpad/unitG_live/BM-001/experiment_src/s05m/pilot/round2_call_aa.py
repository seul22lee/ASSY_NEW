"""ONE DeepSeek revision call: S04 (unchanged) + round-1 plan + verbatim VLM review.

The orchestrator contributes no diagnosis and no repair advice. The only new
evidence in this prompt is DeepSeek-VL2's own visual review, pasted verbatim.
"""
import json, os, sys, time
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ver3.live_providers import env as env_loader
env_loader.load(os.path.join(REPO, "ver3", ".env"))
from ver3.live_providers.deepseek import DeepSeekProvider
from ver3.assy_v3.providers.interfaces import GenerationRequest
import prompt_assembly as P

OUT = os.environ.get("PILOT_OUT", os.path.join(
    REPO, "scratchpad", "unitG_live", "BM-001", "s05_assembly_aware_pilot", "CND-0001"))
brief = json.load(open(os.path.join(OUT, "s04_input.json")))
plan = open(os.path.join(OUT, os.environ.get("PILOT_R1_RAW",
                                              "round1_raw_deepseek_response.txt"))).read()
review = open(os.path.join(OUT, "deepseek_vlm_round1_review.md")).read()

# the SAME output language as round 1, taken from the round-1 template itself
schema = P.PROMPT.split("ANSWER WITH ONE JSON OBJECT")[1].split(
    "THE DECIDED SPATIAL AND KINEMATIC DESIGN")[0]

HEADER = """Your first physical embodiment was compiled and rendered.
A visual mechanical review found that the resulting assembly does not form a
coherent working mechanism.

Revise the PHYSICAL DESIGN, not merely the wording and not merely individual
fields.

Treat the review observations as evidence about the resulting complete object.
Re-picture the complete assembly before writing the replacement design.

Preserve all upstream decisions from the design below:
- bodies;
- joint identity, type and motion;
- which body is stationary and which moves;
- the required states;
- the required interfaces and interactions;
- the functional regions;
- the required assembly intent, the mating sets and the assembly sequence.

You may completely replace your previous body construction, dimensions, element
positions, guide geometry, openings and stop geometry where needed.

The revised result must visually make sense as ONE manufactured mechanism:
- each body must itself look like one coherent manufactured part;
- features belonging to one body must actually form that body rather than float
  separately;
- mating features must visibly meet or fit as intended;
- the moving body must remain guided and captured during the required motion;
- the stationary body must physically contain and support the guide system;
- required openings and free space must exist physically;
- end-state restraints must arise from plausible physical geometry;
- the second state must visibly be the same assembly after the declared motion;
- every mating set you declare must be geometrically real: the mating features
  must actually occupy the same place and fit each other, not merely be named;
- the assembly sequence you declare must be physically performable in that order.

Do not patch the review comments one by one. Replace the design holistically if
necessary.

Choose reasonable nominal dimensions yourself. Do not leave unnecessary unknown
dimensions for a later solver.

Return a COMPLETE replacement plan, not a delta, in the SAME schema you used
before.

ANSWER WITH ONE JSON OBJECT{schema}
THE VISUAL REVIEW OF YOUR COMPILED DESIGN
=========================================
{review}

YOUR PREVIOUS DESIGN, IN FULL
=============================
{plan}

THE DECIDED SPATIAL AND KINEMATIC DESIGN (UNCHANGED)
====================================================
{design}
"""

text = HEADER.format(schema=schema, review=review, plan=plan,
                     design=json.dumps(brief, indent=1, sort_keys=True, default=str))
open(os.path.join(OUT, "round2_prompt.txt"), "w").write(text)
print("prompt chars", len(text), flush=True)

provider = DeepSeekProvider(temperature=1.0)
req = GenerationRequest(purpose="pilot round 2: revise the physical embodiment",
                        stage_id="s05", prompt_text=text, max_output_tokens=32000,
                        deadline_s=900, temperature=1.0, seed=7, max_attempts=1,
                        run_id="pilot-r2", stage_attempt=1, responsibility_id="s05")
t0 = time.time()
result = provider.generate(req)
raw = result.response.raw_text if result.response else ""
open(os.path.join(OUT, "round2_raw_deepseek_response.txt"), "w").write(raw)
print("status", result.execution_status, "| elapsed", round(time.time() - t0, 1),
      "| chars", len(raw), "| truncated", getattr(result.response, "truncated", None),
      flush=True)
