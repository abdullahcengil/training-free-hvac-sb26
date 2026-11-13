#!/usr/bin/env bash
# docs/HIDLIKE.md: 1) pid_water on the patched simulator, ten January stress scenarios; 2) new buildings x new climates.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
echo "start $(date +%H:%M:%S)"
PYTHONPATH=D:/SmartBuildings_data/kit_tankfix $PY -m sb.jobs sb/jobs_subsidy.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "SUBSIDY DONE $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_hidlike.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "HIDLIKE DONE $(date +%H:%M:%S)"
