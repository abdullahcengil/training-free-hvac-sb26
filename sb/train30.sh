#!/usr/bin/env bash
# The 30 training scenarios at full length: v7 (round-1 frozen file; for round 1's
# descriptive H4) and v8 (round-2 frozen file and parameters), for comparison with
# the shipped baseline returns. Skips finished scenarios.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
OUT=/d/SmartBuildings_data/results/train_8640
case $1 in
  v7) $PY -m sb.run --policy D:/SmartBuildings_data/frozen/zonal_ad5946615c746745a243560ae3a681eaf7d19618.py:TransferPolicy \
        --scenarios $SC --out $OUT/zonal --steps 8640 --workers ${WORKERS:-2} --components 2>&1 | grep -v -i warn ;;
  v8) $PY -m sb.run --policy D:/SmartBuildings_data/frozen/zonal_e8dbcd3163f2d0e4ce9006b02ed7067a5f5927bd.py:TransferPolicy \
        --scenarios $SC --out $OUT/v8 --steps 8640 --workers ${WORKERS:-2} --components \
        --kwargs "$(cat docs/preregistration2/V8_PARAMS.json)" 2>&1 | grep -v -i warn ;;
esac
