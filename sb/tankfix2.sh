#!/usr/bin/env bash
# Tank-fix check, part 2 (docs/TANKFIX.md): pid_water on the shipped simulator for the other four scenarios, run the
# same way as the patched runs, after screen e.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "SCREEN E DONE" /d/SmartBuildings_data/v14_e.log; do sleep 30; done
$PY -m sb.jobs sb/jobs_tankfix_shipped2.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "TANKFIX2 DONE $(date +%H:%M:%S)"
