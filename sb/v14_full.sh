#!/usr/bin/env bash
# Full check of offset_free 3 (docs/TUNING_LOG.md, screen e passed 22:40): 30 training + 40 stress scenarios.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "TANKFIX2 DONE" /d/SmartBuildings_data/tankfix2.log; do sleep 30; done
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_v14_full.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "FULL DONE $(date +%H:%M:%S)"
