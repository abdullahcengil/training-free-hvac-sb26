#!/usr/bin/env bash
# Development evaluation: 6 training scenarios (one per building), 10-day episodes.
# Usage: bash sb/dev.sh <policy-spec> <tag> [kwargs-json] [steps]
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
DEV="building_train_1__fairbanks_1 building_train_2__phoenix_6 building_train_4__denver_2 building_train_5__singapore_4 building_train_7__atlanta_8 building_train_8__denver_6"
STEPS=${4:-2880}
cd "$(dirname "$0")/.."
$PY -m sb.run --policy "$1" --scenarios $SC --only $DEV --out /d/SmartBuildings_data/results/dev_${STEPS}/$2 --steps $STEPS --workers ${WORKERS:-3} --components --kwargs "${3:-{\}}" 2>&1 | grep -v -i warn
