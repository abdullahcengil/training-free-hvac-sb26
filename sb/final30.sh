#!/usr/bin/env bash
# The v11 candidate on all 30 training scenarios at full length (4 workers), after the bit-for-bit check of the
# code at the v10 parameters. Usage: bash sb/final30.sh <params.json> <tag>   (params merged over V10_PARAMS.json)
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
P=$1; TAG=$2
cp policies/zonal.py /d/SmartBuildings_data/frozen/zonal_${TAG}.py
bash sb/bitcheck11g.sh
$PY - "$P" "$TAG" <<'PY'
import json, sys
from pathlib import Path
kw = json.loads(Path(sys.argv[1]).read_text()); tag = sys.argv[2]
SC = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios")
order = {"building_train_2": 0, "building_train_4": 1, "building_train_5": 2, "building_train_1": 3,
         "building_train_7": 4, "building_train_8": 5}
scen = sorted((p.parent.parent.name, p.parent.name) for p in SC.glob("*/*/config.gin"))
scen.sort(key=lambda bw: order[bw[0]])
jobs = [{"policy": f"D:/SmartBuildings_data/frozen/zonal_{tag}.py:TransferPolicy", "kwargs": kw,
         "out": f"D:/SmartBuildings_data/results/dev11_8640/{tag}", "scenario": f"{b}__{w}"} for b, w in scen]
Path(f"sb/jobs_{tag}_30.json").write_text(json.dumps(jobs, indent=1))
print(len(jobs), "jobs written")
PY
$PY -m sb.jobs sb/jobs_${TAG}_30.json --workers 4 2>&1 | grep --line-buffered -v -i warn
echo FINAL30 DONE
