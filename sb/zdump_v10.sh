#!/usr/bin/env bash
# Mass-model design data (training scenarios only): per-zone 30-day traces of v10.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py:TransferPolicy
KW=$(cat docs/preregistration4/V10_PARAMS.json)
for s in building_train_1/fairbanks_1 building_train_8/phoenix_4 building_train_4/denver_2 building_train_8/singapore_7; do
  $PY -m sb.zone_dump --policy $POL --scenario $SC/$s --start 0 --end 8640 \
    --out /d/SmartBuildings_data/results/zdump_v10/$(echo $s | tr / _).npz --kwargs "$KW" > /d/SmartBuildings_data/results/zdump_v10/$(echo $s | tr / _).log 2>&1 &
done
wait
echo ZDUMP DONE
