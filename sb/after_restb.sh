#!/usr/bin/env bash
# Second half of the v11 candidate's 30 training scenarios (2 workers) once the two leftover m2c workers exit.
cd "$(dirname "$0")/.."
while tasklist //FI "PID eq 10876" | grep -q python || tasklist //FI "PID eq 12488" | grep -q python; do sleep 20; done
/d/SmartBuildings_data/starter-kit/.venv/Scripts/python -m sb.jobs sb/jobs_v11c_2.json --workers 2 2>&1 | grep --line-buffered -v -i warn
