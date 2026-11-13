#!/usr/bin/env bash
# v9 development: candidates on the six Fairbanks training scenarios, 12 days.
cd "$(dirname "$0")/.."
F="building_train_1__fairbanks_1 building_train_2__fairbanks_2 building_train_4__fairbanks_4 building_train_5__fairbanks_5 building_train_7__fairbanks_7 building_train_8__fairbanks_8"
V8='"safety_pred": 2, "dist_obs": 1'
G='"night_glide": 1, "guard": -5, "lead_h": 0, "f_heat_max": 0.3, "f_heat_safety": 0.3'
run() { WORKERS=4 bash sb/cold.sh "$1" "$2" 3456 $F; }
run v8 "{$V8}"
run fh03 "{$V8, \"f_heat_max\": 0.3, \"f_heat_safety\": 0.3}"
run gl_d "{$V8, $G, \"f_heat_rec\": 0.3}"
run gl_b "{$V8, $G, \"f_heat_rec\": 0.5}"
run gl_e "{$V8, $G, \"f_heat_rec\": 0.3, \"glide_safety\": 0.9}"
echo QUEUE DONE
