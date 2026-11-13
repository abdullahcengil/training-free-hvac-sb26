#!/usr/bin/env bash
# Round-4 CMA-ES search (training scenarios only): 14 parameters, six training scenarios
# that no v10 screen used, 7 days (2016 steps). Snapshot: frozen/zonal_v10dev_c.py.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
$PY -m sb.search --out D:/SmartBuildings_data/results/search/s2 \
  --policy D:/SmartBuildings_data/frozen/zonal_v10dev_c.py:TransferPolicy \
  --base '{"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45, "cool_glide": 1, "cool_free": 1, "cool_ceiling": 8.0}' \
  --space s2 --steps 2016 --gens ${GENS:-6} --popsize 8 --sigma 0.25 --seed 4 --workers 4 \
  --scenarios building_train_2/fairbanks_2 building_train_8/fairbanks_8 building_train_2/phoenix_6 \
              building_train_7/singapore_6 building_train_5/denver_3 building_train_7/atlanta_8 \
  2>&1 | grep --line-buffered -v -i warn
