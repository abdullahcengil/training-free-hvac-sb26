#!/usr/bin/env bash
# Screen d's winner (v12 + glide_floor -16 + f_heat_rec 0.35) on all 30 training scenarios at full length, 4 workers,
# after the occupancy ceiling test (machine limit: four simulations).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "V13OCC DONE" /d/SmartBuildings_data/v13_oracle.log 2>/dev/null; do sleep 30; done
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_v13_all30.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "V13 ALL30 DONE $(date +%H:%M:%S)"
