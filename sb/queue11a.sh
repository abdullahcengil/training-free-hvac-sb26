#!/usr/bin/env bash
# v11 screens at full length (training scenarios only): night band defence, lead time, boost cap.
cd "$(dirname "$0")/.."
F=D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py
until [ -f /d/SmartBuildings_data/results/dev11_8640/floor_m12/building_train_2__fairbanks_2.json ]; do sleep 20; done
WARM="building_train_8__singapore_7 building_train_8__phoenix_4 building_train_1__phoenix_5 building_train_7__atlanta_8"
COLD="building_train_1__fairbanks_1 building_train_8__fairbanks_8 building_train_2__fairbanks_2 building_train_4__denver_2"
WORKERS=4 bash sb/dev11.sh $F guard_0 '{"guard": 0.0}' $WARM
WORKERS=4 bash sb/dev11.sh $F guard_m1 '{"guard": -1.0}' $WARM
WORKERS=4 bash sb/dev11.sh $F boost40 '{"f_heat_safety": 0.4}' $COLD
WORKERS=4 bash sb/dev11.sh $F lead1 '{"lead_h": 1.0}' $WARM
echo QUEUE11A DONE
