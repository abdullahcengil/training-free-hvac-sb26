#!/usr/bin/env bash
# v9 development, round 2 of screening: glide on the heating side only.
cd "$(dirname "$0")/.."
F="building_train_1__fairbanks_1 building_train_2__fairbanks_2 building_train_4__fairbanks_4 building_train_5__fairbanks_5 building_train_7__fairbanks_7 building_train_8__fairbanks_8"
V8='"safety_pred": 2, "dist_obs": 1'
run() { WORKERS=4 bash sb/cold.sh "$1" "$2" 3456 $F; }
run v9a "{$V8, \"night_glide\": 1, \"f_heat_rec\": 0.3, \"f_heat_max\": 0.3, \"f_heat_safety\": 0.3}"
run v9b "{$V8, \"night_glide\": 1, \"f_heat_rec\": 0.3}"
run v9c "{$V8, \"night_glide\": 1, \"glide_floor\": -3, \"f_heat_rec\": 0.3, \"f_heat_max\": 0.3, \"f_heat_safety\": 0.3}"
echo QUEUE DONE
