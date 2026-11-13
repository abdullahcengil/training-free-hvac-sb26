#!/usr/bin/env bash
# Screen e (docs/TUNING_LOG.md, 23 Oct 21:30): offset_free 3 and 1 on 8 scenarios, full length, after the tank-fix runs.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "TANKFIX DONE" /d/SmartBuildings_data/tankfix.log; do sleep 30; done
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_v14_e.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "SCREEN E DONE $(date +%H:%M:%S)"
