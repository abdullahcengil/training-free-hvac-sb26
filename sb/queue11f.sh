#!/usr/bin/env bash
# v11 variants of the mass model on the four cold training scenarios (full length), after queue11e.
# touch /d/SmartBuildings_data/results/dev11_8640/STOP to stop before the next item.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
F11=D:/SmartBuildings_data/frozen/zonal_v11dev_d.py
COLD="building_train_1__fairbanks_1 building_train_8__fairbanks_8 building_train_2__fairbanks_2 building_train_4__denver_2"
until [ $(ls $R/m2c/*.json 2>/dev/null | wc -l) -ge 30 ]; do sleep 30; done
run() { [ -f $R/STOP ] && { echo STOPPED; exit 0; }; WORKERS=4 bash sb/dev11.sh "$@"; }
run $F11 m2d_roll '{"mass_model": 1, "glide_roll": 1}' $COLD
run $F11 m2d_rate '{"mass_model": 1, "m2_rate": 1}' $COLD
run $F11 m2d_roll_f12 '{"mass_model": 1, "glide_roll": 1, "glide_floor": -12.0}' $COLD
run $F11 m2d_caps '{"mass_model": 1, "glide_roll": 1, "f_heat_max": 0.35, "f_heat_safety": 0.45, "f_heat_rec": 0.4}' $COLD
echo QUEUE11F DONE
