#!/usr/bin/env bash
# Long chain after the freeze: held-out (pre-registered), dev reproduction,
# ablations on the dev set, then the 30 training scenarios at full length.
cd "$(dirname "$0")/.."
bash sb/heldout.sh
bash sb/dev.sh policies/zonal.py:TransferPolicy frozen | grep SCORE
printf '%s\n' 'abl_no_rls|{"rls":0}' 'abl_no_delay|{"delay_comp":0}' 'abl_no_sat_econ|{"sat_econ":0}' 'abl_no_heat_cap|{"f_heat_max":1.0}' 'abl_no_idle_reheat|{"idle_aware":0}' 'abl_water_330_310|{"water_heat":330.0,"water_idle":310.0}' | bash sb/queue.sh
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
$PY -m sb.run --policy policies/zonal.py:TransferPolicy --scenarios /d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios --out /d/SmartBuildings_data/results/train_8640/zonal --steps 8640 --workers 3 --components 2>&1 | grep -v -i warn
echo NIGHT_DONE
