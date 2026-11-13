#!/usr/bin/env bash
# v12 screen c (training scenarios only): boost_k 0.25, and boost_k 0.5 with a 0.6 cap, on the cold four.
# Starts once screen b has written all eight results (its runner was stopped by mistake; its pool kept going).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
R=/d/SmartBuildings_data/results/dev12_8640
until [ "$(ls $R/gs80/*.json $R/gs73/*.json 2>/dev/null | wc -l)" -ge 8 ]; do sleep 20; done
echo "screen b complete $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_v12_c.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "V12C DONE $(date +%H:%M:%S)"
