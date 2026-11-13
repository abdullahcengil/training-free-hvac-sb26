#!/usr/bin/env bash
# v10 candidate on all 30 training scenarios at full length (regression check against v9f
# before any freeze). Snapshot and parameters given as arguments.
# Usage: bash sb/train30_v10.sh <snapshot.py> <tag> <kwargs-json>
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
$PY -m sb.run --policy $1:TransferPolicy --scenarios $SC --out /d/SmartBuildings_data/results/train_8640/$2 \
  --steps 8640 --workers ${WORKERS:-4} --components --kwargs "$3" 2>&1 | grep --line-buffered -v -i warn
echo TRAIN30 DONE
