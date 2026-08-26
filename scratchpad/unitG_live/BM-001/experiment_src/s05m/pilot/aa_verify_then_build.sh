source /home/ftk3187/miniconda3/etc/profile.d/conda.sh && conda activate psed310
S=/tmp/claude-1040/-home-ftk3187-github-ASSY-Ver3-0/b3b0e7b8-2dab-4f49-b940-9b2ae78760a9/scratchpad/s05m
P=$S/pilot
echo "########## focused regression: hinge pose boundary ##########"
python $S/verify_hinge_poses.py || exit 1
export PILOT_CID=CND-0001
export PILOT_OUT=/home/ftk3187/github/ASSY_Ver3.0/scratchpad/unitG_live/BM-001/s05_assembly_aware_pilot/CND-0001
export PILOT_PLAN=round1_design_plan.json PILOT_LOG=round1_translation_log.json
export PILOT_PREFIX=round1_ PILOT_CAD=cad_round1
echo "########## round 1: translate + S06 + S07 ##########"
python $P/pipeline2.py
echo "########## renders ##########"
python $P/render.py
