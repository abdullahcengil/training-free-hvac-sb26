#!/usr/bin/env bash
# v9 development, fourth screen: glide-only variants on the union of the cold and mixed sets (10 scenarios), 12 days.
cd "$(dirname "$0")/.."
U="building_train_1__atlanta_2 building_train_1__denver_7 building_train_1__fairbanks_1 building_train_8__fairbanks_8 building_train_2__denver_8 building_train_4__denver_2 building_train_2__fairbanks_2 building_train_4__fairbanks_4 building_train_5__fairbanks_5 building_train_7__fairbanks_7"
V8='"safety_pred": 2, "dist_obs": 1'
B='"night_glide": 1, "f_heat_rec": 0.3'
run() { WORKERS=4 bash sb/cold.sh "$1" "$2" 3456 $U; }
run v9d "{$V8, $B, \"f_heat_safety\": 0.4}"
run v9e "{$V8, $B, \"glide_lead\": 0.5}"
echo QUEUE DONE
