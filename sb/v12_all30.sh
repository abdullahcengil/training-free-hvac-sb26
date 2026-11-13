#!/usr/bin/env bash
# v12 (frozen v11 file + V11_PARAMS + boost_k 0.25) on all 30 training scenarios at full length, 4 workers, after
# the ablation notebook checks have finished (machine limit: four simulations).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "NBCHECK DONE" /d/SmartBuildings_data/nbcheck_ablations.log 2>/dev/null; do sleep 10; done
echo "start $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_v12_all30.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "V12 ALL30 DONE $(date +%H:%M:%S)"
