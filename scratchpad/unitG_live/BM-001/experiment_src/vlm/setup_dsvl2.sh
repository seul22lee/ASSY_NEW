set -e
source /home/ftk3187/miniconda3/etc/profile.d/conda.sh
S=/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad
export HF_HOME=$S/hf
echo "=== create env ==="
conda create -y -n dsvl2 python=3.10 >/dev/null 2>&1 || echo "env exists"
conda activate dsvl2
python -V
echo "=== torch + xformers (matched pair, cu121) ==="
pip install -q --index-url https://download.pytorch.org/whl/cu121 torch==2.5.1 torchvision==0.20.1 2>&1 | tail -3
pip install -q --index-url https://download.pytorch.org/whl/cu121 xformers==0.0.28.post3 2>&1 | tail -3
echo "=== deepseek-vl2 deps ==="
pip install -q "transformers==4.38.2" "timm>=0.9.16" einops sentencepiece accelerate attrdict3 pillow huggingface_hub 2>&1 | tail -5
echo "=== official package, no deps ==="
pip install -q -e $S/DeepSeek-VL2 --no-deps 2>&1 | tail -3
echo "=== verify ==="
python - <<'PY'
import torch, transformers, timm, xformers
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.device_count())
print("transformers", transformers.__version__, "| timm", timm.__version__, "| xformers", xformers.__version__)
import attrdict; print("attrdict OK")
from deepseek_vl2.models import DeepseekVLV2Processor, DeepseekVLV2ForCausalLM
print("deepseek_vl2 import OK")
PY
