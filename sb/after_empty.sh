#!/usr/bin/env bash
# Start the cold variant screens (2 workers) once the empty-day test has finished.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
until [ -f $R/m2e_empty/building_train_1__fairbanks_1.json ] && [ -f $R/m2e_empty/building_train_8__singapore_7.json ]; do sleep 15; done
sleep 10
/d/SmartBuildings_data/starter-kit/.venv/Scripts/python -m sb.jobs sb/jobs_m2f_cold.json --workers 2 2>&1 | grep --line-buffered -v -i warn
