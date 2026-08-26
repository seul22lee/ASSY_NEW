source /home/ftk3187/miniconda3/etc/profile.d/conda.sh && conda activate psed310
P=/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad/s05m/pilot
export PILOT_PLAN=round2_design_plan.json PILOT_LOG=round2_translation_log.json
export PILOT_PREFIX=round2_ PILOT_CAD=cad_round2
echo "########## TRANSLATE + S06 + S07 ##########"
python $P/pipeline2.py
echo "########## RENDER ##########"
python $P/render.py
