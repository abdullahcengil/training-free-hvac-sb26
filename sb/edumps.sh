#!/usr/bin/env bash
# Device-level energy traces of the v11 candidate (full length, two at a time), then the second half of
# the candidate's 30 training scenarios (2 workers).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
F=D:/SmartBuildings_data/frozen/zonal_v11dev_g.py:TransferPolicy
KW='{"mass_model": 1, "glide_floor": -12.0, "margin_cool": 0.25, "f_heat_safety": 0.45}'
O=D:/SmartBuildings_data/results/edump_v11c
mkdir -p $O
d() { $PY analysis/energy_dump.py --policy $F --kwargs "$KW" --scenario $1 --steps 8640 --out $O/$1.npz 2>&1 | grep -v -i warn; }
(d building_train_1__fairbanks_1) &
(d building_train_8__phoenix_4; d building_train_8__singapore_7) &
wait
(d building_train_8__fairbanks_8) &
(d building_train_1__phoenix_5) &
wait
echo EDUMPS DONE
$PY -m sb.jobs sb/jobs_v11c_2.json --workers 2 2>&1 | grep --line-buffered -v -i warn
