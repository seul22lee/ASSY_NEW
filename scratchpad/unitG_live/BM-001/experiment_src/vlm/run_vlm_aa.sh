source /home/ftk3187/miniconda3/etc/profile.d/conda.sh && conda activate psed310
S=/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad
export PYTHONPATH=$S/tf438:$S/DeepSeek-VL2:$S
export HF_HOME=$S/hf CUDA_VISIBLE_DEVICES=3 TOKENIZERS_PARALLELISM=false
export PILOT_OUT=/home/ftk3187/github/ASSY_Ver3.0/scratchpad/unitG_live/BM-001/s05_assembly_aware_pilot/CND-0001
python $S/${1:-vlm_review_aa.py}
