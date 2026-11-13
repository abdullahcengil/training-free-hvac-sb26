#!/usr/bin/env bash
# Pre-registered round 4 (docs/PREREGISTRATION_4.md): v10 (frozen parameters),
# v9 (round-3 frozen file and parameters) and pid_water on held-out set 4,
# 30-day episodes. Run once. At most WORKERS simulations at a time.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout4/scenarios
OUT=/d/SmartBuildings_data/results/heldout4
V9=D:/SmartBuildings_data/frozen/zonal_b7e5ec9d5df75001d3376c5bf7f0ba121a73f19c.py:TransferPolicy
V9_PARAMS=$(cat docs/preregistration3/V9_PARAMS.json)
V10_PARAMS=$(cat docs/preregistration4/V10_PARAMS.json)
mkdir -p $OUT
if [ -n "$(git status --porcelain policies/zonal.py docs/preregistration4)" ]; then
  echo "uncommitted changes in policies/zonal.py or the frozen pre-registration; commit first" >&2
  exit 1
fi
COMMIT=$(git rev-parse HEAD)
git show $COMMIT:policies/zonal.py > /d/SmartBuildings_data/frozen/zonal_$COMMIT.py
V10=D:/SmartBuildings_data/frozen/zonal_$COMMIT.py:TransferPolicy
echo "{\"commit\": \"$COMMIT\", \"v10_params\": $V10_PARAMS, \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_INFO.json
run() {  # spec tag [kwargs]
  echo "== $2"
  $PY -m sb.run --policy "$1" --scenarios $SC --out $OUT/$2 --steps 8640 --workers ${WORKERS:-4} --components \
    --kwargs "${3:-{\}}" 2>&1 | grep --line-buffered -v -i warn
}
run "$V10" v10 "$V10_PARAMS"
run "$V9" v9 "$V9_PARAMS"
run "baseline:pid_water" pid_water
echo "{\"commit\": \"$COMMIT\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_DONE.json
echo ROUND4 DONE
