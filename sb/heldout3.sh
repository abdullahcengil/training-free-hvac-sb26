#!/usr/bin/env bash
# Pre-registered round 3 (docs/PREREGISTRATION_3.md): v9 (frozen parameters),
# v8 (round-2 frozen file and parameters) and pid_water on held-out set 3,
# 30-day episodes. Run once. At most WORKERS simulations at a time.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout3/scenarios
OUT=/d/SmartBuildings_data/results/heldout3
V8=D:/SmartBuildings_data/frozen/zonal_e8dbcd3163f2d0e4ce9006b02ed7067a5f5927bd.py:TransferPolicy
V8_PARAMS=$(cat docs/preregistration2/V8_PARAMS.json)
V9_PARAMS=$(cat docs/preregistration3/V9_PARAMS.json)
mkdir -p $OUT
if [ -n "$(git status --porcelain policies/zonal.py docs/preregistration3)" ]; then
  echo "uncommitted changes in policies/zonal.py or the frozen pre-registration; commit first" >&2
  exit 1
fi
COMMIT=$(git rev-parse HEAD)
git show $COMMIT:policies/zonal.py > /d/SmartBuildings_data/frozen/zonal_$COMMIT.py
V9=D:/SmartBuildings_data/frozen/zonal_$COMMIT.py:TransferPolicy
echo "{\"commit\": \"$COMMIT\", \"v9_params\": $V9_PARAMS, \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_INFO.json
run() {  # spec tag [kwargs]
  echo "== $2"
  $PY -m sb.run --policy "$1" --scenarios $SC --out $OUT/$2 --steps 8640 --workers ${WORKERS:-4} --components \
    --kwargs "${3:-{\}}" 2>&1 | grep --line-buffered -v -i warn
}
run "$V9" v9 "$V9_PARAMS"
run "$V8" v8 "$V8_PARAMS"
run "baseline:pid_water" pid_water
echo "{\"commit\": \"$COMMIT\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_DONE.json
echo ROUND3 DONE
