#!/usr/bin/env bash
# Climate stress test (docs/STRESS_TEST.md): v13 and pid_water on 40 scenarios, 4 workers.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_stress.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "STRESS DONE $(date +%H:%M:%S)"
