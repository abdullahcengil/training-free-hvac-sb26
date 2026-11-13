#!/usr/bin/env bash
# Pre-registered round 2 (docs/PREREGISTRATION_2.md): v8 (frozen parameters),
# v7 (round-1 frozen file) and the four baselines on held-out set 2, 30-day
# episodes. Run once. At most WORKERS simulations at a time.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout2/scenarios
OUT=/d/SmartBuildings_data/results/heldout2
V7=D:/SmartBuildings_data/frozen/zonal_ad5946615c746745a243560ae3a681eaf7d19618.py:TransferPolicy
V8_PARAMS=$(cat docs/preregistration2/V8_PARAMS.json)
mkdir -p $OUT
if [ -n "$(git status --porcelain policies/zonal.py docs/preregistration2)" ]; then
  echo "uncommitted changes in policies/zonal.py or the frozen pre-registration; commit first" >&2
  exit 1
fi
COMMIT=$(git rev-parse HEAD)
git show $COMMIT:policies/zonal.py > /d/SmartBuildings_data/frozen/zonal_$COMMIT.py
V8=D:/SmartBuildings_data/frozen/zonal_$COMMIT.py:TransferPolicy
echo "{\"commit\": \"$COMMIT\", \"v8_params\": $V8_PARAMS, \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_INFO.json
run() {  # spec tag [kwargs]
  echo "== $2"
  $PY -m sb.run --policy "$1" --scenarios $SC --out $OUT/$2 --steps 8640 --workers ${WORKERS:-3} --components \
    --kwargs "${3:-{\}}" 2>&1 | grep -v -i warn
}
run "$V8" v8 "$V8_PARAMS"
run "$V7" v7
for b in pid_water pid fixed_setpoint bang_bang; do run "baseline:$b" $b; done
echo "{\"commit\": \"$COMMIT\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_DONE.json
