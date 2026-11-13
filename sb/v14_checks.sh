#!/usr/bin/env bash
# After the full check: v14 file checks (sb/make_v14f.py). 1) offset_free 0 equals v13 bit for bit (576 steps);
# 2) the v14 notebook gives the tested development file's actions (sb/nbcheck.py, building 7 in Duluth, 576 steps,
# where offset_free 3 is active on the Monday).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "FULL DONE" /d/SmartBuildings_data/v14_full.log; do sleep 30; done
$PY -m sb.v14_eval
$PY - <<'PYEOF' 2>&1 | grep -v -i warn
import json, shutil
from sb.run import run_job
p = json.load(open("submission/V13_PARAMS.json"))
S = "D:/SmartBuildings_data/stress/scenarios/building_train_7/duluth_jan15"
shutil.rmtree("D:/SmartBuildings_data/results/bitcheck14/v14f_off", ignore_errors=True)
r = run_job(("D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy", S, "D:/SmartBuildings_data/results/bitcheck14/v14f_off", 576, True, dict(p, offset_free=0)))
print("v14f offset_free 0:", r["total_reward"], "identical to v13 (-11.63590580757591):", r["total_reward"] == -11.63590580757591)
PYEOF
$PY -m sb.nbcheck --notebook submission/zonal_v14_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v14dev_of.py \
  --params submission/V14_PARAMS.json --scenario D:/SmartBuildings_data/stress/scenarios/building_train_7/duluth_jan15 --steps 576 2>&1 | grep -v -i warn | tail -4
echo "V14 CHECKS DONE $(date +%H:%M:%S)"
