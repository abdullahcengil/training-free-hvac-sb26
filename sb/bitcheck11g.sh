#!/usr/bin/env bash
# Bit-for-bit check of the final v11 code: policies/zonal.py with the v10 parameters (mass model off) must give
# per-step rewards identical to the v10 training runs (train_8640/v10c) for the first 2016 steps.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
OUT=/d/SmartBuildings_data/results/bitcheck11/v10params_codeG
$PY -m sb.run --policy policies/zonal.py:TransferPolicy --scenarios $SC --only building_train_8__fairbanks_8 building_train_8__singapore_7 \
  --out $OUT --steps 2016 --workers 2 --components --kwargs "$(cat docs/preregistration4/V10_PARAMS.json)" 2>&1 | grep -v -i warn
$PY - <<'PY'
import numpy as np
for s in ("building_train_8__fairbanks_8", "building_train_8__singapore_7"):
    a = np.load(f"D:/SmartBuildings_data/results/bitcheck11/v10params_codeG/{s}.npy")
    b = np.load(f"D:/SmartBuildings_data/results/train_8640/v10c/{s}.npy")[: len(a)]
    print(s, len(a), "identical" if np.array_equal(a, b) else f"DIFFERENT (max abs {np.abs(a - b).max():.3g})")
PY
