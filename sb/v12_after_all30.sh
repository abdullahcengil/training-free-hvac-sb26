#!/usr/bin/env bash
# After v12's 30-scenario run: compare with v11 on all 30 (and the screen-c bit-for-bit check), then check the v12
# notebook against the frozen file (576 steps). Prints V12 READY with the numbers; the submission decision is made
# by hand from them.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until grep -q "V12 ALL30 DONE" /d/SmartBuildings_data/v12_all30.log 2>/dev/null; do sleep 15; done
$PY - <<'PY'
import json, glob, os
import numpy as np
R = "D:/SmartBuildings_data/results/"
def load(d):
    return {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(R + d + "/*.json")}
v12, v11, c = load("dev12_8640/v12_all30"), load("dev11_8640/v11f"), load("dev12_8640/bk025")
keys = sorted(v11)
a = np.array([abs(v12[k]["mean_reward"]) for k in keys]); b = np.array([abs(v11[k]["mean_reward"]) for k in keys])
cold = np.array([("fairbanks" in k or "denver" in k) for k in keys])
tie = np.isclose(a, b, rtol=1e-9, atol=0)
print(f"v12 {a.mean():.5f} vs v11 {b.mean():.5f} ({100*(a.mean()/b.mean()-1):+.2f} %); better {int(((a<b)&~tie).sum())}, "
      f"same {int(tie.sum())}, worse {int(((a>b)&~tie).sum())}; cold {100*(a[cold].mean()/b[cold].mean()-1):+.2f} %, "
      f"warm {100*(a[~cold].mean()/b[~cold].mean()-1):+.2f} %")
for k, x, y in zip(keys, a, b):
    if abs(x / y - 1) > 0.002:
        print(f"  {k}: {x:.5f} vs {y:.5f} ({100*(x/y-1):+.1f} %)")
same = all(np.array_equal(np.load(R + f"dev12_8640/v12_all30/{k}.npy"), np.load(R + f"dev12_8640/bk025/{k}.npy")) for k in c)
print("screen-c runs reproduced bit for bit:", same)
comf = lambda d: np.mean([-0.6 * d[k]["components"]["prod"] / 8640 for k in keys])
print(f"comfort per step: v12 {comf(v12):.5f} vs v11 {comf(v11):.5f}")
PY
$PY -m sb.nbcheck --notebook submission/zonal_v12_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v11f.py \
  --params submission/V12_PARAMS.json --scenario D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios/building_train_1/atlanta_2 \
  --steps 576 2>&1 | grep -v -i warn
echo "V12 READY $(date +%H:%M:%S)"
