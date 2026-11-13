#!/usr/bin/env bash
# Tank-fix check (docs/TANKFIX.md): starts when the stress test is done; 10 jobs on the patched copy, 1 on the shipped
# simulator, 4 workers in all.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "STRESS DONE" /d/SmartBuildings_data/stress.log; do sleep 60; done
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_tankfix_shipped.json --workers 1 2>&1 | grep --line-buffered -v -i warn &
PYTHONPATH=D:/SmartBuildings_data/kit_tankfix $PY -m sb.jobs sb/jobs_tankfix.json --workers 3 2>&1 \
  | grep --line-buffered -v -i warn
wait
echo "TANKFIX DONE $(date +%H:%M:%S)"
