#!/usr/bin/env bash
# v8 development runs, one simulation at a time (the machine holds about five).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
# Bit-for-bit check of deviation 2: working copy with defaults vs the frozen dev result.
$PY -m sb.run --policy policies/zonal.py:TransferPolicy --scenarios $SC --only building_train_4__denver_2 \
  --out /d/SmartBuildings_data/results/dev_2880/bitcheck --steps 2880 --workers 1 --components 2>&1 | grep -v -i warn
WORKERS=1 bash sb/dev.sh policies/zonal.py:TransferPolicy v8_dist_only '{"dist_obs":1}'
WORKERS=1 bash sb/dev.sh policies/zonal.py:TransferPolicy v8_beta005 '{"safety_pred":1,"dist_obs":1,"dist_beta":0.05}'
WORKERS=1 bash sb/dev.sh policies/zonal.py:TransferPolicy v8_beta02 '{"safety_pred":1,"dist_obs":1,"dist_beta":0.2}'
WORKERS=1 bash sb/dev.sh policies/zonal.py:TransferPolicy v8_nodelay '{"safety_pred":1,"dist_obs":1,"delay_comp":0}'
echo QUEUE_V8_DONE
