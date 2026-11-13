#!/usr/bin/env bash
# Round-4 screen 1 (training scenarios only): cooling-side night glide in warm climates,
# 7 days (2016 steps). v10a = snapshot of the working copy (frozen/zonal_v10dev_a.py).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=D:/SmartBuildings_data/frozen/zonal_v10dev_a.py:TransferPolicy
V9='"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45'
ONLY="building_train_8__phoenix_4 building_train_1__phoenix_5 building_train_4__singapore_3 building_train_4__atlanta_5"
run() {  # tag kwargs
  echo "== $1"
  $PY -m sb.run --policy $POL --scenarios $SC --only $ONLY --out /d/SmartBuildings_data/results/cool_2016/$1 \
    --steps 2016 --workers ${WORKERS:-4} --components --kwargs "{$V9$2}" 2>&1 | grep --line-buffered -v -i warn
}
run v9_newcode ""
run cg_a ', "cool_glide": 1'
run cg_b ', "cool_glide": 1, "cool_rec_frac": 0.5'
run cg_c ', "cool_glide": 1, "cool_ceiling": 2.0'
echo QUEUE DONE
