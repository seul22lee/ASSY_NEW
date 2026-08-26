source /home/ftk3187/miniconda3/etc/profile.d/conda.sh && conda activate psed310
S=/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad
# transformers 4.38.2 is prepended for THIS PROCESS ONLY; psed310 keeps 4.57.6.
export PYTHONPATH=$S/tf438:$S/DeepSeek-VL2:$S
export HF_HOME=$S/hf CUDA_VISIBLE_DEVICES=3 TOKENIZERS_PARALLELISM=false
python -c "import transformers, torch, sys; print('process transformers', transformers.__version__, '| torch', torch.__version__); print('from', transformers.__file__)"
echo "=== visual review: deepseek-vl2-tiny over the four actual S07 PNGs ==="
python $S/vlm_review.py
