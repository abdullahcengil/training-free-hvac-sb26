#!/usr/bin/env bash
# v11 development (training scenarios only, full length): heating capacity. The VAV coil
# keeps the 35 C discharge cap up to about 1.1 m3/s (57 % of the box maximum), so the
# gas per kW delivered does not change below that; v10 caps heating airflow at 0.245
# (and zones far below their band at only 0.2). Usage: bash sb/cap_queue1.sh <tag> <cap> <scenarios...>
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
POL=D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py:TransferPolicy
TAG=$1; CAP=$2; shift 2
KW=$($PY -c "import json,sys; k=json.load(open('docs/preregistration4/V10_PARAMS.json')); k.update(f_heat_max=$CAP, f_heat_safety=$CAP, f_heat_rec=max($CAP, k['f_heat_rec'])); print(json.dumps(k))")
$PY -m sb.run --policy $POL --scenarios $SC --only "$@" --out /d/SmartBuildings_data/results/dev11_8640/$TAG \
  --steps 8640 --workers ${WORKERS:-2} --components --kwargs "$KW" 2>&1 | grep --line-buffered -v -i warn
