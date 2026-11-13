#!/usr/bin/env bash
# v11 screens at full length (training scenarios only). Waits for the running boost40 screen; touch
# /d/SmartBuildings_data/results/dev11_8640/STOP to stop before the next item.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
F10=D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py
F11=D:/SmartBuildings_data/frozen/zonal_v11dev_b.py
WARM="building_train_8__singapore_7 building_train_8__phoenix_4 building_train_1__phoenix_5 building_train_7__atlanta_8"
COLD="building_train_1__fairbanks_1 building_train_8__fairbanks_8 building_train_2__fairbanks_2 building_train_4__denver_2"
until [ $(ls $R/boost40/*.json 2>/dev/null | wc -l) -ge 4 ]; do sleep 20; done
run() { [ -f $R/STOP ] && { echo STOPPED; exit 0; }; WORKERS=4 bash sb/dev11.sh "$@"; }
run $F11 m2 '{"mass_model": 1}' $COLD
run $F11 m2 '{"mass_model": 1}' $WARM
run $F11 m2roll '{"mass_model": 1, "glide_roll": 1}' $COLD
run $F10 guard2 '{"guard": 2.0}' $WARM
run $F10 lead1 '{"lead_h": 1.0}' $WARM
echo QUEUE11B DONE
