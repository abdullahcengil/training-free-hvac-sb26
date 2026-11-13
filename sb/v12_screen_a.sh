#!/usr/bin/env bash
# v12 screen a (training scenarios only), started after round 5: (1) bit-for-bit check of frozen/zonal_v12dev_a.py
# at the v11 parameters (new options off) against the v11 training runs (dev11_8640/v11f, first 2016 steps);
# (2) start_learn on the cold four and the warm four, boost_k 0.5 on the cold four (full length, 4 workers).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
F=D:/SmartBuildings_data/frozen/zonal_v12dev_a.py
OUT=/d/SmartBuildings_data/results/bitcheck12/v11params_codeA
$PY -m sb.run --policy $F:TransferPolicy --scenarios $SC --only building_train_8__fairbanks_8 building_train_8__singapore_7 \
  --out $OUT --steps 2016 --workers 2 --components --kwargs "$(cat docs/preregistration5/V11_PARAMS.json)" 2>&1 | grep -v -i warn
$PY - <<'PY'
import numpy as np
for s in ("building_train_8__fairbanks_8", "building_train_8__singapore_7"):
    a = np.load(f"D:/SmartBuildings_data/results/bitcheck12/v11params_codeA/{s}.npy")
    b = np.load(f"D:/SmartBuildings_data/results/dev11_8640/v11f/{s}.npy")[: len(a)]
    print(s, len(a), "identical" if np.array_equal(a, b) else f"DIFFERENT (max abs {np.abs(a - b).max():.3g})")
PY
$PY - <<'PY'
import json
from pathlib import Path
v11 = json.loads(Path("docs/preregistration5/V11_PARAMS.json").read_text())
F = "D:/SmartBuildings_data/frozen/zonal_v12dev_a.py:TransferPolicy"
R = "D:/SmartBuildings_data/results/dev12_8640"
cold = ["building_train_8__fairbanks_8", "building_train_1__fairbanks_1", "building_train_4__denver_2", "building_train_2__fairbanks_2"]
warm = ["building_train_8__phoenix_4", "building_train_8__singapore_7", "building_train_7__atlanta_8", "building_train_1__phoenix_5"]
jobs = [{"policy": F, "kwargs": dict(v11, start_learn=1), "out": f"{R}/sl", "scenario": s} for s in cold + warm]
jobs += [{"policy": F, "kwargs": dict(v11, boost_k=0.5), "out": f"{R}/bk05", "scenario": s} for s in cold]
Path("sb/jobs_v12_a.json").write_text(json.dumps(jobs, indent=1))
print(len(jobs), "jobs")
PY
$PY -m sb.jobs sb/jobs_v12_a.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo "V12A DONE"
