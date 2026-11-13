#!/usr/bin/env bash
# v9 candidate on all 30 training scenarios at full length (warm-climate regression check
# before any freeze). Uses a snapshot of the working copy so later edits cannot leak in.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
$PY -m sb.run --policy D:/SmartBuildings_data/frozen/zonal_v9dev_candidate3.py:TransferPolicy \
  --scenarios $SC --out /d/SmartBuildings_data/results/train_8640/v9f --steps 8640 --workers ${WORKERS:-4} --components \
  --kwargs '{"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45}' 2>&1 | grep --line-buffered -v -i warn
echo TRAIN30 DONE
