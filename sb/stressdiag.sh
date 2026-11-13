#!/usr/bin/env bash
# Stress-test diagnosis (docs/STRESS_TEST.md, rule 2): per-zone dumps once a worker is free (the tank-fix check's
# single shipped job ends first). b7 duluth_jan15 days 7-12 (comfort jumps on day 8) and, for contrast, b2 on the
# same days.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
until [ -f /d/SmartBuildings_data/results/tankfix/pid_water_shipped/building_train_1__fairbanks_1.json ]; do sleep 30; done
echo "start $(date +%H:%M:%S)"
S=D:/SmartBuildings_data/stress/scenarios
O=D:/SmartBuildings_data/results/stressdiag
$PY -m sb.stress_dump --scenario $S/building_train_7/duluth_jan15 --start 2016 --end 3744 --out $O/b7_duluth.npz 2>&1 | grep -v -i warn
$PY -m sb.stress_dump --scenario $S/building_train_2/duluth_jan15 --start 2016 --end 3744 --out $O/b2_duluth.npz 2>&1 | grep -v -i warn
echo "STRESSDIAG DONE $(date +%H:%M:%S)"
