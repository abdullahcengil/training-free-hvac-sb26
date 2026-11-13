#!/usr/bin/env bash
# Start the warm variant screens (2 workers) once the diverse mass-model batch has finished.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
until [ $(ls $R/m2c/*.json 2>/dev/null | wc -l) -ge 14 ]; do sleep 20; done
sleep 10
/d/SmartBuildings_data/starter-kit/.venv/Scripts/python -m sb.jobs sb/jobs_m2f_warm.json --workers 2 2>&1 | grep --line-buffered -v -i warn
