#!/usr/bin/env bash
# Round-4 diagnosis: where v9 loses energy in warm climates (training scenarios only).
# Usage: bash sb/diag_warm.sh <steps> <building/weather>...
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
V9='{"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45}'
STEPS=$1; shift
for s in "$@"; do
  tag=$(echo $s | tr / _)
  $PY -m sb.debug --policy policies/zonal.py:TransferPolicy --scenario $SC/$s --steps $STEPS \
    --out /d/SmartBuildings_data/results/dbg_r4/v9_${tag}_${STEPS}.csv --kwargs "${KW:-$V9}" > /d/SmartBuildings_data/results/dbg_r4/v9_${tag}_${STEPS}.log 2>&1 &
done
wait
echo DIAG DONE
