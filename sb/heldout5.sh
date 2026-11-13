#!/usr/bin/env bash
# Pre-registered round 5 (docs/PREREGISTRATION_5.md): v11 (frozen parameters),
# v10 (round-4 frozen file and parameters) and pid_water on held-out set 5,
# 30-day episodes. Run once. At most WORKERS simulations at a time.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout5/scenarios
OUT=/d/SmartBuildings_data/results/heldout5
V10=D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py:TransferPolicy
V10_PARAMS=$(cat docs/preregistration4/V10_PARAMS.json)
V11_PARAMS=$(cat docs/preregistration5/V11_PARAMS.json)
mkdir -p $OUT
if [ -n "$(git status --porcelain policies/zonal.py docs/preregistration5)" ]; then
  echo "uncommitted changes in policies/zonal.py or the frozen pre-registration; commit first" >&2
  exit 1
fi
COMMIT=$(git rev-parse HEAD)
git show $COMMIT:policies/zonal.py > /d/SmartBuildings_data/frozen/zonal_$COMMIT.py
V11=D:/SmartBuildings_data/frozen/zonal_$COMMIT.py:TransferPolicy
echo "{\"commit\": \"$COMMIT\", \"v11_params\": $V11_PARAMS, \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_INFO.json
run() {  # spec tag [kwargs]
  echo "== $2"
  $PY -m sb.run --policy "$1" --scenarios $SC --out $OUT/$2 --steps 8640 --workers ${WORKERS:-4} --components \
    --kwargs "${3:-{\}}" 2>&1 | grep --line-buffered -v -i warn
}
run "$V11" v11 "$V11_PARAMS"
run "$V10" v10 "$V10_PARAMS"
run "baseline:pid_water" pid_water
echo "{\"commit\": \"$COMMIT\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_DONE.json
echo ROUND5 DONE
