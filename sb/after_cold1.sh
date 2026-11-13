#!/usr/bin/env bash
# Next cold screens (2 workers) once the first cold variant list has finished.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
until [ $(ls $R/m2f_rate/*.json 2>/dev/null | wc -l) -ge 4 ]; do sleep 20; done
sleep 10
/d/SmartBuildings_data/starter-kit/.venv/Scripts/python -m sb.jobs sb/jobs_m2g_cold.json --workers 2 2>&1 | grep --line-buffered -v -i warn
