#!/usr/bin/env bash
# Round 5, deviation 5 (docs/DEVIATIONS.md): resume after the run was stopped for a Windows security update.
# Same frozen files and parameters as sb/heldout5.sh; RUN_INFO.json is left as written at the start; sb.run
# skips every scenario that already has a result (all 12 v11 runs had finished).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout5/scenarios
OUT=/d/SmartBuildings_data/results/heldout5
COMMIT=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['commit'])" "$OUT/RUN_INFO.json")
[ -f "/d/SmartBuildings_data/frozen/zonal_$COMMIT.py" ] || { echo "frozen v11 file for '$COMMIT' not found" >&2; exit 1; }
V11=D:/SmartBuildings_data/frozen/zonal_$COMMIT.py:TransferPolicy
V10=D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py:TransferPolicy
V10_PARAMS=$(cat docs/preregistration4/V10_PARAMS.json)
V11_PARAMS=$(cat docs/preregistration5/V11_PARAMS.json)
echo "{\"commit\": \"$COMMIT\", \"resumed\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_RESUME.json
run() {  # spec tag [kwargs]
  echo "== $2"
  $PY -m sb.run --policy "$1" --scenarios $SC --out $OUT/$2 --steps 8640 --workers ${WORKERS:-4} --components \
    --kwargs "${3:-{\}}" 2>&1 | grep --line-buffered -v -i warn
}
run "$V11" v11 "$V11_PARAMS"
run "$V10" v10 "$V10_PARAMS"
run "baseline:pid_water" pid_water
echo "{\"commit\": \"$COMMIT\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"resumed_after_update\": true}" > $OUT/RUN_DONE.json
echo ROUND5 DONE
