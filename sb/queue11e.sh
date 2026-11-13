#!/usr/bin/env bash
# v11: the mass model on all 30 training scenarios at full length, then variants on the cold twelve.
# Starts when queue11c has stopped (STOP file) and its cold batch has finished.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios
F11=D:/SmartBuildings_data/frozen/zonal_v11dev_c.py
until [ $(ls $R/m2c/building_train_1__fairbanks_1.json $R/m2c/building_train_8__fairbanks_8.json $R/m2c/building_train_2__fairbanks_2.json $R/m2c/building_train_4__denver_2.json 2>/dev/null | wc -l) -ge 4 ]; do sleep 20; done
sleep 30
rm -f $R/STOP
KW=$($PY -c "import json; k=json.load(open('docs/preregistration4/V10_PARAMS.json')); k.update(mass_model=1); print(json.dumps(k))")
# all 30 (finished ones are skipped by sb.run); slowest buildings first so the pool stays full
ALL=$(ls -d $SC/building_train_2/* $SC/building_train_4/* $SC/building_train_5/* $SC/building_train_1/* $SC/building_train_7/* $SC/building_train_8/* | sed 's#.*/\(building_train_[0-9]*\)/\(.*\)#\1__\2#')
$PY -m sb.run --policy $F11:TransferPolicy --scenarios $SC --only $ALL --out $R/m2c --steps 8640 --workers 4 --components --kwargs "$KW" 2>&1 | grep --line-buffered -v -i warn
echo QUEUE11E DONE
