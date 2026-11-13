#!/usr/bin/env bash
# Round-4 screen 3 (training scenarios only), 7 days (2016 steps), warm + mixed sets:
# cooling glide with the free-cooling exception and a slower assumed pull-down rate.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=D:/SmartBuildings_data/frozen/zonal_v10dev_b.py:TransferPolicy
V9='"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45'
ALL="building_train_8__phoenix_4 building_train_1__phoenix_5 building_train_4__singapore_3 building_train_4__atlanta_5 building_train_8__denver_6 building_train_5__fairbanks_5 building_train_1__atlanta_2 building_train_4__denver_2 building_train_1__fairbanks_1 building_train_7__phoenix_3"
run() {  # tag kwargs
  echo "== $1"
  $PY -m sb.run --policy $POL --scenarios $SC --only $ALL --out /d/SmartBuildings_data/results/cool_2016/$1 \
    --steps 2016 --workers ${WORKERS:-4} --components --kwargs "{$V9$2}" 2>&1 | grep --line-buffered -v -i warn
}
run cg_f ', "cool_glide": 1, "cool_free": 1'
run cg_g ', "cool_glide": 1, "cool_free": 1, "cool_rate_max": 1.0'
run cg_i ', "cool_glide": 1, "cool_free": 1, "cool_rate_max": 1.0, "cool_ceiling": 8.0'
echo QUEUE DONE
