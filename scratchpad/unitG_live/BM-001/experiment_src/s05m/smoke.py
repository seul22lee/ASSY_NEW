"""HARNESS SMOKE TEST - not the proof. A deterministic builder stands in for
the provider so the S05->S06->S07 plumbing is exercised without a live call."""
import json, os, sys, time
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from ver3.assy_v3.providers.interfaces import (GenerationResponse, GenerationResult,
                                               ProviderCapabilities)
from ver3.assy_v3.stages.base import ExecutionStatus
from ver3.tests.meta import _s05_semantic as S


class Builder:
    """Answers from the prompt's own DUTIES by re-deriving them from state."""

    def __init__(self, state, cid):
        self.state, self.cid, self.records, self.calls = state, cid, [], 0

    def capabilities(self):
        return ProviderCapabilities(provider_id="deterministic-builder", model_id="none",
                                    context_window_tokens=None, max_output_tokens=None,
                                    supports_structured_output=True, supports_seed=True,
                                    requests_per_minute=None, tokens_per_minute=None,
                                    daily_quota_requests=None, notes="harness smoke test")

    def generate(self, request, attempt_index=0):
        self.calls += 1
        view = S.view_of(self.state, self.cid)
        payload = S.minimal_response(view)
        return GenerationResult(
            execution_status=ExecutionStatus.SUCCESS,
            response=GenerationResponse(raw_text=json.dumps(payload), finish_reason="stop",
                                        truncated=False, input_tokens=None,
                                        output_tokens=None, served_model_id="none"),
            attempt_index=attempt_index, started_at=time.time(), ended_at=time.time(),
            from_cache=True)


class Late:
    """The provider is constructed against the state the harness builds, so it
    has to be bound after `run_candidate` starts. This proxy does that."""

    def __init__(self):
        self.inner = None

    def bind(self, state, cid):
        self.inner = Builder(state, cid)

    def capabilities(self):
        return self.inner.capabilities()

    def generate(self, request, attempt_index=0):
        return self.inner.generate(request, attempt_index)

    @property
    def records(self):
        return self.inner.records if self.inner else []


CID = sys.argv[1] if len(sys.argv) > 1 else "CND-0004"
OUT = "/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad/s05m/smoke_out"

# run_candidate builds the state itself; bind the builder by monkey-patching the
# provider's state the moment the stage asks for a completion.
proxy = Late()
_orig_build = harness.build
_captured = {}


def capturing_build():
    state = _orig_build()
    _captured["state"] = state
    proxy.bind(state, CID)
    return state


harness.build = capturing_build
row, state = harness.run_candidate(CID, proxy, OUT)
print(json.dumps(row, indent=1, default=str)[:4000])
