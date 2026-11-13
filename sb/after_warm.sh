#!/usr/bin/env bash
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
until [ $(ls $R/m2f_mc25/*.json 2>/dev/null | wc -l) -ge 4 ]; do sleep 20; done
sleep 10
/d/SmartBuildings_data/starter-kit/.venv/Scripts/python -m sb.jobs sb/jobs_m2c_restB.json --workers 2 2>&1 | grep --line-buffered -v -i warn
