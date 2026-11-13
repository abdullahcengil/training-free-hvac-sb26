#!/usr/bin/env bash
# v9 development, third screen: mixed set where heating matters (two cold, four mild), 12 days.
cd "$(dirname "$0")/.."
M="building_train_1__atlanta_2 building_train_1__denver_7 building_train_1__fairbanks_1 building_train_8__fairbanks_8 building_train_2__denver_8 building_train_4__denver_2"
V8='"safety_pred": 2, "dist_obs": 1'
A='"night_glide": 1, "f_heat_rec": 0.3, "f_heat_max": 0.3, "f_heat_safety": 0.3'
run() { WORKERS=4 bash sb/cold.sh "$1" "$2" 3456 $M; }
run v8 "{$V8}"
run fh03 "{$V8, \"f_heat_max\": 0.3, \"f_heat_safety\": 0.3}"
run v9b "{$V8, \"night_glide\": 1, \"f_heat_rec\": 0.3}"
run v9a_l1 "{$V8, $A, \"glide_lead\": 1.0}"
run v9a_o5 "{$V8, $A, \"glide_oat\": 278.15}"
echo QUEUE DONE
