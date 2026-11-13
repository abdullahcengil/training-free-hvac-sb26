#!/usr/bin/env bash
# v11: the mass model on all 30 training scenarios at full length (finished ones are skipped), started once
# the screens running now have finished, so that at most four simulations run at a time.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
F11=D:/SmartBuildings_data/frozen/zonal_v11dev_c.py
need() { [ -f $R/m2c/building_train_2__fairbanks_2.json ] && [ -f $R/m2d_roll/building_train_1__fairbanks_1.json ] \
         && [ -f $R/m2e_empty/building_train_1__fairbanks_1.json ] && [ -f $R/m2e_empty/building_train_8__singapore_7.json ]; }
until need; do sleep 20; done
sleep 20
rm -f $R/STOP
KW=$($PY -c "import json; k=json.load(open('docs/preregistration4/V10_PARAMS.json')); k.update(mass_model=1); print(json.dumps(k))")
ALL=$(ls -d $SC/building_train_*/* | sed 's#.*/\(building_train_[0-9]*\)/\(.*\)#\1__\2#')
$PY -m sb.run --policy $F11:TransferPolicy --scenarios $SC --only $ALL --out $R/m2c --steps 8640 --workers 4 --components --kwargs "$KW" 2>&1 | grep --line-buffered -v -i warn
echo QUEUE11G DONE
