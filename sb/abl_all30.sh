#!/usr/bin/env bash
# The two test-set ablations of v11 (dp_reset 0; cool_glide 0) on all 30 training scenarios at full length, for the
# paper's comparison of public and training ratios (docs/RESULTS_EXTERNAL.md, 23 Oct). Starts after v12's check.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "V12 READY" /d/SmartBuildings_data/v12_after_all30.log 2>/dev/null; do sleep 20; done
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_abl_all30.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "ABL ALL30 DONE $(date +%H:%M:%S)"
