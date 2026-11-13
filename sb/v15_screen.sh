#!/bin/bash
# v15 screen (docs/BIGDEV.md): waits for v14's 12 reference results on the full-size set, then runs the four
# candidates on the 12 full-size scenarios (2880 steps) with two workers.
cd .
PY=D:/SmartBuildings_data/starter-kit/.venv/Scripts/python
until [ "$(ls D:/SmartBuildings_data/results/bigdev/v14/*.json 2>/dev/null | wc -l)" -ge 12 ]; do sleep 30; done
sleep 60   # let the reference pools exit
echo "v14 reference done $(date)"
$PY -m sb.jobs sb/jobs_v15_screen.json --workers 2 --steps 2880
echo "screen done $(date)"
