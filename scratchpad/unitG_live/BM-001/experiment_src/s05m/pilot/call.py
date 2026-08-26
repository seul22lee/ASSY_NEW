"""ONE DeepSeek call with the pilot prompt. No retry, no repair round."""
import json, os, sys, time
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ver3.live_providers import env as env_loader
env_loader.load(os.path.join(REPO, "ver3", ".env"))
from ver3.live_providers.deepseek import DeepSeekProvider
from ver3.assy_v3.providers.interfaces import GenerationRequest
import importlib
P = importlib.import_module(os.environ.get('PILOT_PROMPT_MODULE', 'prompt'))

OUT = os.environ.get("PILOT_OUT", os.path.join(
    REPO, "scratchpad", "unitG_live", "BM-001", "s05_fresh_authoring_pilot"))
brief = json.load(open(os.path.join(OUT, "s04_input.json")))
text = P.build(brief)
open(os.path.join(OUT, os.environ.get("PILOT_PROMPT_FILE", "fresh_prompt.txt")), "w").write(text)
print("prompt chars", len(text), flush=True)

provider = DeepSeekProvider(temperature=1.0)
req = GenerationRequest(purpose="pilot: design a physical embodiment", stage_id="s05",
                        prompt_text=text, max_output_tokens=32000, deadline_s=600,
                        temperature=1.0, seed=7, max_attempts=1,
                        run_id="pilot", stage_attempt=1, responsibility_id="s05")
t0 = time.time()
result = provider.generate(req)
raw = result.response.raw_text if result.response else ""
open(os.path.join(OUT, os.environ.get("PILOT_RAW_FILE", "raw_deepseek_response.txt")), "w").write(raw)
print("status", result.execution_status, "| elapsed", round(time.time() - t0, 1),
      "| chars", len(raw), "| truncated",
      getattr(result.response, "truncated", None), flush=True)
try:
    plan = json.loads(raw)
    json.dump(plan, open(os.path.join(OUT, os.environ.get("PILOT_PLAN_FILE", "parsed_design_plan.json")), "w"),
              indent=1, sort_keys=True, default=str)
    print("PARSED OK | keys:", sorted(plan))
    print("bodies:", [(b.get("upstream_body"), len(b.get("elements") or []))
                      for b in plan.get("bodies") or []])
    print("dimensions:", len(plan.get("dimensions") or []),
          "| relationships:", len(plan.get("intended_physical_relationships") or []),
          "| state_expectations:", len(plan.get("state_expectations") or []))
    print("scale_mm_per_unit:", plan.get("scale_mm_per_unit"))
except Exception as exc:
    print("PARSE FAILED:", type(exc).__name__, exc)
