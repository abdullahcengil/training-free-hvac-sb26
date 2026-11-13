#!/usr/bin/env bash
# After screen d: (1) bit check of the occupancy-oracle code with the oracle off against the v12 training runs
# (first 2016 steps, two scenarios), alongside two per-zone dumps for detecting departures (sb/occ_dump.py);
# (2) the oracle on the cold four and the warm four (training-only ceiling for a departure detector; never submitted).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
LOG=/d/SmartBuildings_data/v13_screen_d.log
D=/d/SmartBuildings_data/results/occdump
mkdir -p $D
until grep -q "V13D DONE" $LOG; do sleep 60; done
for s in fairbanks_8 phoenix_4; do
  $PY -m sb.occ_dump --policy D:/SmartBuildings_data/frozen/zonal_v11f.py:TransferPolicy \
    --scenario $SC/building_train_8/$s --steps 2016 --out $D/b8_$s.npz --kwargs "$(cat submission/V12_PARAMS.json)" \
    2>&1 | grep -v -i warn &
done
OUT=/d/SmartBuildings_data/results/bitcheck13/occ0
$PY -m sb.run --policy D:/SmartBuildings_data/frozen/zonal_v13dev_occ.py:TransferPolicy --scenarios $SC \
  --only building_train_8__fairbanks_8 building_train_8__singapore_7 --out $OUT --steps 2016 --workers 2 --components \
  --kwargs "$(cat submission/V12_PARAMS.json)" 2>&1 | grep -v -i warn
wait
$PY - <<'PY'
import numpy as np
for s in ("building_train_8__fairbanks_8", "building_train_8__singapore_7"):
    a = np.load(f"D:/SmartBuildings_data/results/bitcheck13/occ0/{s}.npy")
    b = np.load(f"D:/SmartBuildings_data/results/dev12_8640/v12_all30/{s}.npy")[: len(a)]
    print("BITCHECK", s, len(a), "identical" if np.array_equal(a, b) else f"DIFFERENT (max abs {np.abs(a - b).max():.3g})")
PY
echo "DUMPS AND BITCHECK DONE $(date +%H:%M:%S)"
$PY -m sb.jobs sb/jobs_v13_occ2.json --workers 4 2>&1 | grep -v -i warn
echo "V13OCC DONE $(date +%H:%M:%S)"
