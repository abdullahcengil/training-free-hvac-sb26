#!/usr/bin/env bash
# Round-4 development (training scenarios only): the four warm training scenarios where the
# 7-day screens missed a slow failure, at full length (8640 steps). Snapshot frozen/zonal_v10dev_d.py.
# v10b = v10a + cool_guard; v10c = v10a without the cooling glide (search parameters only).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=D:/SmartBuildings_data/frozen/zonal_v10dev_d.py:TransferPolicy
ONLY="building_train_1__phoenix_5 building_train_1__singapore_8 building_train_2__phoenix_6 building_train_8__phoenix_4"
for tag in v10b v10c; do
  echo "== $tag"
  $PY -m sb.run --policy $POL --scenarios $SC --only $ONLY --out /d/SmartBuildings_data/results/hot_8640/$tag \
    --steps 8640 --workers ${WORKERS:-4} --components --kwargs "$(cat /d/SmartBuildings_data/results/search/s3/${tag^^}.json)" 2>&1 | grep --line-buffered -v -i warn
done
echo QUEUE DONE
