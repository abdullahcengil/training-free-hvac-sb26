#!/usr/bin/env bash
# v11 warm screens with the mass model (training scenarios only, full length): night float plus a short,
# strong pull-down before comfort time (the shape the per-zone LP bound chose for phoenix_4).
# Waits for queue11c to finish; touch /d/SmartBuildings_data/results/dev11_8640/STOP to stop.
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
F11=D:/SmartBuildings_data/frozen/zonal_v11dev_c.py
WARM="building_train_8__singapore_7 building_train_8__phoenix_4 building_train_1__phoenix_5 building_train_7__atlanta_8"
until [ $(ls $R/lead1/*.json 2>/dev/null | wc -l) -ge 4 ]; do sleep 20; done
run() { [ -f $R/STOP ] && { echo STOPPED; exit 0; }; WORKERS=4 bash sb/dev11.sh "$@"; }
run $F11 m2c_pc2 '{"mass_model": 1, "precool": 1, "precool_h": 2.0, "precool_k": 1.5}' $WARM
run $F11 m2c_pc2_g0 '{"mass_model": 1, "precool": 1, "precool_h": 2.0, "precool_k": 1.5, "guard": 0.0}' $WARM
echo QUEUE11D DONE
