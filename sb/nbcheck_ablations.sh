#!/usr/bin/env bash
# Check the two ablation notebooks against the frozen v11 file (576 steps each, one at a time), once screen c has at
# most three simulations left (machine limit: four).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios/building_train_1/atlanta_2
until [ "$(grep -c TransferPoli /d/SmartBuildings_data/v12_screen_c.log)" -ge 5 ]; do sleep 15; done
for t in dp0 cg0; do
  echo "== $t $(date +%H:%M:%S)"
  $PY -m sb.nbcheck --notebook submission/zonal_v11_abl_${t}_submission.ipynb \
    --policy D:/SmartBuildings_data/frozen/zonal_v11f.py --params submission/V11_ABL_${t}_PARAMS.json \
    --scenario $SC --steps 576 2>&1 | grep -v -i warn
done
echo "NBCHECK DONE $(date +%H:%M:%S)"
