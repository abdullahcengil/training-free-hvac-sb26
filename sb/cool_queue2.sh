#!/usr/bin/env bash
# Round-4 screen 2 (training scenarios only), 7 days (2016 steps):
# bit-for-bit check of the new code against the round-3 frozen v9 file; higher ceilings in
# the warm set; the cooling glide on six mixed and cold training scenarios.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=D:/SmartBuildings_data/frozen/zonal_v10dev_a.py:TransferPolicy
V9F=D:/SmartBuildings_data/frozen/zonal_b7e5ec9d5df75001d3376c5bf7f0ba121a73f19c.py:TransferPolicy
V9='"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45'
WARM="building_train_8__phoenix_4 building_train_1__phoenix_5 building_train_4__singapore_3 building_train_4__atlanta_5"
MIXED="building_train_8__denver_6 building_train_5__fairbanks_5 building_train_1__atlanta_2 building_train_4__denver_2 building_train_1__fairbanks_1 building_train_7__phoenix_3"
run() {  # policy tag kwargs scenarios...
  pol=$1; tag=$2; kw=$3; shift 3
  echo "== $tag"
  $PY -m sb.run --policy $pol --scenarios $SC --only "$@" --out /d/SmartBuildings_data/results/cool_2016/$tag \
    --steps 2016 --workers ${WORKERS:-4} --components --kwargs "{$V9$kw}" 2>&1 | grep --line-buffered -v -i warn
}
run $V9F v9_frozen "" $WARM
run $POL cg_d ', "cool_glide": 1, "cool_ceiling": 8.0' $WARM
run $POL v9_newcode "" $MIXED
run $POL cg_a ', "cool_glide": 1' $MIXED
echo QUEUE DONE
