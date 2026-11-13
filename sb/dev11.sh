#!/usr/bin/env bash
# v11 development runs (training scenarios only, full length) from a snapshot, v10 parameters
# plus extra JSON. Usage: bash sb/dev11.sh <snapshot.py> <tag> '<extra json>' <scenarios...>
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=$1:TransferPolicy; TAG=$2; EXTRA=$3; shift 3
KW=$($PY -c "import json,sys; k=json.load(open('docs/preregistration4/V10_PARAMS.json')); k.update(json.loads(sys.argv[1])); print(json.dumps(k))" "$EXTRA")
$PY -m sb.run --policy $POL --scenarios $SC --only "$@" --out /d/SmartBuildings_data/results/dev11_8640/$TAG \
  --steps 8640 --workers ${WORKERS:-2} --components --kwargs "$KW" 2>&1 | grep --line-buffered -v -i warn
