#!/usr/bin/env bash
# Cold-climate development runs (training scenarios only).
# Usage: bash sb/cold.sh <tag> <kwargs-json> <steps> <scenario filters...>
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
cd "$(dirname "$0")/.."
TAG=$1; KW=$2; STEPS=$3; shift 3
$PY -m sb.run --policy policies/zonal.py:TransferPolicy --scenarios $SC --only "$@" \
  --out /d/SmartBuildings_data/results/cold_${STEPS}/$TAG --steps $STEPS --workers ${WORKERS:-1} \
  --components --kwargs "$KW" 2>&1 | grep -v -i warn
